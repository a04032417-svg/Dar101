"""Doula Business suite part 2 (Packages, Pricing and Profit per Hour): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from du_core import *
from lib import L, LV


def P(labels):
    """pairs() with list keys cut to 21 characters, unique inside the list"""
    out, seen = [], set()
    for k, l in pairs(labels):
        if not k[:1].isalpha(): k = 'n' + k
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


PKG_ALL = [p['package'] for p in packages]
PKG_MAIN = [p['package'] for p in packages if p['kind'] != 'Add-on']
ADDONS = [p['package'] for p in packages if p['kind'] == 'Add-on']
PPACKS = [p['package'] for p in packages if p['kind'] == 'Postpartum']
BUNDLES = [p['package'] for p in packages if p['kind'] == 'Combined']
SHIFTS = [r['shift'] for r in pp_rates] + ['Short visit']
SCEN = ['Base', 'Best', 'Worst']
CLIENT_STATUS2 = CLIENT_STATUS + ['Enquiry']
LRANGE = ['Birth package', 'Postpartum hour', 'Night hour', 'Combined package', 'Add-on']
# labels that table formulas and tool verdicts return (a formula never types a word: it points at the list cell)
CK = ['Above the target', 'Below the target', 'Add-on', 'Inside the range', 'Below the range', 'Above the range', 'Bundle pays', 'Bundle loses', 'On plan', 'Over plan', 'Under plan',
      'Add a travel fee', 'Hold the fee', 'Pack is cheaper than hourly', 'Pack price is fine', 'Raise the price', 'Hold the price', 'Lower the price', 'Keep it', 'Reprice it', 'Drop it',
      'Lowest package is below the target', 'Lowest package meets the target', 'Price is below the break-even', 'Price is above the break-even', 'Drop the 120 pack', 'Keep the ladder',
      'Reprice a pack', 'Discount is above the ceiling', 'Discount is inside the ceiling']
CK2 = ['Fix the plan hours', 'Promote it', 'Reprice it now', 'Retire it', 'Keep as it is', 'Launch it', 'Adjust the package', 'Rise holds', 'Rise too small', 'Sales are rising',
       'Sales are flat', 'Sales are falling', 'Shorten the window', 'Keep the window', 'Price matters most', 'Hours matter most', 'Raise the price first', 'Hold the price now',
       'Add a travel fee now', 'Hold the travel fee', 'Rate is fine', 'Rate is low', 'Price is inside your cost', 'Price is below your cost']
assert len(CK) <= 30 and len(CK2) <= 30

lists = [
    L('role', 'Role', P(ROLES)), L('pkind', 'Package kind', P(PACKAGE_KINDS)), L('ckind', 'Client kind', P(CLIENT_KINDS)), L('cstatus', 'Client status', P(CLIENT_STATUS2)),
    L('discount', 'Discount', P(DISCOUNTS)), L('area', 'Service area', P(AREAS)), L('doula', 'Doula', P(DOULA_NAMES)), L('ctstatus', 'Contract status', P(CONTRACT_STATUS)),
    L('package', 'Package or add-on', P(PKG_ALL)), L('cpackage', 'Package', P(PKG_MAIN)), L('addon', 'Add-on', P(ADDONS)), L('ppack', 'Postpartum pack', P(PPACKS)),
    L('bundle', 'Combined package', P(BUNDLES)), L('scen', 'Scenario', P(SCEN)), L('lrange', 'Local range', P(LRANGE)), L('shift', 'Shift', P(SHIFTS)),
    L('ck', 'Check result', P(CK)), L('ck2', 'Verdict', P(CK2)),
]
assert len(lists) <= 20
_M = {'role': K(ROLES), 'pkind': K(PACKAGE_KINDS), 'ckind': K(CLIENT_KINDS), 'cstatus': K(CLIENT_STATUS2), 'discount': K(DISCOUNTS), 'area': K(AREAS), 'doula': K(DOULA_NAMES),
      'ctstatus': K(CONTRACT_STATUS), 'package': K(PKG_ALL), 'cpackage': K(PKG_MAIN), 'addon': K(ADDONS), 'ppack': K(PPACKS), 'bundle': K(BUNDLES), 'scen': K(SCEN), 'lrange': K(LRANGE),
      'shift': K(SHIFTS), 'ck': K(CK), 'ck2': K(CK2)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def ck(label): return tok('ck', label)
def v2(label): return tok('ck2', label)
