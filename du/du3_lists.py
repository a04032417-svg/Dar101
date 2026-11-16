"""Doula business suite part 3 (Contracts, Deposits and Payment Plans): label lists shared by data, tables, tools."""
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


SELLABLE = [p['package'] for p in packages if p['kind'] != 'Add-on']                       # 10 packages a client signs
HOURPACKS = ['Postpartum 40 Hours', 'Postpartum 80 Hours', 'Postpartum 120 Hours', 'Night Support 60 Hours', 'Combined Essential', 'Combined Plus', 'Complete Care Bundle']
AGE = ['Due in the next 30 days', '0 to 30 days late', '31 to 60 days late', '61 days or more late', 'Not yet due']
PAYM = PAY_METHODS + ['Gift voucher']
CTS = CONTRACT_STATUS + ['On hold', 'Renewed']
SCEN = ['Base', 'Best', 'Worst']
# labels that table formulas return (a formula never types a word: it points at the list cell)
CKA = ['Paid on time', 'Paid late', 'Deposit due', 'Deposit overdue',
       'Collect before the window', 'Paid before the window', 'Unpaid inside the window', 'Window not near',
       'Hours left', 'Near expiry', 'Used up', 'Ended',
       'Ends before the window', 'Ends after the window', 'Ends within 7 days of it',
       'Overdue', 'Due soon', 'Not due yet', 'Within the setting', 'Above the setting']
VA = ['Chase first', 'Nothing overdue', 'Plan fits', 'Use fewer instalments', 'Start earlier', 'Keep aside', 'Nothing unearned',
      'Rate inside the setting', 'Rate above the setting', 'Refund due', 'Keep everything', 'Send reminders today', 'No reminder today',
      'Move dates earlier', 'All plans fit', 'Cash arrives every week', 'Gap in week', 'Raise the deposit to', 'Keep the deposit',
      'Offer the discount', 'Do not offer the discount']
VB = ['Collect the difference', 'Refund the difference', 'Balance falls', 'No change in price', 'Release the amount', 'Chase use of unused hours',
      'Offer autopay', 'Payer is on time', 'Ask for bank transfer', 'Card fees are small', 'Collect before the window', 'All balances paid',
      'Unearned cash above the cover', 'Unearned cash below the cover', 'On track', 'Short by', 'Paid ahead by']
assert len(CKA) <= 30 and len(VA) <= 30 and len(VB) <= 30

lists = [
    L('role', 'Role', P(ROLES)), L('pkind', 'Package kind', P(PACKAGE_KINDS)), L('ckind', 'Client kind', P(CLIENT_KINDS)), L('cstatus', 'Client status', P(CLIENT_STATUS)),
    L('discount', 'Discount', P(DISCOUNTS)), L('plan', 'Payment plan', P(PLAN_TYPES)), L('ctstatus', 'Contract status', P(CTS)), L('istatus', 'Instalment status', P(INST_STATUS)),
    L('paykind', 'Payment kind', P(PAYMENT_KINDS)), L('method', 'Payment method', P(PAYM)), L('cxkind', 'Change kind', P(CANCEL_KINDS)), L('cxreason', 'Change reason', P(CANCEL_REASONS)),
    L('doula', 'Doula', P(DOULA_NAMES)), L('band', 'Ageing band', P(AGE)), L('scen', 'Scenario', P(SCEN)), L('package', 'Package', P(SELLABLE)), L('hpackage', 'Hour pack package', P(HOURPACKS)),
    L('cka', 'Check result', P(CKA)), L('va', 'Verdict A', P(VA)), L('vb', 'Verdict B', P(VB)),
]
assert len(lists) <= 20
_M = {'role': K(ROLES), 'pkind': K(PACKAGE_KINDS), 'ckind': K(CLIENT_KINDS), 'cstatus': K(CLIENT_STATUS), 'discount': K(DISCOUNTS), 'plan': K(PLAN_TYPES), 'ctstatus': K(CTS),
      'istatus': K(INST_STATUS), 'paykind': K(PAYMENT_KINDS), 'method': K(PAYM), 'cxkind': K(CANCEL_KINDS), 'cxreason': K(CANCEL_REASONS), 'doula': K(DOULA_NAMES), 'band': K(AGE),
      'scen': K(SCEN), 'package': K(SELLABLE), 'hpackage': K(HOURPACKS), 'cka': K(CKA), 'va': K(VA), 'vb': K(VB)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def ca(label): return tok('cka', label)
def va(label): return tok('va', label)
def vb(label): return tok('vb', label)
