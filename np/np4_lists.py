"""Nonprofit suite part 4 (Events and Campaigns): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from np_core import *
from lib import L, LV


def P(labels):
    out, seen = [], set()
    for k, l in pairs(labels):
        if not k[:1].isalpha(): k = 'n' + k
        k = k[:21]
        n_ = 0
        while k in seen:
            n_ += 1; k = k[:19] + 'x%d' % n_
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


EV_SRC = event_rows()
def ev_name(e): return '%s %s' % (e['event'], e['year'])
EV_NAMES = [ev_name(e) for e in EV_SRC] + ['Fun Run 2027']          # EV-12, a planned fun run, pads the table to the 12 rows the depth gate needs
CP_SRC = campaign_rows()
CP_NAMES = ['%s %s' % (c_['campaign'], c_['year']) for c_ in CP_SRC]
GIFT_T = ['One-time', 'Pledge payment', 'Matching gift', 'Event gift']
ECAT = ['Venue and hall', 'Catering and drinks', 'Stage, sound and lighting', 'Entertainment', 'Decor and flowers', 'Printing and mail', 'Insurance and permits', 'Online ads and fees', 'Merchandise and route']
SNEXT = ['Renewal meeting', 'Collect the payment', 'Deliver the last benefits', 'Ask again next season']
WEEKS = ['Week %d' % i for i in range(1, 10)]
EWORK = ['Planning and tickets', 'Sponsors and invitations', 'Auction and printing', 'Set-up and decor', 'Guest check-in', 'Event floor and service', 'Clear-up', 'Thank-yous and report']
LINES = ['Ticket money', 'Sponsor money', 'Auction income', 'Gifts on the night and appeal', 'Total raised'] + ECAT + ['Total costs', 'Net raised', 'Cost per dollar', 'Guests', 'Net per guest', 'Staff hours', 'Volunteer hours']
CKA = ['Good result', 'Over cost by', 'Below last year', 'Not held yet', 'On pace', 'Behind by', 'Ahead', 'Closed', 'Delivered', 'Overdue', 'Due this month', 'Later', 'Call this week', 'Renew', 'Let go', 'Renewed',
       'Run', 'Run smaller', 'Do not run', 'Grow', 'Hold', 'Retire', 'Keep item', 'Lower start', 'Drop item', 'Add a fair value', 'Running', 'Coming']
CKB = ['Gift part', 'Cut', 'next year', 'On budget', 'Within the setting', 'Above the setting by', 'Better', 'Same', 'Worse', 'Repeat', 'Change the cost line', 'Change ticket sales', 'Change the sponsor ask',
       'Deliver', 'benefits this month', 'Up to date', 'Raise the level price to', 'Fine', 'Likely to finish at', '(your estimate)', 'Collect', 'pledged', 'Nothing pledged', 'Need', 'gifts by the end date',
       'Goal reached', 'Sell', 'more tickets or add', 'sponsors', 'Do more of']
CKC = ['Do less of', 'Covered', 'Over by', 'Short by', 'Choose an event', 'No ticket sales']
assert len(CKA) <= 30 and len(CKB) <= 30

lists = [
    L('ekind', 'Event kind', P(EVENT_KINDS)), L('estatus', 'Event status', P(EVENT_STATUS)), L('ticket', 'Ticket type', P(TICKET_TYPES)), L('level', 'Sponsor level', P(SPONSOR_LEVELS)),
    L('sstatus', 'Sponsor status', P(SPONSOR_STATUS)), L('snext', 'Sponsor next step', P(SNEXT)), L('auction', 'Auction status', P(AUCTION_STATUS)), L('ecat', 'Event cost category', P(ECAT)),
    L('campaign', 'Campaign', P(CAMPAIGNS)), L('appeal', 'Appeal', P(APPEALS)), L('gtype', 'Gift type', P(GIFT_T)), L('wk', 'Campaign week', P(WEEKS)), L('ework', 'Event work area', P(EWORK)),
    L('lines', 'Result line', P(LINES)), L('channel', 'Channel', P(CHANNELS)), L('evpick', 'Event', P(EV_NAMES)), L('cpick', 'Campaign and year', P(CP_NAMES)),
    L('ck1', 'Verdict A', P(CKA)), L('ck2', 'Verdict B', P(CKB)), L('ck3', 'Verdict C', P(CKC)),
]
assert len(lists) <= 20
_M = {l['key']: {v['label']: v['key'] for v in l['values']} for l in lists}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ca(label): return tok('ck1', label)
def cb(label): return tok('ck2', label)
def cc(label): return tok('ck3', label)
