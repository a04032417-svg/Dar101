"""Doula business suite part 7 (Referrals, Classes, Reviews, Marketing): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from du_core import *
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


RSOURCES = ['Care provider', 'Past client', 'Support professional', 'Class or workshop']
MNAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
SCEN = ['Base', 'Best', 'Worst']
# labels that table formulas and tool verdicts return (a formula never types a word: it points at the list cell)
CKA = ['Thanked', 'Thank-you due', 'Thank-you missed', 'No client yet', 'Up to date', 'Ask now', 'Asked, waiting', 'Send reminder', 'Answered', 'Not yet due',
       'Above break-even', 'Below break-even', 'Silent this year', 'Sending less', 'Still sending', 'Visit', 'Thank', 'Hold', 'Feed', 'Cut', 'Keep', 'Renegotiate', 'Drop',
       'Run', 'Reprice', 'Raise', 'Lower']
CK2 = ['Thank-yous to send', 'worth', 'No thank-yous due', 'Visit or call first', 'No silent referrers', 'sign-ups needed, you averaged', 'Cannot break even with these seats',
       'Add a session in', 'Enough sessions in', 'Ask clients today', 'No review requests due', 'Ask more often', 'Steady', 'Stars slipping', 'Stars steady', 'Stars improving',
       'Classes bring clients', 'Classes are a cost', 'Too reliant on', 'Sources are spread', 'Budget for gifts', 'Over the gift setting', 'Ask for a referral',
       'No past client to ask yet', 'Expect class income of', 'Converts best', 'Raise the price', 'Hold the price', 'Lower the price', 'Reminders to send']
CK3 = ['Office to visit', 'Offices are steady', 'Within the gift setting', 'Review rate is below your target', 'Review rate is on target', 'Marketing cost is high',
       'Referral clients carry income', 'Not enough history']
assert len(CKA) <= 30 and len(CK2) <= 30 and len(CK3) <= 30

lists = [
    L('source', 'Source', P(SOURCES)), L('rsource', 'Referral source', P(RSOURCES)), L('ctype', 'Class type', P(CLASS_TYPES)), L('mkind', 'Marketing kind', P(MARKETING_KINDS)),
    L('channel', 'Review channel', P(CHANNELS)), L('doula', 'Doula', P(DOULA_NAMES)), L('cstatus', 'Client status', P(CLIENT_STATUS)), L('ckind', 'Client kind', P(CLIENT_KINDS)),
    L('estatus', 'Enquiry status', P(ENQUIRY_STATUS)), L('lostreason', 'Lost reason', P(LOST_REASONS)), L('role', 'Role', P(ROLES)), L('ctstatus', 'Contract status', P(CONTRACT_STATUS)),
    L('scen', 'Scenario', P(SCEN)), L('mname', 'Month name', P(MNAMES)), L('cka', 'Check result', P(CKA)), L('ck2', 'Verdict A', P(CK2)), L('ck3', 'Verdict B', P(CK3)),
]
assert len(lists) <= 20
_M = {'source': K(SOURCES), 'rsource': K(RSOURCES), 'ctype': K(CLASS_TYPES), 'mkind': K(MARKETING_KINDS), 'channel': K(CHANNELS), 'doula': K(DOULA_NAMES), 'cstatus': K(CLIENT_STATUS),
      'ckind': K(CLIENT_KINDS), 'estatus': K(ENQUIRY_STATUS), 'lostreason': K(LOST_REASONS), 'role': K(ROLES), 'ctstatus': K(CONTRACT_STATUS), 'scen': K(SCEN), 'mname': K(MNAMES),
      'cka': K(CKA), 'ck2': K(CK2), 'ck3': K(CK3)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def ca(label): return tok('cka', label)
def c2(label): return tok('ck2', label)
def c3(label): return tok('ck3', label)
