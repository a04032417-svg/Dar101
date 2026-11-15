"""Author and Self-Publisher Business suite - part 3: Sales and Royalties Ledger."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au3_lists import *
from au3_tables import settings, tables, MS
from au3_tools import tools
import au3_data as D

SUITE = 'fx-20261115-author-publisher'
NOTE = 'Sample wording: adapt it to your own business. Check each store\'s current terms and confirm tax questions with your adviser.'
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
EXP, OPN, SPD, PDD = tok('ststatus', 'Expected'), tok('ststatus', 'Open'), tok('ststatus', 'Short-paid'), tok('ststatus', 'Paid')
ABOVE, WITHIN, LIVE = tok('flag', 'Above limit'), tok('flag', 'Within limit'), tok('estatus', 'Live')

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('sales_entry', 'Monthly Sales Entry Sheet', 'Sales line with royalty per copy', 'sales.sale_id', F(
        ('Month', 'sales.month'), ('Edition ID', 'sales.edition_id'), ('Title', 'sales.title'), ('Format', 'sales.format'), ('Store', 'sales.store'), ('Country', 'sales.country'), ('Currency', 'sales.currency'),
        ('Copies', 'sales.units'), ('Returns', 'sales.returns'), ('Gross, store currency', 'sales.gross'), ('Royalty, store currency', 'sales.royalty'), ('Rate per 100 units', 'sales.rate'), ('Royalty, home currency', 'sales.royalty_home')) + [
        FF('Royalty per copy, home currency', 'IFERROR(%s/%s,0)' % (LK('sales', 'sale_id', 'royalty_home'), LK('sales', 'sale_id', 'units')), 'money'),
        FF('Returns, share of copies sold', 'IFERROR(%s/(%s+%s),0)' % (LK('sales', 'sale_id', 'returns'), LK('sales', 'sale_id', 'units'), LK('sales', 'sale_id', 'returns')), 'pct')]),
    FORM('statement_entry', 'Store Statement Entry Sheet', 'Store statement with expected and paid dates', 'statements.statement_id', F(
        ('Month', 'statements.month'), ('Store', 'statements.store'), ('Statement amount', 'statements.statement_amount'), ('Expected on', 'statements.expected_on'), ('Paid on', 'statements.paid_on'), ('Received', 'statements.received'),
        ('Status', 'statements.status'), ('Days overdue', 'statements.days_overdue'), ('Days to pay', 'statements.days_to_pay'), ('Short by', 'statements.short_by')) + [
        FF('Payment delay of this store, days', 'SUMIFS({range:stores.delay_days},{range:stores.store},%s)' % LK('statements', 'statement_id', 'store'), 'int'),
        FF('Statements of this store in the sheet', 'COUNTIFS({range:statements.store},%s)' % LK('statements', 'statement_id', 'store'), 'int')]),
    FORM('payment_sheet', 'Payment Received Sheet', 'Payment received with fees and exchange loss', 'payments.payment_id', F(
        ('Statement ID', 'payments.statement_id'), ('Store', 'payments.store'), ('Month paid for', 'payments.month'), ('Received on', 'payments.received_on'), ('Statement amount', 'payments.statement_amount'), ('Fee', 'payments.fee'),
        ('Exchange loss', 'payments.fx_loss'), ('Received', 'payments.received'), ('Short, not explained by fees', 'payments.unexplained')) + [
        FF('Fees and loss, share of the statement', 'IFERROR((%s+%s)/%s,0)' % (LK('payments', 'payment_id', 'fee'), LK('payments', 'payment_id', 'fx_loss'), LK('payments', 'payment_id', 'statement_amount')), 'pct'),
        FF('Days after the month ended', '%s-EOMONTH(%s,0)' % (LK('payments', 'payment_id', 'received_on'), LK('payments', 'payment_id', 'month')), 'int')]),
    FORM('short_query', 'Short-Payment Query Sheet', 'Payment under its statement, the amount to claim', 'payments.payment_id', F(
        ('Store', 'payments.store'), ('Month paid for', 'payments.month'), ('Statement amount', 'payments.statement_amount'), ('Fee', 'payments.fee'), ('Exchange loss', 'payments.fx_loss'), ('Received', 'payments.received'),
        ('Short, not explained by fees', 'payments.unexplained'), ('Assistant phone', 'payments.va_phone')) + [
        FF('Amount to claim', 'IF(%s>{set:short_tolerance},%s,0)' % (LK('payments', 'payment_id', 'unexplained'), LK('payments', 'payment_id', 'unexplained')), 'money'),
        FF('Your tolerance', '{set:short_tolerance}', 'money'),
        FF('Statements of this store paid short', 'COUNTIFS({range:statements.store},%s,{range:statements.status},%s)' % (LK('payments', 'payment_id', 'store'), SPD), 'int')]),
    FORM('fx_update', 'Exchange Rate Update Sheet', 'Rate of a month against your base rate', 'curmonth.row_id', F(
        ('Month', 'curmonth.month'), ('Currency', 'curmonth.currency'), ('Royalty, store currency', 'curmonth.amount_store'), ('Rate used per 100', 'curmonth.rate_used'), ('Base rate per 100', 'curmonth.base_rate'),
        ('Royalty, home currency', 'curmonth.home_amount'), ('Effect of the rate', 'curmonth.effect_home')) + [
        FF('Highest rate used for this currency', 'SUMPRODUCT(MAX(({range:curmonth.currency}=%s)*{range:curmonth.rate_used}))' % LK('curmonth', 'row_id', 'currency'), 'num'),
        FF('Lowest rate used for this currency', 'SUMPRODUCT(MIN(({range:curmonth.currency}=%s)*{range:curmonth.rate_used}+({range:curmonth.currency}<>%s)*99999))' % (LK('curmonth', 'row_id', 'currency'), LK('curmonth', 'row_id', 'currency')), 'num'),
        FF('Effect of this currency, all months', 'SUMIFS({range:curmonth.effect_home},{range:curmonth.currency},%s)' % LK('curmonth', 'row_id', 'currency'), 'money')]),
    FORM('pageread_sheet', 'Page-Read Entry Sheet', 'Page reads with income at your own rate', 'pagereads.read_id', F(
        ('Month', 'pagereads.month'), ('Edition ID', 'pagereads.edition_id'), ('Title', 'pagereads.title'), ('Pages read', 'pagereads.pages_read'), ('Pay per 1,000 pages', 'pagereads.rate'), ('Income, estimate', 'pagereads.income')) + [
        FF('Income at your own rate', '%s/1000*{set:page_read_rate}' % LK('pagereads', 'read_id', 'pages_read'), 'money'),
        FF('Difference against your own rate', '%s-%s/1000*{set:page_read_rate}' % (LK('pagereads', 'read_id', 'income'), LK('pagereads', 'read_id', 'pages_read')), 'money'),
        FF('Pages read of this title, all months', 'SUMIFS({range:pagereads.pages_read},{range:pagereads.title_id},%s)' % LK('pagereads', 'read_id', 'title_id'), 'int')]),
    FORM('fee_check', 'Fee Check Sheet', 'Fees and exchange loss against your limit', 'fees.payment_id', F(
        ('Store', 'fees.store'), ('Month', 'fees.month'), ('Statement amount', 'fees.statement_amount'), ('Fee', 'fees.fee'), ('Exchange loss', 'fees.fx_loss'), ('Fees and loss, share of statement', 'fees.fee_share'), ('Limit check', 'fees.flag')) + [
        FF('Your flag limit', '{set:fee_flag_pct}', 'pct'),
        FF('Fees and loss allowed at the limit', '%s*{set:fee_flag_pct}' % LK('fees', 'payment_id', 'statement_amount'), 'money'),
        FF('Payments of this store above the limit', 'COUNTIFS({range:fees.store},%s,{range:fees.flag},%s)' % (LK('fees', 'payment_id', 'store'), ABOVE), 'int')]),
    FORM('close_sheet', 'Month Close Sheet', 'Month with its largest stores and open statements', 'depmonth.month', F(
        ('Royalty of the month', 'depmonth.month_total'), ('Largest store', 'depmonth.largest_store'), ('Largest store share', 'depmonth.largest_share'), ('Second store', 'depmonth.second_store'),
        ('Second store share', 'depmonth.second_share'), ('Limit check', 'depmonth.flag'), ('Against the same month last year', 'depmonth.vs_last_year')) + [
        FF('Statements still open for the month', 'COUNTIFS({range:statements.month},{pick},{range:statements.status},%s)' % OPN, 'int'),
        FF('Statement amount of the month', 'SUMIFS({range:statements.statement_amount},{range:statements.month},{pick})', 'money'),
        FF('Page-read income of the month', 'SUMIFS({range:pagereads.income},{range:pagereads.month},{pick})', 'money')]),
    FORM('missing_sheet', 'Missing Sale Report Sheet', 'Edition with no sale this month', 'edroy.edition_id', F(
        ('Title', 'edroy.title'), ('Format', 'edroy.format'), ('Status', 'edroy.status'), ('Copies, 12 months', 'edroy.units'), ('Copies, 3 months', 'edroy.units_3m'), ('Copies this month', 'edroy.units_month'),
        ('Months with a sale', 'edroy.months_sold'), ('Royalty, 12 months', 'edroy.royalty_home')) + [
        FF('Royalty a month on average', '%s/12' % LK('edroy', 'edition_id', 'royalty_home'), 'money'),
        FF('A sale is expected', 'IF(%s>={set:min_months_sold},1,0)' % LK('edroy', 'edition_id', 'months_sold'), 'int'),
        FF('Editions of this title', 'COUNTIFS({range:edroy.title_id},%s)' % LK('edroy', 'edition_id', 'title_id'), 'int')]),
    FORM('terms_sheet', 'Store Terms Check Sheet', 'Store terms and how the store really pays', 'stores.store', F(
        ('Royalty share, check current terms', 'stores.royalty_share'), ('Delay, days', 'stores.delay_days')) + [
        FF('Statements in the last 12 months', 'COUNTIFS({range:statements.store},{pick},{range:statements.month},">="&EDATE(%s,-12))' % MS, 'int'),
        FF('Average days to pay after expected', 'IFERROR(AVERAGEIFS({range:statements.days_to_pay},{range:statements.store},{pick}),0)', 'num'),
        FF('Royalty, last 12 months', 'SUMIFS({range:mstore.royalty_home},{range:mstore.store},{pick},{range:mstore.month},">="&EDATE(%s,-12),{range:mstore.month},"<"&%s)' % (MS, MS), 'money'),
        FF('Share of all royalties, 12 months', 'IFERROR(SUMIFS({range:mstore.royalty_home},{range:mstore.store},{pick},{range:mstore.month},">="&EDATE(%s,-12),{range:mstore.month},"<"&%s)/SUMIFS({range:mstore.royalty_home},{range:mstore.month},">="&EDATE(%s,-12),{range:mstore.month},"<"&%s),0)' % (MS, MS, MS, MS), 'pct'),
        FF('Unpaid now', 'SUMIFS({range:statements.statement_amount},{range:statements.store},{pick},{range:statements.status},%s)+SUMIFS({range:statements.statement_amount},{range:statements.store},{pick},{range:statements.status},%s)' % (EXP, OPN), 'money'),
        FF('Statements paid short', 'COUNTIFS({range:statements.store},{pick},{range:statements.status},%s)' % SPD, 'int')]),
    FORM('edition_sheet', 'Edition Royalty Sheet', 'Edition price, plan and actual royalty per copy', 'editions.edition_id', F(
        ('Title', 'editions.title'), ('Format', 'editions.format'), ('List price', 'editions.list_price'), ('Cost of one copy', 'editions.unit_cost'), ('Royalty share', 'editions.royalty_share'), ('Status', 'editions.status'),
        ('Plan royalty per copy', 'editions.royalty_per_copy')) + [
        FF('Actual royalty per copy, 12 months', 'IFERROR(INDEX({range:edroy.royalty_per_copy},MATCH({pick},{range:edroy.edition_id},0)),0)', 'money'),
        FF('Copies sold, 12 months', 'IFERROR(INDEX({range:edroy.units},MATCH({pick},{range:edroy.edition_id},0)),0)', 'int'),
        FF('Actual against plan', 'IFERROR(INDEX({range:edroy.royalty_per_copy},MATCH({pick},{range:edroy.edition_id},0))-%s,0)' % LK('editions', 'edition_id', 'royalty_per_copy'), 'money')]),
    FORM('country_sheet', 'Country Sales Entry Sheet', 'Country and format with growth and sales tax', 'ctyfmt.row_id', F(
        ('Country', 'ctyfmt.country'), ('Format', 'ctyfmt.format'), ('Copies, 12 months', 'ctyfmt.units'), ('Royalty, 12 months', 'ctyfmt.royalty_home'), ('Royalty, 12 months before', 'ctyfmt.royalty_prev'),
        ('Copies this month', 'ctyfmt.units_month'), ('Share of all', 'ctyfmt.share'), ('Country, 12 months', 'ctyfmt.country_total'), ('Country growth', 'ctyfmt.country_growth')) + [
        FF('Change of this row', '%s-%s' % (LK('ctyfmt', 'row_id', 'royalty_home'), LK('ctyfmt', 'row_id', 'royalty_prev')), 'money'),
        FF('Sales tax of the country (adviser)', 'SUMIFS({range:countries.sales_tax_pct},{range:countries.country},%s)' % LK('ctyfmt', 'row_id', 'country'), 'pct'),
        FF('Currency of the country', 'INDEX({range:countries.currency},MATCH(%s,{range:countries.country},0))' % LK('ctyfmt', 'row_id', 'country'), 'text')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
def DC(k, sheet, title, pick, paras, sign): return DOC(k, sheet, title, pick, paras, sign, NOTE)
documents = [
    DC('monthly_report', 'Monthly Royalty Report', 'Monthly royalty report for a store', 'mstore.row_id', [
        'Monthly royalty report of {set:company}, dated {today}. Store: {col:mstore.store}. Month: {col:mstore.month}.',
        'Copies sold: {col:mstore.units}. Royalty in the home currency: {col:mstore.royalty_home}. This is {col:mstore.share} of the royalties of the month, which were {col:mstore.month_total} in all stores.',
        'Figures from stores are estimates until the payment arrives. The royalty of the twelve months to this month for this store is {col:mstore.store_12m}.', 'Check each store\'s current terms before you rely on a share or a delay.'], ['Author-publisher', 'Assistant']),
    DC('statement_summary', 'Store Statement Summary', 'Summary of one store statement', 'statements.statement_id', [
        'Statement summary of {set:company}, dated {today}. Statement {col:statements.statement_id} of {col:statements.store} for {col:statements.month}.',
        'Statement amount: {col:statements.statement_amount}. Expected on {col:statements.expected_on}. Paid on {col:statements.paid_on}. Received: {col:statements.received}. Status: {col:statements.status}.',
        'Days to pay after the expected date: {col:statements.days_to_pay}. Days overdue now: {col:statements.days_overdue}. Short by: {col:statements.short_by}.', 'File this summary with the statement of the store.'], ['Author-publisher', 'Assistant']),
    DC('short_letter', 'Short-Payment Letter', 'Short-payment query letter to a store', 'payments.payment_id', [
        'Letter of {set:company}, dated {today}. To the royalty team of {col:payments.store}. Subject: payment {col:payments.payment_id} for {col:payments.month}.',
        'Your statement for {col:payments.month} shows {col:payments.statement_amount}. The payment of {col:payments.received_on} was {col:payments.received}, after a fee of {col:payments.fee} and an exchange loss of {col:payments.fx_loss}. A difference of {col:payments.unexplained} is not explained.',
        'Please check the payment against the statement and tell us the reason for the difference. If an amount is owed, please send it with your next payment.', 'Thank you for your help. Please reply to the contact below.'], ['Author-publisher', 'Store contact']),
    DC('overdue_reminder', 'Overdue Statement Reminder', 'Reminder to a store for an unpaid statement', 'statements.statement_id', [
        'Reminder of {set:company}, dated {today}. To the royalty team of {col:statements.store}. Statement {col:statements.statement_id} for {col:statements.month}.',
        'Our records show a statement amount of {col:statements.statement_amount}, expected on {col:statements.expected_on}. Status in our records: {col:statements.status}. Days past the expected date: {col:statements.days_overdue}.',
        'Please confirm the payment date or tell us if a document is missing on your side.', 'Thank you. We keep a copy of this reminder with the statement.'], ['Author-publisher', 'Store contact']),
    DC('title_report', 'Royalty by Title Report', 'Royalty report for one title', 'titles.title_id', [
        'Royalty report of {set:company}, dated {today}. Title: {col:titles.title}, written as {col:titles.pen_name}. Series: {col:titles.series}. Released on {col:titles.release_date}. Status: {col:titles.status}.',
        'Royalties of the last 12 months: {col:titles.royalty_12m}. Page-read income of the last 12 months (an estimate): {col:titles.pr_12m}. Total: {col:titles.total_12m}, which is {col:titles.share_12m} of all titles.',
        'Use this page with the production cost of the title to see whether it has earned back what it cost.', 'Figures from stores are estimates until the payment arrives.'], ['Author-publisher', 'Assistant']),
    DC('format_report', 'Royalty by Format Report', 'Royalty report for a format and month', 'mformat.row_id', [
        'Royalty by format of {set:company}, dated {today}. Format: {col:mformat.format}. Month: {col:mformat.month}.',
        'Copies sold: {col:mformat.units}. Royalty in the home currency: {col:mformat.royalty_home}, which is {col:mformat.share} of the month. The format earned {col:mformat.format_12m} in the twelve months to this month.',
        'Compare the share with the share you want for this format and decide where to push next.', 'Figures from stores are estimates until the payment arrives.'], ['Author-publisher', 'Assistant']),
    DC('pageread_report', 'Page-Read Income Report', 'Page-read income report for a month', 'prmonth.month', [
        'Page-read income report of {set:company}, dated {today}. Month: {col:prmonth.month}.',
        'Pages read: {col:prmonth.pages_read}. Income (an estimate that moves every month): {col:prmonth.income}. Pay per 1,000 pages: {col:prmonth.avg_rate}. Against last month: {col:prmonth.change_prev}.',
        'This is {col:prmonth.share_all} of all royalties of the month ({col:prmonth.royalties}). At a rate one step lower the income would be {col:prmonth.income_minus}, one step higher {col:prmonth.income_plus}.', 'The rate is your own number and the payment may differ.'], ['Author-publisher', 'Assistant']),
    DC('fx_fee_report', 'Exchange and Fee Report', 'Exchange rate effect report for a currency and month', 'curmonth.row_id', [
        'Exchange report of {set:company}, dated {today}. Currency: {col:curmonth.currency}. Month: {col:curmonth.month}.',
        'Royalty in the store currency: {col:curmonth.amount_store}. Rate used per 100 units: {col:curmonth.rate_used}. Your base rate per 100 units: {col:curmonth.base_rate}.',
        'Royalty in the home currency: {col:curmonth.home_amount}. Effect of the rate against your base rate: {col:curmonth.effect_home}.', 'Ask your adviser how to record exchange effects.'], ['Author-publisher', 'Accountant']),
    DC('yearend_summary', 'Year-End Royalty Summary', 'Year-end royalty summary for the accountant', 'mstore.row_id', [
        'Year-end royalty summary of {set:company}, dated {today}, for the accountant. Store: {col:mstore.store}.',
        'Royalties in the twelve months to {col:mstore.month}: {col:mstore.store_12m}. Royalties of that month in all stores: {col:mstore.month_total}.',
        'Amounts are in the home currency, converted with the rate of each month. Figures from stores are estimates until the payment arrives.', 'Please confirm with your adviser how to treat each amount under your local tax rules.'], ['Author-publisher', 'Accountant']),
    DC('terms_summary', 'Store Terms Summary', 'Store terms you currently use', 'stores.store', [
        'Store terms summary of {set:company}, dated {today}. Store: {col:stores.store}.',
        'Royalty share used in this workbook: {col:stores.royalty_share}. Payment delay used: {col:stores.delay_days} days after month end.',
        'These are your own working numbers. Check each store\'s current terms and update the Stores sheet when a store changes them.', 'Write the date of your last check below.'], ['Author-publisher', 'Assistant']),
    DC('country_report', 'Sales by Country Report', 'Sales report for a country and format', 'ctyfmt.row_id', [
        'Sales by country of {set:company}, dated {today}. Country: {col:ctyfmt.country}. Format: {col:ctyfmt.format}.',
        'Copies in the last 12 months: {col:ctyfmt.units}. Royalty: {col:ctyfmt.royalty_home}, against {col:ctyfmt.royalty_prev} in the 12 months before. Share of all royalties: {col:ctyfmt.share}.',
        'The country earned {col:ctyfmt.country_total} in all formats, a change of {col:ctyfmt.country_growth}. Copies this month: {col:ctyfmt.units_month}.', 'Sales tax is not income: confirm with your adviser how it is shown.'], ['Author-publisher', 'Assistant']),
    DC('close_report', 'Month Close Report', 'Month close report', 'depmonth.month', [
        'Month close report of {set:company}, dated {today}. Month: {col:depmonth.month}.',
        'Royalties of the month: {col:depmonth.month_total}. Largest store: {col:depmonth.largest_store} with {col:depmonth.largest_share}. Second store: {col:depmonth.second_store} with {col:depmonth.second_share}. Limit check: {col:depmonth.flag}.',
        'Against the same month last year: {col:depmonth.vs_last_year}. Close the month only when every store has sent its statement or you have written down the missing ones.', 'Sign when the month is closed.'], ['Author-publisher', 'Assistant']),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('weekly_entry', 'Weekly Sales Entry', 'sales', 'sales.month', [('Download the sales report of every store', 0), ('Enter the lines in the Sales ledger', 1), ('Check copies and returns against the report', 1), ('Check the rate of the month', 2), ('Note any store that has not reported', 3), ('Ask the assistant to file the reports', 3)]),
    CHK('month_close', 'Month Close Steps', 'depmonth', 'depmonth.month', [('List the stores that have sent a report', 3), ('Download the statements that are ready', 5), ('Enter the monthly totals by store and format', 7), ('Update the exchange rates of the month', 7), ('Enter the page reads', 8), ('Check the largest store share', 9), ('Write down the stores still missing', 10), ('Sign the month close report', 12)]),
    CHK('match_payments', 'Payment Matching Steps', 'payments', 'payments.received_on', [('Enter the payment in Payments received', 0), ('Find its statement in Statements', 0), ('Check the amount received against the statement', 1), ('Enter the fee and the exchange loss', 1), ('Mark the statement paid', 1), ('Flag a payment that is short', 2), ('File the bank line with the statement', 3)]),
    CHK('short_followup', 'Short-Payment Follow-up', 'payments', 'payments.received_on', [('Work out the amount that fees do not explain', 0), ('Write the query letter to the store', 1), ('Send the letter and keep a copy', 2), ('Wait for the store to answer', 9), ('Remind the store if there is no answer', 16), ('Escalate in writing if it is still open', 30), ('Record the amount recovered', 45)]),
    CHK('fx_update', 'Exchange Rate Update Steps', 'curmonth', 'curmonth.month', [('Look up the rates of the month from your bank', 2), ('Enter the rate used for each currency', 3), ('Compare with your base rate', 4), ('Check the effect in the home currency', 5), ('Update the base rate if it has moved a lot', 6)]),
    CHK('pageread_entry', 'Page-Read Entry Steps', 'pagereads', 'pagereads.month', [('Download the page-read report of the month', 5), ('Enter the pages read by edition', 6), ('Enter the pay per 1,000 pages', 6), ('Compare with the month before', 7), ('Mark the figure as an estimate until paid', 7), ('Check the income with the statement later', 75)]),
    CHK('terms_review', 'Store Terms Review', 'statements', 'statements.month', [('Open each store\'s current terms page', 0), ('Compare the royalty share with the Stores sheet', 1), ('Compare the payment delay with the real days to pay', 2), ('Update the Stores sheet', 3), ('Write the date of the check', 3), ('Tell the assistant about any change', 4)]),
    CHK('quarter_review', 'Quarterly Income Review', 'mformat', 'mformat.month', [('Compare royalties with the last 3 months', 30), ('Check the format mix', 31), ('Check the largest country', 32), ('Check the store dependence', 33), ('Check the page-read share', 34), ('Write three decisions', 40)]),
    CHK('yearend_pack', 'Year-End Royalty Pack', 'prmonth', 'prmonth.month', [('Print the royalty report by store', 30), ('Print the royalty report by title', 30), ('Print the payments received', 31), ('List the fees and the exchange loss', 32), ('Print the page-read income report', 33), ('Send the pack to your accountant', 40), ('Ask your adviser what is still missing', 45)]),
    CHK('new_store', 'Adding a New Store', 'mstore', 'mstore.month', [('Read the terms of the store', 0), ('Add the store to the Stores sheet', 1), ('Enter its royalty share and payment delay', 1), ('Add the store to the lists', 2), ('Enter the first monthly totals', 30), ('Check the first statement and payment', 90)]),
    CHK('missing_sale', 'Missing Sale Investigation', 'earned', 'earned.month', [('List the editions with no sale this month', 0), ('Check the store page of each edition', 1), ('Ask the store for the sales report of the edition', 2), ('Wait for the answer', 9), ('Correct the Sales ledger if lines were missing', 10), ('Note the cause', 11)]),
    CHK('fee_check', 'Currency and Fee Check', 'payments', 'payments.received_on', [('Open the Fee and exchange check sheet', 0), ('Look at the payments above your limit', 0), ('Check the fixed fee of each store', 1), ('Check the minimum payout of each store', 1), ('Decide whether to withdraw less often', 2), ('Write the decision', 3)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('va_week', 'Assistant: enter last week\'s sales', 'mstore', 'mstore.va_phone', 'Hello, please enter last week\'s sales for {store} in the Sales ledger. The royalty of {month} so far is {royalty_home}. Thank you. {company}'),
    M('va_pr', 'Assistant: enter the page reads', 'prmonth', 'prmonth.va_phone', 'Hello, please enter the page reads for {month} from the store report. Last time it was {pages_read} pages. Thank you. {company}'),
    M('va_dl', 'Assistant: download a statement', 'statements', 'statements.va_phone', 'Hello, please download the statement of {store} for {month} and save it with the others. It is expected on {expected_on}. Thank you. {company}'),
    M('va_missing', 'Assistant: a statement is missing', 'statements', 'statements.va_phone', 'Hello, the statement of {store} for {month} is still missing. Please check the store account and tell me today. {company}'),
    M('va_fx', 'Assistant: update the exchange rates', 'curmonth', 'curmonth.va_phone', 'Hello, please update the exchange rates for {month}. The {currency} rate used so far is {rate_used} per 100 units. Thank you. {company}'),
    M('va_match', 'Assistant: match a payment', 'payments', 'payments.va_phone', 'Hello, please match the payment {payment_id} of {received} from {store} to statement {statement_id}. Thank you. {company}'),
    M('va_check', 'Assistant: check an edition', 'edroy', 'edroy.va_phone', 'Hello, please check the edition {title} ({format}) with no sales this month. It sold in {months_sold} of the last 12 months. Thank you. {company}'),
    M('va_file', 'Assistant: file a statement', 'statements', 'statements.va_phone', 'Hello, please file statement {statement_id} of {store} for {month}, amount {statement_amount}, with the others. Thank you. {company}'),
    M('va_close', 'Assistant: prepare the month close', 'depmonth', 'depmonth.va_phone', 'Hello, please prepare the month close report for {month}. Royalties so far are {month_total}. Thank you. {company}'),
    M('ac_roy', 'Accountant: royalties of a month', 'mstore', 'mstore.acct_phone', 'Hello, royalties of {store} for {month} were {royalty_home}, which is {share} of the month. {company}'),
    M('ac_year', 'Accountant: the year-end summary', 'mstore', 'mstore.acct_phone', 'Hello, the year-end royalty summary for {store} is ready: {store_12m} in the 12 months to {month}. Please review it. {company}'),
    M('ac_short', 'Accountant: a payment was short', 'payments', 'payments.acct_phone', 'Hello, payment {payment_id} of {store} for {month} was {unexplained} short of its statement after fees. I am claiming the difference. {company}'),
    M('ac_fx', 'Accountant: the exchange loss', 'payments', 'payments.acct_phone', 'Hello, the exchange loss on the {store} payment for {month} was {fx_loss}. {company}'),
    M('ac_fees', 'Accountant: the fees on a payment', 'payments', 'payments.acct_phone', 'Hello, the fee on the {store} payment of {received_on} was {fee} on a statement of {statement_amount}. {company}'),
    M('au_short', 'Author: a store paid less', 'statements', 'statements.owner_phone', 'Reminder: {store} paid {short_by} less than its statement for {month}. Please send the query letter. {company}'),
    M('au_late', 'Author: a store has not paid', 'statements', 'statements.owner_phone', 'Reminder: {store} has not paid {month}, {days_overdue} days past the expected date {expected_on}. {company}'),
    M('au_ready', 'Author: a statement is ready', 'statements', 'statements.owner_phone', 'The statement of {store} for {month} is ready, {statement_amount} earned. {company}'),
    M('au_arrived', 'Author: a payment arrived', 'payments', 'payments.owner_phone', 'The payment of {store} for {month} arrived on {received_on}: {received}. {company}'),
    M('au_pr', 'Author: page-read income', 'prmonth', 'prmonth.owner_phone', 'Page-read income for {month} is {income}, {change_prev} against last month. It is an estimate until paid. {company}'),
    M('au_roy', 'Author: royalties of the month', 'depmonth', 'depmonth.owner_phone', 'Royalties of {month} were {month_total}, {vs_last_year} against the same month last year. {company}'),
    M('au_dep', 'Author: store dependence', 'depmonth', 'depmonth.owner_phone', '{largest_store} carries {largest_share} of your royalties in {month}, {second_store} carries {second_share}. Check: {flag}. {company}'),
    M('au_audio', 'Author: royalty below the plan', 'edroy', 'edroy.owner_phone', '{title} ({format}) earns {royalty_per_copy} a copy against a plan of {plan_per_copy}, a difference of {difference}. {company}'),
    M('au_fee', 'Author: fees on a payment', 'fees', 'fees.owner_phone', 'The {store} payment of {month}: fees and loss are {fee_share} of the statement. Check: {flag}. {company}'),
    M('au_rate', 'Author: a rate step', 'prmonth', 'prmonth.owner_phone', 'A page-read rate step moves the income of {month} by {move_step}. {company}'),
    M('au_nosale', 'Author: no sales this month', 'edroy', 'edroy.owner_phone', '{title} ({format}) has {units_month} copies this month and sold in {months_sold} of the last 12 months. {company}'),
    M('au_closed', 'Author: the month is closed', 'depmonth', 'depmonth.owner_phone', 'Month {month} is closed: royalties {month_total}. {company}'),
    M('au_unpaid', 'Author: a statement is unpaid', 'statements', 'statements.owner_phone', 'The statement of {store} for {month}, {statement_amount}, is still unpaid. Expected on {expected_on}. {company}'),
    M('au_country', 'Author: a country grows', 'ctyfmt', 'ctyfmt.owner_phone', '{country}: royalties of the last 12 months are {country_total}, a growth of {country_growth}. {company}'),
    M('au_direct', 'Author: store share of the month', 'mstore', 'mstore.owner_phone', '{store} carried {share} of the royalties of {month}: {royalty_home} of {month_total}. {company}'),
    M('au_ledger', 'Author: a ledger line to check', 'sales', 'sales.owner_phone', 'Please check line {sale_id}: {title} in {store}, {month}, {units} copies and {returns} returns. {company}'),
    M('au_terms', 'Author: a store terms check', 'statements', 'statements.owner_phone', 'A terms check is due for {store}: its statement for {month} was expected on {expected_on}. Check the store\'s current terms. {company}'),
    M('au_rpc', 'Author: royalty per copy', 'edroy', 'edroy.owner_phone', 'The royalty per copy of {title} ({format}) is {royalty_per_copy} over the last 12 months. {company}'),
    M('au_diff', 'Author: earned against received', 'earned', 'earned.owner_phone', '{store}, {month}: statement {statement_amount}, received {received}, difference {difference}, paid {days_late} days after the expected date. {company}'),
    M('au_fxeff', 'Author: the exchange rate effect', 'curmonth', 'curmonth.owner_phone', 'The {currency} rate of {month} moved royalties by {effect_home} against your base rate. {company}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30), dashboard, insights
FR = '(DAY({today})/DAY(EOMONTH({today},0)))'
W12 = '{range:mstore.month},">="&EDATE(%s,-12),{range:mstore.month},"<"&%s' % (MS, MS)
def RM(m): return 'SUMIFS({range:mstore.royalty_home},{range:mstore.month},%s)' % m
R12 = 'SUMIFS({range:mstore.royalty_home},%s)' % W12
R3 = 'SUMIFS({range:mstore.royalty_home},{range:mstore.month},">="&EDATE(%s,-3),{range:mstore.month},"<"&%s)' % (MS, MS)
PR12 = 'SUMIFS({range:pagereads.income},{range:pagereads.month},">="&EDATE(%s,-12),{range:pagereads.month},"<"&%s)' % (MS, MS)
def FSHARE(f): return 'IFERROR(SUMIFS({range:mformat.royalty_home},{range:mformat.format},%s,{range:mformat.month},">="&EDATE(%s,-12),{range:mformat.month},"<"&%s)/SUMIFS({range:mformat.royalty_home},{range:mformat.month},">="&EDATE(%s,-12),{range:mformat.month},"<"&%s),0)' % (tok('format', f), MS, MS, MS, MS)
CW = '({range:curmonth.month}>=EDATE(%s,-12))*({range:curmonth.month}<%s)' % (MS, MS)
HOME = tok('currency', 'Home currency')
kpis = [
    KPI('Royalties this month to date', RM(MS), 'money'),
    KPI('Royalties last month', RM('EDATE(%s,-1)' % MS), 'money'),
    KPI('Royalties, last 12 months', R12, 'money'),
    KPI('Royalties vs the same month last year', 'IFERROR(%s/%s/%s-1,0)' % (RM(MS), FR, RM('EDATE(%s,-12)' % MS)), 'pct'),
    KPI('Royalties against the 3-month average', 'IFERROR(%s/%s/(%s/3)-1,0)' % (RM(MS), FR, R3), 'pct'),
    KPI('Copies sold this month', 'SUMIFS({range:mstore.units},{range:mstore.month},%s)' % MS, 'int'),
    KPI('Copies sold, last 12 months', 'SUMIFS({range:mstore.units},%s)' % W12, 'int'),
    KPI('Royalty per copy, last 12 months', 'IFERROR(%s/SUMIFS({range:mstore.units},%s),0)' % (R12, W12), 'money'),
    KPI('Page-read income this month', 'SUMIFS({range:pagereads.income},{range:pagereads.month},%s)' % MS, 'money'),
    KPI('Page-read income, last 12 months', PR12, 'money'),
    KPI('Page reads this month', 'SUMIFS({range:pagereads.pages_read},{range:pagereads.month},%s)' % MS, 'int'),
    KPI('Page-read share of royalties', 'IFERROR(%s/(%s+%s),0)' % (PR12, PR12, R12), 'pct'),
    KPI('Direct store share of royalties', 'IFERROR(SUMIFS({range:mstore.royalty_home},{range:mstore.store},%s,%s)/%s,0)' % (tok('store', 'Direct store'), W12, R12), 'pct'),
    KPI('Largest store share, last month', 'IFERROR(INDEX({range:depmonth.largest_share},MATCH(EDATE(%s,-1),{range:depmonth.month},0)),0)' % MS, 'pct', alert={"when": "> {set:dependence_limit}", "style": "bad"}),
    KPI('Second largest store share, last month', 'IFERROR(INDEX({range:depmonth.second_share},MATCH(EDATE(%s,-1),{range:depmonth.month},0)),0)' % MS, 'pct'),
    KPI('Ebook share of royalties', FSHARE('Ebook'), 'pct'),
    KPI('Paperback share of royalties', FSHARE('Paperback'), 'pct'),
    KPI('Audio share of royalties', FSHARE('Audiobook'), 'pct'),
    KPI('Share of royalties outside home currency', 'IFERROR(SUMPRODUCT((({range:curmonth.currency}<>%s)*({range:curmonth.currency}<>""))*%s*{range:curmonth.amount_store}*{range:curmonth.rate_used})/SUMPRODUCT(%s*{range:curmonth.amount_store}*{range:curmonth.rate_used}),0)' % (HOME, CW, CW), 'pct'),
    KPI('Statements unpaid and not yet due', 'COUNTIFS({range:statements.status},%s,{range:statements.expected_on},">="&{today})+COUNTIFS({range:statements.status},%s,{range:statements.expected_on},">="&{today})' % (EXP, OPN), 'int'),
    KPI('Statements overdue', 'COUNTIFS({range:statements.status},%s,{range:statements.expected_on},"<"&{today})+COUNTIFS({range:statements.status},%s,{range:statements.expected_on},"<"&{today})' % (EXP, OPN), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Oldest unpaid month, days since it began', 'IF(COUNT({range:oldest.oldest_month})=0,0,{today}-MIN({range:oldest.oldest_month}))', 'int'),
    KPI('Amount short-paid in total', 'SUMIFS({range:payments.unexplained},{range:payments.unexplained},">"&{set:short_tolerance})', 'money', alert={"when": "> 0", "style": "bad"}),
    KPI('Expected cash, next 30 days', 'SUMIFS({range:statements.statement_amount},{range:statements.status},%s,{range:statements.expected_on},">="&{today},{range:statements.expected_on},"<="&({today}+30))+SUMIFS({range:statements.statement_amount},{range:statements.status},%s,{range:statements.expected_on},">="&{today},{range:statements.expected_on},"<="&({today}+30))' % (EXP, OPN), 'money'),
    KPI('Fees paid, last 12 months', 'SUMIFS({range:payments.fee},{range:payments.received_on},">="&({today}-365))', 'money'),
    KPI('Exchange loss, last 12 months', 'SUMIFS({range:payments.fx_loss},{range:payments.received_on},">="&({today}-365))', 'money'),
    KPI('Payments with fees above the limit', 'COUNTIFS({range:fees.flag},%s)' % ABOVE, 'int'),
    KPI('Stores that reported this month', 'COUNTIFS({range:mstore.month},%s,{range:mstore.royalty_home},">0")' % MS, 'int'),
    KPI('Countries with sales this month', 'SUMPRODUCT(--(SUMIFS({range:ctyfmt.units_month},{range:ctyfmt.country},{range:countries.country})>0))', 'int'),
    KPI('Live editions with no sale this month', 'COUNTIFS({range:edroy.status},%s,{range:edroy.units_month},0)' % LIVE, 'int'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Royalty KPI Dashboard", "kpis": kpis,
    "monthly": {"title": "Royalties, page-read income, statements and money received", "date": "mstore.month", "series": [
        {"label": "Royalties", "sum": "mstore.royalty_home", "date": "mstore.month"}, {"label": "Page-read income", "sum": "prmonth.income", "date": "prmonth.month"},
        {"label": "Statements", "sum": "statements.statement_amount", "date": "statements.month"}, {"label": "Received", "sum": "payments.received", "date": "payments.received_on"}]},
    "breakdowns": [{"title": "Royalties by store", "by": "mstore.store", "value": "mstore.royalty_home", "agg": "sum"}, {"title": "Royalties by format", "by": "mformat.format", "value": "mformat.royalty_home", "agg": "sum"},
                   {"title": "Royalties by country, 12 months", "by": "ctyfmt.country", "value": "ctyfmt.royalty_home", "agg": "sum"}, {"title": "Statements by status", "by": "statements.status", "agg": "count"}]}
def SER(store): return [('store', '=', tok('store', store))]
insights = {"filters": [{"label": "Store", "list": "store"}, {"label": "Format", "list": "format"}, {"label": "Country", "list": "country"}],
    "gauges": [
        {"title": "Statements paid on time", "num": AGG('count', 'statements', where=[('status', '=', PDD), ('days_to_pay', '<=', '{set:grace_days}')]), "den": AGG('count', 'statements', where=[('status', '<>', EXP), ('status', '<>', OPN)])},
        {"title": "Payments not short-paid", "num": AGG('count', 'payments', where=[('unexplained', '<=', '{set:short_tolerance}')]), "den": AGG('count', 'payments')},
        {"title": "Fees under the flag limit", "num": AGG('count', 'fees', where=[('flag', '=', WITHIN)]), "den": AGG('count', 'fees')},
        {"title": "Largest store under the limit", "num": AGG('count', 'depmonth', where=[('flag', '=', WITHIN)]), "den": AGG('count', 'depmonth')},
        {"title": "Editions with a sale this month", "num": AGG('count', 'edroy', where=[('units_month', '>', 0)]), "den": AGG('count', 'edroy', where=[('status', '=', LIVE)])},
        {"title": "Stores reported this month", "num": AGG('count', 'mstore', where=[('is_current', '=', 1), ('royalty_home', '>', 0)]), "den": AGG('count', 'stores')}],
    "charts": [
        CHART('Royalties per month', 'column', 'month', [AGG('sum', 'mstore', 'mstore.royalty_home', date='mstore.month', label='Royalties')]),
        CHART('Royalties by store', 'bar', 'mstore.store', [AGG('sum', 'mstore', 'mstore.royalty_home', label='Royalties')]),
        CHART('Royalties by format', 'bar', 'mformat.format', [AGG('sum', 'mformat', 'mformat.royalty_home', label='Royalties')]),
        CHART('Royalties by country, 12 months', 'bar', 'ctyfmt.country', [AGG('sum', 'ctyfmt', 'ctyfmt.royalty_home', label='Royalties')]),
        CHART('Royalties by currency', 'bar', 'curmonth.currency', [AGG('sum', 'curmonth', 'curmonth.home_amount', label='Royalties')]),
        CHART('Income by pen name, 12 months', 'bar', 'titles.pen_name', [AGG('sum', 'titles', 'titles.total_12m', label='Income')]),
        CHART('Income by series, 12 months', 'bar', 'titles.series', [AGG('sum', 'titles', 'titles.total_12m', label='Income')]),
        CHART('Copies per month', 'column', 'month', [AGG('sum', 'mstore', 'mstore.units', date='mstore.month', label='Copies')]),
        CHART('Copies by format', 'bar', 'mformat.format', [AGG('sum', 'mformat', 'mformat.units', label='Copies')]),
        CHART('Copies by store', 'bar', 'mstore.store', [AGG('sum', 'mstore', 'mstore.units', label='Copies')]),
        CHART('Page-read income per month', 'line', 'month', [AGG('sum', 'prmonth', 'prmonth.income', date='prmonth.month', label='Page-read income')]),
        CHART('Page reads per month', 'column', 'month', [AGG('sum', 'prmonth', 'prmonth.pages_read', date='prmonth.month', label='Pages read')]),
        CHART('Statements by status', 'bar', 'statements.status', [AGG('count', 'statements', label='Statements')]),
        CHART('Statement amount per month', 'column', 'month', [AGG('sum', 'statements', 'statements.statement_amount', date='statements.month', label='Statement amount')]),
        CHART('Received per month', 'column', 'month', [AGG('sum', 'payments', 'payments.received', date='payments.received_on', label='Received')]),
        CHART('Payments by store', 'bar', 'payments.store', [AGG('count', 'payments', label='Payments')]),
        CHART('Fees per month', 'column', 'month', [AGG('sum', 'payments', 'payments.fee', date='payments.received_on', label='Fees')]),
        CHART('Exchange loss per month', 'column', 'month', [AGG('sum', 'payments', 'payments.fx_loss', date='payments.received_on', label='Exchange loss')]),
        CHART('Short-paid amount by store', 'bar', 'statements.store', [AGG('sum', 'statements', 'statements.short_by', label='Short by')]),
        CHART('Royalties by store and month', 'line', 'month', [AGG('sum', 'mstore', 'mstore.royalty_home', date='mstore.month', where=SER(s), label=s) for s in ('Ebook store', 'Print-on-demand', 'Wide distribution', 'Direct store')]),
        CHART('Direct store royalties per month', 'line', 'month', [AGG('sum', 'mstore', 'mstore.royalty_home', date='mstore.month', where=SER('Direct store'), label='Direct store')]),
        CHART('Returns per month', 'column', 'month', [AGG('sum', 'sales', 'sales.returns', date='sales.month', label='Returns')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Earned against paid reconciler", "why": "pick a store and a month: statement, amount received, the gap fees do not explain and the days past the expected date, with a verdict", "where": "Earned Against Paid Reconciler"},
    {"name": "Overdue statement ranker", "why": "every store ranked by its oldest unpaid month and the amount owed, with write today, wait or escalate", "where": "Overdue Statement Ranker"},
    {"name": "Short-payment finder", "why": "scans every payment for money that fees cannot explain and totals what to claim, with the largest one named", "where": "Short-Payment Finder"},
    {"name": "Expected cash by pay month", "why": "unpaid statements and the run-rate for the months not yet reported, each store with its own delay, in Base, Best and Worst", "where": "Expected Cash by Pay Month"},
    {"name": "Store dependence stress test", "why": "lose any store and see the income left, the months of cash and a verdict against your own limit", "where": "Store Dependence Stress Test"},
    {"name": "Page-read income estimator", "why": "the income at the rate minus and plus 10 and 20 percent and its share of all income, an estimate until the payment arrives", "where": "Page-Read Income Estimator"},
    {"name": "Own-history compare", "why": "this month projected against the 3-month average and the same month last year, store by store, flagged beyond your own limit", "where": "Own-History Compare"},
    {"name": "Royalty per copy by edition", "why": "actual royalty per copy over 12 months against the plan from price, store share and cost of a copy", "where": "Royalty per copy by edition"},
    {"name": "Fee and exchange check", "why": "every payment tested for the share that fees and exchange loss take, flagged above your own limit", "where": "Fee and exchange check"},
    {"name": "Royalty trend and 3-month forecast", "why": "your last 12 months, the trend and last year's season turn into the next 3 months in Base, Best and Worst", "where": "Royalty Trend and Forecast"},
    {"name": "Missing sale detector", "why": "finds the edition that sold most months and has no sale this month, so you ask the store for the report", "where": "Missing Sale Detector"}]
competitors = [
    {"what": "free royalty tracking templates", "lacks": "add up sales by store but never compare a statement with the payment, never find a short payment and never show the days a store is late"},
    {"what": "subscription store dashboards", "lacks": "charge every month, show one store at a time and cannot answer what happens to your income if you lose the largest store"},
    {"what": "generic budget spreadsheets", "lacks": "know income and costs but not editions, currencies, page reads, fees or exchange loss, so royalties arrive as one unexplained number"},
    {"what": "single-sheet royalty ledgers", "lacks": "list rows without earned against received, the oldest unpaid month, a payout threshold or a forecast from your own history"},
    {"what": "store reports on their own", "lacks": "show only that store, in its own currency and layout, with no total in your home currency and no comparison across stores"}]
guide = [
    'Open Start and type your imprint name and your own limits in the yellow cells: the largest store share you accept, the fee flag, the short-payment tolerance and the pay per 1,000 pages read.',
    'Check Stores, Countries, Formats and Exchange rates. They hold the royalty share, the payment delay and the base rate of each store and currency (a typical range, check each store\'s current terms).',
    'Enter the editions and titles once: the royalty per copy fills in from price, store share and the cost of a copy.',
    'Each month enter the sales lines in the Sales ledger or only the monthly totals in Royalty by month and store and by format. Figures from stores are estimates until the payment arrives.',
    'Enter the page reads in Page reads and the rate of each month in Royalty by currency and month; the income and the effect of the rate fill in by themselves.',
    'Enter each store statement in Statements and each payment in Payments received: the expected date, the days overdue, the short amount and the fee check fill in.',
    f'Use the {len(tools)} tools to reconcile a month, rank the stores to write to, find short payments, plan cash, test a lost store and forecast the next 3 months.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'A first-time author with 1 to 3 books can use most sheets with a few rows; a small press can read the pen-name columns as author columns.',
    'Read the Royalty KPI Dashboard and the charts every week. Replace the demo rows with your own when you are ready; a blank copy is shipped beside the sample copy.']
listing = {"title": "Author Royalty Tracker Excel Template: Sales Ledger, Earned vs Paid, Short Payments, Page Reads, Fees, Cash Forecast, Self-Publishing",
    "headline": "See what each store earned, what it paid, and what is still owed",
    "tags": ["royalty tracker", "author template", "self publishing", "book sales ledger", "kdp spreadsheet", "indie author", "royalty report", "author finance", "page reads", "excel template", "book royalties", "cash forecast", "publisher tool"],
    "description": ("Run the royalty side of an author-publisher business in one Excel workbook. Built for an independent author who sells through several stores, in several currencies and countries, and wants to know what was earned, what was paid and what is still owed.\n\n"
        "The Sales ledger and the monthly totals by store and by format give your royalties in one home currency, with the rate of each month. Royalty per copy by edition sets the actual royalty against the plan from price, store share and the cost of a copy. "
        "Statements and Payments received show the expected date of every store with your own payment delay, the oldest unpaid month, the days overdue and the short amount that fees do not explain. Fee and exchange check flags payments above your own limit. Page reads keep the page-read income line as an estimate that moves every month.\n\n"
        f"{len(tools)} tools answer the questions an author asks every week: did this store pay what it earned, which store to write to first, which payments came in short, what lands in the bank over the next 4 months, what happens if you lose the largest store, how much the page-read rate matters, and what the next 3 months may bring from your own history. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to your assistant, your accountant and yourself.\n\n"
        "A standard .xlsx workbook with no macros, no login and no subscription, with a sample copy full of demo data and a blank copy for your own numbers. It helps you keep track of your income and does not promise sales or results. Check each store's current terms and confirm tax questions with your adviser."),
    "features": ["Earned against paid for every store", "Oldest unpaid month and overdue ranking", "Short-payment finder with the amount to claim", "Fees and exchange loss check per payment",
                 "Royalty per copy by edition and store", "Page-read income as a clear estimate", "Store dependence stress test", f"{len(tools)} decision tools with verdicts",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(forms)} printable sheets and {len(documents)} documents", f"{len(messages)} ready text messages", "No macros, works in Excel and Google Sheets"]}
assert 900 <= len(listing['description']) <= 2500, len(listing['description'])
s = spec(id=f'{SUITE}-p3', slug='author-publisher-royalties', profession='Author and Self-Publisher Business', name='Sales and Royalties Ledger',
         tagline='Know what each store earned, paid and still owes you', price_usd=29, colors={"primary": "#2B3A55", "accent": "#CE7777"},
         settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide, listing=listing, insights=insights,
         suite={"key": SUITE, "part": 3, "of": 8, "focus": "Sales ledger, royalties, statements and payments"}, signature=signature, competitors=competitors, tools=tools,
         messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'au3.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']), 'gauges', len(insights['gauges']), 'sig', len(signature))
