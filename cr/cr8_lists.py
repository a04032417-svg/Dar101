"""Car rental suite part 8 (Finance, Replace-or-Sell and Owner Pay): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cr_core import *
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


_E = expense_rows(n=700)
_cnt = {}
for _e in _E: _cnt[_e['vendor']] = _cnt.get(_e['vendor'], 0) + 1
VENDORS = [v for v, _ in sorted(_cnt.items(), key=lambda kv: -kv[1])]
COST_KINDS = ['Loan payment', 'Renewal', 'Payroll', 'Rent and lot', 'Other bills']
EVENTS = ['Purchase', 'Sale']
SCENARIOS = ['Base case', 'Utilisation down', 'More cars', 'Financing rate up', 'Marketplace fees up', 'Rates up']
PEOPLE = ['Nadia', 'Tomas', 'Elsa', 'Ingrid', 'Anil', 'Hassan', 'Diego', 'Olga']
PEOPLE_KEYS = ['owner', 'manager', 'bookkeeper', 'accountant', 'lender', 'broker', 'mechanic', 'tyres']
VA = ['Keep', 'Sell this season', 'Replace', 'Sell now', 'Keep until', 'Refinance', 'Keep the loan', 'Pay off', 'Keep the cash', 'Buy', 'Wait', 'Do not buy', 'Start',
      'Start with a cheaper car', 'Consistent', 'Write down', 'Sale frees', 'Sale needs', 'from cash', 'Pack complete', 'items missing, confirm with your adviser', 'Balanced', 'High interest cost']
VB = ['Safe to draw', 'Draw less, safe amount is', 'Draw less', 'Set aside is on track', 'Short by', 'Worst case still above the cash floor', 'Dips below the floor, lowest in month',
      'Profit is most sensitive to utilisation', 'Profit is most sensitive to daily rate', 'Financing share', 'months covered', 'Above break-even by', 'Below break-even by',
      'Cash stays above the floor', 'Cash falls below the floor', 'earns', 'lowest margin is', 'costs a day', 'the lowest rate to break even is', 'On target', 'Over your limit']
assert len(VA) <= 30 and len(VB) <= 30

lists = [
    L('class', 'Vehicle class', P(CLASSES)), L('expcat', 'Expense category', P(EXPENSE_CATEGORIES)), L('vendor', 'Vendor', P(VENDORS)), L('vstatus', 'Vehicle status', P(VEH_STATUS)),
    L('paystatus', 'Draw status', P(PAY_STATUS)), L('costkind', 'Cost kind', P(COST_KINDS)), L('vevent', 'Event', P(EVENTS)), L('scen', 'Scenario', P(SCENARIOS)),
    L('people', 'Contact first name', list(zip(PEOPLE_KEYS, PEOPLE))), L('va', 'Verdict A', P(VA)), L('vb', 'Verdict B', P(VB)),
]
assert len(lists) <= 20
_M = {'class': K(CLASSES), 'expcat': K(EXPENSE_CATEGORIES), 'vendor': K(VENDORS), 'vstatus': K(VEH_STATUS), 'paystatus': K(PAY_STATUS), 'costkind': K(COST_KINDS), 'vevent': K(EVENTS),
      'scen': K(SCENARIOS), 'va': K(VA), 'vb': K(VB)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def va(label): return tok('va', label)
def vb(label): return tok('vb', label)
def person(k): return LV('people', k)
