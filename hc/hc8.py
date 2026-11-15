"""Home care agency suite - part 8: Owner Money and Business Health."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib as _lib
from hc8_lists import *
from hc8_tables import settings, tables, CA, STAFF, STAFFN, M0, M1, WPM, PNM
from hc8_tools import tools

SUITE = 'fx-20261115-home-care-agency'
NOTE = "Sample wording: adapt it to your own agency; check your own local rules and confirm tax, pay and insurance matters with your adviser."
def F(*p): return [FV(a, b) for a, b in p]
YES = '{list:yesno.yes}'

forms = [
 FORM('month_close', 'Month-end Close Sheet', 'Month-end close with margin, overhead and profit', 'pnl.row_id', F(
  ('Month', 'pnl.month'), ('Revenue', 'pnl.revenue'), ('Billed hours', 'pnl.billed_hours'), ('Caregiver pay', 'pnl.caregiver_pay'), ('Overtime pay', 'pnl.overtime_pay'), ('Travel and mileage', 'pnl.travel_mileage'),
  ('Payroll burden', 'pnl.payroll_burden'), ('Direct cost', 'pnl.direct_cost'), ('Gross margin', 'pnl.gross_margin'), ('Gross margin share', 'pnl.gross_margin_share'), ('Overhead', 'pnl.overhead'), ('Overhead share', 'pnl.overhead_share'),
  ('Profit', 'pnl.profit'), ('Profit share', 'pnl.profit_share'), ('Pay cost ratio', 'pnl.pay_cost_ratio'), ('Gross margin per hour', 'pnl.margin_hour'), ('Weekly hours', 'pnl.weekly_hours'), ('Break-even weekly hours', 'pnl.breakeven_hours'))),
 FORM('budget_line', 'Budget Line Sheet', 'Budget line against last month\'s actual', 'budget.category', F(
  ('Category', 'budget.category'), ('Monthly budget', 'budget.budget'), ('Next review', 'budget.review_on'), ('Actual last month', 'budget.actual_last_month'), ('Variance (plus is over)', 'budget.variance'),
  ('Variance share', 'budget.variance_share'), ('Budget check', 'budget.flag'), ('Budget for the quarter', 'budget.quarter_budget'))),
 FORM('expense_sheet', 'Expense Sheet', 'Expense with the month total of its category', 'expenses.expense_id', F(
  ('Date', 'expenses.date'), ('Month', 'expenses.month'), ('Category', 'expenses.category'), ('Payee', 'expenses.payee'), ('Amount', 'expenses.amount')) + [
  FF('Spent in this category in the month', 'SUMIFS({range:expenses.amount},{range:expenses.category},INDEX({range:expenses.category},MATCH({pick},{range:expenses.expense_id},0)),{range:expenses.month},INDEX({range:expenses.month},MATCH({pick},{range:expenses.expense_id},0)))', 'money'),
  FF('Payments to this payee, all months', 'COUNTIFS({range:expenses.payee},INDEX({range:expenses.payee},MATCH({pick},{range:expenses.expense_id},0)))', 'int')]),
 FORM('draw_sheet', 'Owner Draw Sheet', 'Owner draw with running total and share of profit', 'draws.draw_id', F(
  ('Month', 'draws.month'), ('Draw', 'draws.draw'), ('Taken on', 'draws.taken_on'), ('Running total', 'draws.cumulative'), ('Profit of the month', 'draws.profit'), ('Draw as a share of profit', 'draws.draw_share'), ('Draw check', 'draws.draw_check'))),
 FORM('tax_sheet', 'Tax Set-aside Sheet', 'Tax set-aside for the month (confirm with your adviser)', 'tax.tax_id', F(
  ('Month', 'tax.month'), ('Set-aside share', 'tax.set_aside_pct'), ('Status', 'tax.status'), ('Moved on', 'tax.moved_on'), ('Profit', 'tax.profit'), ('Set-aside', 'tax.set_aside'), ('Running total', 'tax.cumulative'))),
 FORM('cash_check', 'Cash Check Sheet', 'Cash check for a month: in, out and above the floor', 'cash.row_id', F(
  ('Month', 'cash.month'), ('Opening cash', 'cash.opening'), ('Cash in', 'cash.cash_in'), ('Pay runs', 'cash.pay_runs'), ('Expenses', 'cash.expenses'), ('Owner draw', 'cash.owner_draw'), ('Tax set-aside', 'cash.tax_set_aside'),
  ('Cash out', 'cash.cash_out'), ('Closing cash', 'cash.closing'), ('Cash floor', 'cash.cash_floor'), ('Change in cash', 'cash.change'), ('Cash above the floor', 'cash.above_floor'), ('Safe owner draw', 'cash.safe_draw'))),
 FORM('receipt_sheet', 'Payer Receipt Sheet', 'Expected receipt with the payer-pays-later slider', 'receipts.receipt_id', F(
  ('Week number', 'receipts.week_no'), ('Week starts', 'receipts.starts_on'), ('Source', 'receipts.source'), ('Amount', 'receipts.amount'), ('Usual days to pay', 'receipts.usual_days'), ('Arrives in week (slider)', 'receipts.arrives_week'),
  ('Amount that moves later', 'receipts.delayed_amount'), ('Pushed beyond week 13', 'receipts.pushed_out'))),
 FORM('scenario_sheet', 'Scenario Sheet', 'Scenario with break-even hours and profit', 'breakeven.sc_id', F(
  ('Scenario', 'breakeven.scenario'), ('Rate rise', 'breakeven.rate_rise'), ('Hours lost', 'breakeven.hours_lost'), ('Office help a month', 'breakeven.scheduler_cost'), ('Margin per hour after', 'breakeven.new_margin'),
  ('Weekly hours after', 'breakeven.hours_after'), ('Break-even weekly hours', 'breakeven.breakeven_hours'), ('Profit a month', 'breakeven.profit_month'), ('Result', 'breakeven.verdict'))),
 FORM('hours_sheet', 'Hours Target Sheet', 'Hours target plan with the hours gap', 'hplan.plan_id', F(
  ('Plan', 'hplan.plan'), ('Weekly hours', 'hplan.weekly_hours'), ('Margin per hour', 'hplan.margin_hour'), ('Overhead a month', 'hplan.overhead'), ('Owner draw a month', 'hplan.draw'), ('Profit after the draw', 'hplan.profit_after_draw'),
  ('Weekly hours needed', 'hplan.needed_hours'), ('Hours gap (plus is short)', 'hplan.hours_gap'), ('Caregivers to add', 'hplan.caregivers_needed'), ('Hire by', 'hplan.hire_by'))),
 FORM('health_review', 'Health Review Sheet', 'Health review: six measures, points and the worst item', 'health.hl_id', F(
  ('Month', 'health.month'), ('Gross margin per hour', 'health.margin_hour'), ('Overtime share', 'health.overtime_share'), ('Fill rate', 'health.fill_rate'), ('Days to be paid', 'health.days_to_pay'), ('Caregiver turnover', 'health.turnover_rate'),
  ('Weeks of cash cover', 'health.cover_weeks'), ('Points: margin', 'health.p_margin'), ('Points: overtime', 'health.p_overtime'), ('Points: fill rate', 'health.p_fill'), ('Points: days to be paid', 'health.p_days'),
  ('Points: turnover', 'health.p_turnover'), ('Points: cash cover', 'health.p_cover'), ('Health score', 'health.score'), ('Worst item', 'health.worst'))),
 FORM('overhead_review', 'Overhead Review Sheet', 'Overhead review by line', 'overhead.row_id', F(
  ('Month', 'overhead.month'), ('Rent', 'overhead.rent'), ('Office payroll', 'overhead.office_payroll'), ('Field supervisor pay', 'overhead.field_pay'), ('Software and phones', 'overhead.software_phones'), ('Insurance', 'overhead.insurance'),
  ('Marketing and recruiting', 'overhead.marketing_recruiting'), ('Other lines', 'overhead.other'), ('Total overhead', 'overhead.total'), ('Share of revenue', 'overhead.share_of_revenue'))),
 FORM('startup_sheet', 'Start-up Setup Sheet', 'Start-up setup: one page of the suite', 'startup.page_id', F(
  ('Page', 'startup.page'), ('Part', 'startup.part'), ('Used by a one-person agency', 'startup.one_person'), ('Used from caregivers', 'startup.from_caregivers'), ('Note', 'startup.note')) + [
  FF('Pages a one-person agency uses', 'COUNTIFS({range:startup.one_person},%s)' % YES, 'int'), FF('Pages that wait until you grow', 'COUNTA({range:startup.page})-COUNTIFS({range:startup.one_person},%s)' % YES, 'int')]),
]
assert len(forms) == 12

def D_(k, sheet, title, pick, paras, sign): return DOC(k, sheet, title, pick, paras, sign, NOTE)
documents = [
 D_('pl_doc', 'Profit and Loss Statement', 'Monthly profit and loss statement', 'pnl.row_id', [
  'Profit and loss statement of {set:company} for {col:pnl.month}, dated {today}.', 'Revenue {col:pnl.revenue} from {col:pnl.billed_hours} billed hours. Caregiver pay {col:pnl.caregiver_pay}, overtime pay {col:pnl.overtime_pay}, travel and mileage {col:pnl.travel_mileage}, payroll burden {col:pnl.payroll_burden}: direct cost {col:pnl.direct_cost}.',
  'Gross margin {col:pnl.gross_margin} ({col:pnl.gross_margin_share} of revenue, {col:pnl.margin_hour} per billed hour). Overhead {col:pnl.overhead} ({col:pnl.overhead_share} of revenue).', 'Profit {col:pnl.profit} ({col:pnl.profit_share} of revenue). Pay cost ratio {col:pnl.pay_cost_ratio} against a ceiling of {set:payroll_ratio_ceiling}.'], ['Owner-director', 'Office manager']),
 D_('dash_doc', 'Owner Dashboard One-pager', 'Owner dashboard one-pager with the health score', 'pnl.row_id', [
  'Owner dashboard of {set:company} for {col:pnl.month}, dated {today}.', 'Agency health score {col:pnl.health_score} out of 100. The worst item is {col:pnl.worst_item}. Healthy is {set:health_healthy_score} or more, Watch is {set:health_watch_score} or more.',
  'Revenue {col:pnl.revenue}, profit {col:pnl.profit} ({col:pnl.profit_share} of revenue, target {set:profit_target}). Gross margin per hour {col:pnl.margin_hour}.',
  'Weekly hours {col:pnl.weekly_hours} against break-even at {col:pnl.breakeven_hours}. Months to the office help marker: {col:pnl.months_to_marker}.'], ['Owner-director']),
 D_('cash_doc', '13-Week Cash Flow Report', '13-week cash flow forecast for one week and scenario', 'forecast.row_id', [
  '13-week cash flow forecast of {set:company}, dated {today}. Scenario {col:forecast.scenario}, {col:forecast.week} starting {col:forecast.starts_on}.', 'Private pay receipts {col:forecast.private_receipts}, payer receipts {col:forecast.payer_receipts}. Pay run {col:forecast.pay_run}, overhead {col:forecast.overhead}, owner draw {col:forecast.owner_draw}, tax set-aside {col:forecast.tax_set_aside} (confirm with your adviser).',
  'Net cash {col:forecast.net}. Closing balance {col:forecast.closing} against a floor of {set:cash_floor}: {col:forecast.floor_check}. Weeks of cover {col:forecast.weeks_cover}.', 'If third-party payers pay {set:payer_delay_days} days later, the closing balance is {col:forecast.closing_late}.'], ['Owner-director', 'Office manager']),
 D_('budget_doc', 'Budget Against Actual Report', 'Budget against actual report for one expense line', 'budget.category', [
  'Budget report of {set:company}, dated {today}. Line: {col:budget.category}.', 'Monthly budget {col:budget.budget}. Actual last month {col:budget.actual_last_month}. Variance {col:budget.variance} ({col:budget.variance_share}). Check: {col:budget.flag}.',
  'The budget for the quarter is {col:budget.quarter_budget}. Next review on {col:budget.review_on}. A line is flagged when it is more than {set:budget_tolerance} over budget.'], ['Owner-director', 'Office manager']),
 D_('pay_doc', 'Owner Pay and Tax Note', 'Owner pay and tax set-aside note', 'draws.draw_id', [
  'Owner pay note of {set:company}, dated {today}. Month {col:draws.month}.', 'Owner draw {col:draws.draw}, taken on {col:draws.taken_on}. Running total of draws {col:draws.cumulative}. Profit of the month {col:draws.profit}, so the draw is {col:draws.draw_share} of profit ({col:draws.draw_check}).',
  'The tax set-aside is planned at {set:tax_set_aside_pct} of profit. This is a sample rate: confirm the rate, the amounts and the dates with your adviser and check your own local rules.'], ['Owner-director', 'Accountant']),
 D_('year_doc', 'Year-end Pack for Accountant', 'Year-end pack for the accountant', 'pnl.row_id', [
  'Year-end pack of {set:company} to {col:pnl.month}, dated {today}.', 'Revenue this year to date {col:pnl.ytd_revenue}. Profit this year to date {col:pnl.ytd_profit}. Caregiver pay in the last 12 months {col:pnl.annual_pay}.',
  'Attach: the profit and loss by month, the expenses list, the pay run totals, the owner draws, the tax set-aside record and the client invoice and payment totals. Ask your accountant which other papers are needed; check your own local rules.'], ['Owner-director', 'Accountant']),
 D_('be_doc', 'Break-even Report', 'Break-even report for one month', 'pnl.row_id', [
  'Break-even report of {set:company} for {col:pnl.month}, dated {today}.', 'Gross margin per billed hour {col:pnl.margin_hour}. Overhead {col:pnl.overhead}. Break-even weekly hours {col:pnl.breakeven_hours} against weekly hours of {col:pnl.weekly_hours}.',
  'Weekly hours are growing by {col:pnl.hours_growth} a month, so the {set:office_help_hours}-hour marker for office help is about {col:pnl.months_to_marker} months away (99 means no growth).'], ['Owner-director']),
 D_('hours_doc', 'Hours Target Plan Report', 'Hours target plan report', 'hplan.plan_id', [
  'Hours target plan of {set:company}, dated {today}. Plan: {col:hplan.plan}.', 'Weekly hours in the plan {col:hplan.weekly_hours} at a margin of {col:hplan.margin_hour} per hour. Overhead {col:hplan.overhead} a month and an owner draw of {col:hplan.draw} a month.',
  'Profit after the draw {col:hplan.profit_after_draw}. Weekly hours needed {col:hplan.needed_hours}, gap {col:hplan.hours_gap} (plus is short). Caregivers to add {col:hplan.caregivers_needed} by {col:hplan.hire_by}.'], ['Owner-director', 'Recruiter']),
 D_('health_doc', 'Health Score Report', 'Health score report with six measures', 'health.hl_id', [
  'Health score report of {set:company} for {col:health.month}, dated {today}.', 'Gross margin per hour {col:health.margin_hour} ({col:health.p_margin} points). Overtime share {col:health.overtime_share} ({col:health.p_overtime}). Fill rate {col:health.fill_rate} ({col:health.p_fill}). Days to be paid {col:health.days_to_pay} ({col:health.p_days}).',
  'Caregiver turnover {col:health.turnover_rate} ({col:health.p_turnover}). Weeks of cash cover {col:health.cover_weeks} ({col:health.p_cover}).', 'Health score {col:health.score} out of 100. Worst item: {col:health.worst}. Targets are examples: replace them with your own.'], ['Owner-director']),
 D_('scen_doc', 'Scenario Comparison', 'Scenario comparison for one scenario', 'breakeven.sc_id', [
  'Scenario of {set:company}, dated {today}: {col:breakeven.scenario}.', 'Rate rise {col:breakeven.rate_rise}, hours lost {col:breakeven.hours_lost}, office help {col:breakeven.scheduler_cost} a month. Margin per hour after {col:breakeven.new_margin}.',
  'Weekly hours after {col:breakeven.hours_after} against break-even at {col:breakeven.breakeven_hours}. Profit a month {col:breakeven.profit_month}: {col:breakeven.verdict}.'], ['Owner-director']),
 D_('ovh_doc', 'Overhead Report', 'Overhead report by line', 'overhead.row_id', [
  'Overhead report of {set:company} for {col:overhead.month}, dated {today}.', 'Rent {col:overhead.rent}, office payroll {col:overhead.office_payroll}, field supervisor pay {col:overhead.field_pay}, software and phones {col:overhead.software_phones}, insurance {col:overhead.insurance}, marketing and recruiting {col:overhead.marketing_recruiting}, other {col:overhead.other}.',
  'Total overhead {col:overhead.total}, which is {col:overhead.share_of_revenue} of revenue against a target of {set:overhead_share_target}.'], ['Owner-director', 'Office manager']),
 D_('startup_doc', 'One-person Start-up Plan', 'One-person start-up plan for one page', 'startup.page_id', [
  'Start-up plan of {set:company}, dated {today}. Page: {col:startup.page} ({col:startup.part}).', 'Used by a one-person agency: {col:startup.one_person}. Switch it on from {col:startup.from_caregivers} caregivers. {col:startup.note}.',
  'A one-person agency can start with Enquiries, Quotes, Schedule, Visits, Payroll, Invoices and Cash and hide the rest until the agency grows. Use the Start-up Mode tool to see the next page to switch on.'], ['Owner-director']),
]
assert len(documents) == 12

def CS(k, title, table, start, steps): return _lib.CHK(k, title, table, start, steps)
checklists = [
 CS('c_close', 'Month-end Close Steps', 'pnl', 'pnl.month', [('Post every expense of the month', 33), ('Check billed hours and revenue against the invoices', 34), ('Check caregiver pay against the pay runs', 35), ('Enter the profit and loss row', 36), ('Read the health score and the worst item', 37), ('Send the profit and loss to the accountant', 38)]),
 CS('c_weekly', 'Weekly Cash Check Steps', 'forecast', 'forecast.starts_on', [('Update cash in the bank', 0), ('Tick off receipts that arrived', 0), ('Check the next pay run is funded', 1), ('Compare the week with the forecast', 6), ('Note any payer that is late', 6)]),
 CS('c_forecast', '13-Week Forecast Update Steps', 'receipts', 'receipts.starts_on', [('Roll the weeks forward', 0), ('Update expected receipts by payer', 0), ('Update upcoming pay runs', 1), ('Check the lowest cash week and the credit needed', 2), ('Check the Worst scenario against the floor', 2), ('Tell the owner what changed', 3)]),
 CS('c_drawtax', 'Owner Draw and Tax Set-aside Steps', 'draws', 'draws.month', [('Read last month\'s profit', 33), ('Move the tax set-aside; confirm the rate with your adviser', 35), ('Check the safe owner draw', 36), ('Take the draw and record it', 37), ('Check cash above the floor after the draw', 37)]),
 CS('c_budget', 'Budget Review Steps', 'budget', 'budget.review_on', [('Compare actual with budget by line', 0), ('Explain the three largest overruns', 1), ('Change the lines that no longer fit', 2), ('Share the budget with the office manager', 3)]),
 CS('c_overhead', 'Overhead Review Steps', 'overhead', 'overhead.month', [('Read overhead by line for the month', 33), ('Compare the share of revenue with the target', 34), ('Ask suppliers for new quotes on the largest line', 40), ('Cancel plans and subscriptions you do not use', 45)]),
 CS('c_insurance', 'Business Insurance Renewal Steps', 'budget', 'budget.review_on', [('Ask the broker for the renewal quote', -45), ('Update the estimated payroll for the year', -40), ('Compare at least two quotes', -30), ('Check your own local rules on required cover', -25), ('Decide and pay', -7), ('Keep the new papers where the team can find them', 0)]),
 CS('c_yearend', 'Year-end Pack for the Accountant Steps', 'pnl', 'pnl.month', [('Close the last month of the year', 35), ('Export the profit and loss by month', 36), ('Export the expenses list', 36), ('List owner draws and tax set-aside moves', 37), ('Add pay run totals and the payroll service reports', 38), ('Send the pack and book the review; confirm with your adviser', 40)]),
 CS('c_hours', 'Hours Target Review Steps', 'weekly', 'weekly.week', [('Compare weekly hours with the plan', 0), ('Update margin per hour and overhead', 1), ('Check the caregivers to add', 2), ('Tell the recruiter the number and the date', 3)]),
 CS('c_monday', 'Monday Health Review Steps', 'weekly', 'weekly.week', [('Open the Owner Dashboard', 0), ('Read the health score and the worst item', 0), ('Check cash above the floor and the next pay run', 0), ('Check billed minus paid hours', 1), ('Choose one action for the week', 1)]),
 CS('c_quarter', 'Quarterly Owner Review Steps', 'pnl', 'pnl.month', [('Read profit, margin and overhead for the quarter', 35), ('Compare with the same quarter last year', 36), ('Review the rate card and the weakest client', 40), ('Review the hours target and the office help marker', 45), ('Set the actions for the next quarter', 50)]),
 CS('c_startup', 'One-person Start-up Set-up Steps', 'team', 'team.start', [('Open Start-up Pages and hide the pages you do not need', 0), ('Type your own rates, targets and cash floor', 1), ('Replace the demo data with your own', 2), ('Log your first enquiry and quote', 3), ('Set up the schedule and the first invoice', 7), ('Start the 13-week cash forecast', 7)]),
]
assert len(checklists) == 12

# ---------- messages: every message goes to a team member; the table gets the contact's name and phone as calculated columns
CONTACTS = {'owner': 1, 'office': 3, 'scheduler': 2, 'recruiter': 4, 'accountant': 7, 'payroll': 8, 'broker': 9, 'trainer': 11, 'marketer': 13, 'landlord': 14, 'it': 15, 'answering': 16}
MSGS = [
 ('o_health', 'Owner: the health score and the worst item', 'health', 'owner', 'Hello {owner_name}, the agency health score for {month} is {score}. The worst item is {worst}. {company}'),
 ('o_cashlow', 'Owner: cash below the floor in a forecast week', 'forecast', 'owner', 'Hello {owner_name}, in the {scenario} forecast cash is {closing} in {week}, near or below the floor. Please plan credit or a smaller draw. {company}'),
 ('o_safedraw', 'Owner: the safe owner draw this month', 'cash', 'owner', 'Hello {owner_name}, the safe owner draw for {month} is {safe_draw}. Cash above the floor is {above_floor}. {company}'),
 ('o_tax', 'Owner: move the tax set-aside', 'tax', 'owner', 'Hello {owner_name}, please move {set_aside} to the tax set-aside account for {month}. Confirm the rate with your adviser. {company}'),
 ('o_profit', 'Owner: profit and profit share', 'pnl', 'owner', 'Hello {owner_name}, profit for {month} was {profit}, which is {profit_share} of revenue. {company}'),
 ('o_breakeven', 'Owner: break-even against weekly hours', 'pnl', 'owner', 'Hello {owner_name}, break-even for {month} is {breakeven_hours} weekly hours and you are at {weekly_hours}. {company}'),
 ('o_marker', 'Owner: months to the office help marker', 'pnl', 'owner', 'Hello {owner_name}, at the current growth weekly hours reach the office help marker in {months_to_marker} months. Please plan the hire. {company}'),
 ('o_overhead', 'Owner: overhead above the target share', 'overhead', 'owner', 'Hello {owner_name}, overhead for {month} was {share_of_revenue} of revenue, above your target share. {company}'),
 ('o_budget', 'Owner: a budget line is over', 'budget', 'owner', 'Hello {owner_name}, the budget line {category} is {variance} over its monthly budget of {budget}. {company}'),
 ('o_forecast', 'Owner: the 13-week forecast is updated', 'forecast', 'owner', 'Hello {owner_name}, the 13-week forecast is updated. {week} closes at {closing} in the {scenario} case. {company}'),
 ('o_payerlate', 'Owner: a payer pays later', 'forecast', 'owner', 'Hello {owner_name}, if a payer pays later, cash in {week} falls to {closing_late} instead of {closing}. {company}'),
 ('o_yearend', 'Owner: the year-end pack is ready', 'pnl', 'owner', 'Hello {owner_name}, the year-end pack for {accountant_name} is ready: profit to date {ytd_profit} on revenue {ytd_revenue}. {company}'),
 ('m_close', 'Office manager: close the month', 'pnl', 'office', 'Hello {office_name}, please close the month of {month} by {close_by}. {company}'),
 ('m_receipts', 'Office manager: receipts expected', 'receipts', 'office', 'Hello {office_name}, a {source} receipt of {amount} is expected in the week of {starts_on}. Please match it when it arrives. {company}'),
 ('m_payrun', 'Office manager: the pay run goes out', 'payruns', 'office', 'Hello {office_name}, the pay run of {cost_with_burden} goes out on {pay_date}. Please confirm the funds. {company}'),
 ('m_expenses', 'Office manager: post the weekly expenses', 'weekly', 'office', 'Hello {office_name}, please post the expenses for the week of {week}. {company}'),
 ('m_budget', 'Office manager: update the budget line', 'budget', 'office', 'Hello {office_name}, the budget needs an update for {category}: last month {actual_last_month} against {budget}. {company}'),
 ('s_hours', 'Scheduler: weekly hours fell short', 'weekly', 'scheduler', 'Hello {scheduler_name}, delivered hours for the week of {week} were {delivered_hours} against {scheduled_hours} scheduled. Please check open shifts. {company}'),
 ('s_target', 'Scheduler: the hours target', 'hplan', 'scheduler', 'Hello {scheduler_name}, the plan {plan} needs {needed_hours} weekly hours. Please plan the schedule toward it. {company}'),
 ('r_need', 'Recruiter: caregivers needed by a date', 'hplan', 'recruiter', 'Hello {recruiter_name}, we need {caregivers_needed} more caregivers by {hire_by} for the plan {plan}. {company}'),
 ('r_budget', 'Recruiter: the recruiting budget', 'budget', 'recruiter', 'Hello {recruiter_name}, the budget for {category} this month is {budget}. {company}'),
 ('a_pnl', 'Accountant: the profit and loss is attached', 'pnl', 'accountant', 'Hello {accountant_name}, the profit and loss for {month} is attached: revenue {revenue}, profit {profit}. {company}'),
 ('a_expenses', 'Accountant: the expenses list is attached', 'overhead', 'accountant', 'Hello {accountant_name}, the expenses list for {month} is attached. Total overhead {total}. {company}'),
 ('a_tax', 'Accountant: confirm the set-aside rate', 'tax', 'accountant', 'Hello {accountant_name}, the tax set-aside total is {cumulative} after {month}. Please confirm the rate of {set_aside_pct}. {company}'),
 ('a_draw', 'Accountant: review the owner draw', 'draws', 'accountant', 'Hello {accountant_name}, please review the owner draw for the year: {cumulative} taken to {month}. {company}'),
 ('p_fund', 'Payroll service: the funding date', 'payruns', 'payroll', 'Hello {payroll_name}, the funding date for the pay run of {cost_with_burden} is {pay_date}. {company}'),
 ('b_renew', 'Insurance broker: send the renewal quote', 'overhead', 'broker', 'Hello {broker_name}, please send the renewal quote for the business insurance. We pay {insurance} a month now. {company}'),
 ('b_payroll', 'Insurance broker: the estimated payroll', 'pnl', 'broker', 'Hello {broker_name}, the estimated payroll for the year is {annual_pay}. Please use it for the quote. {company}'),
 ('l_rent', 'Landlord: the rent is paid', 'overhead', 'landlord', 'Hello {landlord_name}, the rent of {rent} is paid for {month}. {company}'),
 ('i_plans', 'IT support: renew the software and phone plans', 'overhead', 'it', 'Hello {it_name}, please renew the software and phone plans; they cost {software_phones} in {month}. {company}'),
 ('k_budget', 'Marketing helper: the marketing budget', 'overhead', 'marketer', 'Hello {marketer_name}, the marketing and recruiting budget for {month} is {marketing_recruiting}. {company}'),
 ('k_report', 'Marketing helper: report enquiries by source', 'marketing', 'marketer', 'Hello {marketer_name}, please report the enquiries by source for {month}. We spent {cost} on {kind}. {company}'),
 ('t_budget', 'Training provider: the quarter budget', 'budget', 'trainer', 'Hello {trainer_name}, the budget for {category} for the quarter is {quarter_budget}. {company}'),
 ('v_oncall', 'Answering service: the on-call plan', 'weekly', 'answering', 'Hello {answering_name}, the on-call plan for the week of {week} follows. Please confirm the hours you cover. {company}'),
]
assert len(MSGS) == 34
messages = [MSG(k, moment, tb, '%s.%s_phone' % (tb, ct), text) for k, moment, tb, ct, text in MSGS]
tmap = {t['key']: t for t in tables}
for k, moment, tb, ct, text in MSGS:
    cols = tmap[tb]['columns']
    have = {c['key'] for c in cols}
    for suffix, fn in (('name', STAFFN), ('phone', STAFF)):
        if '%s_%s' % (ct, suffix) not in have: cols.append(fn(CONTACTS[ct], '%s_%s' % (ct, suffix)))
    if 'company' not in have and not any(c['key'] == 'company' for c in cols): cols.append(CA('company', 'Agency', 'text', '{set:company}&""', 24))
    if 'accountant_name' in text and 'accountant_name' not in {c['key'] for c in cols}: cols.append(STAFFN(7, 'accountant_name'))

# ---------- dashboard
def S1(c, v='1'): return '%s' % c
PR = tok('payer', 'Private pay')
kpis = [
 KPI('Revenue this month so far', 'SUMIFS({range:pnl.revenue},{range:pnl.month},%s)' % M0, 'money'),
 KPI('Revenue last month', PNM('revenue'), 'money'),
 KPI('Gross margin last month', PNM('gross_margin'), 'money'),
 KPI('Gross margin share last month', 'IFERROR(%s/%s,0)' % (PNM('gross_margin'), PNM('revenue')), 'pct', alert={"when": "< {set:target_margin}", "style": "warn"}),
 KPI('Overhead last month', PNM('overhead'), 'money'),
 KPI('Overhead share last month', 'IFERROR(%s/%s,0)' % (PNM('overhead'), PNM('revenue')), 'pct', alert={"when": "> {set:overhead_share_target}", "style": "warn"}),
 KPI('Profit last month', PNM('profit'), 'money', alert={"when": "< 0", "style": "bad"}),
 KPI('Profit share last month', 'IFERROR(%s/%s,0)' % (PNM('profit'), PNM('revenue')), 'pct', alert={"when": "< {set:profit_target}", "style": "warn"}),
 KPI('Profit last 3 months', 'SUMIFS({range:pnl.profit},{range:pnl.month},">="&EDATE(%s,-2),{range:pnl.month},"<="&%s)' % (M1, M1), 'money'),
 KPI('Profit this year, full months', 'SUMIFS({range:pnl.profit},{range:pnl.month},">="&DATE(YEAR({today}),1,1),{range:pnl.month},"<"&%s)' % M0, 'money'),
 KPI('Cash now', 'SUMIFS({range:cash.closing},{range:cash.month},%s)' % M0, 'money'),
 KPI('Cash above the floor', 'SUMIFS({range:cash.closing},{range:cash.month},%s)-{set:cash_floor}' % M0, 'money', alert={"when": "< 0", "style": "bad"}),
 KPI('Lowest cash in the next 13 weeks', 'SUMIFS({range:forecast.closing},{range:forecast.scenario},%s,{range:forecast.rank_low},1)' % tok('scen', 'Base'), 'money', alert={"when": "< {set:cash_floor}", "style": "bad"}),
 KPI('Weeks of cash cover', 'IFERROR(SUMIFS({range:cash.closing},{range:cash.month},%s)/((SUMIFS({range:cash.pay_runs},{range:cash.month},%s)+SUMIFS({range:cash.expenses},{range:cash.month},%s))*12/52),0)' % (M0, M1, M1), 'num', alert={"when": "< {set:cash_cover_weeks}", "style": "warn"}),
 KPI('Weeks under the floor, worst case', 'COUNTIFS({range:forecast.scenario},%s,{range:forecast.closing},"<"&{set:cash_floor})' % tok('scen', 'Worst'), 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Credit needed, worst case', 'MAX(0,{set:cash_floor}-SUMIFS({range:forecast.closing},{range:forecast.scenario},%s,{range:forecast.rank_low},1))' % tok('scen', 'Worst'), 'money', alert={"when": "> 0", "style": "bad"}),
 KPI('Pay run due next', 'SUMIFS({range:payruns.cost_with_burden},{range:payruns.status},%s)' % ck('Next run'), 'money'),
 KPI('Receipts expected next 4 weeks', 'SUMIFS({range:receipts.amount},{range:receipts.week_no},"<=4")', 'money'),
 KPI('Payer receipts still expected', 'SUMIFS({range:receipts.amount},{range:receipts.source},"<>"&%s)' % PR, 'money'),
 KPI('Owner draw this year', 'SUMIFS({range:draws.draw},{range:draws.month},">="&DATE(YEAR({today}),1,1),{range:draws.month},"<="&%s)' % M0, 'money'),
 KPI('Safe owner draw this month', 'SUMIFS({range:cash.safe_draw},{range:cash.latest},1)', 'money'),
 KPI('Tax set-aside balance this year', 'SUMIFS({range:tax.set_aside},{range:tax.status},%s,{range:tax.this_year},1)' % tok('taxst', 'Moved'), 'money'),
 KPI('Tax set-aside due now', 'SUMIFS({range:tax.set_aside},{range:tax.status},%s)' % tok('taxst', 'Due'), 'money', alert={"when": "> 0", "style": "warn"}),
 KPI('Break-even weekly hours', 'ROUND(%s,0)' % PNM('breakeven_hours'), 'int'),
 KPI('Weekly hours now', 'ROUND(%s,0)' % PNM('weekly_hours'), 'int'),
 KPI('Margin of safety over break-even', 'IFERROR((%s-%s)/%s,0)' % (PNM('weekly_hours'), PNM('breakeven_hours'), PNM('weekly_hours')), 'pct'),
 KPI('Weekly hours needed for the owner target', 'ROUND((%s+{set:owner_draw})/(%s*%s),0)' % (PNM('overhead'), WPM, PNM('margin_hour')), 'int'),
 KPI('Months to the office help marker', PNM('months_to_marker'), 'int'),
 KPI('Agency health score', 'SUMIFS({range:health.score},{range:health.latest},1)', 'num', alert={"when": "< {set:health_watch_score}", "style": "bad"}),
 KPI('Measures in red', 'COUNTIFS({range:targets.light},%s,{range:targets.level},%s)' % (ck('Red'), tok('lvl', 'Target')), 'int', alert={"when": "> 0", "style": "bad"}),
]
assert len(kpis) == 30
dashboard = {"title": "Owner KPI Dashboard", "kpis": kpis,
 "monthly": {"title": "Revenue, overhead and profit by month", "date": "pnl.month", "series": [
   {"label": "Revenue", "sum": "pnl.revenue", "date": "pnl.month"}, {"label": "Overhead", "sum": "pnl.overhead", "date": "pnl.month"}, {"label": "Profit", "sum": "pnl.profit", "date": "pnl.month"}]},
 "breakdowns": [{"title": "Overhead by category", "by": "expenses.category", "value": "expenses.amount", "agg": "sum"}, {"title": "Revenue by service", "by": "svcrev.service", "value": "svcrev.revenue", "agg": "sum"},
                {"title": "Expected receipts by source", "by": "receipts.source", "value": "receipts.amount", "agg": "sum"}, {"title": "Marketing cost by kind", "by": "marketing.kind", "value": "marketing.cost", "agg": "sum"}]}
FULL = [('complete', '=', 1)]
def tk(lst, lab): return tok(lst, lab)
insights = {"filters": [{"label": "Service", "list": "svc"}, {"label": "Expense category", "list": "ecat"}, {"label": "Marketing kind", "list": "mkind"}],
 "gauges": [
  {"title": "Agency health score", "num": AGG('sum', 'health', 'health.score', where=[('latest', '=', 1)]), "den": AGG('sum', 'health', 'health.scale', where=[('latest', '=', 1)])},
  {"title": "Profit against the target share", "num": AGG('sum', 'pnl', 'pnl.profit', where=FULL), "den": AGG('sum', 'pnl', 'pnl.target_profit', where=FULL)},
  {"title": "Forecast weeks at or above the floor", "num": AGG('sum', 'forecast', 'forecast.above'), "den": AGG('count', 'forecast')},
  {"title": "Months meeting the cash cover target", "num": AGG('count', 'health', where=[('cover_weeks', '>=', '{set:cash_cover_weeks}')]), "den": AGG('count', 'health')},
  {"title": "Tax set-aside funded this year", "num": AGG('sum', 'tax', 'tax.set_aside', where=[('this_year', '=', 1), ('status', '=', tk('taxst', 'Moved'))]), "den": AGG('sum', 'tax', 'tax.set_aside', where=[('this_year', '=', 1)])},
  {"title": "Months with overhead within the target", "num": AGG('count', 'pnl', where=[('overhead_share', '<=', '{set:overhead_share_target}'), ('complete', '=', 1)]), "den": AGG('count', 'pnl', where=FULL)}],
 "charts": [
  CHART('Revenue and profit per month', 'column', 'month', [AGG('sum', 'pnl', 'pnl.revenue', date='pnl.month', label='Revenue', where=FULL), AGG('sum', 'pnl', 'pnl.profit', date='pnl.month', label='Profit', where=FULL)]),
  CHART('Gross margin share per month', 'line', 'month', [AGG('avg', 'pnl', 'pnl.gross_margin_share', date='pnl.month', label='Gross margin share', where=FULL)]),
  CHART('Profit share per month', 'line', 'month', [AGG('avg', 'pnl', 'pnl.profit_share', date='pnl.month', label='Profit share', where=FULL)]),
  CHART('Overhead per month', 'column', 'month', [AGG('sum', 'overhead', 'overhead.total', date='overhead.month', label='Overhead', where=FULL)]),
  CHART('Overhead by category', 'bar', 'expenses.category', [AGG('sum', 'expenses', 'expenses.amount', label='Overhead')]),
  CHART('Overhead share per month', 'line', 'month', [AGG('avg', 'overhead', 'overhead.share_of_revenue', date='overhead.month', label='Overhead share', where=FULL)]),
  CHART('Budget against actual by category', 'bar', 'budget.category', [AGG('sum', 'budget', 'budget.budget', label='Monthly budget'), AGG('sum', 'budget', 'budget.actual_last_month', label='Actual last month')]),
  CHART('Cash closing balance per month', 'line', 'month', [AGG('sum', 'cash', 'cash.closing', date='cash.month', label='Closing cash', where=FULL)]),
  CHART('Cash in against cash out per month', 'column', 'month', [AGG('sum', 'cash', 'cash.cash_in', date='cash.month', label='Cash in', where=FULL), AGG('sum', 'cash', 'cash.cash_out', date='cash.month', label='Cash out', where=FULL)]),
  CHART('13-week closing balance by week', 'line', 'forecast.week', [AGG('avg', 'forecast', 'forecast.closing', label='Base', where=[('scenario', '=', tk('scen', 'Base'))]), AGG('avg', 'forecast', 'forecast.closing', label='Best', where=[('scenario', '=', tk('scen', 'Best'))]),
                                                                    AGG('avg', 'forecast', 'forecast.closing', label='Worst', where=[('scenario', '=', tk('scen', 'Worst'))])]),
  CHART('13-week net cash by scenario', 'bar', 'forecast.scenario', [AGG('sum', 'forecast', 'forecast.net', label='Net cash in 13 weeks')]),
  CHART('Owner draw per month', 'column', 'month', [AGG('sum', 'draws', 'draws.draw', date='draws.month', label='Owner draw')]),
  CHART('Tax set-aside per month', 'column', 'month', [AGG('sum', 'tax', 'tax.set_aside', date='tax.month', label='Set-aside')]),
  CHART('Cumulative tax set-aside per month', 'line', 'month', [AGG('sum', 'tax', 'tax.cumulative', date='tax.month', label='Running total')]),
  CHART('Weekly hours, monthly average', 'line', 'month', [AGG('avg', 'weekly', 'weekly.scheduled_hours', date='weekly.week', label='Scheduled'), AGG('avg', 'weekly', 'weekly.billed_hours', date='weekly.week', label='Billed')]),
  CHART('Billed minus paid hours per month', 'column', 'month', [AGG('sum', 'weekly', 'weekly.billed_minus_paid', date='weekly.week', label='Billed minus paid hours')]),
  CHART('Revenue by service', 'bar', 'svcrev.service', [AGG('sum', 'svcrev', 'svcrev.revenue', label='Revenue')]),
  CHART('Margin share by service', 'bar', 'svcrev.service', [AGG('avg', 'svcrev', 'svcrev.margin_share', label='Margin share')]),
  CHART('Health score per month', 'line', 'month', [AGG('avg', 'health', 'health.score', date='health.month', label='Health score', where=FULL)]),
  CHART('Health measures against target', 'bar', 'targets.measure', [AGG('avg', 'targets', 'targets.points', label='Points (100 is on target)')]),
  CHART('Marketing cost per month', 'column', 'month', [AGG('sum', 'marketing', 'marketing.cost', date='marketing.month', label='Marketing cost')]),
  CHART('Marketing results by kind', 'bar', 'marketing.kind', [AGG('sum', 'marketing', 'marketing.results', label='Results'), AGG('sum', 'marketing', 'marketing.started', label='Started')])]}
assert len(insights['charts']) == 22

signature = [
 {"name": "Is the agency healthy? One score", "why": "margin per hour, overtime, fill rate, days to be paid, turnover and weeks of cash cover each score against your targets, with the worst item first", "where": "Is the Agency Healthy"},
 {"name": "Monthly profit and loss", "why": "revenue from billed hours, caregiver cost, gross margin, overhead and profit by month, with every share worked out", "where": "Profit and Loss"},
 {"name": "13-week cash forecast with Base, Best and Worst", "why": "payroll every pay run, receipts by payer, a floor warning and a payer-pays-later slider show the lowest week before it happens", "where": "13-Week Cash Forecast"},
 {"name": "Lowest cash week and the credit needed", "why": "the week to worry about, the shortfall against your floor and the date to arrange credit", "where": "Lowest Cash Week"},
 {"name": "Safe owner draw", "why": "the largest draw this month that keeps cash above the floor after tax set-aside and the next pay run, with Take it, Take less or Wait", "where": "Safe Owner Draw"},
 {"name": "Tax set-aside planner", "why": "the amount to move each month and the cash left after it (confirm the rate with your adviser)", "where": "Tax Set-Aside Planner"},
 {"name": "Hours target planner with the 1,000-hour marker", "why": "the weekly hours needed to cover overhead and your draw, the gap, the caregivers to add and when to hire office help", "where": "Hours Target Planner"},
 {"name": "Break-even weekly hours", "why": "hours needed at your margin per hour and the margin of safety over today's hours", "where": "Break-Even Hours"},
 {"name": "Rate rise, weakest client and scheduler scenarios", "why": "profit before and after each decision, with Raise or Hold, Release or Keep and Worth adding", "where": "Rate Rise Scenario"},
 {"name": "Budget against actual", "why": "every expense line against its budget, the three largest overruns and a verdict", "where": "Budget Against Actual"},
 {"name": "Health against your own history", "why": "this month against the last three months and the same month last year, naming the measure that slipped most", "where": "Health Against History"},
 {"name": "Start-up mode for a one-person agency", "why": "which pages to use at your size, which to hide, and the point at which to switch on the next one", "where": "Start-up Mode"}]
competitors = [
 {"what": "free budget and profit templates", "lacks": "show income and spending but know nothing about billed hours, margin per hour, pay runs or break-even weekly hours"},
 {"what": "subscription home care software with a per-client fee", "lacks": "charges more as hours grow and gives no 13-week cash forecast, safe owner draw or health score for the owner"},
 {"what": "generic cash flow spreadsheets", "lacks": "have no pay run rhythm, no payer delay slider and no floor warning built for a care agency"},
 {"what": "single-sheet profit and loss logs", "lacks": "record a month but never compare it with the budget, last year or a target, and never name the weakest item"}]
guide = [
 'Open Start here and type your agency name, your cash floor, the planned owner draw and your targets in the yellow cells: profit share, overhead share, cash cover weeks and the 1,000-hour marker (a marker, not a rule).',
 'Check Team, Expenses and Budget. Overhead by month, the budget actual and the profit and loss overhead read the Expenses sheet, so every payment is typed once.',
 'Type each month on Profit and Loss: revenue, billed hours and the caregiver pay lines. Gross margin, profit, the shares, break-even weekly hours and the hours growth fill in by themselves. Payroll burden means payroll taxes, workers\' insurance and benefits on top of pay (confirm with your adviser).',
 'Keep Cash Months, Pay Runs and Expected Receipts up to date. The 13-Week Cash Forecast shows Base, Best and Worst, the lowest week and what happens if third-party payers (an insurer, a public body or an employer scheme in your area) pay later.',
 'Use Owner Draws and Tax Set-Aside each month. The Safe Owner Draw tool gives the largest draw that keeps cash above the floor. Every tax and pay amount is an example: confirm with your adviser.',
 'Read Health Score History and Health Targets. Each of six measures is scored from the target to the red limit; the worst item shows what to fix first. Edit the targets to your own.',
 'Use the Hours Target Plan, Break-Even Scenarios and the scenario tools before a rate rise, a decision about a weak client or a hire. Gross margin per hour means bill rate minus loaded pay cost.',
 'A one-person agency can start with Enquiries, Quotes, Schedule (a rota or roster), Visits, Payroll, Invoices and Cash; Start-up Pages and the Start-up Mode tool show what to hide until you grow.',
 f'Use the {len(tools)} decision tools: each ends with a verdict and a what-if table. Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready messages.',
 'Replace the demo data with your own: clear the demo rows, type your own months and keep the dates as real dates. The workbook has no macros and works in Excel and Google Sheets.',
 'Why a workbook: one flat price, no per-client or per-caregiver fee, no price rise when hours grow, your data stays with you, and reports built for agency owners. It takes typed or pasted figures: there is no live app, no GPS and no automatic check-in.']
listing = {"title": "Home Care Agency Owner Dashboard Excel Template: Profit and Loss, 13-Week Cash Forecast, Safe Owner Draw, Break-Even Hours, Health Score",
 "headline": "Know if your home care agency is healthy: profit, cash, hours and draw",
 "tags": ["home care agency", "cash flow forecast", "profit and loss", "owner dashboard", "break even hours", "agency finance", "tax set aside", "owner draw", "budget template", "kpi dashboard", "excel template", "caregiver payroll", "business health"],
 "description": ("Run the money side of a small home care agency in one Excel workbook. Built for an owner-director with a scheduler, an office manager and a part-time recruiter, and for a one-person start-up agency that wants to begin with the pages it needs.\n\n"
  "Profit and Loss turns revenue from billed hours, caregiver pay, overtime, travel, payroll burden and overhead into gross margin, profit and every share. Expenses feed Overhead by Month and the Budget, so each payment is typed once. Cash Months, Pay Runs and Expected Receipts feed a 13-Week Cash Forecast in Base, Best and Worst, with a floor warning, weeks of cover and a payer-pays-later slider.\n\n"
  f"{len(tools)} decision tools answer the questions an owner asks every week, each with a verdict: Is the agency healthy? (one score from six measures with the worst item first), safe owner draw, tax set-aside (confirm with your adviser), lowest cash week and credit needed, hours target planner with the 1,000-hour marker, break-even weekly hours, rate rise, weakest client and scheduler scenarios, budget against actual and start-up mode. "
  f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists, send {len(messages)} ready messages and read {len(kpis)} live figures and {len(insights['charts'])} charts on the owner dashboard.\n\n"
  "This is part eight of the Home Care Agency Business suite. A standard .xlsx workbook with no macros and no subscription, one flat price with no per-client or per-caregiver fee, your data stays with you, 15 languages in one purchase, with a demo copy full of sample data. Tax, pay and insurance figures are examples: confirm with your adviser and check your own local rules. The workbook holds money, hours and dates only and does not promise results."),
 "features": ["Profit and loss by month with every share", "13-week cash forecast in Base, Best and Worst", "Payer-pays-later slider and lowest cash week", "Safe owner draw and tax set-aside planner", "Health score from six measures, worst item first",
              "Hours target planner with the 1,000-hour marker", "Break-even weekly hours and scenarios", "Budget against actual by line", f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents",
              f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "Start-up mode for a one-person agency", "One flat price, your data stays with you"]}

# ---------- fit the validator limits
for t in tables: t['rows'] = max(50, t['rows'])
HINT = {
 'pnl': 'One row per month: type revenue, billed hours and caregiver pay lines; overhead comes from Expenses; margin, profit, shares and break-even hours fill in.',
 'overhead': 'One row per month: every line is read from Expenses; the total and its share of revenue fill in by themselves.',
 'cash': 'One row per month: type opening cash, cash in and pay runs; other lines come from their own sheets; closing cash and cash above the floor fill in.',
 'forecast': 'Thirteen weeks in Base, Best and Worst: type receipts, pay run, overhead, draw and tax; net, closing balance, floor check and cover fill in.',
 'receipts': 'One row per expected receipt in the next 13 weeks: week, source, amount and usual days to pay; the slider week and the amount that moves fill in.',
 'tax': 'One row per month: type the set-aside share, status and date moved; profit, the set-aside and the running total fill in. Confirm with your adviser.',
 'breakeven': 'One row per scenario: type the rate rise, hours lost and office help cost; new margin per hour, break-even hours and profit fill in.',
 'health': 'One row per month: type overtime, fill rate, days to be paid, turnover and cash cover; points, score and worst item fill in against Health Targets.',
 'targets': 'Six measures, four rows each: target, amber limit, red limit and weight; the latest value, its points and the light fill in. Example values: use your own.',
 'startup': 'One row per page of the suite: whether a one-person agency uses it and from how many caregivers to switch it on; hide the rest until you grow.',
 'staffcost': None}
for t in tables:
    if HINT.get(t['key']): t['hint'] = HINT[t['key']]
    if t['key'] == 'staffcost': t['title'] = 'Office and field staff cost at three stages'
THINT = {
 'cash_planner': 'Type cash now, weekly receipts, pay run, monthly overhead, draw and tax, a scenario (1 Base, 2 Best, 3 Worst) and payer delay; see 13 closing balances and a verdict.',
 'payer_later': 'Type cash now and the weekly flows; the 13 weeks run five times with payers paying 0 to 45 days later, showing lowest cash and credit needed.',
 'safe_draw': 'Type last month\'s profit, cash now, what comes in and goes out, and the draw you plan; tax set-aside comes off first; see the largest safe draw.',
 'tax_move': 'Type profit, the set-aside share, the amount already set aside and cash now; see the amount to move and a verdict. Confirm with your adviser.',
 'hours_target': 'Type overhead, owner draw, margin per hour, weekly hours and hours per caregiver; see the hours needed, the gap and caregivers to add.',
 'office_help': 'Type weekly hours now, hours added a month, office help cost and margin per hour; see months to the marker and a verdict.',
 'drop_client': 'Type the client\'s weekly hours and margin per hour, the share you expect to replace and agency margin; see the profit change and a verdict.',
 'add_scheduler': 'Type monthly pay, burden, extra weekly hours served, margin per hour and expected savings; see the profit change and the hours that pay it back.',
 'startup_mode': 'Type your caregivers, clients and weekly hours and whether someone else schedules; see the pages to use, to hide and the next to switch on.'}
TTITLE = {'health_history': 'Health against your own history', 'tax_move': 'Tax set-aside: the amount to move now', 'hours_target': 'Hours target for overhead and the owner draw', 'add_scheduler': 'Add a scheduler: profit change and payback hours'}
for t in tools:
    if t['key'] in THINT: t['hint'] = THINT[t['key']]
    if t['key'] in TTITLE: t['title'] = TTITLE[t['key']]
for st in settings:
    if st['key'] == 'payroll_burden': st['label'] = 'Payroll burden on pay (example, confirm with your adviser)'
    if st['key'] == 'office_help_hours': st['label'] = 'Weekly hours at which office help is needed (a marker)'
    if st['key'] == 'tax_set_aside_pct': st['label'] = 'Tax set-aside share of profit (example)'
for f in forms:
    f['title'] = {'tax_sheet': 'Tax set-aside for the month', 'cash_check': 'Cash check: in, out and above the floor', 'health_review': 'Health review: six measures and the worst item'}.get(f['key'], f['title'])
for m in messages:
    m['moment'] = {'o_health': 'Owner: health score and worst item', 'o_cashlow': 'Owner: cash low in a forecast week', 'a_pnl': 'Accountant: profit and loss attached', 'a_expenses': 'Accountant: expenses list attached',
                   'i_plans': 'IT support: renew software and phones', 'k_report': 'Marketing helper: enquiries by source'}.get(m['key'], m['moment'])
for c in checklists:
    c['title'] = {'c_drawtax': 'Owner Draw and Tax Steps', 'c_insurance': 'Insurance Renewal Steps', 'c_yearend': 'Year-end Accountant Pack Steps', 'c_startup': 'Start-up Set-up Steps'}.get(c['key'], c['title'])
guide[2] = 'Type each month on Profit and Loss: revenue, billed hours and caregiver pay lines. Margin, profit, shares and break-even hours fill in. Payroll burden means payroll taxes, insurance and benefits on top of pay (confirm with your adviser).'
guide[3] = 'Keep Cash Months, Pay Runs and Expected Receipts up to date. The 13-Week Cash Forecast shows Base, Best and Worst, the lowest week and what happens if third-party payers (an insurer or a public body) pay later.'
guide[10] = 'Why a workbook: one flat price, no per-client or per-caregiver fee, your data stays with you, and reports built for agency owners. It takes typed or pasted figures: no live app, no GPS and no automatic check-in.'
s = _lib.spec(id=f'{SUITE}-p8', slug='home-care-owner', profession='Home Care Agency Business', name='Owner Money and Business Health',
         tagline='Profit, cash, hours and the owner draw: is the agency healthy?', price_usd=29, colors={"primary": "#3A506B", "accent": "#E07A5F"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard,
         forms=forms, guide=guide, listing=listing, insights=insights, suite={"key": SUITE, "part": 8, "of": 8, "focus": "Owner money and business health"}, signature=signature, competitors=competitors,
         tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hc8.en.json'))
    print('tables', len(tables), 'rows', sum(len(t['demo']) for t in tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
