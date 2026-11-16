"""HVAC and plumbing suite part 2: demo rows from hv_core."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hv2_lists import *
import collections, hashlib

ST = story()
SITES = {s['site_id']: s for s in site_rows()}
JOBS = job_rows()
PHONE = {t['staff_id']: t['phone'] for t in team}
NAME_PHONE = {t['name']: t['phone'] for t in team}
OWNER_PH, OFFICE_PH = PHONE['HV-01'], PHONE['HV-02']
EQUIP_PH, COUNTER_PH, ELEC_PH, SHEET_PH, ACCT_PH, APPR_PH = PHONE['HV-11'], PHONE['HV-12'], PHONE['HV-13'], PHONE['HV-14'], PHONE['HV-15'], PHONE['HV-09']
TECH_PH = [NAME_PHONE[n] for n in TECH6]
PLUMB_LEAD, HVAC_LEAD = NAME_PHONE['Jamal Whitfield'], NAME_PHONE['Tomasz Nowak']


def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def h(s): return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)


# ---- jobs per price book task, last 12 months
_TK = collections.Counter(j['task_id'] for j in JOBS if j['status'] == 'Completed' and ago(365) < j['date'] <= TODAY.isoformat() and not j['is_callback'])


def book_d():
    out = []
    for p in price_book:
        pl = PB[p['pb_id']]['_parts']
        mp, mq = '', 0
        if pl:
            nm, q = max(pl, key=lambda x: PART[x[0]]['unit_cost'] * x[1]); mp, mq = PART[nm]['part_id'], q
        out.append(nb(dict(pb_id=p['pb_id'], job_type=key('jobtype', p['job_type']), task=p['task'], tier=key('tier', p['tier']) if p['tier'] else '', labour_hours=p['labour_hours'],
                           parts_cost=p['parts_cost'], permit_fee=p['permit_fee'], disposal=p['disposal'], sub_cost=p['sub_cost'], flat_price=p['flat_price'], previous_price=p['previous_price'],
                           main_part=mp, main_qty=mq, jobs_12m=max(_TK.get(p['pb_id'], 0), 1))))
    out.sort(key=lambda r: r['pb_id'] != 'PB-039')
    return out


def parts_d():
    return [dict(part_id=p['part_id'], part=p['part'], category=key('partcat', p['category']), unit_cost=p['unit_cost'], markup=p['markup'], supplier=key('supplier', p['supplier'])) for p in parts]


# ---- estimates (all, newest first)
_EST = estimate_rows()
_OPEN = [e for e in _EST if e['outcome'] == 'Open']
_NOFU = {e['estimate_id'] for e in sorted(_OPEN, key=lambda e: e['date'])[:4]}   # four older open estimates have no follow-up date
_JB = {j['job_id']: j for j in JOBS}
_CALL = {c_['call_id']: c_ for c_ in call_rows()}


def _call_date(e):
    if e['job_id'] and e['job_id'] in _JB:
        cl = _CALL.get(_JB[e['job_id']]['call_id'])
        if cl: return cl['date']
    return ago((TODAY - to_date(e['date'])).days + h(e['estimate_id']) % 4)


def estimates_d():
    out = []
    for e in sorted(_EST, key=lambda e: (e['date'], e['estimate_id']), reverse=True):
        s = SITES[e['site_id']]
        fu = '' if e['estimate_id'] in _NOFU else e['followup_date']
        jd = _JB[e['job_id']]['date'] if e['job_id'] in _JB else ''
        out.append(nb(dict(estimate_id=e['estimate_id'], date=e['date'], month=e['month'], site_id=e['site_id'], site_ref=s['site_ref'], account=s['account'], phone=s['phone'],
                           job_type=key('estjt', e['job_type']), technician=key('tech', e['technician']), options_offered=e['options_offered'], good_price=e['good_price'],
                           better_price=e['better_price'], best_price=e['best_price'], option_chosen=key('optchosen', e['option_chosen']), outcome=key('estoutcome', e['outcome']),
                           price_won=e['price_won'], lost_reason=key('estlost', e['lost_reason']) if e['lost_reason'] else '', followup_date=fu,
                           call_date=_call_date(e), job_date=jd)))
    return out


def option_lines_d():
    pick = [e for e in _EST if e['outcome'] == 'Open' and e['job_type'] != 'Repipe']
    rest = [e for e in sorted(_EST, key=lambda e: e['date'], reverse=True) if e['outcome'] != 'Open' and e['options_offered'] == 3 and e['job_type'] != 'Repipe']
    chosen = (pick + rest)[:40]
    out, n = [], 0
    for e in chosen:
        for t in TIERS:
            if e['options_offered'] == 3 or (t != 'Best' and e['options_offered'] >= 2) or t == 'Good':
                n += 1; out.append(dict(line_id='OL-%03d' % n, estimate_id=e['estimate_id'], option=key('tier', t)))
    return out


def open_d(): return [dict(rank_no=i) for i in range(1, len(_OPEN) + 1)]
def under_d(): return [dict(rank_no=i) for i in range(1, 16)]


def close_option_d(): return [dict(option=key('tier', t), period=key('period', p)) for t in TIERS for p in PERIODS]
def close_tech_d(): return [dict(technician=key('tech', t), period=key('period', p)) for t in TECH6 for p in PERIODS[1:]]
def close_jt_d(): return [dict(job_type=key('estjt', t), period=key('period', p)) for t in EST_JT for p in PERIODS[1:]]
def lost_d(): return [dict(reason=key('estlost', r)) for r in EST_LOST]
def est_months_d():
    out = []
    w = {p['pb_id']: _TK.get(p['pb_id'], 1) for p in price_book}
    for m in months14():
        num = den = 0.0
        for p in price_book:
            pl = PB[p['pb_id']]['_parts']; pc = sum(cost_at(nm, m) * q for nm, q in pl)
            cost = p['cost'] - p['parts_cost'] + pc
            price = pb_price(p, m); num += w[p['pb_id']] * (price - cost); den += w[p['pb_id']] * price
        out.append(dict(month=iso(m), book_margin=round(num / den, 3)))
    return out


def job_types_d():
    return [dict(job_type=j['job_type'], trade=key('trade', j['trade']), kind=key('jobkind', j['kind']), avg_hours=j['avg_hours'], target_margin=j['target_margin']) for j in job_types]


def labour_d():
    return [dict(technician=key('tech', t['name']), hourly_rate=t['hourly_rate']) for t in techs[:6]]


def changes_d():
    return [dict(change_id=r['change_id'], date=r['date'], part_id=r['part_id'], supplier=key('supplier', r['supplier']), old_cost=r['old_cost'], new_cost=r['new_cost']) for r in price_change_rows()]


def rise_d(): return [dict(rise_pct=round(i / 100.0, 2)) for i in range(1, 13)]
def fin_d(): return [dict(term_months=t, monthly_factor=f) for t, f in ((12, 0.0879), (24, 0.0461), (36, 0.0323), (48, 0.0254), (60, 0.0212), (72, 0.0185))]
def tech_d(): return [dict(technician=key('tech', t['name']), trade=key('trade', t['trade']), van=key('van', t['van'])) for t in techs[:6]]


# ---- diagnostic visits by month (jobs of type Diagnostic visit, completed); conversion = visits that led to a repair or replacement estimate
def _rate(tech, m):
    base = {'Tomasz Nowak': 0.66, 'Kofi Mensah': 0.57, 'Elena Rossi': 0.62}[tech]
    return base + (0.05 if m in (12, 1, 2, 6, 7, 8) else -0.03)


_DIAG = [j for j in JOBS if j['job_type'] == 'Diagnostic visit' and j['status'] == 'Completed']
for _j in _DIAG: _j['_conv'] = (h(_j['job_id']) % 1000) / 1000.0 < _rate(_j['technician'], int(_j['month'][5:7]))


def diag_d():
    out = []
    for m in months14():
        ms = iso(m); js = [j for j in _DIAG if j['month'] == ms]
        out.append(dict(month=ms, visits=len(js), converted=sum(1 for j in js if j['_conv']), fee_income=round(sum(j['price'] for j in js), 2), visit_cost=round(sum(j['total_cost'] for j in js), 2)))
    return out


def diag_by_tech(days=365):
    r = {}
    for t in ('Tomasz Nowak', 'Kofi Mensah', 'Elena Rossi'):
        js = [j for j in _DIAG if j['technician'] == t and j['month'] >= iso(month_start(12))]
        r[t] = (len(js), sum(1 for j in js if j['_conv']))
    return r


# ---- sites (200) and quote log (30)
def sites_d():
    es = {e['site_id'] for e in _EST}
    rows = sorted(SITES.values(), key=lambda s: (s['site_id'] in es, s['last_job']), reverse=True)[:200]
    rows = sorted(rows, key=lambda s: s['site_id'])
    return [nb(dict(site_id=s['site_id'], site_ref=s['site_ref'], area=key('area', s['area']), site_type=key('sitetype', s['site_type']), account=s['account'], phone=s['phone'],
                    member=bool(s['member']), last_job=s['last_job'])) for s in rows]


def quotes_d():
    r = rng('hv2-quotes'); sd = sites_d(); out = []
    types = ['Heating repair', 'Cooling repair', 'Leak repair', 'Drain clearing', 'Boiler repair', 'Fixture install', 'Furnace tune-up', 'Air conditioner tune-up', 'Water heater replacement', 'Diagnostic visit']
    outs = ['Booked'] * 5 + ['Estimate needed'] * 2 + ['Thinking about it'] * 2 + ['Went elsewhere']
    for i in range(30):
        jt = types[i % len(types)]; lines = [p for p in price_book if p['job_type'] == jt]
        p = lines[r.randrange(len(lines))]; pr = round(p['flat_price'] * r.uniform(0.95, 1.12) / 5) * 5
        s = sd[(i * 7) % len(sd)]
        out.append(dict(quote_id='QT-%03d' % (30 - i), date=ago(1 + i * 2), site_ref=s['site_ref'], job_type=key('jobtype', jt), price_quoted=float(pr), outcome=key('quoteout', outs[r.randrange(len(outs))])))
    return out
