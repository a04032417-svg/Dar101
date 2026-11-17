"""Household Finance suite - part 5: Savings Goals and Sinking Funds."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf5_lists import *
from hf5_tables import *
from hf5_lists import vlists, LITX
from hf5_tables import R, MS, DEP, SPEND, EMERG, SINK, GL, CT, AC, RT, IC, CG, CM, EAVG, EBAL, PPY
from hf5_tools import tools
import hf5_data as D

SUITE = 'fx-20261116-household-finance'
NOTE = "Sample wording: adapt it to your own household."
for _t in tables: _t['rows'] = max(50, _t['rows'])
def F(*pairs): return [FV(a, b) for a, b in pairs]
IDCOL = {'goals': 'goal_id', 'contributions': 'contribution_id', 'sinking_spend': 'rank', 'goal_changes': 'change_id', 'annual_costs': 'item_id', 'emergency_months': 'month', 'retirement': 'rt_id',
         'retirement_summary': 'row_id', 'income': 'income_id', 'contrib_goals': 'goal', 'annual_months': 'month', 'goal_funding': 'goal', 'emergency_plan': 'months', 'contrib_months': 'month'}
def LK(t, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, IDCOL[t])
def GLN(t, c): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (GL(c), LK(t, 'goal'), GL('goal'))
THISYR = 'DATE(YEAR({today}),1,1)'

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('goal_sheet', 'Goal Sheet', 'One goal and where it stands', 'goals.goal_id', F(
        ('Goal', 'goals.goal'), ('Kind', 'goals.kind'), ('Account', 'goals.account'), ('Target', 'goals.target'), ('Target date', 'goals.target_date'), ('Monthly amount', 'goals.monthly_amount'),
        ('Saved so far', 'goals.saved'), ('Priority', 'goals.priority'), ('Left to save', 'goals.left'), ('Days left', 'goals.days_left'), ('Needed a month', 'goals.needed_month'),
        ('Set aside per paycheck', 'goals.per_paycheck'), ('Behind by at the date', 'goals.behind_by'), ('Status', 'goals.status')) + [
        FF('Share saved', 'IFERROR(%s/%s,0)' % (LK('goals', 'saved'), LK('goals', 'target')), 'pct'),
        FF('Share of all savings in goals', 'IFERROR(%s/SUM({range:goals.saved}),0)' % LK('goals', 'saved'), 'pct')]),
    FORM('contribution_sheet', 'Contribution Sheet', 'One deposit or spend', 'contributions.contribution_id', F(
        ('Date', 'contributions.date'), ('Goal', 'contributions.goal'), ('Kind', 'contributions.kind'), ('Amount', 'contributions.amount'), ('Goal account', 'contributions.account'),
        ('From account', 'contributions.from_account'), ('Month', 'contributions.month'), ('Goal ID', 'contributions.goal_id'), ('Signed amount', 'contributions.signed')) + [
        FF('Deposits to this goal, last 12 months', 'SUMIFS({range:contributions.amount},{range:contributions.goal},%s,{range:contributions.kind},%s,{range:contributions.date},">="&EDATE({today},-12))' % (LK('contributions', 'goal'), DEP), 'money'),
        FF('This deposit, share of target', 'IFERROR(%s/IFERROR(INDEX(%s,MATCH(%s,%s,0)),0),0)' % (LK('contributions', 'amount'), GL('target'), LK('contributions', 'goal'), GL('goal')), 'pct')]),
    FORM('spend_sheet', 'Sinking Fund Spend Sheet', 'One spend from a goal', 'sinking_spend.rank', F(
        ('Date', 'sinking_spend.date'), ('Goal', 'sinking_spend.goal'), ('Amount spent', 'sinking_spend.amount'), ('Bought from', 'sinking_spend.payee'), ('Fund balance after', 'sinking_spend.balance_after'),
        ('Days ago', 'sinking_spend.days_ago')) + [
        FF('Share of the goal target', 'IFERROR(%s/IFERROR(INDEX(%s,MATCH(%s,%s,0)),0),0)' % (LK('sinking_spend', 'amount'), GL('target'), LK('sinking_spend', 'goal'), GL('goal')), 'pct'),
        FF('Spends from this goal, last 12 months', 'SUMIFS({range:contributions.amount},{range:contributions.goal},%s,{range:contributions.kind},%s,{range:contributions.date},">="&EDATE({today},-12))' % (LK('sinking_spend', 'goal'), SPEND), 'money'),
        FF('Monthly amount of the goal', GLN('sinking_spend', 'monthly_amount'), 'money')]),
    FORM('change_sheet', 'Goal Change Sheet', 'One change of a monthly amount', 'goal_changes.change_id', F(
        ('Date', 'goal_changes.date'), ('Goal', 'goal_changes.goal'), ('Old monthly amount', 'goal_changes.old_monthly'), ('New monthly amount', 'goal_changes.new_monthly'), ('Reason', 'goal_changes.reason'),
        ('Change a month', 'goal_changes.change'), ('Change over a year', 'goal_changes.change_year')) + [
        FF('Monthly amount now', GLN('goal_changes', 'monthly_amount'), 'money'), FF('Target of the goal', GLN('goal_changes', 'target'), 'money'),
        FF('Changes logged for this goal', 'COUNTIFS({range:goal_changes.goal},%s)' % LK('goal_changes', 'goal'), 'int')]),
    FORM('annual_cost_sheet', 'Annual Cost Sheet', 'One yearly cost and its fund', 'annual_costs.item_id', F(
        ('Item', 'annual_costs.item'), ('Category', 'annual_costs.category'), ('Amount', 'annual_costs.amount'), ('Due month', 'annual_costs.due_month'), ('Due day', 'annual_costs.due_day'),
        ('Fund', 'annual_costs.goal'), ('Set aside a month', 'annual_costs.per_month'), ('Set aside per paycheck', 'annual_costs.per_paycheck'), ('Next due date', 'annual_costs.next_due'),
        ('Days to due', 'annual_costs.days_to_due'), ('Saved in its fund', 'annual_costs.fund_saved'), ('Short at the due date', 'annual_costs.short_at_due'), ('Add a month to close the gap', 'annual_costs.add_month'),
        ('Fund status', 'annual_costs.state')) + [FF('Share of all yearly costs', 'IFERROR(%s/SUM({range:annual_costs.amount}),0)' % LK('annual_costs', 'amount'), 'pct')]),
    FORM('emergency_sheet', 'Emergency Fund Sheet', 'The emergency fund at the end of one month', 'emergency_months.month', F(
        ('Essential spending a month', 'emergency_months.essential'), ('Emergency fund balance', 'emergency_months.balance'), ('Months covered', 'emergency_months.months_covered'),
        ('Target months, low end', 'emergency_months.target_months'), ('Target amount, low end', 'emergency_months.target_amount'), ('Gap to the target', 'emergency_months.gap'),
        ('Against the typical range', 'emergency_months.range')) + [
        FF('Target amount, high end', '{set:emergency_high}*%s' % LK('emergency_months', 'essential'), 'money'),
        FF('Months to reach the low end', 'IFERROR(ROUNDUP(%s/SUMIFS(%s,%s,%s),0),0)' % (LK('emergency_months', 'gap'), GL('monthly_amount'), GL('kind'), EMERG), 'int'),
        FF('Typical range in months, low end', '{set:emergency_low}', 'int'), FF('Typical range in months, high end', '{set:emergency_high}', 'int')]),
    FORM('retirement_sheet', 'Retirement Contribution Sheet', 'One contribution and its share of take-home pay', 'retirement.rt_id', F(
        ('Date', 'retirement.date'), ('Person', 'retirement.person'), ('Source', 'retirement.source'), ('Account', 'retirement.account'), ('Your amount', 'retirement.employee_amount'),
        ('Employer amount typed', 'retirement.employer_amount'), ('Total', 'retirement.total'), ('Take-home it is measured against', 'retirement.pay_base'), ('Share of take-home', 'retirement.share')) + [
        FF('Your amount this year so far', 'SUMIFS({range:retirement.employee_amount},{range:retirement.person},%s,{range:retirement.date},">="&%s)' % (LK('retirement', 'person'), THISYR), 'money'),
        FF('Typical range, low end of take-home', '{set:retirement_min}', 'pct'), FF('Typical range, high end of take-home', '{set:retirement_good}', 'pct')]),
    FORM('employer_sheet', 'Employer Contribution Sheet', 'Employer and own amounts of one account and period', 'retirement_summary.row_id', F(
        ('Period', 'retirement_summary.window'), ('Account', 'retirement_summary.account'), ('From', 'retirement_summary.w_from'), ('Up to', 'retirement_summary.w_to'), ('Your amount', 'retirement_summary.employee'),
        ('Employer amount typed', 'retirement_summary.employer'), ('Total', 'retirement_summary.total'), ('Take-home in the period', 'retirement_summary.take_home'), ('Share of take-home', 'retirement_summary.share'),
        ('Yearly total at this pace', 'retirement_summary.yearly')) + [
        FF('Employer share of the total', 'IFERROR(%s/%s,0)' % (LK('retirement_summary', 'employer'), LK('retirement_summary', 'total')), 'pct')]),
    FORM('windfall_sheet', 'Windfall to Goals Sheet', 'One payment and the goals it could fill', 'income.income_id', F(
        ('Date', 'income.date'), ('Person', 'income.person'), ('Source', 'income.source'), ('Amount received', 'income.net'), ('Goal to fund first', 'income.fund_first')) + [
        FF('Left to save on the first goal', 'IFERROR(INDEX({range:goal_ranking.left},1),0)', 'money'),
        FF('Put in the first goal, keeping 20%', 'MIN(0.8*%s,IFERROR(INDEX({range:goal_ranking.left},1),0))' % LK('income', 'net'), 'money'),
        FF('Left to save on all goals', 'SUM({range:goals.left})', 'money'), FF('Share of all that is left to save', 'IFERROR(%s/SUM({range:goals.left}),0)' % LK('income', 'net'), 'pct')]),
    FORM('pause_sheet', 'Goal Pause Sheet', 'What pausing one goal frees up', 'goals.goal_id', F(
        ('Goal', 'goals.goal'), ('Priority', 'goals.priority'), ('Monthly amount', 'goals.monthly_amount'), ('Left to save', 'goals.left'), ('Needed a month', 'goals.needed_month'), ('Status', 'goals.status'),
        ('Reached at this pace on', 'goals.reach_date')) + [
        FF('Freed a month if paused', LK('goals', 'monthly_amount'), 'money'),
        FF('Freed per paycheck if paused', 'ROUND(%s*12/%s,2)' % (LK('goals', 'monthly_amount'), PPY), 'money'),
        FF('Reached on if paused for 3 months', 'IFERROR(%s+91,"")' % LK('goals', 'reach_date'), 'date'),
        FF('Share of the monthly total of open goals', 'IFERROR(%s/SUMIFS({range:goals.monthly_amount},{range:goals.is_reached},0),0)' % LK('goals', 'monthly_amount'), 'pct')]),
    FORM('review_sheet', 'Goal Review Sheet', 'One goal over the last 12 and 3 months', 'contrib_goals.goal', F(
        ('Goal ID', 'contrib_goals.goal_id'), ('Monthly amount', 'contrib_goals.monthly'), ('Deposits, last 12 months', 'contrib_goals.dep12'), ('Spends, last 12 months', 'contrib_goals.spend12'),
        ('Planned, last 12 months', 'contrib_goals.planned12'), ('Deposits against plan', 'contrib_goals.diff12'), ('Deposits, last 3 months', 'contrib_goals.dep3'), ('Planned, last 3 months', 'contrib_goals.planned3'),
        ('Under-funded by, last 3 months', 'contrib_goals.short3'), ('Share of plan funded, last 3 months', 'contrib_goals.share3'), ('Funding', 'contrib_goals.funded')) + [
        FF('Goal status', 'IFERROR(INDEX({range:goals.status},MATCH({pick},{range:goals.goal},0)),"")', 'text'),
        FF('Left to save', 'IFERROR(INDEX({range:goals.left},MATCH({pick},{range:goals.goal},0)),0)', 'money')]),
    FORM('closed_sheet', 'Goal Closed Sheet', 'Closing one goal when it is reached', 'goals.goal_id', F(
        ('Goal', 'goals.goal'), ('Kind', 'goals.kind'), ('Target', 'goals.target'), ('Saved so far', 'goals.saved'), ('Target date', 'goals.target_date'), ('Status', 'goals.status'), ('Days left', 'goals.days_left')) + [
        FF('Reached or projected on', 'IF(%s="",%s,%s)' % (LK('goals', 'reached_on'), LK('goals', 'reach_date'), LK('goals', 'reached_on')), 'date'),
        FF('Saved above the target', 'MAX(0,%s-%s)' % (LK('goals', 'saved'), LK('goals', 'target')), 'money'),
        FF('Monthly amount freed when it is closed', LK('goals', 'monthly_amount'), 'money'),
        FF('Freed per paycheck when it is closed', 'ROUND(%s*12/%s,2)' % (LK('goals', 'monthly_amount'), PPY), 'money')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
SIGN = ['Partner 1', 'Partner 2']
documents = [
    DOC('overview_doc', 'Goals Overview Page', 'Goals overview, one goal', 'goals.goal_id', [
        'Goals overview of {set:household}, dated {today}. Goal: {col:goals.goal} ({col:goals.kind}), priority {col:goals.priority}, held in {col:goals.account}.',
        'Target {col:goals.target}, saved so far {col:goals.saved}, left to save {col:goals.left}. Target date {col:goals.target_date}, {col:goals.days_left} days away. Status: {col:goals.status}.',
        'At the planned monthly amount of {col:goals.monthly_amount} the goal falls short by {col:goals.behind_by} at the date. An estimate from your numbers, not advice.'], SIGN, NOTE),
    DOC('onepager_doc', 'Goal One-pager', 'Goal one-pager, the plan for one goal', 'goals.goal_id', [
        'Goal plan of {set:household}, dated {today}. {col:goals.goal}: a {col:goals.kind} with a target of {col:goals.target} by {col:goals.target_date}.',
        'Saved so far {col:goals.saved}. To reach the target on time, set aside {col:goals.needed_month} a month, which is {col:goals.per_paycheck} for each paycheck. The planned monthly amount is {col:goals.monthly_amount}, deposited on day {col:goals.transfer_day} of the month.',
        'At the planned monthly amount the goal is reached on {col:goals.reach_date}. Straight-line plan so far: {col:goals.plan_so_far}. Estimates from your numbers.'], SIGN, NOTE),
    DOC('calendar_doc', 'Annual Costs Calendar Page', 'Annual costs calendar, one month', 'annual_months.month', [
        'Annual costs calendar of {set:household}, dated {today}. Month: {col:annual_months.month}.',
        'Yearly costs falling due: {col:annual_months.items}, together {col:annual_months.costs_due}. Covered by their funds by then: {col:annual_months.covered}. Short at the due dates: {col:annual_months.gap}. Status: {col:annual_months.state}.',
        'Check each yearly cost on the Annual costs sheet and top up the short funds before the dates. Estimates from your numbers.'], SIGN, NOTE),
    DOC('annual_doc', 'Annual Costs to Monthly Page', 'Annual cost to monthly, one cost', 'annual_costs.item_id', [
        'Yearly cost of {set:household}, dated {today}. {col:annual_costs.item} ({col:annual_costs.category}) costs {col:annual_costs.amount} and falls due on {col:annual_costs.next_due}, {col:annual_costs.days_to_due} days away.',
        'Set aside {col:annual_costs.per_month} a month, which is {col:annual_costs.per_paycheck} for each paycheck. Its fund {col:annual_costs.goal} holds {col:annual_costs.fund_saved}.',
        'Fund status: {col:annual_costs.state}. Short at the due date: {col:annual_costs.short_at_due}; adding {col:annual_costs.add_month} a month closes the gap. An estimate from your numbers.'], SIGN, NOTE),
    DOC('statement_doc', 'Sinking Fund Statement', 'Sinking fund statement, one fund', 'contrib_goals.goal', [
        'Fund statement of {set:household}, dated {today}. Fund: {col:contrib_goals.goal} ({col:contrib_goals.goal_id}).',
        'Deposits in the last 12 months: {col:contrib_goals.dep12}. Spends in the last 12 months: {col:contrib_goals.spend12}. Planned deposits: {col:contrib_goals.planned12}. Deposits against plan: {col:contrib_goals.diff12}.',
        'Last 3 months: deposits {col:contrib_goals.dep3} against {col:contrib_goals.planned3} planned, {col:contrib_goals.share3} funded ({col:contrib_goals.funded}).'], SIGN, NOTE),
    DOC('emergency_doc', 'Emergency Fund Report', 'Emergency fund report, one month', 'emergency_months.month', [
        'Emergency fund report of {set:household}, dated {today}. Month: {col:emergency_months.month}.',
        'Balance {col:emergency_months.balance} against essential spending of {col:emergency_months.essential} a month: {col:emergency_months.months_covered} months covered. A typical range is {set:emergency_low} to {set:emergency_high} months, check your own numbers. Position: {col:emergency_months.range}.',
        'Target amount at the low end: {col:emergency_months.target_amount}. Gap: {col:emergency_months.gap}. An estimate from your numbers, not advice.'], SIGN, NOTE),
    DOC('eplan_doc', 'Emergency Plan Page', 'Emergency fund plan, one target', 'emergency_plan.months', [
        'Emergency fund plan of {set:household}, dated {today}. Target: {col:emergency_plan.months} months of essential spending, {col:emergency_plan.target_amount}.',
        'Essential spending is {col:emergency_plan.essential} a month. Saved {col:emergency_plan.saved}, gap {col:emergency_plan.gap}. The fund covers {col:emergency_plan.months_now} months now.',
        'At {col:emergency_plan.monthly} a month the target is reached in {col:emergency_plan.months_to_reach} months, on {col:emergency_plan.reach_date}. Position: {col:emergency_plan.position}. A typical range, check your own numbers.'], SIGN, NOTE),
    DOC('retirement_doc', 'Retirement Contributions Page', 'Retirement contributions, amounts only', 'retirement_summary.row_id', [
        'Retirement contributions of {set:household}, dated {today}. Account: {col:retirement_summary.account}. Period: {col:retirement_summary.window}, from {col:retirement_summary.w_from} up to {col:retirement_summary.w_to}.',
        'Your amount {col:retirement_summary.employee}, employer amount typed {col:retirement_summary.employer}, total {col:retirement_summary.total}. Take-home in the period {col:retirement_summary.take_home}; your share {col:retirement_summary.share}.',
        'At this pace the yearly total is {col:retirement_summary.yearly}. Amounts only, not advice: ask your adviser about your own situation.'], SIGN, NOTE),
    DOC('funding_doc', 'Goals Funding Plan', 'Goal funding per paycheck, one goal', 'goal_funding.goal', [
        'Funding plan of {set:household}, dated {today}. Goal: {col:goal_funding.goal}. Pay rhythm: {col:goal_funding.rhythm}.',
        'Planned: {col:goal_funding.monthly} a month, {col:goal_funding.per_week} a week, {col:goal_funding.plan_paycheck} per paycheck. Needed to reach the target on time: {col:goal_funding.needed_month} a month, {col:goal_funding.need_paycheck} per paycheck.',
        'Extra needed per paycheck: {col:goal_funding.gap_paycheck}. Estimates from your numbers.'], SIGN, NOTE),
    DOC('shortfall_doc', 'Goal Shortfall Note', 'Goal shortfall note', 'goals.goal_id', [
        'Shortfall note of {set:household}, dated {today}. Goal: {col:goals.goal}, target {col:goals.target} by {col:goals.target_date}.',
        'Saved so far {col:goals.saved}; left to save {col:goals.left}. At the planned monthly amount of {col:goals.monthly_amount} the goal is short by {col:goals.behind_by} at the date (status: {col:goals.status}).',
        'To close the gap, set aside {col:goals.needed_month} a month, or {col:goals.per_paycheck} for each paycheck, or add the shortfall once. Estimates from your numbers.'], SIGN, NOTE),
    DOC('windfall_doc', 'Windfall Plan', 'Windfall plan, one payment', 'income.income_id', [
        'Windfall plan of {set:household}, dated {today}. A payment of {col:income.net} was received on {col:income.date} ({col:income.source}, {col:income.person}).',
        'The goal that needs money first is {col:income.fund_first}. Decide together how much to keep for spending and how much to put in the goals; the Windfall to Goals tool shows the split.',
        'An estimate from your numbers, not advice.'], SIGN, NOTE),
    DOC('year_doc', 'Year Goals Summary', 'Year goals summary, one month', 'contrib_months.month', [
        'Goals summary of {set:household}, dated {today}. Month: {col:contrib_months.month}.',
        'Deposits {col:contrib_months.deposits}, spends {col:contrib_months.spends}, net saved {col:contrib_months.net}. Planned deposits {col:contrib_months.planned}; deposits against plan {col:contrib_months.diff}.',
        'Sinking fund balance at the end of the month: {col:contrib_months.sink_balance}. Funding: {col:contrib_months.funded}.'], SIGN, NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('topup_chk', 'Monthly Goals Top-up Steps', 'contrib_months', 'contrib_months.month', [('Type the deposits of the month in Contributions', 28), ('Type every spend from a goal', 28), ('Check Goal funding per paycheck', 29), ('Run the Goal Funding Check', 30), ('Top up any goal that is under-funded', 31)]),
    CHK('paycheck_chk', 'Every Paycheck Set-aside Steps', 'income', 'income.date', [('Type the paycheck in Income', 0), ('Move the set-aside amount for each goal', 0), ('Type each deposit in Contributions', 1), ('Check the Goal ranking for the next goal to fund', 2)]),
    CHK('spend_chk', 'Sinking Fund Spend Steps', 'contributions', 'contributions.date', [('Type the spend in Contributions as a Spend', 0), ('Put the goal ID in From goal on the Transactions row', 0), ('Check the fund balance in Sinking fund spending', 1), ('Top up the fund if the balance is low', 7)]),
    CHK('newgoal_chk', 'New Goal Steps', 'goals', 'goals.start_date', [('Name the goal and choose the kind', 0), ('Type the target and the target date', 0), ('Run the Monthly Amount Solver', 1), ('Type the monthly amount and the transfer day', 2), ('Ask the bank branch for the monthly transfer', 3), ('Agree it with your partner', 7)]),
    CHK('reached_chk', 'Goal Reached Steps', 'goals', 'goals.target_date', [('Check the saved amount against the target', -7), ('Fill in the Goal Closed Sheet', -3), ('Spend or move the money', 0), ('Stop the monthly transfer', 1), ('Give the freed monthly amount to the next goal', 7)]),
    CHK('annual_chk', 'Annual Costs Review Steps', 'annual_months', 'annual_months.month', [('Open Annual costs and check every amount', 0), ('Check the due months and days', 3), ('Run the Annual Costs Calendar', 7), ('Top up the funds that are short', 14), ('Update the monthly amounts', 21)]),
    CHK('emergency_chk', 'Emergency Fund Review Steps', 'emergency_months', 'emergency_months.month', [('Check the balance on Goals', 28), ('Read the months covered against the typical range', 29), ('Run the Emergency Fund Target tool', 30), ('Adjust the monthly amount', 31)]),
    CHK('insurance_chk', 'Insurance Premium Due Steps', 'goals', 'goals.target_date', [('Run the Insurance Premium Fund tool', -60), ('Top up the fund', -45), ('Ask the insurance agent to confirm the amount and date', -30), ('Ask about instalments if the fund is short', -21), ('Pay the premium', 0), ('Restart the fund for next year', 7)]),
    CHK('holiday_chk', 'Holiday and Gift Fund Prep', 'goals', 'goals.target_date', [('List the gifts and the trips', -90), ('Check the fund against the list', -75), ('Run the Goal Funding Check', -60), ('Top up the fund', -30), ('Spend and record each purchase', -7), ('Reset the fund for next year', 7)]),
    CHK('retirement_chk', 'Retirement Contributions Check', 'retirement', 'retirement.date', [('Check the amount against the payslip', 0), ('Type the employer amount', 1), ('Read the share of take-home against the typical range', 7), ('Ask the payroll office if a change is needed', 14)]),
    CHK('quarter_chk', 'Quarterly Goals Review Steps', 'contrib_months', 'contrib_months.month', [('Read Goals Status', 30), ('Run the Goal Ranking', 31), ('Check the Goal changes log', 32), ('Run the Goals Pause Test if money is tight', 33), ('Write down the monthly amounts you change', 35)]),
    CHK('single_chk', 'Single Adult First Goals Steps', 'goals', 'goals.start_date', [('Start with the emergency fund', 0), ('Add one sinking fund for a yearly cost', 1), ('Leave the partner 2 and children rows empty', 1), ('Run the Goal Set-aside per Paycheck tool', 2), ('Check Goals Status each month', 30)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, ph, text): return MSG(k, moment, table, '%s.%s' % (table, ph), text)
messages = [
    M('p2_insurance', 'Partner 2: the car insurance fund', 'goals', 'p2_phone', 'Hello {partner2}, the {goal} fund holds {saved} of {target}, due on {target_date}. We need to add {needed_month} a month to be full. {household}'),
    M('p2_behind', 'Partner 2: goals are behind', 'goals', 'p2_phone', 'Hello {partner2}, our goals are behind by {total_behind} in total at their dates. Can we top them up? {household}'),
    M('p2_holiday', 'Partner 2: a fund needs more a month', 'goals', 'p2_phone', 'Hello {partner2}, the {goal} fund needs {needed_month} a month until {target_date}. {household}'),
    M('p2_transfer', 'Partner 2: confirm a transfer', 'contributions', 'p2_phone', 'Hello {partner2}, please confirm the transfer of {amount} to {goal} on {date}. {household}'),
    M('p2_emergency', 'Partner 2: the emergency fund in months', 'emergency_months', 'p2_phone', 'Hello {partner2}, at the end of {month} the emergency fund covers {months_covered} months of essential spending. {household}'),
    M('p2_windfall', 'Partner 2: a windfall', 'income', 'p2_phone', 'Hello {partner2}, the payment of {net} could go to {fund_first}. What do you think? {household}'),
    M('p1_setaside', 'Partner 1: this paycheck set-aside', 'goals', 'p1_phone', "Hello {partner1}, this paycheck's set-aside is {per_paycheck} for {goal}. {household}"),
    M('p1_reached', 'Partner 1: a goal is reached', 'goals', 'p1_phone', 'Hello {partner1}, {goal} is reached on {reach_date} at the current monthly amount. {household}'),
    M('p1_retirement', 'Partner 1: your retirement contribution', 'retirement', 'p1_phone', 'Hello {partner1}, your retirement contribution is {employee_amount} a paycheck, {share} of take-home. {household}'),
    M('p1_trip', 'Partner 1: a fund against its target', 'goals', 'p1_phone', 'Hello {partner1}, the {goal} fund is {saved} of {target}. {household}'),
    M('p1_laptop', 'Partner 1: a fund reaches its target', 'goals', 'p1_phone', 'Hello {partner1}, the {goal} fund reaches its target on {reach_date}. {household}'),
    M('hm_review', 'Household member: the goals review', 'goals', 'member_phone', 'Hello Ada, the goals review is on {review_date}. Please bring your questions. {household}'),
    M('hm_annual', 'Household member: yearly costs due', 'annual_months', 'member_phone', 'Hello Ada, the yearly costs due in {month} total {costs_due}. {household}'),
    M('hm_spent', 'Household member: a spend from a goal', 'sinking_spend', 'member_phone', 'Hello Ada, {goal} was spent on {date}, the balance is now {balance_after}. {household}'),
    M('hm_emergency', 'Household member: the emergency fund', 'emergency_plan', 'member_phone', 'Hello Ada, the emergency fund is at {months_now} months of essential spending. {household}'),
    M('gp_trip', 'Grandparent: a family plan', 'goals', 'gp_phone', 'Hello Ada, we plan {goal} for {target_date}. Can you join us? {household}'),
    M('gp_activities', 'Grandparent: thank you for helping', 'goals', 'gp_phone', 'Hello Ada, thank you for helping. The {goal} fund is {saved} of {target} for {target_date}. {household}'),
    M('in_pay', 'Insurance agent: we will pay the premium', 'goals', 'ins_phone', 'Hello Carlos, we will pay the yearly premium of {target} on {target_date}. Please send the invoice. {household}'),
    M('in_inst', 'Insurance agent: pay in instalments', 'goals', 'ins_phone', 'Hello Carlos, can we pay the premium in {instalments} instalments instead? {household}'),
    M('in_renew', 'Insurance agent: confirm the renewal', 'goals', 'ins_phone', 'Hello Carlos, please confirm the renewal date {target_date} and the amount {target}. {household}'),
    M('bk_monthly', 'Bank branch: a monthly transfer', 'goals', 'bank_phone', 'Hello Elif, please set up a monthly transfer of {monthly_amount} to {account} on day {transfer_day}. {household}'),
    M('bk_move', 'Bank branch: move money', 'contributions', 'bank_phone', 'Hello Elif, please move {amount} from {from_account} to {account} on {date}. {household}'),
    M('bk_balance', 'Bank branch: confirm a balance', 'accounts', 'bank_phone', 'Hello Elif, please confirm the balance of {account} on {today_date}. {household}'),
    M('bk_fee', 'Bank branch: no fee on transfers', 'accounts', 'bank_phone', 'Hello Elif, please confirm there is no fee on transfers to {account}. {household}'),
    M('bk_interest', 'Bank branch: the interest summary', 'accounts', 'bank_phone', 'Hello Elif, please send the interest summary for {account} for {year}. {household}'),
    M('pr_change', 'Payroll office: change my contribution', 'retirement', 'payroll_phone', 'Hello Dev, please change my retirement contribution to {share} of take-home from {change_from}. {household}'),
    M('pr_employer', 'Payroll office: employer amount', 'retirement', 'payroll_phone', 'Hello Dev, please confirm the employer contribution of {employer_amount} per pay period. {household}'),
    M('pr_ytd', 'Payroll office: year to date', 'retirement', 'payroll_phone', 'Hello Dev, please send my year-to-date retirement contributions for {account}. {household}'),
    M('tp_retire', 'Tax preparer: record the contributions', 'retirement_summary', 'tax_phone', 'Hello Aiko, please tell us how to record the retirement contributions of {total} for {account}. {household}'),
    M('tp_setaside', 'Tax preparer: the tax set-aside', 'goals', 'tax_phone', 'Hello Aiko, the tax set-aside holds {saved}. Please confirm the estimate for {target_date}. {household}'),
    M('mc_quote', 'Car mechanic: a quote', 'annual_costs', 'mech_phone', 'Hello Pavel, please send the quote for {item} due on {next_due}. {household}'),
    M('sc_fees', 'School office: the activity fees', 'annual_costs', 'school_phone', 'Hello Ruth, please send the activity fees for {next_due}; we plan to pay {amount}. {household}'),
    M('cc_holiday', 'Childcare provider: holiday care dates', 'annual_costs', 'child_phone', 'Hello Nadia, please send the holiday care dates; we set aside {per_month} a month. {household}'),
    M('p2_ontrack', 'Partner 2: deposits for the month', 'contrib_months', 'p2_phone', 'Hello {partner2}, deposits for {month} are {deposits} against {planned} planned. {household}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
NXT = 'IFERROR(SMALL(%s,COUNTIF(%s,"<"&{today})+1),"")' % (GL('open_date'), GL('open_date'))
EMON = 'SUMIFS(%s,%s,%s)' % (GL('monthly_amount'), GL('kind'), EMERG)
ETAR = '{set:emergency_low}*%s' % EAVG
INSN = '{set:insurance_goal}'
DEPR = lambda a: 'SUMIFS(%s,%s,%s,%s,">="&%s,%s,"<="&{today})' % (CT('amount'), CT('kind'), DEP, CT('date'), a, CT('date'))
kpis = [
    KPI('Total saved in goals', 'SUM(%s)' % GL('saved'), 'money'), KPI('Total targets', 'SUM(%s)' % GL('target'), 'money'), KPI('Share of targets reached', 'IFERROR(SUM(%s)/SUM(%s),0)' % (GL('saved'), GL('target')), 'pct'),
    KPI('Goals behind plan', 'SUM(%s)' % GL('is_behind'), 'int'), KPI('Total behind by', 'SUMIFS(%s,%s,1)' % (GL('behind_by'), GL('is_behind')), 'money'),
    KPI('Goals reached this year', 'COUNTIFS(%s,1,%s,">="&%s)' % (GL('is_reached'), GL('reached_on'), THISYR), 'int'), KPI('Next goal date', NXT, 'date'),
    KPI('Days to the next goal date', 'IFERROR(%s-{today},"")' % NXT, 'int'), KPI('Needed per month for all goals', 'SUM(%s)' % GL('needed_month'), 'money'),
    KPI('Planned monthly amount for all goals', 'SUMIFS(%s,%s,0)' % (GL('monthly_amount'), GL('is_reached')), 'money'), KPI('Deposits last 30 days', DEPR('{today}-30'), 'money'),
    KPI('Deposits this year', DEPR(THISYR), 'money'), KPI('Spends from goals this year', 'SUMIFS(%s,%s,%s,%s,">="&%s)' % (CT('amount'), CT('kind'), SPEND, CT('date'), THISYR), 'money'),
    KPI('Net saved last 12 months', 'SUMIFS(%s,%s,1)' % (CM('net'), CM('last12')), 'money'), KPI('Emergency fund balance', EBAL, 'money'),
    KPI('Emergency fund months covered', 'IFERROR(ROUND(%s/%s,1),0)' % (EBAL, EAVG), 'num'), KPI('Emergency fund target amount', 'ROUND(%s,0)' % ETAR, 'money'),
    KPI('Emergency fund gap', 'ROUND(MAX(0,%s-%s),0)' % (ETAR, EBAL), 'money'), KPI('Months to reach the emergency target', 'IFERROR(ROUNDUP(MAX(0,%s-%s)/%s,0),0)' % (ETAR, EBAL, EMON), 'int'),
    KPI('Essential spending per month', 'ROUND(%s,0)' % EAVG, 'money'), KPI('Car insurance fund saved', 'SUMIFS(%s,%s,%s)' % (GL('saved'), GL('goal'), INSN), 'money'),
    KPI('Car insurance fund short by', 'SUMIFS(%s,%s,%s)' % (GL('behind_by'), GL('goal'), INSN), 'money'), KPI('Annual costs per month', 'ROUND(SUM(%s)/12,0)' % AC('amount'), 'money'),
    KPI('Annual costs due in the next 90 days', 'SUMIFS(%s,%s,"<="&{today}+90)' % (AC('amount'), AC('next_due')), 'money'),
    KPI('Annual costs due this year', 'SUMIFS(%s,%s,"<="&DATE(YEAR({today}),12,31))' % (AC('amount'), AC('next_due')), 'money'),
    KPI('Set aside per paycheck for all goals', 'ROUND(SUM(%s),2)' % GL('per_paycheck'), 'money'),
    KPI('Retirement contributions year to date', 'SUMIFS(%s,%s,">="&%s)' % (RT('employee_amount'), RT('date'), THISYR), 'money'),
    KPI('Employer contributions year to date', 'SUMIFS(%s,%s,">="&%s)' % (RT('employer_amount'), RT('date'), THISYR), 'money'),
    KPI('Retirement share of take-home', 'IFERROR(SUMIFS(%s,%s,1)/SUMIFS(%s,%s,1),0)' % (R('retirement_months', 'employee'), R('retirement_months', 'last12'), R('retirement_months', 'take_home'), R('retirement_months', 'last12')), 'pct'),
    KPI('Goals with a deposit last month', 'SUM(%s)' % CG('last_dep'), 'int'),
]
assert len(kpis) == 30
dashboard = {"title": "Goals Dashboard", "kpis": kpis,
    "monthly": {"title": "Deposits, spends and net saved by month", "date": "contrib_months.month", "series": [
        {"label": "Deposits", "sum": "contrib_months.deposits", "date": "contrib_months.month"}, {"label": "Spends", "sum": "contrib_months.spends", "date": "contrib_months.month"},
        {"label": "Net saved", "sum": "contrib_months.net", "date": "contrib_months.month"}]},
    "breakdowns": [{"title": "Saved by goal kind", "by": "goals.kind", "value": "goals.saved", "agg": "sum"},
                   {"title": "Targets by priority", "by": "goals.priority", "value": "goals.target", "agg": "sum"},
                   {"title": "Annual costs by category", "by": "annual_costs.category", "value": "annual_costs.amount", "agg": "sum"},
                   {"title": "Retirement by person", "by": "retirement.person", "value": "retirement.total", "agg": "sum"}]}

def AM(t, c, date=None, label=None, where=None, agg='sum'): return AGG(agg, t, '%s.%s' % (t, c), date=('%s.%s' % (t, date)) if date else None, where=where, label=label)
LAST12 = [('last12', '=', 1)]
insights = {"filters": [{"label": "Person", "list": "person"}, {"label": "Goal kind", "list": "gkind"}, {"label": "Priority", "list": "priority"}],
    "gauges": [
        {"title": "Total saved against targets", "num": AM('goals', 'saved'), "den": AM('goals', 'target')},
        {"title": "Goals on track", "num": AGG('count', 'goals', where=[('is_behind', '=', 0)]), "den": AGG('count', 'goals')},
        {"title": "Emergency fund, low end", "num": AM('emergency_plan', 'saved', where=[('months', '=', '{set:emergency_low}')]), "den": AM('emergency_plan', 'target_amount', where=[('months', '=', '{set:emergency_low}')])},
        {"title": "Emergency fund, high end", "num": AM('emergency_plan', 'saved', where=[('months', '=', '{set:emergency_high}')]), "den": AM('emergency_plan', 'target_amount', where=[('months', '=', '{set:emergency_high}')])},
        {"title": "Deposits made against planned", "num": AM('contrib_months', 'deposits', where=LAST12), "den": AM('contrib_months', 'planned', where=LAST12)},
        {"title": "Employer share of contributions", "num": AM('retirement_months', 'employer', where=LAST12), "den": AM('retirement_months', 'total', where=LAST12)}],
    "charts": [
        CHART('Saved by goal', 'bar', 'contrib_goals.goal', [AM('contrib_goals', 'saved', label='Saved')]),
        CHART('Target and saved by goal', 'bar', 'contrib_goals.goal', [AM('contrib_goals', 'target', label='Target'), AM('contrib_goals', 'saved', label='Saved')]),
        CHART('Left to save by goal', 'bar', 'contrib_goals.goal', [AM('contrib_goals', 'left', label='Left to save')]),
        CHART('Goals by days left', 'bar', 'contrib_goals.goal', [AM('contrib_goals', 'days_left', label='Days left')]),
        CHART('Goals by priority', 'bar', 'goals.priority', [AM('goals', 'target', label='Target'), AM('goals', 'saved', label='Saved')]),
        CHART('Goals by kind', 'bar', 'goals.kind', [AM('goals', 'target', label='Target'), AM('goals', 'saved', label='Saved')]),
        CHART('Deposits per month', 'column', 'month', [AM('contributions', 'amount', 'date', 'Deposits', where=[('kind', '=', DEP)])]),
        CHART('Spends from goals per month', 'column', 'month', [AM('contributions', 'amount', 'date', 'Spends', where=[('kind', '=', SPEND)])]),
        CHART('Net saved per month', 'column', 'month', [AM('contrib_months', 'net', 'month', 'Net saved')]),
        CHART('Emergency fund per month', 'column', 'month', [AM('emergency_months', 'balance', 'month', 'Emergency fund')]),
        CHART('Emergency fund months per month', 'column', 'month', [AM('emergency_months', 'months_covered', 'month', 'Months covered')]),
        CHART('Essential spending per month', 'column', 'month', [AM('essential_months', 'essential', 'month', 'Essential spending'), AM('essential_months', 'avg_before', 'month', 'Average of the months before')]),
        CHART('Annual costs by due month', 'column', 'month', [AM('annual_months', 'costs_due', 'month', 'Costs due'), AM('annual_months', 'gap', 'month', 'Short at the due dates')]),
        CHART('Annual costs by category', 'bar', 'annual_costs.category', [AM('annual_costs', 'amount', label='Yearly amount')]),
        CHART('Sinking fund balance per month', 'column', 'month', [AM('contrib_months', 'sink_balance', 'month', 'Sinking fund balance')]),
        CHART('Planned and actual deposits per month', 'column', 'month', [AM('contrib_months', 'planned', 'month', 'Planned deposits'), AM('contrib_months', 'deposits', 'month', 'Deposits made')]),
        CHART('Deposits by goal, last 12 months', 'bar', 'contrib_goals.goal', [AM('contrib_goals', 'dep12', label='Deposits'), AM('contrib_goals', 'planned12', label='Planned')]),
        CHART('Goal changes by reason', 'bar', 'goal_changes.reason', [AM('goal_changes', 'change_year', label='Change over a year')]),
        CHART('Retirement per month', 'column', 'month', [AM('retirement_months', 'total', 'month', 'Total')]),
        CHART('Retirement by person', 'bar', 'retirement.person', [AM('retirement', 'total', label='Total')]),
        CHART('Employer and employee per month', 'column', 'month', [AM('retirement_months', 'employee', 'month', 'Your amount'), AM('retirement_months', 'employer', 'month', 'Employer amount')]),
        CHART('Retirement share of take-home per month', 'column', 'month', [AM('retirement_months', 'share', 'month', 'Share of take-home')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Goals status", "why": "every goal with its shortfall at the date if you keep the planned monthly amount: how many are behind and how much is short", "where": "Goals Status"},
    {"name": "Monthly amount solver", "why": "the monthly amount that reaches a target by a date, with a typed interest rate, set against what you can save", "where": "Monthly Amount Solver"},
    {"name": "Goal set-aside per paycheck", "why": "any monthly goal turned into an amount for each paycheck and week for your pay rhythm, with the months that have an extra paycheck", "where": "Goal Set-aside per Paycheck"},
    {"name": "Annual costs calendar", "why": "the next 12 months of yearly costs against what their funds will hold: the first month that is short and by how much", "where": "Annual Costs Calendar"},
    {"name": "Insurance premium fund", "why": "the yearly premium against its fund and the days left, with the monthly amount that closes the gap", "where": "Insurance Premium Fund"},
    {"name": "Emergency fund in months", "why": "the emergency balance divided by essential spending against a typical range of months you can edit", "where": "Emergency Fund in Months"},
    {"name": "Windfall to goals", "why": "a windfall placed in the goals in rank order, each getting no more than it needs", "where": "Windfall to Goals"},
    {"name": "Goal ranking", "why": "behind goals first, then priority and days left, so you know which goal to fund first", "where": "Goal Ranking"},
    {"name": "Sinking fund spending", "why": "every spend from a fund with what was bought and the balance after it", "where": "Sinking fund spending"},
    {"name": "Retirement contributions", "why": "per paycheck, year to date and yearly amounts with the share of take-home pay, amounts only", "where": "Retirement Contributions"}]
competitors = [
    {"what": "budgeting app with a monthly subscription and bank links", "lacks": "shows one savings bar per goal but never the shortfall at the date, a yearly costs calendar or a per-paycheck amount, and charges every month"},
    {"what": "single-purpose savings goal template", "lacks": "tracks a target and a saved amount but has no sinking funds for yearly costs, no emergency fund in months and no ranking of which goal to fund first"},
    {"what": "free emergency fund calculator sheet", "lacks": "gives one months-of-cover number from typed figures, with no history by month, no target date and no shock test for a lost income"},
    {"what": "retirement contribution tracker", "lacks": "keeps one running total without the share of take-home pay, the employer amount typed beside yours or a step test of one point of pay"}]
guide = [
    'Start here: open Start and type the household name, the two partner names, your pay rhythm and the typical range for the emergency fund in the yellow cells.',
    'Replace demo data, step 1: clear the demo rows of Goals and Annual costs and type your own goals, targets, dates and monthly amounts; keep the header rows.',
    'Replace demo data, step 2: clear Contributions, Retirement and Income and type your own deposits and spends; paste the monthly totals into Essential spending.',
    'Replace demo data, step 3: type your own accounts in Accounts, then clear the rows of Goal changes and start your own log.',
    'Pay-day routine: when you are paid, type the paycheck in Income, move the set-aside for each goal and type each deposit in Contributions; the Goal ranking shows the next goal to fund.',
    'Month-close routine, in this order: add the month to Essential spending, type every spend from a goal, read Goal funding, run the Goal Funding Check and top up what is under-funded.',
    'Run the Monthly Amount Solver before you set a new goal and the Insurance Premium Fund before a yearly premium falls due; any range shown is a typical range, check your own numbers.',
    'A single adult with one income and no children can use most sheets: keep fewer goals, leave the partner 2 and children rows empty and use Partner 1 as the person.',
    f'Use the {len(tools)} tools for the weekly and monthly questions, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'Read the dashboard and the Charts page each month: saved against targets, deposits against plan, the emergency fund in months and the yearly costs ahead.',
    'Why a workbook: one flat price, no yearly renewal, your data stays with you and there is nothing to link or re-connect; you type or paste your own data. It works in Excel and Google Sheets with no macros.',
    'What this is not: it is not a bank app, and not tax, legal, investment or credit advice; check your local rules and ask your adviser. Every verdict is an estimate from your numbers.']
listing = {"title": "Savings Goals and Sinking Funds Excel Template: Emergency Fund, Annual Costs, Goal Tracker, Retirement Contributions, Per-paycheck Set-aside",
    "headline": "Fund every goal, yearly cost and emergency month on time",
    "tags": ["savings goal tracker", "sinking funds", "emergency fund", "annual costs planner", "savings planner", "goal tracker", "paycheck savings", "retirement tracker", "household budget", "excel template", "family finance", "no subscription", "budget workbook"],
    "description": ("Run the saving side of your household money in one Excel workbook, for a single adult, a couple or a family. List every goal and sinking fund with a target, a date and a monthly amount, and the workbook shows what is left to save, the days left, the amount needed each month and for each paycheck, and the shortfall at the date if you keep the planned amount. "
        "A Goal Ranking tells you which goal to fund first, and the Windfall to Goals tool places a windfall in that order.\n\n"
        "Yearly costs stop being surprises. The Annual Costs sheet turns insurance, car costs, holidays, gifts, school costs and repairs into an amount per month and per paycheck with the month each falls due, and the Annual Costs Calendar shows the first month your funds run short. The Insurance Premium Fund tool compares the yearly premium with its fund and the days left.\n\n"
        "The emergency fund is shown in months of essential spending against a typical range of 3 and 6 months that you can edit, month by month, with the months to reach your target and a shock test of what happens if an income stops. The Monthly Amount Solver and the Goal Date Finder work with a typed interest rate. These are estimates from your numbers, never advice.\n\n"
        "Retirement and other long-term contributions are kept as amounts only: per paycheck, year to date, the employer amount you type, the yearly total and the share of take-home pay, with a step test of one point of pay. No product names and no advice.\n\n"
        f"{len(tools)} decision tools, {len(forms)} printable sheets, {len(documents)} documents, {len(checklists)} checklists and {len(messages)} ready text messages come with it. This is part five of the Household Finance suite. A standard .xlsx workbook that works in Excel and Google Sheets, with no macros, no subscription and no bank links: you type or paste your own data. The demo copy is full of sample data. "
        "It is a household money kit, not a bank app, and not tax, legal, investment or credit advice."),
    "features": ["Goal status with the shortfall at each date", "Set aside per paycheck for any pay rhythm", "Monthly amount solver with a typed interest rate", "Annual costs calendar with the first short month", "Insurance premium fund against the days left",
                 "Emergency fund in months against a typical range", "Emergency fund target and shock test", "Windfall placed in the goals in rank order", "Goal pause test and funding check", "Retirement contributions as amounts and share of take-home",
                 f"{len(tools)} decision tools and {len(forms)} printable sheets", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "One flat price, no subscription, no bank links"]}
s = spec(id=f'{SUITE}-p5', slug='household-finance-goals', profession='Household Finance', name='Savings Goals and Sinking Funds',
         tagline='Fund every goal, yearly cost and emergency month on time', price_usd=29, colors={"primary": "#1F5F5B", "accent": "#F2B134"},
         settings=settings, lists=lists + vlists(), tables=tables, dashboard=dashboard, forms=forms, guide=guide, listing=listing, insights=insights,
         suite={"key": SUITE, "part": 5, "of": 8, "focus": "Savings goals and sinking funds"}, signature=signature, competitors=competitors, tools=tools,
         messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hf5.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'name', len(s['name']))
