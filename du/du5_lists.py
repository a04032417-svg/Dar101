"""Doula business suite part 5 (Visits, Hours, Mileage and Births): label lists shared by data, tables, tools."""
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


ATTENDERS = DOULA_NAMES + BACKUP_NAMES
HPACK = ['Postpartum 40 Hours', 'Postpartum 80 Hours', 'Postpartum 120 Hours', 'Night Support 60 Hours', 'Combined Essential', 'Combined Plus', 'Complete Care Bundle']
BPACK = ['Birth Essential', 'Birth Plus', 'Birth Premier', 'Combined Essential', 'Combined Plus', 'Complete Care Bundle']
HBAND = ['Up to 8 hours', '8 to 12 hours', '12 to 16 hours', '16 to 20 hours', '20 to 24 hours', 'Over 24 hours']
CBAND = ['00:00 to 03:59', '04:00 to 07:59', '08:00 to 11:59', '12:00 to 15:59', '16:00 to 19:59', '20:00 to 23:59']
WKNO = ['Week %d' % i for i in range(1, 27)]
SCEN = ['Base', 'Best', 'Worst']
# labels that table formulas and tool verdicts return (a formula never types a word: it points at the list cell)
CKA = ['Within plan', 'Over plan', 'No hours logged', 'Used in full', 'Ending in 30 days', 'Ending in 60 days', 'Active', 'Expired with hours left', 'Expired and used', 'Over the pack',
       'Within cap', 'Over cap', 'Over cap in a row', 'Enough rest', 'Too little rest', 'High mileage share', 'Normal mileage share']
CK2 = ['Review clients over plan', 'Hours are within plan', 'Client is over plan', 'Client is within plan', 'Invoice the extra hours', 'Use hours before expiry', 'Ledger is clear',
       'Reduce next week', 'Rest week needed', 'Within the cap', 'Add a travel fee', 'Mileage share is fine', 'Quarter is over the maximum', 'Quarter is near the maximum',
       'Quarter is within the maximum', 'Give rest days', 'Enough rest', 'Postpartum share grows', 'Night share grows', 'Prenatal share grows', 'Debrief share grows', 'Mix is steady',
       'Book visits now', 'Let hours lapse', 'No pack ends soon']
CK3 = ['On pace', 'Behind pace', 'Pack finished', 'Invoice now', 'Nothing to invoice', 'Set a minimum', 'Visit length is fine', 'Cluster Northgate visits', 'Cluster Southbank visits',
       'Visits already clustered', 'Plan more birth hours', 'Plan holds', 'Keep arrival under the limit', 'Arrival time is fine', 'Rotate night work', 'Night work is fine',
       'Book the visit now', 'Visit is on time', 'Visit is overdue', 'Prenatal visits are done', 'Over capacity', 'Near capacity', 'Room for more']
assert len(CKA) <= 30 and len(CK2) <= 30 and len(CK3) <= 30

lists = [
    L('role', 'Role', P(ROLES)), L('service', 'Service', P(SERVICES)), L('area', 'Area', P(AREAS)), L('pkind', 'Package kind', P(PACKAGE_KINDS)), L('ckind', 'Client kind', P(CLIENT_KINDS)),
    L('cstatus', 'Client status', P(CLIENT_STATUS)), L('vkind', 'Visit kind', P(VISIT_KINDS)), L('doula', 'Doula', P(DOULA_NAMES)), L('attender', 'Doula who attended', P(ATTENDERS)),
    L('hpack', 'Hour pack package', P(HPACK)), L('bpack', 'Birth package', P(BPACK)), L('hband', 'Birth hours band', P(HBAND)), L('cband', 'Call time band', P(CBAND)),
    L('wday', 'Weekday', P(WEEKDAYS)), L('scen', 'Scenario', P(SCEN)), L('wkno', 'Week number', P(WKNO)),
    L('cka', 'Check result', P(CKA)), L('ck2', 'Verdict A', P(CK2)), L('ck3', 'Verdict B', P(CK3)),
]
assert len(lists) <= 20
_M = {'role': K(ROLES), 'service': K(SERVICES), 'area': K(AREAS), 'pkind': K(PACKAGE_KINDS), 'ckind': K(CLIENT_KINDS), 'cstatus': K(CLIENT_STATUS), 'vkind': K(VISIT_KINDS), 'doula': K(DOULA_NAMES),
      'attender': K(ATTENDERS), 'hpack': K(HPACK), 'bpack': K(BPACK), 'hband': K(HBAND), 'cband': K(CBAND), 'wday': K(WEEKDAYS), 'scen': K(SCEN), 'wkno': K(WKNO), 'cka': K(CKA), 'ck2': K(CK2), 'ck3': K(CK3)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def ca(label): return tok('cka', label)
def c2(label): return tok('ck2', label)
def c3(label): return tok('ck3', label)
