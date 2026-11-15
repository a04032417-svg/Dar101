"""np_core - shared demo data for the Nonprofit Organization suite (Dar Templates, English edition).

Organization: Harbourlight Community Trust, about 1.3M a year, 4 programs, about 1,400 donors, about 30 grants a year.
All rows are deterministic, oldest first; n= thins a list but keeps the most recent rows; optional dates are ''.
Dates are relative to TODAY (env NP_TODAY overrides); about 2 years of activity with rows in the current month and the last 30 days.

Constants: COMPANY, SUITE, OWNER, DEV_MANAGER, TODAY, Y, HISTORY_START, GIFT_START, THANKYOU_DAYS, RESERVE_MONTHS, COST_PER_DOLLAR,
  LAPSE_MONTHS, PLEDGE_OVERDUE_DAYS, PLEDGE_WRITEOFF_DAYS, ACK_OVER, VOLUNTEER_HOUR_VALUE, BOARD_SEATS, ATTEND_MIN, GIVE_OR_GET,
  REPORT_WARN_DAYS, MATCH_CHASE_DAYS, EMPLOYER_COST_PCT, CARD_FEE_PCT, PROB_* stage probabilities.
Date helpers: day, iso, ago, ahead, to_date, month_start, add_months, months14, week_start.
Lists (value lists for the workbooks): ROLES, TEAMS, PAY_TYPES, DONOR_TYPES, DONOR_STATUS, CONTACT_PREFS, CHANNELS, METHODS, GIFT_TYPES, CAMPAIGNS,
  APPEALS, PROGRAMS, FUNCTIONS, FUND_KINDS, FUNDER_TYPES, GRANT_STAGES, GRANT_PAY_STATUS, REPORT_KINDS, REPORT_STATUS, GRANT_LINES,
  PLEDGE_STATUS, INSTALMENT_STATUS, RECUR_STATUS, INKIND_TYPES, MATCH_STATUS, PIPELINE_STAGES, EXPENSE_CATEGORIES, EVENT_KINDS, EVENT_STATUS,
  TICKET_TYPES, SPONSOR_LEVELS, VOL_ROLES, VOL_STATUS, SHIFT_STATUS, PART_STATUS, BOARD_ROLES, COMMITTEES, SKILLS, MEETING_KINDS, ATTEND,
  OBLIGATION_KINDS, MEMBER_LEVELS, DUES_STATUS, BANK_KINDS, BUDGET_AREAS, INCOME_LINES (see the source for the rest); pairs(values) builds list pairs.
People and reference tables: team (16 rows NP-01..NP-16: 8 staff, 8 outside contacts), staff, contacts, funds (FD-01..FD-10),
  programs, expense_categories, channels, appeals, funder_types, vol_roles; board (BM-01..BM-11) via board_rows.
Row generators (each takes n=None): donor_rows, contact_rows, gift_rows, recurring_rows, pledge_rows, pledge_payment_rows, matching_rows,
  inkind_rows, batch_rows, prospect_rows, fund_rows, fund_month_rows, release_rows, transfer_rows, grant_rows, grant_payment_rows,
  grant_report_rows, grant_budget_rows, staff_time_rows, pay_rows, expense_rows, event_rows, ticket_rows, sponsor_rows, auction_rows,
  campaign_rows, volunteer_rows, slot_rows, shift_rows, member_rows, dues_rows, participant_rows, program_month_rows, session_rows,
  outcome_rows, board_rows, meeting_rows, attendance_rows, declaration_rows, obligation_rows, cash_rows, bank_rows, forecast_rows,
  budget_rows, income_budget_rows.
story(): dict of the 6 story ids (asserted): lapsing major donor (donor), grant report due in ~10 days with spending behind (report, grant),
  overdrawn restricted fund (fund), pledge instalment 60+ days overdue (pledge_payment, pledge), gala over budget (event),
  forecast month where reserve falls below 3 months (forecast_month).
"""
import os
import datetime as dt
import calendar
import random
import hashlib
import math

COMPANY = 'Harbourlight Community Trust'
SUITE = 'fx-20261115-nonprofit'
OWNER = 'Grace Adeyemi'
DEV_MANAGER = 'Mateus Oliveira'
TODAY = dt.date.fromisoformat(os.environ['NP_TODAY']) if os.environ.get('NP_TODAY') else dt.date.today()
D = dt.date
Y = TODAY.year

# shared settings defaults (editable "your number" values; only three are sector starting points: reserve months, cost to raise one dollar, retention vs own last year)
THANKYOU_DAYS = 2              # working days a thank-you may wait
RESERVE_MONTHS = 3.0           # starting point, set your own
COST_PER_DOLLAR = 0.25         # starting point, set your own
LAPSE_MONTHS = 12              # gave last year, not this year
PLEDGE_OVERDUE_DAYS = 30
PLEDGE_WRITEOFF_DAYS = 180
ACK_OVER = 250.0               # a gift at or above this needs a written acknowledgement (your own rule)
VOLUNTEER_HOUR_VALUE = 30.0    # example, set your own
BOARD_SEATS = 12
ATTEND_MIN = 0.75
GIVE_OR_GET = 1000.0
REPORT_WARN_DAYS = 30
MATCH_CHASE_DAYS = 45
EMPLOYER_COST_PCT = 0.12
CARD_FEE_PCT = 0.022
PROB_IDENTIFIED, PROB_CULTIVATION, PROB_ASK, PROB_COMMITTED = 0.10, 0.25, 0.50, 0.90
HISTORY_START = D(Y - 2, 1, 1)         # tables other than the gift log
GIFT_START = D(Y - 3, 1, 1)            # the gift log reaches one year further back (retention and lapse need three full years)


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
def rng(tag=''): return random.Random('np-core-20261115-' + str(tag))
def R2(x): return round(x + 1e-9, 2)
def _ms(d): return dt.date(d.year, d.month, 1)
def _eom(d): return dt.date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])
def _next_dow(d, dow):
    while d.weekday() != dow: d += day(1)
    return d
def _months_between(a, b):
    out, d = [], _ms(a)
    while d <= b: out.append(d); d = add_months(d, 1)
    return out


# ------------------------------------------------------------------ lists (plain international English; keys from pairs() stay <= 21 characters)
ROLES = ['Executive director', 'Development manager', 'Program manager', 'Volunteer coordinator', 'Program assistant', 'Bookkeeper', 'Outside accountant', 'Bank contact',
         'Insurance broker', 'Event venue', 'Caterer', 'Printer and mail house', 'Foundation program officer', 'Corporate sponsor contact']
TEAMS = ['Management', 'Programs', 'Outside']
PAY_TYPES = ['Salary', 'Hourly', 'Invoice']
PAY_ROLES = ROLES[:6]
DONOR_TYPES = ['Individual', 'Household', 'Business', 'Foundation', 'Faith or community']
DONOR_STATUS = ['Active', 'Lapsed', 'Prospect', 'Paused']
CONTACT_PREFS = ['Email', 'Mail', 'Phone', 'Text message']
CONTACT_ROLES = ['Primary', 'Partner', 'Office manager', 'Treasurer', 'Community liaison', 'Owner']
CHANNELS = ['Online form', 'Mail', 'Event', 'In person', 'Payroll giving']
METHODS = ['Card', 'Check or cheque', 'Cash', 'Bank transfer']
GIFT_TYPES = ['One-time', 'Recurring', 'Pledge payment', 'Matching gift', 'Event gift']
CAMPAIGNS = ['Year-End Appeal', 'Giving Day', 'Spring Gala', 'Fun Run', 'Summer Camp Appeal', 'Back-to-School Drive', 'Monthly Giving', 'General giving']
APPEALS = ['Year-end letter', 'Year-end email series', 'Giving day online push', 'Gala invitation', 'Gala paddle raise', 'Fun run sponsor ask', 'Camp scholarship letter',
           'School supply drive', 'Monthly giving page', 'Pantry harvest letter', 'Senior holiday card', 'Thank-you and renewal']
APPEAL_CAMPAIGN = {'Year-end letter': 'Year-End Appeal', 'Year-end email series': 'Year-End Appeal', 'Giving day online push': 'Giving Day', 'Gala invitation': 'Spring Gala',
                   'Gala paddle raise': 'Spring Gala', 'Fun run sponsor ask': 'Fun Run', 'Camp scholarship letter': 'Summer Camp Appeal', 'School supply drive': 'Back-to-School Drive',
                   'Monthly giving page': 'Monthly Giving', 'Pantry harvest letter': 'General giving', 'Senior holiday card': 'Year-End Appeal', 'Thank-you and renewal': 'General giving'}
PROGRAMS = ['After-School Learning', 'Family Food Pantry', 'Senior Meals and Visits', 'Summer Youth Camp']
SHIFT_PROGRAMS = PROGRAMS + ['Events', 'Office']
EXPENSE_PROGRAMS = PROGRAMS + ['Shared']
FUNCTIONS = ['Program', 'Management', 'Fundraising', 'Shared']
FUND_KINDS = ['Unrestricted', 'Board-designated', 'Program restricted', 'Purpose restricted', 'Grant restricted']
FUNDER_TYPES = ['Private foundation', 'Community foundation', 'Corporate giving', 'Government grant']
GRANT_STAGES = ['Prospect', 'Letter of inquiry', 'Application', 'Awarded', 'Declined', 'Withdrawn']
GRANT_PAY_STATUS = ['Received', 'Due', 'Late']
REPORT_KINDS = ['Interim', 'Final', 'Quarterly']
REPORT_STATUS = ['Not started', 'In progress', 'Submitted', 'Late']
GRANT_LINES = ['Staff', 'Direct costs', 'Other costs']
PLEDGE_STATUS = ['Open', 'Paid in full', 'Written off']
INSTALMENT_STATUS = ['Paid', 'Due', 'Overdue', 'Written off']
RECUR_STATUS = ['Active', 'Paused', 'Stopped', 'Failed']
INKIND_TYPES = ['Food', 'School supplies', 'Venue', 'Services']
VALUE_BASIS = ['Donor stated', 'Price list', 'Our estimate']
MATCH_STATUS = ['Expected', 'Requested', 'Received', 'Declined']
PIPELINE_STAGES = ['Identified', 'Cultivation', 'Ask made', 'Committed', 'Closed']
EXPENSE_CATEGORIES = ['Staff pay', 'Food purchases', 'Meals contract', 'Program supplies', 'Camp costs', 'Rent and utilities', 'Insurance', 'Professional fees', 'Printing and mail',
                      'Event costs', 'Card and online fees', 'Technology and phones', 'Travel and vehicle', 'Training and volunteers', 'Marketing and comms']
EVENT_KINDS = ['Gala', 'Fun run', 'Giving day']
EVENT_STATUS = ['Done', 'Planned']
TICKET_TYPES = ['Standard', 'Table of ten', 'Supporter', 'Community', 'Adult runner', 'Youth runner', 'Family pack', 'Walker']
SPONSOR_LEVELS = ['Presenting', 'Gold', 'Silver', 'Community']
SPONSOR_STATUS = ['Paid', 'Promised', 'Declined']
AUCTION_STATUS = ['Sold', 'Unsold']
VOL_ROLES = ['Pantry sorter', 'Meal driver', 'Tutor', 'Camp helper', 'Event helper', 'Office helper', 'Web and data']
VOL_STATUS = ['Active', 'Lapsed', 'On break']
SHIFT_TIMES = ['Morning', 'Afternoon', 'Evening']
SHIFT_STATUS = ['Worked', 'No-show', 'Booked']
AVAIL = ['Weekdays', 'Weekends', 'Evenings', 'Flexible']
PART_STATUS = ['Active', 'Waiting', 'Completed', 'Left']
CONTACT_STATUS = ['Up to date', 'Check in', 'Lost touch']
BOARD_ROLES = ['Chair', 'Vice-chair', 'Treasurer', 'Secretary', 'Member']
COMMITTEES = ['Finance', 'Fundraising', 'Governance']
SKILLS = ['Finance', 'Fundraising', 'Law and policy', 'Marketing', 'Community links', 'Education', 'Health and care', 'Technology']
MEETING_KINDS = ['Board', 'Finance', 'Fundraising', 'Governance']
ATTEND = ['Present', 'Apologies', 'Absent']
DECL_STATUS = ['Filed', 'Due', 'Overdue']
OBLIGATION_KINDS = ['Policy review', 'Insurance renewal', 'Yearly return', 'Annual report', 'Accounts review', 'Funder report', 'Board training', 'Safety check']
OB_STATUS = ['Done', 'Upcoming', 'Overdue']
MEMBER_LEVELS = ['Friend', 'Supporter', 'Patron']
DUES_STATUS = ['Paid', 'Due soon', 'Overdue', 'Lapsed']
BANK_KINDS = ['Gift deposit', 'Grant payment', 'Event receipts', 'Membership dues', 'Payroll', 'Supplier payments', 'Rent and bills', 'Fees and transfers']
BUDGET_AREAS = PROGRAMS + ['Management', 'Fundraising']
INCOME_LINES = ['Individuals', 'Business and groups', 'Grants', 'Events', 'Dues and other']
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
BATCH_STATUS = ['Banked', 'Open']
STAFF_NAMES = []   # filled below

# ------------------------------------------------------------------ people
# id, name, country, role, team, pay type, hours a week, monthly salary, hourly rate, area, start days ago
_staff = [('NP-01', 'Grace Adeyemi', 'Nigeria', 'Executive director', 'Management', 'Salary', 40, 6400, 0, 'All areas', 2600),
          ('NP-02', 'Mateus Oliveira', 'Brazil', 'Development manager', 'Management', 'Salary', 40, 5100, 0, 'Donors, grants and events', 1700),
          ('NP-03', 'Priya Nair', 'India', 'Program manager', 'Programs', 'Salary', 40, 4700, 0, 'All four programs', 1500),
          ('NP-04', 'Lars Henriksen', 'Norway', 'Volunteer coordinator', 'Programs', 'Salary', 36, 3800, 0, 'Volunteers and shifts', 1100),
          ('NP-05', 'Amira Haddad', 'Jordan', 'Program assistant', 'Programs', 'Hourly', 26, 0, 20.0, 'After-School Learning', 800),
          ('NP-06', 'Tomasz Wrona', 'Poland', 'Program assistant', 'Programs', 'Hourly', 24, 0, 19.0, 'Family Food Pantry', 620),
          ('NP-07', 'Mei-Ling Tan', 'Singapore', 'Program assistant', 'Programs', 'Hourly', 20, 0, 21.0, 'Senior Meals and Camp', 410),
          ('NP-08', 'Fiona Gallagher', 'Ireland', 'Bookkeeper', 'Management', 'Hourly', 10, 0, 28.0, 'Bookkeeping and banking', 1000)]
staff = []
for _i, (a, b, c, ro, te, pt, hw, sal, hr, ar, st) in enumerate(_staff):
    staff.append(dict(staff_id=a, name=b, role=ro, team=te, pay_type=pt, phone=fake_phone(301 + _i), email=fake_email(b), hours_week=hw, monthly_salary=float(sal),
                      hourly_rate=float(hr), area=ar, country=c, start=ago(st)))
_ctc = [('NP-09', 'Hannah Lindqvist', 'Sweden', 'Outside accountant', 'Yearly accounts review and year-end pack'),
        ('NP-10', 'Samuel Boateng', 'Ghana', 'Bank contact', 'Accounts, deposits and card payouts'),
        ('NP-11', 'Carla Mendes', 'Portugal', 'Insurance broker', 'Liability, property and event cover'),
        ('NP-12', 'Yusuf Karim', 'Tanzania', 'Event venue', 'Gala hall and fun run grounds'),
        ('NP-13', 'Isabella Rossi', 'Italy', 'Caterer', 'Senior meals contract and gala dinner'),
        ('NP-14', 'Kenji Watanabe', 'Japan', 'Printer and mail house', 'Appeal letters, statements and programs'),
        ('NP-15', 'Olivia Brandt', 'Germany', 'Foundation program officer', 'Community foundation grant contact'),
        ('NP-16', 'Rajesh Kapoor', 'India', 'Corporate sponsor contact', 'Gala presenting sponsor and match challenge')]
contacts = [dict(staff_id=a, name=b, role=ro, team='Outside', pay_type='Invoice', phone=fake_phone(321 + _i), email=fake_email(b), hours_week=0, monthly_salary=0.0, hourly_rate=0.0,
                 area=sp, country=c, start=ago(2400 - 200 * _i)) for _i, (a, b, c, ro, sp) in enumerate(_ctc)]
team = staff + contacts
STAFF_NAMES.extend(s['name'] for s in staff)
staff_by_name = {s['name']: s for s in team}
VENDOR = {'Event venue': 'Yusuf Karim', 'Caterer': 'Isabella Rossi', 'Printer and mail house': 'Kenji Watanabe', 'Outside accountant': 'Hannah Lindqvist', 'Insurance broker': 'Carla Mendes',
          'Bank contact': 'Samuel Boateng'}

# program leads: the part-time assistant who runs each program day to day and the program manager
PROGRAM_LEAD = {'After-School Learning': 'Amira Haddad', 'Family Food Pantry': 'Tomasz Wrona', 'Senior Meals and Visits': 'Mei-Ling Tan', 'Summer Youth Camp': 'Mei-Ling Tan'}
PROGRAM_FUND = {'After-School Learning': 'After-School Fund', 'Family Food Pantry': 'Food Pantry Fund', 'Senior Meals and Visits': 'Senior Meals Fund', 'Summer Youth Camp': 'Summer Camp Fund'}

# ------------------------------------------------------------------ reference tables
# fund, kind, opening balance at HISTORY_START (General is solved later), note
_FUNDS = [('General Fund', 'Unrestricted', 0.0, 'Free money: spend on anything the mission needs'),
          ('Facilities Reserve', 'Board-designated', 58000.0, 'Set aside by the board for building repairs and replacements'),
          ('After-School Fund', 'Program restricted', 9500.0, 'Gifts and grants given for After-School Learning'),
          ('Food Pantry Fund', 'Program restricted', 12500.0, 'Gifts and grants given for the Family Food Pantry'),
          ('Senior Meals Fund', 'Program restricted', 8200.0, 'Gifts and grants given for Senior Meals and Visits'),
          ('Summer Camp Fund', 'Program restricted', 6400.0, 'Gifts and grants given for the Summer Youth Camp'),
          ('Kitchen Equipment Fund', 'Purpose restricted', 4000.0, 'Gifts given to replace pantry and meals kitchen equipment'),
          ('Camp Bursary Fund', 'Purpose restricted', 3100.0, 'Gifts given to pay camp places for families'),
          ('Learning Lab Grant Fund', 'Grant restricted', 0.0, 'Money from one grant, for the Learning Lab project only'),
          ('Winter Warmth Fund', 'Purpose restricted', 2600.0, 'Gifts given for winter meal kits and visits for seniors')]
funds = [dict(fund_id='FD-%02d' % (i + 1), fund=a, restriction=b, opening_balance=c, purpose=d_) for i, (a, b, c, d_) in enumerate(_FUNDS)]
FUND = {f['fund']: f for f in funds}
FUND_NAMES = [f['fund'] for f in funds]
RESTRICTED_FUNDS = [f['fund'] for f in funds if f['restriction'] in ('Program restricted', 'Purpose restricted', 'Grant restricted')]
GENERAL = 'General Fund'
RESERVE_FUND = 'Facilities Reserve'
programs = [dict(program_id='PG-%02d' % (i + 1), program=p, lead=PROGRAM_LEAD[p], fund=PROGRAM_FUND[p], capacity=c, unit=u)
            for i, (p, c, u) in enumerate([('After-School Learning', 70, 'children a term'), ('Family Food Pantry', 320, 'households a month'), ('Senior Meals and Visits', 120, 'seniors a month'),
                                           ('Summer Youth Camp', 110, 'campers a summer')])]
PROG = {p['program']: p for p in programs}
# category, program share, management share, fundraising share, rule
_CAT = [('Staff pay', .60, .25, .15, 'staff time'), ('Food purchases', 1, 0, 0, 'direct'), ('Meals contract', 1, 0, 0, 'direct'), ('Program supplies', 1, 0, 0, 'direct'), ('Camp costs', 1, 0, 0, 'direct'),
        ('Rent and utilities', .70, .22, .08, 'floor area'), ('Insurance', .60, .35, .05, 'headcount'), ('Professional fees', .05, .90, .05, 'direct'), ('Printing and mail', .10, .10, .80, 'use'),
        ('Event costs', 0, 0, 1, 'direct'), ('Card and online fees', 0, 0, 1, 'direct'), ('Technology and phones', .50, .30, .20, 'headcount'), ('Travel and vehicle', .90, .05, .05, 'use'),
        ('Training and volunteers', .75, .20, .05, 'headcount'), ('Marketing and comms', .20, .10, .70, 'use')]
expense_categories = [dict(category_id='EC-%02d' % (i + 1), category=a, program_share=b, management_share=c, fundraising_share=d_, rule=e) for i, (a, b, c, d_, e) in enumerate(_CAT)]
CAT = {c['category']: c for c in expense_categories}
channels = [dict(channel_id='CH-%02d' % (i + 1), channel=c, kind=k) for i, (c, k) in enumerate([('Online form', 'Online'), ('Mail', 'Offline'), ('Event', 'Offline'), ('In person', 'Offline'), ('Payroll giving', 'Online')])]
appeals = [dict(appeal_id='AP-%02d' % (i + 1), appeal=a, campaign=APPEAL_CAMPAIGN[a]) for i, a in enumerate(APPEALS)]
funder_types = [dict(type_id='FT-%02d' % (i + 1), funder_type=t) for i, t in enumerate(FUNDER_TYPES)]
vol_roles = [dict(role_id='VR-%02d' % (i + 1), role=r_, program=p, hours=h) for i, (r_, p, h) in enumerate([
    ('Pantry sorter', 'Family Food Pantry', 3.0), ('Meal driver', 'Senior Meals and Visits', 3.0), ('Tutor', 'After-School Learning', 2.5), ('Camp helper', 'Summer Youth Camp', 4.0),
    ('Event helper', 'Events', 5.0), ('Office helper', 'Office', 3.0), ('Web and data', 'Office', 2.0)])]
VROLE = {v['role']: v for v in vol_roles}
OUTCOMES = {'After-School Learning': ['Finished the term', 'Homework done on time', 'Reading check passed', 'Attended 8 of 10 sessions'],
            'Family Food Pantry': ['Households served', 'Fresh produce boxes given', 'Referred to another service', 'Returned within 60 days'],
            'Senior Meals and Visits': ['Meals delivered', 'Wellbeing visits made', 'Joined a social event', 'Referred to another service'],
            'Summer Youth Camp': ['Finished a full session', 'Skill badge earned', 'Bursary places filled', 'Parents joined an open day']}

