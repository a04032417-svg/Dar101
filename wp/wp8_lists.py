"""Wedding Planning suite part 8 (Attire, Decor, Gifts and After the Wedding): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wp_core import *
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


PROJECTS = [d['project'] for d in diy_rows()]
ATTIRE_KINDS = ['Outfit', 'Shoes', 'Accessories', 'Alterations', 'Rings', 'Other']
CASH_USE = ['Wedding budget', 'Honeymoon fund', 'Not decided']
HSOURCE = ['Savings', 'Cash gifts']
RETURN_KINDS = ['Rental return', 'Deposit refund', 'Supplies', 'Other']
RETURN_STATUS = ['Not due', 'Arranged', 'Done']

# verdict and status words (two lists of at most 30 values; a verdict is built from these words, numbers and dates stay in their own cells)
CKA = ['Make', 'Buy', 'Make half', 'Late', 'Start now', 'On time', 'Done', 'Sent', 'Not sent yet', 'Write now', 'Overdue', 'Due soon', 'Upcoming', 'Paid', 'Open',
       'To finish', 'Order now', 'Order soon', 'Nothing waiting', 'Nothing to buy', 'Nothing to order', 'Nothing to pay', 'Nothing to return', 'Doable', 'Start by',
       'Late by', 'days', 'items', 'tables', 'Ready']
CKB = ['hours a week', 'Order for', 'Order', 'Write', 'notes this week', 'a week to finish by', 'Finished', 'Received', 'expected gifts count only when received',
       'You keep', 'Gap closed', 'Short by', 'Final cost', 'under plan', 'over plan', 'per guest', 'above target', 'below target', 'On target', 'Pay', 'balances',
       'Return', 'refunds', 'open', 'Close the wedding', 'to finish', 'Over', 'Watch', 'On track', 'Pick-up']
assert len(CKA) <= 30 and len(CKB) <= 30 and not set(CKA) & set(CKB), set(CKA) & set(CKB)

lists = [
    L('project', 'DIY project', P(PROJECTS)), L('owner', 'Owner', P(OWNERS)), L('basis', 'Quantity basis', P(SUPPLY_BASIS)), L('dstatus', 'DIY status', P(DIY_STATUS)),
    L('sstatus', 'Shopping status', P(SUPPLY_STATUS)), L('akind', 'Attire kind', P(ATTIRE_KINDS)), L('gevent', 'Gift event', P(GIFT_EVENTS)), L('gkind', 'Gift kind', P(GIFT_KINDS)),
    L('tchannel', 'Note channel', P(THANK_CHANNELS)), L('cuse', 'Cash gift goes to', P(CASH_USE)), L('source', 'Funding source', P(FUND_SOURCES)), L('fstatus', 'Funding status', P(FUND_STATUS)),
    L('hsource', 'Honeymoon source', P(HSOURCE)), L('category', 'Budget category', P(BUDGET_CATEGORIES)), L('rkind', 'Return kind', P(RETURN_KINDS)), L('rstatus', 'Return status', P(RETURN_STATUS)),
    L('pkind', 'Paperwork kind', P(PAPER_KINDS)), L('pstatus', 'Paperwork status', P(PAPER_STATUS)), L('cka', 'Verdict words A', P(CKA)), L('ckb', 'Verdict words B', P(CKB)),
]
assert len(lists) <= 20
_M = {'project': K(PROJECTS), 'owner': K(OWNERS), 'basis': K(SUPPLY_BASIS), 'dstatus': K(DIY_STATUS), 'sstatus': K(SUPPLY_STATUS), 'akind': K(ATTIRE_KINDS), 'gevent': K(GIFT_EVENTS),
      'gkind': K(GIFT_KINDS), 'tchannel': K(THANK_CHANNELS), 'cuse': K(CASH_USE), 'source': K(FUND_SOURCES), 'fstatus': K(FUND_STATUS), 'hsource': K(HSOURCE), 'category': K(BUDGET_CATEGORIES),
      'rkind': K(RETURN_KINDS), 'rstatus': K(RETURN_STATUS), 'pkind': K(PAPER_KINDS), 'pstatus': K(PAPER_STATUS), 'cka': K(CKA), 'ckb': K(CKB)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def c(label):
    """token of a verdict word (list cka or ckb)"""
    if label in _M['cka']: return tok('cka', label)
    return tok('ckb', label)
