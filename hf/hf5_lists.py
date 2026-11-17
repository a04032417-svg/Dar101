"""Household Finance suite part 5 (Savings Goals and Sinking Funds): label lists shared by data, tables and tools."""
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


GSTATE = ['Reached', 'On track', 'Behind', 'Past the date']
FSTATE = ['Covered', 'Short', 'No fund set up']
ESTATE = ['Below the typical range', 'Within the typical range', 'Above the typical range']
RLABEL = ['Low end of the typical range', 'High end of the typical range', 'In between', 'Short of the range', 'Beyond the range']
FUNDED = ['Funded', 'Under-funded']
REASONS = ['Income changed', 'Date moved', 'Price changed', 'Catch up', 'Paused', 'Extra paycheck', 'Cost cut']
RWIN = ['Year to date', 'Last 12 months', 'Previous 12 months', 'All recorded']
STATE = GSTATE + FSTATE + ESTATE + RLABEL + FUNDED
ACAT = ['Insurance', 'Car service', 'Work and tax costs', 'Subscriptions', 'Holidays and trips', 'Gifts', 'Household supplies', 'Kids and family', 'Childcare and school', 'Health costs', 'Tax set-aside']
assert all(c in CATEGORY_NAMES for c in ACAT)

lists = [
    L('person', 'Person', P(PERSONS)), L('payfreq', 'Pay rhythm', P(PAY_FREQS)), L('atype', 'Account type', P(ACCOUNT_TYPES)), L('gkind', 'Goal kind', P(GOAL_KINDS)),
    L('priority', 'Priority', P(PRIORITIES)), L('ctkind', 'Contribution kind', P(CT_KINDS)), L('isource', 'Income source', P(INCOME_SOURCES)), L('category', 'Category', P(CATEGORY_NAMES)),
    L('cycle', 'Bill cycle', P(BILL_CYCLES)), L('rtsource', 'Retirement source', P(RT_SOURCES)), L('state', 'Status', P(STATE)), L('reason', 'Change reason', P(REASONS)),
    L('rwindow', 'Period', P(RWIN)), L('acat', 'Annual cost category', P(ACAT)),
]
assert len(lists) <= 20
_M = {'person': K(PERSONS), 'payfreq': K(PAY_FREQS), 'atype': K(ACCOUNT_TYPES), 'gkind': K(GOAL_KINDS), 'priority': K(PRIORITIES), 'ctkind': K(CT_KINDS), 'isource': K(INCOME_SOURCES),
      'category': K(CATEGORY_NAMES), 'cycle': K(BILL_CYCLES), 'rtsource': K(RT_SOURCES), 'reason': K(REASONS), 'rwindow': K(RWIN), 'acat': K(ACAT)}


_ST = K(STATE)
_G = {'gstate': GSTATE, 'fstate': FSTATE, 'estate': ESTATE, 'rlabel': RLABEL, 'funded': FUNDED}
def key(lst, label):
    if lst in _G: assert label in _G[lst]; return _ST[label]
    return _M[lst][label]
def tok(lst, label):
    if lst in _G: return LV('state', key(lst, label))
    return LV(lst, _M[lst][label])


import re as _re
VW = []
def lit(label):
    if label not in VW: VW.append(label)
    i = VW.index(label); return LV('vw%d' % (i // 28 + 1), 'v%d' % (i % 28 + 1))
def LITX(f):
    def rep(m):
        t = m.group(1)
        if not _re.search('[A-Za-z]', t): return m.group(0)
        core = t.strip(); out = lit(core)
        if t[:1] == ' ': out = '" "&' + out
        if t[-1:] == ' ': out = out + '&" "'
        return out
    return _re.sub(r'"([^"]*)"', rep, f)
def vlists():
    out = []
    for n in range(0, len(VW), 28):
        chunk = VW[n:n + 28]
        if len(chunk) < 2: chunk = chunk + ['Not used']
        out.append(L('vw%d' % (n // 28 + 1), 'Words %d' % (n // 28 + 1), [('v%d' % (i + 1), l) for i, l in enumerate(chunk)]))
    return out
