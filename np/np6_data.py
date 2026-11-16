"""Nonprofit suite part 6: demo rows from np_core (full generator output where small, key rows only for calculated tables)."""
import sys, os, collections; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from np6_lists import *
import datetime as _dt
import datetime as dt

dd = to_date
ST = story()
T0 = TODAY
TS = iso(T0)
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
TEAM = {t['name']: t for t in team}
TEAMID = {t['staff_id']: t for t in team}
COORD_PHONE = TEAMID['NP-04']['phone']; ED_PHONE = TEAMID['NP-01']['phone']; DEV_PHONE = TEAMID['NP-02']['phone']; PM_PHONE = TEAMID['NP-03']['phone']; BK_PHONE = TEAMID['NP-08']['phone']
BOARD = board_rows()
CHAIR = [b for b in BOARD if b['role'] == 'Chair'][0]; CHAIR_PHONE = CHAIR['phone']
WD = lambda s: dd(s).strftime('%A')

# ---------------------------------------------------------------- volunteers
VOL = volunteer_rows()
VID = [v['volunteer_id'] for v in sorted(VOL, key=lambda v: v['volunteer_id'] != 'VL-344')]
def volunteers_d():
    return [nb(dict(volunteer_id=v['volunteer_id'], name=v['name'], phone=v['phone'], email=v['email'], role=key('vrole', v['role']), joined=v['joined'], status=key('vstatus', v['status']),
                    availability=key('avail', v['availability']), donor_id=v['donor_id'])) for v in sorted(VOL, key=lambda v: v['volunteer_id'] != 'VL-344')]


def roles_d(): return [dict(role=key('vrole', r['role']), program=key('sprog', r['program']), hours=r['hours']) for r in vol_roles]


# ---------------------------------------------------------------- slots and shifts (the whole history: hours last year and this year need it)
SLO = slot_rows()
SHF = shift_rows()
def slots_d():
    return [dict(slot_id=s['slot_id'], date=s['date'], weekday=key('wday', WD(s['date'])), program=key('sprog', s['program']), shift=key('shift', s['shift']), role=key('srole', s['role']),
                 needed=s['needed'], signed_up=s['signed_up'], hours=s['hours']) for s in SLO]


# the Shifts Worked sheet holds up to 3,000 recent shifts; earlier hours are carried in as totals (archived columns) so the figures stay the real totals
_SS = sorted(SHF, key=lambda s: s['date'])
_cut = _SS[-2990]['date']
LOGSTART = _cut if _SS[-2991]['date'] < _cut else iso(dd(_cut) + _dt.timedelta(days=1))
LOG = [s for s in SHF if s['date'] >= LOGSTART]
ARCH = [s for s in SHF if s['date'] < LOGSTART and s['status'] == 'Worked']
assert len(LOG) <= 3000
def shifts_d():
    return [dict(shift_id=s['shift_id'], date=s['date'], week=s['week'], month=s['month'], weekday=key('wday', WD(s['date'])), volunteer_id=s['volunteer_id'], volunteer=s['volunteer'],
                 role=key('srole', s['role']), program=key('sprog', s['program']), shift=key('shift', s['shift']), hours=s['hours'], status=key('shstatus', s['status'])) for s in LOG]


# tomorrow's list: booked shifts of the next three days (the list shows the days away)
_NEXT = [s for s in SHF if s['status'] == 'Booked' and T0 < dd(s['date']) <= T0 + _dt.timedelta(days=3)]
def tomorrow_d(): return [dict(shift_id=s['shift_id']) for s in _NEXT]


# open slots from tomorrow on
_GAPS = [s for s in SLO if dd(s['date']) > T0 and s['needed'] > s['signed_up']]
def gaps_d(): return [dict(slot_id=s['slot_id']) for s in _GAPS]


_Y0, _Y1 = iso(dt.date(Y, 1, 1)) if False else f'{Y}-01-01', f'{Y - 1}-01-01'
_ah = collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0, ''])   # this year, last year, earlier, shifts, last shift: all before the log
for x in ARCH:
    a = _ah[x['volunteer_id']]
    if x['date'] >= _Y0: a[0] += x['hours']
    elif x['date'] >= _Y1: a[1] += x['hours']
    else: a[2] += x['hours']
    a[3] += 1; a[4] = max(a[4], x['date'])
def hours_vol_d():
    return [nb(dict(volunteer_id=v, arch_year=_ah[v][0], arch_last=_ah[v][1], arch_prev=_ah[v][2], arch_shifts=_ah[v][3], arch_last_shift=_ah[v][4])) for v in VID]


