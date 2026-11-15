"""Therapy part 3: demo rows from th_core. The carried clients are every client with a recent session, invoice or payment plus every client with a package, plan, open or written-off invoice, so
every recent window (this month, last 30, 90 days) is complete; aggregated tables (billing, card fees, collection gap, aging by month) come from the full generator output."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from th3_lists import *
import th_core as C
import collections

dd = to_date
ST = C.story()
TS = iso(TODAY)
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def yn(v): return 'yes' if v in ('Yes', True, 'yes') else 'no'
def mo(d): return iso(dt.date(dd(d).year, dd(d).month, 1))

INV_ALL = C.invoice_rows(); PAY_ALL = C.payment_rows(); SES_ALL = C.session_rows(); CLI_ALL = C.client_rows()
CLI = {c['client_id']: c for c in CLI_ALL}
COF = {x['client_id']: x for x in C.card_on_file_rows()}
PKG = C.package_rows(); PLN = C.payment_plan_rows(); PRO_ALL = C.payment_promise_rows()


def _chosen():
    s = set(x['client_id'] for x in SES_ALL if ago(45) <= x['date'] <= TS and x['status'] in ('Attended', 'Late cancel', 'No-show'))
    s |= set(i['client_id'] for i in INV_ALL if i['issued_on'] >= ago(100))
    s |= set(p['client_id'] for p in PKG) | set(p['client_id'] for p in PLN)
    s |= set(i['client_id'] for i in INV_ALL if i['status'] in ('Unpaid', 'Part paid', 'On plan', 'Written off'))
    s |= set(p['client_id'] for p in PAY_ALL if p['date'] >= ago(100) and p['client_id'])
    s.add(ST['overdue_client_id'])
    return s


CH = _chosen()
# a client name must be unique among the carried clients (links hold the name): keep the first of any repeated name
_seen = {}
for cid in sorted(CH):
    _seen.setdefault(CLI[cid]['client'], cid)
CH = set(_seen.values())
CHN = {CLI[c]['client'] for c in CH}
INV = [i for i in INV_ALL if i['client_id'] in CH]
INV_IDS = {i['invoice_id'] for i in INV}
PAY = [p for p in PAY_ALL if (p['client_id'] in CH) or (p['date'] >= ago(100))]
PH = {c['client']: c['phone'] for c in CLI_ALL}


def _late_payers():
    """a few clients of last month's invoices pay late: 1 to 31 days past the due date (the story client stays the oldest, and nobody else is over 42 days)"""
    global INV, PAY
    INV = [dict(i) for i in INV]; PAY = [dict(p) for p in PAY]
    sm0 = iso(C.add_months(dt.date(TODAY.year, TODAY.month, 1), -1))
    used = {ST['overdue_client']}; plan_inv = set()
    for p in PLN:
        for x in str(p.get('invoices', '')).replace(' ', '').split(','): plan_inv.add(x)
    cand = [i for i in INV if i['issued_on'] == sm0 and i['status'] == 'Paid' and i['fee_type'] in ('Standard', 'Sliding scale') and 100 <= i['amount_due'] <= 400 and i['invoice_id'] not in plan_inv
            and CLI[i['client_id']]['status'] in ('Active', 'On hold')]
    rng = C.rng('th3-late'); rng.shuffle(cand)
    plan = [(1, 'u'), (1, 'p'), (8, 'u'), (8, 'u'), (15, 'u'), (15, 'p'), (22, 'u'), (22, 'u'), (28, 'u')]
    k = 0
    for i in cand:
        if k >= len(plan): break
        if i['client'] in used: continue
        day, how = plan[k]; k += 1; used.add(i['client'])
        d0 = dt.date.fromisoformat(sm0).replace(day=day)
        i['issued_on'] = iso(d0); i['due_date'] = iso(d0 + dt.timedelta(days=14))
        pays = [p for p in PAY if p['ref'] == i['invoice_id']]
        if how == 'u':
            i['status'] = 'Unpaid'; i['paid_amount'] = 0.0; i['paid_on'] = ''
            for p in pays: PAY.remove(p)
        else:
            i['status'] = 'Part paid'; i['paid_amount'] = round(i['amount_due'] * 0.5, 2); i['paid_on'] = iso(d0 + dt.timedelta(days=12))
            for p in pays: PAY.remove(p)
            if pays:
                q = dict(pays[0]); q['amount'] = i['paid_amount']; q['card_fee'] = round(q['amount'] * 0.025, 2) if q['method'] == 'Card' else 0.0; q['date'] = i['paid_on']; PAY.append(q)
    return k


_late_payers()


