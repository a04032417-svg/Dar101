"""wp_core - shared demo data for the Wedding Planning suite (Dar Templates, English edition).

Wedding: "Amara and Theo" (partner 1 and partner 2). One venue for ceremony and reception, seated capacity 130; 150 guests invited in 82 households
  (A list and B list), about 118 expected; total budget about 34,000 in one generic currency paid by the couple, partner 1's family and partner 2's family
  (agreed shares 60 / 25 / 15); 16 vendors in generic words; 8 events; a wedding party of 10; 13 tables; a run of show; DIY projects; gifts; a honeymoon.
All rows are deterministic, oldest first; n= thins a list but keeps the most recent rows; optional dates are ''.
Dates are relative to TODAY (env WP_TODAY overrides): engaged about 9 months ago, wedding day (a Saturday) about 200 days ahead, RSVP reply-by date in 21 days.
Digital invitations and save-the-dates went out early (travel guests, room block); the printed invitation suite is the overdue task on the critical path.

Constants: COUPLE, PARTNER1, PARTNER2, SUITE, TODAY, WEDDING_DAY, ENGAGED_ON, SAVE_THE_DATE_ON, INVITE_A_ON, INVITE_B_ON, RSVP_DEADLINE, HEADCOUNT_DATE,
  ROOM_CUTOFF, VENUE_CAPACITY (130), TOTAL_BUDGET (34000), GUESTS_INVITED (150), TABLE_SIZE (10), VENUE_END ('23:30'), OVERTIME_RATE (per hour),
  AGREED_SHARES (payer -> 0..1), and the editable setting defaults (all "typical, edit" or "your own numbers"): RESERVE_PCT 0.05, EXPECTED_YES_RATE 0.80,
  TRAVEL_DECLINE_EXTRA 0.10, TIP_PCT 0.18, THANKYOU_TARGET_DAYS 56, THANKYOU_ALERT_DAYS 14, INVITE_LEAD_WEEKS 8, DIY_BUFFER_DAYS 14, DIY_HOUR_VALUE 12,
  OWNER_SHARE_MAX 0.5, COST_PER_GUEST_TARGET 300, COST_PER_GUEST_BENCHMARK 290, GUARANTEE_DAYS 21, HIDDEN_COST_PCT 0.09, CARD_FEE_PCT 0.0, PRIORITY_GAP 2.
Date helpers: day, iso, ago, ahead, to_date, month_start, add_months, months14, week_start, months_out, pairs, first_name, fake_phone, fake_email.
Lists (value lists, plain English): ROLES, TEAMS, OWNERS, SIDES, TIERS, LIST_AB, AGE_GROUPS, RSVP, CONTACT_STATUS, MEALS, DIETARY, REGIONS, LODGING, CHANNELS,
  BUDGET_CATEGORIES, PAYERS, FUND_SOURCES, FUND_STATUS, VENDOR_STATUS, CONTRACT_KINDS, PAY_KINDS, PAY_STATUS, METHODS, TASK_AREAS, TASK_STATUS, WHEN, PARTY_ROLES,
  ATTIRE_STATUS, TABLE_KINDS, RULE_KINDS, RULE_REASONS, RUN_BLOCKS, RUN_WHO, DIY_STATUS, SUPPLY_BASIS, SUPPLY_STATUS, GIFT_KINDS, GIFT_EVENTS, THANK_CHANNELS,
  EVENT_KINDS, EVENT_NAMES, EVENT_STATUS, HIDDEN_STATUS, TIP_BASIS, HONEY_KINDS, HONEY_OPTIONS, PAPER_KINDS, PAPER_STATUS, WEEKDAYS (see source); pairs(values).
People and reference tables: team (16 rows WP-01..WP-16: partner 1, partner 2, family helpers, wedding party leads, a friend helper, day-of coordinator, venue /
  caterer / photographer / band or DJ / florist contacts, officiant), payers (3 rows with agreed shares), budget categories via budget_rows.
Row generators (each takes n=None): household_rows (HH-01..HH-82), guest_rows (GS-001..GS-150), vendor_rows (VD-01..VD-16), quote_rows (QT-001..), contract_rows (CT-001..),
  payment_schedule_rows (PY-001.., due date, amount, paid on, status), payment_rows (PM-001.., what was paid, by whom), budget_rows (BL-01..BL-16: planned, committed, paid,
  payer shares), hidden_cost_rows (HC-01..), tip_rows (TP-01..TP-16, one per vendor), funding_rows (FS-001..: savings, family transfers, unconfirmed cash gifts), task_rows (TK-001..TK-140),
  party_rows (WPY-01..WPY-10 wedding party plus WPY-11..14 family helpers), table_rows (TB-01..TB-13), seat_rule_rows (SR-01..), run_rows (RS-01.. run-of-show steps), event_rows (EV-01..EV-08), roomblock_rows (RB-01..),
  diy_rows (DY-01..DY-14), supply_rows (SU-001..), event_line_rows (EL-01.., event budget lines), attire_rows (AT-01.., shopping rows incl. rings outside the budget), return_rows (RT-01.., rentals and deposits to return), gift_rows (GF-001..), thankyou_rows (TY-001..), honeymoon_rows (HM-01..), honeymoon_fund_rows (HF-001..), paperwork_rows (PW-01..).
story(): dict of the 6 story rows (asserted): payment (final balance of vendor, due in about 10 days, not covered by money set aside), rsvp (about 18 guests still silent
  three weeks before the reply-by date), budget (flowers category about 22% over plan), capacity (venue: everyone-says-yes headcount above the seated capacity),
  task (overdue critical-path task: invitations to the printer), gifts (shower gifts received more than 14 days ago with no thank-you note sent).
"""
import os
import datetime as dt
import calendar
import random

COUPLE = 'Amara and Theo'
PARTNER1 = 'Amara'
PARTNER2 = 'Theo'
SUITE = 'fx-20261116-wedding'
TODAY = dt.date.fromisoformat(os.environ['WP_TODAY']) if os.environ.get('WP_TODAY') else dt.date.today()
D = dt.date


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
def _ms(d): return dt.date(d.year, d.month, 1)


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
def R2(x): return round(x + 1e-9, 2)
def rnd5(x): return int(round(x / 5.0)) * 5


def _wedding_day():
    d = TODAY + day(200)
    sh = (5 - d.weekday()) % 7
    return d + day(sh if sh <= 3 else sh - 7)


WEDDING_DAY = _wedding_day()                    # a Saturday, 197 to 203 days ahead
ENGAGED_ON = TODAY - day(275)
SAVE_THE_DATE_ON = TODAY - day(170)
INVITE_A_ON = TODAY - day(40)
INVITE_B_ON = TODAY - day(12)
RSVP_DEADLINE = TODAY + day(21)
HEADCOUNT_DATE = WEDDING_DAY - day(21)
ROOM_CUTOFF = WEDDING_DAY - day(45)
VENUE_CAPACITY = 130
TOTAL_BUDGET = 34000
GUESTS_INVITED = 150
TABLE_SIZE = 10
VENUE_END = '23:30'
OVERTIME_RATE = 250.0

# editable setting defaults ("typical, edit" or "your own numbers")
RESERVE_PCT = 0.05
EXPECTED_YES_RATE = 0.80
TRAVEL_DECLINE_EXTRA = 0.10
TIP_PCT = 0.18
THANKYOU_TARGET_DAYS = 56
THANKYOU_ALERT_DAYS = 14
INVITE_LEAD_WEEKS = 8
DIY_BUFFER_DAYS = 14
DIY_HOUR_VALUE = 12.0
OWNER_SHARE_MAX = 0.5
COST_PER_GUEST_TARGET = 300.0
COST_PER_GUEST_BENCHMARK = 290.0
GUARANTEE_DAYS = 21
HIDDEN_COST_PCT = 0.09
CARD_FEE_PCT = 0.0
PRIORITY_GAP = 2

# ------------------------------------------------------------------ lists (plain international English; keys from pairs() stay <= 21 characters)
ROLES = ['Partner 1', 'Partner 2', 'Parent of partner 1', 'Parent of partner 2', 'Sibling of partner 1', 'Sibling of partner 2', 'Wedding party lead 1', 'Wedding party lead 2',
         'Close friend helper', 'Day-of coordinator', 'Venue contact', 'Caterer contact', 'Photographer contact', 'Band or DJ contact', 'Florist contact', 'Officiant']
TEAMS = ['Couple', 'Family and friends', 'Vendors']
OWNERS = ['Partner 1', 'Partner 2', 'Both partners', 'Parent of partner 1', 'Parent of partner 2', 'Wedding party lead', 'Day-of coordinator', 'Friend or relative']
OWNER_ID = {'Partner 1': 'WP-01', 'Partner 2': 'WP-02', 'Both partners': 'WP-01', 'Parent of partner 1': 'WP-03', 'Parent of partner 2': 'WP-04',
            'Wedding party lead': 'WP-07', 'Day-of coordinator': 'WP-10', 'Friend or relative': 'WP-09'}
SIDES = ['Partner 1', 'Partner 2', 'Shared']
TIERS = ['Family', 'Close friends', 'Friends', 'Colleagues']
LIST_AB = ['A list', 'B list']
AGE_GROUPS = ['Adult', 'Child']
RSVP = ['Yes', 'No', 'Pending']
CONTACT_STATUS = ['Up to date', 'Check in', 'Lost touch']
MEALS = ['Meat', 'Fish', 'Vegetarian', 'Vegan', "Children's meal"]
DIETARY = ['No nuts', 'Gluten free', 'No dairy', 'No shellfish', 'No mushrooms']
REGIONS = ['Local', 'Same country', 'Abroad']
LODGING = ['Room block', 'Own arrangement', 'Local']
CHANNELS = ['Message', 'Phone', 'Email', 'In person']
BUDGET_CATEGORIES = ['Venue', 'Catering and bar', 'Photo and video', 'Music', 'Flowers and decor', 'Attire and alterations', 'Hair and makeup', 'Stationery and postage',
                     'Ceremony and officiant', 'Rentals', 'Cake and favors', 'Transport and lodging', 'Planner and coordinator', 'Other events', 'Tips and fees', 'Reserve']
PAYERS = ['The couple', 'Partner 1 family', 'Partner 2 family']
AGREED_SHARES = {'The couple': 0.60, 'Partner 1 family': 0.25, 'Partner 2 family': 0.15}
FUND_SOURCES = ['Partner 1 savings', 'Partner 2 savings', 'Partner 1 family', 'Partner 2 family', 'Cash gifts']
FUND_STATUS = ['Received', 'Promised', 'Not confirmed']
VENDOR_STATUS = ['Contacted', 'Quote received', 'Shortlisted', 'Booked', 'Declined']
CONTRACT_KINDS = ['Included', 'Not included', 'Cancellation terms', 'Final headcount date', 'Final payment date', 'Arrival and set-up', 'Overtime rate', 'Insurance or permit']
PAY_KINDS = ['Deposit', 'Instalment', 'Final balance']
PAY_STATUS = ['Paid', 'Upcoming', 'Overdue']
METHODS = ['Card', 'Bank transfer', 'Check or cheque', 'Cash']
TASK_AREAS = ['Budget', 'Guests', 'Vendors', 'Venue', 'Attire', 'Ceremony', 'Paper', 'Events', 'Honeymoon', 'Paperwork', 'Day-of', 'Decor and DIY', 'Gifts and thanks']
TASK_STATUS = ['Done', 'In progress', 'Not started']
WHEN = ['12+ months', '9 months', '6 months', '3 months', '1 month', 'Final week', 'Wedding day', 'After']
PARTY_ROLES = ['Lead attendant', 'Attendant', 'Usher', 'Reader', 'Helper']
ATTIRE_STATUS = ['Not started', 'Ordered', 'Arrived', 'Fitted', 'Ready']
TABLE_KINDS = ['Head table', 'Family', 'Friends', 'Colleagues', 'Mixed']
RULE_KINDS = ['Keep together', 'Keep apart']
RULE_REASONS = ['Family', 'Friends', 'Work', 'Needs space']
RUN_BLOCKS = ['Preparation', 'Ceremony', 'Photos', 'Cocktail hour', 'Dinner', 'Dancing', 'Close']
RUN_WHO = ['Couple', 'Wedding party', 'Parents', 'Vendors', 'Officiant', 'All guests']
DIY_STATUS = ['Idea', 'Supplies bought', 'In progress', 'Done']
SUPPLY_BASIS = ['Per guest', 'Per table', 'Fixed']
SUPPLY_STATUS = ['To buy', 'Ordered', 'Bought']
GIFT_KINDS = ['Registry gift', 'Cash gift', 'Handmade or other']
GIFT_EVENTS = ['Engagement party', 'Shower', 'Sent early']
THANK_CHANNELS = ['Handwritten card', 'Message', 'Email']
EVENT_KINDS = ['Engagement party', 'Shower', 'Weekend away', 'Rehearsal dinner', 'Ceremony', 'Reception', 'Farewell brunch']
EVENT_NAMES = ['Engagement party', 'Shower', 'Weekend away, partner 1 friends', 'Weekend away, partner 2 friends', 'Rehearsal dinner', 'Ceremony', 'Reception', 'Farewell brunch']
EVENT_STATUS = ['Done', 'Planned']
HIDDEN_STATUS = ['Expected', 'Paid', 'Not needed']
TIP_BASIS = ['Percent', 'Flat amount', 'None']
HONEY_KINDS = ['Flights', 'Stay', 'Daily spend', 'Activities', 'Local transport', 'Insurance', 'Reserve']
HONEY_OPTIONS = ['Option A: beach week', 'Option B: city minimoon']
PAPER_KINDS = ['Marriage paperwork', 'Name change', 'Other paperwork']
PAPER_STATUS = ['Done', 'In progress', 'Not started']
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

