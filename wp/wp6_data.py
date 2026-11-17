"""Wedding suite part 6: demo rows from wp_core (party, run of show, team, vendors, tips) and the rows of the planning tables built from them."""
import sys, os, collections; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wp6_lists import *

ST = story()
dd = to_date
WD = WEDDING_DAY
TEAM = {t['team_id']: t for t in team}
VEND = {x['vendor_id']: x for x in vendor_rows()}
RUN = run_rows()
RUNID = {r['step_id']: r for r in RUN}
PTY = party_rows()
EVD = {e['event']: e for e in event_rows()}
REHEARSAL = EVD['Rehearsal dinner']
SHIP, MARGIN = 21, 7                       # the settings' defaults: used here only to build the demo tasks


def nb(d): return {k: v_ for k, v_ in d.items() if v_ not in ('', None)}


# ---------------------------------------------------------------- team
def team_d(): return [dict(team_id=t['team_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), phone=t['phone'], email=t['email']) for t in team]


# ---------------------------------------------------------------- wedding party (fittings, one outfit ready, two outfits paid by a parent: your own edits of the demo)
FIT = {'WPY-03': ahead(28), 'WPY-04': ago(20), 'WPY-06': ahead(9), 'WPY-08': ahead(22), 'WPY-09': ago(34), 'WPY-12': ago(12)}
ATT = {'WPY-09': 'Ready'}
PAY = {'WPY-13': 'Parent', 'WPY-14': 'Parent', 'WPY-05': 'Sibling', 'WPY-10': 'Friend'}
ARR = {'WPY-01': 'RS-01', 'WPY-06': 'RS-01', 'WPY-02': 'RS-10', 'WPY-03': 'RS-10', 'WPY-04': 'RS-10', 'WPY-05': 'RS-10', 'WPY-07': 'RS-10', 'WPY-08': 'RS-10', 'WPY-09': 'RS-13', 'WPY-10': 'RS-13',
       'WPY-11': 'RS-03', 'WPY-12': 'RS-13', 'WPY-13': 'RS-06', 'WPY-14': 'RS-13'}


def party_d():
    out = []
    for p in PTY:
        pid = p['party_id']
        out.append(nb(dict(party_id=pid, person=key('person', p['person']), guest_id=p['guest_id'], side=key('pside', p['side']), role=key('prole', p['role']), task='' if pid == 'WPY-11' else p['task'],
                           attire_status=key('attire', ATT.get(pid, p['attire_status'])), outfit_cost=p['outfit_cost'], paid_by=key('paidby', PAY.get(pid, p['paid_by'])),
                           fitting_date=FIT.get(pid, p['fitting_date']), alteration_weeks=p['alteration_weeks'], arrive_step=ARR[pid], phone=p['phone'])))
    return out


def last_order(p):
    fit = dd(FIT.get(p['party_id'], p['fitting_date'])); latest = WD - dt.timedelta(days=7 * p['alteration_weeks'] + MARGIN)
    return min(fit, latest) - dt.timedelta(days=SHIP)


# ---------------------------------------------------------------- run of show
LEAD = {'RS-01': 'Priya Nair', 'RS-02': 'Yuki Tanaka', 'RS-03': 'Maren Lindqvist', 'RS-05': 'Ingrid Solberg', 'RS-06': 'Zainab Okafor', 'RS-07': 'Ingrid Solberg', 'RS-08': 'Yuki Tanaka',
        'RS-09': 'Ingrid Solberg', 'RS-10': 'Mateo Moreno', 'RS-11': 'Yuki Tanaka', 'RS-12': 'Priya Nair', 'RS-14': 'Jonas Lindqvist', 'RS-15': 'Ingrid Solberg', 'RS-16': 'Ingrid Solberg',
        'RS-17': 'Chidi Okafor', 'RS-18': 'Ingrid Solberg', 'RS-20': 'Ingrid Solberg', 'RS-21': 'Ingrid Solberg', 'RS-22': 'Priya Nair', 'RS-24': 'Ingrid Solberg', 'RS-25': 'Ingrid Solberg',
        'RS-26': 'Priya Nair', 'RS-27': 'Mateo Moreno', 'RS-28': 'Yuki Tanaka', 'RS-29': 'Mateo Moreno', 'RS-30': 'Ingrid Solberg'}
# four steps have no person yet (RS-04, RS-13, RS-19, RS-23): the demo story of the "steps with no person" figures


def run_d():
    out = []
    for r in RUN:
        out.append(nb(dict(step_id=r['step_id'], date=r['date'], start=r['start'], minutes=10 if r['step_id'] == 'RS-30' else r['minutes'], buffer_min=r['buffer_min'], block=key('block', r['block']), what=r['what'], who=key('who', r['who']),
                           place=key('place', r['place']), vendor=key('vname', VEND[r['vendor_id']]['vendor']) if r['vendor_id'] else '', lead=key('helper', LEAD[r['step_id']]) if r['step_id'] in LEAD else '')))
    return out


# ---------------------------------------------------------------- vendors
DAYROLE = {'VD-01': 'Opens the doors, hands back the keys', 'VD-02': 'Sets up the kitchen, serves dinner', 'VD-03': 'Details, portraits, family photos, the dance floor', 'VD-04': 'Not booked yet: would film the ceremony',
           'VD-05': 'Sound check, ceremony music, dancing', 'VD-06': 'Flowers to the hotel and the venue', 'VD-07': 'Leads the ceremony and the signing', 'VD-08': 'Delivers the cake before dinner',
           'VD-09': 'Hair and makeup at the hotel', 'VD-10': 'Outfits picked up before the day', 'VD-11': 'Not booked yet: on call for last fixes', 'VD-12': 'Programs delivered before the day',
           'VD-13': 'Delivers, sets up and counts the rentals', 'VD-14': 'Party shuttle and guest shuttle', 'VD-15': 'Runs the day so you do not have to', 'VD-16': 'Holds the rooms and the late check-out'}


def vendors_d():
    return [dict(vendor_id=x['vendor_id'], vendor=key('vname', x['vendor']), category=x['category'], contact=x['contact'], phone=x['phone'], day_role=DAYROLE[x['vendor_id']]) for x in vendor_rows()]


def hours_d():
    rows = [('Vendors may enter', '09:30', 'From your venue contract: check the exact time'), ('Guests may enter', '15:30', 'Doors and welcome drinks'), ('Bar closes', '22:30', 'Last call is 15 minutes earlier'),
            ('Music must end', '23:00', 'Check your contract for the sound limit'), ('Venue closes', '23:30', 'Every minute after this is overtime')]
    return [dict(item=key('hitem', a), time=b, note=c_) for a, b, c_ in rows]


# ---------------------------------------------------------------- moves, who and where, pages, guest timeline
MOVES = [('RS-01', 'RS-10'), ('RS-10', 'RS-12'), ('RS-10', 'RS-13'), ('RS-02', 'RS-11'), ('RS-03', 'RS-17'), ('RS-08', 'RS-11'), ('RS-08', 'RS-17'), ('RS-02', 'RS-06'), ('RS-01', 'RS-03'),
         ('RS-26', 'RS-27'), ('RS-13', 'RS-14'), ('RS-11', 'RS-17')]
def moves_d(): return [dict(move_id='MV-%02d' % (i + 1), from_step=a, to_step=b) for i, (a, b) in enumerate(MOVES)]


def attends(g, r): return r['who'] == g or (r['who'] == 'All guests' and g in ('Couple', 'Wedding party', 'Parents'))


def where_d():
    out, n = [], 0
    for g in ('Couple', 'Wedding party', 'Parents', 'Officiant', 'Vendors'):
        for b in RUN_BLOCKS:
            if any(attends(g, r) and r['block'] == b for r in RUN):
                n += 1; out.append(dict(where_id='WH-%02d' % n, who=key('who', g), block=key('block', b)))
    return out


def pages_d():
    out, n = [], 0
    for g in RUN_WHO:
        for r in RUN:
            if attends(g, r):
                n += 1; out.append(dict(page_id='PG-%02d' % n, who=key('who', g), step_id=r['step_id']))
    return out


GUEST_STEPS = ['RS-14', 'RS-15', 'RS-18', 'RS-19', 'RS-20', 'RS-21', 'RS-22', 'RS-23', 'RS-24', 'RS-25', 'RS-26', 'RS-27']
def gtl_d(): return [dict(step_id=s_) for s_ in GUEST_STEPS]


# ---------------------------------------------------------------- duties and tips
DUTY = [('Gifts table and gift log', 'Maren Lindqvist', 'Yuki Tanaka', 'Done'), ('Cards and card box', 'Yuki Tanaka', 'Maren Lindqvist', 'Done'), ('Tip envelopes', 'Ingrid Solberg', 'Priya Nair', 'In progress'),
        ('Final payments on the day', 'Ingrid Solberg', 'Chidi Okafor', 'In progress'), ('Rentals and returns', 'Mateo Moreno', '', 'In progress'),
        ('Programs and place cards', 'Jonas Lindqvist', 'Zainab Okafor', 'Done'), ('Flowers to the hotel', 'Zainab Okafor', 'Priya Nair', 'Not started'), ('Cake box and leftovers', 'Mateo Moreno', 'Maren Lindqvist', 'Not started'),
        ('Keys and venue hand-back', 'Priya Nair', 'Mateo Moreno', 'Done'), ('Lost property', 'Zainab Okafor', '', 'Not started'), ('Gifts and cards to the car', 'Chidi Okafor', 'Yuki Tanaka', 'In progress'),
        ('Family photo list', 'Chidi Okafor', '', 'Done')]
def duties_d(): return [nb(dict(duty=key('duty', a), named=key('helper', b), backup=key('helper', c_) if c_ else '', status=key('tstatus', d_))) for a, b, c_, d_ in DUTY]


def tips_d():
    out = []
    for t in tip_rows():
        planned = 0 if t['gratuity_included'] else (round(t['pct'] * t['bill'], 2) if t['basis'] == 'Percent' else t['flat'] if t['basis'] == 'Flat amount' else 0)
        out.append(dict(vendor=key('vname', t['vendor']), handed_by=key('hander', t['handed_by']), planned=planned, envelope_ready=bool(t['envelope_ready'])))
    return out


# ---------------------------------------------------------------- planning tables keyed by a list value
def attire_s_d(): return [dict(status=key('attire', s_)) for s_ in ATTIRE_STATUS]
def fits_d(): return [dict(person=key('person', p['person'])) for p in PTY]
def load_d(): return [dict(person=key('person', p['person'])) for p in PTY]
def blocks_d(): return [dict(block=key('block', b)) for b in RUN_BLOCKS]
def overrun_d(): return [dict(block=key('block', b)) for b in RUN_BLOCKS]
def onsite_d(): return [dict(vendor=key('vname', n)) for n in VNAMES]
def paycost_d(): return [dict(paid_by=key('paidby', s_)) for s_ in PAIDBY]
def roles_d(): return [dict(role=key('prole', s_)) for s_ in PARTY_ROLES]


# ---------------------------------------------------------------- party tasks (30)
def ptasks_d():
    out, n = [], 0
    def add(person, task, due, status):
        nonlocal n; n += 1
        out.append(dict(task_id='PT-%02d' % n, person=key('person', person), task=task, due_date=iso(due) if not isinstance(due, str) else due, status=key('tstatus', status)))
    for p in PTY:
        pid = p['party_id']; st = ATT.get(pid, p['attire_status']); lo = last_order(p)
        # the outfit task
        add(p['person'], 'Order your outfit', lo, 'Done' if st != 'Not started' else ('In progress' if pid == 'WPY-10' else 'Not started'))
        # the main task
        t = p['task']
        if t.startswith('Plan the shower'): add(p['person'], t, EVD['Weekend away, partner 1 friends' if p['side'] == 'Partner 1' else 'Weekend away, partner 2 friends']['date'], 'In progress')
        elif t.startswith('Help with DIY'): add(p['person'], t, WD - dt.timedelta(days=14), 'In progress' if pid in ('WPY-03',) else 'Not started')
        elif t.startswith('Help with the order'): add(p['person'], t, WD - dt.timedelta(days=28), 'Not started')
        else: add(p['person'], t, WD, 'Not started')
    add('Rosa Silva', 'Confirm your role', ago(100), 'Done'); add('Bianca Chen', 'Confirm your role', ago(95), 'Done')
    return out


if __name__ == '__main__':
    print(len(party_d()), len(run_d()), len(where_d()), len(pages_d()), len(ptasks_d()), len(tips_d()))
    for p in PTY: print(p['party_id'], p['person'], last_order(p))
    for t in ptasks_d()[:6]: print(t)
