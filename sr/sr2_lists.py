"""Short-term rental host suite part 2: label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sr_core import *
from lib import L, LV


def P(labels):
    out, seen = [], set()
    for k, l in pairs(labels):
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


TAXBY = ['Platform', 'Host']
CREASON = ['Guest changed plans', 'Travel problem', 'Found another place', 'Host cancelled', 'Payment failed', 'Guest unwell', 'Dates mixed up', 'Other reason']
BAND = ['Same week', 'One to two weeks', 'Two to four weeks', 'One to three months', 'Over three months']
BSRC = ['Platform search', 'Direct website', 'Returning guest', 'Referral', 'Phone call', 'Local partner', 'Message to the host']
CHKIND = ['Dates moved earlier', 'Dates moved later', 'Stay extended', 'Stay shortened', 'Guests added', 'Unit swapped']
NKIND = ['Guest request', 'Payment note', 'Late arrival', 'Early arrival', 'Price agreement', 'Change request', 'Platform message', 'Special occasion']
CANSWER = ['Payment released', 'Amount confirmed', 'Waiting for the platform', 'Claim opened', 'Difference explained', 'No answer yet']
POLICY = ['Flexible', 'Moderate', 'Strict']
# labels that formulas return (never typed text inside a formula)
CKA = ['Received on time', 'Received late', 'Received short', 'Chase now', 'Due soon', 'Payout scheduled', 'Kept most of it', 'Kept part', 'Kept nothing', 'Balance paid', 'Balance overdue',
       'Balance due soon', 'Balance later', 'Tax matches', 'Tax differs', 'Tight turnover', 'Normal turnover', 'Roomy turnover', 'Arrives today', 'Arrives this week', 'Arrives later',
       'Stay under way', 'Stay ended', 'Repeat guest', 'First stay', 'Recent guest', 'Lapsed guest']
CKB = ['Stay longer', 'Stay shorter', 'Same length', 'Direct booking', 'Platform booking', 'Host remits tax', 'Platform remits tax', 'Fee above 10 percent', 'Fee up to 10 percent',
       'Fee on booking', 'Fee on payment', 'Fee on cleaning', 'Fee on cancellation', 'Fee on early payout', 'Fee on promotion', 'Note is open', 'Note is closed', 'Chase is open', 'Chase is closed',
       'Discount on target', 'Discount low', 'Discount high', 'Large booking', 'Small booking', 'Typical booking']
CK2 = ['Dates are free', 'Clash with another booking', 'Payout in full', 'Payout short, claim the difference', 'Payout late, chase now', 'Payout not due yet', 'Full refund', 'Part refund',
       'No refund', 'Schedule fits before check-in', 'Pay the full amount now', 'Direct earns the host more', 'Platform earns the host more', 'Price rises', 'Price falls', 'Price unchanged',
       'Host remits the tax', 'Platform remits the tax', 'Claim the full amount', 'Claim the difference', 'Wait for the grace days', 'Discount is generous', 'Discount is modest', 'Profit per night is healthy',
       'Profit per night is thin', 'Loss on this stay', 'Booking fits the unit']
assert len(CKA) <= 30 and len(CKB) <= 30 and len(CK2) <= 30

lists = [
    L('role', 'Role', P(ROLES)), L('team', 'Team', P(TEAMS)), L('yn', 'Yes or no', P(YESNO)), L('utype', 'Unit type', P(UNIT_TYPES)), L('city', 'City', P(CITIES)), L('chan', 'Booking channel', P(CHANNELS)),
    L('bstatus', 'Booking status', P(BOOKING_STATUS)), L('payst', 'Payout status', P(PAYOUT_STATUS)), L('taxby', 'Local tax collected by', P(TAXBY)), L('creason', 'Cancellation reason', P(CREASON)),
    L('band', 'Lead time or notice', P(BAND)), L('bsrc', 'Booking source', P(BSRC)), L('chkind', 'Change kind', P(CHKIND)), L('nkind', 'Note kind', P(NKIND)), L('canswer', 'Payout chase answer', P(CANSWER)),
    L('policy', 'Cancellation policy', P(POLICY)),
    L('cka', 'Check result A', P(CKA)), L('ckb', 'Check result B', P(CKB)), L('ck2', 'Calculator verdict', P(CK2)),
]
_M = {'role': K(ROLES), 'team': K(TEAMS), 'yn': K(YESNO), 'utype': K(UNIT_TYPES), 'city': K(CITIES), 'chan': K(CHANNELS), 'bstatus': K(BOOKING_STATUS), 'payst': K(PAYOUT_STATUS), 'taxby': K(TAXBY),
      'creason': K(CREASON), 'band': K(BAND), 'bsrc': K(BSRC), 'chkind': K(CHKIND), 'nkind': K(NKIND), 'canswer': K(CANSWER), 'policy': K(POLICY), 'cka': K(CKA), 'ckb': K(CKB), 'ck2': K(CK2)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ca(label): return tok('cka', label)
def cb(label): return tok('ckb', label)
def ck2(label): return tok('ck2', label)
