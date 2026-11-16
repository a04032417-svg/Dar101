"""Nonprofit suite part 4: demo rows from np_core (full generator output for the totals, row-level tables built from it)."""
import sys, os, random, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from np4_lists import *
import datetime as _dt

dd = to_date
ST = story()
T0 = TODAY
TS = iso(T0)
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
def d_add(s, n): return iso(dd(s) + _dt.timedelta(days=n))
def m1(s): return s[:8] + '01'

TEAM = {t['name']: t for t in team}
DEV_PHONE = TEAM[DEV_MANAGER]['phone']; EXEC_PHONE = TEAM[OWNER]['phone']
def contact_phone(role): return [t for t in team if t['role'] == role][0]['phone']
VENUE_PHONE = contact_phone('Event venue'); CATERER_PHONE = contact_phone('Caterer'); PRINTER_PHONE = contact_phone('Printer and mail house')
BOOK_PHONE = contact_phone('Bookkeeper'); COORD_PHONE = contact_phone('Volunteer coordinator')
BOARD = board_rows()
CHAIR = [b for b in BOARD if b['committee'] == 'Fundraising'][0]
CHAIR_PHONE = CHAIR['phone']; CHAIR_NAME = CHAIR['name']
DON = {d['donor_id']: d for d in donor_rows()}

# ---------------------------------------------------------------- events
CPD = {}   # (campaign, year) -> campaign_id
for c_ in CP_SRC: CPD[(c_['campaign'], c_['year'])] = c_['campaign_id']
EVR = [dict(e) for e in EV_SRC]
EVR.append(dict(event_id='EV-12', event='Fun Run', kind='Fun run', date='2027-10-23', year=2027, venue='Riverside park', budget_cost=9800.0, goal=25500.0, expected_attendees=285, status='Planned', campaign='Fun Run'))
for e in EVR: e['name'] = ev_name(e)
EVN = {e['event_id']: e['name'] for e in EVR}
EVD = {e['event_id']: e for e in EVR}
DOORS = {'Gala': '18:00', 'Fun run': '08:30', 'Giving day': '09:00'}
EV_ORDER = ['EV-11', 'EV-12', 'EV-10', 'EV-09', 'EV-08', 'EV-07', 'EV-06', 'EV-05', 'EV-04', 'EV-03', 'EV-02', 'EV-01']


def events_d():
    out = []
    for i in EV_ORDER:
        e = EVD[i]
        out.append(nb(dict(event_id=i, event=e['name'], kind=key('ekind', e['kind']), date=e['date'], year=e['year'], venue=e['venue'], doors=DOORS[e['kind']], budget_cost=e['budget_cost'], goal=e['goal'],
                           expected=e['expected_attendees'], status=key('estatus', e['status']), campaign=key('campaign', e['campaign']), campaign_id=CPD.get((e['campaign'], e['year']), ''))))
    return out


# ---------------------------------------------------------------- tickets and ticket types
TKF = ticket_rows()
def tickets_d():
    rows = sorted(TKF, key=lambda t: (t['sold_on'], t['ticket_id']), reverse=True)
    first = [t for t in rows if t['event_id'] == ST['event'] and t['ticket_type'] == 'Table of ten'][:1]
    rows = first + [t for t in rows if t not in first]
    return [dict(ticket_id=t['ticket_id'], event=EVN[t['event_id']], sold_on=t['sold_on'], month=t['month'], buyer=t['buyer'], phone=DON[t['donor_id']]['phone'], ticket_type=key('ticket', t['ticket_type']),
                 quantity=t['qty'], price_each=t['price_each'], benefit_each=t['benefit_each'], seats=t['seats']) for t in rows]


def ticket_types_d():
    last = {}
    for t in TKF: last[t['ticket_type']] = t
    return [dict(ticket=key('ticket', k), price=last[k]['price_each'], benefit_value=last[k]['benefit_each']) for k in TICKET_TYPES]


