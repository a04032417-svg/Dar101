"""Home care agency suite part 8 (Owner Money and Business Health): label lists."""
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


SCEN = ['Base', 'Best', 'Worst']
WEEKS = ['Week %d' % i for i in range(1, 14)]
MEAS = ['Gross margin per hour', 'Overtime share', 'Fill rate', 'Days to be paid', 'Caregiver turnover', 'Weeks of cash cover']
LVL = ['Target', 'Amber limit', 'Red limit', 'Weight']
STVER = ['Current', 'After raise', 'At 1,000 hours']
CHK = ['Over budget', 'Within budget', 'Above the floor', 'Below the floor', 'Paid', 'Next run', 'Planned', 'Covered by profit', 'Above profit', 'Green', 'Amber', 'Red']
VERD = ['Healthy', 'Watch', 'Act', 'Cash stays above the floor', 'Arrange credit', 'Take it', 'Take less', 'Wait', 'Move it now', 'Move part now', 'Not yet',
        'On track', 'Behind', 'Hire office help now', 'Plan it', 'Above break-even', 'Below break-even', 'Overhead within target', 'Overhead above target', 'Raise', 'Hold',
        'Release', 'Keep', 'Worth adding', 'Budget on track', 'Budget overrun', 'Enough cover', 'Build cash', 'Start-up mode', 'Full mode']
assert len(CHK) <= 30 and len(VERD) <= 30

lists = [L('ecat', 'Expense category', P(EXPENSE_CATEGORIES)), L('mkind', 'Marketing kind', P(MARKETING_KINDS)), L('taxst', 'Tax set-aside status', P(TAX_STATUS)), L('role', 'Role', P(ROLES)),
         L('team', 'Team', P(TEAMS)), L('paytype', 'Pay type', P(PAY_TYPES)), L('svc', 'Service', P(SERVICES)), L('payer', 'Payer', P(PAYERS)), L('scen', 'Scenario', P(SCEN)),
         L('wk', 'Week', P(WEEKS)), L('meas', 'Health measure', P(MEAS)), L('lvl', 'Target level', P(LVL)), L('stver', 'Staff cost version', P(STVER)), L('chk', 'Check result', P(CHK)),
         L('verd', 'Decision', P(VERD))]
assert len(lists) <= 20
_M = {'ecat': K(EXPENSE_CATEGORIES), 'mkind': K(MARKETING_KINDS), 'taxst': K(TAX_STATUS), 'role': K(ROLES), 'team': K(TEAMS), 'paytype': K(PAY_TYPES), 'svc': K(SERVICES), 'payer': K(PAYERS),
      'scen': K(SCEN), 'wk': K(WEEKS), 'meas': K(MEAS), 'lvl': K(LVL), 'stver': K(STVER), 'chk': K(CHK), 'verd': K(VERD)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ck(label): return tok('chk', label)
def vd(label): return tok('verd', label)
