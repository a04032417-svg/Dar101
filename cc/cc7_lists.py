"""Childcare center suite part 7 (Families, Programs and Camps): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc_core import *
from lib import L, LV


def P(labels):
    """pairs() with keys that start with a letter and are cut to 21 characters, unique inside the list"""
    out, seen = [], set()
    for k, l in pairs(labels):
        if not k[:1].isalpha(): k = 'n' + k
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


TEACHERS = [RM_LEAD[r] for r in ROOMS]
PERSONS = [OWNER, ASSISTANT_DIRECTOR]
CAMPS = ['Summer camp', 'Holiday camp']
CAMPV = ['Run', 'Run with a minimum', 'Cancel']
# labels that table formulas return (a formula never types a word: it points at the list cell)
FLAG = ['No entry this term', 'Below target', 'Up to date', 'Call this family', 'Reply waiting', 'Recent contact', 'Not enrolled', 'Free slot', 'Booked slot', 'Prepare now',
        'Due this week', 'Coming up', 'Past', 'Held', 'Planned', 'On target', 'Behind target', 'Over the limit', 'Within the limit', 'No camp']
VD = ['on target', 'is behind', 'families unheard', 'Plan is on schedule', 'items due this week', 'All children have entries', 'children need an entry', 'Set the minimum at',
      'Keep the price', 'Raise the price', 'Lower the price', 'Fine as it is', 'Open more places on', 'Call', 'Fine', 'is slow', 'Book', 'families', 'Enough slots',
      'Repeat', 'Change', 'Drop', 'Improving', 'Steady', 'Falling', 'Even', 'has more to do', 'Offer the discount', 'Do not offer the discount', 'Everyone is heard']
VD2 = ['Grow', 'Hold', 'Run', 'Run with a minimum', 'Cancel', 'Promote', 'floater(s)', 'No floaters needed', 'Act first on', 'Add slots, families still to book',
       'No camp weeks', 'Reply time is on target', 'Slow on', 'Nothing due', 'Plan is behind', 'No leavers', 'Camp is below break-even', 'Camp covers its staff cost', 'has', 'more to do']
assert len(FLAG) <= 30 and len(VD) <= 30 and len(VD2) <= 30

lists = [
    L('room', 'Room', P(ROOMS)), L('teacher', 'Teacher', P(TEACHERS)), L('topic', 'Message topic', P(MSG_TOPICS)), L('mstatus', 'Message status', P(MSG_STATUS)),
    L('ekind', 'Event kind', P(EVENT_KINDS)), L('confstatus', 'Conference status', P(CONF_STATUS)), L('okind', 'Observation kind', P(OBS_KINDS)), L('program', 'Program', P(PROGRAMS)), L('campprog', 'Camp program', P(CAMPS)),
    L('cstatus', 'Child status', P(CHILD_STATUS)), L('schedule', 'Schedule', P(SCHEDULES)), L('leavereason', 'Leaving reason', P(['Moved', 'Other setting', 'School'])),
    L('cycle', 'Billing cycle', P(BILL_CYCLES)), L('role', 'Role', P(ROLES)), L('person', 'Sender', P(PERSONS)), L('campverdict', 'Camp decision', P(CAMPV)),
    L('wday', 'Weekday', P(WEEKDAYS)), L('flag', 'Check result', P(FLAG)), L('vd', 'Decision', P(VD)), L('vd2', 'Decision, more', P(VD2)),
]
assert len(lists) <= 20
_M = {'room': K(ROOMS), 'teacher': K(TEACHERS), 'topic': K(MSG_TOPICS), 'mstatus': K(MSG_STATUS), 'ekind': K(EVENT_KINDS), 'confstatus': K(CONF_STATUS), 'okind': K(OBS_KINDS), 'program': K(PROGRAMS), 'campprog': K(CAMPS),
      'cstatus': K(CHILD_STATUS), 'schedule': K(SCHEDULES), 'leavereason': K(['Moved', 'Other setting', 'School']), 'cycle': K(BILL_CYCLES), 'role': K(ROLES), 'person': K(PERSONS),
      'campverdict': K(CAMPV), 'wday': K(WEEKDAYS), 'flag': K(FLAG), 'vd': K(VD), 'vd2': K(VD2)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def fl(label): return tok('flag', label)
def vd(label): return tok('vd', label)
def v2(label): return tok('vd2', label)
YES = '{list:yesno.yes}'
NO = '{list:yesno.no}'
