"""Therapy private practice suite - part 8: Practice Profit, Cash Flow and Growth."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th8_lists import *
from th8_tables import settings, tables, CA, PH
from th8_tools import tools
import th8_lists as _L

SUITE = 'fx-20261115-therapy-practice'
NOTE = "Sample wording: adapt it to your own practice and check your own local rules."
def F(*p): return [FV(a, b) for a, b in p]
import lib as _lib

forms = [
 FORM('expense_sheet', 'Expense Sheet', 'Expense record with category spend this year', 'expenses.expense_id', F(
  ('Date', 'expenses.date'), ('Month', 'expenses.month'), ('Category', 'expenses.category'), ('Description', 'expenses.description'), ('Amount', 'expenses.amount'), ('Paid to', 'expenses.paid_to'), ('Method', 'expenses.method'), ('Category spend this year', 'expenses.category_year'))),
 FORM('close_sheet', 'Monthly Close Sheet', 'Monthly close with profit and margin', 'pnl.pl_id', F(
  ('Month', 'pnl.month'), ('Attended sessions', 'pnl.sessions'), ('Session revenue', 'pnl.session_revenue'), ('Group revenue', 'pnl.group_revenue'), ('Sublet income', 'pnl.sublet_income'), ('Write-offs', 'pnl.write_offs'),
  ('Clinician pay', 'pnl.clinician_pay'), ('Staff pay', 'pnl.staff_pay'), ('Rent', 'pnl.rent'), ('Other expenses', 'pnl.other_expenses'), ('Revenue', 'pnl.revenue'), ('Total costs', 'pnl.costs'), ('Profit', 'pnl.profit'),
  ('Profit margin', 'pnl.margin'), ('Pay share of revenue', 'pnl.pay_share'), ('Overhead share of revenue', 'pnl.overhead_share'), ('Profit per attended session', 'pnl.profit_per_session'), ('Profit after the owner draw', 'pnl.kept'),
  ('Margin check', 'pnl.margin_flag'), ('Overhead check', 'pnl.ovh_flag'))),
 FORM('budget_sheet', 'Budget Sheet', 'Category budget against spending', 'budget.budget_id', F(
  ('Category', 'budget.category'), ('Yearly budget', 'budget.yearly_budget'), ('Monthly budget', 'budget.monthly_budget'), ('Budget to date', 'budget.budget_to_date'), ('Spent this year', 'budget.spent'),
  ('Left in the budget', 'budget.left'), ('Spent over or under the budget to date', 'budget.variance'), ('Status', 'budget.status'))),
 FORM('cash_sheet', 'Cash Check Sheet', 'Monthly cash check', 'cash.cash_id', F(
  ('Month', 'cash.month'), ('Opening cash', 'cash.opening'), ('Client payments', 'cash.client_payments'), ('Payer payments', 'cash.payer_payments'), ('Sublet income', 'cash.sublet_income'), ('Staff pay', 'cash.staff_pay'),
  ('Contractor pay', 'cash.contractor_pay'), ('Rent', 'cash.rent'), ('Other expenses', 'cash.other_expenses'), ('Tax set-aside', 'cash.tax_set_aside'), ('Owner draw', 'cash.owner_draw'), ('Closing cash', 'cash.closing'),
  ('Cash in', 'cash.cash_in'), ('Cash out', 'cash.cash_out'), ('Net flow', 'cash.net_flow'), ('Months of expenses in cash', 'cash.months_cover'))),
 FORM('draw_sheet', 'Owner Draw Sheet', 'Owner draw against the safe draw', 'cash.cash_id', F(
  ('Month', 'cash.month'), ('Closing cash', 'cash.closing'), ('Owner draw taken', 'cash.owner_draw'), ('Safe draw', 'cash.safe_draw'), ('Tax set-aside', 'cash.tax_set_aside'), ('Net flow', 'cash.net_flow'), ('Months of expenses in cash', 'cash.months_cover')) + [
  FF('Cash above the floor', 'IFERROR(INDEX({range:cash.closing},MATCH({pick},{range:cash.cash_id},0))-{set:cash_floor},0)', 'money'),
  FF('Draw above (+) or below (-) safe draw', 'IFERROR(INDEX({range:cash.owner_draw},MATCH({pick},{range:cash.cash_id},0))-INDEX({range:cash.safe_draw},MATCH({pick},{range:cash.cash_id},0)),0)', 'money')]),
 FORM('tax_sheet', 'Tax Set-aside Sheet', 'Tax set-aside for a month (ask your adviser)', 'tax.tax_id', F(
  ('Month', 'tax.month'), ('Revenue', 'tax.revenue'), ('Costs', 'tax.costs'), ('Profit', 'tax.profit'), ('Set-aside share', 'tax.set_aside_pct'), ('Set-aside amount', 'tax.set_aside'), ('Due date', 'tax.due_date'), ('Status', 'tax.status'))),
 FORM('service_sheet', 'Service Review Sheet', 'Service profit review for a month', 'svc_months.row_id', F(
  ('Month', 'svc_months.month'), ('Service type', 'svc_months.service'), ('Booked', 'svc_months.booked'), ('Attended', 'svc_months.sessions'), ('Revenue', 'svc_months.revenue'), ('Clinician pay', 'svc_months.clinician_pay'),
  ('Room cost', 'svc_months.room_cost'), ('Other cost', 'svc_months.other_cost'), ('Profit', 'svc_months.profit'), ('Margin', 'svc_months.margin'), ('Profit per session', 'svc_months.profit_per_session'), ('Verdict', 'svc_months.verdict'))),
 FORM('health_sheet', 'Health Check Sheet', 'Practice health check with five lights', 'health.hc_id', F(
  ('Month', 'health.month'), ('Months of expenses in cash', 'health.months_cover'), ('Booked share of cap', 'health.booked_share'), ('Pay share', 'health.pay_share'), ('Overhead share', 'health.overhead_share'), ('Profit margin', 'health.profit_margin'),
  ('Pay light', 'health.light_pay'), ('Overhead light', 'health.light_overhead'), ('Margin light', 'health.light_margin'), ('Cash light', 'health.light_cover'), ('Booked share light', 'health.light_booked'), ('Targets met (0 to 5)', 'health.score'), ('Verdict', 'health.verdict'))),
 FORM('hiring_sheet', 'Hiring Plan Sheet', 'Hiring scenario with first-year profit', 'hiring.hire_id', F(
  ('Scenario', 'hiring.scenario'), ('Pay type', 'hiring.pay_type'), ('Sessions a week at full volume', 'hiring.sessions_week'), ('Average charge', 'hiring.avg_charge'), ('Ramp-up months', 'hiring.ramp_months'), ('Monthly salary', 'hiring.salary'),
  ('Pay per session', 'hiring.session_pay'), ('Set-up cost', 'hiring.setup_cost'), ('Planned start', 'hiring.start_date'), ('Profit a month at half volume', 'hiring.ramp_profit'), ('Profit a month at full volume', 'hiring.full_profit'), ('First-year profit', 'hiring.yearly_profit'), ('Verdict', 'hiring.verdict'))),
 FORM('room_sheet', 'Room Option Sheet', 'Room option with payback', 'rooms_opt.opt_id', F(
  ('Option', 'rooms_opt.option'), ('Option kind', 'rooms_opt.kind'), ('Extra rent a month', 'rooms_opt.extra_rent'), ('Room hours a week', 'rooms_opt.room_hours'), ('Expected sessions a week', 'rooms_opt.expected_sessions'), ('Sublet hours a week', 'rooms_opt.sublet_hours'),
  ('Sublet rate an hour', 'rooms_opt.sublet_rate'), ('Set-up cost', 'rooms_opt.setup_cost'), ('Planned start', 'rooms_opt.start_date'), ('Profit a month', 'rooms_opt.contribution_month'), ('First-year profit', 'rooms_opt.yearly_profit'), ('Use share of room hours', 'rooms_opt.use_share'), ('Verdict', 'rooms_opt.verdict'))),
 FORM('setup_sheet', 'Set-up Cost Sheet', 'Set-up and equipment cost record', 'setup_costs.item_id', F(
  ('Item', 'setup_costs.item'), ('Date', 'setup_costs.date'), ('Cost', 'setup_costs.cost'), ('Years of use', 'setup_costs.years_of_use'), ('Monthly cost', 'setup_costs.monthly_cost'))),
 FORM('milestone_sheet', 'Growth Milestone Sheet', 'Growth milestone with owner and target date', 'milestones.ms_id', F(
  ('Milestone', 'milestones.milestone'), ('Target date', 'milestones.target_date'), ('Measure', 'milestones.measure'), ('Owner', 'milestones.owner'), ('Status', 'milestones.status'), ('Due check', 'milestones.due_flag'))),
]
assert len(forms) == 12

def D_(k, sheet, title, pick, paras, sign): return DOC(k, sheet, title, pick, paras, sign, NOTE)
documents = [
 D_('pnl_doc', 'Monthly Profit Statement', 'Monthly profit and loss statement', 'pnl.pl_id', [
  'Profit and loss statement of {set:company}, dated {today}. Month {col:pnl.month}.',
  'Revenue {col:pnl.revenue} (session revenue {col:pnl.session_revenue}, group revenue {col:pnl.group_revenue}, sublet income {col:pnl.sublet_income}, less write-offs {col:pnl.write_offs}) from {col:pnl.sessions} attended sessions.',
  'Costs {col:pnl.costs}: clinician pay {col:pnl.clinician_pay}, staff pay {col:pnl.staff_pay}, rent {col:pnl.rent}, other expenses {col:pnl.other_expenses}. Profit {col:pnl.profit}, a margin of {col:pnl.margin} against a wanted margin of {set:profit_target}. Margin check: {col:pnl.margin_flag}.',
  'Pay share of revenue {col:pnl.pay_share}, overhead share {col:pnl.overhead_share} ({col:pnl.ovh_flag}). Profit per attended session {col:pnl.profit_per_session}. Profit after the owner draw {col:pnl.kept}.',
  'Year to this month: revenue {col:pnl.ytd_revenue}, profit {col:pnl.ytd_profit}. Average profit of the 3 months before: {col:pnl.profit_3m}.'], ['Owner', 'Accountant']),
 D_('service_doc', 'Service Profit Report', 'Service profit report for one service and month', 'svc_months.row_id', [
  'Service profit report of {set:company}, dated {today}. Month {col:svc_months.month}. Service: {col:svc_months.service}.',
  'Booked {col:svc_months.booked}, attended {col:svc_months.sessions}. Revenue {col:svc_months.revenue}, clinician pay {col:svc_months.clinician_pay}, room cost {col:svc_months.room_cost}, other cost {col:svc_months.other_cost}.',
  'Profit {col:svc_months.profit}, margin {col:svc_months.margin}, profit per session {col:svc_months.profit_per_session}. Verdict: {col:svc_months.verdict}. The wanted margin is {set:profit_target}.',
  'Decisions for this service are written below.'], ['Owner']),
 D_('clinician_doc', 'Clinician Profit Report', 'Clinician profit report for one clinician and month', 'clin_months.row_id', [
  'Clinician profit report of {set:company}, dated {today}. Month {col:clin_months.month}. Clinician: {col:clin_months.clinician}.',
  'Revenue {col:clin_months.revenue}, clinician pay {col:clin_months.clinician_pay}, room cost {col:clin_months.room_cost}, other cost {col:clin_months.other_cost}.',
  'Profit {col:clin_months.profit}, margin {col:clin_months.margin}. The owner draws profit instead of a salary, so the owner row is read in that light.', 'Actions for the next review are written below.'], ['Owner']),
 D_('cashflow_doc', 'Cash Flow Report', 'Cash flow report for one month', 'cash.cash_id', [
  'Cash flow report of {set:company}, dated {today}. Month {col:cash.month}.',
  'Opening cash {col:cash.opening}. Cash in {col:cash.cash_in} (clients {col:cash.client_payments}, payers {col:cash.payer_payments}, sublets {col:cash.sublet_income}).',
  'Cash out {col:cash.cash_out}: staff pay {col:cash.staff_pay}, contractor pay {col:cash.contractor_pay}, rent {col:cash.rent}, other expenses {col:cash.other_expenses}, tax set-aside {col:cash.tax_set_aside}, owner draw {col:cash.owner_draw}.',
  'Net flow {col:cash.net_flow}. Closing cash {col:cash.closing}, which is {col:cash.months_cover} months of expenses. The cash floor is {set:cash_floor}. A safe owner draw is {col:cash.safe_draw}.'], ['Owner', 'Accountant']),
 D_('plan13_doc', '13-Week Cash Plan', 'Cash plan for one week', 'forecast.fc_id', [
  '13-week cash plan of {set:company}, dated {today}. Week {col:forecast.week}, starting {col:forecast.week_start}.',
  'Expected client payments {col:forecast.client_payments} and payer payments {col:forecast.payer_payments}. Expected pay {col:forecast.pay}, rent and costs {col:forecast.rent_costs}, tax set-aside {col:forecast.tax_set_aside}, owner draw {col:forecast.owner_draw}.',
  'Net flow {col:forecast.net}. Closing cash {col:forecast.closing} against a floor of {col:forecast.floor}: {col:forecast.below_floor}. The lowest closing cash of the 13 weeks is {col:forecast.lowest}.'], ['Owner']),
 D_('tax_doc', 'Tax Set-aside Summary', 'Tax set-aside summary for a month (ask adviser)', 'tax.tax_id', [
  'Tax set-aside summary of {set:company}, dated {today}. Month {col:tax.month}.',
  'Revenue {col:tax.revenue}, costs {col:tax.costs}, profit {col:tax.profit}. Set-aside share {col:tax.set_aside_pct}, amount {col:tax.set_aside}, due {col:tax.due_date}. Status: {col:tax.status}.',
  'This is a planning figure only. Confirm the share and the due dates with your adviser and check your own local rules.'], ['Owner', 'Accountant']),
 D_('health_doc', 'Practice Health Report', 'Practice health report for a month', 'health.hc_id', [
  'Practice health report of {set:company}, dated {today}. Month {col:health.month}.',
  'Pay share {col:health.pay_share} ({col:health.light_pay}), overhead share {col:health.overhead_share} ({col:health.light_overhead}), profit margin {col:health.profit_margin} ({col:health.light_margin}).',
  'Months of expenses in cash {col:health.months_cover} ({col:health.light_cover}), booked share of the session cap {col:health.booked_share} ({col:health.light_booked}).',
  'Targets met: {col:health.score} of 5. Verdict: {col:health.verdict}. Actions are written below.'], ['Owner']),
 D_('budget_doc', 'Yearly Budget Report', 'Yearly budget report for one category', 'budget.budget_id', [
  'Yearly budget report of {set:company}, dated {today}. Category: {col:budget.category}.',
  'Yearly budget {col:budget.yearly_budget}, monthly budget {col:budget.monthly_budget}, budget to date {col:budget.budget_to_date}. Spent this year {col:budget.spent}, left {col:budget.left}.',
  'Spent over or under the budget to date: {col:budget.variance}. Status: {col:budget.status}. Decisions are written below.'], ['Owner']),
 D_('hire_doc', 'Clinician Business Case', 'Business case for adding a clinician', 'hiring.hire_id', [
  'Business case of {set:company}, dated {today}. Scenario: {col:hiring.scenario}. Pay type: {col:hiring.pay_type}.',
  'Sessions a week at full volume {col:hiring.sessions_week}, average charge {col:hiring.avg_charge}, ramp-up {col:hiring.ramp_months} months, set-up cost {col:hiring.setup_cost}, planned start {col:hiring.start_date}.',
  'Profit a month at half volume {col:hiring.ramp_profit}, at full volume {col:hiring.full_profit}. First-year profit {col:hiring.yearly_profit}. Verdict: {col:hiring.verdict}.',
  'A new clinician can bill a third-party payer only after about {set:payer_wait_months} months; plan the cash for that wait.'], ['Owner']),
 D_('room_doc', 'Room Business Case', 'Business case for a room option', 'rooms_opt.opt_id', [
  'Room business case of {set:company}, dated {today}. Option: {col:rooms_opt.option} ({col:rooms_opt.kind}).',
  'Extra rent {col:rooms_opt.extra_rent} a month, {col:rooms_opt.room_hours} room hours a week, {col:rooms_opt.expected_sessions} expected sessions and {col:rooms_opt.sublet_hours} sublet hours a week at {col:rooms_opt.sublet_rate} an hour. Set-up cost {col:rooms_opt.setup_cost}, planned start {col:rooms_opt.start_date}.',
  'Profit a month {col:rooms_opt.contribution_month}, first-year profit {col:rooms_opt.yearly_profit}, use share {col:rooms_opt.use_share}. Verdict: {col:rooms_opt.verdict}.'], ['Owner']),
 D_('growth_doc', 'Growth Plan', 'Growth plan for one milestone', 'milestones.ms_id', [
  'Growth plan of {set:company}, dated {today}. Milestone: {col:milestones.milestone}.',
  'Target date {col:milestones.target_date}. Measure: {col:milestones.measure}. Owner: {col:milestones.owner}. Status: {col:milestones.status}. Due check: {col:milestones.due_flag}.',
  'Next steps are written below.'], ['Owner']),
 D_('year_doc', 'Year-end Pack', 'Year-end pack for a month', 'pnl.pl_id', [
  'Year-end pack of {set:company}, dated {today}. Month {col:pnl.month}.',
  'Revenue for the year to this month {col:pnl.ytd_revenue}; profit for the year to this month {col:pnl.ytd_profit}. Profit in this month {col:pnl.profit} (the same month last year: {col:pnl.profit_ly}).',
  'Pay share {col:pnl.pay_share}, overhead share {col:pnl.overhead_share}. Wanted margin {set:profit_target}; owner draw {set:owner_draw} a month. Check the tax set-aside with your adviser.'], ['Owner', 'Accountant']),
]
assert len(documents) == 12

def CS(k, title, table, start, steps): return _lib.CHK(k, title, table, start, steps)
checklists = [
 CS('c_close', 'Monthly Close Steps', 'pnl', 'pnl.month', [('Enter session, group and sublet revenue', 1), ('Enter clinician pay, staff pay, rent and other expenses', 2), ('Check the write-offs', 3), ('Read profit, margin and the checks', 4), ('Send the figures to the accountant', 5), ('Update the cash month', 5)]),
 CS('c_week', 'Weekly Cash Review Steps', 'forecast', 'forecast.week_start', [('Enter the receipts you expect', 0), ('Enter pay, rent and other costs', 0), ('Check the closing cash against the floor', 1), ('Move a payment if a week is below the floor', 2), ('Confirm the owner draw for the week', 2)]),
 CS('c_health', 'Monthly Health Check Steps', 'health', 'health.month', [('Enter months of expenses in cash', 1), ('Enter the booked share of the session cap', 1), ('Read the five lights', 2), ('Write one action for each red or amber light', 3), ('Share the verdict with the team', 5)]),
 CS('c_service', 'Service Review Steps', 'svc_months', 'svc_months.month', [('Enter booked and attended sessions per service', 2), ('Enter revenue, pay, room and other cost', 3), ('Read the Grow, Fix or Drop verdicts', 4), ('Open the Losing Service Fix tool for each Fix or Drop', 5), ('Decide and write the date of the decision', 7)]),
 CS('c_fix', 'Fixing a Weak Service Steps', 'fixes', 'fixes.decide_by', [('Compare the options in Service Fixes', -7), ('Check the break-even fee against the market band', -5), ('Talk to the clinician about the split or the minutes', -3), ('Choose one option', 0), ('Tell clients about a new fee in good time', 1), ('Review the profit per session after 3 months', 90)]),
 CS('c_tax', 'Tax Set-aside Transfer Steps', 'tax', 'tax.due_date', [('Check the set-aside amount with your adviser', -10), ('Check cash above the floor', -7), ('Transfer the set-aside', -3), ('Enter the paid date', 0), ('Send the receipt to the accountant', 2)]),
 CS('c_cash', 'Cash Month Close Steps', 'cash', 'cash.month', [('Enter opening cash and every receipt', 1), ('Enter every payment', 2), ('Check closing cash against the bank', 3), ('Read months of expenses in cash', 4), ('Decide the owner draw with the Safe Owner Draw tool', 5)]),
 CS('c_budget', 'Yearly Budget Steps', 'forecast12', 'forecast12.month', [('Enter the sessions you expect', -20), ('Enter the average charge', -20), ('Enter pay, rent and other costs', -15), ('Check the margin against the target', -10), ('Compare with the 12-month Profit Forecast tool', -7)]),
 CS('c_hire', 'Hiring Decision Steps', 'hiring', 'hiring.start_date', [('Run the Hire a Clinician Business Case tool', -60), ('Check cash for the months before payer billing', -55), ('Agree pay terms and the ramp-up', -45), ('Plan the room, laptop and accounts', -30), ('Make the offer', -21), ('Review the first 3 months against the plan', 90)]),
 CS('c_room', 'Adding a Room Steps', 'rooms_opt', 'rooms_opt.start_date', [('Run the Add a Room and Online Capacity tools', -60), ('Talk to the landlord about the rent', -45), ('Check the use share target', -40), ('Plan cleaning and set-up', -20), ('Open the room and track the use', 0), ('Review payback after 3 months', 90)]),
 CS('c_roomcost', 'Room Cost Review Steps', 'room_costs', 'room_costs.month', [('Enter rent, cleaning and utilities', 1), ('Enter open hours and used hours', 2), ('Read the use share', 3), ('Close or sublet hours that stay unused', 5)]),
 CS('c_year', 'Year-end Steps', 'tax', 'tax.month', [('Close the last month', 5), ('Compare the year with the budget', 8), ('Check the tax set-aside with your adviser', 10), ('Set the targets for next year in Start', 12), ('Enter the next 12 months budget', 14)]),
]
assert len(checklists) == 12

def NMC(k, n): return CA(k, 'Name to greet', 'text', 'IFERROR(INDEX({range:team.name},%d)&"","")' % n, 20)
NAMES = {'owner_name': 1, 'coordinator_name': 7, 'accountant_name': 8, 'supervisor_name': 9, 'it_name': 10, 'landlord_name': 11, 'cleaner_name': 12}
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
 M('o_profit', 'Owner: profit for the month', 'pnl', 'pnl.owner_phone', 'Hello {owner_name}, the profit for the month starting {month} is {profit} on revenue of {revenue}, a margin of {margin}. Check: {margin_flag}. {company}'),
 M('o_overhead', 'Owner: overhead check', 'pnl', 'pnl.owner_phone', 'Hello {owner_name}, overhead for the month starting {month} is {overhead_share} of revenue ({ovh_flag}). Please review the cost lines. {company}'),
 M('o_service', 'Owner: a service verdict', 'svc_months', 'svc_months.owner_phone', 'Hello {owner_name}, {service} in the month starting {month}: profit {profit}, {profit_per_session} per session. Verdict: {verdict}. {company}'),
 M('o_health', 'Owner: health check result', 'health', 'health.owner_phone', 'Hello {owner_name}, the health check for the month starting {month} meets {score} of 5 targets. Verdict: {verdict}. {company}'),
 M('o_lights', 'Owner: cash and margin lights', 'health', 'health.owner_phone', 'Hello {owner_name}, for the month starting {month} the cash light is {light_cover} and the margin light is {light_margin}. {company}'),
 M('o_cash', 'Owner: closing cash and safe draw', 'cash', 'cash.owner_phone', 'Hello {owner_name}, closing cash for the month starting {month} is {closing}, which is {months_cover} months of expenses. A safe owner draw is {safe_draw}. {company}'),
 M('o_taxmove', 'Owner: move the tax set-aside', 'cash', 'cash.owner_phone', 'Hello {owner_name}, please move the tax set-aside of {tax_set_aside} for the month starting {month} into the separate account. {company}'),
 M('o_week', 'Owner: closing cash for a week', 'forecast', 'forecast.owner_phone', 'Hello {owner_name}, in {week} (from {week_start}) the closing cash is forecast at {closing}. Floor check: {below_floor}. {company}'),
 M('o_lowest', 'Owner: lowest cash in 13 weeks', 'forecast', 'forecast.owner_phone', 'Hello {owner_name}, the lowest closing cash in the next 13 weeks is {lowest}, against a floor of {floor}. {company}'),
 M('o_tax', 'Owner: tax set-aside due', 'tax', 'tax.owner_phone', 'Hello {owner_name}, the tax set-aside for the month starting {month} is {set_aside}, due {due_date}. Status: {status}. Confirm the share with your adviser. {company}'),
 M('o_owed', 'Owner: money owed to the practice', 'owed', 'owed.owner_phone', 'Hello {owner_name}, the practice is owed {total} at the end of the month starting {month}, which is {days_of_revenue} days of revenue. {company}'),
 M('o_claims', 'Owner: chase open payer claims', 'owed', 'owed.owner_phone', 'Hello {owner_name}, open payer claims are {open_claims} at the end of the month starting {month}. Please chase the oldest first. {company}'),
 M('o_bill', 'Owner: a bill is due', 'bills', 'bills.owner_phone', 'Hello {owner_name}, the bill "{item}" of {amount} is due on {due_date}, in {days_to_due} days. {company}'),
 M('o_budget', 'Owner: a category is over budget', 'budget', 'budget.owner_phone', 'Hello {owner_name}, {category} is {variance} against the budget to date. Status: {status}. {company}'),
 M('o_fix', 'Owner: a service fix option', 'fixes', 'fixes.owner_phone', 'Hello {owner_name}, for {service} the option "{option}" gives {after} profit per session. Result: {result}. Decide by {decide_by}. {company}'),
 M('o_hire', 'Owner: a hiring scenario', 'hiring', 'hiring.owner_phone', 'Hello {owner_name}, the hiring scenario "{scenario}" has a first-year profit of {yearly_profit}. Verdict: {verdict}. {company}'),
 M('o_room', 'Owner: a room option', 'rooms_opt', 'rooms_opt.owner_phone', 'Hello {owner_name}, the room option "{option}" pays back in {payback_months} months. Verdict: {verdict}. {company}'),
 M('o_budget12', 'Owner: budget for a coming month', 'forecast12', 'forecast12.owner_phone', 'Hello {owner_name}, the budget for the month starting {month} shows profit of {profit}, a margin of {margin}. {company}'),
 M('o_mile', 'Owner: a growth milestone', 'milestones', 'milestones.owner_phone', 'Hello {owner_name}, the milestone "{milestone}" is due on {target_date}. Due check: {due_flag}. {company}'),
 M('a_cash', 'Accountant: figures for the month', 'cash', 'cash.accountant_phone', 'Hello {accountant_name}, the closing cash for the month starting {month} is {closing} and the net flow is {net_flow}. Please check the figures. {company}'),
 M('a_draw', 'Accountant: record the owner draw', 'cash', 'cash.accountant_phone', 'Hello {accountant_name}, the owner draw for the month starting {month} was {owner_draw}. Please record it. {company}'),
 M('a_pnl', 'Accountant: profit and loss ready', 'pnl', 'pnl.accountant_phone', 'Hello {accountant_name}, the profit and loss for the month starting {month} shows revenue of {revenue} and profit of {profit}. Please check it before the close. {company}'),
 M('a_tax', 'Accountant: confirm the set-aside', 'tax', 'tax.accountant_phone', 'Hello {accountant_name}, please confirm the tax set-aside for the month starting {month}: {set_aside}, due {due_date}. {company}'),
 M('a_setup', 'Accountant: how to record equipment', 'setup_costs', 'setup_costs.accountant_phone', 'Hello {accountant_name}, we bought {item} for {cost} on {date}, to be used for {years_of_use} years. Please advise how to record it. {company}'),
 M('c_expense', 'Coordinator: check an expense', 'expenses', 'expenses.coordinator_phone', 'Hello {coordinator_name}, please check expense {expense_id} of {amount} paid to {paid_to} on {date}. {company}'),
 M('c_category', 'Coordinator: check the receipts', 'expenses', 'expenses.coordinator_phone', 'Hello {coordinator_name}, the {category} spend this year is {category_year}. Please check that every receipt is filed. {company}'),
 M('c_bill', 'Coordinator: pay a bill', 'bills', 'bills.coordinator_phone', 'Hello {coordinator_name}, please pay "{item}" of {amount} by {due_date}. {company}'),
 M('s_budget', 'Supervisor: supervision budget', 'budget', 'budget.supervisor_phone', 'Hello {supervisor_name}, please confirm the {category} costs booked this year; we are {variance} against the budget to date. {company}'),
 M('l_use', 'Landlord: room use and rent', 'room_costs', 'room_costs.landlord_phone', 'Hello {landlord_name}, this is {company}. Our rooms were used for {use_share} of the open hours in the month starting {month}. Could we talk about the rent?'),
 M('l_cost', 'Landlord: room cost breakdown', 'room_costs', 'room_costs.landlord_phone', 'Hello {landlord_name}, our room costs for the month starting {month} were {total_cost}. Please send us the breakdown of rent, cleaning and utilities. {company}'),
 M('l_option', 'Landlord: a second room', 'rooms_opt', 'rooms_opt.landlord_phone', 'Hello {landlord_name}, we are looking at "{option}" with an extra rent of {extra_rent} a month from {start_date}. Can we talk? {company}'),
 M('x_clean', 'Cleaner: extra cleaning for a new room', 'rooms_opt', 'rooms_opt.cleaner_phone', 'Hello {cleaner_name}, we may add room capacity ("{option}", planned start {start_date}). Please tell us what extra cleaning it needs. {company}'),
 M('i_laptop', 'IT support: kit for a new clinician', 'hiring', 'hiring.it_phone', 'Hello {it_name}, we may add a clinician (scenario "{scenario}", planned start {start_date}). Please plan a laptop and accounts. {company}'),
 M('k_fix', 'Clinician: a service under review', 'fixes', 'fixes.clinician_phone', 'Hello {clinician}, we are reviewing {service}. The option "{option}" could change pay terms or minutes. Can we talk this week? {company}'),
]
assert len(messages) == 34, len(messages)

# name columns, practice name and the extra phone columns the messages use
import re
need = {}
for m in messages:
    need.setdefault(m['table'], set()).update(re.findall(r'\{(\w+)\}', m['text']))
tb = {t['key']: t for t in tables}
def addcol(t, c):
    if not any(x['key'] == c['key'] for x in t['columns']): t['columns'].append(c)
addcol(tb['pnl'], PH('owner_phone', 1)); addcol(tb['pnl'], PH('accountant_phone', 8))
for tk, ph in need.items():
    t = tb[tk]
    for p in ph:
        if p == 'company': addcol(t, CA('company', 'Practice', 'text', '{set:company}&""', 24))
        elif p in NAMES: addcol(t, NMC(p, NAMES[p]))
for m in messages:
    t = tb[m['table']]; keys = {c['key'] for c in t['columns']}
    for p in re.findall(r'\{(\w+)\}', m['text']): assert p in keys, (m['key'], p)
    assert m['phone'].split('.')[1] in keys, m['key']

LMS = 'DATE(YEAR({today}),MONTH({today})-1,1)'
def LMV(c): return 'SUMIFS({range:pnl.%s},{range:pnl.month},%s)' % (c, LMS)
LASTC = lambda c: 'INDEX({range:cash.%s},MATCH(MAX({range:cash.month}),{range:cash.month},0))' % c
LASTO = lambda c: 'INDEX({range:owed.%s},MATCH(MAX({range:owed.month}),{range:owed.month},0))' % c
P3 = 'AVERAGEIFS({range:pnl.profit},{range:pnl.month},">="&DATE(YEAR({today}),MONTH({today})-4,1),{range:pnl.month},"<"&%s)' % LMS
LYP = 'SUMIFS({range:pnl.profit},{range:pnl.month},DATE(YEAR({today})-1,MONTH({today})-1,1))'
W12 = '{range:svc_months.month},">="&DATE(YEAR({today}),MONTH({today})-12,1),{range:svc_months.month},"<"&DATE(YEAR({today}),MONTH({today}),1)'
ARR12 = 'SUMIFS({range:svc_months.profit},{range:svc_months.service},{range:services.service},%s)' % W12
kpis = [
 KPI('Revenue last month', LMV('revenue'), 'money'),
 KPI('Profit last month', LMV('profit'), 'money', alert={"when": "< 0", "style": "bad"}),
 KPI('Profit margin last month', 'IFERROR(%s/%s,0)' % (LMV('profit'), LMV('revenue')), 'pct', alert={"when": "< {set:profit_target}", "style": "warn"}),
 KPI('Pay share of revenue last month', 'IFERROR((%s+%s)/%s,0)' % (LMV('clinician_pay'), LMV('staff_pay'), LMV('revenue')), 'pct', alert={"when": "> {set:pay_share_target}+{set:target_tolerance}", "style": "warn"}),
 KPI('Overhead share of revenue last month', 'IFERROR((%s+%s)/%s,0)' % (LMV('rent'), LMV('other_expenses'), LMV('revenue')), 'pct', alert={"when": "> {set:overhead_target}+{set:target_tolerance}", "style": "warn"}),
 KPI('Profit per attended session last month', 'IFERROR(%s/%s,0)' % (LMV('profit'), LMV('sessions')), 'money'),
 KPI('Profit after the owner draw last month', '%s-{set:owner_draw}' % LMV('profit'), 'money', alert={"when": "< 0", "style": "bad"}),
 KPI('Revenue, year to date', 'SUMIFS({range:pnl.revenue},{range:pnl.month},">="&DATE(YEAR({today}),1,1),{range:pnl.month},"<"&DATE(YEAR({today}),MONTH({today}),1))', 'money'),
 KPI('Profit, year to date', 'SUMIFS({range:pnl.profit},{range:pnl.month},">="&DATE(YEAR({today}),1,1),{range:pnl.month},"<"&DATE(YEAR({today}),MONTH({today}),1))', 'money'),
 KPI('Profit against the 3 months before', '%s-IFERROR(%s,0)' % (LMV('profit'), P3), 'money'),
 KPI('Profit against the same month last year', '%s-%s' % (LMV('profit'), LYP), 'money'),
 KPI('Cash now', LASTC('closing'), 'money', alert={"when": "< {set:cash_floor}", "style": "bad"}),
 KPI('Months of expenses in cash', LASTC('months_cover'), 'num', alert={"when": "< {set:reserve_low_months}", "style": "warn"}),
 KPI('Safe owner draw this month', LASTC('safe_draw'), 'money'),
 KPI('Lowest cash in the next 13 weeks', 'MIN({range:forecast.closing})', 'money', alert={"when": "< {set:cash_floor}", "style": "bad"}),
 KPI('Weeks below the cash floor', 'COUNTIFS({range:forecast.below_floor},%s)' % vd('Below the floor'), 'int', alert={"when": "> 0", "style": "bad"}),
 KPI('Money owed to the practice', LASTO('total'), 'money'),
 KPI('Days of revenue owed', LASTO('days_of_revenue'), 'num', alert={"when": "> 45", "style": "warn"}),
 KPI('Bills due in the next 7 days', 'SUMIFS({range:bills.amount},{range:bills.due_date},">="&{today},{range:bills.due_date},"<="&{today}+7)', 'money'),
 KPI('Tax set-aside still to transfer', 'SUMIFS({range:tax.set_aside},{range:tax.status},"<>"&%s)' % tok('taxst', 'Paid'), 'money'),
 KPI('Days to the next tax due date', 'IFERROR(MIN({range:tax.days_to_due}),0)', 'int'),
 KPI('Categories over budget', 'COUNTIFS({range:budget.status},%s)' % vd('Over budget'), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Overspend to date on budget lines', 'SUMIFS({range:budget.variance},{range:budget.variance},">0")', 'money'),
 KPI('Weakest service profit, last 12 months', 'SUMPRODUCT(MIN(%s+({range:services.service}="")*1000000000))' % ARR12, 'money'),
 KPI('Services to fix or drop last month', 'COUNTIFS({range:svc_months.month},%s,{range:svc_months.verdict},%s)+COUNTIFS({range:svc_months.month},%s,{range:svc_months.verdict},%s)' % (LMS, vd('Fix'), LMS, vd('Drop')), 'int', alert={"when": "> 0", "style": "warn"}),
 KPI('Room use share last month', 'IFERROR(SUMIFS({range:room_costs.used_hours},{range:room_costs.month},%s)/SUMIFS({range:room_costs.open_hours},{range:room_costs.month},%s),0)' % (LMS, LMS), 'pct', alert={"when": "< {set:room_use_target}", "style": "warn"}),
 KPI('Cost per used room hour last month', 'IFERROR(SUMIFS({range:room_costs.total_cost},{range:room_costs.month},%s)/SUMIFS({range:room_costs.used_hours},{range:room_costs.month},%s),0)' % (LMS, LMS), 'money'),
 KPI('Hiring scenarios ready to go', 'COUNTIFS({range:hiring.verdict},%s)' % vd('Hire now'), 'int'),
 KPI('Room options ready to go', 'COUNTIFS({range:rooms_opt.verdict},%s)' % vd('Add the room'), 'int'),
 KPI('Milestones overdue or due soon', 'COUNTIFS({range:milestones.due_flag},%s)+COUNTIFS({range:milestones.due_flag},%s)' % (vd('Overdue'), vd('Due soon')), 'int', alert={"when": "> 0", "style": "warn"}),
]
assert len(kpis) == 30
dashboard = {"title": "Practice Profit Dashboard", "kpis": kpis,
 "monthly": {"title": "Revenue, costs and profit by month", "date": "pnl.month", "series": [
   {"label": "Revenue", "sum": "pnl.revenue", "date": "pnl.month"}, {"label": "Costs", "sum": "pnl.costs", "date": "pnl.month"}, {"label": "Profit", "sum": "pnl.profit", "date": "pnl.month"}]},
 "breakdowns": [{"title": "Expenses by category", "by": "expenses.category", "agg": "sum", "value": "expenses.amount"}, {"title": "Profit by service type", "by": "svc_months.service", "agg": "sum", "value": "svc_months.profit"},
                {"title": "Profit by clinician", "by": "clin_months.clinician", "agg": "sum", "value": "clin_months.profit"}]}
insights = {"filters": [{"label": "Clinician", "list": "clin"}, {"label": "Service", "list": "svcall"}],
 "gauges": [
  {"title": "Months at or above the profit target", "num": AGG('count', 'pnl', where=[('margin_flag', '=', vd('Above target'))]), "den": AGG('count', 'pnl')},
  {"title": "Service months with a profit", "num": AGG('count', 'svc_months', where=[('profit', '>', 0)]), "den": AGG('count', 'svc_months')},
  {"title": "Cash months at or above the floor", "num": AGG('count', 'cash', where=[('closing', '>=', '{set:cash_floor}')]), "den": AGG('count', 'cash')},
  {"title": "Months with enough cash cover", "num": AGG('count', 'cash', where=[('months_cover', '>=', '{set:cover_min_months}')]), "den": AGG('count', 'cash')},
  {"title": "Tax set-asides paid", "num": AGG('count', 'tax', where=[('status', '=', tok('taxst', 'Paid'))]), "den": AGG('count', 'tax', where=[('status', '<>', tok('taxst', 'Upcoming'))])},
  {"title": "Months with overhead not heavy", "num": AGG('count', 'pnl', where=[('ovh_flag', '<>', vd('Heavy'))]), "den": AGG('count', 'pnl')}],
 "charts": [
  CHART('Revenue per month', 'column', 'month', [AGG('sum', 'pnl', 'pnl.revenue', date='pnl.month', label='Revenue')]),
  CHART('Profit per month', 'column', 'month', [AGG('sum', 'pnl', 'pnl.profit', date='pnl.month', label='Profit')]),
  CHART('Revenue, costs and profit', 'column', 'month', [AGG('sum', 'pnl', 'pnl.revenue', date='pnl.month', label='Revenue'), AGG('sum', 'pnl', 'pnl.costs', date='pnl.month', label='Costs'), AGG('sum', 'pnl', 'pnl.profit', date='pnl.month', label='Profit')]),
  CHART('Profit margin per month', 'column', 'month', [AGG('sum', 'pnl', 'pnl.margin', date='pnl.month', label='Profit margin')]),
  CHART('Pay share and overhead share', 'column', 'month', [AGG('sum', 'pnl', 'pnl.pay_share', date='pnl.month', label='Pay share'), AGG('sum', 'pnl', 'pnl.overhead_share', date='pnl.month', label='Overhead share')]),
  CHART('Profit by service type', 'bar', 'svc_months.service', [AGG('sum', 'svc_months', 'svc_months.profit', label='Profit')]),
  CHART('Revenue by service type', 'bar', 'svc_months.service', [AGG('sum', 'svc_months', 'svc_months.revenue', label='Revenue')]),
  CHART('Behaviour therapy profit per month', 'column', 'month', [AGG('sum', 'svc_months', 'svc_months.profit', date='svc_months.month', where=[('service', '=', tok('svcall', 'Behaviour therapy'))], label='Behaviour therapy profit')]),
  CHART('Profit by clinician', 'bar', 'clin_months.clinician', [AGG('sum', 'clin_months', 'clin_months.profit', label='Profit')]),
  CHART('Revenue by clinician', 'bar', 'clin_months.clinician', [AGG('sum', 'clin_months', 'clin_months.revenue', label='Revenue')]),
  CHART('Expenses by category', 'bar', 'expenses.category', [AGG('sum', 'expenses', 'expenses.amount', label='Expenses')]),
  CHART('Expenses per month', 'column', 'month', [AGG('sum', 'expenses', 'expenses.amount', date='expenses.date', label='Expenses')]),
  CHART('Budget against spending by category', 'bar', 'budget.category', [AGG('sum', 'budget', 'budget.yearly_budget', label='Yearly budget'), AGG('sum', 'budget', 'budget.spent', label='Spent this year')]),
  CHART('Closing cash per month', 'column', 'month', [AGG('sum', 'cash', 'cash.closing', date='cash.month', label='Closing cash')]),
  CHART('Cash in and cash out', 'column', 'month', [AGG('sum', 'cash', 'cash.cash_in', date='cash.month', label='Cash in'), AGG('sum', 'cash', 'cash.cash_out', date='cash.month', label='Cash out')]),
  CHART('Months of expenses in cash', 'column', 'month', [AGG('sum', 'cash', 'cash.months_cover', date='cash.month', label='Months of expenses')]),
  CHART('13-week closing cash', 'bar', 'forecast.week', [AGG('sum', 'forecast', 'forecast.closing', label='Closing cash')]),
  CHART('Tax set-aside per month', 'column', 'month', [AGG('sum', 'tax', 'tax.set_aside', date='tax.month', label='Tax set-aside')]),
  CHART('Money owed per month', 'column', 'month', [AGG('sum', 'owed', 'owed.total', date='owed.month', label='Money owed')]),
  CHART('Cost per used room hour', 'column', 'month', [AGG('sum', 'room_costs', 'room_costs.per_used_hour', date='room_costs.month', label='Cost per used hour')]),
  CHART('First-year profit by hiring pay type', 'bar', 'hiring.pay_type', [AGG('avg', 'hiring', 'hiring.yearly_profit', label='First-year profit')]),
  CHART('First-year profit by room option', 'bar', 'rooms_opt.kind', [AGG('avg', 'rooms_opt', 'rooms_opt.yearly_profit', label='First-year profit')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
 {"name": "Practice health check with five traffic lights", "why": "pay share, overhead, margin, cash cover and booked share against your targets, with the score and the change from your own history", "where": "Is the Practice Healthy"},
 {"name": "Profit and loss with owner pay plus profit", "why": "every month shows revenue, costs, profit, margin and the same month last year", "where": "Practice P&L Statement"},
 {"name": "Profit per service type with Grow, Fix or Drop", "why": "each service type is ranked by profit and judged against your target margin", "where": "Profit per Service Type"},
 {"name": "Losing service fix finder", "why": "profit per session after a fee rise, split cut or saving, the break-even fee and the sessions a week needed", "where": "Losing Service Fix"},
 {"name": "Fee check against your local band", "why": "the list fee that keeps your margin, where your fee sits in the band and five fee steps", "where": "Is My Fee Right"},
 {"name": "Profit per clinician by pay type", "why": "salary, split or per-session pay compared in one number, with the rank among your clinicians", "where": "Profit per Clinician"},
 {"name": "13-week cash forecast with scenarios", "why": "base, best and worst weeks from your own history with the lowest point against the cash floor", "where": "13-week Cash Flow Forecast"},
 {"name": "Safe owner draw solver", "why": "the draw that keeps cash above the floor after the tax set-aside and the bills of the next 4 weeks", "where": "Safe Owner Draw"},
 {"name": "Hire a clinician business case", "why": "first-year profit, the break-even month and the cash tied up before payer billing starts", "where": "Hire a Clinician Business Case"},
 {"name": "Add a room or go online", "why": "payback months, use share and the cheaper way to add sessions", "where": "Online Capacity or a New Room"},
 {"name": "Budget against actual by category", "why": "budget to date, spend, year-end projection and the three largest overspends", "where": "Budget against Actual"},
 {"name": "12-month profit forecast", "why": "sessions from your last 12 months and their trend give yearly revenue, profit and closing cash in three scenarios", "where": "12-month Profit Forecast"}]
competitors = [
 {"what": "free budget templates", "lacks": "list income and costs but have no per-service profit, clinician pay types or cash floor"},
 {"what": "subscription accounting software", "lacks": "keep books but do not answer whether to raise a fee, hire a clinician or add a room"},
 {"what": "single-sheet profit and loss files", "lacks": "show last month only, with no 13-week forecast, scenarios or owner draw check"},
 {"what": "generic cash flow spreadsheets", "lacks": "use blank rows you fill yourself and know nothing about payer waits or session pay"},
 {"what": "advisor reports once a year", "lacks": "arrive after the decision, with no weekly view of margin, cash cover or the weakest service"}]
guide = [
 'Open Start and type your practice name and your targets in the yellow cells: wanted profit margin, overhead share, pay share, cash floor, owner draw and the months of expenses you want in cash.',
 'Check Team and Services. An employed clinician is paid a salary, a contract (self-employed) clinician a share of each session, an associate (works under supervision) per session. The owner draws profit instead of a salary.',
 'Fill Profit by Month with revenue, pay, rent and other expenses, then Cash Months with what really moved in the bank. Profit, margin, pay share, overhead share and the history rows fill in by themselves.',
 'Log expenses on Expenses and set a yearly budget for each category. Budget by Category shows the budget to date, what was spent and a Within budget, Watch or Over budget status.',
 'Enter service and clinician profit by month. Each service type gets a Grow, Fix or Drop verdict; open the Losing Service Fix tool for a weak one.',
 'Use the 13-week Cash Flow Forecast to see the lowest week against your cash floor, and the Safe Owner Draw tool before you pay yourself. The tax set-aside is a planning figure: confirm the share with your adviser.',
 'Hiring Scenarios and Room Options compare ways to grow: first-year profit, break-even month and payback. A new clinician can bill a third-party payer (an insurer, an employer scheme or a public body) only after a wait; plan the cash.',
 'Check your own local rules on tax, employment and billing. The workbook gives sample wording and planning figures only.',
 f'Use the {len(tools)} decision tools: each ends with a verdict and a what-if table. Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready messages.',
 'Why a workbook: one flat price, no per-clinician fee, and your data stays with you in your own file. The workbook holds status and money figures only, never note content.',
 'Read the Practice Profit Dashboard and Charts every month: margin, pay share, overhead, cash cover, the weakest service and the next tax date.']
listing = {"title": "Therapy Practice Finance Excel Template: Profit, Cash Flow Forecast, Budget, Owner Draw, Hiring and Room Business Case",
 "headline": "Know your profit, protect your cash and plan growth in one Excel file",
 "tags": ["therapy practice", "practice profit", "cash flow forecast", "counselling practice", "practice management", "excel template", "budget template", "private practice", "owner draw", "profit and loss", "group practice", "break even", "clinic finance"],
 "description": ("Run the money side of a small group practice in one Excel workbook. Built for talking therapists and counsellors: an owner-clinician, employed clinicians, contract (self-employed) clinicians, an associate who works under supervision and a front-desk coordinator.\n\n"
  "Profit by Month works out revenue, costs, profit, margin, pay share and overhead share and compares each month with your own history. Service Profit by Month gives each service type a Grow, Fix or Drop verdict; Clinician Profit by Month shows profit per clinician. "
  "Cash Months, the 13-week Cash Flow Forecast and Bills Due show the lowest week against your cash floor; Tax Set-aside, Budget by Category, Room Costs, Hiring Scenarios, Room Options and the Next 12 Months Budget plan the year.\n\n"
  f"{len(tools)} decision tools answer the questions owners ask with a verdict and a what-if table: practice health, profit and loss, profit per service and clinician, losing service fix, fee check, break-even sessions, cash cover, safe owner draw, tax set-aside, hiring and room business cases, budget against actual and a 12-month profit forecast. "
  f"Print {len(forms)} sheets and {len(documents)} reports, follow {len(checklists)} checklists and send {len(messages)} ready messages.\n\n"
  "This is part eight of the Therapy Private Practice suite. A standard .xlsx workbook with no macros and no subscription, one flat price with no per-clinician fee, your data stays with you, 15 languages in one purchase, with a demo copy full of sample data. Tax figures are planning figures only: confirm them with your adviser and check your own local rules. The workbook holds money figures only, never session notes or diagnoses, and it does not promise results."),
 "features": ["Profit and loss by month with your own history", "Grow, Fix or Drop verdict per service type", "13-week cash forecast with scenarios", "Safe owner draw and cash cover checks", "Budget against actual by category",
              "Hiring and room business cases", f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts",
              f"{len(messages)} ready text messages", "Tax set-aside planner (confirm with your adviser)", "One flat price, your data stays with you"]}

# ---- limits: row counts, hints, near-identical money columns -------------------------------------------------------------------------------
def cut(h, n=200):
    if len(h) <= n: return h
    h = h[:n]
    i = max(h.rfind('; '), h.rfind(', '), h.rfind(' and '))
    return h[:i].rstrip(' ,;') + '.'
for t in tables:
    t['rows'] = max(50, t['rows']); t['hint'] = cut(t['hint'])
for t in tools: t['hint'] = cut(t['hint'])
INTCOLS = {('pnl', 'rent'), ('room_costs', 'rent'), ('room_costs', 'cleaning'), ('cash', 'rent'), ('cash', 'owner_draw'), ('forecast', 'rent_costs'), ('forecast', 'tax_set_aside'), ('forecast', 'owner_draw'), ('owed', 'unpaid_sublets'),
           ('fixes', 'fee_change'), ('fixes', 'materials_change'), ('fixes', 'materials'), ('fixes', 'fixed_month'), ('hiring', 'salary'), ('rooms_opt', 'sublet_rate'), ('forecast12', 'avg_charge'), ('forecast12', 'rent'),
           ('team', 'monthly_salary'), ('team', 'session_rate'), ('team', 'hourly_rate')}
for t in tables:
    for c in t['columns']:
        if (t['key'], c['key']) in INTCOLS and c['type'] == 'money': c['type'] = 'int'
s = _lib.spec(id=f'{SUITE}-p8', slug='therapy-practice-finance', profession='Therapy Private Practice', name='Practice Profit, Cash Flow and Growth',
         tagline='Know your profit, protect your cash and plan growth', price_usd=29, colors={"primary": "#2F5D62", "accent": "#A7C4BC"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard,
         forms=forms, guide=guide, listing=listing, insights=insights, suite={"key": SUITE, "part": 8, "of": 8, "focus": "Practice profit, cash flow and growth"}, signature=signature, competitors=competitors,
         tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'th8.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']), 'gauges', len(insights['gauges']), 'name', len(s['name']), 'title', len(listing['title']))
