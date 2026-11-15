"""Short-term rental host suite part 6: label lists shared by data, tables, tools. Check lists fill themselves from the labels the formulas use."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sr_core import *
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


STARS = ['One star', 'Two stars', 'Three stars', 'Four stars', 'Five stars']
COUNTRIES = ['United States', 'Portugal', 'Germany', 'United Kingdom', 'France', 'Spain', 'Brazil', 'Netherlands', 'India', 'Poland', 'Canada', 'Australia']
SEVERITY = ['Minor', 'Moderate', 'Serious']
CACT = ['Apology', 'Partial refund', 'Credit for next stay', 'Fixed on site', 'Moved to another unit', 'No action']
AMETHOD = ['Smart lock code', 'Key box', 'Meeting in person', 'Neighbour handover']
CISSUE = ['No issue', 'Late arrival', 'Code did not work', 'Key not found', 'Unit not ready', 'Could not find the address']
ECKIND = ['Early check-in', 'Late checkout']

# check lists: labels are registered when a formula asks for a token (never typed text inside a formula)
CK = {'cka': [], 'ckb': [], 'ckc': [], 'ck2': []}
CKN = {'cka': 'Check result A', 'ckb': 'Check result B', 'ckc': 'Message sentence', 'ck2': 'Calculator verdict'}
_KEYS = {}


CKK = {'cka': {}, 'ckb': {}, 'ckc': {}, 'ck2': {}}


def _reg(lst, label):
    if label not in CK[lst]:
        CK[lst].append(label)
        assert len(CK[lst]) <= 30, (lst, label)
        k = pairs([label])[0][0][:21]
        used = set(CKK[lst].values())
        base, n = k, 1
        while k in used:
            n += 1; k = base[:19] + str(n)
        CKK[lst][label] = k
    return label


def tokx(lst, label):
    _reg(lst, label); return LV(lst, CKK[lst][label])


def ca(l): return tokx('cka', l)
def cb(l): return tokx('ckb', l)
def cc(l): return tokx('ckc', l)
def ck2(l): return tokx('ck2', l)
def cs(l): return tokx('ckc', l)


base_lists = [
    L('role', 'Role', P(ROLES)), L('team', 'Team', P(TEAMS)), L('yn', 'Yes or no', P(YESNO)), L('utype', 'Unit type', P(UNIT_TYPES)), L('city', 'City', P(CITIES)), L('chan', 'Booking channel', P(CHANNELS)),
    L('bstatus', 'Booking status', P(BOOKING_STATUS)), L('rtopic', 'Review topic', P(REVIEW_TOPICS)), L('msgk', 'Message kind', P(MSG_KINDS)), L('stars', 'Stars', P(STARS)),
    L('country', 'Guest country', P(COUNTRIES)), L('sev', 'Severity', P(SEVERITY)), L('cact', 'Complaint action', P(CACT)), L('amethod', 'Access method', P(AMETHOD)),
    L('cissue', 'Check-in issue', P(CISSUE)), L('eckind', 'Early or late', P(ECKIND)),
]
_M = {'role': K(ROLES), 'team': K(TEAMS), 'yn': K(YESNO), 'utype': K(UNIT_TYPES), 'city': K(CITIES), 'chan': K(CHANNELS), 'bstatus': K(BOOKING_STATUS), 'rtopic': K(REVIEW_TOPICS), 'msgk': K(MSG_KINDS),
      'stars': K(STARS), 'country': K(COUNTRIES), 'sev': K(SEVERITY), 'cact': K(CACT), 'amethod': K(AMETHOD), 'cissue': K(CISSUE), 'eckind': K(ECKIND)}


def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula on a fixed list


def check_lists():
    out = []
    for n in ('cka', 'ckb', 'ckc', 'ck2'):
        if CK[n]: out.append(L(n, CKN[n], [(CKK[n][l], l) for l in CK[n]]))
    return out
