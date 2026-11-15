"""Home care suite part 2: settings and the 20 tables."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hc2_lists import *
import hc2_data as D

def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKV(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),"")' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def STAFF_PH(idx, k): return CA(k, 'Phone to message', 'text', 'IFERROR(INDEX({range:team.phone},%d)&"","")' % idx, 18)
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
NXT_MON = '({today}-WEEKDAY({today},2)+8)'
def ST(lst, lab): return tok(lst, lab)

settings = [
    S('company', 'Your agency name', 'text', COMPANY), S('overtime_hours', 'Weekly hours above which overtime is paid', 'int', 40), S('overtime_mult', 'Overtime pay multiplier', 'num', 1.5),
    S('payroll_burden', 'Payroll burden on pay (example, confirm with your adviser)', 'pct', 0.2), S('cover_premium', 'Cover premium per hour for short-notice cover', 'money', 3),
    S('short_notice_hours', 'Cover found with less notice than this (hours) earns the premium', 'int', 24), S('continuity_limit', 'Most different caregivers a client should see in 4 weeks', 'int', 3),
    S('post_schedule_days', 'Days ahead the schedule is posted', 'int', 14), S('fill_rate_target', 'Wanted fill rate (share of scheduled hours covered)', 'pct', 0.97),
    S('sched_threshold_hours', 'Weekly care hours at which a dedicated scheduler pays off (a marker)', 'int', 1000), S('min_rest_hours', 'Least rest between the last visit and the next start (hours)', 'int', 10),
    S('max_days_in_row', 'Most days a caregiver works in a row', 'int', 6), S('urgent_days', 'An open shift this many days ahead or fewer is urgent', 'int', 2),
    S('calloff_talk_factor', 'A call-off rate above this multiple of the agency rate means a talk', 'num', 1.5), S('cover_minutes_target', 'Wanted minutes to find cover', 'int', 90),
    S('day_shift_hours', 'Hours one extra caregiver covers in a day', 'int', 8)]
assert 3 <= len(settings) <= 20

tables = []
# 1 schedule
tables.append(T('schedule', 'Schedule', 'Weekly schedule (rota or roster): every visit, planned caregiver and cover',
    'One row per visit from 30 days back to 14 days ahead: planned caregiver, who goes, cover type and status; the end time, week, days ahead and phones fill in by themselves. A one-person agency can use only this page.', [
    C('visit_id', 'Visit ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('start', 'Start', 'time', 8), C('sched_hours', 'Hours', 'num', 8), REF('client', 'Client', 'clients.client', 24),
    LST('area', 'Area', 'area', 12), LST('service', 'Service', 'svc', 18), LST('band', 'Time band', 'band', 10), REF('planned', 'Planned caregiver', 'caregivers.name', 22), REF('caregiver', 'Caregiver', 'caregivers.name', 22),
    LST('cover_type', 'Cover type', 'cover', 11), LST('status', 'Status', 'vstatus', 12),
    CA('end_time', 'End', 'time', 'MOD({col:start}+{col:sched_hours}/24,1)', 8), CA('week', 'Week (Monday)', 'date', '{col:date}-WEEKDAY({col:date},2)+1', 12), CA('days_ahead', 'Days ahead', 'int', '{col:date}-{today}', 9),
    CA('holiday', 'Holiday', 'text', 'IFERROR(INDEX({range:holidays.holiday},MATCH({col:date},{range:holidays.date},0))&"","")', 20),
    CA('client_phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client', 'client'), 18), CA('caregiver_phone', 'Caregiver phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'caregiver'), 18),
    STAFF_PH(5, 'supervisor_phone')], D.schedule_d(), 2500,
    [A('status', '= ' + ST('vstatus', 'Open'), 'bad'), A('status', '= ' + ST('vstatus', 'Missed'), 'bad'), A('status', '= ' + ST('vstatus', 'Late'), 'warn'), A('cover_type', '= ' + ST('cover', 'Cover'), 'warn'), A('cover_type', '= ' + ST('cover', 'Uncovered'), 'bad')]))
# 2 weekly grid by caregiver
tables.append(T('grid_cg', 'Weekly Grid by Caregiver', 'Weekly grid by caregiver: hours against the overtime line, days off and the limit',
    'One row per caregiver and week: scheduled hours, days worked and the longest run of days; free hours, the overtime-line flag and the days-off flag fill in by themselves (overtime means hours above the weekly line).', [
    C('row_id', 'Row ID', 'text', 10, required=True), C('week', 'Week (Monday)', 'date', 12), C('caregiver_id', 'Caregiver ID', 'text', 11), REF('caregiver', 'Caregiver', 'caregivers.name', 22), LST('employment', 'Employment type', 'emp', 12),
    LST('area', 'Area', 'area', 12), C('hours_limit', 'Weekly limit, hours', 'int', 10), C('scheduled_hours', 'Scheduled hours', 'num', 10), C('days_worked', 'Days worked', 'int', 9), C('longest_run', 'Longest run, days', 'int', 9),
    CA('free_hours', 'Free hours', 'num', '{col:hours_limit}-{col:scheduled_hours}', 9), CA('over_hours', 'Hours over the line', 'num', 'MAX(0,{col:scheduled_hours}-{set:overtime_hours})', 10),
    CA('load_flag', 'Hours check', 'text', 'IF({col:scheduled_hours}>{set:overtime_hours},%s,IF({col:scheduled_hours}>{col:hours_limit},%s,%s))' % (ck('Over the line'), ck('Over own limit'), ck('Within limit')), 14),
    CA('days_flag', 'Days-off check', 'text', 'IF({col:days_worked}>=7,%s,IF({col:longest_run}>={set:max_days_in_row},%s,%s))' % (ck('No day off'), ck('Long run'), ck('Day off kept')), 14),
    CA('visits_week', 'Visits in the schedule', 'int', 'COUNTIFS({range:schedule.caregiver},{col:caregiver},{range:schedule.week},{col:week},{range:schedule.status},"<>"&%s)' % ST('vstatus', 'Cancelled'), 10),
    CA('phone', 'Caregiver phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'caregiver'), 18), STAFF_PH(2, 'scheduler_phone')], D.grid_cg_d(), 600,
    [A('load_flag', '= ' + ck('Over the line'), 'bad'), A('load_flag', '= ' + ck('Over own limit'), 'warn'), A('days_flag', '= ' + ck('No day off'), 'bad'), A('days_flag', '= ' + ck('Long run'), 'warn')]))
# 3 weekly grid by client
tables.append(T('grid_cl', 'Weekly Grid by Client', 'Weekly grid by client: hours, different caregivers and the main caregiver share',
    'One row per client and week: scheduled hours, different caregivers and hours by the main caregiver; the main share and the continuity flag fill in by themselves (continuity means how few different caregivers a client sees).', [
    C('row_id', 'Row ID', 'text', 10, required=True), C('week', 'Week (Monday)', 'date', 12), REF('client', 'Client', 'clients.client', 24), C('scheduled_hours', 'Scheduled hours', 'num', 10), C('caregivers_seen', 'Different caregivers', 'int', 10),
    C('main_hours', 'Hours by main caregiver', 'num', 11), CA('main_share', 'Main caregiver share', 'pct', 'IF({col:scheduled_hours}>0,{col:main_hours}/{col:scheduled_hours},0)', 11),
    CA('cont_flag', 'Continuity check', 'text', 'IF({col:caregivers_seen}<={set:continuity_limit},%s,IF({col:caregivers_seen}<={set:continuity_limit}+2,%s,%s))' % (ck('Steady'), ck('Watch'), ck('Break')), 14),
    CA('client_phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client', 'client'), 18)], D.grid_cl_d(), 800,
    [A('cont_flag', '= ' + ck('Break'), 'bad'), A('cont_flag', '= ' + ck('Watch'), 'warn')]))
# 4 open shifts
OPENC = '"<>"&' + ck('Closed')
tables.append(T('open_shifts', 'Open Shifts', 'Open shifts board: visits without a caregiver, urgency and how early they were filled',
    'One row per open shift (a visit without a caregiver): date, client, service, language wanted and status; days ahead, urgency and days filled ahead fill in by themselves. A one-person agency can use this page alone.', [
    C('visit_id', 'Visit ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('start', 'Start', 'time', 8), C('hours', 'Hours', 'num', 8), REF('client', 'Client', 'clients.client', 24), LST('area', 'Area', 'area', 12),
    LST('service', 'Service', 'svc', 18), LST('language', 'Language wanted', 'lang', 12), LST('status', 'Status', 'ostatus', 11), C('filled_on', 'Filled on', 'date', 11), REF('caregiver', 'Filled by', 'caregivers.name', 22),
    CA('days_ahead', 'Days ahead', 'int', '{col:date}-{today}', 9),
    CA('urgency', 'Urgency', 'text', 'IF(OR({col:status}=%s,{col:status}=%s),%s,IF({col:date}-{today}<={set:urgent_days},%s,IF({col:date}-{today}<=7,%s,%s)))' % (ST('ostatus', 'Filled'), ST('ostatus', 'Not filled'), ck('Closed'), ck('Urgent'), ck('Soon'), ck('Later')), 11),
    CA('filled_ahead', 'Days filled ahead', 'int', 'IF({col:filled_on}="","",{col:date}-{col:filled_on})', 10),
    CA('open_count', 'Open shifts tomorrow', 'int', 'COUNTIFS({range:open_shifts.date},{today}+1,{range:open_shifts.urgency},%s)' % OPENC, 10), STAFF_PH(2, 'scheduler_phone')], D.open_d(), 200,
    [A('urgency', '= ' + ck('Urgent'), 'bad'), A('urgency', '= ' + ck('Soon'), 'warn'), A('status', '= ' + ST('ostatus', 'Not filled'), 'bad'), A('status', '= ' + ST('ostatus', 'Filled'), 'good')]))
# 5 caregivers
SKILLS = 'IF({col:skill_1}="","",{col:skill_1}&IF({col:skill_2}="","","; "&{col:skill_2})&IF({col:skill_3}="","","; "&{col:skill_3})&IF({col:skill_4}="","","; "&{col:skill_4})&IF({col:skill_5}="","","; "&{col:skill_5}))'
NXTH = 'SUMPRODUCT(MIN(({range:holidays.date}>={today})*{range:holidays.date}+({range:holidays.date}<{today})*99999))'
tables.append(T('caregivers', 'Caregivers', 'Caregivers (carer, care worker or support worker): skills, languages, area, limit and standby',
    'One row per caregiver: employment, pay rate, area, availability, weekly limit, skills and languages; the skills text, languages text and the next holiday fill in by themselves. Skills and languages drive the matching tools.', [
    C('caregiver_id', 'Caregiver ID', 'text', 11, required=True), C('seq', 'No', 'int', 6), C('name', 'Name', 'text', 24), C('hire_date', 'Hire date', 'date', 11), LST('employment', 'Employment type', 'emp', 12), C('pay_rate', 'Pay rate per hour', 'money', 11),
    LST('area', 'Area', 'area', 12), LST('availability', 'Availability', 'avail', 22), C('hours_limit', 'Weekly limit, hours', 'int', 10), LST('status', 'Status', 'cgstatus', 10), C('left_date', 'Left date', 'date', 11),
    LST('leave_reason', 'Leave reason', 'leave', 20), LST('source', 'Recruiting source', 'recsrc', 18), C('phone', 'Phone', 'text', 18), C('email', 'Email', 'text', 26), C('standby', 'On the standby pool', 'bool', 10),
    LST('skill_1', 'Skill 1', 'svc', 18), LST('skill_2', 'Skill 2', 'svc', 18), LST('skill_3', 'Skill 3', 'svc', 18), LST('skill_4', 'Skill 4', 'svc', 18), LST('skill_5', 'Skill 5', 'svc', 18),
    LST('language_1', 'Language 1', 'lang', 12), LST('language_2', 'Language 2', 'lang', 12),
    CA('skills', 'Skills', 'text', SKILLS, 30), CA('languages', 'Languages', 'text', 'IF({col:language_1}="","",{col:language_1}&IF({col:language_2}="","","; "&{col:language_2}))', 20),
    CA('next_holiday_date', 'Next holiday', 'date', 'IF(%s>=99999,"",%s)' % (NXTH, NXTH), 11),
    CA('next_holiday', 'Next holiday name', 'text', 'IFERROR(INDEX({range:holidays.holiday},MATCH({col:next_holiday_date},{range:holidays.date},0))&"","")', 20),
    CA('week_start', 'This week (Monday)', 'date', '{today}-WEEKDAY({today},2)+1', 12), STAFF_PH(16, 'answering_phone')], D.caregivers_d(), 100,
    [A('status', '= ' + ST('cgstatus', 'Left'), 'warn'), A('standby', '= ' + YES, 'good')]))
# 6 availability
tables.append(T('availability', 'Availability', 'Availability by caregiver, weekday and time window',
    'One row per caregiver and weekday: the time window and the most hours the caregiver wants; the window length fills in by itself.', [
    C('avail_id', 'Availability ID', 'text', 11, required=True), REF('caregiver', 'Caregiver', 'caregivers.name', 22), LST('weekday', 'Weekday', 'wday', 11), C('from_time', 'From', 'time', 8), C('to_time', 'To', 'time', 8), C('max_hours', 'Most hours', 'int', 9),
    CA('window_hours', 'Window hours', 'num', 'ROUND(({col:to_time}-{col:from_time})*24,1)', 9), CA('caregiver_phone', 'Caregiver phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'caregiver'), 18)], D.availability_d(), 400))
# 7 time off
tables.append(T('time_off', 'Time Off', 'Time off: holiday, sick days and training days by caregiver',
    'One row per time-off request: kind, dates, days and whether it is approved; the caregiver phone and the visits already scheduled in those days fill in by themselves.', [
    C('timeoff_id', 'Time off ID', 'text', 10, required=True), REF('caregiver', 'Caregiver', 'caregivers.name', 22), LST('kind', 'Kind', 'timeoff', 13), C('start_date', 'Start', 'date', 11), C('end_date', 'End', 'date', 11), C('days', 'Days', 'int', 7),
    C('approved', 'Approved', 'bool', 9),
    CA('visits_in_period', 'Visits scheduled in the period', 'int', 'COUNTIFS({range:schedule.caregiver},{col:caregiver},{range:schedule.date},">="&{col:start_date},{range:schedule.date},"<="&{col:end_date},{range:schedule.status},"<>"&%s)' % ST('vstatus', 'Cancelled'), 12),
    CA('caregiver_phone', 'Caregiver phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'caregiver'), 18)], D.time_off_d(), 400,
    [A('approved', '= ' + NO, 'warn'), A('visits_in_period', '> 0', 'warn')]))
# 8 clients
tables.append(T('clients', 'Clients', 'Clients: area, service, weekly hours, language and preferred caregivers',
    'One row per client: area, main service, agreed weekly hours, language and up to two preferred caregivers; the matching tools read them.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 24), C('phone', 'Phone', 'text', 18), LST('area', 'Area', 'area', 12), LST('service', 'Service', 'svc', 18), C('weekly_hours', 'Weekly hours', 'num', 9),
    LST('language', 'Language', 'clang', 12), REF('preferred', 'Preferred caregiver', 'caregivers.name', 22), REF('preferred_2', 'Second preferred caregiver', 'caregivers.name', 22), LST('status', 'Status', 'clstatus', 9), C('start_date', 'Start date', 'date', 11)],
    D.clients_d(), 150, [A('status', '= ' + ST('clstatus', 'Ended'), 'warn')]))
# 9 match weights
tables.append(T('match_weights', 'Match Weights', 'Match weights: how much each factor counts in the matching score',
    'Six weights you set (they are shared by the Match Scores page and the matching tools); the score is the weighted share of the points, out of 100.', [
    C('factor', 'Factor', 'text', 24, required=True), C('weight', 'Weight', 'int', 9), C('note', 'What it measures', 'text', 44)], D.weights_d(), 50))
# 10 match scores
W = lambda i: 'INDEX({range:match_weights.weight},%d)' % i
BK = '{col:hours_booked}'
tables.append(T('match_scores', 'Match Scores', 'Match scores: candidates for each open shift, ranked with the cost of each option',
    'One row per open shift and candidate: points for skills, area, language, availability, preference and hours booked (0 to 100 each); the weighted score, the rank and the cost of the option fill in by themselves.', [
    C('score_id', 'Score ID', 'text', 10, required=True), C('open_shift', 'Open shift (visit ID)', 'text', 11), REF('caregiver', 'Candidate', 'caregivers.name', 22), C('skills_fit', 'Skills points', 'int', 9), C('area_score', 'Area points', 'int', 9),
    C('language_fit', 'Language points', 'int', 9), C('availability_fit', 'Availability points', 'int', 10), C('preferred', 'Preferred by the client', 'bool', 10), C('hours_booked', 'Hours booked that week', 'num', 10),
    CA('shift_date', 'Shift date', 'date', LKD('open_shifts.date', 'open_shifts.visit_id', 'open_shift'), 11), CA('shift_start', 'Shift start', 'time', LKV('open_shifts.start', 'open_shifts.visit_id', 'open_shift'), 8),
    CA('shift_hours', 'Shift hours', 'num', LKN('open_shifts.hours', 'open_shifts.visit_id', 'open_shift'), 8), CA('client', 'Client', 'text', LKT('open_shifts.client', 'open_shifts.visit_id', 'open_shift'), 24),
    CA('service', 'Service', 'text', LKT('open_shifts.service', 'open_shifts.visit_id', 'open_shift'), 18),
    CA('pay', 'Pay rate', 'money', LKN('caregivers.pay_rate', 'caregivers.name', 'caregiver'), 9), CA('limit', 'Weekly limit', 'int', LKN('caregivers.hours_limit', 'caregivers.name', 'caregiver'), 9),
    CA('hours_fit', 'Hours points', 'int', 'IF({col:limit}>0,MAX(0,ROUND(100*(1-%s/{col:limit}),0)),0)' % BK, 9),
    CA('total_score', 'Match score', 'int', 'ROUND((%s*{col:skills_fit}+%s*{col:area_score}+%s*{col:language_fit}+%s*{col:availability_fit}+%s*100*IF({col:preferred}=%s,1,0)+%s*{col:hours_fit})/SUM({range:match_weights.weight}),0)' % (W(1), W(2), W(3), W(4), W(5), YES, W(6)), 9),
    CA('rank_in_shift', 'Rank for the shift', 'int', '1+COUNTIFS({range:match_scores.open_shift},{col:open_shift},{range:match_scores.total_score},">"&{col:total_score})', 9),
    CA('rank_key', 'Rank key', 'text', '{col:open_shift}&"|"&{col:rank_in_shift}', 14),
    CA('option_cost', 'Cost of this option', 'money', 'ROUND({col:shift_hours}*{col:pay}*(1+{set:payroll_burden})+MAX(0,MIN({col:shift_hours},%s+{col:shift_hours}-{set:overtime_hours}))*{col:pay}*({set:overtime_mult}-1)*(1+{set:payroll_burden})+IF({col:shift_date}-{today}<={set:urgent_days},{col:shift_hours}*{set:cover_premium},0),2)' % BK, 11),
    CA('phone', 'Caregiver phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'caregiver'), 18)], D.scores_d(), 600,
    [A('rank_in_shift', '= 1', 'good'), A('total_score', '< 50', 'warn')]))
# 11 continuity by client
tables.append(T('continuity', 'Continuity by Client', 'Continuity by client: different caregivers seen in the last 28 days',
    'One row per active client: different caregivers in the last 28 days, the main caregiver and hours; the main share and the continuity flag fill in by themselves (continuity means how few different caregivers a client sees).', [
    C('client_id', 'Client ID', 'text', 10, required=True), REF('client', 'Client', 'clients.client', 24), C('caregivers_28d', 'Caregivers in 28 days', 'int', 10), REF('main_caregiver', 'Main caregiver', 'caregivers.name', 22),
    C('main_hours', 'Hours by main caregiver', 'num', 11), C('hours', 'Hours', 'num', 8),
    CA('main_share', 'Main caregiver share', 'pct', 'IF({col:hours}>0,{col:main_hours}/{col:hours},0)', 11), CA('over_by', 'Over the limit by', 'int', 'MAX(0,{col:caregivers_28d}-{set:continuity_limit})', 9),
    CA('cont_flag', 'Continuity check', 'text', 'IF({col:caregivers_28d}<={set:continuity_limit},%s,IF({col:caregivers_28d}<={set:continuity_limit}+2,%s,%s))' % (ck('Steady'), ck('Watch'), ck('Break')), 14),
    CA('client_phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client', 'client'), 18), CA('next_monday', 'Next Monday', 'date', NXT_MON, 11),
    STAFF_PH(2, 'scheduler_phone'), STAFF_PH(5, 'supervisor_phone')], D.continuity_d(), 100,
    [A('cont_flag', '= ' + ck('Break'), 'bad'), A('cont_flag', '= ' + ck('Watch'), 'warn')]))
# 12 call-offs and cover
tables.append(T('calloffs', 'Call-offs and Cover', 'Call-offs (a caregiver cannot come) and the cover that found the visit a caregiver',
    'One row per call-off: reason, notice, who covered, minutes to find cover and the premium paid; the premium per hour and phones fill in by themselves. Cover means another caregiver takes the visit.', [
    C('calloff_id', 'Call-off ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('visit_id', 'Visit ID', 'text', 10), REF('client', 'Client', 'clients.client', 24), LST('area', 'Area', 'area', 12), LST('weekday', 'Weekday', 'wday', 11),
    REF('caregiver', 'Caregiver', 'caregivers.name', 22), LST('reason', 'Reason', 'calloff', 15), C('notice_hours', 'Notice, hours', 'int', 9), C('hours', 'Visit hours', 'num', 8), REF('cover_caregiver', 'Cover caregiver', 'caregivers.name', 22),
    C('minutes_to_cover', 'Minutes to cover', 'int', 9), C('premium', 'Premium paid', 'money', 10), C('covered', 'Covered', 'bool', 9),
    CA('premium_per_hour', 'Premium per hour', 'money', 'IF({col:hours}>0,ROUND({col:premium}/{col:hours},2),"")', 10), CA('cover_phone', 'Cover caregiver phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'cover_caregiver'), 18),
    STAFF_PH(2, 'scheduler_phone'), STAFF_PH(1, 'owner_phone')], D.calloffs_d(), 1500,
    [A('covered', '= ' + NO, 'bad'), A('minutes_to_cover', '> {set:cover_minutes_target}', 'warn')]))
# 13 cover cost by month
AVGPAY = 'AVERAGEIFS({range:caregivers.pay_rate},{range:caregivers.status},%s)' % ST('cgstatus', 'Active')
tables.append(T('cover_month', 'Cover Cost by Month', 'Cover cost by month: call-offs, premium paid and overtime from cover',
    'One row per month: call-offs, covered and uncovered, the premium paid and the overtime hours that cover caused; the cost per call-off fills in by itself (premium plus the overtime extra at the average pay rate, with payroll burden).', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('call_offs', 'Call-offs', 'int', 9), C('covered', 'Covered', 'int', 9), C('uncovered', 'Uncovered', 'int', 9), C('premium_paid', 'Premium paid', 'money', 11),
    C('overtime_hours', 'Overtime hours from cover', 'num', 11),
    CA('cost_per_calloff', 'Cost per call-off', 'money', 'IF({col:call_offs}>0,ROUND(({col:premium_paid}+{col:overtime_hours}*%s*({set:overtime_mult}-1)*(1+{set:payroll_burden}))/{col:call_offs},2),0)' % AVGPAY, 11),
    CA('covered_share', 'Covered share', 'pct', 'IF({col:call_offs}>0,{col:covered}/{col:call_offs},0)', 10), STAFF_PH(1, 'owner_phone')], D.cover_month_d(), 60))
# 14 fill rate by week
tables.append(T('fill_week', 'Fill Rate by Week', 'Fill rate by week: scheduled, planned, cover and uncovered hours',
    'One row per week: scheduled hours split into planned, cover and uncovered, and the overtime hours; the fill rate (planned plus cover hours as a share of scheduled) and the check against your target fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('week', 'Week (Monday)', 'date', 12), C('visits', 'Visits', 'int', 8), C('scheduled_hours', 'Scheduled hours', 'num', 10), C('planned_hours', 'Planned hours', 'num', 10),
    C('cover_hours', 'Cover hours', 'num', 9), C('uncovered_hours', 'Uncovered hours', 'num', 10), C('overtime_hours', 'Overtime hours', 'num', 9),
    CA('filled_hours', 'Filled hours', 'num', '{col:planned_hours}+{col:cover_hours}', 9), CA('fill_rate', 'Fill rate', 'pct', 'IF({col:scheduled_hours}>0,({col:planned_hours}+{col:cover_hours})/{col:scheduled_hours},0)', 9),
    CA('fill_flag', 'Target check', 'text', 'IF({col:fill_rate}>={set:fill_rate_target},%s,%s)' % (ck('On target'), ck('Below target')), 12),
    CA('cover_premium_amount', 'Cover premium', 'money', 'ROUND({col:cover_hours}*{set:cover_premium},2)', 10), STAFF_PH(1, 'owner_phone'), STAFF_PH(2, 'scheduler_phone'), STAFF_PH(3, 'office_phone')], D.fill_week_d(), 200,
    [A('fill_flag', '= ' + ck('Below target'), 'warn')]))
# 15 rest check
tables.append(T('rest_check', 'Rest Check', 'Rest check: last visit end against the next day start',
    'One row per caregiver and day followed by a working day: first start, last end, longest gap and the next day start; the rest hours and the short-rest flag fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), REF('caregiver', 'Caregiver', 'caregivers.name', 22), C('date', 'Date', 'date', 11), C('first_start', 'First start', 'time', 9), C('last_end', 'Last end', 'time', 9),
    C('longest_gap_min', 'Longest gap, minutes', 'int', 10), C('next_day_start', 'Next day start', 'time', 9),
    CA('rest_hours', 'Rest hours', 'num', 'ROUND(MOD({col:next_day_start}-{col:last_end},1)*24,1)', 9), CA('rest_flag', 'Rest check', 'text', 'IF(ROUND(MOD({col:next_day_start}-{col:last_end},1)*24,1)<{set:min_rest_hours},%s,%s)' % (ck('Short rest'), ck('Rest kept')), 11),
    CA('caregiver_phone', 'Caregiver phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'caregiver'), 18)], D.rest_d(), 800, [A('rest_flag', '= ' + ck('Short rest'), 'bad')]))
# 16 holidays
tables.append(T('holidays', 'Holidays', 'Holidays (bank holiday or public holiday) with the pay and bill multiplier',
    'One row per holiday: the weekday and the pay and bill multipliers; days ahead, visits and hours in the schedule, open hours and extra caregivers needed fill in by themselves.', [
    C('date', 'Date', 'date', 11, required=True), C('holiday', 'Holiday', 'text', 22), LST('weekday', 'Weekday', 'wday', 11), C('pay_mult', 'Pay multiplier', 'num', 9), C('bill_mult', 'Bill multiplier', 'num', 9),
    CA('days_ahead', 'Days ahead', 'int', '{col:date}-{today}', 9), CA('visits_on', 'Visits that day', 'int', 'COUNTIFS({range:schedule.date},{col:date},{range:schedule.status},"<>"&%s)' % ST('vstatus', 'Cancelled'), 9),
    CA('hours_on', 'Hours that day', 'num', 'SUMIFS({range:schedule.sched_hours},{range:schedule.date},{col:date},{range:schedule.status},"<>"&%s)' % ST('vstatus', 'Cancelled'), 9),
    CA('open_hours', 'Open shift hours', 'num', 'SUMIFS({range:open_shifts.hours},{range:open_shifts.date},{col:date},{range:open_shifts.urgency},%s)' % OPENC, 9),
    CA('extra_caregivers', 'Extra caregivers needed', 'int', 'ROUNDUP({col:open_hours}/{set:day_shift_hours},0)', 10), STAFF_PH(1, 'owner_phone')], D.holidays_d(), 60,
    [A('days_ahead', '>= 0', 'warn')]))
# 17-20 reference
tables.append(T('areas', 'Areas', 'Areas with the average travel minutes to the other areas', 'Six service areas: the zone and the average travel minutes; the tools use the Travel Times page for exact pairs.', [
    LST('area', 'Area', 'area', 14, required=True), C('zone', 'Zone', 'text', 9), C('avg_travel_min', 'Average travel, minutes', 'int', 11)], D.areas_d(), 50))
tables.append(T('travel', 'Travel Times', 'Travel minutes and km between areas', 'One row per pair of areas: minutes and km; the cover cost and match tools read the minutes.', [
    LST('from_area', 'From area', 'area', 13, required=True), LST('to_area', 'To area', 'area', 13), C('minutes', 'Minutes', 'int', 9), C('km', 'Km', 'num', 8)], D.travel_d(), 60))
tables.append(T('services', 'Services', 'Services with the minimum visit and the weekday rate', 'Six services: the minimum visit length and the weekday base rate per hour (read only here, owned by the rate card).', [
    LST('service', 'Service', 'svc', 18, required=True), C('min_visit_hours', 'Minimum visit, hours', 'int', 11), C('bill_rate', 'Weekday rate per hour', 'money', 12)], D.services_d(), 50))
tables.append(T('team', 'Team', 'Team and outside contacts', 'Sixteen people: the owner-director, the care coordinator (scheduler), the office manager, the recruiter, two field supervisors and ten outside contacts; messages read their phones.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 22), C('role', 'Role', 'text', 18), C('team', 'Team', 'text', 10), C('pay_type', 'Pay type', 'text', 11), C('phone', 'Phone', 'text', 18), C('email', 'Email', 'text', 26),
    C('hours_week', 'Hours a week', 'int', 9), C('monthly_salary', 'Monthly salary', 'num', 11), C('hourly_rate', 'Hourly rate', 'num', 10), C('speciality', 'Speciality', 'text', 30), C('country', 'Country', 'text', 12), C('start', 'Start', 'date', 11),
    CA('scheduler_phone', 'Scheduler phone', 'text', 'IFERROR(INDEX({range:team.phone},2)&"","")', 18)], D.team_d(), 50))
assert len(tables) == 20
