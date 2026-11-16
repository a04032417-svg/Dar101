"""Independent recomputation of every part-8 tool on its default inputs (from du_core only), compared with the recalculated workbook; writes out8/qa.txt."""
import sys, os, json, math, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import du_core as c
from openpyxl import load_workbook
T = c.TODAY; MS = dt.date(T.year, T.month, 1)
def em(d, n): return c.add_months(d, n)
LM = em(MS, -1)
PN = c.pnl_rows(); CA = c.cash_rows(); TX = c.tax_rows(); EX = c.expense_rows(); RN = c.renewal_rows(); TR = c.training_rows()
INS = c.plan_rows(); CT = c.contract_rows(); CL = c.client_rows(); BU = {b['category']: b['monthly_budget'] for b in c.budget}
def rev(p): return p['birth_income'] + p['postpartum_income'] + p['addon_income'] + p['class_income'] + p['other_income']
def cost(p): return p['doula_pay'] + p['backup_pay'] + p['mileage'] + p['admin_pay'] + p['other_costs']
for p in PN: p['rev'] = rev(p); p['cost'] = cost(p); p['prof'] = p['rev'] - p['cost']; p['fixed'] = p['admin_pay'] + p['other_costs']
P = {p['month']: p for p in PN}
CS = {x['month']: x for x in CA}
def in12(p): return em(MS, -12) < p['month'] <= MS
T12 = [p for p in PN if in12(p)]
S12 = lambda k: sum(p[k] for p in T12)
wb = load_workbook(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out8/work/v/en-demo.xlsx'), data_only=True)
spec = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'du8.en.json')))
def outs(sheet):
    d = {}
    for r in wb[sheet].iter_rows(values_only=True):
        r = [x for x in r if x not in (None, '')]
        if len(r) >= 2 and isinstance(r[0], str): d[r[0].replace(' ($)', '')] = r[1]
    return d
def get(d, lab):
    for k in d:
        if k.startswith(lab): return d[k]
    raise KeyError(lab)
def close(a, b, tol=0.51):
    if isinstance(a, dt.datetime): a = a.date()
    if isinstance(b, dt.datetime): b = b.date()
    if isinstance(a, dt.date) or isinstance(b, dt.date): return a == b
    return abs(a - b) <= tol
LINES = []; FAIL = []
def chk(tool, inputs, pairs, verdict):
    d = outs([t for t in spec['tools'] if t['key'] == tool][0]['sheet'])
    name = [t for t in spec['tools'] if t['key'] == tool][0]['sheet']
    parts = []
    for lab, exp, tol in pairs:
        got = get(d, lab)
        ok = close(got, exp, tol)
        if not ok: FAIL.append((tool, lab, got, exp))
        shown = (exp.isoformat() if isinstance(exp, dt.date) else (round(exp, 2) if isinstance(exp, float) else exp))
        parts.append('%s = %s' % (lab, shown))
    v = get(d, 'Verdict'); okv = (v == verdict)
    if not okv: FAIL.append((tool, 'Verdict', v, verdict))
    LINES.append('%s: %s -> %s; Verdict = "%s" (%s)' % (name, inputs, ', '.join(parts), verdict, 'checked' if (okv and not [f for f in FAIL if f[0] == tool]) else 'MISMATCH'))

# ---------- shared pieces
open_r = [r for r in RN if r['renewed_on'] == '']
cash_now = CS[MS]['closing']
still = sum(t['set_aside'] for t in TX if t['status'] == 'Planned')
# 1 renewals
dl = lambda r: (r['due_date'] - T).days
red = [r for r in open_r if dl(r) <= 30]; amb = [r for r in open_r if 30 < dl(r) <= 60]
nx = min(open_r, key=lambda r: r['due_date']); ins = min([r for r in open_r if r['item'] == 'Liability insurance'], key=lambda r: r['due_date'])
chk('renew_dates', 'red = 30, amber = 60, item = Liability insurance', [('Red renewals', len(red), 0), ('Amber renewals', len(amb), 0), ('Next renewal due on', nx['due_date'], 0), ('Days to the next renewal', dl(nx), 0),
    ('Usual cost of that item', 1150, 0), ('Training days planned', len([t for t in TR if T < t['date'] <= T + dt.timedelta(days=90)]), 0)],
    'Red %d, Amber %d. Next renewal: %s in %d days' % (len(red), len(amb), nx['item'], dl(nx)))
