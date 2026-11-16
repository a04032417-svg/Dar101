"""Nonprofit suite part 7: demo rows from np_core (board, meetings, attendance, declarations, obligations, giving)."""
import sys, os, collections; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from np7_lists import *
import datetime as _dt

dd = to_date
T0 = TODAY
TS = iso(T0)
ST = story()
def nb(d): return {k: v for k, v in d.items() if v not in ('', None)}
TEAMID = {t['staff_id']: t for t in team}
ED_PHONE = TEAMID['NP-01']['phone']; ACC_PHONE = TEAMID['NP-09']['phone']; BROKER_PHONE = TEAMID['NP-11']['phone']
VOL = [v for v in volunteer_rows() if v['status'] == 'Active'][3]; VOL_PHONE = VOL['phone']

def yr_key(d, four=True):
    k = dd(d).year - T0.year
    lab = {-2: 'Two years ago', -1: 'Last year', 0: 'This year', 1: 'Next year'}[k]
    return key('yr' if four else 'yr3', lab)

# ---------------------------------------------------------------- board (11 serving members plus one former member, so the roster has 12 rows)
BRD = [dict(b) for b in board_rows()]
_don = donor_rows()
_DID = {d['donor_id']: d for d in _don}
_former_pool = [d for d in _don if d['type'] == 'Individual' and d['status'] == 'Active' and d['gifts'] >= 4]
FD = _former_pool[5]
FORMER = dict(member_id='BM-12', name=FD['donor'], role='Member', committee='Fundraising', term_start=ago(1190), term_end=ago(130), terms_served=2, skill='Marketing', skill2='Community links',
              donor_id=FD['donor_id'], phone=FD['phone'], email=FD['email'])
BRD_ALL = BRD + [FORMER]
BN = {b['member_id']: b for b in BRD_ALL}
NAME2ID = {b['name']: b['member_id'] for b in BRD_ALL}
def bkey(name): return key('bmember', name)
CHAIR = BRD[0]; TREAS = BRD[1]; VICE = BRD[2]; SECR = BRD[3]
CHAIR_PHONE = CHAIR['phone']; TREAS_PHONE = TREAS['phone']; VICE_PHONE = VICE['phone']; SECR_PHONE = SECR['phone']; GOV_CHAIR_PHONE = CHAIR['phone']


def board_d():
    return [dict(member_id=b['member_id'], name=b['name'], role=key('brole', b['role']), committee=key('committee', b['committee']), term_start=b['term_start'], term_end=b['term_end'],
                 terms_served=b['terms_served'], skill=key('skill', b['skill']), skill2=key('skill', b['skill2']), donor_id=b['donor_id'], phone=b['phone'], email=b['email']) for b in BRD_ALL]


def roles_d():
    return [dict(role=key('brole', r), term_years=3, max_terms=(2 if r in ('Chair', 'Vice-chair') else 3)) for r in BOARD_ROLES]


def committees_d():
    rows = [('Finance', 'Michael Brandt', 'Four times a year, the second Thursday of January, April, July and October'), ('Fundraising', 'Sunita Rao', 'Four times a year, the second Thursday of February, May, September and November'),
            ('Governance', 'Dr. Ngozi Eze', 'Twice a year, the second Wednesday of March and September'), ('Executive', 'Dr. Ngozi Eze', 'When needed, between board meetings, with the four officers'),
            ('Nominating', 'Carlos Mendoza', 'Twice a year, before the terms-ending review and before the yearly meeting')]
    return [dict(committee=a, chair=bkey(b), meets=c_) for a, b, c_ in rows]


SKILL_NEED = {'Finance': 2, 'Fundraising': 2, 'Law and policy': 2, 'Marketing': 1, 'Community links': 2, 'Education': 2, 'Health and care': 1, 'Technology': 1}
SKILL_NOTE = {'Finance': 'Reads the accounts and the budget, chairs the finance committee', 'Fundraising': 'Opens doors to donors and funders, joins asks',
              'Law and policy': 'Reads policies and agreements, checks your local rules', 'Marketing': 'Helps with the story, the website and the annual report',
              'Community links': 'Knows the neighbourhood and the people the programs serve', 'Education': 'Guides the learning and youth programs',
              'Health and care': 'Guides the meals, visits and food programs', 'Technology': 'Advises on data, devices and online giving pages'}
