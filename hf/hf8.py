"""Household Finance suite - part 8: Big Purchases, Tax Papers and Year Review."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf8_lists import *
from hf8_tables import *
from hf8_tools import tools
import hf8_data as D

SUITE = 'fx-20261116-household-finance'
NOTE = "Sample wording: adapt it to your own household."
def F(*pairs): return [FV(a, b) for a, b in pairs]
IDCOL = {'big_purchases': 'bp_id', 'purchase_options': 'option_id', 'car_decision': 'row_id', 'move_cash': 'month', 'move_plan': 'move_id', 'rb_compare': 'year', 'event_budget': 'event_item_id',
         'tax_docs': 'doc_id', 'deductions': 'deduction_id', 'set_aside': 'sa_id', 'year_review': 'item', 'next_year_plan': 'category', 'ded_cat': 'row_id', 'missing_docs': 'rank'}
def LK(t, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, IDCOL[t])
THISYR = 'YEAR({today})&""'

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('big_purchase_sheet', 'Big Purchase Sheet', 'One big purchase and what it still needs', 'big_purchases.bp_id', F(
        ('Item', 'big_purchases.item'), ('Kind', 'big_purchases.kind'), ('Planned date', 'big_purchases.planned_date'), ('Target', 'big_purchases.target'), ('Saved so far', 'big_purchases.saved'),
        ('Left to save', 'big_purchases.left'), ('Months to the date', 'big_purchases.months_left'), ('Saving needed a month', 'big_purchases.per_month'), ('Share saved', 'big_purchases.saved_share')) + [
        FF('Options compared', 'COUNTIFS({range:purchase_options.bp_id},{pick})', 'int'),
        FF('Highest option price', 'SUMPRODUCT(MAX(({range:purchase_options.bp_id}={pick})*({range:purchase_options.price})))', 'money'),
        FF('Share of the monthly amount in Settings', 'IFERROR(%s/{set:big_saving},0)' % LK('big_purchases', 'per_month'), 'pct')]),
    FORM('option_sheet', 'Purchase Option Sheet', 'One option with its monthly payment and cost', 'purchase_options.option_id', F(
        ('Purchase', 'purchase_options.item'), ('Option', 'purchase_options.option'), ('Price', 'purchase_options.price'), ('Down payment', 'purchase_options.down_payment'), ('Trade-in', 'purchase_options.trade_in'),
        ('Loan months', 'purchase_options.loan_months'), ('Yearly rate', 'purchase_options.rate'), ('Loan amount', 'purchase_options.loan_amount'), ('Monthly payment', 'purchase_options.monthly_payment'),
        ('Monthly cost with running cost', 'purchase_options.monthly_cost')) + [
        FF('Share of take-home', 'IFERROR(%s/(%s),0)' % (LK('purchase_options', 'monthly_cost'), TH), 'pct'),
        FF('Total of payments over the loan', '%s*%s' % (LK('purchase_options', 'monthly_payment'), LK('purchase_options', 'loan_months')), 'money')]),
    FORM('car_decision_sheet', 'Car Decision Sheet', 'One car option at one loan term', 'car_decision.row_id', F(
        ('Option', 'car_decision.option'), ('Loan months tested', 'car_decision.loan_months'), ('Price', 'car_decision.price'), ('Down payment', 'car_decision.down'), ('Monthly payment', 'car_decision.monthly_payment'),
        ('Running cost a month', 'car_decision.running'), ('Monthly cost', 'car_decision.monthly_cost'), ('Total over the years', 'car_decision.total_years'), ('Share of take-home', 'car_decision.share'),
        ('Against your limit', 'car_decision.verdict'), ('More or less than keeping the car', 'car_decision.diff_keep')) + [
        FF('Monthly cost you accept', '{set:car_limit}*(%s)' % TH, 'money')]),
    FORM('moving_plan_sheet', 'Moving Plan Sheet', 'One month of the move cash plan', 'move_cash.month', F(
        ('Due this month', 'move_cash.due_in_month'), ('Cash needed so far', 'move_cash.due_so_far'), ('You have by then', 'move_cash.saved_by'), ('Short or spare', 'move_cash.gap'), ('Status', 'move_cash.status')) + [
        FF('Share of the cash needed that you have', 'IFERROR(%s/%s,0)' % (LK('move_cash', 'saved_by'), LK('move_cash', 'due_so_far')), 'pct'),
        FF('Total cash needed for the move', 'SUM({range:move_plan.left})', 'money'), FF('Monthly saving in Settings', '{set:big_saving}', 'money')]),
    FORM('move_cost_sheet', 'Move Cost Sheet', 'One cost of the move', 'move_plan.move_id', F(
        ('Item', 'move_plan.item'), ('Kind', 'move_plan.kind'), ('Estimate', 'move_plan.estimate'), ('Paid', 'move_plan.paid'), ('Left to pay', 'move_plan.left'), ('Due date', 'move_plan.due_date'),
        ('Days to due', 'move_plan.days_to_due'), ('Status', 'move_plan.status'), ('Move date', 'move_plan.move_date')) + [
        FF('Share of all move costs', 'IFERROR(%s/SUM({range:move_plan.estimate}),0)' % LK('move_plan', 'estimate'), 'pct'), FF('Total cash needed', 'SUM({range:move_plan.left})', 'money')]),
    FORM('rent_buy_sheet', 'Rent or Buy Sheet', 'One year of the rent or buy comparison', 'rb_compare.year', F(
        ('Rent and running cost paid', 'rb_compare.rent_paid'), ('Return on kept money', 'rb_compare.rent_gain'), ('Renting costs in total', 'rb_compare.rent_cost'), ('Monthly mortgage payment', 'rb_compare.mortgage_payment'),
        ('Loan balance left', 'rb_compare.loan_balance'), ('Buying costs paid', 'rb_compare.buy_paid'), ('Home value less loan', 'rb_compare.buy_equity'), ('Buying costs in total', 'rb_compare.buy_cost'),
        ('Buying more or less', 'rb_compare.difference'), ('Break-even year', 'rb_compare.be_years')) + [FF('Difference as a share of renting', 'IFERROR(%s/%s,0)' % (LK('rb_compare', 'difference'), LK('rb_compare', 'rent_cost')), 'pct')]),
    FORM('event_sheet', 'Event Budget Sheet', 'One item of the event budget', 'event_budget.event_item_id', F(
        ('Event', 'event_budget.event'), ('Item', 'event_budget.item'), ('Estimate', 'event_budget.estimate'), ('Paid', 'event_budget.paid'), ('Left to pay', 'event_budget.left'), ('Due date', 'event_budget.due_date'),
        ('Days to due', 'event_budget.days_to_due'), ('Status', 'event_budget.status'), ('Deposit needed', 'event_budget.deposit')) + [
        FF('Share of the estimate total', 'IFERROR(%s/SUM({range:event_budget.estimate}),0)' % LK('event_budget', 'estimate'), 'pct'), FF('Estimate total', 'SUM({range:event_budget.estimate})', 'money'),
        FF('Over the target by', 'MAX(0,SUM({range:event_budget.estimate})-%s)' % LK('event_budget', 'target_total'), 'money')]),
    FORM('tax_doc_sheet', 'Tax Document Sheet', 'One tax document and where the year stands', 'tax_docs.doc_id', F(
        ('Tax year', 'tax_docs.tax_year'), ('Document type', 'tax_docs.doc_type'), ('Description', 'tax_docs.description'), ('Person', 'tax_docs.person'), ('Expected on', 'tax_docs.expected_on'),
        ('Received on', 'tax_docs.received_on'), ('Due date', 'tax_docs.due_date'), ('Days to due date', 'tax_docs.days_to_due'), ('Status', 'tax_docs.status')) + [
        FF('Documents in hand this year', LK('tax_docs', 'received_count'), 'int'), FF('Documents this year', LK('tax_docs', 'year_total'), 'int'), FF('Missing this year', LK('tax_docs', 'missing_count'), 'int')]),
    FORM('deduction_sheet', 'Deduction Record Sheet', 'One record and its category', 'deductions.deduction_id', F(
        ('Date', 'deductions.date'), ('Description', 'deductions.description'), ('Category', 'deductions.category'), ('Amount', 'deductions.amount'), ('Receipt kept', 'deductions.receipt'),
        ('Tax year', 'deductions.tax_year'), ('Person', 'deductions.person')) + [
        FF('Records in this category and year', 'COUNTIFS({range:deductions.category},%s,{range:deductions.tax_year},%s)' % (LK('deductions', 'category'), LK('deductions', 'tax_year')), 'int'),
        FF('Total of this category and year', 'SUMIFS({range:deductions.amount},{range:deductions.category},%s,{range:deductions.tax_year},%s)' % (LK('deductions', 'category'), LK('deductions', 'tax_year')), 'money'),
        FF('Share of the category total', 'IFERROR(%s/SUMIFS({range:deductions.amount},{range:deductions.category},%s,{range:deductions.tax_year},%s),0)' % (LK('deductions', 'amount'), LK('deductions', 'category'), LK('deductions', 'tax_year')), 'pct')]),
    FORM('set_aside_sheet', 'Tax Set-aside Sheet', 'One payment received and what was set aside', 'set_aside.sa_id', F(
        ('Date', 'set_aside.date'), ('Source', 'set_aside.source'), ('Amount received', 'set_aside.amount'), ('Moved to set-aside', 'set_aside.moved'), ('Suggested by the percentage', 'set_aside.suggested'),
        ('Moved above or below', 'set_aside.difference'), ('Running balance', 'set_aside.balance')) + [
        FF('Share moved', 'IFERROR(%s/%s,0)' % (LK('set_aside', 'moved'), LK('set_aside', 'amount')), 'pct'), FF('Percentage in Settings', '{set:set_aside_pct}', 'pct')]),
    FORM('year_sheet', 'Year Review Sheet', 'One line of the year review', 'year_review.item', F(
        ('Last 12 months', 'year_review.this_year'), ('The 12 months before', 'year_review.last_year'), ('Change', 'year_review.change'), ('Change, percent', 'year_review.change_pct'), ('Direction', 'year_review.note'),
        ('Savings rate, last 12 months', 'year_review.savings_rate_all'), ('Net worth change, last 12 months', 'year_review.nw_change_all')) + [
        FF('Savings rate you want', '{set:savings_rate_target}', 'pct')]),
    FORM('plan_sheet', 'Next-year Plan Sheet', 'One category of the next-year plan', 'next_year_plan.category', F(
        ('Group', 'next_year_plan.group'), ('Last 12 months actual', 'next_year_plan.last_year'), ('Change you typed', 'next_year_plan.change'), ('Plan for next year', 'next_year_plan.plan'), ('More or less', 'next_year_plan.diff'),
        ('Plan a month', 'next_year_plan.per_month'), ('Plan for each paycheck', 'next_year_plan.per_paycheck')) + [
        FF('Share of the whole plan', 'IFERROR(%s/SUM({range:next_year_plan.plan}),0)' % LK('next_year_plan', 'plan'), 'pct')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('car_doc', 'Car Decision Page', 'Car decision, one option', 'car_decision.row_id', [
        'Car decision of {set:household}, dated {today}. Option: {col:car_decision.option}, loan of {col:car_decision.loan_months} months.',
        'Price {col:car_decision.price}, down payment {col:car_decision.down}, monthly payment {col:car_decision.monthly_payment}, running cost {col:car_decision.running} a month. Monthly cost: {col:car_decision.monthly_cost}.',
        'Total over the years you keep the car: {col:car_decision.total_years}. Share of take-home pay: {col:car_decision.share}. Against your own limit: {col:car_decision.verdict}.',
        'Keeping the current car costs {col:car_decision.keep_cost} a month; this option is {col:car_decision.diff_keep} against that. An estimate from your numbers, not advice.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('purchases_doc', 'Big Purchases Plan Page', 'Big purchase plan, one purchase', 'big_purchases.bp_id', [
        'Big purchase plan of {set:household}, dated {today}. Item: {col:big_purchases.item} ({col:big_purchases.kind}), priority {col:big_purchases.priority}.',
        'Target {col:big_purchases.target}, saved so far {col:big_purchases.saved}, left to save {col:big_purchases.left}. Planned date: {col:big_purchases.planned_date}, {col:big_purchases.months_left} months away.',
        'Saving needed a month to reach it by that date: {col:big_purchases.per_month}. Share saved: {col:big_purchases.saved_share}.',
        'When two purchases compete for the same savings, the Purchase Order tool shows which is funded first. An estimate from your numbers.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('moving_doc', 'Moving Plan Page', 'Moving plan, cash needed and dates', 'move_plan.move_id', [
        'Moving plan of {set:household}, dated {today}. Move date: {col:move_plan.move_date}.',
        'Item: {col:move_plan.item} ({col:move_plan.kind}). Estimate {col:move_plan.estimate}, paid {col:move_plan.paid}, left to pay {col:move_plan.left}, due on {col:move_plan.due_date} ({col:move_plan.status}).',
        'All move costs together: {col:move_plan.total_needed}. Money saved for the move: {col:move_plan.have}.',
        'Check the dates against your lease and your own notice period. An estimate from your numbers.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('rentbuy_doc', 'Rent or Buy Page', 'Rent or buy, your numbers not advice', 'rb_compare.year', [
        'Rent or buy page of {set:household}, dated {today}. After {col:rb_compare.year} years.',
        'Renting costs {col:rb_compare.rent_cost} in total (rent and running cost {col:rb_compare.rent_paid}, less a return of {col:rb_compare.rent_gain} on the money you keep).',
        'Buying costs {col:rb_compare.buy_cost} in total (paid {col:rb_compare.buy_paid}, less home value after selling costs and loan {col:rb_compare.buy_equity}). Buying more or less than renting: {col:rb_compare.difference}.',
        'Break-even year in your numbers: {col:rb_compare.be_years}. These are your own typed numbers, an estimate and not advice; ask your adviser.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('event_doc', 'Event Budget Page', 'Event budget, one item', 'event_budget.event_item_id', [
        'Event budget of {set:household}, dated {today}. Event: {col:event_budget.event}. Item: {col:event_budget.item}.',
        'Estimate {col:event_budget.estimate}, paid {col:event_budget.paid}, left {col:event_budget.left}, due on {col:event_budget.due_date} ({col:event_budget.status}). Deposit needed: {col:event_budget.deposit}.',
        'All items: estimate {col:event_budget.estimate_total} against a target of {col:event_budget.target_total}; over the target by {col:event_budget.over_by}.',
        'Saving needed a month until the last due date: {col:event_budget.monthly_saving}.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('taxdocs_doc', 'Tax Documents Checklist Page', 'Tax document checklist, one document', 'tax_docs.doc_id', [
        'Tax documents checklist of {set:household}, dated {today}. Tax year {col:tax_docs.tax_year}.',
        'Document: {col:tax_docs.doc_type}, {col:tax_docs.description}. Person: {col:tax_docs.person}. Expected on {col:tax_docs.expected_on}, received on {col:tax_docs.received_on}. Status: {col:tax_docs.status}.',
        'Due date set by your tax office: {col:tax_docs.due_date}, {col:tax_docs.days_to_due} days from today. For this tax year {col:tax_docs.received_count} of {col:tax_docs.year_total} documents are in hand and {col:tax_docs.missing_count} are overdue.',
        'Check your local rules for what you need to keep and file.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('request_doc', 'Missing Documents Letter', 'Request for a missing document', 'missing_docs.rank', [
        'Date: {today}. To: {col:missing_docs.contact}. From: {set:household}.',
        'We are collecting our papers for our tax return and have not yet received: {col:missing_docs.description} ({col:missing_docs.doc_type}), expected on {col:missing_docs.expected_on}.',
        'Please send it to us as soon as you can, or tell us when we can expect it and what you need from us.',
        'Thank you for your help.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('deductions_doc', 'Deduction Records Page', 'Deduction records by category and receipts', 'ded_cat.row_id', [
        'Deduction records of {set:household}, dated {today}. Tax year {col:ded_cat.tax_year}, category {col:ded_cat.category}.',
        'Total recorded {col:ded_cat.total} in {col:ded_cat.records} records. Receipts kept {col:ded_cat.kept}, receipts missing {col:ded_cat.missing} ({col:ded_cat.missing_amount} without a receipt).',
        'All categories this tax year: {col:ded_cat.total_year} recorded, {col:ded_cat.kept_year} receipts kept, {col:ded_cat.missing_year} missing.',
        'These records say nothing about what is allowed. Ask your adviser and check your local rules.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('setaside_doc', 'Tax Set-aside Statement', 'Tax set-aside statement', 'set_aside.sa_id', [
        'Tax set-aside statement of {set:household}, dated {today}. Row {col:set_aside.sa_id}, month {col:set_aside.month}.',
        'Received on {col:set_aside.date} from {col:set_aside.source}: {col:set_aside.amount}. Moved to the set-aside: {col:set_aside.moved}. Suggested by the percentage in Settings: {col:set_aside.suggested}.',
        'Running balance after the estimated payments made so far: {col:set_aside.balance}.',
        'The percentage is an estimate: confirm it with your adviser.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('pack_doc', 'Tax Papers Pack List', 'Tax papers pack for the tax preparer', 'tax_docs.doc_id', [
        'Tax papers pack of {set:household} for tax year {col:tax_docs.tax_year}, dated {today}.',
        'Documents in hand: {col:tax_docs.received_count} of {col:tax_docs.year_total}. Overdue: {col:tax_docs.missing_count}. Due date: {col:tax_docs.due_date}.',
        'Deduction records for the year: {col:tax_docs.year_deductions}, receipts missing: {col:tax_docs.receipts_missing}. Childcare recorded: {col:tax_docs.childcare_total}. Tax set-aside balance: {col:tax_docs.set_balance}.',
        'Please tell us if you need anything else for the year.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('year_doc', 'Year Review Page', 'Year review, one line', 'year_review.item', [
        'Year review of {set:household}, dated {today}. Item: {col:year_review.item}.',
        'Last 12 months: {col:year_review.this_year}. The 12 months before: {col:year_review.last_year}. Change: {col:year_review.change} ({col:year_review.change_pct}), {col:year_review.note}.',
        'Savings rate over the last 12 months: {col:year_review.savings_rate_all}. Net worth change: {col:year_review.nw_change_all}.',
        'Both periods are complete months, so the comparison is fair. Estimates from your own numbers.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('plan_doc', 'Next-year Plan Page', 'Next-year plan, one category', 'next_year_plan.category', [
        'Next-year plan of {set:household}, dated {today}. Category: {col:next_year_plan.category} ({col:next_year_plan.group}).',
        'Last 12 months: {col:next_year_plan.last_year}. Change you typed: {col:next_year_plan.change}. Plan for next year: {col:next_year_plan.plan}, which is {col:next_year_plan.diff} against last year.',
        'That is {col:next_year_plan.per_month} a month and {col:next_year_plan.per_paycheck} for each paycheck. The whole plan is {col:next_year_plan.plan_total}.',
        'An estimate from your numbers: change it as the year goes on.'], ['Partner 1', 'Partner 2'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('car_chk', 'Car Purchase Steps', 'big_purchases', 'big_purchases.planned_date', [('Set the most you accept for a car a month', -120), ('Fill in the Purchase options', -105), ('Run the Car Purchase Decision', -90), ('Run Buy or Keep the Car', -80), ('Ask the mechanic for a check', -45), ('Agree the loan term with your partner', -30), ('Check the saving with the Big Purchase Saving Plan', -14), ('Buy and note the final price', 0)]),
    CHK('moving_chk', 'Moving Steps', 'move_plan', 'move_plan.move_date', [('Tell the landlord the move date', -90), ('Fill in the Move plan costs', -85), ('Run the Moving Plan tool', -80), ('Book the moving company', -45), ('Set up the new connections', -21), ('Redirect the mail', -7), ('Pay the deposit', -30), ('Close the old accounts', 0)]),
    CHK('event_chk', 'Event Planning Steps', 'event_budget', 'event_budget.due_date', [('Set the target total', -90), ('List every item with an estimate', -85), ('Pay the deposits', -60), ('Send the invitations', -45), ('Run the Event Budget tool', -30), ('Confirm the helpers', -14), ('Pay the last items', 0)]),
    CHK('docs_chk', 'Tax Documents Collection Steps', 'tax_docs', 'tax_docs.expected_on', [('Check the Tax documents sheet', 0), ('Ask for each missing document', 7), ('Record the date received', 14), ('Run the Missing Documents Finder', 21), ('Send a reminder to anyone late', 28)]),
    CHK('ded_chk', 'Deduction Records Upkeep Steps', 'deductions', 'deductions.date', [('Type the record', 0), ('Attach or keep the receipt', 1), ('Set the category', 1), ('Mark the receipt as kept', 2), ('Check the Missing Receipts list each month', 30)]),
    CHK('setaside_chk', 'Tax Set-aside Payment Steps', 'est_payments', 'est_payments.date', [('Run the Set-aside Check', -30), ('Ask the tax preparer to confirm the amount', -21), ('Move the missing amount to the set-aside', -14), ('Make the payment', 0), ('Type the payment in Estimated payments', 1)]),
    CHK('pack_chk', 'Tax Papers Pack Steps', 'tax_docs', 'tax_docs.due_date', [('Collect every received document', -60), ('Print the Tax papers pack list', -45), ('Print the Deduction records page', -40), ('Chase the missing receipts', -35), ('Send the pack to the tax preparer', -30), ('Check the due date with your tax office', -14)]),
    CHK('year_chk', 'Year Review Steps', 'year_months', 'year_months.month', [('Check every month is filled in on Year by month', 30), ('Read the Year in Review sheet', 31), ('Read the Category changes', 32), ('Check the Goals reached', 33), ('Write down three things to change', 34)]),
    CHK('plan_chk', 'Next-year Plan Steps', 'year_months', 'year_months.month', [('Open the Next-year plan', 35), ('Type a change for each category', 36), ('Run the Next-year Plan Builder', 37), ('Agree it with your partner', 38), ('Copy the plan month by month into Budget plan', 40)]),
    CHK('decision_chk', 'Big Purchase Decision Steps', 'big_purchases', 'big_purchases.planned_date', [('Write the target and the date', -180), ('Compare at least two options', -150), ('Run the Big Purchase Saving Plan', -120), ('Run the Purchase Order', -90), ('Decide with your partner', -60), ('Buy or move the date', 0)]),
    CHK('close_chk', 'Year-end Money Close Steps', 'year_months', 'year_months.month', [('Enter the last month on Year by month', 28), ('Update the Goals reached', 29), ('Make the last estimated payment', 30), ('List the receipts still missing', 31), ('Set the savings rate you want for next year', 33)]),
    CHK('single_chk', 'Single Adult Year Review Steps', 'year_months', 'year_months.month', [('Fill in Year by month with your own income and spending', 30), ('Leave the partner 2 and children rows empty', 30), ('Read the Year in Review sheet', 31), ('Use the Tax documents and Deduction records sheets', 32), ('Type your own changes in the Next-year plan', 35)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, ph, text): return MSG(k, moment, table, '%s.%s' % (table, ph), text)
messages = [
    M('p2_car', 'Partner 2: the used car option costs', 'car_decision', 'p2_phone', 'Hello {partner2}, the car option {option} costs {monthly_cost} a month, {share} of our take-home. Shall we talk it through? {household}'),
    M('p2_move', 'Partner 2: the move needs cash', 'move_plan', 'p2_phone', 'Hello {partner2}, the move needs {total_needed} in cash by {move_date} and we have {have} saved so far. {household}'),
    M('p2_event', 'Partner 2: the event budget is over', 'event_budget', 'p2_phone', 'Hello {partner2}, the event budget is {estimate_total} against {target_total}, over by {over_by}. Shall we trim it? {household}'),
    M('p2_setaside', 'Partner 2: the tax set-aside', 'est_payments', 'p2_phone', 'Hello {partner2}, the tax set-aside is {balance} and the next payment is on {next_due}. {household}'),
    M('p2_receipts', 'Partner 2: receipts are missing', 'ded_cat', 'p2_phone', 'Hello {partner2}, {missing_year} receipts are missing for {tax_year}. Please find them when you can. {household}'),
    M('p2_year', 'Partner 2: the year review is ready', 'year_review', 'p2_phone', 'Hello {partner2}, the year review is ready: our savings rate over the last 12 months is {savings_rate_all}. {household}'),
    M('p2_plan', 'Partner 2: the next-year plan', 'next_year_plan', 'p2_phone', 'Hello {partner2}, the next-year plan of {plan_total} is ready for your changes by {ready_by}. {household}'),
    M('p1_loan', 'Partner 1: the car loan payment', 'car_decision', 'p1_phone', 'Hello {partner1}, the car loan payment would be {monthly_payment} a month for {loan_months} months. {household}'),
    M('p1_rb', 'Partner 1: rent or buy break even', 'rb_compare', 'p1_phone', 'Hello {partner1}, in our rent or buy numbers buying breaks even in year {be_years}. These are our own numbers, not advice. {household}'),
    M('p1_docs', 'Partner 1: tax documents are due', 'tax_docs', 'p1_phone', 'Hello {partner1}, the tax documents are due on {due_date} and {missing_count} are still missing. {household}'),
    M('p1_pay', 'Partner 1: send your pay statement', 'tax_docs', 'p1_phone', 'Hello {partner1}, please send your pay statement for {tax_year}. {household}'),
    M('p1_nw', 'Partner 1: net worth changed', 'year_review', 'p1_phone', 'Hello {partner1}, our net worth changed by {nw_change_all} over the last 12 months. {household}'),
    M('hm_receipts', 'Household member: receipts to send', 'tax_docs', 'member_phone', 'Hello Ada, please send the charity and medical receipts for {tax_year}. {household}'),
    M('tp_list', 'Tax preparer: the document list', 'tax_docs', 'tax_phone', 'Hello Aiko, here is the document list for {tax_year}: {received_count} of {year_total} received. {household}'),
    M('tp_missing', 'Tax preparer: a document is missing', 'missing_docs', 'tax_phone', 'Hello Aiko, we are still missing {doc_type}, expected on {expected_on}. {household}'),
    M('tp_due', 'Tax preparer: confirm the due date', 'tax_docs', 'tax_phone', 'Hello Aiko, please confirm the due date {due_date} and the pack you need for {tax_year}. {household}'),
    M('tp_ded', 'Tax preparer: our deduction records', 'ded_cat', 'tax_phone', 'Hello Aiko, our deduction records for {tax_year} total {total_year}, with {kept_year} receipts kept. {household}'),
    M('tp_setaside', 'Tax preparer: how much to set aside', 'est_payments', 'tax_phone', 'Hello Aiko, please tell us how much to set aside from freelance income this quarter. Our balance is {balance}. {household}'),
    M('tp_estdate', 'Tax preparer: confirm payment date', 'est_payments', 'tax_phone', 'Hello Aiko, please confirm the estimated payment date {date}. {household}'),
    M('tp_fee', 'Tax preparer: your fee estimate', 'tax_docs', 'tax_phone', 'Hello Aiko, please send your fee estimate for {tax_year}. {household}'),
    M('pr_pay', 'Payroll office: the pay statement', 'tax_docs', 'payroll_phone', 'Hello Dev, please send the pay statement for {tax_year}. {household}'),
    M('ca_sum', 'Client A: a payment summary', 'tax_docs', 'clienta_phone', 'Hello Lena, please send a payment summary for {tax_year}. {household}'),
    M('cb_sum', 'Client B: a payment summary', 'tax_docs', 'clientb_phone', 'Hello Tomas, please send a payment summary for {tax_year}. {household}'),
    M('bk_int', 'Bank branch: interest statements', 'tax_docs', 'bank_phone', 'Hello Elif, please send the interest and investment statements for {tax_year}. {household}'),
    M('bk_loan', 'Bank branch: the loan interest statement', 'tax_docs', 'bank_phone', 'Hello Elif, please send the loan interest statement for {tax_year}. {household}'),
    M('cc_rec', 'Childcare provider: the receipts', 'tax_docs', 'child_phone', 'Hello Nadia, please send the childcare receipts for {tax_year}; we have {childcare_total} recorded. {household}'),
    M('sc_rec', 'School office: the fee receipts', 'tax_docs', 'school_phone', 'Hello Ruth, please send the fee receipts for {tax_year}. {household}'),
    M('in_prem', 'Insurance agent: the premium statement', 'tax_docs', 'ins_phone', 'Hello Carlos, please send the yearly premium statement for {tax_year}. {household}'),
    M('mc_quote', 'Car mechanic: a quote for the car check', 'big_purchases', 'mech_phone', 'Hello Pavel, please send the quote for the used car check on {planned_date}. {household}'),
    M('ll_move', 'Landlord: we plan to move', 'move_plan', 'landlord_phone', 'Hello Marta, we plan to move on {move_date}. Please confirm the notice period. {household}'),
    M('ll_dep', 'Landlord: the deposit return', 'move_plan', 'landlord_phone', 'Hello Marta, please confirm the return date of the deposit after we leave on {move_date}. {household}'),
    M('ut_new', 'Utility company: the new connection', 'move_plan', 'util_phone', 'Hello Yara, please set up the connection at the new home on {due_date}. {household}'),
    M('ut_old', 'Utility company: close the old account', 'move_plan', 'util_phone', 'Hello Yara, please close the account at the old home on {move_date}. {household}'),
    M('gp_event', 'Grandparent: the family celebration', 'event_budget', 'gp_phone', 'Hello Ada, we plan the family celebration on {due_date}. Can you help with {item}? {household}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
BPR = lambda c: R('big_purchases', c)
NOTB = '%s,"<>"&%s' % (BPR('status'), BOUGHT)
NXTD = 'IFERROR(SMALL(%s,COUNTIF(%s,"<"&{today})+1),"")' % (BPR('planned_date'), BPR('planned_date'))
BEST = 'MIN(%s)' % R('purchase_options', 'car_key')
NWC = '(SUMIFS(%s,%s,EDATE(%s,-1))-SUMIFS(%s,%s,EDATE(%s,-13)))' % (R('year_months', 'net_worth'), R('year_months', 'month'), MS, R('year_months', 'net_worth'), R('year_months', 'month'), MS)
TDR = lambda c: R('tax_docs', c)
DDR = lambda c: R('deductions', c)
kpis = [
    KPI('Big purchases planned', 'COUNTIFS(%s,"<>",%s)' % (BPR('bp_id'), NOTB), 'int'), KPI('Big purchases total target', 'SUMIFS(%s,%s)' % (BPR('target'), NOTB), 'money'),
    KPI('Big purchases saved so far', 'SUMIFS(%s,%s)' % (BPR('saved'), NOTB), 'money'), KPI('Next big purchase date', NXTD, 'date'),
    KPI('Months to the next big purchase', 'IFERROR(ROUND((%s-{today})/30.4375,1),"")' % NXTD, 'num'), KPI('Saving needed a month, all purchases', 'SUM(%s)' % BPR('per_month'), 'money'),
    KPI('Used car monthly cost, best option', BEST, 'money'), KPI('Used car share of take-home', 'IFERROR(%s/(%s),0)' % (BEST, TH), 'pct'),
    KPI('Car decision against your limit', 'IF(IFERROR(%s/(%s),0)<={set:car_limit},%s,%s)' % (BEST, TH, vd('Within your limit'), vd('Above your limit')), 'text'),
    KPI('Move cash needed', 'SUM(%s)' % R('move_plan', 'estimate'), 'money'), KPI('Move cash paid', 'SUM(%s)' % R('move_plan', 'paid'), 'money'), KPI('Move cash left', 'SUM(%s)' % R('move_plan', 'left'), 'money'),
    KPI('Earliest move date', '{today}+ROUND(ROUNDUP(MAX(0,SUM(%s)-%s)/{set:big_saving},0)*30.4375,0)' % (R('move_plan', 'left'), HAVE_MOVE), 'date'),
    KPI('Event estimate total', 'SUM(%s)' % R('event_budget', 'estimate'), 'money'), KPI('Event paid', 'SUM(%s)' % R('event_budget', 'paid'), 'money'),
    KPI('Event over target', 'MAX(0,SUM(%s)-AVERAGE(%s))' % (R('event_budget', 'estimate'), R('event_budget', 'target_total')), 'money'),
    KPI('Tax documents received this year', 'COUNTIFS(%s,%s,%s,1)' % (TDR('tax_year'), THISYR, TDR('got')), 'int'),
    KPI('Tax documents missing this year', 'COUNTIFS(%s,%s,%s,%s)' % (TDR('tax_year'), THISYR, TDR('status'), st('Overdue')), 'int'),
    KPI('Days to the tax due date', 'IFERROR(SMALL(%s,COUNTIF(%s,"<"&{today})+1)-{today},"")' % (TDR('due_date'), TDR('due_date')), 'int'),
    KPI('Documents filed last year', 'COUNTIFS(%s,(YEAR({today})-1)&"",%s,%s)' % (TDR('tax_year'), TDR('filed'), YES), 'int'),
    KPI('Deduction records this year', 'COUNTIFS(%s,%s,%s,"<>")' % (DDR('tax_year'), THISYR, DDR('deduction_id')), 'int'),
    KPI('Deduction amount recorded this year', 'SUMIFS(%s,%s,%s)' % (DDR('amount'), DDR('tax_year'), THISYR), 'money'),
    KPI('Receipts missing this year', 'COUNTIFS(%s,%s,%s,%s)' % (DDR('tax_year'), THISYR, DDR('receipt'), NO), 'int'),
    KPI('Missing receipt amount', 'SUMIFS(%s,%s,%s,%s,%s)' % (DDR('amount'), DDR('tax_year'), THISYR, DDR('receipt'), NO), 'money'),
    KPI('Tax set-aside balance', BAL_NOW, 'money'), KPI('Set-aside moved, last 12 months', 'SUMIFS(%s,%s,">="&EDATE({today},-12))' % (R('set_aside', 'moved'), R('set_aside', 'date')), 'money'),
    KPI('Next estimated payment', 'SUMIFS(%s,%s,1)' % (R('est_payments', 'payment'), R('est_payments', 'is_next')), 'money'),
    KPI('Year take-home, last 12 months', 'SUMIFS(%s,%s,1)' % (R('year_months', 'take_home'), R('year_months', 'last12')), 'money'),
    KPI('Year savings rate', 'IFERROR(SUMIFS(%s,%s,1)/SUMIFS(%s,%s,1),0)' % (R('year_months', 'total_saved'), R('year_months', 'last12'), R('year_months', 'basis'), R('year_months', 'last12')), 'pct'),
    KPI('Net worth change, last 12 months', NWC, 'money'),
]
assert len(kpis) == 30
dashboard = {"title": "Purchases and Year Dashboard", "kpis": kpis,
    "monthly": {"title": "Take-home pay, spending and saving by month", "date": "year_months.month", "series": [
        {"label": "Take-home pay", "sum": "year_months.take_home", "date": "year_months.month"}, {"label": "Counted spending", "sum": "year_months.spending", "date": "year_months.month"},
        {"label": "Total saved", "sum": "year_months.total_saved", "date": "year_months.month"}]},
    "breakdowns": [{"title": "Big purchases by kind", "by": "big_purchases.kind", "value": "big_purchases.target", "agg": "sum"},
                   {"title": "Deductions by category", "by": "deductions.category", "value": "deductions.amount", "agg": "sum"},
                   {"title": "Tax documents by type", "by": "tax_docs.doc_type", "value": "tax_docs.doc_id", "agg": "count"},
                   {"title": "Year spending by group", "by": "category_changes.group", "value": "category_changes.this_year", "agg": "sum"}]}

def AM(t, c, date=None, label=None, where=None, agg='sum'): return AGG(agg, t, '%s.%s' % (t, c), date=('%s.%s' % (t, date)) if date else None, where=where, label=label)
UNB = [('status', '<>', BOUGHT)]
insights = {"filters": [{"label": "Person", "list": "person"}, {"label": "Purchase kind", "list": "bpkind"}, {"label": "Tax year", "list": "tyear"}],
    "gauges": [
        {"title": "Big purchases saved against target", "num": AM('big_purchases', 'saved', where=UNB), "den": AM('big_purchases', 'target', where=UNB)},
        {"title": "Tax documents in hand", "num": AGG('count', 'tax_docs', where=[('got', '=', 1)]), "den": AGG('count', 'tax_docs')},
        {"title": "Deduction receipts kept", "num": AGG('count', 'deductions', where=[('receipt', '=', YES)]), "den": AGG('count', 'deductions')},
        {"title": "Next payment against the set-aside", "num": AM('est_payments', 'payment', where=[('is_next', '=', 1)]), "den": AM('est_payments', 'balance_before', where=[('is_next', '=', 1)])},
        {"title": "Event target against the estimates", "num": AM('event_budget', 'target_total', agg='avg'), "den": AM('event_budget', 'estimate')},
        {"title": "Next-year plan against take-home", "num": AM('next_year_plan', 'plan', where=[('group', '<>', tok('group', 'Savings')), ('group', '<>', tok('group', 'Debt payments'))]),
         "den": AM('year_months', 'take_home', where=[('last12', '=', 1)])}],
    "charts": [
        CHART('Big purchases by target', 'bar', 'big_purchases.kind', [AM('big_purchases', 'target', label='Target', where=UNB)]),
        CHART('Saved against target by status', 'bar', 'big_purchases.status', [AM('big_purchases', 'saved', label='Saved'), AM('big_purchases', 'target', label='Target')]),
        CHART('Purchases by planned month', 'column', 'month', [AM('big_purchases', 'target', 'planned_date', 'Target')]),
        CHART('Car options, average monthly cost', 'bar', 'car_decision.option', [AM('car_decision', 'monthly_cost', label='Monthly cost', agg='avg')]),
        CHART('Car options, average total cost', 'bar', 'car_decision.option', [AM('car_decision', 'total_years', label='Total over the years', agg='avg')]),
        CHART('Move cost by kind', 'bar', 'move_plan.kind', [AM('move_plan', 'estimate', label='Estimate')]),
        CHART('Move cash needed and what you have', 'column', 'month', [AM('move_cash', 'due_so_far', 'month', 'Cash needed so far'), AM('move_cash', 'saved_by', 'month', 'You have by then')]),
        CHART('Event items by estimate', 'bar', 'event_budget.item', [AM('event_budget', 'estimate', label='Estimate')]),
        CHART('Event paid and left by item', 'bar', 'event_budget.item', [AM('event_budget', 'paid', label='Paid'), AM('event_budget', 'left', label='Left to pay')]),
        CHART('Tax documents by type', 'bar', 'tax_docs.doc_type', [AGG('count', 'tax_docs', label='Documents')]),
        CHART('Tax documents by person', 'bar', 'tax_docs.person', [AGG('count', 'tax_docs', label='Documents')]),
        CHART('Tax documents by year', 'bar', 'tax_docs.tax_year', [AGG('count', 'tax_docs', label='Documents')]),
        CHART('Deduction records per month', 'column', 'month', [AM('deductions', 'amount', 'date', 'Recorded')]),
        CHART('Deductions by category', 'bar', 'deductions.category', [AM('deductions', 'amount', label='Recorded')]),
        CHART('Deductions by person', 'bar', 'deductions.person', [AM('deductions', 'amount', label='Recorded')]),
        CHART('Receipts kept and missing by category', 'bar', 'ded_cat.category', [AM('ded_cat', 'kept', label='Receipts kept'), AM('ded_cat', 'missing', label='Receipts missing')]),
        CHART('Tax set-aside per month', 'line', 'month', [AM('set_aside', 'moved', 'date', 'Moved to the set-aside')]),
        CHART('Estimated payments per year', 'bar', 'est_payments.tax_year', [AM('est_payments', 'payment', label='Payments')]),
        CHART('Year income per month', 'stacked', 'month', [AM('year_months', 'paycheck', 'month', 'Partner 1 paychecks'), AM('year_months', 'other_income', 'month', 'Freelance and other')]),
        CHART('Year spending by group', 'bar', 'category_changes.group', [AM('category_changes', 'this_year', label='Last 12 months'), AM('category_changes', 'last_year', label='The 12 months before')]),
        CHART('Category changes against last year', 'bar', 'category_changes.category', [AM('category_changes', 'change', label='Change')]),
        CHART('Net worth change per month', 'column', 'month', [AM('year_months', 'nw_change', 'month', 'Net worth change')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Car purchase decision", "why": "price, deposit, trade-in, loan term and rate in one place: the monthly cost, the total over the years and the share of take-home against your own limit", "where": "Car Purchase Decision"},
    {"name": "Car decision at every loan term", "why": "each car option tested at six loan terms side by side so you see how a longer loan lowers the payment and raises the total", "where": "Car decision"},
    {"name": "Purchase order", "why": "when the car and the move compete for the same savings, it shows which to fund first and the date each is funded", "where": "Purchase Order"},
    {"name": "Moving plan with cash by month", "why": "every move cost with a due date, the cash needed month by month and the date you have it at your saving rate", "where": "Moving Plan"},
    {"name": "Rent or buy comparison", "why": "your own numbers for 15 years, with the year buying starts to cost less; your numbers, never advice", "where": "Rent or buy comparison"},
    {"name": "Tax documents countdown", "why": "every paper by type, received and filed, with the days to the due date and the documents still missing", "where": "Tax Documents Countdown"},
    {"name": "Missing receipts finder", "why": "records without a receipt ranked by amount, with the first thing to try for each", "where": "Missing Receipts Finder"},
    {"name": "Estimated tax set-aside", "why": "a typed percentage of freelance income, a running balance and a check against the next estimated payment", "where": "Estimated Tax Set-aside"},
    {"name": "Year review and next-year plan", "why": "the last 12 months against the 12 before, the biggest category changes and a plan from last year's actuals with a typed change per category", "where": "Year review"}]
competitors = [
    {"what": "budgeting app with a monthly subscription and bank links", "lacks": "has no car decision at several loan terms, no moving cash plan and no tax set-aside check, and charges every month"},
    {"what": "single-purpose budget template", "lacks": "stops at monthly spending: no big purchase order, no tax documents checklist and no year review"},
    {"what": "free car loan calculator sheet", "lacks": "gives one payment but not the share of take-home, the total over the years you keep the car or the comparison with keeping the old one"},
    {"what": "tax records spreadsheet", "lacks": "lists receipts but never ranks the missing ones by amount, never counts down to the due date and never checks the set-aside"}]
guide = [
    'Start here: open Start and type the household name, the two partner names, the savings rate you want, the car limit and the monthly amount for big purchases in the yellow cells.',
    'Replace demo data, step 1: clear the demo rows of Big purchases, Purchase options, Move plan, Event budget, Tax documents and Deduction records and type your own; keep the header rows.',
    'Replace demo data, step 2: paste your monthly totals into Year by month and your category totals into Category changes, then type your own changes in the Next-year plan.',
    'Replace demo data, step 3: type your own numbers in Rent or buy inputs and your own estimated payment dates in Estimated payments; your tax office gives you the dates.',
    'Pay-day routine: when a freelance payment arrives, add it to Tax set-aside with the amount you moved; when you pay something for the tax return, add a Deduction record and keep the receipt.',
    'Month-close routine, in this order: add the month to Year by month, read Missing receipts, read Missing documents, run the Set-aside Check and update the saved amount of each big purchase.',
    'Run the Car Purchase Decision before you say yes to a car and the Purchase Order when two purchases compete for the same savings; any range shown is a typical range, check your own numbers.',
    'A single adult with one income and no children can use the purchase, tax and year sheets: leave the partner 2 and children rows empty and use Partner 1 as the person.',
    f'Use the {len(tools)} tools for the big decisions, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'Read the dashboard and the Charts page before the tax date and at the year end: purchases, documents, receipts, set-aside and the year review.',
    'Why a workbook: one flat price, no yearly renewal, your data stays with you and there is nothing to link or re-connect; you type or paste your own data. It works in Excel and Google Sheets with no macros.',
    'What this is not: it is not a bank app, and not tax, legal, investment or credit advice; check your local rules and ask your adviser. Every verdict is an estimate from your numbers.']
listing = {"title": "Big Purchases, Tax Papers and Year Review Excel Template: Car Decision, Moving Plan, Tax Checklist, Deduction Records, Year in Review",
    "headline": "Decide the big purchases, keep the tax papers and review the year",
    "tags": ["car purchase planner", "moving budget", "rent or buy", "tax documents", "deduction records", "tax set-aside", "year in review", "net worth change", "household budget", "excel template", "family finance", "no subscription", "budget workbook"],
    "description": ("Decide the big, rare money questions of your household in one Excel workbook, for a single adult, a couple or a family. The Car Purchase Decision tests price, deposit, trade-in, loan term, rate and running cost and shows the monthly cost, the total over the years you keep the car and its share of take-home pay against your own limit. "
        "Each car option is tested at six loan terms side by side. The Purchase Order shows which big purchase to fund first when the car and a move compete for the same savings, and the Moving Plan lists every move cost with the cash needed month by month and the date you have it.\n\n"
        "The Rent or Buy comparison uses your own typed numbers over 15 years and marks the year buying starts to cost less. It is an estimate from your numbers, never advice. An event budget tracks estimates, deposits and what is paid against a target.\n\n"
        "The tax pages keep your papers in order: a Tax Documents Checklist with received and filed dates and a countdown to the due date your tax office gave you, a Missing Documents list ranked by days overdue, Deduction Records with receipts kept and missing by category, a Missing Receipts list ranked by amount, and a Tax Set-aside with a running balance checked against the next estimated payment. Nothing here says what is claimable: check your local rules and ask your adviser.\n\n"
        "The Year Review sets the last 12 complete months against the 12 before: income, spending, saving rate, debt paid, interest paid, net worth change, goals and loans reached and the biggest category changes. The Next-year Plan starts from last year's actuals with a typed change per category, shown a month and for each paycheck.\n\n"
        f"{len(tools)} decision tools, {len(forms)} printable sheets, {len(documents)} documents, {len(checklists)} checklists and {len(messages)} ready text messages come with it. This is part eight of the Household Finance suite. A standard .xlsx workbook that works in Excel and Google Sheets, with no macros, no subscription and no bank links: you type or paste your own data. The demo copy is full of sample data. "
        "It is a household money kit, not a bank app, and not tax, legal, investment or credit advice."),
    "features": ["Car purchase decision against your own limit", "Each car option at six loan terms", "Purchase order when purchases compete for savings", "Moving plan with cash needed by month", "Rent or buy comparison from your numbers",
                 "Tax documents checklist with a due-date countdown", "Missing documents and missing receipts ranked", "Estimated tax set-aside with a running balance", "Year review on 12 complete months against the 12 before",
                 "Next-year plan from last year's actuals", f"{len(tools)} decision tools and {len(forms)} printable sheets", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "One flat price, no subscription, no bank links"]}
s = spec(id=f'{SUITE}-p8', slug='household-finance-yearplan', profession='Household Finance', name='Big Purchases, Tax and Year Review',
         tagline='Decide the big purchases, keep the tax papers, review the year', price_usd=29, colors={"primary": "#1F5F5B", "accent": "#F2B134"},
         settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide, listing=listing, insights=insights,
         suite={"key": SUITE, "part": 8, "of": 8, "focus": "Big purchases, tax papers and year review"}, signature=signature, competitors=competitors, tools=tools,
         messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hf8.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'name', len(s['name']))
