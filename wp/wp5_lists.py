"""Wedding suite part 5 (Venue Capacity and Seating Plan): label lists and the verdict-word registry."""
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


TABLE_IDS = [t['table_id'] for t in table_rows()]
RBASIS = ['Per seat', 'Per table', 'Per guest', 'Fixed']
RITEMS = ['Chairs', 'Round tables', 'Table linens', 'Napkins', 'Dinner plates', 'Dessert plates', 'Water glasses', 'Wine glasses', 'Cutlery sets', 'Centerpiece stands', 'Place card holders', 'Table number stands']
SCENS = ['Confirmed yes only', 'Pending 25% yes', 'Pending half yes', 'Expected yes rate', 'Pending 90% yes', 'Every pending says yes', 'Expected plus 6 plus-ones', 'Expected plus 10 B list',
         'Travel guests decline more', 'Everyone invited says yes', 'Everyone says yes plus 4', 'Expected less 10 guests']
TSIZES = ['6', '8', '9', '10', '12']
SITEMS = ['Venue floor area', 'Dance floor', 'Buffet area', 'Stage and band', 'Bar and cake tables', 'Walkways and exits', 'Area per guest, minimum', 'Share of guests dancing']

BASE_LISTS = [
    L('side', 'Side', P(SIDES)), L('tier', 'Tier', P(TIERS)), L('listab', 'Invitation list', P(LIST_AB)), L('age', 'Age group', P(AGE_GROUPS)), L('rsvp', 'RSVP', P(RSVP)),
    L('meal', 'Meal choice', P(MEALS)), L('dietary', 'Dietary note', P(DIETARY)), L('table', 'Table', P(TABLE_IDS)), L('tkind', 'Table kind', P(TABLE_KINDS)),
    L('rkind', 'Rule kind', P(RULE_KINDS)), L('reason', 'Rule reason', P(RULE_REASONS)), L('rbasis', 'Rental basis', P(RBASIS)), L('ritem', 'Rental item', P(RITEMS)),
    L('scen', 'Headcount scenario', P(SCENS)), L('tsize', 'Seats per table', P(TSIZES)), L('sitem', 'Space item', P(SITEMS)),
]
_M = {'side': K(SIDES), 'tier': K(TIERS), 'listab': K(LIST_AB), 'age': K(AGE_GROUPS), 'rsvp': K(RSVP), 'meal': K(MEALS), 'dietary': K(DIETARY), 'table': K(TABLE_IDS), 'tkind': K(TABLE_KINDS),
      'rkind': K(RULE_KINDS), 'reason': K(RULE_REASONS), 'rbasis': K(RBASIS), 'ritem': K(RITEMS), 'scen': K(SCENS), 'tsize': K(TSIZES), 'sitem': K(SITEMS)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])


_VW = {'va': [], 'vb': [], 'vc': [], 'vd': []}
_VK = {}
def v(label):
    """token of a verdict word (lists va..vd); the word is added to a list on first use"""
    if label not in _VK:
        name = next(n_ for n_ in ('va', 'vb', 'vc', 'vd') if len(_VW[n_]) < 30)
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
    for name, lab in (('va', 'Verdict words A'), ('vb', 'Verdict words B'), ('vc', 'Verdict words C'), ('vd', 'Verdict words D')):
        vals = _VW[name]
        if len(vals) == 1: vals = vals + [('Not used', 'not_used')]
        if vals: out.append(L(name, lab, [(k, l) for l, k in vals]))
    return out