# ------------------------------------------------------------------ names
_FIRST = ['Amara', 'Lucas', 'Priya', 'Mateo', 'Yuki', 'Fatima', 'Oliver', 'Chen', 'Ines', 'Kwame', 'Elena', 'Rafael', 'Mei', 'Omar', 'Sofia', 'Jonas', 'Aisha', 'Diego', 'Hannah', 'Ravi',
          'Noor', 'Tomasz', 'Leila', 'Gabriel', 'Ingrid', 'Samuel', 'Zainab', 'Pavel', 'Camila', 'Kenji', 'Anja', 'Idris', 'Maya', 'Stefan', 'Adaeze', 'Hugo', 'Sakura', 'Ahmed', 'Clara', 'Tariq',
          'Bianca', 'Nikolai', 'Esther', 'Mohamed', 'Greta', 'Joao', 'Fiona', 'Arjun', 'Lena', 'Emeka', 'Mina', 'Callum', 'Dalia', 'Marco', 'Yara', 'Felix', 'Thandi', 'Andre', 'Sunita', 'Liam',
          'Rosa', 'Hamza', 'Elif', 'Sven', 'Chiamaka', 'Pedro', 'Aiko', 'Daniel', 'Salma', 'Ivan', 'Nia', 'Rohan', 'Petra', 'Kofi', 'Lucia', 'Jin', 'Marta', 'Dev', 'Alina', 'Tunde',
          'Beatrice', 'Hassan', 'Ewa', 'Mario', 'Naledi', 'Oscar', 'Reem', 'Viktor', 'Wanjiru', 'Xavier', 'Yasmin', 'Zoltan', 'Abena', 'Bruno', 'Chloe', 'Dmitri', 'Eva', 'Farid', 'Gita', 'Henrik',
          'Isla', 'Jamal', 'Katarina', 'Luis', 'Mirela', 'Nathan', 'Olga', 'Pablo', 'Qiu', 'Ruth', 'Sanjay', 'Tamara', 'Uche', 'Vera', 'Wei', 'Anselm', 'Zola', 'Ayesha', 'Bjorn', 'Carmen',
          'Dario', 'Edith', 'Femi', 'Giulia', 'Hiro', 'Imelda', 'Jorge', 'Kavita', 'Leon', 'Mona', 'Nabil', 'Orla', 'Patrice', 'Quinn', 'Rania', 'Soren', 'Tessa', 'Umar', 'Vanessa', 'Wiktor']
_LAST = ['Okafor', 'Lindqvist', 'Moreno', 'Nakamura', 'Haddad', 'Petrov', 'Santos', 'Adeyemi', 'Kowalski', 'Mensah', 'Fernandes', 'Chandran', 'Park', 'Malik', 'Nordin', 'Sorensen', 'Ali', 'Morales',
         'Asante', 'Costa', 'Zhao', 'Desai', 'Murphy', 'Schneider', 'Rossi', 'Dubois', 'Garcia', 'Ivanova', 'Tanaka', 'Nguyen', 'Silva', 'Khan', 'Cohen', 'Novak', 'Johansson', 'Papadopoulos',
         'Hoffmann', 'Ramos', 'Singh', 'Abara', 'Mwangi', 'Sato', 'Olsen', 'Bianchi', 'Yilmaz', 'Hassan', 'Kim', 'Wang', 'Lopez', 'Martin', 'Brown', 'Taylor', 'Wilson', 'Evans', 'Thomas', 'Walker',
         'Clarke', 'Hughes', 'Patel', 'Sharma', 'Das', 'Reddy', 'Ibrahim', 'Mahmoud', 'Aziz', 'Barzani', 'Castillo', 'Vargas', 'Rojas', 'Mendoza', 'Herrera', 'Jimenez', 'Alvarez', 'Pereira',
         'Teixeira', 'Carvalho', 'Almeida', 'Lund', 'Berg', 'Eriksen', 'Hansen', 'Larsen', 'Virtanen', 'Korhonen', 'Nowak', 'Wisniewski', 'Horvat', 'Popescu', 'Kovacs', 'Szabo', 'Marin', 'Jovanovic',
         'Ndlovu', 'Dlamini', 'Botha', 'Mokoena', 'Kamau', 'Otieno', 'Banda', 'Tembo', 'Diallo', 'Traore', 'Sow', 'Keita', 'Boateng', 'Owusu', 'Adjei', 'Eze', 'Obi', 'Nwosu', 'Bello', 'Danjuma',
         'Rahman', 'Chowdhury', 'Hossain', 'Perera', 'Fernando', 'Tran', 'Pham', 'Lim', 'Tan', 'Wong', 'Chan', 'Lee', 'Ong', 'Reyes', 'Cruz', 'Bautista', 'Dela Cruz', 'Whitmore', 'Ashworth', 'Penhale']
_PLACES = ['Elm Street', 'Riverside', 'Harbourview', 'Northgate', 'Eastfield', 'Maple Court', 'Stonebridge', 'Lakeside', 'Cedar Hill', 'Westbrook', 'Oakridge', 'Fairview', 'Pinewood',
           'Millbank', 'Brookside', 'Hillcrest', 'Southgate', 'Ashford', 'Kingsway', 'Willow Bend', 'Copperfield', 'Marsh Lane', 'Highgate', 'Seaview']
_TRADES = ['Bakery', 'Hardware', 'Dental Practice', 'Garage', 'Florist', 'Pharmacy', 'Law Office', 'Print Shop', 'Cafe', 'Builders', 'Accountants', 'Grocers', 'Optical', 'Plumbing',
           'Veterinary Clinic', 'Bookshop', 'Physiotherapy', 'Landscaping', 'Electrical', 'Dry Cleaners', 'Taxi Service', 'Hair Studio']
_GROUPS = ['Faith Community', 'Community Choir', 'Service Club', 'Neighbours Association', "Women's Circle", 'Youth Football Club', 'Garden Club', 'Parish Fellowship', 'Interfaith Circle', 'Book Club',
           'Mosque Community', 'Temple Group', 'Church Fellowship', 'Rowing Club']
_FOUND = ['Family Fund', 'Charitable Trust', 'Giving Circle', 'Foundation', 'Legacy Fund', 'Family Trust']
_BIZ_FIXED = ['Cascade Grocers', 'Hillcrest Builders', 'Granite Logistics', 'Bluewater Energy', 'Sunrise Dairy', 'Lakeside Health Plan']
_STORY_DONOR = 'Eleanor Whitcombe'
_STORY_PLEDGE_BIZ = 'Hillcrest Builders'
_SPONSOR_BIZ = 'Cascade Grocers'

_MW = {1: .035, 2: .03, 3: .07, 4: .05, 5: .085, 6: .05, 7: .035, 8: .045, 9: .06, 10: .07, 11: .13, 12: .34}
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
def _wc(r, vals, ws): return r.choices(vals, ws)[0]
def _nice(x):
    if x < 20: return float(max(5, round(x)))
    if x < 100: return float(round(x / 5.0) * 5)
    if x < 500: return float(round(x / 10.0) * 10)
    if x < 2000: return float(round(x / 25.0) * 25)
    if x < 10000: return float(round(x / 50.0) * 50)
    return float(round(x / 250.0) * 250)
def _wdays(d, k):
    """add k working days"""
    s = 1 if k >= 0 else -1
    k = abs(k)
    while k:
        d += day(s)
        if d.weekday() < 5: k -= 1
    return d
def _pdate(r, y, m):
    if m == 12:
        x = r.random(); dd = r.randint(26, 31) if x < .38 else r.randint(15, 25) if x < .76 else r.randint(1, 14)
    else: dd = r.randint(1, 28)
    return D(y, m, min(dd, calendar.monthrange(y, m)[1]))


# ------------------------------------------------------------------ event dates (relative to the build day)
def _gala_date(y): return _next_dow(D(y, 5, 14), 5)
def _giving_day(y): return _next_dow(D(y, 3, 10), 1)
def _fun_run_dates():
    fr = TODAY - day(22); fr = fr - day((fr.weekday() - 5) % 7)
    return [fr - day(364 * k) for k in (2, 1, 0)]
def _event_plan():
    """(event, kind, date) for three years of history plus the next ones, oldest first"""
    out = []
    for y in range(Y - 2, Y + 2):
        out.append(('Spring Gala', 'Gala', _gala_date(y))); out.append(('Giving Day', 'Giving day', _giving_day(y)))
    for d in _fun_run_dates(): out.append(('Fun Run', 'Fun run', d))
    out = [x for x in out if HISTORY_START <= x[2] <= TODAY + day(200)]
    # the gala on or before today minus 7 days is "this spring's gala"; later ones are planned
    return sorted(out, key=lambda x: x[2])


def _sample_names(r, n, used):
    out = []
    while len(out) < n:
        nm = r.choice(_FIRST) + ' ' + r.choice(_LAST)
        if nm in used: continue
        used.add(nm); out.append(nm)
    return out


# ------------------------------------------------------------------ stage 1: donors
_BOARD = [('BM-01', 'Dr. Ngozi Eze', 'Chair', 'Governance', 'Education'), ('BM-02', 'Michael Brandt', 'Treasurer', 'Finance', 'Finance'),
          ('BM-03', 'Sunita Rao', 'Vice-chair', 'Fundraising', 'Fundraising'), ('BM-04', 'Carlos Mendoza', 'Secretary', 'Governance', 'Law and policy'),
          ('BM-05', 'Aisha Bello', 'Member', 'Fundraising', 'Community links'), ('BM-06', 'Jonas Eriksen', 'Member', 'Finance', 'Technology'),
          ('BM-07', 'Fatima Zahra Idrissi', 'Member', 'Governance', 'Health and care'), ('BM-08', 'Peter Okonkwo', 'Member', 'Fundraising', 'Marketing'),
          ('BM-09', 'Elena Vasquez', 'Member', 'Finance', 'Finance'), ('BM-10', 'Thomas Whitmore', 'Member', 'Fundraising', 'Fundraising'),
          ('BM-11', 'Lin Wei', 'Member', 'Finance', 'Education')]


def _stage_donors(w):
    r = rng('donors'); used = set()
    pool = []
    mix = [('Individual', 1030), ('Household', 175), ('Business', 90), ('Foundation', 28), ('Faith or community', 77)]
    tierw = {'Individual': [.004, .03, .25, .716], 'Household': [.01, .06, .33, .6], 'Business': [.03, .22, .5, .25], 'Foundation': [.2, .6, .2, 0], 'Faith or community': [0, .15, .55, .3]}
    capr = {'major': (5600, 15000), 'mid': (1000, 4800), 'regular': (150, 950), 'small': (25, 145)}
    cohortw = [.30, .26, .24, .20]
    prospect_p = {'Individual': .075, 'Household': .06, 'Business': .1, 'Foundation': .1, 'Faith or community': .03}
    biz_used = list(_BIZ_FIXED)
    for typ, n in mix:
        names = _sample_names(r, n * 2, used) if typ in ('Individual', 'Household') else []
        for k in range(n):
            if typ == 'Individual': nm = names[k]; contact = nm
            elif typ == 'Household':
                nm = names[k].split()[-1] + ' household'; contact = names[k]
            elif typ == 'Business':
                nm = biz_used.pop(0) if biz_used else '%s %s' % (r.choice(_PLACES), r.choice(_TRADES))
                if nm in used: nm = nm + ' Ltd'
                used.add(nm); contact = r.choice(_FIRST) + ' ' + r.choice(_LAST)
            elif typ == 'Foundation':
                nm = '%s %s' % (r.choice(_LAST), r.choice(_FOUND)); contact = r.choice(_FIRST) + ' ' + r.choice(_LAST)
                if nm in used: nm = nm + ' II'
                used.add(nm)
            else:
                nm = '%s %s' % (r.choice(_PLACES), r.choice(_GROUPS)); contact = r.choice(_FIRST) + ' ' + r.choice(_LAST)
                if nm in used: nm = nm + ' North'
                used.add(nm)
            tier = _wc(r, ['major', 'mid', 'regular', 'small'], tierw[typ])
            lo, hi = capr[tier]
            cap = math.exp(r.uniform(math.log(lo), math.log(hi)))
            if typ in ('Business', 'Faith or community') and tier == 'small': cap *= 1.5
            if typ == 'Foundation' and tier == 'major': cap *= 1.35
            loyal = 'high' if tier == 'major' else _wc(r, ['low', 'mid', 'high'], [.15, .5, .35] if tier == 'mid' else [.45, .35, .2])
            y0 = _wc(r, [Y - 3, Y - 2, Y - 1, Y], cohortw)
            prospect = r.random() < prospect_p[typ] and tier != 'major'
            if prospect: y0 = None; cap = 0
            dfund = None
            if r.random() < .16 and not prospect:
                dfund = _wc(r, ['After-School Fund', 'Food Pantry Fund', 'Senior Meals Fund', 'Summer Camp Fund', 'Camp Bursary Fund', 'Winter Warmth Fund'],
                            [.22, .32, .17, .14, .07, .08])
            chp = _wc(r, ['Online form', 'Mail', 'In person'], [.5, .3, .2] if typ in ('Individual', 'Household') else [.35, .4, .25])
            pref = _wc(r, CONTACT_PREFS, [.5, .25, .1, .15] if typ in ('Individual', 'Household') else [.6, .1, .3, 0])
            pool.append(dict(type=typ, name=nm, contact=contact, tier=tier, cap=cap, loyal=loyal, y0=y0, prospect=prospect, recur=False, dfund=dfund, chp=chp, pref=pref,
                             payroll=False, special=''))
    # special donors: story major donor, board members, story pledge business is among _BIZ_FIXED
    def find(nm): return [d for d in pool if d['name'] == nm][0]
    sd = [d for d in pool if d['type'] == 'Individual' and d['tier'] == 'small' and not d['prospect']][0]
    sd.update(name=_STORY_DONOR, contact=_STORY_DONOR, tier='major', cap=7000, loyal='high', y0=Y - 3, special='story_major', dfund=None, chp='Mail', pref='Mail')
    for nm, tier, cap in [(_STORY_PLEDGE_BIZ, 'mid', 3600), (_SPONSOR_BIZ, 'major', 9000)]:
        d = find(nm); d.update(tier=tier, cap=cap, loyal='high', y0=Y - 3, prospect=False, special='pledge_biz' if nm == _STORY_PLEDGE_BIZ else 'sponsor_biz')
    for i, (bid, nm, role, com, skill) in enumerate(_BOARD):
        cand = [d for d in pool if d['type'] == 'Individual' and d['tier'] in ('small', 'regular') and not d['special'] and not d['prospect']]
        d = cand[(i * 37) % len(cand)]
        gives = i not in (7, 10)
        tier, cap = (('mid', 2800) if i in (0, 1, 2) else ('regular', 700 + 90 * i))
        d.update(name=nm, contact=nm, tier=tier if gives else 'regular', cap=cap if gives else 0, loyal='high', y0=Y - 3, special='board', prospect=not gives, chp='Online form', dfund=None)
        if not gives: d['y0'] = None
    # recurring donors: from regular and small donors
    cand = [d for d in pool if d['tier'] in ('regular', 'small') and d['type'] in ('Individual', 'Household') and not d['prospect'] and not d['special']]
    r.shuffle(cand)
    for d in cand[:175]: d['recur'] = True
    for d in cand[:40]: d['payroll'] = True
    # duplicates: 10 individuals appear twice (same email, name written differently)
    dups = [d for d in pool if d['type'] == 'Individual' and not d['special'] and not d['prospect'] and d['tier'] in ('small', 'regular') and not d['recur']][:10]
    for d in dups:
        c = dict(d); parts = d['name'].split(); c['name'] = parts[0][0] + '. ' + ' '.join(parts[1:]); c['special'] = 'duplicate'; c['dup_of'] = d['name']
        c['y0'] = Y - 1 if Y - 1 > d['y0'] else Y; c['tier'] = 'small'; c['cap'] = 60; c['loyal'] = 'low'; c['recur'] = False
        pool.append(c)
    # active years
    for d in pool:
        if d['prospect'] or d['y0'] is None: d['act'] = {}; continue
        act = {d['y0']: True}
        for y in range(d['y0'] + 1, Y + 1):
            if act.get(y - 1):
                p = {'low': .25, 'mid': .62, 'high': .9}[d['loyal']]
                if y - 1 == d['y0'] and d['tier'] not in ('major', 'mid'): p *= .55
            else: p = .04
            if d['special'] in ('story_major',): p = 1.0 if y < Y else 0.0
            if d['special'] == 'board': p = .96
            if d['tier'] == 'major' and d['special'] != 'story_major': p = 1.0
            if d['special'] in ('pledge_biz', 'sponsor_biz'): p = 1.0
            act[y] = r.random() < p
        d['act'] = act
    # donors who give no gift this year yet but were active: keep as drawn
    pool.sort(key=lambda d: ((d['y0'] if d['y0'] is not None else Y - 3 + 3.9 * r.random()) + r.random() * .9))
    w['pool'] = pool


# ------------------------------------------------------------------ stage 2: gifts (raw: one-time, recurring, pledges, matching)
def _method(r, ch, typ):
    if ch == 'Online form': return _wc(r, ['Card', 'Bank transfer'], [.93, .07])
    if ch == 'Payroll giving': return 'Bank transfer'
    if ch == 'Mail': return _wc(r, ['Check or cheque', 'Card', 'Bank transfer'], [.82, .12, .06]) if typ not in ('Business', 'Foundation') else _wc(r, ['Check or cheque', 'Bank transfer'], [.6, .4])
    if ch == 'Event': return _wc(r, ['Card', 'Cash', 'Check or cheque'], [.62, .18, .2])
    return _wc(r, ['Cash', 'Check or cheque', 'Card'], [.35, .35, .3])


def _stage_gifts(w):
    r = rng('gifts'); pool = w['pool']; raw = []
    gd = {y: _giving_day(y) for y in range(Y - 3, Y + 1)}
    for di, d in enumerate(pool):
        if d['prospect'] or d['recur']: continue
        for y in sorted(d['act']):
            if not d['act'][y]: continue
            tier = d['tier']
            n = {'major': r.choice([1, 2, 2, 3]), 'mid': r.choice([2, 2, 3, 4]), 'regular': r.choice([1, 1, 2, 3]), 'small': _wc(r, [1, 2], [.72, .28])}[tier]
            capy = d['cap'] * (1.05 ** (y - (Y - 3))) * math.exp(r.gauss(0, .22))
            for g in range(n):
                m = r.choices(range(1, 13), [_MW[k] for k in range(1, 13)])[0]
                dt_ = _pdate(r, y, m)
                if d['special'] == 'story_major': continue
                if r.random() < (.2 if tier in ('small', 'regular') and d['type'] in ('Individual', 'Household') else 0) and gd[y] >= GIFT_START: dt_ = gd[y]
                amt = capy / n * r.uniform(.7, 1.3)
                raw.append(dict(date=dt_, di=di, amount=amt, gtype='One-time', channel=d['chp'] if r.random() < .8 else r.choice(['Online form', 'Mail', 'In person']), _y=y))
            if y == Y and not any(g['di'] == di and g['date'].year == Y and g['date'] <= TODAY for g in raw[-n:]):
                # keep first-year donors real: a donor new this year has at least one gift up to today
                if d['y0'] == Y or tier == 'major': raw.append(dict(date=TODAY - day(r.randint(3, 280)), di=di, amount=capy / n, gtype='One-time', channel=d['chp'], _y=y))
    raw = [g for g in raw if GIFT_START <= g['date'] <= TODAY]
    # story major donor: exact gifts for the three full years before this one, nothing this year
    sdi = [i for i, d in enumerate(pool) if d['special'] == 'story_major'][0]
    for y, amt, dd, ch in [(Y - 3, 6000.0, D(Y - 3, 12, 12), 'Mail'), (Y - 2, 7500.0, D(Y - 2, 11, 28), 'Mail'), (Y - 1, 7500.0, D(Y - 1, 12, 9), 'Mail')]:
        raw.append(dict(date=dd, di=sdi, amount=amt, gtype='One-time', channel=ch, _y=y, _fixed=True))
    # recurring donors
    rec = []
    amounts = [10, 15, 20, 25, 25, 30, 35, 40, 50, 50, 60, 75, 100, 120]
    ridx = 0
    for di, d in enumerate(pool):
        if not d['recur']: continue
        ridx += 1
        start = GIFT_START + day(r.randint(0, (TODAY - GIFT_START).days - 25))
        if ridx % 5 == 0: start = TODAY - day(r.randint(25, 240))
        amt = float(r.choice(amounts)) * (1.0 if start < D(Y - 1, 1, 1) else 1.1)
        anchor = r.randint(1, 28)
        ch = 'Payroll giving' if d['payroll'] else 'Online form'
        method = 'Bank transfer' if (d['payroll'] or r.random() < .2) else 'Card'
        stop = None
        if ridx % 3 == 0 or ridx % 7 == 0:
            stop = start + day(r.randint(120, 900))
            if stop > TODAY - day(20): stop = None
        fund = d['dfund'] if (d['dfund'] and r.random() < .5) else GENERAL
        rec.append(dict(di=di, amount=amt, start=start, anchor=anchor, channel=ch, method=method, stop=stop, fund=fund, status='Active', last=None, missed=0, _case=''))
    # recurring story-like cases: failed, paused (last received old)
    active = [x for x in rec if x['stop'] is None and (TODAY - x['start']).days > 200]
    for k, x in enumerate(active[:5]): x['status'] = 'Failed'; x['_case'] = 'failed'; x['fail_from'] = TODAY - day(38 + 9 * k)
    for k, x in enumerate(active[5:8]): x['status'] = 'Paused'; x['_case'] = 'paused'; x['fail_from'] = TODAY - day(75 + 20 * k)
    for x in rec:
        d_ = _ms(x['start']); got = []
        while d_ <= TODAY:
            gdte = D(d_.year, d_.month, min(x['anchor'], calendar.monthrange(d_.year, d_.month)[1]))
            if gdte >= x['start'] and gdte <= TODAY and (x['stop'] is None or gdte <= x['stop']):
                if x['_case'] and gdte >= x['fail_from']: pass
                elif r.random() < .012: x['missed'] += 1
                else: got.append(gdte)
            d_ = add_months(d_, 1)
        x['dates'] = got; x['last'] = max(got) if got else None
        if x['stop']: x['status'] = 'Stopped'
        for g in got: raw.append(dict(date=g, di=x['di'], amount=x['amount'], gtype='Recurring', channel=x['channel'], method=x['method'], fund=x['fund'], _y=g.year, _rec=True))
    w['rec'] = rec
    # pledges
    pledges = []
    cands = [(di, d) for di, d in enumerate(pool) if d['tier'] in ('major', 'mid', 'regular') and not d['prospect'] and not d['special'] in ('story_major', 'duplicate') and not d['recur']]
    for di, d in cands:
        for y in sorted(d['act']):
            if not d['act'][y]: continue
            p = {'major': .45, 'mid': .2, 'regular': .04}[d['tier']]
            if r.random() >= p: continue
            m = r.choices(range(1, 13), [_MW[k] for k in range(1, 13)])[0]
            pdte = _pdate(r, y, m)
            if pdte > TODAY - day(3) or pdte < GIFT_START: continue
            tot = {'major': r.choice([6000, 7500, 9000, 12000, 15000, 20000]), 'mid': r.choice([1200, 1500, 2000, 2400, 3000, 4000]), 'regular': r.choice([300, 400, 600, 800, 1000])}[d['tier']]
            tot = float(tot)
            ninst = r.choice([4, 4, 6, 12]) if tot >= 1200 else r.choice([3, 4, 6])
            if d['tier'] == 'major' and r.random() < .3: ninst = 4
            gap = 3 if ninst == 4 else 1
            fund = d['dfund'] or GENERAL
            campaign = 'Year-End Appeal' if pdte.month in (11, 12) else ('Spring Gala' if pdte.month in (4, 5) and r.random() < .3 else 'General giving')
            pledges.append(dict(di=di, pledged_on=pdte, total=tot, n=ninst, gap=gap, fund=fund, campaign=campaign, special=''))
    # story pledge: quarterly 4 x 1,500 from a business, instalment 2 is 74 days overdue
    bi = [i for i, d in enumerate(pool) if d['special'] == 'pledge_biz'][0]
    pledges = [p for p in pledges if p['di'] != bi]
    pledges.append(dict(di=bi, pledged_on=TODAY - day(180), total=6000.0, n=4, gap=3, fund=GENERAL, campaign='General giving', special='story', first_due=TODAY - day(165)))
    pledges.sort(key=lambda p: (p['pledged_on'], p['di']))
    pp_rows = []
    for k, p in enumerate(pledges):
        p['pledge_id'] = 'PL-%04d' % (k + 1)
        base = round(p['total'] / p['n'] / 5) * 5 if p['n'] not in (3, 6) else round(p['total'] / p['n'], 2)
        first = p.get('first_due') or (p['pledged_on'] + day(r.randint(14, 31)))
        paid_total = 0.0
        for j in range(p['n']):
            due = add_months(first, p['gap'] * j) if not p['special'] else first + day(91 * j)
            amt = base if j < p['n'] - 1 else R2(p['total'] - base * (p['n'] - 1))
            age = (TODAY - due).days; paid_on = ''; status = 'Due'
            if p['special'] == 'story':
                if j == 0: paid_on = due + day(2); status = 'Paid'
                elif j == 1: paid_on = ''; status = 'Overdue'
                else: status = 'Due'
            elif age > 0:
                if age <= 14: ok = r.random() < .55
                elif age <= 60: ok = r.random() < .93
                elif age <= PLEDGE_WRITEOFF_DAYS: ok = True
                else: ok = r.random() < .95
                if ok:
                    delay = r.randint(0, 12) if r.random() < .88 else r.randint(15, 45)
                    paid_on = min(due + day(delay), TODAY); status = 'Paid'
                    if paid_on < due: paid_on = due
                else: status = 'Written off' if age > PLEDGE_WRITEOFF_DAYS else 'Overdue'
                if status == 'Overdue' and age >= 60: status = 'Paid'; paid_on = TODAY - day(r.randint(1, 8))
            pp_rows.append(dict(pledge=p, due=due, amount_due=amt, paid_on=paid_on, amount_paid=amt if paid_on else 0.0, status=status))
            if paid_on and GIFT_START <= paid_on <= TODAY:
                raw.append(dict(date=paid_on, di=p['di'], amount=amt, gtype='Pledge payment', channel=_wc(r, ['Online form', 'Mail', 'In person'], [.35, .4, .25]), method=_wc(r, ['Bank transfer', 'Check or cheque', 'Card'], [.4, .4, .2]),
                                fund=p['fund'], campaign=p['campaign'], _pledge=p['pledge_id'], _y=paid_on.year, _fixed=True))
    for p in pledges:
        mine = [x for x in pp_rows if x['pledge'] is p]
        left = [x for x in mine if x['status'] in ('Due', 'Overdue')]
        p['status'] = 'Written off' if any(x['status'] == 'Written off' for x in mine) and not left else ('Paid in full' if not left else 'Open')
    w['pledges'] = pledges; w['pp'] = pp_rows
    w['raw'] = raw


