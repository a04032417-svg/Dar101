"""Childcare center suite part 8 (Business Health and Planning): label lists shared by data, tables, tools. Verdict words are registered with V() and become lists v1..v4."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc_core import *
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


SCNROW = ['Enrol two more infants', 'Enrol three more infants', 'Enrol one infant', 'Lose a family', 'Lose two families', 'Open a part-time day', 'Enrol five school-age children',
          'Fill Twos to capacity', 'Fill Preschool to capacity', 'Toddlers one child fewer', 'Hire relief for Toddlers', 'Drop a school-age day']
BASIS = ['Year to date against last year', 'Last 6 months against the 6 before', 'Last 3 months against the 3 before']
YMEASURE = ['Revenue', 'Costs', 'Profit', 'Profit margin, percent', 'Occupancy, percent', 'Staff cost share, percent', 'Revenue per child a month', 'Cash at the end of the period']
HOMERULE = ['Rooms share', 'Hours share', 'Rooms and hours', 'Whole amount', 'Not shared']
OVRULE = ['As entered', 'Capacity share', 'Children share']
SCEN = ['Base', 'Best', 'Worst']
PERSON = ['Marisol', 'Tobias', 'Eleni', 'Dae-ho', 'Aaliyah', 'Mateusz', 'Ngozi', 'Camille', 'Sofia', 'Rajesh Menon', 'Thandiwe Nkosi', 'Dae-ho Park', 'Eleni Papadakis']

# ---- verdict words: a formula never types a word, it points at the list cell
_V = {}          # label -> (list key, value key)
_VN = {}         # list key -> labels in order


def V(label):
    """token for a verdict or check word; the word is added to the verdict lists on first use (30 words a list)"""
    if label not in _V:
        n = sum(len(v) for v in _VN.values())
        lk = 'v%d' % (n // 30 + 1)
        labs = _VN.setdefault(lk, [])
        k = ''.join(ch if ch.isalnum() else '_' for ch in label.lower()).strip('_')
        while '__' in k: k = k.replace('__', '_')
        k = k[:21]
        used = {_V[x][1] for x in labs}
        while k in used: k = k[:-1] + 'x'
        _V[label] = (lk, k); labs.append(label)
    lk, k = _V[label]
    return LV(lk, k)


def verdict_lists():
    out = []
    for lk in sorted(_VN):
        out.append({"key": lk, "label": {'v1': 'Verdict A', 'v2': 'Verdict B', 'v3': 'Verdict C', 'v4': 'Verdict D'}[lk],
                    "values": [{"key": _V[x][1], "label": x} for x in _VN[lk]]})
    return out


def base_lists():
    return [L('room', 'Room', P(ROOMS)), L('schedule', 'Schedule', P(SCHEDULES)), L('expcat', 'Expense category', P(EXPENSE_CATEGORIES)), L('paytype', 'Pay type', P(PAY_TYPES)),
            L('payrole', 'Pay role', P(PAY_ROLES)), L('scnrow', 'Scenario', P(SCNROW)), L('basis', 'Review period', P(BASIS)), L('ymeasure', 'Measure', P(YMEASURE)),
            L('homerule', 'Home-use rule', P(HOMERULE)), L('ovrule', 'Overhead rule', P(OVRULE)), L('scen', 'Case', P(SCEN)), L('person', 'Person', P(PERSON))]


_M = {'room': K(ROOMS), 'schedule': K(SCHEDULES), 'expcat': K(EXPENSE_CATEGORIES), 'paytype': K(PAY_TYPES), 'payrole': K(PAY_ROLES), 'scnrow': K(SCNROW), 'basis': K(BASIS),
      'ymeasure': K(YMEASURE), 'homerule': K(HOMERULE), 'ovrule': K(OVRULE), 'scen': K(SCEN), 'person': K(PERSON)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
