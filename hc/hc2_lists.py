"""Home care suite part 2 (Schedule, Matching and Cover): label lists."""
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


OPEN_STATUS = ['Open', 'Offered', 'Filled', 'Not filled']
CLIENT_LANGS = ['English', 'Hindi', 'Portuguese', 'Tagalog', 'Polish', 'Arabic']
CHK = ['Within limit', 'Over own limit', 'Over the line', 'Day off kept', 'Long run', 'No day off', 'Steady', 'Watch', 'Break', 'Rest kept', 'Short rest', 'Urgent', 'Soon', 'Later', 'Closed',
       'On target', 'Below target']
VERD = ['Safe', 'Overtime', 'Over limit', 'Phone first', 'No one is free', 'Use regular hours', 'Use overtime', 'Pay the premium', 'Strong match', 'Possible match', 'Weak match', 'Normal', 'Talk',
        'Cost is up', 'Cost is down', 'Cost is steady', 'On track', 'Behind', 'Even', 'Uneven', 'Pool is enough', 'Add standby', 'Room to take it', 'Short of hours', 'Enough volunteers',
        'Short of volunteers', 'Phone now', 'Cover is tight']
assert len(CHK) <= 30 and len(VERD) <= 30
lists = [L('svc', 'Service', P(SERVICES)), L('band', 'Time band', P(BANDS)), L('area', 'Area', P(AREAS)), L('wday', 'Weekday', P(WEEKDAYS)), L('emp', 'Employment type', P(EMPLOYMENT)),
         L('avail', 'Availability', P(AVAILABILITY)), L('cover', 'Cover type', P(COVER_KINDS)), L('vstatus', 'Visit status', P(VISIT_STATUS)), L('calloff', 'Call-off reason', P(CALLOFF_REASONS)),
         L('timeoff', 'Time off kind', P(TIMEOFF_KINDS)), L('cgstatus', 'Caregiver status', P(CAREGIVER_STATUS)), L('clstatus', 'Client status', P(CLIENT_STATUS)), L('lang', 'Language', P(LANGUAGES)),
         L('clang', 'Client language', P(CLIENT_LANGS)), L('leave', 'Leave reason', P(LEAVE_REASONS)), L('recsrc', 'Recruiting source', P(REC_SOURCES)), L('ostatus', 'Open shift status', P(OPEN_STATUS)),
         L('chk', 'Check result', P(CHK)), L('verd', 'Decision', P(VERD))]
assert len(lists) <= 20
_M = {'svc': K(SERVICES), 'band': K(BANDS), 'area': K(AREAS), 'wday': K(WEEKDAYS), 'emp': K(EMPLOYMENT), 'avail': K(AVAILABILITY), 'cover': K(COVER_KINDS), 'vstatus': K(VISIT_STATUS),
      'calloff': K(CALLOFF_REASONS), 'timeoff': K(TIMEOFF_KINDS), 'cgstatus': K(CAREGIVER_STATUS), 'clstatus': K(CLIENT_STATUS), 'lang': K(LANGUAGES), 'clang': K(CLIENT_LANGS), 'leave': K(LEAVE_REASONS),
      'recsrc': K(REC_SOURCES), 'ostatus': K(OPEN_STATUS), 'chk': K(CHK), 'verd': K(VERD)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ck(label): return tok('chk', label)
def vd(label): return tok('verd', label)