# ------------------------------------------------------------------ stage 3: events (tickets, sponsors, auction, event gifts)
_AUCTION = ['Weekend cottage stay', 'Dinner for six at a local restaurant', 'Signed sports shirt', 'Garden makeover day', 'Family photo session', 'Pottery class for four', 'Harbour boat trip',
            'Hot-air balloon ride', 'Spa day voucher', 'Case of local wine', 'Handmade quilt', 'Concert tickets for two', 'Bicycle and helmet', 'Cooking class with a chef', 'Original local painting',
            'Kayak day for four', 'Theatre night for two', 'Home cleaning for a month', 'Football match tickets', 'Weekend city break', 'Gourmet hamper', 'Jewellery gift voucher',
            'Vintage record collection', 'Guided hike and picnic', 'Tech gadget bundle', 'Yoga studio pass', 'Bakery treats for a year', 'Hotel night and breakfast', 'Golf round for four', 'Carpentry workshop']
_VENUE = {'Gala': 'Harbour Hall ballroom', 'Fun run': 'Riverside park', 'Giving day': 'Online and phone bank'}


def _stage_events(w):
    r = rng('events'); pool = w['pool']
    plan = _event_plan(); events = []
    gala_idx = 0
    for k, (name, kind, dte) in enumerate(plan):
        status = 'Done' if dte <= TODAY - day(1) else 'Planned'
        events.append(dict(event_id='EV-%02d' % (k + 1), event=name, kind=kind, date=dte, status=status, venue=_VENUE[kind], campaign={'Gala': 'Spring Gala', 'Fun run': 'Fun Run', 'Giving day': 'Giving Day'}[kind], _d=dte))
    # budgets and goals by order within kind
    seq = {}
    for e in events:
        n = seq.get(e['kind'], 0); seq[e['kind']] = n + 1
        yi = e['date'].year - (Y - 2) if e['kind'] != 'Fun run' else n
        if e['kind'] == 'Gala':
            e.update(budget_cost=[40000.0, 44000.0, 48000.0, 52000.0][min(yi, 3)], goal=[105000.0, 120000.0, 130000.0, 140000.0][min(yi, 3)], expected_attendees=[140, 158, 172, 185][min(yi, 3)])
        elif e['kind'] == 'Fun run':
            e.update(budget_cost=[8200.0, 8800.0, 9400.0][min(yi, 2)], goal=[19000.0, 21500.0, 24000.0][min(yi, 2)], expected_attendees=[210, 240, 270][min(yi, 2)])
        else:
            e.update(budget_cost=[2800.0, 3100.0, 3400.0, 3600.0][min(yi, 3)], goal=[19000.0, 22000.0, 26000.0, 28000.0][min(yi, 3)], expected_attendees=0)
    done_galas = [e for e in events if e['kind'] == 'Gala' and e['status'] == 'Done']
    w['story_gala'] = done_galas[-1]['event_id'] if done_galas else ''
    def active_idx(y, tiers=None):
        return [i for i, d in enumerate(pool) if d['act'].get(y) and (tiers is None or d['tier'] in tiers)]
    def other_idx(y): return [i for i, d in enumerate(pool) if not d['act'].get(y) and not d['special'] in ('duplicate',)]
    tickets, sponsors, auction, egifts = [], [], [], []
    biz = [i for i, d in enumerate(pool) if d['type'] in ('Business', 'Foundation') and d['tier'] in ('mid', 'major', 'regular')]
    sbiz = [i for i, d in enumerate(pool) if d['special'] == 'sponsor_biz'][0]
    for e in events:
        y = e['date'].year; dte = e['date']; kind = e['kind']
        yi = 0 if e['date'] < D(Y - 1, 1, 1) else 1 if e['date'] < D(Y, 1, 1) else 2 if e['date'] <= TODAY + day(60) else 3
        buyers = active_idx(y if y <= Y else Y)
        if kind == 'Gala':
            A = e['expected_attendees']
            price = {'Standard': [135.0, 145.0, 150.0, 155.0][yi], 'Table of ten': [1200.0, 1300.0, 1400.0, 1500.0][yi], 'Supporter': [225.0, 240.0, 250.0, 265.0][yi], 'Community': [50.0, 55.0, 60.0, 60.0][yi]}
            ben = {'Standard': 85.0, 'Table of ten': 850.0, 'Supporter': 85.0, 'Community': 40.0}
            plan_rows = []
            for _ in range(max(1, round(.55 * A / 10))): plan_rows.append(('Table of ten', 1))
            seats = {'Standard': .25 * A, 'Supporter': .12 * A, 'Community': .08 * A}
            for tt, s_ in seats.items():
                left = int(round(s_))
                while left > 0:
                    q = min(left, r.choice([1, 2, 2, 2, 4])); plan_rows.append((tt, q)); left -= q
            for tt, q in plan_rows:
                if e['status'] == 'Planned': continue
                sold = dte - day(r.randint(1, 75))
                if sold > TODAY: sold = TODAY
                di = r.choice(buyers) if r.random() < .8 else r.choice(other_idx(y))
                tickets.append(dict(event=e, sold_on=sold, di=di, ticket_type=tt, qty=q, price_each=price[tt], benefit_each=ben[tt], seats=q * (10 if tt == 'Table of ten' else 1)))
            if e['status'] == 'Planned' and (e['date'] - TODAY).days <= 200:
                for q in range(6):
                    tickets.append(dict(event=e, sold_on=TODAY - day(r.randint(1, 27)), di=r.choice(active_idx(Y, ('mid', 'major', 'regular'))), ticket_type='Supporter', qty=2, price_each=price['Supporter'],
                                        benefit_each=ben['Supporter'], seats=2))
            # sponsors
            lv = [('Presenting', 1, 15000.0), ('Gold', 3, 8000.0), ('Silver', 4, 4000.0), ('Community', 6, 1500.0)]
            fac = [.88, .95, 1.0, 1.04][yi]
            used_b = {sbiz}
            for lvl, cnt, amt in lv:
                for c_ in range(cnt):
                    if lvl == 'Presenting': bi = sbiz
                    else:
                        bi = r.choice([b for b in biz if b not in used_b]); used_b.add(bi)
                    promised = float(round(amt * fac / 50) * 50) if lvl != 'Community' else float(round(amt * fac * r.uniform(.7, 1.3) / 50) * 50)
                    pdate = dte - day(r.randint(60, 170))
                    st = 'Paid' if e['status'] == 'Done' else 'Promised'
                    if e['status'] == 'Planned':
                        if lvl == 'Community' and c_ > 1: continue
                        if lvl == 'Silver' and c_ > 1: continue
                        if lvl == 'Gold' and c_ > 1: continue
                        pdate = TODAY - day(r.randint(3, 26))
                        if lvl == 'Silver' and c_ == 1: st = 'Declined'
                    paid_on = '' if st != 'Paid' else min(dte + day(r.randint(-20, 25)), TODAY)
                    if st == 'Paid' and paid_on < pdate: paid_on = pdate + day(10)
                    owed = {'Presenting': 8, 'Gold': 5, 'Silver': 3, 'Community': 2}[lvl]
                    dlv = owed if (e['status'] == 'Planned' or e['event_id'] != w['story_gala'] or c_ % 2 == 0) else max(0, owed - 2)
                    if e['status'] == 'Planned': dlv = 0
                    sponsors.append(dict(event=e, bi=bi, level=lvl, promised=promised, received=promised if st == 'Paid' else 0.0, promised_on=pdate, received_on=paid_on, status=st, owed=owed, delivered=dlv))
            # auction
            n_items = {0: 22, 1: 25, 2: 28, 3: 9}[yi]
            for t in range(n_items):
                val = float(round(r.choice([80, 120, 150, 200, 250, 300, 400, 500, 650, 800, 1200, 1800]) / 10) * 10)
                don = r.choice(biz) if r.random() < .75 else r.choice(active_idx(y if y <= Y else Y))
                sold_p = 0.0; buyer = ''
                if e['status'] == 'Done' and r.random() < .88: sold_p = float(round(val * r.uniform(.65, 1.35) / 5) * 5); buyer = r.choice(buyers)
                recd = TODAY - day(r.randint(1, 50)) if e['status'] == 'Planned' else dte - day(r.randint(5, 60))
                auction.append(dict(event=e, item=_AUCTION[(t * 7 + yi * 3) % len(_AUCTION)] if t < len(_AUCTION) else _AUCTION[t % len(_AUCTION)], don=don, value=val, start=float(round(val * .5 / 5) * 5),
                                    sold=sold_p, buyer=buyer, received_on=recd, status='Sold' if sold_p else ('Unsold' if e['status'] == 'Done' else 'Unsold')))
            if e['status'] == 'Done':   # paddle raise on the night
                np_ = [48, 55, 60][min(yi, 2)]
                for _ in range(np_):
                    amt = float(r.choice([100, 100, 150, 250, 250, 500, 500, 1000, 1000, 2500, 5000]) * (1.0 if yi < 2 else 1.05))
                    egifts.append(dict(date=dte, di=r.choice(buyers), amount=amt, gtype='Event gift', channel='Event', method=_wc(r, ['Card', 'Cash', 'Check or cheque'], [.7, .1, .2]), campaign='Spring Gala',
                                       appeal='Gala paddle raise', _event=e['event_id'], _fixed=True, _y=y))
        elif kind == 'Fun run':
            n_run = e['expected_attendees']
            cnt = {'Adult runner': int(n_run * .5), 'Youth runner': int(n_run * .18), 'Family pack': int(n_run * .1), 'Walker': int(n_run * .22)}
            pr = {'Adult runner': 30.0, 'Youth runner': 15.0, 'Family pack': 70.0, 'Walker': 20.0}
            for tt, c_ in cnt.items():
                for _ in range(c_):
                    sold = dte - day(min(r.choice([0, 0, 1, 2, 3, 5, 7, 10, 14, 21, 30, 45, 60]), 60))
                    if sold > TODAY: continue
                    tickets.append(dict(event=e, sold_on=sold, di=r.choice(buyers), ticket_type=tt, qty=1, price_each=pr[tt], benefit_each=10.0, seats=4 if tt == 'Family pack' else 1))
            for lvl, cnt_, amt in [('Gold', 2, 2000.0), ('Silver', 3, 1000.0), ('Community', 4, 400.0)]:
                for c_ in range(cnt_):
                    bi = r.choice(biz); st = 'Paid' if e['status'] == 'Done' else 'Promised'
                    sponsors.append(dict(event=e, bi=bi, level=lvl, promised=amt, received=amt if st == 'Paid' else 0.0, promised_on=dte - day(r.randint(30, 90)), received_on=(dte - day(r.randint(0, 20))) if st == 'Paid' else '',
                                         status=st, owed=2, delivered=2 if st == 'Paid' else 0))
            if e['status'] == 'Done':
                for _ in range(int(n_run * .4)):
                    egifts.append(dict(date=dte - day(r.randint(0, 34)), di=r.choice(buyers), amount=float(r.choice([15, 20, 25, 25, 30, 40, 50, 75, 100, 150])), gtype='One-time', channel='Online form', method='Card',
                                       campaign='Fun Run', appeal='Fun run sponsor ask', _event=e['event_id'], _fixed=True, _y=y))
        else:   # giving day: match challenge sponsors, the gifts come from the main gift stream
            for c_, amt in enumerate([2500.0, 2000.0, 1500.0]):
                bi = r.choice(biz); st = 'Paid' if e['status'] == 'Done' else 'Promised'
                sponsors.append(dict(event=e, bi=bi, level=['Gold', 'Silver', 'Silver'][c_], promised=amt, received=amt if st == 'Paid' else 0.0, promised_on=dte - day(r.randint(20, 60)),
                                     received_on=(dte + day(r.randint(0, 10))) if st == 'Paid' and dte + day(10) <= TODAY else '', status=st if (st != 'Paid' or dte + day(10) <= TODAY) else 'Paid', owed=2, delivered=2 if st == 'Paid' else 0))
            if e['status'] == 'Done':
                for _ in range(70):
                    egifts.append(dict(date=dte, di=r.choice(buyers), amount=float(r.choice([25, 25, 30, 40, 50, 50, 60, 75, 100, 100, 150, 250])), gtype='One-time', channel='Online form', method='Card',
                                       campaign='Giving Day', appeal='Giving day online push', _event=e['event_id'], _fixed=True, _y=y))
    for s in sponsors:
        if s['status'] == 'Paid' and s['received_on'] == '': s['received_on'] = min(s['event']['date'], TODAY)
    egifts = [g for g in egifts if g['date'] <= TODAY]
    tickets.sort(key=lambda t: (t['sold_on'], t['event']['event_id']))
    sponsors.sort(key=lambda s: (s['event']['date'], ['Presenting', 'Gold', 'Silver', 'Community'].index(s['level'])))
    auction.sort(key=lambda a: (a['event']['date'], a['item']))
    w['events'] = events; w['tickets'] = tickets; w['sponsors'] = sponsors; w['auction'] = auction; w['egifts'] = egifts
    w['raw'].extend(egifts)


# ------------------------------------------------------------------ stage 4: finalize the gift log (scale, matching, campaign, fund, acknowledgement, ids, deposit batches), donor facts, in-kind
def _camp(r, g):
    d = g['date']; ch = g['channel']
    if g['gtype'] == 'Recurring': return 'Monthly Giving', 'Monthly giving page'
    if d == _giving_day(d.year): return 'Giving Day', 'Giving day online push'
    if d.month in (11, 12) and r.random() < .78:
        if ch == 'Mail': return 'Year-End Appeal', 'Year-end letter'
        if ch == 'Online form': return 'Year-End Appeal', 'Year-end email series' if r.random() < .7 else 'Year-end letter'
        return 'Year-End Appeal', 'Senior holiday card' if r.random() < .2 else 'Year-end letter'
    if d.month == 6 and r.random() < .3: return 'Summer Camp Appeal', 'Camp scholarship letter'
    if (d.month == 8 or (d.month == 9 and d.day <= 15)) and r.random() < .28: return 'Back-to-School Drive', 'School supply drive'
    if d.month in (4, 5) and d <= _gala_date(d.year) and r.random() < .2: return 'Spring Gala', 'Gala invitation'
    if d.month in (9, 10) and r.random() < .15: return 'General giving', 'Pantry harvest letter'
    return 'General giving', ('Thank-you and renewal' if r.random() < .45 else '')


