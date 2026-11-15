"""Short-term rental host suite part 3 (Occupancy, ADR and RevPAR): label lists shared by data, tables, tools."""
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


WDAY = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
BAND = ['Same week', 'One to two weeks', 'Two to four weeks', 'One to three months', 'Over three months']
STAY = ['One night', 'Two nights', 'Three to four nights', 'Five to seven nights', 'Over seven nights']
BREASON = ['Owner stay', 'Repair', 'Deep clean', 'Renovation', 'Photo shoot', 'Personal use', 'Inspection']
# labels that formulas return (never typed text inside a formula)
CKA = ['Ahead of pace', 'On pace', 'Behind pace', 'Above target', 'On target', 'Below target', 'Above market', 'Fair share', 'Below market', 'Strong rating', 'Good rating',
       'Weak rating', 'Poor rating', 'Done', 'Overdue', 'Due soon', 'Open', 'Gap filled', 'Gap missed', 'Growing', 'Flat', 'Falling', 'Healthy unit', 'Watch unit', 'Weak unit',
       'Under minimum', 'Meets minimum', 'Block ended', 'Blocked now', 'Block ahead']
CKB = ['Strong night', 'Normal night', 'Weak night', 'Main channel', 'Minor channel', 'Long block', 'Short block', 'Goal reached', 'Goal in reach', 'Goal far away',
       'Review current', 'Review due', 'Event week', 'Ordinary week', 'Revenue up', 'Revenue down', 'Nights up', 'Nights down', 'Rate above base', 'Rate below base', 'Rate at base',
       'Peak month', 'Low month', 'Mid month', 'Occupancy leads', 'Occupancy lags', 'Rate leads', 'Rate lags', 'Top rank', 'Bottom rank']
CK2 = ['Ahead of target', 'On the target', 'Behind target', 'Raise the price', 'Hold the price', 'Lower the price', 'Cut is worth it', 'Cut loses money', 'Goal is realistic',
       'Goal is a stretch', 'Goal is unrealistic', 'Fair share of the market', 'Ahead of the market', 'Behind the market', 'Open dates earlier', 'Keep the window', 'Shorten the window',
       'Fill the weekday nights', 'Weekends are weak', 'Evenly booked', 'Healthy unit', 'Watch the unit', 'Weak unit', 'Unit A is stronger', 'Unit B is stronger', 'Units are level',
       'Growth comes from rate', 'Growth comes from nights', 'Both fell', 'Block is costly']
CAUSE = ['Price too high', 'Weak reviews', 'Late bookings', 'Short booking window', 'Too few weekday nights', 'Unit is healthy']
FIX = ['Lower the rate on weekdays', 'Fix the cleaning and the complaints', 'Open dates further ahead', 'Cut the minimum stay', 'Add midweek offers', 'Keep the current plan']
CK3 = ['Occupancy', 'ADR', 'Rating', 'Margin', 'Block is acceptable', 'Pace is fine']
RBAND = ['Strong rating', 'Good rating', 'Weak rating', 'Poor rating']
assert len(CKA) <= 30 and len(CKB) <= 30 and len(CK2) <= 30

lists = [
    L('role', 'Role', P(ROLES)), L('team', 'Team', P(TEAMS)), L('yn', 'Yes or no', P(YESNO)), L('utype', 'Unit type', P(UNIT_TYPES)), L('city', 'City', P(CITIES)), L('chan', 'Booking channel', P(CHANNELS)),
    L('bstatus', 'Booking status', P(BOOKING_STATUS)), L('season', 'Season', P(SEASONS)), L('wday', 'Weekday', P(WDAY)), L('band', 'Lead time band', P(BAND)), L('stay', 'Stay length', P(STAY)),
    L('breason', 'Block reason', P(BREASON)), L('cause', 'Likely cause', P(CAUSE)), L('fix', 'Suggested fix', P(FIX)),
    L('ck3', 'Calculator part', P(CK3)), L('cka', 'Check result A', P(CKA)), L('ckb', 'Check result B', P(CKB)), L('ck2', 'Calculator verdict', P(CK2)),
]
_M = {'role': K(ROLES), 'team': K(TEAMS), 'yn': K(YESNO), 'utype': K(UNIT_TYPES), 'city': K(CITIES), 'chan': K(CHANNELS), 'bstatus': K(BOOKING_STATUS), 'season': K(SEASONS), 'wday': K(WDAY),
      'band': K(BAND), 'stay': K(STAY), 'breason': K(BREASON), 'cause': K(CAUSE), 'fix': K(FIX), 'ck3': K(CK3), 'cka': K(CKA), 'ckb': K(CKB), 'ck2': K(CK2)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def ca(label): return tok('cka', label)
def cb(label): return tok('ckb', label)
def ck2(label): return tok('ck2', label)
def ck3(label): return tok('ck3', label)
