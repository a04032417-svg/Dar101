"""QA part 2: recompute each tool's default result independently from the demo workbook tables; writes out2/qa.txt."""
import openpyxl, math, datetime as dt, os
H = os.path.dirname(os.path.abspath(__file__))
wb = openpyxl.load_workbook(H + '/out2/work/v/en-demo.xlsx', data_only=True)
def tbl(n):
    ws = wb[n]; rows = list(ws.iter_rows(min_row=4, values_only=True)); h = rows[0]
    return [{h[i]: r[i] for i in range(len(h)) if h[i]} for r in rows[1:] if r[0] is not None]
def res(sheet):
    d = {}
    for r in wb[sheet].iter_rows(min_row=5, max_col=3, values_only=True):
        if r[1] == 'What if': break
        if r[1] is not None and r[2] is not None: d.setdefault(r[1], r[2])
    return d
jobs = tbl('Jobs'); pays = tbl('Job Payments'); tit = tbl('Titles'); roy = tbl('Royalties by Month'); cash = tbl('Cash by Month'); cat = {r['Kind']: r['Typical rate'] for r in tbl('Cost Categories')}
today = dt.datetime(2026, 11, 15); msd = dt.datetime(2026, 11, 1)
T = {t['Title']: t for t in tit}
out = []; bad = []
def chk(tool, ins, items):
    r = res(tool); parts = []; ok = True
    for lab, py, tol in items:
        wv = r[lab]
        if isinstance(py, dt.datetime): good = wv == py
        elif isinstance(py, str): good = str(wv) == py
        else: good = abs(float(wv) - float(py)) <= tol
        ok &= good
        if not good: bad.append((tool, lab, wv, py))
        parts.append('%s = %s' % (lab, round(py, 3) if isinstance(py, float) else (py.date() if isinstance(py, dt.datetime) else py)))
    out.append('%s: %s -> %s (%s)' % (tool, ins, ', '.join(parts), 'checked' if ok else 'MISMATCH'))
def tcost(tid): return sum(j['Quote'] for j in jobs if j['Title ID'] == tid)
def avg6(title):
    v = [r['Royalties'] for r in roy if r['Title'] == title and dt.datetime(2026, 5, 1) <= r['Month'] < msd]
    return sum(v) / len(v) if v else 0
def months_on_sale(t): return max(0, int((today - t['Release date']).days / 30.4375))
CN = cash[[c['Month'] for c in cash].index(msd)]['Closing cash']

g = "The Glassmaker's Orchard"; t = T[g]; cost = tcost(t['Title ID']); gap = max(0, cost - t['Royalties to date']); mo = gap / avg6(g)
chk('Title Payback Verdict', 'title = %s, sales change = 0' % g, [('Production cost ($)', cost, .01), ('Royalties to date ($)', t['Royalties to date'], .01), ('Still to earn back ($)', round(gap), 1), ('Months on sale', months_on_sale(t), 0),
    ('Own monthly average, last 6 months ($)', avg6(g), .01), ('Months still needed at that pace', mo, .06), ('Verdict', 'Behind' if months_on_sale(t) + mo > 24 else 'On track', 0)])
rpc = 22.99 * .4; be = math.ceil(5720 / rpc)
chk('Break-Even Copies Solver', 'cost = 5720, price = 22.99, share = 0.4, unit cost = 0, sold = 10, pace = 2, allowed = 24', [('Royalty per copy ($)', rpc, .001), ('Break-even copies', be, 0), ('Copies still needed', be - 10, 0),
    ('Months left at the pace', (be - 10) / 2, .06), ('Copies a month needed to pay back in time', (be - 10) / 24, .06), ('Share of break-even reached', 10 / be, .0005), ('Verdict', 'Behind', 0)])
def typ(j): return cat[j['Kind']] * j['Units, thousand words or hours'] if (j['Units, thousand words or hours'] or 0) > 0 else cat[j['Kind']]
ov = {}; tot = 0
for j in jobs:
    if j['Kind'] == 'Setup and identifiers': continue
    d = j['Quote'] - typ(j); ov[j['Title ID']] = ov.get(j['Title ID'], 0) + d; tot += max(0, d)
