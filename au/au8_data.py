"""Author and self-publisher suite part 8: demo rows from au_core (thinned where the table is long, aggregated figures typed from the whole ledger). The slow world build is cached once."""
import sys, os, pickle; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from au8_lists import *
import collections

dd = to_date
ST = story()
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'au8_cache.pkl')


def _build():
    c = {}
    c['team'] = team; c['statements'] = statement_rows(); c['payments'] = payment_rows(); c['jobpay'] = jobpay_rows(); c['expenses'] = expense_rows(); c['pnl'] = pnl_rows(); c['cash'] = cash_rows()
    c['titles'] = {t['title_id']: t['title'] for t in title_rows()}; c['tax'] = tax_rows(); c['auth'] = author_statement_rows(); c['stores'] = stores
    ads = [a for a in ad_day_rows() if a['date'] > ago(90)]
    sp = sum(a['spend'] for a in ads); c['ad_return'] = round((sum(a['royalties'] for a in ads)) / sp, 2) if sp else 0
    by = collections.defaultdict(float); cut = iso(month_start(12))
    for x in sales_rows():
        if x['month'] >= cut: by[x['store']] += x['royalty_home']
    c['store_dep'] = round(max(by.values()) / sum(by.values()), 2)
    rt = readthrough_rows(); c['rt1'] = round(min(r['readthrough'] for r in rt if r['step'] == 1), 3); c['rt_later'] = round(min(r['readthrough'] for r in rt if r['step'] > 1), 3)
    n = 0
    for t in title_rows():
        if t['release_date'] <= iso(TODAY) and title_cost(t['title_id']) > title_royalty(t['title_id']): n += 1
    c['titles_be'] = n
    return c


if os.path.exists(CACHE) and os.environ.get('AU8_FRESH') != '1':
    C = pickle.load(open(CACHE, 'rb'))
    if C.get('today') != iso(TODAY): C = None
else: C = None
if C is None:
    C = _build(); C['today'] = iso(TODAY); pickle.dump(C, open(CACHE, 'wb'))


def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def nz(d, *cols): return {k: v for k, v in d.items() if v not in ('', None) and not (k in cols and v == 0)}

TEAM = C['team']; TEAMD = {t['name']: t for t in TEAM}
MS0 = month_start(0)