def _late_instalments():
    """two instalments of finished plans were paid 4 days late (the payment and the instalment move together)"""
    for pid in [p['plan_id'] for p in PLN if p['status'] == 'Completed'][1:3]:
        got = sorted((p for p in PAY_ALL if p['kind'] == 'Plan instalment' and p['ref'] == pid), key=lambda p: p['date'])
        if len(got) < 2: continue
        pm = got[1]; nd = iso(dd(pm['date']) + day(4))
        if nd > TS: continue
        for L in (PAY_ALL, PAY):
            for q in L:
                if q['payment_id'] == pm['payment_id']: q['date'] = nd


_late_instalments()


def clients_d():
    out = []
    for cid in sorted(CH):
        c = CLI[cid]; k = COF[cid]
        out.append(nb(dict(client_id=cid, client=c['client'], phone=c['phone'], client_type=c['client_type'], service=key('svc', c['service']), clinician=key('clin', c['clinician']),
                           fee_type=key('feetype', c['fee_type']), sliding_pct=c['sliding_pct'], pay_method=key('paym', c['pay_method']), claim_back=yn(c['claim_back']), card_on_file=yn(k['card_on_file']),
                           autopay=yn(k['autopay']), pays_by_instalment=yn(k['pays_by_instalment']), status=key('cstatus', c['status']), first_session=c['first_session'])))
    return out


def invoices_d():
    return [nb(dict(invoice_id=i['invoice_id'], month=i['month'], client=i['client'], fee_type=key('feetype', i['fee_type']), clinician=key('clin', i['clinician']), sessions=i['sessions'], amount=i['amount'],
                    deposit_applied=i['deposit_applied'], issued_on=i['issued_on'], due_date=i['due_date'], paid_amount=i['paid_amount'], paid_on=i['paid_on'], method=key('paym', i['method']),
                    status=key('invst', i['status']))) for i in INV]


def payments_d():
    return [nb(dict(payment_id=p['payment_id'], date=p['date'], client=p['client'], kind=key('payk', p['kind']), ref=p['ref'], method=key('paym', p['method']), amount=p['amount'], card_fee=p['card_fee']))
            for p in PAY]


def ar_clients_d():
    bal = collections.defaultdict(float); last = {}
    for i in INV:
        if i['status'] == 'Written off': continue
        bal[i['client']] += max(0.0, i['amount_due'] - i['paid_amount']); last[i['client']] = max(last.get(i['client'], ''), i['issued_on'])
    pr = collections.Counter(p['client'] for p in PRO_ALL)
    names = sorted(last, key=lambda n: (-(bal[n] > 0.005), -pr[n], last[n], n))
    names = sorted(names[:260], key=lambda n: (-(bal[n] > 0.005), -bal[n]))
    rng = C.rng('th3-chased')
    out = []
    for k, n in enumerate(names, 1):
        who = 'Amira Lindqvist' if bal[n] >= 600 or (k % 9 == 0) else 'Grace Mensah'
        out.append(dict(ar_id='AR-%03d' % k, client=n, chased_by=who))
    return out


def sessions_d():
    out = []
    for s in SES_ALL:
        if s['client_id'] not in CH or not (ago(45) <= s['date'] <= TS) or s['status'] not in ('Attended', 'Late cancel', 'No-show'): continue
        out.append(nb(dict(session_id=s['session_id'], date=s['date'], time=s['time'], client=s['client'], service=key('svc', s['service']), clinician=key('clin', s['clinician']), status=key('sstatus', s['status']),
                           fee_type=key('feetype', s['fee_type']), fee=s['fee'], charge=s['charge'], client_amount=s['client_amount'], package_id=s['package_id'], fee_waived=yn(s['fee_waived']))))
    return out


def promises_d():
    return [nb(dict(promise_id=p['promise_id'], invoice_id=p['invoice_id'], client=p['client'], logged_on=p['logged_on'], promised_on=p['promised_on'], method=key('pmeth', p['method']),
                    outcome=key('promise', p['outcome']))) for p in PRO_ALL if p['invoice_id'] in INV_IDS and p['client'] in CHN]


def reminders_d():
    rows = []
    for i in INV:
        due = dd(i['due_date']); paid = dd(i['paid_on']) if i['paid_on'] else None
        for n, (gap, m) in enumerate(((3, 'Message'), (10, 'Email'), (24, 'Phone')), 1):
            sent = due + day(gap)
            if sent > TODAY: break
            if paid is not None and paid <= sent: break
            if i['status'] == 'On plan' and n > 1: break
            rows.append((iso(sent), i['invoice_id'], i['client'], n, m, 'yes' if (paid is not None and paid >= sent) else 'no'))
    rows.sort()
    rows = rows[-230:]
    return [dict(reminder_id='RD-%04d' % k, invoice_id=r[1], client=r[2], reminder_no=r[3], sent_on=r[0], method=key('pmeth', r[4]), paid_after=r[5]) for k, r in enumerate(rows, 1)]


