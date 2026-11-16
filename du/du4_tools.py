"""Doula suite part 4: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du4_lists import *
import du4_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def R(t, c): return '{range:%s.%s}' % (t, c)
OS, OE, OD, OB, OEDD, OCL, OAREA = R('oncall', 'oncall_start'), R('oncall', 'oncall_end'), R('oncall', 'doula'), R('oncall', 'backup'), R('oncall', 'edd'), R('oncall', 'client'), R('oncall', 'area')
DOUS, DCAP = R('doulas', 'doula'), R('doulas', 'cap_births')
TROLE, TNAME = R('team', 'role'), R('team', 'name')
BROLE = tok('role', 'Backup doula'); PP = tok('service', 'Postpartum'); NO = '{list:yesno.no}'; YES = '{list:yesno.yes}'
CAPM_D, CAPM_M = R('capm', 'due_dates'), R('capm', 'month')
T0 = '{today}'
B1, B2 = tok('backup', BACKUP_NAMES[0]), tok('backup', BACKUP_NAMES[1])
tools = []

# 1 ------------------------------------------------------------ on-call forecast
H = '{in:horizon}'
DAYS_IN = '{range:daily.day_no},">=0",{range:daily.day_no},"<="&%s' % H
WK = lambda c, n=1: 'INDEX({range:weekly.%s},MATCH(LARGE({range:weekly.score},%d),{range:weekly.score},0))' % (c, n)
PEAK1 = 'SUMPRODUCT(MAX(({range:daily.day_no}>=0)*({range:daily.day_no}<=%s)*COUNTIFS(%s,"<="&({today}+{range:daily.day_no}),%s,">="&({today}+{range:daily.day_no}))))' % (H, OS, OE)
tools.append(TOOL('forecast', 'On-Call Forecast', 'On-call forecast with the busiest weeks',
    'Type how many days ahead to look (up to 180): clients on call today, the most on call on one day, the days one doula has 2 or more windows, the busiest weeks and a verdict.', [
    I('horizon', 'Days ahead to look', 90, 'int')], [
    O('Clients on call today', 'int', 'COUNTIFS(%s,"<="&%s,%s,">="&%s)' % (OS, T0, OE, T0)),
    O('Windows opening in these days', 'int', 'COUNTIFS(%s,">="&%s,%s,"<="&(%s+%s))' % (OS, T0, OS, T0, H)),
    O('Most clients on call on one day', 'int', PEAK1),
    O('Days with 2 or more windows of one doula', 'int', 'COUNTIFS(%s,{range:daily.two_plus},1)' % DAYS_IN),
    O('Days above the overlap limit', 'int', 'COUNTIFS(%s,{range:daily.limit_flag},%s)' % (DAYS_IN, ck('Over the limit'))),
    O('Busiest week starts', 'date', WK('week')), O('Clients on call that week', 'int', WK('windows_open')), O('Doulas with a window that week', 'int', WK('doulas_open')),
    O('Second busiest week starts', 'date', WK('week', 2)),
    O('Busiest week in words', 'text', '%s&" "&%s&" "&%s' % (c2('Busiest week has'), WK('windows_open'), c2('clients on call'))),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,{range:daily.limit_flag},%s)>0,%s,IF(COUNTIFS(%s,{range:daily.two_plus},1)>0,%s,%s))' % (DAYS_IN, ck('Over the limit'), c2('Over the limit: add cover now'), DAYS_IN, c2('Overlaps ahead: check cover'), c2('No overlap ahead')))],
    GR('What if you look further ahead', ('30 days', {'horizon': 30}), ('60 days', {'horizon': 60}), ('90 days', {'horizon': 90}), ('120 days', {'horizon': 120}), ('180 days', {'horizon': 180}))))

# 2 ------------------------------------------------------------ can I take this client
WS = '({in:edd}-{set:oncall_before_days})'; WE = '({in:edd}+{set:oncall_after_days})'
MST = 'DATE(YEAR({in:edd}),MONTH({in:edd}),1)'; MEN = 'EOMONTH({in:edd},0)'
OWN_OV = 'COUNTIFS(%s,{in:doula},%s,"<="&%s,%s,">="&%s)' % (OD, OS, WE, OE, WS)
OWN_MO = 'COUNTIFS(%s,{in:doula},%s,">="&%s,%s,"<="&%s)' % (OD, OEDD, MST, OEDD, MEN)
OWN_CAP = 'IFERROR(INDEX(%s,MATCH({in:doula},%s,0)),0)' % (DCAP, DOUS)
AG_MO = 'COUNTIFS(%s,">="&%s,%s,"<="&%s)' % (OEDD, MST, OEDD, MEN)
BK_FREE = 'SUMPRODUCT((%s=%s)*(COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s)<{set:backup_load_max}))' % (TROLE, BROLE, OB, TNAME, OS, WE, OE, WS)
OTH_FREE = 'SUMPRODUCT((%s>0)*(%s<>{in:doula})*(COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s)<{set:max_oncall_overlap})*(COUNTIFS(%s,%s,%s,">="&%s,%s,"<="&%s)<%s))' % (DCAP, DOUS, OD, DOUS, OS, WE, OE, WS, OD, DOUS, OEDD, MST, OEDD, MEN, DCAP)
tools.append(TOOL('take_client', 'Can I Take This Client', 'Can I take this client for this due date',
    'Type the estimated due date, the doula and the service: the windows it overlaps, the monthly cap used, whether a backup is free and the verdict (yes, yes with backup booked, decline or waitlist).', [
    I('edd', 'Estimated due date of the new client', D.OV_EDD, 'date'), IL('doula', 'Doula you would assign', 'bdoula', D.OV_DOULA), IL('service', 'Service wanted', 'service', 'Birth')], [
    O('On-call window opens', 'date', WS), O('On-call window closes', 'date', WE),
    O('Windows of this doula already open then', 'int', OWN_OV), O('Due dates of this doula that month', 'int', OWN_MO), O('Cap of this doula for a month', 'int', OWN_CAP),
    O('Due dates of the agency that month', 'int', AG_MO), O('Agency cap for a month', 'int', '{set:agency_cap_month}'),
    O('Other doulas free for this window', 'int', OTH_FREE), O('Backup doulas free for this window', 'int', BK_FREE),
    O('Verdict', 'text', 'IF({in:service}=%s,%s,IF(OR(%s>={set:agency_cap_month},%s>=%s),%s,IF(%s>={set:max_oncall_overlap},%s,IF(%s=0,%s,IF(%s>0,%s,%s)))))' % (
        PP, ck('No window needed'), AG_MO, OWN_MO, OWN_CAP, ck('Decline or waitlist'), OWN_OV, ck('Decline or waitlist'), OWN_OV, ck('Yes'), BK_FREE, ck('Yes with backup booked'), ck('Decline or waitlist')))],
    GR('What if another doula took the client', ('Lucia Ferreira', {'doula': '=' + tok('bdoula', 'Lucia Ferreira')}), ('Priya Raman', {'doula': '=' + tok('bdoula', 'Priya Raman')}), ('Sven Lindqvist', {'doula': '=' + tok('bdoula', 'Sven Lindqvist')}),
       ('Amara Okonkwo', {'doula': '=' + tok('bdoula', 'Amara Okonkwo')}), ('A due date 30 days later', {'edd': '=({in:edd}+30)'}),
       ('Postpartum hours only', {'service': '=' + tok('service', 'Postpartum')}))))

# 3 ------------------------------------------------------------ monthly cap and utilisation
tools.append(TOOL('cap_util', 'Monthly Cap Utilisation', 'Monthly cap and how much of it is used',
    'Type the most due dates the agency takes in a month: due dates booked in the next 12 months, the months left open, the free dates and the verdict, from the Capacity by Month sheet.', [
    I('cap', 'Most due dates the agency takes in a month', 7, 'int')], [
    O('Due dates booked, next 12 months', 'int', 'SUM(%s)' % CAPM_D), O('Months with a free date', 'int', 'COUNTIFS(%s,"<"&{in:cap})' % CAPM_D), O('Months full', 'int', 'COUNTIFS(%s,">="&{in:cap})' % CAPM_D),
    O('Free dates left, next 12 months', 'int', 'COUNTIFS(%s,"<"&{in:cap})*{in:cap}-SUMIFS(%s,%s,"<"&{in:cap})' % (CAPM_D, CAPM_D, CAPM_D)),
    O('Cap used, next 12 months', 'pct', 'IFERROR(SUM(%s)/(COUNT(%s)*{in:cap}),0)' % (CAPM_D, CAPM_D)),
    O('Busiest month has this many due dates', 'int', 'MAX(%s)' % CAPM_D), O('Busiest month', 'date', 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (CAPM_M, CAPM_D, CAPM_D)),
    O('First month with a free date', 'date', 'IFERROR(INDEX(%s,MATCH(1,INDEX((%s<{in:cap})*(%s>0),0),0)),{today})' % (CAPM_M, CAPM_D, CAPM_M)),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,"<"&{in:cap})=0,%s,IF(COUNTIFS(%s,"<"&{in:cap})<=3,%s,%s))' % (CAPM_D, c2('Fully booked: waitlist only'), CAPM_D, c2('Few months open: sell now'), c2('Months open: keep selling')))],
    GR('What if the cap changes', ('Cap 4', {'cap': 4}), ('Cap 5', {'cap': 5}), ('Cap 6', {'cap': 6}), ('Cap 7', {'cap': 7}), ('Cap 8', {'cap': 8}), ('Cap 10', {'cap': 10}))))

# 4 ------------------------------------------------------------ overlap scenario test
MSI = 'DATE(YEAR({in:month}),MONTH({in:month}),1)'
CNTX = 'COUNTIFS(%s,%s,%s,">="&%s,%s,"<="&EOMONTH(%s,0))' % (OD, DOUS, OEDD, MSI, OEDD, MSI)
EXTRA = 'SUMPRODUCT((%s>1)*(%s-1))' % (CNTX, CNTX)
tools.append(TOOL('overlap_test', 'Overlap Scenario Test', 'What if every client due in the month is attended in 7 days',
    'Pick a month and type the backups you have: all due dates are treated as births in the same 7 days; each doula attends one, the rest need a backup; see the shortfall and the verdict.', [
    I('month', 'Month to test', D.OV_MONTH, 'date'), I('backups', 'Backup doulas you can call', 2, 'int')], [
    O('Due dates in the month', 'int', 'COUNTIFS(%s,">="&%s,%s,"<="&EOMONTH(%s,0))' % (OEDD, MSI, OEDD, MSI)), O('Doulas with a due date', 'int', 'SUMPRODUCT(--(%s>0))' % CNTX),
    O('Most due dates of one doula', 'int', 'SUMPRODUCT(MAX(%s))' % CNTX), O('Doulas above their own monthly cap', 'int', 'SUMPRODUCT((%s>%s)*(%s>0))' % (CNTX, DCAP, DCAP)),
    O('Births that need a backup', 'int', EXTRA), O('Backup doulas you can call', 'int', '{in:backups}'), O('Short by', 'int', 'MAX(0,%s-{in:backups})' % EXTRA),
    O('Verdict', 'text', 'IF(%s>{in:backups},%s&" "&(%s-{in:backups}),%s)' % (EXTRA, c2('Short of backups by'), EXTRA, ck('Backup is enough')))],
    GR('What if you had more backups', ('No backup', {'backups': 0}), ('1 backup', {'backups': 1}), ('2 backups', {'backups': 2}), ('3 backups', {'backups': 3}), ('4 backups', {'backups': 4}))))

# 5 ------------------------------------------------------------ backup cover verdict
OPEN_IN = '%s,">="&%s,%s,"<="&(%s+{in:days})' % (OS, T0, OS, T0)
tools.append(TOOL('cover_tool', 'Backup Cover Verdict', 'Is every window opening soon covered by a backup',
    'Type the days ahead and the most windows one backup can carry in a week: windows without a backup, backups over the load limit, the soonest uncovered client and the verdict.', [
    I('days', 'Days ahead to check', 90, 'int'), I('load_max', 'Most windows a backup carries in a week', 4, 'int')], [
    O('Windows opening in these days', 'int', 'COUNTIFS(%s)' % OPEN_IN), O('Windows with a backup named', 'int', 'COUNTIFS(%s,%s,"<>")' % (OPEN_IN, OB)),
    O('Windows without a backup', 'int', 'COUNTIFS(%s,%s,"")' % (OPEN_IN, OB)),
    O('Share of windows covered', 'pct', 'IFERROR(COUNTIFS(%s,%s,"<>")/COUNTIFS(%s),0)' % (OPEN_IN, OB, OPEN_IN)),
    O('Windows where the backup is over the load limit', 'int', 'COUNTIFS({range:cover.backup_load},">"&{in:load_max},{range:cover.days_to_open},">=0",{range:cover.days_to_open},"<="&{in:days})'),
    O('Heaviest backup load in one week', 'int', 'MAX({range:cover.backup_load})'),
    O('Soonest client without a backup', 'text', 'IFERROR(INDEX({range:cover.client},MATCH(%s,{range:cover.cover_flag},0)),"-")' % ck('No backup named')),
    O('Their window opens', 'date', 'IFERROR(INDEX({range:cover.oncall_start},MATCH(%s,{range:cover.cover_flag},0)),{today})' % ck('No backup named')),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,%s,"")>0,COUNTIFS(%s,%s,"")&" "&%s,IF(COUNTIFS({range:cover.backup_load},">"&{in:load_max},{range:cover.days_to_open},">=0",{range:cover.days_to_open},"<="&{in:days})>0,%s,%s))' % (
        OPEN_IN, OB, OPEN_IN, OB, c2('windows without cover'), c2('Backup load too high'), c2('All windows covered')))],
    GR('What if you look ahead', ('30 days', {'days': 30}), ('60 days', {'days': 60}), ('90 days', {'days': 90}), ('180 days', {'days': 180}), ('Load limit 3', {'load_max': 3}), ('Load limit 5', {'load_max': 5}))))

# 6 ------------------------------------------------------------ backup pay and missed-birth tool
PAY = '{in:attended}*IF({in:rule}=%s,{in:flat},IF({in:rule}=%s,{in:price}*{in:backup_share},{in:hours}*{in:hourly}))' % (tok('rule', 'Flat call-out'), tok('rule', 'Share of the birth part'))
CUT = '{in:price}*{in:agency_share}'
tools.append(TOOL('backup_pay', 'Backup Pay Calculator', 'Backup pay on a birth, with the missed-birth rule',
    'Pick the pay rule and type the birth part of the package: the backup is paid from the doula share; set attended to 0 when the backup cannot attend (no call-out pay).', [
    IL('rule', 'Pay rule', 'rule', 'Flat call-out'), I('price', 'Birth part of the package', 2400), I('agency_share', 'Agency share of the birth part', 0.27, 'pct'), I('flat', 'Flat call-out pay', 420),
    I('backup_share', 'Backup share of the birth part', 0.25, 'pct'), I('hours', 'Hours the backup attends', 16, 'num'), I('hourly', 'Hourly rate for a backup', 28),
    I('attended', 'Backup attended (1 yes, 0 missed)', 1, 'int'), I('weeks', 'Weeks on the rota in the period', 13, 'int')], [
    O('Backup call-out pay', 'money', PAY), O('Agency cut of the birth part', 'money', CUT), O('Doula pay before the backup', 'money', '{in:price}*(1-{in:agency_share})'),
    O('Doula pay after paying the backup', 'money', '{in:price}*(1-{in:agency_share})-(%s)' % PAY),
    O('Agency net when the doula pays the backup', 'money', '%s-{set:agency_cost_client}' % CUT), O('Agency net when the agency pays the backup', 'money', '%s-{set:agency_cost_client}-(%s)' % (CUT, PAY)),
    O('Stipend for the weeks on the rota', 'money', '{in:weeks}*{set:backup_stipend_week}'), O('Total cost of the backup in the period', 'money', '(%s)+{in:weeks}*{set:backup_stipend_week}' % PAY),
    O('Verdict', 'text', 'IF(%s-{set:agency_cost_client}-(%s)<0,%s,%s)' % (CUT, PAY, c2('Agency loses on this birth'), c2('Agency keeps a margin')))],
    GR('What if the rule or the birth changes', ('Share of the birth part', {'rule': '=' + tok('rule', 'Share of the birth part')}), ('Hourly rate', {'rule': '=' + tok('rule', 'Hourly rate')}),
       ('Backup cannot attend', {'attended': 0}), ('Smaller package 1400', {'price': 1400}), ('Larger package 1900', {'price': 1900}), ('Agency share 0.08', {'agency_share': 0.08}))))

# 7 ------------------------------------------------------------ time-off planner
TS = '{in:start}'; TE = '({in:start}+{in:days}-1)'
TCOND = '(((%s={in:holder})+(%s={in:holder}))>0)*(%s<=%s)*(%s>=%s)' % (OD, OB, OS, TE, OE, TS)
TCLASH = 'COUNTIFS(%s,{in:holder},%s,"<="&%s,%s,">="&%s)+COUNTIFS(%s,{in:holder},%s,"<="&%s,%s,">="&%s)' % (OD, OS, TE, OE, TS, OB, OS, TE, OE, TS)
TFIRST = 'SUMPRODUCT(MIN(%s*%s+(1-%s)*99999999))' % (TCOND, OS, TCOND)
TCLIENT = 'IF((%s)=0,"-",IFERROR(INDEX(%s,MATCH({in:holder}&"|"&%s,{range:oncall.dkey},0)),IFERROR(INDEX(%s,MATCH({in:holder}&"|"&%s,{range:oncall.bkey},0)),"-")))' % (TCLASH, OCL, TFIRST, OCL, TFIRST)
tools.append(TOOL('timeoff_plan', 'Time-Off Planner', 'Can I take time off on these dates',
    'Pick who is away, the first day and the number of days: the windows and due dates inside the block, who else is away, the first client affected and the earliest start with no clash.', [
    IL('holder', 'Who is away', 'holder', D.OV_DOULA), I('start', 'First day off', D.TO_START, 'date'), I('days', 'Days off', 7, 'int')], [
    O('Last day off', 'date', TE), O('Windows overlapped', 'int', TCLASH),
    O('Due dates inside the block', 'int', 'COUNTIFS(%s,{in:holder},%s,">="&%s,%s,"<="&%s)' % (OD, OEDD, TS, OEDD, TE)),
    O('Others away on these days', 'int', 'COUNTIFS({range:timeoff.start},"<="&%s,{range:timeoff.end},">="&%s)' % (TE, TS)),
    O('First client affected', 'text', TCLIENT),
    O('Earliest start after the clashing windows', 'date', 'IF((%s)=0,%s,SUMPRODUCT(MAX(%s*%s))+1)' % (TCLASH, TS, TCOND, OE)),
    O('Verdict', 'text', 'IF((%s)=0,%s,%s&" "&%s)' % (TCLASH, ck('Safe to book'), c2('Clashes with'), TCLIENT))],
    GR('What if the block is shorter or longer', ('3 days', {'days': 3}), ('5 days', {'days': 5}), ('7 days', {'days': 7}), ('10 days', {'days': 10}), ('14 days', {'days': 14}))))

# 8 ------------------------------------------------------------ backup assignment ranking
RWS = '{in:start}'; RWE = '({in:start}+{in:days}-1)'
def BLOAD(b): return 'COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s)' % (OB, b, OS, RWE, OE, RWS)
def BAREA(b): return 'COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s,%s,{in:area})' % (OB, b, OS, RWE, OE, RWS, OAREA)
def BROTA(b): return 'COUNTIFS(%s,%s,%s,">="&(%s-6),%s,"<="&%s)' % (R('rota', 'backup'), b, R('rota', 'week'), RWS, R('rota', 'week'), RWE)
def BSCORE(b): return '10*%s-3*%s-%s' % (BLOAD(b), BROTA(b), BAREA(b))
BEST = 'IF(%s<=%s,%s,%s)' % (BSCORE(B1), BSCORE(B2), B1, B2)
tools.append(TOOL('backup_rank', 'Backup Assignment Ranking', 'Which backup doula to name for this window',
    'Type the window start and length and the area: each backup is scored by the windows already covered, the windows in the same area and the rota weeks (lower is better); see who to name.', [
    I('start', 'Window starts on', D.NB_START, 'date'), I('days', 'Window length in days', 29, 'int'), IL('area', 'Area of the client', 'area', 'Southbank'), I('load_max', 'Most windows one backup carries at once', 4, 'int')], [
    O('First backup', 'text', B1), O('Windows the first backup covers then', 'int', BLOAD(B1)), O('Of them in the same area, first backup', 'int', BAREA(B1)), O('Rota weeks inside the window, first backup', 'int', BROTA(B1)), O('Score of the first backup, lower is better', 'int', BSCORE(B1)),
    O('Second backup', 'text', B2), O('Windows the second backup covers then', 'int', BLOAD(B2)), O('Of them in the same area, second backup', 'int', BAREA(B2)), O('Rota weeks inside the window, second backup', 'int', BROTA(B2)), O('Score of the second backup, lower is better', 'int', BSCORE(B2)),
    O('Best backup to name', 'text', BEST),
    O('Verdict', 'text', 'IF(MIN(%s,%s)>={in:load_max},%s,%s&" "&%s)' % (BLOAD(B1), BLOAD(B2), c2('No backup is free: add cover'), c2('Name this backup:'), BEST))],
    GR('What if the window or the load limit changes', ('A shorter window of 14 days', {'days': 14}), ('A longer window of 40 days', {'days': 40}), ('Load limit 2', {'load_max': 2}), ('Load limit 3', {'load_max': 3}), ('Northgate client', {'area': '=' + tok('area', 'Northgate')}))))

# 9 ------------------------------------------------------------ window length effect
def NBR(a, b): return 'SUMPRODUCT((%s>=%s)*(%s<=%s+365)*(COUNTIFS(%s,%s,%s,">="&(%s-(%s+%s)),%s,"<="&(%s+(%s+%s)))>1))' % (OEDD, T0, OEDD, T0, OD, OD, OEDD, OEDD, a, b, OEDD, OEDD, a, b)
WIN12 = 'COUNTIFS(%s,">="&%s,%s,"<="&(%s+365))' % (OEDD, T0, OEDD, T0)
tools.append(TOOL('window_len', 'Window Length Effect', 'Would a shorter on-call window cut the overlaps',
    'Type the on-call days before and after the due date for your current window and a shorter one: the overlapped windows over 12 months and the days saved.', [
    I('before_a', 'Current days before the due date', 14, 'int'), I('after_a', 'Current days after the due date', 14, 'int'), I('before_b', 'Shorter days before the due date', 7, 'int'), I('after_b', 'Shorter days after the due date', 7, 'int'),
    I('min_saving', 'Fewest overlaps saved to shorten the window', 0.25, 'pct')], [
    O('Windows with a due date in the next 12 months', 'int', WIN12), O('Windows overlapped, current window', 'int', NBR('{in:before_a}', '{in:after_a}')), O('Windows overlapped, shorter window', 'int', NBR('{in:before_b}', '{in:after_b}')),
    O('Overlaps saved', 'int', '%s-%s' % (NBR('{in:before_a}', '{in:after_a}'), NBR('{in:before_b}', '{in:after_b}'))),
    O('Share of overlaps saved', 'pct', 'IFERROR((%s-%s)/%s,0)' % (NBR('{in:before_a}', '{in:after_a}'), NBR('{in:before_b}', '{in:after_b}'), NBR('{in:before_a}', '{in:after_a}'))),
    O('On-call days a year, current window', 'int', '%s*({in:before_a}+{in:after_a}+1)' % WIN12), O('On-call days a year, shorter window', 'int', '%s*({in:before_b}+{in:after_b}+1)' % WIN12),
    O('On-call days saved a year', 'int', '%s*({in:before_a}+{in:after_a}-{in:before_b}-{in:after_b})' % WIN12),
    O('Verdict', 'text', 'IF(IFERROR((%s-%s)/%s,0)>={in:min_saving},%s,%s)' % (NBR('{in:before_a}', '{in:after_a}'), NBR('{in:before_b}', '{in:after_b}'), NBR('{in:before_a}', '{in:after_a}'), c2('Shorten the window'), c2('Keep the window')))],
    GR('What if the shorter window changes', ('7 days each side', {'before_b': 7, 'after_b': 7}), ('10 days each side', {'before_b': 10, 'after_b': 10}), ('12 days each side', {'before_b': 12, 'after_b': 12}),
       ('14 before and 7 after', {'before_b': 14, 'after_b': 7}), ('Same as now', {'before_b': 14, 'after_b': 14}))))

# 10 ----------------------------------------------------------- backup rota balance
PER = '{today}-7*{in:weeks}'
def RW(b): return 'COUNTIFS(%s,%s,%s,">="&(%s),%s,"<="&%s)' % (R('rota', 'backup'), b, R('rota', 'week'), PER, R('rota', 'week'), T0)
def WCOV(b): return 'COUNTIFS(%s,%s,%s,">="&(%s),%s,"<="&%s)' % (OB, b, OS, PER, OS, T0)
IMB = 'MAX(ABS(%s-%s)/MAX(1,%s+%s),ABS(%s-%s)/MAX(1,%s+%s))' % (RW(B1), RW(B2), RW(B1), RW(B2), WCOV(B1), WCOV(B2), WCOV(B1), WCOV(B2))
tools.append(TOOL('rota_balance', 'Backup Rota Balance', 'Is the backup rota shared fairly',
    'Type the weeks to look back and the gap you accept: rota weeks, windows covered and the stipend for each backup; see whether the rota needs rebalancing.', [
    I('weeks', 'Weeks to look back', 26, 'int'), I('tolerance', 'Largest gap between backups you accept', 0.2, 'pct')], [
    O('First backup', 'text', B1), O('Rota weeks, first backup', 'int', RW(B1)), O('Windows opened, first backup', 'int', WCOV(B1)), O('Stipend cost, first backup', 'money', '%s*{set:backup_stipend_week}' % RW(B1)),
    O('Second backup', 'text', B2), O('Rota weeks, second backup', 'int', RW(B2)), O('Windows opened, second backup', 'int', WCOV(B2)), O('Stipend cost, second backup', 'money', '%s*{set:backup_stipend_week}' % RW(B2)),
    O('Windows per rota week, both backups', 'num', 'IFERROR((%s+%s)/(%s+%s),0)' % (WCOV(B1), WCOV(B2), RW(B1), RW(B2))), O('Largest gap between the backups', 'pct', IMB),
    O('Verdict', 'text', 'IF(%s>{in:tolerance},%s,%s)' % (IMB, c2('Rebalance the rota'), c2('Rota is balanced')))],
    GR('What if you look back further or accept a bigger gap', ('13 weeks', {'weeks': 13}), ('26 weeks', {'weeks': 26}), ('52 weeks', {'weeks': 52}), ('Accept a 10% gap', {'tolerance': 0.1}), ('Accept a 40% gap', {'tolerance': 0.4}))))

# 11 ----------------------------------------------------------- back-to-back due dates
BCOND = '(%s={in:doula})*(%s>=%s)*(%s<=%s+365)*(COUNTIFS(%s,{in:doula},%s,">="&(%s-{in:gap}),%s,"<="&(%s+{in:gap}))>1)' % (OD, OEDD, T0, OEDD, T0, OD, OEDD, OEDD, OEDD, OEDD)
BNUM = 'SUMPRODUCT(%s)' % BCOND
BFIRST = 'SUMPRODUCT(MIN(%s*%s+(1-%s)*99999999))' % (BCOND, OEDD, BCOND)
BCLIENT = 'IF(%s=0,"-",IFERROR(INDEX(%s,MATCH({in:doula}&"|"&%s,{range:oncall.ekey},0)),"-"))' % (BNUM, OCL, BFIRST)
tools.append(TOOL('b2b_tool', 'Back-to-Back Due Dates', 'Are two due dates of one doula too close together',
    'Pick a doula and type the days that count as too close: the due dates in the next 12 months, how many sit close to another, the first one and the verdict on who to space.', [
    IL('doula', 'Doula to check', 'bdoula', D.B2B_DOULA), I('gap', 'Due dates closer than this many days', 10, 'int')], [
    O('Due dates of this doula, next 12 months', 'int', 'COUNTIFS(%s,{in:doula},%s,">="&%s,%s,"<="&(%s+365))' % (OD, OEDD, T0, OEDD, T0)),
    O('Due dates close to another one', 'int', BNUM), O('Share of their due dates that are close', 'pct', 'IFERROR(%s/COUNTIFS(%s,{in:doula},%s,">="&%s,%s,"<="&(%s+365)),0)' % (BNUM, OD, OEDD, T0, OEDD, T0)),
    O('Earliest close due date', 'date', 'IF(%s=0,{today},%s)' % (BNUM, BFIRST)), O('Client with the earliest close due date', 'text', BCLIENT),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (BNUM, c2('No back-to-back due dates'), c2('Space this client:'), BCLIENT))],
    GR('What if the gap changes', ('3 days', {'gap': 3}), ('5 days', {'gap': 5}), ('7 days', {'gap': 7}), ('10 days', {'gap': 10}), ('14 days', {'gap': 14}), ('21 days', {'gap': 21}))))

# 12 ----------------------------------------------------------- capacity vs income
FREE12 = 'COUNTIFS(%s,"<"&{in:cap})*{in:cap}-SUMIFS(%s,%s,"<"&{in:cap})' % (CAPM_D, CAPM_D, CAPM_D)
QUIET = 'SMALL(%s,1)' % CAPM_D
tools.append(TOOL('cap_income', 'Capacity vs Income', 'How much income the free due dates leave open',
    'Type the average package price and the monthly cap: income booked and income left open over the next 12 months, the quietest month to market and the verdict.', [
    I('price', 'Average package price', 1900), I('cap', 'Most due dates the agency takes in a month', 7, 'int')], [
    O('Due dates booked, next 12 months', 'int', 'SUM(%s)' % CAPM_D), O('Income booked', 'money', 'SUM(%s)*{in:price}' % CAPM_D), O('Free due dates, next 12 months', 'int', FREE12), O('Income left open', 'money', '(%s)*{in:price}' % FREE12),
    O('Quietest month', 'date', 'INDEX(%s,MATCH(%s,%s,0))' % (CAPM_M, QUIET, CAPM_D)), O('Due dates in the quietest month', 'int', QUIET), O('Income left open in the quietest month', 'money', 'MAX(0,{in:cap}-%s)*{in:price}' % QUIET),
    O('Verdict', 'text', 'IF((%s)=0,%s,%s)' % (FREE12, c2('Full: no income left open'), c2('Market the quietest month')))],
    GR('What if the price changes', ('Birth Essential 1400', {'price': 1400}), ('Birth Plus 1900', {'price': 1900}), ('Birth Premier 2400', {'price': 2400}), ('Combined 4400', {'price': 4400}), ('Cap 5', {'cap': 5}), ('Cap 9', {'cap': 9}))))

# 13 ----------------------------------------------------------- unnamed backup alerts
NB_ALL = '(%s="")*(%s>=%s)*(%s>0)' % (OB, OE, T0, OS)
NB_FIRST = 'SUMPRODUCT(MIN(%s*%s+(1-%s)*99999999))' % (NB_ALL, OS, NB_ALL)
NB_POS = 'MATCH(1,INDEX(%s*(%s=%s),0),0)' % (NB_ALL, OS, NB_FIRST)
NB_N = 'COUNTIFS(%s,"",%s,">="&%s,%s,"<="&(%s+{in:days}))' % (OB, OS, T0, OS, T0)
NB_CL = 'IFERROR(INDEX(%s,%s),"-")' % (OCL, NB_POS)
tools.append(TOOL('unnamed', 'Unnamed Backup Alerts', 'Which window needs a backup named first',
    'Type the days ahead: the windows opening with no backup named, the soonest one with the client, doula and phone, the days left and the verdict naming who to fix today.', [
    I('days', 'Days ahead to look', 90, 'int')], [
    O('Windows without a backup, opening in these days', 'int', NB_N), O('Windows without a backup, all upcoming', 'int', 'COUNTIFS(%s,"",%s,">="&%s)' % (OB, OE, T0)),
    O('Soonest client without a backup', 'text', NB_CL), O('Their doula', 'text', 'IFERROR(INDEX(%s,%s),"-")' % (OD, NB_POS)), O('Their window opens', 'date', 'IF(COUNTIFS(%s,"",%s,">="&%s)=0,{today},%s)' % (OB, OE, T0, NB_FIRST)),
    O('Days left before it opens', 'int', 'IF(COUNTIFS(%s,"",%s,">="&%s)=0,0,%s-%s)' % (OB, OE, T0, NB_FIRST, T0)), O('Phone of the doula', 'text', 'IFERROR(INDEX({range:oncall.doula_phone},%s)&"","-")' % NB_POS),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s&" "&%s)' % (NB_N, c2('All windows have a backup'), c2('Name a backup for'), NB_CL, c2('today')))],
    GR('What if you look ahead', ('30 days', {'days': 30}), ('60 days', {'days': 60}), ('90 days', {'days': 90}), ('120 days', {'days': 120}), ('180 days', {'days': 180}))))

# 14 ----------------------------------------------------------- rota swap finder
SD = '{in:date}'
FREE_DOU = '(%s>0)*(%s<>{in:holder})*(COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s)<{set:max_oncall_overlap})' % (DCAP, DOUS, OD, DOUS, OS, SD, OE, SD)
FREE_BK = '(%s=%s)*(%s<>{in:holder})*(COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s)<{set:backup_load_max})' % (TROLE, BROLE, TNAME, OB, TNAME, OS, SD, OE, SD)
OWN_ON = 'COUNTIFS(%s,{in:holder},%s,"<="&%s,%s,">="&%s)+COUNTIFS(%s,{in:holder},%s,"<="&%s,%s,">="&%s)' % (OD, OS, SD, OE, SD, OB, OS, SD, OE, SD)
SW_D = 'IFERROR(INDEX(%s,MATCH(1,INDEX(%s,0),0)),"-")' % (DOUS, FREE_DOU)
SW_B = 'IFERROR(INDEX(%s,MATCH(1,INDEX(%s,0),0)),"-")' % (TNAME, FREE_BK)
tools.append(TOOL('swap_finder', 'Rota Swap Finder', 'Who can swap in when a doula or backup is away',
    'Pick who is away and the date: the windows they hold that day, the doulas and backups that can swap in without breaking the overlap limit and the verdict.', [
    IL('holder', 'Who is away', 'holder', D.OV_DOULA), I('date', 'Date of the swap', D.OV_EDD, 'date')], [
    O('Windows the holder has open that day', 'int', OWN_ON), O('Doulas free to swap in', 'int', 'SUMPRODUCT(%s)' % FREE_DOU), O('Backups free to swap in', 'int', 'SUMPRODUCT(%s)' % FREE_BK),
    O('First doula free', 'text', SW_D), O('First backup free', 'text', SW_B),
    O('Verdict', 'text', 'IF((%s)=0,%s,IF(SUMPRODUCT(%s)+SUMPRODUCT(%s)=0,%s,%s&" "&IF(SUMPRODUCT(%s)>0,%s,%s)))' % (OWN_ON, c3('Backup not needed'), FREE_DOU, FREE_BK, c3('No swap is free'), c3('Swap with'), FREE_DOU, SW_D, SW_B))],
    GR('What if another person is away', ('Lucia Ferreira', {'holder': '=' + tok('holder', 'Lucia Ferreira')}), ('Sven Lindqvist', {'holder': '=' + tok('holder', 'Sven Lindqvist')}), ('Amara Okonkwo', {'holder': '=' + tok('holder', 'Amara Okonkwo')}),
       ('Yasmin Haddad', {'holder': '=' + tok('holder', 'Yasmin Haddad')}), ('Date 30 days later', {'date': '=({in:date}+30)'}))))

# 15 ----------------------------------------------------------- backup call-out forecast
FAC = 'IF({in:scen}=%s,0.5,IF({in:scen}=%s,1.5,1))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
BIR12 = 'COUNTIFS({range:births.date},">="&(%s-365),{range:births.date},"<="&%s)' % (T0, T0)
BAK12 = 'COUNTIFS({range:births.date},">="&(%s-365),{range:births.date},"<="&%s,{range:births.backup_used},%s)' % (T0, T0, YES)
WIN_N = 'COUNTIFS(%s,">="&%s,%s,"<="&EDATE(%s,{in:months}))' % (OS, T0, OS, T0)
EXP_CO = 'IFERROR(%s*%s/%s,0)*%s' % (WIN_N, BAK12, BIR12, FAC)
tools.append(TOOL('callout_fc', 'Call-Out Forecast', 'What backup call-outs will cost over the next months',
    'Pick Base, Best or Worst and the months ahead: your own backup-use rate over 12 months times the windows opening gives the expected call-outs, their pay, the stipends and the amount to budget.', [
    IL('scen', 'Scenario', 'scen', 'Base'), I('months', 'Months ahead', 3, 'int'), I('flat', 'Flat call-out pay', 420)], [
    O('Births attended, last 12 months', 'int', BIR12), O('Births with a backup, last 12 months', 'int', BAK12), O('Backup use rate, last 12 months', 'pct', 'IFERROR(%s/%s,0)' % (BAK12, BIR12)),
    O('Windows opening in these months', 'int', WIN_N), O('Scenario factor', 'num', FAC), O('Expected call-outs', 'num', EXP_CO), O('Expected call-out pay', 'money', '(%s)*{in:flat}' % EXP_CO),
    O('Stipends for the months', 'money', 'ROUND({in:months}*52/12*{set:backup_stipend_week},0)'), O('Call-outs and stipends together', 'money', '(%s)*{in:flat}+ROUND({in:months}*52/12*{set:backup_stipend_week},0)' % EXP_CO),
    O('Verdict', 'text', '%s&" "&ROUND((%s)*{in:flat},0)' % (c3('Budget for call-outs:'), EXP_CO))],
    GR('What if the scenario or the months change', ('Best case', {'scen': '=' + tok('scen', 'Best')}), ('Worst case', {'scen': '=' + tok('scen', 'Worst')}), ('6 months ahead', {'months': 6}), ('12 months ahead', {'months': 12}), ('Flat pay 500', {'flat': 500}))))

# 16 ----------------------------------------------------------- freed date matcher
FD = 'IFERROR(INDEX(%s,MATCH({in:client},%s,0)),{today})' % (OEDD, OCL)
RCOND = '(%s<>%s)*(%s=%s)*(%s>0)*(ABS(%s-(%s))<={in:tol})' % (R('requests', 'service'), PP, R('requests', 'answered'), NO, R('requests', 'edd_wanted'), R('requests', 'edd_wanted'), FD)
RGAP = 'SUMPRODUCT(MIN(%s*ABS(%s-(%s))+(1-%s)*99999))' % (RCOND, R('requests', 'edd_wanted'), FD, RCOND)
RN = 'SUMPRODUCT(%s)' % RCOND
RPOS = 'MATCH(1,INDEX(%s*(ABS(%s-(%s))=%s),0),0)' % (RCOND, R('requests', 'edd_wanted'), FD, RGAP)
RNAME = 'IF(%s=0,"-",IFERROR(INDEX(%s,%s),"-"))' % (RN, R('requests', 'name'), RPOS)
tools.append(TOOL('freed_date', 'Freed Date Matcher', 'Who should get the date a client freed',
    'Type the name of a client who cancelled or moved and the days either side that you accept: the unanswered date requests near their due date, the closest one with a phone and the verdict.', [
    I('client', 'Client whose date is free', D.FREED_CLIENT, 'text'), I('tol', 'Days either side of the freed due date', 21, 'int')], [
    O('Freed due date', 'date', FD), O('Doula of the freed window', 'text', 'IFERROR(INDEX(%s,MATCH({in:client},%s,0)),"-")' % (OD, OCL)),
    O('Date requests near it, all statuses', 'int', 'COUNTIFS(%s,">="&(%s-{in:tol}),%s,"<="&(%s+{in:tol}),%s,"<>"&%s)' % (R('requests', 'edd_wanted'), FD, R('requests', 'edd_wanted'), FD, R('requests', 'service'), PP)),
    O('Unanswered date requests near it', 'int', RN), O('Closest request', 'text', RNAME), O('Their due date wanted', 'date', 'IF(%s=0,{today},IFERROR(INDEX(%s,%s),{today}))' % (RN, R('requests', 'edd_wanted'), RPOS)),
    O('Their phone', 'text', 'IF(%s=0,"-",IFERROR(INDEX(%s,%s)&"","-"))' % (RN, R('requests', 'phone'), RPOS)),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (RN, c3('Hold the date'), c3('Offer the date to'), RNAME))],
    GR('What if you accept a wider or narrower gap', ('7 days', {'tol': 7}), ('14 days', {'tol': 14}), ('21 days', {'tol': 21}), ('35 days', {'tol': 35}), ('60 days', {'tol': 60}))))

# 17 ----------------------------------------------------------- peak season planner
def MON(yoff): return 'COUNTIFS(%s,">="&DATE(YEAR(%s)%s,{in:month_num},1),%s,"<="&EOMONTH(DATE(YEAR(%s)%s,{in:month_num},1),0))' % (OEDD, T0, yoff, OEDD, T0, yoff)
FCST = '%s*(1+{in:trend})' % MON('')
NEEDB = 'ROUNDUP((%s)/{in:per_backup},0)' % FCST
tools.append(TOOL('peak_season', 'Peak Season Planner', 'Do you need more backup cover in the peak month',
    'Pick a month number and a trend: due dates in that month last year and this year, a forecast for next year and the backups needed against the backups you have.', [
    I('month_num', 'Month number, 1 to 12', 9, 'int'), I('trend', 'Growth you expect next year', 0.1, 'pct'), I('per_backup', 'Due dates one backup can cover in a month', 3, 'int')], [
    O('Due dates in that month last year', 'int', MON('-1')), O('Due dates in that month this year', 'int', MON('')), O('Change from last year', 'pct', 'IFERROR(%s/%s-1,0)' % (MON(''), MON('-1'))),
    O('Forecast for next year', 'num', FCST), O('Backups needed in that month', 'int', NEEDB), O('Backups you have', 'int', 'COUNTIFS(%s,%s)' % (TROLE, BROLE)),
    O('Verdict', 'text', 'IF(%s>COUNTIFS(%s,%s),%s,%s)' % (NEEDB, TROLE, BROLE, c3('Add backup cover for the peak'), c3('Cover is enough for the peak')))],
    GR('What if the month or the trend changes', ('March', {'month_num': 3}), ('June', {'month_num': 6}), ('August', {'month_num': 8}), ('October', {'month_num': 10}), ('December', {'month_num': 12}), ('No growth', {'trend': 0}))))

# 18 ----------------------------------------------------------- window-opens alerts
SOON = 'IFERROR(SMALL(%s,COUNTIF(%s,"<"&%s)+1),"")' % (OS, OS, T0)
SPOS = 'MATCH(%s,%s,0)' % (SOON, OS)
OPEN_N = 'COUNTIFS(%s,">="&%s,%s,"<="&(%s+{in:days}))' % (OS, T0, OS, T0)
tools.append(TOOL('opens_alert', 'Window Opens Alerts', 'Which windows open soon and are they ready',
    'Type the days ahead: the windows opening, how many have a backup, and the very next window with the client, doula, backup and phone to call, plus a ready or needs-a-backup verdict.', [
    I('days', 'Days ahead to look', 14, 'int')], [
    O('Windows opening in these days', 'int', OPEN_N), O('Of them with a backup named', 'int', 'COUNTIFS(%s,">="&%s,%s,"<="&(%s+{in:days}),%s,"<>")' % (OS, T0, OS, T0, OB)),
    O('Of them without a backup', 'int', 'COUNTIFS(%s,">="&%s,%s,"<="&(%s+{in:days}),%s,"")' % (OS, T0, OS, T0, OB)),
    O('Next window opens', 'date', SOON), O('Days until it opens', 'int', 'IF(%s="","",%s-%s)' % (SOON, SOON, T0)), O('Client', 'text', 'IFERROR(INDEX(%s,%s),"-")' % (OCL, SPOS)), O('Doula', 'text', 'IFERROR(INDEX(%s,%s),"-")' % (OD, SPOS)),
    O('Backup', 'text', 'IFERROR(IF(INDEX(%s,%s)="","-",INDEX(%s,%s)),"-")' % (OB, SPOS, OB, SPOS)), O('Doula phone', 'text', 'IFERROR(INDEX({range:oncall.doula_phone},%s)&"","-")' % SPOS),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(COUNTIFS(%s,">="&%s,%s,"<="&(%s+{in:days}),%s,"")>0,%s,%s))' % (OPEN_N, c3('Nothing opens soon'), OS, T0, OS, T0, OB, c3('Needs a backup before the window opens'), c3('Ready: every window has a backup')))],
    GR('What if you look further ahead', ('7 days', {'days': 7}), ('14 days', {'days': 14}), ('30 days', {'days': 30}), ('60 days', {'days': 60}), ('90 days', {'days': 90}))))
assert len(tools) == 18, len(tools)