# ---------------------------------------------------------------- sponsors
SPF = sponsor_rows()
def sponsors_d():
    rows = []
    by_ev9 = [s for s in SPF if s['event_id'] == 'EV-09' and s['status'] == 'Paid']
    tweak = {s['sponsor_id'] for s in by_ev9[:4]}
    for s in SPF:
        s = dict(s)
        if s['promised_on'] > TS: s['promised_on'] = d_add(TS, -3 - (hash(s['sponsor_id']) % 9))
        if s['sponsor_id'] in tweak:
            s['benefits_delivered'] = max(0, s['benefits_owed'] - 1); s['next_step'] = 'Deliver the last benefits'
        s['contact'] = DON[s['donor_id']]['contact']; s['phone'] = DON[s['donor_id']]['phone']
        rows.append(s)
    rows.sort(key=lambda s: (s['promised_on'], s['sponsor_id']), reverse=True)
    return [nb(dict(sponsor_id=s['sponsor_id'], event=EVN[s['event_id']], sponsor=s['sponsor'], contact=s['contact'], phone=s['phone'], level=key('level', s['level']), promised=s['promised'], received=s['received'],
                    promised_on=s['promised_on'], received_on=s['received_on'], status=key('sstatus', s['status']), benefits_owed=s['benefits_owed'], benefits_delivered=s['benefits_delivered'],
                    next_step=key('snext', s['next_step']), next_step_date=s['next_step_date'])) for s in rows]


LEVEL_PRICE = {'Gala': {'Presenting': 15600.0, 'Gold': 8300.0, 'Silver': 4150.0, 'Community': 1200.0}, 'Fun run': {'Presenting': 5000.0, 'Gold': 2000.0, 'Silver': 1000.0, 'Community': 400.0},
               'Giving day': {'Presenting': 5000.0, 'Gold': 2500.0, 'Silver': 1500.0, 'Community': 500.0}}
LEVEL_BEN = {'Gala': {'Presenting': 8, 'Gold': 5, 'Silver': 3, 'Community': 2}, 'Fun run': {'Presenting': 5, 'Gold': 3, 'Silver': 2, 'Community': 1}, 'Giving day': {'Presenting': 4, 'Gold': 3, 'Silver': 2, 'Community': 1}}
def sponsor_levels_d():
    return [dict(level=key('level', lv), kind=key('ekind', k), price=LEVEL_PRICE[k][lv], benefits_count=LEVEL_BEN[k][lv]) for k in ('Gala', 'Fun run', 'Giving day') for lv in SPONSOR_LEVELS]


# ---------------------------------------------------------------- auction
AUF = auction_rows()
def auction_d():
    rows = []
    for a in AUF:
        a = dict(a)
        if a['item_id'] in ('AU-076', 'AU-082'): a['fair_value'] = ''          # two items of the planned gala not valued yet
        a['donor_phone'] = DON[a['donor_id']]['phone'] if a['donor_id'] in DON else ''
        a['buyer'] = DON[a['buyer_id']]['donor'] if a['buyer_id'] in DON else ''
        a['buyer_phone'] = DON[a['buyer_id']]['phone'] if a['buyer_id'] in DON else ''
        rows.append(a)
    rows.sort(key=lambda a: ({ST['event']: 0, 'EV-11': 1}.get(a['event_id'], 2), a['status'] != 'Sold', a['item_id']))
    return [nb(dict(item_id=a['item_id'], event=EVN[a['event_id']], item=a['item'], donated_by=a['donated_by'], donor_phone=a['donor_phone'], fair_value=a['fair_value'], starting_bid=a['starting_bid'],
                    sold_price=a['sold_price'] if a['status'] == 'Sold' else '', buyer=a['buyer'], buyer_phone=a['buyer_phone'], status=key('auction', a['status']), received_on=a['received_on'])) for a in rows]


# ---------------------------------------------------------------- campaigns and event gifts
def campaign_of(name, date):
    for c_ in CP_SRC:
        if c_['campaign'] == name and c_['start_date'] <= date <= c_['end_date']: return c_
    return None
