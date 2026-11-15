"""Author and Self-Publisher suite part 4 (Ads and Price Promotions): label lists shared by data, tables, tools.
Verdict words are registered on first use (v('Stop')) and put into the check lists ck1..ck4 at the end (a formula never types a word: it points at the list cell)."""
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


TITLE_NAMES = [t['title'] for t in title_rows()]
SHORT_NAMES = {'Lantern Bay Books 1-3 - cosy mystery readers': 'Lantern Bay Books 1-3 - cosy readers', 'A Winter at Saltmere - cosy series starters': 'A Winter at Saltmere - series starters'}
CAMPAIGN_NAMES = [SHORT_NAMES.get(c['campaign'], c['campaign']) for c in campaign_rows()]
PLATFILTER = ['All platforms'] + AD_PLATFORMS
SCEN = ['Base', 'Best', 'Worst']
PEOPLE_FIRST = ['Lucia', 'Dario', 'Mikael', 'Renata', 'Noor', 'Partner author 03']
VERBS = []
_REG = {}           # label -> (list key, value key)
_CKS = {'ck1': [], 'ck2': [], 'ck3': [], 'ck4': []}


def v(label):
    """token of a verdict word; the word is added to the first check list that has room (30 values each)"""
    if label not in _REG:
        for lk in ('ck1', 'ck2', 'ck3', 'ck4'):
            if len(_CKS[lk]) < 30:
                _CKS[lk].append(label); _REG[label] = lk; break
        else: raise RuntimeError('check lists full')
    return '{list:%s.%s}' % (_REG[label], _key(label))


def _key(label):
    lk = _REG[label]
    return K(_CKS[lk])[label]


def kd(label):
    """demo key of a registered word"""
    v(label); return _key(label)


_M = {'penname': K(PEN_NAMES), 'series': K(SERIES), 'tstatus': K(TITLE_STATUS), 'format': K(FORMATS), 'estatus': K(EDITION_STATUS), 'store': K(STORES), 'platform': K(AD_PLATFORMS),
      'adstatus': K(AD_STATUS), 'pkind': K(PROMO_KINDS), 'pstatus': K(PROMO_STATUS), 'title': K(TITLE_NAMES), 'campaign': K(CAMPAIGN_NAMES), 'platfilter': K(PLATFILTER), 'scen': K(SCEN), 'person': K(PEOPLE_FIRST)}
def key(lst, label): return _M[lst][label]            # demo value of a list column
def tok(lst, label): return LV(lst, _M[lst][label])   # token for a formula
def yes(): return '{list:yesno.yes}'
def no(): return '{list:yesno.no}'


def build_lists():
    base = [L('penname', 'Pen name', P(PEN_NAMES)), L('series', 'Series', P(SERIES)), L('tstatus', 'Title status', P(TITLE_STATUS)), L('format', 'Format', P(FORMATS)),
            L('estatus', 'Edition status', P(EDITION_STATUS)), L('store', 'Store', P(STORES)), L('platform', 'Ad platform', P(AD_PLATFORMS)), L('adstatus', 'Campaign status', P(AD_STATUS)),
            L('pkind', 'Promotion kind', P(PROMO_KINDS)), L('pstatus', 'Promotion status', P(PROMO_STATUS)), L('title', 'Title', P(TITLE_NAMES)), L('campaign', 'Campaign', P(CAMPAIGN_NAMES)),
            L('platfilter', 'Platform filter', P(PLATFILTER)), L('scen', 'Scenario', P(SCEN)), L('person', 'First name', P(PEOPLE_FIRST))]
    names = {'ck1': 'Check result A', 'ck2': 'Check result B', 'ck3': 'Check result C', 'ck4': 'Check result D'}
    for lk in ('ck1', 'ck2', 'ck3', 'ck4'):
        if _CKS[lk]:
            while len(_CKS[lk]) < 2: _CKS[lk].append('Spare %d' % len(_CKS[lk]))
            base.append(L(lk, names[lk], P(_CKS[lk])))
    assert len(base) <= 20
    return base
