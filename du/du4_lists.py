"""Doula Business suite part 4 (On-Call Capacity and Backup Cover): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from du_core import *
from lib import L, LV


def P(labels):
    """pairs() with list keys cut to 21 characters, unique inside the list"""
    out, seen = [], set()
    for k, l in pairs(labels):
        if not k[:1].isalpha(): k = 'n' + k
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


BDOULAS = [d['doula'] for d in doulas if d['cap_births'] > 0]            # the 5 doulas who take births (own on-call windows)
HOLDERS = list(DOULA_NAMES) + list(BACKUP_NAMES)                         # everyone who can take time off (7 doulas + 2 backups)
PHASE = ['Upcoming', 'Open now', 'Closed']
SCEN = ['Base', 'Best', 'Worst']
RULES = ['Flat call-out', 'Share of the birth part', 'Hourly rate']
RBASIS = ['Per week on the rota', 'Per birth attended', 'Share of the birth part', 'Per hour attended', 'Paid when the backup attends']
# labels that table formulas return (a formula never types a word: it points at the list cell)
CK = ['Backup named', 'No backup named', 'Backup overloaded', 'Fine', 'Window closed', 'Not needed', 'Over the limit', 'Within the limit', 'Open', 'Full', 'Over the cap',
      'Not taking births', 'Safe to book', 'Clash', 'Past block', 'Yes', 'Yes with backup booked', 'Decline or waitlist', 'No window needed', 'Backup is enough',
      'Short of backups', 'Backup attended', 'Assigned doula attended', 'Name a backup', 'Up to date']
# verdicts of the tools (part A and part B)
CK2 = ['Over the limit: add cover now', 'Overlaps ahead: check cover', 'No overlap ahead', 'Busiest week has', 'clients on call', 'Fully booked: waitlist only', 'Few months open: sell now',
       'Months open: keep selling', 'Short of backups by', 'All windows covered', 'windows without cover', 'Backup load too high', 'Agency keeps a margin', 'Agency loses on this birth',
       'Clashes with', 'Name this backup:', 'No backup is free: add cover', 'Shorten the window', 'Keep the window', 'Rebalance the rota', 'Rota is balanced',
       'Space this client:', 'No back-to-back due dates', 'Market the quietest month', 'Full: no income left open', 'Name a backup for', 'today', 'All windows have a backup']
CK3 = ['Swap with', 'No swap is free', 'Budget for call-outs:', 'Offer the date to', 'Hold the date', 'Add backup cover for the peak', 'Cover is enough for the peak', 'Nothing opens soon',
       'Ready: every window has a backup', 'Needs a backup before the window opens', 'Backup named for all', 'Quiet: no clash', 'Busy: check cover', 'Cap is full: decline',
       'Room for more clients', 'Backup not needed']
assert len(CK) <= 30 and len(CK2) <= 30 and len(CK3) <= 30

lists = [
    L('role', 'Role', P(ROLES)), L('service', 'Service', P(SERVICES)), L('area', 'Area', P(AREAS)), L('ckind', 'Client kind', P(CLIENT_KINDS)), L('cstatus', 'Client status', P(CLIENT_STATUS)),
    L('package', 'Package', P([p['package'] for p in packages])), L('source', 'Referral source', P(SOURCES)), L('doula', 'Doula', P(DOULA_NAMES)), L('bdoula', 'Birth doula', P(BDOULAS)),
    L('backup', 'Backup doula', P(BACKUP_NAMES)), L('holder', 'Doula or backup', P(HOLDERS)), L('toff', 'Time-off kind', P(TIMEOFF_KINDS)), L('phase', 'Window phase', P(PHASE)),
    L('scen', 'Scenario', P(SCEN)), L('rule', 'Backup pay rule', P(RULES)), L('rbasis', 'Pay basis', P(RBASIS)),
    L('ck', 'Check result', P(CK)), L('ck2', 'Verdict A', P(CK2)), L('ck3', 'Verdict B', P(CK3)),
]
assert len(lists) <= 20
_M = {'role': K(ROLES), 'service': K(SERVICES), 'area': K(AREAS), 'ckind': K(CLIENT_KINDS), 'cstatus': K(CLIENT_STATUS), 'package': K([p['package'] for p in packages]), 'source': K(SOURCES),
      'doula': K(DOULA_NAMES), 'bdoula': K(BDOULAS), 'backup': K(BACKUP_NAMES), 'holder': K(HOLDERS), 'toff': K(TIMEOFF_KINDS), 'phase': K(PHASE), 'scen': K(SCEN), 'rule': K(RULES),
      'rbasis': K(RBASIS), 'ck': K(CK), 'ck2': K(CK2), 'ck3': K(CK3)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def ck(label): return tok('ck', label)
def c2(label): return tok('ck2', label)
def c3(label): return tok('ck3', label)
