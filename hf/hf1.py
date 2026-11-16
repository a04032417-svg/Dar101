"""Household Finance suite - part 1: Money Plan and Paychecks."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf1_lists import *
from hf1_tables import settings, tables, R, B0, NP, UNP, MS, YES, PAID_B, PAID_I, P1, P2, WIND, SIDE, PAYCK, G_FIX, G_VAR, G_WANT, G_SAVE, G_DEBT, WEEKLY, BIWK, TWICE, UNDER, ABOVE
from hf1_tools import tools, TH, BASE0, LOWNP
import hf1_data as D

SUITE = 'fx-20261116-household-finance'
NOTE = "Sample wording: adapt it to your own household and check your local rules."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
PERIODS_PICK = 'IF(%s=%s,52,IF(%s=%s,26,IF(%s=%s,24,12)))'
def PER(col): return PERIODS_PICK % (col, WEEKLY, col, BIWK, col, TWICE)

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('paycheck_entry', 'Paycheck Entry Sheet', 'One payment received, line by line', 'income.income_id', F(
        ('Received on', 'income.date'), ('Person', 'income.person'), ('Source', 'income.source'), ('Gross', 'income.gross'), ('Tax', 'income.tax'), ('Retirement', 'income.retirement'),
        ('Other deductions', 'income.other_deductions'), ('Deductions', 'income.deductions'), ('Take-home', 'income.net'), ('Set aside', 'income.set_aside'), ('Account ID', 'income.account_id'), ('Share of the month', 'income.share_of_month')) + [
        FF('Take-home share of gross', 'IFERROR(%s/%s,0)' % (LK('income', 'income_id', 'net'), LK('income', 'income_id', 'gross')), 'pct'),
        FF('Take-home after the set-aside', '%s-%s' % (LK('income', 'income_id', 'net'), LK('income', 'income_id', 'set_aside')), 'money'),
        FF('Payments received this month', 'COUNTIFS({range:income.month},%s)' % MS, 'int')]),
    FORM('freelance_invoice', 'Freelance Invoice Sheet', 'Freelance invoice and what to set aside', 'invoices.invoice_id', F(
        ('Client', 'invoices.client'), ('Client contact', 'invoices.contact'), ('Issued', 'invoices.issued'), ('Due date', 'invoices.due_date'), ('Amount', 'invoices.amount'), ('Status', 'invoices.status'),
        ('Paid on', 'invoices.paid_on'), ('Days to pay', 'invoices.days_to_pay'), ('Days late', 'invoices.days_late'), ('Usual days late of this client', 'invoices.usual_delay')) + [
        FF('Share to set aside', '{set:set_aside_pct}', 'pct'), FF('Set aside from this invoice', 'ROUND(%s*{set:set_aside_pct},2)' % LK('invoices', 'invoice_id', 'amount'), 'money'),
        FF('Left after the set-aside', 'ROUND(%s*(1-{set:set_aside_pct}),2)' % LK('invoices', 'invoice_id', 'amount'), 'money'),
        FF('Days from issue to the due date', '%s-%s' % (LK('invoices', 'invoice_id', 'due_date'), LK('invoices', 'invoice_id', 'issued')), 'int')]),
    FORM('payment_received', 'Payment Received Sheet', 'Payment received for an invoice', 'invoices.invoice_id', F(
        ('Client', 'invoices.client'), ('Invoice amount', 'invoices.amount'), ('Paid on', 'invoices.paid_on'), ('Days to pay', 'invoices.days_to_pay'), ('Days late', 'invoices.days_late')) + [
        FF('Income record', 'IFERROR(INDEX({range:income.income_id},MATCH({pick},{range:income.invoice_id},0)),"")', 'text'),
        FF('Received in account', 'IFERROR(INDEX({range:income.account_id},MATCH({pick},{range:income.invoice_id},0)),"")', 'text'),
        FF('Take-home recorded', 'IFERROR(INDEX({range:income.net},MATCH({pick},{range:income.invoice_id},0)),0)', 'money'),
        FF('Set aside recorded', 'IFERROR(INDEX({range:income.set_aside},MATCH({pick},{range:income.invoice_id},0)),0)', 'money'),
        FF('Difference to the invoice', '%s-IFERROR(INDEX({range:income.net},MATCH({pick},{range:income.invoice_id},0)),0)' % LK('invoices', 'invoice_id', 'amount'), 'money'),
        FF('Open invoices of all clients', 'SUMIFS({range:invoices.amount},{range:invoices.status},"<>"&%s)' % PAID_I, 'money')]),
    FORM('pay_schedule_sheet', 'Pay Schedule Sheet', 'One pay date and its split', 'pay_schedule.pay_id', F(
        ('Pay date', 'pay_schedule.date'), ('Person', 'pay_schedule.person'), ('Source', 'pay_schedule.source'), ('Pay rhythm', 'pay_schedule.frequency'), ('Expected take-home', 'pay_schedule.expected_net'),
        ('Pay days in the month', 'pay_schedule.pays_in_month'), ('Extra pay month', 'pay_schedule.extra_pay_month'), ('Days away', 'pay_schedule.days_away'), ('Split: bills', 'pay_schedule.split_bills'),
        ('Split: sinking funds', 'pay_schedule.split_sinking'), ('Split: debt', 'pay_schedule.split_debt'), ('Split: goals and savings', 'pay_schedule.split_goals'), ('Split: spending money', 'pay_schedule.split_spend')) + [
        FF('Paychecks a year at this rhythm', PER(LK('pay_schedule', 'pay_id', 'frequency')), 'int'),
        FF('Yearly take-home at this rhythm', '%s*%s' % (LK('pay_schedule', 'pay_id', 'expected_net'), PER(LK('pay_schedule', 'pay_id', 'frequency'))), 'money')]),
    FORM('account_sheet', 'Account Sheet', 'One account with its balance and change', 'accounts.account_id', F(
        ('Account', 'accounts.account'), ('Type', 'accounts.type'), ('Owner', 'accounts.owner'), ('Opening balance', 'accounts.opening_balance'), ('Balance now', 'accounts.balance_now'), ('Change since opening', 'accounts.change')) + [
        FF('Change as a share of the opening balance', 'IFERROR(%s/%s,0)' % (LK('accounts', 'account_id', 'change'), LK('accounts', 'account_id', 'opening_balance')), 'pct'),
        FF('Share of all balances', 'IFERROR(%s/SUM({range:accounts.balance_now}),0)' % LK('accounts', 'account_id', 'balance_now'), 'pct'),
        FF('Accounts in the workbook', 'COUNTA({range:accounts.account_id})', 'int')]),
    FORM('budget_line_sheet', 'Budget Line Sheet', 'One budget line against its own history', 'budget.plan_id', F(
        ('Month', 'budget.month'), ('Category', 'budget.category'), ('Group', 'budget.group'), ('Planned', 'budget.planned')) + [
        FF('Share of the plan of the month', 'IFERROR(%s/SUMIFS({range:budget.planned},{range:budget.month},%s),0)' % (LK('budget', 'plan_id', 'planned'), LK('budget', 'plan_id', 'month')), 'pct'),
        FF('Average of the 3 months before', 'IFERROR(AVERAGEIFS({range:budget.planned},{range:budget.category},%s,{range:budget.month},">="&EDATE(%s,-3),{range:budget.month},"<"&%s),0)' % (LK('budget', 'plan_id', 'category'), LK('budget', 'plan_id', 'month'), LK('budget', 'plan_id', 'month')), 'money'),
        FF('Change against that average', 'IFERROR(%s/AVERAGEIFS({range:budget.planned},{range:budget.category},%s,{range:budget.month},">="&EDATE(%s,-3),{range:budget.month},"<"&%s)-1,0)' % (LK('budget', 'plan_id', 'planned'), LK('budget', 'plan_id', 'category'), LK('budget', 'plan_id', 'month'), LK('budget', 'plan_id', 'month')), 'pct'),
        FF('Planned a year at this amount', '%s*12' % LK('budget', 'plan_id', 'planned'), 'money')]),
    FORM('split_line_sheet', 'Paycheck Split Sheet', 'One line of the paycheck split', 'split_lines.line_id', F(
        ('Line', 'split_lines.line'), ('Kind', 'split_lines.kind'), ('Rule', 'split_lines.rule'), ('Percent of paycheck', 'split_lines.percent'), ('Priority', 'split_lines.priority')) + [
        FF('Amount on a standard paycheck', 'IFERROR(INDEX({range:alloc.amount},MATCH({pick},{range:alloc.line_id},0)),0)', 'money'),
        FF('Share of the paycheck', 'IFERROR(INDEX({range:alloc.amount},MATCH({pick},{range:alloc.line_id},0))/{set:paycheck_net},0)', 'pct'),
        FF('Left to assign after this line', 'IFERROR(INDEX({range:alloc.running_left},MATCH({pick},{range:alloc.line_id},0)),0)', 'money'),
        FF('Amount a month at your pay rhythm', 'IFERROR(INDEX({range:alloc.amount},MATCH({pick},{range:alloc.line_id},0))*%s/12,0)' % PER('{set:pay_freq}'), 'money')]),
    FORM('windfall_sheet', 'Windfall Sheet', 'One windfall and where it goes', 'windfalls.wf_id', F(
        ('Date', 'windfalls.date'), ('Source', 'windfalls.source'), ('Amount', 'windfalls.amount'), ('Assigned to', 'windfalls.assigned_to'), ('Worth in paychecks', 'windfalls.paychecks_worth')) + [
        FF('Share of an average month of take-home', 'IFERROR(%s/(SUMIFS({range:income.net},{range:income.month},">="&EDATE(%s,-6),{range:income.month},"<"&%s)/6),0)' % (LK('windfalls', 'wf_id', 'amount'), MS, MS), 'pct'),
        FF('Months of the income baseline', 'IFERROR(%s/%s,0)' % (LK('windfalls', 'wf_id', 'amount'), BASE0), 'num'),
        FF('Windfalls received this year', 'SUMIFS({range:windfalls.amount},{range:windfalls.date},">="&DATE(YEAR({today}),1,1),{range:windfalls.date},"<="&{today})', 'money')]),
    FORM('baseline_month_sheet', 'Baseline Month Sheet', 'One month of irregular income against its baseline', 'baseline.month', F(
        ('Month', 'baseline.month'), ('Income received', 'baseline.received'), ('Baseline, lowest of last months', 'baseline.baseline'), ('Average of last months', 'baseline.average'),
        ('Above or below baseline', 'baseline.status'), ('Above baseline', 'baseline.surplus'), ('Above baseline, running total', 'baseline.buffer')) + [
        FF('Buffer to hold, months of baseline', '{set:buffer_target}*%s' % LK('baseline', 'month', 'baseline'), 'money'),
        FF('Received against the average', '%s-%s' % (LK('baseline', 'month', 'received'), LK('baseline', 'month', 'average')), 'money'),
        FF('Received as a share of the average', 'IFERROR(%s/%s,0)' % (LK('baseline', 'month', 'received'), LK('baseline', 'month', 'average')), 'pct')]),
    FORM('cash_floor_sheet', 'Cash Floor Sheet', 'Joint balance against your cash floor', 'accounts.account_id', F(
        ('Account', 'accounts.account'), ('Type', 'accounts.type'), ('Balance now', 'accounts.balance_now')) + [
        FF('Cash floor', '{set:cash_floor}', 'money'), FF('Room above the floor', '%s-{set:cash_floor}' % LK('accounts', 'account_id', 'balance_now'), 'money'),
        FF('Unpaid bills due in the next 30 days', UNP('{today}+30', '<='), 'money'), FF('Balance after those bills', '%s-%s' % (LK('accounts', 'account_id', 'balance_now'), UNP('{today}+30', '<=')), 'money'),
        FF('Days of bills your floor covers', 'IFERROR({set:cash_floor}/(SUMIFS({range:bills_due.amount},{range:bills_due.month},%s)/30),0)' % MS, 'num'),
        FF('Lowest balance before the next payday', LOWNP, 'money')]),
    FORM('pay_change_sheet', 'Pay Change Sheet', 'What a pay rise or cut does to a paycheck', 'pay_schedule.pay_id', F(
        ('Person', 'pay_schedule.person'), ('Pay date', 'pay_schedule.date'), ('Pay rhythm', 'pay_schedule.frequency'), ('Expected take-home', 'pay_schedule.expected_net')) + [
        FF('Pay change to test', '{set:pay_change_pct}', 'pct'), FF('New take-home of a paycheck', 'ROUND(%s*(1+{set:pay_change_pct}),2)' % LK('pay_schedule', 'pay_id', 'expected_net'), 'money'),
        FF('Change per paycheck', 'ROUND(%s*{set:pay_change_pct},2)' % LK('pay_schedule', 'pay_id', 'expected_net'), 'money'),
        FF('Change per month', 'ROUND(%s*{set:pay_change_pct}*%s/12,2)' % (LK('pay_schedule', 'pay_id', 'expected_net'), PER(LK('pay_schedule', 'pay_id', 'frequency'))), 'money'),
        FF('Change per year', 'ROUND(%s*{set:pay_change_pct}*%s,2)' % (LK('pay_schedule', 'pay_id', 'expected_net'), PER(LK('pay_schedule', 'pay_id', 'frequency'))), 'money')]),
    FORM('month_opening_form', 'Month Opening Sheet', 'Opening a month: pay days, bills and plan', 'pay_rhythm.month', F(
        ('Month', 'pay_rhythm.month'), ('Partner 1 pay days', 'pay_rhythm.p1_days'), ('Extra pay month', 'pay_rhythm.extra'), ('Partner 1 expected pay', 'pay_rhythm.p1_expected'), ('Income you budget', 'pay_rhythm.budget_income'),
        ('Planned outgoings', 'pay_rhythm.plan_total'), ('Left to assign', 'pay_rhythm.left_to_assign'), ('Bills due in the month', 'pay_rhythm.bills_month')) + [
        FF('Bills as a share of budgeted income', 'IFERROR(%s/%s,0)' % (LK('pay_rhythm', 'month', 'bills_month'), LK('pay_rhythm', 'month', 'budget_income')), 'pct'),
        FF('Joint balance now', B0, 'money'), FF('Lowest balance before the next payday', LOWNP, 'money')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('split_plan_doc', 'Paycheck Split Plan', 'Paycheck split plan', 'pay_schedule.pay_id', [
        'Paycheck split plan of {set:household}, dated {today}. Pay date: {col:pay_schedule.date}. Person: {col:pay_schedule.person}. Expected take-home: {col:pay_schedule.expected_net}.',
        'Bills: {col:pay_schedule.split_bills}. Sinking funds: {col:pay_schedule.split_sinking}. Debt payments: {col:pay_schedule.split_debt}. Goals and savings: {col:pay_schedule.split_goals}. Spending money: {col:pay_schedule.split_spend}.',
        'Give every dollar of the paycheck a job until nothing is left to assign. The lines come from the Paycheck Split Lines sheet; change a line there and every plan follows.',
        'These are estimates from your own numbers. They are a plan you keep, not advice.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('low_point_doc', 'Cash Low Point Page', 'Cash low point before a payday', 'low_point.pn', [
        'Cash low point page of {set:household}, dated {today}. Payday: {col:low_point.payday}, in {col:low_point.days_away} days.',
        'Unpaid bills due before it: {col:low_point.bills_before}. Lowest joint balance before it: {col:low_point.lowest}, on {col:low_point.low_date}. Your cash floor: {col:low_point.floor}.',
        'Gap to the floor: {col:low_point.gap}. Verdict: {col:low_point.verdict}. Amount to move in to reach the floor: {col:low_point.move_in}.',
        'Money free until payday: {col:low_point.spend_money}, about {col:low_point.per_day} a day. The cash floor is your own number; these are estimates from your numbers.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('payday_routine_doc', 'Pay-Day Routine Page', 'Pay-day routine', 'pay_schedule.pay_id', [
        'Pay-day routine of {set:household} for the pay date {col:pay_schedule.date}. Expected take-home: {col:pay_schedule.expected_net}.',
        'Step 1: check that the paycheck reached the account and type it on the Income sheet. Step 2: write the amount that arrived on the Take-Home Check sheet. Step 3: open Paycheck Allocation and move the amounts of the split: bills {col:pay_schedule.split_bills}, sinking funds {col:pay_schedule.split_sinking}, debt {col:pay_schedule.split_debt}, goals and savings {col:pay_schedule.split_goals}.',
        'Step 4: mark the bills paid on Bills Due and update the balances on Accounts. Step 5: read Low Point Before Payday for the next pay date and keep the spending money of {col:pay_schedule.split_spend} for everyday costs.',
        'Keep this page with your records. It is a routine, not advice.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('monthly_budget_doc', 'Monthly Budget Page', 'Monthly budget by group', 'glance.month', [
        'Monthly budget page of {set:household} for the month starting {col:glance.month}. Take-home income: {col:glance.income}.',
        'Planned fixed bills: {col:glance.plan_fixed}. Planned variable needs: {col:glance.plan_variable}. Planned wants: {col:glance.plan_wants}. Planned savings: {col:glance.plan_savings}. Planned debt payments: {col:glance.plan_debt}.',
        'Planned spending: {col:glance.planned_spend}. Spent: {col:glance.spending}. Spent over plan: {col:glance.over_plan}. Saved: {col:glance.saved}. Left: {col:glance.left}.',
        'Compare the groups with a typical range, check your own numbers. This page is a record, not advice.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('zero_based_doc', 'Zero-Based Worksheet', 'Zero-based worksheet for a month', 'pay_rhythm.month', [
        'Zero-based worksheet of {set:household} for the month starting {col:pay_rhythm.month}. A zero-based budget means income minus every planned outgoing equals zero.',
        'Partner 1 pay days: {col:pay_rhythm.p1_days}. Partner 1 expected pay: {col:pay_rhythm.p1_expected}. Partner 2 income you plan on: {set:p2_budget}. Income you budget: {col:pay_rhythm.budget_income}.',
        'Planned outgoings: {col:pay_rhythm.plan_total}. Left to assign: {col:pay_rhythm.left_to_assign}. Assign what is left, or cut a line, until the amount left is zero.',
        'Bills due in the month: {col:pay_rhythm.bills_month}. Use your baseline for partner 2 income when months vary. Estimates from your numbers, not advice.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('invoice_letter_doc', 'Freelance Invoice Letter', 'Freelance invoice letter to a client', 'invoices.invoice_id', [
        'Invoice {col:invoices.invoice_id} of {set:household}, dated {today}. To: {col:invoices.contact}, {col:invoices.client}.',
        'Work invoiced: {col:invoices.amount}. Issued on {col:invoices.issued}. Please pay by {col:invoices.due_date}.',
        'Please tell us if anything on this invoice needs a correction, and send the payment date once it is planned. Thank you for the work together.',
        'Keep a copy of this invoice with your records.'], ['Freelancer', 'Client'], NOTE),
    DOC('invoice_reminder_doc', 'Invoice Reminder Letter', 'Reminder for an unpaid invoice', 'invoices.invoice_id', [
        'Reminder of {set:household}, dated {today}. To: {col:invoices.contact}, {col:invoices.client}.',
        'Invoice {col:invoices.invoice_id} for {col:invoices.amount}, issued on {col:invoices.issued}, was due on {col:invoices.due_date}. Days past the due date: {col:invoices.days_late}.',
        'Could you confirm the payment date? If the payment was sent already, thank you, and please tell us the date so we can match it.',
        'Please reply with any question about the invoice.'], ['Freelancer', 'Client'], NOTE),
    DOC('baseline_note_doc', 'Income Baseline Note', 'Income baseline note for a month', 'baseline.month', [
        'Income baseline note of {set:household} for the month starting {col:baseline.month}. Partner 2 income received: {col:baseline.received}.',
        'Baseline, the lowest of the last months: {col:baseline.baseline}. Average of the last months: {col:baseline.average}. This month: {col:baseline.status}.',
        'Income above the baseline, running total: {col:baseline.buffer}, which is {col:baseline.buffer_months} months of baseline. Budget the baseline; add the income above it to the buffer.',
        'A baseline is the lowest recent months of income, used to budget. Estimates from your numbers, not advice.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('extra_pay_doc', 'Extra Pay Month Plan', 'Plan for an extra pay month', 'extra_pay.month', [
        'Extra pay month plan of {set:household} for the month starting {col:extra_pay.month}. Pay days in the month: {col:extra_pay.pays}.',
        'Extra paycheck to assign: {col:extra_pay.extra_pay}. Suggested split: to debt {col:extra_pay.to_debt}, to goals {col:extra_pay.to_goals}, to the buffer {col:extra_pay.to_buffer}. Status: {col:extra_pay.use}.',
        'Plan the extra paycheck before it arrives and keep your usual bills on the first two paychecks. The shares are set on the Start sheet.',
        'Estimates from your numbers, not advice.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('month_end_doc', 'Month-End Summary', 'Month-end summary', 'glance.month', [
        'Month-end summary of {set:household} for the month starting {col:glance.month}. Take-home income: {col:glance.income}.',
        'Spent: {col:glance.spending}. Saved: {col:glance.saved}. Left: {col:glance.left}. Savings rate: {col:glance.savings_rate}. Joint balance at month end: {col:glance.joint_close}.',
        'Planned spending was {col:glance.planned_spend}; the difference is {col:glance.over_plan}. Write one thing to change next month.',
        'Compare with your own earlier months. A record, not advice.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('pay_record_doc', 'Pay Record Page', 'Pay record, a page you keep', 'income.income_id', [
        'Pay record of {set:household}, dated {today}. Record {col:income.income_id}: received on {col:income.date} by {col:income.person}, source {col:income.source}.',
        'Gross: {col:income.gross}. Tax: {col:income.tax}. Retirement: {col:income.retirement}. Other deductions: {col:income.other_deductions}. Take-home: {col:income.net}. Set aside: {col:income.set_aside}.',
        'This is a record you keep for your own use. It is not a pay statement and not a tax document. Ask your adviser what to keep.',
        'Paid into account: {col:income.account_id}.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('forecast_doc', '60-Day Cash Forecast Page', '60-day cash forecast page', 'forecast.day_no', [
        'Cash forecast page of {set:household}, dated {today}. The forecast starts today and uses paydays and unpaid bills of the joint account.',
        'Lowest balance in the next 60 days: {col:forecast.low_60}, on {col:forecast.low_60_date}. Balance on day 59: {col:forecast.end_60}. Your cash floor: {set:cash_floor}.',
        'Days under the floor in the next 30 days: {col:forecast.under_30}. Move money in before the first day under the floor, or ask what is possible for a bill date.',
        'An estimate from your numbers, not advice.'], ['Partner 1', 'Partner 2'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('every_paycheck', 'Every Paycheck Steps', 'pay_schedule', 'pay_schedule.date', [('Check that the paycheck reached the account', 0), ('Type it on the Income sheet', 0), ('Check it on the Take-Home Check sheet', 0), ('Move the split amounts', 0), ('Mark paid bills on Bills Due', 1), ('Read the low point before the next payday', 1)]),
    CHK('weekly_check', 'Weekly Money Check Steps', 'pay_schedule', 'pay_schedule.date', [('Update the account balances', 0), ('Mark paid bills', 0), ('Read the cash forecast for the week', 1), ('Check open freelance invoices', 1), ('Check spending money until payday', 2), ('Talk about one change for next week', 3)]),
    CHK('month_opening', 'Month Opening Steps', 'pay_rhythm', 'pay_rhythm.month', [('Check the pay days of the month', 0), ('Open the Zero-Based Month sheet', 0), ('Assign every dollar until zero is left', 1), ('Check bills due in the month', 1), ('Set the cash floor and the baseline', 2), ('Send the budget to your partner', 2)]),
    CHK('month_close', 'Month Close Steps', 'glance', 'glance.month', [('Type the joint balance at month end', 28), ('Type what you spent and saved', 29), ('Check planned against actual', 30), ('Check the take-home of every paycheck', 30), ('Update income above the baseline', 31), ('Write one change for next month', 32)]),
    CHK('invoice_sent', 'Freelance Invoice Sent Steps', 'invoices', 'invoices.issued', [('Type the invoice on Freelance Invoices', 0), ('Send the invoice to the client', 0), ('Note the due date', 1), ('Set a reminder before the due date', 7), ('Send a friendly reminder', 14), ('Ask for the payment date', 30)]),
    CHK('payment_received', 'Payment Received Steps', 'invoices', 'invoices.due_date', [('Check the payment in the account', 0), ('Type it on the Income sheet', 0), ('Mark the invoice paid', 0), ('Move the tax set-aside', 1), ('Send a thank-you to the client', 1)]),
    CHK('extra_pay_chk', 'Extra Pay Month Steps', 'extra_pay', 'extra_pay.month', [('Check the pay dates with the payroll office', -14), ('Plan the extra paycheck', -7), ('Keep bills on the first two paychecks', 0), ('Move the debt share', 14), ('Move the goals and buffer shares', 14), ('Record it on Windfalls', 15)]),
    CHK('irregular_month', 'Irregular Income Month Steps', 'baseline', 'baseline.month', [('Type the client payments received', 28), ('Compare with the baseline', 29), ('Add income above the baseline to the buffer', 30), ('If below baseline, use the buffer', 30), ('Set aside the tax share', 30), ('Update the baseline for next month', 31)]),
    CHK('pay_change', 'Pay Change or New Job Steps', 'pay_schedule', 'pay_schedule.date', [('Type the new pay on Pay Schedule', -7), ('Change the pay rhythm in Settings', -7), ('Test the change on the Pay Change Sheet', -5), ('Rebuild the paycheck split', 0), ('Check the take-home of the first paycheck', 0), ('Update the budget plan', 7)]),
    CHK('low_point_warning', 'Cash Low Point Warning Steps', 'bills_due', 'bills_due.due_date', [('Read the bill that breaks the floor', -5), ('Tell your partner about the low point', -5), ('Ask what is possible for the bill date', -4), ('Move money in if needed', -1), ('Check the balance on the bill day', 0), ('Note what happened', 1)]),
    CHK('quarterly_review', 'Quarterly Plan Review Steps', 'budget', 'budget.month', [('Compare planned and actual by month', 0), ('Review the biggest category changes', 3), ('Update the baseline and the buffer', 5), ('Check the cash floor', 7), ('Adjust the budget plan lines', 10), ('Agree the next quarter', 14)]),
    CHK('single_adult', 'Single Adult First Month Steps', 'pay_rhythm', 'pay_rhythm.month', [('Replace the demo data with your own', 0), ('Set your pay rhythm and next pay date', 0), ('Leave partner 2 rows empty', 0), ('Add your bills and accounts', 3), ('Assign every dollar on Zero-Based Month', 5), ('Read the cash low point before payday', 7)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('floor_p2', 'Partner 2: joint account may drop', 'low_point', 'low_point.p2_phone', 'Hi {p2_name}, the joint account may drop under {floor} on {low_date}. Can we move {move_in} in before then? {household}'),
    M('paycheck_p2', 'Partner 2: next paycheck and split', 'pay_schedule', 'pay_schedule.p2_phone', 'Hi {p2_name}, the next paycheck of {expected_net} arrives on {date}. The split is ready: bills {split_bills}, spending money {split_spend}. {household}'),
    M('clients_p2', 'Partner 2: send client payments', 'baseline', 'baseline.p2_phone', 'Hi {p2_name}, please send the client payments you received in {month}, so that our income baseline stays right. {household}'),
    M('above_p2', 'Partner 2: month above baseline', 'baseline', 'baseline.p2_phone', 'Hi {p2_name}, the income of {month} is above the baseline by {above_by}. Shall we add it to the buffer? {household}'),
    M('below_p2', 'Partner 2: month below baseline', 'baseline', 'baseline.p2_phone', 'Hi {p2_name}, the income of {month} is below the baseline by {below_by}. We use the buffer for the gap. {household}'),
    M('payday_p1', 'Partner 1: your payday and split', 'pay_schedule', 'pay_schedule.p1_phone', 'Hi {p1_name}, your payday is {date}. The split is ready: bills {split_bills}, debt {split_debt}, spending money {split_spend}. {household}'),
    M('extra_p1', 'Partner 1: extra pay month', 'extra_pay', 'extra_pay.p1_phone', 'Hi {p1_name}, the extra pay month starting {month} brings {extra_pay} to assign: {to_debt} to debt, {to_goals} to goals, {to_buffer} to the buffer. {household}'),
    M('takehome_p1', 'Partner 1: check the take-home', 'take_home', 'take_home.p1_phone', 'Hi {p1_name}, please check the take-home of the pay on {date}: the amount that arrived differs by {difference}. {household}'),
    M('grandparent', 'Grandparent: thank you for the help', 'team', 'team.phone', 'Hello {name}, thank you for the help. The childcare plan for next week is on the fridge calendar. {household}'),
    M('a_sent', 'Client A: invoice sent', 'invoices', 'invoices.phone', 'Hello {contact}, invoice {invoice_id} for {amount} was sent on {issued}, due {due_date}. Thank you, {household}'),
    M('a_remind', 'Client A: friendly reminder', 'invoices', 'invoices.phone', 'Hello {contact}, a friendly reminder: invoice {invoice_id} for {amount} is due on {due_date}. Thank you, {household}'),
    M('a_late', 'Client A: invoice past due', 'invoices', 'invoices.phone', 'Hello {contact}, invoice {invoice_id} is {days_late} days past its due date. Can you confirm the payment date? Thank you, {household}'),
    M('a_thanks', 'Client A: thank you for the payment', 'invoices', 'invoices.phone', 'Hello {contact}, thank you for the payment of {amount} for invoice {invoice_id}. {household}'),
    M('b_sent', 'Client B: invoice sent', 'invoices', 'invoices.phone', 'Hello {contact}, invoice {invoice_id} for {amount} was sent on {issued}. Please pay by {due_date}. Thank you, {household}'),
    M('b_late', 'Client B: invoice past due', 'invoices', 'invoices.phone', 'Hello {contact}, invoice {invoice_id} is {days_late} days past due. Please confirm the payment date. Thank you, {household}'),
    M('b_thanks', 'Client B: thank you for the payment', 'invoices', 'invoices.phone', 'Hello {contact}, thank you for the payment of {amount} received on {paid_on}. {household}'),
    M('c_invoice', 'Client C: invoice for finished work', 'invoices', 'invoices.phone', 'Hello {contact}, here is invoice {invoice_id} for {amount}, issued on {issued} for the work finished, due {due_date}. Thank you, {household}'),
    M('payroll_dates', 'Payroll office: confirm pay dates', 'pay_schedule', 'pay_schedule.payroll_phone', 'Hello {payroll_name}, please confirm my pay dates for the next {pays_ahead} pay periods, starting {date}. Thank you, {household}'),
    M('payroll_check', 'Payroll office: check a pay statement', 'take_home', 'take_home.payroll_phone', 'Hello {payroll_name}, my pay statement of {date} shows a take-home of {net}. Please check the deductions of {deductions}. Thank you, {household}'),
    M('payroll_extra', 'Payroll office: extra pay date', 'extra_pay', 'extra_pay.payroll_phone', 'Hello {payroll_name}, please confirm the extra pay date in the month starting {month}. Thank you, {household}'),
    M('bank_balance', 'Bank branch: confirm a balance', 'accounts', 'accounts.bank_phone', 'Hello {bank_name}, please confirm the balance of {account} on {as_of}. Thank you, {household}'),
    M('bank_date', 'Bank branch: move a payment date', 'bills_due', 'bills_due.bank_phone', 'Hello {bank_name}, we want to move the payment date of {bill} ({amount}, due {due_date}) to {new_date}, after payday. What is possible? {household}'),
    M('landlord_day', 'Landlord: rent one day after payday', 'bills_due', 'bills_due.landlord_phone', 'Hello {landlord_name}, we plan to pay the rent due on {due_date} one day after payday, on {new_date}. Is that fine? Thank you, {household}'),
    M('landlord_amount', 'Landlord: confirm the rent amount', 'bills_due', 'bills_due.landlord_phone', 'Hello {landlord_name}, please confirm the rent amount of {amount} for the month starting {month}. Thank you, {household}'),
    M('utility_day', 'Utility company: move the due date', 'bills_due', 'bills_due.utility_phone', 'Hello {utility_name}, please move the due date of {bill} to day {new_day} of the month. What is possible? Thank you, {household}'),
    M('childcare_pay', 'Childcare provider: payment date', 'bills_due', 'bills_due.childcare_phone', 'Hello {childcare_name}, the payment of {amount} will arrive on {pay_date}. Thank you for waiting. {household}'),
    M('childcare_invoice', 'Childcare provider: send the invoice', 'bills_due', 'bills_due.childcare_phone', 'Hello {childcare_name}, please send the invoice for the month starting {month} by {ask_by}. Thank you, {household}'),
    M('tax_income', 'Tax preparer: freelance income', 'baseline', 'baseline.tax_phone', 'Hello {tax_name}, my freelance income for the month starting {month} was {received}. Please tell us how to set it aside. Thank you, {household}'),
    M('days_under', 'Household member: days under the floor', 'forecast', 'forecast.p2_phone', 'Hi {p2_name}, the cash forecast shows {under_30} days under the floor in the next 30 days. Let us look at the bills before payday. {household}'),
    M('spend_money', 'Household member: spending money', 'low_point', 'low_point.p2_phone', 'Hi {p2_name}, the spending money until payday on {payday} is {spend_money}, about {per_day} a day. {household}'),
    M('budget_ready', 'Household member: budget is ready', 'zero_month', 'zero_month.p2_phone', 'Hi {p2_name}, the budget for the month starting {month} is ready. Left to assign: {left_final}. {household}'),
    M('buffer_p2', 'Partner 2: income buffer', 'baseline', 'baseline.p2_phone', 'Hi {p2_name}, income above the baseline now holds {buffer_months} months of the baseline. {household}'),
    M('glance_p1', 'Partner 1: month at a glance', 'glance', 'glance.p1_phone', 'Hi {p1_name}, the month at a glance for the month starting {month} shows {left} left after spending and saving. {household}'),
    M('receipts', 'Household member: send the receipts', 'glance', 'glance.p2_phone', 'Hi {p2_name}, please send the receipts for the month starting {month} before the month close. {household}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def INC(extra=''): return 'SUMIFS({range:income.net},%s)' % extra
def LAST(n): return '{range:income.date},">="&({today}-%d)' % n
YS = 'DATE(YEAR({today}),1,1)'
FREE = '{range:income.person},%s,{range:income.source},"<>"&%s,{range:income.source},"<>"&%s' % (P2, SIDE, WIND)
MON = lambda j: 'SUMIFS({range:income.net},{range:income.month},EDATE(%s,-%d))' % (MS, j)
kpis = [
    KPI('Take-home pay this month', INC('{range:income.month},%s' % MS), 'money'),
    KPI('Take-home pay last 30 days', INC(LAST(30)), 'money'),
    KPI('Paychecks received this year', 'COUNTIFS({range:income.source},%s,{range:income.date},">="&%s)' % (PAYCK, YS), 'int'),
    KPI('Freelance income this month', INC('{range:income.month},%s,%s' % (MS, FREE)), 'money'),
    KPI('Freelance income last 30 days', INC('%s,%s' % (LAST(30), FREE)), 'money'),
    KPI('Side income this year', INC('{range:income.source},%s,{range:income.date},">="&%s' % (SIDE, YS)), 'money'),
    KPI('Windfalls this year', 'SUMIFS({range:windfalls.amount},{range:windfalls.date},">="&%s,{range:windfalls.date},"<="&{today})' % YS, 'money'),
    KPI('Average monthly take-home, last 6 months', 'SUMIFS({range:income.net},{range:income.month},">="&EDATE(%s,-6),{range:income.month},"<"&%s)/6' % (MS, MS), 'money'),
    KPI('Lowest monthly take-home, last 6 months', 'MIN(%s)' % ','.join(MON(j) for j in range(1, 7)), 'money'),
    KPI('Income baseline, lowest recent months', BASE0, 'money'),
    KPI('Months above baseline in the last 12', 'COUNTIFS({range:baseline.status},%s,{range:baseline.offset},"<0")' % c1('Above baseline'), 'int'),
    KPI('Above-baseline income, running total', 'SUMIFS({range:baseline.buffer},{range:baseline.offset},-1)', 'money'),
    KPI('Expected income next 30 days', 'SUMIFS({range:pay_schedule.expected_net},{range:pay_schedule.date},">="&{today},{range:pay_schedule.date},"<="&({today}+30))', 'money'),
    KPI('Pay days in the next 60 days', 'COUNTIFS({range:pay_schedule.into_joint},%s,{range:pay_schedule.date},">="&{today},{range:pay_schedule.date},"<="&({today}+60))' % YES, 'int'),
    KPI('Extra pay months in the next 12', 'COUNTIFS({range:extra_pay.extra_pay},">0",{range:extra_pay.offset},"<12")', 'int'),
    KPI('Joint balance now', B0, 'money'),
    KPI('Lowest joint balance before next payday', LOWNP, 'money', alert={"when": "< {set:cash_floor}", "style": "bad"}),
    KPI('Days under the cash floor in the next 30', 'COUNTIFS({range:forecast.flag},%s,{range:forecast.day_no},"<30")' % UNDER, 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Bills due before the next payday', UNP(NP), 'money'),
    KPI('Unpaid bills due within 30 days', 'SUMIFS({range:bills_due.amount},{range:bills_due.status},"<>"&%s,{range:bills_due.due_date},"<="&({today}+30))' % PAID_B, 'money'),
    KPI('Late bills now', 'COUNTIFS({range:bills_due.status},"<>"&%s,{range:bills_due.due_date},"<"&{today},{range:bills_due.due_date},">0")' % PAID_B, 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Spending money per day until payday', 'SUMIFS({range:low_point.per_day},{range:low_point.pn},1)', 'money'),
    KPI('Planned spending this month', 'SUMIFS({range:budget.planned},{range:budget.month},%s,{range:budget.group},"<>"&%s)' % (MS, G_SAVE), 'money'),
    KPI('Planned savings this month', 'SUMIFS({range:budget.planned},{range:budget.month},%s,{range:budget.group},%s)' % (MS, G_SAVE), 'money'),
    KPI('Planned debt payments this month', 'SUMIFS({range:budget.planned},{range:budget.month},%s,{range:budget.group},%s)' % (MS, G_DEBT), 'money'),
    KPI('Left to assign this month', 'SUMIFS({range:pay_rhythm.left_to_assign},{range:pay_rhythm.offset},0)', 'money'),
    KPI('Needs share of take-home', 'SUMIFS({range:need_want.share},{range:need_want.group},%s)+SUMIFS({range:need_want.share},{range:need_want.group},%s)' % (G_FIX, G_VAR), 'pct'),
    KPI('Wants share of take-home', 'SUMIFS({range:need_want.share},{range:need_want.group},%s)' % G_WANT, 'pct'),
    KPI('Savings and debt share of take-home', 'SUMIFS({range:need_want.share},{range:need_want.group},%s)+SUMIFS({range:need_want.share},{range:need_want.group},%s)' % (G_SAVE, G_DEBT), 'pct'),
    KPI('Open freelance invoices total', 'SUMIFS({range:invoices.amount},{range:invoices.status},"<>"&%s)' % PAID_I, 'money'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Money Plan Dashboard", "kpis": kpis,
    "monthly": {"title": "Take-home, spent and saved", "date": "income.month", "series": [
        {"label": "Take-home", "sum": "income.net", "date": "income.month"}, {"label": "Spent", "sum": "glance.spending", "date": "glance.month"}, {"label": "Saved", "sum": "glance.saved", "date": "glance.month"}]},
    "breakdowns": [{"title": "Take-home by source", "by": "income.source", "value": "income.net", "agg": "sum"}, {"title": "Bills due by category", "by": "bills_due.category", "value": "bills_due.amount", "agg": "sum"},
                   {"title": "Freelance invoices by status", "by": "invoices.status", "value": "invoices.amount", "agg": "sum"}, {"title": "Budget plan by group", "by": "budget.group", "value": "budget.planned", "agg": "sum"}]}
def W(c, op, v): return (c, op, v)
insights = {"filters": [{"label": "Person", "list": "person"}, {"label": "Income source", "list": "isource"}, {"label": "Budget group", "list": "group"}],
    "gauges": [
        {"title": "Bills before payday, share of balance", "num": AGG('sum', 'bills_due', 'bills_due.amount', where=[W('status', '<>', PAID_B), W('account_id', '=', '{set:joint_id}'), W('due_date', '<', '{set:next_payday}')]),
         "den": AGG('sum', 'accounts', 'accounts.balance_now', where=[W('account_id', '=', '{set:joint_id}')])},
        {"title": "Take-home this month against plan", "num": AGG('sum', 'income', 'income.net', where=[W('this_month', '=', 1)]), "den": AGG('sum', 'pay_rhythm', 'pay_rhythm.budget_income', where=[W('offset', '=', 0)])},
        {"title": "Months at or above the baseline", "num": AGG('count', 'baseline', where=[W('status', '=', c1('Above baseline')), W('offset', '<', 0)]), "den": AGG('count', 'baseline', where=[W('offset', '<', 0)])},
        {"title": "Needs share of this month's plan", "num": AGG('sum', 'budget', 'budget.p_needs', where=[W('this_month', '=', 1)]), "den": AGG('sum', 'budget', 'budget.planned', where=[W('this_month', '=', 1)])},
        {"title": "Freelance invoices paid on time", "num": AGG('count', 'invoices', where=[W('late_flag', '=', 0)]), "den": AGG('count', 'invoices', where=[W('status', '=', PAID_I)])},
        {"title": "Days at or above the floor, next 30", "num": AGG('count', 'forecast', where=[W('flag', '=', ABOVE), W('day_no', '<', 30)]), "den": AGG('count', 'forecast', where=[W('day_no', '<', 30)])}],
    "charts": [
        CHART('Take-home pay per month', 'column', 'month', [AGG('sum', 'income', 'income.net', date='income.month', label='Take-home')]),
        CHART('Take-home by person per month', 'column', 'month', [AGG('sum', 'income', 'income.net', date='income.month', where=[W('person', '=', P1)], label='Partner 1'), AGG('sum', 'income', 'income.net', date='income.month', where=[W('person', '=', P2)], label='Partner 2')]),
        CHART('Freelance income per month', 'column', 'month', [AGG('sum', 'income', 'income.net', date='income.month', where=[W('person', '=', P2), W('source', '<>', SIDE), W('source', '<>', WIND)], label='Freelance clients')]),
        CHART('Income by source', 'bar', 'income.source', [AGG('sum', 'income', 'income.net', label='Take-home')]),
        CHART('Income by source per month', 'stacked', 'month', [AGG('sum', 'income', 'income.net', date='income.month', where=[W('source', '=', tok('isource', s))], label=s) for s in ('Paycheck', 'Client A', 'Client B', 'Client C')]),
        CHART('Gross, deductions and net per month', 'column', 'month', [AGG('sum', 'income', 'income.gross', date='income.month', label='Gross'), AGG('sum', 'income', 'income.deductions', date='income.month', label='Deductions'), AGG('sum', 'income', 'income.net', date='income.month', label='Take-home')]),
        CHART('Windfalls per month', 'column', 'month', [AGG('sum', 'windfalls', 'windfalls.amount', date='windfalls.date', label='Windfalls')]),
        CHART('Income against baseline per month', 'line', 'month', [AGG('sum', 'baseline', 'baseline.received', date='baseline.month', label='Received'), AGG('sum', 'baseline', 'baseline.baseline', date='baseline.month', label='Baseline')]),
        CHART('Above-baseline income, running total', 'line', 'month', [AGG('sum', 'baseline', 'baseline.buffer', date='baseline.month', label='Running total')]),
        CHART('Expected pay per month, next 12', 'column', 'pay_rhythm.ahead', [AGG('sum', 'pay_rhythm', 'pay_rhythm.total_expected', label='Expected pay')]),
        CHART('Pay days per month, next 12', 'column', 'pay_rhythm.ahead', [AGG('sum', 'pay_rhythm', 'pay_rhythm.p1_days', label='Partner 1 pay days')]),
        CHART('Joint balance at month end', 'line', 'month', [AGG('sum', 'glance', 'glance.joint_close', date='glance.month', label='Joint balance')]),
        CHART('Joint balance forecast by week, next 90 days', 'line', 'forecast.week', [AGG('avg', 'forecast', 'forecast.closing', label='Average closing balance')]),
        CHART('Bills due per month', 'column', 'month', [AGG('sum', 'bills_due', 'bills_due.amount', date='bills_due.month', label='Bills due')]),
        CHART('Bills due by category', 'bar', 'bills_due.category', [AGG('sum', 'bills_due', 'bills_due.amount', label='Bills due')]),
        CHART('Bills paid late per month', 'column', 'month', [AGG('count', 'bills_due', date='bills_due.month', where=[W('late_flag', '>', 0)], label='Late bills')]),
        CHART('Planned by group per month', 'stacked', 'month', [AGG('sum', 'budget', 'budget.p_needs', date='budget.month', label='Needs'), AGG('sum', 'budget', 'budget.p_wants', date='budget.month', label='Wants'),
                                                                 AGG('sum', 'budget', 'budget.p_save', date='budget.month', label='Savings'), AGG('sum', 'budget', 'budget.p_debt', date='budget.month', label='Debt')]),
        CHART('Planned by group, average per line', 'bar', 'budget.group', [AGG('avg', 'budget', 'budget.planned', label='Planned')]),
        CHART('Planned against actual spending per month', 'column', 'month', [AGG('sum', 'glance', 'glance.planned_spend', date='glance.month', label='Planned'), AGG('sum', 'glance', 'glance.spending', date='glance.month', label='Spent')]),
        CHART('Savings planned per month', 'line', 'month', [AGG('sum', 'budget', 'budget.p_save', date='budget.month', label='Savings planned')]),
        CHART('Freelance invoices by status', 'bar', 'invoices.status', [AGG('count', 'invoices', label='Invoices')]),
        CHART('Freelance invoice amount per month', 'column', 'month', [AGG('sum', 'invoices', 'invoices.amount', date='invoices.issued', label='Invoiced')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Cash low point forecast", "why": "the joint balance day by day from today, paydays and unpaid bills, with the lowest balance, its date and the days under your floor", "where": "Cash Low Point Forecast"},
    {"name": "Low point before each payday", "why": "the lowest balance before each of the next paydays, so a short stretch is seen weeks before it happens", "where": "Low Point Before Each Payday"},
    {"name": "Bill that breaks the floor", "why": "the one unpaid bill that pushes the joint account under your floor and the amount to move in by the day before", "where": "Bill That Breaks the Floor"},
    {"name": "Paycheck split to zero", "why": "every dollar of a paycheck gets a job, zero-based or by percent, ending at zero left to assign", "where": "Paycheck Split"},
    {"name": "Irregular income baseline", "why": "the lowest and average months of freelance and side income give the amount to budget, with the buffer above it", "where": "Irregular Income Baseline"},
    {"name": "Pay rhythm calendar", "why": "pay days in every month for weekly, every two weeks, twice a month or monthly pay", "where": "Pay Rhythm Calendar"},
    {"name": "Extra pay month planner", "why": "the month with a third paycheck is found early and split between debt, goals and the buffer", "where": "Extra Pay Month Planner"},
    {"name": "Late paycheck test", "why": "move the next pay date by a few days and see the new low point against your floor", "where": "Late Paycheck Test"},
    {"name": "Freelance cash timing", "why": "open invoices with the date each client usually pays, and whether to chase or wait before the low point", "where": "Freelance Cash Timing"},
    {"name": "Zero-based month check", "why": "income minus every planned outgoing, with what to cut from wants to reach zero", "where": "Zero-Based Month Check"}]
competitors = [
    {"what": "budgeting app with a monthly subscription and bank links", "lacks": "charges every year, breaks when a link breaks and shows no cash low point before payday or irregular-income baseline"},
    {"what": "single-purpose budget template", "lacks": "lists planned and actual amounts but has no paycheck split, no pay rhythm calendar and no forecast"},
    {"what": "free paycheck calculator sheet", "lacks": "works out one take-home and stops: no bills before payday, no extra pay month and no zero-based plan"},
    {"what": "cash flow template for a business", "lacks": "is built for invoices and customers, not for a household with paychecks, bills, a floor and a partner"},
    {"what": "spreadsheet that only tracks spending", "lacks": "looks back at what was spent and never tells you which bill will break the floor next week"}]
guide = [
    'Start here: this workbook plans each payday and the days before the next one. Open Start, type your household name, your next pay date, your pay rhythm and your cash floor in the yellow cells.',
    'Replace the demo data: clear the sample rows of Team, Accounts, Income, Freelance Invoices, Pay Schedule, Bills Due and Budget Plan and type your own. The grey cells calculate by themselves.',
    'Type the day numbers 0 to 89 once on Cash Forecast by Day and 1 to 12 on Low Point Before Payday; every other column fills in. Do the same for the months on Pay Rhythm and Income Baseline.',
    'Pay-day routine: type the paycheck on Income, write the amount that arrived on Take-Home Check, move the amounts of the Paycheck Allocation, mark bills paid on Bills Due and update Accounts.',
    'Before every payday read Low Point Before Payday and the Cash Low Point Forecast: they show the lowest balance, its date and the bill that breaks your floor.',
    'Month-close routine: type the joint balance, what you spent and what you saved on Month at a Glance, check planned against actual, update the baseline and write one change for next month.',
    'Freelance and side income: type each payment on Income and each invoice on Freelance Invoices; the Income Baseline shows the lowest recent months to budget and the income above it.',
    'Use the Zero-Based Month and Needs Wants Savings sheets to assign every dollar; the shares are a typical range, check your own numbers.',
    'A single adult with one income can use most sheets: leave the partner 2 rows, the freelance invoices and the baseline sheets empty and keep the pay rhythm of your own paycheck.',
    'Pick the tool of the question you have: low point, bill that breaks the floor, paycheck split, spending money until payday, late paycheck, extra pay month or the next three months.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Why a workbook: one flat price, no yearly renewal, your data stays with you, nothing to link or re-connect. Type or paste your numbers; no macros, works in Excel and Google Sheets.',
    'What this is not: not a bank app, not tax, legal, investment or credit advice. Forecasts and verdicts are estimates from your numbers.']
listing = {"title": "Household Budget Planner Excel Template: Paycheck Split, Cash Low Point Forecast, Zero-Based Budget, Irregular Income",
    "headline": "Know what every paycheck does and what the days before the next one will bring",
    "tags": ["budget planner", "paycheck budget", "zero based budget", "cash flow forecast", "household budget", "excel template", "irregular income", "biweekly paycheck", "freelance income", "family budget", "bills calendar", "money plan", "no subscription"],
    "description": ("Run the money of your household one payday at a time in one Excel workbook. Built for a single adult, a couple or a family: partner 1 on a salary paid every two weeks, partner 2 freelance with irregular income, or one income on its own. "
        "The Paycheck Allocation splits one paycheck line by line down to zero left to assign. The Pay Rhythm by Month sheet counts the pay days of any rhythm, weekly, every two weeks, twice a month or monthly, and finds the extra pay month with a third paycheck. "
        "Income Baseline shows the lowest and average months of freelance and side income, so you budget the baseline and keep what lands above it.\n\n"
        "The Cash Forecast by Day follows the joint account for 90 days from the balance, paydays and every unpaid bill. Low Point Before Payday shows the lowest balance and its date before each coming payday against your own cash floor, with a verdict of safe, tight or short. "
        "Bills Due lists every bill with its status and names the bill that pushes the account under the floor and the biggest bills to pay first. Budget Plan holds the plan lines by category, Zero-Based Month assigns every dollar, and Needs Wants Savings compares the shares with a typical range, check your own numbers.\n\n"
        f"{len(tools)} tools answer the questions of every week: will the joint account go under my floor, which bill breaks it, how much can I spend a day until payday, what if the paycheck is late, do I chase an invoice, what do we do with the extra paycheck. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to a partner, clients, the landlord, the payroll office and the bank branch.\n\n"
        "This is part one of the eight-part Household Finance suite. A standard .xlsx workbook with no macros, no bank links and no yearly renewal, with a demo copy full of sample data to explore first. "
        "It helps you keep track of your own numbers and does not give tax, legal, investment or credit advice or promise any result."),
    "features": ["Paycheck split down to zero left to assign", "Cash forecast day by day for 90 days", "Low point before each payday with a verdict", "Bill that breaks your cash floor named", "Pay rhythm calendar and extra pay month",
                 "Irregular income baseline and buffer", "Zero-based month and needs wants savings", f"{len(tools)} tools for the questions of every week", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "No macros, no bank links, no yearly renewal"]}
s = spec(id=f'{SUITE}-p1', slug='household-finance-plan', profession='Household Finance', name='Money Plan and Paychecks',
         tagline='Know what every paycheck does and what the days before the next one will bring', price_usd=29,
         colors={"primary": "#1F5F5B", "accent": "#F2B134"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 1, "of": 8, "focus": "Money plan and paychecks"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hf1.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