def skills_d(): return [dict(skill=key('skill', s), needed=SKILL_NEED[s], note=SKILL_NOTE[s]) for s in SKILLS]
def skills_matrix_d():
    return [dict(row_id='SM-%02d' % (i * 3 + j + 1), skill=key('skill', s), when=key('when', w)) for i, s in enumerate(SKILLS) for j, w in enumerate(WHEN)]


def terms_ending_d():
    serving = sorted([b for b in BRD], key=lambda b: b['term_end'])
    def ends(b):
        k = dd(b['term_end']).year - T0.year
        return key('yend', YEND[0] if k <= 0 else YEND[1] if k == 1 else YEND[2] if k == 2 else YEND[3])
    return [dict(member=b['name'], ends_in=ends(b)) for b in serving + [FORMER]]


SEAT_ROLES = ['Chair', 'Vice-chair', 'Treasurer', 'Secretary'] + ['Member'] * 8
def seats_d():
    rows = []
    for i, r in enumerate(SEAT_ROLES):
        d = dict(seat_id='SE-%02d' % (i + 1), seat=key('brole', r))
        if i < len(BRD): d['member'] = bkey(BRD[i]['name'])
        else: d['call_on'] = ahead(9)
        rows.append(d)
    return rows


# ---------------------------------------------------------------- meetings and attendance (attendance of the two members closest to the set share is lifted so exactly two stay under it)
MT = [dict(m) for m in meeting_rows()]
ATT = [dict(a) for a in attendance_rows()]
def _share(mid, yr):
    rows = [a for a in ATT if a['member_id'] == mid and a['date'][:4] == str(yr)]
    return (sum(1 for a in rows if a['status'] == 'Present') / len(rows)) if rows else None
for mid, need in (('BM-06', 0.76), ('BM-08', 0.76)):
    rows = sorted([a for a in ATT if a['member_id'] == mid and a['date'][:4] == str(T0.year) and a['kind'] == 'Board' and a['status'] != 'Present'], key=lambda a: a['date'])
    for a in rows:
        if _share(mid, T0.year) >= need: break
        if a['date'] >= iso(T0 - _dt.timedelta(days=60)): continue
        a['status'] = 'Present'
_att_by = collections.defaultdict(list)
for a in ATT: _att_by[a['meeting_id']].append(a)
for m in MT:
    rows = _att_by.get(m['meeting_id'], [])
    if rows:
        m['present'] = sum(1 for a in rows if a['status'] == 'Present'); m['quorum_met'] = m['present'] >= m['expected'] // 2 + 1
TIMES = {'Board': ['18:30', '18:30', '18:00', '19:00'], 'Finance': ['18:00', '17:30'], 'Fundraising': ['18:15', '18:30'], 'Governance': ['18:45', '18:00']}
for i, m in enumerate(MT):
    m['time'] = TIMES[m['kind']][i % len(TIMES[m['kind']])]
    if m['kind'] == 'Board' and m['date'][5:7] == '12': m['time'] = '18:00'


for m in MT:
    if m['meeting_id'] == 'BMT-060': m['minutes_ready'] = False


def meetings_d():
    return [dict(meeting_id=m['meeting_id'], date=m['date'], start_time=m['time'], kind=key('mkind', m['kind']), period=yr_key(m['date']), expected=m['expected'], present=m['present'],
                 quorum_met=bool(m['quorum_met']), minutes_ready=bool(m['minutes_ready']), status=key('mstatus', m['status'])) for m in MT]


def attendance_d():
    return [dict(att_id=a['att_id'], meeting_id=a['meeting_id'], date=a['date'], kind=key('mkind', a['kind']), member_id=a['member_id'], member=bkey(a['member']), status=key('attend', a['status'])) for a in ATT]


