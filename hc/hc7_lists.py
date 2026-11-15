"""Home care agency suite part 7 (Client Margin and Hours Growth): label lists."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hc_core import *
from lib import L, LV


def P(labels):
    out, seen = [], set()
    for k, l in pairs(labels):
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


RISK = ['Low', 'Medium', 'High']
OUTCOME = ['Accepted', 'Negotiated', 'Hours cut', 'Left']
SCEN = ['Base', 'Best', 'Worst']
STEPS = ['Plus 0.25', 'Plus 0.50', 'Plus 0.75', 'Plus 1.00', 'Plus 1.25', 'Plus 1.50', 'Plus 1.75', 'Plus 2.00', 'Plus 2.50', 'Plus 3.00', 'Plus 3.50', 'Plus 4.00']
STEP_VALUES = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0]
CHK = ['On target', 'Below target', 'Below 30 percent', 'Negative margin', 'Fine', 'Loss on short visits', 'Raise', 'Raise less', 'Hold', 'Worth it', 'Not yet',
       'Rate locked', 'Notice sent', 'Notice due', 'Not due yet']
VERD = ['Keep', 'Raise the rate', 'Release', 'Rate is enough', 'Raise', 'Raise less', 'Hold', 'Raise the minimum', 'Add a travel charge', 'Fine', 'Change the minimum',
        'Keep the minimum', 'Worth it', 'Not yet', 'Hours growing', 'Hours flat', 'Hours shrinking', 'Under the limit', 'Above the limit', 'Hours grow', 'Hours hold',
        'Hours shrink', 'Worth winning', 'Too costly', 'Act first', 'All on target', 'Raise now', 'Nothing to raise', 'On target', 'Below target']
assert len(CHK) <= 30 and len(VERD) <= 30

lists = [L('svc', 'Service', P(SERVICES)), L('band', 'Time band', P(BANDS)), L('area', 'Area', P(AREAS)), L('payer', 'Payer', P(PAYERS)), L('emp', 'Employment', P(EMPLOYMENT)),
         L('clstatus', 'Client status', P(CLIENT_STATUS)), L('endrsn', 'End reason', P(END_REASONS)), L('enqsrc', 'Source', P(ENQ_SOURCES)), L('role', 'Role', P(ROLES)),
         L('team', 'Team', P(TEAMS)), L('paytype', 'Pay type', P(PAY_TYPES)), L('cgstatus', 'Caregiver status', P(CAREGIVER_STATUS)), L('risk', 'Risk of leaving', P(RISK)),
         L('outcome', 'Rise outcome', P(OUTCOME)), L('scen', 'Scenario', P(SCEN)), L('step', 'Pay step', P(STEPS)), L('chk', 'Check result', P(CHK)), L('verd', 'Decision', P(VERD))]
assert len(lists) <= 20
_M = {'svc': K(SERVICES), 'band': K(BANDS), 'area': K(AREAS), 'payer': K(PAYERS), 'emp': K(EMPLOYMENT), 'clstatus': K(CLIENT_STATUS), 'endrsn': K(END_REASONS), 'enqsrc': K(ENQ_SOURCES),
      'role': K(ROLES), 'team': K(TEAMS), 'paytype': K(PAY_TYPES), 'cgstatus': K(CAREGIVER_STATUS), 'risk': K(RISK), 'outcome': K(OUTCOME), 'scen': K(SCEN), 'step': K(STEPS),
      'chk': K(CHK), 'verd': K(VERD)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ck(label): return tok('chk', label)
def vd(label): return tok('verd', label)
