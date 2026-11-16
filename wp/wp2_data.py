"""Wedding suite part 2: demo rows from wp_core (households, guests) and the rows of the small and ranked tables."""
import sys, os, collections, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wp2_lists import *

ST = story()
dd = to_date
TEAM = {t['team_id']: t for t in team}
VEND = {x['vendor_id']: x for x in vendor_rows()}
HHS = [dict(h) for h in household_rows()]
GS = [dict(g) for g in guest_rows()]
WD = WEDDING_DAY


def nb(d): return {k: v_ for k, v_ in d.items() if v_ not in ('', None)}


# ---- phones taken from the team and the vendors (never invented)
P1_PHONE = TEAM['WP-01']['phone']; P2_PHONE = TEAM['WP-02']['phone']; PAR1_PHONE = TEAM['WP-03']['phone']; PAR2_PHONE = TEAM['WP-04']['phone']
LEAD1_PHONE = TEAM['WP-07']['phone']; VENUE_PHONE = TEAM['WP-11']['phone']; CATERER_PHONE = TEAM['WP-12']['phone']
HOTEL_PHONE = VEND['VD-16']['phone']; PRINTER_PHONE = VEND['VD-12']['phone']

# ---- small edits of the shared rows so every list is used and the story has a meal gap (input values of this part)
for h in HHS:
    if h['household_id'] == 'HH-11': h['chase_channel'] = 'In person'
    if h['household_id'] in ('HH-46', 'HH-65'): h['contact_status'] = 'Lost touch'
BOOK, RM = [], 0
for h in HHS:
    if h['lodging'] == 'Room block' and RM < 11:
        BOOK.append(h['household_id']); RM += math.ceil(h['size'] / 2)
for g in GS:
    if g['guest_id'] in ('GS-020', 'GS-031', 'GS-056'): g['meal'] = ''
SIZE = sum(h['size'] for h in HHS)
assert SIZE == len(GS) == 150 and RM == 11


def hh_d():
    out = []
    for h in HHS:
        r = dict(household_id=h['household_id'], household=h['household'], contact=h['contact'], phone=h['phone'], email=h['email'], side=key('side', h['side']), tier=key('tier', h['tier']),
                 list_ab=key('listab', h['list_ab']), region=key('region', h['region']), size=h['size'], rsvp=key('rsvp', h['rsvp']), save_the_date=h['save_the_date'], invite_sent=h['invite_sent'],
                 contact_status=key('cstat', h['contact_status']), last_chase=h['last_chase'], chase_channel=key('channel', h['chase_channel']) if h['chase_channel'] else '',
                 lodging=key('lodging', h['lodging']), arrival=h['arrival'], open_plus_ones=h['open_plus_ones'], room_booked=h['household_id'] in BOOK)
        out.append(nb(r))
    return out


def guests_d():
    out = []
    for g in sorted(GS, key=lambda g_: g_['guest_id'] != 'GS-008'):
        r = dict(guest_id=g['guest_id'], guest=g['guest'], household_id=g['household_id'], household=g['household'], side=key('side', g['side']), tier=key('tier', g['tier']),
                 list_ab=key('listab', g['list_ab']), age_group=key('age', g['age_group']), plus_one=bool(g['plus_one']), invite_sent=g['invite_sent'], rsvp=key('rsvp', g['rsvp']),
                 rsvp_date=g['rsvp_date'], meal=key('meal', g['meal']) if g['meal'] else '', dietary=key('dietary', g['dietary']) if g['dietary'] else '', table=key('table', g['table']) if g['table'] else '')
        out.append(nb(r))
    return out


# ---- counts used as defaults of tools and policy options
NAMED_PLUS = sum(1 for g in GS if g['plus_one'])
KIDS = sum(1 for g in GS if g['age_group'] == 'Child')
FAM_KIDS = sum(1 for g in GS if g['age_group'] == 'Child' and g['tier'] == 'Family')
OPEN_PLUS = sum(h['open_plus_ones'] for h in HHS)
RATES = {('Local', 'A list'): 0.90, ('Same country', 'A list'): 0.80, ('Abroad', 'A list'): 0.60, ('Local', 'B list'): 0.95, ('Same country', 'B list'): 0.85, ('Abroad', 'B list'): 0.65}


def rates_d(): return [dict(region=key('region', r), list_ab=key('listab', l_), rate=RATES[(r, l_)]) for l_ in LIST_AB for r in REGIONS]


def sidebal_d(): return [dict(row_id='SB-%02d' % (n + 1), side=key('side', s), tier=key('tier', t)) for n, (s, t) in enumerate((s, t) for s in SIDES for t in TIERS)]
def forecast_d(): return [dict(row_id='FC-%02d' % (n + 1), tier=key('tier', t), region=key('region', r)) for n, (t, r) in enumerate((t, r) for t in TIERS for r in REGIONS)]


