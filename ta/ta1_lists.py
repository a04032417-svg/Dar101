"""Travel agent suite part 1: label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ta_core import *
from lib import L, LV


def P(labels):
    """pairs() with list keys cut to 21 characters, unique inside the list"""
    out, seen = [], set()
    for k, l in pairs(labels):
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


OUTCOME = ['Ready for a quote', 'Wants options', 'Needs more time', 'Waiting for a partner', 'No answer', 'Will book', 'Declined']
CHANNEL = ['Phone call', 'E-mail', 'Text message', 'Video call', 'Messaging', 'In person']
LREASON = ['Price too high', 'Chose another advisor', 'Not travelling this year', 'No reply after the quote', 'Booked direct with the supplier', 'Dates did not fit']
PACE = ['Relaxed', 'Balanced', 'Busy']
SEASON = ['Peak', 'Shoulder', 'Low']
PKIND = ['Wedding planner', 'Corporate contact', 'Community leader', 'Trade partner']
# labels that formulas return (never typed text inside a formula)
CKA = ['Follow-up planned', 'Follow-up overdue', 'No follow-up set', 'Closed', 'Reply on time', 'Reply late', 'Quote on time', 'Quote late', 'No quote yet', 'Above usual budget', 'Usual budget',
       'Chase now', 'Expired still open', 'Waiting', 'Margin on target', 'Margin under target', 'Deposit paid', 'Deposit awaited', 'Deposit overdue', 'Not needed', 'Touch overdue',
       'Touch planned', 'No next touch', 'Repeat client', 'One trip', 'No trip yet']
CKB = ['Free capacity', 'Tight week', 'Over capacity', 'Fits this week', 'Does not fit this week', 'Thank-you due', 'Thanked', 'Peak month', 'Quiet month', 'Normal month', 'Converts well',
       'Low conversion', 'Review due', 'Review planned', 'Next step passed', 'Next step planned', 'No next step', 'Gap is large', 'Gap is small', 'Window is short', 'Window is wide',
       'Budget is realistic', 'Budget is stretched', 'Fee is waived', 'Fee applies']
CK2 = ['Margin on target', 'Margin under target', 'Budget is enough', 'Budget is thin', 'Budget is too low', 'Win chance is high', 'Win chance is moderate', 'Win chance is low',
       'Capacity fits', 'Capacity is short', 'Source pays back', 'Source does not pay back', 'Option A earns more', 'Option B earns more', 'Both earn the same', 'Offer fewer nights',
       'Offer a lower hotel tier', 'Offer cheaper dates', 'Keep the price', 'Quote can go out now', 'Final payment is far', 'Raise the fee first', 'Price hold ends first', 'Quote expiry ends first', 'Final payment is near',
       'Add-on earns commission', 'Add-on earns no commission']
assert len(CKA) <= 30 and len(CKB) <= 30 and len(CK2) <= 30

lists = [
    L('role', 'Role', P(ROLES)), L('team', 'Team', P(TEAMS)), L('ttype', 'Trip type', P(TRIP_TYPES)), L('tstatus', 'Trip status', P(TRIP_STATUS)), L('scat', 'Supplier category', P(SUPPLIER_CATEGORIES)),
    L('ckind', 'Client kind', P(CLIENT_KINDS)), L('stage', 'Client stage', P(CLIENT_STAGES)), L('enqst', 'Enquiry status', P(ENQ_STATUS)), L('quotest', 'Quote status', P(QUOTE_STATUS)),
    L('msrc', 'Marketing source', P(MARKETING_SOURCES)), L('yn', 'Yes or no', P(YESNO)), L('outcome', 'Outcome', P(OUTCOME)), L('channel', 'Contact channel', P(CHANNEL)),
    L('lreason', 'Lost reason', P(LREASON)), L('pace', 'Trip pace', P(PACE)), L('season', 'Season', P(SEASON)), L('pkind', 'Partner kind', P(PKIND)),
    L('cka', 'Check result A', P(CKA)), L('ckb', 'Check result B', P(CKB)), L('ck2', 'Calculator verdict', P(CK2)),
]
assert len(lists) == 20
_M = {'role': K(ROLES), 'team': K(TEAMS), 'ttype': K(TRIP_TYPES), 'tstatus': K(TRIP_STATUS), 'scat': K(SUPPLIER_CATEGORIES), 'ckind': K(CLIENT_KINDS), 'stage': K(CLIENT_STAGES), 'enqst': K(ENQ_STATUS),
      'quotest': K(QUOTE_STATUS), 'msrc': K(MARKETING_SOURCES), 'yn': K(YESNO), 'outcome': K(OUTCOME), 'channel': K(CHANNEL), 'lreason': K(LREASON), 'pace': K(PACE), 'season': K(SEASON),
      'pkind': K(PKIND), 'cka': K(CKA), 'ckb': K(CKB), 'ck2': K(CK2)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def ca(label): return tok('cka', label)
def cb(label): return tok('ckb', label)
def ck2(label): return tok('ck2', label)
