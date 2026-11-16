"""Wedding suite part 7: demo rows from wp_core (events, lines, honeymoon, party) and the aggregated rows built from the full generator output."""
import sys, os, collections; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wp7_lists import *

ST = story()
dd = to_date
TEAM = {t['team_id']: t for t in team}
EVS = event_rows(); EVD = {e['event']: e for e in EVS}
LNS = event_line_rows()
HHS = household_rows()
VEND = {x['vendor_id']: x for x in vendor_rows()}
WD = WEDDING_DAY


def nb(d): return {k: v_ for k, v_ in d.items() if v_ not in ('', None)}


# ---- phones taken from the team (never invented)
P1_PHONE = TEAM['WP-01']['phone']; P2_PHONE = TEAM['WP-02']['phone']; PAR1_PHONE = TEAM['WP-03']['phone']; PAR2_PHONE = TEAM['WP-04']['phone']
LEAD1_PHONE = TEAM['WP-07']['phone']; LEAD2_PHONE = TEAM['WP-08']['phone']; FRIEND_PHONE = TEAM['WP-09']['phone']; VENUE_PHONE = TEAM['WP-11']['phone']
HOTEL_PHONE = VEND['VD-16']['phone']
HOST_PHONE = {'Engagement party': PAR1_PHONE, 'Shower': FRIEND_PHONE, 'Weekend away, partner 1 friends': LEAD1_PHONE, 'Weekend away, partner 2 friends': LEAD2_PHONE,
              'Rehearsal dinner': P1_PHONE, 'Ceremony': P1_PHONE, 'Reception': P1_PHONE, 'Farewell brunch': PAR2_PHONE}

# ---- guests from the households: travel guests and the guests staying in the room block
TRAVEL_GUESTS = sum(h['size'] for h in HHS if h['region'] != 'Local')
STAY_BEFORE = sum(h['size'] for h in HHS if h['arrival'] == iso(WD - dt.timedelta(days=1)))
STAY_ONDAY = sum(h['size'] for h in HHS if h['arrival'] == iso(WD))
ROOMS_HELD = sum(r['rooms_held'] for r in roomblock_rows())


# ---- events, lines, costs, invitees, calendar
def events_d(): return [dict(event=key('event', e['event']), date=e['date'], status=key('estatus', e['status'])) for e in EVS]


PLANNED = {'EL-15': 310, 'EL-17': 20, 'EL-18': 220, 'EL-19': 70, 'EL-20': 40}
ITEM_OF = {'EV-06': 'Included in the venue contract', 'EV-07': 'Included in the caterer contract'}


def lines_d():
    out = []
    for r in LNS:
        out.append(dict(line_id=r['line_id'], event_id=r['event_id'], event=key('event', r['event']), item=key('item', r['item']), planned=PLANNED.get(r['line_id'], r['amount']), amount=r['amount'], paid=r['paid']))
    for n, e in enumerate([EVD['Ceremony'], EVD['Reception']]):
        out.append(dict(line_id='EL-%02d' % (21 + n), event_id=e['event_id'], event=key('event', e['event']), item=key('item', ITEM_OF[e['event_id']]), planned=0, amount=0, paid=0))
    return out


def ecosts_d(): return [dict(event=key('event', e['event'])) for e in EVS]
def invitees_d(): return [nb(dict(event=key('event', e['event']), start=e['start'], invitees=e['invitees'])) for e in EVS]


def calendar_d():
    m = dt.date(ENGAGED_ON.year, ENGAGED_ON.month, 1); out = []
    for _ in range(24):
        out.append(dict(month=iso(m))); m = add_months(m, 1)
    return out


def nights_d():
    g = {'Night before': STAY_BEFORE, 'Wedding night': STAY_BEFORE + STAY_ONDAY, 'Night after': STAY_ONDAY, 'Two nights before': 0, 'Two nights after': 0}
    return [dict(night=key('night', n), guests=g[n]) for n in ['Night before', 'Wedding night', 'Night after', 'Two nights before', 'Two nights after']]


