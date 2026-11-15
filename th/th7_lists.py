"""Therapy practice suite part 7: label lists."""
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


CKIND = ['Visit', 'Phone call', 'Email', 'Thank-you note', 'Information pack']
FBTOPIC = ['Booking', 'Waiting time', 'Clinician', 'Room', 'Fees', 'Online session']
LISTING = ['Directory listing 1', 'Directory listing 2']
CHK = ['No contact yet', 'Contact due', 'On rhythm', 'Done', 'High value', 'Average value', 'Low value', 'Cost within limit', 'Cost over limit', 'No clients won',
       'Within budget', 'Over budget', 'Pays back fast', 'Pays back slowly', 'Does not pay back', 'Fill at or above minimum', 'Fill below minimum', 'Attendance at target',
       'Attendance low', 'Above break-even', 'Below break-even', 'Signed up', 'Contacted', 'Contact the person', 'High score', 'Mid score', 'Low score', 'Planned', 'No next contact', 'Held']
VERD = ['Invest', 'Hold', 'Cut', 'Profitable', 'Losing', 'Worth repeating', 'Stop', 'Spend more', 'Spend less', 'Keep', 'Renegotiate', 'Drop', 'Run it', 'Skip it', 'Contact now',
        'On rhythm now', 'Move budget to the strongest channel', 'Price is right', 'Raise the fee', 'Wait for sign-ups', 'Postpone', 'Announce the start date', 'Keep collecting interest',
        'Improving', 'Falling', 'On track', 'Need more enquiries', 'Send', 'Not worth the time', 'Capacity needed']
VERD2 = ['Waiting list risk', 'Enough capacity', 'Budget is balanced', 'No referrer is overdue']
assert len(CHK) <= 30 and len(VERD) <= 30
lists = [L('src', 'Referral source', P(REFERRAL_SOURCES)), L('svc', 'Service', P(SESSION_SERVICES)), L('ctype', 'Client type', P(CLIENT_TYPES)), L('rkind', 'Referrer kind', P(REFERRER_KINDS)),
         L('enqst', 'Enquiry status', P(ENQUIRY_STATUS)), L('clin', 'Clinician', P(CLINICIANS)), L('prog', 'Group program', P(GROUP_PROGRAMS)), L('grpst', 'Group status', P(GROUP_STATUS)),
         L('signst', 'Sign-up status', P(SIGNUP_STATUS)), L('mkind', 'Activity kind', P(MARKETING_KINDS)), L('wday', 'Weekday', P(WORKDAYS)), L('room5', 'Room', P(ROOM_NAMES)),
         L('ckind', 'Contact kind', P(CKIND)), L('fbtopic', 'Feedback topic', P(FBTOPIC)), L('listing', 'Directory listing', P(LISTING)), L('chk', 'Check result', P(CHK)),
         L('verd', 'Decision', P(VERD)), L('verd2', 'Decision, more', P(VERD2))]
assert len(lists) <= 20
_M = {'src': K(REFERRAL_SOURCES), 'svc': K(SESSION_SERVICES), 'ctype': K(CLIENT_TYPES), 'rkind': K(REFERRER_KINDS), 'enqst': K(ENQUIRY_STATUS), 'clin': K(CLINICIANS), 'prog': K(GROUP_PROGRAMS),
      'grpst': K(GROUP_STATUS), 'signst': K(SIGNUP_STATUS), 'mkind': K(MARKETING_KINDS), 'wday': K(WORKDAYS), 'room5': K(ROOM_NAMES), 'ckind': K(CKIND), 'fbtopic': K(FBTOPIC), 'listing': K(LISTING),
      'chk': K(CHK), 'verd': K(VERD), 'verd2': K(VERD2)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ck(label): return tok('chk', label)
def vd(label): return tok('verd', label) if label in _M['verd'] else tok('verd2', label)
