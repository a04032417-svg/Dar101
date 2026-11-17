"""HVAC and plumbing contractor suite - part 3: Job Costing, Margin and Callbacks."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv3_lists import *
from hv3_tables import settings, tables
from hv3_tools import tools

SUITE = 'fx-20261115-hvac-plumbing'
NOTE = "Sample wording: adapt it to your own business and check your own local rules."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def FFm(label, f, fmt): return FF(label, f, fmt)

forms = [
    FORM('job_costing_sheet', 'Job Costing Sheet', 'Job costing with every cost line and the verdict', 'jobs.job_id', F(
        ('Date', 'jobs.date'), ('Site reference', 'jobs.site_ref'), ('Job type', 'jobs.job_type'), ('Technician', 'jobs.technician'), ('Van', 'jobs.van'), ('Price', 'jobs.price'), ('Parts cost', 'jobs.parts_cost'),
        ('Labour cost', 'jobs.labour_cost'), ('Permit fee', 'jobs.permit_fee'), ('Disposal', 'jobs.disposal'), ('Subcontract cost', 'jobs.sub_cost'), ('Vehicle cost', 'jobs.vehicle_cost'), ('Total cost', 'jobs.total_cost'),
        ('Margin', 'jobs.margin'), ('Margin percent', 'jobs.margin_pct'), ('Verdict', 'jobs.cause'))),
    FORM('time_sheet', 'Job Time Sheet', 'Hours on site, helper and drive hours', 'jobs.job_id', F(
        ('Date', 'jobs.date'), ('Job type', 'jobs.job_type'), ('Technician', 'jobs.technician'), ('Hours on site', 'jobs.hours'), ('Assistant hours', 'jobs.assistant_hours'), ('Drive hours', 'jobs.drive_hours'),
        ('Hours in the price book', 'jobs.book_hours'), ('Hours over the book', 'jobs.hours_over'), ('Labour cost', 'jobs.labour_cost'), ('Entry check', 'jobs.entry_flag')) + [
        FF('Total hours on the job', 'IFERROR(INDEX({range:jobs.hours},MATCH({pick},{range:jobs.job_id},0))+INDEX({range:jobs.assistant_hours},MATCH({pick},{range:jobs.job_id},0))+INDEX({range:jobs.drive_hours},MATCH({pick},{range:jobs.job_id},0)),0)', 'num')]),
    FORM('parts_sheet', 'Parts Used Sheet', 'Parts cost of one job against the price book', 'jobs.job_id', F(
        ('Date', 'jobs.date'), ('Job type', 'jobs.job_type'), ('Technician', 'jobs.technician'), ('Van', 'jobs.van'), ('Price', 'jobs.price'), ('Parts cost entered', 'jobs.parts_cost'), ('Parts cost in the price book', 'jobs.book_parts'),
        ('Parts over the book', 'jobs.parts_over'), ('Entry check', 'jobs.entry_flag')) + [
        FF('Parts as a share of the price', 'IFERROR(INDEX({range:jobs.parts_cost},MATCH({pick},{range:jobs.job_id},0))/INDEX({range:jobs.price},MATCH({pick},{range:jobs.job_id},0)),0)', 'pct')]),
    FORM('sub_sheet', 'Subcontract Cost Sheet', 'Subcontract, permit and disposal cost of one job', 'jobs.job_id', F(
        ('Date', 'jobs.date'), ('Site reference', 'jobs.site_ref'), ('Job type', 'jobs.job_type'), ('Price', 'jobs.price'), ('Subcontract cost', 'jobs.sub_cost'), ('Permit fee', 'jobs.permit_fee'), ('Disposal', 'jobs.disposal'),
        ('Total cost', 'jobs.total_cost'), ('Margin', 'jobs.margin')) + [
        FF('Outside cost as a share of the price', 'IFERROR((INDEX({range:jobs.sub_cost},MATCH({pick},{range:jobs.job_id},0))+INDEX({range:jobs.permit_fee},MATCH({pick},{range:jobs.job_id},0))+INDEX({range:jobs.disposal},MATCH({pick},{range:jobs.job_id},0)))/INDEX({range:jobs.price},MATCH({pick},{range:jobs.job_id},0)),0)', 'pct')]),
    FORM('callback_report_sheet', 'Callback Report Sheet', 'Callback with reason, hours, parts and cost', 'callbacks.callback_id', F(
        ('Date', 'callbacks.date'), ('Original job', 'callbacks.original_job'), ('Callback job', 'callbacks.callback_job'), ('Technician of the original job', 'callbacks.technician'), ('Job type', 'callbacks.job_type'),
        ('Site reference', 'callbacks.site_ref'), ('Reason', 'callbacks.reason'), ('Hours', 'callbacks.hours'), ('Drive hours', 'callbacks.drive_hours'), ('Parts cost', 'callbacks.parts_cost'), ('Labour and travel', 'callbacks.labour_travel'),
        ('All-in cost', 'callbacks.cost'), ('Who paid', 'callbacks.paid_by'), ('Days after the original job', 'callbacks.days_after'), ('Original job price', 'callbacks.orig_price'))),
    FORM('callback_review_sheet', 'Callback Review Sheet', 'Technician callback rate with the shop rate', 'cb_tech.row_id', F(
        ('Technician', 'cb_tech.technician'), ('Period', 'cb_tech.period'), ('From', 'cb_tech.from_date'), ('To', 'cb_tech.to_date'), ('Jobs that can have a callback', 'cb_tech.jobs'), ('Callbacks', 'cb_tech.callbacks'),
        ('Callback rate', 'cb_tech.rate'), ('Shop callback rate', 'cb_tech.shop_rate'), ('Times the shop rate', 'cb_tech.ratio'), ('Callback cost', 'cb_tech.cost'), ('Verdict', 'cb_tech.status'))),
    FORM('warranty_visit_sheet', 'Warranty Visit Sheet', 'Warranty visit with equipment type and cost', 'callbacks.callback_id', F(
        ('Date', 'callbacks.date'), ('Site reference', 'callbacks.site_ref'), ('Original job', 'callbacks.original_job'), ('Equipment type', 'callbacks.equip_type'), ('Reason', 'callbacks.reason'), ('Warranty', 'callbacks.warranty'),
        ('Days after the original job', 'callbacks.days_after'), ('Technician of the original job', 'callbacks.technician'), ('All-in cost', 'callbacks.cost'), ('Who paid', 'callbacks.paid_by'))),
    FORM('replace_sheet', 'Replace or Repair Sheet', 'Repair or replace numbers and sentence', 'replace_inputs.site_ref', F(
        ('Quote date', 'replace_inputs.quote_date'), ('Equipment type', 'replace_inputs.equip_type'), ('Age in years', 'replace_inputs.age_years'), ('Expected life in years', 'replace_inputs.life_years'), ('Remaining years', 'replace_inputs.remaining'),
        ('Repair quote', 'replace_inputs.repair_quote'), ('Replacement price', 'replace_inputs.replace_price'), ('Repair cost per remaining year', 'replace_inputs.repair_year'), ('Replacement cost per year', 'replace_inputs.replace_year'),
        ('Repair per year over replacement', 'replace_inputs.ratio'), ('Sentence for the estimate', 'replace_inputs.sentence'))),
    FORM('margin_review_sheet', 'Margin Review Sheet', 'Job type margin against target and trend', 'margin_jt.job_type', F(
        ('Job kind', 'margin_jt.kind'), ('Jobs, last 120 days', 'margin_jt.jobs_120'), ('Revenue', 'margin_jt.revenue_120'), ('Cost', 'margin_jt.cost_120'), ('Margin', 'margin_jt.margin_120'), ('Margin percent', 'margin_jt.margin_pct_120'),
        ('Margin percent, 12 months before', 'margin_jt.margin_pct_p12'), ('Change in points', 'margin_jt.change_pts'), ('Target margin', 'margin_jt.target'), ('Gap to target', 'margin_jt.gap'), ('Target check', 'margin_jt.status'),
        ('Trend against last year', 'margin_jt.trend'), ('Price per job', 'margin_jt.price_job'), ('Price per job for the target', 'margin_jt.price_target'), ('Price rise to reach the target', 'margin_jt.rise_target'))),
    FORM('tech_review_sheet', 'Technician Job Review Sheet', 'Technician ticket, margin and callbacks', 'tick_tech.row_id', F(
        ('Technician', 'tick_tech.technician'), ('Period', 'tick_tech.period'), ('Jobs', 'tick_tech.jobs'), ('Revenue', 'tick_tech.revenue'), ('Average ticket', 'tick_tech.avg_ticket'), ('Shop average ticket', 'tick_tech.shop_ticket'),
        ('Gap to shop average', 'tick_tech.ticket_gap'), ('Margin percent', 'tick_tech.margin_pct'), ('Margin per job', 'tick_tech.margin_job'), ('Points lost to callbacks', 'tick_tech.cb_drop'), ('Margin percent after callbacks', 'tick_tech.after_pct'))),
    FORM('scenario_sheet', 'What-if Scenario Sheet', 'Scenario with labour, parts and close rate changes', 'scenarios.row_id', F(
        ('Scenario', 'scenarios.scenario'), ('Jobs volume change', 'scenarios.volume_change'), ('Labour cost change', 'scenarios.labour_change'), ('Parts cost change', 'scenarios.parts_change'), ('Close rate change in points', 'scenarios.close_change'),
        ('Monthly contribution', 'scenarios.contribution'), ('Volume factor', 'scenarios.volume_factor'), ('Monthly profit', 'scenarios.monthly_profit'), ('Against base at today volume', 'scenarios.profit_change'), ('Break-even jobs a week', 'scenarios.break_even_week'))),
    FORM('weekly_profit_sheet', 'Weekly Job Profit Sheet', 'Month of job profit with the average per week', 'tick_month.row_id', F(
        ('Month', 'tick_month.month'), ('Jobs', 'tick_month.jobs'), ('Revenue', 'tick_month.revenue'), ('Parts cost', 'tick_month.parts_cost'), ('Labour cost', 'tick_month.labour_cost'), ('Subcontract cost', 'tick_month.sub_cost'),
        ('Permit, disposal and vehicle', 'tick_month.other_cost'), ('Margin before callbacks', 'tick_month.margin'), ('Callback cost', 'tick_month.cb_cost'), ('Gross profit after callbacks', 'tick_month.gross_profit'),
        ('Margin percent after callbacks', 'tick_month.margin_pct'), ('Average ticket', 'tick_month.avg_ticket'), ('Same month last year', 'tick_month.ly_ticket'), ('Callback rate', 'tick_month.cb_rate'), ('Gross profit per week', 'tick_month.profit_week'))),
]
assert len(forms) == 12

def PG(*x): return list(x)
documents = [
    DOC('job_cost_doc', 'Job Cost Summary', 'Job cost summary for one job', 'jobs.job_id', PG(
        'Job cost summary of {set:company}, dated {today}. Job {col:jobs.job_id} on {col:jobs.date}, site {col:jobs.site_ref}: {col:jobs.job_type}, done by {col:jobs.technician}.',
        'Price {col:jobs.price}. Costs: parts {col:jobs.parts_cost}, labour {col:jobs.labour_cost}, permit {col:jobs.permit_fee}, disposal {col:jobs.disposal}, subcontract {col:jobs.sub_cost}, vehicle {col:jobs.vehicle_cost}. Total cost {col:jobs.total_cost}.',
        'Margin {col:jobs.margin}, which is {col:jobs.margin_pct} of the price. Hours on site {col:jobs.hours}, hours in the price book {col:jobs.book_hours}. Verdict: {col:jobs.cause}.', 'Comments and the action agreed are written below with the date.'), ['Office manager', 'Owner'], NOTE),
    DOC('weekly_profit_doc', 'Weekly Job Profit Report', 'Weekly job profit report from one month', 'tick_month.row_id', PG(
        'Job profit report of {set:company}, dated {today}. Month {col:tick_month.month}: {col:tick_month.jobs} jobs and revenue of {col:tick_month.revenue}.',
        'Costs before callbacks {col:tick_month.cost}; margin before callbacks {col:tick_month.margin}; callback cost {col:tick_month.cb_cost}; gross profit after callbacks {col:tick_month.gross_profit}, which is {col:tick_month.margin_pct} of revenue.',
        'On average the month gave a gross profit of {col:tick_month.profit_week} a week. Average ticket {col:tick_month.avg_ticket}; callback rate {col:tick_month.cb_rate}; jobs that lost money {col:tick_month.losing_jobs}.', 'Points for the weekly meeting are written below.'), ['Office manager', 'Owner'], NOTE),
    DOC('margin_report_doc', 'Margin by Job Type Report', 'Margin report for one job type', 'margin_jt.job_type', PG(
        'Margin report of {set:company}, dated {today}. Job type {col:margin_jt.job_type} ({col:margin_jt.kind}).',
        'Last 120 days: {col:margin_jt.jobs_120} jobs, revenue {col:margin_jt.revenue_120}, cost {col:margin_jt.cost_120}, margin {col:margin_jt.margin_120}, which is {col:margin_jt.margin_pct_120}. Target {col:margin_jt.target}; gap {col:margin_jt.gap}; check: {col:margin_jt.target_check_note}.',
        'The 12 months before: margin percent {col:margin_jt.margin_pct_p12}, so the change is {col:margin_jt.change_pts}. The same days last year: {col:margin_jt.margin_pct_ly}; trend: {col:margin_jt.trend}.', 'Decision and date are written below.'), ['Owner'], NOTE),
    DOC('callback_report_doc', 'Callback Report', 'Callback report with the original job and cost', 'callbacks.callback_id', PG(
        'Callback report of {set:company}, dated {today}. Callback {col:callbacks.callback_id} on {col:callbacks.date}, linked to the original job {col:callbacks.original_job} ({col:callbacks.job_type}, site {col:callbacks.site_ref}).',
        'Technician of the original job: {col:callbacks.technician}. Reason: {col:callbacks.reason}. It came {col:callbacks.days_after} days after the original job.',
        'Hours {col:callbacks.hours}, drive hours {col:callbacks.drive_hours}, parts {col:callbacks.parts_cost}. All-in cost {col:callbacks.cost}; who paid: {col:callbacks.paid_by}.', 'What we change so the job is right the first time is written below.'), ['Office manager', 'Owner'], NOTE),
    DOC('tech_callback_doc', 'Technician Callback Review', 'Callback review for a one-to-one talk', 'cb_tech.row_id', PG(
        'Callback review of {set:company}, dated {today}, for {col:cb_tech.technician}. Period: {col:cb_tech.period}, from {col:cb_tech.from_date} to {col:cb_tech.to_date}.',
        '{col:cb_tech.jobs} jobs could have had a callback and {col:cb_tech.callbacks} did, a rate of {col:cb_tech.rate} against the shop rate of {col:cb_tech.shop_rate}, which is {col:cb_tech.ratio} times the shop rate. Cost of those callbacks: {col:cb_tech.cost}.',
        'Check: {col:cb_tech.status}. This talk looks at the jobs together and asks what would help: time on the job, parts on the van, a second opinion. It is about the work, not about blame.', 'Agreed next steps and a date for the next talk are written below.'), ['Owner', 'Technician'], NOTE),
    DOC('warranty_note_doc', 'Warranty Visit Note', 'Warranty visit note for a customer', 'callbacks.callback_id', PG(
        'Warranty visit note from {set:company}, dated {today}. Site {col:callbacks.site_ref}.',
        'We are returning on {col:callbacks.date} to the work done earlier under job {col:callbacks.original_job}. Equipment type: {col:callbacks.equip_type}.',
        'Please check the terms of your warranty for what they cover. If you have a question, reply to this note and we will answer.', 'Thank you for telling us.'), ['Customer', 'Office manager'], NOTE),
    DOC('replace_summary_doc', 'Replace or Repair Summary', 'Replace or repair summary for the customer', 'replace_inputs.site_ref', PG(
        'Repair or replace summary from {set:company}, dated {today}. Site {col:replace_inputs.site_ref}, quote date {col:replace_inputs.quote_date}. Equipment: {col:replace_inputs.equip_type}, {col:replace_inputs.age_years} years old; expected life used in this summary: {col:replace_inputs.life_years} years.',
        'Repair quote: {col:replace_inputs.repair_quote}. Replacement price: {col:replace_inputs.replace_price}. Repair per remaining year: {col:replace_inputs.repair_year}. Replacement per year: {col:replace_inputs.replace_year}.',
        'In plain words: {col:replace_inputs.sentence}. These are our own numbers and not a technical opinion. Please check with us before you decide.', 'The choice of the customer and the date are written below.'), ['Customer', 'Contractor'], NOTE),
    DOC('price_correction_doc', 'Price Correction Proposal', 'Price correction proposal for one job type', 'margin_jt.job_type', PG(
        'Price correction proposal of {set:company}, dated {today}. Job type {col:margin_jt.job_type}.',
        'Today the price per job is {col:margin_jt.price_job} and the cost per job is {col:margin_jt.cost_job}, so the margin is {col:margin_jt.margin_pct_120} against a target of {col:margin_jt.target}.',
        'The price per job for the target is {col:margin_jt.price_target}, a rise of {col:margin_jt.rise_target}. With the buffer the rise would be {col:margin_jt.rise_buffer}, and at this pace of {col:margin_jt.jobs_year} jobs a year it recovers {col:margin_jt.recover_year} a year before any jobs are lost.',
        'Decision, new flat price and start date are written below.'), ['Owner'], NOTE),
    DOC('losing_jobs_doc', 'Losing Jobs Summary', 'Losing jobs summary for the owner meeting', 'tick_month.row_id', PG(
        'Losing jobs summary of {set:company}, dated {today}. Month {col:tick_month.month}.',
        '{col:tick_month.losing_jobs} of {col:tick_month.jobs} jobs lost money. Callbacks: {col:tick_month.cb_count} costing {col:tick_month.cb_cost}. Gross profit after callbacks: {col:tick_month.gross_profit}, which is {col:tick_month.margin_pct} of revenue.',
        'Parts cost {col:tick_month.parts_cost}, labour cost {col:tick_month.labour_cost}, subcontract cost {col:tick_month.sub_cost}. Use the Losing-Money Job Finder for the job list and bring it to the meeting.', 'Decisions and owners are written below.'), ['Owner', 'Office manager'], NOTE),
    DOC('parts_note_doc', 'Parts Used on a Job', 'Parts used on a job with cost against the book', 'jobs.job_id', PG(
        'Parts used note of {set:company}, dated {today}. Job {col:jobs.job_id} on {col:jobs.date}, {col:jobs.job_type}, van {col:jobs.van}, technician {col:jobs.technician}.',
        'Parts cost entered {col:jobs.parts_cost}; parts cost in the price book {col:jobs.book_parts}; difference {col:jobs.parts_over}. Entry check: {col:jobs.entry_flag}.',
        'Price of the job {col:jobs.price}. Check every part against the van stock count and the supplier invoice before the job is closed.', 'Initials and date are written below.'), ['Technician', 'Office manager'], NOTE),
    DOC('sub_record_doc', 'Subcontract Cost Record', 'Subcontract cost record for one job', 'jobs.job_id', PG(
        'Subcontract cost record of {set:company}, dated {today}. Job {col:jobs.job_id} on {col:jobs.date}, site {col:jobs.site_ref}, {col:jobs.job_type}.',
        'Subcontract cost {col:jobs.sub_cost}; permit fee {col:jobs.permit_fee}; disposal {col:jobs.disposal}. Total cost of the job {col:jobs.total_cost}; price {col:jobs.price}; margin {col:jobs.margin}.',
        'Match the subcontractor invoice to this job before payment and write the invoice number below.', 'Checked by and date are written below.'), ['Office manager', 'Subcontractor'], NOTE),
    DOC('accountant_doc', 'Accountant Job Profit Summary', 'Job profit summary for the accountant', 'tick_month.row_id', PG(
        'Job profit summary of {set:company} for the accountant, dated {today}. Month {col:tick_month.month}.',
        'Revenue {col:tick_month.revenue} from {col:tick_month.jobs} jobs. Parts {col:tick_month.parts_cost}, labour {col:tick_month.labour_cost}, subcontract {col:tick_month.sub_cost}, permit, disposal and vehicle {col:tick_month.other_cost}. Margin before callbacks {col:tick_month.margin}.',
        'Callback cost {col:tick_month.cb_cost}, of which warranty cost {col:tick_month.warranty_cost}; warranty reserve for the month {col:tick_month.reserve}. Gross profit after callbacks {col:tick_month.gross_profit}.', 'Confirm with your adviser how these figures are used in your accounts.'), ['Owner', 'Accountant'], NOTE),
]
assert len(documents) == 12
documents[2]['paragraphs'][1] = documents[2]['paragraphs'][1].replace('; check: {col:margin_jt.target_check_note}.', '; check: {col:margin_jt.status}.')

checklists = [
    CHK('job_closed', 'Job Closed and Costed', 'jobs', 'jobs.date', [('Mark the job finished in your field-service app', 0), ('Enter the hours on site, helper hours and drive hours', 0), ('Enter the parts used from the van', 1), ('Enter permit, disposal and subcontract cost', 1), ('Check the margin and the verdict', 2), ('Invoice the job', 2)]),
    CHK('hours_entered', 'Hours Entered', 'jobs', 'jobs.date', [('Ask the technician for the hours', 0), ('Enter hours on site', 0), ('Enter helper and drive hours', 1), ('Compare with the hours in the price book', 1), ('Note a large gap for the weekly review', 3)]),
    CHK('parts_entered', 'Parts Entered', 'jobs', 'jobs.date', [('List the parts taken from the van', 0), ('Enter the parts cost at the supplier price', 1), ('Check the parts against the price book', 1), ('Match equipment to the supplier invoice', 3), ('Flag a missing part for the van restock', 3)]),
    CHK('sub_entered', 'Subcontract Cost Entered', 'jobs', 'jobs.date', [('Ask the subcontractor for the invoice', 1), ('Enter the subcontract cost on the job', 3), ('Enter permit and disposal fees', 3), ('Check the margin after outside costs', 4), ('Approve the subcontractor invoice for payment', 7)]),
    CHK('callback_recorded', 'Callback Recorded', 'callbacks', 'callbacks.date', [('Record the callback with its date', 0), ('Link it to the original job', 0), ('Enter hours, drive hours and parts', 1), ('Choose the reason', 1), ('Mark warranty or goodwill', 1), ('Tell the technician of the original job', 2)]),
    CHK('callback_review', 'Callback Review Meeting', 'callbacks', 'callbacks.date', [('Open the callback report', 0), ('Read the original job and the reason', 0), ('Ask the technician what would help', 2), ('Agree a change to the job or the van stock', 3), ('Write the action and the owner', 3), ('Check the next ten jobs of the same type', 30)]),
    CHK('warranty_handled', 'Warranty Visit Handled', 'callbacks', 'callbacks.date', [('Check the terms of the warranty for the job', 0), ('Book the visit with the customer', 1), ('Tell the customer the date', 1), ('Do the visit and enter the cost', 3), ('Mark the callback as warranty', 3), ('Ask how everything is working', 10)]),
    CHK('weekly_margin', 'Weekly Margin Review', 'tick_month', 'tick_month.month', [('Open the Losing-Money Job Finder', 0), ('Look at each losing job and its cause', 0), ('Check jobs with no hours or no parts', 1), ('Look at callbacks of the week', 1), ('Write two actions for the week', 2)]),
    CHK('monthly_type', 'Monthly Job Type Review', 'margin_month', 'margin_month.month', [('Update the totals for the month', 1), ('Run the Margin by Job Type Check', 2), ('Look at types under target and falling', 3), ('Check the price book for those types', 4), ('Decide which types to re-price', 7)]),
    CHK('repricing', 'Re-pricing a Job Type', 'price_changes', 'price_changes.date', [('Confirm the new supplier cost', 0), ('Update the price book cost', 2), ('Work out the price for the target margin', 3), ('Test the rise in the Water Heater Margin Watch', 4), ('Set the new flat price', 7), ('Tell the office manager and technicians', 8), ('Check the margin after 30 days', 37)]),
    CHK('replace_repair_talk', 'Replace or Repair Discussion', 'replace_inputs', 'replace_inputs.quote_date', [('Enter the age, the repair quote and the replacement price', 0), ('Read the sentence for the estimate', 0), ('Show the customer both costs per year', 1), ('Ask which choice the customer prefers', 1), ('Record the choice and the date', 2)]),
    CHK('tech_one_to_one', 'Technician Callback One-to-One', 'callbacks', 'callbacks.date', [('Open the callback review for the technician', 0), ('Pick three recent callbacks to talk about', 0), ('Ask what would help on those jobs', 3), ('Agree one change to try', 3), ('Write the agreed step', 3), ('Look at the rate again in 90 days', 90)]),
]
assert len(checklists) == 12

def M(key_, moment, table, phone, text): return MSG(key_, moment, table, phone, text)
messages = [
    M('c_sorry', 'Customer: sorry, we need to come back', 'callbacks', 'callbacks.phone', 'Hello, this is {company}. We are sorry we need to come back to {site_ref}. The new visit date is {date}.'),
    M('c_booked', 'Customer: your return visit is booked', 'callbacks', 'callbacks.phone', 'Hello, your return visit to {site_ref} is booked for {date}. Reply to this message if the day does not suit you. {company}'),
    M('c_thanks', 'Customer: thank you for telling us', 'callbacks', 'callbacks.phone', 'Hello, thank you for telling us about the problem at {site_ref}. We have your report of {date} and will be in touch about the next step. {company}'),
    M('c_warranty', 'Customer: warranty visit confirmed', 'callbacks', 'callbacks.phone', 'Hello, your warranty visit at {site_ref} is confirmed for {date}. Please check the terms of your warranty if you have a question. {company}'),
    M('c_howis', 'Customer: how is everything working', 'jobs', 'jobs.phone', 'Hello, this is {company}. How is everything working at {site_ref} after our visit on {date}? Reply if you need us.'),
    M('c_replace', 'Customer: repair or replace summary', 'replace_inputs', 'replace_inputs.phone', 'Hello, a plain summary for {site_ref}: repair quote {repair_quote}, replacement price {replace_price}. {sentence}. Please check with us before you decide. {company}'),
    M('l_return', 'Landlord: we return at no charge', 'callbacks', 'callbacks.phone', 'Hello, we are returning to {site_ref} on {date} at no charge to you. {company}'),
    M('l_cost', 'Landlord: cost summary for a site', 'jobs', 'jobs.phone', 'Hello, summary for {site_ref}: job {job_id} on {date}, {job_type}, amount billed {price}. {company}'),
    M('t_rate', 'Technician: your callback rate', 'cb_tech', 'cb_tech.tech_phone', 'Hello {technician}, your callback rate for {period} is {rate} against the shop rate of {shop_rate}. Can we talk this week? {company}'),
    M('t_lost', 'Technician: a job lost money', 'jobs', 'jobs.tech_phone', 'Hello {technician}, job {job_id} on {date} ended with a margin of {margin}. Can we talk about it? {company}'),
    M('t_hours', 'Technician: please enter your hours', 'jobs', 'jobs.tech_phone', 'Hello {technician}, please enter your hours for job {job_id} on {date}. {company}'),
    M('t_parts', 'Technician: please enter your parts', 'jobs', 'jobs.tech_phone', 'Hello {technician}, please enter the parts you used on job {job_id} on {date}. {company}'),
    M('t_thanks', 'Technician: your margin per job is up', 'tick_tech', 'tick_tech.tech_phone', 'Hello {technician}, thank you: your margin per job for {period} is {margin_job}. {company}'),
    M('t_cbbooked', 'Technician: a callback on your job', 'callbacks', 'callbacks.tech_phone', 'Hello {technician}, a callback was booked on your job {original_job} for {date}. {company}'),
    M('a_hours', 'Apprentice: please enter your hours', 'costing', 'costing.assist_phone', 'Hello {assistant}, please enter your hours on job {job_id} on {date}. {company}'),
    M('o_nohours', 'Office manager: no hours entered', 'costing', 'costing.office_phone', 'Hello {office_name}, job {job_id} on {date} has no hours entered. Please ask {technician} to enter them. {company}'),
    M('o_noparts', 'Office manager: no parts entered', 'costing', 'costing.office_phone', 'Hello {office_name}, job {job_id} on {date} has no parts entered. Please check with {technician}. {company}'),
    M('o_notlinked', 'Office manager: callback not linked', 'callbacks', 'callbacks.office_phone', 'Hello {office_name}, callback {callback_id} on {date} is not linked to an original job. Please link it. {company}'),
    M('o_warranty', 'Office manager: mark as warranty', 'costing', 'costing.office_phone', 'Hello {office_name}, please mark job {job_id} ({site_ref}, {date}) as warranty if it is one. {company}'),
    M('w_lost', 'Owner: jobs lost money in a month', 'tick_month', 'tick_month.owner_phone', 'Hello {owner_name}, {losing_jobs} jobs lost money in {month}. Gross profit after callbacks was {gross_profit}. {company}'),
    M('w_under', 'Owner: a job type margin is under target', 'margin_jt', 'margin_jt.owner_phone', 'Hello {owner_name}, {job_type} margin is {margin_pct_120} against a target of {target}. {company}'),
    M('w_ratio', 'Owner: technician callbacks vs shop', 'cb_tech', 'cb_tech.owner_phone', 'Hello {owner_name}, {technician} callbacks for {period} are {ratio} times the shop average (rate {rate}). {company}'),
    M('w_cbcost', 'Owner: callback cost', 'cb_tech', 'cb_tech.owner_phone', 'Hello {owner_name}, callback cost for {technician}, {period}, is {cost}. {company}'),
    M('w_wh', 'Owner: water heater margin', 'wh_month', 'wh_month.owner_phone', 'Hello {owner_name}, water heater margin in {month} is {margin_pct} against a target of {target}. {company}'),
    M('w_rise', 'Owner: the price rise needed', 'margin_jt', 'margin_jt.owner_phone', 'Hello {owner_name}, the price rise needed on {job_type} is {rise_target}: price per job {price_job}, price for the target {price_target}. {company}'),
    M('w_proposals', 'Owner: price proposals are ready', 'margin_jt', 'margin_jt.owner_phone', 'Hello {owner_name}, the price correction proposal for {job_type} is ready. Re-pricing could recover {recover_year} a year. {company}'),
    M('w_forecast', 'Owner: the job profit forecast is ready', 'tick_month', 'tick_month.owner_phone', 'Hello {owner_name}, the job profit forecast is ready. Last month on file, {month}, gave a gross profit of {profit_week} a week. {company}'),
    M('s_price', 'Supplier: confirm the new price', 'price_changes', 'price_changes.supplier_phone', 'Hello {supplier_contact}, please confirm the new price for {part}: {new_cost}, up from {old_cost}. {company}'),
    M('p_counter', 'Parts counter: confirm the invoice', 'costing', 'costing.counter_phone', 'Hello {counter_name}, please confirm the parts invoice for job {job_id} on {date}. {company}'),
    M('e_elec', 'Electrical sub: send the invoice', 'costing', 'costing.elec_phone', 'Hello {elec_name}, please send the invoice for the electrical work on job {job_id} on {date} ({site_ref}). {company}'),
    M('e_sheet', 'Sheet-metal sub: send the invoice', 'costing', 'costing.sheet_phone', 'Hello {sheet_name}, please send the invoice for the sheet-metal work on job {job_id} on {date} ({site_ref}). {company}'),
    M('x_job', 'Accountant: job costing is ready', 'tick_month', 'tick_month.acct_phone', 'Hello {acct_name}, job costing for {month} is ready: revenue {revenue}, gross profit {gross_profit}. {company}'),
    M('x_warranty', 'Accountant: warranty cost for a month', 'tick_month', 'tick_month.acct_phone', 'Hello {acct_name}, warranty cost for {month} is {warranty_cost}. {company}'),
    M('i_summary', 'Insurance agent: callback summary', 'tick_month', 'tick_month.ins_phone', 'Hello {ins_name}, callbacks and warranty for {month}: {cb_count} callbacks, warranty cost {warranty_cost}. {company}'),
]
assert len(messages) == 34, len(messages)

# ---------------- dashboard
def J(c): return '{range:jobs.%s}' % c
def CB(c): return '{range:callbacks.%s}' % c
def TM(c): return '{range:tick_month.%s}' % c
def W(n): return '%s,">"&({today}-%d),%s,"<="&{today}' % (J('date'), n, J('date'))
def CW(n): return '%s,">"&({today}-%d),%s,"<="&{today}' % (CB('date'), n, CB('date'))
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; Y12 = 'DATE(YEAR({today}),MONTH({today})-12,1)'
SEASON = 'DATE(YEAR({today}),MONTH({today})-MOD(MONTH({today})-3,3),1)'
P12 = tok('period', 'Last 12 months'); WHT = LV('jobtype', key('jobtype', 'Water heater replacement'))
TMA = '%s,">="&%s' % (TM('month'), Y12)
M90 = 'IFERROR(SUMIFS(%s,%s)/SUMIFS(%s,%s),0)' % (J('margin'), W(90), J('price'), W(90))
WH120 = 'IFERROR(SUMIFS(%s,%s,%s,%s,%s,%s)/SUMIFS(%s,%s,%s,%s,%s,%s),0)' % (J('margin'), J('job_type'), WHT, J('is_callback'), NO, W(120), J('price'), J('job_type'), WHT, J('is_callback'), NO, W(120))
CB12 = 'IFERROR(SUMIFS(%s,%s,%s)/SUMIFS(%s,%s,%s),0)' % (R_ := '{range:cb_tech.callbacks}', '{range:cb_tech.period}', P12, '{range:cb_tech.jobs}', '{range:cb_tech.period}', P12)
kpis = [
    KPI('Job margin percent, last 30 days', 'IFERROR(SUMIFS(%s,%s)/SUMIFS(%s,%s),0)' % (J('margin'), W(30), J('price'), W(30)), 'pct'),
    KPI('Job margin percent, last 90 days', M90, 'pct'),
    KPI('Job margin percent, last 12 months', 'IFERROR(SUMIFS(%s,%s)/SUMIFS(%s,%s),0)' % (TM('gross_profit'), TMA, TM('revenue'), TMA), 'pct'),
    KPI('Margin against target, 90 days (points)', '(%s-{set:margin_target})*100' % M90, 'num'),
    KPI('Average ticket, last 30 days', 'IFERROR(SUMIFS(%s,%s)/COUNTIFS(%s,">0",%s),0)' % (J('price'), W(30), J('price'), W(30)), 'money'),
    KPI('Average ticket, last 12 months', 'IFERROR(SUMIFS(%s,%s)/SUMIFS(%s,%s),0)' % (TM('revenue'), TMA, TM('jobs'), TMA), 'money'),
    KPI('Average ticket, same month last year', 'IFERROR(INDEX(%s,MATCH(EDATE(%s,-12),%s,0)),0)' % (TM('avg_ticket'), MS, TM('month')), 'money'),
    KPI('Jobs that lost money, last 30 days', 'COUNTIFS(%s,">0",%s)' % (J('lost'), W(30)), 'int'),
    KPI('Money lost on losing jobs, last 90 days', 'SUMIFS(%s,%s)' % (J('lost'), W(90)), 'money'),
    KPI('Gross profit this month so far', 'SUMIFS(%s,%s,">="&%s,%s,"<="&{today})' % (J('margin'), J('date'), MS, J('date')), 'money'),
    KPI('Gross profit, last 30 days', 'SUMIFS(%s,%s)' % (J('margin'), W(30)), 'money'),
    KPI('Gross profit per site hour, 90 days', 'IFERROR(SUMIFS(%s,%s)/SUMIFS(%s,%s),0)' % (J('margin'), W(90), J('hours'), W(90)), 'money'),
    KPI('Job types under target', 'COUNTIFS({range:margin_jt.status},%s)' % c2('Under target'), 'int'),
    KPI('Lowest margin job type', 'INDEX({range:margin_jt.job_type},MATCH(MIN({range:margin_jt.margin_pct_120}),{range:margin_jt.margin_pct_120},0))', 'text'),
    KPI('Highest margin job type', 'INDEX({range:margin_jt.job_type},MATCH(MAX({range:margin_jt.margin_pct_120}),{range:margin_jt.margin_pct_120},0))', 'text'),
    KPI('Water heater margin, last 120 days', WH120, 'pct'),
    KPI('Water heater target gap (points)', '(%s-IFERROR(INDEX({range:job_types.target_margin},MATCH(%s,{range:job_types.job_type},0)),0))*100' % (WH120, WHT), 'num'),
    KPI('Callbacks, last 30 days', 'COUNTIFS(%s)' % CW(30), 'int'),
    KPI('Callbacks, last 90 days', 'COUNTIFS(%s)' % CW(90), 'int'),
    KPI('Callback rate, last 12 months', CB12, 'pct'),
    KPI('Callback rate of the highest technician', 'MAX({range:cb_tech.rate12})', 'pct'),
    KPI('Highest rate against shop average', 'IFERROR(MAX({range:cb_tech.rate12})/%s,0)' % CB12, 'num'),
    KPI('Cost of callbacks this season', 'SUMIFS(%s,%s,">="&%s)' % (CB('cost'), CB('date'), SEASON), 'money'),
    KPI('Cost of callbacks, last 12 months', 'SUMIFS(%s,%s,">="&%s)' % (CB('cost'), CB('date'), Y12), 'money'),
    KPI('Warranty callbacks, last 90 days', 'COUNTIFS(%s,%s,%s)' % (CB('warranty'), YES, CW(90)), 'int'),
    KPI('Warranty cost, last 12 months', 'SUMIFS(%s,%s,%s,%s,">="&%s)' % (CB('cost'), CB('warranty'), YES, CB('date'), Y12), 'money'),
    KPI('Callback cost share of revenue', 'IFERROR(SUMIFS(%s,%s,">="&%s)/SUMIFS(%s,%s),0)' % (CB('cost'), CB('date'), Y12, TM('revenue'), TMA), 'pct'),
    KPI('Jobs with no hours entered', 'COUNTIFS(%s,%s)' % (J('entry_flag'), c4('Hours missing')), 'int'),
    KPI('Jobs with no parts entered', 'COUNTIFS(%s,%s)' % (J('entry_flag'), c4('Parts missing')), 'int'),
    KPI('Labour plus 5 percent, profit a month', '-0.05*SUMIFS(%s,%s,">="&%s,%s,"<"&%s)/12' % (TM('labour_cost'), TM('month'), Y12, TM('month'), MS), 'money'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Job Costing Dashboard", "kpis": kpis,
    "monthly": {"title": "Revenue, gross profit and callback cost by month", "date": "tick_month.month", "series": [
        {"label": "Revenue", "sum": "tick_month.revenue", "date": "tick_month.month"}, {"label": "Gross profit after callbacks", "sum": "tick_month.gross_profit", "date": "tick_month.month"},
        {"label": "Callback cost", "sum": "tick_month.cb_cost", "date": "tick_month.month"}]},
    "breakdowns": [{"title": "Revenue by job type, last 120 days", "by": "margin_jt.job_type", "value": "margin_jt.revenue_120", "agg": "sum"},
                   {"title": "Callbacks by technician", "by": "callbacks.technician", "value": "callbacks.cost", "agg": "count"},
                   {"title": "Jobs by option tier", "by": "jobs.tier", "value": "jobs.price", "agg": "count"},
                   {"title": "Callback cost by job type, 12 months", "by": "cb_type.job_type", "value": "cb_type.cb_cost", "agg": "sum"}]}
P12W = ('period', '=', P12)
insights = {"filters": [{"label": "Technician", "list": "tech"}, {"label": "Job type", "list": "jobtype"}],
    "gauges": [{"title": "Jobs at or above the margin target", "num": AGG('count', 'jobs', where=[('is_callback', '=', NO), ('margin_pct', '>=', '{set:margin_target}')]), "den": AGG('count', 'jobs', where=[('is_callback', '=', NO)])},
               {"title": "Technicians within the callback target", "num": AGG('count', 'cb_tech', where=[P12W, ('rate', '<=', '{set:callback_target}')]), "den": AGG('count', 'cb_tech', where=[P12W])},
               {"title": "Job types on or near target", "num": AGG('count', 'margin_jt', where=[('status', '<>', c2('Under target'))]), "den": AGG('count', 'margin_jt')},
               {"title": "Jobs with hours and parts entered", "num": AGG('count', 'jobs', where=[('entry_flag', '=', c4('Complete'))]), "den": AGG('count', 'jobs')},
               {"title": "Jobs that made money", "num": AGG('count', 'jobs', where=[('margin', '>=', 0)]), "den": AGG('count', 'jobs')},
               {"title": "Months with warranty within reserve", "num": AGG('count', 'tick_month', where=[('reserve_flag', '=', c5('Within reserve'))]), "den": AGG('count', 'tick_month')}],
    "charts": [
        CHART('Margin percent per month', 'column', 'month', [AGG('avg', 'tick_month', 'tick_month.margin_pct', date='tick_month.month', label='Margin percent')]),
        CHART('Revenue per month', 'column', 'month', [AGG('sum', 'tick_month', 'tick_month.revenue', date='tick_month.month', label='Revenue')]),
        CHART('Gross profit per month', 'column', 'month', [AGG('sum', 'tick_month', 'tick_month.gross_profit', date='tick_month.month', label='Gross profit after callbacks')]),
        CHART('Margin percent by job type', 'bar', 'margin_jt.job_type', [AGG('avg', 'margin_jt', 'margin_jt.margin_pct_120', label='Margin percent')]),
        CHART('Revenue by job type', 'bar', 'margin_jt.job_type', [AGG('sum', 'margin_jt', 'margin_jt.revenue_120', label='Revenue')]),
        CHART('Jobs by job type', 'bar', 'margin_jt.job_type', [AGG('sum', 'margin_jt', 'margin_jt.jobs_120', label='Jobs')]),
        CHART('Average ticket by technician', 'bar', 'tick_tech.technician', [AGG('avg', 'tick_tech', 'tick_tech.avg_ticket', where=[P12W], label='Average ticket')]),
        CHART('Average ticket by van', 'bar', 'tick_van.van', [AGG('avg', 'tick_van', 'tick_van.avg_ticket', where=[P12W], label='Average ticket')]),
        CHART('Average ticket by site type', 'bar', 'tick_site.site_type', [AGG('avg', 'tick_site', 'tick_site.avg_ticket', where=[P12W], label='Average ticket')]),
        CHART('Average ticket per month', 'column', 'month', [AGG('avg', 'tick_month', 'tick_month.avg_ticket', date='tick_month.month', label='Average ticket')]),
        CHART('Margin percent by technician', 'bar', 'tick_tech.technician', [AGG('avg', 'tick_tech', 'tick_tech.margin_pct', where=[P12W], label='Margin percent')]),
        CHART('Water heater margin per month', 'column', 'month', [AGG('avg', 'wh_month', 'wh_month.margin_pct', date='wh_month.month', label='Margin percent'), AGG('avg', 'wh_month', 'wh_month.target', date='wh_month.month', label='Target')]),
        CHART('Callbacks per month', 'column', 'month', [AGG('count', 'callbacks', date='callbacks.date', label='Callbacks')]),
        CHART('Callbacks by technician', 'bar', 'callbacks.technician', [AGG('count', 'callbacks', label='Callbacks')]),
        CHART('Callbacks by job type, 12 months', 'bar', 'cb_type.job_type', [AGG('sum', 'cb_type', 'cb_type.callbacks', label='Callbacks')]),
        CHART('Callbacks by reason', 'bar', 'callbacks.reason', [AGG('count', 'callbacks', label='Callbacks')]),
        CHART('Callback cost per month', 'column', 'month', [AGG('sum', 'callbacks', 'callbacks.cost', date='callbacks.date', label='Callback cost')]),
        CHART('Callback rate per month', 'column', 'month', [AGG('avg', 'tick_month', 'tick_month.cb_rate', date='tick_month.month', label='Callback rate')]),
        CHART('Warranty callbacks per month', 'column', 'month', [AGG('count', 'callbacks', date='callbacks.date', where=[('warranty', '=', YES)], label='Warranty callbacks')]),
        CHART('Jobs that lost money per month', 'column', 'month', [AGG('sum', 'tick_month', 'tick_month.losing_jobs', date='tick_month.month', label='Jobs that lost money')]),
        CHART('Jobs by option tier', 'bar', 'jobs.tier', [AGG('count', 'jobs', label='Jobs')]),
        CHART('Cost by type per month', 'stacked', 'month', [AGG('sum', 'tick_month', 'tick_month.parts_cost', date='tick_month.month', label='Parts'), AGG('sum', 'tick_month', 'tick_month.labour_cost', date='tick_month.month', label='Labour'),
                                                            AGG('sum', 'tick_month', 'tick_month.sub_cost', date='tick_month.month', label='Subcontract'), AGG('sum', 'tick_month', 'tick_month.other_cost', date='tick_month.month', label='Permit, disposal and vehicle')])]}
assert len(insights['charts']) == 22

signature = [
    {"name": "Job costing per job", "why": "hours times loaded rate, parts, permit, disposal, subcontract and vehicle against the price, with a one-line verdict on why a job won or lost money", "where": "Job Costing per Job"},
    {"name": "Margin check of every job type", "why": "all 15 job types against their own targets and the 12 months before, with the type that fell furthest named", "where": "Margin by Job Type Check"},
    {"name": "Water heater margin watch", "why": "margin by month against the target and the unit cost rise, the flat price that restores the target and what a rise could cost in lost jobs", "where": "Water Heater Margin Watch"},
    {"name": "Losing-money job finder", "why": "the jobs of the last 90 days ranked by the money they lost, with technician, cause and the biggest leak", "where": "Losing-Money Job Finder"},
    {"name": "Callback cost with the original job", "why": "each return visit linked to its original job with hours, parts and travel, who paid and the money it takes this season", "where": "Callback Cost Tool"},
    {"name": "Callback rate by technician and job type", "why": "rate against your target and the shop average, the ratio and a verdict: talk this week, watch or fine", "where": "Callback Rate Tool"},
    {"name": "Callback-aware margin", "why": "job margin after the cost of callbacks by technician and job type, so a margin that looks good and is not shows up", "where": "Callback-Aware Margin"},
    {"name": "Replace versus repair sentence", "why": "your own age, quote, price and life numbers become a cost per year of each choice and a plain sentence for the estimate", "where": "Replace versus Repair Sentence"},
    {"name": "What-if on labour, parts and close rate", "why": "monthly profit and break-even jobs a week for Base, Best and Worst and a sensitivity row", "where": "What-if on Labour and Parts"},
    {"name": "Margin recovery planner", "why": "job types ranked by the price rise needed, the money recovered a year and the net gain after the jobs you could lose", "where": "Margin Recovery Planner"},
    {"name": "Warranty cost against a reserve", "why": "warranty callbacks by month and equipment type against the reserve your own history suggests", "where": "Warranty Cost Tracker"},
    {"name": "Job profit forecast with callbacks", "why": "margin per job times booked jobs and your own seasonal index for the weeks ahead, callback cost deducted, Base, Best and Worst", "where": "Monthly Job Profit Forecast"}]
competitors = [
    {"what": "field-service app with a per-technician fee", "lacks": "bills every seat each month and shows job totals, but not the cost lines of one job, margin by job type against your target or callback cost"},
    {"what": "generic invoice template", "lacks": "records what you billed and nothing about what the job cost, so a job that lost money looks the same as one that made money"},
    {"what": "single-sheet quote calculator", "lacks": "prices one job from a markup but never checks the result against hours, parts, permit and subcontract cost after the job is done"},
    {"what": "pen-and-paper job book", "lacks": "keeps hours and parts on paper, with no margin per job, no callback rate by technician and no warning when a supplier price rise eats a job type"},
    {"what": "accounting package with job tags", "lacks": "reports profit by month but cannot rank losing jobs, price the rise needed per job type or tell a callback from a new job"}]
guide = [
    'Open the Start sheet and type your company name and your own limits in the yellow cells: margin target, thin margin, callback target, close rate, warranty reserve, overhead a month and the extras on pay (confirm with your adviser).',
    'Check Job types and Technicians. They hold your target margin for each job type (a typical range, check your own numbers) and the hourly rate of each technician; the other sheets read them.',
    'Check the Price book: the fixed price per task, built from cost, with its labour hours, parts and all-in cost. Jobs are compared with it.',
    'Enter every finished job on Jobs: price, hours on site, helper hours, drive hours and each cost line. Total cost, margin, margin percent and a one-line verdict fill in by themselves.',
    'Use Job costing lines to see the cost lines of any job and the share of the price that parts and labour take.',
    'Write each return visit to fix the same job on Callbacks (a callback), linked to the original job, with hours, parts and cost. Who paid and the share of the original price calculate.',
    'Type the totals of the last 120 days for each job type on Margin by job type. Trend, gap to target, the price rise needed and margin per hour calculate.',
    'Keep Ticket by month, Ticket by technician, Ticket by van and Ticket by site type up to date. The average ticket is the amount billed on one job.',
    'Callback rate by technician and by job type read the Callbacks sheet; Callback reasons shows which cause costs most.',
    'Watch Water heater margin: the margin against the target month by month and the unit cost rise after a supplier price change.',
    'Type your own numbers on Repair or replace; the sentence for the estimate calculates. It gives no technical advice.',
    'Use Scenario table and the What-if tool to test labour, parts and close rate (estimates won over estimates decided) on monthly profit.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Job Costing Dashboard and Charts every week: margin, ticket, losing jobs, callbacks, warranty cost and water heater margin.']
listing = {"title": "HVAC and Plumbing Job Costing Excel Template: Job Margin, Callbacks, Warranty Cost, Price Book, Repair or Replace",
    "headline": "See what every job really earned, by job type and technician",
    "tags": ["hvac job costing", "plumbing job costing", "job margin", "callback tracker", "warranty cost", "hvac excel", "plumber template", "gross margin", "flat rate pricing", "average ticket", "contractor template", "service business", "callback rate"],
    "description": ("Job costing for a small HVAC and plumbing contractor in one Excel workbook. Built for an owner-run service shop with one to fifteen technicians, an office manager who dispatches and a few vans. "
        "Jobs holds every finished job with its price and each cost line: parts, labour, permit, disposal, subcontract and vehicle. Total cost, margin, margin percent against the price book and a one-line verdict (won money, thin margin, lost money because of parts, hours, price or a callback) fill in by themselves.\n\n"
        "Margin by job type compares the last 120 days of all 15 job types with their own targets, with the 12 months before and with the same days last year, and works out the price rise needed to reach the target. "
        "Water Heater Margin shows the margin month by month against the target after a supplier price rise. Ticket sheets give the average ticket (the amount billed on one job) and margin by technician, van, site type and month.\n\n"
        "Callbacks links every return visit to fix the same job to the original job, with hours, parts, travel and cost, and shows who paid. Callback rate by technician and by job type, callback reasons, callback-aware margin and a warranty cost tracker show where money leaks. "
        "Repair or replace turns your own age, quote, price and life numbers into a cost per year of each choice and a plain sentence for the estimate.\n\n"
        f"{len(tools)} tools answer weekly questions: which jobs lost money, which job type to re-price first, what labour or parts prices do to monthly profit, and what the next weeks may earn. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to customers, landlord accounts, technicians, the office manager, the owner, suppliers, subcontractors and the accountant.\n\n"
        "This is part three of the HVAC and Plumbing Contractor suite. A standard .xlsx workbook with no macros and no per-technician fee, with a demo copy full of sample data to explore first. It helps you keep track of your own numbers and does not promise results."),
    "features": ["Job costing with a verdict on every job", "Margin by job type against your own targets", "Water heater margin watch after a supplier price rise", "Callbacks linked to the original job", "Callback rate by technician and job type",
                 "Callback-aware margin and warranty cost tracker", "Replace versus repair sentence from your own numbers", "What-if on labour, parts and close rate", f"{len(tools)} decision tools",
                 f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p3', slug='hvac-plumbing-job-costing', profession='HVAC and Plumbing Contractor', name='Job Costing, Margin and Callbacks',
         tagline='See what every job earned, what callbacks cost and which prices to fix', price_usd=29,
         colors={"primary": "#1F4E5F", "accent": "#E07A3F"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 3, "of": 8, "focus": "Job costing, margin and callbacks"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hv3.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
