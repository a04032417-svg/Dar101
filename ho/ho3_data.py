"""Home Management suite part 3: demo rows from ho_core (the full chore log, the chores and the work pattern window; aggregated tables are typed keys, the workbook calculates them)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ho3_lists import *

dd = to_date
ST = story()
WS0 = week_start(TODAY)                      # this week's Monday (the Settings week start is Monday in the demo)
FREQ_ORDER = {f: i for i, f in enumerate(FREQS)}
ROOM_ORDER = {r: i for i, r in enumerate(ROOMS)}
CH = chore_rows(); CHN = {c['chore']: c for c in CH}; CHI = {c['chore_id']: c for c in CH}
LOG = chore_log_rows()
EV = event_rows()
TRIP = [e for e in EV if e['event_id'] == ST['trip']][0]
VISIT = [e for e in EV if e['kind'] == 'Visit' and e['date'] >= iso(TODAY) and 'Grandparent' in e['title']][0]
SITTER = [e for e in EV if e['kind'] == 'Visit' and e['date'] >= iso(TODAY) and 'Babysitter' in e['title']][0]


def nxt(wd, after=1):
    d = TODAY + day(after)
    while d.weekday() != wd: d += day(1)
    return iso(d)


def team_d():
    nd = {'HO-05': (VISIT['date'], '', VISIT['start']), 'HO-06': (SITTER['date'], '', SITTER['start']), 'HO-13': (nxt(4), '', '08:05'), 'HO-14': (TRIP['date'], TRIP['end_date'], ''),
          'HO-16': (nxt(3), '', '17:45'), 'HO-12': (iso(NEXT_MON), '', '')}
    out = []
    for t in team:
        n = nd.get(t['member_id'], ('', '', ''))
        out.append(dict(member_id=t['member_id'], name=t['name'], role=key('role', t['role']), group=key('tgroup', t['group']), phone=t['phone'], note=t['note'], start=t['start'],
                        first_name=first_name(t['name']), next_date=n[0], end_date=n[1], at_time=n[2]))
    return out


def chores_d():
    return [dict(chore_id=c['chore_id'], chore=c['chore'], room=key('room', c['room']), frequency=key('freq', c['frequency']), minutes=c['minutes'], owner=('' if c['chore'] == 'Declutter the cupboards' else key('person', c['owner'])), points=c['points'],
                 hidden=bool(c['hidden']), paused=c['chore'].startswith('Mow the lawn'), last_done=c['last_done']) for c in CH]


def log_d():
    return [dict(log_id=x['log_id'], done=x['done'], chore_id=x['chore_id'], chore=x['chore'], room=key('room', x['room']), who=key('person', x['who']), minutes=x['minutes'], points=x['points'],
                 weekday=key('wday', WEEKDAYS[dd(x['done']).weekday()])) for x in LOG]


def rewards_d(): return [dict(reward_id=r['reward_id'], reward=r['reward'], points=r['points']) for r in reward_rows()]


def wp_d():
    lo, hi = iso(TODAY - day(60)), iso(TODAY + day(60))
    return [dict(shift_id=s['shift_id'], date=s['date'], weekday=key('wday', s['weekday']), adult1_late=s['adult1_late'], adult2_shift=key('shift', s['adult2_shift']), adults_free=s['adults_free'])
            for s in shift_rows() if lo <= s['date'] <= hi]


def cs_d():
    rows = sorted(CH, key=lambda c: (ROOM_ORDER[c['room']], FREQ_ORDER[c['frequency']], c['chore_id']))
    return [dict(chore_id=c['chore_id']) for c in rows]


def plan_d(): return [dict(rank=i) for i in range(1, 31)]


SWAPS = {'Do the weekly shop': 'adult_1', 'Clean the windows': 'adult_2', 'Sweep the hallway': 'child_1'}
def rot_d(): return [dict(chore_id=c['chore_id'], swap=SWAPS.get(c['chore'], '')) for c in CH]


def lw_d(): return [dict(wkn=w, person=key('person', p)) for w in range(1, 14) for p in PERSONS]
def fa_d(): return [dict(person=key('pgrp', p)) for p in PERSONS + ['Everyone']]
def hj_d(): return [dict(chore=c['chore']) for c in CH if c['hidden']]


def _wkpoints():
    """points per child and week 1..13 (week 13 is this week) from the full log"""
    out = {k: [0] * 14 for k in KIDS}
    for x in LOG:
        if x['who'] in out:
            k = (WS0 - week_start(dd(x['done']))).days // 7
            if 0 <= k <= 12: out[x['who']][13 - k] += x['points']
    return out


def cp_d():
    pts = _wkpoints(); plan = {'Child 1': {5: 30, 7: 45, 9: 60, 12: 45}, 'Child 2': {6: 30, 8: 45, 10: 60, 12: 45}}
    rows = []; n = 0; final = {}
    for k in KIDS:
        bal = 0
        for w in range(1, 14):
            bal += pts[k][w]
            sp = plan[k].get(w, 0)
            if sp > bal: sp = 0
            bal -= sp
            n += 1
            rows.append(dict(cp_id='CP-%02d' % n, wk=key('wk', 'Week %d' % w), child=key('kid', k), spent=sp))
        final[k] = bal
    cp_d.final = final
    return rows


def rl_d():
    rows = []; n = 0
    for k in KIDS:
        for r in reward_rows():
            n += 1; rows.append(dict(rl_id='RL-%02d' % n, child=key('kid', k), reward=r['reward']))
    return rows


def _last(name): return CHN[name]['last_done']
def ld_d():
    # load type, usual day, who, loads a week, minutes handling per load, interval days, last changed
    spec = [('Colours', 'Saturday', 'Adult 2', 1.5, 15, 7, _last('Laundry, colours')), ('Whites', 'Sunday', 'Adult 1', 1, 15, 7, _last('Laundry, whites')),
            ('Towels', 'Wednesday', 'Adult 2', 1, 15, 7, _last('Wash the towels')), ('Bed linen, main bedroom', 'Friday', 'Adult 1', 1, 25, 7, _last('Change the bed linen')),
            ('Bed linen, kids rooms', 'Saturday', 'Adult 2', 0.5, 25, 14, _last('Change the kids bed linen')), ('School uniform', 'Sunday', 'Adult 1', 1, 10, 7, ago(3)),
            ('Sports kit', 'Thursday', 'Child 1', 1, 10, 7, ago(5)), ('Dark clothes', 'Tuesday', 'Adult 1', 1, 15, 7, ago(9)), ('Tea towels and cloths', 'Monday', 'Adult 2', 0.5, 10, 14, ago(12)),
            ('Pet bedding', 'Saturday', 'Adult 2', 0.25, 20, 30, _last('Wash the pet bedding')), ('Curtains', 'Sunday', 'Adult 2', 0.1, 40, 91, _last('Wash the curtains')),
            ('Delicates', 'Wednesday', 'Adult 1', 0.5, 10, 14, ago(10))]
    return [dict(load=key('ltype', a), usual_day=key('wday', b), who=key('person', c), loads_wk=d, minutes=e, interval_days=f, last_changed=g) for a, b, c, d, e, f, g in spec]


def hm_d(): return [dict(month=iso(m)) for m in months25()]
def dm_d(): return [dict(wk=key('wk', w)) for w in WEEKS]
def st_d(): return [dict(person=key('pgrp', p)) for p in PERSONS + ['Everyone']]


def aw_d():
    m = NEXT_MON
    spec = [(m, 'Adult 2', 24, 'Training course away'), (m + day(1), 'Adult 2', 24, 'Training course away'), (m + day(2), 'Adult 2', 24, 'Training course away'),
            (m + day(3), 'Adult 2', 24, 'Training course away'), (m + day(4), 'Adult 2', 10, 'Back in the afternoon'),
            (m + day(9), 'Child 1', 10, 'School trip'), (m + day(10), 'Child 1', 10, 'School trip'), (m + day(12), 'Child 2', 14, 'Sleepover at a friend home'),
            (m + day(14), 'Child 2', 8, 'Day with the grandparent'), (m + day(16), 'Adult 1', 24, 'Work trip'), (m + day(17), 'Adult 1', 12, 'Work trip, back in the evening'),
            (m + day(21), 'Adult 1', 12, 'Conference day')]
    return [dict(away_id='AW-%02d' % (i + 1), day=iso(d), person=key('person', p), hours=h, note=n) for i, (d, p, h, n) in enumerate(spec)]


def rm_d(): return [dict(room=key('room', r)) for r in ROOMS]
def fq_d(): return [dict(frequency=key('freq', f)) for f in FREQS]


if __name__ == '__main__':
    for f in (team_d, chores_d, log_d, rewards_d, wp_d, cs_d, plan_d, rot_d, lw_d, fa_d, hj_d, cp_d, rl_d, ld_d, hm_d, dm_d, st_d, aw_d, rm_d, fq_d): print(f.__name__, len(f()))
    print(cp_d.final, _wkpoints())
