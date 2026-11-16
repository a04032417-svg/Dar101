"""Household Finance suite part 2 (Bills, Subscriptions and Due Dates): label lists shared by data, tables, tools.
Verdict labels are registered with V('label') and grouped into the lists va, vb, vc, vd (30 labels each) when hf2.py assembles the file."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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


BILL_CATS = ['Rent or mortgage', 'Utilities', 'Phone and internet', 'Insurance', 'Childcare and school', 'Car loan', 'Student loan', 'Card payments', 'Car service', 'Work and tax costs']
DAYBANDS = ['Days 1 to 7', 'Days 8 to 14', 'Days 15 to 21', 'Days 22 to 31']
USE_BANDS = ['Used this week', 'Used this month', 'Used 30 to 59 days ago', 'Not used for 60 days or more']
PAY_ACCTS = ['Joint checking', 'Car and home savings']
CARDS = ['Card A', 'Card B']

base_lists = [
    L('role', 'Role', P(ROLES)), L('tgroup', 'Team group', P(TEAM_GROUPS)), L('atype', 'Account type', P(ACCOUNT_TYPES)), L('person', 'Person', P(PERSONS)),
    L('bcat', 'Bill category', P(BILL_CATS)), L('cycle', 'Billing cycle', P(BILL_CYCLES)), L('bstatus', 'Bill status', P(BILL_STATUS)), L('decision', 'Decision', P(SB_DECISIONS)),
    L('ckind', 'Contract kind', P(CONTRACT_KINDS)), L('payfreq', 'Pay frequency', P(PAY_FREQS)), L('dayband', 'Day of the month', P(DAYBANDS)), L('useband', 'Days since last use', P(USE_BANDS)),
    L('payacct', 'Paid from', P(PAY_ACCTS)), L('card', 'Card', P(CARDS)),
]
_M = {'role': K(ROLES), 'tgroup': K(TEAM_GROUPS), 'atype': K(ACCOUNT_TYPES), 'person': K(PERSONS), 'bcat': K(BILL_CATS), 'cycle': K(BILL_CYCLES), 'bstatus': K(BILL_STATUS), 'decision': K(SB_DECISIONS),
      'ckind': K(CONTRACT_KINDS), 'payfreq': K(PAY_FREQS), 'dayband': K(DAYBANDS), 'useband': K(USE_BANDS), 'payacct': K(PAY_ACCTS), 'card': K(CARDS)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])

# ---- verdict registry: V('Label') -> '{list:vN.key}' (the label is written once, the list is built at the end)
_REG = []          # (list key, value key, label)
_VIDX = {}
def V(label):
    if label in _VIDX: return _VIDX[label]
    assert len(label) <= 40, label
    n = len(_REG); lk = 'v' + 'abcd'[n // 30]
    used = {k for l, k, _ in _REG if l == lk}
    k = P([label])[0][0]
    while k in used: k = k[:-1] + 'x'
    _REG.append((lk, k, label)); _VIDX[label] = LV(lk, k)
    return _VIDX[label]


def verdict_lists():
    out = []
    for lk, nm in (('va', 'Verdict A'), ('vb', 'Verdict B'), ('vc', 'Verdict C'), ('vd', 'Verdict D')):
        vals = [(k, l) for a, k, l in _REG if a == lk]
        if vals: out.append(L(lk, nm, vals))
    return out
