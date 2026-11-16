"""Wedding suite part 7 (Events, Travel and Honeymoon): label lists, the verdict-word registry and the list helpers."""
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


LINE_ITEMS = ['Food and snacks', 'Drinks', 'Decor and flowers', 'Invitations and cards', 'Favors', 'Games and prizes', 'Cards', 'Gift for the group', 'Shared transport', 'Snacks',
              'Restaurant deposit', 'Food and drinks balance', 'Room hire', 'Thank-you gifts for helpers', 'Food', 'Coffee and drinks', 'Decor and signs',
              'Included in the venue contract', 'Included in the caterer contract']
NIGHTS = ['Two nights before', 'Night before', 'Wedding night', 'Night after', 'Two nights after']
HM_STATUS = ['Idea', 'Quote received', 'Booked']
HSOURCE = ['Savings', 'Cash gifts']
PERSONS = [r['person'] for r in party_rows()]
TLINES = ['Venue', 'Food and drink', 'Photo and video', 'Music', 'Flowers and decor', 'Attire and alterations', 'Stationery and postage', 'Ceremony and officiant', 'Rentals and cake',
          'Other events', 'Planner and travel', 'Tips, fees and reserve']
HSCEN = ['Option A as planned', 'Option A without activities', 'Option A, three days shorter', 'Option B as planned', 'Option B, two days longer', 'Option B plus the beach activities']
TINPUT = ['Big wedding guests', 'Ceremony guests', 'Party guests', 'Ceremony venue cost', 'Party venue cost', 'Ceremony food per guest', 'Party food per guest', 'Events in the small track']
CITEM = ['Events done', 'Events planned', 'Party travel the couple covers', 'Couple travel and stay', 'Honeymoon trip, chosen option', 'Honeymoon reserve, chosen option']

BASE_LISTS = [
    L('event', 'Event', P(EVENT_NAMES)), L('estatus', 'Event status', P(EVENT_STATUS)), L('item', 'Event line item', P(LINE_ITEMS)), L('night', 'Night', P(NIGHTS)),
    L('hoption', 'Honeymoon option', P(HONEY_OPTIONS)), L('hkind', 'Honeymoon cost kind', P(HONEY_KINDS)), L('hmstatus', 'Honeymoon item status', P(HM_STATUS)),
    L('hsource', 'Honeymoon fund source', P(HSOURCE)), L('fstatus', 'Funding status', P(FUND_STATUS)), L('category', 'Budget category', P(BUDGET_CATEGORIES)),
    L('prole', 'Wedding party role', P(PARTY_ROLES)), L('person', 'Person', P(PERSONS)), L('pkind', 'Paperwork kind', P(PAPER_KINDS)), L('tstatus', 'Task status', P(TASK_STATUS)),
    L('tline', 'Two-track line', P(TLINES)), L('hscen', 'Honeymoon scenario', P(HSCEN)), L('tinput', 'Track input', P(TINPUT)), L('citem', 'Combined cost item', P(CITEM)),
]
_M = {'event': K(EVENT_NAMES), 'estatus': K(EVENT_STATUS), 'item': K(LINE_ITEMS), 'night': K(NIGHTS), 'hoption': K(HONEY_OPTIONS), 'hkind': K(HONEY_KINDS), 'hmstatus': K(HM_STATUS),
      'hsource': K(HSOURCE), 'fstatus': K(FUND_STATUS), 'category': K(BUDGET_CATEGORIES), 'prole': K(PARTY_ROLES), 'person': K(PERSONS), 'pkind': K(PAPER_KINDS), 'tstatus': K(TASK_STATUS),
      'tline': K(TLINES), 'hscen': K(HSCEN), 'tinput': K(TINPUT), 'citem': K(CITEM)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])


# verdict and flag words: two lists of at most 30 values, filled in the order the words are first used
_VW = {'va': [], 'vb': []}
_VK = {}
def v(label):
    """token of a verdict word (list va or vb); the word is added to the list on first use"""
    if label not in _VK:
        name = 'va' if len(_VW['va']) < 30 else 'vb'
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
    for name, lab in (('va', 'Verdict words A'), ('vb', 'Verdict words B')):
        vals = _VW[name]
        if len(vals) == 1: vals = vals + [('Not used', 'not_used')]
        if vals: out.append(L(name, lab, [(k, l) for l, k in vals]))
    return out


def vkey(label): return _VK[label][1]
