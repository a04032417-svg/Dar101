"""Author and self-publisher suite part 7: demo rows from au_core (thinned row-level tables, monthly totals built from the full generator output)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from au7_lists import *
import collections

dd = to_date
ST = story()
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}

EDS = edition_rows(); ED = {e['edition_id']: e for e in EDS}
EVS = event_rows(); ELS = event_sale_rows(); STK = stock_rows(); DEALS = deal_rows(); INST = instalment_rows(); ORD = direct_order_rows(); PNL = pnl_rows()
PRINT_IDS = [e['edition_id'] for e in EDS if e['format'] in PRINT_FORMATS]
assert len(PRINT_IDS) == 37
STOCK_IDS = []
for _s in STK:
    if _s['edition_id'] not in STOCK_IDS: STOCK_IDS.append(_s['edition_id'])
assert len(STOCK_IDS) == 17


def team_d():
    return [dict(person_id=t['person_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), pay_type=key('paytype', t['pay_type']), phone=t['phone'], email=t['email'],
                 rate=t['rate'], rate_unit=t['rate_unit'], country=t['country'], since=t['since']) for t in team]


def stores_d(): return [dict(store=key('store', s['store']), royalty_share=s['royalty_share'], delay_days=s['delay_days']) for s in stores]
def countries_d(): return [dict(country=key('country', x['country']), currency=key('currency', x['currency']), sales_tax_pct=x['sales_tax_pct']) for x in countries]
def formats_d(): return [dict(format=key('format', f['format']), royalty_share=f['royalty_share'], base_cost=f['base_cost']) for f in formats]


def direct_price(e, i):
    """direct store price: the list price, a few discounted ebooks and audiobooks"""
    p = e['list_price']
    if e['format'] == 'Ebook' and e['royalty_share'] >= 0.7 and p >= 2.99 and i % 3 == 0: return round(p * 0.7) - 0.01
    if e['format'] == 'Audiobook': return round(p * 0.9) - 0.01
    if e['edition_id'] == 'ED-0062': return 12.99
    return p


def editions_d():
    return [dict(edition_id=e['edition_id'], title_id=e['title_id'], title=e['title'], format=key('format', e['format']), list_price=e['list_price'], direct_price=direct_price(e, i), unit_cost=e['unit_cost'],
                 royalty_share=e['royalty_share'], pages=e['pages'], release_date=e['release_date'], status=key('estatus', e['status'])) for i, e in enumerate(EDS)]


def orders_d():
    out = []
    for o in ORD[-400:]:
        out.append(dict(order_id=o['order_id'], date=o['date'], country=key('country', o['country']), currency=key('currency', o['currency']), edition_id=o['edition_id'], title=o['title'],
                        format=key('format', o['format']), qty=o['qty'], unit_price=o['unit_price'], discount=o['discount'], tax_collected=o['tax_collected'], shipping_charged=o['shipping_charged'],
                        payment_fee=o['payment_fee'], delivery_cost=o['delivery_cost'], rate=o['rate']))
    return out


def ledger_d():
    """the last five months with sales of each edition, rows of the full ledger (royalty in the home currency)"""
    by = collections.defaultdict(list)
    for x in sales_rows():
        if x['units'] > 0 and x['store'] != 'Direct store': by[x['edition_id']].append(x)
    out = []
    for eid in sorted(by):
        for x in by[eid][-5:]: out.append(x)
    out.sort(key=lambda x: (x['month'], x['edition_id']))
    return [dict(sale_id=x['sale_id'], month=x['month'], edition_id=x['edition_id'], title=x['title'], format=key('format', x['format']), store=key('store', x['store']), units=x['units'],
                 royalty_home=round(x['royalty_home'], 2)) for x in out]


def dmargin_d():
    return [dict(edition_id=e['edition_id'], format=key('format', e['format']), review_on=ago(10 + (i * 11) % 170)) for i, e in enumerate(EDS)]


# ---- monthly totals of the direct store, built from every order (home currency); the order rows above are the recent ones
def dmonth_d():
    agg = collections.defaultdict(lambda: collections.defaultdict(float))
    for o in ORD:
        a = agg[o['month']]; r = o['rate']
        a['orders'] += 1; a['copies'] += o['qty']; a['gross'] += o['qty'] * o['unit_price'] * r; a['discounts'] += o['discount'] * r; a['shipping'] += o['shipping_charged'] * r
        a['tax'] += o['tax_collected'] * r; a['fees'] += o['payment_fee'] * r; a['delivery'] += o['delivery_cost']
    rev = {p['month']: p['revenue'] for p in PNL}
    out = []
    for m in months24():
        k = iso(m); a = agg[k]
        out.append(dict(month=k, orders=int(a['orders']), copies=int(a['copies']), gross=round(a['gross'], 2), discounts=round(a['discounts'], 2), shipping_charged=round(a['shipping'], 2),
                        tax_collected=round(a['tax'], 2), fees=round(a['fees'], 2), delivery=round(a['delivery'], 2), all_revenue=round(rev[k], 2)))
    return out


def dgoal_d(): return [dict(month=iso(month_start(k))) for k in range(11, -1, -1)]
def printm_d(): return [dict(edition_id=i, format=key('pformat', ED[i]['format']), checked_on=ago(8 + (n * 13) % 200)) for n, i in enumerate(PRINT_IDS)]


def stockmoves_d():
    return [dict(stock_id=s['stock_id'], date=s['date'], edition_id=s['edition_id'], title=s['title'], format=key('pformat', s['format']), move=key('move', s['move']), copies=s['copies'], unit_cost=s['unit_cost']) for s in STK]


_CNT = {'ED-0036': 21, 'ED-0065': 40, 'ED-0062': 75, 'ED-0002': 52}      # last count dates (days ago): the low paperback was counted long ago
def stockpos_d():
    return [dict(edition_id=i, format=key('pformat', ED[i]['format']), counted_on=ago(_CNT.get(i, 25 + (n * 29) % 330))) for n, i in enumerate(STOCK_IDS)]


def events_d():
    return [dict(event_id=e['event_id'], date=e['date'], name=e['name'], kind=key('ekind', e['kind']), city=e['city'], hours=e['hours'], table_fee=e['table_fee'], travel_cost=e['travel_cost'],
                 nights=e['nights'], lodging_cost=e['lodging_cost'], copies_taken=e['copies_taken'], copies_sold=e['copies_sold'], sales=e['sales'], cost_of_copies=e['cost_of_copies'],
                 new_subscribers=e['new_subscribers']) for e in EVS]


def evlines_d():
    return [dict(line_id=l['line_id'], event_id=l['event_id'], date=l['date'], edition_id=l['edition_id'], title=l['title'], format=key('format', l['format']), copies=l['copies'], price=l['price']) for l in ELS]


def evprofit_d(): return [dict(event_id=e['event_id']) for e in EVS]
def evkinds_d(): return [dict(kind=key('ekind', k), period=key('period', p)) for p in PERIODS for k in EVENT_KINDS]


def deals_d():
    return [nb(dict(deal_id=d['deal_id'], title=d['title'], kind=key('dkind', d['kind']), language=d['language'], territory=d['territory'], offered_on=d['offered_on'], signed_on=d['signed_on'],
                    term_years=d['term_years'], term_end=d['term_end'], fee=d['fee'], agent_pct=d['agent_pct'], status=key('dstatus', d['status']))) for d in DEALS]


def instal_d():
    return [nb(dict(instalment_id=i['instalment_id'], deal_id=i['deal_id'], due_date=i['due_date'], amount=i['amount'], received_on=i['received_on'])) for i in sorted([x for x in INST if x['received_on']], key=lambda x: x['due_date'], reverse=True) + sorted([x for x in INST if not x['received_on']], key=lambda x: x['due_date'])]


def rmonth_d(): return [dict(month=iso(month_start(k))) for k in range(9, -4, -1)]
