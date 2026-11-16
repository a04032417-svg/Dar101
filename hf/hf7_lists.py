"""Household Finance suite part 7 (Partners, Kids and Shared Costs): label lists shared by data, tables, tools."""
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


PAYERS = ['Partner 1', 'Partner 2']
KID = ['Noa', 'Ike']
SHARED_CATS = ['Household supplies', 'Entertainment', 'Health costs', 'Kids and family', 'Eating out']
MEMBERS = ['Partner 1', 'Partner 2', 'Noa', 'Ike', 'Grandparent']
DEBTS = ['Card A', 'Card B', 'Card C', 'Car loan', 'Student loan']
SCENS = ['Lose one income', 'Expense shock', 'Interest-rate change', 'Mortgage switch', 'New baby', 'Extra payment', 'Growth example']
SITEMS = [r['item'] for r in scenario_rows()]
TBASIS = ['Agreed split', 'Income share', 'Equal', 'Custom share']

# verdict and status labels (formulas never write text: they point at these list cells)
VERD = ['Settled', 'Overdue', 'Open', 'Square', 'Partner 2 over', 'Partner 1 over', 'On share', 'Saving well', 'Ask to save more', 'pays', 'to', 'Nothing to settle',
        'is owed', 'Balance is square', 'over for', 'months, settle up', 'No streak to settle', 'Agreement holds', 'Reset to', 'is', 'of shared costs', 'costs', 'a year',
        'Pay', 'on', 'Saving', 'Gap', 'a month,', 'months of cover with the cuts', 'No gap, income covers the plan', 'Cut', 'from', 'Cuts do not close the gap', 'No cut needed', 'Covered',
        'Uses', 'months of emergency fund', 'Payment rises by', 'No change in the payment', 'savings last', 'months', 'more a month, your numbers, not advice',
        'less a month, your numbers, not advice', 'No difference', 'Transfer', 'each payday', 'Split', 'Month in progress', 'Allowance is below your average',
        'Allowance is above your average', 'Allowance matches your average', 'Savings cover the plan', 'Savings run out', 'Settle now', 'Under your own range', 'Cuts close the gap']
assert len(set(VERD)) == len(VERD) and len(VERD) <= 90
_chunks = [VERD[i:i + 20] for i in range(0, len(VERD), 20)]
if len(_chunks[-1]) < 2: _chunks[-2] += _chunks.pop()
assert len(_chunks) <= 3 and all(2 <= len(c) <= 30 for c in _chunks)
VNAMES = ['va', 'vb', 'vc', 'vd'][:len(_chunks)]
_VMAP = {}
for _n, _c in zip(VNAMES, _chunks):
    for _l in _c: _VMAP[_l] = (_n, K(_c)[_l])


def V(label):
    n, k = _VMAP[label]
    return LV(n, k)


lists = [
    L('payer', 'Paid by', P(PAYERS)), L('kid', 'Child', P(KID)), L('child', 'Child or both', P(KIDS)), L('kidkind', 'Kids cost kind', P(KID_KINDS)),
    L('sharedcat', 'Shared cost category', P(SHARED_CATS)), L('split', 'Split rule', P(SPLIT_RULES)), L('group', 'Group', P(GROUPS)), L('wday', 'Weekday', P(WEEKDAYS)),
    L('member', 'Household member', P(MEMBERS)), L('debt', 'Debt', P(DEBTS)), L('scen', 'Scenario', P(SCENS)), L('sitem', 'Scenario item', P(SITEMS)),
    L('role', 'Role', P(ROLES)), L('tgroup', 'Team group', P(TEAM_GROUPS)), L('tbasis', 'Transfer basis', P(TBASIS)),
] + [L(n, 'Verdict ' + n[1:].upper(), P(c)) for n, c in zip(VNAMES, _chunks)]
assert len(lists) <= 20
_M = {'payer': K(PAYERS), 'kid': K(KID), 'child': K(KIDS), 'kidkind': K(KID_KINDS), 'sharedcat': K(SHARED_CATS), 'split': K(SPLIT_RULES), 'group': K(GROUPS), 'wday': K(WEEKDAYS),
      'member': K(MEMBERS), 'debt': K(DEBTS), 'scen': K(SCENS), 'sitem': K(SITEMS), 'role': K(ROLES), 'tgroup': K(TEAM_GROUPS), 'tbasis': K(TBASIS)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
P1 = tok('payer', 'Partner 1')
P2 = tok('payer', 'Partner 2')