EVENT_CAMP = {'Spring Gala', 'Giving Day', 'Fun Run'}
APPEAL_CAMP = ['Year-End Appeal', 'Giving Day', 'Spring Gala', 'Fun Run', 'Summer Camp Appeal', 'Back-to-School Drive']
GF = gift_rows()
GIFTS = []
for g in GF:
    if g['campaign'] in APPEAL_CAMP:
        c_ = campaign_of(g['campaign'], g['date'])
        if c_: GIFTS.append((g, c_))
_ev_of = {}
for e in EVR: _ev_of[(e['campaign'], e['year'])] = e['name']


def event_gifts_d():
    rows = sorted(GIFTS, key=lambda x: (x[0]['date'], x[0]['gift_id']), reverse=True)
    out = []
    for g, c_ in rows:
        d = DON[g['donor_id']]
        new = c_['start_date'] <= d['first_gift'] <= c_['end_date']
        out.append(nb(dict(gift_id=g['gift_id'], date=g['date'], month=g['month'], donor_id=g['donor_id'], donor=g['donor'], phone=d['phone'], amount=g['amount'], event=_ev_of.get((c_['campaign'], c_['year'])) if c_['campaign'] in EVENT_CAMP else '',
                           campaign_id=c_['campaign_id'], campaign=key('campaign', g['campaign']), appeal=key('appeal', g['appeal']) if g['appeal'] else '', gift_type=key('gtype', g['gift_type']), new_donor=bool(new))))
    first = [i for i, r in enumerate(out) if r.get('event') and r['campaign_id'] == CPD[('Spring Gala', 2026)]][:1]
    if first: out.insert(0, out.pop(first[0]))
    return out


def open_pledges():
    pl = {x['pledge_id']: x for x in pledge_rows()}
    res = {}
    for x in pledge_payment_rows():
        if x['status'] in ('Due', 'Overdue'):
            p = pl[x['pledge_id']]; yr = int(p['pledged_on'][:4]); cid = CPD.get((p['campaign'], yr))
            if cid: res[cid] = res.get(cid, 0.0) + x['amount_due']
    return res
OPENP = open_pledges()


def campaigns_d():
    out = []
    for c_ in CP_SRC:
        nm = c_['campaign']; cid = c_['campaign_id']
        row = dict(campaign_id=cid, campaign=key('campaign', nm), year=c_['year'], start_date=c_['start_date'], end_date=c_['end_date'], goal=c_['goal'])
        if OPENP.get(cid): row['pledged_open'] = round(OPENP[cid], 2)
        if cid == 'CP-17': row['main'] = True
        if nm in ('Monthly Giving', 'General giving'):
            gs = [g for g in GF if g['campaign'] == nm and g['date'][:4] == str(c_['year'])]
            donors = {g['donor_id'] for g in gs if g['donor_id'] in DON}
            row['other_raised'] = round(sum(g['amount'] for g in gs), 2); row['other_donors'] = len(donors)
            row['other_new'] = sum(1 for d_ in donors if DON[d_]['first_gift'][:4] == str(c_['year']))
            if nm == 'Monthly Giving': row['other_cost'] = round(row['other_raised'] * CARD_FEE_PCT, 2)
        out.append(row)
    return out


PROG_IDS = ['CP-17', 'CP-18', 'CP-19', 'CP-20', 'CP-21', 'CP-22', 'CP-23', 'CP-24', 'CP-09', 'CP-10', 'CP-11', 'CP-12']
def campaign_progress_d(): return [dict(campaign_id=i) for i in PROG_IDS]


WEEK_IDS = ['CP-17', 'CP-09', 'CP-01', 'CP-22', 'CP-14', 'CP-06', 'CP-21', 'CP-13', 'CP-05', 'CP-18', 'CP-10', 'CP-02']
def campaign_weeks_d():
    out = []
    byid = {c_['campaign_id']: c_ for c_ in CP_SRC}
    for i in WEEK_IDS:
        c_ = byid[i]; n = math.ceil(((dd(c_['end_date']) - dd(c_['start_date'])).days + 1) / 7)
        for w in range(1, n + 1): out.append(dict(campaign_id=i, week=key('wk', 'Week %d' % w)))
    return out


