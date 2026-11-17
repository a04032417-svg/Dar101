"""Doula business suite - part 7: Referrals, Classes, Reviews, Marketing."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du7_lists import *
from du7_tables import settings, tables
from du7_tools import tools
import du7_data as D

SUITE = 'fx-20261115-doula-business'
NOTE = "Sample wording: adapt it to your own business and check your local rules."
YES = '{list:yesno.yes}'
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
def LKD(t, idc, c): return 'IFERROR(IF(%s=0,"",%s),"")' % (LK(t, idc, c), LK(t, idc, c))
CANC = tok('ctstatus', 'Cancelled'); CARE, PAST, SUPP, CLSS = (tok('rsource', s) for s in RSOURCES)
DUE, ASK, BELOW = ca('Thank-you due'), ca('Ask now'), ca('Below break-even')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def DW(col, n): return '{range:%s},">="&({today}-%s),{range:%s},"<="&{today}' % (col, n, col)
def DM(col, n): return '{range:%s},">"&EDATE({today},-%s),{range:%s},"<="&{today}' % (col, n, col)
def MM(n): return '{range:marketing.month},">"&EDATE(%s,-%s),{range:marketing.month},"<="&%s' % (MS, n, MS)

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('referral_sheet', 'Referral Sheet', 'Referral with the client it became and its thank-you', 'referrals.referral_id', F(
        ('Date', 'referrals.date'), ('Source', 'referrals.source'), ('Referrer', 'referrals.referrer'), ('Enquiry ID', 'referrals.enquiry_id'), ('Client ID', 'referrals.client_id'), ('Client', 'referrals.client'),
        ('Thanked on', 'referrals.thanked_on'), ('Gift cost', 'referrals.gift_cost'), ('Thank-you check', 'referrals.thank_flag'), ('Client income', 'referrals.income'), ('Days since the referral', 'referrals.age_days'),
        ('Referrer phone', 'referrals.referrer_phone')) + [
        FF('Referrals from this referrer', 'COUNTIFS({range:referrals.referrer},%s)' % LK('referrals', 'referral_id', 'referrer'), 'int'),
        FF('Gift value for this source', 'IFERROR(INDEX({range:sources.gift_value},MATCH(%s,{range:sources.source},0)),0)' % LK('referrals', 'referral_id', 'source'), 'money')]),
    FORM('thanks_sheet', 'Thank-you Sheet', 'Thank-you to send to a referrer and its gift value', 'thanks.referrer', F(
        ('Source', 'thanks.source'), ('Clients in the window', 'thanks.clients_q'), ('Thank-yous due', 'thanks.due_n'), ('Thank-yous missed', 'thanks.missed_n'), ('Longest wait, days', 'thanks.waiting_days'),
        ('Last thanked on', 'thanks.last_thanked'), ('Gift value to send', 'thanks.gift_due'), ('Thank-you check', 'thanks.flag')) + [
        FF('Referrer phone', 'INDEX({range:referrers.phone},MATCH({pick},{range:referrers.referrer},0))', 'text'),
        FF('Referrals, all time', 'INDEX({range:referrers.referrals},MATCH({pick},{range:referrers.referrer},0))', 'int'),
        FF('Income of their clients', 'INDEX({range:referrers.income},MATCH({pick},{range:referrers.referrer},0))', 'money')]),
    FORM('source_sheet', 'Referral Source Review Sheet', 'Review of one source: income, cost and rank', 'src_value.source', F(
        ('Income', 'src_value.income'), ('Income per client', 'src_value.income_client')) + [
        FF('Clients, all time', 'COUNTIFS({range:contracts.source},{pick},{range:contracts.status},"<>"&%s)' % CANC, 'int'),
        FF('Enquiries, all time', 'COUNTIFS({range:enquiries.source},{pick})', 'int'),
        FF('Cost of gifts and fees', 'INDEX({range:src_cost.cost},MATCH({pick},{range:src_cost.source},0))', 'money'),
        FF('Cost per signed client', 'INDEX({range:src_cost.cost_signed},MATCH({pick},{range:src_cost.source},0))', 'money'),
        FF('Income left after the cost', 'INDEX({range:src_value.income},MATCH({pick},{range:src_value.source},0))-INDEX({range:src_cost.cost},MATCH({pick},{range:src_cost.source},0))', 'money'),
        FF('Share of all income', 'IFERROR(INDEX({range:src_value.income},MATCH({pick},{range:src_value.source},0))/SUM({range:src_value.income}),0)', 'pct'),
        FF('Rank by income', 'COUNTIFS({range:src_value.income},">"&INDEX({range:src_value.income},MATCH({pick},{range:src_value.source},0)))+1', 'int'),
        FF('Gift value', 'INDEX({range:sources.gift_value},MATCH({pick},{range:sources.source},0))', 'money')]),
    FORM('session_sheet', 'Class Session Sheet', 'Class session plan: seats, price, cost and break-even', 'class_sessions.session_id', F(
        ('Date', 'class_sessions.date'), ('Class', 'class_sessions.class'), ('Venue', 'class_sessions.venue'), ('Instructor', 'class_sessions.instructor'), ('Seats', 'class_sessions.seats'), ('Signed up', 'class_sessions.signed_up'),
        ('Price per seat', 'class_sessions.price'), ('Hours', 'class_sessions.hours'), ('Venue cost', 'class_sessions.venue_cost'), ('Instructor cost', 'class_sessions.instr_cost'), ('Total cost', 'class_sessions.cost'),
        ('Break-even sign-ups', 'class_sessions.breakeven'), ('Seats left', 'class_sessions.seats_left'), ('Break-even check', 'class_sessions.class_flag'))),
    FORM('signup_sheet', 'Class Sign-up Sheet', 'Sign-up list of a class session', 'class_sessions.session_id', F(
        ('Date', 'class_sessions.date'), ('Class', 'class_sessions.class'), ('Venue', 'class_sessions.venue'), ('Seats', 'class_sessions.seats'), ('Signed up', 'class_sessions.signed_up'), ('Seats left', 'class_sessions.seats_left'),
        ('Price per seat', 'class_sessions.price'), ('Income', 'class_sessions.income')) + [
        FF('Sign-ups listed below', 'COUNTIFS({range:class_attendees.session_id},{pick})', 'int'),
        FF('Paid so far', 'SUMIFS({range:class_attendees.paid},{range:class_attendees.session_id},{pick})', 'money')],
        {"from": "class_attendees", "match": "class_attendees.session_id", "columns": ["attendee", "phone", "paid"], "max": 20}),
    FORM('attendance_sheet', 'Class Attendance Sheet', 'Attendance of a class session', 'class_sessions.session_id', F(
        ('Date', 'class_sessions.date'), ('Class', 'class_sessions.class'), ('Instructor', 'class_sessions.instructor'), ('Signed up', 'class_sessions.signed_up'), ('Attended', 'class_sessions.attended'), ('New clients', 'class_sessions.new_clients')) + [
        FF('Signed up and did not come', 'MAX(0,%s-%s)' % (LK('class_sessions', 'session_id', 'signed_up'), LK('class_sessions', 'session_id', 'attended')), 'int'),
        FF('Attendance rate', 'IFERROR(%s/%s,0)' % (LK('class_sessions', 'session_id', 'attended'), LK('class_sessions', 'session_id', 'signed_up')), 'pct'),
        FF('Attendees listed as came', 'COUNTIFS({range:class_attendees.session_id},{pick},{range:class_attendees.came},1)', 'int')],
        {"from": "class_attendees", "match": "class_attendees.session_id", "columns": ["attendee", "attended", "client_id"], "max": 20}),
    FORM('feedback_sheet', 'Class Feedback Sheet', 'Result of a class session against its class type', 'class_econ.session_id', F(
        ('Class', 'class_econ.class'), ('Date', 'class_econ.date'), ('Signed up', 'class_econ.signed_up'), ('Income', 'class_econ.income'), ('Total cost', 'class_econ.cost'), ('Profit', 'class_econ.profit'),
        ('Profit per class hour', 'class_econ.profit_hour'), ('Type average per hour', 'class_econ.type_avg'), ('Against the type average', 'class_econ.vs_type'), ('Break-even check', 'class_econ.flag')) + [
        FF('New clients from the session', 'INDEX({range:class_sessions.new_clients},MATCH({pick},{range:class_sessions.session_id},0))', 'int'),
        FF('Attended', 'INDEX({range:class_sessions.attended},MATCH({pick},{range:class_sessions.session_id},0))', 'int'),
        FF('Instructor', 'INDEX({range:class_sessions.instructor},MATCH({pick},{range:class_sessions.session_id},0))', 'text')]),
    FORM('review_request_sheet', 'Review Request Sheet', 'Review request for one client', 'review_due.client', F(
        ('Doula', 'review_due.doula'), ('Attended on', 'review_due.attended_on'), ('Request date', 'review_due.request_date'), ('Request check', 'review_due.status'), ('Client phone', 'review_due.phone')) + [
        FF('Days since the birth', '{today}-%s' % LK('review_due', 'client', 'attended_on'), 'int'),
        FF('Days since the request date', '{today}-%s' % LK('review_due', 'client', 'request_date'), 'int'),
        FF('Average stars of this doula', 'IFERROR(ROUND(AVERAGEIFS({range:reviews.stars},{range:reviews.doula},%s),2),0)' % LK('review_due', 'client', 'doula'), 'num')]),
    FORM('testimonial_sheet', 'Testimonial Permission Sheet', 'Review with the permission to use the words', 'reviews.review_id', F(
        ('Client', 'reviews.client'), ('Doula', 'reviews.doula'), ('Asked on', 'reviews.asked_on'), ('Received on', 'reviews.received_on'), ('Stars', 'reviews.stars'), ('Channel', 'reviews.channel'),
        ('Days to answer', 'reviews.days_answer'), ('Client phone', 'reviews.phone')) + [
        FF('Reviews of this doula', 'COUNTIFS({range:reviews.doula},%s,{range:reviews.answered},1)' % LK('reviews', 'review_id', 'doula'), 'int'),
        FF('Average stars of this doula', 'IFERROR(ROUND(AVERAGEIFS({range:reviews.stars},{range:reviews.doula},%s),2),0)' % LK('reviews', 'review_id', 'doula'), 'num')]),
    FORM('marketing_sheet', 'Marketing Spend Sheet', 'Marketing spend and what it brought', 'marketing.campaign_id', F(
        ('Month', 'marketing.month'), ('Kind', 'marketing.kind'), ('Source', 'marketing.source'), ('Cost', 'marketing.cost'), ('Enquiries', 'marketing.enquiries'), ('Signed clients', 'marketing.signed'),
        ('Cost per enquiry', 'marketing.cost_enq'), ('Cost per signed client', 'marketing.cost_signed')) + [
        FF('Cost per signed client you accept', '{set:cac_max}', 'money'),
        FF('Cost of this kind, 12 months', 'SUMIFS({range:marketing.cost},{range:marketing.kind},%s,%s)' % (LK('marketing', 'campaign_id', 'kind'), MM(12)), 'money'),
        FF('Signed clients of this kind, 12 months', 'SUMIFS({range:marketing.signed},{range:marketing.kind},%s,%s)' % (LK('marketing', 'campaign_id', 'kind'), MM(12)), 'int')]),
    FORM('event_sheet', 'Event Sign-up Sheet', 'Class type sheet with sessions, fill and clients', 'class_types.class', F(
        ('Price per seat', 'class_types.price'), ('Seats', 'class_types.seats')) + [
        FF('Sessions held', 'INDEX({range:ctype_stats.sessions},MATCH({pick},{range:ctype_stats.class},0))', 'int'),
        FF('Profit per class hour', 'INDEX({range:ctype_stats.profit_hour},MATCH({pick},{range:ctype_stats.class},0))', 'money'),
        FF('Average sign-ups per session', 'IFERROR(ROUND(AVERAGEIFS({range:class_sessions.signed_up},{range:class_sessions.class},{pick}),1),0)', 'num'),
        FF('Average fill', 'IFERROR(SUMIFS({range:class_sessions.signed_up},{range:class_sessions.class},{pick})/SUMIFS({range:class_sessions.seats},{range:class_sessions.class},{pick}),0)', 'pct'),
        FF('Last session', 'SUMPRODUCT(MAX(({range:class_sessions.class}={pick})*{range:class_sessions.date}))', 'date'),
        FF('New clients from this class', 'SUMIFS({range:class_sessions.new_clients},{range:class_sessions.class},{pick})', 'int'),
        FF('Next class date', '{set:next_class_date}', 'date')]),
    FORM('partner_sheet', 'Partner Contact Sheet', 'Partner contact with referral history', 'referrers.referrer', F(
        ('Phone', 'referrers.phone'), ('Source', 'referrers.source'), ('Referrals', 'referrers.referrals'), ('Clients', 'referrers.clients'), ('Income', 'referrers.income'), ('Gift cost', 'referrers.gift_cost'),
        ('Referrals, last 12 months', 'referrers.last12'), ('Referrals, 12 months before', 'referrers.prev12'), ('Last referral', 'referrers.last_referral'), ('Last thanked on', 'referrers.last_thanked'),
        ('Thank-you check', 'referrers.thank_due'), ('Next step', 'referrers.action'), ('Rank by income', 'referrers.rank')),
        {"from": "referrals", "match": "referrals.referrer", "columns": ["date", "client", "thank_flag", "gift_cost"], "max": 12}),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('office_letter_doc', 'Thank-you Letter Office', 'Thank-you letter to a care-provider office', 'referrers.referrer', [
        'Thank-you letter of {set:company}, dated {today}. Dear {col:referrers.referrer},',
        'Thank you for the people you sent to us. In the last 12 months you referred {col:referrers.last12} people, and {col:referrers.clients} clients have come to us through you in all.',
        'We keep our work simple: dates, hours and clear prices, with each client\'s care staying with their own care provider. We would be glad to visit you, share our information sheet and hear how we can make referring easier.',
        'With thanks, and we hope to stay in touch.'], ['Owner-doula'], NOTE),
    DOC('past_note_doc', 'Thank-you Note', 'Thank-you note to a past client who referred us', 'referrals.referral_id', [
        'Thank-you note of {set:company}, dated {today}. Dear {col:referrals.referrer},',
        'Thank you for recommending us. Your referral of {col:referrals.date} meant a great deal to us, and we are glad you thought of us.',
        'Please accept this small gift as a thank-you. If you know someone else who might like to hear about our work, we would be happy to talk with them.', 'With warm thanks.'], ['Owner-doula'], NOTE),
    DOC('flyer_doc', 'Class Flyer', 'Class flyer with date, venue and price', 'class_sessions.session_id', [
        '{col:class_sessions.class}. A class by {set:company}.',
        'Date: {col:class_sessions.date}. Venue: {col:class_sessions.venue}. Length: {col:class_sessions.hours} hours. Led by {col:class_sessions.instructor}.',
        'Price per seat: {col:class_sessions.price}. Seats: {col:class_sessions.seats}, seats left today: {col:class_sessions.seats_left}.',
        'To hold a seat, reply to this flyer or contact {set:company}. The class gives general information only; for any personal question, ask your own care provider.'], ['Owner-doula'], NOTE),
    DOC('confirm_doc', 'Class Confirmation', 'Confirmation of a seat in a class', 'class_attendees.attendee_id', [
        'Class confirmation of {set:company}, dated {today}. Dear {col:class_attendees.attendee},',
        'Your seat for {col:class_attendees.class} on {col:class_attendees.date} is confirmed. Amount paid: {col:class_attendees.paid}. Please keep this page.',
        'If you cannot come, tell us as early as you can so that we can offer the seat to someone else. Our next class date is {col:class_attendees.next_class}.'], ['Owner-doula'], NOTE),
    DOC('attendance_doc', 'Class Attendance Record', 'Attendance record of a class session', 'class_sessions.session_id', [
        'Attendance record of {set:company}, dated {today}. Session {col:class_sessions.session_id}: {col:class_sessions.class} on {col:class_sessions.date} at {col:class_sessions.venue}.',
        'Instructor: {col:class_sessions.instructor}. Seats: {col:class_sessions.seats}. Signed up: {col:class_sessions.signed_up}. Attended: {col:class_sessions.attended}. New clients from the session: {col:class_sessions.new_clients}.',
        'This record holds counts and dates only. Keep it with your class records and check your local rules for how long to keep it.'], ['Instructor', 'Owner-doula'], NOTE),
    DOC('handout_doc', 'Workshop Handout Cover', 'Cover page for a workshop handout', 'class_types.class', [
        '{col:class_types.class}', 'Workshop handout of {set:company}, dated {today}.',
        'Usual price per seat: {col:class_types.price}. Seats in the room: {col:class_types.seats}. Next class: {set:next_class_name} on {set:next_class_date}.',
        'This handout gives general information only. For any personal question, ask your own care provider.'], ['Instructor'], NOTE),
    DOC('review_letter_doc', 'Review Request Letter', 'Letter asking a client for a review', 'review_due.client', [
        'Review request of {set:company}, dated {today}. Dear {col:review_due.client},',
        'It was our pleasure to work with you. {col:review_due.doula} supported you, and your birth was attended on {col:review_due.attended_on}. Would you take two minutes to give your stars and a few words about your time with us?',
        'Your review helps other clients find us. If you would rather not, there is no need to reply. Thank you.'], ['Owner-doula'], NOTE),
    DOC('permission_doc', 'Testimonial Permission Form', 'Permission to use a review on our pages', 'reviews.review_id', [
        'Testimonial permission of {set:company}, dated {today}.',
        'I, {col:reviews.client}, gave {col:reviews.stars} stars on {col:reviews.received_on} through {col:reviews.channel}. I allow {set:company} to use my words and my stars on its website and printed pages, with my first name and family initial only.',
        'I may withdraw this permission at any time by telling {set:company}. Check your local rules on consent before you publish.'], ['Client', 'Owner-doula'], NOTE),
    DOC('referral_report_doc', 'Referral Report', 'Referral report for one referrer', 'referrers.referrer', [
        'Referral report of {set:company}, dated {today}. Referrer: {col:referrers.referrer}. Source: {col:referrers.source}. Rank by income: {col:referrers.rank}.',
        'Referrals: {col:referrers.referrals}. Clients: {col:referrers.clients}. Income of those clients: {col:referrers.income}. Gift cost: {col:referrers.gift_cost}.',
        'Referrals in the last 12 months: {col:referrers.last12}, against {col:referrers.prev12} in the 12 months before. Last referral: {col:referrers.last_referral}. Last thanked on: {col:referrers.last_thanked}.',
        'Thank-you check: {col:referrers.thank_due}. Next step: {col:referrers.action}.'], ['Owner-doula'], NOTE),
    DOC('marketing_summary_doc', 'Marketing Summary', 'Marketing summary for one source', 'src_cost.source', [
        'Marketing summary of {set:company}, dated {today}. Source: {col:src_cost.source}.',
        'Cost of gifts and fees: {col:src_cost.cost}. Cost per signed client: {col:src_cost.cost_signed}. Cost per signed client you accept: {set:cac_max}.',
        'Use this page for the monthly marketing review: keep what costs less than you accept, renegotiate what costs more, and drop what brings no clients.'], ['Owner-doula'], NOTE),
    DOC('intro_letter_doc', 'Partner Introduction Letter', 'Introduction letter to a new partner', 'referrers.referrer', [
        'Introduction letter of {set:company}, dated {today}. Dear {col:referrers.referrer},',
        'We are a small doula business. We help clients plan dates, hours and support around a birth, and each client\'s care stays with their own care provider; questions about care go to them.',
        'We would be glad to meet you, leave our information sheet and talk about how we can work together. Please call us on {col:referrers.owner_phone} to arrange a short visit.'], ['Owner-doula'], NOTE),
    DOC('class_income_doc', 'Class Income Report', 'Income, cost and profit of a class session', 'class_econ.session_id', [
        'Class income report of {set:company}, dated {today}. Session {col:class_econ.session_id}: {col:class_econ.class} on {col:class_econ.date}.',
        'Signed up: {col:class_econ.signed_up}. Income: {col:class_econ.income}. Total cost: {col:class_econ.cost}. Profit: {col:class_econ.profit}. Profit per class hour: {col:class_econ.profit_hour}.',
        'Break-even sign-ups: {col:class_econ.breakeven}. Break-even check: {col:class_econ.flag}. The average for this class type is {col:class_econ.type_avg} per class hour.'], ['Owner-doula'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('new_referral', 'New Referral Steps', 'referrals', 'referrals.date', [('Write the referral in the Referral Log', 0), ('Reply to the enquiry within your target hours', 0), ('Tell the referrer the enquiry was received', 1), ('Book the consultation', 3), ('Check the source is correct', 7)]),
    CHK('thank_sent', 'Thank-you Sent Steps', 'referrals', 'referrals.date', [('Check that the referral became a client', 14), ('Choose the thank-you gift', 15), ('Send the thank-you and the gift', 17), ('Write the date in Thanked on', 17), ('Write the gift cost', 18)]),
    CHK('class_plan', 'Class Planning Steps', 'class_sessions', 'class_sessions.date', [('Choose the class, the date and the price', -42), ('Book the venue', -35), ('Set the seats and the break-even sign-ups', -35), ('Make the flyer', -28), ('Send the invitations', -21), ('Check the sign-ups against break-even', -7)]),
    CHK('class_day', 'Class Day Steps', 'class_sessions', 'class_sessions.date', [('Send the reminder the day before', -1), ('Print the sign-up sheet', -1), ('Arrive early and check the room', 0), ('Take the attendance', 0), ('Hand out the information sheet', 0), ('Collect any payment due', 0)]),
    CHK('after_class', 'After the Class Steps', 'class_sessions', 'class_sessions.date', [('Write the attendance and the new clients', 0), ('Send the thank-you to everyone who came', 1), ('Ask for feedback', 2), ('Pay the venue and the instructor', 7), ('Check the profit per class hour', 7), ('Follow up with the enquiries from the class', 7)]),
    CHK('review_request', 'Review Request Steps', 'reviews', 'reviews.asked_on', [('Send the review request', 0), ('Note the date in Asked on', 0), ('Send one reminder', 14), ('Write the stars and the channel when it arrives', 21)]),
    CHK('review_received', 'Review Received Steps', 'reviews', 'reviews.asked_on', [('Write the date in Received on', 21), ('Write the stars and the channel', 21), ('Thank the client for the review', 22), ('Ask permission to use the words', 23), ('Ask for a referral if the stars are high', 30)]),
    CHK('permission', 'Testimonial Permission Steps', 'reviews', 'reviews.asked_on', [('Send the permission form', 22), ('Wait for the signed form', 29), ('Keep the form with your records', 30), ('Publish only what was allowed', 31)]),
    CHK('marketing_review', 'Marketing Review Steps', 'marketing', 'marketing.month', [('List the spend of the month', 30), ('Write the enquiries and signed clients', 35), ('Check the cost per signed client', 36), ('Keep, renegotiate or drop each kind', 37), ('Set next month\'s spend', 38)]),
    CHK('monthly_review', 'Monthly Referral Review Steps', 'review_month', 'review_month.month', [('Open the Referrer Ranking', 30), ('Send the thank-yous that are due', 31), ('Read the Referral Gap List', 32), ('Plan one partner visit', 33), ('Check the source mix', 34)]),
    CHK('partner_visit', 'Partner Visit Steps', 'gaps', 'gaps.visited_on', [('Call to book the visit', -7), ('Prepare the information sheet', -2), ('Visit the partner', 0), ('Send a thank-you note', 1), ('Write what you agreed', 1), ('Plan the next visit', 90)]),
    CHK('class_calendar', 'Yearly Class Calendar Steps', 'class_sessions', 'class_sessions.date', [('Look at last year\'s sessions by month', 0), ('Mark the quiet months', 7), ('Set the sessions for each month', 14), ('Book the venue dates for the first quarter', 21), ('Publish the class dates', 28), ('Send the dates to your partners', 35)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('r_thanks', 'Referrer: thanks for sending a client', 'referrals', 'referrals.referrer_phone', 'Hello {referrer}, thank you for sending {client} to {company}. We are glad you thought of us.'),
    M('r_received', 'Referrer: your referral was received', 'referrals', 'referrals.referrer_phone', 'Hello {referrer}, we received your referral {enquiry_id} on {date}. We will contact them soon. {company}'),
    M('r_signed', 'Referrer: your referral signed', 'referrals', 'referrals.referrer_phone', 'Hello {referrer}, {client} signed with us after your referral. Thank you. {company}'),
    M('sp_thanks', 'Support professional: thank you', 'referrals', 'referrals.referrer_phone', 'Hello {referrer}, thank you for the referral of {client}. We value your trust. {company}'),
    M('r_quarter', 'Referrer: a small thank-you', 'referrers', 'referrers.phone', 'Hello {referrer}, a small thank-you from {company} for the {referrals_q} referrals you sent us recently.'),
    M('r_visit', 'Referrer: may we visit', 'referrers', 'referrers.phone', 'Hello {referrer}, we would love to stay in touch. May we visit you soon to say thank you? {company}'),
    M('r_sheet', 'Referrer: our information sheet', 'referrers', 'referrers.phone', 'Hello {referrer}, here is our information sheet to share with your clients: packages, dates and prices. {company}'),
    M('o_thankdue', 'Owner: a thank-you is due', 'referrers', 'referrers.owner_phone', 'Hello {owner_name}, {referrer} sent {clients_q} clients recently and {due_n} thank-yous are due. {company}'),
    M('o_silent', 'Owner: a referrer has gone silent', 'referrers', 'referrers.owner_phone', 'Hello {owner_name}, {referrer} has sent none this year, {prev12} the year before. Follow-up on {follow_up}. {company}'),
    M('p_review1', 'Past client: would you leave a review', 'reviews', 'reviews.phone', 'Hello {client}, congratulations again. Would you leave a short review of your time with {doula}? {company}'),
    M('p_review2', 'Past client: your review request', 'reviews', 'reviews.phone', 'Hello {client}, your review request: it takes 2 minutes and helps others find us. {company}'),
    M('p_remind', 'Past client: a reminder for your review', 'reviews', 'reviews.phone', 'Hello {client}, a gentle reminder about the review we asked for on {asked_on}. Thank you. {company}'),
    M('p_stars', 'Past client: thank you for your stars', 'reviews', 'reviews.phone', 'Hello {client}, thank you for your review of {stars} stars. It means a lot to us. {company}'),
    M('p_permission', 'Past client: may we use your words', 'reviews', 'reviews.phone', 'Hello {client}, may we use your words from your review on our website? Please reply yes or no. {company}'),
    M('p_recommend', 'Past client: would you recommend us', 'reviews', 'reviews.phone', 'Hello {client}, would you recommend us to a friend who is looking for a doula? Thank you. {company}'),
    M('p_class', 'Past client: you are invited to a class', 'reviews', 'reviews.phone', 'Hello {client}, you are invited to our next class on {next_class}. Reply to book a seat. {company}'),
    M('e_invite', 'Enquirer: you are invited to a class', 'enquiries', 'enquiries.phone', 'Hello {name}, you are invited to the class on {next_class}. Reply to hold a seat. {company}'),
    M('e_series', 'Enquirer: the next class series', 'enquiries', 'enquiries.phone', 'Hello {name}, the next class series starts on {next_class}. Would you like a seat? {company}'),
    M('e_seat', 'Enquirer: your seat is booked', 'class_attendees', 'class_attendees.phone', 'Hello {attendee}, your seat for {class} on {date} is booked. {company}'),
    M('e_remind', 'Enquirer: your class is tomorrow', 'class_attendees', 'class_attendees.phone', 'Hello {attendee}, a reminder: your class {class} is tomorrow, {date}. {company}'),
    M('e_packages', 'Enquirer: thank you for coming', 'class_attendees', 'class_attendees.phone', 'Hello {attendee}, thank you for coming to {class}. Reply and we will send our packages. {company}'),
    M('a_cancel', 'Attendee: the class is cancelled', 'class_attendees', 'class_attendees.phone', 'Hello {attendee}, the class on {date} is cancelled. A new date is {next_class}. Sorry for the change. {company}'),
    M('a_refund', 'Attendee: your seat is refunded', 'class_attendees', 'class_attendees.phone', 'Hello {attendee}, your seat is refunded: {paid} goes back to you. {company}'),
    M('a_feedback', 'Attendee: tell us what you thought', 'class_attendees', 'class_attendees.phone', 'Hello {attendee}, please tell us what you thought of {class} on {date}. {company}'),
    M('o_seats', 'Owner: seats booked for a class', 'class_sessions', 'class_sessions.owner_phone', 'Hello {owner_name}, the class on {date} has {signed_up} of {seats} seats booked. {company}'),
    M('o_below', 'Owner: a class is below break-even', 'class_sessions', 'class_sessions.owner_phone', 'Hello {owner_name}, the class on {date} ({class}) has {signed_up} sign-ups and needs {breakeven} to break even. {company}'),
    M('o_reviews', 'Owner: reviews asked this month', 'team', 'team.phone', 'Hello {name}, reviews asked this month are {reviews_month}. {company}'),
    M('o_stars', 'Owner: your stars this quarter', 'team', 'team.phone', 'Hello {name}, your average stars this quarter are {stars_q}. {company}'),
    M('o_mkt', 'Owner: marketing cost per signed client', 'team', 'team.phone', 'Hello {name}, marketing cost per signed client over 12 months is {cost_signed_12}. {company}'),
    M('o_topsrc', 'Owner: the top source by income', 'team', 'team.phone', 'Hello {name}, {top_source} is the top source by income: {top_income}. {company}'),
    M('v_book', 'Class venue: we would like to book', 'class_sessions', 'class_sessions.venue_phone', 'Hello {venue_contact}, we would like to book {date} for {class} at your venue. {company}'),
    M('v_cancel', 'Class venue: the class is cancelled', 'class_sessions', 'class_sessions.venue_phone', 'Hello {venue_contact}, the class on {date} ({class}) is cancelled. Sorry for the change. {company}'),
    M('v_dates', 'Class venue: our dates next quarter', 'class_sessions', 'class_sessions.venue_phone', 'Hello {venue_contact}, our class dates for the next quarter start on {next_class}. May we hold the room? {company}'),
    M('ph_ask', 'Photographer: a client asks about photos', 'clients', 'clients.photographer_phone', 'Hello {photographer}, our client {client} asks about photography around the estimated due date, {edd}. May we call you? {company}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30), dashboard, insights
S_TOT = 'COUNTIFS(%s,{range:contracts.status},"<>"&%s)' % (DM('contracts.signed_on', 12), CANC)
S_REF = 'COUNTIFS({range:contracts.from_referral},1,%s,{range:contracts.status},"<>"&%s)' % (DM('contracts.signed_on', 12), CANC)
X_CNT = 'COUNTIFS({range:contracts.source},{range:sources.source},%s,{range:contracts.status},"<>"&%s)' % (DM('contracts.signed_on', 12), CANC)
kpis = [
    KPI('Referrals this month', 'COUNTIFS({range:referrals.month},%s)' % MS, 'int'),
    KPI('Referrals, last 90 days', 'COUNTIFS(%s)' % DW('referrals.date', 90), 'int'),
    KPI('Clients from referrals, 12 months', S_REF, 'int'),
    KPI('Income from referrals, 12 months', 'SUMIFS({range:contracts.price},{range:contracts.from_referral},1,%s,{range:contracts.status},"<>"&%s)' % (DM('contracts.signed_on', 12), CANC), 'money'),
    KPI('Referral share of clients, 12 months', 'IFERROR(%s/%s,0)' % (S_REF, S_TOT), 'pct', alert={"when": "< {set:ref_share_target}", "style": "warn"}),
    KPI('Best source by income', 'IFERROR(INDEX({range:src_value.source},MATCH(MAX({range:src_value.income}),{range:src_value.income},0))&"","")', 'text'),
    KPI('Best source by income per client', 'IFERROR(INDEX({range:src_value.source},MATCH(MAX({range:src_value.income_client}),{range:src_value.income_client},0))&"","")', 'text'),
    KPI('Care-provider referrals, 12 months', 'COUNTIFS({range:referrals.source},%s,%s)' % (CARE, DW('referrals.date', 365)), 'int'),
    KPI('Past-client referrals, 12 months', 'COUNTIFS({range:referrals.source},%s,%s)' % (PAST, DW('referrals.date', 365)), 'int'),
    KPI('Thank-yous due', 'COUNTIFS({range:referrals.thank_flag},%s)' % DUE, 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Thanked share, last 90 days', 'IFERROR(COUNTIFS(%s,{range:referrals.signed},1,{range:referrals.thanked},1)/COUNTIFS(%s,{range:referrals.signed},1),0)' % (DW('referrals.date', 90), DW('referrals.date', 90)), 'pct'),
    KPI('Referrers silent this year', 'SUM({range:referrers.silent})', 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Gift cost, last 12 months', 'SUMIFS({range:referrals.gift_cost},%s)' % DW('referrals.date', 365), 'money'),
    KPI('Marketing spend this month', 'SUMIFS({range:marketing.cost},{range:marketing.month},%s)' % MS, 'money'),
    KPI('Marketing cost per signed client', 'IFERROR(SUMIFS({range:marketing.cost},%s)/SUMIFS({range:marketing.signed},%s),0)' % (MM(12), MM(12)), 'money', alert={"when": "> {set:cac_max}", "style": "warn"}),
    KPI('Class sessions this month', 'COUNTIFS({range:class_sessions.month},%s)' % MS, 'int'),
    KPI('Class sessions, last 12 months', 'COUNTIFS(%s)' % DM('class_sessions.date', 12), 'int'),
    KPI('Class sign-ups, last 90 days', 'SUMIFS({range:class_sessions.signed_up},%s)' % DW('class_sessions.date', 90), 'int'),
    KPI('Average class fill, 12 months', 'IFERROR(SUMIFS({range:class_sessions.signed_up},%s)/SUMIFS({range:class_sessions.seats},%s),0)' % (DM('class_sessions.date', 12), DM('class_sessions.date', 12)), 'pct', alert={"when": "< {set:class_fill_target}", "style": "warn"}),
    KPI('Class income, last 12 months', 'SUMIFS({range:class_sessions.income},%s)' % DM('class_sessions.date', 12), 'money'),
    KPI('Class profit, last 12 months', 'SUMIFS({range:class_sessions.profit},%s)' % DM('class_sessions.date', 12), 'money'),
    KPI('Class profit per class hour', 'IFERROR(SUMIFS({range:class_sessions.profit},%s)/SUMIFS({range:class_sessions.hours},%s),0)' % (DM('class_sessions.date', 12), DM('class_sessions.date', 12)), 'money', alert={"when": "< {set:class_hour_target}", "style": "warn"}),
    KPI('Clients from classes, 12 months', 'SUMIFS({range:class_sessions.new_clients},%s)' % DM('class_sessions.date', 12), 'int'),
    KPI('Sessions below break-even, 12 months', 'COUNTIFS(%s,{range:class_sessions.above},0)' % DM('class_sessions.date', 12), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Reviews asked, last 90 days', 'COUNTIFS(%s)' % DW('reviews.asked_on', 90), 'int'),
    KPI('Reviews received, last 90 days', 'COUNTIFS(%s)' % DW('reviews.received_on', 90), 'int'),
    KPI('Review response rate, 90 days', 'IFERROR(COUNTIFS(%s,{range:reviews.answered},1)/COUNTIFS(%s),0)' % (DW('reviews.asked_on', 90), DW('reviews.asked_on', 90)), 'pct', alert={"when": "< {set:review_rate_min}", "style": "warn"}),
    KPI('Average stars, last 12 months', 'IFERROR(AVERAGEIFS({range:reviews.stars},%s),0)' % DM('reviews.received_on', 12), 'num', alert={"when": "< {set:star_target}", "style": "warn"}),
    KPI('Review requests due now', 'COUNTIFS({range:review_due.status},%s)' % ASK, 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Share of clients from the top source', 'IFERROR(SUMPRODUCT(MAX(%s))/%s,0)' % (X_CNT, S_TOT), 'pct', alert={"when": "> {set:top_source_max}", "style": "warn"}),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Referrals Dashboard", "kpis": kpis,
    "monthly": {"title": "Class income, venue cost, marketing cost and gift cost", "date": "class_sessions.date", "series": [
        {"label": "Class income", "sum": "class_sessions.income", "date": "class_sessions.date"}, {"label": "Venue cost", "sum": "class_sessions.venue_cost", "date": "class_sessions.date"},
        {"label": "Marketing cost", "sum": "marketing.cost", "date": "marketing.month"}, {"label": "Gift cost", "sum": "referrals.gift_cost", "date": "referrals.date"}]},
    "breakdowns": [{"title": "Referrals by source", "by": "referrals.source", "value": "referrals.gift_cost", "agg": "count"}, {"title": "Class income by type", "by": "class_sessions.class", "value": "class_sessions.income", "agg": "sum"},
                   {"title": "Marketing cost by kind", "by": "marketing.kind", "value": "marketing.cost", "agg": "sum"}, {"title": "Reviews by channel", "by": "reviews.channel", "value": "reviews.stars", "agg": "count"}]}
def SRC(s): return [('source', '=', tok('source', s))]
insights = {"filters": [{"label": "Source", "list": "source"}, {"label": "Class type", "list": "ctype"}, {"label": "Doula", "list": "doula"}],
    "gauges": [
        {"title": "Referrers thanked in time", "num": AGG('count', 'referrals', where=[('in_time', '=', 1)]), "den": AGG('count', 'referrals', where=[('matured', '=', 1)])},
        {"title": "Sessions at or above break-even", "num": AGG('count', 'class_sessions', where=[('above', '=', 1)]), "den": AGG('count', 'class_sessions')},
        {"title": "Sessions filled to your target", "num": AGG('count', 'class_sessions', where=[('fill_ok', '=', 1)]), "den": AGG('count', 'class_sessions')},
        {"title": "Reviews answered quickly", "num": AGG('count', 'reviews', where=[('quick', '=', 1)]), "den": AGG('count', 'reviews', where=[('old_enough', '=', 1)])},
        {"title": "Reviews with four or five stars", "num": AGG('count', 'reviews', where=[('good', '=', 1)]), "den": AGG('count', 'reviews', where=[('answered', '=', 1)])},
        {"title": "Income share from referrals", "num": AGG('sum', 'contracts', 'contracts.price', where=[('from_referral', '=', 1), ('status', '<>', CANC)]), "den": AGG('sum', 'contracts', 'contracts.price', where=[('status', '<>', CANC)])}],
    "charts": [
        CHART('Referrals per month', 'column', 'month', [AGG('count', 'referrals', date='referrals.date', label='Referrals')]),
        CHART('Referrals by source', 'bar', 'referrals.source', [AGG('count', 'referrals', label='Referrals')]),
        CHART('Referrals by referrer', 'bar', 'referrals.referrer', [AGG('count', 'referrals', label='Referrals')]),
        CHART('Referrals thanked per month', 'column', 'month', [AGG('count', 'referrals', date='referrals.date', where=[('thanked', '=', 1)], label='Thanked'), AGG('count', 'referrals', date='referrals.date', where=[('signed', '=', 1)], label='Became clients')]),
        CHART('Enquiries by source', 'bar', 'enquiries.source', [AGG('count', 'enquiries', label='Enquiries')]),
        CHART('Clients signed by source', 'bar', 'clients.source', [AGG('count', 'clients', label='Clients')]),
        CHART('Signed clients per month by source', 'stacked', 'month', [AGG('count', 'clients', date='clients.signed_on', where=SRC(s), label=s) for s in ('Care provider', 'Past client', 'Online search', 'Social media')]),
        CHART('Marketing cost per month', 'column', 'month', [AGG('sum', 'marketing', 'marketing.cost', date='marketing.month', label='Marketing cost')]),
        CHART('Marketing cost by kind', 'bar', 'marketing.kind', [AGG('sum', 'marketing', 'marketing.cost', label='Cost')]),
        CHART('Marketing enquiries by kind', 'bar', 'marketing.kind', [AGG('sum', 'marketing', 'marketing.enquiries', label='Enquiries')]),
        CHART('Marketing signed clients by kind', 'bar', 'marketing.kind', [AGG('sum', 'marketing', 'marketing.signed', label='Signed clients')]),
        CHART('Class sessions per month', 'column', 'month', [AGG('count', 'class_sessions', date='class_sessions.date', label='Sessions')]),
        CHART('Class sessions by type', 'bar', 'class_sessions.class', [AGG('count', 'class_sessions', label='Sessions')]),
        CHART('Class income per month', 'column', 'month', [AGG('sum', 'class_sessions', 'class_sessions.income', date='class_sessions.date', label='Class income')]),
        CHART('Class income by type', 'bar', 'class_sessions.class', [AGG('sum', 'class_sessions', 'class_sessions.income', label='Class income')]),
        CHART('Class sign-ups per month', 'column', 'month', [AGG('sum', 'class_sessions', 'class_sessions.signed_up', date='class_sessions.date', label='Sign-ups'), AGG('sum', 'class_sessions', 'class_sessions.seats', date='class_sessions.date', label='Seats')]),
        CHART('Class attendees per month', 'column', 'month', [AGG('sum', 'class_sessions', 'class_sessions.attended', date='class_sessions.date', label='Attended')]),
        CHART('Class new clients per month', 'column', 'month', [AGG('sum', 'class_sessions', 'class_sessions.new_clients', date='class_sessions.date', label='New clients')]),
        CHART('Reviews asked per month', 'column', 'month', [AGG('sum', 'review_month', 'review_month.asked', date='review_month.month', label='Asked')]),
        CHART('Reviews received per month', 'column', 'month', [AGG('sum', 'review_month', 'review_month.received', date='review_month.month', label='Received')]),
        CHART('Reviews by doula', 'bar', 'reviews.doula', [AGG('count', 'reviews', label='Reviews asked')]),
        CHART('Reviews by channel', 'bar', 'reviews.channel', [AGG('count', 'reviews', label='Reviews received')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Referral source value ranker", "why": "ranks every source by income and not by count, with the cost of gifts and fees and a feed, hold or cut verdict", "where": "Source Value Ranker"},
    {"name": "Referral gap list", "why": "names the referrers who sent clients before and none now, with the date to follow up", "where": "Referral Gap List"},
    {"name": "Thank-you due list", "why": "every referral that became a client and was not thanked, with the gift value to send", "where": "Thank-you Due"},
    {"name": "Class and workshop economics", "why": "price, seats, sign-ups, break-even and profit per class hour against your own history of each class", "where": "Class Economics Tool"},
    {"name": "Class break-even solver", "why": "the fewest sign-ups that cover venue cost and instructor time, and the price that would", "where": "Class Break-even Solver"},
    {"name": "Review and testimonial pipeline", "why": "who to ask for a review today and who to remind, with the answer rate against your target", "where": "Review Pipeline"},
    {"name": "Marketing keep or drop", "why": "cost per signed client and months to pay back for each listing, post or flyer", "where": "Marketing Keep or Drop"},
    {"name": "Source mix risk", "why": "the share of clients from your top source and top two, so one source never carries the business", "where": "Source Mix Risk"},
    {"name": "Care provider office planner", "why": "offices ranked by referral trend over 12 months with a visit, thank or hold step for each", "where": "Care Provider Office Planner"},
    {"name": "Class fill forecast", "why": "the next 3 months of class income from your own history, with the quiet December and Base, Best and Worst", "where": "Class Fill Forecast"}]
competitors = [
    {"what": "free client-tracker templates", "lacks": "list clients but never rank referral sources by income, count thank-yous due or show who stopped referring"},
    {"what": "subscription practice-management software", "lacks": "charge every month and give no class break-even, no review pipeline and no gap list for partners"},
    {"what": "generic marketing spreadsheets", "lacks": "total spend but cannot tie it to signed clients, income per client or a keep-or-drop verdict by kind"},
    {"what": "single-sheet class sign-up lists", "lacks": "hold names and seats but know nothing of venue cost, instructor time, profit per class hour or the clients a class brings"},
    {"what": "social review dashboards", "lacks": "count stars but never link a review request to the birth date, the doula or a referral ask afterwards"}]
guide = [
    'Open Start and type your business name and your own limits in the yellow cells: the days for a thank-you, the stars you want, the fill you want, the cost of an instructor hour and the cost per signed client you accept.',
    'Check Sources, Class Types and Team. They hold the gift value of each source, the usual price and seats of each class and the phones the message links read.',
    'Write every referral in Referrals: date, source, referrer, enquiry, client and the thank-you date. The client, income and thank-you check fill in by themselves.',
    'Keep Enquiries, Clients and Contracts up to date: the source of each client decides what every source earned.',
    'Write each class in Class Sessions and each sign-up in Class Attendees. Profit, break-even and fill fill in; Class Economics and Class by Type compare sessions.',
    'Write each review request in Reviews with the date asked, the date received, the stars and the channel. No review text is kept.',
    'Write the marketing spend of each month in Marketing Spend with its enquiries and signed clients. Source Costs and the Marketing Keep or Drop tool read it.',
    'Read Referral Value by Source, Referrer Ranking, Thank-you Due and the Referral Gap List every month to see who to thank and who to visit.',
    f'Use the {len(tools)} tools to rank sources, price classes, plan the class calendar, run the review pipeline, keep or drop marketing and watch the source mix.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Referrals Dashboard and the charts every month. A solo doula uses the same sheets with one doula and fewer sources.']
listing = {"title": "Doula Business Referrals, Classes, Reviews and Marketing Excel Template: Referral Source Value, Class Break-even, Review Tracker",
    "headline": "See which sources, classes and reviews really grow your doula business",
    "tags": ["doula", "doula business", "doula template", "referral tracker", "class planner", "review tracker", "marketing tracker", "excel template", "break even", "thank you list", "source tracking", "workshop income", "business tracker"],
    "description": ("Find out where your doula clients really come from and what keeps them coming, in one Excel workbook. Built for an owner-doula who also takes clients, contracted doulas and a part-time admin, and just as useful for a solo doula with fewer sources. "
        "Referrals records every enquiry sent to you, the referrer, the client it became and the date you said thank you. Referral Value by Source ranks the sources by income and not by count, Source Costs shows the cost of gifts and fees, and Referrer Ranking shows who sent the most and who went quiet.\n\n"
        "Class Sessions and Class Attendees record each class and workshop with seats, sign-ups, venue cost and income. Class Economics, Class by Type and the break-even tools show profit per class hour and the sign-ups you need. Reviews records every review request with stars and channel but no text, and Review Requests Due lists the clients to ask or remind. Marketing Spend ties each listing, post or flyer to enquiries and signed clients.\n\n"
        f"{len(tools)} tools answer the weekly questions: which sources to feed, hold or cut, who to thank, who to visit, what a class earns, how many sign-ups cover a session, whether a price should rise, what the next 3 months of classes will bring, who to ask for a review, which marketing to keep or drop and whether one source carries too much. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to referrers, past clients, enquirers, class attendees, the class venue and the owner-doula.\n\n"
        "This is part seven of the Doula Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Clients appear by name and dates only, with no medical detail. It helps you keep track of dates, hours, money and capacity and does not promise any result. Check your local rules for records, consent and tax."),
    "features": ["Referral sources ranked by income, not by count", "Thank-you due list with gift values", "Referral gap list with follow-up dates", "Class economics with profit per class hour", "Class break-even solver", "Review pipeline with stars and channel",
                 "Marketing keep-or-drop by cost per signed client", f"{len(tools)} decision tools with a verdict", f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts",
                 f"{len(messages)} ready text messages"]}
def _cut(x, n):
    if len(x) <= n: return x
    y = x[:n - 1]
    for sep in ('. ', '; ', ': ', ', '):
        i = y.rfind(sep)
        if i > n * 0.55: return y[:i].rstrip() + '.'
    return y[:y.rfind(' ')].rstrip(' ,;:') + '.'
for _t in tables + tools:
    _t['hint'] = _cut(_t['hint'], 200); _t['title'] = _cut(_t['title'], 60).rstrip('.')
for _f in forms: _f['title'] = _cut(_f['title'], 50).rstrip('.')
s = spec(id=f'{SUITE}-p7', slug='doula-business-referrals', profession='Doula Business', name='Referrals, Classes, Reviews, Marketing',
         tagline='Know which sources, classes and reviews grow your doula business', price_usd=29,
         colors={"primary": "#4A3F6B", "accent": "#E8A87C"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 7, "of": 8, "focus": "Referrals, classes, reviews and marketing"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'du7.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
