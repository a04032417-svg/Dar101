"""Short-term rental host suite (Dar Templates) - shared demo story for ALL eight parts.

Pure data + tiny helpers + deterministic row generators, independent of call order (one cached world is built on first use). The demo business is "Harbor and Pine Stays"
(fictional): a host (owner Noor Castellanos, SR-01) running 12 furnished units in 4 cities (apartments, lofts, studios, houses and cabins): 7 units belong to the host (rented or
financed, with rent or mortgage) and 5 are managed for 3 other owners (management fee 18-20% of revenue after platform fees). A co-host (Kai Andersson, SR-02) handles guest messages,
check-ins and four host units for a fee; 4 cleaners (SR-03..06) and 2 handymen (SR-07, SR-08). Channels: 'Platform A', 'Platform B', 'Platform C' (booking platforms, each keeps a
fee of the gross) and 'Direct' (small card processing fee). About 1,200 bookings over ~2 years with nights, guests, ADR, fees, local occupancy tax, payouts and cancellations; turnovers
and cleaner pay, supplies purchases and stock, maintenance tickets, damage claims, reviews, guest messages, expenses, owner statements, co-host fees, tax returns, cash.
One generic currency; every date is relative to the build day (TODAY).

Money model: a booking has a nightly rate (season x weekend lift x yearly growth), room revenue = nights x rate, cleaning fee, gross = room revenue + cleaning fee. The channel keeps
fee_pct of the earned amount; local occupancy tax (tax_pct of the city x room revenue) is collected from the guest: tax_by 'Platform' means the platform remits it, 'Host' means the
host remits it and it is paid out with the booking. net_payout = earned - fee (+ tax if the host remits). A cancelled booking keeps kept_amount (a share of room revenue, may be 0) and
refunds the rest. Payout dates: platforms pay 1-2 days after check-in, direct bookings are paid 7 days before check-in. Reporting month = month of check-out for revenue and statements;
occupancy per month allocates nights to the month they are slept in. Owner statements: revenue - platform fees - cleaning - supplies - maintenance - utilities - management fee.

Story rows (ids from story(), never hard-coded): unit_losing (a unit that loses money after fees and cleaning), missing_payout (a Platform B payout 3+ weeks late), pending_claim
(a damage claim waiting), low_review_unit (a unit whose recent reviews hurt it), overbooked_cleaner (a cleaner with 5+ turnovers and 10+ hours on one busy day), pricing_opportunity
(a unit sold out in a local event week at the base rate).

Exports
  constants: COMPANY SUITE OWNER COHOST; dates TODAY iso ago ahead month_start add_months to_date months14() week_start; helpers pairs first_name fake_phone fake_email rng
  lists: ROLES TEAMS YESNO UNIT_TYPES CITIES CHANNELS BOOKING_STATUS PAYOUT_STATUS TURN_STATUS TICKET_KINDS PRIORITIES TICKET_STATUS DAMAGE_STATUS REVIEW_TOPICS MSG_KINDS
         SUPPLY_CATEGORIES EXPENSE_CATEGORIES STATEMENT_STATUS TAX_STATUS SEASONS TICKET_SOURCES
  people: staff (8), contacts (4 outside), team (12), units (12), owners (4), channels (4), cities (4), supply_items (24)
  generators (fresh lists of dicts, oldest first; n= thins a long list): booking_rows payout_rows turnover_rows cleaner_pay_rows supply_stock_rows supply_purchase_rows maintenance_rows
    damage_rows review_rows guest_message_rows guest_rows expense_rows owner_statement_rows cohost_fee_rows tax_rows unit_month_rows price_rows season_rows cash_rows; story()
Lesson: money cells are plain amounts; optional dates (paid_on, done_on, cancelled_on, reply_on) are '' when blank: wrap lookups with IF(x=0,"",x). Links hold NAMES (unit, guest,
cleaner) or ids (booking BK-0001, unit UN-01).
"""
import datetime as dt
import calendar
import random
import hashlib

COMPANY = 'Harbor and Pine Stays'
SUITE = 'fx-20261113-short-term-rental'
OWNER = 'Noor Castellanos'
COHOST = 'Kai Andersson'
TODAY = dt.date.today()
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
def rng(tag=''): return random.Random('sr-core-20261113-' + str(tag))
def R2(x): return round(x + 1e-9, 2)
def _ms(d): return dt.date(d.year, d.month, 1)


ROLES = ['Owner host', 'Co-host', 'Cleaner', 'Handyperson', 'Accountant', 'Locksmith', 'Linen supplier', 'Tax adviser']
TEAMS = ['Management', 'Guest care', 'Cleaning', 'Maintenance', 'Outside']
YESNO = ['Yes', 'No']
UNIT_TYPES = ['Apartment', 'Loft', 'Studio', 'House', 'Cabin']
CITIES = ['Lisbon', 'Porto', 'Cascais', 'Sintra']
CHANNELS = ['Platform A', 'Platform B', 'Platform C', 'Direct']
BOOKING_STATUS = ['Upcoming', 'In stay', 'Completed', 'Cancelled']
PAYOUT_STATUS = ['Scheduled', 'Paid', 'Short paid', 'Missing']
TURN_STATUS = ['Scheduled', 'Done', 'Redo needed']
TICKET_KINDS = ['Plumbing', 'Electrical', 'Appliance', 'Heating and cooling', 'Furniture', 'Locks and keys', 'Garden and exterior', 'Pest control', 'Wi-Fi and TV']
PRIORITIES = ['High', 'Normal', 'Low']
TICKET_STATUS = ['Open', 'In progress', 'Waiting parts', 'Done']
TICKET_SOURCES = ['Guest report', 'Cleaner report', 'Inspection', 'Damage claim']
DAMAGE_STATUS = ['Pending', 'Approved', 'Partially paid', 'Paid', 'Rejected']
REVIEW_TOPICS = ['Cleanliness', 'Check-in', 'Noise', 'Comfort', 'Location', 'Value', 'Host communication', 'Amenities']
MSG_KINDS = ['Booking question', 'Check-in instructions', 'Question during stay', 'Complaint', 'Special request', 'Checkout reminder', 'Review request']
SUPPLY_CATEGORIES = ['Linen and towels', 'Toiletries', 'Kitchen', 'Cleaning products', 'Consumables', 'Safety']
EXPENSE_CATEGORIES = ['Rent or mortgage', 'Utilities', 'Internet and TV', 'Insurance', 'Software and subscriptions', 'Marketing and photos', 'Accounting and legal', 'Local taxes and permits']
STATEMENT_STATUS = ['Draft', 'Sent', 'Paid']
TAX_STATUS = ['Filed and paid', 'Due', 'Upcoming']
SEASONS = ['Low', 'Shoulder', 'High', 'Peak']
HISTORY_DAYS = 735

# ------------------------------------------------------------------ people
_dom = 'harborpine.example.com'
_staff = [('SR-01', 'Noor Castellanos', 'Brazil', '+351 91 555 0301', 'Owner host', 'Management', 40, 0, 'Pricing, owners and finance'),
          ('SR-02', 'Kai Andersson', 'Sweden', '+351 92 555 0302', 'Co-host', 'Guest care', 32, 0, 'Guest messages and check-ins'),
          ('SR-03', 'Lucia Fernandes', 'Portugal', '+351 93 555 0303', 'Cleaner', 'Cleaning', 30, 17, 'Lisbon units'),
          ('SR-04', 'Amara Diallo', 'Senegal', '+351 96 555 0304', 'Cleaner', 'Cleaning', 28, 17, 'Porto units'),
          ('SR-05', 'Yuki Sato', 'Japan', '+351 91 555 0305', 'Cleaner', 'Cleaning', 28, 18, 'Cascais and Sintra units'),
          ('SR-06', 'Dmitri Ivanov', 'Ukraine', '+351 92 555 0306', 'Cleaner', 'Cleaning', 20, 17, 'Backup and deep cleans'),
          ('SR-07', 'Ravi Menon', 'India', '+351 93 555 0307', 'Handyperson', 'Maintenance', 24, 28, 'Plumbing, electrical and appliances'),
          ('SR-08', 'Tariq Haddad', 'Jordan', '+351 96 555 0308', 'Handyperson', 'Maintenance', 18, 26, 'Furniture, locks and garden')]
staff = []
for a, b, c, d, e, f, g, rt, sp in _staff:
    staff.append(dict(staff_id=a, name=b, country=c, phone=d, email=b.lower().replace(' ', '.') + '@' + _dom, role=e, team=f, hours_week=g, hourly_rate=rt, speciality=sp,
                      start=ago(1500 - 150 * len(staff))))
_ctc = [('SR-09', 'Mei Tanaka', 'Japan', '+351 91 555 0309', 'Accountant', 'Bookkeeping and yearly accounts'), ('SR-10', 'Rafael Costa', 'Portugal', '+351 92 555 0310', 'Locksmith', 'Locks, keys and smart lock repairs'),
        ('SR-11', 'Sofia Haddad', 'Canada', '+351 93 555 0311', 'Linen supplier', 'Linen, towels and hotel-grade bedding'), ('SR-12', 'Arjun Khan', 'Australia', '+351 96 555 0312', 'Tax adviser', 'Local occupancy tax and income tax')]