def combined_d(): return [dict(item=key('citem', c_)) for c_ in CITEM]


# ---- honeymoon
HM_ST = {'HM-01': 'Quote received', 'HM-02': 'Quote received', 'HM-03': 'Idea', 'HM-04': 'Idea', 'HM-05': 'Idea', 'HM-06': 'Idea', 'HM-07': 'Idea',
         'HM-08': 'Quote received', 'HM-09': 'Booked', 'HM-10': 'Idea', 'HM-11': 'Idea', 'HM-12': 'Idea', 'HM-13': 'Booked', 'HM-14': 'Idea'}
HM_PAID = {'HM-13': iso(TODAY - dt.timedelta(days=12))}
HMS = honeymoon_rows()
HFS = honeymoon_fund_rows()


def hm_d():
    return [nb(dict(phone=fake_phone(41 + n), hm_id=r['hm_id'], option=key('hoption', r['option']), kind=key('hkind', r['kind']), description=r['description'], amount=r['amount'], days=r['days'], due_date=r['due_date'],
                    paid_on=HM_PAID.get(r['hm_id'], ''), status=key('hmstatus', HM_ST[r['hm_id']]))) for n, r in enumerate(HMS)]


def hf_d(): return [dict(hf_id=r['hf_id'], date=r['date'], month=r['month'], source=key('hsource', r['source']), amount=r['amount'], status=key('fstatus', r['status'])) for r in HFS]
def hcomp_d(): return [dict(kind=key('hkind', k_)) for k_ in HONEY_KINDS]


def hfm_d():
    first = dd(min(r['month'] for r in HFS)); last = dd(max(r['month'] for r in HFS)); m = first; out = []
    while m <= last:
        out.append(dict(month=iso(m))); m = add_months(m, 1)
    return out


def htime_d(): return [dict(hm_id=r['hm_id']) for r in HMS]


# ---- quotes and destination quotes
QS = quote_rows()
def quotes_d():
    return [dict(quote_id=q['quote_id'], vendor_id=q['vendor_id'], vendor=q['vendor'], category=key('category', q['category']), option=q['option'], base_price=q['base_price'], status=q['status'],
                 phone=VEND[q['vendor_id']]['phone']) for q in QS]


def dest_d():
    by = collections.defaultdict(list)
    for q in QS: by[q['vendor_id']].append(q)
    out = []
    for n, vid in enumerate(sorted(by), 1):
        qs = by[vid]
        pick = next((q for q in qs if q['chosen']), None) or next((q for q in qs if q['status'] == 'Shortlisted'), None) or min((q for q in qs if q['status'] != 'Declined'), key=lambda q: q['base_price'])
        out.append(dict(dest_id='DQ-%02d' % n, quote_id=pick['quote_id'], category=key('category', pick['category'])))
    return out


# ---- party travel
PTY = party_rows()
FLIGHTS = [640, 480, 560, 720, 410, 590, 650, 520, 380, 450, 300, 340, 280, 360]
NIGHTS_P = [3, 3, 4, 3, 2, 3, 4, 3, 2, 3, 2, 2, 2, 2]
HELPED = [200, 240, 60, 360, 205, 180, 100, 0, 0, 225, 0, 0, 0, 0]
PEVENT = ['Weekend away, partner 1 friends'] * 5 + ['Weekend away, partner 2 friends'] * 5 + ['Rehearsal dinner'] * 4


def party_d():
    return [dict(party_id=p['party_id'], person=key('person', p['person']), role=key('prole', p['role']), event=key('event', PEVENT[i]), flights=FLIGHTS[i], nights=NIGHTS_P[i], helped=HELPED[i], phone=p['phone'])
            for i, p in enumerate(PTY)]


