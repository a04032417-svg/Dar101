"""Car rental suite part 2 (Booking Calendar and Availability): label lists shared by data, tables, tools."""
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


CAL_STATUS = ['Rented', 'Reserved', 'Service', 'Free']
BANDS = ['Same or next day', '2 to 7 days', '8 to 14 days', '15 to 30 days', 'Over 30 days']
CX_KINDS = ['Cancelled', 'No-show']
EXT_DEC = ['Open', 'Approved', 'Declined']
SWAP_WHY = ['Service due', 'Damage', 'Breakdown', 'Renter request', 'Overlap fix']
PK_KINDS = ['Pickup', 'Return']
SCEN = ['Base', 'Best', 'Worst']
# verdicts of the tables (VR) and of the tools (VT1, VT2); every label is used by a formula through v('label')
VR = ['Clear', 'Tight turn', 'Inside turnaround time', 'Overlaps another booking', 'Not holding the car', 'Extend', 'Extend with a swap to', 'Cannot extend', 'Close listing', 'Hold',
      'Promote', 'Fill this gap', 'Short gap', 'Car ready', 'Check the car', 'Call the renter', 'Move the next pickup', 'No effect', 'Free notice', 'Late cancellation',
      'No-show fee', 'Falls in a service block', 'Yes', 'No']
VT1 = ['Offer car', 'Offer class from the next free date', 'Cannot offer', 'Overlaps booking', 'Inside turnaround time by', 'Full', 'Gap to fill', 'Idle', 'Swap to',
       'No car of this class is free', 'nets less a day than direct', 'nets about the same as direct', 'List more cars', 'List fewer cars', 'Hold the mix', 'Second person needed at hour',
       'Covered', 'Block marketplace listings for', 'Safe']
VT2 = ['Raise the buffer to', 'Keep the buffer', 'Tighten the cancellation fee', 'Acceptable', 'Ahead of last year', 'On pace', 'Behind by', 'Move booking',
       'No car free for booking', 'No booking affected', 'dates to block today', 'Nothing to block today', 'Free upgrade', 'Charge the difference', 'Decline', 'Promote weekly',
       'Open', 'Not enough history']
VT2 = [x for x in VT2 if x != 'Open']
assert not (set(VR) & set(VT1) | set(VR) & set(VT2) | set(VT1) & set(VT2))

lists = [
    L('class', 'Vehicle class', P(CLASSES)), L('channel', 'Channel', P(CHANNELS)), L('location', 'Pickup location', P(LOCATIONS)), L('plan', 'Plan', P(PLANS)), L('season', 'Season', P(SEASONS)),
    L('bstatus', 'Booking status', P(BOOK_STATUS)), L('vstatus', 'Vehicle status', P(VEH_STATUS)), L('mkind', 'Service kind', P([k for k in MAINT_KINDS if k != 'Towing'])), L('calst', 'Day status', P(CAL_STATUS)),
    L('wday', 'Weekday', P(WEEKDAYS)), L('band', 'Lead time band', P(BANDS)), L('cxkind', 'Cancellation kind', P(CX_KINDS)), L('extdec', 'Extension decision', P(EXT_DEC)),
    L('swapwhy', 'Swap reason', P(SWAP_WHY)), L('pkind', 'Pickup or return', P(PK_KINDS)), L('scen', 'Scenario', P(SCEN)), L('vr', 'Result', P(VR)), L('vt1', 'Verdict A', P(VT1)), L('vt2', 'Verdict B', P(VT2)),
]
assert len(lists) <= 20
_M = {'class': K(CLASSES), 'channel': K(CHANNELS), 'location': K(LOCATIONS), 'plan': K(PLANS), 'season': K(SEASONS), 'bstatus': K(BOOK_STATUS), 'vstatus': K(VEH_STATUS), 'mkind': K([k for k in MAINT_KINDS if k != 'Towing']),
      'calst': K(CAL_STATUS), 'wday': K(WEEKDAYS), 'band': K(BANDS), 'cxkind': K(CX_KINDS), 'extdec': K(EXT_DEC), 'swapwhy': K(SWAP_WHY), 'pkind': K(PK_KINDS), 'scen': K(SCEN),
      'vr': K(VR), 'vt1': K(VT1), 'vt2': K(VT2)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
_V = {}
for _l in ('vr', 'vt1', 'vt2'):
    for _x in _M[_l]: _V[_x] = _l
def v(label): return tok(_V[label], label)          # token of a verdict label wherever it lives
def vkey(label): return key(_V[label], label)
