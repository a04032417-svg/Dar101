"""Home care agency suite part 4 (Caregiver Payroll and Overtime): label lists."""
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


WARN_KINDS = ['Overtime near the line', 'Missing check-out', 'Negative net pay', 'Hours mismatch', 'Missing time sheet', 'Rate not set']
ADJ_KINDS = ['Retention bonus', 'Referral bonus', 'Holiday thank-you', 'Advance repaid', 'Uniform and supplies', 'Overpayment recovered', 'Training fee repaid']
RAISE_REASONS = ['Yearly review', 'Probation passed', 'Extra skills', 'Market adjustment', 'Live-in rate update', 'Correction']
HOLIDAY_NAMES = ['Year-end Eve', 'Year-end Holiday', 'Year-end Day 2', 'New Year Day', 'Spring Holiday', 'Early Summer Holiday', 'Midsummer Holiday', 'Late Summer Holiday', 'Autumn Holiday', 'Harvest Holiday']
SCENARIOS = ['Base', 'Best', 'Worst']
CHK = ['Open', 'Fixed', 'Awaiting approval', 'Approved', 'Matches', 'Mismatch', 'Safe', 'Near the line', 'Over the line', 'Within ceiling', 'Near ceiling', 'Over ceiling', 'Bonus', 'Deduction',
       'Move', 'Keep', 'Worth it', 'Thin margin', 'Loses money', 'Within target', 'Over target', 'Net pay is fine', 'Negative net pay']
VERD = ['Ready to pay', 'Fix first', 'Overtime in this line', 'Weekly line costs more', 'Daily line costs more', 'Same cost under both', 'Under the target', 'Above the target',
        'Under the ceiling', 'Over the ceiling', 'Matches the setting', 'Burden above the setting', 'Burden below the setting', 'Pay 1.25 times', 'Pay 1.5 times', 'Pay 2 times',
        'Fund now', 'Wait', 'Within budget', 'Over budget', 'Pay as entered', 'Carry the rest forward', 'Saves pay', 'No saving', 'Above your average', 'Within your average',
        'Move the visit', 'Keep the visit']
assert len(CHK) <= 30 and len(VERD) <= 30
lists = [L('emp', 'Employment type', P(EMPLOYMENT)), L('paystat', 'Pay status', P(PAY_STATUS)), L('wday', 'Weekday', P(WEEKDAYS)), L('band', 'Time band', P(BANDS)),
         L('svc', 'Service', P(SERVICES)), L('area', 'Area', P(AREAS)), L('cgstatus', 'Caregiver status', P(CAREGIVER_STATUS)), L('vstatus', 'Visit status', P(VISIT_STATUS)),
         L('role', 'Role', P(ROLES)), L('team', 'Team', P(TEAMS)), L('paytype', 'Pay type', P(PAY_TYPES)), L('wkind', 'Warning kind', P(WARN_KINDS)),
         L('adjk', 'Bonus or deduction kind', P(ADJ_KINDS)), L('raisr', 'Pay rate change reason', P(RAISE_REASONS)), L('hol', 'Holiday', P(HOLIDAY_NAMES)),
         L('scen', 'Scenario', P(SCENARIOS)), L('chk', 'Check result', P(CHK)), L('verd', 'Decision', P(VERD))]
assert len(lists) <= 20
_M = {'emp': K(EMPLOYMENT), 'paystat': K(PAY_STATUS), 'wday': K(WEEKDAYS), 'band': K(BANDS), 'svc': K(SERVICES), 'area': K(AREAS), 'cgstatus': K(CAREGIVER_STATUS),
      'vstatus': K(VISIT_STATUS), 'role': K(ROLES), 'team': K(TEAMS), 'paytype': K(PAY_TYPES), 'wkind': K(WARN_KINDS), 'adjk': K(ADJ_KINDS), 'raisr': K(RAISE_REASONS),
      'hol': K(HOLIDAY_NAMES), 'scen': K(SCENARIOS), 'chk': K(CHK), 'verd': K(VERD)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ck(label): return tok('chk', label)
def vd(label): return tok('verd', label)
