"""Childcare center suite part 8: demo rows from cc_core (monthly P&L, room months, cash, expenses ... full generator output where small, aggregates built from the generators)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc8_lists import *
import collections

dd = to_date
ST = story()
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}


TEAM = {t['name']: t for t in team}
OWNER_PHONE = TEAM[OWNER]['phone']; DIRECTOR_PHONE = TEAM[ASSISTANT_DIRECTOR]['phone']
CONTACT = {t['role']: t for t in contacts}
ACC_PHONE = CONTACT['Accountant']['phone']; FOOD_PHONE = CONTACT['Food supplier']['phone']; CLEAN_PHONE = CONTACT['Cleaner']['phone']; MAINT_PHONE = CONTACT['Maintenance']['phone']
ACC_NAME = CONTACT['Accountant']['name']; FOOD_NAME = CONTACT['Food supplier']['name']; CLEAN_NAME = CONTACT['Cleaner']['name']; MAINT_NAME = CONTACT['Maintenance']['name']
LEAD = {}
for t in team:
    if t['role'] == 'Lead teacher': LEAD[t['room']] = t
LEAD['School-age'] = TEAM['Sofia Petrova']
FIRST = lambda n: n.split()[0]

ATT = attendance_rows()
CHILD_DAYS = collections.Counter(x['month'] for x in ATT if x['status'] == 'Present')
CHILD_HOURS = collections.defaultdict(float)
for _x in ATT:
    if _x['status'] == 'Present': CHILD_HOURS[(_x['month'], _x['room'])] += _x['hours']
PNL = pnl_rows(); RMF = room_month_rows(); CASH = cash_rows(); TAX = tax_rows()
M0 = month_start(0)
LAST12 = [month_start(k) for k in range(12, 0, -1)]      # the 12 full months before this month
CUR12 = [month_start(k) for k in range(12, -1, -1)]      # the 12 full months and this month


def pnl_d():
    return [dict(month=r['month'], tuition_revenue=r['tuition_revenue'], fee_revenue=r['fee_revenue'], government_part=r['government_part'], staff_pay=r['staff_pay'], owner_pay=r['owner_pay'],
                 food=r['food'], rent=r['rent'], other_costs=r['other_costs'], staff_hours=r['staff_hours'], child_days=CHILD_DAYS.get(r['month'], 0)) for r in PNL]


def room_months_d():
    return [dict(row_id=r['row_id'], month=r['month'], room=key('room', r['room']), enrolled=r['enrolled'], revenue=r['revenue'], staff_cost=r['staff_cost'], food_cost=r['food_cost'], overhead_share=r['overhead_share']) for r in RMF]


def cash_d():
    return [dict(month=r['month'], opening=r['opening'], parent_payments=r['parent_payments'], government_payments=r['government_payments'], pay_out=r['pay_out'], expenses_out=r['expenses_out'],
                 tax_set_aside=r['tax_set_aside'], deposit_refunds=r['deposit_refunds'], owner_extra=r['owner_extra']) for r in CASH]


def tax_d():
    return [nb(dict(month=r['month'], due_date=r['due_date'], paid_on=r['paid_on'])) for r in TAX]


_EX = [x for x in expense_rows() if x['date'] >= iso(month_start(12))]
_UNCAT = {_EX[i]['expense_id'] for i in (-3, -9, -17)}   # story touch: three recent receipts are still without a category


def expenses_d():
    out = []
    for x in _EX:
        d = dict(expense_id=x['expense_id'], date=x['date'], month=x['month'], category=key('expcat', x['category']), description=x['description'], amount=x['amount'], paid_to=x['paid_to'])
        if x['expense_id'] in _UNCAT: d.pop('category')
        out.append(d)
    i = next(k for k, x in enumerate(out) if x.get('category') == key('expcat', 'Supplies and toys'))
    out.insert(0, out.pop(i))
    return out


def bills_d():
    return [dict(bill_id=b['bill_id'], due_date=b['due_date'], category=b['category'], paid_to=b['paid_to'], amount=b['amount'], paid=(b['status'] == 'Paid')) for b in bills]


bills = bill_rows()


def rooms_d(): return [dict(room=key('room', r['room']), capacity=r['capacity'], ratio=r['ratio']) for r in rooms]


def rates_d():
    return [dict(rate_id=r['rate_id'], room=key('room', r['room']), schedule=key('schedule', r['schedule']), weekly_rate=r['weekly_rate'], last_year_rate=r['last_year_rate'], days=r['days'],
                 hours_day=r['hours_day'], day_rate=r['day_rate'], reviewed_on=iso(dt.date(TODAY.year, 1, 1))) for r in rates]


def payroll_d():
    return [dict(pay_id=p['pay_id'], month=p['month'], person=p['person'], role=key('payrole', p['role']), pay_type=key('paytype', p['pay_type']), hours=p['hours'], total=p['total'], pay_date=p['pay_date'])
            for p in pay_rows(n=100)]


def rev_room_d(): return [dict(room=key('room', r), month=iso(m)) for r in ROOMS for m in LAST12]
def staff_share_d(): return [dict(month=r['month']) for r in PNL]
def occupancy_d(): return [dict(month=r['month']) for r in PNL]
def breakeven_d(): return [dict(month=r['month']) for r in PNL]
def cost_hour_d(): return [dict(room=key('room', r), month=iso(m), child_hours=round(CHILD_HOURS.get((iso(m), r), 0.0), 1)) for r in ROOMS for m in CUR12]
def fee_check_d(): return [dict(room=key('room', r)) for r in ROOMS]

_SC = [('Enrol two more infants', 'Infants', 2, 0), ('Enrol three more infants', 'Infants', 3, 0), ('Enrol one infant', 'Infants', 1, 0), ('Lose a family', 'Toddlers', -2, 0),
       ('Lose two families', 'Twos', -3, 0), ('Open a part-time day', 'School-age', 4, 30), ('Enrol five school-age children', 'School-age', 5, 40), ('Fill Twos to capacity', 'Twos', 1, 0),
       ('Fill Preschool to capacity', 'Preschool', 3, 0), ('Toddlers one child fewer', 'Toddlers', -1, 0), ('Hire relief for Toddlers', 'Toddlers', 0, 40), ('Drop a school-age day', 'School-age', -3, -30)]


def scenarios_d(): return [dict(scenario=key('scnrow', a), room=key('room', b), children_change=c, staff_hours_change=d) for a, b, c, d in _SC]


def budget_d():
    ex = expense_rows(); act = collections.defaultdict(float)
    for x in ex: act[(x['category'], x['month'])] += x['amount']
    out = []; cm = {}; bn = 0
    for cat in EXPENSE_CATEGORIES:
        tot = sum(v for (c, m), v in act.items() if c == cat)
        cm[cat] = max(10.0, round(tot / 24.0 * 1.03 / 10.0) * 10.0)
    cm['Rent'] = 4700.0
    for cat in EXPENSE_CATEGORIES:
        for m in LAST12:
            ly = act.get((cat, iso(add_months(m, -12))), 0.0)
            bn += 1; d = dict(budget_id='BG-%03d' % bn, category=key('expcat', cat), month=iso(m), budget=cm[cat])
            if iso(add_months(m, -12)) >= iso(HISTORY_START): d['last_year'] = round(ly, 2)
            out.append(d)
    return out


_HL = [('Rent or housing cost', 1850, 'Rooms and hours', 300), ('Electricity and heating', 210, 'Rooms and hours', 280), ('Water', 55, 'Hours share', 250), ('Internet and phone', 70, 'Hours share', 210),
       ('Home insurance', 95, 'Rooms share', 190), ('Repairs and upkeep', 120, 'Rooms share', 150), ('Garden and play area', 80, 'Hours share', 120), ('Cleaning supplies', 45, 'Whole amount', 90),
       ('Kitchen equipment', 60, 'Hours share', 75), ('Laundry', 35, 'Whole amount', 60), ('Furniture and storage', 40, 'Rooms share', 40), ('Household groceries', 520, 'Not shared', 20)]


def home_lines_d():
    return [dict(line=a, amount=float(b), rule=key('homerule', c), set_on=ago(d), confirmed=(i % 3 != 2)) for i, (a, b, c, d) in enumerate(_HL)]


def draw_plan_d(): return [dict(no=i) for i in range(1, 13)]
def year_review_d(): return [dict(review_id='YR-%02d' % (i + 1), no=n, basis=key('basis', b)) for i, (b, n) in enumerate((b, n) for b in BASIS for n in range(1, 9))]
