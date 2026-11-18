"""Home Management suite part 7: demo rows from ho_core (documents, contacts, renewal sources) and the typed rows of routines, keys and the sitter sheet."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ho7_lists import *
import datetime as _dt

ST = story()
T0 = TODAY
def D_(s): return _dt.date.fromisoformat(s)
def plus(s, n): return iso(D_(s) + _dt.timedelta(days=n))

DOCS = document_rows(); CON = contact_rows(); INV = inventory_rows(); MNT = maintenance_rows(); VEH = vehicle_rows(); PET = pet_rows()
BLANK_PLACE = {'Library cards, family', 'School bus pass, Child 1'}      # two papers with no place typed yet: the "documents without a place" checks have something to find


def team_d():
    return [dict(member_id=t['member_id'], name=t['name'], role=key('role', t['role']), group=t['group'], phone=t['phone'], email=t['email'], note=t['note'], start=t['start'],
                 short=first_name(t['name'])) for t in team]


def _doc_handler(r):
    d = r['doc']
    if any(w in d for w in ('Heating system service', 'Home alarm service', 'Boiler guarantee', 'Window cleaner', 'Garden waste')): return 'A trade'
    if 'Adult 2' in d or 'older car' in d or r['kind'] == 'Pet paper' or 'Pet insurance' in d or 'Dishwasher' in d or 'Washing machine' in d: return 'Adult 2'
    return 'Adult 1'


def docs_d():
    out = []
    for r in DOCS:
        row = dict(doc_id=r['doc_id'], doc=r['doc'], kind=key('dkind', r['kind']), holder=key('epeople', r['holder']), expiry=r['expiry'], renew_lead_days=r['renew_lead_days'],
                   status=key('dstatus', r['status']), handler=key('hand', _doc_handler(r)))
        if r['doc'] not in BLANK_PLACE: row['kept_where'] = key('kept', r['kept_where'])
        if r['renewed_on']: row['renewed_on'] = r['renewed_on']
        out.append(row)
    REN = {'DC-01': -66, 'DC-02': -35, 'DC-03': -27, 'DC-04': -33, 'DC-05': 5, 'DC-06': -31}       # renewed_on = expiry + days: most started before the action date, one renewed late
    for r in out:
        if r['doc_id'] in REN: r['renewed_on'] = plus(r['expiry'], REN[r['doc_id']])
    i = next(k for k, r in enumerate(out) if r['doc_id'] == ST['travel'])
    out.insert(0, out.pop(i))                              # the story row first: Child 1 travel document, lead time missed, before the trip
    return out


def contacts_d():
    out = []
    for r in CON:
        row = dict(contact_id=r['contact_id'], name=r['name'], kind=key('ckind', r['kind']), trade=r['trade'], phone=r['phone'], email=r['email'], last_used=r['last_used'], cost_last=r['cost_last'],
                   would_use_again=bool(r['would_use_again']))
        if r['member_id']: row['member_id'] = r['member_id']
        if r['name'] == 'Kofi Mensah': row.pop('phone')         # one contact with no number typed yet
        out.append(row)
    i = next(k for k, r in enumerate(out) if r['contact_id'] == 'CT-01')
    out.insert(0, out.pop(i))
    return out


def warranties_d():
    rows = [r for r in INV if r['warranty_end']]
    rows.sort(key=lambda r: r['warranty_end'])
    rows = rows[-50:]
    out = []
    for r in rows:
        trade = r['item'] in ('Washing machine', 'Heated towel rail', 'Chest freezer', 'Shower pump', 'Smoke alarm set', 'Doorbell camera')
        cat = r['category']
        hand = 'A trade' if trade else ('Adult 2' if cat in ('Appliance', 'Kitchenware', 'Bedding and linen') else 'Adult 1')
        row = dict(item_id=r['item_id'], item=r['item'], room=r['room'], warranty_end=r['warranty_end'], price=r['price'], handler=key('hand', hand),
                   receipt=bool(r['receipt_date']), manual=r['manual_place'])
        if r['item_id'] == ST['washer']: row['note'] = 'Open fault logged: does not drain'
        elif r['receipt_date']: row['note'] = 'Receipt kept in the document box'
        out.append(row)
    i = next(k for k, r in enumerate(out) if r['item_id'] == ST['washer'])
    out.insert(0, out.pop(i))
    return out


def vehicle_dates_d():
    rows = []
    v1, v2 = VEH
    nx = lambda v: plus(v['last_service'], v['service_days'])
    spec = [(v1, 'Service', nx(v1), 'Next yearly service, typical, check the manual', 'Adult 1'), (v1, 'Tyres', '2027-09-24', 'Tyre check, typical yearly, check the manual', 'Adult 1'),
            (v1, 'Annual test', v1['inspection_due'], 'Annual vehicle test, check your local rules', 'Adult 1'), (v1, 'Insurance renewal', v1['insurance_renewal'], 'Compare the offers before the date', 'Adult 1'),
            (v1, 'Registration renewal', v1['registration_renewal'], 'Typed from the renewal letter', 'Adult 1'), (v1, 'Repair', ahead(52), 'Follow-up visit booked with the car mechanic', 'Adult 2'),
            (v2, 'Service', nx(v2), 'Next yearly service, typical, check the manual', 'Adult 2'), (v2, 'Tyres', '2027-02-16', 'Tyre check, typical, check the manual', 'Adult 2'),
            (v2, 'Annual test', v2['inspection_due'], 'Annual vehicle test, check your local rules', 'Adult 2'), (v2, 'Insurance renewal', v2['insurance_renewal'], 'Compare the offers before the date', 'Adult 1'),
            (v2, 'Registration renewal', v2['registration_renewal'], 'Typed from the renewal letter', 'Adult 2'), (v2, 'Repair', ahead(21), 'Follow-up visit booked with the car mechanic', 'A trade')]
    for i, (v, kind, d, note, h) in enumerate(spec, 1):
        rows.append(dict(vd_id='VD-%02d' % i, vehicle=v['vehicle'], kind=key('vkind', kind), date=d, notes=note, handler=key('hand', h)))
    return rows


def pet_dates_d():
    b, p = PET
    spec = [(b, 'Grooming', plus(b['last_groom'], b['groom_every_days']), True, 'A trade'), (b, 'Vet visit', b['vet_next'], True, 'Adult 1'), (b, 'Vaccination visit', ahead(112), False, 'Adult 1'),
            (b, 'Nail trim', ahead(33), False, 'Adult 2'), (b, 'Food bag due', ahead(14), False, 'Adult 2'), (b, 'Bath', ahead(47), False, 'Adult 2'),
            (p, 'Vet visit', p['vet_next'], True, 'Adult 1'), (p, 'Vaccination visit', ahead(85), True, 'A trade'), (p, 'Nail trim', ahead(61), False, 'Adult 2'),
            (p, 'Food bag due', ahead(10), False, 'Adult 2'), (p, 'Grooming', ahead(150), False, 'Adult 2'), (p, 'Bath', ahead(200), False, 'Adult 2')]
    return [dict(pd_id='PD-%02d' % i, pet=v['pet'], task=key('ptask', t), date=d, booked=bk, handler=key('hand', h)) for i, (v, t, d, bk, h) in enumerate(spec, 1)]


FA_AREAS = {'Heating and air', 'Electrics and alarms', 'Safety checks'}


def tasks_d():
    out = []
    for r in MNT:
        out.append(dict(task_id=r['task_id'], task=r['task'], area=r['area'], assigned=key('hand', r['assigned']), interval_days=r['interval_days'], last_done=r['last_done'], fa=r['area'] in FA_AREAS))
    i = next(k for k, r in enumerate(out) if r['task_id'] == ST['filter'])
    out.insert(0, out.pop(i))
    return out


def routines_d():
    spec = [('Bin day', 'Thursday: bins out the night before, recycling on the other weeks', 20), ('School hours', '08:45 to 15:15, doors open at 08:30', 35), ('Bedtimes', 'Child 1 at 21:00, Child 2 at 19:30 on school nights', 60),
            ('Pet feed times', 'Bruno at 07:00 and 17:30, Pip at 07:30 and 18:00', 14), ('Dog walk', 'Weekday walk with the dog walker on late days', 140), ('Quiet hours', 'Screens off at 20:45 for Child 2, 21:30 for Child 1', 75),
            ('Homework time', '16:30 to 17:15 at the kitchen table', 210), ('Heating timer', 'On at 06:30 and 17:00, off at 22:00', 45), ('School pick-up', 'The grandparent collects on Wednesdays', 28),
            ('Babysitter evening', 'Some Fridays, the children are in bed by the times above', 9), ('Weekly shop', 'Saturday morning, the list is on the fridge', 400), ('Laundry day', 'Sunday and Wednesday, bed linen on Sunday', 120)]
    return [dict(routine=a, when=b, notes='Check with the household before a sitter evening' if i in (2, 9) else '', reviewed=ago(c)) for i, (a, b, c) in enumerate(spec)]


def where_d():
    spec = [('Stopcock', 'Under the kitchen sink', 'Everyone should know where it is', 30), ('Fuse box', 'Hall cupboard, top shelf', 'Label the circuits when you can', 30), ('Spare keys', 'Key hook by the back door', 'Copies are listed on the key list', 12),
            ('Manuals box', 'Study shelf, the blue box', 'Warranty papers are in the document box', 90), ('Torches', 'Cupboard under the stairs', 'Spare batteries beside them', 150), ('Spare bulbs and batteries', 'Utility room, second shelf', '', 150),
            ('Tool box', 'Garage, left shelf', 'Drill and drill bits are inside', 200), ('Filter spares', 'Utility room, bottom shelf', 'Boiler or furnace and cooker hood filters', 22), ('Meter readings', 'Hall cupboard, on the door', 'Photo on the first of the month',45),
            ('Router', 'Living room shelf', 'The sticker has the network name', 300), ('Bin bags', 'Under the stairs', '', 300), ('Pet food', 'Utility room, bottom shelf', 'Bruno and Pip, check the bag dates', 10)]
    return [dict(thing=a, place=b, notes=c, checked=ago(d)) for a, b, c, d in spec]


def keys_d():
    spec = [('Neighbour', 'Spare front door key', '2023-01-28', '', 'Kept in the neighbour hall'), ('Dog walker', 'Back door key', '2023-10-15', '', 'For weekday walks on late days'),
            ('Babysitter', 'Front door key for the evening', ago(41), plus(ago(41), 1), 'Returned the next morning'), ('Grandparent', 'House key copy', '2021-09-01', '', 'For the Wednesday pick-up'),
            ('Neighbour', 'Garage remote', '2024-04-02', '', 'Spare remote'), ('Babysitter', 'Front door key for the evening', ago(68), plus(ago(68), 1), 'Returned the next morning'),
            ('Carpool family', 'Shed key', ago(79), '', 'Borrowed to fetch the ladders'), ('Dog walker', 'Garden gate key', '2025-03-04', '2025-03-05', 'Returned after the spring walks'),
            ('Landlord or agent', 'Spare key for inspections', '2024-02-01', '', 'Renters: keep the date of each visit'), ('Babysitter', 'Front door key for the evening', ago(5), '', 'Out for the Friday evening'),
            ('Grandparent', 'Car key, second car', ago(180), ago(168), 'Returned after the school run week'), ('Carpool family', 'Garage remote', '2025-11-02', '2025-11-30', 'Returned after the holiday lifts')]
    out = []
    for i, (h, what, since, ret, note) in enumerate(spec, 1):
        row = dict(key_id='KY-%02d' % i, holder=key('kholder', h), what=what, since=since, note=note)
        if ret: row['returned'] = ret
        out.append(row)
    return out


def renewals_d(): return [dict(no=i) for i in range(1, 61)]
def month_d(): return [dict(mk=i, ahead=key('ahead12', AHEAD[i]), qtr=key('qtr4', QTR[i // 3])) for i in range(12)]
def rtype_d(): return [dict(type=key('rtype', t)) for t in RTYPES]
def board_d(): return [dict(no=i) for i in range(1, 42)]
def actions_d(): return [dict(no=i) for i in range(1, 21)]
def holder_d(): return [dict(holder=h, kind=k) for h, k in sorted({(r['holder'], r['kind']) for r in docs_d()})]
def ckind_d(): return [dict(kind=key('ckind', k)) for k in CONTACT_KINDS]
def storage_d(): return [dict(kept=key('kept', k)) for k in KEPT]


def emergency_d():
    spec = [('Adult 1', 'Family and home', 'First call for the children and the house', 20), ('Adult 2', 'Family and home', 'Second call, shifts change: check the pattern', 20), ('Grandparent', 'Family and home', 'Close to the school, has a key', 45),
            ('Neighbour', 'Family and home', 'Holds a spare key, can reach the house quickly', 30), ('Landlord or agent', 'Family and home', 'Renters: maintenance requests', 410), ('Plumber', 'Trades and vehicles', 'Water or drain problem in the house', 60),
            ('Electrician', 'Trades and vehicles', 'Socket or lighting problem', 60), ('Heating engineer', 'Trades and vehicles', 'Boiler or furnace problem', 95), ('Car mechanic', 'Trades and vehicles', 'Breakdown or a service question', 95),
            ('School office', 'School and pets', 'Absence notes and pick-up changes', 25), ('Carpool family', 'School and pets', 'When a lift changes', 40), ('Vet clinic', 'School and pets', 'Dates only: visit changes', 380)]
    return [dict(who=key('role', r), page=p, when_to_call=w, last_checked=ago(d)) for r, p, w, d in spec]


def sitter_d():
    spec = [('Child 1', 'Team', 'HO-03'), ('Child 2', 'Team', 'HO-04'), ('Call first, adult 1', 'Team', 'HO-01'), ('Call second, adult 2', 'Team', 'HO-02'), ('Neighbour with the spare key', 'Contacts', 'Neighbour'),
            ('School hours', 'Home routines', 'School hours'), ('Bedtimes', 'Home routines', 'Bedtimes'), ('Bin day', 'Home routines', 'Bin day'), ('Feed times', 'Home routines', 'Pet feed times'),
            ('Spare key', 'Where things are', 'Spare keys'), ('Stopcock', 'Where things are', 'Stopcock'), ('Torches and batteries', 'Where things are', '')]
    out = []
    for item, src, look in spec:
        row = dict(item=item, source=key('ssrc', src), sheet='Sitter evening')
        if look: row['lookup'] = look
        out.append(row)
    return out
