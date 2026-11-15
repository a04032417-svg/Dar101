"""Childcare center suite part 4 (Tuition, Fees and Invoices): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc_core import *
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


REASONS = ['Public holiday', 'Staff training day', 'Winter break']
YEARS = [str(TODAY.year - 1), str(TODAY.year)]
CKA = ['Matches', 'Differs', 'Fees charged', 'Fees missing', 'Statement matches', 'Statement differs', 'Sent', 'Not sent yet', 'Repeat late', 'Occasional', 'Holds target', 'Above target',
       'Notice kept', 'Notice short', 'No notice yet', 'Refund due', 'On the run', 'No child enrolled', 'Registration missing', 'Fees complete']
CK2 = ['Invoice ready', 'Lines to check', 'All match', 'Some differ', 'Percent rule is cheapest', 'Flat amount is cheapest', 'No discount is cheapest', 'Rise now', 'Rise at a later date', 'Rise less',
       'Fee covers the cost', 'Fee below the cost', 'Ledger matches', 'Ledger differs', 'Statement matches ledger', 'Statement differs from ledger', 'Offer monthly', 'Keep weekly',
       'Accept the day', 'Decline the day', 'Bill camp fee', 'Bill tuition', 'Keep the discounts', 'Limit the discounts']
CK3 = ['Send notice by', 'Notice period too short', 'Rise is even', 'Uneven by room', 'Fees charged', 'Fees missing', 'First invoice ready', 'Check the start date',
       'Credit centre-chosen days', 'Offer a make-up day', 'No credit', 'Reprice the lowest schedule', 'Rates are in line', 'Issue both runs', 'Issue the weekly run',
       'Issue the monthly run', 'No run on this date']
assert len(CKA) <= 30 and len(CK2) <= 30 and len(CK3) <= 30

lists = [
    L('room', 'Room', P(ROOMS)), L('schedule', 'Schedule', P(SCHEDULES)), L('cstatus', 'Child status', P(CHILD_STATUS)), L('cycle', 'Billing cycle', P(BILL_CYCLES)), L('method', 'Payment method', P(PAY_METHODS)),
    L('discount', 'Discount', P(DISCOUNTS)), L('istatus', 'Invoice status', P(INVOICE_STATUS)), L('depstatus', 'Deposit status', P(DEPOSIT_STATUS)), L('wday', 'Weekday', P(WEEKDAYS)),
    L('creason', 'Closure reason', P(REASONS)), L('syear', 'Statement year', P(YEARS)), L('cka', 'Check result', P(CKA)), L('ck2', 'Verdict A', P(CK2)), L('ck3', 'Verdict B', P(CK3)),
]
assert len(lists) <= 20
_M = {'room': K(ROOMS), 'schedule': K(SCHEDULES), 'cstatus': K(CHILD_STATUS), 'cycle': K(BILL_CYCLES), 'method': K(PAY_METHODS), 'discount': K(DISCOUNTS), 'istatus': K(INVOICE_STATUS),
      'depstatus': K(DEPOSIT_STATUS), 'wday': K(WEEKDAYS), 'creason': K(REASONS), 'syear': K(YEARS), 'cka': K(CKA), 'ck2': K(CK2), 'ck3': K(CK3)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ca(label): return tok('cka', label)
def c2(label): return tok('ck2', label)
def c3(label): return tok('ck3', label)
