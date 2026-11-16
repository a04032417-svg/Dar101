"""Household Finance suite part 3 (Spending Tracker and Groceries): label lists shared by data, tables, tools."""
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


SPEND_ACCTS = ['Joint checking', 'Partner 1 checking', 'Partner 2 checking', 'Card A', 'Card B', 'Card C', 'Family goals savings', 'Car and home savings']
PAYERS = ['Partner 1', 'Partner 2']
WEEKS = ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5']
PERIODS = ['This month', 'Last month', 'Last 3 months', 'Last 12 months', 'This year', 'Last year']
PACE = ['On pace', 'Over pace', 'Under pace', 'No plan']
CHG = ['Higher', 'Same', 'Lower']
SFLAG = ['Best month', 'At or above target', 'Below target']
CHKS = ['Large payment', 'Possible duplicate', 'Category Other', 'No issue', 'Check the receipt', 'Ask your bank about the second payment', 'Choose a real category', 'Nothing to do']
SEASONS = ['Holidays', 'Back to school', 'Winter utilities']
VA = ['On plan', 'Over plan', 'Fix the top category first', 'Nothing is over plan', 'On pace', 'Overspend at month end', 'Can spend the daily amount', 'Over the envelope',
      'Plan used up', 'Allow the weekly amount shown', 'Envelopes over pace', 'All envelopes on pace', 'Raise the plan or cut spending', 'Watch it this month', 'On track this month']
VB = ['Higher than your history', 'Same as your history', 'Lower than your history', 'Rising categories found', 'No category is up', 'At or above your target', 'Below your target',
      'Save more each month', 'On target', 'More no-spend days than last month', 'Fewer no-spend days than last month', 'Same no-spend days as last month',
      'Eating out is up', 'Eating out is steady', 'Eating out is down']
VC = ['Fuel is up', 'Fuel is normal', 'Fuel is down', 'Set aside the monthly amount', 'No extra needed for the season', 'Raise the plan', 'Keep the plan', 'Lower the plan',
      'Small leaks found', 'No small leaks', 'Possible duplicate found', 'No duplicate found', 'Re-categorise the listed items', 'Clean']
assert len(VA) <= 30 and len(VB) <= 30 and len(VC) <= 30

lists = [
    L('person', 'Person', P(PERSONS)), L('payer', 'Paid by', P(PAYERS)), L('group', 'Group', P(GROUPS)), L('category', 'Category', P(CATEGORY_NAMES)),
    L('atype', 'Account type', P(ACCOUNT_TYPES)), L('spendacct', 'Spending account', P(SPEND_ACCTS)), L('isource', 'Income source', P(INCOME_SOURCES)),
    L('ctkind', 'Contribution kind', P(CT_KINDS)), L('wday', 'Weekday', P(WEEKDAYS)), L('wom', 'Week of the month', P(WEEKS)), L('period', 'Period', P(PERIODS)),
    L('pace', 'Pace flag', P(PACE)), L('chg', 'Change', P(CHG)), L('sflag', 'Savings rate flag', P(SFLAG)), L('chk', 'Check kind and fix', P(CHKS)),
    L('season', 'Season', P(SEASONS)), L('va', 'Verdict A', P(VA)), L('vb', 'Verdict B', P(VB)), L('vc', 'Verdict C', P(VC)),
]
assert len(lists) <= 20
_M = {'person': K(PERSONS), 'payer': K(PAYERS), 'group': K(GROUPS), 'category': K(CATEGORY_NAMES), 'atype': K(ACCOUNT_TYPES), 'spendacct': K(SPEND_ACCTS), 'isource': K(INCOME_SOURCES),
      'ctkind': K(CT_KINDS), 'wday': K(WEEKDAYS), 'wom': K(WEEKS), 'period': K(PERIODS), 'pace': K(PACE), 'chg': K(CHG), 'sflag': K(SFLAG), 'chk': K(CHKS), 'season': K(SEASONS),
      'va': K(VA), 'vb': K(VB), 'vc': K(VC)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def va(label): return tok('va', label)
def vb(label): return tok('vb', label)
def vc(label): return tok('vc', label)
def ck(label): return tok('chk', label)
def cat(label): return tok('category', label)
def grp(label): return tok('group', label)
def pace(label): return tok('pace', label)
def per(label): return tok('period', label)
