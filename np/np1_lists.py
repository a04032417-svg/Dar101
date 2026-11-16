"""Nonprofit suite part 1 (Donor Book and Gift Log): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from np_core import *
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


BASIS = list(VALUE_BASIS) + ['Not recorded']
FUND_L = [f['fund'] for f in funds]
CAMPAIGN_L = list(CAMPAIGNS)

# verdict and check labels (two lists of at most 30 values)
CKA = ['Complete', 'Donor missing', 'Fund missing', 'Possible duplicate', 'Batch off', 'Tied', 'Off', 'Open', 'Send today', 'On time', 'Letter needed', 'Note enough',
       'Ready', 'Gifts missing a fund', 'No gifts in the year', 'Not late yet', 'Chase', 'Final notice', 'Propose write-off', 'Closed', 'Contact today', 'Wait one more cycle',
       'Received', 'Not active', 'Value recorded', 'Basis missing', 'Wait', 'Merge', 'Keep both', 'Keep']
CKB = ['Save', 'Fix the donor', 'Fix the fund', 'Check the amount', 'Chase batches', 'Print statements', 'Fix first', 'On schedule', 'Days behind', 'Nothing overdue',
       'Counts toward cash forecast', 'Base growing', 'Base flat', 'Base shrinking', 'Ask donors', 'Active', 'Lapsing', 'Lapsed', 'No gift yet', 'Healthy', 'Fix rows',
       'Add the donor', 'Pick a fund', 'Confirm or delete one', 'Check the bank slip', 'Chase now', 'Send request', 'merge into', 'Widen the list', 'Nothing to chase']
assert len(CKA) <= 30 and len(CKB) <= 30 and not set(CKA) & set(CKB)

lists = [
    L('fund', 'Fund', P(FUND_L)), L('campaign', 'Campaign', P(CAMPAIGN_L)), L('appeal', 'Appeal', P(APPEALS)), L('channel', 'Channel', P(CHANNELS)), L('method', 'Method', P(METHODS)),
    L('gtype', 'Gift type', P(GIFT_TYPES)), L('dtype', 'Donor type', P(DONOR_TYPES)), L('dstatus', 'Donor status', P(DONOR_STATUS)), L('pref', 'Contact preference', P(CONTACT_PREFS)),
    L('fundkind', 'Fund restriction', P(FUND_KINDS)), L('plstatus', 'Pledge status', P(PLEDGE_STATUS)), L('instatus', 'Instalment status', P(INSTALMENT_STATUS)),
    L('recstatus', 'Recurring status', P(RECUR_STATUS)), L('ikind', 'In-kind kind', P(INKIND_TYPES)), L('basis', 'Value basis', P(BASIS)), L('mstatus', 'Match status', P(MATCH_STATUS)),
    L('batch', 'Batch status', P(BATCH_STATUS)), L('wday', 'Weekday', P(WEEKDAYS)), L('cka', 'Check result A', P(CKA)), L('ckb', 'Check result B', P(CKB)),
]
assert len(lists) <= 20
_M = {'fund': K(FUND_L), 'campaign': K(CAMPAIGN_L), 'appeal': K(APPEALS), 'channel': K(CHANNELS), 'method': K(METHODS), 'gtype': K(GIFT_TYPES), 'dtype': K(DONOR_TYPES),
      'dstatus': K(DONOR_STATUS), 'pref': K(CONTACT_PREFS), 'fundkind': K(FUND_KINDS), 'plstatus': K(PLEDGE_STATUS), 'instatus': K(INSTALMENT_STATUS), 'recstatus': K(RECUR_STATUS),
      'ikind': K(INKIND_TYPES), 'basis': K(BASIS), 'mstatus': K(MATCH_STATUS), 'batch': K(BATCH_STATUS), 'wday': K(WEEKDAYS), 'cka': K(CKA), 'ckb': K(CKB)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def c(label):
    """token of a check or verdict label (list cka or ckb)"""
    if label in _M['cka']: return tok('cka', label)
    return tok('ckb', label)
