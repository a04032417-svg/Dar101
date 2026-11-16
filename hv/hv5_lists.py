"""HVAC and plumbing contractor suite part 5: label lists shared by data, tables, tools."""
import sys, os, re, datetime as dt; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
SUPPLIERS = ['Your parts counter', 'Your equipment supplier']
PAYEES = ['Your equipment supplier', 'Your parts counter', 'Electrical subcontractor', 'Sheet-metal subcontractor']
PCCAT = ['Heating', 'Cooling', 'Plumbing', 'Equipment']
CPERIOD = ['Last 3 months', 'Previous 3 months']
SPERIOD = ['Last 6 counts', 'Earlier counts']
SCEN = ['Base', 'Best', 'Worst']
import random as _random
def tools_adj():
    """tool purchase rows from hv_core; a third are moved back in time so some tools are due or past their life (demo story); generic wording"""
    rows = [dict(x) for x in tool_rows()]
    r = _random.Random('hv5-tools')
    for i, x in enumerate(rows):
        if i % 3 == 0:
            d = TODAY - dt.timedelta(days=int(x['life_years'] * 365 + r.uniform(-330, 420)))
            x['date'] = iso(d); x['month'] = iso(dt.date(d.year, d.month, 1)); x['cost'] = round(x['cost'] * r.uniform(.8, 1.0), 2)
        if x['description'] == 'Ladders and roof safety kit': x['description'] = 'Ladders and roof kit'
        x['replace_year'] = to_date(x['date']).year + x['life_years']
    rows.sort(key=lambda x: x['date'])
    for i, x in enumerate(rows, 1): x['tool_id'] = 'TL-%04d' % i
    return rows
TOOLS_ADJ = tools_adj()
RYEARS = [str(y) for y in sorted({x['replace_year'] for x in TOOLS_ADJ})]
base_lists = [
    L('tech', 'Technician', P(TECH6)), L('crew', 'Field crew', P(TECH_NAMES)), L('van', 'Van', P(VAN_NAMES)), L('partcat', 'Part category', P(PART_CATEGORIES)), L('pccat', 'Price change category', P(PCCAT)),
    L('supplier', 'Supplier', P(SUPPLIERS)), L('payee', 'Payee', P(PAYEES)), L('pokind', 'Purchase kind', P(PURCHASE_KINDS)), L('postatus', 'Purchase status', P(PO_STATUS)),
    L('jobtype', 'Job type', P(JOB_TYPES)), L('cperiod', 'Cost period', P(CPERIOD)), L('speriod', 'Count period', P(SPERIOD)), L('scen', 'Scenario', P(SCEN)), L('season', 'Season', P(SEASONS)),
    L('ryear', 'Replacement year', [('y' + y, y) for y in RYEARS]),
]
_M = {'tech': K(TECH6), 'crew': K(TECH_NAMES), 'van': K(VAN_NAMES), 'partcat': K(PART_CATEGORIES), 'pccat': K(PCCAT), 'supplier': K(SUPPLIERS), 'payee': K(PAYEES), 'pokind': K(PURCHASE_KINDS),
      'postatus': K(PO_STATUS), 'jobtype': K(JOB_TYPES), 'cperiod': K(CPERIOD), 'speriod': K(SPERIOD), 'scen': K(SCEN), 'season': K(SEASONS), 'ryear': {y: 'y' + y for y in RYEARS}}
def key(lst, label): return _M[lst][label]
def tok(lst, label): return LV(lst, _M[lst][label])

CKL, CKK = [], {}
def ck(label):
    if label not in CKK:
        k = re.sub(r'[^a-z0-9]+', '_', label.lower()).strip('_')[:21]
        while k in CKK.values(): k = k[:-1] + 'x'
        CKK[label] = k; CKL.append(label)
    return '{list:ck%d.%s}' % (CKL.index(label) // 30 + 1, CKK[label])
def ck_lists():
    out = []
    for i in range(0, len(CKL), 30):
        out.append(L('ck%d' % (i // 30 + 1), 'Check result %d' % (i // 30 + 1), [(CKK[l], l) for l in CKL[i:i + 30]]))
    return out
