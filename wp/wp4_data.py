"""Wedding suite part 4: demo rows from wp_core and the small reference rows the timeline workbook adds."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wp4_lists import *

ST = story()
TEAM = {t['team_id']: t for t in team}
P1_PHONE = TEAM['WP-01']['phone']; P2_PHONE = TEAM['WP-02']['phone']
VEND = {x['vendor_id']: x for x in vendor_rows()}
VPHONE = {x['vendor']: x['phone'] for x in vendor_rows()}


def nb(d): return {k: v_ for k, v_ in d.items() if v_ not in ('', None)}


def team_d():
    return [dict(team_id=t['team_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), phone=t['phone'], email=t['email']) for t in team]


# task title word -> vendor the task is about (so a message can go to that vendor)
VMAP = [('invitation files to the printer', 'Stationery printer'), ('printing date for reply cards', 'Stationery printer'), ('wedding day programs', 'Stationery printer'), ('order of service', 'Stationery printer'),
        ('place cards', 'Stationery printer'), ('final stationery balance', 'Stationery printer'), ('Post the invitations', 'Stationery printer'), ('room block', 'Hotel room block'),
        ('florist instalment', 'Florist'), ('Florist', 'Florist'), ('tailor', 'Tailor'), ('first fitting', 'Attire shop'), ('Second outfit fitting', 'Attire shop'), ('Final fitting', 'Attire shop'),
        ('attire shop', 'Attire shop'), ('wedding party outfits', 'Attire shop'), ('caterer', 'Caterer'), ('menu tasting', 'Caterer'), ('officiant', 'Officiant'), ('ceremony layout', 'Venue'),
        ('venue instalment', 'Venue'), ('venue one last time', 'Venue'), ('Rehearsal at the venue', 'Venue'), ('band or DJ', 'Band or DJ'), ('videographer', 'Videographer'), ('transport', 'Transport'),
        ('hair and makeup', 'Hair and makeup'), ('rental', 'Rentals'), ('Photographer', 'Photographer'), ('photographer', 'Photographer'), ('cake baker', 'Cake baker')]


def vendor_of(title):
    for w, vn in VMAP:
        if w in title: return vn
    return ''


AREA_FIX = {'Music': 'Vendors', 'After': 'Day-of'}   # the generator uses two areas the shared list does not have


def tasks_d():
    out = []
    for t in task_rows():
        vn = vendor_of(t['title'])
        out.append(nb(dict(task_id=t['task_id'], title=t['title'], area=key('area', AREA_FIX.get(t['area'], t['area'])), when=key('when', t['when']), due_date=t['due_date'], owner=key('owner', t['owner']), owner_id=t['owner_id'],
                           vendor=key('vname', vn) if vn else '', vphone=VPHONE[vn] if vn else '', status=key('tstatus', t['status']), done_date=t['done_date'], critical=bool(t['critical']))))
    return out


WT_LEAD = {'Local wedding': (12, 'The standard plan: 140 tasks from 12 months out'), 'Destination wedding': (15, 'Guests book travel early: start sooner, no DIY'),
           'Small plus a party': (6, 'A small ceremony, then a party: fewer paper and event tasks'), 'Multi-event wedding': (14, 'More events, more helpers: start sooner'),
           'Home or garden wedding': (9, 'No venue hunt, more rentals and decor')}
def wtypes_d(): return [dict(type=key('wtype', k), lead_months=a, note=b) for k, (a, b) in WT_LEAD.items()]


# area -> (local, destination, small, multi, home, lead days, hours per task)
FIT = {'Budget': (1, 1, 1, 1, 1, 3, 1.5), 'Guests': (1, 1, 1, 1, 1, 14, 2.5), 'Vendors': (1, 1, 1, 1, 1, 21, 3.0), 'Venue': (1, 1, 1, 1, 0, 14, 2.5), 'Attire': (1, 1, 1, 1, 1, 42, 3.0),
       'Ceremony': (1, 1, 1, 1, 1, 14, 2.0), 'Paper': (1, 1, 0, 1, 0, 28, 2.5), 'Events': (1, 1, 0, 1, 0, 21, 3.5), 'Honeymoon': (1, 1, 1, 1, 1, 30, 2.0), 'Paperwork': (1, 1, 1, 1, 1, 21, 1.5),
       'Day-of': (1, 1, 1, 1, 1, 7, 2.0), 'Decor and DIY': (1, 0, 0, 1, 1, 28, 4.0), 'Gifts and thanks': (1, 1, 1, 1, 1, 7, 1.5)}
assert list(FIT) == TASK_AREAS
def fit_d(): return [dict(area=key('area', a), local=bool(f[0]), destination=bool(f[1]), small=bool(f[2]), multi=bool(f[3]), home=bool(f[4]), lead_days=f[5], hours=f[6]) for a, f in FIT.items()]

HELPER = {'Budget': 'Parent of partner 1', 'Guests': 'Wedding party lead', 'Vendors': 'Day-of coordinator', 'Venue': 'Parent of partner 2', 'Attire': 'Wedding party lead', 'Ceremony': 'Parent of partner 2',
          'Paper': 'Friend or relative', 'Events': 'Wedding party lead', 'Honeymoon': 'Partner 2', 'Paperwork': 'Partner 1', 'Day-of': 'Day-of coordinator', 'Decor and DIY': 'Friend or relative',
          'Gifts and thanks': 'Parent of partner 1'}
def areasum_d(): return [dict(area=key('area', a), helper=key('owner', HELPER[a])) for a in TASK_AREAS]


def mprog_d(): return [dict(when=key('when', w)) for w in WHEN]
def workload_d(): return [dict(owner=key('owner', o)) for o in OWNERS]
def slots(n): return [dict(seqno=i) for i in range(1, n + 1)]
def key_d(): return [dict(no=i) for i in range(1, 13)]
def compress_d(): return [dict(task_id=t['task_id']) for t in task_rows()]
def doneby_d(): return [dict(month=iso(add_months(month_start(0), i))) for i in range(-9, 9)]


def schedule_d():
    return [dict(pay_id=r['pay_id'], vendor=key('vname', r['vendor']), kind=key('paykind', r['kind']), due_date=r['due_date'], amount_due=r['amount_due'], status=key('paystatus', r['status']),
                 phone=VEND[r['vendor_id']]['phone']) for r in payment_schedule_rows()]


def contracts_d():
    return [nb(dict(contract_id=r['contract_id'], vendor=key('vname', r['vendor']), kind=key('ckind', r['kind']), detail=r['detail'], item_date=r['item_date'])) for r in contract_rows()]


def party_d():
    import datetime as _dt
    out = []
    for i, p in enumerate(party_rows()):
        d = _dt.date.fromisoformat(str(p['fitting_date'])[:10])
        if i % 3 == 0:
            d = d - _dt.timedelta(days=170 + 9 * i)
        out.append(dict(party_id=p['party_id'], person=p['person'], role=key('prole', p['role']), fitting_date=d.isoformat(), attire_status=key('attire', p['attire_status'])))
    return out


if __name__ == '__main__':
    for f in (team_d, tasks_d, wtypes_d, fit_d, areasum_d, mprog_d, workload_d, key_d, compress_d, doneby_d, schedule_d, contracts_d, party_d):
        print(f.__name__, len(f()))
    import collections
    print(collections.Counter(t.get('vendor') for t in tasks_d()))
    print([ (t['task_id'], t['title'][:30], t['vendor']) for t in tasks_d() if t.get('vendor') and t['status']!='done'][:60])
