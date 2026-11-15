"""Independent check of the 18 tools of part 6: every default result is recomputed in Python from au_core and compared with the recalculated workbook; writes out6/qa.txt"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import au6_data as DD
from au6_lists import *
from openpyxl import load_workbook
wb = load_workbook('out6/work/v/en-demo.xlsx', data_only=True)
MS0 = month_start(0)
def mi(k): return iso(month_start(k))
def win(m, a, b=0): return mi(a) <= m < mi(b)
AG = DD._AGG
TIT = {t['title_id']: t for t in DD.TITLES}
def roy(tid, a=12, b=0): return sum(v[1] for (t, m), v in AG.items() if t == tid and win(m, a, b))
def cop(tid, a=12, b=0): return sum(v[0] for (t, m), v in AG.items() if t == tid and win(m, a, b))
def adsp(tid): return sum(a for (t, m), (a, p) in DD._CST.items() if t == tid and win(m, 12))
def age(t):
    rd = to_date(t['release_date']); return max(0, (TODAY.year - rd.year) * 12 + TODAY.month - rd.month)
def tid_of(name): return DD.TBYNAME[name]['title_id']
def out(sheet):
    ws = wb[sheet]; res = {}; inp = {}; mode = None
    for r in range(1, 70):
        b, c = ws.cell(r, 2).value, ws.cell(r, 3).value
        if b == 'Inputs': mode = 'i'; continue
        if b == 'Results': mode = 'o'; continue
        if b == 'What if': break
        if mode and b is not None: (inp if mode == 'i' else res)[str(b).replace(' ($)', '')] = c
    return inp, res
lines = []; bad = 0
def chk(name, sheet, pairs, fmt):
    """pairs: output label -> expected"""
    global bad
    inp, res = out(sheet); ok = True; parts = []
    for lab, exp in pairs.items():
        got = res[lab]
        if isinstance(exp, str): good = (got == exp)
        elif hasattr(exp, 'isoformat'): good = (got.date() == exp)
        else: good = abs(float(got) - exp) <= max(0.1, abs(exp) * 1e-5)
        if not good: ok = False; print('MISMATCH', name, lab, got, exp)
        parts.append('%s = %s' % (lab, (round(exp, 4) if isinstance(exp, float) else (exp.isoformat() if hasattr(exp, 'isoformat') else exp))))
    bad += (not ok)
    lines.append('%s: %s -> %s (%s)' % (name, fmt, ', '.join(parts), 'checked' if ok else 'MISMATCH'))

# 1 series money case
inp, _ = out('Series Money Case')
B, CE, G, B1, R1, RL, RY = 5, 4200.0, 3, 300.0, 0.55, 0.90, 3.0
def chainf(k, m=1.0): return 1.0 if k == 1 else (R1 * m if k == 2 else R1 * m * RL ** (k - 2))
def copies(m=1.0): return sum(B1 * chainf(k, m) * max(0, 24 - (k - 1) * G) for k in range(1, B + 1))
nets = [B1 * chainf(k) * max(0, 24 - (k - 1) * G) * RY - CE for k in range(1, B + 1)]
chk('Series money case', 'Series Money Case', {'Copies in 24 months': copies(), 'Royalties in 24 months': copies() * RY, 'Net after production cost': copies() * RY - B * CE,
    'Months to earn back the cost (average pace)': B * CE / (copies() * RY / 24), 'Royalties, worst case (read-through 20% lower)': copies(0.8) * RY, 'Net of book 5': nets[4], 'Verdict': 'Build the series'},
    'books = 5, cost each = 4200, gap = 3, copies book 1 = 300, read-through = 0.55 and 0.90, royalty per copy = 3.00')
# 2 books to reach a target
now = sum(roy(t) for t in TIT) / 12; gap = max(0, 14000 - now); per = 540 * 1.05; n = math.ceil(gap / per)
chk('Books to reach a target', 'Books to Reach a Target', {'Royalties a month now (last 12 months)': now, 'Gap to the target': gap, 'Added by one new book (with the lift)': per, 'Books needed': float(n),
    'Months at your pace': n / 2 * 12, 'Verdict': '%d more books at this pace' % n}, 'target = 14000, new book = 540, lift = 0.05, books a year = 2, cap = 8')
# 3 read-through by step
a, b = tid_of('The Tidebound Cartographer'), tid_of('Salt and Lantern Sky'); ca_, cb = cop(a), cop(b); short = ca_ * 0.25 - cb; rcopy = roy(b) / cb
chk('Step read-through verdict', 'Step Read-through Verdict', {'Copies of book n': float(ca_), 'Copies of book n+1': float(cb), 'Read-through': cb / ca_, 'Copies short of the threshold': float(round(short + 1e-9)),
    'Royalties those copies bring in a year': short * 0.5 * rcopy, 'Verdict': 'Book 2 needs work (Tidebound Realms, Step 1)'}, 'series = Tidebound Realms, step = Step 1, gap closed = 0.5')
# 4 where readers drop
steps = []
for s, ts in DD.CHAIN:
    for x, y in zip(ts, ts[1:]):
        steps.append((max(0, cop(x['title_id']) - cop(y['title_id'])), s, x['series_order'], x['title'], y['title_id']))
steps.sort(reverse=True); tot = sum(x[0] for x in steps); first = steps[0]; vlost = first[0] * roy(first[4]) / cop(first[4])
chk('Drop fix first', 'Drop Fix First', {'Readers lost, all steps': float(tot), 'First: readers lost': float(first[0]), 'First: share of all readers lost': first[0] / tot, 'Royalties those readers bring': vlost * 0.10,
    'Verdict': 'Fix first: %s, Step %d (%s)' % (first[1], first[2], first[3])}, 'share you could win back = 0.10')
# 5 reader value (Lantern Bay)
ts = [t for t in DD.CHAIN if t[0] == 'Lantern Bay Mysteries'][0][1]; c1 = cop(ts[0]['title_id']); val = 0.0
for t in ts: val += cop(t['title_id']) / c1 * roy(t['title_id']) / cop(t['title_id'])
ad1 = adsp(ts[0]['title_id']) / c1
chk('Reader value and ad ceiling', 'Reader Value and Ad Ceiling', {'Copies of book 1, last 12 months': float(c1), 'Royalty per copy of book 1': roy(ts[0]['title_id']) / c1, 'Value of a book-1 reader over the series': val,
    'Ad ceiling at your share': val * 0.35, 'Your ad spend per copy of book 1': ad1, 'Verdict': 'Ads justified up to a cost per sale of %s' % ('%g' % round(val * 0.35, 2) if len('%g' % round(val * 0.35, 2)) else '')},
    'series = Lantern Bay Mysteries, share accepted as ad cost = 0.35')
# 6 price test
rn, rw = 2.99 * 0.70, 0.99 * 0.35; tn = 300 * (rn + 3.0); tw = 300 * 1.4 * (rw + 3.0)
chk('Book 1 price test', 'Book 1 Price Test', {'Royalty per copy now': rn, 'Royalty per copy at the new price': rw, 'Copies needed to hold the book 1 royalties': float(round(300 * rn / rw)),
    'Total a month now': tn, 'Total a month at the new price': tw, 'Change a month': tw - tn, 'Verdict': 'Keep the price'}, 'price 2.99 -> 0.99, shares 0.70 -> 0.35, copies = 300, lift = 0.40, later books = 3.00')
# 7/8/18 pen names
def pen_month(p, m):
    r = sum(v[1] for (t, mm), v in AG.items() if mm == m and TIT[t]['pen_name'] == p)
    d = sum(a + pp for (t, mm), (a, pp) in DD._CST.items() if mm == m and TIT[t]['pen_name'] == p) + sum(x['amount'] for x in expense_rows() if x['month'] == m and x['pen_name'] == p)
    return r, d
def shared(m): return sum(x['amount'] for x in expense_rows() if x['month'] == m and x['pen_name'] == 'Shared')
def rev_tot(m): return sum(v[1] for (t, mm), v in AG.items() if mm == m)
def ntit(p, m): return sum(1 for t in DD.TITLES if (p is None or t['pen_name'] == p) and to_date(t['release_date']) <= add_months(to_date(m), 1) - day(1))
def prof(p, m, rule):
    r, d = pen_month(p, m); S = shared(m)
    sh = {'eq': S / 2, 'rev': S * r / rev_tot(m) if rev_tot(m) else 0, 'tit': S * ntit(p, m) / ntit(None, m)}[rule]
    return r, d, sh, r - d - sh
def span(a, b): return [mi(k) for k in range(a, b, -1)]
P = PEN_NAMES; mons = span(11, 0)
R = {p: [sum(prof(p, m, 'rev')[i] for m in mons) for i in range(4)] for p in P}
mg = {p: R[p][3] / R[p][0] for p in P}
chk('Pen-name profit verdict', 'Pen-name Profit Verdict', {'Tamsin Hartwell: revenue': R[P[0]][0], 'Tamsin Hartwell: direct costs': R[P[0]][1], 'Tamsin Hartwell: shared costs': R[P[0]][2], 'Tamsin Hartwell: profit': R[P[0]][3],
    'Tamsin Hartwell: margin': mg[P[0]], 'Corvin Ashdale: profit': R[P[1]][3], 'Corvin Ashdale: margin': mg[P[1]], 'Verdict': 'Feed pen name ' + (P[0] if mg[P[0]] > mg[P[1]] else P[1])},
    'months = 11, balanced within 0.05, rule on Start = By revenue')
pr = {(p, ru): sum(prof(p, m, ru)[3] for m in mons) for p in P for ru in ('eq', 'rev', 'tit')}
gaps = {ru: abs(pr[(P[0], ru)] / R[P[0]][0] - pr[(P[1], ru)] / R[P[1]][0]) for ru in ('eq', 'rev', 'tit')}
best = min(gaps, key=gaps.get)
sw = max(max(sum(prof(p, m, ru)[2] for m in mons) for ru in ('eq', 'rev', 'tit')) - min(sum(prof(p, m, ru)[2] for m in mons) for ru in ('eq', 'rev', 'tit')) for p in P)
chk('Shared cost rule comparer', 'Shared Cost Rule Comparer', {'Tamsin Hartwell: profit, equal rule': pr[(P[0], 'eq')], 'Corvin Ashdale: profit, by titles': pr[(P[1], 'tit')], 'Margin gap, equal rule': gaps['eq'],
    'Margin gap, by revenue': gaps['rev'], 'Largest swing between rules for one pen name': sw, 'Verdict': 'Fairest rule is ' + {'eq': 'Equal', 'rev': 'By revenue', 'tit': 'By titles'}[best]}, 'months = 11')
# pen growth
cur, prv = mons, span(22, 11)
def pr_roy(p, ms_): return sum(pen_month(p, m)[0] for m in ms_)
g = {p: pr_roy(p, cur) / pr_roy(p, prv) - 1 for p in P}
added = {p: sum(1 for t in DD.TITLES if t['pen_name'] == p and mi(11) <= t['release_date'] < mi(0)) for p in P}
chk('Pen-name growth compare', 'Pen-name Growth Compare', {'Tamsin Hartwell: royalties, latest period': pr_roy(P[0], cur), 'Tamsin Hartwell: royalties, period before': pr_roy(P[0], prv), 'Tamsin Hartwell: growth': g[P[0]],
    'Corvin Ashdale: growth': g[P[1]], 'Tamsin Hartwell: titles added': float(added[P[0]]), 'Verdict': 'Pen name %s is growing faster' % (P[0] if g[P[0]] > g[P[1]] else P[1])}, 'months in each period = 11, level within 0.02')
# 9 box set
bx = 60 * 10.99 * 0.7 - 25 * 5.99 * 0.7; netc = 10.99 * 0.7 - 25 / 60.0 * 5.99 * 0.7
chk('Box set case', 'Box Set Case', {'Extra income a month': bx, 'Net gain per box set copy': netc, 'Break-even box set copies': float(math.ceil(880 / netc)), 'Months to earn back the set-up cost': 880 / bx,
    'Income in the first year after cost': bx * 12 - 880, 'Verdict': 'Make the box set'}, 'books 3, single 5.99, box 10.99, share 0.70, copies 60, taken 25, set-up 880, limit 12 months')
# 10 bundle check
box = tid_of('The Ember Crown Books 1-3'); rd = to_date(TIT[box]['release_date']); st = add_months(dt.date(rd.year, rd.month, 1), 1)
singles = [t['title_id'] for t in DD.TITLES if t['series'] == 'The Ember Crown' and t['series_order'] <= 3]
def sroy(ids, a, n): return sum(AG.get((i, iso(add_months(st, a + j))), [0, 0])[1] for i in ids for j in range(n))
bef, aft, bxr = sroy(singles, -4, 3), sroy(singles, 0, 3), sroy([box], 0, 3)
chk('Bundle cannibalisation check', 'Bundle Cannibalisation Check', {'Single books, royalties before': bef, 'Single books, royalties after': aft, 'Box set royalties after': bxr, 'Change against the singles before': (aft + bxr) / bef - 1,
    'Verdict': 'Bundle adds' if aft + bxr >= bef else 'Bundle swaps'}, 'box set = The Ember Crown Books 1-3, series = The Ember Crown, last single book = 3, months = 3')
# 11 catalogue decision (Glassmaker)
g_ = tid_of("The Glassmaker's Orchard"); r12 = roy(g_); left = max(0, title_cost(g_) - title_royalty(g_)); l3, p3 = roy(g_, 3, 0), roy(g_, 6, 3)
chk('Catalogue decision', 'Catalogue Decision', {'Verdict': 'Repackage', 'Reason': 'Cost not earned back', 'Royalties, last 12 months': r12, 'Cost left to recover': left, 'Change, last 3 months': l3 / p3 - 1,
    'Yearly return': r12 / title_cost(g_), 'Months to earn back the cost left': left / (r12 / 12), 'Age (months)': float(age(TIT[g_]))}, "title = The Glassmaker's Orchard, change in pace = 0")
# 12 return test
chk('Return test verdict', 'Return Test Verdict', {'Production cost': title_cost(g_), 'Yearly return': r12 / title_cost(g_), 'Royalties a month needed to pass': title_cost(g_) * 0.10 / 12,
    'Titles tested': 20.0, 'Titles that fail at this target': float(sum(1 for t in DD.TITLES if t['status'] == 'Released' and roy(t['title_id']) / title_cost(t['title_id']) < 0.10)), 'Verdict': 'Passes'},
    "title = The Glassmaker's Orchard, target = 0.10")
# 13 trend
pb = tid_of('The Pale Bell Ringers'); l3, p3, y3 = roy(pb, 3, 0), roy(pb, 6, 3), roy(pb, 15, 12)
chk('Title trend verdict', 'Title Trend Verdict', {'Last 3 months': l3, 'Previous 3 months': p3, 'Same 3 months last year': y3, 'Change against previous 3 months': l3 / p3 - 1, 'Change against last year': l3 / y3 - 1,
    'Your 3-month average': roy(pb) / 4, 'Verdict': 'Declining'}, 'title = The Pale Bell Ringers, flag = 0.20')
# 14 completion
lb = [t for t in DD.CHAIN if t[0] == 'Lantern Bay Mysteries'][0][1]; sr = sum(roy(t['title_id']) for t in lb); rel = [t for t in DD.TITLES if t['status'] == 'Released']
avg_all = sum(roy(t['title_id']) for t in rel) / len(rel); fin = 1 * sr / 6 + 0.05 * sr
earl = [t['title_id'] for t in lb[:-1]]; st2 = add_months(dt.date(2026, 6, 1), 1)
lb_bef = sum(AG.get((i, iso(add_months(st2, -4 + j))), [0, 0])[1] for i in earl for j in range(3)); lb_aft = sum(AG.get((i, iso(add_months(st2, j))), [0, 0])[1] for i in earl for j in range(3))
chk('Series completion value', 'Series Completion Value', {'Royalties of the series, last 12 months': sr, 'Average royalties a released book': sr / 6, 'Lift measured in your own history': lb_aft / lb_bef - 1,
    'Extra royalties in 12 months if you finish': fin, 'Same books as a new series, average title': avg_all, 'Verdict': 'Finish the series' if fin >= avg_all else 'Start a new series'},
    'series = Lantern Bay Mysteries, books left = 1, lift = 0.05')
# 15 next book
c3 = 5200 * 0.08 + 410 * 0.7
chk('Next book forecast', 'Next Book Forecast', {'Copies in 3 months, Base': c3, 'Copies in 3 months, Worst': c3 * 0.7, 'Royalties in 3 months, Base': c3 * 3.1, 'Months to earn back the cost, Base': 4750 / (c3 * 3.1 / 3),
    'Months to earn back the cost, Worst': 4750 / (c3 * 3.1 * 0.7 / 3), 'Verdict': 'Expected to earn back'}, 'list = 5200, launch share = 0.08, previous copies = 410, read-through = 0.70, royalty = 3.10, cost = 4750, horizon = 12')
# 16 backlist
tot12 = sum(roy(t['title_id']) for t in DD.TITLES); old = sum(roy(t['title_id']) for t in DD.TITLES if age(t) > 12); old24 = sum(roy(t['title_id']) for t in DD.TITLES if age(t) > 24)
chk('Backlist against frontlist', 'Backlist against Frontlist', {'Royalties, last 12 months': tot12, 'From titles older than the first age': old, 'Backlist share': old / tot12, 'Share from the older titles': old24 / tot12,
    'Verdict': 'Backlist carries %d%%' % round(old / tot12 * 100)}, 'backlist after = 12 months, strong backlist after = 24 months, pivot = 0.50')
# 17 top 3
rs = sorted((roy(t['title_id']) for t in DD.TITLES), reverse=True); names = sorted(DD.TITLES, key=lambda t: -roy(t['title_id']))
chk('Top title dependence', 'Top Title Dependence', {'Share of the top titles': sum(rs[:3]) / tot12, 'Royalties from outside the top titles': tot12 - sum(rs[:3]), 'Top title': names[0]['title'],
    'Income a month lost if the top title stopped': rs[0] / 12, 'Verdict': 'Dependence is ok'}, 'top titles = 3, highest share accepted = 0.40')
open('out6/qa.txt', 'w').write('\n'.join(lines) + '\n')
print('\n'.join(l[:260] for l in lines)); print('mismatches', bad)
