"""Doula business suite part 6 (Doulas, Agency Splits and Pay Runs): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from du_core import *
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


PAYEES = CONTRACTED + BACKUP_NAMES
ATTENDERS = ['Amara Okonkwo', 'Lucia Ferreira', 'Priya Raman', 'Mei-Ling Chen', 'Sven Lindqvist'] + BACKUP_NAMES
SCEN = ['Base', 'Best', 'Worst']
SVC = ['Birth', 'Postpartum', 'Both']
_BASE = [('role', 'Role', ROLES), ('paytype', 'Pay type', PAY_TYPES), ('area', 'Area', AREAS), ('pkind', 'Package kind', PACKAGE_KINDS), ('ckind', 'Client kind', CLIENT_KINDS),
         ('cstatus', 'Client status', CLIENT_STATUS), ('vkind', 'Visit kind', VISIT_KINDS), ('doula', 'Doula', DOULA_NAMES), ('payee', 'Paid person', PAYEES), ('cdoula', 'Contracted doula', CONTRACTED),
         ('backup', 'Backup doula', BACKUP_NAMES), ('attender', 'Doula who attended', ATTENDERS), ('basis', 'Pay basis', PAY_BASIS), ('paystatus', 'Pay status', PAY_STATUS),
         ('scen', 'Scenario', SCEN), ('service', 'Service', SVC)]
_M = {k: K(v) for k, _, v in _BASE}
# verdict and check labels: every label a formula returns is registered here when first used (a formula points at the list cell, never types a word)
_CK = {'ck': [], 'ck2': []}
def ck(label):
    for lst in ('ck', 'ck2'):
        if label in _CK[lst]: return LV(lst, K([label])[label])
    lst = 'ck' if len(_CK['ck']) < 30 else 'ck2'
    _CK[lst].append(label)
    return LV(lst, K([label])[label])


def get_lists():
    ls = [L(k, lab, P(v)) for k, lab, v in _BASE]
    ls.append(L('ck', 'Check result', P(_CK['ck'])))
    if _CK['ck2']: ls.append(L('ck2', 'Verdict', P(_CK['ck2'])))
    assert len(ls) <= 20 and all(len(l['values']) <= 30 for l in ls)
    return ls


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
