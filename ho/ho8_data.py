"""Home Management suite part 8: demo rows from ho_core (projects, tasks, guests, declutter) plus the typed hosting, move and year-review rows."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ho8_lists import *
import datetime as _dt
from collections import Counter, OrderedDict

T0 = TODAY
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def D_(s): return _dt.date.fromisoformat(s)
def nz(x): return x if x else None
def dd(n): return iso(T0 + _dt.timedelta(days=n))

PROJ = project_rows() + [dict(project_id='PJ-05', project='Move to the new home', kind='Move')]
TASKS = project_task_rows(); GST = guest_rows(); DECL = declutter_rows()
def _t(i, task, owner, s0, due, status, dep, est, act, done):
    return dict(project_id='PJ-05', task=task, owner=owner, start=iso(TODAY + _dt.timedelta(days=s0)), due=iso(TODAY + _dt.timedelta(days=due)), status=status, depends_on=dep, est_cost=float(est), actual_cost=float(act),
                done_on=iso(TODAY + _dt.timedelta(days=done)) if done is not None else '', task_id='PK-%03d' % i)
TASKS = TASKS + [_t(56, 'Choose the removal company', 'Adult 1', -21, -12, 'Done', '', 0, 0, -13), _t(57, 'Pay the deposit for the van', 'Adult 1', -12, -8, 'Done', 'PK-056', 120, 130, -9),
                 _t(58, 'Book the removal van and helpers', 'Adult 2', -6, 2, 'In progress', 'PK-057', 450, 0, None), _t(59, 'Order boxes and packing paper', 'Adult 1', 3, 9, 'Not started', 'PK-058', 85, 0, None),
                 _t(60, 'Book the cleaners for the old home', 'Adult 2', 30, 40, 'Not started', 'PK-058', 160, 0, None)]
TASKD = {t['task_id']: t for t in TASKS}
DINNER = next_on(12, 20)                      # the holiday dinner (PJ-03 is counted back from this date)
MOVE = T0 + _dt.timedelta(days=49)            # the planned move day of the move planner (a sample plan, replace it)

PHASES = [
    ('PJ-01', 'Plan and choose', [1, 2, 3], 'Agree the plan, get quotes, choose tiles and fittings', '', ''),
    ('PJ-01', 'Order and book', [4, 5, 12], 'Book the builder and plumber, order the bath and the mirror', '', ''),
    ('PJ-01', 'Strip out the room', [6, 7], 'Clear the room and strip out the old suite', 'Raj Mehta', '+1 92 555 5424'),
    ('PJ-01', 'Build and fit', [8, 9, 10, 11], 'First fix, tiling, paint and the new bath and toilet', 'Tomas Reyes', '+44 33 555 4277'),
    ('PJ-01', 'Finish and snag', [13, 14, 15], 'Final clean, snag list, final invoice and the mirror', '', ''),
    ('PJ-02', 'Plan and mark out', [16, 17], 'Choose the spot, measure and mark the bed', '', ''),
    ('PJ-02', 'Dig, build and fill', [18, 19, 20, 21], 'Dig, order compost and edging, build the edge and fill', 'Omar Khalil', '+61 57 555 5239'),
    ('PJ-02', 'Plant and care', [22, 23, 24, 25, 26, 27], 'Plants, planting with the children, mulch, watering rota', '', ''),
    ('PJ-03', 'Invite and RSVP', [28, 29, 30], 'Guest list, invitations, replies and preference notes', '', ''),
    ('PJ-03', 'Menu and orders', [31, 32, 33], 'Menu, chairs and table, the main dish order', '', ''),
    ('PJ-03', 'Shop and prepare', [34, 35, 36, 37, 38, 39], 'Plates, linen, shopping, deep clean, starters and dessert', '', ''),
    ('PJ-03', 'The day', [40, 41, 42, 43], 'Set the table, cook, welcome the guests, clear up', '', ''),
    ('PJ-04', 'Plan and sort', [44, 45, 46, 47, 48, 49, 50, 51, 52], 'Pick the areas and sort every room: keep, donate, sell or bin', '', ''),
    ('PJ-04', 'Donate and finish', [53, 54, 55], 'Donation drop-off, recycling run and the final walk-through', '', ''),
    ('PJ-05', 'Plan the move', [56, 57, 58, 59, 60], 'Choose the van, pay the deposit, book helpers, boxes and cleaners', '', '')]
PHASE_OF = {}
for pj, ph, ids, *_ in PHASES:
    for i in ids: PHASE_OF['PK-%03d' % i] = ph


def minutes(t):
    dur = (D_(t['due']) - D_(t['start'])).days + 1
    if t['owner'] == 'A trade': return 60
    if t['owner'] in ('Child 1', 'Child 2'): return min(120, 20 * dur)
    return min(480, 35 * dur)


def team_d():
    return [dict(member_id=t['member_id'], name=t['name'], role=key('role', t['role']), group=t['group'], phone=t['phone'], email=t['email'], note=t['note'], start=t['start'], short=first_name(t['name'])) for t in team]


def projects_d(): return [dict(project_id=p['project_id'], project=p['project'], kind=key('pkind', p['kind'])) for p in PROJ]


def plan_d():
    out = []
    for pj, ph, ids, note, helper, hph in PHASES:
        ts = [TASKD['PK-%03d' % i] for i in ids]
        owners = Counter(t['owner'] for t in ts if t['owner'] != 'A trade') or Counter(['A trade'])
        sts = {t['status'] for t in ts}
        stage = 'Done' if sts == {'Done'} else 'Waiting' if 'Blocked' in sts else 'In progress' if sts & {'In progress', 'Done'} else 'Planned'
        out.append(nb(dict(project_id=pj, phase=ph, start=min(t['start'] for t in ts), end=max(t['due'] for t in ts), owner=key('powner', ('A trade' if helper else owners.most_common(1)[0][0])),
                           estimate=nz(sum(t['est_cost'] for t in ts)), stage=key('pstage', stage), note=note, helper=helper, helper_phone=hph)))
    return out


def tasks_d():
    out = []
    for t in TASKS:
        out.append(nb(dict(task_id=t['task_id'], project_id=t['project_id'], phase=PHASE_OF[t['task_id']], task=t['task'], owner=key('powner', t['owner']), start=t['start'], due=t['due'],
                           status=key('tstatus', t['status']), depends_on=t['depends_on'], minutes=minutes(t), est_cost=nz(t['est_cost']), actual_cost=nz(t['actual_cost']), done_on=t['done_on'])))
    out.sort(key=lambda r: (r['task_id'] != 'PK-012', r['task_id']))
    return out


def guests_d():
    out = []; tbl = 0
    for i, g in enumerate(GST):
        size = 2 if g['guest_id'] == 'GU-01' else 1
        if g['rsvp'] in ('Yes', 'Maybe'): tbl += 1
        out.append(nb(dict(guest_id=g['guest_id'], guest=g['guest'], rsvp=key('rsvp', g['rsvp']), party_size=size, pref_label=key('gprefs', g['pref_label']), project_id=g['project_id'],
                           invited_on=g['invited_on'], phone=fake_phone(300 + i), table_no=(1 if tbl % 2 else 2) if g['rsvp'] in ('Yes', 'Maybe') else None)))
    return out


MENU = [('Starter', 'RC-16', 16, 'Adult 1', -3), ('Main', 'RC-17', 12, 'Adult 2', 0), ('Main', 'RC-23', 6, 'Adult 1', -1), ('Main', 'RC-22', 4, 'Adult 2', 0),
        ('Side', 'RC-21', 16, 'Adult 1', -1), ('Side', 'RC-34', 16, 'Child 1', 0), ('Side', 'RC-38', 16, 'Child 1', 0), ('Side', 'RC-36', 12, 'Adult 2', -1),
        ('Dessert', 'RC-46', 16, 'Adult 1', -3), ('Dessert', 'RC-50', 12, 'Adult 1', -3), ('Dessert', 'RC-42', 8, 'Child 1', 0), ('Snack', 'RC-49', 12, 'Child 1', -2)]
REC = recipe_rows(); RI = recipe_ingredient_rows()


def recipes_d(): return [dict(recipe_id=r['recipe_id'], recipe=r['recipe'], category=key('rcat', r['category']), prep_min=r['prep_min'], servings=r['servings'], pref_label=key('pref', r['pref_label'])) for r in REC]
def ri_d(): return [dict(ingredient_id=r['ingredient_id'], recipe_id=r['recipe_id'], item=r['item'], qty=r['qty'], unit=key('unit', r['unit']), section=r['section']) for r in RI]
def menu_d(): return [dict(course=c, recipe_id=rid, portions=p, cook=key('powner', ck), day_to_cook=iso(DINNER + _dt.timedelta(days=o))) for c, rid, p, ck, o in MENU]


PACK = {'potatoes': 2, 'leeks': 1, 'onion': 1, 'stock cubes': 1, 'milk': 2, 'chicken thighs': 1, 'carrots': 1, 'olive oil': 1, 'cheese': 0.5, 'broccoli': 1, 'cream': 300, 'pasta': 0.5, 'fish fillets': 1,
        'lemons': 4, 'peppers': 3, 'rice': 1, 'mince': 0.5, 'tinned tomatoes': 1, 'cucumber': 1, 'tomatoes': 0.5, 'lettuce': 1, 'couscous': 0.5, 'chickpeas': 1, 'beans': 1, 'sweetcorn': 1,
        'yoghurt': 4, 'bananas': 6, 'berries': 1, 'oats': 1, 'honey': 350, 'apples': 1, 'flour': 1.5, 'butter': 1, 'sugar': 1, 'eggs': 12, 'baking powder': 1}
BOUGHT = {'stock cubes', 'olive oil', 'baking powder', 'sugar', 'honey', 'tinned tomatoes', 'chickpeas', 'sweetcorn', 'couscous'}


def menu_shop_d():
    ids = {m[1] for m in MENU}; seen = OrderedDict()
    for r in RI:
        if r['recipe_id'] in ids: seen.setdefault(r['item'], (r['unit'], r['section']))
    out = [dict(item=it, section=key('msect', sec), unit=key('unit', u), pack_size=PACK[it], bought=it in BOUGHT) for it, (u, sec) in seen.items()]
    out.sort(key=lambda r: (_M['msect'][next(l for l in MSECT if _M['msect'][l] == r['section'])] if False else MSECT.index(next(l for l in MSECT if key('msect', l) == r['section'])), r['item']))
    return out


def timeline_d():
    out = []
    for t in TASKS:
        if t['project_id'] != 'PJ-03': continue
        out.append(dict(task=t['task'], days_before=(DINNER - D_(t['due'])).days + 0, owner=key('hown', t['owner']), _due=t['due'], _st=t['status']))
    out.sort(key=lambda r: (r['_st'] == 'Done', r['_due']))
    return [{k: v for k, v in r.items() if not k.startswith('_')} for r in out]


BOXES = [('GAR-1', 'Garage', 14, True, 'Tools and shelves', -2), ('GDN-1', 'Garden', 5, True, 'Pots and garden tools', -2), ('UTL-1', 'Utility room', 6, True, 'Cleaning supplies', 0),
         ('HAL-1', 'Hallway', 4, True, 'Shoes, coats and the key box', 0), ('KIT-A', 'Kitchen', 12, False, 'Pans, plates and glasses', 0), ('KIT-B', 'Kitchen', 7, False, 'Food and tins, packed last', 0),
         ('LIV-1', 'Living room', 10, False, 'Books, games and photos', 0), ('BTH-1', 'Bathroom', 3, False, 'Towels and bathroom items', 0), ('MBR-1', 'Main bedroom', 9, False, 'Clothes and bed linen', 0),
         ('KID-A', 'Kids room', 8, False, 'Child 1 room: books and clothes', 0), ('KID-B', 'Kids room', 6, True, 'Child 2 room: toys, packed first', 0), ('WHL-1', 'Whole home', 4, False, 'First-night box and papers', 0)]
def boxes_d(): return sorted([dict(label=l, room=key('room', r), boxes=b, packed=p, notes=n, moves_on=iso(MOVE + _dt.timedelta(days=o))) for l, r, b, p, n, o in BOXES], key=lambda r: r['packed'])

NOTICE = {'Employer and payroll': (28, 10), 'Banks and card providers': (28, 0), 'Insurance providers': (21, 4), 'Energy and water suppliers': (14, 0), 'Internet and phone providers': (28, 0),
          'Post redirect service': (14, 0), 'Schools and childcare': (56, 0), 'Vehicle and licence offices': (21, 20), 'Local council or town office': (21, 0), 'Vet clinic and pet registration': (14, 6),
          'Subscriptions and memberships': (14, 3), 'Family and friends': (7, 0)}
def address_d():
    return sorted([nb(dict(orgtype=key('orgtype', o), notice_days=n, done=bool(d), done_on=dd(-d) if d else None)) for o, (n, d) in NOTICE.items()], key=lambda r: r['done'])


STEPS = [('Give notice to the landlord or confirm the completion date', 56, True), ('Book the removal van or helpers', 49, False), ('Order boxes and packing materials', 42, False),
         ('Start the change-of-address list', 35, False), ('Book the time off and the sitter for moving day', 28, False), ('Pack the rooms you use least', 21, False),
         ('Book the final meter readings', 14, False), ('Collect the keys of the new home', 10, False), ('Redirect the post and tell the school office', 7, False),
         ('Defrost the freezer and use up the food', 3, False), ('Pack a first-night box', 2, False), ('Confirm the van, the keys and the parking', 1, False)]
def countdown_d(): return [dict(step=s, days_before=d, done=dn) for s, d, dn in STEPS]


def declutter_d():
    out = []
    for x in DECL:
        out.append(nb(dict(declutter_id=x['declutter_id'], date=x['date'], area=key('room', x['area']), item=x['item'], decision=key('decision', x['decision']), count=x['count'], project_id=x['project_id'],
                           destination=x['destination'], value=nz(x['value']))))
    out.sort(key=lambda r: (r['declutter_id'] != 'DN-100', r['declutter_id']))
    return out


def donations_d(): return [dict(no=i) for i in range(1, 31)]
def areas_d(): return [dict(area=key('room', r)) for r in ROOMS]
def status_d(): return [dict(phase=ph) for pj, ph, *_ in PHASES]
def deps_d(): return [dict(task_id=t['task_id']) for t in sorted(TASKS, key=lambda t: (t['task_id'] != 'PK-012', t['task_id']))]
def cost_d(): return [dict(project=p['project'], owner=key('powner', o)) for p in PROJ for o in ('Adult 1', 'Adult 2', 'A trade')]

YR = [  # measure, typed this year, last year, higher is better, next-year line
    ('Maintenance tasks done', 44, 39, True, ''), ('Maintenance tasks overdue at year end', 3, 5, False, 'Put every filter change in the plan at the start of each season'),
    ('Repairs logged', 14, 12, False, 'Do the seasonal maintenance tasks on time'), ('Repair cost line per repair', 68, 79, False, ''), ('Adult 1 chore hours', 96, 105, True, 'Share the planning and booking jobs more evenly'),
    ('Points away from the agreed chore share', 13, 18, False, ''), ('Weeks the children met the points goal', 31, 24, True, ''), ('Warranties that ended with a fault open', 1, None, False, ''),
    ('Dinners cooked per week', 5.2, 4.9, True, ''), ('Share of planned dinners cooked, percent', 86, 87, True, ''), ('Projects finished', None, 1, True, ''), ('Project tasks done', None, 18, True, ''),
    ('Areas decluttered, of 10', None, 5, True, ''), ('Items donated', None, 150, True, '')]
def year_d(): return sorted([nb(dict(measure=key('ymeasure', m), this_typed=t, last_year=l, higher_better=h, next_year=n, typed_on=dd(-3))) for m, t, l, h, n in YR], key=lambda r: 'next_year' not in r)


if __name__ == '__main__':
    for f in (team_d, projects_d, plan_d, tasks_d, guests_d, recipes_d, ri_d, menu_d, menu_shop_d, timeline_d, boxes_d, address_d, countdown_d, declutter_d, donations_d, areas_d, status_d, deps_d, cost_d, year_d):
        print(f.__name__, len(f()))
    print(timeline_d()[:3]); print(menu_shop_d()[:3]); print(plan_d()[:2])
