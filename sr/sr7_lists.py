"""Short-term rental host suite part 7: label lists shared by data, tables, tools."""
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


REQ = ['Replace an item', 'Deep clean', 'Repair approval', 'New linen', 'Photo refresh', 'Owner visit', 'Price review', 'Copy of a report']
DUTY = ['Guest messages', 'Check-in help', 'Key handover', 'Review replies', 'Calendar check', 'Listing update', 'Issue follow-up', 'Owner update']
ADJ = ['Cancelled stay refund', 'Late booking added', 'Rate applied in error', 'Long stay exemption', 'Platform report timing', 'Owner stay not taxed', 'Rounding difference']
LKIND = ['Revenue', 'Platform fees', 'Cleaning', 'Supplies', 'Maintenance', 'Utilities', 'Management fee']
PMETH = ['Bank transfer', 'Standing order', 'Card payout']
PSTAT = ['Paid', 'Scheduled', 'Delayed']
PKG = ['Basic', 'Standard', 'Full']
OKIND = ['Own portfolio', 'Managed for owner', 'Company account']
COLL = ['Host', 'Platform']
# labels that formulas return (never typed text inside a formula)
CKA = ['Sent on time', 'Sent late', 'Not sent yet', 'Paid on time', 'Paid late', 'Payment due', 'Payment overdue', 'Draft statement', 'Margin fine', 'Margin below the floor', 'Net is negative',
       'Statement adds up', 'Statement does not add up', 'Fee matches the rate', 'Fee differs from the rate', 'Fee per message normal', 'Fee per message high', 'Tax matches', 'Difference to explain',
       'Filed on time', 'Filed late', 'Due soon', 'Overdue', 'Not yet due', 'Scheduled', 'Delayed', 'Pay rate on target', 'Pay rate off target', 'Reserve fine', 'Reserve low']
CKB = ['Request open', 'Request done', 'Ends within 90 days', 'Running', 'Term ended', 'Upcoming stay', 'Past stay', 'Duty done', 'Duty planned', 'Duty overdue', 'Filed', 'Not yet filed',
       'Adds to the return', 'Reduces the return', 'Charged to owner', 'Paid by the host', 'Own unit', 'Managed unit', 'Notice date passed', 'Notice date ahead', 'Fully remitted', 'Still to remit']
CK2 = ['Net is positive', 'Net is negative', 'Margin above the floor', 'Margin below the floor', 'Fee on the net', 'Fee on the gross', 'Minimum fee applies', 'Fee above the tier', 'Fee on the tier',
       'Reserve is enough', 'Top up the reserve', 'Difference to explain', 'Tax matches', 'Owner pays for the stay', 'Return is above target', 'Return is below target', 'Costs rose', 'Costs fell',
       'Net rose', 'Net fell', 'Host fee rose', 'Cash covers the payments', 'Cash is short', 'Charge below cost', 'Fee per message is high', 'Fee per message is fine', 'Tax already paid by the platform']
assert len(CKA) <= 30 and len(CKB) <= 30 and len(CK2) <= 30

lists = [
    L('role', 'Role', P(ROLES)), L('team', 'Team', P(TEAMS)), L('yn', 'Yes or no', P(YESNO)), L('city', 'City', P(CITIES)), L('bstatus', 'Booking status', P(BOOKING_STATUS)),
    L('stmst', 'Statement status', P(STATEMENT_STATUS)), L('taxst', 'Tax return status', P(TAX_STATUS)), L('ecat', 'Expense category', P(EXPENSE_CATEGORIES)), L('okind', 'Owner kind', P(OKIND)),
    L('pmeth', 'Payment method', P(PMETH)), L('pstat', 'Payment status', P(PSTAT)), L('req', 'Owner request', P(REQ)), L('duty', 'Co-host duty', P(DUTY)), L('adj', 'Tax adjustment reason', P(ADJ)),
    L('lkind', 'Statement line kind', P(LKIND)), L('pkg', 'Service package', P(PKG)), L('coll', 'Tax collected by', P(COLL)),
    L('cka', 'Check result A', P(CKA)), L('ckb', 'Check result B', P(CKB)), L('ck2', 'Calculator verdict', P(CK2)),
]
assert len(lists) == 20
_M = {'role': K(ROLES), 'team': K(TEAMS), 'yn': K(YESNO), 'city': K(CITIES), 'bstatus': K(BOOKING_STATUS), 'stmst': K(STATEMENT_STATUS), 'taxst': K(TAX_STATUS), 'ecat': K(EXPENSE_CATEGORIES),
      'okind': K(OKIND), 'pmeth': K(PMETH), 'pstat': K(PSTAT), 'req': K(REQ), 'duty': K(DUTY), 'adj': K(ADJ), 'lkind': K(LKIND), 'pkg': K(PKG), 'coll': K(COLL), 'cka': K(CKA), 'ckb': K(CKB), 'ck2': K(CK2)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ca(label): return tok('cka', label)
def cb(label): return tok('ckb', label)
def ck2(label): return tok('ck2', label)
