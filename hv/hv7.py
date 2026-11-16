"""HVAC and plumbing contractor suite - part 7: Invoices, Collections and Seasonal Cash."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv7_lists import *
from hv7_tables import settings, tables, MS, L12, CASH_NOW, FIXED3
from hv7_tools import tools
import hv7_data as D

SUITE = 'fx-20261115-hvac-plumbing'
NOTE = "Sample wording: adapt it to your own business and check your local rules."
YES, NO = '{list:yesno.yes}', '{list:yesno.no}'
PAID, WO = tok('invstatus', 'Paid'), tok('invstatus', 'Written off')
def F(*pairs): return [FV(a, b) for a, b in pairs]

# the first demo row of a table opens the forms and documents: pick rows whose calculated fields all have values
def front(tkey, pred):
    t = next(x for x in tables if x['key'] == tkey)
    k = next(i for i, r in enumerate(t['demo']) if pred(r))
    t['demo'].insert(0, t['demo'].pop(k))
front('tax', lambda r: r['month'] == iso(month_start(4)))
front('pnl', lambda r: r['month'] == iso(month_start(1)))
front('cash', lambda r: r['month'] == iso(month_start(2)))

forms = [
    FORM('invoice_sheet', 'Invoice Sheet', 'Invoice with deposit, balance and days outstanding', 'invoices.invoice_id', F(
        ('Site reference', 'invoices.site_ref'), ('Account', 'invoices.account'), ('Job', 'invoices.job_id'), ('Job type', 'invoices.job_type'), ('Technician', 'invoices.technician'), ('Invoice date', 'invoices.date'),
        ('Due date', 'invoices.due_date'), ('Terms, days', 'invoices.terms_days'), ('Amount before sales tax', 'invoices.amount'), ('Deposit paid', 'invoices.deposit_paid'), ('Balance', 'invoices.balance'),
        ('Status', 'invoices.status'), ('Days outstanding', 'invoices.days_out'), ('Ageing bucket', 'invoices.bucket'))),
    FORM('deposit_sheet', 'Deposit Request Sheet', 'Deposit request to hold a date and cover equipment', 'invoices.invoice_id', F(
        ('Site reference', 'invoices.site_ref'), ('Phone', 'invoices.phone'), ('Job type', 'invoices.job_type'), ('Job amount', 'invoices.amount'), ('Deposit asked', 'invoices.deposit_asked'), ('Deposit paid', 'invoices.deposit_paid')) + [
        FF('Deposit at your percent', 'INDEX({range:invoices.amount},MATCH({pick},{range:invoices.invoice_id},0))*{set:deposit_pct}', 'money'),
        FF('Balance after the deposit', 'INDEX({range:invoices.amount},MATCH({pick},{range:invoices.invoice_id},0))-INDEX({range:invoices.deposit_asked},MATCH({pick},{range:invoices.invoice_id},0))', 'money')]),
    FORM('payment_sheet', 'Payment Received Sheet', 'Payment received and recorded', 'payments.payment_id', F(
        ('Date', 'payments.date'), ('Invoice', 'payments.invoice_id'), ('Job', 'payments.job_id'), ('Account', 'payments.account'), ('Site reference', 'payments.site_ref'), ('Amount', 'payments.amount'), ('Method', 'payments.method'),
        ('Kind', 'payments.kind'), ('Invoice amount', 'payments.invoice_amount'), ('Days after the invoice', 'payments.days_after'))),
    FORM('financing_sheet', 'Financing Note Sheet', 'Financing offer note for one invoice', 'invoices.invoice_id', F(
        ('Site reference', 'invoices.site_ref'), ('Phone', 'invoices.phone'), ('Job type', 'invoices.job_type'), ('Amount', 'invoices.amount'), ('Deposit paid', 'invoices.deposit_paid'), ('Financing used', 'invoices.financing')) + [
        FF('Amount to finance', 'INDEX({range:invoices.amount},MATCH({pick},{range:invoices.invoice_id},0))-INDEX({range:invoices.deposit_paid},MATCH({pick},{range:invoices.invoice_id},0))', 'money'),
        FF('Monthly payment at your factor', '(INDEX({range:invoices.amount},MATCH({pick},{range:invoices.invoice_id},0))-INDEX({range:invoices.deposit_paid},MATCH({pick},{range:invoices.invoice_id},0)))*{set:financing_factor}', 'money')]),
    FORM('chase_sheet', 'Chase Call Sheet', 'Chase call with the promise and the balance', 'chase.chase_id', F(
        ('Invoice', 'chase.invoice_id'), ('Account', 'chase.account'), ('Site reference', 'chase.site_ref'), ('Phone', 'chase.phone'), ('Call date', 'chase.date'), ('Method', 'chase.method'), ('Promised on', 'chase.promised_on'),
        ('Promised amount', 'chase.promised_amount'), ('Outcome', 'chase.outcome'), ('Invoice balance', 'chase.balance'), ('Days past due', 'chase.days_past_due'))),
    FORM('promise_sheet', 'Promise to Pay Sheet', 'Promise to pay with the amount left', 'chase.chase_id', F(
        ('Invoice', 'chase.invoice_id'), ('Account', 'chase.account'), ('Promised on', 'chase.promised_on'), ('Days promised', 'chase.promise_gap'), ('Promised amount', 'chase.promised_amount'), ('Invoice balance', 'chase.balance')) + [
        FF('Left after the promise', 'INDEX({range:chase.balance},MATCH({pick},{range:chase.chase_id},0))-INDEX({range:chase.promised_amount},MATCH({pick},{range:chase.chase_id},0))', 'money')]),
    FORM('terms_sheet', 'Account Terms Sheet', 'Account terms for a landlord or business account', 'accounts.account', F(
        ('Site type', 'accounts.site_type'), ('Terms, days', 'accounts.terms_days'), ('Phone', 'accounts.phone'), ('Open balance', 'accounts.open_balance')) + [
        FF('Terms for home customers, days', '{set:terms_home}', 'int'), FF('Share past terms asking pre-payment', '{set:prepay_share}', 'pct')]),
    FORM('supplier_bill_sheet', 'Supplier Bill Sheet', 'Supplier bill with the cash left after it', 'bills.bill_id', F(
        ('Payee', 'bills.payee'), ('Category', 'bills.category'), ('Kind', 'bills.kind'), ('Due date', 'bills.due_date'), ('Amount', 'bills.amount'), ('Days ahead', 'bills.days_ahead'), ('Running total due', 'bills.cum_due'),
        ('Cash after this bill', 'bills.cash_after'), ('Cash now less this bill', 'bills.cash_after_bill'), ('Floor check', 'bills.check')) + [FF('Cash floor', '{set:cash_floor}', 'money')]),
    FORM('sub_invoice_sheet', 'Subcontractor Invoice Sheet', 'Subcontractor invoice with the due date', 'purchases.po_id', F(
        ('Supplier', 'purchases.supplier'), ('Kind', 'purchases.kind'), ('Job', 'purchases.job_id'), ('Date', 'purchases.date'), ('Amount', 'purchases.amount'), ('Due date', 'purchases.due_date'), ('Paid on', 'purchases.paid_on'),
        ('Status', 'purchases.status'), ('Days paid after the due date', 'purchases.days_paid_vs_due'))),
    FORM('draw_sheet', 'Owner Draw Sheet', 'Owner draw option with the cash left', 'draw_options.option', F(
        ('Monthly owner pay', 'draw_options.monthly_draw'), ('Months of cover at the lowest month', 'draw_options.cover_left')) + [
        FF('Cash now', CASH_NOW, 'money'), FF('Cash floor', '{set:cash_floor}', 'money'), FF('Safe owner pay each month', 'INDEX({range:forecast.safe_pay},1)', 'money'), FF('Lowest closing cash in the plan', 'MIN({range:forecast.closing_cash})', 'money')]),
    FORM('tax_sheet', 'Tax Set-aside Sheet', 'Tax set-aside for one month, with your adviser', 'tax.month', F(
        ('Set-aside percent', 'tax.set_aside_pct'), ('Net profit', 'tax.profit'), ('Set aside', 'tax.set_aside'), ('Set aside year to date', 'tax.ytd_set_aside'), ('Tax paid', 'tax.tax_paid'), ('Tax paid year to date', 'tax.ytd_paid'))),
    FORM('close_sheet', 'Month-end Close Sheet', 'Month-end close with profit and cash', 'pnl.month', F(
        ('Period', 'pnl.period'), ('Jobs', 'pnl.jobs'), ('Revenue', 'pnl.revenue'), ('Gross profit', 'pnl.gross_profit'), ('Net profit', 'pnl.net_profit'), ('Gross margin', 'pnl.gross_pct'), ('Net margin', 'pnl.net_pct'),
        ('Net profit same month last year', 'pnl.ly_net'), ('Against last year', 'pnl.vs_ly')) + [
        FF('Closing cash of the month', 'SUMIFS({range:cash.closing_cash},{range:cash.month},{pick})', 'money'), FF('Cash in of the month', 'SUMIFS({range:cash.cash_in},{range:cash.month},{pick})', 'money')]),
]
assert len(forms) == 12
SG = ['Contractor', 'Customer']
documents = [
    DOC('invoice_doc', 'Invoice', 'Invoice for a job with deposit and balance', 'invoices.invoice_id', [
        'Invoice {col:invoices.invoice_id} of {set:company}, dated {col:invoices.date}. Site reference {col:invoices.site_ref}, account {col:invoices.account}, job {col:invoices.job_id}.',
        'Work: {col:invoices.job_type}. Technician: {col:invoices.technician}. The parts and labour lines of the job are written below.',
        'Amount before sales tax: {col:invoices.amount}. Deposit paid: {col:invoices.deposit_paid}. Balance: {col:invoices.balance}. Due date: {col:invoices.due_date} ({col:invoices.terms_days} days).',
        'Please pay by the due date and quote the invoice number.'], SG, NOTE),
    DOC('deposit_doc', 'Deposit Request', 'Deposit request to hold a date', 'invoices.invoice_id', [
        'Deposit request of {set:company}, dated {today}. Site reference {col:invoices.site_ref}, job {col:invoices.job_id}.',
        'A deposit is a payment taken to hold a date and cover equipment, applied to the final invoice. Deposit asked: {col:invoices.deposit_asked}. Job amount: {col:invoices.amount}.',
        'The date is held once the deposit is received. Notes are written below.'], SG, NOTE),
    DOC('receipt_doc', 'Payment Receipt', 'Payment receipt', 'payments.payment_id', [
        'Payment receipt of {set:company}, dated {col:payments.date}. Receipt {col:payments.payment_id}, site reference {col:payments.site_ref}.',
        'Received: {col:payments.amount} by {col:payments.method} as {col:payments.kind} for invoice {col:payments.invoice_id}.', 'Thank you for your payment.'], ['Contractor'], NOTE),
    DOC('statement_doc', 'Account Statement', 'Statement for a landlord account with ageing', 'ageing.account', [
        'Statement of {set:company}, dated {col:ageing.as_of}. Account {col:ageing.account}, terms {col:ageing.terms_days} days.',
        'Open invoices: {col:ageing.open_invoices}. Balance: {col:ageing.balance}. Ageing by days outstanding: 0 to 30 days {col:ageing.b0_30}, 31 to 60 days {col:ageing.b31_60}, 61 to 90 days {col:ageing.b61_90}, over 90 days {col:ageing.b90_plus}.',
        'Oldest invoice: {col:ageing.oldest_days} days. The invoice lines are written below. Please contact {set:company} with any question.'], ['Contractor', 'Account contact'], NOTE),
    DOC('reminder1_doc', 'Friendly Reminder', 'Friendly reminder letter', 'invoices.invoice_id', [
        'Letter of {set:company}, dated {today}. Site reference {col:invoices.site_ref}.', 'This is a friendly reminder that invoice {col:invoices.invoice_id} for {col:invoices.balance} was due on {col:invoices.due_date}.',
        'If you have already paid, thank you and please ignore this letter. Otherwise please contact {set:company}.'], ['Office'], NOTE),
    DOC('reminder2_doc', 'Second Reminder', 'Second reminder letter', 'invoices.invoice_id', [
        'Second reminder of {set:company}, dated {today}. Site reference {col:invoices.site_ref}.', 'Invoice {col:invoices.invoice_id} for {col:invoices.balance} is {col:invoices.days_past_due} days past due. Your last promise was for {col:invoices.promised_on}.',
        'Please pay now or tell us the date you will pay. The reply of the customer is written below.'], SG, NOTE),
    DOC('final_doc', 'Final Notice', 'Final notice letter in plain wording', 'invoices.invoice_id', [
        'Final notice of {set:company}, dated {today}. Site reference {col:invoices.site_ref}, account {col:invoices.account}.', 'Invoice {col:invoices.invoice_id} for {col:invoices.balance} is {col:invoices.days_outstanding_text} past due.' if False else
        'Invoice {col:invoices.invoice_id} for {col:invoices.balance} has been outstanding for {col:invoices.days_out} days and is {col:invoices.days_past_due} days past due.',
        'Please pay by the date written below. New work will be paused until the balance is settled. Contact {set:company} to agree a date.'], SG, NOTE),
    DOC('plan_doc', 'Payment Plan', 'Payment plan agreement in plain terms', 'invoices.invoice_id', [
        'Payment plan of {set:company}, dated {today}. Site reference {col:invoices.site_ref}, invoice {col:invoices.invoice_id}.', 'Balance to be paid: {col:invoices.balance}. The number of payments, their dates and amounts are agreed with the customer and written below.',
        'If a payment is missed, {set:company} may ask for the full balance. Agree the terms with the customer before you sign.'], SG, NOTE),
    DOC('forecast_doc', 'Cash Forecast Summary', 'Seasonal cash forecast summary for the owner', 'forecast.month', [
        'Cash forecast summary of {set:company}, dated {today}. Month starting {col:forecast.month}, {col:forecast.season}.',
        'Cash in: {col:forecast.cash_in}. Costs: {col:forecast.costs}. Payroll: {col:forecast.payroll}. Owner draw and bonus: {col:forecast.owner_pay}. Tax: {col:forecast.tax}. Net cash: {col:forecast.net}.',
        'Closing cash: {col:forecast.closing_cash}. Months of cover: {col:forecast.months_cover}. Floor check: {col:forecast.verdict}. Lowest closing cash in the plan: {col:forecast.lowest_cash}.', 'Actions are written below.'], ['Owner'], NOTE),
    DOC('pnl_doc', 'Month-end Summary', 'Month-end profit and loss summary', 'pnl.month', [
        'Profit and loss summary of {set:company}, dated {today}. Month starting {col:pnl.month}, {col:pnl.period}.', 'Jobs: {col:pnl.jobs}. Revenue: {col:pnl.revenue}. Materials: {col:pnl.materials}. Subcontract: {col:pnl.subcontract}. Technician pay: {col:pnl.technician_pay}. Gross profit: {col:pnl.gross_profit}.',
        'Vehicles: {col:pnl.vehicles}. Overhead: {col:pnl.overhead}. Net profit: {col:pnl.net_profit}. Same month last year: {col:pnl.ly_net}.', 'Notes are written below.'], ['Owner', 'Accountant'], NOTE),
    DOC('draw_note_doc', 'Owner Draw and Tax Note', 'Owner draw and tax set-aside note, with your adviser', 'tax.month', [
        'Owner draw and tax set-aside note of {set:company}, dated {today}. Month starting {col:tax.month}.', 'Net profit: {col:tax.profit}. Set aside at {col:tax.set_aside_pct}: {col:tax.set_aside}. Set aside this year to date: {col:tax.ytd_set_aside}. Tax paid this year to date: {col:tax.ytd_paid}.',
        'The tax figures are estimates: confirm them with your adviser. The owner draw decision is written below.'], ['Owner', 'Accountant'], NOTE),
    DOC('payment_schedule_doc', 'Supplier Payment Schedule', 'Supplier payment schedule', 'bills.bill_id', [
        'Supplier payment schedule of {set:company}, dated {today}. Bill {col:bills.bill_id}.', 'Payee: {col:bills.payee}. Category: {col:bills.category}. Amount: {col:bills.amount}. Due date: {col:bills.due_date}. Running total due: {col:bills.cum_due}.',
        'Cash after this bill: {col:bills.cash_after}. Floor check: {col:bills.check}. The agreed payment dates are written below.'], ['Owner', 'Office manager'], NOTE),
]
assert len(documents) == 12
checklists = [
    CHK('job_invoiced', 'Job Complete and Invoiced', 'unbilled', 'unbilled.date', [('Check the job note and the parts used', 0), ('Write the price and the invoice', 0), ('Send the invoice to the customer', 1), ('Type the invoice number on the job', 1), ('Chase the job note if it is missing', 2)]),
    CHK('deposit_collected', 'Deposit Collected', 'invoices', 'invoices.date', [('Write the deposit amount', -7), ('Send the deposit request', -7), ('Check the deposit is received', -3), ('Order the equipment only after the deposit', -2), ('Apply the deposit to the final invoice', 0)]),
    CHK('payment_recorded', 'Payment Received and Recorded', 'payments', 'payments.date', [('Match the payment to the invoice', 0), ('Record the method', 0), ('Send the receipt', 1), ('Update the invoice status', 1), ('Thank the customer', 2)]),
    CHK('weekly_chase', 'Weekly Chase Call', 'chase', 'chase.date', [('Open the Chase List', 0), ('Call the top accounts', 0), ('Write each promise date and amount', 0), ('Send a text to those who did not answer', 1), ('Check the promises due next week', 5)]),
    CHK('monthly_statements', 'Monthly Statements to Accounts', 'cash', 'cash.month', [('Check the ageing by account', 28), ('Print the statements', 29), ('Send the statements', 30), ('Call accounts over 60 days', 31), ('Record the promises', 32)]),
    CHK('month_end', 'Month-end Close', 'pnl', 'pnl.month', [('Record all payments', 28), ('Record all supplier bills', 28), ('Check the Profit and Loss sheet', 29), ('Update Cash by Month', 29), ('Send the month-end pack to the accountant', 31)]),
    CHK('bills_week', 'Supplier Bills Due This Week', 'bills', 'bills.due_date', [('List the bills due this week', -7), ('Check cash against the floor', -6), ('Ask to move a bill if cash is short', -5), ('Pay the bills', 0), ('Mark the bills paid', 1)]),
    CHK('forecast_update', 'Cash Forecast Update', 'forecast', 'forecast.month', [('Add last month to Cash by Month', 0), ('Check the cash index of the season', 1), ('Read the lowest cash month', 2), ('Run the slow-summer test', 3), ('Write the actions for the owner', 4)]),
    CHK('draw_decision', 'Owner Draw Decision', 'tax', 'tax.month', [('Read the safe owner pay', 28), ('Compare it with the draw and bonus taken', 29), ('Check cash above the floor', 29), ('Decide the draw for next month', 30), ('Note the decision', 30)]),
    CHK('tax_check', 'Tax Set-aside Check', 'tax', 'tax.month', [('Read the set-aside of the month', 28), ('Move the money to the tax account', 29), ('Check the next payment estimate', 30), ('Confirm the figures with your adviser', 35)]),
    CHK('slow_season', 'Slow-Season Cash Plan', 'forecast', 'forecast.month', [('Find the months below the floor', -60), ('Book tune-ups to fill slow weeks', -45), ('Ask for deposits on installs', -30), ('Plan the supplier payments', -21), ('Review the plan each month', 0)]),
    CHK('year_end', 'Year-end Accountant Paperwork', 'pnl', 'pnl.month', [('Collect the invoices and payments', 0), ('Collect the supplier bills and expenses', 7), ('Check the tax set-aside', 14), ('Send the pack to the accountant', 21), ('File the copies', 28)]),
]
assert len(checklists) == 12
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('c_invoice', 'Customer: your invoice is attached', 'invoices', 'invoices.phone', 'Hello, your invoice {invoice_id} for {amount} at {site_ref} is attached. {company}'),
    M('c_deposit', 'Customer: your deposit holds your date', 'invoices', 'invoices.phone', 'Hello, your deposit of {deposit_asked} holds your date for {site_ref}. {company}'),
    M('c_thanks', 'Customer: thank you for your payment', 'payments', 'payments.phone', 'Hello, thank you for your payment of {amount} on {date} for {site_ref}. {company}'),
    M('c_friendly', 'Customer: friendly reminder, due date', 'invoices', 'invoices.phone', 'Hello, a friendly reminder that invoice {invoice_id} for {balance} is due {due_date}. {company}'),
    M('c_pastdue', 'Customer: your invoice is days past due', 'invoices', 'invoices.phone', 'Hello, invoice {invoice_id} for {balance} is {days_past_due} days past due. Please contact {company}.'),
    M('c_tell', 'Customer: tell us when you can pay', 'invoices', 'invoices.phone', 'Hello, invoice {invoice_id} has a balance of {balance}. Please tell us when you can pay. {company}'),
    M('c_plan', 'Customer: a payment plan we can offer', 'invoices', 'invoices.phone', 'Hello, we can offer a payment plan for the balance of {balance} on invoice {invoice_id}. Reply to agree the dates. {company}'),
    M('c_financing', 'Customer: your financing offer is ready', 'invoices', 'invoices.phone', 'Hello, your financing offer for {site_ref}, invoice {invoice_id} for {amount}, is ready. {company}'),
    M('l_statement', 'Landlord: statement is attached', 'ageing', 'ageing.phone', 'Hello {account}, your statement dated {as_of} is attached: balance {balance}, oldest invoice {oldest_days} days. {company}'),
    M('l_pastdue', 'Landlord: invoice is days past due', 'chase', 'chase.phone', 'Hello {account}, invoice {invoice_id} is {days_past_due} days past due. {company}'),
    M('l_promise', 'Landlord: you promised payment by a date', 'chase', 'chase.phone', 'Hello {account}, you promised {promised_amount} by {promised_on}, please confirm. {company}'),
    M('l_before_job', 'Landlord: payment before the next job', 'ageing', 'ageing.phone', 'Hello {account}, we need payment of {over60} before the next job. {company}'),
    M('l_uptodate', 'Landlord: your account is up to date', 'ageing', 'ageing.phone', 'Hello {account}, thank you, your account is up to date. {company}'),
    M('t_note', 'Technician: finish the job note', 'unbilled', 'unbilled.tech_phone', 'Hello {technician}, please finish the job note so we can invoice {job_id} at {site_ref}. {company}'),
    M('t_paid', 'Technician: your job was paid', 'invoices', 'invoices.tech_phone', 'Hello {technician}, your job {job_id} was paid, thank you. {company}'),
    M('a_photos', 'Apprentice: upload the job photos', 'unbilled', 'unbilled.apprentice_phone', 'Hello {apprentice}, please upload the job photos for {job_id}. {company}'),
    M('om_unbilled', 'Office manager: jobs not invoiced', 'unbilled', 'unbilled.office_phone', 'Completed jobs not invoiced: {waiting_count}. Please invoice them today. {company}'),
    M('om_pastdue', 'Office manager: invoices past due', 'ageing', 'ageing.office_phone', 'Invoices past due: {past_due_count}. Please start the chase calls. {company}'),
    M('om_promises', 'Office manager: promises due this week', 'chase', 'chase.office_phone', 'Promises due this week: {promises_week}. Please check each one. {company}'),
    M('om_deposits', 'Office manager: deposits not collected', 'deposits', 'deposits.office_phone', 'Deposits not collected on {no_deposit_count} jobs. Please call before equipment is ordered. {company}'),
    M('ow_over60', 'Owner: money over 60 days', 'ageing', 'ageing.owner_phone', 'Money over 60 days is {over60_total}. {company}'),
    M('ow_oldest', 'Owner: the oldest invoice is days old', 'ageing', 'ageing.owner_phone', 'The oldest invoice is {oldest_all} days old. {company}'),
    M('ow_cash', 'Owner: cash now and the floor', 'cash', 'cash.owner_phone', 'Cash now is {cash_now}, the floor is {floor}. {company}'),
    M('ow_bill', 'Owner: the supplier bill takes cash down', 'bills', 'bills.owner_phone', 'The supplier bill on {due_date} takes cash to {cash_after_bill} if paid from cash now. {company}'),
    M('ow_lowest', 'Owner: the lowest cash month', 'forecast', 'forecast.owner_phone', 'The lowest cash month is {lowest_month}, at {lowest_cash}. {company}'),
    M('ow_cover', 'Owner: months of cover now', 'cash', 'cash.owner_phone', 'Months of cover now: {cover_now}. {company}'),
    M('ow_draw', 'Owner: the owner pay this month', 'forecast', 'forecast.owner_phone', 'The owner pay this month can be {safe_pay}. {company}'),
    M('ow_tax', 'Owner: tax set-aside this month', 'tax', 'tax.owner_phone', 'The tax set-aside this month is {set_aside}. Confirm with your adviser. {company}'),
    M('s_planned', 'Equipment supplier: payment is planned', 'bills', 'bills.supplier_phone', 'Hello, a payment of {amount} is planned for {due_date}. {company}'),
    M('s_move', 'Equipment supplier: move the payment', 'bills', 'bills.supplier_phone', 'Hello, can we move the payment of {amount} to {ask_date}? {company}'),
    M('p_paid', 'Parts counter: the statement is paid', 'purchases', 'purchases.parts_phone', 'Hello, the statement for {month} is paid. {company}'),
    M('e_sched', 'Electrical sub: invoice is scheduled', 'purchases', 'purchases.elec_phone', 'Hello, your invoice {po_id} for {amount} is scheduled for {due_date}. {company}'),
    M('m_sched', 'Sheet-metal sub: invoice is scheduled', 'purchases', 'purchases.sheet_phone', 'Hello, your invoice {po_id} for {amount} is scheduled for {due_date}. {company}'),
    M('ac_pack', 'Accountant: month-end pack is ready', 'pnl', 'pnl.acct_phone', 'Hello, the month-end pack for {month} is ready. {company}'),
]
assert len(messages) == 34, len(messages)

def CD(c, n): return '{range:%s},">="&({today}-%d)' % (c, n)
IV = lambda c: '{range:invoices.%s}' % c
BAL = IV('balance')
def BK(lo, hi=None): return 'SUMIFS(%s,%s,">=%d"%s)' % (BAL, IV('days_out'), lo, (',%s,"<=%d"' % (IV('days_out'), hi)) if hi else '')
kpis = [
    KPI('Invoiced this month', 'SUMIFS(%s,%s,%s)' % (IV('amount'), IV('month'), MS), 'money'),
    KPI('Invoiced, last 30 days', 'SUMIFS(%s,%s)' % (IV('amount'), CD('invoices.date', 30)), 'money'),
    KPI('Collected this month', 'SUMIFS({range:payments.amount},{range:payments.month},%s)' % MS, 'money'),
    KPI('Collected, last 30 days', 'SUMIFS({range:payments.amount},%s)' % CD('payments.date', 30), 'money'),
    KPI('Open invoices', 'SUM(%s)' % IV('open'), 'int'), KPI('Open balance', 'SUM(%s)' % BAL, 'money'),
    KPI('Balance 0-30 days', BK(0, 30), 'money'), KPI('Balance 31-60 days', 'SUMIFS(%s,%s,">30",%s,"<=60")' % (BAL, IV('days_out'), IV('days_out')), 'money'),
    KPI('Balance 61-90 days', 'SUMIFS(%s,%s,">60",%s,"<=90")' % (BAL, IV('days_out'), IV('days_out')), 'money'), KPI('Balance over 90 days', 'SUMIFS(%s,%s,">90")' % (BAL, IV('days_out')), 'money'),
    KPI('Balance over 60 days', 'SUMIFS(%s,%s,">60")' % (BAL, IV('days_out')), 'money'), KPI('Oldest open invoice, days', 'MAX(%s)' % IV('days_out'), 'int'),
    KPI('Invoices past due', 'COUNTIFS(%s,">0")' % IV('days_past_due'), 'int'), KPI('Money past due', 'SUMIFS(%s,%s,">0")' % (BAL, IV('days_past_due')), 'money'),
    KPI('Completed jobs not invoiced', 'SUM({range:unbilled.waiting})', 'int'), KPI('Money not yet invoiced', 'SUMIFS({range:unbilled.price},{range:unbilled.waiting},1)', 'money'),
    KPI('Average days to paid, last 90 days', 'IFERROR(AVERAGEIFS(%s,%s),0)' % (IV('days_to_paid'), CD('invoices.paid_on', 90)), 'num'),
    KPI('Share paid late, last 90 days', 'IFERROR(COUNTIFS(%s,%s,1)/COUNTIFS(%s,%s,">=0"),0)' % (CD('invoices.paid_on', 90), IV('paid_late'), CD('invoices.paid_on', 90), IV('days_to_paid')), 'pct'),
    KPI('Deposits collected, last 30 days', 'SUMIFS({range:payments.amount},{range:payments.kind},%s,%s)' % (tok('paykind', 'Deposit'), CD('payments.date', 30)), 'money'),
    KPI('Deposit share paid, last 90 days', 'IFERROR(SUMIFS(%s,%s)/SUMIFS(%s,%s),0)' % (IV('deposit_paid'), CD('invoices.date', 90), IV('deposit_asked'), CD('invoices.date', 90)), 'pct'),
    KPI('Financed jobs, last 90 days', 'COUNTIFS(%s,%s,%s)' % (IV('financing'), YES, CD('invoices.date', 90)), 'int'),
    KPI('Net profit last month', 'SUMIFS({range:pnl.net_profit},{range:pnl.month},EDATE(%s,-1))' % MS, 'money'),
    KPI('Net profit this month so far', 'SUMIFS({range:pnl.net_profit},{range:pnl.month},%s)' % MS, 'money'),
    KPI('Net profit percent, last 12 months', 'IFERROR(SUMIFS({range:pnl.net_profit},%s)/SUMIFS({range:pnl.revenue},%s),0)' % (L12('pnl.month'), L12('pnl.month')), 'pct'),
    KPI('Cash now', CASH_NOW, 'money'),
    KPI('Cash after equipment bills due in 7 days', '%s-SUMIFS({range:bills.amount},{range:bills.category},%s,{range:bills.due_date},"<="&({today}+7),{range:bills.paid},%s)' % (CASH_NOW, tok('billcat', 'Equipment'), NO), 'money'),
    KPI('Months of cover now', 'IFERROR(%s/%s,0)' % (CASH_NOW, FIXED3), 'num'), KPI('Lowest closing cash in the forecast', 'MIN({range:forecast.closing_cash})', 'money'),
    KPI('Owner draw and bonus this month', 'SUMIFS({range:cash.owner_draw},{range:cash.month},%s)+SUMIFS({range:cash.owner_bonus},{range:cash.month},%s)' % (MS, MS), 'money'),
    KPI('Tax set-aside year to date', 'SUMIFS({range:tax.set_aside},{range:tax.month},">="&DATE(YEAR({today}),1,1),{range:tax.month},"<="&%s)' % MS, 'money'),
]
assert len(kpis) == 30, len(kpis)
def DS(c, label): return {"label": label, "sum": "deposits." + c}
dashboard = {"title": "Invoices and Cash Dashboard", "kpis": kpis,
    "monthly": {"title": "Invoiced and collected by month", "date": "deposits.month", "series": [DS('invoiced', 'Invoiced'), DS('collected', 'Collected')]},
    "breakdowns": [{"title": "Invoices by status", "by": "invoices.status", "value": "invoices.balance", "agg": "count"}, {"title": "Invoices by payment method", "by": "invoices.method", "value": "invoices.amount", "agg": "count"},
                   {"title": "Open balance by site type", "by": "invoices.site_type", "value": "invoices.balance", "agg": "sum"}, {"title": "Purchases by supplier", "by": "purchases.supplier", "value": "purchases.amount", "agg": "sum"}]}
def CM(title, typ, tbl, col, label, agg='sum', date=None): return CHART(title, typ, 'month', [AGG(agg, tbl, '%s.%s' % (tbl, col), date='%s.%s' % (tbl, date or 'month'), label=label)])
def CM2(title, typ, tbl, cols, date=None): return CHART(title, typ, 'month', [AGG('sum', tbl, '%s.%s' % (tbl, c), date='%s.%s' % (tbl, date or 'month'), label=l) for c, l in cols])
def CNT(title, tbl, col, label): return CHART(title, 'bar', '%s.%s' % (tbl, col), [AGG('count', tbl, label=label)])
def BUCKET(label, lo, hi=None): return AGG('sum', 'invoices', 'invoices.balance', where=[('days_out', '>=', lo)] + ([('days_out', '<=', hi)] if hi else []), label=label)
insights = {"filters": [{"label": "Technician", "list": "tech"}, {"label": "Job type", "list": "jobtype"}, {"label": "Site type", "list": "sitetype"}],
    "gauges": [{"title": "Invoices paid on time", "num": AGG('count', 'invoices', where=[('paid_late', '=', 0)]), "den": AGG('count', 'invoices', where=[('paid_late', '>=', 0)])},
               {"title": "Balance under 60 days", "num": AGG('sum', 'invoices', 'invoices.balance', where=[('days_out', '<=', 60)]), "den": AGG('sum', 'invoices', 'invoices.balance')},
               {"title": "Jobs invoiced within the target", "num": AGG('count', 'unbilled', where=[('in_time', '=', 1)]), "den": AGG('count', 'unbilled', where=[('in_time', '>=', 0)])},
               {"title": "Deposits collected", "num": AGG('sum', 'deposits', 'deposits.deposits_paid'), "den": AGG('sum', 'deposits', 'deposits.deposits_asked')},
               {"title": "Forecast months above the floor", "num": AGG('count', 'forecast', where=[('below', '=', 0)]), "den": AGG('count', 'forecast')},
               {"title": "Forecast months with cover met", "num": AGG('count', 'forecast', where=[('months_cover', '>=', '{set:cover_months}')]), "den": AGG('count', 'forecast')}],
    "charts": [
        CM('Invoiced per month', 'column', 'deposits', 'invoiced', 'Invoiced'),
        CM2('Collected per month', 'stacked', 'deposits', [('collected_invoices', 'On invoices'), ('collected_deposits', 'Deposits'), ('collected_fees', 'Agreement fees')]),
        CNT('Invoices by status', 'invoices', 'status', 'Invoices'), CNT('Invoices by payment method', 'invoices', 'method', 'Invoices'), CNT('Invoices by site type', 'invoices', 'site_type', 'Invoices'), CHART('Invoices by job type', 'bar', 'dtp_job.job_type', [AGG('sum', 'dtp_job', 'dtp_job.invoices', label='Invoices')]),
        CHART('Balance by ageing bucket and site type', 'stacked', 'invoices.site_type', [BUCKET('0-30 days', 0, 30), BUCKET('31-60 days', 31, 60), BUCKET('61-90 days', 61, 90), BUCKET('Over 90 days', 91)]),
        CHART('Balance by account', 'bar', 'ageing.account', [AGG('sum', 'ageing', 'ageing.balance', label='Balance')]),
        CM('Days to paid per month', 'line', 'deposits', 'avg_days', 'Days to paid', 'avg'), CM('Chase contacts per month', 'column', 'chase', 'chase_id', 'Chase contacts', 'count', 'date') if False else CHART('Chase contacts per month', 'column', 'month', [AGG('count', 'chase', date='chase.date', label='Chase contacts')]),
        CNT('Chase outcomes', 'chase', 'outcome', 'Chase contacts'),
        CM2('Deposits per month', 'column', 'deposits', [('deposits_asked', 'Asked'), ('deposits_paid', 'Paid')]),
        CM('Financed jobs per month', 'column', 'financing', 'financed_jobs', 'Financed jobs'), CM('Revenue per month', 'column', 'pnl', 'revenue', 'Revenue'), CM('Net profit per month', 'column', 'pnl', 'net_profit', 'Net profit'),
        CM2('Cash in and net cash per month', 'column', 'cash', [('cash_in', 'Cash in'), ('net', 'Net cash')]),
        CM2('Costs per month', 'stacked', 'cash', [('payroll', 'Payroll'), ('purchases', 'Purchases'), ('overhead', 'Overhead')]),
        CM('Closing cash per month', 'line', 'cash', 'closing_cash', 'Closing cash'),
        CM2('Owner draw per month', 'stacked', 'cash', [('owner_draw', 'Owner draw'), ('owner_bonus', 'Owner bonus')]),
        CM('Tax set-aside per month', 'column', 'tax', 'set_aside', 'Set-aside'), CM('Purchases per month', 'column', 'purchases', 'amount', 'Purchases', date='date'),
        CHART('Revenue by season', 'bar', 'pnl.season', [AGG('sum', 'pnl', 'pnl.revenue', label='Revenue')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6, len(insights['charts'])
signature = [
    {"name": "Not Invoiced Warning", "why": "completed jobs with no invoice are ranked by value and age, so money you earned is never left unbilled", "where": "Not Invoiced Warning"},
    {"name": "Ageing Analyser", "why": "open invoices are grouped by days outstanding with the oldest accounts named and a red, amber or green light", "where": "Ageing Analyser"},
    {"name": "Chase List", "why": "overdue invoices ranked by amount times days past due, with the next action for each and the money your weekly calls cover", "where": "Chase List"},
    {"name": "Seasonal Cash Forecast", "why": "12 months of cash from your own history and a cash index for each season, with the lowest month against your floor", "where": "Seasonal Cash Forecast"},
    {"name": "Slow-Summer Test", "why": "cut the cooling season cash in and see the lowest cash, with base, best and worst rows and a sensitivity row", "where": "Slow-Summer Test"},
    {"name": "Supplier Bill Check", "why": "a bill due this week against cash now: pay now, pay on the due date, negotiate terms or delay and ask", "where": "Supplier Bill Check"},
    {"name": "Safe Owner Draw", "why": "the monthly owner pay that profit after tax set-aside and your cash plan can both carry, as one closed-form number", "where": "Safe Owner Draw"},
    {"name": "Landlord Account Review", "why": "each account's balance, oldest invoice and share past terms with a pre-pay, reduce terms or keep verdict", "where": "Landlord Account Review"},
    {"name": "Profit and Loss by Season", "why": "heating, cooling and shoulder seasons against the same months a year earlier, naming the season carrying the year", "where": "Profit and Loss by Season"},
    {"name": "Break-even Revenue Solver", "why": "fixed costs, owner draw and margin give the revenue and jobs a week you must bill, with a minus and plus 10 percent margin row", "where": "Break-even Revenue Solver"}]
competitors = [
    {"what": "field-service app with a per-technician fee", "lacks": "charges each person every month, sends invoices but does not forecast seasonal cash or test a slow summer"},
    {"what": "generic invoice template", "lacks": "prints an invoice but has no ageing, no chase list, no promises and no deposits on installs"},
    {"what": "single-sheet quote calculator", "lacks": "prices one job but cannot show unbilled jobs, days to paid or the cash left after a supplier bill"},
    {"what": "pen-and-paper job book", "lacks": "keeps no running balance, so old invoices, broken promises and a cash dip in a slow season go unseen"}]
guide = [
    'Open Start and type your company name and your own limits in the yellow cells: the cash floor, the days to invoice a job, the owner draw, the tax set-aside percent (confirm with your adviser) and the share of weekly cash in you count on.',
    'Check Customer Accounts and Seasons. They hold your landlord and business accounts with their terms and the demand of each month.',
    'Enter each invoice on Invoices with its dates, amount, deposit and balance, and each payment on Payments. Days outstanding, the ageing bucket and the next action fill in by themselves.',
    'Type each completed job on Completed Jobs and the invoice number once billed. Jobs still waiting show with their days and a flag.',
    'Write each chase contact on Chase Log with the promised date and amount. Ageing by Account and the Chase List read it.',
    'Type the month starts on Deposits and Collections and Financing Used, and fill Profit and Loss, Cash by Month and Tax Set-aside each month.',
    'List supplier bills on Upcoming Bills and purchases on Purchases. Cash after each bill and the floor check calculate themselves.',
    'Type the 12 month starts on Cash Forecast. Closing cash, months of cover and the safe owner pay fill in from your own history.',
    f'Use the {len(tools)} tools: each answers one question with a verdict. Change the yellow inputs to try another day limit, cut or owner pay.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Invoices and Cash Dashboard and the Charts every week. A one-person owner-operator with one van uses the same sheets; a shop with a dispatcher uses the office columns.']
listing = {"title": "HVAC and Plumbing Contractor Excel Template: Invoices, Collections, Ageing, Chase List, Seasonal Cash Forecast, Owner Draw",
    "headline": "Get paid and stay liquid through the seasons: invoices, ageing and cash",
    "tags": ["hvac template", "plumbing template", "invoice tracker", "ageing report", "cash flow forecast", "contractor excel", "service business", "collections", "owner draw", "deposit tracker", "profit and loss", "field service", "tradesman"],
    "description": ("Get paid on time and see the cash dip before it arrives, in one Excel workbook built for an owner-run HVAC and plumbing contractor with 1 to 15 technicians and an office manager who also dispatches. "
        "A one-person owner-operator with one van uses the same sheets; a shop with a dispatcher uses the office columns.\n\n"
        "Invoices keeps each invoice with its deposit asked and paid, balance, due date, financing used and method, and works out the days outstanding, the ageing bucket, the days past due and the next action. "
        "Completed Jobs shows the jobs finished but not invoiced. Ageing by Account groups unpaid invoices by days outstanding for each landlord and business account. The Chase Log keeps promises, amounts and outcomes. "
        "Cash by Month, Profit and Loss, Tax Set-aside, Upcoming Bills and Cash Forecast show the money side of the seasons, with a cash index for each month taken from your own history.\n\n"
        f"{len(tools)} tools answer weekly questions with a clear verdict: the complete-but-not-invoiced warning, the ageing analyser, the chase list, a promise tracker, days to paid, a landlord account review, a write-off check, a seasonal cash forecast, a slow-summer test, a supplier bill and cash floor check, a safe owner draw, a tax set-aside tool, a break-even solver and profit and loss by season. "
        f"Print {len(forms)} sheets and {len(documents)} documents such as the invoice, the statement and the reminder letters, follow {len(checklists)} checklists and send {len(messages)} ready text messages to customers, accounts, technicians, your office, the owner, your supplier and the accountant.\n\n"
        "This is part seven of the HVAC and Plumbing Contractor suite. A standard .xlsx workbook with no macros and no per-technician fee: you keep your data. A demo copy full of sample data and a blank copy are included. It helps you keep track of your business and does not promise results."),
    "features": ["Invoice register with deposit, balance and days outstanding", "Completed jobs not invoiced, ranked by value and age", "Ageing by account with a pre-pay, reduce terms or keep verdict",
                 "Chase list ranked by amount times days past due", "Promise tracker for promised and broken payments", "Seasonal cash forecast from your own history with a cash index",
                 "Slow-summer test with base, best, worst and sensitivity rows", "Supplier bill check against your cash floor", "Safe owner draw and tax set-aside (confirm with your adviser)",
                 f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
TOOLH = {}
s = spec(id=f'{SUITE}-p7', slug='hvac-plumbing-invoices-cash', profession='HVAC and Plumbing Contractor', name='Invoices, Collections and Cash',
         tagline='Get paid on time and see the cash dip before it arrives', price_usd=29,
         colors={"primary": "#1F4E5F", "accent": "#E07A3F"}, settings=settings, lists=base_lists + ck_lists(), tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 7, "of": 8, "focus": "Invoices, collections and seasonal cash"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hv7.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'lists', len(s['lists']))
