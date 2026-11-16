"""Nonprofit suite part 2: demo rows from np_core (full generator output where small, this year's gifts, per-donor yearly totals built from all gifts)."""
import sys, os, datetime as _dt; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from np2_lists import *
import np_core as core

ST = story()
dd = to_date
Y0 = Y
TEAM = {t['name']: t for t in team}
DM_PHONE = TEAM['Mateus Oliveira']['phone']; ED_PHONE = TEAM['Grace Adeyemi']['phone']; BK_PHONE = TEAM['Fiona Gallagher']['phone']; PR_PHONE = TEAM['Kenji Watanabe']['phone']
_board = core.board_rows()
BOARD_CHAIR = [b for b in _board if b['role'] == 'Chair'][0]
FR_MEMBER = [b for b in _board if b['committee'] == 'Fundraising'][0]
VOLS = [v for v in core.volunteer_rows() if v['status'] == 'Active']
VOL = VOLS[3]
CASH = core.cash_rows()[-1]
FREE_MONEY = round(CASH['free_money']); MONTHLY_EXPENSE = round(CASH['avg_monthly_expense'])

DONORS = core.donor_rows()
DON = {d['donor_id']: d for d in DONORS}
GIFTS = core.gift_rows()
YR_OF = lambda s: int(s[:4])

# ---- per donor and year, first and second gift, last gift amount
YEARLY = {d['donor_id']: [0.0, 0.0, 0.0, 0.0] for d in DONORS}
GL = {}
for g in GIFTS:
    did = g['donor_id']
    if not did: continue
    k = Y0 - YR_OF(g['date'])
    if 0 <= k <= 3: YEARLY[did][k] += g['amount']
    GL.setdefault(did, []).append(g)
for did in YEARLY: YEARLY[did] = [round(v, 2) for v in YEARLY[did]]
LASTAMT = {did: gl[-1]['amount'] for did, gl in GL.items()}


def donors_d():
    out = []
    for d in DONORS:
        r = dict(donor_id=d['donor_id'], donor=d['donor'], type=key('dtype', d['type']), status=key('dstatus', d['status']), joined_via=key('channel', d['joined_via']) if d['joined_via'] else '',
                 first_gift=d['first_gift'], last_gift=d['last_gift'], gifts=d['gifts'], total_given=d['total_given'], last_amount=LASTAMT.get(d['donor_id'], 0.0),
                 contact=d['contact'], phone=d['phone'], contact_pref=key('pref', d['contact_pref']))
        out.append({k: v for k, v in r.items() if v not in ('', None)})
    return out


def giving_d():
    return [dict(donor_id=d['donor_id'], y0=YEARLY[d['donor_id']][0], y1=YEARLY[d['donor_id']][1], y2=YEARLY[d['donor_id']][2], y3=YEARLY[d['donor_id']][3]) for d in DONORS]


GIFTS_Y = [g for g in GIFTS if g['date'][:4] == str(Y0)]


def gifts_d():
    out = []
    for g in GIFTS_Y:
        r = dict(gift_id=g['gift_id'], date=g['date'], donor_id=g['donor_id'], donor=g['donor'], amount=g['amount'], appeal=key('appeal', g['appeal']) if g['appeal'] else '',
                 campaign=key('campaign', g['campaign']), channel=key('channel', g['channel']), fund=key('fund', g['fund'] or 'General Fund'), gift_type=key('gtype', g['gift_type']))
        out.append({k: v for k, v in r.items() if v != ''})
    return out


# ---- first-time donors (first gift in the three years) with their second gift
def _first_second():
    rows = []
    for did, gl in GL.items():
        gl = sorted(gl, key=lambda g: (g['date'], g['gift_id']))
        first = gl[0]
        second = gl[1] if len(gl) > 1 else None
        rows.append((first['date'], did, first, second))
    rows.sort()
    return rows
FS = _first_second()


def first_time_d():
    out = []
    for dt_, did, f, s in FS:
        r = dict(donor_id=did, first_gift=f['date'], first_amount=f['amount'], first_appeal=key('appeal', f['appeal']) if f['appeal'] else '', second_gift=s['date'] if s else '')
        out.append({k: v for k, v in r.items() if v != ''})
    out.sort(key=lambda r: not (r.get('first_appeal') and r.get('second_gift')))
    return out