def lapsed_d(): return [dict(volunteer_id=v['volunteer_id']) for v in sorted([v for v in VOL if v['status'] == 'Lapsed'], key=lambda v: -v['hours_worked'])]


_DON = {d['donor_id']: d for d in donor_rows()}
def givers_d():
    out = []
    for v in VOL:
        d = _DON.get(v['donor_id']) if v['donor_id'] else None
        if d: out.append(nb(dict(volunteer_id=v['volunteer_id'], total_given=d['total_given'], gifts=d['gifts'], last_gift=d['last_gift'])))
    return out


_am = collections.defaultdict(lambda: [0.0, 0])
_apm = collections.defaultdict(lambda: [0.0, 0])
for x in ARCH:
    _am[x['month']][0] += x['hours']; _am[x['month']][1] += 1
    _apm[(x['month'], x['program'])][0] += x['hours']; _apm[(x['month'], x['program'])][1] += 1
def hours_value_d(): return [dict(month=iso(add_months(month_start(0), -k)), arch_hours=_am[iso(add_months(month_start(0), -k))][0], arch_shifts=_am[iso(add_months(month_start(0), -k))][1]) for k in range(23, -1, -1)]
def new_by_month_d(): return [dict(month=iso(add_months(month_start(0), -k))) for k in range(23, -1, -1)]
def hours_pm_d():
    out = []
    for k in range(23, -1, -1):
        m = iso(add_months(month_start(0), -k))
        for p in SPROGS: out.append(dict(month=m, program=key('sprog', p), arch_hours=_apm[(m, p)][0], arch_shifts=_apm[(m, p)][1]))
    return out
def retention_d(): return [dict(year=yy, role=key('vrole', r)) for yy in (Y - 2, Y - 1, Y) for r in VOL_ROLES]


def availability_d(): return [dict(weekday=key('wday', w), shift=key('shift', s)) for w in WDAYS for s in SHIFTS]


# ---------------------------------------------------------------- members
MEM = [dict(m) for m in member_rows()]
for m in MEM:   # a member cannot join after the due date: keep the story in order
    if dd(m['joined']) > dd(m['due_date']): m['joined'] = iso(dd(m['due_date']) - _dt.timedelta(days=400))
MPHONE = {m['member_id']: fake_phone(i * 5 + 3) for i, m in enumerate(MEM)}
MLEVEL = {m['member_id']: m['level'] for m in MEM}
def members_d():
    return [nb(dict(member_id=m['member_id'], donor_id=m['donor_id'], member=m['member'], phone=MPHONE[m['member_id']], level=key('mlevel', m['level']), joined=m['joined'], due_date=m['due_date'],
                    last_paid=m['last_paid'], status=key('dues', m['status']), annual_dues=m['annual_dues'])) for m in MEM]


def dues_d():
    return [dict(dues_id=x['dues_id'], member_id=x['member_id'], member=x['member'], date=x['date'], month=x['month'], amount=x['amount'], year=x['year'], method=key('dmethod', x['method']),
                 level=key('mlevel', MLEVEL[x['member_id']])) for x in dues_rows()]


BENEFITS = {'Student': 'Newsletter and the members evening', 'Friend': 'Newsletter and a yearly members evening', 'Supporter': 'Newsletter, members evening and a seat at the open day',
            'Patron': 'All of Supporter plus a name on the thank-you wall', 'Business': 'All of Patron plus a mention at our events'}
def levels_d(): return [dict(level=l, annual_dues=d_, benefits=BENEFITS[l]) for l, d_ in (('Student', 25.0), ('Friend', 40.0), ('Supporter', 100.0), ('Patron', 250.0), ('Business', 500.0))]
def renewals_d(): return [dict(member_id=m['member_id']) for m in MEM if m['status'] != 'Paid']
def forecast_d(): return [dict(month=iso(add_months(month_start(0), k))) for k in range(12)]
_SW = [(0, 1, 'Switch on, 1 for membership pages, 0 to hide the figures'), (1, 30, 'Days before the due date that a notice goes out'), (2, 0.8, 'Your estimate of the share who renew, change it each year'),
       (3, 60, 'Days after the due date before a member counts as lapsed'), (4, 130, 'Your own goal for the number of members')]
def switch_d(): return [dict(item=key('mitem', MITEMS[i]), setting=v, note=n) for i, v, n in _SW]


if __name__ == '__main__':
    print(LOGSTART, len(LOG), len(ARCH), len(VOL), len(SLO), len(SHF), len(_NEXT), len(_GAPS), len(lapsed_d()), len(givers_d()), len(MEM), len(dues_d()), len(renewals_d()))
