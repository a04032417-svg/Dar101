"""Short-term rental host suite part 6: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr6_lists import *
import sr6_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IF(%s=0,"",%s)' % (LKN(src, kc, my), LKN(src, kc, my))
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def GPH(src='bookings', kc='booking_id', my='booking_id'): return CA('guest_phone', 'Guest phone', 'text', LKT(src + '.guest_phone' if src == 'bookings' else src + '.phone', src + '.' + kc, my), 18)
def OWNP(my='unit'): return CA('owner_phone', 'Owner phone', 'text', LKT('units.owner_phone', 'units.name', my), 18)
def COH(): return CA('cohost_phone', 'Co-host phone', 'text', '"%s"' % D.COHOST_PHONE, 18)
def HOST(): return CA('host_phone', 'Host phone', 'text', '"%s"' % D.OWNER_PHONE, 18)
YES = tok('yn', 'Yes'); NO = tok('yn', 'No')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'

settings = [
    S('company', 'Your company name', 'text', COMPANY), S('min_rating', 'Lowest acceptable 90-day rating of a unit', 'num', 4.2), S('target_rating', 'Wanted average rating of all units', 'num', 4.6),
    S('response_target_min', 'Wanted first reply time to a guest, in minutes', 'int', 30), S('warn_days', 'Days ahead to warn of a check-in or a deadline', 'int', 7),
    S('reply_days', 'Days allowed to reply to a review', 'int', 2), S('complaint_days', 'Days allowed to resolve a complaint', 'int', 3), S('review_window', 'Days a review request stays open', 'int', 14),
    S('winback_days', 'Days since the last stay before a win-back offer', 'int', 180), S('welcome_days', 'Days before a welcome book section is reviewed', 'int', 180),
    S('template_days', 'Days before a message template is reviewed', 'int', 270), S('free_hours', 'Hours of early check-in or late checkout that are free', 'num', 1),
    S('hour_share', 'Share of the nightly rate charged for each extra hour', 'pct', 0.08), S('comp_moderate', 'Compensation for a moderate complaint, share of nights', 'pct', 0.15),
    S('comp_serious', 'Compensation for a serious complaint, share of nights', 'pct', 0.35), S('checkin_time', 'Usual check-in time', 'text', '15:00'), S('checkout_time', 'Usual checkout time', 'text', '11:00'),
    S('low_stars', 'Highest rating counted as a low review', 'int', 3), S('survey_good', 'Survey score of a happy guest, out of 10', 'int', 8),
]
assert 3 <= len(settings) <= 20

tables = [
    T('reviews', 'Reviews', 'Reviews with ratings, topic and reply',
      'One row per review: unit, guest, stars, four sub-ratings, topic and reply date; the level, days to reply or waiting, reply status and sub-rating average fill in by themselves.', [
        C('review_id', 'Review ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('booking_id', 'Booking ID', 'text', 10), REF('unit', 'Unit', 'units.name', 26), LST('unit_type', 'Unit type', 'utype', 11),
        LST('city', 'City', 'city', 10), LST('channel', 'Channel', 'chan', 11), C('guest', 'Guest', 'text', 24), C('rating', 'Rating', 'int', 8), LST('stars', 'Stars', 'stars', 9), C('cleanliness', 'Cleanliness', 'int', 11),
        C('communication', 'Communication', 'int', 13), C('location', 'Location', 'int', 9), C('value', 'Value', 'int', 8), LST('topic', 'Topic', 'rtopic', 17), LST('replied', 'Replied', 'yn', 9), C('reply_on', 'Reply on', 'date', 11),
        CA('level', 'Level', 'text', 'IF({col:rating}>=5,%s,IF({col:rating}>{set:low_stars},%s,%s))' % (ca('Five stars'), ca('Four stars'), ca('Three stars or less')), 20),
        CA('avg_sub', 'Sub-rating average', 'num', 'ROUND(({col:cleanliness}+{col:communication}+{col:location}+{col:value})/4,2)', 11),
        CA('days_to_reply', 'Days to reply or waiting', 'int', 'IF(OR({col:replied}<>%s,{col:reply_on}=0),{today}-{col:date},{col:reply_on}-{col:date})' % YES, 10),
        CA('reply_status', 'Reply status', 'text', 'IF({col:replied}=%s,IF({col:reply_on}-{col:date}<={set:reply_days},%s,%s),IF({today}-{col:date}<={set:reply_days},%s,%s))' % (
            YES, ca('Replied on time'), ca('Replied late'), ca('Waiting for reply'), ca('Waiting too long')), 18),
        CA('replied_num', 'Replied (1 or 0)', 'int', 'IF({col:replied}=%s,1,0)' % YES, 9), CA('max_stars', 'Best rating', 'int', '5', 8),
        GPH(), OWNP(), COH(), HOST()],
      D.reviews_d(), 700, [A('level', '= ' + ca('Three stars or less'), 'bad'), A('level', '= ' + ca('Five stars'), 'good'), A('reply_status', '= ' + ca('Waiting too long'), 'bad'), A('reply_status', '= ' + ca('Replied late'), 'warn')]),
    T('gmsg', 'Guest Messages', 'Guest message log with reply times',
      'One row per guest message: booking, kind, who answered and the minutes to the first reply; the reply check, the minutes over the target and the phone numbers fill in by themselves.', [
        C('message_id', 'Message ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('booking_id', 'Booking ID', 'text', 10), REF('unit', 'Unit', 'units.name', 26), C('guest', 'Guest', 'text', 24),
        LST('kind', 'Kind', 'msgk', 20), LST('channel', 'Channel', 'chan', 11), REF('handled_by', 'Handled by', 'team.name', 22), C('response_min', 'Reply minutes', 'int', 11), LST('resolved', 'Resolved', 'yn', 9),
        CA('reply_flag', 'Reply check', 'text', 'IF({col:response_min}<={set:response_target_min},%s,%s)' % (ca('Within target'), ca('Over target')), 15),
        CA('over_by', 'Minutes over target', 'int', 'MAX(0,{col:response_min}-{set:response_target_min})', 11), GPH(), COH(), HOST()],
      D.gmsg_d(), 900, [A('reply_flag', '= ' + ca('Over target'), 'warn'), A('response_min', '> 120', 'bad'), A('resolved', '= ' + NO, 'warn')]),
    T('guests', 'Guests', 'Guest profiles with stays and spend',
      'One row per guest: country, stays, nights, spend and first and last stay; the repeat check, spend per stay, days since the last stay, win-back check and reviews left fill in by themselves.', [
        C('guest_id', 'Guest ID', 'text', 10, required=True), C('guest', 'Guest', 'text', 24), LST('country', 'Country', 'country', 15), C('phone', 'Phone', 'text', 18), C('stays', 'Stays', 'int', 8), C('nights', 'Nights', 'int', 8),
        C('spend', 'Spend', 'money', 11), C('first_stay', 'First stay', 'date', 11), C('last_stay', 'Last stay', 'date', 11), LST('channel', 'Channel', 'chan', 11),
        CA('repeat_flag', 'Repeat check', 'text', 'IF({col:stays}>=3,%s,IF({col:stays}>=2,%s,%s))' % (ca('Loyal guest'), ca('Repeat guest'), ca('First-time guest')), 16),
        CA('avg_spend', 'Spend per stay', 'money', 'IF({col:stays}>0,{col:spend}/{col:stays},0)', 11), CA('spend_night', 'Spend per night', 'money', 'IF({col:nights}>0,{col:spend}/{col:nights},0)', 11),
        CA('days_since', 'Days since last stay', 'int', '{today}-{col:last_stay}', 11),
        CA('win_flag', 'Win-back check', 'text', 'IF(AND({col:stays}>=2,{today}-{col:last_stay}>={set:winback_days}),%s,%s)' % (ca('Win-back due'), ca('Not due')), 14),
        CA('reviews_left', 'Reviews left', 'int', 'COUNTIFS({range:reviews.guest},{col:guest})', 9), CA('prefs_noted', 'Preferences noted', 'int', 'COUNTIFS({range:prefs.guest},{col:guest})', 11), HOST()],
      D.guests_d(), 500, [A('repeat_flag', '= ' + ca('Loyal guest'), 'good'), A('win_flag', '= ' + ca('Win-back due'), 'warn')]),
    T('bookings', 'Bookings', 'Bookings with guest, dates and review check',
      'One row per booking: guest, unit, channel, dates, guests and amount; the nights, lead time, review check, message count and complaints fill in by themselves.', [
        C('booking_id', 'Booking ID', 'text', 10, required=True), C('guest', 'Guest', 'text', 24), C('guest_phone', 'Guest phone', 'text', 18), REF('unit', 'Unit', 'units.name', 26), LST('city', 'City', 'city', 10),
        LST('channel', 'Channel', 'chan', 11), C('booked_on', 'Booked on', 'date', 11), C('check_in', 'Check-in', 'date', 11), C('check_out', 'Check-out', 'date', 11), C('guests', 'Guests', 'int', 8),
        C('nightly_rate', 'Nightly rate', 'money', 11), C('gross', 'Amount', 'money', 11), LST('status', 'Status', 'bstatus', 11),
        CA('nights', 'Nights', 'int', '{col:check_out}-{col:check_in}', 8), CA('lead_days', 'Lead days', 'int', '{col:check_in}-{col:booked_on}', 9),
        CA('checkin_time', 'Check-in time', 'text', '{set:checkin_time}', 11), CA('checkout_time', 'Checkout time', 'text', '{set:checkout_time}', 11),
        CA('review_flag', 'Review check', 'text', 'IF(COUNTIFS({range:reviews.booking_id},{col:booking_id})>0,%s,IF(OR({col:status}=%s,{col:check_out}>{today}),%s,IF({col:check_out}>={today}-{set:review_window},%s,%s)))' % (
            ca('Reviewed'), tok('bstatus', 'Cancelled'), ca('Stay not finished'), ca('Waiting for review'), ca('Not reviewed')), 18),
        CA('msgs', 'Messages', 'int', 'COUNTIFS({range:gmsg.booking_id},{col:booking_id})', 9), CA('complaints_n', 'Complaints', 'int', 'COUNTIFS({range:complaints.booking_id},{col:booking_id})', 10), COH()],
      D.bookings_d(), 800, [A('review_flag', '= ' + ca('Not reviewed'), 'warn'), A('review_flag', '= ' + ca('Reviewed'), 'good'), A('complaints_n', '> 0', 'bad'), A('check_in', '= {today}', 'good')]),
    T('units', 'Units', 'Units with ratings, replies and complaints',
      'One row per unit: type, city, owner and listing date; reviews, ratings, unanswered reviews, complaints, reply minutes and the welcome book status fill in by themselves.', [
        C('unit_id', 'Unit ID', 'text', 9, required=True), C('name', 'Name', 'text', 26), LST('unit_type', 'Unit type', 'utype', 11), LST('city', 'City', 'city', 10), C('bedrooms', 'Bedrooms', 'int', 9), C('owner', 'Owner', 'text', 22),
        C('owner_phone', 'Owner phone', 'text', 18), C('since', 'Listed since', 'date', 11),
        CA('reviews_90d', 'Reviews, 90 days', 'int', 'COUNTIFS({range:reviews.unit},{col:name},{range:reviews.date},">="&({today}-90))', 11),
        CA('avg_rating_90d', 'Rating, 90 days', 'num', 'IFERROR(AVERAGEIFS({range:reviews.rating},{range:reviews.unit},{col:name},{range:reviews.date},">="&({today}-90)),0)', 11),
        CA('avg_clean_90d', 'Cleanliness, 90 days', 'num', 'IFERROR(AVERAGEIFS({range:reviews.cleanliness},{range:reviews.unit},{col:name},{range:reviews.date},">="&({today}-90)),0)', 11),
        CA('reviews_12m', 'Reviews, 12 months', 'int', 'COUNTIFS({range:reviews.unit},{col:name},{range:reviews.date},">="&({today}-365))', 11),
        CA('avg_rating_12m', 'Rating, 12 months', 'num', 'IFERROR(AVERAGEIFS({range:reviews.rating},{range:reviews.unit},{col:name},{range:reviews.date},">="&({today}-365)),0)', 11),
        CA('unanswered', 'Reviews without a reply', 'int', 'COUNTIFS({range:reviews.unit},{col:name},{range:reviews.replied},%s)' % NO, 11),
        CA('rating_flag', 'Rating check', 'text', 'IF({col:avg_rating_90d}<{set:min_rating},%s,%s)' % (ca('Below minimum'), ca('Above minimum')), 14),
        CA('complaints_90d', 'Complaints, 90 days', 'int', 'COUNTIFS({range:complaints.unit},{col:name},{range:complaints.date},">="&({today}-90))', 11),
        CA('msgs_90d', 'Messages, 90 days', 'int', 'COUNTIFS({range:gmsg.unit},{col:name},{range:gmsg.date},">="&({today}-90))', 11),
        CA('avg_reply_90d', 'Reply minutes, 90 days', 'int', 'IFERROR(AVERAGEIFS({range:gmsg.response_min},{range:gmsg.unit},{col:name},{range:gmsg.date},">="&({today}-90)),0)', 11),
        CA('wb_sections', 'Welcome book sections', 'int', 'COUNTIFS({range:welcome.unit},{col:name})', 11),
        CA('wb_updated', 'Welcome book updated', 'date', 'IF(SUMPRODUCT(MAX(({range:welcome.unit}={col:name})*{range:welcome.updated_on}))=0,"",SUMPRODUCT(MAX(({range:welcome.unit}={col:name})*{range:welcome.updated_on})))', 11),
        COH(), HOST()],
      D.units_d(), 50, [A('rating_flag', '= ' + ca('Below minimum'), 'bad'), A('unanswered', '> 5', 'warn'), A('complaints_90d', '> 4', 'warn')]),
    T('checkins', 'Check-in Records', 'Check-in records with arrival and issues',
      'One row per check-in: planned and real arrival time, how the guest got in, any issue and who handled it; minutes late, the issue check and the guest phone fill in by themselves.', [
        C('ci_id', 'Record ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('booking_id', 'Booking ID', 'text', 10), REF('unit', 'Unit', 'units.name', 26), C('planned', 'Planned time', 'time', 10), C('arrival', 'Arrival time', 'time', 10),
        LST('method', 'Access method', 'amethod', 18), LST('issue', 'Issue', 'cissue', 24), REF('handled_by', 'Handled by', 'team.name', 22),
        CA('guest', 'Guest', 'text', LKT('bookings.guest', 'bookings.booking_id', 'booking_id'), 24), CA('late_min', 'Minutes after planned', 'int', 'ROUND(({col:arrival}-{col:planned})*1440,0)', 11),
        CA('issue_flag', 'Issue check', 'text', 'IF({col:issue}=%s,%s,%s)' % (tok('cissue', 'No issue'), ca('Smooth check-in'), ca('Issue at check-in')), 16), GPH(), COH()],
      D.checkins_d(), 400, [A('issue_flag', '= ' + ca('Issue at check-in'), 'bad'), A('late_min', '> 180', 'warn')]),
    T('complaints', 'Complaints', 'Complaints with action and compensation',
      'One row per complaint: booking, topic, severity, action, compensation and the date it was resolved; the days to resolve, the status and the share of the stay given back fill in by themselves.', [
        C('cp_id', 'Complaint ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('booking_id', 'Booking ID', 'text', 10), REF('unit', 'Unit', 'units.name', 26), C('guest', 'Guest', 'text', 24),
        LST('topic', 'Topic', 'rtopic', 17), LST('severity', 'Severity', 'sev', 10), LST('action', 'Action', 'cact', 20), C('compensation', 'Compensation', 'money', 12), C('resolved_on', 'Resolved on', 'date', 11),
        REF('handled_by', 'Handled by', 'team.name', 22),
        CA('days_to_resolve', 'Days to resolve or open', 'int', 'IF({col:resolved_on}=0,{today}-{col:date},{col:resolved_on}-{col:date})', 12),
        CA('status', 'Status', 'text', 'IF({col:resolved_on}=0,IF({today}-{col:date}>{set:complaint_days},%s,%s),IF({col:resolved_on}-{col:date}<={set:complaint_days},%s,%s))' % (
            ca('Open and late'), ca('Open'), ca('Resolved on time'), ca('Resolved late')), 16),
        CA('is_resolved', 'Resolved (1 or 0)', 'int', 'IF({col:resolved_on}=0,0,1)', 9), CA('stay_amount', 'Stay amount', 'money', LKN('bookings.gross', 'bookings.booking_id', 'booking_id'), 11),
        CA('comp_pct', 'Share given back', 'pct', 'IF({col:stay_amount}>0,{col:compensation}/{col:stay_amount},0)', 11), GPH(), OWNP(), COH(), HOST()],
      D.complaints_d(), 200, [A('status', '= ' + ca('Open and late'), 'bad'), A('status', '= ' + ca('Resolved late'), 'warn'), A('severity', '= ' + tok('sev', 'Serious'), 'bad'), A('status', '= ' + ca('Resolved on time'), 'good')]),
    T('prefs', 'Guest Preferences', 'Guest preferences noted for next stays',
      'One row per preference noted about a guest: what they like, the unit and the date; the stays, last stay and phone are looked up from Guests.', [
        C('pf_id', 'Note ID', 'text', 9, required=True), C('guest', 'Guest', 'text', 24), C('preference', 'Preference', 'text', 30), REF('unit', 'Unit', 'units.name', 26), C('noted_on', 'Noted on', 'date', 11),
        CA('stays', 'Stays', 'int', LKN('guests.stays', 'guests.guest', 'guest'), 8), CA('last_stay', 'Last stay', 'date', LKD('guests.last_stay', 'guests.guest', 'guest'), 11),
        CA('repeat_flag', 'Repeat check', 'text', 'IF({col:stays}>=3,%s,IF({col:stays}>=2,%s,%s))' % (ca('Loyal guest'), ca('Repeat guest'), ca('First-time guest')), 16), GPH('guests', 'guest', 'guest')],
      D.prefs_d(), 200),
    T('replies', 'Review Replies', 'Review replies with speed and tone',
      'One row per reply written to a review: the review, date, who wrote it, length and tone; the rating, unit, topic, days to reply and the speed check are looked up from Reviews.', [
        C('rp_id', 'Reply ID', 'text', 9, required=True), C('review_id', 'Review ID', 'text', 10), C('replied_on', 'Replied on', 'date', 11), REF('replied_by', 'Replied by', 'team.name', 22), C('length', 'Words', 'int', 8), C('tone', 'Tone', 'text', 22),
        CA('rating', 'Rating', 'int', LKN('reviews.rating', 'reviews.review_id', 'review_id'), 8), CA('unit', 'Unit', 'text', LKT('reviews.unit', 'reviews.review_id', 'review_id'), 26),
        CA('topic', 'Topic', 'text', LKT('reviews.topic', 'reviews.review_id', 'review_id'), 17),
        CA('days_to_reply', 'Days to reply', 'int', '{col:replied_on}-%s' % LKN('reviews.date', 'reviews.review_id', 'review_id'), 10),
        CA('speed_flag', 'Speed check', 'text', 'IF({col:days_to_reply}<={set:reply_days},%s,%s)' % (ca('Replied on time'), ca('Replied late')), 16)],
      D.replies_d(), 300, [A('speed_flag', '= ' + ca('Replied late'), 'warn'), A('rating', '<= 3', 'bad')]),
    T('templates', 'Message Templates', 'Message templates with uses and review date',
      'One row per ready-made guest message: kind, language, how often it was used and when it was last edited; the age, the share of all uses and the review check fill in by themselves.', [
        C('tpl_id', 'Template ID', 'text', 10, required=True), C('template', 'Template', 'text', 30), LST('kind', 'Kind', 'msgk', 20), C('language', 'Language', 'text', 12), C('uses', 'Uses', 'int', 8),
        C('last_edited', 'Last edited', 'date', 11), REF('edited_by', 'Edited by', 'team.name', 22),
        CA('age_days', 'Age in days', 'int', '{today}-{col:last_edited}', 10), CA('use_share', 'Share of uses', 'pct', 'IF(SUM({range:templates.uses})>0,{col:uses}/SUM({range:templates.uses}),0)', 10),
        CA('review_flag', 'Review check', 'text', 'IF({col:age_days}>{set:template_days},%s,%s)' % (ca('Update due'), ca('Up to date')), 13)],
      D.templates_d(), 60, [A('review_flag', '= ' + ca('Update due'), 'warn')]),
    T('welcome', 'Welcome Book', 'Welcome book sections by unit',
      'One row per section of a unit welcome book: the unit, section, last update and who keeps it; the age, the review check and the city fill in by themselves.', [
        C('wb_id', 'Section ID', 'text', 9, required=True), REF('unit', 'Unit', 'units.name', 26), C('section', 'Section', 'text', 24), C('updated_on', 'Updated on', 'date', 11), REF('maintained_by', 'Kept by', 'team.name', 22),
        CA('age_days', 'Age in days', 'int', '{today}-{col:updated_on}', 10), CA('wb_flag', 'Review check', 'text', 'IF({col:age_days}>{set:welcome_days},%s,%s)' % (ca('Update due'), ca('Up to date')), 13),
        CA('city', 'City', 'text', LKT('units.city', 'units.name', 'unit'), 10)],
      D.welcome_d(), 100, [A('wb_flag', '= ' + ca('Update due'), 'warn')]),
    T('surveys', 'Guest Surveys', 'Guest surveys with score and return intent',
      'One row per short survey after a stay: score out of 10, one comment and whether the guest would return; the guest, phone and mood fill in by themselves.', [
        C('sv_id', 'Survey ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('booking_id', 'Booking ID', 'text', 10), REF('unit', 'Unit', 'units.name', 26), C('score', 'Score', 'int', 8), C('comment', 'Comment', 'text', 30),
        LST('would_return', 'Would return', 'yn', 11),
        CA('guest', 'Guest', 'text', LKT('bookings.guest', 'bookings.booking_id', 'booking_id'), 24),
        CA('mood', 'Mood', 'text', 'IF({col:score}>={set:survey_good},%s,IF({col:score}>=6,%s,%s))' % (cb('Happy guest'), cb('Neutral guest'), cb('Unhappy guest')), 14),
        CA('return_num', 'Would return (1 or 0)', 'int', 'IF({col:would_return}=%s,1,0)' % YES, 9), GPH()],
      D.surveys_d(), 300, [A('mood', '= ' + cb('Unhappy guest'), 'bad'), A('mood', '= ' + cb('Happy guest'), 'good')]),
    T('referrals', 'Referrals', 'Guest referrals with reward status',
      'One row per guest who referred a friend: the referrer, the friend, the booking made and the reward; the status, the booking amount and the reward share fill in by themselves.', [
        C('rf_id', 'Referral ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('guest', 'Referrer', 'text', 24), C('referred', 'Friend referred', 'text', 24), C('booking_id', 'Booking ID', 'text', 10), C('reward', 'Reward', 'money', 10),
        LST('reward_paid', 'Reward paid', 'yn', 11),
        CA('status', 'Status', 'text', 'IF({col:booking_id}="",%s,IF({col:reward_paid}=%s,%s,%s))' % (cb('Referral pending'), YES, cb('Reward paid'), cb('Reward due')), 16),
        CA('booked_amount', 'Booking amount', 'money', LKN('bookings.gross', 'bookings.booking_id', 'booking_id'), 11),
        CA('reward_share', 'Reward share of booking', 'pct', 'IF({col:booked_amount}>0,{col:reward}/{col:booked_amount},0)', 11), GPH('guests', 'guest', 'guest')],
      D.referrals_d(), 100, [A('status', '= ' + cb('Reward due'), 'warn'), A('status', '= ' + cb('Reward paid'), 'good')]),
    T('requests', 'Special Requests', 'Special requests with cost and fee',
      'One row per special request: the booking, what was asked, the cost to you, the fee charged and whether it was approved and done; the guest, unit, status and margin fill in by themselves.', [
        C('sq_id', 'Request ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('booking_id', 'Booking ID', 'text', 10), C('request', 'Request', 'text', 26), C('cost', 'Cost', 'money', 9), C('fee', 'Fee charged', 'money', 11),
        LST('approved', 'Approved', 'yn', 10), C('done_on', 'Done on', 'date', 11),
        CA('guest', 'Guest', 'text', LKT('bookings.guest', 'bookings.booking_id', 'booking_id'), 24), CA('unit', 'Unit', 'text', LKT('bookings.unit', 'bookings.booking_id', 'booking_id'), 26),
        CA('status', 'Status', 'text', 'IF({col:approved}<>%s,%s,IF({col:done_on}=0,%s,%s))' % (YES, cb('Not approved'), cb('Approved, to do'), cb('Done')), 16),
        CA('margin', 'Margin', 'money', '{col:fee}-{col:cost}', 9), GPH(), COH()],
      D.requests_d(), 200, [A('status', '= ' + cb('Approved, to do'), 'warn'), A('margin', '< 0', 'bad')]),
    T('earlyout', 'Early and Late', 'Early check-in and late checkout requests',
      'One row per early check-in or late checkout: the hours asked, the fee charged and whether it was approved; the nightly rate, the suggested fee and the fee check fill in by themselves.', [
        C('eo_id', 'Request ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('booking_id', 'Booking ID', 'text', 10), LST('kind', 'Kind', 'eckind', 15), C('hours', 'Hours', 'num', 8), C('fee', 'Fee charged', 'money', 11),
        LST('approved', 'Approved', 'yn', 10),
        CA('guest', 'Guest', 'text', LKT('bookings.guest', 'bookings.booking_id', 'booking_id'), 24), CA('unit', 'Unit', 'text', LKT('bookings.unit', 'bookings.booking_id', 'booking_id'), 26),
        CA('rate', 'Nightly rate', 'money', LKN('bookings.nightly_rate', 'bookings.booking_id', 'booking_id'), 11),
        CA('suggested_fee', 'Suggested fee', 'money', 'ROUND(MAX(0,{col:hours}-{set:free_hours})*{col:rate}*{set:hour_share},0)', 11),
        CA('fee_flag', 'Fee check', 'text', 'IF({col:approved}<>%s,%s,IF({col:suggested_fee}=0,%s,IF({col:fee}>={col:suggested_fee},%s,%s)))' % (YES, cb('Not approved'), cb('Free as agreed'), cb('Fee on target'), cb('Fee below suggestion')), 18),
        GPH(), COH()],
      D.earlyout_d(), 200, [A('fee_flag', '= ' + cb('Fee below suggestion'), 'warn'), A('fee_flag', '= ' + cb('Fee on target'), 'good')]),
    T('breaches', 'House Rule Breaches', 'House rule breaches with warnings',
      'One row per breach of a house rule: the unit, guest, rule broken, action taken and whether a warning was sent; the warning check and the breaches of the unit in 12 months fill in by themselves.', [
        C('hb_id', 'Notice ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('booking_id', 'Booking ID', 'text', 10), REF('unit', 'Unit', 'units.name', 26), C('guest', 'Guest', 'text', 24), C('rule', 'Rule', 'text', 28),
        C('action', 'Action', 'text', 22), LST('warning_sent', 'Warning sent', 'yn', 11),
        CA('warning_flag', 'Warning check', 'text', 'IF({col:warning_sent}=%s,%s,%s)' % (YES, cb('Warning sent'), cb('Warning due')), 14),
        CA('unit_breaches', 'Breaches of the unit, 12 months', 'int', 'COUNTIFS({range:breaches.unit},{col:unit},{range:breaches.date},">="&({today}-365))', 14), GPH(), COH()],
      D.breaches_d(), 100, [A('warning_flag', '= ' + cb('Warning due'), 'warn'), A('unit_breaches', '> 3', 'bad')]),
    T('revreq', 'Review Requests', 'Review requests with days to review',
      'One row per review request sent after a stay: the booking, the date sent and the date the guest reviewed; the days to review, the status and the delay after checkout fill in by themselves.', [
        C('rq_id', 'Request ID', 'text', 9, required=True), C('booking_id', 'Booking ID', 'text', 10), C('sent_on', 'Sent on', 'date', 11), C('reviewed_on', 'Reviewed on', 'date', 11),
        CA('guest', 'Guest', 'text', LKT('bookings.guest', 'bookings.booking_id', 'booking_id'), 24), CA('unit', 'Unit', 'text', LKT('bookings.unit', 'bookings.booking_id', 'booking_id'), 26),
        CA('send_lag', 'Days after checkout', 'int', '{col:sent_on}-%s' % LKN('bookings.check_out', 'bookings.booking_id', 'booking_id'), 11),
        CA('days_to_review', 'Days to review', 'int', 'IF({col:reviewed_on}=0,"",{col:reviewed_on}-{col:sent_on})', 10),
        CA('status', 'Status', 'text', 'IF({col:reviewed_on}>0,%s,IF({today}-{col:sent_on}<={set:review_window},%s,%s))' % (ca('Reviewed'), ca('Waiting for review'), ca('Not reviewed')), 18),
        CA('reviewed_num', 'Reviewed (1 or 0)', 'int', 'IF({col:reviewed_on}>0,1,0)', 9), GPH()],
      D.revreq_d(), 400, [A('status', '= ' + ca('Not reviewed'), 'warn'), A('status', '= ' + ca('Reviewed'), 'good')]),
    T('topicmo', 'Rating by Topic', 'Reviews and average rating by month and topic',
      'One row per month and review topic: how many reviews and the average rating; the gap to the minimum and the check fill in by themselves. The monthly guest report reads it.', [
        C('tm_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('topic', 'Topic', 'rtopic', 17), C('reviews', 'Reviews', 'int', 9), C('avg_rating', 'Average rating', 'num', 11),
        CA('gap_to_min', 'Gap to minimum', 'num', '{col:avg_rating}-{set:min_rating}', 11),
        CA('rating_flag', 'Rating check', 'text', 'IF({col:avg_rating}<{set:min_rating},%s,%s)' % (ca('Below minimum'), ca('Above minimum')), 14), HOST()],
      D.topicmo_d(), 200, [A('rating_flag', '= ' + ca('Below minimum'), 'bad')]),
    T('winback', 'Win-back List', 'Win-back list of repeat guests not seen for months',
      'One row per repeat guest not seen for months: last stay, nights, the offer sent and whether they booked again; the days since the last stay, the result and the guest phone fill in by themselves.', [
        C('wn_id', 'Row ID', 'text', 9, required=True), C('guest', 'Guest', 'text', 24), C('last_stay', 'Last stay', 'date', 11), C('nights', 'Nights', 'int', 8), C('offer', 'Offer', 'text', 30), C('sent_on', 'Sent on', 'date', 11),
        LST('booked', 'Booked again', 'yn', 11),
        CA('days_since', 'Days since last stay', 'int', '{today}-{col:last_stay}', 11),
        CA('result', 'Result', 'text', 'IF({col:booked}=%s,%s,IF({today}-{col:sent_on}>30,%s,%s))' % (YES, cb('Booked again'), cb('No answer'), cb('Waiting for answer')), 18),
        CA('guest_spend', 'Guest spend so far', 'money', LKN('guests.spend', 'guests.guest', 'guest'), 11), GPH('guests', 'guest', 'guest')],
      D.winback_d(), 100, [A('result', '= ' + cb('Booked again'), 'good'), A('result', '= ' + cb('No answer'), 'warn')]),
    T('team', 'Team', 'Team with the messages and replies each person handles',
      'The host, the co-host (a helper who handles guests for a fee), four cleaners, two handypeople and four outside contacts; guest messages, complaints and review replies handled fill in by themselves.', [
        C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 14), LST('team', 'Team', 'team', 12), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
        C('hours_week', 'Hours a week', 'int', 10), C('hourly_rate', 'Hourly rate', 'money', 10), C('speciality', 'Speciality', 'text', 26), C('country', 'Country', 'text', 14), C('start', 'Start', 'date', 11),
        CA('msgs_handled', 'Guest messages handled', 'int', 'COUNTIFS({range:gmsg.handled_by},{col:name})', 11),
        CA('complaints_handled', 'Complaints handled', 'int', 'COUNTIFS({range:complaints.handled_by},{col:name})', 11),
        CA('replies_written', 'Review replies written', 'int', 'COUNTIFS({range:replies.replied_by},{col:name})', 11)],
      D.team_d(), 50),
]
assert len(tables) == 20, len(tables)
for _t in tables: assert len(_t['hint']) <= 200, (_t['key'], len(_t['hint']))

if __name__ == '__main__':
    for t in tables: print(t['key'], len(t['demo']), len(t['columns']))
