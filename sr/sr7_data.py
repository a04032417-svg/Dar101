"""Short-term rental host suite part 7: demo rows from sr_core plus generated owner rows (same owners, units, months)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sr7_lists import *
import collections

dd = to_date
R = rng('sr7')
UNI = {u['unit_id']: u for u in units}; UNN = {u['name']: u for u in units}
OWNP = {o['name']: o['phone'] for o in owners}
HOST = OWNER
MANAGED = [o['name'] for o in owners if o['mgmt_pct'] > 0]
MUNITS = [u for u in units if u['owner'] != HOST]
OWNER_PHONE = team[0]['phone']; COHOST_PHONE = team[1]['phone']
ACCT_PHONE = [t for t in team if t['role'] == 'Accountant'][0]['phone']
BKF = booking_rows()
STM = owner_statement_rows(); TAX = tax_rows(); CFE = cohost_fee_rows(); MNT = maintenance_rows()
def nb(d): return {k: v for k, v in d.items() if v not in ('', None, 0, 0.0)}
def nz(d): return {k: v for k, v in d.items() if v not in ('', None)}
def nm(m): return m[:7]
def nxt(m, day):
    y, mo = int(m[:4]), int(m[5:7]) + 1
    if mo > 12: y += 1; mo = 1
    return '%d-%02d-%02d' % (y, mo, day)
def clip(d): return d if d <= ago(0) else ''

# ---------- team (12) and owners (4), cities (4)
def team_d():
    return [nz(dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), phone=t['phone'], email=t['email'], hours_week=t['hours_week'], hourly_rate=t['hourly_rate'],
                    speciality=t['speciality'], country=t['country'], start=t['start'])) for t in team]
def owners_d(): return [dict(name=o['name'], kind=key('okind', o['kind']), mgmt_pct=o['mgmt_pct']) for o in owners] + [dict(name=COMPANY, kind=key('okind', 'Company account'), mgmt_pct=0.0)]
def cities_d(): return [dict(city=key('city', c['city']), collector=key('coll', w), tax_pct=c['tax_pct']) for c in cities for w in ('Host', 'Platform')]
def units_d():
    return [dict(unit_id=u['unit_id'], name=u['name'], unit_type=u['unit_type'], city=key('city', u['city']), owner=u['owner'], mgmt_pct=u['mgmt_pct'], since=u['since'], owner_phone=OWNP[u['owner']]) for u in units]

# ---------- owner statements (45)
def statements_d():
    r = rng('sr7-sent'); out = []
    for s in STM:
        sent = ''
        if s['status'] != 'Draft': sent = nxt(s['month'], r.choice([2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 5, 6, 7]))
        out.append(nz(dict(statement_id=s['statement_id'], month=s['month'], owner=s['owner'], units=s['units'], nights=s['nights'], revenue=s['revenue'], platform_fees=s['platform_fees'],
                           cleaning_costs=s['cleaning_costs'], supplies=s['supplies'], maintenance=s['maintenance'], utilities=s['utilities'], mgmt_pct=s['mgmt_pct'], mgmt_fee=s['mgmt_fee'],
                           net_to_owner=s['net_to_owner'], status=key('stmst', s['status']), sent_on=sent, paid_on=s['paid_on'])))
    return out

# ---------- statement lines (about 380: last 13 months, split by unit)
def _split(total, w):
    out = [round(total * x, 2) for x in w]; out[-1] = round(total - sum(out[:-1]), 2); return out
def lines_d():
    out = []; n = 0; start = month_start(12).isoformat()
    for s in STM:
        if s['month'] < start: continue
        ms = nm(s['month']); us = [u for u in MUNITS if u['owner'] == s['owner'] and u['since'] <= s['month'][:7] + '-28'][:] or [u for u in MUNITS if u['owner'] == s['owner']]
        # the statement says how many units it covers
        us = us[:s['units']] if len(us) >= s['units'] else us
        bk = {u['unit_id']: [b for b in BKF if b['unit_id'] == u['unit_id'] and nm(b['check_out']) == ms and b['status'] != 'Cancelled'] for u in us}
        wts = [sum(b['earned'] for b in bk[u['unit_id']]) for u in us]
        tot = sum(wts); w = [x / tot for x in wts] if tot > 0 else [1.0 / len(us)] * len(us)
        tk = {u['unit_id']: [m for m in MNT if m['unit_id'] == u['unit_id'] and m['done_on'] and nm(m['done_on']) == ms and m['cost'] > 0] for u in us}
        kinds = [('Revenue', s['revenue']), ('Platform fees', s['platform_fees']), ('Cleaning', s['cleaning_costs']), ('Supplies', s['supplies']), ('Maintenance', s['maintenance']),
                 ('Utilities', s['utilities']), ('Management fee', s['mgmt_fee'])]
        for kind, val in kinds:
            if not val: continue
            if kind == 'Maintenance':
                wk = [sum(m['cost'] for m in tk[u['unit_id']]) for u in us]
                ww = [x / sum(wk) for x in wk] if sum(wk) > 0 else w
            else: ww = w
            for u, a in zip(us, _split(val, ww)):
                if a <= 0: continue
                ref = ''
                if kind == 'Revenue' and bk[u['unit_id']]: ref = max(bk[u['unit_id']], key=lambda b: b['earned'])['booking_id']
                if kind == 'Maintenance' and tk[u['unit_id']]: ref = max(tk[u['unit_id']], key=lambda m: m['cost'])['ticket_id']
                n += 1
                out.append(nz(dict(line_id='SL-%04d' % n, statement=s['statement_id'], unit=u['name'], month=s['month'], kind=key('lkind', kind), amount=a, ref_id=ref)))
    return out

# ---------- owner payments (about 58)
def payments_d():
    r = rng('sr7-pay'); out = []; n = 0
    def add(st, date, amt, meth, status):
        nonlocal n; n += 1
        out.append(dict(pay_id='OP-%03d' % n, statement=st['statement_id'], date=date, amount=round(amt, 2), method=key('pmeth', meth), status=key('pstat', status)))
    for s in STM:
        meth = r.choice(['Bank transfer', 'Bank transfer', 'Bank transfer', 'Standing order', 'Card payout'])
        if s['status'] == 'Paid':
            if r.random() < 0.3 and s['net_to_owner'] > 1500:   # an advance and the balance
                a = round(s['net_to_owner'] * r.choice([0.4, 0.5, 0.6]), 2)
                d0 = dd(s['paid_on']) - __import__('datetime').timedelta(days=r.choice([4, 5, 6])); add(s, d0.isoformat(), a, meth, 'Paid'); add(s, s['paid_on'], s['net_to_owner'] - a, meth, 'Paid')
            else: add(s, s['paid_on'], s['net_to_owner'], meth, 'Paid')
        elif s['status'] == 'Sent':
            if s['owner'] == 'Ingrid Solberg':
                add(s, ago(7), 2000.0, meth, 'Paid'); add(s, ahead(1), s['net_to_owner'] - 2000.0, meth, 'Scheduled')
            elif s['owner'] == 'Pablo Reyes': add(s, ahead(2), s['net_to_owner'], meth, 'Scheduled')
            else: add(s, ago(2), s['net_to_owner'], meth, 'Delayed')
        else: add(s, nxt(s['month'], 10), s['net_to_owner'], meth, 'Scheduled')
    return out

# ---------- co-host fees (24) and duties (60)
def cohost_fees_d():
    return [nb(dict(fee_id=c['fee_id'], month=c['month'], units=c['units'], revenue=c['revenue'], platform_fees=c['platform_fees'], net_revenue=c['net_revenue'], fee_pct=c['fee_pct'],
                    fee_amount=c['fee_amount'], messages=c['messages'], status=c['status'], paid_on=c['paid_on'])) for c in CFE]
def duties_d():
    r = rng('sr7-duty'); cu = [u['name'] for u in units if u['cohost'] == 'Yes']; rows = []
    days = [r.randint(0, 350) for _ in range(46)] + [r.randint(0, 28) for _ in range(8)]
    for d in days: rows.append((ago(d), 'Yes' if d > 0 or r.random() < 0.9 else 'No'))
    for d in (1, 3, 5, 8): rows.append((ahead(d), 'No'))
    rows.append((ago(9), 'No')); rows.append((ago(16), 'No'))
    rows.sort(); out = []
    for i, (d, dn) in enumerate(rows):
        t = r.choice(DUTY); mins = {'Guest messages': (20, 90), 'Check-in help': (30, 75), 'Key handover': (15, 45), 'Review replies': (15, 40), 'Calendar check': (10, 30), 'Listing update': (25, 80),
                                    'Issue follow-up': (20, 120), 'Owner update': (15, 50)}[t]
        out.append(dict(duty_id='CD-%03d' % (i + 1), date=d, task=key('duty', t), unit=r.choice(cu), minutes=5 * r.randint(mins[0] // 5, mins[1] // 5), done=key('yn', dn)))
    return out

# ---------- bookings on owner units (about 320)
def bookings_d():
    lim = month_start(12).isoformat(); out = []
    for b in BKF:
        u = UNI[b['unit_id']]
        if u['owner'] == HOST or b['check_out'] < lim: continue
        out.append(nb(dict(booking_id=b['booking_id'], unit=b['unit'], owner=u['owner'], guest=b['guest'], check_in=b['check_in'], check_out=b['check_out'], nights=b['nights'], earned=b['earned'],
                           platform_fee=b['platform_fee'], status=key('bstatus', b['status']))))
    return sorted(out, key=lambda x: (x['check_out'], x['booking_id']))

# ---------- local tax (88), adjustments (30)
_DIFF = {}
def local_tax_d():
    r = rng('sr7-tax'); out = []
    for i, t in enumerate(TAX):
        t = dict(t)
        if t['month'] == '2026-09-01' and t['city'] == 'Porto': t['status'] = 'Due'; t['paid_on'] = ''; t['remitted'] = 0.0
        part = round(t['tax_collected'] - t['collected_by_host'], 2); rep = part
        if r.random() < 0.075 and t['month'] >= '2025-02-01': rep = round(part + r.choice([-1, 1]) * r.uniform(6, 38), 2); _DIFF[(t['month'], t['city'])] = round(rep - part, 2)
        out.append(nb(dict(tax_id=t['tax_id'], month=t['month'], city=key('city', t['city']), tax_pct=t['tax_pct'], nights=t['nights'], room_revenue=t['room_revenue'], tax_collected=t['tax_collected'],
                           collected_by_host=t['collected_by_host'], platform_reported=rep, due_date=t['due_date'], remitted=t['remitted'], paid_on=t['paid_on'], status=key('taxst', t['status']))))
    return out
def adjustments_d():
    local_tax_d()
    r = rng('sr7-adj'); rows = []; used = set()
    cityk = {c['city']: key('city', c['city']) for c in cities}
    for (m, c), diff in _DIFF.items(): rows.append((m, c, -diff, r.choice(['Platform report timing', 'Cancelled stay refund', 'Rate applied in error']))); used.add((m, c))
    cand = [(t['month'], t['city']) for t in TAX if (t['month'], t['city']) not in used]
    recent = [x for x in cand if x[0] >= '2026-09-01']
    for x in r.sample(recent, 4) + r.sample([c for c in cand if c[0] < '2026-09-01'], max(0, 30 - len(rows) - 4)):
        rows.append((x[0], x[1], round(r.choice([-1, 1]) * r.uniform(3, 46), 2), r.choice(['Late booking added', 'Long stay exemption', 'Owner stay not taxed', 'Rounding difference', 'Cancelled stay refund'])))
    rows.sort(); out = []
    for i, (m, c, a, why) in enumerate(rows[:30]):
        f = clip(nxt(m, r.randint(8, 24))) if m < '2026-10-01' else ''
        out.append(nz(dict(adj_id='TA-%03d' % (i + 1), month=m, city=cityk[c], reason=key('adj', why), amount=round(a, 2), filed_on=f)))
    return out

# ---------- management fee tiers (12)
def tiers_d():
    bands = [('1 unit', 1, 1), ('2 to 3 units', 2, 3), ('4 to 6 units', 4, 6), ('7 or more units', 7, 99)]
    pct = {'Basic': [0.14, 0.13, 0.12, 0.11], 'Standard': [0.17, 0.16, 0.15, 0.14], 'Full': [0.20, 0.20, 0.19, 0.18]}
    sv = {'Basic': 'Listing, guest messages and calendar', 'Standard': 'Basic plus cleaning, linen and supplies', 'Full': 'Standard plus repairs, pricing and monthly owner statement'}
    return [dict(tier='%s, %s' % (p, b[0]), package=key('pkg', p), units_from=b[1], units_to=b[2], fee_pct=pct[p][i], services=sv[p]) for p in PKG for i, b in enumerate(bands)]

# ---------- owner requests (about 50)
def requests_d():
    r = rng('sr7-req'); out = []; cost = {'Replace an item': (40, 320), 'Deep clean': (90, 180), 'Repair approval': (80, 640), 'New linen': (60, 210), 'Photo refresh': (120, 260), 'Owner visit': None, 'Price review': None, 'Copy of a report': None}
    days = sorted([r.randint(0, 355) for _ in range(42)] + [r.randint(0, 18) for _ in range(8)], reverse=True)
    for i, d in enumerate(days):
        o = r.choice(MANAGED); u = r.choice([x for x in MUNITS if x['owner'] == o]); q = 'Replace an item' if i == 0 else r.choice(REQ); c = cost[q]
        done = '' if (d <= 18 and r.random() < 0.75 and i > 0) else clip((dd(ago(d)) + __import__('datetime').timedelta(days=r.randint(1, 12))).isoformat())
        out.append(nz(dict(req_id='OR-%03d' % (i + 1), date=ago(d), owner=o, unit=u['name'], request=key('req', q), done_on=done, cost=round(r.uniform(*c), 2) if c else '')))
    return out

# ---------- owner stays (24)
def stays_d():
    r = rng('sr7-stay'); out = []; rows = []
    for d in sorted([r.randint(-90, -3) for _ in range(4)] + [r.randint(5, 330) for _ in range(20)], reverse=True):
        o = r.choice(MANAGED); u = r.choice([x for x in MUNITS if x['owner'] == o]); n = r.randint(2, 7)
        ci = dd(ago(d)); co = ci + __import__('datetime').timedelta(days=n)
        rows.append((ci.isoformat(), co.isoformat(), o, u))
    rows.sort()
    for i, (ci, co, o, u) in enumerate(rows):
        out.append(dict(stay_id='SY-%02d' % (i + 1), owner=o, unit=u['name'], check_in=ci, check_out=co, cleaning_charged=float(u['cleaning_fee']), linen_charged=float(r.choice([12, 15, 18, 22, 26]) + len(u['name']) % 5)))
    return out

# ---------- owner reserves (36)
def reserves_d():
    r = rng('sr7-res'); out = []; n = 0; months = [month_start(k).isoformat() for k in range(11, -1, -1)]
    bal = {o: 0.0 for o in MANAGED}; cfg = {'Ingrid Solberg': 1500.0, 'Pablo Reyes': 1200.0, 'Wen Zhao': 1000.0}
    for mi, m in enumerate(months):
        for o in MANAGED:
            held = spent = 0.0
            if mi == 0: held = cfg[o]; spent = round(r.uniform(60, 140), 2)
            else:
                if r.random() < 0.42: spent = round(r.uniform(70, 460), 2)
                if o == 'Pablo Reyes' and mi == 11: spent = 520.0
            b = bal[o] + held - spent
            if mi > 0 and mi < 11 and b < 700: held = round(cfg[o] - b, 2) if r.random() < 0.9 else 0.0
            elif mi == 11 and o == 'Wen Zhao' and b < 800: held = 0.0
            bal[o] = bal[o] + held - spent; n += 1
            out.append(nb(dict(reserve_id='RV-%03d' % n, month=m, owner=o, reserve_held=round(held, 2), spent=round(spent, 2))))
    return out

# ---------- expenses (about 300): owner units, portfolio costs and recent costs of the host's own units
def expenses_d():
    keep = []
    for e in expense_rows():
        mu = e['unit_id'] and UNI[e['unit_id']]['owner'] != HOST
        if mu or e['unit'] == 'Portfolio' or e['date'] >= ago(100): keep.append(e)
    keep.sort(key=lambda e: (e['date'], e['expense_id']))
    return [dict(expense_id=e['expense_id'], date=e['date'], unit=e['unit'], category=key('ecat', e['category']), description=e['description'], amount=e['amount'], paid_to=e['paid_to']) for e in keep]

# ---------- cleaner pay (90) and maintenance costs (about 120)
def cleaner_pay_d():
    return [nb(dict(pay_id=c['pay_id'], month=c['month'], cleaner=c['cleaner'], turnovers=c['turnovers'], hours=c['hours'], amount=c['amount'], paid_on=c['paid_on'])) for c in cleaner_pay_rows()]
def maint_d():
    rows = [m for m in MNT if m['cost'] > 0 and m['done_on'] and (UNI[m['unit_id']]['owner'] != HOST)]
    own = [m for m in MNT if m['cost'] > 0 and m['done_on'] and UNI[m['unit_id']]['owner'] == HOST][-24:]
    out = []
    for m in sorted(rows + own, key=lambda m: (m['done_on'], m['ticket_id'])):
        out.append(dict(ticket_id=m['ticket_id'], unit=m['unit'], done_on=m['done_on'], cost=m['cost'], charged_to_owner=key('yn', 'Yes' if UNI[m['unit_id']]['owner'] != HOST else 'No')))
    return out

# ---------- owner contracts (12)
def contracts_d():
    import datetime as dt
    def add(d, months):
        return add_months(d, months)
    terms = {'UN-08': [6, 12, 12], 'UN-09': [6, 12, 12], 'UN-10': [3, 6, 12], 'UN-11': [12], 'UN-12': [6, 12]}
    rows = []
    for uid, ts in terms.items():
        u = UNI[uid]; s = dd(u['since'])
        for t in ts:
            e = add(s, t) - dt.timedelta(days=1); rows.append((s.isoformat(), e.isoformat(), u)); s = e + dt.timedelta(days=1)
    rows.sort(key=lambda x: (x[0], x[2]['unit_id']))
    return [dict(contract_id='OC-%02d' % (i + 1), owner=u['owner'], unit=u['name'], start_date=a, end_date=b, mgmt_pct=u['mgmt_pct'], notice_days=30 if i % 3 else 60) for i, (a, b, u) in enumerate(rows)]

if __name__ == '__main__':
    for n in ['reserves', 'expenses', 'cleaner_pay', 'maint', 'contracts']:
        d = globals()[n + '_d'](); print(n, len(d))
    print(len(_DIFF), collections.Counter(x['status'] for x in requests_d() if 'done_on' not in x) if False else '')
    print(sum(1 for x in requests_d() if 'done_on' not in x), 'open requests')
    print([ (c['start_date'],c['end_date'],c['unit']) for c in contracts_d()])
    print(reserves_d()[-3:], reserves_d()[:2])