top = max(ov, key=lambda k: ov[k])
chk('Budget vs Actual Ranker', 'rank = 1, tolerance = 0.1', [('Title at this rank', [x['Title'] for x in tit if x['Title ID'] == top][0], 0), ('Production cost of the title ($)', tcost(top), .01),
    ('Over (+) or under (-) your typical rates ($)', ov[top], .05), ('Total over your typical rates, all jobs ($)', tot, .1), ('Verdict', 'Renegotiate the next quote', 0)])
op = [p for p in pays if p['Status'] != 'Paid' and p['Date'] <= today + dt.timedelta(days=3)]; due = sum(p['Amount'] for p in op); lg = max(op, key=lambda p: p['Amount'])
chk('Invoice Cash Test', 'days = 3, other cash out = 0, floor = 8000', [('Cash now ($)', CN, 0), ('Invoices due in that time', len(op), 0), ('Amount due ($)', due, .01), ('Largest invoice ($)', lg['Amount'], .01),
    ('Contractor of the largest invoice', lg['Contractor'], 0), ('Cash after paying them all ($)', CN - due, .01), ('Cash after paying the largest invoice alone ($)', CN - lg['Amount'], .01), ('Amount to move to a later date ($)', 8000 - (CN - due), .01), ('Verdict', 'Ask to split', 0)])
nj = [j for j in jobs if j['Kind'] == 'Narration' and (j['Units, thousand words or hours'] or 0) > 0]; av = sum(j['Quote'] for j in nj) / sum(j['Units, thousand words or hours'] for j in nj)
chk('Unit Cost Test', 'kind = Narration, quote = 5000, units = 11', [('Cost per unit ($)', 5000 / 11, .01), ('Own average per unit for this kind ($)', av, .05), ('Difference from your own average', 5000 / 11 / av - 1, .002), ('Quote that matches your average ($)', av * 11, 1), ('Verdict', 'High', 0)])
CE = tbl('Cost per Edition')
def ebm(title):
    e = [x for x in CE if x['Title'] == title and x['Format'] == 'Ebook'][0]; return e['Copies a month since release'], 0
c, m = ebm('The Pale Bell Ringers'); em = res('Audio Go or No-go')['Ebook copies a month for this title']
assert abs(em - c) < .06, (em, c)
w = T['The Pale Bell Ringers']['Words']; cost = round(285 * w / 9300 + 150); r_ = 17.99 * .4; mid = em * .09
chk('Audio Go or No-go', 'title = The Pale Bell Ringers, rate = 285, extra = 150, price = 17.99, share = 0.4, ratio = 0.09, ebook copies a month = %s' % em, [('One-off cost ($)', cost, 1), ('Royalty per copy ($)', r_, .001),
    ('Copies a month, mid', mid, .06), ('Payback months, mid', cost / (mid * r_), .15), ('Payback months, low', cost / (mid * .5 * r_), .3), ('Payback months, high', cost / (mid * 1.6 * r_), .2), ('Verdict', 'Skip' if cost / (mid * r_) > 24 else 'Produce', 0)])
for sh, nm, fc, pr, sh_, pc, ra, ex in [('Large Print Go or No-go', 'Large print go or no-go', 300, 17.99, .6, 5.4, .05, 0), ('Hardcover Go or No-go', 'Hardcover go or no-go', 340, 24.99, .6, 11, .035, 0)]:
    r_ = pr * sh_ - pc; mid = em * ra; pm = fc / (mid * r_)
    chk(sh, 'title = The Pale Bell Ringers, cost = %d, price = %s, share = %s, print cost = %s, ratio = %s, ebook copies a month = %s' % (fc, pr, sh_, pc, ra, em), [('One-off cost ($)', fc, .01), ('Royalty per copy ($)', r_, .001), ('Copies a month, mid', mid, .06),
        ('Payback months, mid', pm, .15), ('Payback months, low', fc / (mid * .5 * r_), .3), ('Payback months, high', fc / (mid * 1.6 * r_), .2), ('Verdict', 'Produce' if pm <= 12 else ('Wait' if pm <= 24 else 'Skip'), 0)])