# 2 expense tracker
act = sum(e['amount'] for e in EX if e['category'] == 'Marketing' and e['month'] == LM); bud = BU['Marketing']
ly = sum(e['amount'] for e in EX if e['category'] == 'Marketing' and e['month'] == em(LM, -12))
chk('expense_tracker', 'category = Marketing, month = last full month, accept = 10%', [('Spending in the month', act, .01), ('Monthly budget', bud, 0), ('Over or under budget', act - bud, .01), ('Same month last year', ly, .01),
    ('Share of revenue', act / P[LM]['rev'], .0001)], 'Marketing is %d over budget' % round(act - bud))
# 3 cash forecast (independent model)
def forecast():
    first = em(MS, 1)
    exp_in = {}
    def add(d, a):
        m = max(dt.date(d.year, d.month, 1), first); exp_in[m] = exp_in.get(m, 0) + a
    for i in INS:
        if i['status'] == 'Unpaid': add(i['due_date'], i['amount'])
    for x in CT:
        if x['status'] == 'Signed' and x['plan'] == 'Pay in full' and x['balance_paid_on'] == '' and x['balance_due'] != '' and x['price'] - x['deposit'] > 0: add(x['balance_due'], x['price'] - x['deposit'])
    new = round(sum(x['deposit'] for x in CT if em(MS, -6) <= x['signed_on'] < MS) / 6)
    bc = [x for x in CT if em(MS, -12) <= x['signed_on'] < MS and x['kind'] != 'Postpartum']
    bal = (sum(x['price'] for x in bc) - sum(x['deposit'] for x in bc)) / len(bc)
    avgb = sum(p['births'] for p in PN if em(MS, -12) <= p['month'] < MS) / 12
    last6 = [x for x in CA if em(MS, -6) <= x['month'] < MS]
    costs = round(sum(x['pay_out'] + x['expenses_out'] + x['refunds'] for x in last6) / 6)
    fixed = round(sum(P[x['month']]['fixed'] for x in last6) / 6)
    rows = []; cum = cash_now
    for k in range(1, 13):
        m = em(MS, k)
        due = len([x for x in CL if x['status'] != 'Cancelled' and x['kind'] != 'Postpartum' and dt.date(x['edd'].year, x['edd'].month, 1) == m])
        sched = exp_in.get(m, 0); unb = round(max(0, avgb - due) * bal)
        ein = sched + new + unb; sa = round(0.25 * max(0, ein - costs)); net = ein - costs - 3600 - sa; cum += net
        rows.append(dict(m=m, k=k, ein=ein, costs=costs, fixed=fixed, closing=cum, net=net, sched=sched, new=new, unb=unb, due=due))
    return rows
FR = forecast()
low = min(FR, key=lambda r: r['closing'])
cover = low['closing'] / (FR[0]['fixed'] + 3600)
chk('cash_forecast', 'scenario = Base, floor = 15000, cover = 3', [('Cash now', cash_now, .01), ('Lowest closing cash ahead', low['closing'], 1), ('Month of the lowest cash', low['m'], 0), ('Months below the floor', len([r for r in FR if r['closing'] < 15000]), 0),
    ('Months of cover at the lowest cash', cover, .01), ('Closing cash in 12 months', FR[-1]['closing'], 1), ('Births due in the next 12 months', sum(r['due'] for r in FR), 0)],
    'Lowest cash %d in %s %d, %s months of cover' % (round(low['closing']), c.MONTH_NAMES[low['m'].month - 1] if hasattr(c, 'MONTH_NAMES') else ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][low['m'].month - 1], low['m'].year, round(cover, 1)))
