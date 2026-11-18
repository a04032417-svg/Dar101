"""Home Management suite part 6: demo rows from ho_core (calendar, work pattern, terms, gifts, pets, vehicles, tasks) and the typed rows of visits, pet and vehicle dates."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ho6_lists import *
import datetime as _dt

ST = story()
T0 = TODAY
def D_(s): return _dt.date.fromisoformat(s)
def plus(s, n): return iso(D_(s) + _dt.timedelta(days=n))

EV = event_rows(); SH = shift_rows(); TM = term_rows(); GF = gift_rows(); PET = pet_rows(); VEH = vehicle_rows(); PC = pet_care_rows(); VL = vehicle_log_rows(); MNT = maintenance_rows()
STORY_EV = set(ST['overlap'])


def team_d():
    return [dict(member_id=t['member_id'], name=t['name'], role=key('role', t['role']), group=t['group'], phone=t['phone'], email=t['email'], note=t['note'], start=t['start'],
                 short=first_name(t['name'])) for t in team]


def events_d():
    out, n = [], 0
    for r in EV:
        row = dict(event_id=r['event_id'], date=r['date'], end_date=r['end_date'], person=key('epeople', r['person']), kind=key('ekind', r['kind']), title=r['title'], start=r['start'], end=r['end'],
                   place=r['place'], carpool=bool(r['carpool']))
        drv = r['driver']
        if r['title'] == 'Piano lesson':
            n += 1
            if n % 6 == 0 and not (T0 - _dt.timedelta(days=42) <= D_(r['date']) <= T0 + _dt.timedelta(days=60)): drv = 'Walk or bike'; row['carpool'] = False
        if drv: row['driver'] = key('driver', drv)
        out.append(row)
    return out


def shifts_d():
    return [dict(shift_id=r['shift_id'], date=r['date'], weekday=key('wday', r['weekday']), adult1_late=bool(r['adult1_late']), adult2_shift=key('shift', r['adult2_shift']), adults_free=r['adults_free'])
            for r in SH]


def terms_d():
    return [dict(term_id=r['term_id'], term=key('tname', r['term']), kind=key('tkind', r['kind']), start=r['start'], end=r['end'], days=r['days']) for r in TM]


def gifts_d():
    out = []
    for r in GF:
        row = dict(gift_id=r['gift_id'], name=r['name'], relation=r['relation'], date=r['date'], gift_idea=r['gift_idea'], status=key('gstatus', 'Given' if r['name'] == 'Cousin Mia' else r['status']), cost=r['cost'])
        if r['age_turning'] != '': row['age_turning'] = r['age_turning']
        out.append(row)
    return out


def pets_d():
    out = [dict(pet_id=p['pet_id'], pet=p['pet'], species=p['species']) for p in PET]
    return out + [dict(pet_id='PT-%02d' % i) for i in range(3, 6)]


def vehicles_d():
    out = [dict(vehicle_id=v['vehicle_id'], vehicle=v['vehicle'], year=v['year']) for v in VEH]
    return out + [dict(vehicle_id='VH-%02d' % i) for i in range(3, 6)]


def pet_care_d():
    out = []
    for r in PC:
        row = dict(care_id=r['care_id'], pet_id=r['pet_id'], pet=r['pet'], date=r['date'], task=key('ptask', r['task']), booked=bool(r['booked']))
        if r['qty_kg']: row['qty_kg'] = r['qty_kg']
        if r['cost']: row['cost'] = r['cost']
        out.append(row)
    return out


def vehicle_log_d():
    out = []
    for r in VL:
        row = dict(log_id=r['log_id'], vehicle_id=r['vehicle_id'], vehicle=r['vehicle'], date=r['date'], kind=key('vkind', r['kind']), km=r['km'], who=r['who'])
        if r['cost']: row['cost'] = r['cost']
        out.append(row)
    return out


def tasks_d():
    out = [dict(task_id=r['task_id'], task=r['task'], area=r['area'], assigned=r['assigned'], interval_days=r['interval_days'], last_done=r['last_done']) for r in MNT]
    i = next(k for k, r in enumerate(out) if r['task_id'] == ST['filter']); out.insert(0, out.pop(i))
    return out


def visitors_d():
    spec = [('Hana', 9, 11, 1, 'Living room sofa'), ('Aunt Lena', 34, 39, 2, 'Guest room'), ('Uncle Femi', 36, 39, 1, 'Study sofa bed'), ('Ada', 36, 38, 1, 'Child 2 room, camp bed'),
            ('Cousin Mia', 37, 39, 1, 'Living room sofa'), ('Friend Omar', -60, -58, 1, 'Living room sofa'), ('Cousin Tobi', -120, -116, 2, 'Guest room'), ('Friend Zoe', -200, -198, 2, 'Guest room'),
            ('Noor', -260, -258, 1, 'Living room sofa'), ('Dev', -330, -326, 1, 'Guest room'), ('Marcus', 150, 152, 1, 'Study sofa bed'), ('Sven', 230, 233, 1, 'Study sofa bed')]
    return [dict(visitor=a, arrive=iso(T0 + _dt.timedelta(days=b)), leave=iso(T0 + _dt.timedelta(days=c)), beds=d, room=key('stayroom', e), phone=fake_phone(40 + i)) for i, (a, b, c, d, e) in enumerate(spec)]


def pet_sched_d():
    spec = [('Bruno', 'Grooming', 56, '10:00'), ('Bruno', 'Vet visit', 365, '09:30'), ('Bruno', 'Vaccination visit', 365, '09:30'), ('Bruno', 'Nail trim', 120, ''), ('Bruno', 'Bath', 28, ''), ('Bruno', 'Food bag bought', 24, ''),
            ('Pip', 'Vet visit', 365, '11:00'), ('Pip', 'Vaccination visit', 365, '11:00'), ('Pip', 'Nail trim', 60, ''), ('Pip', 'Food bag bought', 30, ''), ('Pip', 'Grooming', 90, ''), ('Pip', 'Bath', 120, '')]
    out = []
    for i, (p, t, iv, at) in enumerate(spec, 1):
        row = dict(ps_id='PS-%02d' % i, pet=p, task=key('ptask', t), interval_days=iv)
        if at: row['at'] = at
        out.append(row)
    return out


def vehicle_dates_d():
    out, i = [], 0
    for v in VEH:
        for kind, iv in (('Service', 365), ('Tyres', 730), ('Annual test', 365), ('Insurance renewal', 365), ('Registration renewal', 365), ('Mileage reading', 30)):
            i += 1; out.append(dict(vd_id='VD-%02d' % i, vehicle=v['vehicle'], kind=key('vkind', kind), interval_days=iv))
    return out


def nums(n): return [dict(no=i) for i in range(1, n + 1)]
def busy_d(): return [dict(no=i, wk=key('wk12', 'Week %d' % i)) for i in range(1, 13)]
def driving_d(): return [dict(no=i, weeks_ago=(i + 1) // 2, adult=key('adult', 'Adult %d' % (2 - i % 2))) for i in range(1, 25)]
def pet_food_d(): return [dict(pet_id='PT-%02d' % i) for i in range(1, 6)]
def veh_est_d(): return [dict(vehicle_id='VH-%02d' % i) for i in range(1, 6)]
