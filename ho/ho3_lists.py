"""Home Management suite part 3 (Cleaning, Laundry and Chore Rotation): label lists shared by data, tables and tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho_core import *            # ho_core after lib: TODAY, ago, ahead, iso, month_start, add_months follow HO_TODAY
from lib import L, LV


def P(labels):
    out, seen = [], set()
    for k, l in pairs(labels):
        if not k[:1].isalpha(): k = 'n' + k
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


KIDS = ['Child 1', 'Child 2']
STATUS = ['OK', 'Due soon', 'Overdue']
METHODS = ['Rotation', 'Balance by points']
WEEKS = ['Week %d' % i for i in range(1, 14)]
LOADS = ['Colours', 'Whites', 'Towels', 'Bed linen, main bedroom', 'Bed linen, kids rooms', 'School uniform', 'Sports kit', 'Dark clothes', 'Tea towels and cloths', 'Pet bedding', 'Curtains', 'Delicates']
RSTAT = ['Can claim now', 'Points to go', 'Next reward']
# verdict words: tools join them with the numbers (formulas never write words, they point at these cells)
VWA = ['Start with', 'days overdue', 'Nothing is overdue, next is', 'Balanced within', 'points', 'carries', 'more points', 'of adult minutes against an agreed', 'In line with the agreed share',
       'With hidden jobs', 'chores unowned,', 'takes', 'more minutes', 'Choose another person to cover', 'points to', 'All rewards reached', 'Next reward', 'in', 'Balance',
       'carried to next week', 'Busiest laundry day', 'loads', 'Change the bedding on the date shown', 'Swap moves', 'from', 'to', 'does', 'chores', 'minutes', 'has']
VWB = ['free hours on late weeks', 'free hours on a usual week', 'Above your own average', 'In line with your own average', 'Below your own average', 'weeks in a row at goal',
       'Below goal last week', 'Clear in', 'days at', 'minutes a day', 'Moves', 'minutes a month', 'Nothing is overdue', 'Pick a chore from 1 to 45', 'Pick a week from 1 to 13',
       'Change the bedding now', 'Date is outside the work pattern', 'Nothing due that day']
assert len(VWA) <= 30 and len(VWB) <= 30

lists = [
    L('person', 'Person', P(PERSONS)), L('pgrp', 'Person or everyone', P(PERSONS + ['Everyone'])), L('kid', 'Child', P(KIDS)), L('room', 'Room', P(ROOMS)), L('freq', 'Frequency', P(FREQS)), L('wday', 'Weekday', P(WEEKDAYS)), L('shift', 'Shift', P(SHIFTS)),
    L('role', 'Role', P(ROLES)), L('tgroup', 'Team group', P(TEAM_GROUPS)), L('cstat', 'Chore status', P(STATUS)), L('meth', 'Rotation method', P(METHODS)), L('wk', 'Week', P(WEEKS)),
    L('ltype', 'Load type', P(LOADS)), L('rstat', 'Reward status', P(RSTAT)), L('vwa', 'Verdict words A', P(VWA)), L('vwb', 'Verdict words B', P(VWB)),
]
assert len(lists) <= 20
_M = {'person': K(PERSONS), 'pgrp': K(PERSONS + ['Everyone']), 'kid': K(KIDS), 'room': K(ROOMS), 'freq': K(FREQS), 'wday': K(WEEKDAYS), 'shift': K(SHIFTS), 'role': K(ROLES), 'tgroup': K(TEAM_GROUPS), 'cstat': K(STATUS),
      'meth': K(METHODS), 'wk': K(WEEKS), 'ltype': K(LOADS), 'rstat': K(RSTAT), 'vwa': K(VWA), 'vwb': K(VWB)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def wa(label): return tok('vwa', label)
def wb(label): return tok('vwb', label)
def wd(label):
    return wa(label) if label in _M['vwa'] else wb(label)
