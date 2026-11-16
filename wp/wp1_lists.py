"""Wedding suite part 1 (Budget, Payments and Cash Plan): label lists, the verdict-word registry and the list helpers."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wp_core import *
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


VSTATUS = ['Quote received', 'Shortlisted', 'Booked']
PAYERX = PAYERS + ['Other relatives', 'Friends']
VNAMES = [x['vendor'] for x in vendor_rows()]
PAREAS = ['Venue and setting', 'Food and drink', 'Photo and video', 'Music and dancing', 'Flowers and decor', 'Attire', 'Invitations and paper', 'Extra events', 'Guest comfort', 'Reserve and tips']
CTYPES = ['Per guest', 'Fixed']
DOPTS = ['Option A: current Saturday', 'Option B: a Friday, three weeks later', 'Option C: a Saturday in September']
CSTEPS = ['Remove %d guests' % n for n in range(0, 60, 5)]

BASE_LISTS = [
    L('category', 'Budget category', P(BUDGET_CATEGORIES)), L('payer', 'Payer', P(PAYERS)), L('payerx', 'Payer or helper', P(PAYERX)), L('source', 'Funding source', P(FUND_SOURCES)), L('fstatus', 'Funding status', P(FUND_STATUS)),
    L('paykind', 'Payment kind', P(PAY_KINDS)), L('paystatus', 'Payment status', P(PAY_STATUS)), L('method', 'Payment method', P(METHODS)), L('owner', 'Owner', P(OWNERS)),
    L('vstatus', 'Vendor status', P(VSTATUS)), L('hstatus', 'Hidden cost status', P(HIDDEN_STATUS)), L('tipbasis', 'Tip basis', P(TIP_BASIS)), L('parea', 'Priority area', P(PAREAS)),
    L('ctype', 'Cost type', P(CTYPES)), L('dopt', 'Date option', P(DOPTS)), L('cstep', 'Cut step', P(CSTEPS)), L('vname', 'Vendor', P(VNAMES)),
]
_M = {'category': K(BUDGET_CATEGORIES), 'payer': K(PAYERS), 'payerx': K(PAYERX), 'source': K(FUND_SOURCES), 'fstatus': K(FUND_STATUS), 'paykind': K(PAY_KINDS), 'paystatus': K(PAY_STATUS), 'method': K(METHODS),
      'owner': K(OWNERS), 'vstatus': K(VSTATUS), 'hstatus': K(HIDDEN_STATUS), 'tipbasis': K(TIP_BASIS), 'parea': K(PAREAS), 'ctype': K(CTYPES), 'dopt': K(DOPTS), 'cstep': K(CSTEPS), 'vname': K(VNAMES)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])


# verdict and flag words: two lists of at most 30 values, filled in the order the words are first used
_VW = {'va': [], 'vb': []}
_VK = {}
def v(label):
    """token of a verdict word (list va or vb); the word is added to the list on first use"""
    if label not in _VK:
        name = 'va' if len(_VW['va']) < 30 else 'vb'
        used = {k for _, k in _VW[name]}
        k = ''.join(ch if ch.isalnum() else '_' for ch in label.lower()).strip('_')
        while '__' in k: k = k.replace('__', '_')
        k = k[:21].rstrip('_')
        if not k[:1].isalpha(): k = 'w' + k
        while k in used: k = k[:-1] + 'x'
        _VW[name].append((label, k)); _VK[label] = (name, k)
    n, k = _VK[label]
    return LV(n, k)


def verdict_lists():
    out = []
    for name, lab in (('va', 'Verdict words A'), ('vb', 'Verdict words B')):
        vals = _VW[name]
        if len(vals) == 1: vals = vals + [('Not used', 'not_used')]
        if vals: out.append(L(name, lab, [(k, l) for l, k in vals]))
    return out
