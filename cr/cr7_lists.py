"""Car rental suite part 7 (Utilisation, Profit and Pricing Review): label lists shared by data, tables and tools."""
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


BANDS = ['Red', 'Amber', 'Green']
VERDICTS = ['Keep', 'Reprice', 'Sell']
FLAGS = ['Below last year', 'In line', 'Above last year']
SCENARIOS = ['Base', 'Best', 'Worst']
BE = ['Above break-even', 'Below break-even']

lists = [
    L('class', 'Vehicle class', P(CLASSES)), L('channel', 'Channel', P(CHANNELS)), L('plan', 'Rental plan', P(PLANS)), L('season', 'Season', P(SEASONS)),
    L('bstatus', 'Booking status', P(BOOK_STATUS)), L('vstatus', 'Vehicle status', P(VEH_STATUS)), L('wday', 'Weekday', P(WEEKDAYS)), L('band', 'Utilisation band', P(BANDS)),
    L('verdict', 'Vehicle verdict', P(VERDICTS)), L('flag', 'Rate flag', P(FLAGS)), L('scenario', 'Scenario', P(SCENARIOS)), L('be', 'Break-even status', P(BE)),
]
assert len(lists) <= 20
_M = {'class': K(CLASSES), 'channel': K(CHANNELS), 'plan': K(PLANS), 'season': K(SEASONS), 'bstatus': K(BOOK_STATUS), 'vstatus': K(VEH_STATUS), 'wday': K(WEEKDAYS), 'band': K(BANDS),
      'verdict': K(VERDICTS), 'flag': K(FLAGS), 'scenario': K(SCENARIOS), 'be': K(BE)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])

# verdict wording: a formula may not hold a text literal with letters, so each phrase is a list label
import re
PHR = []
def ph(t):
    if t not in PHR: PHR.append(t)
    i = PHR.index(t); return '{list:ph%d.p%d}' % (i // 30 + 1, i)
_LIT = re.compile(r'"([^"]*)"')
def fixlit(f):
    def rep(m):
        s = m.group(1)
        if not re.search(r'[A-Za-z]', s): return m.group(0)
        core = s.strip(); lead = s[:len(s) - len(s.lstrip())]; trail = s[len(s.rstrip()):]
        out = ph(core)
        if lead: out = '" "&' + out
        if trail: out = out + '&" "'
        return '(' + out + ')' if (lead or trail) else out
    return _LIT.sub(rep, f)
def phrase_lists():
    n = (len(PHR) + 29) // 30; out = []
    for k in range(n):
        vals = [('p%d' % i, PHR[i]) for i in range(k * 30, min(len(PHR), (k + 1) * 30))]
        while len(vals) < 2: vals.append(('x%d' % len(vals), 'Check'))
        out.append(L('ph%d' % (k + 1), 'Verdict wording %d' % (k + 1), vals))
    return out
