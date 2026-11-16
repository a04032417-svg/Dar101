"""HVAC suite part 7: demo rows from hv_core (full generator output for the monthly aggregates, recent samples for the long registers)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hv7_lists import *
import collections

TD = TODAY
ST = story()
SITES = site_rows(); SITE = {s['site_id']: s for s in SITES}
INV = invoice_rows(); PAY = payment_rows(); JOBS = job_rows(); CHASE = chase_rows(); PUR = purchase_rows()
INVD = {i['invoice_id']: i for i in INV}
PH = {t['name']: t['phone'] for t in team}
ROLEPH = {t['role']: t['phone'] for t in team}
ASSIGN_PH = {t['assignment']: t['phone'] for t in team}
OWNER_PHONE = PH[OWNER]; OFFICE_PHONE = PH[OFFICE_MANAGER]
SUP_PHONE = ROLEPH['Equipment supplier']; PARTS_PHONE = ROLEPH['Parts counter']; ACCT_PHONE = ROLEPH['Accountant']
ELEC_PHONE = ASSIGN_PH['Electrical work']; SHEET_PHONE = ASSIGN_PH['Sheet-metal work']
TECH_PHONES = [PH[n] for n in TECH_NAMES]
APPRENTICE, APPRENTICE_PHONE = TECH_NAMES[6], PH[TECH_NAMES[6]]
SUPPLIER_PHONE = {'Your equipment supplier': SUP_PHONE, 'Your parts counter': PARTS_PHONE, 'Electrical subcontractor': ELEC_PHONE, 'Sheet-metal subcontractor': SHEET_PHONE}
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def mk(m): return iso(m)

WIN_DAYS = 110
OPEN_ST = ('Unpaid', 'Part paid')
CH_BY_INV = collections.defaultdict(list)
for c in CHASE: CH_BY_INV[c['invoice_id']].append(c)

# ---------- invoices: the last 110 days, every unpaid, part paid and written-off invoice, and every financed invoice
def _inv_sel():
    sel = [i for i in INV if i['date'] >= ago(WIN_DAYS) or i['status'] != 'Paid' or i['financing']]
    return sel
INV_SEL = _inv_sel(); INV_SEL_IDS = {i['invoice_id'] for i in INV_SEL}
def invoices_d():
    out = []
    for i in INV_SEL:
        s = SITE[i['site_id']]
        r = dict(invoice_id=i['invoice_id'], job_id=i['job_id'], date=i['date'], month=i['month'], due_date=i['due_date'], site_id=i['site_id'], site_ref=s['site_ref'], account=i['account'], phone=s['phone'],
                 site_type=key('sitetype', i['site_type']), job_type=key('jobtype', i['job_type']), technician=key('tech', i['technician']), amount=i['amount'], deposit_asked=i['deposit_asked'], deposit_paid=i['deposit_paid'],
                 financing=i['financing'], method=key('paymethod', i['method']) if i['method'] else '', paid_amount=i['paid_amount'], paid_on=i['paid_on'], balance=round(i['balance']), terms_days=i['terms_days'], status=key('invstatus', i['status']))
        out.append(nb(r) if False else {k: v for k, v in r.items() if v is not None and not (v == '' and k in ('method', 'paid_on'))})
    k = next(n for n, i in enumerate(INV_SEL) if i['status'] == 'Part paid' and i['deposit_paid'] > 0 and CH_BY_INV.get(i['invoice_id']) and i['date'] >= ago(90) and i['due_date'] < iso(TD))
    out.insert(0, out.pop(k))
    return out

def payments_d():
    sel = [p for p in PAY if p['date'] >= ago(75)]
    out = []
    for p in sel:
        r = dict(payment_id=p['payment_id'], date=p['date'], month=p['month'], invoice_id=p['invoice_id'], job_id=p['job_id'], account=p['account'], site_id=p['site_id'], amount=p['amount'], method=key('paymethod', p['method']), kind=key('paykind', p['kind']))
        out.append({k: v for k, v in r.items() if v != ''})
    k = next(n for n, p in enumerate(sel) if p['kind'] == 'Invoice' and p['invoice_id'] in INV_SEL_IDS and (to_date(p['date']) - to_date(INVD[p['invoice_id']]['date'])).days >= 3 and p['amount'] >= 200)
    out.insert(0, out.pop(k))
    return out

# ---------- completed jobs and whether they were invoiced
def _covered(j): return j['price'] == 0 or j['kind'] == 'Tune-up' or j['job_type'] == 'Agreement visit' or j['warranty'] or j['is_callback']
def unbilled_d():
    sel = [j for j in JOBS if j['status'] == 'Completed' and (j['date'] >= ago(21) or (not j['invoice_id'] and not _covered(j) and j['date'] >= ago(120)))]
    out = []
    for j in sel:
        s = SITE[j['site_id']]
        out.append({k: v for k, v in dict(job_id=j['job_id'], date=j['date'], site_id=j['site_id'], site_ref=s['site_ref'], phone=s['phone'], job_type=key('jobtype', j['job_type']), technician=key('tech', j['technician']),
                    price=j['price'], invoice_id=j['invoice_id'], covered=_covered(j)).items() if v != ''})
    k = next(n for n, j in enumerate(sel) if not j['invoice_id'] and not _covered(j) and (TD - to_date(j['date'])).days >= 5 and j['price'] >= 300)
    out.insert(0, out.pop(k))
    return out
UNB_WAIT = [j for j in JOBS if j['status'] == 'Completed' and not j['invoice_id'] and not _covered(j) and j['date'] >= ago(120)]

# ---------- accounts and ageing
def _acct_rows():
    ag = {a['account']: a for a in ageing_rows()}
    by = collections.defaultdict(list)
    for s in SITES:
        if s['account'].startswith('LA-'): by[s['account']].append(s)
    out = []
    for a in sorted(by):
        ss = by[a]
        st = ag[a]['site_type'] if a in ag else collections.Counter(s['site_type'] for s in ss).most_common(1)[0][0]
        out.append(dict(account=a, site_type=st, terms_days=TERMS_LANDLORD, phone=ss[0]['phone']))
    return out
def accounts_d(): return _acct_rows()
def ageing_d(): return [dict(account=a['account']) for a in sorted(_acct_rows(), key=lambda r: r['account'] != ST['overdue_account'])]

# ---------- chase log (all of it) with the story invoice first
def chase_d():
    out = [{k: v for k, v in dict(chase_id=c['chase_id'], date=c['date'], invoice_id=c['invoice_id'], account=c['account'], method=key('chasemethod', c['method']), promised_on=c['promised_on'],
                                  promised_amount=c['promised_amount'], outcome=key('chaseoutcome', c['outcome'])).items() if v != ''} for c in CHASE]
    first = INV_SEL and next(i for i in INV_SEL if i['status'] == 'Part paid' and i['deposit_paid'] > 0 and CH_BY_INV.get(i['invoice_id']) and i['date'] >= ago(90) and i['due_date'] < iso(TD))['invoice_id']
    k = next(n for n, c in enumerate(CHASE) if c['invoice_id'] == first)
    out.insert(0, out.pop(k))
    return out

# ---------- monthly aggregates from the full generator output
def deposits_d():
    out = []
    for m in months14():
        ms = iso(m); iv = [i for i in INV if i['month'] == ms]; pays = [p for p in PAY if p['month'] == ms]
        paid = [i for i in iv if i['status'] == 'Paid' and i['paid_on']]
        days = [(to_date(i['paid_on']) - to_date(i['date'])).days for i in paid]
        late = [1 for i in paid if i['paid_on'] > i['due_date']]
        out.append(dict(month=ms, invoices=len(iv), invoiced=round(sum(i['amount'] for i in iv)), collected_invoices=round(sum(p['amount'] for p in pays if p['kind'] == 'Invoice')),
                        collected_deposits=round(sum(p['amount'] for p in pays if p['kind'] == 'Deposit')), collected_fees=round(sum(p['amount'] for p in pays if p['kind'] == 'Agreement fee')),
                        deposits_asked=round(sum(i['deposit_asked'] for i in iv)), deposits_paid=round(sum(i['deposit_paid'] for i in iv)),
                        avg_days=round(sum(days) / len(days), 1) if days else 0, late_share=round(len(late) / len(paid), 3) if paid else 0))
    return out

def financing_d():
    out = []
    for m in months14():
        ms = iso(m); iv = [i for i in INV if i['month'] == ms]; f = [i for i in iv if i['financing']]
        out.append(dict(month=ms, invoiced_jobs=len(iv), financed_jobs=len(f), financed_amount=round(sum(i['amount'] for i in f)), other_amount=round(sum(i['amount'] for i in iv if not i['financing']))))
    return out

def pnl_d():
    return [dict(month=r['month'], season=key('season', r['season']), jobs=r['jobs'], revenue=round(r['revenue']), materials=round(r['materials']), subcontract=round(r['subcontract']), permits_disposal=round(r['permits_disposal']),
                 technician_pay=round(r['technician_pay']), vehicles=round(r['vehicles']), overhead=round(r['overhead'])) for r in pnl_rows()]

def cash_d():
    return [dict(month=r['month'], cash_in=round(r['cash_in']), payroll=round(r['payroll']), owner_draw=round(r['owner_draw']), purchases=round(r['purchases']), overhead=round(r['overhead']), tax_paid=round(r['tax_paid']),
                 owner_bonus=round(r['owner_bonus']), closing_cash=round(r['closing_cash'])) for r in cash_rows()]

def tax_d(): return [dict(month=r['month'], set_aside_pct=r['set_aside_pct']) for r in tax_rows()]

BILLS = bill_rows()
def bills_d():
    out = [dict(bill_id=b['bill_id'], due_date=b['due_date'], payee=b['payee'], category=key('billcat', b['category']), amount=round(b['amount'], 2), kind=key('billkind', b['kind']), paid=False) for b in BILLS]
    k = next(n for n, b in enumerate(BILLS) if b['amount'] == ST['supplier_po_amount'])
    out.insert(0, out.pop(k))
    return out
STORY_BILL = next(b['bill_id'] for b in BILLS if b['amount'] == ST['supplier_po_amount'])

def purchases_d():
    sel = PUR[-330:]
    out = [{k: v for k, v in dict(po_id=p['po_id'], date=p['date'], month=p['month'], supplier=key('supplier', p['supplier']), kind=key('pokind', p['kind']), job_id=p['job_id'], amount=round(p['amount'], 2), due_date=p['due_date'],
                                  paid_on=p['paid_on'], status=key('postatus', p['status'])).items() if v != ''} for p in sel]
    k = next((n for n, p in enumerate(sel) if p['kind'] == 'Subcontract' and p['status'] == 'Open' and p['job_id']), None)
    if k is None: k = max(n for n, p in enumerate(sel) if p['kind'] == 'Subcontract' and p['job_id'])
    out.insert(0, out.pop(k))
    return out

def expenses_d():
    return [dict(expense_id=e['expense_id'], date=e['date'], month=e['month'], category=key('expcat', e['category']), description=e['description'], amount=round(e['amount'], 2), paid_to=e['paid_to'], method=e['method']) for e in expense_rows()]
def cost_cats_d(): return [dict(category=c['category'], grp=c['grp'], monthly_budget=c['monthly_budget']) for c in cost_categories]
def seasons_d(): return [dict(month_no=s['month_no'], month_name=s['month_name'], season=key('season', s['season']), demand_index=s['demand_index']) for s in seasons]
def forecast_d(): return [dict(month=iso(add_months(month_start(0), k))) for k in range(12)]
def draw_d(): return [dict(option=key('drawopt', o)) for o in DRAW_OPTIONS]
def dtp_job_d(): return [dict(job_type=key('jobtype', j)) for j in JOB_TYPES]
def dtp_tech_d(): return [dict(technician=key('tech', t)) for t in TECH6]

# ---------- defaults for the tools (editable inputs, taken from the same history)
def _defaults():
    pn = pnl_rows(); closed = [r for r in pn if r['month'] < iso(month_start(0))][-12:]; last6 = closed[-6:]
    rev = sum(r['revenue'] for r in closed); gross = sum(r['revenue'] - r['materials'] - r['subcontract'] - r['permits_disposal'] - r['technician_pay'] for r in closed)
    fixed = sum(r['overhead'] + r['vehicles'] for r in last6) / 6
    jobs = sum(r['jobs'] for r in closed)
    return dict(margin=round(gross / rev, 2), fixed=round(fixed, -2), ticket=round(rev / jobs, -1), equip_share=0.40, account=ST['overdue_account'], bill=STORY_BILL)
DEF = _defaults()

if __name__ == '__main__':
    print(len(invoices_d()), len(payments_d()), len(unbilled_d()), len(UNB_WAIT), len(chase_d()), len(purchases_d()), len(bills_d()), len(expenses_d()))
    print(invoices_d()[0]); print(payments_d()[0]); print(unbilled_d()[0]); print(chase_d()[0]); print(bills_d()[0]); print(purchases_d()[0])
    print(accounts_d()[:3], DEF); print(deposits_d()[-2:]); print(financing_d()[-3:])
    print(collections.Counter(r.get('method') for r in invoices_d()), collections.Counter(r['status'] for r in invoices_d()))
