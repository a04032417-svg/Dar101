"""Short-term rental host suite - part 7: Owner Statements, Fees and Local Taxes."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr7_lists import *
from sr7_tables import settings, tables
from sr7_tools import tools

SUITE = 'fx-20261113-short-term-rental'
NOTE = "Sample wording: adapt it to your own practice and check your own local rules."
def F(*pairs): return [FV(a, b) for a, b in pairs]
forms = [
    FORM('statement_sheet', 'Owner Statement Sheet', 'Owner statement for one month', 'statements.statement_id', F(
        ('Month', 'statements.month'), ('Owner', 'statements.owner'), ('Units', 'statements.units'), ('Nights', 'statements.nights'), ('Revenue', 'statements.revenue'), ('Platform fees', 'statements.platform_fees'),
        ('Cleaning costs', 'statements.cleaning_costs'), ('Supplies', 'statements.supplies'), ('Maintenance', 'statements.maintenance'), ('Utilities', 'statements.utilities'), ('Management percent', 'statements.mgmt_pct'),
        ('Management fee', 'statements.mgmt_fee'), ('Net to owner', 'statements.net_to_owner'), ('Net margin', 'statements.net_margin'), ('Status', 'statements.status'), ('Statement check', 'statements.check_flag'), ('Payment check', 'statements.pay_flag'))),
    FORM('payment_sheet', 'Owner Payment Sheet', 'Owner payment with method and check', 'payments.pay_id', F(
        ('Statement', 'payments.statement'), ('Owner', 'payments.owner'), ('Statement month', 'payments.stmt_month'), ('Date', 'payments.date'), ('Amount', 'payments.amount'), ('Method', 'payments.method'), ('Status', 'payments.status'),
        ('Statement net', 'payments.stmt_net'), ('Share of the statement', 'payments.share'), ('Pay by', 'payments.pay_due'), ('Payment check', 'payments.pay_flag'), ('Owner phone', 'payments.owner_phone'))),
    FORM('request_sheet', 'Owner Request Sheet', 'Owner request with cost and days open', 'requests.req_id', F(
        ('Date', 'requests.date'), ('Owner', 'requests.owner'), ('Unit', 'requests.unit'), ('Request', 'requests.request'), ('Done on', 'requests.done_on'), ('Cost', 'requests.cost'), ('Status', 'requests.status'),
        ('Days open', 'requests.days_open'), ('Owner phone', 'requests.owner_phone'), ('Co-host phone', 'requests.cohost_phone'))),
    FORM('stay_sheet', 'Owner Stay Sheet', 'Owner stay with cleaning and linen charged', 'stays.stay_id', F(
        ('Owner', 'stays.owner'), ('Unit', 'stays.unit'), ('Check-in', 'stays.check_in'), ('Check-out', 'stays.check_out'), ('Nights', 'stays.nights'), ('Cleaning charged', 'stays.cleaning_charged'), ('Linen charged', 'stays.linen_charged'),
        ('Total charged', 'stays.stay_charge'), ('Stay check', 'stays.stay_flag'), ('Owner phone', 'stays.owner_phone'))),
    FORM('cohost_fee_sheet', 'Co-host Fee Sheet', 'Co-host fee for one month', 'cohost_fees.fee_id', F(
        ('Month', 'cohost_fees.month'), ('Units', 'cohost_fees.units'), ('Revenue', 'cohost_fees.revenue'), ('Platform fees', 'cohost_fees.platform_fees'), ('Net revenue', 'cohost_fees.net_revenue'), ('Fee percent', 'cohost_fees.fee_pct'),
        ('Fee amount', 'cohost_fees.fee_amount'), ('Messages', 'cohost_fees.messages'), ('Fee per message', 'cohost_fees.fee_per_message'), ('Fee check', 'cohost_fees.fee_check'), ('Message check', 'cohost_fees.msg_check'), ('Status', 'cohost_fees.status'), ('Paid on', 'cohost_fees.paid_on'))),
    FORM('duty_sheet', 'Co-host Duty Sheet', 'Co-host duty with minutes and check', 'duties.duty_id', F(
        ('Date', 'duties.date'), ('Task', 'duties.task'), ('Unit', 'duties.unit'), ('Minutes', 'duties.minutes'), ('Hours', 'duties.hours'), ('Done', 'duties.done'), ('Duty check', 'duties.duty_flag'), ('Co-host phone', 'duties.cohost_phone'))),
    FORM('tax_return_sheet', 'Local Tax Return Sheet', 'Local tax return for one city and month', 'local_tax.tax_id', F(
        ('Month', 'local_tax.month'), ('City', 'local_tax.city'), ('Tax percent', 'local_tax.tax_pct'), ('Nights', 'local_tax.nights'), ('Room revenue', 'local_tax.room_revenue'), ('Tax collected', 'local_tax.tax_collected'),
        ('Collected by host', 'local_tax.collected_by_host'), ('Collected by platform', 'local_tax.platform_part'), ('Platform reported', 'local_tax.platform_reported'), ('Difference', 'local_tax.tax_diff'), ('Tax check', 'local_tax.tax_check'),
        ('Adjustments', 'local_tax.adj_sum'), ('Tax to remit', 'local_tax.to_remit'), ('Due date', 'local_tax.due_date'), ('Remitted', 'local_tax.remitted'), ('Paid on', 'local_tax.paid_on'), ('Filing check', 'local_tax.file_flag'))),
    FORM('adjustment_sheet', 'Tax Adjustment Sheet', 'Local tax adjustment with reason and filing', 'adjustments.adj_id', F(
        ('Month', 'adjustments.month'), ('City', 'adjustments.city'), ('Reason', 'adjustments.reason'), ('Amount', 'adjustments.amount'), ('Effect', 'adjustments.effect'), ('Filed on', 'adjustments.filed_on'),
        ('Filing check', 'adjustments.filing_flag'), ('Days from month start to filing', 'adjustments.days_to_file'), ('Accountant phone', 'adjustments.accountant_phone'))),
    FORM('contract_sheet', 'Owner Contract Sheet', 'Owner contract term with end and notice dates', 'contracts.contract_id', F(
        ('Owner', 'contracts.owner'), ('Unit', 'contracts.unit'), ('Start', 'contracts.start_date'), ('End', 'contracts.end_date'), ('Term in months', 'contracts.term_months'), ('Management percent', 'contracts.mgmt_pct'),
        ('Notice days', 'contracts.notice_days'), ('Notice by', 'contracts.notice_by'), ('Days to the end', 'contracts.days_to_end'), ('Renewal check', 'contracts.end_flag'), ('Notice check', 'contracts.notice_flag'), ('Owner phone', 'contracts.owner_phone'))),
    FORM('reserve_sheet', 'Reserve Top-up Sheet', 'Owner repair reserve for one month', 'reserves.reserve_id', F(
        ('Month', 'reserves.month'), ('Owner', 'reserves.owner'), ('Reserve held', 'reserves.reserve_held'), ('Spent', 'reserves.spent'), ('Balance', 'reserves.balance'), ('Reserve check', 'reserves.low_flag'), ('Owner phone', 'reserves.owner_phone'))),
]
assert len(forms) == 10
documents = [
    DOC('statement_doc', 'Monthly Owner Statement', 'Monthly owner statement', 'statements.statement_id', [
        'Owner statement of {set:company}, dated {today}. Owner: {col:statements.owner}. Statement {col:statements.statement_id} for the month starting {col:statements.month}: {col:statements.units} units and {col:statements.nights} nights booked.',
        'Revenue {col:statements.revenue}. Platform fees {col:statements.platform_fees}. Cleaning {col:statements.cleaning_costs}. Supplies {col:statements.supplies}. Maintenance {col:statements.maintenance}. Utilities {col:statements.utilities}.',
        'Management fee at {col:statements.mgmt_pct}: {col:statements.mgmt_fee}. Net to owner: {col:statements.net_to_owner}, which is {col:statements.net_margin} of revenue.',
        'Status: {col:statements.status}. Sent on {col:statements.sent_on}, paid on {col:statements.paid_on}. Statement check: {col:statements.check_flag}. Payment check: {col:statements.pay_flag}.',
        'Amounts are in one currency and before any income tax of the owner. Ask about any line and the booking or repair behind it is shown.'], ['Host', 'Owner'], NOTE),
    DOC('year_doc', 'Owner Year Summary', 'Owner year summary', 'statements.statement_id', [
        'Owner year summary of {set:company}, dated {today}. Owner: {col:statements.owner}.',
        'Over the last 12 months the units of this owner earned revenue of {col:statements.own_rev_12m}. Our management fees were {col:statements.own_fee_12m} and the net paid to the owner was {col:statements.own_net_12m}.',
        'The statement used to open this summary is {col:statements.statement_id} for the month starting {col:statements.month}, with net to owner of {col:statements.net_to_owner}.',
        'The full monthly statements and the lines behind them are available on request. This summary is a record, not tax advice: check your own local rules with your adviser.'], ['Host', 'Owner'], NOTE),
    DOC('advice_doc', 'Owner Payment Advice', 'Owner payment advice', 'payments.pay_id', [
        'Payment advice of {set:company}, dated {today}. Payment {col:payments.pay_id} to {col:payments.owner}.',
        'Amount {col:payments.amount} on {col:payments.date} by {col:payments.method}. Status: {col:payments.status}. This pays {col:payments.share} of statement {col:payments.statement}, whose net to owner is {col:payments.stmt_net}.',
        'The statement is for the month starting {col:payments.stmt_month}. The payment was due by {col:payments.pay_due}. Check: {col:payments.pay_flag}.',
        'Please tell us if the amount does not arrive within three working days.'], ['Host', 'Owner'], NOTE),
    DOC('agreement_doc', 'Management Agreement Summary', 'Management agreement summary', 'contracts.contract_id', [
        'Management agreement summary of {set:company}, dated {today}. Contract {col:contracts.contract_id} between the host and {col:contracts.owner} for {col:contracts.unit}.',
        'The term starts on {col:contracts.start_date} and ends on {col:contracts.end_date}, a term of {col:contracts.term_months} months. Management percent: {col:contracts.mgmt_pct}. Notice to end the contract: {col:contracts.notice_days} days, given by {col:contracts.notice_by}.',
        'Renewal check: {col:contracts.end_flag}. Days to the end: {col:contracts.days_to_end}. Notice check: {col:contracts.notice_flag}.',
        'This is a summary of the main terms only. The signed contract terms are the ones that apply.'], ['Host', 'Owner'], NOTE),
    DOC('cohost_doc', 'Co-host Fee Statement', 'Co-host fee statement', 'cohost_fees.fee_id', [
        'Co-host fee statement of {set:company}, dated {today}. Statement {col:cohost_fees.fee_id} for the month starting {col:cohost_fees.month}.',
        'Units handled: {col:cohost_fees.units}. Revenue {col:cohost_fees.revenue}, platform fees {col:cohost_fees.platform_fees}, net revenue {col:cohost_fees.net_revenue}. Fee percent {col:cohost_fees.fee_pct}.',
        'Fee amount: {col:cohost_fees.fee_amount} for {col:cohost_fees.messages} messages answered, which is {col:cohost_fees.fee_per_message} per message. Fee check: {col:cohost_fees.fee_check}. Message check: {col:cohost_fees.msg_check}.',
        'Status: {col:cohost_fees.status}, paid on {col:cohost_fees.paid_on}.'], ['Host', 'Co-host'], NOTE),
    DOC('tax_return_doc', 'Local Tax Return Worksheet', 'Local tax return worksheet', 'local_tax.tax_id', [
        'Local tax return worksheet of {set:company}, dated {today}. Return {col:local_tax.tax_id} for {col:local_tax.city}, month starting {col:local_tax.month}.',
        'Nights {col:local_tax.nights}. Room revenue {col:local_tax.room_revenue}. Tax percent {col:local_tax.tax_pct}. Tax collected from guests: {col:local_tax.tax_collected}, of which collected by the host {col:local_tax.collected_by_host} and by the platforms {col:local_tax.platform_part}.',
        'The platforms reported {col:local_tax.platform_reported}, a difference of {col:local_tax.tax_diff}. Tax check: {col:local_tax.tax_check}. Adjustments: {col:local_tax.adj_sum}. Tax to remit: {col:local_tax.to_remit}.',
        'Due date {col:local_tax.due_date}. Remitted {col:local_tax.remitted} on {col:local_tax.paid_on}. Filing check: {col:local_tax.file_flag}. Check your own local rules for the form and the date.'], ['Host', 'Accountant'], NOTE),
    DOC('city_doc', 'Local Tax Summary by City', 'Local tax summary by city', 'local_tax.tax_id', [
        'Local tax summary of {set:company}, dated {today}. City: {col:local_tax.city}.',
        'Over the last 12 months the tax collected from guests in this city was {col:local_tax.city_12m}. The host collected {col:local_tax.city_host_12m} of it and remitted {col:local_tax.city_paid_12m}.',
        'The return used to open this page is {col:local_tax.tax_id} for the month starting {col:local_tax.month}: tax collected {col:local_tax.tax_collected}, tax to remit {col:local_tax.to_remit}, filing check {col:local_tax.file_flag}.',
        'Tax collected by the platforms is remitted by them. Check your own local rules for what the host must report.'], ['Host', 'Accountant'], NOTE),
    DOC('stay_doc', 'Owner Stay Confirmation', 'Owner stay confirmation', 'stays.stay_id', [
        'Owner stay confirmation of {set:company}, dated {today}. Stay {col:stays.stay_id} for {col:stays.owner} in {col:stays.unit}.',
        'Check-in {col:stays.check_in}, check-out {col:stays.check_out}, {col:stays.nights} nights. The owner pays the cleaning {col:stays.cleaning_charged} and the linen {col:stays.linen_charged}, in total {col:stays.stay_charge}.',
        'The dates are blocked on all booking channels. Stay check: {col:stays.stay_flag}. The charge is shown on the next owner statement.',
        'A stay of an owner earns no revenue for the unit in those nights.'], ['Host', 'Owner'], NOTE),
    DOC('reserve_doc', 'Owner Reserve Statement', 'Owner reserve statement', 'reserves.reserve_id', [
        'Owner reserve statement of {set:company}, dated {today}. Owner: {col:reserves.owner}. Month starting {col:reserves.month}.',
        'Added to the repair reserve this month: {col:reserves.reserve_held}. Spent from the reserve this month: {col:reserves.spent}. Balance now: {col:reserves.balance}.',
        'Reserve check: {col:reserves.low_flag}. Small repairs are paid from the reserve so that a repair is never held up. The owner is asked to top up the reserve when it is low.',
        'Every spend from the reserve is shown on the owner statement with its repair ticket.'], ['Host', 'Owner'], NOTE),
    DOC('tier_doc', 'Fee Tier Schedule', 'Fee tier schedule', 'tiers.tier', [
        'Management fee schedule of {set:company}, dated {today}. Tier: {col:tiers.tier}.',
        'Package: {col:tiers.package}. Units managed from {col:tiers.units_from} to {col:tiers.units_to}. Fee percent: {col:tiers.fee_pct}. Services included: {col:tiers.services}.',
        'On an average monthly statement this tier gives a management fee of {col:tiers.fee_on_avg}.',
        'The fee is charged on revenue after platform fees. The lower tiers apply when an owner brings more units.'], ['Host', 'Owner'], NOTE),
]
assert len(documents) == 10
checklists = [
    CHK('month_close', 'Month-End Statement Close Steps', 'statements', 'statements.month', [('Check every booking of the month is on the sheet', 28), ('Add cleaning, supplies and utilities', 30), ('Add repair costs with their tickets', 31), ('Work out the management fee', 32),
        ('Check the statement adds up', 33), ('Send the statement to the owner', 35), ('Send the pack to the accountant', 36), ('Plan the owner payment', 37)]),
    CHK('statement_review', 'Owner Statement Review Steps', 'statements', 'statements.month', [('Compare revenue with last month', 31), ('Look at costs above 40 percent of revenue', 32), ('Check the net margin against your floor', 32), ('Check the lines behind unusual costs', 33),
        ('Check the reserve balance', 33), ('Fix any difference before sending', 34), ('Mark the statement as sent', 35)]),
    CHK('pay_day', 'Owner Payment Day Steps', 'payments', 'payments.date', [('Check cash against the total to pay', -3), ('Confirm the amounts with the statements', -2), ('Pay the owners', 0), ('Send each payment advice', 0), ('Mark the payment as paid', 0), ('Chase any payment not received in 3 days', 3)]),
    CHK('cohost_run', 'Co-host Fee Check Steps', 'cohost_fees', 'cohost_fees.month', [('Count the messages answered', 29), ('Check the net revenue of the units handled', 30), ('Work out the fee at the agreed percent', 31), ('Compare the fee per message with last months', 32), ('Send the fee statement', 33), ('Pay the fee', 36)]),
    CHK('tax_run', 'Local Tax Return Steps', 'local_tax', 'local_tax.due_date', [('Collect nights and room revenue of the month', -20), ('Split the tax collected by host and by platform', -18), ('Compare with the platform tax reports', -16), ('Add any adjustments', -14), ('Send the return to the accountant', -10),
        ('Check the amount to remit', -7), ('Remit the tax', -2), ('Keep the proof of payment', 0)]),
    CHK('adj_run', 'Tax Adjustment Steps', 'adjustments', 'adjustments.month', [('Find the booking or refund behind the difference', 32), ('Work out the amount and its sign', 33), ('Write the adjustment with its reason', 34), ('Send it to the accountant', 35), ('Add it to the next return', 40), ('Record the filing date', 45)]),
    CHK('onboard_run', 'Owner Onboarding Steps', 'contracts', 'contracts.start_date', [('Agree the package and the management percent', -21), ('Sign the contract terms', -14), ('Collect the unit details and the owner phone', -12), ('Take photos and write the listing', -10), ('Set the opening reserve', -7), ('Set up cleaning, linen and a repair contact', -5),
        ('Block the dates the owner wants', -3), ('Open the first statement', 0)]),
    CHK('renewal_run', 'Owner Contract Renewal Steps', 'contracts', 'contracts.end_date', [('Prepare the year summary for the owner', -90), ('Check the fee tier for the units managed', -75), ('Talk to the owner about the renewal', -60), ('Send the renewal terms', -45), ('Check the notice date', -30), ('Sign the renewal', -14), ('Update the contract sheet', 0)]),
    CHK('stay_run', 'Owner Stay Steps', 'stays', 'stays.check_in', [('Block the dates on all channels', -30), ('Confirm the stay with the owner', -14), ('Book the cleaner for the end of the stay', -7), ('Set the linen and supplies', -3), ('Check the unit is ready', -1), ('Charge cleaning and linen on the next statement', 5)]),
    CHK('year_run', 'Year-End Owner Summary Steps', 'statements', 'statements.month', [('Check all 12 statements are sent and paid', 31), ('Work out revenue, fees and net per owner', 45), ('Check the reserve balance of each owner', 50), ('Send the year summary to each owner', 60), ('Send the local tax summary to the accountant', 62), ('Plan fee tiers and contracts for next year', 75)]),
]
assert len(checklists) == 10
def M(key_, moment, table, phone, text): return MSG(key_, moment, table, phone, text)
messages = [
    M('o_ready', 'Owner: your statement is ready', 'statements', 'statements.owner_phone', 'Hello {owner}, your statement for {month} is ready. Revenue {revenue}, management fee {mgmt_fee}, net to you {net_to_owner}.'),
    M('o_paid', 'Owner: your payment has been sent', 'payments', 'payments.owner_phone', 'Hello {owner}, your payment of {amount} was sent on {date} by {method}. Please tell us when it arrives.'),
    M('o_costs', 'Owner: costs were higher, here is why', 'statements', 'statements.owner_phone', 'Hello {owner}, costs were higher in {month}: cleaning {cleaning_costs}, maintenance {maintenance}, utilities {utilities}. Net to you is {net_to_owner}. Happy to explain.'),
    M('o_earned', 'Owner: your unit earned this month', 'statements', 'statements.owner_phone', 'Hello {owner}, your unit earned {revenue} over {nights} nights in {month}.'),
    M('o_repair', 'Owner: please approve the repair cost', 'maint', 'maint.owner_phone', 'Hello {owner}, a repair at {unit} cost {cost} on {done_on}. Please confirm you approve the charge on your statement.'),
    M('o_reserve', 'Owner: your reserve is low', 'reserves', 'reserves.owner_phone', 'Hello {owner}, your repair reserve is {balance} after {month}. Please add funds so repairs are never held up.'),
    M('o_stay', 'Owner: your own stay is confirmed', 'stays', 'stays.owner_phone', 'Hello {owner}, your stay in {unit} from {check_in} to {check_out} is confirmed. Cleaning and linen charge: {stay_charge}.'),
    M('o_contract', 'Owner: your contract renews soon', 'contracts', 'contracts.owner_phone', 'Hello {owner}, your management contract for {unit} ends on {end_date}. Shall we renew it at {mgmt_pct}?'),
    M('o_year', 'Owner: a summary of your year is ready', 'statements', 'statements.owner_phone', 'Hello {owner}, your 12-month summary is ready: revenue {own_rev_12m}, management fees {own_fee_12m}, net to you {own_net_12m}.'),
    M('o_tier', 'Owner: our fee changes with more units', 'contracts', 'contracts.owner_phone', 'Hello {owner}, the fee for {unit} is {mgmt_pct}. With more units our fee schedule goes down. Would you like to add another unit?'),
    M('o_question', 'Owner: a question about your statement', 'statements', 'statements.owner_phone', 'Hello {owner}, a question about your statement for {month}: net to you is {net_to_owner}. Could we speak this week?'),
    M('o_delay', 'Owner: your payment is delayed one day', 'payments', 'payments.owner_phone', 'Hello {owner}, your payment of {amount} due on {date} is delayed by one day. Sorry for that.'),
    M('o_thanks', 'Owner: a thank you and a summary', 'statements', 'statements.owner_phone', 'Hello {owner}, thank you for trusting us with your unit. In {month} guests stayed {nights} nights and the unit earned {revenue}.'),
    M('o_item', 'Owner: your unit needs a new item', 'requests', 'requests.owner_phone', 'Hello {owner}, {unit} needs this: {request}. Estimated cost {cost}. Please reply to confirm.'),
    M('c_stmt', 'Co-host: your fee statement', 'cohost_fees', 'cohost_fees.cohost_phone', 'Hello, your fee statement for {month}: net revenue {net_revenue}, fee {fee_amount} for {messages} messages.'),
    M('c_paid', 'Co-host: your fee has been sent', 'cohost_fees', 'cohost_fees.cohost_phone', 'Hello, your fee of {fee_amount} for {month} has been sent. Thank you for the work.'),
    M('c_log', 'Co-host: please log your duties', 'duties', 'duties.cohost_phone', 'Hello, please log your duties for the month. The last one on the sheet is {task} at {unit} on {date}, {minutes} minutes.'),
    M('c_high', 'Co-host: the fee looks high', 'cohost_fees', 'cohost_fees.cohost_phone', 'Hello, the fee for {month} looks high at {fee_per_message} a message for {messages} messages. Please check the count with me.'),
    M('a_pack', 'Accountant: the statements for the month', 'statements', 'statements.accountant_phone', 'Hello, the owner statements for {month} are attached. This one: {owner}, revenue {revenue}, net to owner {net_to_owner}.'),
    M('a_tax', 'Accountant: local tax is due', 'local_tax', 'local_tax.accountant_phone', 'Hello, local tax for {city} is due on {due_date}. The host must remit {to_remit}. Please prepare the return.'),
    M('a_adj', 'Accountant: tax adjustments', 'adjustments', 'adjustments.accountant_phone', 'Hello, tax adjustment for {city}, month {month}: {amount}. Please include it in the return.'),
    M('a_year', 'Accountant: the year-end owner summary', 'statements', 'statements.accountant_phone', 'Hello, the year-end summary for {owner} is attached: revenue {own_rev_12m}, net to owner {own_net_12m}.'),
    M('h_draft', 'Host: a statement is still in draft', 'statements', 'statements.host_phone', 'Hello, the statement for {owner} for {month} is still in draft. Net to owner so far: {net_to_owner}.'),
    M('h_tax7', 'Host: local tax is due soon', 'local_tax', 'local_tax.host_phone', 'Hello, local tax for {city} is due on {due_date}, in {days_to_due} days. Amount to remit: {to_remit}.'),
    M('h_diff', 'Host: the tax check shows a difference', 'local_tax', 'local_tax.host_phone', 'Hello, the tax check shows a difference of {tax_diff} in {city} for {month}. Please look at it before the return.'),
    M('h_pay', 'Host: an owner payment is due', 'payments', 'payments.host_phone', 'Hello, an owner payment is due: {owner}, {amount} on {date}.'),
    M('h_neg', 'Host: a statement shows a low net', 'statements', 'statements.host_phone', 'Hello, the statement for {owner} for {month} shows net to owner of {net_to_owner}. Please review it before it is sent.'),
    M('h_contract', 'Host: an owner contract ends soon', 'contracts', 'contracts.host_phone', 'Hello, the contract of {owner} for {unit} ends on {end_date}, in {days_to_end} days. Time to talk about the renewal.'),
]
assert len(messages) == 28
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; PM = 'DATE(YEAR({today}),MONTH({today})-1,1)'; Y1 = 'DATE(YEAR({today}),MONTH({today})-12,1)'
def S12(col, tb='statements'): return 'SUMIFS({range:%s.%s},{range:%s.month},">="&%s,{range:%s.month},"<"&%s)' % (tb, col, tb, Y1, tb, MS)
def SM(col, m): return 'SUMIFS({range:statements.%s},{range:statements.month},%s)' % (col, m)
def OM(i, col): return 'SUMIFS({range:statements.%s},{range:statements.owner},INDEX({range:owners.name},%d),{range:statements.month},">="&%s,{range:statements.month},"<"&%s)' % (col, i, Y1, MS)
def MG(i): return 'IFERROR(%s/%s,1)' % (OM(i, 'net_to_owner'), OM(i, 'revenue'))
LOW = 'MIN(%s,%s,%s)' % (MG(2), MG(3), MG(4))
NF = tok('taxst', 'Filed and paid')
DUEWIN = '{range:local_tax.status},"<>"&%s' % NF
kpis = [
    KPI('Owner revenue this month', SM('revenue', MS), 'money'), KPI('Owner revenue last month', SM('revenue', PM), 'money'), KPI('Net to owner this month', SM('net_to_owner', MS), 'money'),
    KPI('Net to owner, last 12 months', S12('net_to_owner'), 'money'), KPI('Management fees earned this month', SM('mgmt_fee', MS), 'money'), KPI('Management fees earned, last 12 months', S12('mgmt_fee'), 'money'),
    KPI('Management fee share of owner revenue', 'IFERROR(%s/%s,0)' % (S12('mgmt_fee'), S12('revenue')), 'pct'),
    KPI('Statements in draft', 'COUNTIFS({range:statements.status},%s)' % tok('stmst', 'Draft'), 'int'),
    KPI('Statements sent, not paid', 'COUNTIFS({range:statements.status},%s)' % tok('stmst', 'Sent'), 'int'),
    KPI('Owner payments due in the next 7 days', 'SUMIFS({range:payments.amount},{range:payments.status},%s,{range:payments.date},">="&{today},{range:payments.date},"<="&({today}+{set:warn_days}))' % tok('pstat', 'Scheduled'), 'money'),
    KPI('Owner payments made this month', 'SUMIFS({range:payments.amount},{range:payments.status},%s,{range:payments.date},">="&%s,{range:payments.date},"<="&{today})' % (tok('pstat', 'Paid'), MS), 'money'),
    KPI('Average net to owner margin, 12 months', 'IFERROR(%s/%s,0)' % (S12('net_to_owner'), S12('revenue')), 'pct'),
    KPI('Owner with the lowest margin', 'IF(%s<=%s,INDEX({range:owners.name},2),IF(%s<=%s,INDEX({range:owners.name},3),INDEX({range:owners.name},4)))' % (MG(2), LOW, MG(3), LOW), 'text'),
    KPI('Platform fees on owner units, 12 months', S12('platform_fees'), 'money'), KPI('Cleaning cost on owner units, 12 months', S12('cleaning_costs'), 'money'),
    KPI('Maintenance on owner units, 12 months', S12('maintenance'), 'money'), KPI('Utilities on owner units, 12 months', S12('utilities'), 'money'),
    KPI('Co-host fees this month', 'SUMIFS({range:cohost_fees.fee_amount},{range:cohost_fees.month},%s)' % MS, 'money'), KPI('Co-host fees, last 12 months', S12('fee_amount', 'cohost_fees'), 'money'),
    KPI('Co-host fee as a share of net revenue', 'IFERROR(%s/%s,0)' % (S12('fee_amount', 'cohost_fees'), S12('net_revenue', 'cohost_fees')), 'pct'),
    KPI('Local tax collected this month', 'SUMIFS({range:local_tax.tax_collected},{range:local_tax.month},%s)' % MS, 'money'),
    KPI('Local tax the host must remit', 'SUMIFS({range:local_tax.to_remit},%s)' % DUEWIN, 'money'),
    KPI('Local tax due in the next 30 days', 'SUMIFS({range:local_tax.to_remit},%s,{range:local_tax.due_date},">="&{today},{range:local_tax.due_date},"<="&({today}+30))' % DUEWIN, 'money'),
    KPI('Local tax overdue', 'SUMIFS({range:local_tax.to_remit},%s,{range:local_tax.due_date},"<"&{today})' % DUEWIN, 'money'),
    KPI('Local tax paid this year', 'SUMIFS({range:local_tax.remitted},{range:local_tax.paid_on},">="&DATE(YEAR({today}),1,1),{range:local_tax.paid_on},"<="&{today})', 'money'),
    KPI('Tax checks with a difference', 'COUNTIFS({range:local_tax.tax_check},%s)' % ca('Difference to explain'), 'int'),
    KPI('Owner reserves held', 'SUMIFS({range:reserves.balance},{range:reserves.month},%s)' % MS, 'money'),
    KPI('Owner contracts ending in 90 days', 'COUNTIFS({range:contracts.end_date},">="&{today},{range:contracts.end_date},"<="&({today}+{set:renewal_days}))', 'int'),
    KPI('Owner requests open', 'COUNTIFS({range:requests.status},%s)' % cb('Request open'), 'int'),
]
assert len(kpis) == 29, len(kpis)
dashboard = {"title": "Owner and Tax Dashboard", "kpis": kpis,
    "monthly": {"title": "Owner revenue, net to owner, management fees and local tax", "date": "statements.month", "series": [
        {"label": "Owner revenue", "sum": "statements.revenue", "date": "statements.month"}, {"label": "Net to owner", "sum": "statements.net_to_owner", "date": "statements.month"},
        {"label": "Management fees", "sum": "statements.mgmt_fee", "date": "statements.month"}, {"label": "Local tax collected", "sum": "local_tax.tax_collected", "date": "local_tax.month"}]},
    "breakdowns": [{"title": "Revenue by owner", "by": "statements.owner", "value": "statements.revenue", "agg": "sum"}, {"title": "Local tax by city", "by": "local_tax.city", "value": "local_tax.tax_collected", "agg": "sum"},
                   {"title": "Statements by status", "by": "statements.status", "value": "statements.revenue", "agg": "count"}, {"title": "Costs by type on owner statements", "by": "lines.kind", "value": "lines.amount", "agg": "sum"}]}
NREV = ('kind', '<>', tok('lkind', 'Revenue'))
insights = {"filters": [{"label": "Owner", "ref": "owners.name"}, {"label": "City", "list": "city"}],
    "gauges": [{"title": "Statements sent on time", "num": AGG('count', 'statements', where=[('sent_flag', '=', ca('Sent on time'))]), "den": AGG('count', 'statements', where=[('status', '<>', tok('stmst', 'Draft'))])},
               {"title": "Net to owner margin", "num": AGG('sum', 'statements', 'statements.net_to_owner'), "den": AGG('sum', 'statements', 'statements.revenue')},
               {"title": "Owner payments on time", "num": AGG('count', 'payments', where=[('pay_flag', '=', ca('Paid on time'))]), "den": AGG('count', 'payments', where=[('status', '<>', tok('pstat', 'Scheduled'))])},
               {"title": "Local tax filed on time", "num": AGG('count', 'local_tax', where=[('file_flag', '=', ca('Filed on time'))]), "den": AGG('count', 'local_tax', where=[('file_flag', '<>', ca('Not yet due')), ('file_flag', '<>', ca('Due soon'))])},
               {"title": "Management fee share", "num": AGG('sum', 'statements', 'statements.mgmt_fee'), "den": AGG('sum', 'statements', 'statements.revenue')},
               {"title": "Co-host fee share", "num": AGG('sum', 'cohost_fees', 'cohost_fees.fee_amount'), "den": AGG('sum', 'cohost_fees', 'cohost_fees.net_revenue')}],
    "charts": [
        CHART('Owner revenue per month', 'column', 'month', [AGG('sum', 'statements', 'statements.revenue', date='statements.month', label='Revenue')]),
        CHART('Net to owner per month', 'column', 'month', [AGG('sum', 'statements', 'statements.net_to_owner', date='statements.month', label='Net to owner')]),
        CHART('Management fees per month', 'column', 'month', [AGG('sum', 'statements', 'statements.mgmt_fee', date='statements.month', label='Management fees')]),
        CHART('Costs by type on owner statements', 'bar', 'lines.kind', [AGG('sum', 'lines', 'lines.amount', where=[NREV], label='Costs and fee')]),
        CHART('Revenue by owner', 'bar', 'statements.owner', [AGG('sum', 'statements', 'statements.revenue', label='Revenue')]),
        CHART('Net to owner by owner', 'bar', 'statements.owner', [AGG('sum', 'statements', 'statements.net_to_owner', label='Net to owner')]),
        CHART('Platform fees per month on owner units', 'column', 'month', [AGG('sum', 'statements', 'statements.platform_fees', date='statements.month', label='Platform fees')]),
        CHART('Cleaning cost per month on owner units', 'column', 'month', [AGG('sum', 'statements', 'statements.cleaning_costs', date='statements.month', label='Cleaning')]),
        CHART('Maintenance cost per month on owner units', 'column', 'month', [AGG('sum', 'statements', 'statements.maintenance', date='statements.month', label='Maintenance')]),
        CHART('Statements by status', 'bar', 'statements.status', [AGG('count', 'statements', label='Statements')]),
        CHART('Co-host fees per month', 'column', 'month', [AGG('sum', 'cohost_fees', 'cohost_fees.fee_amount', date='cohost_fees.month', label='Co-host fee')]),
        CHART('Co-host messages per month', 'column', 'month', [AGG('sum', 'cohost_fees', 'cohost_fees.messages', date='cohost_fees.month', label='Messages')]),
        CHART('Local tax collected per month', 'column', 'month', [AGG('sum', 'local_tax', 'local_tax.tax_collected', date='local_tax.month', label='Tax collected')]),
        CHART('Local tax by city', 'bar', 'local_tax.city', [AGG('sum', 'local_tax', 'local_tax.tax_collected', label='Tax collected')]),
        CHART('Local tax by status', 'bar', 'local_tax.status', [AGG('sum', 'local_tax', 'local_tax.tax_collected', label='Tax collected')]),
        CHART('Local tax collected by host or platform per month', 'column', 'month', [AGG('sum', 'local_tax', 'local_tax.collected_by_host', date='local_tax.month', label='Collected by host'), AGG('sum', 'local_tax', 'local_tax.platform_part', date='local_tax.month', label='Collected by platform')]),
        CHART('Owner requests per month', 'column', 'month', [AGG('count', 'requests', date='requests.date', label='Requests')]),
        CHART('Owner reserves per month', 'line', 'month', [AGG('sum', 'reserves', 'reserves.balance', date='reserves.month', label='Reserves held')])]}
signature = [
    {"name": "Owner statement builder with management fee", "why": "revenue, platform fees, cleaning, supplies, repairs and utilities become one statement with the management fee and the net to owner, checked line by line", "where": "Owner Statements"},
    {"name": "Statement lines behind every number", "why": "each amount on a statement is split by unit and kind, with the booking or repair it comes from, so an owner's question has an answer", "where": "Statement Lines"},
    {"name": "Owner payment schedule", "why": "send dates, payment dates, the first working day, the total to pay and whether your cash covers it", "where": "Owner Payment Schedule"},
    {"name": "Co-host fee calculator", "why": "the fee on net revenue, the fee per message and per unit, compared with your own history so a high month stands out", "where": "Co-host Fee Calculator"},
    {"name": "Management fee tiers", "why": "the fee percent for each package and number of units, with the tier finder and the fee on an average statement", "where": "Fee Tiers"},
    {"name": "Local tax collected, remitted and due by city", "why": "tax collected by the host and by the platforms, what must be remitted, the due date and the days to go for every city and month", "where": "Local Tax"},
    {"name": "Tax check for differences", "why": "the tax the platforms say they remitted against the tax you worked out, with the difference to explain and the adjustments that follow", "where": "Local Tax Check"},
    {"name": "Tax due calendar", "why": "the next three return dates with the amounts and a warning when a date is close", "where": "Tax Due Calendar"},
    {"name": "Owner stay charge", "why": "cleaning and linen for an owner's own stay, the revenue the unit gives up and the margin on the charge", "where": "Owner Stay Charge"},
    {"name": "Owner reserve planner", "why": "the repair reserve to hold for each owner, the running balance by month and a low-reserve warning", "where": "Reserve and Float Planner"}]
competitors = [
    {"what": "free statement templates", "lacks": "give one blank page per owner but no lines by unit, no management fee tiers, no payment checks and no link to local tax"},
    {"what": "subscription property-management software", "lacks": "charge every month per unit and keep the fee rules inside, so you cannot test a management percent or see why a statement came out as it did"},
    {"what": "single-sheet booking trackers", "lacks": "list stays and revenue but never turn them into costs, a management fee, a net to owner or a payment date"},
    {"what": "generic expense spreadsheets", "lacks": "add up costs but cannot split them by owner, charge repairs to the right statement or hold a repair reserve"},
    {"what": "accountant-only tax worksheets", "lacks": "start at the return and miss the nights, the split between host and platform collection and the checks that find a difference early"}]
guide = [
    'Open Start and type your company name and your limits in the yellow cells: statement and payment days, tax due day, co-host fee percent, lowest net to owner and the reserve to hold.',
    'Check Owners, Units, Cities, Team and Fee Tiers. They hold the people, the units, the local tax percent of each city and the fee percent of each package; the other sheets look them up.',
    'At the end of each month fill Owner Statements: revenue, platform fees, cleaning, supplies, maintenance, utilities and the management percent. The management fee, the net to owner, the margin and the checks calculate themselves.',
    'Add the lines behind each statement on Statement Lines, one per unit and kind, with the booking or repair it comes from. Revenue, net and fee per unit fill in on Units.',
    'Record each payment to an owner on Owner Payments with its method. A statement paid in two parts has two rows; the payment check shows what is on time, late or delayed.',
    'Keep Bookings, Expenses, Cleaner Pay and Maintenance Costs up to date so every statement can be checked against its source.',
    'On Co-host Fees enter the month, the net revenue and the messages answered; the fee and the fee per message calculate themselves. Log the work on Co-host Duties.',
    'On Local Tax enter nights, room revenue, the tax collected, what the host collected and what the platforms reported. You see what to remit, the due date and any difference.',
    'Write each correction on Tax Adjustments with its reason and filing date. The tax to remit on Local Tax includes the adjustments.',
    'Track repair reserves on Owner Reserves, owner requests on Owner Requests, owner stays on Owner Stays and the term, notice date and renewal of each contract on Owner Contracts.',
    f'Use the {len(tools)} calculators for statements, fees, payment dates, the reserve, local tax, the tax calendar and check, owner stays, fee tiers, owner return and a percent grid.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in. Check your own local rules for tax forms and dates.',
    'Read the Owner and Tax Dashboard and the Charts every month: revenue, net to owner, fees, costs, statements, co-host fees, local tax, requests and reserves.']
listing = {"title": "Short-Term Rental Owner Statements Excel Template: Management Fees, Owner Payments, Co-host Fees, Local Occupancy Tax",
    "headline": "Send every owner a clear statement and never miss a local tax date",
    "tags": ["short term rental", "vacation rental", "owner statement", "management fee", "rental host", "excel template", "co-host fee", "local occupancy tax", "owner payments", "property manager", "tax tracker", "holiday let", "rental accounting"],
    "description": ("Run the owner and tax side of a short-term or vacation rental business in one Excel workbook. Built for a host or co-host who manages furnished units for other owners and rents them by the night through booking platforms and direct bookings. "
        "Owner Statements turns each month into a clear statement: revenue, platform fees, cleaning, supplies, maintenance, utilities, the management fee and the net to the owner, with the margin, the sending date, the payment date and a check that the figures add up.\n\n"
        "Statement Lines shows every amount by unit and kind with the booking or repair behind it, Units shows revenue and net per unit for 12 months, and Owner Payments tracks each payment, its method and whether it was on time. "
        "Co-host Fees works out the fee on net revenue and the fee per message for the co-host, a helper who handles guests for a fee, and Co-host Duties logs the work. Fee Tiers holds the fee percent for each service package and number of units.\n\n"
        "Local Tax follows the local occupancy tax, a tax on each night collected from the guest, by city and month: collected by the host, reported by the platforms, adjustments, the amount to remit, the due date and a check for differences. "
        "Owner Reserves, Owner Requests, Owner Stays and Owner Contracts keep repair reserves, requests, the cleaning and linen charged for an owner's own stay and the contract end and notice dates.\n\n"
        f"{len(tools)} calculators cover the statement, the management fee on net or gross, the co-host fee, the net per unit, payment dates, the reserve, local tax, the tax calendar, the tax check, owner stays, fee tiers, the owner return, a month comparison and a management percent grid. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to owners, the co-host, the accountant and the host.\n\n"
        "This is part seven of the Short-Term Rental Host suite. A standard .xlsx workbook with no macros and no subscription, 15 languages in one purchase, with a demo copy full of sample data to explore first. It helps you organise your own figures and does not give tax or legal advice: check your own local rules."),
    "features": ["Monthly owner statement with management fee and net to owner", "Statement lines by unit with the booking or repair behind them", "Owner payment tracker and payment schedule", "Co-host fee on net revenue and fee per message",
                 "Management fee tiers by package and units", "Local occupancy tax by city: collected, remitted, due", "Tax check for differences and adjustments", "Owner reserves, requests, stays and contracts",
                 f"{len(tools)} calculators for fees, tax, reserves and returns", f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p7', slug='short-term-rental-owners', profession='Short-Term Rental Host', name='Owner Statements, Fees and Local Taxes',
         tagline='Send every owner a clear statement and never miss a local tax date', price_usd=29,
         colors={"primary": "#264653", "accent": "#E9C46A"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 7, "of": 8, "focus": "Owner statements, fees and local taxes"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sr7.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'name', len(s['name']))
