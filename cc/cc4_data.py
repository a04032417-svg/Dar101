"""Childcare center suite part 4: demo rows from cc_core (full generator output where small, thinned where large, aggregated tables built from the full output)."""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cc4_lists import *
import datetime as _dt

dd = to_date
ST = story()
T0 = TODAY
Y0 = iso(D(T0.year, 1, 1))
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def d_add(s, n): return iso(dd(s) + _dt.timedelta(days=n))

TEAM = {t['name']: t for t in team}
OWNER_PHONE = TEAM[OWNER]['phone']; DIRECTOR_PHONE = TEAM[ASSISTANT_DIRECTOR]['phone']
ACCOUNTANT_PHONE = [t for t in team if t['role'] == 'Accountant'][0]['phone']
RATE_KEY = {(r['room'], r['schedule']): r for r in rates}

FAM = family_rows(); FAMD = {f['family_id']: f for f in FAM}; FAMN = {f['family']: f for f in FAM}
CHF = [dict(c) for c in child_rows()]
# demo story touch: two enrolled children have given notice and leave in the next weeks (their deposits are due back)
_enr = [c for c in CHF if c['status'] == 'Enrolled' and c['child'] != ST['health_child'] and c['family'] != ST['overdue_family']]
LEAVERS = [_enr[4], _enr[13]]
for c_, e_, n_ in zip(LEAVERS, (14, 21), (16, 9)):
    c_['end_date'] = ahead(e_); c_['notice_on'] = ago(n_)
CHD = {c['child']: c for c in CHF}
INVF = invoice_rows(); INV = [i for i in INVF if i['issued_on'] >= Y0]
LFF = late_fee_rows(); LF = late_fee_rows(n=300)
DPF = deposit_rows(); STF = statement_rows(); CLF = closure_rows()
DROP = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cc4_dropin.json')))
CHROOM = {c['child_id']: c['room'] for c in CHF}


def rates_d():
    return [dict(rate_id=r['rate_id'], room=key('room', r['room']), schedule=key('schedule', r['schedule']), weekly_rate=r['weekly_rate'], last_year_rate=r['last_year_rate'], days=r['days'],
                 hours_day=r['hours_day'], day_rate=r['day_rate']) for r in rates]


def fees_d(): return [dict(fee=f['fee'], amount=f['amount'], rule=f['rule']) for f in fees]


def families_d():
    return [dict(family_id=f['family_id'], family=f['family'], guardian=f['guardian'], phone=f['phone'], email=f['email'], cycle=key('cycle', f['cycle']), pay_method=key('method', f['pay_method']),
                 autopay=f['autopay'], gov_share=f['gov_share'], late_prone=f['late_prone'], staff_family=f['staff_family'], children=f['children'], first_start=f['first_start']) for f in FAM]


def children_d():
    out = []
    for c in CHF:
        out.append(nb(dict(child_id=c['child_id'], child=c['child'], family=c['family'], family_id=c['family_id'], room=key('room', c['room']), schedule=key('schedule', c['schedule']), days=len(c['days'].split()),
                           start_date=c['start_date'], end_date=c['end_date'], status=key('cstatus', c['status']), discount=key('discount', c['discount']), discount_pct=c['discount_pct'], guardian=c['guardian'], phone=c['phone'])))
    return out


def invoices_d():
    return [nb(dict(invoice_id=i['invoice_id'], family=i['family'], cycle=key('cycle', i['cycle']), month=i['month'], period_start=i['period_start'], period_end=i['period_end'], issued_on=i['issued_on'],
                    due_date=i['due_date'], children=i['children'], tuition=i['tuition'], discount=i['discount'], registration=i['registration'], supply_fee=i['supply_fee'], camp_fee=i['camp_fee'],
                    drop_in=i['drop_in'], late_fees=i['late_fees'], gov_expected=i['gov_expected'], paid_amount=i['paid_amount'], paid_on=i['paid_on'], status=key('istatus', i['status']))) for i in INV]