def attendance_member_d():
    rows = []; n = 0
    for per in YR3:
        for b in BRD:
            n += 1; rows.append(dict(row_id='AM-%02d' % n, member=bkey(b['name']), period=key('yr3', per)))
    rows.sort(key=lambda r: (r['row_id'] != 'x'))
    return rows


# ---------------------------------------------------------------- giving (from the gift log: counts and totals per member and year)
_GIFTS = collections.defaultdict(lambda: [0, 0.0])
_ids = {b['donor_id'] for b in BRD}
for g in gift_rows():
    if g['donor_id'] in _ids:
        _GIFTS[(g['donor_id'], int(g['date'][:4]))][0] += 1; _GIFTS[(g['donor_id'], int(g['date'][:4]))][1] += g['amount']
RAISED = {'This year': [600, 1500, 2400, 0, 300, 450, 900, 1200, 0, 500, 0], 'Last year': [1200, 1800, 2000, 500, 0, 250, 0, 600, 0, 900, 150], 'Two years ago': [800, 1000, 1500, 0, 400, 0, 0, 0, 350, 0, 0]}
def board_giving_d():
    rows = []; n = 0
    for per, off in (('This year', 0), ('Last year', 1), ('Two years ago', 2)):
        for b in BRD:
            n += 1; gg = _GIFTS.get((b['donor_id'], T0.year - off), [0, 0.0])
            rows.append(dict(row_id='BG-%02d' % n, member=bkey(b['name']), period=key('yr3', per), gifts=gg[0], total=round(gg[1], 2)))
    return rows
def give_or_get_d():
    rows = []; n = 0
    for per in ('This year', 'Last year'):
        for i, b in enumerate(BRD):
            n += 1; rows.append(dict(row_id='GG-%02d' % n, member=bkey(b['name']), period=key('yr2', per), raised=float(RAISED[per][i])))
    return rows
def board_share_d():
    rows = []; n = 0
    for per in YR3:
        for g in BGROUP:
            n += 1; rows.append(dict(row_id='BS-%02d' % n, period=key('yr3', per), group=key('bgroup', g)))
    return rows


# ---------------------------------------------------------------- declarations (one new member has a declaration that is due soon, so the demo shows all three statuses)
DEC = [dict(d) for d in declaration_rows()]
for d in DEC:
    if d['member_id'] == 'BM-11' and d['year'] == T0.year and d['status'] != 'Filed':
        d['status'] = 'Due'; d['due_date'] = ahead(21)
def declarations_d():
    rows = sorted(DEC, key=lambda d: (d['year'] != T0.year, d['year'], d['member_id']))
    out = []
    for d in rows:
        out.append(nb(dict(decl_id=d['decl_id'], member_id=d['member_id'], member=bkey(d['member']), year=key('yr3', {-2: 'Two years ago', -1: 'Last year', 0: 'This year'}[d['year'] - T0.year]), due_date=d['due_date'],
                           filed_on=d['filed_on'], items_declared=d['items_declared'], status=key('dclstatus', d['status']))))
    return out
def decl_status_d():
    rows = []; n = 0
    for per in YR3:
        for b in BRD:
            n += 1; rows.append(dict(row_id='DS-%02d' % n, member=bkey(b['name']), year=key('yr3', per)))
    return rows


# ---------------------------------------------------------------- obligations
OBL = [dict(o) for o in obligation_rows()]
OBL += [dict(ob_id='OB-041', item='Final report to the community foundation', kind='Funder report', due_date=ago(12), owner='Fundraising', done_on=ago(14), status='Done'),
        dict(ob_id='OB-042', item='Interim report to the Learning Lab funder', kind='Funder report', due_date=ahead(10), owner='Fundraising', done_on='', status='Upcoming')]
