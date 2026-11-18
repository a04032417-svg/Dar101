"""Home Management suite part 8: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho8_lists import *
from ho8_tables import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def F(x): return ('f', x)
def V(*parts):
    """a verdict: words (list labels) and numbers or names joined with spaces; a tuple ('f', formula) is a value"""
    out = []
    for p in parts:
        if isinstance(p, tuple): out.append('(' + p[1] + ')')
        else: out.append(lbl(p))
    return '&" "&'.join(out)
def RND(x): return F('ROUND(%s,0)' % x)
def PRJ(n='pn'): return 'INDEX(%s,{in:%s})' % (PR('project_id'), n)
def PN(n='pn'): return 'INDEX(%s,{in:%s})' % (PR('project'), n)
PROJGRID = GR('What if another project', ('Bathroom refresh', {'pn': 1}), ('Garden bed', {'pn': 2}), ('Holiday dinner', {'pn': 3}), ('Spring declutter', {'pn': 4}), ('Move to the new home', {'pn': 5}))
PIN = I('pn', 'Project number, 1 to 5', 1)
tools = []

# 1 ------------------------------------------------------------ project health
NT = 'COUNTIFS(%s,%s)' % (PT('project_id'), PRJ())
ND = 'COUNTIFS(%s,%s,%s,%s)' % (PT('project_id'), PRJ(), PT('status'), S_DONE)
LATE1 = 'SUMPRODUCT(MAX((%s=%s)*(%s<>%s)*(%s<{today})*({today}-%s)))' % (PT('project_id'), PRJ(), PT('status'), S_DONE, PT('due'), PT('due'))
NB1 = 'COUNTIFS(%s,%s,%s,%s)' % (PT('project_id'), PRJ(), PT('status'), S_BL)
PAID1 = 'SUMIFS(%s,%s,%s,%s,%s)' % (PT('actual_cost'), PT('project_id'), PRJ(), PT('status'), S_DONE)
EST1 = 'SUMIFS(%s,%s,%s,%s,%s)' % (PT('est_cost'), PT('project_id'), PRJ(), PT('status'), S_DONE)
OVER1 = 'IF(%s=0,0,(%s-%s)/%s)' % (EST1, PAID1, EST1, EST1)
PC1 = 'IF(%s=0,0,ROUND(%s/%s*100,0))' % (NT, ND, NT)
tools.append(TOOL('project_health', 'Project health', 'Is the project on track',
    'Pick a project by its number on the Projects sheet: tasks, share done, the worst days late, blocked tasks and the cost of finished work against its estimate give the verdict.', [PIN], [
    O('Project', 'text', PN()), O('Tasks', 'int', NT), O('Tasks done', 'int', ND), O('Share done', 'pct', 'IF(%s=0,0,%s/%s)' % (NT, ND, NT)), O('Days late, worst task', 'int', LATE1), O('Blocked tasks', 'int', NB1),
    O('Finished work against its estimate', 'pct', OVER1),
    O('Verdict', 'text', 'IF(%s=%s,%s,IF(%s>0,%s,IF(OR(%s>0,%s>{set:cost_margin}),%s,%s)))' % (
        ND, NT, lbl('Done'), LATE1, V('Late by', F(LATE1), 'days,', RND(PC1), 'percent done'), NB1, OVER1, V('At risk,', RND(PC1), 'percent done'), V('On track,', RND(PC1), 'percent done')))], PROJGRID))

# 2 ------------------------------------------------------------ project cost against estimate
EST2 = 'SUMIFS(%s,%s,%s)' % (PT('est_cost'), PT('project_id'), PRJ())
ACT2 = 'SUMIFS(%s,%s,%s)' % (PT('actual_cost'), PT('project_id'), PRJ())
DIF2 = 'ROUND(%s-%s,2)' % (PAID1, EST1)
tools.append(TOOL('cost_vs_estimate', 'Project cost against estimate', 'Is the cost of finished work within the estimate',
    'The estimate, the actual cost to date and the paid cost lines of the project; finished tasks are compared with their own estimate, so work still to do does not hide an overspend.', [PIN], [
    O('Project', 'text', PN()), O('Estimate, whole project', 'money', EST2), O('Actual cost to date', 'money', ACT2), O('Paid, finished tasks', 'money', PAID1), O('Estimate, finished tasks', 'money', EST1),
    O('Paid less estimate, finished tasks', 'money', DIF2), O('Estimate still open', 'money', 'ROUND(%s-%s,2)' % (EST2, EST1), ),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (DIF2, V('Over by', F(DIF2)), V('Within the estimate by', F('-' + DIF2))))], PROJGRID))

# 3 ------------------------------------------------------------ move date moved
FALL = ('COUNTIFS(%s,%s,%s,"<>",%s,"<"&({today}-{in:shift}))+COUNTIFS(%s,%s,%s,"<>",%s,"<"&({today}-{in:shift}))+COUNTIFS(%s,%s,%s,"<>",%s,"<"&({today}-{in:shift}))' % (
    MC('done'), NO, MC('step'), MC('due'), AD('done'), NO, AD('orgtype'), AD('needed_by'), MB('packed'), NO, MB('label'), MB('pack_by')))
MOVES = 'COUNTIFS(%s,%s,%s,"<>")+COUNTIFS(%s,%s,%s,"<>")+COUNTIFS(%s,%s,%s,"<>")' % (MC('done'), NO, MC('step'), AD('done'), NO, AD('orgtype'), MB('packed'), NO, MB('label'))
OV0 = 'MAX(0,{set:move_date}+{set:cleanup_days}-{set:key_date})'
OV1 = 'MAX(0,{set:move_date}+{in:shift}+{set:cleanup_days}-{set:key_date})'
EXTRA3 = 'MAX(0,%s-%s)' % (OV1, OV0)
tools.append(TOOL('move_shift', 'Move date moved', 'What moves when the move day moves by a typed number of days',
    'Type the days the move day moves (minus for earlier): every step, notice and box group shifts; open items that now fall before today and the extra overlap days are counted.', [
    I('shift', 'Days the move day moves (minus = earlier)', 14)], [
    O('Move day now', 'date', '{set:move_date}'), O('Move day after the shift', 'date', '{set:move_date}+{in:shift}'), O('Days to the new move day', 'int', '{set:move_date}+{in:shift}-{today}'),
    O('Open steps, notices and box groups that move', 'int', MOVES), O('Open items that now fall before today', 'int', FALL),
    O('Overlap days now', 'int', OV0), O('Overlap days after the shift', 'int', OV1), O('Extra overlap days', 'int', EXTRA3),
    O('Verdict', 'text', V(F(FALL), 'tasks fall before today,', F(EXTRA3), 'extra overlap days'))],
    GR('What if the move day moves by', ('Minus 21 days', {'shift': -21}), ('Minus 14 days', {'shift': -14}), ('Plus 7 days', {'shift': 7}), ('Plus 14 days', {'shift': 14}), ('Plus 28 days', {'shift': 28}))))

# 4 ------------------------------------------------------------ hosting countdown
OPENH = 'COUNTIFS(%s,0,%s,"<>")' % (HT('done_flag'), HT('task'))
NBH = 'COUNTIFS(%s,%s,%s,"<>")' % (MS('bought'), NO, MS('item'))
DAYSD = 'IF({set:dinner_date}="","",{set:dinner_date}-{today})'
tools.append(TOOL('hosting_countdown', 'Hosting countdown', 'How ready is the holiday dinner',
    'Counts the days left to the dinner, the hosting tasks still open and overdue and the menu items not bought; type how many days before the dinner you want to shop to see the shopping day.', [
    I('shop_before', 'Shop this many days before the dinner', 3)], [
    O('Dinner date', 'date', '{set:dinner_date}'), O('Days left', 'int', DAYSD), O('Hosting tasks open', 'int', OPENH),
    O('Hosting tasks overdue', 'int', 'COUNTIFS(%s,"<"&{today})' % HT('open_due')), O('Menu items not bought', 'int', NBH),
    O('Shopping day', 'date', '{set:dinner_date}-{in:shop_before}'), O('Days to the shopping day', 'int', '{set:dinner_date}-{in:shop_before}-{today}'),
    O('Verdict', 'text', V(F(DAYSD), 'days left,', F(OPENH), 'tasks open,', F(NBH), 'items not bought'))],
    GR('What if you shop', ('1 day before', {'shop_before': 1}), ('2 days before', {'shop_before': 2}), ('4 days before', {'shop_before': 4}), ('5 days before', {'shop_before': 5}), ('7 days before', {'shop_before': 7}))))

# 5 ------------------------------------------------------------ guest count to menu quantities
SC = '{set:guests_at_table}/{in:guests}'
PACKSG = '+'.join('COUNTIFS(%s,">"&((%d+0.000001)*%s))' % (MS('exact'), k, SC) for k in range(25))
tools.append(TOOL('guest_menu', 'Guest count to menu quantities', 'How many packs for this many guests',
    'Type the guests at the table: every menu item is scaled from the guests the menu was planned for and rounded up to whole packs; the extra packs against the planned menu are shown.', [
    I('guests', 'Guests at the table', 14)], [
    O('Guests the menu is planned for', 'int', '{set:guests_at_table}'), O('Scale against the planned menu', 'num', 'ROUND({in:guests}/{set:guests_at_table},2)'),
    O('Items to buy', 'int', 'COUNTIFS(%s,">0")' % MS('exact')), O('Packs for the planned menu', 'int', 'SUM(%s)' % MS('packs')), O('Packs for the typed guests', 'int', PACKSG),
    O('Extra packs against the plan', 'int', '(%s)-SUM(%s)' % (PACKSG, MS('packs'))),
    O('Verdict', 'text', V('Buy', F(PACKSG), 'packs for', F('{in:guests}'), 'guests'))],
    GR('What if the guests are', ('8 guests', {'guests': 8}), ('10 guests', {'guests': 10}), ('12 guests', {'guests': 12}), ('16 guests', {'guests': 16}), ('20 guests', {'guests': 20}))))

# 6 ------------------------------------------------------------ RSVP summary
YES_P = 'SUMIFS(%s,%s,%s)' % (GS('party_size'), GS('rsvp'), tok('rsvp', 'Yes'))
MAY_P = 'SUMIFS(%s,%s,%s)' % (GS('party_size'), GS('rsvp'), tok('rsvp', 'Maybe'))
NO_P = 'SUMIFS(%s,%s,%s)' % (GS('party_size'), GS('rsvp'), tok('rsvp', 'No'))
NR_P = 'SUMIFS(%s,%s,%s)' % (GS('party_size'), GS('rsvp'), tok('rsvp', 'No reply'))
EXPECT = '(%s+ROUND(%s*{in:maybe_pct}/100,0))' % (YES_P, MAY_P)
tools.append(TOOL('rsvp_summary', 'RSVP summary', 'Who is coming to the dinner',
    'Yes, maybe, no and no reply counted in people (party sizes); type the share of maybe guests who usually come to see how many to expect at the table and the seats left.', [
    I('maybe_pct', 'Share of maybe guests who come, percent', 50)], [
    O('Invited, people', 'int', 'SUM(%s)' % GS('party_size')), O('Confirmed, people', 'int', YES_P), O('Maybe, people', 'int', MAY_P), O('No, people', 'int', NO_P), O('No reply, people', 'int', NR_P),
    O('Expect at the table', 'int', EXPECT), O('Seats left at the table', 'int', '{set:guests_at_table}-%s' % EXPECT),
    O('Verdict', 'text', V(F(YES_P), 'confirmed,', F(MAY_P), 'maybe, expect', F(EXPECT), 'at the table'))],
    GR('What if maybe guests come', ('0 percent', {'maybe_pct': 0}), ('25 percent', {'maybe_pct': 25}), ('75 percent', {'maybe_pct': 75}), ('100 percent', {'maybe_pct': 100}))))

# 7 ------------------------------------------------------------ hosting task timeline
NEXTD = 'MIN(%s)' % HT('open_due')
NXT = 'IF(COUNT(%s)=0,"",%s+{in:move})' % (HT('open_due'), NEXTD)
NXT_N = 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&"","")' % (HT('task'), NEXTD, HT('open_due'))
NXT_D = '(%s-{today})' % NXT
tools.append(TOOL('hosting_timeline_tool', 'Hosting task timeline', 'Which hosting task is next',
    'The hosting tasks counted back from the dinner date: the next open task, when it is due and how many fall in the next 7 days; type the days the dinner moves to shift every task.', [
    I('move', 'Days the dinner moves', 0)], [
    O('Hosting tasks', 'int', 'COUNTIFS(%s,"<>")' % HT('task')), O('Hosting tasks done', 'int', 'SUM(%s)' % HT('done_flag')), O('Next task', 'text', NXT_N), O('Next task due', 'date', NXT),
    O('Days to the next task', 'int', NXT_D), O('Open tasks due in the next 7 days', 'int', 'COUNTIFS(%s,">="&({today}-{in:move}),%s,"<="&({today}+6-{in:move}))' % (HT('open_due'), HT('open_due'))),
    O('Open tasks overdue', 'int', 'COUNTIFS(%s,"<"&({today}-{in:move}))' % HT('open_due')),
    O('Verdict', 'text', 'IF(COUNT(%s)=0,%s,IF(%s<0,%s,%s))' % (HT('open_due'), lbl('All hosting tasks done'), NXT_D, V('Next task', F(NXT_N), 'is overdue by', F('-' + NXT_D), 'days'), V('Next task', F(NXT_N), 'is due in', F(NXT_D), 'days')))],
    GR('What if the dinner moves by', ('Minus 7 days', {'move': -7}), ('Minus 3 days', {'move': -3}), ('Plus 3 days', {'move': 3}), ('Plus 7 days', {'move': 7}))))

# 8 ------------------------------------------------------------ critical path
CNT_C = 'COUNTIFS(%s,"<"&(({in:pn}+1)*100))' % TD('chain_key')
CHAIN = 'MAX(0,IFERROR(SMALL(%s,%s)-{in:pn}*100,0))' % (TD('chain_key'), CNT_C)
FCK = 'IFERROR(SMALL(%s,COUNTIFS(%s,"<"&(({in:pn}+1)*100000)))-{in:pn}*100000,0)' % (TD('fc_key'), TD('fc_key'))
PLAN = 'SUMPRODUCT(MAX((%s=%s)*%s))' % (PT('project_id'), PRJ(), PT('due'))
FC = 'IF(%s<=0,%s,%s)' % (FCK, PLAN, FCK)
WSL = 'MAX(0,IFERROR(SMALL(%s,COUNTIFS(%s,"<"&(({in:pn}+1)*1000)))-{in:pn}*1000,0))' % (TD('slip_key'), TD('slip_key'))
SLIP8 = 'MAX(0,%s-%s)' % (FC, PLAN)
tools.append(TOOL('critical_path', 'Critical path', 'How long is the chain of waiting tasks and does it slip',
    'Every open task waits for the task it depends on: the longest chain of open tasks of the project, the worst slip a late task passes down the chain, the planned finish and the forecast finish.', [PIN], [
    O('Project', 'text', PN()), O('Open tasks in the longest chain', 'int', CHAIN), O('Worst slip passed down the chain, days', 'int', WSL), O('Planned finish', 'date', PLAN), O('Forecast finish', 'date', FC),
    O('Days to the forecast finish', 'int', '%s-{today}' % FC), O('Slip of the finish, days', 'int', SLIP8),
    O('Verdict', 'text', 'IF(%s<=0,%s,IF(%s>0,%s,%s))' % (FCK, lbl('Done'), SLIP8, V('Slips by', F(SLIP8), 'days'), V('On time, finish in', F('%s-{today}' % FC), 'days')))], PROJGRID))

# 9 ------------------------------------------------------------ task owner load
def OWN(o, extra=''): return 'COUNTIFS(%s,%s,%s,1,%s,"<="&({today}+{in:days})%s)' % (PT('owner'), tok('powner', o), PT('open'), PT('due'), extra)
def OWM(o): return 'SUMIFS(%s,%s,%s,%s,1,%s,"<="&({today}+{in:days}))' % (PT('minutes'), PT('owner'), tok('powner', o), PT('open'), PT('due'))
TOT9 = '(%s)' % '+'.join(OWN(o) for o in POWNER)
A1S = 'IF(%s=0,0,%s/%s)' % (TOT9, OWN('Adult 1'), TOT9)
A2S = 'IF(%s+%s=0,0,%s/(%s+%s))' % (OWN('Adult 1'), OWN('Adult 2'), OWN('Adult 2'), OWN('Adult 1'), OWN('Adult 2'))
tools.append(TOOL('owner_load', 'Task owner load', 'Who holds the open project tasks',
    'Open project tasks that fall due in the look-ahead window (late tasks included) and their effort minutes for each person; the fairness line compares adult 2 with the agreed share.', [
    I('days', 'Look-ahead, days', 30)], [
    O('Open tasks, adult 1', 'int', OWN('Adult 1')), O('Open tasks, adult 2', 'int', OWN('Adult 2')), O('Open tasks, children', 'int', '%s+%s' % (OWN('Child 1'), OWN('Child 2'))), O('Open tasks, a trade', 'int', OWN('A trade')),
    O('Minutes, adult 1', 'int', OWM('Adult 1')), O('Minutes, adult 2', 'int', OWM('Adult 2')),
    O('Adult 2 share of adult tasks', 'pct', A2S), O('Agreed share of adult 2', 'pct', '{set:agreed_split_a2}'), O('Points away from the agreed share', 'num', 'ROUND((%s-{set:agreed_split_a2})*100,1)' % A2S),
    O('Verdict', 'text', V('Adult 1 holds', RND(A1S + '*100'), 'percent of open tasks'))],
    GR('What if the window is', ('14 days', {'days': 14}), ('45 days', {'days': 45}), ('60 days', {'days': 60}), ('90 days', {'days': 90}))))

# 10 ----------------------------------------------------------- overlap days in a move
REL = '{set:move_date}+{in:shift}+{in:kept}'
OVL = 'MAX(0,%s-{set:key_date})' % REL
tools.append(TOOL('overlap_days', 'Overlap days in a move', 'How many days do two homes overlap and what do they cost',
    'The new key date and the old home released after the move day give the days you hold both homes; type the cost per day of the old home for the cost line of the overlap.', [
    I('kept', 'Days the old home is kept after the move day', 2), I('shift', 'Days the move day moves', 0), I('perday', 'Cost of the old home per day', 35, 'money')], [
    O('Key date of the new home', 'date', '{set:key_date}'), O('Move day', 'date', '{set:move_date}+{in:shift}'), O('Old home released', 'date', REL),
    O('Days from the key date to the move day', 'int', 'MAX(0,{set:move_date}+{in:shift}-{set:key_date})'), O('Overlap days', 'int', OVL), O('Cost line of the overlap', 'money', '%s*{in:perday}' % OVL),
    O('Verdict', 'text', V(F(OVL), 'overlap days'))],
    GR('What if the old home is kept', ('0 days', {'kept': 0}), ('5 days', {'kept': 5}), ('7 days', {'kept': 7}), ('14 days', {'kept': 14}))))

# 11 ----------------------------------------------------------- packing progress
BCNT = 'SUM(%s)' % MB('boxes'); BPK = 'SUMIFS(%s,%s,%s)' % (MB('boxes'), MB('packed'), YES); BLEFT = 'SUM(%s)' % MB('left')
DMV = '({set:move_date}-{today})'
tools.append(TOOL('packing_progress', 'Packing progress', 'Will the boxes be packed before the move',
    'Boxes counted, packed and left against the days to the move day; type how many boxes you pack a day to see the days needed and the busiest room.', [
    I('rate', 'Boxes you pack in a day', 6)], [
    O('Boxes counted', 'int', BCNT), O('Boxes packed', 'int', BPK), O('Boxes left', 'int', BLEFT), O('Share packed', 'pct', 'IF(%s=0,0,%s/%s)' % (BCNT, BPK, BCNT)), O('Days to the move day', 'int', DMV),
    O('Boxes a day to finish', 'num', 'IF(%s<=0,"",ROUND(%s/%s,1))' % (DMV, BLEFT, DMV)), O('Days needed at the typed rate', 'int', 'ROUNDUP(%s/{in:rate},0)' % BLEFT),
    O('Room with the most boxes left', 'text', 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0))&"","")' % (MB('room'), MB('left'), MB('left'))),
    O('Verdict', 'text', V(F(BLEFT), 'boxes left,', F(DMV), 'days'))],
    GR('What if you pack', ('3 boxes a day', {'rate': 3}), ('4 boxes a day', {'rate': 4}), ('8 boxes a day', {'rate': 8}), ('12 boxes a day', {'rate': 12}))))

# 12 ----------------------------------------------------------- change-of-address progress
LEFTA = 'COUNTIFS(%s,%s,%s,"<>")' % (AD('done'), NO, AD('orgtype'))
FIRSTA = 'MIN(%s)+{in:shift}' % AD('open_by')
DAYSA = '(%s-{today})' % FIRSTA
tools.append(TOOL('address_progress', 'Change-of-address progress', 'Who still has to be told about the new address',
    'Organisation types done against the notice they need; the first date to tell one is the move day less the longest notice still open. Type the days the move day moves to shift every date.', [
    I('shift', 'Days the move day moves', 0)], [
    O('Organisation types', 'int', 'COUNTIFS(%s,"<>")' % AD('orgtype')), O('Done', 'int', 'COUNTIFS(%s,%s)' % (AD('done'), YES)), O('Left', 'int', LEFTA),
    O('Left and overdue', 'int', 'COUNTIFS(%s,"<"&({today}-{in:shift}))' % AD('open_by')), O('First to tell by', 'date', FIRSTA), O('Days to the first date', 'int', DAYSA),
    O('Longest notice still open, days', 'int', 'SUMPRODUCT(MAX((%s=%s)*%s))' % (AD('done'), NO, AD('notice_days'))),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s<0,%s,%s))' % (LEFTA, lbl('Everyone has been told'), DAYSA, V(F(LEFTA), 'organisations left, first overdue by', F('-' + DAYSA), 'days'), V(F(LEFTA), 'organisations left, first in', F(DAYSA), 'days')))],
    GR('What if the move day moves by', ('Minus 14 days', {'shift': -14}), ('Minus 7 days', {'shift': -7}), ('Plus 7 days', {'shift': 7}), ('Plus 14 days', {'shift': 14}))))

# 13 ----------------------------------------------------------- declutter progress by area
STARTED = 'COUNTIFS(%s,">="&{in:min_items})' % DA('decided')
AREAS = 'COUNTIFS(%s,"<>")' % DA('area')
tools.append(TOOL('declutter_progress', 'Declutter progress by area', 'How many areas are decided',
    'Areas with items decided in the Declutter log against the areas still not started; type how many items make an area count as started.', [
    I('min_items', 'Items that make an area started', 1)], [
    O('Areas', 'int', AREAS), O('Areas started', 'int', STARTED), O('Areas not started', 'int', '%s-%s' % (AREAS, STARTED)), O('Share of areas started', 'pct', 'IF(%s=0,0,%s/%s)' % (AREAS, STARTED, AREAS)),
    O('Items decided', 'int', 'SUM(%s)' % DA('decided')), O('Busiest area', 'text', 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0))&"","")' % (DA('area'), DA('decided'), DA('decided'))),
    O('Next area to start', 'text', '{col_unused}'),
    O('Verdict', 'text', V(F('%s-%s' % (AREAS, STARTED)), 'areas not started'))],
    GR('What if an area is started at', ('2 items', {'min_items': 2}), ('5 items', {'min_items': 5}), ('10 items', {'min_items': 10}), ('20 items', {'min_items': 20}))))
tools[-1]['outputs'][6] = O('Next area to start', 'text', 'IFERROR(INDEX(%s,MATCH(0,%s,0))&"","")' % (DA('area'), DA('decided')))

# 14 ----------------------------------------------------------- donations by month
Y0 = 'YEAR({today})'
DY = 'SUMIFS(%s,%s,%s)' % (DN('count'), DN('year'), Y0)
DM = 'SUMIFS(%s,%s,">="&DATE(%s,{in:month},1),%s,"<"&DATE(%s,{in:month}+1,1))' % (DN('count'), DN('date'), Y0, DN('date'), Y0)
tools.append(TOOL('donations_month', 'Donations by month', 'How many items went to a donation this year',
    'Items donated this year and in the month you type, from the donation log; the drop-off days count each date once.', [
    I('month', 'Month number, 1 to 12', 3)], [
    O('Items donated this year', 'int', DY), O('Items donated in the typed month', 'int', DM),
    O('Drop-off days this year', 'int', 'SUMIFS(%s,%s,%s)' % (DN('drop_off'), DN('year'), Y0)), O('Donation lines this year', 'int', 'COUNTIFS(%s,%s)' % (DN('year'), Y0)),
    O('Last drop-off', 'date', 'MAX(%s)' % DN('date')), O('Average items per drop-off', 'num', 'IFERROR(ROUND(%s/SUMIFS(%s,%s,%s),1),0)' % (DY, DN('drop_off'), DN('year'), Y0)),
    O('Verdict', 'text', V(F(DY), 'items donated this year'))],
    GR('What if the month is', ('Month 2', {'month': 2}), ('Month 4', {'month': 4}), ('Month 5', {'month': 5}), ('Month 11', {'month': 11}))))

# 15 ----------------------------------------------------------- keep, donate, sell or bin split
CR = 'IF({in:area_no}=0,"*",INDEX(%s,{in:area_no}))' % DA('area')
def DEC(d): return 'SUMIFS(%s,%s,%s,%s,%s)' % (DL('count'), DL('decision'), tok('decision', d), DL('area'), CR)
TOT15 = 'SUMIFS(%s,%s,%s)' % (DL('count'), DL('area'), CR)
tools.append(TOOL('decision_split', 'Keep, donate, sell or bin split', 'What share of the items went where',
    'The items of the Declutter log split into keep, donate, sell and bin, for all areas or for the area number you type from Declutter areas.', [
    I('area_no', 'Area number, 0 for all areas', 0)], [
    O('Area', 'text', 'IF({in:area_no}=0,%s,INDEX(%s,{in:area_no})&"")' % (lbl('All areas'), DA('area'))), O('Items decided', 'int', TOT15), O('Keep', 'int', DEC('Keep')), O('Donate', 'int', DEC('Donate')), O('Sell', 'int', DEC('Sell')),
    O('Bin', 'int', DEC('Bin')), O('Share donated', 'pct', 'IF(%s=0,0,%s/%s)' % (TOT15, DEC('Donate'), TOT15)), O('Value of the items sold', 'money', 'SUMIFS(%s,%s,%s,%s,%s)' % (DL('value'), DL('decision'), SELL, DL('area'), CR)),
    O('Verdict', 'text', V(RND('IF(%s=0,0,%s/%s)*100' % (TOT15, DEC('Donate'), TOT15)), 'percent of items donated'))],
    GR('What if the area is', ('Area 1', {'area_no': 1}), ('Area 2', {'area_no': 2}), ('Area 3', {'area_no': 3}), ('Area 4', {'area_no': 4}))))

# 16 ----------------------------------------------------------- time to finish a declutter
NSA = 'COUNTIFS(%s,0,%s,"<>")' % (DA('decided'), DA('area'))
SESS = 'ROUNDUP(%s/{in:per_session},0)' % NSA
SMIN = '{in:per_session}*{in:minutes}'
tools.append(TOOL('declutter_time', 'Time to finish a declutter', 'How many sessions are left',
    'The areas not started times the minutes you type for one area, grouped into sessions of the areas you do together; the finish day follows from the days between sessions.', [
    I('minutes', 'Minutes for one area', 45), I('per_session', 'Areas in one session', 1), I('gap', 'Days between sessions', 7)], [
    O('Areas not started', 'int', NSA), O('Minutes in total', 'int', '%s*{in:minutes}' % NSA), O('Sessions', 'int', SESS), O('Minutes in one session', 'int', SMIN),
    O('Finish day', 'date', '{today}+(%s-1)*{in:gap}' % SESS), O('Days to the finish day', 'int', '(%s-1)*{in:gap}' % SESS),
    O('Verdict', 'text', V(F(SESS), 'sessions of', F(SMIN), 'minutes'))],
    GR('What if one session holds', ('2 areas', {'per_session': 2}), ('3 areas', {'per_session': 3}), ('4 areas', {'per_session': 4}), ('5 areas', {'per_session': 5}))))

# 17 ----------------------------------------------------------- year in review summary
WL = 'COUNT(%s)' % YV('gain')
IMP = 'COUNTIFS(%s,">"&({in:band}/100))' % YV('gain')
WRS = 'COUNTIFS(%s,"<"&(-{in:band}/100))' % YV('gain')
tools.append(TOOL('year_summary', 'Year in review summary', 'Did the home do better than last year',
    'The 14 measures of this year against last year: improved, worse and the same, with a band in percent inside which a change counts as the same.', [
    I('band', 'Same when the change is within, percent', 2)], [
    O('Measures with a number this year', 'int', 'COUNT(%s)' % YV('this_year')), O('Measures with last year typed', 'int', WL), O('Improved', 'int', IMP), O('Worse', 'int', WRS), O('The same', 'int', '%s-%s-%s' % (WL, IMP, WRS)),
    O('Share improved', 'pct', 'IF(%s=0,0,%s/%s)' % (WL, IMP, WL)), O('Measure that improved most', 'text', 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0))&"","")' % (YV('measure'), YV('gain'), YV('gain'))),
    O('Verdict', 'text', V(F(IMP), 'of 14 measures improved,', F(WRS), 'worse'))],
    GR('What if the band is', ('0 percent', {'band': 0}), ('5 percent', {'band': 5}), ('10 percent', {'band': 10}), ('20 percent', {'band': 20}))))

# 18 ----------------------------------------------------------- next-year plan lines
def SETL(k): return '(LEN(TRIM({in:%s}))>0)' % k
def MEAS(k): return 'IFERROR(INDEX(%s,{in:%s})&"","")' % (YV('measure'), k)
def WORSE(k): return 'IFERROR(IF(INDEX(%s,{in:%s})<-{set:same_band},1,0),0)' % (YV('gain'), k)
SETN = '(%s)' % '+'.join(SETL(k) for k in ('l1', 'l2', 'l3'))
tools.append(TOOL('next_year', 'Next-year plan lines', 'Is there a line for next year',
    'Type three lines for next year and the number of the measure each one answers (the row on Year in review): see the measure, whether it got worse and how many lines are still missing.', [
    I('l1', 'Line 1', 'Put every filter change in the plan at the start of each season', 'text'), I('m1', 'Line 1 answers measure number', 1),
    I('l2', 'Line 2', 'Do the seasonal maintenance tasks on time', 'text'), I('m2', 'Line 2 answers measure number', 2),
    I('l3', 'Line 3', 'Share the planning and booking jobs more evenly', 'text'), I('m3', 'Line 3 answers measure number', 3)], [
    O('Lines set', 'int', SETN), O('Lines missing', 'int', '3-%s' % SETN), O('Measure line 1 answers', 'text', MEAS('m1')), O('Measure line 2 answers', 'text', MEAS('m2')), O('Measure line 3 answers', 'text', MEAS('m3')),
    O('Lines on a measure that got worse', 'int', '%s+%s+%s' % (WORSE('m1'), WORSE('m2'), WORSE('m3'))),
    O('Verdict', 'text', 'IF(%s=3,%s,%s)' % (SETN, lbl('3 lines set'), V(F('3-%s' % SETN), 'lines missing')))],
    GR('What if the first line answers measure', ('Measure 1', {'m1': 1}), ('Measure 2', {'m1': 2}), ('Measure 9', {'m1': 9}), ('Measure 14', {'m1': 14}))))
assert len(tools) == 18, len(tools)