tc = 55 * 78 + 380 + 260; rp = 5.99 * .7 - .12; pm = tc / (40 * rp); net = 40 * 24 * rp - tc
chk('Translation Business Case', 'title = The Salt Pier Letter, German, rate = 55, edit = 380, cover = 260, price = 5.99, share = 0.7, delivery = 0.12, copies = 40, look ahead = 24, fee = 1800', [('Translation cost ($)', 55 * 78, .01), ('Total cost with edit and cover ($)', tc, .01),
    ('Royalty per copy ($)', rp, .001), ('Payback months, low (half the copies)', tc / (20 * rp), .06), ('Payback months, mid', pm, .06), ('Payback months, high (1.6 times the copies)', tc / (64 * rp), .06), ('Net after the months you look ahead, mid ($)', net, .05), ('Verdict', 'Sell the rights instead' if net < 1800 else 'Translate', 0)])
sal = avg6('The Salt Pier Letter'); ser = [x for x in tit if x['Series'] == 'The Ember Crown' and x['Status'] == 'Released']; sa = sum(avg6(x['Title']) for x in ser) / len(ser); sc = sum(tcost(x['Title ID']) for x in ser) / len(ser)
tr = sal * .3
chk('Translate or Write', 'book = The Salt Pier Letter, series = The Ember Crown, translate cost = 4930, share = 0.3, new book cost = 5200', [('Own monthly average of the book, last 6 months ($)', sal, .5), ('Expected royalties a month, translation ($)', tr, .6),
    ('Own average monthly royalties of a book in the series ($)', sa, .6), ('Own average cost of a book in the series ($)', sc, .6), ('Royalties a month per 1,000 spent, translation ($)', round(tr) / 4.93, .1), ('Royalties a month per 1,000 spent, new book ($)', sa / 5.2, .1),
    ('Months to pay back, translation', 4930 / tr, .06), ('Months to pay back, new book', 5200 / sa, .06), ('Verdict', 'Write', 0)])
chk('Payment Scheduler', 'quote = 3200, deposit = 0.25, milestone = 0.35, start = 2026-11-15, due = 2027-01-29, final after 10 days', [('Deposit ($)', 800, .01), ('Milestone payment ($)', 1120, .01), ('Final payment ($)', 3200 - 800 - 1120, .01),
    ('Final payment date', dt.datetime(2027, 2, 8), 0), ('Cash after the deposit ($)', CN - 800, 0), ('Verdict', 'Schedule fits', 0)])
p12 = {}
for p in pays:
    if p['Status'] == 'Paid' and today - dt.timedelta(days=365) <= p['Date'] <= today: p12[p['Contractor']] = p12.get(p['Contractor'], 0) + p['Amount']
s = sorted(p12.items(), key=lambda x: -x[1]); T12 = sum(p12.values())
chk('Contractor Concentration', 'limit = 0.35, new job = 0', [('Production paid, last 12 months ($)', T12, .05), ('Contractors paid in 12 months', len(p12), 0), ('Largest contractor', s[0][0], 0), ('Share of the largest', s[0][1] / T12, .0005),
    ('Second share', s[1][1] / T12, .0005), ('Share of the three largest together', sum(x[1] for x in s[:3]) / T12, .0005), ('Verdict', 'Spread the work', 0)])
cj = [j for j in jobs if j['Kind'] == 'Copy edit' and (j['Units, thousand words or hours'] or 0) > 0]; av = sum(j['Quote'] for j in cj) / sum(j['Units, thousand words or hours'] for j in cj)
f = lambda q, d: .7 * (av / (q / 98)) + .3 * (25 / d); S = {'A': f(1830, 28), 'B': f(1990, 25), 'C': f(1760, 45)}
chk('Quote Chooser', 'Copy edit, 98 units, A 1830 in 28 days, B 1990 in 25, C 1760 in 45, weight = 0.7', [('Own average per unit for this kind ($)', av, .02), ('Price per unit, A ($)', 1830 / 98, .01), ('A against your average', 1830 / 98 / av - 1, .002),
    ('Score A', S['A'], .002), ('Score B', S['B'], .002), ('Score C', S['C'], .002), ('Verdict', 'Choose ' + max(S, key=S.get), 0)])
