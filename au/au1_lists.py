"""Author and Self-Publisher suite part 1 (Catalogue, Series Plan and Releases): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import L, LV
import au_core as core
from au_core import (TODAY, ago, ahead, iso, to_date, month_start, add_months, team, story, PEN_NAMES, SERIES, GENRES, TITLE_STATUS, FORMATS, EDITION_STATUS, STORES, CURRENCIES,
                     JOB_KINDS, PROMO_KINDS, ROLES, COMPANY, MIN_RELEASE_GAP_DAYS)


def P(labels):
    """pairs() with list keys cut to 21 characters, unique inside the list"""
    out, seen = [], set()
    for k, l in core.pairs(labels):
        if not k[:1].isalpha(): k = 'n' + k
        k = k[:21]
        while k in seen: k = k[:-1] + 'x'
        seen.add(k); out.append((k, l))
    return out


def K(labels): return {l: k for k, l in P(labels)}


PERSON = ['Priya Nandakumar', 'Leopold Brandt', 'Ines Carvalho', 'Tomasz Wrona', 'Amara Oyelaran', 'Gideon Falk', 'Yuki Tanabe', 'Noor Castellan']
CKIND = ['Release', 'Pre-order opens', 'Promotion starts', 'Contractor deadline', 'Planned edition']
WPRIO = ['High', 'Medium', 'Low']
WSTATUS = ['Idea', 'Quoted', 'Booked', 'On hold']
PLANSTATUS = ['Released', 'Pre-order', 'In production', 'Planned']
CHKL = ['Clear', 'Too close to a release', 'Busy week', 'Under the minimum', 'Above the minimum', 'First release', 'Complete', 'Needs fixing', 'Planned, not checked',
       'Price matches', 'Price differs', 'Delivered on time', 'Delivered late', 'Open', 'Open and late', 'Busy month', 'Normal month', 'Identifier missing', 'Identifier duplicated',
       'Price missing', 'Pages or hours missing', 'Release date missing', 'No problem', 'Check due', 'Checked in time', 'Do now', 'Next quarter', 'Drop', 'Cost share high', 'Cost share fine']
V1 = ['Slot is free', 'Move the date', 'Too close to a release', 'On plan', 'Behind plan', 'Start now', 'On time', 'Late', 'Realistic', 'Compress the plan',
      'Start by the dates below', 'Already late', 'Upload now', 'Safe', 'Window too long']
V2 = ['Add audio first', 'Add large print first', 'Add paperback first', 'Add hardcover first', 'Covered', 'Add now', 'Wait', 'Align the prices', 'Prices are consistent',
      'Price high', 'Price fair', 'Price low', 'Clean', 'Fix before upload', 'Keep the date', 'Move the release']
V3 = ['Spread the work', 'Load is ok', 'Readers wait too long', 'Wait is ok', 'Feed Tamsin Hartwell', 'Feed Corvin Ashdale', 'Balanced', 'Refresh prices', 'Prices up to date',
      'Pre-order is safe', 'Pre-order is at risk']
assert len(CHKL) <= 30 and len(V1) <= 30 and len(V2) <= 30 and len(V3) <= 30

lists = [
    L('role', 'Role', P(ROLES)), L('penname', 'Pen name', P(PEN_NAMES)), L('series', 'Series', P(SERIES)), L('genre', 'Genre', P(GENRES)), L('tstatus', 'Title status', P(TITLE_STATUS)),
    L('format', 'Format', P(FORMATS)), L('estatus', 'Edition status', P(EDITION_STATUS)), L('store', 'Store', P(STORES)), L('currency', 'Currency', P(CURRENCIES)),
    L('jobkind', 'Job kind', P(JOB_KINDS)), L('person', 'Contractor', P(PERSON)), L('ckind', 'Calendar entry kind', P(CKIND)), L('pkind', 'Promotion kind', P(PROMO_KINDS)),
    L('wprio', 'Priority', P(WPRIO)), L('wstatus', 'Wish list status', P(WSTATUS)), L('planstatus', 'Series plan status', P(PLANSTATUS)), L('chk', 'Check result', P(CHKL)),
    L('v1', 'Verdict A', P(V1)), L('v2', 'Verdict B', P(V2)), L('v3', 'Verdict C', P(V3)),
]
assert len(lists) <= 20
_M = {'role': K(ROLES), 'penname': K(PEN_NAMES), 'series': K(SERIES), 'genre': K(GENRES), 'tstatus': K(TITLE_STATUS), 'format': K(FORMATS), 'estatus': K(EDITION_STATUS), 'store': K(STORES),
      'currency': K(CURRENCIES), 'jobkind': K(JOB_KINDS), 'person': K(PERSON), 'ckind': K(CKIND), 'pkind': K(PROMO_KINDS), 'wprio': K(WPRIO), 'wstatus': K(WSTATUS), 'planstatus': K(PLANSTATUS),
      'chk': K(CHKL), 'v1': K(V1), 'v2': K(V2), 'v3': K(V3)}


def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def ck(label): return tok('chk', label)
def v1(label): return tok('v1', label)
def v2(label): return tok('v2', label)
def v3(label): return tok('v3', label)
def fmt(label): return tok('format', label)
def sr(label): return tok('series', label)
def tst(label): return tok('tstatus', label)
def est(label): return tok('estatus', label)
def ckd(label): return tok('ckind', label)
