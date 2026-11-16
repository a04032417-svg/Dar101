"""Doula business suite part 8: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du8_lists import *
import du8_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def CO(): return CA('company', 'Business', 'text', '{set:company}', 24)
def OWN(): return CA('owner_phone', 'Owner-doula phone', 'text', '"%s"' % D.OWNER_PHONE, 18)
def ACC(): return CA('accountant_phone', 'Accountant phone', 'text', '"%s"' % D.ACCOUNTANT_PHONE, 18)
def ADM(): return CA('admin_phone', 'Admin phone', 'text', '"%s"' % D.ADMIN_PHONE, 18)
def OWNN(): return CA('owner_name', 'Owner-doula name', 'text', 'IFERROR(INDEX({range:team.name},MATCH(%s,{range:team.role},0))&"","")' % tok('role', 'Owner-doula'), 22)
def ACCN(): return CA('accountant_name', 'Accountant name', 'text', 'IFERROR(INDEX({range:team.name},MATCH(%s,{range:team.role},0))&"","")' % tok('role', 'Accountant'), 22)
def ADMN(): return CA('admin_name', 'Admin name', 'text', 'IFERROR(INDEX({range:team.name},MATCH(%s,{range:team.role},0))&"","")' % tok('role', 'Admin'), 22)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
LM = 'EDATE(%s,-1)' % MS
CASHNOW = 'SUMIFS({range:cash.closing},{range:cash.month},%s)' % MS
def T12(col, k=0, t='pnl', m='month'):
    """sum of a column over the 12 months that end with this month (k=1: the 12 months before)"""
    return 'SUMIFS({range:%s.%s},{range:%s.%s},">"&EDATE(%s,%d),{range:%s.%s},"<="&EDATE(%s,%d))' % (t, col, t, m, MS, -12 - 12 * k, t, m, MS, -12 * k)
def F6(col, t='cash'): return 'SUMIFS({range:%s.%s},{range:%s.month},">="&EDATE(%s,-6),{range:%s.month},"<"&%s)' % (t, col, t, MS, t, MS)
MOVED, PLANNED = tok('taxstatus', 'Moved'), tok('taxstatus', 'Planned')
SIGNED = tok('ctstatus', 'Signed'); PAYFULL = tok('plan', 'Pay in full'); PAID, UNPAID = tok('istatus', 'Paid'), tok('istatus', 'Unpaid')
BOOKED, ONCALL = tok('cstatus', 'Booked'), tok('cstatus', 'On call'); PPKIND = tok('ckind', 'Postpartum'); CANC = tok('cstatus', 'Cancelled')
RAGT = {k: tok('rag', k) for k in RAG}
TRD = {k: tok('trend', k) for k in TREND}

settings = [
    S('company', 'Your business name', 'text', COMPANY), S('owner_draw', 'Owner draw per month', 'money', OWNER_DRAW), S('tax_set_aside_pct', 'Income tax set-aside share (confirm with your adviser)', 'pct', TAX_SET_ASIDE_PCT),
    S('cash_floor', 'Lowest cash you accept', 'money', CASH_FLOOR), S('cash_cover_months', 'Months of cover you want', 'int', CASH_COVER_MONTHS), S('renewal_red_days', 'Renewals due within this many days are red', 'int', RENEWAL_RED_DAYS),
    S('renewal_amber_days', 'Renewals due within this many days are amber', 'int', RENEWAL_AMBER_DAYS), S('cpd_target_hours', 'Training hours a year per doula', 'int', CPD_TARGET_HOURS),
    S('drop_flag_pct', 'Change that counts as a drop or a rise', 'pct', 0.10), S('best_factor', 'Best case: new booking cash times', 'num', 1.15), S('worst_factor', 'Worst case: new booking cash times', 'num', 0.8),
    S('income_target', 'Income target for the year', 'money', 300000), S('draw_step', 'Owner draw step for the draw scenario', 'pct', 0.10), S('fixed_share_max', 'Highest fixed costs as a share of revenue', 'pct', 0.15),
    S('budget_tolerance', 'Spending over budget that you accept', 'pct', 0.10), S('alloc_prenatal', 'Share of a package earned by the on-call start', 'pct', ALLOC['prenatal']),
    S('timeoff_weeks', 'Weeks of time off to test', 'int', 4), S('timeoff_stop_share', 'Share of income that stops during time off', 'pct', 0.35), S('alloc_postpartum', 'Share of a birth package earned after the birth', 'pct', ALLOC['postpartum']),
]
assert 3 <= len(settings) <= 20

tables = []
# ---------------------------------------------------------------- 1 profit and loss
tables.append(T('pnl', 'Profit and Loss', 'Profit and Loss Statement by month',
    'One row per month: income by source (postpartum is the weeks after a birth) and costs; revenue, profit, margin, cost per birth and the comparison with your own history fill in by themselves.', [
    C('pnl_id', 'Month ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('birth_income', 'Birth income', 'money', 12), C('postpartum_income', 'Postpartum income', 'money', 12), C('addon_income', 'Add-on income', 'money', 12),
    C('class_income', 'Class income', 'money', 12), C('other_income', 'Other income', 'money', 12), C('doula_pay', 'Doula pay', 'money', 12), C('backup_pay', 'Backup pay', 'money', 12), C('mileage', 'Mileage cost', 'money', 12),
    C('admin_pay', 'Admin pay', 'int', 12), C('other_costs', 'Other costs', 'money', 12), C('births', 'Births', 'int', 8), C('visit_hours', 'Visit hours', 'num', 9),
    CA('revenue', 'Revenue', 'money', '{col:birth_income}+{col:postpartum_income}+{col:addon_income}+{col:class_income}+{col:other_income}', 12),
    CA('costs', 'Total costs', 'money', '{col:doula_pay}+{col:backup_pay}+{col:mileage}+{col:admin_pay}+{col:other_costs}', 12), CA('profit', 'Profit before owner pay', 'money', '{col:revenue}-{col:costs}', 12),
    CA('margin', 'Profit margin', 'pct', 'IF({col:revenue}>0,{col:profit}/{col:revenue},0)', 9), CA('doula_share', 'Doula pay share of revenue', 'pct', 'IF({col:revenue}>0,({col:doula_pay}+{col:backup_pay})/{col:revenue},0)', 9),
    CA('cost_share', 'Cost share of revenue', 'pct', 'IF({col:revenue}>0,{col:costs}/{col:revenue},0)', 9), CA('fixed_share', 'Fixed cost share of revenue', 'pct', 'IF({col:revenue}>0,({col:admin_pay}+{col:other_costs})/{col:revenue},0)', 9),
    CA('cost_birth', 'Cost per birth', 'money', 'IF({col:births}>0,{col:costs}/{col:births},0)', 11), CA('profit_birth', 'Profit per birth', 'money', 'IF({col:births}>0,{col:profit}/{col:births},0)', 11),
    CA('revenue_birth', 'Revenue per birth', 'money', 'IF({col:births}>0,{col:revenue}/{col:births},0)', 11),
    CA('margin_avg3', 'Margin, last 3 months', 'pct', 'IFERROR(AVERAGEIFS({range:pnl.margin},{range:pnl.month},">="&EDATE({col:month},-3),{range:pnl.month},"<"&{col:month}),{col:margin})', 9),
    CA('margin_ly', 'Margin, same month last year', 'pct', 'IF(COUNTIFS({range:pnl.month},EDATE({col:month},-12))>0,SUMIFS({range:pnl.margin},{range:pnl.month},EDATE({col:month},-12)),"")', 9),
    CA('in12', 'In the last 12 months', 'int', 'IF(AND({col:month}>EDATE(%s,-12),{col:month}<=%s),1,0)' % (MS, MS), 8),
    CA('above_avg', 'Margin at or above the 12-month margin', 'int', 'IF(AND({col:in12}=1,{col:margin}>=SUMIFS({range:pnl.profit},{range:pnl.in12},1)/SUMIFS({range:pnl.revenue},{range:pnl.in12},1)),1,0)', 9),
    CA('fixed_costs', 'Fixed costs', 'money', '{col:admin_pay}+{col:other_costs}', 12), CA('profit12', 'Profit, last 12 months', 'money', 'IF({col:in12}=1,{col:profit},"")', 12),
    CA('closing_cash', 'Closing cash', 'money', 'SUMIFS({range:cash.closing},{range:cash.month},{col:month})', 12), CA('tax_aside', 'Set-aside', 'money', 'SUMIFS({range:tax.set_aside},{range:tax.month},{col:month})', 11),
    CA('expenses_total', 'Expenses sheet total', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.month},{col:month})', 12), CA('expenses_diff', 'Other costs less Expenses sheet', 'money', 'ROUND({col:other_costs}-{col:expenses_total},0)', 11),
    OWN(), OWNN(), ACC(), ACCN(), CO()], D.pnl_d(), 60, [A('profit', '< 0', 'bad')]))
# ---------------------------------------------------------------- 2 cash by month
tables.append(T('cash', 'Cash by Month', 'Cash by month: opening, cash in, cash out and closing balance',
    'One row per month: opening cash, cash in, pay out, expenses, refunds, set-aside, owner draw and closing cash; the months of cover, the floor check and the roll-forward check fill in by themselves.', [
    C('cash_id', 'Cash ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('opening', 'Opening cash', 'money', 12), C('cash_in', 'Cash in', 'money', 12), C('pay_out', 'Pay out', 'money', 12),
    C('expenses_out', 'Expenses out', 'money', 12), C('refunds', 'Refunds', 'money', 11), C('set_aside', 'Set-aside moved', 'money', 11), C('owner_draw', 'Owner draw', 'int', 11), C('closing', 'Closing cash', 'money', 12),
    CA('costs_out', 'Costs out', 'money', '{col:pay_out}+{col:expenses_out}+{col:refunds}', 12), CA('net_change', 'Change in cash', 'money', '{col:closing}-{col:opening}', 12),
    CA('fixed_avg3', 'Fixed costs, 3-month average', 'money', 'IFERROR(AVERAGEIFS({range:pnl.fixed_costs},{range:pnl.month},">"&EDATE({col:month},-3),{range:pnl.month},"<="&{col:month}),0)', 12),
    CA('cover', 'Months of cover (fixed costs and draw)', 'num', 'IF({col:fixed_avg3}+{set:owner_draw}>0,{col:closing}/({col:fixed_avg3}+{set:owner_draw}),0)', 9),
    CA('above_floor', 'Above the floor', 'int', 'IF({col:closing}>={set:cash_floor},1,0)', 8), CA('cover_ok', 'Cover reaches the setting', 'int', 'IF({col:cover}>={set:cash_cover_months},1,0)', 8),
    CA('drop', 'Fall in cash (full months)', 'money', 'IF({col:month}<%s,MAX(0,{col:opening}-{col:closing}),0)' % MS, 11),
    CA('roll_diff', 'Roll-forward difference', 'money', 'ROUND({col:opening}+{col:cash_in}-{col:pay_out}-{col:expenses_out}-{col:refunds}-{col:set_aside}-{col:owner_draw}-{col:closing},0)', 11),
    CA('floor', 'Your floor', 'money', '{set:cash_floor}', 11), OWN(), OWNN(), CO()], D.cash_d(), 60, [A('above_floor', '= 0', 'bad')]))
# ---------------------------------------------------------------- 3 tax set-aside
tables.append(T('tax', 'Tax Set-aside', 'Income tax set-aside by month (confirm with your adviser)',
    'One row per month: the set-aside share, the date it was moved and its status; the profit, the set-aside, the due date and the quarter total fill in by themselves.', [
    C('tax_id', 'Set-aside ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('set_aside_pct', 'Set-aside share', 'pct', 9), C('moved_on', 'Moved on', 'date', 11), LST('status', 'Status', 'taxstatus', 11),
    CA('profit', 'Profit', 'money', 'IFERROR(INDEX({range:pnl.profit},MATCH({col:month},{range:pnl.month},0)),0)', 12), CA('set_aside', 'Set-aside', 'money', 'ROUND(MAX(0,{col:profit})*{col:set_aside_pct},2)', 12),
    CA('due_by', 'Move by', 'date', 'EDATE({col:month},1)+4', 11), CA('planned_by', 'Planned, move by', 'date', 'IF({col:status}=%s,{col:due_by},"")' % PLANNED, 11), CA('due_passed', 'Due date passed', 'int', 'IF({col:due_by}<={today},1,0)', 8),
    CA('on_time', 'Moved on time', 'int', 'IF(AND({col:status}=%s,{col:moved_on}>0,{col:moved_on}<={col:due_by}),1,0)' % MOVED, 8),
    CA('late', 'Late', 'int', 'IF(AND({col:status}=%s,{col:due_passed}=1),1,0)' % PLANNED, 8),
    CA('quarter_set_aside', 'Set-aside, quarter', 'money', 'SUMIFS({range:tax.set_aside},{range:tax.month},">="&DATE(YEAR({col:month}),3*INT((MONTH({col:month})-1)/3)+1,1),{range:tax.month},"<"&EDATE(DATE(YEAR({col:month}),3*INT((MONTH({col:month})-1)/3)+1,1),3))', 12),
    OWN(), OWNN(), ACC(), ACCN(), CO()], D.tax_d(), 60, [A('status', '= ' + PLANNED, 'warn'), A('late', '= 1', 'bad')]))
# ---------------------------------------------------------------- 4 expenses
tables.append(T('expenses', 'Expenses', 'Expense tracker: every cost by category and payee',
    'One row per expense: date, category, description, amount and payee; the month fills in and the budget variance sheet adds the rows up against the monthly budget.', [
    C('expense_id', 'Expense ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), LST('category', 'Category', 'expcat', 22), C('description', 'Description', 'text', 28), C('amount', 'Amount', 'money', 11),
    LST('paid_to', 'Paid to', 'payee', 24), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    CA('cat_month', 'Category total, month', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.category},{col:category},{range:expenses.month},{col:month})', 12),
    CA('cat_12m', 'Category total, 12 months', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.category},{col:category},{range:expenses.date},">"&EDATE({today},-12),{range:expenses.date},"<="&{today})', 12),
    CA('month_all', 'All expenses, month', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.month},{col:month})', 12), CA('cat_share', 'Category share of the month', 'pct', 'IF({col:month_all}>0,{col:cat_month}/{col:month_all},0)', 9), ADM(), ADMN(), CO()], D.expenses_d(), 1500))
# ---------------------------------------------------------------- 5 budget
tables.append(T('budget', 'Budget', 'Monthly budget by expense category',
    'One row per expense category: the monthly budget you set; the budget against actual sheet compares each month of spending with it.', [
    LST('category', 'Category', 'expcat', 24, required=True), C('monthly_budget', 'Monthly budget', 'money', 14)], D.budget_d(), 50))
# ---------------------------------------------------------------- 6 renewals
tables.append(T('renewals', 'Renewals', 'Renewals tracker: certification, insurance, registration and checks',
    'One row per renewal: holder, item, due date, the date renewed and the cost; the days left, the red amber green status and the next renewal of each holder fill in by themselves.', [
    C('renewal_id', 'Renewal ID', 'text', 10, required=True), REF('holder', 'Holder', 'team.name', 22), LST('item', 'Item', 'renewal', 22), C('due_date', 'Due date', 'date', 11), C('renewed_on', 'Renewed on', 'date', 11),
    C('cost', 'Cost', 'money', 11),
    CA('is_open', 'Open', 'int', 'IF({col:renewed_on}>0,0,1)', 8), CA('days_left', 'Days left', 'int', 'IF({col:is_open}=1,{col:due_date}-{today},"")', 8),
    CA('is_red', 'Red', 'int', 'IF(AND({col:is_open}=1,{col:due_date}-{today}<={set:renewal_red_days}),1,0)', 8),
    CA('is_amber', 'Amber', 'int', 'IF(AND({col:is_open}=1,{col:due_date}-{today}>{set:renewal_red_days},{col:due_date}-{today}<={set:renewal_amber_days}),1,0)', 8),
    CA('status', 'Status', 'text', 'IF({col:is_open}=0,%s,IF({col:due_date}<{today},%s,IF({col:is_red}=1,%s,IF({col:is_amber}=1,%s,%s))))' % (RAGT['Done'], RAGT['Overdue'], RAGT['Red'], RAGT['Amber'], RAGT['Green']), 11),
    CA('open_due', 'Open due date', 'date', 'IF({col:is_open}=1,{col:due_date},"")', 11),
    CA('item_rank', 'Order of this item', 'int', 'IF({col:is_open}=1,COUNTIFS({range:renewals.item},{col:item},{range:renewals.open_due},"<"&{col:open_due})+1,"")', 8),
    CA('item_key', 'Item key', 'text', 'IF({col:is_open}=1,{col:item}&"|"&{col:item_rank},"")', 20),
    CA('holder_rank', 'Order for the holder', 'int', 'IF({col:is_open}=1,COUNTIFS({range:renewals.holder},{col:holder},{range:renewals.open_due},"<"&{col:open_due})+1,"")', 8),
    CA('holder_key', 'Holder key', 'text', 'IF({col:is_open}=1,{col:holder}&"|"&{col:holder_rank},"")', 22),
    CA('month', 'Due month', 'date', 'DATE(YEAR({col:due_date}),MONTH({col:due_date}),1)', 11),
    CA('phone', 'Holder phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH({col:holder},{range:team.name},0))&"","")', 18), OWN(), OWNN(), CO()],
    D.renewals_d(), 300, [A('status', '= ' + RAGT['Red'], 'bad'), A('status', '= ' + RAGT['Overdue'], 'bad'), A('status', '= ' + RAGT['Amber'], 'warn'), A('status', '= ' + RAGT['Done'], 'good')]))
# ---------------------------------------------------------------- 7 renewal items
tables.append(T('renewal_items', 'Renewal Items', 'Renewal items with the cycle and the usual cost',
    'One row per kind of renewal: how many days one renewal lasts and what it usually costs; use it to plan the next one.', [
    LST('item', 'Item', 'renewal', 24, required=True), C('cycle_days', 'Cycle, days', 'int', 10), C('cost', 'Usual cost', 'money', 11)], D.items_d(), 50))
# ---------------------------------------------------------------- 8 training
tables.append(T('training', 'Training', 'Training and continuing education log',
    'One row per training: holder, kind, title, date, hours and cost; the yearly hours of each doula against the target fill in on Training Hours by Holder.', [
    C('training_id', 'Training ID', 'text', 10, required=True), REF('holder', 'Holder', 'team.name', 22), LST('kind', 'Kind', 'cpd', 16), C('title', 'Title', 'text', 28), C('date', 'Date', 'date', 11), C('hours', 'Hours', 'num', 8),
    C('cost', 'Cost', 'money', 11), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('done', 'Done', 'int', 'IF({col:date}<={today},1,0)', 8),
    CA('days_to', 'Days to training', 'int', '{col:date}-{today}', 9), CA('phone', 'Holder phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH({col:holder},{range:team.name},0))&"","")', 18), CO()],
    D.training_d(), 200))
# ---------------------------------------------------------------- 9 instalments
tables.append(T('instalments', 'Instalments', 'Payment plan instalments: due, paid and unpaid',
    'One row per instalment: client, due date, amount, paid on and status; the month, the days late and the cash expected next month fill in by themselves.', [
    C('inst_id', 'Instalment ID', 'text', 10, required=True), C('client_id', 'Client ID', 'text', 10), REF('client', 'Client', 'clients.client', 22), C('due_date', 'Due date', 'date', 11), C('amount', 'Amount', 'money', 11),
    C('paid_on', 'Paid on', 'date', 11), LST('status', 'Status', 'istatus', 10), CA('month', 'Due month', 'date', 'DATE(YEAR({col:due_date}),MONTH({col:due_date}),1)', 11),
    CA('is_open', 'Open', 'int', 'IF({col:status}=%s,1,0)' % UNPAID, 8), CA('days_late', 'Days late', 'int', 'IF(AND({col:is_open}=1,{col:due_date}<{today}),{today}-{col:due_date},0)', 8),
    CA('expect_on', 'Expected in', 'date', 'IF({col:is_open}=1,MAX({col:due_date},EDATE(%s,1)),"")' % MS, 11)], D.instalments_d(), 500, [A('days_late', '> 0', 'bad'), A('status', '= ' + UNPAID, 'warn')]))
# ---------------------------------------------------------------- 10 contracts
tables.append(T('contracts', 'Contracts', 'Contracts with the cash received and the unearned balance',
    'One row per contract: package, price, deposit (a payment that reserves the date), dates and plan; cash received, the unearned balance (cash received for work not yet done) and balance due fill in.', [
    C('contract_id', 'Contract ID', 'text', 10, required=True), C('client_id', 'Client ID', 'text', 10), REF('client', 'Client', 'clients.client', 22), C('package', 'Package', 'text', 22), LST('kind', 'Kind', 'ckind', 11),
    C('price', 'Price', 'money', 11), C('deposit', 'Deposit', 'money', 11), C('signed_on', 'Signed on', 'date', 11), C('deposit_paid_on', 'Deposit paid on', 'date', 11), C('balance_due', 'Balance due', 'date', 11),
    C('balance_paid_on', 'Balance paid on', 'date', 11), LST('plan', 'Payment plan', 'plan', 13), LST('status', 'Status', 'ctstatus', 11), C('pack_hours', 'Hour pack hours', 'num', 9), C('pack_used', 'Hour pack hours used', 'num', 9),
    CA('client_status', 'Client status', 'text', 'IFERROR(INDEX({range:clients.status},MATCH({col:client_id},{range:clients.client_id},0))&"","")', 14),
    CA('cash_received', 'Cash received', 'money', 'IF({col:deposit_paid_on}>0,{col:deposit},0)+IF({col:balance_paid_on}>0,{col:price}-{col:deposit},0)+SUMIFS({range:instalments.amount},{range:instalments.client_id},{col:client_id},{range:instalments.status},%s)' % PAID, 12),
    CA('pack_share', 'Share of the hour pack used', 'pct', 'IF({col:pack_hours}>0,MIN(1,{col:pack_used}/{col:pack_hours}),0)', 9),
    CA('earned_share', 'Share earned', 'pct', 'IF({col:status}<>%s,1,IF({col:client_status}=%s,0,IF({col:client_status}=%s,{set:alloc_prenatal},IF({col:kind}=%s,{col:pack_share},1-{set:alloc_postpartum}*(1-{col:pack_share})))))' % (SIGNED, BOOKED, ONCALL, PPKIND), 9),
    CA('unearned', 'Unearned balance', 'money', 'IF({col:status}=%s,ROUND(MAX(0,{col:cash_received}-{col:price}*{col:earned_share}),2),0)' % SIGNED, 12),
    CA('owing', 'Still to receive', 'money', 'IF({col:status}=%s,MAX(0,{col:price}-{col:cash_received}),0)' % SIGNED, 12),
    CA('balance_open', 'Balance due, pay in full', 'money', 'IF(AND({col:status}=%s,{col:plan}=%s,{col:balance_paid_on}=0,{col:balance_due}>0),ROUND(MAX(0,{col:price}-{col:deposit}),2),0)' % (SIGNED, PAYFULL), 12),
    CA('expect_on', 'Balance expected in', 'date', 'IF({col:balance_open}>0,MAX({col:balance_due},EDATE(%s,1)),"")' % MS, 11)], D.contracts_d(), 500, [A('unearned', '> 0', 'warn')]))
# ---------------------------------------------------------------- 11 clients
tables.append(T('clients', 'Clients', 'Clients with package, estimated due date and status',
    'One row per client (name only): kind, package, estimated due date (a date the client gives) and status; the due month and the birth count for the cash forecast fill in.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 22), LST('kind', 'Kind', 'ckind', 11), C('package', 'Package', 'text', 22), C('edd', 'Estimated due date', 'date', 11), LST('status', 'Status', 'cstatus', 15),
    CA('due_month', 'Due month', 'date', 'DATE(YEAR({col:edd}),MONTH({col:edd}),1)', 11), CA('birth_due', 'Birth due', 'int', 'IF(AND({col:status}<>%s,{col:kind}<>%s),1,0)' % (CANC, PPKIND), 8)], D.clients_d(), 500))
# ---------------------------------------------------------------- 12 team
RO = '{col:role}=%s' % tok('role', 'Owner-doula'); RC = '{col:role}=%s' % tok('role', 'Contracted doula'); RB = '{col:role}=%s' % tok('role', 'Backup doula')
tables.append(T('team', 'Team', 'Team with training hours and the next renewal',
    'One row per person: doulas, backup doulas (a second doula who attends if the assigned one cannot), the admin and outside contacts; training hours and the next renewal fill in by themselves.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 20), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
    CA('cpd_hours', 'Training hours, 12 months', 'num', 'SUMIFS({range:training.hours},{range:training.holder},{col:name},{range:training.date},">"&EDATE({today},-12),{range:training.date},"<="&{today})', 9),
    CA('cpd_gap', 'Hours short of the target', 'num', 'IF(OR(%s,%s,%s),MAX(0,{set:cpd_target_hours}-{col:cpd_hours}),0)' % (RO, RC, RB), 9),
    CA('open_renewals', 'Open renewals', 'int', 'COUNTIFS({range:renewals.holder},{col:name},{range:renewals.is_open},1)', 8),
    CA('next_item', 'Next renewal', 'text', 'IFERROR(INDEX({range:renewals.item},MATCH({col:name}&"|1",{range:renewals.holder_key},0))&"","")', 22),
    CA('next_due', 'Next renewal due', 'date', 'IFERROR(INDEX({range:renewals.due_date},MATCH({col:name}&"|1",{range:renewals.holder_key},0)),"")', 11), CO()], D.team_d(), 50))
# ---------------------------------------------------------------- 13 cash forecast
AVGB = '(SUMIFS({range:pnl.births},{range:pnl.month},">="&EDATE(%s,-12),{range:pnl.month},"<"&%s)/12)' % (MS, MS)
BALB = 'IFERROR((SUMIFS({range:contracts.price},{range:contracts.signed_on},">="&EDATE(%s,-12),{range:contracts.signed_on},"<"&%s,{range:contracts.kind},"<>"&%s)-SUMIFS({range:contracts.deposit},{range:contracts.signed_on},">="&EDATE(%s,-12),{range:contracts.signed_on},"<"&%s,{range:contracts.kind},"<>"&%s))/COUNTIFS({range:contracts.signed_on},">="&EDATE(%s,-12),{range:contracts.signed_on},"<"&%s,{range:contracts.kind},"<>"&%s),0)' % ((MS, MS, PPKIND) * 3)
def NETF(f): return 'ROUND({col:scheduled_in}+({col:new_in}+{col:unbooked_in})*%s-{col:expected_costs}-{col:owner_pay}-{set:tax_set_aside_pct}*MAX(0,{col:scheduled_in}+({col:new_in}+{col:unbooked_in})*%s-{col:expected_costs}),0)' % (f, f)
tables.append(T('forecast', 'Cash Forecast', 'Cash Forecast for the next 12 months from due dates and payment plans',
    'One row per coming month: cash expected from instalments, balances and new bookings, costs, owner pay and set-aside, then the closing cash, the months of cover and the best and worst cases; uneven months show where cash dips.', [
    C('month', 'Month', 'date', 11, required=True), CA('ahead', 'Months ahead', 'int', '(YEAR({col:month})-YEAR(%s))*12+MONTH({col:month})-MONTH(%s)' % (MS, MS), 8),
    CA('due_dates', 'Births due', 'int', 'COUNTIFS({range:clients.due_month},{col:month},{range:clients.birth_due},1)', 8),
    CA('scheduled_in', 'Cash from balances and instalments', 'money', 'SUMIFS({range:instalments.amount},{range:instalments.expect_on},">="&{col:month},{range:instalments.expect_on},"<"&EDATE({col:month},1))+SUMIFS({range:contracts.balance_open},{range:contracts.expect_on},">="&{col:month},{range:contracts.expect_on},"<"&EDATE({col:month},1))', 12),
    CA('new_in', 'Cash from new bookings', 'money', 'ROUND(SUMIFS({range:contracts.deposit},{range:contracts.signed_on},">="&EDATE(%s,-6),{range:contracts.signed_on},"<"&%s)/6,0)' % (MS, MS), 12),
    CA('unbooked_in', 'Cash from births not yet booked', 'money', 'ROUND(MAX(0,%s-{col:due_dates})*%s,0)' % (AVGB, BALB), 12),
    CA('expected_in', 'Expected cash in', 'money', '{col:scheduled_in}+{col:new_in}+{col:unbooked_in}', 12), CA('expected_costs', 'Expected costs', 'money', 'ROUND(%s/6,0)' % F6('costs_out'), 12), CA('fixed_costs', 'Fixed costs', 'money', 'ROUND(%s/6,0)' % F6('fixed_costs', 'pnl'), 11),
    CA('owner_pay', 'Owner pay', 'money', '{set:owner_draw}', 11), CA('set_aside', 'Set-aside', 'money', 'ROUND({set:tax_set_aside_pct}*MAX(0,{col:expected_in}-{col:expected_costs}),0)', 11),
    CA('net', 'Net cash change', 'money', '{col:expected_in}-{col:expected_costs}-{col:owner_pay}-{col:set_aside}', 12),
    CA('closing', 'Closing cash', 'money', '%s+SUMIFS({range:forecast.net},{range:forecast.month},"<="&{col:month})' % CASHNOW, 12),
    CA('cover', 'Months of cover (fixed costs and draw)', 'num', 'IF({col:fixed_costs}+{col:owner_pay}>0,{col:closing}/({col:fixed_costs}+{col:owner_pay}),0)', 9),
    CA('status', 'Cash check', 'text', 'IF({col:closing}<{set:cash_floor},%s,IF({col:closing}<{set:cash_floor}+{col:expected_costs},%s,%s))' % (tok('fchk', 'Below the floor'), tok('fchk', 'Near the floor'), tok('fchk', 'Above the floor')), 15),
    CA('below_floor', 'Below the floor', 'int', 'IF({col:closing}<{set:cash_floor},1,0)', 8),
    CA('net_best', 'Net change, best case', 'money', NETF('{set:best_factor}'), 12), CA('net_worst', 'Net change, worst case', 'money', NETF('{set:worst_factor}'), 12),
    CA('closing_best', 'Closing cash, best case', 'money', '%s+SUMIFS({range:forecast.net_best},{range:forecast.month},"<="&{col:month})' % CASHNOW, 12),
    CA('closing_worst', 'Closing cash, worst case', 'money', '%s+SUMIFS({range:forecast.net_worst},{range:forecast.month},"<="&{col:month})' % CASHNOW, 12),
    CA('closing_dn', 'Closing cash, lower draw', 'money', '{col:closing}+{col:ahead}*ROUND({set:owner_draw}*{set:draw_step},0)', 12), CA('closing_up', 'Closing cash, higher draw', 'money', '{col:closing}-{col:ahead}*ROUND({set:owner_draw}*{set:draw_step},0)', 12),
    CA('lowest_amount', 'Lowest closing cash ahead', 'money', 'SMALL({range:forecast.closing},1)', 12),
    CA('lowest_month', 'Month of the lowest cash', 'date', 'IFERROR(INDEX({range:forecast.month},MATCH(SMALL({range:forecast.closing},1),{range:forecast.closing},0)),"")', 11), OWN(), OWNN(), CO()],
    D.forecast_d(), 50, [A('status', '= ' + tok('fchk', 'Below the floor'), 'bad'), A('status', '= ' + tok('fchk', 'Near the floor'), 'warn')]))
# ---------------------------------------------------------------- 14 owner pay plan
RUN6 = 'ROUND(AVERAGEIFS({range:pnl.profit},{range:pnl.month},">="&EDATE(%s,-6),{range:pnl.month},"<"&%s),0)' % (MS, MS)
tables.append(T('ownerplan', 'Owner Pay Plan', 'Owner pay plan for the next 12 months',
    'One row per coming month: expected profit (a blend of your last 6 months and the same month last year), the set-aside, your draw and the cash left; the draw check tells you when to reduce the draw.', [
    C('month', 'Month', 'date', 11, required=True), CA('profit', 'Expected profit', 'money', 'ROUND(IF(EDATE({col:month},-12)>=%s,%s,(%s+SUMIFS({range:pnl.profit},{range:pnl.month},EDATE({col:month},-12)))/2),0)' % (MS, RUN6, RUN6), 12),
    CA('set_aside', 'Set-aside', 'money', 'ROUND({set:tax_set_aside_pct}*MAX(0,{col:profit}),0)', 11), CA('owner_draw', 'Owner draw', 'money', '{set:owner_draw}', 11),
    CA('surplus', 'Profit after set-aside and draw', 'money', '{col:profit}-{col:set_aside}-{col:owner_draw}', 12),
    CA('cash_left', 'Cash left', 'money', '%s+SUMIFS({range:ownerplan.surplus},{range:ownerplan.month},"<="&{col:month})' % CASHNOW, 12),
    CA('safe_draw', 'Draw the profit supports', 'money', 'MAX(0,{col:profit}-{col:set_aside})', 12), CA('headroom', 'Cash above the floor', 'money', '{col:cash_left}-{set:cash_floor}', 12),
    CA('can_pay', 'Draw you can afford', 'money', 'MAX(0,{col:owner_draw}+MIN(0,{col:headroom}))', 12),
    CA('plan_check', 'Draw check', 'text', 'IF({col:cash_left}<{set:cash_floor},%s,IF({col:surplus}<0,%s,%s))' % (tok('pchk', 'Reduce the draw'), tok('pchk', 'Draw uses cash'), tok('pchk', 'Draw covered by profit')), 20),
    CA('unearned', 'Unearned cash now', 'money', 'SUM({range:contracts.unearned})', 12),
    CA('timeoff_hit', 'Cash lost by the time off', 'money', 'ROUND({set:timeoff_weeks}*%s/52*{set:timeoff_stop_share}*(1-IFERROR((%s+%s+%s)/%s,0)),0)' % (T12('revenue'), T12('doula_pay'), T12('backup_pay'), T12('mileage'), T12('revenue')), 12),
    CA('cover_after', 'Months of cover after the time off', 'num', 'IFERROR(({col:cash_left}-{col:timeoff_hit})/(ROUND(%s/6,0)+{set:owner_draw}),0)' % F6('fixed_costs', 'pnl'), 10), OWN(), OWNN(), CO()], D.ownerplan_d(), 50,
    [A('plan_check', '= ' + tok('pchk', 'Reduce the draw'), 'bad'), A('plan_check', '= ' + tok('pchk', 'Draw uses cash'), 'warn')]))
# ---------------------------------------------------------------- 15 budget vs actual
tables.append(T('expvar', 'Budget vs Actual', 'Budget vs Actual by expense category and month',
    'One row per category and month: actual spending from Expenses against the monthly budget, the variance, the same month last year and the share of revenue; the ranking sheet reads these rows.', [
    LST('category', 'Category', 'expcat', 22, required=True), C('month', 'Month', 'date', 11),
    CA('amount', 'Actual', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.category},{col:category},{range:expenses.month},{col:month})', 11),
    CA('budget', 'Budget', 'money', 'IFERROR(INDEX({range:budget.monthly_budget},MATCH({col:category},{range:budget.category},0)),0)', 11), CA('variance', 'Variance', 'money', '{col:amount}-{col:budget}', 11),
    CA('over_share', 'Share over budget', 'pct', 'IF({col:budget}>0,{col:variance}/{col:budget},0)', 9),
    CA('same_ly', 'Same month last year', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.category},{col:category},{range:expenses.month},EDATE({col:month},-12))', 11),
    CA('vs_ly', 'Change on last year', 'money', '{col:amount}-{col:same_ly}', 11),
    CA('share_rev', 'Share of revenue', 'pct', 'IFERROR({col:amount}/SUMIFS({range:pnl.revenue},{range:pnl.month},{col:month}),0)', 9), CA('within', 'Within budget', 'int', 'IF({col:variance}<=0,1,0)', 8),
    CA('v_last', 'Variance, last full month', 'money', 'IF({col:month}=%s,{col:variance},"")' % LM, 11),
    CA('v_year', 'Variance, 12 months', 'money', 'IF({col:month}=%s,SUMIFS({range:expvar.variance},{range:expvar.category},{col:category}),"")' % LM, 11),
    CA('amt_year', 'Actual, 12 months', 'money', 'IF({col:month}=%s,SUMIFS({range:expvar.amount},{range:expvar.category},{col:category}),"")' % LM, 11),
    CA('cat_year_amount', 'Category actual, 12 months', 'money', 'SUMIFS({range:expvar.amount},{range:expvar.category},{col:category})', 12), CA('cat_year_budget', 'Category budget, 12 months', 'money', 'SUMIFS({range:expvar.budget},{range:expvar.category},{col:category})', 12),
    CA('cat_last_amount', 'Category actual, last full month', 'money', 'SUMIFS({range:expvar.amount},{range:expvar.category},{col:category},{range:expvar.month},%s)' % LM, 12),
    CA('cat_over_months', 'Months over budget', 'int', 'COUNTIFS({range:expvar.category},{col:category},{range:expvar.within},0)', 8), OWN(), OWNN(), ACC(), ACCN(), CO()],
    D.expvar_d(), 150, [A('variance', '> 0', 'warn')]))
# ---------------------------------------------------------------- 16 own history compare
def CMPSRC(c):
    if c.startswith('cash.'): return '{range:cash.%s}' % c[5:], '{range:cash.month}'
    if c.startswith('tax.'): return '{range:tax.%s}' % c[4:], '{range:tax.month}'
    return '{range:pnl.%s}' % c, '{range:pnl.month}'
def CH(fn): return 'CHOOSE({col:no},%s)' % ','.join(fn(*CMPSRC(c)) for m, c, d in D.CMP)
tables.append(T('compare', 'Own History Compare', 'Compare with Your Own History: last full month, 3-month average, same month last year',
    'One row per monthly figure: the last full month against the average of the 3 months before and the same month last year; a figure that moves the wrong way by more than your set share is flagged.', [
    C('measure', 'Figure', 'text', 28, required=True), C('no', 'Order', 'int', 7), C('direction', 'Good direction (1, -1 or 0)', 'int', 10),
    CA('ref_month', 'Last full month starts', 'date', LM, 11),
    CA('last_month', 'Last full month', 'num', CH(lambda s, m: 'SUMIFS(%s,%s,{col:ref_month})' % (s, m)), 12),
    CA('avg3', 'Average of the 3 months before', 'num', CH(lambda s, m: 'IFERROR(AVERAGEIFS(%s,%s,">="&EDATE({col:ref_month},-3),%s,"<"&{col:ref_month}),0)' % (s, m, m)), 12),
    CA('ly', 'Same month last year', 'num', CH(lambda s, m: 'SUMIFS(%s,%s,EDATE({col:ref_month},-12))' % (s, m)), 12),
    CA('change', 'Change on 3-month average', 'pct', 'IF({col:avg3}<>0,{col:last_month}/{col:avg3}-1,0)', 9), CA('change_ly', 'Change on last year', 'pct', 'IF({col:ly}<>0,{col:last_month}/{col:ly}-1,0)', 9),
    CA('score', 'Score (change in the good direction)', 'pct', '{col:change}*{col:direction}', 9),
    CA('flag', 'Check', 'text', 'IF({col:direction}=0,%s,IF({col:score}<-{set:drop_flag_pct},%s,IF({col:score}>{set:drop_flag_pct},%s,%s)))' % (TRD['Within range'], TRD['Dropped'], TRD['Improved'], TRD['Within range']), 14), OWN(), OWNN(), CO()],
    D.compare_d(), 60, [A('flag', '= ' + TRD['Dropped'], 'bad'), A('flag', '= ' + TRD['Improved'], 'good')]))
# ---------------------------------------------------------------- 17 renewal calendar
def RCL(c): return 'IFERROR(INDEX({range:renewals.%s},MATCH({col:renewal_id},{range:renewals.renewal_id},0)),"")' % c
tables.append(T('renewcal', 'Renewal Calendar', 'Renewal calendar: the next renewals in date order',
    'One row per coming renewal: holder, item, due date, days left, red amber green status and cost, read from Renewals; the owner, admin and insurer phones are ready for the messages.', [
    REF('renewal_id', 'Renewal', 'renewals.renewal_id', 10, required=True), CA('holder', 'Holder', 'text', RCL('holder') + '&""', 22), CA('item', 'Item', 'text', RCL('item') + '&""', 22), CA('due_date', 'Due date', 'date', RCL('due_date'), 11),
    CA('days_left', 'Days left', 'int', RCL('days_left'), 8), CA('status', 'Status', 'text', RCL('status') + '&""', 11), CA('cost', 'Cost', 'money', RCL('cost'), 11),
    CA('red_total', 'Red renewals now', 'int', 'SUM({range:renewals.is_red})', 8), CA('soon_total', 'Red and amber renewals now', 'int', 'SUM({range:renewals.is_red})+SUM({range:renewals.is_amber})', 8),
    CA('phone', 'Holder phone', 'text', RCL('phone') + '&""', 18), OWN(), OWNN(), ADM(), ADMN(), CA('insurer_phone', 'Insurer phone', 'text', '"%s"' % D.INSURER_PHONE, 18), CA('insurer_name', 'Insurer name', 'text', 'IFERROR(INDEX({range:team.name},MATCH(%s,{range:team.role},0))&"","")' % tok('role', 'Insurer'), 22), CO()],
    D.renewcal_d(), 60, [A('status', '= ' + RAGT['Red'], 'bad'), A('status', '= ' + RAGT['Amber'], 'warn')]))
# ---------------------------------------------------------------- 18 cpd hours by holder
tables.append(T('cpd', 'Training Hours by Holder', 'Training hours by holder against the yearly target',
    'One row per doula and backup doula: training hours of the last 12 months and the gap to the target in Settings.', [
    REF('holder', 'Holder', 'team.name', 24, required=True), CA('hours_12', 'Hours, last 12 months', 'num', 'SUMIFS({range:training.hours},{range:training.holder},{col:holder},{range:training.date},">"&EDATE({today},-12),{range:training.date},"<="&{today})', 12),
    CA('gap', 'Hours short of the target', 'num', 'MAX(0,{set:cpd_target_hours}-{col:hours_12})', 12)], D.cpd_d(), 50))
# ---------------------------------------------------------------- 19 year in review
def YRX(c, lo, hi):
    if c == 'margin': return 'IFERROR(SUMIFS({range:pnl.profit},{range:pnl.month},">"&%s,{range:pnl.month},"<="&%s)/SUMIFS({range:pnl.revenue},{range:pnl.month},">"&%s,{range:pnl.month},"<="&%s),0)' % (lo, hi, lo, hi)
    if c in ('rpb', 'ppb'):
        n = 'revenue' if c == 'rpb' else 'profit'
        return 'IFERROR(SUMIFS({range:pnl.%s},{range:pnl.month},">"&%s,{range:pnl.month},"<="&%s)/SUMIFS({range:pnl.births},{range:pnl.month},">"&%s,{range:pnl.month},"<="&%s),0)' % (n, lo, hi, lo, hi)
    t, col = c.split('.'); m = 'date' if False else 'month'
    return 'SUMIFS({range:%s.%s},{range:%s.%s},">"&%s,{range:%s.%s},"<="&%s)' % (t, col, t, m, lo, t, m, hi)
THIS = ('EDATE(%s,-12)' % MS, MS); LAST = ('EDATE(%s,-24)' % MS, 'EDATE(%s,-12)' % MS)
tables.append(T('yearrev', 'Year in Review', 'Year in Review: the last 12 months against the 12 months before',
    'One row per yearly figure: the last 12 months (this month so far included) against the 12 months before, the change and a verdict; the year-end summary and the next-year plan read these rows.', [
    C('measure', 'Figure', 'text', 26, required=True), C('no', 'Order', 'int', 7), C('direction', 'Good direction (1, -1 or 0)', 'int', 10),
    CA('this_year', 'Last 12 months', 'num', 'CHOOSE({col:no},%s)' % ','.join(YRX(c, *THIS) for m, c, d in D.YR), 13),
    CA('last_year', 'The 12 months before', 'num', 'CHOOSE({col:no},%s)' % ','.join(YRX(c, *LAST) for m, c, d in D.YR), 13),
    CA('change', 'Change', 'pct', 'IF({col:last_year}<>0,{col:this_year}/{col:last_year}-1,0)', 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:direction}=0,%s,IF({col:direction}*{col:change}>{set:drop_flag_pct},%s,IF({col:direction}*{col:change}<-{set:drop_flag_pct},%s,%s)))' % (TRD['Within range'], TRD['Improved'], TRD['Dropped'], TRD['Within range']), 14),
    CA('stream', 'Income stream, last 12 months', 'num', 'IF(AND({col:no}>=2,{col:no}<=5),{col:this_year},"")', 12),
    CA('rev_12', 'Revenue, last 12 months', 'money', T12('revenue'), 12), CA('profit_12', 'Profit, last 12 months', 'money', T12('profit'), 12), CA('births_12', 'Births, last 12 months', 'int', T12('births'), 9),
    OWN(), OWNN(), ACC(), ACCN(), CO()], D.yearrev_d(), 50, [A('verdict', '= ' + TRD['Dropped'], 'bad'), A('verdict', '= ' + TRD['Improved'], 'good')]))
# ---------------------------------------------------------------- 20 year plan
CURB = 'ROUND(%s/12,1)' % T12('births')
RPB = 'IFERROR(%s/%s,0)' % (T12('revenue'), T12('births'))
VARB = 'IFERROR((%s+%s+%s)/%s,0)' % (T12('doula_pay'), T12('backup_pay'), T12('mileage'), T12('births'))
FIXED = '(%s+%s)' % (T12('admin_pay'), T12('other_costs'))
tables.append(T('yearplan', 'Year Plan', 'Year Plan: income and profit with more or fewer births a month',
    'One row per scenario: births a month moved up or down from your last 12 months, priced at your own revenue and cost per birth; the income, profit, profit after your draw and the gap to your target fill in.', [
    C('scenario', 'Scenario', 'text', 26, required=True), C('delta', 'Births a month, change', 'int', 9),
    CA('births_month', 'Births a month', 'num', 'MAX(0,%s+{col:delta})' % CURB, 9), CA('income', 'Income for the year', 'money', 'ROUND({col:births_month}*12*%s,0)' % RPB, 13),
    CA('costs', 'Costs for the year', 'money', 'ROUND({col:births_month}*12*%s+%s,0)' % (VARB, FIXED), 13), CA('profit', 'Profit for the year', 'money', '{col:income}-{col:costs}', 13),
    CA('after_pay', 'Profit after your draw', 'money', '{col:profit}-12*{set:owner_draw}', 13), CA('gap_target', 'Income against your target', 'money', '{col:income}-{set:income_target}', 13),
    CA('need_births', 'Births a month to reach the target', 'num', 'IFERROR(ROUNDUP({set:income_target}/(12*%s),1),0)' % RPB, 10), OWN(), OWNN(), CO()], D.yearplan_d(), 50,
    [A('gap_target', '< 0', 'warn'), A('after_pay', '< 0', 'bad')]))
assert len(tables) == 20, len(tables)
