"""Nonprofit suite part 6 (Volunteers and Members): label lists shared by data, tables and tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from np_core import *
from lib import L, LV


def P(labels):
    out, seen = [], set()
    for k, l in pairs(labels):
        if not k[:1].isalpha(): k = 'n' + k
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


WDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']   # the demo has no Sunday shifts
SHIFTS = ['Morning', 'Afternoon']
SPROGS = SHIFT_PROGRAMS                                                         # four programs plus Events and Office
SCENARIOS = ['Base', 'Best', 'Worst']
VPERIODS = ['This year', 'Last year']
MITEMS = ['Use membership pages', 'Notice days before due date', 'Share of due members who renew', 'Days after due date before lapsed', 'Members you aim for']
STAFF_NAMES = [s['name'] for s in staff]
SROLES = [r for r in VOL_ROLES if r != 'Web and data']                          # roles that have planned shifts
DMETHODS = ['Card', 'Check or cheque', 'Bank transfer']                          # how dues arrive

# verdict and state words live in three registered lists (a word is added the first time a formula asks for it)
_CKL = [[], [], []]
_CKK = ('ck1', 'ck2', 'ck3'); _CKT = ('State', 'Verdict word', 'Verdict phrase')
_CKM = {}


def ck(label):
    """list token for a verdict or state word, registered on first use"""
    label = label.lower() if label.lower() in _CKM else label
    if label.lower() not in _CKM:
        i = len(_CKM) % 3
        k = [x for x, _ in P([label])][0]
        while any(k == kk for kk, _ in _CKL[i]): k = k[:-1] + 'x'
        assert len(_CKL[i]) < 30
        _CKL[i].append((k, label)); _CKM[label.lower()] = (i, k)
    i, k = _CKM[label.lower()]
    return LV(_CKK[i], k)


lists = [
    L('vrole', 'Volunteer role', P(VOL_ROLES)), L('vstatus', 'Volunteer status', P(VOL_STATUS)), L('avail', 'Availability', P(AVAIL)), L('sprog', 'Program or area', P(SPROGS)),
    L('program', 'Program', P(PROGRAMS)), L('shift', 'Shift time', P(SHIFTS)), L('shstatus', 'Shift status', P(SHIFT_STATUS)), L('wday', 'Weekday', P(WDAYS)),
    L('mlevel', 'Member level', P(MEMBER_LEVELS)), L('dues', 'Dues status', P(DUES_STATUS)), L('dmethod', 'Dues method', P(DMETHODS)), L('srole', 'Shift role', P(SROLES)), L('scenario', 'Scenario', P(SCENARIOS)),
    L('vperiod', 'Period', P(VPERIODS)), L('mitem', 'Membership setting', P(MITEMS)),
]
_M = {'vrole': K(VOL_ROLES), 'vstatus': K(VOL_STATUS), 'avail': K(AVAIL), 'sprog': K(SPROGS), 'program': K(PROGRAMS), 'shift': K(SHIFTS), 'shstatus': K(SHIFT_STATUS), 'wday': K(WDAYS),
      'mlevel': K(MEMBER_LEVELS), 'dues': K(DUES_STATUS), 'dmethod': K(DMETHODS), 'srole': K(SROLES), 'scenario': K(SCENARIOS), 'vperiod': K(VPERIODS), 'mitem': K(MITEMS)}


def finish_lists():
    """append the three registered verdict lists (call once, after every formula was written)"""
    for i in range(3):
        if _CKL[i]: lists.append(L(_CKK[i], _CKT[i], list(_CKL[i])))
    assert len(lists) <= 20
    return lists


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
