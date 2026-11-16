"""hf_core - shared demo data for the Household Finance suite (Dar Templates, English edition).

Household: the Rivera-Okafor household. Partner 1 (salaried, paid every two weeks), partner 2 (freelance, 2-3 clients and a small side income),
two children (about 11 and 7) and a grandparent who helps with childcare. 14 accounts, 28 spending categories, about 20 bills, 14 subscriptions,
3 cards, a car loan and a student loan, 10 savings goals and sinking funds, 2 retirement accounts and 1 brokerage account, big purchases planned.
All rows are deterministic, oldest first; n= thins a list but keeps the most recent rows; optional dates are ''.
Dates are relative to TODAY (env HF_TODAY overrides); about 2 years of history, scheduled items up to 12 months ahead, rows in the last 30 days.
Money is one generic currency; shares and rates are 0..1 fractions. No brand, bank, lender, insurer or company names anywhere.

Constants: HOUSEHOLD, SUITE, TODAY, Y, HISTORY_START, FUTURE_END, PARTNER1, PARTNER2, CASH_FLOOR, EMERGENCY_MONTHS_LOW, EMERGENCY_MONTHS_HIGH,
  DEBT_INCOME_GROSS, CONSUMER_DEBT_TAKEHOME, HOUSING_GROSS, SAVINGS_RATE_TARGET, NEEDS_SHARE, WANTS_SHARE, SAVINGS_SHARE, RETIREMENT_MIN,
  RETIREMENT_GOOD, SET_ASIDE_PCT, REVIEW_DAYS, GROWTH_RATE, EXTRA_PAYMENT, SUB_UNUSED_DAYS, BASELINE_MONTHS, AGREED_P1_SHARE, PAY_FREQ,
  PAYDAY1_NEXT, PAYDAY1_FREQ, PAYDAY2_DOM, TAX_DUE (generic date), CHILD_AGES.
Date helpers: day, iso, ago, ahead, to_date, month_start, add_months, months14, months25, week_start, paydays(freq, anchor, start, end),
  pays_in_month(freq, anchor, y, m), monthly_payday(y, m, dom); pairs, first_name, fake_phone, fake_email.
Lists (constants): PERSONS, PAY_FREQS, ACCOUNT_TYPES, GROUPS, CATEGORIES (name, group), CATEGORY_NAMES, INCOME_SOURCES, INVOICE_STATUS, BILL_STATUS,
  BILL_CYCLES, SB_CYCLES, SB_DECISIONS, GOAL_KINDS, PRIORITIES, CT_KINDS, DEBT_KINDS, DEBT_METHODS, CONTRACT_KINDS, TD_TYPES, DEDUCTION_CATS,
  BP_KINDS, BP_STATUS, KIDS, KID_KINDS, SPLIT_RULES, TR_PURPOSES, RT_SOURCES, NW_CLASS, ROLES, TEAM_GROUPS, WEEKDAYS, MONTH_NAMES.
People and reference: team (16 rows HF-01..HF-16), household (the 5 household members), outside (the 11 outside contacts), category_rows (28).
Row generators (each takes n=None): account_rows (AC-01..AC-14), income_rows (IN-), invoice_rows (INV-), pay_schedule_rows (PD-), bill_rows (BL-01..),
  bill_due_rows (BI-), tx_rows (TX-), subscription_rows (SB-01..SB-14), contract_rows (CN-), debt_rows (DB-01..DB-05), debt_payment_rows (DP-),
  goal_rows (SG-01..SG-10), contribution_rows (CT-), retirement_rows (RT-), transfer_rows (TR-), networth_rows (NW-), shared_cost_rows (SC-),
  settle_rows (SE-), kid_cost_rows (KC-), allowance_rows (AL-), tax_doc_rows (TD-), deduction_rows (DR-), big_purchase_rows (BP-),
  purchase_option_rows (BO-), scenario_rows (SN-), budget_rows (BU-), event_item_rows (EI-, a family celebration budget), move_item_rows (MV-, the move plan).
story(): dict of the story ids (asserted): the bill due in about 5 days before the next payday that pushes joint checking below the cash floor
  (bill, bill_due, account, payday, low_point), subscriptions 40% dearer than 6 months ago with two unused 60+ days (subs_unused, subs_ratio),
  groceries about 18% over plan this month to date (plan_line, groceries_ratio), the highest-rate card with less extra payment than a lower-rate card
  (debt, debt_lower, interest_lost_year), the car-insurance sinking fund short of the yearly premium due in about 7 weeks (goal),
  partner 2 paid more than the agreed share of shared costs 3 months in a row (shared_months).
"""
import os
import datetime as dt
import calendar
import random

HOUSEHOLD = 'the Rivera-Okafor household'
SUITE = 'fx-20261116-household-finance'
TODAY = dt.date.fromisoformat(os.environ['HF_TODAY']) if os.environ.get('HF_TODAY') else dt.date.today()
D = dt.date
Y = TODAY.year
PARTNER1 = 'Partner 1'
PARTNER2 = 'Partner 2'

CASH_FLOOR = 500.0              # low-balance warning on the joint account, set your own
EMERGENCY_MONTHS_LOW = 3        # a typical range, check your own numbers
EMERGENCY_MONTHS_HIGH = 6
DEBT_INCOME_GROSS = 0.36        # total debt payments over gross income, a typical range
CONSUMER_DEBT_TAKEHOME = 0.20   # card and consumer debt over take-home pay, a typical range
HOUSING_GROSS = 0.28
SAVINGS_RATE_TARGET = 0.20
NEEDS_SHARE, WANTS_SHARE, SAVINGS_SHARE = 0.50, 0.30, 0.20
RETIREMENT_MIN, RETIREMENT_GOOD = 0.10, 0.15
SET_ASIDE_PCT = 0.25            # share of freelance income moved to the tax set-aside
REVIEW_DAYS = 45                # review insurance and contracts this many days before renewal
GROWTH_RATE = 0.05              # an example yearly growth rate for the projection, not a forecast
EXTRA_PAYMENT = 300.0
SUB_UNUSED_DAYS = 60
BASELINE_MONTHS = 6
AGREED_P1_SHARE = 0.60
PAY_FREQ = 'Every two weeks'
PAYDAY1_FREQ = PAY_FREQ
PAYDAY2_DOM = 28                # partner 2 pays itself a drawing on this day; client money arrives irregularly
CHILD_AGES = (11, 7)

HISTORY_START = None            # set below
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
def rng(tag=''): return random.Random('hf-core-20261116-' + str(tag))
def R2(x): return round(x + 1e-9, 2)
def _ms(d): return dt.date(d.year, d.month, 1)
def _dim(y, m): return calendar.monthrange(y, m)[1]
def _dd(y, m, d): return D(y, m, min(d, _dim(y, m)))
def _next_dow(d, dow):
    while d.weekday() != dow: d += day(1)
    return d


PAYDAY1_NEXT = TODAY + day(8)   # partner 1's next payday; every two weeks from here
TAX_DUE = D(Y + 1, 4, 15)       # "your tax office's date": a generic date for the checklist countdown