kj = [j for j in jobs if j['Title'] == 'The Kelp Throne']; ce = [j for j in kj if j['Kind'] == 'Copy edit'][0]; last = max(j['Due date'] for j in kj); rel = T['The Kelp Throne']['Release date']; late = (today - ce['Due date']).days
chk('Late Job Impact', 'title = The Kelp Throne, late job = Copy edit, further days = 0', [('Days late now', late, 0), ('Jobs of the title due after it', sum(1 for j in kj if j['Due date'] > ce['Due date']), 0), ('Due date of the last job of the title', last, 0),
    ('Days between the last job and the release', (rel - last).days, 0), ('Days the release must move', max(0, late - (rel - last).days), 0), ('Verdict', 'Absorb the delay', 0)])
rel_ = [x for x in tit if x['Status'] == 'Released']; oc = sum(tcost(x['Title ID']) for x in rel_) / len(rel_); orr = sum(avg6(x['Title']) for x in rel_) / len(rel_)
chk('Cost Cap per Title', 'months = 18, royalties a month = 420, plan = 5200, royalty per copy = 3.4', [('Largest budget (months times royalties a month) ($)', 7560, .01), ('Planned budget over (+) or under (-) the cap ($)', 5200 - 7560, .01),
    ('Copies a month needed to pay back the plan', 5200 / 18 / 3.4, .6), ('Royalties a month needed for the plan ($)', 5200 / 18, .6), ('Own average cost of a released title ($)', oc, 1), ('Own average monthly royalties of a released title ($)', orr, 1), ('Verdict', 'Within the cap', 0)])
chk('Series Budget Planner', 'series = The Ember Crown, books left = 2, cost per book = 5200', [('Released books in the series', len(ser), 0), ('Own average cost of a book in the series ($)', sc, .6), ('Own average monthly royalties of a book ($)', sa, .6),
    ('Budget for the books left ($)', 10400, .01), ('Expected royalties a month from the new books ($)', 2 * sa, 1.1), ('Months to pay back the budget', 10400 / (2 * sa), .06), ('Verdict', 'Affordable', 0)])
dl = [x for x in CE if x['Title'] == 'The Drowned Ledger']; cm0 = sum(x['Copies a month since release'] for x in dl); rp0 = sum(x['Royalties earned to date'] for x in dl) / sum(x['Copies sold to date'] for x in dl)
r = res('Cover Refresh Test'); cm = r['Copies a month now, all formats']; rpcc = r['Royalty per copy, all formats ($)']; xt = 550 / 12 / rpcc
assert abs(cm - cm0) < .6 and abs(rpcc - rp0) < .02, (cm, cm0, rpcc, rp0)
chk('Cover Refresh Test', 'title = The Drowned Ledger, cover = 550, months = 12, lift = 0.15, copies a month now = %s, royalty per copy = %s' % (cm, rpcc), [('Extra copies a month needed', xt, .06), ('Lift needed', xt / cm, .0006), ('Extra royalties a month needed ($)', 550 / 12, .6), ('Verdict', 'Refresh the cover' if xt / cm <= .15 else 'Hold', 0)])
chk('Payback What-if', 'title = %s, target = 24' % g, [('Still to earn back ($)', round(gap), 1), ('Months on sale', months_on_sale(T[g]), 0), ('Months still needed, sales down 20%', gap / (.8 * avg6(g)), .06), ('Months still needed, sales down 10%', gap / (.9 * avg6(g)), .06),
    ('Months still needed, sales as now', gap / avg6(g), .06), ('Months still needed, sales up 10%', gap / (1.1 * avg6(g)), .06), ('Months still needed, sales up 20%', gap / (1.2 * avg6(g)), .06), ('Verdict', 'Sensitive', 0)])
open(H + '/out2/qa.txt', 'w').write('\n'.join(out) + '\n')
print(len(out), 'lines'); print('MISMATCH', bad)
