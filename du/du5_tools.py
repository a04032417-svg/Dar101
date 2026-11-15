"""Doula business suite part 5: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du5_lists import *
import du5_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='num', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, lab): return IN(k, label, 'list', key(lst, lab), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
THISMON = '({today}-WEEKDAY({today},2)+1)'
QS = 'DATE(YEAR({today}),3*INT((MONTH({today})-1)/3)+1,1)'
YES = '{list:yesno.yes}'
PRE = tok('vkind', 'Prenatal visit'); PPV = tok('vkind', 'Postpartum visit'); NIGHT = tok('vkind', 'Night shift'); DEB = tok('vkind', 'Debrief visit')
def DW(col, n): return '{range:%s},">="&({today}-%s),{range:%s},"<="&{today}' % (col, n, col)
def DM(col, n): return '{range:%s},">"&EDATE({today},-%s),{range:%s},"<="&{today}' % (col, n, col)
tools = []

# 1 ------------------------------------------------------------ actual hours vs plan
def PH(c): return 'IFERROR(INDEX({range:phase.%s},MATCH({in:client},{range:phase.client},0)),0)' % c
WORST = 'MAX({range:phase.over_share})'
tools.append(TOOL('hours_plan', 'Actual Hours vs Plan', 'Which clients took more hours than the package plans',
    'Type a client and the share over plan that you accept: the hours by phase against the package plan, the clients over plan and the worst one; the hours are counted from Visits, Births Attended and On-call Windows.', [
    I('client', 'Client', D.DEF_OVER_CLIENT, 'text'), I('share', 'Share over plan that you accept', 0.15, 'pct')], [
    O('Package', 'text', 'IFERROR(INDEX({range:phase.package},MATCH({in:client},{range:phase.client},0)),"")'), O('Planned hours', 'num', PH('plan_hours')),
    O('Prenatal hours', 'num', PH('prenatal_hours')), O('On-call contact hours', 'num', PH('oncall_hours')), O('Birth hours', 'num', PH('birth_hours')), O('Postpartum hours', 'num', PH('postpartum_hours')),
    O('Total hours', 'num', PH('total_hours')), O('Hours over or under plan', 'num', '%s-%s' % (PH('total_hours'), PH('plan_hours'))), O('Share over or under plan', 'pct', PH('over_share')),
    O('Client check', 'text', 'IF(%s>{in:share},%s,%s)' % (PH('over_share'), c2('Client is over plan'), c2('Client is within plan'))),
    O('Clients over the share you accept', 'int', 'COUNTIFS({range:phase.over_share},">"&{in:share})'), O('Worst client', 'text', 'IFERROR(INDEX({range:phase.client},MATCH(%s,{range:phase.over_share},0)),"")' % WORST),
    O('Worst share over plan', 'pct', WORST), O('Extra hours across those clients', 'num', 'SUMIFS({range:phase.excess_hours},{range:phase.over_share},">"&{in:share})'),
    O('Value of those extra hours at the extra-hour rate', 'money', 'SUMIFS({range:phase.excess_hours},{range:phase.over_share},">"&{in:share})*{set:extra_hour_rate}'),
    O('Verdict', 'text', 'IF(COUNTIFS({range:phase.over_share},">"&{in:share})>0,%s&": "&COUNTIFS({range:phase.over_share},">"&{in:share}),%s)' % (c2('Review clients over plan'), c2('Hours are within plan')))],
    GR('What if', ('Accept 5% over plan', {'share': 0.05}), ('Accept 10% over plan', {'share': 0.10}), ('Accept 20% over plan', {'share': 0.20}), ('Accept 30% over plan', {'share': 0.30}), ('Accept 40% over plan', {'share': 0.40}))))

# 2 ------------------------------------------------------------ postpartum hours ledger
def LG(c): return 'IFERROR(INDEX({range:ledger.%s},MATCH({in:pack},{range:ledger.pack_id},0)),0)' % c
SOON = '{range:ledger.days_to_expiry},">=0",{range:ledger.days_to_expiry},"<="&{in:soon},{range:ledger.hours_left},">0"'
tools.append(TOOL('ledger_tool', 'Postpartum Hours Ledger', 'What to invoice and which hours to use before a pack ends',
    'Type a pack and the days that count as ending soon: hours bought, used and left, the extra hours as an invoice-ready amount at your rate, and the packs with hours left before they end; read from Hour Pack Ledger.', [
    I('pack', 'Pack ID', D.DEF_PACK, 'text'), I('rate', 'Rate for extra hours, per hour', 40, 'money'), I('soon', 'Days that count as ending soon', 30, 'int')], [
    O('Client', 'text', 'IFERROR(INDEX({range:ledger.client},MATCH({in:pack},{range:ledger.pack_id},0)),"")'), O('Hours bought', 'num', LG('hours_bought')), O('Hours used', 'num', LG('hours_used')), O('Hours left', 'num', LG('hours_left')),
    O('Expires on', 'date', LG('expires_on')), O('Days to expiry', 'int', LG('days_to_expiry')), O('Extra hours beyond the pack', 'num', LG('extra_hours')), O('Invoice-ready amount for this pack', 'money', '%s*{in:rate}' % LG('extra_hours')),
    O('Packs ending soon with hours left', 'int', 'COUNTIFS(%s)' % SOON), O('Hours left on those packs', 'num', 'SUMIFS({range:ledger.hours_left},%s)' % SOON), O('Value of those hours', 'money', 'SUMIFS({range:ledger.value_left},%s)' % SOON),
    O('Extra hours not yet invoiced, all packs', 'num', 'SUMIFS({range:ledger.extra_hours},{range:ledger.to_invoice},1)'), O('Invoice-ready amount, all packs', 'money', 'SUMIFS({range:ledger.extra_hours},{range:ledger.to_invoice},1)*{in:rate}'),
    O('Value of hours left on running packs', 'money', 'SUMIFS({range:ledger.value_left},{range:ledger.days_to_expiry},">=0")'),
    O('Verdict', 'text', 'IF(SUMIFS({range:ledger.extra_hours},{range:ledger.to_invoice},1)>0,%s&": "&ROUND(SUMIFS({range:ledger.extra_hours},{range:ledger.to_invoice},1)*{in:rate},0),IF(COUNTIFS(%s)>0,%s&": "&ROUND(SUMIFS({range:ledger.hours_left},%s),0),%s))' % (c2('Invoice the extra hours'), SOON, c2('Use hours before expiry'), SOON, c2('Ledger is clear')))],
    GR('What if', ('Rate 35 an hour', {'rate': 35}), ('Rate 45 an hour', {'rate': 45}), ('Ending soon means 14 days', {'soon': 14}), ('Ending soon means 60 days', {'soon': 60}), ('Ending soon means 90 days', {'soon': 90}))))

# 3 ------------------------------------------------------------ weekly hours load
TWK = 'SUMIFS({range:visits.hours},{range:visits.doula},{in:doula},{range:visits.week},%s)+SUMIFS({range:births.hours},{range:births.doula},{in:doula},{range:births.week},%s)' % (THISMON, THISMON)
def HW(n): return '(SUMIFS({range:visits.hours},{range:visits.doula},{in:doula},%s)+SUMIFS({range:births.hours},{range:births.doula},{in:doula},%s))' % (DW('visits.date', n), DW('births.date', n))
STREAK = 'SUMIFS({range:wk_doula.weeks_over},{range:wk_doula.doula},{in:doula},{range:wk_doula.week},%s)' % THISMON
tools.append(TOOL('weekly_load', 'Weekly Hours Load', 'Is a doula over the weekly hours cap and does next week need a cut',
    'Pick a doula, type the hours planned for next week and the cap: this week, the last 4 and 12 weeks, the weeks over the cap and in a row, and whether to cut hours or give a rest week; read from Weekly Hours by Doula.', [
    IL('doula', 'Doula', 'doula', 'Sven Lindqvist'), I('planned', 'Hours planned for next week', 30), I('cap', 'Weekly hours cap', WEEKLY_HOURS_CAP)], [
    O('Hours this week', 'num', TWK), O('Average weekly hours, last 4 weeks', 'num', '%s/4' % HW(28)), O('Average weekly hours, last 12 weeks', 'num', '%s/12' % HW(84)),
    O('Weeks over the cap, last 12 weeks', 'int', 'COUNTIFS({range:wk_doula.doula},{in:doula},{range:wk_doula.week},">="&({today}-84),{range:wk_doula.total_hours},">"&{in:cap})'),
    O('Weeks over the cap in a row, now', 'int', STREAK), O('Hours planned for next week', 'num', '{in:planned}'), O('Room under the cap next week', 'num', '{in:cap}-{in:planned}'), O('Hours to take out of next week', 'num', 'MAX(0,{in:planned}-{in:cap})'),
    O('Busiest doula in the last 4 weeks', 'text', 'IFERROR(INDEX({range:wk_doula.doula},MATCH(MAX({range:wk_doula.hours_last4}),{range:wk_doula.hours_last4},0)),"")'), O('Hours of the busiest doula in one week', 'num', 'MAX({range:wk_doula.hours_last4})'),
    O('Verdict', 'text', 'IF(%s>={set:weeks_over_warn},%s,IF({in:planned}>{in:cap},%s&": "&ROUND({in:planned}-{in:cap},0),%s))' % (STREAK, c2('Rest week needed'), c2('Reduce next week'), c2('Within the cap')))],
    GR('What if', ('Light week of 12 hours', {'planned': 12}), ('Week at the cap', {'planned': 24}), ('Heavy week of 40 hours', {'planned': 40}), ('Cap of 30 hours', {'cap': 30}), ('Cap of 20 hours', {'cap': 20}))))

# 4 ------------------------------------------------------------ mileage log totals
PRICE12 = 'SUMIFS({range:clients.price},{range:clients.edd},">"&EDATE({today},-{in:months}),{range:clients.edd},"<="&{today},{range:clients.status},"<>"&%s)' % tok('cstatus', 'Cancelled')
N12 = 'COUNTIFS({range:clients.edd},">"&EDATE({today},-{in:months}),{range:clients.edd},"<="&{today},{range:clients.status},"<>"&%s)' % tok('cstatus', 'Cancelled')
COST12 = 'SUMIFS({range:mil_month.mileage_cost},{range:mil_month.month},">="&EDATE(%s,-{in:months}),{range:mil_month.month},"<="&%s)' % (MS, MS)
VA = '{range:visits.area},{in:area},%s' % DM('visits.date', '{in:months}'); BA = '{range:births.area},{in:area},%s' % DM('births.date', '{in:months}')
tools.append(TOOL('mileage_tool', 'Mileage Log Totals', 'Is mileage a fair share of the package income or does it need a travel fee',
    'Pick an area and the months to look back: trips, miles and mileage cost at the area rate, the cost per client and the mileage share of the list price against your limit; read from Visits, Births Attended and Mileage by Month.', [
    IL('area', 'Area', 'area', 'Southbank'), I('months', 'Months to look back', 12, 'int'), I('fee', 'Travel fee you could add per client', 25, 'money')], [
    O('Visits in the area', 'int', 'COUNTIFS(%s)' % VA), O('Births attended in the area', 'int', 'COUNTIFS(%s)' % BA),
    O('Miles in the area', 'num', 'SUMIFS({range:visits.miles},%s)+SUMIFS({range:births.miles},%s)' % (VA, BA)), O('Mileage rate per mile', 'money', 'SUMIFS({range:areas.mileage_rate},{range:areas.area},{in:area},{range:areas.in_use},1)'),
    O('Mileage cost in the area', 'money', 'SUMIFS({range:visits.mileage_cost},%s)+SUMIFS({range:births.mileage_cost},%s)' % (VA, BA)),
    O('Mileage cost per trip in the area', 'money', 'IFERROR((SUMIFS({range:visits.mileage_cost},%s)+SUMIFS({range:births.mileage_cost},%s))/(COUNTIFS(%s)+COUNTIFS(%s)),0)' % (VA, BA, VA, BA)),
    O('Mileage cost, all areas', 'money', COST12), O('Clients due in the period', 'int', N12), O('List price of those clients', 'money', PRICE12),
    O('Mileage cost per client', 'money', 'IFERROR(%s/%s,0)' % (COST12, N12)), O('Mileage share of the list price', 'pct', 'IFERROR(%s/%s,0)' % (COST12, PRICE12)), O('Mileage share you accept', 'pct', '{set:mileage_share_max}'),
    O('Travel fee that brings the share to your limit', 'money', 'MAX(0,IFERROR(%s/%s,0)-IFERROR({set:mileage_share_max}*%s/%s,0))' % (COST12, N12, PRICE12, N12)),
    O('Income from your fee over the period', 'money', '{in:fee}*%s' % N12),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s,0)>{set:mileage_share_max},%s,%s)' % (COST12, PRICE12, c2('Add a travel fee'), c2('Mileage share is fine')))],
    GR('What if', ('Northgate, 12 months', {'area': '=' + tok('area', 'Northgate')}), ('Southbank, 6 months', {'months': 6}), ('Southbank, 3 months', {'months': 3}), ('Southbank, 24 months', {'months': 24}), ('Travel fee of 50', {'fee': 50}))))

# 5 ------------------------------------------------------------ births attended summary
BQ = 'COUNTIFS({range:births.qtr},%s)' % QS
tools.append(TOOL('births_tool', 'Births Attended Summary', 'How many births are attended this quarter against the maximum',
    'Pick a doula and type the most births the agency attends in a quarter: births this quarter, last quarter and a year ago, the doula\'s births and hours over 12 months and the average; read from Births Attended.', [
    IL('doula', 'Doula who attended', 'attender', 'Amara Okonkwo'), I('qmax', 'Most births the agency attends in a quarter', 18, 'int')], [
    O('Births this quarter so far', 'int', BQ), O('Births last quarter', 'int', 'COUNTIFS({range:births.qtr},EDATE(%s,-3))' % QS), O('Births in the same quarter last year', 'int', 'COUNTIFS({range:births.qtr},EDATE(%s,-12))' % QS),
    O('Births left before the maximum', 'int', '{in:qmax}-%s' % BQ), O('Days left in the quarter', 'int', 'EOMONTH(%s,2)-{today}' % QS),
    O('Births of this doula this quarter', 'int', 'COUNTIFS({range:births.qtr},%s,{range:births.doula},{in:doula})' % QS),
    O('Births of this doula, last 12 months', 'int', 'COUNTIFS({range:births.doula},{in:doula},%s)' % DM('births.date', 12)),
    O('Hours attended by this doula, last 12 months', 'num', 'SUMIFS({range:births.hours},{range:births.doula},{in:doula},%s)' % DM('births.date', 12)),
    O('Average hours per birth, this doula', 'num', 'IFERROR(SUMIFS({range:births.hours},{range:births.doula},{in:doula},%s)/COUNTIFS({range:births.doula},{in:doula},%s),0)' % (DM('births.date', 12), DM('births.date', 12))),
    O('Agency births a month, last 12 months', 'num', 'COUNTIFS(%s)/12' % DM('births.date', 12)), O('Average hours per birth, agency', 'num', 'IFERROR(AVERAGEIFS({range:births.hours},%s),0)' % DM('births.date', 12)),
    O('Births with a backup doula, last 12 months', 'int', 'COUNTIFS({range:births.backup_used},%s,%s)' % (YES, DM('births.date', 12))),
    O('Verdict', 'text', 'IF(%s>{in:qmax},%s,IF(%s>=0.75*{in:qmax},%s,%s))' % (BQ, c2('Quarter is over the maximum'), BQ, c2('Quarter is near the maximum'), c2('Quarter is within the maximum')))],
    GR('What if', ('Maximum of 12', {'qmax': 12}), ('Maximum of 14', {'qmax': 14}), ('Maximum of 16', {'qmax': 16}), ('Maximum of 24', {'qmax': 24}), ('Maximum of 30', {'qmax': 30}))))

# 6 ------------------------------------------------------------ rest days between births
LASTB = 'SUMPRODUCT(MAX(({range:births.doula}={in:doula})*{range:births.date}))'
NEXTW = 'SUMPRODUCT(MIN(({range:oncall.doula}={in:doula})*({range:oncall.oncall_start}>={today})*({range:oncall.attended_on}=0)*{range:oncall.oncall_start}+(1-({range:oncall.doula}={in:doula})*({range:oncall.oncall_start}>={today})*({range:oncall.attended_on}=0))*99999))'
tools.append(TOOL('rest_tool', 'Rest Days Check', 'Has a doula had enough rest days since the last birth',
    'Pick a doula and the fewest rest days between two births: the last birth attended, the full rest days since, the next on-call window and how often rest was too short in 12 months; read from Rest Days Between Births.', [
    IL('doula', 'Doula who attended', 'attender', 'Sven Lindqvist'), I('minrest', 'Fewest rest days between two births', 3, 'int')], [
    O('Last birth attended', 'date', LASTB), O('Days since the last birth', 'int', '{today}-%s' % LASTB), O('Full rest days since', 'int', 'MAX(0,{today}-%s-1)' % LASTB),
    O('Rest days still needed', 'int', 'MAX(0,{in:minrest}-MAX(0,{today}-%s-1))' % LASTB), O('Next on-call window starts', 'date', 'IF(%s>=99999,"",%s)' % (NEXTW, NEXTW)),
    O('Rest days before that window', 'int', 'IF(%s>=99999,0,%s-%s-1)' % (NEXTW, NEXTW, LASTB)),
    O('Births with too little rest, 12 months', 'int', 'COUNTIFS({range:rest.doula},{in:doula},{range:rest.flag},%s,%s)' % (ca('Too little rest'), DM('rest.date', 12))),
    O('Births after an earlier birth, 12 months', 'int', 'COUNTIFS({range:rest.doula},{in:doula},%s)' % DM('rest.date', 12)),
    O('Average rest days between births', 'num', 'IFERROR(AVERAGEIFS({range:rest.rest_days},{range:rest.doula},{in:doula}),0)'),
    O('Agency births with too little rest, 12 months', 'int', 'COUNTIFS({range:rest.flag},%s,%s)' % (ca('Too little rest'), DM('rest.date', 12))),
    O('Verdict', 'text', 'IF(MAX(0,{today}-%s-1)<{in:minrest},%s&": "&MAX(0,{in:minrest}-MAX(0,{today}-%s-1)),%s)' % (LASTB, c2('Give rest days'), LASTB, c2('Enough rest')))],
    GR('What if', ('Minimum of 1 rest day', {'minrest': 1}), ('Minimum of 2 rest days', {'minrest': 2}), ('Minimum of 4 rest days', {'minrest': 4}), ('Minimum of 7 rest days', {'minrest': 7}), ('Minimum of 10 rest days', {'minrest': 10}))))

# 7 ------------------------------------------------------------ visit hours by kind
KH = lambda k, a, b: 'SUMIFS({range:visits.hours},{range:visits.kind},%s,{range:visits.date},">"&EDATE({today},-%s),{range:visits.date},"<="&EDATE({today},-%s))' % (k, a, b)
TH_ = lambda a, b: 'SUMIFS({range:visits.hours},{range:visits.date},">"&EDATE({today},-%s),{range:visits.date},"<="&EDATE({today},-%s))' % (a, b)
CHG = lambda k: 'IFERROR(%s/%s-%s/%s,0)' % (KH(k, '{in:months}', 0), TH_('{in:months}', 0), KH(k, '2*{in:months}', '{in:months}'), TH_('2*{in:months}', '{in:months}'))
tools.append(TOOL('kind_mix', 'Visit Hours by Kind', 'Which kind of visit takes a growing share of the hours',
    'Pick a kind of visit and the months to compare: its share of all visit hours now and in the months before, the change for all four kinds and the verdict; read from Visits.', [
    IL('kind', 'Kind of visit', 'vkind', 'Night shift'), I('months', 'Months in each period', 3, 'int')], [
    O('Visit hours now, all kinds', 'num', TH_('{in:months}', 0)), O('Visit hours in the period before, all kinds', 'num', TH_('2*{in:months}', '{in:months}')),
    O('Hours of this kind now', 'num', KH('{in:kind}', '{in:months}', 0)), O('Hours of this kind before', 'num', KH('{in:kind}', '2*{in:months}', '{in:months}')),
    O('Share of this kind now', 'pct', 'IFERROR(%s/%s,0)' % (KH('{in:kind}', '{in:months}', 0), TH_('{in:months}', 0))), O('Share of this kind before', 'pct', 'IFERROR(%s/%s,0)' % (KH('{in:kind}', '2*{in:months}', '{in:months}'), TH_('2*{in:months}', '{in:months}'))),
    O('Change in share, prenatal visits', 'pct', CHG(PRE)), O('Change in share, postpartum visits', 'pct', CHG(PPV)), O('Change in share, night shifts', 'pct', CHG(NIGHT)), O('Change in share, debrief visits', 'pct', CHG(DEB)),
    O('Verdict', 'text', 'IF(%s<=0.01,%s,IF({in:kind}=%s,%s,IF({in:kind}=%s,%s,IF({in:kind}=%s,%s,%s))))' % (CHG('{in:kind}'), c2('Mix is steady'), PRE, c2('Prenatal share grows'), PPV, c2('Postpartum share grows'), NIGHT, c2('Night share grows'), c2('Debrief share grows')))],
    GR('What if', ('Prenatal visits', {'kind': '=' + PRE}), ('Postpartum visits', {'kind': '=' + PPV}), ('Debrief visits', {'kind': '=' + DEB}), ('Night shifts, 2 months', {'months': 2}), ('Night shifts, 6 months', {'months': 6}))))

# 8 ------------------------------------------------------------ pack expiry planner
P1 = '{range:ledger.days_to_expiry},">=0",{range:ledger.days_to_expiry},"<="&{in:d1},{range:ledger.hours_left},">0"'
P2 = '{range:ledger.days_to_expiry},">=0",{range:ledger.days_to_expiry},"<="&{in:d2},{range:ledger.hours_left},">0"'
H1 = 'SUMIFS({range:ledger.hours_left},%s)' % P1; N1 = 'COUNTIFS(%s)' % P1
WK1 = 'IFERROR(AVERAGEIFS({range:ledger.days_to_expiry},%s)/7,0)' % P1
NEED = 'IFERROR((%s/%s)/{in:len}/MAX(1,%s),0)' % (H1, N1, WK1)
BOOKABLE = 'MIN(%s,%s*{in:maxv}*{in:len}*%s)' % (H1, N1, WK1)
tools.append(TOOL('expiry_planner', 'Pack Expiry Planner', 'Can the hours left on packs ending soon still be booked',
    'Type the two day limits, a typical visit length and the visits a week a client will take: the packs ending in each limit, the hours left, the visits a week needed and the hours that will lapse; read from Hour Pack Ledger.', [
    I('d1', 'First limit, days', 30, 'int'), I('d2', 'Second limit, days', 60, 'int'), I('len', 'Typical visit length, hours', 4), I('maxv', 'Visits a week a client will take', 2)], [
    O('Packs ending in the first limit with hours left', 'int', N1), O('Hours left on those packs', 'num', H1), O('Value of those hours', 'money', 'SUMIFS({range:ledger.value_left},%s)' % P1),
    O('Packs ending in the second limit with hours left', 'int', 'COUNTIFS(%s)' % P2), O('Hours left on those packs, second limit', 'num', 'SUMIFS({range:ledger.hours_left},%s)' % P2),
    O('Average weeks left on the first group', 'num', WK1), O('Visits a week needed per pack, first group', 'num', NEED), O('Hours that can still be booked, first group', 'num', BOOKABLE),
    O('Hours that will lapse, first group', 'num', 'MAX(0,%s-%s)' % (H1, BOOKABLE)), O('Pack with the most hours left, ending soon', 'text', 'IFERROR(INDEX({range:ledger.client},MATCH(MAX({range:ledger.soon_hours}),{range:ledger.soon_hours},0)),"")'),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s<={in:maxv},%s&": "&ROUND(%s,1),%s&": "&ROUND(MAX(0,%s-%s),0)))' % (N1, c2('No pack ends soon'), NEED, c2('Book visits now'), NEED, c2('Let hours lapse'), H1, BOOKABLE))],
    GR('What if', ('Clients take 1 visit a week', {'maxv': 1}), ('Clients take 3 visits a week', {'maxv': 3}), ('Visits of 3 hours', {'len': 3}), ('Visits of 6 hours', {'len': 6}), ('Look 14 days ahead', {'d1': 14}))))

# 9 ------------------------------------------------------------ pack pace check
CLP = 'IFERROR(INDEX({range:packs.client},MATCH({in:pack},{range:packs.pack_id},0)),"")'
PKV = lambda c: 'IFERROR(INDEX({range:packs.%s},MATCH({in:pack},{range:packs.pack_id},0)),0)' % c
CND = '({range:visits.client}=%s)*({range:visits.kind}<>%s)' % (CLP, PRE)
FIRSTV = 'SUMPRODUCT(MIN(%s*{range:visits.date}+(1-%s)*99999))' % (CND, CND)
USED = PKV('hours_used'); BOUGHT = PKV('hours_bought'); EXP = PKV('expires_on')
EXPECT = '%s*MIN(1,MAX(0,{today}-%s)/MAX(1,%s-%s))' % (BOUGHT, FIRSTV, EXP, FIRSTV)
tools.append(TOOL('pace_check', 'Pack Pace Check', 'Will this pack be used before it ends',
    'Type a pack ID and the hours of slack you accept: hours used per week since the first visit against the pace needed to finish, and the hours behind a straight line from the first visit to the expiry; read from Hour Packs and Visits.', [
    I('pack', 'Pack ID', D.DEF_PACK, 'text'), I('slack', 'Hours behind that you accept', 4)], [
    O('Client', 'text', CLP), O('Hours bought', 'num', BOUGHT), O('Hours used', 'num', USED), O('Hours left', 'num', 'MAX(0,%s-%s)' % (BOUGHT, USED)), O('Expires on', 'date', EXP), O('Days to expiry', 'int', '%s-{today}' % EXP),
    O('First postpartum visit', 'date', 'IF(%s>=99999,"",%s)' % (FIRSTV, FIRSTV)), O('Weeks since the first visit', 'num', 'IF(%s>=99999,0,({today}-%s)/7)' % (FIRSTV, FIRSTV)),
    O('Hours used per week so far', 'num', 'IF(%s>=99999,0,%s/MAX(1,({today}-%s)/7))' % (FIRSTV, USED, FIRSTV)),
    O('Hours a week needed to finish', 'num', 'IF(%s>{today},MAX(0,%s-%s)/MAX(1,(%s-{today})/7),0)' % (EXP, BOUGHT, USED, EXP)),
    O('Hours expected by now on a straight line', 'num', 'IF(%s>=99999,0,%s)' % (FIRSTV, EXPECT)), O('Behind the line by hours', 'num', 'IF(%s>=99999,0,MAX(0,%s-%s))' % (FIRSTV, EXPECT, USED)),
    O('Verdict', 'text', 'IF(%s>=%s,%s,IF(%s<={today},%s,IF(MAX(0,%s-%s)>{in:slack},%s&": "&ROUND(%s-%s,0),%s)))' % (USED, BOUGHT, c3('Pack finished'), EXP, c3('Behind pace'), EXPECT, USED, c3('Behind pace'), EXPECT, USED, c3('On pace')))],
    GR('What if', ('Accept 2 hours behind', {'slack': 2}), ('Accept 8 hours behind', {'slack': 8}), ('Accept 20 hours behind', {'slack': 20}), ('Accept 40 hours behind', {'slack': 40}), ('Accept 80 hours behind', {'slack': 80}))))

# 10 ----------------------------------------------------------- invoice-ready extra hours
MONTH = 'DATE(YEAR({in:month}),MONTH({in:month}),1)'
XM = lambda a, b: 'SUMIFS({range:ledger.extra_hours},{range:ledger.expires_on},">="&%s,{range:ledger.expires_on},"<"&%s)' % (a, b)
ALLX = 'SUMIFS({range:ledger.extra_hours},{range:ledger.to_invoice},1)'
tools.append(TOOL('extra_invoice', 'Extra Hours Invoice', 'How much extra postpartum time is ready to invoice',
    'Pick a month and the rate for extra hours (hours beyond the pack): the extra hours of packs ending in that month, the ones still not invoiced, the monthly average and the same month last year; read from Hour Pack Ledger.', [
    I('month', 'Month to check', 'today-120', 'date'), I('rate', 'Rate for extra hours, per hour', 40, 'money')], [
    O('Extra hours, packs ending in the month', 'num', XM(MONTH, 'EDATE(%s,1)' % MONTH)), O('Amount for that month', 'money', '%s*{in:rate}' % XM(MONTH, 'EDATE(%s,1)' % MONTH)),
    O('Packs with extra hours in the month', 'int', 'COUNTIFS({range:ledger.expires_on},">="&%s,{range:ledger.expires_on},"<"&EDATE(%s,1),{range:ledger.extra_hours},">0")' % (MONTH, MONTH)),
    O('Monthly average of the 3 months before', 'num', '%s/3' % XM('EDATE(%s,-3)' % MONTH, MONTH)), O('Same month last year', 'num', XM('EDATE(%s,-12)' % MONTH, 'EDATE(%s,-11)' % MONTH)),
    O('Extra hours not yet invoiced, all packs', 'num', ALLX), O('Invoice-ready amount, all packs', 'money', '%s*{in:rate}' % ALLX), O('Packs still to invoice', 'int', 'COUNTIFS({range:ledger.to_invoice},1)'),
    O('Average extra hours per pack with extra hours', 'num', 'IFERROR(AVERAGEIFS({range:ledger.extra_hours},{range:ledger.extra_hours},">0"),0)'),
    O('Share of packs that run over', 'pct', 'IFERROR(COUNTIFS({range:ledger.extra_hours},">0")/COUNT({range:ledger.hours_bought}),0)'),
    O('Verdict', 'text', 'IF(%s>0,%s&": "&ROUND(%s*{in:rate},0),%s)' % (ALLX, c3('Invoice now'), ALLX, c3('Nothing to invoice')))],
    GR('What if', ('Rate 35 an hour', {'rate': 35}), ('Rate 45 an hour', {'rate': 45}), ('Rate 50 an hour', {'rate': 50}), ('A month 6 months ago', {'month': '={today}-180'}), ('A month a year ago', {'month': '={today}-365'}))))

# 11 ----------------------------------------------------------- visit length check
VL = '{range:visits.kind},{in:kind},%s' % DM('visits.date', '{in:months}')
SH = '%s,{range:visits.hours},"<"&{in:minh}' % VL
tools.append(TOOL('length_check', 'Visit Length Check', 'Do short visits cost more in travel than they earn',
    'Pick a kind of visit, the minimum booking in hours and the months to look back: how many visits are shorter than the minimum, the miles and mileage cost spent on them and a verdict on setting a minimum; read from Visits.', [
    IL('kind', 'Kind of visit', 'vkind', 'Postpartum visit'), I('minh', 'Minimum booking, hours', 4), I('months', 'Months to look back', 3, 'int'), I('maxs', 'Share of short visits that you accept', 0.10, 'pct')], [
    O('Visits of this kind', 'int', 'COUNTIFS(%s)' % VL), O('Average hours per visit', 'num', 'IFERROR(AVERAGEIFS({range:visits.hours},%s),0)' % VL), O('Visits shorter than the minimum', 'int', 'COUNTIFS(%s)' % SH),
    O('Share of short visits', 'pct', 'IFERROR(COUNTIFS(%s)/COUNTIFS(%s),0)' % (SH, VL)), O('Hours on short visits', 'num', 'SUMIFS({range:visits.hours},%s)' % SH), O('Miles on short visits', 'num', 'SUMIFS({range:visits.miles},%s)' % SH),
    O('Mileage cost on short visits', 'money', 'SUMIFS({range:visits.mileage_cost},%s)' % SH), O('Mileage cost per hour, short visits', 'money', 'IFERROR(SUMIFS({range:visits.mileage_cost},%s)/SUMIFS({range:visits.hours},%s),0)' % (SH, SH)),
    O('Mileage cost per hour, all visits of the kind', 'money', 'IFERROR(SUMIFS({range:visits.mileage_cost},%s)/SUMIFS({range:visits.hours},%s),0)' % (VL, VL)),
    O('Mileage cost per short visit', 'money', 'IFERROR(SUMIFS({range:visits.mileage_cost},%s)/COUNTIFS(%s),0)' % (SH, SH)), O('Share you accept', 'pct', '{in:maxs}'),
    O('Verdict', 'text', 'IF(IFERROR(COUNTIFS(%s)/COUNTIFS(%s),0)>{in:maxs},%s,%s)' % (SH, VL, c3('Set a minimum'), c3('Visit length is fine')))],
    GR('What if', ('Minimum of 3 hours', {'minh': 3}), ('Minimum of 5 hours', {'minh': 5}), ('Accept 20% short', {'maxs': 0.20}), ('Look back 6 months', {'months': 6}), ('Look back 12 months', {'months': 12}))))

# 12 ----------------------------------------------------------- area clustering
def WD(n): return 'COUNTIFS({range:visits.area},{in:area},{range:visits.weekday},%d,%s)' % (n, DW('visits.date', '{in:days}'))
ENC = 'MAX(%s)' % ','.join('10*%s+%d' % (WD(n), 8 - n) for n in range(1, 8))
WDL = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
AV = 'COUNTIFS({range:visits.area},{in:area},%s)' % DW('visits.date', '{in:days}')
tools.append(TOOL('area_cluster', 'Area Clustering', 'Which weekday should visits in one area be grouped on',
    'Pick an area and the days to look back: visits by weekday, the busiest weekday and the miles and mileage cost that would be saved if mixed days were grouped on it; read from Visits.', [
    IL('area', 'Area', 'area', 'Southbank'), I('days', 'Days to look back', 120, 'int'), I('saving', 'Share of miles saved when visits are grouped', 0.35, 'pct')], [
    O('Visits in the area', 'int', AV)] + [O('Visits on %s' % d.capitalize(), 'int', WD(i + 1)) for i, d in enumerate(WDL)] + [
    O('Busiest weekday', 'text', 'IF(%s=0,"",CHOOSE(8-MOD(%s,10),%s))' % (AV, ENC, ','.join(LV('wday', d) for d in WDL))), O('Visits on the busiest weekday', 'int', 'INT(%s/10)' % ENC),
    O('Share on the busiest weekday', 'pct', 'IFERROR(INT(%s/10)/%s,0)' % (ENC, AV)), O('Average miles per visit in the area', 'num', 'IFERROR(AVERAGEIFS({range:visits.miles},{range:visits.area},{in:area},%s),0)' % DW('visits.date', '{in:days}')),
    O('Miles saved if mixed days were grouped', 'num', '(%s-INT(%s/10))*IFERROR(AVERAGEIFS({range:visits.miles},{range:visits.area},{in:area},%s),0)*{in:saving}' % (AV, ENC, DW('visits.date', '{in:days}'))),
    O('Mileage cost saved', 'money', '(%s-INT(%s/10))*IFERROR(AVERAGEIFS({range:visits.miles},{range:visits.area},{in:area},%s),0)*{in:saving}*SUMIFS({range:areas.mileage_rate},{range:areas.area},{in:area},{range:areas.in_use},1)' % (AV, ENC, DW('visits.date', '{in:days}'))),
    O('Verdict', 'text', 'IF(IFERROR(INT(%s/10)/%s,0)>=0.3,%s,IF({in:area}=%s,%s,%s))' % (ENC, AV, c3('Visits already clustered'), tok('area', 'Northgate'), c3('Cluster Northgate visits'), c3('Cluster Southbank visits')))],
    GR('What if', ('Northgate', {'area': '=' + tok('area', 'Northgate')}), ('Last 30 days', {'days': 30}), ('Last 60 days', {'days': 60}), ('Last 365 days', {'days': 365}), ('Saving of 50%', {'saving': 0.5}))))

# 13 ----------------------------------------------------------- birth hours spread
BP = '{range:births.package},{in:package}'
PLAN = 'IFERROR(INDEX({range:packages.birth_hours},MATCH({in:package},{range:packages.package},0)),0)'
AVGB = 'IFERROR(AVERAGEIFS({range:births.hours},%s),0)' % BP
tools.append(TOOL('birth_spread', 'Birth Hours Spread', 'Does the planned birth time of a package match the hours attended',
    'Pick a birth package and the margin you accept: the births in that package, the hours attended against the hours the package plans, the longest and shortest births and the hours to plan; read from Births Attended and Packages.', [
    IL('package', 'Birth package', 'bpack', 'Birth Essential'), I('tol', 'Margin over the average that you accept', 0.10, 'pct')], [
    O('Births in the package', 'int', 'COUNTIFS(%s)' % BP), O('Planned birth hours', 'num', PLAN), O('Average hours attended', 'num', AVGB),
    O('Longest birth attended', 'num', 'SUMPRODUCT(MAX(({range:births.package}={in:package})*{range:births.hours}))'),
    O('Shortest birth attended', 'num', 'IF(COUNTIFS(%s)=0,0,SUMPRODUCT(MIN(({range:births.package}={in:package})*{range:births.hours}+(1-({range:births.package}={in:package}))*99999)))' % BP),
    O('Births longer than the plan', 'int', 'COUNTIFS(%s,{range:births.hours},">"&%s)' % (BP, PLAN)), O('Share longer than the plan', 'pct', 'IFERROR(COUNTIFS(%s,{range:births.hours},">"&%s)/COUNTIFS(%s),0)' % (BP, PLAN, BP)),
    O('Average less the plan, hours', 'num', '%s-%s' % (AVGB, PLAN)), O('Hours to plan at the average plus the margin', 'num', 'ROUNDUP(%s*(1+{in:tol}),0)' % AVGB),
    O('Average hours attended, all births', 'num', 'IFERROR(AVERAGE({range:births.hours}),0)'),
    O('Verdict', 'text', 'IF(%s*(1+{in:tol})>%s,%s&": "&ROUNDUP(%s*(1+{in:tol}),0),%s)' % (AVGB, PLAN, c3('Plan more birth hours'), AVGB, c3('Plan holds')))],
    GR('What if', ('Birth Plus', {'package': '=' + tok('bpack', 'Birth Plus')}), ('Birth Premier', {'package': '=' + tok('bpack', 'Birth Premier')}), ('Combined Essential', {'package': '=' + tok('bpack', 'Combined Essential')}),
       ('Complete Care Bundle', {'package': '=' + tok('bpack', 'Complete Care Bundle')}), ('Margin of 40%', {'tol': 0.40}))))

# 14 ----------------------------------------------------------- call-to-arrival time
BD = '{range:births.doula},{in:doula}'
LONGEST = 'ROUND(SUMPRODUCT(MAX(({range:births.doula}={in:doula})*MOD({range:births.arrive_time}-{range:births.call_time},1)*1440)),0)'
tools.append(TOOL('arrival_tool', 'Call-to-Arrival Time', 'How fast does each doula arrive after a call',
    'Pick a doula and the longest wanted time from the call to the arrival in minutes: the average and longest time, the share of calls inside the limit and night against day calls; read from Births Attended (times only).', [
    IL('doula', 'Doula who attended', 'attender', 'Amara Okonkwo'), I('limit', 'Longest wanted time to arrive, minutes', 75, 'int')], [
    O('Births attended by this doula', 'int', 'COUNTIFS(%s)' % BD), O('Average minutes to arrive, this doula', 'num', 'IFERROR(AVERAGEIFS({range:births.arrive_min},%s),0)' % BD), O('Longest time to arrive, this doula', 'int', LONGEST),
    O('Share of calls inside the limit, this doula', 'pct', 'IFERROR(COUNTIFS(%s,{range:births.arrive_min},"<="&{in:limit})/COUNTIFS(%s),0)' % (BD, BD)),
    O('Average minutes to arrive, all births', 'num', 'IFERROR(AVERAGE({range:births.arrive_min}),0)'), O('Average minutes at night, all births', 'num', 'IFERROR(AVERAGEIFS({range:births.arrive_min},{range:births.night_call},1),0)'),
    O('Average minutes by day, all births', 'num', 'IFERROR(AVERAGEIFS({range:births.arrive_min},{range:births.night_call},0),0)'),
    O('Share of all calls inside the limit', 'pct', 'IFERROR(COUNTIFS({range:births.arrive_min},"<="&{in:limit})/COUNT({range:births.arrive_min}),0)'),
    O('Longest wanted time', 'int', '{in:limit}'),
    O('Verdict', 'text', 'IF(IFERROR(AVERAGEIFS({range:births.arrive_min},%s),0)>{in:limit},%s&": "&{in:limit},%s)' % (BD, c3('Keep arrival under the limit'), c3('Arrival time is fine')))],
    GR('What if', ('Limit of 60 minutes', {'limit': 60}), ('Limit of 70 minutes', {'limit': 70}), ('Limit of 80 minutes', {'limit': 80}), ('Limit of 90 minutes', {'limit': 90}), ('Limit of 110 minutes', {'limit': 110}))))

# 15 ----------------------------------------------------------- night work load
NS = 'COUNTIFS({range:visits.doula},{in:doula},{range:visits.kind},%s,%s)' % (NIGHT, DW('visits.date', '{in:days}'))
NC = 'COUNTIFS({range:births.doula},{in:doula},{range:births.night_call},1,%s)' % DW('births.date', '{in:days}')
TEAMN = '(COUNTIFS({range:visits.kind},%s,%s)+COUNTIFS({range:births.night_call},1,%s))' % (NIGHT, DW('visits.date', '{in:days}'), DW('births.date', '{in:days}'))
tools.append(TOOL('night_tool', 'Night Work Load', 'Is night work spread fairly between the doulas',
    'Pick a doula and the days to look back: night shifts and night calls (between 22:00 and 06:00), the count per 30 days against your limit and the share of the team\'s night work; read from Visits and Births Attended.', [
    IL('doula', 'Doula who attended', 'attender', D.DEF_NIGHT), I('days', 'Days to look back', 90, 'int'), I('maxn', 'Most nights for one doula in 30 days', 3, 'int')], [
    O('Night shifts', 'int', NS), O('Night calls', 'int', NC), O('Night shifts and calls together', 'int', '%s+%s' % (NS, NC)), O('Per 30 days', 'num', '(%s+%s)*30/{in:days}' % (NS, NC)),
    O('Night work of the whole team', 'int', TEAMN), O('Share of the team night work', 'pct', 'IFERROR((%s+%s)/%s,0)' % (NS, NC, TEAMN)), O('Fair share for 7 doulas', 'pct', '1/7'),
    O('Limit per 30 days', 'int', '{in:maxn}'), O('Night work of this doula over the limit', 'num', 'MAX(0,(%s+%s)*30/{in:days}-{in:maxn})' % (NS, NC)),
    O('Verdict', 'text', 'IF(OR((%s+%s)*30/{in:days}>{in:maxn},IFERROR((%s+%s)/%s,0)>2/7),%s,%s)' % (NS, NC, NS, NC, TEAMN, c3('Rotate night work'), c3('Night work is fine')))],
    GR('What if', ('Limit of 1 night', {'maxn': 1}), ('Limit of 2 nights', {'maxn': 2}), ('Limit of 5 nights', {'maxn': 5}), ('Look back 30 days', {'days': 30}), ('Look back 180 days', {'days': 180}))))

# 16 ----------------------------------------------------------- prenatal visit timing
CM = 'MATCH({in:client},{range:clients.client},0)'
def CL_(c): return 'IFERROR(INDEX({range:clients.%s},%s),0)' % (c, CM)
LEFT = CL_('prenatal_left'); ONC = CL_('oncall_start'); LATEST = '(%s-{in:gap})' % ONC
DUEBY = 'IF(%s=0,"",MIN(%s,{today}+ROUND(MAX(0,%s-{today})/%s,0)))' % (LEFT, LATEST, LATEST, LEFT)
tools.append(TOOL('prenatal_timing', 'Prenatal Visit Timing', 'When must the next prenatal visit be booked',
    'Type a client and the days before the on-call start by which the last prenatal visit should be done: visits planned and done, the days left and the date to book the next one; read from Clients.', [
    I('client', 'Client', D.DEF_TIMING, 'text'), I('gap', 'Days before the on-call start for the last visit', 7, 'int')], [
    O('Package', 'text', 'IFERROR(INDEX({range:clients.package},%s)&"","")' % CM), O('Signed on', 'date', CL_('signed_on')), O('Estimated due date', 'date', CL_('edd')), O('On-call start', 'date', ONC),
    O('Days from signing to the on-call start', 'int', '%s-%s' % (ONC, CL_('signed_on'))), O('Prenatal visits planned', 'int', CL_('prenatal_plan')), O('Prenatal visits done', 'int', CL_('prenatal_n')), O('Prenatal visits left', 'int', LEFT),
    O('Days left before the last visit is due', 'int', 'MAX(0,%s-{today})' % LATEST), O('Visit number to book', 'int', CL_('prenatal_no')), O('Book the next visit by', 'date', DUEBY),
    O('Next visit already booked', 'date', 'IF(%s=0,"",%s)' % (CL_('next_visit'), CL_('next_visit'))),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s<{today},%s,IF(AND(%s>0,%s<=%s),%s,IF(%s-{today}<=14,%s,%s))))' % (LEFT, c3('Prenatal visits are done'), DUEBY, c3('Visit is overdue'), CL_('next_visit'), CL_('next_visit'), DUEBY, c3('Visit is on time'), DUEBY, c3('Book the visit now'), c3('Visit is on time')))],
    GR('What if', ('Last visit 3 days before', {'gap': 3}), ('Last visit 14 days before', {'gap': 14}), ('Last visit 21 days before', {'gap': 21}), ('Last visit 30 days before', {'gap': 30}), ('Last visit 60 days before', {'gap': 60}))))

# 17 ----------------------------------------------------------- hours forecast next 4 weeks
FAC = 'IF({in:scenario}=%s,1,IF({in:scenario}=%s,0.9,1.25))' % (tok('scen', 'Base'), tok('scen', 'Best'))
AVGBH = 'IFERROR(AVERAGEIFS({range:births.hours},%s),0)' % DM('births.date', 12)
AVGPV = 'IFERROR(AVERAGEIFS({range:visits.hours},{range:visits.kind},%s,%s),0)' % (PRE, DM('visits.date', 12))
def WK(k):
    ws = '(%s+%d)' % (THISMON, 7 * k)
    return '((SUM({range:ledger.pace_week})*{in:use}+COUNTIFS({range:oncall.oncall_start},"<="&(%s+6),{range:oncall.oncall_end},">="&%s,{range:oncall.attended_on},"")*7/29*%s+COUNTIFS({range:clients.next_visit},">="&%s,{range:clients.next_visit},"<="&(%s+6),{range:clients.next_kind},%s)*%s)*%s)' % (ws, ws, AVGBH, ws, ws, PRE, AVGPV, FAC)
def _onc(k):
    ws = '(%s+%d)' % (THISMON, 7 * k)
    return 'COUNTIFS({range:oncall.oncall_start},"<="&(%s+6),{range:oncall.oncall_end},">="&%s,{range:oncall.attended_on},"")' % (ws, ws)
X4 = '(%s*(4*SUM({range:ledger.pace_week})*{in:use}+%s*7/29*(%s)+%s*COUNTIFS({range:clients.next_visit},">="&(%s+7),{range:clients.next_visit},"<="&(%s+34),{range:clients.next_kind},%s)))' % (FAC, AVGBH, '+'.join(_onc(k) for k in (1, 2, 3, 4)), AVGPV, THISMON, THISMON, PRE)
tools.append(TOOL('hours_forecast', 'Hours Forecast', 'How many hours will the team work in the next 4 weeks',
    'Pick Base, Best or Worst and the share of the pack pace that clients book: open packs, on-call windows and booked prenatal visits become expected hours for each of the next 4 weeks, set against the team cap.', [
    IL('scenario', 'Scenario', 'scen', 'Base'), I('use', 'Share of the needed pack pace that clients book', 0.9, 'pct')], [
    O('Hours, next week', 'num', WK(1)), O('Hours, week 2', 'num', WK(2)), O('Hours, week 3', 'num', WK(3)), O('Hours, week 4', 'num', WK(4)),
    O('Hours, next 4 weeks', 'num', X4), O('Average hours a week', 'num', '%s/4' % X4),
    O('Team cap, hours a week', 'num', 'SUM({range:team.cap})'), O('Actual average, last 4 weeks', 'num', 'IFERROR(AVERAGEIFS({range:wk_all.total_hours},{range:wk_all.week},">="&({today}-28)),0)'),
    O('Pack hours a week if clients follow the pace', 'num', 'SUM({range:ledger.pace_week})'),
    O('Windows open in the next 4 weeks', 'int', 'COUNTIFS({range:oncall.oncall_start},"<="&(%s+34),{range:oncall.oncall_end},">="&(%s+7),{range:oncall.attended_on},"")' % (THISMON, THISMON)),
    O('Share of the cap', 'pct', 'IFERROR(%s/4/SUM({range:team.cap}),0)' % X4),
    O('Verdict', 'text', 'IF(%s/4>0.9*SUM({range:team.cap}),%s,IF(%s/4>0.7*SUM({range:team.cap}),%s,%s))&": "&ROUND(%s/4,0)' % (X4, c3('Over capacity'), X4, c3('Near capacity'), c3('Room for more'), X4))],
    GR('What if', ('Best case', {'scenario': '=' + tok('scen', 'Best')}), ('Worst case', {'scenario': '=' + tok('scen', 'Worst')}), ('Clients book 50% of the pace', {'use': 0.5}), ('Clients book 70% of the pace', {'use': 0.7}), ('Clients book all of the pace', {'use': 1.0}))))

# 18 ----------------------------------------------------------- yearly hours per doula
YV = lambda k: 'SUMIFS({range:visits.hours},{range:visits.doula},{in:doula},{range:visits.kind},%s,%s)' % (k, DM('visits.date', 12))
YB = 'SUMIFS({range:births.hours},{range:births.doula},{in:doula},%s)' % DM('births.date', 12)
YT = '(%s+%s+%s+%s+%s)' % (YV(PRE), YV(PPV), YV(NIGHT), YV(DEB), YB)
tools.append(TOOL('yearly_hours', 'Yearly Hours per Doula', 'How much of its yearly capacity each doula uses',
    'Pick a doula and the weekly cap: the hours of the last 12 months by phase against the cap times 52 weeks, the spare hours a week and the share of all team hours; read from Visits and Births Attended.', [
    IL('doula', 'Doula', 'doula', 'Sven Lindqvist'), I('cap', 'Weekly hours cap', 24), I('high', 'Share of capacity that counts as full', 0.85, 'pct'), I('low', 'Share of capacity that counts as busy', 0.6, 'pct')], [
    O('Prenatal visit hours', 'num', YV(PRE)), O('Postpartum visit hours', 'num', YV(PPV)), O('Night shift hours', 'num', YV(NIGHT)), O('Debrief visit hours', 'num', YV(DEB)), O('Birth hours attended', 'num', YB),
    O('Total hours, 12 months', 'num', YT), O('Capacity, hours a year', 'num', '{in:cap}*52'), O('Share of capacity used', 'pct', 'IFERROR(%s/({in:cap}*52),0)' % YT), O('Spare hours a week', 'num', '({in:cap}*52-%s)/52' % YT),
    O('Share of all team hours', 'pct', 'IFERROR(%s/(SUMIFS({range:visits.hours},%s)+SUMIFS({range:births.hours},%s)),0)' % (YT, DM('visits.date', 12), DM('births.date', 12))),
    O('Weeks over the cap, last 12 weeks', 'int', 'COUNTIFS({range:wk_doula.doula},{in:doula},{range:wk_doula.week},">="&({today}-84),{range:wk_doula.total_hours},">"&{in:cap})'),
    O('Verdict', 'text', 'IF(IFERROR(%s/({in:cap}*52),0)>{in:high},%s,IF(IFERROR(%s/({in:cap}*52),0)>={in:low},%s,%s))&": "&ROUND(IFERROR(%s/({in:cap}*52),0)*100,0)&"%%"' % (YT, c3('Over capacity'), YT, c3('Near capacity'), c3('Room for more'), YT))],
    GR('What if', ('Cap of 20 hours', {'cap': 20}), ('Cap of 30 hours', {'cap': 30}), ('Cap of 40 hours', {'cap': 40}), ('Full means 70%', {'high': 0.7}), ('Busy means 40%', {'low': 0.4}))))
assert len(tools) == 18, len(tools)
