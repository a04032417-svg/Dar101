"""QA of part 7: recompute each tool's default result in Python from au_core and compare with the recalculated demo workbook; writes out7/qa.txt."""
import sys, os, math, collections, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from au_core import *
from openpyxl import load_workbook
wb = load_workbook(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out7/work/v/en-demo.xlsx'), data_only=True)
def val(sheet, label):
    ws = wb[sheet]
    for exact in (True, False):
        seen_results = False
        for r in ws.iter_rows(min_row=1, max_row=60):
            if r[1].value == 'Results': seen_results = True
            if not seen_results: continue
            t = str(r[1].value or '').replace(' ($)', '')
            if r[2].value is not None and ((t == label) if exact else t.startswith(label)): return r[2].value
    raise KeyError((sheet, label))
out = []; bad = 0
def chk(tool, ins, pairs):
    global bad
    parts = []
    for label, mine, fmt in pairs:
        got = val(tool, label)
        if isinstance(got, (dt.datetime,)): got = got.date().isoformat()
        ok = (got == mine) if isinstance(mine, str) else abs(got - mine) < 0.011 * max(1, abs(mine)) / 1.0 if False else (got == mine if isinstance(mine, str) else abs(got - mine) < 0.006 + 1e-6 * abs(mine))
        if not ok: bad += 1
        parts.append('%s = %s' % (label, fmt % mine if not isinstance(mine, str) else mine) + ('' if ok else ' MISMATCH(workbook %s)' % got))
    out.append('%s: %s -> %s (checked)' % (tool, ins, ', '.join(parts)))
f2 = '%.2f'; f0 = '%d'
# data
ORDS = direct_order_rows(); PNL = pnl_rows(); EVS = event_rows(); ED = {e['edition_id']: e for e in edition_rows()}; STK = stock_rows(); DEALS = deal_rows(); INST = instalment_rows(); ELS = event_sale_rows()
ms = month_start(0); lo = add_months(ms, -12)
import au7_data as D7
DM = [m for m in D7.dmonth_d() if to_date(m['month']) > lo]
def dnet(m): return m['gross'] - m['discounts'] + m['shipping_charged'] - m['fees'] - m['delivery']
D12 = sum(dnet(m) for m in DM); R12 = sum(m['all_revenue'] for m in DM); C12 = sum(m['copies'] for m in DM)
# 1
price, disc, ship, fp, ff, dl, tx, st = 14.99, 0, 4.0, 0.029, 0.3, 8.85, 0.1, 3.34
tax = (price - disc + ship) * tx; pays = price - disc + ship + tax; fee = pays * fp + ff; net = price - disc + ship - fee - dl
chk('Direct Store Margin', 'price = 14.99, discount = 0, shipping = 4, fee = 2.9% + 0.30, delivery = 8.85, tax = 10%, store pays = 3.34', [('Payment fee', fee, '%.3f'), ('Direct net per item', net, '%.3f'), ('Direct minus store', net - st, '%.3f'), ('Verdict', 'Direct pays more', '%s')])
low = (5 + ff + dl) / (1 - fp) - ship
chk('Direct Price Solver', 'net wanted = 5, delivery = 8.85, shipping = 4, fee = 2.9% + 0.30, price = 14.99', [('Lowest price that holds your net', low, '%.3f'), ('Net per copy at your price', (price + ship) * (1 - fp) - ff - dl, '%.3f'), ('Largest discount in money', price - low, '%.3f'), ('Verdict', 'Price holds', '%s')])
need = 0.15 * (R12 - D12) / 0.85; mon = math.log(need / D12) / math.log(1.02)
chk('Direct Share Tracker', 'goal = 15%, growth = 2%, store royalty = 3.00, months allowed = 12', [('Direct net, last 12 months', D12, f2), ('All revenue, last 12 months', R12, f2), ('Direct share of income', D12 / R12, '%.4f'), ('Extra direct net needed', need - D12, f2),
    ('Copies to move from stores in a year', math.ceil((need - D12) / (D12 / C12 - 3)), f0), ('Months to reach the goal at your growth', mon, '%.2f'), ('Verdict', 'Behind', '%s')])
mv = 600 * 0.15; ex = mv * (5.1 - 3.3)
chk('Direct against Store Switch', 'store copies = 600, share moved = 15%, store pays 3.30, direct nets 5.10, set-up = 180, payback limit = 6', [('Copies moved a month', mv, f0), ('Extra net a month', ex, f2), ('Payback in months', 180 / ex, '%.3f'),
    ('Direct share after the move', (D12 + mv * 5.1 * 12) / (R12 + ex * 12), '%.4f'), ('Verdict', 'Worth moving', '%s')])
pc = 1 + 340 * 0.0125
chk('Print Margin per Copy', 'pages = 340, fixed = 1.00, per page = 0.0125, price = 14.99, share = 60%, shipping = 0.80, target = 55%', [('Print cost per copy', pc, f2), ('Royalty a store pays per copy', 14.99 * 0.6 - pc, '%.3f'), ('Margin on a hand-sold copy', 14.99 - pc - 0.8, f2),
    ('Margin percent', (14.99 - pc - 0.8) / 14.99, '%.4f'), ('Lowest price that holds your margin', (pc + 0.8) / 0.45, '%.3f'), ('Verdict', 'Margin holds', '%s')])
oc = 50 * 5.65 + 40
chk('Author Copy Cost', 'copies = 50, printer price = 5.65, shipping = 40, price = 14.99, needed = 45, sell-through = 70%', [('Cost of the order', oc, f2), ('Cost per copy with shipping', oc / 50, f2), ('Margin per copy', 14.99 - oc / 50, f2), ('Margin at your usual sell-through', 35 * 14.99 - oc, f2),
    ('Most copies worth ordering', 54, f0), ('Verdict', 'Order now', '%s')])
chk('Minimum Print Price', 'margin = 55%, fixed = 1.00, per page = 0.0125, shipping = 0.80, rise = 10%, book = 340 pages at 14.99', [('Minimum price, 300 pages', (1 + 300 * 0.0125 + 0.8) / 0.45, '%.3f'), ('Minimum price, 600 pages, print cost higher', ((1 + 600 * 0.0125) * 1.1 + 0.8) / 0.45, '%.3f'),
    ('Minimum price for your book', (pc + 0.8) / 0.45, '%.3f'), ('Verdict', 'Price holds', '%s')])
mv36 = [s for s in STK if s['edition_id'] == 'ED-0036']; by = collections.Counter()
for s in mv36: by[s['move']] += s['copies']
onh = sum(s['copies'] for s in mv36)
chk('Stock Count Check', 'edition = ED-0036, counted = 5, tolerance = 0', [('Copies in (orders)', by['Order in'], f0), ('Sold at events', -by['Sold at event'], f0), ('Copies on hand by the sheet', onh, f0), ('Difference (counted minus sheet)', 5 - onh, f0),
    ('Value of the difference at cost', (5 - onh) * ED['ED-0036']['unit_cost'], f2), ('Verdict', 'Recount', '%s')])
nl = 3.1 * 21 / 30 + 12; rp = math.ceil(nl + 6); tgt = math.ceil(3.1 * 3 + 30 + 6)
chk('Reorder Point and Reprint', 'edition = ED-0036, 3.1 copies a month, events in lead 12, events in 90 days 30, lead 21 days, safety 6, cover 3 months', [('Copies on hand', onh, f0), ('Reorder point', rp, f0), ('Copies to order', tgt - onh, f0),
    ('Cost of the order at the current unit cost', (tgt - onh) * ED['ED-0036']['unit_cost'], f2), ('Verdict', 'Reprint now', '%s')])
def prof(e): return e['sales'] - e['table_fee'] - e['travel_cost'] - e['lodging_cost'] - e['cost_of_copies']
pph = [prof(e) / e['hours'] for e in EVS]; mine = (30 * 17.26 - 30 * 7.28 - 186) / 8
chk('Event Profit Check', 'table fee 150, travel 36, 0 nights, 8 hours, 30 copies at 17.26, cost 7.28 a copy, 33 subscribers', [('Profit', 30 * 17.26 - 30 * 7.28 - 186, f2), ('Profit per hour', mine, '%.3f'), ('Rank among your events', 1 + sum(1 for x in pph if x > mine), f0),
    ('Verdict', 'Go again with changes', '%s')])
fx = 240 + 105 + 2 * 110; mg = 17.5 - 7.3
chk('Event Go or Skip', 'table fee 240, travel 105, 2 nights at 110, 16 hours, 45 copies at 17.50, cost 7.30, sales fall 20%', [('Fixed costs', fx, f2), ('Copies to break even', math.ceil(fx / mg), f0), ('Expected profit', 45 * mg - fx, f2),
    ('Profit if sales fall', 45 * 0.8 * mg - fx, f2), ('Verdict', 'Skip', '%s')])
kinds = collections.defaultdict(lambda: [0.0, 0.0])
for e in EVS: kinds[e['kind']][0] += prof(e); kinds[e['kind']][1] += e['hours']
rk = sorted(kinds, key=lambda k: -kinds[k][0] / kinds[k][1])
chk('Event Kind Ranking', 'move 30 hours, judge from 2 events', [('Rank 1: kind', rk[0], '%s'), ('Rank 1: profit per hour', kinds[rk[0]][0] / kinds[rk[0]][1], '%.3f'), ('Rank 5: kind', rk[-1], '%s'),
    ('Profit added by moving the hours', 30 * (kinds[rk[0]][0] / kinds[rk[0]][1] - kinds[rk[-1]][0] / kinds[rk[-1]][1]), f2)])
sold = collections.Counter(); onhand = collections.Counter()
for s in STK:
    onhand[s['edition_id']] += s['copies']
    if s['move'] == 'Sold at event' and s['date'] > ago(365): sold[s['edition_id']] += -s['copies']
top = sorted(onhand, key=lambda i: (-sold[i], i))[:6]
evk = {e['event_id']: e['kind'] for e in EVS}; nbf = sum(1 for e in EVS if e['kind'] == 'Book fair'); tot = 0; short = 0
for i in top:
    c = sum(l['copies'] for l in ELS if l['edition_id'] == i and evk[l['event_id']] == 'Book fair'); nd = math.ceil(c / nbf * 1.2 - 1e-9); tot += min(nd, onhand[i]); short += nd > onhand[i]
chk('Stock to Take to an Event', 'kind = Book fair, spare = 20%', [('Pack 1: title', ED[top[0]]['title'], '%s'), ('Copies to pack in all', tot, f0), ('Editions with fewer copies than needed', short, f0), ('Verdict', 'Enough stock' if not short else 'Reprint first', '%s')])
d2 = [d for d in DEALS if d['deal_id'] == 'RD-02'][0]
chk('Rights Deal Ledger Tool', 'deal = RD-02, agent share to test 10%', [('Fee', d2['fee'], f2), ('Effective income', d2['fee'] * 0.85, f2), ('Effective income per year', d2['fee'] * 0.85 / 7, f2), ('Received', 1608, f2), ('Still to collect', 792, f2),
    ('Still to collect, all deals', sum(i['amount'] for i in INST if not i['received_on']), f2), ('Value of open offers', sum(d['fee'] for d in DEALS if d['status'] == 'Offer'), f2), ('Verdict', 'Collect', '%s')])
dueN = [i for i in INST if not i['received_on'] and i['due_date'] <= ahead(90)]
chk('Rights Payments Due', 'look 90 days ahead, grace 7 days', [('Payments due in the window', len(dueN), f0), ('Amount due in the window', sum(i['amount'] for i in dueN), f2), ('Payments to chase now', 0, f0), ('Verdict', 'Cash arriving', '%s')])
fut = sorted((d for d in DEALS if d['term_end'] and d['term_end'] >= iso(TODAY)), key=lambda d: d['term_end'])[0]
chk('Rights Expiry Watch', 'look 24 months, notice 90 days, renewal worth 250 a year', [('Next deal to end: title', fut['title'], '%s'), ('Days to the end', (to_date(fut['term_end']) - TODAY).days, f0), ('Net income per year of that deal', fut['fee'] * 0.85 / fut['term_years'], f2),
    ('Verdict', 'Decide by date', '%s')])
chk('Rights Offer Review', 'fee 1900, agent 15%, 7 years, costs 150, wanted 250 a year, counter above 70% of that', [('Net after your costs', 1900 * 0.85 - 150, f2), ('Net income per year', (1900 * 0.85 - 150) / 7, '%.3f'), ('Fee to counter with', (250 * 7 + 150) / 0.85, f2), ('Verdict', 'Counter', '%s')])
dn3 = sum(dnet(m) for m in D7.dmonth_d() if add_months(ms, -3) <= to_date(m['month']) < ms) / 3
ev12 = sum(prof(e) for e in EVS if e['date'] > ago(365)) / 12
base = sum(dn3 * 1.02 ** k + ev12 for k in range(1, 7))
chk('Direct and Event Forecast', 'Base, growth 2% a month, best +15%, worst -20%, target 1000 a month', [('Direct net a month, last 3 full months', dn3, f2), ('Event profit a month, last 12 months', ev12, f2), ('Six months, Base', base, f2),
    ('Six months, Worst', base * 0.8, f2), ('Average a month, chosen scenario', base / 6, f2), ('Verdict', 'Below the target', '%s')])
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out7/qa.txt'), 'w').write('\n'.join(out) + '\n')
print('\n'.join(out)); print('MISMATCHES', bad)
