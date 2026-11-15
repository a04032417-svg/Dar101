"""Short-term rental host suite - part 6: Guests, Messages and Reviews."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr6_lists import *
from sr6_tables import settings, tables
from sr6_tools import tools

SUITE = 'fx-20261113-short-term-rental'
NOTE = "Sample wording: adapt it to your own practice and check your own local rules."
YES, NO = tok('yn', 'Yes'), tok('yn', 'No')
def F(*pairs): return [FV(a, b) for a, b in pairs]
forms = [
    FORM('guest_profile', 'Guest Profile Sheet', 'Guest profile with stays, spend and offers', 'guests.guest_id', F(
        ('Guest', 'guests.guest'), ('Country', 'guests.country'), ('Phone', 'guests.phone'), ('Stays', 'guests.stays'), ('Nights', 'guests.nights'), ('Spend', 'guests.spend'), ('First stay', 'guests.first_stay'),
        ('Last stay', 'guests.last_stay'), ('Booked through', 'guests.channel'), ('Repeat check', 'guests.repeat_flag'), ('Spend per stay', 'guests.avg_spend'), ('Days since the last stay', 'guests.days_since'),
        ('Win-back check', 'guests.win_flag'), ('Reviews left', 'guests.reviews_left'), ('Preferences noted', 'guests.prefs_noted')) + [
        FF('Average stays per guest, all guests', 'AVERAGE({range:guests.stays})', 'num')]),
    FORM('message_log', 'Message Log Sheet', 'Guest message with reply time', 'gmsg.message_id', F(
        ('Date', 'gmsg.date'), ('Booking', 'gmsg.booking_id'), ('Unit', 'gmsg.unit'), ('Guest', 'gmsg.guest'), ('Kind', 'gmsg.kind'), ('Channel', 'gmsg.channel'), ('Handled by', 'gmsg.handled_by'),
        ('Minutes to the first reply', 'gmsg.response_min'), ('Reply check', 'gmsg.reply_flag'), ('Minutes over the target', 'gmsg.over_by'), ('Resolved', 'gmsg.resolved')) + [
        FF('Wanted first reply, minutes', '{set:response_target_min}', 'int'), FF('Average reply minutes, all messages', 'AVERAGE({range:gmsg.response_min})', 'int')]),
    FORM('complaint_sheet', 'Complaint Sheet', 'Complaint with action and compensation', 'complaints.cp_id', F(
        ('Date', 'complaints.date'), ('Booking', 'complaints.booking_id'), ('Unit', 'complaints.unit'), ('Guest', 'complaints.guest'), ('Topic', 'complaints.topic'), ('Severity', 'complaints.severity'), ('Action', 'complaints.action'),
        ('Compensation', 'complaints.compensation'), ('Share of the stay given back', 'complaints.comp_pct'), ('Resolved on', 'complaints.resolved_on'), ('Days to resolve or open', 'complaints.days_to_resolve'),
        ('Status', 'complaints.status'), ('Handled by', 'complaints.handled_by'), ('Guest phone', 'complaints.guest_phone')) + [
        FF('Complaints on this unit, all time', 'COUNTIFS({range:complaints.unit},INDEX({range:complaints.unit},MATCH({pick},{range:complaints.cp_id},0)))', 'int')]),
    FORM('review_reply_sheet', 'Review Reply Sheet', 'Review with reply status', 'reviews.review_id', F(
        ('Date', 'reviews.date'), ('Unit', 'reviews.unit'), ('Guest', 'reviews.guest'), ('Channel', 'reviews.channel'), ('Rating', 'reviews.rating'), ('Cleanliness', 'reviews.cleanliness'), ('Communication', 'reviews.communication'),
        ('Location', 'reviews.location'), ('Value', 'reviews.value'), ('Topic', 'reviews.topic'), ('Level', 'reviews.level'), ('Replied', 'reviews.replied'), ('Reply status', 'reviews.reply_status'), ('Days to reply', 'reviews.days_to_reply'))),
    FORM('checkin_record', 'Check-in Record Sheet', 'Check-in with arrival time and issue', 'checkins.ci_id', F(
        ('Date', 'checkins.date'), ('Booking', 'checkins.booking_id'), ('Unit', 'checkins.unit'), ('Guest', 'checkins.guest'), ('Planned time', 'checkins.planned'), ('Arrival time', 'checkins.arrival'),
        ('Minutes after planned', 'checkins.late_min'), ('Access method', 'checkins.method'), ('Issue', 'checkins.issue'), ('Issue check', 'checkins.issue_flag'), ('Handled by', 'checkins.handled_by'), ('Guest phone', 'checkins.guest_phone'))),
    FORM('survey_sheet', 'Survey Sheet', 'Guest survey with score and comment', 'surveys.sv_id', F(
        ('Date', 'surveys.date'), ('Booking', 'surveys.booking_id'), ('Unit', 'surveys.unit'), ('Guest', 'surveys.guest'), ('Score out of 10', 'surveys.score'), ('Comment', 'surveys.comment'), ('Would return', 'surveys.would_return'),
        ('Mood', 'surveys.mood'), ('Guest phone', 'surveys.guest_phone')) + [FF('Average score, all surveys', 'AVERAGE({range:surveys.score})', 'num')]),
    FORM('request_sheet', 'Special Request Sheet', 'Special request with cost, fee and margin', 'requests.sq_id', F(
        ('Date', 'requests.date'), ('Booking', 'requests.booking_id'), ('Guest', 'requests.guest'), ('Unit', 'requests.unit'), ('Request', 'requests.request'), ('Cost to you', 'requests.cost'), ('Fee charged', 'requests.fee'),
        ('Margin', 'requests.margin'), ('Approved', 'requests.approved'), ('Done on', 'requests.done_on'), ('Status', 'requests.status'), ('Guest phone', 'requests.guest_phone'))),
    FORM('early_sheet', 'Early Check-in Sheet', 'Early check-in or late checkout with fee', 'earlyout.eo_id', F(
        ('Date', 'earlyout.date'), ('Booking', 'earlyout.booking_id'), ('Guest', 'earlyout.guest'), ('Unit', 'earlyout.unit'), ('Kind', 'earlyout.kind'), ('Hours', 'earlyout.hours'), ('Nightly rate', 'earlyout.rate'),
        ('Suggested fee', 'earlyout.suggested_fee'), ('Fee charged', 'earlyout.fee'), ('Approved', 'earlyout.approved'), ('Fee check', 'earlyout.fee_flag'), ('Guest phone', 'earlyout.guest_phone'))),
    FORM('notice_sheet', 'House Rule Notice Sheet', 'House rule breach with warning', 'breaches.hb_id', F(
        ('Date', 'breaches.date'), ('Booking', 'breaches.booking_id'), ('Unit', 'breaches.unit'), ('Guest', 'breaches.guest'), ('Rule', 'breaches.rule'), ('Action', 'breaches.action'), ('Warning sent', 'breaches.warning_sent'),
        ('Warning check', 'breaches.warning_flag'), ('Breaches of the unit, 12 months', 'breaches.unit_breaches'), ('Guest phone', 'breaches.guest_phone'))),
    FORM('winback_sheet', 'Win-back Offer Sheet', 'Win-back offer with result', 'winback.wn_id', F(
        ('Guest', 'winback.guest'), ('Last stay', 'winback.last_stay'), ('Days since the last stay', 'winback.days_since'), ('Nights', 'winback.nights'), ('Spend so far', 'winback.guest_spend'), ('Offer', 'winback.offer'),
        ('Sent on', 'winback.sent_on'), ('Booked again', 'winback.booked'), ('Result', 'winback.result'), ('Guest phone', 'winback.guest_phone'))),
]
assert len(forms) == 10
documents = [
    DOC('welcome_letter', 'Guest Welcome Letter', 'Welcome letter for one booking', 'bookings.booking_id', [
        'Welcome letter of {set:company}, dated {today}. Dear {col:bookings.guest}, welcome to {col:bookings.unit} in {col:bookings.city}.',
        'Your stay runs from {col:bookings.check_in} to {col:bookings.check_out}, {col:bookings.nights} nights for {col:bookings.guests} guests. Check-in is from {col:bookings.checkin_time} and checkout is at {col:bookings.checkout_time}.',
        'Your host and co-host are one message away. We answer messages within {set:response_target_min} minutes during the day.', 'Please read the house rules and the welcome book in the unit. We hope you enjoy your stay.'], ['Host', 'Guest'], NOTE),
    DOC('house_rules', 'House Rules Sheet', 'House rules for one unit', 'units.unit_id', [
        'House rules of {set:company}, dated {today}. Unit: {col:units.name}, {col:units.unit_type} in {col:units.city} with {col:units.bedrooms} bedrooms.',
        'Check-in from {set:checkin_time}, checkout by {set:checkout_time}. Quiet hours apply late at night and early in the morning. Please do not hold parties or events.',
        'Smoking and pets follow the listing. Please keep the number of guests to the number booked, put rubbish in the right bins and close windows and doors when you leave.', 'Check your own local rules for extra notices that must be shown to guests. The host may end a stay when a serious rule is broken.'], ['Host', 'Guest'], NOTE),
    DOC('checkin_doc', 'Check-in Instructions', 'Check-in instructions for one booking', 'bookings.booking_id', [
        'Check-in instructions of {set:company}, dated {today}. Guest: {col:bookings.guest}. Unit: {col:bookings.unit}, {col:bookings.city}.',
        'Check-in on {col:bookings.check_in} from {col:bookings.checkin_time}. You will receive the way to get in by message on the morning of arrival. Please tell us your arrival time.',
        'If you cannot get in, message us at once and we reply within {set:response_target_min} minutes. Co-host phone: {col:bookings.cohost_phone}.', 'Booking {col:bookings.booking_id}, booked on {col:bookings.booked_on}, {col:bookings.nights} nights.'], ['Host', 'Guest'], NOTE),
    DOC('checkout_doc', 'Checkout Instructions', 'Checkout instructions for one booking', 'bookings.booking_id', [
        'Checkout instructions of {set:company}, dated {today}. Guest: {col:bookings.guest}. Unit: {col:bookings.unit}.',
        'Checkout on {col:bookings.check_out} by {col:bookings.checkout_time}. Please close the windows, turn off lights and heating, put the used towels in the bath and leave the keys or close the lock as shown.',
        'Tell us about any damage or anything left behind. A late checkout may be possible: ask us before the day and we will answer with the fee, if any.', 'Thank you for staying. A short review helps other guests and our small team.'], ['Host', 'Guest'], NOTE),
    DOC('complaint_letter', 'Complaint Resolution Letter', 'Complaint resolution letter', 'complaints.cp_id', [
        'Complaint resolution of {set:company}, dated {today}. Dear {col:complaints.guest}, thank you for telling us about the {col:complaints.topic} problem in {col:complaints.unit} on {col:complaints.date}.',
        'We take it seriously. Action taken: {col:complaints.action}. Compensation offered: {col:complaints.compensation}, which is {col:complaints.comp_pct} of the stay amount.',
        'Status: {col:complaints.status}. Days to resolve or open: {col:complaints.days_to_resolve}. Handled by {col:complaints.handled_by}.', 'We are sorry for the trouble and would like to welcome you again.'], ['Host', 'Guest'], NOTE),
    DOC('reply_doc', 'Review Reply Letter', 'Review reply for one review', 'reviews.review_id', [
        'Review reply of {set:company}, dated {today}. Review {col:reviews.review_id} of {col:reviews.unit} by {col:reviews.guest}, written on {col:reviews.date}.',
        'Rating {col:reviews.rating} (level: {col:reviews.level}). Cleanliness {col:reviews.cleanliness}, communication {col:reviews.communication}, location {col:reviews.location}, value {col:reviews.value}. Main topic: {col:reviews.topic}.',
        'Reply status: {col:reviews.reply_status}. Days to reply: {col:reviews.days_to_reply}. We reply within {set:reply_days} days.', 'Draft reply: thank the guest by name, mention the topic and say what you will do. Write the final text below.'], ['Host', 'Co-host'], NOTE),
    DOC('guest_summary', 'Guest Profile Summary', 'Guest profile summary', 'guests.guest_id', [
        'Guest profile of {set:company}, dated {today}. Guest {col:guests.guest_id}: {col:guests.guest} from {col:guests.country}.',
        'Stays: {col:guests.stays}, nights: {col:guests.nights}, spend: {col:guests.spend}, spend per stay: {col:guests.avg_spend}. First stay {col:guests.first_stay}, last stay {col:guests.last_stay}, booked through {col:guests.channel}.',
        'Check: {col:guests.repeat_flag}. Win-back check: {col:guests.win_flag}. Reviews left: {col:guests.reviews_left}. Preferences noted: {col:guests.prefs_noted}.', 'Use the preferences to prepare the next stay and the win-back offer.'], ['Host', 'Co-host'], NOTE),
    DOC('monthly_report', 'Monthly Guest Report', 'Guest report for one unit', 'units.unit_id', [
        'Guest report of {set:company}, dated {today}. Unit {col:units.unit_id}: {col:units.name} ({col:units.city}), owner {col:units.owner}.',
        'Last 90 days: {col:units.reviews_90d} reviews, average rating {col:units.avg_rating_90d}, cleanliness {col:units.avg_clean_90d}. Last 12 months: {col:units.reviews_12m} reviews, rating {col:units.avg_rating_12m}. Check: {col:units.rating_flag}.',
        'Reviews without a reply: {col:units.unanswered}. Complaints in 90 days: {col:units.complaints_90d}. Guest messages in 90 days: {col:units.msgs_90d}, average reply {col:units.avg_reply_90d} minutes.',
        'Actions for the next month and the person who owns each are written below.'], ['Host', 'Owner'], NOTE),
    DOC('welcome_book_doc', 'Welcome Book Page', 'Welcome book summary for one unit', 'units.unit_id', [
        'Welcome book of {set:company}, dated {today}. Unit: {col:units.name}, a {col:units.unit_type} with {col:units.bedrooms} bedrooms in {col:units.city}.',
        'Sections kept up to date: {col:units.wb_sections}. Last update: {col:units.wb_updated}. Sections cover the Wi-Fi and TV, heating and hot water, parking, bins, local food, emergency numbers and the checkout steps.',
        'Check-in from {set:checkin_time}, checkout by {set:checkout_time}. Co-host phone: {col:units.cohost_phone}.', 'Review every section when it is older than {set:welcome_days} days.'], ['Host', 'Co-host'], NOTE),
    DOC('winback_letter', 'Win-back Letter', 'Win-back letter for one guest', 'winback.wn_id', [
        'Win-back letter of {set:company}, dated {today}. Dear {col:winback.guest}, it has been {col:winback.days_since} days since your last stay of {col:winback.nights} nights.',
        'We would love to welcome you again. Your offer: {col:winback.offer}. Book direct and we will confirm the dates and the total price in writing. Prices are before any local tax.',
        'Sent on {col:winback.sent_on}. Result so far: {col:winback.result}.', 'Reply to this message and we will hold your dates.'], ['Host', 'Guest'], NOTE),
]
assert len(documents) == 10
checklists = [
    CHK('new_booking', 'New Booking Message Steps', 'bookings', 'bookings.booked_on', [('Send the booking confirmation', 0), ('Ask for the arrival time and the number of guests', 1), ('Save special requests in Guest Preferences', 1), ('Check the guest history in Guests', 2),
        ('Send the house rules', 3), ('Answer every question within the target time', 3), ('Tell the cleaner about extra beds or a baby cot', 5)]),
    CHK('checkin_day', 'Check-in Day Steps', 'bookings', 'bookings.check_in', [('Send the check-in instructions', -1), ('Test the lock code or check the key box', -1), ('Check the unit is clean and stocked', 0), ('Send the welcome message', 0), ('Watch for the arrival time and answer questions', 0),
        ('Write the check-in record with any issue', 1)]),
    CHK('mid_stay', 'Mid-stay Check Steps', 'bookings', 'bookings.check_in', [('Send a how-is-everything message', 1), ('Answer any request the same day', 1), ('Offer a mid-stay clean on stays of 5 nights or more', 2), ('Check for house rule or noise reports', 2), ('Note preferences the guest mentions', 3)]),
    CHK('checkout_day', 'Checkout Day Steps', 'bookings', 'bookings.check_out', [('Send the checkout reminder the evening before', -1), ('Confirm the checkout time', 0), ('Tell the cleaner when the guest has left', 0), ('Check for damage or lost items', 0), ('Send thanks and the review request', 1), ('Send the lost item message if needed', 2)]),
    CHK('review_request', 'Review Request Steps', 'revreq', 'revreq.sent_on', [('Check the stay had no open complaint', -1), ('Send the review request', 0), ('Wait for the review', 2), ('Send one reminder', 4), ('Thank the guest after the review', 5), ('Record the result in Review Requests', 14)]),
    CHK('review_reply', 'Review Reply Steps', 'reviews', 'reviews.date', [('Read the whole review and the sub-ratings', 0), ('Pick the tone from the rating and topic', 0), ('Write the reply with the guest name', 1), ('Reply within the allowed days', 2), ('Share a low review with the owner', 2), ('Tell the cleaner or handyperson about the fix', 3)]),
    CHK('complaint_handling', 'Complaint Handling Steps', 'complaints', 'complaints.date', [('Reply to the guest within the target time', 0), ('Ask for photos or details', 0), ('Choose the action and the compensation', 0), ('Fix the problem or move the guest', 1), ('Confirm with the guest that it is solved', 2), ('Write the result and the cost', 3), ('Tell the owner', 3)]),
    CHK('repeat_guest', 'Repeat Guest Steps', 'guests', 'guests.last_stay', [('Read the guest preferences', 0), ('Send a thank you after the stay', 1), ('Offer a direct booking price', 30), ('Send a win-back offer after the usual number of days', 180), ('Record the result in the Win-back List', 210)]),
    CHK('weekly_review', 'Weekly Review Report Steps', 'reviews', 'reviews.date', [('List new reviews of the week', 0), ('Reply to every review without a reply', 1), ('Check units below the minimum rating', 2), ('Read the low review topics', 3), ('Agree one fix with the cleaner or handyperson', 4), ('Send the summary to the host and the owners', 6)]),
    CHK('monthly_report', 'Monthly Guest Report Steps', 'topicmo', 'topicmo.month', [('Update the Rating by Topic table', 28), ('Read average rating, replies and complaints per unit', 29), ('Compare reply times with the target', 30), ('Count repeat guests and win-back offers', 31), ('Send the guest report to the owners', 33), ('Plan the next month fixes', 35)]),
]
assert len(checklists) == 10
def M(key_, moment, table, phone, text): return MSG(key_, moment, table, phone, text)
messages = [
    M('g_welcome', 'Guest: welcome to your stay', 'bookings', 'bookings.guest_phone', 'Hello {guest}, welcome! Your stay at {unit} starts on {check_in}. Check-in is from {checkin_time}. Write to us if you need anything.'),
    M('g_instr', 'Guest: your check-in instructions', 'bookings', 'bookings.guest_phone', 'Hello {guest}, your check-in instructions for {unit}: arrive from {checkin_time} on {check_in}. The way to get in comes by message on the morning of arrival.'),
    M('g_night', 'Guest: how was your first night', 'bookings', 'bookings.guest_phone', 'Hello {guest}, how was your first night in {unit}? Tell us if anything is missing and we will fix it today.'),
    M('g_rules', 'Guest: a reminder about the house rules', 'bookings', 'bookings.guest_phone', 'Hello {guest}, a friendly reminder of the house rules of {unit}: quiet hours at night, no parties and no smoking indoors. Thank you.'),
    M('g_checkout', 'Guest: your checkout time', 'bookings', 'bookings.guest_phone', 'Hello {guest}, your checkout from {unit} is at {checkout_time} on {check_out}. Please close the windows and leave the keys as shown.'),
    M('g_review', 'Guest: a review would help', 'bookings', 'bookings.guest_phone', 'Hello {guest}, thank you for staying in {unit}. A short review helps other guests and our small team. It takes two minutes.'),
    M('g_sorry', 'Guest: we are sorry, with compensation', 'complaints', 'complaints.guest_phone', 'Hello {guest}, we are sorry about the {topic} problem in {unit}. We offer {compensation} and have fixed the cause.'),
    M('g_early', 'Guest: your early check-in is approved', 'earlyout', 'earlyout.guest_phone', 'Hello {guest}, your request of {hours} hours ({kind}) in {unit} is approved. The fee is {fee}.'),
    M('g_late', 'Guest: a late checkout is possible', 'earlyout', 'earlyout.guest_phone', 'Hello {guest}, a late checkout of {hours} hours from {unit} is possible for {fee}. Reply to confirm.'),
    M('g_arrival', 'Guest: your arrival time', 'bookings', 'bookings.guest_phone', 'Hello {guest}, what time do you plan to arrive at {unit} on {check_in}? We will be ready for you.'),
    M('g_winback', 'Guest: a welcome-back offer', 'winback', 'winback.guest_phone', 'Hello {guest}, it has been {days_since} days since your last stay. Book direct for your next stay and enjoy: {offer}.'),
    M('g_gift', 'Guest: a small gift for your stay', 'bookings', 'bookings.guest_phone', 'Hello {guest}, a small welcome gift waits for you in {unit}. We hope you enjoy your stay from {check_in}.'),
    M('g_thanks', 'Guest: thank you for your review', 'reviews', 'reviews.guest_phone', 'Hello {guest}, thank you for your {rating} star review of {unit}. We are glad you stayed with us.'),
    M('g_lost', 'Guest: your lost item was found', 'bookings', 'bookings.guest_phone', 'Hello {guest}, we found an item you left in {unit} after your stay on {check_out}. Tell us where to send it.'),
    M('g_quiet', 'Guest: a quiet hours reminder', 'bookings', 'bookings.guest_phone', 'Hello {guest}, a quiet hours reminder for {unit}: our neighbours sleep late at night. Thank you for your care.'),
    M('g_survey', 'Guest: your short survey', 'surveys', 'surveys.guest_phone', 'Hello {guest}, your survey for {unit} is short. Please give a score from 1 to 10 and tell us one thing to improve.'),
    M('c_wait', 'Co-host: a guest message waits', 'gmsg', 'gmsg.cohost_phone', 'Hello, a {kind} message from {guest} for {unit} waits for a reply. Reply time so far: {response_min} minutes.'),
    M('c_complaint', 'Co-host: a complaint needs action today', 'complaints', 'complaints.cohost_phone', 'Hello, a complaint about {topic} in {unit} needs action today. Guest: {guest}. Severity: {severity}.'),
    M('c_checkin', 'Co-host: send check-in instructions', 'bookings', 'bookings.cohost_phone', 'Hello, please send the check-in instructions to {guest} for {unit} on {check_in}.'),
    M('c_review', 'Co-host: a review waits for a reply', 'reviews', 'reviews.cohost_phone', 'Hello, the {rating} star review of {unit} from {guest} is waiting for a reply.'),
    M('c_late', 'Co-host: a guest asks for late checkout', 'earlyout', 'earlyout.cohost_phone', 'Hello, {guest} asked for {hours} hours ({kind}) in {unit}. Please check the next arrival and answer.'),
    M('h_review', 'Host: a low review needs a reply', 'reviews', 'reviews.host_phone', 'Hello, a review of {rating} stars for {unit} needs a reply. Guest: {guest}. Topic: {topic}.'),
    M('h_unit', 'Host: a unit rating is below the minimum', 'units', 'units.host_phone', 'Hello, the rating of {name} is {avg_rating_90d} over 90 days, below the minimum. Please look at its reviews.'),
    M('h_slow', 'Host: a reply was slow', 'gmsg', 'gmsg.host_phone', 'Hello, the reply to {guest} for {unit} took {response_min} minutes. Please look at the message log.'),
    M('h_report', 'Host: the guest report is ready', 'topicmo', 'topicmo.host_phone', 'Hello, the guest report is ready. Topic {topic}: {reviews} reviews, average rating {avg_rating}.'),
    M('h_repeat', 'Host: a repeat guest booked again', 'guests', 'guests.host_phone', 'Hello, {guest} is a repeat guest with {stays} stays and a total spend of {spend}. Please send a thank you.'),
    M('o_five', 'Owner: your unit got a five-star review', 'reviews', 'reviews.owner_phone', 'Hello, {unit} received a {rating} star review from {guest}. Topic: {topic}.'),
    M('o_low', 'Owner: your unit got a low review', 'reviews', 'reviews.owner_phone', 'Hello, {unit} received a low review of {rating} stars on {date}. Topic: {topic}. We are working on it.'),
]
assert len(messages) == 28, len(messages)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; NXT = 'DATE(YEAR({today}),MONTH({today})+1,1)'
QS = 'DATE(YEAR({today}),3*INT((MONTH({today})-1)/3)+1,1)'
def DR(col, a, b='{today}'): return '{range:%s},">="&%s,{range:%s},"<="&%s' % (col, a, col, b)
kpis = [
    KPI('Reviews this month', 'COUNTIFS(%s)' % DR('reviews.date', MS), 'int'),
    KPI('Average rating this month', 'IFERROR(AVERAGEIFS({range:reviews.rating},%s),0)' % DR('reviews.date', MS), 'num'),
    KPI('Average rating, last 90 days', 'IFERROR(AVERAGEIFS({range:reviews.rating},%s),0)' % DR('reviews.date', '({today}-90)'), 'num'),
    KPI('Average rating, last 12 months', 'IFERROR(AVERAGEIFS({range:reviews.rating},%s),0)' % DR('reviews.date', '({today}-365)'), 'num'),
    KPI('Five-star share', 'IFERROR(COUNTIFS({range:reviews.rating},5)/COUNT({range:reviews.rating}),0)', 'pct'),
    KPI('Reviews of 3 stars or less, last 90 days', 'COUNTIFS({range:reviews.rating},"<="&{set:low_stars},%s)' % DR('reviews.date', '({today}-90)'), 'int'),
    KPI('Reviews waiting for a reply', 'COUNTIFS({range:reviews.replied},%s)' % NO, 'int'),
    KPI('Review rate of stays', 'IFERROR(SUM({range:revreq.reviewed_num})/COUNT({range:revreq.reviewed_num}),0)', 'pct'),
    KPI('Average cleanliness rating', 'IFERROR(AVERAGE({range:reviews.cleanliness}),0)', 'num'),
    KPI('Average communication rating', 'IFERROR(AVERAGE({range:reviews.communication}),0)', 'num'),
    KPI('Average location rating', 'IFERROR(AVERAGE({range:reviews.location}),0)', 'num'),
    KPI('Average value rating', 'IFERROR(AVERAGE({range:reviews.value}),0)', 'num'),
    KPI('Units below the minimum rating', 'COUNTIFS({range:units.rating_flag},%s)' % ca('Below minimum'), 'int'),
    KPI('Lowest unit rating, last 90 days', 'MIN({range:units.avg_rating_90d})', 'num'),
    KPI('Guest messages this month', 'COUNTIFS(%s)' % DR('gmsg.date', MS), 'int'),
    KPI('Average first reply minutes, 90 days', 'IFERROR(AVERAGEIFS({range:gmsg.response_min},%s),0)' % DR('gmsg.date', '({today}-90)'), 'int'),
    KPI('Replies over the target, last 30 days', 'COUNTIFS({range:gmsg.reply_flag},%s,%s)' % (ca('Over target'), DR('gmsg.date', '({today}-30)')), 'int'),
    KPI('Complaints this month', 'COUNTIFS(%s)' % DR('complaints.date', MS), 'int'),
    KPI('Open complaints', 'COUNTIFS({range:complaints.status},%s)+COUNTIFS({range:complaints.status},%s)' % (ca('Open'), ca('Open and late')), 'int'),
    KPI('Average days to resolve a complaint', 'IFERROR(AVERAGEIFS({range:complaints.days_to_resolve},{range:complaints.is_resolved},1),0)', 'num'),
    KPI('Compensation given this year', 'SUMIFS({range:complaints.compensation},{range:complaints.date},">="&DATE(YEAR({today}),1,1))', 'money'),
    KPI('Repeat guests share', 'IFERROR(COUNTIFS({range:guests.stays},">=2")/COUNT({range:guests.stays}),0)', 'pct'),
    KPI('Guests with 2 or more stays', 'COUNTIFS({range:guests.stays},">=2")', 'int'),
    KPI('Average stays per guest', 'IFERROR(AVERAGE({range:guests.stays}),0)', 'num'),
    KPI('Surveys with a return intent', 'COUNTIFS({range:surveys.would_return},%s)' % YES, 'int'),
    KPI('Check-ins with an issue', 'COUNTIFS({range:checkins.issue_flag},%s)' % ca('Issue at check-in'), 'int'),
    KPI('Early check-ins approved', 'COUNTIFS({range:earlyout.kind},%s,{range:earlyout.approved},%s)' % (tok('eckind', 'Early check-in'), YES), 'int'),
    KPI('House rule breaches this quarter', 'COUNTIFS(%s)' % DR('breaches.date', QS), 'int'),
    KPI('Win-back offers booked', 'COUNTIFS({range:winback.booked},%s)' % YES, 'int'),
]
assert len(kpis) == 29, len(kpis)
dashboard = {"title": "Guest Dashboard", "kpis": kpis,
    "monthly": {"title": "Reviews, compensation, request fees and early or late fees", "date": "topicmo.month", "series": [
        {"label": "Reviews by month", "sum": "topicmo.reviews", "date": "topicmo.month"}, {"label": "Compensation given", "sum": "complaints.compensation", "date": "complaints.date"},
        {"label": "Special request fees", "sum": "requests.fee", "date": "requests.date"}, {"label": "Early and late fees", "sum": "earlyout.fee", "date": "earlyout.date"}]},
    "breakdowns": [{"title": "Reviews by unit", "by": "reviews.unit", "value": "reviews.rating", "agg": "count"}, {"title": "Compensation by complaint topic", "by": "complaints.topic", "value": "complaints.compensation", "agg": "sum"},
                   {"title": "Guest messages by kind", "by": "gmsg.kind", "value": "gmsg.response_min", "agg": "count"}, {"title": "Guest spend by booking channel", "by": "guests.channel", "value": "guests.spend", "agg": "sum"}]}
insights = {"filters": [{"label": "Unit", "ref": "units.name"}, {"label": "City", "list": "city"}, {"label": "Channel", "list": "chan"}],
    "gauges": [{"title": "Average rating", "num": AGG('sum', 'reviews', 'reviews.rating'), "den": AGG('sum', 'reviews', 'reviews.max_stars')},
               {"title": "Five-star share", "num": AGG('count', 'reviews', where=[('rating', '=', 5)]), "den": AGG('count', 'reviews')},
               {"title": "Replies within the target", "num": AGG('count', 'gmsg', where=[('reply_flag', '=', ca('Within target'))]), "den": AGG('count', 'gmsg')},
               {"title": "Reviews replied to", "num": AGG('count', 'reviews', where=[('replied', '=', YES)]), "den": AGG('count', 'reviews')},
               {"title": "Complaints resolved", "num": AGG('sum', 'complaints', 'complaints.is_resolved'), "den": AGG('count', 'complaints')},
               {"title": "Repeat guests share", "num": AGG('count', 'guests', where=[('stays', '>=', 2)]), "den": AGG('count', 'guests')}],
    "charts": [
        CHART('Reviews per month', 'column', 'month', [AGG('count', 'reviews', date='reviews.date', label='Reviews')]),
        CHART('Average rating per month', 'line', 'month', [AGG('avg', 'reviews', 'reviews.rating', date='reviews.date', label='Average rating')]),
        CHART('Ratings by star', 'bar', 'reviews.stars', [AGG('count', 'reviews', label='Reviews')]),
        CHART('Ratings by unit type', 'bar', 'reviews.unit_type', [AGG('avg', 'reviews', 'reviews.rating', label='Average rating')]),
        CHART('Ratings by city', 'bar', 'reviews.city', [AGG('avg', 'reviews', 'reviews.rating', label='Average rating')]),
        CHART('Rating by booking channel', 'bar', 'reviews.channel', [AGG('avg', 'reviews', 'reviews.rating', label='Average rating')]),
        CHART('Topics of low reviews', 'bar', 'reviews.topic', [AGG('count', 'reviews', where=[('rating', '<=', 3)], label='Low reviews')]),
        CHART('Rating by topic', 'bar', 'topicmo.topic', [AGG('avg', 'topicmo', 'topicmo.avg_rating', label='Average rating')]),
        CHART('Guest messages per month', 'column', 'month', [AGG('count', 'gmsg', date='gmsg.date', label='Messages')]),
        CHART('Guest messages by kind', 'bar', 'gmsg.kind', [AGG('count', 'gmsg', label='Messages')]),
        CHART('Average reply minutes per month', 'line', 'month', [AGG('avg', 'gmsg', 'gmsg.response_min', date='gmsg.date', label='Reply minutes')]),
        CHART('Complaints per month', 'column', 'month', [AGG('count', 'complaints', date='complaints.date', label='Complaints')]),
        CHART('Complaints by topic', 'bar', 'complaints.topic', [AGG('count', 'complaints', label='Complaints')]),
        CHART('Compensation per month', 'column', 'month', [AGG('sum', 'complaints', 'complaints.compensation', date='complaints.date', label='Compensation')]),
        CHART('Repeat guests per month of the last stay', 'column', 'month', [AGG('count', 'guests', date='guests.last_stay', where=[('stays', '>=', 2)], label='Repeat guests')]),
        CHART('Guests by country', 'bar', 'guests.country', [AGG('count', 'guests', label='Guests')]),
        CHART('Replied share per month', 'line', 'month', [AGG('avg', 'reviews', 'reviews.replied_num', date='reviews.date', label='Replied share')]),
        CHART('Review rate per month', 'line', 'month', [AGG('avg', 'revreq', 'revreq.reviewed_num', date='revreq.sent_on', label='Review rate')])]}
signature = [
    {"name": "Review tracker by unit and topic", "why": "every review with its four sub-ratings and topic, the 90-day rating of each unit and the topic that hurts most", "where": "Reviews"},
    {"name": "Rating gap to the target", "why": "the average, the five-star reviews needed to reach your target and how many months that takes at your review pace", "where": "Rating Gap Calculator"},
    {"name": "Low review alert by unit", "why": "units whose 90-day rating falls below your minimum are flagged with their cleanliness score and unanswered reviews", "where": "Units"},
    {"name": "Review reply helper", "why": "rating, topic and guest name become a tone, an opening, a topic sentence and a full reply draft to adapt", "where": "Review Reply Helper"},
    {"name": "Guest message log with reply times", "why": "every message with who answered and the minutes to the first reply, flagged when it is over your target", "where": "Guest Messages"},
    {"name": "Complaint tracker with compensation", "why": "topic, severity, action, compensation and days to resolve, with open and late complaints in red", "where": "Complaints"},
    {"name": "Check-in message builder", "why": "unit, guest, time and way of getting in become a ready check-in text with the date to send it", "where": "Check-in Message Builder"},
    {"name": "Repeat guest value", "why": "stays, spend and the last stay give the value of a guest, the offer to make and whether to send a win-back message now", "where": "Repeat Guest Value"},
    {"name": "Review request timing", "why": "the best day to ask for a review, the reminder date and the review rate of your own requests", "where": "Review Request Timing"},
    {"name": "Win-back list", "why": "repeat guests not seen for months with the offer sent, the days since the stay and whether they booked again", "where": "Win-back List"}]
competitors = [
    {"what": "free review trackers", "lacks": "list ratings but never split them by unit, topic and sub-rating, and have no reply status, reply helper or rating gap to the target"},
    {"what": "subscription property-management software", "lacks": "send automatic messages you cannot read or change, and hide reply times, complaint costs and the topics behind low reviews"},
    {"name": "single-sheet booking trackers", "what": "single-sheet booking trackers", "lacks": "hold dates and guests but have no message log, complaint tracker, check-in record or repeat guest value"},
    {"what": "generic customer spreadsheets", "lacks": "store names and notes but know nothing about stays, nights, review requests, compensation or win-back offers"},
    {"what": "review monitoring services", "lacks": "show stars after the fact but do not link a low review to the unit, the cleaner, the complaint and the fix you plan"}]
for _c in competitors: _c.pop('name', None)
guide = [
    'Open Start and type your company name and your own limits in the yellow cells: lowest acceptable unit rating, wanted rating, wanted reply time, days to reply to a review and days to resolve a complaint.',
    'Check Units, Team and Bookings. They hold your units, the people who answer guests and the stays the other sheets look up.',
    'Log every review on Reviews with the four sub-ratings and the topic. Level, days to reply and reply status fill in. Write each reply on Review Replies.',
    'Log each guest message on Guest Messages with the minutes to the first reply. The sheet flags replies over your target.',
    'Keep Guests up to date with stays, nights and spend. Repeat guests, spend per stay and win-back checks calculate themselves. Note likes on Guest Preferences.',
    'Write every complaint on Complaints with severity, action and compensation. Days to resolve and the open or late status fill in.',
    'Use Check-in Records, Early and Late, Special Requests and House Rule Breaches to see what happens around the stay.',
    'Send review requests and write them on Review Requests. Guest Surveys, Referrals and the Win-back List show what brings guests back.',
    'Keep Message Templates and Welcome Book current. Both show a review check when they are older than your limit.',
    'Fill Rating by Topic each month to see which topic pulls ratings down.',
    f'Use the {len(tools)} calculators for rating impact, reply drafts, reply times, complaints, compensation, check-in texts, repeat guest value, review timing, rating gaps, topics, early and late fees, a satisfaction score and message dates.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Guest Dashboard and Charts every week: ratings, replies, messages, complaints, compensation, repeat guests and countries.']
listing = {"title": "Short-Term Rental Guest Experience Excel Template: Reviews, Guest Messages, Complaints, Repeat Guests, Check-in Records",
    "headline": "Turn every stay into a five-star review and a returning guest",
    "tags": ["short term rental", "vacation rental", "rental host", "guest reviews", "review tracker", "excel template", "guest messages", "complaint log", "repeat guests", "rating tracker", "host template", "holiday let", "guest experience"],
    "description": ("Run the guest side of a short-term or vacation rental business in one Excel workbook. Built for a host or co-host with 3 to 15 furnished units rented by the night through booking platforms and direct bookings. "
        "Reviews logs every review with four sub-ratings, the topic and the reply, and works out the level, the days to reply and the reply status. Units shows the 90-day and 12-month rating of each unit, the reviews still without a reply and the units that fall below your minimum.\n\n"
        "Guest Messages records the minutes to the first reply and flags the replies over your target. Complaints tracks topic, severity, action, compensation and the days to resolve. Guests, Guest Preferences and the Win-back List show repeat guests, what each one is worth and who to write to. "
        "Check-in Records, Early and Late, Special Requests and House Rule Breaches cover what happens around the stay. Review Requests, Guest Surveys, Referrals, Message Templates, the Welcome Book and Rating by Topic show what brings reviews and returns.\n\n"
        f"{len(tools)} calculators cover the rating average and the effect of one review, review reply drafts, reply times, complaint actions, compensation, check-in texts, repeat guest value, review timing, the rating gap, topics, early check-in and late checkout fees, a satisfaction score and the dates of every message. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to guests, the co-host (a helper who handles guests for a fee), the host and owners.\n\n"
        "This is part six of the Short-Term Rental Host suite. A standard .xlsx workbook with no macros and no subscription, 15 languages in one purchase, with a demo copy full of sample data for a small portfolio to explore first. It helps you plan your guest work and does not promise results."),
    "features": ["Review tracker by unit and topic", "Low review alert by unit", "Guest message log with reply times", "Complaint tracker with compensation", "Repeat guests and win-back list", "Check-in records and early or late fees",
                 "Review reply helper", "Rating gap to the target", f"{len(tools)} calculators for reviews and guests", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p6', slug='short-term-rental-guests', profession='Short-Term Rental Host', name='Guests, Messages and Reviews',
         tagline='Turn every stay into a five-star review and a returning guest', price_usd=29,
         colors={"primary": "#264653", "accent": "#E9C46A"}, settings=settings, lists=base_lists + check_lists(), tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 6, "of": 8, "focus": "Guests, messages and reviews"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sr6.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'lists', len(s['lists']), {k: len(v) for k, v in CK.items()})
