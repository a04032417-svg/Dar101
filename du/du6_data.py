"""Doula business suite part 6: demo rows from du_core (row-level tables carry the full generator output; calculated tables only list their key inputs)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from du6_lists import *
import datetime as _dt

R = rng('du6')
ST = story()
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def I(x): return iso(x) if hasattr(x, 'isoformat') else x
T0 = TODAY; MS0 = month_start(0)
TEAMD = {t['name']: t for t in team}
OWNER_PHONE = TEAMD[OWNER]['phone']; ADMIN_PHONE = TEAMD[ADMIN]['phone']
ACCOUNTANT_PHONE = [t for t in team if t['role'] == 'Accountant'][0]['phone']
DOUD = {d['doula']: d for d in doulas}
CLF = client_rows(); CLD = {c['client_id']: c for c in CLF}
PYF = pay_rows(); VSF = visit_rows(); BTF = birth_rows(); ONF = oncall_rows(); RTF = rota_rows(); OTF = owner_time_rows()
def front(rows, pred):
    for i, r in enumerate(rows):
        if pred(r): return [rows[i]] + rows[:i] + rows[i + 1:]
    return rows

DIFFS = [p for p in PYF if p['status'] == 'Paid' and abs(p['paid_amount'] - p['pay_due']) > 0.005]
DEF_DIFF = DIFFS[-1]
LASTM = month_start(1)
CALLOUT = [p for p in PYF if p['basis'] == 'Backup call-out'][-1]


def pay_d():
    out = [nb(dict(pay_id=p['pay_id'], month=I(p['month']), doula=key('payee', p['doula']), client_id=p['client_id'], client=p['client'], basis=key('basis', p['basis']), hours=p['hours'], miles=p['miles'],
                   gross=p['gross'], agency_share=p['agency_share'], pay_due=p['pay_due'], paid_amount=p['paid_amount'], paid_on=I(p['paid_on']), status=key('paystatus', p['status']))) for p in PYF]
    return front(out, lambda r: r['pay_id'] == CALLOUT['pay_id'])
def doulas_d(): return [dict(doula=key('doula', d['doula']), agency_share=d['agency_share'], hourly_pay=d['hourly_pay']) for d in doulas]
def clients_d():
    out = [nb(dict(client_id=c['client_id'], client=c['client'], phone=c['phone'], kind=key('ckind', c['kind']), package=c['package'], doula=key('doula', c['doula']), backup=(key('backup', c['backup']) if c['backup'] else ''),
                   status=key('cstatus', c['status']), signed_on=I(c['signed_on']), edd=I(c['edd']))) for c in CLF]
    return front(out, lambda r: r.get('status') == key('cstatus', 'Booked') and r.get('doula') == key('doula', 'Lucia Ferreira'))
def packages_d(): return [dict(package=p['package'], kind=key('pkind', p['kind']), price=p['price'], birth_value=p['birth_value'], pp_value=p['pp_value'], birth_hours=p['birth_hours'], postpartum_hours=p['postpartum_hours'], plan_hours=p['plan_hours']) for p in packages]
def visits_d(): return [dict(visit_id=v['visit_id'], date=I(v['date']), client=v['client'], doula=key('doula', v['doula']), kind=key('vkind', v['kind']), hours=v['hours'], miles=v['miles'], area=key('area', v['area'])) for v in VSF]
def births_d(): return [dict(birth_id=b['birth_id'], date=I(b['date']), client=b['client'], doula=key('attender', b['doula']), assigned=key('doula', b['assigned']), backup_used=bool(b['backup_used']), hours=b['hours'], miles=b['miles'], area=key('area', b['area'])) for b in BTF]
def oncall_d(): return [nb(dict(window_id=o['window_id'], client=o['client'], doula=key('doula', o['doula']), backup=(key('backup', o['backup']) if o['backup'] else ''), oncall_start=I(o['oncall_start']), oncall_end=I(o['oncall_end']), contact_hours=o['contact_hours'])) for o in ONF]
def rota_d(): return [dict(rota_id=r['rota_id'], week=I(r['week']), backup=key('backup', r['backup']), stipend=int(r['stipend'])) for r in RTF]
def owner_time_d(): return [dict(log_id=o['log_id'], week=I(o['week']), own_client_hours=o['own_client_hours'], management_hours=o['management_hours'], admin_hours=o['admin_hours']) for o in OTF]


def team_d():
    out = []
    for i, t in enumerate(team):
        d = DOUD.get(t['name'])
        r = dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), pay_type=key('paytype', t['pay_type']), phone=t['phone'], email=t['email'], hours_week=t['hours_week'], start=t['start'],
                 hourly_rate=(d['hourly_pay'] if d else {'Amara Okonkwo': 30, 'Rosa Delgado': 65, 'Kofi Mensah': 40, 'Ingrid Sorensen': 90, 'Aiko Tanaka': 45}.get(t['name'], t['hourly_rate'])))
        if t['service']: r['service'] = key('service', t['service'])
        if d: r.update(cap_births=d['cap_births'], weekly_hours_cap=d['weekly_hours_cap'], review_on=ahead(6 + 9 * (i % 6)))
        out.append(nb(r))
    return front(out, lambda r: r['name'] == 'Priya Raman')


_LINES = [p for p in PYF if p['basis'] in ('Per client', 'Per hour')]
def margin_d(): return [dict(client_id=c) for c in sorted({p['client_id'] for p in _LINES})]
def margin_doula_d(): return [dict(doula=key('cdoula', d)) for d in CONTRACTED]


def payrun_d():
    out = []; n = 0
    for m in [month_start(k) for k in range(11, -1, -1)]:
        for d in PAYEES:
            if not any(p['month'] == m and p['doula'] == d for p in PYF): continue
            n += 1; r = dict(run_id='PR-%03d' % n, month=I(m), doula=key('payee', d))
            if m < MS0:
                eom = add_months(m, 1) - _dt.timedelta(days=1)
                late = rng('late%d' % n).random() < 0.18
                r['sent_on'] = I(eom + _dt.timedelta(days=(rng('lt%d' % n).randrange(7, 12) if late else rng('ot%d' % n).randrange(1, 5))))
            out.append(r)
    return front(out, lambda r: r['month'] == I(LASTM) and r['doula'] == key('payee', 'Mei-Ling Chen'))


def diffs_d():
    due = [p for p in PYF if p['status'] == 'Due' and p['basis'] in ('Per client', 'Per hour')][:5]
    rows = list(reversed(DIFFS)) + due
    return [dict(pay_id=p['pay_id']) for p in rows]


def cap_d():
    out = []; n = 0
    for k in range(-3, 9):
        m = add_months(MS0, k)
        for d in DOULA_NAMES:
            n += 1; out.append(dict(cap_id='CP-%03d' % n, doula=key('doula', d), month=I(m)))
    return front(out, lambda r: r['doula'] == key('doula', ST['overlap_doula']) and r['month'] == ST['overlap_month'])


def hrs_d(): return [dict(doula=key('doula', d), month=I(month_start(k))) for k in range(11, -1, -1) for d in DOULA_NAMES]
def profit_d(): return [dict(doula=key('cdoula', d), month=I(month_start(k))) for k in range(13, -1, -1) for d in CONTRACTED]
def owner_load_d(): return front([dict(month=I(month_start(k))) for k in range(23, -1, -1)], lambda r: r['month'] == I(LASTM))
def backup_month_d(): return front([dict(month=I(month_start(k))) for k in range(23, -1, -1)], lambda r: r['month'] == I(CALLOUT['month']))


def splits_d():
    plan = [('Lucia Ferreira', [0.25, 0.22, 0.30], 15, 1950), ('Priya Raman', [0.20, 0.28, 0.15], 13, 1880), ('Mei-Ling Chen', [0.24, 0.30, 0.27], 14, 2040), ('Sven Lindqvist', [0.26, 0.33, 0.30], 16, 1760)]
    out = []; n = 0
    for d, shares, cy, avg in plan:
        for j, sh in enumerate(shares):
            n += 1; out.append(dict(split_id='SP-%02d' % n, doula=key('cdoula', d), new_share=sh, clients_year=cy + j - 1, avg_package=avg + 40 * j, proposed_on=ago(4 + 6 * n)))
    return front(out, lambda r: r['doula'] == key('cdoula', 'Priya Raman'))


# defaults for tools (derived from the data so that the tools open on a meaningful case)
_ot = OTF[-5:-1]
DEF_OWN = round(sum(o['own_client_hours'] for o in _ot) / 4); DEF_MGMT = round(sum(o['management_hours'] for o in _ot) / 4); DEF_ADMIN = round(sum(o['admin_hours'] for o in _ot) / 4)
MILDIFF = [p for p in DIFFS if p['basis'] == 'Mileage'][-1]
