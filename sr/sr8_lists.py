"""Short-term rental host suite part 8: label lists shared by data, tables, tools."""
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


DREASON = ['Monthly draw', 'Extra draw after peak season', 'Reduced draw, cash tight', 'Holiday top-up', 'Draw for a personal cost']
LKIND = ['Unit lease', 'Furniture loan', 'Equipment loan', 'Bank loan', 'Deposit loan']
SCEN = ['Add one more unit', 'Add two more units', 'Raise rates 5 percent', 'Raise rates 8 percent', 'Lift occupancy 5 points', 'Lift occupancy 10 points', 'More direct bookings',
        'Drop the losing unit', 'Cut platform fees', 'Cut cleaning cost', 'Rate rise and one new unit', 'Fewer units, higher rates']
# labels that formulas return (never typed text inside a formula)
CKF = ['Profit on target', 'Margin too thin', 'Loss', 'Above break-even', 'Below break-even', 'Cannot break even', 'Payout on time', 'Payout late', 'Payout short', 'Payout missing',
       'Payout expected', 'Below the floor', 'Near the floor', 'Above the floor', 'Lease ends soon', 'Lease running', 'Lease ended', 'Fully funded', 'Underfunded', 'Pays back fast',
       'Pays back slowly', 'Does not pay back', 'Draw within safe limit', 'Draw above safe limit', 'Tax overdue', 'Tax due soon', 'Tax paid', 'Tax later', 'Cost rose', 'Cost steady']
CKG = ['Statement paid', 'Statement sent', 'Statement overdue', 'Statement draft', 'Fee on agreed share', 'Fee differs from share', 'Pay in line with rate', 'Pay above rate', 'Pay below rate',
       'High cost per turnover', 'Normal cost per turnover', 'Big purchase', 'Normal purchase', 'Scenario adds profit', 'Scenario loses profit', 'Scenario small gain', 'Draw taken',
       'Draw planned', 'Repair above 300', 'Repair under 300', 'Cash is safe', 'Cash is tight', 'Cost per night fell', 'Cost per night rose', 'Still to be paid', 'Filed and paid',
       'Collected, not yet remitted', 'Remit soon', 'Remit overdue', 'Nothing to remit']
CK2 = ['Keep the unit', 'Fix the rate first', 'Drop the unit', 'Review the unit', 'Raise the rate', 'Hold the rate', 'Rate rise adds profit', 'Rate rise loses profit', 'Cash is safe',
       'Cash is tight', 'Cash is below the floor', 'Safe to draw', 'Draw less', 'No draw this month', 'Add the unit', 'Do not add the unit', 'Direct saves money', 'Direct saves little',
       'Tax is funded', 'Set aside more', 'Cash covers the gap', 'Gap needs cash', 'No gap', 'Profit', 'Loss', 'Pays back in time', 'Pays back too slowly']
assert len(CKF) <= 30 and len(CKG) <= 30 and len(CK2) <= 30

lists = [
    L('role', 'Role', P(ROLES)), L('team', 'Team', P(TEAMS)), L('yn', 'Yes or no', P(YESNO)), L('utype', 'Unit type', P(UNIT_TYPES)), L('city', 'City', P(CITIES)), L('chan', 'Booking channel', P(CHANNELS)),
    L('bstatus', 'Booking status', P(BOOKING_STATUS)), L('payst', 'Payout status', P(PAYOUT_STATUS)), L('ecat', 'Expense category', P(EXPENSE_CATEGORIES)), L('scat', 'Supply category', P(SUPPLY_CATEGORIES)),
    L('stmst', 'Statement status', P(STATEMENT_STATUS)), L('taxst', 'Tax status', P(TAX_STATUS)), L('dreason', 'Draw reason', P(DREASON)), L('lkind', 'Loan kind', P(LKIND)), L('scn', 'Scenario', P(SCEN)),
    L('ckf', 'Check result A', P(CKF)), L('ckg', 'Check result B', P(CKG)), L('ck2', 'Calculator verdict', P(CK2)),
]
_M = {'role': K(ROLES), 'team': K(TEAMS), 'yn': K(YESNO), 'utype': K(UNIT_TYPES), 'city': K(CITIES), 'chan': K(CHANNELS), 'bstatus': K(BOOKING_STATUS), 'payst': K(PAYOUT_STATUS), 'ecat': K(EXPENSE_CATEGORIES),
      'scat': K(SUPPLY_CATEGORIES), 'stmst': K(STATEMENT_STATUS), 'taxst': K(TAX_STATUS), 'dreason': K(DREASON), 'lkind': K(LKIND), 'scn': K(SCEN), 'ckf': K(CKF), 'ckg': K(CKG), 'ck2': K(CK2)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def cf(label): return tok('ckf', label)
def cg(label): return tok('ckg', label)
def ck2(label): return tok('ck2', label)
