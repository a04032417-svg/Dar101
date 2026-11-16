"""Household Finance suite - part 7: Partners, Kids and Shared Costs."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf7_lists import *
from hf7_tables import *
from hf7_tables import SCV, NEED
from hf7_tools import tools
import hf7_data as D

SUITE = 'fx-20261116-household-finance'
NOTE = "Sample wording: adapt it to your own household."
def F(*pairs): return [FV(a, b) for a, b in pairs]
IDCOL = {'shared': 'shared_id', 'split_cmp': 'sc_id', 'settle': 'settle_id', 'fair_split': 'month', 'allowance_summary': 'as_id', 'kids_costs': 'kid_cost_id', 'allowances': 'allowance_id',
         'scenarios': 'scenario_id', 'lose': 'category', 'expense_shock': 'month', 'rate_change': 'rc_id', 'new_baby': 'month', 'kids_year': 'ky_id', 'cost_member': 'cm_id', 'overpaid': 'month'}
def LK(t, c, v='{pick}'): return 'INDEX({range:%s.%s},MATCH(%s,{range:%s.%s},0))' % (t, c, v, t, IDCOL[t])
SHR = lambda c: R('shared', c)
KCR = lambda c: R('kids_costs', c)
ALR = lambda c: R('allowances', c)

# ------------------------------------------------------------------ forms (12)
_SMONTH = LK('shared', 'month')
forms = [
    FORM('shared_cost_sheet', 'Shared Cost Sheet', 'One shared cost and its place in the month', 'shared.shared_id', F(
        ('Date', 'shared.date'), ('Description', 'shared.description'), ('Category', 'shared.category'), ('Amount', 'shared.amount'), ('Paid by', 'shared.paid_by'),
        ('Agreed share of partner 1', 'shared.agreed_p1'), ('Split rule', 'shared.split_rule'), ('Partner 1 share', 'shared.p1_share'), ('Partner 2 share', 'shared.p2_share')) + [
        FF('Shared costs that month', 'SUMIFS(%s,%s,%s)' % (SHR('amount'), SHR('month'), _SMONTH), 'money'),
        FF('Share of the month', 'IFERROR(%s/SUMIFS(%s,%s,%s),0)' % (LK('shared', 'amount'), SHR('amount'), SHR('month'), _SMONTH), 'pct'),
        FF('Same category that month', 'SUMIFS(%s,%s,%s,%s,%s)' % (SHR('amount'), SHR('category'), LK('shared', 'category'), SHR('month'), _SMONTH), 'money'),
        FF('Payments by the same partner that month', 'COUNTIFS(%s,%s,%s,%s)' % (SHR('paid_by'), LK('shared', 'paid_by'), SHR('month'), _SMONTH), 'int')]),
    FORM('split_agreement_sheet', 'Split Agreement Sheet', 'A split rule against the agreed split', 'split_cmp.sc_id', F(
        ('Split rule', 'split_cmp.rule'), ('Months back', 'split_cmp.months'), ('Shared costs', 'split_cmp.shared_total'), ('Partner 1 share', 'split_cmp.p1_ratio'), ('Partner 1 pays', 'split_cmp.p1_pays'),
        ('Partner 2 pays', 'split_cmp.p2_pays'), ('Partner 2 pays on the agreed split', 'split_cmp.p2_now'), ('Partner 2 difference', 'split_cmp.difference')) + [
        FF('Agreed share of partner 1', '{set:agreed_p1_share}', 'pct'), FF('Partner 2 share under this rule', 'IFERROR(%s/%s,0)' % (LK('split_cmp', 'p2_pays'), LK('split_cmp', 'shared_total')), 'pct'),
        FF('Partner 2 difference a month', 'IFERROR(%s/%s,0)' % (LK('split_cmp', 'difference'), LK('split_cmp', 'months')), 'money')]),
    FORM('settle_sheet', 'Settle Up Sheet', 'One month to settle between the partners', 'settle.settle_id', F(
        ('Month', 'settle.month'), ('Shared total', 'settle.total'), ('Partner 1 paid', 'settle.p1_paid'), ('Partner 2 paid', 'settle.p2_paid'), ('Partner 1 share', 'settle.p1_share'),
        ('Partner 2 share', 'settle.p2_share'), ('From partner', 'settle.from_partner'), ('To partner', 'settle.to_partner'), ('Amount to settle', 'settle.amount'), ('Settle by', 'settle.due_date'),
        ('Status', 'settle.status'), ('Running balance owed to partner 2', 'settle.running_balance')) + [
        FF('Days past the settle by date', '{today}-%s' % LK('settle', 'due_date'), 'int'), FF('Amount as a share of the month', 'IFERROR(%s/%s,0)' % (LK('settle', 'amount'), LK('settle', 'total')), 'pct')]),
    FORM('transfer_sheet', 'Transfer to Joint Sheet', 'What each partner moves to the joint account', 'fair_split.month', F(
        ('Shared total', 'fair_split.shared_total'), ('Partner 1 take-home share', 'fair_split.p1_takehome_share'), ('Partner 1 transfer, income share', 'fair_split.p1_transfer'),
        ('Partner 2 transfer, income share', 'fair_split.p2_transfer')) + [
        FF('Joint account need a month', '{set:joint_monthly}', 'money'), FF('Equal split transfer', '{set:joint_monthly}/2', 'money'),
        FF('Partner 1 against an equal split', '%s-{set:joint_monthly}/2' % LK('fair_split', 'p1_transfer'), 'money'),
        FF('Partner 1 transfer, agreed split', '{set:joint_monthly}*{set:agreed_p1_share}', 'money')]),
    FORM('allowance_sheet', 'Allowance Sheet', 'One child and month of allowance', 'allowance_summary.as_id', F(
        ('Month', 'allowance_summary.month'), ('Child', 'allowance_summary.child'), ('Paid', 'allowance_summary.paid'), ('Saved', 'allowance_summary.saved'), ('Spent', 'allowance_summary.spent'),
        ('Saved share', 'allowance_summary.saved_share'), ('Saving check', 'allowance_summary.flag')) + [
        FF('Share you want saved', '{set:save_target}', 'pct'), FF('Saved needed for the target', '{set:save_target}*%s' % LK('allowance_summary', 'paid'), 'money'),
        FF('Short of the target', 'MAX(0,{set:save_target}*%s-%s)' % (LK('allowance_summary', 'paid'), LK('allowance_summary', 'saved')), 'money')]),
    FORM('kids_cost_sheet', 'Kids Cost Sheet', 'One kids cost and what it means for the year', 'kids_costs.kid_cost_id', F(
        ('Date', 'kids_costs.date'), ('Child', 'kids_costs.child'), ('Kind', 'kids_costs.kind'), ('Amount', 'kids_costs.amount'), ('Payment ID', 'kids_costs.tx_id')) + [
        FF('Same kind for the child this year', 'SUMIFS(%s,%s,%s,%s,%s,%s,">="&DATE(YEAR({today}),1,1))' % (KCR('amount'), KCR('child'), LK('kids_costs', 'child'), KCR('kind'), LK('kids_costs', 'kind'), KCR('date')), 'money'),
        FF('Kids costs that month', 'SUMIFS(%s,%s,%s)' % (KCR('amount'), KCR('month'), LK('kids_costs', 'month')), 'money'),
        FF('Share of the month', 'IFERROR(%s/SUMIFS(%s,%s,%s),0)' % (LK('kids_costs', 'amount'), KCR('amount'), KCR('month'), LK('kids_costs', 'month')), 'pct'),
        FF('Kids costs the same month last year', 'SUMIFS(%s,%s,EDATE(%s,-12))' % (KCR('amount'), KCR('month'), LK('kids_costs', 'month')), 'money')]),
    FORM('child_savings_sheet', 'Child Savings Sheet', 'One allowance paid and the child\'s saving', 'allowances.allowance_id', F(
        ('Date', 'allowances.date'), ('Child', 'allowances.child'), ('Amount', 'allowances.amount'), ('Saved', 'allowances.saved'), ('Spent', 'allowances.spent'), ('Weekday', 'allowances.weekday'),
        ('Saved share', 'allowances.saved_share')) + [
        FF('Saved by the child, last 12 months', 'SUMIFS(%s,%s,%s,%s,">="&({today}-365))' % (ALR('saved'), ALR('child'), LK('allowances', 'child'), ALR('date')), 'money'),
        FF('Allowance paid, last 12 months', 'SUMIFS(%s,%s,%s,%s,">="&({today}-365))' % (ALR('amount'), ALR('child'), LK('allowances', 'child'), ALR('date')), 'money'),
        FF('Saved share, last 12 months', 'IFERROR(SUMIFS(%s,%s,%s,%s,">="&({today}-365))/SUMIFS(%s,%s,%s,%s,">="&({today}-365)),0)' % (
            ALR('saved'), ALR('child'), LK('allowances', 'child'), ALR('date'), ALR('amount'), ALR('child'), LK('allowances', 'child'), ALR('date')), 'pct')]),
    FORM('scenario_sheet', 'Scenario Input Sheet', 'One scenario input and how fresh it is', 'scenarios.scenario_id', F(
        ('Scenario', 'scenarios.scenario'), ('Item', 'scenarios.item'), ('Value', 'scenarios.value'), ('Unit', 'scenarios.unit'), ('Last set on', 'scenarios.set_on')) + [
        FF('Days since it was set', '{today}-%s' % LK('scenarios', 'set_on'), 'int'),
        FF('Inputs in the same scenario', 'COUNTIFS(%s,%s)' % (R('scenarios', 'scenario'), LK('scenarios', 'scenario')), 'int'),
        FF('Inputs in it older than 90 days', 'COUNTIFS(%s,%s,%s,"<"&({today}-90))' % (R('scenarios', 'scenario'), LK('scenarios', 'scenario'), R('scenarios', 'set_on')), 'int')]),
    FORM('lose_income_sheet', 'Lose One Income Sheet', 'One category in the lose-one-income plan', 'lose.category', F(
        ('Group', 'lose.group'), ('Plan a month', 'lose.plan'), ('Share you could cut', 'lose.cut_share'), ('Cut amount', 'lose.cut_amount'), ('New plan', 'lose.new_plan'),
        ('Gap if partner 1 income stops', 'lose.gap_p1'), ('Gap if partner 2 income stops', 'lose.gap_p2'), ('Cuts available', 'lose.cut_total'),
        ('Months of cover, partner 2 stops', 'lose.months_p2'), ('Months of cover, partner 1 stops', 'lose.months_p1')) + [
        FF('Share of the plan', 'IFERROR(%s/%s,0)' % (LK('lose', 'plan'), 'SUM(%s)' % R('lose', 'plan')), 'pct'), FF('Share of all cuts', 'IFERROR(%s/SUM(%s),0)' % (LK('lose', 'cut_amount'), R('lose', 'cut_amount')), 'pct'),
        FF('Cut rank', LK('lose', 'rank_cut'), 'int')]),
    FORM('shock_sheet', 'Expense Shock Sheet', 'A one-off cost landing in one month', 'expense_shock.month', F(
        ('One-off cost', 'expense_shock.cost'), ('Emergency fund before', 'expense_shock.fund_before'), ('Emergency fund after', 'expense_shock.balance_after'),
        ('Months of essentials left', 'expense_shock.months_left'), ('Months of essentials used', 'expense_shock.months_used')) + [
        FF('Share of the fund used', 'IFERROR(%s/%s,0)' % (LK('expense_shock', 'cost'), LK('expense_shock', 'fund_before')), 'pct'),
        FF('Months of deposits to rebuild it', 'IFERROR(%s/{set:emergency_monthly},0)' % LK('expense_shock', 'cost'), 'num'),
        FF('Essential spending a month', NEED(), 'money')]),
    FORM('rate_sheet', 'Rate Change Sheet', 'A debt tested with a rate rise', 'rate_change.rc_id', F(
        ('Debt', 'rate_change.debt'), ('Balance', 'rate_change.balance'), ('Rate now', 'rate_change.rate'), ('Months left', 'rate_change.term_months'), ('Points added', 'rate_change.points'),
        ('Payment now', 'rate_change.payment_now'), ('Payment after', 'rate_change.payment_after'), ('Extra a month', 'rate_change.extra_month'), ('Extra cost a year', 'rate_change.extra_cost_year')) + [
        FF('Rise in the payment', 'IFERROR(%s/%s,0)' % (LK('rate_change', 'extra_month'), LK('rate_change', 'payment_now')), 'pct'),
        FF('Extra a year, all debts, same points', 'SUMIFS(%s,%s,%s)' % (R('rate_change', 'extra_cost_year'), R('rate_change', 'points'), LK('rate_change', 'points')), 'money'),
        FF('Share of that extra cost', 'IFERROR(%s/SUMIFS(%s,%s,%s),0)' % (LK('rate_change', 'extra_cost_year'), R('rate_change', 'extra_cost_year'), R('rate_change', 'points'), LK('rate_change', 'points')), 'pct')]),
    FORM('baby_sheet', 'New Baby Sheet', 'One month of the new baby plan', 'new_baby.month', F(
        ('One-off costs', 'new_baby.one_off'), ('Monthly costs', 'new_baby.monthly'), ('Income lost on leave', 'new_baby.leave_loss'), ('Gap after surplus', 'new_baby.gap'),
        ('Gap so far', 'new_baby.cum_gap'), ('Savings left', 'new_baby.savings_left'), ('Leave starts', 'new_baby.leave_start')) + [
        FF('Month of the plan', '(YEAR(%s)-YEAR({set:baby_month}))*12+MONTH(%s)-MONTH({set:baby_month})+1' % ('{pick}', '{pick}'), 'int'),
        FF('Savings left as a share of the set aside', 'IFERROR(%s/{set:baby_savings},0)' % LK('new_baby', 'savings_left'), 'pct'),
        FF('Gap over all 12 months', 'SUM(%s)' % R('new_baby', 'gap'), 'money')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
SG = ['Partner 1', 'Partner 2']
documents = [
    DOC('fair_split_doc', 'Fair Split Agreement', 'Fair split agreement page', 'split_cmp.sc_id', [
        'Fair split agreement of {set:household}, dated {today}. Rule tested: {col:split_cmp.rule} over {col:split_cmp.months} complete months.',
        'Shared costs in the period: {col:split_cmp.shared_total}. Partner 1 pays {col:split_cmp.p1_pays} ({col:split_cmp.p1_ratio} of the costs); partner 2 pays {col:split_cmp.p2_pays}.',
        'On the split agreed now ({set:agreed_p1_share} for partner 1), partner 2 would pay {col:split_cmp.p2_now}; the difference is {col:split_cmp.difference}.',
        'Both partners agree the rule and review it when take-home pay changes. These are estimates from your own numbers.'], SG, NOTE),
    DOC('settle_doc', 'Settle Up Statement', 'Settle up statement for one month', 'settle.settle_id', [
        'Settle up statement of {set:household}, dated {today}. Month: {col:settle.month}.',
        'Shared costs: {col:settle.total}. Partner 1 paid {col:settle.p1_paid} against a share of {col:settle.p1_share}; partner 2 paid {col:settle.p2_paid} against a share of {col:settle.p2_share}.',
        '{col:settle.from_partner} pays {col:settle.amount} to {col:settle.to_partner} by {col:settle.due_date}. Status: {col:settle.status}.',
        'The statement squares costs paid from different accounts; it is a record between partners, not financial advice.'], SG, NOTE),
    DOC('balance_doc', 'Running Balance Page', 'Running balance page', 'settle.settle_id', [
        'Running balance of {set:household}, after the month {col:settle.month}, dated {today}.',
        'Open balance carried from unsettled months: {col:settle.running_balance} owed to partner 2 (a negative figure is owed to partner 1).',
        'This month: difference {col:settle.diff}; settle by {col:settle.due_date}; status {col:settle.status}.',
        'Settling the open months in one payment needs fewer transfers than settling each month. Estimates from your numbers.'], SG, NOTE),
    DOC('shared_report_doc', 'Shared Costs Report', 'Shared costs report by partner', 'fair_split.month', [
        'Shared costs report of {set:household}, dated {today}. Month: {col:fair_split.month}.',
        'Shared costs: {col:fair_split.shared_total}. Partner 1 should pay {col:fair_split.p1_share} and paid {col:fair_split.p1_paid}. Partner 2 should pay {col:fair_split.p2_share} and paid {col:fair_split.p2_paid}.',
        'Partner 2 over (+) or under (-) the share: {col:fair_split.difference}. Flag: {col:fair_split.flag}. Take-home share of partner 1: {col:fair_split.p1_takehome_share}.',
        'Figures come from the Shared costs sheet and your own agreed shares.'], SG, NOTE),
    DOC('kids_child_doc', 'Kids Costs Page', 'Kids costs page per child', 'kids_year.ky_id', [
        'Kids costs of {set:household}, dated {today}. Year {col:kids_year.year}, {col:kids_year.child}.',
        'Childcare {col:kids_year.childcare}; school costs {col:kids_year.school}; activities {col:kids_year.activities}; clothing {col:kids_year.clothing}; allowance {col:kids_year.allowance}; other {col:kids_year.other}.',
        'Total {col:kids_year.total} against a plan of {col:kids_year.plan} for the year ({col:kids_year.plan_to_date} to date). Over (+) or under (-): {col:kids_year.vs_plan}.',
        'Figures are what you typed in Kids costs; the plan is your own number.'], SG, NOTE),
    DOC('allowance_doc', 'Allowance Record', 'Allowance record per child', 'allowance_summary.as_id', [
        'Allowance record of {set:household}, dated {today}. Child: {col:allowance_summary.child}. Month: {col:allowance_summary.month}.',
        'Allowance paid {col:allowance_summary.paid}; saved {col:allowance_summary.saved}; spent {col:allowance_summary.spent}. Saved share {col:allowance_summary.saved_share} against the {set:save_target} you want.',
        'Saving check: {col:allowance_summary.flag}.', 'A record kept at home to talk about saving and spending with the child.'], ['Parent', 'Child'], NOTE),
    DOC('member_cost_doc', 'Cost per Member Page', 'Cost per household member page', 'cost_member.cm_id', [
        'Cost per household member of {set:household}, dated {today}. Member: {col:cost_member.member}. Year {col:cost_member.year}.',
        'Kids costs {col:cost_member.kids_share}; share of shared costs {col:cost_member.shared_share}; total {col:cost_member.total}; about {col:cost_member.per_month} a month with costs.',
        'The shared costs are split evenly between the {set:household_size} people in the household. Estimates from your numbers.'], SG, NOTE),
    DOC('lose_plan_doc', 'Lose One Income Plan', 'Lose one income plan', 'lose.category', [
        'Lose one income plan of {set:household}, dated {today}. Category: {col:lose.category} ({col:lose.group}).',
        'Plan {col:lose.plan}; cut {col:lose.cut_amount} ({col:lose.cut_share}); new plan {col:lose.new_plan}.',
        'If partner 2 income stops the gap is {col:lose.gap_p2} a month; if partner 1 income stops, {col:lose.gap_p1}. Cuts available: {col:lose.cut_total}.',
        'After the cuts the gap left is {col:lose.left_p2} (partner 2 stops) or {col:lose.left_p1} (partner 1 stops): about {col:lose.months_p2} and {col:lose.months_p1} months of emergency fund. Estimates from your numbers.'], SG, NOTE),
    DOC('shock_doc', 'Expense Shock Plan', 'Expense shock plan', 'expense_shock.month', [
        'Expense shock plan of {set:household}, dated {today}. A one-off cost in {col:expense_shock.month}.',
        'Cost {col:expense_shock.cost}. Emergency fund before {col:expense_shock.fund_before}, after {col:expense_shock.balance_after}.',
        'Months of essential spending left: {col:expense_shock.months_left}; used by the cost: {col:expense_shock.months_used}.',
        'Decide together how to pay: cash above the floor, the emergency fund or a payment plan. An estimate, not advice.'], SG, NOTE),
    DOC('rate_doc', 'Rate Change Note', 'Rate change note', 'rate_change.rc_id', [
        'Rate change note of {set:household}, dated {today}. Debt: {col:rate_change.debt}.',
        'Balance {col:rate_change.balance} at {col:rate_change.rate}; a rise of {col:rate_change.points} points gives {col:rate_change.rate_after}.',
        'Payment now {col:rate_change.payment_now}; after {col:rate_change.payment_after}; extra {col:rate_change.extra_month} a month and {col:rate_change.extra_cost_year} a year.',
        'Ask your lender what is possible if the payment becomes hard to pay. An estimate from your numbers.'], SG, NOTE),
    DOC('baby_doc', 'New Baby Plan Page', 'New baby plan', 'new_baby.month', [
        'New baby plan of {set:household}, dated {today}. Month: {col:new_baby.month}; leave starts {col:new_baby.leave_start}.',
        'One-off costs {col:new_baby.one_off}; monthly costs {col:new_baby.monthly}; income lost on leave {col:new_baby.leave_loss}; gap after your monthly surplus {col:new_baby.gap}.',
        'Gap so far {col:new_baby.cum_gap}; savings left {col:new_baby.savings_left} of {set:baby_savings}.',
        'Estimates from the numbers you typed; check your leave pay with the payroll office.'], SG, NOTE),
    DOC('agreement_doc', 'Household Money Agreement', 'Household money agreement summary', 'overpaid.month', [
        'Household money agreement of {set:household}, dated {today}. Month checked: {col:overpaid.month}.',
        'Agreed share of partner 1: {col:overpaid.agreed_p1}; agreed share of partner 2: {col:overpaid.agreed_p2}. Partner 2 paid {col:overpaid.p2_paid_share} of the shared costs that month.',
        'Months in a row partner 2 was over the agreed share: {col:overpaid.streak}. Review the split on {col:overpaid.review_on}.',
        'Joint account need a month: {set:joint_monthly}. Settle up by day {set:settle_day} of the month. Emergency fund: {set:emergency_balance}.',
        'Both partners confirm these rules and review them when income changes.'], SG, NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('settle_chk', 'Monthly Settle Up Steps', 'settle', 'settle.month', [('Type the last shared costs of the month', 30), ('Check who paid what in Fair split by month', 31), ('Read the Settle Up tool', 32), ('Agree the payment between the partners', 33), ('Make the payment', 35), ('Type the date in Settled on', 36)]),
    CHK('split_chk', 'Set the Fair Split Steps', 'fair_split', 'fair_split.month', [('Run the Income Share tool', 30), ('Compare the rules in Split rule comparison', 31), ('Run the Fair-split Calculator', 32), ('Agree the share and type it in Settings', 33), ('Update the agreed share on new shared costs', 34)]),
    CHK('income_chk', 'Change of Income Steps', 'income', 'income.date', [('Type the new take-home in Income', 0), ('Run the Income Share tool', 7), ('Reset the agreed split in Settings', 14), ('Update the transfer to the joint account', 14), ('Run the Lose One Income Test again', 21)]),
    CHK('transfer_chk', 'Monthly Transfer to Joint Steps', 'fair_split', 'fair_split.month', [('Run the Transfer to Joint tool', -3), ('Agree the amount with your partner', -2), ('Set the standing transfer with your bank', -1), ('Check the transfer arrived', 3), ('Note any change in Settings', 5)]),
    CHK('allowance_chk', 'Allowance Day Steps', 'allowances', 'allowances.date', [('Check the amount in the Allowance Planner', 0), ('Pay the allowance', 0), ('Type it in Allowances with the saved part', 1), ('Talk with the child about saving', 7)]),
    CHK('kids_chk', 'Kids Costs Review Steps', 'kids_costs', 'kids_costs.date', [('Type the kids costs of the month', 30), ('Read Kids Costs per Child', 31), ('Compare with the plan in Kids costs by year', 32), ('Adjust next year\'s plan', 33)]),
    CHK('lose_chk', 'Lose One Income Plan Steps', 'scenarios', 'scenarios.set_on', [('Check the plan and cut shares in Lose one income', 0), ('Run the Lose One Income Test for each partner', 3), ('Run the Cut List to Close the Gap', 5), ('Agree which cuts you would make first', 10), ('Check the emergency fund balance in Settings', 14)]),
    CHK('shock_chk', 'Expense Shock Plan Steps', 'expense_shock', 'expense_shock.month', [('Type the one-off cost in Scenario inputs', 0), ('Run the Expense Shock Test', 1), ('Decide how to pay it', 3), ('Move the money', 5), ('Plan how to rebuild the emergency fund', 14)]),
    CHK('baby_chk', 'New Baby Preparation Steps', 'new_baby', 'new_baby.month', [('Type the baby inputs in Scenario inputs', -180), ('Run the New Baby Plan', -150), ('Set the savings amount to build', -120), ('Ask the payroll office about pay during leave', -90), ('Review the plan with your partner', -30)]),
    CHK('rate_chk', 'Rate Change Review Steps', 'scenarios', 'scenarios.set_on', [('List the debts with a variable rate', 0), ('Run the Interest-rate Change Test', 3), ('Read Rate change by debt', 5), ('Ask your lender for the terms', 10), ('Decide whether to pay extra now', 14)]),
    CHK('mortgage_chk', 'Mortgage Switch Review Steps', 'scenarios', 'scenarios.set_on', [('Type price, down payment, rate and term in Scenario inputs', 0), ('Run the Mortgage Switch Scenario', 3), ('Fill Mortgage switch line by line', 7), ('Talk to your adviser about the numbers', 14), ('Decide together', 30)]),
    CHK('single_chk', 'Single Adult Kids and Scenarios', 'kids_costs', 'kids_costs.date', [('Leave partner 2 and shared cost rows empty', 0), ('Use Kids costs only if you have children', 1), ('Type your plan in Lose one income', 7), ('Run the Expense Shock Test', 14), ('Run the Interest-rate Change Test', 21)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('p2_costs', 'Partner 2: shared costs and share', 'fair_split', 'fair_split.p2_phone', 'Hello {partner2}, shared costs for {month} are {shared_total}; your share is {p2_share}. {household}'),
    M('p2_settle', 'Partner 2: paid against share', 'settle', 'settle.p2_phone', 'Hello {partner2}, for {month} you paid {p2_paid} against a share of {p2_share}. Settle up is {amount}. {household}'),
    M('p2_streak', 'Partner 2: paid more for months', 'overpaid', 'overpaid.p2_phone', 'Hello {partner2}, you have paid more than your share for {streak} months in a row up to {month}. Let us settle. {household}'),
    M('p2_transfer', 'Partner 2: transfer to joint', 'fair_split', 'fair_split.p2_phone', 'Hello {partner2}, on an income share your transfer to the joint account for {month} is {p2_transfer}. {household}'),
    M('p2_review', 'Partner 2: review the split', 'overpaid', 'overpaid.p2_phone', 'Hello {partner2}, let us review the agreed split of {agreed_p1} on {review_on}. {household}'),
    M('p2_drop', 'Partner 2: if income drops', 'lose', 'lose.p2_phone', 'Hello {partner2}, if your income drops to {p2_scn_income}, the monthly gap is {p2_scn_gap}. {household}'),
    M('p2_shock', 'Partner 2: expense shock', 'expense_shock', 'expense_shock.p2_phone', 'Hello {partner2}, a one-off cost of {cost} in {month} leaves {months_left} months of emergency fund. {household}'),
    M('p2_baby', 'Partner 2: new baby gap', 'new_baby', 'new_baby.p2_phone', 'Hello {partner2}, the new baby plan shows a gap of {gap} for {month}. Shall we look at it? {household}'),
    M('p1_costs', 'Partner 1: shared costs and share', 'fair_split', 'fair_split.p1_phone', 'Hello {partner1}, shared costs for {month} are {shared_total}; your share is {p1_share}. {household}'),
    M('p1_owe', 'Partner 1: please settle', 'settle', 'settle.p1_phone', 'Hello {partner1}, for {month} the settle up is {amount} from {from_partner} to {to_partner}. Please settle by {due_date}. {household}'),
    M('p1_balance', 'Partner 1: running balance', 'settle', 'settle.p1_phone', 'Hello {partner1}, the running balance owed to {partner2} is {running_balance} after {month}. {household}'),
    M('p1_transfer', 'Partner 1: transfer to joint', 'fair_split', 'fair_split.p1_phone', 'Hello {partner1}, on an income share your transfer to the joint account for {month} is {p1_transfer}. {household}'),
    M('p1_rate', 'Partner 1: rate change', 'rate_change', 'rate_change.bank_phone', 'Hello {partner1}, a rate change of {points} on {debt} adds {extra_month} a month. {household}'),
    M('p1_mortgage', 'Partner 1: mortgage switch', 'mortgage', 'mortgage.p1_phone', 'Hello {partner1}, the mortgage switch comparison is ready: {total_diff} a month difference, our numbers, not advice. {household}'),
    M('p1_drop', 'Partner 1: if income drops', 'lose', 'lose.p1_phone', 'Hello {partner1}, if your income drops to {p1_scn_income}, the monthly gap is {p1_scn_gap}. {household}'),
    M('hm_report', 'Household member: shared cost report', 'fair_split', 'fair_split.member_phone', 'Hello, the shared cost report for {month} is ready: {shared_total} in all. {household}'),
    M('hm_day', 'Household member: allowance day', 'allowances', 'allowances.member_phone', 'Hello, the allowance day for {child} is {weekday}. {household}'),
    M('hm_kids', 'Household member: kids costs a year', 'kids_year', 'kids_year.member_phone', 'Hello, the kids costs for {year} are {total} for {child}. {household}'),
    M('hm_member', 'Household member: cost per member', 'cost_member', 'cost_member.member_phone', 'Hello, the cost per household member for {year} is ready: {total} for {member}. {household}'),
    M('noa_allow', 'Noa: your allowance', 'allowances', 'allowances.child_phone', 'Hello {child}, your allowance of {amount} is paid on {weekday}. {household}'),
    M('noa_saved', 'Noa: you saved', 'allowance_summary', 'allowance_summary.child_phone', 'Hello {child}, you saved {saved} of your {paid} allowance in {month}, well done. {household}'),
    M('ike_allow', 'Ike: your allowance', 'allowances', 'allowances.child_phone', 'Hi {child}, your allowance of {amount} is paid on {weekday}. {household}'),
    M('ike_saved', 'Ike: you saved', 'allowance_summary', 'allowance_summary.child_phone', 'Hi {child}, you saved {saved} of your allowance in {month}. {household}'),
    M('gp_thanks', 'Grandparent: thank you', 'cost_member', 'cost_member.member_phone', 'Hello, thank you for helping with childcare. We note {per_month} a month of household costs for {name}; tell us if it is not enough. {household}'),
    M('gp_days', 'Grandparent: confirm your days', 'fair_split', 'fair_split.member_phone', 'Hello, please confirm the days you can help with the children in {month}. Thank you. {household}'),
    M('cc_fee', 'Childcare provider: send the fee', 'kids_costs', 'kids_costs.provider_phone', 'Hello, please send the fee for {child} for {month}. Thank you. {household}'),
    M('cc_days', 'Childcare provider: change the days', 'kids_costs', 'kids_costs.provider_phone', 'Hello, we ask to change the days for {child} from {date}. What is possible? {household}'),
    M('sc_costs', 'School office: send the costs', 'kids_costs', 'kids_costs.school_phone', 'Hello, please send the costs for {child} for the term. Thank you. {household}'),
    M('sc_pay', 'School office: confirm payment', 'kids_costs', 'kids_costs.school_phone', 'Hello, please confirm the payment of {amount} for {child} on {date}. {household}'),
    M('bk_standing', 'Bank branch: standing transfer', 'settle', 'settle.bank_phone', 'Hello, please set up a standing transfer of {amount} from the account of {from_partner} to the account of {to_partner}. {household}'),
    M('bk_confirm', 'Bank branch: confirm a transfer', 'settle', 'settle.bank_phone', 'Hello, please confirm the transfer of {amount} due on {due_date}. {household}'),
    M('bk_rate', 'Bank branch: rate review', 'rate_change', 'rate_change.bank_phone', 'Hello, we plan a rate change review for {debt}; please send the terms. {household}'),
    M('pay_leave', 'Payroll office: pay during leave', 'new_baby', 'new_baby.payroll_phone', 'Hello, please confirm my pay during leave from {leave_start}. Thank you. {household}'),
    M('tax_income', 'Tax preparer: change of income', 'lose', 'lose.tax_phone', 'Hello, if one of our incomes changes, please tell us how it affects our tax set-aside. {household}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
SMON = lambda c, m: 'SUMIFS(%s,%s,%s)' % (SHR(c), SHR('month'), m)
YS = '%s,">="&DATE(YEAR({today}),1,1)'
def Y_(rng, dcol, extra=''): return 'SUMIFS(%s,%s,">="&DATE(YEAR({today}),1,1)%s)' % (rng, dcol, extra)
def KYK(kind): return Y_(KCR('amount'), KCR('date'), ',%s,%s' % (KCR('kind'), tok('kidkind', kind)))
def KPC(c): return '(%s+0.5*%s)' % (Y_(KCR('amount'), KCR('date'), ',%s,%s' % (KCR('child'), tok('child', c))), Y_(KCR('amount'), KCR('date'), ',%s,%s' % (KCR('child'), BOTH)))
LASTMON = 'EDATE(%s,-1)' % MS
kpis = [
    KPI('Shared costs this month', SMON('amount', MS), 'money'),
    KPI('Shared costs last 3 months', 'SUMIFS(%s,%s,">="&EDATE(%s,-3),%s,"<"&%s)' % (SHR('amount'), SHR('date'), MS, SHR('date'), MS), 'money'),
    KPI('Shared costs this year', Y_(SHR('amount'), SHR('date')), 'money'),
    KPI('Partner 1 paid this month', 'SUMIFS(%s,%s,%s,%s,%s)' % (SHR('amount'), SHR('month'), MS, SHR('paid_by'), P1), 'money'),
    KPI('Partner 2 paid this month', 'SUMIFS(%s,%s,%s,%s,%s)' % (SHR('amount'), SHR('month'), MS, SHR('paid_by'), P2), 'money'),
    KPI('Partner 2 share paid this month', 'IFERROR(SUMIFS(%s,%s,%s,%s,%s)/%s,0)' % (SHR('amount'), SHR('month'), MS, SHR('paid_by'), P2, SMON('amount', MS)), 'pct'),
    KPI('Agreed partner 2 share', '1-{set:agreed_p1_share}', 'pct'),
    KPI('Partner 2 over agreed share, month', 'SUMIFS(%s,%s,%s,%s,%s)-%s' % (SHR('amount'), SHR('month'), MS, SHR('paid_by'), P2, SMON('p2_share', MS)), 'money'),
    KPI('Months in a row partner 2 over', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('overpaid', 'streak'), LASTMON, R('overpaid', 'month')), 'int'),
    KPI('Running balance owed to partner 2', 'SUM(%s)' % R('settle', 'open_diff'), 'money'),
    KPI('Open settle-up months', 'COUNTIFS(%s,%s)+COUNTIFS(%s,%s)' % (R('settle', 'status'), V('Overdue'), R('settle', 'status'), V('Open')), 'int'),
    KPI('Settled months', 'COUNTIFS(%s,%s)' % (R('settle', 'status'), V('Settled')), 'int'),
    KPI('Partner 1 take-home share', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('fair_split', 'p1_takehome_share'), LASTMON, R('fair_split', 'month')), 'pct'),
    KPI('Partner 2 take-home share', '1-IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('fair_split', 'p1_takehome_share'), LASTMON, R('fair_split', 'month')), 'pct'),
    KPI('Transfer to joint, partner 1', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('transfer_joint', 'transfer'), R('transfer_joint', 'partner'), P1, R('transfer_joint', 'basis'), tok('tbasis', 'Agreed split')), 'money'),
    KPI('Transfer to joint, partner 2', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('transfer_joint', 'transfer'), R('transfer_joint', 'partner'), P2, R('transfer_joint', 'basis'), tok('tbasis', 'Agreed split')), 'money'),
    KPI('Kids costs this month', 'SUMIFS(%s,%s,%s)' % (KCR('amount'), KCR('month'), MS), 'money'),
    KPI('Kids costs this year', Y_(KCR('amount'), KCR('date')), 'money'),
    KPI('Childcare this year', KYK('Childcare'), 'money'), KPI('School costs this year', KYK('School costs'), 'money'), KPI('Activities this year', KYK('Activities'), 'money'),
    KPI('Allowance paid this month', 'SUMIFS(%s,%s,%s)' % (ALR('amount'), ALR('month'), MS), 'money'),
    KPI('Allowance saved this year', Y_(ALR('saved'), ALR('date')), 'money'),
    KPI('Allowance saved share', 'IFERROR(%s/%s,0)' % (Y_(ALR('saved'), ALR('date')), Y_(ALR('amount'), ALR('date'))), 'pct'),
    KPI('Kids costs per child, Noa', KPC('Noa'), 'money'), KPI('Kids costs per child, Ike', KPC('Ike'), 'money'),
    KPI('Cost per household member this year', 'AVERAGEIFS(%s,%s,YEAR({today}))' % (R('cost_member', 'total'), R('cost_member', 'year')), 'money'),
    KPI('Monthly gap if partner 2 income stops', 'AVERAGE(%s)' % R('lose', 'gap_p2'), 'money'),
    KPI('Monthly gap if partner 1 income stops', 'AVERAGE(%s)' % R('lose', 'gap_p1'), 'money'),
    KPI('Emergency fund months if partner 2 stops', 'AVERAGE(%s)' % R('lose', 'months_p2'), 'num'),
]
assert len(kpis) == 30
dashboard = {"title": "Partners and Kids Dashboard", "kpis": kpis,
    "monthly": {"title": "Shared costs, kids costs and allowance by month", "date": "shared.date", "series": [
        {"label": "Shared costs", "sum": "shared.amount", "date": "shared.date"}, {"label": "Kids costs", "sum": "kids_costs.amount", "date": "kids_costs.date"},
        {"label": "Allowance paid", "sum": "allowances.amount", "date": "allowances.date"}]},
    "breakdowns": [{"title": "Shared costs by category", "by": "shared.category", "value": "shared.amount", "agg": "sum"},
                   {"title": "Kids costs by kind", "by": "kids_costs.kind", "value": "kids_costs.amount", "agg": "sum"},
                   {"title": "Kids costs by child", "by": "kids_costs.child", "value": "kids_costs.amount", "agg": "sum"},
                   {"title": "Shared costs by who paid", "by": "shared.paid_by", "value": "shared.amount", "agg": "sum"}]}

def AM(t, c, date=None, label=None, where=None): return AGG('sum', t, '%s.%s' % (t, c), date=('%s.%s' % (t, date)) if date else None, where=where, label=label)
YR = ('year', '=', '{set:report_year}')
insights = {"filters": [{"label": "Paid by", "list": "payer"}, {"label": "Child", "list": "child"}, {"label": "Category", "list": "sharedcat"}],
    "gauges": [
        {"title": "Partner 2 paid against the agreed share", "num": AGG('sum', 'fair_split', 'fair_split.p2_paid'), "den": AGG('sum', 'fair_split', 'fair_split.p2_share')},
        {"title": "Settle-up months closed", "num": AGG('count', 'settle', where=[('status', '=', V('Settled'))]), "den": AGG('count', 'settle')},
        {"title": "Allowance saved share", "num": AGG('sum', 'allowances', 'allowances.saved'), "den": AGG('sum', 'allowances', 'allowances.amount')},
        {"title": "Kids costs against the plan to date", "num": AGG('sum', 'kids_year', 'kids_year.total', where=[YR]), "den": AGG('sum', 'kids_year', 'kids_year.plan_to_date', where=[YR])},
        {"title": "Emergency fund against the gap cover", "num": AGG('sum', 'lose', 'lose.fund_now'), "den": AGG('sum', 'lose', 'lose.fund_need')},
        {"title": "Months paid on the agreed share", "num": AGG('count', 'overpaid', where=[('over', '=', 0)]), "den": AGG('count', 'overpaid')}],
    "charts": [
        CHART('Shared costs per month', 'column', 'month', [AM('shared', 'amount', 'date', 'Shared costs')]),
        CHART('Shared costs by category', 'bar', 'shared.category', [AM('shared', 'amount', 'date', 'Shared costs')]),
        CHART('Shared costs by payer per month', 'stacked', 'month', [AM('shared', 'amount', 'date', 'Partner 1 paid', [('paid_by', '=', P1)]), AM('shared', 'amount', 'date', 'Partner 2 paid', [('paid_by', '=', P2)])]),
        CHART('Partner 2 share paid per month', 'line', 'month', [AM('overpaid', 'p2_paid_share', 'month', 'Share paid'), AM('overpaid', 'agreed_p2', 'month', 'Agreed share')]),
        CHART('Settle up amount per month', 'column', 'month', [AM('settle', 'amount', 'month', 'To settle')]),
        CHART('Running balance per month', 'line', 'month', [AM('settle', 'running_balance', 'month', 'Owed to partner 2')]),
        CHART('Shared costs by split rule', 'bar', 'shared.split_rule', [AM('shared', 'amount', 'date', 'Shared costs')]),
        CHART('Take-home by person per month', 'stacked', 'month', [AM('income', 'net', 'date', 'Partner 1', [('person', '=', P1)]), AM('income', 'net', 'date', 'Partner 2', [('person', '=', P2)])]),
        CHART('Transfers to joint per month, income share', 'stacked', 'month', [AM('fair_split', 'p1_transfer', 'month', 'Partner 1'), AM('fair_split', 'p2_transfer', 'month', 'Partner 2')]),
        CHART('Kids costs per month', 'column', 'month', [AM('kids_costs', 'amount', 'date', 'Kids costs')]),
        CHART('Kids costs by child', 'bar', 'kids_costs.child', [AM('kids_costs', 'amount', 'date', 'Kids costs')]),
        CHART('Kids costs by kind', 'bar', 'kids_costs.kind', [AM('kids_costs', 'amount', 'date', 'Kids costs')]),
        CHART('Kids costs by kind per month', 'stacked', 'month', [AM('kids_costs', 'amount', 'date', k, [('kind', '=', tok('kidkind', k))]) for k in ('Childcare', 'School costs', 'Activities', 'Clothing')]),
        CHART('Childcare per month', 'line', 'month', [AM('kids_costs', 'amount', 'date', 'Childcare', [('kind', '=', tok('kidkind', 'Childcare'))])]),
        CHART('Allowance paid per month', 'column', 'month', [AM('allowances', 'amount', 'date', 'Allowance paid')]),
        CHART('Allowance saved and spent per month', 'stacked', 'month', [AM('allowances', 'saved', 'date', 'Saved'), AM('allowances', 'spent', 'date', 'Spent')]),
        CHART('Allowance by child', 'bar', 'allowances.child', [AM('allowances', 'amount', 'date', 'Allowance paid')]),
        CHART('Kids costs against the plan, report year', 'bar', 'kids_year.child', [AM('kids_year', 'total', None, 'Costs', [YR]), AM('kids_year', 'plan_to_date', None, 'Plan to date', [YR])]),
        CHART('Cost per household member, report year', 'bar', 'cost_member.member', [AM('cost_member', 'total', None, 'Cost for the year', [YR])]),
        CHART('Lose one income: plan before and after cuts', 'bar', 'lose.group', [AM('lose', 'plan', None, 'Plan'), AM('lose', 'new_plan', None, 'Plan after cuts')]),
        CHART('Expense shock: emergency fund after, by month', 'column', 'month', [AM('expense_shock', 'balance_after', 'month', 'Emergency fund after')]),
        CHART('Rate change: extra cost a year by debt', 'bar', 'rate_change.debt', [AM('rate_change', 'extra_cost_year', None, 'Extra cost a year', [('points', '=', 0.02)])])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Fair-split calculator", "why": "shared costs split equally, by take-home share or by your own share, with what each partner pays against the agreed split", "where": "Fair-split Calculator"},
    {"name": "Settle up with the fewest payments", "why": "costs paid from different accounts squared into one payment, with the payments and money saved against settling month by month", "where": "Settle up plan"},
    {"name": "Running settle balance", "why": "the balance carried from unsettled months, since when and what it becomes if you wait", "where": "Running Settle Balance"},
    {"name": "Over-paid streak check", "why": "months in a row one partner paid above the agreed share, so a quiet imbalance is settled before it grows", "where": "Over-paid Streak Check"},
    {"name": "Agreed share check", "why": "the agreed split against what each partner really paid, with the share to reset to", "where": "Agreed Share Check"},
    {"name": "Lose one income test", "why": "one partner's income set to zero or a share: the new monthly gap, the cuts and the months of emergency fund", "where": "Lose One Income Test"},
    {"name": "Cut list to close the gap", "why": "categories ranked by what you could cut, with how many it takes to close the gap you type", "where": "Cut List to Close the Gap"},
    {"name": "Expense shock test", "why": "a one-off cost against cash above your floor and the emergency fund, with the delay if it goes on a card", "where": "Expense Shock Test"},
    {"name": "Interest-rate change test", "why": "points added to a variable loan or card: the new payment and the extra cost a year, debt by debt", "where": "Interest-rate Change Test"},
    {"name": "New baby plan", "why": "one-off and monthly costs and income lost on leave: the monthly gap, how long savings last and what to save before the birth", "where": "New Baby Plan"},
    {"name": "Allowance planner and saved check", "why": "the weekly amount, the pay day and the share each child saves against the share you want", "where": "Allowance Planner"}]
competitors = [
    {"what": "budgeting app with a monthly subscription and bank links", "lacks": "charges every month, has no settle up between partners and cannot show who paid above the agreed share for months in a row"},
    {"what": "single-purpose budget template", "lacks": "one shared column with no fair split, no running balance and no scenario tests for losing an income"},
    {"what": "free expense splitting sheet", "lacks": "splits only equally, forgets the balance from earlier months and has no kids costs or allowances"},
    {"what": "kids chore and allowance chart", "lacks": "tracks stars but not the money: no saved and spent split, no yearly cost per child and no link to the household budget"}]
guide = [
    'Start here: open Start and type the household name, both partner names and the agreed share of partner 1 in the yellow cells.',
    'Replace demo data, step 1: clear the demo rows of Shared costs, Income, Kids costs and Allowances, keep the header row, and keep Team as your own contacts.',
    'Replace demo data, step 2: in Settle up type one row for each complete month with its date; the totals fill in by themselves from Shared costs.',
    'Replace demo data, step 3: type your own plan and cut shares in Lose one income, your debts in Rate change and your numbers in Scenario inputs.',
    'Pay-day routine: when a paycheck or client payment arrives, type it in Income; check the Transfer to Joint tool and set your standing transfer.',
    'Weekly routine: type every shared cost with who paid it, pay the allowance on its day and type it in Allowances with the saved part.',
    'Month-close routine, in this order: type the last shared costs, read Fair split by month, run Settle Up, make the payment, type the date in Settled on, then read Over-paid streak.',
    'Scenario routine: change a value in Scenario inputs, then run the Lose One Income Test, the Expense Shock Test, the Interest-rate Change Test, the New Baby Plan and the Mortgage Switch Scenario.',
    'A single adult with one income and no children can use the kids and scenario sheets and leave partner 2 and the shared cost rows empty.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'Every verdict is an estimate from your numbers; any range shown is a typical range, check your own numbers.',
    'Why a workbook: one flat price, no yearly renewal, your data stays with you and there is nothing to link or re-connect; you type or paste your own data. It works in Excel and Google Sheets with no macros.',
    'What this is not: it is not a bank app, and not tax, legal, investment or credit advice.']
listing = {"title": "Partners, Kids and Shared Costs Excel Template: Fair Split, Settle Up, Allowances, Scenario Tests, Household Budget",
    "headline": "Split shared costs fairly and test what if an income stops",
    "tags": ["fair split", "settle up", "couples budget", "shared expenses", "kids allowance", "household budget", "scenario test", "lose one income", "expense shock", "new baby budget", "excel template", "no subscription", "family finance"],
    "description": ("Run the money between two partners and the children in one Excel workbook, for a couple, a family or a single adult with children. Type your shared costs with who paid and the workbook shows the fair split by month, "
        "what each partner should pay against what each paid, and who owes whom. Settle Up nets the open months into one payment, the Running Balance carries what is still owed and the Over-paid Streak Check shows when one partner paid above the agreed share month after month.\n\n"
        "The Fair-split Calculator compares an equal split, an income share and a custom share, the Income Share tool follows take-home pay, and the Transfer to Joint tool gives each partner's monthly amount and the amount for each payday. "
        "Kids Costs by Child and Year add up childcare, school, activities, clothing and allowance against your own plan, and the Allowance Planner and Saved Check follow what each child saves.\n\n"
        "Scenario tests answer the what-ifs: lose one income, a cut list that closes the gap, an expense shock against your emergency fund, an interest-rate change debt by debt, a new baby plan and a mortgage switch with your own numbers.\n\n"
        f"{len(tools)} tools, {len(forms)} printable sheets, {len(documents)} documents, {len(checklists)} checklists and {len(messages)} ready text messages to partners, the children, the grandparent, the school office and your bank branch are included. "
        "This is part seven of the Household Finance suite. A standard .xlsx workbook that works in Excel and Google Sheets, with no macros, no subscription and no bank links: you type or paste your own data. "
        "It is a household money kit, not a bank app, and not tax, legal, investment or credit advice. Every verdict is an estimate from your own numbers."),
    "features": ["Fair split by month with what each partner paid", "Settle up with the fewest payments and a running balance", "Over-paid streak check for months in a row", "Income share, equal or custom split compared",
                 "Monthly transfer to the joint account", "Kids costs per child and year against your plan", "Allowance planner and saved check", "Lose one income test and cut list",
                 "Expense shock and interest-rate change tests", f"{len(tools)} tools and {len(forms)} printable sheets", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "One flat price, no subscription, no bank links"]}
s = spec(id=f'{SUITE}-p7', slug='household-finance-partners', profession='Household Finance', name='Partners, Kids and Shared Costs',
         tagline='Split shared costs fairly and test what if an income stops', price_usd=29,
         colors={"primary": "#1F5F5B", "accent": "#F2B134"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 7, "of": 8, "focus": "Partners, kids and shared costs"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hf7.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
