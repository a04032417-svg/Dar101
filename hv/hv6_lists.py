"""HVAC and plumbing contractor suite part 6: label lists shared by data, tables, tools."""
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


LAPSE_REASONS = ['Price too high', 'Moved away', 'Service not as expected', 'Switched provider', 'Equipment replaced', 'No reason given']
AGE_BANDS = ['Up to 5 years', 'From 6 to 10 years', 'From 11 to 15 years', 'Over 15 years']
CHANNELS = ['Text message', 'Mailed letter', 'Phone call']
PERIODS = ['Last 12 months', 'Previous 12 months']
RENEW_OUT = ['Renewed', 'Lapsed', 'Open']
TECH6 = TECH_NAMES[:6]
base_lists = [
    L('tech', 'Technician', P(TECH6)), L('area', 'Area', P(AREAS)), L('sitetype', 'Site type', P(SITE_TYPES)), L('equiptype', 'Equipment type', P(EQUIP_TYPES)), L('fuel', 'Fuel', P(FUELS)),
    L('plan', 'Agreement plan', P(PLAN_NAMES)), L('agrstatus', 'Agreement status', P(AGREEMENT_STATUS)), L('visitseason', 'Tune-up window', P(VISIT_SEASONS)), L('visitstatus', 'Visit status', P(VISIT_STATUS)),
    L('renewout', 'Renewal outcome', P(RENEW_OUT)), L('lapsereason', 'Lapse reason', P(LAPSE_REASONS)), L('ageband', 'Equipment age band', P(AGE_BANDS)), L('channel', 'Reminder channel', P(CHANNELS)),
    L('period', 'Period', P(PERIODS)), L('crew', 'Field crew', P(TECH_NAMES)),
]
_M = {'tech': K(TECH6), 'area': K(AREAS), 'sitetype': K(SITE_TYPES), 'equiptype': K(EQUIP_TYPES), 'fuel': K(FUELS), 'plan': K(PLAN_NAMES), 'agrstatus': K(AGREEMENT_STATUS), 'visitseason': K(VISIT_SEASONS),
      'visitstatus': K(VISIT_STATUS), 'renewout': K(RENEW_OUT), 'lapsereason': K(LAPSE_REASONS), 'ageband': K(AGE_BANDS), 'channel': K(CHANNELS), 'period': K(PERIODS), 'crew': K(TECH_NAMES)}
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
