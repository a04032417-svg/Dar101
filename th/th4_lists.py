"""Therapy practice suite part 4: label lists."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from th_core import *
from lib import L, LV


def P(labels):
    out, seen = [], set()
    for k, l in pairs(labels):
        k = k[:21]
        if not k[:1].isalpha(): k = 'x' + k[:20]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


FMETHOD = ['Phone', 'Email', 'Online portal']
FANSWER = ['Paid soon', 'Being processed', 'Needs more details', 'No answer']
WREASON = ['Denied, not fixable', 'Not resubmitted in time', 'Duplicate claim', 'Payer would not pay', 'Small balance']
SCEN = ['Base', 'Best', 'Worst']
LCRULE = ['Half the fee after 24 hours', 'Full fee after 24 hours', 'First late cancel waived']
PKOPT = ['No package', '6 sessions', '10 sessions']
CHK = ['Accepted first time', 'Not accepted first time', 'Chase now', 'Chased this week', 'Fix and resubmit', 'Within usual time', 'Closed', 'Claimed', 'Not claimed yet', 'Not claimable',
       'Late, over the rule', 'Within the rule', 'Ready to submit', 'Fix first', 'Valid', 'Ending soon', 'Ended', 'Fixed and resent', 'Fix now', 'Past resubmit window', 'Written off',
       'Checked before first session', 'Checked after first session', 'Matched', 'Investigate', 'Can bill', 'Waiting for payer', 'Renew soon', 'Active payer client', 'Not active']
VERD = ['Covered', 'Get pre-approval first', 'Offer the self-pay fee', 'Package saves money', 'Pay per session', 'Submit', 'Fix first', 'Submit now, it is late', 'Chase first', 'Wait',
        'Within the limit', 'Slow payer', 'Old tail growing', 'On target', 'Below target', 'Fix now', 'Too late, write off', 'Resubmit all', 'Skip the small ones', 'Query the payer',
        'Accept', 'Chase', 'Escalate', 'Write off', 'Matched', 'Investigate']
VERD2 = ['Renew now', 'Approval OK', 'Grow', 'Hold', 'Renegotiate', 'Bill the payer', 'Self-pay', 'Apply now', 'On track', 'Covers the pay run', 'Short of the pay run', 'Ready to issue',
         'Details missing', 'Acceptable', 'Act on denials']
assert len(CHK) <= 30 and len(VERD) <= 30 and len(VERD2) <= 30
lists = [L('payer', 'Payer', P(PAYERS)), L('svc', 'Service', P(SESSION_SERVICES)), L('clin', 'Clinician', P(CLINICIANS)), L('clmst', 'Claim status', P(CLAIM_STATUS)),
         L('denial', 'Denial reason', P(DENIAL_REASONS)), L('ageband', 'Age band, days', P(AGE_BANDS)), L('benres', 'Benefits check result', P(BENEFIT_RESULTS)),
         L('enrolst', 'Enrolment status', P(ENROLMENT_STATUS)), L('sstatus', 'Session status', P(SESSION_STATUS)), L('cstatus', 'Client status', P(CLIENT_STATUS)),
         L('fmethod', 'Follow-up method', P(FMETHOD)), L('fanswer', 'Payer answer', P(FANSWER)), L('wreason', 'Write-off reason', P(WREASON)), L('scen', 'Scenario', P(SCEN)),
         L('lcrule', 'Late-cancel rule', P(LCRULE)), L('pkopt', 'Package option', P(PKOPT)), L('chk', 'Check result', P(CHK)), L('verd', 'Decision', P(VERD)), L('verd2', 'Decision 2', P(VERD2))]
assert len(lists) <= 20
_M = {'payer': K(PAYERS), 'svc': K(SESSION_SERVICES), 'clin': K(CLINICIANS), 'clmst': K(CLAIM_STATUS), 'denial': K(DENIAL_REASONS), 'ageband': K(AGE_BANDS), 'benres': K(BENEFIT_RESULTS),
      'enrolst': K(ENROLMENT_STATUS), 'sstatus': K(SESSION_STATUS), 'cstatus': K(CLIENT_STATUS), 'fmethod': K(FMETHOD), 'fanswer': K(FANSWER), 'wreason': K(WREASON), 'scen': K(SCEN),
      'lcrule': K(LCRULE), 'pkopt': K(PKOPT), 'chk': K(CHK), 'verd': K(VERD), 'verd2': K(VERD2)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ck(label): return tok('chk', label)
def vd(label): return tok('verd', label)
def v2(label): return tok('verd2', label)