_FIRST = ['Amira', 'Lucas', 'Priya', 'Mateo', 'Yuki', 'Fatima', 'Oliver', 'Chen', 'Ines', 'Kwame', 'Elena', 'Rafael', 'Aisha', 'Noah', 'Mei', 'Omar', 'Sofia', 'Dmitri', 'Chloe', 'Tariq',
          'Hannah', 'Diego', 'Leila', 'Ethan', 'Nia', 'Marco', 'Anika', 'Samuel', 'Zoe', 'Ravi', 'Greta', 'Jamal', 'Camila', 'Pavel', 'Mia', 'Andre', 'Sana', 'Felix', 'Thandi', 'Henrik',
          'Lina', 'Kofi', 'Isla', 'Arjun', 'Bianca', 'Tomas', 'Grace', 'Hugo', 'Nadia', 'Ivan', 'Maya', 'Joel', 'Esther', 'Luca', 'Dina', 'Victor', 'Alma', 'Reza', 'Clara', 'Idris',
          'Wanjiru', 'Axel', 'Mariam', 'Kai', 'Petra', 'Sami', 'Ruth', 'Emil', 'Farah', 'Gabriel', 'Hana', 'Jonas', 'Kira', 'Leon', 'Maren', 'Nico', 'Olga', 'Pia', 'Quentin', 'Rosa',
          'Stefan', 'Tessa', 'Uma', 'Vera', 'Wen', 'Yara', 'Zane', 'Beatriz', 'Cyrus', 'Delia', 'Ewan', 'Freya', 'Hector', 'Imani', 'Jules', 'Katya', 'Lior', 'Mina', 'Nolan', 'Orla']
_LAST = ['Okafor', 'Lindqvist', 'Moreno', 'Nakamura', 'Haddad', 'Petrov', 'Santos', 'Adeyemi', 'Kowalski', 'Chen', 'Rossi', 'Mensah', 'Johansson', 'Patel', 'Silva', 'Novak', 'Hassan',
         'Fischer', 'Tanaka', 'Oyelaran', 'Costa', 'Bergstrom', 'Rahman', 'Dubois', 'Alvarez', 'Park', 'Nowak', 'Okoye', 'Mbeki', 'Hughes', 'Larsen', 'Abdi', 'Romero', 'Kaur', 'Vargas',
         'Weber', 'Ito', 'Mwangi', 'Brennan', 'Khalil', 'Sorensen', 'Ferreira', 'Osei', 'Ivanova', 'Lopez', 'Takahashi', 'Murphy', 'Haile', 'Moreau', 'Gupta', 'Eriksen', 'Delgado',
         'Yilmaz', 'Brandt', 'Nasser', 'Whitfield', 'Ramos', 'Sato', 'Achebe', 'Lund']


# ------------------------------------------------------------------ team
_TEAM = [('WP-01', 'Amara Okafor', 'Partner 1', 'Couple'), ('WP-02', 'Theo Lindqvist', 'Partner 2', 'Couple'),
         ('WP-03', 'Chidi Okafor', 'Parent of partner 1', 'Family and friends'), ('WP-04', 'Maren Lindqvist', 'Parent of partner 2', 'Family and friends'),
         ('WP-05', 'Zainab Okafor', 'Sibling of partner 1', 'Family and friends'), ('WP-06', 'Jonas Lindqvist', 'Sibling of partner 2', 'Family and friends'),
         ('WP-07', 'Priya Nair', 'Wedding party lead 1', 'Family and friends'), ('WP-08', 'Mateo Moreno', 'Wedding party lead 2', 'Family and friends'),
         ('WP-09', 'Yuki Tanaka', 'Close friend helper', 'Family and friends'), ('WP-10', 'Ingrid Solberg', 'Day-of coordinator', 'Vendors'),
         ('WP-11', 'Daniel Okoye', 'Venue contact', 'Vendors'), ('WP-12', 'Isabella Rossi', 'Caterer contact', 'Vendors'),
         ('WP-13', 'Kenji Watanabe', 'Photographer contact', 'Vendors'), ('WP-14', 'Samuel Mensah', 'Band or DJ contact', 'Vendors'),
         ('WP-15', 'Leila Haddad', 'Florist contact', 'Vendors'), ('WP-16', 'Marta Kowalski', 'Officiant', 'Vendors')]
team = [dict(team_id=t[0], name=t[1], role=t[2], team=t[3], phone=fake_phone(i), email=fake_email(t[1], 0)) for i, t in enumerate(_TEAM)]
TEAM_NAME = {t['team_id']: t['name'] for t in team}
_USED = set(t['name'] for t in team)
payers = [dict(payer=p, share=AGREED_SHARES[p], agreed_amount=R2(AGREED_SHARES[p] * TOTAL_BUDGET)) for p in PAYERS]

_CACHE = {}


