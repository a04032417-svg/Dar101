"""Home care suite part 3 (Visits, Hours and Travel): label lists."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hc_core import *
from lib import L, LV


def P(labels):
    out, seen = [], set()
    for k, l in pairs(labels):
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


NOTICE = ['Two days or more', 'One to two days', 'Four to 23 hours', 'Under four hours']
CFIELD = ['Check-in time', 'Check-out time', 'Start time', 'Caregiver', 'Visit status']
# labels that formulas return in table columns (never typed text inside a formula)
CHK = ['On time', 'Late', 'Short', 'Long', 'Missed', 'Cancelled', 'Not due yet', 'No check-in', 'Check-in overdue', 'Checked in', 'Repeat caregiver', 'Single event',
       'Short notice', 'Enough notice', 'Matches', 'Mismatch', 'Not sent', 'Within target', 'Over target', 'Billed all', 'Part unbilled', 'Call caregiver first',
       'Call client first', 'Corrected same week', 'Corrected later', 'Time sheet in']
# labels that tool outputs return
VERD = ['On target', 'Watch', 'Act', 'Investigate', 'Normal', 'Leak found', 'No leak', 'Travel paid, not billed', 'Overrun not billed', 'Minimum-visit rounding', 'Missed visit with pay',
        'Accept', 'Query', 'Absorb the travel', 'Charge travel', 'Share the pair', 'Keep apart', 'Cluster the week', 'Keep as is', 'Pay as claimed', 'Query hours', 'Correct hours',
        'Rounds in your favour', 'Rounds against you', 'Bill the extra', 'Change the schedule', 'Better than last year', 'Worse than last year']
assert len(CHK) <= 30 and len(VERD) <= 30

lists = [L('svc', 'Service', P(SERVICES)), L('band', 'Time band', P(BANDS)), L('area', 'Area', P(AREAS)), L('emp', 'Employment type', P(EMPLOYMENT)), L('wday', 'Weekday', P(WEEKDAYS)),
         L('vstatus', 'Visit status', P(VISIT_STATUS)), L('cover', 'Cover type', P(COVER_KINDS)), L('delay', 'Delay reason', P(DELAY_REASONS)), L('miss', 'Missed visit reason', P(MISS_REASONS)),
         L('cgstatus', 'Caregiver status', P(CAREGIVER_STATUS)), L('clstatus', 'Client status', P(CLIENT_STATUS)), L('cycle', 'Billing cycle', P(BILL_CYCLES)), L('role', 'Role', P(ROLES)),
         L('team', 'Team', P(TEAMS)), L('paytype', 'Pay type', P(PAY_TYPES)), L('zone', 'Zone', P(ZONES)), L('chk', 'Check result', P(CHK)), L('verd', 'Decision', P(VERD)),
         L('notice', 'Notice band', P(NOTICE)), L('cfield', 'Field corrected', P(CFIELD))]
assert len(lists) <= 20
_M = {l['key']: {v['label']: v['key'] for v in l['values']} for l in lists}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ck(label): return tok('chk', label)
def vd(label): return tok('verd', label)
