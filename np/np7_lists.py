"""Nonprofit suite part 7 (Board and Governance): label lists shared by data, tables and tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from np_core import *
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


BOARD_NAMES = [b['name'] for b in board_rows()]          # the 11 serving members (the former member is added in the data file)
YR4 = ['Two years ago', 'Last year', 'This year', 'Next year']
YR3 = ['Two years ago', 'Last year', 'This year']
YR2 = ['Last year', 'This year']
YEND = ['This year', 'Next year', 'In two years', 'In three years']
WHEN = ['Now', 'In 6 months', 'In 12 months']
BGROUP = ['Whole board', 'Finance', 'Fundraising', 'Governance']
MSTATUS = ['Held', 'Planned']

CK1 = ['On track', 'Under the setting', 'No meetings', 'Gave', 'Not yet', 'Met', 'On target', 'Behind', 'Filed on time', 'Filed late', 'Overdue', 'Due soon', 'Not recorded',
       'Done', 'Due this week', 'Due this month', 'Coming up', 'Covered', 'One short', 'Short of two or more', 'No member', 'Can renew', 'Term limit reached', 'Filled',
       'Open now', 'Term ends soon', 'Role differs']
CK2 = ['Held', 'Quorum at risk', 'Quorum expected', 'Not asked yet', 'Quorum met', 'Quorum missed', 'Ready', 'Late', 'Not due yet', 'Missing', 'OK', 'Watch', 'Act',
       'Up', 'Down', 'Same', 'Minutes ready', 'Minutes not final']
CK3 = ['Roster complete', 'Seats open', 'Renew', 'Recruit for', 'Full', 'Recruit', 'Stagger terms', 'Fine', 'Add', 'to', 'Need', 'more', 'Finish minutes', 'Up to date',
       'Call', 'Talk to', 'Better', 'Same', 'Worse', 'Behind by', 'All filed', 'Chase', 'Clear', 'Start now', 'On time', 'Pack ready', 'Due this month']
assert len(CK1) <= 30 and len(CK2) <= 30 and len(CK3) <= 30
STAFF_NAMES = [s['name'] for s in staff]

lists = [
    L('brole', 'Board role', P(BOARD_ROLES)), L('committee', 'Committee', P(COMMITTEES)), L('skill', 'Skill', P(SKILLS)), L('mkind', 'Meeting kind', P(MEETING_KINDS)),
    L('attend', 'Attendance', P(ATTEND)), L('dclstatus', 'Declaration status', P(DECL_STATUS)), L('obkind', 'Obligation kind', P(OBLIGATION_KINDS)), L('obstatus', 'Obligation status', P(OB_STATUS)),
    L('mstatus', 'Meeting status', P(MSTATUS)), L('yr', 'Year', P(YR4)), L('yr3', 'Year (three years)', P(YR3)), L('yr2', 'Year (two years)', P(YR2)), L('yend', 'Term ends in', P(YEND)),
    L('when', 'Skills at', P(WHEN)), L('bgroup', 'Board group', P(BGROUP)), L('bmember', 'Board member', P(BOARD_NAMES)),
    L('ck1', 'Check result', P(CK1)), L('ck2', 'Verdict A', P(CK2)), L('ck3', 'Verdict B', P(CK3)),
]
assert len(lists) <= 20
_M = {'brole': K(BOARD_ROLES), 'committee': K(COMMITTEES), 'skill': K(SKILLS), 'mkind': K(MEETING_KINDS), 'attend': K(ATTEND), 'dclstatus': K(DECL_STATUS), 'obkind': K(OBLIGATION_KINDS),
      'obstatus': K(OB_STATUS), 'mstatus': K(MSTATUS), 'yr': K(YR4), 'yr3': K(YR3), 'yr2': K(YR2), 'yend': K(YEND), 'when': K(WHEN), 'bgroup': K(BGROUP), 'bmember': K(BOARD_NAMES),
      'ck1': K(CK1), 'ck2': K(CK2), 'ck3': K(CK3)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def c1(label): return tok('ck1', label)
def c2(label): return tok('ck2', label)
def c3(label): return tok('ck3', label)
