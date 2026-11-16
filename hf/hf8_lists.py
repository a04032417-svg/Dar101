"""Household Finance suite part 8 (Big Purchases, Tax Papers and Year Review): label lists shared by data, tables and tools."""
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


CONTACTS = ['Payroll office', 'Freelance client', 'Bank branch', 'Childcare provider', 'Tax preparer']
MV_KINDS = ['Deposit', 'Moving', 'Overlap', 'Setup']
EVENT_ITEMS = [e['item'] for e in event_item_rows()]
CAR_OPTS = [o['option'] for o in purchase_option_rows() if o['bp_id'] == 'BP-01']
RB_ITEMS = ['Home price', 'Down payment', 'Mortgage rate, percent a year', 'Mortgage term, years', 'Monthly rent', 'Rent growth, percent a year', 'Home price growth, percent a year',
            'Upkeep and local charges a year', 'Other running cost a month', 'Buying costs, percent of price', 'Selling costs, percent of price', 'Return on kept money, percent a year']
YITEMS = ['Take-home income', 'Partner 1 paychecks', 'Freelance and side income', 'Counted spending', 'Fixed bills', 'Variable needs', 'Wants', 'Saved into goals', 'Retirement contributions',
          'Total saved', 'Savings rate, percent', 'Debt payments', 'Interest paid', 'Principal repaid', 'Net worth at the end', 'Net worth change', 'Average take-home a month',
          'Average spending a month', 'Highest spending month', 'Months at or above your savings target']
TYEARS = ['2024', '2025', '2026']
PYEARS = ['2025', '2026', '2027']
GD_KINDS = list(GOAL_KINDS) + ['Instalment loan']
STATE = ['Filed', 'Received', 'Expected', 'Overdue', 'Paid', 'Due soon', 'Later', 'Covered', 'Short', 'Higher', 'Same', 'Lower', 'Reached', 'Almost there', 'In progress', 'Early days',
         'Ask the contact', 'Find it in your own records', 'Not due yet', 'Ask the seller for a copy', 'Find the card or bank statement', 'Savings rate at or above your target',
         'Savings rate below your target', 'Plan is below this year', 'Plan is above this year', 'Plan matches this year', 'Biggest rise shown', 'No category is up', 'Nothing is missing',
         'No receipt is missing']
VERDICT = ['Within your limit', 'Above your limit', 'Loan runs as standard', 'Loan is shortened by the extra payment', 'New car costs more a month', 'New car costs less a month',
           'About the same cost a month', 'Save the monthly amount shown', 'Date too soon for this target', 'Already saved', 'Purchase order set by date and gap', 'Covered by the move date',
           'Short at the move date', 'Earliest move date shown', 'Not reached within 10 years', 'Buying breaks even in the years shown', 'Renting costs less in the years tested', 'On target',
           'Over target', 'Documents are missing', 'All documents received', 'Ask for the first document', 'Receipts are missing', 'All receipts kept', 'Find the listed receipts',
           'Set aside the amount shown', 'On track', 'Short of the next payment', 'Net worth up', 'Net worth down']
assert len(STATE) <= 30 and len(VERDICT) <= 30 and len(set(STATE)) == len(STATE)

lists = [
    L('person', 'Person', P(PERSONS)), L('category', 'Category', P(CATEGORY_NAMES)), L('group', 'Budget group', P(GROUPS)), L('priority', 'Priority', P(PRIORITIES)),
    L('bpkind', 'Purchase kind', P(BP_KINDS)), L('bpstatus', 'Purchase status', P(BP_STATUS)), L('tdtype', 'Document type', P(TD_TYPES)), L('dedcat', 'Deduction category', P(DEDUCTION_CATS)),
    L('isource', 'Income source', P(INCOME_SOURCES)), L('contact', 'Who to ask', P(CONTACTS)), L('mvkind', 'Move cost kind', P(MV_KINDS)), L('eitem', 'Event item', P(EVENT_ITEMS)),
    L('caropt', 'Car option', P(CAR_OPTS)), L('rbitem', 'Rent or buy item', P(RB_ITEMS)), L('yitem', 'Year review item', P(YITEMS)), L('tyear', 'Tax year', P(TYEARS)),
    L('pyear', 'Payment year', P(PYEARS)), L('gdkind', 'Goal or loan kind', P(GD_KINDS)), L('state', 'Status', P(STATE)), L('verdict', 'Verdict', P(VERDICT)),
]
assert len(lists) <= 20, len(lists)
_M = {'person': K(PERSONS), 'category': K(CATEGORY_NAMES), 'group': K(GROUPS), 'priority': K(PRIORITIES), 'bpkind': K(BP_KINDS), 'bpstatus': K(BP_STATUS), 'tdtype': K(TD_TYPES),
      'dedcat': K(DEDUCTION_CATS), 'isource': K(INCOME_SOURCES), 'contact': K(CONTACTS), 'mvkind': K(MV_KINDS), 'eitem': K(EVENT_ITEMS), 'caropt': K(CAR_OPTS), 'rbitem': K(RB_ITEMS),
      'yitem': K(YITEMS), 'tyear': K(TYEARS), 'pyear': K(PYEARS), 'gdkind': K(GD_KINDS), 'state': K(STATE), 'verdict': K(VERDICT)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def st(label): return tok('state', label)
def vd(label): return tok('verdict', label)