def campaign_compare_d(): return [dict(campaign_id=c_['campaign_id'], campaign=key('campaign', c_['campaign'])) for c_ in sorted(CP_SRC, key=lambda c_: (-c_['year'], c_['campaign_id']))]
def method_rank_d(): return [dict(campaign=key('campaign', c_)) for c_ in CAMPAIGNS]


# ---------------------------------------------------------------- event costs
CATMAP = {'Online ads': 'Online ads and fees', 'Online giving fees': 'Online ads and fees', 'Phone bank refreshments': 'Catering and drinks', 'Insurance and permits': 'Insurance and permits', 'Auction and printing': 'Printing and mail',
          'Venue hire': 'Venue and hall', 'Venue deposit': 'Venue and hall', 'Decor and flowers': 'Decor and flowers', 'Entertainment': 'Entertainment', 'Stage, sound and lighting': 'Stage, sound and lighting',
          'Sound and staging': 'Stage, sound and lighting', 'Dinner and drinks': 'Catering and drinks', 'Refreshments': 'Catering and drinks', 'Printing and signs': 'Printing and mail',
          'Shirts and medals': 'Merchandise and route', 'Route and marshals': 'Merchandise and route'}
EXF = expense_rows()
def cost_lines():
    out = []
    for x in EXF:
        if x['event_id']:
            e = EVD[x['event_id']]; cat = CATMAP[x['note']]; a = x['amount']
            cid = CPD.get((e['campaign'], e['year']), '')
            if a >= 12000: parts = [(0.3, -30), (0.3, -14), (0.4, 0)]
            elif a >= 3000: parts = [(0.4, -21), (0.6, 0)]
            else: parts = [(1.0, 0)]
            acc = 0.0
            for j, (sh, off) in enumerate(parts):
                amt = round(a * sh, 2) if j < len(parts) - 1 else round(a - acc, 2)
                acc += amt
                dt_ = d_add(x['date'], off)
                if dt_ > TS: dt_ = x['date']
                eid = x['expense_id'] if j == len(parts) - 1 else x['expense_id'] + 'ab'[j]
                out.append(dict(expense_id=eid, date=dt_, event=e['name'], campaign_id=cid, category=cat, vendor=x['vendor'], amount=amt))
        elif x['campaign'] and x['campaign'] in APPEAL_CAMP + ['General giving']:
            c_ = CPD.get((x['campaign'], int(x['date'][:4])))
            out.append(dict(expense_id=x['expense_id'], date=x['date'], event='', campaign_id=c_ or '', category='Printing and mail', vendor=x['vendor'], amount=x['amount']))
    return out
COSTL = cost_lines()
def event_costs_d():
    rows = sorted(COSTL, key=lambda r: (r['event'] == '', r['date'], r['expense_id']), reverse=False)
    ev = sorted([r for r in COSTL if r['event']], key=lambda r: (r['date'], r['expense_id']), reverse=True)
    top = [r for r in ev if r['event'] == EVN[ST['event']] and r['category'] == 'Catering and drinks'][:1]
    ev = top + [r for r in ev if r not in top]
    cp = sorted([r for r in COSTL if not r['event']], key=lambda r: (r['date'], r['expense_id']), reverse=True)
    return [nb(dict(expense_id=r['expense_id'], date=r['date'], event=r['event'], campaign_id=r['campaign_id'], category=key('ecat', r['category']), vendor=r['vendor'], amount=r['amount'])) for r in ev + cp]


# ---------------------------------------------------------------- event hours
VOLS = [v for v in volunteer_rows() if v['role'] == 'Event helper' and v['status'] == 'Active']
SHD = {}
for s in shift_rows():
    if s['role'] == 'Event helper' and s['status'] == 'Worked': SHD[s['date']] = SHD.get(s['date'], 0.0) + s['hours']
