"""HVAC and plumbing contractor suite - part 1: Calls, Dispatch and Jobs."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv1_lists import *
from hv1_tables import settings, tables
from hv1_tools import tools
import hv1_data as D

SUITE = 'fx-20261115-hvac-plumbing'
NOTE = "Sample wording: adapt it to your own business and check your local rules."
YES, NO = '{list:yesno.yes}', '{list:yesno.no}'
CANC, COMP, SCHED, PROG = tok('jobstatus', 'Cancelled'), tok('jobstatus', 'Completed'), tok('jobstatus', 'Scheduled'), tok('jobstatus', 'In progress')
APPL, APPR, INSP = tok('permitstatus', 'Applied'), tok('permitstatus', 'Approved'), tok('permitstatus', 'Inspection booked')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def F(*pairs): return [FV(a, b) for a, b in pairs]
def CN(cond): return 'COUNTIFS(%s)' % cond

forms = [
    FORM('call_log_sheet', 'Call Log Sheet', 'Call log entry', 'calls.call_id', F(
        ('Date', 'calls.date'), ('Time', 'calls.time'), ('Source', 'calls.source'), ('Call type', 'calls.call_type'), ('Outcome', 'calls.outcome'), ('Answered by', 'calls.answered_by'), ('Site', 'calls.site_id'),
        ('Site reference', 'calls.site_ref'), ('Caller phone', 'calls.caller_phone'), ('Estimated value', 'calls.est_value'), ('Booked, 1 or 0', 'calls.booked'), ('Lost value', 'calls.lost_value'), ('Job', 'calls.job_id'))),
    FORM('emergency_sheet', 'Emergency Call Sheet', 'Emergency call with the call-out fee', 'calls.call_id', F(
        ('Date', 'calls.date'), ('Hour of the call', 'calls.hour'), ('Call type', 'calls.call_type'), ('Emergency', 'calls.emergency'), ('Answered by', 'calls.answered_by'), ('Caller phone', 'calls.caller_phone'), ('Site reference', 'calls.site_ref'),
        ('Estimated value', 'calls.est_value'), ('Outcome', 'calls.outcome'), ('Job', 'calls.job_id')) + [FF('Call-out fee, diagnostic', '{set:diag_fee}', 'money'), FF('Emergency calls on this weekday, 90 days', 'COUNTIFS({range:calls.weekday},INDEX({range:calls.weekday},MATCH({pick},{range:calls.call_id},0)),{range:calls.emergency},%s)' % YES, 'int')]),
    FORM('booking_sheet', 'Booking Sheet', 'Booking with date, window and call-out fee', 'workorders.job_id', F(
        ('Date', 'workorders.date'), ('Arrival window', 'workorders.window'), ('Site reference', 'workorders.site_ref'), ('Area', 'workorders.area'), ('Customer phone', 'workorders.phone'), ('Job type', 'workorders.job_type'),
        ('Reason', 'workorders.reason'), ('Technician', 'workorders.technician'), ('Van', 'workorders.van'), ('Diagnostic fee', 'workorders.diag_fee'), ('Parts ready', 'workorders.parts_ready'), ('Permit needed', 'workorders.permit_needed'))),
    FORM('job_record_sheet', 'Job Record Sheet', 'Job record with price, cost and margin', 'jobs.job_id', F(
        ('Date', 'jobs.date'), ('Site reference', 'jobs.site_ref'), ('Area', 'jobs.area'), ('Job type', 'jobs.job_type'), ('Technician', 'jobs.technician'), ('Van', 'jobs.van'), ('Hours on site', 'jobs.hours'), ('Drive hours', 'jobs.drive_hours'),
        ('Price', 'jobs.price'), ('Cost', 'jobs.cost'), ('Status', 'jobs.status'), ('Repeat check', 'jobs.repeat'), ('Days since the last job at the site', 'jobs.days_since')) + [
        FF('Margin', 'INDEX({range:jobs.price},MATCH({pick},{range:jobs.job_id},0))-INDEX({range:jobs.cost},MATCH({pick},{range:jobs.job_id},0))', 'money'),
        FF('Margin percent', 'IFERROR(1-INDEX({range:jobs.cost},MATCH({pick},{range:jobs.job_id},0))/INDEX({range:jobs.price},MATCH({pick},{range:jobs.job_id},0)),0)', 'pct')]),
    FORM('work_order_sheet', 'Work Order Sheet', 'Work order with parts and permit status', 'jobs.job_id', F(
        ('Date', 'jobs.date'), ('Start', 'jobs.start'), ('Site reference', 'jobs.site_ref'), ('Area', 'jobs.area'), ('Equipment', 'jobs.equipment_id'), ('Job type', 'jobs.job_type'), ('Reason', 'jobs.reason'),
        ('Technician', 'jobs.technician'), ('Assistant', 'jobs.assistant'), ('Van', 'jobs.van'), ('Hours on site', 'jobs.hours'), ('Parts ready', 'jobs.parts_ready'), ('Permit needed', 'jobs.permit_needed')) + [
        FF('Hours with drive time', 'INDEX({range:jobs.hours},MATCH({pick},{range:jobs.job_id},0))+INDEX({range:jobs.drive_hours},MATCH({pick},{range:jobs.job_id},0))', 'num')]),
    FORM('dispatch_day_sheet', 'Dispatch Day Sheet', 'One technician day on the board', 'dispatch.row_id', F(
        ('Technician', 'dispatch.technician'), ('Van', 'dispatch.van'), ('Trade', 'dispatch.trade'), ('Date', 'dispatch.date'), ('Jobs', 'dispatch.jobs'), ('Booked hours', 'dispatch.booked_hours'), ('Drive hours', 'dispatch.drive_hours'),
        ('Free hours', 'dispatch.free_hours'), ('Jobs with no parts confirmed', 'dispatch.no_parts'), ('Day check', 'dispatch.flag'), ('Technician phone', 'dispatch.tech_phone'))),
    FORM('parts_needed_sheet', 'Parts Needed Sheet', 'Parts and equipment needed for one job', 'workorders.job_id', F(
        ('Job', 'workorders.job_id'), ('Date', 'workorders.date'), ('Site reference', 'workorders.site_ref'), ('Job type', 'workorders.job_type'), ('Technician', 'workorders.technician'), ('Van', 'workorders.van'),
        ('Equipment', 'workorders.equipment'), ('Parts ready', 'workorders.parts_ready'), ('Equipment supplier phone', 'workorders.supplier_phone'), ('Parts counter phone', 'workorders.parts_phone'))),
    FORM('permit_app_sheet', 'Permit Application Sheet', 'Permit application with dates and fee', 'permits.permit_id', F(
        ('Job', 'permits.job_id'), ('Site reference', 'permits.site_ref'), ('Job type', 'permits.job_type'), ('Technician', 'permits.technician'), ('Job date', 'permits.job_date'), ('Applied on', 'permits.applied_on'), ('Fee', 'permits.fee'),
        ('Status', 'permits.status'), ('Days waiting', 'permits.days_waiting'), ('Money held, job price', 'permits.job_price'))),
    FORM('inspection_sheet', 'Inspection Booking Sheet', 'Inspection booking with the days between steps', 'permits.permit_id', F(
        ('Permit', 'permits.permit_id'), ('Site reference', 'permits.site_ref'), ('Approved on', 'permits.approved_on'), ('Inspection on', 'permits.inspection_on'), ('Passed on', 'permits.passed_on'), ('Days to approve', 'permits.days_to_approve'),
        ('Days from approval to inspection', 'permits.days_to_inspect'), ('Status', 'permits.status'), ('Days held past the job date', 'permits.days_held'), ('Van cost waiting', 'permits.van_cost_waiting'), ('Customer phone', 'permits.phone'))),
    FORM('job_completion_sheet', 'Job Completion Sheet', 'Job completion with hours and status', 'jobs.job_id', F(
        ('Date', 'jobs.date'), ('Site reference', 'jobs.site_ref'), ('Job type', 'jobs.job_type'), ('Technician', 'jobs.technician'), ('Hours on site', 'jobs.hours'), ('Drive hours', 'jobs.drive_hours'), ('Equipment', 'jobs.equipment_id'),
        ('Status', 'jobs.status'), ('Parts ready', 'jobs.parts_ready'), ('Call', 'jobs.call_id'), ('Same-day job, 1 or 0', 'jobs.same_day'))),
    FORM('signature_sheet', 'Customer Signature Sheet', 'Customer signature page for one visit', 'workorders.job_id', F(
        ('Job', 'workorders.job_id'), ('Date', 'workorders.date'), ('Site reference', 'workorders.site_ref'), ('Area', 'workorders.area'), ('Job type', 'workorders.job_type'), ('Technician', 'workorders.technician'), ('Customer phone', 'workorders.phone'),
        ('Account', 'workorders.account'))),
    FORM('callback_flag_sheet', 'Callback Flag Sheet', 'Possible callback with cost against the earlier job'[:0] + 'Possible callback and its cost', 'repeats.job_id', F(
        ('Date', 'repeats.date'), ('Site reference', 'repeats.site_ref'), ('Job type', 'repeats.job_type'), ('Technician', 'repeats.technician'), ('Previous job', 'repeats.prev_job'), ('Previous job on', 'repeats.prev_date'),
        ('Technician of the earlier job', 'repeats.prev_technician'), ('Days between', 'repeats.days_between'), ('Cost of this visit', 'repeats.cost'), ('Earlier job price', 'repeats.prev_price'), ('Cost against earlier price', 'repeats.cost_share'), ('Flag', 'repeats.flag'))),
]
assert len(forms) == 12
SG = ['Contractor', 'Customer']
documents = [
    DOC('work_order_doc', 'Work Order', 'Work order with a customer signature line', 'jobs.job_id', [
        'Work order of {set:company}, dated {today}. Job {col:jobs.job_id} on {col:jobs.date}, start {col:jobs.start}. Site {col:jobs.site_ref} in {col:jobs.area}. Equipment record: {col:jobs.equipment_id}.',
        'Job type: {col:jobs.job_type}. Reason for the call: {col:jobs.reason}. Technician: {col:jobs.technician}, assistant: {col:jobs.assistant}, van: {col:jobs.van}. Hours planned on site: {col:jobs.hours}.',
        'Parts ready: {col:jobs.parts_ready}. Permit needed: {col:jobs.permit_needed}. Status: {col:jobs.status}.', 'Work done and the customer notes are written below. The customer signs to confirm the visit took place.'], SG, NOTE),
    DOC('booking_doc', 'Booking Confirmation', 'Booking confirmation for a customer', 'workorders.job_id', [
        'Booking confirmation of {set:company}, dated {today}. Site reference {col:workorders.site_ref}, {col:workorders.area}.', 'Your visit is booked for {col:workorders.date}, arrival window {col:workorders.window}. Job type: {col:workorders.job_type}. Technician: {col:workorders.technician}.',
        'The diagnostic fee, a fee for coming out to find the cause, is {col:workorders.diag_fee}. It is credited if you go ahead with the work. Prices are before sales tax.', 'Please reply if you need to move your visit.'], SG, NOTE),
    DOC('window_doc', 'Arrival Window Notice', 'Arrival window notice', 'workorders.job_id', [
        'Arrival window notice of {set:company}, dated {today}.', 'Site reference {col:workorders.site_ref}. Your technician {col:workorders.technician} arrives on {col:workorders.date} in the window {col:workorders.window}.',
        'The technician calls about {col:workorders.minutes} minutes before arrival. Please make sure someone can give access to the site.', 'Call {set:company} if the window does not suit you.'], ['Dispatcher'], NOTE),
    DOC('board_doc', 'Dispatch Board Printout', 'Dispatch board printout for one technician day', 'dispatch.row_id', [
        'Dispatch board of {set:company}, dated {today}. Technician {col:dispatch.technician}, van {col:dispatch.van}, date {col:dispatch.date}.', 'Jobs: {col:dispatch.jobs}. Booked hours: {col:dispatch.booked_hours}. Drive hours: {col:dispatch.drive_hours}. Free hours: {col:dispatch.free_hours}.',
        'Jobs with no parts confirmed: {col:dispatch.no_parts}. Day check: {col:dispatch.flag}.', 'Changes to the board are written below and told to the technician.'], ['Dispatcher', 'Technician'], NOTE),
    DOC('route_doc', 'Daily Route Sheet', 'Daily route sheet for a technician', 'workorders.job_id', [
        'Daily route sheet of {set:company}, dated {today}. Technician {col:workorders.technician}, van {col:workorders.van}.', 'Stop: job {col:workorders.job_id} at {col:workorders.site_ref} in {col:workorders.area} on {col:workorders.date}, window {col:workorders.window}.',
        'Job type: {col:workorders.job_type}. Drive time to the stop: about {col:workorders.minutes} minutes. Parts ready: {col:workorders.parts_ready}. Permit needed: {col:workorders.permit_needed}.', 'Arrival and finish times are written below for each stop.'], ['Technician', 'Dispatcher'], NOTE),
    DOC('parts_list_doc', 'Parts Needed List', 'Parts needed list for the supplier run', 'workorders.job_id', [
        'Parts needed list of {set:company}, dated {today}. Job {col:workorders.job_id} on {col:workorders.date}, site reference {col:workorders.site_ref}.', 'Job type: {col:workorders.job_type}. Equipment record: {col:workorders.equipment}. Technician: {col:workorders.technician}, van {col:workorders.van}. Parts ready: {col:workorders.parts_ready}.',
        'Equipment supplier phone: {col:workorders.supplier_phone}. Parts counter phone: {col:workorders.parts_phone}. The part lines and quantities are written below.', 'Mark each line when it is picked up.'], ['Dispatcher', 'Parts counter'], NOTE),
    DOC('permit_doc', 'Permit Tracking Sheet', 'Permit tracking sheet', 'permits.permit_id', [
        'Permit tracking sheet of {set:company}, dated {today}. Permit {col:permits.permit_id} for job {col:permits.job_id}, site reference {col:permits.site_ref}, {col:permits.job_type}.', 'Applied on {col:permits.applied_on}. Approved on {col:permits.approved_on}. Inspection on {col:permits.inspection_on}. Passed on {col:permits.passed_on}. Status: {col:permits.status}.',
        'Job date: {col:permits.job_date}. Days waiting: {col:permits.days_waiting}. Days held past the job date: {col:permits.days_held}. Van cost waiting: {col:permits.van_cost_waiting}. Fee: {col:permits.fee}.', 'Check your local rules for what each step needs. Notes are written below.'], ['Office', 'Technician'], NOTE),
    DOC('inspection_doc', 'Inspection Day Notice', 'Inspection day notice', 'permits.permit_id', [
        'Inspection day notice of {set:company}, dated {today}. Site reference {col:permits.site_ref}, job {col:permits.job_id}.', 'The inspection is booked for {col:permits.inspection_on}. Technician: {col:permits.technician}. Please make sure someone can give access to the site.',
        'Permit {col:permits.permit_id} was approved on {col:permits.approved_on}. Status: {col:permits.status}. Check your local rules for what the inspection needs.', 'The result and the date are written below.'], ['Office', 'Customer'], NOTE),
    DOC('completion_doc', 'Job Completion Note', 'Job completion note with a signature line', 'jobs.job_id', [
        'Job completion note of {set:company}, dated {today}. Job {col:jobs.job_id} on {col:jobs.date}, site reference {col:jobs.site_ref}, {col:jobs.area}.', 'Job type: {col:jobs.job_type}. Technician: {col:jobs.technician}. Hours on site: {col:jobs.hours}. Drive hours: {col:jobs.drive_hours}. Status: {col:jobs.status}.',
        'Price of the job: {col:jobs.price}, before sales tax. Equipment record: {col:jobs.equipment_id}.', 'The work done and any follow-up visit are written below. The customer signs to confirm the visit.'], SG, NOTE),
    DOC('price_notice_doc', 'Emergency Price Notice', 'Emergency call price notice', 'calls.call_id', [
        'Emergency call price notice of {set:company}, dated {today}. Call {col:calls.call_id} on {col:calls.date} at {col:calls.time}, call type {col:calls.call_type}.', 'The diagnostic fee, a fee for coming out to find the cause, is {set:diag_fee}. It is credited if you go ahead with the work. Check the current price before you quote it.',
        'After-hours terms and the price of the work are told before the visit starts. Prices are before sales tax.', 'The customer confirms the fee below.'], SG, NOTE),
    DOC('callback_doc', 'Callback Record', 'Callback record with the original job and its cost', 'repeats.job_id', [
        'Callback record of {set:company}, dated {today}. Job {col:repeats.job_id} on {col:repeats.date}, site reference {col:repeats.site_ref}, {col:repeats.job_type}. Technician: {col:repeats.technician}.',
        'The earlier job at the site was {col:repeats.prev_job} on {col:repeats.prev_date}, {col:repeats.days_between} days before. Technician of the earlier job: {col:repeats.prev_technician}. Flag: {col:repeats.flag}.',
        'Cost of this visit: {col:repeats.cost}. Price of the earlier job: {col:repeats.prev_price}. Cost against the earlier price: {col:repeats.cost_share}.', 'The reason for the second visit and who follows up are written below.'], ['Owner', 'Technician'], NOTE),
    DOC('weekly_doc', 'Call Log Weekly Summary', 'Call log summary for one month', 'calls_month.month', [
        'Call log summary of {set:company}, dated {today}. Month starting {col:calls_month.month}.', 'Calls: {col:calls_month.calls}. Booked: {col:calls_month.booked}. Booking rate: {col:calls_month.booking_rate}. Emergency calls: {col:calls_month.emergency_calls}.',
        'Estimated value of unbooked calls: {col:calls_month.lost_value}. Jobs: {col:calls_month.jobs}. Possible callbacks: {col:calls_month.possible_callbacks}.', 'Actions for the next review are written below.'], ['Owner', 'Office manager'], NOTE),
]
assert len(documents) == 12
def S(*st): return list(st)
checklists = [
    CHK('answer_call', 'Answering a New Call', 'calls', 'calls.date', [('Answer inside three rings and say the company name', 0), ('Ask for the site reference or the phone number', 0), ('Ask what the problem is and whether it is an emergency', 0), ('Offer the first slot that fits the board', 0), ('Tell the customer the call-out fee', 0), ('Confirm the date, window and phone number', 0), ('Write the call in the log with the source', 0)]),
    CHK('emergency_call', 'Emergency Call', 'calls', 'calls.date', [('Log the call and the time', 0), ('Check the reserve hours on the board', 0), ('Pick the technician with the most free hours', 0), ('Tell the customer the call-out fee and the arrival window', 0), ('Text the technician the site reference', 0), ('Confirm someone will be at the site', 0), ('Record the outcome of the call', 1)]),
    CHK('book_job', 'Booking a Job', 'jobs', 'jobs.date', [('Check the capacity of the day', -3), ('Check parts and equipment', -3), ('Check whether a permit is needed and apply', -3), ('Confirm the window with the customer', -2), ('Add the job to the dispatch board', -2), ('Send the booking confirmation', -2)]),
    CHK('daily_plan', 'Daily Dispatch Plan', 'dispatch', 'dispatch.date', [('Open the board for the day', -1), ('Check jobs with no parts confirmed', -1), ('Check hours against capacity for each technician', -1), ('Group jobs by area to cut drive time', -1), ('Send each technician the route', -1), ('Keep the emergency reserve free', 0)]),
    CHK('day_before', 'Day Before the Job', 'jobs', 'jobs.date', [('Send the reminder text', -1), ('Confirm someone will be at the site', -1), ('Check parts on the van', -1), ('Check the permit status', -1), ('Print the work order', -1), ('Tell the apprentice who they ride with', -1)]),
    CHK('parts_tomorrow', 'Parts Ready for Tomorrow', 'jobs', 'jobs.date', [('List jobs with no parts confirmed', -2), ('Order from the equipment supplier or the parts counter', -2), ('Confirm the pick-up time', -1), ('Load the van', -1), ('Tick the parts on the work order', -1), ('Move the job if parts will not arrive', -1)]),
    CHK('arrive_site', 'Arriving at a Site', 'jobs', 'jobs.date', [('Text the customer when on the way', 0), ('Greet the customer and check the work order', 0), ('Confirm the reason for the visit', 0), ('Tell the customer the price before work starts', 0), ('Record the start time', 0)]),
    CHK('job_closed', 'Job Closed and Paid', 'jobs', 'jobs.date', [('Record hours, parts and notes', 0), ('Get the customer signature', 0), ('Mark the job completed on the board', 0), ('Send the invoice', 1), ('Record the payment or the promised date', 3), ('Ask for a review', 5)]),
    CHK('permit_applied', 'Permit Applied', 'permits', 'permits.applied_on', [('Write the permit in the log', 0), ('Note the job date and the van', 0), ('Check the status every two days', 2), ('Chase when the wait passes your average', 7), ('Move the van if the job date is at risk', 10)]),
    CHK('inspection_booked', 'Inspection Booked', 'permits', 'permits.job_date', [('Record the inspection date', -7), ('Tell the customer the date', -5), ('Tell the technician', -3), ('Confirm access to the site', -1), ('Write the result in the log', 1)]),
    CHK('missed_review', 'Weekly Missed-Call Review', 'calls', 'calls.date', [('Open the Missed Call Ranker', 0), ('Call back the top calls by value', 1), ('Note why calls were missed', 2), ('Check after-hours coverage', 3), ('Update the log with the outcomes', 4)]),
    CHK('monday_meeting', 'Monday Dispatch Meeting', 'jobs_week', 'jobs_week.week', [('Read last week jobs and cancellations', 0), ('Read the week board for over-capacity days', 0), ('List jobs with no parts confirmed', 0), ('List permits waiting', 0), ('Check the call volume forecast', 0), ('Agree who covers emergencies', 0)]),
]
assert len(checklists) == 12
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
W = 'workorders'
messages = [
    M('c_book', 'Customer: your job is booked', W, 'workorders.phone', 'Hello, thank you for calling {company}. Your {job_type} visit at {site_ref} is booked for {date}, window {window}.'),
    M('c_remind', 'Customer: technician arrives tomorrow', W, 'workorders.phone', 'Hello, reminder from {company}: {technician} arrives {date}, window {window}, for {job_type} at {site_ref}.'),
    M('c_way', 'Customer: your technician is on the way', W, 'workorders.phone', 'Hello, {technician} from {company} is on the way to {site_ref}, about {minutes} minutes.'),
    M('c_late', 'Customer: we are running late', W, 'workorders.phone', 'Hello, {company} is running late for {site_ref}. {technician} now arrives in the window {window} on {date}. Sorry for the wait.'),
    M('c_confirm', 'Customer: please confirm access', W, 'workorders.phone', 'Hello, {company} needs to confirm someone will be at {site_ref} on {date}, window {window}. Please reply yes.'),
    M('c_parts', 'Customer: the visit needs parts', W, 'workorders.phone', 'Hello, your {job_type} visit at {site_ref} needs parts. {company} booked the next visit for {date}, window {window}.'),
    M('c_permit', 'Customer: the permit is approved', 'permits', 'permits.phone', 'Hello, the permit for your job at {site_ref} is approved. The job date is {job_date}. {company}'),
    M('c_inspect', 'Customer: the inspection is booked', 'permits', 'permits.phone', 'Hello, the inspection for your job at {site_ref} is booked for {inspection_on}. Please make sure someone can give access. {company}'),
    M('c_done', 'Customer: your job is complete', W, 'workorders.phone', 'Hello, your {job_type} job at {site_ref} is complete. Thank you for choosing {company}.'),
    M('c_missed', 'Customer: sorry we missed your call', 'calls', 'calls.caller_phone', 'Hello, sorry we missed your call on {date}. This is {company}. Can we call you back today?'),
    M('c_fee', 'Customer: the call-out fee', W, 'workorders.phone', 'Hello, the call-out fee for your visit on {date} is {diag_fee}. It is credited if you go ahead with the work. {company}'),
    M('c_cancel', 'Customer: a cancellation opened a visit', W, 'workorders.phone', 'Hello, a cancellation opened a visit on {date}, window {window}. Reply to {company} if you want it.'),
    M('c_move', 'Customer: reply to move your visit', W, 'workorders.phone', 'Hello, please reply to {company} if you need to move your visit on {date} at {site_ref}.'),
    M('l_new', 'Landlord account: new job, contact', W, 'workorders.phone', 'Hello, {company} has a new job at {site_ref} (account {account}) on {date}: {job_type}. Who should we contact for access?'),
    M('l_done', 'Landlord account: job complete', W, 'workorders.phone', 'Hello, the {job_type} job at {site_ref} (account {account}) is complete. {company}'),
    M('l_access', 'Landlord account: access needed', W, 'workorders.phone', 'Hello, {company} needs access to {site_ref} on {date}, window {window}. Please confirm who will open the site.'),
    M('t_tomorrow', 'Technician: your jobs for tomorrow', W, 'workorders.tech_phone', 'Hello {technician}, your jobs for {date} start at {site_ref}, window {window}. {company}'),
    M('t_added', 'Technician: a job was added today', W, 'workorders.tech_phone', 'Hello {technician}, a job was added today at {site_ref}: {job_type}, window {window}. {company}'),
    M('t_parts', 'Technician: parts are not confirmed', W, 'workorders.tech_phone', 'Hello {technician}, parts for {job_type} at {site_ref} on {date} are not confirmed. Please check with the office. {company}'),
    M('t_permit', 'Technician: the permit is waiting', 'permits', 'permits.tech_phone', 'Hello {technician}, the permit for {site_ref} is still waiting. Please wait for the office before you start. {company}'),
    M('t_orders', 'Technician: complete your work orders', 'dispatch', 'dispatch.tech_phone', 'Hello {technician}, please complete your work orders for {date}. {company}'),
    M('t_board', 'Technician: the board changed', 'dispatch', 'dispatch.tech_phone', 'Hello {technician}, the board changed for {date}. Please check your route. {company}'),
    M('a_ride', 'Apprentice: you ride with a technician', W, 'workorders.assistant_phone', 'Hello {assistant}, you ride with {technician} on {date}, first stop {site_ref}, window {window}. {company}'),
    M('om_calls', 'Office manager: call still not booked', 'calls', 'calls.office_phone', 'Call {call_id} of {date} is still not booked. Estimated value {est_value}. Please call back. {company}'),
    M('om_parts', 'Office manager: no parts confirmed', W, 'workorders.office_phone', 'Job {job_id} at {site_ref} on {date} has no parts confirmed. Please check the order. {company}'),
    M('om_permits', 'Office manager: permit waiting too long', 'permits', 'permits.office_phone', 'The permit at {site_ref} has waited {days_waiting} days. Please chase it today. {company}'),
    M('ow_rate', 'Owner: the booking rate', 'calls_month', 'calls_month.owner_phone', 'Booking rate for the month of {month}: {booking_rate}, {booked} booked of {calls} calls. {company}'),
    M('ow_van', 'Owner: a van is waiting on a permit', 'permits', 'permits.owner_phone', 'A van is waiting on the permit at {site_ref}: {days_held} days past the job date, cost so far {van_cost_waiting}. {company}'),
    M('ow_callback', 'Owner: possible callback to review', 'jobs', 'jobs.owner_phone', 'Possible callback at {site_ref}: job {job_id} on {date} came {days_since} days after the last job. Please review. {company}'),
    M('s_equip', 'Equipment supplier: confirm equipment', W, 'workorders.supplier_phone', 'Hello, please confirm the equipment for {job_type} on {date} at {site_ref}, job {job_id}. {company}'),
    M('p_parts', 'Parts counter: order for the morning run', W, 'workorders.parts_phone', 'Hello, order for the morning run: parts for {job_type} on {date}, job {job_id}. {company}'),
    M('e_elec', 'Electrical subcontractor: confirm date', W, 'workorders.elec_phone', 'Hello, please confirm {date} at {site_ref} for the electrical work, job {job_id}. {company}'),
    M('sm_sheet', 'Sheet-metal sub: measurements ready', W, 'workorders.sheet_phone', 'Hello, the site measurements for {site_ref} are ready for job {job_id}. Please call {company} to arrange pick-up.'),
    M('ac_week', 'Accountant: the weekly job list is ready', 'jobs_week', 'jobs_week.acct_phone', 'Hello, the job list for the week of {week} is ready: {completed} jobs completed, {cancelled} cancelled. {company}'),
]
assert len(messages) == 34, len(messages)

def CW(n): return '{range:calls.date},">="&({today}-%d),{range:calls.date},"<="&{today}' % n
def JW(n): return '{range:jobs.date},">="&({today}-%d),{range:jobs.date},"<="&{today}' % n
NXT7 = '{range:jobs.date},">"&{today},{range:jobs.date},"<="&({today}+7)'
CAP7 = '{range:capacity.date},">"&{today},{range:capacity.date},"<="&({today}+7)'
MON = '({today}-WEEKDAY({today},2)+1)'
POSS = ck('Possible callback')
kpis = [
    KPI('Calls this month', 'COUNTIFS({range:calls.date},">="&%s,{range:calls.date},"<="&{today})' % MS, 'int'),
    KPI('Calls, last 30 days', CN(CW(30)), 'int'),
    KPI('Booking rate, last 90 days', 'IFERROR(SUMIFS({range:calls.booked},%s)/COUNTIFS(%s),0)' % (CW(90), CW(90)), 'pct'),
    KPI('Booking rate this month', 'IFERROR(SUMIFS({range:calls.booked},{range:calls.date},">="&%s,{range:calls.date},"<="&{today})/COUNTIFS({range:calls.date},">="&%s,{range:calls.date},"<="&{today}),0)' % (MS, MS), 'pct'),
    KPI('Calls not booked, last 30 days', 'COUNTIFS({range:calls.booked},0,%s)' % CW(30), 'int'),
    KPI('Unbooked call value, last 30 days', 'SUMIFS({range:calls.lost_value},%s)' % CW(30), 'money'),
    KPI('Missed calls, last 7 days', 'COUNTIFS({range:calls.outcome},%s,%s)' % (tok('calloutcome', 'Missed call'), CW(7)), 'int'),
    KPI('Emergency calls this month', 'COUNTIFS({range:calls.emergency},%s,{range:calls.date},">="&%s,{range:calls.date},"<="&{today})' % (YES, MS), 'int'),
    KPI('Emergency calls, last 30 days', 'COUNTIFS({range:calls.emergency},%s,%s)' % (YES, CW(30)), 'int'),
    KPI('Calls answered by a person, last 90 days', 'IFERROR(1-COUNTIFS({range:calls.answered_by},%s,%s)/COUNTIFS(%s),0)' % (tok('answeredby', 'After-hours line'), CW(90), CW(90)), 'pct'),
    KPI('Jobs booked this week', 'COUNTIFS({range:jobs.date},">="&%s,{range:jobs.date},"<="&(%s+6),{range:jobs.status},"<>"&%s)' % (MON, MON, CANC), 'int'),
    KPI('Jobs booked, next 7 days', 'COUNTIFS(%s,{range:jobs.status},"<>"&%s)' % (NXT7, CANC), 'int'),
    KPI('Jobs completed this month', 'COUNTIFS({range:jobs.status},%s,{range:jobs.date},">="&%s,{range:jobs.date},"<="&{today})' % (COMP, MS), 'int'),
    KPI('Jobs completed, last 30 days', 'COUNTIFS({range:jobs.status},%s,%s)' % (COMP, JW(30)), 'int'),
    KPI('Jobs waiting for parts', 'COUNTIFS({range:jobs.parts_ready},%s,{range:jobs.status},%s)+COUNTIFS({range:jobs.parts_ready},%s,{range:jobs.status},%s)' % (NO, SCHED, NO, PROG), 'int'),
    KPI('Jobs with no parts, next 7 days', 'COUNTIFS({range:jobs.parts_ready},%s,{range:jobs.status},%s,%s)' % (NO, SCHED, NXT7), 'int'),
    KPI('Booked hours, next 7 days', 'SUMIFS({range:capacity.hours_booked},%s)' % CAP7, 'num'),
    KPI('Free hours, next 7 days', 'SUMIFS({range:capacity.free_hours},%s)' % CAP7, 'num'),
    KPI('Capacity used, next 7 days', 'IFERROR(SUMIFS({range:capacity.hours_booked},%s)/SUMIFS({range:capacity.hours_available},%s),0)' % (CAP7, CAP7), 'pct'),
    KPI('Technician days over capacity, 14 days', 'COUNTIFS({range:dispatch.flag},%s,{range:dispatch.date},">="&{today},{range:dispatch.date},"<="&({today}+14))' % ck('Over capacity'), 'int'),
    KPI('Average drive hours a job, last 30 days', 'IFERROR(AVERAGEIFS({range:jobs.drive_hours},%s,{range:jobs.status},"<>"&%s),0)' % (JW(30), CANC), 'num'),
    KPI('Permits waiting for approval', 'COUNTIFS({range:permits.status},%s)' % APPL, 'int'),
    KPI('Permits waiting for inspection', 'COUNTIFS({range:permits.status},%s)+COUNTIFS({range:permits.status},%s)' % (APPR, INSP), 'int'),
    KPI('Days to approve a permit, 12 months', 'IFERROR(AVERAGEIFS({range:permits.days_to_approve},{range:permits.applied_on},">="&({today}-365)),0)', 'num'),
    KPI('Jobs held by a permit', 'COUNTIFS({range:permits.days_held},">0")', 'int'),
    KPI('Van cost waiting, month to date', 'SUMIFS({range:permits.van_cost_waiting},{range:permits.job_date},">="&%s)' % MS, 'money'),
    KPI('Possible callbacks, last 30 days', 'COUNTIFS({range:jobs.repeat},%s,%s)' % (POSS, JW(30)), 'int'),
    KPI('Possible callbacks over jobs, 90 days', 'IFERROR(COUNTIFS({range:jobs.repeat},%s,%s)/COUNTIFS({range:jobs.status},"<>"&%s,%s),0)' % (POSS, JW(90), CANC, JW(90)), 'pct'),
    KPI('Cancellation rate, last 90 days', 'IFERROR(COUNTIFS({range:jobs.status},%s,%s)/COUNTIFS(%s),0)' % (CANC, JW(90), JW(90)), 'pct'),
    KPI('Same-day jobs, last 30 days', 'SUMIFS({range:jobs.same_day},%s)' % JW(30), 'int'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Calls and Dispatch Dashboard", "kpis": kpis,
    "monthly": {"title": "Calls, booked calls and jobs by month", "date": "calls_month.month", "series": [
        {"label": "Calls", "sum": "calls_month.calls", "date": "calls_month.month"}, {"label": "Booked calls", "sum": "calls_month.booked", "date": "calls_month.month"}, {"label": "Jobs", "sum": "calls_month.jobs", "date": "calls_month.month"}]},
    "breakdowns": [{"title": "Calls by source", "by": "calls.source", "value": "calls.est_value", "agg": "count"}, {"title": "Calls by outcome", "by": "calls.outcome", "value": "calls.est_value", "agg": "count"},
                   {"title": "Jobs by technician", "by": "jobs.technician", "value": "jobs.price", "agg": "count"}, {"title": "Permits by status", "by": "permits.status", "value": "permits.fee", "agg": "count"}]}
NCJ = ('status', '<>', CANC)
def CM(title, typ, col, label, agg='sum'): return CHART(title, typ, 'month', [AGG(agg, 'calls_month', 'calls_month.' + col, date='calls_month.month', label=label)])
def CNT(title, tbl, col, where=None, label=None): return CHART(title, 'bar', '%s.%s' % (tbl, col), [AGG('count', tbl, where=where, label=label or title.split(' by ')[0])])
insights = {"filters": [{"label": "Technician", "list": "tech"}, {"label": "Area", "list": "area"}, {"label": "Source", "list": "source"}],
    "gauges": [{"title": "Booking rate against the target", "num": AGG('sum', 'calls', 'calls.booked'), "den": AGG('count', 'calls')},
               {"title": "Calls answered by a person", "num": AGG('count', 'calls', where=[('answered_by', '<>', tok('answeredby', 'After-hours line'))]), "den": AGG('count', 'calls')},
               {"title": "Open jobs with parts ready", "num": AGG('count', 'jobs', where=[('status', '=', SCHED), ('parts_ready', '=', YES)]), "den": AGG('count', 'jobs', where=[('status', '=', SCHED)])},
               {"title": "Capacity used, next 30 days", "num": AGG('sum', 'capacity', 'capacity.hours_booked', where=[('date', '>', '{today}')]), "den": AGG('sum', 'capacity', 'capacity.hours_available', where=[('date', '>', '{today}')])},
               {"title": "Permits approved on time", "num": AGG('count', 'permits', where=[('days_to_approve', '<=', '{set:permit_ok_days}')]), "den": AGG('count', 'permits', where=[('days_to_approve', '>=', 0)])},
               {"title": "Jobs without a repeat visit", "num": AGG('count', 'jobs', where=[NCJ, ('repeat', '<>', POSS)]), "den": AGG('count', 'jobs', where=[NCJ])}],
    "charts": [
        CM('Calls per month', 'column', 'calls', 'Calls'), CNT('Calls by source', 'calls', 'source'), CNT('Calls by call type', 'calls', 'call_type'), CNT('Calls by outcome', 'calls', 'outcome'), CNT('Calls by weekday', 'calls', 'weekday'),
        CNT('Calls by who answered', 'calls', 'answered_by'), CM('Booking rate per month', 'column', 'booking_rate', 'Booking rate', 'avg'), CM('Unbooked call value per month', 'column', 'lost_value', 'Unbooked call value'),
        CM('Emergency calls per month', 'column', 'emergency_calls', 'Emergency calls'), CM('Jobs per month', 'column', 'jobs', 'Jobs'), CNT('Jobs by job type', 'jobs', 'job_type', [NCJ]), CNT('Jobs by status', 'jobs', 'status'),
        CNT('Jobs by technician', 'jobs', 'technician', [NCJ]), CNT('Jobs by van', 'jobs', 'van', [NCJ]), CNT('Jobs by area', 'jobs', 'area', [NCJ]), CNT('Jobs by site type', 'jobs', 'site_type', [NCJ]),
        CNT('Jobs by weekday', 'jobs', 'weekday', [NCJ]), CM('Drive hours per month', 'column', 'drive_hours', 'Drive hours'), CNT('Permits by status', 'permits', 'status'),
        CHART('Permits per month', 'column', 'month', [AGG('count', 'permits', date='permits.applied_on', label='Permits applied')]),
        CHART('Days waiting for a permit by job type', 'bar', 'permit_wait.job_type', [AGG('avg', 'permit_wait', 'permit_wait.avg_approve', label='Average days to approve')]),
        CM('Possible callbacks per month', 'column', 'possible_callbacks', 'Possible callbacks')]}
assert len(insights['charts']) == 22
signature = [
    {"name": "Booking Rate Analyzer", "why": "booking rate by lead source and by who answered, with the value of unbooked calls and a verdict against your target", "where": "Booking Rate Analyzer"},
    {"name": "Missed Call Ranker", "why": "the ten unbooked calls ranked by estimated job value and age, with the money on the table and a call-back date", "where": "Missed Call Ranker"},
    {"name": "Weekly Dispatch Board", "why": "every technician and day with booked and drive hours, free hours, over-capacity and no-parts flags and a green, amber or red verdict", "where": "Dispatch Board"},
    {"name": "Work Order Builder", "why": "a job record becomes a work order with a customer-signature line and a check that lists what is missing before you print", "where": "Work Order Builder"},
    {"name": "Permit and Inspection Tracker", "why": "open permits ranked by days waiting and money held against your own average wait, with a chase-today verdict", "where": "Permit and Inspection Tracker"},
    {"name": "Van Waiting Cost", "why": "what a van and technician cost for each day they wait on a permit or parts, and which job to move first", "where": "Van Waiting Cost"},
    {"name": "Repeat-Visit Flag", "why": "a second job at the same site inside your repeat window is flagged as a possible callback, with the earlier technician and the cost", "where": "Repeat Visits"},
    {"name": "Capacity Check for a New Job", "why": "the first of the next 10 working days with room for a job, drive time included, or the day to offer when there is none", "where": "Capacity Check for a New Job"},
    {"name": "Call Volume Forecast", "why": "calls, jobs and technician hours for the next 8 weeks from your own last months and the season, with best and worst rows", "where": "Call Volume Forecast"},
    {"name": "Jobs-a-Week Break-Even Solver", "why": "the jobs a week that cover your fixed cost and your owner draw, with a sensitivity at minus and plus 10 percent", "where": "Jobs-a-Week Break-Even"}]
competitors = [
    {"what": "field-service app with a per-technician fee", "lacks": "charges every month for each person, hides how a booking rate or a callback is worked out and does not rank unbooked calls by value or permits by money held"},
    {"what": "generic invoice template", "lacks": "writes a bill but has no call log, no dispatch board, no capacity check and no permit tracking"},
    {"what": "single-sheet quote calculator", "lacks": "prices one job but cannot show booking rate by source, jobs by technician and day or the cost of a van waiting"},
    {"what": "pen-and-paper job book", "lacks": "keeps no call history, so missed calls, repeat visits and busy weekdays never show up"}]
guide = [
    'Open Start and type your company name and your own limits in the yellow cells: booking rate wanted, repeat days, diagnostic fee, hours in a technician day and the costs of a technician and a van.',
    'Check Technicians, Vans, Job Types, Call Types, Call Outcomes and Lead Sources. They hold your people, vans and the lists the other sheets look up.',
    'Log every call on Calls with its source, call type, outcome and who answered. The booked flag, the lost value and the act-first score fill in by themselves.',
    'Enter each job on Jobs with the technician, van, hours, price, status and whether parts are confirmed. The days since the last job at the site and the possible-callback flag calculate themselves.',
    'Open Dispatch Board to see each technician and day: jobs, booked and drive hours, free hours and the day check. Open Capacity by Day for the next 30 days.',
    'Write each permit on Permit Log with its dates. Days waiting, days held past the job date and the van cost waiting fill in. Permit Wait shows your own average by job type.',
    'Type the job numbers of the coming days on Work Orders. The date, window, site reference, parts and permit status and the phones for the texts fill in.',
    'Fill Booking by Source, Booking by Answerer, Missed Calls by Weekday and Calls by Month from your call log each month. The booking rates calculate themselves.',
    f'Use the {len(tools)} tools: each answers one question with a verdict. Change the yellow inputs to try another source, week, job or permit.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Calls and Dispatch Dashboard and the Charts every week. A one-person owner-operator with one van uses the same sheets; a shop with a dispatcher uses the dispatcher columns.']
listing = {"title": "HVAC and Plumbing Contractor Excel Template: Call Log, Dispatch Board, Work Orders, Permit Tracker, Booking Rate, Capacity",
    "headline": "From the first call to the closed job: calls, dispatch, work orders and permits",
    "tags": ["hvac template", "plumbing template", "dispatch board", "work order template", "call log", "contractor excel", "service business", "permit tracker", "booking rate", "job tracker", "van schedule", "field service", "tradesman"],
    "description": ("Run the front half of an HVAC and plumbing contractor business in one Excel workbook. Built for an owner-run residential and light-commercial service shop with 1 to 15 technicians, an office manager who also dispatches, and a van for each lead technician. "
        "A one-person owner-operator with one van uses the same sheets; a shop with a dispatcher uses the dispatcher columns.\n\n"
        "The Calls sheet logs every call with its source, call type, outcome and who answered, and works out the booked flag, the estimated value of unbooked calls and the order in which to call people back. Booking by Source, Booking by Answerer, Missed Calls by Weekday and Calls by Month show your booking rate against the target you set. "
        "Jobs holds every job with technician, van, hours, price, status and parts. A second job at the same site inside your repeat window is flagged as a possible callback. The Dispatch Board and Capacity by Day show booked and drive hours, free hours and over-capacity days for each technician.\n\n"
        f"The Permit Log tracks applied, approved, inspection booked and passed with days waiting and the cost of a van held past its job date. {len(tools)} tools answer weekly questions with a clear verdict: booking rate by source, the missed call ranker, the dispatch board, a capacity check for a new job, a same-day slotter, the permit tracker, van waiting cost, a call volume forecast and a jobs-a-week break-even solver. "
        f"Print {len(forms)} sheets and {len(documents)} documents such as the work order with a signature line, follow {len(checklists)} checklists and send {len(messages)} ready text messages to customers, landlord accounts, technicians, the office, your equipment supplier and the accountant.\n\n"
        "This is part one of the HVAC and Plumbing Contractor suite. A standard .xlsx workbook with no macros and no per-technician fee: you keep your data. A demo copy full of sample data and a blank copy are included. It helps you keep track of your business and does not promise results."),
    "features": ["Call log with booking rate by source and by who answered", "Missed call ranker by estimated job value", "Dispatch board by technician and day", "Capacity check and same-day job slotter", "Work orders with a customer-signature line",
                 "Permit and inspection tracker with van waiting cost", "Repeat-visit and possible-callback flag", "Call volume forecast and jobs-a-week break-even", f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
for _l in ('Spare label',):
    if len(CKL) % 30 == 1: ck(_l)
HINTS = {
 'call_ranker': 'The ten-call act-first list: unbooked calls ranked by estimated value and age, the money on the table and a call-back date. Type the days allowed and the share you expect to win back.',
 'after_hours': 'From your call log of 90 days: emergency calls by weekday, after-hours calls nobody answered and their value. Type the monthly cost of an answering service and the share it would book.',
 'call_conversion': 'Pick a call type and the days back: calls, booked calls, jobs done, value booked and lost, and whether this type loses the most. The what-if rows walk through every type.',
 'dispatch_week': 'Type the Monday of a week: for each day the jobs, free hours and a green, amber or red verdict from the Dispatch Board, plus the week totals.',
 'work_order_check': 'Type a job number: the work order fields and a check of what is missing (equipment, parts, permit, phone) before you print the order with its signature line.',
 'same_day_slotter': 'Type the trade, hours and area of an urgent call: the technicians of that trade ranked by free hours today, the drive time and a send-today or next-day verdict.',
 'permit_tracker': 'Type the days over your average wait that you allow: open permits, your average wait, the permits to chase today and the open permits ranked by days waiting and money held.',
 'repeat_flag': 'Type a job number: the previous job at the site, the days between, the earlier technician and the cost against the earlier price, flagged against your repeat window.',
 'second_visit_rate': 'Pick a site type and a job type: the share of jobs with a second visit inside your repeat window, every site type ranked and a comparison with the last 12 months.',
 'call_forecast': 'From your last three full months and the same months last year: seasonal index, calls, jobs and hours for 8 weeks with base, best and worst rows and a capacity verdict.',
 'jobs_break_even': 'Type fixed cost, owner draw, margin per job and jobs a week now: the jobs needed to cover both, the cushion and a verdict, with rows at minus and plus 10 percent.'}
for _t in tools:
    if _t['key'] in HINTS: _t['hint'] = HINTS[_t['key']]
    if _t['key'] == 'second_visit_rate': _t['title'] = 'Second-visit rate by site type and job type'
s_ = None
s = spec(id=f'{SUITE}-p1', slug='hvac-plumbing-calls-dispatch', profession='HVAC and Plumbing Contractor', name='Calls, Dispatch and Jobs',
         tagline='From the first call to the closed job: calls, dispatch, work orders and permits', price_usd=29,
         colors={"primary": "#1F4E5F", "accent": "#E07A3F"}, settings=settings, lists=base_lists + ck_lists(), tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 1, "of": 8, "focus": "Calls, dispatch and jobs"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hv1.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'lists', len(s['lists']))
