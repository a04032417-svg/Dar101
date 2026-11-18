"""Author and Self-Publisher Business suite - part 8: Cash, Tax, Expenses and Author Shares."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au8_lists import *
from au8_tables import *
from au8_tables import settings, tables, MS, LM, WIN, SUM12, SUMN, CASHNOW, PAID, EXPD, OPEN, NOTPAID, DUE_IN, STMT_RECV, POT_NOW, AVGCOST12, W12
from au8_tools import tools

SUITE = 'fx-20261115-author-publisher'
NOTE = "Sample wording: adapt it to your own business. Confirm anything about tax, contracts or store terms with your adviser."
def F(*pairs): return [FV(a, b) for a, b in pairs]
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('cashfc_sheet', 'Cash Forecast Input Sheet', 'Cash forecast for one month', 'forecast.month', F(
        ('Sales change of the scenario', 'forecast.sales_change'), ('Cost change of the scenario', 'forecast.cost_change'), ('Expected receipts, before the scenario', 'forecast.base_receipts'), ('Known contractor payments', 'forecast.known'),
        ('New jobs you plan', 'forecast.plan'), ('Ad budget', 'forecast.ads'), ('Usual expenses', 'forecast.expenses'), ('Expected receipts', 'forecast.receipts'), ('Contractor payments', 'forecast.contractors'),
        ('Tax set-aside', 'forecast.tax_set_aside'), ('Owner draw', 'forecast.owner_draw'), ('Net flow', 'forecast.net'), ('Opening cash', 'forecast.opening'), ('Closing cash', 'forecast.closing'), ('Low-cash flag', 'forecast.flag')) + [
        FF('Closing cash, Worst (sales minus 20%)', 'INDEX({range:forecast.close_worst},MATCH({pick},{range:forecast.month},0))', 'money')],
        {"from": "jobpay", "match": "jobpay.month", "columns": ["contractor", "title", "stage", "date", "amount", "status"], "max": 10}),
    FORM('weekly_cash_sheet', 'Weekly Cash Check Sheet', 'Weekly cash check', 'cash.month', F(
        ('Opening cash', 'cash.opening'), ('Receipts', 'cash.receipts'), ('Ads', 'cash.ads'), ('Production', 'cash.production'), ('Expenses', 'cash.expenses'), ('Event costs', 'cash.event_costs'), ('Author copies', 'cash.author_copies'),
        ('Tax set-aside', 'cash.tax_set_aside'), ('Owner draw', 'cash.owner_draw'), ('Closing cash', 'cash.closing'), ('Months of cover', 'cash.cover_months'), ('Floor check', 'cash.low_flag')) + [
        FF('Payments due in the next 30 days', DUE_IN(30), 'money'), FF('Receipts expected in the next 30 days', STMT_RECV(30), 'money'), FF('Cash after both, today', '%s+%s-%s' % (CASHNOW, STMT_RECV(30), DUE_IN(30)), 'money'),
        FF('Your floor', '{set:cash_floor}', 'money')]),
    FORM('draw_sheet', 'Owner Draw Sheet', 'Owner draw for one month', 'forecast.month', F(
        ('Owner draw planned', 'forecast.owner_draw'), ('Expected receipts', 'forecast.receipts'), ('Tax set-aside', 'forecast.tax_set_aside'), ('Closing cash with this draw', 'forecast.closing'), ('Low-cash flag', 'forecast.flag'),
        ('Largest steady draw that holds the floor', 'forecast.max_draw'), ('Your floor', 'forecast.floor')) + [
        FF('Cash above (+) or below (-) the floor', 'INDEX({range:forecast.closing},MATCH({pick},{range:forecast.month},0))-{set:cash_floor}', 'money'),
        FF('Draws taken, last 12 months', SUM12('cash', 'owner_draw'), 'money'), FF('Average draw a month, last 12 months', '%s/12' % SUM12('cash', 'owner_draw'), 'money')]),
    FORM('taxsa_sheet', 'Tax Set-aside Sheet', 'Tax set-aside for one month', 'taxmonth.month', F(
        ('Profit of the month', 'taxmonth.profit_month'), ('Set-aside percent', 'taxmonth.set_aside_pct'), ('Set-aside at your percent', 'taxmonth.target_amount'), ('Set aside', 'taxmonth.set_aside'), ('At your percent (1 = yes)', 'taxmonth.on_target'),
        ('Pot balance', 'taxmonth.pot_balance')) + [
        FF('Set aside against your percent', 'INDEX({range:taxmonth.set_aside},MATCH({pick},{range:taxmonth.month},0))-INDEX({range:taxmonth.target_amount},MATCH({pick},{range:taxmonth.month},0))', 'money'),
        FF('Set aside, last 12 months', SUM12('taxmonth', 'set_aside'), 'money')]),
    FORM('taxpay_sheet', 'Tax Payment Sheet', 'Tax payment and the pot', 'taxmonth.month', F(
        ('Tax paid this month', 'taxmonth.tax_paid'), ('Pot balance', 'taxmonth.pot_balance'), ('Next tax payment on', 'taxmonth.next_payment_on'), ('Next tax payment', 'taxmonth.next_payment'), ('Pot short by', 'taxmonth.short_by')) + [
        FF('Days to the payment', '{set:next_tax_on}-{today}', 'int'), FF('Tax paid, last 12 months', SUM12('taxmonth', 'tax_paid'), 'money'),
        FF('Average monthly set-aside, last 3 months', '%s/3' % SUMN('taxmonth', 'set_aside', 3), 'money')]),
    FORM('expense_entry_sheet', 'Expense Entry Sheet', 'One expense with its category and receipt', 'expenses.expense_id', F(
        ('Date', 'expenses.date'), ('Category', 'expenses.category'), ('Vendor', 'expenses.vendor'), ('Amount', 'expenses.amount'), ('Pen name', 'expenses.pen_name'), ('Receipt on file', 'expenses.receipt'), ('Receipt check', 'expenses.receipt_check'),
        ('Cost of this vendor, last 12 months', 'expenses.vendor_12m'), ('Bills from this vendor, 12 months', 'expenses.vendor_bills')) + [
        FF('Your monthly budget for this category', 'IFERROR(INDEX({range:costcat.monthly_budget},MATCH(INDEX({range:expenses.category},MATCH({pick},{range:expenses.expense_id},0)),{range:costcat.category},0)),0)', 'money'),
        FF('Logged in this category this month', 'SUMIFS({range:expenses.amount},{range:expenses.category},INDEX({range:expenses.category},MATCH({pick},{range:expenses.expense_id},0)),{range:expenses.month},INDEX({range:expenses.month},MATCH({pick},{range:expenses.expense_id},0)))', 'money')]),
    FORM('expense_review_sheet', 'Expense Review Sheet', 'Review of one category and month', 'expmonth.row_id', F(
        ('Month', 'expmonth.month'), ('Category', 'expmonth.category'), ('Amount', 'expmonth.amount'), ('Your budget', 'expmonth.budget'), ('Over (+) or under (-)', 'expmonth.difference'), ('Share of budget used', 'expmonth.used'),
        ('Verdict', 'expmonth.verdict'), ('Category, last 12 months', 'expmonth.cat_12m'), ('Category monthly average', 'expmonth.cat_avg')) + [
        FF('Months over budget, last 12 months', 'COUNTIFS({range:expmonth.category},INDEX({range:expmonth.category},MATCH({pick},{range:expmonth.row_id},0)),{range:expmonth.verdict},%s)' % vt('Over budget'), 'int')]),
    FORM('yearend_sheet', 'Year-end Pack Sheet', 'One line of the year-end pack', 'yearend.line_no', F(
        ('Line', 'yearend.line'), ('Amount', 'yearend.amount'), ('Where it comes from', 'yearend.note')) + [
        FF('Revenue, last 12 months', SUM12('pnl', 'revenue'), 'money'), FF('Costs, last 12 months', SUM12('pnl', 'costs'), 'money'), FF('Profit, last 12 months', SUM12('pnl', 'profit'), 'money'),
        FF('Tax set-aside, last 12 months', SUM12('taxmonth', 'set_aside'), 'money'), FF('Owner draws, last 12 months', SUM12('cash', 'owner_draw'), 'money'),
        FF('Lines without a receipt, last 12 months', 'COUNTIFS({range:expenses.receipt},%s,{range:expenses.month},">="&EDATE(%s,-12),{range:expenses.month},"<"&%s)' % (NO, MS, MS), 'int')]),
    FORM('health_sheet', 'Health Check Sheet', 'One area of the owner health check', 'health.area_no', F(
        ('Area', 'health.area'), ('Your value', 'health.value'), ('Your target', 'health.target'), ('Distance from the target', 'health.gap'), ('Verdict', 'health.verdict'), ('Action', 'health.action'),
        ('Score of the whole check', 'health.score'), ('Red areas', 'health.red_count'), ('Area furthest from the target', 'health.top_area')) + [
        FF('Areas in green', 'COUNTIFS({range:health.verdict},%s)' % vh('Green'), 'int'), FF('Areas in amber', 'COUNTIFS({range:health.verdict},%s)' % vh('Amber'), 'int')]),
    FORM('authshare_sheet', 'Author Share Setup Sheet', 'Author share agreed from one date', 'authors.effective_from', F(
        ('Pen name', 'authors.pen_name'), ('Author share', 'authors.author_share')) + [
        FF('Press share', '1-INDEX({range:authors.author_share},MATCH({pick},{range:authors.effective_from},0))', 'pct'),
        FF('Royalties earned, last 12 months', 'SUMIFS({range:authstmt.royalties_earned},{range:authstmt.pen_name},INDEX({range:authors.pen_name},MATCH({pick},{range:authors.effective_from},0)),%s)' % WIN('{range:authstmt.month}', 12), 'money'),
        FF('Author part, last 12 months', 'SUMIFS({range:authstmt.author_part},{range:authstmt.pen_name},INDEX({range:authors.pen_name},MATCH({pick},{range:authors.effective_from},0)),%s)' % WIN('{range:authstmt.month}', 12), 'money'),
        FF('Payable, last 12 months', 'SUMIFS({range:authstmt.payable},{range:authstmt.pen_name},INDEX({range:authors.pen_name},MATCH({pick},{range:authors.effective_from},0)),%s)' % WIN('{range:authstmt.month}', 12), 'money'),
        FF('Costs charged back, last 12 months', 'SUMIFS({range:authstmt.costs_charged_back},{range:authstmt.pen_name},INDEX({range:authors.pen_name},MATCH({pick},{range:authors.effective_from},0)),%s)' % WIN('{range:authstmt.month}', 12), 'money')]),
    FORM('authstmt_sheet', 'Author Statement Sheet', 'Statement of one author for one month', 'authstmt.statement_id', F(
        ('Month', 'authstmt.month'), ('Pen name', 'authstmt.pen_name'), ('Royalties earned', 'authstmt.royalties_earned'), ('Author share', 'authstmt.author_share'), ('Author part', 'authstmt.author_part'),
        ('Advance recouped', 'authstmt.advance_recouped'), ('Advance left', 'authstmt.advance_left'), ('Costs charged back', 'authstmt.costs_charged_back'), ('Payable', 'authstmt.payable'), ('Press share', 'authstmt.press_share'),
        ('Payable to all authors this month', 'authstmt.month_payable')) + [
        FF('Cash forecast to pay it', 'IFERROR(INDEX({range:forecast.closing},1),0)', 'money')]),
    FORM('advance_sheet', 'Advance Tracker Sheet', 'Advance and recoup of one pen name', 'authstmt.statement_id', F(('Pen name', 'authstmt.pen_name'), ('Month', 'authstmt.month'), ('Advance paid', 'authstmt.advance_paid'),
        ('Recouped so far', 'authstmt.recouped_total'), ('Advance left', 'authstmt.advance_left'), ('Months recouping', 'authstmt.months_recouping'), ('Advance recouped this month', 'authstmt.advance_recouped')) + [
        FF('Share of the advance recouped', 'IFERROR(INDEX({range:authstmt.recouped_total},MATCH({pick},{range:authstmt.statement_id},0))/INDEX({range:authstmt.advance_paid},MATCH({pick},{range:authstmt.statement_id},0)),0)', 'pct')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('cashfc_doc', 'Cash Flow Forecast Report', 'Cash flow forecast report for one month', 'forecast.month', [
        'Cash flow forecast of {set:company}, dated {today}. Month: {col:forecast.month}. Scenario sales change: {col:forecast.sales_change}; cost change: {col:forecast.cost_change}.',
        'Expected receipts: {col:forecast.receipts}. Known contractor payments: {col:forecast.known}. Contractor payments with new jobs: {col:forecast.contractors}. Ad budget: {col:forecast.ads}. Expenses: {col:forecast.expenses}.',
        'Tax set-aside: {col:forecast.tax_set_aside}. Owner draw: {col:forecast.owner_draw}. Net flow of the month: {col:forecast.net}.',
        'Opening cash: {col:forecast.opening}. Closing cash: {col:forecast.closing}. Low-cash flag: {col:forecast.flag}. Closing cash in the worst case (sales minus 20 percent): {col:forecast.close_worst}.',
        'The forecast is an estimate from your own history. Your floor is {col:forecast.floor}.'], ['Author-publisher', 'Accountant'], NOTE),
    DOC('cashpos_doc', 'Cash Position Note', 'Cash position note for one month', 'cash.month', [
        'Cash position of {set:company}, dated {today}. Month: {col:cash.month}.',
        'Opening cash: {col:cash.opening}. Receipts: {col:cash.receipts}. Paid out: ads {col:cash.ads}, production {col:cash.production}, expenses {col:cash.expenses}, event costs {col:cash.event_costs}, author copies {col:cash.author_copies}.',
        'Tax set-aside: {col:cash.tax_set_aside}. Owner draw: {col:cash.owner_draw}. Closing cash: {col:cash.closing}.',
        'Months of cover: {col:cash.cover_months}. Floor check: {col:cash.low_flag}. Your floor is {set:cash_floor}.'], ['Author-publisher'], NOTE),
    DOC('draw_doc', 'Owner Draw Note', 'Owner draw note', 'forecast.month', [
        'Owner draw note of {set:company}, dated {today}. Month: {col:forecast.month}.',
        'The draw planned is {col:forecast.owner_draw}. With this draw the closing cash is {col:forecast.closing} against your floor of {col:forecast.floor} ({col:forecast.flag}).',
        'The largest steady draw that holds your floor in every forecast month is {col:forecast.max_draw}.',
        'Write the draw you decide on below. The owner draw is the money you take out for yourself.'], ['Author-publisher'], NOTE),
    DOC('taxsa_doc', 'Tax Set-aside Statement', 'Tax set-aside statement for one month', 'taxmonth.month', [
        'Tax set-aside statement of {set:company}, dated {today}. Month: {col:taxmonth.month}.',
        'Profit of the month: {col:taxmonth.profit_month}. Set-aside percent: {col:taxmonth.set_aside_pct}. Set-aside at your percent: {col:taxmonth.target_amount}. Amount set aside: {col:taxmonth.set_aside}.',
        'Tax paid in the month: {col:taxmonth.tax_paid}. Pot balance at the end of the month: {col:taxmonth.pot_balance}.',
        'Next tax payment: {col:taxmonth.next_payment} on {col:taxmonth.next_payment_on}. The pot is short by {col:taxmonth.short_by} of it today.',
        'The percent and the amounts are your own numbers: confirm them with your tax adviser.'], ['Author-publisher', 'Accountant'], NOTE),
    DOC('yearend_doc', 'Year-end Summary', 'Year-end summary for your adviser', 'pnl.month', [
        'Year-end summary of {set:company}, dated {today}. The 12 months that end in {col:pnl.month}.',
        'Revenue: {col:pnl.revenue_12m}. Costs: {col:pnl.costs_12m}. Profit: {col:pnl.profit_12m}.',
        'Tax set-aside in the 12 months: {col:pnl.setaside_12m}. Owner draws in the 12 months: {col:pnl.draws_12m}.',
        'Receipts missing in {col:pnl.month}: {col:pnl.missing_receipts} of {col:pnl.expense_count} expense lines. Please bring the missing receipts before the meeting.',
        'The figures come from your own sheets and help you keep track: your adviser decides what counts for tax.'], ['Author-publisher', 'Accountant'], NOTE),
    DOC('expcat_doc', 'Expense Report by Category', 'Expense report by category', 'expmonth.row_id', [
        'Expense report of {set:company}, dated {today}. Category: {col:expmonth.category}. Month: {col:expmonth.month}.',
        'Amount logged: {col:expmonth.amount}. Your monthly budget: {col:expmonth.budget}. Difference: {col:expmonth.difference}, which is {col:expmonth.used} of the budget ({col:expmonth.verdict}).',
        'The category cost {col:expmonth.cat_12m} in the last 12 months, an average of {col:expmonth.cat_avg} a month.',
        'Write below what you will change in this category.'], ['Author-publisher'], NOTE),
    DOC('expmonth_doc', 'Expense List for One Month', 'Expense list for one month', 'pnl.month', [
        'Expense list of {set:company}, dated {today}. Month: {col:pnl.month}.',
        'Expense lines logged: {col:pnl.expense_count}. Expenses logged: {col:pnl.expense_sum}. Expenses in Profit and Loss: {col:pnl.expenses}. Lines without a receipt: {col:pnl.missing_receipts}.',
        'The two expense totals should be the same: if they differ, check the Expenses sheet for a missing line or a wrong month.',
        'Costs of the month: {col:pnl.costs}. Profit of the month: {col:pnl.profit}.'], ['Author-publisher', 'Assistant'], NOTE),
    DOC('health_doc', 'Owner Health Check Report', 'Owner health check report for one area', 'health.area_no', [
        'Owner health check of {set:company}, dated {today}. Area: {col:health.area}.',
        'Your value: {col:health.value}. Your target: {col:health.target}. Distance from the target: {col:health.gap}. Verdict: {col:health.verdict}.',
        'Action: {col:health.action}.',
        'The whole check scores {col:health.score} out of 100 with {col:health.red_count} red areas. The area furthest from your target is {col:health.top_area}. All targets are your own numbers.'], ['Author-publisher'], NOTE),
    DOC('actions_doc', 'Actions of the Month Report', 'Three actions of the month', 'pnl.month', [
        'Three actions of {set:company}, dated {today}, for {col:pnl.month}.',
        'Your three actions: {col:pnl.actions_text}.',
        'They are the areas furthest from your own targets on the Health Check Areas sheet. Write who does each action and by when.',
        'Revenue of the month: {col:pnl.revenue}. Profit of the month: {col:pnl.profit}. Profit margin: {col:pnl.margin}.'], ['Author-publisher', 'Assistant'], NOTE),
    DOC('authstmt_doc', 'Author Statement', 'Author statement for one author', 'authstmt.statement_id', [
        'Author statement of {set:company}, dated {today}. Pen name: {col:authstmt.pen_name}. Month: {col:authstmt.month}. Statement {col:authstmt.statement_id}.',
        'Royalties earned: {col:authstmt.royalties_earned}. Author share: {col:authstmt.author_share}. Author part: {col:authstmt.author_part}.',
        'Advance recouped this month: {col:authstmt.advance_recouped}. Advance left: {col:authstmt.advance_left}. Costs charged back: {col:authstmt.costs_charged_back}.',
        'Payable to the author: {col:authstmt.payable}. Press share: {col:authstmt.press_share}.',
        'Figures are estimates until the stores pay.'], ['Author-publisher', 'Author'], NOTE),
    DOC('authmonth_doc', 'Author Statements for a Month', 'Author statements for one month', 'authstmt.statement_id', [
        'Author statements of {set:company}, dated {today}, for {col:authstmt.month}.',
        'Royalties of all authors this month: {col:authstmt.month_earned}. Payable to all authors this month: {col:authstmt.month_payable}.',
        'This statement ({col:authstmt.statement_id}, {col:authstmt.pen_name}) shows {col:authstmt.payable} payable and a press share of {col:authstmt.press_share}.',
        'Check that the payables, the advances recouped, the costs charged back and the press share add up to the royalties earned: the Shares Check sheet does it.'], ['Author-publisher'], NOTE),
    DOC('advance_doc', 'Advance and Recoup Report', 'Advance and recoup report', 'authstmt.statement_id', [
        'Advance and recoup report of {set:company}, dated {today}. Pen name: {col:authstmt.pen_name}. Up to {col:authstmt.month}.',
        'Advance paid: {col:authstmt.advance_paid}. Recouped so far: {col:authstmt.recouped_total} over {col:authstmt.months_recouping} months. Advance left: {col:authstmt.advance_left}.',
        'The advance is earned back from the author part of the royalties before anything more is paid; the amount recouped this month is {col:authstmt.advance_recouped}.',
        'Write below the pace you agree with the author.'], ['Author-publisher', 'Author'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('weekly_cash', 'Weekly Cash Check', 'cash', 'cash.month', [('Write the money received this week in the Cash by Month sheet', 0), ('Write the payments made this week', 1), ('Check the open statements for late payers', 2), ('Read Cash for the Next 30 Days', 3), ('Compare the balance with your floor', 4), ('Decide: pay now, pay in parts or hold the draw', 5)]),
    CHK('month_close', 'Month-end Close', 'pnl', 'pnl.month', [('Enter the expenses of the month with their category', 30), ('Add the missing receipts', 33), ('Enter the payments received', 34), ('Write the income and cost lines in Profit and Loss', 35), ('Write the cash lines in Cash by Month', 36), ('Check the tax set-aside of the month', 37), ('Read the health check', 38)]),
    CHK('draw_decision', 'Owner Draw Decision', 'forecast', 'forecast.month', [('Read the forecast closing cash of the month', -10), ('Read the largest steady draw that holds your floor', -9), ('Check the contractor payments due', -7), ('Check the tax pot against the next payment', -6), ('Choose the draw', -5), ('Write the draw in Start', -4)]),
    CHK('taxsa_month', 'Tax Set-aside Month', 'taxmonth', 'taxmonth.month', [('Write the profit of the month', 35), ('Work out the set-aside at your percent', 36), ('Move the amount to the pot', 37), ('Write the amount in Tax Set-aside by Month', 37), ('Check the pot against the next payment', 38), ('Ask your tax adviser if the percent still fits', 40)]),
    CHK('tax_payment', 'Tax Payment', 'taxmonth', 'taxmonth.month', [('Ask your tax adviser for the amount and the date', 0), ('Check the pot balance', 3), ('Fill the pot if it is short', 7), ('Pay the tax from the pot', 14), ('Write the payment in Tax Set-aside by Month', 15), ('Keep the confirmation with the records', 16)]),
    CHK('expense_month', 'Expense Month Check', 'expmonth', 'expmonth.month', [('Check every expense line has a category', 30), ('Add the missing receipts', 32), ('Compare each category with your budget', 33), ('Look at the categories over budget', 34), ('Ask for a lower price where a cost keeps rising', 36), ('Cancel what you no longer use', 38)]),
    CHK('year_pack', 'Year-end Pack', 'pnl', 'pnl.month', [('Close the last month of the year', 30), ('Print the Year-end Summary Lines', 33), ('Add the missing receipts', 35), ('Check the tax set-aside and the tax paid', 37), ('Send the pack to your adviser', 40), ('Write the questions of your adviser', 45), ('Plan the draws for the new year', 50)]),
    CHK('quarter_health', 'Quarterly Health Check', 'cash', 'cash.month', [('Update the five figures in Health Check Areas', 30), ('Read the verdict of every area', 31), ('Write the three actions of the month', 32), ('Give each action an owner and a date', 33), ('Check the actions at the next review', 90)]),
    CHK('low_cash', 'Low-cash Plan', 'forecast', 'forecast.month', [('Read the first low-cash month in the forecast', -60), ('Hold the owner draw', -55), ('Ask the ad specialist to pause new campaigns', -50), ('Ask contractors to take the payment in parts', -45), ('Chase the late store statements', -40), ('Check the forecast again', -30)]),
    CHK('author_setup', 'New Author Setup', 'authstmt', 'authstmt.month', [('Add the pen name in Authors and Shares', 0), ('Agree the author share and the advance', 1), ('Write the advance paid', 2), ('Set the recoup pace with the author', 3), ('Write the first author statement', 30), ('Check the shares with the Shares Check', 31)]),
    CHK('author_month', 'Author Statement Month', 'authstmt', 'authstmt.month', [('Write the royalties earned of each pen name', 33), ('Write the advance recouped', 34), ('Write the costs charged back', 35), ('Check that the statements add up', 36), ('Send each statement to its author', 37), ('Pay the amount payable', 40)]),
    CHK('advance_review', 'Advance Recoup Review', 'authstmt', 'authstmt.month', [('Read the advance left', 33), ('Read the months left at your pace', 34), ('Tell the author where the advance stands', 35), ('Agree a new pace if it is slow', 38), ('Write the decision', 40)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('a_percent', 'Accountant: confirm the percent', 'taxmonth', 'taxmonth.acct_phone', 'Hello {acct_name}, please confirm the set-aside percent of {set_aside_pct} for this year. {company}'),
    M('a_profit', 'Accountant: profit and set-aside', 'taxmonth', 'taxmonth.acct_phone', 'Hello {acct_name}, the profit of {month} is {profit_month} and the set-aside is {set_aside}. {company}'),
    M('a_next', 'Accountant: next tax payment', 'taxmonth', 'taxmonth.acct_phone', 'Hello {acct_name}, please send the amount of the next tax payment due on {next_payment_on}. {company}'),
    M('a_yearend', 'Accountant: year-end summary ready', 'taxmonth', 'taxmonth.acct_phone', 'Hello {acct_name}, the year-end summary is ready, please review it. The tax pot at {month} is {pot_balance}. {company}'),
    M('a_category', 'Accountant: confirm an expense category', 'expenses', 'expenses.acct_phone', 'Hello {acct_name}, please confirm the expense category for {vendor} at {amount}. I have it under {category}. {company}'),
    M('a_pot', 'Accountant: tax pot and next payment', 'taxmonth', 'taxmonth.acct_phone', 'Hello {acct_name}, the tax pot is {pot_balance} and the next payment is {next_payment}. {company}'),
    M('a_fee', 'Accountant: check a fee and loss', 'payments', 'payments.acct_phone', 'Hello {acct_name}, please check the fee and exchange loss on the payment of {store} for {month}: fee {fee}, exchange loss {fx_loss}. {company}'),
    M('v_expenses', 'Assistant: enter the expenses of a month', 'cash', 'cash.va_phone', 'Hello {va_name}, please enter the expenses of {month} with their category. {company}'),
    M('v_payments', 'Assistant: enter the payments received', 'cash', 'cash.va_phone', 'Hello {va_name}, please enter the payments received in {month}. {company}'),
    M('v_open', 'Assistant: list the open payments', 'cash', 'cash.va_phone', 'Hello {va_name}, please list the open payments for the next 30 days. Cash at the end of {month} was {closing}. {company}'),
    M('v_receipt', 'Assistant: collect a missing receipt', 'expenses', 'expenses.va_phone', 'Hello {va_name}, please collect the missing receipt for {vendor}: {amount} on {date}. {company}'),
    M('n_final', 'Narrator: final payment date', 'jobpay', 'jobpay.phone', 'Hello {contractor}, your final payment of {amount} for {title} will be paid on {date}. {company}'),
    M('n_move', 'Narrator: confirm a new payment date', 'jobpay', 'jobpay.phone', 'Hello {contractor}, may I move your payment of {amount} for {title} by {move_days} days, from {date} to {new_date}? Please confirm. {company}'),
    M('e_invoice', 'Editor: invoice payment date', 'jobpay', 'jobpay.phone', 'Hello {contractor}, your invoice of {amount} for the edit of {title} will be paid on {date}. {company}'),
    M('d_invoice', 'Cover designer: invoice payment date', 'jobpay', 'jobpay.phone', 'Hello {contractor}, your invoice of {amount} for the cover of {title} will be paid on {date}. {company}'),
    M('f_invoice', 'Formatter: invoice payment date', 'jobpay', 'jobpay.phone', 'Hello {contractor}, your invoice of {amount} for the layout of {title} will be paid on {date}. {company}'),
    M('t_final', 'Translator: final payment date', 'jobpay', 'jobpay.phone', 'Hello {contractor}, your final payment of {amount} for the translation of {title} will be paid on {date}. {company}'),
    M('ad_budget', 'Ad specialist: the ad budget of a month', 'forecast', 'forecast.ad_phone', 'Hello {ad_name}, the ad budget for {month} is {ads}, please keep within it. {company}'),
    M('ad_pause', 'Ad specialist: pause new campaigns', 'forecast', 'forecast.ad_phone', 'Hello {ad_name}, please pause new campaigns until cash is above {floor}. The forecast for {month} is {closing}. {company}'),
    M('c_hold', 'Coordinator: hold new launch spend', 'forecast', 'forecast.coord_phone', 'Hello {coord_name}, please hold new launch spend until cash is above {floor}. The forecast for {month} is {closing}. {company}'),
    M('p_copies', 'Printer: invoice the author copies', 'cash', 'cash.printer_phone', 'Hello {printer_name}, please invoice the author copies for {month}. {company}'),
    M('w_invoice', 'Web developer: send the invoice', 'expenses', 'expenses.webdev_phone', 'Hello {webdev_name}, please send the invoice for {date} of {amount}. {company}'),
    M('ev_invoice', 'Event organiser: send the invoice', 'cash', 'cash.events_phone', 'Hello {events_name}, please send the invoice for the events of {month}: I have {event_costs} in costs so far. {company}'),
    M('r_payment', 'Rights agent: next rights payment', 'pnl', 'pnl.rights_phone', 'Hello {rights_name}, please confirm the next rights payment after the {rights} received in {month}. {company}'),
    M('o_floor', 'Author: a payment crosses the floor', 'due', 'due.author_phone', 'Hello {author_name}, cash after paying {amount} on {due_date} would be {balance_after}, below your floor of {floor}. {company}'),
    M('o_cover', 'Author: cash balance and cover', 'cash', 'cash.author_phone', 'Hello {author_name}, the cash balance at the end of {month} is {closing}, which is {cover_months} months of cover. {company}'),
    M('o_draw', 'Author: the owner draw of a month', 'forecast', 'forecast.author_phone', 'Hello {author_name}, the owner draw for {month} is {owner_draw}, cash after the draw is {closing}. {company}'),
    M('o_pot', 'Author: the tax pot is short', 'taxmonth', 'taxmonth.author_phone', 'Hello {author_name}, the tax pot is short by {short_by} for the next payment of {next_payment}. {company}'),
    M('o_over', 'Author: a category is over budget', 'expmonth', 'expmonth.author_phone', 'Hello {author_name}, {category} is {over_pct} above your own budget in {month}. {company}'),
    M('o_red', 'Author: red areas of the health check', 'health', 'health.author_phone', 'Hello {author_name}, the health check shows {red_count} red areas and a score of {score}. The area furthest from your target is {top_area}. {company}'),
    M('o_actions', 'Author: your three actions', 'health', 'health.author_phone', 'Hello {author_name}, your three actions of the month are: {actions_text}. {company}'),
    M('o_shares', 'Author: the shares of a pen name', 'authstmt', 'authstmt.author_phone', 'Hello {author_name}, the author share of {pen_name} is {author_share} and the press keeps {press_pct}, together {share_total}. {company}'),
    M('o_payable', 'Author: the payable of a statement', 'authstmt', 'authstmt.author_phone', 'Hello {author_name}, the statement of {pen_name} for {month} shows {payable} payable. {company}'),
    M('o_advance', 'Author: the advance left', 'authstmt', 'authstmt.author_phone', 'Hello {author_name}, the advance left on {pen_name} is {advance_left} after {month}. {company}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30), dashboard, insights
kpis = [
    KPI('Cash today', CASHNOW, 'money'),
    KPI('Cash after payments due in 30 days', '%s-%s' % (CASHNOW, DUE_IN(30)), 'money', alert={"when": "< {set:cash_floor}", "style": "warn"}),
    KPI('Lowest forecast cash, next 12 months', 'MIN({range:forecast.closing})', 'money', alert={"when": "< {set:cash_floor}", "style": "bad"}),
    KPI('Months of cash cover', 'IFERROR(%s/%s,0)' % (CASHNOW, AVGCOST12), 'num'),
    KPI('Cash against the floor (gap)', '%s-{set:cash_floor}' % CASHNOW, 'money'),
    KPI('Receipts, last 12 months', SUM12('cash', 'receipts'), 'money'),
    KPI('Receipts expected, next 90 days', 'SUMIFS({range:receipts.expected},{range:receipts.month},"<"&EDATE(%s,4))' % MS, 'money'),
    KPI('Open statements amount', 'SUMIFS({range:statements.statement_amount},{range:statements.status},%s)+SUMIFS({range:statements.statement_amount},{range:statements.status},%s)' % (EXPD, OPEN), 'money'),
    KPI('Contractor payments due in 30 days', DUE_IN(30), 'money'),
    KPI('Contractor payments due in 90 days', DUE_IN(90), 'money'),
    KPI('Owner draws, last 12 months', SUM12('cash', 'owner_draw'), 'money'),
    KPI('Revenue, last 12 months', SUM12('pnl', 'revenue'), 'money'),
    KPI('Costs, last 12 months', SUM12('pnl', 'costs'), 'money'),
    KPI('Profit, last 12 months', SUM12('pnl', 'profit'), 'money'),
    KPI('Profit margin, last 12 months', 'IFERROR(%s/%s,0)' % (SUM12('pnl', 'profit'), SUM12('pnl', 'revenue')), 'pct', alert={"when": "< {set:margin_target}", "style": "warn"}),
    KPI('Profit margin, last 3 months', 'IFERROR(%s/%s,0)' % (SUMN('pnl', 'profit', 3), SUMN('pnl', 'revenue', 3)), 'pct'),
    KPI('Expenses, last 12 months', SUM12('expenses', 'amount', 'month'), 'money'),
    KPI('Largest expense category, last 12 months', 'INDEX({range:expmonth.category},MATCH(MAX({range:expmonth.cat_12m}),{range:expmonth.cat_12m},0))', 'text'),
    KPI('Categories over your budget, last month', 'COUNTIFS({range:expmonth.month},%s,{range:expmonth.verdict},%s)' % (LM, vt('Over budget')), 'int', alert={"when": "> {set:over_limit}", "style": "warn"}),
    KPI('Ad spend share of revenue, 12 months', 'IFERROR(%s/%s,0)' % (SUM12('pnl', 'ads'), SUM12('pnl', 'revenue')), 'pct'),
    KPI('Tax set-aside, last 12 months', SUM12('taxmonth', 'set_aside'), 'money'),
    KPI('Tax pot balance', POT_NOW, 'money'),
    KPI('Tax paid, last 12 months', SUM12('taxmonth', 'tax_paid'), 'money'),
    KPI('Pot shortfall against next payment', 'MAX(0,{set:next_tax_amount}-%s)' % POT_NOW, 'money', alert={"when": "> 0", "style": "warn"}),
    KPI('Health check red areas', 'COUNTIFS({range:health.verdict},%s)' % vh('Red'), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Health check score (0 to 100)', 'AVERAGE({range:health.points})', 'int'),
    KPI('Royalties of authors, last 12 months', SUM12('authstmt', 'royalties_earned'), 'money'),
    KPI('Payable to authors, last month', 'SUMIFS({range:authstmt.payable},{range:authstmt.month},%s)' % LM, 'money'),
    KPI('Advance left across authors', 'SUMIFS({range:authstmt.advance_left},{range:authstmt.latest},1)', 'money'),
    KPI('Costs charged back, last 12 months', SUM12('authstmt', 'costs_charged_back'), 'money'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Cash and Tax Dashboard", "kpis": kpis,
    "monthly": {"title": "Revenue, costs and profit by month", "date": "pnl.month", "series": [
        {"label": "Revenue", "sum": "pnl.revenue", "date": "pnl.month"}, {"label": "Costs", "sum": "pnl.costs", "date": "pnl.month"}, {"label": "Profit", "sum": "pnl.profit", "date": "pnl.month"}]},
    "breakdowns": [{"title": "Expenses by category", "by": "expenses.category", "value": "expenses.amount", "agg": "sum"}, {"title": "Statements by status", "by": "statements.status", "agg": "count"},
                   {"title": "Money received by store", "by": "payments.store", "value": "payments.received", "agg": "sum"}, {"title": "Contractor payments by stage", "by": "jobpay.stage", "value": "jobpay.amount", "agg": "sum"}]}
def PEN(n): return tok('penname', n)
insights = {"filters": [{"label": "Expense category", "list": "expcat"}, {"label": "Store", "list": "store"}, {"label": "Pen name", "list": "penname"}],
    "gauges": [
        {"title": "Months with cash at or above the floor", "num": AGG('count', 'cash', where=[('closing', '>=', '{set:cash_floor}')]), "den": AGG('count', 'cash')},
        {"title": "Months with cash cover at your target", "num": AGG('count', 'cash', where=[('cover_months', '>=', '{set:cash_cover_months}')]), "den": AGG('count', 'cash')},
        {"title": "Expense lines within budget", "num": AGG('count', 'expmonth', where=[('verdict', '<>', vt('Over budget'))]), "den": AGG('count', 'expmonth')},
        {"title": "Months set aside at your percent", "num": AGG('count', 'taxmonth', where=[('on_target', '=', 1)]), "den": AGG('count', 'taxmonth')},
        {"title": "Health check areas in green", "num": AGG('count', 'health', where=[('verdict', '=', vh('Green'))]), "den": AGG('count', 'health')},
        {"title": "Statements paid in full", "num": AGG('count', 'statements', where=[('status', '=', SPAID)]), "den": AGG('count', 'statements')}],
    "charts": [
        CHART('Cash balance per month', 'column', 'month', [AGG('sum', 'cash', 'cash.closing', date='cash.month', label='Closing cash')]),
        CHART('Receipts per month', 'column', 'month', [AGG('sum', 'cash', 'cash.receipts', date='cash.month', label='Receipts')]),
        CHART('Costs per month', 'column', 'month', [AGG('sum', 'pnl', 'pnl.costs', date='pnl.month', label='Costs')]),
        CHART('Profit per month', 'column', 'month', [AGG('sum', 'pnl', 'pnl.profit', date='pnl.month', label='Profit')]),
        CHART('Owner draw per month', 'column', 'month', [AGG('sum', 'cash', 'cash.owner_draw', date='cash.month', label='Owner draw')]),
        CHART('Cash forecast, closing cash by month', 'line', 'forecast.fmon', [AGG('sum', 'forecast', 'forecast.closing', label='Closing cash')]),
        CHART('Forecast receipts by pay month', 'column', 'receipts.fmon', [AGG('sum', 'receipts', 'receipts.expected', label='Expected receipts'), AGG('sum', 'receipts', 'receipts.needed', label='Paid out in a usual month')]),
        CHART('Known contractor payments by forecast month', 'column', 'forecast.fmon', [AGG('sum', 'forecast', 'forecast.known', label='Known payments')]),
        CHART('Expenses by category', 'bar', 'expenses.category', [AGG('sum', 'expenses', 'expenses.amount', label='Expenses')]),
        CHART('Expenses per month', 'column', 'month', [AGG('sum', 'expenses', 'expenses.amount', date='expenses.date', label='Expenses')]),
        CHART('Expenses by pen name', 'bar', 'expenses.pen_name', [AGG('sum', 'expenses', 'expenses.amount', label='Expenses')]),
        CHART('Budget against actual by category', 'bar', 'expmonth.category', [AGG('sum', 'expmonth', 'expmonth.amount', label='Actual'), AGG('sum', 'expmonth', 'expmonth.budget', label='Budget')]),
        CHART('Tax set-aside per month', 'column', 'month', [AGG('sum', 'taxmonth', 'taxmonth.set_aside', date='taxmonth.month', label='Set aside')]),
        CHART('Tax pot balance per month', 'column', 'month', [AGG('sum', 'taxmonth', 'taxmonth.pot_balance', date='taxmonth.month', label='Pot balance')]),
        CHART('Tax paid per month', 'column', 'month', [AGG('sum', 'taxmonth', 'taxmonth.tax_paid', date='taxmonth.month', label='Tax paid')]),
        CHART('Statements by status', 'bar', 'statements.status', [AGG('count', 'statements', label='Statements')]),
        CHART('Money received by store', 'bar', 'payments.store', [AGG('sum', 'payments', 'payments.received', label='Received')]),
        CHART('Fees and exchange loss per month', 'column', 'month', [AGG('sum', 'payments', 'payments.fee', date='payments.received_on', label='Fees'), AGG('sum', 'payments', 'payments.fx_loss', date='payments.received_on', label='Exchange loss')]),
        CHART('Royalties earned by pen name', 'bar', 'authstmt.pen_name', [AGG('sum', 'authstmt', 'authstmt.royalties_earned', label='Royalties earned')]),
        CHART('Payable by pen name per month', 'column', 'month', [AGG('sum', 'authstmt', 'authstmt.payable', date='authstmt.month', where=[('pen_name', '=', PEN('Tamsin Hartwell'))], label='Tamsin Hartwell'),
                                                               AGG('sum', 'authstmt', 'authstmt.payable', date='authstmt.month', where=[('pen_name', '=', PEN('Corvin Ashdale'))], label='Corvin Ashdale')]),
        CHART('Advance left by pen name', 'bar', 'authstmt.pen_name', [AGG('sum', 'authstmt', 'authstmt.advance_left', where=[('latest', '=', 1)], label='Advance left')]),
        CHART('Costs charged back per month', 'column', 'month', [AGG('sum', 'authstmt', 'authstmt.costs_charged_back', date='authstmt.month', label='Costs charged back')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "12-month cash forecast with Base, Best and Worst", "why": "expected royalties by pay month, known contractor payments, ads, expenses, set-aside and draw give the closing cash of every month and the first low-cash month", "where": "Cash Forecast"},
    {"name": "Cash check for the next 30 days", "why": "the payments due and the receipts expected turned into pay now, pay in parts or hold the draw against your own floor", "where": "Cash for the Next 30 Days"},
    {"name": "Receipts by pay month from the store delays", "why": "each store's delay moves its earnings to the month the money really arrives, so a thin month shows before it happens", "where": "Receipts by Pay Month"},
    {"name": "Owner draw planner", "why": "the largest steady draw that keeps cash at or above your floor in every month, with five draws tested", "where": "Owner Draw Planner"},
    {"name": "Contractor payment queue", "why": "open payments in due order with the cash left after each one and the first payment that crosses your floor", "where": "Known Payments Due"},
    {"name": "Tax set-aside pot and payment planner", "why": "the pot against the next payment, the percent of profit that fills it in time and the shortfall, to confirm with your tax adviser", "where": "Tax Payment Planner"},
    {"name": "Expense log against your own budget", "why": "every category and month against your budget, ranked from the most over, with the receipts still missing", "where": "Expense Log Check"},
    {"name": "Year-end pack for your adviser", "why": "20 lines of income, costs, profit, set-aside, tax paid, draws and cash for the last 12 complete months", "where": "Year-end Summary Lines"},
    {"name": "Owner health check with three actions", "why": "twelve areas scored green, amber or red against your own targets and the three worst turned into actions", "where": "Owner Health Check"},
    {"name": "Author statements and advance tracker", "why": "payable per author, advance left and a check that the shares and the money add up, for a small press or a first author", "where": "Author Statements"}]
competitors = [
    {"what": "free royalty tracking templates", "lacks": "list what each store paid but never forecast cash, delay receipts by store or check what is still owed"},
    {"what": "generic budget spreadsheets", "lacks": "know no pay delays, no advance copies, no tax pot and no per-pen-name statements"},
    {"what": "subscription store dashboards", "lacks": "show sales by day but not your costs, your cash floor, your tax pot or an owner draw that fits"},
    {"what": "accounting apps for small businesses", "lacks": "record the books but give no author-publisher health check, no read-through or break-even verdict and no author shares"},
    {"what": "single-sheet profit and loss templates", "lacks": "stop at last month and give no forecast, no scenarios and no three actions for next month"}]
guide = [
    'Open Start and type your imprint name, your cash floor, the months of cover you want, the owner draw you plan, the set-aside percent (confirm it with your tax adviser) and the date and amount of your next tax payment.',
    'Check Team and Stores. Team holds the phones for the message links; Stores holds the payment delay of each store, which the receipts forecast uses.',
    'Write each store statement in Statements and each payment that reached your bank in Payments Received. The gap, the days overdue and the fee check fill in by themselves.',
    'Write each payment to a freelancer or provider in Job Payments. Known Payments Due lists the open ones in the order to pay them, with the cash left after each.',
    'Write every expense in Expenses with its category, its vendor and whether the receipt is on file. Expenses by Category and Month compares each month with your own budget in Cost Categories.',
    'Write the totals of each month in Profit and Loss by Month and Cash by Month, and the tax you set aside and paid in Tax Set-aside by Month. Revenue, costs, profit, closing cash and the pot balance fill in.',
    'Read Cash Forecast for the next 12 months. Choose Base, Best or Worst on Start; Worst is sales minus 20 percent. The tools show the first low-cash month and the largest owner draw that holds your floor.',
    'Type the five figures that come from your other parts in Health Check Areas (ad return, store dependence, two read-through figures and titles under break-even). The verdicts and the three actions fill in.',
    'For a small press keep one row per pen name in Authors and Shares and one statement per pen name and month in Author Statements; a first author sets the share to 100 percent.',
    f'Use the {len(tools)} calculators for the weekly cash decisions, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in. Figures are estimates until the stores pay.']
listing = {"title": "Author and Self-Publisher Cash Flow Forecast, Tax Set-aside and Expense Tracker Excel Template: Owner Draw, Health Check, Author Statements",
    "headline": "Know if you can pay what you owe, set tax aside and see what is left for you",
    "tags": ["author template", "cash flow forecast", "tax set aside", "expense tracker", "owner draw", "self publishing", "indie author", "excel template", "author business", "profit and loss", "author statements", "health check", "royalty payments"],
    "description": ("Run the money side of an author or small publishing business in one Excel workbook. Built for an independent author who publishes under one or two pen names, often with a part-time assistant and freelancers paid per job. "
        "Cash Forecast looks 12 months ahead from your own history: expected royalties by pay month (each store's delay is a number you edit), known contractor payments, ad budget, expenses, tax set-aside and owner draw, with Base, Best and Worst scenarios (Worst is sales minus 20 percent) and a low-cash flag against your own floor.\n\n"
        "Known Payments Due lists open payments to freelancers in the order to pay them, with the cash left after each. Cash for the Next 30 Days says pay now, pay in parts or hold the draw. Owner Draw Planner finds the largest steady draw that keeps your floor. "
        "Tax Set-aside by Month keeps the pot, the payments and the shortfall against your next payment (the percent is yours: confirm it with your tax adviser). Expenses by Category and Month compare each month with your own budget, and Year-end Summary Lines gather the pack for your adviser.\n\n"
        "Health Check Areas scores twelve areas green, amber or red against your own targets and turns the worst three into actions. A small press gets Author Statements per pen name with shares, advance recouped, costs charged back and the amount payable, plus a shares check and an advance tracker.\n\n"
        f"{len(tools)} calculators, {len(forms)} printable sheets, {len(documents)} documents, {len(checklists)} checklists and {len(messages)} ready text messages to the accountant, the assistant, freelancers and the author are included. "
        "This is part eight of the Author and Self-Publisher Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Figures are estimates until the stores pay, every target is your own number, and it helps you keep track without promising any income."),
    "features": ["12-month cash forecast with Base, Best and Worst", "Receipts by pay month from each store delay", "Cash check for the next 30 days", "Owner draw planner that keeps your floor", "Contractor payment queue with cash left after each",
                 "Tax set-aside pot with payment planner", "Expense log against your own budget", "Year-end pack for your adviser", "Owner health check with three actions", "Author statements with shares and advances",
                 f"{len(tools)} calculators for cash and tax decisions", f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p8', slug='author-publisher-cash', profession='Author and Self-Publisher Business', name='Cash, Tax, Expenses and Author Shares',
         tagline='Cash forecast, tax set-aside, expenses and author statements', price_usd=29,
         colors={"primary": "#2B3A55", "accent": "#CE7777"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 8, "of": 8, "focus": "Cash, tax, expenses and author shares"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'au8.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
