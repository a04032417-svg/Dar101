"""Car rental suite part 4 (Deposits, Payments and Payouts): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cr_core import *
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


MARKETS = ['Marketplace A', 'Marketplace B']
REASONS = ['Fees', 'Damage claim']
BUCKETS = ['Not yet due', '1-7 days', '8-30 days', '31-60 days', '60+ days']
METHODS = PAY_METHODS + ['Mobile wallet']
ACCOUNTS = ['Corporate account %d' % i for i in range(1, 7)]
OUTCOMES = ['Kept', 'Missed', 'Pending']
SCENS = ['Base', 'Best', 'Worst']
CK1 = ['Release now', 'Keep for claim', 'Due this week', 'Not due yet', 'Settled', 'On time', 'Released late', 'Still held', 'Paid within terms', 'Paid after terms', 'Open', 'Written off',
       'Promise kept', 'Chase on promised date', 'Escalate', 'Balanced', 'Short', 'Over', 'Lines match', 'Lines differ', 'Kept amount supported', 'Amount to explain', 'Cash holds',
       'Below the floor', 'Payouts match', 'Gap to chase']
CK2 = ['Release holds now', 'All holds current', 'Release the first hold first', 'No holds due', 'Liability covered', 'Keep cash aside', 'Chase the difference', 'All payouts match',
       'Pays later than promised', 'Pays as promised', 'Pays earlier than promised', 'Share rising', 'Share steady', 'Share falling', 'Chase the oldest invoice first', 'Nothing overdue',
       'Send split invoice', 'One invoice is fine', 'Collecting slower', 'Collecting steady', 'Collecting faster', 'Day total matches', 'Amount unexplained', 'Offer transfer on long rentals',
       'Keep cards', 'Extend credit', 'Hold new bookings', 'Ask for payment', 'Write off the balance', 'Keep chasing']
assert len(CK1) <= 30 and len(CK2) <= 30

lists = [
    L('class', 'Vehicle class', P(CLASSES)), L('channel', 'Channel', P(CHANNELS)), L('market', 'Marketplace', P(MARKETS)), L('bstatus', 'Booking status', P(BOOK_STATUS)),
    L('depstatus', 'Deposit status', P(DEPOSIT_STATUS)), L('depreason', 'Deposit kept for', P(REASONS)), L('method', 'Payment method', P(METHODS)), L('paykind', 'Payment kind', P(PAY_KINDS)),
    L('payoutstatus', 'Payout status', P(PAYOUT_STATUS)), L('istatus', 'Invoice status', P(INVOICE_STATUS)), L('bucket', 'Ageing bucket', P(BUCKETS)), L('account', 'Corporate account', P(ACCOUNTS)),
    L('outcome', 'Promise outcome', P(OUTCOMES)), L('scen', 'Scenario', P(SCENS)), L('ck1', 'Check result', P(CK1)), L('ck2', 'Verdict', P(CK2)),
]
assert len(lists) <= 20
_M = {'class': K(CLASSES), 'channel': K(CHANNELS), 'market': K(MARKETS), 'bstatus': K(BOOK_STATUS), 'depstatus': K(DEPOSIT_STATUS), 'depreason': K(REASONS), 'method': K(METHODS),
      'paykind': K(PAY_KINDS), 'payoutstatus': K(PAYOUT_STATUS), 'istatus': K(INVOICE_STATUS), 'bucket': K(BUCKETS), 'account': K(ACCOUNTS), 'outcome': K(OUTCOMES), 'scen': K(SCENS),
      'ck1': K(CK1), 'ck2': K(CK2)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def c1(label): return tok('ck1', label)
def c2(label): return tok('ck2', label)
