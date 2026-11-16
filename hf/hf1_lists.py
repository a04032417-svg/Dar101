"""Household Finance suite part 1 (Money Plan and Paychecks): label lists shared by data, tables and tools."""
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


_BILL_CATS = []
for _b in bill_rows():
    if _b['category'] not in _BILL_CATS: _BILL_CATS.append(_b['category'])
BILL_CATS = [c for c in CATEGORY_NAMES if c in _BILL_CATS]
AHEAD = ['This month'] + ['In %d month%s' % (i, '' if i == 1 else 's') for i in range(1, 13)]
WEEKS = ['Week %d' % i for i in range(1, 14)]
LINE_KINDS = ['Bills', 'Sinking funds', 'Debt', 'Goals', 'Savings', 'Spending money']
LINE_RULES = ['Percent', 'Fixed amount', 'Rest']
WF_USES = ['Emergency fund', 'Debt payoff', 'Goals', 'Income buffer', 'Spending', 'Tax set-aside', 'Not assigned yet']
SPLIT_METHODS = ['Zero-based', 'Percentage']

# verdict and status labels (formulas never write text: they point at these list cells)
CK1 = ['Under the floor', 'Above the floor', 'Safe', 'Tight', 'Short', 'Extra pay month', 'Normal month', 'Above baseline', 'Below baseline', 'At baseline',
       'Month in progress', 'Matches', 'Check the difference', 'Assign the extra paycheck', 'No extra paycheck', 'Within range', 'Needs high', 'Wants high', 'Savings low']
CK2 = ['Safe until payday', 'Short before payday', 'Move money in', 'Fine as it is', 'Zero left to assign', 'Left to assign', 'Over-assigned', 'Extra pay month ahead',
       'No extra pay month', 'Assign to debt', 'Assign to goals', 'Assign to buffer', 'Set aside per paycheck', 'Budget the baseline', 'Buffer is built', 'Buffer is building',
       'Covered', 'Short of the bills', 'Within your limit', 'Above your limit']
CK3 = ['Can spend per day', 'Nothing to spend', 'Ahead of plan', 'On plan', 'Behind plan', 'Chase the client', 'Wait for the payment', 'Surplus', 'Gap', 'Safe if pay is late',
       'Short if pay is late', 'Matches the bank', 'Check the take-home', 'Above baseline so far', 'Below baseline so far', 'Within the typical range', 'Wants are high', 'Savings are low']
assert len(CK1) <= 30 and len(CK2) <= 30 and len(CK3) <= 30

lists = [
    L('person', 'Person', P(PERSONS)), L('payfreq', 'Pay rhythm', P(PAY_FREQS)), L('atype', 'Account type', P(ACCOUNT_TYPES)), L('group', 'Budget group', P(GROUPS)),
    L('category', 'Category', P(CATEGORY_NAMES)), L('bcat', 'Bill category', P(BILL_CATS)), L('isource', 'Income source', P(INCOME_SOURCES)), L('istatus', 'Invoice status', P(INVOICE_STATUS)),
    L('bstatus', 'Bill status', P(BILL_STATUS)), L('role', 'Role', P(ROLES)), L('tgroup', 'Team group', P(TEAM_GROUPS)), L('lkind', 'Split line kind', P(LINE_KINDS)),
    L('lrule', 'Split line rule', P(LINE_RULES)), L('wuse', 'Windfall use', P(WF_USES)), L('ahead', 'Months ahead', P(AHEAD)), L('week', 'Forecast week', P(WEEKS)),
    L('smethod', 'Split method', P(SPLIT_METHODS)), L('ck1', 'Status', P(CK1)), L('ck2', 'Verdict A', P(CK2)), L('ck3', 'Verdict B', P(CK3)),
]
assert len(lists) <= 20
_M = {'person': K(PERSONS), 'payfreq': K(PAY_FREQS), 'atype': K(ACCOUNT_TYPES), 'group': K(GROUPS), 'category': K(CATEGORY_NAMES), 'bcat': K(BILL_CATS), 'isource': K(INCOME_SOURCES),
      'istatus': K(INVOICE_STATUS), 'bstatus': K(BILL_STATUS), 'role': K(ROLES), 'tgroup': K(TEAM_GROUPS), 'lkind': K(LINE_KINDS), 'lrule': K(LINE_RULES), 'wuse': K(WF_USES),
      'ahead': K(AHEAD), 'week': K(WEEKS), 'smethod': K(SPLIT_METHODS), 'ck1': K(CK1), 'ck2': K(CK2), 'ck3': K(CK3)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def c1(label): return tok('ck1', label)
def c2(label): return tok('ck2', label)
def c3(label): return tok('ck3', label)
