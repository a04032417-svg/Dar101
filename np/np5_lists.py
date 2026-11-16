"""Nonprofit suite part 5 (Programs and People Served): label lists shared by data, tables and tools."""
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


SPROGRAMS = PROGRAMS + ['Shared']
STAFF_NAMES = [s['name'] for s in staff]
OUTCOME_NAMES = []
for _p in PROGRAMS:
    for _o in OUTCOMES[_p]:
        if _o not in OUTCOME_NAMES: OUTCOME_NAMES.append(_o)
YEARS = [str(Y - 2), str(Y - 1), str(Y)]
RPERIODS = ['This year', 'Last year', 'Last 12 months', 'This quarter', 'Last quarter']
PACES = ['Half your usual pace', 'Your usual pace', 'One and a half times']
ST_STATUS = ['Active', 'Waiting', 'Completed', 'Left']

CK1 = ['Full', 'Healthy', 'Quiet', 'Off season', 'On target', 'Behind target', 'Rising', 'Steady', 'Falling', 'Up', 'Same', 'Down', 'Better', 'Worse',
       'Grow', 'Hold', 'Review', 'Funded', 'Short', 'On file', 'Not on file', 'Rule is complete', 'Rule is off', 'Room free', 'Add a session', 'Offer a place',
       'Keep waiting', 'Nothing to compare', 'Call this week', 'Close the record']
CK2 = ['Nobody is missing', 'Sentence ready, check the numbers', 'Ready to paste', 'Complete', 'Rule applied to', 'Cost per participant falls to', 'Cost per participant is',
       'Expect next quarter, your estimate', 'No forecast yet', 'Behind by', 'Target reached', 'Needed each month', 'Short by', 'Clears in', 'Add', 'places', 'session(s) on', 'weeks',
       'Missing', 'No shared cost that month', 'Outcome not found', 'Pick an outcome of this program', 'Funded', 'Nothing missing', 'Better than last year', 'Same as last year',
       'Worse than last year', 'List clears now', 'Add a session', 'Hold']
CK3 = ['people served', 'visits', 'sessions', 'outcomes', 'cost', 'volunteer hours', 'Grow', 'Hold', 'Review', 'Off season', 'No sessions on file', 'Cost per participant is not known',
       'a month', 'per person', 'more', 'less']
SW = ['served', 'people with', 'visits in', 'sessions, at a cost of', 'per participant, with', 'volunteer hours']

lists = [
    L('program', 'Program', P(PROGRAMS)), L('sprogram', 'Program or shared', P(SPROGRAMS)), L('pstat', 'Participant status', P(ST_STATUS)), L('cstat', 'Contact status', P(CONTACT_STATUS)),
    L('category', 'Expense category', P(EXPENSE_CATEGORIES)), L('function', 'Function', P(FUNCTIONS)), L('fund', 'Fund', P([f['fund'] for f in funds])), L('staff', 'Staff member', P(STAFF_NAMES)),
    L('outcome', 'Outcome', P(OUTCOME_NAMES)), L('wday', 'Weekday', P(WEEKDAYS)), L('syear', 'Year', P(YEARS)), L('rperiod', 'Report period', P(RPERIODS)), L('pace', 'Places freed a week', P(PACES)),
    L('ck1', 'Status', P(CK1)), L('ck2', 'Verdict', P(CK2)), L('ck3', 'Verdict word', P(CK3)), L('sw', 'Sentence word', P(SW)),
]
assert len(lists) <= 20 and all(len(l['values']) <= 30 for l in lists)
_M = {'program': K(PROGRAMS), 'sprogram': K(SPROGRAMS), 'pstat': K(ST_STATUS), 'cstat': K(CONTACT_STATUS), 'category': K(EXPENSE_CATEGORIES), 'function': K(FUNCTIONS),
      'fund': K([f['fund'] for f in funds]), 'staff': K(STAFF_NAMES), 'outcome': K(OUTCOME_NAMES), 'wday': K(WEEKDAYS), 'syear': K(YEARS), 'rperiod': K(RPERIODS), 'pace': K(PACES),
      'ck1': K(CK1), 'ck2': K(CK2), 'ck3': K(CK3), 'sw': K(SW)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def c1(label): return tok('ck1', label)
def c2(label): return tok('ck2', label)
def c3(label): return tok('ck3', label)
def sw(label): return tok('sw', label)