# ---- ranked tables: the number of rows follows the households that have something to chase
def _score(h):
    n = sum(1 for g in GS if g['household_id'] == h['household_id'] and g['rsvp'] == 'Yes' and not g['meal'])
    return h['rsvp'] == 'Pending' or n > 0 or h['open_plus_ones'] > 0 or h['contact_status'] != 'Up to date'
N_CHASE = sum(1 for h in HHS if _score(h))
N_BQ = sum(1 for h in HHS if h['list_ab'] == 'B list')
N_STAY = sum(1 for h in HHS if h['lodging'] != 'Local')
N_DIET = sum(1 for g in GS if g['dietary'])
assert N_CHASE >= 12 and N_BQ >= 12 and N_STAY >= 12 and N_DIET >= 12, (N_CHASE, N_BQ, N_STAY, N_DIET)


def chase_d(): return [dict(rank=i + 1) for i in range(N_CHASE)]
def bq_d(): return [dict(rank=i + 1) for i in range(N_BQ)]
def stay_d(): return [dict(rank=i + 1) for i in range(N_STAY)]
def diet_d(): return [dict(rank=i + 1) for i in range(N_DIET)]


def weeks_d():
    w0 = week_start(INVITE_A_ON)
    return [dict(week=key('week', 'Week %d' % (i + 1)), week_start=iso(w0 + day(7 * i))) for i in range(12)]


def meals_d(): return [dict(meal=key('meal', m)) for m in MEALS]
def mtable_d(): return [dict(table=key('table', t)) for t in TABLE_IDS]
def cstat_d(): return [dict(status=key('cstat', s), tier=key('tier', t)) for s in CONTACT_STATUS for t in TIERS]
def scen_d(): return [dict(scenario=key('scen', s)) for s in SCENARIOS]


def pol_d():
    vals = {'Named guests and open plus-ones': (NAMED_PLUS + OPEN_PLUS, KIDS), 'Named guests only': (NAMED_PLUS, KIDS), 'Adults only': (NAMED_PLUS, 0), 'Adults and family children': (NAMED_PLUS, FAM_KIDS), 'No plus-ones, family children': (0, FAM_KIDS)}
    return [dict(policy=key('policy', p), plusones=vals[p][0], children=vals[p][1]) for p in POLICIES]


def polres_d(): return [dict(policy=key('policy', p)) for p in POLICIES]


def rooms_d():
    rb = roomblock_rows()
    out = [dict(night=iso(WD - day(2)), rooms_held=6, picked_up=2)] + [dict(night=r['night'], rooms_held=r['rooms_held'], picked_up=r['picked_up']) for r in rb]
    return out + [dict(night=iso(WD + day(2)), rooms_held=4, picked_up=0)]


def arrivals_d(): return [dict(date=iso(WD + day(k))) for k in (-1, 0, -2, 1, 2)]


# invitation timeline: the dates are the planned or actual dates; weeks before the wedding fill in
TIME = [('Save the date, all households', ago(170), True), ('Travel and hotel details sent', ago(160), True), ('Invitations, A list', ago(40), True), ('Invitations, B list second wave', ago(12), True),
        ('First reminder to silent households', ahead(7), False), ('Phone calls to silent households', ahead(14), False), ('Reply-by date', iso(RSVP_DEADLINE), False),
        ('Meal and dietary choices closed', iso(RSVP_DEADLINE + day(7)), False), ('Seating plan from the replies', ahead(45), False), ('Room block cut-off', iso(ROOM_CUTOFF), False),
        ('Final headcount to the caterer', iso(HEADCOUNT_DATE), False), ('Place cards and table list printed', iso(WD - day(10)), False)]


def itime_d(): return [dict(step=s, date=d_, done=dn) for s, d_, dn in TIME]


PAPER = {'Save the date card': (1, False, '', 0.62), 'Invitation card': (1, False, '', 2.30), 'Reply card': (1, False, '', 0.45), 'Details card': (1, False, '', 0.60), 'Envelope': (2, False, '', 0.38),
         'Reminder card': (1, False, '', 0.45), 'Place card': (1, True, '', 0.30), 'Order of service': (1, True, '', 0.60), 'Postage, local': (1, False, 'Local', 0.85),
         'Postage, same country': (1, False, 'Same country', 1.10), 'Postage, abroad': (1, False, 'Abroad', 2.40), 'Thank-you card': (1, False, '', 0.70)}


def paper_d():
    return [nb(dict(item=key('pitem', i), per_unit=PAPER[i][0], per_guest=PAPER[i][1], region=key('region', PAPER[i][2]) if PAPER[i][2] else '', unit_cost=PAPER[i][3])) for i in PAPER_ITEMS]
