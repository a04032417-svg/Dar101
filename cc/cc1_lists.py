"""Childcare center suite part 1 (Enquiries, Tours and Waitlist): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc_core import *
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


RBAND = ['Up to 4 hours', '5 to 24 hours', '25 to 48 hours', 'Over 48 hours', 'No reply yet']
OFFERANS = ['Accepted', 'Declined']
APPSTATUS = ['Forms pending', 'Deposit pending', 'On waiting list', 'Enrolled', 'Withdrawn']
NEXTSTEP = ['Call today', 'Write today', 'Remind about the tour', 'Send the next steps', 'Chase the forms', 'Re-confirm the place', 'Close the enquiry', 'Not due yet']
SCEN = ['Base', 'Best', 'Worst']
WDAY7 = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
# labels that table formulas return (a formula never types a word: it points at the list cell)
CKA = ['Reply in time', 'Slow reply', 'No reply yet', 'Outcome recorded', 'Outcome missing', 'Tour coming up', 'On the list', 'Re-confirm now', 'Offer open', 'Offer overdue',
       'Started', 'Withdrawn', 'Answered', 'Release the place', 'Chase today', 'Waiting for answer', 'Complete', 'Forms missing', 'Deposit missing', 'Forms and deposit missing',
       'Slots free', 'Fully booked', 'Room has a free place', 'Room is full', 'Can start now', 'Starts later', 'No place yet', 'Recruit more', 'Enough waiting']
CK2 = ['Offer now', 'Offer soon', 'Hold the place', 'No free place', 'No one waiting', 'Can start on the date', 'Start later', 'No place in 12 months',
       'Funnel on track', 'Fix the first reply', 'Fix tour booking', 'Fix tour attendance', 'Fix tour to application', 'Fix application to enrolment',
       'Feed this source', 'Hold this source', 'Cut this source', 'Keep it', 'Renegotiate it', 'Drop it',
       'Fix places first', 'Fix price first', 'Fix hours first', 'Fix distance first', 'Fix reply time first', 'Reply faster', 'Reply time on target',
       'Below occupancy target', 'At occupancy target']
CK3 = ['Add tour slots', 'Enough tour slots', 'Offer a place', 'Re-confirm', 'Remove from the list', 'Keep waiting', 'Wait for the answer', 'Hire relief', 'Hold staffing',
       'Repeat the open day', 'Change the open day', 'Drop the open day', 'Date added is fairest', 'Sibling first is fairest', 'Staff child first is fairest',
       'Same winner under every rule', 'Worth it', 'Not worth it', 'Places will fill', 'Places may stay empty']
assert len(CKA) <= 30 and len(CK2) <= 30 and len(CK3) <= 30

lists = [
    L('role', 'Role', P(ROLES)), L('room', 'Room', P(ROOMS)), L('schedule', 'Schedule', P(SCHEDULES)), L('cstatus', 'Child status', P(CHILD_STATUS)), L('source', 'Enquiry source', P(SOURCES)),
    L('estatus', 'Enquiry status', P(ENQUIRY_STATUS)), L('lostreason', 'Lost reason', P(LOST_REASONS)), L('tourstatus', 'Tour status', P(TOUR_STATUS)), L('waitstatus', 'Waiting list status', P(WAIT_STATUS)),
    L('priority', 'Priority', P(PRIORITIES)), L('mkind', 'Marketing kind', P(MARKETING_KINDS)), L('rband', 'Reply time band', P(RBAND)), L('offerans', 'Offer answer', P(OFFERANS)),
    L('appstatus', 'Application status', P(APPSTATUS)), L('nextstep', 'Next step', P(NEXTSTEP)), L('scen', 'Scenario', P(SCEN)), L('wday', 'Weekday', P(WDAY7)),
    L('cka', 'Check result', P(CKA)), L('ck2', 'Verdict A', P(CK2)), L('ck3', 'Verdict B', P(CK3)),
]
assert len(lists) <= 20
_M = {'role': K(ROLES), 'room': K(ROOMS), 'schedule': K(SCHEDULES), 'cstatus': K(CHILD_STATUS), 'source': K(SOURCES), 'estatus': K(ENQUIRY_STATUS), 'lostreason': K(LOST_REASONS),
      'tourstatus': K(TOUR_STATUS), 'waitstatus': K(WAIT_STATUS), 'priority': K(PRIORITIES), 'mkind': K(MARKETING_KINDS), 'rband': K(RBAND), 'offerans': K(OFFERANS), 'appstatus': K(APPSTATUS),
      'nextstep': K(NEXTSTEP), 'scen': K(SCEN), 'wday': K(WDAY7), 'cka': K(CKA), 'ck2': K(CK2), 'ck3': K(CK3)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def ca(label): return tok('cka', label)
def c2(label): return tok('ck2', label)
def c3(label): return tok('ck3', label)
def ns(label): return tok('nextstep', label)
