"""HVAC and plumbing contractor suite part 3 (Job Costing, Margin and Callbacks): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hv_core import *
from lib import L, LV


def P(labels):
    """pairs() with list keys cut to 21 characters, unique inside the list"""
    out, seen = [], set()
    for k, l in pairs(labels):
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


LEADS = TECH_NAMES[:6]
EQ7 = EQUIP_TYPES + ['No equipment record']
SUPPLIERS = ['Your parts counter', 'Your equipment supplier']
SCEN = ['Base', 'Best', 'Worst']
PERIODS = ['Last 90 days', 'Last 12 months', 'Previous 12 months']
# labels that formulas return (never typed text inside a formula)
CK1 = ['Won money', 'Thin margin', 'Lost money: parts', 'Lost money: hours', 'Lost money: callback', 'Lost money: price', 'Costing incomplete']
CK2 = ['Under target', 'Close to target', 'On target']
CK3 = ['Improving', 'Slipping', 'Steady']
CK4 = ['Complete', 'Hours missing', 'Parts missing']
CK5 = ['Talk this week', 'Watch', 'Fine', 'Within reserve', 'Over reserve', 'Shop warranty', 'Shop goodwill', 'Repair costs less per year', 'Replacement costs less per year',
       'Close call, ask the customer', 'Replace lead: age is past your limit', 'Even', 'Gap is worth a look', 'Not enough data']
CK6 = ['Raise the price', 'Hold the price', 'Re-price first', 'Book more', 'Book less', 'Re-price or book less', 'Fix this cause first', 'Prices are on target', 'Every type is on target',
       'Profit is covered', 'Profit does not cover overhead', 'Margin looks fine', 'Margin falls after callbacks', 'Callbacks are under control', 'Leak is parts', 'Leak is hours', 'Leak is price',
       'No clear leak', 'Re-price these types', 'Hold, no type is under target', 'Hours are the cost to watch', 'Parts are the cost to watch', 'Spread is small', 'Spread is wide']
assert len(CK1) <= 30 and len(CK5) <= 30 and len(CK6) <= 30

lists = [
    L('jobtype', 'Job type', P(JOB_TYPES)), L('trade', 'Trade', P(TRADES)), L('jobkind', 'Job kind', P(JOB_KINDS)), L('tier', 'Option tier', P(TIERS)), L('sitetype', 'Site type', P(SITE_TYPES)),
    L('cbreason', 'Callback reason', P(CALLBACK_REASONS)), L('eqtype', 'Equipment type', P(EQ7)), L('van', 'Van', P(VAN_NAMES)), L('tech', 'Technician', P(LEADS)), L('assist', 'Assistant', P(['Amira Haddad', "Liam O'Connell"])),
    L('scen', 'Scenario', P(SCEN)), L('period', 'Period', P(PERIODS)), L('supplier', 'Supplier', P(SUPPLIERS)),
    L('ck1', 'Job verdict', P(CK1)), L('ck2', 'Target check', P(CK2)), L('ck3', 'Trend', P(CK3)), L('ck4', 'Entry check', P(CK4)), L('ck5', 'Check result', P(CK5)), L('ck6', 'Decision', P(CK6)),
]
_M = {'jobtype': K(JOB_TYPES), 'trade': K(TRADES), 'jobkind': K(JOB_KINDS), 'tier': K(TIERS), 'sitetype': K(SITE_TYPES), 'cbreason': K(CALLBACK_REASONS), 'eqtype': K(EQ7), 'van': K(VAN_NAMES),
      'tech': K(LEADS), 'assist': K(['Amira Haddad', "Liam O'Connell"]), 'scen': K(SCEN), 'period': K(PERIODS), 'supplier': K(SUPPLIERS), 'ck1': K(CK1), 'ck2': K(CK2), 'ck3': K(CK3), 'ck4': K(CK4), 'ck5': K(CK5), 'ck6': K(CK6)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def c1(x): return tok('ck1', x)
def c2(x): return tok('ck2', x)
def c3(x): return tok('ck3', x)
def c4(x): return tok('ck4', x)
def c5(x): return tok('ck5', x)
def c6(x): return tok('ck6', x)
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
