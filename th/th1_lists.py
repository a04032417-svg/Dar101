"""Therapy practice suite part 1: label lists."""
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


CAUSE = ['No reply', 'Fee too high', 'No suitable time', 'No suitable clinician', 'Waited too long']
ANSWER = ['Accepted', 'Declined', 'No reply', 'Waiting']
NEXTSTEP = ['Book intake', 'Waiting list', 'Signpost', 'Close enquiry']
CBMETH = ['Phone', 'Text message', 'Email']
SLOTHOLD = ['Open', 'Intake hold', 'Urgent hold']
CHK = ['Within target', 'Over target', 'Closed', 'Replied in time', 'Replied late', 'Re-contact due', 'Re-contact planned', 'No re-contact', 'Within 7 days', 'Later than 7 days',
       'Came back', 'Did not return', 'Not attended', 'Back on time', 'Back late', 'Missing, session passed', 'Open, session ahead', 'Takes new clients', 'Full for now',
       'Ready to take', 'No free slots', 'Call today', 'Not due yet', 'Intake possible', 'No intake possible', 'Call overdue']
VERD = ['Match found', 'No clinician free', 'Weakest: screening', 'Weakest: offering', 'Weakest: booking', 'Weakest: starting', 'Reserve is enough', 'Hold more slots', 'Above what you accept',
        'Within what you accept', 'List is clearing', 'List is growing', 'Offer now', 'Raise the deposit', 'Keep the deposit', 'Deposit covers the loss', 'Deposit covers part', 'Offer more',
        'Enough offers', 'Busy month ahead', 'Quiet month ahead', 'Normal month ahead', 'Deposit is due', 'No deposit needed', 'Release slots now', 'Keep all held', 'Worth opening', 'Not worth opening']
assert len(CHK) <= 30 and len(VERD) <= 30
lists = [L('ctype', 'Client type', P(CLIENT_TYPES)), L('svc', 'Service', P(SESSION_SERVICES)), L('src', 'Referral source', P(REFERRAL_SOURCES)), L('cmethod', 'Contact method', P(CONTACT_METHODS)),
         L('prio', 'Priority', P(PRIORITIES)), L('enqst', 'Enquiry status', P(ENQUIRY_STATUS)), L('enqr', 'Enquiry reason', P(ENQUIRY_REASONS)), L('clin', 'Clinician', P(CLINICIANS)),
         L('waitst', 'Waitlist status', P(WAIT_STATUS)), L('fmt', 'Session format', P(FORMATS)), L('sstatus', 'Session status', P(SESSION_STATUS)), L('wday', 'Weekday', P(WORKDAYS)),
         L('depst', 'Deposit status', P(DEPOSIT_STATUS)), L('answer', 'Offer answer', P(ANSWER)), L('slothold', 'Slot use', P(SLOTHOLD)), L('chk', 'Check result', P(CHK)),
         L('verd', 'Decision', P(VERD)), L('feetype', 'Fee type', P(FEE_TYPES)), L('cause', 'Lost enquiry cause', P(CAUSE)), L('nextstep', 'Screening next step', P(NEXTSTEP))]
assert len(lists) <= 20
_M = {'ctype': K(CLIENT_TYPES), 'svc': K(SESSION_SERVICES), 'src': K(REFERRAL_SOURCES), 'cmethod': K(CONTACT_METHODS), 'prio': K(PRIORITIES), 'enqst': K(ENQUIRY_STATUS), 'enqr': K(ENQUIRY_REASONS),
      'clin': K(CLINICIANS), 'waitst': K(WAIT_STATUS), 'fmt': K(FORMATS), 'sstatus': K(SESSION_STATUS), 'wday': K(WORKDAYS), 'depst': K(DEPOSIT_STATUS), 'answer': K(ANSWER), 'slothold': K(SLOTHOLD),
      'chk': K(CHK), 'verd': K(VERD), 'feetype': K(FEE_TYPES), 'cause': K(CAUSE), 'nextstep': K(NEXTSTEP)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ck(label): return tok('chk', label)
def vd(label): return tok('verd', label)
