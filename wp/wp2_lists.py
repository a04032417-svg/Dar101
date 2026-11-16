"""Wedding suite part 2 (Guests, Invitations and RSVPs): label lists, the verdict-word registry and the list helpers."""
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
WEEKS = ['Week %d' % i for i in range(1, 13)]
POLICIES = ['Named guests and open plus-ones', 'Named guests only', 'Adults only', 'Adults and family children', 'No plus-ones, family children']
SCENARIOS = ['Confirmed yes', 'Low', 'Expected', 'High', 'Everyone says yes', 'Seated capacity']
PAPER_ITEMS = ['Save the date card', 'Invitation card', 'Reply card', 'Details card', 'Envelope', 'Reminder card', 'Place card', 'Order of service', 'Postage, local',
               'Postage, same country', 'Postage, abroad', 'Thank-you card']

BASE_LISTS = [
    L('side', 'Side', P(SIDES)), L('tier', 'Tier', P(TIERS)), L('listab', 'Invitation list', P(LIST_AB)), L('region', 'Region', P(REGIONS)), L('rsvp', 'RSVP', P(RSVP)),
    L('cstat', 'Contact status', P(CONTACT_STATUS)), L('channel', 'Chase channel', P(CHANNELS)), L('lodging', 'Lodging', P(LODGING)), L('meal', 'Meal choice', P(MEALS)),
    L('dietary', 'Dietary note', P(DIETARY)), L('age', 'Age group', P(AGE_GROUPS)), L('table', 'Table', P(TABLE_IDS)), L('week', 'Reply week', P(WEEKS)),
    L('policy', 'Guest policy', P(POLICIES)), L('scen', 'Headcount scenario', P(SCENARIOS)), L('pitem', 'Paper item', P(PAPER_ITEMS)),
]
_M = {'side': K(SIDES), 'tier': K(TIERS), 'listab': K(LIST_AB), 'region': K(REGIONS), 'rsvp': K(RSVP), 'cstat': K(CONTACT_STATUS), 'channel': K(CHANNELS), 'lodging': K(LODGING),
      'meal': K(MEALS), 'dietary': K(DIETARY), 'age': K(AGE_GROUPS), 'table': K(TABLE_IDS), 'week': K(WEEKS), 'policy': K(POLICIES), 'scen': K(SCENARIOS), 'pitem': K(PAPER_ITEMS)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])


# verdict and flag words: two lists of at most 30 values, filled in the order the words are first used
_VW = {'va': [], 'vb': [], 'vc': [], 'vd': []}
_VK = {}
def v(label):
    """token of a verdict word (list va or vb); the word is added to the list on first use"""
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


def vkey(label): return _VK[label][1]
