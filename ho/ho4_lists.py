"""Home Management suite part 4 (Home Maintenance and Repairs): label lists shared by data, tables and tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho_core import *            # ho_core after lib: TODAY, ago, ahead, iso, month_start, add_months follow HO_TODAY
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


STATUS = ['OK', 'Due soon', 'Overdue']
MWHO = ['Adult 1', 'Adult 2', 'A trade']
AHEAD = ['This month', 'Next month'] + ['In %d months' % i for i in range(2, 12)]
CTRADES = ['Plumber', 'Electrician', 'Heating engineer', 'Vet clinic', 'Car mechanic', 'School office', 'Carpool family', 'Neighbour', 'Landlord or agent', 'Dog walker', 'Roofer',
           'Locksmith', 'Pest controller', 'Window cleaner', 'Tree surgeon', 'Appliance repairer', 'Handyman', 'Painter and decorator', 'Cleaner', 'Glazier', 'Tiler', 'Builder',
           'Gardener', 'Cousin with a spare key']
PERSONS4 = ['Adult 1', 'Adult 2', 'Child 1', 'Child 2']
ISSUES = ['Leak or blocked drain', 'Heating or hot water', 'Socket, light or wiring', 'Appliance stopped', 'Roof or gutter', 'Door or lock', 'Pests', 'Fence, gate or shelf',
          'Window or glass', 'Tiles or grout']
BASE = [('role', 'Role', ROLES), ('tgroup', 'Team group', TEAM_GROUPS), ('area', 'Area', MAINT_AREAS), ('season', 'Season', SEASONS), ('mwho', 'Assigned', MWHO), ('trade', 'Trade called', TRADES),
        ('rstatus', 'Repair status', REPAIR_STATUS), ('room', 'Room', ROOMS), ('ckind', 'Contact kind', CONTACT_KINDS), ('ctrade', 'Trade or contact type', CTRADES), ('mstat', 'Status', STATUS),
        ('ahead12', 'Month ahead', AHEAD), ('mname', 'Month', MONTH_NAMES), ('issue', 'Kind of issue', ISSUES), ('person', 'Person', PERSONS4)]
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
