"""Wedding suite part 3 (Vendors, Quotes and Contracts): label lists, the verdict-word registry and the list helpers."""
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
QSTATUS = ['Quote received', 'Shortlisted', 'Booked', 'Declined']
VSTAGE = ['Contacted', 'Quote received', 'Shortlisted', 'Booked', 'Declined']
OPTIONS = ['Option A', 'Option B', 'Option C']
PLACES = ['Hotel', 'Venue', 'Transport']
VNAMES = [x['vendor'] for x in vendor_rows()]
VCATS = [c_ for c_ in BUDGET_CATEGORIES if c_ in {x['category'] for x in vendor_rows()}]

BASE_LISTS = [
    L('category', 'Budget category', P(BUDGET_CATEGORIES)), L('vcat', 'Vendor category', P(VCATS)), L('payer', 'Payer', P(PAYERS)), L('vname', 'Vendor', P(VNAMES)),
    L('vstatus', 'Vendor status', P(VSTATUS)), L('qstatus', 'Quote status', P(QSTATUS)), L('vstage', 'Pipeline stage', P(VSTAGE)), L('option', 'Quote option', P(OPTIONS)),
    L('ckind', 'Contract item kind', P(CONTRACT_KINDS)), L('paykind', 'Payment kind', P(PAY_KINDS)), L('paystatus', 'Payment status', P(PAY_STATUS)),
    L('block', 'Run of show block', P(RUN_BLOCKS)), L('place', 'Place', P(PLACES)),
]
_M = {'category': K(BUDGET_CATEGORIES), 'vcat': K(VCATS), 'payer': K(PAYERS), 'vname': K(VNAMES), 'vstatus': K(VSTATUS), 'qstatus': K(QSTATUS), 'vstage': K(VSTAGE), 'option': K(OPTIONS),
      'ckind': K(CONTRACT_KINDS), 'paykind': K(PAY_KINDS), 'paystatus': K(PAY_STATUS), 'block': K(RUN_BLOCKS), 'place': K(PLACES)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])


# verdict and flag words: two lists of at most 30 values, filled in the order the words are first used
_VW = {'va': [], 'vb': [], 'vc': [], 'vd': []}
_VK = {}
def v(label):
    """token of a verdict word (list va or vb); the word is added to the list on first use"""
    if label not in _VK:
        name = next(n_ for n_ in ('va', 'vb', 'vc', 'vd') if len(_VW[n_]) < 30)
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
    for name, lab in (('va', 'Verdict words A'), ('vb', 'Verdict words B'), ('vc', 'Verdict words C'), ('vd', 'Verdict words D')):
        vals = _VW[name]
        if len(vals) == 1: vals = vals + [('Not used', 'not_used')]
        if vals: out.append(L(name, lab, [(k, l) for l, k in vals]))
    return out