def plans_d():
    return [nb(dict(plan_id=p['plan_id'], client=p['client'], start_date=p['start_date'], balance=p['balance'], instalments=p['instalments'], instalment=p['instalment'], paid_instalments=p['paid_instalments'],
                    next_due=p['next_due'], invoices=p['invoices'], status=key('planst', p['status']))) for p in PLN]


def instalments_d():
    out = []; k = 0
    pays = collections.defaultdict(list)
    for p in PAY_ALL:
        if p['kind'] == 'Plan instalment': pays[p['ref']].append(p['date'])
    for a in C._accounts()['plans']:
        pid = a['plan_id']; got = sorted(pays.get(pid, [])); n = a['instalments']
        for j, due in enumerate(a['dates']):
            k += 1; amt = a['instalment'] if j < n - 1 else round(a['balance'] - a['instalment'] * (n - 1), 2)
            paid = got[j] if j < len(got) else ''
            if paid and paid > TS: paid = ''
            out.append(nb(dict(inst_id='PI-%03d' % k, plan_id=pid, due_date=iso(due), amount=amt, paid_on=paid)))
    return out


def packages_d():
    return [nb(dict(package_id=p['package_id'], client=p['client'], kind=key('pkkind', p['kind']), sessions=p['sessions'], price=p['price'], bought_on=p['bought_on'], used=p['used'], expires_on=p['expires_on'],
                    status=key('pkst', p['status']))) for p in PKG]


def ar_months_d():
    return [dict(ageing_id=x['ageing_id'], month=x['month'], as_of=x['as_of'], band=key('ageband', x['band']), invoices=x['invoices'], balance=x['balance']) for x in C.client_ageing_rows()]


def fees_d():
    out = []; k = 0
    for y, fld in ((TODAY.year - 1, 'last_year_fee'), (TODAY.year, 'fee')):
        for s in C.services:
            k += 1; out.append(dict(fee_id='FS-%02d' % k, year=y, service=key('svcall', s['service']), fee=s[fld], minutes=s['minutes']))
    return out


def fee_notices_d():
    """one notice per client and service used in the second half of last year (the fee rise took effect on 1 January)"""
    rng = C.rng('th3-notice'); out = []; k = 0
    jan1 = dt.date(TODAY.year, 1, 1); fee = {s['service']: s for s in C.services}
    seen = set()
    for s in SES_ALL:
        if s['client_id'] not in CH or s['status'] != 'Attended' or not (iso(jan1 - day(182)) <= s['date'] < iso(jan1)): continue
        if s['service'] not in fee or s['service'] == 'Group program' or (s['client_id'], s['service']) in seen: continue
        c = CLI[s['client_id']]
        if c['fee_type'] == 'Third-party payer' or (c['discharge_date'] and dd(c['discharge_date']) < jan1): continue
        seen.add((s['client_id'], s['service']))
    rows = sorted(seen)
    for cid, svc in rows:
        f = fee[svc]; k += 1
        out.append(dict(notice_id='FN-%03d' % k, client=CLI[cid]['client'], service=key('svc', svc), old_fee=f['last_year_fee'], new_fee=f['fee'], sent_on=iso(jan1 - day(rng.randint(42, 75))), effective_date=iso(jan1)))
    return out[:200]


BANDS = [('Band 1', 0, 9999, 0.60), ('Band 2', 10000, 14999, 0.60), ('Band 3', 15000, 19999, 0.60), ('Band 4', 20000, 24999, 0.65), ('Band 5', 25000, 29999, 0.65), ('Band 6', 30000, 34999, 0.70),
         ('Band 7', 35000, 39999, 0.70), ('Band 8', 40000, 44999, 0.75), ('Band 9', 45000, 49999, 0.75), ('Band 10', 50000, 54999, 0.80), ('Band 11', 55000, 59999, 0.80), ('Band 12', 60000, 250000, 0.90)]


def bands_d():
    return [dict(band=b[0], income_from=b[1], income_to=b[2], share=b[3]) for b in BANDS]


