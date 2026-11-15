"""Author and self-publisher suite part 8 (Cash, Tax, Expenses and Author Shares): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from au_core import *
from lib import L, LV


def P(labels):
    """pairs() with list keys cut to 21 characters, unique inside the list"""
    out, seen = [], set()
    for k, l in pairs(labels):
        if not k[:1].isalpha(): k = 'n' + k
        k = k[:21]
        i = 1
        while k in seen: k = k[:19] + str(i); i += 1
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


DRAW_PLAN = 6000
SCEN3 = ['Base', 'Best', 'Worst']
SCEN = SCEN3 + ['Cautious', 'Strong']
FMON = ['Month %d' % i for i in range(1, 13)]
EXP_PEN = list(PEN_NAMES) + ['Shared']
# verdict words that table formulas and tool verdicts return (a formula never types a word: it points at the list cell)
VC = ['Cash holds', 'Low-cash month', 'Pay now', 'Pay in parts', 'Hold the draw', 'Covered', 'Thin', 'Short', 'A gap in the month', 'No gap', 'Pay in this order', 'Draw fits', 'Reduce the draw',
      'Pay in full', 'Pay in two parts', 'Above the floor', 'Below the floor', 'Nothing due']
VT = ['Pot covers the payment', 'Pot is short', 'On track', 'Raise the percent', 'Over budget', 'Near the budget', 'Within budget', 'Keep', 'Ask for a lower price', 'Cancel', 'Complete',
      'Missing receipts', 'Paid in full', 'Short-paid', 'Overdue', 'Due soon', 'Expected later', 'Improving', 'Flat', 'Falling', 'Fee flag', 'Fee normal', 'Receipt on file', 'Add the receipt']
VH = ['Green', 'Amber', 'Red', 'Ready to pay', 'Check', 'Adds up', 'Does not add up', 'Recouped', 'On pace', 'Slow', 'No advance', 'Pay in full now']
AREAS = ['Profit margin, last 12 months', 'Profit margin, last 3 months', 'Ad return (royalties per unit of spend)', 'Ad spend share of revenue', 'Months of cash cover', 'Cash against the floor',
         'Store dependence (largest store share)', 'Read-through, book 1 to book 2', 'Read-through, later books', 'Titles under break-even', 'Categories over budget, last month', 'Tax pot against the next payment']
ACTS = ['Keep going', 'Review the three largest cost lines', 'Check what changed in the last 3 months', 'Pause or fix the weak ad campaign', 'Cut the ad budget until revenue grows',
        'Hold the draw and build the cash cover', 'Pay in parts and hold the draw', 'Move readers to other stores', 'Fix the link from book 1 to book 2',
        'Add a reader magnet in the later books', 'Review the titles under break-even', 'Review the categories over budget', 'Raise the set-aside percent']
YLINES = ['Royalties', 'Page reads', 'Direct store net', 'Event sales', 'Rights', 'Revenue', 'Ads', 'Production', 'Expenses', 'Event costs', 'Costs', 'Profit', 'Tax set-aside', 'Tax paid',
          'Tax pot balance, end of period', 'Owner draws', 'Author copy orders', 'Cash, end of period', 'Contractor payments paid', 'Fees and exchange loss on payments']
YNOTES = ['Profit and Loss: royalties line', 'Profit and Loss: page reads line', 'Profit and Loss: direct store line', 'Profit and Loss: event sales line', 'Profit and Loss: rights line', 'Sum of the five income lines',
          'Profit and Loss: ads line', 'Profit and Loss: production line', 'Profit and Loss: expenses line', 'Profit and Loss: event costs line', 'Sum of the four cost lines', 'Revenue minus costs',
          'Tax Set-aside by Month: set aside', 'Tax Set-aside by Month: tax paid', 'Pot balance at the last full month', 'Cash by Month: owner draw', 'Cash by Month: author copies', 'Closing cash of the last full month',
          'Job Payments marked paid', 'Payments Received: fee and exchange loss']
assert len(YLINES) == 20 == len(YNOTES)
assert len(ACTS) == 13

lists = [
    L('role', 'Role', P(ROLES)), L('team', 'Team', P(TEAMS)), L('paytype', 'Pay type', P(PAY_TYPES)), L('penname', 'Pen name', P(PEN_NAMES)), L('expen', 'Expense pen name', P(EXP_PEN)),
    L('store', 'Store', P(STORES)), L('expcat', 'Expense category', P(EXPENSE_CATEGORIES)), L('ststatus', 'Statement status', P(STATEMENT_STATUS)), L('stage', 'Payment stage', P(PAY_STAGES)),
    L('cpaystatus', 'Job payment status', P(CPAY_STATUS)), L('scen', 'Scenario', P(SCEN)), L('scen3', 'Scenario to test', P(SCEN3)), L('vc', 'Cash verdict', P(VC)), L('vt', 'Check result', P(VT)), L('vh', 'Health and author verdict', P(VH)),
    L('area', 'Health check area', P(AREAS)), L('act', 'Action', P(ACTS)), L('yline', 'Year-end line', P(YLINES)), L('ynote', 'Year-end note', P(YNOTES)), L('fmon', 'Forecast month', P(FMON)),
]
assert len(lists) <= 20
_M = {'role': K(ROLES), 'team': K(TEAMS), 'paytype': K(PAY_TYPES), 'penname': K(PEN_NAMES), 'expen': K(EXP_PEN), 'store': K(STORES), 'expcat': K(EXPENSE_CATEGORIES), 'ststatus': K(STATEMENT_STATUS),
      'stage': K(PAY_STAGES), 'cpaystatus': K(CPAY_STATUS), 'scen': K(SCEN), 'scen3': K(SCEN3), 'vc': K(VC), 'vt': K(VT), 'vh': K(VH), 'area': K(AREAS), 'act': K(ACTS), 'yline': K(YLINES), 'ynote': K(YNOTES), 'fmon': K(FMON)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def vc(label): return tok('vc', label)
def vt(label): return tok('vt', label)
def vh(label): return tok('vh', label)
def act(label): return tok('act', label)
