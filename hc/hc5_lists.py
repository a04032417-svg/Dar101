"""Home care agency suite part 5: label lists (Client Invoices, Deposits and Payers)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hc_core import *
from lib import L, LV


def P(labels):
    out, seen = [], set()
    for k, l in pairs(labels):
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


AGEBANDS = ['Days 0-30', 'Days 31-60', 'Days 61-90', 'Days over 90']
COLACT = ['Reminder message', 'Phone call', 'Letter', 'Payment plan offered', 'Care paused', 'Final notice']
COLOUT = ['Promised to pay', 'Paid', 'No answer', 'Dispute', 'Plan agreed', 'Left message']
WRSN = ['Payer would not pay', 'Client dispute', 'Small balance', 'Client not reachable', 'Billing error']
CHK = ['Matches agreement', 'Query hours', 'On the card', 'Off the card', 'Enough', 'Low balance', 'Within terms', 'Over terms', 'Open', 'Within usual days', 'Paid late',
       'Chase now', 'Wait', 'Resubmit now', 'Resubmit soon', 'Ready', 'Fix first', 'Not due yet', 'Past due', 'Call today', 'Promise kept', 'Promise broken', 'Closed',
       'Owner approval', 'Office approval', 'No open balance', 'Lines not kept']
VERD = ['Send', 'Check hours', 'Bill', 'Query', 'Credit', 'Covers cost', 'Below cost', 'Top up now', 'Fine', 'Refund due', 'Client owes', 'Hold the deposit', 'Healthy', 'Watch',
        'Act', 'Phone first', 'Offer the plan', 'Shorten the plan', 'Continue', 'Reminder', 'Pause', 'Submit', 'Fix first', 'Chase now', 'Wait', 'Resubmit', 'Write off',
        'Accept', 'Pursue', 'Within target']
VERD2 = ['Over target', 'Margin on target', 'Margin below target', 'No overdue balance', 'No open claims', 'Cash is steady', 'Cash is thin', 'Faster than usual', 'Slower than usual', 'As usual']
assert len(CHK) <= 30 and len(VERD) <= 30

lists = [L('svc', 'Service', P(SERVICES)), L('band', 'Time band', P(BANDS)), L('payer', 'Payer', P(PAYERS)), L('cycle', 'Billing cycle', P(BILL_CYCLES)),
         L('cpayer', 'Claim payer', P(PAYERS[1:])), L('invst', 'Invoice status', P(INVOICE_STATUS)), L('paym', 'Payment method', P(PAYMENT_METHODS)),
         L('paidby', 'Paid by', P(PAID_BY)), L('payk', 'Payment kind', P(PAYMENT_KINDS)), L('clmst', 'Claim status', P(CLAIM_STATUS)), L('clmrsn', 'Claim reason', P(CLAIM_REASONS)),
         L('depk', 'Deposit kind', P(DEPOSIT_KINDS)), L('depst', 'Deposit status', P(DEPOSIT_STATUS)), L('ageband', 'Age band', P(AGEBANDS)), L('colact', 'Collection action', P(COLACT)),
         L('colout', 'Collection outcome', P(COLOUT)), L('wrsn', 'Write-off reason', P(WRSN)), L('chk', 'Check result', P(CHK)), L('verd', 'Decision', P(VERD)), L('verd2', 'Decision, more', P(VERD2))]
assert len(lists) <= 20
_M = {'svc': K(SERVICES), 'band': K(BANDS), 'payer': K(PAYERS), 'cycle': K(BILL_CYCLES), 'cpayer': K(PAYERS[1:]), 'invst': K(INVOICE_STATUS), 'paym': K(PAYMENT_METHODS),
      'paidby': K(PAID_BY), 'payk': K(PAYMENT_KINDS), 'clmst': K(CLAIM_STATUS), 'clmrsn': K(CLAIM_REASONS), 'depk': K(DEPOSIT_KINDS), 'depst': K(DEPOSIT_STATUS), 'ageband': K(AGEBANDS),
      'colact': K(COLACT), 'colout': K(COLOUT), 'wrsn': K(WRSN), 'chk': K(CHK), 'verd': K(VERD), 'verd2': K(VERD2)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ck(label): return tok('chk', label)
def vd(label): return tok('verd', label) if label in _M['verd'] else tok('verd2', label)
