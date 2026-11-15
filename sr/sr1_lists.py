"""Short-term rental host suite part 1: label lists shared by data, tables, tools."""
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


REASON = ['Season change', 'Event week', 'Low demand', 'High demand', 'Competitor rate', 'Gap night fill', 'Last-minute fill', 'Review score', 'Cost increase', 'Weekend lift']
DTRIG = ['Gap night', 'Last minute', 'Weekly stay', 'Monthly stay', 'Returning guest', 'Direct booking', 'Low season', 'Early booking']
WDAY = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
EXRES = ['Running', 'Rate worked', 'Rate too high', 'Rate too low', 'No clear result']
BAND = ['Same week', 'One to two weeks', 'Two to four weeks', 'One to three months', 'Over three months']
DAYTYPE = ['Sunday to Thursday', 'Friday or Saturday']
# labels that formulas return (never typed text inside a formula)
CKA = ['On suggested rate', 'Below suggested rate', 'Above suggested rate', 'Fully booked', 'Few free nights', 'Many free nights', 'Past event', 'Happening now', 'Coming soon', 'Later',
       'Priced above us', 'Priced below us', 'Close to our rate', 'Filled', 'Missed', 'Open', 'Above break-even', 'Below break-even', 'Offer active', 'Offer ended', 'Offer not started',
       'Lift achieved', 'Lift missed', 'Not a weekend', 'Margin on target', 'Margin too thin', 'Test running', 'Test ended', 'Gap nights allowed', 'Gap nights blocked']
CKB = ['Busy check-in day', 'Quiet check-in day', 'Normal check-in day', 'Rate raised', 'Rate cut', 'Rate unchanged', 'Very late fill', 'Late fill', 'Early fill', 'Rule is on', 'Rule is off',
       'Review due', 'Review planned', 'Rate above base', 'Rate at base', 'Rate below base', 'Below target ADR', 'On target ADR']
CK2 = ['Raise the rate', 'Hold the rate', 'Lower the rate', 'Offer the discount', 'Hold the price', 'Discount adds revenue', 'Discount costs revenue', 'Accept the stay', 'Keep the minimum',
       'Shorten the minimum', 'Raise the fee', 'Fee is fair', 'Above break-even', 'Below break-even', 'Priced above comparables', 'Priced below comparables', 'Priced in line',
       'Direct is cheaper for the guest', 'Direct earns the host more', 'Rate change adds profit', 'Rate change loses profit', 'Rate is on target', 'Rate is below target', 'Event rate applies']
assert len(CKA) <= 30 and len(CKB) <= 30 and len(CK2) <= 30

lists = [
    L('role', 'Role', P(ROLES)), L('team', 'Team', P(TEAMS)), L('yn', 'Yes or no', P(YESNO)), L('utype', 'Unit type', P(UNIT_TYPES)), L('city', 'City', P(CITIES)), L('chan', 'Booking channel', P(CHANNELS)),
    L('bstatus', 'Booking status', P(BOOKING_STATUS)), L('season', 'Season', P(SEASONS)), L('reason', 'Rate change reason', P(REASON)), L('dtrig', 'Discount trigger', P(DTRIG)),
    L('wday', 'Weekday', P(WDAY)), L('expres', 'Test result', P(EXRES)), L('band', 'Lead time band', P(BAND)), L('daytype', 'Night type', P(DAYTYPE)),
    L('cka', 'Check result A', P(CKA)), L('ckb', 'Check result B', P(CKB)), L('ck2', 'Calculator verdict', P(CK2)),
]
_M = {'role': K(ROLES), 'team': K(TEAMS), 'yn': K(YESNO), 'utype': K(UNIT_TYPES), 'city': K(CITIES), 'chan': K(CHANNELS), 'bstatus': K(BOOKING_STATUS), 'season': K(SEASONS), 'reason': K(REASON),
      'dtrig': K(DTRIG), 'wday': K(WDAY), 'expres': K(EXRES), 'band': K(BAND), 'daytype': K(DAYTYPE), 'cka': K(CKA), 'ckb': K(CKB), 'ck2': K(CK2)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def ca(label): return tok('cka', label)
def cb(label): return tok('ckb', label)
def ck2(label): return tok('ck2', label)