# 4 owner pay
last6 = [P[em(MS, -k)] for k in range(1, 7)]
avgp = sum(p['prof'] for p in last6) / 6; aside = round(0.25 * avgp)
afford = max(0, min(3600, cash_now - 15000 - still))
chk('owner_pay', 'draw = 3600, set-aside share = 25%, floor = 15000, months = 6', [('Average monthly profit', avgp, 1), ('Set-aside to move each month', aside, 1), ('Set-aside still to move', still, .01),
    ('Cash above the floor after the set-aside', cash_now - 15000 - still, .01), ('Draw your cash allows now', afford, .01)], 'Yes, pay yourself 3600' if 3600 <= afford else 'Reduce')
# 5 ratios
marg = lambda p: p['prof'] / p['rev']
a3 = sum(marg(P[em(LM, -k)]) for k in (1, 2, 3)) / 3
chk('ratios', 'month = last full month, band = 2 points', [('Revenue', P[LM]['rev'], .01), ('Profit', P[LM]['prof'], .01), ('Profit margin', marg(P[LM]), .0001), ('Margin, average of the 3 months before', a3, .0001),
    ('Margin, same month last year', marg(P[em(LM, -12)]), .0001)], 'Margin matches your own history' if abs(marg(P[LM]) - a3) <= .02 else ('Margin is above your own history' if marg(P[LM]) > a3 else 'Margin is below your own history'))
# 6 own history
def series(name):
    if name.startswith('cash.'): return {x['month']: x[name[5:]] for x in CA}
    if name.startswith('tax.'): return {x['month']: x[name[4:]] for x in TX}
    return None
def val(measure, m):
    p = P.get(m)
    if p is None: return 0
    d = {'revenue': p['rev'], 'birth_income': p['birth_income'], 'postpartum_income': p['postpartum_income'], 'addon_income': p['addon_income'], 'class_income': p['class_income'], 'doula_pay': p['doula_pay'], 'backup_pay': p['backup_pay'],
         'mileage': p['mileage'], 'admin_pay': p['admin_pay'], 'other_costs': p['other_costs'], 'costs': p['cost'], 'profit': p['prof'], 'margin': p['prof'] / p['rev'], 'births': p['births'], 'visit_hours': p['visit_hours'],
         'doula_share': (p['doula_pay'] + p['backup_pay']) / p['rev'], 'cost_birth': p['cost'] / p['births'], 'profit_birth': p['prof'] / p['births'], 'cost_share': p['cost'] / p['rev'], 'revenue_birth': p['rev'] / p['births']}
    return d.get(measure)
import du8_data as D
nd = 0; scores = []
for (mname, col, direction) in D.CMP:
    if col.startswith('cash.'): f = lambda m, col=col: CS[m][col[5:]]
    elif col.startswith('tax.'): f = lambda m: next(x for x in TX if x['month'] == m)['set_aside']
    else: f = lambda m, col=col: val(col, m)
    last = f(LM); a = sum(f(em(LM, -k)) for k in (1, 2, 3)) / 3
    ch = (last / a - 1) if a else 0; sc = ch * direction; scores.append((sc, mname))
    if direction != 0 and sc < -0.10: nd += 1
