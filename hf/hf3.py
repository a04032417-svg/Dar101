"""Household Finance suite - part 3: Spending Tracker and Groceries."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf3_lists import *
from hf3_tables import *
from hf3_tables import _NM
from hf3_tools import tools
import hf3_data as D

SUITE = 'fx-20261116-household-finance'
NOTE = "Sample wording: adapt it to your own household."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, c, idc='', v='{pick}'):
    return 'INDEX({range:%s.%s},MATCH(%s,{range:%s.%s},0))' % (t, c, v, t, idc or IDCOL[t])
IDCOL = {'transactions': 'tx_id', 'payees': 'payee', 'categories': 'category', 'budget': 'plan_id', 'envelopes': 'envelope', 'grocery_week': 'week_start', 'env_status': 'envelope',
         'checks': 'tx_id', 'accounts': 'account_id', 'savings_rate': 'month'}
TXR = lambda c: R('transactions', c)

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('transaction_sheet', 'Transaction Sheet', 'One payment and where it sits in its category', 'transactions.tx_id', F(
        ('Date', 'transactions.date'), ('Account', 'transactions.account'), ('Payee', 'transactions.payee'), ('Category', 'transactions.category'), ('Group', 'transactions.group'),
        ('Amount', 'transactions.amount'), ('Paid by', 'transactions.paid_by'), ('Week start', 'transactions.week_start'), ('Weekday', 'transactions.weekday')) + [
        FF('Spent in this category that month', 'SUMIFS(%s,%s,%s,%s,%s,%s,"")' % (TXR('amount'), TXR('category'), LK('transactions', 'category'), TXR('month'), LK('transactions', 'month'), TXR('from_goal')), 'money'),
        FF('Planned for the category that month', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('budget', 'planned'), R('budget', 'month'), LK('transactions', 'month'), R('budget', 'category'), LK('transactions', 'category')), 'money'),
        FF('Share of the category that month', 'IFERROR(%s/SUMIFS(%s,%s,%s,%s,%s,%s,""),0)' % (LK('transactions', 'amount'), TXR('amount'), TXR('category'), LK('transactions', 'category'), TXR('month'), LK('transactions', 'month'), TXR('from_goal')), 'pct'),
        FF('Payments to this payee, last 12 months', 'COUNTIFS(%s,%s,%s,">="&({today}-365))' % (TXR('payee'), LK('transactions', 'payee'), TXR('date')), 'int'),
        FF('Average payment to this payee, 12 months', 'IFERROR(SUMIFS(%s,%s,%s,%s,">="&({today}-365))/COUNTIFS(%s,%s,%s,">="&({today}-365)),0)' % (
            TXR('amount'), TXR('payee'), LK('transactions', 'payee'), TXR('date'), TXR('payee'), LK('transactions', 'payee'), TXR('date')), 'money')]),
    FORM('receipt_sheet', 'Receipt Entry Sheet', 'Receipts to keep for one payee', 'payees.payee', F(
        ('Payments, 12 months', 'payees.count12'), ('Spent, 12 months', 'payees.amount12'), ('Average payment', 'payees.average'), ('Share of spending', 'payees.share'),
        ('Payments, 90 days', 'payees.count90'), ('Spent, 90 days', 'payees.amount90')) + [
        FF('Largest payment, last 12 months', 'SUMPRODUCT(MAX((%s={pick})*(%s>={today}-365)*(%s)))' % (TXR('payee'), TXR('date'), TXR('amount')), 'money'),
        FF('Date of the last payment', 'SUMPRODUCT(MAX((%s={pick})*(%s)))' % (TXR('payee'), TXR('date')), 'date'),
        FF('Days since the last payment', '{today}-SUMPRODUCT(MAX((%s={pick})*(%s)))' % (TXR('payee'), TXR('date')), 'int'),
        FF('Receipts to file for the last 12 months', 'COUNTIFS(%s,{pick},%s,">="&({today}-365))' % (TXR('payee'), TXR('date')), 'int')]),
    FORM('category_change_sheet', 'Category Change Sheet', 'A category and what moving a payment would change', 'categories.category', F(
        ('Group', 'categories.group'), ('Year to date, complete months', 'categories.ytd'), ('Plan year to date', 'categories.ytd_plan'), ('Over or under plan', 'categories.ytd_diff')) + [
        FF('Spent this month so far', 'SUMIFS(%s,%s,{pick},%s,%s,%s,"")' % (TXR('amount'), TXR('category'), TXR('month'), MS, TXR('from_goal')), 'money'),
        FF('Plan this month', 'SUMIFS(%s,%s,%s,%s,{pick})' % (R('budget', 'planned'), R('budget', 'month'), MS, R('budget', 'category')), 'money'),
        FF('Payments this month', 'COUNTIFS(%s,{pick},%s,%s,%s,"")' % (TXR('category'), TXR('month'), MS, TXR('from_goal')), 'int'),
        FF('Share of all counted spending this month', 'IFERROR(SUMIFS(%s,%s,{pick},%s,%s)/SUMIFS(%s,%s,%s),0)' % (TXR('counted'), TXR('category'), TXR('month'), MS, TXR('counted'), TXR('month'), MS), 'pct'),
        FF('Largest payment this month', 'SUMPRODUCT(MAX((%s={pick})*(%s>=%s)*(%s)))' % (TXR('category'), TXR('date'), MS, TXR('amount')), 'money')]),
    FORM('budget_line_sheet', 'Budget Line Change Sheet', 'One plan line and the plan to suggest', 'budget.plan_id', F(
        ('Month', 'budget.month'), ('Category', 'budget.category'), ('Group', 'budget.group'), ('Planned a month', 'budget.planned')) + [
        FF('Actual so far in that month', ACTM(LK('budget', 'category'), LK('budget', 'month')), 'money'),
        FF('Over (+) or under (-) the plan', '%s-%s' % (ACTM(LK('budget', 'category'), LK('budget', 'month')), LK('budget', 'planned')), 'money'),
        FF('Average of the last 3 complete months', 'SUMIFS(%s,%s,%s,%s,">="&EDATE(%s,-3),%s,"<"&%s)/3' % (R('pva', 'actual'), R('pva', 'category'), LK('budget', 'category'), R('pva', 'month'), MS, R('pva', 'month'), MS), 'money'),
        FF('Suggested plan with the trend, nearest 5', 'ROUND(SUMIFS(%s,%s,%s,%s,">="&EDATE(%s,-3),%s,"<"&%s)/3*(1+{set:plan_trend})/5,0)*5' % (R('pva', 'actual'), R('pva', 'category'), LK('budget', 'category'), R('pva', 'month'), MS, R('pva', 'month'), MS), 'money'),
        FF('Trend used', '{set:plan_trend}', 'pct')]),
    FORM('weekly_allow_sheet', 'Weekly Allowance Sheet', 'The weekly allowance of one envelope', 'envelopes.envelope', F(
        ('Category', 'envelopes.category'), ('Weekly allowance', 'envelopes.weekly'), ('Week starts on', 'envelopes.start_day'), ('Monthly allowance', 'envelopes.monthly')) + [
        FF('Spent this month so far', 'SUMIFS(%s,%s,%s,%s,%s,%s,"")' % (TXR('amount'), TXR('category'), LK('envelopes', 'category'), TXR('month'), MS, TXR('from_goal')), 'money'),
        FF('Weekly average, last 3 complete months', 'SUMIFS(%s,%s,%s,%s,">="&EDATE(%s,-3),%s,"<"&%s)/(3*52/12)' % (R('pva', 'actual'), R('pva', 'category'), LK('envelopes', 'category'), R('pva', 'month'), MS, R('pva', 'month'), MS), 'money'),
        FF('Allowance against the last 3 months', 'IFERROR(%s/(SUMIFS(%s,%s,%s,%s,">="&EDATE(%s,-3),%s,"<"&%s)/(3*52/12)),0)' % (LK('envelopes', 'weekly'), R('pva', 'actual'), R('pva', 'category'), LK('envelopes', 'category'), R('pva', 'month'), MS, R('pva', 'month'), MS), 'pct'),
        FF('Allowance over a year', '%s*52' % LK('envelopes', 'weekly'), 'money')]),
    FORM('grocery_trip_sheet', 'Grocery Trip Sheet', 'One week of groceries against the allowance', 'grocery_week.week_start', F(
        ('Week of the month', 'grocery_week.wom'), ('Groceries spent', 'grocery_week.spent'), ('Weekly allowance', 'grocery_week.allowance'), ('Over or under', 'grocery_week.over_under'),
        ('Running total, 8 weeks', 'grocery_week.running'), ('Grocery payments', 'grocery_week.trips'), ('All spending that week', 'grocery_week.week_total')) + [
        FF('Average grocery payment that week', 'IFERROR(%s/%s,0)' % (LK('grocery_week', 'spent'), LK('grocery_week', 'trips')), 'money'),
        FF('Largest grocery payment that week', 'SUMPRODUCT(MAX((%s=%s)*(%s={pick})*(%s)))' % (TXR('category'), C_GRO, TXR('week_start'), TXR('amount')), 'money'),
        FF('Share of the weekly allowance used', 'IFERROR(%s/%s,0)' % (LK('grocery_week', 'spent'), LK('grocery_week', 'allowance')), 'pct'),
        FF('Share of all spending that week', 'IFERROR(%s/%s,0)' % (LK('grocery_week', 'spent'), LK('grocery_week', 'week_total')), 'pct')]),
    FORM('envelope_topup_sheet', 'Envelope Top-up Sheet', 'An envelope at today\'s pace and its top-up', 'env_status.envelope', F(
        ('Category', 'env_status.category'), ('Monthly allowance', 'env_status.allowance'), ('Spent so far', 'env_status.spent'), ('Left this month', 'env_status.left'), ('Can spend a day', 'env_status.per_day'),
        ('Pace at month end', 'env_status.month_end'), ('Pace flag', 'env_status.flag')) + [
        FF('Top-up needed at the current pace', 'MAX(0,%s-%s)' % (LK('env_status', 'month_end'), LK('env_status', 'allowance')), 'money'),
        FF('Share of the allowance used', 'IFERROR(%s/%s,0)' % (LK('env_status', 'spent'), LK('env_status', 'allowance')), 'pct'),
        FF('Weeks left in the month', '(%s-%s)/7' % (DIM, DAYN), 'num'),
        FF('Allowance for each week that remains', 'IFERROR(MAX(0,%s)/((%s-%s)/7),0)' % (LK('env_status', 'left'), DIM, DAYN), 'money')]),
    FORM('refund_sheet', 'Refund Sheet', 'A payment you want money back for', 'checks.tx_id', F(
        ('Date', 'checks.date'), ('Payee', 'checks.payee'), ('Category', 'checks.category'), ('Amount', 'checks.amount'), ('Check', 'checks.check_kind')) + [
        FF('Refund to ask for', LK('checks', 'amount'), 'money'), FF('Days since the payment', '{today}-%s' % LK('checks', 'date'), 'int'),
        FF('Payments to this payee, last 12 months', 'COUNTIFS(%s,%s,%s,">="&({today}-365))' % (TXR('payee'), LK('checks', 'payee'), TXR('date')), 'int'),
        FF('Share of the category that month', 'IFERROR(%s/SUMIFS(%s,%s,%s,%s,%s),0)' % (LK('checks', 'amount'), TXR('amount'), TXR('category'), LK('checks', 'category'), TXR('month'),
                                                                                    'DATE(YEAR(%s),MONTH(%s),1)' % (LK('checks', 'date'), LK('checks', 'date'))), 'pct')]),
    FORM('cash_spending_sheet', 'Cash Spending Sheet', 'Money out of one account', 'accounts.account_id', F(
        ('Account', 'accounts.account'), ('Type', 'accounts.type'), ('Owner', 'accounts.owner'), ('Balance now', 'accounts.balance_now'), ('Money out, last 30 days', 'accounts.spent_30d')) + [
        FF('Money out a day, last 30 days', '%s/30' % LK('accounts', 'spent_30d'), 'money'),
        FF('Share of all money out, last 30 days', 'IFERROR(%s/SUM(%s),0)' % (LK('accounts', 'spent_30d'), R('accounts', 'spent_30d')), 'pct'),
        FF('Days the balance covers at this pace', 'IFERROR(%s/(%s/30),0)' % (LK('accounts', 'balance_now'), LK('accounts', 'spent_30d')), 'int'),
        FF('Payments from this account, last 30 days', 'COUNTIFS(%s,%s,%s,">="&({today}-30))' % (TXR('account'), LK('accounts', 'account'), TXR('date')), 'int')]),
    FORM('dup_review_sheet', 'Duplicate Review Sheet', 'A possible duplicate payment to review', 'checks.tx_id', F(
        ('Date', 'checks.date'), ('Payee', 'checks.payee'), ('Amount', 'checks.amount'), ('Check', 'checks.check_kind'), ('Fix', 'checks.fix')) + [
        FF('Same payee and amount, days set', 'COUNTIFS(%s,%s,%s,%s,%s,">="&(%s-{set:dup_days}),%s,"<="&(%s+{set:dup_days}))' % (
            TXR('payee'), LK('checks', 'payee'), TXR('amount'), LK('checks', 'amount'), TXR('date'), LK('checks', 'date'), TXR('date'), LK('checks', 'date')), 'int'),
        FF('Money in those payments', 'COUNTIFS(%s,%s,%s,%s,%s,">="&(%s-{set:dup_days}),%s,"<="&(%s+{set:dup_days}))*%s' % (
            TXR('payee'), LK('checks', 'payee'), TXR('amount'), LK('checks', 'amount'), TXR('date'), LK('checks', 'date'), TXR('date'), LK('checks', 'date'), LK('checks', 'amount')), 'money'),
        FF('Likely extra payment to ask about', '(COUNTIFS(%s,%s,%s,%s,%s,">="&(%s-{set:dup_days}),%s,"<="&(%s+{set:dup_days}))-1)*%s' % (
            TXR('payee'), LK('checks', 'payee'), TXR('amount'), LK('checks', 'amount'), TXR('date'), LK('checks', 'date'), TXR('date'), LK('checks', 'date'), LK('checks', 'amount')), 'money'),
        FF('Days apart allowed in Settings', '{set:dup_days}', 'int')]),
    FORM('savings_goal_sheet', 'Savings Rate Goal Sheet', 'A month against your savings rate goal', 'savings_rate.month', F(
        ('Take-home after set-aside', 'savings_rate.take_home'), ('Retirement', 'savings_rate.retirement'), ('Saved into goals', 'savings_rate.saved'), ('Extra debt payments', 'savings_rate.debt_extra'),
        ('Total saved', 'savings_rate.total_saved'), ('Savings rate', 'savings_rate.savings_rate'), ('Against your best', 'savings_rate.flag')) + [
        FF('Savings rate you want', '{set:savings_rate_target}', 'pct'), FF('Saving needed for the goal', '{set:savings_rate_target}*%s' % LK('savings_rate', 'basis'), 'money'),
        FF('Saved above (+) or below (-) the goal', '%s-{set:savings_rate_target}*%s' % (LK('savings_rate', 'total_saved'), LK('savings_rate', 'basis')), 'money'),
        FF('Best savings rate in your history', 'MAX(%s)' % R('savings_rate', 'savings_rate'), 'pct')]),
    FORM('seasonal_sheet', 'Seasonal Spending Sheet', 'A category through the holiday season', 'categories.category', F(
        ('Group', 'categories.group'), ('Spent in the last Nov and Dec', 'categories.season_total'), ('Set aside a month for the next season', 'categories.season_month')) + [
        FF('Months until the next holiday season', _NM, 'int'),
        FF('Share of the category, last 12 months', 'IFERROR(%s/SUMIFS(%s,%s,{pick},%s,">="&({today}-365)),0)' % (LK('categories', 'season_total'), TXR('amount'), TXR('category'), TXR('date')), 'pct'),
        FF('Average a month, last 12 months', 'SUMIFS(%s,%s,{pick},%s,">="&({today}-365))/12' % (TXR('amount'), TXR('category'), TXR('date')), 'money'),
        FF('Season in months of normal spending', 'IFERROR(%s/(SUMIFS(%s,%s,{pick},%s,">="&({today}-365))/12),0)' % (LK('categories', 'season_total'), TXR('amount'), TXR('category'), TXR('date')), 'num')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('monthly_report_doc', 'Monthly Spending Report', 'Monthly spending report, planned against actual', 'savings_rate.month', [
        'Monthly spending report of {set:household}, dated {today}. Month: {col:savings_rate.month}.',
        'Counted spending: {col:savings_rate.spent}. Planned spending: {col:savings_rate.planned}. Left of the plan: {col:savings_rate.plan_left}. Same month last year: {col:savings_rate.spent_ly}.',
        'Needs (fixed bills and variable needs): {col:savings_rate.needs}. Wants: {col:savings_rate.wants}. Days with no variable spending: {col:savings_rate.no_spend_days} of {col:savings_rate.days}.',
        'Spending leaves out payments from a savings goal and debt payments, because card purchases are counted already. The figures are estimates from your own entries.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('overbudget_doc', 'Over-budget Report', 'Over-budget report for one category', 'overbudget.rank', [
        'Over-budget report of {set:household}, dated {today}. Rank {col:overbudget.rank}: {col:overbudget.category}.',
        'Over the plan to date by {col:overbudget.over_by}, which is {col:overbudget.share_over} above the plan for the days gone.',
        'In the last 3 complete months this category was over plan {col:overbudget.months_over} times. Suggested step: {col:overbudget.action}.',
        'Variable spending is compared with the plan pro-rated by days; bills and savings with the full month. A typical range, check your own numbers.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('groceries_doc', 'Groceries Weekly Page', 'Groceries for one week', 'grocery_week.week_start', [
        'Groceries page of {set:household}, dated {today}. Week starting {col:grocery_week.week_start} ({col:grocery_week.wom}).',
        'Groceries spent: {col:grocery_week.spent} in {col:grocery_week.trips} payments. Weekly allowance: {col:grocery_week.allowance}. Over or under the allowance: {col:grocery_week.over_under}.',
        'Running total of the last 8 weeks against the allowance: {col:grocery_week.running}. A positive total means the allowance was passed.',
        'Use the Groceries Envelope tool to see what you can spend a day for the rest of the month.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('category_doc', 'Spending by Category Page', 'Spending by category this month', 'this_month.category', [
        'Category page of {set:household}, dated {today}. Category: {col:this_month.category} ({col:this_month.group}).',
        'Planned this month: {col:this_month.planned}. Plan to date: {col:this_month.base}. Actual to date: {col:this_month.actual}. Over or under the plan: {col:this_month.variance}.',
        'Against the plan to date: {col:this_month.vs_plan}. Pace at month end: {col:this_month.pace_end}. Pace flag: {col:this_month.flag}.',
        'Spending paid from a savings goal is left out. Pace at month end is an estimate from your numbers.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('compare_doc', 'Compare Page', 'A category against your own history', 'compare.category', [
        'History page of {set:household}, dated {today}. Category: {col:compare.category}.',
        'This month to date: {col:compare.this_month}. Last 3 months, same days (average): {col:compare.avg3}. Same days last year: {col:compare.last_year}.',
        'Change on the 3-month average: {col:compare.change_avg}. Change on last year: {col:compare.change_ly}. Against 3 months: {col:compare.trend}.',
        'This page compares the household with its own history only; no national figure is used.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('savings_doc', 'Savings Rate Report', 'Savings rate report for one month', 'savings_rate.month', [
        'Savings rate report of {set:household}, dated {today}. Month: {col:savings_rate.month}.',
        'Take-home after set-aside: {col:savings_rate.take_home}. Retirement: {col:savings_rate.retirement}. Saved into goals: {col:savings_rate.saved}. Extra debt payments: {col:savings_rate.debt_extra}.',
        'Total saved: {col:savings_rate.total_saved}. Savings rate: {col:savings_rate.savings_rate}. Against your best: {col:savings_rate.flag}. Your own target: {set:savings_rate_target}.',
        'The savings rate is the total saved divided by take-home pay plus retirement. It is an estimate from your numbers, not advice.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('season_doc', 'Seasonal Spending Plan', 'Seasonal spending plan for one category', 'categories.category', [
        'Seasonal plan of {set:household}, dated {today}. Category: {col:categories.category} ({col:categories.group}).',
        'Spent in the last November and December: {col:categories.season_total}. Set aside each month until the next holiday season: {col:categories.season_month}.',
        'Money paid from a savings goal counts here, because the season costs that money too. Move the monthly amount to your goal on each payday.',
        'Both figures are estimates from your numbers; adapt the amount to the season ahead.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('weekly_doc', 'Weekly Spending Summary', 'Weekly spending summary', 'grocery_week.week_start', [
        'Weekly summary of {set:household}, dated {today}. Week starting {col:grocery_week.week_start}.',
        'All counted spending that week: {col:grocery_week.week_total} in {col:grocery_week.week_tx} payments. Of this, groceries: {col:grocery_week.spent} against an allowance of {col:grocery_week.allowance}.',
        'Allowance of the older child: {col:grocery_week.noa_allow}. Allowance of the younger child: {col:grocery_week.ike_allow}.',
        'Read this page together on the same day each week and agree what changes.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('envelope_doc', 'Envelope Status Page', 'Envelope status page', 'env_status.envelope', [
        'Envelope page of {set:household}, dated {today}. Envelope: {col:env_status.envelope} ({col:env_status.category}).',
        'Monthly allowance: {col:env_status.allowance}. Spent so far: {col:env_status.spent}. Left this month: {col:env_status.left}. Days left: {col:env_status.days_left}. You can spend {col:env_status.per_day} a day.',
        'Pace at month end: {col:env_status.month_end} ({col:env_status.flag}). This envelope week: spent {col:env_status.week_spent} of {col:env_status.week_allow}, left {col:env_status.week_left}.',
        'Pace is the spending so far divided by the days gone times the days in the month: an estimate from your numbers.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('ytd_doc', 'Year-to-date Page', 'Year-to-date spending for one category', 'categories.category', [
        'Year-to-date page of {set:household}, dated {today}. Category: {col:categories.category} ({col:categories.group}).',
        'Spent this year in the complete months: {col:categories.ytd}. Plan for the same months: {col:categories.ytd_plan}. Over (+) or under (-) the plan: {col:categories.ytd_diff}.',
        'The current month is not included until it is complete, so that every comparison uses whole months.',
        'Keep this page with your records for the year review.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('person_doc', 'Spending by Person Page', 'Spending paid by one partner', 'by_person.bp_id', [
        'Spending by person of {set:household}, dated {today}. Paid by: {col:by_person.paid_by}. Period: {col:by_person.period} ({col:by_person.from_date} to {col:by_person.to_date}).',
        'Counted spending paid: {col:by_person.amount} in {col:by_person.count} payments. Share of all counted spending in the period: {col:by_person.share}.',
        'This page shows who paid, not who owes whom. Use the shared-cost pages of the Partners, Kids and Shared Costs workbook to settle up.',
        'Figures are estimates from your own entries.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('monthend_doc', 'Month-end Note', 'Month-end note by group', 'monthgroup.mg_id', [
        'Month-end note of {set:household}, dated {today}. Month: {col:monthgroup.month}. Group: {col:monthgroup.group}.',
        'Amount for the group: {col:monthgroup.amount}. Share of the month: {col:monthgroup.share}.',
        'For the group Savings the amount is the deposits into goals plus retirement paid through payroll. Debt payments are shown on their own.',
        'Check the month against the plan on the Planned against Actual sheet before you close it.'], ['Partner 1', 'Partner 2'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('weekly_log_chk', 'Weekly Spending Log Steps', 'grocery_week', 'grocery_week.week_start', [('Collect receipts and statements', 0), ('Type or paste the payments into Transactions', 1), ('Set the category of every payment', 1), ('Check Envelope Status', 2), ('Read the Groceries by Week row', 2), ('Agree one change for next week', 3)]),
    CHK('weekly_groc_chk', 'Weekly Groceries Check Steps', 'grocery_week', 'grocery_week.week_start', [('Count the groceries spent in the week', 6), ('Compare with the weekly allowance', 6), ('Run the Groceries Envelope tool', 6), ('Set the allowance for the coming week', 7), ('Write the shopping list against the allowance', 7)]),
    CHK('month_close_chk', 'Month-end Spending Review Steps', 'savings_rate', 'savings_rate.month', [('Enter the last payments of the month', 30), ('Check Large and Duplicate Checks', 31), ('Fix every payment in the category Other', 31), ('Read Planned against Actual', 32), ('Read the Over-budget List', 32), ('Read Savings Rate by Month', 33), ('Write down one change for next month', 34)]),
    CHK('new_month_chk', 'New Month Plan Steps', 'budget', 'budget.month', [('Run the Plan Reset for the biggest categories', -5), ('Type the new plan lines in Budget plan', -3), ('Set the weekly allowance of each envelope', -2), ('Add known large payments and bills', -1), ('Check the savings lines against your savings rate goal', 0)]),
    CHK('clean_chk', 'Category Clean-up Steps', 'pva', 'pva.month', [('Run the Category Check', 28), ('Re-categorise payments in Other', 29), ('Merge categories you never use', 30), ('Check the group of each category', 31), ('Re-read Planned against Actual for the month', 32)]),
    CHK('overbudget_chk', 'Over-budget Follow-up Steps', 'pva', 'pva.month', [('List the categories over plan', 29), ('Run the Over-budget Ranker', 29), ('Decide: cut the spending or raise the plan', 30), ('Use the Plan Reset for the categories you raise', 31), ('Talk it through with your partner', 32), ('Check again in two weeks', 45)]),
    CHK('envelope_chk', 'Envelope Reset Steps', 'savings_rate', 'savings_rate.month', [('Read last month on the Envelope Status page', 30), ('Set each weekly allowance in Envelopes', 31), ('Move leftover money to a goal', 31), ('Run the Variable Envelopes Pace tool in week 2', 45), ('Top up an envelope only with a planned move', 50)]),
    CHK('nospend_chk', 'No-spend Month Steps', 'savings_rate', 'savings_rate.month', [('Choose the categories you pause', -3), ('Set the no-spend days you want', -2), ('Pre-pay the bills that fall due', -1), ('Check the No-spend Days tool each week', 7), ('Write the amount you kept', 31)]),
    CHK('season_chk', 'Seasonal Spending Prep Steps', 'budget', 'budget.month', [('Run the Seasonal Spike Planner', -120), ('Set the monthly amount aside', -90), ('List gifts, trips and extra bills', -60), ('Check the amount saved so far', -30), ('Set the plan for the season months', -14)]),
    CHK('receipts_chk', 'Receipts and Refunds Steps', 'transactions', 'transactions.date', [('Keep the receipt of the payment', 0), ('Type the payment into Transactions', 1), ('Note an expected refund', 2), ('Ask the shop or your bank about a missing refund', 14), ('Record the refund when it arrives', 30)]),
    CHK('ytd_chk', 'Year-to-date Review Steps', 'savings_rate', 'savings_rate.month', [('Open the Year-to-date Page of each big category', 30), ('Compare with the Compare Page', 31), ('Note the categories that rose most', 31), ('Reset the plan for the rest of the year', 33), ('Update your savings rate goal', 34)]),
    CHK('single_chk', 'Single Adult First Month Steps', 'transactions', 'transactions.date', [('Set your name and savings rate goal in Settings', 0), ('Use one account and Paid by Partner 1', 1), ('Type your first week of payments', 7), ('Write a plan for each category you use', 14), ('Leave partner 2, children and allowance rows empty', 14), ('Review the month with the Planned vs Actual Check', 30)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('p2_groc', 'Partner 2: groceries are over plan', 'env_status', 'env_status.p2_phone', 'Hello {partner2}, {category} is {over_share} over the allowance to date this month: {spent} spent so far. Shall we slow down? {household}'),
    M('p2_perday', 'Partner 2: what we can spend a day', 'env_status', 'env_status.p2_phone', 'Hello {partner2}, we can spend {per_day} a day on {category} for the next {days_left} days to stay on plan. {household}'),
    M('p2_over', 'Partner 2: a category is over plan', 'this_month', 'this_month.p2_phone', 'Hello {partner2}, {category} is over plan by {over_amt} this month so far. Shall we adjust the plan or the spending? {household}'),
    M('p2_eating', 'Partner 2: eating out against plan', 'this_month', 'this_month.p2_phone', 'Hello {partner2}, {category} is {actual} so far this month against {base} planned to date. {household}'),
    M('p2_receipts', 'Partner 2: please log your receipts', 'grocery_week', 'grocery_week.p2_phone', 'Hello {partner2}, please log your receipts from the week of {week_start}. We need them for the month-end review. {household}'),
    M('p1_allow', 'Partner 1: the groceries allowance', 'grocery_week', 'grocery_week.p1_phone', 'Hello {partner1}, the weekly groceries allowance is {allowance} and we spent {spent} in the week of {week_start}. {household}'),
    M('p1_spend', 'Partner 1: spending against plan', 'savings_rate', 'savings_rate.p1_phone', 'Hello {partner1}, spending for {month} is {spent} against {planned} planned. {household}'),
    M('p1_rate', 'Partner 1: the savings rate', 'savings_rate', 'savings_rate.p1_phone', 'Hello {partner1}, the savings rate for {month} is {savings_rate}: {total_saved} saved from {basis}. {household}'),
    M('p1_up', 'Partner 1: a category is up on last year', 'compare', 'compare.p1_phone', 'Hello {partner1}, {category} is up {change_ly} on the same days last year. Shall we look at it? {household}'),
    M('p1_large', 'Partner 1: please check a large payment', 'checks', 'checks.p1_phone', 'Hello {partner1}, please check the large payment of {amount} to {payee} on {date}. {household}'),
    M('p1_dup', 'Partner 1: a possible duplicate payment', 'checks', 'checks.p1_phone', 'Hello {partner1}, there may be a duplicate payment to {payee} on {date}, {amount}. Please check with me. {household}'),
    M('hm_week', 'Household member: weekly summary', 'grocery_week', 'grocery_week.member_phone', 'Hello Ada, the weekly spending summary for the week of {week_start} is ready: {week_total} in {week_tx} payments. {household}'),
    M('hm_review', 'Household member: the month-end review', 'savings_rate', 'savings_rate.member_phone', 'Hello Ada, the month-end review for {month} is on {month_end}. Please send your receipts before then. {household}'),
    M('hm_fuel', 'Household member: envelope nearly used', 'env_status', 'env_status.member_phone', 'Hello Ada, the {envelope} envelope is nearly used: {left} left for the next {days_left} days. {household}'),
    M('hm_holiday', 'Household member: holiday plan', 'categories', 'categories.member_phone', 'Hello Ada, for {category} we plan to set aside {season_month} a month for the holiday season. {household}'),
    M('hm_spent', 'Household member: what we spent', 'pva', 'pva.member_phone', 'Hello Ada, we spent {actual} on {category} in {month}, against {planned} planned. {household}'),
    M('gp_school', 'Grandparent: school run thanks', 'env_status', 'env_status.member_phone', 'Hello Ada, thank you for the school run. Here is the {envelope} top-up of {week_allow} for the week from {date}. {household}'),
    M('noa_allow', 'Child (Noa): your weekly allowance', 'grocery_week', 'grocery_week.noa_phone', 'Hello Noa, your weekly allowance of {noa_allow} is ready on {week_start}. {household}'),
    M('ike_allow', 'Child (Ike): your weekly allowance', 'grocery_week', 'grocery_week.ike_phone', 'Hello Ike, your weekly allowance of {ike_allow} is ready on {week_start}. {household}'),
    M('noa_year', 'Child (Noa): allowance over a year', 'payees', 'payees.noa_phone', 'Hello Noa, your allowance came to {amount12} over the last 12 months in {count12} payments. Well done for planning how you use it. {household}'),
    M('ike_year', 'Child (Ike): allowance over a year', 'payees', 'payees.ike_phone', 'Hello Ike, your allowance came to {amount12} over the last 12 months in {count12} payments. Well done for planning how you use it. {household}'),
    M('bk_unknown', 'Bank branch: payment not recognised', 'checks', 'checks.bank_phone', 'Hello Elif, we see a payment of {amount} to {payee} on {date} that we do not recognise. Please check it for us. {household}'),
    M('bk_refund', 'Bank branch: a refund is missing', 'checks', 'checks.bank_phone', 'Hello Elif, a refund of {amount} from {payee} is missing since {date}. Please tell us what you see on your side. {household}'),
    M('bk_once', 'Bank branch: confirm one payment', 'checks', 'checks.bank_phone', 'Hello Elif, please confirm that the payment of {amount} on {date} to {payee} was taken once. {household}'),
    M('bk_stmt', 'Bank branch: send the statement', 'savings_rate', 'savings_rate.bank_phone', 'Hello Elif, please send the statement for {month} for our records. {household}'),
    M('sc_amount', 'School office: confirm the amount', 'pva', 'pva.school_phone', 'Hello Ruth, please confirm the amount of {actual} charged for {month}. {household}'),
    M('sc_receipt', 'School office: we need the receipt', 'pva', 'pva.school_phone', 'Hello Ruth, we need the receipt for the trip payment in {month}, {actual}. Please send it when you can. {household}'),
    M('mc_invoice', 'Car mechanic: send the invoice', 'pva', 'pva.mech_phone', 'Hello Pavel, please send the invoice for the service in {month}, {actual}. {household}'),
    M('mc_paid', 'Car mechanic: please confirm our payment', 'pva', 'pva.mech_phone', 'Hello Pavel, we paid {actual} in {month}. Please confirm that you have it. {household}'),
    M('ut_diff', 'Utility company: explain the difference', 'pva', 'pva.util_phone', 'Hello Yara, we see {actual} charged in {month} against {planned} planned. Please explain the difference. {household}'),
    M('in_premium', 'Insurance agent: confirm the premium', 'pva', 'pva.ins_phone', 'Hello Carlos, we see a charge of {actual} in {month}. Please confirm the premium. {household}'),
    M('tx_work', 'Tax preparer: work expenses', 'pva', 'pva.tax_phone', 'Hello Aiko, here is the list of work expenses for {month}, total {actual}. {household}'),
    M('tx_child', 'Tax preparer: childcare costs', 'pva', 'pva.tax_phone', 'Hello Aiko, here is the list of childcare costs for {month}, total {actual}. {household}'),
    M('p2_closed', 'Partner 2: the month is closed', 'savings_rate', 'savings_rate.p2_phone', 'Hello {partner2}, spending for {month} is closed: {spent} against {planned}, {plan_left} left of the plan. {household}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def TXC(): return R('transactions', 'counted')
def MON(m): return 'SUMIFS(%s,%s,%s)' % (TXC(), R('transactions', 'month'), m)
def CATM(c): return 'SUMIFS(%s,%s,%s,%s,%s,%s,"")' % (R('transactions', 'amount'), R('transactions', 'category'), c, R('transactions', 'month'), MS, R('transactions', 'from_goal'))
TMc = lambda c: R('this_month', c)
SRc = lambda c: R('savings_rate', c)
L30 = '%s,">="&({today}-30),%s,"<="&{today}' % (R('transactions', 'date'), R('transactions', 'date'))
LAST3 = '%s,">="&EDATE(%s,-3),%s,"<"&%s' % (SRc('month'), MS, SRc('month'), MS)
GROC = lambda c: 'SUMIFS(%s,%s,%s)' % (R('env_status', c), R('env_status', 'category'), C_GRO)
WANTS_M = 'SUMIFS(%s,%s,%s,%s,%s)' % (TXC(), R('transactions', 'month'), MS, R('transactions', 'group'), G_WANT)
kpis = [
    KPI('Spending this month to date', MON(MS), 'money'), KPI('Spending last 30 days', 'SUMIFS(%s,%s)' % (TXC(), L30), 'money'), KPI('Spending last month', MON('EDATE(%s,-1)' % MS), 'money'),
    KPI('Spending same month last year', MON('EDATE(%s,-12)' % MS), 'money'), KPI('Planned spending this month', 'SUMIFS(%s,%s,1)' % (TMc('planned'), TMc('counts')), 'money'),
    KPI('Spending against plan to date', 'IFERROR(SUMIFS(%s,%s,1)/SUMIFS(%s,%s,1),0)' % (TMc('actual'), TMc('counts'), TMc('base'), TMc('counts')), 'pct'),
    KPI('Groceries this month to date', GROC('spent'), 'money'), KPI('Groceries planned to date', GROC('to_date'), 'money'), KPI('Groceries pace against plan', 'IFERROR(%s/%s,0)' % (GROC('spent'), GROC('to_date')), 'pct'),
    KPI('Eating out this month', CATM(C_EAT), 'money'), KPI('Fuel and transport this month', CATM(C_FUEL), 'money'), KPI('Shopping this month', CATM(C_SHOP), 'money'),
    KPI('Kids and family this month', CATM(C_KIDS), 'money'), KPI('Categories over plan this month', 'COUNTIFS(%s,%s,%s,1)' % (TMc('flag'), pace('Over pace'), TMc('counts')), 'int'),
    KPI('Biggest overspend amount', 'MAX(%s)' % TMc('over_amt'), 'money'), KPI('Largest payment last 30 days', 'SUMPRODUCT(MAX((%s>={today}-30)*(%s)))' % (R('transactions', 'date'), R('transactions', 'amount')), 'money'),
    KPI('Payments last 30 days', 'COUNTIFS(%s,%s,"<>")' % (L30, R('transactions', 'tx_id')), 'int'), KPI('Average daily spending last 30 days', 'SUMIFS(%s,%s)/30' % (TXC(), L30), 'money'),
    KPI('Variable spending you can still do a day', 'IFERROR(MAX(0,SUMIFS(%s,%s,1)-SUMIFS(%s,%s,1))/(%s-%s),0)' % (TMc('planned'), TMc('var'), TMc('actual'), TMc('var'), DIM, DAYN), 'money'),
    KPI('Savings rate this month', 'INDEX(%s,MATCH(%s,%s,0))' % (SRc('savings_rate'), MS, SRc('month')), 'pct'),
    KPI('Savings rate last 3 months', 'IFERROR(SUMIFS(%s,%s)/SUMIFS(%s,%s),0)' % (SRc('total_saved'), LAST3, SRc('basis'), LAST3), 'pct'),
    KPI('Best savings rate in 12 months', 'MAX(%s)' % SRc('rate_12m'), 'pct'), KPI('Saved this month', 'INDEX(%s,MATCH(%s,%s,0))' % (SRc('total_saved'), MS, SRc('month')), 'money'),
    KPI('Needs spending this month', 'SUMIFS(%s,%s,%s,%s,%s)+SUMIFS(%s,%s,%s,%s,%s)' % (TXC(), R('transactions', 'month'), MS, R('transactions', 'group'), G_FIX, TXC(), R('transactions', 'month'), MS, R('transactions', 'group'), G_VAR), 'money'),
    KPI('Wants spending this month', WANTS_M, 'money'), KPI('Wants share of spending', 'IFERROR(%s/%s,0)' % (WANTS_M, MON(MS)), 'pct'),
    KPI('Spending paid by partner 1 this month', 'SUMIFS(%s,%s,%s,%s,%s)' % (TXC(), R('transactions', 'month'), MS, R('transactions', 'paid_by'), tok('payer', 'Partner 1')), 'money'),
    KPI('Spending paid by partner 2 this month', 'SUMIFS(%s,%s,%s,%s,%s)' % (TXC(), R('transactions', 'month'), MS, R('transactions', 'paid_by'), tok('payer', 'Partner 2')), 'money'),
    KPI('Possible duplicate payments, 12 months', 'COUNTIFS(%s,">="&({today}-365))' % R('transactions', 'dup_date'), 'int'),
    KPI('Payments in the category Other, 90 days', 'COUNTIFS(%s,%s,%s,">="&({today}-90))' % (R('transactions', 'category'), C_OTHER, R('transactions', 'date')), 'int'),
]
assert len(kpis) == 30
dashboard = {"title": "Spending Dashboard", "kpis": kpis,
    "monthly": {"title": "Spending, planned spending and saving by month", "date": "transactions.date", "series": [
        {"label": "Counted spending", "sum": "transactions.counted", "date": "transactions.date"}, {"label": "Planned spending", "sum": "savings_rate.planned", "date": "savings_rate.month"},
        {"label": "Total saved", "sum": "savings_rate.total_saved", "date": "savings_rate.month"}]},
    "breakdowns": [{"title": "Actual by category, complete months", "by": "pva.category", "value": "pva.actual", "agg": "sum"},
                   {"title": "Money out by account", "by": "transactions.account", "value": "transactions.amount", "agg": "sum"},
                   {"title": "Counted spending by who paid", "by": "transactions.paid_by", "value": "transactions.counted", "agg": "sum"},
                   {"title": "Year to date by group", "by": "categories.group", "value": "categories.ytd", "agg": "sum"}]}

def AM(t, c, date=None, label=None, where=None): return AGG('sum', t, '%s.%s' % (t, c), date=('%s.%s' % (t, date)) if date else None, where=where, label=label)
TXD_ = lambda c, label, cat_: AGG('sum', 'transactions', 'transactions.amount', date='transactions.date', where=[('category', '=', cat_)], label=label)
MG = lambda g, label: AGG('sum', 'monthgroup', 'monthgroup.amount', date='monthgroup.month', where=[('group', '=', g)], label=label)
insights = {"filters": [{"label": "Category", "list": "category"}, {"label": "Paid by", "list": "payer"}, {"label": "Account", "list": "spendacct"}],
    "gauges": [
        {"title": "Spending against plan to date", "num": AGG('sum', 'this_month', 'this_month.actual', where=[('counts', '=', 1)]), "den": AGG('sum', 'this_month', 'this_month.base', where=[('counts', '=', 1)])},
        {"title": "Groceries against plan pro-rated", "num": AGG('sum', 'env_status', 'env_status.spent', where=[('category', '=', C_GRO)]), "den": AGG('sum', 'env_status', 'env_status.to_date', where=[('category', '=', C_GRO)])},
        {"title": "Categories within plan", "num": AGG('count', 'this_month', where=[('counts', '=', 1), ('flag', '<>', pace('Over pace'))]), "den": AGG('count', 'this_month', where=[('counts', '=', 1)])},
        {"title": "Savings rate, all months", "num": AGG('sum', 'savings_rate', 'savings_rate.total_saved'), "den": AGG('sum', 'savings_rate', 'savings_rate.basis')},
        {"title": "Wants share of counted spending", "num": AGG('sum', 'monthgroup', 'monthgroup.amount', where=[('group', '=', G_WANT)]), "den": AGG('sum', 'savings_rate', 'savings_rate.spent')},
        {"title": "Days with no variable spending", "num": AGG('sum', 'savings_rate', 'savings_rate.no_spend_days'), "den": AGG('sum', 'savings_rate', 'savings_rate.days')}],
    "charts": [
        CHART('Spending per month', 'column', 'month', [AM('transactions', 'counted', 'date', 'Counted spending')]),
        CHART('Spending by group per month', 'stacked', 'month', [MG(G_FIX, 'Fixed bills'), MG(G_VAR, 'Variable needs'), MG(G_WANT, 'Wants'), MG(G_DEBT, 'Debt payments')]),
        CHART('Spending by category this year', 'bar', 'pva.category', [AM('pva', 'actual', 'month', 'Actual')]),
        CHART('Planned and actual per month', 'column', 'month', [AM('savings_rate', 'planned', 'month', 'Planned spending'), AM('savings_rate', 'spent', 'month', 'Counted spending')]),
        CHART('Planned and actual by category', 'bar', 'pva.category', [AM('pva', 'planned', 'month', 'Planned'), AM('pva', 'actual', 'month', 'Actual')]),
        CHART('Variance by category', 'bar', 'pva.category', [AM('pva', 'variance', 'month', 'Over or under plan')]),
        CHART('Groceries per month', 'line', 'month', [TXD_('', 'Groceries', C_GRO)]),
        CHART('Groceries per week of the month', 'bar', 'grocery_week.wom', [AGG('avg', 'grocery_week', 'grocery_week.spent', label='Spent'), AGG('avg', 'grocery_week', 'grocery_week.allowance', label='Allowance')]),
        CHART('Eating out per month', 'line', 'month', [TXD_('', 'Eating out', C_EAT)]),
        CHART('Fuel and transport per month', 'line', 'month', [TXD_('', 'Fuel and transport', C_FUEL)]),
        CHART('Shopping per month', 'column', 'month', [TXD_('', 'Shopping', C_SHOP)]),
        CHART('Kids and family per month', 'column', 'month', [TXD_('', 'Kids and family', C_KIDS)]),
        CHART('Spending by account', 'bar', 'transactions.account', [AM('transactions', 'amount', 'date', 'Money out')]),
        CHART('Spending by person, last 12 months', 'bar', 'by_person.paid_by', [AGG('sum', 'by_person', 'by_person.amount', where=[('period', '=', per('Last 12 months'))], label='Counted spending')]),
        CHART('Spending by weekday, last 12 months', 'bar', 'weekday.weekday', [AGG('sum', 'weekday', 'weekday.amount', where=[('period', '=', per('Last 12 months'))], label='Counted spending')]),
        CHART('Spending by payee, top 20', 'bar', 'payees.payee', [AGG('sum', 'payees', 'payees.amount12', label='Last 12 months')]),
        CHART('Needs, wants and savings per month', 'stacked', 'month', [AM('savings_rate', 'needs', 'month', 'Needs'), AM('savings_rate', 'wants', 'month', 'Wants'), AM('savings_rate', 'total_saved', 'month', 'Saved')]),
        CHART('Savings rate per month', 'line', 'month', [AM('savings_rate', 'savings_rate', 'month', 'Savings rate')]),
        CHART('Savings per month', 'column', 'month', [AM('savings_rate', 'total_saved', 'month', 'Total saved')]),
        CHART('Seasonal categories per month', 'stacked', 'month', [TXD_('', 'Gifts', cat('Gifts')), TXD_('', 'Holidays and trips', cat('Holidays and trips')), TXD_('', 'Utilities', cat('Utilities')), TXD_('', 'Childcare and school', cat('Childcare and school'))]),
        CHART('Large payments per month', 'column', 'month', [AGG('sum', 'transactions', 'transactions.amount', date='transactions.date', where=[('amount', '>=', '{set:large_payment}'), ('group', '<>', G_FIX), ('group', '<>', G_DEBT), ('group', '<>', G_SAV)], label='Large variable payments')]),
        CHART('Spending this year against last year', 'column', 'month', [AM('savings_rate', 'spent', 'month', 'This year'), AM('savings_rate', 'spent_ly', 'month', 'Same month last year')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Planned against actual, pro-rated by days", "why": "every category this month to date against a plan that counts days, so groceries 18% over plan shows today, not at month end", "where": "Planned vs Actual Check"},
    {"name": "Month-end pace", "why": "spending to date divided by days gone times days in the month, with a payment still to come, tells you the overspend before it happens", "where": "Month-end Pace"},
    {"name": "Groceries envelope", "why": "a weekly allowance, spent so far, days left and what you can spend a day, with a verdict", "where": "Groceries Envelope"},
    {"name": "Compare with my own history", "why": "this month to date against the same days of the last 3 months and a year ago for all 28 categories, with no national figure", "where": "Compare with My History"},
    {"name": "Savings rate solver", "why": "the monthly, weekly and per-paycheck saving that reaches your own savings rate target, worked out from your last 3 months", "where": "Savings Rate Solver"},
    {"name": "Plan reset", "why": "a new plan per category from the last 3 complete months times a trend, rounded to a number you can use", "where": "Plan Reset"},
    {"name": "Small leaks finder", "why": "frequent small payments by payee over 90 days added up per month, with what you keep if you stop a share", "where": "Small Leaks Finder"},
    {"name": "Envelope status", "why": "twelve weekly allowances with spent, left, days left, a daily amount and a pace flag in one table", "where": "Envelope status"},
    {"name": "Over-budget list", "why": "categories over plan ranked by amount with how often each was over in the last 3 complete months", "where": "Over-budget list"},
    {"name": "Seasonal spike planner", "why": "last year's holiday, back-to-school or winter bills above a normal month, spread over the months you have to save", "where": "Seasonal Spike Planner"},
    {"name": "Duplicate payment finder", "why": "the same payee and amount within days, flagged in the log and listed with the second payment to ask about", "where": "Duplicate Payment Finder"}]
competitors = [
    {"what": "budgeting app with a monthly subscription and bank links", "lacks": "charges every month, breaks when a bank link changes and cannot compare a category with your own last 3 months or last year"},
    {"what": "single-purpose budget template", "lacks": "lists planned and actual per month but has no pro-rated plan, no pace at month end and no groceries envelope"},
    {"what": "expense tracker sheet", "lacks": "logs payments but never finds duplicates, small leaks or payments sitting in the category Other"},
    {"what": "free monthly budget printable", "lacks": "gives a blank grid with no savings rate against your own best month, no seasonal set-aside and no who-paid view"}]
guide = [
    'Start here: open Start and type the household name, the two partner names, the savings rate you want and the limits for a large payment and a small leak in the yellow cells.',
    'Replace demo data, step 1: clear the demo rows of Transactions, Income, Contributions and Debt payments, keep the header row, and keep Categories and Accounts as your own lists.',
    'Replace demo data, step 2: write your Budget plan for this month and the months ahead, one row for each category and month; a zero is fine for a category you do not use.',
    'Replace demo data, step 3: set a weekly allowance for each envelope in Envelopes; the Envelope status and Groceries by week sheets follow at once.',
    'Pay-day routine: when a paycheck arrives, type it in Income (take-home, set-aside, retirement), add the money you move to savings in Contributions and any extra card or loan payment in Debt payments.',
    'Weekly routine: type or paste the week of payments into Transactions, open Envelope status and Groceries by week, then run the Groceries Envelope and the Month-end Pace.',
    'Month-close routine, in this order: check Large and duplicate checks, clear the category Other, read Planned against actual and the Over-budget list, read Savings rate by month, then set next month in Budget plan with the Plan Reset.',
    'Compare with own history, the savings rate and the seasonal planner use only your own numbers; any range shown is a typical range, check your own numbers.',
    'A single adult with one income and no children can use most sheets: use one account, set Paid by to Partner 1 and leave the partner 2, children and allowance rows empty.',
    f'Use the {len(tools)} calculators for the weekly and monthly money questions, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'Read the Spending Dashboard and the Charts page every week: spending against plan, groceries pace, savings rate and the biggest categories.',
    'Why a workbook: one flat price, no yearly renewal, your data stays with you and there is nothing to link or re-connect; you type or paste your own data. It works in Excel and Google Sheets with no macros.',
    'What this is not: it is not a bank app, and not tax, legal, investment or credit advice; every verdict is an estimate from your numbers.']
listing = {"title": "Household Spending Tracker and Groceries Excel Template: Planned vs Actual, Groceries Envelope, Savings Rate, Budget Planner",
    "headline": "See where the money goes and fix it before the month ends",
    "tags": ["budget planner", "spending tracker", "expense tracker", "groceries budget", "planned vs actual", "savings rate", "envelope budget", "household budget", "excel template", "family budget", "monthly budget", "no subscription", "budget workbook"],
    "description": ("Run your household spending in one Excel workbook, for a single adult, a couple or a family. Type or paste your payments and the workbook shows where the money goes: planned against actual by category and month, this month to date against the plan pro-rated by days, "
        "the pace at month end, and an over-budget list ranked by amount. Groceries and variable spending run on weekly envelopes with spent so far, days left and what you can spend a day.\n\n"
        "The Compare with Own History sheet sets every category this month to date against the same days of the last 3 months and the same days a year ago, so you compare with your own numbers, never a national figure. Savings Rate by Month adds savings into goals, extra debt payments and retirement over take-home pay and flags your best month. "
        "Spending by Month and Group, by Payee, by Person and by Weekday show who pays what and when, and the Large and Duplicate Checks sheet lists possible duplicate payments, large payments and anything left in the category Other.\n\n"
        f"{len(tools)} calculators answer the weekly and monthly questions: planned against actual, the over-budget ranker, month-end pace, the groceries envelope, a weekly allowance setter, savings rate and a savings rate solver, no-spend days, eating out and fuel watches, a seasonal spike planner, a plan reset and a small leaks finder. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to a partner, a household member, the children and your bank branch, the school office and others.\n\n"
        "This is part three of the Household Finance suite. A standard .xlsx workbook that works in Excel and Google Sheets, with no macros, no subscription and no bank links: you type or paste your own data. The demo copy is full of sample data. "
        "It is a household money kit, not a bank app, and not tax, legal, investment or credit advice. Savings rates, paces and plans are estimates from your own numbers."),
    "features": ["Planned against actual by category and month", "This month to date against the plan pro-rated by days", "Groceries and variable envelopes with a daily amount", "Compare with your own history, never a national figure",
                 "Savings rate by month against your own best", "Over-budget list ranked by amount", f"{len(tools)} calculators for weekly money questions", "Duplicate, large and Other-category payment checks",
                 f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "One flat price, no subscription, no bank links"]}
s = spec(id=f'{SUITE}-p3', slug='household-finance-spending', profession='Household Finance', name='Spending Tracker and Groceries',
         tagline='See where the money goes and fix it before the month ends', price_usd=29,
         colors={"primary": "#1F5F5B", "accent": "#F2B134"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 3, "of": 8, "focus": "Spending tracker and groceries"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hf3.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