def paydays(freq, anchor, start, end):
    """Pay dates between start and end (inclusive) for Weekly, Every two weeks, Twice a month (15th and last day) or Monthly (day of the anchor)."""
    out = []
    if freq in ('Weekly', 'Every two weeks'):
        step = 7 if freq == 'Weekly' else 14
        d = anchor - day(step * ((anchor - start).days // step)) if anchor >= start else anchor
        while d < start: d += day(step)
        while d <= end: out.append(d); d += day(step)
    else:
        m = _ms(start)
        while m <= end:
            ds = [_dd(m.year, m.month, 15), _dd(m.year, m.month, 31)] if freq == 'Twice a month' else [_dd(m.year, m.month, anchor.day)]
            out += [p for p in ds if start <= p <= end]
            m = add_months(m, 1)
    return out


def pays_in_month(freq, anchor, y, m): return len(paydays(freq, anchor, D(y, m, 1), D(y, m, _dim(y, m))))
def monthly_payday(y, m, dom=28): return _dd(y, m, dom)


# ------------------------------------------------------------------ lists (plain international English; keys from pairs() stay <= 21 characters)
PERSONS = ['Partner 1', 'Partner 2', 'Joint']
PAY_FREQS = ['Weekly', 'Every two weeks', 'Twice a month', 'Monthly']
ACCOUNT_TYPES = ['Checking', 'Savings', 'Credit card', 'Loan', 'Retirement', 'Brokerage']
GROUPS = ['Fixed bills', 'Variable needs', 'Wants', 'Savings', 'Debt payments']
CATEGORIES = [('Rent or mortgage', 'Fixed bills'), ('Utilities', 'Fixed bills'), ('Phone and internet', 'Fixed bills'), ('Insurance', 'Fixed bills'),
              ('Childcare and school', 'Fixed bills'), ('Groceries', 'Variable needs'), ('Fuel and transport', 'Variable needs'), ('Health costs', 'Variable needs'),
              ('Household supplies', 'Variable needs'), ('Car service', 'Variable needs'), ('Kids and family', 'Variable needs'), ('Work and tax costs', 'Variable needs'),
              ('Eating out', 'Wants'), ('Subscriptions', 'Wants'), ('Shopping', 'Wants'), ('Entertainment', 'Wants'), ('Personal care', 'Wants'),
              ('Holidays and trips', 'Wants'), ('Gifts', 'Wants'), ('Emergency fund', 'Savings'), ('Goal savings', 'Savings'), ('Retirement', 'Savings'),
              ('Tax set-aside', 'Savings'), ('Card payments', 'Debt payments'), ('Car loan', 'Debt payments'), ('Student loan', 'Debt payments'),
              ('Extra debt payment', 'Debt payments'), ('Other', 'Variable needs')]
CATEGORY_NAMES = [c for c, g in CATEGORIES]
CAT_GROUP = dict(CATEGORIES)
INCOME_SOURCES = ['Paycheck', 'Client A', 'Client B', 'Client C', 'Side income', 'Windfall']
INVOICE_STATUS = ['Paid', 'Sent', 'Late']
BILL_STATUS = ['Paid', 'Unpaid', 'Late']
BILL_CYCLES = ['Monthly', 'Yearly']
SB_CYCLES = ['Monthly', 'Yearly']
SB_DECISIONS = ['Keep', 'Review', 'Cancel']
GOAL_KINDS = ['Emergency fund', 'Sinking fund', 'Savings goal']
PRIORITIES = ['High', 'Medium', 'Low']
CT_KINDS = ['Deposit', 'Spend']
DEBT_KINDS = ['Credit card', 'Instalment loan']
DEBT_METHODS = ['Snowball', 'Avalanche']
CONTRACT_KINDS = ['Insurance', 'Utility', 'Phone and internet', 'Rent', 'Loan']
TD_TYPES = ['Income statement', 'Interest statement', 'Investment statement', 'Charity receipt', 'Medical receipt', 'Work-expense receipt', 'Childcare receipt',
            'Tax payment record']
DEDUCTION_CATS = ['Home office costs', 'Work travel', 'Equipment and supplies', 'Professional fees', 'Charity gifts', 'Medical costs', 'Childcare', 'Education']
BP_KINDS = ['Car', 'Move', 'Home', 'Family trip', 'Equipment']
BP_STATUS = ['Planning', 'Saving', 'Bought']
KIDS = ['Noa', 'Ike', 'Both children']
KID_KINDS = ['Childcare', 'School costs', 'Activities', 'Clothing', 'Allowance', 'Other']
SPLIT_RULES = ['Income share', 'Equal', 'Custom']
TR_PURPOSES = ['Personal spending money', 'Settle up']
RT_SOURCES = ['Payroll', 'Transfer']
NW_CLASS = ['Asset', 'Liability']
ROLES = ['Partner 1', 'Partner 2', 'Child', 'Grandparent', 'Landlord', 'Payroll office', 'Freelance client', 'Tax preparer', 'Insurance agent', 'Childcare provider',
         'School office', 'Car mechanic', 'Utility company', 'Bank branch']
TEAM_GROUPS = ['Household', 'Outside']
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

# ------------------------------------------------------------------ people
_house = [('HF-01', 'Sam Rivera', 'Partner 1', 'Salaried, paid every two weeks', 38),
          ('HF-02', 'Riley Okafor', 'Partner 2', 'Freelance, irregular monthly income', 36),
          ('HF-03', 'Noa Rivera-Okafor', 'Child', 'Child, about 11 years', 11),
          ('HF-04', 'Ike Rivera-Okafor', 'Child', 'Child, about 7 years', 7),
          ('HF-05', 'Ada Okafor', 'Grandparent', 'Helps with childcare', 66)]
_out = [('HF-06', 'Marta Kowalski', 'Landlord', 'Rent and repairs'), ('HF-07', 'Dev Patel', 'Payroll office', 'Pay statements for partner 1'),
        ('HF-08', 'Lena Hoffmann', 'Freelance client', 'Client A, monthly retainer'), ('HF-09', 'Tomas Novak', 'Freelance client', 'Client B, project invoices'),
        ('HF-10', 'Aiko Tanaka', 'Tax preparer', 'Yearly tax papers'), ('HF-11', 'Carlos Mendes', 'Insurance agent', 'Car, renters and life cover'),
        ('HF-12', 'Nadia Haddad', 'Childcare provider', 'After-school care'), ('HF-13', 'Ruth Mensah', 'School office', 'School fees and trips'),
        ('HF-14', 'Pavel Ivanov', 'Car mechanic', 'Service and yearly car checks'), ('HF-15', 'Yara Santos', 'Utility company', 'Power, gas, water and internet'),
        ('HF-16', 'Elif Demir', 'Bank branch', 'Accounts, cards and loans')]
household = [dict(member_id=a, name=b, role=c, group='Household', phone=fake_phone(401 + i), email=fake_email(b), note=d, start=ago(3000 - 100 * i))
             for i, (a, b, c, d, e) in enumerate(_house)]
outside = [dict(member_id=a, name=b, role=c, group='Outside', phone=fake_phone(421 + i), email=fake_email(b), note=d, start=ago(2400 - 150 * i))
           for i, (a, b, c, d) in enumerate(_out)]
team = household + outside
MEMBER = {t['member_id']: t for t in team}
category_rows = [dict(category=c, group=g) for c, g in CATEGORIES]


# ------------------------------------------------------------------ the world (built once, in dependency order)
_CACHE = {}
_MONTHS = [month_start(k) for k in range(24, -1, -1)]          # 25 months, the last is this month
_FREE = {1: .85, 2: .9, 3: 1.05, 4: 1.05, 5: 1.0, 6: .95, 7: .8, 8: .7, 9: 1.1, 10: 1.15, 11: 1.1, 12: .75}   # freelance seasons
P2_SCALE = 1.1


def _thin(rows, n):
    if not n or n >= len(rows): return rows
    k = min(max(3, n // 5), n)
    if k >= n: return rows[-n:]
    recent = rows[-k:]; rest = rows[:-k]; m = n - k; step = len(rest) / float(m)
    return [rest[int(i * step)] for i in range(m)] + recent


def _r25(x): return float(round(x / 25.0) * 25)


def _income(w):
    r = rng('income'); inc = []; inv = []
    # partner 1: paycheck every two weeks
    for d in paydays(PAYDAY1_FREQ, PAYDAY1_NEXT, HISTORY_START, TODAY):
        g = 2850.0 if d >= TODAY - day(300) else 2750.0
        tax, ret = R2(g * .15), R2(g * .05)
        inc.append(dict(date=d, person=PARTNER1, source='Paycheck', gross=g, tax=tax, retirement=ret, other_deductions=120.0, account_id='AC-01', invoice_id=''))
    # windfalls: a yearly bonus, a tax refund, a gift
    for yy in (Y - 2, Y - 1, Y):
        for (mm, dd, amt) in ((12, 15, 700.0), (4, 18, 1150.0 if yy != Y - 2 else 980.0), (6, 22, 200.0)):
            d = D(yy, mm, dd)
            if HISTORY_START <= d <= TODAY: inc.append(dict(date=d, person=PARTNER1 if mm != 6 else PARTNER2, source='Windfall', gross=amt, tax=0.0, retirement=0.0,
                                                           other_deductions=0.0, account_id='AC-01', invoice_id=''))
    # partner 2: invoices and payments
    for m in _MONTHS:
        f = _FREE[m.month] * P2_SCALE
        a = _r25(r.uniform(2100, 2600) * (0.8 + 0.2 * f)); d0 = _dd(m.year, m.month, r.randint(2, 6)); inv.append(('Client A', d0, 30, a, 'HF-08'))
        if r.random() < .78: inv.append(('Client B', _dd(m.year, m.month, r.randint(12, 22)), 21, _r25(r.uniform(700, 2600) * f), 'HF-09'))
        if r.random() < .3: inv.append(('Client C', _dd(m.year, m.month, r.randint(8, 25)), 14, _r25(r.uniform(450, 1500) * f), ''))
        if r.random() < .6: inc.append(dict(date=_dd(m.year, m.month, r.randint(3, 27)), person=PARTNER2, source='Side income', gross=_r25(r.uniform(90, 420)), tax=0.0, retirement=0.0,
                                           other_deductions=0.0, account_id='AC-03', invoice_id=''))
    inv.append(('Client B', TODAY - day(43), 30, 840.0, 'HF-09'))      # a late invoice (due 13 days ago)
    inv = sorted([x for x in inv if x[1] <= TODAY], key=lambda x: x[1])
    invoices = []
    for i, (cl, d0, terms, amt, cid) in enumerate(inv):
        due = d0 + day(terms)
        if d0 == TODAY - day(43) and amt == 840.0: paid = None
        else: paid = due + day(r.randint(-5, 4))
        if paid is not None and paid > TODAY: paid = None
        st = 'Paid' if paid else ('Late' if due < TODAY else 'Sent')
        invoices.append(dict(invoice_id='INV-%03d' % (i + 1), client=cl, issued=iso(d0), due_date=iso(due), amount=amt, status=st, paid_on=iso(paid) if paid else '', contact_id=cid))
        if paid: inc.append(dict(date=paid, person=PARTNER2, source=cl, gross=amt, tax=0.0, retirement=0.0, other_deductions=0.0, account_id='AC-01', invoice_id='INV-%03d' % (i + 1)))
    if not any(TODAY - day(30) <= x['date'] <= TODAY for x in inc if x['person'] == PARTNER2):
        inc.append(dict(date=TODAY - day(6), person=PARTNER2, source='Side income', gross=215.0, tax=0.0, retirement=0.0, other_deductions=0.0, account_id='AC-03', invoice_id=''))
    inc.sort(key=lambda x: x['date'])
    rows = []
    for i, x in enumerate(inc):
        ded = R2(x['tax'] + x['retirement'] + x['other_deductions'])
        src = x['source']; setaside = R2(x['gross'] * SET_ASIDE_PCT) if src in ('Client A', 'Client B', 'Client C') else 0.0
        rows.append(dict(income_id='IN-%04d' % (i + 1), date=iso(x['date']), month=iso(_ms(x['date'])), person=x['person'], source=src, gross=x['gross'], tax=x['tax'],
                         retirement=x['retirement'], other_deductions=x['other_deductions'], deductions=ded, net=R2(x['gross'] - ded), set_aside=setaside,
                         account_id=x['account_id'], invoice_id=x['invoice_id']))
    w['income'] = rows; w['invoices'] = invoices
    # pay schedule: the next 12 months
    ps = []
    for d in paydays(PAYDAY1_FREQ, PAYDAY1_NEXT, TODAY + day(1), FUTURE_END):
        ps.append(dict(date=d, person=PARTNER1, source='Paycheck', frequency=PAYDAY1_FREQ, expected_net=2161.0))
    for m in range(0, 13):
        d = monthly_payday(add_months(_ms(TODAY), m).year, add_months(_ms(TODAY), m).month, PAYDAY2_DOM)
        if TODAY < d <= FUTURE_END: ps.append(dict(date=d, person=PARTNER2, source='Client money (estimate)', frequency='Monthly', expected_net=3000.0))
    ps.sort(key=lambda x: x['date'])
    cnt = {}
    for x in ps:
        if x['person'] == PARTNER1: cnt[(x['date'].year, x['date'].month)] = cnt.get((x['date'].year, x['date'].month), 0) + 1
    w['pay_schedule'] = [dict(pay_id='PD-%03d' % (i + 1), date=iso(x['date']), month=iso(_ms(x['date'])), person=x['person'], source=x['source'], frequency=x['frequency'],
                              expected_net=x['expected_net'], pays_in_month=cnt.get((x['date'].year, x['date'].month), 1) if x['person'] == PARTNER1 else 1,
                              extra_pay_month=bool(x['person'] == PARTNER1 and cnt.get((x['date'].year, x['date'].month), 1) >= 3)) for i, x in enumerate(ps)]


# name, category, amount now, due day (None = story rules), cycle, autopay, account, contact, payee, seasonal key, debt id, yearly anchor
_BILLS = [('Rent', 'Rent or mortgage', 1650.0, 1, 'Monthly', True, 'AC-01', 'HF-06', 'Landlord', '', ''),
          ('Electricity', 'Utilities', 92.0, 14, 'Monthly', True, 'AC-01', 'HF-15', 'Electricity supplier', 'elec', ''),
          ('Gas heating', 'Utilities', 70.0, 18, 'Monthly', True, 'AC-01', 'HF-15', 'Gas supplier', 'gas', ''),
          ('Water and trash', 'Utilities', 58.0, 'late', 'Monthly', False, 'AC-01', 'HF-15', 'Water supplier', 'water', ''),
          ('Internet', 'Phone and internet', 65.0, 9, 'Monthly', True, 'AC-01', 'HF-15', 'Internet provider', '', ''),
          ('Phone plan', 'Phone and internet', 96.0, 22, 'Monthly', True, 'AC-01', 'HF-15', 'Phone provider', '', ''),
          ('Renters insurance', 'Insurance', 24.0, 3, 'Monthly', True, 'AC-01', 'HF-11', 'Insurance agent', '', ''),
          ('Life insurance', 'Insurance', 46.0, 12, 'Monthly', True, 'AC-01', 'HF-11', 'Insurance agent', '', ''),
          ('Childcare provider', 'Childcare and school', 560.0, 'story', 'Monthly', False, 'AC-01', 'HF-12', 'Childcare provider', '', ''),
          ('School costs', 'Childcare and school', 110.0, 5, 'Monthly', False, 'AC-01', 'HF-13', 'School office', '', ''),
          ('Kids activities club', 'Childcare and school', 70.0, 6, 'Monthly', True, 'AC-01', 'HF-13', 'Activities club', '', ''),
          ('Car loan payment', 'Car loan', 412.0, 9, 'Monthly', True, 'AC-01', 'HF-16', 'Car loan', '', 'DB-04'),
          ('Student loan payment', 'Student loan', 285.0, 15, 'Monthly', True, 'AC-01', 'HF-16', 'Student loan', '', 'DB-05'),
          ('Card A minimum', 'Card payments', 140.0, 21, 'Monthly', True, 'AC-01', 'HF-16', 'Card A payment', '', 'DB-01'),
          ('Card B minimum', 'Card payments', 85.0, 24, 'Monthly', True, 'AC-01', 'HF-16', 'Card B payment', '', 'DB-02'),
          ('Card C minimum', 'Card payments', 60.0, 27, 'Monthly', True, 'AC-01', 'HF-16', 'Card C payment', '', 'DB-03'),
          ('Car insurance yearly premium', 'Insurance', 1260.0, 'caryear', 'Yearly', False, 'AC-06', 'HF-11', 'Insurance agent', '', ''),
          ('Car registration', 'Car service', 185.0, D(Y, 3, 12), 'Yearly', False, 'AC-01', 'HF-14', 'Vehicle office', '', ''),
          ('Annual car checks', 'Car service', 140.0, D(Y, 9, 20), 'Yearly', False, 'AC-01', 'HF-14', 'Garage', '', ''),
          ('Tax preparer fee', 'Work and tax costs', 240.0, D(Y, 3, 20), 'Yearly', False, 'AC-01', 'HF-10', 'Tax preparer', '', '')]
CAR_INS_DATE = TODAY + day(49)
STORY_BILL_DATE = TODAY + day(5)
LATE_BILL_DATE = TODAY - day(4)


def _bill_amount(b, d, r):
    name, amt = b[0], b[2]
    if name == 'Rent': return 1590.0 if d < D(Y, 1, 1) else 1650.0
    if name == 'Childcare provider': return 520.0 if d < D(Y, 9, 1) else 560.0
    sk = b[9]
    if sk == 'elec': return R2(amt * (1.3 if d.month in (7, 8) else 1.15 if d.month in (12, 1, 2) else .95) * r.uniform(.94, 1.06))
    if sk == 'gas': return R2(amt * {12: 2.1, 1: 2.3, 2: 2.0, 3: 1.3, 11: 1.3, 4: .8, 10: .7}.get(d.month, .35) * r.uniform(.95, 1.05))
    if sk == 'water': return R2(amt * r.uniform(.93, 1.08))
    if name == 'Car insurance yearly premium': return 1260.0 if d >= CAR_INS_DATE - day(30) or d > TODAY - day(400) else 1190.0
    if b[4] == 'Yearly': return R2(amt * (1.0 if d >= D(Y, 1, 1) else .95))
    return amt


def _bills(w):
    r = rng('bills'); bl = []; bi = []
    for i, b in enumerate(_BILLS):
        name, cat, amt, dd, cyc, auto, acct, cid, payee, sk, debt = b
        bid = 'BL-%02d' % (i + 1)
        if dd == 'story': dday = STORY_BILL_DATE.day
        elif dd == 'late': dday = LATE_BILL_DATE.day
        elif dd == 'caryear': dday = CAR_INS_DATE.day
        elif isinstance(dd, dt.date): dday = dd.day
        else: dday = dd
        fg = 'SG-02' if name == 'Car insurance yearly premium' else ''
        bl.append(dict(bill_id=bid, bill=name, category=cat, amount=amt, due_day=dday, cycle=cyc, autopay=auto, account_id=acct, contact_id=cid, payee=payee, from_goal=fg, debt_id=debt,
                       due_month=(CAR_INS_DATE.month if dd == 'caryear' else dd.month if isinstance(dd, dt.date) else 0)))
        dates = []
        if cyc == 'Monthly':
            for m in _MONTHS + [add_months(_ms(TODAY), k) for k in range(1, 13)]:
                d = _dd(m.year, m.month, dday)
                if dd == 'story' and abs((d - STORY_BILL_DATE).days) > 15: pass
                dates.append(d)
        else:
            anc = CAR_INS_DATE if dd == 'caryear' else dd
            for k in range(-3, 2):
                d = add_months(anc, 12 * k)
                dates.append(d)
        for d in sorted(set(dates)):
            if not (HISTORY_START <= d <= FUTURE_END): continue
            a = _bill_amount(b, d, r)
            if d <= TODAY:
                if name == 'Water and trash' and d == LATE_BILL_DATE: st, po = 'Late', None
                else:
                    lag = 0 if auto else (r.randint(2, 9) if r.random() < .06 else r.randint(0, 2))
                    po = min(d + day(lag), TODAY); st = 'Paid'
            else: st, po = 'Unpaid', None
            bi.append(dict(bill_id=bid, bill=name, due_date=d, month=_ms(d), amount=a, status=st, paid_on=po, account_id=acct, autopay=auto, category=cat, payee=payee, from_goal=fg))
    bi.sort(key=lambda x: (x['due_date'], x['bill_id']))
    w['bills'] = bl
    w['bill_due'] = [dict(due_id='BI-%04d' % (i + 1), bill_id=x['bill_id'], bill=x['bill'], due_date=iso(x['due_date']), month=iso(x['month']), amount=x['amount'], status=x['status'],
                          paid_on=iso(x['paid_on']) if x['paid_on'] else '', account_id=x['account_id'], autopay=x['autopay']) for i, x in enumerate(bi)]
    w['_bi'] = bi


# name, price now, cycle, price then, start days ago, change days ago, renew day, account, last used days ago, decision, owner
_SUBS = [('Video streaming A', 15.99, 'Monthly', 13.99, 900, 110, 4, 'AC-07', 2, 'Keep', 'Joint'),
         ('Video streaming B', 11.99, 'Monthly', 10.99, 700, 95, 11, 'AC-07', 9, 'Review', 'Joint'),
         ('Music streaming', 16.99, 'Monthly', 14.99, 1100, 140, 17, 'AC-07', 1, 'Keep', 'Joint'),
         ('Cloud storage', 9.99, 'Monthly', 8.99, 800, 60, 8, 'AC-07', 0, 'Keep', 'Joint'),
         ('Newspaper online', 14.00, 'Monthly', 11.00, 400, 150, 23, 'AC-07', 21, 'Review', 'Partner 1'),
         ('Gym membership', 38.00, 'Monthly', 34.00, 600, 125, 1, 'AC-07', 5, 'Keep', 'Partner 1'),
         ('Language lessons app', 12.99, 'Monthly', 12.99, 500, None, 14, 'AC-08', 94, 'Review', 'Partner 2'),
         ('Games pass', 14.99, 'Monthly', 0.0, 120, None, 19, 'AC-08', 3, 'Keep', 'Joint'),
         ('Kids learning app', 9.99, 'Monthly', 7.99, 520, 100, 26, 'AC-08', 4, 'Keep', 'Joint'),
         ('Audiobooks', 14.95, 'Monthly', 0.0, 150, None, 2, 'AC-08', 72, 'Review', 'Partner 2'),
         ('Antivirus', 59.99, 'Yearly', 39.99, 700, 160, 0, 'AC-08', 1, 'Keep', 'Joint'),
         ('Meal planning', 7.99, 'Monthly', 0.0, 90, None, 29, 'AC-08', 11, 'Review', 'Partner 1'),
         ('Photo club', 6.99, 'Monthly', 6.99, 450, None, 12, 'AC-08', 33, 'Keep', 'Partner 1'),
         ('Magazine box', 19.99, 'Monthly', 15.99, 330, 135, 6, 'AC-08', 40, 'Review', 'Partner 2')]


def _subs(w):
    rows = []; ch = []
    for i, (nm, p, cyc, then, sd, cd, rd, acct, lu, dec, own) in enumerate(_SUBS):
        sid = 'SB-%02d' % (i + 1); start = TODAY - day(sd); change = TODAY - day(cd) if cd else None
        if cyc == 'Monthly':
            nxt = _dd(TODAY.year, TODAY.month, rd)
            if nxt < TODAY: nxt = _dd(add_months(_ms(TODAY), 1).year, add_months(_ms(TODAY), 1).month, rd)
        else: nxt = TODAY + day(37)
        rows.append(dict(sub_id=sid, name=nm, price=p, cycle=cyc, monthly_cost=R2(p if cyc == 'Monthly' else p / 12.0), yearly_cost=R2(p * (12 if cyc == 'Monthly' else 1)),
                         account_id=acct, renewal_date=iso(nxt), last_used=ago(lu), price_6m_ago=then, decision=dec, owner=own, start_date=iso(start)))
        # charges on the card (history only)
        if cyc == 'Monthly':
            for m in _MONTHS:
                d = _dd(m.year, m.month, rd)
                if start <= d <= TODAY: ch.append((d, nm, acct, then if (change and d < change) else p, sid))
        else:
            for k in range(0, 3):
                d = add_months(nxt, -12 * k)
                if start <= d <= TODAY: ch.append((d, nm, acct, then if (change and d < change) else p, sid))
    w['subs'] = rows; w['_sub_charges'] = ch


# ------------------------------------------------------------------ plan, seasons, spending
_SEAS = {'Groceries': {12: 1.15, 11: 1.05, 8: 1.05}, 'Fuel and transport': {7: 1.12, 8: 1.12, 12: 1.05}, 'Eating out': {12: 1.2, 7: 1.1, 6: 1.05},
         'Shopping': {11: 1.5, 12: 1.9, 8: 1.6, 9: 1.3, 1: .7, 2: .8}, 'Kids and family': {8: 1.8, 9: 1.5, 12: 1.5}, 'Entertainment': {12: 1.2, 7: 1.3, 8: 1.2},
         'Health costs': {1: 1.3, 2: 1.2}, 'Household supplies': {3: 1.2, 4: 1.1, 12: 1.1}, 'Personal care': {12: 1.3, 6: 1.1},
         'Utilities': {12: 1.4, 1: 1.45, 2: 1.35, 3: 1.05, 7: 1.12, 8: 1.12, 4: .85, 5: .8, 6: .85, 9: .85, 10: .9, 11: 1.1}}
EXTRA_START = month_start(9)
GOAL_MONTHLY = {'SG-01': 400.0, 'SG-02': 105.0, 'SG-03': 120.0, 'SG-04': 60.0, 'SG-05': 200.0, 'SG-06': 80.0, 'SG-07': 75.0, 'SG-08': 160.0, 'SG-09': 150.0, 'SG-10': 900.0}
_PLAN = {'Rent or mortgage': 1650.0, 'Utilities': 300.0, 'Phone and internet': 161.0, 'Insurance': 70.0, 'Childcare and school': 740.0, 'Groceries': 900.0,
         'Fuel and transport': 230.0, 'Health costs': 90.0, 'Household supplies': 90.0, 'Car service': 60.0, 'Kids and family': 190.0, 'Work and tax costs': 90.0,
         'Eating out': 280.0, 'Subscriptions': 145.0, 'Shopping': 200.0, 'Entertainment': 100.0, 'Personal care': 60.0, 'Other': 40.0,
         'Emergency fund': GOAL_MONTHLY['SG-01'], 'Goal savings': sum(v for k, v in GOAL_MONTHLY.items() if k not in ('SG-01', 'SG-10')), 'Retirement': 370.0,
         'Tax set-aside': GOAL_MONTHLY['SG-10'], 'Card payments': 285.0, 'Car loan': 412.0, 'Student loan': 285.0, 'Extra debt payment': EXTRA_PAYMENT}


def plan_amount(cat, m):
    p = _PLAN.get(cat, 0.0)
    if cat == 'Extra debt payment' and m < EXTRA_START: return 0.0
    if cat == 'Rent or mortgage' and m < D(Y, 1, 1): return 1590.0
    if cat == 'Childcare and school' and m < D(Y, 9, 1): return 700.0
    return R2(p * _SEAS.get(cat, {}).get(m.month, 1.0))


# category, generation factor against the plan, transactions a month, accounts with weights, payees
_VARS = [('Groceries', 1.0, 9, [('AC-01', 1.0)], ['Grocery store', 'Neighbourhood market', 'Bulk food shop', 'Bakery']),
         ('Fuel and transport', 1.0, 4, [('AC-01', .7), ('AC-09', .3)], ['Fuel station', 'Parking and tolls', 'Transit pass']),
         ('Health costs', .85, 2, [('AC-01', 1.0)], ['Pharmacy', 'Clinic']),
         ('Household supplies', .75, 3, [('AC-01', 1.0)], ['Hardware store', 'Household shop']),
         ('Kids and family', .55, 3, [('AC-01', 1.0)], ['Toy shop', 'Bookshop', 'Sports shop', 'Kids clothing shop', 'School supplies shop']),
         ('Work and tax costs', .75, 1, [('AC-03', 1.0)], ['Office supplies shop', 'Print shop']),
         ('Eating out', .75, 5, [('AC-02', .4), ('AC-03', .4), ('AC-01', .2)], ['Restaurant', 'Cafe', 'Takeaway']),
         ('Shopping', 1.0, 4, [('AC-02', .4), ('AC-03', .4), ('AC-08', .2)], ['Clothing shop', 'Online shop', 'Department store']),
         ('Entertainment', .8, 2, [('AC-01', .6), ('AC-08', .4)], ['Cinema', 'Concert tickets', 'Games shop']),
         ('Personal care', 1.0, 2, [('AC-02', .5), ('AC-03', .5)], ['Hair salon', 'Pharmacy']),
         ('Other', 1.0, 1, [('AC-01', 1.0)], ['Post office', 'Photo shop'])]
_OWNER = {'AC-02': PARTNER1, 'AC-03': PARTNER2}
_PERSONAL = {'AC-02': 'Partner 1', 'AC-03': 'Partner 2'}


def _spread(r, total, n, lo, hi):
    ws = [r.uniform(.5, 1.5) for _ in range(n)]; s = sum(ws)
    amts = [R2(total * x / s) for x in ws]; amts[-1] = R2(total - sum(amts[:-1]))
    return amts, sorted(r.randint(lo, hi) for _ in range(n))


def _spending(w):
    r = rng('tx'); tx = []

    def add(d, acct, payee, cat, amt, paid_by=None, goal='', child='', kind='Spend'):
        if paid_by is None: paid_by = _OWNER.get(acct) or (PARTNER1 if r.random() < .48 else PARTNER2)
        tx.append(dict(date=d, account_id=acct, payee=payee, category=cat, amount=R2(amt), paid_by=paid_by, from_goal=goal, _child=child))
    # variable spending by month
    for m in _MONTHS:
        cur = (m == _ms(TODAY)); last = TODAY.day if cur else _dim(m.year, m.month); frac = (last / float(_dim(m.year, m.month))) if cur else 1.0
        for cat, gf, n, accts, payees in _VARS:
            plan = plan_amount(cat, m) * gf
            fac = 1.18 if (cat == 'Groceries' and cur) else r.uniform(.92, 1.06) if cat != 'Groceries' else r.uniform(.95, 1.08)
            total = plan * fac * frac; ne = max(1, int(round(n * frac))) if cur else n
            if cat in ('Other', 'Work and tax costs') and not cur and r.random() < .35: continue
            amts, days = _spread(r, total, ne, 1, last)
            for a, dd in zip(amts, days):
                ac = r.choices([x[0] for x in accts], [x[1] for x in accts])[0]
                ch = ('Both children' if r.random() < .4 else 'Noa' if r.random() < .5 else 'Ike') if cat == 'Kids and family' else ''
                add(D(m.year, m.month, dd), ac, r.choice(payees), cat, a, child=ch)
        # lumpy car service
        for mm, amt in ((3, 310.0), (9, 430.0), (12, 120.0)):
            d = D(m.year, m.month, 11)
            if m.month == mm and d <= TODAY: add(d, 'AC-01', 'Garage', 'Car service', amt * r.uniform(.95, 1.08))
    # allowances every Saturday
    al = []; d = _next_dow(HISTORY_START, 5); i = 0
    while d <= TODAY:
        for kid, amt in (('Noa', 10.0 if d >= D(Y, 1, 1) else 8.0), ('Ike', 5.0 if d >= D(Y, 1, 1) else 4.0)):
            add(d, 'AC-01', 'Allowance ' + kid, 'Kids and family', amt, PARTNER1 if i % 2 == 0 else PARTNER2, child=kid)
            sv = .25 if kid == 'Noa' else .4
            al.append(dict(date=iso(d), child=kid, amount=amt, saved=R2(amt * sv * (1.0 if (i + (kid == 'Ike')) % 5 else 1.5)), paid_by=PARTNER1 if i % 2 == 0 else PARTNER2))
        d += day(7); i += 1
    for j, a in enumerate(al): a['allowance_id'] = 'AL-%04d' % (j + 1); a['month'] = iso(_ms(to_date(a['date']))); a['spent'] = R2(a['amount'] - a['saved'])
    w['allowances'] = al
    # sinking-fund spending (paid from the goal's account)
    def lump(goal, acct, cat, payee, d, amt, parts=1):
        if not (HISTORY_START <= d <= TODAY): return
        for k in range(parts): add(d + day(k * 2), acct, payee, cat, amt / parts, goal=goal)
    for yy in (Y - 2, Y - 1, Y):
        lump('SG-03', 'AC-05', 'Holidays and trips', 'Shops and travel', D(yy, 12, 12), {Y - 2: 450.0, Y - 1: 1800.0, Y: 1800.0}[yy], 3)
        lump('SG-04', 'AC-05', 'Gifts', 'Gift shop', D(yy, 12, 8), 520.0 if yy != Y else 540.0, 2)
        lump('SG-04', 'AC-05', 'Gifts', 'Gift shop', D(yy, 11, 12), 180.0 + (yy - Y) * 10, 1)
        lump('SG-04', 'AC-05', 'Gifts', 'Gift shop', D(yy, 4, 9), 60.0, 1)
        lump('SG-07', 'AC-05', 'Kids and family', 'Activity fees', D(yy, 9, 3), 850.0 if yy == Y else 790.0)
        lump('SG-08', 'AC-05', 'Holidays and trips', 'Travel and lodging', D(yy, 8, 2), {Y - 2: 980.0, Y - 1: 1100.0, Y: 1350.0}[yy], 3)
        for (mm, dd_, amt) in ((1, 15, 1500.0 if yy == Y - 1 else 3600.0), (4, 15, 2800.0), (6, 15, 1900.0), (9, 15, 2800.0)):
            lump('SG-10', 'AC-06', 'Work and tax costs', 'Tax office payment', D(yy, mm, dd_), amt)
    lump('SG-06', 'AC-06', 'Household supplies', 'Repair person', D(Y - 1, 6, 10), 650.0)
    lump('SG-06', 'AC-06', 'Household supplies', 'Repair person', D(Y, 2, 10), 420.0)
    # bills that were paid
    for x in w['_bi']:
        if x['status'] == 'Paid':
            ch = {'Childcare provider': 'Ike', 'School costs': 'Both children', 'Kids activities club': 'Noa'}.get(x['bill'], '')
            add(x['paid_on'], x['account_id'], x['payee'], x['category'], x['amount'], goal=x['from_goal'], child=ch)
    # extra debt payments on the due day of each card
    EX = {'DB-01': 60.0, 'DB-02': 160.0, 'DB-03': 80.0}; w['_extra'] = EX
    for b in w['bills']:
        if b['debt_id'] in EX:
            for m in _MONTHS:
                d = _dd(m.year, m.month, b['due_day'])
                if m >= EXTRA_START and d <= TODAY: add(d, 'AC-01', b['payee'], 'Extra debt payment', EX[b['debt_id']])
    for d, nm, acct, p, sid in w['_sub_charges']: add(d, acct, nm, 'Subscriptions', p)
    w['_tx'] = tx


def _shared(w):
    r = rng('shared'); sc = []
    cats = [('Household supplies', ['Hardware store', 'Household shop'], 18, 120), ('Kids and family', ['Toy shop', 'Bookshop', 'Sports shop'], 20, 140),
            ('Eating out', ['Restaurant', 'Takeaway'], 25, 110), ('Entertainment', ['Cinema', 'Games shop'], 15, 90), ('Health costs', ['Pharmacy', 'Clinic'], 15, 80)]
    ms = _MONTHS
    story_months = ms[-4:-1]; calm = ms[-5]
    for m in ms:
        cur = (m == _ms(TODAY)); last = TODAY.day if cur else _dim(m.year, m.month); n = max(2, int(round(7 * (last / float(_dim(m.year, m.month)))))) if cur else 7
        items = []
        for _ in range(n):
            cat, pay, lo, hi = r.choice(cats); items.append([D(m.year, m.month, r.randint(1, last)), cat, r.choice(pay), R2(r.uniform(lo, hi))])
        items.sort(key=lambda x: -x[3]); tot = sum(x[3] for x in items)
        p2 = 0.0
        if m in story_months:
            for it in items:
                it.append(PARTNER2 if p2 < .60 * tot else PARTNER1); p2 += it[3] if it[4] == PARTNER2 else 0
        elif m == calm:
            for it in items: it.append(PARTNER1 if (p2 + it[3]) > .30 * tot and False else (PARTNER2 if p2 + it[3] <= .30 * tot else PARTNER1)); p2 += it[3] if it[4] == PARTNER2 else 0
        else:
            for it in items: it.append(PARTNER2 if r.random() < .42 else PARTNER1)
        sc += [(it[0], it[1], it[2], it[3], it[4]) for it in items]
    sc.sort(key=lambda x: (x[0], x[3]))
    rows = []
    for i, (d, cat, payee, amt, who) in enumerate(sc):
        rows.append(dict(shared_id='SC-%04d' % (i + 1), date=iso(d), month=iso(_ms(d)), description=payee, category=cat, amount=amt, paid_by=who, agreed_p1=AGREED_P1_SHARE, split_rule='Income share'))
        w['_tx'].append(dict(date=d, account_id='AC-02' if who == PARTNER1 else 'AC-03', payee=payee, category=cat, amount=amt, paid_by=who, from_goal='',
                             _child=('Both children' if cat == 'Kids and family' else '')))
    w['shared'] = rows
    # settle up: complete months before the three story months are settled in the next month
    se = []; by = {}
    for x in rows: by.setdefault(x['month'], {PARTNER1: 0.0, PARTNER2: 0.0}); by[x['month']][x['paid_by']] += x['amount']
    for m in ms[:-1]:
        v = by.get(iso(m), {PARTNER1: 0.0, PARTNER2: 0.0}); tot = v[PARTNER1] + v[PARTNER2]
        owe2 = R2(v[PARTNER2] - tot * (1 - AGREED_P1_SHARE))        # >0: partner 1 owes partner 2
        settled = m in ms[:-4]
        se.append(dict(month=iso(m), total=R2(tot), p1_paid=R2(v[PARTNER1]), p2_paid=R2(v[PARTNER2]), from_partner=PARTNER1 if owe2 > 0 else PARTNER2, to_partner=PARTNER2 if owe2 > 0 else PARTNER1,
                       amount=abs(owe2), settled_on=iso(add_months(m, 1) + day(4)) if settled else ''))
    for i, s in enumerate(se): s['settle_id'] = 'SE-%02d' % (i + 1)
    w['settle'] = se


# ------------------------------------------------------------------ goals, contributions, retirement, debts
def _next(m, d):
    x = D(Y, m, d)
    return x if x >= TODAY else D(Y + 1, m, d)


# id, goal, kind, account, target, target date, priority, saved now (None = from rows, opening 0), first month index (0 = all history)
_GOALS = [('SG-01', 'Emergency fund', 'Emergency fund', 'AC-04', 20000.0, TODAY + day(540), 'High', 11800.0),
          ('SG-02', 'Car insurance yearly premium', 'Sinking fund', 'AC-06', 1260.0, CAR_INS_DATE, 'High', 600.0),
          ('SG-03', 'Holidays', 'Sinking fund', 'AC-05', 1800.0, _next(12, 12), 'Medium', 1450.0),
          ('SG-04', 'Gifts', 'Sinking fund', 'AC-05', 700.0, _next(12, 8), 'Medium', 430.0),
          ('SG-05', 'Car replacement', 'Savings goal', 'AC-06', 9000.0, TODAY + day(300), 'Medium', 4750.0),
          ('SG-06', 'Home repairs', 'Sinking fund', 'AC-06', 3000.0, TODAY + day(400), 'Low', 1640.0),
          ('SG-07', "Kids' activities", 'Sinking fund', 'AC-05', 900.0, _next(9, 3), 'Medium', 520.0),
          ('SG-08', 'Family trip', 'Savings goal', 'AC-05', 2400.0, _next(8, 2), 'High', 1500.0),
          ('SG-09', 'New laptop', 'Savings goal', 'AC-05', 1350.0, TODAY + day(120), 'Low', None),
          ('SG-10', 'Tax set-aside', 'Sinking fund', 'AC-06', 4200.0, _next(1, 15), 'High', 3100.0)]


def _goals(w):
    r = rng('goals'); ct = []
    spend_by = {}
    for x in w['_tx']:
        if x['from_goal'] and x['date'] <= TODAY: ct.append(dict(date=x['date'], goal_id=x['from_goal'], kind='Spend', amount=x['amount'], account_id=x['account_id'], from_account=''))
    for gid, nm, kind, acct, tgt, td, pr, saved in _GOALS:
        if gid == 'SG-10':
            for x in w['income']:
                if x['set_aside'] > 0 and to_date(x['date']) <= TODAY: ct.append(dict(date=to_date(x['date']), goal_id=gid, kind='Deposit', amount=x['set_aside'], account_id=acct, from_account='AC-01'))
            continue
        for m in _MONTHS:
            d = _dd(m.year, m.month, 4)
            if d > TODAY: continue
            if gid == 'SG-09' and m < month_start(5): continue
            if gid == 'SG-02': amt = 95.0 if d <= CAR_INS_DATE - day(365) else 45.0
            else: amt = R2(GOAL_MONTHLY[gid] * r.uniform(.85, 1.0))
            ct.append(dict(date=d, goal_id=gid, kind='Deposit', amount=amt, account_id=acct, from_account='AC-01'))
    ct.sort(key=lambda x: (x['date'], x['goal_id']))
    gname = {g[0]: g[1] for g in _GOALS}
    net = {}
    for x in ct: net[x['goal_id']] = net.get(x['goal_id'], 0.0) + (x['amount'] if x['kind'] == 'Deposit' else -x['amount'])
    openg = {}
    for gid, nm, kind, acct, tgt, td, pr, saved in _GOALS: openg[gid] = 0.0 if saved is None else R2(saved - net.get(gid, 0.0))
    w['_goal_open'] = openg; w['_ct'] = ct
    w['contributions'] = [dict(contribution_id='CT-%04d' % (i + 1), date=iso(x['date']), month=iso(_ms(x['date'])), goal_id=x['goal_id'], goal=gname[x['goal_id']], kind=x['kind'],
                               amount=x['amount'], account_id=x['account_id'], from_account=x['from_account']) for i, x in enumerate(ct)]
    rows = []
    for gid, nm, kind, acct, tgt, td, pr, saved in _GOALS:
        sv = R2(openg[gid] + net.get(gid, 0.0))
        rows.append(dict(goal_id=gid, goal=nm, kind=kind, account_id=acct, target=tgt, target_date=iso(td), monthly_amount=GOAL_MONTHLY[gid], saved=sv, priority=pr,
                         start_date=iso(HISTORY_START if gid != 'SG-09' else month_start(5))))
    w['goals'] = rows


def _retire(w):
    r = rng('retire'); rt = []
    for x in w['income']:
        if x['retirement'] > 0: rt.append(dict(date=to_date(x['date']), account_id='AC-12', person=PARTNER1, source='Payroll', employee_amount=x['retirement'], employer_amount=R2(x['retirement'] * .5)))
    for m in _MONTHS:
        for dd, acct, who, amt in ((7, 'AC-13', PARTNER2, 250.0), (8, 'AC-14', 'Joint', 120.0)):
            d = _dd(m.year, m.month, dd)
            if d <= TODAY: rt.append(dict(date=d, account_id=acct, person=who, source='Transfer', employee_amount=amt, employer_amount=0.0))
    rt.sort(key=lambda x: (x['date'], x['account_id']))
    w['_rt'] = rt
    w['retirement'] = [dict(rt_id='RT-%04d' % (i + 1), date=iso(x['date']), month=iso(_ms(x['date'])), account_id=x['account_id'], person=x['person'], source=x['source'],
                            employee_amount=x['employee_amount'], employer_amount=x['employer_amount'], total=R2(x['employee_amount'] + x['employer_amount'])) for i, x in enumerate(rt)]


_DEBTS = [('DB-01', 'Card A', 'Credit card', 'AC-07', .2499, 140.0, 21, 5600.0, 0.0, 0, 'Joint'),
          ('DB-02', 'Card B', 'Credit card', 'AC-08', .1999, 85.0, 24, 3300.0, 0.0, 0, 'Partner 1'),
          ('DB-03', 'Card C', 'Credit card', 'AC-09', .1599, 60.0, 27, 2100.0, 0.0, 0, 'Partner 2'),
          ('DB-04', 'Car loan', 'Instalment loan', 'AC-10', .0699, 412.0, 9, 13600.0, 26000.0, 72, 'Joint'),
          ('DB-05', 'Student loan', 'Instalment loan', 'AC-11', .045, 285.0, 15, 17400.0, 28000.0, 120, 'Partner 1')]


def _debts(w):
    chg = {}
    for x in w['_tx']:
        if x['account_id'] in ('AC-07', 'AC-08', 'AC-09') and x['date'] <= TODAY and x['from_goal'] == '':
            k = (x['account_id'], _ms(x['date'])); chg[k] = chg.get(k, 0.0) + x['amount']
    EX = w['_extra']; rows = []; dps = []; series = {}; opens = {}

    def run(did, acct, rate, mn, dday, opening, rec):
        bal = opening; out = {}
        for m in _MONTHS:
            interest = bal * rate / 12.0; bal += interest; bal += chg.get((acct, m), 0.0)
            d = _dd(m.year, m.month, dday); ex = EX.get(did, 0.0) if m >= EXTRA_START else 0.0
            if d <= TODAY:
                bal -= (mn + ex)
                if rec is not None: rec.append((d, did, mn, ex, R2(interest), m))
            out[m] = bal
        return out
    for did, nm, kind, acct, rate, mn, dday, tgt, orig, term, own in _DEBTS:
        e0 = run(did, acct, rate, mn, dday, 0.0, None)[_MONTHS[-1]]
        g = 1.0
        for _ in _MONTHS: g *= (1 + rate / 12.0)
        op = (tgt - e0) / g; opens[did] = R2(op)
        rec = []; ser = run(did, acct, rate, mn, dday, op, rec); series[acct] = ser
        for d, _id, a, b, intr, m in rec:
            dps.append(dict(date=d, debt_id=did, debt=nm, minimum=a, extra=b, amount=R2(a + b), interest=intr, principal=R2(a + b - intr), balance_after=R2(ser[m]), month=_ms(d)))
        rows.append(dict(debt_id=did, debt=nm, kind=kind, account_id=acct, balance=tgt, rate=rate, min_payment=mn, due_day=dday, extra_planned=EX.get(did, 0.0), original_amount=orig,
                         term_months=term, owner=own, opened=iso(HISTORY_START)))
    dps.sort(key=lambda x: (x['date'], x['debt_id']))
    w['debts'] = rows; w['_debt_open'] = opens; w['_debt_series'] = series
    w['debt_payments'] = [dict(payment_id='DP-%04d' % (i + 1), date=iso(x['date']), month=iso(x['month']), debt_id=x['debt_id'], debt=x['debt'], minimum=x['minimum'], extra=x['extra'],
                               amount=x['amount'], interest=x['interest'], principal=x['principal'], balance_after=x['balance_after']) for i, x in enumerate(dps)]


def sim12(extra, months=12):
    """Interest charged over the next months if the extra payment is split as in extra {debt_id: amount} (a helper for the story and the tests)."""
    bal = {d['debt_id']: float(d['balance']) for d in w_cached()['debts']}; tot = 0.0
    rate = {d['debt_id']: d['rate'] for d in w_cached()['debts']}; mn = {d['debt_id']: d['min_payment'] for d in w_cached()['debts']}
    for _ in range(months):
        for k in bal:
            i = bal[k] * rate[k] / 12.0; tot += i; bal[k] += i - min(bal[k] + i, mn[k] + extra.get(k, 0.0))
    return R2(tot)


# ------------------------------------------------------------------ accounts, balances, net worth
_ACCTS = [('AC-01', 'Joint checking', 'Checking', 'Joint'), ('AC-02', 'Partner 1 checking', 'Checking', 'Partner 1'), ('AC-03', 'Partner 2 checking', 'Checking', 'Partner 2'),
          ('AC-04', 'Emergency savings', 'Savings', 'Joint'), ('AC-05', 'Family goals savings', 'Savings', 'Joint'), ('AC-06', 'Car and home savings', 'Savings', 'Joint'),
          ('AC-07', 'Card A', 'Credit card', 'Joint'), ('AC-08', 'Card B', 'Credit card', 'Partner 1'), ('AC-09', 'Card C', 'Credit card', 'Partner 2'),
          ('AC-10', 'Car loan', 'Loan', 'Joint'), ('AC-11', 'Student loan', 'Loan', 'Partner 1'), ('AC-12', 'Retirement account partner 1', 'Retirement', 'Partner 1'),
          ('AC-13', 'Retirement account partner 2', 'Retirement', 'Partner 2'), ('AC-14', 'Brokerage account', 'Brokerage', 'Joint')]
_RET_OPEN = {'AC-12': 18500.0, 'AC-13': 9800.0, 'AC-14': 6300.0}


def _eom(d): return D(d.year, d.month, _dim(d.year, d.month))


def _cum(events, opening, ends):
    """balance at each date in ends (inclusive) from dated (date, amount) events"""
    ev = sorted(events, key=lambda e: e[0]); out = {}; i = 0; b = opening
    for e in ends:
        while i < len(ev) and ev[i][0] <= e: b += ev[i][1]; i += 1
        out[e] = b
    return out


def _balances(w):
    r = rng('bal'); tx = w['_tx']; ends = [min(_eom(m), TODAY) for m in _MONTHS]
    # personal spending money: the monthly transfer from the joint account covers the average personal spending
    tr = []
    for acct in ('AC-02', 'AC-03'):
        out = sum(x['amount'] for x in tx if x['account_id'] == acct); side = sum(to_date(x['date']) and x['net'] for x in w['income'] if x['account_id'] == acct)
        amt = max(150.0, _r25((out - side) / 25.0)); w['_pers_' + acct] = amt
        for m in _MONTHS:
            d = _dd(m.year, m.month, 3)
            if d <= TODAY: tr.append(dict(date=d, from_account='AC-01', to_account=acct, amount=amt, purpose='Personal spending money'))
    for s in w['settle']:
        if s['settled_on'] and s['amount'] > 0:
            fa, ta = ('AC-02', 'AC-03') if s['from_partner'] == PARTNER1 else ('AC-03', 'AC-02')
            tr.append(dict(date=to_date(s['settled_on']), from_account=fa, to_account=ta, amount=s['amount'], purpose='Settle up'))
    tr.sort(key=lambda x: (x['date'], x['to_account']))
    w['transfers'] = [dict(transfer_id='TR-%04d' % (i + 1), date=iso(x['date']), month=iso(_ms(x['date'])), from_account=x['from_account'], to_account=x['to_account'], amount=x['amount'],
                           purpose=x['purpose']) for i, x in enumerate(tr)]
    ev = {a[0]: [] for a in _ACCTS}
    for x in w['income']: ev[x['account_id']].append((to_date(x['date']), x['net']))
    for x in tx:
        if x['from_goal'] == '' and x['account_id'] in ('AC-01', 'AC-02', 'AC-03'): ev[x['account_id']].append((x['date'], -x['amount']))
    for x in w['_ct']:
        if x['kind'] == 'Deposit': ev['AC-01'].append((x['date'], -x['amount']))
    for x in w['_rt']:
        if x['source'] == 'Transfer': ev['AC-01'].append((x['date'], -x['employee_amount']))
    for x in tr:
        ev[x['from_account']].append((x['date'], -x['amount'])); ev[x['to_account']].append((x['date'], x['amount']))
    # the story: a bill due in 5 days pushes joint checking under the floor before the next payday
    sb = [b for b in w['_bi'] if b['bill'] == 'Childcare provider' and b['due_date'] == STORY_BILL_DATE][0]
    others = sum(b['amount'] for b in w['_bi'] if b['account_id'] == 'AC-01' and b['status'] in ('Late', 'Unpaid') and b['due_date'] <= STORY_BILL_DATE and b is not sb)
    b0 = CASH_FLOOR + sb['amount'] - 150.0 + others
    flow = sum(a for d, a in ev['AC-01'] if d <= TODAY)
    openings = {'AC-01': R2(b0 - flow)}
    for a in ('AC-02', 'AC-03'):
        e = sorted(ev[a]); c = 0.0; mn = 0.0
        for d, amt in e:
            if d <= TODAY: c += amt; mn = min(mn, c)
        openings[a] = max(150.0, R2(120.0 - mn))
    ser = {a: _cum([e for e in ev[a] if e[0] <= TODAY], openings[a], ends) for a in ('AC-01', 'AC-02', 'AC-03')}
    w['_b0'] = b0; w['_story_bill'] = sb
    # goal accounts
    gsum = {}
    for gid, nm, kind, acct, tgt, td, pr, saved in _GOALS: gsum.setdefault(acct, []).append(gid)
    for acct, gids in gsum.items():
        evs = [(x['date'], x['amount'] if x['kind'] == 'Deposit' else -x['amount']) for x in w['_ct'] if x['goal_id'] in gids]
        openings[acct] = R2(sum(w['_goal_open'][g] for g in gids)); ser[acct] = _cum(evs, openings[acct], ends)
    # cards and loans: month-end balances from the debt simulation
    for acct, s in w['_debt_series'].items():
        ser[acct] = {e: s[m] for e, m in zip(ends, _MONTHS)}
    for did, nm, kind, acct, *_ in _DEBTS: openings[acct] = w['_debt_open'][did]
    # retirement and brokerage: contributions plus a made-up growth of about half a percent a month (an example, not a forecast)
    for acct in ('AC-12', 'AC-13', 'AC-14'):
        bal = _RET_OPEN[acct]; s = {}; openings[acct] = bal
        for m, e in zip(_MONTHS, ends):
            bal = bal * (1 + r.uniform(-.008, .018)) + sum(x['employee_amount'] + x['employer_amount'] for x in w['_rt'] if x['account_id'] == acct and _ms(x['date']) == m)
            s[e] = bal
        ser[acct] = s
    nw = []; k = 0
    for m, e in zip(_MONTHS, ends):
        for acct, nm, typ, own in _ACCTS:
            k += 1
            nw.append(dict(nw_id='NW-%04d' % k, month=iso(m), as_of=iso(e), account_id=acct, account=nm, type=typ, side='Liability' if typ in ('Credit card', 'Loan') else 'Asset', balance=R2(ser[acct][e])))
    w['networth'] = nw
    now = {x['account_id']: x['balance'] for x in nw if x['month'] == iso(_ms(TODAY))}
    w['accounts'] = [dict(account_id=a, account=nm, type=t, owner=o, opening_balance=R2(openings[a]), opened=iso(HISTORY_START), balance_now=now[a],
                          side='Liability' if t in ('Credit card', 'Loan') else 'Asset') for a, nm, t, o in _ACCTS]


# ------------------------------------------------------------------ other tables
def _others(w):
    r = rng('other')
    # contracts and insurance
    cn = [('Rent lease', 'Rent', 'HF-06', 1650.0, 'Monthly', TODAY + day(120), 60), ('Car insurance', 'Insurance', 'HF-11', 1260.0, 'Yearly', CAR_INS_DATE, 30),
          ('Renters insurance', 'Insurance', 'HF-11', 24.0, 'Monthly', TODAY + day(210), 30), ('Life insurance', 'Insurance', 'HF-11', 46.0, 'Monthly', TODAY + day(300), 30),
          ('Electricity supply', 'Utility', 'HF-15', 92.0, 'Monthly', TODAY + day(80), 30), ('Gas supply', 'Utility', 'HF-15', 70.0, 'Monthly', TODAY + day(150), 30),
          ('Internet plan', 'Phone and internet', 'HF-15', 65.0, 'Monthly', TODAY + day(40), 30), ('Phone plan', 'Phone and internet', 'HF-15', 96.0, 'Monthly', TODAY + day(260), 30),
          ('Childcare agreement', 'Rent', 'HF-12', 560.0, 'Monthly', TODAY + day(290), 45), ('Car loan agreement', 'Loan', 'HF-16', 412.0, 'Monthly', TODAY + day(1000), 0),
          ('Student loan agreement', 'Loan', 'HF-16', 285.0, 'Monthly', TODAY + day(2500), 0)]
    w['contracts'] = [dict(contract_id='CN-%02d' % (i + 1), contract=a, kind=b, contact_id=c, amount=d, cycle=e, yearly_cost=R2(d * (12 if e == 'Monthly' else 1)), renewal_date=iso(f), notice_days=g,
                           review_on=iso(f - day(REVIEW_DAYS))) for i, (a, b, c, d, e, f, g) in enumerate(cn)]
    # tax documents: last year all in, this year in progress
    tdr = []
    docs = [('Income statement', 'Pay statement for the year, partner 1', 'HF-07', 'Partner 1'), ('Income statement', 'Client A payments for the year', 'HF-08', 'Partner 2'),
            ('Income statement', 'Client B payments for the year', 'HF-09', 'Partner 2'), ('Interest statement', 'Savings interest for the year', 'HF-16', 'Joint'),
            ('Interest statement', 'Student loan interest for the year', 'HF-16', 'Partner 1'), ('Investment statement', 'Brokerage year-end statement', 'HF-16', 'Joint'),
            ('Investment statement', 'Retirement contributions summary', 'HF-16', 'Partner 1'), ('Charity receipt', 'Charity gifts, receipts kept', '', 'Joint'),
            ('Medical receipt', 'Medical costs, receipts kept', '', 'Joint'), ('Work-expense receipt', 'Work expenses, partner 2', '', 'Partner 2'),
            ('Childcare receipt', 'Childcare costs for the year', 'HF-12', 'Joint'), ('Tax payment record', 'Estimated payments made', '', 'Partner 2'),
            ('Work-expense receipt', 'Work expenses, partner 1', '', 'Partner 1'), ('Tax payment record', 'Final payment record', '', 'Partner 2')]
    for yy in (Y - 1, Y):
        for i, (t, dsc, src, who) in enumerate(docs):
            exp = D(yy + 1, 1, 10) + day(i * 3) if t not in ('Charity receipt', 'Medical receipt', 'Work-expense receipt', 'Tax payment record') else D(yy, 12, 20) - day(i)
            if yy == Y - 1: rec = exp + day(r.randint(0, 6)); filed = True
            else:
                got = t in ('Charity receipt', 'Medical receipt', 'Work-expense receipt', 'Childcare receipt', 'Tax payment record') and i != 13
                rec = (TODAY - day(r.randint(5, 80))) if got else None; filed = False
            tdr.append(dict(tax_year=yy, doc_type=t, description=dsc, source_id=src, person=who, expected_on=iso(exp), received_on=iso(rec) if rec else '', filed=filed,
                            due_date=iso(D(yy + 1, 4, 15))))
    for i, x in enumerate(tdr): x['doc_id'] = 'TD-%02d' % (i + 1)
    w['tax_docs'] = tdr
    # deduction records
    dc = {'Home office costs': (['Desk lamp', 'Office chair', 'Share of internet cost', 'Shelving'], 20, 180), 'Work travel': (['Train to a client meeting', 'Parking at a client site', 'Taxi to a client'], 8, 70),
          'Equipment and supplies': (['Printer paper', 'External drive', 'Cables and adapters', 'Headset'], 10, 120), 'Professional fees': (['Invoicing tool', 'Accountant call', 'Contract template'], 20, 160),
          'Charity gifts': (['Donation to a local charity', 'Charity run entry'], 15, 120), 'Medical costs': (['Medical costs'], 20, 240), 'Childcare': (['Holiday childcare week'], 120, 420),
          'Education': (['Online course', 'Workshop fee'], 40, 300)}
    dr = []
    for m in _MONTHS:
        cur = (m == _ms(TODAY)); last = TODAY.day if cur else _dim(m.year, m.month)
        for _ in range(1 if cur else 5):
            cat = r.choices(list(dc), [4, 3, 4, 2, 3, 3, 1, 1])[0]; dsc, lo, hi = dc[cat]
            d = D(m.year, m.month, r.randint(1, last)); ok = r.random() > (.16 if d.year == Y else .05)
            dr.append(dict(date=d, description=r.choice(dsc), category=cat, amount=R2(r.uniform(lo, hi)), receipt=ok, tax_year=d.year, person=PARTNER2 if cat in ('Home office costs', 'Work travel',
                           'Equipment and supplies', 'Professional fees') else r.choice(['Joint', PARTNER1, PARTNER2])))
    dr.sort(key=lambda x: x['date'])
    w['deductions'] = [dict(deduction_id='DR-%04d' % (i + 1), date=iso(x['date']), month=iso(_ms(x['date'])), description=x['description'], category=x['category'], amount=x['amount'],
                            receipt=x['receipt'], tax_year=x['tax_year'], person=x['person']) for i, x in enumerate(dr)]
    # big purchases and their options
    sv = {g['goal_id']: g['saved'] for g in w['goals']}
    bp = [('BP-01', 'Used car', 'Car', TODAY + day(300), 11500.0, sv['SG-05'], 'SG-05', 'High', 'Saving'), ('BP-02', 'Move to a bigger home', 'Move', TODAY + day(330), 9800.0, 2100.0, '', 'Medium', 'Planning'),
          ('BP-03', 'Washing machine', 'Equipment', TODAY + day(60), 780.0, 300.0, '', 'Medium', 'Saving'), ('BP-04', 'Family trip next summer', 'Family trip', _next(8, 2), 2400.0, sv['SG-08'], 'SG-08', 'High', 'Saving'),
          ('BP-05', 'New laptop', 'Equipment', TODAY + day(120), 1350.0, sv['SG-09'], 'SG-09', 'Low', 'Saving'), ('BP-06', 'Furniture for the new home', 'Home', TODAY + day(360), 1900.0, 0.0, '', 'Low', 'Planning')]
    w['big_purchases'] = [dict(bp_id=a, item=b, kind=c, planned_date=iso(d), target=e, saved=f, goal_id=g, priority=h, status=i) for a, b, c, d, e, f, g, h, i in bp]
    bo = [('BP-01', 'Used hatchback, 4 years old', 13500.0, 3000.0, 1500.0, 48, .079, 320.0), ('BP-01', 'Used estate, 6 years old', 11200.0, 3000.0, 1500.0, 36, .079, 350.0),
          ('BP-01', 'Keep the current car', 0.0, 0.0, 0.0, 0, 0.0, 395.0), ('BP-02', 'Larger rented flat', 0.0, 2600.0, 0.0, 0, 0.0, 1950.0),
          ('BP-02', 'Buy a small house', 310000.0, 40000.0, 0.0, 300, .059, 520.0), ('BP-02', 'Stay and renovate', 0.0, 0.0, 0.0, 0, 0.0, 1650.0),
          ('BP-03', 'Model A', 780.0, 0.0, 0.0, 0, 0.0, 6.0), ('BP-03', 'Model B', 640.0, 0.0, 0.0, 0, 0.0, 8.0), ('BP-04', 'Beach week', 2400.0, 0.0, 0.0, 0, 0.0, 0.0),
          ('BP-04', 'City break', 1500.0, 0.0, 0.0, 0, 0.0, 0.0), ('BP-05', 'Standard laptop', 1350.0, 0.0, 0.0, 0, 0.0, 0.0), ('BP-05', 'Basic laptop', 899.0, 0.0, 0.0, 0, 0.0, 0.0),
          ('BP-06', 'Used furniture set', 1900.0, 0.0, 0.0, 0, 0.0, 0.0), ('BP-06', 'New furniture set', 3200.0, 0.0, 0.0, 12, .0, 0.0)]
    w['purchase_options'] = [dict(option_id='BO-%02d' % (i + 1), bp_id=a, option=b, price=c, down_payment=d, trade_in=e, loan_months=f, rate=g, running_cost=h) for i, (a, b, c, d, e, f, g, h) in enumerate(bo)]
    sn = [('Lose one income', 'Income of partner 2 kept', 0.0, 'share'), ('Lose one income', 'Reduced hours of partner 1', .5, 'share'), ('Expense shock', 'One-off cost', 3500.0, 'amount'),
          ('Expense shock', 'Months without work', 2.0, 'months'), ('Interest-rate change', 'Rate change in points', .02, 'rate'), ('Mortgage switch', 'Price', 310000.0, 'amount'),
          ('Mortgage switch', 'Down payment', 40000.0, 'amount'), ('Mortgage switch', 'Yearly rate', .059, 'rate'), ('Mortgage switch', 'Term in years', 25.0, 'years'),
          ('Mortgage switch', 'Upkeep and local charges a year', 3100.0, 'amount'), ('New baby', 'One-off costs', 2400.0, 'amount'), ('New baby', 'Monthly costs', 420.0, 'amount'),
          ('New baby', 'Months of leave', 4.0, 'months'), ('New baby', 'Income change on leave', -.4, 'share'), ('Extra payment', 'Extra each month', EXTRA_PAYMENT, 'amount'),
          ('Growth example', 'Yearly growth, an example', GROWTH_RATE, 'rate')]
    w['scenarios'] = [dict(scenario_id='SN-%02d' % (i + 1), scenario=a, item=b, value=c, unit=d) for i, (a, b, c, d) in enumerate(sn)]
    # a family event budget (a celebration planned in 4 months) and the move plan
    ev = [('Venue hire', 600.0, 300.0, 60, True), ('Catering', 780.0, 0.0, 20, False), ('Cake', 95.0, 0.0, 10, False), ('Invitations', 45.0, 45.0, 90, False),
          ('Decorations', 120.0, 40.0, 25, False), ('Music or entertainment', 250.0, 100.0, 40, True), ('Photographer', 300.0, 0.0, 15, True),
          ('Drinks', 210.0, 0.0, 12, False), ('Outfits', 260.0, 120.0, 35, False), ('Travel for guests', 180.0, 0.0, 30, False), ('Tips and thank-you gifts', 90.0, 0.0, 5, False),
          ('Spare for surprises', 150.0, 0.0, 5, False)]
    w['event_items'] = [dict(event_item_id='EI-%02d' % (i + 1), event='Family celebration', item=a, estimate=b, paid=c, due_date=iso(TODAY + day(120 - d)), deposit=e,
                             target_total=2600.0) for i, (a, b, c, d, e) in enumerate(ev)]
    mv = [('Deposit on the new home', 3900.0, 0.0, 300, 'Deposit'), ('Moving company', 950.0, 0.0, 322, 'Moving'), ('Boxes and packing', 120.0, 60.0, 280, 'Moving'),
          ('Overlapping rent', 1650.0, 0.0, 300, 'Overlap'), ('Utilities connection', 140.0, 0.0, 310, 'Setup'), ('Internet installation', 70.0, 0.0, 315, 'Setup'),
          ('Cleaning of the old home', 220.0, 0.0, 330, 'Moving'), ('Repairs and paint', 380.0, 0.0, 320, 'Setup'), ('Mail redirect', 35.0, 0.0, 325, 'Setup'),
          ('Window blinds and lamps', 460.0, 0.0, 335, 'Setup'), ('Kitchen items', 280.0, 0.0, 335, 'Setup'), ('Spare for surprises', 600.0, 0.0, 335, 'Setup')]
    w['move_items'] = [dict(move_id='MV-%02d' % (i + 1), item=a, estimate=b, paid=c, due_date=iso(TODAY + day(d)), kind=k, move_date=iso(TODAY + day(330))) for i, (a, b, c, d, k) in enumerate(mv)]
    # budget plan lines
    bu = []; k = 0
    for m in _MONTHS + [add_months(_ms(TODAY), j) for j in range(1, 13)]:
        for c, g in CATEGORIES:
            p = plan_amount(c, m)
            if p > 0: k += 1; bu.append(dict(plan_id='BU-%04d' % k, month=iso(m), category=c, group=g, planned=p))
    w['budget'] = bu


def _finish(w):
    tx = sorted(w['_tx'], key=lambda x: (x['date'], x['account_id'], x['category'], x['amount']))
    an = {a[0]: a[1] for a in _ACCTS}; rows = []; kid = []
    for i, x in enumerate(tx):
        tid = 'TX-%05d' % (i + 1)
        rows.append(dict(tx_id=tid, date=iso(x['date']), month=iso(_ms(x['date'])), account_id=x['account_id'], account=an[x['account_id']], payee=x['payee'], category=x['category'],
                         group=CAT_GROUP[x['category']], amount=x['amount'], paid_by=x['paid_by'], from_goal=x['from_goal']))
        if x['_child'] and x['date'] <= TODAY:
            p = x['payee']
            kind = 'Allowance' if p.startswith('Allowance') else 'Childcare' if p == 'Childcare provider' else 'School costs' if p == 'School office' else 'Activities' if p in ('Activities club', 'Activity fees') \
                else 'Clothing' if p == 'Kids clothing shop' else 'Other'
            kid.append(dict(date=iso(x['date']), month=iso(_ms(x['date'])), child=x['_child'], kind=kind, amount=x['amount'], tx_id=tid))
    for i, k in enumerate(kid): k['kid_cost_id'] = 'KC-%04d' % (i + 1)
    w['tx'] = rows; w['kid_costs'] = kid


def _build():
    w = {}
    _income(w); _bills(w); _subs(w); _spending(w); _shared(w); _goals(w); _retire(w); _debts(w); _balances(w); _others(w); _finish(w)
    return w


def w_cached():
    if 'w' not in _CACHE: _CACHE['w'] = _build()
    return _CACHE['w']


_MAP = dict(account_rows='accounts', income_rows='income', invoice_rows='invoices', pay_schedule_rows='pay_schedule', bill_rows='bills', bill_due_rows='bill_due', tx_rows='tx',
            subscription_rows='subs', contract_rows='contracts', debt_rows='debts', debt_payment_rows='debt_payments', goal_rows='goals', contribution_rows='contributions',
            retirement_rows='retirement', transfer_rows='transfers', networth_rows='networth', shared_cost_rows='shared', settle_rows='settle', kid_cost_rows='kid_costs',
            allowance_rows='allowances', tax_doc_rows='tax_docs', deduction_rows='deductions', big_purchase_rows='big_purchases', purchase_option_rows='purchase_options',
            scenario_rows='scenarios', budget_rows='budget', event_item_rows='event_items', move_item_rows='move_items')


def _mk(key):
    def f(n=None): return _thin([dict(x) for x in w_cached()[key]], n)
    return f


for _nm, _k in _MAP.items():
    globals()[_nm] = _mk(_k); globals()[_nm].__name__ = _nm
_GENS = list(_MAP)


# ------------------------------------------------------------------ story
def story():
    """Ids of the story rows, with the values that make each one true (all asserted)."""
    w = w_cached(); bi = w['_bi']
    sb = w['_story_bill']
    assert 4 <= (sb['due_date'] - TODAY).days <= 6 and sb['due_date'] < PAYDAY1_NEXT
    due = sorted((b for b in bi if b['account_id'] == 'AC-01' and b['status'] in ('Late', 'Unpaid') and b['due_date'] < PAYDAY1_NEXT), key=lambda b: b['due_date'])
    before = w['_b0'] - sum(b['amount'] for b in due if b['due_date'] <= STORY_BILL_DATE and b is not sb)
    assert before >= CASH_FLOOR and before - sb['amount'] < CASH_FLOOR, (before, sb['amount'])
    low = R2(w['_b0'] - sum(b['amount'] for b in due))
    bill_id = [x for x in w['bills'] if x['bill'] == 'Childcare provider'][0]['bill_id']
    due_id = [x['due_id'] for x in w['bill_due'] if x['bill_id'] == bill_id and x['due_date'] == iso(STORY_BILL_DATE)][0]
    # subscriptions
    now = sum(s['monthly_cost'] for s in w['subs']); then = sum(s['price_6m_ago'] / (12.0 if s['cycle'] == 'Yearly' else 1.0) for s in w['subs'])
    assert 1.33 <= now / then <= 1.47, now / then
    unused = [s['sub_id'] for s in w['subs'] if (TODAY - to_date(s['last_used'])).days >= SUB_UNUSED_DAYS]
    assert len(unused) == 2, unused
    # groceries
    m0 = _ms(TODAY); frac = TODAY.day / float(_dim(TODAY.year, TODAY.month))
    mtd = sum(x['amount'] for x in w['tx'] if x['category'] == 'Groceries' and x['month'] == iso(m0))
    ratio = mtd / (plan_amount('Groceries', m0) * frac); assert 1.12 <= ratio <= 1.24, ratio
    plan_line = [x['plan_id'] for x in w['budget'] if x['category'] == 'Groceries' and x['month'] == iso(m0)][0]
    # debt order broken
    cards = sorted((d for d in w['debts'] if d['kind'] == 'Credit card'), key=lambda d: -d['rate'])
    assert cards[0]['extra_planned'] < max(c['extra_planned'] for c in cards[1:])
    lower = max(cards[1:], key=lambda c: c['extra_planned'])
    lost = R2(sim12({d['debt_id']: d['extra_planned'] for d in w['debts']}) - sim12({cards[0]['debt_id']: EXTRA_PAYMENT})); assert lost > 0, lost
    # car insurance fund
    g = [x for x in w['goals'] if x['goal'] == 'Car insurance yearly premium'][0]
    left = (to_date(g['target_date']) - TODAY).days; assert 40 <= left <= 60
    assert g['saved'] + g['monthly_amount'] * left / 30.4 < g['target'], g
    # shared costs: partner 2 over the agreed share three complete months in a row
    ms = [iso(month_start(k)) for k in (4, 3, 2, 1)]; share = {}
    for m in ms:
        rows = [x for x in w['shared'] if x['month'] == m]; tot = sum(x['amount'] for x in rows)
        share[m] = sum(x['amount'] for x in rows if x['paid_by'] == PARTNER2) / tot
    agreed2 = 1 - AGREED_P1_SHARE
    assert all(share[m] > agreed2 + .05 for m in ms[1:]) and share[ms[0]] <= agreed2 + .03, share
    return dict(bill=bill_id, bill_due=due_id, account='AC-01', payday=iso(PAYDAY1_NEXT), low_point=low, subs_unused=unused, subs_ratio=round(now / then, 3), plan_line=plan_line,
                groceries_ratio=round(ratio, 3), debt=cards[0]['debt_id'], debt_lower=lower['debt_id'], interest_lost_year=lost, goal=g['goal_id'], shared_months=ms[1:])


if __name__ == '__main__':
    for nm in _GENS: print(nm, len(globals()[nm]()))
    print(story())