scores.sort()
chk('own_history', 'drop = 10%', [('Figures checked', 24, 0), ('Figures that dropped', nd, 0), ('Biggest drop', 0, 1e9) if False else ('Size of the biggest drop', scores[0][0], .0005)], '%d figures dropped over 10%%' % nd)
# 7 year end
b12 = S12('births'); r12 = S12('rev'); p12 = S12('prof'); rpb = r12 / b12
need = math.ceil(300000 / (12 * rpb) * 10 - 1e-9) / 10; did = b12 / 12
var = (S12('doula_pay') + S12('backup_pay') + S12('mileage')) / b12
chk('year_end', 'target = 300000, change = 1', [('Births, last 12 months', b12, 0), ('Revenue, last 12 months', r12, .01), ('Profit, last 12 months', p12, .01), ('Revenue per birth', rpb, .01), ('Births a month needed for your target', need, .001),
    ('Profit with one more birth a month', p12 + 12 * (rpb - var), 1)], 'You need %s births a month, you did %s' % (need, round(did, 1)))
# 8 runway
cin3 = sum(CS[em(MS, -k)]['cash_in'] for k in (1, 2, 3)) / 3
var3 = sum(P[em(MS, -k)]['doula_pay'] + P[em(MS, -k)]['backup_pay'] + P[em(MS, -k)]['mileage'] for k in (1, 2, 3)) / 3
fix3 = sum(P[em(MS, -k)]['fixed'] for k in (1, 2, 3)) / 3
net = cin3 * 0.5 - var3 * 0.5 - fix3 - 3600; burn = max(0, -net); run = min(24, (cash_now - 15000) / burn) if burn > 0 else 24
chk('runway', 'fall = 50%, draw = 3600, floor = 15000', [('Cash in a month, last 3 months', cin3, .5), ('Fixed costs a month', fix3, .5), ('Cash change a month after the fall', net, 1), ('Months until the floor', run, .01)],
    'Comfortable' if run >= 6 else ('Watch' if run >= 3 else 'Act now'))
# 9 ranker
vr = {k: sum(e['amount'] for e in EX if e['category'] == k and e['month'] == LM) - v for k, v in BU.items()}
top = sorted(vr.items(), key=lambda x: -x[1])
chk('ranker', 'accept = 10%', [('Variance of all categories, last full month', sum(vr.values()), .01), ('Categories over budget', len([v for v in vr.values() if v > 0]), 0), ('Amount over budget', top[0][1], .01), ('Amount of the second', top[1][1], .01),
    ('Amount under budget', min(vr.values()), .01)], 'Investigate %s' % top[0][0])
# 10 breakeven
fixy = S12('admin_pay') + S12('other_costs'); marg_b = rpb - var; needb = math.ceil((fixy + 12 * 3600) / (12 * marg_b) * 10 - 1e-9) / 10
chk('breakeven', 'draw = 3600, extra fixed cost = 0, price change = 0%', [('Revenue per birth', rpb, .6), ('Margin per birth', marg_b, .6), ('Fixed costs for a year', fixy, .01), ('Births a month to break even', needb, .001)], 'You need %s births a month to break even' % needb)
# 11 draw scenario
step = round(3600 * 0.1)
lows = {'dn': min(r['closing'] + r['k'] * step for r in FR), 'as': min(r['closing'] for r in FR), 'up': min(r['closing'] - r['k'] * step for r in FR)}
chk('draw_scenario', 'floor = 15000, cover = 3', [('Lowest cash with the lower draw', lows['dn'], 1), ('Lowest cash as it is', lows['as'], 1), ('Lowest cash with the higher draw', lows['up'], 1), ('Highest draw that keeps the floor', 3600 + step, 0)], 'Affordable')
# 12 tax check
ytd = sum(p['prof'] for p in PN if dt.date(T.year, 1, 1) <= p['month'] <= MS)
pl = [t for t in TX if t['status'] == 'Planned']; nd_ = min(em(t['month'], 1) + dt.timedelta(days=4) for t in pl)
chk('tax_check', 'share = 25%, tax year starts in month 1', [('Profit, year to date', ytd, .01), ('Set-aside due at your share', round(max(0, ytd) * .25), .6), ('Next transfer date', nd_, 0), ('Amount to move by then', sum(t['set_aside'] for t in pl), .01)],
    'Move %d by %d %s %d, confirm with your adviser' % (round(sum(t['set_aside'] for t in pl)), nd_.day, ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][nd_.month - 1], nd_.year))