# ---- appeal costs: this year and last year per appeal, from the real gifts so cost per dollar is believable
RAISED = {}
for g in GIFTS:
    if g['appeal']: RAISED[(g['appeal'], YR_OF(g['date']))] = RAISED.get((g['appeal'], YR_OF(g['date'])), 0.0) + g['amount']
RATIO = {'Year-end letter': (0.22, 0.25), 'Year-end email series': (0.09, 0.11), 'Giving day online push': (0.12, 0.13), 'Gala invitation': (0.62, 0.48), 'Gala paddle raise': (0.06, 0.07),
         'Fun run sponsor ask': (0.15, 0.17), 'Camp scholarship letter': (0.41, 0.30), 'School supply drive': (0.33, 0.36), 'Monthly giving page': (0.04, 0.05), 'Pantry harvest letter': (0.28, 0.31),
         'Senior holiday card': (0.70, 0.45), 'Thank-you and renewal': (0.10, 0.12)}
ACHAN = {'Year-end letter': 'Mail', 'Year-end email series': 'Online form', 'Giving day online push': 'Online form', 'Gala invitation': 'Mail', 'Gala paddle raise': 'Event', 'Fun run sponsor ask': 'Online form',
         'Camp scholarship letter': 'Mail', 'School supply drive': 'In person', 'Monthly giving page': 'Online form', 'Pantry harvest letter': 'Mail', 'Senior holiday card': 'In person', 'Thank-you and renewal': 'In person'}
PIECES = {'Year-end letter': (1400, 1350), 'Year-end email series': (5200, 5000), 'Giving day online push': (4800, 4600), 'Gala invitation': (450, 420), 'Gala paddle raise': (180, 170), 'Fun run sponsor ask': (900, 850),
          'Camp scholarship letter': (620, 600), 'School supply drive': (700, 680), 'Monthly giving page': (3200, 3000), 'Pantry harvest letter': (900, 880), 'Senior holiday card': (320, 300), 'Thank-you and renewal': (1100, 1050)}
NOTE = {'Year-end letter': 'Printing, postage and mail house', 'Year-end email series': 'Writing and sending time', 'Giving day online push': 'Page, email and prizes', 'Gala invitation': 'Printing and postage', 'Gala paddle raise': 'Auctioneer and display',
        'Fun run sponsor ask': 'Printing and sponsor pack', 'Camp scholarship letter': 'Printing and postage', 'School supply drive': 'Collection boxes and flyers', 'Monthly giving page': 'Page upkeep and thank-you cards',
        'Pantry harvest letter': 'Printing and postage', 'Senior holiday card': 'Cards and stamps', 'Thank-you and renewal': 'Calls and cards'}
REVIEW = {a: (ago(40 + 9 * i), ago(300 + 9 * i)) for i, a in enumerate(APPEALS)}


def appeal_costs_d():
    out = []; n = 0
    for yr_i, yv in ((0, Y0), (1, Y0 - 1)):
        for a in APPEALS:
            n += 1; raised = round(RAISED.get((a, yv), 0.0), 2)
            cost = max(60.0, round(RATIO[a][yr_i] * raised / 10.0) * 10.0)
            r = dict(appeal_id='AC-%02d' % n, appeal=key('appeal', a), year=yv, cost=cost, channel=key('channel', ACHAN[a]), pieces=PIECES[a][yr_i], cost_note=NOTE[a], review_on=REVIEW[a][yr_i])
            if yr_i == 1: r['raised'] = raised
            out.append(r)
    # the payroll giving share of the monthly giving page is a cost line of its own
    for yr_i, yv in ((0, Y0), (1, Y0 - 1)):
        n += 1
        out.append(dict(appeal_id='AC-%02d' % n, appeal=key('appeal', 'Monthly giving page'), year=yv, cost=(420.0, 380.0)[yr_i], channel=key('channel', 'Payroll giving'), pieces=(210, 200)[yr_i],
                        cost_note='Employer sign-up pack', review_on=REVIEW['Monthly giving page'][yr_i]))
    out.sort(key=lambda r: 'raised' not in r)
    return out


