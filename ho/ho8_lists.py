"""Home Management suite part 8 (Projects, Hosting and Declutter): label lists shared by data, tables and tools."""
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


POWNER = ['Adult 1', 'Adult 2', 'Child 1', 'Child 2', 'A trade']
HOWN = ['Adult 1', 'Adult 2', 'Child 1']
MSECT = ['Fruit and veg', 'Dairy and eggs', 'Meat and fish', 'Dry goods and tins']
PROJ_NAMES = [p['project'] for p in project_rows()] + ['Move to the new home']
ORGS = ['Employer and payroll', 'Banks and card providers', 'Insurance providers', 'Energy and water suppliers', 'Internet and phone providers', 'Post redirect service',
        'Schools and childcare', 'Vehicle and licence offices', 'Local council or town office', 'Vet clinic and pet registration', 'Subscriptions and memberships', 'Family and friends']
YMEAS = ['Maintenance tasks done', 'Maintenance tasks overdue at year end', 'Repairs logged', 'Repair cost line per repair', 'Adult 1 chore hours', 'Points away from the agreed chore share',
         'Weeks the children met the points goal', 'Warranties that ended with a fault open', 'Dinners cooked per week', 'Share of planned dinners cooked, percent', 'Projects finished',
         'Project tasks done', 'Areas decluttered, of 10', 'Items donated']

BASE = [('role', 'Role', ROLES), ('pkind', 'Project kind', PROJECT_KINDS + ['Move']), ('pstage', 'Project stage', PROJECT_STAGES), ('tstatus', 'Task status', TASK_STATUS), ('powner', 'Task owner', POWNER),
        ('hown', 'Hosting owner', HOWN), ('rsvp', 'RSVP', RSVP), ('gprefs', 'Guest preference label', GUEST_PREFS), ('decision', 'Decision', DECISIONS), ('room', 'Room or area', ROOMS),
        ('pj', 'Project', PROJ_NAMES), ('orgtype', 'Organisation type', ORGS), ('ymeasure', 'Year in review measure', YMEAS), ('msect', 'Menu section', MSECT),
        ('rcat', 'Recipe category', RECIPE_CATS), ('pref', 'Preference label', PREF_LABELS), ('unit', 'Unit', UNITS)]
lists_base = [L(k, lab, P(v)) for k, lab, v in BASE]
_M = {k: K(v) for k, lab, v in BASE}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])


# ---- verdict and status words: formulas never write letters, so every word they print is a list label registered here (lists vd1..vd3, at most 30 labels each)
_VD, _VK = [], {}


def lbl(text):
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