def assessments_d():
    rng = C.rng('th3-assess'); out = []; k = 0
    for cid in sorted(CH):
        c = CLI[cid]
        if c['sliding_pct'] >= 1.0: continue
        cand = [b for b in BANDS if abs(b[3] - c['sliding_pct']) < 0.001]
        first = dd(c['first_session']) - day(6); dates = [first]
        while dates[-1] + day(365) <= TODAY - day(10): dates.append(dates[-1] + day(365 + rng.randint(-20, 20)))
        for d in dates:
            if d > TODAY: continue
            b = cand[rng.randint(0, len(cand) - 1)]; k += 1
            out.append(dict(assess_id='SA-%03d' % k, client=c['client'], date=iso(d), household_size=rng.randint(1, 5), income_band=b[0], share_agreed=c['sliding_pct'], review_date=iso(add_months(d, 12))))
    return out


def writeoffs_d():
    why = ['Client unreachable', 'Small balance', 'Moved away', 'Three broken promises', 'Hardship agreed', 'Client left, no reply']
    out = []; k = 0
    for i in INV:
        if i['status'] != 'Written off': continue
        k += 1; d = min(dd(i['due_date']) + day(75 + (k * 7) % 25), TODAY - day(3))
        out.append(dict(writeoff_id='WO-%02d' % k, invoice_id=i['invoice_id'], client=i['client'], date=iso(d), amount=i['amount_due'], reason=why[k % len(why)],
                        approved_by='Amira Lindqvist' if i['amount_due'] >= 100 else 'Grace Mensah'))
    return out


def _gap_month_concessions():
    acc = collections.defaultdict(float)
    for s in SES_ALL:
        if s['date'] > TS: continue
        if s['status'] == 'Attended' and s['fee_type'] == 'Sliding scale': acc[s['month']] += s['fee'] - s['charge']
        if s['fee_waived'] == 'Yes': acc[s['month']] += s['fee'] * C.LATE_FEE_PCT
    return acc


def billing_d():
    conc = _gap_month_concessions(); out = []
    months = [C.add_months(dt.date(TODAY.year, TODAY.month, 1), -k) for k in range(23, -1, -1)]
    for n, M in enumerate(months, 1):
        a = TODAY if (M.year, M.month) == (TODAY.year, TODAY.month) else C._eom(M); ai = iso(a)
        iss = [i for i in INV_ALL if mo(i['issued_on']) == iso(M)]
        owed = 0.0
        for i in INV_ALL:
            if i['status'] == 'Written off' or i['issued_on'] > ai: continue
            paid = i['paid_amount'] if (i['paid_on'] == '' or i['paid_on'] <= ai) else 0.0
            o = round(i['amount_due'] - paid, 2)
            if o > 0.005: owed += o
        sm = iso(C.add_months(M, -1))
        out.append(dict(bill_id='BM-%02d' % n, month=iso(M), sessions_charged=sum(i['sessions'] for i in iss), invoiced=round(sum(i['amount_due'] for i in iss), 2), concessions=round(conc.get(sm, 0.0), 2),
                        collected=round(sum(i['paid_amount'] for i in iss), 2), written_off=round(sum(i['amount_due'] for i in iss if i['status'] == 'Written off'), 2), outstanding_end=round(owed, 2)))
    return out


def gap_d():
    return [dict(gap_id=x['gap_id'], month=x['month'], cause=key('gapcause', x['cause']), amount=x['amount']) for x in C.collection_gap_rows()]


def cardfees_d():
    acc = collections.defaultdict(lambda: [0.0, 0.0, 0.0])
    for p in PAY_ALL:
        a = acc[mo(p['date'])]; a[0] += p['amount']; a[2] += p['card_fee']
        if p['method'] == 'Card': a[1] += p['amount']
    months = [iso(C.add_months(dt.date(TODAY.year, TODAY.month, 1), -k)) for k in range(23, -1, -1)]
    return [dict(month=m, all_payments=round(acc[m][0], 2), card_payments=round(acc[m][1], 2), card_fees=round(acc[m][2], 2)) for m in months]


def team_d():
    return [nb(dict(staff_id=t['staff_id'], name=t['name'], role=t['role'], team=t['team'], pay_type=t['pay_type'], phone=t['phone'], email=t['email'], hours_week=t['hours_week'],
                    monthly_salary=t['monthly_salary'], split_pct=t['split_pct'], session_rate=t['session_rate'], hourly_rate=t['hourly_rate'], session_cap=t['session_cap'], session_target=t['session_target'],
                    speciality=t['speciality'], country=t['country'], start=t['start'])) for t in C.team]


if __name__ == '__main__':
    for f in (clients_d, invoices_d, payments_d, ar_clients_d, sessions_d, promises_d, reminders_d, plans_d, instalments_d, packages_d, ar_months_d, fees_d, fee_notices_d, bands_d, assessments_d, writeoffs_d, billing_d, gap_d,
              cardfees_d, team_d):
        r = f(); print(f.__name__, len(r))
    print(billing_d()[-3:])
