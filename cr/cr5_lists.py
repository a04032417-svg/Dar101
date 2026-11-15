"""Car rental suite part 5 (Fleet Register, Service and Renewals): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cr_core import *
from lib import L, LV


def P(labels):
    """pairs() with list keys cut to 21 characters, unique inside the list, starting with a letter"""
    out, seen = [], set()
    for k, l in pairs(labels):
        if not k[:1].isalpha(): k = 'n' + k
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


MGROUPS = ['Service', 'Inspection', 'Tyres', 'Repair', 'Towing']
GROUP_OF = {'Minor service': 'Service', 'Major service': 'Service', 'Brake service': 'Service', 'Battery check': 'Service', 'Inspection': 'Inspection', 'Tyre set': 'Tyres',
            'Repair': 'Repair', 'Body repair': 'Repair', 'Towing': 'Towing'}
VENDORS = [VENDOR['Mechanic'], VENDOR['Tyre supplier'], VENDOR['Body repair shop'], VENDOR['Towing service']]
FLEET_AGE = ['0 to 12 months', '13 to 24 months', '25 to 36 months', '37 to 48 months', 'Over 48 months']
FLEET_EVENTS = ['Bought', 'Sold']
BOOK_NOW = ['Booked', 'Active']
MAHEAD = ['Month %d' % i for i in range(1, 13)]
SCENARIOS = ['Base', 'Best', 'Worst']
YEARS = sorted({str(v['year']) for v in vehicle_rows()})

# labels that formulas return (never typed text inside a formula)
CKA = ['Service now', 'Book soon', 'Current', 'Sold', 'Pull from booking', 'Book a slot', 'Overdue', 'Due in 30 days', 'Due in 60 days', 'Later', 'Done', 'Open renewal', 'Paid on time',
       'Paid late', 'Free slot', 'Best slot', 'Acceptable', 'Loses bookings', 'Busy day', 'Free day', 'Rising', 'Steady', 'Falling', 'Above class average', 'At or below class',
       'Tyres due', 'Tyres fine', 'Over the limit', 'Within the limit']
CKB = ['Register complete', 'Gaps to fill', 'Review this vehicle', 'Within the class range', 'Re-quote', 'Renew as is', 'Keep', 'Renegotiate', 'Try another workshop', 'Order tyre sets now',
       'No tyre order needed', 'Book the inspection', 'Move a booking', 'Repeat breakdowns, review', 'No repeat breakdowns', 'Serving early, costs extra', 'On time', 'Late',
       'Not enough services yet', 'Enough set aside', 'Set aside more', 'Add a workshop slot', 'Backlog clears in weeks', 'Peak in week', 'Book ahead']
CK2 = ['No overdue car is booked this week', 'Book the best slot', 'Book the free slot', 'Add candidate dates', 'Service in the low season', 'costs above its class by',
       'Downtime costs more than the repair', 'Repair costs more than the downtime', 'Nothing due in 30 days', 'Renewals need attention', 'Trend needs more months', 'Vehicle not found']
assert len(CKA) <= 30 and len(CKB) <= 30 and len(CK2) <= 30

lists = [
    L('class', 'Vehicle class', P(CLASSES)), L('fuel', 'Fuel', P(FUELS)), L('vstatus', 'Vehicle status', P(VEH_STATUS)), L('mkind', 'Service kind', P(MAINT_KINDS)),
    L('mgroup', 'Cost group', P(MGROUPS)), L('renewal', 'Renewal kind', P(RENEWAL_KINDS)), L('rstatus2', 'Renewal status', P(RENEWAL_STATUS)), L('vendor', 'Workshop vendor', P(VENDORS)),
    L('fleetage', 'Fleet age band', P(FLEET_AGE)), L('vyear', 'Model year', P(YEARS)), L('fevent', 'Fleet event', P(FLEET_EVENTS)), L('bstat2', 'Booking status', P(BOOK_NOW)),
    L('mahead', 'Month ahead', P(MAHEAD)), L('location', 'Location', P(LOCATIONS)), L('scen', 'Scenario', P(SCENARIOS)),
    L('cka', 'Check result A', P(CKA)), L('ckb', 'Check result B', P(CKB)), L('ck2', 'Verdict words', P(CK2)),
]
assert len(lists) <= 20
_M = {'class': K(CLASSES), 'fuel': K(FUELS), 'vstatus': K(VEH_STATUS), 'mkind': K(MAINT_KINDS), 'mgroup': K(MGROUPS), 'renewal': K(RENEWAL_KINDS), 'rstatus2': K(RENEWAL_STATUS),
      'vendor': K(VENDORS), 'fleetage': K(FLEET_AGE), 'vyear': K(YEARS), 'fevent': K(FLEET_EVENTS), 'bstat2': K(BOOK_NOW), 'mahead': K(MAHEAD), 'location': K(LOCATIONS), 'scen': K(SCENARIOS),
      'cka': K(CKA), 'ckb': K(CKB), 'ck2': K(CK2)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ca(label): return tok('cka', label)
def cb(label): return tok('ckb', label)
def c2(label): return tok('ck2', label)