# ---- paperwork (short names, the status of one open step moved to In progress so the three statuses show)
PW_SHORT = {'PW-01': 'Ask the office about the lead time', 'PW-02': 'Book the marriage paperwork appointment', 'PW-03': 'Gather the documents the office asks for', 'PW-04': 'Complete the marriage paperwork steps',
            'PW-05': 'Ask the officiant about the signing page', 'PW-06': 'Order copies of the marriage record', 'PW-07': 'Decide about a name change', 'PW-08': 'Update identity documents (optional)',
            'PW-09': 'Update bank and card accounts (optional)', 'PW-10': 'Update work records (optional)', 'PW-11': 'Update insurance and tax records (optional)', 'PW-12': 'Update home and utility records (optional)',
            'PW-13': 'Review insurance and benefits (optional)', 'PW-14': 'Review wills and beneficiaries (optional)'}


def paper_d():
    out = []
    for r in paperwork_rows():
        st = 'In progress' if r['item_id'] == 'PW-03' else r['status']
        out.append(dict(item_id=r['item_id'], item=PW_SHORT[r['item_id']], kind=key('pkind', r['kind']), due_date=r['due_date'], status=key('tstatus', st), owner=r['owner']))
    out.sort(key=lambda x: x['item_id'] in ('PW-01', 'PW-07'))
    return out


# ---- two tracks
TRK = {  # line: (category 1, category 2, scales with guests, share of the big-wedding cost kept in the small track)
    'Venue': ('Venue', '', False, 1.0), 'Food and drink': ('Catering and bar', '', True, 1.0), 'Photo and video': ('Photo and video', '', False, 0.55), 'Music': ('Music', '', False, 0.35),
    'Flowers and decor': ('Flowers and decor', '', False, 0.40), 'Attire and alterations': ('Attire and alterations', 'Hair and makeup', False, 1.0), 'Stationery and postage': ('Stationery and postage', '', True, 0.9),
    'Ceremony and officiant': ('Ceremony and officiant', '', False, 1.0), 'Rentals and cake': ('Rentals', 'Cake and favors', True, 0.8), 'Other events': ('Other events', '', False, 0.40),
    'Planner and travel': ('Planner and coordinator', 'Transport and lodging', False, 0.5), 'Tips, fees and reserve': ('Tips and fees', 'Reserve', False, 0.5)}


def tracks_d():
    out = []
    for ln in TLINES:
        c1, c2, sc, sh = TRK[ln]
        out.append(nb(dict(line=key('tline', ln), cat1=key('category', c1), cat2=key('category', c2) if c2 else '', scales=sc, share=sh)))
    return out


TIN = [('Big wedding guests', 118, 'Your forecast from the guest list'), ('Ceremony guests', 30, 'Family and the closest friends'), ('Party guests', 60, 'A casual party after the honeymoon'),
       ('Ceremony venue cost', 1200, 'A small room for the ceremony'), ('Party venue cost', 1400, 'A hall for the party'), ('Ceremony food per guest', 75, 'A seated meal'),
       ('Party food per guest', 34, 'Food and drink for the party'), ('Events in the small track', 2, 'The ceremony and the party')]
def tin_d(): return [dict(item=key('tinput', a), value=b, note=c_) for a, b, c_ in TIN]


def budget_d(): return [dict(line_id=b['line_id'], category=key('category', b['category']), planned=b['planned'], committed=b['committed'], paid=b['paid']) for b in budget_rows()]
def scen_d(): return [dict(scenario=key('hscen', s_)) for s_ in HSCEN]


if __name__ == '__main__':
    print('travel guests', TRAVEL_GUESTS, 'stay', STAY_BEFORE, STAY_ONDAY, 'rooms held', ROOMS_HELD)
    for f in (events_d, lines_d, calendar_d, nights_d, hm_d, hfm_d, dest_d, party_d, paper_d, tracks_d): print(f.__name__, len(f()))
