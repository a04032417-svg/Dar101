"""HVAC and plumbing contractor suite part 1: label lists shared by data, tables, tools."""
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


DAYPART = ['Business hours', 'After hours']
PERIOD = ['Last 90 days', 'Previous 90 days']
TECH6 = TECH_NAMES[:6]
base_lists = [
    L('tech', 'Technician', P(TECH6)), L('crew', 'Field crew', P(TECH_NAMES)), L('van', 'Van', P(VAN_NAMES)), L('source', 'Lead source', P(SOURCES)), L('calltype', 'Call type', P(CALL_TYPES)),
    L('calloutcome', 'Call outcome', P(CALL_OUTCOMES)), L('answeredby', 'Answered by', P(ANSWERED_BY)), L('jobtype', 'Job type', P(JOB_TYPES)), L('sitetype', 'Site type', P(SITE_TYPES)),
    L('area', 'Area', P(AREAS)), L('wday7', 'Weekday', P(WEEKDAYS7)), L('jobstatus', 'Job status', P(JOB_STATUS)), L('permitstatus', 'Permit status', P(PERMIT_STATUS)),
    L('daypart', 'Time of day', P(DAYPART)), L('period', 'Period', P(PERIOD)), L('trade', 'Trade', P(TRADES)),
]
_M = {'tech': K(TECH6), 'crew': K(TECH_NAMES), 'van': K(VAN_NAMES), 'source': K(SOURCES), 'calltype': K(CALL_TYPES), 'calloutcome': K(CALL_OUTCOMES), 'answeredby': K(ANSWERED_BY),
      'jobtype': K(JOB_TYPES), 'sitetype': K(SITE_TYPES), 'area': K(AREAS), 'wday7': K(WEEKDAYS7), 'jobstatus': K(JOB_STATUS), 'permitstatus': K(PERMIT_STATUS), 'daypart': K(DAYPART),
      'period': K(PERIOD), 'trade': K(TRADES)}
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
