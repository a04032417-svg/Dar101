"""Part 3 demo rows from hv_core: row-level tables show recent jobs and all callbacks; aggregated tables are built from the full generator output."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hv3_lists import *
import collections

T0 = TODAY.isoformat()
WH = 'Water heater replacement'
ST = story()
JALL = job_rows()
JD = {j['job_id']: j for j in JALL}
SITE = {s['site_id']: s for s in site_rows()}
EQ = {e['equipment_id']: e for e in equipment_rows()}
PH = {t['name']: t['phone'] for t in team}
OWNER_PHONE = PH[OWNER]; OFFICE_PHONE = PH[OFFICE_MANAGER]
_BYID = {t['staff_id']: t['name'] for t in team}
EQUIP_NAME, COUNTER_NAME, ELEC_NAME, SHEET_NAME, ACCT_NAME, INS_NAME = [_BYID['HV-%d' % i] for i in range(11, 17)]
CONTACT = {t['staff_id']: t['phone'] for t in team}
EQUIP_PHONE, COUNTER_PHONE, ELEC_PHONE, SHEET_PHONE, ACCT_PHONE, INS_PHONE = [CONTACT['HV-%d' % i] for i in range(11, 17)]
TECH_PHONES = [PH[n] for n in LEADS]
CREW_PHONES = [PH[n] for n in TECH_NAMES]
DONE = [j for j in JALL if j['status'] == 'Completed' and j['date'] <= T0]
BASE = [j for j in DONE if not j['is_callback']]
M12 = month_start(12).isoformat(); M24 = month_start(24).isoformat(); D90 = ago(90); D120 = ago(120); D125 = ago(125)
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def per(d):
    """period key of a date, or None"""
    if d > T0: return None
    out = []
    if d > D90: out.append('Last 90 days')
    if d >= M12: out.append('Last 12 months')
    elif d >= M24: out.append('Previous 12 months')
    return out
def shown(j):
    return j['status'] in ('Completed', 'In progress') and j['date'] <= T0 and (j['date'] > D90 or (j['job_type'] == WH and j['date'] > D125))

# ---------- jobs (every job of the last 90 days plus the water heater jobs of the 35 days before)
def jobs_d():
    out = []
    # a few recent repair, replacement and install jobs whose parts are not entered yet (the office chases them)
    late = [j['job_id'] for j in JALL if shown(j) and j['status'] == 'Completed' and not j['is_callback'] and j['kind'] in ('Repair', 'Replacement', 'Install') and j['parts_cost'] > 0 and j['date'] > ago(14)][-6:]
    for j in JALL:
        if not shown(j): continue
        s = SITE[j['site_id']]
        r = dict(job_id=j['job_id'], date=j['date'], site_ref=s['site_ref'], phone=s['phone'], site_type=key('sitetype', j['site_type']), job_type=key('jobtype', j['job_type']),
                 technician=key('tech', j['technician']), assistant=key('assist', j['assistant']) if j['assistant'] else '', van=key('van', j['van']), hours=j['hours'], assistant_hours=j['assistant_hours'],
                 drive_hours=j['drive_hours'], price=j['price'], parts_cost=j['parts_cost'], labour_cost=j['labour_cost'], permit_fee=j['permit_fee'], disposal=j['disposal'],
                 sub_cost=j['sub_cost'], vehicle_cost=j['vehicle_cost'], task_id=j['task_id'], tier=key('tier', j['tier']) if j['tier'] else '', is_callback=bool(j['is_callback']),
                 original_job=j['original_job'], warranty=bool(j['warranty']))
        if j['status'] == 'In progress': r.update(hours=0, assistant_hours=0, labour_cost=0)   # hours are entered when the job is closed
        if j['job_id'] in late: r.update(parts_cost=0)
        out.append(nb(r))
    return out

# ---------- job costing lines (the jobs a reviewer opens: every losing or thin job of the last 90 days and the latest jobs)
def costing_d():
    ids = []
    rows = [j for j in JALL if shown(j) and j['date'] > D90]
    for j in rows:
        if j['status'] == 'In progress': continue
        if j['margin'] < 0 or (j['price'] > 0 and j['margin_pct'] < 0.15): ids.append(j['job_id'])
    ids = set(ids) | {j['job_id'] for j in rows[-60:]}
    return [dict(job_id=i) for i in sorted(ids)]

# ---------- callbacks
def callbacks_d():
    out = []
    for b in callback_rows():
        o = JD[b['original_job']]; s = SITE[b['site_id']]
        et = EQ[o['equipment_id']]['type'] if o['equipment_id'] else 'No equipment record'
        out.append(nb(dict(callback_id=b['callback_id'], date=b['date'], month=b['month'], original_job=b['original_job'], callback_job=b['callback_job'], technician=key('tech', b['technician']),
                           job_type=key('jobtype', b['job_type']), site_id=b['site_id'], site_ref=s['site_ref'], phone=s['phone'], reason=key('cbreason', b['reason']), hours=b['hours'],
                           drive_hours=b['drive_hours'], parts_cost=b['parts_cost'], cost=b['cost'], warranty=bool(b['warranty']), days_after=b['days_after'], equip_type=key('eqtype', et))))
    return out

# ---------- margin by job type (three windows: last 120 days, the 12 months before it, the same 120 days a year earlier)
def _agg(js):
    return dict(n=len(js), rev=round(sum(j['price'] for j in js), 2), cost=round(sum(j['total_cost'] for j in js), 2), hrs=round(sum(j['hours'] for j in js), 2), drv=round(sum(j['drive_hours'] for j in js), 2))
def margin_jt_d():
    out = []
    for t in JOB_TYPES:
        js = [j for j in BASE if j['job_type'] == t]
        r = _agg([j for j in js if D120 < j['date'] <= T0]); p = _agg([j for j in js if ago(485) < j['date'] <= D120]); y = _agg([j for j in js if ago(485) < j['date'] <= ago(365)])
        out.append(dict(job_type=key('jobtype', t), jobs_120=r['n'], revenue_120=r['rev'], cost_120=r['cost'], hours_120=r['hrs'], drive_120=r['drv'], revenue_p12=p['rev'], cost_p12=p['cost'],
                        jobs_ly=y['n'], revenue_ly=y['rev'], cost_ly=y['cost']))
    return out

# ---------- margin by month for six main job types
_rev = collections.Counter()
for _j in BASE:
    if _j['date'] >= month_start(11).isoformat() and _j['job_type'] != WH: _rev[_j['job_type']] += _j['price']
MAIN6 = [t for t, _ in _rev.most_common(6)]
def margin_month_d():
    out = []
    for k in range(11, -1, -1):
        m = month_start(k).isoformat()
        for t in MAIN6:
            js = [j for j in BASE if j['month'] == m and j['job_type'] == t]
            a = _agg(js)
            out.append(dict(row_id='MM-%03d' % (len(out) + 1), month=m, job_type=key('jobtype', t), jobs=a['n'], revenue=a['rev'], cost=a['cost']))
    return out

# ---------- ticket tables: technician, van, site type by period
def _tick(field, names, lst):
    out = []
    n = 0
    for nm in names:
        for p in PERIODS:
            js = [j for j in BASE if j[field] == nm and p in per(j['date'])]
            a = _agg(js); n += 1
            out.append(dict(row_id='%s-%02d' % (field[:2].upper(), n), **{field: key(lst, nm)}, period=key('period', p), jobs=a['n'], revenue=a['rev'], cost=a['cost']))
    return out
def tick_tech_d(): return _tick('technician', LEADS, 'tech')
def tick_van_d(): return _tick('van', VAN_NAMES, 'van')
def tick_site_d(): return _tick('site_type', SITE_TYPES, 'sitetype')

# ---------- ticket by month (every month of the history)
_KB = {'Repair', 'Replacement', 'Install', 'Drain', 'Repipe', 'Tune-up', 'Diagnostic'}
def tick_month_d():
    out = []
    months = sorted({j['month'] for j in DONE})
    for i, m in enumerate(reversed(months), 1):
        js = [j for j in BASE if j['month'] == m]
        a = _agg(js)
        part = round(sum(j['parts_cost'] for j in js), 2); lab = round(sum(j['labour_cost'] for j in js), 2); sub = round(sum(j['sub_cost'] for j in js), 2)
        oth = round(sum(j['permit_fee'] + j['disposal'] + j['vehicle_cost'] for j in js), 2)
        lose = sum(1 for j in DONE if j['month'] == m and j['total_cost'] > j['price'] and j['hours'] > 0)
        base_jobs = sum(1 for j in js if can_cb(j))
        out.append(dict(row_id='TM-%03d' % i, month=m, jobs=a['n'], revenue=a['rev'], parts_cost=part, labour_cost=lab, sub_cost=sub, other_cost=oth, losing_jobs=lose, base_jobs=base_jobs, owner_name=OWNER, acct_name=ACCT_NAME, ins_name=INS_NAME))
    return out
# the callback-rate base of hv_core: completed jobs of a kind that can have a callback (never an agreement visit)
def can_cb(j): return j['kind'] in _KB and j['job_type'] != 'Agreement visit'
BASEJ = [j for j in BASE if can_cb(j)]

def cb_tech_d():
    out = []; n = 0
    for nm in LEADS:
        for p in PERIODS:
            js = [j for j in BASEJ if j['technician'] == nm and p in per(j['date'])]
            n += 1
            out.append(dict(row_id='CT-%02d' % n, technician=key('tech', nm), period=key('period', p), jobs=len(js)))
    return out

def cb_type_d():
    out = []
    for t in JOB_TYPES:
        js = [j for j in BASE if j['job_type'] == t and M12 <= j['date'] <= T0]
        a = _agg(js); nj = sum(1 for j in js if can_cb(j))
        out.append(dict(job_type=key('jobtype', t), jobs=nj, revenue=a['rev'], cost=a['cost']))
    return out

def cb_reason_d(): return [dict(reason=key('cbreason', r)) for r in CALLBACK_REASONS]

def price_book_d():
    return [dict(pb_id=p['pb_id'], task=p['task'], job_type=key('jobtype', p['job_type']), tier=key('tier', p['tier']) if p['tier'] else '', labour_hours=p['labour_hours'], parts_cost=p['parts_cost'],
                 flat_price=p['flat_price'], previous_price=p['previous_price'], cost=p['cost'], permit_fee=p['permit_fee'], disposal=p['disposal'], sub_cost=p['sub_cost'])
            for p in price_book]
def price_changes_d():
    return [dict(change_id=c['change_id'], date=c['date'], part_id=c['part_id'], part=c['part'], supplier=key('supplier', c['supplier']), old_cost=c['old_cost'], new_cost=c['new_cost']) for c in price_change_rows()]

def wh_month_d():
    out = []
    WHP = [p['part'] for p in parts if p['part_id'] in ST['margin_part_ids']]
    for i, k in enumerate(range(13, -1, -1)):
        m = month_start(k); ms = m.isoformat()
        js = [j for j in BASE if j['job_type'] == WH and j['month'] == ms]
        a = _agg(js)
        uc = round(sum(cost_at(pid, m.replace(day=15) if m.replace(day=15) <= TODAY else TODAY) for pid in WHP) / len(WHP), 2)
        out.append(dict(month=ms, jobs=a['n'], revenue=a['rev'], cost=a['cost'], unit_cost=uc))
    return out

def replace_d():
    r = rng('hv3_replace'); out = []
    pbp = {p['task']: p for p in price_book}
    base_rep = {'Furnace': 'Furnace, high efficiency', 'Air conditioner': 'Air conditioner, high efficiency', 'Heat pump': 'Heat pump, standard', 'Boiler': 'Furnace, standard efficiency',
                'Water heater': 'Water heater, 50 gal tank', 'Mini-split': 'Mini-split, single zone'}
    life = {'Furnace': 18, 'Air conditioner': 15, 'Heat pump': 15, 'Boiler': 20, 'Water heater': 12, 'Mini-split': 13}
    seen, n = set(), 0
    eqs = sorted(EQ.values(), key=lambda e: e['install_date'])
    for e in eqs[::97]:
        if n >= 12: break
        s = SITE[e['site_id']]
        if s['site_ref'] in seen or e['type'] not in base_rep: continue
        seen.add(s['site_ref']); n += 1
        age = int((TODAY - to_date(e['install_date'])).days / 365.25)
        rep = pbp[base_rep[e['type']]]['flat_price']
        quote = round(rep * r.uniform(0.07, 0.3) / 5) * 5
        out.append(dict(site_ref=s['site_ref'], phone=s['phone'], equip_type=key('eqtype', e['type']), quote_date=ago(3 + n * 6), age_years=max(age, 4 + n % 9), repair_quote=quote, replace_price=rep, life_years=life[e['type']]))
    return out

def settings_echo_d():
    return [dict(setting='Margin target for a whole job', note='A typical range, check your own numbers'), dict(setting='Thin margin below', note='A job under this share of its price is flagged as thin'),
            dict(setting='Callback rate target', note='Callbacks over jobs that can have one; set your own'), dict(setting='Close rate', note='Estimates won over estimates decided'),
            dict(setting='Warranty reserve', note='Share of revenue you set aside for warranty visits'), dict(setting='Overhead per month', note='Rent, insurance, office and other fixed cost'),
            dict(setting='Labour extras on pay', note='Employer extras on pay, confirm with your adviser'), dict(setting='Replace lead age', note='Equipment age that makes a replacement quote worth offering')]

def scenarios_d():
    vols = [-0.10, 0.0, 0.10, 0.20]
    base = {'Base': (0.0, 0.0, 0.0), 'Best': (-0.03, -0.04, 0.03), 'Worst': (0.05, 0.08, -0.03)}
    out = []
    for s in SCEN:
        for v in vols:
            lab, par, clo = base[s]
            out.append(dict(row_id='SC-%02d' % (len(out) + 1), scenario=key('scen', s), volume_change=v, labour_change=lab, parts_change=par, close_change=clo))
    return out

def job_types_d(): return [dict(job_type=key('jobtype', t['job_type']), trade=key('trade', t['trade']), kind=key('jobkind', t['kind']), target_margin=t['target_margin']) for t in job_types]
def technicians_d():
    ts = {t['name']: t for t in techs}
    return [dict(technician=key('tech', n), hourly_rate=ts[n]['hourly_rate'], van=key('van', ts[n]['van'])) for n in LEADS]
def _overhead():
    tm = [r for r in tick_month_d() if month_start(12).isoformat() <= r['month'] < month_start(0).isoformat()]
    cb = sum(b['cost'] for b in callback_rows() if month_start(12).isoformat() <= b['date'] < month_start(0).isoformat())
    contrib = sum(r['revenue'] - r['parts_cost'] - r['labour_cost'] - r['sub_cost'] - r['other_cost'] for r in tm) / 12 - cb / 12
    net = sum(r['net_profit'] for r in pnl_rows()[-13:-1]) / 12
    return round((contrib - net) / 500) * 500
OVERHEAD_MONTH = _overhead()


# greeting names: contact columns added to the tables whose messages greet the owner, office, supplier or subcontractors
def _with(fn, extra):
    def g():
        return [dict(r, **extra(r)) for r in fn()]
    return g
_o = {'owner_name': OWNER}
margin_jt_d = _with(margin_jt_d, lambda r: _o)
cb_tech_d = _with(cb_tech_d, lambda r: _o)
wh_month_d = _with(wh_month_d, lambda r: _o)
callbacks_d = _with(callbacks_d, lambda r: {'office_name': OFFICE_MANAGER})
costing_d = _with(costing_d, lambda r: {'office_name': OFFICE_MANAGER, 'counter_name': COUNTER_NAME, 'elec_name': ELEC_NAME, 'sheet_name': SHEET_NAME})
price_changes_d = _with(price_changes_d, lambda r: {'supplier_contact': EQUIP_NAME if r['supplier'] == key('supplier', 'Your equipment supplier') else COUNTER_NAME})
