"""Childcare center suite part 5: demo rows from cc_core."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc5_lists import *
import datetime as dt

ST = story()
expense_rows()                       # cc_core builds bills from expenses: call it first
TEAM = {t['staff_id']: t for t in team}
OWNER_PHONE = TEAM['CC-01']['phone']; AD_PHONE = TEAM['CC-02']['phone']; ACC_PHONE = TEAM['CC-13']['phone']
SUP_PHONE = TEAM['CC-14']['phone']; MAINT_PHONE = TEAM['CC-16']['phone']
def nb(d): return {k: v for k, v in d.items() if v not in ('', None, 0, 0.0)} if False else {k: v for k, v in d.items() if v not in ('', None)}
def nz(d, *keys):
    """drop the listed keys when zero (blank money cells keep the depth gate happy)"""
    return {k: v for k, v in d.items() if not (k in keys and not v)}

INV = invoice_rows(); PAY = payment_rows(); FAM = family_rows(); GOV = gov_payment_rows()
FAMD = {f['family']: f for f in FAM}


def invoices_d():
    out = []
    for i in INV[-1480:]:
        d = dict(invoice_id=i['invoice_id'], family=i['family'], cycle=key('cycle', i['cycle']), issued_on=i['issued_on'], due_date=i['due_date'], amount=i['amount'],
                 gov_expected=i['gov_expected'], paid_amount=i['paid_amount'], paid_on=i['paid_on'], status=key('istatus', i['status']))
        out.append(nb(nz(d, 'gov_expected', 'paid_amount')))
    return out


def payments_d():
    rows = PAY[-1480:]; ids = {p['payment_id'] for p in rows}
    rows = [p for p in PAY if p['kind'] == 'Plan instalment' and p['payment_id'] not in ids] + rows
    return [nb(dict(payment_id=p['payment_id'], date=p['date'], family=p['family'], invoice_id=p['invoice_id'], amount=p['amount'], method=key('method', p['method']), kind=key('paykind', p['kind']))) for p in rows]


def families_d():
    return [dict(family_id=f['family_id'], family=f['family'], guardian=f['guardian'], phone=f['phone'], email=f['email'], cycle=key('cycle', f['cycle']), pay_method=key('method', f['pay_method']),
                 autopay=bool(f['autopay']), habit=key('habit', f['habit']), gov_share=f['gov_share'] or None, late_prone=bool(f['late_prone']), first_start=f['first_start'])
            for f in FAM]


def aging_d(): return [dict(ageing_id=a['ageing_id'], family=a['family']) for a in ageing_rows()]


def aging_month_d(): return [nb(dict(row_id=a['row_id'], month=a['month'], band=key('band', a['band']), amount=a['amount'] or None)) for a in ageing_month_rows()]


def promises_d():
    return [dict(promise_id=p['promise_id'], promised_on=p['promised_on'], family=p['family'], invoice_id=p['invoice_id'], promised_amount=p['promised_amount'],
                 method=key('pmethod', p['method']), outcome=key('outcome', p['outcome'])) for p in promise_rows()]


PLANS = [dict(plan_id=p['plan_id'], balance=p['balance'], instalments=p['instalments'], family=p['family'], first_due=p['first_due']) for p in plan_rows()]
PLANS.append(dict(plan_id='PP-04', balance=1266.0, instalments=4, family='Garcia family', first_due=ahead(3)))
PLANS.append(dict(plan_id='PP-05', balance=555.04, instalments=3, family='Barbosa family', first_due=ahead(10)))


def plans_d(): return [dict(plan_id=p['plan_id'], balance=p['balance'], instalments=p['instalments']) for p in PLANS]


def instalments_d():
    out = []; n = 0
    for p in PLANS:
        fd = to_date(p['first_due'])
        for k in range(1, p['instalments'] + 1):
            n += 1; due = add_months(fd, k - 1)
            paid = iso(due) if due <= TODAY and p['plan_id'] not in ('PP-04', 'PP-05') else ''
            out.append(nb(dict(inst_id='PI-%02d' % n, plan=p['plan_id'], family=p['family'], number=k, first_due=p['first_due'], paid_on=paid)))
    return out


def gov_d():
    return [nb(dict(gov_id=g['gov_id'], month=g['month'], family=g['family'], expected=g['expected'], received=g['received'] or None, due_on=g['due_on'], paid_on=g['paid_on'],
                    status=key('govstatus', g['status']))) for g in GOV]


def gov_month_d():
    ms = sorted({g['month'] for g in GOV})[-24:]
    return [dict(gm_id='GM-%02d' % i, month=m) for i, m in enumerate(ms, 1)]


def deposits_d():
    return [nb(dict(deposit_id=d['deposit_id'], child_id=d['child_id'], child=d['child'], family=d['family'], amount=d['amount'], received_on=d['received_on'], status=key('depstatus', d['status']),
                    settled_on=d['settled_on'], notice_days=d['notice_days'])) for d in deposit_rows()]


def cash_d():
    out = []
    for c in cash_rows():
        d = dict(cash_id=c['cash_id'], month=c['month'], opening=c['opening'], parent_payments=c['parent_payments'], government_payments=c['government_payments'], pay_out=c['pay_out'],
                 expenses_out=c['expenses_out'], tax_set_aside=c['tax_set_aside'], deposit_refunds=c['deposit_refunds'], owner_extra=int(c['owner_extra']))
        out.append(nz(d, 'tax_set_aside', 'deposit_refunds', 'owner_extra'))
    return out


def bills_d():
    out = []
    for b in bill_rows():
        d = dict(bill_id=b['bill_id'], due_date=b['due_date'], category=key('billcat', b['category']), paid_to=b['paid_to'], amount=b['amount'], status=key('done2', b['status']))
        if b['paid_to'] == 'Rajesh Menon': d['phone'] = SUP_PHONE
        elif b['paid_to'] == 'Eleni Papadakis': d['phone'] = ACC_PHONE
        out.append(d)
    return out


def expenses_d():
    out = []
    mm = {'Card': 'Autopay card', 'Direct debit': 'Autopay bank', 'Bank transfer': 'Bank transfer'}
    for e in expense_rows()[-300:]:
        d = dict(expense_id=e['expense_id'], date=e['date'], category=key('expcat', e['category']), description=e['description'], amount=e['amount'], paid_to=e['paid_to'], method=key('method', mm[e['method']]))
        if e['paid_to'] == 'Dae-ho Park': d['phone'] = MAINT_PHONE
        out.append(d)
    return out


def payroll_d():
    return [dict(pay_id=p['pay_id'], month=p['month'], person=p['person'], role=key('payrole', p['role']), pay_type=key('paytype', p['pay_type']), hours=p['hours'] or None, total=p['total'],
                 pay_date=p['pay_date'], status=key('paystat', p['status'])) for p in pay_rows()[-160:] ] if False else \
           [nb(dict(pay_id=p['pay_id'], month=p['month'], person=p['person'], role=key('payrole', p['role']), pay_type=key('paytype', p['pay_type']), hours=p['hours'] or None, total=p['total'],
                    pay_date=p['pay_date'], status=key('paystat', p['status']))) for p in pay_rows()[-160:]]


def collect_d(): return [dict(col_id='CO-%02d' % i, month=iso(month_start(11 - i + 1))) for i in range(1, 13)]


def tax_d():
    return [nb(dict(tax_id=t['tax_id'], month=t['month'], revenue=t['revenue'], costs=t['costs'], set_aside_pct=t['set_aside_pct'], set_aside=t['set_aside'], due_date=t['due_date'],
                    paid_on=t['paid_on'], status=key('done2', t['status']))) for t in tax_rows()]


def forecast_d(): return [dict(fc_id='FC-%02d' % i) for i in range(1, 14)]
def overdue_d(): return [dict(of_id='OF-%02d' % i) for i in range(1, 16)]
def reminder_d(): return [dict(rs_id='RS-%02d' % i) for i in range(1, 21)]


def front(rows, pred):
    """move the story rows to the top of a demo list (the first row is the record forms and documents open on)"""
    a = [r for r in rows if pred(r)]; b = [r for r in rows if not pred(r)]
    return a + b