def late_fees_d():
    return [nb(dict(fee_id=x['fee_id'], date=x['date'], month=x['month'], child=x['child'], family=FAMD[x['family_id']]['family'], room=key('room', CHROOM[x['child_id']]), late_minutes=x['late_minutes'],
                    waived=x['waived'], invoice_id=x['invoice_id'])) for x in LF]


def deposits_d():
    out = []
    for x in DPF:
        c = CHD[x['child']]
        out.append(nb(dict(deposit_id=x['deposit_id'], child=x['child'], amount=x['amount'], received_on=x['received_on'], status=key('depstatus', x['status']), settled_on=x['settled_on'],
                           notice_days=(30 if c in LEAVERS else x['notice_days']))))
    return out


# ---- invoice check: expected tuition = rates of the children enrolled for the whole period x weeks billed (the same rule as the sheet formula)
def _wr(c): return RATE_KEY[(c['room'], c['schedule'])]['weekly_rate']
def expected_tuition(i):
    ps, pe = i['period_start'], i['period_end']
    kids = [c for c in CHF if c['family'] == i['family']]
    s1 = sum(_wr(c) for c in kids if c['start_date'] <= ps)
    s2 = sum(_wr(c) for c in kids if c['start_date'] <= ps and c['end_date'] and c['end_date'] < pe)
    return (s1 - s2) * (1 if i['cycle'] == 'Weekly' else 52.0 / 12.0)


