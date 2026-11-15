"""Childcare center suite part 5 (Payments, Balances and Cash): label lists shared by data, tables, tools. Verdict words are registered with V() and become lists v1..v3."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc_core import *
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


OUTCOMES = ['Kept', 'Broken', 'Pending']
PMETHODS = ['Phone', 'Email', 'Message']
HABITS = ['Prompt', 'Normal', 'Slow', 'Very slow']
BILLCATS = ['Rent', 'Payroll', 'Insurance', 'Utilities', 'Food and groceries', 'Cleaning', 'Accounting', 'Management software']
DONE2 = ['Paid', 'Upcoming']
PAYSTAT = ['Paid', 'Accruing']
SCEN = ['Base', 'Best', 'Worst', 'Families leave']
PAYTYPES3 = ['Owner draw', 'Salary', 'Hourly']

_V = {}
_VN = {}


def V(label):
    """token for a verdict or check word; the word is added to the verdict lists on first use (30 words a list)"""
    if label not in _V:
        n = sum(len(v) for v in _VN.values())
        lk = 'v%d' % (n // 30 + 1)
        labs = _VN.setdefault(lk, [])
        k = ''.join(ch if ch.isalnum() else '_' for ch in label.lower()).strip('_')
        while '__' in k: k = k.replace('__', '_')
        k = k[:21]
        used = {_V[x][1] for x in labs}
        while k in used: k = k[:-1] + 'x'
        _V[label] = (lk, k); labs.append(label)
    lk, k = _V[label]
    return LV(lk, k)


def verdict_lists():
    out = []
    for lk in sorted(_VN):
        out.append({"key": lk, "label": {'v1': 'Decision A', 'v2': 'Decision B', 'v3': 'Decision C', 'v4': 'Decision D'}[lk],
                    "values": [{"key": _V[x][1], "label": x} for x in _VN[lk]]})
    return out


def base_lists():
    return [L('cycle', 'Billing cycle', P(BILL_CYCLES)), L('method', 'Payment method', P(PAY_METHODS)), L('istatus', 'Invoice status', P(INVOICE_STATUS)),
            L('paykind', 'Payment kind', P(PAYMENT_KINDS)), L('govstatus', 'Government payment status', P(GOV_STATUS)), L('depstatus', 'Deposit status', P(DEPOSIT_STATUS)),
            L('expcat', 'Expense category', P(EXPENSE_CATEGORIES)), L('payrole', 'Pay role', P(PAY_ROLES)), L('paytype', 'Pay type', P(PAYTYPES3)),
            L('done2', 'Bill status', P(DONE2)), L('paystat', 'Payroll status', P(PAYSTAT)), L('band', 'Aging band', P(AGE_BANDS)), L('outcome', 'Promise outcome', P(OUTCOMES)),
            L('pmethod', 'Promise method', P(PMETHODS)), L('habit', 'Payment habit', P(HABITS)), L('billcat', 'Bill category', P(BILLCATS)), L('scen', 'Case', P(SCEN))]


_M = {'cycle': K(BILL_CYCLES), 'method': K(PAY_METHODS), 'istatus': K(INVOICE_STATUS), 'paykind': K(PAYMENT_KINDS), 'govstatus': K(GOV_STATUS), 'depstatus': K(DEPOSIT_STATUS),
      'expcat': K(EXPENSE_CATEGORIES), 'payrole': K(PAY_ROLES), 'paytype': K(PAYTYPES3), 'done2': K(DONE2), 'paystat': K(PAYSTAT), 'band': K(AGE_BANDS), 'outcome': K(OUTCOMES),
      'pmethod': K(PMETHODS), 'habit': K(HABITS), 'billcat': K(BILLCATS), 'scen': K(SCEN)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
YES = '{list:yesno.yes}'
NO = '{list:yesno.no}'