# 13 free cash
payrun = CA[-2]['pay_out']; exp3 = round(sum(CS[em(MS, -k)]['expenses_out'] for k in (1, 2, 3)) / 3 * 30 / 30)
free = cash_now - still - payrun - exp3
chk('free_cash', 'next pay run = %.2f, days of costs = 30, draw = 3600' % payrun, [('Cash now', cash_now, .01), ('Expenses for the days you keep', exp3, .6), ('Free cash', free, 1), ('Free cash after your draw', free - 3600, 1)], 'Free cash is %d' % round(free))
# 14 cost plan
rc = sum(r['cost'] for r in open_r if T < r['due_date'] <= em(T, 12)); tc = sum(t['cost'] for t in TR if T < t['date'] <= em(T, 12))
chk('cost_plan', 'months = 12', [('Renewal costs due', rc, .01), ('Training costs planned', tc, .01), ('Total to plan for', rc + tc, .01), ('Set aside each month', int((rc + tc) / 12 + .5), .6)], 'Set aside %d a month' % int((rc + tc) / 12 + .5))
# 15 time off
wk = r12 / 52; vsh = (S12('doula_pay') + S12('backup_pay') + S12('mileage')) / r12; hit = round(4 * wk * 0.35 * (1 - vsh))
fix6 = round(sum(P[em(MS, -k)]['fixed'] for k in range(1, 7)) / 6); cova = (cash_now - hit) / (fix6 + 3600)
chk('timeoff', 'weeks = 4, share of income that stops = 35%, draw = 3600', [('Average revenue a week', round(wk), .6), ('Cash lost by the time off', hit, .6), ('Fixed costs that continue a month', fix6, .6), ('Months of cover after the time off', cova, .01)], 'Affordable with %s months of cover' % round(cova, 1))
# 16 cushion
drops = sorted([max(0, x['opening'] - x['closing']) for x in CA if x['month'] < MS], reverse=True)
chk('cushion', 'biggest falls to plan for = 2, floor = 15000', [('Lowest closing cash, 24 months', min(x['closing'] for x in CA), .01), ('Biggest fall in one month', drops[0], .01), ('Second biggest fall', drops[1], .01), ('Cushion to keep above the floor', drops[0] + drops[1], .01)], 'Keep %d aside' % round(drops[0] + drops[1]))
# 17 fixed costs
fx = S12('admin_pay') + S12('other_costs'); share = fx / r12
cat12 = {}
for e in EX:
    if em(MS, -11) <= e['month'] <= MS: cat12[e['category']] = cat12.get(e['category'], 0) + e['amount']
topc = max(cat12, key=cat12.get)
chk('fixed_costs', 'limit = 15%', [('Fixed costs, last 12 months', fx, .01), ('Share of revenue', share, .0001), ('Admin pay, last 12 months', S12('admin_pay'), .01), ('Spending of that category', cat12[topc], .01)], 'Fixed costs are %d%% of revenue, review %s' % (round(share * 100), 'Admin' if S12('admin_pay') > cat12[topc] else topc))
# 18 pack check
exp_all = sum(e['amount'] for e in EX if em(MS, -12) < e['month'] <= MS)
chk('pack_check', 'months = 12, difference counted as balanced = 1', [('Profit, months checked', p12, .01), ('Other costs on Profit and Loss', S12('other_costs'), .01), ('Expenses on the Expenses sheet', exp_all, .01), ('Difference: other costs against Expenses', round(S12('other_costs') - exp_all), .6),
    ('Total of the differences', 0, .6)], 'Pack balances')
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out8/qa.txt'), 'w').write('\n'.join(LINES) + '\n')
print('\n'.join(LINES)); print('FAIL', FAIL)
