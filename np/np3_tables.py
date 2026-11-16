"""Nonprofit suite part 3: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np3_lists import *
import np3_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def ORG(): return CA('org', 'Organization', 'text', '{set:org}', 22)
def CPH(key_, label, phone): return CA(key_, label, 'text', '"%s"' % phone, 18)
def FPH(idcol='grant_id'): return CA('phone', 'Funder phone', 'text', LKT('grants.phone', 'grants.grant_id', idcol), 18)
def R(t, c): return '{range:%s.%s}' % (t, c)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YES = '{list:yesno.yes}'
STG = lambda s: tok('gstage', s)
RCV = tok('gpay', 'Received'); SUBM = tok('rstatus', 'Submitted')
RESTRICTED = [tok('fundkind', k) for k in ('Program restricted', 'Purpose restricted', 'Grant restricted')]
OPENSTG = [STG(s) for s in OPEN_STAGES]
def IS_RESTRICTED(x): return 'OR(%s)' % ','.join('%s=%s' % (x, r) for r in RESTRICTED)
def SUM_OPEN(col, extra=''):  # sum of a grants column over the three open stages
    return '(' + '+'.join('SUMIFS(%s,%s,%s%s)' % (R('grants', col), R('grants', 'stage'), s, extra) for s in OPENSTG) + ')'
def CNT_OPEN(extra=''):
    return '(' + '+'.join('COUNTIFS(%s,%s%s)' % (R('grants', 'stage'), s, extra) for s in OPENSTG) + ')'

settings = [
    S('org', 'Your organization name', 'text', COMPANY), S('report_warn_days', 'Days before a report is due that you start to flag it', 'int', REPORT_WARN_DAYS),
    S('late_after_days', 'Days after the due date before an instalment counts as late', 'int', 5), S('spend_margin', 'How far share spent may differ from share of period', 'pct', 0.10),
    S('prob_prospect', 'Chance of an award at Prospect, your estimate', 'pct', 0.10), S('prob_inquiry', 'Chance of an award after a letter of inquiry, your estimate', 'pct', 0.25),
    S('prob_applied', 'Chance of an award after an application, your estimate', 'pct', 0.45), S('grant_income_budget', 'Grant income in your budget for the year', 'money', 360000),
    S('reserve_months', 'Months of reserve, starting point, set your own', 'num', RESERVE_MONTHS), S('near_zero_limit', 'A restricted fund below this balance is near zero', 'money', 2500),
    S('write_cost_hour', 'Cost of one hour of grant writing', 'money', 34), S('time_tolerance', 'How far a staff month may be from 100%', 'pct', 0.005),
    S('charge_tolerance', 'How far a grant charge may differ from the time allocated', 'pct', 0.10),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 grants ------------------------------------------------------------------
tables.append(T('grants', 'Grants', 'Grants from first idea to close-out',
    'One row per grant: funder, stage, amounts, dates and hours to write; the weighted amount, decision days and pipeline totals fill in by themselves.', [
    C('grant_id', 'Grant ID', 'text', 9, required=True), C('funder', 'Funder', 'text', 26), LST('funder_type', 'Funder type', 'ftype', 18), LST('program', 'Program', 'gprogram', 22), C('project', 'Project', 'text', 24),
    LST('fund', 'Fund', 'fund', 22), LST('stage', 'Stage', 'gstage', 16), C('asked', 'Asked', 'money', 11), C('awarded', 'Awarded', 'num', 11), C('probability', 'Probability', 'pct', 10), LST('owner', 'Owner', 'staff', 16),
    C('prospect_on', 'Prospect on', 'date', 11), C('loi_on', 'Inquiry sent on', 'date', 11), C('applied_on', 'Applied on', 'date', 11), C('decision_on', 'Decision on', 'date', 11), C('expected_on', 'Decision expected on', 'date', 11),
    C('start_on', 'Start on', 'date', 11), C('end_on', 'End on', 'date', 11), C('write_hours', 'Hours to write', 'int', 9), C('restricted', 'Restricted', 'bool', 9), C('phone', 'Funder phone', 'text', 18), C('visit_on', 'Visit on', 'date', 11),
    CA('weighted', 'Weighted amount', 'money', 'IF({col:awarded}>0,{col:awarded},IF(OR({col:stage}=%s,{col:stage}=%s),0,ROUND({col:asked}*{col:probability},0)))' % (STG('Declined'), STG('Withdrawn')), 12),
    CA('won', 'Won', 'int', 'IF({col:awarded}>0,1,0)', 6), CA('decided', 'Decided', 'int', 'IF(OR({col:awarded}>0,{col:stage}=%s),1,0)' % STG('Declined'), 7),
    CA('days_to_decision', 'Days to decision', 'int', 'IF({col:expected_on}>0,{col:expected_on}-{today},"")', 9), CA('write_cost', 'Cost to write', 'money', '{col:write_hours}*{set:write_cost_hour}', 10),
    CA('pipe_n', 'Grants in the pipeline', 'int', CNT_OPEN(), 9), CA('pipe_weighted', 'Weighted pipeline', 'money', SUM_OPEN('weighted'), 12), CPH('dev_phone', 'Development manager phone', D.DEV_PHONE), ORG()],
    D.grants_d(), 300, [A('stage', '= ' + STG('Awarded'), 'good'), A('stage', '= ' + STG('Declined'), 'warn')]))
# 2 grant payments ----------------------------------------------------------
tables.append(T('grant_payments', 'Grant Payments', 'Grant instalments with the days late',
    'One row per instalment: due date, amount, date received and status; the days late, the timing and the funder phone fill in by themselves.', [
    C('pay_id', 'Pay ID', 'text', 9, required=True), C('grant_id', 'Grant ID', 'text', 9), C('funder', 'Funder', 'text', 26), C('number', 'Number', 'int', 8), C('due_date', 'Due date', 'date', 11), C('amount', 'Amount', 'money', 11),
    C('received_on', 'Received on', 'date', 11), LST('status', 'Status', 'gpay', 10),
    CA('days_late', 'Days late', 'int', 'IF({col:received_on}>0,0,IF({today}-{col:due_date}>{set:late_after_days},{today}-{col:due_date},0))', 8), CA('days_to_due', 'Days to due', 'int', 'IF({col:received_on}>0,"",{col:due_date}-{today})', 8),
    CA('timing', 'Timing', 'text', 'IF({col:received_on}>0,IF({col:received_on}<={col:due_date}+{set:late_after_days},%s,%s),IF({col:days_late}>0,%s,%s))' % (c1('Received on time'), c1('Received late'), c1('Open and late'), c1('Open, not due yet')), 16),
    CA('rank_score', 'Chase score', 'int', 'IF({col:days_late}>0,ROUND({col:amount}*{col:days_late}/50000,0)*1000+VALUE(RIGHT({col:pay_id},3)),0)', 12),
    CA('project', 'Project', 'text', LKT('grants.project', 'grants.grant_id', 'grant_id'), 22), FPH(), CPH('dev_phone', 'Development manager phone', D.DEV_PHONE), ORG()],
    D.payments_d(), 300, [A('timing', '= ' + c1('Open and late'), 'bad'), A('timing', '= ' + c1('Received late'), 'warn'), A('status', '= ' + RCV, 'good')]))
# 3 grant reports -----------------------------------------------------------
def ACT(col, kc='grant_actual.grant_id'): return 'IFERROR(INDEX({range:grant_actual.%s},MATCH({col:grant_id},{range:%s},0)),"")' % (col, kc)
tables.append(T('grant_reports', 'Grant Reports', 'Funder reports due, submitted and late',
    'One row per report: kind, due date, submission and status; the days to due, the timing, the spending against the period and the action (write now, start or on time) fill in by themselves.', [
    C('report_id', 'Report ID', 'text', 9, required=True), C('grant_id', 'Grant ID', 'text', 9), C('funder', 'Funder', 'text', 26), LST('kind', 'Kind', 'rkind', 11), C('due_date', 'Due date', 'date', 11), C('submitted_on', 'Submitted on', 'date', 11),
    LST('status', 'Status', 'rstatus', 12), LST('owner', 'Owner', 'staff', 16),
    CA('days_to_due', 'Days to due', 'int', 'IF({col:status}=%s,"",{col:due_date}-{today})' % SUBM, 8),
    CA('timing', 'Timing', 'text', 'IF({col:status}=%s,IF({col:submitted_on}<={col:due_date},%s,%s),IF({col:due_date}<{today},%s,%s))' % (SUBM, c1('Submitted on time'), c1('Submitted late'), c1('Open and late'), c1('Open, not due yet')), 16),
    CA('project', 'Project', 'text', LKT('grants.project', 'grants.grant_id', 'grant_id'), 22), CA('share_spent', 'Share spent', 'pct', ACT('share_spent'), 9), CA('elapsed', 'Share of the period', 'pct', ACT('elapsed'), 9),
    CA('gap', 'Spent minus period', 'pct', 'IF(AND(ISNUMBER({col:share_spent}),ISNUMBER({col:elapsed})),{col:share_spent}-{col:elapsed},"")', 9),
    CA('action', 'Action', 'text', 'IF({col:status}=%s,"",IF(OR({col:days_to_due}<=14,AND({col:days_to_due}<={set:report_warn_days},IF(ISNUMBER({col:gap}),{col:gap}<-{set:spend_margin},FALSE))),%s,IF({col:days_to_due}<={set:report_warn_days},%s,%s)))' % (SUBM, c2('Write now'), c2('Start'), c2('On time')), 11),
    CA('rank_score', 'Urgency score', 'int', 'IF({col:status}=%s,0,(500-MAX(-400,{col:days_to_due}))*1000+VALUE(RIGHT({col:report_id},3)))' % SUBM, 12),
    CA('due_n', 'Reports due in the warning days', 'int', 'COUNTIFS({range:grant_reports.status},"<>"&%s,{range:grant_reports.due_date},"<="&({today}+{set:report_warn_days}))' % SUBM, 9), CA('warn_days', 'Warning days', 'int', '{set:report_warn_days}', 8),
    FPH(), CPH('dev_phone', 'Development manager phone', D.DEV_PHONE), CPH('pm_phone', 'Program manager phone', D.PM_PHONE), CPH('vol_phone', 'Volunteer phone', D.VOL_PHONE), ORG()],
    D.reports_d(), 300, [A('timing', '= ' + c1('Open and late'), 'bad'), A('timing', '= ' + c1('Submitted late'), 'warn'), A('status', '= ' + SUBM, 'good')]))
# 4 budget lines ------------------------------------------------------------
tables.append(T('grant_budget_lines', 'Grant Budget Lines', 'Budget lines of each grant',
    'One row per budget line of a grant (staff, direct costs, other costs); the funder and the share of the grant fill in by themselves.', [
    C('line_id', 'Line ID', 'text', 9, required=True), C('grant_id', 'Grant ID', 'text', 9), LST('line', 'Line', 'gline', 14), C('budget', 'Budget', 'money', 11),
    CA('funder', 'Funder', 'text', LKT('grants.funder', 'grants.grant_id', 'grant_id'), 26),
    CA('share', 'Share of the grant', 'pct', 'IFERROR({col:budget}/SUMIFS({range:grant_budget_lines.budget},{range:grant_budget_lines.grant_id},{col:grant_id}),0)', 9)], D.budget_lines_d(), 200))
# 5 funder types ------------------------------------------------------------
tables.append(T('funder_types', 'Funder Types', 'Funder types with the note on each',
    'One row per funder type: a short note on how this kind of funder works and how heavy its reporting is (1 light, 5 heavy), your own view.', [
    LST('funder_type', 'Funder type', 'ftype', 22, required=True), C('win_note', 'How this funder works', 'text', 30), C('reporting_weight', 'Reporting weight', 'int', 9)], D.funder_types_d(), 50))
# 6 grant stages ------------------------------------------------------------
tables.append(T('grant_stages', 'Grant Stages', 'Grant stages with the chance of an award',
    'One row per stage: the order and the chance of an award; the chances of the three open stages come from the settings on the Start sheet and are your estimate.', [
    LST('stage', 'Stage', 'gstage', 18, required=True), C('order', 'Order', 'int', 7),
    CA('probability', 'Chance of an award', 'pct', 'IF({col:stage}=%s,{set:prob_prospect},IF({col:stage}=%s,{set:prob_inquiry},IF({col:stage}=%s,{set:prob_applied},IF(OR({col:stage}=%s,{col:stage}=%s),1,0))))' % (STG('Prospect'), STG('Letter of inquiry'), STG('Application'), STG('Awarded'), STG('Closed out')), 10)],
    D.stages_d(), 50))
# 7 pipeline by stage -------------------------------------------------------
tables.append(T('pipeline_stage', 'Pipeline by Stage', 'Money asked and weighted at each stage',
    'One row per stage: the money asked and the weighted amount of the grants at that stage, taken from the Grants sheet.', [
    LST('stage', 'Stage', 'gstage', 18, required=True), CA('asked', 'Asked', 'money', 'SUMIFS({range:grants.asked},{range:grants.stage},{col:stage})', 12),
    CA('weighted', 'Weighted amount', 'money', 'SUMIFS({range:grants.weighted},{range:grants.stage},{col:stage})', 12)], D.pipeline_d(), 50))
# 8 income by quarter -------------------------------------------------------
def QW(col, a, b): return 'SUMIFS({range:%s},{range:%s},">="&%s,{range:%s},"<"&%s)' % (col, a, '{col:quarter_start}', a, b)
tables.append(T('income_quarter', 'Income by Quarter', 'Grant income by quarter against the budget',
    'One row per quarter, four past and eight ahead: instalments due, weighted pipeline, the total against a quarter of your budget and reports due fill in.', [
    C('quarter_start', 'Quarter starts', 'date', 12, required=True),
    CA('quarter_end', 'Quarter ends', 'date', 'EOMONTH({col:quarter_start},2)', 11),
    CA('awarded_inst', 'Awarded instalments', 'money', 'SUMIFS({range:grant_payments.amount},{range:grant_payments.due_date},">="&{col:quarter_start},{range:grant_payments.due_date},"<"&EDATE({col:quarter_start},3))', 12),
    CA('weighted', 'Weighted pipeline', 'money', 'SUMIFS({range:grants.weighted},{range:grants.expected_on},">="&{col:quarter_start},{range:grants.expected_on},"<"&EDATE({col:quarter_start},3))', 12),
    CA('total', 'Total', 'money', '{col:awarded_inst}+{col:weighted}', 12), CA('needed', 'A quarter of the budget', 'money', 'ROUND({set:grant_income_budget}/4,0)', 12),
    CA('gap', 'Over or short', 'money', '{col:total}-{col:needed}', 12), CA('status', 'Status', 'text', 'IF({col:gap}>=0,%s,%s)' % (c2('Covered'), c2('Short')), 9),
    CA('reports_due', 'Reports due', 'int', 'COUNTIFS({range:grant_reports.due_date},">="&{col:quarter_start},{range:grant_reports.due_date},"<"&EDATE({col:quarter_start},3))', 8),
    CA('pay_due', 'Instalments due', 'int', 'COUNTIFS({range:grant_payments.due_date},">="&{col:quarter_start},{range:grant_payments.due_date},"<"&EDATE({col:quarter_start},3))', 8), ORG(), CPH('ed_phone', 'Executive director phone', D.ED_PHONE)],
    D.income_quarter_d(), 50, [A('status', '= ' + c2('Short'), 'warn'), A('status', '= ' + c2('Covered'), 'good')]))
# 9 win rate ----------------------------------------------------------------
PER = [('all', 'All decisions'), ('last12', 'Last 12 months')]
DEC12 = '{range:grants.decision_on},">="&({today}-365)'
def won_f(period): return 'IF({col:period}=%s,COUNTIFS({range:grants.funder_type},{col:funder_type},{range:grants.awarded},">0",%s),COUNTIFS({range:grants.funder_type},{col:funder_type},{range:grants.awarded},">0"))' % (period, DEC12)
def lost_f(period): return 'IF({col:period}=%s,COUNTIFS({range:grants.funder_type},{col:funder_type},{range:grants.stage},%s,%s),COUNTIFS({range:grants.funder_type},{col:funder_type},{range:grants.stage},%s))' % (period, STG('Declined'), DEC12, STG('Declined'))
tables.append(T('win_rate', 'Win Rate by Funder Type', 'Own win rate by funder type and period',
    'One row per funder type and period: decided applications, awards and the win rate from your own history; the note compares each rate with your own average.', [
    LST('funder_type', 'Funder type', 'ftype', 22, required=True), LST('period', 'Period', 'period', 15),
    CA('won', 'Won', 'int', None, 7), CA('lost', 'Declined', 'int', None, 8), CA('submitted', 'Decided', 'int', '{col:won}+{col:lost}', 8),
    CA('win_rate', 'Win rate', 'pct', 'IF({col:submitted}>0,{col:won}/{col:submitted},0)', 9),
    CA('all_rate', 'Your average rate', 'pct', 'IFERROR(SUMIFS({range:win_rate.won},{range:win_rate.period},{col:period})/SUMIFS({range:win_rate.submitted},{range:win_rate.period},{col:period}),0)', 9),
    CA('note', 'Own history note', 'text', 'IF({col:submitted}<3,%s,IF({col:win_rate}>{col:all_rate}+0.05,%s,IF({col:win_rate}<{col:all_rate}-0.05,%s,%s)))' % (c1('Too few decisions'), c1('Above your average'), c1('Below your average'), c1('Near your average')), 18),
    CA('qualified', 'Rate with 3 or more decisions', 'pct', 'IF({col:submitted}>=3,{col:win_rate},0)', 9)], D.win_rate_d(), 50, [A('note', '= ' + c1('Above your average'), 'good'), A('note', '= ' + c1('Below your average'), 'warn')]))
# 10 next 90 days calendar --------------------------------------------------
def CL(pay, rep, pay_id='pay_id', rep_id='report_id'):
    return 'IF({col:kind}=%s,IFERROR(INDEX({range:grant_payments.%s},MATCH({col:item_id},{range:grant_payments.%s},0)),""),IFERROR(INDEX({range:grant_reports.%s},MATCH({col:item_id},{range:grant_reports.%s},0)),""))' % (tok('ckind', 'Instalment'), pay, pay_id, rep, rep_id)
tables.append(T('calendar90', 'Next 90 Days Calendar', 'Instalments and reports in date order for the next 90 days',
    'One row per instalment or report: type the pay or report ID and its kind; the date, grant, funder, amount, owner, days away and the late flag fill in, and the sort key puts the rows in date order.', [
    C('item_id', 'Pay or report ID', 'text', 10, required=True), LST('kind', 'Kind', 'ckind', 11),
    CA('date', 'Due date', 'date', CL('due_date', 'due_date'), 11), CA('grant_id', 'Grant ID', 'text', CL('grant_id', 'grant_id'), 9), CA('funder', 'Funder', 'text', CL('funder', 'funder'), 26),
    CA('amount', 'Amount', 'money', 'IF({col:kind}=%s,IFERROR(INDEX({range:grant_payments.amount},MATCH({col:item_id},{range:grant_payments.pay_id},0)),""),"")' % tok('ckind', 'Instalment'), 11),
    CA('owner', 'Owner', 'text', 'IF({col:kind}=%s,IFERROR(INDEX({range:grants.owner},MATCH({col:grant_id},{range:grants.grant_id},0))&"",""),IFERROR(INDEX({range:grant_reports.owner},MATCH({col:item_id},{range:grant_reports.report_id},0))&"",""))' % tok('ckind', 'Instalment'), 16),
    CA('done_on', 'Done on', 'date', 'IF({col:kind}=%s,IFERROR(IF(INDEX({range:grant_payments.received_on},MATCH({col:item_id},{range:grant_payments.pay_id},0))=0,"",INDEX({range:grant_payments.received_on},MATCH({col:item_id},{range:grant_payments.pay_id},0))),""),IFERROR(IF(INDEX({range:grant_reports.submitted_on},MATCH({col:item_id},{range:grant_reports.report_id},0))=0,"",INDEX({range:grant_reports.submitted_on},MATCH({col:item_id},{range:grant_reports.report_id},0))),""))' % tok('ckind', 'Instalment'), 11),
    CA('days_away', 'Days away', 'int', 'IF(ISNUMBER({col:date}),{col:date}-{today},"")', 8),
    CA('state', 'State', 'text', 'IF(ISNUMBER({col:done_on}),%s,IF({col:date}<{today},%s,IF({col:date}<={today}+7,%s,%s)))' % (c1('Done'), c1('Late'), c1('Due this week'), c1('Coming up')), 14),
    CA('sort_key', 'Sort key', 'num', 'IF(AND(ISNUMBER({col:date}),NOT(ISNUMBER({col:done_on}))),{col:date}+VALUE(RIGHT({col:item_id},3))/1000+IF({col:kind}=%s,0.0005,0),"")' % tok('ckind', 'Report'), 11),
    CA('late_n', 'Late items', 'int', 'COUNTIFS({range:calendar90.state},%s)' % c1('Late'), 8), CA('week_n', 'Due this week', 'int', 'COUNTIFS({range:calendar90.state},%s)' % c1('Due this week'), 8),
    CA('open_n', 'Open items', 'int', 'COUNTIFS({range:calendar90.state},"<>"&%s,{range:calendar90.date},">0")' % c1('Done'), 8),
    CA('open_money', 'Money still to come', 'money', 'SUMIFS({range:calendar90.amount},{range:calendar90.state},"<>"&%s)' % c1('Done'), 12), ORG()],
    D.calendar_d(), 60, [A('state', '= ' + c1('Late'), 'bad'), A('state', '= ' + c1('Due this week'), 'warn'), A('state', '= ' + c1('Done'), 'good')]))
# 11 grant spending ---------------------------------------------------------
tables.append(T('grant_spending', 'Grant Spending', 'Spending coded to each grant',
    'One row per expense coded to a grant: date, grant, category, amount, program, fund and budget line; the funder fills in by itself.', [
    C('expense_id', 'Expense ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), C('grant_id', 'Grant ID', 'text', 9), LST('category', 'Category', 'gcat', 18), C('amount', 'Amount', 'money', 11),
    LST('program', 'Program', 'gprogram', 22), LST('fund', 'Fund', 'fund', 22), LST('line', 'Budget line', 'gline', 14),
    CA('funder', 'Funder', 'text', LKT('grants.funder', 'grants.grant_id', 'grant_id'), 26),
    CA('is_restricted', 'Restricted fund', 'int', 'IF(%s,1,0)' % IS_RESTRICTED(LKT('funds.restriction', 'funds.fund', 'fund')), 7), CPH('bk_phone', 'Bookkeeper phone', D.BK_PHONE), ORG()], D.spending_d(), 900))
# 12 grant budget against actual --------------------------------------------
def GA(col, kind='N'):
    f = {'N': LKN, 'T': LKT, 'D': LKD}[kind]; return f('grants.' + col, 'grants.grant_id', 'grant_id')
tables.append(T('grant_actual', 'Grant Budget vs Actual', 'Each grant: spent against the award and period',
    'One row per grant with a budget: the spending, what is left, the share of the period against the share spent, the forecast to the end date and the status fill in from the Grant Spending sheet.', [
    C('grant_id', 'Grant ID', 'text', 9, required=True), LST('funder_type', 'Funder type', 'ftype', 18),
    CA('funder', 'Funder', 'text', GA('funder', 'T'), 26), CA('project', 'Project', 'text', GA('project', 'T'), 22), CA('awarded', 'Awarded', 'money', GA('awarded'), 11), CA('start_on', 'Start on', 'date', GA('start_on', 'D'), 11), CA('end_on', 'End on', 'date', GA('end_on', 'D'), 11),
    CA('spent', 'Spent', 'money', 'SUMIFS({range:grant_spending.amount},{range:grant_spending.grant_id},{col:grant_id})', 11), CA('remaining', 'Remaining', 'money', '{col:awarded}-{col:spent}', 11),
    CA('elapsed', 'Share of the period', 'pct', 'IF({col:end_on}>{col:start_on},MIN(1,MAX(0,({today}-{col:start_on})/({col:end_on}-{col:start_on}))),0)', 9),
    CA('share_spent', 'Share spent', 'pct', 'IF({col:awarded}>0,{col:spent}/{col:awarded},0)', 9), CA('expected_spend', 'Spend expected by now', 'money', 'ROUND({col:awarded}*{col:elapsed},0)', 11),
    CA('forecast', 'Forecast to the end', 'money', 'IF({col:elapsed}>0,ROUND({col:spent}/{col:elapsed},0),{col:spent})', 11),
    CA('months_left', 'Months left', 'num', 'MAX(0,ROUND(({col:end_on}-{today})/30.4375,1))', 8),
    CA('status', 'Status', 'text', 'IF({col:spent}>{col:awarded},%s,IF({col:end_on}<{today},%s,IF({col:share_spent}<{col:elapsed}-{set:spend_margin},%s,IF({col:forecast}>{col:awarded}*(1+{set:spend_margin}),%s,%s))))' % (c1('Overspending'), c1('Closed'), c1('Underspending'), c1('Overspending'), c1('On track')), 14),
    CA('at_risk', 'Money at risk of return', 'money', 'IF({col:status}=%s,MAX(0,{col:awarded}-{col:forecast}),0)' % c1('Underspending'), 11),
    CA('month_need', 'Spend needed a month', 'money', 'IF({col:months_left}>0,ROUND({col:remaining}/{col:months_left},0),0)', 11), CA('new_end', 'End date plus 3 months', 'date', 'IF(ISNUMBER({col:end_on}),EDATE({col:end_on},3),"")', 11),
    CA('under_n', 'Grants underspent', 'int', 'COUNTIFS({range:grant_actual.status},%s)' % c1('Underspending'), 8), CA('risk_total', 'Money at risk in all grants', 'money', 'SUM({range:grant_actual.at_risk})', 11),
    FPH(), CPH('po_phone', 'Program officer phone', D.PO_PHONE), CPH('ed_phone', 'Executive director phone', D.ED_PHONE), CPH('pm_phone', 'Program manager phone', D.PM_PHONE), ORG()],
    D.actual_d(), 60, [A('status', '= ' + c1('Underspending'), 'warn'), A('status', '= ' + c1('Overspending'), 'bad'), A('status', '= ' + c1('On track'), 'good')]))
# 13 grant spending by line -------------------------------------------------
tables.append(T('grant_lines', 'Grant Spending by Line', 'Budget and spending of every grant line',
    'One row per budget line of a grant: the budget, the spending, what is left, the share used and a status against the share of the period fill in by themselves.', [
    C('line_no', 'Line ID', 'text', 9, required=True), C('grant_id', 'Grant ID', 'text', 9), LST('line', 'Line', 'gline', 14),
    CA('funder', 'Funder', 'text', LKT('grants.funder', 'grants.grant_id', 'grant_id'), 26),
    CA('budget', 'Budget', 'money', 'SUMIFS({range:grant_budget_lines.budget},{range:grant_budget_lines.grant_id},{col:grant_id},{range:grant_budget_lines.line},{col:line})', 11),
    CA('spent', 'Spent', 'money', 'SUMIFS({range:grant_spending.amount},{range:grant_spending.grant_id},{col:grant_id},{range:grant_spending.line},{col:line})', 11), CA('remaining', 'Remaining', 'money', '{col:budget}-{col:spent}', 11),
    CA('share_used', 'Share used', 'pct', 'IF({col:budget}>0,{col:spent}/{col:budget},0)', 9), CA('over_by', 'Over by', 'money', 'MAX(0,{col:spent}-{col:budget})', 10), CA('spare', 'Spare', 'money', 'MAX(0,{col:budget}-{col:spent})', 10),
    CA('elapsed', 'Share of the period', 'pct', 'IFERROR(INDEX({range:grant_actual.elapsed},MATCH({col:grant_id},{range:grant_actual.grant_id},0)),0)', 9),
    CA('status', 'Status', 'text', 'IF({col:spent}>{col:budget},%s,IF({col:share_used}<{col:elapsed}-{set:spend_margin},%s,%s))' % (c1('Over budget'), c1('Under budget'), c1('Within budget')), 14),
    FPH(), CPH('acc_phone', 'Accountant phone', D.ACC_PHONE), ORG()], D.lines_d(), 150, [A('status', '= ' + c1('Over budget'), 'bad'), A('status', '= ' + c1('Under budget'), 'warn')]))
# 14 funds ------------------------------------------------------------------
tables.append(T('funds', 'Funds', 'Funds: general, board-designated and restricted',
    'One row per fund: its restriction (money given for one purpose is restricted) and the opening balance at the start of your history.', [
    LST('fund', 'Fund', 'fund', 24, required=True), LST('restriction', 'Restriction', 'fundkind', 20), C('opening_balance', 'Opening balance', 'money', 14)], D.funds_d(), 50))
# 15 fund months ------------------------------------------------------------
def FM(col): return 'SUMIFS({range:fund_months.%s},{range:fund_months.fund},{col:fund},{range:fund_months.month},">="&DATE(YEAR({col:month}),1,1),{range:fund_months.month},"<="&{col:month})' % col
NEAR = '+'.join('COUNTIFS({range:fund_months.month},%s,{range:fund_months.restriction},%s,{range:fund_months.balance},"<"&{set:near_zero_limit})' % (MS, r) for r in RESTRICTED)
tables.append(T('fund_months', 'Fund Months', 'Receipts, releases and balance of every fund by month',
    'One row per fund and month: receipts, money released from restriction, transfers and the closing balance; the restriction, the year to date and the below-zero amount fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('fund', 'Fund', 'fund', 22), C('receipts', 'Receipts', 'money', 11), C('released', 'Released', 'money', 11), C('transfers', 'Transfers', 'num', 10), C('balance', 'Balance', 'money', 12),
    CA('restriction', 'Restriction', 'text', LKT('funds.restriction', 'funds.fund', 'fund'), 18),
    CA('restricted_bal', 'Restricted balance', 'money', 'IF(%s,{col:balance},0)' % IS_RESTRICTED('{col:restriction}'), 12), CA('designated_bal', 'Designated balance', 'money', 'IF({col:restriction}=%s,{col:balance},0)' % tok('fundkind', 'Board-designated'), 12),
    CA('receipts_ytd', 'Receipts, year to date', 'money', FM('receipts'), 12), CA('released_ytd', 'Released, year to date', 'money', FM('released'), 12),
    CA('below_by', 'Below zero by', 'money', 'MAX(0,-{col:balance})', 10), CA('spare', 'Money left', 'money', 'MAX(0,{col:balance})', 10), CA('plan_month', 'Plan spending for', 'date', 'EDATE({col:month},1)', 11),
    CA('as_of', 'As of', 'date', '{today}', 11), CA('near_n', 'Restricted funds near zero', 'int', NEAR, 8),
    CPH('bk_phone', 'Bookkeeper phone', D.BK_PHONE), CPH('pm_phone', 'Program manager phone', D.PM_PHONE), CPH('acc_phone', 'Accountant phone', D.ACC_PHONE), CPH('treas_phone', 'Treasurer phone', D.TREAS_PHONE), ORG()],
    D.fund_months_d(), 450, [A('balance', '< 0', 'bad')]))
# 16 fund position ----------------------------------------------------------
def FMS(col): return 'SUMIFS({range:fund_months.%s},{range:fund_months.fund},{col:fund},{range:fund_months.month},{col:month})' % col
tables.append(T('fund_position', 'Fund Position', 'Balance of each fund this month and last',
    'One row per fund and month (this and last): receipts, releases, transfers and balance fill in from Fund Months, with a flag when a fund is below zero.', [
    LST('fund', 'Fund', 'fund', 22, required=True), C('month', 'Month', 'date', 11),
    CA('restriction', 'Restriction', 'text', LKT('funds.restriction', 'funds.fund', 'fund'), 18), CA('receipts', 'Receipts', 'money', FMS('receipts'), 11), CA('released', 'Released', 'money', FMS('released'), 11),
    CA('transfers', 'Transfers', 'money', FMS('transfers'), 10), CA('balance', 'Balance', 'money', FMS('balance'), 12), CA('opening', 'Opening', 'money', '{col:balance}-{col:receipts}+{col:released}-{col:transfers}', 12),
    CA('status', 'Flag', 'text', 'IF({col:balance}<0,%s,IF(AND(%s,{col:balance}<{set:near_zero_limit}),%s,%s))' % (c1('Below zero'), IS_RESTRICTED('{col:restriction}'), c1('Near zero'), c1('OK')), 11),
    CA('is_now', 'This month', 'int', 'IF({col:month}=%s,1,0)' % MS, 7), CA('restricted_balance', 'Restricted balance', 'money', 'IF(%s,{col:balance},0)' % IS_RESTRICTED('{col:restriction}'), 12),
    CA('is_restricted', 'Restricted fund', 'int', 'IF(%s,1,0)' % IS_RESTRICTED('{col:restriction}'), 7), CA('ok_restricted', 'Restricted and at or above zero', 'int', 'IF(AND(%s,{col:balance}>=0),1,0)' % IS_RESTRICTED('{col:restriction}'), 7)],
    D.fund_position_d_full(), 50, [A('status', '= ' + c1('Below zero'), 'bad'), A('status', '= ' + c1('Near zero'), 'warn')]))
# 17 release journal --------------------------------------------------------
tables.append(T('release_journal', 'Release Journal', 'Releases from restriction by date, fund and grant',
    'One row per release from restriction (spent money moved from a restricted fund to expense): date, fund, amount, program and grant; the funder fills in by itself.', [
    C('release_id', 'Release ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), LST('fund', 'Fund', 'fund', 22), C('amount', 'Amount', 'money', 11), LST('program', 'Program', 'program', 22), C('grant_id', 'Grant ID', 'text', 9),
    CA('funder', 'Funder', 'text', LKT('grants.funder', 'grants.grant_id', 'grant_id'), 26),
    CA('on_grant', 'Coded to a grant', 'int', 'IF(LEN({col:grant_id})>0,1,0)', 7), CPH('bk_phone', 'Bookkeeper phone', D.BK_PHONE), ORG()], D.release_d(), 700))
# 18 free money position ----------------------------------------------------
tables.append(T('free_money', 'Free Money Position', 'Free money in months of reserve',
    'One row per month: type cash and average monthly expense; restricted and designated money, free money (cash less both) and months of reserve fill in.', [
    C('month', 'Month', 'date', 11, required=True), C('cash', 'Cash', 'money', 12), C('avg_expense', 'Average monthly expense', 'money', 12),
    CA('restricted', 'Restricted money', 'money', 'SUMIFS({range:fund_months.restricted_bal},{range:fund_months.month},{col:month})', 12), CA('designated', 'Designated money', 'money', 'SUMIFS({range:fund_months.designated_bal},{range:fund_months.month},{col:month})', 12),
    CA('free_money', 'Free money', 'money', '{col:cash}-{col:restricted}-{col:designated}', 12), CA('reserve_months', 'Months of reserve', 'num', 'IF({col:avg_expense}>0,ROUND({col:free_money}/{col:avg_expense},2),0)', 9),
    CA('status', 'Status', 'text', 'IF({col:reserve_months}>={set:reserve_months},%s,%s)' % (c1('Healthy'), c1('Below the setting')), 14), CA('target_money', 'Free money the setting asks for', 'money', 'ROUND({set:reserve_months}*{col:avg_expense},0)', 12),
    CA('is_now', 'This month', 'int', 'IF({col:month}=%s,1,0)' % MS, 7), CPH('treas_phone', 'Treasurer phone', D.TREAS_PHONE), ORG()], D.free_money_d(), 60, [A('status', '= ' + c1('Below the setting'), 'warn'), A('status', '= ' + c1('Healthy'), 'good')]))
# 19 staff time -------------------------------------------------------------
tables.append(T('staff_time', 'Staff Time', 'Staff time split across grants and programs',
    'One row per staff member, month and target: the share of the month, the hours and the cost; every staff month should total 100% (see Staff Time Check).', [
    C('time_id', 'Time ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), LST('staff', 'Staff', 'staff', 18), LST('target_kind', 'Target', 'tkind', 13), C('grant_id', 'Grant ID', 'text', 9), LST('program', 'Program', 'sprogram', 22),
    C('function', 'Function', 'text', 12), C('percent', 'Percent', 'pct', 9), C('hours', 'Hours', 'num', 9), C('cost', 'Cost', 'money', 11)], D.staff_time_d(), 1800))
# 20 staff time check -------------------------------------------------------
def STM(extra=''): return 'SUMIFS({range:staff_time.percent},{range:staff_time.staff},{col:staff},{range:staff_time.month},{col:month}%s)' % extra
tables.append(T('staff_check', 'Staff Time Check', 'Does every staff month total 100%',
    'One row per staff member and month: the total percent, the difference from 100%, a flag and the cost charged to grants fill in from the Staff Time sheet.', [
    C('check_id', 'Check ID', 'text', 9, required=True), LST('staff', 'Staff', 'staff', 18), C('month', 'Month', 'date', 11), C('phone', 'Staff phone', 'text', 18),
    CA('total_percent', 'Total percent', 'pct', STM(), 9), CA('diff', 'Difference from 100%', 'pct', '{col:total_percent}-1', 9),
    CA('flag', 'Flag', 'text', 'IF(ABS({col:diff})<={set:time_tolerance},%s,IF({col:diff}<0,%s,%s))' % (c1('Totals 100%'), c1('Short of 100%'), c1('Over 100%')), 14),
    CA('grant_percent', 'Percent on grants', 'pct', STM(',{range:staff_time.target_kind},%s' % tok('tkind', 'Grant')), 9),
    CA('cost_to_grants', 'Cost to grants', 'money', 'SUMIFS({range:staff_time.cost},{range:staff_time.staff},{col:staff},{range:staff_time.month},{col:month},{range:staff_time.target_kind},%s)' % tok('tkind', 'Grant'), 11),
    CA('total_cost', 'Total cost', 'money', 'SUMIFS({range:staff_time.cost},{range:staff_time.staff},{col:staff},{range:staff_time.month},{col:month})', 11), CPH('bk_phone', 'Bookkeeper phone', D.BK_PHONE), ORG()],
    D.staff_check_d(), 60, [A('flag', '= ' + c1('Short of 100%'), 'warn'), A('flag', '= ' + c1('Over 100%'), 'bad'), A('flag', '= ' + c1('Totals 100%'), 'good')]))
assert len(tables) == 20, len(tables)

# the win rate counts need the period list, which lives in lists
for t in tables:
    if t['key'] == 'win_rate':
        PA, PB = tok('period', 'All decisions'), tok('period', 'Last 12 months')
        for c in t['columns']:
            if c['key'] == 'won': c['formula'] = won_f(PB)
            if c['key'] == 'lost': c['formula'] = lost_f(PB)
