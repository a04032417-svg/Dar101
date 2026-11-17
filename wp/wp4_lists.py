"""Wedding suite part 4 (Master Timeline, Checklist and Task Owners): label lists, the verdict-word registry and the list helpers."""
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


WTYPES = ['Local wedding', 'Destination wedding', 'Small plus a party', 'Multi-event wedding', 'Home or garden wedding']
VNAMES = [x['vendor'] for x in vendor_rows()]

BASE_LISTS = [
    L('owner', 'Owner', P(OWNERS)), L('area', 'Task area', P(TASK_AREAS)), L('when', 'Month-out bucket', P(WHEN)), L('tstatus', 'Task status', P(TASK_STATUS)),
    L('wtype', 'Wedding type', P(WTYPES)), L('team', 'Team', P(TEAMS)), L('role', 'Role', P(ROLES)), L('prole', 'Party role', P(PARTY_ROLES)), L('attire', 'Attire status', P(ATTIRE_STATUS)),
    L('paykind', 'Payment kind', P(PAY_KINDS)), L('paystatus', 'Payment status', P(PAY_STATUS)), L('ckind', 'Contract item kind', P(CONTRACT_KINDS)), L('vname', 'Vendor', P(VNAMES)),
]
_M = {'owner': K(OWNERS), 'area': K(TASK_AREAS), 'when': K(WHEN), 'tstatus': K(TASK_STATUS), 'wtype': K(WTYPES), 'team': K(TEAMS), 'role': K(ROLES), 'prole': K(PARTY_ROLES), 'attire': K(ATTIRE_STATUS),
      'paykind': K(PAY_KINDS), 'paystatus': K(PAY_STATUS), 'ckind': K(CONTRACT_KINDS), 'vname': K(VNAMES)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])


# verdict and flag words: two lists of at most 30 values, filled in the order the words are first used
_VW = {n: [] for n in ('va', 'vb', 'vc', 'vd', 've')}
_NAMES = ('va', 'vb', 'vc', 'vd', 've')
_VK = {}
def v(label):
    """token of a verdict word (list va or vb); the word is added to the list on first use"""
    if label not in _VK:
        name = next(n for n in _NAMES if len(_VW[n]) < 30)
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
    for name, lab in zip(_NAMES, ('Verdict words A', 'Verdict words B', 'Verdict words C', 'Verdict words D', 'Verdict words E')):
        vals = _VW[name]
        if len(vals) == 1: vals = vals + [('Not used', 'not_used')]
        if vals: out.append(L(name, lab, [(k, l) for l, k in vals]))
    return out
