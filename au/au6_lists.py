"""Author and self-publisher suite part 6 (Series, Title and Pen-Name Performance): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from au_core import *
from lib import L, LV


def P(labels):
    """pairs() with list keys cut to 21 characters, unique inside the list"""
    out, seen = [], set()
    for k, l in pairs(labels):
        if not k[:1].isalpha(): k = 'n' + k
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


TITLE_NAMES = [t['title'] for t in title_rows()]
SERIES4 = SERIES[:4]
XPEN = ['Shared'] + PEN_NAMES
BSTEP = ['Step %d' % i for i in range(1, 6)]
BOOKNO = ['Book %d' % i for i in range(1, 7)]
TSTEP = ['Step %d' % i for i in range(1, 13)]
RULES = ['Equal', 'By revenue', 'By titles']
DVERDICT = ['Keep', 'Reprice', 'Repackage', 'Retire']
VL1 = ['Healthy step', 'Below the threshold', 'Passes', 'Fails', 'Not tested', 'Growing', 'Flat', 'Declining', 'Too new to judge', 'Fix first', 'Fix next', 'Fix later',
       'Target reached', 'Reachable', 'Far away', 'Book 1', 'Later book', 'Standalone book', 'Box set', 'Not released', 'Make the box set', 'Skip the box set', 'Test first']
VL2 = ['Not released yet', 'Cost not earned back', 'Fails the return test', 'Sales are falling, test a price', 'Earns little, no series needs it', 'Earns its cost and holds its sales']
VL3 = ['Build the series', 'Stretch', 'Stop at book', 'Do not start the series', 'more books at this pace', 'Target is far', 'Step is healthy', 'Book 2 needs work', 'Step needs work',
       'No data for this step', 'Fix first:', 'Ads justified up to a cost per sale of', 'Ads cost more than the ceiling', 'Lower the price', 'Keep the price', 'Raise the price', 'Feed pen name', 'Balanced',
       'Fairest rule is', 'Bundle adds', 'Bundle swaps']
VL4 = ['Pen name', 'is growing faster', 'Growth is level', 'Backlist carries', 'Frontlist carries', 'Diversify', 'Dependence is ok', 'Expected to earn back', 'May not earn back',
       'Finish the series', 'Start a new series']
_all = VL1 + VL2 + VL3 + VL4
assert len(set(_all)) == len(_all), 'verdict labels must be unique across the four lists'
assert max(len(VL1), len(VL2), len(VL3), len(VL4)) <= 30

lists = [
    L('role', 'Role', P(ROLES)), L('team', 'Team', P(TEAMS)), L('paytype', 'Pay type', P(PAY_TYPES)), L('penname', 'Pen name', P(PEN_NAMES)), L('series', 'Series', P(SERIES)),
    L('series4', 'Series with books in order', P(SERIES4)), L('genre', 'Genre', P(GENRES)), L('tstatus', 'Title status', P(TITLE_STATUS)), L('expcat', 'Expense category', P(EXPENSE_CATEGORIES)),
    L('xpen', 'Cost belongs to', P(XPEN)), L('bstep', 'Series step', P(BSTEP)), L('bookno', 'Book number', P(BOOKNO)), L('tstep', 'Target step', P(TSTEP)), L('rule', 'Shared cost rule', P(RULES)),
    L('dverdict', 'Catalogue decision', P(DVERDICT)), L('vl1', 'Check result', P(VL1)), L('vl2', 'Decision reason', P(VL2)), L('vl3', 'Verdict A', P(VL3)), L('vl4', 'Verdict B', P(VL4)),
    L('title', 'Title', P(TITLE_NAMES)),
]
assert len(lists) <= 20
_M = {'role': K(ROLES), 'team': K(TEAMS), 'paytype': K(PAY_TYPES), 'penname': K(PEN_NAMES), 'series': K(SERIES), 'series4': K(SERIES4), 'genre': K(GENRES), 'tstatus': K(TITLE_STATUS),
      'expcat': K(EXPENSE_CATEGORIES), 'xpen': K(XPEN), 'bstep': K(BSTEP), 'bookno': K(BOOKNO), 'tstep': K(TSTEP), 'rule': K(RULES), 'dverdict': K(DVERDICT), 'vl1': K(VL1), 'vl2': K(VL2),
      'vl3': K(VL3), 'vl4': K(VL4), 'title': K(TITLE_NAMES)}
_VL = {}
for _l in ('vl1', 'vl2', 'vl3', 'vl4'):
    for _lab in _M[_l]: _VL[_lab] = _l
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def v(label): return tok(_VL[label], label)            # token of a verdict or check label
