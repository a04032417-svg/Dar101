"""Wedding suite part 3: demo rows from wp_core and the small reference rows the vendor workbook adds."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wp3_lists import *

ST = story()
TEAM = {t['team_id']: t for t in team}
P2_PHONE = TEAM['WP-02']['phone']; P1_PHONE = TEAM['WP-01']['phone']
VEND = {x['vendor_id']: x for x in vendor_rows()}
VID = {x['vendor']: x['vendor_id'] for x in vendor_rows()}


def nb(d): return {k: v_ for k, v_ in d.items() if v_ not in ('', None)}
def I(x): return int(round(x))


CONFIRMED = {'VD-01', 'VD-02', 'VD-03', 'VD-07', 'VD-15'}


def vendors_d():
    return [nb(dict(vendor_id=x['vendor_id'], vendor=key('vname', x['vendor']), category=key('vcat', x['category']), contact=x['contact'], phone=x['phone'], email=x['email'],
                    status=key('vstatus', x['status']), booked_on=x['booked_on'], contract_total=I(x['contract_total']), lead_months=x['lead_months'], payer=key('payer', x['payer']),
                    last_contact=x['last_contact'], follow_up=x['follow_up'], confirmed=(x['vendor_id'] in CONFIRMED))) for x in vendor_rows()]


TIP = {'VD-03': 0.05, 'VD-05': 0.05, 'VD-04': 0.05, 'VD-14': 0.10, 'VD-09': 0.10, 'VD-02': 0.0}


def quotes_d():
    out = []
    for q in quote_rows():
        valid = ago(3) if q['quote_id'] == 'QT-035' else q['valid_until']
        out.append(nb(dict(quote_id=q['quote_id'], vendor_id=q['vendor_id'], vendor=key('vname', q['vendor']), category=key('vcat', q['category']), option=key('option', q['option']),
                           status=key('qstatus', q['status']), quote_date=q['quote_date'], base_price=I(q['base_price']), service_pct=q['service_pct'], tax_pct=q['tax_pct'],
                           delivery=I(q['delivery']), overtime=I(q['overtime']), travel=I(q['travel']), tip_pct=TIP.get(q['vendor_id'], 0.0), response_days=q['response_days'],
                           fit=q['fit'], response=q['response'], reviews=q['reviews'], chosen=bool(q['chosen']), included=q['included'], excluded=q['excluded'], valid_until=valid)))
    return out


BLANK_DETAIL = {'CT-039', 'CT-056'}   # cancellation terms not yet written down (cake baker, rentals)
BLANK_DATE = {'CT-063'}               # coordinator final payment date not yet recorded


def contracts_d():
    out = []
    for c_ in contract_rows():
        out.append(nb(dict(contract_id=c_['contract_id'], vendor_id=c_['vendor_id'], vendor=key('vname', c_['vendor']), kind=key('ckind', c_['kind']),
                           detail='' if c_['contract_id'] in BLANK_DETAIL else c_['detail'], item_date='' if c_['contract_id'] in BLANK_DATE else c_['item_date'], amount=I(c_['amount']))))
    return out


def schedule_d():
    return [nb(dict(pay_id=r['pay_id'], vendor_id=r['vendor_id'], vendor=key('vname', r['vendor']), category=key('vcat', r['category']), kind=key('paykind', r['kind']), due_date=r['due_date'],
                    amount_due=I(r['amount_due']), amount_paid=I(r['amount_paid']), status=key('paystatus', r['status']))) for r in payment_schedule_rows()]


def run_d():
    return _fix([nb(dict(step_id=r['step_id'], date=r['date'], start=r['start'], minutes=r['minutes'], block=key('block', r['block']), place=key('place', r['place']), vendor_id=r['vendor_id'], what=r['what']))
            for r in run_rows()])


def _fix(rows):
    for r in rows:
        if r.get('step_id') == 'RS-30': r['minutes'] = 10
    return rows


def budget_d():
    return [dict(line_id=b['line_id'], category=key('category', b['category']), planned=I(b['planned']), committed=I(b['committed']), paid=I(b['paid'])) for b in budget_rows()]


WEIGHTS = [('Price', 0.35, 'Lowest true total in the slot divided by this quote'), ('Fit', 0.25, 'Your rating of how well it fits, 1 to 5'), ('Response', 0.15, 'Your rating of how they answer, 1 to 5'),
           ('Reviews', 0.15, 'Your rating of what others say, 1 to 5'), ('Speed of reply', 0.10, 'Fewer days to reply scores higher, 10 days scores zero')]
def weights_d(): return [dict(factor=f, weight=w, note=n) for f, w, n in WEIGHTS]


def pipeline_d(): return [dict(category=key('category', c_)) for c_ in BUDGET_CATEGORIES]
def planfit_d(): return [dict(category=key('category', c_)) for c_ in BUDGET_CATEGORIES]
def winners_d(): return [dict(vendor=key('vname', n)) for n in VNAMES]
def compare_d(): return [dict(quote_id=q['quote_id']) for q in quote_rows()]
def response_d(): return [dict(vendor=key('vname', n)) for n in VNAMES]
def lead_d(): return [dict(vendor=key('vname', n)) for n in VNAMES]
def statusum_d(): return [dict(status=key('vstage', s_)) for s_ in VSTAGE]


def deadlines_d():
    rows = []
    for c_ in contract_rows():
        if c_['item_date'] and c_['contract_id'] not in BLANK_DATE: rows.append((c_['item_date'], c_['contract_id']))
    for p in payment_schedule_rows():
        if p['status'] != 'Paid': rows.append((p['due_date'], p['pay_id']))
    for q in quotes_d():
        if q['status'] in (key('qstatus', 'Quote received'), key('qstatus', 'Shortlisted')): rows.append((q['valid_until'], q['quote_id']))
    return [dict(ref_id=i) for d_, i in sorted(rows)]


def arrivals_d(): return [dict(step_id=r['step_id']) for r in run_rows() if r['vendor_id']]


ORDER = ['Hair and makeup', 'Florist', 'Rentals', 'Caterer', 'Band or DJ', 'Photographer', 'Day-of coordinator', 'Transport', 'Officiant', 'Cake baker', 'Venue',
         'Videographer', 'Attire shop', 'Tailor', 'Stationery printer', 'Hotel room block']
assert sorted(ORDER) == sorted(VNAMES)
def contact_d(): return [dict(vendor=key('vname', n)) for n in ORDER]


CREW = {'Venue': 2, 'Caterer': 4, 'Photographer': 2, 'Videographer': 1, 'Band or DJ': 3, 'Florist': 2, 'Officiant': 1, 'Cake baker': 1, 'Hair and makeup': 2, 'Attire shop': 1,
        'Tailor': 1, 'Stationery printer': 1, 'Rentals': 3, 'Transport': 2, 'Day-of coordinator': 1, 'Hotel room block': 1}
def meals_d(): return [dict(vendor=key('vname', n), crew=CREW[n]) for n in ORDER]


FOLLOW = ['Videographer', 'Florist', 'Day-of coordinator', 'Stationery printer', 'Band or DJ', 'Rentals', 'Hotel room block', 'Officiant', 'Attire shop', 'Hair and makeup', 'Tailor', 'Transport']
def followups_d(): return [dict(vendor=key('vname', n)) for n in FOLLOW]


def cancel_d(): return [dict(vendor=key('vname', x['vendor']), category=key('vcat', x['category'])) for x in vendor_rows() if x['status'] == 'Booked']


if __name__ == '__main__':
    for f in (vendors_d, quotes_d, contracts_d, schedule_d, run_d, budget_d, weights_d, pipeline_d, planfit_d, winners_d, compare_d, response_d, lead_d, statusum_d, deadlines_d, arrivals_d, contact_d, meals_d, followups_d, cancel_d):
        print(f.__name__, len(f()))
