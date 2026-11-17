"""Wedding suite part 5: demo rows from wp_core (households, guests, tables, rules) with small seating edits, and the rows of the ranked tables."""
import sys, os, collections, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wp5_lists import *

ST = story()
TEAM = {t['team_id']: t for t in team}
VEND = {x['vendor_id']: x for x in vendor_rows()}
HHS = [dict(h) for h in household_rows()]
GS = [dict(g) for g in guest_rows()]
TBS = [dict(t) for t in table_rows()]
RULES = [dict(r) for r in seat_rule_rows()]
WD = WEDDING_DAY
GI = {g['guest_id']: g for g in GS}


def nb(d): return {k: v_ for k, v_ in d.items() if v_ not in ('', None)}


def phone_of(vendor_word):
    return next(x['phone'] for x in VEND.values() if x['vendor'] == vendor_word)


P1_PHONE = TEAM['WP-01']['phone']; P2_PHONE = TEAM['WP-02']['phone']; PAR1_PHONE = TEAM['WP-03']['phone']; PAR2_PHONE = TEAM['WP-04']['phone']
LEAD1_PHONE = TEAM['WP-07']['phone']; HELPER_PHONE = TEAM['WP-09']['phone']; DAYOF_PHONE = TEAM['WP-10']['phone']
VENUE_PHONE = TEAM['WP-11']['phone']; CATERER_PHONE = TEAM['WP-12']['phone']; OFFICIANT_PHONE = TEAM['WP-16']['phone']
HOTEL_PHONE = VEND['VD-16']['phone']
RENTALS_PHONE = next((x['phone'] for x in VEND.values() if 'ental' in x['vendor']), VENUE_PHONE)

# ---- seating edits (input values of this part): five keep-together pairs are seated together, three still conflict, one keep-apart pair shares a table
def occ(t): return sum(1 for g in GS if g['table'] == t) + next(x['reserved'] for x in TBS if x['table_id'] == t)
for rid in ('SR-02', 'SR-03', 'SR-04', 'SR-06', 'SR-07'):
    r = next(x for x in RULES if x['rule_id'] == rid)
    a, b = GI[r['guest_a']], GI[r['guest_b']]
    if a['table'] and a['table'] != b['table'] and occ(a['table']) < 10: b['table'] = a['table']
r14 = next(x for x in RULES if x['rule_id'] == 'SR-14'); GI[r14['guest_b']]['table'] = GI[r14['guest_a']]['table']
assert all(occ(t['table_id']) <= 10 for t in TBS)
SEATED = [g for g in GS if g['table']]
UNSEATED_YES = [g for g in GS if g['rsvp'] == 'Yes' and not g['table']]
PENDING = [g for g in GS if g['rsvp'] == 'Pending']
assert len(SEATED) == 99 and len(UNSEATED_YES) == 4 and len(PENDING) == 18
N_UNSEAT = len(UNSEATED_YES) + len(PENDING)
N_CARDS = len(SEATED)
N_SPLIT = sum(1 for h in HHS if h['size'] >= 2 and h['rsvp'] == 'Yes')
assert N_SPLIT >= 12 and N_CARDS >= 12


def hh_d():
    return [nb(dict(household_id=h['household_id'], household=h['household'], contact=h['contact'], phone=h['phone'], side=key('side', h['side']), size=h['size'], rsvp=key('rsvp', h['rsvp']),
                    list_ab=key('listab', h['list_ab']))) for h in HHS]


def guests_d():
    out = []
    first = next(g for g in GS if g['table'] and g['dietary'] and g['meal'])
    for g in sorted(GS, key=lambda g_: g_ is not first):
        out.append(nb(dict(guest_id=g['guest_id'], guest=g['guest'], household_id=g['household_id'], household=g['household'], side=key('side', g['side']), tier=key('tier', g['tier']),
                           list_ab=key('listab', g['list_ab']), age_group=key('age', g['age_group']), rsvp=key('rsvp', g['rsvp']), meal=key('meal', g['meal']) if g['meal'] else '',
                           dietary=key('dietary', g['dietary']) if g['dietary'] else '', table=key('table', g['table']) if g['table'] else '')))
    return out