def inv_check_d():
    cand = [i for i in INV if i['issued_on'] >= ago(150) and i['tuition'] > 0]
    ok = [i for i in cand if abs(expected_tuition(i) - i['tuition']) <= 1.0]
    bad = [i for i in cand if abs(expected_tuition(i) - i['tuition']) > 1.0]
    pick = ok[::max(1, len(ok) // 52)][:52] + bad[::max(1, len(bad) // 8)][:8]
    pick.sort(key=lambda i: i['invoice_id'])
    return [dict(invoice_id=i['invoice_id']) for i in pick]


def statements_d():
    out = []; k = 0
    for x in STF:
        led = x['parent_paid']
        if x['year'] == T0.year:
            k += 1
            if k in (7, 19, 41): led = R2(led + {7: -120.0, 19: 45.0, 41: -366.0}[k])
        out.append(nb(dict(statement_id=x['statement_id'], family=x['family'], year=key('syear', str(x['year'])), parent_paid=x['parent_paid'], government_paid=x['government_paid'], payments=x['payments'],
                           ledger_paid=led, sent_on=x['sent_on'])))
    return out


def discounted_d():
    by = {}
    for c in CHF: by.setdefault(c['family'], []).append(c)
    rows = [c for c in CHF if c['discount'] != 'None']
    flagged = {c['family'] for c in rows}
    for f, ks in by.items():
        if f in flagged: rows += [k for k in ks if k['discount'] == 'None']
    for f, ks in by.items():
        if len(ks) >= 2 and f not in flagged: rows += ks
    seen = set(); out = []
    for c in rows:
        if c['child'] in seen: continue
        seen.add(c['child']); out.append(dict(child=c['child'], from_date=c['start_date']))
    return out[:24]


RISE = [(0.02, 0), (0.03, 0), (0.04, 1), (0.05, 1), (0.06, 1), (0.07, 2), (0.08, 2), (0.09, 3), (0.10, 4), (0.03, 2), (0.05, 0), (0.07, 3)]
def fee_rise_d(): return [dict(rise_pct=r, leavers=n, announce_on=ahead(10)) for r, n in RISE]


def drop_in_d():
    out = []
    for i, x in enumerate(DROP, 1):
        r = RATE_KEY[(x['room'], x['schedule'])]['day_rate']
        r = r if x['date'] >= Y0 else R2(r / 1.03)
        out.append(dict(drop_id='DI-%03d' % i, date=x['date'], child=x['child'], family=FAMD[x['family_id']]['family'], room=key('room', x['room']), hours=round(x['hours'], 1), day_rate=r))
    return out


def discount_rules_d():
    return [dict(rule='Sibling discount', share=SIBLING_PCT), dict(rule='Staff discount', share=STAFF_PCT), dict(rule='Late pickup waiver', share=0.33), dict(rule='Registration fee waiver', share=0.15), dict(rule='Drop-in surcharge waiver', share=0.10)]


def repeat_late_d():
    cnt = {}
    for x in LF:
        if x['date'] >= ago(180): cnt[x['family_id']] = cnt.get(x['family_id'], 0) + 1
    top = sorted(cnt.items(), key=lambda kv: -kv[1])[:16]
    return [dict(family=FAMD[f]['family']) for f, _ in top]


_KIDS_ENR = {}
for c in CHF:
    if c['status'] != 'Left': _KIDS_ENR.setdefault(c['family_id'], []).append(c)
def weekly_run_d(): return [dict(family=f['family']) for f in FAM if f['cycle'] == 'Weekly' and f['family_id'] in _KIDS_ENR]
def monthly_run_d(): return [dict(family=f['family']) for f in FAM if f['cycle'] == 'Monthly' and f['family_id'] in _KIDS_ENR]


def starters_d():
    out = []
    inv_by = {}
    for i in INVF: inv_by.setdefault(i['family'], []).append(i)
    dep = {x['child']: x['amount'] for x in DPF}
    lo = ago(365)
    for c in CHF:
        if c['start_date'] < lo: continue
        reg = 0.0
        for i in inv_by.get(c['family'], []):
            if i['registration'] > 0 and i['period_start'] <= c['start_date'] <= i['period_end']: reg = REG_FEE if c['start_date'] >= Y0 else REG_FEE - 20; break
        sup = 0.0
        for y in (T0.year - 1, T0.year):
            sd = dd(iso(D(y, 9, 1)))
            while sd.weekday() > 4: sd += _dt.timedelta(days=1)
            if dd(c['start_date']) <= sd and (not c['end_date'] or dd(c['end_date']) >= sd) and iso(sd) >= lo and sd <= T0:
                sup = SUPPLY_FEE if y == T0.year else SUPPLY_FEE - 10
        out.append(nb(dict(child=c['child'], start_date=c['start_date'], registration=reg, supply_fee=sup, deposit=dep.get(c['child'], 0.0))))
    return out


def _month_totals():
    tot = {}
    for i in INVF:
        m = i['month']; t = tot.setdefault(m, dict(n=0, amount=0.0, ex=0.0, d=0.0, t=0.0, gov=0.0, paid=0.0))
        t['n'] += 1; t['amount'] += i['amount']; t['ex'] += i['registration'] + i['supply_fee'] + i['camp_fee'] + i['drop_in'] + i['late_fees']
        t['d'] += i['discount']; t['t'] += i['tuition']; t['gov'] += i['gov_expected']; t['paid'] += i['paid_amount']
    return tot


def rev_room_d():
    tot = _month_totals(); rm = {(x['month'], x['room']): x['revenue'] for x in room_month_rows()}; out = []
    for k in range(11, -1, -1):
        m = iso(month_start(k)); t = tot[m]
        for r in ROOMS:
            R = rm.get((m, r), 0.0)
            ex = R * t['ex'] / t['amount']; tu = (R - ex) * t['t'] / (t['t'] - t['d']); out.append(dict(room=key('room', r), month=m, tuition=R2(tu), discounts=R2(tu - (R - ex)), extras=R2(ex)))
    return out


def invoice_status_d():
    tot = _month_totals(); out = []
    for k in range(23, -1, -1):
        m = iso(month_start(k)); t = tot.get(m)
        if not t: continue
        out.append(dict(month=m, invoices=t['n'], billed=R2(t['amount']), discounts=R2(t['d']), government=R2(t['gov']), paid=R2(t['paid'])))
    return out


def closures_d(): return [dict(closure_id=x['closure_id'], date=x['date'], weekday=key('wday', x['weekday']), reason=key('creason', x['reason'])) for x in CLF]
