"""Author and self-publisher suite part 8: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au8_lists import *
import au8_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def BYROLE(role): return 'IFERROR(INDEX({range:team.phone},MATCH(%s,{range:team.role},0))&"","")' % tok('role', role)
def NAMEROLE(role): return 'IFERROR(INDEX({range:team.name},MATCH(%s,{range:team.role},0))&"","")' % tok('role', role)
def PH(prefix, role, label): return CA(prefix + '_phone', label + ' phone', 'text', BYROLE(role), 18)
def NM(prefix, role, label): return CA(prefix + '_name', label + ' name', 'text', NAMEROLE(role), 20)
def ACCT(): return [NM('acct', 'Accountant', 'Accountant'), PH('acct', 'Accountant', 'Accountant')]
def VA(): return [NM('va', 'Virtual assistant', 'Assistant'), PH('va', 'Virtual assistant', 'Assistant')]
def AUTH(): return [NM('author', 'Author-publisher', 'Author'), PH('author', 'Author-publisher', 'Author')]
def COMPANY_(): return CA('company', 'Imprint', 'text', '{set:company}', 20)

MS = 'DATE(YEAR({today}),MONTH({today}),1)'
LM = 'EDATE(%s,-1)' % MS
def WIN(rng, n): return '%s,">="&EDATE(%s,-%d),%s,"<"&%s' % (rng, MS, n, rng, MS)      # the n complete months before this month
def W12(t, c='month'): return WIN('{range:%s.%s}' % (t, c), 12)
def SUM12(t, col, dc='month'): return 'SUMIFS({range:%s.%s},%s)' % (t, col, W12(t, dc))
def SUMN(t, col, n, dc='month'): return 'SUMIFS({range:%s.%s},%s)' % (t, col, WIN('{range:%s.%s}' % (t, dc), n))
CASHNOW = 'INDEX({range:cash.closing},MATCH(%s,{range:cash.month},0))' % MS
PAID = tok('cpaystatus', 'Paid'); EXPD = tok('ststatus', 'Expected'); OPEN = tok('ststatus', 'Open'); SHORT = tok('ststatus', 'Short-paid'); SPAID = tok('ststatus', 'Paid')
NOTPAID = '"<>"&' + PAID
SCA = 'INDEX({range:scenarios.sales_change},MATCH({set:scenario},{range:scenarios.scenario},0))'
SCB = 'INDEX({range:scenarios.cost_change},MATCH({set:scenario},{range:scenarios.scenario},0))'
def SCN(name, col): return 'INDEX({range:scenarios.%s},MATCH(%s,{range:scenarios.scenario},0))' % (col, tok('scen', name))
POT_NOW = 'INDEX({range:taxmonth.pot_balance},MATCH(%s,{range:taxmonth.month},0))' % MS
AVGCOST12 = '(%s/12)' % SUM12('pnl', 'costs')
DUE_IN = lambda d: 'SUMIFS({range:jobpay.amount},{range:jobpay.status},%s,{range:jobpay.date},"<="&({today}+%s))' % (NOTPAID, d)
UNPAID_STM_BY = lambda cutoff: ('(SUMIFS({range:statements.statement_amount},{range:statements.status},%s,{range:statements.expected_on},"<"&%s)+SUMIFS({range:statements.statement_amount},{range:statements.status},%s,{range:statements.expected_on},"<"&%s))' % (EXPD, cutoff, OPEN, cutoff))
STMT_RECV = lambda d: ('(SUMIFS({range:statements.statement_amount},{range:statements.status},%s,{range:statements.expected_on},"<="&({today}+%s))+SUMIFS({range:statements.statement_amount},{range:statements.status},%s,{range:statements.expected_on},"<="&({today}+%s)))' % (EXPD, d, OPEN, d))

settings = [
    S('company', 'Your imprint name', 'text', COMPANY),
    S('cash_floor', 'Lowest cash balance you want (your own number)', 'money', CASH_FLOOR),
    S('cash_cover_months', 'Months of costs your cash should cover (your own number)', 'int', CASH_COVER_MONTHS),
    S('tax_set_aside_pct', 'Tax set-aside percent (confirm with your adviser)', 'pct', TAX_SET_ASIDE_PCT),
    S('owner_draw_plan', 'Owner draw you plan each month', 'money', DRAW_PLAN),
    S('new_jobs_plan', 'New freelancer jobs you plan each month', 'money', 900),
    S('ad_budget', 'Ad budget you plan each month', 'money', 650),
    S('scenario', 'Scenario the forecast uses', 'list', key('scen', 'Base'), list='scen'),
    S('trend_factor', 'Trend factor of earnings (1.00 = level, your own number)', 'num', 1.0),
    S('next_tax_on', 'Date of your next tax payment (ask your tax adviser)', 'date', iso(add_months(month_start(0), 2).replace(day=15))),
    S('next_tax_amount', 'Amount of your next tax payment (ask your tax adviser)', 'money', 6300),
    S('margin_target', 'Profit margin you want (your own number)', 'pct', 0.50),
    S('ad_share_limit', 'Highest share of revenue you spend on ads (your own number)', 'pct', 0.08),
    S('store_dep_limit', 'Highest share of royalties from one store (your own number)', 'pct', STORE_DEPENDENCE_LIMIT),
    S('readthrough_warn_1', 'Read-through you want, book 1 to book 2 (your own number)', 'pct', READTHROUGH_WARN_1),
    S('readthrough_warn', 'Read-through you want, later books (your own number)', 'pct', READTHROUGH_WARN),
    S('ad_return_target', 'Ad return you want (1.00 is break-even)', 'num', AD_RETURN_TARGET),
    S('titles_be_limit', 'Titles you accept under break-even', 'int', 1),
    S('over_limit', 'Categories over budget that you accept in a month', 'int', 2),
    S('fee_flag_pct', 'Flag a payment with fees above this share', 'pct', FEE_FLAG_PCT),
]
assert 3 <= len(settings) <= 20

tables = []
# ---------------------------------------------------------------- 1 team
tables.append(T('team', 'Team', 'The author, assistant, freelancers and service providers',
    'One row per person you work with: role, pay type, phone and the usual rate; a freelancer is paid per job, the assistant by the hour, and these phones feed the message links.', [
    C('person_id', 'Person ID', 'text', 10, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 18), LST('team', 'Team', 'team', 15), LST('pay_type', 'Pay type', 'paytype', 12), C('phone', 'Phone', 'text', 18),
    C('email', 'E-mail', 'text', 26), C('rate', 'Usual rate', 'money', 11), C('rate_unit', 'Rate unit', 'text', 20), C('country', 'Country', 'text', 14), C('since', 'Working together since', 'date', 12)],
    D.team_d(), 50))
# ---------------------------------------------------------------- 2 stores
tables.append(T('stores', 'Stores', 'Stores with royalty share and payment delay',
    'One row per store: the typical royalty share (check each store\'s current terms) and the days a store takes to pay after month end; the receipts forecast reads these delays.', [
    LST('store', 'Store', 'store', 22, required=True), C('royalty_share', 'Royalty share', 'pct', 12), C('delay_days', 'Payment delay (days)', 'int', 14)],
    D.stores_d(), 50))
# ---------------------------------------------------------------- 3 statements
tables.append(T('statements', 'Statements', 'Store statements with expected and paid dates',
    'One row per store statement (what a store says it owes you for a month): amount, dates and what arrived; the gap, days overdue and a check fill in by themselves.', [
    C('statement_id', 'Statement ID', 'text', 11, required=True), C('month', 'Month', 'date', 11), LST('store', 'Store', 'store', 20), C('statement_amount', 'Statement amount', 'money', 13), C('expected_on', 'Expected on', 'date', 12),
    C('paid_on', 'Paid on', 'date', 11), C('received', 'Received', 'money', 12), LST('status', 'Status', 'ststatus', 12),
    CA('gap', 'Gap (statement minus received)', 'money', 'IF({col:paid_on}>0,{col:statement_amount}-{col:received},0)', 12),
    CA('days_overdue', 'Days overdue', 'int', 'IF(OR({col:status}=%s,{col:status}=%s),MAX(0,{today}-{col:expected_on}),0)' % (EXPD, OPEN), 9),
    CA('check', 'Statement check', 'text', 'IF({col:status}=%s,%s,IF({col:status}=%s,%s,IF({col:expected_on}<{today},%s,IF({col:expected_on}-{today}<=30,%s,%s))))' % (
        SHORT, vt('Short-paid'), SPAID, vt('Paid in full'), vt('Overdue'), vt('Due soon'), vt('Expected later')), 16), *ACCT(), COMPANY_()],
    D.statements_d(), 300, [A('check', '= ' + vt('Short-paid'), 'bad'), A('check', '= ' + vt('Overdue'), 'bad'), A('check', '= ' + vt('Due soon'), 'warn'), A('check', '= ' + vt('Paid in full'), 'good')]))
# ---------------------------------------------------------------- 4 payments received
tables.append(T('payments', 'Payments Received', 'Payments received with fees and exchange loss',
    'One row per payment that reached your bank: the statement it pays, the fee and the exchange loss; the loss, its share of the statement and a flag against your own limit fill in by themselves.', [
    C('payment_id', 'Payment ID', 'text', 11, required=True), REF('statement_id', 'Statement ID', 'statements.statement_id', 11), LST('store', 'Store', 'store', 20), C('month', 'Month', 'date', 11), C('received_on', 'Received on', 'date', 11),
    C('statement_amount', 'Statement amount', 'money', 13), C('fee', 'Fee', 'money', 9), C('fx_loss', 'Exchange loss', 'money', 11), C('received', 'Received', 'money', 12),
    CA('loss', 'Total loss', 'money', '{col:statement_amount}-{col:received}', 10), CA('loss_pct', 'Loss share', 'pct', 'IF({col:statement_amount}>0,{col:loss}/{col:statement_amount},0)', 9),
    CA('check', 'Fee check', 'text', 'IF({col:loss_pct}>{set:fee_flag_pct},%s,%s)' % (vt('Fee flag'), vt('Fee normal')), 12), *ACCT(), COMPANY_()],
    D.payments_d(), 300, [A('check', '= ' + vt('Fee flag'), 'warn'), A('loss_pct', '> {set:fee_flag_pct}', 'warn')]))
# ---------------------------------------------------------------- 5 job payments
tables.append(T('jobpay', 'Job Payments', 'Payments to freelancers and service providers',
    'One row per payment to a contractor (deposit, milestone or final): amount, date and status; days to due, the payment check and the order of the open payments fill in by themselves.', [
    C('cpay_id', 'Payment ID', 'text', 10, required=True), C('job_id', 'Job ID', 'text', 9), C('title_id', 'Title ID', 'text', 9), C('title', 'Title', 'text', 26), REF('contractor', 'Contractor', 'team.name', 20), LST('stage', 'Stage', 'stage', 10),
    C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), C('amount', 'Amount', 'money', 11), LST('status', 'Status', 'cpaystatus', 11), C('move_days', 'Days to move it', 'int', 9),
    CA('days_to_due', 'Days to due', 'int', 'IF({col:status}<>%s,{col:date}-{today},"")' % PAID, 9),
    CA('new_date', 'New payment date', 'date', 'IF({col:move_days}>0,{col:date}+{col:move_days},"")', 12),
    CA('check', 'Payment check', 'text', 'IF({col:status}=%s,%s,IF({col:date}<{today},%s,IF({col:date}-{today}<=7,%s,%s)))' % (PAID, vt('Paid in full'), vt('Overdue'), vt('Due soon'), vt('Expected later')), 16),
    CA('open_key', 'Open order key', 'num', 'IF({col:status}<>%s,{col:date}+VALUE(RIGHT({col:cpay_id},4))/10000,99999)' % PAID, 11),
    CA('role', 'Contractor role', 'text', LKT('team.role', 'team.name', 'contractor'), 16), CA('phone', 'Contractor phone', 'text', LKT('team.phone', 'team.name', 'contractor'), 18), COMPANY_()],
    D.jobpay_d(), 400, [A('check', '= ' + vt('Overdue'), 'bad'), A('check', '= ' + vt('Due soon'), 'warn'), A('check', '= ' + vt('Paid in full'), 'good')]))
# ---------------------------------------------------------------- 6 expenses
tables.append(T('expenses', 'Expenses', 'Expense log with category, vendor and receipt',
    'One row per expense: date, category, vendor, amount, pen name and whether the receipt is on file; the 12-month cost of the vendor and the receipt check fill in by themselves.', [
    C('expense_id', 'Expense ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), LST('category', 'Category', 'expcat', 20), C('vendor', 'Vendor', 'text', 26), C('amount', 'Amount', 'money', 11),
    LST('pen_name', 'Pen name', 'expen', 16), C('receipt', 'Receipt on file', 'bool', 9),
    CA('vendor_12m', 'Vendor cost, last 12 months', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.vendor},{col:vendor},{range:expenses.date},">"&({today}-365))', 13),
    CA('vendor_bills', 'Bills from the vendor, 12 months', 'int', 'COUNTIFS({range:expenses.vendor},{col:vendor},{range:expenses.date},">"&({today}-365))', 11),
    CA('receipt_check', 'Receipt check', 'text', 'IF({col:receipt}={list:yesno.yes},%s,%s)' % (vt('Receipt on file'), vt('Add the receipt')), 15),
    *VA(), *ACCT(), NM('webdev', 'Web developer', 'Web developer'), PH('webdev', 'Web developer', 'Web developer'), COMPANY_()],
    D.expenses_d(), 800, [A('receipt_check', '= ' + vt('Add the receipt'), 'warn')]))
# ---------------------------------------------------------------- 7 cost categories
tables.append(T('costcat', 'Cost Categories', 'Expense categories with your own monthly budget',
    'One row per expense category with your own monthly budget (a number you choose); the expense checks compare each month with it.', [
    LST('category', 'Category', 'expcat', 22, required=True), C('monthly_budget', 'Monthly budget', 'money', 13), C('note', 'What it covers', 'text', 36)],
    D.costcat_d(), 50))
# ---------------------------------------------------------------- 8 profit and loss
tables.append(T('pnl', 'Profit and Loss by Month', 'Profit and loss statement by month',
    'One row per month: type the income and cost lines; revenue, costs, profit, margin and the rolling 12-month totals fill in by themselves.', [
    C('month', 'Month', 'date', 11, required=True), C('royalties', 'Royalties', 'money', 11), C('page_reads', 'Page reads', 'money', 11), C('direct_net', 'Direct store net', 'money', 12), C('event_sales', 'Event sales', 'money', 11),
    C('rights', 'Rights', 'money', 10), C('ads', 'Ads', 'money', 10), C('production', 'Production', 'money', 11), C('expenses', 'Expenses', 'money', 11), C('event_costs', 'Event costs', 'money', 11),
    CA('revenue', 'Revenue', 'money', '{col:royalties}+{col:page_reads}+{col:direct_net}+{col:event_sales}+{col:rights}', 12),
    CA('costs', 'Costs', 'money', '{col:ads}+{col:production}+{col:expenses}+{col:event_costs}', 11), CA('profit', 'Profit', 'money', '{col:revenue}-{col:costs}', 11),
    CA('margin', 'Profit margin', 'pct', 'IF({col:revenue}>0,{col:profit}/{col:revenue},0)', 9),
    CA('revenue_12m', 'Revenue, 12 months to here', 'money', 'SUMIFS({range:pnl.revenue},{range:pnl.month},">"&EDATE({col:month},-12),{range:pnl.month},"<="&{col:month})', 13),
    CA('costs_12m', 'Costs, 12 months to here', 'money', 'SUMIFS({range:pnl.costs},{range:pnl.month},">"&EDATE({col:month},-12),{range:pnl.month},"<="&{col:month})', 13),
    CA('profit_12m', 'Profit, 12 months to here', 'money', '{col:revenue_12m}-{col:costs_12m}', 13),
    CA('setaside_12m', 'Set-aside, 12 months to here', 'money', 'SUMIFS({range:taxmonth.set_aside},{range:taxmonth.month},">"&EDATE({col:month},-12),{range:taxmonth.month},"<="&{col:month})', 13),
    CA('draws_12m', 'Owner draws, 12 months to here', 'money', 'SUMIFS({range:cash.owner_draw},{range:cash.month},">"&EDATE({col:month},-12),{range:cash.month},"<="&{col:month})', 13),
    CA('expense_count', 'Expense lines this month', 'int', 'COUNTIFS({range:expenses.month},{col:month})', 9),
    CA('expense_sum', 'Expenses logged this month', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.month},{col:month})', 12),
    CA('missing_receipts', 'Receipts missing this month', 'int', 'COUNTIFS({range:expenses.month},{col:month},{range:expenses.receipt},{list:yesno.no})', 10),
    CA('actions_text', 'Your three actions', 'text', 'INDEX({range:health.actions_text},1)', 40), *ACCT(), CA('rights_name', 'Rights agent name', 'text', NAMEROLE('Rights agent'), 20), PH('rights', 'Rights agent', 'Rights agent'), COMPANY_()],
    D.pnl_d(), 60, [A('profit', '< 0', 'bad'), A('margin', '< {set:margin_target}', 'warn')]))
# ---------------------------------------------------------------- 9 cash by month
tables.append(T('cash', 'Cash by Month', 'Cash by month with receipts and payments out',
    'One row per month: opening cash, the money received and paid out; closing cash, months of cover and a floor check fill in by themselves.', [
    C('month', 'Month', 'date', 11, required=True), C('opening', 'Opening cash', 'money', 12), C('receipts', 'Receipts', 'money', 11), C('ads', 'Ads', 'money', 10), C('production', 'Production', 'money', 11), C('expenses', 'Expenses', 'money', 11),
    C('event_costs', 'Event costs', 'money', 11), C('author_copies', 'Author copies', 'money', 11), C('tax_set_aside', 'Tax set-aside', 'money', 11), C('owner_draw', 'Owner draw', 'money', 11),
    CA('closing', 'Closing cash', 'money', '{col:opening}+{col:receipts}-{col:ads}-{col:production}-{col:expenses}-{col:event_costs}-{col:author_copies}-{col:tax_set_aside}-{col:owner_draw}', 12),
    CA('net_flow', 'Net flow', 'money', '{col:closing}-{col:opening}', 11),
    CA('cover_months', 'Months of cover', 'num', 'IFERROR({col:closing}/INDEX({range:pnl.costs},MATCH({col:month},{range:pnl.month},0)),0)', 9),
    CA('low_flag', 'Floor check', 'text', 'IF({col:closing}<{set:cash_floor},%s,%s)' % (vc('Below the floor'), vc('Above the floor')), 14),
    *VA(), NM('printer', 'Printer', 'Printer'), PH('printer', 'Printer', 'Printer'), NM('events', 'Event organiser', 'Event organiser'), PH('events', 'Event organiser', 'Event organiser'), *AUTH(), COMPANY_()],
    D.cash_d(), 60, [A('low_flag', '= ' + vc('Below the floor'), 'warn'), A('low_flag', '= ' + vc('Above the floor'), 'good')]))
# ---------------------------------------------------------------- 10 tax set-aside by month
tables.append(T('taxmonth', 'Tax Set-aside by Month', 'Tax set-aside, payments and pot balance by month',
    'One row per month: the percent you set aside (confirm with your adviser), the amount moved to the pot and the tax paid; the pot balance and the shortfall fill in.', [
    C('month', 'Month', 'date', 11, required=True), C('set_aside_pct', 'Set-aside percent', 'pct', 11), C('set_aside', 'Set aside', 'money', 11), C('tax_paid', 'Tax paid', 'money', 11),
    CA('profit_month', 'Profit of the month', 'money', 'IFERROR(INDEX({range:pnl.profit},MATCH({col:month},{range:pnl.month},0)),0)', 12),
    CA('pot_balance', 'Pot balance', 'money', 'SUMIFS({range:taxmonth.set_aside},{range:taxmonth.month},"<="&{col:month})-SUMIFS({range:taxmonth.tax_paid},{range:taxmonth.month},"<="&{col:month})', 12),
    CA('target_amount', 'Set-aside at your percent', 'money', 'MAX(0,{col:profit_month})*{col:set_aside_pct}', 12),
    CA('on_target', 'At your percent (1 = yes)', 'int', 'IF({col:set_aside}>={col:target_amount}*0.9,1,0)', 9),
    CA('next_payment_on', 'Next tax payment on', 'date', '{set:next_tax_on}', 12), CA('next_payment', 'Next tax payment', 'money', '{set:next_tax_amount}', 12),
    CA('short_by', 'Pot short by', 'money', 'MAX(0,{col:next_payment}-{col:pot_balance})', 11), *ACCT(), *AUTH(), COMPANY_()],
    D.tax_d(), 60, [A('short_by', '> 0', 'warn'), A('on_target', '= 0', 'warn')]))
# ---------------------------------------------------------------- 11 expenses by category and month
tables.append(T('expmonth', 'Expenses by Category and Month', 'Expenses by category and month against your budget',
    'One row per category and month (the last 12 months): the amount logged, your own budget, the difference and a verdict; near the budget means 90 to 100 percent of it.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('category', 'Category', 'expcat', 20),
    CA('amount', 'Amount', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.category},{col:category},{range:expenses.month},{col:month})', 11),
    CA('budget', 'Budget', 'money', LKN('costcat.monthly_budget', 'costcat.category', 'category'), 10),
    CA('difference', 'Over (+) or under (-)', 'money', '{col:amount}-{col:budget}', 11), CA('used', 'Share of budget used', 'pct', 'IF({col:budget}>0,{col:amount}/{col:budget},0)', 10),
    CA('over_pct', 'Percent above budget', 'pct', 'MAX(0,{col:used}-1)', 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:amount}>{col:budget},%s,IF({col:amount}>={col:budget}*0.9,%s,%s))' % (vt('Over budget'), vt('Near the budget'), vt('Within budget')), 15),
    CA('rank_last', 'Rank last month', 'int', 'IF({col:month}=%s,COUNTIFS({range:expmonth.month},{col:month},{range:expmonth.difference},">"&{col:difference})+1,"")' % LM, 9),
    CA('cat_12m', 'Category, last 12 months', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.category},{col:category},{range:expenses.month},">="&EDATE(%s,-12),{range:expenses.month},"<"&%s)' % (MS, MS), 13),
    CA('cat_avg', 'Category monthly average', 'money', '{col:cat_12m}/12', 12), *AUTH(), COMPANY_()],
    D.expmonth_d(), 200, [A('verdict', '= ' + vt('Over budget'), 'bad'), A('verdict', '= ' + vt('Near the budget'), 'warn'), A('verdict', '= ' + vt('Within budget'), 'good')]))
# ---------------------------------------------------------------- 12 cash forecast
FM = '{range:forecast.month}'
START = '{col:start_cash}'
def NET_S(name):
    a, b = SCN(name, 'sales_change'), SCN(name, 'cost_change')
    P_ = '({col:base_receipts}*(1+%s)-{col:known}-({col:plan}+{col:ads_base}+{col:exp_base})*(1+%s))' % (a, b)
    return '%s-MAX(0,%s)*{set:tax_set_aside_pct}-{set:owner_draw_plan}' % (P_, P_)
def CLOSE_S(name): return '%s+SUMIFS({range:forecast.net_%s},%s,"<="&{col:month})' % (START, name.lower(), FM)
def MIN12(f): return 'MIN(' + ','.join(f(k) for k in range(1, 13)) + ')'
tables.append(T('forecast', 'Cash Forecast', 'Cash flow forecast for the next 12 months',
    'One row per future month for the scenario on Start: receipts, payments, set-aside and draw; opening and closing cash, a low-cash flag and the three scenario closings fill in.', [
    C('month', 'Month', 'date', 11, required=True), LST('fmon', 'Forecast month', 'fmon', 10),
    CA('start_cash', 'Cash at the start of the forecast', 'money', '%s+%s-SUMIFS({range:jobpay.amount},{range:jobpay.status},%s,{range:jobpay.date},"<"&MIN(%s))' % (CASHNOW, UNPAID_STM_BY('MIN(%s)' % FM), NOTPAID, FM), 13),
    CA('sales_change', 'Sales change of the scenario', 'pct', SCA, 9), CA('cost_change', 'Cost change of the scenario', 'pct', SCB, 9),
    CA('base_receipts', 'Expected receipts, before the scenario', 'money', 'IFERROR(INDEX({range:receipts.expected},MATCH({col:month},{range:receipts.month},0)),0)', 13),
    CA('known', 'Known contractor payments', 'money', 'SUMIFS({range:jobpay.amount},{range:jobpay.month},{col:month},{range:jobpay.status},%s)' % NOTPAID, 12),
    CA('plan', 'New jobs you plan', 'money', '{set:new_jobs_plan}', 11), CA('ads_base', 'Ad budget, before the scenario', 'money', '{set:ad_budget}', 11),
    CA('exp_base', 'Usual expenses, before the scenario', 'money', '(%s+%s+%s)/6' % (SUMN('cash', 'expenses', 6), SUMN('cash', 'event_costs', 6), SUMN('cash', 'author_copies', 6)), 12),
    CA('receipts', 'Expected receipts', 'money', '{col:base_receipts}*(1+{col:sales_change})', 12),
    CA('contractors', 'Contractor payments', 'money', '{col:known}+{col:plan}*(1+{col:cost_change})', 12), CA('ads', 'Ad budget', 'money', '{col:ads_base}*(1+{col:cost_change})', 10),
    CA('expenses', 'Expenses', 'money', '{col:exp_base}*(1+{col:cost_change})', 11),
    CA('tax_set_aside', 'Tax set-aside', 'money', 'MAX(0,{col:receipts}-{col:contractors}-{col:ads}-{col:expenses})*{set:tax_set_aside_pct}', 11),
    CA('owner_draw', 'Owner draw', 'money', '{set:owner_draw_plan}', 11),
    CA('net', 'Net flow', 'money', '{col:receipts}-{col:contractors}-{col:ads}-{col:expenses}-{col:tax_set_aside}-{col:owner_draw}', 11),
    CA('month_no', 'Month number', 'int', 'COUNTIFS(%s,"<="&{col:month})' % FM, 8),
    CA('opening', 'Opening cash', 'money', '%s+SUMIFS({range:forecast.net},%s,"<"&{col:month})' % (START, FM), 12), CA('closing', 'Closing cash', 'money', '{col:opening}+{col:net}', 12),
    CA('flag', 'Low-cash flag', 'text', 'IF({col:closing}<{set:cash_floor},%s,%s)' % (vc('Low-cash month'), vc('Cash holds')), 14),
    CA('net_base', 'Net flow, Base', 'money', NET_S('Base'), 11), CA('net_best', 'Net flow, Best', 'money', NET_S('Best'), 11), CA('net_worst', 'Net flow, Worst', 'money', NET_S('Worst'), 11),
    CA('close_base', 'Closing cash, Base', 'money', CLOSE_S('Base'), 12), CA('close_best', 'Closing cash, Best', 'money', CLOSE_S('Best'), 12), CA('close_worst', 'Closing cash, Worst (sales minus 20%)', 'money', CLOSE_S('Worst'), 13),
    CA('max_draw', 'Largest steady draw that holds the floor', 'money', '{set:owner_draw_plan}+' + MIN12(lambda k: '(INDEX({range:forecast.closing},%d)-{set:cash_floor})/%d' % (k, k)), 14),
    CA('floor', 'Cash floor', 'money', '{set:cash_floor}', 10), *VA(), NM('ad', 'Ad specialist', 'Ad specialist'), PH('ad', 'Ad specialist', 'Ad specialist'), NM('coord', 'Launch coordinator', 'Launch coordinator'), PH('coord', 'Launch coordinator', 'Launch coordinator'), *AUTH(), COMPANY_()],
    D.forecast_d(), 50, [A('flag', '= ' + vc('Low-cash month'), 'bad'), A('flag', '= ' + vc('Cash holds'), 'good')]))
# ---------------------------------------------------------------- 13 receipts by pay month
RR_ALL = '(SUMIFS({range:statements.statement_amount},%s)/6)' % WIN('{range:statements.month}', 6)
LAG = '(INT({range:stores.delay_days}/30.5)+1)'
MARR = 'DATE(YEAR({col:month}),MONTH({col:month})-%s,1)' % LAG
EXPECTED = ('SUMPRODUCT((%s<%s)*SUMIFS({range:statements.statement_amount},{range:statements.store},{range:stores.store},{range:statements.month},%s)'
            '+(%s>=%s)*SUMIFS({range:statements.statement_amount},{range:statements.store},{range:stores.store},%s)/6*{set:trend_factor})') % (
    MARR, MS, MARR, MARR, MS, WIN('{range:statements.month}', 6))
tables.append(T('receipts', 'Receipts by Pay Month', 'Expected royalties by pay month from the store delays',
    'One row per future month: what your statements earn and what arrives once each store delay is added (from Stores), against what you pay out; estimates until paid.', [
    C('month', 'Pay month', 'date', 11, required=True), LST('fmon', 'Forecast month', 'fmon', 10),
    CA('earned_est', 'Earned in the month (estimate)', 'money', 'IF({col:month}<%s,SUMIFS({range:statements.statement_amount},{range:statements.month},{col:month}),%s*{set:trend_factor})' % (MS, RR_ALL), 13),
    CA('expected', 'Expected in the month by store delay', 'money', EXPECTED, 14), CA('difference', 'Difference (expected minus earned)', 'money', '{col:expected}-{col:earned_est}', 13),
    CA('diff_pct', 'Difference share', 'pct', 'IF({col:earned_est}>0,{col:difference}/{col:earned_est},0)', 9),
    CA('needed', 'Paid out in a usual month', 'money', '%s/6+{set:owner_draw_plan}+%s/6' % (SUMN('pnl', 'costs', 6), SUMN('taxmonth', 'set_aside', 6)), 13),
    CA('spare', 'Spare cash (expected minus paid out)', 'money', '{col:expected}-{col:needed}', 13),
    CA('verdict', 'Verdict', 'text', 'IF({col:expected}<{col:needed},%s,%s)' % (vc('A gap in the month'), vc('No gap')), 16)],
    D.receipts_d(), 50, [A('verdict', '= ' + vc('A gap in the month'), 'bad')]))
# ---------------------------------------------------------------- 14 known payments due
BAL = 'IF({col:amount}="","",%s-SUMIFS({range:due.amount},{range:due.rank_no},"<="&{col:rank_no}))' % CASHNOW
DX = 'MATCH(SMALL({range:jobpay.open_key},{col:rank_no}),{range:jobpay.open_key},0)'
def DJ(col): return 'IFERROR(IF(SMALL({range:jobpay.open_key},{col:rank_no})>=99999,"",INDEX({range:jobpay.%s},%s)),"")' % (col, DX)
tables.append(T('due', 'Known Payments Due', 'Open contractor payments in the order to pay them',
    'One row per open payment in order of due date: contractor, title, stage and amount from Job Payments; the cash left after paying it and a floor check fill in by themselves.', [
    C('rank_no', 'Order', 'int', 7, required=True),
    CA('due_date', 'Due date', 'date', DJ('date'), 11), CA('contractor', 'Contractor', 'text', DJ('contractor'), 20), CA('title', 'Title', 'text', DJ('title'), 26), CA('stage', 'Stage', 'text', DJ('stage'), 10),
    CA('amount', 'Amount', 'money', DJ('amount'), 11), CA('cumulative', 'Paid so far, with this one', 'money', 'IF({col:amount}="","",SUMIFS({range:due.amount},{range:due.rank_no},"<="&{col:rank_no}))', 12),
    CA('balance_after', 'Cash left after paying it', 'money', BAL, 13),
    CA('check', 'Floor check', 'text', 'IF({col:amount}="","",IF({col:balance_after}<{set:cash_floor},%s,%s))' % (vc('Below the floor'), vc('Above the floor')), 14),
    CA('phone', 'Contractor phone', 'text', DJ('phone'), 18), CA('floor', 'Cash floor', 'money', '{set:cash_floor}', 10), *AUTH(), COMPANY_()],
    D.due_d()[:14], 50, [A('check', '= ' + vc('Below the floor'), 'bad'), A('check', '= ' + vc('Above the floor'), 'good')]))
# ---------------------------------------------------------------- 15 sales scenarios
tables.append(T('scenarios', 'Sales Scenarios', 'Base, Best and Worst scenarios for the forecast',
    'One row per scenario: the change of sales and the change of costs (your own numbers); the forecast uses the scenario chosen on Start, and Worst is sales minus 20%.', [
    LST('scenario', 'Scenario', 'scen', 14, required=True), C('sales_change', 'Sales change', 'pct', 12), C('cost_change', 'Cost change', 'pct', 12)],
    D.scenarios_d(), 50))
# ---------------------------------------------------------------- 16 health check areas
HV = lambda t, c: 'INDEX({range:%s.%s},MATCH({col:area_no},{range:health.area_no},0))' % (t, c)
SC3 = lambda t, c: 'SUMIFS({range:%s.%s},%s)' % (t, c, WIN('{range:%s.month}' % t, 3))
V_ALL = ('CHOOSE({col:area_no},IFERROR(%s/%s,0),IFERROR(%s/%s,0),{col:typed_value},IFERROR(%s/%s,0),IFERROR(%s/%s,0),%s/{set:cash_floor},{col:typed_value},{col:typed_value},{col:typed_value},{col:typed_value},'
         'COUNTIFS({range:expmonth.month},%s,{range:expmonth.verdict},%s),IFERROR((%s+MAX(0,({set:next_tax_on}-{today})/30.4)*%s/3)/{set:next_tax_amount},0))') % (
    SUM12('pnl', 'profit'), SUM12('pnl', 'revenue'), SC3('pnl', 'profit'), SC3('pnl', 'revenue'), SUM12('pnl', 'ads'), SUM12('pnl', 'revenue'), CASHNOW, AVGCOST12, CASHNOW, LM, vt('Over budget'), POT_NOW, SC3('taxmonth', 'set_aside'))
TGT = ('CHOOSE({col:area_no},{set:margin_target},{set:margin_target},{set:ad_return_target},{set:ad_share_limit},{set:cash_cover_months},1,{set:store_dep_limit},{set:readthrough_warn_1},{set:readthrough_warn},'
       '{set:titles_be_limit},{set:over_limit},1)')
def TOPN(n, col): return 'IFERROR(INDEX({range:health.%s},MATCH(%d,{range:health.rank},0)),"")' % (col, n)
tables.append(T('health', 'Health Check Areas', 'Owner health check by area with green, amber and red',
    'One row per area: your value, your target (from Start), the distance, a green, amber or red verdict and an action; type the five figures from your other parts.', [
    C('area_no', 'Area no', 'int', 7, required=True), C('typed_value', 'Figure from your other sheets', 'num', 12), C('band', 'Amber band (share of the target)', 'pct', 12),
    CA('area', 'Area', 'text', 'CHOOSE({col:area_no},%s)' % ','.join(tok('area', a) for a in AREAS), 36), CA('value', 'Your value', 'num', V_ALL, 10), CA('target', 'Your target', 'num', TGT, 10),
    CA('lower', 'Lower is better (1 = yes)', 'int', 'CHOOSE({col:area_no},0,0,0,1,0,0,1,0,0,1,1,0)', 9),
    CA('gap', 'Distance from the target', 'pct', 'IF({col:target}>0,IF({col:lower}=1,({col:value}-{col:target})/{col:target},({col:target}-{col:value})/{col:target}),0)', 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:gap}<=0,%s,IF({col:gap}<={col:band},%s,%s))' % (vh('Green'), vh('Amber'), vh('Red')), 9),
    CA('points', 'Points', 'int', 'IF({col:verdict}=%s,100,IF({col:verdict}=%s,50,0))' % (vh('Green'), vh('Amber')), 7),
    CA('rank_key', 'Rank key', 'num', 'IF({col:gap}>0,{col:gap}+{col:area_no}/1000000,-{col:area_no}/1000000)', 9), CA('rank', 'Rank (1 = furthest from target)', 'int', 'COUNTIFS({range:health.rank_key},">"&{col:rank_key})+1', 10),
    CA('action', 'Action', 'text', 'IF({col:verdict}=%s,%s,CHOOSE({col:area_no},%s))' % (vh('Green'), act('Keep going'), ','.join(act(a) for a in ACTS[1:])), 40),
    CA('score', 'Score of the check', 'int', 'AVERAGE({range:health.points})', 8), CA('red_count', 'Red areas', 'int', 'COUNTIFS({range:health.verdict},%s)' % vh('Red'), 7),
    CA('top_area', 'Area furthest from the target', 'text', TOPN(1, 'area'), 30),
    CA('actions_text', 'Your three actions', 'text', 'IF({col:red_count}+COUNTIFS({range:health.verdict},%s)=0,%s,%s&"; "&%s&"; "&%s)' % (vh('Amber'), act('Keep going'), TOPN(1, 'action'), TOPN(2, 'action'), TOPN(3, 'action')), 60), *AUTH(), COMPANY_()],
    D.health_d(), 50, [A('verdict', '= ' + vh('Red'), 'bad'), A('verdict', '= ' + vh('Amber'), 'warn'), A('verdict', '= ' + vh('Green'), 'good')]))
# ---------------------------------------------------------------- 17 authors and shares
tables.append(T('authors', 'Authors and Shares', 'Pen names with the author share in force from a date',
    'One row per pen name and agreed share, from the date it starts (a new row when the share changes); a one-author business sets the share to 100 percent.', [
    LST('pen_name', 'Pen name', 'penname', 20, required=True), C('effective_from', 'Share in force from', 'date', 14), C('author_share', 'Author share', 'pct', 12)],
    D.authors_d(), 50))
# ---------------------------------------------------------------- 18 author statements
AS_SUM = lambda col, extra='': 'SUMIFS({range:authstmt.%s},{range:authstmt.pen_name},{col:pen_name},{range:authstmt.month},"<="&{col:month}%s)' % (col, extra)
tables.append(T('authstmt', 'Author Statements', 'Statement for each author and month',
    'One row per pen name and month: royalties earned, advance recouped and costs charged back; the share, the advance left, the press share and the amount payable fill in.', [
    C('statement_id', 'Statement ID', 'text', 11, required=True), C('month', 'Month', 'date', 11), LST('pen_name', 'Pen name', 'penname', 17), C('royalties_earned', 'Royalties earned', 'money', 13), C('advance_paid', 'Advance paid', 'num', 11),
    C('advance_recouped', 'Advance recouped', 'money', 12), C('costs_charged_back', 'Costs charged back', 'money', 12),
    CA('share_from', 'Share in force from', 'date', 'SUMPRODUCT(MAX(({range:authors.pen_name}={col:pen_name})*({range:authors.effective_from}<={col:month}+27)*{range:authors.effective_from}))', 12),
    CA('author_share', 'Author share', 'pct', 'SUMIFS({range:authors.author_share},{range:authors.pen_name},{col:pen_name},{range:authors.effective_from},{col:share_from})', 10),
    CA('author_part', 'Author part', 'money', '{col:royalties_earned}*{col:author_share}', 11),
    CA('advance_left', 'Advance left', 'money', 'IF(%s>0,{col:advance_paid}-%s,0)' % (AS_SUM('advance_recouped'), AS_SUM('advance_recouped')), 11),
    CA('payable', 'Payable', 'money', '{col:author_part}-{col:advance_recouped}-{col:costs_charged_back}', 11), CA('press_share', 'Press share', 'money', '{col:royalties_earned}-{col:author_part}', 11),
    CA('press_pct', 'Press share of royalties', 'pct', '1-{col:author_share}', 9), CA('share_total', 'Author and press shares together', 'pct', '{col:author_share}+{col:press_pct}', 10),
    CA('latest', 'Latest month (1 = yes)', 'int', 'IF({col:month}=MAX({range:authstmt.month}),1,0)', 8),
    CA('month_payable', 'Payable to all authors this month', 'money', 'SUMIFS({range:authstmt.payable},{range:authstmt.month},{col:month})', 13),
    CA('month_earned', 'Royalties of all authors this month', 'money', 'SUMIFS({range:authstmt.royalties_earned},{range:authstmt.month},{col:month})', 13),
    CA('recouped_total', 'Advance recouped so far', 'money', AS_SUM('advance_recouped'), 12), CA('months_recouping', 'Months recouping', 'int', 'COUNTIFS({range:authstmt.pen_name},{col:pen_name},{range:authstmt.advance_recouped},">0",{range:authstmt.month},"<="&{col:month})', 9),
    *AUTH(), COMPANY_()],
    D.authstmt_d(), 120, [A('payable', '< 0', 'bad')]))
# ---------------------------------------------------------------- 19 author payments schedule
tables.append(T('authsched', 'Author Payments Schedule', 'What you owe each author by month and the cash left',
    'One row per month and pen name for the next 6 months: the payable from your own last 3 months and the scenario, the forecast cash and the cash left after paying every author that month.', [
    C('month', 'Month', 'date', 11, required=True), LST('pen_name', 'Pen name', 'penname', 17),
    CA('payable', 'Payable (estimate)', 'money', 'IFERROR(AVERAGEIFS({range:authstmt.payable},{range:authstmt.pen_name},{col:pen_name},%s),0)*(1+%s)' % (WIN('{range:authstmt.month}', 3), SCA), 13),
    CA('month_total', 'Payable to all authors', 'money', 'SUMIFS({range:authsched.payable},{range:authsched.month},{col:month})', 12),
    CA('cash_before', 'Forecast cash before paying', 'money', 'IFERROR(INDEX({range:forecast.closing},MATCH({col:month},{range:forecast.month},0)),0)', 13),
    CA('cash_after', 'Cash after paying all authors', 'money', '{col:cash_before}-{col:month_total}', 13),
    CA('verdict', 'Verdict', 'text', 'IF({col:cash_after}>={set:cash_floor},%s,%s)' % (vc('Pay in full'), vc('Pay in two parts')), 16), *AUTH(), COMPANY_()],
    D.authsched_d(), 50, [A('verdict', '= ' + vc('Pay in two parts'), 'warn'), A('verdict', '= ' + vc('Pay in full'), 'good')]))
# ---------------------------------------------------------------- 20 year-end summary lines
YAMT = [SUM12('pnl', c) for c in ('royalties', 'page_reads', 'direct_net', 'event_sales', 'rights', 'revenue', 'ads', 'production', 'expenses', 'event_costs', 'costs', 'profit')]
YAMT += [SUM12('taxmonth', 'set_aside'), SUM12('taxmonth', 'tax_paid'), 'IFERROR(INDEX({range:taxmonth.pot_balance},MATCH(%s,{range:taxmonth.month},0)),0)' % LM, SUM12('cash', 'owner_draw'), SUM12('cash', 'author_copies'),
         'IFERROR(INDEX({range:cash.closing},MATCH(%s,{range:cash.month},0)),0)' % LM,
         'SUMIFS({range:jobpay.amount},{range:jobpay.status},%s,%s)' % (PAID, W12('jobpay', 'date')), '(%s+%s)' % (SUM12('payments', 'fee', 'received_on'), SUM12('payments', 'fx_loss', 'received_on'))]
assert len(YAMT) == 20
tables.append(T('yearend', 'Year-end Summary Lines', 'The year-end pack for your adviser in 20 lines',
    'One row per line of the pack for the last 12 complete months: income lines, cost lines, profit, tax set-aside, tax paid, draws and cash; the note says where each number comes from.', [
    C('line_no', 'Line', 'int', 7, required=True), CA('line', 'Line', 'text', 'CHOOSE({col:line_no},%s)' % ','.join(tok('yline', a) for a in YLINES), 34),
    CA('amount', 'Amount', 'money', 'CHOOSE({col:line_no},%s)' % ','.join(YAMT), 13), CA('note', 'Where it comes from', 'text', 'CHOOSE({col:line_no},%s)' % ','.join(tok('ynote', a) for a in YNOTES), 32), ACCT()[0], ACCT()[1], COMPANY_()],
    D.yearend_d(), 50))
assert len(tables) == 20, len(tables)
