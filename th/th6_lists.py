"""Therapy practice suite part 6 (Clinical Admin, Supervision and Renewals): label lists shared by data, tables and tools."""
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


PAIDBY = ['Practice', 'Clinician']
REQKIND = ['Copy of records', 'Summary letter', 'Transfer of records', 'Correction request']
INCKIND = ['Complaint', 'Privacy incident', 'Room or equipment', 'Billing query', 'Staff concern', 'Near miss']
SCEN = ['Base', 'Best', 'Worst']
WEEKS = ['Week %d' % i for i in range(1, 14)]
# labels returned by formulas (a formula never types a word): table flags first, then tool verdicts
RESA = ['On time', 'Late', 'Overdue', 'Due soon', 'Done on time', 'Done late', 'Due in 30 days', 'On schedule', 'Improved', 'No change', 'Review the plan', 'No score yet',
        'Sent', 'Not sent', 'Within the rule', 'Over the rule', 'Up to date', 'Behind', 'On pace', 'Renewed', 'Red', 'Amber', 'OK', 'Review due', 'Current', 'Closed',
        'Archive now', 'Keep', 'Archived', 'Past keep-until date']
RESB = ['All done', 'Incomplete', 'Open', 'Book review', 'Recorded', 'Missing intake score', 'Not active', 'Within target', 'Below target', 'Clear today',
        'Catch up this week', 'Clear this week', 'Add admin time', 'Due this week', 'Clear in a month', 'Most clients improved', 'Review the caseload', 'Supervision up to date',
        'Book hours now', 'Within budget', 'Over budget', 'Set money aside', 'Covered', 'Book reviews', 'Send now', 'Waiting', 'Behind the pace', 'Short of target', 'Target reached', 'Clear the backlog']
for _x in (RESA, RESB): assert len(_x) <= 30 and len(set(_x)) == len(_x), len(_x)
assert not set(RESA) & set(RESB)

lists = [
    L('clin', 'Clinician', P(CLINICIANS)), L('svc', 'Service', P(SESSION_SERVICES)), L('cstatus', 'Client status', P(CLIENT_STATUS)), L('dreason', 'Discharge reason', P(DISCHARGE_REASONS)),
    L('refto', 'Referred to', P(REFERRED_TO)), L('opoint', 'Score point', P(OUTCOME_POINTS)), L('supk', 'Supervision kind', P(SUPERVISION_KINDS)), L('cek', 'Course kind', P(CE_KINDS)),
    L('renk', 'Renewal item', P(RENEWAL_KINDS_ALL)), L('holder', 'Holder', P(HOLDERS)), L('paidby', 'Paid by', P(PAIDBY)), L('reqkind', 'Request kind', P(REQKIND)),
    L('inckind', 'Incident kind', P(INCKIND)), L('wk', 'Week of the last 13', P(WEEKS)), L('scen', 'Scenario', P(SCEN)), L('csvc', 'Client service', P([x for x in SESSION_SERVICES if x not in ('Intake assessment', 'Review session')])), L('cka', 'Check result A', P(RESA)), L('ckb', 'Check result B', P(RESB))]
assert len(lists) <= 20
_M = {l['key']: {v['label']: v['key'] for v in l['values']} for l in lists}
_V = {}
for _l in ('cka', 'ckb'):
    for _lab in _M[_l]: _V[_lab] = (_l, _M[_l][_lab])
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ck(label):
    """list token for a result label (flag or verdict)"""
    l, k = _V[label]
    return LV(l, k)
def ckey(label): return _V[label][1]
vd = ck
