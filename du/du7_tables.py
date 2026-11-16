"""Doula business suite part 7: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du7_lists import *
import du7_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def CO(): return CA('company', 'Business', 'text', '{set:company}', 24)
def OWN(): return CA('owner_phone', 'Owner-doula phone', 'text', '"%s"' % D.OWNER_PHONE, 18)
def OWNN(): return CA('owner_name', 'Owner-doula', 'text', 'IFERROR(INDEX({range:team.name},MATCH(%s,{range:team.role},0))&"","")' % tok('role', 'Owner-doula'), 18)
def NXT(): return CA('next_class', 'Next class date', 'date', '{set:next_class_date}', 11)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
QS = 'DATE(YEAR({today}),3*INT((MONTH({today})-1)/3)+1,1)'
YES = '{list:yesno.yes}'
CANC = tok('ctstatus', 'Cancelled'); CARE = tok('rsource', 'Care provider'); TYS = tok('mkind', 'Referral thank-yous')
THK, DUE, MISS, NOCL, UPD = ca('Thanked'), ca('Thank-you due'), ca('Thank-you missed'), ca('No client yet'), ca('Up to date')
ASK, WAIT, REM, ANS, NYD = ca('Ask now'), ca('Asked, waiting'), ca('Send reminder'), ca('Answered'), ca('Not yet due')
ABOVE, BELOW = ca('Above break-even'), ca('Below break-even')
SIL, LESS, STILL = ca('Silent this year'), ca('Sending less'), ca('Still sending')
VISIT, THANK, HOLD = ca('Visit'), ca('Thank'), ca('Hold')
def DW(col, n): return '{range:%s},">="&({today}-%s),{range:%s},"<="&{today}' % (col, n, col)

settings = [
    S('company', 'Your business name', 'text', COMPANY),
    S('thank_days', 'Days after a referral that a thank-you still counts as due', 'int', 90),
    S('thank_late', 'Days after a referral before a thank-you is late', 'int', 30),
    S('follow_days', 'Days from today for the follow-up with a silent referrer', 'int', 14),
    S('review_ask_days', 'Days after the birth to ask for a review, and to remind', 'int', REVIEW_ASK_DAYS),
    S('star_target', 'Average stars you want', 'num', 4.6),
    S('review_rate_min', 'Review answers you want from your requests', 'pct', 0.60),
    S('ref_share_target', 'Share of income you want from referrals', 'pct', 0.45),
    S('top_source_max', 'Highest share of clients from one source', 'pct', 0.30),
    S('class_fill_target', 'Class fill you want (sign-ups of seats)', 'pct', 0.70),
    S('instructor_rate', 'Cost of an instructor hour, teaching and preparing', 'money', 75),
    S('class_hour_target', 'Profit per class hour you want', 'money', 30),
    S('cac_max', 'Highest marketing cost per signed client you accept', 'money', 60),
    S('gift_budget_year', 'Thank-you gift budget for a year', 'money', 1800),
    S('scen_best', 'Best scenario multiplier', 'pct', 1.15),
    S('scen_worst', 'Worst scenario multiplier', 'pct', 0.80),
    S('next_class_date', 'Date of your next class', 'date', ahead(21)),
    S('next_class_name', 'Name of your next class', 'text', 'Newborn workshop'),
    S('nudge_stars', 'Lowest stars before you ask a past client for a referral', 'int', 4),
    S('nudge_days', 'Days after the review before you ask for a referral', 'int', 7),
]
assert 3 <= len(settings) <= 20

tables = []
# ---------------------------------------------------------------- 1 referrals
tables.append(T('referrals', 'Referrals', 'Referral Log: who sent an enquiry, thanks and gifts',
    'One row per referral: date, source, referrer, enquiry, client, thank-you date and gift cost; the client, income, thank-you check and referrer phone fill in by themselves.', [
    C('referral_id', 'Referral ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), LST('source', 'Source', 'rsource', 20), REF('referrer', 'Referrer', 'referrers.referrer', 24),
    C('enquiry_id', 'Enquiry ID', 'text', 10), C('client_id', 'Client ID', 'text', 10), C('thanked_on', 'Thanked on', 'date', 11), C('gift_cost', 'Gift cost', 'int', 10),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('client', 'Client', 'text', LKT('clients.client', 'clients.client_id', 'client_id'), 22),
    CA('signed', 'Became a client', 'int', 'IF({col:client_id}<>"",1,0)', 9), CA('thanked', 'Thanked', 'int', 'IF({col:thanked_on}>0,1,0)', 8),
    CA('age_days', 'Days since referral', 'int', '{today}-{col:date}', 9),
    CA('days_to_thank', 'Days to thank', 'int', 'IF({col:thanked}=1,{col:thanked_on}-{col:date},0)', 9),
    CA('in_time', 'Thanked in time', 'int', 'IF(AND({col:thanked}=1,{col:days_to_thank}<={set:thank_late}),1,0)', 9),
    CA('matured', 'Thank-you old enough', 'int', 'IF(AND({col:signed}=1,{col:age_days}>{set:thank_late}),1,0)', 9),
    CA('thank_flag', 'Thank-you check', 'text', 'IF({col:signed}=0,%s,IF({col:thanked}=1,%s,IF({col:age_days}>{set:thank_days},%s,%s)))' % (NOCL, THK, MISS, DUE), 16),
    CA('income', 'Client income', 'money', 'IF({col:signed}=1,SUMIFS({range:contracts.price},{range:contracts.client_id},{col:client_id},{range:contracts.status},"<>"&%s),0)' % CANC, 11),
    CA('referrer_phone', 'Referrer phone', 'text', 'IFERROR(INDEX({range:referrers.phone},MATCH({col:referrer},{range:referrers.referrer},0))&"","")', 18), CO()],
    D.referrals_d(), 600, [A('thank_flag', '= ' + DUE, 'warn'), A('thank_flag', '= ' + MISS, 'bad')]))
# ---------------------------------------------------------------- 2 enquiries
tables.append(T('enquiries', 'Enquiries', 'Enquiries with source, status and outcome',
    'One row per enquiry: date, name, phone, source, status, lost reason and the client it became; the month and the class invitation fields fill in by themselves.', [
    C('enquiry_id', 'Enquiry ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('name', 'Name', 'text', 24), C('phone', 'Phone', 'text', 18), LST('source', 'Source', 'source', 20),
    LST('status', 'Status', 'estatus', 18), LST('reason', 'Lost reason', 'lostreason', 17), C('signed_on', 'Signed on', 'date', 11), C('client_id', 'Client ID', 'text', 10),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('next_class', 'Next class date', 'date', '{set:next_class_date}', 11),
    CA('class_name', 'Next class', 'text', '{set:next_class_name}', 20), CO()], D.enquiries_d(), 900))
# ---------------------------------------------------------------- 3 clients
tables.append(T('clients', 'Clients', 'Clients with source, package and doula',
    'One row per client (first name and family name only): kind, package, doula, source, signed on, attended on and status; income, referral and review fields fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 22), C('phone', 'Phone', 'text', 18), LST('kind', 'Kind', 'ckind', 11), C('package', 'Package', 'text', 22),
    LST('doula', 'Doula', 'doula', 17), LST('source', 'Source', 'source', 20), C('signed_on', 'Signed on', 'date', 11), C('attended_on', 'Attended on', 'date', 11), LST('status', 'Status', 'cstatus', 15),
    C('edd', 'Estimated due date', 'date', 11),
    CA('month', 'Signed month', 'date', 'DATE(YEAR({col:signed_on}),MONTH({col:signed_on}),1)', 11),
    CA('income', 'Package income', 'money', 'SUMIFS({range:contracts.price},{range:contracts.client_id},{col:client_id},{range:contracts.status},"<>"&%s)' % CANC, 11),
    CA('from_referral', 'From a referral', 'int', 'IF(COUNTIFS({range:referrals.client_id},{col:client_id})>0,1,0)', 9),
    CA('reviewed', 'Reviews asked', 'int', 'COUNTIFS({range:reviews.client_id},{col:client_id})', 9),
    CA('photographer', 'Photographer', 'text', 'IFERROR(INDEX({range:team.name},MATCH(%s,{range:team.role},0))&"","")' % tok('role', 'Photographer'), 18),
    CA('photographer_phone', 'Photographer phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH(%s,{range:team.role},0))&"","")' % tok('role', 'Photographer'), 18), CO()],
    D.clients_d(), 450, [A('status', '= ' + tok('cstatus', 'Cancelled'), 'warn')]))
# ---------------------------------------------------------------- 4 contracts
tables.append(T('contracts', 'Contracts', 'Contracts with price and status',
    'One row per contract: client, package, price, signed on and status; the source of the client and whether a referral brought them fill in from Clients and Referrals.', [
    C('contract_id', 'Contract ID', 'text', 10, required=True), C('client_id', 'Client ID', 'text', 10), REF('client', 'Client', 'clients.client', 22), C('package', 'Package', 'text', 22), C('price', 'Price', 'money', 11),
    C('signed_on', 'Signed on', 'date', 11), LST('status', 'Status', 'ctstatus', 11),
    CA('source', 'Source', 'text', LKT('clients.source', 'clients.client_id', 'client_id'), 20),
    CA('from_referral', 'From a referral', 'int', 'IF(COUNTIFS({range:referrals.client_id},{col:client_id})>0,1,0)', 9),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:signed_on}),MONTH({col:signed_on}),1)', 11)],
    D.contracts_d(), 450, [A('status', '= ' + CANC, 'warn')]))
# ---------------------------------------------------------------- 5 sources
tables.append(T('sources', 'Sources', 'Sources with the thank-you gift value',
    'One row per source of enquiries: its kind and the value of a thank-you gift for a referral; the gift cost estimates read these values.', [
    LST('source', 'Source', 'source', 22, required=True), C('kind', 'Kind', 'text', 12), C('gift_value', 'Gift value', 'money', 11)], D.sources_d(), 50))
# ---------------------------------------------------------------- 6 marketing
tables.append(T('marketing', 'Marketing Spend', 'Marketing spend with enquiries and signed clients',
    'One row per campaign and month: kind, source, cost, enquiries and signed clients; the cost per enquiry and per signed client fill in by themselves.', [
    C('campaign_id', 'Campaign ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), LST('kind', 'Kind', 'mkind', 20), LST('source', 'Source', 'source', 20), C('cost', 'Cost', 'money', 11),
    C('enquiries', 'Enquiries', 'int', 9), C('signed', 'Signed clients', 'int', 9),
    CA('cost_enq', 'Cost per enquiry', 'money', 'IF({col:enquiries}>0,ROUND({col:cost}/{col:enquiries},2),0)', 11),
    CA('cost_signed', 'Cost per signed client', 'money', 'IF({col:signed}>0,ROUND({col:cost}/{col:signed},2),0)', 11), CO()],
    D.marketing_d(), 250, [A('cost_signed', '> {set:cac_max}', 'warn')]))
# ---------------------------------------------------------------- 7 class sessions
tables.append(T('class_sessions', 'Class Sessions', 'Class and workshop sessions with seats, income and costs',
    'One row per session: date, class, venue, instructor, seats, sign-ups, attendance, price, hours, venue cost, income and new clients; the instructor cost, profit, break-even and fill fill in by themselves.', [
    C('session_id', 'Session ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), LST('class', 'Class', 'ctype', 20), C('venue', 'Venue', 'text', 16), LST('instructor', 'Instructor', 'doula', 17),
    C('seats', 'Seats', 'int', 8), C('signed_up', 'Signed up', 'int', 8), C('attended', 'Attended', 'int', 8), C('price', 'Price per seat', 'money', 10), C('hours', 'Hours', 'num', 8),
    C('venue_cost', 'Venue cost', 'money', 10), C('income', 'Income', 'money', 10), C('new_clients', 'New clients', 'int', 8),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('fill', 'Fill', 'pct', 'IF({col:seats}>0,{col:signed_up}/{col:seats},0)', 8),
    CA('instr_cost', 'Instructor cost', 'money', 'ROUND({col:hours}*{set:instructor_rate},2)', 10), CA('cost', 'Total cost', 'money', '{col:venue_cost}+{col:instr_cost}', 10),
    CA('profit', 'Profit', 'money', '{col:income}-{col:cost}', 10), CA('profit_hour', 'Profit per class hour', 'money', 'IF({col:hours}>0,ROUND({col:profit}/{col:hours},2),0)', 10),
    CA('breakeven', 'Break-even sign-ups', 'int', 'IF({col:price}>0,ROUNDUP({col:cost}/{col:price},0),0)', 9),
    CA('above', 'At or above break-even', 'int', 'IF({col:signed_up}>={col:breakeven},1,0)', 9), CA('fill_ok', 'Fill on target', 'int', 'IF({col:fill}>={set:class_fill_target},1,0)', 9),
    CA('seats_left', 'Seats left', 'int', 'MAX(0,{col:seats}-{col:signed_up})', 8), CA('class_flag', 'Break-even check', 'text', 'IF({col:above}=1,%s,%s)' % (ABOVE, BELOW), 16),
    OWN(), OWNN(), CA('venue_contact', 'Venue contact', 'text', 'IFERROR(INDEX({range:team.name},MATCH(%s,{range:team.role},0))&"","")' % tok('role', 'Class venue'), 18), CA('venue_phone', 'Venue phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH(%s,{range:team.role},0))&"","")' % tok('role', 'Class venue'), 18), NXT(), CO()],
    D.class_sessions_d(), 200, [A('class_flag', '= ' + BELOW, 'bad'), A('class_flag', '= ' + ABOVE, 'good')]))
# ---------------------------------------------------------------- 8 class attendees
tables.append(T('class_attendees', 'Class Attendees', 'Class attendees with the client they became',
    'One row per sign-up: session, date, first name and initial, phone, client ID if they became a client, amount paid and whether they came; the class and the next class date fill in.', [
    C('attendee_id', 'Attendee ID', 'text', 10, required=True), REF('session_id', 'Session', 'class_sessions.session_id', 10), C('date', 'Date', 'date', 11), C('attendee', 'Attendee', 'text', 18), C('phone', 'Phone', 'text', 18),
    C('client_id', 'Client ID', 'text', 10), C('paid', 'Paid', 'money', 10), C('attended', 'Attended', 'bool', 8),
    CA('class', 'Class', 'text', LKT('class_sessions.class', 'class_sessions.session_id', 'session_id'), 20), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    CA('came', 'Came', 'int', 'IF({col:attended}=%s,1,0)' % YES, 7), NXT(), CO()], D.class_attendees_d(), 1000))
# ---------------------------------------------------------------- 9 class types
tables.append(T('class_types', 'Class Types', 'Class types with price and seats',
    'One row per class type: the usual price per seat and the seats; the class planning sheets compare each session with these.', [
    LST('class', 'Class', 'ctype', 22, required=True), C('price', 'Price per seat', 'money', 11), C('seats', 'Seats', 'int', 8)], D.class_types_d(), 50))
# ---------------------------------------------------------------- 10 reviews
tables.append(T('reviews', 'Reviews', 'Review requests and answers with stars and channel',
    'One row per review request: client, doula, asked on, received on, stars and channel (no text is kept); the answer, days to answer and the phone fill in by themselves.', [
    C('review_id', 'Review ID', 'text', 10, required=True), C('client_id', 'Client ID', 'text', 10), REF('client', 'Client', 'clients.client', 22), LST('doula', 'Doula', 'doula', 17), C('asked_on', 'Asked on', 'date', 11),
    C('received_on', 'Received on', 'date', 11), C('stars', 'Stars', 'int', 7), LST('channel', 'Channel', 'channel', 15),
    CA('month', 'Month asked', 'date', 'DATE(YEAR({col:asked_on}),MONTH({col:asked_on}),1)', 11), CA('answered', 'Answered', 'int', 'IF({col:received_on}>0,1,0)', 8),
    CA('good', 'Four or five stars', 'int', 'IF({col:stars}>=4,1,0)', 8), CA('days_answer', 'Days to answer', 'int', 'IF({col:answered}=1,{col:received_on}-{col:asked_on},0)', 8),
    CA('quick', 'Answered within two asks', 'int', 'IF(AND({col:answered}=1,{col:days_answer}<=2*{set:review_ask_days}),1,0)', 9),
    CA('old_enough', 'Asked long enough ago', 'int', 'IF({today}-{col:asked_on}>2*{set:review_ask_days},1,0)', 9),
    CA('phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client', 'client'), 18),
    CA('nudge', 'Ask for a referral', 'int', 'IF(AND({col:answered}=1,{col:stars}>={set:nudge_stars},{col:received_on}+{set:nudge_days}<={today},COUNTIFS({range:referrals.referrer},{col:client})=0),1,0)', 9),
    CA('nudge_date', 'Referral ask review date', 'date', 'IF({col:nudge}=1,{col:received_on},0)', 11), NXT(), CO()],
    D.reviews_d(), 300))
# ---------------------------------------------------------------- 11 team
tables.append(T('team', 'Team', 'Team and outside contacts with phones',
    'One row per person: staff, doulas, backup doulas, the admin and outside contacts; the message links read these phones, and the owner summary fields fill in from the other sheets.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 20), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
    CA('top_source', 'Top source by income', 'text', 'IFERROR(INDEX({range:src_value.source},MATCH(MAX({range:src_value.income}),{range:src_value.income},0))&"","")', 20),
    CA('top_income', 'Income of the top source', 'money', 'MAX({range:src_value.income})', 11),
    CA('reviews_month', 'Reviews asked this month', 'int', 'COUNTIFS({range:reviews.month},%s)' % MS, 9),
    CA('stars_q', 'Average stars this quarter', 'num', 'IFERROR(ROUND(AVERAGEIFS({range:reviews.stars},{range:reviews.received_on},">="&%s,{range:reviews.received_on},"<="&{today}),2),0)' % QS, 9),
    CA('cost_signed_12', 'Marketing cost per signed client', 'money', 'IFERROR(ROUND(SUMIFS({range:marketing.cost},{range:marketing.month},">"&EDATE(%s,-12),{range:marketing.month},"<="&%s)/SUMIFS({range:marketing.signed},{range:marketing.month},">"&EDATE(%s,-12),{range:marketing.month},"<="&%s),2),0)' % (MS, MS, MS, MS), 11),
    CO()], D.team_d(), 50))
# ---------------------------------------------------------------- 12 referral value by source
tables.append(T('src_value', 'Referral Value by Source', 'Income and income per client for each source',
    'One row per source: the price of all non-cancelled contracts of its clients and the income per client; sources are judged by income, not by count.', [
    LST('source', 'Source', 'source', 22, required=True),
    CA('income', 'Income', 'money', 'SUMIFS({range:contracts.price},{range:contracts.source},{col:source},{range:contracts.status},"<>"&%s)' % CANC, 12),
    CA('income_client', 'Income per client', 'money', 'IFERROR(ROUND({col:income}/COUNTIFS({range:contracts.source},{col:source},{range:contracts.status},"<>"&%s),2),0)' % CANC, 12)], D.src_d(), 50))
# ---------------------------------------------------------------- 13 source costs
tables.append(T('src_cost', 'Source Costs', 'Cost of gifts and fees for each source',
    'One row per source: the thank-you gifts plus the marketing spend tied to it (the thank-you line of Marketing Spend is already inside the gift cost) and the cost per signed client.', [
    LST('source', 'Source', 'source', 22, required=True),
    CA('cost', 'Cost of gifts and fees', 'money', 'SUMIFS({range:referrals.gift_cost},{range:referrals.source},{col:source})+SUMIFS({range:marketing.cost},{range:marketing.source},{col:source},{range:marketing.kind},"<>"&%s)' % TYS, 12),
    CA('cost_signed', 'Cost per signed client', 'money', 'IFERROR(ROUND({col:cost}/COUNTIFS({range:contracts.source},{col:source},{range:contracts.status},"<>"&%s),2),0)' % CANC, 12)], D.src_d(), 50))
# ---------------------------------------------------------------- 14 referrers
R = '{range:referrals.referrer},{col:referrer}'
tables.append(T('referrers', 'Referrer Ranking', 'Referrers ranked with referrals, clients and income',
    'One row per referrer (a care-provider office, a support professional, a past client or a class): referrals, clients, income, last 12 months against the 12 before, last referral and what to do next.', [
    C('referrer', 'Referrer', 'text', 24, required=True), C('phone', 'Phone', 'text', 18), LST('source', 'Source', 'rsource', 20),
    CA('referrals', 'Referrals', 'int', 'COUNTIFS(%s)' % R, 9), CA('clients', 'Clients', 'int', 'COUNTIFS(%s,{range:referrals.signed},1)' % R, 8),
    CA('income', 'Income', 'money', 'SUMIFS({range:referrals.income},%s)' % R, 11), CA('gift_cost', 'Gift cost', 'money', 'SUMIFS({range:referrals.gift_cost},%s)' % R, 10),
    CA('rank', 'Rank by income', 'int', 'COUNTIFS({range:referrers.income},">"&{col:income})+1', 8),
    CA('last12', 'Referrals, last 12 months', 'int', 'COUNTIFS(%s,%s)' % (R, DW('referrals.date', 365)), 9),
    CA('prev12', 'Referrals, 12 months before', 'int', 'COUNTIFS(%s,{range:referrals.date},">"&({today}-730),{range:referrals.date},"<="&({today}-365))' % R, 9),
    CA('trend', 'Change in referrals', 'int', '{col:last12}-{col:prev12}', 9),
    CA('silent', 'Silent this year', 'int', 'IF(AND({col:last12}=0,{col:prev12}>0),1,0)', 8), CA('silent_prev', 'Referrals before the silence', 'int', 'IF({col:silent}=1,{col:prev12},0)', 9),
    CA('office_trend', 'Care-provider trend', 'int', 'IF({col:source}=%s,{col:trend},999)' % CARE, 9),
    CA('referrals_q', 'Referrals, thank-you window', 'int', 'COUNTIFS(%s,{range:referrals.date},">="&({today}-{set:thank_days}))' % R, 9),
    CA('clients_q', 'Clients, thank-you window', 'int', 'COUNTIFS(%s,{range:referrals.signed},1,{range:referrals.date},">="&({today}-{set:thank_days}))' % R, 9),
    CA('due_n', 'Thank-yous due', 'int', 'COUNTIFS(%s,{range:referrals.thank_flag},%s)' % (R, DUE), 8), CA('missed_n', 'Thank-yous missed', 'int', 'COUNTIFS(%s,{range:referrals.thank_flag},%s)' % (R, MISS), 8),
    CA('last_referral', 'Last referral', 'date', 'IF(SUMPRODUCT(MAX(({range:referrals.referrer}={col:referrer})*{range:referrals.date}))=0,"",SUMPRODUCT(MAX(({range:referrals.referrer}={col:referrer})*{range:referrals.date})))', 11),
    CA('last_thanked', 'Last thanked on', 'date', 'IF(SUMPRODUCT(MAX(({range:referrals.referrer}={col:referrer})*{range:referrals.thanked_on}))=0,"",SUMPRODUCT(MAX(({range:referrals.referrer}={col:referrer})*{range:referrals.thanked_on})))', 11),
    CA('thank_due', 'Thank-you check', 'text', 'IF({col:due_n}>0,%s,IF({col:missed_n}>0,%s,%s))' % (DUE, MISS, UPD), 16),
    CA('follow_up', 'Follow-up date', 'date', 'IF({col:silent}=1,{today}+{set:follow_days},"")', 11),
    CA('action', 'Next step', 'text', 'IF(OR({col:silent}=1,AND({col:prev12}>=4,{col:last12}<{col:prev12})),%s,IF({col:due_n}>0,%s,%s))' % (VISIT, THANK, HOLD), 10), OWN(), OWNN(), CO()],
    D.referrers_d(), 250, [A('silent', '= 1', 'bad'), A('due_n', '> 0', 'warn')]))
# ---------------------------------------------------------------- 15 thank-you due
tables.append(T('thanks', 'Thank-you Due', 'Referrers with a thank-you still to send',
    'One row per referrer whose client was not thanked yet: clients in the thank-you window, thank-yous due and missed, the longest wait, the gift value to send and the check.', [
    REF('referrer', 'Referrer', 'referrers.referrer', 24, required=True), CA('source', 'Source', 'text', LKT('referrers.source', 'referrers.referrer', 'referrer'), 20),
    CA('clients_q', 'Clients, thank-you window', 'int', LKN('referrers.clients_q', 'referrers.referrer', 'referrer'), 9), CA('due_n', 'Thank-yous due', 'int', LKN('referrers.due_n', 'referrers.referrer', 'referrer'), 8),
    CA('missed_n', 'Thank-yous missed', 'int', LKN('referrers.missed_n', 'referrers.referrer', 'referrer'), 8),
    CA('waiting_days', 'Longest wait, days', 'int', 'SUMPRODUCT(MAX(({range:referrals.referrer}={col:referrer})*({range:referrals.client_id}<>"")*({range:referrals.thanked_on}=0)*({today}-{range:referrals.date})))', 9),
    CA('last_thanked', 'Last thanked on', 'date', LKD('referrers.last_thanked', 'referrers.referrer', 'referrer'), 11),
    CA('gift_due', 'Gift value to send', 'money', '({col:due_n}+{col:missed_n})*IFERROR(INDEX({range:sources.gift_value},MATCH({col:source},{range:sources.source},0)),0)', 11),
    CA('flag', 'Thank-you check', 'text', 'IF({col:due_n}>0,%s,IF({col:missed_n}>0,%s,%s))' % (DUE, MISS, UPD), 16)],
    D.thanks_d(), 60, [A('flag', '= ' + DUE, 'warn'), A('flag', '= ' + MISS, 'bad')]))
# ---------------------------------------------------------------- 16 referral gap list
tables.append(T('gaps', 'Referral Gap List', 'Referrers who sent clients before and fewer or none now',
    'One row per referrer to win back: referrals in the last 12 months and the 12 before, the last referral, the date you last visited and the follow-up date.', [
    REF('referrer', 'Referrer', 'referrers.referrer', 24, required=True), C('visited_on', 'Last visited on', 'date', 11),
    CA('source', 'Source', 'text', LKT('referrers.source', 'referrers.referrer', 'referrer'), 20), CA('prev12', 'Referrals, 12 months before', 'int', LKN('referrers.prev12', 'referrers.referrer', 'referrer'), 9),
    CA('last12', 'Referrals, last 12 months', 'int', LKN('referrers.last12', 'referrers.referrer', 'referrer'), 9), CA('last_referral', 'Last referral', 'date', LKD('referrers.last_referral', 'referrers.referrer', 'referrer'), 11),
    CA('follow_up', 'Follow-up date', 'date', '{today}+{set:follow_days}', 11),
    CA('flag', 'Gap check', 'text', 'IF({col:last12}=0,%s,IF({col:last12}<{col:prev12},%s,%s))' % (SIL, LESS, STILL), 16)],
    D.gaps_d(), 60, [A('flag', '= ' + SIL, 'bad'), A('flag', '= ' + LESS, 'warn')]))
# ---------------------------------------------------------------- 17 class economics
def CSL(c): return LKN('class_sessions.%s' % c, 'class_sessions.session_id', 'session_id')
tables.append(T('class_econ', 'Class Economics', 'Recent sessions with profit per class hour and break-even',
    'One row per recent session: sign-ups, income, total cost, profit, profit per class hour, the break-even sign-ups and how the session compares with its class type.', [
    REF('session_id', 'Session', 'class_sessions.session_id', 10, required=True), CA('class', 'Class', 'text', LKT('class_sessions.class', 'class_sessions.session_id', 'session_id'), 20),
    CA('date', 'Date', 'date', LKD('class_sessions.date', 'class_sessions.session_id', 'session_id'), 11), CA('signed_up', 'Signed up', 'int', CSL('signed_up'), 8), CA('income', 'Income', 'money', CSL('income'), 10),
    CA('cost', 'Total cost', 'money', CSL('cost'), 10), CA('profit', 'Profit', 'money', CSL('profit'), 10), CA('profit_hour', 'Profit per class hour', 'money', CSL('profit_hour'), 10),
    CA('breakeven', 'Break-even sign-ups', 'int', CSL('breakeven'), 9), CA('flag', 'Break-even check', 'text', LKT('class_sessions.class_flag', 'class_sessions.session_id', 'session_id'), 16),
    CA('type_avg', 'Type average per hour', 'money', 'IFERROR(INDEX({range:ctype_stats.profit_hour},MATCH({col:class},{range:ctype_stats.class},0)),0)', 10),
    CA('vs_type', 'Against the type average', 'money', '{col:profit_hour}-{col:type_avg}', 10), CO()],
    D.class_econ_d(), 60, [A('flag', '= ' + BELOW, 'bad')]))
# ---------------------------------------------------------------- 18 class by type
tables.append(T('ctype_stats', 'Class by Type', 'Sessions and profit per class hour for each class type',
    'One row per class type: the sessions held and the profit per class hour over all sessions, after venue cost and instructor time.', [
    LST('class', 'Class', 'ctype', 22, required=True), CA('sessions', 'Sessions', 'int', 'COUNTIFS({range:class_sessions.class},{col:class})', 9),
    CA('profit_hour', 'Profit per class hour', 'money', 'IFERROR(ROUND(SUMIFS({range:class_sessions.profit},{range:class_sessions.class},{col:class})/SUMIFS({range:class_sessions.hours},{range:class_sessions.class},{col:class}),2),0)', 12)],
    D.ctype_stats_d(), 50))
# ---------------------------------------------------------------- 19 review requests due
def RV(c): return 'IFERROR(INDEX({range:reviews.%s},MATCH({col:client},{range:reviews.client},0)),"")' % c
tables.append(T('review_due', 'Review Requests Due', 'Clients due for a review request or a reminder',
    'One row per recent birth attended: the doula, the date of the birth, the request date after your ask days, when you asked, when they answered and what to do next.', [
    REF('client', 'Client', 'clients.client', 22, required=True), CA('doula', 'Doula', 'text', LKT('clients.doula', 'clients.client', 'client'), 17),
    CA('attended_on', 'Attended on', 'date', LKD('clients.attended_on', 'clients.client', 'client'), 11),
    CA('request_date', 'Request date', 'date', 'IF(ISNUMBER({col:attended_on}),{col:attended_on}+{set:review_ask_days},"")', 11),
    CA('asked_on', 'Asked on', 'date', RV('asked_on'), 11),
    CA('answered_on', 'Answered on', 'date', 'IFERROR(IF(INDEX({range:reviews.received_on},MATCH({col:client},{range:reviews.client},0))=0,"",INDEX({range:reviews.received_on},MATCH({col:client},{range:reviews.client},0))),"")', 11),
    CA('status', 'Request check', 'text', 'IF(ISNUMBER({col:answered_on}),%s,IF(ISNUMBER({col:asked_on}),IF({today}-{col:asked_on}>={set:review_ask_days},%s,%s),IF({col:request_date}<={today},%s,%s)))' % (ANS, REM, WAIT, ASK, NYD), 16),
    CA('phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client', 'client'), 18), CO()],
    D.review_due_d(), 80, [A('status', '= ' + ASK, 'bad'), A('status', '= ' + REM, 'warn'), A('status', '= ' + ANS, 'good')]))
# ---------------------------------------------------------------- 20 reviews by month
tables.append(T('review_month', 'Reviews by Month', 'Review requests, answers and stars for each month',
    'One row per month: requests asked, answers received, the answer rate, the average stars of that month and of the last 3 months.', [
    C('month', 'Month', 'date', 11, required=True), CA('asked', 'Asked', 'int', 'COUNTIFS({range:reviews.month},{col:month})', 8),
    CA('received', 'Received', 'int', 'COUNTIFS({range:reviews.received_on},">="&{col:month},{range:reviews.received_on},"<"&EDATE({col:month},1))', 8),
    CA('rate', 'Answer rate', 'pct', 'IF({col:asked}>0,COUNTIFS({range:reviews.month},{col:month},{range:reviews.answered},1)/{col:asked},0)', 9),
    CA('avg_stars', 'Average stars', 'num', 'IFERROR(ROUND(AVERAGEIFS({range:reviews.stars},{range:reviews.received_on},">="&{col:month},{range:reviews.received_on},"<"&EDATE({col:month},1)),2),0)', 9),
    CA('avg_3m', 'Average stars, 3 months', 'num', 'IFERROR(ROUND(AVERAGEIFS({range:reviews.stars},{range:reviews.received_on},">="&EDATE({col:month},-2),{range:reviews.received_on},"<"&EDATE({col:month},1)),2),0)', 9)],
    D.review_month_d(), 50))
assert len(tables) == 20, len(tables)