def team_d(): return [dict(person_id=t['person_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), pay_type=key('paytype', t['pay_type']), phone=t['phone'], email=t['email'],
                           rate=t['rate'], rate_unit=t['rate_unit'], country=t['country'], since=t['since']) for t in TEAM]


def stores_d(): return [dict(store=key('store', s['store']), royalty_share=s['royalty_share'], delay_days=s['delay_days']) for s in C['stores']]


STM = C['statements'][-60:]; STM_IDS = {s['statement_id'] for s in STM}
def statements_d(): return [nb(dict(statement_id=s['statement_id'], month=s['month'], store=key('store', s['store']), statement_amount=s['statement_amount'], expected_on=s['expected_on'], paid_on=s['paid_on'],
                                    received=s['received'], status=key('ststatus', s['status']))) for s in STM]


PAYS = [p for p in C['payments'] if p['statement_id'] in STM_IDS][-60:]
def payments_d(): return [nz(dict(payment_id=p['payment_id'], statement_id=p['statement_id'], store=key('store', p['store']), month=p['month'], received_on=p['received_on'], statement_amount=p['statement_amount'],
                                  fee=p['fee'], fx_loss=p['fx_loss'], received=p['received']), 'fee', 'fx_loss') for p in PAYS]


_open = [j for j in C['jobpay'] if j['status'] != 'Paid']
_paid = [j for j in C['jobpay'] if j['status'] == 'Paid'][-(90 - len(_open)):]
JOBPAY = sorted(_paid + _open, key=lambda j: (j['date'], j['cpay_id']))
_MOVE = {'CP-0239': 14, 'CP-0241': 7, 'CP-0246': 10}
def jobpay_d(): return [nb(dict(cpay_id=j['cpay_id'], job_id=j['job_id'], title_id=j['title_id'], title=C['titles'][j['title_id']], contractor=j['contractor'], stage=key('stage', j['stage']), date=j['date'], month=j['month'], amount=j['amount'],
                             status=key('cpaystatus', j['status']), move_days=_MOVE.get(j['cpay_id'], ''))) for j in JOBPAY]


_EX = C['expenses']
_MISS = {e['expense_id'] for i, e in enumerate(_EX) if e['date'] >= ago(170) and e['category'] in ('Review copies', 'Education', 'Other', 'Office and equipment', 'Software and tools') and i % 2 == 0}
def expenses_d(): return [dict(expense_id=e['expense_id'], date=e['date'], month=e['month'], category=key('expcat', e['category']), vendor=e['vendor'], amount=e['amount'], pen_name=key('expen', e['pen_name']),
                               receipt=e['expense_id'] not in _MISS) for e in _EX]


_BUD = {'Newsletter service': 55, 'Website and store': 90, 'Software and tools': 60, 'Virtual assistant': 330, 'Review copies': 70, 'Accounting and fees': 90, 'Education': 40, 'Office and equipment': 45,
        'Business insurance': 25, 'Other': 40}
_NOTE = {'Newsletter service': 'The newsletter service bill', 'Website and store': 'Hosting, the direct store and the web developer', 'Software and tools': 'Writing, design and layout tools', 'Virtual assistant': 'The assistant, by the hour',
         'Review copies': 'Gifts and postage for reviewers', 'Accounting and fees': 'The accountant and bank fees', 'Education': 'Courses and books', 'Office and equipment': 'Supplies and small equipment',
         'Business insurance': 'Insurance of the business', 'Other': 'Anything that fits no other line'}
def costcat_d(): return [dict(category=key('expcat', k), monthly_budget=_BUD[k], note=_NOTE[k]) for k in EXPENSE_CATEGORIES]


def pnl_d(): return [nz(dict(month=p['month'], royalties=p['royalties'], page_reads=p['page_reads'], direct_net=p['direct_net'], event_sales=p['event_sales'], rights=p['rights'], ads=p['ads'], production=p['production'],
                             expenses=p['expenses'], event_costs=p['event_costs']), 'rights', 'ads') for p in C['pnl']]


def cash_d(): return [nz(dict(month=x['month'], opening=x['opening'], receipts=x['receipts'], ads=x['ads'], production=x['production'], expenses=x['expenses'], event_costs=x['event_costs'],
                              author_copies=x['author_copies'], tax_set_aside=x['tax_set_aside'], owner_draw=x['owner_draw']), 'ads', 'event_costs', 'author_copies', 'tax_set_aside') for x in C['cash']]


def tax_d(): return [nz(dict(month=t['month'], set_aside_pct=t['set_aside_pct'], set_aside=t['set_aside'], tax_paid=t['tax_paid']), 'set_aside', 'tax_paid') for t in C['tax']]


def expmonth_d(): return [dict(row_id='EC-%03d' % (i + 1), month=iso(month_start(k)), category=key('expcat', c)) for i, (k, c) in enumerate((k, c) for k in range(11, -1, -1) for c in EXPENSE_CATEGORIES)]
def forecast_d(): return [dict(month=iso(add_months(MS0, i)), fmon=key('fmon', 'Month %d' % i)) for i in range(1, 13)]
def receipts_d(): return [dict(month=iso(add_months(MS0, i)), fmon=key('fmon', 'Month %d' % i)) for i in range(1, 13)]
def due_d(): return [dict(rank_no=i) for i in range(1, 21)]
def scenarios_d(): return [dict(scenario=key('scen', 'Base'), sales_change=0.0, cost_change=0.0), dict(scenario=key('scen', 'Best'), sales_change=0.10, cost_change=-0.03),
                           dict(scenario=key('scen', 'Worst'), sales_change=-0.20, cost_change=0.05), dict(scenario=key('scen', 'Cautious'), sales_change=-0.10, cost_change=0.02),
                           dict(scenario=key('scen', 'Strong'), sales_change=0.20, cost_change=-0.05)]
def health_d():
    typed = {3: C['ad_return'], 7: C['store_dep'], 8: C['rt1'], 9: C['rt_later'], 10: C['titles_be']}
    return [nb(dict(area_no=i, typed_value=typed.get(i, ''), band=0.2)) for i in range(1, 13)]


# ---- authors: the advance is a demo value of this workbook (one pen name carries an advance that the author share recoups at a share of each month)
ADV = {'Tamsin Hartwell': 0.0, 'Corvin Ashdale': 10000.0}; RECOUP = 0.30; ADV_FROM = iso(month_start(9))
TERMS = [('Tamsin Hartwell', iso(add_months(MS0, -24).replace(day=1)), 0.65), ('Corvin Ashdale', iso(add_months(MS0, -24).replace(day=15)), 0.60), ('Corvin Ashdale', iso(add_months(MS0, -17).replace(day=15)), 0.65),
         ('Tamsin Hartwell', iso(add_months(MS0, -12).replace(day=1)), 0.70), ('Corvin Ashdale', iso(add_months(MS0, -9).replace(day=15)), 0.70)]
def authors_d(): return [dict(pen_name=key('penname', p), effective_from=d, author_share=sh) for p, d, sh in TERMS]

def _share(pen, month): return [sh for p, d, sh in sorted(TERMS, key=lambda t: t[1]) if p == pen and d <= month][-1]


def _auth():
    left = {p: 0.0 for p in ADV}; out = []
    for a in C['auth']:
        if a['month'] == ADV_FROM: left = dict(ADV)
        shr = _share(a['pen_name'], a['month']); sh = a['royalties_earned'] * shr; rec = round(min(left[a['pen_name']], sh * RECOUP), 2) if left[a['pen_name']] > 0 and a['month'] >= ADV_FROM else 0.0
        left[a['pen_name']] = round(left[a['pen_name']] - rec, 2)
        out.append(dict(a, author_share=shr, advance_recouped=rec, advance_left=left[a['pen_name']]))
    return out
AUTH = _auth()
def authstmt_d(): return [nz(dict(statement_id=a['statement_id'], month=a['month'], pen_name=key('penname', a['pen_name']), royalties_earned=a['royalties_earned'], advance_paid=ADV[a['pen_name']],
                                  advance_recouped=a['advance_recouped'], costs_charged_back=a['costs_charged_back']), 'advance_recouped', 'advance_paid') for a in AUTH]


def authsched_d(): return [dict(month=iso(add_months(MS0, i)), pen_name=key('penname', p)) for i in range(1, 7) for p in PEN_NAMES]
def yearend_d(): return [dict(line_no=i) for i in range(1, 21)]


def _first(rows, pred):
    """put the newest row that fills every optional field first, so the printed sheets of the demo show every field"""
    for i in range(len(rows) - 1, -1, -1):
        if pred(rows[i]): return [rows[i]] + rows[:i] + rows[i + 1:]
    return rows
_cash_d, _tax_d, _auth_d = cash_d, tax_d, authstmt_d
def cash_d(): return _first(_cash_d(), lambda r: all(r.get(k) for k in ('ads', 'event_costs', 'author_copies', 'tax_set_aside')))
def tax_d(): return _first(_tax_d(), lambda r: r.get('set_aside') and r.get('tax_paid'))
def authstmt_d(): return _first(_auth_d(), lambda r: r.get('advance_recouped') and r.get('advance_paid') and r['pen_name'] == key('penname', 'Corvin Ashdale'))
