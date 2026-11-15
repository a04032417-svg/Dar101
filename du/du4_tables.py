"""Doula suite part 4: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du4_lists import *
import du4_data as D


def R(t, c): return '{range:%s.%s}' % (t, c)
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def PH_TEAM(col, key_='phone', label='Phone'): return CA(key_, label, 'text', 'IFERROR(INDEX({range:team.phone},MATCH({col:%s},{range:team.name},0))&"","")' % col, 18)
def OWNER_PH(): return CA('owner_phone', 'Owner-doula phone', 'text', '"%s"' % D.OWNER_PHONE, 18)
def ADMIN_PH(): return CA('admin_phone', 'Admin phone', 'text', '"%s"' % D.ADMIN_PHONE, 18)
def COMP(): return CA('company', 'Agency', 'text', '{set:company}', 22)

OS, OE, OD, OB, OEDD, OCL = R('oncall', 'oncall_start'), R('oncall', 'oncall_end'), R('oncall', 'doula'), R('oncall', 'backup'), R('oncall', 'edd'), R('oncall', 'client')
DOUS, DCAP = R('doulas', 'doula'), R('doulas', 'cap_births')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YES = '{list:yesno.yes}'
PP = tok('service', 'Postpartum')
PPK = tok('ckind', 'Postpartum')
WEEK = '{today}-WEEKDAY({today},2)+1+7*{col:week_no}'
def CNT_D(a, b): return 'COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s)' % (OD, DOUS, OS, b, OE, a)      # open windows per doula (array over the Doulas table) overlapping a..b

settings = [
    S('company', 'Your agency name', 'text', COMPANY),
    S('oncall_before_days', 'On-call starts this many days before the due date', 'int', ONCALL_BEFORE),
    S('oncall_after_days', 'On-call ends this many days after the due date', 'int', ONCALL_AFTER),
    S('max_oncall_overlap', 'Most on-call windows of one doula at the same time', 'int', MAX_OVERLAP),
    S('cap_births_month', 'Most due dates of one doula in a month', 'int', CAP_BIRTHS),
    S('agency_cap_month', 'Most due dates the agency takes in a month', 'int', 7),
    S('backup_load_max', 'Most windows one backup doula covers in a week', 'int', 4),
    S('backup_flat_pay', 'Flat call-out pay when a backup attends', 'money', BACKUP_FLAT_PAY),
    S('backup_stipend_week', 'Weekly stipend of a backup doula on the rota', 'money', BACKUP_STIPEND_WEEK),
    S('stipend_plan_month', 'Planned backup stipends in one month', 'money', 400),
    S('cover_alert_days', 'Days ahead to look for windows without a backup', 'int', 90),
    S('window_alert_days', 'Days ahead to warn that a window opens', 'int', 14),
    S('back_to_back_days', 'Due dates closer than this many days are back to back', 'int', 10),
    S('agency_cost_client', 'Agency overhead per client', 'money', AGENCY_COST_CLIENT),
]
assert 3 <= len(settings) <= 20

tables = []
# ---------------------------------------------------------------- 1 on-call windows
tables.append(T('oncall', 'On-Call Windows', 'On-call windows of every client with a due date',
    'One row per client window: doula, backup, estimated due date, on-call start and end and the contact hours; the window days, cover check and overlap check fill in by themselves.', [
    C('window_id', 'Window ID', 'text', 10, required=True), REF('client_id', 'Client ID', 'clients.client_id', 10), REF('client', 'Client', 'clients.client', 22), LST('doula', 'Doula', 'bdoula', 16),
    LST('backup', 'Backup doula', 'backup', 16), C('edd', 'Estimated due date', 'date', 12), C('oncall_start', 'On-call start', 'date', 12), C('oncall_end', 'On-call end', 'date', 12),
    LST('area', 'Area', 'area', 11), C('attended_on', 'Attended on', 'date', 11), C('contact_hours', 'Contact hours', 'num', 10),
    CA('window_days', 'Window days', 'int', 'IF({col:oncall_start}>0,{col:oncall_end}-{col:oncall_start}+1,"")', 9),
    CA('days_to_open', 'Days to open', 'int', 'IF({col:oncall_start}>0,{col:oncall_start}-{today},"")', 9),
    CA('phase', 'Window phase', 'text', 'IF({col:oncall_end}<{today},%s,IF({col:oncall_start}<={today},%s,%s))' % (tok('phase', 'Closed'), tok('phase', 'Open now'), tok('phase', 'Upcoming')), 12),
    CA('no_backup', 'No backup', 'int', 'IF({col:backup}="",1,0)', 9),
    CA('cover', 'Cover check', 'text', 'IF({col:oncall_end}<{today},%s,IF({col:backup}="",%s,%s))' % (ck('Window closed'), ck('No backup named'), ck('Backup named')), 17),
    CA('overlap', 'Doula windows open on my start day', 'int', 'COUNTIFS(%s,{col:doula},%s,"<="&{col:oncall_start},%s,">="&{col:oncall_start})' % (OD, OS, OE), 11),
    CA('overlap_flag', 'Overlap check', 'text', 'IF({col:overlap}>{set:max_oncall_overlap},%s,%s)' % (ck('Over the limit'), ck('Within the limit')), 15),
    CA('load_30', 'Doula windows, next 30 days', 'int', 'COUNTIFS(%s,{col:doula},%s,"<="&({today}+30),%s,">="&{today})' % (OD, OS, OE), 11),
    CA('b2b', 'Other due dates close by', 'int', 'COUNTIFS(%s,{col:doula},%s,">="&({col:edd}-{set:back_to_back_days}),%s,"<="&({col:edd}+{set:back_to_back_days}))-1' % (OD, OEDD, OEDD), 11),
    CA('next_start', 'Doula next window opens', 'date', 'IF(COUNTIFS(%s,{col:doula},%s,">"&{col:oncall_start})=0,"",SUMPRODUCT(MIN((%s={col:doula})*(%s>{col:oncall_start})*%s+(1-(%s={col:doula})*(%s>{col:oncall_start}))*99999999)))' % (OD, OS, OD, OS, OS, OD, OS), 12),
    CA('dkey', 'Doula key', 'text', '{col:doula}&"|"&{col:oncall_start}', 12), CA('bkey', 'Backup key', 'text', '{col:backup}&"|"&{col:oncall_start}', 12), CA('ekey', 'Due date key', 'text', '{col:doula}&"|"&{col:edd}', 12),
    CA('phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18), PH_TEAM('doula', 'doula_phone', 'Doula phone'), PH_TEAM('backup', 'backup_phone', 'Backup phone'), COMP()],
    D.oncall_d(), 300, [A('cover', '= ' + ck('No backup named'), 'bad'), A('overlap_flag', '= ' + ck('Over the limit'), 'bad'), A('phase', '= ' + tok('phase', 'Open now'), 'good'), A('backup', '= ""', 'warn')]))
# ---------------------------------------------------------------- 2 clients
tables.append(T('clients', 'Clients', 'Clients with due dates, doula and backup',
    'One row per client (first name and family name, area, due date and package only): the doula, the backup and the status; the days to the due date, on-call dates and cover check fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 22), C('phone', 'Phone', 'text', 18), LST('area', 'Area', 'area', 11), LST('kind', 'Kind', 'ckind', 12),
    LST('package', 'Package', 'package', 22), C('edd', 'Estimated due date', 'date', 12), C('due_month', 'Due month', 'date', 11), LST('doula', 'Doula', 'doula', 16), LST('backup', 'Backup doula', 'backup', 16),
    LST('source', 'Source', 'source', 18), LST('status', 'Status', 'cstatus', 15),
    CA('days_to_edd', 'Days to due date', 'int', 'IF({col:edd}>0,{col:edd}-{today},"")', 9),
    CA('oncall_start', 'On-call start', 'date', 'IF({col:kind}=%s,"",{col:edd}-{set:oncall_before_days})' % PPK, 12), CA('oncall_end', 'On-call end', 'date', 'IF({col:kind}=%s,"",{col:edd}+{set:oncall_after_days})' % PPK, 12),
    CA('cover', 'Cover check', 'text', 'IF(OR({col:kind}=%s,{col:status}=%s,{col:status}=%s,{col:status}=%s),%s,IF({col:backup}="",%s,%s))' % (
        PPK, tok('cstatus', 'Completed'), tok('cstatus', 'Cancelled'), tok('cstatus', 'Postpartum care'), ck('Not needed'), ck('No backup named'), ck('Backup named')), 17),
    PH_TEAM('doula', 'doula_phone', 'Doula phone'), PH_TEAM('backup', 'backup_phone', 'Backup phone'), COMP()],
    D.clients_d(), 400, [A('cover', '= ' + ck('No backup named'), 'bad'), A('status', '= ' + tok('cstatus', 'On call'), 'good'), A('status', '= ' + tok('cstatus', 'Cancelled'), 'warn')]))
# ---------------------------------------------------------------- 3 doulas
tables.append(T('doulas', 'Doulas', 'Doulas with service and monthly due-date cap',
    'One row per doula: the service (a solo doula keeps one row) and the most due dates the doula takes in a month; the capacity tables and tools read these caps.', [
    LST('doula', 'Doula', 'doula', 18, required=True), LST('service', 'Service', 'service', 12), C('cap_births', 'Due dates a month, cap', 'int', 12)],
    D.doulas_d(), 50))
# ---------------------------------------------------------------- 4 backup rota
tables.append(T('rota', 'Backup Rota', 'Backup doula on the rota each week',
    'One row per week: which backup doula is on the rota and the weekly stipend; the windows covered that week, the load check and the message fields fill in by themselves.', [
    C('rota_id', 'Rota ID', 'text', 9, required=True), C('week', 'Week starting Monday', 'date', 12), LST('backup', 'Backup doula', 'backup', 16), C('stipend', 'Stipend', 'int', 9),
    CA('windows', 'Windows covered', 'int', 'COUNTIFS(%s,{col:backup},%s,"<="&({col:week}+6),%s,">="&{col:week})' % (OB, OS, OE), 10),
    CA('flag', 'Load check', 'text', 'IF({col:windows}>{set:backup_load_max},%s,%s)' % (ck('Backup overloaded'), ck('Fine')), 16),
    PH_TEAM('backup', 'backup_phone', 'Backup phone'), ADMIN_PH(), COMP()],
    D.rota_d(), 300, [A('flag', '= ' + ck('Backup overloaded'), 'bad')]))
# ---------------------------------------------------------------- 5 time off
tables.append(T('timeoff', 'Time Off', 'Time off of doulas and backups',
    'One row per time-off block (holiday, family time, rest block, training): holder, start, end and kind; the days, the windows it overlaps and the clash check fill in by themselves.', [
    C('timeoff_id', 'Time-off ID', 'text', 10, required=True), LST('holder', 'Holder', 'holder', 16), C('start', 'Start', 'date', 11), C('end', 'End', 'date', 11), LST('kind', 'Kind', 'toff', 13),
    CA('days', 'Days', 'int', 'IF({col:end}>0,{col:end}-{col:start}+1,"")', 7),
    CA('clashes', 'Windows overlapped', 'int', 'COUNTIFS(%s,{col:holder},%s,"<="&{col:end},%s,">="&{col:start})+COUNTIFS(%s,{col:holder},%s,"<="&{col:end},%s,">="&{col:start})' % (OD, OS, OE, OB, OS, OE), 10),
    CA('status', 'Clash check', 'text', 'IF({col:end}<{today},%s,IF({col:clashes}>0,%s,%s))' % (ck('Past block'), ck('Clash'), ck('Safe to book')), 14),
    PH_TEAM('holder', 'holder_phone', 'Holder phone'), COMP()],
    D.timeoff_d(), 200, [A('status', '= ' + ck('Clash'), 'bad'), A('status', '= ' + ck('Safe to book'), 'good')]))
# ---------------------------------------------------------------- 6 births attended
tables.append(T('births', 'Births Attended', 'Births attended by the assigned doula or a backup',
    'One row per birth attended: date, client, who attended, the assigned doula, the backup if one attended and the hours; the outcome fills in by itself. Dates and hours only, never any detail.', [
    C('birth_id', 'Birth ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('client_id', 'Client ID', 'clients.client_id', 10), REF('client', 'Client', 'clients.client', 22),
    LST('doula', 'Attended by', 'holder', 16), LST('assigned', 'Assigned doula', 'bdoula', 16), LST('backup', 'Backup who attended', 'backup', 16), C('backup_used', 'Backup used', 'bool', 9), C('hours', 'Hours', 'num', 8),
    CA('outcome', 'Outcome', 'text', 'IF({col:backup_used}=%s,%s,%s)' % (YES, ck('Backup attended'), ck('Assigned doula attended')), 22)],
    D.births_d(), 300, [A('outcome', '= ' + ck('Backup attended'), 'warn')]))
# ---------------------------------------------------------------- 7 team
tables.append(T('team', 'Team', 'Team with roles and phones',
    'One row per person: the owner-doula, doulas, backups, the admin and outside contacts; the message links read these phones. A solo doula keeps one row.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 22), LST('role', 'Role', 'role', 20), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 28)],
    D.team_d(), 50))
# ---------------------------------------------------------------- 8 daily load
tables.append(T('daily', 'Daily On-Call Load', 'On-call load for every day ahead',
    'One row per day from 10 days ago to 6 months ahead (type the day number, 0 is today): clients on call, doulas on call and the busiest doula, counted from On-Call Windows; flags fill in by themselves.', [
    C('day_no', 'Day number', 'int', 9, required=True),
    CA('date', 'Date', 'date', '{today}+{col:day_no}', 11),
    CA('clients_on_call', 'Clients on call', 'int', 'COUNTIFS(%s,"<="&{col:date},%s,">="&{col:date})' % (OS, OE), 9),
    CA('doulas_on_call', 'Doulas on call', 'int', 'SUMPRODUCT(--(%s>0))' % CNT_D('{col:date}', '{col:date}'), 9),
    CA('busiest', 'Busiest doula windows', 'int', 'SUMPRODUCT(MAX(%s))' % CNT_D('{col:date}', '{col:date}'), 10),
    CA('two_plus', 'Doula with 2 or more', 'int', 'IF({col:busiest}>=2,1,0)', 9), CA('three_plus', 'Doula with 3 or more', 'int', 'IF({col:busiest}>=3,1,0)', 9),
    CA('limit_flag', 'Limit check', 'text', 'IF({col:busiest}>{set:max_oncall_overlap},%s,%s)' % (ck('Over the limit'), ck('Within the limit')), 14)],
    D.daily_d(), 250, [A('limit_flag', '= ' + ck('Over the limit'), 'bad'), A('two_plus', '= 1', 'warn')]))
# ---------------------------------------------------------------- 9 weekly load
tables.append(T('weekly', 'Weekly On-Call Load', 'On-call load for every week ahead',
    'One row per week from 4 weeks ago to 6 months ahead (type the week number, 0 is this week): windows open, due dates and the most windows of one doula; the busy score fills in by itself.', [
    C('week_no', 'Week number', 'int', 9, required=True),
    CA('week', 'Week starting Monday', 'date', WEEK, 12),
    CA('windows_open', 'Windows open', 'int', 'COUNTIFS(%s,"<="&({col:week}+6),%s,">="&{col:week})' % (OS, OE), 9),
    CA('due_dates', 'Due dates in the week', 'int', 'COUNTIFS(%s,">="&{col:week},%s,"<="&({col:week}+6))' % (OEDD, OEDD), 10),
    CA('doulas_open', 'Doulas with a window', 'int', 'SUMPRODUCT(--(%s>0))' % CNT_D('{col:week}', '({col:week}+6)'), 10),
    CA('peak_overlap', 'Most windows of one doula', 'int', 'SUMPRODUCT(MAX(%s))' % CNT_D('{col:week}', '({col:week}+6)'), 10),
    CA('score', 'Busy score', 'num', 'IF({col:week_no}>=0,{col:windows_open}*100+{col:peak_overlap}*10-{col:week_no}/100,0)', 11),
    CA('flag', 'Limit check', 'text', 'IF({col:peak_overlap}>{set:max_oncall_overlap},%s,%s)' % (ck('Over the limit'), ck('Within the limit')), 14),
    ADMIN_PH(), COMP()],
    D.weekly_d(), 100, [A('flag', '= ' + ck('Over the limit'), 'bad'), A('windows_open', '>= 6', 'warn')]))
# ---------------------------------------------------------------- 10 capacity by month
INMO = '%s,">="&{col:month},%s,"<="&EOMONTH({col:month},0)'
tables.append(T('capm', 'Capacity by Month', 'Due dates against the cap for each month',
    'One row per month: due dates booked, the agency cap you set, the free dates and the share used; backup stipends and call-out pay fill in by themselves.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('m_ahead', 'Months ahead', 'int', '(YEAR({col:month})-YEAR({today}))*12+MONTH({col:month})-MONTH({today})', 8),
    CA('due_dates', 'Due dates booked', 'int', 'COUNTIFS(%s)' % (INMO % (OEDD, OEDD)), 9),
    CA('cap', 'Agency cap', 'int', '{set:agency_cap_month}', 8), CA('doula_caps', 'Doula caps added', 'int', 'SUM(%s)' % DCAP, 9),
    CA('free_dates', 'Free dates', 'int', 'MAX(0,{col:cap}-{col:due_dates})', 8), CA('utilisation', 'Cap used', 'pct', 'IF({col:cap}>0,{col:due_dates}/{col:cap},0)', 9),
    CA('status', 'Cap check', 'text', 'IF({col:due_dates}>={col:cap},%s,%s)' % (ck('Full'), ck('Open')), 10),
    CA('windows_opening', 'Windows opening', 'int', 'COUNTIFS(%s)' % (INMO % (OS, OS)), 9),
    CA('stipend', 'Backup stipends', 'int', 'SUMIFS(%s,%s,">="&{col:month},%s,"<="&EOMONTH({col:month},0))' % (R('rota', 'stipend'), R('rota', 'week'), R('rota', 'week')), 10),
    CA('stipend_plan', 'Planned stipends', 'int', '{set:stipend_plan_month}', 10),
    CA('callout_pay', 'Call-out pay', 'int', 'SUMIFS(%s,%s,">="&{col:month},%s,"<="&EOMONTH({col:month},0))' % (R('callouts', 'backup_pay'), R('callouts', 'date'), R('callouts', 'date')), 10),
    CA('accountant_phone', 'Accountant phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH(%s,{range:team.role},0))&"","")' % tok('role', 'Accountant'), 18), OWNER_PH(), COMP()],
    D.capm_d(), 60, [A('status', '= ' + ck('Full'), 'bad'), A('utilisation', '>= 0.85', 'warn')]))
# ---------------------------------------------------------------- 11 capacity by doula and month
DM = '%s,{col:doula},%s,">="&{col:month},%s,"<="&EOMONTH({col:month},0)' % (OD, OEDD, OEDD)
tables.append(T('capd', 'Capacity by Doula and Month', 'Due dates and overlap for each doula and month',
    'One row per doula and month: due dates booked against that doula cap and the most windows of the doula open together; the free dates, the cap check and the limit check fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), LST('doula', 'Doula', 'doula', 16), C('month', 'Month', 'date', 11),
    CA('due_dates', 'Due dates booked', 'int', 'COUNTIFS(%s)' % DM, 9),
    CA('cap', 'Doula cap', 'int', 'IFERROR(INDEX(%s,MATCH({col:doula},%s,0)),0)' % (DCAP, DOUS), 8), CA('free_dates', 'Free dates', 'int', 'MAX(0,{col:cap}-{col:due_dates})', 8),
    CA('peak_overlap', 'Most windows open together', 'int', 'SUMPRODUCT(MAX((%s={col:doula})*(%s>={col:month})*(%s<=EOMONTH({col:month},0))*COUNTIFS(%s,{col:doula},%s,"<="&%s,%s,">="&%s)))' % (OD, OS, OS, OD, OS, OS, OE, OS), 10),
    CA('status', 'Cap check', 'text', 'IF({col:cap}=0,%s,IF({col:due_dates}>{col:cap},%s,IF({col:due_dates}={col:cap},%s,%s)))' % (ck('Not taking births'), ck('Over the cap'), ck('Full'), ck('Open')), 16),
    CA('limit_flag', 'Limit check', 'text', 'IF({col:peak_overlap}>{set:max_oncall_overlap},%s,%s)' % (ck('Over the limit'), ck('Within the limit')), 14),
    PH_TEAM('doula', 'doula_phone', 'Doula phone'), OWNER_PH(), COMP()],
    D.capd_d(), 150, [A('limit_flag', '= ' + ck('Over the limit'), 'bad'), A('status', '= ' + ck('Full'), 'warn'), A('status', '= ' + ck('Over the cap'), 'bad')]))
# ---------------------------------------------------------------- 12 busiest weeks
BW = lambda c: 'INDEX({range:weekly.%s},MATCH({col:top_score},{range:weekly.score},0))' % c
tables.append(T('busy', 'Busiest Weeks', 'The busiest weeks ahead, ranked',
    'One row per rank (1 is the busiest): the week, the clients on call, the doulas needed and the most windows of one doula, ranked by the busy score; everything fills in by itself.', [
    C('rank', 'Rank', 'int', 7, required=True),
    CA('top_score', 'Busy score', 'num', 'LARGE({range:weekly.score},{col:rank})', 11),
    CA('week', 'Week starting Monday', 'date', BW('week'), 12), CA('clients_on_call', 'Clients on call', 'int', BW('windows_open'), 9),
    CA('doulas_needed', 'Doulas needed', 'int', BW('doulas_open'), 9), CA('peak_overlap', 'Most windows of one doula', 'int', BW('peak_overlap'), 10),
    CA('flag', 'Limit check', 'text', 'IF({col:peak_overlap}>{set:max_oncall_overlap},%s,%s)' % (ck('Over the limit'), ck('Within the limit')), 14), OWNER_PH(), COMP()],
    D.busy_d(), 50, [A('flag', '= ' + ck('Over the limit'), 'bad')]))
# ---------------------------------------------------------------- 13 backup cover check
OW_ = lambda c: LKT('oncall.' + c, 'oncall.window_id', 'window_id')
tables.append(T('cover', 'Backup Cover Check', 'Every upcoming window against its backup',
    'One row per window that has not closed (soonest first): the doula, the backup and the backup load in the week the window opens; the cover check shows a missing or overloaded backup.', [
    REF('window_id', 'Window ID', 'oncall.window_id', 10, required=True),
    CA('client', 'Client', 'text', OW_('client'), 22), CA('doula', 'Doula', 'text', OW_('doula'), 16), CA('backup', 'Backup doula', 'text', OW_('backup'), 16),
    CA('oncall_start', 'On-call start', 'date', LKD('oncall.oncall_start', 'oncall.window_id', 'window_id'), 12), CA('oncall_end', 'On-call end', 'date', LKD('oncall.oncall_end', 'oncall.window_id', 'window_id'), 12),
    CA('days_to_open', 'Days to open', 'int', 'IF({col:oncall_start}>0,{col:oncall_start}-{today},"")', 9),
    CA('backup_load', 'Backup load that week', 'int', 'IF({col:backup}="","",COUNTIFS(%s,{col:backup},%s,"<="&({col:oncall_start}+6),%s,">="&{col:oncall_start}))' % (OB, OS, OE), 10),
    CA('cover_flag', 'Cover check', 'text', 'IF({col:backup}="",%s,IF({col:backup_load}>{set:backup_load_max},%s,%s))' % (ck('No backup named'), ck('Backup overloaded'), ck('Backup named')), 17),
    CA('client_phone', 'Client phone', 'text', LKT('oncall.phone', 'oncall.window_id', 'window_id'), 18), CA('doula_phone', 'Doula phone', 'text', LKT('oncall.doula_phone', 'oncall.window_id', 'window_id'), 18),
    CA('backup_phone', 'Backup phone', 'text', LKT('oncall.backup_phone', 'oncall.window_id', 'window_id'), 18), OWNER_PH(), ADMIN_PH(), COMP()],
    D.cover_d(), 120, [A('cover_flag', '= ' + ck('No backup named'), 'bad'), A('cover_flag', '= ' + ck('Backup overloaded'), 'warn'), A('days_to_open', '<= {set:window_alert_days}', 'warn')]))
# ---------------------------------------------------------------- 14 backup load by week
tables.append(T('bload', 'Backup Load by Week', 'Windows each backup covers in each week ahead',
    'One row per backup and week (type the week number, 0 is this week): the windows the backup covers, whether the backup is on the rota that week and the load check fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), LST('backup', 'Backup doula', 'backup', 16), C('week_no', 'Week number', 'int', 9),
    CA('week', 'Week starting Monday', 'date', WEEK, 12),
    CA('windows_covered', 'Windows covered', 'int', 'COUNTIFS(%s,{col:backup},%s,"<="&({col:week}+6),%s,">="&{col:week})' % (OB, OS, OE), 10),
    CA('on_rota', 'On the rota', 'int', 'COUNTIFS(%s,{col:week},%s,{col:backup})' % (R('rota', 'week'), R('rota', 'backup')), 9),
    CA('flag', 'Load check', 'text', 'IF({col:windows_covered}>{set:backup_load_max},%s,%s)' % (ck('Backup overloaded'), ck('Fine')), 16),
    PH_TEAM('backup', 'backup_phone', 'Backup phone'), COMP()],
    D.bload_d(), 60, [A('flag', '= ' + ck('Backup overloaded'), 'bad')]))
# ---------------------------------------------------------------- 15 date requests
RM0 = 'DATE(YEAR({col:edd_wanted}),MONTH({col:edd_wanted}),1)'
RM1 = 'EOMONTH({col:edd_wanted},0)'
FREE_D = lambda lim: 'SUMPRODUCT((%s>0)*(COUNTIFS(%s,%s,%s,"<="&{col:window_end},%s,">="&{col:window_start})%s)*(COUNTIFS(%s,%s,%s,">="&%s,%s,"<="&%s)<%s))' % (DCAP, OD, DOUS, OS, OE, lim, OD, DOUS, OEDD, RM0, OEDD, RM1, DCAP)
tables.append(T('requests', 'Date Requests', 'Due-date requests with a yes or no',
    'One row per recent enquiry for a due date: the window dates, the clients it overlaps, the doulas free and the verdict (yes, yes with backup booked, decline or waitlist) fill in by themselves.', [
    C('enquiry_id', 'Enquiry ID', 'text', 10, required=True), C('date', 'Received on', 'date', 11), C('name', 'Name', 'text', 22), C('phone', 'Phone', 'text', 18), LST('service', 'Service', 'service', 12),
    LST('area', 'Area', 'area', 11), C('edd_wanted', 'Estimated due date wanted', 'date', 12), LST('source', 'Source', 'source', 18), C('answered', 'Answered', 'bool', 9),
    CA('window_start', 'Window start', 'date', 'IF({col:service}=%s,"",{col:edd_wanted}-{set:oncall_before_days})' % PP, 12),
    CA('window_end', 'Window end', 'date', 'IF({col:service}=%s,"",{col:edd_wanted}+{set:oncall_after_days})' % PP, 12),
    CA('overlapping', 'Clients overlapping', 'int', 'IF({col:service}=%s,0,COUNTIFS(%s,"<="&{col:window_end},%s,">="&{col:window_start}))' % (PP, OS, OE), 10),
    CA('month_count', 'Due dates that month', 'int', 'COUNTIFS(%s,">="&%s,%s,"<="&%s)' % (OEDD, RM0, OEDD, RM1), 10),
    CA('free_doulas', 'Doulas free', 'int', 'IF({col:service}=%s,0,%s)' % (PP, FREE_D('<{set:max_oncall_overlap}')), 9),
    CA('clear_doulas', 'Doulas fully clear', 'int', 'IF({col:service}=%s,0,%s)' % (PP, FREE_D('=0')), 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:service}=%s,%s,IF(OR({col:month_count}>={set:agency_cap_month},{col:free_doulas}=0),%s,IF({col:clear_doulas}>0,%s,%s)))' % (
        PP, ck('No window needed'), ck('Decline or waitlist'), ck('Yes'), ck('Yes with backup booked')), 22),
    CA('days_waiting', 'Days since the request', 'int', '{today}-{col:date}', 9), OWNER_PH(), COMP()],
    D.requests_d(), 100, [A('verdict', '= ' + ck('Decline or waitlist'), 'bad'), A('verdict', '= ' + ck('Yes with backup booked'), 'warn'), A('verdict', '= ' + ck('Yes'), 'good')]))
# ---------------------------------------------------------------- 16 overlap scenario
CNTM = 'COUNTIFS(%s,%s,%s,">="&{col:month},%s,"<="&EOMONTH({col:month},0))' % (OD, DOUS, OEDD, OEDD)
tables.append(T('overlap_scn', 'Overlap Scenario', 'What if every client due in a month is attended in 7 days',
    'One row per month: due dates, the doulas that have one and the births that need a backup if all land in the same 7 days; the backups you have, the shortfall and the verdict fill in by themselves.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('due_dates', 'Due dates', 'int', 'COUNTIFS(%s,">="&{col:month},%s,"<="&EOMONTH({col:month},0))' % (OEDD, OEDD), 9),
    CA('doulas_busy', 'Doulas with a due date', 'int', 'SUMPRODUCT(--(%s>0))' % CNTM, 10),
    CA('extra', 'Births needing a backup', 'int', 'SUMPRODUCT((%s>1)*(%s-1))' % (CNTM, CNTM), 10),
    CA('backups', 'Backups available', 'int', 'COUNTIFS({range:team.role},%s)' % tok('role', 'Backup doula'), 10),
    CA('short_by', 'Short by', 'int', 'MAX(0,{col:extra}-{col:backups})', 8),
    CA('verdict', 'Verdict', 'text', 'IF({col:short_by}>0,%s,%s)' % (ck('Short of backups'), ck('Backup is enough')), 16), OWNER_PH(), COMP()],
    D.scn_d(), 50, [A('verdict', '= ' + ck('Short of backups'), 'bad'), A('verdict', '= ' + ck('Backup is enough'), 'good')]))
# ---------------------------------------------------------------- 17 time-off clashes
TC = '(((%s={col:holder})+(%s={col:holder}))>0)*(%s<={col:end})*(%s>={col:start})' % (OD, OB, OS, OE)
FM = lambda c, key_: 'IFERROR(INDEX(%s,MATCH({col:holder}&"|"&{col:first_start},%s,0)),IFERROR(INDEX(%s,MATCH({col:holder}&"|"&{col:first_start},%s,0)),""))' % (c, R('oncall', 'dkey'), c, R('oncall', 'bkey'))
tables.append(T('clash', 'Time-Off Clashes', 'Time off against the on-call windows',
    'One row per time-off block you check: the holder, the dates, the windows it overlaps and the first client affected with their doula and backup; the clash check and phone fill in by themselves.', [
    REF('timeoff_id', 'Time-off ID', 'timeoff.timeoff_id', 10, required=True),
    CA('holder', 'Holder', 'text', LKT('timeoff.holder', 'timeoff.timeoff_id', 'timeoff_id'), 16),
    CA('start', 'Start', 'date', LKD('timeoff.start', 'timeoff.timeoff_id', 'timeoff_id'), 11), CA('end', 'End', 'date', LKD('timeoff.end', 'timeoff.timeoff_id', 'timeoff_id'), 11),
    CA('windows_overlapped', 'Windows overlapped', 'int', LKN('timeoff.clashes', 'timeoff.timeoff_id', 'timeoff_id'), 10),
    CA('first_start', 'First window opens', 'date', 'IF({col:windows_overlapped}=0,"",SUMPRODUCT(MIN(%s*%s+(1-%s)*99999999)))' % (TC, OS, TC), 12),
    CA('first_client', 'First client affected', 'text', 'IF({col:windows_overlapped}=0,"",%s)' % FM(OCL, 'client'), 22),
    CA('first_doula', 'Their doula', 'text', 'IF({col:windows_overlapped}=0,"",%s)' % FM(OD, 'doula'), 16),
    CA('first_backup', 'Their backup', 'text', 'IF({col:windows_overlapped}=0,"",%s&"")' % FM(OB, 'backup'), 16),
    CA('days_to_start', 'Days to start', 'int', 'IF({col:start}>0,{col:start}-{today},"")', 9),
    CA('flag', 'Clash check', 'text', 'IF({col:end}<{today},%s,IF({col:windows_overlapped}>0,%s,%s))' % (ck('Past block'), ck('Clash'), ck('Safe to book')), 14),
    CA('client_phone', 'Client phone', 'text', 'IFERROR(INDEX(%s,MATCH({col:first_client},%s,0))&"","")' % (R('oncall', 'phone'), OCL), 18), OWNER_PH(), COMP()],
    D.clash_d(), 60, [A('flag', '= ' + ck('Clash'), 'bad'), A('flag', '= ' + ck('Safe to book'), 'good')]))
# ---------------------------------------------------------------- 18 backup pay rules
tables.append(T('rules', 'Backup Pay Rules', 'Rules for paying a backup doula',
    'One row per pay rule: the rule, what it is paid on and the amount (a share is a fraction); the pay tools use these numbers, so keep them in step with your contract.', [
    C('rule', 'Rule', 'text', 24, required=True), LST('basis', 'Paid on', 'rbasis', 26), C('amount', 'Amount or share', 'num', 12)],
    D.rules_d(), 50))
# ---------------------------------------------------------------- 19 backup call-outs
BR = lambda c: LKT('births.' + c, 'births.birth_id', 'birth_id')
tables.append(T('callouts', 'Backup Call-Outs', 'Births with the backup pay and the doula pay after it',
    'One row per birth you review: the backup who attended, the birth part of the package and the agency share you type; call-out pay, agency cut and doula pay fill in by themselves.', [
    REF('birth_id', 'Birth ID', 'births.birth_id', 10, required=True),
    CA('date', 'Date', 'date', LKD('births.date', 'births.birth_id', 'birth_id'), 11), CA('client', 'Client', 'text', BR('client'), 22), CA('assigned', 'Assigned doula', 'text', BR('assigned'), 16), CA('backup', 'Backup who attended', 'text', BR('backup'), 16),
    C('birth_value', 'Birth part of the package', 'money', 13), C('agency_share', 'Agency share', 'pct', 9),
    CA('outcome', 'Outcome', 'text', 'IF({col:backup}="",%s,%s)' % (ck('Assigned doula attended'), ck('Backup attended')), 22),
    CA('backup_pay', 'Call-out pay', 'money', 'IF({col:backup}="",0,{set:backup_flat_pay})', 11),
    CA('agency_cut', 'Agency cut', 'money', '{col:birth_value}*{col:agency_share}', 11), CA('doula_pay', 'Doula pay after the split', 'money', '{col:birth_value}-{col:agency_cut}-{col:backup_pay}', 12),
    PH_TEAM('backup', 'backup_phone', 'Backup phone'), OWNER_PH(), COMP()],
    D.callouts_d(), 60, [A('outcome', '= ' + ck('Backup attended'), 'warn'), A('doula_pay', '< 0', 'bad')]))
# ---------------------------------------------------------------- 20 backup named share
tables.append(T('named', 'Backup Named Share', 'Share of windows with a named backup by month',
    'One row per month: windows opening, the windows with a backup named and the share named; the check says when a backup is still to be named.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('windows', 'Windows opening', 'int', 'COUNTIFS(%s,">="&{col:month},%s,"<="&EOMONTH({col:month},0))' % (OS, OS), 9),
    CA('named', 'Backup named', 'int', 'COUNTIFS(%s,">="&{col:month},%s,"<="&EOMONTH({col:month},0),%s,"<>")' % (OS, OS, OB), 9),
    CA('share', 'Share named', 'pct', 'IF({col:windows}>0,{col:named}/{col:windows},"")', 9),
    CA('status', 'Check', 'text', 'IF({col:windows}=0,%s,IF({col:named}<{col:windows},%s,%s))' % (ck('Not needed'), ck('Name a backup'), ck('Backup named')), 16), OWNER_PH(), COMP()],
    D.named_d(), 50, [A('status', '= ' + ck('Name a backup'), 'bad'), A('share', '< 1', 'warn')]))
assert len(tables) == 20, len(tables)
