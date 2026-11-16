"""Nonprofit suite part 2 (Donor Growth, Retention and Major Gifts): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from np_core import *
from lib import L, LV


def P(labels):
    out, seen = [], set()
    for k, l in pairs(labels):
        if not k[:1].isalpha(): k = 'n' + k
        k = k[:21]
        base, i = k, 1
        while k in seen: i += 1; k = base[:21 - len(str(i))] + str(i)
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


FUND_NAMES = [f['fund'] for f in funds]
DGROUP = ['All donors'] + DONOR_TYPES
OWNERS = ['Grace Adeyemi', 'Mateus Oliveira', 'Michael Brandt', 'Sunita Rao']
YR = ['Two years ago', 'Last year', 'This year']
YR2 = ['Last year', 'This year']
GSTATE = ['Retained', 'New', 'Recaptured', 'Lapsed', 'Not giving']
GFLAG = ['Upgraded', 'Downgraded', 'Steady', 'No comparison']
BANDS = ['Under 25', '25 to 49', '50 to 99', '100 to 149', '150 to 249', '250 to 499', '500 to 999', '1,000 to 2,499', '2,500 to 4,999', '5,000 to 9,999', '10,000 to 24,999', '25,000 and over']
BAND_LIMITS = [(0.01, 25), (25, 50), (50, 100), (100, 150), (150, 250), (250, 500), (500, 1000), (1000, 2500), (2500, 5000), (5000, 10000), (10000, 25000), (25000, 99999999)]
CAPBANDS = ['Under 5,000', '5,000 to 9,999', '10,000 to 19,999', '20,000 and over']
VA = ['Call', 'Write', 'Let go', 'Ask now', 'Wait', 'Call this month', 'Note', 'Worth a campaign', 'Low value', 'Act today', 'Reschedule', 'On schedule', 'Ask', 'Cultivate', 'Pause',
      'Closed', 'Keep', 'Fix', 'Stop', 'Spread out', 'Watch', 'At risk', 'Covered', 'Gap', 'Steady', 'Falling', 'Holding', 'Second-gift plan needed']
VB = ['Better than last year', 'Same as last year', 'Worse than last year', 'Second gift in time', 'Second gift late', 'Waiting for second gift', 'No second gift', 'Above own last year',
      'Below own last year', 'Level with last year', 'Donors up', 'Donors flat', 'Donors down', 'Money up', 'Money flat', 'Money down', 'A few large gifts lift the average', 'Spread evenly',
      'Send the second-gift ask', 'Send a thank-you only', 'Need more second gifts', 'Second-gift target met', 'Pipeline covers the goal', 'Pipeline short of the goal',
      'Shift effort to Online form', 'Shift effort to Mail', 'Shift effort to Event', 'Shift effort to In person', 'Shift effort to Payroll giving']
STORY = ['More donors, giving more', 'More donors, giving the same', 'More donors, giving less', 'Same donors, giving more', 'Same donors, giving the same',
         'Same donors, giving less', 'Fewer donors, giving more', 'Fewer donors, giving the same', 'Fewer donors, giving less']
VC = STORY + ['Retention above your target', 'Retention below your target', 'Retention level with your target', 'Top 5 give more than a third', 'Giving is spread out']

lists = [
    L('dtype', 'Donor type', P(DONOR_TYPES)), L('dgroup', 'Donor group', P(DGROUP)), L('dstatus', 'Donor status', P(DONOR_STATUS)), L('pref', 'Contact preference', P(CONTACT_PREFS)),
    L('channel', 'Channel', P(CHANNELS)), L('gtype', 'Gift type', P(GIFT_TYPES)), L('campaign', 'Campaign', P(CAMPAIGNS)), L('appeal', 'Appeal', P(APPEALS)), L('fund', 'Fund', P(FUND_NAMES)),
    L('pstage', 'Pipeline stage', P(PIPELINE_STAGES)), L('owner', 'Prospect owner', P(OWNERS)), L('yr', 'Year', P(YR)), L('yr2', 'Year to check', P(YR2)), L('gstate', 'Donor state this year', P(GSTATE)),
    L('gflag', 'Giving change', P(GFLAG)), L('band', 'Giving size band', P(BANDS)), L('capband', 'Capacity band', P(CAPBANDS)), L('va', 'Decision', P(VA)), L('vb', 'Check result', P(VB)),
    L('vc', 'Story and watch result', P(VC)),
]
assert len(lists) <= 20
_M = {'dtype': K(DONOR_TYPES), 'dgroup': K(DGROUP), 'dstatus': K(DONOR_STATUS), 'pref': K(CONTACT_PREFS), 'channel': K(CHANNELS), 'gtype': K(GIFT_TYPES), 'campaign': K(CAMPAIGNS), 'appeal': K(APPEALS),
      'fund': K(FUND_NAMES), 'pstage': K(PIPELINE_STAGES), 'owner': K(OWNERS), 'yr': K(YR), 'yr2': K(YR2), 'gstate': K(GSTATE), 'gflag': K(GFLAG), 'band': K(BANDS), 'capband': K(CAPBANDS),
      'va': K(VA), 'vb': K(VB), 'vc': K(VC)}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def va(label): return tok('va', label)
def vb(label): return tok('vb', label)
def vc(label): return tok('vc', label)
