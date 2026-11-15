"""Home care agency suite part 6: label lists (Recruiting, Onboarding and Renewals)."""
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


SCEN = ['Base', 'Best', 'Worst']
COURSES = ['Onboarding training', 'Core skills refresher', 'First aid course', 'Communication skills', 'Safe driving', 'Record keeping basics']
KINDS = ['Phone screen', 'Interview']
OUTCOME = ['Pass', 'Hold', 'Not selected', 'Accepted', 'Declined', 'No reply', 'Waiting']
STEPS = ['Identity check', 'References', 'Background check', 'Training', 'Agreement signed', 'First shift']
CREDST = ['Valid', 'Renewed']
CHK = ['Call overdue', 'Called', 'Within 3 days', 'Closed', 'Ready', 'Blocked', 'Overdue', 'Done', 'Open', 'Expired',
       'Red zone', 'Amber zone', 'Green', 'Due now', 'Not due yet', 'Paid', 'No hire yet', 'Left early', 'Within target', 'Over target',
       'Booked', 'Not booked', 'Applied only', 'Screened', 'Interviewed', 'Offered', 'Started', 'First 90 days', 'From 4 to 12 months', 'Over 1 year']
VERD = ['Weakest: phone screen', 'Weakest: interview', 'Weakest: offer', 'Weakest: start', 'Grow', 'Keep', 'Cut', 'Renew now', 'Book soon',
        'Move visits', 'Renew first', 'Normal', 'Watch', 'High', 'Hire now', 'Wait', 'Not yet', 'Start recruiting now', 'Recruit later',
        'Below your average', 'Above your average', 'Fix the first 90 days', 'Low priority', 'Book now', 'On time to book', 'On target',
        'Below target', 'Enough applicants', 'Need more applicants']
assert len(CHK) <= 30 and len(VERD) <= 30

lists = [L('recsrc', 'Recruiting source', P(REC_SOURCES)), L('applst', 'Applicant status', P(APPLICANT_STATUS)), L('applrsn', 'Applicant reason', P(APPLICANT_REASONS)),
         L('cred', 'Credential', P(CRED_TYPES)), L('credst', 'Credential status', P(CREDST)), L('emp', 'Employment', P(EMPLOYMENT)), L('area', 'Area', P(AREAS)),
         L('cgstatus', 'Caregiver status', P(CAREGIVER_STATUS)), L('leave', 'Leaving reason', P(LEAVE_REASONS)), L('role', 'Role', P(ROLES)), L('team', 'Team', P(TEAMS)),
         L('paytype', 'Pay type', P(PAY_TYPES)), L('mkind', 'Campaign kind', P(MARKETING_KINDS)), L('scen', 'Scenario', P(SCEN)), L('chk', 'Check result', P(CHK)),
         L('verd', 'Decision', P(VERD)), L('course', 'Course', P(COURSES)), L('kind', 'Kind', P(KINDS)), L('outcome', 'Result or answer', P(OUTCOME)), L('step', 'Onboarding step', P(STEPS))]
assert len(lists) <= 20
_M = {'recsrc': K(REC_SOURCES), 'applst': K(APPLICANT_STATUS), 'applrsn': K(APPLICANT_REASONS), 'cred': K(CRED_TYPES), 'credst': K(CREDST), 'emp': K(EMPLOYMENT), 'area': K(AREAS),
      'cgstatus': K(CAREGIVER_STATUS), 'leave': K(LEAVE_REASONS), 'role': K(ROLES), 'team': K(TEAMS), 'paytype': K(PAY_TYPES), 'mkind': K(MARKETING_KINDS), 'scen': K(SCEN),
      'chk': K(CHK), 'verd': K(VERD), 'course': K(COURSES), 'kind': K(KINDS), 'outcome': K(OUTCOME), 'step': K(STEPS)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ck(label): return tok('chk', label)
def vd(label): return tok('verd', label)