contacts = [dict(staff_id=a, name=b, country=c, phone=d, email=b.lower().replace(' ', '.') + '@' + _dom, role=e, team='Outside', hours_week=0, hourly_rate=0, speciality=sp, start=ago(1200 - 100 * i))
            for i, (a, b, c, d, e, sp) in enumerate(_ctc)]
team = staff + contacts
staff_by_name = {s['name']: s for s in team}
CLEANERS = [s['name'] for s in staff if s['role'] == 'Cleaner']
HANDY = [s['name'] for s in staff if s['role'] == 'Handyperson']

owners = [dict(owner_id='OW-01', name='Noor Castellanos', kind='Own portfolio', mgmt_pct=0.0, phone='+351 91 555 0301'),
          dict(owner_id='OW-02', name='Ingrid Solberg', kind='Managed for owner', mgmt_pct=0.20, phone='+47 91 555 0402'),
          dict(owner_id='OW-03', name='Pablo Reyes', kind='Managed for owner', mgmt_pct=0.18, phone='+34 61 555 0403'),
          dict(owner_id='OW-04', name='Wen Zhao', kind='Managed for owner', mgmt_pct=0.20, phone='+65 81 555 0404')]
cities = [dict(city='Lisbon', tax_pct=0.06), dict(city='Porto', tax_pct=0.05), dict(city='Cascais', tax_pct=0.05), dict(city='Sintra', tax_pct=0.04)]
TAXP = {c['city']: c['tax_pct'] for c in cities}
channels = [dict(channel='Platform A', fee_pct=0.15, payout_days=1, tax_by='Platform', share=0.44), dict(channel='Platform B', fee_pct=0.14, payout_days=1, tax_by='Platform', share=0.24),
            dict(channel='Platform C', fee_pct=0.12, payout_days=2, tax_by='Host', share=0.10), dict(channel='Direct', fee_pct=0.03, payout_days=-7, tax_by='Host', share=0.22)]
CH = {c['channel']: c for c in channels}
# unit_id, name, type, city, bedrooms, max_guests, owner, base_rate, cleaning_fee, rent, utilities, internet, start_days_ago, occupancy, cohost
_units = [('UN-01', 'Alfama Terrace Flat', 'Apartment', 'Lisbon', 2, 4, 'Noor Castellanos', 135, 55, 1150, 140, 38, 735, .36, 'Yes'),
          ('UN-02', 'Chiado Loft', 'Loft', 'Lisbon', 1, 2, 'Noor Castellanos', 118, 45, 980, 105, 38, 730, .34, 'Yes'),
          ('UN-03', 'Bairro Alto Studio', 'Studio', 'Lisbon', 1, 2, 'Noor Castellanos', 82, 35, 700, 80, 35, 700, .32, 'Yes'),
          ('UN-04', 'Ribeira River Suite', 'Apartment', 'Porto', 2, 4, 'Noor Castellanos', 126, 55, 1050, 125, 38, 690, .33, 'Yes'),
          ('UN-05', 'Foz Garden House', 'House', 'Porto', 3, 6, 'Noor Castellanos', 215, 85, 1700, 210, 45, 600, .27, 'No'),
          ('UN-06', 'Cascais Bay Apartment', 'Apartment', 'Cascais', 2, 5, 'Noor Castellanos', 160, 65, 1250, 150, 40, 520, .31, 'No'),
          ('UN-07', 'Estoril Seaside Studio', 'Studio', 'Cascais', 1, 2, 'Noor Castellanos', 66, 25, 1180, 135, 40, 450, .22, 'No'),
          ('UN-08', 'Sintra Forest Cabin', 'Cabin', 'Sintra', 2, 4, 'Ingrid Solberg', 150, 60, 0, 120, 38, 640, .28, 'No'),
          ('UN-09', 'Sintra Hilltop Cottage', 'House', 'Sintra', 3, 6, 'Ingrid Solberg', 190, 75, 0, 160, 40, 560, .29, 'No'),
          ('UN-10', 'Porto Vineyard Loft', 'Loft', 'Porto', 1, 3, 'Pablo Reyes', 105, 42, 0, 95, 38, 400, .30, 'Yes'),
          ('UN-11', 'Cascais Marina Penthouse', 'Apartment', 'Cascais', 3, 6, 'Pablo Reyes', 280, 95, 0, 190, 45, 330, .27, 'No'),
          ('UN-12', 'Lisbon Rooftop Duplex', 'Apartment', 'Lisbon', 3, 6, 'Wen Zhao', 230, 90, 0, 175, 45, 250, .29, 'No')]
_OMP = {o['name']: o['mgmt_pct'] for o in owners}
units = []
for u in _units:
    units.append(dict(unit_id=u[0], name=u[1], unit_type=u[2], city=u[3], bedrooms=u[4], max_guests=u[5], owner=u[6], base_rate=u[7], cleaning_fee=u[8], mgmt_pct=_OMP[u[6]],
                      rent=u[9], utilities=u[10], internet=u[11], since=ago(u[12]), cohost=u[14], _occ=u[13] * 1.14, _start=u[12]))
UNIT = {u['unit_id']: u for u in units}
STORY_LOSING, STORY_LOW_REVIEW, STORY_EVENT_UNIT = 'UN-07', 'UN-09', 'UN-01'
_SEAS = [0, .76, .79, .88, 1.0, 1.08, 1.18, 1.36, 1.42, 1.15, 1.0, .84, 1.0]        # price factor by month number
_OCC = [0, .80, .84, .92, 1.0, 1.08, 1.15, 1.30, 1.34, 1.12, .98, .82, 1.02]       # occupancy factor by month number


def season_of(m):
    f = _SEAS[m]
    return 'Low' if f < .9 else 'Shoulder' if f < 1.05 else 'High' if f < 1.25 else 'Peak'


_G = [('Portugal', ['Ana', 'Rui', 'Marta', 'Tiago', 'Ines', 'Diogo', 'Sara', 'Nuno'], ['Silva', 'Pereira', 'Costa', 'Ribeiro', 'Almeida', 'Moreira', 'Gomes', 'Teixeira']),
      ('Germany', ['Jonas', 'Lena', 'Felix', 'Mira', 'Leon', 'Hanna', 'Emil', 'Nele'], ['Becker', 'Hoffmann', 'Schulz', 'Keller', 'Vogel', 'Brandt', 'Lorenz', 'Fuchs']),
      ('United Kingdom', ['Oliver', 'Ella', 'Harvey', 'Isla', 'Noah', 'Freya', 'Alfie', 'Poppy'], ['Turner', 'Hughes', 'Walsh', 'Barker', 'Ellis', 'Pearce', 'Dawson', 'Fisher']),
      ('United States', ['Jordan', 'Taylor', 'Riley', 'Morgan', 'Casey', 'Avery', 'Quinn', 'Rowan'], ['Bennett', 'Carter', 'Brooks', 'Hayes', 'Foster', 'Reed', 'Gray', 'Webb']),
      ('France', ['Camille', 'Louis', 'Chloe', 'Hugo', 'Manon', 'Theo', 'Lea', 'Jules'], ['Moreau', 'Laurent', 'Girard', 'Roux', 'Fournier', 'Mercier', 'Blanc', 'Dupont']),
      ('Spain', ['Lucia', 'Pablo', 'Carmen', 'Hector', 'Elena', 'Alvaro', 'Noa', 'Iker'], ['Navarro', 'Ortega', 'Molina', 'Castro', 'Herrera', 'Vidal', 'Prieto', 'Cano']),
      ('Netherlands', ['Daan', 'Sanne', 'Bram', 'Fenna', 'Lars', 'Anouk', 'Joris', 'Femke'], ['de Vries', 'Visser', 'Smit', 'Bos', 'Mulder', 'Dekker', 'Peters', 'Hendriks']),
      ('Brazil', ['Gabriel', 'Beatriz', 'Caio', 'Larissa', 'Thiago', 'Julia', 'Enzo', 'Livia'], ['Souza', 'Lima', 'Araujo', 'Barbosa', 'Rocha', 'Cardoso', 'Nunes', 'Freitas']),
      ('Poland', ['Kasia', 'Marek', 'Zofia', 'Piotr', 'Ola', 'Jakub', 'Wiktoria', 'Antoni'], ['Nowak', 'Kowal', 'Wisniewski', 'Zielinski', 'Lewandowski', 'Mazur', 'Kaczmarek', 'Pawlak']),
      ('India', ['Aarav', 'Diya', 'Kabir', 'Meera', 'Rohan', 'Anika', 'Vihaan', 'Tara'], ['Sharma', 'Iyer', 'Nair', 'Kapoor', 'Mehta', 'Joshi', 'Bose', 'Rao']),
      ('Australia', ['Mia', 'Lachlan', 'Zara', 'Hamish', 'Ruby', 'Declan', 'Sienna', 'Archer'], ['Murray', 'Fraser', 'Hart', 'Doyle', 'Sutton', 'Blake', 'Lowe', 'Pratt']),
      ('Canada', ['Liam', 'Ava', 'Mason', 'Chloe', 'Ethan', 'Nora', 'Owen', 'Maya'], ['Tremblay', 'Gagnon', 'Roy', 'Cote', 'Leblanc', 'Bouchard', 'Morin', 'Pelletier'])]
_GW = [.14, .12, .12, .12, .08, .08, .08, .07, .05, .05, .05, .04]

