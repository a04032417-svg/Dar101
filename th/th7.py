"""Therapy private practice suite - part 7: Referrals, Marketing and Group Programs."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib as _lib
from th7_lists import *
from th7_tables import settings, tables, CA
from th7_tools import tools

SUITE = 'fx-20261115-therapy-practice'
NOTE = "Sample wording: adapt it to your own practice and check your own local rules."
def F(*p): return [FV(a, b) for a, b in p]
def cnt(tb, col, pick): return 'COUNTIFS({range:%s.%s},INDEX({range:%s.%s},MATCH({pick},{range:%s},0)))' % (tb, col, tb, col, pick)
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'

forms = [
 FORM('campaign_sheet', 'Campaign Sheet', 'Campaign with cost per enquiry and per client won', 'campaigns.campaign_id', F(
  ('Date', 'campaigns.date'), ('Activity kind', 'campaigns.kind'), ('Description', 'campaigns.description'), ('Cost', 'campaigns.cost'), ('Enquiries', 'campaigns.enquiries'), ('Clients won', 'campaigns.clients_won'),
  ('Cost per enquiry', 'campaigns.cost_per_enquiry'), ('Cost per client won', 'campaigns.cost_per_client'), ('Cost check', 'campaigns.cost_check'), ('Clients won per 100 spent, same kind', 'campaigns.kind_return')) + [
  FF('Campaigns of the same kind', cnt('campaigns', 'kind', 'campaigns.campaign_id'), 'int'), FF('Total cost of all campaigns', 'SUM({range:campaigns.cost})', 'money')]),
 FORM('referrer_sheet', 'Referrer Profile Sheet', 'Referrer profile with 12-month referrals and value', 'referrers.referrer_id', F(
  ('Name', 'referrers.name'), ('Kind', 'referrers.kind'), ('Phone', 'referrers.phone'), ('Email', 'referrers.email'), ('Referrals, last 12 months', 'referrers.referrals_12m'), ('Booked, last 12 months', 'referrers.booked_12m'),
  ('Value, last 12 months', 'referrers.value_12m'), ('Last contact', 'referrers.last_contact'), ('Days since last contact', 'referrers.days_since'), ('Contact check', 'referrers.contact_check'), ('Next contact by', 'referrers.next_contact'),
  ('Next group program', 'referrers.program'), ('Next group start', 'referrers.start_date')) + [FF('Contacts logged for this referrer', cnt('contacts', 'referrer', 'referrers.name').replace('INDEX({range:contacts.referrer},MATCH({pick},{range:referrers.name},0))', '{pick}') if False else 'COUNTIFS({range:contacts.referrer},INDEX({range:referrers.name},MATCH({pick},{range:referrers.referrer_id},0)))', 'int')]),
 FORM('contact_sheet', 'Referrer Contact Sheet', 'Referrer contact with the next contact date', 'contacts.contact_id', F(
  ('Date', 'contacts.date'), ('Referrer', 'contacts.referrer'), ('Contact kind', 'contacts.contact_kind'), ('Done by', 'contacts.done_by'), ('Next contact', 'contacts.next_contact'), ('Days since', 'contacts.days_since'),
  ('Contact check', 'contacts.contact_flag'), ('Referrer phone', 'contacts.referrer_phone')) + [FF('Contacts with this referrer', cnt('contacts', 'referrer', 'contacts.contact_id'), 'int')]),
 FORM('workshop_sheet', 'Workshop Plan Sheet', 'Workshop or talk plan with cost per attendee', 'workshops.workshop_id', F(
  ('Date', 'workshops.date'), ('Kind', 'workshops.kind'), ('Title', 'workshops.title'), ('Audience', 'workshops.audience'), ('Attendees', 'workshops.attendees'), ('Cost', 'workshops.cost'), ('Enquiries', 'workshops.enquiries'),
  ('Host contact', 'workshops.contact'), ('Host contact phone', 'workshops.contact_phone'), ('Cost per attendee', 'workshops.cost_per_attendee'), ('Enquiries per 100 attendees', 'workshops.enq_per_100')) + [
  FF('Events of the same kind', cnt('workshops', 'kind', 'workshops.workshop_id'), 'int')]),
 FORM('listing_sheet', 'Directory Listing Review Sheet', 'Directory listing review with months to pay back', 'directory.dl_id', F(
  ('Month', 'directory.month'), ('Directory listing', 'directory.listing'), ('Cost', 'directory.cost'), ('Profile views', 'directory.profile_views'), ('Enquiries', 'directory.enquiries'), ('Clients won', 'directory.clients_won'),
  ('Clients won per enquiry', 'directory.booked_share'), ('Cost per client won', 'directory.cost_per_client'), ('Months to pay back one listing', 'directory.payback_months'), ('Payback check', 'directory.payback_check')) + [
  FF('Rows for this listing', cnt('directory', 'listing', 'directory.dl_id'), 'int')]),
 FORM('newsletter_sheet', 'Newsletter Plan Sheet', 'Newsletter issue with replies and enquiries', 'newsletter.issue_id', F(
  ('Date', 'newsletter.date'), ('Topic', 'newsletter.topic'), ('Sent to', 'newsletter.sent_to'), ('Replies', 'newsletter.replies'), ('Enquiries', 'newsletter.enquiries'), ('Reply rate', 'newsletter.reply_rate'),
  ('Enquiries per 1,000 sent', 'newsletter.enq_per_1000')) + [FF('Average reply rate, all issues', 'SUM({range:newsletter.replies})/SUM({range:newsletter.sent_to})', 'pct')]),
 FORM('survey_sheet', 'Feedback Survey Sheet', 'Feedback survey answer', 'feedback.survey_id', F(
  ('Date', 'feedback.date'), ('Client type', 'feedback.client_type'), ('Service', 'feedback.service'), ('Feedback score (1-10)', 'feedback.rating'), ('Would recommend', 'feedback.would_recommend'), ('Topic', 'feedback.topic'),
  ('Score band', 'feedback.rating_band'), ('Topic average score, last 12 months', 'feedback.topic_avg_12m')) + [FF('Answers on the same topic', cnt('feedback', 'topic', 'feedback.survey_id'), 'int')]),
 FORM('group_plan_sheet', 'Group Plan Sheet', 'Group plan with break-even sign-ups', 'groups.group_id', F(
  ('Program', 'groups.program'), ('Facilitator', 'groups.facilitator'), ('Room', 'groups.room'), ('Start date', 'groups.start_date'), ('Weekday', 'groups.weekday'), ('Start time', 'groups.start_time'), ('Weeks', 'groups.weeks'),
  ('Capacity (places)', 'groups.capacity'), ('Fee per person', 'groups.fee'), ('Materials, marketing and room', 'groups.fixed_costs'), ('Facilitator pay share of fees', 'groups.pay_share'), ('Break-even sign-ups', 'groups.breakeven_signups'),
  ('Facilitator phone', 'groups.facilitator_phone'), ('Status', 'groups.status'))),
 FORM('signup_sheet', 'Group Sign-up Sheet', 'Group sign-up with payment and attendance', 'signups.signup_id', F(
  ('Group', 'signups.group_id'), ('Program', 'signups.program'), ('Name', 'signups.name'), ('Phone', 'signups.phone'), ('Signed up on', 'signups.signed_on'), ('Paid', 'signups.paid_amount'), ('Paid on', 'signups.paid_on'),
  ('Status', 'signups.status'), ('Group start', 'signups.start_date'), ('Start time', 'signups.start_time'), ('Room', 'signups.room'), ('Group fee', 'signups.fee'), ('Weeks in the program', 'signups.weeks'),
  ('Meetings attended', 'signups.sessions_attended'), ('Meetings held so far', 'signups.meetings_held'), ('Attendance, % of meetings held', 'signups.attendance_share'))),
 FORM('attendance_sheet', 'Group Attendance Sheet', 'Group meeting attendance', 'attendance.row_id', F(
  ('Group', 'attendance.group_id'), ('Program', 'attendance.program'), ('Meeting number', 'attendance.meeting_no'), ('Date', 'attendance.date'), ('Attended', 'attendance.attended'), ('People signed up', 'attendance.expected'),
  ('Attendance', 'attendance.attendance_share'), ('Attendance check', 'attendance.attendance_check')) + [
  FF('Meetings recorded for this group', cnt('attendance', 'group_id', 'attendance.row_id'), 'int')]),
 FORM('group_review_sheet', 'Group Review Sheet', 'Group review: fill, attendance and profit', 'groups.group_id', F(
  ('Program', 'groups.program'), ('Status', 'groups.status'), ('Capacity (places)', 'groups.capacity'), ('Sign-ups', 'groups.signups'), ('Fill rate', 'groups.fill_rate'), ('Fill check', 'groups.fill_check'), ('Revenue', 'groups.revenue'),
  ('Facilitator pay', 'groups.facilitator_pay'), ('Facilitator pay share of fees', 'groups.pay_share'), ('Materials, marketing and room', 'groups.fixed_costs'), ('Attendance at meetings', 'groups.attendance_rate'), ('Profit', 'groups.profit'),
  ('Profit per person', 'groups.profit_per_person'), ('Profit per facilitator hour', 'groups.profit_per_hour'), ('Break-even sign-ups', 'groups.breakeven_signups'), ('Break-even check', 'groups.break_check'))),
 FORM('idea_sheet', 'New Group Idea Sheet', 'New group idea with expected revenue', 'ideas.idea_id', F(
  ('Idea', 'ideas.idea'), ('Client type', 'ideas.client_type'), ('People interested', 'ideas.people_interested'), ('Facilitator', 'ideas.facilitator'), ('Capacity (places)', 'ideas.capacity'), ('Expected sign-ups', 'ideas.expected_signups'),
  ('Fee per person', 'ideas.fee'), ('Expected revenue', 'ideas.expected_revenue'), ('Expected fill', 'ideas.expected_fill'), ('Fill check', 'ideas.idea_check')) + [
  FF('Sign-ups per 100 interested', 'INDEX({range:ideas.expected_signups},MATCH({pick},{range:ideas.idea_id},0))*100/INDEX({range:ideas.people_interested},MATCH({pick},{range:ideas.idea_id},0))', 'num')]),
]
assert len(forms) == 12
# the referrer profile count line uses the id of the picked referrer
forms[1]['fields'][-1] = FF('Contacts logged for this referrer', 'COUNTIFS({range:contacts.referrer},INDEX({range:referrers.name},MATCH({pick},{range:referrers.referrer_id},0)))', 'int')

def D_(key_, sheet, title, pick, paras, sign): return DOC(key_, sheet, title, pick, paras, sign, NOTE)
documents = [
 D_('referrer_pack_doc', 'Referrer Pack Letter', 'Referrer information pack letter', 'referrers.referrer_id', [
  'Referrer information pack of {set:company}, dated {today}. Dear {col:referrers.name},',
  'Thank you for the work you do. {set:company} is a small group practice of talking therapists and counsellors. We offer individual, couples, family and child sessions, speech and behaviour therapy and group programs, in person and by video session.',
  'How to refer: send us the contact details of the person, or ask them to contact us. We contact the person ourselves and offer a first assessment session (the intake). Current waiting times are on the enclosed sheet.',
  'Our next group is {col:referrers.program}, starting on {col:referrers.start_date}. You referred {col:referrers.referrals_12m} people in the last 12 months.',
  'For privacy we do not share anything about a person with you unless they agree; check your own local rules.'], ['Practice team']),
 D_('referrer_thanks_doc', 'Referrer Thank-you Letter', 'Referrer thank-you letter without client details', 'referrers.referrer_id', [
  'Thank-you letter of {set:company}, dated {today}. Dear {col:referrers.name},',
  'In the last 12 months you referred {col:referrers.referrals_12m} people to us. Thank you for trusting us.',
  'We last contacted you on {col:referrers.last_contact}. We would be glad to visit your team or to send our new information pack.',
  'We do not share information about the people you refer unless they agree; check your own local rules.'], ['Owner']),
 D_('flyer_doc', 'Workshop Flyer Text', 'Workshop or talk flyer text', 'workshops.workshop_id', [
  '{col:workshops.title}',
  '{col:workshops.kind} for: {col:workshops.audience}. Date: {col:workshops.date}. Hosted with {col:workshops.contact}.',
  'Come and meet the team of {set:company}, hear how our sessions and group programs work and ask your questions. Places are limited, so please book early with the front desk.',
  'This event gives general information only; it is not advice about any person\'s situation.'], ['Front desk']),
 D_('talk_outline_doc', 'Community Talk Outline', 'Community talk outline with generic topics', 'workshops.workshop_id', [
  'Talk outline of {set:company}, dated {today}. Event: {col:workshops.title}, {col:workshops.date}. Audience: {col:workshops.audience}. Expected attendees: {col:workshops.attendees}.',
  '1. Welcome and who we are (5 minutes). 2. How a first assessment session (the intake) works and how to book (10 minutes). 3. Fees, including a lower fee agreed from a client\'s means (a sliding scale), and how to cancel (5 minutes).',
  '4. What a group program looks like: weekly meetings with a facilitator (10 minutes). 5. Questions (15 minutes). 6. How to contact us (2 minutes).',
  'The talk gives practical information only: it does not diagnose, give advice about any person or promise results.'], ['Speaker']),
 D_('group_info_doc', 'Group Information Sheet', 'Group program information sheet', 'groups.group_id', [
  'Group program information of {set:company}, dated {today}. Program: {col:groups.program}.',
  'The group meets every {col:groups.weekday} at {col:groups.start_time} in {col:groups.room}, starting on {col:groups.start_date}, for {col:groups.weeks} weekly meetings. Places: {col:groups.capacity}. Fee: {col:groups.fee} per person.',
  'Facilitator: {col:groups.facilitator}. The group runs when enough people have signed up; if we postpone or cancel it we will tell you and refund your fee.',
  'To sign up, contact the front desk. Group reference: {col:groups.group_id}.'], ['Front desk']),
 D_('signup_confirm_doc', 'Group Sign-up Confirmation', 'Group sign-up confirmation', 'signups.signup_id', [
  'Sign-up confirmation of {set:company}, dated {today}. Dear {col:signups.name},',
  'Your place in the {col:signups.program} group is confirmed. The first meeting is on {col:signups.start_date} at {col:signups.start_time} in {col:signups.room}. The program has {col:signups.weeks} weekly meetings.',
  'Fee: {col:signups.fee}. You paid {col:signups.paid_amount} on {col:signups.paid_on}. If we cancel the group your fee is refunded.',
  'Please tell us if you cannot come to a meeting. Reference {col:signups.signup_id}.'], ['Front desk']),
 D_('certificate_doc', 'Attendance Certificate', 'Group attendance certificate', 'signups.signup_id', [
  'Attendance certificate of {set:company}, dated {today}.',
  '{col:signups.name} attended {col:signups.sessions_attended} of {col:signups.weeks} weekly meetings of the {col:signups.program} group that started on {col:signups.start_date}.',
  'This certificate records attendance only. Reference {col:signups.signup_id}.'], ['Facilitator', 'Practice owner']),
 D_('group_report_doc', 'Group Program Report', 'Group program report: fill, attendance and profit', 'groups.group_id', [
  'Group program report of {set:company}, dated {today}. Group {col:groups.group_id}: {col:groups.program}, starting {col:groups.start_date}. Status: {col:groups.status}.',
  'Fill: {col:groups.signups} sign-ups for {col:groups.capacity} places, a fill rate of {col:groups.fill_rate}. Fill check: {col:groups.fill_check}. Attendance at meetings: {col:groups.attendance_rate}.',
  'Revenue {col:groups.revenue}; facilitator pay {col:groups.facilitator_pay} ({col:groups.pay_share} of fees); materials, marketing and room {col:groups.fixed_costs}. Profit {col:groups.profit}, which is {col:groups.profit_per_person} per person and {col:groups.profit_per_hour} per facilitator hour.',
  'Break-even was {col:groups.breakeven_signups} sign-ups: {col:groups.break_check}. Decisions for the next run are written below.'], ['Owner', 'Facilitator']),
 D_('marketing_plan_doc', 'Marketing Plan', 'Marketing plan for the next 12 months', 'budget.row_id', [
  'Marketing plan of {set:company}, dated {today}. Plan starting in the month of {col:budget.month}.',
  'Budget this month: {col:budget.budget}; spent: {col:budget.spent}; left: {col:budget.left}. At this pace the budget for 12 months is {col:budget.yearly_pace}.',
  'Priorities: 1. contact every referrer at least every {set:contact_days} days; 2. keep, renegotiate or drop each directory listing after the payback check; 3. run the workshops and talks that win clients at a cost under {set:max_cost_client} per client; 4. plan groups from the interest list.',
  'Targets: booked share of enquiries {set:target_conv}; group fill rate {set:min_group_fill}; feedback score {set:target_rating}. Actions and owners are written below.'], ['Owner', 'Coordinator']),
 D_('monthly_report_doc', 'Monthly Marketing Report', 'Monthly marketing report', 'website.row_id', [
  'Monthly marketing report of {set:company}, dated {today}. Month: {col:website.month}.',
  'All enquiries: {col:website.all_enquiries}. Booked clients: {col:website.all_booked}. Marketing spent: {col:website.marketing_spent}. Cost per enquiry: {col:website.cost_per_enquiry}. Cost per booked client: {col:website.cost_per_client}.',
  'Website: {col:website.visits} visits, {col:website.enquiry_forms} enquiry forms ({col:website.form_share} of visits) and {col:website.bookings} bookings ({col:website.booking_share} of forms).',
  'Comments and decisions are written below.'], ['Owner']),
 D_('source_report_doc', 'Referral Source Report', 'Referral source report with value first', 'sourcemonths.row_id', [
  'Referral source report of {set:company}, dated {today}. Source: {col:sourcemonths.source}.',
  'Value first. Revenue per enquiry over the last 12 months: {col:sourcemonths.val_enq_12m}. Revenue per booked client over the last 12 months: {col:sourcemonths.val_client_12m}.',
  'Month {col:sourcemonths.month}: {col:sourcemonths.enquiries} enquiries, {col:sourcemonths.booked} booked clients ({col:sourcemonths.booked_share} booked share) and revenue {col:sourcemonths.revenue}.',
  'Decision: invest, hold or cut this source; write it below.'], ['Owner']),
 D_('listing_text_doc', 'Directory Listing Text', 'Directory listing text: practice description', 'directory.dl_id', [
  'Listing text for {col:directory.listing}, prepared {today}.',
  '{set:company} is a small group practice of talking therapists and counsellors. We offer individual, couples, family and child sessions, speech and behaviour therapy and group programs, in person and by video session.',
  'We start with a first assessment session (the intake). A lower fee agreed from your means (a sliding scale) may be available, and some third-party payers (organisations that pay part of a client\'s fee) are accepted; ask us how it works.',
  'This is not an emergency service: in an emergency contact your local emergency number.'], ['Practice team']),
]
assert len(documents) == 12

def CS(key_, title, table, start, steps): return _lib.CHK(key_, title, table, start, steps)
checklists = [
 CS('c_new_referrer', 'New Referrer Steps', 'contacts', 'contacts.date', [('Record the referrer, kind and phone on the Referrers sheet', 0), ('Send the information pack', 1), ('Log the contact on Referrer Contacts', 1), ('Set the next contact date', 2), ('Send a thank-you after the first referral', 14)]),
 CS('c_visit', 'Referrer Visit Steps', 'contacts', 'contacts.date', [('Agree a day and time with the referrer', -14), ('Prepare the information pack and the current waiting times', -3), ('Visit and listen to what the team needs', 0), ('Log the visit and set the next contact date', 1), ('Send a thank-you note', 2)]),
 CS('c_thank_round', 'Monthly Thank-you Round Steps', 'budget', 'budget.month', [('List the referrers with referrals last month', 1), ('Write thank-you notes without client details', 3), ('Send the notes', 5), ('Log each contact on Referrer Contacts', 6), ('Check the referrers past their contact rhythm', 8)]),
 CS('c_workshop', 'Workshop or Talk Steps', 'workshops', 'workshops.date', [('Agree the date, host and room', -28), ('Print the flyer text and post it', -21), ('Book the room and equipment', -14), ('Send reminders to the people who signed up', -2), ('Run the event and count the attendees', 0), ('Record enquiries from the event', 7), ('Thank the host', 2)]),
 CS('c_school_talk', 'School Talk Steps', 'workshops', 'workshops.date', [('Agree the topic and audience with school staff', -30), ('Prepare the talk outline with generic topics only', -14), ('Send the flyer to the school', -10), ('Give the talk and leave the information sheet', 0), ('Record attendees and enquiries', 1), ('Send a thank-you to the school contact', 3)]),
 CS('c_listing_review', 'Directory Listing Review Steps', 'directory', 'directory.month', [('Check profile views, enquiries and clients won', 1), ('Work out the months to pay back one listing', 1), ('Compare with your target months', 2), ('Decide: keep, renegotiate or drop', 3), ('Update the listing text if you keep it', 5)]),
 CS('c_website', 'Website Update Steps', 'website', 'website.month', [('Check visits, enquiry forms and bookings', 1), ('Check that the enquiry form works', 1), ('Update fees, hours and group dates', 3), ('Check the page on a phone', 4), ('Record what changed', 5)]),
 CS('c_newsletter', 'Newsletter Issue Steps', 'newsletter', 'newsletter.date', [('Choose the topic and the call to action', -7), ('Write the issue and check the dates', -4), ('Check the list is up to date', -2), ('Send the issue', 0), ('Count replies and enquiries after 7 days', 7)]),
 CS('c_new_group', 'Planning a New Group Steps', 'groups', 'groups.start_date', [('Check the interest list for the program', -70), ('Agree the facilitator, room, weekday and time', -63), ('Work out the fee and the break-even sign-ups', -56), ('Open sign-up and post the group', -49), ('Contact everyone on the interest list', -42), ('Decide to run or postpone', -14)]),
 CS('c_group_start', 'Group Start Week Steps', 'groups', 'groups.start_date', [('Confirm every place and payment', -7), ('Send the first meeting reminder', -2), ('Prepare the room and materials', -1), ('Record attendance at the first meeting', 0), ('Follow up anyone who did not come', 1)]),
 CS('c_group_end', 'Group End and Review Steps', 'groups', 'groups.start_date', [('Record attendance for every meeting', 49), ('Send the feedback survey', 50), ('Send attendance certificates', 52), ('Work out fill rate, profit and profit per facilitator hour', 56), ('Decide on the next run and contact the interest list', 60)]),
 CS('c_survey_round', 'Feedback Survey Round Steps', 'feedback', 'feedback.date', [('Choose the clients to ask', 0), ('Send the short survey', 1), ('Remind after 3 days', 4), ('Enter the answers', 7), ('Review the weakest topic with the team', 10)]),
]
assert len(checklists) == 12

def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
 M('r_thanks', 'Referrer: thank you for referrals', 'referrers', 'referrers.phone', 'Hello {name}, thank you for trusting {company} with {referrals_12m} referrals in the last 12 months. We appreciate it.'),
 M('r_services', 'Referrer: services and waiting times', 'referrers', 'referrers.phone', 'Hello {name}, {company} offers individual, couples, family and child sessions, speech and behaviour therapy and group programs. Reply and we will send our services list and current waiting times.'),
 M('r_group', 'Referrer: a new group starts', 'referrers', 'referrers.phone', 'Hello {name}, a new {program} group starts on {start_date} at {company}. Reply and we will send the information sheet for your team.'),
 M('r_visit', 'Referrer: may we visit your team', 'referrers', 'referrers.phone', 'Hello {name}, may we visit your team around {next_contact} to say thank you and share our services? Please tell us a day that suits you. {company}'),
 M('r_speech', 'Referrer: speech and behaviour hours', 'referrers', 'referrers.phone', 'Hello {name}, our speech and behaviour therapy hours are open for new referrals. Reply and we will send the hours and waiting times. {company}'),
 M('r_pack', 'Referrer: our new information pack', 'referrers', 'referrers.phone', 'Hello {name}, our new information pack for referrers is ready. Reply and we will send it by email or post. {company}'),
 M('g_confirm', 'Group member: your place is confirmed', 'signups', 'signups.phone', 'Hello {name}, your place in the {program} group is confirmed. It starts on {start_date}. {company}'),
 M('g_first', 'Group member: the first meeting', 'signups', 'signups.phone', 'Hello {name}, the first meeting of {program} is on {start_date} at {start_time} in {room}. Please arrive 5 minutes early. {company}'),
 M('g_tonight', 'Group member: the group meets tonight', 'signups', 'signups.phone', 'Hello {name}, a reminder: the {program} group meets tonight at {start_time} in {room}. {company}'),
 M('g_pay', 'Group member: please pay the group fee', 'signups', 'signups.phone', 'Hello {name}, please pay the group fee of {fee} for {program} before {start_date}. {company}'),
 M('g_missed', 'Group member: we missed you', 'signups', 'signups.phone', 'Hello {name}, we missed you at the {program} meeting; you have attended {sessions_attended} so far. Please tell us if you can come next week. {company}'),
 M('g_full', 'Group member: the group is full', 'interest', 'interest.phone', 'Hello {name}, the {program} group is full for now. You are on our interest list and we will contact you when a place opens or a new group is planned. {company}'),
 M('g_new', 'Group member: a new group is open', 'interest', 'interest.phone', 'Hello {name}, a new {program} group is open for sign-up and starts on {next_start}. Reply to take a place. {company}'),
 M('g_cancel', 'Group member: the group is cancelled', 'signups', 'signups.phone', 'Hello {name}, we are sorry: the {program} group is cancelled and your fee of {paid_amount} will be refunded. {company}'),
 M('g_thanks', 'Group member: thank you for completing', 'signups', 'signups.phone', 'Hello {name}, thank you for completing the {program} group; you attended {sessions_attended} of {weeks} meetings. {company}'),
 M('g_feedback', 'Group member: please share your feedback', 'signups', 'signups.phone', 'Hello {name}, please share your feedback on the {program} group in a short survey. {company}'),
 M('i_soon', 'Interest list: a group starts soon', 'interest', 'interest.phone', 'Hello {name}, a {program} group starts on {next_start}. You asked to hear about it. Reply to book a place. {company}'),
 M('f_signups', 'Facilitator: sign-ups for your group', 'groups', 'groups.facilitator_phone', 'Hello {facilitator}, sign-ups for {group_id} ({program}) are {signups} of {capacity} places. {company}'),
 M('f_breakeven', 'Facilitator: break-even sign-ups', 'groups', 'groups.facilitator_phone', 'Hello {facilitator}, break-even for {group_id} is {breakeven_signups} sign-ups and you have {signups}. {company}'),
 M('f_attendance', 'Facilitator: please record attendance', 'groups', 'groups.facilitator_phone', 'Hello {facilitator}, please record attendance for {group_id} ({program}) after the meeting. {company}'),
 M('c_post', 'Coordinator: post the new group', 'groups', 'groups.coordinator_phone', 'Hello, please post the new {program} group ({group_id}) starting on {start_date} in the online directories and on the website.'),
 M('c_room', 'Coordinator: book the workshop room', 'workshops', 'workshops.coordinator_phone', 'Hello, please book the room for the {kind} "{title}" on {date}: {attendees} people are expected.'),
 M('c_thank', 'Coordinator: referrers to thank', 'referrers', 'referrers.coordinator_phone', 'Hello, please thank {name} this month: {referrals_12m} referrals in the last 12 months, last contact on {last_contact}.'),
 M('o_value', 'Owner: source with most value', 'sourcemonths', 'sourcemonths.owner_phone', 'Hello, {source} brings {val_enq_12m} of revenue per enquiry over the last 12 months. Check whether to invest more.'),
 M('o_cost', 'Owner: cost per client by channel', 'campaigns', 'campaigns.owner_phone', 'Hello, the cost per client won for {kind} on {date} was {cost_per_client}. Check it against the most you accept to pay.'),
 M('o_stopped', 'Owner: a source stopped sending', 'sourcemonths', 'sourcemonths.owner_phone', 'Hello, {source} sent {enquiries} enquiries in {month}. Check whether this source has stopped sending enquiries.'),
 M('o_fill', 'Owner: the fill rate of a group is low', 'groups', 'groups.owner_phone', 'Hello, the fill rate of {group_id} ({program}) is {fill_rate}: {signups} sign-ups for {capacity} places.'),
 M('o_profit', 'Owner: the group made a profit', 'groups', 'groups.owner_phone', 'Hello, the group {group_id} ({program}) made a profit of {profit}.'),
 M('o_report', 'Owner: marketing report is ready', 'budget', 'budget.owner_phone', 'Hello, the monthly marketing report is ready: {spent} spent of a {budget} budget, {left} left.'),
 M('o_listing', 'Owner: keep or drop a listing', 'directory', 'directory.owner_phone', 'Hello, keep, renegotiate or drop the {listing} directory listing? It pays back in {payback_months} months at its current results.'),
 M('cl_survey', 'Client: a short feedback survey', 'clientvalue', 'clientvalue.phone', 'Hello {client}, would you share a short feedback survey about your experience with {company}? It takes two minutes. Thank you.'),
 M('w_thanks', 'Workshop contact: thank you for coming', 'workshops', 'workshops.contact_phone', 'Hello {contact}, thank you for coming to our {title} on {date}. {company}'),
 M('w_next', 'Workshop contact: our next talk', 'workshops', 'workshops.contact_phone', 'Hello {contact}, we will send you the date of our next talk. Reply if you would like to bring colleagues. {company}'),
 M('n_next', 'Newsletter reader: our next workshop', 'interest', 'interest.phone', 'Hello {name}, our next workshop will be announced in our newsletter. Reply and we will add you to the list. {company}'),
]
assert len(messages) == 34, len(messages)

need = {m['table'] for m in messages}
for t in tables:
    if t['key'] in need and not any(c['key'] == 'company' for c in t['columns']): t['columns'].append(CA('company', 'Practice', 'text', '{set:company}&""', 24))

MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YS = 'DATE(YEAR({today}),1,1)'
S12 = 'DATE(YEAR({today}),MONTH({today})-11,1)'
def L12(tb, col='date'): return '{range:%s.%s},">="&({today}-365),{range:%s.%s},"<="&{today}' % (tb, col, tb, col)
def D90(tb): return '{range:%s.date},">="&({today}-90),{range:%s.date},"<="&{today}' % (tb, tb)
def SMS(col, extra=''): return 'SUMIFS({range:sourcemonths.%s},{range:sourcemonths.month},">="&%s%s)' % (col, S12, extra)
THIS_YEAR_GRP = '{range:groups.counted},1,{range:groups.start_date},">="&%s' % YS
kpis = [
 KPI('Enquiries from referrals this month', 'SUMIFS({range:sourcemonths.enquiries},{range:sourcemonths.month},%s,{range:sourcemonths.referral_based},1)' % MS, 'int'),
 KPI('Referral share of enquiries, 12 months', '%s/%s' % (SMS('enquiries', ',{range:sourcemonths.referral_based},1'), SMS('enquiries')), 'pct'),
 KPI('Active referrers, last 12 months', 'COUNTIFS({range:referrers.referrals_12m},">0")', 'int'),
 KPI('Referrers not contacted for 90 days', 'COUNTIFS({range:referrers.days_since},">"&{set:contact_days})', 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Best source value per client, 12 months', 'MAX({range:sourcemonths.val_client_12m})', 'money'),
 KPI('Directory enquiries this month', 'SUMIFS({range:directory.enquiries},{range:directory.month},%s)' % MS, 'int'),
 KPI('Website enquiry forms this month', 'SUMIFS({range:website.enquiry_forms},{range:website.month},%s)' % MS, 'int'),
 KPI('Workshop and talk enquiries this year', 'SUMIFS({range:workshops.enquiries},{range:workshops.date},">="&%s,{range:workshops.date},"<="&{today})' % YS, 'int'),
 KPI('Marketing spend this month', 'SUMIFS({range:budget.spent},{range:budget.month},%s)' % MS, 'money'),
 KPI('Marketing spend this year', 'SUMIFS({range:budget.spent},{range:budget.month},">="&%s,{range:budget.month},"<="&%s)' % (YS, MS), 'money'),
 KPI('Cost per enquiry, last 12 months', 'SUMIFS({range:campaigns.cost},%s)/SUMIFS({range:campaigns.enquiries},%s)' % (L12('campaigns'), L12('campaigns')), 'money'),
 KPI('Cost per client won, last 12 months', 'SUMIFS({range:campaigns.cost},%s)/SUMIFS({range:campaigns.clients_won},%s)' % (L12('campaigns'), L12('campaigns')), 'money', alert={"when": "> {set:max_cost_client}", "style": "bad"}),
 KPI('Clients won by workshops, this year', '+'.join('SUMIFS({range:campaigns.clients_won},{range:campaigns.kind},%s,{range:campaigns.date},">="&%s)' % (tok('mkind', k), YS) for k in ('Workshop', 'Community talk', 'School talk')), 'int'),
 KPI('Directory booked share, 12 months', '%s/%s' % (SMS('booked', ',{range:sourcemonths.source},%s' % tok('src', 'Online directory')), SMS('enquiries', ',{range:sourcemonths.source},%s' % tok('src', 'Online directory'))), 'pct'),
 KPI('Waiting for the next group', 'IFERROR(COUNTIFS({range:interest.program},INDEX({range:groups.program},MATCH(1,{range:groups.next_flag},0)),{range:interest.signed_up},%s),0)' % NO, 'int'),
 KPI('Average client value', 'AVERAGE({range:clientvalue.revenue})', 'money'),
 KPI('Best source value per enquiry, 12 mo', 'MAX({range:sourcemonths.val_enq_12m})', 'money'),
 KPI('Months to pay back one directory listing', '12*SUMIFS({range:directory.cost},{range:directory.month},">="&%s)/(SUMIFS({range:directory.clients_won},{range:directory.month},">="&%s)*{set:avg_charge}*{set:client_sessions_month}*{set:margin_pct})' % (S12, S12), 'num', alert={"when": "> {set:max_payback_months}", "style": "warn"}),
 KPI('Workshop attendees this year', 'SUMIFS({range:workshops.attendees},{range:workshops.date},">="&%s,{range:workshops.date},"<="&{today})' % YS, 'int'),
 KPI('Groups running now', 'COUNTIFS({range:groups.status},%s)' % tok('grpst', 'Running'), 'int'),
 KPI('Sign-ups for the next group', 'SUMIFS({range:groups.signups},{range:groups.next_flag},1)', 'int'),
 KPI('Group fill rate this year', 'SUMIFS({range:groups.signups},%s)/SUMIFS({range:groups.capacity},%s)' % (THIS_YEAR_GRP, THIS_YEAR_GRP), 'pct', alert={"when": "< {set:min_group_fill}", "style": "warn"}),
 KPI('Group revenue this year', 'SUMIFS({range:groups.revenue},%s)' % THIS_YEAR_GRP, 'money'),
 KPI('Group profit this year', 'SUMIFS({range:groups.profit},%s)' % THIS_YEAR_GRP, 'money'),
 KPI('Group drop-out rate', 'COUNTIFS({range:signups.status},%s)/COUNTA({range:signups.signup_id})' % tok('signst', 'Dropped out'), 'pct'),
 KPI('Facilitator pay share of fees, this year', 'SUMIFS({range:groups.facilitator_pay},%s)/SUMIFS({range:groups.revenue},%s)' % (THIS_YEAR_GRP, THIS_YEAR_GRP), 'pct'),
 KPI('People on the group interest list', 'COUNTIFS({range:interest.signed_up},%s)' % NO, 'int'),
 KPI('Break-even sign-ups for the next group', 'SUMIFS({range:groups.breakeven_signups},{range:groups.next_flag},1)', 'int'),
 KPI('Average feedback score, last 90 days', 'IFERROR(AVERAGEIFS({range:feedback.rating},%s),0)' % D90('feedback'), 'num', alert={"when": "< {set:target_rating}", "style": "warn"}),
 KPI('Would recommend share, last 90 days', 'IFERROR(COUNTIFS({range:feedback.would_recommend},%s,%s)/COUNTIFS(%s),0)' % (YES, D90('feedback'), D90('feedback')), 'pct', alert={"when": "< {set:target_recommend}", "style": "warn"}),
]
assert len(kpis) == 30
dashboard = {"title": "Marketing KPI Dashboard", "kpis": kpis,
 "monthly": {"title": "Enquiries and booked clients by month", "date": "sourcemonths.month", "series": [
   {"label": "Enquiries", "sum": "sourcemonths.enquiries", "date": "sourcemonths.month"}, {"label": "Booked clients", "sum": "sourcemonths.booked", "date": "sourcemonths.month"},
   {"label": "Directory enquiries", "sum": "directory.enquiries", "date": "directory.month"}, {"label": "Website forms", "sum": "website.enquiry_forms", "date": "website.month"}]},
 "breakdowns": [{"title": "Enquiries by referral source", "by": "enquiries.source", "agg": "count"}, {"title": "Referrals by referrer kind", "by": "referrallog.kind", "agg": "count"},
                {"title": "Campaigns by kind", "by": "campaigns.kind", "agg": "count"}, {"title": "Groups by status", "by": "groups.status", "agg": "count"}]}

def SRCSER(name): return AGG('sum', 'sourcemonths', 'sourcemonths.enquiries', date='sourcemonths.month', where=[('source', '=', tok('src', name))], label=name)
insights = {"filters": [{"label": "Referral source", "list": "src"}, {"label": "Program", "list": "prog"}, {"label": "Referrer kind", "list": "rkind"}],
 "gauges": [
  {"title": "Referral share of enquiries", "num": AGG('sum', 'sourcemonths', 'sourcemonths.enquiries', where=[('referral_based', '=', 1)]), "den": AGG('sum', 'sourcemonths', 'sourcemonths.enquiries')},
  {"title": "Directory enquiries that became clients", "num": AGG('sum', 'directory', 'directory.clients_won'), "den": AGG('sum', 'directory', 'directory.enquiries')},
  {"title": "Group fill rate", "num": AGG('sum', 'groups', 'groups.signups', where=[('counted', '=', 1)]), "den": AGG('sum', 'groups', 'groups.capacity', where=[('counted', '=', 1)])},
  {"title": "Group attendance", "num": AGG('sum', 'attendance', 'attendance.attended'), "den": AGG('sum', 'attendance', 'attendance.expected')},
  {"title": "Months with spend within budget", "num": AGG('count', 'budget', where=[('budget_check', '=', ck('Within budget'))]), "den": AGG('count', 'budget')},
  {"title": "Would recommend", "num": AGG('count', 'feedback', where=[('would_recommend', '=', YES)]), "den": AGG('count', 'feedback')}],
 "charts": [
  CHART('Enquiries by referral source', 'bar', 'sourcemonths.source', [AGG('sum', 'sourcemonths', 'sourcemonths.enquiries', label='Enquiries')]),
  CHART('Booked clients by referral source', 'bar', 'sourcemonths.source', [AGG('sum', 'sourcemonths', 'sourcemonths.booked', label='Booked clients')]),
  CHART('Referral enquiries per month, by source', 'stacked', 'month', [SRCSER('Doctor referral'), SRCSER('School referral'), SRCSER('Other clinician'), SRCSER('Employer program')]),
  CHART('Referrals by referrer kind', 'bar', 'referrallog.kind', [AGG('count', 'referrallog', label='Referrals')]),
  CHART('Marketing spent and budget per month', 'column', 'month', [AGG('sum', 'budget', 'budget.spent', date='budget.month', label='Spent'), AGG('sum', 'budget', 'budget.budget', date='budget.month', label='Budget')]),
  CHART('Spend by activity kind', 'bar', 'campaigns.kind', [AGG('sum', 'campaigns', 'campaigns.cost', label='Cost')]),
  CHART('Enquiries by activity kind', 'bar', 'campaigns.kind', [AGG('sum', 'campaigns', 'campaigns.enquiries', label='Enquiries')]),
  CHART('Clients won by activity kind', 'bar', 'campaigns.kind', [AGG('sum', 'campaigns', 'campaigns.clients_won', label='Clients won')]),
  CHART('Directory enquiries per month', 'column', 'month', [AGG('sum', 'directory', 'directory.enquiries', date='directory.month', label='Enquiries'), AGG('sum', 'directory', 'directory.clients_won', date='directory.month', label='Clients won')]),
  CHART('Website enquiry forms per month', 'column', 'month', [AGG('sum', 'website', 'website.enquiry_forms', date='website.month', label='Enquiry forms'), AGG('sum', 'website', 'website.bookings', date='website.month', label='Bookings')]),
  CHART('Months to pay back one listing, by directory listing', 'bar', 'directory.listing', [AGG('avg', 'directory', 'directory.payback_months', label='Months to pay back')]),
  CHART('Referrer contacts per month', 'column', 'month', [AGG('count', 'contacts', date='contacts.date', label='Contacts')]),
  CHART('Value per enquiry by source, last 12 months', 'bar', 'sourcemonths.source', [AGG('avg', 'sourcemonths', 'sourcemonths.val_enq_12m', label='Revenue per enquiry')]),
  CHART('Group sign-ups by program', 'bar', 'groups.program', [AGG('sum', 'groups', 'groups.signups', label='Sign-ups')]),
  CHART('Group revenue by program', 'bar', 'groups.program', [AGG('sum', 'groups', 'groups.revenue', label='Revenue')]),
  CHART('Group profit by program', 'bar', 'groups.program', [AGG('sum', 'groups', 'groups.profit', label='Profit')]),
  CHART('Groups by status', 'bar', 'groups.status', [AGG('count', 'groups', label='Groups')]),
  CHART('Facilitator pay share of fees by program', 'bar', 'groups.program', [AGG('avg', 'groups', 'groups.pay_share', label='Pay share of fees')]),
  CHART('Group attendance per month', 'column', 'month', [AGG('sum', 'attendance', 'attendance.attended', date='attendance.date', label='People attending')]),
  CHART('Feedback score per month', 'column', 'month', [AGG('avg', 'feedback', 'feedback.rating', date='feedback.date', label='Average score')]),
  CHART('Feedback score by topic', 'bar', 'feedback.topic', [AGG('avg', 'feedback', 'feedback.rating', label='Average score')]),
  CHART('Revenue per client by source, all clients', 'bar', 'clientvalue.source', [AGG('avg', 'clientvalue', 'clientvalue.revenue', label='Revenue per client')])]}
assert len(insights['charts']) == 22

signature = [
 {"name": "Enquiries and booked clients by referral source", "why": "every month shows enquiries, booked clients and revenue per source, so you see which source fills the practice", "where": "Source Performance by Month"},
 {"name": "Referral source value ranking", "why": "value per enquiry and per client for each source over 12 months, ranked, with an invest, hold or cut verdict", "where": "Referral Source Value"},
 {"name": "Referrer log with the contact rhythm", "why": "12-month referrals, value and days since the last contact rank which referrer to contact first, without any client details", "where": "Referrers"},
 {"name": "Cost per enquiry and per client won by channel", "why": "every campaign shows what one enquiry and one client cost against the most you accept to pay", "where": "Campaigns"},
 {"name": "Client value by source", "why": "sessions and revenue per client with a value band show which source brings the clients that stay", "where": "Client Value by Source"},
 {"name": "Directory listing keep-or-drop check", "why": "months to pay back a year's fee, the highest fee that still pays back and a keep, renegotiate or drop verdict", "where": "Directory Listing Check"},
 {"name": "Workshop and talk planner", "why": "cost, expected clients and the fee that covers the cost decide whether to run an event", "where": "Workshop Planner"},
 {"name": "Group program pricing and break-even", "why": "profit per person and per facilitator hour, the fee that meets your profit target and the break-even sign-ups", "where": "Group Program Pricing"},
 {"name": "Group fill and attendance tracker", "why": "fill rate, drop-outs and attendance against your minimum, with a run or postpone verdict", "where": "Group Fill and Attendance"},
 {"name": "New group business case", "why": "people interested, sign-up share and costs give profit per run and per year in a base, best or worst case", "where": "New Group Business Case"},
 {"name": "Group interest list with the next start date", "why": "each person sees the next group of their program and its start, and the planner gives the meeting dates", "where": "Group Interest List"},
 {"name": "Source forecast from your own history", "why": "the last 6 months of a source, a trend and a scenario give 3 months of enquiries and a capacity verdict", "where": "Source Forecast"}]
competitors = [
 {"what": "free appointment templates", "lacks": "list bookings only, with no referral sources, referrer contact rhythm, campaign costs or group programs"},
 {"what": "subscription practice-management software", "lacks": "charge per clinician and keep your data in their system, with no editable cost per client or group break-even planner"},
 {"what": "single-sheet session logs", "lacks": "record sessions only, so the source of each client and what marketing cost are never counted"},
 {"what": "generic marketing spreadsheets", "lacks": "track spend but not value per enquiry, referrer rhythm, listing payback or group profit per facilitator hour"},
 {"what": "online directory dashboards", "lacks": "show profile views but not clients won, months to pay back or how the listing compares with other channels"}]
guide = [
 'Open Start and type your practice name and your targets in the yellow cells: contact rhythm for referrers, average charge, margin, most you pay to win a client, minimum group fill and wanted feedback score.',
 'Check Team, Programs and the Referrers sheet. An employed clinician is paid a salary, a contract (self-employed) clinician a share of each session, an associate (works under supervision) per session.',
 'Log every enquiry on Enquiries by Source with its referral source and referrer. Source Performance by Month totals enquiries, booked clients and revenue per source; value per enquiry and per client are worked out for you.',
 'Keep the Referral Log and Referrer Contacts up to date. Record receipt of a referral only, never details about a client. The Referrers sheet ranks who to contact first by value and days since the last contact.',
 'Record every marketing activity on Campaigns, with cost, enquiries and clients won. Marketing Budget takes the amount spent from your campaigns; Directory Listings and Website Performance follow the two channels you pay for every month.',
 'Add each workshop, talk and newsletter issue, and each client feedback answer (a score from 1 to 10 and a recommend answer, never comments).',
 'Plan groups on Groups: fill rate, facilitator pay as a share of fees, break-even sign-ups, profit, profit per person and per facilitator hour fill in. Group Sign-ups, Group Attendance and the Group Interest List follow each person.',
 'Use the 18 decision tools: each ends with a verdict and a what-if table. Print 12 sheets and 12 documents, follow 12 checklists and send 34 ready messages.',
 'A sliding scale is a lower fee agreed from the client\'s means. A third-party payer is an organisation that pays part of a client\'s fee. Check your own local rules for privacy and consent.',
 'Why a workbook: one flat price, no per-clinician fee, and your data stays with you in your own file. The workbook holds status only, never note content.',
 'Read the Marketing KPI Dashboard and Charts every month: referral share, referrers past their rhythm, cost per client won, group fill rate and profit, and the feedback score.']
listing = {"title": "Therapy Practice Marketing Excel Template: Referral Source Value, Referrer Log, Cost per Client Won, Group Programs, KPI Dashboard",
 "headline": "Know where clients come from and fill every group in one Excel file",
 "tags": ["therapy practice", "referral tracker", "marketing tracker", "group program", "counselling practice", "practice management", "excel template", "client acquisition", "private practice", "referrer log",
          "marketing budget", "cost per client", "group planner"],
 "description": ("Know which referral sources, referrers and channels bring the clients who stay, and run group programs that make a profit, in one Excel workbook. Built for a small group practice of talking therapists and counsellors: an owner-clinician, employed clinicians, contract (self-employed) clinicians, an associate who works under supervision and a front-desk coordinator.\n\n"
  "Source Performance by Month totals enquiries, booked clients and revenue for nine referral sources, then works out value per enquiry and value per client first. The Referrers sheet shows 12-month referrals, value, days since the last contact and an act-first rank, without a single client detail. "
  "Campaigns show cost per enquiry and cost per client won against the most you accept to pay; Marketing Budget, Directory Listings, Website Performance, Workshops and Talks, Newsletter Issues and a Client Feedback Survey keep every channel honest. "
  "Groups show fill rate, facilitator pay as a share of fees, break-even sign-ups, profit, profit per person and profit per facilitator hour, with sign-ups, attendance, an interest list with the next start date and new group ideas.\n\n"
  f"{len(tools)} decision tools answer weekly questions with a verdict and a what-if table: referral source value, cost per client won, marketing return, client lifetime value, directory listing check, workshop planner, referrer contact schedule, budget split, group pricing, group break-even, new group business case, source forecast and more. "
  f"Print {len(forms)} sheets and {len(documents)} letters and reports, follow {len(checklists)} checklists and send {len(messages)} ready text messages.\n\n"
  "This is part seven of the Therapy Private Practice suite. A standard .xlsx workbook with no macros and no subscription, one flat price with no per-clinician fee, your data stays with you, 15 languages in one purchase, with a demo copy full of sample data. The workbook holds status only, never session notes or diagnoses, and it does not promise results."),
 "features": ["Enquiries and booked clients by referral source", "Value per enquiry and per client by source", "Referrer log with the contact rhythm", "Cost per enquiry and per client won", "Directory listing keep-or-drop check",
              "Workshop, talk and newsletter planners", "Group pricing, break-even and profit per hour", "Group fill, attendance and interest list", f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents",
              f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "One flat price, your data stays with you"]}
s = _lib.spec(id=f'{SUITE}-p7', slug='therapy-practice-marketing', profession='Therapy Private Practice', name='Referrals, Marketing and Groups',
         tagline='Know where clients come from and fill every group', price_usd=29, colors={"primary": "#2F5D62", "accent": "#A7C4BC"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard,
         forms=forms, guide=guide, listing=listing, insights=insights, suite={"key": SUITE, "part": 7, "of": 8, "focus": "Referrals, marketing and group programs"}, signature=signature, competitors=competitors,
         tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'th7.en.json'))
    print('tables', len(tables), 'rows', sum(len(t['demo']) for t in tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']), 'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'name', len(s['name']), 'tag', len(s['tagline']))
