"""Home Management suite part 4: demo rows from ho_core (maintenance, log, repairs, appliances, contacts) and the typed rows of the calculated tables."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ho4_lists import *
import datetime as _dt

ST = story()
T0 = TODAY
def D_(s): return _dt.date.fromisoformat(s)
def plus(s, n): return iso(D_(s) + _dt.timedelta(days=n))

MNT = maintenance_rows(); MLOG = maintenance_log_rows(); REP = repair_rows(); CON = contact_rows(); INV = {i['item_id']: i for i in inventory_rows()}
YEARS = [Y - 4, Y - 3, Y - 2, Y - 1, Y]

# three trade tasks fall due inside the next 60 days (set last done so the next due falls there); the log row of the task moves with it
LAST_OVERRIDE = {'MT-11': ago(1825 - 38), 'MT-31': ago(730 - 27), 'MT-14': ago(730 - 51)}
SUMMER = {'MT-17', 'MT-41', 'MT-38'}                      # three tasks belong to summer so every season has tasks
SAFETY = {'MT-06', 'MT-07', 'MT-08', 'MT-11', 'MT-35', 'MT-46', 'MT-47'}
MINUTES = dict(zip(['MT-%02d' % i for i in range(1, 51)], [15, 0, 30, 10, 0, 10, 20, 10, 15, 20, 0, 90, 20, 0, 60, 45, 90, 15, 45, 120, 30, 15, 20, 20, 30, 25, 10, 60, 10, 60,
                                                          0, 15, 20, 20, 10, 45, 15, 60, 20, 30, 30, 15, 60, 0, 90, 30, 10, 30, 15, 0]))


PERSON_OF = {'HO-01': 'Adult 1', 'HO-02': 'Adult 2', 'HO-03': 'Child 1', 'HO-04': 'Child 2'}
PERSON_OF = {k: key('person', v) for k, v in PERSON_OF.items()}


def team_d():
    nd = {'HO-07': (ahead(6), '10:00', '12:00'), 'HO-08': (ahead(12), '14:00', '16:00'), 'HO-09': (ahead(9), '09:00', '12:00'), 'HO-02': (ahead(9), '09:00', '12:00'),
          'HO-05': (ahead(6), '10:00', '12:00'), 'HO-11': (ahead(15), '', ''), 'HO-14': (ahead(6), '10:00', ''), 'HO-15': (ahead(8), '13:00', '17:00')}
    out = []
    for t in team:
        n = nd.get(t['member_id'], ('', '', ''))
        out.append(dict(member_id=t['member_id'], name=t['name'], role=key('role', t['role']), group=key('tgroup', t['group']), phone=t['phone'], note=t['note'], start=t['start'],
                        first_name=first_name(t['name']), person=PERSON_OF.get(t['member_id'], ''), next_date=n[0], at_time=n[1], end_time=n[2]))
    return out


def maintenance_d():
    out = []
    for m in MNT:
        tid = m['task_id']
        season = 'Summer' if tid in SUMMER else m['season']
        out.append(dict(task_id=tid, task=m['task'], area=key('area', m['area']), season=key('season', season), interval_days=m['interval_days'], assigned=key('mwho', m['assigned']),
                        typical_cost=m['typical_cost'], trade=(key('trade', m['trade']) if m['trade'] else ''), last_done=LAST_OVERRIDE.get(tid, m['last_done']),
                        minutes=MINUTES[tid], safety=tid in SAFETY))
    return out


def log_d():
    moved = {k: False for k in LAST_OVERRIDE}
    out = []
    for l in MLOG:
        done = l['done']
        if l['task_id'] in LAST_OVERRIDE and l['task_id'] != 'MT-11':
            done = LAST_OVERRIDE[l['task_id']]
        cost = l['cost']
        if l['task_id'] == 'MT-22' and not cost: cost = round(2.2 + (len(out) * 7 % 9) * 0.3, 2)
        out.append(dict(log_id=l['log_id'], task_id=l['task_id'], task=l['task'], done=done, who=key('mwho', l['who']), cost=cost, note=l['note']))
    return out


def repairs_d():
    return [dict(repair_id=r['repair_id'], date=r['date'], room=key('room', r['room']), issue=r['issue'], trade=key('trade', r['trade']), quote=r['quote'], cost=r['cost'],
                 status=key('rstatus', r['status']), fixed_on=r['fixed_on'], warranty_used=bool(r['warranty_used']), item_id=r['item_id']) for r in REP]


APPL = [('IV-012', 'MT-02'), ('IV-004', 'MT-04'), ('IV-047', 'MT-26'), ('IV-074', 'MT-30'), ('IV-062', 'MT-24'), ('IV-064', 'MT-22'), ('IV-058', 'MT-25'), ('IV-052', 'MT-28'),
        ('IV-063', 'MT-27'), ('IV-013', 'MT-29'), ('IV-084', 'MT-16'), ('IV-017', 'MT-17'), ('IV-060', 'MT-15'), ('IV-070', 'MT-19'), ('IV-005', 'MT-18'), ('IV-071', 'MT-06'),
        ('IV-061', 'MT-03'), ('IV-041', 'MT-10'), ('IV-082', 'MT-47'), ('IV-067', 'MT-33'), ('IV-007', 'MT-34'), ('IV-092', 'MT-20')]
assert len({t for _, t in APPL}) == 22


def appliances_d():
    return [dict(item_id=i, item=INV[i]['item'], room=key('room', INV[i]['room']), purchase_date=INV[i]['purchase_date'], warranty_end=INV[i]['warranty_end'], service_task_id=t) for i, t in APPL]


def contacts_d():
    out = []
    for c in CON:
        tr = c['trade']
        if c['contact_id'] == 'CT-17': tr = 'Handyman'
        if tr.startswith('Cousin'): tr = 'Cousin with a spare key'
        out.append(dict(contact_id=c['contact_id'], name=c['name'], kind=key('ckind', c['kind']), trade=key('ctrade', tr), phone=c['phone'], email=c['email'], last_used=c['last_used'],
                        cost_last=c['cost_last'], would_use_again=bool(c['would_use_again']), member_id=c['member_id'], first_name=first_name(c['name'])))
    return out


def _ml(tid): return next(m['last_done'] for m in maintenance_d() if m['task_id'] == tid)


def consumables_d():
    spec = [('Furnace or boiler filter', 'Filter 20x25', 'Utility room', 90, 'MT-01', 1, 'Utility cupboard, top shelf'),
            ('Water filter cartridge', 'Cartridge size B', 'Kitchen tap', 90, 'MT-27', 0, 'Pantry, bottom shelf'),
            ('Vacuum cleaner bags', 'Bag type 4', 'Utility room', 90, 'MT-29', 2, 'Under the stairs'),
            ('Smoke alarm batteries', 'AA, pack of 4', 'Hallway and landing', 182, 'MT-07', 0, 'Drawer in the hallway'),
            ('Thermostat batteries', 'AAA, pack of 2', 'Hallway', 365, 'MT-04', 2, 'Drawer in the hallway'),
            ('Descaler for the machines', 'Sachets, pack of 6', 'Utility room and kitchen', 90, 'MT-23', 1, 'Utility cupboard, middle shelf'),
            ('Torch batteries', 'D cell, pack of 2', 'Under the stairs', 182, 'MT-47', 3, 'Under the stairs'),
            ('Bathroom sealant', 'White, 300 ml', 'Bathroom', 730, 'MT-36', 1, 'Garage shelf'),
            ('Grout cleaner', 'Spray, 500 ml', 'Bathroom', 182, 'MT-38', 1, 'Bathroom cupboard'),
            ('Floor and worktop oil', 'Bottle, 500 ml', 'Kitchen and hallway', 365, 'MT-45', 0, 'Garage shelf'),
            ('Lawn mower oil and plug', 'Service kit', 'Garden shed', 365, 'MT-16', 1, 'Garage shelf'),
            ('Door hinge and lock oil', 'Spray, 150 ml', 'Doors and windows', 365, 'MT-39', 1, 'Garage shelf')]
    return [dict(item=a, code=b, where_used=c, interval_days=d, last_changed=_ml(e), units=f, task_id=e, stored=g) for a, b, c, d, e, f, g in spec]


def schedule_d(): return [dict(rank=i) for i in range(1, 51)]
def overdue_d(): return [dict(rank=i) for i in range(1, 21)]
def next12_d(): return [dict(task_id=m['task_id']) for m in MNT]
def month_load_d(): return [dict(mk=i, ahead=key('ahead12', AHEAD[i - 1])) for i in range(1, 13)]
def season_d(): return [dict(season=key('season', s)) for s in SEASONS]
def reorder_d(): return [dict(item=c['item']) for c in consumables_d()]
def app_service_d(): return [dict(item_id=i) for i, _ in APPL]
def svc_overdue_d(): return [dict(rank=i) for i in range(1, 16)]
def open_repairs_d(): return [dict(rank=i) for i in range(1, 16)]
def room_year_d(): return [dict(room=key('room', r), year=y) for r in ROOMS for y in YEARS]
def repeat_d(): return [dict(room=key('room', r)) for r in ROOMS]
def trades_used_d(): return [dict(trade=key('trade', t), year=y) for t in TRADES for y in YEARS]
def cost_year_d(): return [dict(year=y) for y in range(Y - 4, Y + 1)]


if __name__ == '__main__':
    for f in (team_d, maintenance_d, log_d, repairs_d, appliances_d, contacts_d, consumables_d, schedule_d, overdue_d, next12_d, month_load_d, season_d, reorder_d, app_service_d,
              svc_overdue_d, open_repairs_d, room_year_d, repeat_d, trades_used_d, cost_year_d): print(f.__name__, len(f()))