def _thin(rows, n):
    if not n or n >= len(rows): return rows
    k = min(max(3, n // 5), n)
    if k >= n: return rows[-n:]
    recent = rows[-k:]; rest = rows[:-k]; m = n - k; step = len(rest) / float(m)
    return [rest[int(i * step)] for i in range(m)] + recent


# ------------------------------------------------------------------ households and guests
def _stage_guests(w):
    r = random.Random('wp-guests-20261116')
    sizes = [1] * 40 + [2] * 26 + [3] * 8 + [4] * 6 + [5] * 2
    r.shuffle(sizes)
    sides = ['Partner 1'] * 36 + ['Partner 2'] * 34 + ['Shared'] * 12
    r.shuffle(sides)
    firsts = _FIRST[:]; r.shuffle(firsts)
    lasts = _LAST[:]; r.shuffle(lasts)
    fi = [0]

    def fn():
        v = firsts[fi[0] % len(firsts)]; fi[0] += 1; return v
    hh, gs = [], []
    # list B: households in random order until about 26 guests
    order = list(range(82)); r.shuffle(order)
    bset, bn = set(), 0
    for i in order:
        if bn + sizes[i] <= 27 and bn < 26 and sizes[i] <= 2: bset.add(i); bn += sizes[i]
    for i in range(82):
        size, side = sizes[i], sides[i]
        last = lasts[i % len(lasts)]
        ab = 'B list' if i in bset else 'A list'
        if side == 'Shared': tier = r.choice(['Close friends', 'Friends', 'Friends', 'Colleagues'])
        elif ab == 'B list': tier = r.choice(['Friends', 'Friends', 'Colleagues', 'Close friends'])
        else: tier = r.choices(TIERS, [4, 3, 3, 1])[0]
        wr = r.random()
        region = 'Local' if wr < 0.52 else ('Same country' if wr < 0.86 else 'Abroad')
        names = []
        for k in range(size):
            nm = '%s %s' % (fn(), last)
            while nm in _USED: nm = '%s %s' % (fn(), last)
            _USED.add(nm); names.append(nm)
        if size == 1: hname = names[0]
        elif size == 2: hname = '%s and %s' % (first_name(names[0]), names[1])
        else: hname = 'The %s family' % last
        hid = 'HH-%02d' % (i + 1)
        hh.append(dict(household_id=hid, household=hname, side=side, tier=tier, list_ab=ab, region=region, size=size, contact=names[0], _names=names))
        for k, nm in enumerate(names):
            child = size >= 3 and k >= 2
            gs.append(dict(household_id=hid, household=hname, guest=nm, side=side, tier=tier, list_ab=ab, age_group='Child' if child else 'Adult',
                           plus_one=bool(size == 2 and k == 1 and r.random() < 0.45)))
    # RSVP: pending 18 guests (B list first), no 29 guests (travel first)
    byh = {h['household_id']: h for h in hh}
    sz = {h['household_id']: h['size'] for h in hh}
    state = {}

    def pick(cands, target):
        left = target
        for h in cands:
            if h['household_id'] in state: continue
            if h['size'] <= left:
                state[h['household_id']] = None; left -= h['size']; yield h
            if left == 0: break
        if left: raise AssertionError('cannot reach %d' % target)
    cand = [h for h in hh if h['list_ab'] == 'B list']; r.shuffle(cand)
    rest = [h for h in hh if h['list_ab'] == 'A list']; r.shuffle(rest)
    pend = []
    left = 18
    bsum = 0
    for h in cand + rest:
        if left == 0: break
        if h['household_id'] in state or h['size'] > left: continue
        if h['list_ab'] == 'B list' and bsum + h['size'] > 9: continue
        if h['list_ab'] == 'B list': bsum += h['size']
        state[h['household_id']] = 'Pending'; left -= h['size']; pend.append(h)
    assert left == 0
    decl = [h for h in hh if h['household_id'] not in state]
    decl.sort(key=lambda h: (0 if h['region'] == 'Abroad' else 1 if h['region'] == 'Same country' else 2, r.random()))
    left = 29
    for h in decl:
        if left == 0: break
        if h['size'] > left: continue
        state[h['household_id']] = 'No'; left -= h['size']
    assert left == 0
    for h in hh:
        h['rsvp'] = state.get(h['household_id']) or 'Yes'
    # guests: rsvp, dates, meals
    hdate = {}
    for h in hh:
        inv = INVITE_B_ON if h['list_ab'] == 'B list' else INVITE_A_ON
        h['invite_sent'] = inv
        span = 11 if h['list_ab'] == 'B list' else 38
        hdate[h['household_id']] = inv + day(r.randint(1, span)) if h['rsvp'] != 'Pending' else None
    for g in gs:
        h = byh[g['household_id']]
        g['rsvp'] = h['rsvp']
        g['invite_sent'] = iso(h['invite_sent'])
        d = hdate[g['household_id']]
        g['rsvp_date'] = iso(d + day(r.choice([0, 0, 0, 1]))) if d else ''
        if g['rsvp_date'] and to_date(g['rsvp_date']) > TODAY: g['rsvp_date'] = iso(TODAY)
        g['meal'] = ''; g['dietary'] = ''; g['table'] = ''
        if g['rsvp'] == 'Yes':
            g['meal'] = "Children's meal" if g['age_group'] == 'Child' else r.choices(['Meat', 'Fish', 'Vegetarian', 'Vegan'], [42, 28, 22, 8])[0]
            if g['age_group'] == 'Adult' and r.random() < 0.14: g['dietary'] = r.choice(DIETARY)
    # wedding party: 10 adults, yes, family or close friends, 5 + 5 by side
    party = []
    for side in ('Partner 1', 'Partner 2'):
        pool = [g for g in gs if g['side'] == side and g['rsvp'] == 'Yes' and g['age_group'] == 'Adult' and g['tier'] in ('Family', 'Close friends') and not g['plus_one']]
        r.shuffle(pool)
        party += pool[:5]
    # seating
    cap = 9
    taken = set()
    head = party[:2] + party[2:5] + party[5:8]
    head = [party[0], party[1], party[2], party[3], party[5], party[6], party[7], party[8]]
    for g in head: g['table'] = 'TB-01'; taken.add(g['guest'])
    yes_h = [h for h in hh if h['rsvp'] == 'Yes']
    yes_h.sort(key=lambda h: (h['side'], TIERS.index(h['tier']), h['household_id']))
    cur, fill = 2, 0
    seated_order = []
    for h in yes_h:
        mem = [g for g in gs if g['household_id'] == h['household_id'] and g['guest'] not in taken]
        if not mem: continue
        if fill + len(mem) > cap:
            cur += 1; fill = 0
        if cur > 13: cur = 13
        for g in mem: g['table'] = 'TB-%02d' % cur
        fill += len(mem); seated_order.append(h)
    # late replies stay unseated (about 4 guests)
    late = sorted([h for h in yes_h if all(g['table'] != 'TB-01' for g in gs if g['household_id'] == h['household_id'])], key=lambda h: (hdate[h['household_id']], h['household_id']), reverse=True)
    un = 0
    for h in late:
        if un >= 4: break
        if h['size'] + un > 5: continue
        for g in gs:
            if g['household_id'] == h['household_id']: g['table'] = ''
        un += h['size']
    # households: contact status, chase, lodging, plus-ones, phone
    opens = set(r.sample([h['household_id'] for h in hh if h['size'] <= 2 and h['rsvp'] == 'Yes'], 4))
    for i, h in enumerate(hh):
        h['phone'] = fake_phone(i + 3); h['email'] = fake_email(h['contact'], 0)
        h['save_the_date'] = iso(SAVE_THE_DATE_ON) if h['list_ab'] == 'A list' else ''
        h['invite_sent'] = iso(h['invite_sent'])
        if h['rsvp'] == 'Pending':
            h['contact_status'] = r.choices(['Check in', 'Lost touch', 'Up to date'], [6, 2, 2])[0]
            ch = r.random() < 0.55
            h['last_chase'] = iso(TODAY - day(r.randint(3, 11))) if ch else ''
            h['chase_channel'] = r.choice(['Message', 'Phone', 'Email']) if ch else ''
        else:
            h['contact_status'] = 'Up to date' if r.random() < 0.93 else 'Check in'
            h['last_chase'] = ''; h['chase_channel'] = ''
        h['lodging'] = 'Local' if h['region'] == 'Local' else ('Room block' if r.random() < 0.7 else 'Own arrangement')
        h['arrival'] = iso(WEDDING_DAY - day(1 if h['lodging'] == 'Room block' else 0)) if h['region'] != 'Local' else ''
        h['open_plus_ones'] = 1 if h['household_id'] in opens else 0
    # guest ids oldest household first
    for i, g in enumerate(gs): g['guest_id'] = 'GS-%03d' % (i + 1)
    for p, g in zip(range(10), party): g['_party'] = True
    return dict(hh=hh, gs=gs, party=party)


# ------------------------------------------------------------------ vendors, quotes, contracts, payments
# id, vendor, category, contact team id (or name), status, contract total, lead months, booked days ago, payer, tip basis
_V = [
    ('VD-01', 'Venue', 'Venue', 'WP-11', 'Booked', 5900, 12, 250, 'Partner 1 family'),
    ('VD-02', 'Caterer', 'Catering and bar', 'WP-12', 'Booked', 8740, 10, 200, 'The couple'),
    ('VD-03', 'Photographer', 'Photo and video', 'WP-13', 'Booked', 2650, 10, 230, 'The couple'),
    ('VD-04', 'Videographer', 'Photo and video', 'Noor Hakimi', 'Quote received', 0, 9, 0, 'The couple'),
    ('VD-05', 'Band or DJ', 'Music', 'WP-14', 'Booked', 2150, 9, 190, 'Partner 2 family'),
    ('VD-06', 'Florist', 'Flowers and decor', 'WP-15', 'Booked', 2928, 6, 150, 'The couple'),
    ('VD-07', 'Officiant', 'Ceremony and officiant', 'WP-16', 'Booked', 380, 6, 140, 'The couple'),
    ('VD-08', 'Cake baker', 'Cake and favors', 'Rosa Bellini', 'Booked', 520, 4, 100, 'Partner 1 family'),
    ('VD-09', 'Hair and makeup', 'Hair and makeup', 'Tessa Moreau', 'Booked', 480, 4, 90, 'The couple'),
    ('VD-10', 'Attire shop', 'Attire and alterations', 'Ravi Gupta', 'Booked', 2450, 8, 60, 'The couple'),
    ('VD-11', 'Tailor', 'Attire and alterations', 'Hana Ito', 'Shortlisted', 0, 3, 0, 'The couple'),
    ('VD-12', 'Stationery printer', 'Stationery and postage', 'Felix Weber', 'Booked', 640, 5, 50, 'The couple'),
    ('VD-13', 'Rentals', 'Rentals', 'Omar Nasser', 'Booked', 1040, 5, 120, 'Partner 2 family'),
    ('VD-14', 'Transport', 'Transport and lodging', 'Diego Ramos', 'Quote received', 0, 3, 0, 'The couple'),
    ('VD-15', 'Day-of coordinator', 'Planner and coordinator', 'WP-10', 'Booked', 950, 8, 170, 'Partner 1 family'),
    ('VD-16', 'Hotel room block', 'Transport and lodging', 'Clara Dubois', 'Booked', 300, 9, 130, 'The couple'),
]
# payment plans: (kind, amount or share<=1, due) due = ('t', days from today) or ('w', days before the wedding)
_PLAN = {
    'VD-01': [('Deposit', .50, ('t', -250)), ('Instalment', .20, ('w', 150)), ('Final balance', .30, ('w', 30))],
    'VD-02': [('Deposit', .30, ('t', -200)), ('Instalment', .20, ('w', 90)), ('Final balance', .50, ('w', 14))],
    'VD-03': [('Deposit', .30, ('t', -230)), ('Instalment', .30, ('t', -12)), ('Final balance', .40, ('w', 30))],
    'VD-05': [('Deposit', .25, ('t', -190)), ('Instalment', .25, ('w', 140)), ('Final balance', .50, ('w', 7))],
    'VD-06': [('Deposit', .25, ('t', -150)), ('Instalment', .25, ('t', -4)), ('Final balance', .50, ('w', 10))],
    'VD-07': [('Deposit', .50, ('t', -140)), ('Final balance', .50, ('w', 7))],
    'VD-08': [('Deposit', .40, ('t', -100)), ('Final balance', .60, ('w', 14))],
    'VD-09': [('Deposit', .30, ('t', -90)), ('Final balance', .70, ('w', 7))],
    'VD-10': [('Deposit', 1100, ('t', -60)), ('Final balance', 1350, ('t', 10))],
    'VD-12': [('Deposit', 320, ('t', -50)), ('Final balance', 320, ('w', 45))],
    'VD-13': [('Deposit', 260, ('t', -120)), ('Final balance', 780, ('w', 21))],
    'VD-15': [('Deposit', 380, ('t', -170)), ('Instalment', 285, ('t', -20)), ('Final balance', 285, ('w', 7))],
    'VD-16': [('Deposit', 300, ('t', -130))],
}
_FIRST_DEPOSIT_PAYER = {'VD-02': 'The couple'}


def _due(spec):
    return TODAY + day(spec[1]) if spec[0] == 't' else WEDDING_DAY - day(spec[1])


def _stage_money(w):
    r = random.Random('wp-money-20261116')
    vend, sched, pays = [], [], []
    for i, v in enumerate(_V):
        vid, name, cat, ct, status, total, lead, bago, payer = v
        cname = TEAM_NAME.get(ct, ct)
        vend.append(dict(vendor_id=vid, vendor=name, category=cat, contact=cname, phone=fake_phone(i + 40), email=fake_email(cname, 0), status=status,
                         booked_on=ago(bago) if bago else '', contract_total=float(total), lead_months=lead, payer=payer,
                         last_contact=ago(r.randint(2, 25) if status != 'Booked' else r.randint(5, 60)),
                         follow_up=ahead(r.randint(4, 20)) if status in ('Quote received', 'Shortlisted') else ''))
    k = 0
    for vid, plan in _PLAN.items():
        v = next(x for x in _V if x[0] == vid); total = v[5]
        amts, used = [], 0.0
        for j, (kind, a, due) in enumerate(plan):
            if j == len(plan) - 1: amt = float(total) - used
            else: amt = float(a) if a > 1 else float(rnd5(total * a))
            used += amt; amts.append(amt)
        for (kind, a, due), amt in zip(plan, amts):
            k += 1
            d = _due(due)
            row = dict(pay_id='PY-%03d' % k, vendor_id=vid, vendor=v[1], category=v[2], kind=kind, due_date=iso(d), amount_due=float(amt), payer=v[8],
                       paid_on='', amount_paid=0.0, method='', status='Upcoming', paid_by='')
            if d <= TODAY and not (vid == 'VD-06' and kind == 'Instalment'):
                po = d - day(r.choice([0, 0, 1, 2, 3]))
                if vid == 'VD-03' and kind == 'Instalment': po = d
                if vid == 'VD-15' and kind == 'Instalment': po = d
                row.update(paid_on=iso(po), amount_paid=float(amt), status='Paid', method=r.choice(METHODS[:2] + ['Card']), paid_by=v[8])
            elif d < TODAY:
                row['status'] = 'Overdue'
            sched.append(row)
    # actual payments (one deposit paid in two pieces by two payers; two paid by a different payer than agreed)
    m = 0
    for s in sched:
        if s['status'] != 'Paid': continue
        if s['pay_id'] == next(x for x in sched if x['vendor_id'] == 'VD-02')['pay_id']:
            a1 = rnd5(s['amount_due'] / 2)
            for amt, who, dd in ((a1, 'The couple', 0), (s['amount_due'] - a1, 'Partner 2 family', 3)):
                m += 1; pays.append(dict(payment_id='PM-%03d' % m, pay_id=s['pay_id'], date=iso(to_date(s['paid_on']) + day(dd)), amount=float(amt), paid_by=who, method=s['method']))
            s['paid_on'] = pays[-1]['date']; s['paid_by'] = 'The couple'
            continue
        by = s['payer']
        if s['vendor_id'] in ('VD-08', 'VD-12') and s['kind'] == 'Deposit': by = 'Partner 1 family'
        if s['vendor_id'] == 'VD-07': by = 'Partner 2 family'
        s['paid_by'] = by
        m += 1; pays.append(dict(payment_id='PM-%03d' % m, pay_id=s['pay_id'], date=s['paid_on'], amount=s['amount_paid'], paid_by=by, method=s['method']))
    pays.sort(key=lambda p: (p['date'], p['payment_id']))
    for i, p in enumerate(pays): p['payment_id'] = 'PM-%03d' % (i + 1)
    sched.sort(key=lambda s: (s['due_date'], s['pay_id']))
    for i, s in enumerate(sched): s['_old'] = s['pay_id']
    idmap = {s['_old']: 'PY-%03d' % (i + 1) for i, s in enumerate(sched)}
    for s in sched: s['pay_id'] = idmap[s['_old']]; del s['_old']
    for p in pays: p['pay_id'] = idmap[p['pay_id']]
    return dict(vend=vend, sched=sched, pays=pays)


# category rows: planned, couple / partner 1 family / partner 2 family shares
_CAT = {'Venue': (5900, .4, .4, .2), 'Catering and bar': (8500, .6, .2, .2), 'Photo and video': (3400, .7, .3, 0), 'Music': (2200, .2, 0, .8),
        'Flowers and decor': (2400, .5, .5, 0), 'Attire and alterations': (2800, 1, 0, 0), 'Hair and makeup': (500, 1, 0, 0), 'Stationery and postage': (750, 1, 0, 0),
        'Ceremony and officiant': (400, 1, 0, 0), 'Rentals': (1100, .5, 0, .5), 'Cake and favors': (600, 0, 1, 0), 'Transport and lodging': (650, 1, 0, 0),
        'Planner and coordinator': (1000, 0, 1, 0), 'Other events': (1450, .6, .2, .2), 'Tips and fees': (550, 1, 0, 0), 'Reserve': (1800, 1, 0, 0)}
assert sum(v[0] for v in _CAT.values()) == TOTAL_BUDGET

# events: id, name, kind, days (t or w), status, group, invitees, budget, cost, paid, booked, host
_EV = [('Engagement party', 'Engagement party', ('t', -250), 'Done', 'Family and close friends', 70, 380, 380, 380, True, 'Parent of partner 1'),
       ('Shower', 'Shower', ('t', -24), 'Done', 'Wedding party and family', 28, 60, 60, 60, True, 'Friends of the couple'),
       ('Weekend away, partner 1 friends', 'Weekend away', ('w', 40), 'Planned', 'Partner 1 close friends', 9, 80, 80, 0, False, 'Friends of the couple'),
       ('Weekend away, partner 2 friends', 'Weekend away', ('w', 33), 'Planned', 'Partner 2 close friends', 8, 80, 80, 0, False, 'Friends of the couple'),
       ('Rehearsal dinner', 'Rehearsal dinner', ('w', 1), 'Planned', 'Wedding party and parents', 30, 560, 560, 150, True, 'Both partners'),
       ('Ceremony', 'Ceremony', ('w', 0), 'Planned', 'All guests', 150, 0, 0, 0, True, 'Both partners'),
       ('Reception', 'Reception', ('w', 0), 'Planned', 'All guests', 150, 0, 0, 0, True, 'Both partners'),
       ('Farewell brunch', 'Farewell brunch', ('w', -1), 'Planned', 'Family and out-of-town guests', 40, 290, 290, 0, False, 'Parent of partner 2')]


def event_start(name): return {'Ceremony': '16:00', 'Reception': '17:30', 'Rehearsal dinner': '18:30', 'Farewell brunch': '10:30', 'Engagement party': '18:00', 'Shower': '14:00'}.get(name, '')


def _stage_budget(w):
    M = w['money']; ev = w['events']
    out = []
    for i, c in enumerate(BUDGET_CATEGORIES):
        pl, a, b, cc = _CAT[c]
        vendors = [v for v in M['vend'] if v['category'] == c]
        committed = sum(v['contract_total'] for v in vendors if v['status'] == 'Booked')
        paid = sum(s['amount_paid'] for s in M['sched'] if s['category'] == c)
        if c == 'Other events':
            committed += sum(e['cost'] for e in ev if e['booked'] and e['kind'] != 'Ceremony' and e['kind'] != 'Reception'); paid += sum(e['paid'] for e in ev)
        if c == 'Tips and fees':
            paid += 0.0
        out.append(dict(line_id='BL-%02d' % (i + 1), category=c, planned=float(pl), committed=float(committed), paid=float(paid), share_couple=a, share_p1_family=b, share_p2_family=cc,
                        priority=['Venue', 'Catering and bar', 'Music', 'Photo and video'].count(c) and 5 or 3))
    return out


def _stage_events(w):
    out = []
    for i, e in enumerate(_EV):
        name, kind, due, status, group, inv, bud, cost, paid, booked, host = e
        d = _due(due) if due[0] == 't' else (WEDDING_DAY - day(due[1]))
        out.append(dict(event_id='EV-%02d' % (i + 1), event=name, kind=kind, date=iso(d), start=event_start(name), status=status, group=group, invitees=inv, budget=float(bud),
                        cost=float(cost), paid=float(paid), booked=booked, host=host))
    return out


# quotes: 2 or 3 per slot; the booked one is the chosen quote. (fit, response, reviews) are the couple's own 1..5 ratings
def _stage_quotes(w):
    r = random.Random('wp-quotes-20261116')
    out = []
    for v in w['money']['vend']:
        opts = {'VD-01': 3, 'VD-02': 3, 'VD-03': 3, 'VD-04': 2, 'VD-05': 3, 'VD-06': 3, 'VD-07': 2, 'VD-08': 2, 'VD-09': 2, 'VD-10': 3, 'VD-11': 2, 'VD-12': 3, 'VD-13': 2,
                'VD-14': 2, 'VD-15': 3, 'VD-16': 2}[v['vendor_id']]
        cat = v['category']
        booked = v['status'] == 'Booked'
        if booked: tot = v['contract_total']
        else: tot = {'VD-04': 950.0, 'VD-11': 340.0, 'VD-14': 560.0}[v['vendor_id']]
        chosen_idx = 0 if booked or v['status'] == 'Shortlisted' else -1
        for j in range(opts):
            factor = 1.0 if j == 0 else (r.choice([0.86, 0.92, 1.12, 1.2]) if opts > 2 or j else 1.0)
            if opts == 2 and j == 1: factor = r.choice([0.9, 1.15])
            svc = {'VD-02': 0.18, 'VD-01': 0.0}.get(v['vendor_id'], r.choice([0.0, 0.0, 0.05]))
            tax = r.choice([0.0, 0.05, 0.08])
            deliv = r.choice([0, 0, 60, 120]) if cat in ('Flowers and decor', 'Rentals', 'Cake and favors', 'Music') else 0
            over = r.choice([0, 0, 150, 250]) if cat in ('Venue', 'Photo and video', 'Music', 'Catering and bar') else 0
            trav = r.choice([0, 0, 90, 140]) if cat in ('Photo and video', 'Music', 'Hair and makeup', 'Ceremony and officiant') else 0
            tt = tot * factor
            base = max(50.0, round(tt / (1 + tax) / (1 + svc) - deliv - over - trav, 0))
            status = 'Booked' if (booked and j == 0) else ('Declined' if booked else ('Shortlisted' if j == 0 and v['status'] == 'Shortlisted' else 'Quote received'))
            if v['status'] == 'Quote received' and j == 0: status = 'Quote received'
            qdate = TODAY - day(r.randint(2, 24)) if not booked else (TODAY - day(int(v['booked_on'] and (TODAY - to_date(v['booked_on'])).days) + r.randint(5, 30)))
            out.append(dict(vendor_id=v['vendor_id'], vendor=v['vendor'], category=cat, option='Option %s' % 'ABC'[j], status=status, quote_date=iso(qdate), base_price=base,
                            service_pct=svc, tax_pct=tax, delivery=float(deliv), overtime=float(over), travel=float(trav), response_days=r.randint(1, 9),
                            fit=5 - j if j < 2 else 3, response=r.randint(3, 5), reviews=r.randint(3, 5), chosen=bool(booked and j == 0),
                            included='Base package and set-up' if j == 0 else r.choice(['Base package only', 'Package, fewer hours', 'Package and extras']),
                            excluded=r.choice(['Overtime, travel', 'Delivery, tax', 'Tips', 'Extra hours']),
                            valid_until=iso(TODAY + day(r.randint(10, 60)))))
    out.sort(key=lambda q: (q['quote_date'], q['vendor_id'], q['option']))
    for i, q in enumerate(out): q['quote_id'] = 'QT-%03d' % (i + 1)
    return out


def _stage_contracts(w):
    out = []
    M = w['money']
    SCHED = {}
    for s in M['sched']: SCHED.setdefault(s['vendor_id'], []).append(s)
    inc = {'Venue': 'Ceremony and reception space, tables and chairs', 'Catering and bar': 'Three-course meal, service staff, soft drinks and bar package',
           'Photo and video': 'Eight hours, edited photos in an online gallery', 'Music': 'Four hours of music, sound system, announcements', 'Flowers and decor': 'Bouquets, centrepieces, ceremony flowers',
           'Ceremony and officiant': 'Ceremony script and rehearsal call', 'Cake and favors': 'Three-tier cake, delivery and set-up', 'Hair and makeup': 'Trial plus wedding-day styling for two',
           'Attire and alterations': 'Two outfits, first fitting', 'Stationery and postage': 'Invitation suite, reply cards, envelopes', 'Rentals': 'Linens, glassware, lounge furniture',
           'Planner and coordinator': 'Month-of planning, rehearsal, eight hours on the day', 'Transport and lodging': 'Block of 18 rooms, three nights'}
    exc = {'Venue': 'Overtime, security deposit', 'Catering and bar': 'Corkage, cake cutting', 'Photo and video': 'Printed albums, travel beyond the city', 'Music': 'Extra hours, extra microphones',
           'Flowers and decor': 'Delivery of extra pieces, tips', 'Ceremony and officiant': 'Travel', 'Cake and favors': 'Cake stand hire', 'Hair and makeup': 'Guest styling',
           'Attire and alterations': 'Alterations', 'Stationery and postage': 'Postage, calligraphy', 'Rentals': 'Delivery after the first window', 'Planner and coordinator': 'Extra hours',
           'Transport and lodging': 'Breakfast'}
    n = 0
    for v in M['vend']:
        if v['status'] != 'Booked': continue
        s = SCHED[v['vendor_id']]
        fin = [x for x in s if x['kind'] == 'Final balance'] or s[-1:]
        cat = v['category']
        items = [('Included', inc.get(cat, 'Agreed package'), '', 0.0), ('Not included', exc.get(cat, 'Extras'), '', 0.0),
                 ('Cancellation terms', 'Deposit non-refundable; later payments refundable up to 60 days before' if cat in ('Venue', 'Catering and bar') else 'Deposit non-refundable', '', 0.0),
                 ('Final payment date', 'Final balance due', fin[0]['due_date'], 0.0)]
        if cat in ('Venue', 'Catering and bar', 'Rentals', 'Cake and favors'): items.append(('Final headcount date', 'Final number of guests to the vendor', iso(HEADCOUNT_DATE), 0.0))
        if cat in ('Venue', 'Photo and video', 'Music', 'Planner and coordinator'): items.append(('Overtime rate', 'Per extra hour', '', OVERTIME_RATE if cat == 'Venue' else 150.0))
        if cat in ('Venue', 'Music', 'Flowers and decor', 'Rentals', 'Catering and bar', 'Photo and video'):
            at = {'Venue': '10:00', 'Catering and bar': '12:00', 'Music': '14:00', 'Flowers and decor': '11:30', 'Rentals': '09:30', 'Photo and video': '13:00'}[cat]
            items.append(('Arrival and set-up', 'Arrives at %s, set-up 60 to 90 minutes' % at, iso(WEDDING_DAY), 0.0))
        if cat in ('Venue', 'Music'): items.append(('Insurance or permit', 'Vendor proof of cover, noise limit after 22:00', '', 0.0))
        for kind, det, dd, amt in items:
            n += 1
            out.append(dict(contract_id='CT-%03d' % n, vendor_id=v['vendor_id'], vendor=v['vendor'], kind=kind, detail=det, item_date=dd, amount=float(amt)))
    return out


def _stage_hidden(w):
    items = [('Postage and mailing for invitations', 220.0, 'Expected', 'Stationery and postage'), ('Extra alterations and a second fitting', 250.0, 'Expected', 'Attire and alterations'),
             ('Hair and cake trials', 150.0, 'Paid', 'Hair and makeup'), ('Service charge on the venue invoice', 300.0, 'Expected', 'Venue'),
             ('Delivery and set-up fees', 280.0, 'Expected', 'Rentals'), ('Taxes on vendor invoices', 380.0, 'Expected', 'Catering and bar'),
             ('Event insurance for the day', 180.0, 'Paid', 'Venue'), ('Overtime for the band or the venue', 250.0, 'Expected', 'Music'),
             ('Rush fees if the print date slips', 120.0, 'Expected', 'Stationery and postage'), ('Marriage paperwork fees', 90.0, 'Expected', 'Other events'),
             ('Signs, guest book and emergency kit', 140.0, 'Expected', 'Decor'), ('Gift bags for the room block', 110.0, 'Not needed', 'Transport and lodging')]
    return [dict(hidden_id='HC-%02d' % (i + 1), item=a, expected=b, status=c, category=d if d != 'Decor' else 'Flowers and decor') for i, (a, b, c, d) in enumerate(items)]


def _stage_tips(w):
    V = {v['vendor_id']: v for v in w['money']['vend']}
    rows = [('VD-01', 'Venue staff', False, 'Flat amount', 0.0, 80.0, 'Day-of coordinator'), ('VD-02', 'Caterer', True, 'None', 0.0, 0.0, 'Day-of coordinator'),
            ('VD-03', 'Photographer', False, 'Flat amount', 0.0, 100.0, 'Friend or relative'), ('VD-04', 'Videographer', False, 'Flat amount', 0.0, 50.0, 'Friend or relative'),
            ('VD-05', 'Band or DJ', False, 'Flat amount', 0.0, 100.0, 'Wedding party lead'), ('VD-06', 'Florist', False, 'None', 0.0, 0.0, 'Friend or relative'),
            ('VD-07', 'Officiant', False, 'Flat amount', 0.0, 50.0, 'Parent of partner 1'), ('VD-09', 'Hair and makeup', False, 'Percent', TIP_PCT, 0.0, 'Wedding party lead'),
            ('VD-14', 'Transport', False, 'Percent', 0.15, 0.0, 'Day-of coordinator'), ('VD-15', 'Day-of coordinator', False, 'Flat amount', 0.0, 50.0, 'Both partners'),
            ('VD-08', 'Cake baker', False, 'None', 0.0, 0.0, 'Both partners'), ('VD-10', 'Attire shop', False, 'None', 0.0, 0.0, 'Both partners'),
            ('VD-11', 'Tailor', False, 'None', 0.0, 0.0, 'Both partners'), ('VD-12', 'Stationery printer', False, 'None', 0.0, 0.0, 'Both partners'),
            ('VD-13', 'Rentals', False, 'None', 0.0, 0.0, 'Both partners'), ('VD-16', 'Hotel room block', False, 'None', 0.0, 0.0, 'Both partners')]
    out = []
    for i, (vid, nm, inc, basis, pct, flat, who) in enumerate(rows):
        out.append(dict(tip_id='TP-%02d' % (i + 1), vendor_id=vid, vendor=V[vid]['vendor'], gratuity_included=inc, basis=basis, pct=pct, flat=flat, bill=V[vid]['contract_total'] or 560.0,
                        handed_by=who, envelope_ready=bool(i % 3 == 0)))
    return out


def _stage_funding(w):
    M = w['money']
    paid_to_date = sum(p['amount'] for p in M['pays'])
    rows = []

    def add(src, d, amt, st): rows.append(dict(source=src, date=iso(d), amount=float(amt), status=st))
    # savings: a lump at the start and a monthly transfer on the 1st
    add('Partner 1 savings', ENGAGED_ON + day(20), 1000, 'Received')
    add('Partner 2 savings', ENGAGED_ON + day(22), 800, 'Received')
    d = _ms(add_months(ENGAGED_ON, 1)); rec = 1800.0
    fut = []
    while d < _ms(WEDDING_DAY):
        if d <= TODAY: add('Partner 1 savings', d, 500, 'Received'); add('Partner 2 savings', d, 450, 'Received'); rec += 950
        else: fut.append(d)
        d = add_months(d, 1)
    couple_target = TOTAL_BUDGET * AGREED_SHARES['The couple'] - 850.0
    m = (couple_target - rec) / max(1, len(fut))
    m1 = rnd5(m * 0.52); m2 = rnd5(m * 0.48)
    for d in fut: add('Partner 1 savings', d, m1, 'Promised'); add('Partner 2 savings', d, m2, 'Promised')
    # partner 2 family: first transfer sized so the money set aside is below the next final balance (the story)
    fb = [s for s in M['sched'] if s['kind'] == 'Final balance' and 8 <= (to_date(s['due_date']) - TODAY).days <= 12][0]
    due_fb = to_date(fb['due_date'])
    inc_win = sum(x['amount'] for x in rows if x['status'] == 'Promised' and TODAY < to_date(x['date']) <= due_fb)
    r2 = max(300.0, min(3200.0, rnd5(paid_to_date + 0.5 * fb['amount_due'] - rec - inc_win)))
    add('Partner 2 family', TODAY - day(120), r2, 'Received')
    add('Partner 2 family', WEDDING_DAY - day(90), TOTAL_BUDGET * AGREED_SHARES['Partner 2 family'] - r2, 'Promised')
    add('Partner 1 family', TODAY + day(25), 4000, 'Promised')
    add('Partner 1 family', WEDDING_DAY - day(60), TOTAL_BUDGET * AGREED_SHARES['Partner 1 family'] - 4000, 'Promised')
    add('Cash gifts', WEDDING_DAY, 3000, 'Not confirmed')
    rows.sort(key=lambda x: (x['date'], x['source']))
    for i, x in enumerate(rows): x['fund_id'] = 'FS-%03d' % (i + 1)
    return rows


# ------------------------------------------------------------------ tasks (offset = days before the wedding, or tN / t-N = days from today; crit = critical path)
_TASKS = """
470|Budget|B|1|Agree the total budget and who pays what
467|Budget|B|0|Agree the three things that matter most
464|Guests|B|0|Draft the guest list by household and side
461|Budget|P1|0|Open one shared folder for contracts and quotes
458|Venue|B|0|Choose season, weekday and a date range
452|Venue|B|1|Shortlist ceremony and reception venues
447|Venue|F1|0|Visit the top three venues
443|Venue|B|1|Book the venue and pay the deposit
438|Vendors|B|0|Decide on a planner or a day-of coordinator
433|Events|F1|0|Plan the engagement party
428|Events|B|0|Hold the engagement party
424|Paper|P2|0|Set up a simple wedding page for guests
420|Vendors|P2|1|Shortlist photographers and ask for quotes
415|Vendors|B|1|Shortlist caterers and ask for quotes
410|Vendors|P1|0|Shortlist music: band or DJ
404|Honeymoon|B|0|Agree the honeymoon style and budget range
398|Paperwork|B|0|Ask your officiant or local office about your local marriage paperwork lead time
392|Guests|B|0|Decide the plus-one and children policy
386|Budget|B|0|Start the monthly savings transfers
380|Vendors|B|1|Book the caterer and pay the deposit
374|Vendors|P2|1|Book the photographer and pay the deposit
372|Paper|P1|0|Send save-the-dates to the A list
366|Budget|B|0|Set the hidden-cost reserve
360|Ceremony|P1|0|Choose the ceremony style and shortlist officiants
352|Vendors|P1|1|Book the band or DJ
346|Ceremony|B|1|Book the officiant
340|Vendors|F1|0|Book the day-of coordinator
334|Vendors|P2|0|Choose the florist and agree a design brief
328|Venue|B|0|Hold a hotel room block for out-of-town guests
322|Guests|B|0|Start the wedding party list and ask each person
316|Attire|P1|0|Visit attire shops and set a fitting budget
313|Venue|B|0|Ask the venue for its vendor insurance and noise rules
310|Budget|B|0|Record what each contract includes, cancellation and final payment date
304|Budget|B|0|Enter every deposit and payment date in the payment schedule
298|Guests|B|0|Build the A list and the B list
292|Events|WP|0|Plan the shower with the hosts
286|Honeymoon|B|0|Compare two honeymoon options
280|Vendors|P2|0|Book the cake baker
274|Vendors|P1|0|Book hair and makeup
268|Paper|P2|0|Choose the invitation design and wording
262|Guests|P1|0|Confirm contact details for every household
256|Budget|B|0|Review budget against actual
250|Gifts and thanks|B|0|Open the gift registry list
244|Guests|B|0|Write the guest travel and hotel information
238|Attire|P1|1|Order the main outfit
232|Attire|P2|0|Order the second outfit
226|Vendors|P2|1|Book the florist and pay the deposit
222|Decor and DIY|FR|0|List the DIY projects and supplies
218|Venue|B|0|Walk the venue with the day-of coordinator
t-21|Vendors|B|0|Ask two videographers for quotes
t-15|Attire|WP|0|Choose the wedding party outfits
t-9|Decor and DIY|P2|0|Draft the decor and DIY plan
t-6|Paper|P2|1|Send the invitation files to the printer
t-3|Guests|B|0|Update the A list and B list after the first replies
t-2|Budget|B|0|Check the florist instalment against the schedule
t-1|Vendors|P1|0|Confirm the room block cut-off with the hotel
206|Paper|B|0|Proof the invitation text with one family reader
203|Guests|B|0|Send the second wave to the B list
199|Venue|B|0|Choose the ceremony layout and seating style
196|Attire|P1|0|Book the first fitting
194|Budget|B|0|Move this month's savings to the wedding fund
192|Honeymoon|B|0|Choose between the two honeymoon options
190|Guests|P1|0|Chase households that have not replied
185|Budget|B|1|Pay the final balance to the attire shop
183|Gifts and thanks|P2|1|Write thank-you notes for the shower gifts
180|Vendors|P2|0|Ask the tailor to confirm alteration dates
176|Vendors|B|0|Choose the videographer
172|Paper|P1|0|Reserve the printing date for reply cards
168|Events|WP|0|Plan the two weekends away
164|Vendors|P1|0|Get a transport quote for guests and the wedding party
160|Guests|B|1|Send the reply reminder to households that are silent
156|Budget|B|0|Agree the family payments schedule
152|Venue|B|1|Pay the second venue instalment
150|Vendors|B|0|Ask the caterer for tasting dates
146|Attire|P2|0|Second outfit fitting
142|Paper|P2|1|Order the wedding day programs
140|Music|B|0|Draft the music list and first dance song
138|Ceremony|B|0|Draft the ceremony outline with the officiant
135|Honeymoon|B|1|Book flights for the honeymoon
132|Decor and DIY|FR|0|Buy the first DIY supplies
128|Venue|B|0|Confirm the room block pickup and the cut-off date
125|Guests|B|1|Close the reply-by date and count the replies
122|Guests|B|0|Draft the seating plan
112|Vendors|B|0|Attend the menu tasting
108|Vendors|P2|0|Book hair and makeup trial dates
104|Attire|WP|0|Collect the wedding party outfits
100|Events|F2|0|Book the rehearsal dinner
96|Paper|P1|0|Choose the order of service and print date
92|Budget|B|1|Pay the second caterer instalment
88|Guests|P1|0|Collect meal choices and short dietary notes
84|Decor and DIY|FR|0|Build the centrepieces
80|Day-of|DC|0|Draft the run of show with the coordinator
76|Honeymoon|B|0|Book the honeymoon stay
72|Vendors|B|0|Confirm every vendor arrival time
68|Paperwork|B|0|Check the marriage paperwork steps with your officiant or local office
64|Events|F1|0|Plan the farewell brunch
60|Budget|B|0|Plan tip envelopes and who hands them out
56|Guests|B|1|Post the invitations that went to the printer
54|Guests|P1|0|Ask households who need a ride or help getting to the venue
52|Guests|P1|0|Send the final reminder to households that have not replied
48|Day-of|WP|0|Assign day-of helpers: who carries what, who greets
45|Paper|P2|0|Pay the final stationery balance
42|Budget|B|0|Review budget against actual and the reserve
39|Attire|P1|1|Final fitting for the main outfit
36|Attire|P2|0|Final fitting for the second outfit
33|Guests|B|1|Give the final headcount to the caterer and venue
30|Budget|B|1|Pay the final balances due this month
28|Guests|B|0|Finalise the seating plan
26|Day-of|DC|0|Share the run of show with every vendor
24|Paper|P2|0|Print place cards and table numbers
22|Decor and DIY|FR|0|Finish all DIY projects
20|Day-of|P1|0|Write the speeches
18|Music|B|0|Send the final music list to the band or DJ
16|Venue|B|0|Confirm the rental delivery and pick-up window
14|Day-of|B|1|Pay the caterer final balance
12|Day-of|F2|0|Pack the emergency kit
10|Vendors|DC|0|Reconfirm every vendor in writing
8|Budget|B|0|Prepare labelled tip envelopes
7|Day-of|WP|0|Hold the final wedding party briefing
6|Day-of|P1|0|Pack for the wedding night and the honeymoon
5|Paperwork|B|1|Complete the marriage paperwork steps
4|Day-of|DC|0|Walk through the venue one last time
3|Events|WP|0|Rehearsal at the venue
2|Day-of|F1|0|Deliver welcome bags to the hotel
1|Events|F2|0|Rehearsal dinner
0|Day-of|DC|1|Wedding day: ceremony and reception
0|Day-of|FR|0|Collect cards and gifts and hand them to one named person
0|Day-of|DC|0|Hand out tip envelopes
0|Day-of|DC|0|Load-out and rental returns at the end of the night
-1|Events|F2|0|Farewell brunch
-2|Budget|B|0|Pay any remaining vendor balance
-3|Gifts and thanks|B|0|Log every gift and card by household
-5|After|B|0|Return the rentals and attire
-7|Budget|B|0|Ask vendors about deposit returns
-10|Gifts and thanks|B|0|Start the thank-you notes
-14|Paperwork|B|0|Start the name change steps if you want them
-20|Gifts and thanks|B|0|Finish the thank-you notes
-25|Budget|B|0|Compare final budget against actual
-30|Paperwork|B|0|Update accounts and documents, optional
-45|Gifts and thanks|B|0|Send photo and thank-you note to every vendor
""".strip().split('\n')
_OWN = {'P1': 'Partner 1', 'P2': 'Partner 2', 'B': 'Both partners', 'F1': 'Parent of partner 1', 'F2': 'Parent of partner 2', 'WP': 'Wedding party lead', 'DC': 'Day-of coordinator', 'FR': 'Friend or relative'}


def when_of(off):
    if off > 300: return '12+ months'
    if off > 210: return '9 months'
    if off > 120: return '6 months'
    if off > 45: return '3 months'
    if off > 7: return '1 month'
    if off > 0: return 'Final week'
    if off == 0: return 'Wedding day'
    return 'After'


def months_out(d):
    """whole months between a date and the wedding day (rounded down)"""
    d = to_date(d)
    return int((WEDDING_DAY - d).days // 30.4)


def _stage_tasks(w):
    r = random.Random('wp-tasks-20261116')
    rows = []
    for ln in _TASKS:
        off, area, own, crit, title = ln.split('|')
        if off.startswith('t'): due = TODAY + day(int(off[1:])); special = True
        else: due = WEDDING_DAY - day(int(off)); special = False
        rows.append(dict(title=title, area=area, owner=_OWN[own], owner_id=OWNER_ID[_OWN[own]], due_date=due, critical=crit == '1', special=special))
    rows.sort(key=lambda x: (x['due_date'], not x['critical']))
    out = []
    for i, x in enumerate(rows):
        due = x['due_date']
        if x['special']: status = 'Not started' if 'printer' in x['title'] or i % 2 else 'In progress'
        elif due < TODAY: status = 'Done'
        elif (due - TODAY).days <= 30 and i % 4 == 0: status = 'In progress'
        else: status = 'Not started'
        done = ''
        if status == 'Done': done = iso(max(ENGAGED_ON, min(TODAY, due - day(r.choice([0, 0, 1, 2, 4, 6])))))
        out.append(dict(task_id='TK-%03d' % (i + 1), title=x['title'], area=x['area'], when=when_of((WEDDING_DAY - due).days), due_date=iso(due), owner=x['owner'], owner_id=x['owner_id'],
                        status=status, done_date=done, critical=x['critical']))
    assert len(out) == 140, len(out)
    return out


# ------------------------------------------------------------------ wedding party, tables, rules
_PARTY_TASKS = {'Lead attendant': ['Plan the shower and the weekend away', 'Hold the rings and keep the day on time'], 'Attendant': ['Help with DIY and the welcome bags', 'Greet guests at the door'],
                'Usher': ['Seat guests and hand out programs', 'Carry gifts to the car at the end'], 'Reader': ['Read at the ceremony', 'Help with the order of service']}


def _stage_party(w):
    r = random.Random('wp-party-20261116')
    party = w['guests']['party']
    roles = ['Lead attendant', 'Attendant', 'Attendant', 'Attendant', 'Reader', 'Lead attendant', 'Attendant', 'Attendant', 'Usher', 'Usher']
    out = []
    for i, g in enumerate(party):
        role = roles[i]
        k = i % 3
        status = ['Ordered', 'Ordered', 'Arrived', 'Fitted', 'Not started'][i % 5]
        if i == 5: status = 'Arrived'
        out.append(dict(party_id='WPY-%02d' % (i + 1), person=g['guest'], guest_id=g['guest_id'], side=g['side'], role=role, task=_PARTY_TASKS[role][k % 2],
                        attire_status=status, outfit_cost=float(r.choice([140, 165, 180, 210, 95, 120])), paid_by=r.choice(['Own', 'Own', 'Couple']),
                        fitting_date=iso(WEDDING_DAY - day(r.choice([46, 40, 34, 28]))), alteration_weeks=r.choice([3, 4, 4, 6]),
                        phone=fake_phone(i + 60)))
    for j, tid in enumerate(('WP-03', 'WP-04', 'WP-05', 'WP-06')):
        t = next(x for x in team if x['team_id'] == tid)
        out.append(dict(party_id='WPY-%02d' % (11 + j), person=t['name'], guest_id='', side='Partner 1' if j % 2 == 0 else 'Partner 2', role='Helper',
                        task=['Welcome guests at the hotel', 'Look after the guest book and gifts table', 'Carry flowers between venues', 'Hand out programs'][j],
                        attire_status=['Ordered', 'Fitted', 'Arrived', 'Not started'][j], outfit_cost=float([120, 150, 95, 110][j]), paid_by='Own', fitting_date=iso(WEDDING_DAY - day(34 + 3 * j)),
                        alteration_weeks=3, phone=t['phone']))
    return out


def _stage_tables(w):
    gs = w['guests']['gs']
    out = []
    for i in range(13):
        tid = 'TB-%02d' % (i + 1)
        occ = [g for g in gs if g['table'] == tid]
        if i == 0: kind = 'Head table'
        else:
            tc = {}
            for g in occ: tc[g['tier']] = tc.get(g['tier'], 0) + 1
            top = max(tc, key=tc.get) if tc else 'Friends'
            kind = {'Family': 'Family', 'Close friends': 'Friends', 'Friends': 'Friends', 'Colleagues': 'Colleagues'}[top] if tc and tc[top] >= 0.6 * len(occ) else 'Mixed'
        out.append(dict(table_id=tid, table_name='Head table' if i == 0 else 'Table %d' % (i + 1), capacity=TABLE_SIZE, kind=kind, reserved=2 if i == 0 else 0))
    return out


def _stage_rules(w):
    r = random.Random('wp-rules-20261116')
    gs = w['guests']['gs']
    yes = [g for g in gs if g['rsvp'] == 'Yes' and g['age_group'] == 'Adult']
    out, used = [], set()
    kinds = [('Keep together', 'Friends')] * 5 + [('Keep together', 'Family')] * 3 + [('Keep apart', 'Needs space')] * 4 + [('Keep apart', 'Work')] * 2
    k = 0
    for kind, reason in kinds:
        for _ in range(100):
            a, b = r.sample(yes, 2)
            if a['household_id'] == b['household_id'] or a['guest_id'] in used or b['guest_id'] in used: continue
            if kind == 'Keep together' and a['side'] != b['side'] and reason == 'Family': continue
            used.add(a['guest_id']); used.add(b['guest_id'])
            k += 1; out.append(dict(rule_id='SR-%02d' % k, kind=kind, guest_a=a['guest_id'], guest_b=b['guest_id'], reason=reason)); break
    return out


# ------------------------------------------------------------------ run of show (wedding day)
_RUN = """
07:30|60|Preparation|Hair and makeup starts for partner 1 and the wedding party|Wedding party|Hotel|VD-09
08:30|60|Preparation|Breakfast and getting ready, flowers arrive at the hotel|Couple|Hotel|VD-06
09:30|60|Preparation|Hair and makeup for partner 2 and the parents|Parents|Hotel|VD-09
10:00|90|Preparation|Rentals delivered and set up at the venue|Vendors|Venue|VD-13
11:30|45|Preparation|Caterer arrives and sets up the kitchen|Vendors|Venue|VD-02
12:00|30|Preparation|Florist sets up ceremony and reception flowers|Vendors|Venue|VD-06
13:00|45|Preparation|Band or DJ load-in and sound check|Vendors|Venue|VD-05
13:30|45|Preparation|Photographer arrives, detail shots of rings and outfits|Vendors|Hotel|VD-03
14:15|45|Preparation|Day-of coordinator walks the venue and checks the seating chart|Vendors|Venue|VD-15
14:30|30|Preparation|Wedding party and parents travel to the venue|Wedding party|Transport|VD-14
15:00|30|Photos|First look and couple portraits|Couple|Venue|VD-03
15:30|20|Photos|Wedding party photos|Wedding party|Venue|VD-03
15:45|15|Preparation|Ushers and greeters in place, programs handed out|Wedding party|Venue|
16:00|10|Ceremony|Guests seated, music plays|All guests|Venue|VD-05
16:10|35|Ceremony|Ceremony with the officiant, readings and vows|Officiant|Venue|VD-07
16:45|15|Ceremony|Recessional and signing|Couple|Venue|VD-07
17:00|30|Photos|Family photos|Parents|Venue|VD-03
17:15|60|Cocktail hour|Cocktail hour with music, couple takes a short break|All guests|Venue|VD-05
17:30|15|Dinner|Guests move to the reception room and find seats|All guests|Venue|VD-02
18:15|15|Dinner|Grand entrance and welcome speech|All guests|Venue|VD-05
18:30|75|Dinner|Dinner served, tables released in order|All guests|Venue|VD-02
19:45|30|Dinner|Speeches and toasts|All guests|Venue|VD-05
20:15|15|Dinner|Cake cutting|All guests|Venue|VD-08
20:30|15|Dancing|First dance and parent dances|All guests|Venue|VD-05
20:45|135|Dancing|Open dancing, late snack at 22:00|All guests|Venue|VD-05
23:00|15|Close|Last dance and send-off|All guests|Venue|VD-03
23:15|15|Close|Guests leave, shuttle runs to the hotel|All guests|Transport|VD-14
23:15|30|Close|Tips handed out, gifts and cards given to one named person|Vendors|Venue|VD-15
23:30|15|Close|Load-out begins, rentals counted|Vendors|Venue|VD-13
23:45|15|Close|Venue handed back, keys returned|Vendors|Venue|VD-01
""".strip().split('\n')


def _stage_run(w):
    out = []
    for i, ln in enumerate(_RUN):
        st, mins, blk, what, who, place, vid = ln.split('|')
        out.append(dict(step_id='RS-%02d' % (i + 1), date=iso(WEDDING_DAY), start=st, minutes=int(mins), buffer_min=5 if blk in ('Photos', 'Ceremony', 'Preparation') else 0, block=blk,
                        what=what, who=who, place=place, vendor_id=vid))
    return out


# ------------------------------------------------------------------ DIY, gifts, honeymoon, paperwork, rooms
_DIY = [('Table centrepieces: jars and greenery', 'Per table', 14, 190.0, 'In progress'), ('Welcome sign', 'Fixed', 4, 60.0, 'Supplies bought'),
        ('Seating chart display and place cards', 'Per guest', 9, 120.0, 'Idea'), ('Favors: small jars of jam', 'Per guest', 12, 210.0, 'Idea'),
        ('Table numbers', 'Per table', 3, 45.0, 'Supplies bought'), ('Ceremony programs', 'Per guest', 5, 85.0, 'Idea'),
        ('Guest book and photo wall', 'Fixed', 6, 110.0, 'Idea'), ('Welcome bags for the room block', 'Per guest', 8, 150.0, 'Idea'),
        ('Aisle markers', 'Fixed', 3, 70.0, 'Done'), ('Bouquet and buttonhole greenery', 'Fixed', 4, 130.0, 'Idea'),
        ('Cocktail hour signs', 'Fixed', 2, 40.0, 'Idea'), ('Lanterns for the aisle and entrance', 'Fixed', 3, 95.0, 'Idea'), ('Photo props box', 'Fixed', 3, 55.0, 'Idea'),
        ('Thank-you cards, printed early', 'Per guest', 6, 90.0, 'Idea')]
_SUP = [(0, 'Glass jars', 'Per table', 3, 1.8, 'Bought'), (0, 'Greenery bundles', 'Per table', 2, 4.5, 'Ordered'), (0, 'Tea lights', 'Per table', 6, 0.4, 'To buy'), (0, 'Ribbon', 'Per table', 0.5, 3.0, 'To buy'),
        (1, 'Wooden board', 'Fixed', 1, 24.0, 'Bought'), (1, 'Paint and brushes', 'Fixed', 1, 12.0, 'Bought'), (1, 'Vinyl letters', 'Fixed', 1, 9.0, 'Bought'),
        (2, 'Card stock for place cards', 'Per guest', 1, 0.25, 'To buy'), (2, 'Frame for the chart', 'Fixed', 1, 35.0, 'To buy'), (2, 'Pens', 'Fixed', 2, 6.0, 'To buy'),
        (3, 'Small jars', 'Per guest', 1, 1.9, 'To buy'), (3, 'Labels', 'Per guest', 1, 0.12, 'To buy'), (3, 'Fruit and sugar for jam', 'Per guest', 1, 1.1, 'To buy'),
        (4, 'Wooden stands', 'Per table', 1, 3.2, 'Bought'), (4, 'Paint', 'Fixed', 1, 8.0, 'Bought'),
        (5, 'Paper for programs', 'Per guest', 0.5, 0.35, 'To buy'), (5, 'Ribbon for programs', 'Fixed', 1, 12.0, 'To buy'),
        (6, 'Guest book', 'Fixed', 1, 22.0, 'To buy'), (6, 'Photo frame and clips', 'Fixed', 1, 28.0, 'To buy'),
        (7, 'Paper bags', 'Per guest', 0.4, 0.5, 'To buy'), (7, 'Snacks and water', 'Per guest', 0.4, 2.2, 'To buy'),
        (8, 'Short posts', 'Fixed', 8, 4.5, 'Bought'), (8, 'Ribbon and bows', 'Fixed', 1, 10.0, 'Bought'),
        (9, 'Greenery for the bouquet', 'Fixed', 1, 18.0, 'To buy'), (9, 'Wire and tape', 'Fixed', 1, 6.0, 'To buy'),
        (10, 'Chalkboards and chalk', 'Fixed', 2, 14.0, 'To buy'), (11, 'Lanterns', 'Fixed', 8, 6.5, 'To buy'), (11, 'Candles for lanterns', 'Fixed', 8, 1.2, 'To buy'),
        (12, 'Props: hats and frames', 'Fixed', 1, 32.0, 'Ordered'), (13, 'Cards and envelopes', 'Per guest', 0.8, 0.6, 'To buy'), (13, 'Stamps', 'Per guest', 0.8, 0.5, 'To buy')]


def _stage_diy(w):
    r = random.Random('wp-diy-20261116')
    projects = []
    for i, (name, basis, hrs, buy, status) in enumerate(_DIY):
        projects.append(dict(diy_id='DY-%02d' % (i + 1), project=name, basis=basis, hours=float(hrs), buy_cost=buy, status=status,
                             start_by=iso(WEDDING_DAY - day(DIY_BUFFER_DAYS + hrs * 3 + 14 + i * 4)), owner=['Friend or relative', 'Partner 2', 'Partner 1', 'Parent of partner 1', 'Wedding party lead'][i % 5]))
    sup = []
    for i, (p, item, basis, qty, cost, status) in enumerate(_SUP):
        sup.append(dict(supply_id='SU-%03d' % (i + 1), diy_id=projects[p]['diy_id'], project=projects[p]['project'], item=item, basis=basis, qty_per=float(qty), unit_cost=float(cost), status=status,
                        bought_on=ago(r.randint(3, 80)) if status == 'Bought' else ''))
    return dict(projects=projects, supplies=sup)


_GIFT_ITEMS = ['Kitchen knife set', 'Towel set', 'Picture frame', 'Cookware set', 'Bedding set', 'Wine glasses', 'Coffee maker', 'Serving dishes', 'Cutting boards', 'Lamp',
               'Photo album', 'Plant and planter', 'Blanket', 'Candle set', 'Cake stand', 'Board game set', 'Handmade quilt', 'Vase', 'Spice rack', 'Tablecloth set']


def _stage_gifts(w):
    r = random.Random('wp-gifts-20261116')
    hh = [h for h in w['guests']['hh'] if h['rsvp'] == 'Yes']
    r.shuffle(hh)
    rows = []
    shower = TODAY - day(24)
    plan = [('Engagement party', TODAY - day(250), 8, 0), ('Shower', shower, 24, 0)]
    pos = 0
    for ev, d0, cnt, _ in plan:
        for k in range(cnt):
            h = hh[pos % len(hh)]; pos += 1
            d = d0 + day(r.choice([0, 0, 0, 1])) if ev == 'Engagement party' else shower - day(r.choice([0, 0, 0, 1, 2, 3, 5]))
            kind = r.choices(GIFT_KINDS, [6, 3, 1])[0]
            rows.append(dict(date=iso(d), household_id=h['household_id'], household=h['household'], event=ev, kind=kind,
                             description='Cash gift' if kind == 'Cash gift' else ('Handmade ' + r.choice(['card and jam', 'quilt', 'photo book']) if kind == 'Handmade or other' else r.choice(_GIFT_ITEMS)),
                             amount=float(r.choice([50, 75, 100, 150, 200, 250])) if kind == 'Cash gift' else 0.0))
    for d in (190, 150, 120, 95, 70, 41, 9, 6, 3):
        h = hh[pos % len(hh)]; pos += 1
        kind = r.choices(GIFT_KINDS, [6, 3, 1])[0]
        rows.append(dict(date=ago(d), household_id=h['household_id'], household=h['household'], event='Sent early', kind=kind,
                         description='Cash gift' if kind == 'Cash gift' else r.choice(_GIFT_ITEMS), amount=float(r.choice([50, 100, 150, 200])) if kind == 'Cash gift' else 0.0))
    rows.sort(key=lambda x: (x['date'], x['household_id']))
    thanks = []
    unthanked = 0
    for i, g in enumerate(rows):
        g['gift_id'] = 'GF-%03d' % (i + 1)
        age = (TODAY - to_date(g['date'])).days
        if age <= 14: thanked = False
        elif g['event'] == 'Shower': thanked = (unthanked >= 9) or (i % 2 == 0 and unthanked >= 0 and r.random() < 0.7)
        else: thanked = True
        if g['event'] == 'Shower' and age > 14 and not thanked: unthanked += 1
        g['_thanked'] = thanked
    # exactly 9 shower gifts older than 14 days without a thank-you: fix up
    sh = [g for g in rows if g['event'] == 'Shower' and (TODAY - to_date(g['date'])).days > 14]
    for j, g in enumerate(sh): g['_thanked'] = (j % 8 in (0, 1, 3, 5, 6)) if j < 16 else False
    miss = [g for g in sh if not g['_thanked']]
    while len(miss) > 9:
        g = miss.pop(); g['_thanked'] = True
    while len(miss) < 9:
        c = [g for g in sh if g['_thanked'] and (TODAY - to_date(g['date'])).days <= 29][-1]; c['_thanked'] = False; miss.append(c)
    k = 0
    for g in rows:
        if not g['_thanked']: continue
        k += 1
        wr = to_date(g['date']) + day(r.randint(2, 9)); wr = min(wr, TODAY - day(2)) if g['event'] == 'Shower' else min(wr, TODAY)
        sent = wr + day(r.choice([0, 1, 2, 4]))
        thanks.append(dict(gift_id=g['gift_id'], household=g['household'], written_on=iso(wr), sent_on=iso(sent) if sent <= TODAY else '', channel=r.choices(THANK_CHANNELS, [6, 2, 2])[0]))
    thanks.sort(key=lambda t: (t['written_on'], t['gift_id']))
    for i, t in enumerate(thanks): t['note_id'] = 'TY-%03d' % (i + 1)
    for g in rows: del g['_thanked']
    return dict(gifts=rows, thanks=thanks)


def _stage_honeymoon(w):
    A = [('Flights', 'Two return flights', 1240.0, 80), ('Stay', 'Ten nights at a beach hotel', 1500.0, 70), ('Daily spend', 'Food and local costs, 10 days', 900.0, 0),
         ('Activities', 'Boat day and two tours', 400.0, 20), ('Local transport', 'Transfers and a hired car', 250.0, 20), ('Insurance', 'Travel insurance for two', 120.0, 60), ('Reserve', 'Reserve of ten percent', 440.0, 0)]
    B = [('Flights', 'Two return train or flight tickets', 380.0, 60), ('Stay', 'Four nights in a city hotel', 680.0, 50), ('Daily spend', 'Food and local costs, 5 days', 550.0, 0),
         ('Activities', 'Museum and show tickets', 150.0, 15), ('Local transport', 'Local passes', 80.0, 15), ('Insurance', 'Travel insurance for two', 40.0, 40), ('Reserve', 'Reserve of ten percent', 190.0, 0)]
    rows = []
    for opt, L in zip(HONEY_OPTIONS, (A, B)):
        for kind, desc, amt, lead in L:
            rows.append(dict(option=opt, kind=kind, description=desc, amount=amt, days=10 if opt == HONEY_OPTIONS[0] else 5,
                             due_date=iso(WEDDING_DAY - day(lead)) if lead else '', paid_on=''))
    for i, x in enumerate(rows): x['hm_id'] = 'HM-%02d' % (i + 1)
    fund = []
    d = _ms(add_months(ENGAGED_ON, 1))
    while d < _ms(WEDDING_DAY):
        fund.append(dict(date=iso(d), month=iso(d), source='Savings', amount=200.0 if d.month % 3 else 260.0, status='Received' if d <= TODAY else 'Promised'))
        d = add_months(d, 1)
    fund.append(dict(date=iso(WEDDING_DAY), month=iso(_ms(WEDDING_DAY)), source='Cash gifts', amount=1500.0, status='Not confirmed'))
    for i, x in enumerate(fund): x['hf_id'] = 'HF-%03d' % (i + 1)
    return dict(rows=rows, fund=fund)


def _stage_paper(w):
    items = [('Ask your officiant or local office about your local marriage paperwork lead time', 'Marriage paperwork', False, 398, 'Done', 'Both partners'),
             ('Book the appointment for your local marriage paperwork', 'Marriage paperwork', False, 75, 'Not started', 'Both partners'),
             ('Gather the documents your local office asks for', 'Marriage paperwork', False, 70, 'Not started', 'Both partners'),
             ('Complete the marriage paperwork steps', 'Marriage paperwork', False, 5, 'Not started', 'Both partners'),
             ('Ask the officiant for the signing page and who keeps it', 'Marriage paperwork', False, 30, 'Not started', 'Partner 2'),
             ('Order copies of the marriage record', 'Other paperwork', True, -10, 'Not started', 'Partner 1'),
             ('Decide whether either partner will change a name', 'Name change', True, 120, 'Done', 'Both partners'),
             ('Update identity documents (optional)', 'Name change', True, -21, 'Not started', 'Partner 1'),
             ('Update bank and card accounts (optional)', 'Name change', True, -28, 'Not started', 'Partner 1'),
             ('Update work records and payroll (optional)', 'Name change', True, -35, 'Not started', 'Partner 1'),
             ('Update insurance and tax records (optional)', 'Other paperwork', True, -45, 'Not started', 'Both partners'),
             ('Update home and utility records (optional)', 'Other paperwork', True, -50, 'Not started', 'Partner 2'),
             ('Combine or review insurance and benefits (optional)', 'Other paperwork', True, -60, 'Not started', 'Both partners'),
             ('Review wills and beneficiaries (optional)', 'Other paperwork', True, -75, 'Not started', 'Both partners')]
    return [dict(item_id='PW-%02d' % (i + 1), item=a, kind=b, optional=c, due_date=iso(WEDDING_DAY - day(d)), status=e, owner=f) for i, (a, b, c, d, e, f) in enumerate(items)]


def _stage_rooms(w):
    out = []
    for i, (k, held, pick) in enumerate(((1, 10, 6), (0, 18, 11), (-1, 8, 2))):
        d = WEDDING_DAY - day(k)
        out.append(dict(block_id='RB-%02d' % (i + 1), night=iso(d), rooms_held=held, picked_up=pick, rate=139.0, cutoff_date=iso(ROOM_CUTOFF),
                        attrition_date=iso(WEDDING_DAY - day(60)), attrition_pct=0.80))
    return out


def _stage_extra(w):
    ev = {e['event']: e for e in w['events']}
    L = [('Engagement party', [('Food and snacks', 220, 1), ('Drinks', 90, 1), ('Decor and flowers', 40, 1), ('Invitations and cards', 30, 1)]),
         ('Shower', [('Favors', 40, 1), ('Games and prizes', 10, 1), ('Cards', 10, 1)]),
         ('Weekend away, partner 1 friends', [('Gift for the group', 50, 0), ('Shared transport', 20, 0), ('Snacks', 10, 0)]),
         ('Weekend away, partner 2 friends', [('Gift for the group', 50, 0), ('Shared transport', 20, 0), ('Snacks', 10, 0)]),
         ('Rehearsal dinner', [('Restaurant deposit', 150, 1), ('Food and drinks balance', 330, 0), ('Room hire', 40, 0), ('Thank-you gifts for helpers', 40, 0)]),
         ('Farewell brunch', [('Food', 200, 0), ('Coffee and drinks', 60, 0), ('Decor and signs', 30, 0)])]
    lines, k = [], 0
    for name, items in L:
        e = ev[name]
        assert sum(a for _, a, _ in items) == e['cost'], (name, e['cost'])
        for item, amt, paid in items:
            k += 1
            lines.append(dict(line_id='EL-%02d' % k, event_id=e['event_id'], event=name, item=item, amount=float(amt), paid=float(amt if paid else 0)))
    A = [('Outfit for partner 1', 'Partner 1', 'Outfit', 'VD-10', 1450, 'Ordered', 236), ('Outfit for partner 2', 'Partner 2', 'Outfit', 'VD-10', 1000, 'Ordered', 232),
         ('Shoes for partner 1', 'Partner 1', 'Shoes', '', 120, 'To buy', 150), ('Shoes for partner 2', 'Partner 2', 'Shoes', '', 95, 'Bought', 150),
         ('Veil or hair piece', 'Partner 1', 'Accessories', '', 80, 'To buy', 120), ('Cufflinks and tie', 'Partner 2', 'Accessories', '', 40, 'To buy', 110),
         ('Alterations for partner 1', 'Partner 1', 'Alterations', 'VD-11', 180, 'To buy', 70), ('Alterations for partner 2', 'Partner 2', 'Alterations', 'VD-11', 140, 'To buy', 70),
         ('Rings', 'Both', 'Rings', '', 640, 'Bought', 90), ('Garment bags and hangers', 'Both', 'Other', '', 35, 'To buy', 30),
         ('Emergency sewing and stain kit', 'Both', 'Other', '', 25, 'To buy', 14), ('Underlayers and socks', 'Both', 'Other', '', 60, 'To buy', 60),
         ('Wedding party outfits, see the roster', 'Wedding party', 'Outfit', '', 1900, 'Ordered', 104), ('Honeymoon outfits', 'Both', 'Other', '', 150, 'To buy', 10)]
    attire = [dict(attire_id='AT-%02d' % (i + 1), item=a, for_person=b, kind=c, vendor_id=d, cost=float(e), status=f, order_by=iso(WEDDING_DAY - day(g)), in_budget=c != 'Rings')
              for i, (a, b, c, d, e, f, g) in enumerate(A)]
    R = [('Linens and glassware', 'VD-13', 'Rental return', 1, 0, 'Not due'), ('Lounge furniture', 'VD-13', 'Rental return', 1, 0, 'Not due'),
         ('Rental security deposit', 'VD-13', 'Deposit refund', 10, 150, 'Not due'), ('Venue security deposit', 'VD-01', 'Deposit refund', 14, 500, 'Not due'),
         ('Cake stand and cake box', 'VD-08', 'Rental return', 2, 0, 'Not due'), ('Florist vases and stands', 'VD-06', 'Rental return', 3, 0, 'Not due'),
         ('Attire shop accessories', 'VD-10', 'Rental return', 2, 0, 'Not due'), ('Room block unused rooms credit', 'VD-16', 'Deposit refund', 21, 100, 'Not due'),
         ('Caterer headcount adjustment', 'VD-02', 'Deposit refund', 14, 0, 'Not due'), ('DIY lanterns and signs, put away or sell', '', 'Supplies', 7, 0, 'Not due'),
         ('Borrowed items returned to family', '', 'Supplies', 5, 0, 'Not due'), ('Photo gallery and files received', 'VD-03', 'Other', 28, 0, 'Not due')]
    rets = [dict(return_id='RT-%02d' % (i + 1), item=a, vendor_id=b, kind=c, due_date=iso(WEDDING_DAY + day(d)), refund=float(e), status=f) for i, (a, b, c, d, e, f) in enumerate(R)]
    return dict(lines=lines, attire=attire, returns=rets)


def _world():
    w = {}
    w['guests'] = _stage_guests(w)
    w['money'] = _stage_money(w)
    w['events'] = _stage_events(w)
    w['budget'] = _stage_budget(w)
    w['quotes'] = _stage_quotes(w)
    w['contracts'] = _stage_contracts(w)
    w['hidden'] = _stage_hidden(w)
    w['tips'] = _stage_tips(w)
    w['funding'] = _stage_funding(w)
    w['tasks'] = _stage_tasks(w)
    w['party'] = _stage_party(w)
    w['tables'] = _stage_tables(w)
    w['rules'] = _stage_rules(w)
    w['run'] = _stage_run(w)
    w['diy'] = _stage_diy(w)
    w['gifts'] = _stage_gifts(w)
    w['honey'] = _stage_honeymoon(w)
    w['paper'] = _stage_paper(w)
    w['rooms'] = _stage_rooms(w)
    w['extra'] = _stage_extra(w)
    return w


def _W():
    if 'w' not in _CACHE: _CACHE['w'] = _world()
    return _CACHE['w']


def _pub(rows): return [{k: v for k, v in x.items() if not k.startswith('_')} for x in rows]


def _out(rows, n): return _thin([dict(x) for x in _pub(rows)], n)


_HH_COLS = ['household_id', 'household', 'contact', 'phone', 'email', 'side', 'tier', 'list_ab', 'region', 'size', 'rsvp', 'save_the_date', 'invite_sent', 'contact_status', 'last_chase',
            'chase_channel', 'lodging', 'arrival', 'open_plus_ones']
_GS_COLS = ['guest_id', 'guest', 'household_id', 'household', 'side', 'tier', 'list_ab', 'age_group', 'plus_one', 'invite_sent', 'rsvp', 'rsvp_date', 'meal', 'dietary', 'table']


def household_rows(n=None): return _thin([{k: x[k] for k in _HH_COLS} for x in _W()['guests']['hh']], n)
def guest_rows(n=None): return _thin([{k: x[k] for k in _GS_COLS} for x in _W()['guests']['gs']], n)
def vendor_rows(n=None): return _out(_W()['money']['vend'], n)
def quote_rows(n=None): return _out(sorted(_W()['quotes'], key=lambda q: q['quote_id']), n)
def contract_rows(n=None): return _out(_W()['contracts'], n)
def payment_schedule_rows(n=None): return _out(_W()['money']['sched'], n)
def payment_rows(n=None): return _out(_W()['money']['pays'], n)
def budget_rows(n=None): return _out(_W()['budget'], n)
def hidden_cost_rows(n=None): return _out(_W()['hidden'], n)
def tip_rows(n=None): return _out(_W()['tips'], n)
def funding_rows(n=None): return _out(_W()['funding'], n)
def task_rows(n=None): return _out(_W()['tasks'], n)
def party_rows(n=None): return _out(_W()['party'], n)
def table_rows(n=None): return _out(_W()['tables'], n)
def seat_rule_rows(n=None): return _out(_W()['rules'], n)
def run_rows(n=None): return _out(_W()['run'], n)
def event_rows(n=None): return _out(_W()['events'], n)
def roomblock_rows(n=None): return _out(_W()['rooms'], n)
def diy_rows(n=None): return _out(_W()['diy']['projects'], n)
def supply_rows(n=None): return _out(_W()['diy']['supplies'], n)
def gift_rows(n=None): return _out(_W()['gifts']['gifts'], n)
def thankyou_rows(n=None): return _out(_W()['gifts']['thanks'], n)
def honeymoon_rows(n=None): return _out(_W()['honey']['rows'], n)
def honeymoon_fund_rows(n=None): return _out(_W()['honey']['fund'], n)
def paperwork_rows(n=None): return _out(_W()['paper'], n)
def event_line_rows(n=None): return _out(_W()['extra']['lines'], n)
def attire_rows(n=None): return _out(_W()['extra']['attire'], n)
def return_rows(n=None): return _out(_W()['extra']['returns'], n)


_GENS = ['household_rows', 'guest_rows', 'vendor_rows', 'quote_rows', 'contract_rows', 'payment_schedule_rows', 'payment_rows', 'budget_rows', 'hidden_cost_rows', 'tip_rows',
         'funding_rows', 'task_rows', 'party_rows', 'table_rows', 'seat_rule_rows', 'run_rows', 'event_rows', 'roomblock_rows', 'diy_rows', 'supply_rows', 'gift_rows', 'thankyou_rows',
         'honeymoon_rows', 'honeymoon_fund_rows', 'paperwork_rows', 'event_line_rows', 'attire_rows', 'return_rows']


def expected_headcount(rate=EXPECTED_YES_RATE):
    """yes + pending x rate (a quick check of the demo story; the workbooks compute their own)"""
    g = guest_rows()
    return sum(1 for x in g if x['rsvp'] == 'Yes') + rate * sum(1 for x in g if x['rsvp'] == 'Pending')


def cash_on_hand(on=None):
    """money received minus money paid up to a date (the money set aside)"""
    on = on or TODAY
    rec = sum(f['amount'] for f in funding_rows() if f['status'] == 'Received' and to_date(f['date']) <= on)
    paid = sum(p['amount'] for p in payment_rows() if to_date(p['date']) <= on)
    return rec - paid


# ------------------------------------------------------------------ story
def story():
    """Ids of the 6 story rows, with the values that make each one true (all asserted)."""
    sched = payment_schedule_rows()
    fb = [s for s in sched if s['kind'] == 'Final balance' and s['status'] != 'Paid' and 8 <= (to_date(s['due_date']) - TODAY).days <= 12]
    assert len(fb) == 1, fb
    due = to_date(fb[0]['due_date'])
    incoming = sum(f['amount'] for f in funding_rows() if f['status'] != 'Received' and TODAY < to_date(f['date']) <= due and f['source'] != 'Cash gifts')
    assert cash_on_hand() + incoming < fb[0]['amount_due'], (cash_on_hand(), incoming, fb[0])
    gs = guest_rows()
    pend = [g['guest_id'] for g in gs if g['rsvp'] == 'Pending']
    assert 16 <= len(pend) <= 20 and (RSVP_DEADLINE - TODAY).days == 21, len(pend)
    bl = budget_rows()
    over = [b for b in bl if b['planned'] and b['committed'] / b['planned'] - 1 >= 0.15]
    assert len(over) == 1 and over[0]['category'] == 'Flowers and decor' and 0.20 <= over[0]['committed'] / over[0]['planned'] - 1 <= 0.24, over
    assert len(gs) == GUESTS_INVITED > VENUE_CAPACITY and expected_headcount() < VENUE_CAPACITY - 8
    vn = [v for v in vendor_rows() if v['vendor'] == 'Venue'][0]
    tk = [t for t in task_rows() if t['critical'] and t['status'] != 'Done' and to_date(t['due_date']) < TODAY]
    assert len(tk) == 1 and 'printer' in tk[0]['title'], tk
    thanked = set(t['gift_id'] for t in thankyou_rows())
    un = [g['gift_id'] for g in gift_rows() if g['event'] == 'Shower' and g['gift_id'] not in thanked and (TODAY - to_date(g['date'])).days > 14]
    assert len(un) >= 5 and not [g for g in gift_rows() if g['event'] != 'Shower' and g['gift_id'] not in thanked and (TODAY - to_date(g['date'])).days > 14]
    return dict(payment=fb[0]['pay_id'], vendor=fb[0]['vendor_id'], rsvp=pend, budget=over[0]['line_id'], capacity=vn['vendor_id'], task=tk[0]['task_id'], gifts=un)


if __name__ == '__main__':
    for nm in _GENS: print(nm, len(globals()[nm]()))
    print(story())
