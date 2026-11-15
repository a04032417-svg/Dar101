"""Car rental suite part 1 (Enquiries, Quotes and Rate Card): label lists shared by data, tables, tools."""
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


HANDLERS = [OWNER, MANAGER, 'Sana Malik']
SOURCES = ['Website', 'Phone', 'Corporate account', 'Hotel partner']
BANDS = ['Within 1 hour', '1 to 4 hours', '4 to 24 hours', 'Over 24 hours', 'Not replied yet']
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
SCENARIOS = ['Base', 'Best', 'Worst']
VKA = ['Above floor', 'Thin margin', 'Below floor', 'Step pays back', 'Chase now', 'Chase soon', 'Fresh quote']
VKB = ['Quote ready', 'Below the floor price', 'Price above floor', 'Raise the price', 'Raise', 'Hold', 'Lower', 'Keep', 'Raise the step', 'Lower the step',
       'Push the top add-on', 'On target', 'Below target', 'Price covers', 'Raise the surcharge', 'Match', 'Decline', 'Rise now', 'Rise at the set date', 'No rise needed',
       'Offer', 'Counter at the floor', 'Accept 1-day rentals', 'Set a minimum stay', 'Capacity short', 'Enough cars']
VKC = ['Reply sooner', 'Reply time on target', 'Feed', 'Hold source', 'Cut', 'Chase this quote first', 'Weakest step: reply', 'Weakest step: quote', 'Weakest step: close',
       'Fix price', 'Fix availability', 'Fix dates', 'Fix replies', 'Fix other reasons', 'Raise the weekend rate', 'Hold the weekend rate', 'No open quotes']
assert max(len(x) for x in VKA + VKB + VKC) <= 40

lists = [
    L('class', 'Vehicle class', P(CLASSES)), L('channel', 'Channel', P(CHANNELS)), L('location', 'Pickup place', P(LOCATIONS)), L('season', 'Season', P(SEASONS)),
    L('plan', 'Plan', P(PLANS)), L('addon', 'Add-on', P(ADDONS)), L('estatus', 'Enquiry status', P(ENQ_STATUS)), L('lostreason', 'Lost reason', P(LOST_REASONS)),
    L('ekind', 'Event kind', P(EVENT_KINDS)), L('wday', 'Weekday', P(WEEKDAYS)), L('handler', 'Handled by', P(HANDLERS)), L('source', 'Enquiry source', P(SOURCES)),
    L('band', 'Reply time band', P(BANDS)), L('moy', 'Month of the year', P(MONTHS)), L('scen', 'Scenario', P(SCENARIOS)),
    L('vka', 'Check result', P(VKA)), L('vkb', 'Verdict A', P(VKB)), L('vkc', 'Verdict B', P(VKC)),
]
assert len(lists) <= 20
_M = {'class': K(CLASSES), 'channel': K(CHANNELS), 'location': K(LOCATIONS), 'season': K(SEASONS), 'plan': K(PLANS), 'addon': K(ADDONS), 'estatus': K(ENQ_STATUS),
      'lostreason': K(LOST_REASONS), 'ekind': K(EVENT_KINDS), 'wday': K(WEEKDAYS), 'handler': K(HANDLERS), 'source': K(SOURCES), 'band': K(BANDS), 'moy': K(MONTHS),
      'scen': K(SCENARIOS), 'vka': K(VKA), 'vkb': K(VKB), 'vkc': K(VKC)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ka(label): return tok('vka', label)
def kb(label): return tok('vkb', label)
def kc(label): return tok('vkc', label)
