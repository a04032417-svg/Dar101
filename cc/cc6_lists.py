"""Childcare center suite part 6 (Meals, Health and Safety Records): label lists shared by data, tables, tools."""
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


HOURS_L = ['7 am', '8 am', '9 am', '10 am', '11 am', '12 pm', '1 pm', '2 pm', '3 pm', '4 pm', '5 pm', '6 pm']
DRILL_STATUS = ['Done', 'Missed']
FUP = ['Done', 'Open']
FLAG = ['Counts consistent', 'Over the children present', 'At the limit', 'Record on file', 'Due soon', 'Past due', 'Missing', 'All on file', 'Records due', 'Records missing',
        'Update needed', 'Current', 'Follow-up done', 'Follow-up open', 'Parent not informed', 'On target', 'Below target', 'Above your usual', 'Near your usual', 'Below your usual',
        'On time', 'Overdue', 'Ready to claim', 'Days to fix', 'Done', 'Due this month', 'Missed in month', 'Planned', 'Not due', 'Open']
VERDICT = ['Within your usual cost', 'Above your usual cost', 'Claim ready', 'day(s) to fix', 'All on file', 'due', 'missing', 'Watch this hour', 'No pattern', 'All drills current',
           'overdue', 'On track', 'Missing checks', 'kg to order by the date shown', 'Swap this dish', 'Menu cost is fine', 'Call today', 'Send a reminder', 'Escalate to the owner',
           'follow-ups to close today', 'Nothing open', 'Schedule this drill this month', 'Drill is current', 'Talk to this team', 'No room is missing checks', 'Order less', 'Order is right',
           'Absorb the rise', 'Renegotiate', 'Raise the fee']
VERDICT2 = ['Counts are consistent', 'day(s) over', 'Diet list is current', 'Needs an update', 'Above your usual', 'Near your usual', 'Below your usual', 'Plan is ready',
            'Reduce the order', 'Rooms are on target', 'Hold the menu', 'No records to chase']
assert len(FLAG) <= 30 and len(VERDICT) <= 30 and len(VERDICT2) <= 30
STAFF_NAMES = [s['name'] for s in staff]

lists = [
    L('room', 'Room', P(ROOMS)), L('meal', 'Meal', P(MEALS)), L('hrecord', 'Record', P(HEALTH_RECORDS)), L('hstatus', 'Record status', P(HEALTH_STATUS)), L('itype', 'Incident type', P(INCIDENT_TYPES)),
    L('drill', 'Drill kind', P(DRILL_KINDS)), L('ckind', 'Check kind', P(CHECK_KINDS)), L('checkstatus', 'Check status', P(CHECK_STATUS)), L('wday', 'Weekday', P(WEEKDAYS)),
    L('cstatus', 'Child status', P(CHILD_STATUS)), L('schedule', 'Schedule', P(SCHEDULES)), L('staff', 'Staff member', P(STAFF_NAMES)), L('hourl', 'Hour of the day', P(HOURS_L)),
    L('dstatus', 'Drill status', P(DRILL_STATUS)), L('fup', 'Follow-up', P(FUP)), L('flag', 'Check result', P(FLAG)), L('verdict', 'Decision', P(VERDICT)), L('verdict2', 'Decision, more', P(VERDICT2)),
]
_M = {'room': K(ROOMS), 'meal': K(MEALS), 'hrecord': K(HEALTH_RECORDS), 'hstatus': K(HEALTH_STATUS), 'itype': K(INCIDENT_TYPES), 'drill': K(DRILL_KINDS), 'ckind': K(CHECK_KINDS),
      'checkstatus': K(CHECK_STATUS), 'wday': K(WEEKDAYS), 'cstatus': K(CHILD_STATUS), 'schedule': K(SCHEDULES), 'staff': K(STAFF_NAMES), 'hourl': K(HOURS_L), 'dstatus': K(DRILL_STATUS), 'fup': K(FUP),
      'flag': K(FLAG), 'verdict': K(VERDICT), 'verdict2': K(VERDICT2)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def fl(label): return tok('flag', label)
def vd(label): return tok('verdict', label)
def v2(label): return tok('verdict2', label)
YES = '{list:yesno.yes}'
NO = '{list:yesno.no}'
