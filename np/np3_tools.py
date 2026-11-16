"""Nonprofit suite part 3: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np3_lists import *
import np3_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def R(t, c): return '{range:%s.%s}' % (t, c)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YS = 'DATE(YEAR({today}),1,1)'
STG = lambda s: tok('gstage', s)
RCV = tok('gpay', 'Received'); SUBM = tok('rstatus', 'Submitted')
OPENSTG = [STG(s) for s in OPEN_STAGES]
RESTRICTED = [tok('fundkind', k) for k in ('Program restricted', 'Purpose restricted', 'Grant restricted')]
def QS(k): return 'DATE(YEAR({today}),3*INT((MONTH({today})-1)/3)+1+%d,1)' % (3 * k)
def IDX(g): return D.ACT_IDS.index(g) + 1
def GA(col, no='{in:no}'): return 'INDEX(%s,%s)' % (R('grant_actual', col), no)
def NTHR(table, col, score, k): return 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),"")' % (R(table, col), R(table, score), k, R(table, score))
def NTHS(table, col, score, k): return 'IFERROR(INDEX(%s,MATCH(SMALL(%s,%d),%s,0)),"")' % (R(table, col), R(table, score), k, R(table, score))
tools = []
GID = D.ST['grant']

# 1 ------------------------------------------------------------ grant pipeline view
A_ = ['SUMIFS(%s,%s,%s)' % (R('grants', 'asked'), R('grants', 'stage'), s) for s in OPENSTG]
W1 = '(%s*{in:p1}+%s*{in:p2}+%s*{in:p3})' % tuple(A_)
def QW(k): return '(' + '+'.join('{in:p%d}*SUMIFS(%s,%s,%s,%s,">="&%s,%s,"<"&%s)' % (i + 1, R('grants', 'asked'), R('grants', 'stage'), s, R('grants', 'expected_on'), QS(k), R('grants', 'expected_on'), QS(k + 1)) for i, s in enumerate(OPENSTG)) + ')'
INST12 = 'SUMIFS(%s,%s,"<>"&%s,%s,"<="&({today}+365))' % (R('grant_payments', 'amount'), R('grant_payments', 'status'), RCV, R('grant_payments', 'due_date'))
TOT1 = '(%s+%s)' % (INST12, W1)
tools.append(TOOL('pipeline_view', 'Grant Pipeline View', 'Does the pipeline cover the grant budget',
    'Type your chance of an award at each stage and the grant income you need; weighted pipeline by quarter and what pipeline and instalments cover are shown.', [
    I('p1', 'Chance of an award at Prospect', 0.10, 'pct'), I('p2', 'Chance after a letter of inquiry', 0.25, 'pct'), I('p3', 'Chance after an application', 0.45, 'pct'), I('budget', 'Grant income you need over the next 12 months', 360000)], [
    O('Money asked at Prospect', 'money', A_[0]), O('Money asked after a letter of inquiry', 'money', A_[1]), O('Money asked with an application', 'money', A_[2]),
    O('Grants in the pipeline', 'int', '(' + '+'.join('COUNTIFS(%s,%s)' % (R('grants', 'stage'), s) for s in OPENSTG) + ')'), O('Weighted pipeline at your chances', 'money', W1),
    O('Weighted pipeline at each grant\'s own chance', 'money', '(' + '+'.join('SUMIFS(%s,%s,%s)' % (R('grants', 'weighted'), R('grants', 'stage'), s) for s in OPENSTG) + ')'),
    O('Weighted income this quarter', 'money', QW(0)), O('Weighted income next quarter', 'money', QW(1)), O('Weighted income, quarter after that', 'money', QW(2)), O('Weighted income, fourth quarter', 'money', QW(3)),
    O('Instalments still to come, next 12 months', 'money', INST12), O('Pipeline plus instalments', 'money', TOT1), O('Grant income you need', 'money', '{in:budget}'),
    O('Share of the grant budget covered', 'pct', 'IFERROR(%s/{in:budget},0)' % TOT1), O('Money still to find', 'money', 'MAX(0,{in:budget}-%s)' % TOT1),
    O('Verdict', 'text', 'IF(IFERROR(%s/{in:budget},0)>=1,%s,IF(IFERROR(%s/{in:budget},0)>=0.6,%s,%s))' % (TOT1, c2('Pipeline covers the grant budget'), TOT1, c2('Pipeline covers part of the grant budget'), c2('Pipeline is thin')))],
    GR('What if', ('Chances 5 points higher', {'p1': 0.15, 'p2': 0.30, 'p3': 0.50}), ('Chances 10 points lower', {'p1': 0.05, 'p2': 0.15, 'p3': 0.35}), ('Budget 20 percent higher', {'budget': 432000}),
       ('Budget 20 percent lower', {'budget': 288000}), ('Only applications count', {'p1': 0, 'p2': 0}))))

# 2 ------------------------------------------------------------ grant win rate
def WON(extra, ft=True): return 'COUNTIFS(%s,">0",%s,">="&EDATE({today},-{in:months})%s%s)' % (R('grants', 'awarded'), R('grants', 'decision_on'), (',%s,{in:ftype}' % R('grants', 'funder_type')) if ft else '', extra)
def LOST(ft=True): return 'COUNTIFS(%s,%s,%s,">="&EDATE({today},-{in:months})%s)' % (R('grants', 'stage'), STG('Declined'), R('grants', 'decision_on'), (',%s,{in:ftype}' % R('grants', 'funder_type')) if ft else '')
RT_ = 'IFERROR(%s/(%s+%s),0)' % (WON('', True), WON('', True), LOST(True)); RA_ = 'IFERROR(%s/(%s+%s),0)' % (WON('', False), WON('', False), LOST(False))
YTD = 'COUNTIFS(%s,">0",%s,">="&%s)' % (R('grants', 'awarded'), R('grants', 'decision_on'), YS)
WAIT = 'COUNTIFS(%s,%s)' % (R('grants', 'stage'), STG('Application'))
NEED2 = 'MAX(0,{in:goal}-%s-%s*%s)' % (YTD, WAIT, RA_)
tools.append(TOOL('win_rate_tool', 'Grant Win Rate', 'How many more grants must we apply to this year',
    'Pick a funder type, the months of history and the number of awards you want this year; your own wins and declines give the win rate and how many more applications you need.', [
    IL('ftype', 'Funder type', 'ftype', 'Private foundation'), I('months', 'Months of history to count', 24, 'int'), I('goal', 'Awards you want this year', 14, 'int')], [
    O('Won, this funder type', 'int', WON('', True)), O('Declined, this funder type', 'int', LOST(True)), O('Win rate, this funder type', 'pct', RT_), O('Won, all funder types', 'int', WON('', False)),
    O('Declined, all funder types', 'int', LOST(False)), O('Win rate, all funder types', 'pct', RA_), O('Awards so far this year', 'int', YTD), O('Applications waiting for a decision', 'int', WAIT),
    O('Awards expected from those applications', 'num', '%s*%s' % (WAIT, RA_)), O('Awards still needed to reach the goal', 'num', NEED2),
    O('More applications needed, all funder types', 'int', 'IFERROR(ROUNDUP(%s/%s,0),0)' % (NEED2, RA_)), O('More applications needed, this funder type', 'int', 'IFERROR(ROUNDUP(%s/%s,0),0)' % (NEED2, RT_)),
    O('Verdict', 'text', 'IF(%s<=0,%s,%s)' % (NEED2, c2('On pace for the goal'), c2('Apply to more grants')))],
    GR('What if', ('Corporate giving', {'ftype': '=' + tok('ftype', 'Corporate giving')}), ('Local government', {'ftype': '=' + tok('ftype', 'Local government')}), ('Community foundation', {'ftype': '=' + tok('ftype', 'Community foundation')}),
       ('Goal of 20 awards', {'goal': 20}), ('Only the last 12 months', {'months': 12}))))

# 3 ------------------------------------------------------------ grant income forecast
FAC = 'IF({in:scn}=%s,1,IF({in:scn}=%s,{in:best},{in:worst}))' % (tok('scenario', 'Base'), tok('scenario', 'Best'))
def INSTQ(k): return 'SUMIFS(%s,%s,">="&%s,%s,"<"&%s)' % (R('grant_payments', 'amount'), R('grant_payments', 'due_date'), QS(k), R('grant_payments', 'due_date'), QS(k + 1))
def WQ(k): return 'SUMIFS(%s,%s,">="&%s,%s,"<"&%s)' % (R('grants', 'weighted'), R('grants', 'expected_on'), QS(k), R('grants', 'expected_on'), QS(k + 1))
def TQ(k): return '(%s+%s*%s)' % (INSTQ(k), WQ(k), FAC)
NEEDQ = '({in:budget}/4)'
def SH(k): return 'MAX(0,%s-%s)' % (NEEDQ, TQ(k))
SHALL = '(%s+%s+%s+%s)' % (SH(0), SH(1), SH(2), SH(3))
tools.append(TOOL('income_forecast', 'Grant Income Forecast', 'Which quarter is short of grant income',
    'Pick Base, Best or Worst and type your grant income budget; instalments plus weighted pipeline are set against a quarter of it for four quarters.', [
    IL('scn', 'Scenario', 'scenario', 'Base'), I('best', 'Best case, pipeline times', 1.25, 'num'), I('worst', 'Worst case, pipeline times', 0.5, 'num'), I('budget', 'Grant income in your budget for the year', 360000)], [
    O('Pipeline factor of this scenario', 'num', FAC), O('A quarter of the budget', 'money', NEEDQ),
    O('This quarter, instalments plus pipeline', 'money', TQ(0)), O('Next quarter, instalments plus pipeline', 'money', TQ(1)), O('Third quarter, instalments plus pipeline', 'money', TQ(2)), O('Fourth quarter, instalments plus pipeline', 'money', TQ(3)),
    O('This quarter, short by', 'money', SH(0)), O('Next quarter, short by', 'money', SH(1)), O('Third quarter, short by', 'money', SH(2)), O('Fourth quarter, short by', 'money', SH(3)),
    O('First quarter that is short starts', 'date', 'IF(%s>0,%s,IF(%s>0,%s,IF(%s>0,%s,IF(%s>0,%s,""))))' % (SH(0), QS(0), SH(1), QS(1), SH(2), QS(2), SH(3), QS(3))), O('Total short over four quarters', 'money', SHALL),
    O('Next quarter, Base', 'money', '(%s+%s)' % (INSTQ(1), WQ(1))), O('Next quarter, Best', 'money', '(%s+%s*{in:best})' % (INSTQ(1), WQ(1))), O('Next quarter, Worst', 'money', '(%s+%s*{in:worst})' % (INSTQ(1), WQ(1))),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (SHALL, c2('Quarter is short'), c2('All quarters covered')))],
    GR('What if', ('Best case', {'scn': '=' + tok('scenario', 'Best')}), ('Worst case', {'scn': '=' + tok('scenario', 'Worst')}), ('Budget 20 percent higher', {'budget': 432000}), ('Worst case, quarter of the pipeline', {'scn': '=' + tok('scenario', 'Worst'), 'worst': 0.25}))))

# 4 ------------------------------------------------------------ next 90 days calendar tool
LATEC = 'COUNTIFS(%s,%s)' % (R('calendar90', 'state'), c1('Late')); WEEKC = 'COUNTIFS(%s,%s)' % (R('calendar90', 'state'), c1('Due this week'))
SK = R('calendar90', 'sort_key')
def CALN(k, col): return NTHS('calendar90', col, 'sort_key', k)
tools.append(TOOL('calendar_tool', 'Grant Calendar Check', 'What is late or due this week in the next 90 days',
    'Type how many days ahead you want to look; late and due-this-week items are counted from the Next 90 Days Calendar sheet and the next three items in date order are named.', [
    I('days', 'Days ahead to look', 30, 'int')], [
    O('Late items', 'int', LATEC), O('Money late', 'money', 'SUMIFS(%s,%s,%s)' % (R('calendar90', 'amount'), R('calendar90', 'state'), c1('Late'))), O('Due this week', 'int', WEEKC),
    O('Open items in the days ahead', 'int', 'COUNTIFS(%s,"<>"&%s,%s,">="&{today},%s,"<="&({today}+{in:days}))' % (R('calendar90', 'state'), c1('Done'), R('calendar90', 'date'), R('calendar90', 'date'))),
    O('Money due in the days ahead', 'money', 'SUMIFS(%s,%s,"<>"&%s,%s,">="&{today},%s,"<="&({today}+{in:days}))' % (R('calendar90', 'amount'), R('calendar90', 'state'), c1('Done'), R('calendar90', 'date'), R('calendar90', 'date'))),
    O('Open items in all', 'int', 'COUNT(%s)' % SK),
    O('First open item, date', 'date', CALN(1, 'date')), O('First open item, funder', 'text', CALN(1, 'funder')), O('First open item, kind', 'text', CALN(1, 'kind')),
    O('Second open item, date', 'date', CALN(2, 'date')), O('Second open item, funder', 'text', CALN(2, 'funder')), O('Second open item, kind', 'text', CALN(2, 'kind')),
    O('Third open item, date', 'date', CALN(3, 'date')), O('Third open item, funder', 'text', CALN(3, 'funder')), O('Third open item, kind', 'text', CALN(3, 'kind')),
    O('Verdict', 'text', 'IF(%s>0,%s,IF(%s>0,%s,%s))' % (LATEC, c2('Late items'), WEEKC, c1('Due this week'), c2('Clear')))],
    GR('What if', ('One week ahead', {'days': 7}), ('Two weeks ahead', {'days': 14}), ('60 days ahead', {'days': 60}), ('90 days ahead', {'days': 90}))))

# 5 ------------------------------------------------------------ report due ranker
OPENR = '%s,"<>"&%s,%s,"<>"' % (R('grant_reports', 'status'), SUBM, R('grant_reports', 'report_id'))
def RR(k, col): return NTHR('grant_reports', col, 'rank_score', k)
def ACT5(d, g): return 'IF(OR(%s<=14,AND(%s<={in:warn},IF(ISNUMBER(%s),%s<-{in:margin},FALSE))),%s,IF(%s<={in:warn},%s,%s))' % (d, d, g, g, c2('Write now'), d, c2('Start'), c2('On time'))
D1 = 'IF(ISNUMBER(%s),%s,9999)' % (RR(1, 'days_to_due'), RR(1, 'days_to_due'))
tools.append(TOOL('report_ranker', 'Report Due Ranker', 'Which funder report do we write first',
    'Type the warning days and how far behind the period spending may be; open reports are ranked by days to due, and the first report gets a verdict of write now, start or on time.', [
    I('warn', 'Warning days before a report is due', 30, 'int'), I('margin', 'Spending behind the period that you flag', 0.10, 'pct')], [
    O('Open reports', 'int', 'COUNTIFS(%s)' % OPENR), O('Reports late', 'int', 'COUNTIFS(%s,%s,"<"&{today})' % (OPENR, R('grant_reports', 'due_date'))), O('Reports due in the warning days', 'int', 'COUNTIFS(%s,%s,"<="&({today}+{in:warn}))' % (OPENR, R('grant_reports', 'due_date'))),
    O('Of those, with spending behind the period', 'int', 'COUNTIFS(%s,%s,"<="&({today}+{in:warn}),%s,"<"&-{in:margin})' % (OPENR, R('grant_reports', 'due_date'), R('grant_reports', 'gap'))),
    O('First report', 'text', RR(1, 'report_id')), O('First report, funder', 'text', RR(1, 'funder')), O('First report, days to due', 'int', RR(1, 'days_to_due')), O('First report, share spent', 'pct', RR(1, 'share_spent')), O('First report, share of the period', 'pct', RR(1, 'elapsed')),
    O('Second report', 'text', RR(2, 'report_id')), O('Second report, funder', 'text', RR(2, 'funder')), O('Second report, days to due', 'int', RR(2, 'days_to_due')), O('Second report, share spent', 'pct', RR(2, 'share_spent')),
    O('Third report', 'text', RR(3, 'report_id')), O('Third report, funder', 'text', RR(3, 'funder')), O('Third report, days to due', 'int', RR(3, 'days_to_due')),
    O('Verdict for the first report', 'text', ACT5(D1, 'IF(ISNUMBER(%s),%s-%s,"")' % (RR(1, 'share_spent'), RR(1, 'share_spent'), RR(1, 'elapsed'))))],
    GR('What if', ('Warn 14 days ahead', {'warn': 14}), ('Warn 60 days ahead', {'warn': 60}), ('Flag spending 5 points behind', {'margin': 0.05}), ('Flag spending 25 points behind', {'margin': 0.25}))))

# 6 ------------------------------------------------------------ late grant payment chaser
PO_ = '%s,"<>"&%s,%s,"<"&({today}-{in:grace})' % (R('grant_payments', 'status'), RCV, R('grant_payments', 'due_date'))
def PC(k, col): return NTHR('grant_payments', col, 'rank_score', k)
tools.append(TOOL('payment_chaser', 'Late Grant Payment Chaser', 'Which funder do we chase for a late instalment',
    'Type the grace days after the due date; instalments not yet received are ranked by money times days late, and the first funder is named for a call or a message.', [
    I('grace', 'Grace days after the due date', 5, 'int')], [
    O('Late instalments', 'int', 'COUNTIFS(%s)' % PO_), O('Money late', 'money', 'SUMIFS(%s,%s)' % (R('grant_payments', 'amount'), PO_)), O('Next instalment due in, days', 'int', 'IFERROR(SMALL(%s,COUNTIF(%s,"<0")+1),"")' % (R('grant_payments', 'days_to_due'), R('grant_payments', 'days_to_due'))),
    O('Next instalment amount', 'money', 'IFERROR(INDEX(%s,MATCH(SMALL(%s,COUNTIF(%s,"<0")+1),%s,0)),"")' % (R('grant_payments', 'amount'), R('grant_payments', 'days_to_due'), R('grant_payments', 'days_to_due'), R('grant_payments', 'days_to_due'))),
    O('First to chase, instalment', 'text', PC(1, 'pay_id')), O('First to chase, funder', 'text', PC(1, 'funder')), O('First to chase, amount', 'money', PC(1, 'amount')), O('First to chase, days late', 'int', PC(1, 'days_late')),
    O('Second to chase, funder', 'text', PC(2, 'funder')), O('Second to chase, amount', 'money', PC(2, 'amount')), O('Second to chase, days late', 'int', PC(2, 'days_late')),
    O('Third to chase, funder', 'text', PC(3, 'funder')), O('Third to chase, amount', 'money', PC(3, 'amount')), O('Third to chase, days late', 'int', PC(3, 'days_late')),
    O('Verdict', 'text', 'IF(COUNTIFS(%s)>0,%s&" "&%s,%s)' % (PO_, c2('Chase'), PC(1, 'funder'), c2('Wait')))],
    GR('What if', ('No grace', {'grace': 0}), ('Two weeks of grace', {'grace': 14}), ('One month of grace', {'grace': 30}), ('Two months of grace', {'grace': 60}))))

# 7 ------------------------------------------------------------ grant budget against actual
S7 = GA('status'); SH7 = GA('share_spent'); EL7 = GA('elapsed')
tools.append(TOOL('budget_actual_tool', 'Grant Budget Against Actual', 'Is this grant spending on track for its period',
    'Type the row number of a grant on the Grant Budget vs Actual sheet; the share of the period is set against the share spent and the forecast to the end date, with a status.', [
    I('no', 'Row number on the Grant Budget vs Actual sheet', IDX(GID), 'int')], [
    O('Funder', 'text', GA('funder')), O('Project', 'text', GA('project')), O('Awarded', 'money', GA('awarded')), O('Spent to date', 'money', GA('spent')), O('Remaining', 'money', GA('remaining')),
    O('Share of the period that has passed', 'pct', EL7), O('Share of the award spent', 'pct', SH7), O('Spend expected by now', 'money', GA('expected_spend')), O('Spent minus expected', 'money', '%s-%s' % (GA('spent'), GA('expected_spend'))),
    O('Forecast to the end date', 'money', GA('forecast')), O('Money at risk of being returned', 'money', GA('at_risk')), O('Grants underspent, all grants', 'int', 'COUNTIFS(%s,%s)' % (R('grant_actual', 'status'), c1('Underspending'))),
    O('Grants overspent, all grants', 'int', 'COUNTIFS(%s,%s)' % (R('grant_actual', 'status'), c1('Overspending'))), O('Verdict', 'text', S7)],
    GR('What if', ('A grant that is ahead', {'no': IDX('GR-072')}), ('A grant that is overspent', {'no': IDX('GR-062')}), ('A grant just started', {'no': IDX('GR-082')}), ('A closed grant', {'no': IDX('GR-050')}))))

# 8 ------------------------------------------------------------ underspend rescue plan
REM8 = GA('remaining'); AW8 = GA('awarded'); ML8 = GA('months_left'); SP8 = GA('spent')
TGT8 = 'MAX(0,%s*{in:target}-%s)' % (AW8, SP8)
EM8 = 'MAX(0.5,(({today}-%s)/30.4375))' % GA('start_on')
PACE8 = '(%s/%s)' % (SP8, EM8)
NEEDM8 = 'IFERROR(%s/%s,0)' % (TGT8, ML8)
tools.append(TOOL('underspend_rescue', 'Underspend Rescue Plan', 'What monthly spend uses the award before the end date',
    'Type a grant row number and the share of the award you plan to use; the spend needed each month to the end date is set against your current pace, with the effect of an extension.', [
    I('no', 'Row number on the Grant Budget vs Actual sheet', IDX(GID), 'int'), I('target', 'Share of the award you plan to use', 0.95, 'pct'), I('ext', 'Months of extension you could ask for', 3, 'int'), I('stretch', 'Most you can raise monthly spend, times your pace', 2.0, 'num')], [
    O('Funder', 'text', GA('funder')), O('Awarded', 'money', AW8), O('Spent to date', 'money', SP8), O('Money still to use for your target', 'money', TGT8), O('Months left to the end date', 'num', ML8),
    O('Your monthly pace so far', 'money', PACE8), O('Spend needed each month', 'money', NEEDM8), O('Needed pace compared with your pace', 'num', 'IFERROR(%s/%s,0)' % (NEEDM8, PACE8)),
    O('Spend needed each month with the extension', 'money', 'IFERROR(%s/(%s+{in:ext}),0)' % (TGT8, ML8)), O('Money at risk if the pace stays', 'money', 'MAX(0,%s*{in:target}-%s-%s*%s)' % (AW8, SP8, PACE8, ML8)),
    O('Extension ends on', 'date', 'IFERROR(EDATE(%s,{in:ext}),"")' % GA('end_on')),
    O('Verdict', 'text', 'IF(%s<=0,%s,IF(IFERROR(%s/%s,0)<={in:stretch},%s,%s))' % (TGT8, c2('No rescue needed'), NEEDM8, PACE8, c2('Raise spend'), c2('Ask for an extension')))],
    GR('What if', ('Use 80 percent', {'target': 0.80}), ('Use the whole award', {'target': 1.0}), ('Can only stretch 1.5 times', {'stretch': 1.5}), ('A grant that is far behind', {'no': IDX('GR-074')}), ('Six months of extension', {'ext': 6}))))

# 9 ------------------------------------------------------------ overspend limit
LIM9 = 'IFERROR(%s*(1-{in:buffer})/%s,0)' % (GA('remaining'), GA('months_left'))
tools.append(TOOL('overspend_limit', 'Overspend Limit', 'What can we spend each month and stay inside the award',
    'Type a grant row number and the share of the remaining money you keep as a buffer; the spend each remaining month that stays inside the award is set against your current pace.', [
    I('no', 'Row number on the Grant Budget vs Actual sheet', IDX('GR-075'), 'int'), I('buffer', 'Share of the remaining money you keep as a buffer', 0.05, 'pct')], [
    O('Funder', 'text', GA('funder')), O('Awarded', 'money', GA('awarded')), O('Spent to date', 'money', GA('spent')), O('Remaining', 'money', GA('remaining')), O('Months left to the end date', 'num', GA('months_left')),
    O('Most to spend each month', 'money', LIM9), O('Your monthly pace so far', 'money', '(%s/MAX(0.5,(({today}-%s)/30.4375)))' % (GA('spent'), GA('start_on'))),
    O('Cut needed each month', 'money', 'MAX(0,(%s/MAX(0.5,(({today}-%s)/30.4375)))-%s)' % (GA('spent'), GA('start_on'), LIM9)),
    O('Months until the money runs out at your pace', 'num', 'IFERROR(MAX(0,%s)/(%s/MAX(0.5,(({today}-%s)/30.4375))),0)' % (GA('remaining'), GA('spent'), GA('start_on'))),
    O('Forecast to the end date', 'money', GA('forecast')), O('Forecast over the award by', 'money', 'MAX(0,%s-%s)' % (GA('forecast'), GA('awarded'))),
    O('Verdict', 'text', 'IF(%s<0,%s,IF(%s>%s+0.5,%s,%s))' % (GA('remaining'), c3('Overspend limit passed'), '(%s/MAX(0.5,(({today}-%s)/30.4375)))' % (GA('spent'), GA('start_on')), LIM9, c2('Cut spending'), c2('Fine')))],
    GR('What if', ('Keep no buffer', {'buffer': 0}), ('Keep 15 percent', {'buffer': 0.15}), ('A grant that is overspent', {'no': IDX('GR-062')}), ('A large grant', {'no': IDX('GR-072')}), ('A grant that is ahead', {'no': IDX('GR-074')}))))

# 10 ----------------------------------------------------------- grant line mover
GL = 'INDEX(%s,{in:no})' % R('grant_actual', 'grant_id')
def LINEV(col, line): return 'SUMIFS(%s,%s,%s,%s,%s)' % (R('grant_lines', col), R('grant_lines', 'grant_id'), GL, R('grant_lines', 'line'), tok('gline', line))
OV = [LINEV('over_by', l) for l in GRANT_LINES]; SP = [LINEV('spare', l) for l in GRANT_LINES]
TOV = '(%s)' % '+'.join(OV)
MAXSP = 'MAX(%s)' % ','.join(SP); MAXOV = 'MAX(%s)' % ','.join(OV)
def PICK(vals, mx): return 'IF(%s=%s,%s,IF(%s=%s,%s,%s))' % (vals[0], mx, tok('gline', GRANT_LINES[0]), vals[1], mx, tok('gline', GRANT_LINES[1]), tok('gline', GRANT_LINES[2]))
CAP = '(%s*{in:cap})' % GA('awarded'); MOVE = 'MIN(%s,%s,%s)' % (TOV, MAXSP, CAP)
tools.append(TOOL('line_mover', 'Grant Line Mover', 'Which budget line do we move money from and to',
    'Type a grant row number and the most your funder lets you move between lines (check your funder\'s rules); lines over and under budget are shown with a suggested move.', [
    I('no', 'Row number on the Grant Budget vs Actual sheet', IDX('GR-062'), 'int'), I('cap', 'Most you may move, share of the award', 0.10, 'pct')], [
    O('Funder', 'text', GA('funder')), O('Staff line, over by', 'money', OV[0]), O('Direct costs line, over by', 'money', OV[1]), O('Other costs line, over by', 'money', OV[2]),
    O('Staff line, spare', 'money', SP[0]), O('Direct costs line, spare', 'money', SP[1]), O('Other costs line, spare', 'money', SP[2]), O('Total over budget on its lines', 'money', TOV),
    O('Line most over budget', 'text', 'IF(%s=0,"",%s)' % (MAXOV, PICK(OV, MAXOV))), O('Line with the most spare', 'text', 'IF(%s=0,"",%s)' % (MAXSP, PICK(SP, MAXSP))),
    O('Most you may move', 'money', CAP), O('Suggested move', 'money', MOVE), O('Still over after the move', 'money', 'MAX(0,%s-%s)' % (TOV, MOVE)),
    O('Verdict', 'text', 'IF(%s<=0,%s,%s)' % (TOV, c2('No move needed'), c2('Move money between lines')))],
    GR('What if', ('Move up to 25 percent', {'cap': 0.25}), ('Move up to 5 percent', {'cap': 0.05}), ('Another grant over on a line', {'no': IDX('GR-050')}), ('A grant within its lines', {'no': IDX('GR-072')}))))

# 11 ----------------------------------------------------------- fund balance check
def FUNDV(col): return 'SUMIFS(%s,%s,{in:fund})' % (R('fund_months', col), R('fund_months', 'fund'))
OPEN11 = 'SUMIFS(%s,%s,{in:fund})' % (R('funds', 'opening_balance'), R('funds', 'fund'))
BAL11 = '(%s+%s-%s+%s)' % (OPEN11, FUNDV('receipts'), FUNDV('released'), FUNDV('transfers'))
NOWB = 'SUMIFS(%s,%s,{in:fund},%s,%s)' % (R('fund_months', 'balance'), R('fund_months', 'fund'), R('fund_months', 'month'), MS)
AVG6 = '(SUMIFS(%s,%s,{in:fund},%s,">="&EDATE(%s,-6),%s,"<"&%s)/6)' % (R('fund_months', 'released'), R('fund_months', 'fund'), R('fund_months', 'month'), MS, R('fund_months', 'month'), MS)
tools.append(TOOL('fund_check', 'Fund Balance Check', 'Is every restricted fund still at or above zero',
    'Pick a fund; its opening balance plus receipts less releases and transfers gives the balance, checked against Fund Months, and every restricted fund below zero is counted.', [
    IL('fund', 'Fund', 'fund', D.ST['fund'])], [
    O('Restriction', 'text', 'IFERROR(INDEX(%s,MATCH({in:fund},%s,0))&"","")' % (R('funds', 'restriction'), R('funds', 'fund'))), O('Opening balance', 'money', OPEN11), O('Receipts to date', 'money', FUNDV('receipts')),
    O('Released from restriction to date', 'money', FUNDV('released')), O('Transfers to date', 'money', FUNDV('transfers')), O('Balance worked out', 'money', BAL11), O('Balance on Fund Months this month', 'money', NOWB),
    O('Difference between the two', 'money', 'ROUND(%s-%s,2)' % (BAL11, NOWB)), O('Average released a month, last 6 months', 'money', AVG6), O('Months of spending the balance covers', 'num', 'IFERROR(MAX(0,%s)/%s,0)' % (NOWB, AVG6)),
    O('Below zero by', 'money', 'MAX(0,-%s)' % NOWB), O('Restricted funds below zero, all funds', 'int', 'COUNTIFS(%s,%s,%s,1)' % (R('fund_position', 'status'), c1('Below zero'), R('fund_position', 'is_now'))),
    O('Total below zero, all funds', 'money', '-SUMIFS(%s,%s,"<0",%s,1)' % (R('fund_position', 'balance'), R('fund_position', 'balance'), R('fund_position', 'is_now'))),
    O('Verdict', 'text', 'IF(%s<0,%s,IF(AND(%s<{set:near_zero_limit},SUMIFS(%s,%s,{in:fund},%s,1)=1),%s,%s))' % (NOWB, c1('Below zero'), NOWB, R('fund_position', 'is_restricted'), R('fund_position', 'fund'), R('fund_position', 'is_now'), c1('Near zero'), c1('OK')))],
    GR('What if', ('Food Pantry Fund', {'fund': '=' + tok('fund', 'Food Pantry Fund')}), ('Learning Lab Grant Fund', {'fund': '=' + tok('fund', 'Learning Lab Grant Fund')}), ('Camp Bursary Fund', {'fund': '=' + tok('fund', 'Camp Bursary Fund')}),
       ('General Fund', {'fund': '=' + tok('fund', 'General Fund')}), ('Facilities Reserve', {'fund': '=' + tok('fund', 'Facilities Reserve')}))))

# 12 ----------------------------------------------------------- spending against fund
BALF = 'SUMIFS(%s,%s,{in:fund},%s,1)' % (R('fund_position', 'balance'), R('fund_position', 'fund'), R('fund_position', 'is_now'))
GENF = 'SUMIFS(%s,%s,%s,%s,1)' % (R('fund_position', 'balance'), R('fund_position', 'fund'), tok('fund', 'General Fund'), R('fund_position', 'is_now'))
COV12 = 'MIN({in:cost},MAX(0,%s-{in:keep}))' % BALF
tools.append(TOOL('spend_against_fund', 'Spending Against Fund', 'Can this restricted fund pay for this cost',
    'Pick a fund, type the planned cost and the money you want to keep in the fund; the cost is tested against its balance, and any part it cannot pay is charged to General Fund.', [
    IL('fund', 'Fund to charge', 'fund', D.ST['fund']), I('cost', 'Planned cost', 2400), I('keep', 'Money you want to keep in the fund', 0)], [
    O('Balance of the fund now', 'money', BALF), O('Planned cost', 'money', '{in:cost}'), O('Balance after the whole cost', 'money', '%s-{in:cost}' % BALF), O('The fund can pay', 'money', COV12),
    O('Charge to General Fund', 'money', '{in:cost}-%s' % COV12), O('General Fund balance now', 'money', GENF), O('General Fund balance after', 'money', '%s-({in:cost}-%s)' % (GENF, COV12)),
    O('Average released from this fund a month, last 6 months', 'money', AVG6), O('Months of spending the fund covers after this cost', 'num', 'IFERROR(MAX(0,%s-%s)/%s,0)' % (BALF, COV12, AVG6)),
    O('Verdict', 'text', 'IF(%s-{in:cost}>={in:keep},%s,%s)' % (BALF, c2('Charge the fund'), c2('Charge General Fund')))],
    GR('What if', ('Food Pantry Fund, 4,800', {'fund': '=' + tok('fund', 'Food Pantry Fund'), 'cost': 4800}), ('Learning Lab Grant Fund, 3,000', {'fund': '=' + tok('fund', 'Learning Lab Grant Fund'), 'cost': 3000}),
       ('Senior Meals Fund, 1,500, keep 500', {'fund': '=' + tok('fund', 'Senior Meals Fund'), 'cost': 1500, 'keep': 500}), ('Kitchen Equipment Fund, 800', {'cost': 800}), ('Camp Bursary Fund, 900', {'fund': '=' + tok('fund', 'Camp Bursary Fund'), 'cost': 900}))))

# 13 ----------------------------------------------------------- release from restriction journal
SPR13 = 'SUMIFS(%s,%s,{in:month},%s,1)' % (R('grant_spending', 'amount'), R('grant_spending', 'month'), R('grant_spending', 'is_restricted'))
REL13 = 'SUMIFS(%s,%s,{in:month},%s,1)' % (R('release_journal', 'amount'), R('release_journal', 'month'), R('release_journal', 'on_grant'))
SPF13 = 'SUMIFS(%s,%s,{in:month},%s,{in:fund})' % (R('grant_spending', 'amount'), R('grant_spending', 'month'), R('grant_spending', 'fund'))
RLF13 = 'SUMIFS(%s,%s,{in:month},%s,{in:fund},%s,1)' % (R('release_journal', 'amount'), R('release_journal', 'month'), R('release_journal', 'fund'), R('release_journal', 'on_grant'))
tools.append(TOOL('release_tool', 'Release from Restriction', 'How much do we release from restricted funds this month',
    'Type a month and a fund; the grant spending coded to restricted funds in that month is set against the releases already in the Release Journal, and the amount left to release is shown.', [
    I('month', 'Month, any day of it', iso(month_start(0)), 'date'), IL('fund', 'Fund', 'fund', 'Food Pantry Fund')], [
    O('Spending coded to restricted funds in the month', 'money', SPR13), O('Released in the journal for that spending', 'money', REL13), O('Still to release, all restricted funds', 'money', '%s-%s' % (SPR13, REL13)),
    O('Spending coded to this fund', 'money', SPF13), O('Released for it in the journal', 'money', RLF13), O('Still to release for this fund', 'money', '%s-%s' % (SPF13, RLF13)),
    O('All releases of this fund in the month', 'money', 'SUMIFS(%s,%s,{in:month},%s,{in:fund})' % (R('release_journal', 'amount'), R('release_journal', 'month'), R('release_journal', 'fund'))),
    O('Releases in the journal in the month, all funds', 'money', 'SUMIFS(%s,%s,{in:month})' % (R('release_journal', 'amount'), R('release_journal', 'month'))), O('Released this year, all funds', 'money', 'SUMIFS(%s,%s,">="&%s)' % (R('release_journal', 'amount'), R('release_journal', 'date'), YS)),
    O('Release journal lines in the month', 'int', 'COUNTIFS(%s,{in:month})' % R('release_journal', 'month')),
    O('Verdict', 'text', 'IF(%s-%s>1,%s,%s)' % (SPR13, REL13, c2('Release this month'), c2('Nothing to release')))],
    GR('What if', ('Last month', {'month': '=EDATE(%s,-1)' % MS}), ('Two months ago', {'month': '=EDATE(%s,-2)' % MS}), ('Senior Meals Fund', {'fund': '=' + tok('fund', 'Senior Meals Fund')}), ('Learning Lab Grant Fund', {'fund': '=' + tok('fund', 'Learning Lab Grant Fund')}))))

# 14 ----------------------------------------------------------- free money position
def FMV(col): return 'SUMIFS(%s,%s,DATE(YEAR({in:month}),MONTH({in:month}),1))' % (R('free_money', col), R('free_money', 'month'))
def FM3(col): return 'SUMIFS(%s,%s,EDATE(DATE(YEAR({in:month}),MONTH({in:month}),1),-3))' % (R('free_money', col), R('free_money', 'month'))
M14 = 'IFERROR(%s/%s,0)' % (FMV('free_money'), FMV('avg_expense'))
tools.append(TOOL('free_money_tool', 'Free Money Tool', 'Is free money healthy once restricted money is set aside',
    'Type a month and a one-off cost; cash less restricted and designated money is free money, shown in months of expense against your setting and three months ago.', [
    I('month', 'Month, any day of it', iso(month_start(0)), 'date'), I('spend', 'A one-off cost you are thinking of', 25000), I('target', 'Months of reserve you want, starting point, set your own', 3.0, 'num')], [
    O('Cash', 'money', FMV('cash')), O('Restricted money', 'money', FMV('restricted')), O('Designated money', 'money', FMV('designated')), O('Free money', 'money', FMV('free_money')), O('Average monthly expense', 'money', FMV('avg_expense')),
    O('Months of reserve', 'num', M14), O('Months of reserve three months earlier', 'num', 'IFERROR(%s/%s,0)' % (FM3('free_money'), FM3('avg_expense'))), O('Free money you need for the reserve you want', 'money', '{in:target}*%s' % FMV('avg_expense')),
    O('Free money above or below that', 'money', '%s-{in:target}*%s' % (FMV('free_money'), FMV('avg_expense'))), O('Months of reserve after the one-off cost', 'num', 'IFERROR((%s-{in:spend})/%s,0)' % (FMV('free_money'), FMV('avg_expense'))),
    O('Months of cash, restricted money counted', 'num', 'IFERROR(%s/%s,0)' % (FMV('cash'), FMV('avg_expense'))),
    O('Verdict', 'text', 'IF(%s>={in:target},%s,IF(IFERROR(%s/%s,0)>={in:target},%s,%s))' % (M14, c1('Healthy'), FMV('cash'), FMV('avg_expense'), c2('Cash looks good but free money is low'), c2('Free money is low')))],
    GR('What if', ('Last month', {'month': '=EDATE(%s,-1)' % MS}), ('A cost of 60,000', {'spend': 60000}), ('Reserve of 4 months', {'target': 4.0}), ('Three months ago', {'month': '=EDATE(%s,-3)' % MS}))))

# 15 ----------------------------------------------------------- staff time allocator
def STK(kind=None): return 'SUMIFS(%s,%s,{in:staff},%s,DATE(YEAR({in:month}),MONTH({in:month}),1)%s)' % (R('staff_time', 'percent'), R('staff_time', 'staff'), R('staff_time', 'month'), (',%s,%s' % (R('staff_time', 'target_kind'), tok('tkind', kind))) if kind else '')
TOT15 = STK()
tools.append(TOOL('time_allocator', 'Staff Time Allocator', 'Does this staff month total 100 percent',
    'Pick a staff member and a month; the percent on grants, programs, management and fundraising is added up from the Staff Time sheet and checked against 100 percent.', [
    IL('staff', 'Staff member', 'staff', 'Priya Nair'), I('month', 'Month, any day of it', iso(month_start(1)), 'date'), I('hours', 'Paid hours in the month', 160, 'num')], [
    O('Percent on grants', 'pct', STK('Grant')), O('Percent on programs', 'pct', STK('Program')), O('Percent on management', 'pct', STK('Management')), O('Percent on fundraising', 'pct', STK('Fundraising')),
    O('Total percent', 'pct', TOT15), O('Short of or over 100 percent by', 'pct', '%s-1' % TOT15),
    O('Hours short or over', 'num', '(%s-1)*{in:hours}' % TOT15), O('Cost charged to grants', 'money', 'SUMIFS(%s,%s,{in:staff},%s,DATE(YEAR({in:month}),MONTH({in:month}),1),%s,%s)' % (R('staff_time', 'cost'), R('staff_time', 'staff'), R('staff_time', 'month'), R('staff_time', 'target_kind'), tok('tkind', 'Grant'))),
    O('Total cost of the month', 'money', 'SUMIFS(%s,%s,{in:staff},%s,DATE(YEAR({in:month}),MONTH({in:month}),1))' % (R('staff_time', 'cost'), R('staff_time', 'staff'), R('staff_time', 'month'))),
    O('Staff months not at 100 percent, all staff, last 3 months', 'int', 'COUNTIFS(%s,%s)+COUNTIFS(%s,%s)' % (R('staff_check', 'flag'), c1('Short of 100%'), R('staff_check', 'flag'), c1('Over 100%'))),
    O('Verdict', 'text', 'IF(ABS(%s-1)<={set:time_tolerance},%s,IF(%s<1,%s,%s))' % (TOT15, c1('Totals 100%'), TOT15, c1('Short of 100%'), c1('Over 100%')))],
    GR('What if', ('Lars Henriksen last month', {'staff': '=' + tok('staff', 'Lars Henriksen')}), ('Priya Nair this month', {'month': '=' + MS}), ('Grace Adeyemi last month', {'staff': '=' + tok('staff', 'Grace Adeyemi')}), ('Fiona Gallagher last month', {'staff': '=' + tok('staff', 'Fiona Gallagher')}))))

# 16 ----------------------------------------------------------- grant charge check
GRID16 = GA('grant_id')
PERS16 = 'SUMIFS(%s,%s,%s,%s,%s)' % (R('grant_budget_lines', 'budget'), R('grant_budget_lines', 'grant_id'), GRID16, R('grant_budget_lines', 'line'), tok('gline', 'Staff'))
ALLOC16 = 'SUMIFS(%s,%s,%s)' % (R('staff_time', 'cost'), R('staff_time', 'grant_id'), GRID16)
CHG16 = 'SUMIFS(%s,%s,%s,%s,%s)' % (R('grant_spending', 'amount'), R('grant_spending', 'grant_id'), GRID16, R('grant_spending', 'category'), tok('gcat', 'Staff pay'))
tools.append(TOOL('charge_check', 'Grant Charge Check', 'Is staff cost charged to this grant in line with time',
    'Type a grant row number and the difference you accept; the staff pay coded to the grant is set against the staff time cost allocated to it and against its personnel budget line.', [
    I('no', 'Row number on the Grant Budget vs Actual sheet', IDX('GR-072'), 'int'), I('tol', 'Difference you accept', 0.10, 'pct')], [
    O('Funder', 'text', GA('funder')), O('Personnel line of the budget', 'money', PERS16), O('Staff time cost allocated to the grant', 'money', ALLOC16), O('Staff pay coded to the grant', 'money', CHG16),
    O('Charged minus allocated', 'money', '%s-%s' % (CHG16, ALLOC16)), O('Charged against allocated', 'pct', 'IFERROR(%s/%s,0)' % (CHG16, ALLOC16)), O('Charged against the personnel line', 'pct', 'IFERROR(%s/%s,0)' % (CHG16, PERS16)),
    O('Allocated against the personnel line', 'pct', 'IFERROR(%s/%s,0)' % (ALLOC16, PERS16)), O('Staff months on this grant', 'int', 'COUNTIFS(%s,%s)' % (R('staff_time', 'grant_id'), GRID16)),
    O('Verdict', 'text', 'IF(%s>%s*(1+{in:tol}),%s,IF(%s<%s*(1-{in:tol}),%s,%s))' % (CHG16, ALLOC16, c3('Over-charged'), CHG16, ALLOC16, c3('Under-charged'), c2('Fine')))],
    GR('What if', ('Accept 25 percent', {'tol': 0.25}), ('Accept 2 percent', {'tol': 0.02}), ('The Learning Lab grant', {'no': IDX(GID)}), ('A large grant', {'no': IDX('GR-072')}), ('A grant that ended', {'no': IDX('GR-060')}))))

# 17 ----------------------------------------------------------- grant should-we-apply tool
OWN_PER_HOUR = 'IFERROR(SUMIFS(%s,%s,1)/SUMIFS(%s,%s,1),0)' % (R('grants', 'awarded'), R('grants', 'decided'), R('grants', 'write_hours'), R('grants', 'decided'))
OWN_RATE = 'IFERROR(SUM(%s)/SUM(%s),0)' % (R('grants', 'won'), R('grants', 'decided'))
COST17 = '({in:hours}+{in:report})*{in:rate}'
EV17 = '({in:ask}*{in:prob}*{in:fit})'
PH17 = 'IFERROR((%s-%s)/({in:hours}+{in:report}),0)' % (EV17, COST17)
tools.append(TOOL('apply_tool', 'Grant Should-We-Apply Tool', 'Is this grant worth the hours it takes to win it',
    'Type hours, cost of an hour, amount asked, your chance and the fit; expected value per hour is set against your own money won per writing hour.', [
    I('hours', 'Hours to write the application', 30, 'int'), I('report', 'Hours to report over the grant', 20, 'int'), I('rate', 'Cost of one hour', 34), I('ask', 'Amount asked', 25000), I('prob', 'Your chance of an award, your estimate', 0.40, 'pct'),
    I('fit', 'How well the grant fits, 100 percent is a full fit', 0.90, 'pct')], [
    O('Cost of writing and reporting', 'money', COST17), O('Expected award at your chance', 'money', '{in:ask}*{in:prob}'), O('Expected value after the fit', 'money', EV17), O('Expected value minus cost', 'money', '%s-%s' % (EV17, COST17)),
    O('Expected value per hour', 'money', PH17), O('Your own money won per writing hour, all decisions', 'money', OWN_PER_HOUR), O('Your own win rate, all decisions', 'pct', OWN_RATE),
    O('Win rate needed to cover the cost', 'pct', 'IFERROR(%s/({in:ask}*{in:fit}),0)' % COST17), O('Writing hours so far on open applications', 'int', '(' + '+'.join('SUMIFS(%s,%s,%s)' % (R('grants', 'write_hours'), R('grants', 'stage'), s) for s in OPENSTG) + ')'),
    O('Verdict', 'text', 'IF(%s>=%s*0.25,%s,IF(%s>=%s*0.1,%s,%s))' % (PH17, OWN_PER_HOUR, c3('Apply'), PH17, OWN_PER_HOUR, c3('Apply if time'), c3('Skip')))],
    GR('What if', ('Chance of 20 percent', {'prob': 0.20}), ('A small grant of 5,000', {'ask': 5000, 'hours': 12, 'report': 6}), ('A large grant of 90,000', {'ask': 90000, 'hours': 60, 'report': 50}), ('Poor fit', {'fit': 0.4}), ('A short form of 8 hours', {'hours': 8, 'report': 8}))))

# 18 ----------------------------------------------------------- grant pace sensitivity
CST18 = '(({in:hours}+{in:report})*{in:rate})'
tools.append(TOOL('pace_sensitivity', 'Grant Pace Sensitivity', 'How low can the win rate go before it is not worth it',
    'Type hours, cost of an hour, amount asked and the multiple you want back; the win rate that pays for the hours is found and moved up and down.', [
    I('hours', 'Hours to write', 30, 'int'), I('report', 'Hours to report', 20, 'int'), I('rate', 'Cost of one hour', 34), I('ask', 'Amount asked', 25000), I('win', 'Your win rate, your estimate', 0.40, 'pct'), I('multiple', 'Times the cost you want back in expected award', 3.0, 'num')], [
    O('Cost of the hours', 'money', CST18), O('Expected award at your win rate', 'money', '{in:ask}*{in:win}'), O('Expected award as a multiple of the cost', 'num', 'IFERROR({in:ask}*{in:win}/%s,0)' % CST18),
    O('Win rate that returns your multiple', 'pct', 'IFERROR(%s*{in:multiple}/{in:ask},0)' % CST18), O('Win rate with a multiple of 1, the break-even', 'pct', 'IFERROR(%s/{in:ask},0)' % CST18),
    O('Multiple if the win rate is 10 points lower', 'num', 'IFERROR({in:ask}*MAX(0,{in:win}-0.1)/%s,0)' % CST18), O('Multiple if the win rate is 5 points lower', 'num', 'IFERROR({in:ask}*MAX(0,{in:win}-0.05)/%s,0)' % CST18),
    O('Multiple if the win rate is 5 points higher', 'num', 'IFERROR({in:ask}*({in:win}+0.05)/%s,0)' % CST18), O('Multiple if the hours are 50 percent more', 'num', 'IFERROR({in:ask}*{in:win}/(%s*1.5),0)' % CST18),
    O('Multiple if the hours are half', 'num', 'IFERROR({in:ask}*{in:win}/(%s*0.5),0)' % CST18), O('Highest cost of an hour that still returns your multiple', 'money', 'IFERROR({in:ask}*{in:win}/{in:multiple}/({in:hours}+{in:report}),0)'),
    O('Verdict', 'text', 'IF(IFERROR({in:ask}*{in:win}/%s,0)>={in:multiple},%s,%s)' % (CST18, c3('Worth it'), c3('Not worth it at this win rate')))],
    GR('What if', ('Win rate 20 percent', {'win': 0.20}), ('Win rate 60 percent', {'win': 0.60}), ('Small grant of 8,000', {'ask': 8000}), ('Twice the hours', {'hours': 60, 'report': 40}), ('Want 5 times back', {'multiple': 5.0}))))
assert len(tools) == 18, len(tools)
