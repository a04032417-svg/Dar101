"""Short-term rental host suite part 4: label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sr_core import *
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


WDAY = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
PAYST = ['Paid', 'Accruing', 'Due']
SUPPLIERS = ['Wholesale club', 'Cleaning supplier', 'Linen wholesaler', 'Hardware store', 'Home store']
PAIDBY = ['Business card', 'Bank transfer']
RREASON = ['Dust or hair left', 'Bathroom not clean', 'Bed linen missed', 'Kitchen not clean', 'Marks or smell', 'Supplies not restocked']
DREASON = ['Long stay ended', 'Season start', 'After repair work', 'Quarterly clean', 'Guest complaint']
ORDST = ['Ordered', 'Delivered', 'Short delivery', 'Late']
LLOC = ['Own machines', 'Laundry service', 'Linen hire']
FREQ = ['Every turnover', 'Weekly', 'Monthly', 'Quarterly']
LFST = ['Found', 'Contacted', 'Returned', 'Disposed']
# labels that formulas return (never typed text inside a formula)
CKA = ['Tight turn', 'Time to spare', 'Cleaner set', 'No cleaner', 'Over weekly hours', 'Within weekly hours', 'Not a cleaner', 'Pass', 'Fail', 'Fee covers cost', 'Fee too low',
       'Below reorder point', 'Reorder soon', 'Stock is fine', 'Overbooked', 'Full day', 'Spare hours', 'Too tight', 'Tight but possible', 'Comfortable']
CKB = ['Loss is high', 'Loss is normal', 'Delivery overdue', 'On the way', 'Received', 'Open for days', 'Open', 'Closed', 'Follow up needed', 'No follow-up', 'Above target', 'On target']
CK2 = ['Overbooked', 'Within the limit', 'Slack', 'Late start', 'Fee covers cost', 'Raise the fee', 'Fee is fair', 'Order now', 'Stock is fine', 'Own machines are cheapest',
       'Laundry service is cheapest', 'Linen hire is cheapest', 'Add a cleaner', 'Cleaners cover it', 'Redo costs more than the fee', 'Redo is small', 'Over budget', 'Within budget']
assert len(CKA) <= 30 and len(CKB) <= 30 and len(CK2) <= 30

lists = [
    L('role', 'Role', P(ROLES)), L('team', 'Team', P(TEAMS)), L('yn', 'Yes or no', P(YESNO)), L('utype', 'Unit type', P(UNIT_TYPES)), L('city', 'City', P(CITIES)),
    L('bstatus', 'Booking status', P(BOOKING_STATUS)), L('turnst', 'Turnover status', P(TURN_STATUS)), L('scat', 'Supply category', P(SUPPLY_CATEGORIES)), L('wday', 'Weekday', P(WDAY)),
    L('paystat', 'Pay status', P(PAYST)), L('supplier', 'Supplier', P(SUPPLIERS)), L('paidby', 'Paid by', P(PAIDBY)), L('rreason', 'Redo reason', P(RREASON)), L('dreason', 'Deep clean reason', P(DREASON)),
    L('ordst', 'Order status', P(ORDST)), L('lloc', 'Laundry route', P(LLOC)), L('freq', 'Task frequency', P(FREQ)), L('lfst', 'Lost item status', P(LFST)),
    L('cka', 'Check result A', P(CKA)), L('ckb', 'Check result B', P(CKB)), L('ck2', 'Calculator verdict', P(CK2)),
]
_M = {'role': K(ROLES), 'team': K(TEAMS), 'yn': K(YESNO), 'utype': K(UNIT_TYPES), 'city': K(CITIES), 'bstatus': K(BOOKING_STATUS), 'turnst': K(TURN_STATUS), 'scat': K(SUPPLY_CATEGORIES), 'wday': K(WDAY),
      'paystat': K(PAYST), 'supplier': K(SUPPLIERS), 'paidby': K(PAIDBY), 'rreason': K(RREASON), 'dreason': K(DREASON), 'ordst': K(ORDST), 'lloc': K(LLOC), 'freq': K(FREQ), 'lfst': K(LFST),
      'cka': K(CKA), 'ckb': K(CKB), 'ck2': K(CK2)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def ca(label): return tok('cka', label)
def cb(label): return tok('ckb', label)
def ck2(label): return tok('ck2', label)