def _stage_finalize_gifts(w):
    r = rng('final'); pool = w['pool']; raw = w['raw']
    T = {Y - 3: 440000.0, Y - 2: 505000.0, Y - 1: 560000.0}
    fixed, var = {}, {}
    for g in raw:
        if g.get('_event'): continue
        y = g['date'].year
        if g.get('_fixed') or g.get('_rec'): fixed[y] = fixed.get(y, 0.0) + g['amount']
        else: var[y] = var.get(y, 0.0) + g['amount']
    f = {y: max(.3, (T[y] - fixed.get(y, 0.0)) / var[y]) for y in T}
    f[Y] = f[Y - 1] * 0.8
    w['scale'] = f
    for g in raw:
        if not (g.get('_fixed') or g.get('_rec')): g['amount'] = _nice(g['amount'] * f[g['date'].year])
        g['amount'] = float(g['amount'])
    # matching gifts
    biz = [i for i, d in enumerate(pool) if d['type'] == 'Business' and d['tier'] != 'major']
    matches, extra = [], []
    for g in raw:
        d = pool[g['di']]
        if g['gtype'] != 'One-time' or g.get('_event') or d['type'] not in ('Individual', 'Household') or g['amount'] < 40 or g['channel'] not in ('Online form', 'In person'): continue
        if r.random() >= .075: continue
        ratio = 1.0 if r.random() < .7 else .5
        exp = R2(min(g['amount'], 500.0) * ratio); req = g['date'] + day(r.randint(3, 10)); age = (TODAY - g['date']).days
        if age > 80: st = _wc(r, ['Received', 'Declined', 'Requested'], [.9, .05, .05])
        elif age > 35: st = _wc(r, ['Received', 'Requested'], [.6, .4])
        else: st = _wc(r, ['Expected', 'Requested'], [.45, .55])
        rec_on = req + day(r.randint(18, 55)) if st == 'Received' else ''
        if rec_on and rec_on > TODAY: st = 'Requested'; rec_on = ''
        m = dict(src=g, employer=r.choice(biz), ratio=ratio, expected=exp, requested_on=req if st != 'Expected' else '', received_on=rec_on, status=st, received=exp if st == 'Received' else 0.0)
        matches.append(m)
        if st == 'Received':
            extra.append(dict(date=rec_on, di=m['employer'], amount=exp, gtype='Matching gift', channel='Payroll giving', method='Bank transfer', fund=GENERAL, _fixed=True, _matchfor=g, _y=rec_on.year,
                              campaign=None))
    raw.extend(extra)
    # the story donor is the only donor with 5,000 or more in each of the three full years and nothing this year: others get a gift this year
    yt = {}
    for g in raw: yt.setdefault(g['di'], {}); yt[g['di']][g['date'].year] = yt[g['di']].get(g['date'].year, 0.0) + g['amount']
    for di_, v in yt.items():
        if pool[di_]['special'] != 'story_major' and all(v.get(y_, 0) >= 5000 for y_ in (Y - 3, Y - 2, Y - 1)) and v.get(Y, 0) == 0:
            raw.append(dict(date=TODAY - day(r.randint(5, 120)), di=di_, amount=_nice(v[Y - 1] / 3.0), gtype='One-time', channel=pool[di_]['chp'], _y=Y, _fixed=True))
    # campaign, appeal, fund, method
    fd = {'Camp': ['Summer Camp Fund', 'Camp Bursary Fund', GENERAL], 'School': ['After-School Fund', GENERAL], 'Senior': ['Winter Warmth Fund', GENERAL], 'Pantry': ['Food Pantry Fund', GENERAL]}
    for g in raw:
        d = pool[g['di']]
        if g.get('campaign') is None or 'campaign' not in g:
            if g.get('_matchfor') is not None:
                g['campaign'] = g['_matchfor'].get('campaign') or 'General giving'; g['appeal'] = ''
            else:
                g['campaign'], g['appeal'] = _camp(r, g)
        g.setdefault('appeal', '')
        if 'method' not in g: g['method'] = _method(r, g['channel'], d['type'])
        if 'fund' not in g:
            f_ = d['dfund'] if (d['dfund'] and r.random() < .8) else GENERAL
            a = g['appeal']
            if a == 'Camp scholarship letter': f_ = _wc(r, fd['Camp'], [.6, .25, .15])
            elif a == 'School supply drive': f_ = _wc(r, fd['School'], [.6, .4])
            elif a == 'Senior holiday card': f_ = _wc(r, fd['Senior'], [.5, .5])
            elif a == 'Pantry harvest letter': f_ = _wc(r, fd['Pantry'], [.5, .5])
            g['fund'] = f_
        if g['appeal'] == 'Gala paddle raise':
            g['fund'] = GENERAL
        if g['campaign'] == 'Giving Day' and g['fund'] != GENERAL and r.random() < .5: g['fund'] = GENERAL
    # flaws among the newest one-time gifts: no donor (cash at the door), no fund, duplicates
    recent = [g for g in raw if g['gtype'] == 'One-time' and g['date'] >= TODAY - day(45) and not g.get('_event')]
    recent.sort(key=lambda g: (g['date'], g['di']))
    for g in recent[:3]: g['_nodonor'] = True; g['channel'] = 'In person'; g['method'] = 'Cash'; g['amount'] = min(g['amount'], 150.0)
    for g in recent[3:5]: g['fund'] = ''
    for g in recent[5:9]:
        c = dict(g); c['_dup'] = True; raw.append(c)
    # acknowledgement
    for g in raw:
        if g['gtype'] in ('Recurring', 'Pledge payment', 'Matching gift'): g['ack'] = g['date']
        elif g['date'] >= TODAY - day(2): g['ack'] = ''
        else:
            delay = r.choice([1, 1, 1, 2, 2, 3]) if r.random() < .92 else r.randint(4, 12)
            a = g['date'] + day(delay); g['ack'] = a if a <= TODAY else ''
    old = [g for g in raw if g['ack'] == '' and g['date'] < TODAY - day(3)]
    # a backlog of about 20 gifts that were never thanked, oldest about 70 days
    cand = [g for g in raw if g['gtype'] in ('One-time', 'Event gift') and TODAY - day(75) <= g['date'] <= TODAY - day(3) and g['ack'] != '']
    r.shuffle(cand)
    for g in cand[:20]: g['ack'] = ''
    raw.sort(key=lambda g: (g['date'], g['di'], g['amount'], g['gtype']))
    for i, g in enumerate(raw): g['gift_id'] = 'GF-%05d' % (i + 1)
    # deposit batches: one per week
    wk = {}
    for g in raw: wk.setdefault(week_start(g['date']), []).append(g)
    batches = []
    for i, ws in enumerate(sorted(wk)):
        gs = wk[ws]; logged = R2(sum(g['amount'] for g in gs)); banked_on = ws + day(8)
        b = dict(batch_id='BT-%03d' % (i + 1), week_start=ws, logged=logged, count=len(gs), banked_on=banked_on if banked_on <= TODAY else '', gap=0.0)
        for g in gs: g['batch'] = b['batch_id']
        batches.append(b)
    closed = [b for b in batches if b['banked_on'] != '']
    for k, b in enumerate(closed):
        if r.random() < .022: b['gap'] = -float(r.choice([20, 35, 60, 85, 140, 220]))
        elif r.random() < .012: b['gap'] = float(r.choice([10, 25, 40]))
    if len(closed) > 12:
        closed[-3]['gap'] = -140.0; closed[-7]['gap'] = 35.0
    for b in batches: b['banked'] = R2(b['logged'] + b['gap']) if b['banked_on'] != '' else 0.0
    w['batches'] = batches; w['matches'] = matches
    w['gifts'] = raw
    # donor facts
    firsts, lasts, cnt, tot = {}, {}, {}, {}
    for g in raw:
        if g.get('_nodonor'): continue
        i = g['di']
        firsts[i] = min(firsts.get(i, g['date']), g['date']); lasts[i] = max(lasts.get(i, g['date']), g['date']); cnt[i] = cnt.get(i, 0) + 1; tot[i] = tot.get(i, 0.0) + g['amount']
    w['dfacts'] = dict(first=firsts, last=lasts, cnt=cnt, tot=tot)
    for i, d in enumerate(pool):
        d['donor_id'] = 'DN-%04d' % (i + 1)
    # status
    rr = rng('dstatus')
    for i, d in enumerate(pool):
        if i not in firsts: d['status'] = 'Prospect'
        elif (TODAY - lasts[i]).days <= 365: d['status'] = 'Active'
        else: d['status'] = 'Lapsed'
        if d['status'] in ('Active', 'Lapsed') and rr.random() < .012 and d['special'] == '': d['status'] = 'Paused'


def _stage_inkind(w):
    r = rng('inkind'); pool = w['pool']; rows = []
    biz = [i for i, d in enumerate(pool) if d['type'] in ('Business', 'Faith or community')]
    ind = [i for i, d in enumerate(pool) if d['type'] in ('Individual', 'Household') and not d['prospect']]
    d_ = HISTORY_START
    desc = {'Food': ['Pallet of canned goods', 'Fresh produce delivery', 'Bread and bakery items', 'Dairy and eggs', 'Frozen meals', 'Holiday food boxes', 'Rice and pasta'],
            'School supplies': ['Backpacks and notebooks', 'Art supplies', 'Pencils and stationery', 'Calculators', 'Reading books'],
            'Venue': ['Hall hire at a reduced rate', 'Field and grounds use', 'Meeting room for training'],
            'Services': ['Printing of flyers', 'Website hosting help', 'Accounting hours', 'Photography at an event', 'Delivery van loan', 'Legal advice hours']}
    n_m = {}
    for m in _months_between(HISTORY_START, TODAY):
        k = 15 + (4 if m.month in (11, 12) else 0) + (3 if m.month in (8, 9) else 0) + r.randint(-3, 3)
        for _ in range(k):
            typ = _wc(r, INKIND_TYPES, [.6, .12 + (.2 if m.month in (8, 9) else 0), .03, .17])
            dte = D(m.year, m.month, r.randint(1, 28))
            if dte > TODAY: dte = TODAY - day(r.randint(0, 6))
            di = r.choice(biz) if typ in ('Food', 'Venue', 'Services') and r.random() < .75 else r.choice(ind)
            val = {'Food': r.choice([120, 180, 250, 400, 650, 900, 1500, 2400]), 'School supplies': r.choice([80, 140, 200, 350, 600, 900]), 'Venue': r.choice([300, 800, 1500, 3000, 6000]),
                   'Services': r.choice([200, 400, 800, 1500, 2500, 4000])}[typ]
            basis = _wc(r, VALUE_BASIS, [.45, .3, .25])
            ack = dte + day(r.randint(1, 6))
            rows.append(dict(date=dte, di=di, type=typ, item=r.choice(desc[typ]), qty=r.choice([1, 1, 2, 5, 10, 20, 40]) if typ in ('Food', 'School supplies') else 1,
                             value=float(val), basis=basis, ack=ack if ack <= TODAY else '', fund=GENERAL))
    rows.sort(key=lambda x: (x['date'], x['di']))
    for i, x in enumerate(rows): x['inkind_id'] = 'IK-%05d' % (i + 1)
    w['inkind'] = rows


def _stage_contacts(w):
    r = rng('contacts'); pool = w['pool']; rows = []
    for i, d in enumerate(pool):
        rows.append(dict(di=i, name=d['contact'], role='Owner' if d['type'] == 'Business' and d['contact'] == d['name'] else 'Primary', phone=fake_phone(500 + i), email=fake_email(d['contact'], 0 if d['special'] != 'duplicate' else 0)))
        if d['type'] == 'Household' and r.random() < .7:
            nm = r.choice(_FIRST) + ' ' + d['name'].split()[0]
            rows.append(dict(di=i, name=nm, role='Partner', phone=fake_phone(900 + i), email=fake_email(nm, i)))
        elif d['type'] in ('Business', 'Faith or community', 'Foundation') and r.random() < .55:
            nm = r.choice(_FIRST) + ' ' + r.choice(_LAST)
            rows.append(dict(di=i, name=nm, role=r.choice(['Office manager', 'Treasurer', 'Community liaison']), phone=fake_phone(1300 + i), email=fake_email(nm, i)))
    w['contacts'] = rows


# ------------------------------------------------------------------ stage 5: grants, payments, reports, grant budgets
GRANT_PROGRAMS = PROGRAMS + ['General operating']
_FUNDERS = {'Private foundation': ['Riverbend Family Foundation', 'Ashdown Charitable Trust', "Meridian Children's Fund", 'Oakhaven Foundation', 'Lindenhurst Family Trust', 'Brightfield Foundation',
                                   'Silverleaf Giving Trust', 'Marlowe Education Fund', 'Westcott Foundation', 'Evergreen Neighbours Trust', 'Stonehaven Foundation', 'Pinecrest Family Fund',
                                   'Holloway Charitable Fund', 'Fairmont Hunger Relief Fund'],
            'Community foundation': ['Eastshore Community Foundation', 'Tri-Valley Community Foundation', 'Meadowbrook Community Foundation'],
            'Corporate giving': ['Northwind Corporate Giving', 'Cascade Grocers Community Fund', 'Bluewater Energy Giving Program', 'Granite Logistics Giving', 'Sunrise Dairy Community Fund',
                                 'Hillcrest Builders Giving', 'Lakeside Health Plan Giving', 'Clearview Partners Program'],
            'Government grant': ['County Youth Services Grant', 'State Food Security Fund', 'Regional Senior Services Grant', 'City Neighbourhood Grant', 'Regional Learning and Skills Grant',
                                 'City Summer Opportunity Grant', 'State Community Kitchen Grant', 'County Wellbeing Grant']}
_PROJECTS = {'After-School Learning': ['Reading Boost', 'Homework Club Support', 'Afternoons of Science', 'Learning Lab', 'Tutoring Hours'],
             'Family Food Pantry': ['Fresh Produce Boxes', 'Weekly Pantry Support', 'Cold Storage Upgrade', 'Pantry Delivery Van', 'Holiday Food Boxes'],
             'Senior Meals and Visits': ['Hot Meals Delivery', 'Friendly Visits', 'Winter Meal Kits', 'Senior Lunch Club'],
             'Summer Youth Camp': ['Camp Places Fund', 'Outdoor Learning Week', 'Camp Transport', 'Camp Staff Training'],
             'General operating': ['Core Operating Support', 'Capacity Building', 'Volunteer Program Support']}
_BSHARE = {'After-School Learning': (.62, .30, .08), 'Family Food Pantry': (.30, .62, .08), 'Senior Meals and Visits': (.42, .50, .08), 'Summer Youth Camp': (.38, .52, .10)}
_ASK = {'Government grant': (60000, 150000), 'Community foundation': (20000, 90000), 'Private foundation': (6000, 50000), 'Corporate giving': (2500, 25000)}
_WIN = {'Government grant': .5, 'Community foundation': .6, 'Private foundation': .5, 'Corporate giving': .6}


def _inst_plan(amount, term):
    if amount <= 12000: n = 1
    elif amount <= 45000: n = 2
    else: n = 4
    if term >= 24: n *= 2
    return n


