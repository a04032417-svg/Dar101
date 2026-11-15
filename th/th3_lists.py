"""Therapy private practice suite part 3 (Client Fees, Accounts and Packages): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from th_core import *
from lib import L, LV


def P(labels):
    out, seen = [], set()
    for k, l in pairs(labels):
        k = k[:21]
        if not k or not k[0].isalpha(): k = 'b' + k
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


SCEN = ['Base', 'Best', 'Worst']
# labels returned by formulas (a formula never types a word): table flags, tool verdicts
CKA = ['Paid on time', 'Paid late', 'Overdue', 'Not yet due', 'On plan', 'Written off', 'Settled', 'On next invoice', 'Invoiced', 'Fee waived', 'Nothing to bill', 'No fee', 'Chase now',
       'Waiting', 'Closed', 'Late', 'Due later', 'Used up', 'Expired', 'Expires in 30 days', 'Active', 'Superseded', 'Review due', 'Review within 60 days', 'Current', 'Notice given',
       'Short notice', 'No promise logged', 'Up to date', 'Balance due']
CKB = ['Standard fee', 'Sliding scale applies', 'Package price applies', 'Payer co-pay applies', 'Band confirmed', 'Review at the next assessment', 'Offer it', 'Discount too deep', 'Send now',
       'Check first', 'Chase first', 'On track', 'Plan fits', 'Extend the term', 'Send reminder', 'Final notice due', 'Wait for the promised date', 'Not due yet', 'Ask at booking',
       'Not worth it', 'Keep card', 'Nudge to transfer', 'Raise', 'Hold', 'Chase', 'Offer a plan', 'Write off', 'Deliverable', 'Too much prepaid', 'Covers the pay run']
CKC = ['Short of the pay run', 'At target', 'Below target', 'Within the maximum', 'Slow', 'Within target', 'Above target', 'Policy holding', 'Too many waived', 'On target', 'Chase next']
for _x in (CKA, CKB, CKC): assert len(_x) <= 30 and len(set(_x)) == len(_x), len(_x)
AGEB = ['0-30', '31-60', '61-90', '90+']

lists = [
    L('clin', 'Clinician', P(CLINICIANS)), L('svc', 'Service', P(SESSION_SERVICES)), L('svcall', 'Service or program', P(SERVICES)), L('sstatus', 'Session status', P(SESSION_STATUS)),
    L('feetype', 'Fee type', P(FEE_TYPES)), L('ageband', 'Age band, days', P(AGEB)), L('paym', 'Payment method', P(PAYMENT_METHODS)), L('payk', 'Payment kind', P(PAYMENT_KINDS)),
    L('invst', 'Invoice status', P(INVOICE_STATUS)), L('planst', 'Plan status', P(PLAN_STATUS)), L('pkkind', 'Package kind', P(PACKAGE_KINDS)), L('pkst', 'Package status', P(PACKAGE_STATUS)),
    L('promise', 'Promise outcome', P(PROMISE_OUTCOMES)), L('pmeth', 'Contact method', P(PROMISE_METHODS)), L('gapcause', 'Gap cause', P(GAP_CAUSES)), L('cstatus', 'Client status', P(CLIENT_STATUS)),
    L('scn', 'Scenario', P(SCEN)), L('cka', 'Check result A', P(CKA)), L('ckb', 'Verdict A', P(CKB)), L('ckc', 'Verdict B', P(CKC)),
]
assert len(lists) == 20
_M = {l['key']: {v['label']: v['key'] for v in l['values']} for l in lists}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ca(x): return tok('cka', x)
def vb(x): return tok('ckb', x)
def vc(x): return tok('ckc', x)
def ab(x): return tok('ageband', x)
