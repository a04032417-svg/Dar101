"""Home care agency suite part 5: demo rows built from hc_core (row-level tables thinned, monthly and aggregate tables built from the full data)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hc5_lists import *
import collections, datetime as _dt

dd = to_date
TODAY_ISO = iso(TODAY)
ST = story()
INV = invoice_rows(); PAY = payment_rows(); DEP = deposit_rows(); CLM = claim_rows(); CLI = client_rows(); VIS = visit_rows(); CMR = client_month_rows()
CL = {c['client_id']: c for c in CLI}
INVD = {i['invoice_id']: i for i in INV}
PH = {s['name']: s['phone'] for s in team}
PAYER_PHONE = {p['payer']: fake_phone(900 + n * 13) for n, p in enumerate(payers) if p['payer'] != 'Private pay'}
OPEN_ST = ('Unpaid', 'Part paid')


def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def yn(b): return 'yes' if b else 'no'
def front(rows, pred):
    for i, r in enumerate(rows):
        if pred(r): return [rows[i]] + rows[:i] + rows[i + 1:]
    return rows
def me_of(d): return add_months(_dt.date(d.year, d.month, 1), 1) - _dt.timedelta(days=1)


# ---------------------------------------------------------------- invoice sample
def _keep(i, r):
    return r['status'] in OPEN_ST or r['written_off'] > 0 or r['issued_on'] >= ago(110) or i % 10 == 0 or (r['payer'] == 'Private pay' and r['days_to_pay'] != '' and r['days_to_pay'] >= 18)
INV_S = [r for i, r in enumerate(INV) if _keep(i, r)]
INV_S_IDS = {r['invoice_id'] for r in INV_S}
LINE_FROM = ago(90)

_vis = collections.defaultdict(list)
for v in VIS:
    if v['billed_hours'] > 0: _vis[v['client_id']].append(v)
_LINES = {}
for r in INV_S:
    if r['issued_on'] < LINE_FROM: continue
    g = collections.OrderedDict()
    for v in _vis[r['client_id']]:
        if r['period_start'] <= v['date'] <= r['period_end']:
            h, a = g.get(v['band'], (0.0, 0.0)); g[v['band']] = (h + v['billed_hours'], a + v['charge'])
    _LINES[r['invoice_id']] = g
LINE_IDS = {k for k, g in _LINES.items() if g}


def invoices_d():
    rows = []
    for r in INV_S:
        rows.append(nb(dict(invoice_id=r['invoice_id'], client_id=r['client_id'], client=r['client'], payer=key('payer', r['payer']), cycle=key('cycle', r['cycle']), period_start=r['period_start'],
                            period_end=r['period_end'], issued_on=r['issued_on'], due_date=r['due_date'], hours=r['hours'], amount=r['amount'], deposit_applied=r['deposit_applied'],
                            paid_amount=r['paid_amount'], paid_on=r['paid_on'], paid_by=key('paidby', r['paid_by']) if r['paid_by'] else '', written_off=r['written_off'], status=key('invst', r['status']))))
    return front(rows, lambda x: x['invoice_id'] == ST['overdue_invoice'])


def lines_d():
    rows = []; n = 0
    for r in INV_S:
        g = _LINES.get(r['invoice_id'])
        if not g: continue
        for b in BANDS:
            if b in g and g[b][0] > 0:
                n += 1; h, a = g[b]
                rows.append(dict(line_id='IL-%04d' % n, invoice_id=r['invoice_id'], client=r['client'], service=key('svc', CL[r['client_id']]['service']), band=key('band', b), hours=round(h, 2),
                                 rate=round(a / h, 2), amount=round(a, 2)))
    return rows


def hours_d():
    rows = []; n = 0; rr = rng('hc5hours')
    mlist = [month_start(k) for k in range(10, 0, -1)]
    for m in mlist:
        nd = (add_months(m, 1) - m).days
        for x in CMR:
            if x['month'] != iso(m): continue
            cl = CL[x['client_id']]
            if x['visits'] < 4 or dd(cl['start_date']) >= m or (cl['end_date'] and dd(cl['end_date']) < add_months(m, 1)): continue
            if rr.random() < 0.18: continue
            n += 1
            rows.append(dict(row_id='HK-%04d' % n, client_id=x['client_id'], client=x['client'], month=x['month'], agreed_hours=round(cl['weekly_hours'] * nd / 7, 1), delivered_hours=round(x['delivered_hours'], 2),
                             billed_hours=round(x['billed_hours'], 2)))
    return rows


# ---------------------------------------------------------------- payments, deposits, ledger
def payments_d():
    rows = []
    for i, p in enumerate(PAY):
        if p['date'] >= ago(150) or i % 8 == 0:
            rows.append(nb(dict(payment_id=p['payment_id'], date=p['date'], client_id=p['client_id'], client=p['client'], kind=key('payk', p['kind']), method=key('paym', p['method']), amount=p['amount'], invoice_id=p['invoice_id'])))
    return rows


def deposits_d():
    return [dict(deposit_id=d['deposit_id'], client_id=d['client_id'], client=d['client'], kind=key('depk', d['kind']), received_on=d['received_on'], amount=d['amount'], used=d['used'], balance=d['balance'],
                 weekly_bill=d['weekly_bill'], status=key('depst', d['status'])) for d in DEP]


def _ledger_events():
    ev = collections.defaultdict(list)
    for p in PAY:
        if p['kind'] == 'Prepayment': ev[p['client_id']].append((p['date'], 0, 'Prepayment', p['amount'], ''))
    for i in INV:
        if i['paid_by'] == 'Prepaid balance': ev[i['client_id']].append((i['paid_on'], 1, 'Invoice payment', -i['paid_amount'], i['invoice_id']))
    for c in ev: ev[c].sort()
    return ev
LEDGER = _ledger_events()


def ledger_d():
    rows = []; n = 0
    for cid in sorted(LEDGER):
        bal = 0.0; seq = []
        for d, _, k, a, inv in LEDGER[cid]:
            bal = round(bal + a, 2); seq.append((d, k, a, bal, inv))
        for d, k, a, bal, inv in seq[-13:]:
            n += 1
            rows.append(nb(dict(ledger_id='PL-%03d' % n, client_id=cid, client=CL[cid]['client'], date=d, top_up=yn(k == 'Prepayment'), amount=round(a, 2), balance_after=bal, invoice_id=inv)))
    return rows


def prepaid_month_balance():
    """total prepaid balance at each month end (clients whose prepayment is still held)"""
    held = {d['client_id'] for d in DEP if d['kind'] == 'Prepayment' and d['status'] == 'Held'}
    out = {}
    for k in range(23, -1, -1):
        me = me_of(month_start(k)) if k else TODAY
        tot = 0.0
        for cid in held:
            for d, _, kind, a, inv in LEDGER[cid]:
                if d <= iso(me): tot += a
        out[iso(month_start(k))] = round(max(tot, 0), 2)
    return out


# ---------------------------------------------------------------- ageing
def _cleared(r):
    if r['status'] == 'Paid': return dd(r['paid_on']) if r['paid_on'] else dd(r['issued_on'])
    if r['status'] == 'Written off': return _wo_date(r)
    return None
def _wo_date(r):
    if r['paid_on']: return dd(r['paid_on'])
    return min(dd(r['due_date']) + _dt.timedelta(days=75), TODAY - _dt.timedelta(days=1))
def _open_amt(r):
    a = r['amount'] - r['deposit_applied']
    if r['status'] == 'Part paid': a -= r['paid_amount']
    return max(a, 0.0)
def _open_at(r, me):
    if dd(r['issued_on']) > me: return 0.0
    c = _cleared(r)
    if c is not None and c <= me: return 0.0
    return _open_amt(r)
def _bucket(days):
    return 0 if days <= 30 else 1 if days <= 60 else 2 if days <= 90 else 3


def ageing_month_d():
    rows = []
    for k in range(13, -1, -1):
        me = me_of(month_start(k)) if k else TODAY
        b = [0.0] * 4
        for r in INV:
            a = _open_at(r, me)
            if a > 0: b[_bucket(max(0, (me - dd(r['issued_on'])).days))] += a
        rows.append(dict(as_of=iso(me), age_0_30=round(b[0], 2), age_31_60=round(b[1], 2), age_61_90=round(b[2], 2), age_90_plus=round(b[3], 2)))
    return rows


def ageing_client_d():
    rows = []
    for c in CLI:
        if c['status'] == 'Active': rows.append(dict(client_id=c['client_id'], reviewed_on=ago(1 + int(rng('rev' + c['client_id']).random() * 40))))
    return front(rows, lambda x: x['client_id'] == ST['overdue_client_id'])


def days_to_pay_d():
    rows = []; pm = prepaid_month_balance(); last_p, last_q = 12.0, 42.0
    for k in range(23, -1, -1):
        m = month_start(k); mi = iso(m); nx = iso(add_months(m, 1))
        iss = [r for r in INV if r['month'] == mi]
        paid_in = [r for r in INV if r['paid_on'] and mi <= r['paid_on'] < nx]
        pr = [r['days_to_pay'] for r in paid_in if r['payer'] == 'Private pay' and r['days_to_pay'] != '']
        py = [r['days_to_pay'] for r in paid_in if r['payer'] != 'Private pay' and r['days_to_pay'] != '']
        if pr: last_p = sum(pr) / len(pr)
        if py: last_q = sum(py) / len(py)
        due = [r for r in INV if mi <= r['due_date'] < nx and r['due_date'] <= TODAY_ISO]
        den = sum(r['amount'] for r in due)
        share = (sum(r['paid_amount'] + r['deposit_applied'] for r in due) / den) if den else 0.95
        rec = sum(p['amount'] for p in PAY if mi <= p['date'] < nx)
        rows.append(dict(month=mi, invoices=len(iss), invoiced=round(sum(r['amount'] for r in iss), 2), received=round(rec, 2), private_days=round(last_p, 1), payer_days=round(last_q, 1),
                         collected_share=round(min(share, 1.0), 4), prepaid_balance=pm[mi]))
    return rows


# ---------------------------------------------------------------- statements
def statements_d():
    rows = []; n = 0
    cl_ids = [c['client_id'] for c in CLI if c['status'] == 'Active' and c['billing_cycle'] == 'Monthly']
    pick = [ST['overdue_client_id']] + [c for c in cl_ids if c != ST['overdue_client_id']][:9]
    mlist = [month_start(k) for k in range(10, 0, -1)]
    mine = collections.defaultdict(list)
    for r in INV: mine[r['client_id']].append(r)
    for cid in pick:
        for m in mlist:
            me = me_of(m); pme = me_of(add_months(m, -1))
            op = sum(_open_at(r, pme) for r in mine[cid]); cl = sum(_open_at(r, me) for r in mine[cid])
            invd = sum(r['amount'] - r['deposit_applied'] for r in mine[cid] if m <= dd(r['issued_on']) <= me)
            n += 1
            rows.append(dict(statement_id='ST-%04d' % n, client_id=cid, client=CL[cid]['client'], month=iso(m), opening=round(op, 2), invoiced=round(invd, 2), paid=round(op + invd - cl, 2), closing=round(cl, 2),
                             sent_on=iso(me + _dt.timedelta(days=1))))
    return rows


# ---------------------------------------------------------------- collections
def collections_d():
    ev = []; rr = rng('hc5coll')
    for r in INV_S:
        if r['payer'] != 'Private pay': continue
        due = dd(r['due_date']); op = r['status'] in OPEN_ST
        paid = dd(r['paid_on']) if (r['paid_on'] and not op) else None
        late = (TODAY - due).days if op else ((paid - due).days if paid else 0)
        if late < 4: continue
        offs = [1, 5, 11, 22, 36, 50]; n = 1 + sum(late > x for x in (9, 15, 27, 39, 51))
        acts = [('Reminder message', 'Left message'), ('Phone call', 'Promised to pay'), ('Phone call', 'No answer'), ('Letter', 'Left message'), ('Phone call', 'Promised to pay'), ('Final notice', 'No answer')]
        story = r['invoice_id'] in ST['overdue_invoices']
        for k in range(n):
            d = due + _dt.timedelta(days=offs[k] + rr.randint(0, 2)); a, o = acts[k]
            if d > TODAY: continue
            if story and k == 3: a, o = 'Payment plan offered', 'Plan agreed'
            if k == n - 1 and paid: a, o, d = 'Phone call', 'Paid', paid
            if o == 'Dispute': pass
            prom = ''; kept = ''
            if o in ('Promised to pay', 'Plan agreed'):
                pd_ = d + _dt.timedelta(days=rr.randint(4, 9)); prom = iso(pd_)
                kept = yn(bool(paid) and paid <= pd_ + _dt.timedelta(days=1)) if pd_ <= TODAY else ''
            ev.append(nb(dict(date=iso(d), client_id=r['client_id'], client=r['client'], invoice_id=r['invoice_id'], action=key('colact', a), outcome=key('colout', o), promised_on=prom, kept=kept)))
    ev.sort(key=lambda x: x['date'])
    keep = ev[-170:]
    for n, e in enumerate(keep, 1): e['call_id'] = 'CC-%04d' % n
    out = [dict(call_id=e['call_id'], **{k: v for k, v in e.items() if k != 'call_id'}) for e in keep]
    return front(out, lambda x: x.get('promised_on') and x.get('kept'))


# ---------------------------------------------------------------- claims
def claims_d():
    rows = []
    for c in CLM:
        rows.append(nb(dict(claim_id=c['claim_id'], invoice_id=c['invoice_id'], client_id=c['client_id'], client=c['client'], payer=key('cpayer', c['payer']), month=c['month'], hours=c['hours'],
                            billed_amount=c['billed_amount'], submitted_on=c['submitted_on'], status=key('clmst', c['status']), reason=key('clmrsn', c['reason']) if c['reason'] else '',
                            resubmitted_on=c['resubmitted_on'], paid_on=c['paid_on'], paid_amount=c['paid_amount'], short_amount=c['short_amount'], payer_phone=PAYER_PHONE[c['payer']])))
    return front(rows, lambda x: x['status'] == key('clmst', 'Short-paid') and x.get('paid_on') and x.get('reason') and x['submitted_on'] > ago(300))


OPEN_CLM = ('Submitted', 'Accepted', 'Resubmitted', 'Rejected')


def claim_status_d():
    g = collections.OrderedDict()
    for c in CLM:
        k = (c['payer'], c['month']); g.setdefault(k, []).append(c)
    rows = []; n = 0
    for (p, m), cs in sorted(g.items(), key=lambda t: (t[0][1], t[0][0])):
        n += 1
        rows.append(dict(row_id='CS-%03d' % n, payer=key('cpayer', p), month=m, submitted=len(cs), paid=sum(c['status'] == 'Paid' for c in cs), short_paid=sum(c['status'] == 'Short-paid' for c in cs),
                         rejected=sum(c['status'] == 'Rejected' for c in cs), outstanding=round(sum(c['billed_amount'] for c in cs if c['status'] in OPEN_CLM), 2),
                         short_amount=round(sum(c['short_amount'] for c in cs), 2), billed=round(sum(c['billed_amount'] for c in cs), 2)))
    return rows


def resubmit_d():
    rows = []; notes = {'Hours mismatch': 'Attach the signed hours sheet', 'Rate difference': 'Check the agreed rate', 'Missing details': 'Add the missing details',
                        'Authorisation missing': 'Ask for the authorisation reference', 'Late submission': 'Explain the late submission', '': 'Check the payer remittance'}
    names = [PH_NAME for PH_NAME in ('Priyanka Nair',)] * 1
    for c in CLM:
        if c['status'] not in ('Rejected', 'Resubmitted', 'Short-paid', 'Written off'): continue
        by = iso(dd(c['submitted_on']) + _dt.timedelta(days=21)) if c['status'] in ('Rejected', 'Resubmitted') else ''
        rows.append(nb(dict(claim_id=c['claim_id'], handled_by='Priyanka Nair', resubmit_by=by, next_step=notes.get(c['reason'], notes['']))))
    return front(rows, lambda x: x['claim_id'] == 'CP-0239')


def payer_payments_d():
    g = collections.OrderedDict()
    for c in CLM:
        if c['paid_on'] and c['paid_amount'] > 0: g.setdefault((c['payer'], c['paid_on']), []).append(c)
    items = sorted(g.items(), key=lambda t: (t[0][1], t[0][0]))[-155:]
    return [dict(row_id='PP-%03d' % n, payer=key('cpayer', p), date=d, claims_paid=len(cs), amount=round(sum(c['paid_amount'] for c in cs), 2)) for n, ((p, d), cs) in enumerate(items, 1)]


def writeoffs_d():
    rows = []; n = 0
    for r in INV:
        if r['written_off'] <= 0: continue
        n += 1; pv = r['payer'] == 'Private pay'
        rsn = ('Client not reachable' if n % 2 else 'Client dispute') if pv else ['Payer would not pay', 'Billing error', 'Payer would not pay', 'Small balance'][n % 4]
        if r['written_off'] < 300 and not pv: rsn = 'Small balance'
        rows.append(dict(writeoff_id='WO-%02d' % n, invoice_id=r['invoice_id'], client=r['client'], date=iso(_wo_date(r)), amount=round(r['written_off'], 2), reason=key('wrsn', rsn),
                         approved_by='Marguerite Adeyemi' if r['written_off'] > 500 else 'Priyanka Nair'))
    return rows


# ---------------------------------------------------------------- reference tables
def clients_d():
    rows = []
    for c in CLI:
        rows.append(nb(dict(client_id=c['client_id'], client=c['client'], phone=c['phone'], email=c['email'], payer=key('payer', c['payer']), service=key('svc', c['service']), billing_cycle=key('cycle', c['billing_cycle']),
                            weekly_hours=c['weekly_hours'], bill_rate=c['bill_rate'], deposit=c['deposit'], prepay=yn(c['prepay']), status=c['status'], start_date=c['start_date'])))
    return rows


def team_d():
    return [dict(staff_id=t['staff_id'], name=t['name'], role=t['role'], team=t['team'], pay_type=t['pay_type'], phone=t['phone'], email=t['email'], hours_week=t['hours_week'], monthly_salary=int(t['monthly_salary']),
                 hourly_rate=int(t['hourly_rate']), speciality=t['speciality'], country=t['country'], start=t['start']) for t in team]
def payers_d(): return [dict(payer=p['payer'], rate_share=p['rate_share'], pay_days=p['pay_days']) for p in payers] + [dict(payer='Prepaid balance', rate_share=1.0, pay_days=0)]
def rate_card_d(): return [dict(service=key('svc', r['service']), band=key('band', r['band']), bill_rate=r['bill_rate']) for r in rate_card]


if __name__ == '__main__':
    for f in (invoices_d, lines_d, hours_d, payments_d, deposits_d, ledger_d, ageing_month_d, ageing_client_d, days_to_pay_d, statements_d, collections_d, claims_d, claim_status_d, resubmit_d, payer_payments_d, writeoffs_d):
        r = f(); print(f.__name__, len(r), r[0])
    print(ageing_month_d()[-1], sum(_open_amt(r) for r in INV if r['status'] in OPEN_ST))
    print(days_to_pay_d()[-3:])
