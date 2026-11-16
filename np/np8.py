"""Nonprofit Organization suite - part 8: Budget, Cash and Annual Report."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np8_lists import *
from np8_tables import settings, tables, FI, NOWROW
from np8_tools import SH, FS
from np8_tools import tools
import np8_data as D

SUITE = 'fx-20261115-nonprofit'
NOTE = "Sample wording: adapt it to your own organization and check your local rules."
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
JAN1 = 'DATE(YEAR({today}),1,1)'
CURM = 'DATE(YEAR({today}),MONTH({today}),1)'
THIS = tok('yr', 'This year'); LAST = tok('yr', 'Last year')
def R(t, c): return '{range:%s.%s}' % (t, c)
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
fn = first_name
FC = lambda c: R('forecast', c)

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('budget_sheet', 'Budget Sheet', 'Budget line for one area and month', 'budget.budget_id', F(('Month', 'budget.month'), ('Area', 'budget.area'), ('Budget', 'budget.budget'), ('Year', 'budget.year')) + [
        FF('Same month last year, same area', 'SUMIFS(%s,%s,EDATE(%s,-12),%s,%s)' % (R('budget', 'budget'), R('budget', 'month'), LK('budget', 'budget_id', 'month'), R('budget', 'area'), LK('budget', 'budget_id', 'area')), 'money'),
        FF('Budget of the area for the whole year', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('budget', 'budget'), R('budget', 'area'), LK('budget', 'budget_id', 'area'), R('budget', 'year'), LK('budget', 'budget_id', 'year')), 'money'),
        FF('Share of the whole budget that month', 'IFERROR(%s/SUMIFS(%s,%s,%s),0)' % (LK('budget', 'budget_id', 'budget'), R('budget', 'budget'), R('budget', 'month'), LK('budget', 'budget_id', 'month')), 'pct')]),
    FORM('change_sheet', 'Budget Change Sheet', 'Change of a budget line after the actual cost', 'budget_actual.row_id', F(('Month', 'budget_actual.month'), ('Area', 'budget_actual.area'), ('Budget', 'budget_actual.budget'), ('Direct cost', 'budget_actual.direct'),
        ('Allocated shared cost', 'budget_actual.shared_part'), ('Actual', 'budget_actual.actual'), ('Difference', 'budget_actual.difference'), ('Share used', 'budget_actual.share_used'), ('Status', 'budget_actual.status')) + [
        FF('Suggested monthly budget with your trend', 'ROUND(%s*(1+{set:trend}),0)' % LK('budget_actual', 'row_id', 'actual'), 'money'),
        FF('Change on the present budget', 'ROUND(%s*(1+{set:trend}),0)-%s' % (LK('budget_actual', 'row_id', 'actual'), LK('budget_actual', 'row_id', 'budget')), 'money')]),
    FORM('income_budget_sheet', 'Income Budget Sheet', 'Income budget line for one month', 'income_budget.income_id', F(('Month', 'income_budget.month'), ('Income line', 'income_budget.line'), ('Budget', 'income_budget.budget'), ('Year', 'income_budget.year')) + [
        FF('Same month last year, same line', 'SUMIFS(%s,%s,EDATE(%s,-12),%s,%s)' % (R('income_budget', 'budget'), R('income_budget', 'month'), LK('income_budget', 'income_id', 'month'), R('income_budget', 'line'), LK('income_budget', 'income_id', 'line')), 'money'),
        FF('Budget of the line for the whole year', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('income_budget', 'budget'), R('income_budget', 'line'), LK('income_budget', 'income_id', 'line'), R('income_budget', 'year'), LK('income_budget', 'income_id', 'year')), 'money'),
        FF('Money in that month so far', 'SUMIFS(%s,%s,%s)' % (R('income_source', 'total'), R('income_source', 'month'), LK('income_budget', 'income_id', 'month')), 'money')]),
    FORM('expense_sheet', 'Expense Sheet', 'Expense record', 'expenses.expense_id', F(('Date', 'expenses.date'), ('Category', 'expenses.category'), ('Vendor', 'expenses.vendor'), ('Program', 'expenses.program'), ('Function', 'expenses.function'), ('Fund', 'expenses.fund'),
        ('Amount', 'expenses.amount')) + [
        FF('Rule of the category', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (R('expense_categories', 'rule'), LK('expenses', 'expense_id', 'category'), R('expense_categories', 'category')), 'text'),
        FF('Program share of the category', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('expense_categories', 'program_share'), LK('expenses', 'expense_id', 'category'), R('expense_categories', 'category')), 'pct'),
        FF('Category total this year', 'SUMIFS(%s,%s,%s,%s,">="&%s)' % (R('expenses', 'amount'), R('expenses', 'category'), LK('expenses', 'expense_id', 'category'), R('expenses', 'date'), JAN1), 'money'),
        FF('Share of all money out this year', 'IFERROR(%s/SUMIFS(%s,%s,">="&%s),0)' % (LK('expenses', 'expense_id', 'amount'), R('expenses', 'amount'), R('expenses', 'date'), JAN1), 'pct')]),
    FORM('rule_sheet', 'Shared Cost Rule Sheet', 'Rule and shares of one expense category', 'expense_categories.category', F(('Category', 'expense_categories.category'), ('Program share', 'expense_categories.program_share'),
        ('Management share', 'expense_categories.management_share'), ('Fundraising share', 'expense_categories.fundraising_share'), ('Rule', 'expense_categories.rule'), ('Basis of the rule', 'expense_categories.basis'),
        ('Shares add to 100%', 'expense_categories.check'), ('Shared cost this year', 'expense_categories.shared_year')) + [
        FF('Charged to programs this year', 'SUMIFS(%s,%s,{pick})' % (R('allocation_rules', 'program'), R('allocation_rules', 'category')), 'money'),
        FF('Charged to management this year', 'SUMIFS(%s,%s,{pick})' % (R('allocation_rules', 'management'), R('allocation_rules', 'category')), 'money'),
        FF('Charged to fundraising this year', 'SUMIFS(%s,%s,{pick})' % (R('allocation_rules', 'fundraising'), R('allocation_rules', 'category')), 'money')]),
    FORM('forecast_sheet', 'Cash Forecast Input Sheet', 'Cash forecast month', 'forecast.forecast_id', F(('Month', 'forecast.month'), ('Gifts', 'forecast.gifts'), ('Recurring gifts', 'forecast.recurring'), ('Pledges due', 'forecast.pledges_due'),
        ('Grants', 'forecast.grants'), ('Event net', 'forecast.event_net'), ('Dues', 'forecast.dues'), ('Expenses', 'forecast.expenses'), ('Net for the month', 'forecast.net'), ('Closing cash', 'forecast.closing'),
        ('Free money', 'forecast.free_money'), ('Months of reserve', 'forecast.reserve_months')) + [
        FF('Months of reserve you want', '{set:reserve_months}', 'num'), FF('Free money above the setting', LK('forecast', 'forecast_id', 'headroom'), 'money')]),
    FORM('oneoff_sheet', 'One-off Cost Sheet', 'One-off cost in the forecast', 'forecast.forecast_id', F(('Month', 'forecast.month'), ('One-off cost', 'forecast.one_off'), ('Closing cash', 'forecast.closing'), ('Months of reserve', 'forecast.reserve_months')) + [
        FF('Biggest one-off cost in the forecast', 'MAX(%s)' % FC('one_off'), 'money'),
        FF('Reserve months without one-off cost', 'ROUND((%s+SUMIFS(%s,%s,"<="&%s))/%s,2)' % (LK('forecast', 'forecast_id', 'free_money'), FC('one_off'), FC('month'), LK('forecast', 'forecast_id', 'month'), LK('forecast', 'forecast_id', 'avg_expense')), 'num'),
        FF('One-off cost to date', 'SUMIFS(%s,%s,"<="&%s)' % (FC('one_off'), FC('month'), LK('forecast', 'forecast_id', 'month')), 'money')]),
    FORM('hire_sheet', 'Hire Sheet', 'New hire: cost and verdict', 'afford.item', F(('Hire or program', 'afford.item'), ('Monthly cost', 'afford.monthly_cost'), ('Set-up cost', 'afford.setup_cost'), ('Start month number', 'afford.start_no'),
        ('Cost for a full year', 'afford.yearly_cost'), ('Verdict', 'afford.verdict')) + [
        FF('Pay before employer costs', 'ROUND(%s/(1+{set:employer_cost_pct}),0)' % LK('afford', 'item', 'monthly_cost'), 'money'),
        FF('Employer costs each month', '%s-ROUND(%s/(1+{set:employer_cost_pct}),0)' % (LK('afford', 'item', 'monthly_cost'), LK('afford', 'item', 'monthly_cost')), 'money'),
        FF('Months under the setting', LK('afford', 'item', 'short_months'), 'int')]),
    FORM('program_sheet', 'Program Start Sheet', 'New program: funding check', 'afford.item', F(('Program or hire', 'afford.item'), ('Monthly cost', 'afford.monthly_cost'), ('Set-up cost', 'afford.setup_cost'), ('Months funded above the setting', 'afford.months_funded'),
        ('Lowest months of reserve after', 'afford.reserve_after'), ('Earliest start number', 'afford.first_ok')) + [
        FF('Hire capacity a month on free money now', 'MAX(0,ROUND((%s-{set:reserve_months}*%s)/12,0))' % (NOWROW('free_money'), NOWROW('avg_monthly_expense')), 'money'),
        FF('Gap between cost and capacity', 'MAX(0,%s-MAX(0,ROUND((%s-{set:reserve_months}*%s)/12,0)))' % (LK('afford', 'item', 'monthly_cost'), NOWROW('free_money'), NOWROW('avg_monthly_expense')), 'money'),
        FF('Restricted money now', NOWROW('restricted'), 'money')]),
    FORM('scenario_sheet', 'Scenario Sheet', 'One scenario and its result', 'scenarios.scenario', F(('Scenario', 'scenarios.scenario'), ('Change in gifts', 'scenarios.gifts_pct'), ('Change in recurring gifts', 'scenarios.recurring_pct'),
        ('Change in costs', 'scenarios.cost_pct'), ('Income change', 'scenarios.income_change'), ('Cost change', 'scenarios.cost_change'), ('Year-end cash', 'scenarios.year_end_cash'), ('Months of reserve', 'scenarios.reserve_months'), ('Verdict', 'scenarios.verdict')) + [
        FF('Months of reserve in the base scenario', 'SUMIFS(%s,%s,%s)' % (R('scenarios', 'reserve_months'), R('scenarios', 'scenario'), tok('scen', 'Base')), 'num'),
        FF('Months of reserve against the base', 'ROUND(%s-SUMIFS(%s,%s,%s),2)' % (LK('scenarios', 'scenario', 'reserve_months'), R('scenarios', 'reserve_months'), R('scenarios', 'scenario'), tok('scen', 'Base')), 'num')]),
    FORM('reserve_sheet', 'Reserve Policy Sheet', 'Reserve of one month against the policy', 'cash.cash_id', F(('Month', 'cash.month'), ('Closing cash', 'cash.closing'), ('Restricted money', 'cash.restricted'), ('Designated money', 'cash.designated'),
        ('Free money', 'cash.free_money'), ('Average monthly expense', 'cash.avg_monthly_expense'), ('Months of reserve', 'cash.reserve_months')) + [
        FF('Months of reserve you want', '{set:reserve_months}', 'num'), FF('Free money needed for the setting', '{set:reserve_months}*%s' % LK('cash', 'cash_id', 'avg_monthly_expense'), 'money'),
        FF('Free money above or below the setting', '%s-{set:reserve_months}*%s' % (LK('cash', 'cash_id', 'free_money'), LK('cash', 'cash_id', 'avg_monthly_expense')), 'money')]),
    FORM('report_sheet', 'Annual Report Numbers Sheet', 'One number of the annual report', 'annual_report.item', F(('Item', 'annual_report.item'), ('Number', 'annual_report.no'), ('This year', 'annual_report.this_year'), ('Last year', 'annual_report.last_year'),
        ('Status', 'annual_report.status'), ('Sentence', 'annual_report.sentence')) + [
        FF('Change on last year', 'ROUND(%s-%s,2)' % (LK('annual_report', 'item', 'this_year'), LK('annual_report', 'item', 'last_year')), 'num'),
        FF('Items ready', LK('annual_report', 'item', 'items_ready'), 'int'), FF('Items missing', LK('annual_report', 'item', 'missing_n'), 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('func_doc', 'Budget by Program and Function', 'Budget by program, management and fundraising for one month', 'functional.month', [
        'Functional budget page of {set:org}, dated {today}. Month: {col:functional.month_name}. Budget for the month: {col:functional.budget}.',
        'Cost by function after each shared cost is split by its rule: programs {col:functional.program}, management {col:functional.management}, fundraising {col:functional.fundraising}. Total {col:functional.total}.',
        'Shares: programs {col:functional.program_share}, management {col:functional.management_share}, fundraising {col:functional.fundraising_share}.',
        'Fundraising share this year {col:functional.fr_share_year} against {col:functional.fr_share_last} last year. Budget for next year, your estimate: {col:functional.next_budget}.'], ['Executive director', 'Finance chair'], NOTE),
    DOC('bva_doc', 'Budget vs Actual Statement', 'Budget against actual statement for one area and month', 'budget_actual.row_id', [
        'Budget against actual of {set:org}, dated {today}. Area: {col:budget_actual.area}. Month: {col:budget_actual.month_name}.',
        'Budget {col:budget_actual.budget}. Direct cost {col:budget_actual.direct}. Allocated shared cost {col:budget_actual.shared_part}. Actual {col:budget_actual.actual}.',
        'Difference {col:budget_actual.difference}. Share of the budget used {col:budget_actual.share_used}. Status: {col:budget_actual.status}.',
        'Explain any difference above your tolerance and say what will change next month.'], ['Program manager', 'Executive director'], NOTE),
    DOC('fc_doc', 'Cash Forecast Page', 'Cash forecast page for one month', 'forecast.forecast_id', [
        'Cash forecast of {set:org}, dated {today}. Month: {col:forecast.month_name}.',
        'Money in: gifts {col:forecast.gifts}, recurring {col:forecast.recurring}, pledges due {col:forecast.pledges_due}, grants {col:forecast.grants}, event net {col:forecast.event_net}, dues {col:forecast.dues}. Expenses {col:forecast.expenses}. One-off cost {col:forecast.one_off}.',
        'Net for the month {col:forecast.net}. Closing cash {col:forecast.closing}. Free money {col:forecast.free_money}. Months of reserve {col:forecast.reserve_months} against the setting of {col:forecast.setting}.',
        'The lowest cash in the next 12 months is {col:forecast.low_amount}, in {col:forecast.low_month_name}. This is your estimate, not a promise of income.'], ['Executive director', 'Finance chair'], NOTE),
    DOC('reserve_doc', 'Reserve Months Report', 'Reserve months report for one month', 'cash.cash_id', [
        'Reserve report of {set:org}, dated {today}. Month: {col:cash.month_name}.',
        'Closing cash {col:cash.closing}. Restricted money (money given for one purpose) {col:cash.restricted}. Designated money (set aside by the board for a purpose, it can change that) {col:cash.designated}.',
        'Free money (cash less restricted and designated money) {col:cash.free_money}. Average monthly expense {col:cash.avg_monthly_expense}. Months of reserve (free money divided by average monthly expense) {col:cash.reserve_months}.',
        'The starting point of {col:cash.setting} months is yours to change.'], ['Finance chair', 'Executive director'], NOTE),
    DOC('scen_doc', 'Scenario Test Report', 'Scenario test report', 'scenarios.scenario', [
        'Scenario test of {set:org}, dated {today}. Scenario: {col:scenarios.scenario}.',
        'Change in gifts {col:scenarios.gifts_pct}, in recurring gifts {col:scenarios.recurring_pct}, in costs {col:scenarios.cost_pct}. Income change {col:scenarios.income_change}. Cost change {col:scenarios.cost_change}.',
        'Year-end cash {col:scenarios.year_end_cash}. Months of reserve {col:scenarios.reserve_months} against the setting of {col:scenarios.setting}. Verdict: {col:scenarios.verdict}.',
        'This is your estimate from your own forecast, not a promise of any result.'], ['Executive director', 'Finance chair'], NOTE),
    DOC('afford_doc', 'Afford This Decision Page', 'Decision page for a new hire or program', 'afford.item', [
        'Decision page of {set:org}, dated {today}. Proposal: {col:afford.item}.',
        'Monthly cost {col:afford.monthly_cost}. Set-up cost {col:afford.setup_cost}. Planned start: month number {col:afford.start_no}. Cost for a full year {col:afford.yearly_cost}.',
        'Months funded above the reserve setting: {col:afford.months_funded}. Lowest months of reserve after the cost starts: {col:afford.reserve_after}. Months under the setting: {col:afford.short_months}. Verdict: {col:afford.verdict}.',
        'Decision of the board or director: ____________________________________________.'], ['Executive director', 'Finance chair'], NOTE),
    DOC('hire_doc', 'Hire Cost Sheet', 'Yearly cost of a hire', 'afford.item', [
        'Hire cost sheet of {set:org}, dated {today}. Role: {col:afford.item}.',
        'Monthly cost with employer costs {col:afford.monthly_cost}. Set-up cost {col:afford.setup_cost}. Full year {col:afford.yearly_cost}.',
        'Verdict from the forecast: {col:afford.verdict}. Earliest start number {col:afford.first_ok}.',
        'Check your local rules and ask your accountant what the employer costs include.'], ['Executive director', 'Chair'], NOTE),
    DOC('gap_doc', 'Funding Gap Note', 'Funding gap note for one forecast month', 'forecast.forecast_id', [
        'Funding gap note of {set:org}, dated {today}. Month: {col:forecast.month_name}.',
        'Free money {col:forecast.free_money}. Months of reserve {col:forecast.reserve_months} against the setting of {col:forecast.setting}. Free money above the setting {col:forecast.headroom}. Gap to the setting {col:forecast.gap}.',
        'The first month under the setting is {col:forecast.first_dip_name}. The lowest cash is {col:forecast.low_amount} in {col:forecast.low_month_name}.',
        'Steps to close the gap: ____________________________________________.'], ['Executive director', 'Finance chair'], NOTE),
    DOC('annual_doc', 'Annual Report Numbers Page', 'Annual report numbers page', 'annual_report.item', [
        'Annual report numbers of {set:org}, dated {today}. Item: {col:annual_report.item}.',
        'This year {col:annual_report.this_year}. Last year {col:annual_report.last_year}. Status {col:annual_report.status}. {col:annual_report.sentence}',
        'Money in this year {col:annual_report.money_in}. People served {col:annual_report.people}. Numbers ready {col:annual_report.items_ready}, numbers missing {col:annual_report.missing_n}.',
        'Check each number with your accountant before you print it.'], ['Executive director', 'Chair'], NOTE),
    DOC('pack_doc', 'Year-End Pack List', 'Year-end pack list for the accountant', 'cash.cash_id', [
        'Year-end pack list of {set:org}, dated {today}. Month on file: {col:cash.month_name}. Closing cash {col:cash.closing}. Bank lines not reconciled {col:cash.unrec_n}. Pay cost this year {col:cash.pay_year}.',
        'Papers to send: bank statements for every month; payroll summary; grant award letters and reports; list of pledges still open; restricted fund balances; list of equipment and assets; insurance policy list; minutes that approved the budget; gift totals tied to the bank; volunteer hours summary.',
        'Ask your accountant what your rules need and in which form.',
        'Sent by: ______________________  Date: ______________________'], ['Bookkeeper', 'Executive director'], NOTE),
    DOC('policy_doc', 'Reserve Policy Note', 'Reserve policy note for the board', 'cash.cash_id', [
        'Reserve policy note of {set:org}, dated {today}. The board holds free money of at least {col:cash.setting} months of average expense, a starting point the board sets for itself.',
        'Position in {col:cash.month_name}: free money {col:cash.free_money}, average monthly expense {col:cash.avg_monthly_expense}, months of reserve {col:cash.reserve_months}.',
        'If the reserve falls below the setting, the director tells the finance chair within a week and brings a plan to the next board meeting.',
        'Approved by the board on: ______________________'], ['Chair', 'Finance chair'], NOTE),
    DOC('board_doc', 'Board Finance Report', 'Board finance report for one month', 'income_source.month', [
        'Board finance report of {set:org}, dated {today}. Month: {col:income_source.month_name}.',
        'Money in {col:income_source.total} against a budget of {col:income_source.budget}. Money out {col:income_source.money_out}. Net {col:income_source.net}.',
        'This year so far: money in {col:income_source.money_in_year}, money out {col:income_source.money_out_year}. Income behind plan by {col:income_source.behind_by}.',
        'Questions for the finance committee: ____________________________________________.'], ['Finance chair', 'Executive director'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('close_chk', 'Monthly Close', 'cash', 'cash.month', [('Enter every gift and deposit', 0), ('Enter every expense and bill', 3), ('Reconcile the bank lines', 5), ('Check pledges due and received', 6), ('Check grant instalments received', 6), ('Close the month', 10), ('Send the month-end numbers to the accountant', 11), ('Update the cash forecast', 12)]),
    CHK('bva_chk', 'Budget Against Actual Review', 'budget_actual', 'budget_actual.month', [('Open Budget vs Actual for the month', 12), ('List the areas over budget', 13), ('Ask each program lead why', 15), ('Check that shared costs use the right rule', 16), ('Decide what to change next month', 18), ('Report to the finance committee', 25)]),
    CHK('fc_chk', 'Quarterly Forecast Update', 'forecast', 'forecast.month', [('Update gifts from the gift log run-rate', -40), ('Update pledges due', -38), ('Ask the development manager for grant timing', -35), ('Add events and one-off costs', -33), ('Update expenses', -30), ('Read the lowest cash month', -28), ('Send the forecast to the finance chair', -25)]),
    CHK('reserve_chk', 'Reserve Review', 'cash', 'cash.month', [('Check restricted and designated money', 10), ('Work out free money', 11), ('Divide by the average monthly expense', 12), ('Compare with the setting', 13), ('Tell the finance chair if below', 14), ('Plan the rebuild if needed', 21)]),
    CHK('build_chk', 'Annual Budget Build', 'budget', 'budget.month', [('Take this year\'s actual cost', -90), ('Apply your trend factor', -85), ('Ask each program lead for changes', -80), ('Plan income by line', -70), ('Test the scenarios', -60), ('Send the draft to the finance committee', -50), ('Board approves the budget', -30), ('Load the budget lines', -20)]),
    CHK('yearend_chk', 'Year-End Close', 'cash', 'cash.month', [('Reconcile every bank line', 5), ('Enter all gifts up to the last day', 7), ('Enter all expenses and accruals', 9), ('Check restricted fund balances', 12), ('Record releases from restriction', 14), ('Move any board-designated money', 18), ('Close the year', 25)]),
    CHK('pack_chk', 'Year-End Pack for Accountant', 'cash', 'cash.month', [('Print bank statements', 20), ('Prepare the payroll summary', 21), ('Collect grant letters and reports', 22), ('List open pledges', 23), ('List restricted fund balances', 24), ('List equipment and assets', 25), ('Send the pack', 28), ('Ask what else your rules need', 29)]),
    CHK('annual_chk', 'Annual Report Prep', 'cash', 'cash.month', [('Money in by source', 30), ('Money out by function', 31), ('People served from the programs sheet', 32), ('Volunteer hours and their value', 33), ('Donors and retention', 34), ('Write the sentences', 36), ('Check with the accountant', 40), ('Send to the board', 45)]),
    CHK('hire_chk', 'Hire Decision', 'afford', 'afford.decide_on', [('Write down the role and the monthly cost', 0), ('Run Can We Afford This', 1), ('Check the reserve in every forecast month', 2), ('Check grant timing', 3), ('Ask the finance chair', 5), ('Board agrees', 14), ('Post the role', 15)]),
    CHK('program_chk', 'New Program Funding Check', 'afford', 'afford.decide_on', [('List the costs and the set-up', 0), ('Name the funding for each month', 2), ('Check the forecast and the reserve', 3), ('Check funder rules for restricted money', 5), ('Plan who runs it', 7), ('Board approves', 14)]),
    CHK('tie_chk', 'Bank Tie-out Steps', 'bank', 'bank.date', [('Compare the bank balance with Cash by Month', 1), ('List lines not reconciled', 2), ('Find each missing record', 3), ('Fix or ask the bank contact', 5), ('Mark the lines reconciled', 6), ('Record the date done', 7)]),
    CHK('founder_chk', 'Founder First Budget', 'budget', 'budget.month', [('List your programs and give each one budget line', 0), ('Add management and fundraising lines', 3), ('Type the monthly budget', 7), ('Type the expenses as they happen', 14), ('Compare budget with actual each month', 30), ('Set aside a first reserve', 60), ('Ask your accountant what your rules need', 75)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
ED, FIN, BMN, DEV, PMN, BKN = fn(OWNER), fn(D.TREAS['name']).replace('Dr.', 'Dr'), fn(D.VICE['name']), fn(DEV_MANAGER), fn(D.TEAMID['NP-03']['name']), fn(D.TEAMID['NP-08']['name'])
ACC, BNK, BRK, FUN = fn(D.TEAMID['NP-09']['name']), fn(D.TEAMID['NP-10']['name']), fn(D.TEAMID['NP-11']['name']), fn(D.TEAMID['NP-15']['name'])
VOLN, DON = D.VOL_FIRST, D.DONOR_FIRST
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('ed_over', 'Executive director: over budget', 'budget_actual', 'budget_actual.ed_phone', 'Hello %s, budget against actual for {month_name}: {area} is over by {over_by}. {org}' % ED),
    M('ed_cash', 'Executive director: cash is lowest', 'forecast', 'forecast.ed_phone', 'Hello %s, cash is lowest in {low_month_name} at {low_amount}. {org}' % ED),
    M('ed_reserve', 'Executive director: months of reserve', 'cash', 'cash.ed_phone', 'Hello %s, the reserve is {reserve_months} months against the setting of {setting}. {org}' % ED),
    M('ed_scen', 'Executive director: a scenario result', 'scenarios', 'scenarios.ed_phone', 'Hello %s, the scenario {scenario} leaves {reserve_months} months of reserve, your estimate. {org}' % ED),
    M('ed_hire', 'Executive director: afford this', 'afford', 'afford.ed_phone', 'Hello %s, {item} at {monthly_cost} a month: {verdict}. {org}' % ED),
    M('ed_report', 'Executive director: report numbers', 'annual_report', 'annual_report.ed_phone', 'Hello %s, {items_ready} annual report numbers are ready and {missing_n} are missing. {org}' % ED),
    M('fin_fc', 'Finance chair: the cash forecast', 'forecast', 'forecast.fin_phone', 'Hello %s, the cash forecast for {month_name} is attached. {org}' % FIN),
    M('fin_dip', 'Finance chair: reserve falls below', 'forecast', 'forecast.fin_phone', 'Hello %s, the reserve falls below {setting} months in {first_dip_name}. {org}' % FIN),
    M('fin_fr', 'Finance chair: fundraising share', 'functional', 'functional.fin_phone', 'Hello %s, the fundraising share is {fr_share_year} against {fr_share_last} last year. {org}' % FIN),
    M('fin_budget', 'Finance chair: next year budget', 'functional', 'functional.fin_phone', 'Hello %s, the budget for next year is {next_budget}, your estimate. {org}' % FIN),
    M('bm_year', 'Board member: money in and out', 'income_source', 'income_source.bm_phone', 'Hello %s, money in for the year is {money_in_year} and money out is {money_out_year}. {org}' % BMN),
    M('bm_free', 'Board member: free money', 'cash', 'cash.bm_phone', 'Hello %s, free money is {free_money}, {reserve_months} months of reserve. {org}' % BMN),
    M('bm_pack', 'Board member: the finance page', 'cash', 'cash.bm_phone', 'Hello %s, the board pack finance page for {month_name} is ready. {org}' % BMN),
    M('dev_gifts', 'Development manager: expected gifts', 'forecast', 'forecast.dev_phone', 'Hello %s, expected gifts for {month_name} are {gifts}. {org}' % DEV),
    M('dev_behind', 'Development manager: behind plan', 'income_source', 'income_source.dev_phone', 'Hello %s, income is behind plan by {behind_by} this year. {org}' % DEV),
    M('dev_grants', 'Development manager: grant timing', 'forecast', 'forecast.dev_phone', 'Hello %s, the forecast needs your grant timing for {month_name}. {org}' % DEV),
    M('pm_spent', 'Program manager: share of budget spent', 'budget_actual', 'budget_actual.pm_phone', 'Hello %s, {area} spent {share_used} of its budget in {month_name}. {org}' % PMN),
    M('pm_shared', 'Program manager: shared cost', 'budget_actual', 'budget_actual.pm_phone', 'Hello %s, the shared cost for {area} in {month_name} is {shared_part}. {org}' % PMN),
    M('pm_confirm', 'Program manager: confirm budget lines', 'budget_actual', 'budget_actual.pm_phone', 'Hello %s, please confirm your budget lines for next year by {confirm_by}. {org}' % PMN),
    M('bk_close', 'Bookkeeper: close the month', 'cash', 'cash.bk_phone', 'Hello %s, please close {month_name} by {close_by}. {org}' % BKN),
    M('bk_unrec', 'Bookkeeper: bank lines not reconciled', 'cash', 'cash.bk_phone', 'Hello %s, {unrec_n} bank lines are not reconciled. {org}' % BKN),
    M('bk_pledges', 'Bookkeeper: enter pledges due', 'forecast', 'forecast.bk_phone', 'Hello %s, please enter pledges due in {month_name}: {pledges_due}. {org}' % BKN),
    M('bk_rule', 'Bookkeeper: a shared cost rule changes', 'expense_categories', 'expense_categories.bk_phone', 'Hello %s, the shared cost rule for {category} changes on {change_on}. {org}' % BKN),
    M('bk_budget', 'Bookkeeper: budget is loaded', 'budget_actual', 'budget_actual.bk_phone', 'Hello %s, the budget for {month_name} is loaded. {org}' % BKN),
    M('acc_month', 'Accountant: month-end numbers', 'cash', 'cash.acc_phone', 'Hello %s, the month-end numbers for {month_name} are attached. {org}' % ACC),
    M('acc_pack', 'Accountant: year-end pack list', 'annual_report', 'annual_report.acc_phone', 'Hello %s, the year-end pack list is attached; {items_ready} report numbers are ready. {org}' % ACC),
    M('acc_scen', 'Accountant: a scenario to test', 'scenarios', 'scenarios.acc_phone', 'Hello %s, we are testing a scenario of {scenario}. What should we check? {org}' % ACC),
    M('bank_bal', 'Bank contact: confirm the balance', 'cash', 'cash.bank_phone', 'Hello %s, please confirm the balance on {balance_date}. {org}' % BNK),
    M('broker', 'Insurance broker: payroll totals', 'cash', 'cash.broker_phone', 'Hello %s, payroll and cost totals for the year are {pay_year}. {org}' % BRK),
    M('funder', 'Funder: budget against actual', 'annual_report', 'annual_report.funder_phone', 'Hello %s, our budget against actual for {grant_id} is attached. {org}' % FUN),
    M('staff_time', 'Staff member: confirm your time', 'pay', 'pay.phone', 'Hello {staff}, your time for {month_name} is {time_pct} of a full month. Please confirm. {org}'),
    M('staff_hours', 'Staff member: your hours', 'pay', 'pay.phone', 'Hello {staff}, your hours for {month_name} are {hours}. {org}'),
    M('vol_cash', 'Volunteer treasurer: check the cash page', 'cash', 'cash.vol_phone', 'Hello %s, please check the cash page for {month_name}. {org}' % VOLN),
    M('donor', 'Donor: our yearly numbers', 'annual_report', 'annual_report.donor_phone', 'Hello %s, our yearly numbers are ready: money in {money_in}, people served {people}. {org}' % DON),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def INSUM(c, a, b=None): return 'SUMIFS(%s,%s,">="&%s%s)' % (R('income_source', c), R('income_source', 'month'), a, (',%s,"<="&%s' % (R('income_source', 'month'), b)) if b else '')
LY1, LY12 = 'DATE(YEAR({today})-1,1,1)', 'DATE(YEAR({today})-1,12,1)'
OUTSUM = lambda a, b=None: 'SUMIFS(%s,%s,">="&%s%s)' % (R('expenses', 'amount'), R('expenses', 'date'), a, (',%s,"<="&%s' % (R('expenses', 'date'), b)) if b else '')
LASTCOMP = lambda c, t='income_source': 'SUMIFS(%s,%s,">="&%s,%s,"<"&%s)' % (R(t, c), R(t, 'month'), JAN1, R(t, 'month'), CURM)
CAPM = 'MAX(0,ROUND((%s-{set:reserve_months}*%s)/12,0))' % (NOWROW('free_money'), NOWROW('avg_monthly_expense'))
kpis = [
    KPI('Money in this year', INSUM('total', JAN1), 'money'), KPI('Money out this year', OUTSUM(JAN1), 'money'), KPI('Net this year', '%s-%s' % (INSUM('total', JAN1), OUTSUM(JAN1)), 'money'),
    KPI('Money in last year', INSUM('total', LY1, LY12), 'money'), KPI('Money out last year', OUTSUM(LY1, 'DATE(YEAR({today})-1,12,31)'), 'money'),
    KPI('Money in against budget', 'IFERROR(%s/%s,0)' % (LASTCOMP('total'), LASTCOMP('budget')), 'pct'), KPI('Money out against budget', 'IFERROR(%s/%s,0)' % (LASTCOMP('total', 'functional'), LASTCOMP('budget', 'functional')), 'pct'),
    KPI('Program share of cost', SH('program', THIS), 'pct'), KPI('Management share of cost', SH('management', THIS), 'pct'), KPI('Fundraising share of cost', SH('fundraising', THIS), 'pct'), KPI('Fundraising share last year', SH('fundraising', LAST), 'pct'),
    KPI('Largest cost area over budget', 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (R('budget_actual', 'area'), R('budget_actual', 'difference'), R('budget_actual', 'difference')), 'text'),
    KPI('Cash now', NOWROW('closing'), 'money'), KPI('Restricted money now', NOWROW('restricted'), 'money'), KPI('Designated money now', NOWROW('designated'), 'money'), KPI('Free money now', NOWROW('free_money'), 'money'),
    KPI('Average monthly expense last 12 months', NOWROW('avg_monthly_expense'), 'money'), KPI('Months of reserve now', NOWROW('reserve_months'), 'num'), KPI('Months of reserve lowest next 12', 'MIN(%s)' % FC('reserve_months'), 'num'),
    KPI('Lowest cash month', 'INDEX(%s,MATCH(MIN(%s),%s,0))' % (FC('month'), FC('closing'), FC('closing')), 'date'), KPI('Lowest cash amount', 'MIN(%s)' % FC('closing'), 'money'),
    KPI('Pledges due next 90 days', 'SUMIFS(%s,%s,"<="&({today}+90))' % (FC('pledges_due'), FC('month')), 'money'), KPI('Grant instalments due next 6 months', 'SUMIFS(%s,%s,"<="&EDATE({today},6))' % (FC('grants'), FC('month')), 'money'),
    KPI('Forecast net next 12 months', 'SUM(%s)' % FC('net'), 'money'),
    KPI('Biggest donor share of income', 'IFERROR(%s/%s,0)' % (FI('Biggest donor giving a year'), INSUM('total', 'EDATE(%s,-12)' % CURM, 'EDATE(%s,-1)' % CURM)), 'pct'),
    KPI('Scenario worst case reserve months', 'MIN(%s)' % R('scenarios', 'reserve_months'), 'num'), KPI('Hire capacity a month', CAPM, 'money'),
    KPI('Unreconciled bank lines', 'COUNTIFS(%s,%s,%s,"<>")' % (R('bank', 'reconciled'), NO, R('bank', 'bank_id')), 'int'), KPI('Pay cost this month', 'SUMIFS(%s,%s,%s)' % (R('pay', 'total'), R('pay', 'month'), CURM), 'money'),
    KPI('Annual report items missing', 'COUNTIFS(%s,%s,%s,"<>")' % (R('annual_report', 'status'), v('Missing'), R('annual_report', 'item')), 'int'),
]
assert len(kpis) == 30
dashboard = {"title": "Budget and Cash Dashboard", "kpis": kpis,
    "monthly": {"title": "Money in, money out and net", "date": "income_source.month", "series": [
        {"label": "Money in", "sum": "income_source.total", "date": "income_source.month"}, {"label": "Money out", "sum": "income_source.money_out", "date": "income_source.month"},
        {"label": "Net", "sum": "income_source.net", "date": "income_source.month"}]},
    "breakdowns": [{"title": "Expenses by category", "by": "expenses.category", "value": "expenses.amount", "agg": "sum"}, {"title": "Expenses by function", "by": "expenses.function", "value": "expenses.amount", "agg": "sum"},
                   {"title": "Expenses by program", "by": "expenses.program", "value": "expenses.amount", "agg": "sum"}, {"title": "Bank money out by kind", "by": "bank.kind", "value": "bank.money_out", "agg": "sum"}]}

def W(c, o, v_): return (c, o, v_)
insights = {"filters": [{"label": "Fund", "list": "fund"}, {"label": "Expense category", "list": "category"}, {"label": "Budget area", "list": "area"}],
    "gauges": [
        {"title": "Months of reserve against the setting", "num": AGG('sum', 'cash', 'cash.reserve_now'), "den": AGG('sum', 'cash', 'cash.setting_now')},
        {"title": "Program share of cost this year", "num": AGG('sum', 'functional', 'functional.program', where=[W('period', '=', THIS)]), "den": AGG('sum', 'functional', 'functional.total', where=[W('period', '=', THIS)])},
        {"title": "Money in against budget", "num": AGG('sum', 'income_source', 'income_source.total', where=[W('period', '=', THIS), W('complete', '=', 1)]), "den": AGG('sum', 'income_source', 'income_source.budget', where=[W('period', '=', THIS), W('complete', '=', 1)])},
        {"title": "Money out against budget", "num": AGG('sum', 'functional', 'functional.total', where=[W('period', '=', THIS), W('complete', '=', 1)]), "den": AGG('sum', 'functional', 'functional.budget', where=[W('period', '=', THIS), W('complete', '=', 1)])},
        {"title": "Fundraising cost per dollar, this year", "num": AGG('sum', 'functional', 'functional.fundraising', where=[W('period', '=', THIS)]), "den": AGG('sum', 'income_source', 'income_source.total', where=[W('period', '=', THIS)])},
        {"title": "Bank lines reconciled", "num": AGG('count', 'bank', where=[W('reconciled', '=', YES)]), "den": AGG('count', 'bank')}],
    "charts": [
        CHART('Money in per month', 'column', 'month', [AGG('sum', 'income_source', 'income_source.total', date='income_source.month', label='Money in')]),
        CHART('Money out per month', 'column', 'month', [AGG('sum', 'expenses', 'expenses.amount', date='expenses.date', label='Money out')]),
        CHART('Net per month', 'column', 'month', [AGG('sum', 'income_source', 'income_source.net', date='income_source.month', label='Net')]),
        CHART('Income by source per month', 'stacked', 'month', [AGG('sum', 'income_source', 'income_source.%s' % c, date='income_source.month', label=l) for c, l in (('gifts', 'Gifts'), ('grants', 'Grants'), ('events', 'Events'), ('dues', 'Dues'))]),
        CHART('Money in by source and year', 'bar', 'money_by_source.source', [AGG('sum', 'money_by_source', 'money_by_source.amount', where=[W('period', '=', tok('yr', p))], label=p) for p in ('This year', 'Last year', 'Two years ago')]),
        CHART('Expenses by category', 'bar', 'expenses.category', [AGG('sum', 'expenses', 'expenses.amount', label='Expenses')]),
        CHART('Expenses by function', 'bar', 'expenses.function', [AGG('sum', 'expenses', 'expenses.amount', label='Expenses')]),
        CHART('Expenses by program', 'bar', 'expenses.program', [AGG('sum', 'expenses', 'expenses.amount', label='Expenses')]),
        CHART('Budget and actual by area', 'bar', 'budget_actual.area', [AGG('sum', 'budget_actual', 'budget_actual.budget', label='Budget'), AGG('sum', 'budget_actual', 'budget_actual.actual', label='Actual')]),
        CHART('Program share of cost per month', 'line', 'month', [AGG('avg', 'functional', 'functional.program_share', date='functional.month', label='Program share')]),
        CHART('Fundraising share per month', 'line', 'month', [AGG('avg', 'functional', 'functional.fundraising_share', date='functional.month', label='Fundraising share')]),
        CHART('Cash closing per month', 'line', 'month', [AGG('sum', 'cash', 'cash.closing', date='cash.month', label='Closing cash')]),
        CHART('Free money per month', 'line', 'month', [AGG('sum', 'cash', 'cash.free_money', date='cash.month', label='Free money')]),
        CHART('Months of reserve per month', 'line', 'month', [AGG('avg', 'cash', 'cash.reserve_months', date='cash.month', label='Months of reserve')]),
        CHART('Forecast closing cash', 'line', 'forecast.step', [AGG('sum', 'forecast', 'forecast.closing', label='Closing cash')]),
        CHART('Forecast gifts per month', 'column', 'forecast.step', [AGG('sum', 'forecast', 'forecast.gifts', label='Gifts')]),
        CHART('Forecast expenses per month', 'column', 'forecast.step', [AGG('sum', 'forecast', 'forecast.expenses', label='Expenses')]),
        CHART('Forecast pledges and grants per month', 'column', 'forecast.step', [AGG('sum', 'forecast', 'forecast.pledges_due', label='Pledges due'), AGG('sum', 'forecast', 'forecast.grants', label='Grants')]),
        CHART('Scenario months of reserve', 'bar', 'scenarios.scenario', [AGG('avg', 'scenarios', 'scenarios.reserve_months', label='Months of reserve')]),
        CHART('Pay cost per month', 'column', 'month', [AGG('sum', 'pay', 'pay.total', date='pay.month', label='Pay cost')]),
        CHART('Pay cost by role', 'bar', 'pay.role', [AGG('sum', 'pay', 'pay.total', label='Pay cost')]),
        CHART('Bank money in and out per month', 'column', 'month', [AGG('sum', 'bank', 'bank.money_in', date='bank.date', label='Money in'), AGG('sum', 'bank', 'bank.money_out', date='bank.date', label='Money out')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Cash forecast", "why": "twelve months of cash from gifts, recurring gifts, pledges, grant instalments, event net and expenses, with the lowest month named", "where": "Cash Forecast Tool"},
    {"name": "Reserve date finder", "why": "the first month free money falls below your reserve setting, or a clear answer that it does not within 12 months", "where": "Reserve Date Finder"},
    {"name": "Reserve rebuild plan", "why": "the monthly saving that brings you back to the setting in the months you choose", "where": "Reserve Rebuild Plan"},
    {"name": "Can-we-afford-this tool", "why": "a new hire or program tested month by month against the forecast, with the earliest month it fits", "where": "Can We Afford This"},
    {"name": "Scenario tester", "why": "lose the biggest donor, lose a grant, donors fall, recurring grows or costs rise, each with year-end cash and months of reserve", "where": "Scenario Tester"},
    {"name": "Shared cost allocator", "why": "each shared cost split to programs, management and fundraising by staff time, floor area or headcount, on your own rule", "where": "Shared Cost Allocator"},
    {"name": "Annual report numbers builder", "why": "money in, money out, people served, volunteer value and donors as plain sentences, with the missing items named", "where": "Annual Report Numbers Builder"},
    {"name": "Budget against actual by area", "why": "every program, management and fundraising line against its actual cost, with the largest overspend named", "where": "Budget vs Actual Tool"},
    {"name": "Fundraising share alert", "why": "fundraising cost over total cost against your own last year, with the cost to raise one dollar", "where": "Fundraising Share Alert"},
    {"name": "Bank tie-out", "why": "opening cash plus bank money in less money out against closing cash, with the lines not reconciled counted", "where": "Bank Tie-out"}]
competitors = [
    {"what": "donor-management software", "lacks": "tracks gifts but has no functional budget, no shared cost rules, no cash forecast and no months of reserve"},
    {"what": "generic nonprofit budget templates", "lacks": "give a grid of numbers but never split shared costs by a rule, compare with your own history or warn when fundraising cost rises"},
    {"what": "single-purpose cash flow spreadsheets", "lacks": "list months but have no restricted and designated money, no reserve date finder and no scenario tests"},
    {"what": "nonprofit accounting add-ons", "lacks": "cost a monthly fee and give no afford-this tool, no reserve rebuild plan and no annual report sentences"}]
guide = [
    'Open Start and type your organization name, the months of reserve you want (a starting point of 3), the cost to raise one dollar you aim for (a starting point of 0.25) and your floor shares.',
    'Type the monthly budget for each area on Budget and the planned money in on Income Budget; a founder with volunteers can use one line per program.',
    'Type every expense on Expenses with its category, program, function and fund; set the shares and the rule of each category on Expense Categories.',
    'Read Budget vs Actual and Functional Split: each shared cost is split by the rule you set and the shares fill in by themselves.',
    'Type the gifts, grants, events and dues of each month on Income by Source; Money in by Source and the dashboard fill in.',
    'Type opening cash, receipts, payments, restricted and designated money on Cash by Month; free money and months of reserve fill in.',
    'Enter your 12-month plan on Cash Forecast and the changes on Forecast Inputs; Lowest Cash Month names the tightest month.',
    'Test ideas on Scenarios and Afford This, and use Reserve Date Finder and Reserve Rebuild Plan when the reserve falls.',
    'Type the pay of each staff member on Pay and Staff Cost, and the bank lines on Bank Lines, ticking each one you have reconciled.',
    'Type people served, volunteer hours, donors and retention on Annual Report Numbers; the sentences fill in.',
    f'Use the {len(tools)} tools for decisions: budget, shares, forecast, reserve, hires, scenarios, bank tie-out and the year-end pack.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the numbers written in. A founder with volunteers and no staff can use the same sheets with one program and one fund.']
listing = {"title": "Nonprofit Budget and Cash Flow Excel Template: Functional Budget, Cash Forecast, Months of Reserve, Scenarios, Annual Report",
    "headline": "Budget, cash forecast, reserve months and annual report numbers",
    "tags": ["nonprofit budget", "cash flow forecast", "functional budget", "months of reserve", "operating reserve", "budget vs actual", "nonprofit excel", "scenario tests", "annual report", "cost allocation", "charity finance", "board finance report", "restricted funds"],
    "description": ("Run the money of a small community nonprofit in one Excel workbook. Built for an executive director, a finance chair and a bookkeeper who must know whether the organization is on budget, when cash is lowest and how many months of reserve are left. "
        "Budget and Expenses hold the monthly budget by program, management and fundraising and every expense with its category, function and fund. Expense Categories sets the share of each shared cost by a visible rule (staff time, floor area or headcount), and Budget vs Actual, Functional Split and Allocation Rules show who carries each cost.\n\n"
        "Income by Source, Cash by Month and Bank Lines show money in, money out, restricted and designated money, free money and months of reserve against the starting point of 3 months. Cash Forecast builds twelve months from gifts, recurring gifts, pledges due, grant instalments, event net and expenses, and Lowest Cash Month names the tightest month. Scenarios test losing the biggest donor or a grant, donors falling, recurring growing and costs rising. "
        f"{len(tools)} tools answer the weekly questions: budget against actual, shared cost allocator, fundraising share alert, budget builder, cash forecast, reserve date finder, reserve rebuild plan, can-we-afford-this, hire cost, scenario tester, bank tie-out and the annual report numbers builder. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to the director, finance chair, bookkeeper and accountant.\n\n"
        "This is part eight of the Nonprofit Organization suite. It works in Excel and Google Sheets, has no macros and no subscription, and comes with a demo copy full of sample data. A founder with volunteers can use it with one budget line per program. Forecasts and verdicts are your own estimate. It helps you keep records and is not accounting or legal advice; ask your accountant what you need."),
    "features": ["Budget against actual by area", "Functional budget with shared cost rules", "Cash forecast for 12 months", "Free money and months of reserve", "Reserve date finder and rebuild plan", "Can-we-afford-this tool for hires and programs",
                 "Scenario tests with year-end cash", "Annual report numbers in plain sentences", f"{len(tools)} decision tools", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "Works for a founder with one budget line per program"]}
for _t in tables: _t['rows'] = max(50, _t['rows'], len(_t['demo']))
s = spec(id=f'{SUITE}-p8', slug='nonprofit-budget', profession='Nonprofit Organization', name='Budget, Cash and Annual Report',
         tagline='Budget, cash forecast, reserve months and annual report numbers', price_usd=29,
         colors={"primary": "#22577A", "accent": "#F2A541"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 8, "of": 8, "focus": "Budget, cash and annual report"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'np8.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'name', len(s['name']))