def seating_d(): return [dict(table_id=key('table', t['table_id']), table_name=t['table_name'], capacity=t['capacity'], kind=key('tkind', t['kind']), reserved=t['reserved']) for t in TBS]


# rule dates: the first wishes were noted soon after the engagement, the latest a few days ago
RD = [272, 266, 241, 214, 187, 160, 133, 106, 84, 61, 40, 22, 9, 2]
def rules_d():
    return [dict(rule_id=r['rule_id'], kind=key('rkind', r['kind']), guest_a=r['guest_a'], guest_b=r['guest_b'], reason=key('reason', r['reason']), agreed_on=ago(RD[i])) for i, r in enumerate(RULES)]


SPACE = [('Venue floor area', 270, 'Floor plan of the room, your measure, edit'), ('Dance floor', 36, 'Square metres of the dance floor from the plan, edit'),
         ('Buffet area', 20, 'Food stations and queue space, edit'), ('Stage and band', 12, 'Band or DJ set-up, edit'), ('Bar and cake tables', 14, 'Bar, cake and gift tables, edit'),
         ('Walkways and exits', 30, 'Aisles and exits kept clear, your own number'), ('Area per guest, minimum', 1.1, 'Your own minimum square metres per seated guest'),
         ('Share of guests dancing', 0.6, 'Share of guests on the floor at once, your estimate')]
def space_d(): return [dict(item=key('sitem', i), value=v_, note=n) for i, v_, n in SPACE]
def tsizes_d(): return [dict(size=key('tsize', s)) for s in TSIZES]


SC = [(0, False, 0), (0.25, False, 0), (0.5, False, 0), (0.8, False, 0), (0.9, False, 0), (1.0, False, 0), (0.8, False, 6), (0.8, False, 10), (0.7, False, 0), (1.0, True, 0), (1.0, True, 4), (0.8, False, -10)]
def scen_d(): return [dict(scenario=key('scen', s), yes_rate=SC[i][0], include_no=SC[i][1], add_guests=SC[i][2]) for i, s in enumerate(SCENS)]
def tid_d(col='table'): return [{col: key('table', t)} for t in TABLE_IDS]
def ranks(n): return [dict(no=i + 1) for i in range(n)]


def rentals_d():
    # item, basis, pieces each, spare share, unit cost, ordered, order by (days before the wedding)
    R_ = [('Chairs', 'Per seat', 1, 0.03, 2.2, 120, 70), ('Round tables', 'Per table', 1, 0.0, 14.0, 13, 70), ('Table linens', 'Per table', 1, 0.10, 9.5, 14, 63), ('Napkins', 'Per seat', 1, 0.10, 0.6, 120, 63),
          ('Dinner plates', 'Per guest', 1, 0.05, 0.8, 100, 56), ('Dessert plates', 'Per guest', 1, 0.05, 0.6, 0, 56), ('Water glasses', 'Per guest', 1, 0.08, 0.5, 130, 49), ('Wine glasses', 'Per guest', 2, 0.08, 0.7, 0, 49),
          ('Cutlery sets', 'Per guest', 1, 0.05, 1.1, 110, 56), ('Centerpiece stands', 'Per table', 1, 0.0, 3.5, 13, 42), ('Place card holders', 'Per guest', 1, 0.10, 0.4, 0, 35), ('Table number stands', 'Fixed', 14, 0.0, 2.8, 14, 35)]
    return [dict(item=key('ritem', i), basis=key('rbasis', b), per_unit=pu, spare_pct=sp, unit_cost=uc, ordered=o, order_by=iso(WD - day(d))) for i, b, pu, sp, uc, o, d in R_]


def headtable_d(): return [dict(seat=i + 1) for i in range(10)]
def signoff_d(): return [dict(check=c) for c in SIGN]
SIGN = ['Yes guests without a seat', 'Seat rule conflicts', 'Tables over capacity', 'Households split across tables', 'Yes guests without a meal at a table', 'Rental items still to order', 'Head table seats over', 'Place cards to print']
