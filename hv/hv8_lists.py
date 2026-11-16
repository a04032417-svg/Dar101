"""HVAC and plumbing contractor suite part 8: label lists shared by data, tables, tools."""
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


TECH6 = TECH_NAMES[:6]
PERIODS = ['Last 3 months', 'Last 12 months', 'Previous 12 months']
SRC_KINDS = ['Paid', 'Reward', 'Own list']
BANDS = ['Overdue', 'Red, within 30 days', 'Amber, within 60 days', 'Green, later', 'Renewed']
MEASURES = ['Job margin, %', 'Net profit, %', 'Technician utilisation, %', 'Callback rate, shop, %', 'Callback rate, highest technician, %', 'Close rate, %',
            'Margin of the watched job type, %', 'Open balance over 60 days, amount', 'Agreement renewal rate, %', 'Tune-up visits done in the window, %',
            'Cash after the next big bill, amount', 'Cash cover, months of fixed costs']
ACT_OWNERS = ['Owner', 'Office manager', 'Lead HVAC tech', 'Install crew lead', 'Accountant']
RN_STATUS = ['Open', 'Renewed']
base_lists = [
    L('tech', 'Technician', P(TECH6)), L('source', 'Lead source', P(SOURCES)), L('jobtype', 'Job type', P(JOB_TYPES)), L('calltype', 'Call type', P(CALL_TYPES)),
    L('calloutcome', 'Call outcome', P(CALL_OUTCOMES)), L('jobkind', 'Job kind', P(JOB_KINDS)), L('jobstatus', 'Job status', P(JOB_STATUS)), L('srckind', 'Source kind', P(SRC_KINDS)),
    L('renewal', 'Renewal item', P(RENEWAL_KINDS)), L('rnstatus', 'Renewal status', P(RN_STATUS)), L('band', 'Renewal band', P(BANDS)), L('period', 'Period', P(PERIODS)),
    L('measure', 'Scorecard measure', P(MEASURES)), L('actowner', 'Action owner', P(ACT_OWNERS)),
]
_M = {'tech': K(TECH6), 'source': K(SOURCES), 'jobtype': K(JOB_TYPES), 'calltype': K(CALL_TYPES), 'calloutcome': K(CALL_OUTCOMES), 'jobkind': K(JOB_KINDS), 'jobstatus': K(JOB_STATUS),
      'srckind': K(SRC_KINDS), 'renewal': K(RENEWAL_KINDS), 'rnstatus': K(RN_STATUS), 'band': K(BANDS), 'period': K(PERIODS), 'measure': K(MEASURES), 'actowner': K(ACT_OWNERS)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula

# ---- labels that formulas return: registered on first use, split in lists of at most 30 values
CKL, CKK = [], {}
def ck(label):
    if label not in CKK:
        k = re.sub(r'[^a-z0-9]+', '_', label.lower()).strip('_')[:21]
        while k in CKK.values(): k = k[:-1] + 'x'
        CKK[label] = k; CKL.append(label)
    return '{list:ck%d.%s}' % (CKL.index(label) // 30 + 1, CKK[label])
def ck_lists():
    out = []
    for i in range(0, len(CKL), 30):
        out.append(L('ck%d' % (i // 30 + 1), 'Check result %d' % (i // 30 + 1), [(CKK[l], l) for l in CKL[i:i + 30]]))
    return out