# ---- prospects
def _capband(c):
    return 'Under 5,000' if c < 5000 else '5,000 to 9,999' if c < 10000 else '10,000 to 19,999' if c < 20000 else '20,000 and over'


def prospects_d():
    out = []
    for p in core.prospect_rows():
        r = dict(prospect_id=p['prospect_id'], donor_id=p['donor_id'], donor=p['donor'], capacity=p['capacity'], capband=key('capband', _capband(p['capacity'])), stage=key('pstage', p['stage']), ask_amount=p['ask_amount'],
                 next_step=p['next_step'], next_step_date=p['next_step_date'], owner=key('owner', p['owner']), last_contact=p['last_contact'], expected_close=p['expected_close'])
        out.append({k: v for k, v in r.items() if v != ''})
    out.sort(key=lambda r: r['stage'] == 'closed')
    return out


# ---- bands, conversion rows, simple rank rows
def bands_d(): return [dict(band=key('band', b), lower=lo, upper=up) for b, (lo, up) in zip(BANDS, BAND_LIMITS)]
def conversion_d(): return [dict(appeal=key('appeal', a)) for a in APPEALS]
def ranks_d(n): return [dict(rank=i) for i in range(1, n + 1)]
def donor_types_d(): return [dict(type=key('dtype', t)) for t in DONOR_TYPES]
def pipeline_d(): return [dict(stage=key('pstage', s)) for s in PIPELINE_STAGES]
def source_d(): return [dict(channel=key('channel', c)) for c in CHANNELS]
def results_d(): return [dict(appeal=key('appeal', a)) for a in APPEALS]


def ret_detail_d():
    return [dict(year=key('yr2', y), group=key('dgroup', g), review_on=ago(20 + 7 * (i % 6)) if y == 'This year' else ago(380 + 7 * (i % 6))) for y in ('This year', 'Last year') for i, g in enumerate(DGROUP)]


def _grp(d): return d['type']
def three_year_d():
    out = []; n = 0
    for yk, y in enumerate(YR):
        yv = Y0 - (2 - yk)
        for g in DGROUP:
            n += 1
            cnt = sum(1 for gg in GIFTS if gg['donor_id'] and YR_OF(gg['date']) == yv and (g == 'All donors' or DON[gg['donor_id']]['type'] == g))
            out.append(dict(row_id='TY-%02d' % n, year=key('yr', y), group=key('dgroup', g), gifts=cnt, review_on=ago(15 + 4 * n) if y == 'This year' else ago(370 + 4 * n)))
    return out


SCENARIOS = [('Biggest donor leaves', 1, 1.0, 0.0), ('Top 3 donors leave', 3, 1.0, 0.0), ('Top 5 donors leave', 5, 1.0, 0.0), ('Top 10 donors leave', 10, 1.0, 0.0), ('Biggest donor gives half', 1, 0.5, 0.0),
             ('Top 5 donors give half', 5, 0.5, 0.0), ('Top 10 donors give 20 percent less', 10, 0.2, 0.0), ('Lapsing major donors do not return', 0, 0.0, 1.0),
             ('Lapsing major donors return, biggest donor leaves', 1, 1.0, 0.0), ('Lapsing major donors do not return, biggest leaves', 1, 1.0, 1.0), ('Half the lapsing major donors return', 0, 0.0, 0.5),
             ('Top 3 give half, lapsing major donors do not return', 3, 0.5, 1.0)]
def scenarios_d(): return [dict(scenario=s, top_n=n, lost_pct=p, lapsed_pct=q, review_on=ago(30 + 11 * i)) for i, (s, n, p, q) in enumerate(SCENARIOS)]


def upgrade_d():
    return [dict(rank=i, ask_on=ahead(7 + 3 * ((i - 1) % 30)), **({'last_asked': ago(60 + 5 * i)} if i % 7 == 3 else {})) for i in range(1, 61)]


def lapsed_d():
    return [dict(rank=i, caller=key('owner', ['Mateus Oliveira', 'Grace Adeyemi', 'Mateus Oliveira', 'Sunita Rao'][(i - 1) % 4]), contact_by=ahead(2 + ((i - 1) // 6))) for i in range(1, 121)]
