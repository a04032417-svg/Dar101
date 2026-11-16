"""Doula Business suite part 1 (Enquiries, Consultations and Quotes): label lists shared by data, tables, tools."""
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


PACKAGE_NAMES = [p['package'] for p in packages if p['kind'] != 'Add-on']
QSTATUS = ['Open', 'Signed', 'Lapsed']
RBAND = ['Up to 4 hours', '5 to 24 hours', '25 to 48 hours', 'Over 48 hours', 'No reply yet']
NEXTSTEP = ['Call today', 'Write today', 'Remind about the consultation', 'Send the quote', 'Chase the quote', 'Close the enquiry', 'Welcome the new client', 'Offer another time', 'Not due yet']
SCEN = ['Base', 'Best', 'Worst']
# labels that table formulas and tools return (a formula never types a word: it points at the list cell)
CKA = ['Reply in time', 'Slow reply', 'No reply yet', 'Consultation coming up', 'Outcome missing', 'Follow-up overdue', 'Follow up today', 'Follow-up planned', 'Outcome recorded',
       'Slots free', 'Fully booked', 'Ends within 7 days', 'Quote valid', 'Quote lapsed', 'Quote closed']
CK2 = ['Above target, send the quote', 'Raise the price or cut hours', 'Reply faster', 'Reply time on target', 'Funnel on track', 'Fix consultation booking', 'Fix consultation attendance',
       'Fix signing after consultation', 'Strong source', 'Average source', 'Weak source', 'Fix price first', 'Fix date capacity first', 'Fix backup cover first', 'Fix the pitch first',
       'Fix reply time first', 'Declined share above setting', 'Declined share within setting', 'Worth it', 'Not worth it', 'Overbook one slot', 'No-show rate is fine',
       'Keep your usual length', 'Allow longer consultations', 'Waitlist these dates', 'Open more dates', 'Enough for now']
CK3 = ['Keep the discounts', 'Cap the discounts', 'Pipeline on pace', 'Quiet month ahead', 'Chase now', 'Close lapsed quotes', 'No quote ending soon', 'Wins at consultation',
       'Keep in the lineup', 'Rework or drop', 'Promote postpartum', 'Hold the mix', 'Add a travel fee', 'Hold the travel fee', 'Offer a plan', 'A plan is not needed',
       'Cover this weekday', 'Reply cover is fine']
assert len(CKA) <= 30 and len(CK2) <= 30 and len(CK3) <= 30

lists = [
    L('role', 'Role', P(ROLES)), L('service', 'Service wanted', P(SERVICES)), L('area', 'Service area', P(AREAS)), L('source', 'Enquiry source', P(SOURCES)),
    L('estatus', 'Enquiry status', P(ENQUIRY_STATUS)), L('lostreason', 'Lost reason', P(LOST_REASONS)), L('outcome', 'Consultation outcome', P(CONSULT_OUTCOMES)),
    L('discount', 'Discount', P(DISCOUNTS)), L('ckind', 'Client kind', P(CLIENT_KINDS)), L('cstatus', 'Client status', P(CLIENT_STATUS)), L('package', 'Package', P(PACKAGE_NAMES)),
    L('doula', 'Doula', P(DOULA_NAMES)), L('wday', 'Weekday', P(WEEKDAYS)), L('qstatus', 'Quote status', P(QSTATUS)), L('rband', 'Reply time band', P(RBAND)),
    L('nextstep', 'Next step', P(NEXTSTEP)), L('scen', 'Scenario', P(SCEN)),
    L('cka', 'Check result', P(CKA)), L('ck2', 'Verdict A', P(CK2)), L('ck3', 'Verdict B', P(CK3)),
]
assert len(lists) <= 20
_M = {'role': K(ROLES), 'service': K(SERVICES), 'area': K(AREAS), 'source': K(SOURCES), 'estatus': K(ENQUIRY_STATUS), 'lostreason': K(LOST_REASONS), 'outcome': K(CONSULT_OUTCOMES),
      'discount': K(DISCOUNTS), 'ckind': K(CLIENT_KINDS), 'cstatus': K(CLIENT_STATUS), 'package': K(PACKAGE_NAMES), 'doula': K(DOULA_NAMES), 'wday': K(WEEKDAYS), 'qstatus': K(QSTATUS),
      'rband': K(RBAND), 'nextstep': K(NEXTSTEP), 'scen': K(SCEN), 'cka': K(CKA), 'ck2': K(CK2), 'ck3': K(CK3)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def ca(label): return tok('cka', label)
def c2(label): return tok('ck2', label)
def c3(label): return tok('ck3', label)
def ns(label): return tok('nextstep', label)
