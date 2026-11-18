"""Home Management suite part 5 (Home Inventory and Warranties): label lists shared by data, tables and tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ho_core import *
from lib import L, LV


def P(labels):
    out, seen = [], set()
    for k, l in pairs(labels):
        if not k[:1].isalpha(): k = 'n' + k
        if len(k) < 2: k = k + '_u'
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


KEPT = ['Kitchen drawer, manuals folder', 'Filing box A, folder 3', 'Shed shelf, blue box', 'Online, saved copy', 'Filing box B, folder 1', 'Utility room shelf', 'Garage, manual tray', 'With the item', 'None kept']
RITEMS = ['Washing machine', 'Tumble dryer', 'Dishwasher', 'Fridge freezer', 'Oven', 'Induction hob', 'Extractor hood', 'Boiler or furnace', 'Chest freezer', 'Television', 'Sofa', 'Mattress',
          'Lawn mower', 'Laptop, Adult 1', 'Child 1 laptop for school', 'Microwave', 'Vacuum cleaner', 'Robot vacuum', 'Stand mixer', 'Pressure washer']
YEARS = [str(Y - 10 + i) for i in range(11)]
AHEAD13 = ['This month', 'Next month'] + ['In %d months' % i for i in range(2, 13)]
ABANDS = ['Under 1 year', '1 to 2 years', '2 to 4 years', '4 to 6 years', '6 to 8 years', '8 years or more']
PBANDS = ['Under 50', '50 to 99', '100 to 249', '250 to 499', '500 to 999', '1000 and over']

BASE = [
    ('role', 'Role', ROLES), ('room', 'Room', ROOMS), ('icat', 'Item category', ITEM_CATS), ('kept', 'Manual place', KEPT), ('trade', 'Trade', TRADES), ('rstatus', 'Repair status', REPAIR_STATUS),
    ('ritem', 'Replacement item', RITEMS), ('pyear', 'Purchase year', YEARS), ('ahead13', 'Months ahead', AHEAD13), ('aband', 'Age band', ABANDS), ('pband', 'Price band', PBANDS), ('mname', 'Month', MONTH_NAMES)]
lists_base = [L(k, lab, P(v)) for k, lab, v in BASE]
_M = {k: K(v) for k, lab, v in BASE}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])


# ---- verdict and status words: formulas never write letters, so every word they print is a list label registered here (lists vd1.., at most 30 labels each)
_VD, _VK = [], {}


def lbl(text):
    """list token of a verdict or status word; the word is added to the verdict lists on first use"""
    assert len(text) <= 40, text
    if text not in _VK:
        n = len(_VD); lst = 'vd%d' % (n // 30 + 1)
        k = ''.join(ch if ch.isalnum() else '_' for ch in text.lower()).strip('_')
        while '__' in k: k = k.replace('__', '_')
        k = k[:19] or 'w'
        if not k[:1].isalpha(): k = 'w' + k
        used = {v[1] for v in _VD if v[0] == lst}
        i = 0; k0 = k
        while k in used: i += 1; k = k0[:17] + 'x%d' % i
        _VD.append((lst, k, text)); _VK[text] = (lst, k)
    lst, k = _VK[text]
    return '{list:%s.%s}' % (lst, k)


def verdict_lists():
    out = []
    for lst in sorted({v[0] for v in _VD}):
        out.append(L(lst, 'Verdict words %s' % lst[2:], [(k, t) for l, k, t in _VD if l == lst]))
    return out
