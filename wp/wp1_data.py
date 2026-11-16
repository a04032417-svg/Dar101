"""Wedding suite part 1: demo rows from wp_core and the small reference rows the budget workbook adds."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wp1_lists import *

ST = story()
TEAM = {t['team_id']: t for t in team}
P1_PHONE = TEAM['WP-01']['phone']; P2_PHONE = TEAM['WP-02']['phone']; PAR1_PHONE = TEAM['WP-03']['phone']; PAR2_PHONE = TEAM['WP-04']['phone']
FRIEND_PHONE = TEAM['WP-09']['phone']
VEND = {x['vendor_id']: x for x in vendor_rows()}


def nb(d): return {k: v_ for k, v_ in d.items() if v_ not in ('', None)}


def budget_d():
    return [dict(line_id=b['line_id'], category=key('category', b['category']), planned=b['planned'], committed=b['committed'], paid=b['paid'], share_couple=b['share_couple'],
                 share_p1_family=b['share_p1_family'], share_p2_family=b['share_p2_family'], priority=b['priority']) for b in budget_rows()]


def payers_d(): return [dict(payer=key('payerx', p['payer']), share=p['share'], agreed_amount=p['agreed_amount']) for p in payers] + [dict(payer=key('payerx', x), share=0, agreed_amount=0) for x in PAYERX[3:]]


def funding_d():
    return [dict(fund_id=f['fund_id'], source=key('source', f['source']), date=f['date'], amount=f['amount'], status=key('fstatus', f['status'])) for f in funding_rows()]


def fsum_d(): return [dict(source=key('source', s)) for s in FUND_SOURCES]


MOV = {'PY-005': 'Check or cheque', 'PY-007': 'Check or cheque', 'PY-009': 'Cash', 'PY-013': 'Cash'}


def schedule_d():
    out = []
    for r in payment_schedule_rows():
        out.append(nb(dict(pay_id=r['pay_id'], vendor_id=r['vendor_id'], vendor=key('vname', r['vendor']), category=key('category', r['category']), kind=key('paykind', r['kind']), due_date=r['due_date'],
                           amount_due=r['amount_due'], payer=key('payer', r['payer']), paid_on=r['paid_on'], amount_paid=r['amount_paid'], method=key('method', MOV.get(r['pay_id'], r['method'])) if r['method'] else '',
                           status=key('paystatus', r['status']), paid_by=key('payer', r['paid_by']) if r['paid_by'] else '')))
    return out


def payments_d():
    return [dict(payment_id=p['payment_id'], pay_id=p['pay_id'], date=p['date'], amount=p['amount'], paid_by=key('payer', p['paid_by']), method=key('method', MOV.get(p['pay_id'], p['method']))) for p in payment_rows()]


def vendors_d():
    return [nb(dict(vendor_id=x['vendor_id'], vendor=key('vname', x['vendor']), category=key('category', x['category']), contract_total=x['contract_total'], status=key('vstatus', x['status']),
                    payer=key('payer', x['payer']), booked_on=x['booked_on'], phone=x['phone'])) for x in vendor_rows()]


def hidden_d():
    return [dict(hidden_id=h['hidden_id'], item=h['item'], expected=h['expected'], status=key('hstatus', h['status']), category=key('category', h['category'])) for h in hidden_cost_rows()]


def tips_d():
    return [dict(tip_id=t['tip_id'], vendor_id=t['vendor_id'], vendor=key('vname', t['vendor']), gratuity_included=bool(t['gratuity_included']), basis=key('tipbasis', t['basis']), pct=t['pct'], flat=t['flat'],
                 bill=t['bill'], handed_by=key('owner', t['handed_by']), envelope_ready=bool(t['envelope_ready'])) for t in tip_rows()]


SCORES = {'Venue and setting': (5, 5), 'Food and drink': (5, 4), 'Photo and video': (4, 3), 'Music and dancing': (3, 5), 'Flowers and decor': (3, 2), 'Attire': (3, 4),
          'Invitations and paper': (2, 3), 'Extra events': (2, 4), 'Guest comfort': (4, 4), 'Reserve and tips': (3, 3)}
def pscore_d(): return [dict(area=key('parea', a), score_p1=s[0], score_p2=s[1]) for a, s in SCORES.items()]
def prank_d(): return [dict(area=key('parea', a)) for a in PAREAS]

BANDS = {  # category: (typical share, cost type, priority area, flexibility 1..5)
    'Venue': (0.17, 'Fixed', 'Venue and setting', 1), 'Catering and bar': (0.25, 'Per guest', 'Food and drink', 3), 'Photo and video': (0.10, 'Fixed', 'Photo and video', 3),
    'Music': (0.07, 'Fixed', 'Music and dancing', 3), 'Flowers and decor': (0.07, 'Fixed', 'Flowers and decor', 3), 'Attire and alterations': (0.08, 'Fixed', 'Attire', 3),
    'Hair and makeup': (0.02, 'Fixed', 'Attire', 2), 'Stationery and postage': (0.02, 'Per guest', 'Invitations and paper', 3), 'Ceremony and officiant': (0.01, 'Fixed', 'Venue and setting', 1),
    'Rentals': (0.03, 'Per guest', 'Guest comfort', 3), 'Cake and favors': (0.02, 'Per guest', 'Food and drink', 4), 'Transport and lodging': (0.02, 'Fixed', 'Guest comfort', 4),
    'Planner and coordinator': (0.03, 'Fixed', 'Guest comfort', 2), 'Other events': (0.04, 'Fixed', 'Extra events', 3), 'Tips and fees': (0.02, 'Fixed', 'Reserve and tips', 4),
    'Reserve': (0.05, 'Fixed', 'Reserve and tips', 1)}
assert abs(sum(b[0] for b in BANDS.values()) - 1) < 1e-9 and list(BANDS) == BUDGET_CATEGORIES


def bands_d(): return [dict(category=key('category', c_), typical_share=b[0], cost_type=key('ctype', b[1]), priority_area=key('parea', b[2])) for c_, b in BANDS.items()]
def rebal_d(): return [dict(category=key('category', c_), flex=b[3]) for c_, b in BANDS.items()]
def catpay_d(): return [dict(category=key('category', c_)) for c_ in BUDGET_CATEGORIES]
def truebud_d(): return [dict(category=key('category', c_)) for c_ in BUDGET_CATEGORIES]
def settle_d(): return [dict(payer=key('payerx', p_)) for p_ in PAYERX]
def due60_d(): return [dict(seqno=i) for i in range(1, 16)]


def cash_d():
    return [dict(month=iso(add_months(month_start(0), i))) for i in range(-1, 13)]


def ladder_d(): return [dict(step=key('cstep', s_), removed=5 * i) for i, s_ in enumerate(CSTEPS)]


QUOTES = {  # option -> (venue, catering, photo, music, flowers)
    'Option A: current Saturday': (5900, 8740, 2650, 2150, 2928),
    'Option B: a Friday, three weeks later': (5150, 8740, 2400, 1950, 2928),
    'Option C: a Saturday in September': (5400, 8740, 2650, 2150, 2500)}
CATS5 = ['Venue', 'Catering and bar', 'Photo and video', 'Music', 'Flowers and decor']
LEADS = [12, 10, 9, 8, 6]
NOTES = {'Option A: current Saturday': 'Your booked contracts', 'Option B: a Friday, three weeks later': 'Weekday rates, check the date is free', 'Option C: a Saturday in September': 'Shoulder season, ask each vendor'}
OPT_DATE = {'Option A: current Saturday': WEDDING_DAY, 'Option B: a Friday, three weeks later': WEDDING_DAY + dt.timedelta(days=20), 'Option C: a Saturday in September': WEDDING_DAY + dt.timedelta(days=112)}
SHORT = {'Option A: current Saturday': 'A: booked quotes', 'Option B: a Friday, three weeks later': 'B: weekday quotes', 'Option C: a Saturday in September': 'C: shoulder season quotes'}


def dates_d():
    out = []
    for o, qs in QUOTES.items():
        for c_, q, lead in zip(CATS5, qs, LEADS):
            out.append(dict(option=key('dopt', o), category=key('category', c_), quote=q, lead_months=lead, note=NOTES[o], option_date=iso(OPT_DATE[o])))
    return out


if __name__ == '__main__':
    for f in (budget_d, payers_d, funding_d, fsum_d, schedule_d, payments_d, vendors_d, hidden_d, tips_d, pscore_d, prank_d, bands_d, rebal_d, catpay_d, truebud_d, settle_d, due60_d, cash_d, ladder_d, dates_d):
        print(f.__name__, len(f()))
    print(OPT_DATE, [d.strftime('%A') for d in OPT_DATE.values()])
