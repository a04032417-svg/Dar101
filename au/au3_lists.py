"""Part 3 (Sales and Royalties Ledger): label lists shared by data, tables and tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from au_core import *
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


FLAG = ['Within limit', 'Above limit']
V1 = ['Paid in full', 'Short-paid', 'Overdue', 'Not yet due', 'No statement', 'Wait', 'Write today', 'Escalate', 'Claim now', 'Within tolerance']
V2 = ['Cash arrives as planned', 'Gap in month 1', 'Gap in month 2', 'Gap in month 3', 'Gap in month 4', 'Batch payments', 'Fine', 'Price holds', 'Raise the price', 'Income at risk', 'Stable']
V3 = ['Stay in the program', 'Test going wide', 'Push audio', 'Push paperback', 'Balanced', 'Diversify', 'Keep the mix', 'Hedge by pricing', 'Exposure is fine', 'Close the month', 'Wait for stores']
V4 = ['Above your average', 'Near your average', 'Below your average', 'Top three carry over half', 'Spread across titles', 'Advertise in the top country', 'Hold', 'Ask the store for the report', 'Normal', 'Up', 'Flat', 'Down']
V5 = ['Withdraw monthly'] + ['Withdraw every %d months' % n for n in range(2, 13)]

lists = [
    L('store', 'Store', P(STORES)), L('format', 'Format', P(FORMATS)), L('country', 'Country', P(COUNTRIES)), L('currency', 'Currency', P(CURRENCIES)),
    L('penname', 'Pen name', P(PEN_NAMES)), L('series', 'Series', P(SERIES)), L('tstatus', 'Title status', P(TITLE_STATUS)), L('estatus', 'Edition status', P(EDITION_STATUS)),
    L('ststatus', 'Statement status', P(STATEMENT_STATUS)), L('flag', 'Limit check', P(FLAG)), L('v1', 'Verdict A', P(V1)), L('v2', 'Verdict B', P(V2)), L('v3', 'Verdict C', P(V3)),
    L('v4', 'Verdict D', P(V4)), L('v5', 'Verdict E', P(V5)),
]
assert len(lists) <= 20
_M = {'store': K(STORES), 'format': K(FORMATS), 'country': K(COUNTRIES), 'currency': K(CURRENCIES), 'penname': K(PEN_NAMES), 'series': K(SERIES), 'tstatus': K(TITLE_STATUS),
      'estatus': K(EDITION_STATUS), 'ststatus': K(STATEMENT_STATUS), 'flag': K(FLAG), 'v1': K(V1), 'v2': K(V2), 'v3': K(V3), 'v4': K(V4), 'v5': K(V5)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
