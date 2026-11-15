"""Childcare center suite part 3 (Staff, Rota and Ratios): label lists."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc_core import *
from lib import L, LV


def P(labels):
    out, seen = [], set()
    for k, l in pairs(labels):
        if not k[0].isalpha(): k = 'n_' + k
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


SHIFT_ROOMS = ROOMS + ['Kitchen']
SHIFT_STAFF = STAFF_NAMES + ['Tariq Anwar', 'Chiara Neri']
HOUR_L = ['%02d:00' % h for h in range(7, 18)]
WEEKN = ['Week %d' % i for i in range(1, 14)]
REQ_STATUS = ['Open', 'Filled', 'Not filled']
SCENARIO = ['Base', 'Best', 'Worst']
FLAG = ['Covered', 'Short', 'Over-staffed', 'Tight', 'Clash', 'No clash', 'Add a break', 'No break needed', 'Over the cap', 'Within the cap', 'Under contract',
        'Over contract', 'On contract', 'Done', 'Overdue', 'Due in 30 days', 'Due in 45 days', 'Due in 60 days', 'Later', 'Matches', 'Differs', 'Behind', 'On track', 'Add break cover', 'Keep the time']
VERDICT = ['Covered', 'Short by', 'Over-staffed by', 'No relief needed', 'Hire relief hours for', 'No clashes', 'breaks to move', 'Review the dearest room', 'Hire relief',
           'Use part-timers', 'Hold', 'Raise pays back', 'Raise does not pay back', 'All current', 'due soon', 'overdue', 'Rota covers', 'Add shifts', 'Within the cap',
           'Over the cap by', 'Swap is safe', 'Swap breaks the ratio', 'Place the floater in', 'Keep the cover', 'Above the target', 'Near the target', 'Below the target',
           'On track', 'Behind', 'Advertise now']
VERDICT2 = ['Wait', 'Pay matches', 'rows differ', 'Under-used', 'Fits', 'Over-used', 'Current rota holds', 'Add staff hours', 'at', 'room-hours checked',
            'Hire relief and stop cover', 'Cover is cheaper than relief', 'Above the center cost', 'At or below the center cost']
assert len(FLAG) <= 30 and len(VERDICT) <= 30 and len(VERDICT2) <= 30

lists = [
    L('role', 'Role', P(ROLES)), L('team', 'Team', P(TEAMS)), L('paytype', 'Pay type', P(PAY_TYPES)), L('payrole', 'Pay role', P(PAY_ROLES)), L('room', 'Room', P(ROOMS)),
    L('shiftroom', 'Shift room', P(SHIFT_ROOMS)), L('wday', 'Weekday', P(WEEKDAYS)), L('shiftkind', 'Shift kind', P(SHIFT_KINDS)), L('staff', 'Staff member', P(STAFF_NAMES)),
    L('shiftstaff', 'Rostered staff', P(SHIFT_STAFF)), L('hourl', 'Hour of the day', P(HOUR_L)), L('renewal', 'Renewal item', P(RENEWAL_KINDS)), L('cpd', 'Training kind', P(CPD_KINDS)),
    L('paystatus', 'Pay status', P(PAY_STATUS)), L('weekn', 'Week', P(WEEKN)), L('reqstatus', 'Request status', P(REQ_STATUS)), L('scenario', 'Scenario', P(SCENARIO)),
    L('flag', 'Check result', P(FLAG)), L('verdict', 'Decision', P(VERDICT)), L('verdict2', 'Decision, more', P(VERDICT2)),
]
_M = {'role': K(ROLES), 'team': K(TEAMS), 'paytype': K(PAY_TYPES), 'payrole': K(PAY_ROLES), 'room': K(ROOMS), 'shiftroom': K(SHIFT_ROOMS), 'wday': K(WEEKDAYS), 'shiftkind': K(SHIFT_KINDS),
      'staff': K(STAFF_NAMES), 'shiftstaff': K(SHIFT_STAFF), 'hourl': K(HOUR_L), 'renewal': K(RENEWAL_KINDS), 'cpd': K(CPD_KINDS), 'paystatus': K(PAY_STATUS), 'weekn': K(WEEKN),
      'reqstatus': K(REQ_STATUS), 'scenario': K(SCENARIO), 'flag': K(FLAG), 'verdict': K(VERDICT), 'verdict2': K(VERDICT2)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def fl(label): return tok('flag', label)
def vd(label): return tok('verdict', label)
def v2(label): return tok('verdict2', label)
YES = '{list:yesno.yes}'
NO = '{list:yesno.no}'
