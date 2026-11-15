"""Home care agency suite part 6: settings and the 20 tables."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hc6_lists import *
import hc6_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def STAFF(idx, k): return CA(k, 'Phone to message', 'text', 'IFERROR(INDEX({range:team.phone},%d)&"","")' % idx, 18)
YES = '{list:yesno.yes}'
MS_ = 'DATE(YEAR({today}),MONTH({today}),1)'

settings = [
    S('company', 'Your agency name', 'text', COMPANY),
    S('call_days', 'Days within which a new applicant gets a first call (target)', 'int', 3),
    S('renewal_warn_days', 'Days before expiry when a credential turns amber (example)', 'int', 60),
    S('renewal_red_days', 'Days before expiry when a credential turns red (example)', 'int', 30),
    S('turnover_flag', 'Annual turnover above this share is flagged (example)', 'pct', 0.30),
    S('first90_target', 'Share of new caregivers lost in 90 days (target)', 'pct', 0.10),
    S('hire_ad_cost', 'Advert cost for one vacancy (example)', 'money', 180),
    S('background_check_cost', 'Background check cost per applicant (example, use your own)', 'money', 45),
    S('onboard_hours', 'Paid onboarding training hours for a new caregiver (example)', 'int', 16),
    S('training_pay_rate', 'Pay per hour while a caregiver trains (example)', 'money', 18.5),
    S('payroll_burden', 'Payroll burden on pay (example, confirm with adviser)', 'pct', PAYROLL_BURDEN),
    S('hours_per_caregiver', 'Hours a week one caregiver usually takes', 'int', 24),
    S('margin_hour', 'Gross margin per care hour (example)', 'money', 12),
    S('weeks_to_full', 'Weeks until a new caregiver reaches full hours', 'int', 4),
    S('ramp_loss_share', 'Share of margin lost while a new caregiver ramps up', 'pct', 0.5),
    S('referral_bonus', 'Referral bonus per new caregiver (example)', 'money', 250),
    S('bonus_days', 'Days a new caregiver stays before the bonus is due', 'int', 90),
    S('days_to_start_target', 'Days from applying to the first day (target)', 'int', 25),
    S('pay_low', 'Lowest hourly pay in a job advertisement (example)', 'money', 16.5),
    S('pay_high', 'Highest hourly pay in a job advertisement (example)', 'money', 21.5)]
assert 3 <= len(settings) <= 20

tables = []
# 1 applicants
tables.append(T('applicants', 'Applicants', 'Applicants with source, call speed and days to start',
    'One row per applicant: source and stage dates; days to call, days to start, stage reached and the call check fill in. A one-person agency can use it for first hires.', [
    C('applicant_id', 'Applicant ID', 'text', 11, required=True), C('applied_on', 'Applied on', 'date', 11), C('name', 'Name', 'text', 24), C('phone', 'Phone', 'text', 18), LST('source', 'Source', 'recsrc', 18),
    C('phone_screen_on', 'Phone screen on', 'date', 12), C('interview_on', 'Interview on', 'date', 12), C('offer_on', 'Offer on', 'date', 11), C('start_on', 'Start on', 'date', 11), LST('status', 'Status', 'applst', 13),
    LST('reason', 'Reason', 'applrsn', 17), C('caregiver_id', 'Caregiver ID', 'text', 11),
    CA('days_to_call', 'Days to first call', 'int', 'IF({col:phone_screen_on}="","",{col:phone_screen_on}-{col:applied_on})', 10),
    CA('days_to_start', 'Days to start', 'int', 'IF(AND({col:status}=%s,{col:start_on}<>""),{col:start_on}-{col:applied_on},"")' % tok('applst', 'Started'), 10),
    CA('stage', 'Stage reached', 'text', 'IF(AND({col:status}=%s,{col:start_on}<>""),%s,IF({col:offer_on}<>"",%s,IF({col:interview_on}<>"",%s,IF({col:phone_screen_on}<>"",%s,%s))))' % (
        tok('applst', 'Started'), ck('Started'), ck('Offered'), ck('Interviewed'), ck('Screened'), ck('Applied only')), 13),
    CA('wait_check', 'Call check', 'text', 'IF({col:phone_screen_on}<>"",%s,IF(OR({col:status}=%s,{col:status}=%s),%s,IF({today}-{col:applied_on}>{set:call_days},%s,%s)))' % (
        ck('Called'), tok('applst', 'Withdrawn'), tok('applst', 'Not selected'), ck('Closed'), ck('Call overdue'), ck('Within 3 days')), 14),
    CA('call_by', 'Call by', 'date', '{col:applied_on}+{set:call_days}', 11),
    CA('waiting_count', 'Waiting for a call', 'int', 'COUNTIFS({range:applicants.wait_check},%s)+COUNTIFS({range:applicants.wait_check},%s)' % (ck('Call overdue'), ck('Within 3 days')), 10), STAFF(4, 'recruiter_phone')],
    D.applicants_d(), 1200, [A('wait_check', '= ' + ck('Call overdue'), 'bad'), A('status', '= ' + tok('applst', 'Started'), 'good'), A('status', '= ' + tok('applst', 'Offer'), 'warn')]))
# 2 funnel
tables.append(T('funnel', 'Recruiting Funnel', 'Recruiting funnel by month with conversion at each step',
    'One row per month of applications: applicants, phone screens, interviews, offers and starts; the conversion at each step and applicants per start fill in by themselves.', [
    C('funnel_id', 'Funnel ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('applicants', 'Applicants', 'int', 10), C('phone_screens', 'Phone screens', 'int', 11), C('interviews', 'Interviews', 'int', 10),
    C('offers', 'Offers', 'int', 8), C('starts', 'Starts', 'int', 8),
    CA('screen_rate', 'Screened', 'pct', 'IF({col:applicants}=0,"",{col:phone_screens}/{col:applicants})', 10),
    CA('interview_rate', 'Interviewed', 'pct', 'IF({col:phone_screens}=0,"",{col:interviews}/{col:phone_screens})', 11),
    CA('offer_rate', 'Offered', 'pct', 'IF({col:interviews}=0,"",{col:offers}/{col:interviews})', 10),
    CA('start_rate', 'Started', 'pct', 'IF({col:offers}=0,"",{col:starts}/{col:offers})', 10),
    CA('per_start', 'Applicants per start', 'num', 'IF({col:starts}=0,"",{col:applicants}/{col:starts})', 11)], D.funnel_d(), 60,
    [A('per_start', '> 12', 'warn')]))
# 3 sources
tables.append(T('sources', 'Source by Month', 'Applicants, starts and 90-day retention by source',
    'One row per source and month: applicants, starts, caregivers still active after 90 days and the advert cost; cost per start and the retention share fill in by themselves.', [
    C('source_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('source', 'Source', 'recsrc', 18), C('applicants', 'Applicants', 'int', 10), C('starts', 'Starts', 'int', 8),
    C('active_90', 'Active after 90 days', 'int', 11), C('cost', 'Cost', 'money', 11),
    CA('cost_per_start', 'Cost per start', 'money', 'IF({col:starts}=0,"",{col:cost}/{col:starts})', 11), CA('retention', 'Retention', 'pct', 'IF({col:starts}=0,"",{col:active_90}/{col:starts})', 10),
    STAFF(1, 'owner_phone')], D.sources_d(), 400, [A('retention', '< 0.5', 'warn')]))
# 4 screens
tables.append(T('screens', 'Screens and Interviews', 'Phone screens and interviews with result and minutes',
    'One row per phone screen or interview: who did it, the result and the minutes; the applicant name and the days after applying fill in by themselves.', [
    C('screen_id', 'Screen ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('applicant_id', 'Applicant ID', 'text', 11), LST('kind', 'Kind', 'kind', 13), REF('done_by', 'Done by', 'team.name', 20),
    LST('result', 'Result', 'outcome', 13), C('minutes', 'Minutes', 'int', 9),
    CA('name', 'Applicant', 'text', LKT('applicants.name', 'applicants.applicant_id', 'applicant_id'), 24),
    CA('days_after', 'Days after applying', 'int', 'IFERROR({col:date}-INDEX({range:applicants.applied_on},MATCH({col:applicant_id},{range:applicants.applicant_id},0)),"")', 10)], D.screens_d(), 600,
    [A('result', '= ' + tok('outcome', 'Not selected'), 'warn'), A('result', '= ' + tok('outcome', 'Pass'), 'good')]))
# 5 offers
tables.append(T('offers', 'Offers', 'Offers with answer, days to answer and days to start',
    'One row per offer: pay, hours, answer and start date; the name, phone, days to answer, days to start and days open fill in by themselves.', [
    C('offer_id', 'Offer ID', 'text', 9, required=True), C('offer_on', 'Offer on', 'date', 11), C('applicant_id', 'Applicant ID', 'text', 11), LST('answer', 'Answer', 'outcome', 12), C('answered_on', 'Answered on', 'date', 12),
    C('start_on', 'Start on', 'date', 11), C('pay_rate', 'Pay per hour', 'money', 11), C('hours_week', 'Hours a week', 'int', 10),
    CA('name', 'Applicant', 'text', LKT('applicants.name', 'applicants.applicant_id', 'applicant_id'), 24), CA('phone', 'Phone', 'text', LKT('applicants.phone', 'applicants.applicant_id', 'applicant_id'), 18),
    CA('days_to_answer', 'Days to answer', 'int', 'IF({col:answered_on}="","",{col:answered_on}-{col:offer_on})', 10), CA('days_to_start', 'Days to start', 'int', 'IF({col:start_on}="","",{col:start_on}-{col:offer_on})', 10),
    CA('days_open', 'Days open', 'int', 'IF({col:answer}=%s,{today}-{col:offer_on},"")' % tok('outcome', 'Waiting'), 9), STAFF(4, 'recruiter_phone')], D.offers_d(), 300,
    [A('answer', '= ' + tok('outcome', 'Declined'), 'warn'), A('answer', '= ' + tok('outcome', 'Accepted'), 'good'), A('days_open', '> 3', 'bad')]))
# 6 onboarding
tables.append(T('onboarding', 'Onboarding', 'Onboarding with the ready-for-first-shift flag',
    'One row per new caregiver: five checks and the first shift; steps done, Ready or Blocked, days to ready and next due fill in. The schedule reads it.', [
    C('onboarding_id', 'Onboarding ID', 'text', 11, required=True), C('person', 'Person', 'text', 24), C('caregiver_id', 'Caregiver ID', 'text', 11), C('start_date', 'Start date', 'date', 11), C('identity_check_on', 'Identity check on', 'date', 12),
    C('references_on', 'References on', 'date', 12), C('background_check_on', 'Background check on', 'date', 12), C('training_on', 'Training on', 'date', 11), C('agreement_signed_on', 'Agreement signed on', 'date', 12),
    C('first_shift_on', 'First shift on', 'date', 12), REF('owner', 'Owner', 'team.name', 20),
    CA('steps_done', 'Steps done', 'int', 'COUNT({col:identity_check_on},{col:references_on},{col:background_check_on},{col:training_on},{col:agreement_signed_on})', 9),
    CA('steps_missing', 'Steps missing', 'int', '5-COUNT({col:identity_check_on},{col:references_on},{col:background_check_on},{col:training_on},{col:agreement_signed_on})', 9),
    CA('ready_check', 'Ready for first shift', 'text', 'IF({col:steps_missing}=0,%s,%s)' % (ck('Ready'), ck('Blocked')), 12),
    CA('days_to_ready', 'Days to ready', 'int', 'IF({col:steps_missing}=0,MAX({col:identity_check_on},{col:references_on},{col:background_check_on},{col:training_on},{col:agreement_signed_on})-MIN({col:identity_check_on},{col:references_on},{col:background_check_on},{col:training_on},{col:agreement_signed_on}),"")', 9),
    CA('next_due', 'Next step due', 'date', 'IFERROR(IF(SUMPRODUCT(MIN(({range:steps.person}={col:person})*({range:steps.done_on}="")*{range:steps.due_date}+(1-({range:steps.person}={col:person})*({range:steps.done_on}=""))*99999))>=99999,"",SUMPRODUCT(MIN(({range:steps.person}={col:person})*({range:steps.done_on}="")*{range:steps.due_date}+(1-({range:steps.person}={col:person})*({range:steps.done_on}=""))*99999))),"")', 11),
    CA('checkin_on', '90-day check-in', 'date', '{col:start_date}+90', 11),
    CA('checks_needed', 'Background checks to run', 'int', 'COUNT({range:onboarding.start_date})-COUNT({range:onboarding.background_check_on})', 10),
    CA('phone', 'Phone', 'text', LKT('applicants.phone', 'applicants.name', 'person'), 18), STAFF(4, 'recruiter_phone'), STAFF(2, 'scheduler_phone'), STAFF(10, 'bg_phone')], D.onboarding_d(), 80,
    [A('ready_check', '= ' + ck('Blocked'), 'bad'), A('ready_check', '= ' + ck('Ready'), 'good')]))
# 7 steps
tables.append(T('steps', 'Onboarding Steps', 'Onboarding steps with due dates and the overdue flag',
    'One row per onboarding step of a person: the step, its due date and the day it was done; Done, Open or Overdue and days late fill in by themselves.', [
    C('step_id', 'Step ID', 'text', 9, required=True), REF('person', 'Person', 'onboarding.person', 24), LST('step', 'Step', 'step', 16), C('due_date', 'Due date', 'date', 11), C('done_on', 'Done on', 'date', 11),
    CA('overdue_check', 'Step check', 'text', 'IF({col:done_on}<>"",%s,IF({col:due_date}<{today},%s,%s))' % (ck('Done'), ck('Overdue'), ck('Open')), 11),
    CA('days_late', 'Days late', 'int', 'IF({col:done_on}="","",MAX(0,{col:done_on}-{col:due_date}))', 9)], D.steps_d(), 500,
    [A('overdue_check', '= ' + ck('Overdue'), 'bad'), A('overdue_check', '= ' + ck('Done'), 'good')]))
# 8 credentials
tables.append(T('credentials', 'Credentials', 'Credential register with 60 and 30-day colours',
    'One row per credential record: type, issue, expiry and renewal; days left, the red, amber or green colour and the date after which the caregiver cannot be scheduled fill in by themselves.', [
    C('credential_id', 'Credential ID', 'text', 11, required=True), REF('caregiver', 'Caregiver', 'caregivers.name', 24), LST('credential', 'Credential', 'cred', 20), C('issued_on', 'Issued on', 'date', 11), C('expires_on', 'Expires on', 'date', 11),
    C('renewed_on', 'Renewed on', 'date', 11), LST('status', 'Status', 'credst', 10), C('reminder_sent', 'Reminder sent', 'bool', 9),
    CA('days_left', 'Days left', 'int', 'IF({col:status}=%s,"",{col:expires_on}-{today})' % tok('credst', 'Renewed'), 9),
    CA('colour', 'Colour', 'text', 'IF({col:status}=%s,%s,IF({col:expires_on}<{today},%s,IF({col:expires_on}-{today}<={set:renewal_red_days},%s,IF({col:expires_on}-{today}<={set:renewal_warn_days},%s,%s))))' % (
        tok('credst', 'Renewed'), ck('Closed'), ck('Expired'), ck('Red zone'), ck('Amber zone'), ck('Green')), 12),
    CA('cannot_schedule', 'Cannot be scheduled from', 'date', 'IF({col:status}=%s,"",{col:expires_on}+1)' % tok('credst', 'Renewed'), 12),
    CA('phone', 'Phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'caregiver'), 18)], D.credentials_d(), 500,
    [A('colour', '= ' + ck('Red zone'), 'bad'), A('colour', '= ' + ck('Expired'), 'bad'), A('colour', '= ' + ck('Amber zone'), 'warn'), A('colour', '= ' + ck('Green'), 'good')]))
# 9 credential types
tables.append(T('credtypes', 'Credential Types', 'Credential types and how often they renew',
    'One row per credential type: how many months it lasts and who needs it. Edit the months to match your own rules.', [
    LST('credential', 'Credential', 'cred', 22, required=True), C('renew_months', 'Renew every (months)', 'int', 14), C('required_for', 'Required for', 'text', 22)], D.credtypes_d(), 50))
# 10 renewals
tables.append(T('renewals', 'Renewals Due', 'Renewals due with course booking and visits at risk',
    'One row per credential coming up for renewal: when the course is booked; days left, the colour, visits scheduled after expiry and the date to renew by fill in by themselves.', [
    C('renewal_id', 'Renewal ID', 'text', 10, required=True), REF('caregiver', 'Caregiver', 'caregivers.name', 24), LST('credential', 'Credential', 'cred', 20), C('expires_on', 'Expires on', 'date', 11), C('booked_on', 'Booked on', 'date', 11),
    C('course_date', 'Course date', 'date', 11),
    CA('days_left', 'Days left', 'int', '{col:expires_on}-{today}', 9),
    CA('colour', 'Colour', 'text', 'IF({col:expires_on}<{today},%s,IF({col:expires_on}-{today}<={set:renewal_red_days},%s,IF({col:expires_on}-{today}<={set:renewal_warn_days},%s,%s)))' % (ck('Expired'), ck('Red zone'), ck('Amber zone'), ck('Green')), 12),
    CA('booking_check', 'Booking', 'text', 'IF({col:booked_on}<>"",%s,%s)' % (ck('Booked'), ck('Not booked')), 11),
    CA('visits_at_risk', 'Visits after expiry', 'int', 'COUNTIFS({range:visitsafter.caregiver},{col:caregiver},{range:visitsafter.credential},{col:credential})', 10),
    CA('renew_by', 'Renew by', 'date', 'MIN({col:expires_on},MAX({today},{col:expires_on}-{set:renewal_red_days}))', 11),
    CA('same_course', 'People due, same credential', 'int', 'COUNTIFS({range:renewals.credential},{col:credential})', 10),
    CA('phone', 'Phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'caregiver'), 18), STAFF(2, 'scheduler_phone'), STAFF(11, 'training_phone')], D.renewals_d(), 200,
    [A('colour', '= ' + ck('Red zone'), 'bad'), A('colour', '= ' + ck('Amber zone'), 'warn'), A('booking_check', '= ' + ck('Booked'), 'good')]))
# 11 caregivers
tables.append(T('caregivers', 'Caregivers', 'Caregivers with hire date, source and leaving reason',
    'One row per caregiver, current or past: employment, area, status and where they were recruited; leavers keep their left date and reason. Other pages read this list.', [
    C('caregiver_id', 'Caregiver ID', 'text', 11, required=True), C('name', 'Name', 'text', 24), C('hire_date', 'Hire date', 'date', 11), LST('employment', 'Employment', 'emp', 12), LST('area', 'Area', 'area', 13),
    LST('status', 'Status', 'cgstatus', 11), C('left_date', 'Left date', 'date', 11), LST('leave_reason', 'Leaving reason', 'leave', 19), LST('source', 'Source', 'recsrc', 18), C('pay_rate', 'Pay per hour', 'money', 11), C('phone', 'Phone', 'text', 18),
    CA('hired_12m', 'Hired in 12 months', 'int', 'COUNTIFS({range:caregivers.hire_date},">="&({today}-365),{range:caregivers.hire_date},"<="&{today})', 10), STAFF(9, 'broker_phone')], D.caregivers_d(), 120,
    [A('status', '= ' + tok('cgstatus', 'Left'), 'warn')]))
# 12 leavers
tables.append(T('leavers', 'Leavers', 'Leavers with tenure and tenure band',
    'One row per caregiver who left: hire and left dates, the reason and the source; tenure in days and the band (first 90 days, 4 to 12 months, over 1 year) fill in by themselves.', [
    C('leaver_id', 'Leaver ID', 'text', 9, required=True), C('caregiver', 'Caregiver', 'text', 24), C('hire_date', 'Hire date', 'date', 11), C('left_date', 'Left date', 'date', 11), LST('reason', 'Reason', 'leave', 19), LST('source', 'Source', 'recsrc', 18),
    CA('tenure_days', 'Tenure (days)', 'int', '{col:left_date}-{col:hire_date}', 10),
    CA('tenure_band', 'Tenure band', 'text', 'IF({col:tenure_days}<=90,%s,IF({col:tenure_days}<=365,%s,%s))' % (ck('First 90 days'), ck('From 4 to 12 months'), ck('Over 1 year')), 14),
    CA('phone', 'Phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'caregiver'), 18)], D.leavers_d(), 60,
    [A('tenure_band', '= ' + ck('First 90 days'), 'bad')]))
# 13 turnover
tables.append(T('turnover', 'Turnover by Month', 'Turnover by month with the trailing 12-month rate',
    'One row per month: caregivers at the start, hires, leavers and first-90-day leavers; the month rate, the trailing 12-month rate against your flag and the year to date fill in by themselves.', [
    C('turn_id', 'Row ID', 'text', 8, required=True), C('month', 'Month', 'date', 11), C('caregivers_start', 'Caregivers at start', 'int', 11), C('hires', 'Hires', 'int', 8), C('leavers', 'Leavers', 'int', 9), C('first90', 'First-90-day leavers', 'int', 11),
    CA('caregivers_end', 'Caregivers at end', 'int', '{col:caregivers_start}+{col:hires}-{col:leavers}', 10),
    CA('turnover_rate', 'Turnover in the month', 'pct', 'IF({col:caregivers_start}=0,"",{col:leavers}/(({col:caregivers_start}+{col:caregivers_end})/2))', 10),
    CA('trail12', 'Turnover, trailing 12 months', 'pct', 'IF(COUNTIFS({range:turnover.month},"<="&{col:month})>=12,IFERROR(SUMIFS({range:turnover.leavers},{range:turnover.month},">"&DATE(YEAR({col:month}),MONTH({col:month})-12,1),{range:turnover.month},"<="&{col:month})/AVERAGEIFS({range:turnover.caregivers_start},{range:turnover.month},">"&DATE(YEAR({col:month}),MONTH({col:month})-12,1),{range:turnover.month},"<="&{col:month}),""),"")', 11),
    CA('turnover_pct', 'Turnover percent', 'num', 'IF({col:trail12}="","",ROUND({col:trail12}*100,1))', 10),
    CA('first90_year', 'First-90-day leavers this year', 'int', 'SUMIFS({range:turnover.first90},{range:turnover.month},">="&DATE(YEAR({col:month}),1,1),{range:turnover.month},"<="&{col:month})', 11), STAFF(1, 'owner_phone')], D.turnover_d(), 60,
    [A('trail12', '> {set:turnover_flag}', 'bad')]))
# 14 hiring cost
tables.append(T('hirecost', 'Hiring Cost Log', 'Hiring cost log with cost per hire',
    'One row per person who cost money to recruit: advert, background check, paid training hours and other cost; the training cost, total and cost per hire (hired people only) fill in by themselves.', [
    C('cost_id', 'Cost ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('person', 'Person', 'text', 24), C('hired', 'Hired', 'bool', 8), C('advert_cost', 'Advert cost', 'money', 11), C('check_cost', 'Background check', 'money', 11),
    C('training_hours', 'Paid training hours', 'num', 10), C('other_cost', 'Other cost', 'money', 11),
    CA('training_cost', 'Training cost', 'money', '{col:training_hours}*{set:training_pay_rate}*(1+{set:payroll_burden})', 11),
    CA('total_cost', 'Total cost', 'money', '{col:advert_cost}+{col:check_cost}+{col:other_cost}+{col:training_hours}*{set:training_pay_rate}*(1+{set:payroll_burden})', 11),
    CA('cost_per_hire', 'Cost per hire', 'money', 'IF({col:hired}=%s,{col:total_cost},"")' % YES, 11),
    CA('year_cost', 'Cost this year', 'money', 'SUMIFS({range:hirecost.total_cost},{range:hirecost.month},">="&DATE(YEAR({today}),1,1),{range:hirecost.month},"<="&{today})', 11), STAFF(7, 'accountant_phone')], D.hirecost_d(), 200,
    [A('cost_per_hire', '> 700', 'warn')]))
# 15 training
tables.append(T('training', 'Training Sessions', 'Training sessions with hours and cost',
    'One row per course a caregiver attended: course, hours, provider, whether the hours were paid and any fee; the training cost fills in by themselves.', [
    C('training_id', 'Training ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('caregiver', 'Caregiver', 'caregivers.name', 24), LST('course', 'Course', 'course', 20), C('hours', 'Hours', 'num', 8),
    C('provider', 'Provider', 'text', 18), C('paid', 'Paid hours', 'bool', 9), C('fee', 'Course fee', 'money', 11),
    CA('training_cost', 'Training cost', 'money', '{col:fee}+IF({col:paid}=%s,{col:hours}*{set:training_pay_rate}*(1+{set:payroll_burden}),0)' % YES, 11),
    CA('phone', 'Phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'caregiver'), 18)], D.training_d(), 400))
# 16 hire planning
tables.append(T('hireplan', 'Hire Planning by Week', 'Hire planning by week: hours waiting for a caregiver',
    'One row per week: visit hours without a planned caregiver (cover or still open) and the free caregiver hours that fit them; the gap in hours and the caregivers needed fill in by themselves.', [
    C('plan_id', 'Plan ID', 'text', 8, required=True), C('week', 'Week (Monday)', 'date', 12), C('hours_waiting', 'Hours waiting for a caregiver', 'num', 12), C('free_hours', 'Free caregiver hours that fit', 'num', 12),
    CA('gap_hours', 'Gap in hours', 'num', 'MAX(0,{col:hours_waiting}-{col:free_hours})', 10), CA('caregivers_needed', 'Caregivers needed', 'num', 'ROUND({col:gap_hours}/{set:hours_per_caregiver},2)', 10), STAFF(1, 'owner_phone')],
    D.hireplan_d(), 80, [A('gap_hours', '> {set:hours_per_caregiver}', 'bad')]))
# 17 campaigns
tables.append(T('campaigns', 'Recruiting Campaigns', 'Recruiting campaigns with cost per applicant',
    'One row per recruiting campaign: kind, area, hours offered, cost, applicants and starts; cost per applicant fills in by themselves. The job advertisement is filled from a row.', [
    C('campaign_id', 'Campaign ID', 'text', 11, required=True), C('month', 'Month', 'date', 11), LST('kind', 'Kind', 'mkind', 17), LST('area', 'Area', 'area', 13), C('hours_week', 'Hours a week offered', 'int', 11), C('cost', 'Cost', 'money', 11),
    C('applicants', 'Applicants', 'int', 10), C('starts', 'Starts', 'int', 8), CA('cost_per_applicant', 'Cost per applicant', 'money', 'IF({col:applicants}=0,"",{col:cost}/{col:applicants})', 11)], D.campaigns_d(), 120))
# 18 referrals
tables.append(T('referrals', 'Referral Bonuses', 'Referral bonuses with the 90-day date and due flag',
    'One row per caregiver referral: who referred, the new caregiver, hire date, bonus and the day it was paid; the 90-day date and Due now, Not due yet, Paid or Left early fill in by themselves.', [
    C('referral_id', 'Referral ID', 'text', 10, required=True), REF('referring', 'Referring caregiver', 'caregivers.name', 24), C('new_caregiver', 'New caregiver', 'text', 24), C('hire_date', 'Hire date', 'date', 11), C('amount', 'Bonus amount', 'money', 11),
    C('paid_on', 'Paid on', 'date', 11),
    CA('ninety_day', '90-day date', 'date', 'IF({col:hire_date}="","",{col:hire_date}+{set:bonus_days})', 11),
    CA('left_date', 'Left on', 'date', LKD('caregivers.left_date', 'caregivers.name', 'new_caregiver'), 11),
    CA('due_flag', 'Bonus check', 'text', 'IF({col:hire_date}="",%s,IF({col:paid_on}<>"",%s,IF(AND({col:left_date}<>"",{col:left_date}<{col:ninety_day}),%s,IF({today}>={col:ninety_day},%s,%s))))' % (ck('No hire yet'), ck('Paid'), ck('Left early'), ck('Due now'), ck('Not due yet')), 12),
    CA('phone', 'Phone', 'text', LKT('caregivers.phone', 'caregivers.name', 'referring'), 18)], D.referrals_d(), 80,
    [A('due_flag', '= ' + ck('Due now'), 'bad'), A('due_flag', '= ' + ck('Paid'), 'good')]))
# 19 visits after expiry
tables.append(T('visitsafter', 'Visits After Expiry', 'Scheduled visits after a credential expires',
    'One row per visit that falls after a credential expires: client, date and hours; expiry date and days after expiry fill in. Move them or renew first.', [
    C('item_id', 'Item ID', 'text', 9, required=True), LST('credential', 'Credential', 'cred', 20), REF('caregiver', 'Caregiver', 'caregivers.name', 24), C('date', 'Date', 'date', 11), C('client', 'Client', 'text', 24), C('hours', 'Hours', 'num', 8),
    C('basis', 'Basis', 'text', 22),
    CA('expires_on', 'Expires on', 'date', 'IF(SUMIFS({range:renewals.expires_on},{range:renewals.caregiver},{col:caregiver},{range:renewals.credential},{col:credential})=0,"",SUMIFS({range:renewals.expires_on},{range:renewals.caregiver},{col:caregiver},{range:renewals.credential},{col:credential}))', 11),
    CA('days_after', 'Days after expiry', 'int', 'IF({col:expires_on}="","",{col:date}-{col:expires_on})', 10)], D.visitsafter_d(), 200, [A('days_after', '> 0', 'bad')]))
# 20 team
tables.append(T('team', 'Team', 'Team and outside contacts',
    'One row per staff member and outside contact: role, phone and pay type. Other pages look up phones here.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 18), LST('team', 'Team', 'team', 11), LST('pay_type', 'Pay type', 'paytype', 12), C('phone', 'Phone', 'text', 18),
    C('email', 'Email', 'text', 26), C('hours_week', 'Hours a week', 'int', 10), C('monthly_salary', 'Monthly salary', 'num', 12), C('hourly_rate', 'Hourly rate', 'num', 11), C('speciality', 'Speciality', 'text', 30),
    C('country', 'Country', 'text', 14), C('start', 'Start', 'date', 11)], D.team_d(), 50))
assert len(tables) == 20