_CACHE = {}
def _raw(key, fn):
    if key not in _CACHE: _CACHE[key] = fn()
    return _CACHE[key]
def _cached(key, fn): return [dict(r) for r in _raw(key, fn)]
def _thin(rows, n):
    if not n or n >= len(rows): return rows
    step = len(rows) / float(n)
    return [rows[int(i * step)] for i in range(n)]
def _pub(rows): return [{k: v for k, v in x.items() if not k.startswith('_')} for x in rows]
def _wchoice(r, vals, ws):
    x, acc = r.random() * sum(ws), 0
    for v, w in zip(vals, ws):
        acc += w
        if x <= acc: return v
    return vals[-1]


# ------------------------------------------------------------------ world: bookings
def _event():
    s = week_start(TODAY + day(24)) + day(7) if week_start(TODAY + day(24)) < TODAY + day(24) else week_start(TODAY + day(24))
    return s, s + day(7)


def _nightly(u, d, r):
    f = _SEAS[d.month] * (1.15 if d.weekday() in (4, 5) else 1.0) * (1 + .05 * ((d - (TODAY - day(HISTORY_DAYS))).days / 365.0)) * r.uniform(.94, 1.06)
    return u['base_rate'] * f


def _stays(u):
    r = rng('stays-' + u['unit_id']); ev0, ev1 = _event(); lisbon = u['city'] == 'Lisbon' and u['unit_id'] != 'UN-07'
    d = TODAY - day(u['_start']); end = TODAY + day(160); out = []
    while d < end:
        forced = lisbon and ev0 - day(3) <= d < ev1
        if lisbon and ev0 - day(3) <= d < ev0: d = ev0; forced = True
        p = min(.93, u['_occ'] * _OCC[d.month] * (1.6 if d.weekday() in (4, 5) else 1.0))
        if not forced and r.random() > p: d += day(1); continue
        n = _wchoice(r, [1, 2, 3, 4, 5, 6, 7, 9, 12, 14], [3, 17, 21, 21, 13, 9, 9, 3, 2, 2]) if not forced else r.choice([3, 4, 5])
        if lisbon and d < ev0 < d + day(n): n = (ev0 - d).days
        if forced: n = min(n, (ev1 - d).days)
        ci, co = d, d + day(n)
        lead = max(1, min(150, int(r.expovariate(1 / 30.0)) + 1))
        if forced: lead = (ci - TODAY).days + r.randint(2, 25) if ci > TODAY else lead
        booked = ci - day(lead)
        if booked > TODAY: d = co; continue
        rates = [_nightly(u, ci + day(i), r) for i in range(n)]
        if forced and ci >= ev0: rates = [u['base_rate'] * _SEAS[ev0.month] * r.uniform(.98, 1.03) for _ in range(n)]    # event nights left at the normal price
        out.append(dict(unit_id=u['unit_id'], check_in=ci, check_out=co, nights=n, booked_on=booked, lead_days=lead, rate=sum(rates) / n, _forced=forced))
        d = co + day(r.choice([0, 0, 1])) if not forced else co
    return out


def _world_bookings():
    r = rng('bk'); allb = []
    for u in units: allb += _stays(u)
    allb.sort(key=lambda b: (b['check_in'], b['unit_id']))
    used, pool = [], []
    wl = {c['channel']: c['share'] for c in channels}
    cancelled_flag = 0
    for i, b in enumerate(allb, 1):
        u = UNIT[b['unit_id']]; b['booking_id'] = 'BK-%04d' % i; b['unit'] = u['name']; b['city'] = u['city']
        repeat = used and r.random() < .11
        if repeat:
            g = r.choice(used); b['guest'], b['guest_country'] = g
            b['channel'] = 'Direct' if r.random() < .45 else _wchoice(r, CHANNELS, [wl[c] for c in CHANNELS])
        else:
            k = _wchoice(r, list(range(len(_G))), _GW); country, fs, ls = _G[k]
            b['guest'] = '%s %s' % (r.choice(fs), r.choice(ls)); b['guest_country'] = country
            dshare = .12 + .16 * ((b['booked_on'] - (TODAY - day(HISTORY_DAYS))).days / float(HISTORY_DAYS))     # direct grows over time
            ws = [wl['Platform A'] * (1 - dshare), wl['Platform B'] * (1 - dshare) * .9, wl['Platform C'] * (1 - dshare) * .9, dshare * .8 + .02]
            b['channel'] = _wchoice(r, CHANNELS, ws); used.append((b['guest'], b['guest_country']))
        b['guests'] = max(1, min(u['max_guests'], int(r.choice([1, 2, 2, 2, 3, 4, 4, 5, 6]) * (u['max_guests'] / 4.0) ** .5 + .5)))
        c = CH[b['channel']]; rate = R2(b['rate']); b['nightly_rate'] = rate; del b['rate']
        room = R2(rate * b['nights']); b['room_revenue'] = room; b['cleaning_fee'] = u['cleaning_fee']; b['gross'] = R2(room + u['cleaning_fee'])
        b['tax_pct'] = TAXP[u['city']]; b['tax_collected'] = R2(room * b['tax_pct']); b['tax_by'] = c['tax_by']; b['fee_pct'] = c['fee_pct']
        b['cancelled_on'] = ''; b['refund_amount'] = 0.0; b['kept_amount'] = 0.0
        canc = r.random() < .075 and not b['_forced'] and b['lead_days'] > 4 and b['check_in'] > TODAY - day(HISTORY_DAYS) + day(5)
        if canc:
            co_ = b['booked_on'] + day(r.randint(1, max(1, b['lead_days'] - 2)))
            if co_ <= TODAY:
                b['cancelled_on'] = iso(co_); late = (b['check_in'] - co_).days < 14
                b['kept_amount'] = R2(room * (r.choice([.3, .5, 1.0]) if late and b['channel'] == 'Direct' else (r.choice([0, 0, .3, .5]) if late else 0)))
                if b['channel'] != 'Direct' and late and r.random() < .3: b['kept_amount'] = R2(room * .5)
                b['refund_amount'] = R2(b['gross'] - b['kept_amount'])
        if b['cancelled_on']:
            b['status'] = 'Cancelled'; earned = b['kept_amount']; b['tax_collected'] = 0.0
        else:
            b['status'] = 'Completed' if b['check_out'] <= TODAY else 'In stay' if b['check_in'] <= TODAY else 'Upcoming'; earned = b['gross']
        b['earned'] = R2(earned); b['platform_fee'] = R2(earned * c['fee_pct'])
        b['net_payout'] = R2(earned - b['platform_fee'] + (b['tax_collected'] if c['tax_by'] == 'Host' else 0))
        if b['cancelled_on']: exp = to_date(b['cancelled_on']) + day(3)
        else: exp = b['check_in'] + day(c['payout_days']); exp = max(exp, b['booked_on']) if c['payout_days'] < 0 else exp
        b['payout_date'] = iso(exp); b['check_in'] = iso(b['check_in']); b['check_out'] = iso(b['check_out']); b['booked_on'] = iso(b['booked_on'])
        b['channel_share'] = 0
        del b['channel_share']
    # story: a Platform B payout that never arrived (check-in 3+ weeks ago, 4-6 nights)
    cand = [b for b in allb if b['channel'] == 'Platform B' and b['status'] == 'Completed' and 22 <= (TODAY - to_date(b['check_in'])).days <= 40 and b['nights'] >= 4 and b['net_payout'] > 500]
    if not cand: cand = [b for b in allb if b['channel'] == 'Platform B' and b['status'] == 'Completed' and 22 <= (TODAY - to_date(b['check_in'])).days <= 60 and b['net_payout'] > 300]
    story_b = cand[0]['booking_id']
    # payout status per booking
    for b in allb:
        pr = rng('po-' + b['booking_id']); exp = to_date(b['payout_date'])
        if b['status'] == 'Cancelled' and b['kept_amount'] == 0: b['payout_status'] = 'Paid'; b['paid_on'] = ''; b['received_amount'] = 0.0; b['_no_payout'] = True; continue
        b['_no_payout'] = False
        paid = exp + day(pr.choice([0, 0, 0, 1, 1, 2])) if b['channel'] != 'Direct' else exp
        if b['booking_id'] == story_b: b['payout_status'] = 'Missing'; b['paid_on'] = ''; b['received_amount'] = 0.0; continue
        if paid <= TODAY:
            short = pr.random() < .025 and b['channel'] != 'Direct'
            b['payout_status'] = 'Short paid' if short else 'Paid'; b['paid_on'] = iso(paid); b['received_amount'] = R2(b['net_payout'] * (pr.choice([.88, .92, .95]) if short else 1.0))
        else:
            b['payout_status'] = 'Scheduled'; b['paid_on'] = ''; b['received_amount'] = 0.0
    return allb, story_b


def _bk(): return _raw('bk', _world_bookings)
def booking_rows(n=None): return _thin(_cached('bkp', lambda: _pub(_bk()[0])), n)


def payout_rows(n=None):
    def f():
        rows = [b for b in _bk()[0] if not b['_no_payout']]; rows.sort(key=lambda b: (b['payout_date'], b['booking_id'])); out = []
        for i, b in enumerate(rows, 1):
            out.append(dict(payout_id='PO-%04d' % i, booking_id=b['booking_id'], channel=b['channel'], unit=b['unit'], expected_date=b['payout_date'], paid_on=b['paid_on'],
                            expected_amount=b['net_payout'], received_amount=b['received_amount'], status=b['payout_status']))
        return out
    return _thin(_cached('po', f), n)


