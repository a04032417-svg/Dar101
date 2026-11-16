"""HVAC and plumbing contractor suite part 4: label lists shared by data, tables, tools."""
import sys, os, re; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hv_core import *
from lib import L, LV


def P(labels):
    out, seen = [], set()
    for k, l in pairs(labels):
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


TECH6 = TECH_NAMES[:6]
PAYPAID = ['Owner draw', 'Salary', 'Hourly', 'Flat rate']
PAYSTATUS = ['Paid', 'Accruing']
LEAVE_TYPES = ['Annual leave', 'Sick leave', 'Training day', 'Unpaid leave']
CBASE = ['Sold', 'Collected']
PAY_MODELS = ['Hourly', 'Flat rate', 'Salary plus commission', 'Mixed']
SPIFF_ITEMS = ['Maintenance agreement sold', 'Thermostat added', 'Water filter added', 'Better option sold', 'Best option sold', 'Five-star review named']
HIRE_OPTS = ['Lead HVAC tech', 'HVAC technician', 'Service plumber', 'Apprentice']
WK26 = ['Week %d' % i for i in range(1, 27)]
PERIODS = ['Last 13 weeks', 'Last 4 weeks']
base_lists = [
    L('tech', 'Technician', P(TECH6)), L('crew', 'Field crew', P(TECH_NAMES)), L('payperson', 'Paid person', P([s['name'] for s in staff])), L('paypaid', 'Pay type', P(PAYPAID)),
    L('jobtype', 'Job type', P(JOB_TYPES)), L('jobstatus', 'Job status', P(JOB_STATUS)), L('cbreason', 'Callback reason', P(CALLBACK_REASONS)), L('estoutcome', 'Estimate outcome', P(EST_OUTCOME)),
    L('paystatus', 'Pay status', P(PAYSTATUS)), L('leavetype', 'Leave type', P(LEAVE_TYPES)), L('cbase', 'Commission base', P(CBASE)), L('paymodel', 'Pay model', P(PAY_MODELS)),
    L('spiffitem', 'Spiff item', P(SPIFF_ITEMS)), L('hireopt', 'Hire option', P(HIRE_OPTS)), L('wk26', 'Week', P(WK26)), L('season', 'Season', P(SEASONS)), L('period', 'Period', P(PERIODS)),
]
_M = {'tech': K(TECH6), 'crew': K(TECH_NAMES), 'payperson': K([s['name'] for s in staff]), 'paypaid': K(PAYPAID), 'jobtype': K(JOB_TYPES), 'jobstatus': K(JOB_STATUS),
      'cbreason': K(CALLBACK_REASONS), 'estoutcome': K(EST_OUTCOME), 'paystatus': K(PAYSTATUS), 'leavetype': K(LEAVE_TYPES), 'cbase': K(CBASE), 'paymodel': K(PAY_MODELS),
      'spiffitem': K(SPIFF_ITEMS), 'hireopt': K(HIRE_OPTS), 'wk26': K(WK26), 'season': K(SEASONS), 'period': K(PERIODS)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])

CKL, CKK = [], {}
def ck(label):
    if label not in CKK:
        k = re.sub(r'[^a-z0-9]+', '_', label.lower()).strip('_')[:21]
        while k in CKK.values(): k = k[:-1] + 'x'
        CKK[label] = k; CKL.append(label)
    return '{list:ck%d.%s}' % (CKL.index(label) // 30 + 1, CKK[label])
def ck_lists():
    out = []
    for i in range(0, len(CKL), 30):
        out.append(L('ck%d' % (i // 30 + 1), 'Check result %d' % (i // 30 + 1), [(CKK[l], l) for l in CKL[i:i + 30]]))
    return out
