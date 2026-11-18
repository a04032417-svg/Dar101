"""Home Management suite part 6 (Family Calendar, Pets and Vehicles): label lists shared by data, tables and tools."""
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


TNAMES = ['Autumn term', 'Winter break', 'Spring term', 'Mid-term break', 'Spring break', 'Summer term', 'Summer break']
WEEKS = ['Week %d' % i for i in range(1, 13)]
STAYROOMS = ['Guest room', 'Study sofa bed', 'Child 1 room, camp bed', 'Child 2 room, camp bed', 'Living room sofa']
ADULTS = ['Adult 1', 'Adult 2']

BASE = [
    ('wday', 'Weekday', WEEKDAYS), ('epeople', 'Person', EVENT_PEOPLE), ('driver', 'Driver', DRIVERS), ('ekind', 'Event kind', EVENT_KINDS), ('tkind', 'Term or break', TERM_KINDS),
    ('shift', 'Shift', SHIFTS), ('role', 'Role', ROLES), ('gstatus', 'Gift status', GIFT_STATUS), ('ptask', 'Pet task', PET_TASKS), ('vkind', 'Vehicle kind', VEH_KINDS),
    ('adult', 'Adult', ADULTS), ('tname', 'Term name', TNAMES), ('wk12', 'Week ahead', WEEKS), ('stayroom', 'Stay room', STAYROOMS)]
lists_base = [L(k, lab, P(v)) for k, lab, v in BASE]
_M = {k: K(v) for k, lab, v in BASE}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])


# ---- verdict and status words: formulas never write letters, so every word they print is a list label registered here (lists vd1.., at most 30 labels each)
_VD, _VK = [], {}


def lbl(text):
    """list token of a verdict or status word; the word is added to the verdict lists on first use"""
    assert len(text) <= 60, text
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
