"""HVAC and plumbing contractor suite part 7 (Invoices, Collections and Seasonal Cash): label lists shared by data, tables, tools."""
import sys, os, re; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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


BILL_KINDS = ['Fixed', 'Payroll', 'Supplier', 'Tax']
BILL_CATS = ['Parts run', 'Equipment', 'Technician and office pay', 'Owner draw', 'Accounting', 'Rent and yard', 'Insurance', 'Software', 'Utilities', 'Vehicle lease', 'Tax set-aside payment']
SUPPLIERS = ['Your equipment supplier', 'Your parts counter', 'Electrical subcontractor', 'Sheet-metal subcontractor']
DRAW_OPTIONS = ['Current draw', 'Safe draw', 'Current plus 10 percent', 'Current less 20 percent', 'Current less 40 percent']
TECH6 = TECH_NAMES[:6]
base_lists = [
    L('tech', 'Technician', P(TECH6)), L('sitetype', 'Site type', P(SITE_TYPES)), L('jobtype', 'Job type', P(JOB_TYPES)), L('paymethod', 'Payment method', P(PAY_METHODS)),
    L('invstatus', 'Invoice status', P(INVOICE_STATUS)), L('paykind', 'Payment kind', P(PAYMENT_KINDS)), L('chasemethod', 'Chase method', P(CHASE_METHODS)), L('chaseoutcome', 'Chase outcome', P(CHASE_OUTCOMES)),
    L('pokind', 'Purchase kind', P(PURCHASE_KINDS)), L('postatus', 'Purchase status', P(PO_STATUS)), L('expcat', 'Expense category', P(EXPENSE_CATEGORIES)), L('season', 'Season', P(SEASONS)),
    L('billkind', 'Bill kind', P(BILL_KINDS)), L('billcat', 'Bill category', P(BILL_CATS)), L('supplier', 'Supplier', P(SUPPLIERS)), L('drawopt', 'Owner pay option', P(DRAW_OPTIONS)),
]
_M = {'tech': K(TECH6), 'sitetype': K(SITE_TYPES), 'jobtype': K(JOB_TYPES), 'paymethod': K(PAY_METHODS), 'invstatus': K(INVOICE_STATUS), 'paykind': K(PAYMENT_KINDS), 'chasemethod': K(CHASE_METHODS),
      'chaseoutcome': K(CHASE_OUTCOMES), 'pokind': K(PURCHASE_KINDS), 'postatus': K(PO_STATUS), 'expcat': K(EXPENSE_CATEGORIES), 'season': K(SEASONS), 'billkind': K(BILL_KINDS), 'billcat': K(BILL_CATS),
      'supplier': K(SUPPLIERS), 'drawopt': K(DRAW_OPTIONS)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula

# ---- labels that formulas return: registered on first use, split in lists of at most 30 values
CKL, CKK = [], {}
def ck(label):
    if label not in CKK:
        k = re.sub(r'[^a-z0-9]+', '_', label.lower()).strip('_')
        if not k[0].isalpha(): k = 'b' + k
        k = k[:21]
        while k in CKK.values(): k = k[:-1] + 'x'
        CKK[label] = k; CKL.append(label)
    return '{list:ck%d.%s}' % (CKL.index(label) // 30 + 1, CKK[label])
def ck_lists():
    out = []
    for i in range(0, len(CKL), 30):
        out.append(L('ck%d' % (i // 30 + 1), 'Check result %d' % (i // 30 + 1), [(CKK[l], l) for l in CKL[i:i + 30]]))
    return out
