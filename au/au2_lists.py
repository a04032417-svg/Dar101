"""Author and Self-Publisher suite, part 2 (Production Costs and Break-Even): label lists shared by data, tables, tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from au_core import *
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


LANGS = ['Japanese', 'German', 'Spanish', 'French', 'Portuguese', 'Italian', 'Polish']
GOFMT = ['Audiobook', 'Large print', 'Hardcover']
GOSTATUS = ['Open', 'Decided']
CONTRACTORS = ['Priya Nandakumar', 'Leopold Brandt', 'Ines Carvalho', 'Tomasz Wrona', 'Amara Oyelaran', 'Gideon Falk', 'Yuki Tanabe', 'Noor Castellan',
               'Lucia Ferreira', 'Mikael Dahl', 'Hye-jin Seo', 'Sven Hallgren']
TITLE_NAMES = [t['title'] for t in title_rows()]

# labels that table formulas return (a formula never types a word: it points at the list cell)
CKA = ['Paid back', 'On track', 'Behind', 'Not on sale yet', 'Over the typical rate', 'Within the typical rate', 'Under the typical rate',
       'Overdue', 'Delivered, not paid', 'In progress', 'Booked', 'Below the floor', 'Above the floor', 'High for the kind', 'Fair for the kind', 'Low for the kind',
       'Produce', 'Wait', 'Skip', 'Translate', 'Sell the rights instead', 'Above your average', 'Below your average', 'Due in 7 days', 'Due in 30 days', 'Due later']
CK2 = ['Renegotiate the next quote', 'Within budget', 'Pay on the due date', 'Ask to split', 'Hold the next job', 'Write', 'Both', 'Schedule fits', 'Move a payment later',
       'Spread the work', 'Concentration is ok', 'Choose A', 'Choose B', 'Choose C', 'Move the release', 'Absorb the delay', 'Within the cap', 'Over the cap', 'Affordable',
       'Stretch', 'Too heavy', 'Refresh the cover', 'Hold the cover', 'Robust', 'Sensitive', 'Fair', 'High', 'Low']
assert len(CKA) <= 30 and len(CK2) <= 30

lists = [
    L('role', 'Role', P(ROLES)), L('penname', 'Pen name', P(PEN_NAMES)), L('series', 'Series', P(SERIES)), L('tstatus', 'Title status', P(TITLE_STATUS)),
    L('format', 'Format', P(FORMATS)), L('estatus', 'Edition status', P(EDITION_STATUS)), L('jobkind', 'Job kind', P(JOB_KINDS)), L('jstatus', 'Job status', P(JOB_STATUS)),
    L('stage', 'Payment stage', P(PAY_STAGES)), L('cpaystatus', 'Payment status', P(CPAY_STATUS)), L('language', 'Language', P(LANGS)), L('title', 'Title', P(TITLE_NAMES)),
    L('contractor', 'Contractor', P(CONTRACTORS)), L('gofmt', 'New format', P(GOFMT)), L('gostatus', 'Case status', P(GOSTATUS)),
    L('cka', 'Check result', P(CKA)), L('ck2', 'Verdict', P(CK2)),
]
assert len(lists) <= 20
_M = {'role': K(ROLES), 'penname': K(PEN_NAMES), 'series': K(SERIES), 'tstatus': K(TITLE_STATUS), 'format': K(FORMATS), 'estatus': K(EDITION_STATUS), 'jobkind': K(JOB_KINDS),
      'jstatus': K(JOB_STATUS), 'stage': K(PAY_STAGES), 'cpaystatus': K(CPAY_STATUS), 'language': K(LANGS), 'title': K(TITLE_NAMES), 'contractor': K(CONTRACTORS), 'gofmt': K(GOFMT),
      'gostatus': K(GOSTATUS), 'cka': K(CKA), 'ck2': K(CK2)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def ca(label): return tok('cka', label)
def c2(label): return tok('ck2', label)
