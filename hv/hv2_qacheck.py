import sys; sys.path.insert(0, '/home/claude/work/hv')
import hv2_qa as Q
from hv2_lists import *
import hv2_data as DD
V = {t['key']: Q.vals(t) for t in Q.spec['tools']}
EST = DD._EST; T = TODAY
def d(e): return to_date(e['date'])
def win(n): return [e for e in EST if (T - d(e)).days <= n and d(e) <= T]
est_val = lambda e: e['better_price'] if e['better_price'] > 0 else e['good_price']
PBd = {p['pb_id']: p for p in price_book}
lines = []; fails = []
def chk(tool, name, got, exp, tol=0.006, text=''):
    ok = abs(got - exp) <= tol * max(1, abs(exp)) if not isinstance(exp, str) else got == exp
    if not ok: fails.append((tool, name, got, exp))
    return ok
def line(tool, inputs, outs, ok): lines.append('%s: %s -> %s (%s)' % (tool, inputs, outs, 'checked' if ok else 'MISMATCH'))
t = V
# 1 line builder
c = PBd['PB-039']['cost']; need = 1875
ok = chk('lb', 'cost', t['line_builder']['Total cost'], c, 0.001) and chk('lb', 'need', t['line_builder']['Price at the target margin'], need) and chk('lb', 'margin', t['line_builder']['Margin at the flat price'], PBd['PB-039']['margin'], 0.002)
line('Flat-Rate Line Builder', 'task number = 39, hours = 0, parts = 0, target = 0', 'total cost = %.2f, price at target = %s, margin = %.3f, verdict = %s' % (t['line_builder']['Total cost'], t['line_builder']['Price at the target margin'], t['line_builder']['Margin at the flat price'], t['line_builder']['Verdict']), ok)
# 2 margin check
under = [p for p in price_book if p['margin'] < p['target_margin'] - 0.01]; watch = [p for p in price_book if p['target_margin'] - 0.01 <= p['margin'] < p['target_margin']]
ok = chk('mc', 'under', t['margin_check']['Lines under target'], len(under)) and chk('mc', 'watch', t['margin_check']['Lines on watch'], len(watch))
line('Price Book Margin Check', 'amber range = 2 points', 'under target = %d, on watch = %d, margin lost a year = %.1f, worst line = %s, verdict = %s' % (len(under), len(watch), t['margin_check']['Margin lost a year on these lines'], t['margin_check']['Lowest margin line 1'], t['margin_check']['Verdict']), ok)
# 3 impact
p65 = PART['Water heater, 50 gal tank']; extra = 1 * (607 - p65['unit_cost'])
ok = chk('pi', 'extra', t['price_impact']['Extra cost per job'], extra) and chk('pi', 'after', t['price_impact']['Margin after the change'], (1750 - PBd['PB-039']['cost'] - extra) / 1750, 0.002) and chk('pi', 'risk', t['price_impact']['Money at risk a year'], extra * t['price_impact']['Jobs a year on the line'])
line('Supplier Price Change Impact', 'part number = 65, new cost = 607', 'extra cost per job = %.0f, margin after = %.3f, price needed = %s, money at risk = %.0f, verdict = %s' % (extra, t['price_impact']['Margin after the change'], t['price_impact']['Price needed after the change'], t['price_impact']['Money at risk a year'], t['price_impact']['Verdict']), ok)
# 4 gbb
sg, sb = round(sum(1 for e in EST if e['outcome'] == 'Won' and (T - d(e)).days < 365 and e['option_chosen'] == 'Good') / 292.0, 2), 0.52
g = t['gbb_builder']; ok = chk('g', 'mg', g['Margin, good'], PBd['PB-024']['margin'], 0.002) and chk('g', 'mb', g['Margin, better'], PBd['PB-025']['margin'], 0.002) and chk('g', 'pay', g['Monthly payment, better'], round(5700 * FINANCE_FACTOR))
line('Good-Better-Best Builder', 'costs = 2404/3183/3841, prices = 4025/5700/7075, shares = 25/52/23%, target = 38%', 'margins = %.3f/%.3f/%.3f, better payment = %s, average ticket = %.0f, verdict = %s' % (g['Margin, good'], g['Margin, better'], g['Margin, best'], g['Monthly payment, better'], g['Average ticket at these shares'], g['Verdict: option to lead with']), ok)
# 5 mix
w12 = [e for e in EST if e['outcome'] == 'Won' and (T - d(e)).days <= 365]
n = len(w12); av = lambda o: sum(e['price_won'] for e in w12 if e['option_chosen'] == o) / max(1, sum(1 for e in w12 if e['option_chosen'] == o))
tk = sum(e['price_won'] for e in w12) / n; m = V['option_mix']
ok = chk('om', 'n', m['Estimates won, 12 months'], n) and chk('om', 'tk', m['Average ticket won'], tk, 0.002) and chk('om', 'b', m['Average ticket at better'], av('Better'), 0.002)
gain = 0.10 * (av('Better') - av('Good')) + 0.05 * (av('Best') - av('Better')); ok = ok and chk('om', 'gain', m['Ticket gained per won estimate after the shift'], gain, 0.002)
line('Option Mix Analyser', 'shift good to better = 10%, better to best = 5%', 'won = %d, average ticket = %.0f, ticket gained = %.0f, extra revenue a year = %.0f, verdict = %s' % (n, tk, gain, m['Extra revenue a year after the shift'], m['Verdict']), ok)
# 6 ranker
op = [e for e in EST if e['outcome'] == 'Open']; tot = sum(est_val(e) for e in op)
score = sorted(op, key=lambda e: -(est_val(e) * ((T - d(e)).days + 1)))
cov = sum(est_val(e) for e in score[:8]); r = V['followup_ranker']
ok = chk('r', 'tot', r['Money on the table'], tot) and chk('r', 'cov', r['Value covered by those calls'], cov) and chk('r', 'first', r['Call first, no. 1'], score[0]['estimate_id'])
line('Estimate Follow-up Ranker', 'calls today = 8, expected close = 35%', 'open = %d, money on the table = %.0f, covered by 8 calls = %.0f, expected won = %.0f, first = %s, verdict = %s' % (len(op), tot, cov, r['Expected value won from the calls'], r['Call first, no. 1'], r['Verdict']), ok)
# 7 close analyser
def cr(days, lo=0):
    es = [e for e in EST if lo <= (T - d(e)).days <= days and e['outcome'] != 'Open']; return sum(1 for e in es if e['outcome'] == 'Won') / float(len(es))
