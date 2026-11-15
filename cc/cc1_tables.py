"""Childcare center suite part 1: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc1_lists import *
import cc1_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def OWNER_PH(): return CA('owner_phone', 'Owner-director phone', 'text', '"%s"' % D.OWNER_PHONE, 18)
def DIR_PH(): return CA('director_phone', 'Assistant director phone', 'text', '"%s"' % D.DIRECTOR_PHONE, 18)
def CENTER(): return CA('center', 'Center', 'text', '{set:company}', 22)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; NXT = 'DATE(YEAR({today}),MONTH({today})+1,1)'
YES = '{list:yesno.yes}'
ENR = tok('estatus', 'Enrolled'); LOST = tok('estatus', 'Lost'); NEW = tok('estatus', 'New'); TB = tok('estatus', 'Tour booked'); TH = tok('estatus', 'Tour held'); APP = tok('estatus', 'Applied'); WLS = tok('estatus', 'Waitlist')
HELD = tok('tourstatus', 'Held'); NOSHOW = tok('tourstatus', 'No-show'); BOOKED = tok('tourstatus', 'Booked')
WW = tok('waitstatus', 'Waiting'); WO = tok('waitstatus', 'Offered'); WS = tok('waitstatus', 'Started'); WX = tok('waitstatus', 'Withdrawn')


def RATE_OF(room, sched): return 'SUMIFS({range:rates.weekly_rate},{range:rates.room},%s,{range:rates.schedule},%s)' % (room, sched)
def INM(rng_, col): return '{range:%s},">="&%s,{range:%s},"<"&EDATE(%s,1)' % (rng_, col, rng_, col)

settings = [
    S('company', 'Your center name', 'text', COMPANY), S('reply_hours_target', 'Target hours to the first reply', 'int', 24),
    S('occupancy_target', 'Wanted occupancy, children booked of licensed places', 'pct', 0.90), S('offer_days', 'Days a family has to answer a place offer', 'int', 7),
    S('recheck_days', 'Days on the waiting list before you re-confirm', 'int', 90), S('stale_days', 'Days without a step before an enquiry is stale', 'int', 7),
    S('close_after_days', 'Days without an answer before you close an enquiry', 'int', 30), S('tour_slots_day', 'Tour slots you can give on one day', 'int', 3),
    S('tour_minutes', 'Minutes one tour takes', 'int', 45), S('start_window_days', 'Days ahead that count as starting now', 'int', 45),
    S('fill_weeks', 'Weeks ahead used to value a free place', 'int', 26), S('weeks_open', 'Weeks a year the center is open and billing', 'int', 50),
    S('payback_months', 'Months a marketing spend should take to pay back', 'int', 6), S('target_conversion', 'Wanted enrolments per enquiry', 'pct', 0.12),
    S('no_show_target', 'Highest tour no-show rate you accept', 'pct', 0.10), S('reg_fee', 'Registration fee', 'money', REG_FEE),
    S('sibling_pct', 'Sibling discount, lower fee for a second child', 'pct', SIBLING_PCT), S('staff_pct', 'Staff discount', 'pct', STAFF_PCT),
    S('open_day_date', 'Date of the next open day', 'date', ahead(21)),
]
assert 3 <= len(settings) <= 20

tables = []
# ---------------------------------------------------------------- 1 enquiries
tables.append(T('enquiries', 'Enquiries', 'Enquiries with first reply, tour and outcome',
    'One row per enquiry: contact, wanted room and start, source, hours to the first reply, status and the dates of the tour, application and enrolment; the days to a tour, the reply check, the weekly value and the message fields fill in by themselves.', [
    C('enquiry_id', 'Enquiry ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), C('name', 'Name', 'text', 22), C('phone', 'Phone', 'text', 18),
    C('child_age_months', 'Child age, months', 'int', 9), LST('want_room', 'Wanted room', 'room', 11), LST('want_schedule', 'Wanted schedule', 'schedule', 13), C('want_start', 'Wanted start', 'date', 11),
    LST('source', 'Source', 'source', 15), C('first_reply_hours', 'First reply, hours', 'int', 9), LST('status', 'Status', 'estatus', 12), LST('reason', 'Lost reason', 'lostreason', 11),
    C('tour_date', 'Tour date', 'date', 11), C('applied_on', 'Applied on', 'date', 11), C('enrolled_on', 'Enrolled on', 'date', 11),
    CA('days_to_tour', 'Days to tour', 'int', 'IF({col:tour_date}>0,{col:tour_date}-{col:date},"")', 9),
    CA('reply_flag', 'Reply check', 'text', 'IF({col:first_reply_hours}="",%s,IF({col:first_reply_hours}<={set:reply_hours_target},%s,%s))' % (ca('No reply yet'), ca('Reply in time'), ca('Slow reply')), 13),
    CA('reply_band', 'Reply time band', 'text', 'IF({col:first_reply_hours}="",%s,IF({col:first_reply_hours}<=4,%s,IF({col:first_reply_hours}<=24,%s,IF({col:first_reply_hours}<=48,%s,%s))))' % (
        tok('rband', 'No reply yet'), tok('rband', 'Up to 4 hours'), tok('rband', '5 to 24 hours'), tok('rband', '25 to 48 hours'), tok('rband', 'Over 48 hours')), 14),
    CA('weekly_value', 'Weekly value of the days wanted', 'money', RATE_OF('{col:want_room}', '{col:want_schedule}'), 13),
    CA('center', 'Center', 'text', '{set:company}', 22), CA('reply_hours', 'Reply target, hours', 'int', '{set:reply_hours_target}', 9), CA('open_day', 'Open day', 'date', '{set:open_day_date}', 11),
    CA('reg_fee', 'Registration fee', 'money', '{set:reg_fee}', 11), OWNER_PH()],
    D.enquiries_d(), 700, [A('reply_flag', '= ' + ca('Slow reply'), 'warn'), A('reply_flag', '= ' + ca('No reply yet'), 'bad'), A('status', '= ' + ENR, 'good'), A('status', '= ' + LOST, 'warn')]))
# ---------------------------------------------------------------- 2 tours
tables.append(T('tours', 'Tours', 'Tours booked, held, missed and cancelled',
    'One row per tour: date, family, who showed them round, status, source and whether an application followed; the held flag, the outcome check and the message fields fill in by themselves.', [
    C('tour_id', 'Tour ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), REF('enquiry_id', 'Enquiry', 'enquiries.enquiry_id', 10), C('name', 'Name', 'text', 22), C('phone', 'Phone', 'text', 18),
    REF('staff', 'Showed round', 'team.name', 20), LST('status', 'Status', 'tourstatus', 11), LST('source', 'Source', 'source', 15), C('applied', 'Applied', 'bool', 9), LST('room', 'Room', 'room', 11),
    CA('held', 'Held', 'int', 'IF({col:status}=%s,1,0)' % HELD, 7),
    CA('outcome_flag', 'Outcome check', 'text', 'IF({col:status}=%s,IF({col:date}<{today},%s,%s),%s)' % (BOOKED, ca('Outcome missing'), ca('Tour coming up'), ca('Outcome recorded')), 14),
    CENTER(), OWNER_PH(), DIR_PH()],
    D.tours_d(), 500, [A('outcome_flag', '= ' + ca('Outcome missing'), 'bad'), A('status', '= ' + NOSHOW, 'warn'), A('status', '= ' + HELD, 'good')]))
# ---------------------------------------------------------------- 3 waitlist
OFF_DUE = '{col:offered_on}+{set:offer_days}'
tables.append(T('waitlist', 'Waiting List', 'Waiting list with days waiting and weekly value',
    'One row per family on the waiting list (families waiting for a place): room, schedule, wanted start, priority and the offer dates; the days waiting, the weekly value of the days wanted, the offer due date and the list check fill in by themselves.', [
    C('wait_id', 'Waiting ID', 'text', 9, required=True), REF('enquiry_id', 'Enquiry', 'enquiries.enquiry_id', 10), C('name', 'Name', 'text', 22), C('phone', 'Phone', 'text', 18), C('child_age_months', 'Child age, months', 'int', 9),
    LST('room', 'Room', 'room', 11), LST('schedule', 'Schedule', 'schedule', 13), C('want_start', 'Wanted start', 'date', 11), C('added_on', 'Added on', 'date', 11), C('offered_on', 'Offered on', 'date', 11),
    C('started_on', 'Started on', 'date', 11), LST('priority', 'Priority', 'priority', 9), LST('status', 'Status', 'waitstatus', 11),
    CA('days_waiting', 'Days waiting', 'int', 'IF(OR({col:status}=%s,{col:status}=%s),{today}-{col:added_on},IF({col:started_on}>0,{col:started_on}-{col:added_on},0))' % (WW, WO), 9),
    CA('weekly_value', 'Weekly value of the days wanted', 'money', RATE_OF('{col:room}', '{col:schedule}'), 13),
    CA('offer_due', 'Offer answer due', 'date', 'IF({col:offered_on}>0,%s,"")' % OFF_DUE, 11),
    CA('wait_flag', 'List check', 'text', 'IF({col:status}=%s,IF({col:days_waiting}>{set:recheck_days},%s,%s),IF({col:status}=%s,IF(%s<{today},%s,%s),IF({col:status}=%s,%s,%s)))' % (
        WW, ca('Re-confirm now'), ca('On the list'), WO, OFF_DUE, ca('Offer overdue'), ca('Offer open'), WS, ca('Started'), ca('Withdrawn')), 14),
    CENTER()],
    D.waitlist_d(), 200, [A('wait_flag', '= ' + ca('Re-confirm now'), 'warn'), A('wait_flag', '= ' + ca('Offer overdue'), 'bad'), A('wait_flag', '= ' + ca('Started'), 'good')]))
# ---------------------------------------------------------------- 4 marketing
tables.append(T('marketing', 'Marketing Spend', 'Marketing spend with enquiries and enrolments',
    'One row per month and spend item (online directory, website, roadside sign, flyers, open day, referral reward): cost, enquiries it brought and children enrolled; the cost per enquiry and per enrolled child fill in by themselves.', [
    C('campaign_id', 'Spend ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('kind', 'Kind', 'mkind', 15), LST('source', 'Source', 'source', 15), C('cost', 'Cost', 'money', 11),
    C('enquiries', 'Enquiries', 'int', 10), C('enrolled', 'Enrolled', 'int', 10),
    CA('cost_per_enquiry', 'Cost per enquiry', 'money', 'IF({col:enquiries}>0,{col:cost}/{col:enquiries},0)', 11),
    CA('cost_per_enrolled', 'Cost per enrolled child', 'money', 'IF({col:enrolled}>0,{col:cost}/{col:enrolled},0)', 12), CENTER(), OWNER_PH()],
    D.marketing_d(), 300, [A('cost_per_enrolled', '> 300', 'warn')]))
# ---------------------------------------------------------------- 5 children
tables.append(T('children', 'Children', 'Children with room, schedule and start date',
    'One row per child (first name and family name only): family, room, schedule, days a week, start and end date and status; the weekly rate, the place-days enrolled to date and the message fields fill in by themselves.', [
    C('child_id', 'Child ID', 'text', 9, required=True), C('child', 'Child', 'text', 22), C('family', 'Family', 'text', 22), C('guardian', 'Parent or guardian', 'text', 22), C('phone', 'Phone', 'text', 18),
    LST('room', 'Room', 'room', 11), LST('schedule', 'Schedule', 'schedule', 13), C('days', 'Days a week', 'int', 8), C('start_date', 'Start date', 'date', 11), C('end_date', 'End date', 'date', 11), LST('status', 'Status', 'cstatus', 12),
    CA('weekly_rate', 'Weekly rate', 'money', RATE_OF('{col:room}', '{col:schedule}'), 11),
    CA('place_days', 'Place-days to date', 'int', 'MAX(0,ROUND({col:days}*(IF({col:end_date}>0,{col:end_date},{today})-{col:start_date})/7,0))', 11),
    CA('teacher_phone', 'Lead teacher phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH({col:room},{range:team.room},0))&"","")', 18),
    CA('cook_phone', 'Cook phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH(%s,{range:team.role},0))&"","")' % tok('role', 'Cook'), 18), CENTER()],
    D.children_d(), 300, [A('status', '= ' + tok('cstatus', 'Starting soon'), 'good')]))
# ---------------------------------------------------------------- 6 rates
tables.append(T('rates', 'Rates', 'Weekly rates by room and schedule',
    'One row per room and schedule: the weekly rate this year and last year, days, hours and the day rate; the rise, the monthly equivalent and the sibling and staff rates fill in by themselves.', [
    C('rate_id', 'Rate ID', 'text', 9, required=True), LST('room', 'Room', 'room', 11), LST('schedule', 'Schedule', 'schedule', 13), C('weekly_rate', 'Weekly rate', 'money', 11), C('last_year_rate', 'Last year rate', 'money', 11),
    C('days', 'Days', 'int', 7), C('hours_day', 'Hours a day', 'num', 9), C('day_rate', 'Day rate', 'money', 10),
    CA('rise_pct', 'Rise this year', 'pct', 'IF({col:last_year_rate}>0,{col:weekly_rate}/{col:last_year_rate}-1,0)', 9),
    CA('monthly_rate', 'Monthly equivalent', 'money', 'ROUND({col:weekly_rate}*52/12,0)', 11), CA('sibling_rate', 'Weekly rate with sibling discount', 'money', 'ROUND({col:weekly_rate}*(1-{set:sibling_pct}),0)', 13),
    CA('staff_rate', 'Weekly rate with staff discount', 'money', 'ROUND({col:weekly_rate}*(1-{set:staff_pct}),0)', 13)],
    D.rates_d(), 50))
# ---------------------------------------------------------------- 7 rooms
tables.append(T('rooms', 'Rooms', 'Rooms with licensed places and ratio',
    'One row per room: licensed places and the ratio, the number of children each staff member may care for (check your local rules). A home daycare keeps one row.', [
    LST('room', 'Room', 'room', 12, required=True), C('capacity', 'Licensed places', 'int', 11), C('ratio', 'Ratio, children per staff', 'int', 11)],
    D.rooms_d(), 50))
# ---------------------------------------------------------------- 8 places by room and month
BK = 'COUNTIFS({range:children.room},{col:room},{range:children.start_date},"<="&{col:month})-COUNTIFS({range:children.room},{col:room},{range:children.start_date},"<="&{col:month},{range:children.end_date},"<"&{col:month})'
tables.append(T('places', 'Places by Room and Month', 'Free places by room and month',
    'One row per room and month: licensed places, children booked on the 1st, leavers expected and starters booked; the free places at month end, the occupancy and the weekly revenue left empty fill in by themselves.', [
    C('place_id', 'Place ID', 'text', 9, required=True), LST('room', 'Room', 'room', 11), C('month', 'Month', 'date', 11),
    CA('capacity', 'Licensed places', 'int', 'SUMIFS({range:rooms.capacity},{range:rooms.room},{col:room})', 10), CA('booked', 'Children booked on the 1st', 'int', BK, 11),
    CA('leavers', 'Leavers expected', 'int', 'COUNTIFS({range:children.room},{col:room},{range:children.end_date},">="&{col:month},{range:children.end_date},"<="&EOMONTH({col:month},0))', 10),
    CA('starters', 'Starters booked', 'int', 'COUNTIFS({range:children.room},{col:room},{range:children.start_date},">"&{col:month},{range:children.start_date},"<="&EOMONTH({col:month},0))', 10),
    CA('free_places', 'Free places at month end', 'int', '{col:capacity}-{col:booked}+{col:leavers}-{col:starters}', 11),
    CA('free_flag', 'Free', 'int', 'IF({col:free_places}>0,1,0)', 6),
    CA('occupancy', 'Occupancy at month end', 'pct', 'IF({col:capacity}>0,({col:capacity}-{col:free_places})/{col:capacity},0)', 11),
    CA('weekly_left', 'Weekly revenue left empty', 'money', 'MAX(0,{col:free_places})*%s' % RATE_OF('{col:room}', tok('schedule', '5 full days')), 12)],
    D.places_d(), 200, [A('free_places', '<= 0', 'good'), A('occupancy', '< {set:occupancy_target}', 'warn')]))
# ---------------------------------------------------------------- 9 funnel by month
tables.append(T('funnel', 'Funnel by Month', 'Tour funnel by month from enquiry to start',
    'One row per month: enquiries, tours booked, held and missed, applications and children starting, all counted from the other sheets; the enrolments per enquiry and the tour show rate fill in by themselves.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('enquiries', 'Enquiries', 'int', 'COUNTIFS({range:enquiries.month},{col:month})', 10),
    CA('tours_booked', 'Tours booked', 'int', 'COUNTIFS(%s)' % INM('tours.date', '{col:month}'), 10),
    CA('tours_held', 'Tours held', 'int', 'COUNTIFS(%s,{range:tours.status},%s)' % (INM('tours.date', '{col:month}'), HELD), 10),
    CA('noshows', 'Tour no-shows', 'int', 'COUNTIFS(%s,{range:tours.status},%s)' % (INM('tours.date', '{col:month}'), NOSHOW), 10),
    CA('applications', 'Applications', 'int', 'COUNTIFS(%s)' % INM('applications.applied_on', '{col:month}'), 10),
    CA('enrolled', 'Children starting', 'int', 'COUNTIFS(%s)' % INM('children.start_date', '{col:month}'), 10),
    CA('conversion', 'Starts per enquiry', 'pct', 'IF({col:enquiries}>0,{col:enrolled}/{col:enquiries},0)', 10),
    CA('show_rate', 'Tour show rate', 'pct', 'IF({col:tours_held}+{col:noshows}>0,{col:tours_held}/({col:tours_held}+{col:noshows}),0)', 10),
    CA('own_book', 'Own: tours booked per enquiry', 'pct', 'IFERROR(SUMIFS({range:funnel.tours_booked},{range:funnel.month},">="&EDATE({col:month},-6),{range:funnel.month},"<"&{col:month})/SUMIFS({range:funnel.enquiries},{range:funnel.month},">="&EDATE({col:month},-6),{range:funnel.month},"<"&{col:month}),0)', 10),
    CA('own_held', 'Own: held per booked', 'pct', 'IFERROR(SUMIFS({range:funnel.tours_held},{range:funnel.month},">="&EDATE({col:month},-6),{range:funnel.month},"<"&{col:month})/SUMIFS({range:funnel.tours_booked},{range:funnel.month},">="&EDATE({col:month},-6),{range:funnel.month},"<"&{col:month}),0)', 10),
    CA('own_app', 'Own: applications per held', 'pct', 'IFERROR(SUMIFS({range:funnel.applications},{range:funnel.month},">="&EDATE({col:month},-6),{range:funnel.month},"<"&{col:month})/SUMIFS({range:funnel.tours_held},{range:funnel.month},">="&EDATE({col:month},-6),{range:funnel.month},"<"&{col:month}),0)', 10),
    CA('own_enr', 'Own: starts per application', 'pct', 'IFERROR(SUMIFS({range:funnel.enrolled},{range:funnel.month},">="&EDATE({col:month},-6),{range:funnel.month},"<"&{col:month})/SUMIFS({range:funnel.applications},{range:funnel.month},">="&EDATE({col:month},-6),{range:funnel.month},"<"&{col:month}),0)', 10)],
    D.funnel_d(), 60, [A('show_rate', '< 0.85', 'warn'), A('conversion', '< {set:target_conversion}', 'warn')]))
# ---------------------------------------------------------------- 10 source value
tables.append(T('sources', 'Source Value', 'Value of each enquiry source',
    'One row per enquiry source: enquiries in the last 12 months and the yearly tuition of a child enrolled from it, so you rank sources by revenue and not by counts.', [
    LST('source', 'Source', 'source', 16, required=True),
    CA('enquiries', 'Enquiries, 12 months', 'int', 'COUNTIFS({range:enquiries.source},{col:source},{range:enquiries.date},">="&({today}-365))', 12),
    CA('revenue_child', 'Yearly revenue per enrolled child', 'money', 'IFERROR(AVERAGEIFS({range:enquiries.weekly_value},{range:enquiries.source},{col:source},{range:enquiries.status},%s)*{set:weeks_open},0)' % ENR, 14)],
    D.sources_d(), 50))
# ---------------------------------------------------------------- 11 lost reasons
LOSTC = '{range:enquiries.status},%s,{range:enquiries.reason},{col:reason},{range:enquiries.date},">="&({today}-365)' % LOST
tables.append(T('lost', 'Lost Reasons', 'Lost enquiries by reason',
    'One row per reason a family chose elsewhere: the lost enquiries and the weekly tuition lost in the last 12 months.', [
    LST('reason', 'Reason', 'lostreason', 14, required=True), CA('lost_enquiries', 'Lost enquiries, 12 months', 'int', 'COUNTIFS(%s)' % LOSTC, 12),
    CA('weekly_lost', 'Weekly tuition lost', 'money', 'SUMIFS({range:enquiries.weekly_value},%s)' % LOSTC, 12)],
    D.lost_d(), 50))
# ---------------------------------------------------------------- 12 reply bands
tables.append(T('reply_bands', 'Reply Time Bands', 'First reply time against enrolment',
    'One row per band of hours to the first reply: the enquiries in the band and the share of them that enrolled, so you see what a slow reply costs.', [
    LST('band', 'Reply time band', 'rband', 15, required=True), CA('enquiries', 'Enquiries', 'int', 'COUNTIFS({range:enquiries.reply_band},{col:band})', 10),
    CA('enrolled_share', 'Share enrolled', 'pct', 'IF({col:enquiries}>0,COUNTIFS({range:enquiries.reply_band},{col:band},{range:enquiries.status},%s)/{col:enquiries},0)' % ENR, 10)],
    D.bands_d(), 50))
# ---------------------------------------------------------------- 13 offers
tables.append(T('offers', 'Offer Log', 'Place offers with answer and days to answer',
    'One row per place offered to a waiting family: the offer date, the answer and the answer date; the days to answer, the answer due date, the start date and the offer check fill in by themselves.', [
    C('offer_id', 'Offer ID', 'text', 9, required=True), REF('wait_id', 'Waiting ID', 'waitlist.wait_id', 10), C('offered_on', 'Offered on', 'date', 11), LST('answer', 'Answer', 'offerans', 10), C('answered_on', 'Answered on', 'date', 11),
    CA('name', 'Name', 'text', LKT('waitlist.name', 'waitlist.wait_id', 'wait_id'), 22), CA('phone', 'Phone', 'text', LKT('waitlist.phone', 'waitlist.wait_id', 'wait_id'), 18),
    CA('room', 'Room', 'text', LKT('waitlist.room', 'waitlist.wait_id', 'wait_id'), 11),
    CA('offer_due', 'Answer due', 'date', '{col:offered_on}+{set:offer_days}', 11),
    CA('days_to_answer', 'Days to answer, or open', 'int', 'IF({col:answered_on}>0,{col:answered_on}-{col:offered_on},{today}-{col:offered_on})', 11),
    CA('started_on', 'Started on', 'date', 'IF(%s=0,"",%s)' % (LKN('waitlist.started_on', 'waitlist.wait_id', 'wait_id'), LKN('waitlist.started_on', 'waitlist.wait_id', 'wait_id')), 11),
    CA('offer_flag', 'Offer check', 'text', 'IF({col:answered_on}>0,%s,IF({col:offer_due}<{today},%s,IF({col:offer_due}-{today}<=2,%s,%s)))' % (ca('Answered'), ca('Release the place'), ca('Chase today'), ca('Waiting for answer')), 14),
    CENTER(), OWNER_PH()],
    D.offers_d(), 100, [A('offer_flag', '= ' + ca('Release the place'), 'bad'), A('offer_flag', '= ' + ca('Chase today'), 'warn'), A('answer', '= ' + tok('offerans', 'Declined'), 'warn')]))
# ---------------------------------------------------------------- 14 tour calendar
tables.append(T('tour_cal', 'Tour Calendar', 'Tour calendar for the next 15 open days',
    'One row per open day ahead: who shows families round; the weekday, the tours booked, the free slots and the day check fill in by themselves.', [
    C('date', 'Date', 'date', 11, required=True), REF('staff', 'Showing round', 'team.name', 20),
    CA('weekday', 'Weekday', 'text', 'CHOOSE(WEEKDAY({col:date},2),%s)' % ','.join(tok('wday', d) for d in WDAY7), 11),
    CA('tours_booked', 'Tours booked', 'int', 'COUNTIFS({range:tours.date},{col:date},{range:tours.status},%s)' % BOOKED, 10),
    CA('free_slots', 'Free slots', 'int', 'MAX(0,{set:tour_slots_day}-{col:tours_booked})', 9),
    CA('slot_flag', 'Day check', 'text', 'IF({col:free_slots}>0,%s,%s)' % (ca('Slots free'), ca('Fully booked')), 12)],
    D.tour_cal_d(), 60, [A('slot_flag', '= ' + ca('Fully booked'), 'warn'), A('tours_booked', '> 0', 'good')]))
# ---------------------------------------------------------------- 15 applications
tables.append(T('applications', 'Applications', 'Applications with forms and deposit',
    'One row per application: room, schedule, wanted start, whether the forms are back and the deposit is paid (a payment held to keep a place) and the status; the days since applying and the paperwork check fill in by themselves.', [
    REF('enquiry_id', 'Enquiry', 'enquiries.enquiry_id', 10, required=True), C('name', 'Name', 'text', 22), C('applied_on', 'Applied on', 'date', 11), LST('room', 'Room', 'room', 11), LST('schedule', 'Schedule', 'schedule', 13),
    C('want_start', 'Wanted start', 'date', 11), C('forms_back', 'Forms back', 'bool', 9), C('deposit_paid', 'Deposit paid', 'bool', 9), LST('status', 'Status', 'appstatus', 14),
    CA('days_since', 'Days since applying', 'int', '{today}-{col:applied_on}', 10),
    CA('paperwork_flag', 'Paperwork check', 'text', 'IF(AND({col:forms_back}=%s,{col:deposit_paid}=%s),%s,IF({col:forms_back}=%s,%s,IF({col:deposit_paid}=%s,%s,%s)))' % (YES, YES, ca('Complete'), YES, ca('Deposit missing'), YES, ca('Forms missing'), ca('Forms and deposit missing')), 16),
    CA('phone', 'Phone', 'text', LKT('enquiries.phone', 'enquiries.enquiry_id', 'enquiry_id'), 18), CA('weekly_value', 'Weekly value of the days wanted', 'money', RATE_OF('{col:room}', '{col:schedule}'), 13), CENTER()],
    D.applications_d(), 300, [A('paperwork_flag', '= ' + ca('Forms missing'), 'warn'), A('paperwork_flag', '= ' + ca('Forms and deposit missing'), 'bad'), A('status', '= ' + tok('appstatus', 'Enrolled'), 'good')]))
# ---------------------------------------------------------------- 16 fill candidates
W = lambda c: LKT('waitlist.' + c, 'waitlist.wait_id', 'wait_id')
tables.append(T('fill', 'Fill Candidates', 'Waiting families ranked to fill a free place',
    'One row per family waiting or holding an offer: room, weekly value and wanted start from the Waiting List; the free places in the room, the revenue over the weeks ahead, the rank for the whole center and for the room fill in by themselves.', [
    REF('wait_id', 'Waiting ID', 'waitlist.wait_id', 10, required=True),
    CA('name', 'Waiting family', 'text', W('name'), 22), CA('room', 'Room', 'text', W('room'), 11), CA('schedule', 'Schedule', 'text', W('schedule'), 13), CA('status', 'Status', 'text', W('status'), 11),
    CA('weekly_value', 'Weekly value', 'money', LKN('waitlist.weekly_value', 'waitlist.wait_id', 'wait_id'), 11),
    CA('want_start', 'Wanted start', 'date', LKN('waitlist.want_start', 'waitlist.wait_id', 'wait_id'), 11),
    CA('days_to_start', 'Days to start', 'int', '{col:want_start}-{today}', 9),
    CA('free_now', 'Free places in the room', 'int', 'SUMIFS({range:places.free_places},{range:places.room},{col:room},{range:places.month},%s)' % MS, 11),
    CA('room_fit', 'Room fit', 'text', 'IF({col:free_now}>0,%s,%s)' % (ca('Room has a free place'), ca('Room is full')), 18),
    CA('horizon_value', 'Revenue over the weeks ahead', 'money', 'ROUND({col:weekly_value}*MAX(0,({today}+7*{set:fill_weeks}-MAX({col:want_start},{today}))/7),0)', 13),
    CA('start_flag', 'Can start', 'text', 'IF({col:free_now}<=0,%s,IF({col:days_to_start}<={set:start_window_days},%s,%s))' % (ca('No place yet'), ca('Can start now'), ca('Starts later')), 14),
    CA('score', 'Fill score', 'num', 'IF(AND({col:status}=%s,{col:free_now}>0),{col:horizon_value},0)-VALUE(RIGHT({col:wait_id},3))/1000000' % WW, 11),
    CA('rank', 'Rank, whole center', 'int', 'COUNTIFS({range:fill.score},">"&{col:score})+1', 9),
    CA('room_rank', 'Rank in the room', 'int', 'COUNTIFS({range:fill.room},{col:room},{range:fill.score},">"&{col:score})+1', 9),
    CA('room_key', 'Room key', 'text', '{col:room}&"|"&{col:room_rank}', 12), CENTER(), OWNER_PH()],
    D.fill_d(), 80, [A('rank', '= 1', 'good'), A('start_flag', '= ' + ca('Can start now'), 'good'), A('room_fit', '= ' + ca('Room is full'), 'warn')]))
# ---------------------------------------------------------------- 17 demand by room and start month
WANT = '{range:enquiries.want_room},{col:room},{range:enquiries.want_start},">="&{col:month},{range:enquiries.want_start},"<"&EDATE({col:month},1)'
WLM = '{range:waitlist.room},{col:room},{range:waitlist.want_start},">="&{col:month},{range:waitlist.want_start},"<"&EDATE({col:month},1)'
tables.append(T('demand', 'Demand by Room and Start Month', 'Wanted starts against free places by room and month',
    'One row per room and start month: the open enquiries that want to start then, the waiting families and the free places at that month end; the balance and the recruit check fill in by themselves.', [
    LST('room', 'Room', 'room', 11, required=True), C('month', 'Start month', 'date', 11),
    CA('wanted_starts', 'Open enquiries wanting to start', 'int', 'COUNTIFS(%s)-COUNTIFS(%s,{range:enquiries.status},%s)-COUNTIFS(%s,{range:enquiries.status},%s)' % (WANT, WANT, LOST, WANT, ENR), 12),
    CA('waiting_families', 'Waiting families', 'int', 'COUNTIFS(%s,{range:waitlist.status},%s)+COUNTIFS(%s,{range:waitlist.status},%s)' % (WLM, WW, WLM, WO), 10),
    CA('free_places', 'Free places at month end', 'int', 'SUMIFS({range:places.free_places},{range:places.room},{col:room},{range:places.month},{col:month})', 11),
    CA('balance', 'Free places less waiting families', 'int', '{col:free_places}-{col:waiting_families}', 11),
    CA('gap_flag', 'Recruit check', 'text', 'IF({col:balance}>0,%s,%s)' % (ca('Recruit more'), ca('Enough waiting')), 14)],
    D.demand_d(), 100, [A('gap_flag', '= ' + ca('Recruit more'), 'warn'), A('balance', '< 0', 'bad')]))
# ---------------------------------------------------------------- 18 stale enquiries
EQ = lambda c: LKN('enquiries.' + c, 'enquiries.enquiry_id', 'enquiry_id')
TD = EQ('tour_date')
tables.append(T('stale', 'Stale Enquiries', 'Open enquiries and what to do next',
    'One row per open enquiry or waiting family you follow up: the days since the last step and the next step (call, write, remind, chase or close) fill in by themselves from the enquiry.', [
    REF('enquiry_id', 'Enquiry', 'enquiries.enquiry_id', 10, required=True),
    CA('name', 'Name', 'text', LKT('enquiries.name', 'enquiries.enquiry_id', 'enquiry_id'), 22), CA('status', 'Status', 'text', LKT('enquiries.status', 'enquiries.enquiry_id', 'enquiry_id'), 12),
    CA('last_step', 'Last step', 'date', 'MAX(%s,IF(AND(%s>0,%s<={today}),%s,0),%s,%s)' % (EQ('date'), TD, TD, TD, EQ('applied_on'), LKN('waitlist.added_on', 'waitlist.enquiry_id', 'enquiry_id')), 11),
    CA('days_since', 'Days since the last step', 'int', '{today}-{col:last_step}', 10),
    CA('next_step', 'Next step', 'text', 'IF({col:days_since}>={set:close_after_days},%s,IF({col:status}=%s,IF({col:days_since}>=1,%s,%s),IF({col:status}=%s,IF(AND(%s>={today},%s<={today}+2),%s,%s),IF({col:status}=%s,IF({col:days_since}>=2,%s,%s),IF({col:status}=%s,IF({col:days_since}>=3,%s,%s),IF({col:days_since}>={set:recheck_days},%s,%s))))))' % (
        ns('Close the enquiry'), NEW, ns('Call today'), ns('Write today'), TB, TD, TD, ns('Remind about the tour'), ns('Not due yet'), TH, ns('Send the next steps'), ns('Not due yet'),
        APP, ns('Chase the forms'), ns('Not due yet'), ns('Re-confirm the place'), ns('Not due yet')), 20)],
    D.stale_d(), 100, [A('next_step', '= ' + ns('Close the enquiry'), 'bad'), A('next_step', '= ' + ns('Call today'), 'warn'), A('next_step', '= ' + ns('Chase the forms'), 'warn')]))
# ---------------------------------------------------------------- 19 marketing by kind
tables.append(T('kinds', 'Marketing by Kind', 'Marketing cost and enrolments by kind',
    'One row per kind of spend: the cost and the children enrolled in the last 12 months, counted from Marketing Spend.', [
    LST('kind', 'Kind', 'mkind', 16, required=True),
    CA('cost', 'Cost, 12 months', 'money', 'SUMIFS({range:marketing.cost},{range:marketing.kind},{col:kind},{range:marketing.month},">="&EDATE(%s,-12))' % MS, 12),
    CA('enrolled', 'Enrolled, 12 months', 'int', 'SUMIFS({range:marketing.enrolled},{range:marketing.kind},{col:kind},{range:marketing.month},">="&EDATE(%s,-12))' % MS, 12)],
    D.kinds_d(), 50))
# ---------------------------------------------------------------- 20 team
tables.append(T('team', 'Team', 'Team with roles and phones',
    'One row per person: staff, the owner-director, the assistant director and outside contacts, with the room a teacher leads; the message links and tour lists read these phones.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 22), LST('role', 'Role', 'role', 18), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26), C('room', 'Room or duty', 'text', 26)],
    D.team_d(), 50))
assert len(tables) == 20, len(tables)
