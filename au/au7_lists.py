"""Author and self-publisher suite part 7 (Direct Sales, Stock, Events and Rights): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from au_core import *
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


PRINT_FORMATS = ['Paperback', 'Hardcover', 'Large print']
SCEN = ['Base', 'Best', 'Worst']
PERIODS = ['All history', 'Last 12 months', 'Before that']
# labels that table formulas and tool verdicts return (a formula points at the list cell)
V1 = ['Direct pays more', 'Store pays more', 'Price too low', 'Price holds', 'Raise the price', 'On track', 'Behind', 'Worth moving', 'Keep in the store', 'Margin holds', 'Order now', 'Order fewer']
V2 = ['Count matches', 'Recount', 'Reprint now', 'Wait', 'Enough stock', 'Reprint first', 'Collect', 'Closed']
V3 = ['Go again', 'Go again with changes', 'Skip', 'Book it', 'Negotiate', 'Do more', 'Change or drop']
V4 = ['Received', 'Overdue', 'Due in 30 days', 'Due soon', 'Later', 'Cash arriving', 'Chase the agent', 'Renew', 'Take back', 'Decide by date', 'Accept', 'Counter', 'Decline',
      'On track for the target', 'Below the target', 'No deal ends soon']

lists = [
    L('role', 'Role', P(ROLES)), L('team', 'Team', P(TEAMS)), L('paytype', 'Pay type', P(PAY_TYPES)), L('format', 'Format', P(FORMATS)), L('pformat', 'Print format', P(PRINT_FORMATS)),
    L('estatus', 'Edition status', P(EDITION_STATUS)), L('store', 'Store', P(STORES)), L('country', 'Country', P(COUNTRIES)), L('currency', 'Currency', P(CURRENCIES)),
    L('ekind', 'Event kind', P(EVENT_KINDS)), L('move', 'Stock move', P(STOCK_MOVES)), L('dkind', 'Deal kind', P(DEAL_KINDS)), L('dstatus', 'Deal status', P(DEAL_STATUS)), L('scen', 'Scenario', P(SCEN)),
    L('period', 'Period', P(PERIODS)), L('v1', 'Verdict, direct and print', P(V1)), L('v2', 'Verdict, stock and rights', P(V2)), L('v3', 'Verdict, events', P(V3)), L('v4', 'Verdict, rights and forecast', P(V4)),
]
assert len(lists) <= 20
_M = {'role': K(ROLES), 'team': K(TEAMS), 'paytype': K(PAY_TYPES), 'format': K(FORMATS), 'pformat': K(PRINT_FORMATS), 'estatus': K(EDITION_STATUS), 'store': K(STORES), 'country': K(COUNTRIES),
      'currency': K(CURRENCIES), 'ekind': K(EVENT_KINDS), 'move': K(STOCK_MOVES), 'dkind': K(DEAL_KINDS), 'dstatus': K(DEAL_STATUS), 'scen': K(SCEN), 'period': K(PERIODS), 'v1': K(V1), 'v2': K(V2), 'v3': K(V3), 'v4': K(V4)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def v1(l): return tok('v1', l)
def v2(l): return tok('v2', l)
def v3(l): return tok('v3', l)
def v4(l): return tok('v4', l)
