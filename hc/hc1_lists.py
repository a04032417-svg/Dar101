"""Home care agency suite part 1: label lists (Enquiries, Quotes and Agreements)."""
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


QUOTE_STATUS = ['Open', 'Accepted', 'Declined', 'Expired']
SCEN = ['Base', 'Best', 'Worst']
CHK = ['Replied in time', 'Replied late', 'Stale', 'Open, in contact', 'Closed', 'Signed within 7 days', 'Signed later', 'Unsigned, chase', 'Unsigned, waiting',
       'Meets target', 'Below target', 'Valid', 'Expired', 'Locked rate', 'On the card', 'Free hours', 'Full', 'Over the line', 'Next holiday', 'Past holiday',
       'Fast start', 'Slow start', 'Not started', 'Within target', 'Over target', 'Quote on target', 'Quote below target', 'Ended', 'Coming up', 'Not working']
VERD = ['Accept', 'Quote higher', 'Decline', 'Raise the rate', 'Rate card is enough', 'Publish', 'Raise', 'Take a deposit', 'No deposit needed', 'Add a surcharge',
        'Short visit pays', 'Reply faster', 'Reply speed is on target', 'Weakest: assessment', 'Weakest: agreement', 'Weakest: first visit', 'Weakest: reply',
        'Slowest: assessment', 'Slowest: agreement', 'Slowest: introduction', 'Charge covers cost', 'Raise the cancellation share', 'Hold the rate', 'Match the rate',
        'Hire ahead', 'Capacity is enough', 'Take', 'Full', 'Holiday rate pays', 'Holiday rate is thin']
VERD2 = ['Within target', 'Over target', 'Grow this source', 'Cut or fix this source', 'Pays', 'Thin', 'Below cost', 'No free caregiver', 'Hold the quote', 'Quote lower', 'Keep as is']
assert len(CHK) <= 30 and len(VERD) <= 30

lists = [L('svc', 'Service', P(SERVICES)), L('band', 'Time band', P(BANDS)), L('area', 'Area', P(AREAS)), L('payer', 'Payer', P(PAYERS)), L('wday', 'Weekday', P(WEEKDAYS)),
         L('enqsrc', 'Enquiry source', P(ENQ_SOURCES)), L('enqst', 'Enquiry status', P(ENQUIRY_STATUS)), L('loss', 'Loss reason', P(LOSS_REASONS)),
         L('agrk', 'Agreement kind', P(AGREEMENT_KINDS)), L('agrst', 'Agreement status', P(AGREEMENT_STATUS)), L('cycle', 'Billing cycle', P(BILL_CYCLES)),
         L('qst', 'Quote status', P(QUOTE_STATUS)), L('zone', 'Zone', P(ZONES)), L('emp', 'Employment', P(EMPLOYMENT)), L('avail', 'Availability', P(AVAILABILITY)),
         L('clstatus', 'Client status', P(CLIENT_STATUS)), L('scen', 'Scenario', P(SCEN)), L('chk', 'Check result', P(CHK)), L('verd', 'Decision', P(VERD)), L('verd2', 'Decision, more', P(VERD2))]
assert len(lists) <= 20
_M = {'svc': K(SERVICES), 'band': K(BANDS), 'area': K(AREAS), 'payer': K(PAYERS), 'wday': K(WEEKDAYS), 'enqsrc': K(ENQ_SOURCES), 'enqst': K(ENQUIRY_STATUS), 'loss': K(LOSS_REASONS),
      'agrk': K(AGREEMENT_KINDS), 'agrst': K(AGREEMENT_STATUS), 'cycle': K(BILL_CYCLES), 'qst': K(QUOTE_STATUS), 'zone': K(ZONES), 'emp': K(EMPLOYMENT), 'avail': K(AVAILABILITY),
      'clstatus': K(CLIENT_STATUS), 'scen': K(SCEN), 'chk': K(CHK), 'verd': K(VERD), 'verd2': K(VERD2)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ck(label): return tok('chk', label)
def vd(label): return tok('verd', label) if label in _M['verd'] else tok('verd2', label)
