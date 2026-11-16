"""HVAC and plumbing contractor suite - part 8: Leads, Reviews, Renewals, Scorecard."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv8_lists import *
from hv8_tables import settings, tables
from hv8_tools import tools
import hv8_data as D

SUITE = 'fx-20261115-hvac-plumbing'
NOTE = "Sample wording: adapt it to your own business and check your local rules."
YES, NO = '{list:yesno.yes}', '{list:yesno.no}'
COMP = tok('jobstatus', 'Completed')
OPEN = tok('rnstatus', 'Open')
G, AM, RD = ck('Green'), ck('Amber'), ck('Red')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def EM(n): return 'EDATE(%s,%d)' % (MS, n)
def F(*pairs): return [FV(a, b) for a, b in pairs]
SG = ['Owner', 'Office manager']

forms = [
    FORM('lead_source_sheet', 'Lead Source Sheet', 'Lead source result for one period', 'src_results.row_id', F(
        ('Source', 'src_results.source'), ('Period', 'src_results.period'), ('Spend', 'src_results.spend'), ('Calls', 'src_results.calls'), ('Booked jobs', 'src_results.booked'), ('Sold jobs', 'src_results.sold'),
        ('Revenue', 'src_results.revenue'), ('Cost per booked job', 'src_results.cost_per_booked'), ('Revenue per spend', 'src_results.revenue_per_spend'), ('Verdict', 'src_results.verdict'))),
    FORM('marketing_sheet', 'Marketing Spend Sheet', 'Marketing spend of one source and month', 'marketing.row_id', F(
        ('Month', 'marketing.month'), ('Source', 'marketing.source'), ('Spend', 'marketing.spend'), ('Calls', 'marketing.calls'), ('Booked jobs', 'marketing.booked'), ('Sold jobs', 'marketing.sold'), ('Revenue', 'marketing.revenue'),
        ('Cost per lead', 'marketing.cost_per_lead'), ('Cost per booked job', 'marketing.cost_per_booked'), ('Revenue per spend', 'marketing.revenue_per_spend'))),
    FORM('review_request_sheet', 'Review Request Sheet', 'Review requests of one technician and month', 'reviews.row_id', F(
        ('Month', 'reviews.month'), ('Technician', 'reviews.technician'), ('Jobs', 'reviews.jobs'), ('Requests sent', 'reviews.requests_sent'), ('Request rate', 'reviews.request_rate'), ('Jobs with no request', 'reviews.not_requested')) + [
        FF('Requests needed for your review target', 'IFERROR(ROUNDUP({set:review_target}*INDEX({range:reviews.jobs},MATCH({pick},{range:reviews.row_id},0))/INDEX({range:reviews.per_request},MATCH({pick},{range:reviews.row_id},0)),0),0)', 'int')]),
    FORM('review_received_sheet', 'Review Received Sheet', 'Reviews received by one technician in a period', 'rev_tech.row_id', F(
        ('Technician', 'rev_tech.technician'), ('Period', 'rev_tech.period'), ('Jobs', 'rev_tech.jobs'), ('Reviews received', 'rev_tech.reviews'), ('Jobs to reviews', 'rev_tech.conversion'), ('Reviews per request', 'rev_tech.per_request'),
        ('Gap to the target', 'rev_tech.gap_to_target'), ('Technician phone', 'rev_tech.tech_phone'))),
    FORM('referral_sheet', 'Referral Sheet', 'Referrals of one month', 'rev_month.month', F(
        ('Month', 'rev_month.month'), ('Jobs', 'rev_month.jobs'), ('Referrals', 'rev_month.referrals'), ('Reviews received', 'rev_month.reviews')) + [
        FF('Referrals per 100 jobs', 'IFERROR(INDEX({range:rev_month.referrals},MATCH({pick},{range:rev_month.month},0))/INDEX({range:rev_month.jobs},MATCH({pick},{range:rev_month.month},0))*100,0)', 'num')]),
    FORM('thank_you_sheet', 'Thank-you Sheet', 'Thank-you notes owed to a technician month', 'tech_month.row_id', F(
        ('Technician', 'tech_month.technician'), ('Month', 'tech_month.month'), ('Reviews received', 'tech_month.reviews'), ('Referrals', 'tech_month.referrals'), ('Technician phone', 'tech_month.tech_phone')) + [
        FF('Thank-you notes to send', 'INDEX({range:tech_month.reviews},MATCH({pick},{range:tech_month.row_id},0))+INDEX({range:tech_month.referrals},MATCH({pick},{range:tech_month.row_id},0))', 'int')]),
    FORM('renewal_date_sheet', 'Renewal Date Sheet', 'One renewal date with days left and band', 'dates.licence_id', F(
        ('Item', 'dates.item'), ('Holder', 'dates.holder'), ('Due date', 'dates.due_date'), ('Cost', 'dates.cost'), ('Status', 'dates.status'), ('Days left', 'dates.days_left'), ('Band', 'dates.band'), ('Handled by', 'dates.handled_by'))),
    FORM('renewal_done_sheet', 'Renewal Done Sheet', 'Record a renewal that is done', 'dates.licence_id', F(
        ('Item', 'dates.item'), ('Holder', 'dates.holder'), ('Due date', 'dates.due_date'), ('Cost', 'dates.cost'), ('Next due date after renewal', 'dates.next_due')) + [
        FF('Days from today to the due date', 'INDEX({range:dates.due_date},MATCH({pick},{range:dates.licence_id},0))-{today}', 'int'),
        FF('Cost if it rises 10 percent', 'INDEX({range:dates.cost},MATCH({pick},{range:dates.licence_id},0))*1.1', 'money')]),
    FORM('scorecard_sheet', 'Owner Scorecard Sheet', 'One scorecard measure against target and history', 'scorecard.measure', F(
        ('Unit', 'scorecard.unit'), ('Value', 'scorecard.value'), ('Target', 'scorecard.target'), ('Own last 12 months', 'scorecard.own12'), ('Same time last year', 'scorecard.ly'), ('Light', 'scorecard.light'), ('Trend', 'scorecard.trend'),
        ('Gap to target, % of target', 'scorecard.gap_pct'), ('Money behind the gap, a year', 'scorecard.money_at_stake'), ('Note', 'scorecard.note'))),
    FORM('monday_sheet', 'Monday Meeting Sheet', 'One Monday action with owner and date', 'actions.rank', F(
        ('Measure', 'actions.measure'), ('Light', 'actions.light'), ('Action', 'actions.action'), ('Owner', 'actions.owner'), ('Due', 'actions.due'), ('Money at stake', 'actions.money'))),
    FORM('target_sheet', 'Target Setting Sheet', 'One target with its typical and own range', 'targets.setting', F(
        ('Target', 'targets.target'), ('Typical range', 'targets.typical_range'), ('Own highest, 12 months', 'targets.own_high'), ('Own lowest, 12 months', 'targets.own_low'), ('Check', 'targets.check'))),
    FORM('start_sheet', 'Start Here Setup Sheet', 'One first-week step', 'start_steps.step', F(
        ('What to do', 'start_steps.what'), ('Tab', 'start_steps.tab')) + [FF('Steps in the first week', 'COUNTA({range:start_steps.step})', 'int')]),
]
assert len(forms) == 12
documents = [
    DOC('scorecard_doc', 'Scorecard Print', 'Owner scorecard, one page for a month', 'hist.month', [
        'Owner scorecard of {set:company}, dated {today}. Month starting {col:hist.month}. The current month is month to date.',
        'Job margin {col:hist.margin} against {set:margin_target}. Net profit {col:hist.net_pct} against {set:net_target}. Utilisation {col:hist.utilisation} against {set:util_target}. Callback rate {col:hist.callbacks} and highest technician {col:hist.top_callback} against {set:callback_target}.',
        'Close rate {col:hist.close_rate} against {set:close_target}. Watched job type margin {col:hist.watch_margin} against {set:watch_margin_target}. Open over 60 days {col:hist.ageing60} against {set:ageing_limit}.',
        'Renewals done {col:hist.renewals}. Tune-ups done {col:hist.tuneups}. Cash after the largest bill {col:hist.cash_after} against {set:cash_floor}. Cash cover {col:hist.cash_cover} months. Measures at target: {col:hist.greens} of 12.'], SG, NOTE),
    DOC('monday_doc', 'Monday Agenda', 'Monday meeting agenda and actions', 'actions.rank', [
        'Monday meeting of {set:company}, dated {today}. Agenda: read the scorecard, agree the actions, set owners and dates.',
        'Action {col:actions.rank}: {col:actions.measure}, light {col:actions.light}. {col:actions.action}.', 'Owner: {col:actions.owner}. Due: {col:actions.due}. Money behind the gap, a year: {col:actions.money}.',
        'Decisions and notes are written below.'], SG, NOTE),
    DOC('source_doc', 'Lead Source Report', 'Lead source report for one period', 'src_results.row_id', [
        'Lead source report of {set:company}, dated {today}. Source: {col:src_results.source}. Period: {col:src_results.period}.',
        'Spend {col:src_results.spend}. Calls {col:src_results.calls}. Booked jobs {col:src_results.booked}. Sold jobs {col:src_results.sold}. Revenue {col:src_results.revenue}.',
        'Cost per booked job {col:src_results.cost_per_booked}. Revenue per spend {col:src_results.revenue_per_spend}. Verdict: {col:src_results.verdict}.', 'The decision for the next quarter is written below.'], SG, NOTE),
    DOC('budget_plan_doc', 'Marketing Budget Plan', 'Marketing budget plan for the year', 'cpb_month.month', [
        'Marketing budget plan of {set:company}, dated {today}. Reference month {col:cpb_month.month}.',
        'Monthly budget wanted: {set:marketing_budget}. Spend in the reference month: {col:cpb_month.spend}. Booked jobs: {col:cpb_month.booked}. Cost per booked job: {col:cpb_month.cost_per_booked}, target {set:lead_cost_target}.',
        'The amount for each source and each month of the year is written below.', 'Review the plan every quarter against revenue per spend.'], SG, NOTE),
    DOC('request_script_doc', 'Review Request Script', 'Review request script for a technician', 'tech_month.row_id', [
        'Review request script of {set:company}, dated {today}. Technician {col:tech_month.technician}, month {col:tech_month.month}: {col:tech_month.requests} requests for {col:tech_month.jobs} jobs.',
        'Say: "Thank you for choosing us today. If you were happy with the visit, would you leave a short review? It takes a minute and it helps a small team."',
        'Ask after every completed job, in person or by text. Do not ask while the customer is upset; note it for the office instead.', 'Notes are written below.'], ['Technician', 'Office manager'], NOTE),
    DOC('thanks_doc', 'Referral Thank-you Note', 'Referral thank-you note for a customer', 'jobs.job_id', [
        'Thank-you note of {set:company}, dated {today}. Site reference {col:jobs.site_ref}.', 'Thank you for recommending us. Your visit on {col:jobs.date} was looked after by {col:jobs.technician}, and we are glad you trusted us with a neighbour or friend.',
        'We appreciate it. Call us any time.', 'A personal line is written below.'], ['Owner'], NOTE),
    DOC('calendar_doc', 'Renewal Dates Calendar', 'Renewal date entry for the calendar', 'dates.licence_id', [
        'Renewal calendar entry of {set:company}, dated {today}. Item: {col:dates.item}. Holder: {col:dates.holder}.', 'Due date {col:dates.due_date}. Status {col:dates.status}. Days left {col:dates.days_left}. Band {col:dates.band}. Cost {col:dates.cost}.',
        'Handled by {col:dates.handled_by}. Check your local rules for what the renewal needs.', 'Notes are written below.'], SG, NOTE),
    DOC('renewal_budget_doc', 'Yearly Renewal Budget', 'Yearly renewal budget line for a month', 'ren_budget.month', [
        'Yearly renewal budget of {set:company}, dated {today}. Month starting {col:ren_budget.month}.', 'Renewals due {col:ren_budget.due}. Cost {col:ren_budget.cost}. Running total {col:ren_budget.running}. Share of the year {col:ren_budget.share}.',
        'Cost of the next 12 months: {col:ren_budget.year_cost}. Confirm tax treatment with your adviser.', 'Notes are written below.'], ['Owner', 'Accountant'], NOTE),
    DOC('start_doc', 'Start Here Sheet', 'Start here sheet: first week steps', 'start_steps.step', [
        'Start here sheet of {set:company}, dated {today}. First step: {col:start_steps.step}.', 'What to do: {col:start_steps.what}. Tab: {col:start_steps.tab}.',
        'One owner-operator with one van uses the same sheets; a shop with a dispatcher uses the dispatcher columns.', 'Tick each step when it is done.'], ['Owner'], NOTE),
    DOC('replace_doc', 'Replace Demo Data Guide', 'Guide to replace the demo data', 'start_steps.step', [
        'Replace demo data guide of {set:company}, dated {today}. Step: {col:start_steps.step}, on the tab {col:start_steps.tab}.', 'Clear the sample rows of that tab, keep the column headings and type your own rows. Calculated columns fill in by themselves.',
        'Do not type in white or grey calculated cells. Settings hold your company name and targets.', 'Note the date you finished each tab below.'], ['Owner'], NOTE),
    DOC('targets_doc', 'Targets Sheet', 'Targets sheet with typical ranges', 'targets.setting', [
        'Targets sheet of {set:company}, dated {today}. Measure: {col:targets.setting}.', 'Target {col:targets.target}. Typical range: {col:targets.typical_range} (a typical range, check your own numbers).',
        'Your own highest month {col:targets.own_high}, lowest month {col:targets.own_low}. Check: {col:targets.check}.', 'The target agreed and the date are written below.'], SG, NOTE),
    DOC('year_doc', 'Year in Review', 'Year in review for the accountant and the owner', 'hist.month', [
        'Year in review of {set:company}, dated {today}. Month starting {col:hist.month}.', 'Net profit {col:hist.net_pct}. Job margin {col:hist.margin}. Cash at month end {col:hist.cash}. Fixed costs a month {col:hist.fixed_cost}. Cash cover {col:hist.cash_cover} months.',
        'Open over 60 days {col:hist.ageing60}. Measures at target {col:hist.greens} of 12. Confirm tax and pay matters with your adviser.', 'Notes for the accountant are written below.'], ['Owner', 'Accountant'], NOTE),
]
assert len(documents) == 12
checklists = [
    CHK('monday_review', 'Monday Scorecard Review', 'hist', 'hist.month', [('Open the scorecard', 0), ('Read the reds and ambers', 0), ('Name the weakest link', 0), ('Open Monday Actions', 0), ('Agree an owner and a date for each', 0), ('Print the page', 0)]),
    CHK('weekly_source', 'Weekly Lead Source Check', 'marketing', 'marketing.month', [('Update spend for each source', 0), ('Update calls and booked jobs', 1), ('Read the source results', 2), ('Note a source to renegotiate', 3), ('Tell the office manager', 4)]),
    CHK('monthly_marketing', 'Monthly Marketing Review', 'cpb_month', 'cpb_month.month', [('Close the month of spend', 1), ('Read cost per booked job', 2), ('Compare with the target', 3), ('Decide keep, renegotiate or drop', 5), ('Plan next month budget', 7)]),
    CHK('requests_sent', 'Review Requests Sent', 'jobs', 'jobs.date', [('List completed jobs with no request', 0), ('Send the requests today', 0), ('Ask the technicians to ask in person', 1), ('Count reviews received', 7), ('Thank the customers who replied', 8)]),
    CHK('referral_thanked', 'Referral Thanked', 'jobs', 'jobs.date', [('Note the referral on the job', 0), ('Send the thank-you note', 1), ('Tell the technician', 2), ('Record the referral count', 3)]),
    CHK('renewal_check', 'Renewal Date Check', 'dates', 'dates.due_date', [('Open the register', -60), ('Mark items inside 60 days', -60), ('Ask for quotes', -45), ('Tell the owner the cost', -30), ('Start the renewal', -21)]),
    CHK('renewal_done', 'Renewal Done and Recorded', 'dates', 'dates.due_date', [('Pay the renewal', -14), ('Keep the new paperwork', -7), ('Write the renewed date', -3), ('Check the next due date', 0), ('Update the cost', 1)]),
    CHK('target_review', 'Target Review, Quarterly', 'hist', 'hist.month', [('Read your own best and worst months', 0), ('Compare targets with the typical ranges', 2), ('Change a target in Settings', 3), ('Tell the team', 5), ('Write the date', 5)]),
    CHK('start_week', 'Start Here, First Week', 'src_month', 'src_month.month', [('Replace the demo data', 0), ('Set your targets', 1), ('Enter your sources', 2), ('Enter 10 jobs', 3), ('Read the scorecard', 5), ('Hold the Monday meeting', 7)]),
    CHK('replace_demo', 'Replace Demo Data', 'rev_month', 'rev_month.month', [('Type your company name', 0), ('Clear the sample rows tab by tab', 1), ('Enter your own rows', 2), ('Check the calculated columns', 3), ('Delete what you do not use', 4)]),
    CHK('year_end', 'Year-End Review', 'hist', 'hist.month', [('Print the scorecard history', 0), ('Review marketing by source', 3), ('Review renewals paid', 5), ('Send the accountant the year', 7), ('Set next year targets', 10)]),
    CHK('slow_season', 'Slow-Season Planning', 'cpb_month', 'cpb_month.month', [('Read last year slow months', 0), ('Plan tune-up and agreement offers', 3), ('Plan marketing for the slow months', 5), ('Check cash against the floor', 7), ('Tell the team', 10)]),
]
assert len(checklists) == 12
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('c_thanks', 'Customer: thank you, would you leave a short review', 'jobs', 'jobs.phone', 'Hello, thank you for choosing {company} for your visit at {site_ref}. Would you leave us a short review? It helps a small team.'),
    M('c_invoice', 'Customer: your invoice carries a review note', 'jobs', 'jobs.phone', 'Hello, the invoice from {company} for {site_ref} has a short note on how to leave a review. Thank you.'),
    M('c_referral', 'Customer: thank you for the referral', 'jobs', 'jobs.phone', 'Hello, thank you for recommending {company}. We appreciate your trust at {site_ref}.'),
    M('c_neighbour', 'Customer: a thank-you for referring a neighbour', 'jobs', 'jobs.phone', 'Hello, {company} says thank you for recommending us to a neighbour. A small thank-you is waiting at your next visit, {site_ref}.'),
    M('c_feedback', 'Customer: we would love your feedback', 'jobs', 'jobs.phone', 'Hello, {company} would love your feedback on the {job_type} visit at {site_ref}. A few words by reply are enough.'),
    M('c_how', 'Customer: how did we do on your last visit', 'jobs', 'jobs.phone', 'Hello, how did {technician} and {company} do on your last visit at {site_ref}? A short reply helps us.'),
    M('l_recommend', 'Landlord account: would you recommend us to other landlords', 'jobs', 'jobs.phone', 'Hello, {company} looks after account {account}. Would you recommend us to other landlords you know?'),
    M('l_reference', 'Landlord account: thank you for your reference', 'jobs', 'jobs.phone', 'Hello, thank you for your reference on account {account}. {company} values your trust.'),
    M('t_requests', 'Technician: your review requests this month', 'tech_month', 'tech_month.tech_phone', 'Hello {technician}, your review requests in {month}: {requests} for {jobs} jobs. {company}'),
    M('t_reviews', 'Technician: you received reviews this month', 'tech_month', 'tech_month.tech_phone', 'Hello {technician}, you received {reviews} reviews in {month}. Thank you. {company}'),
    M('t_every', 'Technician: please send a request after every completed job', 'tech_month', 'tech_month.tech_phone', 'Hello {technician}, please send a review request after every completed job. In {month} you asked for {requests} of {jobs} jobs. {company}'),
    M('t_referrals', 'Technician: your referrals this month', 'tech_month', 'tech_month.tech_phone', 'Hello {technician}, your referrals in {month}: {referrals}. Thank you. {company}'),
    M('a_ask', 'Apprentice: please ask for a review after the job with your lead', 'jobs', 'jobs.assistant_phone', 'Hello {assistant}, please ask for a review after the job with {technician} at {site_ref}. {company}'),
    M('om_unsent', 'Office manager: review requests not sent', 'rev_month', 'rev_month.office_phone', 'Review requests not sent in {month}: {not_sent} of {jobs} jobs. Please send them today. {company}'),
    M('om_renewals', 'Office manager: renewals due in 30 days', 'dates', 'dates.office_phone', '{due_30} renewals are due in the next 30 days. Please check Renewal Dates. {company}'),
    M('om_monday', 'Office manager: the Monday actions are ready', 'actions', 'actions.office_phone', 'The Monday actions are ready. Action {rank}: {action}, due {due}. {company}'),
    M('om_spend', 'Office manager: please update spend for a source', 'marketing', 'marketing.office_phone', 'Please update the spend for {source} for {month}. {company}'),
    M('ow_cost', 'Owner: a source costs this much per booked job', 'src_results', 'src_results.owner_phone', '{source} costs {cost_per_booked} per booked job ({period}). Please check it against your target. {company}'),
    M('ow_best', 'Owner: a source has the best revenue per spend', 'src_results', 'src_results.owner_phone', '{source} has revenue per spend of {revenue_per_spend} ({period}). {company}'),
    M('ow_cut', 'Owner: cut or renegotiate a source', 'src_results', 'src_results.owner_phone', 'Verdict for {source} ({period}): {verdict}. Cut or renegotiate if revenue per spend stays low. {company}'),
    M('ow_score', 'Owner: the scorecard is ready', 'scorecard', 'scorecard.owner_phone', 'The scorecard is ready. {measure}: {value} against {target}, light {light}. {company}'),
    M('ow_renewal', 'Owner: a renewal is due', 'dates', 'dates.owner_phone', '{item} for {holder} is due in {days_left} days, cost {cost}. {company}'),
    M('ow_yearly', 'Owner: yearly renewals cost', 'ren_budget', 'ren_budget.owner_phone', 'Renewals cost {year_cost} over the next 12 months; {month} is {cost}. {company}'),
    M('ow_spend', 'Owner: marketing spend this month', 'cpb_month', 'cpb_month.owner_phone', 'Marketing in {month}: spend {spend}, {booked} booked jobs, {cost_per_booked} each. {company}'),
    M('ow_reviews', 'Owner: reviews this month', 'rev_month', 'rev_month.owner_phone', 'Reviews in {month}: {reviews} from {jobs} jobs. {company}'),
    M('ow_targets', 'Owner: your targets changed', 'targets', 'targets.owner_phone', 'Your target for {setting} is {target}. Checked on {today_date}. {company}'),
    M('s_lead', 'Equipment supplier: lead times for the season', 'cpb_month', 'cpb_month.supplier_phone', 'Hello, {company} would like your equipment lead times for {month}. Please send them when you can.'),
    M('p_discount', 'Parts counter: referral discount for an account', 'jobs', 'jobs.parts_phone', 'Hello, please apply the referral discount for account {account}, site {site_ref}. {company}'),
    M('e_dates', 'Electrical subcontractor: send your renewal dates', 'dates', 'dates.elec_phone', 'Hello, please send {company} your licence renewal dates so we can keep them on file.'),
    M('sm_insure', 'Sheet-metal subcontractor: confirm your insurance renewal', 'dates', 'dates.sheet_phone', 'Hello, please confirm your insurance renewal date to {company}. We keep it on file.'),
    M('ac_budget', 'Accountant: renewal costs for the budget', 'ren_budget', 'ren_budget.acct_phone', 'Hello, renewal costs for {month}: {cost}; {year_cost} for the next 12 months. {company}'),
    M('ac_score', 'Accountant: scorecard for the quarter', 'hist', 'hist.acct_phone', 'Hello, the scorecard for {month} is ready: {greens} of 12 measures at target. {company}'),
    M('in_quote', 'Insurance agent: a renewal is coming, send the quote', 'dates', 'dates.agent_phone', 'Hello, {item} for {holder} renews on {due_date}. Please send the quote. {company}'),
    M('in_vans', 'Insurance agent: confirm the cover for new vans', 'dates', 'dates.agent_phone', 'Hello, {company} adds vans over the year. Please confirm the cover for {holder} ({item}), due {due_date}.'),
]
assert len(messages) == 34, len(messages)

def PW(n, tbl='marketing', col='month'): return '{range:%s.%s},">="&%s' % (tbl, col, EM(-n))
def JW(n): return '{range:jobs.date},">="&({today}-%d),{range:jobs.date},"<="&{today}' % n
def SCV(i, c): return 'INDEX({range:scorecard.%s},%d)' % (c, i)
kpis = [
    KPI('Marketing spend this month', 'SUMIFS({range:marketing.spend},{range:marketing.month},%s)' % MS, 'money'),
    KPI('Marketing spend, last 12 months', 'SUMIFS({range:marketing.spend},%s)' % PW(11), 'money'),
    KPI('Calls from marketing, last 3 months', 'SUMIFS({range:marketing.calls},%s)' % PW(2), 'int'),
    KPI('Booked jobs from marketing, 3 months', 'SUMIFS({range:marketing.booked},%s)' % PW(2), 'int'),
    KPI('Cost per lead, last 3 months', 'IFERROR(SUMIFS({range:marketing.spend},%s)/SUMIFS({range:marketing.calls},%s),0)' % (PW(2), PW(2)), 'money'),
    KPI('Cost per booked job, last 3 months', 'IFERROR(SUMIFS({range:marketing.spend},%s)/SUMIFS({range:marketing.booked},%s),0)' % (PW(2), PW(2)), 'money'),
    KPI('Cost per booked job against the target', 'IFERROR(SUMIFS({range:marketing.spend},%s)/SUMIFS({range:marketing.booked},%s),0)-{set:lead_cost_target}' % (PW(2), PW(2)), 'money'),
    KPI('Revenue per spend, last 12 months', 'IFERROR(SUMIFS({range:marketing.revenue},%s)/SUMIFS({range:marketing.spend},%s),0)' % (PW(11), PW(11)), 'num'),
    KPI('Best source, revenue per spend', 'LARGE({range:src_results.rank_key},1)', 'num'),
    KPI('Weakest source, revenue per spend', 'SMALL({range:src_results.rank_key},1)', 'num'),
    KPI('Calls from referrals, last 30 days', 'IFERROR(COUNTIFS({range:calls.source},%s,{range:calls.date},">="&({today}-30))/COUNTIFS({range:calls.date},">="&({today}-30)),0)' % tok('source', 'Referral'), 'pct'),
    KPI('Calls from repeat customers, 30 days', 'IFERROR(COUNTIFS({range:calls.source},%s,{range:calls.date},">="&({today}-30))/COUNTIFS({range:calls.date},">="&({today}-30)),0)' % tok('source', 'Repeat customer'), 'pct'),
    KPI('Review requests, last 30 days', 'COUNTIFS({range:jobs.request_sent},%s,%s)' % (YES, JW(30)), 'int'),
    KPI('Reviews received, last 30 days', 'COUNTIFS({range:jobs.reviewed},%s,%s)' % (YES, JW(30)), 'int'),
    KPI('Review conversion, last 3 months', 'IFERROR(SUMIFS({range:reviews.reviews_received},%s)/SUMIFS({range:reviews.jobs},%s),0)' % (PW(2, 'reviews'), PW(2, 'reviews')), 'pct'),
    KPI('Referrals, last 3 months', 'SUMIFS({range:reviews.referrals},%s)' % PW(2, 'reviews'), 'int'),
    KPI('Jobs with no review request, 30 days', 'COUNTIFS({range:jobs.status},%s,{range:jobs.request_sent},%s,%s)' % (COMP, NO, JW(30)), 'int'),
    KPI('Renewals due in 30 days', 'COUNTIFS({range:dates.status},%s,{range:dates.due_date},">="&{today},{range:dates.due_date},"<="&({today}+30))' % OPEN, 'int'),
    KPI('Renewals due in 60 days', 'COUNTIFS({range:dates.status},%s,{range:dates.due_date},">="&{today},{range:dates.due_date},"<="&({today}+60))' % OPEN, 'int'),
    KPI('Renewals overdue', 'COUNTIFS({range:dates.status},%s,{range:dates.due_date},"<"&{today})' % OPEN, 'int'),
    KPI('Renewal cost, next 12 months', 'SUM({range:ren_budget.cost})', 'money'),
    KPI('Renewal cost, next 90 days', 'SUMIFS({range:dates.cost},{range:dates.status},%s,{range:dates.due_date},">="&{today},{range:dates.due_date},"<="&({today}+90))' % OPEN, 'money'),
    KPI('Scorecard measures green', 'COUNTIFS({range:scorecard.light},%s)' % G, 'int'),
    KPI('Scorecard measures amber', 'COUNTIFS({range:scorecard.light},%s)' % AM, 'int'),
    KPI('Scorecard measures red', 'COUNTIFS({range:scorecard.light},%s)' % RD, 'int'),
    KPI('Weakest scorecard gap, % of target', 'MAX({range:scorecard.gap_pct})', 'num'),
    KPI('Net profit against the target, points', SCV(2, 'value') + '-' + SCV(2, 'target'), 'num'),
    KPI('Utilisation against the target, points', SCV(3, 'value') + '-' + SCV(3, 'target'), 'num'),
    KPI('Callback rate against the target, points', SCV(4, 'value') + '-' + SCV(4, 'target'), 'num'),
    KPI('Cash cover against the target, months', SCV(12, 'value') + '-' + SCV(12, 'target'), 'num'),
]
assert len(kpis) == 30
dashboard = {"title": "Leads and Scorecard Dashboard", "kpis": kpis,
    "monthly": {"title": "Spend, booked jobs and revenue by month", "date": "cpb_month.month", "series": [
        {"label": "Marketing spend", "sum": "cpb_month.spend", "date": "cpb_month.month"}, {"label": "Booked jobs", "sum": "cpb_month.booked", "date": "cpb_month.month"}, {"label": "Revenue", "sum": "cpb_month.revenue", "date": "cpb_month.month"}]},
    "breakdowns": [{"title": "Calls by source", "by": "marketing.source", "value": "marketing.calls", "agg": "sum"}, {"title": "Revenue by source", "by": "marketing.source", "value": "marketing.revenue", "agg": "sum"},
                   {"title": "Reviews by technician", "by": "reviews.technician", "value": "reviews.reviews_received", "agg": "sum"}, {"title": "Renewal cost by item", "by": "dates.item", "value": "dates.cost", "agg": "sum"}]}
def CM(title, typ, tbl, col, label, agg='sum', dcol=None): return CHART(title, typ, 'month', [AGG(agg, tbl, '%s.%s' % (tbl, col), date='%s.%s' % (tbl, dcol or 'month'), label=label)])
def CB(title, tbl, by, val, label, agg='sum', where=None): return CHART(title, 'bar', '%s.%s' % (tbl, by), [AGG(agg, tbl, '%s.%s' % (tbl, val) if agg != 'count' else None, where=where, label=label)])
insights = {"filters": [{"label": "Technician", "list": "tech"}, {"label": "Source", "list": "source"}],
    "gauges": [{"title": "Technicians at the review target", "num": AGG('count', 'rev_tech', where=[('period', '=', tok('period', 'Last 12 months')), ('conversion', '>=', '{set:review_target}')]), "den": AGG('count', 'rev_tech', where=[('period', '=', tok('period', 'Last 12 months'))])},
               {"title": "Renewals done on time", "num": AGG('count', 'dates', where=[('on_time', '=', 1)]), "den": AGG('count', 'dates', where=[('status', '=', tok('rnstatus', 'Renewed'))])},
               {"title": "Scorecard measures green", "num": AGG('count', 'scorecard', where=[('light', '=', G)]), "den": AGG('count', 'scorecard')},
               {"title": "Months within the marketing budget", "num": AGG('count', 'cpb_month', where=[('spend', '<=', '{set:marketing_budget}')]), "den": AGG('count', 'cpb_month')},
               {"title": "Months at or under cost target", "num": AGG('count', 'cpb_month', where=[('cost_per_booked', '<=', '{set:lead_cost_target}')]), "den": AGG('count', 'cpb_month')},
               {"title": "Completed jobs with a review request", "num": AGG('count', 'jobs', where=[('status', '=', COMP), ('request_sent', '=', YES)]), "den": AGG('count', 'jobs', where=[('status', '=', COMP)])}],
    "charts": [
        CM('Marketing spend per month', 'column', 'cpb_month', 'spend', 'Marketing spend'), CB('Marketing spend by source', 'marketing', 'source', 'spend', 'Spend'), CB('Calls by source', 'marketing', 'source', 'calls', 'Calls'),
        CB('Booked jobs by source', 'marketing', 'source', 'booked', 'Booked jobs'), CB('Revenue by source', 'marketing', 'source', 'revenue', 'Revenue'),
        CM('Cost per booked job per month', 'line', 'cpb_month', 'cost_per_booked', 'Cost per booked job', 'avg'), CM('Revenue per spend per month', 'line', 'cpb_month', 'revenue_per_spend', 'Revenue per spend', 'avg'),
        CM('Calls from marketing per month', 'column', 'src_month', 'calls', 'Calls'), CM('Reviews received per month', 'column', 'rev_month', 'reviews', 'Reviews received'), CM('Review requests per month', 'column', 'rev_month', 'requests', 'Requests sent'),
        CB('Reviews by technician', 'reviews', 'technician', 'reviews_received', 'Reviews received'), CM('Referrals per month', 'column', 'rev_month', 'referrals', 'Referrals'), CB('Referrals by technician', 'reviews', 'technician', 'referrals', 'Referrals'),
        CM('Review conversion per month', 'line', 'rev_month', 'conversion', 'Jobs to reviews', 'avg'), CB('Renewals by status', 'dates', 'status', None, 'Renewals', 'count'), CB('Renewals by item', 'dates', 'item', None, 'Renewals', 'count'),
        CM('Renewal cost per month', 'column', 'ren_budget', 'cost', 'Renewal cost'), CM('Renewals due by month', 'column', 'ren_budget', 'due', 'Renewals due'),
        CB('Scorecard gap to target by measure', 'scorecard', 'measure', 'gap_pct', 'Gap, % of target', 'avg'), CM('Margin percent per month', 'line', 'hist', 'margin', 'Job margin', 'avg'),
        CM('Utilisation per month', 'line', 'hist', 'utilisation', 'Utilisation', 'avg'), CM('Cash cover per month', 'line', 'hist', 'cash_cover', 'Cash cover, months', 'avg')]}
assert len(insights['charts']) == 22
signature = [
    {"name": "Lead Source Ranker", "why": "every source ranked by revenue per spend with a keep, renegotiate or drop verdict and the money moved if the weakest is cut", "where": "Lead Source Ranker"},
    {"name": "Cost per Booked Job Tool", "why": "a source that is cheap per lead but costly per booked job shows up against your target", "where": "Cost per Booked Job Tool"},
    {"name": "Marketing Budget Split Planner", "why": "move a monthly budget between two sources and see the booked jobs and margin it moves, with base, best and worst rows", "where": "Marketing Budget Split Planner"},
    {"name": "Review Request Gap Finder", "why": "completed jobs with no review request by technician and week, the number to send today and the extra reviews it brings", "where": "Review Request Gap Finder"},
    {"name": "Renewal Dates Register", "why": "licence, insurance, registration, inspection and training dates in red under 30 days, amber under 60 and green later, with the first three to act on", "where": "Renewal Dates Register"},
    {"name": "Owner Scorecard", "why": "twelve measures each green, amber or red against your targets and your own last 12 months, with a one-line note and the money behind each gap", "where": "Owner Scorecard"},
    {"name": "Scorecard Weakest Link", "why": "the measure furthest below its target as a share of the target, with the action, the owner and the money behind it", "where": "Scorecard Weakest Link"},
    {"name": "Monday Actions Builder", "why": "the five largest gaps become actions with an owner, a due date and the money at stake, printed as one page for the Monday meeting", "where": "Monday Actions Builder"},
    {"name": "Seasonal Lead Forecast", "why": "calls, booked jobs and spend for the next 12 weeks from the same months last year, by source", "where": "Seasonal Lead Forecast"},
    {"name": "Own-History Comparison", "why": "every measure now against the period before, your last 12 months and the same time last year, improving or slipping", "where": "Own-History Comparison"}]
competitors = [
    {"what": "field-service app with a per-technician fee", "lacks": "charges for every person, keeps lead spend and the scorecard behind extra plans and shows no verdict per lead source or per renewal date"},
    {"what": "generic invoice template", "lacks": "writes a bill but tracks no lead source, no review requests, no renewal dates and no scorecard"},
    {"what": "single-sheet quote calculator", "lacks": "prices one job but cannot rank sources by revenue per spend or show callbacks, cash and margin in one place"},
    {"what": "pen-and-paper job book", "lacks": "forgets renewal dates and review requests and gives no Monday page of actions with money behind each one"}]
guide = [
    'Open Start and type your company name and your own limits in the yellow cells: targets for margin, utilisation, callbacks, close rate, reviews and cash cover, and the red and amber days for renewals.',
    'Check Lead Sources and Technicians. They hold the sources, what each costs a month and the six lead technicians the review sheets use.',
    'Enter each month of each source on Marketing Spend: spend, calls, booked jobs, sold jobs and revenue. Cost per lead, cost per booked job and revenue per spend fill in by themselves.',
    'Read Source Results: each source for 3 months, 12 months and the 12 before, with a keep, renegotiate or drop verdict from the limits in Settings.',
    'Enter recent jobs on Jobs with source, price, margin and whether a review was asked for and received. Enter Reviews and Referrals counts for each technician and month.',
    'List every licence, insurance, registration, inspection and training date on Renewal Dates. Days left and the red, amber or green band fill in; Renewal Budget shows the cost by month.',
    'Fill Scorecard History with one row for each month. Scorecard turns it into twelve measures with lights, trends and the money behind each gap; Targets shows your own best and worst month.',
    'Open Monday Actions: the largest gaps become actions with an owner, a date and the money at stake. Print the first five for the Monday meeting.',
    f'Use the {len(tools)} tools: each answers one question with a verdict. Change the yellow inputs to try another source, technician, renewal item or target.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Leads and Scorecard Dashboard and the Charts every week. A one-person owner-operator with one van uses the same sheets; a shop with a dispatcher uses the dispatcher columns.']
listing = {"title": "HVAC and Plumbing Contractor Excel Template: Lead Sources, Reviews, Renewal Dates, Owner Scorecard, Monday Actions",
    "headline": "Where work comes from and the one page you read on Monday",
    "tags": ["hvac template", "plumbing template", "owner scorecard", "lead source tracker", "marketing spend", "review tracker", "renewal dates", "contractor excel", "service business", "kpi dashboard", "cost per lead", "monday meeting", "tradesman"],
    "description": ("Know where your work comes from and what to fix this week, in one Excel workbook. Built for an owner-run residential and light-commercial HVAC and plumbing shop with 1 to 15 technicians. "
        "A one-person owner-operator with one van uses the same sheets; a shop with a dispatcher uses the dispatcher columns.\n\n"
        "Marketing Spend holds each source and month: spend, calls, booked jobs, sold jobs and revenue. Source Results ranks every source by revenue per spend with a keep, renegotiate or drop verdict, and the cost per booked job tool shows a source that is cheap per lead but costly per booked job. "
        "Reviews and Referrals keep counts only by technician and month, and the Review Request Gap Finder lists completed jobs with no request.\n\n"
        "Renewal Dates tracks licence, insurance, registration, inspection and training dates with red under 30 days, amber under 60 and green later, and Renewal Budget shows the cost by month. "
        "The Owner Scorecard reads twelve measures from your own history, each green, amber or red against targets you set, with the trend, a one-line note and the money behind the gap. The weakest link tool and Monday Actions turn the largest gaps into actions with an owner and a date.\n\n"
        f"{len(tools)} tools answer weekly questions with a clear verdict. Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to customers, landlord accounts, technicians, your office, your equipment supplier, the accountant and the insurance agent.\n\n"
        "This is part eight of the HVAC and Plumbing Contractor suite. A standard .xlsx workbook with no macros and no per-technician fee: you keep your data. A demo copy full of sample data and a blank copy are included. Targets are yours to set; a typical range is a place to start, check your own numbers. It helps you keep track of your business and does not promise results."),
    "features": ["Lead source ranker with keep, renegotiate or drop", "Cost per booked job against your target", "Marketing budget split planner", "Review request gap finder", "Renewal dates register with red and amber bands",
                 "Owner scorecard against targets and your own history", "Weakest link and Monday actions builder", "Seasonal lead forecast for 12 weeks", f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
TITLES = {'lead_ranker': 'Lead sources ranked: keep, renegotiate or drop', 'payback': 'Months to pay back a monthly marketing spend', 'review_tracker': 'Requests, reviews and referrals by technician',
          'review_gap': 'Completed jobs with no review request', 'renewal_register': 'Renewal dates: red under 30, amber under 60', 'renewal_actions': 'The next renewals, who handles them, when to start',
          'owner_scorecard': 'Twelve measures against targets and history', 'weakest_link': 'The measure furthest below its target', 'history_compare': 'Now against before, 12 months and last year'}
HINTS = {'lead_ranker': 'Pick a source and the share of its jobs that still arrive without spend: 12-month results, the best and weakest source and what cutting the weakest would move.',
 'budget_split': 'Pick the source to cut and the source to feed, the amount moved and how well extra spend works: jobs lost and gained, revenue and margin moved, with base, best and worst rows.',
 'referral_value': 'Type the average ticket, the cost of a thank-you and the most of a first-job margin you would spend: referrals of 12 months, their value and a verdict.',
 'renewal_budget': 'Type a yearly budget and a cost rise: renewal cost for the next 12 months with the rise, the month with the highest outflow and the budget left. Enter that outflow in your cash forecast.',
 'renewal_actions': 'Type the days ahead and the days of notice you need: open renewals in that window with cost, and the first three with who handles each and the date to start.',
 'owner_scorecard': 'Pick a measure: value, target, own 12 months, the period before, last year, light, trend and money behind the gap, with the green, amber and red counts of all twelve.',
 'weakest_link': 'Type 1 for the weakest measure, 2 for the second: value, target, gap as a share of the target, the money behind it, the action and its owner, and a verdict.',
 'monday_builder': 'Type the working days for the fifth action and the share of the gap you close: five actions with owner, due date and money at stake, and the money recovered a year.',
 'targets_tool': 'Pick a measure and type a trial target: the current target, typical range, your own highest and lowest month, months that would have met it and a check.',
 'history_compare': 'Pick a measure: value now, the period before, your last 12 months and last year, the changes and whether it is improving or slipping; all twelve trends are listed.'}
for _t in tools:
    if _t['key'] in TITLES: _t['title'] = TITLES[_t['key']]
    if _t['key'] in HINTS: _t['hint'] = HINTS[_t['key']]
MOM = {'c_thanks': 'Customer: would you leave a short review', 'c_invoice': 'Customer: review note on your invoice', 'c_neighbour': 'Customer: thanks for a referral', 'c_how': 'Customer: how did we do on your visit',
       'l_recommend': 'Landlord: would you recommend us', 'l_reference': 'Landlord: thank you for your reference', 't_requests': 'Technician: your review requests', 't_reviews': 'Technician: reviews you received',
       't_every': 'Technician: ask after every job', 'a_ask': 'Apprentice: ask for a review after a job', 'om_monday': 'Office manager: Monday actions ready', 'om_spend': 'Office manager: update source spend',
       'ow_cost': 'Owner: cost per booked job of a source', 'ow_best': 'Owner: best revenue per spend', 's_lead': 'Equipment supplier: season lead times', 'p_discount': 'Parts counter: referral discount',
       'e_dates': 'Electrical sub: send renewal dates', 'sm_insure': 'Sheet-metal sub: confirm insurance date', 'in_quote': 'Insurance agent: renewal, send the quote', 'in_vans': 'Insurance agent: cover for new vans'}
for _m in messages:
    if _m['key'] in MOM: _m['moment'] = MOM[_m['key']]
for _t in tables: _t['rows'] = max(_t['rows'], 50)
for _l in ('Spare label',):
    if len(CKL) % 30 == 1: ck(_l)
s = spec(id=f'{SUITE}-p8', slug='hvac-plumbing-leads-scorecard', profession='HVAC and Plumbing Contractor', name='Leads, Reviews, Renewals, Scorecard',
         tagline='Where work comes from and the one page you read on Monday', price_usd=29,
         colors={"primary": "#1F4E5F", "accent": "#E07A3F"}, settings=settings, lists=base_lists + ck_lists(), tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 8, "of": 8, "focus": "Leads, reviews, renewals and the owner scorecard"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hv8.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'lists', len(s['lists']))