AREAS = {'Gala': EWORK, 'Fun run': ['Planning and tickets', 'Sponsors and invitations', 'Set-up and decor', 'Guest check-in', 'Event floor and service', 'Clear-up'],
         'Giving day': ['Planning and tickets', 'Sponsors and invitations', 'Event floor and service', 'Thank-yous and report']}
OFF = {'Planning and tickets': -42, 'Sponsors and invitations': -35, 'Auction and printing': -21, 'Set-up and decor': -1, 'Guest check-in': 0, 'Event floor and service': 0, 'Clear-up': 1, 'Thank-yous and report': 10}
STAFF_H = {'Planning and tickets': 52, 'Sponsors and invitations': 64, 'Auction and printing': 38, 'Set-up and decor': 30, 'Guest check-in': 14, 'Event floor and service': 40, 'Clear-up': 12, 'Thank-yous and report': 24}
VOL_SHARE = {'Planning and tickets': 0.04, 'Sponsors and invitations': 0.02, 'Auction and printing': 0.06, 'Set-up and decor': 0.22, 'Guest check-in': 0.16, 'Event floor and service': 0.34, 'Clear-up': 0.14, 'Thank-yous and report': 0.02}
STAFF_LEAD = {'Planning and tickets': DEV_MANAGER, 'Sponsors and invitations': DEV_MANAGER, 'Thank-yous and report': OWNER}
KIND_VH = {'Gala': 120.0, 'Fun run': 135.0, 'Giving day': 21.0}
def hours_d():
    out = []; rnd = random.Random(404); k = 0; vi = 0
    for i in ['EV-11', 'EV-10', 'EV-09', 'EV-08', 'EV-07', 'EV-06', 'EV-05', 'EV-04', 'EV-03', 'EV-02', 'EV-01']:
        e = EVD[i]; planned = e['status'] == 'Planned'; areas = AREAS[e['kind']]
        total_v = SHD.get(e['date'], KIND_VH[e['kind']] * (0.85 if e['year'] == 2024 else 1.0))
        for a in areas:
            k += 1
            if a in STAFF_LEAD: lead = STAFF_LEAD[a]; ph = TEAM[lead]['phone']
            else:
                v = VOLS[vi % len(VOLS)]; vi += 1; lead = v['name']; ph = v['phone']
            sh = round(STAFF_H[a] * (0.55 if e['kind'] == 'Giving day' else 0.8 if e['kind'] == 'Fun run' else 1.0) * rnd.uniform(0.9, 1.1) * (1.15 if i == ST['event'] else 1.0), 1)
            vh = round(max(2.0, total_v * VOL_SHARE[a]), 1); need = max(1, math.ceil(vh / 3.0)); signed = need if not planned else max(0, need - 1 - (k % 3))
            if planned: sh = 0.0; vh = 0.0
            row = dict(hours_id='EH-%03d' % k, event=e['name'], area=key('ework', a), lead=lead, lead_phone=ph, work_date=d_add(e['date'], OFF[a]), staff_hours=sh, volunteer_hours=vh, volunteers_needed=need, volunteers_signed=signed)
            if not planned: row['volunteer_hours'] = vh
            out.append(row)
    for r in out:
        if r['work_date'] > TS and EVD[[x for x in EVD if EVN[x] == r['event']][0]]['status'] != 'Planned': r['work_date'] = TS
    return out


# ---------------------------------------------------------------- renewal, benefits, scenarios, years, appeals
def sponsor_renewal_d():
    rows = [s for s in SPF if s['event_id'] in ('EV-06', 'EV-07', 'EV-08', 'EV-09') and s['status'] == 'Paid']
    rows.sort(key=lambda s: (-s['received'], s['sponsor_id']))
    return [dict(sponsor_id=s['sponsor_id']) for s in rows]


