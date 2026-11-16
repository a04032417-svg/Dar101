"""Nonprofit suite part 8 (Budget, Cash and Annual Report): label lists shared by data, tables and tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from np_core import *
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


STAFF_NAMES = [s['name'] for s in staff]
PAY_ROLE_LIST = ROLES[:6]
RULES = ['Staff time', 'Floor area', 'Headcount', 'Use', 'Direct']
SOURCES = ['Gifts', 'Grants', 'Events', 'Dues', 'In-kind']
SCEN = ['Base', 'Lose the biggest donor', 'Lose one grant', 'Donors fall 5%', 'Recurring grows 10%', 'Costs up 8%', 'Donors fall 10%', 'Costs up 4%', 'Costs up 12%', 'Gifts up 5%',
        'Worst case together', 'Best case together']
YR3 = ['Two years ago', 'Last year', 'This year']
FINPUT = ['Gifts change', 'Recurring change', 'Pledges collected share', 'Grants received share', 'Event net change', 'Expenses change', 'Expense growth for reserve months',
          'Biggest donor giving a year', 'Dues change', 'Opening cash change']
STEPS = ['Month %d' % i for i in range(1, 13)]
MONS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
CK1 = ['On budget', 'Over by', 'in', 'Rule applied to', 'Steady', 'Falling by', 'Rising by', 'Rising, review', 'Budget', 'your estimate', 'Ahead', 'On plan', 'Behind by', 'Cash low in', 'at',
       'Safe', 'Watch', 'Act now', 'Above', 'On the setting', 'Below', 'Yes', 'Yes after', 'Not yet', 'Full yearly cost', 'Tied', 'Check', 'lines', 'Ready', 'Missing']
CK2 = ['Complete', 'Add', 'Below in', 'Not within 12 months', 'Save', 'a month for', 'months', 'Worst case', 'leaves', 'Most sensitive to', 'Holds', 'Thin', 'Over', 'Under', 'OK',
       'Lowest closing cash', 'Lowest free money', 'Lowest reserve months', 'Highest closing cash', 'Highest reserve months', 'this year', 'last year', 'percent',
       'points', 'Already at the setting']
CK3 = ['Budget builder base', 'Best', 'Worst', 'Base case', 'Program', 'Management', 'Fundraising', 'Shared', 'Still open', 'Allocated', 'Lines to check', 'Items missing', 'Items ready',
       'Free money', 'Cash', 'Reserve months', 'Short', 'Enough', 'Waits', 'Funded months', 'Rule', 'Basis', 'Done', 'Not done', 'Match', 'Differs', 'Sensitive', 'Little effect', 'Rising', 'Falling']
for _l in (CK1, CK2, CK3): assert len(_l) <= 30 and len(set(_l)) == len(_l)

lists = [
    L('area', 'Budget area', P(BUDGET_AREAS)), L('eprogram', 'Expense program', P(EXPENSE_PROGRAMS)), L('function', 'Function', P(FUNCTIONS)), L('category', 'Expense category', P(EXPENSE_CATEGORIES)),
    L('fund', 'Fund', P([f['fund'] for f in funds])), L('iline', 'Income line', P(INCOME_LINES)), L('bkind', 'Bank line kind', P(BANK_KINDS)), L('payrole', 'Pay role', P(PAY_ROLE_LIST)),
    L('staff', 'Staff member', P(STAFF_NAMES)), L('rule', 'Allocation rule', P(RULES)), L('source', 'Income source', P(SOURCES)), L('scen', 'Scenario', P(SCEN)), L('yr', 'Year', P(YR3)),
    L('finput', 'Forecast input', P(FINPUT)), L('step', 'Forecast month', P(STEPS)), L('mon', 'Month name', P(MONS)),
    L('ck1', 'Verdict words A', P(CK1)), L('ck2', 'Verdict words B', P(CK2)), L('ck3', 'Verdict words C', P(CK3)),
]
assert len(lists) <= 20
_M = {'area': K(BUDGET_AREAS), 'eprogram': K(EXPENSE_PROGRAMS), 'function': K(FUNCTIONS), 'category': K(EXPENSE_CATEGORIES), 'fund': K([f['fund'] for f in funds]), 'iline': K(INCOME_LINES),
      'bkind': K(BANK_KINDS), 'payrole': K(PAY_ROLE_LIST), 'staff': K(STAFF_NAMES), 'rule': K(RULES), 'source': K(SOURCES), 'scen': K(SCEN), 'yr': K(YR3), 'finput': K(FINPUT), 'step': K(STEPS),
      'mon': K(MONS), 'ck1': K(CK1), 'ck2': K(CK2), 'ck3': K(CK3)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def v(label):
    """token of a verdict word from whichever verdict list holds it"""
    for l in ('ck1', 'ck2', 'ck3'):
        if label in _M[l]: return tok(l, label)
    raise KeyError(label)
def vkey(label):
    for l in ('ck1', 'ck2', 'ck3'):
        if label in _M[l]: return _M[l][label]
    raise KeyError(label)
def MONTXT(d):
    """month name and year of a date expression, from the Month name list"""
    return 'CHOOSE(MONTH(%s),%s)&" "&YEAR(%s)' % (d, ','.join(tok('mon', m) for m in MONS), d)
def MONONLY(d): return 'CHOOSE(MONTH(%s),%s)' % (d, ','.join(tok('mon', m) for m in MONS))
