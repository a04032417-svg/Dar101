"""Household Finance suite part 8: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf8_lists import *
import hf8_data as D


def R(t, c): return '{range:%s.%s}' % (t, c)
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)
def G(idc, body): return 'IF({col:%s}="","",%s)' % (idc, body)


MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YES, NO = '{list:yesno.yes}', '{list:yesno.no}'
BOUGHT, CAR, MOVE = tok('bpstatus', 'Bought'), tok('bpkind', 'Car'), tok('bpkind', 'Move')
THIS_Y, LAST_Y = 'YEAR({today})&""', '(YEAR({today})-1)&""'
TH = 'SUMIFS(%s,%s,1)/12' % (R('year_months', 'take_home'), R('year_months', 'last12'))
HAVE_MOVE = 'SUMIFS(%s,%s,%s,%s,"<>"&%s)' % (R('big_purchases', 'saved'), R('big_purchases', 'kind'), MOVE, R('big_purchases', 'status'), BOUGHT)
BAL_NOW = '(SUMIFS(%s,%s,"<="&{today})-SUMIFS(%s,%s,"<="&{today}))' % (R('set_aside', 'moved'), R('set_aside', 'date'), R('est_payments', 'payment'), R('est_payments', 'date'))
P = D.PH
def PHC(who, label): return CA(who + '_phone', label, 'text', '"%s"' % P[who], 18)
def HH(): return CA('household', 'Household', 'text', '{set:household}', 22)
def N1(): return CA('partner1', 'Partner 1 name', 'text', '{set:partner1}', 14)
def N2(): return CA('partner2', 'Partner 2 name', 'text', '{set:partner2}', 14)

settings = [
    S('household', 'Household name', 'text', HOUSEHOLD), S('partner1', 'Partner 1 name, shown in messages', 'text', 'Partner 1'), S('partner2', 'Partner 2 name, shown in messages', 'text', 'Partner 2'),
    S('savings_rate_target', 'Savings rate you want, your own number', 'pct', SAVINGS_RATE_TARGET), S('set_aside_pct', 'Set-aside share of freelance income, confirm with adviser', 'pct', SET_ASIDE_PCT),
    S('car_limit', 'Car cost share of take-home, a typical range, check your own', 'pct', 0.07), S('car_years', 'Years you plan to keep a car', 'int', 5),
    S('big_saving', 'Monthly amount you can put toward big purchases', 'money', D.BIG_SAVING), S('pay_per_year', 'Paychecks a year', 'int', 26),
    S('due_soon_days', 'An item due within this many days is due soon', 'int', 30), S('income_change', 'Expected income change next year, an example', 'pct', 0.03),
    S('receipt_big', 'A receipt of this amount or more is worth chasing first', 'money', 100)]

tables = []
# 1 big purchases ------------------------------------------------------------------------------------------------
tables.append(T('big_purchases', 'Big purchases', 'Big Purchases',
    'Every big purchase with its target, what is saved and the planned date; what is left to save, the months to the date and the monthly saving needed fill in by themselves.', [
    C('bp_id', 'Purchase ID', 'text', 10, required=True), C('item', 'Item', 'text', 26), LST('kind', 'Kind', 'bpkind', 13), C('planned_date', 'Planned date', 'date', 12), C('target', 'Target', 'money', 12),
    C('saved', 'Saved so far', 'money', 12), C('goal_id', 'Goal ID', 'text', 9), LST('priority', 'Priority', 'priority', 10), LST('status', 'Status', 'bpstatus', 10),
    CA('left', 'Left to save', 'money', G('bp_id', 'IF({col:status}=%s,0,MAX(0,{col:target}-{col:saved}))' % BOUGHT), 12),
    CA('months_left', 'Months to the date', 'num', G('bp_id', 'IF({col:planned_date}="","",ROUND(MAX(0,{col:planned_date}-{today})/30.4375,1))'), 11),
    CA('per_month', 'Saving needed a month', 'money', G('bp_id', 'IF({col:left}=0,0,IF({col:months_left}="",{col:left},{col:left}/MAX(1,{col:months_left})))'), 13),
    CA('saved_share', 'Share saved', 'pct', G('bp_id', 'IF({col:target}>0,MIN(1,{col:saved}/{col:target}),0)'), 10),
    CA('order_key', 'Order key', 'num', G('bp_id', 'IF({col:status}=%s,"",{col:planned_date}+MATCH({col:bp_id},%s,0)/1000)' % (BOUGHT, R('big_purchases', 'bp_id'))), 10), HH(), PHC('mech', 'Car mechanic phone')],
    D.big_purchases_d(), 50, [A('status', '= ' + BOUGHT, 'good')]))
# 2 purchase options ----------------------------------------------------------------------------------------------
PO = lambda c: R('purchase_options', c)
tables.append(T('purchase_options', 'Purchase options', 'Purchase Options',
    'The options you compare for each big purchase: price, down payment, trade-in, loan and running cost; the loan amount, the monthly payment and the monthly cost fill in.', [
    C('option_id', 'Option ID', 'text', 9, required=True), REF('bp_id', 'Purchase ID', 'big_purchases.bp_id', 10), C('option', 'Option', 'text', 28), C('price', 'Price', 'money', 12),
    C('down_payment', 'Down payment', 'int', 12), C('trade_in', 'Trade-in', 'int', 10), C('loan_months', 'Loan months', 'int', 9), C('rate', 'Yearly rate', 'pct', 9), C('running_cost', 'Running cost a month', 'money', 12),
    CA('item', 'Purchase', 'text', LKT('big_purchases.item', 'big_purchases.bp_id', 'bp_id'), 24),
    CA('loan_amount', 'Loan amount', 'money', G('option_id', 'MAX(0,{col:price}-{col:down_payment}-{col:trade_in})'), 12),
    CA('monthly_payment', 'Monthly payment', 'money', G('option_id', 'IF(OR({col:loan_months}<=0,{col:loan_amount}<=0),0,IF({col:rate}=0,{col:loan_amount}/{col:loan_months},-PMT({col:rate}/12,{col:loan_months},{col:loan_amount})))'), 12),
    CA('monthly_cost', 'Monthly cost', 'money', G('option_id', '{col:monthly_payment}+{col:running_cost}'), 12),
    CA('car_key', 'Car monthly cost', 'money', G('option_id', 'IF(AND({col:price}>0,%s=%s),{col:monthly_cost},"")' % (LKT('big_purchases.kind', 'big_purchases.bp_id', 'bp_id'), CAR)), 12)],
    D.options_d(), 50))
# 3 car decision --------------------------------------------------------------------------------------------------
def CP(c): return 'IFERROR(INDEX(%s,MATCH({col:option},%s,0)),0)' % (PO(c), PO('option'))
tables.append(T('car_decision', 'Car decision', 'Car Decision, Each Option and Loan Term',
    'Each car option at several loan terms: monthly payment, running cost, total over the years you keep the car, the share of take-home pay and a verdict against your own limit.', [
    C('row_id', 'Row ID', 'text', 8, required=True), LST('option', 'Option', 'caropt', 28), C('loan_months', 'Loan months tested', 'int', 11),
    CA('price', 'Price', 'money', G('row_id', CP('price')), 11), CA('down', 'Down payment', 'money', G('row_id', CP('down_payment')), 12), CA('rate', 'Yearly rate', 'pct', G('row_id', CP('rate')), 9),
    CA('running', 'Running cost a month', 'money', G('row_id', CP('running_cost')), 12),
    CA('loan', 'Loan amount', 'money', G('row_id', 'MAX(0,{col:price}-{col:down}-%s)' % CP('trade_in')), 12),
    CA('monthly_payment', 'Monthly payment', 'money', G('row_id', 'IF(OR({col:loan_months}<=0,{col:loan}<=0),0,IF({col:rate}=0,{col:loan}/{col:loan_months},-PMT({col:rate}/12,{col:loan_months},{col:loan})))'), 12),
    CA('monthly_cost', 'Monthly cost', 'money', G('row_id', '{col:monthly_payment}+{col:running}'), 12),
    CA('total_years', 'Total over the years', 'money', G('row_id', '{col:down}+{col:monthly_payment}*{col:loan_months}+{col:running}*MAX({set:car_years}*12,{col:loan_months})'), 13),
    CA('share', 'Share of take-home', 'pct', G('row_id', 'IFERROR({col:monthly_cost}/(%s),0)' % TH), 10),
    CA('verdict', 'Against your limit', 'text', G('row_id', 'IF({col:share}<={set:car_limit},%s,%s)' % (vd('Within your limit'), vd('Above your limit'))), 15),
    CA('keep_cost', 'Keep the current car, a month', 'money', 'IFERROR(INDEX(%s,MATCH({list:caropt.%s},%s,0)),0)' % (PO('running_cost'), key('caropt', CAR_OPTS[2]), PO('option')), 13),
    CA('diff_keep', 'More (+) or less (-) than keeping', 'money', G('row_id', '{col:monthly_cost}-{col:keep_cost}'), 13), HH(), N1(), N2(), PHC('p1', 'Partner 1 phone'), PHC('p2', 'Partner 2 phone')],
    D.car_decision_d(), 50, [A('verdict', '= ' + vd('Above your limit'), 'warn'), A('verdict', '= ' + vd('Within your limit'), 'good')]))
# 4 move plan -----------------------------------------------------------------------------------------------------
MP = lambda c: R('move_plan', c)
tables.append(T('move_plan', 'Move plan', 'Moving Plan, Cost by Cost',
    'Every cost of the move with estimate, paid and due date; what is left, the days to the due date and a status fill in, with the total cash needed and the money saved for the move.', [
    C('move_id', 'Move item ID', 'text', 9, required=True), C('item', 'Item', 'text', 28), C('estimate', 'Estimate', 'money', 12), C('paid', 'Paid', 'money', 11), C('due_date', 'Due date', 'date', 11),
    LST('kind', 'Kind', 'mvkind', 11), C('move_date', 'Move date', 'date', 11),
    CA('left', 'Left to pay', 'money', G('move_id', 'MAX(0,{col:estimate}-{col:paid})'), 12), CA('days_to_due', 'Days to due', 'int', G('move_id', 'IF({col:due_date}="","",{col:due_date}-{today})'), 9),
    CA('status', 'Status', 'text', G('move_id', 'IF({col:left}=0,%s,IF({col:due_date}<{today},%s,IF({col:due_date}-{today}<={set:due_soon_days},%s,%s)))' % (st('Paid'), st('Overdue'), st('Due soon'), st('Later'))), 11),
    CA('total_needed', 'Total cash needed', 'money', 'SUM(%s)' % MP('estimate'), 13), CA('have', 'Saved for the move', 'money', HAVE_MOVE, 13), HH(), N2(),
    PHC('p2', 'Partner 2 phone'), PHC('landlord', 'Landlord phone'), PHC('util', 'Utility company phone')],
    D.move_plan_d(), 50, [A('status', '= ' + st('Overdue'), 'bad'), A('status', '= ' + st('Due soon'), 'warn'), A('status', '= ' + st('Paid'), 'good')]))
# 5 move cash by month -------------------------------------------------------------------------------------------
tables.append(T('move_cash', 'Move cash needed', 'Move Cash Needed by Month',
    'Month by month: the move costs that fall due, the running total of cash needed, the money you have if the monthly saving goes to the move, and whether the move is covered.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('due_in_month', 'Due this month', 'money', 'SUMIFS(%s,%s,">="&{col:month},%s,"<"&EDATE({col:month},1))' % (MP('left'), MP('due_date'), MP('due_date')), 12),
    CA('due_so_far', 'Cash needed so far', 'money', 'SUMIFS(%s,%s,"<"&EDATE({col:month},1))' % (MP('left'), MP('due_date')), 13),
    CA('saved_by', 'You have by then', 'money', G('month', '%s+{set:big_saving}*((YEAR({col:month})-YEAR(%s))*12+MONTH({col:month})-MONTH(%s))' % (HAVE_MOVE, MS, MS)), 13),
    CA('gap', 'Short (+) or spare (-)', 'money', G('month', '{col:due_so_far}-{col:saved_by}'), 13),
    CA('status', 'Status', 'text', G('month', 'IF({col:gap}<=0,%s,%s)' % (st('Covered'), st('Short'))), 10)],
    D.move_cash_d(), 50, [A('status', '= ' + st('Short'), 'warn'), A('status', '= ' + st('Covered'), 'good')]))
# 6 event budget --------------------------------------------------------------------------------------------------
EB = lambda c: R('event_budget', c)
tables.append(T('event_budget', 'Event budget', 'Event Budget',
    'Every item of a family event with estimate, paid, due date and deposit against the target total; what is left, the days to due, a status and the total over or under the target fill in.', [
    C('event_item_id', 'Event item ID', 'text', 10, required=True), C('event', 'Event', 'text', 20), LST('item', 'Item', 'eitem', 24), C('estimate', 'Estimate', 'money', 11), C('paid', 'Paid', 'money', 11),
    C('due_date', 'Due date', 'date', 11), C('deposit', 'Deposit needed', 'bool', 9), C('target_total', 'Target total', 'int', 11),
    CA('left', 'Left to pay', 'money', G('event_item_id', 'MAX(0,{col:estimate}-{col:paid})'), 11), CA('days_to_due', 'Days to due', 'int', G('event_item_id', 'IF({col:due_date}="","",{col:due_date}-{today})'), 9),
    CA('status', 'Status', 'text', G('event_item_id', 'IF({col:left}=0,%s,IF({col:due_date}<{today},%s,IF({col:due_date}-{today}<={set:due_soon_days},%s,%s)))' % (st('Paid'), st('Overdue'), st('Due soon'), st('Later'))), 10),
    CA('estimate_total', 'Estimate total', 'money', 'SUM(%s)' % EB('estimate'), 12), CA('over_by', 'Over the target by', 'money', G('event_item_id', 'MAX(0,SUM(%s)-{col:target_total})' % EB('estimate')), 12),
    CA('monthly_saving', 'Saving a month to the last date', 'money', G('event_item_id', 'MAX(0,SUM(%s)-SUM(%s))/MAX(1,(LARGE(%s,1)-{today})/30.4375)' % (EB('estimate'), EB('paid'), EB('due_date'))), 13),
    HH(), N2(), PHC('p2', 'Partner 2 phone'), PHC('gp', 'Grandparent phone')],
    D.event_budget_d(), 50, [A('status', '= ' + st('Overdue'), 'bad'), A('status', '= ' + st('Due soon'), 'warn'), A('status', '= ' + st('Paid'), 'good')]))
# 7 rent or buy inputs ---------------------------------------------------------------------------------------------
tables.append(T('rb_inputs', 'Rent or buy inputs', 'Rent or Buy, Your Numbers',
    'Type your own numbers for renting and for buying; percentages are typed as percent (5.9 means 5.9 percent). The comparison is an estimate from your numbers, not advice.', [
    LST('item', 'Item', 'rbitem', 36, required=True), C('rent_option', 'Rent option', 'num', 12), C('buy_option', 'Buy option', 'num', 12), C('note', 'Note', 'text', 40)],
    D.rb_inputs_d(), 50))
# 8 rent or buy comparison ------------------------------------------------------------------------------------------
def RBR(k): return 'INDEX(%s,MATCH({list:rbitem.%s},%s,0))' % (R('rb_inputs', 'rent_option'), key('rbitem', k), R('rb_inputs', 'item'))
def RBB(k): return 'INDEX(%s,MATCH({list:rbitem.%s},%s,0))' % (R('rb_inputs', 'buy_option'), key('rbitem', k), R('rb_inputs', 'item'))
PRICE, DOWN, RATE, TERM = RBB('Home price'), RBB('Down payment'), '(' + RBB('Mortgage rate, percent a year') + '/1200)', RBB('Mortgage term, years')
LOAN = '(%s-%s)' % (PRICE, DOWN)
tables.append(T('rb_compare', 'Rent or buy comparison', 'Rent or Buy, Cost over the Years',
    'For each year: what renting costs in total (with the return on the money you keep) and what buying costs in total (if you sold that year); the year buying starts to cost less is marked.', [
    C('year', 'Year', 'int', 7, required=True),
    CA('rent_paid', 'Rent and running cost paid', 'money', G('year', '%s*12*IF(%s=0,{col:year},((1+%s/100)^{col:year}-1)/(%s/100))+%s*12*{col:year}' % (RBR('Monthly rent'), RBR('Rent growth, percent a year'), RBR('Rent growth, percent a year'), RBR('Rent growth, percent a year'), RBR('Other running cost a month'))), 14),
    CA('rent_gain', 'Return on kept money', 'money', G('year', '(%s+%s*%s/100)*((1+%s/100)^{col:year}-1)' % (DOWN, PRICE, RBB('Buying costs, percent of price'), RBR('Return on kept money, percent a year'))), 13),
    CA('rent_cost', 'Renting costs in total', 'money', G('year', '{col:rent_paid}-{col:rent_gain}'), 13),
    CA('mortgage_payment', 'Monthly mortgage payment', 'money', G('year', 'IF(%s=0,%s/(%s*12),-PMT(%s,%s*12,%s))' % (RATE, LOAN, TERM, RATE, TERM, LOAN)), 13),
    CA('loan_balance', 'Loan balance left', 'money', G('year', 'IF(%s=0,%s-{col:mortgage_payment}*12*{col:year},%s*(1+%s)^(12*{col:year})-{col:mortgage_payment}*((1+%s)^(12*{col:year})-1)/%s)' % (RATE, LOAN, LOAN, RATE, RATE, RATE)), 13),
    CA('buy_paid', 'Buying costs paid', 'money', G('year', '%s+%s*%s/100+{col:mortgage_payment}*12*MIN({col:year},%s)+(%s+%s*12)*{col:year}' % (DOWN, PRICE, RBB('Buying costs, percent of price'), TERM, RBB('Upkeep and local charges a year'), RBB('Other running cost a month'))), 14),
    CA('buy_equity', 'Home value less selling costs and loan', 'money', G('year', '%s*(1+%s/100)^{col:year}*(1-%s/100)-{col:loan_balance}' % (PRICE, RBB('Home price growth, percent a year'), RBB('Selling costs, percent of price'))), 15),
    CA('buy_cost', 'Buying costs in total', 'money', G('year', '{col:buy_paid}-{col:buy_equity}'), 13),
    CA('difference', 'Buying more (+) or less (-)', 'money', G('year', '{col:buy_cost}-{col:rent_cost}'), 13),
    CA('break_even', 'First year buying costs less', 'int', G('year', 'IF(AND({col:difference}<=0,COUNTIFS(%s,"<"&{col:year},%s,"<=0")=0),1,0)' % (R('rb_compare', 'year'), R('rb_compare', 'difference'))), 11),
    CA('be_years', 'Break-even year', 'int', 'IFERROR(INDEX(%s,MATCH(1,%s,0)),"")' % (R('rb_compare', 'year'), R('rb_compare', 'break_even')), 10), HH(), N1(), PHC('p1', 'Partner 1 phone')],
    D.rb_compare_d(), 50, [A('break_even', '= 1', 'good')]))
# 9 tax documents -----------------------------------------------------------------------------------------------------
TD = lambda c: R('tax_docs', c)
DEDR = lambda c: R('deductions', c)
tables.append(T('tax_docs', 'Tax documents', 'Tax Documents Checklist',
    'Every paper for your tax office: expected, received, filed and the due date; days to due, status and the missing count fill in. Check your local rules.', [
    C('doc_id', 'Document ID', 'text', 10, required=True), LST('tax_year', 'Tax year', 'tyear', 9), LST('doc_type', 'Document type', 'tdtype', 20), C('description', 'Description', 'text', 30),
    C('source_id', 'Source ID', 'text', 9), LST('contact', 'Who to ask', 'contact', 18), LST('person', 'Person', 'person', 10), C('expected_on', 'Expected on', 'date', 11), C('received_on', 'Received on', 'date', 11),
    C('filed', 'Filed', 'bool', 7), C('due_date', 'Due date', 'date', 11),
    CA('got', 'In hand', 'int', G('doc_id', 'IF(OR({col:received_on}<>"",{col:filed}=%s),1,0)' % YES), 8),
    CA('status', 'Status', 'text', G('doc_id', 'IF({col:filed}=%s,%s,IF({col:received_on}<>"",%s,IF({col:expected_on}<{today},%s,%s)))' % (YES, st('Filed'), st('Received'), st('Overdue'), st('Expected'))), 11),
    CA('days_to_due', 'Days to due date', 'int', G('doc_id', 'IF({col:due_date}="","",{col:due_date}-{today})'), 10),
    CA('miss_key', 'Missing key', 'num', G('doc_id', 'IF({col:got}=0,IF({col:expected_on}="",0,{today}-{col:expected_on})+(1000-MATCH({col:doc_id},%s,0))/10000,"")' % TD('doc_id')), 10),
    CA('year_total', 'Documents this year', 'int', G('doc_id', 'COUNTIFS(%s,{col:tax_year},%s,"<>")' % (TD('tax_year'), TD('doc_id'))), 10),
    CA('received_count', 'Received this tax year', 'int', G('doc_id', 'COUNTIFS(%s,{col:tax_year},%s,1)' % (TD('tax_year'), TD('got'))), 10),
    CA('missing_count', 'Missing this tax year', 'int', G('doc_id', 'COUNTIFS(%s,{col:tax_year},%s,%s)' % (TD('tax_year'), TD('status'), st('Overdue'))), 10),
    CA('type_received', 'Received of this type', 'int', G('doc_id', 'COUNTIFS(%s,{col:tax_year},%s,{col:doc_type},%s,1)' % (TD('tax_year'), TD('doc_type'), TD('got'))), 10),
    CA('type_total', 'Documents of this type', 'int', G('doc_id', 'COUNTIFS(%s,{col:tax_year},%s,{col:doc_type})' % (TD('tax_year'), TD('doc_type'))), 10),
    CA('year_deductions', 'Deductions recorded this year', 'money', G('doc_id', 'SUMIFS(%s,%s,{col:tax_year})' % (DEDR('amount'), DEDR('tax_year'))), 13),
    CA('receipts_missing', 'Receipts missing this year', 'int', G('doc_id', 'COUNTIFS(%s,{col:tax_year},%s,%s)' % (DEDR('tax_year'), DEDR('receipt'), NO)), 10),
    CA('childcare_total', 'Childcare recorded this year', 'money', G('doc_id', 'SUMIFS(%s,%s,{col:tax_year},%s,%s)' % (DEDR('amount'), DEDR('tax_year'), DEDR('category'), tok('dedcat', 'Childcare'))), 13),
    CA('set_balance', 'Tax set-aside balance', 'money', G('doc_id', BAL_NOW), 12), HH(), N1(),
    PHC('p1', 'Partner 1 phone'), PHC('member', 'Household member phone'), PHC('tax', 'Tax preparer phone'), PHC('payroll', 'Payroll office phone'), PHC('clienta', 'Client A phone'),
    PHC('clientb', 'Client B phone'), PHC('bank', 'Bank branch phone'), PHC('child', 'Childcare provider phone'), PHC('school', 'School office phone'), PHC('ins', 'Insurance agent phone')],
    D.tax_docs_d(), 60, [A('status', '= ' + st('Overdue'), 'bad'), A('status', '= ' + st('Filed'), 'good')]))
# 10 missing documents ------------------------------------------------------------------------------------------------
def MDX(c): return 'IF({col:mkey}="","",INDEX(%s,MATCH({col:mkey},%s,0)))' % (TD(c), TD('miss_key'))
tables.append(T('missing_docs', 'Missing documents', 'Missing Documents, Most Overdue First',
    'The documents not yet in hand, the most overdue first (a minus means it is not due yet), with who to ask and the next step; it fills in from the Tax documents sheet.', [
    C('rank', 'Rank', 'int', 7, required=True), CA('mkey', 'Ranking key', 'num', 'IFERROR(LARGE(%s,{col:rank}),"")' % TD('miss_key'), 10),
    CA('doc_id', 'Document ID', 'text', MDX('doc_id'), 10), CA('doc_type', 'Document type', 'text', MDX('doc_type'), 20), CA('description', 'Description', 'text', MDX('description'), 30),
    CA('expected_on', 'Expected on', 'date', MDX('expected_on'), 11), CA('days_overdue', 'Days overdue', 'int', 'IF({col:mkey}="","",{today}-{col:expected_on})', 10),
    CA('contact', 'Who to ask', 'text', 'IF({col:mkey}="","",INDEX(%s,MATCH({col:mkey},%s,0))&"")' % (TD('contact'), TD('miss_key')), 18),
    CA('next_step', 'Next step', 'text', 'IF({col:mkey}="","",IF({col:days_overdue}<=0,%s,IF({col:contact}<>"",%s,%s)))' % (st('Not due yet'), st('Ask the contact'), st('Find it in your own records')), 24),
    HH(), N2(), PHC('tax', 'Tax preparer phone')],
    D.missing_docs_d(), 50, [A('days_overdue', '> 0', 'bad')]))
# 11 deductions ---------------------------------------------------------------------------------------------------------
tables.append(T('deductions', 'Deduction records', 'Deduction Records',
    'Every cost you keep a record of for your tax return: date, description, amount, category and whether you hold the receipt. The records say nothing about what is allowed: ask your adviser.', [
    C('deduction_id', 'Record ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), CA('month', 'Month', 'date', 'IF({col:date}="","",DATE(YEAR({col:date}),MONTH({col:date}),1))', 11),
    C('description', 'Description', 'text', 26), LST('category', 'Category', 'dedcat', 20), C('amount', 'Amount', 'money', 11), C('receipt', 'Receipt kept', 'bool', 9), LST('tax_year', 'Tax year', 'tyear', 9),
    LST('person', 'Person', 'person', 10),
    CA('miss_key', 'Missing receipt key', 'num', G('deduction_id', 'IF({col:receipt}=%s,"",{col:amount}+(100000-MATCH({col:deduction_id},%s,0))/10000000)' % (YES, DEDR('deduction_id'))), 11)],
    D.deductions_d(), 400, [A('receipt', '= ' + NO, 'warn')]))
# 12 deductions by category -----------------------------------------------------------------------------------------------
def DC(f, extra=''): return 'SUMIFS(%s,%s,{col:tax_year},%s,{col:category}%s)' % (DEDR('amount'), DEDR('tax_year'), DEDR('category'), extra)
def DCN(extra=''): return 'COUNTIFS(%s,{col:tax_year},%s,{col:category}%s)' % (DEDR('tax_year'), DEDR('category'), extra)
DCT = lambda c: R('ded_cat', c)
tables.append(T('ded_cat', 'Deductions by category', 'Deduction Records by Category and Tax Year',
    'Each tax year and category: the total recorded, the records, receipts kept and missing; no claim is made about what can be claimed.', [
    C('row_id', 'Row ID', 'text', 8, required=True), LST('tax_year', 'Tax year', 'tyear', 9), LST('category', 'Category', 'dedcat', 20),
    CA('total', 'Total recorded', 'money', DC(0), 12), CA('records', 'Records', 'int', DCN(), 9), CA('kept', 'Receipts kept', 'int', DCN(',%s,%s' % (DEDR('receipt'), YES)), 9),
    CA('missing', 'Receipts missing', 'int', DCN(',%s,%s' % (DEDR('receipt'), NO)), 9), CA('missing_amount', 'Amount without receipt', 'money', DC(0, ',%s,%s' % (DEDR('receipt'), NO)), 13),
    CA('kept_share', 'Share with receipt', 'pct', 'IF({col:records}=0,0,{col:kept}/{col:records})', 10),
    CA('total_year', 'Total for the tax year', 'money', 'SUMIFS(%s,%s,{col:tax_year})' % (DEDR('amount'), DEDR('tax_year')), 13),
    CA('kept_year', 'Receipts kept, tax year', 'int', 'COUNTIFS(%s,{col:tax_year},%s,%s)' % (DEDR('tax_year'), DEDR('receipt'), YES), 10),
    CA('missing_year', 'Receipts missing, tax year', 'int', 'COUNTIFS(%s,{col:tax_year},%s,%s)' % (DEDR('tax_year'), DEDR('receipt'), NO), 10), HH(), N2(), PHC('p2', 'Partner 2 phone'), PHC('tax', 'Tax preparer phone')],
    D.ded_cat_d(), 50, [A('missing', '> 0', 'warn')]))
# 13 missing receipts ------------------------------------------------------------------------------------------------------
def MRX(c): return 'IF({col:mkey}="","",INDEX(%s,MATCH({col:mkey},%s,0)))' % (DEDR(c), DEDR('miss_key'))
tables.append(T('missing_receipts', 'Missing receipts', 'Missing Receipts, Biggest First',
    'The records without a receipt, the biggest amount first, with the person and the first thing to try; it fills in from the Deduction records sheet.', [
    C('rank', 'Rank', 'int', 7, required=True), CA('mkey', 'Ranking key', 'num', 'IFERROR(LARGE(%s,{col:rank}),"")' % DEDR('miss_key'), 10),
    CA('date', 'Date', 'date', MRX('date'), 11), CA('description', 'Description', 'text', MRX('description'), 26), CA('amount', 'Amount', 'money', MRX('amount'), 11),
    CA('person', 'Person', 'text', MRX('person'), 10), CA('tax_year', 'Tax year', 'text', MRX('tax_year'), 9),
    CA('fix', 'Fix', 'text', 'IF({col:mkey}="","",IF({col:amount}>={set:receipt_big},%s,IF({col:amount}>={set:receipt_big}/3,%s,%s)))' % (st('Ask the seller for a copy'), st('Find the card or bank statement'), st('Find it in your own records')), 26)],
    D.missing_receipts_d(), 50, [A('amount', '>= {set:receipt_big}', 'warn')]))
# 14 tax set-aside ----------------------------------------------------------------------------------------------------------
SA = lambda c: R('set_aside', c)
EP = lambda c: R('est_payments', c)
tables.append(T('set_aside', 'Tax set-aside', 'Tax Set-aside, Income and Running Balance',
    'Each freelance payment received, what you moved to the set-aside and what the percentage suggests; the running balance fills in. Confirm with your adviser.', [
    C('sa_id', 'Row ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), CA('month', 'Month', 'date', 'IF({col:date}="","",DATE(YEAR({col:date}),MONTH({col:date}),1))', 11), LST('source', 'Source', 'isource', 13),
    C('amount', 'Amount received', 'money', 13), C('moved', 'Moved to set-aside', 'money', 13),
    CA('suggested', 'Suggested by the percentage', 'money', G('sa_id', 'ROUND({col:amount}*{set:set_aside_pct},2)'), 14), CA('difference', 'Moved above (+) or below (-)', 'money', G('sa_id', '{col:moved}-{col:suggested}'), 14),
    CA('balance', 'Running balance', 'money', G('sa_id', 'SUMIFS(%s,%s,"<="&{col:date})-SUMIFS(%s,%s,"<="&MIN({col:date},{today}))' % (SA('moved'), SA('date'), EP('payment'), EP('date'))), 13)],
    D.set_aside_d(), 150))
# 15 estimated payments ----------------------------------------------------------------------------------------------------
tables.append(T('est_payments', 'Estimated payments', 'Estimated Payments to Your Tax Office',
    'The dates of your estimated payments (type the dates your tax office gives you) and the amounts; the set-aside balance before and after each, whether it is covered and the next payment fill in.', [
    C('pay_id', 'Payment ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('payment', 'Payment', 'money', 11), LST('tax_year', 'Payment year', 'pyear', 10),
    CA('balance_before', 'Balance before', 'money', G('pay_id', 'SUMIFS(%s,%s,"<="&MIN({col:date},{today}))+IF({col:date}>{today},SUMIFS(%s,%s,">="&EDATE({today},-12))/12*({col:date}-{today})/30.4375,0)-SUMIFS(%s,%s,"<"&{col:date})' % (SA('moved'), SA('date'), SA('moved'), SA('date'), EP('payment'), EP('date'))), 13),
    CA('balance_after', 'Balance after', 'money', G('pay_id', '{col:balance_before}-{col:payment}'), 13),
    CA('status', 'Status', 'text', G('pay_id', 'IF({col:date}<={today},%s,IF({col:balance_before}>={col:payment},%s,%s))' % (st('Paid'), st('Covered'), st('Short'))), 10),
    CA('is_next', 'Next payment', 'int', G('pay_id', 'IF(AND({col:date}>{today},COUNTIFS(%s,">"&{today},%s,"<"&{col:date})=0),1,0)' % (EP('date'), EP('date'))), 9),
    CA('next_due', 'Next payment date', 'date', 'IFERROR(SMALL(%s,COUNTIF(%s,"<="&{today})+1),"")' % (EP('date'), EP('date')), 12),
    CA('balance', 'Set-aside balance now', 'money', G('pay_id', BAL_NOW), 13), HH(), N2(), PHC('p2', 'Partner 2 phone'), PHC('tax', 'Tax preparer phone')],
    D.est_payments_d(), 50, [A('status', '= ' + st('Short'), 'bad'), A('status', '= ' + st('Covered'), 'good')]))
# 16 year review ---------------------------------------------------------------------------------------------------------------
YM = lambda c: R('year_months', c)
def W(c, win): return 'SUMIFS(%s,%s,1)' % (YM(c), YM(win))
def SPMAX(a, b): return 'SUMPRODUCT(MAX((%s>=EDATE(%s,%d))*(%s<EDATE(%s,%d))*(%s+%s+%s)))' % (YM('month'), MS, a, YM('month'), MS, b, YM('fixed'), YM('variable'), YM('wants'))
def NWAT(k): return 'SUMIFS(%s,%s,EDATE(%s,%d))' % (YM('net_worth'), YM('month'), MS, k)
def yitem_formula(win):
    e = -1 if win == 'last12' else -13
    a, b = (-12, 0) if win == 'last12' else (-24, -12)
    cases = [('Take-home income', W('take_home', win)), ('Partner 1 paychecks', W('paycheck', win)), ('Freelance and side income', '%s-%s' % (W('take_home', win), W('paycheck', win))),
             ('Counted spending', W('spending', win)), ('Fixed bills', W('fixed', win)), ('Variable needs', W('variable', win)), ('Wants', W('wants', win)), ('Saved into goals', W('saved', win)),
             ('Retirement contributions', W('retirement', win)), ('Total saved', W('total_saved', win)), ('Savings rate, percent', 'IFERROR(100*%s/%s,0)' % (W('total_saved', win), W('basis', win))),
             ('Debt payments', W('debt_paid', win)), ('Interest paid', W('interest_paid', win)), ('Principal repaid', '%s-%s' % (W('debt_paid', win), W('interest_paid', win))),
             ('Net worth at the end', NWAT(e)), ('Net worth change', ('%s-%s' % (NWAT(-1), NWAT(-13))) if win == 'last12' else '""'), ('Average take-home a month', '%s/12' % W('take_home', win)),
             ('Average spending a month', '%s/12' % W('spending', win)), ('Highest spending month', SPMAX(a, b)),
             ('Months at or above your savings target', 'COUNTIFS(%s,1,%s,">="&{set:savings_rate_target})' % (YM(win), YM('savings_rate')))]
    f = '""'
    for lab, fx in reversed(cases): f = 'IF({col:item}={list:yitem.%s},%s,%s)' % (key('yitem', lab), fx, f)
    return f
RATE_ALL = 'IFERROR(SUMIFS(%s,%s,1)/SUMIFS(%s,%s,1),0)' % (YM('total_saved'), YM('last12'), YM('basis'), YM('last12'))
NWCH = '(%s-%s)' % (NWAT(-1), NWAT(-13))
tables.append(T('year_review', 'Year review', 'Year in Review, Last 12 Months against the 12 Before',
    'Income, spending, saving, debt, interest and net worth for the last 12 complete months against the 12 months before; the change and the direction fill in from the Year by month sheet.', [
    LST('item', 'Item', 'yitem', 36, required=True), CA('this_year', 'Last 12 months', 'num', yitem_formula('last12'), 14), CA('last_year', 'The 12 months before', 'num', yitem_formula('prev12'), 14),
    CA('change', 'Change', 'num', 'IF({col:last_year}="","",{col:this_year}-{col:last_year})', 12), CA('change_pct', 'Change, percent', 'pct', 'IF({col:last_year}="","",IF({col:last_year}=0,0,{col:change}/ABS({col:last_year})))', 11),
    CA('note', 'Direction', 'text', 'IF({col:change}="","",IF({col:change}>0,%s,IF({col:change}<0,%s,%s)))' % (st('Higher'), st('Lower'), st('Same')), 10),
    CA('savings_rate_all', 'Savings rate, last 12 months', 'pct', RATE_ALL, 12), CA('nw_change_all', 'Net worth change, last 12 months', 'money', NWCH, 14), HH(), N1(), N2(),
    PHC('p1', 'Partner 1 phone'), PHC('p2', 'Partner 2 phone')],
    D.year_review_d(), 50))
# 17 category changes ----------------------------------------------------------------------------------------------------------------
CCr = lambda c: R('category_changes', c)
tables.append(T('category_changes', 'Category changes', 'Category Changes against Last Year',
    'Every category: the last 12 months and the 12 months before (paste the totals from Planned against Actual), the change, the share of all rises and the rank of the rise.', [
    LST('category', 'Category', 'category', 24, required=True), LST('group', 'Group', 'group', 15), C('this_year', 'Last 12 months', 'money', 13), C('last_year', 'The 12 months before', 'money', 14),
    CA('change', 'Change', 'money', G('category', '{col:this_year}-{col:last_year}'), 12), CA('change_pct', 'Change, percent', 'pct', G('category', 'IF({col:last_year}=0,0,{col:change}/{col:last_year})'), 11),
    CA('share_rise', 'Share of all rises', 'pct', G('category', 'IF({col:change}>0,{col:change}/SUMIFS(%s,%s,">0"),0)' % (CCr('change'), CCr('change'))), 11),
    CA('rise_key', 'Ranking key', 'num', G('category', '{col:change}+(100-MATCH({col:category},%s,0))/100000' % CCr('category')), 10),
    CA('rise_rank', 'Rank of the rise', 'int', G('category', 'COUNTIFS(%s,">"&{col:rise_key})+1' % CCr('rise_key')), 9)],
    D.category_changes_d(), 50, [A('change', '> 0', 'warn')]))
# 18 goals reached -----------------------------------------------------------------------------------------------------------------------
tables.append(T('goals_reached', 'Goals reached', 'Goals and Loans, How Far You Got',
    'Each savings goal and each instalment loan: the target (or the original loan), what is saved or repaid, the share and whether it is reached.', [
    C('item_id', 'Item ID', 'text', 9, required=True), C('item', 'Item', 'text', 28), LST('kind', 'Kind', 'gdkind', 15), C('target', 'Target or original loan', 'money', 14), C('saved', 'Saved or repaid', 'money', 13),
    CA('share', 'Share reached', 'pct', G('item_id', 'IF({col:target}>0,MIN(1,{col:saved}/{col:target}),0)'), 10), CA('left', 'Still to go', 'money', G('item_id', 'MAX(0,{col:target}-{col:saved})'), 12),
    CA('reached', 'Reached', 'text', G('item_id', 'IF({col:share}>=1,%s,IF({col:share}>=0.8,%s,IF({col:share}>=0.4,%s,%s)))' % (st('Reached'), st('Almost there'), st('In progress'), st('Early days'))), 12)],
    D.goals_d(), 50, [A('reached', '= ' + st('Reached'), 'good')]))
# 19 next-year plan ----------------------------------------------------------------------------------------------------------------------
NP = lambda c: R('next_year_plan', c)
tables.append(T('next_year_plan', 'Next-year plan', 'Next-year Plan from Last Year\'s Actuals',
    'Each category: last year\'s actual, a change you type, the plan for next year, the plan a month and the plan for each paycheck; it fills in from the Category changes sheet.', [
    LST('category', 'Category', 'category', 24, required=True), C('change', 'Change you type', 'pct', 12),
    CA('group', 'Group', 'text', LKT('category_changes.group', 'category_changes.category', 'category'), 14), CA('last_year', 'Last 12 months actual', 'money', G('category', LKN('category_changes.this_year', 'category_changes.category', 'category')), 13),
    CA('plan', 'Plan for next year', 'money', G('category', 'ROUND({col:last_year}*(1+{col:change}),2)'), 13), CA('diff', 'More (+) or less (-)', 'money', G('category', '{col:plan}-{col:last_year}'), 12),
    CA('per_month', 'Plan a month', 'money', G('category', '{col:plan}/12'), 11), CA('per_paycheck', 'Plan for each paycheck', 'money', G('category', '{col:plan}/{set:pay_per_year}'), 12),
    CA('plan_total', 'Plan total', 'money', 'SUM(%s)' % NP('plan'), 13), CA('ready_by', 'Ready for changes by', 'date', '{today}+14', 12), HH(), N2(), PHC('p2', 'Partner 2 phone')],
    D.next_year_d(), 50))
# 20 year by month --------------------------------------------------------------------------------------------------------------------------
def numcol(key_, label, rows, w=12):
    vals = [r[key_] for r in rows]
    return C(key_, label, 'money' if (len(set(vals)) >= 3 and max(vals.count(v) for v in set(vals)) <= 0.5 * len(vals)) else 'int', w)
YMR = D.year_months_d()
tables.append(T('year_months', 'Year by month', 'Year by Month, Income, Spending and Net Worth',
    'One row a month: take-home, spending by group, saving, debt and net worth (paste them in); the savings rate and net worth change fill in.', [
    C('month', 'Month', 'date', 11, required=True), numcol('take_home', 'Take-home pay', YMR, 12), numcol('set_aside', 'Moved to tax set-aside', YMR, 12), numcol('paycheck', 'Partner 1 paychecks', YMR, 12),
    numcol('fixed', 'Fixed bills', YMR), numcol('variable', 'Variable needs', YMR), numcol('wants', 'Wants', YMR), numcol('saved', 'Saved into goals', YMR), numcol('retirement', 'Retirement', YMR, 11),
    numcol('debt_paid', 'Debt payments', YMR), numcol('debt_extra', 'Extra debt payments', YMR), numcol('interest_paid', 'Interest paid', YMR), numcol('net_worth', 'Net worth at month end', YMR, 13),
    CA('spending', 'Counted spending', 'money', G('month', '{col:fixed}+{col:variable}+{col:wants}'), 12), CA('other_income', 'Freelance and other take-home', 'money', G('month', '{col:take_home}-{col:paycheck}'), 13), CA('total_saved', 'Total saved', 'money', G('month', '{col:saved}+{col:retirement}+{col:debt_extra}'), 12),
    CA('basis', 'Take-home less set-aside plus retirement', 'money', G('month', '{col:take_home}-{col:set_aside}+{col:retirement}'), 14),
    CA('savings_rate', 'Savings rate', 'pct', G('month', 'IF({col:basis}>0,{col:total_saved}/{col:basis},0)'), 10),
    CA('nw_change', 'Net worth change', 'money', G('month', 'IF(COUNTIFS(%s,EDATE({col:month},-1))=0,0,{col:net_worth}-SUMIFS(%s,%s,EDATE({col:month},-1)))' % (YM('month'), YM('net_worth'), YM('month'))), 12),
    CA('last12', 'In the last 12 months', 'int', G('month', 'IF(AND({col:month}>=EDATE(%s,-12),{col:month}<%s),1,0)' % (MS, MS)), 9),
    CA('prev12', 'In the 12 months before', 'int', G('month', 'IF(AND({col:month}>=EDATE(%s,-24),{col:month}<EDATE(%s,-12)),1,0)' % (MS, MS)), 9)],
    YMR, 50))
assert len(tables) == 20, len(tables)
