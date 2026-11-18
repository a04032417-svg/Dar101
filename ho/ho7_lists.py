"""Home Management suite part 7 (Documents, Contacts and Renewals): label lists shared by data, tables and tools."""
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


KEPT = ['Filing cabinet, drawer 2', 'Fireproof box', 'Document box, folder A', 'Document box, folder B', 'Desk tray', 'Online, saved copy']
HAND = ['Adult 1', 'Adult 2', 'A trade']
AHEAD = ['This month', 'Next month'] + ['In %d months' % i for i in range(2, 12)]
QTR = ['Months 1 to 3', 'Months 4 to 6', 'Months 7 to 9', 'Months 10 to 12']
RTYPES = ['Documents', 'Contracts and policies', 'Warranties', 'Vehicles', 'Pets', 'Home tasks']
KHOLD = ['Neighbour', 'Dog walker', 'Babysitter', 'Grandparent', 'Carpool family', 'Landlord or agent']
SSRC = ['Team', 'Home routines', 'Where things are', 'Contacts']
PETKINDS = ['Grooming', 'Vet visit', 'Vaccination visit', 'Nail trim', 'Food bag due', 'Bath']

BASE = [
    ('role', 'Role', ROLES), ('epeople', 'Holder', EVENT_PEOPLE), ('dkind', 'Document kind', DOC_KINDS), ('dstatus', 'Document status', DOC_STATUS), ('kept', 'Kept where', KEPT),
    ('hand', 'Handled by', HAND), ('ckind', 'Contact kind', CONTACT_KINDS), ('vkind', 'Vehicle date kind', VEH_KINDS), ('ptask', 'Pet date kind', PETKINDS), ('ahead12', 'Months ahead', AHEAD),
    ('qtr4', 'Quarter ahead', QTR), ('rtype', 'Renewal type', RTYPES), ('kholder', 'Key holder', KHOLD), ('ssrc', 'Sitter source', SSRC), ('mname', 'Month', MONTH_NAMES)]
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
