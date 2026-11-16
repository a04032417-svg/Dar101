"""Doula Business suite part 1: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du1_lists import *
import du1_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def COMPANY_C(): return CA('company', 'Company', 'text', '{set:company}', 24)
def OWNER_PH(): return CA('owner_phone', 'Owner-doula phone', 'text', '"%s"' % D.OWNER_PHONE, 18)
def ADMIN_PH(): return CA('admin_phone', 'Admin phone', 'text', '"%s"' % D.ADMIN_PHONE, 18)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def INM(rng_, col): return '{range:%s},">="&%s,{range:%s},"<"&EDATE(%s,1)' % (rng_, col, rng_, col)
LOST = tok('estatus', 'Lost'); SIGNED = tok('estatus', 'Signed'); NEWE = tok('estatus', 'New'); BOOKE = tok('estatus', 'Consultation booked'); HELDE = tok('estatus', 'Consultation held'); SENTE = tok('estatus', 'Contract sent')
O_SIGNED = tok('outcome', 'Signed'); O_THINK = tok('outcome', 'Thinking'); O_DECL = tok('outcome', 'Declined'); O_NOSHOW = tok('outcome', 'No-show'); O_BOOKED = tok('outcome', 'Booked')
R_PRICE = tok('lostreason', 'Price'); R_FULL = tok('lostreason', 'Date full'); R_BACKUP = tok('lostreason', 'No backup'); R_OTHER = tok('lostreason', 'Chose someone else'); R_NOREPLY = tok('lostreason', 'No reply')
SV_PP = tok('service', 'Postpartum'); KD_PP = tok('ckind', 'Postpartum'); CS_CANCEL = tok('cstatus', 'Cancelled')
D_COMM = tok('discount', 'Community rate'); D_RET = tok('discount', 'Returning client'); Q_OPEN = tok('qstatus', 'Open'); Q_SIGNED = tok('qstatus', 'Signed'); Q_LAPSED = tok('qstatus', 'Lapsed')
WD7 = ','.join(tok('wday', d) for d in WEEKDAYS)
Y12 = '">="&({today}-365)'

settings = [
    S('company', 'Your company name', 'text', COMPANY), S('reply_hours_target', 'Target hours to the first reply', 'int', REPLY_HOURS_TARGET),
    S('working_day_hours', 'Hours that count as one working day for a reply', 'int', 10), S('quote_valid_days', 'Days a quote stays valid', 'int', 14),
    S('follow_up_days', 'Days after a consultation before you follow up', 'int', 5), S('hold_days', 'Days you hold a due date for an enquirer', 'int', 7),
    S('balance_weeks', 'Weeks before the estimated due date the balance is due', 'int', BALANCE_WEEKS), S('instalment_days', 'Days between instalments', 'int', 28),
    S('oncall_before_days', 'On-call window starts, days before the estimated due date', 'int', ONCALL_BEFORE),
    S('oncall_after_days', 'On-call window ends, days after the estimated due date', 'int', ONCALL_AFTER),
    S('target_income_hour', 'Income per hour you want from a package, all hours', 'money', 30), S('min_booking_hours', 'Smallest postpartum booking, hours', 'int', MIN_BOOKING_HOURS),
    S('declined_max', 'Highest share of enquiries you accept to decline', 'pct', DECLINED_MAX), S('agency_cap_month', 'Most due dates you take in one month', 'int', 6),
    S('consult_slots_day', 'Consultation slots you can give on one day', 'int', 4), S('noshow_max', 'Highest consultation no-show rate you accept', 'pct', 0.10),
    S('community_discount', 'Community rate discount', 'pct', 0.15), S('returning_discount', 'Returning client discount', 'pct', 0.10),
    S('signed_target', 'Wanted contracts per enquiry', 'pct', 0.40),
]
assert 3 <= len(settings) <= 20

tables = []
# ---------------------------------------------------------------- 1 enquiries
tables.append(T('enquiries', 'Enquiries', 'Enquiries with first reply, consultation and outcome',
    'One row per enquiry: contact, service, due date wanted, source, hours to the first reply, status and the consultation and signing dates; the reply check and valid-until date fill in by themselves.', [
    C('enquiry_id', 'Enquiry ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), C('name', 'Name', 'text', 24), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
    LST('area', 'Area', 'area', 11), LST('service', 'Service wanted', 'service', 11), C('edd_wanted', 'Due date wanted', 'date', 11), LST('source', 'Source', 'source', 17),
    C('first_reply_hours', 'First reply, hours', 'num', 9), LST('status', 'Status', 'estatus', 17), LST('reason', 'Lost reason', 'lostreason', 17), LST('package_quoted', 'Package quoted', 'package', 20),
    C('quote', 'Quote', 'money', 11), C('consult_date', 'Consultation date', 'date', 11), C('signed_on', 'Signed on', 'date', 11), C('client_id', 'Client ID', 'text', 10),
    CA('days_to_consult', 'Days to consultation', 'int', 'IF({col:consult_date}>0,{col:consult_date}-{col:date},"")', 10),
    CA('reply_flag', 'Reply check', 'text', 'IF({col:first_reply_hours}="",%s,IF({col:first_reply_hours}<={set:reply_hours_target},%s,%s))' % (ca('No reply yet'), ca('Reply in time'), ca('Slow reply')), 13),
    CA('reply_band', 'Reply time band', 'text', 'IF({col:first_reply_hours}="",%s,IF({col:first_reply_hours}<=4,%s,IF({col:first_reply_hours}<=24,%s,IF({col:first_reply_hours}<=48,%s,%s))))' % (
        tok('rband', 'No reply yet'), tok('rband', 'Up to 4 hours'), tok('rband', '5 to 24 hours'), tok('rband', '25 to 48 hours'), tok('rband', 'Over 48 hours')), 14),
    CA('weekday', 'Weekday', 'text', 'CHOOSE(WEEKDAY({col:date},2),%s)' % WD7, 11),
    CA('due_month', 'Due month', 'date', 'DATE(YEAR({col:edd_wanted}),MONTH({col:edd_wanted}),1)', 11),
    CA('valid_until', 'Quote valid until', 'date', 'IF({col:quote}>0,MAX({col:date},{col:consult_date})+{set:quote_valid_days},"")', 11),
    CA('hold_until', 'Date held until', 'date', 'MAX({col:date},{col:consult_date})+{set:hold_days}', 11),
    CA('days_to_sign', 'Days to signing', 'int', 'IF({col:signed_on}>0,{col:signed_on}-{col:date},"")', 9),
    CA('declined', 'Declined', 'int', 'IF(AND({col:status}=%s,OR({col:reason}=%s,{col:reason}=%s)),1,0)' % (LOST, R_FULL, R_BACKUP), 8),
    CA('fast_reply', 'Replied in a working day', 'int', 'IF({col:first_reply_hours}="",0,IF({col:first_reply_hours}<={set:working_day_hours},1,0))', 9),
    COMPANY_C(), CA('reply_hours', 'Reply target, hours', 'int', '{set:reply_hours_target}', 9), OWNER_PH()],
    D.enquiries_d(), 900, [A('reply_flag', '= ' + ca('Slow reply'), 'warn'), A('reply_flag', '= ' + ca('No reply yet'), 'bad'), A('status', '= ' + SIGNED, 'good'), A('status', '= ' + LOST, 'warn')]))
# ---------------------------------------------------------------- 2 consultations
tables.append(T('consults', 'Consultations', 'Consultations booked, held and missed',
    'One row per consultation: date, doula, minutes, outcome and follow-up date; the days since, the follow-up check, the phone and the message fields fill in by themselves.', [
    C('consult_id', 'Consultation ID', 'text', 11, required=True), REF('enquiry_id', 'Enquiry', 'enquiries.enquiry_id', 10), C('date', 'Date', 'date', 11), C('name', 'Name', 'text', 24), LST('doula', 'Doula', 'doula', 17),
    C('minutes', 'Minutes', 'int', 8), LST('outcome', 'Outcome', 'outcome', 11), C('follow_up_on', 'Follow-up on', 'date', 11),
    CA('phone', 'Phone', 'text', LKT('enquiries.phone', 'enquiries.enquiry_id', 'enquiry_id'), 18),
    CA('held', 'Held', 'int', 'IF(OR({col:outcome}=%s,{col:outcome}=%s,{col:outcome}=%s),1,0)' % (O_SIGNED, O_THINK, O_DECL), 7),
    CA('days_since', 'Days since', 'int', 'IF({col:date}<={today},{today}-{col:date},"")', 9),
    CA('follow_flag', 'Follow-up check', 'text', 'IF({col:outcome}=%s,IF({col:date}>={today},%s,%s),IF(AND({col:outcome}=%s,{col:follow_up_on}>0),IF({col:follow_up_on}>{today},%s,IF({col:follow_up_on}={today},%s,IF({today}-{col:follow_up_on}<=30,%s,%s))),%s))' % (
        O_BOOKED, ca('Consultation coming up'), ca('Outcome missing'), O_THINK, ca('Follow-up planned'), ca('Follow up today'), ca('Follow-up overdue'), ca('Outcome recorded'), ca('Outcome recorded')), 15),
    CA('doula_phone', 'Doula phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH({col:doula},{range:team.name},0))&"","")', 18),
    COMPANY_C(), OWNER_PH()],
    D.consults_d(), 700, [A('follow_flag', '= ' + ca('Follow-up overdue'), 'bad'), A('follow_flag', '= ' + ca('Outcome missing'), 'bad'), A('follow_flag', '= ' + ca('Follow up today'), 'warn'), A('outcome', '= ' + O_SIGNED, 'good'), A('outcome', '= ' + O_NOSHOW, 'warn')]))
# ---------------------------------------------------------------- 3 clients
tables.append(T('clients', 'Clients', 'Clients signed, with doula and estimated due date',
    'One row per client (first name and family name, no medical detail): package, estimated due date (a date the client gives), doula, source and status; the due month fills in by itself.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 24), C('phone', 'Phone', 'text', 18), LST('kind', 'Kind', 'ckind', 12), LST('package', 'Package', 'package', 20), C('edd', 'Estimated due date', 'date', 11),
    LST('doula', 'Doula', 'doula', 17), LST('source', 'Source', 'source', 17), C('signed_on', 'Signed on', 'date', 11), LST('status', 'Status', 'cstatus', 15),
    CA('due_month', 'Due month', 'date', 'DATE(YEAR({col:edd}),MONTH({col:edd}),1)', 11), COMPANY_C()],
    D.clients_d(), 400, [A('status', '= ' + tok('cstatus', 'On call'), 'good'), A('status', '= ' + CS_CANCEL, 'warn')]))
# ---------------------------------------------------------------- 4 packages
PKQ = '{range:enquiries.package_quoted},{col:package},{range:enquiries.date},%s' % Y12
tables.append(T('packages', 'Packages', 'Packages with income per hour and win rate at quote',
    'One row per package: price, planned hours and deposit share; the income per hour of all hours, the price for your target and the quotes and contracts of 12 months fill in by themselves.', [
    C('package_id', 'Package ID', 'text', 10, required=True), C('package', 'Package', 'text', 24), C('kind', 'Kind', 'text', 11), C('price', 'Price', 'money', 11), C('birth_hours', 'Birth hours', 'int', 9),
    C('prenatal_visits', 'Prenatal visits', 'int', 9), C('postpartum_hours', 'Postpartum hours', 'int', 10), C('plan_hours', 'Plan hours', 'num', 9), C('deposit_pct', 'Deposit share', 'pct', 9),
    CA('income_hour', 'Income per hour', 'money', 'IF({col:plan_hours}>0,ROUND({col:price}/{col:plan_hours},1),0)', 10),
    CA('price_needed', 'Price for the target', 'money', 'ROUND({set:target_income_hour}*{col:plan_hours},0)', 11),
    CA('target_flag', 'Target check', 'text', 'IF({col:plan_hours}>=10,IF({col:income_hour}>={set:target_income_hour},%s,%s),%s)' % (c2('Above target, send the quote'), c2('Raise the price or cut hours'), c2('Above target, send the quote')), 24),
    CA('quotes_12m', 'Quotes, 12 months', 'int', 'COUNTIFS(%s)' % PKQ, 9),
    CA('signed_12m', 'Signed, 12 months', 'int', 'COUNTIFS(%s,{range:enquiries.status},%s)' % (PKQ, SIGNED), 9),
    CA('win_rate', 'Win rate at quote', 'pct', 'IF({col:quotes_12m}>=10,{col:signed_12m}/{col:quotes_12m},0)', 9)],
    D.packages_d(), 50, [A('target_flag', '= ' + c2('Raise the price or cut hours'), 'bad')]))
# ---------------------------------------------------------------- 5 pay rates, 6 areas, 7 sources
tables.append(T('pp_rates', 'Pay rates', 'Postpartum rate per hour by shift',
    'One row per shift: what the client pays per hour and the smallest booking in hours; the quote builder and your price answers read these.', [
    C('shift', 'Shift', 'text', 24, required=True), C('rate_hour', 'Rate per hour', 'money', 12), C('min_hours', 'Minimum hours', 'int', 10)],
    D.pay_rates_d(), 50))
tables.append(T('areas', 'Areas', 'Service areas with mileage rate and distance',
    'One row per service area: the mileage rate per mile and the usual miles one way; the quote builder and the travel check read these.', [
    C('area', 'Area', 'text', 30, required=True), C('mileage_rate', 'Mileage rate per mile', 'money', 12), C('miles_one_way', 'Miles one way', 'int', 10)],
    D.areas_d(), 50))
tables.append(T('sources', 'Sources', 'Enquiry sources with a thank-you gift',
    'One row per enquiry source: its kind and the value of a thank-you gift for a referral; the source tables and letters read these.', [
    LST('source', 'Source', 'source', 20, required=True), C('kind', 'Kind', 'text', 12), C('gift_value', 'Gift value', 'money', 11)],
    D.sources_d(), 50))
# ---------------------------------------------------------------- 8 team
tables.append(T('team', 'Team', 'Team and outside contacts with phones',
    'One row per person: the owner-doula, contracted and backup doulas, the admin and the outside contacts; message links and consultation lists read these phones.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 20), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26), COMPANY_C()],
    D.team_d(), 50))
# ---------------------------------------------------------------- 9 funnel by month
OWN = lambda num, den: 'IFERROR(SUMIFS({range:funnel.%s},{range:funnel.month},">="&EDATE({col:month},-6),{range:funnel.month},"<"&{col:month})/SUMIFS({range:funnel.%s},{range:funnel.month},">="&EDATE({col:month},-6),{range:funnel.month},"<"&{col:month}),0)' % (num, den)
tables.append(T('funnel', 'Funnel by Month', 'Funnel by month from enquiry to contract',
    'One row per month: enquiries, consultations booked, held and missed, contracts signed, lost and open, counted from the other sheets; the conversion, show rate and your own 6-month rates fill in.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('enquiries', 'Enquiries', 'int', 'COUNTIFS({range:enquiries.month},{col:month})', 10),
    CA('consult_booked', 'Consultations booked', 'int', 'COUNTIFS(%s)' % INM('consults.date', '{col:month}'), 11),
    CA('consult_held', 'Consultations held', 'int', 'COUNTIFS(%s,{range:consults.held},1)' % INM('consults.date', '{col:month}'), 10),
    CA('noshows', 'No-shows', 'int', 'COUNTIFS(%s,{range:consults.outcome},%s)' % (INM('consults.date', '{col:month}'), O_NOSHOW), 9),
    CA('signed', 'Contracts signed', 'int', 'COUNTIFS(%s)' % INM('enquiries.signed_on', '{col:month}'), 10),
    CA('lost', 'Lost', 'int', 'COUNTIFS({range:enquiries.month},{col:month},{range:enquiries.status},%s)' % LOST, 8),
    CA('open', 'Still open', 'int', 'COUNTIFS({range:enquiries.month},{col:month},{range:enquiries.status},"<>"&%s,{range:enquiries.status},"<>"&%s)' % (LOST, SIGNED), 9),
    CA('conversion', 'Conversion', 'pct', 'IF({col:enquiries}>0,COUNTIFS({range:enquiries.month},{col:month},{range:enquiries.status},%s)/{col:enquiries},0)' % SIGNED, 10),
    CA('show_rate', 'Show rate', 'pct', 'IF({col:consult_held}+{col:noshows}>0,{col:consult_held}/({col:consult_held}+{col:noshows}),0)', 9),
    CA('own_book', 'Own: booked per enquiry', 'pct', OWN('consult_booked', 'enquiries'), 10), CA('own_held', 'Own: held per booked', 'pct', OWN('consult_held', 'consult_booked'), 10),
    CA('own_sign', 'Own: signed per held', 'pct', OWN('signed', 'consult_held'), 10)],
    D.funnel_d(), 60, [A('conversion', '< {set:signed_target}', 'warn'), A('show_rate', '< 0.85', 'warn')]))
# ---------------------------------------------------------------- 10 source conversion
tables.append(T('source_conv', 'Source Conversion', 'Conversion of each enquiry source',
    'One row per enquiry source: the enquiries of the last 12 months and the share that became contracts, so you feed the sources that sign and not only the ones that write.', [
    LST('source', 'Source', 'source', 20, required=True),
    CA('enquiries', 'Enquiries, 12 months', 'int', 'COUNTIFS({range:enquiries.source},{col:source},{range:enquiries.date},%s)' % Y12, 12),
    CA('conversion', 'Conversion', 'pct', 'IF({col:enquiries}>0,COUNTIFS({range:enquiries.source},{col:source},{range:enquiries.status},%s,{range:enquiries.date},%s)/{col:enquiries},0)' % (SIGNED, Y12), 11)],
    D.source_conv_d(), 50))
# ---------------------------------------------------------------- 11 lost reasons
LOSTC = '{range:enquiries.status},%s,{range:enquiries.reason},{col:reason},{range:enquiries.date},%s' % (LOST, Y12)
tables.append(T('lost_reasons', 'Lost Reasons', 'Lost enquiries by reason with quote value lost',
    'One row per reason an enquiry was lost: the lost enquiries and the value of the quotes lost in the last 12 months, counted from Enquiries.', [
    LST('reason', 'Reason', 'lostreason', 20, required=True), CA('lost_enquiries', 'Lost enquiries, 12 months', 'int', 'COUNTIFS(%s)' % LOSTC, 12),
    CA('quote_value_lost', 'Quote value lost', 'money', 'SUMIFS({range:enquiries.quote},%s)' % LOSTC, 12)],
    D.lost_reasons_d(), 50))
# ---------------------------------------------------------------- 12 reply time bands
tables.append(T('reply_bands', 'Reply Time Bands', 'First reply time against contracts',
    'One row per band of hours to the first reply: the enquiries of the last 12 months and the share that became contracts, so you see what a slow reply costs.', [
    LST('band', 'Reply time band', 'rband', 18, required=True), CA('enquiries', 'Enquiries, 12 months', 'int', 'COUNTIFS({range:enquiries.reply_band},{col:band},{range:enquiries.date},%s)' % Y12, 12),
    CA('signed_share', 'Share signed', 'pct', 'IF({col:enquiries}>0,COUNTIFS({range:enquiries.reply_band},{col:band},{range:enquiries.status},%s,{range:enquiries.date},%s)/{col:enquiries},0)' % (SIGNED, Y12), 11)],
    D.reply_bands_d(), 50))
# ---------------------------------------------------------------- 13 quotes
E = lambda c: LKT('enquiries.' + c, 'enquiries.enquiry_id', 'enquiry_id')
PKL = lambda c: 'IFERROR(INDEX({range:packages.%s},MATCH({col:package},{range:packages.package},0)),0)' % c
tables.append(T('quotes', 'Quotes', 'Quotes with discount, add-ons, travel, deposit, instalments',
    'One row per quote: enquiry, package, discount, add-ons, travel fee, instalments and status; the total, deposit, balance date, instalment dates, valid-until date and expiry check fill in.', [
    C('quote_id', 'Quote ID', 'text', 9, required=True), REF('enquiry_id', 'Enquiry', 'enquiries.enquiry_id', 10), C('quote_date', 'Quote date', 'date', 11), LST('package', 'Package', 'package', 20),
    LST('discount', 'Discount', 'discount', 16), C('addons', 'Add-ons', 'money', 10), C('travel_fee', 'Travel fee', 'money', 10), C('instalments', 'Instalments', 'int', 9), LST('status', 'Status', 'qstatus', 10),
    CA('name', 'Name', 'text', E('name'), 24), CA('phone', 'Phone', 'text', E('phone'), 18), CA('area', 'Area', 'text', E('area'), 11),
    CA('edd_wanted', 'Due date wanted', 'date', 'IFERROR(INDEX({range:enquiries.edd_wanted},MATCH({col:enquiry_id},{range:enquiries.enquiry_id},0)),0)', 11),
    CA('list_price', 'List price', 'money', PKL('price'), 10), CA('deposit_pct', 'Deposit share', 'pct', PKL('deposit_pct'), 9),
    CA('discount_amount', 'Discount amount', 'money', 'ROUND({col:list_price}*IF({col:discount}=%s,{set:community_discount},IF({col:discount}=%s,{set:returning_discount},0)),0)' % (D_COMM, D_RET), 10),
    CA('quote_total', 'Quote total', 'money', '{col:list_price}-{col:discount_amount}+{col:addons}+{col:travel_fee}', 11),
    CA('deposit', 'Deposit', 'money', 'ROUND({col:quote_total}*{col:deposit_pct},0)', 10), CA('balance', 'Balance', 'money', '{col:quote_total}-{col:deposit}', 10),
    CA('balance_due', 'Balance due date', 'date', 'IF({col:balance}>0,{col:edd_wanted}-7*{set:balance_weeks},"")', 11),
    CA('instalment', 'Instalment amount', 'money', 'IF({col:balance}>0,ROUND({col:balance}/MAX(1,{col:instalments}),0),0)', 11),
    CA('last_inst', 'Last instalment due', 'date', 'IF(AND({col:balance}>0,{col:instalments}>1),{col:edd_wanted}-{set:oncall_before_days}-2,"")', 11),
    CA('first_inst', 'First instalment due', 'date', 'IF({col:last_inst}="","",{col:last_inst}-({col:instalments}-1)*{set:instalment_days})', 11),
    CA('valid_until', 'Valid until', 'date', '{col:quote_date}+{set:quote_valid_days}', 11), CA('days_left', 'Days left', 'int', '{col:valid_until}-{today}', 8),
    CA('expiry_flag', 'Expiry check', 'text', 'IF({col:status}<>%s,%s,IF({col:days_left}<0,%s,IF({col:days_left}<=7,%s,%s)))' % (Q_OPEN, ca('Quote closed'), ca('Quote lapsed'), ca('Ends within 7 days'), ca('Quote valid')), 17),
    COMPANY_C(), OWNER_PH(), ADMIN_PH()],
    D.quotes_d(), 400, [A('expiry_flag', '= ' + ca('Ends within 7 days'), 'warn'), A('expiry_flag', '= ' + ca('Quote lapsed'), 'bad'), A('status', '= ' + Q_SIGNED, 'good')]))
# ---------------------------------------------------------------- 14 follow-up list
EQ = lambda c: LKN('enquiries.' + c, 'enquiries.enquiry_id', 'enquiry_id')
CD = EQ('consult_date')
tables.append(T('followups', 'Follow-up List', 'Open enquiries and what to do next',
    'One row per open enquiry or newly signed client you follow up: the days since the last step and the next step (call, write, remind, send the quote, chase or welcome) fill in by themselves.', [
    REF('enquiry_id', 'Enquiry', 'enquiries.enquiry_id', 10, required=True),
    CA('name', 'Name', 'text', E('name'), 24), CA('status', 'Status', 'text', E('status'), 17),
    CA('last_step', 'Last step', 'date', 'MAX(%s,IF(AND(%s>0,%s<={today}),%s,0),%s)' % (EQ('date'), CD, CD, CD, EQ('signed_on')), 11),
    CA('days_since', 'Days since the last step', 'int', '{today}-{col:last_step}', 10),
    CA('next_step', 'Next step', 'text', 'IF({col:status}=%s,IF(%s="",%s,IF({col:days_since}>={set:follow_up_days},%s,%s)),IF({col:status}=%s,IF(AND(%s>={today},%s<={today}+2),%s,%s),IF({col:status}=%s,IF({col:days_since}>=1,%s,%s),IF({col:status}=%s,IF({col:days_since}>={set:follow_up_days},%s,%s),IF({col:status}=%s,IF({col:days_since}<=14,%s,%s),%s)))))' % (
        NEWE, LKT('enquiries.first_reply_hours', 'enquiries.enquiry_id', 'enquiry_id'), ns('Call today'), ns('Write today'), ns('Not due yet'),
        BOOKE, CD, CD, ns('Remind about the consultation'), ns('Not due yet'), HELDE, ns('Send the quote'), ns('Not due yet'),
        SENTE, ns('Chase the quote'), ns('Not due yet'), SIGNED, ns('Welcome the new client'), ns('Not due yet'), ns('Not due yet')), 24)],
    D.followups_d(), 100, [A('next_step', '= ' + ns('Call today'), 'bad'), A('next_step', '= ' + ns('Chase the quote'), 'warn'), A('next_step', '= ' + ns('Send the quote'), 'warn'), A('next_step', '= ' + ns('Welcome the new client'), 'good')]))
# ---------------------------------------------------------------- 15 consultation calendar
tables.append(T('consult_cal', 'Consultation Calendar', 'Consultations booked and free slots for the next 21 days',
    'One row per day ahead: which doula takes consultations; the weekday, the consultations booked, the free slots and the day check fill in by themselves.', [
    C('date', 'Date', 'date', 11, required=True), LST('doula', 'Doula on duty', 'doula', 17),
    CA('weekday', 'Weekday', 'text', 'CHOOSE(WEEKDAY({col:date},2),%s)' % WD7, 11),
    CA('booked', 'Consultations booked', 'int', 'COUNTIFS({range:consults.date},{col:date},{range:consults.outcome},%s)' % O_BOOKED, 11),
    CA('free_slots', 'Free slots', 'int', 'MAX(0,{set:consult_slots_day}-{col:booked})', 9),
    CA('slot_flag', 'Day check', 'text', 'IF({col:free_slots}>0,%s,%s)' % (ca('Slots free'), ca('Fully booked')), 12), ADMIN_PH(), COMPANY_C()],
    D.consult_cal_d(), 60, [A('slot_flag', '= ' + ca('Fully booked'), 'warn'), A('booked', '> 0', 'good')]))
# ---------------------------------------------------------------- 16 demand by due month
WANT = INM('enquiries.edd_wanted', '{col:due_month}') + ',{range:enquiries.service},"<>"&' + SV_PP
tables.append(T('demand', 'Demand by Due Month', 'Due dates wanted against clients booked and your limit',
    'One row per due month ahead: enquiries wanting it, clients booked and open quotes (birth and combined only); the load, the spaces left against your limit and the waitlist check fill in.', [
    C('due_month', 'Due month', 'date', 11, required=True),
    CA('enquiries_wanting', 'Enquiries wanting it', 'int', 'COUNTIFS(%s)' % WANT, 10),
    CA('clients_booked', 'Clients booked', 'int', 'COUNTIFS(%s,{range:clients.status},"<>"&%s,{range:clients.kind},"<>"&%s)' % (INM('clients.edd', '{col:due_month}'), CS_CANCEL, KD_PP), 10),
    CA('open_quotes', 'Open quotes', 'int', 'COUNTIFS(%s)-COUNTIFS(%s,{range:enquiries.status},%s)-COUNTIFS(%s,{range:enquiries.status},%s)-COUNTIFS(%s,{range:enquiries.status},%s)' % (WANT, WANT, LOST, WANT, SIGNED, WANT, NEWE), 9),
    CA('load', 'Load', 'int', '{col:clients_booked}+{col:open_quotes}', 8), CA('spaces', 'Spaces left', 'int', '{set:agency_cap_month}-{col:load}', 9),
    CA('cap_flag', 'Date check', 'text', 'IF({col:load}>{set:agency_cap_month},%s,IF({col:load}<=0.6*{set:agency_cap_month},%s,%s))' % (c2('Waitlist these dates'), c2('Open more dates'), c2('Enough for now')), 18), OWNER_PH(), COMPANY_C()],
    D.demand_d(), 60, [A('cap_flag', '= ' + c2('Waitlist these dates'), 'bad'), A('cap_flag', '= ' + c2('Open more dates'), 'warn'), A('spaces', '< 0', 'bad')]))
# ---------------------------------------------------------------- 17 consultations by doula
DCW = '{range:consults.doula},{col:doula},{range:consults.date},%s' % Y12
tables.append(T('doula_cons', 'Consultations by Doula', 'Consultations held and signed share by doula',
    'One row per doula: the consultations held in the last 12 months and the share that became contracts, counted from Consultations.', [
    LST('doula', 'Doula', 'doula', 20, required=True), CA('consultations', 'Held, 12 months', 'int', 'COUNTIFS(%s,{range:consults.held},1)' % DCW, 11),
    CA('signed_share', 'Share signed', 'pct', 'IF({col:consultations}>0,COUNTIFS(%s,{range:consults.outcome},%s)/{col:consultations},0)' % (DCW, O_SIGNED), 11)],
    D.doula_cons_d(), 50))
# ---------------------------------------------------------------- 18 lost value by month
tables.append(T('lost_month', 'Lost Value by Month', 'Lost enquiries, quote value lost and declined share by month',
    'One row per month: the enquiries, the lost enquiries and the value of the quotes lost; the declined share (date full or no backup) against your setting fills in by itself.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('enquiries', 'Enquiries', 'int', 'COUNTIFS({range:enquiries.month},{col:month})', 9),
    CA('lost_enquiries', 'Lost enquiries', 'int', 'COUNTIFS({range:enquiries.month},{col:month},{range:enquiries.status},%s)' % LOST, 9),
    CA('quote_value_lost', 'Quote value lost', 'money', 'SUMIFS({range:enquiries.quote},{range:enquiries.month},{col:month},{range:enquiries.status},%s)' % LOST, 12),
    CA('declined_share', 'Declined share', 'pct', 'IF({col:enquiries}>0,SUMIFS({range:enquiries.declined},{range:enquiries.month},{col:month})/{col:enquiries},0)', 10),
    OWNER_PH(), COMPANY_C()],
    D.lost_month_d(), 60, [A('declined_share', '> {set:declined_max}', 'bad')]))
# ---------------------------------------------------------------- 19 discount use
tables.append(T('discount_use', 'Discount Use', 'Price given up by discount and area',
    'One row per discount and area: the price given up on contracts signed in the last 12 months, counted from Quotes.', [
    LST('discount', 'Discount', 'discount', 18, required=True), LST('area', 'Area', 'area', 12),
    CA('price_given_up', 'Price given up, 12 months', 'money', 'SUMIFS({range:quotes.discount_amount},{range:quotes.discount},{col:discount},{range:quotes.area},{col:area},{range:quotes.status},%s,{range:quotes.quote_date},">="&EDATE(%s,-12))' % (Q_SIGNED, MS), 13)],
    D.discount_use_d(), 50))
# ---------------------------------------------------------------- 20 enquiries by service and area
tables.append(T('svc_area', 'Enquiries by Service and Area', 'Enquiries by service and area',
    'One row per service and area: the enquiries of the last 12 months, counted from Enquiries, for the service mix and the travel checks.', [
    LST('service', 'Service', 'service', 14, required=True), LST('area', 'Area', 'area', 12),
    CA('enquiries', 'Enquiries, 12 months', 'int', 'COUNTIFS({range:enquiries.service},{col:service},{range:enquiries.area},{col:area},{range:enquiries.date},%s)' % Y12, 12)],
    D.svc_area_d(), 50))
assert len(tables) == 20, len(tables)
