"""Wedding suite part 6 (Wedding Party and Day-Of Run-of-Show): label lists, the verdict-word registry and the list helpers."""
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


PSIDES = ['Partner 1', 'Partner 2']
PAIDBY = ['Own', 'Couple', 'Parent', 'Sibling', 'Friend']
PLACES = ['Hotel', 'Venue', 'Transport']
PERSONS = [r['person'] for r in party_rows()]
VNAMES = [x['vendor'] for x in vendor_rows()]
HANDERS = ['Both partners', 'Parent of partner 1', 'Wedding party lead', 'Day-of coordinator', 'Friend or relative']
HITEMS = ['Vendors may enter', 'Guests may enter', 'Bar closes', 'Music must end', 'Venue closes']
DUTIES = ['Gifts table and gift log', 'Cards and card box', 'Tip envelopes', 'Final payments on the day', 'Rentals and returns', 'Programs and place cards', 'Flowers to the hotel',
          'Cake box and leftovers', 'Keys and venue hand-back', 'Lost property', 'Gifts and cards to the car', 'Family photo list']
HELPERS = ['Maren Lindqvist', 'Yuki Tanaka', 'Ingrid Solberg', 'Priya Nair', 'Chidi Okafor', 'Mateo Moreno', 'Jonas Lindqvist', 'Zainab Okafor']

BASE_LISTS = [
    L('role', 'Team role', P(ROLES)), L('team', 'Team', P(TEAMS)), L('pside', 'Side', P(PSIDES)), L('prole', 'Wedding party role', P(PARTY_ROLES)), L('attire', 'Attire status', P(ATTIRE_STATUS)),
    L('paidby', 'Outfit paid by', P(PAIDBY)), L('who', 'Who', P(RUN_WHO)), L('block', 'Run of show block', P(RUN_BLOCKS)), L('place', 'Place', P(PLACES)), L('person', 'Person', P(PERSONS)),
    L('vname', 'Vendor', P(VNAMES)), L('hander', 'Hands out the envelope', P(HANDERS)), L('tstatus', 'Status', P(TASK_STATUS)), L('hitem', 'Venue hours item', P(HITEMS)),
    L('duty', 'Day-of duty', P(DUTIES)), L('helper', 'Named person', P(HELPERS)),
]
_M = {'role': K(ROLES), 'team': K(TEAMS), 'pside': K(PSIDES), 'prole': K(PARTY_ROLES), 'attire': K(ATTIRE_STATUS), 'paidby': K(PAIDBY), 'who': K(RUN_WHO), 'block': K(RUN_BLOCKS), 'place': K(PLACES),
      'person': K(PERSONS), 'vname': K(VNAMES), 'hander': K(HANDERS), 'tstatus': K(TASK_STATUS), 'hitem': K(HITEMS), 'duty': K(DUTIES), 'helper': K(HELPERS)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])


# verdict and flag words: lists of at most 30 values, filled in the order the words are first used
_VW = {'va': [], 'vb': [], 'vc': []}
_VK = {}
def v(label):
    """token of a verdict word (list va, vb or vc); the word is added to the list on first use"""
    if label not in _VK:
        name = next(n_ for n_ in ('va', 'vb', 'vc') if len(_VW[n_]) < 30)
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
    for name, lab in (('va', 'Verdict words A'), ('vb', 'Verdict words B'), ('vc', 'Verdict words C')):
        vals = _VW[name]
        if len(vals) == 1: vals = vals + [('Not used', 'not_used')]
        if vals: out.append(L(name, lab, [(k, l) for l, k in vals]))
    return out


def vkey(label): return _VK[label][1]
