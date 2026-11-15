"""Childcare center suite part 5: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc5_lists import *
import cc5_data as D


def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def R(t, c): return '{range:%s.%s}' % (t, c)
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def SM_(t, c): return 'SUM(%s)' % R(t, c)
def PH(p): return '"%s"' % p
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
UNPAID, PART, WO = tok('istatus', 'Unpaid'), tok('istatus', 'Part paid'), tok('istatus', 'Written off')
SHORT, EXPECTED = tok('govstatus', 'Short-paid'), tok('govstatus', 'Expected')
KEPT, BROKEN, PENDING = tok('outcome', 'Kept'), tok('outcome', 'Broken'), tok('outcome', 'Pending')
HELD = tok('depstatus', 'Held'); UPC = tok('done2', 'Upcoming'); PAID2 = tok('done2', 'Paid'); PAYROLL = tok('billcat', 'Payroll')
CASH, ACARD, ABANK, XFER = tok('method', 'Cash'), tok('method', 'Autopay card'), tok('method', 'Autopay bank'), tok('method', 'Bank transfer')
DEPOSIT = tok('paykind', 'Deposit')
def W(t, c, m, n=1): return '%s,">="&%s,%s,"<"&EDATE(%s,%d)' % (R(t, c), m, R(t, c), m, n)

settings = [
    S('company', 'Your center name', 'text', COMPANY), S('card_fee_pct', 'Card processing fee, share of a card payment', 'pct', CARD_FEE_PCT),
    S('cash_floor', 'Cash floor, the lowest balance you want', 'money', CASH_FLOOR), S('tax_set_aside_pct', 'Tax set-aside share of profit, confirm with your adviser', 'pct', TAX_SET_ASIDE_PCT),
    S('call_day', 'Days overdue when you call the family', 'int', 8), S('plan_day', 'Days overdue when you offer a payment plan', 'int', 21),
    S('pause_day', 'Days overdue when you give notice to pause care', 'int', 56), S('over_days_limit', 'Days overdue that count as a long balance', 'int', 60),
    S('gov_wait_days', 'Days to wait for the payer before you bill the family share', 'int', 30), S('leave_week', 'Week they leave in the leave case', 'int', 4), S('late_grace_days', 'Days after the due date before a payment counts as late', 'int', 7),
    S('autopay_target', 'Autopay share of tuition you want', 'pct', 0.65),     S('hour_value', 'Value of one hour of billing time', 'money', 24), S('best_pct', 'Best case: tuition above the base forecast', 'pct', 0.03),
    S('worst_pct', 'Worst case: tuition below the base forecast', 'pct', 0.05), S('leave_families', 'Families that leave in the leave case', 'int', 3),
    S('extra_draw', 'Quarterly extra owner draw', 'money', OWNER_EXTRA), S('extra_draw_on', 'Date of the next extra draw', 'date', iso(min(d for d in (dt.date(y, m, 15) for y in (TODAY.year, TODAY.year + 1) for m in (3, 6, 9, 12)) if d > TODAY))),
    S('billing_name', 'Billing contact', 'text', ASSISTANT_DIRECTOR), S('director_name', 'Owner-director', 'text', OWNER),
]
assert 3 <= len(settings) <= 20

tables = []
IN_ = lambda t, c: R(t, c)

# 1 invoices ---------------------------------------------------------------------------------------------------
BAND_F = ('IF({col:open_balance}=0,%s,IF({col:days_overdue}<=30,%s,IF({col:days_overdue}<=60,%s,IF({col:days_overdue}<=90,%s,%s))))'
          % (V('Settled'), tok('band', '0-30'), tok('band', '31-60'), tok('band', '61-90'), tok('band', '90+')))
tables.append(T('invoices', 'Invoices', 'Invoices: open and recent, with days overdue',
    'One row per invoice: type the family, dates, amounts, the paid amount and status; the family share, the open balance, the days overdue and the aging band fill in by themselves.', [
    C('invoice_id', 'Invoice ID', 'text', 10, required=True), REF('family', 'Family', 'families.family', 22), LST('cycle', 'Cycle', 'cycle', 9), C('issued_on', 'Issued on', 'date', 11), C('due_date', 'Due date', 'date', 11),
    C('amount', 'Invoice amount', 'money', 12), C('gov_expected', 'Government expected', 'money', 12), C('paid_amount', 'Paid amount', 'money', 11), C('paid_on', 'Paid on', 'date', 11),
    LST('status', 'Status', 'istatus', 11),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:issued_on}),MONTH({col:issued_on}),1)', 11), CA('parent_due', 'Parent due', 'money', '{col:amount}-{col:gov_expected}', 11),
    CA('open_balance', 'Open balance', 'money', 'IF(OR({col:status}=%s,{col:status}=%s),MAX(0,ROUND({col:parent_due}-{col:paid_amount},2)),0)' % (UNPAID, PART), 11),
    CA('days_overdue', 'Days overdue', 'int', 'IF({col:open_balance}>0,MAX(0,{today}-{col:due_date}),0)', 9),
    CA('band', 'Aging band', 'text', BAND_F, 11),
    CA('late_amount', 'Paid or held late', 'money', 'IF({col:status}=%s,0,IF({col:days_overdue}>{set:late_grace_days},{col:open_balance},0)+IF(AND({col:paid_on}<>"",{col:paid_on}>{col:due_date}+{set:late_grace_days}),{col:paid_amount},0))' % WO, 11),
    CA('is_late', 'Late', 'int', 'IF({col:late_amount}>0,1,0)', 7),
    CA('autopay', 'On autopay', 'int', 'IF(IFERROR(INDEX(%s,MATCH({col:family},%s,0)),%s)=%s,1,0)' % (R('families', 'autopay'), R('families', 'family'), NO, YES), 8),
    CA('written_off', 'Written off', 'money', 'IF({col:status}=%s,MAX(0,ROUND({col:parent_due}-{col:paid_amount},2)),0)' % WO, 11),
    CA('chase_key', 'Chase ranking key value', 'num', 'IF({col:days_overdue}>0,{col:days_overdue}*100000+ROUND({col:open_balance},0)+VALUE(RIGHT({col:invoice_id},5))/100000,"")', 10),
    CA('phone', 'Family phone', 'text', LKT('families.phone', 'families.family', 'family'), 18), CA('acc_phone', 'Accountant phone', 'text', PH(D.ACC_PHONE), 18)],
    D.front(D.invoices_d(), lambda r: r['invoice_id'] == D.ST['overdue_invoice']), 1800, [A('days_overdue', '> 30', 'bad'), A('days_overdue', '> 0', 'warn')]))

# 2 payments ---------------------------------------------------------------------------------------------------
tables.append(T('payments', 'Payments', 'Payments received by date, family and method',
    'One row per payment: type the date, family, invoice, amount, method and kind; the month, the card processing cost and the family phone fill in.', [
    C('payment_id', 'Payment ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('family', 'Family', 'families.family', 22), C('invoice_id', 'Invoice ID', 'text', 10), C('amount', 'Amount', 'money', 11),
    LST('method', 'Method', 'method', 13), LST('kind', 'Kind', 'paykind', 14),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    CA('card_cost', 'Card processing cost', 'money', 'IF({col:method}=%s,ROUND({col:amount}*{set:card_fee_pct},2),0)' % ACARD, 11),
    CA('phone', 'Family phone', 'text', LKT('families.phone', 'families.family', 'family'), 18)], D.front(D.payments_d(), lambda r: r['payment_id'] == D.PAY[-1]['payment_id']), 1800))

# 3 families ---------------------------------------------------------------------------------------------------
HAB = ('IF({col:habit}=%s,0,IF({col:habit}=%s,1,IF({col:habit}=%s,2,3)))' % (tok('habit', 'Prompt'), tok('habit', 'Normal'), tok('habit', 'Slow')))
tables.append(T('families', 'Families', 'Families: billing cycle, pay method and habit',
    'One row per family: type the contact, cycle, pay method, autopay, how they usually pay and any government share; the open balance, days late on average and the risk key fill in.', [
    C('family_id', 'Family ID', 'text', 9, required=True), C('family', 'Family', 'text', 22), C('guardian', 'Guardian', 'text', 22), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
    LST('cycle', 'Cycle', 'cycle', 9), LST('pay_method', 'Pay method', 'method', 13), C('autopay', 'Autopay', 'bool', 8), LST('habit', 'Habit', 'habit', 10), C('gov_share', 'Government share', 'pct', 10),
    C('late_prone', 'Late prone', 'bool', 8), C('first_start', 'First start', 'date', 11),
    CA('active', 'Active', 'int', 'IF(COUNTIFS(%s,{col:family},%s,">"&({today}-35))>0,1,0)' % (R('invoices', 'family'), R('invoices', 'issued_on')), 7),
    CA('open_balance', 'Open balance', 'money', 'SUMIFS(%s,%s,{col:family})' % (R('invoices', 'open_balance'), R('invoices', 'family')), 11),
    CA('paid_year', 'Paid this year', 'money', 'SUMIFS(%s,%s,{col:family},%s,">="&DATE(YEAR({today}),1,1))' % (R('payments', 'amount'), R('payments', 'family'), R('payments', 'date')), 11),
    CA('card_fee', 'Card fee share', 'pct', '{set:card_fee_pct}', 9),
    CA('avg_days_late', 'Days late on average', 'num', 'IFERROR(ROUND(SUMPRODUCT((%s={col:family})*(%s<>"")*(%s>%s)*(%s-%s))/COUNTIFS(%s,{col:family},%s,"<>"),1),0)'
       % (R('invoices', 'family'), R('invoices', 'paid_on'), R('invoices', 'paid_on'), R('invoices', 'due_date'), R('invoices', 'paid_on'), R('invoices', 'due_date'), R('invoices', 'family'), R('invoices', 'paid_on')), 10),
    CA('risk_key', 'Risk ranking key value', 'num', '%s*10+{col:avg_days_late}*3+{col:open_balance}/100*2+IF({col:late_prone}=%s,10,0)+VALUE(RIGHT({col:family_id},3))/100000' % (HAB, YES), 9)],
    D.front(D.families_d(), lambda r: r['family'] == D.ST['overdue_family']), 130, [A('open_balance', '> 1000', 'bad')]))

# 4 aging by family --------------------------------------------------------------------------------------------
INV_OPEN = '((%s=%s)+(%s=%s))' % (R('invoices', 'status'), UNPAID, R('invoices', 'status'), PART)
def BAND_SUM(lo, hi=None):
    c = '%s,{col:family},%s,">%d"' % (R('invoices', 'family'), R('invoices', 'days_overdue'), lo) if lo is not None else ''
    return c
def BS(cond): return 'SUMIFS(%s,%s,{col:family}%s)' % (R('invoices', 'open_balance'), R('invoices', 'family'), cond)
DAYS = R('invoices', 'days_overdue')
EFF = '({col:oldest_days}+7*{col:broken})'
STEP_F = ('IF({col:balance}=0,%s,IF({col:oldest_days}<=0,%s,IF(%s<{set:call_day},%s,IF(%s<{set:plan_day},%s,IF(%s<{set:pause_day},%s,%s)))))'
          % (V('Settled'), V('Not due yet'), EFF, V('Friendly reminder'), EFF, V('Call today'), EFF, V('Offer a payment plan'), V('Pause care after notice')))
tables.append(T('aging', 'Aging by Family', 'A/R aging of balances by family',
    'Type a family that owes money; its balance, the aging bands, oldest days, open invoices, open promise and next step in the reminder ladder fill in.', [
    C('ageing_id', 'Aging ID', 'text', 9, required=True), REF('family', 'Family', 'families.family', 22),
    CA('cycle', 'Cycle', 'text', LKT('families.cycle', 'families.family', 'family'), 9), CA('habit', 'Habit', 'text', LKT('families.habit', 'families.family', 'family'), 10),
    CA('balance', 'Balance', 'money', BS(''), 11), CA('d0_30', 'Days 0-30', 'money', BS(',%s,"<=30"' % DAYS), 11), CA('d31_60', 'Days 31-60', 'money', BS(',%s,">30",%s,"<=60"' % (DAYS, DAYS)), 11),
    CA('d61_90', 'Days 61-90', 'money', BS(',%s,">60",%s,"<=90"' % (DAYS, DAYS)), 11), CA('d90_plus', 'Days 90+', 'money', BS(',%s,">90"' % DAYS), 11),
    CA('oldest_days', 'Oldest days', 'int', 'MAX(0,SUMPRODUCT(MAX((%s={col:family})*%s*({today}-%s))))' % (R('invoices', 'family'), INV_OPEN, R('invoices', 'due_date')), 9),
    CA('open_invoices', 'Open invoices', 'int', 'COUNTIFS(%s,{col:family},%s,%s)+COUNTIFS(%s,{col:family},%s,%s)' % (R('invoices', 'family'), R('invoices', 'status'), UNPAID, R('invoices', 'family'), R('invoices', 'status'), PART), 9),
    CA('over_limit', 'Over your days limit', 'money', BS(',%s,">"&{set:over_days_limit}' % DAYS), 11), CA('under_limit', 'Within your days limit', 'money', '{col:balance}-{col:over_limit}', 11),
    CA('broken', 'Promises broken', 'int', 'COUNTIFS(%s,{col:family},%s,%s)' % (R('promises', 'family'), R('promises', 'outcome'), BROKEN), 9),
    CA('next_promise', 'Open promise date', 'date', 'IF(SUMPRODUCT(MAX((%s={col:family})*(%s=%s)*%s))=0,"",SUMPRODUCT(MAX((%s={col:family})*(%s=%s)*%s)))'
       % (R('promises', 'family'), R('promises', 'outcome'), PENDING, R('promises', 'promised_on'), R('promises', 'family'), R('promises', 'outcome'), PENDING, R('promises', 'promised_on')), 11),
    CA('step', 'Next step', 'text', STEP_F, 22),
    CA('score_key', 'Act-first ranking key value', 'num', '{col:balance}+{col:oldest_days}*20+{col:broken}*100+VALUE(RIGHT({col:ageing_id},3))/100000', 10),
    CA('ad_phone', 'Billing phone', 'text', PH(D.AD_PHONE), 18), CA('owner_phone', 'Owner phone', 'text', PH(D.OWNER_PHONE), 18),
    CA('phone', 'Family phone', 'text', LKT('families.phone', 'families.family', 'family'), 18)],
    D.aging_d(), 50, [A('oldest_days', '> 55', 'bad'), A('oldest_days', '> 20', 'warn')]))

# 5 aging by month ---------------------------------------------------------------------------------------------
tables.append(T('aging_month', 'Aging by Month', 'Aging of balances by month and band',
    'One row per month and band: type the month-end amount owed in each band; the month total, the band share and the latest-month flag fill in.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('band', 'Band', 'band', 9), C('amount', 'Amount', 'money', 12),
    CA('month_total', 'Month total', 'money', 'SUMIFS(%s,%s,{col:month})' % (R('aging_month', 'amount'), R('aging_month', 'month')), 12),
    CA('share', 'Band share', 'pct', 'IF({col:month_total}>0,{col:amount}/{col:month_total},0)', 9),
    CA('is_latest', 'Latest month', 'int', 'IF({col:month}=MAX(%s),1,0)' % R('aging_month', 'month'), 8)], D.aging_month_d(), 80))

# 6 promises ---------------------------------------------------------------------------------------------------
tables.append(T('promises', 'Promises', 'Payment promises and whether they were kept',
    'One row per promise to pay: type the date, family, invoice, amount, how it was made and the outcome; the days to the promise and a check fill in.', [
    C('promise_id', 'Promise ID', 'text', 10, required=True), C('promised_on', 'Promised on', 'date', 11), REF('family', 'Family', 'families.family', 22), C('invoice_id', 'Invoice ID', 'text', 10),
    C('promised_amount', 'Promised amount', 'money', 12), LST('method', 'Method', 'pmethod', 9), LST('outcome', 'Outcome', 'outcome', 10),
    CA('due_in', 'Days to promise', 'int', '{col:promised_on}-{today}', 9),
    CA('promise_flag', 'Promise check', 'text', 'IF({col:outcome}=%s,%s,IF({col:outcome}=%s,%s,IF({col:due_in}<0,%s,IF({col:due_in}<=7,%s,%s))))' % (KEPT, V('Kept'), BROKEN, V('Missed'), V('Overdue promise'), V('Due this week'), V('Later')), 16),
    CA('settled', 'Settled', 'int', 'IF({col:outcome}=%s,0,1)' % PENDING, 7), CA('kept_n', 'Kept', 'int', 'IF({col:outcome}=%s,1,0)' % KEPT, 7),
    CA('ad_phone', 'Billing phone', 'text', PH(D.AD_PHONE), 18), CA('phone', 'Family phone', 'text', LKT('families.phone', 'families.family', 'family'), 18)],
    D.front(D.promises_d(), lambda r: r['family'] == D.ST['overdue_family'] and r['outcome'] == key('outcome', 'Broken')), 60, [A('outcome', '= ' + BROKEN, 'bad'), A('outcome', '= ' + PENDING, 'warn')]))

# 7 plans (3 columns) ------------------------------------------------------------------------------------------
tables.append(T('plans', 'Payment Plans', 'Payment plans: balance and number of instalments',
    'One row per plan: type the plan number, the balance and the number of instalments; the dates and amounts are on the Plan Instalments sheet.', [
    C('plan_id', 'Plan ID', 'text', 9, required=True), C('balance', 'Balance', 'money', 11), C('instalments', 'Instalments', 'int', 10)], D.plans_d(), 50))

# 8 instalments ------------------------------------------------------------------------------------------------
tables.append(T('instalments', 'Plan Instalments', 'Plan instalments with due dates and status',
    'One row per instalment: type the plan, family, number, first due date and the date paid; the due date, amount, status and whether the plan is still open fill in.', [
    C('inst_id', 'Instalment ID', 'text', 10, required=True), REF('plan', 'Plan', 'plans.plan_id', 9), REF('family', 'Family', 'families.family', 22), C('number', 'Number', 'int', 8),
    C('first_due', 'First due', 'date', 11), C('paid_on', 'Paid on', 'date', 11),
    CA('due_date', 'Due date', 'date', 'EDATE({col:first_due},{col:number}-1)', 11),
    CA('plan_instalments', 'Instalments in plan', 'int', LKN('plans.instalments', 'plans.plan_id', 'plan'), 9),
    CA('amount', 'Instalment', 'money', 'IFERROR(IF({col:number}={col:plan_instalments},ROUND(INDEX(%s,MATCH({col:plan},%s,0))-ROUND(INDEX(%s,MATCH({col:plan},%s,0))/{col:plan_instalments},2)*({col:number}-1),2),ROUND(INDEX(%s,MATCH({col:plan},%s,0))/{col:plan_instalments},2)),0)'
       % ((R('plans', 'balance'), R('plans', 'plan_id')) * 3), 11),
    CA('paid_amount', 'Paid', 'money', 'IF({col:paid_on}<>"",{col:amount},0)', 11),
    CA('status', 'Status', 'text', 'IF({col:paid_on}<>"",%s,IF({col:due_date}<{today},%s,IF({col:due_date}<={today}+7,%s,%s)))' % (V('Paid'), V('Late instalment'), V('Due this week'), V('Planned')), 15),
    CA('closes_plan', 'Plan open', 'int', 'IF(AND({col:number}={col:plan_instalments},{col:paid_on}=""),1,0)', 8),
    CA('phone', 'Family phone', 'text', LKT('families.phone', 'families.family', 'family'), 18)], D.front(D.instalments_d(), lambda r: r['plan'] == 'PP-04' and r['number'] == 1), 50, [A('status', '= ' + V('Late instalment'), 'bad')]))

# 9 government payments ----------------------------------------------------------------------------------------
tables.append(T('gov', 'Government Payments', 'Government childcare payments: expected, received and status',
    'One row per family and month: type the expected and received amounts, the due date, the date paid and the status; the gap, days since, next step and family share fill in.', [
    C('gov_id', 'Payment ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), REF('family', 'Family', 'families.family', 22), C('expected', 'Expected', 'money', 11), C('received', 'Received', 'money', 11),
    C('due_on', 'Due on', 'date', 11), C('paid_on', 'Paid on', 'date', 11), LST('status', 'Status', 'govstatus', 11),
    CA('gap', 'Gap', 'money', 'IF({col:status}=%s,ROUND({col:expected}-{col:received},2),0)' % SHORT, 10),
    CA('late', 'Late', 'int', 'IF(AND({col:status}=%s,{col:due_on}<{today}),1,0)' % EXPECTED, 7),
    CA('matched', 'Expected, resolved', 'money', 'IF({col:status}=%s,0,{col:expected})' % EXPECTED, 11),
    CA('days_since', 'Days since', 'int', 'IF({col:status}=%s,{today}-{col:paid_on},IF({col:status}=%s,MAX(0,{today}-{col:due_on}),0))' % (SHORT, EXPECTED), 8),
    CA('family_share', 'Family share', 'money', 'IFERROR(IF(INDEX(%s,MATCH({col:family},%s,0))>0,ROUND({col:expected}*(1-INDEX(%s,MATCH({col:family},%s,0)))/INDEX(%s,MATCH({col:family},%s,0)),2),0),0)' % ((R('families', 'gov_share'), R('families', 'family')) * 3), 10),
    CA('step', 'Next step', 'text', 'IF({col:status}=%s,IF({col:days_since}>{set:gov_wait_days},%s,%s),IF({col:late}=1,%s,IF({col:status}=%s,%s,%s)))' % (SHORT, V('Bill the family share'), V('Chase the payer'), V('Chase the payer'), EXPECTED, V('Not due yet'), V('Matched')), 20),
    CA('chase_key', 'Chase ranking key value', 'num', 'IF(OR({col:status}=%s,{col:late}=1),IF({col:status}=%s,{col:gap},{col:expected})*100+{col:days_since}+VALUE(RIGHT({col:gov_id},4))/100000,"")' % (SHORT, SHORT), 10),
    CA('ad_phone', 'Billing phone', 'text', PH(D.AD_PHONE), 18), CA('phone', 'Family phone', 'text', LKT('families.phone', 'families.family', 'family'), 18)],
    D.front(D.gov_d(), lambda r: r['gov_id'] == D.ST['gov_id']), 400, [A('status', '= ' + SHORT, 'bad'), A('late', '= 1', 'warn')]))

# 10 government reconciliation by month -----------------------------------------------------------------------
def GM(c, extra=''): return 'SUMIFS(%s,%s,{col:month}%s)' % (R('gov', c), R('gov', 'month'), extra)
tables.append(T('gov_month', 'Government Reconciliation', 'Government payments reconciled by month',
    'One row per month: type the month; expected, received, the gap, items short, items late and the match share fill in from the Government Payments sheet.', [
    C('gm_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11),
    CA('expected', 'Expected', 'money', GM('expected'), 11), CA('matched', 'Expected, resolved', 'money', GM('matched'), 11), CA('received', 'Received', 'money', GM('received'), 11),
    CA('gap', 'Gap', 'money', '{col:matched}-{col:received}', 10),
    CA('items_short', 'Items short', 'int', 'COUNTIFS(%s,{col:month},%s,%s)' % (R('gov', 'month'), R('gov', 'status'), SHORT), 8),
    CA('items_late', 'Items late', 'int', GM('late'), 8), CA('items_waiting', 'Items waiting', 'int', 'COUNTIFS(%s,{col:month},%s,%s)' % (R('gov', 'month'), R('gov', 'status'), EXPECTED), 8),
    CA('match_share', 'Received of resolved', 'pct', 'IF({col:matched}>0,{col:received}/{col:matched},0)', 10),
    CA('flag', 'Month check', 'text', 'IF({col:gap}>0.005,%s,IF({col:items_waiting}>0,%s,%s))' % (V('Gap to chase'), V('Waiting for payer'), V('Matched')), 18),
    CA('ad_phone', 'Billing phone', 'text', PH(D.AD_PHONE), 18)], D.front(D.gov_month_d(), lambda r: r['month'] == D.ST['gov_month']), 50, [A('gap', '> 0.01', 'bad')]))

# 11 deposits --------------------------------------------------------------------------------------------------
tables.append(T('deposits', 'Deposits', 'Deposits held, applied and refunded',
    'One row per deposit: type the child, family, amount, date received, status, date settled and the notice days; the amount held, days held, refund date and family phone fill in.', [
    C('deposit_id', 'Deposit ID', 'text', 10, required=True), C('child_id', 'Child ID', 'text', 9), C('child', 'Child', 'text', 22), REF('family', 'Family', 'families.family', 22), C('amount', 'Amount', 'money', 11),
    C('received_on', 'Received on', 'date', 11), LST('status', 'Status', 'depstatus', 10), C('settled_on', 'Settled on', 'date', 11), C('notice_days', 'Notice days', 'int', 9),
    CA('held', 'Held now', 'money', 'IF({col:status}=%s,{col:amount},0)' % HELD, 11),
    CA('days_held', 'Days held', 'int', 'IF({col:settled_on}<>"",{col:settled_on},{today})-{col:received_on}', 9),
    CA('refund_on', 'Refund date', 'date', 'IF({col:settled_on}<>"",{col:settled_on},{today}+14)', 11),
    CA('phone', 'Family phone', 'text', LKT('families.phone', 'families.family', 'family'), 18)], D.front(D.deposits_d(), lambda r: r['status'] == key('depstatus', 'Held') and r['received_on'] > ago(60)), 140))

# 12 cash by month ---------------------------------------------------------------------------------------------
tables.append(T('cash', 'Cash by Month', 'Cash by month: money in, money out and closing balance',
    'One row per month: type the opening cash and what came in and went out; cash in, cash out, closing cash, the cash payments counted and the floor check fill in.', [
    C('cash_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('opening', 'Opening cash', 'money', 12), C('parent_payments', 'Parent payments', 'money', 12),
    C('government_payments', 'Government payments', 'money', 12), C('pay_out', 'Payroll out', 'money', 12), C('expenses_out', 'Expenses out', 'money', 12), C('tax_set_aside', 'Tax set aside', 'money', 11),
    C('deposit_refunds', 'Deposit refunds', 'money', 11), C('owner_extra', 'Extra owner draw', 'int', 11),
    CA('cash_in', 'Cash in', 'money', '{col:parent_payments}+{col:government_payments}', 12),
    CA('cash_out', 'Cash out', 'money', '{col:pay_out}+{col:expenses_out}+{col:tax_set_aside}+{col:deposit_refunds}+{col:owner_extra}', 12),
    CA('closing', 'Closing cash', 'money', '{col:opening}+{col:cash_in}-{col:cash_out}', 12),
    CA('cash_taken', 'Cash payments counted', 'money', 'SUMIFS(%s,%s,%s)' % (R('payments', 'amount'), W('payments', 'date', '{col:month}'), R('payments', 'method'), CASH) if False else
       'SUMIFS(%s,%s,%s,%s)' % (R('payments', 'amount'), W('payments', 'date', '{col:month}'), R('payments', 'method'), CASH), 11),
    CA('above_floor', 'Above the floor', 'money', '{col:closing}-{set:cash_floor}', 11),
    CA('floor_flag', 'Floor check', 'text', 'IF({col:closing}<{set:cash_floor},%s,IF({col:closing}<{set:cash_floor}*1.25,%s,%s))' % (V('Below the floor'), V('Near the floor'), V('Above the floor')), 15),
    CA('acc_phone', 'Accountant phone', 'text', PH(D.ACC_PHONE), 18), CA('owner_phone', 'Owner phone', 'text', PH(D.OWNER_PHONE), 18)], D.cash_d(), 50, [A('floor_flag', '= ' + V('Below the floor'), 'bad')]))

# 13 forecast --------------------------------------------------------------------------------------------------
BASEW = 'SUMIFS(%s,%s,">"&({today}-91),%s,"<>"&%s)/13' % (R('payments', 'amount'), R('payments', 'date'), R('payments', 'kind'), DEPOSIT)
WK = '%s,">="&{col:week_start},%s,"<"&({col:week_start}+7)'
def INWK(t, c, d, *more): return 'SUMIFS(%s,%s,">="&{col:week_start},%s,"<"&({col:week_start}+7)%s)' % (R(t, c), R(t, d), R(t, d), ''.join(',%s,%s' % (R(t, a), b) for a, b in more))
OTHER13 = '(%s)/13' % '+'.join('SUMIFS(%s,%s,">"&({today}-91),%s,%s)' % (R('expenses', 'amount'), R('expenses', 'date'), R('expenses', 'category'), tok('expcat', k))
                                for k in ('Supplies and toys', 'Training', 'Marketing', 'Maintenance', 'Bank and card fees'))
GOV3 = 'SUMIFS(%s,%s,">"&({today}-92))/3' % (R('gov', 'received'), R('gov', 'paid_on'))
CASH_NOW = 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('cash', 'closing'), MS, R('cash', 'month'))
tables.append(T('forecast', 'Cash Forecast 13 Weeks', 'Cash forecast: the next 13 weeks',
    'Thirteen weeks from the next Monday: tuition from your own history, government payments due, payroll, bills, tax and the extra draw give closing cash and the floor check.', [
    C('fc_id', 'Week ID', 'text', 9, required=True),
    CA('week_no', 'Week number', 'int', 'VALUE(RIGHT({col:fc_id},2))', 8), CA('week_start', 'Week (Monday)', 'date', '{today}-WEEKDAY({today},2)+8+7*({col:week_no}-1)', 12),
    CA('opening', 'Opening cash', 'money', '{col:closing}-{col:net}', 12),
    CA('tuition_in', 'Tuition in', 'money', 'ROUND(%s,2)+%s' % (BASEW, INWK('instalments', 'amount', 'due_date', ('paid_amount', '0'))), 12),
    CA('government_in', 'Government in', 'money', 'ROUND(%s+IF({col:week_no}=1,SUMIFS(%s,%s,%s,%s,"<"&{col:week_start}),0)+IF(AND(DAY({col:week_start}+6)>=13,DAY({col:week_start}+6)<=19,{col:week_start}+6>MAX(%s)),%s,0),2)'
       % (INWK('gov', 'expected', 'due_on', ('status', EXPECTED)), R('gov', 'expected'), R('gov', 'status'), EXPECTED, R('gov', 'due_on'), R('gov', 'due_on'), GOV3), 12),
    CA('payroll_out', 'Payroll out', 'money', INWK('bills', 'amount', 'due_date', ('category', PAYROLL), ('status', UPC)), 12),
    CA('rent_bills_out', 'Rent and bills out', 'money', 'SUMIFS(%s,%s,">="&{col:week_start},%s,"<"&({col:week_start}+7),%s,"<>"&%s,%s,%s)' % (R('bills', 'amount'), R('bills', 'due_date'), R('bills', 'due_date'), R('bills', 'category'), PAYROLL, R('bills', 'status'), UPC), 12),
    CA('other_out', 'Routine costs out', 'money', 'ROUND(%s,2)' % OTHER13, 12),
    CA('draw_tax_out', 'Tax and extra draw out', 'money', '%s+IF(AND({set:extra_draw_on}>={col:week_start},{set:extra_draw_on}<{col:week_start}+7),{set:extra_draw},0)' % INWK('tax', 'set_aside', 'due_date', ('status', UPC)), 12),
    CA('net', 'Net', 'money', '{col:tuition_in}+{col:government_in}-{col:payroll_out}-{col:rent_bills_out}-{col:other_out}-{col:draw_tax_out}', 11),
    CA('closing', 'Closing cash', 'money', '%s+SUMIFS(%s,%s,"<="&{col:week_no})' % (CASH_NOW, R('forecast', 'net'), R('forecast', 'week_no')), 12),
    CA('cum_tuition', 'Tuition to date', 'money', 'SUMIFS(%s,%s,"<="&{col:week_no})' % (R('forecast', 'tuition_in'), R('forecast', 'week_no')), 12),
    CA('closing_best', 'Closing cash, best case', 'money', '{col:closing}+{set:best_pct}*{col:cum_tuition}', 12),
    CA('closing_worst', 'Closing cash, worst case', 'money', '{col:closing}-{set:worst_pct}*{col:cum_tuition}', 12),
    CA('closing_leave', 'Closing cash, families leave', 'money', '{col:closing}-{set:leave_families}*ROUND(%s/MAX(1,%s),2)*MAX(0,{col:week_no}-{set:leave_week}+1)' % (BASEW, SM_('families', 'active')), 12),
    CA('below_floor', 'Below floor', 'int', 'IF({col:closing}<{set:cash_floor},1,0)', 7), CA('floor', 'Cash floor', 'money', '{set:cash_floor}', 11),
    CA('floor_flag', 'Floor check', 'text', 'IF({col:closing}<{set:cash_floor},%s,IF({col:closing}<{set:cash_floor}*1.25,%s,%s))' % (V('Below the floor'), V('Near the floor'), V('Above the floor')), 15),
    CA('owner_phone', 'Owner phone', 'text', PH(D.OWNER_PHONE), 18)], D.forecast_d(), 50, [A('floor_flag', '= ' + V('Below the floor'), 'bad'), A('floor_flag', '= ' + V('Near the floor'), 'warn')]))

# 14 bills -----------------------------------------------------------------------------------------------------
tables.append(T('bills', 'Bills', 'Bills due: rent, payroll and regular suppliers',
    'One row per bill: type the due date, category, who is paid, the amount, the status and the supplier phone; the days to due date, the check and the order key fill in.', [
    C('bill_id', 'Bill ID', 'text', 9, required=True), C('due_date', 'Due date', 'date', 11), LST('category', 'Category', 'billcat', 18), C('paid_to', 'Paid to', 'text', 22), C('amount', 'Amount', 'money', 11),
    LST('status', 'Status', 'done2', 10), C('phone', 'Supplier phone', 'text', 18),
    CA('days_to_due', 'Days to due date', 'int', '{col:due_date}-{today}', 9),
    CA('due_flag', 'Bill check', 'text', 'IF({col:status}=%s,%s,IF({col:days_to_due}<0,%s,IF({col:days_to_due}<=7,%s,IF({col:days_to_due}<=30,%s,%s))))' % (PAID2, V('Paid'), V('Overdue bill'), V('Due in 7 days'), V('Due in 30 days'), V('Later')), 14),
    CA('open_key', 'Pay order key value', 'num', 'IF({col:status}=%s,{col:due_date}+VALUE(RIGHT({col:bill_id},3))/1000,"")' % UPC, 10)], D.bills_d(), 90,
    [A('due_flag', '= ' + V('Due in 7 days'), 'warn')]))

# 15 expenses --------------------------------------------------------------------------------------------------
tables.append(T('expenses', 'Expenses', 'Expenses paid, by date and category',
    'One row per expense: type the date, category, description, amount, who was paid, the method and a phone if you message them; the month fills in.', [
    C('expense_id', 'Expense ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), LST('category', 'Category', 'expcat', 18), C('description', 'Description', 'text', 28), C('amount', 'Amount', 'money', 11),
    C('paid_to', 'Paid to', 'text', 22), LST('method', 'Method', 'method', 13), C('phone', 'Contact phone', 'text', 18),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11)], D.expenses_d(), 400))

# 16 payroll ---------------------------------------------------------------------------------------------------
tables.append(T('payroll', 'Payroll', 'Payroll by month, person and pay date',
    'One row per person and month: type the role, pay type, hours, total cost and pay date; the cost per hour fills in.', [
    C('pay_id', 'Pay ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('person', 'Person', 'text', 22), LST('role', 'Role', 'payrole', 18), LST('pay_type', 'Pay type', 'paytype', 11),
    C('hours', 'Hours', 'num', 8), C('total', 'Total cost', 'money', 11), C('pay_date', 'Pay date', 'date', 11), LST('status', 'Status', 'paystat', 10),
    CA('cost_hour', 'Cost per hour', 'money', 'IF({col:hours}>0,ROUND({col:total}/{col:hours},2),0)', 10)], D.payroll_d(), 220))

# 17 collections and autopay by month -------------------------------------------------------------------------
MP = lambda c, *more: 'SUMIFS(%s,%s%s)' % (R('payments', c), W('payments', 'date', '{col:month}'), ''.join(',%s,%s' % (R('payments', a), b) for a, b in more))
INW = 'SUMIFS(%s,%s,">="&{col:month},%s,"<"&MIN(EDATE({col:month},1),{today})%s)'
def MI(c, *more): return INW % (R('invoices', c), R('invoices', 'due_date'), R('invoices', 'due_date'), ''.join(',%s,%s' % (R('invoices', a), b) for a, b in more))
tables.append(T('collect', 'Collections and Autopay', 'Collection rate and autopay effect by month',
    'One row per month: type the month; due, collected, collection rate against your last 3 months, autopay and manual shares, late amounts and card cost fill in from invoices and payments.', [
    C('col_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11),
    CA('due', 'Due', 'money', MI('parent_due'), 12), CA('collected', 'Collected', 'money', MI('paid_amount'), 12), CA('rate', 'Collection rate', 'pct', 'IF({col:due}>0,{col:collected}/{col:due},0)', 10),
    CA('avg3', 'Rate, 3 months before', 'pct', 'IFERROR(AVERAGEIFS(%s,%s,">="&EDATE({col:month},-3),%s,"<"&{col:month}),0)' % (R('collect', 'rate'), R('collect', 'month'), R('collect', 'month')), 10),
    CA('rate_flag', 'Rate check', 'text', 'IF({col:avg3}=0,%s,IF({col:rate}>{col:avg3}+0.02,%s,IF({col:rate}<{col:avg3}-0.02,%s,%s)))' % (V('Near your average'), V('Above your average'), V('Below your average'), V('Near your average')), 17),
    CA('total_paid', 'Paid in month', 'money', MP('amount', ('kind', '"<>"&' + DEPOSIT)), 12),
    CA('card_paid', 'Autopay card', 'money', MP('amount', ('method', ACARD), ('kind', '"<>"&' + DEPOSIT)), 11), CA('bank_auto', 'Autopay bank', 'money', MP('amount', ('method', ABANK), ('kind', '"<>"&' + DEPOSIT)), 11),
    CA('transfer_paid', 'Bank transfer', 'money', MP('amount', ('method', XFER), ('kind', '"<>"&' + DEPOSIT)), 11), CA('cash_paid', 'Cash', 'money', MP('amount', ('method', CASH), ('kind', '"<>"&' + DEPOSIT)), 11),
    CA('autopay_paid', 'Autopay total', 'money', '{col:card_paid}+{col:bank_auto}', 12),
    CA('autopay_share', 'Autopay share', 'pct', 'IF({col:total_paid}>0,{col:autopay_paid}/{col:total_paid},0)', 9), CA('manual_share', 'Manual share', 'pct', 'IF({col:total_paid}>0,1-{col:autopay_share},0)', 9),
    CA('late_autopay', 'Late, autopay', 'money', MI('late_amount', ('autopay', '1')), 11), CA('late_manual', 'Late, manual', 'money', MI('late_amount', ('autopay', '0')), 11),
    CA('card_cost', 'Card processing cost', 'money', MP('card_cost'), 11), CA('owner_phone', 'Owner phone', 'text', PH(D.OWNER_PHONE), 18)], D.front(D.collect_d(), lambda r: r['month'] == iso(month_start(1))), 50))

# 18 overdue families (ranked) ---------------------------------------------------------------------------------
def AGI(c): return 'IFERROR(INDEX(%s,MATCH({col:family},%s,0)),0)' % (R('aging', c), R('aging', 'family'))
tables.append(T('overdue', 'Overdue Families', 'Overdue families, ranked: who to act on first',
    'Ranked by balance, days overdue and broken promises: the family, balance, oldest days, promises kept and broken, the last promise and the next step fill in by themselves.', [
    C('of_id', 'Row ID', 'text', 9, required=True), CA('rank', 'Rank', 'int', 'VALUE(RIGHT({col:of_id},2))', 6),
    CA('family', 'Family', 'text', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,{col:rank}),%s,0)),"")' % (R('aging', 'family'), R('aging', 'score_key'), R('aging', 'score_key')), 22),
    CA('balance', 'Balance', 'money', AGI('balance'), 11), CA('oldest_days', 'Oldest days', 'int', AGI('oldest_days'), 9), CA('open_invoices', 'Open invoices', 'int', AGI('open_invoices'), 9),
    CA('promises_kept', 'Promises kept', 'int', 'COUNTIFS(%s,{col:family},%s,%s)' % (R('promises', 'family'), R('promises', 'outcome'), KEPT), 9),
    CA('promises_broken', 'Promises broken', 'int', AGI('broken'), 9),
    CA('last_promise', 'Last promise', 'date', 'IF(SUMPRODUCT(MAX((%s={col:family})*(%s<={today})*%s))=0,"",SUMPRODUCT(MAX((%s={col:family})*(%s<={today})*%s)))'
       % ((R('promises', 'family'), R('promises', 'promised_on'), R('promises', 'promised_on')) * 2), 11),
    CA('step', 'Next step', 'text', 'IFERROR(INDEX(%s,MATCH({col:family},%s,0)),"")' % (R('aging', 'step'), R('aging', 'family')), 22),
    CA('owner', 'Who acts', 'text', 'IF({col:oldest_days}>={set:pause_day},{set:director_name},{set:billing_name})', 18),
    CA('over_60', 'Over your days limit', 'money', AGI('over_limit'), 11),
    CA('ad_phone', 'Billing phone', 'text', PH(D.AD_PHONE), 18), CA('owner_phone', 'Owner phone', 'text', PH(D.OWNER_PHONE), 18),
    CA('phone', 'Family phone', 'text', LKT('families.phone', 'families.family', 'family'), 18)], D.overdue_d(), 50))

# 19 reminder schedule (ranked) --------------------------------------------------------------------------------
def INVL(c): return 'IFERROR(INDEX(%s,MATCH({col:invoice_id},%s,0)),0)' % (R('invoices', c), R('invoices', 'invoice_id'))
EFF2 = '({col:days_overdue}+7*{col:broken})'
tables.append(T('reminder', 'Reminder Schedule', 'Reminder schedule: the 20 oldest overdue invoices',
    'Ranked by days overdue and amount: the invoice, family, balance, step in the ladder, the date of the next step and who acts fill in by themselves.', [
    C('rs_id', 'Row ID', 'text', 9, required=True), CA('rank', 'Rank', 'int', 'VALUE(RIGHT({col:rs_id},2))', 6),
    CA('invoice_id', 'Invoice ID', 'text', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,{col:rank}),%s,0)),"")' % (R('invoices', 'invoice_id'), R('invoices', 'chase_key'), R('invoices', 'chase_key')), 10),
    CA('family', 'Family', 'text', 'IFERROR(INDEX(%s,MATCH({col:invoice_id},%s,0))&"","")' % (R('invoices', 'family'), R('invoices', 'invoice_id')), 22),
    CA('balance', 'Balance', 'money', INVL('open_balance'), 11), CA('due_date', 'Due date', 'date', INVL('due_date'), 11), CA('days_overdue', 'Days overdue', 'int', INVL('days_overdue'), 9),
    CA('broken', 'Promises broken', 'int', 'COUNTIFS(%s,{col:family},%s,%s)' % (R('promises', 'family'), R('promises', 'outcome'), BROKEN), 9),
    CA('step', 'Step', 'text', 'IF(%s<{set:call_day},%s,IF(%s<{set:plan_day},%s,IF(%s<{set:pause_day},%s,%s)))' % (EFF2, V('Friendly reminder'), EFF2, V('Call today'), EFF2, V('Offer a payment plan'), V('Pause care after notice')), 22),
    CA('next_date', 'Next step on', 'date', 'MAX({today},{col:due_date}+IF({col:days_overdue}<{set:call_day},{set:call_day},IF({col:days_overdue}<{set:plan_day},{set:plan_day},{set:pause_day})))', 11),
    CA('pause_on', 'Pause care after', 'date', '{col:due_date}+{set:pause_day}', 11), CA('pay_by', 'Please pay by', 'date', '{today}+3', 11),
    CA('owner', 'Who acts', 'text', 'IF({col:days_overdue}>={set:pause_day},{set:director_name},{set:billing_name})', 18),
    CA('ad_phone', 'Billing phone', 'text', PH(D.AD_PHONE), 18),
    CA('phone', 'Family phone', 'text', 'IFERROR(INDEX(%s,MATCH({col:family},%s,0))&"","")' % (R('families', 'phone'), R('families', 'family')), 18)], D.reminder_d(), 50))

# 20 tax set-aside ---------------------------------------------------------------------------------------------
tables.append(T('tax', 'Tax Set-aside', 'Income tax set-aside by month (confirm with your adviser)',
    'One row per month: type revenue, costs, the share, the amount set aside and the due date; profit, the amount your share requires and the gap fill in.', [
    C('tax_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('revenue', 'Revenue', 'money', 12), C('costs', 'Costs', 'money', 12), C('set_aside_pct', 'Share', 'pct', 8),
    C('set_aside', 'Set aside', 'money', 11), C('due_date', 'Due date', 'date', 11), C('paid_on', 'Paid on', 'date', 11), LST('status', 'Status', 'done2', 10),
    CA('profit', 'Profit', 'money', '{col:revenue}-{col:costs}', 11), CA('required', 'Your share requires', 'money', 'ROUND(MAX(0,{col:profit})*{set:tax_set_aside_pct},2)', 11),
    CA('gap', 'Gap', 'money', '{col:required}-{col:set_aside}', 10),
    CA('tax_flag', 'Set-aside check', 'text', 'IF({col:gap}>1,%s,%s)' % (V('Short of your share'), V('Set aside is on track')), 20),
    CA('owner_phone', 'Owner phone', 'text', PH(D.OWNER_PHONE), 18)], D.tax_d(), 50, [A('tax_flag', '= ' + V('Short of your share'), 'warn')]))

assert len(tables) == 20, len(tables)
