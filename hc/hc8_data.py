"""Home care agency suite part 8: demo rows (full data for monthly tables, the same story as every other part)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hc8_lists import *
import collections, datetime as dt

R = rng('hc8')
D = dt.date
def d_(s): return D.fromisoformat(s)
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def yn(b): return 'yes' if b else 'no'
def r2(x): return round(x + 1e-9, 2)

PNL = pnl_rows(); EXP = expense_rows(); CASH = cash_rows(); TAX = tax_rows(); WK = week_rows(); SM = service_month_rows(); MK = marketing_rows(); PAY = payroll_rows()
INV = invoice_rows(); CLM = claim_rows(); CGR = caregiver_rows()
MONTHS = [r['month'] for r in PNL]
M0 = D(TODAY.year, TODAY.month, 1).isoformat()
M1 = month_start(1).isoformat()
BURDEN = PAYROLL_BURDEN

# ---------- profit and loss
def pnl_d():
    return [dict(row_id=r['row_id'], month=r['month'], revenue=r['revenue'], billed_hours=r['billed_hours'], caregiver_pay=r['caregiver_pay'], overtime_pay=r['overtime_pay'],
                 travel_mileage=r2(r['travel_pay'] + r['mileage_pay']), payroll_burden=r['payroll_burden']) for r in PNL]

# ---------- expenses
def expenses_d():
    return [dict(expense_id=e['expense_id'], date=e['date'], month=e['month'], category=key('ecat', e['category']), payee=e['vendor'], amount=e['amount']) for e in EXP]

def overhead_d(): return [dict(row_id='OV-%02d' % (i + 1), month=m) for i, m in enumerate(MONTHS)]

# ---------- budget: the average of the last six full months by category with a plan factor
def _cat_month():
    a = collections.defaultdict(float)
    for e in EXP: a[(e['month'], e['category'])] += e['amount']
    return a
CATM = _cat_month()
OVH_M = collections.defaultdict(float)
for e in EXP: OVH_M[e['month']] += e['amount']
def budget_d():
    last6 = [month_start(k).isoformat() for k in range(1, 7)]
    out = []
    for i, cat in enumerate(EXPENSE_CATEGORIES):
        vals = [CATM.get((m, cat), 0) for m in last6]
        avg = sum(vals) / 6
        f = [1.0, 1.02, 0.97, 1.05, 1.0, 0.95, 1.08, 1.0, 1.04, 0.9, 1.0, 1.03, 0.92, 1.06][i]
        out.append(dict(category=key('ecat', cat), budget=max(50, round(avg * f / 10) * 10), review_on=ahead(20 + i * 24)))
    return out
BUD = {b['category']: b for b in budget_d()}

# ---------- owner draws and tax
DRAW0 = [4000, 4000, 4500, 4500, 5000, 5000, 5500, 6000, 6500, 7000]
def draws_d():
    out = []
    for i, m in enumerate(MONTHS):
        amt = DRAW0[i] if i < len(DRAW0) else int(OWNER_DRAW)
        out.append(dict(draw_id='DR-%02d' % (i + 1), month=m, draw=amt, taken_on=(d_(m) + dt.timedelta(days=4)).isoformat()))
    return out
DRAWS = {d['month']: d['draw'] for d in draws_d()}
def tax_d():
    return [nb(dict(tax_id=t['tax_id'], month=t['month'], set_aside_pct=t['set_aside_pct'], status=key('taxst', t['status']), moved_on=t['moved_on'])) for t in TAX]
PROFIT = {r['month']: r['profit'] for r in PNL}
SETASIDE = {t['month']: round(max(0, PROFIT[t['month']] * t['set_aside_pct']) + 1e-9, 2) for t in TAX}

# ---------- cash months (opening, cash in and pay runs are typed; the rest is calculated)
def cash_d(): return [dict(row_id=c['row_id'], month=c['month'], opening=c['opening'], cash_in=c['cash_in'], pay_runs=c['pay_runs']) for c in CASH]
def _closing(c):
    m = c['month']; prev = add_months(d_(m), -1).replace(day=1).isoformat()
    return r2(c['opening'] + c['cash_in'] - (c['pay_runs'] + OVH_M[m] + DRAWS[m] + SETASIDE[prev]))
CASH_NOW = _closing(CASH[-1])
LAST_CASH = CASH[-1]

# ---------- pay runs from the payroll rows (hours and gross pay of each pay date), future runs estimated
def _runs():
    by = collections.defaultdict(lambda: [0.0, 0.0, '', ''])
    for r in PAY:
        a = by[r['pay_date']]; a[0] += r['regular_hours'] + r['overtime_hours'] + r['holiday_hours']; a[1] += r['gross_pay']; a[2] = r['period_start']; a[3] = r['period_end']
    return [(k, v) for k, v in sorted(by.items())]
RUNS = _runs()
def payruns_d():
    today = TODAY.isoformat()
    past = [x for x in RUNS if x[0] < today]
    nxt = [x for x in RUNS if x[0] >= today and x[1][1] > 20000]
    rows = past[-5:] + nxt[:1]
    last = d_(rows[-1][0]); base_h = sum(x[1][0] for x in rows[-4:]) / 4; base_c = sum(x[1][1] for x in rows[-4:]) / 4
    seas = [1.0, 1.012, 1.045, 1.04, 1.01, 1.0, 1.0]
    out = [dict(period_start=v[2], period_end=v[3], pay_date=k, hours=round(v[0], 1), est_cost=round(v[1], 2)) for k, v in rows]
    for i in range(1, 7):
        pd_ = last + dt.timedelta(days=14 * i)
        f = (1.004 ** i) * seas[i]
        out.append(dict(period_start=(pd_ - dt.timedelta(days=21)).isoformat(), period_end=(pd_ - dt.timedelta(days=8)).isoformat(), pay_date=pd_.isoformat(), hours=round(base_h * f, 1), est_cost=round(base_c * f, 2)))
    for i, o in enumerate(out): o['run_id'] = 'RN-%02d' % (i + 1)
    return [dict(run_id=o['run_id'], **{k: v for k, v in o.items() if k != 'run_id'}) for o in out]
PAYRUNS = payruns_d()

# ---------- 13-week forecast and expected receipts
FW0 = TODAY + dt.timedelta(days=7 - TODAY.weekday())
def _weekly_receipts():
    ms = [month_start(k).isoformat() for k in range(1, 7)]
    payer = sum(c['paid_amount'] for c in CLM if c['paid_on'] and c['paid_on'][:7] + '-01' in ms) / 6
    cin = sum(c['cash_in'] for c in CASH if c['month'] in ms) / 6
    return (cin - payer) * 12 / 52, payer * 12 / 52
PRIV_W, PAYER_W = _weekly_receipts()
_pf = [1.0, 1.02, 0.97, 1.03, 0.99, 1.01, 0.94, 0.90, 1.0, 1.05, 1.04, 1.02, 1.01]
_rf = [0.55, 1.35, 0.8, 1.6, 0.7, 1.1, 1.45, 0.6, 1.25, 0.9, 1.5, 0.75, 1.2]
_pay_w = [('Care insurer', 38), ('Third-party payer A', 45), ('Third-party payer B', 52)]
def receipts_d():
    out = []; i = 0
    for k in range(1, 14):
        s = (FW0 + dt.timedelta(days=7 * (k - 1))).isoformat()
        i += 1; out.append(dict(receipt_id='RC-%02d' % i, week_no=k, starts_on=s, source=key('payer', 'Private pay'), amount=round(PRIV_W * _pf[k - 1] * (0.97 + 0.06 * R.random()), -1), usual_days=10))
        src, dd = _pay_w[(k - 1) % 3]
        i += 1; out.append(dict(receipt_id='RC-%02d' % i, week_no=k, starts_on=s, source=key('payer', src), amount=round(PAYER_W * _rf[k - 1] * (0.97 + 0.06 * R.random()), -1), usual_days=dd))
    return out
RECEIPTS = receipts_d()
def _week_sum(src_private, k): return sum(r['amount'] for r in RECEIPTS if r['week_no'] == k and (r['source'] == key('payer', 'Private pay')) == src_private)

def _overhead_week(start):
    last3 = [month_start(k).isoformat() for k in (1, 2, 3)]
    avg = lambda cats: sum(CATM.get((m, c), 0) for m in last3 for c in cats) / 3
    lump1 = avg(['Office rent', 'Business insurance', 'Software and phones'])
    pay = avg(['Office payroll', 'Field supervisor pay'])
    other = (sum(OVH_M[m] for m in last3) / 3 - lump1 - pay) * 12 / 52
    tot = other
    for j in range(7):
        d = start + dt.timedelta(days=j)
        nxt = d + dt.timedelta(days=1)
        if d.day == 1: tot += lump1
        if d.day == 15: tot += pay / 2
        if nxt.day == 1: tot += pay / 2
    return round(tot, -1)
PROFIT3 = sum(PROFIT[month_start(k).isoformat()] for k in (1, 2, 3)) / 3
def forecast_d():
    out = []; n = 0
    for sc in SCEN:
        pf = {'Base': 1.0, 'Best': 1.04, 'Worst': 0.865}[sc]; qf = {'Base': 1.0, 'Best': 1.04, 'Worst': 0.86}[sc]; rf = {'Base': 1.0, 'Best': 1.0, 'Worst': 1.03}[sc]
        for k in range(1, 14):
            s = FW0 + dt.timedelta(days=7 * (k - 1)); e = s + dt.timedelta(days=6)
            run = sum(round(p['est_cost'] * (1 + BURDEN), 2) for p in PAYRUNS if s <= d_(p['pay_date']) <= e)
            draw = int(OWNER_DRAW) if any((s + dt.timedelta(days=j)).day == 5 for j in range(7)) else 0
            tx = int(round(PROFIT3 * TAX_SET_ASIDE_PCT, -1)) if any((s + dt.timedelta(days=j)).day == 10 for j in range(7)) else 0
            n += 1
            row = dict(row_id='FC-%03d' % n, week=key('wk', 'Week %d' % k), week_no=k, starts_on=s.isoformat(), scenario=key('scen', sc), private_receipts=round(_week_sum(True, k) * pf, -1),
                       payer_receipts=round(_week_sum(False, k) * qf, -1), pay_run=round(run * rf, 2) if run else '', overhead=_overhead_week(s), owner_draw=draw or '', tax_set_aside=tx or '')
            out.append(nb(row))
    return out
FORECAST = forecast_d()

# ---------- health history
def _month_key(d): return d[:7]
def _overtime():
    a = collections.defaultdict(lambda: [0.0, 0.0])
    for r in PAY:
        a[r['month']][0] += r['overtime_hours']; a[r['month']][1] += r['regular_hours'] + r['overtime_hours'] + r['holiday_hours']
    return {m: v[0] / v[1] for m, v in a.items() if v[1]}
def _fill():
    a = collections.defaultdict(lambda: [0.0, 0.0])
    for r in WK:
        if r['week'] <= TODAY.isoformat(): a[r['month']][0] += r['uncovered_hours']; a[r['month']][1] += r['scheduled_hours']
    return {m: 1 - v[0] / v[1] for m, v in a.items() if v[1]}
def _days_to_pay():
    a = collections.defaultdict(list)
    for r in INV:
        if r['status'] == 'Paid' and r['paid_on'] != '' and r['days_to_pay'] != '': a[r['paid_on'][:7] + '-01'].append(r['days_to_pay'])
    return {m: sum(v) / len(v) for m, v in a.items()}
def _turnover():
    out = {}
    for m in MONTHS:
        end = add_months(d_(m), 1) - dt.timedelta(days=1); start = end - dt.timedelta(days=365)
        left = sum(1 for g in CGR if g['left_date'] and start < d_(g['left_date']) <= end)
        act = sum(1 for g in CGR if d_(g['hire_date']) <= end and (not g['left_date'] or d_(g['left_date']) > end))
        out[m] = left / max(act, 1)
    return out
OT, FILL, DTP, TURN = _overtime(), _fill(), _days_to_pay(), _turnover()
EST_CLOSE = [41000, 43500, 40200, 44800, 47000, 49500, 52800, 58000, 64500, 70800]
def _cover(i, m):
    base = PNL[i] if m != M0 else PNL[i - 1]
    weekly = (base['direct_cost'] + OVH_M[base['month']]) * 12 / 52
    closing = EST_CLOSE[i] if i < len(EST_CLOSE) else [_closing(c) for c in CASH if c['month'] == m][0]
    return closing / weekly
def health_d():
    out = []
    for i, m in enumerate(MONTHS):
        out.append(dict(hl_id='HS-%02d' % (i + 1), month=m, overtime_share=round(OT.get(m, 0.005), 4), fill_rate=round(FILL.get(m, 0.985), 4), days_to_pay=round(DTP.get(m, 13), 1),
                        turnover_rate=round(TURN[m], 4), cover_weeks=round(_cover(i, m), 2)))
    return out
HEALTH = health_d()
HEALTH_NOW = dict(HEALTH[-1], margin=round(PNL[-1]['gross_margin'] / PNL[-1]['billed_hours'], 2))
TARGETS = {'Gross margin per hour': (12.5, 11.5, 10.5, 25), 'Overtime share': (0.02, 0.03, 0.05, 10), 'Fill rate': (0.97, 0.95, 0.92, 15), 'Days to be paid': (14, 18, 28, 15),
           'Caregiver turnover': (0.25, 0.30, 0.45, 15), 'Weeks of cash cover': (4, 3, 1.5, 20)}
def targets_d():
    out = []; n = 0
    for m in MEAS:
        for j, lv in enumerate(LVL):
            n += 1; out.append(dict(tg_id='TG-%02d' % n, measure=key('meas', m), level=key('lvl', lv), value=TARGETS[m][j]))
    return out

# ---------- weekly hours, service revenue, marketing, team, start-up pages
def weekly_d():
    rows = [r for r in WK if r['week'] <= TODAY.isoformat()]
    return [dict(row_id=r['row_id'], week=r['week'], scheduled_hours=r['scheduled_hours'], delivered_hours=r['delivered_hours'], billed_hours=r['billed_hours'], paid_hours=r['paid_hours'], visits=r['visits']) for r in rows]
def svcrev_d():
    return [dict(row_id=r['row_id'], month=r['month'], service=key('svc', r['service']), billed_hours=r['billed_hours'], revenue=r['revenue'], cost=r['cost']) for r in SM]
def marketing_d():
    return [dict(campaign_id=r['campaign_id'], month=r['month'], kind=key('mkind', r['kind']), for_recruiting=yn(r['target'] == 'Caregivers'), cost=r['cost'], results=r['results'], started=r['started']) for r in MK]
def team_d():
    return [dict(staff_id=t['staff_id'], name=t['name'], role=key('role', t['role']), team=key('team', t['team']), pay_type=key('paytype', t['pay_type']), phone=t['phone'], email=t['email'],
                 hours_week=t['hours_week'], monthly_salary=int(t['monthly_salary']), hourly_rate=int(t['hourly_rate']), speciality=t['speciality'], country=t['country'], start=t['start']) for t in team]
PAGES = [('Enquiries', 'Part 1', True, 0, 'Log every call and message; the answer time and the start date show how fast you win a client'), ('Quotes and Agreements', 'Part 1', True, 0, 'A quote and a signed service agreement before the first visit'),
         ('Schedule', 'Part 2', True, 0, 'The weekly schedule; a rota or roster for one person is a short list'), ('Caregiver Matching', 'Part 2', False, 8, 'Skills, area, language and availability matter once you can choose between caregivers'),
         ('Open Shifts and Cover', 'Part 2', False, 10, 'A visit without a caregiver and who takes it; needed once call-offs happen weekly'), ('Visits and Check-ins', 'Part 3', True, 0, 'Typed or pasted check-in times against the schedule'),
         ('Payroll and Overtime', 'Part 4', True, 0, 'Hours, travel and mileage into pay; overtime shows before the pay run'), ('Invoices and Deposits', 'Part 5', True, 0, 'Invoice by actual hours and keep deposits and balances'),
         ('Payer Claims', 'Part 5', False, 12, 'Claims as status and amounts only; needed when a third-party payer pays part of the hours'), ('Recruiting and Renewals', 'Part 6', False, 5, 'Applicants, onboarding and credential renewals once you hire every few months'),
         ('Client Margin', 'Part 7', False, 15, 'Margin per client hour matters when clients differ in rate and travel'), ('Cash Forecast', 'Part 8', True, 0, 'The 13-week forecast and the safe owner draw: use it from day one')]
def startup_d():
    return [dict(page_id='SP-%02d' % (i + 1), page=p[0], part=p[1], one_person=yn(p[2]), from_caregivers=p[3], note=p[4]) for i, p in enumerate(PAGES)]

# ---------- hours plan, break-even scenarios, staff cost
def hplan_d():
    rows = [('Today', 860, 12.2, 32800, 7500), ('Owner draw 10,000', 860, 12.2, 32800, 10000), ('Owner draw 12,500', 860, 12.2, 32800, 12500), ('Add a scheduler', 880, 12.2, 37200, 7500),
            ('Scheduler and draw 10,000', 920, 12.3, 37200, 10000), ('Rate rise 3 percent', 860, 13.27, 32800, 7500), ('Rate rise 3 percent, draw 12,500', 860, 13.27, 32800, 12500),
            ('Grow to 1,000 hours', 1000, 12.3, 37200, 9000), ('1,000 hours, second coordinator', 1000, 12.3, 44400, 10000), ('1,100 hours, two office hires', 1100, 12.4, 46800, 12000),
            ('1,200 hours, full office team', 1200, 12.5, 52500, 14000), ('Slow year, hours fall 5 percent', 817, 12.0, 32800, 7500)]
    return [dict(plan_id='HP-%02d' % (i + 1), plan=r[0], weekly_hours=r[1], margin_hour=r[2], overhead=r[3], draw=r[4]) for i, r in enumerate(rows)]
def breakeven_d():
    rows = [('Today', 0, 0, 0), ('Rate rise 2 percent', .02, 0, 0), ('Rate rise 3 percent, lose 1 percent of hours', .03, .01, 0), ('Rate rise 5 percent, lose 3 percent of hours', .05, .03, 0),
            ('Rate rise 5 percent, lose 6 percent of hours', .05, .06, 0), ('Lose the weakest client', 0, .014, 0), ('Add a scheduler', 0, 0, 4200), ('Scheduler and rate rise 3 percent', .03, 0, 4200),
            ('Scheduler, lose 2 percent of hours', 0, .02, 4200), ('Hard year, lose 8 percent of hours', 0, .08, 0), ('Rate rise 4 percent, lose 2 percent, scheduler', .04, .02, 4200),
            ('Two office hires, rate rise 5 percent', .05, 0, 8400)]
    return [dict(sc_id='BS-%02d' % (i + 1), scenario=r[0], rate_rise=r[1], hours_lost=r[2], scheduler_cost=r[3]) for i, r in enumerate(rows)]
def staffcost_d():
    people = [('Marguerite Adeyemi', 7500, 45), ('Tomasz Kowalski', 4300, 40), ('Priyanka Nair', 4800, 40), ('Camille Dubois', 2253, 20), ('Joaquin Ramirez', 3900, 40), ('Amara Diallo', 3800, 40)]
    out = []; n = 0
    for nm, sal, hrs in people:
        for ver, f, hf in (('Current', 1.0, 1.0), ('After raise', 1.035, 1.0), ('At 1,000 hours', 1.08, 1.1)):
            n += 1; out.append(dict(sc_id='SC-%02d' % n, person=nm, version=key('stver', ver), monthly_salary=int(round(sal * f)), hours_week=int(round(hrs * hf))))
    return out

# ---------- values the tools start from (the same numbers the workbook shows)
def _pn(m, k): return [r for r in PNL if r['month'] == m][0][k]
LAST = [r for r in PNL if r['month'] == M1][0]
LAST_MPH = LAST['gross_margin'] / LAST['billed_hours']; LAST_RPH = LAST['revenue'] / LAST['billed_hours']; LAST_OVH = OVH_M[M1]; LAST_HOURS = LAST['billed_hours'] / (52 / 12)
if __name__ == '__main__':
    print('cash now', CASH_NOW, 'priv w', round(PRIV_W), 'payer w', round(PAYER_W), 'fw0', FW0, 'profit3', round(PROFIT3))
    print('last mph', round(LAST_MPH, 3), 'rph', round(LAST_RPH, 2), 'ovh', LAST_OVH, 'hours', round(LAST_HOURS, 1))
    for h in HEALTH[-6:]: print(h)
    for sc in SCEN:
        cl = CASH_NOW; low = 1e9
        for f in [f for f in FORECAST if f['scenario'] == key('scen', sc)]:
            cl += f['private_receipts'] + f['payer_receipts'] - f.get('pay_run', 0) - f['overhead'] - f.get('owner_draw', 0) - f.get('tax_set_aside', 0); low = min(low, cl)
        print(sc, 'week13', round(cl), 'lowest', round(low))
    for p in PAYRUNS: print(p)
