"""Therapy private practice suite part 5 (Clinician Pay and Productivity): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from th_core import *
from lib import L, LV


def P(labels):
    out, seen = [], set()
    for k, l in pairs(labels):
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


ROLE2 = {'Owner clinician': 'Owner clinician', 'Clinician': 'Employed clinician', 'Contract clinician': 'Contract (self-employed) clinician',
         'Associate': 'Associate (works under supervision)'}
ROLES2 = ['Owner clinician', 'Employed clinician', 'Contract (self-employed) clinician', 'Associate (works under supervision)', 'Practice coordinator', 'Accountant',
          'Clinical supervisor', 'IT support', 'Landlord', 'Cleaner']
ATASKS = ['Session notes', 'Client e-mails and calls', 'Plan reviews', 'Referral letters', 'Team meeting', 'Scheduling and billing queries', 'Supervision preparation', 'Reading and training']
PFIND = ['Booked share of cap in strain', 'Booked share of cap idle', 'Late cancels above target', 'Retention below target', 'Admin time heavy', 'Rebooking below target',
         'Revenue per hour below target', 'Notes overdue', 'On track']
PCHG = ['Yearly review', 'Larger caseload', 'Cost of living', 'New contract terms', 'Associate review']
CPAY = ['Owner draw', 'Salary', 'Percentage split', 'Per session']
SCEN = ['Base', 'Best', 'Worst']
# labels returned by formulas (a formula never types a word)
CKA = ['Idle', 'Below healthy', 'Healthy', 'Above healthy', 'Strain', 'On target', 'Below target', 'Above target', 'Matches statement', 'Does not match', 'Open', 'Done', 'Overdue',
       'Planned', 'In force', 'No clash', 'Clash with another clinician', 'Within the target', 'Watch', 'Over', 'Margin on target', 'Retained to 6', 'Stopped early',
       'After intake only', 'After more sessions', 'Review now', 'Fine', 'Rebooked', 'Not rebooked']
CKB = ['Split affordable', 'Above the pay share target', 'Accept', 'Counter-offer', 'Pay', 'Query the invoice', 'Net margin on target', 'Supervision erodes the margin', 'Salary is cheaper',
       'Split is cheaper', 'Above break-even', 'Below break-even', 'Improving', 'Falling', 'Realistic', 'Above the cap', 'Leave fits', 'Move sessions first', 'Admin heavy', 'Balanced',
       'Affordable', 'Pushes margin below target']
for _x in (CKA, CKB): assert len(_x) <= 30 and len(set(_x)) == len(_x), len(_x)

lists = [
    L('role', 'Role', P(ROLES2)), L('team', 'Team', P(TEAMS)), L('paytype', 'Pay type', P(PAY_TYPES)), L('paykind', 'Pay kind', P(PAY_KINDS)), L('clin', 'Clinician', P(CLINICIANS)),
    L('staff', 'Paid staff', P(PAID_STAFF)), L('svc', 'Service', P(SESSION_SERVICES)), L('sstatus', 'Session status', P(SESSION_STATUS)), L('wday', 'Weekday', P(WORKDAYS)),
    L('cstatus', 'Client status', P(CLIENT_STATUS)), L('dreason', 'Discharge reason', P(DISCHARGE_REASONS)), L('payst', 'Pay status', P(PAY_STATUS)), L('atask', 'Admin task', P(ATASKS)),
    L('pfind', 'Review finding', P(PFIND)), L('pchg', 'Pay change reason', P(PCHG)), L('cpay', 'Clinician pay type', P(CPAY)), L('scen', 'Scenario', P(SCEN)),
    L('csvc', 'Client service', P([x for x in SESSION_SERVICES if x not in ('Intake assessment', 'Review session')])), L('cka', 'Check result A', P(CKA)), L('ckb', 'Check result B', P(CKB)),
]
assert len(lists) <= 20
_M = {l['key']: {v['label']: v['key'] for v in l['values']} for l in lists}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
_V = {}
for _l in ('cka', 'ckb'):
    for _lab in _M[_l]: _V[_lab] = (_l, _M[_l][_lab])
def V(label):
    """token of a verdict or flag label (found in the check lists)"""
    l, k = _V[label]; return LV(l, k)


def BAND(sh):
    """utilization band label of a share-of-cap expression, from the editable bands in Start"""
    return 'IF(%s>{set:util_strain_above},%s,IF(%s>{set:target_utilisation},%s,IF(%s>={set:util_healthy_from},%s,IF(%s>={set:util_idle_below},%s,%s))))' % (
        sh, V('Strain'), sh, V('Above healthy'), sh, V('Healthy'), sh, V('Below healthy'), V('Idle'))