def _stage_grants(w):
    r = rng('grants')
    grants = []
    owners = [DEV_MANAGER, DEV_MANAGER, DEV_MANAGER, OWNER, 'Priya Nair']
    def new(**k):
        g = dict(funder='', ftype='', program='', project='', fund=GENERAL, stage='', asked=0.0, awarded=0.0, prob=0.0, prospect_on='', loi_on='', applied_on='', decision_on='', expected_on='',
                 start_on='', end_on='', term=12, owner=r.choice(owners), write_hours=r.choice([8, 12, 16, 20, 24, 30, 40, 55, 70]), special='', pace=1.0)
        g.update(k); grants.append(g); return g
    used = {}
    def pick(ftype, program):
        names = _FUNDERS[ftype]
        if ftype == 'Community foundation': names = ['Eastshore Community Foundation', 'Tri-Valley Community Foundation', 'Meadowbrook Community Foundation']
        if program == 'Family Food Pantry' and ftype == 'Government grant': names = ['State Food Security Fund', 'County Wellbeing Grant']
        if program == 'Senior Meals and Visits' and ftype == 'Government grant': names = ['Regional Senior Services Grant', 'County Wellbeing Grant']
        if program == 'After-School Learning' and ftype == 'Government grant': names = ['Regional Learning and Skills Grant', 'County Youth Services Grant']
        if program == 'Summer Youth Camp' and ftype == 'Government grant': names = ['City Summer Opportunity Grant', 'City Neighbourhood Grant']
        return r.choice(names)
    def program_pick(): return _wc(r, GRANT_PROGRAMS, [.14, .34, .19, .13, .20])
    lo = HISTORY_START - day(330); hi = TODAY - day(6)
    n_past = 84
    for k in range(n_past):
        ft = _wc(r, FUNDER_TYPES, [.40, .14, .28, .18]); pg = program_pick()
        dec = lo + day(r.randint(0, (hi - lo).days))
        lo_a, hi_a = _ASK[ft]
        ask = float(round(math.exp(r.uniform(math.log(lo_a), math.log(hi_a))) / 500) * 500)
        outcome = 'Awarded' if r.random() < _WIN[ft] else 'Declined'
        if k % 24 == 7: outcome = 'Withdrawn'
        app = dec - day(r.randint(45, 115)); loi = app - day(r.randint(14, 45)) if r.random() < .55 else ''
        term = {'Government grant': r.choice([12, 12, 24]), 'Community foundation': 12, 'Private foundation': r.choice([12, 12, 12, 24, 6]), 'Corporate giving': r.choice([6, 12])}[ft]
        awarded = float(round(ask * r.uniform(.55, 1.0) / 250) * 250) if outcome == 'Awarded' else 0.0
        st = dec + day(r.randint(14, 40))
        g = new(funder=pick(ft, pg), ftype=ft, program=pg, project=r.choice(_PROJECTS[pg]), stage=outcome, asked=ask, awarded=awarded, prob=1.0 if outcome == 'Awarded' else 0.0,
                prospect_on=app - day(r.randint(25, 90)) if loi == '' else loi - day(r.randint(10, 40)), loi_on=loi, applied_on=app, decision_on=dec, start_on=st if outcome == 'Awarded' else '', term=term,
                end_on=(add_months(st, term) - day(1)) if outcome == 'Awarded' else '')
        if outcome == 'Withdrawn': g['decision_on'] = dec
    # open pipeline
    for k in range(9):    # prospects
        ft = _wc(r, FUNDER_TYPES, [.40, .14, .28, .18]); pg = program_pick(); lo_a, hi_a = _ASK[ft]
        new(funder=pick(ft, pg), ftype=ft, program=pg, project=r.choice(_PROJECTS[pg]), stage='Prospect', asked=float(round(math.exp(r.uniform(math.log(lo_a), math.log(hi_a))) / 500) * 500),
            prob=round(r.uniform(.05, .2), 2), prospect_on=TODAY - day(r.randint(5, 90)), expected_on=TODAY + day(r.randint(120, 260)))
    for k in range(6):    # letters of inquiry sent
        ft = _wc(r, FUNDER_TYPES, [.40, .14, .28, .18]); pg = program_pick(); lo_a, hi_a = _ASK[ft]
        new(funder=pick(ft, pg), ftype=ft, program=pg, project=r.choice(_PROJECTS[pg]), stage='Letter of inquiry', asked=float(round(math.exp(r.uniform(math.log(lo_a), math.log(hi_a))) / 500) * 500),
            prob=round(r.uniform(.15, .35), 2), prospect_on=TODAY - day(r.randint(50, 120)), loi_on=TODAY - day(r.randint(7, 45)), expected_on=TODAY + day(r.randint(60, 150)))
    for k in range(8):    # applications waiting for a decision
        ft = _wc(r, FUNDER_TYPES, [.40, .14, .28, .18]); pg = program_pick(); lo_a, hi_a = _ASK[ft]
        ap = TODAY - day(r.randint(10, 95))
        new(funder=pick(ft, pg), ftype=ft, program=pg, project=r.choice(_PROJECTS[pg]), stage='Application', asked=float(round(math.exp(r.uniform(math.log(lo_a), math.log(hi_a))) / 500) * 500),
            prob=round(r.uniform(.3, .6), 2), prospect_on=ap - day(r.randint(40, 100)), loi_on=(ap - day(r.randint(14, 40))) if r.random() < .5 else '', applied_on=ap, expected_on=ap + day(r.randint(70, 120)))
    # the story grant: a community foundation award, 12 months, spending far behind
    st = TODAY - day(240)
    new(funder='Harbour County Community Foundation', ftype='Community foundation', program='After-School Learning', project='Learning Lab', fund='Learning Lab Grant Fund', stage='Awarded', asked=50000.0,
        awarded=48000.0, prob=1.0, prospect_on=st - day(190), loi_on=st - day(165), applied_on=st - day(95), decision_on=st - day(22), start_on=st, end_on=add_months(st, 12) - day(1), term=12, owner='Priya Nair',
        write_hours=44, special='story', pace=.45)
    # a kitchen grant (restricted by purpose)
    kst = TODAY - day(150)
    new(funder='State Community Kitchen Grant', ftype='Government grant', program='Family Food Pantry', project='Kitchen Equipment', fund='Kitchen Equipment Fund', stage='Awarded', asked=36000.0, awarded=30000.0,
        prob=1.0, prospect_on=kst - day(230), loi_on='', applied_on=kst - day(150), decision_on=kst - day(40), start_on=kst, end_on=add_months(kst, 9) - day(1), term=9, owner=DEV_MANAGER, write_hours=60, special='kitchen', pace=.9)
    # sort by first date and number
    grants.sort(key=lambda g: (g['prospect_on'] or g['applied_on'] or TODAY, g['funder']))
    for i, g in enumerate(grants): g['grant_id'] = 'GR-%03d' % (i + 1)
    # fund and pace for awarded restricted grants
    for g in grants:
        if g['special']: continue
        if g['stage'] == 'Awarded':
            g['fund'] = GENERAL if g['program'] == 'General operating' else PROGRAM_FUND[g['program']]
            g['pace'] = min(1.08, max(.85, r.gauss(.97, .06)))
        elif g['program'] != 'General operating':
            g['fund'] = PROGRAM_FUND[g['program']]
    # scale awards so grant money is about the size of a 1.3 million organization (about 480,000 awarded a year)
    tgt = {Y - 3: 300000.0, Y - 2: 440000.0, Y - 1: 470000.0, Y: 470000.0}
    for y_, t_ in tgt.items():
        items = [g for g in grants if g['stage'] == 'Awarded' and not g['special'] and g['decision_on'].year == y_]
        fixed_ = sum(g['awarded'] for g in grants if g['stage'] == 'Awarded' and g['special'] and g['decision_on'].year == y_)
        base_ = sum(g['awarded'] for g in items)
        if not items or base_ <= 0: continue
        k_ = max(.5, (t_ - fixed_) / base_)
        cap_ = {'Government grant': 120000.0, 'Community foundation': 70000.0, 'Private foundation': 55000.0, 'Corporate giving': 25000.0}
        for g in items:
            g['awarded'] = float(min(cap_[g['ftype']], round(g['awarded'] * k_ / 250) * 250))
            g['asked'] = float(max(g['awarded'], round(g['awarded'] / r.uniform(.6, 1.0) / 500) * 500))
    # payments and reports
    pays, reports, budgets = [], [], []
    active = []
    for g in grants:
        if g['stage'] != 'Awarded': continue
        a = g['awarded']; term = g['term']; n = _inst_plan(a, term) if not g['special'] else 2
        if g['special'] == 'story': offs = [(7, 24000.0), (None, 24000.0)]
        elif g['special'] == 'kitchen': offs = [(10, 15000.0), (200, 15000.0)]
        else:
            base = round(a / n / 50) * 50; offs = []
            for j in range(n):
                due = 7 if n == 1 else (7 + (term * 30 // n) * j)
                offs.append((due, base if j < n - 1 else R2(a - base * (n - 1))))
        for j, (off, amt) in enumerate(offs):
            due = (g['start_on'] + day(off)) if off is not None else TODAY + day(25)
            age = (TODAY - due).days
            rec = ''; st_ = 'Due'
            if age > 0:
                if age > 14: rec = due + day(r.randint(0, 12)); st_ = 'Received'
                elif g['special'] == 'story': pass
                else:
                    if r.random() < .7: rec = due + day(r.randint(0, min(age, 6))); st_ = 'Received'
                    else: st_ = 'Late'
                if rec and rec > TODAY: rec = TODAY; 
            pays.append(dict(grant=g, due=due, amount=amt, received_on=rec, status=st_ if not rec else 'Received', n=j + 1))
        # reports
        s_ = g['start_on']; e_ = g['end_on']
        rep = []
        if g['ftype'] == 'Government grant' and term >= 12:
            for q in range(1, term // 3 + 1): rep.append(('Quarterly', add_months(s_, 3 * q) + day(15)))
        elif term >= 12: rep.append(('Interim', add_months(s_, term // 2) + day(0) if not g['special'] == 'story' else TODAY + day(10)))
        rep.append(('Final', e_ + day(30)))
        for kind, due in rep:
            sub = ''; st_ = 'Not started'
            if due < TODAY - day(2):
                sub = due - day(r.randint(0, 6)); st_ = 'Submitted'
                if r.random() < .12: sub = due + day(r.randint(1, 8))
            elif (due - TODAY).days <= 45: st_ = 'In progress'
            reports.append(dict(grant=g, kind=kind, due=due, submitted_on=sub, status=st_, owner=g['owner']))
        # budget lines (restricted grants only)
        if g['program'] != 'General operating':
            sh = _BSHARE[g['program']]
            if g['special'] == 'story': amts = [27000.0, 17000.0, 4000.0]
            else: amts = [round(a * sh[0] / 50) * 50.0, round(a * sh[1] / 50) * 50.0, 0.0]; amts[2] = R2(a - amts[0] - amts[1])
            for ln, am in zip(GRANT_LINES, amts): budgets.append(dict(grant=g, line=ln, budget=am))
        if g['start_on'] <= TODAY <= g['end_on']: active.append(g)
    # a few active grants under- and overspend; a report that is already late
    cand = [g for g in active if not g['special'] and g['program'] != 'General operating']
    for k, g in enumerate(cand[:3]): g['pace'] = [.72, .78, 1.2][k]
    late_c = [x for x in reports if x['status'] in ('Not started', 'In progress') and x['due'] < TODAY + day(1) and x['grant']['special'] == '']
    for x in reports:
        if x['grant']['special'] == 'story': continue
        # keep the story report the only open one due within 20 days; push others out or close them
        if x['status'] in ('Not started', 'In progress') and 0 <= (x['due'] - TODAY).days <= 20:
            x['due'] = TODAY + day(24 + (hash(x['grant']['grant_id']) % 25)); x['status'] = 'In progress' if (x['due'] - TODAY).days <= 45 else 'Not started'
    # one report is already late (due a week ago, still open)
    for x in reports:
        if x['grant']['special'] == '' and x['status'] == 'Submitted' and 3 <= (TODAY - x['due']).days <= 30:
            x['status'] = 'Late'; x['submitted_on'] = ''; x['due'] = TODAY - day(6); break
    pays.sort(key=lambda p: (p['due'], p['grant']['grant_id']))
    for i, p in enumerate(pays): p['pay_id'] = 'GP-%03d' % (i + 1)
    reports.sort(key=lambda x: (x['due'], x['grant']['grant_id']))
    for i, x in enumerate(reports): x['report_id'] = 'RP-%03d' % (i + 1)
    for i, b in enumerate(budgets): b['line_id'] = 'GB-%03d' % (i + 1)
    w['grants'] = grants; w['gpays'] = pays; w['greports'] = reports; w['gbudgets'] = budgets; w['gactive'] = active


# ------------------------------------------------------------------ stage 6: pay, staff time across grants and programs, expenses
def _month_hours(r, s):
    return R2(s['hours_week'] * 4.33 * r.uniform(.92, 1.04)) if s['pay_type'] == 'Hourly' else R2(s['hours_week'] * 4.33)


def _staff_base(name, m):
    """base split of one person's month: list of (kind, program, function, share)"""
    summer = m.month in (6, 7, 8); late_spring = m.month == 5
    if name == 'Grace Adeyemi': return [('Management', 'Shared', 'Management', .52), ('Fundraising', 'Shared', 'Fundraising', .23), ('Program', 'Shared', 'Program', .25)]
    if name == 'Mateus Oliveira': return [('Fundraising', 'Shared', 'Fundraising', .86), ('Management', 'Shared', 'Management', .05), ('Program', 'Shared', 'Program', .09)]
    if name == 'Priya Nair':
        c = .45 if summer else .30 if late_spring else .14
        rest = 1 - c - .05
        return [('Program', 'After-School Learning', 'Program', R2(rest * .34)), ('Program', 'Family Food Pantry', 'Program', R2(rest * .34)), ('Program', 'Senior Meals and Visits', 'Program', R2(rest * .32)),
                ('Program', 'Summer Youth Camp', 'Program', R2(c)), ('Management', 'Shared', 'Management', .05)]
    if name == 'Lars Henriksen':
        c = .30 if summer else .08
        return [('Program', 'Family Food Pantry', 'Program', .25), ('Program', 'Senior Meals and Visits', 'Program', .20), ('Program', 'After-School Learning', 'Program', R2(.57 - c - .25 - .20 + .20)),
                ('Program', 'Summer Youth Camp', 'Program', R2(c)), ('Fundraising', 'Shared', 'Fundraising', .10), ('Management', 'Shared', 'Management', .05)]
    if name == 'Amira Haddad': return [('Program', 'After-School Learning', 'Program', .94 if not summer else .55), ('Program', 'Summer Youth Camp', 'Program', .0 if not summer else .39), ('Management', 'Shared', 'Management', .06)]
    if name == 'Tomasz Wrona': return [('Program', 'Family Food Pantry', 'Program', .95), ('Management', 'Shared', 'Management', .05)]
    if name == 'Mei-Ling Tan': return [('Program', 'Senior Meals and Visits', 'Program', .40 if summer else .72), ('Program', 'Summer Youth Camp', 'Program', .55 if summer else .22), ('Management', 'Shared', 'Management', .05 if summer else .06)]
    return [('Management', 'Shared', 'Management', .78), ('Fundraising', 'Shared', 'Fundraising', .12), ('Program', 'Shared', 'Program', .10)]


def _stage_money(w):
    r = rng('money'); months = _months_between(HISTORY_START, TODAY)
    pay = []; cost = {}
    for m in months:
        raise_f = 1.03 ** (m.year - (Y - 2))
        for s in staff:
            hrs = _month_hours(r, s)
            gross = R2(s['monthly_salary'] * raise_f) if s['pay_type'] == 'Salary' else R2(hrs * s['hourly_rate'] * raise_f)
            emp = R2(gross * EMPLOYER_COST_PCT)
            pay.append(dict(month=m, staff=s['name'], role=s['role'], pay_type=s['pay_type'], hours=hrs if s['pay_type'] == 'Hourly' else R2(s['hours_week'] * 4.33), gross=gross, employer_cost=emp,
                            total=R2(gross + emp), status='Paid' if _eom(m) < TODAY or D(m.year, m.month, 25) <= TODAY else 'Accruing'))
            cost[(s['name'], m)] = (R2(gross + emp), pay[-1]['hours'])
    pay.sort(key=lambda p: (p['month'], p['staff']))
    for i, p in enumerate(pay): p['pay_id'] = 'PA-%04d' % (i + 1)
    # staff time lines
    grants = [g for g in w['grants'] if g['stage'] == 'Awarded' and g['program'] != 'General operating']
    gb = {}
    for b in w['gbudgets']: gb.setdefault(b['grant']['grant_id'], {})[b['line']] = b['budget']
    lines = []
    for m in months:
        act = [g for g in grants if _ms(g['start_on']) <= m <= _ms(g['end_on']) and g['start_on'] <= TODAY]
        dem = {}
        for g in act:
            monthly = gb[g['grant_id']]['Staff'] / g['term'] * g['pace'] * r.uniform(.93, 1.07)
            lead = PROGRAM_LEAD[g['program']]
            for nm, sh in ((lead, .55), ('Priya Nair', .45)):
                dem.setdefault(nm, []).append((g, monthly * sh))
        for s in staff:
            nm = s['name']; tot, hrs = cost[(nm, m)]
            base = [list(x) for x in _staff_base(nm, m)]
            gl = []
            for g, amt in dem.get(nm, []):
                pct = amt / tot
                src = [b for b in base if b[1] == g['program'] and b[0] == 'Program']
                if not src: src = [b for b in base if b[0] == 'Program']
                if not src: continue
                src = max(src, key=lambda b: b[3])
                pct = min(pct, max(0.0, src[3] - .02))
                if pct < .005: continue
                src[3] = R2(src[3] - pct); gl.append((g, round(pct, 3)))
            out = [(b[0] if b[0] != 'Program' else 'Program', None, b[1], b[2], b[3]) for b in base if b[3] > 0] + [('Grant', g, g['program'], 'Program', pc) for g, pc in gl]
            tp = sum(x[4] for x in out); out = [(a, b, c, d_, round(e / tp, 3)) for a, b, c, d_, e in out]
            diff = round(1.0 - sum(x[4] for x in out), 3)
            a, b, c, d_, e = out[-1]; out[-1] = (a, b, c, d_, round(e + diff, 3))
            for (kind, g, prog, fun, pc) in out:
                lines.append(dict(month=m, staff=nm, staff_id=s['staff_id'], kind=kind, grant=g, program=prog, function=fun, percent=pc, hours=R2(hrs * pc), cost=R2(tot * pc)))
    for i, x in enumerate(lines): x['time_id'] = 'ST-%05d' % (i + 1)
    w['pay'] = pay; w['stime'] = lines
    # ---- expenses
    ex = []
    def add(d, cat, vendor, prog, fun, amt, grant=None, event=None, campaign='', appeal='', note='', cand=None):
        if d > TODAY or d < HISTORY_START: return
        ex.append(dict(date=d, category=cat, vendor=vendor, program=prog, function=fun, amount=R2(amt), grant=grant, event=event, campaign=campaign, appeal=appeal, note=note, cand=cand))
    for x in lines:
        d = D(x['month'].year, x['month'].month, 25)
        if d > TODAY: continue
        g = x['grant']
        add(d, 'Staff pay', 'Payroll', x['program'] if x['program'] in PROGRAMS else 'Shared', x['function'], x['cost'], grant=g['grant_id'] if g else None, note='Allocated by staff time',
            cand=(g['fund'] if g else (PROGRAM_FUND.get(x['program']) if x['function'] == 'Program' and x['program'] in PROGRAMS else GENERAL)))
    yf = {Y - 2: .94, Y - 1: .97, Y: 1.0}
    gcode = {}
    for m in months:
        f_ = yf[m.year]
        act = [g for g in grants if _ms(g['start_on']) <= m <= _ms(g['end_on']) and g['start_on'] <= TODAY]
        cat_of = {'After-School Learning': 'Program supplies', 'Family Food Pantry': 'Food purchases', 'Senior Meals and Visits': 'Meals contract', 'Summer Youth Camp': 'Camp costs'}
        gsum = {}
        for g in act:
            amt = (gb[g['grant_id']]['Direct costs'] + gb[g['grant_id']]['Other costs']) / g['term'] * g['pace'] * r.uniform(.8, 1.2)
            cat = 'Program supplies' if g['special'] == 'kitchen' else cat_of[g['program']]
            k = 2 if amt > 2500 else 1
            for _ in range(k):
                add(D(m.year, m.month, r.randint(3, 27)), cat, {'Food purchases': 'Wholesale food supplier', 'Meals contract': VENDOR['Caterer'], 'Camp costs': 'Camp activity providers',
                                                              'Program supplies': 'School and program supplier'}[cat], g['program'], 'Program', amt / k, grant=g['grant_id'], cand=g['fund'], note=g['project'])
            gsum[(cat, g['program'])] = gsum.get((cat, g['program']), 0.0) + amt
        summer = m.month in (6, 7, 8)
        def rest(cat, prog, target, parts, vendors, note, cand=None):
            tgt = max(target * .15, target - gsum.get((cat, prog), 0.0))
            for k in range(parts):
                add(D(m.year, m.month, min(28, 2 + k * (26 // parts) + r.randint(0, 3))), cat, r.choice(vendors), prog, 'Program', tgt / parts * r.uniform(.85, 1.15), note=note, cand=cand or PROGRAM_FUND[prog])
        rest('Food purchases', 'Family Food Pantry', 14500 * f_ * (1.25 if m.month in (11, 12) else .92 if m.month in (7, 8) else 1), 7, ['Wholesale food supplier', 'Produce supplier', 'Bakery supplier', 'Dairy supplier', 'Regional food bank partner'], 'Weekly food purchase')
        rest('Meals contract', 'Senior Meals and Visits', 9800 * f_ * (1.1 if m.month in (11, 12, 1, 2) else 1), 2, [VENDOR['Caterer']], 'Meals contract invoice')
        rest('Program supplies', 'After-School Learning', (700 if m.month in (7, 8) else 1900) * f_, 3, ['School and program supplier', 'Book and stationery supplier'], 'Learning materials')
        rest('Program supplies', 'Family Food Pantry', 800 * f_, 2, ['Packaging and storage supplier'], 'Bags, boxes and cleaning')
        rest('Program supplies', 'Senior Meals and Visits', 700 * f_, 1, ['Packaging and storage supplier'], 'Meal containers')
        rest('Program supplies', 'Summer Youth Camp', (4200 if summer else 300) * f_, 2, ['School and program supplier'], 'Camp materials')
        rest('Camp costs', 'Summer Youth Camp', (21000 if summer else 1800 if m.month == 5 else 1000 if m.month == 4 else 300) * f_, 3 if summer else 1, ['Camp activity providers', 'Coach and transport hire'], 'Camp activities and transport',
             cand='Camp Bursary Fund' if r.random() < .08 else None)
        # shared and management costs
        add(D(m.year, m.month, 1), 'Rent and utilities', 'Building landlord', 'Shared', 'Shared', 6900 * (1.0 if m.year < Y else 1.03) * (.97 if m.year == Y - 2 else 1), note='Monthly rent')
        add(D(m.year, m.month, 20), 'Rent and utilities', 'Utility providers', 'Shared', 'Shared', (1150 + (260 if m.month in (12, 1, 2, 7, 8) else 0)) * r.uniform(.9, 1.1) * f_, note='Heat, power and water')
        if m.month in (1, 4, 7, 10): add(D(m.year, m.month, 5), 'Insurance', VENDOR['Insurance broker'], 'Shared', 'Shared', 5350 * f_, note='Quarterly cover')
        add(D(m.year, m.month, 14), 'Professional fees', 'Bank', 'Shared', 'Management', 190 * r.uniform(.9, 1.1), note='Bank account fees')
        if m.month == 2: add(D(m.year, 2, 18), 'Professional fees', VENDOR['Outside accountant'], 'Shared', 'Management', 9500 * f_, note='Yearly accounts review')
        if m.month in (3, 6, 9, 12): add(D(m.year, m.month, 15), 'Professional fees', VENDOR['Outside accountant'], 'Shared', 'Management', 1200 * f_, note='Quarterly check-in')
        add(D(m.year, m.month, 1), 'Technology and phones', 'Software and web providers', 'Shared', 'Shared', 760 * f_, note='Software and web hosting')
        add(D(m.year, m.month, 12), 'Technology and phones', 'Phone and internet provider', 'Shared', 'Shared', 590 * f_ * r.uniform(.95, 1.05), note='Phones and internet')
        add(D(m.year, m.month, 9), 'Travel and vehicle', 'Fuel and vehicle costs', 'Senior Meals and Visits', 'Program', 1150 * f_ * r.uniform(.9, 1.1), note='Meal delivery van', cand=PROGRAM_FUND['Senior Meals and Visits'])
        add(D(m.year, m.month, 21), 'Travel and vehicle', 'Fuel and vehicle costs', 'Family Food Pantry', 'Program', 780 * f_ * r.uniform(.9, 1.1), note='Food pickups', cand=PROGRAM_FUND['Family Food Pantry'])
        add(D(m.year, m.month, 7), 'Training and volunteers', 'Training providers', 'Shared', 'Shared', 650 * f_ * r.uniform(.8, 1.3), note='Volunteer training and checks')
        add(D(m.year, m.month, 23), 'Training and volunteers', 'Volunteer appreciation', 'Shared', 'Shared', 800 * f_ * r.uniform(.6, 1.5) * (2.2 if m.month in (4, 12) else 1), note='Volunteer thank-you costs')
        add(D(m.year, m.month, 6), 'Marketing and comms', 'Web and design helpers', 'Shared', 'Shared', 700 * f_, note='Website and newsletter tool')
        add(D(m.year, m.month, 17), 'Marketing and comms', 'Local media and ads', 'Shared', 'Shared', 850 * f_ * r.uniform(.6, 1.5), note='Awareness and recruitment ads')
        # printing and mail: appeals
        P_ = VENDOR['Printer and mail house']
        if m.month == 11:
            add(D(m.year, 11, 3), 'Printing and mail', P_, 'Shared', 'Fundraising', 4200 * f_, campaign='Year-End Appeal', appeal='Year-end letter', note='Year-end letter print')
            add(D(m.year, 11, 6), 'Printing and mail', P_, 'Shared', 'Fundraising', 7300 * f_, campaign='Year-End Appeal', appeal='Year-end letter', note='Year-end letter postage and mail house')
        if m.month == 12: add(D(m.year, 12, 4), 'Printing and mail', P_, 'Shared', 'Fundraising', 1100 * f_, campaign='Year-End Appeal', appeal='Senior holiday card', note='Holiday cards')
        if m.month == 4: add(D(m.year, 4, 10), 'Printing and mail', P_, 'Shared', 'Fundraising', 3300 * f_, campaign='Spring Gala', appeal='Gala invitation', note='Gala invitations')
        if m.month == 5: add(D(m.year, 5, 12), 'Printing and mail', P_, 'Shared', 'Fundraising', 2400 * f_, campaign='Summer Camp Appeal', appeal='Camp scholarship letter', note='Camp letter')
        if m.month == 8: add(D(m.year, 8, 8), 'Printing and mail', P_, 'Shared', 'Fundraising', 900 * f_, campaign='Back-to-School Drive', appeal='School supply drive', note='Drive flyers')
        if m.month == 9: add(D(m.year, 9, 10), 'Printing and mail', P_, 'Shared', 'Fundraising', 1600 * f_, campaign='General giving', appeal='Pantry harvest letter', note='Harvest letter')
        if m.month == 1: add(D(m.year, 1, 20), 'Printing and mail', P_, 'Shared', 'Management', 1400 * f_, note='Giving statements print and mail')
        if m.month in (3, 6, 9, 12): add(D(m.year, m.month, 20), 'Printing and mail', P_, 'Shared', 'Fundraising', 1500 * f_, campaign='General giving', appeal='Thank-you and renewal', note='Quarterly newsletter')
    # card and online fees from the gifts paid by card
    cardm = {}
    for g in w['gifts']:
        if g['method'] == 'Card': cardm[_ms(g['date'])] = cardm.get(_ms(g['date']), 0.0) + g['amount']
    for m in months:
        if cardm.get(m): add(min(D(m.year, m.month, 27), TODAY), 'Card and online fees', 'Payment provider', 'Shared', 'Fundraising', cardm[m] * CARD_FEE_PCT + 45, note='Fees on card gifts')
    # event costs
    ev_plan = {'Gala': [('Venue hire', .22, -2), ('Dinner and drinks', .40, 6), ('Stage, sound and lighting', .14, 0), ('Decor and flowers', .08, -1), ('Entertainment', .06, 0), ('Auction and printing', .06, -20), ('Insurance and permits', .04, -30)],
               'Fun run': [('Route and marshals', .34, 0), ('Shirts and medals', .26, -25), ('Sound and staging', .16, 0), ('Refreshments', .15, 0), ('Printing and signs', .09, -30)],
               'Giving day': [('Online giving fees', .45, 3), ('Phone bank refreshments', .20, 0), ('Online ads', .35, -10)]}
    for e in w['events']:
        if e['status'] == 'Planned':
            if e['kind'] == 'Gala' and (e['date'] - TODAY).days <= 200: add(TODAY - day(14), 'Event costs', VENDOR['Event venue'], 'Shared', 'Fundraising', 4000.0, event=e['event_id'], campaign=e['campaign'], note='Venue deposit')
            continue
        budget = e['budget_cost']
        if e['kind'] == 'Gala': total = budget * (1.27 if e['event_id'] == w['story_gala'] else r.uniform(.95, 1.0))
        elif e['kind'] == 'Fun run': total = budget * r.uniform(.96, 1.04)
        else: total = budget * r.uniform(.92, 1.05)
        e['actual_cost'] = R2(total)
        for nm, sh, off in ev_plan[e['kind']]:
            v = VENDOR['Event venue'] if 'Venue' in nm else VENDOR['Caterer'] if 'Dinner' in nm or 'Refresh' in nm else VENDOR['Printer and mail house'] if 'printing' in nm.lower() else 'Event suppliers'
            if e['event_id'] == w['story_gala'] and nm.startswith('Dinner'): sh = sh + .06
            add(e['date'] + day(off), 'Event costs', v, 'Shared', 'Fundraising', total * sh * r.uniform(.97, 1.03), event=e['event_id'], campaign=e['campaign'], note=nm)
    ex.sort(key=lambda x: (x['date'], x['category'], x['amount']))
    for i, x in enumerate(ex): x['expense_id'] = 'EX-%05d' % (i + 1); x['month'] = _ms(x['date'])
    w['expenses'] = ex


# ------------------------------------------------------------------ stage 7: members and dues, funds (restricted balances, overdrawn story), cash, bank, forecast, budgets
_DUES = {'Friend': 40.0, 'Supporter': 100.0, 'Patron': 250.0}


def _stage_members(w):
    r = rng('members'); pool = w['pool']; mem, dues = [], []
    cand = [i for i, d in enumerate(pool) if d['type'] in ('Individual', 'Household') and d['status'] in ('Active', 'Lapsed') and not d['special']]
    r.shuffle(cand)
    for k, di in enumerate(cand[:118]):
        lvl = _wc(r, MEMBER_LEVELS, [.5, .38, .12]); joined = TODAY - day(r.randint(120, 1700))
        pm, pd = r.randint(1, 12), r.randint(1, 28)
        mem.append(dict(di=di, level=lvl, joined=joined, pm=pm, pd=pd, lapsed=k >= 106, overdue=(k % 12 == 5 and k < 106)))
    for m in mem:
        due_this = D(Y, m['pm'], m['pd'])
        last = None
        for y in range(max(joined_y := m['joined'].year, Y - 2), Y + 1):
            dd = D(y, m['pm'], m['pd'])
            if dd < m['joined'] + day(60): continue
            if m['lapsed'] and y >= Y - 1: continue
            if m['overdue'] and y == Y: continue
            pay = dd + day(r.randint(0, 9))
            if pay <= TODAY: dues.append(dict(m=m, date=pay, amount=_DUES[m['level']], year=y, method=_wc(r, ['Card', 'Check or cheque', 'Bank transfer'], [.6, .2, .2]))); last = pay
        m['last'] = last
        if m['lapsed']: m['due'] = D(Y - 1, m['pm'], m['pd']) if D(Y - 1, m['pm'], m['pd']) > (last or D(Y - 3, 1, 1)) else D(Y, m['pm'], m['pd'])
        elif m['overdue']: m['due'] = due_this if due_this <= TODAY else D(Y - 1, m['pm'], m['pd'])
        else: m['due'] = due_this if due_this > TODAY or (last and last < due_this - day(60)) else D(Y + 1, m['pm'], m['pd'])
        if not m['lapsed'] and not m['overdue'] and m['due'] <= TODAY: m['due'] = D(Y + 1, m['pm'], m['pd'])
        if m['lapsed']: st = 'Lapsed'
        elif m['due'] <= TODAY: st = 'Overdue'
        elif (m['due'] - TODAY).days <= 30: st = 'Due soon'
        else: st = 'Paid'
        m['status'] = st
    mem.sort(key=lambda m: m['joined'])
    for i, m in enumerate(mem): m['member_id'] = 'MB-%03d' % (i + 1)
    dues.sort(key=lambda x: (x['date'], x['m']['member_id']))
    for i, x in enumerate(dues): x['dues_id'] = 'MP-%04d' % (i + 1)
    w['members'] = mem; w['dues'] = dues


def _stage_funds(w):
    r = rng('funds'); months = _months_between(HISTORY_START, TODAY)
    rec = []   # (date, fund, amount, kind)
    for g in w['gifts']:
        if g['date'] < HISTORY_START: continue
        rec.append((g['date'], g['fund'] if g['fund'] else GENERAL, g['amount'], 'gift'))
    for p in w['gpays']:
        if p['received_on'] and HISTORY_START <= p['received_on'] <= TODAY: rec.append((p['received_on'], p['grant']['fund'], p['amount'], 'grant'))
    for t in w['tickets']: rec.append((t['sold_on'], GENERAL, t['qty'] * t['price_each'], 'event'))
    for s in w['sponsors']:
        if s['received_on'] and s['received_on'] <= TODAY and s['received']: rec.append((s['received_on'], GENERAL, s['received'], 'event'))
    for a in w['auction']:
        if a['sold'] and a['event']['date'] <= TODAY: rec.append((a['event']['date'], GENERAL, a['sold'], 'event'))
    for x in w['dues']: rec.append((x['date'], GENERAL, x['amount'], 'dues'))
    transfers = [dict(date=D(Y - 2, 12, 20), amount=12000.0, note='Board moves surplus to the facilities reserve'), dict(date=D(Y - 1, 12, 18), amount=15000.0, note='Board adds to the facilities reserve')]
    transfers = [t for t in transfers if t['date'] <= TODAY]
    for i, t in enumerate(transfers): t['transfer_id'] = 'TR-%02d' % (i + 1)
    stamp = TODAY - day(18)

    def run(over):
        bal = {f['fund']: f['opening_balance'] for f in funds if f['fund'] != GENERAL}; bal[GENERAL] = 0.0
        ev = [(d, 0, f, a, k, None) for d, f, a, k in rec] + [(t['date'], 0, RESERVE_FUND, t['amount'], 'transfer', None) for t in transfers] + [(t['date'], 1, GENERAL, -t['amount'], 'transfer-out', None) for t in transfers]
        ev += [(x['date'], 2, None, x['amount'], 'exp', x) for x in w['expenses']]
        ev.append((stamp, 3, 'Kitchen Equipment Fund', over, 'over', None))
        ev.sort(key=lambda e: (e[0], e[1]))
        info = dict(at_stamp=0.0, after=0.0)
        for d, o, f, a, k, x in ev:
            if k == 'exp':
                cand = x['cand'] or GENERAL
                if cand in RESTRICTED_FUNDS and bal[cand] >= a: x['fund'] = cand
                else: x['fund'] = GENERAL
                bal[x['fund']] -= a
            elif k == 'over':
                info['at_stamp'] = bal[f]; bal[f] -= a
            else:
                bal[f] += a
                if f == 'Kitchen Equipment Fund' and d > stamp and k in ('gift', 'grant'): info['after'] += a
        return bal, info
    for x in w['expenses']: x['fund'] = GENERAL
    _, info = run(0.0)
    over = max(0.0, info['at_stamp'] + info['after'] + 3150.0)
    for x in w['expenses']: x['fund'] = GENERAL
    bal, info2 = run(over)
    over_row = dict(date=stamp, category='Program supplies', vendor='Kitchen equipment supplier', program='Family Food Pantry', function='Program', amount=R2(over), grant=None, event=None, campaign='', appeal='',
                    note='Commercial dishwasher and shelving', cand='Kitchen Equipment Fund', fund='Kitchen Equipment Fund')
    w['expenses'].append(over_row)
    w['expenses'].sort(key=lambda x: (x['date'], x['category'], x['amount']))
    for i, x in enumerate(w['expenses']): x['expense_id'] = 'EX-%05d' % (i + 1); x['month'] = _ms(x['date'])
    w['over_amount'] = R2(over)
    # monthly fund table
    fm = {}; run_bal = {f['fund']: f['opening_balance'] for f in funds if f['fund'] != GENERAL}; run_bal[GENERAL] = 0.0
    events = []
    for d, f, a, k in rec: events.append((d, f, a, 'in' if k != 'x' else 'in'))
    for t in transfers: events += [(t['date'], RESERVE_FUND, t['amount'], 'tr'), (t['date'], GENERAL, -t['amount'], 'tr')]
    for x in w['expenses']: events.append((x['date'], x['fund'], x['amount'], 'out'))
    agg = {}
    for d, f, a, k in events:
        key = (_ms(d), f); e = agg.setdefault(key, dict(receipts=0.0, released=0.0, transfers=0.0))
        if k == 'in': e['receipts'] += a
        elif k == 'out': e['released'] += a
        else: e['transfers'] += a
    rows = []
    for m in months:
        for f in funds:
            e = agg.get((m, f['fund']), dict(receipts=0.0, released=0.0, transfers=0.0))
            run_bal[f['fund']] = run_bal[f['fund']] + e['receipts'] - e['released'] + e['transfers']
            rows.append(dict(month=m, fund=f['fund'], receipts=R2(e['receipts']), released=R2(e['released']), transfers=R2(e['transfers']), balance=R2(run_bal[f['fund']])))
    # bank lines
    lines = []
    for b in w['batches']:
        if b['banked_on'] != '' and b['banked_on'] >= HISTORY_START: lines.append((b['banked_on'], 'Gift deposit', 'Gift deposit, week of %s' % b['week_start'].isoformat(), b['banked'], 0.0))
    for p in w['gpays']:
        if p['received_on'] and p['received_on'] >= HISTORY_START: lines.append((p['received_on'], 'Grant payment', 'Grant payment %s' % p['grant']['grant_id'], p['amount'], 0.0))
    evr = {}
    for t in w['tickets']: evr[(week_start(t['sold_on']), t['event']['event_id'])] = evr.get((week_start(t['sold_on']), t['event']['event_id']), 0.0) + t['qty'] * t['price_each']
    for k, v in evr.items(): lines.append((min(k[0] + day(4), TODAY), 'Event receipts', 'Ticket sales %s' % k[1], v, 0.0))
    for s in w['sponsors']:
        if s['received_on'] and s['received_on'] <= TODAY and s['received']: lines.append((s['received_on'], 'Event receipts', 'Sponsor payment %s' % s['event']['event_id'], s['received'], 0.0))
    ak = {}
    for a in w['auction']:
        if a['sold'] and a['event']['date'] <= TODAY: ak[a['event']['event_id']] = ak.get(a['event']['event_id'], 0.0) + a['sold']
    for k, v in ak.items(): lines.append((min([e['date'] for e in w['events'] if e['event_id'] == k][0] + day(2), TODAY), 'Event receipts', 'Auction receipts %s' % k, v, 0.0))
    dk = {}
    for x in w['dues']: dk[week_start(x['date'])] = dk.get(week_start(x['date']), 0.0) + x['amount']
    for k, v in dk.items(): lines.append((min(k + day(4), TODAY), 'Membership dues', 'Membership dues, week of %s' % k.isoformat(), v, 0.0))
    kind_of = {'Staff pay': 'Payroll', 'Rent and utilities': 'Rent and bills', 'Insurance': 'Rent and bills', 'Technology and phones': 'Rent and bills', 'Card and online fees': 'Fees and transfers'}
    og = {}
    for x in w['expenses']:
        k = kind_of.get(x['category'], 'Supplier payments')
        if x['category'] == 'Professional fees' and x['note'] == 'Bank account fees': k = 'Fees and transfers'
        key = (x['date'], k) if k == 'Payroll' else (min(week_start(x['date']) + day(4), TODAY), k)
        og[key] = og.get(key, 0.0) + x['amount']
    for (d, k), v in og.items(): lines.append((d, k, '%s' % ('Payroll run' if k == 'Payroll' else k + ' paid'), 0.0, R2(v)))
    lines.sort(key=lambda l: (l[0], l[1]))
    run_ = 0.0; bank = []
    for i, (d, k, desc, a_in, a_out) in enumerate(lines):
        run_ += a_in - a_out
        bank.append(dict(date=d, kind=k, description=desc, money_in=R2(a_in), money_out=R2(a_out), _run=run_))
    # cash by month
    last = {}
    for b in bank: last[_ms(b['date'])] = b['_run']
    cum, prev = 0.0, 0.0; cashm = {}
    for m in months:
        if m in last: prev = last[m]
        cashm[m] = prev
    expm = {m: sum(x['amount'] for x in w['expenses'] if x['month'] == m) for m in months}
    restr = {m: sum(r_['balance'] for r_ in rows if r_['month'] == m and r_['fund'] in RESTRICTED_FUNDS) for m in months}
    desg = {m: sum(r_['balance'] for r_ in rows if r_['month'] == m and r_['fund'] == RESERVE_FUND) for m in months}
    full = [m for m in months if m < _ms(TODAY)][-12:]
    avg_exp12 = sum(expm[m] for m in full) / 12.0
    free_target = 3.45 * avg_exp12
    cash_now = free_target + restr[months[-1]] + desg[months[-1]]
    open_bank = cash_now - cashm[months[-1]]
    cash_rows = []
    prev_close = open_bank
    for i, m in enumerate(months):
        close = cashm[m] + open_bank
        rin = sum(b['money_in'] for b in bank if _ms(b['date']) == m); rout = sum(b['money_out'] for b in bank if _ms(b['date']) == m)
        trail = [expm[mm] for mm in months if mm < m][-12:] or [expm[m]]
        avg = sum(trail) / len(trail)
        free = close - restr[m] - desg[m]
        cash_rows.append(dict(month=m, opening=R2(prev_close), receipts=R2(rin), payments=R2(rout), closing=R2(close), restricted=R2(restr[m]), designated=R2(desg[m]), free_money=R2(free),
                              avg_monthly_expense=R2(avg), reserve_months=R2(free / avg) if avg else 0.0))
        prev_close = close
    for i, c_ in enumerate(cash_rows): c_['cash_id'] = 'CF-%03d' % (i + 1)
    for i, b in enumerate(bank):
        b['balance'] = R2(b['_run'] + open_bank); b['bank_id'] = 'BK-%05d' % (i + 1); b['month'] = _ms(b['date']); b['reconciled'] = b['date'] <= TODAY - day(45)
    # General fund opening so that its balance equals free money now
    g_flow = sum(r_['receipts'] - r_['released'] + r_['transfers'] for r_ in rows if r_['fund'] == GENERAL)
    g_open = R2(cash_rows[-1]['free_money'] - g_flow)
    FUND[GENERAL]['opening_balance'] = g_open
    funds[0]['opening_balance'] = g_open
    shift = g_open
    for r_ in rows:
        if r_['fund'] == GENERAL: r_['balance'] = R2(r_['balance'] + shift)
    for i, r_ in enumerate(rows): r_['row_id'] = 'FM-%04d' % (i + 1)
    w['fm'] = rows; w['bank'] = bank; w['cash'] = cash_rows; w['transfers'] = transfers; w['avg_exp12'] = avg_exp12; w['free_now'] = cash_rows[-1]['free_money']
    w['fund_now'] = {f['fund']: [r_['balance'] for r_ in rows if r_['fund'] == f['fund'] and r_['month'] == months[-1]][0] for f in funds}


# ------------------------------------------------------------------ stage 8: forecast, budgets
def _area_of(x):
    """expense row -> {budget area: share}"""
    if x['function'] == 'Program':
        if x['program'] in PROGRAMS: return {x['program']: 1.0}
        return {p: .25 for p in PROGRAMS}
    if x['function'] == 'Management': return {'Management': 1.0}
    if x['function'] == 'Fundraising': return {'Fundraising': 1.0}
    c = CAT[x['category']]
    out = {'Management': c['management_share'], 'Fundraising': c['fundraising_share']}
    for p, sh in zip(PROGRAMS, (.30, .30, .25, .15)): out[p] = c['program_share'] * sh
    return {k: v for k, v in out.items() if v}


def _stage_plan(w):
    r = rng('plan'); months = _months_between(HISTORY_START, TODAY)
    cur = _ms(TODAY); h0 = add_months(cur, -12); h1 = cur - day(1)
    fm_ = [add_months(cur, k) for k in range(1, 13)]
    gen = {m: 0.0 for m in range(1, 13)}
    for g in w['gifts']:
        if h0 <= g['date'] <= h1 and g['fund'] in ('', GENERAL) and g['gtype'] in ('One-time', 'Event gift'): gen[g['date'].month] += g['amount']
    rec_base = sum(x['amount'] for x in w['rec'] if x['status'] == 'Active' and x['fund'] == GENERAL)
    pled = {}
    for x in w['pp']:
        if x['status'] in ('Due', 'Overdue') and x['pledge']['fund'] == GENERAL:
            k = _ms(x['due']) if x['due'] > TODAY else _ms(TODAY) + day(32)
            pled[_ms(k)] = pled.get(_ms(k), 0.0) + x['amount_due']
    gr = {}
    for p in w['gpays']:
        if p['status'] in ('Due', 'Late') and p['grant']['fund'] == GENERAL:
            k = _ms(p['due']) if p['due'] > TODAY else fm_[0]
            gr[k] = gr.get(k, 0.0) + p['amount']
    dues = {}
    for m in w['members']:
        if m['status'] != 'Lapsed': dues[_ms(m['due'] if m['due'] > TODAY else add_months(m['due'], 12))] = dues.get(_ms(m['due'] if m['due'] > TODAY else add_months(m['due'], 12)), 0.0) + _DUES[m['level']]
    ev_rev = {}
    for e in w['events']:
        if e['status'] != 'Done': continue
        rev = sum(t['qty'] * t['price_each'] for t in w['tickets'] if t['event'] is e) + sum(s['received'] for s in w['sponsors'] if s['event'] is e) + sum(a['sold'] for a in w['auction'] if a['event'] is e)
        ev_rev[e['event_id']] = rev
    last_by_kind = {}
    for e in w['events']:
        if e['status'] == 'Done': last_by_kind[e['kind']] = e
    exp_gen = {}
    for x in w['expenses']:
        if h0 <= x['date'] <= h1 and x['fund'] == GENERAL and x['category'] != 'Event costs': exp_gen[x['date'].month] = exp_gen.get(x['date'].month, 0.0) + x['amount']
    avg_gen = sum(exp_gen.values()) / 12.0
    tot_by_m = {}
    for x in w['expenses']:
        if h0 <= x['date'] <= h1 and x['category'] != 'Event costs': tot_by_m[x['date'].month] = tot_by_m.get(x['date'].month, 0.0) + x['amount']
    avg_tot = sum(tot_by_m.values()) / 12.0
    exp12 = sum(x['amount'] for x in w['expenses'] if h0 <= x['date'] <= h1) / 12.0
    rows = []
    free = w['free_now']
    for k, m in enumerate(fm_):
        ev_net = 0.0; ev_note = ''
        for e in w['events']:
            if e['status'] == 'Planned' and _ms(e['date']) == m:
                lk = last_by_kind.get(e['kind'])
                rev = ev_rev.get(lk['event_id'], 0.0) * 1.04 if lk else 0.0
                ev_net += rev - e['budget_cost']; ev_note = e['event']
        for fr in _fun_run_dates()[-1:]:
            nxt = fr + day(364)
            if _ms(nxt) == m and TODAY < nxt:
                lk = last_by_kind.get('Fun run'); rev = ev_rev.get(lk['event_id'], 0.0) * 1.04 if lk else 0.0
                ev_net += rev - 9800.0; ev_note = 'Fun Run'
        seas = (.5 + .5 * tot_by_m.get(m.month, avg_tot) / avg_tot) if avg_tot else 1.0
        rows.append(dict(month=m, gifts=R2(gen[m.month] * 1.04), recurring=R2(rec_base), pledges_due=R2(pled.get(m, 0.0)), grants=R2(gr.get(m, 0.0)), event_net=R2(ev_net), dues=R2(dues.get(m, 0.0)),
                         expenses=R2(avg_gen * seas * 1.04), one_off=0.0, one_off_note='', event=ev_note))
    avg_f = exp12 * 1.04
    def path(rows_):
        f = free; out = []
        for x in rows_:
            f = f + x['gifts'] + x['recurring'] + x['pledges_due'] + x['grants'] + x['event_net'] + x['dues'] - x['expenses'] - x['one_off']
            out.append(f)
        return out
    nat = path(rows)
    # the story month: the middle month of the next calendar quarter; the biggest instalment due in that quarter arrives three months late and a planned one-off falls in the story month
    nq_first = add_months(D(TODAY.year, ((TODAY.month - 1) // 3) * 3 + 1, 1), 3)
    sm = add_months(nq_first, 1)
    si = [i for i, x in enumerate(rows) if x['month'] == sm][0]
    qi = [i for i, x in enumerate(rows) if nq_first <= x['month'] < add_months(nq_first, 3)]
    big = max(qi, key=lambda i: rows[i]['grants'])
    if rows[big]['grants'] > 0 and big + 3 < len(rows):
        rows[big + 3]['grants'] = R2(rows[big + 3]['grants'] + rows[big]['grants']); rows[big]['delayed'] = rows[big]['grants']; rows[big]['grants'] = 0.0
    nat2 = path(rows)
    amt = min(95000.0, max(20000.0, round((nat2[si] - 2.85 * avg_f) / 500.0) * 500.0))
    rows[si]['one_off'] = amt; rows[si]['one_off_note'] = 'Replace the delivery van and pay the annual cover'
    p = path(rows)
    for i, x in enumerate(rows):
        x['closing_free'] = R2(p[i]); x['reserve_months'] = R2(p[i] / avg_f)
        x['forecast_id'] = 'FC-%02d' % (i + 1)
    w['forecast'] = rows; w['avg_f'] = avg_f; w['story_month'] = sm; w['nat_path'] = nat
    # budgets by area and month (a mix of the year's own average and the month, a plain budget the board approved)
    area_m = {}
    for x in w['expenses']:
        for a, sh in _area_of(x).items(): area_m[(a, x['month'])] = area_m.get((a, x['month']), 0.0) + x['amount'] * sh
    bud = []
    for a in BUDGET_AREAS:
        for m in months:
            yr = [area_m.get((a, mm), 0.0) for mm in months if mm.year == m.year and mm <= _ms(TODAY)]
            avg = sum(yr) / max(1, len(yr))
            b = (0.45 * area_m.get((a, m), 0.0) + 0.55 * avg) * r.uniform(.96, 1.07)
            bud.append(dict(month=m, area=a, budget=float(round(b / 10) * 10)))
    bud.sort(key=lambda x: (x['month'], BUDGET_AREAS.index(x['area'])))
    for i, x in enumerate(bud): x['budget_id'] = 'BG-%04d' % (i + 1)
    inc = {}
    for g in w['gifts']:
        if g['date'] < HISTORY_START: continue
        t = w['pool'][g['di']]['type']
        ln = 'Individuals' if t in ('Individual', 'Household') else 'Business and groups'
        inc[(ln, _ms(g['date']))] = inc.get((ln, _ms(g['date'])), 0.0) + g['amount']
    for p_ in w['gpays']:
        if p_['received_on'] and p_['received_on'] >= HISTORY_START: inc[('Grants', _ms(p_['received_on']))] = inc.get(('Grants', _ms(p_['received_on'])), 0.0) + p_['amount']
    for t in w['tickets']: inc[('Events', _ms(t['sold_on']))] = inc.get(('Events', _ms(t['sold_on'])), 0.0) + t['qty'] * t['price_each']
    for s in w['sponsors']:
        if s['received_on'] and s['received_on'] <= TODAY: inc[('Events', _ms(s['received_on']))] = inc.get(('Events', _ms(s['received_on'])), 0.0) + s['received']
    for a in w['auction']:
        if a['sold'] and a['event']['date'] <= TODAY: inc[('Events', _ms(a['event']['date']))] = inc.get(('Events', _ms(a['event']['date'])), 0.0) + a['sold']
    for d_ in w['dues']: inc[('Dues and other', _ms(d_['date']))] = inc.get(('Dues and other', _ms(d_['date'])), 0.0) + d_['amount']
    ib = []
    for ln in INCOME_LINES:
        for m in months:
            yr = [inc.get((ln, mm), 0.0) for mm in months if mm.year == m.year and mm <= _ms(TODAY)]
            avg = sum(yr) / max(1, len(yr))
            b = (0.5 * inc.get((ln, m), 0.0) + 0.5 * avg) * r.uniform(.93, 1.08)
            ib.append(dict(month=m, line=ln, budget=float(round(b / 10) * 10)))
    ib.sort(key=lambda x: (x['month'], INCOME_LINES.index(x['line'])))
    for i, x in enumerate(ib): x['budget_id'] = 'IB-%04d' % (i + 1)
    w['budget'] = bud; w['ibudget'] = ib


# ------------------------------------------------------------------ stage 9: volunteers, shift slots and shifts
def _slots_for(d):
    """(program, shift, needed, hours, role) for one calendar day"""
    wd = d.weekday(); out = []
    if wd in (1, 3): out.append(('Family Food Pantry', 'Morning', 7, 3.0, 'Pantry sorter'))
    if wd == 5: out.append(('Family Food Pantry', 'Morning', 9, 3.5, 'Pantry sorter'))
    if wd < 5:
        out.append(('Senior Meals and Visits', 'Morning', 3, 3.0, 'Meal driver')); out.append(('Senior Meals and Visits', 'Afternoon', 4, 3.0, 'Meal driver'))
    if wd < 4 and d.month not in (7, 8): out.append(('After-School Learning', 'Afternoon', 5, 2.5, 'Tutor'))
    if wd < 5 and D(d.year, 6, 24) <= d <= D(d.year, 8, 16): out.append(('Summer Youth Camp', 'Morning', 8, 4.0, 'Camp helper'))
    if wd == 2: out.append(('Office', 'Morning', 2, 3.0, 'Office helper'))
    return out


def _stage_volunteers(w):
    r = rng('vols'); pool = w['pool']; vols = []
    linked = [i for i, d in enumerate(pool) if d['type'] in ('Individual', 'Household') and d['status'] in ('Active', 'Lapsed') and not d['special']]
    r.shuffle(linked); linked = linked[:75]
    names = set(); roles = VOL_ROLES; rw = [.26, .16, .14, .13, .2, .07, .04]
    for k in range(350):
        if k < len(linked): di = linked[k]; nm = pool[di]['contact']; ph = fake_phone(2000 + k); em = fake_email(nm, 0)
        else:
            di = None
            while True:
                nm = r.choice(_FIRST) + ' ' + r.choice(_LAST)
                if nm not in names and nm not in used_names(pool): break
            ph = fake_phone(2000 + k); em = fake_email(nm, k)
        names.add(nm)
        role = _wc(r, roles, rw)
        start = TODAY - day(r.randint(5, 2000))
        if k < 240: end = None
        else: end = max(start + day(60), HISTORY_START + day(r.randint(0, (TODAY - HISTORY_START).days - 120)))
        vols.append(dict(name=nm, phone=ph, email=em, role=role, start=start, end=end if (end and end < TODAY - day(100)) else (None if k < 240 else TODAY - day(130)), di=di, freq=r.choice([.6, 1, 1.5, 2, 2, 3, 4]),
                         avail=_wc(r, AVAIL, [.3, .22, .18, .3]), brk=None))
    # on break: twelve volunteers who have not come for 100 to 200 days
    for v in vols[:240][-14:]: v['brk'] = (TODAY - day(r.randint(100, 200)), TODAY + day(30))
    vols.sort(key=lambda v: v['start'])
    for i, v in enumerate(vols): v['volunteer_id'] = 'VL-%03d' % (i + 1)
    byrole = {}
    for v in vols: byrole.setdefault(v['role'], []).append(v)
    byrole['Office helper'] = byrole.get('Office helper', []) + byrole.get('Web and data', [])
    slots, shifts = [], []
    d_ = month_start(23)
    d_ = D(d_.year, d_.month, 1); end_d = TODAY + day(21)
    events_days = {e['date']: e for e in w['events']}
    while d_ <= end_d:
        sl = list(_slots_for(d_))
        e = events_days.get(d_)
        if e: sl.append(('Events', 'Afternoon' if e['kind'] != 'Fun run' else 'Morning', {'Gala': 24, 'Fun run': 35, 'Giving day': 8}[e['kind']], 5.0 if e['kind'] != 'Giving day' else 3.0, 'Event helper'))
        for prog, sh, need, hrs, role in sl:
            elig = [v for v in byrole.get(role, []) if v['start'] <= d_ and (v['end'] is None or d_ <= v['end']) and not (v['brk'] and v['brk'][0] <= d_ <= v['brk'][1])]
            future = d_ > TODAY
            fill = r.uniform(.35, 1.0) if future else (r.uniform(.5, .8) if r.random() < .06 else r.uniform(.85, 1.0))
            k = min(len(elig), max(0, int(round(need * fill))))
            keyed = sorted(elig, key=lambda v: -(r.random() ** (1.0 / v['freq'])))[:k]
            slots.append(dict(date=d_, program=prog, shift=sh, needed=need, signed=len(keyed), hours=hrs, role=role))
            for v in keyed:
                st = 'Booked' if d_ >= TODAY else ('No-show' if r.random() < .045 else 'Worked')
                shifts.append(dict(date=d_, vol=v, program=prog, shift=sh, hours=hrs if st != 'No-show' else 0.0, status=st, role=role))
        d_ += day(1)
    for i, s in enumerate(slots): s['slot_id'] = 'SL-%05d' % (i + 1)
    for i, s in enumerate(shifts): s['shift_id'] = 'SF-%05d' % (i + 1); s['week'] = week_start(s['date']); s['month'] = _ms(s['date'])
    last = {}
    for s in shifts:
        if s['status'] == 'Worked': last[s['vol']['volunteer_id']] = s['date']
    for v in vols:
        v['last_shift'] = last.get(v['volunteer_id'], '')
        if v['last_shift'] != '' and (TODAY - v['last_shift']).days <= 90: v['status'] = 'Active'
        elif v['brk']: v['status'] = 'On break'
        else: v['status'] = 'Lapsed'
    w['vols'] = vols; w['slots'] = slots; w['vshifts'] = shifts


def used_names(pool):
    if '_names' not in _CACHE: _CACHE['_names'] = set(d['contact'] for d in pool) | set(d['name'] for d in pool)
    return _CACHE['_names']


# ------------------------------------------------------------------ stage 10: participants, sessions, outcomes
def _stage_programs(w):
    r = rng('people'); parts = []
    months = _months_between(HISTORY_START, TODAY)
    def add(prog, start, end, fn, status):
        parts.append(dict(program=prog, start=start, end=end, fn=fn, status=status, vis={}))
    # After-School: school-year cohorts
    for y in range(Y - 2, Y + 1):
        for st_m, n in ((9, 46), (1, 14)):
            st = D(y, st_m, r.randint(3, 20))
            if st > TODAY: continue
            for _ in range(n):
                length = r.choice([4, 9, 10, 16, 21])
                en = add_months(st, length)
                add('After-School Learning', st, en if en < TODAY - day(10) else None, 'visits_as', 'Completed' if r.random() < .75 else 'Left')
    for m in months:
        for _ in range(r.randint(30, 44)):
            st = D(m.year, m.month, r.randint(1, 28))
            if st > TODAY: st = TODAY - day(r.randint(0, 6))
            en = add_months(st, r.randint(2, 12))
            add('Family Food Pantry', st, en if en < TODAY - day(10) else None, 'visits_fp', 'Completed' if r.random() < .6 else 'Left')
        for _ in range(r.randint(3, 7)):
            st = D(m.year, m.month, r.randint(1, 28))
            if st > TODAY: st = TODAY - day(r.randint(0, 6))
            en = add_months(st, r.randint(6, 40))
            add('Senior Meals and Visits', st, en if en < TODAY - day(10) else None, 'visits_sm', 'Completed' if r.random() < .5 else 'Left')
    for y in range(Y - 2, Y + 1):
        if D(y, 6, 24) > TODAY: continue
        for _ in range(int(88 + (y - (Y - 2)) * 4)):
            add('Summer Youth Camp', D(y, 6, 24) + day(r.choice([0, 0, 0, 14, 28])), D(y, 8, 16), 'visits_sc', 'Completed')
    # monthly visits
    for p in parts:
        for m in months:
            lo = _ms(p['start']); hi = _ms(p['end']) if p['end'] else _ms(TODAY)
            if m < lo or m > hi: continue
            if p['fn'] == 'visits_as': v = 0 if m.month in (7, 8) else r.randint(7, 15)
            elif p['fn'] == 'visits_fp': v = _wc(r, [0, 1, 2, 3, 4], [.2, .35, .27, .12, .06])
            elif p['fn'] == 'visits_sm': v = r.randint(8, 21) if m.month in (11, 12, 1, 2) else r.randint(7, 19)
            else: v = r.randint(8, 16) if m.month in (6, 7, 8) else 0
            if m == lo and p['fn'] != 'visits_sc': v = max(1, v // 2 + 1) if v else 0
            if v and m == _ms(TODAY): v = min(v, max(1, (TODAY.day * v) // 30))
            if v: p['vis'][m] = v
    parts = [p for p in parts if p['vis']]
    # waiting lists
    for prog, n in (('After-School Learning', 9), ('Summer Youth Camp', 14), ('Senior Meals and Visits', 6)):
        for _ in range(n): parts.append(dict(program=prog, start='', end=None, fn='wait', status='Waiting', vis={}))
    parts.sort(key=lambda p: (p['start'] or TODAY + day(1), p['program']))
    for i, p in enumerate(parts):
        p['participant_id'] = 'PT-%04d' % (i + 1)
        nm = r.choice(_FIRST) + ' ' + r.choice('ABCDEFGHIJKLMNOPRSTVWYZ') + '.'
        p['name'] = nm; p['phone'] = fake_phone(4000 + i)
        if p['vis']:
            lm = max(p['vis']); p['sessions'] = sum(p['vis'].values())
            p['last'] = min(D(lm.year, lm.month, r.randint(1, min(28, calendar.monthrange(lm.year, lm.month)[1]))), TODAY)
            if lm == _ms(TODAY): p['last'] = TODAY - day(r.randint(0, 12))
            active = p['end'] is None
            if active:
                p['status'] = 'Active'
                age = (TODAY - p['last']).days
                p['contact'] = 'Up to date' if age <= 30 else 'Check in' if age <= 60 else 'Lost touch'
            else: p['contact'] = 'Up to date' if p['status'] == 'Completed' else 'Lost touch'
        else:
            p['sessions'] = 0; p['last'] = ''; p['contact'] = 'Up to date'
    # a little extra: a few active pantry households and seniors have not been seen for a while
    act = [p for p in parts if p['status'] == 'Active' and p['program'] in ('Family Food Pantry', 'Senior Meals and Visits')]
    for k, p in enumerate(act[:18]):
        if p['vis'] and _ms(p['start']) < add_months(_ms(TODAY), -3):
            cut = TODAY - day(35 + 4 * k)
            for m in list(p['vis']):
                if m > _ms(cut): del p['vis'][m]
            if p['vis']:
                lm = max(p['vis']); p['sessions'] = sum(p['vis'].values()); p['last'] = min(cut, _eom(lm)); age = (TODAY - p['last']).days
                p['contact'] = 'Up to date' if age <= 30 else 'Check in' if age <= 60 else 'Lost touch'
    # program months
    cap = {p['program']: p['capacity'] for p in programs}
    pm = []
    sess_days = {}
    for m in months:
        for prog in PROGRAMS:
            ds = []
            d_ = m
            while d_ <= _eom(m) and d_ <= TODAY:
                wd = d_.weekday()
                ok = (prog == 'After-School Learning' and wd < 4 and m.month not in (7, 8)) or (prog == 'Family Food Pantry' and wd in (1, 3, 5)) or (prog == 'Senior Meals and Visits' and wd < 5) \
                    or (prog == 'Summer Youth Camp' and wd < 5 and D(m.year, 6, 24) <= d_ <= D(m.year, 8, 16))
                if ok: ds.append(d_)
                d_ += day(1)
            sess_days[(prog, m)] = ds
            ps = [p for p in parts if p['program'] == prog and m in p['vis']]
            tot = sum(p['vis'][m] for p in ps)
            new = sum(1 for p in ps if p['start'] != '' and _ms(p['start']) == m)
            pm.append(dict(month=m, program=prog, unique=len(ps), visits=tot, new=new, sessions=len(ds), capacity=cap[prog],
                           waiting=sum(1 for p in parts if p['program'] == prog and p['status'] == 'Waiting') if m == _ms(TODAY) else 0))
    for i, x in enumerate(pm): x['row_id'] = 'PM-%04d' % (i + 1)
    # session rows
    slotvols = {}
    for s in w['slots']: slotvols[(s['date'], s['program'])] = slotvols.get((s['date'], s['program']), 0) + s['signed']
    sess = []
    for x in pm:
        ds = sess_days[(x['program'], x['month'])]
        if not ds or not x['visits']: continue
        wts = [r.uniform(.75, 1.25) for _ in ds]; tw = sum(wts)
        att = [int(round(x['visits'] * wv / tw)) for wv in wts]
        att[-1] += x['visits'] - sum(att)
        for d_, a in zip(ds, att): sess.append(dict(date=d_, month=x['month'], program=x['program'], staff=PROGRAM_LEAD[x['program']], attendees=max(0, a), volunteers=slotvols.get((d_, x['program']), 0)))
    sess.sort(key=lambda s: (s['date'], s['program']))
    for i, s in enumerate(sess): s['session_id'] = 'SS-%05d' % (i + 1)
    # outcomes per quarter
    outc = []
    qs = sorted(set(D(m.year, 3 * ((m.month - 1) // 3) + 1, 1) for m in months))
    for q in qs:
        for prog in PROGRAMS:
            ms = [m for m in months if D(m.year, 3 * ((m.month - 1) // 3) + 1, 1) == q]
            uni = max([x['unique'] for x in pm if x['program'] == prog and x['month'] in ms] or [0])
            vis = sum(x['visits'] for x in pm if x['program'] == prog and x['month'] in ms)
            base = {'After-School Learning': [uni * .8, uni * .85, uni * .5, uni * .7], 'Family Food Pantry': [uni, vis * .22, uni * .12, uni * .5],
                    'Senior Meals and Visits': [vis * .8, vis * .12, uni * .4, uni * .08], 'Summer Youth Camp': [uni * .9, uni * .5, 12, uni * .35]}[prog]
            for nm, b in zip(OUTCOMES[prog], base):
                if prog == 'Summer Youth Camp' and q.month not in (7,) and nm != 'Bursary places filled': b = 0
                tgt = float(round(b * 1.05)) if b else 0.0
                act_ = float(round(b * r.uniform(.82, 1.08))) if b else 0.0
                if (q > D(TODAY.year, 3 * ((TODAY.month - 1) // 3) + 1, 1)) or (q == D(TODAY.year, 3 * ((TODAY.month - 1) // 3) + 1, 1) and False): continue
                outc.append(dict(quarter=q, program=prog, outcome=nm, target=tgt, actual=act_))
    outc = [o for o in outc if o['target'] > 0]
    outc.sort(key=lambda o: (o['quarter'], PROGRAMS.index(o['program']), OUTCOMES[o['program']].index(o['outcome'])))
    for i, o in enumerate(outc): o['outcome_id'] = 'OC-%03d' % (i + 1)
    w['parts'] = parts; w['pm'] = pm; w['sessions'] = sess; w['outcomes'] = outc


# ------------------------------------------------------------------ stage 11: board, meetings, attendance, declarations, obligations, major-gift pipeline
def _third_tuesday(y, m):
    d = D(y, m, 1)
    while d.weekday() != 1: d += day(1)
    return d + day(14)


def _stage_board(w):
    r = rng('board'); pool = w['pool']; board = []
    ends = [TODAY + day(400), TODAY + day(300), TODAY + day(700), TODAY + day(84), TODAY + day(510), TODAY + day(850), TODAY + day(620), TODAY + day(900), TODAY + day(152), TODAY + day(260), TODAY + day(1000)]
    served = [2, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1]
    skills2 = ['Community links', 'Law and policy', 'Marketing', 'Finance', 'Education', 'Technology', 'Community links', 'Fundraising', 'Education', 'Health and care', 'Technology']
    for i, (bid, nm, role, com, skill) in enumerate(_BOARD):
        di = [k for k, d in enumerate(pool) if d['name'] == nm][0]
        board.append(dict(member_id=bid, name=nm, role=role, committee=com, term_end=ends[i], term_start=add_months(ends[i], -36) + day(1), terms_served=served[i], skill=skill, skill2=skills2[i],
                          di=di, phone=fake_phone(6000 + i), email=fake_email(nm), rel={0: .93, 1: .96, 2: .9, 3: .88, 4: .55, 5: .85, 6: .8, 7: .7, 8: .94, 9: .68, 10: .82}[i]))
    meetings = []
    for y in range(Y - 2, Y + 2):
        for m in range(1, 13):
            if m != 8: meetings.append(('Board', _third_tuesday(y, m)))
            if m in (1, 4, 7, 10): meetings.append(('Finance', _next_dow(D(y, m, 8), 3)))
            if m in (2, 5, 9, 11): meetings.append(('Fundraising', _next_dow(D(y, m, 9), 3)))
            if m in (3, 9): meetings.append(('Governance', _next_dow(D(y, m, 14), 2)))
    meetings = sorted([x for x in meetings if HISTORY_START <= x[1] <= TODAY + day(75)], key=lambda x: (x[1], x[0]))
    mt, att = [], []
    for i, (kind, d_) in enumerate(meetings):
        mem = board if kind == 'Board' else [b for b in board if b['committee'] == kind or b['role'] == 'Chair']
        rows = []
        if d_ <= TODAY - day(1):
            for b in mem:
                x = r.random()
                st = 'Present' if x < b['rel'] else ('Apologies' if x < b['rel'] + (1 - b['rel']) * .55 else 'Absent')
                rows.append(dict(meeting='BMT-%03d' % (i + 1), member=b['name'], member_id=b['member_id'], status=st))
        pres = sum(1 for x in rows if x['status'] == 'Present')
        mt.append(dict(meeting_id='BMT-%03d' % (i + 1), date=d_, kind=kind, expected=len(mem), present=pres if rows else 0, quorum=(pres >= (len(mem) // 2 + 1)) if rows else False,
                       minutes=d_ <= TODAY - day(20) or (d_ <= TODAY - day(1) and r.random() < .5), planned=d_ > TODAY - day(1)))
        att.extend(rows)
    for i, x in enumerate(att): x['att_id'] = 'BA-%04d' % (i + 1)
    decl = []
    for b in board:
        for y in (Y - 2, Y - 1, Y):
            due = D(y, 3, 31)
            filed = D(y, 2, r.randint(5, 28)) if (y < Y or r.random() < .7) else ''
            decl.append(dict(member=b['name'], member_id=b['member_id'], year=y, due=due, filed=filed if filed != '' and filed <= TODAY else '', items=r.choice([0, 0, 1, 1, 2]), _b=b))
    for x in decl:
        x['status'] = 'Filed' if x['filed'] else ('Overdue' if x['due'] < TODAY else 'Due')
        if not x['filed']: x['items'] = 0
    decl.sort(key=lambda x: (x['year'], x['member_id']))
    for i, x in enumerate(decl): x['decl_id'] = 'CD-%03d' % (i + 1)
    ob = []
    base = [('Safeguarding policy review', 'Policy review', D(1, 4, 30), 'Governance'), ('Conflict of interest policy review', 'Policy review', D(1, 1, 31), 'Governance'),
            ('Insurance renewal for premises and events', 'Insurance renewal', D(1, 7, 1), 'Finance'), ('Insurance renewal for vehicles', 'Insurance renewal', D(1, 10, 1), 'Finance'),
            ('Yearly information return', 'Yearly return', D(1, 5, 15), 'Finance'), ('Annual report ready for the members', 'Annual report', D(1, 6, 30), 'Fundraising'),
            ('Accounts review by the outside accountant', 'Accounts review', D(1, 3, 15), 'Finance'), ('Board training day', 'Board training', D(1, 9, 20), 'Governance'),
            ('Fire and safety check of the building', 'Safety check', D(1, 8, 25), 'Governance'), ('Volunteer policy review', 'Policy review', D(1, 11, 30), 'Governance'),
            ('Reserve policy review', 'Policy review', D(1, 12, 10), 'Finance')]
    for y in range(Y - 2, Y + 2):
        for nm, kind, d0, own in base:
            due = D(y, d0.month, d0.day)
            if due > TODAY + day(300): continue
            done = due + day(r.randint(-12, 3)) if due < TODAY - day(2) else ''
            ob.append(dict(item=nm, kind=kind, due=due, owner=own, done=done, status='Done' if done != '' else 'Upcoming'))
    # one is overdue: the safeguarding policy review
    cand = [x for x in ob if x['kind'] == 'Policy review' and x['status'] == 'Done' and x['item'].startswith('Volunteer')]
    for x in ob:
        if x['item'].startswith('Volunteer policy review') and x['due'].year == Y - 1: pass
    od = [x for x in ob if x['status'] == 'Upcoming' and x['due'] < TODAY]
    for x in ob:
        if x['status'] == 'Upcoming' and x['due'] < TODAY: x['status'] = 'Overdue'
    if not od:
        t = [x for x in ob if x['kind'] == 'Policy review' and x['due'] < TODAY and x['status'] == 'Done'][-1]
        t.update(done='', status='Overdue', due=TODAY - day(12))
    ob.sort(key=lambda x: (x['due'], x['item']))
    for i, x in enumerate(ob): x['ob_id'] = 'OB-%03d' % (i + 1)
    w['board'] = board; w['meetings'] = mt; w['attend'] = att; w['decl'] = decl; w['oblig'] = ob


def _stage_pipeline(w):
    r = rng('pipeline'); pool = w['pool']; rows = []
    story = [i for i, d in enumerate(pool) if d['special'] == 'story_major'][0]
    cand = [i for i, d in enumerate(pool) if (d['status'] == 'Prospect' and d['type'] != 'Faith or community' and not d['special']) or (d['status'] == 'Active' and d['tier'] in ('mid', 'major') and not d['special'])]
    r.shuffle(cand)
    stages = ['Identified'] * 8 + ['Cultivation'] * 12 + ['Ask made'] * 7 + ['Committed'] * 4 + ['Closed'] * 3
    steps = {'Identified': ['Research and first call', 'Invite to an open day', 'Ask a board member to introduce'], 'Cultivation': ['Coffee meeting', 'Site visit', 'Send an impact update', 'Invite to the gala table'],
             'Ask made': ['Follow up the proposal', 'Thank-you and next meeting', 'Answer questions'], 'Committed': ['Agree the pledge schedule', 'Send the gift agreement'], 'Closed': ['Thank-you call', 'Plan stewardship visit']}
    owners = [DEV_MANAGER, DEV_MANAGER, OWNER, 'Michael Brandt', 'Sunita Rao']
    for k, st in enumerate(stages):
        di = cand[k]; d = pool[di]
        cap = {'major': 20000, 'mid': 6000, 'regular': 2000, 'small': 1000}[d['tier']] * r.choice([1, 1, 1.5, 2, 3])
        if d['tier'] == 'small': cap = r.choice([3000, 5000, 7500])
        cap = float(round(cap / 250) * 250)
        ask = float(round(cap * r.choice([.25, .3, .4, .5]) / 250) * 250) or 1000.0
        nd = TODAY + day(r.randint(-40, 45)) if k % 3 == 0 else TODAY + day(r.randint(2, 60))
        rows.append(dict(di=di, capacity=cap, stage=st, ask=ask, next_step=r.choice(steps[st]), next_date=nd, owner=r.choice(owners), last_contact=TODAY - day(r.randint(4, 120)),
                         expected=TODAY + day(r.randint(20, 240)) if st != 'Closed' else ''))
    rows.append(dict(di=story, capacity=15000.0, stage='Cultivation', ask=7500.0, next_step='Stewardship call', next_date=TODAY - day(21), owner=OWNER, last_contact=TODAY - day(158), expected=TODAY + day(75)))
    rows.sort(key=lambda x: x['next_date'])
    for i, x in enumerate(rows): x['prospect_id'] = 'PR-%03d' % (i + 1)
    w['pipeline'] = rows


def _world():
    w = {}
    for f in (_stage_donors, _stage_gifts, _stage_events, _stage_finalize_gifts, _stage_inkind, _stage_contacts, _stage_grants, _stage_money, _stage_members, _stage_funds, _stage_plan,
              _stage_volunteers, _stage_programs, _stage_board, _stage_pipeline): f(w)
    return w


# ------------------------------------------------------------------ public rows
def _W(): return _raw('world', _world)


def _public():
    w = _W(); P = {}; pool = w['pool']
    did = lambda i: pool[i]['donor_id']; dn = lambda i: pool[i]['name']
    f = w['dfacts']
    first_ch = {}
    for g in w['gifts']:
        if not g.get('_nodonor') and g['di'] not in first_ch: first_ch[g['di']] = g['channel']
    P['donor_rows'] = [dict(donor_id=d['donor_id'], donor=d['name'], type=d['type'], contact=d['contact'], phone=fake_phone(500 + i), email=fake_email(d['contact'], 0 if d['special'] != 'duplicate' else 0),
                            contact_pref=d['pref'], status=d['status'], joined_via=first_ch.get(i, ''), first_gift=iso(f['first'][i]) if i in f['first'] else '', last_gift=iso(f['last'][i]) if i in f['last'] else '',
                            gifts=f['cnt'].get(i, 0), total_given=R2(f['tot'].get(i, 0.0))) for i, d in enumerate(pool)]
    # duplicate records share the e-mail of the first record
    byname = {d['donor']: d for d in P['donor_rows']}
    for i, d in enumerate(pool):
        if d['special'] == 'duplicate' and d.get('dup_of') in byname: P['donor_rows'][i]['email'] = byname[d['dup_of']]['email']
    P['contact_rows'] = [dict(contact_id='CT-%04d' % (k + 1), donor_id=did(x['di']), donor=dn(x['di']), contact=x['name'], role=x['role'], phone=x['phone'], email=x['email']) for k, x in enumerate(w['contacts'])]
    rcid = {}
    rec = sorted(w['rec'], key=lambda x: (x['start'], x['di']))
    for k, x in enumerate(rec): x['recurring_id'] = 'RC-%04d' % (k + 1); rcid[x['di']] = x['recurring_id']
    P['recurring_rows'] = [dict(recurring_id=x['recurring_id'], donor_id=did(x['di']), donor=dn(x['di']), amount=x['amount'], start_date=iso(x['start']), day=x['anchor'], channel=x['channel'], method=x['method'],
                                fund=x['fund'], status=x['status'], last_received=iso(x['last']) if x['last'] else '', stopped_on=iso(x['stop']) if x['stop'] else '', missed=x['missed']) for x in rec]
    P['gift_rows'] = [dict(gift_id=g['gift_id'], date=iso(g['date']), month=iso(_ms(g['date'])), donor_id='' if g.get('_nodonor') else did(g['di']), donor='(no donor recorded)' if g.get('_nodonor') else dn(g['di']),
                           amount=g['amount'], fund=g['fund'], campaign=g['campaign'], appeal=g['appeal'], channel=g['channel'], method=g['method'], gift_type=g['gtype'],
                           restricted=g['fund'] in RESTRICTED_FUNDS, ack_sent=iso(g['ack']) if g['ack'] != '' else '', batch_id=g['batch'], pledge_id=g.get('_pledge', ''),
                           recurring_id=rcid.get(g['di'], '') if g['gtype'] == 'Recurring' else '', match_for=g['_matchfor']['gift_id'] if g.get('_matchfor') is not None else '') for g in w['gifts']]
    P['pledge_rows'] = [dict(pledge_id=p['pledge_id'], donor_id=did(p['di']), donor=dn(p['di']), pledged_on=iso(p['pledged_on']), total=p['total'], instalments=p['n'], every_months=p['gap'], fund=p['fund'],
                             campaign=p['campaign'], status=p['status']) for p in w['pledges']]
    pps = sorted(w['pp'], key=lambda x: (x['due'], x['pledge']['pledge_id']))
    P['pledge_payment_rows'] = [dict(pp_id='PP-%05d' % (k + 1), pledge_id=x['pledge']['pledge_id'], donor_id=did(x['pledge']['di']), donor=dn(x['pledge']['di']), due_date=iso(x['due']), amount_due=x['amount_due'],
                                     paid_on=iso(x['paid_on']) if x['paid_on'] else '', amount_paid=x['amount_paid'], status=x['status']) for k, x in enumerate(pps)]
    for k, x in enumerate(pps): x['pp_id'] = 'PP-%05d' % (k + 1)
    P['matching_rows'] = [dict(match_id='MG-%04d' % (k + 1), gift_id=m['src']['gift_id'], donor_id=did(m['src']['di']), donor=dn(m['src']['di']), employer=dn(m['employer']), employer_donor_id=did(m['employer']),
                               ratio=m['ratio'], expected=m['expected'], requested_on=iso(m['requested_on']) if m['requested_on'] else '', received_on=iso(m['received_on']) if m['received_on'] else '',
                               received=m['received'], status=m['status']) for k, m in enumerate(sorted(w['matches'], key=lambda m: m['src']['gift_id']))]
    P['inkind_rows'] = [dict(inkind_id=x['inkind_id'], date=iso(x['date']), month=iso(_ms(x['date'])), donor_id=did(x['di']), donor=dn(x['di']), kind=x['type'], item=x['item'], qty=x['qty'], fair_value=x['value'],
                             value_basis=x['basis'], ack_sent=iso(x['ack']) if x['ack'] != '' else '') for x in w['inkind']]
    P['batch_rows'] = [dict(batch_id=b['batch_id'], week_start=iso(b['week_start']), banked_on=iso(b['banked_on']) if b['banked_on'] != '' else '', logged_amount=b['logged'], gift_count=b['count'], banked_amount=b['banked'],
                           status='Banked' if b['banked_on'] != '' else 'Open') for b in w['batches']]
    P['prospect_rows'] = [dict(prospect_id=x['prospect_id'], donor_id=did(x['di']), donor=dn(x['di']), capacity=x['capacity'], stage=x['stage'], ask_amount=x['ask'], next_step=x['next_step'], next_step_date=iso(x['next_date']),
                               owner=x['owner'], last_contact=iso(x['last_contact']), expected_close=iso(x['expected']) if x['expected'] != '' else '') for x in w['pipeline']]
    P['fund_rows'] = [dict(fund_id=f_['fund_id'], fund=f_['fund'], restriction=f_['restriction'], opening_balance=f_['opening_balance'], purpose=f_['purpose']) for f_ in funds]
    P['fund_month_rows'] = [dict(row_id=r_['row_id'], month=iso(r_['month']), fund=r_['fund'], receipts=r_['receipts'], released=r_['released'], transfers=r_['transfers'], balance=r_['balance']) for r_ in w['fm']]
    rel = {}
    for x in w['expenses']:
        if x['fund'] in RESTRICTED_FUNDS:
            k = (min(_eom(x['date']), TODAY), x['fund'], x['grant'] or '', x['program']); rel[k] = rel.get(k, 0.0) + x['amount']
    P['release_rows'] = [dict(release_id='RL-%04d' % (i + 1), date=iso(k[0]), month=iso(_ms(k[0])), fund=k[1], amount=R2(v), program=k[3], grant_id=k[2]) for i, (k, v) in enumerate(sorted(rel.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2])))]
    P['transfer_rows'] = [dict(transfer_id=t['transfer_id'], date=iso(t['date']), from_fund=GENERAL, to_fund=RESERVE_FUND, amount=t['amount'], note=t['note']) for t in w['transfers']]
    gname = {}
    P['grant_rows'] = [dict(grant_id=g['grant_id'], funder=g['funder'], funder_type=g['ftype'], program=g['program'], project=g['project'], fund=g['fund'], stage=g['stage'], asked=g['asked'], awarded=g['awarded'],
                            probability=g['prob'], owner=g['owner'], prospect_on=iso(g['prospect_on']) if g['prospect_on'] else '', loi_on=iso(g['loi_on']) if g['loi_on'] else '',
                            applied_on=iso(g['applied_on']) if g['applied_on'] else '', decision_on=iso(g['decision_on']) if g['decision_on'] else '', expected_on=iso(g['expected_on']) if g['expected_on'] else '',
                            start_on=iso(g['start_on']) if g['start_on'] else '', end_on=iso(g['end_on']) if g['end_on'] else '', term_months=g['term'] if g['stage'] == 'Awarded' else 0, write_hours=g['write_hours'],
                            restricted=g['program'] != 'General operating') for g in w['grants']]
    P['grant_payment_rows'] = [dict(pay_id=p['pay_id'], grant_id=p['grant']['grant_id'], funder=p['grant']['funder'], number=p['n'], due_date=iso(p['due']), amount=p['amount'],
                                    received_on=iso(p['received_on']) if p['received_on'] else '', status=p['status']) for p in w['gpays']]
    P['grant_report_rows'] = [dict(report_id=x['report_id'], grant_id=x['grant']['grant_id'], funder=x['grant']['funder'], kind=x['kind'], due_date=iso(x['due']), submitted_on=iso(x['submitted_on']) if x['submitted_on'] else '',
                                   status=x['status'], owner=x['owner']) for x in w['greports']]
    P['grant_budget_rows'] = [dict(line_id=b['line_id'], grant_id=b['grant']['grant_id'], line=b['line'], budget=b['budget']) for b in w['gbudgets']]
    P['staff_time_rows'] = [dict(time_id=x['time_id'], month=iso(x['month']), staff=x['staff'], staff_id=x['staff_id'], target_kind=x['kind'], grant_id=x['grant']['grant_id'] if x['grant'] else '', program=x['program'],
                                 function=x['function'], percent=x['percent'], hours=x['hours'], cost=x['cost']) for x in w['stime']]
    P['pay_rows'] = [dict(pay_id=p['pay_id'], month=iso(p['month']), staff=p['staff'], role=p['role'], pay_type=p['pay_type'], hours=p['hours'], gross=p['gross'], employer_cost=p['employer_cost'], total=p['total'],
                          status=p['status']) for p in w['pay']]
    P['expense_rows'] = [dict(expense_id=x['expense_id'], date=iso(x['date']), month=iso(x['month']), category=x['category'], vendor=x['vendor'], program=x['program'], function=x['function'], fund=x['fund'], amount=x['amount'],
                              grant_id=x['grant'] or '', event_id=x['event'] or '', campaign=x['campaign'], appeal=x['appeal'], note=x['note']) for x in w['expenses']]
    P['event_rows'] = [dict(event_id=e['event_id'], event=e['event'], kind=e['kind'], date=iso(e['date']), year=e['date'].year, venue=e['venue'], budget_cost=e['budget_cost'], goal=e['goal'],
                            expected_attendees=e['expected_attendees'], status=e['status'], campaign=e['campaign']) for e in w['events']]
    P['ticket_rows'] = [dict(ticket_id='TK-%05d' % (k + 1), event_id=t['event']['event_id'], event=t['event']['event'], sold_on=iso(t['sold_on']), month=iso(_ms(t['sold_on'])), donor_id=did(t['di']), buyer=dn(t['di']),
                             ticket_type=t['ticket_type'], qty=t['qty'], price_each=t['price_each'], amount=R2(t['qty'] * t['price_each']), benefit_each=t['benefit_each'], seats=t['seats']) for k, t in enumerate(w['tickets'])]
    steps_done = ['Send the impact report', 'Renewal meeting', 'Deliver the last benefit', 'Thank-you visit']
    sp_rows = []
    for k, s in enumerate(w['sponsors']):
        e = s['event']; done = s['status'] == 'Paid'
        nxt = ('Renewal meeting' if s['delivered'] >= s['owed'] else 'Deliver the last benefits') if done else ('Collect the payment' if s['status'] == 'Promised' else 'Ask again next season')
        nd = (e['date'] + day(30 + 7 * (k % 5))) if done else (TODAY + day(7 + (k % 20)))
        sp_rows.append(dict(sponsor_id='SP-%03d' % (k + 1), event_id=e['event_id'], event=e['event'], donor_id=did(s['bi']), sponsor=dn(s['bi']), level=s['level'], promised=s['promised'], received=s['received'],
                            promised_on=iso(s['promised_on']), received_on=iso(s['received_on']) if s['received_on'] else '', status=s['status'], benefits_owed=s['owed'], benefits_delivered=s['delivered'],
                            next_step=nxt, next_step_date=iso(nd)))
    P['sponsor_rows'] = sp_rows
    P['auction_rows'] = [dict(item_id='AU-%03d' % (k + 1), event_id=a['event']['event_id'], event=a['event']['event'], item=a['item'], donor_id=did(a['don']), donated_by=dn(a['don']), fair_value=a['value'],
                              starting_bid=a['start'], sold_price=a['sold'], buyer_id=did(a['buyer']) if a['buyer'] != '' else '', status=a['status'], received_on=iso(a['received_on'])) for k, a in enumerate(w['auction'])]
    # campaigns per year with goals from the previous year's own result
    camp_actual = {}
    for g in w['gifts']:
        k = (g['campaign'], g['date'].year); camp_actual[k] = camp_actual.get(k, 0.0) + g['amount']
    evgoal = {(e['campaign'], e['date'].year): e['goal'] for e in w['events']}
    gd = lambda y: _giving_day(y); ga = lambda y: _gala_date(y)
    spans = {'Year-End Appeal': lambda y: (D(y, 11, 1), D(y, 12, 31)), 'Giving Day': lambda y: (gd(y) - day(7), gd(y) + day(1)), 'Spring Gala': lambda y: (D(y, 4, 1), ga(y)),
             'Fun Run': lambda y: (_fun_run_dates()[min(2, max(0, y - (Y - 2)))] - day(45), _fun_run_dates()[min(2, max(0, y - (Y - 2)))]), 'Summer Camp Appeal': lambda y: (D(y, 6, 1), D(y, 6, 30)),
             'Back-to-School Drive': lambda y: (D(y, 8, 1), D(y, 9, 15)), 'Monthly Giving': lambda y: (D(y, 1, 1), D(y, 12, 31)), 'General giving': lambda y: (D(y, 1, 1), D(y, 12, 31))}
    cr_ = []
    for y in range(Y - 2, Y + 1):
        for c_ in CAMPAIGNS:
            a, b = spans[c_](y)
            goal = evgoal.get((c_, y)) or float(round(max(2000.0, camp_actual.get((c_, y - 1), camp_actual.get((c_, y), 3000.0) * .9)) * 1.07 / 500.0) * 500.0)
            if y == Y - 2 and not evgoal.get((c_, y)): goal = float(round(max(2000.0, camp_actual.get((c_, y), 3000.0)) * 1.03 / 500.0) * 500.0)
            cr_.append(dict(campaign=c_, year=y, start_date=iso(a), end_date=iso(b), goal=goal))
    for k, x in enumerate(cr_): x['campaign_id'] = 'CP-%02d' % (k + 1)
    P['campaign_rows'] = [dict(campaign_id=x['campaign_id'], campaign=x['campaign'], year=x['year'], start_date=x['start_date'], end_date=x['end_date'], goal=x['goal']) for x in cr_]
    hrs = {}
    for s in w['vshifts']:
        if s['status'] == 'Worked': hrs[s['vol']['volunteer_id']] = hrs.get(s['vol']['volunteer_id'], 0.0) + s['hours']
    P['volunteer_rows'] = [dict(volunteer_id=v['volunteer_id'], name=v['name'], phone=v['phone'], email=v['email'], role=v['role'], joined=iso(v['start']), last_shift=iso(v['last_shift']) if v['last_shift'] != '' else '',
                                status=v['status'], availability=v['avail'], donor_id=did(v['di']) if v['di'] is not None else '', hours_worked=R2(hrs.get(v['volunteer_id'], 0.0))) for v in w['vols']]
    P['slot_rows'] = [dict(slot_id=s['slot_id'], date=iso(s['date']), program=s['program'], shift=s['shift'], role=s['role'], needed=s['needed'], signed_up=s['signed'], hours=s['hours']) for s in w['slots']]
    P['shift_rows'] = [dict(shift_id=s['shift_id'], date=iso(s['date']), week=iso(s['week']), month=iso(s['month']), volunteer_id=s['vol']['volunteer_id'], volunteer=s['vol']['name'], role=s['role'], program=s['program'],
                            shift=s['shift'], hours=s['hours'], status=s['status']) for s in w['vshifts']]
    P['member_rows'] = [dict(member_id=m['member_id'], donor_id=did(m['di']), member=dn(m['di']), level=m['level'], joined=iso(m['joined']), due_date=iso(m['due']), last_paid=iso(m['last']) if m['last'] else '',
                             status=m['status'], annual_dues=_DUES[m['level']]) for m in w['members']]
    P['dues_rows'] = [dict(dues_id=x['dues_id'], member_id=x['m']['member_id'], member=dn(x['m']['di']), date=iso(x['date']), month=iso(_ms(x['date'])), amount=x['amount'], year=x['year'], method=x['method']) for x in w['dues']]
    P['participant_rows'] = [dict(participant_id=p['participant_id'], name=p['name'], phone=p['phone'], program=p['program'], status=p['status'], start_date=iso(p['start']) if p['start'] != '' else '',
                                  last_attended=iso(p['last']) if p['last'] != '' else '', sessions=p['sessions'], contact_status=p['contact']) for p in w['parts']]
    P['program_month_rows'] = [dict(row_id=x['row_id'], month=iso(x['month']), program=x['program'], participants=x['unique'], visits=x['visits'], new_participants=x['new'], sessions=x['sessions'], capacity=x['capacity'],
                                    waiting=x['waiting']) for x in w['pm']]
    P['session_rows'] = [dict(session_id=s['session_id'], date=iso(s['date']), month=iso(s['month']), program=s['program'], staff=s['staff'], attendees=s['attendees'], volunteers=s['volunteers']) for s in w['sessions']]
    P['outcome_rows'] = [dict(outcome_id=o['outcome_id'], quarter=iso(o['quarter']), program=o['program'], outcome=o['outcome'], target=o['target'], actual=o['actual']) for o in w['outcomes']]
    P['board_rows'] = [dict(member_id=b['member_id'], name=b['name'], role=b['role'], committee=b['committee'], term_start=iso(b['term_start']), term_end=iso(b['term_end']), terms_served=b['terms_served'],
                            skill=b['skill'], skill2=b['skill2'], donor_id=did(b['di']), phone=b['phone'], email=b['email']) for b in w['board']]
    P['meeting_rows'] = [dict(meeting_id=m['meeting_id'], date=iso(m['date']), kind=m['kind'], expected=m['expected'], present=m['present'], quorum_met=m['quorum'], minutes_ready=m['minutes'],
                              status='Planned' if m['planned'] else 'Held') for m in w['meetings']]
    md = {m['meeting_id']: m for m in w['meetings']}
    P['attendance_rows'] = [dict(att_id=a['att_id'], meeting_id=a['meeting'], date=iso(md[a['meeting']]['date']), kind=md[a['meeting']]['kind'], member_id=a['member_id'], member=a['member'], status=a['status']) for a in w['attend']]
    P['declaration_rows'] = [dict(decl_id=x['decl_id'], member_id=x['member_id'], member=x['member'], year=x['year'], due_date=iso(x['due']), filed_on=iso(x['filed']) if x['filed'] else '', items_declared=x['items'], status=x['status']) for x in w['decl']]
    P['obligation_rows'] = [dict(ob_id=x['ob_id'], item=x['item'], kind=x['kind'], due_date=iso(x['due']), owner=x['owner'], done_on=iso(x['done']) if x['done'] != '' else '', status=x['status']) for x in w['oblig']]
    P['cash_rows'] = [dict(cash_id=x['cash_id'], month=iso(x['month']), opening=x['opening'], receipts=x['receipts'], payments=x['payments'], closing=x['closing'], restricted=x['restricted'], designated=x['designated'],
                           free_money=x['free_money'], avg_monthly_expense=x['avg_monthly_expense'], reserve_months=x['reserve_months']) for x in w['cash']]
    P['bank_rows'] = [dict(bank_id=b['bank_id'], date=iso(b['date']), month=iso(b['month']), kind=b['kind'], description=b['description'], money_in=b['money_in'], money_out=b['money_out'], balance=b['balance'],
                           reconciled=b['reconciled']) for b in w['bank']]
    P['forecast_rows'] = [dict(forecast_id=x['forecast_id'], month=iso(x['month']), gifts=x['gifts'], recurring=x['recurring'], pledges_due=x['pledges_due'], grants=x['grants'], event_net=x['event_net'], dues=x['dues'],
                               expenses=x['expenses'], one_off=x['one_off'], one_off_note=x['one_off_note'], event=x['event']) for x in w['forecast']]
    P['budget_rows'] = [dict(budget_id=x['budget_id'], month=iso(x['month']), area=x['area'], budget=x['budget']) for x in w['budget']]
    P['income_budget_rows'] = [dict(budget_id=x['budget_id'], month=iso(x['month']), line=x['line'], budget=x['budget']) for x in w['ibudget']]
    return P


def _mk(name):
    def f(n=None): return _thin(_cached(name, lambda: _public()[name]), n)
    f.__name__ = name; return f


_GENS = ['donor_rows', 'contact_rows', 'gift_rows', 'recurring_rows', 'pledge_rows', 'pledge_payment_rows', 'matching_rows', 'inkind_rows', 'batch_rows', 'prospect_rows', 'fund_rows', 'fund_month_rows',
         'release_rows', 'transfer_rows', 'grant_rows', 'grant_payment_rows', 'grant_report_rows', 'grant_budget_rows', 'staff_time_rows', 'pay_rows', 'expense_rows', 'event_rows', 'ticket_rows', 'sponsor_rows',
         'auction_rows', 'campaign_rows', 'volunteer_rows', 'slot_rows', 'shift_rows', 'member_rows', 'dues_rows', 'participant_rows', 'program_month_rows', 'session_rows', 'outcome_rows', 'board_rows',
         'meeting_rows', 'attendance_rows', 'declaration_rows', 'obligation_rows', 'cash_rows', 'bank_rows', 'forecast_rows', 'budget_rows', 'income_budget_rows']
for _nm in _GENS: globals()[_nm] = _mk(_nm)


# ------------------------------------------------------------------ story
def story():
    """Ids of the 6 story rows, with the values that make each one true (all asserted)."""
    gifts = gift_rows(); don = donor_rows()
    yr = {}
    for g in gifts:
        if g['donor_id']: yr[(g['donor_id'], int(g['date'][:4]))] = yr.get((g['donor_id'], int(g['date'][:4])), 0.0) + g['amount']
    lapsing = [d['donor_id'] for d in don if all(yr.get((d['donor_id'], Y - k), 0) >= 5000 for k in (1, 2, 3)) and yr.get((d['donor_id'], Y), 0) == 0]
    sid = [d['donor_id'] for d in don if d.get('name') == _STORY_DONOR or d.get('contact') == _STORY_DONOR]
    assert sid and sid[0] in lapsing, (sid, lapsing)
    lapsing = [sid[0]]   # early in the year other major donors may not have given yet; the story donor is the designed one
    gr = {g['grant_id']: g for g in grant_rows()}
    spent = {}
    for x in expense_rows():
        if x['grant_id']: spent[x['grant_id']] = spent.get(x['grant_id'], 0.0) + x['amount']
    bud = {}
    for b in grant_budget_rows(): bud[b['grant_id']] = bud.get(b['grant_id'], 0.0) + b['budget']
    rep = [r for r in grant_report_rows() if r['status'] != 'Submitted' and 8 <= (to_date(r['due_date']) - TODAY).days <= 12]
    assert len(rep) == 1, rep
    r0 = rep[0]; g0 = gr[r0['grant_id']]
    el = (TODAY - to_date(g0['start_on'])).days / max(1.0, (to_date(g0['end_on']) - to_date(g0['start_on'])).days)
    assert spent.get(g0['grant_id'], 0) / bud[g0['grant_id']] < el - 0.2
    over = [f_ for f_ in fund_month_rows() if f_['month'] == iso(_ms(TODAY)) and f_['balance'] < 0]
    assert len(over) == 1, over
    od = [p for p in pledge_payment_rows() if p['status'] in ('Overdue', 'Due', 'Open', 'Partial') and (TODAY - to_date(p['due_date'])).days >= 60]
    assert len(od) == 1, od
    ev = [e for e in event_rows() if e['kind'] == 'Gala' and e['status'] == 'Done']
    ev = max(ev, key=lambda e: e['date'])
    ecost = sum(x['amount'] for x in expense_rows() if x['event_id'] == ev['event_id'])
    eraised = sum(t['amount'] for t in ticket_rows() if t['event_id'] == ev['event_id'])
    assert ecost > ev['budget_cost'] * 1.2
    cash = [f_ for f_ in forecast_rows()]
    return dict(donor=lapsing[0], report=r0['report_id'], grant=g0['grant_id'], fund=over[0]['fund'], pledge_payment=od[0]['pp_id'] if 'pp_id' in od[0] else od[0]['pledge_id'],
                pledge=od[0]['pledge_id'], event=ev['event_id'], forecast_month=[f_['forecast_id'] for f_ in cash if f_['one_off_note']][0] if any(f_['one_off_note'] for f_ in cash) else '')


if __name__ == '__main__':
    for nm in _GENS: print(nm, len(globals()[nm]()))
    print(story())
