"""Household Finance suite part 6 (Net Worth and Accounts): label lists shared by data, tables, tools."""
import sys, os, re; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hf_core import *
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


PAYERS = ['Partner 1', 'Partner 2']
BASES = ['Agreed split', 'Income share']
PYEARS = ['Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5']
PITEMS = ['Growth gap for low and high cases', 'Starting amount, 0 = balances now', 'Years shown on the projection page', 'Net worth target', 'Years to reach the target']

# verdict words: registered on first use, so tools and tables just write V('Label')
_VL, _VK = [], {}
CHUNK = 28
def V(label):
    if label not in _VK:
        k = re.sub(r'[^a-z0-9]+', '_', label.lower()).strip('_')[:21] or 'v'
        used = {x[1] for x in _VK.values()}
        while k in used: k = k[:-1] + 'x'
        i = len(_VL); _VL.append(label)
        _VK[label] = ('v' + 'abc'[i // CHUNK], k)
    n, k = _VK[label]
    return LV(n, k)


def verdict_lists():
    out = []
    for ci in range((len(_VL) + CHUNK - 1) // CHUNK):
        labs = _VL[ci * CHUNK:(ci + 1) * CHUNK]
        if len(labs) < 2: labs = labs + ['Spare']
        out.append(L('v' + 'abc'[ci], 'Verdict ' + 'ABC'[ci], [(_VK[l][1] if l in _VK else 'spare', l) for l in labs]))
    return out


base_lists = [
    L('person', 'Owner', P(PERSONS)), L('atype', 'Account group', P(ACCOUNT_TYPES)), L('side', 'Asset or liability', P(NW_CLASS)), L('cycle', 'Cycle', P(BILL_CYCLES)),
    L('category', 'Category', P(CATEGORY_NAMES)), L('purpose', 'Transfer purpose', P(TR_PURPOSES)), L('role', 'Role', P(ROLES)), L('tgroup', 'Team group', P(TEAM_GROUPS)),
    L('payer', 'Partner', P(PAYERS)), L('basis', 'Transfer basis', P(BASES)), L('payfreq', 'Pay rhythm', P(PAY_FREQS)), L('pyear', 'Projection year', P(PYEARS)),
    L('pitem', 'Projection input', P(PITEMS))]
_M = {'person': K(PERSONS), 'atype': K(ACCOUNT_TYPES), 'side': K(NW_CLASS), 'cycle': K(BILL_CYCLES), 'category': K(CATEGORY_NAMES), 'purpose': K(TR_PURPOSES), 'role': K(ROLES),
      'tgroup': K(TEAM_GROUPS), 'payer': K(PAYERS), 'basis': K(BASES), 'payfreq': K(PAY_FREQS), 'pyear': K(PYEARS), 'pitem': K(PITEMS)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
P1, P2 = tok('payer', 'Partner 1'), tok('payer', 'Partner 2')
