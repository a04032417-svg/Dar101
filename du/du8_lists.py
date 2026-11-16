"""Doula business suite part 8 (Money, Owner Pay, Renewals, Year Plan): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from du_core import *
from lib import L, LV


def P(labels):
    """pairs() with list keys cut to 21 characters, unique inside the list"""
    out, seen = [], set()
    for k, l in pairs(labels):
        if not k[:1].isalpha(): k = 'n' + k
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


PAYEES = ['Marketing suppliers', 'Kofi Mensah', 'Print and stationery shop', 'Training provider', 'Renewal fee', 'Phone and online tools', 'Callum Reid', 'Thank-you gifts', 'Payment provider', 'Various', 'Rosa Delgado', 'Membership body']
SCEN = ['Base', 'Best', 'Worst']
MNAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
RAG = ['Done', 'Overdue', 'Red', 'Amber', 'Green']
TREND = ['Dropped', 'Within range', 'Improved']
PCHK = ['Draw covered by profit', 'Draw uses cash', 'Reduce the draw']
FCHK = ['Above the floor', 'Near the floor', 'Below the floor']
# words that tool verdicts return (a formula never types a word: it points at the list cell)
VW = ['Next renewal', 'in', 'days', 'No open renewals', 'is', 'over budget', 'under budget', 'Lowest cash', 'months of cover', 'Yes, pay yourself', 'Reduce your draw to', 'cash would fall below the floor',
      'Margin is above your own history', 'Margin is below your own history', 'Margin matches your own history', 'figures dropped over', 'You need', 'births a month, you did',
      'births a month to break even', 'births a month to reach your target', 'Comfortable', 'Watch', 'Act now', 'Investigate', 'No category is over budget', 'Affordable', 'Not affordable',
      'Affordable with', 'Plan more cash', 'Move', 'by', 'confirm with your adviser', 'Nothing to move', 'Free cash is', 'No free cash', 'Set aside', 'a month', 'Keep', 'aside',
      'Fixed costs are', 'review', 'Pack balances', 'Pack differs by', 'of revenue', 'No month falls below the floor', 'Time off first', 'Hold the draw']
assert len(VW) <= 60
VD, VE = VW[:30], VW[30:]

lists = [
    L('role', 'Role', P(ROLES)), L('expcat', 'Expense category', P(EXPENSE_CATEGORIES)), L('renewal', 'Renewal item', P(RENEWAL_KINDS)), L('cpd', 'Training kind', P(CPD_KINDS)),
    L('taxstatus', 'Set-aside status', P(['Moved', 'Planned'])), L('ctstatus', 'Contract status', P(CONTRACT_STATUS)), L('plan', 'Payment plan', P(PLAN_TYPES)), L('istatus', 'Instalment status', P(INST_STATUS)),
    L('ckind', 'Client kind', P(CLIENT_KINDS)), L('cstatus', 'Client status', P(CLIENT_STATUS)), L('payee', 'Paid to', P(PAYEES)), L('scen', 'Scenario', P(SCEN)), L('mname', 'Month name', P(MNAMES)),
    L('rag', 'Renewal status', P(RAG)), L('trend', 'Trend', P(TREND)), L('pchk', 'Draw check', P(PCHK)), L('fchk', 'Cash check', P(FCHK)), L('vd', 'Verdict words A', P(VD)), L('ve', 'Verdict words B', P(VE)),
]
assert len(lists) <= 20
_M = {'role': K(ROLES), 'expcat': K(EXPENSE_CATEGORIES), 'renewal': K(RENEWAL_KINDS), 'cpd': K(CPD_KINDS), 'taxstatus': K(['Moved', 'Planned']), 'ctstatus': K(CONTRACT_STATUS), 'plan': K(PLAN_TYPES),
      'istatus': K(INST_STATUS), 'ckind': K(CLIENT_KINDS), 'cstatus': K(CLIENT_STATUS), 'payee': K(PAYEES), 'scen': K(SCEN), 'mname': K(MNAMES), 'rag': K(RAG), 'trend': K(TREND), 'pchk': K(PCHK),
      'fchk': K(FCHK), 'vd': K(VD), 've': K(VE)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def vt(label): return tok('vd', label) if label in _M['vd'] else tok('ve', label)
def MN(x): return 'CHOOSE(MONTH(%s),%s)' % (x, ','.join(tok('mname', m) for m in MNAMES))
