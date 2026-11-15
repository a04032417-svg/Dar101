"""Car rental suite part 6 (Turnaround, Delivery Runs and Staff): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cr_core import *
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


HOURLY6 = ['Lucia Fernandes', 'Kofi Mensah', 'Jun Park', 'Ravi Chandran', 'Sana Malik', 'Elsa Nordin']
CLEANERS = ['Lucia Fernandes', 'Kofi Mensah']
DRIVERS = ['Jun Park', 'Ravi Chandran']
ZONES = [x for x in LOCATIONS if x != 'Main lot']
SCEN = ['Base', 'Best', 'Worst']
TASKS = {
    'Owner-operator': ['Open the lot and check the board', 'End-of-day lot check', 'Review the next-day runs'],
    'Manager': ['Approve the weekly roster', 'Check the turnaround board', 'Confirm next-day pickups'],
    'Detailer': ['Wash and vacuum each return', 'Check fuel or charge level', 'Restock cleaning supplies'],
    'Delivery driver': ['Check the car before a delivery', 'Hand over at the door', 'Refuel or recharge before return'],
    'Booking assistant': ['Check renter status before pickup', 'Close the counter log', 'Call back enquiries'],
    'Bookkeeper': ['Record staff hours', 'Prepare the pay run', 'Match supplies invoices'],
}
TASK_ITEMS = [t for r in PAY_ROLES for t in TASKS[r]]
VA = ['Ready on time', 'Tight, under the minimum', 'Late, clean first', 'No pickup booked', 'Clean the first car now', 'No car at risk', 'Keep the buffer',
      'Raise the buffer', 'Fee covers the cost', 'Raise the fee', 'Reprice the weakest zone', 'All zones earn the target', 'Add detailer hours', 'Enough detailer hours',
      'Fees cover driver time and fuel', 'Fees are short of the cost', 'No clash, keep the plan', 'Assign the run to the other driver', 'Move the run to another time',
      'Clash found', 'Cleaning fee covers the extra work', 'Price the cleaning fee higher']
VB = ['Add a shift', 'Staff cover is enough', 'Above your usual', 'On your usual', 'Below your usual', 'Pay run is ready', 'Check the hours first', 'Shorten the longest shift',
      'Shifts are within limits', 'Review the missed tasks', 'Tasks are on track', 'Add cover', 'Weekend is covered', 'Hire part-time hours', 'Enough staff',
      'Above your usual spend', 'On track', 'Covered', 'Short', 'Check this pay line']
assert len(VA) <= 30 and len(VB) <= 30

lists = [
    L('payrole', 'Role', P(PAY_ROLES)), L('paytype', 'Pay type', P(PAY_TYPES)), L('class', 'Vehicle class', P(CLASSES)), L('zone', 'Delivery zone', P(ZONES)),
    L('location', 'Location', P(LOCATIONS)), L('runkind', 'Run kind', P(RUN_KINDS)), L('runstatus', 'Run status', P(RUN_STATUS)), L('task', 'Shift task', P(SHIFT_TASKS)),
    L('paystatus', 'Pay status', P(PAY_STATUS)), L('wday', 'Weekday', P(WEEKDAYS)), L('staff', 'Staff member', P(STAFF_NAMES)), L('shiftstaff', 'Shift staff', P(HOURLY6)),
    L('cleaner', 'Detailer', P(CLEANERS)), L('driver', 'Driver', P(DRIVERS)), L('bstatus', 'Booking status', P(BOOK_STATUS)), L('taskitem', 'Task', P(TASK_ITEMS)),
    L('scen', 'Scenario', P(SCEN)), L('va', 'Verdict A', P(VA)), L('vb', 'Verdict B', P(VB)),
]
assert len(lists) <= 20
_M = {'payrole': K(PAY_ROLES), 'paytype': K(PAY_TYPES), 'class': K(CLASSES), 'zone': K(ZONES), 'location': K(LOCATIONS), 'runkind': K(RUN_KINDS), 'runstatus': K(RUN_STATUS),
      'task': K(SHIFT_TASKS), 'paystatus': K(PAY_STATUS), 'wday': K(WEEKDAYS), 'staff': K(STAFF_NAMES), 'shiftstaff': K(HOURLY6), 'cleaner': K(CLEANERS), 'driver': K(DRIVERS),
      'bstatus': K(BOOK_STATUS), 'taskitem': K(TASK_ITEMS), 'scen': K(SCEN), 'va': K(VA), 'vb': K(VB)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def va(label): return tok('va', label)
def vb(label): return tok('vb', label)
