"""HVAC suite part 6: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv6_lists import *
import hv6_data as D

YES, NO = '{list:yesno.yes}', '{list:yesno.no}'
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def ph(v): return '"%s"' % v
def CONST(k, label, v): return CA(k, label, 'text', ph(v), 18)
def TECHPH(col='assigned'): return CA('tech_phone', 'Technician phone', 'text', 'IFERROR(CHOOSE(MATCH({col:%s},{range:techs.technician},0),%s),"")' % (col, ','.join(ph(p) for p in D.TECH_PHONES[:6])), 18)
COMPANY_COL = lambda: CA('company', 'Company', 'text', '{set:company}', 24)
ACT, RD, LAP, CAN = (tok('agrstatus', s) for s in ('Active', 'Renewal due', 'Lapsed', 'Cancelled'))
DONE, DUE, BOOKED, MISSED = (tok('visitstatus', s) for s in ('Done', 'Due', 'Booked', 'Missed'))
RENEWED, RLAPSED, ROPEN = (tok('renewout', s) for s in ('Renewed', 'Lapsed', 'Open'))
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
# the open tune-up window: the window that holds today, or the one that ended last; and the same window a year earlier
WS = 'IF({today}>=DATE(YEAR({today}),8,15),DATE(YEAR({today}),8,15),IF({today}>=DATE(YEAR({today}),2,15),DATE(YEAR({today}),2,15),DATE(YEAR({today})-1,8,15)))'
WSL = 'DATE(YEAR(%s)-1,MONTH(%s),15)' % (WS, WS)
def WIN_DONE(): return 'IFERROR(COUNTIFS({range:visits.window_start},%s,{range:visits.status},%s)/COUNTIFS({range:visits.window_start},%s),0)' % (WS, DONE, WS)
def WIN_EXP(): return 'IFERROR(COUNTIFS({range:visits.window_start},%s,{range:visits.status},%s,{range:visits.done_on},"<="&EDATE({today},-12))/COUNTIFS({range:visits.window_start},%s),0)' % (WSL, DONE, WSL)
def WIN_PLANNED(): return 'COUNTIFS({range:visits.window_start},%s)' % WS
def WIN_DONEN(): return 'COUNTIFS({range:visits.window_start},%s,{range:visits.status},%s)' % (WS, DONE)
WIN_END = 'EDATE(%s,4)' % WS
WEEKS_LEFT = 'MAX(1,(%s-{today})/7)' % WIN_END

settings = [
    S('company', 'Your company name', 'text', COMPANY), S('replace_age', 'Equipment age that makes a replacement lead, years', 'int', 12),
    S('renewal_target', 'Agreement renewal rate wanted (typical range, check yours)', 'pct', 0.85), S('renewal_warn_days', 'Days before renewal that count as red', 'int', RENEWAL_WARN_DAYS),
    S('renewal_amber_days', 'Days before renewal that count as amber', 'int', 60), S('attach_target', 'Agreements sold per eligible job wanted', 'pct', 0.02),
    S('spiff_agreement', 'Bonus for each agreement sold, a fixed bonus per item sold', 'money', SPIFF_AGREEMENT), S('member_discount', 'Member discount on repairs', 'pct', MEMBER_DISCOUNT),
    S('capacity_hours', 'Productive hours in a technician day, drive time included', 'num', 8.5), S('tune_techs', 'Technicians who run tune-ups', 'int', 4),
    S('visit_hours', 'Hours of one tune-up visit, drive time included', 'num', 1.8), S('busy_share', 'Share of a technician day taken by other work', 'pct', 0.55),
    S('overdue_back_days', 'Days back to count a missed visit as overdue', 'int', 200), S('lead_quota', 'Aged equipment leads to call each week', 'int', 10),
    S('booked_target', 'Reminders that should book a tune-up (set your own)', 'pct', 0.25), S('cost_text', 'Cost of one text message reminder', 'money', 0.2),
    S('cost_letter', 'Cost of one mailed letter reminder, print and post', 'money', 1.4), S('cost_call', 'Cost of one reminder phone call, office time', 'money', 4.5),
    S('cost_booked_target', 'Cost per booked tune-up you accept', 'money', 20), S('follow_margin', 'Margin on repair and replacement work', 'pct', 0.45),
]
tables = []
# 1 customer sites
tables.append(T('sites', 'Customer Sites', 'Customer sites by reference, area and phone',
  'One row per customer site: reference, area, site type, landlord or business account, phone, equipment and jobs. Oldest equipment age, last service and open tune-ups fill in by themselves. Customers appear as a reference, never by name.', [
    C('site_id', 'Site', 'text', 10, required=True), C('site_ref', 'Site reference', 'text', 11), LST('area', 'Area', 'area', 11), LST('site_type', 'Site type', 'sitetype', 10), C('landlord', 'Landlord account', 'bool', 9),
    C('account', 'Account', 'text', 10), C('phone', 'Phone', 'text', 18), C('member', 'Member', 'bool', 9), C('equipment', 'Equipment', 'int', 9), C('jobs', 'Jobs', 'int', 7), C('first_job', 'First job', 'date', 11),
    C('last_job', 'Last job', 'date', 11), C('revenue', 'Revenue', 'money', 11),
    CA('oldest_age', 'Oldest equipment, years', 'num', 'IF({col:equipment}>0,ROUND(SUMPRODUCT(MAX(({range:equipment.site_id}={col:site_id})*({today}-{range:equipment.install_date})))/365.25,1),"")', 11),
    CA('last_service', 'Last service', 'date', 'IF({col:equipment}>0,IF(SUMPRODUCT(MAX(({range:equipment.site_id}={col:site_id})*{range:equipment.last_service}))=0,"",SUMPRODUCT(MAX(({range:equipment.site_id}={col:site_id})*{range:equipment.last_service}))),"")', 11),
    CA('gap_months', 'Months since a service', 'int', 'IF({col:equipment}=0,"",IF({col:last_service}="",999,ROUND(({today}-{col:last_service})/30.4,0)))', 9),
    CA('open_visits', 'Open tune-ups', 'int', 'COUNTIFS({range:visits.site_id},{col:site_id},{range:visits.status},%s)+COUNTIFS({range:visits.site_id},{col:site_id},{range:visits.status},%s)' % (DUE, BOOKED), 9),
    CA('due_renewals', 'Renewals due this month', 'int', 'COUNTIFS({range:agreements.site_id},{col:site_id},{range:agreements.due_month},1)', 9), COMPANY_COL()],
  D.sites_d(), 1500, [A('member', '= ' + YES, 'good'), A('gap_months', '>= 24', 'warn')]))
# 2 equipment
tables.append(T('equipment', 'Equipment', 'Equipment records with age and replacement lead score',
  'One row per piece of equipment: type, fuel, install date, make, model, serial and last service. Age, the aged flag, the lead score and the call-now, mail or hold verdict fill in by themselves. No technical data is kept.', [
    C('equipment_id', 'Equipment', 'text', 10, required=True), C('site_id', 'Site', 'text', 10), LST('type', 'Type', 'equiptype', 14), LST('fuel', 'Fuel', 'fuel', 9), C('install_date', 'Install date', 'date', 11), C('warranty_end', 'Warranty end', 'date', 11),
    C('make', 'Make', 'text', 9), C('model', 'Model', 'text', 10), C('serial', 'Serial', 'text', 12), C('last_service', 'Last service', 'date', 11),
    CA('site_ref', 'Site reference', 'text', LKT('sites.site_ref', 'sites.site_id', 'site_id'), 11),
    CA('age_years', 'Age, years', 'num', 'ROUND(({today}-{col:install_date})/365.25,1)', 8),
    CA('aged', 'Aged (1 or 0)', 'int', 'IF({col:age_years}>={set:replace_age},1,0)', 8),
    CA('never_serviced', 'Never serviced (1 or 0)', 'int', 'IF({col:last_service}="",1,0)', 9),
    CA('gap_months', 'Months since a service', 'int', 'IF({col:last_service}="","",ROUND(({today}-{col:last_service})/30.4,0))', 9),
    CA('site_jobs', 'Jobs at the site', 'int', LKN('sites.jobs', 'sites.site_id', 'site_id'), 8),
    CA('replace_value', 'Replacement value', 'money', 'IFERROR(INDEX({range:equip_types.replace_ticket},MATCH({col:type},{range:equip_types.type},0)),0)', 11),
    CA('lead_score', 'Lead score', 'num', 'IF({col:aged}=1,{col:age_years}+IF({col:never_serviced}=1,3,IF({today}-{col:last_service}>548,2,0))+MIN({col:site_jobs},10)/10+VALUE(RIGHT({col:equipment_id},4))/1000000,"")', 10),
    CA('verdict', 'Call now, mail or hold', 'text', 'IF({col:aged}=0,%s,IF({col:lead_score}>=IFERROR(LARGE({range:equipment.lead_score},{set:lead_quota}),0),%s,%s))' % (ck('Hold'), ck('Call now'), ck('Mail')), 12),
    CA('complete', 'Record complete (1 or 0)', 'int', 'IF(AND({col:install_date}<>"",{col:make}<>"",{col:model}<>"",{col:serial}<>""),1,0)', 9)],
  D.equipment_d(), 2000, [A('verdict', '= ' + ck('Call now'), 'bad'), A('verdict', '= ' + ck('Mail'), 'warn'), A('never_serviced', '= 1', 'warn')]))
# 3 agreements
tables.append(T('agreements', 'Agreements', 'Agreements with plan, price, renewal date and status',
  'One row per maintenance agreement, a yearly plan with tune-ups: plan, price, start, renewal date and status. Days left, the renewal flag, monthly recurring revenue and the ranking of renewals due fill in by themselves.', [
    C('agreement_id', 'Agreement', 'text', 10, required=True), C('site_id', 'Site', 'text', 10), LST('site_type', 'Site type', 'sitetype', 10), LST('plan', 'Plan', 'plan', 19), C('price', 'Price a year', 'money', 11), C('visits_per_year', 'Visits a year', 'int', 8),
    C('billing', 'Billing', 'text', 9), C('start_date', 'Start date', 'date', 11), C('end_date', 'End date', 'date', 11), C('renewal_date', 'Renewal date', 'date', 11), C('last_renewed', 'Last renewed', 'date', 11), C('renewals', 'Renewals', 'int', 8),
    LST('status', 'Status', 'agrstatus', 12), LST('sold_by', 'Sold by', 'tech', 16), C('visits_done', 'Visits done', 'int', 8), LST('lapse_reason', 'Lapse reason', 'lapsereason', 22),
    CA('site_ref', 'Site reference', 'text', LKT('sites.site_ref', 'sites.site_id', 'site_id'), 11), CA('phone', 'Phone', 'text', LKT('sites.phone', 'sites.site_id', 'site_id'), 18), CA('account', 'Account', 'text', LKT('sites.account', 'sites.site_id', 'site_id'), 10),
    CA('running', 'Running (1 or 0)', 'int', 'IF(OR({col:status}=%s,{col:status}=%s),1,0)' % (ACT, RD), 8),
    CA('end_eff', 'End key', 'int', 'IF({col:end_date}="",99999,{col:end_date})', 8),
    CA('days_left', 'Days to renewal', 'int', 'IF(OR({col:renewal_date}="",{col:running}=0),"",{col:renewal_date}-{today})', 9),
    CA('due_month', 'Due this month (1 or 0)', 'int', 'IF(AND({col:status}=%s,{col:renewal_date}>=%s,{col:renewal_date}<EDATE(%s,1)),1,0)' % (RD, MS, MS), 9),
    CA('due_score', 'Renewal call score', 'num', 'IF({col:due_month}=1,{col:price}+(400-{col:days_left})/10000+VALUE(RIGHT({col:agreement_id},4))/1000000000,"")', 11),
    CA('flag', 'Renewal flag', 'text', 'IF({col:running}=0,%s,IF({col:days_left}<0,%s,IF({col:days_left}<={set:renewal_warn_days},%s,IF({col:days_left}<={set:renewal_amber_days},%s,%s))))' % (ck('Ended'), ck('Past the renewal date'), ck('Red: due soon'), ck('Amber: due in the next weeks'), ck('Green: renewal later')), 20),
    CA('months_member', 'Months as a member', 'int', 'IF({col:end_date}="",ROUND(({today}-{col:start_date})/30.4,0),ROUND(({col:end_date}-{col:start_date})/30.4,0))', 9),
    CA('lapse_score', 'Lapse order score', 'num', 'IF(OR({col:status}=%s,{col:status}=%s),{col:end_date}+VALUE(RIGHT({col:agreement_id},4))/100000,"")' % (LAP, CAN), 11),
    CA('mrr', 'Monthly recurring revenue', 'money', 'IF({col:running}=1,{col:price}/12,0)', 11),
    CA('reason_n', 'Same reason, last 12 months', 'int', 'IF(AND({col:lapse_reason}<>"",{col:end_date}>={today}-365),COUNTIFS({range:agreements.lapse_reason},{col:lapse_reason},{range:agreements.end_date},">="&({today}-365)),"")', 10),
    CA('visit_value', 'Value of one visit', 'money', 'IFERROR({col:price}/{col:visits_per_year},0)', 10),
    CA('member_pct', 'Member discount on repairs', 'pct', '{set:member_discount}', 10), COMPANY_COL()],
  D.agreements_d(), 500, [A('flag', '= ' + ck('Past the renewal date'), 'bad'), A('flag', '= ' + ck('Red: due soon'), 'bad'), A('flag', '= ' + ck('Amber: due in the next weeks'), 'warn'), A('status', '= ' + LAP, 'warn')]))
# 4 renewals
tables.append(T('renewals', 'Renewals', 'Agreement renewals with due date and outcome',
  'One row per renewal that came due: the agreement, the due date, the date it was renewed and the outcome (renewed, lapsed or still open). Days late fills in by itself.', [
    C('renewal_id', 'Renewal', 'text', 10, required=True), C('agreement_id', 'Agreement', 'text', 10), C('site_id', 'Site', 'text', 10), LST('plan', 'Plan', 'plan', 19), C('due_date', 'Due date', 'date', 11), C('month', 'Month', 'date', 10),
    C('renewed_on', 'Renewed on', 'date', 11), LST('outcome', 'Outcome', 'renewout', 10), C('price', 'Price', 'money', 10),
    CA('site_ref', 'Site reference', 'text', LKT('sites.site_ref', 'sites.site_id', 'site_id'), 11),
    CA('days_late', 'Days from due date to renewal', 'int', 'IF({col:renewed_on}="","",{col:renewed_on}-{col:due_date})', 10),
    CA('days_open', 'Days open', 'int', 'IF({col:outcome}=%s,{today}-{col:due_date},"")' % ROPEN, 8)],
  D.renewals_d(), 1050, [A('outcome', '= ' + RLAPSED, 'bad'), A('outcome', '= ' + ROPEN, 'warn'), A('outcome', '= ' + RENEWED, 'good')]))
# 5 tune-up visits
tables.append(T('visits', 'Tune-up Visits', 'Tune-up visits by window, plan and status',
  'One row per tune-up visit, a planned seasonal visit to one system: the window, the planned date, the date done and the status. Behind, overdue and the value of the visit fill in by themselves.', [
    C('visit_id', 'Visit', 'text', 10, required=True), C('agreement_id', 'Agreement', 'text', 10), C('site_id', 'Site', 'text', 10), LST('plan', 'Plan', 'plan', 19), LST('season', 'Window', 'visitseason', 20),
    C('window_start', 'Window start', 'date', 11), C('window_end', 'Window end', 'date', 11), C('planned_date', 'Planned date', 'date', 11), C('done_on', 'Done on', 'date', 11), LST('technician', 'Technician', 'tech', 16),
    C('job_id', 'Job', 'text', 10), LST('status', 'Status', 'visitstatus', 9),
    CA('site_ref', 'Site reference', 'text', LKT('sites.site_ref', 'sites.site_id', 'site_id'), 11), CA('phone', 'Phone', 'text', LKT('sites.phone', 'sites.site_id', 'site_id'), 18),
    CA('plan_price', 'Plan price', 'money', 'IFERROR(INDEX({range:plans.price},MATCH({col:plan},{range:plans.plan},0)),0)', 10),
    CA('visit_value', 'Value of the visit', 'money', 'IFERROR({col:plan_price}/INDEX({range:plans.visits_per_year},MATCH({col:plan},{range:plans.plan},0)),0)', 10),
    CA('behind', 'Behind plan (1 or 0)', 'int', 'IF(AND(OR({col:status}=%s,{col:status}=%s),{col:planned_date}<{today}),1,0)' % (DUE, BOOKED), 9),
    CA('overdue_score', 'Overdue call score', 'num', 'IF(AND({col:status}=%s,{col:window_end}>={today}-{set:overdue_back_days}),{col:plan_price}+VALUE(RIGHT({col:visit_id},5))/1000000,"")' % MISSED, 11),
    CA('days_past_end', 'Days past the window end', 'int', 'IF({col:overdue_score}="","",{today}-{col:window_end})', 9),
    CA('assigned', 'Technician for the visit', 'text', 'IF({col:technician}<>"",{col:technician},IFERROR(INDEX({range:agreements.sold_by},MATCH({col:agreement_id},{range:agreements.agreement_id},0))&"",""))', 16),
    TECHPH(), CA('overdue_count', 'Visits overdue now', 'int', 'COUNTIFS({range:visits.overdue_score},">0")', 9),
    CONST('office_phone', 'Office manager phone', D.OFFICE_PHONE), CA('apprentice', 'Apprentice', 'text', tok('crew', D.APPRENTICE), 16), CONST('apprentice_phone', 'Apprentice phone', D.APPRENTICE_PHONE), COMPANY_COL()],
  D.visits_d(), 1500, [A('status', '= ' + MISSED, 'bad'), A('behind', '= 1', 'warn'), A('status', '= ' + DONE, 'good')]))
# 6 agreement plans (3 columns)
tables.append(T('plans', 'Agreement Plans', 'Agreement plans with price and visits a year', 'The five plans you sell, the yearly price and the tune-up visits each includes; the visit value and plan profit read this sheet.',
  [C('plan', 'Plan', 'text', 19, required=True), C('price', 'Price a year', 'money', 12), C('visits_per_year', 'Visits a year', 'int', 9)], D.plans_d(), 12))
# 7 aged equipment ranked
def IX(t, c): return 'IF({col:pos}="","",INDEX({range:%s.%s},{col:pos}))' % (t, c)
tables.append(T('aged', 'Aged Equipment', 'Aged equipment ranked as replacement leads',
  'Type the rank numbers 1, 2, 3 and so on: each row shows the aged equipment with that lead score, its site reference, age, last service, replacement value and whether to call this week, mail or hold.', [
    C('rank_no', 'Rank', 'int', 7, required=True), CA('pos', 'Row', 'int', 'IFERROR(MATCH(LARGE({range:equipment.lead_score},{col:rank_no}),{range:equipment.lead_score},0),"")', 6),
    CA('equipment_id', 'Equipment', 'text', IX('equipment', 'equipment_id'), 10), CA('site_id', 'Site', 'text', IX('equipment', 'site_id'), 10), CA('site_ref', 'Site reference', 'text', IX('equipment', 'site_ref'), 11),
    CA('type', 'Type', 'text', IX('equipment', 'type'), 14), CA('age_years', 'Age, years', 'num', IX('equipment', 'age_years'), 8),
    CA('last_service', 'Last service', 'date', 'IF({col:pos}="","",IF(INDEX({range:equipment.last_service},{col:pos})=0,"",INDEX({range:equipment.last_service},{col:pos})))', 11),
    CA('service_note', 'Service record', 'text', 'IF({col:pos}="","",IF({col:last_service}="",%s,%s))' % (ck('Not serviced by the shop'), ck('Serviced by the shop')), 14),
    CA('lead_score', 'Lead score', 'num', IX('equipment', 'lead_score'), 9), CA('replace_value', 'Replacement value', 'money', IX('equipment', 'replace_value'), 11),
    CA('call_week', 'This week', 'text', 'IF({col:pos}="","",IF({col:rank_no}<={set:lead_quota},%s,%s))' % (ck('Call this week'), ck('Mail')), 14),
    CA('phone', 'Phone', 'text', 'IF({col:pos}="","",IFERROR(INDEX({range:sites.phone},MATCH({col:site_id},{range:sites.site_id},0))&"",""))', 18),
    CA('aged_count', 'Aged equipment records', 'int', 'COUNTIFS({range:equipment.aged},1)', 9), CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), COMPANY_COL()],
  D.aged_d(), 60, [A('call_week', '= ' + ck('Call this week'), 'bad'), A('call_week', '= ' + ck('Mail'), 'warn')]))
# 8 renewals due this month ranked
def IA(c): return 'IF({col:pos}="","",INDEX({range:agreements.%s},{col:pos}))' % c
tables.append(T('renew_due', 'Renewals Due', 'Renewals due this month ranked by value and days left',
  'Type the rank numbers 1, 2, 3 and so on: each row shows the agreement due this month and not yet renewed, ranked by value then by days left, with the call-by date and the phone for the text.', [
    C('rank_no', 'Rank', 'int', 7, required=True), CA('pos', 'Row', 'int', 'IFERROR(MATCH(LARGE({range:agreements.due_score},{col:rank_no}),{range:agreements.due_score},0),"")', 6),
    CA('agreement_id', 'Agreement', 'text', IA('agreement_id'), 10), CA('site_ref', 'Site reference', 'text', IA('site_ref'), 11), CA('plan', 'Plan', 'text', IA('plan'), 19), CA('price', 'Price a year', 'money', IA('price'), 10),
    CA('renewal_date', 'Renewal date', 'date', IA('renewal_date'), 11), CA('days_left', 'Days left', 'int', IA('days_left'), 8), CA('flag', 'Flag', 'text', IA('flag'), 20),
    CA('call_by', 'Call by', 'date', 'IF({col:pos}="","",MAX({today},WORKDAY({col:renewal_date},-5)))', 11), CA('phone', 'Phone', 'text', IA('phone'), 18),
    CA('due_count', 'Renewals due this month', 'int', 'SUM({range:agreements.due_month})', 9), CA('risk_total', 'Revenue at risk', 'money', 'SUMIFS({range:agreements.price},{range:agreements.due_month},1)', 11),
    CONST('office_phone', 'Office manager phone', D.OFFICE_PHONE), CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), COMPANY_COL()],
  D.renew_due_d(), 60, [A('flag', '= ' + ck('Past the renewal date'), 'bad'), A('flag', '= ' + ck('Red: due soon'), 'bad'), A('flag', '= ' + ck('Amber: due in the next weeks'), 'warn')]))
# 9 lapse list
tables.append(T('lapse', 'Lapse List', 'Lapsed and cancelled agreements, newest first',
  'Type the rank numbers 1, 2, 3 and so on: each row shows the lapsed or cancelled agreement ended most recently, with the plan, price, months as a member and the reason noted.', [
    C('rank_no', 'Rank', 'int', 7, required=True), CA('pos', 'Row', 'int', 'IFERROR(MATCH(LARGE({range:agreements.lapse_score},{col:rank_no}),{range:agreements.lapse_score},0),"")', 6),
    CA('agreement_id', 'Agreement', 'text', IA('agreement_id'), 10), CA('site_ref', 'Site reference', 'text', IA('site_ref'), 11), CA('plan', 'Plan', 'text', IA('plan'), 19),
    CA('end_date', 'Ended on', 'date', 'IF({col:pos}="","",IF(INDEX({range:agreements.end_date},{col:pos})=0,"",INDEX({range:agreements.end_date},{col:pos})))', 11), CA('price', 'Price a year', 'money', IA('price'), 10),
    CA('months_member', 'Months as a member', 'int', IA('months_member'), 9), CA('reason', 'Reason noted', 'text', IA('lapse_reason'), 22), CA('phone', 'Phone', 'text', IA('phone'), 18), COMPANY_COL()],
  D.lapse_d(), 60, [A('months_member', '< 12', 'warn')]))
# 10 agreement book by month
def BK(c): return '{range:agreements.%s}' % c
NXT = 'EDATE({col:month},1)'
tables.append(T('book_month', 'Agreement Book by Month', 'Agreement book by month and recurring revenue',
  'One row per month: new, lapsed and running agreements from the Agreements sheet, renewals from the Renewals sheet, monthly recurring revenue and the renewal rate. The last month is month to date.', [
    C('month', 'Month', 'date', 10, required=True),
    CA('new', 'New agreements', 'int', 'COUNTIFS({range:agreements.start_date},">="&{col:month},{range:agreements.start_date},"<"&%s)' % NXT, 9),
    CA('renewed', 'Renewed', 'int', 'COUNTIFS({range:renewals.month},{col:month},{range:renewals.outcome},%s)' % RENEWED, 9),
    CA('renew_lapsed', 'Renewals lapsed', 'int', 'COUNTIFS({range:renewals.month},{col:month},{range:renewals.outcome},%s)' % RLAPSED, 9),
    CA('renewals_due', 'Renewals due', 'int', 'COUNTIFS({range:renewals.month},{col:month})', 9),
    CA('lapsed', 'Agreements ended', 'int', 'COUNTIFS({range:agreements.end_date},">="&{col:month},{range:agreements.end_date},"<"&%s)' % NXT, 9),
    CA('running', 'Running at month end', 'int', 'COUNTIFS({range:agreements.start_date},"<"&%s,{range:agreements.end_eff},">="&%s)' % (NXT, NXT), 9),
    CA('mrr', 'Monthly recurring revenue', 'money', 'SUMIFS({range:agreements.price},{range:agreements.start_date},"<"&%s,{range:agreements.end_eff},">="&%s)/12' % (NXT, NXT), 12),
    CA('renew_rate', 'Renewal rate', 'pct', 'IFERROR({col:renewed}/({col:renewed}+{col:renew_lapsed}),0)', 9),
    CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), CONST('acct_phone', 'Accountant phone', D.ACCT_PHONE), COMPANY_COL()],
  D.book_month_d(), 40, [A('renew_rate', '< {set:renewal_target}', 'warn')]))
# 11 plans by status
tables.append(T('plan_status', 'Plans by Status', 'Agreements and yearly fees by plan and status',
  'One row per plan and status: the number of agreements and the yearly fees, counted from the Agreements sheet; the lapse rate of the plan fills in by itself.', [
    LST('plan', 'Plan', 'plan', 19, required=True), LST('status', 'Status', 'agrstatus', 12),
    CA('agreements', 'Agreements', 'int', 'COUNTIFS({range:agreements.plan},{col:plan},{range:agreements.status},{col:status})', 9),
    CA('revenue', 'Yearly fees', 'money', 'SUMIFS({range:agreements.price},{range:agreements.plan},{col:plan},{range:agreements.status},{col:status})', 11),
    CA('lapse_rate', 'Lapse rate of the plan', 'pct', 'IFERROR((COUNTIFS({range:agreements.plan},{col:plan},{range:agreements.status},%s)+COUNTIFS({range:agreements.plan},{col:plan},{range:agreements.status},%s))/COUNTIFS({range:agreements.plan},{col:plan}),0)' % (LAP, CAN), 10)],
  D.plan_status_d(), 40))
# 12 visits due by month
tables.append(T('visits_month', 'Visits Due by Month', 'Tune-up visits due by month against technician hours',
  'One row per month: visits due and done from the Tune-up Visits sheet, hours needed, hours free for tune-ups after the other work of the season (demand index, 1.00 is an average month) and the slack. The open window gap fills in too.', [
    C('month', 'Month', 'date', 10, required=True), C('demand_index', 'Demand index', 'num', 9),
    CA('visits_due', 'Visits due', 'int', 'COUNTIFS({range:visits.planned_date},">="&{col:month},{range:visits.planned_date},"<"&EDATE({col:month},1))', 8),
    CA('visits_done', 'Visits done', 'int', 'COUNTIFS({range:visits.done_on},">="&{col:month},{range:visits.done_on},"<"&EDATE({col:month},1))', 8),
    CA('workdays', 'Working days', 'int', 'NETWORKDAYS({col:month},EOMONTH({col:month},0))', 8),
    CA('hours_needed', 'Hours needed', 'num', '{col:visits_due}*{set:visit_hours}', 9),
    CA('free_share', 'Share of the day free', 'pct', 'MAX(0.05,1-{col:demand_index}*{set:busy_share})', 9),
    CA('hours_per_tech', 'Free hours per technician', 'num', '{col:workdays}*{set:capacity_hours}*{col:free_share}', 10),
    CA('capacity_hours', 'Hours free for tune-ups', 'num', '{set:tune_techs}*{col:hours_per_tech}', 10),
    CA('visits_per_hour', 'Visits due per free hour', 'num', 'IFERROR({col:visits_due}/{col:hours_per_tech},0)', 9),
    CA('slack_hours', 'Slack hours', 'num', '{col:capacity_hours}-{col:hours_needed}', 9), CA('load', 'Load', 'pct', 'IFERROR({col:hours_needed}/{col:capacity_hours},0)', 8),
    CA('flag', 'Month check', 'text', 'IF({col:load}>1,%s,IF({col:load}<0.5,%s,%s))' % (ck('Over capacity'), ck('Room to add tune-ups'), ck('Fits')), 18),
    CA('window_gap', 'Open window gap, points', 'pct', '%s-%s' % (WIN_DONE(), WIN_EXP()), 10),
    CA('book_week', 'Visits to book this week', 'int', 'ROUNDUP(MAX(0,%s-%s)/%s,0)' % (WIN_PLANNED(), WIN_DONEN(), WEEKS_LEFT), 9),
    CONST('office_phone', 'Office manager phone', D.OFFICE_PHONE), CONST('parts_phone', 'Parts counter phone', D.PARTS_PHONE), COMPANY_COL()],
  D.visits_month_d(), 40, [A('flag', '= ' + ck('Over capacity'), 'bad'), A('flag', '= ' + ck('Room to add tune-ups'), 'warn')]))
# 13 member versus non-member revenue
tables.append(T('member_rev', 'Member Revenue', 'Member and non-member revenue by area, last 12 months',
  'One row per member group and area: revenue of the last 12 months split into repairs, replacements, tune-up work and agreement fees; the sites and the revenue per site fill in by themselves.', [
    C('member', 'Member', 'bool', 9, required=True), LST('area', 'Area', 'area', 11),
    CA('sites', 'Sites', 'int', 'COUNTIFS({range:sites.member},{col:member},{range:sites.area},{col:area})', 8),
    C('repair_revenue', 'Repair revenue', 'money', 12), C('replacement_revenue', 'Replacement revenue', 'money', 12), C('tune_up_revenue', 'Tune-up work revenue', 'money', 12), C('agreement_fees', 'Agreement fees', 'money', 12),
    CA('total_revenue', 'Total revenue', 'money', '{col:repair_revenue}+{col:replacement_revenue}+{col:tune_up_revenue}+{col:agreement_fees}', 12),
    CA('per_site', 'Revenue per site', 'money', 'IFERROR({col:total_revenue}/{col:sites},0)', 11)],
  D.member_rev_d(), 40, [A('per_site', '>= 2000', 'good')]))
# 14 agreement profit by plan and site type
tables.append(T('plan_profit', 'Agreement Profit', 'Agreement profit by plan and site type',
  'One row per plan and site type: cost of a visit, travel and the member discount from your own jobs, with the plan price from the Agreement Plans sheet; profit, margin and the profit on follow-on repairs and replacements fill in by themselves.', [
    LST('plan', 'Plan', 'plan', 19, required=True), LST('site_type', 'Site type', 'sitetype', 10), C('visit_cost', 'Cost of one visit', 'money', 11), C('travel_cost', 'Travel cost a visit', 'money', 11),
    C('follow_on', 'Follow-on revenue a year', 'money', 12), C('discount_given', 'Member discount given a year', 'money', 12),
    CA('price', 'Plan price', 'money', 'IFERROR(INDEX({range:plans.price},MATCH({col:plan},{range:plans.plan},0)),0)', 10),
    CA('visits', 'Visits a year', 'int', 'IFERROR(INDEX({range:plans.visits_per_year},MATCH({col:plan},{range:plans.plan},0)),0)', 8),
    CA('agreements', 'Running agreements', 'int', 'COUNTIFS({range:agreements.plan},{col:plan},{range:agreements.site_type},{col:site_type},{range:agreements.running},1)', 9),
    CA('visit_total', 'Visit cost a year', 'money', '{col:visits}*{col:visit_cost}', 10), CA('travel_total', 'Travel a year', 'money', '{col:visits}*{col:travel_cost}', 10),
    CA('cost_total', 'Cost a year', 'money', '{col:visit_total}+{col:travel_total}+{col:discount_given}', 10), CA('profit', 'Profit on the plan', 'money', '{col:price}-{col:cost_total}', 10),
    CA('margin', 'Margin on the plan', 'pct', 'IFERROR({col:profit}/{col:price},0)', 9), CA('follow_profit', 'Profit on follow-on work', 'money', '{col:follow_on}*{set:follow_margin}', 11),
    CA('total_value', 'Plan and follow-on profit', 'money', '{col:profit}+{col:follow_profit}', 11),
    CA('w_cost', 'Cost x agreements', 'money', '{col:agreements}*{col:cost_total}', 10), CA('w_follow', 'Follow-on x agreements', 'money', '{col:agreements}*{col:follow_on}', 11),
    CA('w_visit', 'Visit and travel x agreements', 'money', '{col:agreements}*({col:visit_total}+{col:travel_total})', 11)],
  D.plan_profit_d(), 40, [A('profit', '< 0', 'bad'), A('total_value', '< 0', 'bad')]))
# 15 campaign list
tables.append(T('campaign', 'Campaign List', 'Pre-season reminders by site, channel and result',
  'One row per reminder sent to a site before a tune-up window: the date, the channel, whether a tune-up was booked and whether an agreement was sold. Last service, equipment age, cost and the next window start fill in by themselves.', [
    C('campaign_id', 'Reminder', 'text', 10, required=True), C('site_id', 'Site', 'text', 10), C('reminder_sent', 'Reminder sent', 'date', 11), LST('channel', 'Channel', 'channel', 14), C('booked', 'Booked', 'bool', 8), C('converted', 'Agreement sold', 'bool', 9),
    CA('site_ref', 'Site reference', 'text', LKT('sites.site_ref', 'sites.site_id', 'site_id'), 11), CA('phone', 'Phone', 'text', LKT('sites.phone', 'sites.site_id', 'site_id'), 18),
    CA('last_service', 'Last service', 'date', 'IF(SUMPRODUCT(MAX(({range:equipment.site_id}={col:site_id})*{range:equipment.last_service}))=0,"",SUMPRODUCT(MAX(({range:equipment.site_id}={col:site_id})*{range:equipment.last_service})))', 11),
    CA('equip_age', 'Oldest equipment, years', 'num', 'ROUND(SUMPRODUCT(MAX(({range:equipment.site_id}={col:site_id})*({today}-{range:equipment.install_date})))/365.25,1)', 10),
    CA('cost', 'Cost of the reminder', 'money', 'IF({col:channel}=%s,{set:cost_text},IF({col:channel}=%s,{set:cost_letter},{set:cost_call}))' % (tok('channel', 'Text message'), tok('channel', 'Mailed letter')), 10),
    CA('next_window', 'Next window starts', 'date', 'IF({col:reminder_sent}<=DATE(YEAR({col:reminder_sent}),2,15),DATE(YEAR({col:reminder_sent}),2,15),IF({col:reminder_sent}<=DATE(YEAR({col:reminder_sent}),8,15),DATE(YEAR({col:reminder_sent}),8,15),DATE(YEAR({col:reminder_sent})+1,2,15)))', 11),
    COMPANY_COL()],
  D.campaign_d(), 400, [A('booked', '= ' + YES, 'good'), A('converted', '= ' + YES, 'good')]))
# 16 campaign results by month
tables.append(T('campaign_month', 'Campaign Results', 'Campaign results by month',
  'One row per month, counted from the Campaign List: reminders sent, tune-ups booked, agreements sold and cost; the booked rate and the cost per booked tune-up fill in by themselves.', [
    C('month', 'Month', 'date', 10, required=True),
    CA('reminders', 'Reminders', 'int', 'COUNTIFS({range:campaign.reminder_sent},">="&{col:month},{range:campaign.reminder_sent},"<"&EDATE({col:month},1))', 9),
    CA('booked', 'Tune-ups booked', 'int', 'COUNTIFS({range:campaign.reminder_sent},">="&{col:month},{range:campaign.reminder_sent},"<"&EDATE({col:month},1),{range:campaign.booked},%s)' % YES, 9),
    CA('sold', 'Agreements sold', 'int', 'COUNTIFS({range:campaign.reminder_sent},">="&{col:month},{range:campaign.reminder_sent},"<"&EDATE({col:month},1),{range:campaign.converted},%s)' % YES, 9),
    CA('cost', 'Cost', 'money', 'SUMIFS({range:campaign.cost},{range:campaign.reminder_sent},">="&{col:month},{range:campaign.reminder_sent},"<"&EDATE({col:month},1))', 10),
    CA('booked_rate', 'Booked rate', 'pct', 'IFERROR({col:booked}/{col:reminders},0)', 9), CA('cost_per_booked', 'Cost per booked tune-up', 'money', 'IFERROR({col:cost}/{col:booked},0)', 11),
    CONST('owner_phone', 'Owner phone', D.OWNER_PHONE), COMPANY_COL()],
  D.campaign_month_d(), 40, [A('booked_rate', '< {set:booked_target}', 'warn')]))
# 17 equipment by age band and type
tables.append(T('age_bands', 'Equipment by Age Band', 'Equipment by age band and type with expected replacements',
  'One row per age band and equipment type: records counted from the Equipment sheet, the share you expect to replace next year (set your own from your own history) and the replacements and revenue that follow.', [
    LST('band', 'Age band', 'ageband', 15, required=True), LST('type', 'Type', 'equiptype', 14), C('replace_share', 'Replaced next year (share)', 'pct', 10),
    CA('age_from', 'From, years', 'int', 'IF({col:band}=%s,0,IF({col:band}=%s,6,IF({col:band}=%s,11,16)))' % (tok('ageband', 'Up to 5 years'), tok('ageband', 'From 6 to 10 years'), tok('ageband', 'From 11 to 15 years')), 7),
    CA('age_to', 'To, years', 'int', 'IF({col:band}=%s,6,IF({col:band}=%s,11,IF({col:band}=%s,16,200)))' % (tok('ageband', 'Up to 5 years'), tok('ageband', 'From 6 to 10 years'), tok('ageband', 'From 11 to 15 years')), 7),
    CA('records', 'Records', 'int', 'COUNTIFS({range:equipment.type},{col:type},{range:equipment.age_years},">="&{col:age_from},{range:equipment.age_years},"<"&{col:age_to})', 8),
    CA('expected', 'Replacements expected', 'num', '{col:records}*{col:replace_share}', 10), CA('expected_whole', 'Replacements, whole number', 'int', 'ROUND({col:expected},0)', 10),
    CA('value', 'Replacement revenue', 'money', '{col:expected}*IFERROR(INDEX({range:equip_types.replace_ticket},MATCH({col:type},{range:equip_types.type},0)),0)', 12),
    CONST('supplier_phone', 'Equipment supplier phone', D.SUP_PHONE), COMPANY_COL()],
  D.age_bands_d(), 40))
# 18 technicians (3 columns)
tables.append(T('techs', 'Technicians', 'Technicians with trade and van', 'The six lead technicians, their trade and the van they drive; the phones for the texts read this sheet.',
  [C('technician', 'Technician', 'text', 24, required=True), C('trade', 'Trade', 'text', 11), C('van', 'Van', 'text', 9)], D.techs_d(), 12))
# 19 agreement attach by technician
tables.append(T('attach', 'Agreement Attach', 'Agreement attach rate by technician and period',
  'One row per technician and period: the eligible jobs (repair, diagnostic, replacement and install jobs at sites without an agreement) you count, and the agreements sold from the Agreements sheet; the attach rate and the bonus cost fill in by themselves.', [
    LST('technician', 'Technician', 'tech', 16, required=True), LST('period', 'Period', 'period', 18), C('eligible', 'Eligible jobs', 'int', 9),
    CA('from_date', 'From', 'date', 'IF({col:period}=%s,{today}-365,{today}-730)' % tok('period', 'Last 12 months'), 11), CA('to_date', 'To', 'date', 'IF({col:period}=%s,{today},{today}-365)' % tok('period', 'Last 12 months'), 11),
    CA('sold', 'Agreements sold', 'int', 'COUNTIFS({range:agreements.sold_by},{col:technician},{range:agreements.start_date},">"&{col:from_date},{range:agreements.start_date},"<="&{col:to_date})', 9),
    CA('attach_rate', 'Attach rate', 'pct', 'IFERROR({col:sold}/{col:eligible},0)', 9), CA('gap', 'Gap to the target', 'pct', '{col:attach_rate}-{set:attach_target}', 9),
    CA('spiff_cost', 'Bonus cost', 'money', '{col:sold}*{set:spiff_agreement}', 9),
    CA('rate_last', 'Rate, last 12 months', 'pct', 'IF({col:period}=%s,{col:attach_rate},"")' % tok('period', 'Last 12 months'), 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:attach_rate}>={set:attach_target},%s,%s)' % (ck('On target'), ck('Coach on the offer')), 16),
    CA('tech_phone', 'Technician phone', 'text', 'IFERROR(CHOOSE(MATCH({col:technician},{range:techs.technician},0),%s),"")' % ','.join(ph(p) for p in D.TECH_PHONES[:6]), 18), COMPANY_COL()],
  D.attach_d(), 30, [A('verdict', '= ' + ck('Coach on the offer'), 'warn'), A('verdict', '= ' + ck('On target'), 'good')]))
# 20 replacement ticket by equipment type (2 columns)
tables.append(T('equip_types', 'Equipment Types', 'Average replacement ticket by equipment type', 'The amount billed on one replacement of each equipment type (set your own from your price book); the replacement value of aged equipment reads this sheet.',
  [C('type', 'Type', 'text', 16, required=True), C('replace_ticket', 'Replacement ticket', 'money', 12)], D.equip_types_d(), 12))
for _t in tables: _t['rows'] = max(50, _t['rows'])
assert len(tables) == 20, len(tables)
