"""HVAC and plumbing suite part 2: label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/claude/work/hv')
from hv_core import *
from lib import L, LV


def P(labels):
    out, seen = [], set()
    for k, l in pairs(labels):
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


TECH6 = TECH_NAMES[:6]
EST_JT = ['Furnace replacement', 'Air conditioner replacement', 'Heat pump install', 'Water heater replacement', 'Repipe']
PERIODS = ['Last 30 days', 'Last 90 days', 'Last 12 months', 'Year before']
SUPPLIERS = ['Your parts counter', 'Your equipment supplier']
QUOTE_OUT = ['Booked', 'Estimate needed', 'Thinking about it', 'Went elsewhere']
SAY = ['Our fixed price for this job is', 'Prices include parts and labour', 'The diagnostic fee is', 'It is credited if you go ahead',
       'A deposit holds your date', 'Please check the current price', 'The member price is', 'Three options are available']
CKA = ['On target', 'Watch', 'Under target', 'Follow-up set', 'No follow-up date', 'Follow-up overdue', 'Due today', 'Decided',
       'Above floor', 'Under floor', 'Meets target', 'Below target', 'Quick', 'Slow', 'On time', 'Late']
CK2 = ['Raise price', 'Hold', 'Fine', 'Offer financing', 'Limit to larger jobs', 'Lead with good', 'Lead with better', 'Lead with best',
       'Raise the fee', 'Hold the fee', 'Lower the fee', 'Fix price first', 'Fix timing first', 'Fix second opinion first', 'Fix no answer first', 'Fix financing first',
       'Raise prices now', 'Planned rise covers costs', 'Planned rise is not enough', 'Call today', 'Nothing waiting', 'Limit the discount', 'Member prices are safe',
       'Turnaround on target', 'Turnaround too slow', 'Rise pays off', 'Rise loses profit', 'Close rate on target', 'Close rate below target', 'Mix is healthy']
assert len(CKA) <= 30 and len(CK2) <= 30
JT_LABELS = JOB_TYPES

lists = [
    L('tech', 'Technician', P(TECH6)), L('jobtype', 'Job type', P(JOB_TYPES)), L('estjt', 'Estimate job type', P(EST_JT)), L('jobkind', 'Job kind', P(JOB_KINDS)),
    L('trade', 'Trade', P(TRADES)), L('tier', 'Option', P(TIERS)), L('optchosen', 'Option chosen', P(OPTION_CHOSEN)), L('estoutcome', 'Estimate outcome', P(EST_OUTCOME)),
    L('estlost', 'Lost reason', P(EST_LOST)), L('partcat', 'Part category', P(PART_CATEGORIES)), L('supplier', 'Supplier', P(SUPPLIERS)), L('sitetype', 'Site type', P(SITE_TYPES)),
    L('area', 'Area', P(AREAS)), L('van', 'Van', P(VAN_NAMES)), L('period', 'Period', P(PERIODS)), L('quoteout', 'Quote outcome', P(QUOTE_OUT)),
    L('say', 'Phone wording', P(SAY)), L('cka', 'Check result', P(CKA)), L('ck2', 'Verdict', P(CK2)),
]
_M = {'tech': K(TECH6), 'jobtype': K(JOB_TYPES), 'estjt': K(EST_JT), 'jobkind': K(JOB_KINDS), 'trade': K(TRADES), 'tier': K(TIERS), 'optchosen': K(OPTION_CHOSEN), 'estoutcome': K(EST_OUTCOME),
      'estlost': K(EST_LOST), 'partcat': K(PART_CATEGORIES), 'supplier': K(SUPPLIERS), 'sitetype': K(SITE_TYPES), 'area': K(AREAS), 'van': K(VAN_NAMES), 'period': K(PERIODS),
      'quoteout': K(QUOTE_OUT), 'say': K(SAY), 'cka': K(CKA), 'ck2': K(CK2)}


def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])
def ca(label): return tok('cka', label)
def c2(label): return tok('ck2', label)
