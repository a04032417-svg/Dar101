"""Household Finance suite part 1: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf1_lists import *
import hf1_data as D


def R(t, c): return '{range:%s.%s}' % (t, c)
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)


YES = '{list:yesno.yes}'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
PAID_B = tok('bstatus', 'Paid'); PAID_I = tok('istatus', 'Paid')
P1 = tok('person', 'Partner 1'); P2 = tok('person', 'Partner 2')
WIND = tok('isource', 'Windfall'); PAYCK = tok('isource', 'Paycheck'); SIDE = tok('isource', 'Side income')
WEEKLY = tok('payfreq', 'Weekly'); BIWK = tok('payfreq', 'Every two weeks'); TWICE = tok('payfreq', 'Twice a month')
G_FIX, G_VAR, G_WANT, G_SAVE, G_DEBT = (tok('group', g) for g in GROUPS)
UNDER = c1('Under the floor'); ABOVE = c1('Above the floor')
B0 = 'SUMIFS(%s,%s,{set:joint_id})' % (R('accounts', 'balance_now'), R('accounts', 'account_id'))
NP = 'SUMIFS(%s,%s,1)' % (R('low_point', 'payday'), R('low_point', 'pn'))
NP2 = 'SUMIFS(%s,%s,2)' % (R('low_point', 'payday'), R('low_point', 'pn'))
FREQ = '{set:pay_freq}'; ANCH = '{set:next_payday}'


def UNP(d, op='<'):
    """unpaid bills of the joint account due before (or on, op '<=') the date expression d"""
    return 'SUMIFS(%s,%s,"<>"&%s,%s,{set:joint_id},%s,"%s"&(%s))' % (R('bills_due', 'amount'), R('bills_due', 'status'), PAID_B, R('bills_due', 'account_id'), R('bills_due', 'due_date'), op, d)


def PAYIN(hi, op='<'):
    """paychecks that land in the joint account from today up to the date expression hi"""
    return 'SUMIFS(%s,%s,%s,%s,">="&{today},%s,"%s"&(%s))' % (R('pay_schedule', 'expected_net'), R('pay_schedule', 'into_joint'), YES, R('pay_schedule', 'date'), R('pay_schedule', 'date'), op, hi)


def TL(role, col): return 'IFERROR(INDEX({range:team.%s},MATCH({list:role.%s},{range:team.role},0))&"","")' % (col, key('role', role))
def NAME(role, k, label='Name'): return CA(k, label, 'text', TL(role, 'name'), 22)
def PHONE(role, k, label='Phone'): return CA(k, label, 'text', TL(role, 'phone'), 18)
def HOUSE(): return CA('household', 'Household', 'text', '{set:household}', 24)


settings = [
    S('household', 'Household name', 'text', HOUSEHOLD), S('partner1', 'Partner 1 shown as', 'text', 'Partner 1'), S('partner2', 'Partner 2 shown as', 'text', 'Partner 2'),
    S('pay_freq', 'Pay rhythm of partner 1', 'list', key('payfreq', PAYDAY1_FREQ), list='payfreq'), S('next_payday', 'Next pay date of partner 1', 'date', iso(PAYDAY1_NEXT)),
    S('paycheck_net', 'Take-home of one paycheck of partner 1', 'money', D.PAYCHECK_NET), S('p2_budget', 'Partner 2 income you plan on each month', 'money', D.P2_BUDGET),
    S('cash_floor', 'Cash floor of the joint account, your own number', 'money', CASH_FLOOR), S('tight_margin', 'Tight when the low point is within this of the floor', 'money', 150),
    S('joint_id', 'Account ID of the joint checking account', 'text', 'AC-01'), S('daily_spend', 'Daily spending from the joint account, 0 = bills only', 'money', 0),
    S('baseline_months', 'Months of income used for the baseline, 1 to 6', 'int', BASELINE_MONTHS), S('buffer_target', 'Buffer to build, months of baseline', 'int', 3),
    S('needs_share', 'Needs share, a typical range, check your own numbers', 'pct', NEEDS_SHARE), S('wants_share', 'Wants share, a typical range, check your own numbers', 'pct', WANTS_SHARE),
    S('savings_share', 'Savings and debt share, typical range, check your own', 'pct', SAVINGS_SHARE), S('set_aside_pct', 'Freelance income set aside, confirm with your adviser', 'pct', SET_ASIDE_PCT),
    S('tolerance', 'Rounding tolerance when checking amounts', 'money', 1.0), S('extra_debt_share', 'Share of an extra paycheck that goes to debt', 'pct', 0.4),
    S('pay_change_pct', 'Pay change to test, a rise or a cut', 'pct', 0.03),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 team ----------------------------------------------------------------------
tables.append(T('team', 'Team', 'Household members and outside contacts',
    'One row per household member and outside contact: role, phone and e-mail; the messages in this workbook use these phone numbers.', [
    C('member_id', 'Member ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 18), LST('group', 'Group', 'tgroup', 11), C('phone', 'Phone', 'text', 18),
    C('email', 'E-mail', 'text', 26), C('note', 'Note', 'text', 30), C('start', 'Since', 'date', 11), HOUSE()], D.team_d(), 50))
# 2 accounts ------------------------------------------------------------------
tables.append(T('accounts', 'Accounts', 'Accounts with the balance now',
    'One row per account: type, owner, opening balance and balance now (a card or loan balance is the amount owed); the change since opening fills in.', [
    C('account_id', 'Account ID', 'text', 9, required=True), C('account', 'Account', 'text', 26), LST('type', 'Type', 'atype', 12), LST('owner', 'Owner', 'person', 11),
    C('opening_balance', 'Opening balance', 'money', 14), C('balance_now', 'Balance now', 'money', 14),
    CA('change', 'Change since opening', 'money', '{col:balance_now}-{col:opening_balance}', 14), CA('as_of', 'Balance date', 'date', '{today}', 11),
    PHONE('Bank branch', 'bank_phone', 'Bank branch phone'), NAME('Bank branch', 'bank_name', 'Bank branch contact'), HOUSE()], D.accounts_d(), 50))
# 3 categories ----------------------------------------------------------------
tables.append(T('categories', 'Categories', 'Spending categories and their budget group',
    'One row per category with its budget group: needs are fixed bills plus variable needs, then wants, savings and debt payments.', [
    C('category', 'Category', 'text', 24, required=True), LST('group', 'Group', 'group', 15)], D.categories_d(), 50))
# 4 income --------------------------------------------------------------------
tables.append(T('income', 'Income', 'Paychecks, client payments, side income and windfalls',
    'One row per payment received: gross, tax, retirement and other deductions, take-home and the tax set-aside; the share of the month fills in.', [
    C('income_id', 'Income ID', 'text', 10, required=True), C('date', 'Received on', 'date', 11), C('month', 'Month', 'date', 11), LST('person', 'Person', 'person', 11), LST('source', 'Source', 'isource', 13),
    C('gross', 'Gross', 'money', 12), C('tax', 'Tax', 'num', 10), C('retirement', 'Retirement', 'num', 11), C('other_deductions', 'Other deductions', 'num', 11), C('deductions', 'Deductions', 'num', 11),
    C('net', 'Take-home', 'money', 12), C('set_aside', 'Set aside', 'num', 11), C('account_id', 'Account ID', 'text', 9), C('invoice_id', 'Invoice ID', 'text', 10),
    CA('share_of_month', 'Share of the month', 'pct', 'IFERROR({col:net}/SUMIFS({range:income.net},{range:income.month},{col:month}),0)', 10),
    CA('this_month', 'This month, 1 or 0', 'int', 'IF({col:month}=%s,1,0)' % MS, 9)],
    D.income_d(), 400, [A('source', '= ' + WIND, 'good')]))
# 5 invoices ------------------------------------------------------------------
tables.append(T('invoices', 'Freelance Invoices', 'Freelance invoices with days to pay and days late',
    'One row per invoice to a client: issued, due, amount, status and payment date; days to pay, days late, the usual delay of the client and the expected payment date fill in.', [
    C('invoice_id', 'Invoice ID', 'text', 10, required=True), LST('client', 'Client', 'isource', 11), C('issued', 'Issued', 'date', 11), C('due_date', 'Due date', 'date', 11), C('amount', 'Amount', 'money', 11),
    LST('status', 'Status', 'istatus', 9), C('paid_on', 'Paid on', 'date', 11), C('contact_id', 'Contact ID', 'text', 9),
    CA('days_to_pay', 'Days to pay', 'int', 'IF({col:paid_on}>0,{col:paid_on}-{col:issued},"")', 9),
    CA('days_late', 'Days late', 'int', 'IF({col:paid_on}>0,MAX(0,{col:paid_on}-{col:due_date}),IF({col:status}<>%s,MAX(0,{today}-{col:due_date}),""))' % PAID_I, 8),
    CA('late_flag', 'Paid late, 1 or 0', 'int', 'IF({col:paid_on}>0,IF({col:paid_on}>{col:due_date},1,0),"")', 9),
    CA('usual_delay', 'Usual days late of this client', 'int', 'IFERROR(ROUND(AVERAGEIFS({range:invoices.days_late},{range:invoices.client},{col:client},{range:invoices.status},%s),0),0)' % PAID_I, 11),
    CA('expected_pay', 'Expected payment date', 'date', 'IF({col:status}<>%s,IF({col:due_date}<{today},"",{col:due_date}+{col:usual_delay}),"")' % PAID_I, 12),
    CA('chase_rank', 'Chase first, 1 is first', 'int', 'IF({col:status}<>%s,COUNTIFS({range:invoices.status},"<>"&%s,{range:invoices.days_late},">"&{col:days_late})+COUNTIFS({range:invoices.status},"<>"&%s,{range:invoices.days_late},{col:days_late},{range:invoices.amount},">"&{col:amount})+1,"")' % (PAID_I, PAID_I, PAID_I), 10),
    CA('contact', 'Client contact', 'text', LKT('team.name', 'team.member_id', 'contact_id'), 22), CA('phone', 'Client phone', 'text', LKT('team.phone', 'team.member_id', 'contact_id'), 18), HOUSE()],
    D.invoices_d(), 200, [A('status', '= ' + tok('istatus', 'Late'), 'bad'), A('status', '= ' + tok('istatus', 'Sent'), 'warn'), A('status', '= ' + PAID_I, 'good')]))
# 6 pay schedule --------------------------------------------------------------
def SPL(kinds):
    fx = '+'.join('SUMIFS({range:split_lines.fixed_amount},{range:split_lines.kind},%s,{range:split_lines.rule},%s)' % (tok('lkind', k), tok('lrule', 'Fixed amount')) for k in kinds)
    pc = '+'.join('SUMIFS({range:split_lines.percent},{range:split_lines.kind},%s,{range:split_lines.rule},%s)' % (tok('lkind', k), tok('lrule', 'Percent')) for k in kinds)
    return 'IF({col:person}=%s,ROUND(%s+{col:expected_net}*(%s),2),"")' % (P1, fx, pc)
tables.append(T('pay_schedule', 'Pay Schedule', 'Pay dates ahead with the split of each paycheck',
    'One row per expected pay date, up to 12 months ahead: expected take-home and whether it lands in the joint account; the rank, days away and the split by kind fill in.', [
    C('pay_id', 'Pay ID', 'text', 8, required=True), C('date', 'Pay date', 'date', 11), C('month', 'Month', 'date', 11), LST('person', 'Person', 'person', 11), C('source', 'Source', 'text', 22),
    LST('frequency', 'Pay rhythm', 'payfreq', 15), C('expected_net', 'Expected take-home', 'num', 12), C('pays_in_month', 'Pay days in the month', 'int', 9), C('extra_pay_month', 'Extra pay month', 'bool', 9),
    C('into_joint', 'Lands in joint account', 'bool', 10),
    CA('rank', 'Next payday rank', 'int', 'IF(AND({col:into_joint}=%s,{col:date}>={today}),COUNTIFS({range:pay_schedule.into_joint},%s,{range:pay_schedule.date},">="&{today},{range:pay_schedule.date},"<"&{col:date})+1,"")' % (YES, YES), 9),
    CA('days_away', 'Days away', 'int', '{col:date}-{today}', 8),
    CA('split_bills', 'Split: bills', 'money', SPL(['Bills']), 11), CA('split_sinking', 'Split: sinking funds', 'money', SPL(['Sinking funds']), 11), CA('split_debt', 'Split: debt', 'money', SPL(['Debt']), 11),
    CA('split_goals', 'Split: goals and savings', 'money', SPL(['Goals', 'Savings']), 11),
    CA('split_spend', 'Split: spending money', 'money', 'IF({col:person}=%s,ROUND({col:expected_net}-{col:split_bills}-{col:split_sinking}-{col:split_debt}-{col:split_goals},2),"")' % P1, 11),
    CA('pays_ahead', 'Pay dates in the next 90 days', 'int', 'COUNTIFS({range:pay_schedule.into_joint},%s,{range:pay_schedule.date},">="&{today},{range:pay_schedule.date},"<="&({today}+90))' % YES, 9),
    NAME('Partner 1', 'p1_name', 'Partner 1 name'), PHONE('Partner 1', 'p1_phone', 'Partner 1 phone'), NAME('Partner 2', 'p2_name', 'Partner 2 name'), PHONE('Partner 2', 'p2_phone', 'Partner 2 phone'),
    PHONE('Payroll office', 'payroll_phone', 'Payroll office phone'), NAME('Payroll office', 'payroll_name', 'Payroll office contact'), HOUSE()], D.pay_schedule_d(), 80, [A('extra_pay_month', '= ' + YES, 'good')]))
# 7 pay rhythm by month -------------------------------------------------------
P1D = ('IF(%s=%s,INT((EOMONTH({col:month},0)-%s)/7)-INT(({col:month}-1-%s)/7),IF(%s=%s,INT((EOMONTH({col:month},0)-%s)/14)-INT(({col:month}-1-%s)/14),IF(%s=%s,2,1)))'
       % (FREQ, WEEKLY, ANCH, ANCH, FREQ, BIWK, ANCH, ANCH, FREQ, TWICE))
NORMAL = 'IF(%s=%s,4,IF(%s=%s,2,99))' % (FREQ, WEEKLY, FREQ, BIWK)
tables.append(T('pay_rhythm', 'Pay Rhythm by Month', 'Pay days in each of the next 13 months for any pay rhythm',
    'One row per month: partner 1 pay days from the rhythm and next pay date in Settings, the extra pay month flag, expected pay, the budgeted income and the plan left to assign.', [
    C('month', 'Month', 'date', 11, required=True), LST('ahead', 'Months ahead', 'ahead', 13), CA('offset', 'Offset', 'int', '(YEAR({col:month})-YEAR({today}))*12+MONTH({col:month})-MONTH({today})', 7),
    CA('p1_days', 'Partner 1 pay days', 'int', P1D, 9), CA('extra', 'Extra pay month', 'text', 'IF({col:p1_days}>%s,%s,%s)' % (NORMAL, c1('Extra pay month'), c1('Normal month')), 15),
    CA('p1_expected', 'Partner 1 expected pay', 'money', '{col:p1_days}*{set:paycheck_net}', 12),
    CA('p2_expected', 'Partner 2 expected pay', 'money', 'SUMIFS({range:pay_schedule.expected_net},{range:pay_schedule.month},{col:month},{range:pay_schedule.person},%s)' % P2, 12),
    CA('total_expected', 'Total expected pay', 'money', '{col:p1_expected}+{col:p2_expected}', 12), CA('budget_income', 'Income you budget', 'money', '{col:p1_expected}+{set:p2_budget}', 12),
    CA('plan_total', 'Planned outgoings', 'money', 'SUMIFS({range:budget.planned},{range:budget.month},{col:month})', 12), CA('left_to_assign', 'Left to assign', 'money', '{col:budget_income}-{col:plan_total}', 12),
    CA('bills_month', 'Bills due in the month', 'money', 'SUMIFS({range:bills_due.amount},{range:bills_due.month},{col:month})', 12), HOUSE()],
    D.pay_rhythm_d(), 50, [A('extra', '= ' + c1('Extra pay month'), 'good'), A('left_to_assign', '< 0', 'warn')]))
# 8 bills due -----------------------------------------------------------------
NPX = NP
WIN = '{range:bills_due.status},"<>"&%s,{range:bills_due.account_id},{set:joint_id},{range:bills_due.due_date},"<"&(%s)' % (PAID_B, NPX)
tables.append(T('bills_due', 'Bills Due', 'Every bill that falls due, paid, unpaid or late',
    'One row per bill due date: amount, status and payment date; days to due, the balance after the bill, the bill that breaks the cash floor and the act-first rank fill in.', [
    C('due_id', 'Due ID', 'text', 10, required=True), C('bill_id', 'Bill ID', 'text', 8), C('bill', 'Bill', 'text', 24), C('due_date', 'Due date', 'date', 11), C('month', 'Month', 'date', 11), C('amount', 'Amount', 'money', 11),
    LST('status', 'Status', 'bstatus', 9), C('paid_on', 'Paid on', 'date', 11), C('account_id', 'Account ID', 'text', 9), C('autopay', 'Autopay', 'bool', 8), LST('category', 'Category', 'bcat', 18),
    CA('days_to_due', 'Days to due', 'int', 'IF(AND({col:status}<>%s,{col:due_date}>0),{col:due_date}-{today},"")' % PAID_B, 8),
    CA('late_flag', 'Late, 1 or 0', 'int', 'IF({col:paid_on}>0,IF({col:paid_on}>{col:due_date},1,0),IF(AND({col:status}<>%s,{col:due_date}<{today}),1,0))' % PAID_B, 8),
    CA('seq', 'Sequence', 'int', 'VALUE(RIGHT({col:due_id},4))', 8),
    CA('after', 'Joint balance after this bill', 'money', 'IF(AND({col:status}<>%s,{col:account_id}={set:joint_id}),ROUND(%s+%s-%s-SUMIFS({range:bills_due.amount},{range:bills_due.status},"<>"&%s,{range:bills_due.account_id},{set:joint_id},{range:bills_due.due_date},{col:due_date},{range:bills_due.seq},"<="&{col:seq})-{set:daily_spend}*MAX(0,{col:due_date}-{today}),2),"")'
       % (PAID_B, B0, PAYIN('{col:due_date}', '<='), UNP('{col:due_date}'), PAID_B), 13),
    CA('break_date', 'Breaks the floor on', 'date', 'IF({col:after}="","",IF({col:after}<{set:cash_floor},{col:due_date},""))', 11),
    CA('act_rank', 'Act first, 1 is largest', 'int', 'IF(AND({col:status}<>%s,{col:account_id}={set:joint_id},{col:due_date}<%s),COUNTIFS(%s,{range:bills_due.amount},">"&{col:amount})+COUNTIFS(%s,{range:bills_due.amount},{col:amount},{range:bills_due.seq},"<"&{col:seq})+1,"")' % (PAID_B, NPX, WIN, WIN), 9),
    PHONE('Landlord', 'landlord_phone', 'Landlord phone'), PHONE('Childcare provider', 'childcare_phone', 'Childcare provider phone'), PHONE('Utility company', 'utility_phone', 'Utility company phone'),
    PHONE('Bank branch', 'bank_phone', 'Bank branch phone'), NAME('Bank branch', 'bank_name', 'Bank branch contact'), NAME('Landlord', 'landlord_name', 'Landlord contact'), NAME('Childcare provider', 'childcare_name', 'Childcare provider contact'), NAME('Utility company', 'utility_name', 'Utility company contact'), CA('pay_date', 'Next payday', 'date', 'IF(%s>0,%s,"")' % (NPX, NPX), 11), CA('new_date', 'Day after payday', 'date', 'IF(%s>0,%s+1,"")' % (NPX, NPX), 11),
    CA('new_day', 'Day of the month after payday', 'int', 'IF(%s>0,DAY(%s+1),"")' % (NPX, NPX), 9), CA('ask_by', 'Invoice wanted by', 'date', '{col:due_date}-7', 11), HOUSE()],
    D.bills_due_d(), 800, [A('status', '= ' + tok('bstatus', 'Late'), 'bad'), A('status', '= ' + tok('bstatus', 'Unpaid'), 'warn'), A('status', '= ' + PAID_B, 'good'), A('break_date', '> 0', 'bad')]))
# 9 budget plan ---------------------------------------------------------------
tables.append(T('budget', 'Budget Plan', 'Monthly budget as plan lines by category',
    'One row per category and month: the amount planned, from 24 months back to 12 months ahead; needs, wants, savings and debt columns and the this-month flag fill in.', [
    C('plan_id', 'Plan ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('category', 'Category', 'category', 22), LST('group', 'Group', 'group', 15), C('planned', 'Planned', 'money', 11),
    CA('p_needs', 'Needs planned', 'money', 'IF(OR({col:group}=%s,{col:group}=%s),{col:planned},0)' % (G_FIX, G_VAR), 11), CA('p_wants', 'Wants planned', 'money', 'IF({col:group}=%s,{col:planned},0)' % G_WANT, 11),
    CA('p_save', 'Savings planned', 'money', 'IF({col:group}=%s,{col:planned},0)' % G_SAVE, 11), CA('p_debt', 'Debt planned', 'money', 'IF({col:group}=%s,{col:planned},0)' % G_DEBT, 11),
    CA('this_month', 'This month, 1 or 0', 'int', 'IF({col:month}=%s,1,0)' % MS, 9)], D.budget_d(), 1100))
# 10 paycheck split lines ------------------------------------------------------
tables.append(T('split_lines', 'Paycheck Split Lines', 'The rules that split one paycheck',
    'One row per line of the split, in priority order: a percent, a fixed amount or the rest; the Paycheck Allocation sheet turns them into amounts for one paycheck.', [
    C('line_id', 'Line ID', 'text', 8, required=True), C('line', 'Line', 'text', 32), LST('kind', 'Kind', 'lkind', 15), LST('rule', 'Rule', 'lrule', 13), C('percent', 'Percent of paycheck', 'pct', 10),
    C('fixed_amount', 'Fixed amount', 'money', 12), C('priority', 'Priority', 'int', 8)], D.split_lines_d(), 60))
# 11 paycheck allocation ------------------------------------------------------
SL = lambda c: LKN('split_lines.' + c, 'split_lines.line_id', 'line_id')
tables.append(T('alloc', 'Paycheck Allocation', 'One paycheck allocated line by line down to zero',
    'One row per split line: the rule and the amount for one paycheck from Settings, with the running amount left to assign; the last line takes the rest.', [
    REF('line_id', 'Line ID', 'split_lines.line_id', 8, required=True), CA('line', 'Line', 'text', LKT('split_lines.line', 'split_lines.line_id', 'line_id'), 32),
    CA('kind', 'Kind', 'text', LKT('split_lines.kind', 'split_lines.line_id', 'line_id'), 15), CA('rule', 'Rule', 'text', LKT('split_lines.rule', 'split_lines.line_id', 'line_id'), 13),
    CA('priority', 'Priority', 'int', SL('priority'), 8),
    CA('amount', 'Amount', 'money', 'IF({col:rule}=%s,ROUND(%s*{set:paycheck_net},2),IF({col:rule}=%s,%s,MAX(0,ROUND({set:paycheck_net}-SUMIFS({range:split_lines.fixed_amount},{range:split_lines.rule},%s)-{set:paycheck_net}*SUMIFS({range:split_lines.percent},{range:split_lines.rule},%s),2))))'
       % (tok('lrule', 'Percent'), SL('percent'), tok('lrule', 'Fixed amount'), SL('fixed_amount'), tok('lrule', 'Fixed amount'), tok('lrule', 'Percent')), 12),
    CA('share', 'Share of paycheck', 'pct', 'IFERROR({col:amount}/{set:paycheck_net},0)', 9),
    CA('running_left', 'Left to assign', 'money', 'ROUND({set:paycheck_net}-SUMIFS({range:alloc.amount},{range:alloc.priority},"<="&{col:priority}),2)', 12)],
    D.alloc_d(), 50, [A('running_left', '< 0', 'bad')]))
# 12 cash forecast by day -----------------------------------------------------
tables.append(T('forecast', 'Cash Forecast by Day', 'Joint account balance day by day for the next 90 days',
    'One row per day from today: opening balance, paychecks in, unpaid bills out and closing balance against the cash floor; type the day numbers 0 to 89 once and the rest fills in.', [
    C('day_no', 'Day number', 'int', 8, required=True), LST('week', 'Week', 'week', 9), CA('date', 'Date', 'date', '{today}+{col:day_no}', 11),
    CA('opening', 'Opening balance', 'money', 'ROUND({col:closing}-{col:pay_in}+{col:bills_out}+{col:spend},2)', 12),
    CA('pay_in', 'Paychecks in', 'money', 'SUMIFS({range:pay_schedule.expected_net},{range:pay_schedule.into_joint},%s,{range:pay_schedule.date},{col:date})' % YES, 11),
    CA('bills_out', 'Bills out', 'money', 'SUMIFS({range:bills_due.amount},{range:bills_due.status},"<>"&%s,{range:bills_due.account_id},{set:joint_id},{range:bills_due.due_date},{col:date})+IF({col:day_no}=0,%s,0)' % (PAID_B, UNP('{today}')), 11),
    CA('spend', 'Everyday spending', 'money', 'IF({col:day_no}=0,0,{set:daily_spend})', 10),
    CA('closing', 'Closing balance', 'money', 'ROUND(%s+%s-%s-{set:daily_spend}*{col:day_no},2)' % (B0, PAYIN('{col:date}', '<='), UNP('{col:date}', '<=')), 12),
    CA('flag', 'Against the floor', 'text', 'IF({col:closing}<{set:cash_floor},%s,%s)' % (UNDER, ABOVE), 14),
    CA('low_60', 'Lowest balance, 60 days', 'money', 'IFERROR(SUMPRODUCT(MIN({range:forecast.closing}+({range:forecast.day_no}>59)*1000000000)),"")', 12),
    CA('low_60_date', 'Date of the lowest', 'date', 'IFERROR(INDEX({range:forecast.date},MATCH({col:low_60},{range:forecast.closing},0)),"")', 11),
    CA('end_60', 'Balance on day 59', 'money', 'IFERROR(INDEX({range:forecast.closing},MATCH(59,{range:forecast.day_no},0)),"")', 11),
    CA('under_30', 'Days under the floor, next 30', 'int', 'COUNTIFS({range:forecast.flag},%s,{range:forecast.day_no},"<30")' % UNDER, 9),
    PHONE('Partner 2', 'p2_phone', 'Partner 2 phone'), NAME('Partner 2', 'p2_name', 'Partner 2 name'), HOUSE()],
    D.forecast_d(), 90, [A('flag', '= ' + UNDER, 'bad'), A('closing', '< {set:cash_floor}', 'bad')]))
# 13 low point before payday --------------------------------------------------
LD = 'IF({col:pn}=1,{today},IFERROR(INDEX({range:low_point.payday},MATCH({col:pn}-1,{range:low_point.pn},0)),""))'
tables.append(T('low_point', 'Low Point Before Payday', 'The lowest joint balance before each of the next paydays',
    'One row per coming payday: bills due before it, the lowest balance, the date of the low, the gap to your cash floor and a verdict; type 1 to 12 once and the rest fills in.', [
    C('pn', 'Payday number', 'int', 8, required=True),
    CA('payday', 'Payday', 'date', 'IFERROR(INDEX({range:pay_schedule.date},MATCH({col:pn},{range:pay_schedule.rank},0)),"")', 11), CA('days_away', 'Days away', 'int', 'IF({col:payday}="","",{col:payday}-{today})', 8),
    CA('prev_pay', 'Period starts', 'date', 'IF({col:payday}="","",%s)' % LD, 11),
    CA('bills_before', 'Unpaid bills due before it', 'money', 'IF({col:payday}="","",%s)' % UNP('{col:payday}'), 12),
    CA('spend_money', 'Money free until payday', 'money', 'IF({col:payday}="","",MAX(0,ROUND(%s+%s-{col:bills_before},2)))' % (B0, PAYIN('{col:payday}')), 12),
    CA('lowest', 'Lowest balance before payday', 'money', 'IF({col:payday}="","",ROUND(%s+%s-{col:bills_before}-{set:daily_spend}*MAX(0,{col:payday}-1-{today}),2))' % (B0, PAYIN('{col:payday}')), 13),
    CA('low_date', 'Date of the low', 'date', 'IF({col:payday}="","",IF({set:daily_spend}>0,{col:payday}-1,MAX({col:prev_pay},SUMPRODUCT(MAX(({range:bills_due.status}<>%s)*({range:bills_due.account_id}={set:joint_id})*({range:bills_due.due_date}<{col:payday})*{range:bills_due.due_date})))))' % PAID_B, 11),
    CA('floor', 'Cash floor', 'money', '{set:cash_floor}', 10), CA('gap', 'Gap to the floor', 'money', 'IF({col:payday}="","",{col:lowest}-{col:floor})', 11),
    CA('verdict', 'Verdict', 'text', 'IF({col:payday}="","",IF({col:lowest}<{col:floor},%s,IF({col:lowest}<{col:floor}+{set:tight_margin},%s,%s)))' % (c1('Short'), c1('Tight'), c1('Safe')), 10),
    CA('move_in', 'Move in to reach the floor', 'money', 'IF({col:payday}="","",MAX(0,ROUND({col:floor}-{col:lowest},2)))', 12),
    CA('per_day', 'Free money a day', 'money', 'IF({col:payday}="","",IF({col:days_away}>0,ROUND({col:spend_money}/{col:days_away},2),0))', 10),
    NAME('Partner 2', 'p2_name', 'Partner 2 name'), PHONE('Partner 2', 'p2_phone', 'Partner 2 phone'), HOUSE()],
    D.low_point_d(), 50, [A('verdict', '= ' + c1('Short'), 'bad'), A('verdict', '= ' + c1('Tight'), 'warn'), A('verdict', '= ' + c1('Safe'), 'good')]))
# 14 income baseline ----------------------------------------------------------
def RCV(shift): return 'SUMIFS({range:income.net},{range:income.month},EDATE({col:month},%d),{range:income.person},%s,{range:income.source},"<>"&%s)' % (shift, P2, WIND)
LAGS = ['lag%d' % j for j in range(1, 7)]
BASE_MIN = 'MIN(' + ','.join('IF({set:baseline_months}>=%d,{col:lag%d},1000000000)' % (j, j) for j in range(1, 7)) + ')'
BASE_SUM = '(' + '+'.join('IF({set:baseline_months}>=%d,{col:lag%d},0)' % (j, j) for j in range(1, 7)) + ')'
tables.append(T('baseline', 'Income Baseline', 'Irregular income against its baseline, month by month',
    'One row per month of partner 2 income (clients and side income): received, the lowest and average of the months before, above or below baseline and the running total above baseline.', [
    C('month', 'Month', 'date', 11, required=True), CA('offset', 'Offset', 'int', '(YEAR({col:month})-YEAR({today}))*12+MONTH({col:month})-MONTH({today})', 7),
    CA('received', 'Income received', 'money', RCV(0), 12)] + [CA('lag%d' % j, 'Received %d month%s before' % (j, '' if j == 1 else 's'), 'money', RCV(-j), 10) for j in range(1, 7)] + [
    CA('baseline', 'Baseline, lowest of last months', 'money', BASE_MIN, 12), CA('average', 'Average of last months', 'money', 'ROUND(%s/{set:baseline_months},2)' % BASE_SUM, 12),
    CA('status', 'Above or below baseline', 'text', 'IF({col:offset}=0,%s,IF({col:received}>{col:baseline},%s,IF({col:received}<{col:baseline},%s,%s)))' % (c1('Month in progress'), c1('Above baseline'), c1('Below baseline'), c1('At baseline')), 15),
    CA('surplus', 'Above baseline', 'money', 'IF({col:offset}=0,0,{col:received}-{col:baseline})', 11),
    CA('buffer', 'Above baseline, running total', 'money', 'MAX(0,SUMIFS({range:baseline.surplus},{range:baseline.month},"<="&{col:month}))', 13),
    CA('buffer_months', 'Running total in months of baseline', 'num', 'IFERROR(ROUND({col:buffer}/{col:baseline},1),0)', 11),
    CA('above_by', 'Above baseline by', 'money', 'MAX(0,{col:received}-{col:baseline})', 11), CA('below_by', 'Below baseline by', 'money', 'MAX(0,{col:baseline}-{col:received})', 11),
    NAME('Partner 2', 'p2_name', 'Partner 2 name'), PHONE('Partner 2', 'p2_phone', 'Partner 2 phone'), PHONE('Tax preparer', 'tax_phone', 'Tax preparer phone'), NAME('Tax preparer', 'tax_name', 'Tax preparer contact'), HOUSE()],
    D.baseline_d(), 50, [A('status', '= ' + c1('Below baseline'), 'warn'), A('status', '= ' + c1('Above baseline'), 'good')]))
# 15 zero-based month ---------------------------------------------------------
TH = 'SUMIFS({range:pay_rhythm.budget_income},{range:pay_rhythm.offset},0)'
tables.append(T('zero_month', 'Zero-Based Month', 'This month: income minus every planned outgoing down to zero',
    'One row per category: planned this month, its share of the income you budget and what is left to assign after it, in the order of the Order column.', [
    REF('category', 'Category', 'categories.category', 24, required=True), C('order', 'Order', 'int', 7),
    CA('group', 'Group', 'text', LKT('categories.group', 'categories.category', 'category'), 15),
    CA('planned', 'Planned this month', 'money', 'SUMIFS({range:budget.planned},{range:budget.month},%s,{range:budget.category},{col:category})' % MS, 12),
    CA('share', 'Share of income', 'pct', 'IFERROR({col:planned}/{col:take_home},0)', 9),
    CA('left', 'Left to assign', 'money', 'ROUND({col:take_home}-SUMIFS({range:zero_month.planned},{range:zero_month.order},"<="&{col:order}),2)', 12),
    CA('month', 'Month', 'date', MS, 11), CA('take_home', 'Income you budget', 'money', TH, 12), CA('left_final', 'Left to assign at the end', 'money', 'MIN({range:zero_month.left})', 12),
    PHONE('Partner 2', 'p2_phone', 'Partner 2 phone'), NAME('Partner 2', 'p2_name', 'Partner 2 name'), HOUSE()],
    D.zero_month_d(), 50, [A('left', '< 0', 'bad')]))
# 16 needs wants savings ------------------------------------------------------
tables.append(T('need_want', 'Needs Wants Savings', 'Planned needs, wants, savings and debt as a share of income',
    'One row per budget group: planned this month and its share of the income you budget; compare with a typical range, check your own numbers.', [
    LST('group', 'Group', 'group', 16, required=True), CA('planned', 'Planned this month', 'money', 'SUMIFS({range:budget.planned},{range:budget.month},%s,{range:budget.group},{col:group})' % MS, 13),
    CA('share', 'Share of income', 'pct', 'IFERROR({col:planned}/%s,0)' % TH, 11)], D.need_want_d(), 50))
# 17 extra pay months ---------------------------------------------------------
EXTRA = 'IF({col:pays}>%s,({col:pays}-%s)*{set:paycheck_net},0)' % (NORMAL, NORMAL)
tables.append(T('extra_pay', 'Extra Pay Months', 'Months with a third paycheck and what to do with it',
    'One row per month ahead: pay days, the extra paycheck and its suggested split between debt, goals and the buffer; shares come from Settings.', [
    C('month', 'Month', 'date', 11, required=True), CA('offset', 'Offset', 'int', '(YEAR({col:month})-YEAR({today}))*12+MONTH({col:month})-MONTH({today})', 7),
    CA('pays', 'Pay days', 'int', 'SUMIFS({range:pay_rhythm.p1_days},{range:pay_rhythm.month},{col:month})', 8), CA('extra_pay', 'Extra paycheck', 'money', EXTRA, 11),
    CA('to_debt', 'To debt', 'money', 'ROUND({col:extra_pay}*{set:extra_debt_share},2)', 10), CA('to_goals', 'To goals', 'money', 'ROUND({col:extra_pay}*(1-{set:extra_debt_share})/2,2)', 10),
    CA('to_buffer', 'To the buffer', 'money', '{col:extra_pay}-{col:to_debt}-{col:to_goals}', 10),
    CA('use', 'Suggested use', 'text', 'IF({col:extra_pay}>0,%s,%s)' % (c1('Assign the extra paycheck'), c1('No extra paycheck')), 20), CA('month_if_extra', 'Extra pay month', 'date', 'IF({col:extra_pay}>0,{col:month},"")', 11),
    NAME('Partner 1', 'p1_name', 'Partner 1 name'), PHONE('Partner 1', 'p1_phone', 'Partner 1 phone'), PHONE('Payroll office', 'payroll_phone', 'Payroll office phone'), NAME('Payroll office', 'payroll_name', 'Payroll office contact'), HOUSE()],
    D.extra_pay_d(), 50, [A('use', '= ' + c1('Assign the extra paycheck'), 'good')]))
# 18 windfalls ----------------------------------------------------------------
tables.append(T('windfalls', 'Windfalls', 'Bonuses, refunds, gifts and extra paychecks, and their use',
    'One row per windfall: date, source, amount and where it was assigned; the number of paychecks it is worth fills in.', [
    C('wf_id', 'Windfall ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('source', 'Source', 'text', 26), C('amount', 'Amount', 'money', 11), LST('assigned_to', 'Assigned to', 'wuse', 17),
    CA('paychecks_worth', 'Worth in paychecks', 'num', 'ROUND({col:amount}/{set:paycheck_net},2)', 10)], D.windfalls_d(), 60))
# 19 take-home check ----------------------------------------------------------
tables.append(T('take_home', 'Take-Home Check', 'Gross less deductions against the amount that arrived',
    'One row per paycheck: the amount that arrived in the account; gross, deductions, take-home and the difference fill in and flag a paycheck that does not match.', [
    REF('income_id', 'Income ID', 'income.income_id', 10, required=True), C('bank_deposit', 'Amount that arrived', 'num', 12),
    CA('date', 'Received on', 'date', LKN('income.date', 'income.income_id', 'income_id'), 11), CA('person', 'Person', 'text', LKT('income.person', 'income.income_id', 'income_id'), 11),
    CA('gross', 'Gross', 'money', LKN('income.gross', 'income.income_id', 'income_id'), 11), CA('deductions', 'Deductions', 'money', LKN('income.deductions', 'income.income_id', 'income_id'), 11),
    CA('net', 'Take-home', 'money', 'ROUND({col:gross}-{col:deductions},2)', 11), CA('difference', 'Difference', 'money', 'ROUND({col:bank_deposit}-{col:net},2)', 10),
    CA('flag', 'Check', 'text', 'IF(ABS({col:difference})<={set:tolerance},%s,%s)' % (c1('Matches'), c1('Check the difference')), 18),
    NAME('Partner 1', 'p1_name', 'Partner 1 name'), PHONE('Partner 1', 'p1_phone', 'Partner 1 phone'), PHONE('Payroll office', 'payroll_phone', 'Payroll office phone'), NAME('Payroll office', 'payroll_name', 'Payroll office contact'), HOUSE()],
    D.take_home_d(), 80, [A('flag', '= ' + c1('Check the difference'), 'warn'), A('flag', '= ' + c1('Matches'), 'good')]))
# 20 month at a glance --------------------------------------------------------
def GP(g): return 'SUMIFS({range:budget.planned},{range:budget.month},{col:month},{range:budget.group},%s)' % g
tables.append(T('glance', 'Month at a Glance', 'Income, spending, saved and left for each month',
    'One row per month: type the joint balance at month end, what you spent and what you saved; income, what is left, the plan and the planned amount by group fill in.', [
    C('month', 'Month', 'date', 11, required=True), C('joint_close', 'Joint balance at month end', 'money', 13), C('spending', 'Spent', 'money', 12), C('saved', 'Saved', 'money', 12),
    CA('income', 'Take-home income', 'money', 'SUMIFS({range:income.net},{range:income.month},{col:month})', 12), CA('left', 'Left', 'money', 'ROUND({col:income}-{col:spending}-{col:saved},2)', 11),
    CA('planned_spend', 'Planned spending', 'money', 'SUMIFS({range:budget.planned},{range:budget.month},{col:month})-%s' % GP(G_SAVE), 12), CA('over_plan', 'Spent over plan', 'money', '{col:spending}-{col:planned_spend}', 11),
    CA('savings_rate', 'Savings rate', 'pct', 'IFERROR({col:saved}/{col:income},0)', 9),
    CA('plan_fixed', 'Plan: fixed bills', 'money', GP(G_FIX), 11), CA('plan_variable', 'Plan: variable needs', 'money', GP(G_VAR), 11), CA('plan_wants', 'Plan: wants', 'money', GP(G_WANT), 11),
    CA('plan_savings', 'Plan: savings', 'money', GP(G_SAVE), 11), CA('plan_debt', 'Plan: debt payments', 'money', GP(G_DEBT), 11),
    NAME('Partner 1', 'p1_name', 'Partner 1 name'), PHONE('Partner 1', 'p1_phone', 'Partner 1 phone'), PHONE('Partner 2', 'p2_phone', 'Partner 2 phone'), NAME('Partner 2', 'p2_name', 'Partner 2 name'), HOUSE()],
    D.glance_d(), 50, [A('left', '< 0', 'warn'), A('over_plan', '> 0', 'warn')]))
assert len(tables) == 20, len(tables)
