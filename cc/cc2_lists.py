"""Childcare center suite part 2 (Rooms, Places and Attendance): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc_core import *
from lib import L, LV


def P(labels):
    """pairs() with keys that start with a letter and are cut to 21 characters, unique inside the list"""
    out, seen = [], set()
    for k, l in pairs(labels):
        if not k[0].isalpha(): k = 'n_' + k
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


DAYTYPE = ['Full day', 'Half day']
HOURS_L = ['7 am', '8 am', '9 am', '10 am', '11 am', '12 pm', '1 pm', '2 pm', '3 pm', '4 pm', '5 pm']
HOLD_STATUS = ['Active', 'Converted to start', 'Expired', 'Released']
CLOSE_REASON = ['Public holiday', 'Winter break', 'Staff training day']
LEAVE_REASON = ['Moved', 'Other setting', 'School']
REQ_STATUS = ['Waiting for answer', 'Offered', 'Accepted', 'Declined']
SCENARIO = ['Base', 'Best', 'Worst']
FIT = ['Accept', 'Accept with a day swap', 'Decline, keep on the list']
FLAG = ['Busy day', 'Normal day', 'Quiet day', 'Over tolerance', 'Within tolerance', 'Move now', 'Move within window', 'Move later', 'No next room',
        'Over capacity', 'Full', 'Has free places', 'Past', 'Coming up', 'Notice met', 'Short notice', 'Hold active', 'Hold ending soon', 'Hold ended',
        'Check in with the family', 'No concern', 'Signed out', 'Still signed in', 'Absent', 'Not booked', 'Late pickup', 'On time', 'Fee matches the rule', 'Fee differs', 'Above 80 percent']
VERDICT = ['Market this day', 'Day is fine', 'Accept', 'Accept with a day swap', 'Decline', 'Open a place', 'Hold', 'Move on the date', 'Keep booked billing', 'Review the schedule',
           'Enough room', 'Add a second group', 'Place available', 'Waiting list', 'Move now', 'Review the absence rule', 'Absence rule is fine', 'Stagger arrivals', 'Fine as it is',
           'Accept the drop-in', 'Decline the drop-in', 'Credit the days', 'No credit', 'Fills within six months', 'Stays below target', 'Reshuffle days', 'Keep the days',
           'Within limit', 'Over the limit', 'Check in with the family']
VERDICT2 = ['Above target', 'Near target', 'Below target', 'Advertise the place now', 'Advertise the place later', 'Charge the late fee', 'No fee inside the grace time',
            'Nothing to move', 'Move up this month', 'Enough staff', 'Add a staff member', 'No concern']
assert len(FLAG) <= 30 and len(VERDICT) <= 30 and len(VERDICT2) <= 30

lists = [
    L('room', 'Room', P(ROOMS)), L('schedule', 'Schedule', P(SCHEDULES)), L('cstatus', 'Child status', P(CHILD_STATUS)), L('attstatus', 'Attendance status', P(ATT_STATUS)),
    L('discount', 'Discount', P(DISCOUNTS)), L('wday', 'Weekday', P(WEEKDAYS)), L('daytype', 'Day type', P(DAYTYPE)), L('hour', 'Hour of the day', P(HOURS_L)),
    L('holdstatus', 'Place hold status', P(HOLD_STATUS)), L('closereason', 'Closure reason', P(CLOSE_REASON)), L('leavereason', 'Leaving reason', P(LEAVE_REASON)),
    L('reqstatus', 'Request status', P(REQ_STATUS)), L('scenario', 'Scenario', P(SCENARIO)), L('fit', 'Fit verdict', P(FIT)), L('flag', 'Check result', P(FLAG)),
    L('verdict', 'Decision', P(VERDICT)), L('verdict2', 'Decision, more', P(VERDICT2)),
]
_M = {'room': K(ROOMS), 'schedule': K(SCHEDULES), 'cstatus': K(CHILD_STATUS), 'attstatus': K(ATT_STATUS), 'discount': K(DISCOUNTS), 'wday': K(WEEKDAYS), 'daytype': K(DAYTYPE),
      'hour': K(HOURS_L), 'holdstatus': K(HOLD_STATUS), 'closereason': K(CLOSE_REASON), 'leavereason': K(LEAVE_REASON), 'reqstatus': K(REQ_STATUS), 'scenario': K(SCENARIO),
      'fit': K(FIT), 'flag': K(FLAG), 'verdict': K(VERDICT), 'verdict2': K(VERDICT2)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def fl(label): return tok('flag', label)
def vd(label): return tok('verdict', label)
def v2(label): return tok('verdict2', label)
YES = '{list:yesno.yes}'
NO = '{list:yesno.no}'
