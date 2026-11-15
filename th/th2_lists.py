"""Therapy private practice suite part 2 (Scheduling, Caseload and Rooms): label lists shared by data, tables, tools."""
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


ROLE2 = {'Owner clinician': 'Owner clinician', 'Clinician': 'Employed clinician', 'Contract clinician': 'Contract (self-employed) clinician',
         'Associate': 'Associate (works under supervision)'}
ROLES2 = ['Owner clinician', 'Employed clinician', 'Contract (self-employed) clinician', 'Associate (works under supervision)', 'Practice coordinator', 'Accountant',
          'Clinical supervisor', 'IT support', 'Landlord', 'Cleaner']
CREASON2 = CANCEL_REASONS + ['Rescheduled by client']
CHAN = ['Text message', 'E-mail', 'Phone call']
# labels returned by formulas (a formula never types a word)
CKA = ['No fee', 'Fee due', 'Fee waived', 'Over cap', 'Above target band', 'Top of target band', 'In target band', 'Below target band', 'Away this week',
       'Next session booked', 'No next session', 'In time', 'Late notice', 'Rebooked', 'Not rebooked', 'Within waiver limit', 'Over waiver limit', 'Waiting', 'Offered', 'Filled',
       'Before cancel deadline', 'Inside cancel window', 'Connection problem', 'Details not sent', 'Smooth session', 'Room clash', 'Clear', 'Above room target', 'Near room target',
       'Below room target']
CKB = ['Busy hour', 'Quiet hour', 'Normal hour', 'Past week', 'Away now', 'Planned', 'Cover set', 'Cover needed', 'No cover needed', 'Book now', 'Due soon', 'On schedule',
       'Paid', 'Invoiced', 'Accruing', 'Paid on time', 'Paid late', 'Overdue', 'Not yet due', 'Back to back', 'Has a break', 'Over cap: move sessions', 'Room to book',
       'Away: cover needed', 'Within target band', 'Charge the fee', 'Waive the fee', 'No fee: notice given', 'Above target', 'Within target']
CKC = ['Rooms are enough', 'Add room hours', 'Rooms freed', 'No room saved', 'Cover most sessions', 'Rebook many clients', 'Send on a working day', 'Falls on a Sunday',
       'Add people to the list', 'List is long enough', 'Clear to book', 'Clinician clash', 'Room and clinician clash', 'Can share one slot', 'Cannot share the slot', 'Large closure impact',
       'Small closure impact', 'Rate meets margin', 'Rate below margin', 'Worth listing the hours', 'Not worth listing', 'Heavy day: add a break', 'Day is balanced', 'Top of the band',
       'Above the band', 'Rate on target', 'Rate above target']
for _x in (CKA, CKB, CKC): assert len(_x) <= 30 and len(set(_x)) == len(_x), len(_x)

lists = [
    L('role', 'Role', P(ROLES2)), L('team', 'Team', P(TEAMS)), L('paytype', 'Pay type', P(PAY_TYPES)), L('clin', 'Clinician', P(CLINICIANS)), L('ctype', 'Client type', P(CLIENT_TYPES)),
    L('svc', 'Service', P(SESSION_SERVICES)), L('fmt', 'Session format', P(FORMATS)), L('sstatus', 'Session status', P(SESSION_STATUS)), L('creason', 'Cancel reason', P(CREASON2)),
    L('freq', 'Frequency', P(FREQUENCIES)), L('wday', 'Weekday', P(WORKDAYS)), L('room', 'Room or online', P(ROOMS)), L('room5', 'Room', P(ROOM_NAMES)), L('slotst', 'Diary slot status', P(SLOT_STATUS)),
    L('cstatus', 'Client status', P(CLIENT_STATUS)), L('chan', 'Reminder channel', P(CHAN)), L('absk', 'Absence kind', P(ABSENCE_KINDS)),
    L('cka', 'Check result A', P(CKA)), L('ckb', 'Check result B', P(CKB)), L('ckc', 'Decision', P(CKC)),
]
assert len(lists) == 20
_M = {l['key']: {v['label']: v['key'] for v in l['values']} for l in lists}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ca(x): return tok('cka', x)
def cb(x): return tok('ckb', x)
def cc(x): return tok('ckc', x)
