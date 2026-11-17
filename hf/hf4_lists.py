"""Household Finance suite part 4 (Debt Payoff Planner): label lists shared by data, tables and tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hf_core import *
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


PLANS = ['Minimum payments only', 'Current plan', 'Snowball', 'Avalanche', 'Avalanche with 100 more']
XOFF = [-300, -200, -100, -50, 0, 50, 100, 200, 300, 500, 700, 1000]
XSTEPS = ['Plan minus 300', 'Plan minus 200', 'Plan minus 100', 'Plan minus 50', 'Plan as set', 'Plan plus 50', 'Plan plus 100', 'Plan plus 200', 'Plan plus 300', 'Plan plus 500', 'Plan plus 700', 'Plan plus 1000']
WINDFALLS = [250, 500, 750, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 7500, 10000]
PYEARS = ['Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5']
RATIOS = ['Debt payments over gross income', 'Consumer debt over take-home', 'Minimum payments over take-home', 'Loan payments over take-home', 'Total debt over yearly gross income',
          'Card balances over yearly take-home', 'Extra payment over take-home', 'Interest share of debt payments', 'Highest rate against the card range', 'Average rate against the card range',
          'Cards share of total debt', 'Loans share of total debt']
STEPSZ = ['50', '100', '200']
STATE = ['Active', 'Paid off', 'Covers interest', 'Below interest', 'Within range', 'Above range', 'Below range', 'No typical range', 'Tight', 'Comfortable', 'Within your limit', 'Above your limit',
         'On time', 'Late', 'Highest rate', 'Lower rate', 'Within a year', 'Longer than a year']
VERDICT = ['Debt-free date and interest shown', 'Not paid off within the schedule', 'Avalanche costs less interest', 'Snowball costs less interest', 'Both cost the same', 'Extra payment shortens the plan',
           'Pay the extra shown', 'Not within reach with the steps tested', 'Move the extra to the highest rate', 'Extra already on the highest rate', 'Within the typical range', 'Above the typical range',
           'Every minimum covers the interest', 'A minimum does not cover the interest', 'Pay on the date shown', 'Move the due date', 'Windfall saves interest and months', 'Half paid by the date shown',
           'Total debt is down', 'Total debt is up', 'Total debt is the same', 'Ends on schedule', 'Check the payment', 'Fund the emergency fund first', 'Debt first, typical range only',
           'Type 50, 100 or 200', 'Within your limit', 'Above your limit', 'Highest interest cost is first']
assert len(STATE) <= 30 and len(VERDICT) <= 30 and len(set(STATE)) == len(STATE) and len(set(VERDICT)) == len(VERDICT)

lists = [
    L('person', 'Person', P(PERSONS)), L('payer', 'Paid to', P(['Partner 1', 'Partner 2'])), L('dkind', 'Debt kind', P(DEBT_KINDS)), L('atype', 'Account type', P(ACCOUNT_TYPES)), L('side', 'Asset or liability', P(NW_CLASS)),
    L('isource', 'Income source', P(INCOME_SOURCES)), L('method', 'Payoff method', P(DEBT_METHODS)), L('plans', 'Payoff plan', P(PLANS)), L('xstep', 'Extra payment step', P(XSTEPS)),
    L('planyear', 'Plan year', P(PYEARS)), L('ratio', 'Debt ratio', P(RATIOS)), L('stepsz', 'Step size', P(STEPSZ)), L('state', 'Status', P(STATE)), L('verdict', 'Verdict', P(VERDICT)),
]
assert len(lists) <= 20
_M = {'person': K(PERSONS), 'payer': K(['Partner 1', 'Partner 2']), 'dkind': K(DEBT_KINDS), 'atype': K(ACCOUNT_TYPES), 'side': K(NW_CLASS), 'isource': K(INCOME_SOURCES), 'method': K(DEBT_METHODS), 'plans': K(PLANS), 'xstep': K(XSTEPS),
      'planyear': K(PYEARS), 'ratio': K(RATIOS), 'stepsz': K(STEPSZ), 'state': K(STATE), 'verdict': K(VERDICT)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def st(label): return tok('state', label)
def vd(label): return tok('verdict', label)