def obligations_d():
    return [nb(dict(ob_id=o['ob_id'], item=o['item'], kind=key('obkind', o['kind']), due_date=o['due_date'], owner=key('committee', o['owner']), done_on=o['done_on'], status=key('obstatus', o['status']))) for o in OBL]
CAL_FROM = iso(T0 - _dt.timedelta(days=200))
def ob_calendar_d(): return [dict(ob_id=o['ob_id']) for o in OBL if o['due_date'] >= CAL_FROM]
OB_REPEAT = {'Policy review': 12, 'Insurance renewal': 12, 'Yearly return': 12, 'Annual report': 12, 'Accounts review': 12, 'Funder report': 6, 'Board training': 12, 'Safety check': 12}
OB_OWNER = {'Policy review': 'Governance', 'Insurance renewal': 'Finance', 'Yearly return': 'Finance', 'Annual report': 'Fundraising', 'Accounts review': 'Finance', 'Funder report': 'Fundraising', 'Board training': 'Governance', 'Safety check': 'Governance'}
def ob_kinds_d(): return [dict(kind=key('obkind', k), repeats_months=OB_REPEAT[k], owner=key('committee', OB_OWNER[k])) for k in OBLIGATION_KINDS]


# ---------------------------------------------------------------- meeting plan: the last nine board meetings and the three planned ones
BOARD_MT = [m for m in MT if m['kind'] == 'Board']
_held = [m for m in BOARD_MT if m['status'] == 'Held'][-9:]
_plan = [m for m in BOARD_MT if m['status'] == 'Planned']
PLAN_PLANNED = {0: (7, True, 5), 1: (5, False, 8), 2: (0, False, 0)}
def meeting_plan_d():
    rows = []
    for i, m in enumerate(_held): rows.append(dict(meeting_id=m['meeting_id'], agenda_items=6 + (i * 2) % 4, papers_ready=True, confirmed=min(m['expected'], m['present'] + (1 if i % 3 == 0 else 0))))
    for i, m in enumerate(_plan):
        a, p, c_ = PLAN_PLANNED[i]; rows.append(dict(meeting_id=m['meeting_id'], agenda_items=a, papers_ready=p, confirmed=c_))
    return rows


# ---------------------------------------------------------------- board pack: the four finance items are typed from the other parts of the suite
CASH = cash_rows()
CASH_NOW, CASH_LAST = CASH[-1], CASH[-2]
PACK = [('Cash at the bank', 1, 'money', round(CASH_NOW['closing']), round(CASH_LAST['closing'])), ('Months of reserve', 2, 'months', CASH_NOW['reserve_months'], CASH_LAST['reserve_months']),
        ('Weighted grant pipeline', 3, 'money', None, 214000), ('Restricted funds below zero', 4, 'count', 1, 0),
        ('Board members now', 5, 'count', None, 11), ('Seats vacant', 6, 'count', None, 1), ('Terms ending in 6 months', 7, 'count', None, 1), ('Attendance this year', 8, '%', None, 79),
        ('Members under the attendance setting', 9, 'count', None, 3), ('Declarations filed this year', 10, 'count', None, 7), ('Obligations overdue now', 11, 'count', None, 0),
        ('Obligations due in 30 days', 12, 'count', None, 2), ('Minutes not final', 13, 'count', None, 0), ('Meetings without quorum this year', 14, 'count', None, 0)]
def board_pack_d(): return [nb(dict(item=a, no=n, unit=u, typed=t, last=l)) for a, n, u, t, l in PACK]


if __name__ == '__main__':
    print(len(BRD_ALL), len(MT), len(ATT), len(DEC), len(OBL), len(ob_calendar_d()), FORMER['name'])
    for b in BRD: print(b['member_id'], round(_share(b['member_id'], T0.year), 2), end=' | ')
    print()
    print(collections.Counter((m['status'], m['quorum_met']) for m in MT if m['date'][:4] == str(T0.year)), collections.Counter(d['status'] for d in DEC if d['year'] == T0.year))
    print([ (m['meeting_id'], m['date'], m['present'], m['expected']) for m in _plan], len(_held))