# ------------------------------------------------------------------ turnovers, cleaners
def _turn_build():
    bks = _bk()[0]; r = rng('turn'); live = [b for b in bks if b['status'] != 'Cancelled']
    by_unit = {}
    for b in live: by_unit.setdefault(b['unit_id'], []).append(b)
    rows = []
    for b in live:
        co = to_date(b['check_out'])
        if co > TODAY + day(45): continue
        u = UNIT[b['unit_id']]
        nxt = next((x for x in by_unit[b['unit_id']] if x['check_in'] >= b['check_out'] and x['booking_id'] != b['booking_id']), None)
        same = 'Yes' if nxt and nxt['check_in'] == b['check_out'] else 'No'
        hours = R2(1.4 + .9 * u['bedrooms'] + (.5 if same == 'Yes' else 0) + r.choice([0, 0, .25, .5]))
        pref = {'Lisbon': 'Lucia Fernandes', 'Porto': 'Amara Diallo', 'Cascais': 'Yuki Sato', 'Sintra': 'Yuki Sato'}[u['city']]
        cl = pref if r.random() < .78 else r.choice(CLEANERS)
        rows.append(dict(unit_id=u['unit_id'], unit=u['name'], date=b['check_out'], booking_id=b['booking_id'], next_check_in=nxt['check_in'] if nxt else '', same_day=same, cleaner=cl,
                         hours=hours, linen_sets=max(1, b['guests'] // 2 + 1), status='Done' if co <= TODAY else 'Scheduled', score=0))
    rows.sort(key=lambda t: (t['date'], t['unit_id']))
    # story: the busiest coming day gets 5 turnovers for one cleaner
    ev1 = iso(_event()[1]); today_s = iso(TODAY); cnt = {}
    for t in rows:
        if t['date'] > today_s: cnt[t['date']] = cnt.get(t['date'], 0) + 1
    busy = max(cnt, key=lambda k: (cnt[k], k == ev1)) if cnt else ev1
    sc = 'Lucia Fernandes'; k = 0
    for t in rows:
        if t['date'] == busy and k < 5 and t['status'] == 'Scheduled': t['cleaner'] = sc; t['hours'] = max(t['hours'], 2.3); k += 1
    for i, t in enumerate(rows, 1):
        t['turnover_id'] = 'TO-%04d' % i; rate = staff_by_name[t['cleaner']]['hourly_rate']; t['pay'] = R2(t['hours'] * rate)
        if t['status'] == 'Done':
            x = r.random(); t['score'] = 5 if x < .55 else 4 if x < .88 else 3 if x < .97 else 2
            if t['unit_id'] == STORY_LOW_REVIEW and (TODAY - to_date(t['date'])).days < 80: t['score'] = r.choice([2, 3, 3])
            if t['score'] == 2: t['status'] = 'Redo needed'
    cols = ['turnover_id', 'date', 'unit_id', 'unit', 'booking_id', 'next_check_in', 'same_day', 'cleaner', 'hours', 'pay', 'linen_sets', 'status', 'score']
    return [{k: t[k] for k in cols} for t in rows], (busy, sc)


def _tb(): return _raw('turn', _turn_build)
def turnover_rows(n=None): return _thin(_cached('turn_p', lambda: _tb()[0]), n)


def cleaner_pay_rows(n=None):
    def f():
        agg = {}
        for t in _tb()[0]:
            if t['status'] == 'Scheduled': continue
            k = (t['date'][:7], t['cleaner']); a = agg.setdefault(k, [0, 0.0, 0.0]); a[0] += 1; a[1] += t['hours']; a[2] += t['pay']
        out = []
        for (ym, cl), (cnt, hrs, amt) in sorted(agg.items()):
            m = D(int(ym[:4]), int(ym[5:]), 1)
            out.append(dict(month=iso(m), cleaner=cl, turnovers=cnt, hours=R2(hrs), amount=R2(amt), paid_on=iso(add_months(m, 1) + day(4)) if m < _ms(TODAY) else '',
                            status='Paid' if m < _ms(TODAY) else 'Accruing'))
        for i, x in enumerate(out, 1): x['pay_id'] = 'CP-%03d' % i
        return [{k: x[k] for k in ['pay_id', 'month', 'cleaner', 'turnovers', 'hours', 'amount', 'paid_on', 'status']} for x in out]
    return _thin(_cached('cpay', f), n)


# ------------------------------------------------------------------ supplies
# name, category, pack, unit_cost, reorder_point, par, supplier, use per turnover, buy every k months
_SUP = [('Bath towel', 'Linen and towels', 'each', 6.5, 40, 90, 'Linen wholesaler', .5, 4), ('Hand towel', 'Linen and towels', 'each', 3.2, 40, 90, 'Linen wholesaler', .4, 4),
        ('Bed sheet set', 'Linen and towels', 'set', 18.0, 24, 60, 'Linen wholesaler', .5, 4), ('Duvet cover', 'Linen and towels', 'each', 14.5, 20, 48, 'Linen wholesaler', .3, 6),
        ('Pillow protector', 'Linen and towels', 'each', 5.0, 24, 60, 'Linen wholesaler', .2, 6), ('Shampoo mini', 'Toiletries', 'pack of 50', 22.0, 3, 8, 'Wholesale club', .08, 1),
        ('Body wash mini', 'Toiletries', 'pack of 50', 22.0, 3, 8, 'Wholesale club', .08, 1), ('Hand soap refill', 'Toiletries', 'litre', 4.8, 6, 16, 'Wholesale club', .25, 1),
        ('Toilet paper', 'Consumables', 'pack of 24', 15.0, 4, 10, 'Wholesale club', .12, 1), ('Kitchen roll', 'Consumables', 'pack of 12', 11.0, 3, 8, 'Wholesale club', .1, 1),
        ('Coffee capsules', 'Consumables', 'box of 100', 24.0, 3, 8, 'Wholesale club', .1, 1), ('Tea and sugar kit', 'Consumables', 'box', 9.0, 4, 10, 'Wholesale club', .1, 1),
        ('Bin bags', 'Consumables', 'roll of 50', 4.5, 8, 20, 'Wholesale club', .3, 1), ('Dishwasher tablets', 'Cleaning products', 'box of 60', 10.5, 3, 8, 'Cleaning supplier', .08, 1),
        ('All-purpose cleaner', 'Cleaning products', 'litre', 3.6, 8, 20, 'Cleaning supplier', .3, 1), ('Bathroom cleaner', 'Cleaning products', 'litre', 4.1, 6, 16, 'Cleaning supplier', .2, 1),
        ('Laundry detergent', 'Cleaning products', 'box', 17.0, 3, 8, 'Cleaning supplier', .1, 1), ('Mop heads and cloths', 'Cleaning products', 'pack', 12.0, 3, 8, 'Cleaning supplier', .05, 2),
        ('Wine glasses', 'Kitchen', 'set of 6', 14.0, 4, 10, 'Home store', .03, 3), ('Plates and bowls', 'Kitchen', 'set of 6', 19.0, 3, 8, 'Home store', .03, 3),
        ('Cooking pans', 'Kitchen', 'each', 21.0, 2, 6, 'Home store', .02, 6), ('Smoke alarm battery', 'Safety', 'pack of 4', 9.5, 3, 8, 'Hardware store', .02, 3),
        ('First aid kit', 'Safety', 'each', 16.0, 3, 6, 'Hardware store', .01, 6), ('Door lock battery', 'Safety', 'pack of 8', 13.0, 2, 6, 'Hardware store', .02, 3)]
supply_items = [dict(item_id='IT-%02d' % i, item=s[0], category=s[1], pack=s[2], unit_cost=s[3], reorder_point=s[4], par_level=s[5], supplier=s[6]) for i, s in enumerate(_SUP, 1)]


def supply_purchase_rows(n=None):
    def f():
        r = rng('sup'); tmonth = {}
        for t in _tb()[0]:
            if t['status'] != 'Scheduled': tmonth[t['date'][:7]] = tmonth.get(t['date'][:7], 0) + 1
        out = []
        for k in range(23, -1, -1):
            m = month_start(k)
            for si, s in enumerate(_SUP):
                if (k + si) % s[8]: continue
                tn = sum(tmonth.get(iso(add_months(m, -j))[:7], 0) for j in range(s[8]))
                qty = max(2, int(round(tn * s[7] * r.uniform(.9, 1.15))))
                d = m + day(r.randint(0, 24))
                if d > TODAY: continue
                out.append(dict(date=iso(d), month=iso(m), item=s[0], category=s[1], qty=qty, unit_cost=R2(s[3] * r.uniform(.96, 1.06) * (1 + .03 * (23 - k) / 23.0)), supplier=s[6],
                                paid_by=r.choice(['Business card', 'Business card', 'Bank transfer'])))
        out.sort(key=lambda x: (x['date'], x['item']))
        for i, x in enumerate(out, 1): x['purchase_id'] = 'PU-%04d' % i; x['amount'] = R2(x['qty'] * x['unit_cost'])
        cols = ['purchase_id', 'date', 'month', 'item', 'category', 'qty', 'unit_cost', 'amount', 'supplier', 'paid_by']
        return [{k: x[k] for k in cols} for x in out]
    return _thin(_cached('pur', f), n)


def supply_stock_rows(n=None):
    def f():
        r = rng('stock'); pur = supply_purchase_rows(); out = []
        for s in supply_items:
            last = [p['date'] for p in pur if p['item'] == s['item']]
            low = s['item'] in ('Bath towel', 'Coffee capsules', 'Bin bags', 'Smoke alarm battery')
            on = int(s['reorder_point'] * (r.uniform(.3, .8) if low else r.uniform(1.15, 2.4)))
            out.append(dict(item_id=s['item_id'], item=s['item'], category=s['category'], on_hand=on, reorder_point=s['reorder_point'], par_level=s['par_level'], unit_cost=s['unit_cost'],
                            supplier=s['supplier'], last_bought=last[-1] if last else '', lead_days=r.choice([2, 3, 5, 7])))
        return out
    return _thin(_cached('stock', f), n)


# ------------------------------------------------------------------ maintenance, damage, reviews, messages
def maintenance_rows(n=None):
    def f():
        r = rng('mt'); bks = [b for b in _bk()[0] if b['status'] in ('Completed', 'In stay')]; out = []
        w = [1.0 + (.8 if u['unit_id'] in ('UN-05', 'UN-07', 'UN-09') else 0) for u in units]
        for i in range(236):
            u = _wchoice(r, units, w); days = int(r.random() ** .9 * (HISTORY_DAYS - 20)) + 3
            rep = TODAY - day(min(days, (TODAY - to_date(u['since'])).days - 2)) if days < (TODAY - to_date(u['since'])).days else TODAY - day(r.randint(3, 120))
            kind = r.choice(TICKET_KINDS); src = _wchoice(r, TICKET_SOURCES, [45, 25, 22, 8]); pri = _wchoice(r, PRIORITIES, [25, 55, 20])
            hm = r.choice(HANDY[:1] * 3 + HANDY[1:] * 2)
            age = (TODAY - rep).days; st = 'Done'
            if age < 30: st = _wchoice(r, TICKET_STATUS, [22, 20, 13, 45])
            elif age < 90 and r.random() < .06: st = 'Waiting parts'
            parts = R2(r.choice([0, 0, 12, 25, 40, 85, 160, 340]) * r.uniform(.8, 1.2)); lab = R2(staff_by_name[hm]['hourly_rate'] * r.choice([1, 1.5, 2, 3, 4]))
            done = iso(rep + day(r.randint(0, 6 if pri != 'High' else 2))) if st == 'Done' else ''
            if done and to_date(done) > TODAY: done = ago(0)
            out.append(dict(unit_id=u['unit_id'], unit=u['name'], reported_on=iso(rep), kind=kind, priority=pri, source=src, handyperson=hm, status=st, done_on=done,
                            parts_cost=parts if st != 'Open' else 0.0, labour_cost=lab if st in ('Done', 'In progress') else 0.0,
                            guest_impact='Yes' if (pri == 'High' and r.random() < .7) else 'No'))
        out.sort(key=lambda x: (x['reported_on'], x['unit_id']))
        for i, x in enumerate(out, 1):
            x['ticket_id'] = 'MT-%04d' % i; x['cost'] = R2(x['parts_cost'] + x['labour_cost'])
        cols = ['ticket_id', 'reported_on', 'unit_id', 'unit', 'kind', 'priority', 'source', 'handyperson', 'status', 'done_on', 'parts_cost', 'labour_cost', 'cost', 'guest_impact']
        return [{k: x[k] for k in cols} for x in out]
    return _thin(_cached('maint', f), n)


_DAMAGE = [('Broken wine glasses and plates', 60, 140), ('Stained sofa cover', 90, 260), ('Cigarette burn on bedding', 80, 220), ('Broken shower door handle', 70, 180),
           ('Missing towels and linen', 60, 150), ('Scratched wooden table', 110, 320), ('Damaged garden chair', 70, 160), ('Broken lamp and shade', 55, 130),
           ('Wall paint marks', 120, 380), ('Lost door key and lock change', 90, 210), ('Heavy cleaning after a party', 100, 260), ('Broken TV remote and stand', 60, 190)]


def damage_rows(n=None):
    def f():
        r = rng('dm'); done = [b for b in _bk()[0] if b['status'] == 'Completed' and b['nights'] >= 2]; ch = r.sample(range(len(done)), 34); out = []
        for i in sorted(ch):
            b = done[i]; kind, lo, hi = r.choice(_DAMAGE); amt = R2(r.randint(lo, hi) * (1 + b['nights'] / 20.0)); rep = to_date(b['check_out']) + day(r.randint(0, 3))
            if rep > TODAY - day(20): rep = TODAY - day(r.randint(25, 60))
            dep = {'Direct': 200.0, 'Platform C': 150.0}.get(b['channel'], 0.0)
            st = _wchoice(r, DAMAGE_STATUS, [4, 10, 14, 58, 14]); paid = {'Paid': amt, 'Approved': 0.0, 'Partially paid': R2(amt * .6), 'Rejected': 0.0, 'Pending': 0.0}[st]
            if st == 'Approved' and (TODAY - rep).days > 45: st = 'Paid'; paid = amt
            out.append(dict(booking_id=b['booking_id'], unit_id=b['unit_id'], unit=b['unit'], guest=b['guest'], channel=b['channel'], reported_on=iso(rep), damage=kind, claimed_amount=amt,
                            deposit_held=dep, repair_cost=R2(amt * r.uniform(.6, .95)), status=st, paid_amount=paid, paid_on=iso(rep + day(r.randint(6, 25))) if paid and rep + day(25) < TODAY else ('' if not paid else iso(rep + day(6)))))
        # story: a pending claim reported 9 days ago on a recent stay
        rec = [b for b in _bk()[0] if b['status'] == 'Completed' and 9 <= (TODAY - to_date(b['check_out'])).days <= 14 and b['nights'] >= 3 and b['booking_id'] not in {x['booking_id'] for x in out}]
        b = rec[0] if rec else [b for b in done if (TODAY - to_date(b['check_out'])).days < 40][-1]
        out.append(dict(booking_id=b['booking_id'], unit_id=b['unit_id'], unit=b['unit'], guest=b['guest'], channel=b['channel'], reported_on=ago(9), damage='Burn marks on the sofa and a broken glass table top',
                        claimed_amount=640.0, deposit_held=0.0, repair_cost=455.0, status='Pending', paid_amount=0.0, paid_on=''))
        out.sort(key=lambda x: x['reported_on'])
        for i, x in enumerate(out, 1): x['claim_id'] = 'DM-%03d' % i
        cols = ['claim_id', 'reported_on', 'booking_id', 'unit_id', 'unit', 'guest', 'channel', 'damage', 'claimed_amount', 'deposit_held', 'repair_cost', 'status', 'paid_amount', 'paid_on']
        return [{k: x[k] for k in cols} for x in out]
    return _thin(_cached('dm', f), n)


def review_rows(n=None):
    def f():
        r = rng('rv'); out = []
        for b in _bk()[0]:
            if b['status'] != 'Completed' or r.random() > .64: continue
            u = UNIT[b['unit_id']]; rec = (TODAY - to_date(b['check_out'])).days
            rating = _wchoice(r, [5, 4, 3, 2, 1], [64, 27, 6, 2, 1])
            if u['unit_id'] == STORY_LOSING: rating = _wchoice(r, [5, 4, 3, 2, 1], [48, 33, 12, 5, 2])
            if u['unit_id'] == STORY_LOW_REVIEW and rec < 80: rating = r.choice([2, 3, 3, 2, 3])
            topic = 'Cleanliness' if (u['unit_id'] == STORY_LOW_REVIEW and rec < 80) else r.choice(REVIEW_TOPICS)
            sub = lambda: max(1, min(5, rating + r.choice([-1, 0, 0, 0, 1])))
            rd = to_date(b['check_out']) + day(r.randint(1, 6))
            if rd > TODAY: continue
            replied = 'Yes' if r.random() < (.9 if rating <= 3 else .7) else 'No'
            out.append(dict(date=iso(rd), booking_id=b['booking_id'], unit_id=u['unit_id'], unit=u['name'], channel=b['channel'], guest=b['guest'], rating=rating, cleanliness=sub(),
                            communication=sub(), location=max(3, sub()), value=sub(), topic=topic, replied=replied, reply_on=iso(rd + day(r.randint(0, 3))) if replied == 'Yes' and rd + day(3) <= TODAY else ''))
        out.sort(key=lambda x: (x['date'], x['booking_id']))
        for i, x in enumerate(out, 1): x['review_id'] = 'RV-%04d' % i
        cols = ['review_id', 'date', 'booking_id', 'unit_id', 'unit', 'channel', 'guest', 'rating', 'cleanliness', 'communication', 'location', 'value', 'topic', 'replied', 'reply_on']
        return [{k: x[k] for k in cols} for x in out]
    return _thin(_cached('rv', f), n)


def guest_message_rows(n=None):
    def f():
        r = rng('gm'); out = []; hosts = [OWNER, COHOST]
        for b in _bk()[0]:
            if b['status'] == 'Cancelled' and r.random() < .5: continue
            kinds = ['Check-in instructions'] + [r.choice(MSG_KINDS) for _ in range(r.choice([0, 0, 1, 1, 2]))]
            for j, k in enumerate(kinds):
                if k == 'Check-in instructions': d = to_date(b['check_in']) - day(1)
                elif k in ('Booking question', 'Special request'): d = to_date(b['booked_on']) + day(r.randint(0, 2))
                else: d = to_date(b['check_in']) + day(r.randint(0, max(0, b['nights'] - 1)))
                if d > TODAY or r.random() < .3 and k != 'Check-in instructions': continue
                out.append(dict(date=iso(d), booking_id=b['booking_id'], unit_id=b['unit_id'], unit=b['unit'], guest=b['guest'], kind=k, channel=b['channel'],
                                handled_by=COHOST if UNIT[b['unit_id']]['cohost'] == 'Yes' and r.random() < .8 else OWNER,
                                response_min=int(r.choice([3, 5, 8, 12, 20, 35, 60, 150, 400]) * (1.5 if k == 'Complaint' else 1)), resolved='Yes' if (k != 'Complaint' or r.random() < .85) else 'No'))
        out.sort(key=lambda x: (x['date'], x['booking_id']))
        for i, x in enumerate(out, 1): x['message_id'] = 'GM-%04d' % i
        cols = ['message_id', 'date', 'booking_id', 'unit_id', 'unit', 'guest', 'kind', 'channel', 'handled_by', 'response_min', 'resolved']
        return [{k: x[k] for k in cols} for x in out]
    return _thin(_cached('gm', f), n)


def guest_rows(n=None):
    def f():
        g = {}
        for b in _bk()[0]:
            if b['status'] == 'Cancelled': continue
            x = g.setdefault(b['guest'], dict(guest=b['guest'], country=b['guest_country'], stays=0, nights=0, spend=0.0, last_stay='', first_stay=b['check_in'], channel=b['channel']))
            x['stays'] += 1; x['nights'] += b['nights']; x['spend'] = R2(x['spend'] + b['gross']); x['last_stay'] = b['check_out']
        rows = sorted(g.values(), key=lambda x: (-x['stays'], -x['spend'], x['guest']))
        for i, x in enumerate(rows, 1): x['guest_id'] = 'GS-%04d' % i
        cols = ['guest_id', 'guest', 'country', 'stays', 'nights', 'spend', 'first_stay', 'last_stay', 'channel']
        return [{k: x[k] for k in cols} for x in rows]
    return _thin(_cached('gs', f), n)


# ------------------------------------------------------------------ expenses, statements, taxes, cash
def expense_rows(n=None):
    def f():
        r = rng('ex'); out = []; pay = {'Rent or mortgage': 'Landlord or lender', 'Utilities': 'Utility company', 'Internet and TV': 'Internet provider'}
        for k in range(24, -1, -1):
            m = month_start(k)
            for u in units:
                if to_date(u['since']) > add_months(m, 1) - day(1): continue
                if u['rent']: out.append(dict(date=iso(m), month=iso(m), unit_id=u['unit_id'], unit=u['name'], category='Rent or mortgage', description='Monthly rent or loan payment', amount=float(u['rent']), paid_to=pay['Rent or mortgage']))
                wf = 1.0 + (.22 if m.month in (12, 1, 2) else .18 if m.month in (7, 8) else 0)
                out.append(dict(date=iso(m + day(6)), month=iso(m), unit_id=u['unit_id'], unit=u['name'], category='Utilities', description='Power, water and gas', amount=R2(u['utilities'] * wf * r.uniform(.9, 1.1)), paid_to=pay['Utilities']))
                out.append(dict(date=iso(m + day(9)), month=iso(m), unit_id=u['unit_id'], unit=u['name'], category='Internet and TV', description='Fibre and TV plan', amount=float(u['internet']), paid_to=pay['Internet and TV']))
                if m.month == 1: out.append(dict(date=iso(m + day(14)), month=iso(m), unit_id=u['unit_id'], unit=u['name'], category='Local taxes and permits', description='Yearly licence and registration', amount=R2(r.choice([95, 120, 140])), paid_to='City office'))
            pf = [('Software and subscriptions', 'Pricing tool, channel manager and lock app', 118.0 + 4 * (24 - k) / 6.0, 'Software provider', 3), ('Accounting and legal', 'Bookkeeping and tax adviser', 160.0, 'Accountant', 12)]
            for cat, desc, amt, to, dd in pf: out.append(dict(date=iso(m + day(dd)), month=iso(m), unit_id='', unit='Portfolio', category=cat, description=desc, amount=R2(amt), paid_to=to))
            if r.random() < .75: out.append(dict(date=iso(m + day(r.randint(10, 25))), month=iso(m), unit_id='', unit='Portfolio', category='Marketing and photos', description=r.choice(['Photo update', 'Direct booking site', 'Listing boost', 'Guest guidebook print']), amount=R2(r.choice([60, 95, 140, 220, 380])), paid_to='Photo and print studio'))
            if m.month in (1, 4, 7, 10): out.append(dict(date=iso(m + day(2)), month=iso(m), unit_id='', unit='Portfolio', category='Insurance', description='Property and liability cover, quarter', amount=R2(430 + 18 * (24 - k) / 6.0), paid_to='Insurer'))
        out = [x for x in out if to_date(x['date']) <= TODAY and to_date(x['month']) >= month_start(23)]
        out.sort(key=lambda x: (x['date'], x['unit_id'], x['category']))
        for i, x in enumerate(out, 1): x['expense_id'] = 'EX-%04d' % i
        cols = ['expense_id', 'date', 'month', 'unit_id', 'unit', 'category', 'description', 'amount', 'paid_to']
        return [{k: x[k] for k in cols} for x in out]
    return _thin(_cached('exp', f), n)


def _by_month_unit():
    """monthly per unit sums by check-out month: revenue, fees, cleaning, supplies, maintenance, utilities"""
    def f():
        agg = {}
        def a(u, m): return agg.setdefault((u, m), dict(revenue=0.0, fees=0.0, cleaning=0.0, supplies=0.0, maintenance=0.0, utilities=0.0, fixed=0.0, nights=0, stays=0))
        for b in _bk()[0]:
            m = b['check_out'][:7]
            if b['status'] in ('Completed',): x = a(b['unit_id'], m); x['revenue'] += b['earned']; x['fees'] += b['platform_fee']; x['nights'] += b['nights']; x['stays'] += 1
            elif b['status'] == 'Cancelled' and b['kept_amount'] and to_date(b['check_out']) <= TODAY: x = a(b['unit_id'], m); x['revenue'] += b['earned']; x['fees'] += b['platform_fee']
        for t in _tb()[0]:
            if t['status'] != 'Scheduled':
                a(t['unit_id'], t['date'][:7])['cleaning'] += t['pay']
                a(t['unit_id'], t['date'][:7])['supplies'] += 8.0 + 2.5 * UNIT[t['unit_id']]['bedrooms']
        for t in maintenance_rows():
            if t['status'] == 'Done' and t['done_on']: a(t['unit_id'], t['done_on'][:7])['maintenance'] += t['cost']
        for e in expense_rows():
            if e['unit_id']:
                x = a(e['unit_id'], e['month'][:7])
                if e['category'] in ('Utilities', 'Internet and TV'): x['utilities'] += e['amount']
                else: x['fixed'] += e['amount']
        return agg
    return _raw('bmu', f)


def owner_statement_rows(n=None):
    def f():
        out = []; agg = _by_month_unit()
        for o in owners[1:]:
            ous = [u for u in units if u['owner'] == o['name']]
            for k in range(23, -1, -1):
                m = month_start(k); ym = iso(m)[:7]; tot = dict(revenue=0.0, fees=0.0, cleaning=0.0, supplies=0.0, maintenance=0.0, utilities=0.0, nights=0)
                for u in ous:
                    x = agg.get((u['unit_id'], ym))
                    if x:
                        for kk in tot: tot[kk] += x[kk]
                if tot['revenue'] == 0: continue
                mg = R2((tot['revenue'] - tot['fees']) * o['mgmt_pct'])
                net = R2(tot['revenue'] - tot['fees'] - tot['cleaning'] - tot['supplies'] - tot['maintenance'] - tot['utilities'] - mg)
                st = 'Paid' if k >= 2 else 'Sent' if k == 1 else 'Draft'
                out.append(dict(owner=o['name'], month=iso(m), units=len(ous), nights=tot['nights'], revenue=R2(tot['revenue']), platform_fees=R2(tot['fees']), cleaning_costs=R2(tot['cleaning']),
                                supplies=R2(tot['supplies']), maintenance=R2(tot['maintenance']), utilities=R2(tot['utilities']), mgmt_pct=o['mgmt_pct'], mgmt_fee=mg, net_to_owner=net, status=st,
                                paid_on=iso(add_months(m, 1) + day(9)) if st == 'Paid' else ''))
        out.sort(key=lambda x: (x['month'], x['owner']))
        for i, x in enumerate(out, 1): x['statement_id'] = 'OS-%03d' % i
        cols = ['statement_id', 'month', 'owner', 'units', 'nights', 'revenue', 'platform_fees', 'cleaning_costs', 'supplies', 'maintenance', 'utilities', 'mgmt_pct', 'mgmt_fee', 'net_to_owner', 'status', 'paid_on']
        return [{k: x[k] for k in cols} for x in out]
    return _thin(_cached('os', f), n)


def cohost_fee_rows(n=None):
    def f():
        agg = _by_month_unit(); out = []
        for k in range(23, -1, -1):
            m = month_start(k); ym = iso(m)[:7]; cu = [u for u in units if u['cohost'] == 'Yes']; rev = sum(agg.get((u['unit_id'], ym), {}).get('revenue', 0) for u in cu)
            fee = sum(agg.get((u['unit_id'], ym), {}).get('fees', 0) for u in cu)
            if rev == 0: continue
            net = R2(rev - fee); msgs = sum(1 for g in guest_message_rows() if g['date'][:7] == ym and g['handled_by'] == COHOST)
            out.append(dict(month=iso(m), units=len(cu), revenue=R2(rev), platform_fees=R2(fee), net_revenue=net, fee_pct=0.10, fee_amount=R2(net * .10), messages=msgs,
                            status='Paid' if k >= 1 else 'Accruing', paid_on=iso(add_months(m, 1) + day(4)) if k >= 1 else ''))
        for i, x in enumerate(out, 1): x['fee_id'] = 'CF-%03d' % i
        cols = ['fee_id', 'month', 'units', 'revenue', 'platform_fees', 'net_revenue', 'fee_pct', 'fee_amount', 'messages', 'status', 'paid_on']
        return [{k: x[k] for k in cols} for x in out]
    return _thin(_cached('cf', f), n)


def tax_rows(n=None):
    def f():
        out = []
        for k in range(23, -1, -1):
            m = month_start(k); ym = iso(m)[:7]
            for c in cities:
                bs = [b for b in _bk()[0] if b['city'] == c['city'] and b['check_in'][:7] == ym and b['status'] != 'Cancelled']
                if not bs: continue
                tot = sum(b['tax_collected'] for b in bs); host = sum(b['tax_collected'] for b in bs if b['tax_by'] == 'Host'); due = add_months(m, 1) + day(19)
                st = 'Filed and paid' if due < TODAY else 'Due' if due - day(30) < TODAY else 'Upcoming'
                out.append(dict(month=iso(m), city=c['city'], tax_pct=c['tax_pct'], nights=sum(b['nights'] for b in bs), room_revenue=R2(sum(b['room_revenue'] for b in bs)), tax_collected=R2(tot),
                                collected_by_host=R2(host), due_date=iso(due), remitted=R2(host) if st == 'Filed and paid' else 0.0, paid_on=iso(due - day(2 + (k * 3) % 6)) if st == 'Filed and paid' else '', status=st))
        for i, x in enumerate(out, 1): x['tax_id'] = 'TX-%03d' % i
        cols = ['tax_id', 'month', 'city', 'tax_pct', 'nights', 'room_revenue', 'tax_collected', 'collected_by_host', 'due_date', 'remitted', 'paid_on', 'status']
        return [{k: x[k] for k in cols} for x in out]
    return _thin(_cached('tax', f), n)


def unit_month_rows(n=None):
    def f():
        nights = {}
        for b in _bk()[0]:
            if b['status'] == 'Cancelled': continue
            ci, co = to_date(b['check_in']), to_date(b['check_out'])
            for i in range(b['nights']):
                d = ci + day(i); nights.setdefault((b['unit_id'], iso(d)[:7]), [0, 0.0]); x = nights[(b['unit_id'], iso(d)[:7])]; x[0] += 1; x[1] += b['room_revenue'] / b['nights']
        out = []
        for k in range(23, -3, -1):
            m = month_start(k); ym = iso(m)[:7]; dim = calendar.monthrange(m.year, m.month)[1]
            for u in units:
                s = to_date(u['since'])
                if s > add_months(m, 1) - day(1): continue
                avail = dim - max(0, (s - m).days) if s > m else dim; o, rev = nights.get((u['unit_id'], ym), [0, 0.0]); o = min(o, avail)
                out.append(dict(month=iso(m), unit_id=u['unit_id'], unit=u['name'], city=u['city'], available_nights=avail, booked_nights=o, room_revenue=R2(rev),
                                occupancy=R2(o / float(avail)), adr=R2(rev / o) if o else 0.0, revpar=R2(rev / avail), basis='Slept' if m < _ms(TODAY) else 'On the books'))
        for i, x in enumerate(out, 1): x['row_id'] = 'UM-%04d' % i
        cols = ['row_id', 'month', 'unit_id', 'unit', 'city', 'available_nights', 'booked_nights', 'room_revenue', 'occupancy', 'adr', 'revpar', 'basis']
        return [{k: x[k] for k in cols} for x in out]
    return _thin(_cached('um', f), n)


def season_rows(n=None):
    def f():
        out = []
        for m in range(1, 13):
            out.append(dict(month_no=m, month_name=calendar.month_name[m], season=season_of(m), price_factor=_SEAS[m], occupancy_factor=_OCC[m], weekend_lift=0.15))
        return out
    return _thin(_cached('seas', f), n)


def price_rows(n=None):
    def f():
        r = rng('price'); ev0, ev1 = _event(); w0 = week_start(TODAY); out = []; bks = [b for b in _bk()[0] if b['status'] != 'Cancelled']
        for w in range(13):
            ws = w0 + day(7 * w)
            for u in units:
                booked = 0; rev = 0.0
                for b in bks:
                    if b['unit_id'] != u['unit_id']: continue
                    ci, co = to_date(b['check_in']), to_date(b['check_out'])
                    if co <= ws or ci >= ws + day(7): continue
                    ov = (min(co, ws + day(7)) - max(ci, ws)).days; booked += ov; rev += ov * b['room_revenue'] / b['nights']
                ev = ws == ev0 and u['city'] == 'Lisbon'; demand = 1.5 if ev else R2(r.uniform(.85, 1.2))
                fac = _SEAS[(ws + day(3)).month]; listed = R2(u['base_rate'] * fac * (1.0 if ev else r.uniform(.97, 1.04)))
                if ev: listed = R2(u['base_rate'] * _SEAS[ev0.month])
                out.append(dict(week=iso(ws), unit_id=u['unit_id'], unit=u['name'], city=u['city'], base_rate=float(u['base_rate']), season=season_of((ws + day(3)).month), season_factor=fac,
                                demand_index=demand, event='Local festival week' if ev else '', listed_rate=listed, booked_nights=booked, free_nights=7 - booked,
                                avg_booked_rate=R2(rev / booked) if booked else 0.0, min_stay=2 if fac < 1.2 else 3))
        for i, x in enumerate(out, 1): x['row_id'] = 'PR-%04d' % i
        cols = ['row_id', 'week', 'unit_id', 'unit', 'city', 'base_rate', 'season', 'season_factor', 'demand_index', 'event', 'listed_rate', 'booked_nights', 'free_nights', 'avg_booked_rate', 'min_stay']
        return [{k: x[k] for k in cols} for x in out]
    return _thin(_cached('pr', f), n)


def unit_profit(unit_id, months=12):
    agg = _by_month_unit(); ms = [iso(month_start(k))[:7] for k in range(1, months + 1)]; t = dict(revenue=0.0, fees=0.0, cleaning=0.0, supplies=0.0, maintenance=0.0, utilities=0.0, fixed=0.0, nights=0)
    for m in ms:
        x = agg.get((unit_id, m))
        if x:
            for k in t: t[k] += x[k]
    t['profit'] = R2(t['revenue'] - t['fees'] - t['cleaning'] - t['supplies'] - t['maintenance'] - t['utilities'] - t['fixed'])
    return t


def cash_rows(n=None):
    def f():
        agg = _by_month_unit(); out = []; bk = _bk()[0]
        pos = {}
        def add(ym, k, v): pos.setdefault(ym, {}).setdefault(k, 0.0); pos[ym][k] += v
        for b in bk:
            if b['paid_on']: add(b['paid_on'][:7], 'payouts', b['received_amount'])
        for d in damage_rows():
            if d['paid_on'] and d['paid_amount']: add(d['paid_on'][:7], 'damage', d['paid_amount'])
        for e in expense_rows(): add(e['date'][:7], 'expenses', e['amount'])
        for t in _tb()[0]:
            if t['status'] != 'Scheduled': add(add_months(to_date(t['date']), 1).isoformat()[:7] if False else t['date'][:7], 'cleaners', t['pay'])
        for p in supply_purchase_rows(): add(p['date'][:7], 'supplies', p['amount'])
        for t in maintenance_rows():
            if t['status'] == 'Done' and t['done_on']: add(t['done_on'][:7], 'maintenance', t['cost'])
        for c in cohost_fee_rows():
            if c['paid_on']: add(c['paid_on'][:7], 'cohost', c['fee_amount'])
        for s in owner_statement_rows():
            if s['paid_on']: add(s['paid_on'][:7], 'owners', s['net_to_owner'])
        for t in tax_rows():
            if t['paid_on']: add(t['paid_on'][:7], 'taxes', t['remitted'])
        bal = 0.0; rows = []
        for k in range(13, -1, -1):
            m = month_start(k); ym = iso(m)[:7]; p = pos.get(ym, {})
            inn = p.get('payouts', 0) + p.get('damage', 0); out_ = sum(p.get(x, 0) for x in ('expenses', 'cleaners', 'supplies', 'maintenance', 'cohost', 'owners', 'taxes'))
            draw = 7000.0 if k > 0 else 3000.0
            rows.append(dict(month=iso(m), opening=0, cash_in=R2(inn), expenses=R2(p.get('expenses', 0)), cleaners=R2(p.get('cleaners', 0)), supplies=R2(p.get('supplies', 0)),
                             maintenance=R2(p.get('maintenance', 0)), cohost_fees=R2(p.get('cohost', 0)), owner_payouts=R2(p.get('owners', 0)), local_taxes=R2(p.get('taxes', 0)), owner_draw=draw, closing=0))
        run = 0.0; mn = 0.0
        for x in rows:
            run += x['cash_in'] - (x['expenses'] + x['cleaners'] + x['supplies'] + x['maintenance'] + x['cohost_fees'] + x['owner_payouts'] + x['local_taxes'] + x['owner_draw']); mn = min(mn, run)
        op = R2(9000 - mn); bal = op
        for x in rows:
            x['opening'] = R2(bal); bal += x['cash_in'] - (x['expenses'] + x['cleaners'] + x['supplies'] + x['maintenance'] + x['cohost_fees'] + x['owner_payouts'] + x['local_taxes'] + x['owner_draw'])
            x['closing'] = R2(bal)
        return rows
    return _thin(_cached('cash', f), n)


def story():
    """ids of the story rows: unit_losing (+ unit_losing_profit), missing_payout (payout id, booking, amount), pending_claim, low_review_unit (+ low_review_avg), overbooked_cleaner,
    overbooked_date, overbooked_turnovers, overbooked_hours, pricing_unit, pricing_week, pricing_booked_nights, pricing_listed_rate"""
    bks, sb = _bk(); out = {}
    out['unit_losing'] = STORY_LOSING; out['unit_losing_profit'] = unit_profit(STORY_LOSING)['profit']
    po = next(p for p in payout_rows() if p['booking_id'] == sb); out['missing_payout'] = po['payout_id']; out['missing_booking'] = sb; out['missing_amount'] = po['expected_amount']; out['missing_channel'] = po['channel']
    pc = [d for d in damage_rows() if d['status'] == 'Pending']; out['pending_claim'] = pc[-1]['claim_id']; out['pending_amount'] = pc[-1]['claimed_amount']
    rv = [x for x in review_rows() if x['unit_id'] == STORY_LOW_REVIEW and (TODAY - to_date(x['date'])).days <= 90]
    out['low_review_unit'] = STORY_LOW_REVIEW; out['low_review_avg'] = R2(sum(x['rating'] for x in rv) / float(len(rv))) if rv else 0; out['low_review_count'] = len(rv)
    busy, sc = _tb()[1]; ts = [t for t in turnover_rows() if t['date'] == busy and t['cleaner'] == sc]
    out['overbooked_cleaner'] = sc; out['overbooked_date'] = busy; out['overbooked_turnovers'] = len(ts); out['overbooked_hours'] = R2(sum(t['hours'] for t in ts))
    ev0, ev1 = _event(); pr = next(p for p in price_rows() if p['unit_id'] == STORY_EVENT_UNIT and p['week'] == iso(ev0))
    out['pricing_unit'] = STORY_EVENT_UNIT; out['pricing_week'] = iso(ev0); out['pricing_booked_nights'] = pr['booked_nights']; out['pricing_listed_rate'] = pr['listed_rate']; out['pricing_base_rate'] = pr['base_rate']
    return out


def _digest():
    h = hashlib.md5()
    for fn in (booking_rows, payout_rows, turnover_rows, cleaner_pay_rows, supply_purchase_rows, supply_stock_rows, maintenance_rows, damage_rows, review_rows, guest_message_rows, expense_rows,
               owner_statement_rows, cohost_fee_rows, tax_rows, unit_month_rows, price_rows, cash_rows):
        h.update(repr(fn()).encode())
    return h.hexdigest()[:12]


if __name__ == '__main__':
    import time
    t0 = time.time(); S = story(); bk = booking_rows(); po = payout_rows(); to = turnover_rows(); cr = cash_rows()
    print('staff', len(staff), 'units', len(units), 'bookings', len(bk), 'payouts', len(po), 'turnovers', len(to), 'cleaner pay', len(cleaner_pay_rows()), 'purchases', len(supply_purchase_rows()),
          'stock', len(supply_stock_rows()), 'tickets', len(maintenance_rows()), 'claims', len(damage_rows()), 'reviews', len(review_rows()), 'messages', len(guest_message_rows()),
          'guests', len(guest_rows()))
    print('expenses', len(expense_rows()), 'statements', len(owner_statement_rows()), 'cohost fees', len(cohost_fee_rows()), 'tax', len(tax_rows()), 'unit months', len(unit_month_rows()),
          'price rows', len(price_rows()), 'cash', len(cr))
    for nm, rows, key in (('bookings', bk, 'booking_id'), ('payouts', po, 'payout_id'), ('turnovers', to, 'turnover_id'), ('tickets', maintenance_rows(), 'ticket_id'), ('claims', damage_rows(), 'claim_id'),
                          ('reviews', review_rows(), 'review_id'), ('messages', guest_message_rows(), 'message_id'), ('expenses', expense_rows(), 'expense_id'), ('purchases', supply_purchase_rows(), 'purchase_id'),
                          ('statements', owner_statement_rows(), 'statement_id'), ('tax', tax_rows(), 'tax_id'), ('guests', guest_rows(), 'guest_id')):
        assert len({x[key] for x in rows}) == len(rows), nm
    assert 1100 <= len(bk) <= 1350, len(bk)
    assert {b['channel'] for b in bk} <= set(CHANNELS) and {b['status'] for b in bk} <= set(BOOKING_STATUS) and {p['status'] for p in po} <= set(PAYOUT_STATUS)
    assert {t['status'] for t in to} <= set(TURN_STATUS) and {x['category'] for x in expense_rows()} <= set(EXPENSE_CATEGORIES) and {x['status'] for x in damage_rows()} <= set(DAMAGE_STATUS)
    assert all(b['gross'] > 0 and b['nights'] >= 1 for b in bk) and all(b['check_out'] > b['check_in'] for b in bk)
    # current month and last 30 days must have bookings and payouts
    ms = iso(month_start(0)); t30 = ago(30)
    assert sum(1 for b in bk if b['check_in'] >= ms and b['check_in'] <= iso(TODAY) and b['status'] != 'Cancelled') >= 3, 'check-ins this month'
    assert sum(1 for b in bk if b['booked_on'] >= ms) >= 10, 'booked this month'
    assert sum(1 for b in bk if b['booked_on'] >= t30) >= 25 and sum(1 for p in po if p['paid_on'] >= t30 and p['paid_on'] <= iso(TODAY)) >= 15, 'last 30 days'
    assert sum(1 for p in po if p['paid_on'] >= ms and p['paid_on'] <= iso(TODAY)) >= 3 and sum(1 for b in bk if b['check_out'] >= ms and b['check_out'] <= iso(TODAY) and b['status'] == 'Completed') >= 3
    tot = sum(b['gross'] for b in bk if b['status'] in ('Completed', 'In stay')); print('gross', round(tot), 'fees', round(sum(b['platform_fee'] for b in bk)), 'by channel', {c: sum(1 for b in bk if b['channel'] == c) for c in CHANNELS})
    print('cash min', min(c['closing'] for c in cr), 'last', cr[-1]['closing'], 'opening', cr[0]['opening']); assert min(c['closing'] for c in cr) > 0 and cr[-1]['closing'] > cr[0]['opening'] * 0.5
    # story checks
    assert S['unit_losing_profit'] < 0 and all(unit_profit(u['unit_id'])['profit'] > 0 for u in units if u['unit_id'] != STORY_LOSING and u['unit_id'] != 'UN-08' or u['unit_id'] == 'UN-08'), S['unit_losing_profit']
    pl = {u['unit_id']: unit_profit(u['unit_id'])['profit'] for u in units}; print('unit profit 12m', {k: round(v) for k, v in pl.items()}); assert sum(1 for v in pl.values() if v < 0) == 1
    mb = next(b for b in bk if b['booking_id'] == S['missing_booking']); assert mb['payout_status'] == 'Missing' and mb['channel'] == 'Platform B' and 21 <= (TODAY - to_date(mb['payout_date'])).days <= 45 and S['missing_amount'] > 300
    assert S['pending_amount'] >= 500 and sum(1 for d in damage_rows() if d['status'] == 'Pending') >= 1
    assert S['low_review_count'] >= 5 and S['low_review_avg'] < 3.5
    others = [x['rating'] for x in review_rows() if x['unit_id'] != STORY_LOW_REVIEW and (TODAY - to_date(x['date'])).days <= 90]; assert sum(others) / float(len(others)) > 4.4
    assert S['overbooked_turnovers'] >= 5 and S['overbooked_hours'] > 10 and 0 < (to_date(S['overbooked_date']) - TODAY).days <= 45
    assert S['pricing_booked_nights'] >= 6 and S['pricing_listed_rate'] <= S['pricing_base_rate'] * 1.1
    print('story', S)
    d1 = _digest(); _CACHE.clear()
    for fn in (cash_rows, price_rows, review_rows, turnover_rows, booking_rows): fn()
    d2 = _digest(); assert d1 == d2, (d1, d2)
    print('digest', d1, 'secs', round(time.time() - t0, 1))
