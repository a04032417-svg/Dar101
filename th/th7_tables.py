"""Therapy practice suite part 7: settings and the 20 tables."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th7_lists import *
import th7_data as D

def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def OWNER_PH(): return CA('owner_phone', 'Owner phone', 'text', 'IFERROR(INDEX({range:team.phone},1)&"","")', 18)
def COORD_PH(): return CA('coordinator_phone', 'Coordinator phone', 'text', 'IFERROR(INDEX({range:team.phone},7)&"","")', 18)
def COMPCOL(): return CA('company', 'Practice', 'text', '{set:company}&""', 24)
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
M0 = 'DATE(YEAR({today}),MONTH({today}),1)'
S12 = 'DATE(YEAR({today}),MONTH({today})-11,1)'
CAN = tok('grpst', 'Cancelled')
REFSRC = [tok('src', s) for s in ('Doctor referral', 'School referral', 'Other clinician', 'Employer program')]

settings = [
    S('company', 'Your practice name', 'text', COMPANY),
    S('target_conv', 'Wanted share of enquiries that become bookings', 'pct', 0.5),
    S('contact_days', 'Days between contacts with a referrer', 'int', 90),
    S('avg_charge', 'Average charge per session', 'money', 105),
    S('margin_pct', 'Share of a charge left after pay, room and admin', 'pct', 0.4),
    S('client_sessions_month', 'Sessions a client has in a month', 'num', 2),
    S('max_cost_client', 'Most you accept to pay to win one client', 'money', 150),
    S('max_payback_months', 'Most months you accept to pay back a directory listing', 'num', 4),
    S('room_cost_hour', 'Rent, cleaning and power per hour of room time', 'money', 12),
    S('meeting_hours', 'Hours of one group meeting', 'num', 1.5),
    S('min_group_fill', 'Wanted minimum group fill rate (share of places)', 'pct', 0.6),
    S('group_margin_target', 'Wanted profit share of group fees', 'pct', 0.3),
    S('min_attendance', 'Wanted attendance at group meetings', 'pct', 0.75),
    S('target_rating', 'Wanted average feedback score (1 to 10)', 'num', 8.5),
    S('target_recommend', 'Wanted share of clients who would recommend', 'pct', 0.85)]
assert 3 <= len(settings) <= 20

# next group: earliest start date after today that is not cancelled
FUT = '({range:groups.start_date}>{today})*({range:groups.status}<>%s)' % CAN
NEXTMIN = 'SUMPRODUCT(MIN(%s*{range:groups.start_date}+(1-%s)*99999))' % (FUT, FUT)
def NEXTPROG(p):
    f = '({range:groups.program}=%s)*%s' % (p, FUT)
    return 'SUMPRODUCT(MIN(%s*{range:groups.start_date}+(1-%s)*99999))' % (f, f)
WIN12 = '{range:referrallog.date},">="&({today}-365),{range:referrallog.date},"<="&{today}'

tables = []
tables.append(T('enquiries', 'Enquiries by Source', 'Enquiries by referral source with booked flag',
    'One row per enquiry with its source and referrer: client type, service, status and first session; the booked flag and the days to the first session fill in by themselves.', [
    C('enquiry_id', 'Enquiry ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), LST('source', 'Referral source', 'src', 17), C('referrer', 'Referrer', 'text', 22), LST('service', 'Service', 'svc', 18),
    LST('client_type', 'Client type', 'ctype', 12), LST('status', 'Status', 'enqst', 17), C('first_session', 'First session', 'date', 12),
    CA('booked', 'Booked (1 = yes)', 'int', 'IF({col:status}=%s,1,0)' % tok('enqst', 'Booked'), 9),
    CA('days_to_first', 'Days to first session', 'int', 'IF({col:first_session}="","",{col:first_session}-{col:date})', 10)], D.enquiries_d(), 1200,
    [A('status', '= ' + tok('enqst', 'Booked'), 'good'), A('status', '= ' + tok('enqst', 'No reply'), 'warn')]))
tables.append(T('sourcemonths', 'Source Performance by Month', 'Source performance by month',
    'One row per month and referral source: enquiries, booked clients and revenue; booked share, value per enquiry and per client, and each source\'s value over the last 12 months fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('source', 'Referral source', 'src', 17), C('enquiries', 'Enquiries', 'int', 10), C('booked', 'Booked clients', 'int', 10),
    C('revenue', 'Revenue', 'int', 11),
    CA('booked_share', 'Booked share, %', 'pct', 'IF({col:enquiries}>0,{col:booked}/{col:enquiries},0)', 10),
    CA('value_per_enquiry', 'Value per enquiry', 'money', 'IF({col:enquiries}>0,{col:revenue}/{col:enquiries},"")', 11),
    CA('value_per_client', 'Value per booked client', 'money', 'IF({col:booked}>0,{col:revenue}/{col:booked},"")', 11),
    CA('referral_based', 'Referrer-based source (1 = yes)', 'int', 'IF(OR({col:source}=%s),1,0)' % ',{col:source}='.join(REFSRC), 10),
    CA('val_enq_12m', 'Value per enquiry, last 12 months', 'money', 'IFERROR(SUMIFS({range:sourcemonths.revenue},{range:sourcemonths.source},{col:source},{range:sourcemonths.month},">="&%s)/SUMIFS({range:sourcemonths.enquiries},{range:sourcemonths.source},{col:source},{range:sourcemonths.month},">="&%s),0)' % (S12, S12), 12),
    CA('val_client_12m', 'Value per client, last 12 months', 'money', 'IFERROR(SUMIFS({range:sourcemonths.revenue},{range:sourcemonths.source},{col:source},{range:sourcemonths.month},">="&%s)/SUMIFS({range:sourcemonths.booked},{range:sourcemonths.source},{col:source},{range:sourcemonths.month},">="&%s),0)' % (S12, S12), 12),
    OWNER_PH(), COMPCOL()], D.sourcemonths_d(), 300, [A('booked_share', '< {set:target_conv}', 'warn')]))
tables.append(T('clientvalue', 'Client Value by Source', 'Client value by source: sessions and revenue per client',
    'One row per client with the source they came from, sessions attended and revenue so far; revenue per session and a value band (high, average or low against the average client) fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 24), C('phone', 'Phone', 'text', 18), LST('source', 'Referral source', 'src', 17), C('referrer', 'Referrer', 'text', 22),
    C('first_session', 'First session', 'date', 12), C('sessions_attended', 'Sessions attended', 'int', 10), C('revenue', 'Revenue', 'int', 11),
    CA('revenue_per_session', 'Revenue per session', 'money', 'IF({col:sessions_attended}>0,{col:revenue}/{col:sessions_attended},0)', 11),
    CA('value_band', 'Value band', 'text', 'IF({col:revenue}>=1.5*AVERAGE({range:clientvalue.revenue}),%s,IF({col:revenue}<0.5*AVERAGE({range:clientvalue.revenue}),%s,%s))' % (ck('High value'), ck('Low value'), ck('Average value')), 14),
    COMPCOL()], D.clientvalue_d(), 600, [A('value_band', '= ' + ck('High value'), 'good'), A('value_band', '= ' + ck('Low value'), 'warn')]))
tables.append(T('referrers', 'Referrers', 'Referrers with 12-month referrals, value and contact rhythm',
    'One row per named referrer (doctor, school, clinician, employer, community); 12-month referrals, value, last contact and act-first rank fill in by themselves.', [
    C('referrer_id', 'Referrer ID', 'text', 10, required=True), C('name', 'Name', 'text', 24), LST('kind', 'Kind', 'rkind', 16), C('phone', 'Phone', 'text', 18), C('email', 'Email', 'text', 26),
    CA('referrals_12m', 'Referrals, last 12 months', 'int', 'COUNTIFS({range:referrallog.referrer},{col:name},%s)' % WIN12, 11),
    CA('booked_12m', 'Booked, last 12 months', 'int', 'COUNTIFS({range:referrallog.referrer},{col:name},%s,{range:referrallog.outcome},%s)' % (WIN12, tok('enqst', 'Booked')), 11),
    CA('value_12m', 'Value, last 12 months', 'money', 'ROUND({col:booked_12m}*AVERAGE({range:clientvalue.revenue}),0)', 11),
    CA('last_contact', 'Last contact', 'date', 'IFERROR(IF(SUMPRODUCT(MAX(({range:contacts.referrer}={col:name})*{range:contacts.date}))=0,"",SUMPRODUCT(MAX(({range:contacts.referrer}={col:name})*{range:contacts.date}))),"")', 12),
    CA('days_since', 'Days since last contact', 'int', 'IF({col:last_contact}="","",{today}-{col:last_contact})', 10),
    CA('contact_check', 'Contact check', 'text', 'IF({col:days_since}="",%s,IF({col:days_since}>{set:contact_days},%s,%s))' % (ck('No contact yet'), ck('Contact due'), ck('On rhythm')), 14),
    CA('next_contact', 'Next contact by', 'date', 'IF({col:last_contact}="",{today},{col:last_contact}+{set:contact_days})', 12),
    CA('act_score', 'Act-first score', 'num', 'IF({col:days_since}="",0,IF({col:days_since}>{set:contact_days},{col:value_12m}+{col:days_since}/1000+1,0))', 10),
    CA('act_rank', 'Contact first (rank)', 'int', 'IF({col:act_score}>0,1+COUNTIFS({range:referrers.act_score},">"&{col:act_score}),"")', 10),
    CA('program', 'Next group program', 'text', 'IFERROR(INDEX({range:groups.program},MATCH(1,{range:groups.next_flag},0))&"","")', 18),
    CA('start_date', 'Next group start', 'date', 'IFERROR(INDEX({range:groups.start_date},MATCH(1,{range:groups.next_flag},0)),"")', 12),
    COMPCOL(), COORD_PH()], D.referrers_d(), 60, [A('contact_check', '= ' + ck('Contact due'), 'bad'), A('act_rank', '<= 3', 'warn')]))
tables.append(T('referrallog', 'Referral Log', 'Referral log: who referred and the outcome',
    'One row per referral received from a named referrer: service, client type and outcome; days to the first session and a booked flag fill in by themselves. Never record client details beyond receipt.', [
    C('log_id', 'Log ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), REF('referrer', 'Referrer', 'referrers.name', 22), LST('kind', 'Referrer kind', 'rkind', 16), LST('service', 'Service', 'svc', 18),
    LST('client_type', 'Client type', 'ctype', 12), LST('outcome', 'Outcome', 'enqst', 17), C('first_session', 'First session', 'date', 12),
    CA('days_to_first', 'Days to first session', 'int', 'IF({col:first_session}="","",{col:first_session}-{col:date})', 10),
    CA('booked', 'Booked (1 = yes)', 'int', 'IF({col:outcome}=%s,1,0)' % tok('enqst', 'Booked'), 9)], D.referrallog_d(), 1200,
    [A('outcome', '= ' + tok('enqst', 'Booked'), 'good'), A('outcome', '= ' + tok('enqst', 'No reply'), 'warn')]))
tables.append(T('contacts', 'Referrer Contacts', 'Referrer contacts: visits, calls, emails and thank-you notes',
    'One row per contact with a referrer: kind, who made it and the next contact date; days since and the contact check fill in by themselves.', [
    C('contact_id', 'Contact ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('referrer', 'Referrer', 'referrers.name', 22), LST('contact_kind', 'Contact kind', 'ckind', 16), REF('done_by', 'Done by', 'team.name', 20),
    C('next_contact', 'Next contact', 'date', 12),
    CA('days_since', 'Days since', 'int', '{today}-{col:date}', 9),
    CA('contact_flag', 'Contact check', 'text', 'IF({col:next_contact}="",%s,IF({col:next_contact}<{today},%s,%s))' % (ck('Done'), ck('Contact due'), ck('On rhythm')), 14),
    CA('referrer_phone', 'Referrer phone', 'text', LKT('referrers.phone', 'referrers.name', 'referrer'), 18), COMPCOL()], D.contacts_d(), 300,
    [A('contact_flag', '= ' + ck('Contact due'), 'bad')]))
tables.append(T('campaigns', 'Campaigns', 'Marketing campaigns with cost per enquiry and per client won',
    'One row per marketing activity: kind, cost, enquiries and clients won; cost per enquiry, cost per client won and the check against what you accept to pay fill in by themselves.', [
    C('campaign_id', 'Campaign ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), LST('kind', 'Activity kind', 'mkind', 16), C('description', 'Description', 'text', 30), C('cost', 'Cost', 'money', 11),
    C('enquiries', 'Enquiries', 'int', 10), C('clients_won', 'Clients won', 'int', 10),
    CA('cost_per_enquiry', 'Cost per enquiry', 'money', 'IF({col:enquiries}>0,{col:cost}/{col:enquiries},"")', 11),
    CA('cost_per_client', 'Cost per client won', 'money', 'IF({col:clients_won}>0,{col:cost}/{col:clients_won},"")', 11),
    CA('cost_check', 'Cost check', 'text', 'IF({col:clients_won}=0,%s,IF({col:cost}/{col:clients_won}<={set:max_cost_client},%s,%s))' % (ck('No clients won'), ck('Cost within limit'), ck('Cost over limit')), 15),
    CA('kind_return', 'Clients won per 100 spent, same kind', 'num', 'IFERROR(SUMIFS({range:campaigns.clients_won},{range:campaigns.kind},{col:kind})/SUMIFS({range:campaigns.cost},{range:campaigns.kind},{col:kind})*100,0)', 12),
    OWNER_PH(), COMPCOL()], D.campaigns_d(), 300, [A('cost_check', '= ' + ck('Cost over limit'), 'bad'), A('cost_check', '= ' + ck('No clients won'), 'warn')]))
tables.append(T('budget', 'Marketing Budget', 'Marketing budget by month: spent comes from your campaigns',
    'One row per month: type the budget; the amount spent comes from the Campaigns sheet, then the amount left, the share used and the budget check fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('budget', 'Budget', 'money', 11),
    CA('spent', 'Spent', 'money', 'SUMIFS({range:campaigns.cost},{range:campaigns.date},">="&{col:month},{range:campaigns.date},"<"&DATE(YEAR({col:month}),MONTH({col:month})+1,1))', 11),
    CA('left', 'Left', 'money', '{col:budget}-{col:spent}', 11), CA('yearly_pace', 'Budget for 12 months at this pace', 'money', '12*{col:budget}', 12), CA('used_share', 'Share used, %', 'pct', 'IF({col:budget}>0,{col:spent}/{col:budget},0)', 10),
    CA('budget_check', 'Budget check', 'text', 'IF({col:spent}<={col:budget},%s,%s)' % (ck('Within budget'), ck('Over budget')), 14), OWNER_PH(), COMPCOL()], D.budget_d(), 60,
    [A('budget_check', '= ' + ck('Over budget'), 'bad')]))
tables.append(T('directory', 'Directory Listings', 'Directory listings: cost, views and clients won',
    'One row per month and online directory listing: cost, profile views, enquiries and clients won; cost per client, months to pay back one listing (a year\'s fee) and the check fill in by themselves.', [
    C('dl_id', 'Listing row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('listing', 'Directory listing', 'listing', 19), C('cost', 'Cost', 'money', 11), C('profile_views', 'Profile views', 'int', 10),
    C('enquiries', 'Enquiries', 'int', 10), C('clients_won', 'Clients won', 'int', 10),
    CA('booked_share', 'Clients won per enquiry, %', 'pct', 'IF({col:enquiries}>0,{col:clients_won}/{col:enquiries},0)', 11),
    CA('cost_per_client', 'Cost per client won', 'money', 'IF({col:clients_won}>0,{col:cost}/{col:clients_won},"")', 11),
    CA('payback_months', 'Months to pay back one listing', 'num', 'IF({col:clients_won}>0,ROUND(12*{col:cost}/({col:clients_won}*{set:avg_charge}*{set:client_sessions_month}*{set:margin_pct}),1),"")', 11),
    CA('payback_check', 'Payback check', 'text', 'IF({col:payback_months}="",%s,IF({col:payback_months}<={set:max_payback_months},%s,IF({col:payback_months}<=2*{set:max_payback_months},%s,%s)))' % (ck('Does not pay back'), ck('Pays back fast'), ck('Pays back slowly'), ck('Does not pay back')), 16),
    OWNER_PH(), COMPCOL()], D.directory_d(), 150, [A('payback_check', '= ' + ck('Does not pay back'), 'bad'), A('payback_check', '= ' + ck('Pays back slowly'), 'warn')]))
tables.append(T('website', 'Website Performance', 'Website: visits, forms and bookings by month',
    'One row per month: visits, enquiry forms and bookings; the form and booking shares and the month\'s marketing spend, enquiries and cost per client fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('visits', 'Visits', 'int', 10), C('enquiry_forms', 'Enquiry forms', 'int', 10), C('bookings', 'Bookings', 'int', 10),
    CA('form_share', 'Visits to form, %', 'pct', 'IF({col:visits}>0,{col:enquiry_forms}/{col:visits},0)', 11), CA('booking_share', 'Forms to booking, %', 'pct', 'IF({col:enquiry_forms}>0,{col:bookings}/{col:enquiry_forms},0)', 11),
    CA('marketing_spent', 'Marketing spent in the month', 'money', 'SUMIFS({range:budget.spent},{range:budget.month},{col:month})', 12),
    CA('all_enquiries', 'All enquiries in the month', 'int', 'SUMIFS({range:sourcemonths.enquiries},{range:sourcemonths.month},{col:month})', 11),
    CA('all_booked', 'All booked clients in the month', 'int', 'SUMIFS({range:sourcemonths.booked},{range:sourcemonths.month},{col:month})', 11),
    CA('cost_per_enquiry', 'Cost per enquiry', 'money', 'IF({col:all_enquiries}>0,{col:marketing_spent}/{col:all_enquiries},0)', 11),
    CA('cost_per_client', 'Cost per booked client', 'money', 'IF({col:all_booked}>0,{col:marketing_spent}/{col:all_booked},0)', 11)], D.website_d(), 60))
tables.append(T('workshops', 'Workshops and Talks', 'Workshops and talks with attendees, cost and enquiries',
    'One row per workshop or talk: audience, attendees, cost, enquiries and the contact at the host; cost per attendee and enquiries per 100 attendees fill in by themselves.', [
    C('workshop_id', 'Event ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), LST('kind', 'Kind', 'mkind', 15), C('title', 'Title', 'text', 30), C('audience', 'Audience', 'text', 28), C('attendees', 'Attendees', 'int', 10),
    C('cost', 'Cost', 'money', 11), C('enquiries', 'Enquiries', 'int', 10), REF('contact', 'Host contact', 'referrers.name', 22),
    CA('cost_per_attendee', 'Cost per attendee', 'money', 'IF({col:attendees}>0,{col:cost}/{col:attendees},0)', 11),
    CA('enq_per_100', 'Enquiries per 100 attendees', 'num', 'IF({col:attendees}>0,{col:enquiries}*100/{col:attendees},0)', 11),
    CA('contact_phone', 'Host contact phone', 'text', LKT('referrers.phone', 'referrers.name', 'contact'), 18), COORD_PH(), COMPCOL()], D.workshops_d(), 80))
tables.append(T('newsletter', 'Newsletter Issues', 'Newsletter issues with replies and enquiries',
    'One row per issue: topic, people it was sent to, replies and enquiries; the reply rate and enquiries per 1,000 sent fill in by themselves.', [
    C('issue_id', 'Issue ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('topic', 'Topic', 'text', 34), C('sent_to', 'Sent to', 'int', 10), C('replies', 'Replies', 'int', 10), C('enquiries', 'Enquiries', 'int', 10),
    CA('reply_rate', 'Reply rate, %', 'pct', 'IF({col:sent_to}>0,{col:replies}/{col:sent_to},0)', 10),
    CA('enq_per_1000', 'Enquiries per 1,000 sent', 'num', 'IF({col:sent_to}>0,{col:enquiries}*1000/{col:sent_to},0)', 11)], D.newsletter_d(), 80))
tables.append(T('feedback', 'Client Feedback Survey', 'Client feedback survey: score, recommend answer and topic',
    'One row per survey answer: client type, service, a score from 1 to 10, would recommend and the topic; the score band fills in by itself. No comments are recorded.', [
    C('survey_id', 'Survey ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), LST('client_type', 'Client type', 'ctype', 12), LST('service', 'Service', 'svc', 18), C('rating', 'Feedback score (1-10)', 'int', 10),
    C('would_recommend', 'Would recommend', 'bool', 10), LST('topic', 'Topic', 'fbtopic', 16),
    CA('rating_band', 'Score band', 'text', 'IF({col:rating}>=9,%s,IF({col:rating}>=7,%s,%s))' % (ck('High score'), ck('Mid score'), ck('Low score')), 12),
    CA('topic_avg_12m', 'Topic average score, last 12 months', 'num', 'IFERROR(AVERAGEIFS({range:feedback.rating},{range:feedback.topic},{col:topic},{range:feedback.date},">="&({today}-365),{range:feedback.date},"<="&{today}),0)', 11)], D.feedback_d(), 500,
    [A('rating_band', '= ' + ck('Low score'), 'bad'), A('rating_band', '= ' + ck('High score'), 'good')]))
tables.append(T('groups', 'Groups', 'Group programs with fill rate, break-even and profit',
    'One row per group run: facilitator, room, start, capacity, sign-ups and costs; fill rate, break-even, profit, profit per person and per hour fill in by themselves.', [
    C('group_id', 'Group ID', 'text', 9, required=True), LST('program', 'Program', 'prog', 21), LST('facilitator', 'Facilitator', 'clin', 16), LST('co_facilitator', 'Co-facilitator', 'clin', 16), LST('room', 'Room', 'room5', 13),
    C('start_date', 'Start date', 'date', 11), LST('weekday', 'Weekday', 'wday', 11), C('start_time', 'Start time', 'time', 9), C('weeks', 'Weeks', 'int', 9), C('capacity', 'Capacity (places)', 'int', 10), C('fee', 'Fee per person', 'money', 11),
    C('signups', 'Sign-ups', 'int', 9), C('revenue', 'Revenue', 'money', 11), C('facilitator_pay', 'Facilitator pay', 'money', 11), C('materials', 'Materials', 'money', 11), C('marketing', 'Marketing', 'money', 11),
    C('room_cost', 'Room cost', 'money', 11), C('meetings_held', 'Meetings held', 'int', 9), LST('status', 'Status', 'grpst', 16),
    CA('fill_rate', 'Fill rate, %', 'pct', 'IF({col:capacity}>0,{col:signups}/{col:capacity},0)', 10),
    CA('fill_check', 'Fill check', 'text', 'IF({col:fill_rate}>={set:min_group_fill},%s,%s)' % (ck('Fill at or above minimum'), ck('Fill below minimum')), 16),
    CA('net_fee', 'Revenue per person', 'money', 'IF({col:signups}>0,{col:revenue}/{col:signups},{col:fee})', 11),
    CA('pay_share', 'Facilitator pay share of fees, %', 'pct', 'IF({col:revenue}>0,{col:facilitator_pay}/{col:revenue},0)', 11),
    CA('fixed_costs', 'Materials, marketing and room', 'money', '{col:materials}+{col:marketing}+{col:room_cost}', 11),
    CA('breakeven_signups', 'Break-even sign-ups', 'int', 'IFERROR(ROUNDUP({col:fixed_costs}/({col:net_fee}*(1-{col:pay_share})),0),0)', 10),
    CA('break_check', 'Break-even check', 'text', 'IF({col:signups}>={col:breakeven_signups},%s,%s)' % (ck('Above break-even'), ck('Below break-even')), 15),
    CA('attendance_rate', 'Attendance at meetings, %', 'pct', 'IFERROR(SUMIFS({range:attendance.attended},{range:attendance.group_id},{col:group_id})/SUMIFS({range:attendance.expected},{range:attendance.group_id},{col:group_id}),"")', 11),
    CA('profit', 'Profit', 'money', '{col:revenue}-{col:facilitator_pay}-{col:fixed_costs}', 11),
    CA('profit_per_person', 'Profit per person', 'money', 'IF({col:signups}>0,{col:profit}/{col:signups},"")', 11),
    CA('profit_per_hour', 'Profit per facilitator hour', 'money', 'IF({col:weeks}>0,{col:profit}/({col:weeks}*{set:meeting_hours}),"")', 11),
    CA('counted', 'Counted in totals (1 = yes)', 'int', 'IF(OR({col:status}=%s,{col:status}=%s),1,0)' % (tok('grpst', 'Completed'), tok('grpst', 'Running')), 10),
    CA('next_flag', 'Next group (1 = yes)', 'int', 'IF(AND({col:start_date}>{today},{col:status}<>%s,{col:start_date}=%s),1,0)' % (CAN, NEXTMIN), 10),
    CA('facilitator_phone', 'Facilitator phone', 'text', LKT('team.phone', 'team.name', 'facilitator'), 18), COORD_PH(), OWNER_PH(), COMPCOL()], D.groups_d(), 80,
    [A('fill_check', '= ' + ck('Fill below minimum'), 'warn'), A('break_check', '= ' + ck('Below break-even'), 'bad'), A('profit', '< 0', 'bad')]))
tables.append(T('signups', 'Group Sign-ups', 'Group sign-ups with payment and attendance',
    'One row per person signed up to a group: payment, meetings attended and status; the group start, fee and attendance share fill in by themselves.', [
    C('signup_id', 'Sign-up ID', 'text', 10, required=True), REF('group_id', 'Group', 'groups.group_id', 9), LST('program', 'Program', 'prog', 21), C('name', 'Name', 'text', 24), C('phone', 'Phone', 'text', 18),
    C('signed_on', 'Signed up on', 'date', 11), C('paid_amount', 'Paid', 'money', 11), C('paid_on', 'Paid on', 'date', 11), C('sessions_attended', 'Meetings attended', 'int', 10), LST('status', 'Status', 'signst', 13),
    CA('start_date', 'Group start', 'date', LKD('groups.start_date', 'groups.group_id', 'group_id'), 11),
    CA('start_time', 'Start time', 'time', 'IFERROR(INDEX({range:groups.start_time},MATCH({col:group_id},{range:groups.group_id},0)),"")', 9),
    CA('room', 'Room', 'text', LKT('groups.room', 'groups.group_id', 'group_id'), 13),
    CA('fee', 'Group fee', 'money', LKN('groups.fee', 'groups.group_id', 'group_id'), 11),
    CA('weeks', 'Weeks in the program', 'int', LKN('groups.weeks', 'groups.group_id', 'group_id'), 10),
    CA('meetings_held', 'Meetings held so far', 'int', LKN('groups.meetings_held', 'groups.group_id', 'group_id'), 10),
    CA('attendance_share', 'Attendance, % of meetings held', 'pct', 'IF({col:meetings_held}>0,{col:sessions_attended}/MIN({col:weeks},{col:meetings_held}),"")', 11),
    COMPCOL()], D.signups_d(), 300, [A('status', '= ' + tok('signst', 'Dropped out'), 'warn'), A('status', '= ' + tok('signst', 'Refunded'), 'bad')]))
tables.append(T('attendance', 'Group Attendance', 'Group attendance by meeting',
    'One row per group meeting: meeting number, date and people who came; the program, the people signed up and the attendance share fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), REF('group_id', 'Group', 'groups.group_id', 9), C('meeting_no', 'Meeting number', 'int', 10), C('date', 'Date', 'date', 11), C('attended', 'Attended', 'int', 10),
    CA('program', 'Program', 'text', LKT('groups.program', 'groups.group_id', 'group_id'), 21), CA('expected', 'People signed up', 'int', LKN('groups.signups', 'groups.group_id', 'group_id'), 10),
    CA('attendance_share', 'Attendance, %', 'pct', 'IF({col:expected}>0,{col:attended}/{col:expected},0)', 10),
    CA('attendance_check', 'Attendance check', 'text', 'IF({col:attendance_share}>={set:min_attendance},%s,%s)' % (ck('Attendance at target'), ck('Attendance low')), 15)], D.attendance_d(), 300,
    [A('attendance_check', '= ' + ck('Attendance low'), 'warn')]))
tables.append(T('interest', 'Group Interest List', 'Group interest list with the next group of each program',
    'One row per person interested in a group: program, when added, when contacted and whether they signed up; the next group of that program, its start and the contact check fill in by themselves.', [
    C('interest_id', 'Interest ID', 'text', 10, required=True), C('name', 'Name', 'text', 24), C('phone', 'Phone', 'text', 18), LST('program', 'Program', 'prog', 21), C('added_on', 'Added on', 'date', 11),
    C('contacted_on', 'Contacted on', 'date', 12), C('signed_up', 'Signed up', 'bool', 9),
    CA('next_start', 'Next group start', 'date', 'IF(%s>=99999,"",%s)' % (NEXTPROG('{col:program}'), NEXTPROG('{col:program}')), 12),
    CA('next_group', 'Next group', 'text', 'IFERROR(IF({col:next_start}="","",INDEX({range:groups.group_id},MATCH({col:next_start},{range:groups.start_date},0))),"")', 9),
    CA('days_waiting', 'Days on the list', 'int', 'IF({col:signed_up}=%s,"",{today}-{col:added_on})' % YES, 9),
    CA('interest_check', 'Contact check', 'text', 'IF({col:signed_up}=%s,%s,IF({col:contacted_on}="",%s,%s))' % (YES, ck('Signed up'), ck('Contact the person'), ck('Contacted')), 16),
    COMPCOL()], D.interest_d(), 150, [A('interest_check', '= ' + ck('Contact the person'), 'bad'), A('interest_check', '= ' + ck('Signed up'), 'good')]))
tables.append(T('ideas', 'Group Ideas', 'Ideas for new groups with expected sign-ups and revenue',
    'One row per idea for a new group: who it is for, people interested, facilitator, places and fee; expected revenue, the expected fill and the check fill in by themselves.', [
    C('idea_id', 'Idea ID', 'text', 9, required=True), C('idea', 'Idea', 'text', 34), LST('client_type', 'Client type', 'ctype', 13), C('people_interested', 'People interested', 'int', 10), LST('facilitator', 'Facilitator', 'clin', 16),
    C('capacity', 'Capacity (places)', 'int', 10), C('expected_signups', 'Expected sign-ups', 'int', 10), C('fee', 'Fee per person', 'money', 11),
    CA('expected_revenue', 'Expected revenue', 'money', '{col:expected_signups}*{col:fee}', 11), CA('expected_fill', 'Expected fill, %', 'pct', 'IF({col:capacity}>0,{col:expected_signups}/{col:capacity},0)', 10),
    CA('idea_check', 'Fill check', 'text', 'IF({col:expected_fill}>={set:min_group_fill},%s,%s)' % (ck('Fill at or above minimum'), ck('Fill below minimum')), 16)], D.ideas_d(), 50,
    [A('idea_check', '= ' + ck('Fill below minimum'), 'warn')]))
tables.append(T('programs', 'Programs', 'Group programs with weeks and fee', 'One row per group program: weeks and the fee per person before any tax.', [
    LST('program', 'Program', 'prog', 22, required=True), C('weeks', 'Weeks', 'int', 9), C('fee', 'Fee per person', 'money', 12)], D.programs_d(), 50))
tables.append(T('team', 'Team', 'Team: clinicians, coordinator and outside contacts',
    'One row per person: employed, contract (self-employed) and associate (works under supervision) clinicians, the coordinator and outside contacts; the groups each led or co-led fill in by themselves.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), C('role', 'Role', 'text', 24), C('team', 'Team', 'text', 12), C('pay_type', 'Pay type', 'text', 16), C('phone', 'Phone', 'text', 18), C('email', 'Email', 'text', 26),
    C('hours_week', 'Hours a week', 'int', 9), C('monthly_salary', 'Monthly salary', 'int', 11), C('split_pct', 'Split share', 'pct', 9), C('session_rate', 'Rate per session', 'int', 10), C('hourly_rate', 'Hourly rate', 'int', 9),
    C('session_cap', 'Session cap a week', 'int', 10), C('session_target', 'Session target a week', 'int', 10), C('speciality', 'Speciality', 'text', 30), C('country', 'Country', 'text', 14), C('start', 'Start', 'date', 11),
    CA('groups_led', 'Groups led or co-led', 'int', 'COUNTIFS({range:groups.facilitator},{col:name})+COUNTIFS({range:groups.co_facilitator},{col:name})', 10)], D.team_d(), 50))
assert len(tables) == 20

# practice name column on every table that sends a message (added when missing by th7.py)
