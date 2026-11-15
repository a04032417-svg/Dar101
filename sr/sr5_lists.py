"""Short-term rental host suite part 5: label lists shared by data, tables, tools."""
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


SRES = ['Pass', 'Fixed on the spot', 'Needs repair']
QDEC = ['Waiting', 'Approved', 'Declined']
PSTAT = ['Ordered', 'Shipped', 'Delivered', 'Cancelled']
WRES = ['Waiting', 'Accepted', 'Rejected']
CXST = ['Idea', 'Planned', 'Approved', 'Done']
LEVENT = ['Code changed after check-out', 'Code changed on request', 'Battery changed', 'Key copied', 'Key lost', 'Lock repaired', 'Lock replaced']
PFIND = ['Nothing found', 'Insects', 'Rodent signs', 'Damp or mould', 'Crack or damage', 'Loose rail or tile', 'Blocked gutter']
CKA = ['Overdue', 'Due soon', 'On time', 'Closed on time', 'Closed late', 'Waiting for parts', 'Claim waiting too long', 'Claim waiting', 'Claim closed', 'Up to date', 'Superseded', 'On schedule',
       'In warranty', 'Warranty ends soon', 'Warranty expired', 'Part delivered', 'Part late', 'Part on the way', 'Passed', 'Failed', 'Incident open', 'Incident closed', 'Overloaded', 'Busy',
       'Spare capacity', 'Repeat issue', 'Watch', 'One-off', 'Clear', 'Needs action']
CKB = ['Released in full', 'Released with deduction', 'Overdue to release', 'Deposit held', 'Code safe', 'Change the code now', 'Code unchanged', 'Payback under 24 months', 'Payback over 24 months',
       'No saving counted', 'Above cost target', 'Within cost target', 'Repeat issues', 'No repeat issues', 'Quote decided', 'Quote waiting', 'Old, plan a replacement', 'Age is fine', 'Over the repair limit',
       'Within the repair limit', 'Order cancelled']
CK2 = ['Repair it', 'Replace it', 'Repair now, plan a replacement', 'Release the deposit', 'Keep part of the deposit', 'Keep the deposit', 'Claim the full amount', 'Claim the rest after the deposit',
       'Deposit covers the damage', 'Start now', 'Start by the last safe day', 'Last safe day has passed', 'Cover ended', 'Cover left', 'Pays back in time', 'Slow payback', 'Spend more, it pays',
       'Spend is enough', 'Overdue now', 'Due soon', 'Up to date', 'Handyperson has spare hours', 'Handyperson is full', 'Cost per night is high', 'Cost per night is fine', 'Cost above the limit']
assert len(CKA) <= 30 and len(CKB) <= 30 and len(CK2) <= 30

lists = [
    L('utype', 'Unit type', P(UNIT_TYPES)), L('city', 'City', P(CITIES)), L('chan', 'Booking channel', P(CHANNELS)), L('bstatus', 'Booking status', P(BOOKING_STATUS)), L('yn', 'Yes or no', P(YESNO)),
    L('tkind', 'Ticket kind', P(TICKET_KINDS)), L('prio', 'Priority', P(PRIORITIES)), L('tkst', 'Ticket status', P(TICKET_STATUS)), L('tsrc', 'Ticket source', P(TICKET_SOURCES)), L('dmst', 'Claim status', P(DAMAGE_STATUS)),
    L('sres', 'Safety result', P(SRES)), L('qdec', 'Quote decision', P(QDEC)), L('pstat', 'Parts order status', P(PSTAT)), L('wres', 'Warranty claim result', P(WRES)), L('cxst', 'Capex status', P(CXST)),
    L('levent', 'Lock event', P(LEVENT)), L('pfind', 'Pest finding', P(PFIND)), L('cka', 'Check result A', P(CKA)), L('ckb', 'Check result B', P(CKB)), L('ck2', 'Calculator verdict', P(CK2)),
]
assert len(lists) == 20
_M = {'utype': K(UNIT_TYPES), 'city': K(CITIES), 'chan': K(CHANNELS), 'bstatus': K(BOOKING_STATUS), 'yn': K(YESNO), 'tkind': K(TICKET_KINDS), 'prio': K(PRIORITIES), 'tkst': K(TICKET_STATUS),
      'tsrc': K(TICKET_SOURCES), 'dmst': K(DAMAGE_STATUS), 'sres': K(SRES), 'qdec': K(QDEC), 'pstat': K(PSTAT), 'wres': K(WRES), 'cxst': K(CXST), 'levent': K(LEVENT), 'pfind': K(PFIND),
      'cka': K(CKA), 'ckb': K(CKB), 'ck2': K(CK2)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ca(label): return tok('cka', label)
def cb(label): return tok('ckb', label)
def ck2(label): return tok('ck2', label)
