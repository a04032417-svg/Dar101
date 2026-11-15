"""Author and self-publisher suite part 5 (Readers, Newsletter and Launches): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from au_core import *
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


TITLE_NAMES = [t['title'] for t in title_rows()]
SWAP_KINDS = ['Newsletter swap', 'Paid promotion']
OWNER_ROLES = ['Editor', 'Cover designer', 'Formatter', 'Author-publisher', 'Launch coordinator', 'Virtual assistant', 'Ad specialist']
SCEN = ['Base', 'Best', 'Worst']
# labels that table formulas and tool verdicts return (a formula never types a word: it points at the list cell)
CKA = ['Done on time', 'Done late', 'Late', 'Due soon', 'Not due yet', 'Done', 'Posted', 'Overdue', 'Waiting for review', 'Not sent yet', 'Marked no reply',
       'Keep', 'Test', 'Remove from the list', 'Good response', 'Low response', 'No copies sent', 'Remind today', 'Wait', 'Mark no reply', 'Do today', 'This week',
       'Ready to launch', 'At risk', 'Delay the launch', 'Send more copies', 'Enough copies']
CK2 = ['Good send', 'Average send', 'Weak send', 'Swap again', 'Change partner', 'Stop', 'Invite again', 'Skip', 'Keep this source', 'Watch this source', 'Stop this source',
       'Send more of this', 'Send fewer of this', 'Clean the list', 'Keep the list', 'On the way to the target', 'Behind the target', 'Free of charge']
CK3 = ['Launch worked', 'In line with my average', 'Weaker than my average', 'Better', 'Flat', 'Worse', 'Reachable from your list', 'Stretch', 'Reviewer mix works', 'Change the mix',
       'Plan fits', 'Too many sends', 'Too few sends', 'Ahead', 'On pace', 'Behind']
assert len(CKA) <= 30 and len(CK2) <= 30 and len(CK3) <= 30

lists = [
    L('role', 'Role', P(ROLES)), L('ownerrole', 'Step owner role', P(OWNER_ROLES)), L('penname', 'Pen name', P(PEN_NAMES)), L('series', 'Series', P(SERIES)), L('tstatus', 'Title status', P(TITLE_STATUS)), L('step', 'Launch step', P(LAUNCH_STEP_NAMES)),
    L('taskstatus', 'Step status', P(TASK_STATUS)), L('arcstatus', 'Advance copy status', P(ARC_STATUS)), L('rkind', 'Reviewer kind', P(REVIEWER_KINDS)), L('subsource', 'Subscriber source', P(SUB_SOURCES)),
    L('skind', 'Send kind', P(SEND_KINDS)), L('swapkind', 'Swap kind', P(SWAP_KINDS)), L('title', 'Title', P(TITLE_NAMES)), L('scen', 'Scenario', P(SCEN)),
    L('cka', 'Check result', P(CKA)), L('ck2', 'Verdict A', P(CK2)), L('ck3', 'Verdict B', P(CK3)),
]
assert len(lists) <= 20
_M = {'role': K(ROLES), 'ownerrole': K(OWNER_ROLES), 'penname': K(PEN_NAMES), 'series': K(SERIES), 'tstatus': K(TITLE_STATUS), 'step': K(LAUNCH_STEP_NAMES), 'taskstatus': K(TASK_STATUS), 'arcstatus': K(ARC_STATUS),
      'rkind': K(REVIEWER_KINDS), 'subsource': K(SUB_SOURCES), 'skind': K(SEND_KINDS), 'swapkind': K(SWAP_KINDS), 'title': K(TITLE_NAMES), 'scen': K(SCEN), 'cka': K(CKA), 'ck2': K(CK2), 'ck3': K(CK3)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def ca(label): return tok('cka', label)
def c2(label): return tok('ck2', label)
def c3(label): return tok('ck3', label)
