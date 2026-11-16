"""QA for part 7: recompute every tool output independently from du_core and compare with the recalculated demo workbook; writes out7/qa.txt."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json, math, datetime as dt, collections as C
import openpyxl
import du_core as c

HERE = os.path.dirname(os.path.abspath(__file__))
T = c.TODAY
def ed(d, n): return c.add_months(d, n)
MS = c.month_start(0)
def dm(d, n): return ed(T, -n) < d <= T                 # last n months, like DM()
def dw(d, n): return T - dt.timedelta(days=n) <= d <= T  # last n days, like DW()
CL = {x['client_id']: x for x in c.client_rows()}; CLN = {x['client']: x for x in CL.values()}
CON = [x for x in c.contract_rows()]
for x in CON: x['source'] = CL[x['client_id']]['source']
RF = c.referral_rows(); EN = c.enquiry_rows(); MK = c.marketing_rows(); CS = c.class_session_rows(); RV = c.review_rows()
SRC = {s['source']: s for s in c.sources_ref}
CANC = 'Cancelled'; RATE = 75.0; HT = 30.0; CAC = 60.0
REFSET = {r['client_id'] for r in RF if r['client_id']}
for s in CS:
    s['cost'] = s['venue_cost'] + s['hours'] * RATE; s['profit'] = s['income'] - s['cost']
    s['be'] = math.ceil(s['cost'] / s['price'] - 1e-9); s['above'] = s['signed_up'] >= s['be']

wb = openpyxl.load_workbook(os.path.join(HERE, 'out7/work/v/en-demo.xlsx'), data_only=True)
spec = json.load(open(os.path.join(HERE, 'du7.en.json')))
def sheet_values(name):
    ws = wb[name]; d = {}
    for row in ws.iter_rows(min_row=1, max_row=40):
        vals = [x.value for x in row if x.value not in (None, '')]
        if len(vals) >= 2 and isinstance(vals[0], str) and vals[0] not in d: d[vals[0]] = vals[1]
    return d
TOOLS = {t['key']: t for t in spec['tools']}
def actual(key):
    t = TOOLS[key]; v = sheet_values(t['sheet'])
    lab = lambda s: next(k for k in v if k.startswith(s))
    return t, v, lab
lines = []; bad = []
def chk(name, tool, inputs, items, verdict):
    """items: list of (output label start, expected); a number matches within 0.01 (or 1% when large)"""
    t, v, lab = actual(tool); outs = []
    for l, e in items:
        a = v[lab(l)]
        if isinstance(e, (int, float)) and isinstance(a, (int, float)): ok = abs(a - e) <= max(0.011, abs(e) * 0.002)
        elif isinstance(e, dt.date): ok = a.date() == e if hasattr(a, 'date') else a == e
        else: ok = str(a) == str(e)
        if not ok: bad.append((name, l, a, e))
        outs.append('%s = %s' % (l, (round(a, 2) if isinstance(a, float) else a if not hasattr(a, 'date') else a.date().isoformat())))
    av = v[lab('Verdict')]
    if str(av) != str(verdict): bad.append((name, 'Verdict', av, verdict))
    lines.append('%s: %s -> %s, Verdict = %s (checked)' % (name, ', '.join('%s = %s' % kv for kv in inputs), ', '.join(outs), av))
def gift_in(r, n): return r['gift_cost'] if dm(r['date'], n) else 0

# 1 source value ranker
src, mo = 'Care provider', 12
enq = sum(1 for e in EN if e['source'] == src and dm(e['date'], mo)); cl = [x for x in CON if x['source'] == src and dm(x['signed_on'], mo) and x['status'] != CANC]
inc = sum(x['price'] for x in cl); cost = sum(gift_in(r, mo) for r in RF if r['source'] == src) + sum(m['cost'] for m in MK if m['source'] == src and ed(MS, -mo) < m['month'] <= MS and m['kind'] != 'Referral thank-yous')
allc = [x for x in CON if dm(x['signed_on'], mo) and x['status'] != CANC]
by = C.defaultdict(float)
for x in allc: by[x['source']] += x['price']
rank = 1 + sum(1 for s in c.SOURCES if by[s] > inc)
cps = cost / len(cl)
verdict = 'Feed' if not (cps > 3 * CAC) and not (cps > CAC or inc / len(cl) < sum(x['price'] for x in allc) / len(allc)) else 'Hold'
chk('Source Value Ranker', 'src_ranker', [('source', src), ('months', mo)], [('Enquiries', enq), ('Clients signed', len(cl)), ('Income of those', inc), ('Cost of gifts', cost), ('Cost per signed', cps), ('Rank by income', rank)], verdict)

# 2 thank-you due
days = 90
unth = [r for r in RF if r['client_id'] and r['thanked_on'] == '']
n = sum(1 for r in unth if (T - r['date']).days <= days)
gv = sum(SRC[r['source']]['gift_value'] for r in unth if (T - r['date']).days <= days)
chk('Thank-you Due Tool', 'thanks_tool', [('days', days), ('gift', 0)], [('Referrals waiting', n), ('Gift value to send', gv), ('Older thank-yous', sum(1 for r in unth if (T - r['date']).days > days)), ('Gift cost, last 12', sum(r['gift_cost'] for r in RF if dw(r['date'], 365)))],
    'Thank-yous to send: %d, worth %d' % (n, round(gv)))

# 3 referral gap
byref = C.defaultdict(list)
for r in RF: byref[r['referrer']].append(r)
def n12(n_): return sum(1 for r in byref[n_] if dw(r['date'], 365))
def p12(n_): return sum(1 for r in byref[n_] if T - dt.timedelta(days=730) < r['date'] <= T - dt.timedelta(days=365))
sil = [n_ for n_ in byref if p12(n_) >= 2 and n12(n_) == 0]
top = max(sil, key=lambda n_: (p12(n_), n_ == min(sil)))
bigp = max(p12(n_) for n_ in sil)
names = [n_ for n_ in sil if p12(n_) == bigp]
chk('Referral Gap Tool', 'gap_tool', [('min', 2), ('follow', 14)], [('Referrers who went silent', len(sil)), ('Referrals they sent', sum(p12(n_) for n_ in sil)), ('Clients they sent', sum(1 for n_ in sil for r in byref[n_] if r['client_id'])),
    ('Referrals before the silence', bigp)], 'Visit or call first: %s' % names[0])

# 4 class economics (Newborn workshop)
inc4 = 55 * 9; cost4 = 120 + 3 * RATE; prof = inc4 - cost4
nb = [s for s in CS if s['class'] == 'Newborn workshop']
chk('Class Economics Tool', 'class_econ_tool', [('class', 'Newborn workshop'), ('price', 55), ('seats', 12), ('signups', 9), ('hours', 3), ('venue', 120)],
    [('Income', inc4), ('Total cost', cost4), ('Profit', prof), ('Profit per class hour', prof / 3), ('Break-even sign-ups', math.ceil(cost4 / 55)), ('Your own fill', sum(s['signed_up'] for s in nb) / sum(s['seats'] for s in nb)),
     ('Your own profit per class hour', sum(s['profit'] for s in nb) / sum(s['hours'] for s in nb))], 'Run' if prof / 3 >= HT else 'Reprice')

# 5 break-even solver (Partner workshop)
pw = [s for s in CS if s['class'] == 'Partner workshop']; fixed = 112 + 2.5 * RATE; be = math.ceil(fixed / 45); avg = sum(s['signed_up'] for s in pw) / len(pw)
chk('Class Break-even Solver', 'breakeven_tool', [('class', 'Partner workshop'), ('price', 45), ('venue', 112), ('hours', 2.5), ('seats', 12)],
    [('Fixed cost', fixed), ('Sign-ups to break even', be), ('Sign-ups for your profit', math.ceil((fixed + 2.5 * HT) / 45)), ('Your average sign-ups', round(avg, 1)), ('Price at break-even for your average', round(fixed / avg, 2)),
     ('Sessions of this class below', sum(1 for s in pw if not s['above']) / len(pw))], '%d sign-ups needed, you averaged %s' % (be, round(avg, 1)))

# 6 class calendar planner
nm = ed(MS, 1); last12 = [s for s in CS if dm(s['date'], 12)]
same = [s for s in CS if s['month'] == ed(nm, -12)]
avgm = len(last12) / 12.0
chk('Class Calendar Planner', 'calendar_tool', [('month', nm.isoformat()), ('planned', 2)],
    [('Sessions in the same month last year', len(same)), ('Income in the same month', sum(s['income'] for s in same)), ('Sessions a month', round(avgm, 1)),
     ('Seats per session', round(sum(s['seats'] for s in last12) / len(last12), 1)), ('Sign-ups to expect', round(2 * sum(s['signed_up'] for s in last12) / len(last12))), ('Income to expect', round(2 * sum(s['income'] for s in last12) / len(last12)))],
    'Add a session in December' if 2 < avgm else 'Enough sessions in December')

# 7 review pipeline
ask, back = 14, 120
asked_ids = {r['client_id'] for r in RV}
first = sum(1 for x in CL.values() if x['attended_on'] != '' and x['attended_on'] + dt.timedelta(days=ask) <= T and x['attended_on'] >= T - dt.timedelta(days=back) and x['status'] != CANC and x['client_id'] not in asked_ids)
inb = [r for r in RV if r['asked_on'] >= T - dt.timedelta(days=back)]
rem = sum(1 for r in inb if r['asked_on'] <= T - dt.timedelta(days=ask) and r['received_on'] == '')
ans = sum(1 for r in inb if r['received_on'] != '')
st = [r['stars'] for r in RV if r['received_on'] != '' and r['received_on'] >= T - dt.timedelta(days=back)]
chk('Review Pipeline', 'review_pipeline', [('ask', ask), ('back', back)], [('Clients due a first request', first), ('Reminders due', rem), ('Requests asked in the period', len(inb)), ('Answers from those', ans), ('Answer rate', ans / len(inb)),
    ('Average stars in the period', round(sum(st) / len(st), 2))], 'Ask clients today: %d, Reminders to send %d' % (first, rem))

# 8 review rate by doula
old = [r for r in RV if r['asked_on'] <= T - dt.timedelta(days=14)]
dr = [r for r in old if r['doula'] == 'Priya Raman']; ra = sum(1 for r in dr if r['received_on'] != '') / len(dr); rt = sum(1 for r in old if r['received_on'] != '') / len(old)
chk('Review Rate by Doula', 'review_rate', [('doula', 'Priya Raman'), ('channel', 'Online listing')], [('Requests asked of this doula', len(dr)), ('Answers', sum(1 for r in dr if r['received_on'] != '')), ('Answer rate of this doula', ra), ('Answer rate of the whole team', rt),
    ('Answers on this channel', sum(1 for r in RV if r['channel'] == 'Online listing'))], 'Ask more often' if ra < min(0.60, rt) else 'Steady')

# 9 marketing keep or drop
kd = 'Local flyers'; mk = [m for m in MK if m['kind'] == kd and ed(MS, -12) < m['month'] <= MS]
cst = sum(m['cost'] for m in mk); sg = sum(m['signed'] for m in mk); avgp = sum(x['price'] for x in allc) / len(allc)
cpsm = cst / sg if sg else cst
chk('Marketing Keep or Drop', 'mkt_keepdrop', [('kind', kd), ('months', 12)], [('Cost', cst), ('Enquiries', sum(m['enquiries'] for m in mk)), ('Signed clients', sg), ('Cost per signed client', cpsm), ('Average price of a client contract', avgp),
    ('Months of that income to pay back', cst / (sg * avgp / 12))], 'Drop' if sg == 0 else 'Keep' if cpsm <= CAC else 'Renegotiate' if cpsm <= 3 * CAC else 'Drop')

# 10 referral conversion
def conv(s): e = [x for x in EN if x['source'] == s and dm(x['date'], 12)]; g = [x for x in e if x['status'] == 'Signed']; return len(e), len(g), len(g) / len(e)
cv = {s: conv(s) for s in ('Care provider', 'Past client', 'Support professional', 'Class or workshop')}
best = max(cv, key=lambda s: cv[s][2])
chk('Referral Conversion', 'conv_type', [('months', 12)], [('Care provider enquiries', cv['Care provider'][0]), ('Care provider clients signed', cv['Care provider'][1]), ('Past client conversion', cv['Past client'][2]),
    ('Support professional conversion', cv['Support professional'][2]), ('Class enquiries', cv['Class or workshop'][0]), ('Best conversion', cv[best][2])], 'Converts best: %s' % best)

# 11 class to client funnel (Newborn workshop, 12 months)
nb12 = [s for s in CS if s['class'] == 'Newborn workshop' and dm(s['date'], 12)]; newc = sum(s['new_clients'] for s in nb12); pr = sum(s['profit'] for s in nb12)
att = sum(s['attended'] for s in nb12)
clsc = [x for x in CON if x['source'] == 'Class or workshop' and dm(x['signed_on'], 12) and x['status'] != CANC]
chk('Class to Client Funnel', 'class_funnel', [('class', 'Newborn workshop'), ('months', 12)], [('Sessions', len(nb12)), ('Attendees', att), ('New clients from this class', newc), ('Profit of this class', pr),
    ('Clients from classes, all types', len(clsc)), ('Income of clients from classes', sum(x['price'] for x in clsc))], 'Classes bring clients' if newc > 0 and pr + newc * avgp > 0 else 'Classes are a cost')

# 12 class pricing test
seats, fill, price, hours, venue, resp = 12, 0.71, 55, 3, 112, 0.08; cst12 = venue + hours * RATE
dn = min(seats, seats * fill * (1 + resp)) * price * 0.9 - cst12; asis = seats * fill * price - cst12; up = seats * fill * (1 - resp) * price * 1.1 - cst12
chk('Class Pricing Test', 'price_test', [('price', 55), ('seats', 12), ('fill', 0.71), ('hours', 3), ('venue', 112), ('resp', 0.08)], [('Profit at -10%', dn), ('Profit as is', asis), ('Profit at +10%', up), ('Profit per class hour as is', asis / 3)],
    'Raise the price' if up > asis and up >= dn else 'Lower the price' if dn > asis else 'Hold the price')

# 13 class fill forecast
avgi = sum(s['income'] for s in CS if dm(s['date'], 12)) / 12.0
def fc(k): return (0.5 * sum(s['income'] for s in CS if s['month'] == ed(ed(MS, k), -12)) + 0.5 * avgi) * 1.05
tot = fc(1) + fc(2) + fc(3)
chk('Class Fill Forecast', 'fill_forecast', [('scenario', 'Base'), ('trend', 1.05)], [('Income to expect, month 1', round(fc(1))), ('Income to expect, month 2', round(fc(2))), ('Income to expect, month 3', round(fc(3))), ('Income to expect, 3 months', round(tot)),
    ('Class income, last 12 months', sum(s['income'] for s in CS if dm(s['date'], 12)))], 'Expect class income of %d' % round(tot))

# 14 past-client referral nudge
refd = set(r['referrer'] for r in RF)
nud = [r for r in RV if r['received_on'] != '' and r['stars'] >= 4 and r['received_on'] + dt.timedelta(days=7) <= T and r['client'] not in refd and r['received_on'] >= T - dt.timedelta(days=180)]
latest = max(nud, key=lambda r: r['received_on'])
chk('Past-Client Referral Nudge', 'nudge_tool', [('back', 180), ('gift', 15)], [('Past clients to ask', len(nud)), ('Ask first', latest['client']), ('Stars of that review', latest['stars']),
    ('Past-client referrals, last 12 months', sum(1 for r in RF if r['source'] == 'Past client' and dw(r['date'], 365))), ('Clients who finished', sum(1 for x in CL.values() if x['status'] == 'Completed'))], 'Ask for a referral: %s' % latest['client'])

# 15 gift budget
g12 = sum(r['gift_cost'] for r in RF if dw(r['date'], 365)); rc = [x for x in CON if x['client_id'] in REFSET and dm(x['signed_on'], 12) and x['status'] != CANC]
exp = 80 * g12 / len(rc)
chk('Gift Budget Planner', 'gift_budget', [('expected', 80), ('budget', 1800)], [('Gift cost, last 12 months', g12), ('Thank-you gifts given', sum(1 for r in RF if dw(r['date'], 365) and r['gift_cost'] > 0)),
    ('Clients from referrals, last', len(rc)), ('Gift cost to expect', round(exp)), ('Care provider gifts', sum(r['gift_cost'] for r in RF if r['source'] == 'Care provider' and dw(r['date'], 365)))],
    ('Budget for gifts: %d' % round(exp)) if exp <= 1800 else 'Over the gift setting')

# 16 review score tracker
m1 = c.month_start(1)
def stars_in(a, b): return [r['stars'] for r in RV if r['received_on'] != '' and a <= r['received_on'] < b]
now_ = stars_in(m1, ed(m1, 1)); b3 = stars_in(ed(m1, -3), m1); ly = stars_in(ed(m1, -12), ed(m1, -11))
a_now = round(sum(now_) / len(now_), 2); a_b3 = round(sum(b3) / len(b3), 2); a_ly = round(sum(ly) / len(ly), 2)
chk('Review Score Tracker', 'score_tracker', [('month', m1.isoformat())], [('Answers received in the month', len(now_)), ('Average stars of the month', a_now), ('Average stars, 3 months before', a_b3), ('Average stars, same month last year', a_ly)],
    'Stars slipping' if a_now < sum(b3) / len(b3) - 0.1 else 'Stars improving' if a_now > sum(b3) / len(b3) + 0.1 else 'Stars steady')

# 17 source mix risk
cnt = C.Counter(x['source'] for x in allc); tot17 = len(allc); order = sorted(cnt.values(), reverse=True)
srcs = list(c.SOURCES); p1 = max(i for i, s in enumerate(srcs) if cnt[s] == order[0]); p2 = max(i for i, s in enumerate(srcs) if cnt[s] == order[1] and i != p1)
chk('Source Mix Risk', 'mix_risk', [('months', 12), ('limit', 0.30)], [('Clients signed in the period', tot17), ('Top source', srcs[p1]), ('Clients from the top source', order[0]), ('Share of clients from the top source', order[0] / tot17),
    ('Second source', srcs[p2]), ('Share from the top two', (order[0] + order[1]) / tot17), ('Sources that brought a client', sum(1 for s in srcs if cnt[s] > 0))],
    ('Too reliant on %s' % srcs[p1]) if order[0] / tot17 > 0.30 else 'Sources are spread')

# 18 care provider office planner
off = 'Oakfield Care Office'
a, b = n12(off), p12(off); chg = a / b - 1
offs = [n_ for n_ in byref if byref[n_][0]['source'] == 'Care provider']
tr = {n_: n12(n_) - p12(n_) for n_ in offs}; worst = min(tr, key=tr.get)
chk('Care Provider Office Planner', 'office_planner', [('office', off), ('drop', 0.25)], [('Referrals, last 12 months', a), ('Referrals, 12 months before', b), ('Change', chg), ('Clients, last 12 months', sum(1 for r in byref[off] if r['client_id'] and dw(r['date'], 365))),
    ('Care-provider offices', len(offs)), ('Rank by trend', 1 + sum(1 for n_ in offs if tr[n_] < tr[off])), ('Office falling the most', worst), ('Its change in referrals', tr[worst])], 'Visit')

open(os.path.join(HERE, 'out7/qa.txt'), 'w').write('\n'.join(lines) + '\n')
print(len(lines), 'tool lines written; mismatches:', len(bad))
for b_ in bad: print('  MISMATCH', b_)
