"""HVAC suite part 8: demo rows from hv_core (full generator output for the aggregated tables, recent rows elsewhere)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hv8_lists import *
import collections, random, datetime as _dt

TD = TODAY
MS0 = month_start(0)
M24 = [month_start(k) for k in range(23, -1, -1)]
M14 = [month_start(k) for k in range(13, -1, -1)]
M12 = [month_start(k) for k in range(11, -1, -1)]
NEXT12 = [add_months(MS0, k) for k in range(12)]
ST = story()
SITES = {s['site_id']: s for s in site_rows()}
PH = {t['name']: t['phone'] for t in team}
ROLEPH = {t['role']: t['phone'] for t in team}
OWNER_PHONE = PH[OWNER]; OFFICE_PHONE = PH[OFFICE_MANAGER]
SUP_PHONE = ROLEPH['Equipment supplier']; PARTS_PHONE = ROLEPH['Parts counter']; ACCT_PHONE = ROLEPH['Accountant']; AGENT_PHONE = ROLEPH['Insurance agent']
_sub = [t for t in team if t['role'] == 'Subcontractor']
ELEC_PHONE, SHEET_PHONE = _sub[0]['phone'], _sub[1]['phone']
TECH_PHONES = [PH[n] for n in TECH_NAMES]
APPR = [t['name'] for t in team if t['role'] == 'Apprentice']
APPR_PHONES = [PH[n] for n in APPR]
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def eom(d): return add_months(d, 1) - _dt.timedelta(days=1)

MK = marketing_rows(); RV = review_rows(); JOBS_ALL = job_rows(); CALLS_ALL = call_rows(); EST = estimate_rows(); INV = invoice_rows(); VIS = visit_rows()
RN = renewal_rows(); TM = tech_month_rows(); TS = timesheet_rows(); CBS = callback_rows(); PUR = purchase_rows(); PNL = pnl_rows(); CASH = cash_rows(); BILLS = bill_rows(); JTM = job_type_month_rows()
LIC = licence_rows()
WATCH = ST['margin_job_type']; WATCH_TARGET = ST['margin_target']

_W = hv_core_w = None
import hv_core as _hc
_JW = _hc._w()['jobs']
_BASE = [j for j in _JW if j['status'] == 'Completed' and not j['is_callback'] and j['_v'] is None and j['kind'] in _hc._KIND_CB]
_CBJ = [j for j in _JW if j['status'] == 'Completed' and j['is_callback']]
def cb_rate(lo, hi, tech=None):
    """callback rate of the core rule between two ISO dates (callbacks of the ORIGINAL technician over repeat-prone base jobs)"""
    lo, hi = to_date(lo), to_date(hi)
    b = sum(1 for j in _BASE if lo <= j['date'] <= hi and (tech is None or j['technician'] == tech))
    c = sum(1 for j in _CBJ if lo <= j['date'] <= hi and (tech is None or j['_orig']['technician'] == tech))
    return c / b if b else 0.0

# ---------- sold jobs by month and source
SOLD = collections.Counter()
for j in JOBS_ALL:
    if j['status'] == 'Completed': SOLD[(j['month'], j['source'])] += 1


def sources_d(): return [dict(source=key('source', s['source']), monthly_cost=s['monthly_cost'], kind=key('srckind', s['kind'])) for s in lead_sources]


def marketing_d():
    out = []
    for i, r in enumerate(MK):
        out.append(dict(row_id='MK-%04d' % (i + 1), month=r['month'], source=key('source', r['source']), spend=r['spend'], calls=r['calls'], booked=r['booked'], sold=SOLD[(r['month'], r['source'])], revenue=r['revenue']))
    return out


def calls_d(n=500):
    rows = [c for c in CALLS_ALL if c['date'] <= iso(TD)][-n:]
    return [nb(dict(call_id=c['call_id'], date=c['date'], month=c['month'], source=key('source', c['source']), call_type=key('calltype', c['call_type']), outcome=key('calloutcome', c['outcome']),
                    est_value=c['est_value'], job_id=c['job_id'])) for c in rows]


_RQ = {(r['month'], r['technician']): r for r in RV}
_R = rng('hv8-req')
def jobs_d(n=700):
    rows = [j for j in JOBS_ALL if j['date'] <= iso(TD)][-n:]
    out = []
    for j in rows:
        rv = _RQ.get((j['month'], j['technician']))
        pr = min(0.97, rv['requests_sent'] / max(rv['jobs'], 1)) if rv else 0.4
        pv = min(0.9, rv['reviews_received'] / max(rv['requests_sent'], 1)) if rv else 0.3
        done = j['status'] == 'Completed'
        sent = done and _R.random() < pr
        got = sent and _R.random() < pv
        s = SITES.get(j['site_id'])
        out.append(nb(dict(job_id=j['job_id'], date=j['date'], week=j['week'], month=j['month'], source=key('source', j['source']), job_type=key('jobtype', j['job_type']), kind=key('jobkind', j['kind']),
                           technician=key('tech', j['technician']), status=key('jobstatus', j['status']), price=j['price'], margin=j['margin'], request_sent=sent, reviewed=got,
                           site_ref=s['site_ref'] if s else '', account=j['account'], phone=s['phone'] if s else '', assistant=j['assistant'], assistant_phone=PH.get(j['assistant'], ''))))
    return out


def reviews_d():
    return [dict(row_id=r['row_id'], month=r['month'], technician=key('tech', r['technician']), jobs=r['jobs'], requests_sent=r['requests_sent'], reviews_received=r['reviews_received'], referrals=r['referrals']) for r in RV]


def src_results_d():
    out = []; i = 0
    for p in PERIODS:
        for s in SOURCES:
            i += 1; out.append(dict(row_id='SR-%02d' % i, source=key('source', s), period=key('period', p)))
    return out


def src_month_d():
    out = []; i = 0
    for m in M14:
        for s in SOURCES:
            i += 1; out.append(dict(row_id='SM-%03d' % i, month=iso(m), source=key('source', s)))
    return out


def rev_tech_d():
    out = []; i = 0
    for p in ['Last 12 months', 'Previous 12 months', 'Last 3 months']:
        for t in TECH6:
            i += 1; out.append(dict(row_id='RT-%02d' % i, technician=key('tech', t), period=key('period', p)))
    return out


def rev_month_d(): return [dict(month=iso(m)) for m in M14]
def tech_month_d():
    out = []; i = 0
    for t in TECH6:
        for m in M12:
            i += 1; out.append(dict(row_id='TR-%03d' % i, technician=key('tech', t), month=iso(m)))
    return out


def dates_d():
    rows = [dict(r) for r in LIC]
    opn = sorted([r for r in rows if r['status'] == 'Open'], key=lambda r: r['due_date'])
    # story: one tool calibration slipped past its date and is still open
    cal = [r for r in opn if r['item'] == 'Tool calibration']
    if cal: cal[0]['due_date'] = ago(6)
    first = opn[0]
    rows.remove(first); rows.insert(0, first)
    out = []
    for r in rows:
        out.append(nb(dict(licence_id=r['licence_id'], item=key('renewal', r['item']), holder=r['holder'], due_date=r['due_date'], renewed_on=r['renewed_on'], cost=r['cost'], status=key('rnstatus', r['status']))))
    return out


def ren_budget_d(): return [dict(month=iso(m)) for m in NEXT12]
def bands_d(): return [dict(band=key('band', b)) for b in BANDS]
def techs_d(): return [dict(technician=t['name'], trade=t['trade'], van=t['van']) for t in techs[:6]]
def cpb_month_d(): return [dict(month=iso(m)) for m in M14]
TYPICAL = ['45 to 60 percent', '8 to 20 percent', '60 to 80 percent', '2 to 6 percent', '2 to 6 percent', '40 to 65 percent', '35 to 55 percent', '0 to 1,000 amount', '80 to 95 percent', '85 to 95 percent', '20,000 to 40,000 amount', '1 to 3 months']
def targets_d(): return [dict(setting=key('measure', m), typical_range=TYPICAL[i]) for i, m in enumerate(MEASURES)]
def actions_d(): return [dict(rank=i + 1) for i in range(12)]


# ---------- scorecard history (24 months, current month = month to date or as of today)
def _share(num, den): return round(num / den, 4) if den else 0


def tuneup_share(asof):
    """share of the visits planned up to a date (in the open window, or the one that ended last) that were done by that date"""
    a = iso(asof)
    cur = max((v['window_start'] for v in VIS if v['window_start'] <= a), default=None)
    if cur is None: return None
    pl = [v for v in VIS if v['window_start'] == cur and v['planned_date'] <= a]
    if not pl: return None
    return sum(1 for v in pl if v['done_on'] and v['done_on'] <= a) / len(pl)


def history():
    jm = collections.defaultdict(lambda: [0.0, 0.0])
    for r in JTM: jm[r['month']][0] += r['revenue']; jm[r['month']][1] += r['margin']
    wh = {r['month']: r['margin_pct'] for r in JTM if r['job_type'] == WATCH}
    pn = {r['month']: r for r in PNL}; cs = {r['month']: r for r in CASH}
    ut = collections.defaultdict(lambda: [0.0, 0.0])
    for r in TS: ut[r['month']][0] += r['billed_hours']; ut[r['month']][1] += r['clock_hours']
    tj = collections.defaultdict(lambda: [0, 0]); tt = collections.defaultdict(lambda: [0, 0])
    for r in TM:
        tj[r['month']][0] += r['callbacks']; tj[r['month']][1] += r['jobs']
        tt[(r['technician'], r['month'])] = (r['callbacks'], r['jobs'])
    cl = collections.defaultdict(lambda: [0, 0])
    for r in EST:
        if r['outcome'] == 'Won': cl[r['month']][0] += 1
        if r['outcome'] in ('Won', 'Lost'): cl[r['month']][1] += 1
    rn = collections.defaultdict(collections.Counter)
    for r in RN:
        rn[r['month']][r['outcome']] += 1
    big = [i for i in INV if i['status'] != 'Written off']
    def age60(asof):
        a = iso(asof); cut = iso(asof - _dt.timedelta(days=60)); tot = 0.0
        for i in big:
            if i['date'] < cut and i['date'] <= a:
                if i['paid_on'] == '' : tot += i['balance']
                elif i['paid_on'] > a: tot += i['amount']
        return round(tot, 2)
    def bill7(asof):
        a = iso(asof); e = iso(asof + _dt.timedelta(days=7))
        v = [p['amount'] for p in PUR if a < p['due_date'] <= e]
        return round(max(v), 2) if v else 0.0
    out = []
    tun = {}
    for m in M24:
        asof = eom(m) if m < MS0 else TD
        tun[m] = tuneup_share(asof)
    for idx, m in enumerate(M24):
        ms = iso(m); cur = m == MS0
        asof = eom(m) if not cur else TD
        a = jm[ms]
        lo12 = iso(add_months(m, -11) if not cur else month_start(12)); hi = iso(eom(m) if not cur else TD)
        best = max(cb_rate(lo12, hi, t) for t in TECH6)
        c = cl[ms]
        r = rn[ms]
        renew = r['Renewed'] / (r['Renewed'] + r['Lapsed'] + r['Open']) if (r['Renewed'] + r['Lapsed'] + r['Open']) else 1
        tu = tun[m]
        if tu is None or m < M24[3]: tu = tun[add_months(m, 12)]
        cash = CASH and cs[ms]['closing_cash']
        fixed = cs[ms]['overhead'] + cs[ms]['owner_draw']
        out.append(dict(month=ms, margin=_share(a[1], a[0]), net_pct=_share(pn[ms]['net_profit'], pn[ms]['revenue']), utilisation=_share(ut[ms][0], ut[ms][1]), callbacks=round(cb_rate(ms, iso(eom(m) if not cur else TD)), 4),
                        top_callback=round(best, 4), close_rate=_share(c[0], c[1]), watch_margin=round(job_margin(WATCH, ago(120), iso(TD))['margin_pct'], 4) if cur else round(wh.get(ms, 0.45), 4),
                        ageing60=age60(asof), renewals=round(renew, 4), tuneups=round(tu, 4), cash=cash, bill_7d=(max(b['amount'] for b in BILLS if iso(TD) <= b['due_date'] <= ahead(7)) if cur else bill7(asof)), fixed_cost=round(fixed, 2)))
    return out


HIST = history()


def sc_history_d():
    rows = [dict(r) for r in HIST]
    last_full = [r for r in rows if r['month'] == iso(month_start(1))][0]
    rows.remove(last_full); rows.insert(0, last_full)
    return rows


def start_steps_d():
    rows = [('Replace the demo data', 'Type your company name and your own limits in Settings, then clear the sample rows you do not need', 'Start'),
            ('Set your targets', 'Check the twelve targets and their typical ranges against your own last 12 months', 'Targets'),
            ('Enter your lead sources', 'List the sources and what each costs a month', 'Lead Sources'),
            ('Enter marketing spend', 'Add each month the spend, calls, booked jobs, sold jobs and revenue of every source', 'Marketing Spend'),
            ('Enter 10 jobs', 'Add ten recent jobs with source, price, margin and whether you asked for a review', 'Jobs'),
            ('Enter reviews and referrals', 'Add each technician and month: jobs, requests sent, reviews received and referrals', 'Reviews and Referrals'),
            ('Enter renewal dates', 'List every licence, insurance, registration, inspection and training date with its cost', 'Renewal Dates'),
            ('Fill the scorecard history', 'Add one row per month with the measures the scorecard reads', 'Scorecard History'),
            ('Read the scorecard', 'Open the scorecard and the Monday actions and note the weakest link', 'Scorecard'),
            ('Hold the Monday meeting', 'Print the Monday actions and agree an owner and a date for each', 'Monday Actions')]
    return [dict(step=a, what=b, tab=c) for a, b, c in rows]


def _money_points():
    full = [r for r in PNL if iso(month_start(12)) <= r['month'] < iso(MS0)]
    rev = sum(r['revenue'] for r in full)
    lo, hi = month_start(12), TD
    base = [j for j in _BASE if lo <= j['date'] <= hi]
    cbs = [r for r in CBS if iso(lo) <= r['date'] <= iso(hi)]
    avg_cb = sum(r['cost'] for r in cbs) / max(len(cbs), 1)
    kofi = sum(1 for j in base if j['technician'] == ST['callback_tech'])
    est = [e for e in EST if iso(lo) <= e['date'] <= iso(hi) and e['outcome'] in ('Won', 'Lost')]
    won = [e['price_won'] for e in est if e['outcome'] == 'Won' and e['price_won']]
    avg_won = sum(won) / max(len(won), 1)
    wh = sum(r['revenue'] for r in JTM if r['job_type'] == WATCH and iso(lo) <= r['month'] < iso(MS0))
    ren = [r for r in RN if iso(lo) <= r['due_date'] <= iso(hi)]
    avg_fee = sum(r['price'] for r in ren) / max(len(ren), 1)
    util = [r['utilisation'] for r in HIST[-13:-1]]
    fixed = sum(r['fixed_cost'] for r in HIST[-13:-1]) / 12
    win = max(v['window_start'] for v in VIS if v['window_start'] <= iso(TD))
    nwin = sum(1 for v in VIS if v['window_start'] == win)
    return [rev / 100, rev / 100, rev * 0.5 / (100 * sum(util) / len(util)), len(base) * avg_cb / 100, kofi * avg_cb / 100, len(est) * avg_won * 0.4 / 100, wh / 100, 1,
            len(ren) * avg_fee / 100, nwin * avg_fee / 2 / 100, 1, fixed]


ACTIONS = ['Check the price-book lines that lost margin and raise the flat price where it sits under your target', 'Review overhead and slow-season costs with the accountant',
           'Fill idle hours: book tune-ups and follow-ups into the free days on the dispatch board', 'Review the return visits of the last month and note the reason for each',
           'Sit down with the technician whose callback rate is highest and review their last return visits', 'Follow up every open estimate older than 7 days and offer the three options',
           'Compare the supplier cost of the watched job type with its flat price and raise the price if it is under target', 'Call the account with the oldest open invoice and agree a payment date',
           'Contact the agreements due this month that are not renewed yet', 'Book the tune-up visits still due in the open window, oldest first',
           'Hold the large supplier bill to a later date, or collect open invoices before paying it', 'Build cash toward your cover target: collect old invoices and plan big purchases']
OWNERS = ['Owner', 'Accountant', 'Office manager', 'Lead HVAC tech', 'Lead HVAC tech', 'Office manager', 'Owner', 'Office manager', 'Office manager', 'Office manager', 'Owner', 'Owner']
UNITS = ['points', 'points', 'points', 'points', 'points', 'points', 'points', 'amount', 'points', 'points', 'amount', 'months']
HIGHER = [True, True, True, False, False, True, True, False, True, True, True, True]
BASIS = ['3-month average', '3-month average', '3-month average', '3-month average', 'As of today', '3-month average', 'As of today', 'As of today', 'This month', 'As of today', 'As of today', 'As of today']


def scorecard_d():
    mp = _money_points()
    return [dict(measure=key('measure', m), unit=UNITS[i], basis=BASIS[i], higher_better=HIGHER[i], money_per_point=round(mp[i], 2), action=ACTIONS[i], owner=key('actowner', OWNERS[i])) for i, m in enumerate(MEASURES)]


if __name__ == '__main__':
    for r in HIST: print(r)
    print(ST['margin_recent'], ST['callback_rate'], ST['visit_done_share'], ST['cash_now'], ST['cash_after'])
