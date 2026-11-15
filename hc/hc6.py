"""Home care agency suite - part 6: Recruiting, Onboarding and Renewals."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib as _lib
from hc6_lists import *
from hc6_tables import settings, tables, CA, STAFF
from hc6_tools import tools

SUITE = 'fx-20261115-home-care-agency'
NOTE = "Sample wording: adapt it to your own agency and check your own local rules."
def F(*p): return [FV(a, b) for a, b in p]
def cnt(tb, col, pick): return 'COUNTIFS({range:%s.%s},INDEX({range:%s.%s},MATCH({pick},{range:%s},0)))' % (tb, col, tb, col, pick)

forms = [
 FORM('applicant_sheet', 'Applicant Sheet', 'Applicant with call speed and stage reached', 'applicants.applicant_id', F(
  ('Applied on', 'applicants.applied_on'), ('Name', 'applicants.name'), ('Phone', 'applicants.phone'), ('Source', 'applicants.source'), ('Phone screen on', 'applicants.phone_screen_on'), ('Interview on', 'applicants.interview_on'),
  ('Offer on', 'applicants.offer_on'), ('Start on', 'applicants.start_on'), ('Status', 'applicants.status'), ('Stage reached', 'applicants.stage'), ('Days to first call', 'applicants.days_to_call'), ('Days to start', 'applicants.days_to_start'),
  ('Call check', 'applicants.wait_check')) + [FF('Applicants from the same source', cnt('applicants', 'source', 'applicants.applicant_id'), 'int')]),
 FORM('screen_sheet', 'Phone Screen Sheet', 'Phone screen with result and minutes', 'screens.screen_id', F(
  ('Date', 'screens.date'), ('Applicant ID', 'screens.applicant_id'), ('Applicant', 'screens.name'), ('Kind', 'screens.kind'), ('Done by', 'screens.done_by'), ('Result', 'screens.result'), ('Minutes', 'screens.minutes'), ('Days after applying', 'screens.days_after')) + [
  FF('Average minutes, all screens', 'AVERAGE({range:screens.minutes})', 'num'), FF('Screens by this person', cnt('screens', 'done_by', 'screens.screen_id'), 'int')]),
 FORM('interview_sheet', 'Interview Sheet', 'Interview with the applicant record', 'screens.screen_id', F(
  ('Interview date', 'screens.date'), ('Applicant', 'screens.name'), ('Interviewer', 'screens.done_by'), ('Result', 'screens.result'), ('Minutes', 'screens.minutes'), ('Days after applying', 'screens.days_after')) + [
  FF('Applicant status', 'IFERROR(INDEX({range:applicants.status},MATCH(INDEX({range:screens.applicant_id},MATCH({pick},{range:screens.screen_id},0)),{range:applicants.applicant_id},0)),"")', 'text'),
  FF('Applicant phone', 'IFERROR(INDEX({range:applicants.phone},MATCH(INDEX({range:screens.applicant_id},MATCH({pick},{range:screens.screen_id},0)),{range:applicants.applicant_id},0)),"")', 'text'),
  FF('Interviews done by this person', cnt('screens', 'done_by', 'screens.screen_id'), 'int')]),
 FORM('offer_sheet', 'Offer Sheet', 'Offer with pay, hours and answer', 'offers.offer_id', F(
  ('Offer on', 'offers.offer_on'), ('Applicant', 'offers.name'), ('Phone', 'offers.phone'), ('Pay per hour', 'offers.pay_rate'), ('Hours a week', 'offers.hours_week'), ('Answer', 'offers.answer'), ('Answered on', 'offers.answered_on'),
  ('Start on', 'offers.start_on'), ('Days to answer', 'offers.days_to_answer'), ('Days to start', 'offers.days_to_start'))),
 FORM('reference_sheet', 'Reference Check Sheet', 'Reference check with dates and owner', 'onboarding.onboarding_id', F(
  ('Person', 'onboarding.person'), ('Phone', 'onboarding.phone'), ('Start date', 'onboarding.start_date'), ('References on', 'onboarding.references_on'), ('Identity check on', 'onboarding.identity_check_on'),
  ('Background check on', 'onboarding.background_check_on'), ('Owner', 'onboarding.owner')) + [FF('Days from references to start', 'INDEX({range:onboarding.start_date},MATCH({pick},{range:onboarding.onboarding_id},0))-INDEX({range:onboarding.references_on},MATCH({pick},{range:onboarding.onboarding_id},0))', 'int')]),
 FORM('onboarding_sheet', 'Onboarding Sheet', 'Onboarding steps, dates and next due', 'onboarding.onboarding_id', F(
  ('Person', 'onboarding.person'), ('Caregiver ID', 'onboarding.caregiver_id'), ('Start date', 'onboarding.start_date'), ('Identity check on', 'onboarding.identity_check_on'), ('References on', 'onboarding.references_on'), ('Background check on', 'onboarding.background_check_on'),
  ('Training on', 'onboarding.training_on'), ('Agreement signed on', 'onboarding.agreement_signed_on'), ('First shift on', 'onboarding.first_shift_on'), ('Owner', 'onboarding.owner'), ('Steps done', 'onboarding.steps_done'), ('90-day check-in', 'onboarding.checkin_on'))),
 FORM('ready_sheet', 'First Shift Ready Sheet', 'Ready or Blocked for a first shift', 'onboarding.onboarding_id', F(
  ('Person', 'onboarding.person'), ('Steps done', 'onboarding.steps_done'), ('Steps missing', 'onboarding.steps_missing'), ('Ready for first shift', 'onboarding.ready_check'), ('Days to ready', 'onboarding.days_to_ready'), ('First shift on', 'onboarding.first_shift_on')) + [
  FF('People blocked now', 'COUNTIFS({range:onboarding.ready_check},%s)' % ck('Blocked'), 'int'), FF('People ready now', 'COUNTIFS({range:onboarding.ready_check},%s)' % ck('Ready'), 'int')]),
 FORM('renewal_sheet', 'Credential Renewal Sheet', 'Credential renewal with course booking', 'renewals.renewal_id', F(
  ('Caregiver', 'renewals.caregiver'), ('Phone', 'renewals.phone'), ('Credential', 'renewals.credential'), ('Expires on', 'renewals.expires_on'), ('Days left', 'renewals.days_left'), ('Colour', 'renewals.colour'), ('Renew by', 'renewals.renew_by'),
  ('Booking', 'renewals.booking_check'), ('Visits after expiry', 'renewals.visits_at_risk'), ('People due, same credential', 'renewals.same_course'))),
 FORM('training_sheet', 'Training Record Sheet', 'Training record with hours and cost', 'training.training_id', F(
  ('Date', 'training.date'), ('Caregiver', 'training.caregiver'), ('Phone', 'training.phone'), ('Course', 'training.course'), ('Hours', 'training.hours'), ('Provider', 'training.provider'), ('Paid hours', 'training.paid'), ('Course fee', 'training.fee'),
  ('Training cost', 'training.training_cost')) + [FF('Training hours of this caregiver', 'SUMIFS({range:training.hours},{range:training.caregiver},INDEX({range:training.caregiver},MATCH({pick},{range:training.training_id},0)))', 'num')]),
 FORM('leaver_sheet', 'Leaver Sheet', 'Leaver with tenure and reason', 'leavers.leaver_id', F(
  ('Caregiver', 'leavers.caregiver'), ('Phone', 'leavers.phone'), ('Hire date', 'leavers.hire_date'), ('Left date', 'leavers.left_date'), ('Reason', 'leavers.reason'), ('Source', 'leavers.source'), ('Tenure (days)', 'leavers.tenure_days'), ('Tenure band', 'leavers.tenure_band')) + [
  FF('Leavers with the same reason', cnt('leavers', 'reason', 'leavers.leaver_id'), 'int')]),
 FORM('referral_sheet', 'Referral Bonus Sheet', 'Referral bonus with the 90-day date', 'referrals.referral_id', F(
  ('Referring caregiver', 'referrals.referring'), ('Phone', 'referrals.phone'), ('New caregiver', 'referrals.new_caregiver'), ('Hire date', 'referrals.hire_date'), ('90-day date', 'referrals.ninety_day'), ('Bonus amount', 'referrals.amount'),
  ('Paid on', 'referrals.paid_on'), ('Bonus check', 'referrals.due_flag'))),
 FORM('hirecost_sheet', 'Hiring Cost Sheet', 'Hiring cost with cost per hire', 'hirecost.cost_id', F(
  ('Month', 'hirecost.month'), ('Person', 'hirecost.person'), ('Hired', 'hirecost.hired'), ('Advert cost', 'hirecost.advert_cost'), ('Background check', 'hirecost.check_cost'), ('Paid training hours', 'hirecost.training_hours'), ('Training cost', 'hirecost.training_cost'),
  ('Other cost', 'hirecost.other_cost'), ('Total cost', 'hirecost.total_cost'), ('Cost per hire', 'hirecost.cost_per_hire')) + [FF('Hiring cost this year, all people', 'INDEX({range:hirecost.year_cost},1)', 'money')]),
]
assert len(forms) == 12

def D_(k, sheet, title, pick, paras, sign): return DOC(k, sheet, title, pick, paras, sign, NOTE)
documents = [
 D_('job_ad_doc', 'Job Advertisement', 'Job advertisement for a caregiver vacancy', 'campaigns.campaign_id', [
  'Caregiver wanted at {set:company}, dated {today}. Campaign {col:campaigns.campaign_id}, {col:campaigns.kind}.',
  'We are looking for a caregiver (carer, care worker or support worker) in {col:campaigns.area}. Hours: about {col:campaigns.hours_week} a week, with day, evening and weekend visits to suit you. Pay: {set:pay_low} to {set:pay_high} an hour, depending on the service and the time of day.',
  'We provide training and a paid onboarding. Please apply with your name and phone number and we will call you within {set:call_days} days. Checks and credentials are required; check your own local rules.'], ['Recruiter']),
 D_('offer_doc', 'Offer Letter', 'Offer letter for a caregiver', 'offers.offer_id', [
  'Offer letter of {set:company}, dated {today}. Dear {col:offers.name},',
  'We would like to offer you the position of caregiver: about {col:offers.hours_week} hours a week at {col:offers.pay_rate} an hour, starting on {col:offers.start_on}. Offer made on {col:offers.offer_on}, reference {col:offers.offer_id}.',
  'Please tell us your answer. The offer depends on your checks and signed agreement; confirm the details with your adviser and check your own local rules.'], ['Owner-director', 'Caregiver']),
 D_('agreement_doc', 'Caregiver Agreement', 'Caregiver agreement with generic terms', 'caregivers.caregiver_id', [
  'Caregiver agreement of {set:company}, dated {today}. Between the agency and {col:caregivers.name} (caregiver {col:caregivers.caregiver_id}).',
  'Start date: {col:caregivers.hire_date}. Employment: {col:caregivers.employment}. Home area: {col:caregivers.area}. Pay: {col:caregivers.pay_rate} an hour; overtime, holiday pay and payroll taxes follow your own local rules (confirm with your adviser).',
  'The caregiver agrees to keep clients\' details private, to arrive on time, to give notice when a visit cannot be covered and to keep credentials valid. This is sample wording, not legal advice.'], ['Owner-director', 'Caregiver']),
 D_('onb_list_doc', 'Onboarding Checklist Print', 'Printable onboarding checklist', 'onboarding.onboarding_id', [
  'Onboarding checklist of {set:company}, dated {today}. Person: {col:onboarding.person}. Start date: {col:onboarding.start_date}. Owner: {col:onboarding.owner}.',
  'Identity check: {col:onboarding.identity_check_on}. References: {col:onboarding.references_on}. Background check: {col:onboarding.background_check_on}. Training: {col:onboarding.training_on}. Agreement signed: {col:onboarding.agreement_signed_on}. First shift: {col:onboarding.first_shift_on}.',
  'Steps done: {col:onboarding.steps_done} of 5. Ready for first shift: {col:onboarding.ready_check}. Tick each step when done and sign below.'], ['Recruiter', 'Caregiver']),
 D_('welcome_doc', 'Welcome Pack', 'Welcome pack for a new caregiver', 'onboarding.onboarding_id', [
  'Welcome to {set:company}, {col:onboarding.person}. Your first day is {col:onboarding.start_date}.',
  'Your onboarding owner is {col:onboarding.owner}. We will agree your first shift once the five steps are done; your 90-day check-in is on {col:onboarding.checkin_on}.',
  'Please keep your phone on for schedule messages, tell us early if a visit cannot be covered and keep your credentials valid. Call us any time you have a question.'], ['Recruiter']),
 D_('renewal_doc', 'Renewal Reminder Letter', 'Renewal reminder letter', 'renewals.renewal_id', [
  'Renewal reminder of {set:company}, dated {today}. Dear {col:renewals.caregiver},',
  'Your {col:renewals.credential} expires on {col:renewals.expires_on}, in {col:renewals.days_left} days. Please renew by {col:renewals.renew_by}. Visits scheduled after the expiry date: {col:renewals.visits_at_risk}.',
  'From the day after it expires we cannot schedule you until it is renewed; check your own local rules. Course booking: {col:renewals.booking_check}.'], ['Recruiter']),
 D_('training_doc', 'Training Record', 'Training record for a caregiver', 'training.training_id', [
  'Training record of {set:company}, dated {today}. Caregiver: {col:training.caregiver}.',
  'Course: {col:training.course}. Date: {col:training.date}. Hours: {col:training.hours}. Provider: {col:training.provider}. Paid hours: {col:training.paid}. Cost: {col:training.training_cost}.',
  'The caregiver attended the full course. Reference {col:training.training_id}.'], ['Trainer', 'Caregiver']),
 D_('leaver_doc', 'Leaver Letter', 'Leaver letter', 'leavers.leaver_id', [
  'Leaver letter of {set:company}, dated {today}. Dear {col:leavers.caregiver},',
  'This confirms that your last day with us was {col:leavers.left_date}. You started on {col:leavers.hire_date}, so you worked {col:leavers.tenure_days} days. Reason recorded: {col:leavers.reason}.',
  'Please return any agency items. Final pay and taxes follow your own local rules; confirm with your adviser. Thank you for your work with our clients.'], ['Owner-director']),
 D_('recruit_report_doc', 'Recruiting Report', 'Recruiting report for one month', 'funnel.funnel_id', [
  'Recruiting report of {set:company}, dated {today}. Month {col:funnel.month}.',
  'Applicants: {col:funnel.applicants}. Phone screens: {col:funnel.phone_screens}. Interviews: {col:funnel.interviews}. Offers: {col:funnel.offers}. Starts: {col:funnel.starts}. Applicants per start: {col:funnel.per_start}.',
  'Decisions for the weekly hiring review are written below.'], ['Recruiter', 'Owner-director']),
 D_('turnover_doc', 'Turnover Report', 'Turnover report for one month', 'turnover.turn_id', [
  'Turnover report of {set:company}, dated {today}. Month {col:turnover.month}.',
  'Caregivers at the start: {col:turnover.caregivers_start}. Hires: {col:turnover.hires}. Leavers: {col:turnover.leavers}. First-90-day leavers: {col:turnover.first90}. Caregivers at the end: {col:turnover.caregivers_end}.',
  'Turnover over the last 12 months: {col:turnover.turnover_pct} percent, against a flag of {set:turnover_flag} as a share. First-90-day leavers this year: {col:turnover.first90_year}.'], ['Owner-director']),
 D_('cred_register_doc', 'Credential Register', 'Credential register entry', 'credentials.credential_id', [
  'Credential register of {set:company}, dated {today}. Entry {col:credentials.credential_id}.',
  'Caregiver: {col:credentials.caregiver}. Credential: {col:credentials.credential}. Issued on {col:credentials.issued_on}; expires on {col:credentials.expires_on}. Status: {col:credentials.status}.',
  'Days left: {col:credentials.days_left}. Colour: {col:credentials.colour}. Cannot be scheduled from: {col:credentials.cannot_schedule}.'], ['Recruiter']),
 D_('hire_case_doc', 'Hire Business Case', 'Hire business case for the owner', 'hireplan.plan_id', [
  'Hire business case of {set:company}, dated {today}. Week of {col:hireplan.week}.',
  'Hours waiting for a caregiver: {col:hireplan.hours_waiting}. Free caregiver hours that fit: {col:hireplan.free_hours}. Gap: {col:hireplan.gap_hours} hours, which is {col:hireplan.caregivers_needed} caregivers at {set:hours_per_caregiver} hours a week.',
  'Margin per hour {set:margin_hour}; weeks to full hours {set:weeks_to_full}. Use the Hire-or-Not Decision tool for the payback and write the decision below.'], ['Recruiter', 'Owner-director']),
]
assert len(documents) == 12

def CS(k, title, table, start, steps): return _lib.CHK(k, title, table, start, steps)
checklists = [
 CS('c_applicant', 'Applicant Screening Steps', 'applicants', 'applicants.applied_on', [('Reply and thank the applicant', 0), ('Check hours, area and pay fit', 1), ('Book the phone screen', 1), ('Record the source', 1), ('Send the call-by message', 1)]),
 CS('c_phone', 'Phone Screen Steps', 'screens', 'screens.date', [('Check the applicant record before the call', 0), ('Ask about hours, area, languages and transport', 0), ('Explain pay, visits and the process', 0), ('Record minutes and result', 0), ('Send the next-step message', 1)]),
 CS('c_interview', 'Interview Steps', 'screens', 'screens.date', [('Prepare the questions', -1), ('Hold the interview', 0), ('Record the result and minutes', 0), ('Decide within two days', 2), ('Tell the applicant', 3)]),
 CS('c_checks', 'Identity and Background Checks', 'onboarding', 'onboarding.start_date', [('Check identity documents; check your own local rules', -12), ('Take two references', -8), ('Start the background check', -10), ('Record the results', -7), ('Decide if the person can continue', -6)]),
 CS('c_offer', 'Offer and Acceptance Steps', 'offers', 'offers.offer_on', [('Send the offer with pay and hours', 0), ('Remind after two days', 2), ('Record the answer', 4), ('Agree the start date', 4), ('Start the checks', 5)]),
 CS('c_onboard', 'Onboarding Week Steps', 'onboarding', 'onboarding.start_date', [('Welcome call', -3), ('Paid onboarding training', 0), ('Sign the agreement', -3), ('Meet a field supervisor', 2), ('Shadow a visit', 3), ('Check-in at the end of the week', 6)]),
 CS('c_ready', 'Ready for First Shift Steps', 'onboarding', 'onboarding.start_date', [('Five checks done', -2), ('Tell the scheduler: Ready', -1), ('Send the first shift message', 0), ('Introduce the caregiver to the client', 4), ('Check how the first shift went', 6)]),
 CS('c_renew60', '60-Day Credential Renewal Steps', 'renewals', 'renewals.expires_on', [('Send the 60-day reminder', -60), ('Book the course', -45), ('Tell the scheduler about visits after expiry', -30), ('Send the 30-day reminder', -30), ('Record the renewal', -3)]),
 CS('c_training', 'Training Completion Steps', 'training', 'training.date', [('Confirm attendance', 0), ('Record hours and cost', 0), ('File the certificate', 2), ('Send a thank-you message', 1)]),
 CS('c_leaver', 'Leaver Exit Steps', 'leavers', 'leavers.left_date', [('Record the reason', 0), ('Remove the caregiver from the schedule', 0), ('Collect agency items', 1), ('Send final pay details; confirm with your adviser', 3), ('Send the leaver letter', 2)]),
 CS('c_90day', '90-Day Check-in Steps', 'caregivers', 'caregivers.hire_date', [('First week call', 7), ('30-day check-in', 30), ('60-day check-in', 60), ('90-day check-in', 90), ('Referral bonus check', 91)]),
 CS('c_review', 'Monthly Recruiting Review Steps', 'funnel', 'funnel.month', [('Check applicants and starts', 1), ('Check the weakest funnel step', 2), ('Check the source ranking', 3), ('Check credentials due in 60 days', 3), ('Check hours waiting and the hire decision', 5)]),
]
assert len(checklists) == 12

def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
 M('a_thanks', 'Applicant: thank you for applying', 'applicants', 'applicants.phone', 'Hello {name}, thank you for applying to {company}. We will call you by {call_by}.'),
 M('a_screen', 'Applicant: your phone screen', 'applicants', 'applicants.phone', 'Hello {name}, your phone screen with {company} is on {phone_screen_on}. Reply here if the time does not suit you.'),
 M('a_interview', 'Applicant: your interview', 'applicants', 'applicants.phone', 'Hello {name}, your interview at {company} is on {interview_on}. We look forward to meeting you.'),
 M('a_offer', 'Applicant: we offer you the position', 'offers', 'offers.phone', 'Hello {name}, we would like to offer you the caregiver position at {company}: {hours_week} hours a week at {pay_rate} an hour. Please tell us your answer.'),
 M('a_start', 'Applicant: confirm your start date', 'offers', 'offers.phone', 'Hello {name}, please confirm your start date of {start_on} with {company}.'),
 M('a_decline', 'Applicant: not going ahead', 'applicants', 'applicants.phone', 'Hello {name}, thank you for your time. {company} is not going ahead this time. You are welcome to apply again.'),
 M('a_docs', 'Applicant: send your documents', 'applicants', 'applicants.phone', 'Hello {name}, please send the documents we asked for so {company} can move your application forward.'),
 M('a_noreach', 'Applicant: we could not reach you', 'applicants', 'applicants.phone', 'Hello {name}, we could not reach you about your application to {company}. Are you still interested? Please reply.'),
 M('n_welcome', 'New caregiver: welcome', 'onboarding', 'onboarding.phone', 'Hello {person}, welcome to {company}. Your first day is {start_date}.'),
 M('n_due', 'New caregiver: steps due', 'onboarding', 'onboarding.phone', 'Hello {person}, your next onboarding step at {company} is due on {next_due}. Please reply if you need help.'),
 M('n_ready', 'New caregiver: ready for first shift', 'onboarding', 'onboarding.phone', 'Hello {person}, you are ready for your first shift on {first_shift_on}. {company}'),
 M('n_training', 'New caregiver: training booked', 'training', 'training.phone', 'Hello {caregiver}, your {course} training at {company} is booked for {date}, {hours} hours.'),
 M('n_week', 'New caregiver: first week', 'onboarding', 'onboarding.phone', 'Hello {person}, how is your first week going? Tell us what we can help with. {company}'),
 M('n_90', 'New caregiver: 90-day check-in', 'onboarding', 'onboarding.phone', 'Hello {person}, your 90-day check-in with {company} is on {checkin_on}.'),
 M('c_expires', 'Caregiver: credential expires', 'renewals', 'renewals.phone', 'Hello {caregiver}, your {credential} expires on {expires_on}. Please renew by {renew_by}. {company}'),
 M('c_days', 'Caregiver: visits will move', 'renewals', 'renewals.phone', 'Hello {caregiver}, your {credential} expires in {days_left} days and visits after it will move. Please renew soon. {company}'),
 M('c_renewed', 'Caregiver: renewal recorded', 'credentials', 'credentials.phone', 'Hello {caregiver}, your renewed {credential} is recorded, thank you. {company}'),
 M('c_course', 'Caregiver: your training course', 'training', 'training.phone', 'Hello {caregiver}, your training course ({course}) is on {date}. {company}'),
 M('c_bonus', 'Caregiver: referral bonus paid', 'referrals', 'referrals.phone', 'Hello {referring}, your referral bonus of {amount} for {new_caregiver} is paid. Thank you. {company}'),
 M('c_friend', 'Caregiver: introduce a friend', 'referrals', 'referrals.phone', 'Hello {referring}, please introduce a friend to {company}. The referral bonus is {amount}.'),
 M('r_screens', 'Recruiter: applicants to screen', 'applicants', 'applicants.recruiter_phone', 'Hello, {waiting_count} applicants need a phone screen this week. Open the Applicants page for the list.'),
 M('r_offer', 'Recruiter: offer not answered', 'offers', 'offers.recruiter_phone', 'Hello, the offer to {name} is not answered after {days_open} days. Please call.'),
 M('r_onb', 'Recruiter: onboarding steps missing', 'onboarding', 'onboarding.recruiter_phone', 'Hello, onboarding for {person} has {steps_missing} steps missing. Start date {start_date}.'),
 M('s_notready', 'Scheduler: not ready, do not schedule', 'onboarding', 'onboarding.scheduler_phone', 'Hello, {person} is not ready for a first shift ({steps_missing} steps missing). Please do not schedule yet.'),
 M('s_cannot', 'Scheduler: cannot be scheduled', 'renewals', 'renewals.scheduler_phone', 'Hello, {caregiver} cannot be scheduled after {expires_on} until the {credential} is renewed.'),
 M('s_visits', 'Scheduler: visits need another caregiver', 'renewals', 'renewals.scheduler_phone', 'Hello, {visits_at_risk} visits after {expires_on} need another caregiver ({caregiver}, {credential}).'),
 M('o_turn', 'Owner: turnover over 12 months', 'turnover', 'turnover.owner_phone', 'Hello, turnover over 12 months to {month} is {turnover_pct} percent. {company}'),
 M('o_first90', 'Owner: first-90-day leavers', 'turnover', 'turnover.owner_phone', 'Hello, {first90_year} new caregivers left within 90 days this year (to {month}). {company}'),
 M('o_hire', 'Owner: hire decision is ready', 'hireplan', 'hireplan.owner_phone', 'Hello, hours waiting for a caregiver in the week of {week} are {hours_waiting}; the hire decision is ready. {company}'),
 M('o_source', 'Owner: source result', 'sources', 'sources.owner_phone', 'Hello, source check: {source} brought {starts} starts at {cost_per_start} each in {month}, {active_90} still active after 90 days. {company}'),
 M('t_book', 'Training provider: please book', 'renewals', 'renewals.training_phone', 'Hello, please book {same_course} caregivers on the {credential} course. Next expiry {expires_on}. {company}'),
 M('b_checks', 'Background checks: please run', 'onboarding', 'onboarding.bg_phone', 'Hello, please run the background checks for {checks_needed} new caregivers. {company}'),
 M('i_broker', 'Insurance broker: new caregivers', 'caregivers', 'caregivers.broker_phone', 'Hello, the new caregiver list for the workers\' insurance estimate is attached: {hired_12m} caregivers hired in the last 12 months. {company}'),
 M('x_acc', 'Accountant: hiring costs attached', 'hirecost', 'hirecost.accountant_phone', 'Hello, the hiring costs for the year are attached: {year_cost} so far this year. {company}'),
]
assert len(messages) == 34
need = {m['table'] for m in messages}
for t in tables:
    if t['key'] in need and not any(c['key'] == 'company' for c in t['columns']): t['columns'].append(CA('company', 'Agency', 'text', '{set:company}&""', 24))
for t in tables:
    if t['key'] in ('renewals', 'training', 'credentials'): pass
# caregiver placeholder in training/credentials/renewals: the column is called caregiver (present)

MS_ = 'DATE(YEAR({today}),MONTH({today}),1)'
def L30(c): return '{range:%s},">="&({today}-29),{range:%s},"<="&{today}' % (c, c)
def TM(c): return '{range:%s},">="&%s,{range:%s},"<="&{today}' % (c, MS_, c)
def L90(c): return '{range:%s},">="&({today}-89),{range:%s},"<="&{today}' % (c, c)
def L12(c): return '{range:%s},">="&({today}-364),{range:%s},"<="&{today}' % (c, c)
M12 = '{range:hirecost.month},">="&DATE(YEAR({today}),MONTH({today})-11,1),{range:hirecost.month},"<="&{today}'
YES = '{list:yesno.yes}'
LV12 = 'COUNTIFS(%s)' % L12('caregivers.left_date')
kpis = [
 KPI('Applicants this month', 'COUNTIFS(%s)' % TM('applicants.applied_on'), 'int'),
 KPI('Applicants last 30 days', 'COUNTIFS(%s)' % L30('applicants.applied_on'), 'int'),
 KPI('Phone screens this month', 'COUNTIFS(%s)' % TM('applicants.phone_screen_on'), 'int'),
 KPI('Interviews this month', 'COUNTIFS(%s)' % TM('applicants.interview_on'), 'int'),
 KPI('Offers open', 'COUNTIFS({range:offers.answer},%s)' % tok('outcome', 'Waiting'), 'int'),
 KPI('Offers accepted last 90 days', 'COUNTIFS({range:offers.answer},%s,%s)' % (tok('outcome', 'Accepted'), L90('offers.offer_on')), 'int'),
 KPI('Caregivers started this month', 'COUNTIFS(%s)' % TM('caregivers.hire_date'), 'int'),
 KPI('Caregivers started last 12 months', 'COUNTIFS(%s)' % L12('caregivers.hire_date'), 'int'),
 KPI('Applicant-to-start rate, 90 days', 'IFERROR(COUNTIFS({range:applicants.status},%s,%s)/COUNTIFS(%s),0)' % (tok('applst', 'Started'), L90('applicants.applied_on'), L90('applicants.applied_on')), 'pct'),
 KPI('Days from applying to start, 12 mo', 'IFERROR(AVERAGEIFS({range:applicants.days_to_start},%s),0)' % L12('applicants.start_on'), 'num', alert={"when": "> {set:days_to_start_target}", "style": "warn"}),
 KPI('Cost per hire last 12 months', 'IFERROR(SUMIFS({range:hirecost.total_cost},%s)/COUNTIFS({range:hirecost.hired},%s,%s),0)' % (M12, YES, M12), 'money'),
 KPI('Applicants waiting for a call', 'COUNTIFS({range:applicants.wait_check},%s)' % ck('Call overdue'), 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('People in onboarding', 'COUNT({range:onboarding.start_date})-COUNT({range:onboarding.first_shift_on})', 'int'),
 KPI('Onboarding steps overdue', 'COUNTIFS({range:steps.overdue_check},%s)' % ck('Overdue'), 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Caregivers not ready for a first shift', 'COUNTIFS({range:onboarding.ready_check},%s)' % ck('Blocked'), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Credentials expiring in 60 days', 'COUNTIFS({range:credentials.days_left},">=0",{range:credentials.days_left},"<="&{set:renewal_warn_days})', 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Credentials expiring in 30 days', 'COUNTIFS({range:credentials.days_left},">=0",{range:credentials.days_left},"<="&{set:renewal_red_days})', 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Credentials expired and not renewed', 'COUNTIFS({range:credentials.colour},%s)' % ck('Expired'), 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Credentials due in 14 days', 'COUNTIFS({range:credentials.days_left},">=0",{range:credentials.days_left},"<=14")', 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Visits after a credential expires', 'COUNTIFS({range:visitsafter.days_after},">0")', 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Renewals booked', 'COUNTIFS({range:renewals.booking_check},%s)' % ck('Booked'), 'int'),
 KPI('Training hours this year', 'SUMIFS({range:training.hours},{range:training.date},">="&DATE(YEAR({today}),1,1),{range:training.date},"<="&{today})', 'num'),
 KPI('Training cost this year', 'SUMIFS({range:training.training_cost},{range:training.date},">="&DATE(YEAR({today}),1,1),{range:training.date},"<="&{today})', 'money'),
 KPI('Leavers this month', 'COUNTIFS(%s)' % TM('caregivers.left_date'), 'int'),
 KPI('Leavers last 12 months', LV12, 'int'),
 KPI('Annual turnover rate', 'IFERROR(SUMIFS({range:turnover.trail12},{range:turnover.month},%s),0)' % MS_, 'pct', alert={"when": "> {set:turnover_flag}", "style": "bad"}),
 KPI('First-90-day leavers last 12 months', 'COUNTIFS({range:leavers.tenure_days},"<=90",%s)' % L12('leavers.left_date'), 'int'),
 KPI('Share of leavers in the first 90 days', 'IFERROR(COUNTIFS({range:leavers.tenure_days},"<=90",%s)/%s,0)' % (L12('leavers.left_date'), LV12), 'pct'),
 KPI('Cost of turnover last 12 months', '%s*(IFERROR(SUMIFS({range:hirecost.total_cost},%s)/COUNTIFS({range:hirecost.hired},%s,%s),0)+{set:weeks_to_full}*{set:hours_per_caregiver}*{set:margin_hour}*{set:ramp_loss_share})' % (LV12, M12, YES, M12), 'money'),
 KPI('Hours waiting for a caregiver this week', 'SUMIFS({range:hireplan.hours_waiting},{range:hireplan.week},{today}-WEEKDAY({today},2)+1)', 'num'),
]
assert len(kpis) == 30
dashboard = {"title": "Recruiting KPI Dashboard", "kpis": kpis,
 "monthly": {"title": "Applicants, screens, offers and starts", "date": "funnel.month", "series": [
   {"label": "Applicants", "sum": "funnel.applicants", "date": "funnel.month"}, {"label": "Phone screens", "sum": "funnel.phone_screens", "date": "funnel.month"},
   {"label": "Offers", "sum": "funnel.offers", "date": "funnel.month"}, {"label": "Starts", "sum": "funnel.starts", "date": "funnel.month"}]},
 "breakdowns": [{"title": "Applicants by source", "by": "applicants.source", "agg": "count"}, {"title": "Applicants by status", "by": "applicants.status", "agg": "count"},
                {"title": "Credentials by type", "by": "credentials.credential", "agg": "count"}, {"title": "Leavers by reason", "by": "leavers.reason", "agg": "count"}]}
def TKN(l, v): return tok(l, v)
insights = {"filters": [{"label": "Source", "list": "recsrc"}, {"label": "Credential", "list": "cred"}, {"label": "Reason leaving", "list": "leave"}],
 "gauges": [
  {"title": "Annual turnover under the flag", "num": AGG('count', 'turnover', where=[('trail12', '<=', '{set:turnover_flag}')]), "den": AGG('count', 'turnover', where=[('trail12', '>=', 0)])},
  {"title": "First-90-day retention", "num": AGG('sum', 'sources', 'sources.active_90'), "den": AGG('sum', 'sources', 'sources.starts')},
  {"title": "Caregivers ready for first shift", "num": AGG('count', 'onboarding', where=[('ready_check', '=', ck('Ready'))]), "den": AGG('count', 'onboarding')},
  {"title": "Credentials valid for 60 days", "num": AGG('count', 'credentials', where=[('days_left', '>', '{set:renewal_warn_days}')]), "den": AGG('count', 'credentials', where=[('days_left', '>=', 0)])},
  {"title": "Applicants called within 3 days", "num": AGG('count', 'applicants', where=[('days_to_call', '<=', '{set:call_days}')]), "den": AGG('count', 'applicants', where=[('days_to_call', '>=', 0)])},
  {"title": "Offers accepted", "num": AGG('count', 'offers', where=[('answer', '=', tok('outcome', 'Accepted'))]), "den": AGG('count', 'offers', where=[('answer', '<>', tok('outcome', 'Waiting'))])}],
 "charts": [
  CHART('Applicants per month', 'column', 'month', [AGG('sum', 'funnel', 'funnel.applicants', date='funnel.month', label='Applicants')]),
  CHART('Applicants by source', 'bar', 'applicants.source', [AGG('count', 'applicants', label='Applicants')]),
  CHART('Starts per month', 'column', 'month', [AGG('sum', 'funnel', 'funnel.starts', date='funnel.month', label='Starts')]),
  CHART('Starts by source', 'bar', 'sources.source', [AGG('sum', 'sources', 'sources.starts', label='Starts')]),
  CHART('Funnel by stage per month', 'column', 'month', [AGG('sum', 'funnel', 'funnel.phone_screens', date='funnel.month', label='Phone screens'), AGG('sum', 'funnel', 'funnel.interviews', date='funnel.month', label='Interviews'),
                                                       AGG('sum', 'funnel', 'funnel.offers', date='funnel.month', label='Offers'), AGG('sum', 'funnel', 'funnel.starts', date='funnel.month', label='Starts')]),
  CHART('Conversion per month', 'line', 'month', [AGG('avg', 'funnel', 'funnel.screen_rate', date='funnel.month', label='Screened'), AGG('avg', 'funnel', 'funnel.offer_rate', date='funnel.month', label='Offered'), AGG('avg', 'funnel', 'funnel.start_rate', date='funnel.month', label='Started')]),
  CHART('Days to start per month', 'line', 'month', [AGG('avg', 'applicants', 'applicants.days_to_start', date='applicants.applied_on', label='Days to start')]),
  CHART('Cost per hire per month', 'line', 'month', [AGG('avg', 'hirecost', 'hirecost.cost_per_hire', date='hirecost.month', label='Cost per hire')]),
  CHART('Applicants by status', 'bar', 'applicants.status', [AGG('count', 'applicants', label='Applicants')]),
  CHART('Reasons applicants dropped out', 'bar', 'applicants.reason', [AGG('count', 'applicants', label='Applicants')]),
  CHART('Active after 90 days by source', 'bar', 'sources.source', [AGG('sum', 'sources', 'sources.active_90', label='Active after 90 days')]),
  CHART('Onboarding steps done by month', 'column', 'month', [AGG('count', 'steps', date='steps.done_on', label='Steps done')]),
  CHART('Credentials by type', 'bar', 'credentials.credential', [AGG('count', 'credentials', label='Credentials')]),
  CHART('Credentials expiring by month', 'column', 'month', [AGG('count', 'credentials', date='credentials.expires_on', label='Expiring', where=[('status', '=', tok('credst', 'Valid'))])]),
  CHART('Renewals by credential type', 'bar', 'renewals.credential', [AGG('count', 'renewals', label='Renewals due')]),
  CHART('Leavers per month', 'column', 'month', [AGG('sum', 'turnover', 'turnover.leavers', date='turnover.month', label='Leavers')]),
  CHART('Leavers by reason', 'bar', 'leavers.reason', [AGG('count', 'leavers', label='Leavers')]),
  CHART('Leavers by tenure band', 'stacked', 'month', [AGG('count', 'leavers', date='leavers.left_date', label='First 90 days', where=[('tenure_days', '<=', 90)]),
                                                     AGG('count', 'leavers', date='leavers.left_date', label='4 to 12 months', where=[('tenure_days', '>', 90), ('tenure_days', '<=', 365)]),
                                                     AGG('count', 'leavers', date='leavers.left_date', label='Over 1 year', where=[('tenure_days', '>', 365)])]),
  CHART('Turnover rate per month', 'line', 'month', [AGG('avg', 'turnover', 'turnover.trail12', date='turnover.month', label='Trailing 12 months'), AGG('avg', 'turnover', 'turnover.turnover_rate', date='turnover.month', label='In the month')]),
  CHART('First-90-day leavers per month', 'column', 'month', [AGG('sum', 'turnover', 'turnover.first90', date='turnover.month', label='First-90-day leavers')]),
  CHART('Training hours per month', 'column', 'month', [AGG('sum', 'training', 'training.hours', date='training.date', label='Training hours')]),
  CHART('Hours waiting for a caregiver per month', 'line', 'month', [AGG('avg', 'hireplan', 'hireplan.hours_waiting', date='hireplan.week', label='Hours waiting a week')])]}
assert len(insights['charts']) == 22

signature = [
 {"name": "Recruiting funnel with cost per hire", "why": "applicants, screens, interviews, offers and starts show the weakest step, days to start and cost per hire", "where": "Recruiting Funnel"},
 {"name": "Source ranking by 90-day retention", "why": "each source is ranked by cost per caregiver still active after 90 days: Grow, Keep or Cut", "where": "Source Ranking"},
 {"name": "Onboarding checklist with Ready or Blocked", "why": "five checks per caregiver give a ready-for-first-shift flag the schedule reads", "where": "Onboarding"},
 {"name": "Renewal register with 60 and 30-day colours", "why": "every credential shows days left, red, amber or green and the date after which no visit can be scheduled", "where": "Credentials"},
 {"name": "Visits after expiry list", "why": "visits that fall after a credential expires are listed so the scheduler moves them before they are missed", "where": "Visits After Expiry"},
 {"name": "Turnover by tenure with its cost", "why": "leavers split into first 90 days, 4 to 12 months and over 1 year, with the cost of turnover", "where": "Turnover by Month"},
 {"name": "Replacement cost calculator", "why": "advert, check, staff and onboarding hours and lost margin give the cost of one replacement and the saving if early leavers halve", "where": "Replacement Cost"},
 {"name": "Hire-or-not decision with payback", "why": "hours waiting, margin and hiring cost give months to pay back and Hire now, Wait or Not yet", "where": "Hire-or-Not Decision"},
 {"name": "Hire timing planner", "why": "monthly hours growth and your lead time give the month to start recruiting and the adverts to run", "where": "Hire Timing Planner"},
 {"name": "Referral bonus tracker", "why": "each referral shows its 90-day date and whether the bonus is due, paid or lost to an early leaver", "where": "Referral Bonuses"}]
competitors = [
 {"what": "free schedule template", "lacks": "lists shifts but has no applicant funnel, onboarding flag or credential renewal dates"},
 {"what": "subscription home care software with a per-caregiver fee", "lacks": "charges for every caregiver, keeps your data in its system and has no editable turnover flag or hire payback"},
 {"what": "single-sheet applicant list", "lacks": "records names only, so source retention, days to start and cost per hire are never worked out"},
 {"what": "generic checklist spreadsheet", "lacks": "ticks steps but cannot tell the scheduler who is ready or who cannot be scheduled after an expiry date"},
 {"what": "online job board dashboard", "lacks": "counts clicks and applicants but not who started or stayed 90 days"}]
guide = [
 'Open the Start tab and type your agency name and targets in the yellow cells: days to a first call, red and amber renewal days, the turnover flag and your hiring costs.',
 'A caregiver is also called a carer, care worker or support worker. Add each applicant on Applicants with the source; days to call, days to start and the stage reached fill in.',
 'Log phone screens and interviews on Screens and Interviews, and each offer on Offers. The Recruiting Funnel and Source by Month show conversion and cost per start.',
 'When someone accepts, add a row on Onboarding. Fill each check date as it happens: Ready or Blocked tells the scheduler whether a first shift can be set. A one-person agency can start with Applicants, Onboarding and Credentials.',
 'Keep every credential on Credentials with its expiry date. Red is under 30 days, amber under 60 (edit both on the Start tab). Renewals Due and Visits After Expiry show who cannot be scheduled after the date.',
 'Leavers and Turnover by Month show turnover (the share of caregivers who leave in a year) and first-90-day leavers; their cost comes from the Cost of Turnover and Replacement Cost tools.',
 'Hire Planning by Week records the hours waiting for a caregiver (a visit without a caregiver, or one covered at short notice). The Hire-or-Not Decision tool turns it into a verdict.',
 'Use the 18 decision tools: each ends with a verdict and a what-if table. Print 12 sheets and 12 documents, follow 12 checklists and send 34 ready messages.',
 'Payroll taxes, workers\' insurance, checks and credentials follow your own local rules; confirm with your adviser. The workbook holds dates, hours and amounts only.',
 'Why a workbook: one flat price, no per-caregiver fee, no price rise when you grow, and your data stays with you. No macros; it works in Excel and Google Sheets.',
 'Read the Recruiting KPI Dashboard and Charts every week with the recruiter, and use the Monthly Recruiting Review checklist.']
listing = {"title": "Home Care Agency Recruiting Excel Template: Applicant Funnel, Onboarding, Credential Renewals, Turnover, Hire Decision",
 "headline": "Hire, onboard and keep caregivers with one Excel file",
 "tags": ["home care agency", "caregiver hiring", "recruiting tracker", "onboarding checklist", "credential tracker", "turnover tracker", "excel template", "applicant tracker", "cost per hire", "caregiver retention", "hiring planner", "agency management", "renewal dates"],
 "description": ("Run recruiting, onboarding and renewals for a non-medical home care agency in one Excel workbook. Built for an owner-director, a part-time recruiter, a scheduler and field supervisors.\n\n"
  "Applicants records every applicant with source, phone screen, interview, offer and start, and works out days to first call, days to start and the stage reached. The Recruiting Funnel shows conversion at each step and applicants per start; Source by Month ranks each source by caregivers still active after 90 days and cost per start. "
  "Onboarding tracks five checks per caregiver with a Ready or Blocked flag for the first shift. Credentials and Renewals Due show days left with red, amber and green colours at 30 and 60 days (editable), and Visits After Expiry lists the visits that must move.\n\n"
  "Leavers, Turnover by Month, Hiring Cost Log, Training Sessions, Referral Bonuses and Hire Planning by Week give turnover against your flag, first-90-day leavers, cost per hire and hours waiting for a caregiver.\n\n"
  f"{len(tools)} decision tools answer weekly questions with a verdict and a what-if table: recruiting funnel, cost per hire, source ranking, days to start, ready for first shift, renewal countdown, cannot be scheduled after, turnover, replacement cost, hire-or-not decision, hire timing and payback. "
  f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages.\n\n"
  "This is part six of the Home Care Agency suite. A standard .xlsx workbook with no macros and no subscription, one flat price with no per-caregiver fee, a demo copy full of sample data and a blank copy. The workbook holds dates, hours and amounts only and does not promise results; no live app, no GPS and no automatic check-in."),
 "features": ["Applicant funnel with cost per hire and days to start", "Source ranking by 90-day retention", "Onboarding with a Ready or Blocked flag", "Credential renewals with 60 and 30-day colours", "Visits after expiry list", "Turnover by tenure and its cost",
              "Hire-or-not decision with payback", f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "One flat price, your data stays with you"]}
s = _lib.spec(id=f'{SUITE}-p6', slug='home-care-recruiting', profession='Home Care Agency Business', name='Recruiting, Onboarding and Renewals', tagline='Hire, onboard and keep caregivers with confidence',
              price_usd=29, colors={"primary": "#3A506B", "accent": "#E07A5F"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide, listing=listing, insights=insights,
              suite={"key": SUITE, "part": 6, "of": 8, "focus": "Recruiting, onboarding and credential renewals"}, signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    _lib.dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hc6.en.json'))
    print('tables', len(tables), 'rows', sum(len(t['demo']) for t in tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']), 'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'name', len(s['name']))
