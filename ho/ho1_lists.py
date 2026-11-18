"""Home Management suite part 1 (Meal Plan and Grocery List): label lists shared by data, tables and tools."""
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


WEEKS2 = ['Week 1', 'Week 2']
USYS = ['Metric', 'Imperial']
FSTAT = ['ok', 'use soon', 'past date']

BASE = [
    ('cook', 'Cook', ['Adult 1', 'Adult 2', 'Child 1']), ('role', 'Role', ROLES), ('tgroup', 'Team group', TEAM_GROUPS), ('rcat', 'Recipe category', RECIPE_CATS), ('pref', 'Preference label', PREF_LABELS),
    ('slot', 'Meal slot', MEAL_SLOTS), ('unit', 'Unit', UNITS), ('section', 'Section', SECTIONS), ('place', 'Place', STORAGE_PLACES), ('shop', 'Shop', SHOPS), ('wday', 'Weekday', WEEKDAYS),
    ('shift', 'Shift', SHIFTS), ('lstatus', 'List status', ['Open', 'Bought']), ('wk', 'Plan week', WEEKS2), ('usys', 'Units', USYS)]
lists_base = [L(k, lab, P(v)) for k, lab, v in BASE]
_M = {k: K(v) for k, lab, v in BASE}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])


# ---- verdict and status words: formulas never write letters, so every word they print is a list label registered here (lists vd1..vd4, at most 30 labels each)
_VD, _VK = [], {}


def lbl(text):
    """list token of a verdict or status word; the word is added to the verdict lists on first use"""
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