def benefit_tracker_d():
    rows = [s for s in SPF if s['event_id'] in ('EV-05', 'EV-06', 'EV-07', 'EV-08', 'EV-09', 'EV-10', 'EV-11') and s['status'] != 'Declined']
    s9 = [s for s in rows if s['event_id'] == 'EV-09' and s['status'] == 'Paid'][:4]
    rows.sort(key=lambda s: (s not in s9, s['event_id'] != 'EV-11', s['sponsor_id']))
    return [dict(sponsor_id=s['sponsor_id']) for s in rows]


def scenarios_d():
    f = {'Ticket money': (0.85, 1.0, 1.15), 'Sponsor money': (0.8, 1.0, 1.1), 'Auction income': (0.65, 1.0, 1.25), 'Gifts on the night and appeal': (0.85, 1.0, 1.1)}
    out = []
    for ln in LINES[:5] + ECAT + ['Total costs', 'Net raised', 'Cost per dollar']:
        row = dict(line=key('lines', ln))
        if ln in f: row.update(low_f=f[ln][0], exp_f=f[ln][1], high_f=f[ln][2])
        elif ln in ECAT: row.update(low_f=1.05, exp_f=1.03, high_f=1.03)
        out.append(row)
    return out


GALA_LINES = ['Ticket money', 'Sponsor money', 'Auction income', 'Gifts on the night and appeal', 'Total raised', 'Total costs', 'Net raised', 'Cost per dollar', 'Guests', 'Net per guest', 'Staff hours', 'Volunteer hours']
def gala_d(): return [dict(metric=key('lines', m)) for m in GALA_LINES]
CH_MAP = {'Year-end letter': 'Mail', 'Year-end email series': 'Online form', 'Giving day online push': 'Online form', 'Gala invitation': 'Mail', 'Gala paddle raise': 'Event', 'Fun run sponsor ask': 'In person',
          'Camp scholarship letter': 'Mail', 'School supply drive': 'In person', 'Monthly giving page': 'Online form', 'Pantry harvest letter': 'Mail', 'Senior holiday card': 'Mail', 'Thank-you and renewal': 'Mail'}
def appeals_d(): return [dict(appeal=key('appeal', a['appeal']), campaign=key('campaign', a['campaign']), channel=key('channel', CH_MAP[a['appeal']])) for a in appeals]


# ---------------------------------------------------------------- python-side totals (QA and tool defaults)
def ev_totals(i):
    nm = EVN[i]
    tk = sum(t['amount'] for t in TKF if t['event_id'] == i); seats = sum(t['seats'] for t in TKF if t['event_id'] == i)
    sp = sum(s['received'] for s in SPF if s['event_id'] == i); spp = sum(s['promised'] for s in SPF if s['event_id'] == i and s['status'] != 'Declined')
    au = sum(a['sold_price'] for a in AUF if a['event_id'] == i)
    gi = sum(g['amount'] for g, c_ in GIFTS if c_['campaign'] in EVENT_CAMP and _ev_of.get((c_['campaign'], c_['year'])) == nm)
    co = sum(r['amount'] for r in COSTL if r['event'] == nm)
    raised = tk + sp + au + gi
    return dict(tickets=tk, seats=seats, sponsors=sp, promised=spp, auction=au, gifts=gi, raised=raised, cost=co, net=raised - co, cpd=(co / raised if raised else 0))
TOT = {e['event_id']: ev_totals(e['event_id']) for e in EVR}

if __name__ == '__main__':
    print('events', len(events_d()), 'tickets', len(tickets_d()), 'sponsors', len(sponsors_d()), 'auction', len(auction_d()), 'gifts', len(event_gifts_d()), 'costs', len(event_costs_d()), 'hours', len(hours_d()),
          'campaigns', len(campaigns_d()), 'weeks', len(campaign_weeks_d()), 'renewal', len(sponsor_renewal_d()), 'benefit', len(benefit_tracker_d()))
    for k, v in TOT.items(): print(k, EVN[k], {a: round(b, 2) for a, b in v.items()})