ca_ = V['close_analyser']; ok = chk('c', '90', ca_['Close rate, last 90 days'], cr(90), 0.01) and chk('c', '12', ca_['Close rate, last 12 months'], cr(365), 0.01)
line('Close Rate Analyser', 'watch range = 5 points', 'close rate 90 days = %.3f, 12 months = %.3f, weakest technician = %s (%.3f), verdict = %s' % (ca_['Close rate, last 90 days'], ca_['Close rate, last 12 months'], ca_['Weakest technician, 12 months'], ca_['Their close rate'], ca_['Verdict']), ok)
# 8 expiry
ex = V['expiry_planner']; bands = [(0, 7), (8, 14), (15, 30), (31, 9999)]
vals = [sum(est_val(e) for e in op if lo <= (T - d(e)).days <= hi) for lo, hi in bands]; rates = [0.45, 0.30, 0.15, 0.05]
win_ = sum(v * r_ for v, r_ in zip(vals, rates)); drop = sum(v for v, r_ in zip(vals, rates) if r_ < 0.10)
ok = chk('e', 'win', ex['Value still winnable'], win_) and chk('e', 'drop', ex['Value to drop from the list'], drop)
line('Estimate Expiry Planner', 'close rates by age = 45/30/15/5%, drop below 10%', 'value by band = %s, still winnable = %.0f, to drop = %.0f, verdict = %s' % ('/'.join('%.0f' % v for v in vals), win_, drop, ex['Verdict']), ok)
# 9 lost
l12 = [e for e in EST if e['outcome'] == 'Lost' and (T - d(e)).days <= 365]; lv = sum(est_val(e) for e in l12); pv = sum(est_val(e) for e in l12 if e['lost_reason'] == 'Price'); lc = V['lost_cause']
ok = chk('l', 'tot', lc['Lost value, 12 months'], lv) and chk('l', 'price', lc['Lost to price'], pv) and chk('l', 'wb', lc['Extra gross profit'], pv * 0.15 * 0.42)
line('Lost-Estimate Cause Analyser', 'win back = 15%, margin = 42%', 'lost value = %.0f, top cause = %s (%.0f), extra gross profit = %.0f, verdict = %s' % (lv, lc['Top cause'], pv, lc['Extra gross profit'], lc['Verdict: cause to fix first']), ok)
# 10 yearly
rev = sum(PBd[p]['flat_price'] * DD._TK.get(p, 1) if DD._TK.get(p, 1) else 0 for p in PBd); rev = sum(p['flat_price'] * max(DD._TK.get(p['pb_id'], 0), 1) for p in price_book)
cost = sum(p['cost'] * max(DD._TK.get(p['pb_id'], 0), 1) for p in price_book); yr = V['yearly_review']
parts_ = sum(p['parts_cost'] * max(DD._TK.get(p['pb_id'], 0), 1) for p in price_book); trip = sum((p['labour_hours'] + 0.45) * max(DD._TK.get(p['pb_id'], 0), 1) for p in price_book) * VEHICLE_HOUR
oth = sum((p['permit_fee'] + p['disposal'] + p['sub_cost']) * max(DD._TK.get(p['pb_id'], 0), 1) for p in price_book); lab = cost - parts_ - trip - oth
xj = lab * 0.04 + parts_ * 0.06 + trip * 0.08
ok = chk('y', 'rev', yr['Revenue on the price book, 12 months'], rev, 0.002) and chk('y', 'xj', yr['Extra job cost a year'], xj, 0.003) and chk('y', 'need', yr['Total rise needed'], xj / cost + 49200 * 0.08 / rev, 0.003)
line('Yearly Price Review', 'labour = 4%, parts = 6%, fuel = 8%, insurance = 8% of 49,200, plan = 4%', 'extra job cost = %.0f, total rise needed = %.4f, shortfall = %.4f, first line to lift = %s, verdict = %s' % (xj, yr['Total rise needed'], yr['Shortfall against your planned rise'], yr['Lift first, line 1'], yr['Verdict']), ok)
# 11 breakeven
mm = (rev - cost) / rev; x = 0.05; be = V['rise_breakeven']; L = x / (mm + x)
ok = chk('b', 'm', be['Gross margin of the price book mix'], mm, 0.002) and chk('b', 'L', be['Job loss that leaves profit unchanged'], L, 0.003) and chk('b', 'chg', be['Change in gross profit'], 0.96 * (rev * 1.05 - cost) - (rev - cost), 0.01)
line('Price Rise Break-Even Solver', 'rise = 5%, jobs lost = 4%', 'book margin = %.3f, job loss allowed = %.4f, jobs you can lose = %s, change in gross profit = %.0f, verdict = %s' % (mm, L, be['Jobs you can lose'], be['Change in gross profit'], be['Verdict']), ok)
# 12 diag fee
dv = [j for j in DD._DIAG if j['month'] >= iso(month_start(12))]; conv = sum(1 for j in dv if j['_conv']) / float(len(dv)); df = V['diag_fee_test']
ok = chk('d', 'cost', df['Cost of one visit'], 1 * 40 + 1.45 * 9.5, 0.001) and chk('d', 'conv', df['Conversion, last 12 months'], conv, 0.002)
line('Call-Out and Diagnostic Fee', 'fee = 99, hours = 1, drive = 0.45, rate = 40, repair profit = 190', 'cost of a visit = %.2f, fee multiple = %.2f, conversion = %.3f, verdict = %s' % (df['Cost of one visit'], df['Fee as a multiple of cost'], conv, df['Verdict']), ok)
# 13 diag by tech
bt = DD.diag_by_tech(); dt = V['diag_by_tech']; ok = chk('dt', 'k', dt['Conversion, Kofi Mensah'], bt['Kofi Mensah'][1] / float(bt['Kofi Mensah'][0]), 0.002) and chk('dt', 'all', dt['Conversion of the three together'], conv, 0.002)
line('Diagnostic Conversion by Tech', 'visits and converted from the 12-month log, target = 60%', 'conversion = %.3f / %.3f / %.3f, best = %s, weakest = %s, verdict = %s' % (dt['Conversion, Tomasz Nowak'], dt['Conversion, Kofi Mensah'], dt['Conversion, Elena Rossi'], dt['Best converter'], dt['Weakest converter'], dt['Verdict']), ok)
# 14 member
rep = [p for p in price_book if p['job_type'] in [j['job_type'] for j in job_types if j['kind'] == 'Repair']]; mn = min(p['margin'] for p in rep); mem = V['member_check']
ok = chk('m', 'n', mem['Repair lines in the book'], len(rep)) and chk('m', 'min', mem['Lowest repair margin at the full price'], mn, 0.003) and chk('m', 'mem', mem['Lowest repair margin at the member price'], 1 - (1 - mn) / 0.9, 0.003)
line('Member Price and Discount Check', 'discount = 10%, floor = 30%, member share = 30%', 'repair lines = %d, under floor = %d, lowest margin at member price = %.3f, discount given away = %.0f, verdict = %s' % (len(rep), mem['Repair lines under the floor at the member price'], mem['Lowest repair margin at the member price'], mem['Discount given away a year'], mem['Verdict']), ok)
# 15 financing
fc = V['financing_check']; ok = chk('f', 'pay', fc['Monthly payment'], 6500 * 0.0212, 0.002) and chk('f', 'fee', fc['Fee you absorb'], 6500 * 0.03 + 40) and chk('f', 'pct', fc['Margin percent after the fee'], (6500 * 0.42 - 235) / 6500, 0.002) and chk('f', 'small', fc['Smallest job worth financing'], 40 / (0.42 - 0.03 - 0.30), 0.002)
line('Financing Cost Check', 'amount = 6500, term = 60, fee = 3%, fixed fee = 40, margin = 42%', 'monthly payment = %.1f, fee absorbed = %.0f, margin after fee = %.3f, smallest job = %.0f, verdict = %s' % (fc['Monthly payment'], fc['Fee you absorb'], fc['Margin percent after the fee'], fc['Smallest job worth financing'], fc['Verdict']), ok)
# 16 turnaround
tw = [e for e in EST if (T - d(e)).days <= 365 and e['job_type'] == 'Repipe']; cd = [(d(e) - to_date(DD._call_date(e))).days for e in tw]; tu = V['turnaround']
ok = chk('t', 'repipe', tu['Days to estimate, Repipe'], sum(cd) / float(len(cd)), 0.01)
line('Estimate Turnaround Tool', 'target days = 2', 'repipe call to estimate = %.2f days, shop average = %.2f, slowest = %s, verdict = %s' % (tu['Days to estimate, Repipe'], tu['Shop average, call to estimate'], tu['Slowest job type'], tu['Verdict']), ok)
# 17 phone quote
pq = V['phone_quote']; ok = chk('p', 'price', pq['Price to quote'], 1750) and chk('p', 'dep', pq['Deposit to hold the date'], 525) and chk('p', 'max', pq['Highest price for the job type'], 3025)
line('Quote-by-Phone Helper', 'job type = Water heater replacement, option = Better, member = 0', 'price = %s, range = %s to %s, deposit = %s, monthly = %s (check the current price)' % (pq['Price to quote'], pq['Lowest price for the job type'], pq['Highest price for the job type'], pq['Deposit to hold the date'], pq['Monthly payment']), ok)
# 18 tier whatif
tw_ = V['tier_whatif']; sgd, sbd = 0.25, 0.52; ssd = round(1 - 0.25 - 0.52, 2)
sh = [round(sum(1 for e in w12 if e['option_chosen'] == o) / float(n), 2) for o in ('Good', 'Better')]; sh.append(round(1 - sh[0] - sh[1], 2))
at = sh[0] * 4025 + sh[1] * 5700 + sh[2] * 7075; ac = sh[0] * PBd['PB-024']['cost'] + sh[1] * PBd['PB-025']['cost'] + sh[2] * PBd['PB-026']['cost']
ok = chk('w', 'at', tw_['Average ticket'], at, 0.002) and chk('w', 'gp', tw_['Gross profit a month'], int(round(n / 12.0)) * (at - ac), 0.003)
line('Margin-by-Tier What-If', 'prices = 4025/5700/7075, shares = %s, jobs a month = %d, target = 40%%' % ('/'.join('%d' % round(x * 100) for x in sh), int(round(n / 12.0))), 'average ticket = %.0f, gross profit a month = %.0f, margin = %.3f, verdict = %s' % (tw_['Average ticket'], tw_['Gross profit a month'], tw_['Average margin'], tw_['Verdict']), ok)
print('\n'.join(lines)); print('FAILS', fails)
if '--write' in sys.argv: open('/home/claude/work/hv/out2/qa.txt', 'w').write('\n'.join(lines) + '\n')
