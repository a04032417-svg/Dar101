"""HVAC and plumbing contractor suite - part 2: Price Book, Estimates and Options."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv2_lists import *
from hv2_tables import settings, tables
from hv2_tools import tools

SUITE = 'fx-20261115-hvac-plumbing'
NOTE = "Sample wording: adapt it to your own business."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def FX(label, f, fmt): return FF(label, f, fmt)


def fields(t, *pairs): return [FV(a, '%s.%s' % (t, b)) for a, b in pairs]


forms = [
    FORM('estimate_sheet', 'Estimate Sheet', 'Estimate with options, value and follow-up', 'estimates.estimate_id', fields('estimates',
        ('Date', 'date'), ('Site reference', 'site_ref'), ('Phone', 'phone'), ('Account', 'account'), ('Job type', 'job_type'), ('Technician', 'technician'), ('Options offered', 'options_offered'),
        ('Good price', 'good_price'), ('Better price', 'better_price'), ('Best price', 'best_price'), ('Estimate value', 'est_value'), ('Valid until', 'valid_until'), ('Deposit', 'deposit'),
        ('Follow-up date', 'followup_date'), ('Follow-up check', 'followup_flag'), ('Outcome', 'outcome'))),
    FORM('options_sheet', 'Good-Better-Best Options Sheet', 'One option with cost, margin and monthly payment', 'option_lines.line_id', fields('option_lines',
        ('Estimate', 'estimate_id'), ('Option', 'option'), ('Job type', 'job_type'), ('Site reference', 'site_ref'), ('Technician', 'technician'), ('Price', 'price'), ('Cost', 'cost'), ('Margin', 'margin'),
        ('Target margin', 'target_margin'), ('Margin check', 'margin_flag'), ('Monthly payment', 'monthly_payment'), ('Deposit', 'deposit'))),
    FORM('line_sheet', 'Price Book Line Sheet', 'Price book line with cost build-up', 'price_book.pb_id', fields('price_book',
        ('Task', 'task'), ('Job type', 'job_type'), ('Labour hours', 'labour_hours'), ('Parts cost', 'parts_cost'), ('Permit fee', 'permit_fee'), ('Disposal', 'disposal'), ('Subcontract cost', 'sub_cost'),
        ('Cost, all in', 'cost'), ('Flat price', 'flat_price'), ('Previous price', 'previous_price'), ('Margin', 'margin'), ('Target margin', 'target_margin'), ('Margin check', 'status'), ('Price at target', 'price_needed'),
        ('Money lost per job', 'gap_money'), ('Margin lost a year', 'lost_year'))),
    FORM('change_sheet', 'Price Change Sheet', 'Supplier price change with the lines it touches', 'price_changes.change_id', fields('price_changes',
        ('Date', 'date'), ('Part ID', 'part_id'), ('Part', 'part'), ('Supplier', 'supplier'), ('Old cost', 'old_cost'), ('New cost', 'new_cost'), ('Rise', 'rise'), ('Price book lines using it', 'lines_hit'))),
    FORM('followup_sheet', 'Estimate Follow-up Sheet', 'Open estimate with the next call', 'open_est.rank_no', fields('open_est',
        ('Estimate', 'estimate_id'), ('Site reference', 'site_ref'), ('Technician', 'technician'), ('Job type', 'job_type'), ('Value', 'est_value'), ('Age in days', 'age_days'),
        ('Follow-up check', 'followup_flag'), ('Call next on', 'next_call'), ('Technician phone', 'tech_phone'))),
    FORM('decision_sheet', 'Estimate Decision Sheet', 'Decision, option chosen and days taken', 'estimates.estimate_id', fields('estimates',
        ('Date', 'date'), ('Job type', 'job_type'), ('Technician', 'technician'), ('Option chosen', 'option_chosen'), ('Outcome', 'outcome'), ('Price won', 'price_won'),
        ('Lost value', 'lost_value'), ('Days call to estimate', 'days_to_estimate'), ('Follow-up date', 'followup_date'), ('Follow-up check', 'followup_flag'), ('Valid until', 'valid_until'))),
    FORM('diag_sheet', 'Diagnostic Visit Sheet', 'Diagnostic visits of one month', 'diag_months.month', fields('diag_months',
        ('Diagnostic visits', 'visits'), ('Converted to repair', 'converted'), ('Conversion', 'conversion'), ('Fee income', 'fee_income'), ('Visit cost', 'visit_cost'), ('Cost per visit', 'cost_per_visit'), ('Fee less cost per visit', 'net_per_visit'))),
    FORM('quote_sheet', 'Phone Quote Sheet', 'Quote given by phone', 'quote_log.quote_id', fields('quote_log',
        ('Date', 'date'), ('Site reference', 'site_ref'), ('Phone', 'phone'), ('Job type', 'job_type'), ('Price quoted', 'price_quoted'), ('Outcome', 'outcome'), ('Price book average', 'book_price'),
        ('Against the book', 'vs_book'), ('Member price', 'member_price'), ('Deposit', 'deposit'))),
    FORM('member_sheet', 'Member Price Request Sheet', 'Member price range for a job type', 'job_types.job_type', fields('job_types',
        ('Trade', 'trade'), ('Kind', 'kind'), ('Price book lines', 'lines'), ('Lowest price', 'min_price'), ('Highest price', 'max_price'), ('Average price', 'avg_price'), ('Member price, average', 'member_avg'), ('Target margin', 'target_margin'))),
    FORM('finance_sheet', 'Financing Offer Sheet', 'Monthly payments for the three options', 'estimates.estimate_id', fields('estimates',
        ('Site reference', 'site_ref'), ('Job type', 'job_type'), ('Good price', 'good_price'), ('Better price', 'better_price'), ('Best price', 'best_price'), ('Monthly payment, good', 'monthly_good'),
        ('Monthly payment, better', 'monthly_better'), ('Monthly payment, best', 'monthly_best'), ('Deposit', 'deposit'))),
    FORM('review_sheet', 'Price Review Sheet', 'Price rise scenario with jobs you can lose', 'price_rise.rise_pct', fields('price_rise',
        ('Lines back on target', 'lines_fixed'), ('Extra margin a year', 'extra_margin'), ('Job loss allowed', 'loss_share'), ('Jobs to lose to break even', 'jobs_lost'))),
    FORM('lost_sheet', 'Lost Estimate Sheet', 'Lost estimates by reason', 'lost_reasons.reason', fields('lost_reasons', ('Lost estimates', 'estimates'), ('Lost value', 'lost_value')) + [
        FF('Share of all lost value', 'IFERROR(INDEX({range:lost_reasons.lost_value},MATCH({pick},{range:lost_reasons.reason},0))/SUM({range:lost_reasons.lost_value}),0)', 'pct'),
        FF('Average lost per estimate', 'IFERROR(INDEX({range:lost_reasons.lost_value},MATCH({pick},{range:lost_reasons.reason},0))/INDEX({range:lost_reasons.estimates},MATCH({pick},{range:lost_reasons.reason},0)),0)', 'money')]),
]
assert len(forms) == 12


def D_(key_, sheet, title, pick, paras, sign): return DOC(key_, sheet, title, pick, paras, sign, NOTE)
documents = [
    D_('three_options', 'Estimate with Three Options', 'Estimate with good, better and best', 'estimates.estimate_id', [
        'Estimate from {set:company}, dated {today}. Estimate {col:estimates.estimate_id} for {col:estimates.site_ref}, {col:estimates.job_type}, prepared by {col:estimates.technician} on {col:estimates.date}.',
        'Option good: {col:estimates.good_price}, about {col:estimates.monthly_good} a month with a financing offer. Option better: {col:estimates.better_price}, about {col:estimates.monthly_better} a month. Option best: {col:estimates.best_price}, about {col:estimates.monthly_best} a month.',
        'A deposit of {col:estimates.deposit} holds your date and is applied to the final invoice. The estimate is valid until {col:estimates.valid_until}. Prices are before sales tax and include parts and labour. Please check the current price before you decide.',
        'Monthly payments depend on your lender and are examples only.'], ['Contractor', 'Customer']),
    D_('repair_estimate', 'Estimate for a Repair', 'Estimate for one repair with price and deposit', 'quote_log.quote_id', [
        'Estimate from {set:company}, dated {today}. Quote {col:quote_log.quote_id} given on {col:quote_log.date} for {col:quote_log.site_ref}: {col:quote_log.job_type}.',
        'Price: {col:quote_log.price_quoted}, before sales tax. Member price: {col:quote_log.member_price}. A deposit of {col:quote_log.deposit} holds the date if one is asked.',
        'The diagnostic fee of {set:diag_fee} is credited if you go ahead. Please check the current price with us before work starts.'], ['Contractor', 'Customer']),
    D_('accepted', 'Estimate Accepted', 'Confirmation of the option accepted', 'option_lines.line_id', [
        'Confirmation from {set:company}, dated {today}. Thank you for choosing the {col:option_lines.option} option on estimate {col:option_lines.estimate_id} for {col:option_lines.site_ref}, {col:option_lines.job_type}.',
        'Price: {col:option_lines.price}, before sales tax. Deposit: {col:option_lines.deposit}. Monthly payment with a financing offer: about {col:option_lines.monthly_payment}.',
        'Technician: {col:option_lines.technician}. We will confirm the date and the arrival window in writing.'], ['Contractor', 'Customer']),
    D_('followup_letter', 'Estimate Follow-up Letter', 'Follow-up letter for an open estimate', 'open_est.rank_no', [
        'Letter from {set:company}, dated {today}. Estimate {col:open_est.estimate_id} for {col:open_est.site_ref}, {col:open_est.job_type}, value {col:open_est.est_value}.',
        'Our estimate was sent {col:open_est.age_days} days ago. We would be glad to talk through the options and answer questions. {col:open_est.technician} will call you on {col:open_est.next_call}.',
        'If your plans changed, please tell us so we can close the estimate.'], ['Contractor']),
    D_('price_list', 'Flat-Rate Price List', 'Flat-rate prices for one job type', 'job_types.job_type', [
        'Price list of {set:company}, dated {today}. Job type: {col:job_types.job_type}.',
        'Our flat-rate prices for this job type run from {col:job_types.min_price} to {col:job_types.highest_price_placeholder}.'.replace('highest_price_placeholder', 'max_price') + ' The average price is {col:job_types.avg_price}. Prices include parts and labour and are before sales tax.',
        'A flat price is a fixed price per task, built from cost. Please check the current price before you book.'], ['Contractor']),
    D_('member_list', 'Member Price List', 'Member price for one job type', 'job_types.job_type', [
        'Member price list of {set:company}, dated {today}. Job type: {col:job_types.job_type}.',
        'Members of a maintenance agreement (a yearly plan with two tune-ups) get {set:member_discount} off repairs. The average member price for this job type is {col:job_types.member_avg}, against {col:job_types.avg_price} for other customers.',
        'Prices include parts and labour and are before sales tax. Please check the current price before you book.'], ['Contractor']),
    D_('repair_replace', 'Repair or Replace Summary', 'Replacement summary for the customer', 'estimates.estimate_id', [
        'Summary from {set:company}, dated {today}. Estimate {col:estimates.estimate_id} for {col:estimates.site_ref}, {col:estimates.job_type}, prepared by {col:estimates.technician}.',
        'The choice between repairing and replacing is yours. The replacement price starts at {col:estimates.good_price} and the middle option is {col:estimates.better_price}. A financing offer can spread the cost: about {col:estimates.monthly_better} a month on the middle option.',
        'Please read the options and tell us your choice. Your choice is recorded as: {col:estimates.option_chosen}. Outcome: {col:estimates.outcome}.'], ['Contractor', 'Customer']),
    D_('expiry', 'Estimate Expiry Notice', 'Notice that an estimate expires', 'estimates.estimate_id', [
        'Notice from {set:company}, dated {today}. Estimate {col:estimates.estimate_id} for {col:estimates.site_ref}, {col:estimates.job_type}, value {col:estimates.est_value}.',
        'This estimate is valid until {col:estimates.valid_until}. After that date the price may change. We keep a closed estimate on file until {col:estimates.file_until}.',
        'To book, call us before the date above.'], ['Contractor']),
    D_('landlord_notice', 'Price Change Notice', 'Price change notice to a landlord account', 'sites.site_id', [
        'Notice from {set:company}, dated {today}. Account {col:sites.account}, site {col:sites.site_ref}.',
        'Our flat-rate prices change on {col:sites.price_date}, by about {set:planned_rise} on average. Jobs booked before that date keep the current price.',
        'Please contact us if you want to book planned work at the current prices.'], ['Contractor', 'Account holder']),
    D_('diag_notice', 'Diagnostic Fee Notice', 'Diagnostic fee notice', 'quote_log.quote_id', [
        'Notice from {set:company}, dated {today}. Quote {col:quote_log.quote_id} for {col:quote_log.site_ref}: {col:quote_log.job_type}.',
        'A diagnostic fee of {set:diag_fee} is a fee for coming out to find the cause. It is credited to the job if you go ahead.',
        'Prices are before sales tax. Please check the current price before you book.'], ['Contractor', 'Customer']),
    D_('financing_sheet', 'Financing Offer', 'Financing offer in generic words', 'fin_options.term_months', [
        'Financing offer of {set:company}, dated {today}. Term: {col:fin_options.term_months} months.',
        'The monthly payment is about {col:fin_options.monthly_factor} of the amount financed. On {set:finance_example} financed this is about {col:fin_options.example_payment} a month.',
        'A financing offer is a loan or payment plan through your lender. Terms and approval are the lender\'s; the figures here are examples only.'], ['Contractor', 'Customer']),
    D_('book_review', 'Price Book Review Summary', 'Price book line review for the owner', 'lines_under.rank_no', [
        'Price book review of {set:company}, dated {today}. Rank {col:lines_under.rank_no}: {col:lines_under.pb_id}, {col:lines_under.task}.',
        'Flat price {col:lines_under.flat_price}, cost {col:lines_under.cost}. Margin {col:lines_under.margin} against a target of {col:lines_under.target_margin}. Check: {col:lines_under.status}.',
        'Price needed at the target: {col:lines_under.price_needed}, a rise of {col:lines_under.rise_needed}. Margin lost a year at the current price: {col:lines_under.lost_year}. Lines under target in the book: {col:lines_under.under_count}.'], ['Owner']),
]
assert len(documents) == 12
checklists = [
    CHK('build_est', 'Building an Estimate', 'estimates', 'estimates.date', [('Confirm the site reference and the job type', 0), ('Find the task in the price book', 0), ('Check parts at today\'s cost', 0), ('Add permit, disposal and subcontract cost', 0), ('Check the margin against the target', 0), ('Add the estimate to the Estimates sheet', 1)]),
    CHK('three_opts', 'Presenting Three Options', 'estimates', 'estimates.date', [('Price good, better and best from the price book', 0), ('Check the margin of each option', 0), ('Work out the monthly payment of each option', 0), ('Lead with the option the history supports', 1), ('Offer the deposit that holds the date', 1)]),
    CHK('est_sent', 'Estimate Sent', 'estimates', 'estimates.date', [('Send the estimate to the customer', 0), ('Write the valid-until date', 0), ('Set the follow-up date', 0), ('Tell the technician what was sent', 1)]),
    CHK('fu3', 'Estimate Follow-up Day 3', 'estimates', 'estimates.date', [('Call the customer', 3), ('Ask if the options are clear', 3), ('Offer to talk through the three options', 3), ('Write the answer and the next follow-up date', 3)]),
    CHK('fu10', 'Estimate Follow-up Day 10', 'estimates', 'estimates.date', [('Check the estimate is still open', 10), ('Call or message the customer', 10), ('Offer a date that suits the customer', 10), ('Record the outcome or the new follow-up date', 11)]),
    CHK('accepted', 'Accepted Estimate and Deposit', 'estimates', 'estimates.date', [('Confirm the option chosen', 0), ('Ask for the deposit', 0), ('Book the date and the technician', 1), ('Order the equipment', 1), ('Mark the estimate as won', 1)]),
    CHK('lost_review', 'Estimate Lost Review', 'estimates', 'estimates.date', [('Record the lost reason', 0), ('Ask the customer why, if they are willing', 7), ('Check the price against the book', 7), ('Keep the estimate on file for 90 days', 90)]),
    CHK('month_check', 'Monthly Price Book Check', 'est_months', 'est_months.month', [('Open the Lines Under Target sheet', 30), ('Check parts cost changes of the month', 30), ('Update parts and flat prices that moved', 31), ('Type the price book margin in Estimates by Month', 31), ('Tell the technicians about changed prices', 32)]),
    CHK('supplier_change', 'Supplier Price Change Received', 'price_changes', 'price_changes.date', [('Write the change in Supplier Price Changes', 0), ('Update the part cost in Parts Cost List', 0), ('Check the lines that use the part', 1), ('Raise the flat price if the line fell under target', 3), ('Tell the technicians and the office manager', 3)]),
    CHK('year_review', 'Yearly Price Review Steps', 'est_months', 'est_months.month', [('Collect the cost rises: labour, parts, fuel, insurance', 0), ('Run the Yearly Price Review tool', 7), ('Lift the lines with the largest money lost first', 14), ('Write the new flat prices and keep the old ones', 21), ('Tell landlord accounts the date of the change', 21), ('Tell the technicians', 28)]),
    CHK('diag_review', 'Diagnostic Fee Review', 'diag_months', 'diag_months.month', [('Read visits and conversion of the month', 30), ('Compare the fee with the cost of a visit', 30), ('Run the Call-Out and Diagnostic Fee tool', 31), ('Decide to raise, hold or lower the fee', 32)]),
    CHK('member_review', 'Member Price Review', 'quote_log', 'quote_log.date', [('List repair lines under the margin floor at the member price', 0), ('Check how many members use the discount', 3), ('Run the Member Price and Discount Check tool', 3), ('Change the discount or the lines', 7), ('Tell the office manager', 7)]),
]
assert len(checklists) == 12


def M(k_, moment, table, phone, text): return MSG(k_, moment, table, phone, text)
messages = [
    M('c_three', 'Customer: estimate with three options', 'estimates', 'estimates.phone', 'Hello, your estimate {estimate_id} for {job_type} at {site_ref} has three options: good {good_price}, better {better_price}, best {best_price}. {company}'),
    M('c_valid', 'Customer: your estimate is valid until', 'estimates', 'estimates.phone', 'Hello, your estimate {estimate_id} for {job_type} is valid until {valid_until}. {company}'),
    M('c_talk', 'Customer: talk through the options?', 'estimates', 'estimates.phone', 'Hello, would you like to talk through the options on estimate {estimate_id}? Reply with a good time to call. {company}'),
    M('c_remind', 'Customer: your estimate expires soon', 'estimates', 'estimates.phone', 'A reminder: your estimate {estimate_id} expires on {valid_until}. {company}'),
    M('c_updated', 'Customer: your estimate was updated', 'estimates', 'estimates.phone', 'Your estimate {estimate_id} was updated. The new price is {est_value}. {company}'),
    M('c_booked', 'Customer: we booked your job', 'estimates', 'estimates.phone', 'Thank you, we booked your job for {job_date}. Estimate {estimate_id}, {job_type}. {company}'),
    M('c_deposit', 'Customer: a deposit holds your date', 'estimates', 'estimates.phone', 'A deposit of {deposit} holds your date for estimate {estimate_id}. {company}'),
    M('c_monthly', 'Customer: your monthly payment', 'estimates', 'estimates.phone', 'The monthly payment for the better option on estimate {estimate_id} is about {monthly_better}. {company}'),
    M('c_member', 'Customer: your member price', 'quote_log', 'quote_log.phone', 'Hello, your member price for {job_type} at {site_ref} is {member_price}. Please check the current price with us. {company}'),
    M('c_match', 'Customer: we can match your date', 'estimates', 'estimates.phone', 'We can match your date if you decide on estimate {estimate_id} by {valid_until}. {company}'),
    M('c_why', 'Customer: why another company?', 'estimates', 'estimates.phone', 'May we ask why you chose another company for estimate {estimate_id}? Your answer helps us improve. {company}'),
    M('c_file', 'Customer: we kept your estimate on file', 'estimates', 'estimates.phone', 'We kept your estimate {estimate_id} on file until {file_until}. {company}'),
    M('l_ready', 'Landlord account: the estimate is ready', 'estimates', 'estimates.phone', 'Hello {account}, the estimate {estimate_id} for {site_ref} is ready. Value {est_value}. {company}'),
    M('l_approve', 'Landlord account: please approve', 'estimates', 'estimates.phone', 'Hello {account}, please approve estimate {estimate_id} for {site_ref}, value {est_value}. {company}'),
    M('l_prices', 'Landlord account: our prices change', 'sites', 'sites.phone', 'Hello {account}, our prices change on {price_date}. Jobs booked before that date keep the current price. {company}'),
    M('l_expires', 'Landlord account: estimate expires soon', 'estimates', 'estimates.phone', 'Hello {account}, the estimate {estimate_id} for {site_ref} expires on {valid_until}. {company}'),
    M('t_today', 'Technician: estimate follow-up today', 'open_est', 'open_est.tech_phone', 'Hello {technician}, please call {site_ref} today about estimate {estimate_id}, value {est_value}. {company}'),
    M('t_week', 'Technician: your estimates won', 'close_tech', 'close_tech.tech_phone', 'Hello {technician}, estimates in the period {period}: {won} won of {estimates} decided, close rate {close_rate}. {company}'),
    M('t_price', 'Technician: the price of a task changed', 'price_book', 'price_book.lead_phone', 'The price for {task} changed to {flat_price}. {company}'),
    M('t_better', 'Technician: lead with the better option', 'estimates', 'estimates.tech_phone', 'Hello {technician}, on estimate {estimate_id} ({job_type}) lead with the better option, {better_price}. {company}'),
    M('a_parts', 'Apprentice: add the parts list', 'estimates', 'estimates.apprentice_phone', 'Hello, please add the parts list to estimate {estimate_id} for {job_type}. {company}'),
    M('o_nofu', 'Office manager: no follow-up date', 'open_est', 'open_est.office_phone', 'Estimate {estimate_id} for {site_ref} ({technician}) needs a follow-up date. Please set one. {company}'),
    M('o_old', 'Office manager: estimate over 14 days', 'open_est', 'open_est.office_phone', 'Estimate {estimate_id} is {age_days} days old, value {est_value}. Please follow up. {company}'),
    M('o_book', 'Office manager: update the price book', 'price_changes', 'price_changes.office_phone', 'Please update the price book for {part}: the new cost is {new_cost}. {company}'),
    M('w_table', 'Owner: money on the table', 'open_est', 'open_est.owner_phone', 'Money on the table is {open_total} across {open_count} open estimates. {company}'),
    M('w_under', 'Owner: lines under target', 'lines_under', 'lines_under.owner_phone', 'The price book has {under_count} lines under target. Lowest margin: {task}, {margin}. {company}'),
    M('w_close', 'Owner: the close rate of the month', 'est_months', 'est_months.owner_phone', 'The close rate for the month starting {month} is {close_rate}. {company}'),
    M('w_supplier', 'Owner: supplier price change', 'price_changes', 'price_changes.owner_phone', 'Supplier price change on {part}: {old_cost} to {new_cost}, a rise of {rise}. {company}'),
    M('w_review', 'Owner: the yearly price review is due', 'lines_under', 'lines_under.owner_phone', 'The yearly price review is due: {under_count} lines are under target and the lowest is {task}. {company}'),
    M('e_confirm', 'Equipment supplier: confirm the price', 'parts', 'parts.equip_phone', 'Please confirm the price for {part}. Our cost on file is {unit_cost}. {company}'),
    M('p_list', 'Parts counter: send the new price list', 'parts', 'parts.counter_phone', 'Please send the new price list for {category} parts. {company}'),
    M('x_elec', 'Electrical sub: send your price', 'price_book', 'price_book.elec_phone', 'Please send your price for {job_type}, task {task}. {company}'),
    M('x_sheet', 'Sheet-metal sub: send your price', 'price_book', 'price_book.sheet_phone', 'Please send your price for {job_type}, task {task}. {company}'),
    M('x_acct', 'Accountant: price changes summary', 'price_changes', 'price_changes.acct_phone', 'Supplier price changes this year are in the summary, for example {part}: {old_cost} to {new_cost} on {date}. {company}'),
]
assert len(messages) == 34, len(messages)

MS = 'DATE(YEAR({today}),MONTH({today}),1)'
ES = lambda c_: '{range:estimates.%s}' % c_
PB = lambda c_: '{range:price_book.%s}' % c_
OPEN_, WON, LOST = tok('estoutcome', 'Open'), tok('estoutcome', 'Won'), tok('estoutcome', 'Lost')
def DW(n): return '%s,">="&({today}-%d),%s,"<="&{today}' % (ES('date'), n, ES('date'))
def CR(n): return 'IFERROR(COUNTIFS(%s,%s,%s)/COUNTIFS(%s,"<>"&%s,%s),0)' % (ES('outcome'), WON, DW(n), ES('outcome'), OPEN_, DW(n))
def SHARE(t_): return 'IFERROR(COUNTIFS(%s,%s,%s,%s,%s)/COUNTIFS(%s,%s,%s),0)' % (ES('outcome'), WON, ES('option_chosen'), tok('optchosen', t_), DW(365), ES('outcome'), WON, DW(365))
DM = lambda c_: '{range:diag_months.%s}' % c_
kpis = [
    KPI('Estimates sent this month', 'COUNTIFS(%s,">="&%s,%s,"<="&{today})' % (ES('date'), MS, ES('date')), 'int'),
    KPI('Estimates sent last 30 days', 'COUNTIFS(%s)' % DW(30), 'int'),
    KPI('Estimates won this month', 'COUNTIFS(%s,">="&%s,%s,"<="&{today},%s,%s)' % (ES('date'), MS, ES('date'), ES('outcome'), WON), 'int'),
    KPI('Close rate last 90 days', CR(90), 'pct', alert={"when": "< {set:close_target}", "style": "warn"}),
    KPI('Close rate last 12 months', CR(365), 'pct', alert={"when": "< {set:close_target}", "style": "warn"}),
    KPI('Money on the table', 'SUM(%s)' % ES('value_open'), 'money'),
    KPI('Open estimates older than 14 days', 'COUNTIFS(%s,">"&{set:stale_days})' % ES('age_days'), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Open estimates with no follow-up date', 'COUNTIFS(%s,%s)' % (ES('followup_flag'), ca('No follow-up date')), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Average estimate value last 90 days', 'IFERROR(AVERAGEIFS(%s,%s),0)' % (ES('est_value'), DW(90)), 'money'),
    KPI('Average ticket won last 90 days', 'IFERROR(AVERAGEIFS(%s,%s,%s,%s),0)' % (ES('price_won'), ES('outcome'), WON, DW(90)), 'money'),
    KPI('Share of estimates won at good', SHARE('Good'), 'pct'), KPI('Share of estimates won at better', SHARE('Better'), 'pct'), KPI('Share of estimates won at best', SHARE('Best'), 'pct'),
    KPI('Options offered per estimate', 'IFERROR(AVERAGEIFS(%s,%s),0)' % (ES('options_offered'), DW(90)), 'num'),
    KPI('Lost estimates last 90 days', 'COUNTIFS(%s,%s,%s)' % (ES('outcome'), LOST, DW(90)), 'int'),
    KPI('Lost value last 90 days', 'SUMIFS(%s,%s)' % (ES('lost_value'), DW(90)), 'money'),
    KPI('Share lost to price last 90 days', 'IFERROR(COUNTIFS(%s,%s,%s,%s)/COUNTIFS(%s,%s,%s),0)' % (ES('lost_reason'), tok('estlost', 'Price'), ES('outcome'), LOST, ES('outcome'), LOST, DW(90)) if False else
        'IFERROR(COUNTIFS(%s,%s,%s,%s,%s)/COUNTIFS(%s,%s,%s),0)' % (ES('lost_reason'), tok('estlost', 'Price'), ES('outcome'), LOST, DW(90), ES('outcome'), LOST, DW(90)), 'pct'),
    KPI('Price book lines', 'COUNTA(%s)' % PB('pb_id'), 'int'),
    KPI('Price book lines under target', 'COUNTIFS(%s,%s)' % (PB('status'), ca('Under target')), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Lowest margin line', 'MIN(%s)' % PB('margin'), 'pct'), KPI('Average price book margin', 'AVERAGE(%s)' % PB('margin'), 'pct'),
    KPI('Supplier price changes last 12 months', 'COUNTIFS({range:price_changes.date},">="&({today}-365),{range:price_changes.date},"<="&{today})', 'int'),
    KPI('Money at risk on lines under target', 'SUM(%s)' % PB('lost_year'), 'money', alert={"when": "> 0", "style": "bad"}),
    KPI('Price rise needed for the margin target', 'IFERROR(SUM(%s)/SUMIFS(%s,%s,">0"),0)' % (PB('lost_year'), PB('revenue_year'), PB('gap_money')), 'pct'),
    KPI('Diagnostic visits this month', 'SUMIFS(%s,%s,%s)' % (DM('visits'), DM('month'), MS), 'int'),
    KPI('Diagnostic conversion, last 3 months', 'IFERROR(SUMIFS(%s,%s,">="&EDATE(%s,-3))/SUMIFS(%s,%s,">="&EDATE(%s,-3)),0)' % (DM('converted'), DM('month'), MS, DM('visits'), DM('month'), MS), 'pct'),
    KPI('Diagnostic fee income this month', 'SUMIFS(%s,%s,%s)' % (DM('fee_income'), DM('month'), MS), 'money'),
    KPI('Cost of one diagnostic visit', 'IFERROR(SUM(%s)/SUM(%s),0)' % (DM('visit_cost'), DM('visits')), 'money'),
    KPI('Best technician wins, last 90 days', 'MAX({range:close_tech.won_recent})', 'int'),
    KPI('Average days from call to estimate', 'IFERROR(AVERAGEIFS(%s,%s),0)' % (ES('days_to_estimate'), DW(365)), 'num'),
]
assert len(kpis) == 30, len(kpis)


def AGGW(*w): return list(w)
OW = ('outcome', '=', WON)
dashboard = {"title": "KPI Dashboard", "kpis": kpis,
    "monthly": {"title": "Value sent, won, lost and diagnostic fees", "date": "estimates.date", "series": [
        {"label": "Value sent", "sum": "estimates.est_value", "date": "estimates.date"}, {"label": "Value won", "sum": "estimates.price_won", "date": "estimates.date"},
        {"label": "Value lost", "sum": "estimates.lost_value", "date": "estimates.date"}, {"label": "Diagnostic fee income", "sum": "diag_months.fee_income", "date": "diag_months.month"}]},
    "breakdowns": [{"title": "Value won by job type", "by": "estimates.job_type", "value": "estimates.price_won", "agg": "sum"}, {"title": "Estimates by technician", "by": "estimates.technician", "agg": "count"},
                   {"title": "Price book lines by job type", "by": "price_book.job_type", "agg": "count"}, {"title": "Lost value by reason", "by": "estimates.lost_reason", "value": "estimates.lost_value", "agg": "sum"}]}
insights = {"filters": [{"label": "Technician", "list": "tech"}, {"label": "Job type", "list": "estjt"}],
    "gauges": [
        {"title": "Close rate against the target", "num": AGG('count', 'estimates', where=[OW]), "den": AGG('count', 'estimates', where=[('outcome', '<>', OPEN_)])},
        {"title": "Open estimates followed up", "num": AGG('count', 'estimates', where=[('outcome', '=', OPEN_), ('followup_flag', '=', ca('Follow-up set'))]), "den": AGG('count', 'estimates', where=[('outcome', '=', OPEN_)])},
        {"title": "Price book lines on target", "num": AGG('count', 'price_book', where=[('status', '=', ca('On target'))]), "den": AGG('count', 'price_book')},
        {"title": "Estimates won at better or best", "num": AGG('count', 'estimates', where=[OW, ('option_chosen', '<>', tok('optchosen', 'Good'))]), "den": AGG('count', 'estimates', where=[OW])},
        {"title": "Diagnostic visits converted", "num": AGG('sum', 'diag_months', 'diag_months.converted'), "den": AGG('sum', 'diag_months', 'diag_months.visits')},
        {"title": "Estimates answered within 3 days", "num": AGG('count', 'estimates', where=[('days_to_estimate', '>=', 0), ('days_to_estimate', '<=', '{set:followup_days}')]), "den": AGG('count', 'estimates', where=[('days_to_estimate', '>=', 0)])}],
    "charts": [
        CHART('Estimates per month', 'column', 'month', [AGG('count', 'estimates', date='estimates.date', label='Estimates')]),
        CHART('Estimates won per month', 'column', 'month', [AGG('count', 'estimates', date='estimates.date', where=[OW], label='Won')]),
        CHART('Close rate per month', 'line', 'month', [AGG('avg', 'estimates', 'estimates.won_flag', date='estimates.date', label='Close rate')]),
        CHART('Estimates by outcome', 'bar', 'estimates.outcome', [AGG('count', 'estimates', label='Estimates')]),
        CHART('Estimates by option chosen', 'bar', 'estimates.option_chosen', [AGG('count', 'estimates', label='Estimates')]),
        CHART('Estimates by job type', 'bar', 'estimates.job_type', [AGG('count', 'estimates', label='Estimates')]),
        CHART('Estimates by technician', 'bar', 'estimates.technician', [AGG('count', 'estimates', label='Estimates')]),
        CHART('Lost estimates by reason', 'bar', 'estimates.lost_reason', [AGG('count', 'estimates', where=[('outcome', '=', LOST)], label='Lost')]),
        CHART('Lost value per month', 'column', 'month', [AGG('sum', 'estimates', 'estimates.lost_value', date='estimates.date', label='Lost value')]),
        CHART('Average ticket won per month', 'line', 'month', [AGG('avg', 'estimates', 'estimates.price_won', date='estimates.date', where=[OW], label='Average ticket')]),
        CHART('Open estimate value by technician', 'bar', 'estimates.technician', [AGG('sum', 'estimates', 'estimates.value_open', label='Open value')]),
        CHART('Price book lines by job type', 'bar', 'price_book.job_type', [AGG('count', 'price_book', label='Lines')]),
        CHART('Price book margin by job type', 'bar', 'price_book.job_type', [AGG('avg', 'price_book', 'price_book.margin', label='Margin')]),
        CHART('Price book lines by option', 'bar', 'price_book.tier', [AGG('count', 'price_book', label='Lines')]),
        CHART('Supplier price changes per month', 'column', 'month', [AGG('count', 'price_changes', date='price_changes.date', label='Changes')]),
        CHART('Supplier price change by supplier', 'bar', 'price_changes.supplier', [AGG('avg', 'price_changes', 'price_changes.rise', label='Average rise')]),
        CHART('Price book margin per month', 'line', 'month', [AGG('avg', 'est_months', 'est_months.book_margin', date='est_months.month', label='Price book margin')]),
        CHART('Diagnostic visits per month', 'column', 'month', [AGG('sum', 'diag_months', 'diag_months.visits', date='diag_months.month', label='Visits')]),
        CHART('Diagnostic conversion per month', 'line', 'month', [AGG('avg', 'diag_months', 'diag_months.conversion', date='diag_months.month', label='Conversion')]),
        CHART('Estimate value per month', 'column', 'month', [AGG('sum', 'estimates', 'estimates.est_value', date='estimates.date', label='Estimate value')]),
        CHART('Value won by job type', 'bar', 'estimates.job_type', [AGG('sum', 'estimates', 'estimates.price_won', label='Value won')]),
        CHART('Options offered per month', 'line', 'month', [AGG('avg', 'estimates', 'estimates.options_offered', date='estimates.date', label='Options offered')])]}
assert len(insights['charts']) == 22

signature = [
    {"name": "Flat-rate price book built from cost", "why": "labour hours, parts, permit, disposal, subcontract and trip give the cost, margin and price at target for 57 tasks", "where": "Price Book"},
    {"name": "Price book margin check", "why": "all lines ranked by margin gap against the target, with the money lost on each job", "where": "Price Book Margin Check"},
    {"name": "Supplier price change impact", "why": "type a part and its new cost to see which lines fall under target and the money at risk a year", "where": "Supplier Price Change Impact"},
    {"name": "Good-better-best builder", "why": "three priced options with margin, monthly payment and the option to lead with from your own history", "where": "Good-Better-Best Builder"},
    {"name": "Estimate follow-up ranker", "why": "open estimates ranked by value times age, with the money on the table and the first calls to make today", "where": "Estimate Follow-up Ranker"},
    {"name": "Yearly price review", "why": "enter your cost rises and see the price rise needed and the lines to lift first", "where": "Yearly Price Review"},
    {"name": "Price rise break-even solver", "why": "the share of jobs you can lose after a price rise before profit falls, with a sensitivity row", "where": "Price Rise Break-Even Solver"},
    {"name": "Call-out and diagnostic fee test", "why": "fee against the cost of a visit, the conversion you need and a verdict to raise, hold or lower", "where": "Call-Out and Diagnostic Fee"},
    {"name": "Close rate by option, technician and job type", "why": "three periods side by side so a weak cell shows against your own last 12 months", "where": "Close Rate by Technician"},
    {"name": "Lost-estimate cause analyser", "why": "lost value by cause with the cause to fix first and the profit of winning some back", "where": "Lost-Estimate Cause Analyser"}]
competitors = [
    {"what": "field-service app with a per-technician fee", "lacks": "charges every month and hides how a price was built, so you cannot test a margin target or a cost rise yourself"},
    {"what": "generic invoice template", "lacks": "writes a price but never builds it from labour, parts and trip cost, and has no margin per line"},
    {"what": "single-sheet quote calculator", "lacks": "prices one job at a time with no good-better-best options, no follow-up list and no close-rate history"},
    {"what": "pen-and-paper job book", "lacks": "keeps no history, so supplier price rises, lost estimates and old open quotes are never counted"},
    {"what": "free price list spreadsheet", "lacks": "lists prices only, with no margin against target, no yearly review and no price rise break-even"}]
guide = [
    'Open Start and type your company name and your own limits in the yellow cells: close target, margin floor, loaded labour rates, diagnostic fee, member discount and financing factor.',
    'Check Job Types and Labour Rates. They hold your target margin by job type and the labour cost the price book uses.',
    'Fill Parts Cost List with today\'s supplier cost. Every price book line reads its parts cost and its main part from there.',
    'Keep the Price Book up to date: hours, parts, permit, disposal, subcontract and flat price. Cost, margin, the gap to target and the price needed fill in by themselves.',
    'Log every supplier cost change on Supplier Price Changes, then read Lines Under Target to see which lines need a new price.',
    'Add every estimate to Estimates with its three prices, the option chosen, the outcome and the follow-up date. Open Estimates ranks what to call first.',
    'Use Option Builder for good, better and best lines with margin and a monthly payment from your financing factor.',
    'Read Close Rate by Option, Technician and Job Type, Lost Reasons and Estimates by Month to see where estimates are won and lost.',
    'Type each month of diagnostic visits on Diagnostic Visits and log phone quotes on Quote Log.',
    f'Use the {len(tools)} tools for line prices, margin checks, supplier changes, options, follow-ups, price reviews, fees and financing.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'A one-person owner-operator with one van can use the Price Book as a quote sheet; a shop with a dispatcher shares the follow-up list with the office.',
    'Read the KPI Dashboard and Charts every week: close rate, money on the table, margin lines under target, lost value and diagnostic conversion.']
listing = {"title": "HVAC and Plumbing Price Book Excel Template: Flat-Rate Pricing, Estimates, Good-Better-Best Options, Margin and Follow-up",
    "headline": "Price every job from cost and win more of your estimates",
    "tags": ["hvac template", "plumbing template", "flat rate pricing", "price book", "estimate tracker", "good better best", "contractor excel", "close rate", "job margin", "service pricing", "quote template", "hvac business", "plumber estimate"],
    "description": ("Run the pricing and estimates side of an HVAC and plumbing business in one Excel workbook. Built for a small owner-run service shop with 1 to 15 technicians, or a one-person owner-operator who uses the price book as a quote sheet.\n\n"
        "The Price Book holds a flat-rate price for each task, a fixed price built from cost: labour hours at your loaded rate, parts, permit, disposal, subcontract work and the trip. Cost, margin, the gap to your target margin, the price needed and the money lost a year on each line fill in by themselves. "
        "Supplier Price Changes and Parts Cost List show which lines fall under target after a supplier price rise, and Lines Under Target ranks them.\n\n"
        "Estimates records every estimate with good, better and best prices (three priced options for one job), the option chosen, the outcome and the follow-up date. Open Estimates ranks what to call first, and Option Builder shows margin and a monthly payment from a financing factor you enter. "
        "Close Rate by Option, Technician and Job Type compare the last 90 days, the last 12 months and the year before; Lost Reasons and Estimates by Month show where money is lost.\n\n"
        f"{len(tools)} tools answer weekly questions: the price at your margin target, supplier price impact, the option to lead with, estimate follow-up, the yearly price review, the price rise break-even, the diagnostic fee test, member prices, financing and phone quotes. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to customers, landlord accounts, technicians, suppliers and your accountant.\n\n"
        "This is part two of the HVAC and Plumbing Contractor suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data. It helps you keep track of prices and estimates and does not promise results."),
    "features": ["Flat-rate price book with margin per line", "Lines under target after supplier price rises", "Good-better-best option builder with monthly payments", "Open estimate follow-up list ranked by money",
                 "Close rate by option, technician and job type", "Yearly price review and price rise break-even", "Diagnostic fee test and member price check", f"{len(tools)} decision tools",
                 f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p2', slug='hvac-plumbing-price-book', profession='HVAC and Plumbing Contractor', name='Price Book, Estimates and Options',
         tagline='Price every job from cost and win more of your estimates', price_usd=29, colors={"primary": "#1F4E5F", "accent": "#E07A3F"},
         settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide, listing=listing, insights=insights,
         suite={"key": SUITE, "part": 2, "of": 8, "focus": "Price book, estimates and options"}, signature=signature, competitors=competitors,
         tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hv2.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
