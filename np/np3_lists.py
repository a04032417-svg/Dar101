"""Nonprofit suite part 3 (Grants and Restricted Funds): label lists shared by data, tables and tools."""
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


# Part 3 widens two reference lists so the grant pages read like a real grant desk (see the report):
# six funder types (the private and government groups split) and seven stages (an awarded grant whose end date has passed is "Closed out").
FTYPES = ['Private foundation', 'Family foundation', 'Community foundation', 'Corporate giving', 'Local government', 'State government']
STAGES = ['Prospect', 'Letter of inquiry', 'Application', 'Awarded', 'Closed out', 'Declined', 'Withdrawn']
OPEN_STAGES = ['Prospect', 'Letter of inquiry', 'Application']
SPROGRAMS = PROGRAMS + ['Shared']
GPROGRAMS = PROGRAMS + ['General operating']
TIME_KINDS = ['Grant', 'Program', 'Management', 'Fundraising']
SCENARIOS = ['Base', 'Best', 'Worst']
CAL_KINDS = ['Instalment', 'Report']
PERIODS = ['All decisions', 'Last 12 months']
GCATS = ['Staff pay', 'Food purchases', 'Meals contract', 'Program supplies']
STAFF_NAMES = [s['name'] for s in staff]

CK1 = ['Received on time', 'Received late', 'Open and late', 'Open, not due yet', 'Submitted on time', 'Submitted late',
       'Done', 'Late', 'Due this week', 'Coming up', 'On track', 'Underspending', 'Overspending', 'Closed',
       'Over budget', 'Under budget', 'Within budget', 'OK', 'Near zero', 'Below zero', 'Totals 100%', 'Short of 100%', 'Over 100%',
       'Healthy', 'Below the setting', 'Too few decisions', 'Above your average', 'Below your average', 'Near your average']
CK2 = ['Write now', 'Start', 'On time', 'Covered', 'Short', 'Pipeline covers the grant budget', 'Pipeline covers part of the grant budget', 'Pipeline is thin',
       'Apply to more grants', 'On pace for the goal', 'Quarter is short', 'All quarters covered', 'Late items', 'Clear', 'Chase', 'Wait',
       'Raise spend', 'Ask for an extension', 'No rescue needed', 'Cut spending', 'Fine', 'Move money between lines', 'No move needed',
       'Charge the fund', 'Charge General Fund', 'Release this month', 'Nothing to release', 'Cash looks good but free money is low', 'Free money is low']
CK3 = ['Over-charged', 'Under-charged', 'Apply', 'Apply if time', 'Skip', 'Worth it', 'Not worth it at this win rate', 'Fund covers it', 'Fund is short',
       'Within the limit', 'Overspend limit passed', 'Raise the pace']
assert len(CK1) <= 30 and len(CK2) <= 30 and len(CK3) <= 30

lists = [
    L('ftype', 'Funder type', P(FTYPES)), L('gstage', 'Grant stage', P(STAGES)), L('gpay', 'Payment status', P(GRANT_PAY_STATUS)), L('rkind', 'Report kind', P(REPORT_KINDS)),
    L('rstatus', 'Report status', P(REPORT_STATUS)), L('gline', 'Budget line', P(GRANT_LINES)), L('gcat', 'Spending category', P(GCATS)), L('fund', 'Fund', P(fund_names := [f['fund'] for f in funds])),
    L('fundkind', 'Fund restriction', P(FUND_KINDS)), L('program', 'Program', P(PROGRAMS)), L('gprogram', 'Program or general operating', P(GPROGRAMS)), L('sprogram', 'Program or shared', P(SPROGRAMS)), L('staff', 'Staff member', P(STAFF_NAMES)),
    L('tkind', 'Time target', P(TIME_KINDS)), L('scenario', 'Scenario', P(SCENARIOS)), L('ckind', 'Calendar item', P(CAL_KINDS)),
    L('period', 'Period', P(PERIODS)), L('ck1', 'Check result', P(CK1)), L('ck2', 'Verdict A', P(CK2)), L('ck3', 'Verdict B', P(CK3)),
]
assert len(lists) <= 20
_M = {'ftype': K(FTYPES), 'gstage': K(STAGES), 'gpay': K(GRANT_PAY_STATUS), 'rkind': K(REPORT_KINDS), 'rstatus': K(REPORT_STATUS), 'gline': K(GRANT_LINES), 'gcat': K(GCATS),
      'fund': K(fund_names), 'fundkind': K(FUND_KINDS), 'program': K(PROGRAMS), 'sprogram': K(SPROGRAMS), 'gprogram': K(GPROGRAMS), 'staff': K(STAFF_NAMES), 'tkind': K(TIME_KINDS),
      'scenario': K(SCENARIOS), 'ckind': K(CAL_KINDS), 'period': K(PERIODS), 'ck1': K(CK1), 'ck2': K(CK2), 'ck3': K(CK3)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def c1(label): return tok('ck1', label)
def c2(label): return tok('ck2', label)
def c3(label): return tok('ck3', label)
