"""Therapy practice suite part 8 (Practice Profit, Cash Flow and Growth): label lists shared by data, tables and tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from th_core import *
from lib import L, LV


def P(labels):
    out, seen = [], set()
    for k, l in pairs(labels):
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


EMETH = ['Bank transfer', 'Card', 'Direct debit', 'Cash']
HPAY = ['Salary', 'Percentage split', 'Per session']
MSTAT = ['Not started', 'In progress', 'Done', 'At risk']
SCEN = ['Base', 'Best', 'Worst']
LIGHT = ['Green', 'Amber', 'Red']
WEEKS = ['Week %d' % i for i in range(1, 14)]
FIXKIND = ["Today's terms", 'Raise the fee', 'Change the split', 'Shorter set-up', 'Cheaper materials', 'Combined fix']
ROOMOPT = ['New treatment room', 'Online capacity', 'Sublet the room', 'Longer opening hours']
VERD = ['Healthy', 'Watch', 'Act now', 'Above the profit target', 'Below the profit target', 'Grow', 'Fix', 'Drop', 'Raise the fee to', 'Change the split', 'Stop offering it', 'Raise', 'Right',
        'Hold', 'Above target', 'Below target', 'Room use low', 'Room use healthy', 'Lean', 'In band', 'Heavy', 'Above break-even', 'Below break-even', 'Above the floor',
        'Below the floor in week', 'Reserve met', 'Build the reserve', 'Take the full draw', 'Take less', 'Wait']
VERD2 = ['Transfer now', 'Funded', 'Hire now', 'Add the room', 'Go online first', 'Add a room', 'Within budget', 'Over budget', 'Meets the profit target', 'Below the target', 'Fee first',
         'Below the floor', 'Done', 'On track', 'Due soon', 'Overdue', 'No break-even']
assert len(VERD) <= 30 and len(VERD2) <= 30
lists = [L('role', 'Role', P(ROLES)), L('team', 'Team', P(TEAMS)), L('paytype', 'Pay type', P(PAY_TYPES)), L('hpay', 'Hire pay type', P(HPAY)), L('clin', 'Clinician', P(CLINICIANS)),
         L('svcall', 'Service type', P(SERVICES)), L('room5', 'Room', P(ROOM_NAMES)), L('ecat', 'Expense category', P(EXPENSE_CATEGORIES)), L('paym', 'Payment method', P(EMETH)),
         L('taxst', 'Tax set-aside status', P(TAX_STATUS)), L('mstat', 'Milestone status', P(MSTAT)), L('scen', 'Scenario', P(SCEN)), L('light', 'Traffic light', P(LIGHT)),
         L('wk', 'Week', P(WEEKS)), L('fixkind', 'Fix kind', P(FIXKIND)), L('roomopt', 'Room option kind', P(ROOMOPT)), L('verd', 'Verdict', P(VERD)), L('verd2', 'Verdict, more', P(VERD2))]
assert len(lists) <= 20
_M = {'role': K(ROLES), 'team': K(TEAMS), 'paytype': K(PAY_TYPES), 'hpay': K(HPAY), 'clin': K(CLINICIANS), 'svcall': K(SERVICES), 'room5': K(ROOM_NAMES), 'ecat': K(EXPENSE_CATEGORIES),
      'paym': K(EMETH), 'taxst': K(TAX_STATUS), 'mstat': K(MSTAT), 'scen': K(SCEN), 'light': K(LIGHT), 'wk': K(WEEKS), 'fixkind': K(FIXKIND), 'roomopt': K(ROOMOPT),
      'verd': K(VERD), 'verd2': K(VERD2)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def vd(label): return LV('verd', _M['verd'][label]) if label in _M['verd'] else LV('verd2', _M['verd2'][label])
def lt(label): return tok('light', label)
