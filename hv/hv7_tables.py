"""HVAC suite part 7: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv7_lists import *
import hv7_data as D

YES, NO = '{list:yesno.yes}', '{list:yesno.no}'
PAID, PART, UNPD, WO = (tok('invstatus', s) for s in ('Paid', 'Part paid', 'Unpaid', 'Written off'))
CKEPT, CBROKEN, COPEN = (tok('chaseoutcome', s) for s in ('Kept', 'Broken', 'Open'))
POPEN, PPAID = tok('postatus', 'Open'), tok('postatus', 'Paid')
COOL = tok('season', 'Cooling season')
DR_CUR, DR_SAFE, DR_PLUS, DR_CUT, DR_CUT2 = (tok('drawopt', s) for s in DRAW_OPTIONS)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKB(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),"")' % (src, my, kc)
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def ph(v): return '"%s"' % v
def CONST(k, label, v): return CA(k, label, 'text', ph(v), 18)
COMPANY_COL = lambda: CA('company', 'Company', 'text', '{set:company}', 24)
OWNER_PH = lambda: CONST('owner_phone', 'Owner phone', D.OWNER_PHONE)
OFFICE_PH = lambda: CONST('office_phone', 'Office manager phone', D.OFFICE_PHONE)
def TECHPH(col='technician'):
    f = '""'
    for n in reversed(D.TECH6 if hasattr(D, 'TECH6') else TECH6): f = 'IF({col:%s}=%s,%s,%s)' % (col, tok('tech', n), ph(D.PH[n]), f)
    return CA('tech_phone', 'Technician phone', 'text', f, 18)
def inwin(col, a, b): return '{range:%s},">="&%s,{range:%s},"<"&%s' % (col, a, col, b)
L12 = lambda col: inwin(col, 'EDATE(%s,-12)' % MS, MS)           # the last 12 closed months
L6 = lambda col: inwin(col, 'EDATE(%s,-6)' % MS, MS)
L3 = lambda col: inwin(col, 'EDATE(%s,-3)' % MS, MS)
CASH_NOW = 'SUMIFS({range:cash.closing_cash},{range:cash.month},%s)' % MS
FIXED3 = '((SUMIFS({range:cash.payroll},%s)+SUMIFS({range:cash.overhead},%s)+SUMIFS({range:cash.owner_draw},%s))/3)' % (L3('cash.month'), L3('cash.month'), L3('cash.month'))
WEEKLY_IN = 'SUMIFS({range:cash.cash_in},%s)/13*{set:inflow_count}' % L3('cash.month')

settings = [
    S('company', 'Your company name', 'text', COMPANY), S('invoice_days', 'Days after a completed job by which it should be invoiced', 'int', 2),
    S('writeoff_days', 'Days outstanding after which an invoice is at risk of loss', 'int', 90), S('cash_floor', 'Cash floor: the lowest balance you want (set your own)', 'money', CASH_FLOOR),
    S('cover_months', 'Months of fixed costs to keep in cash (set your own)', 'num', 0.5), S('tax_set_aside_pct', 'Tax set-aside, share of profit (confirm with adviser)', 'pct', TAX_SET_ASIDE_PCT),
    S('owner_draw', 'Owner draw each month', 'money', OWNER_DRAW), S('bonus_plan', 'Usual owner bonus each month in the cash plan', 'money', 24000),
    S('deposit_pct', 'Deposit asked on installs, share of the price', 'pct', DEPOSIT_PCT), S('deposit_min', 'Jobs from this amount ask for a deposit', 'money', 2000),
    S('terms_home', 'Invoice terms for homes, days', 'int', TERMS_HOME), S('terms_landlord', 'Invoice terms for landlord and business accounts, days', 'int', TERMS_LANDLORD),
    S('margin_target', 'Gross margin you want on jobs (set your own)', 'pct', 0.5), S('net_target', 'Net profit you want, share of revenue (set your own)', 'pct', 0.12),
    S('financing_factor', 'Financing monthly payment, share financed (enter yours)', 'pct', FINANCE_FACTOR), S('summer_cut', 'Cooling season cash in cut for the slow-summer test', 'pct', 0.15),
    S('inflow_count', 'Share of weekly cash in you count on for bills', 'pct', 0.5), S('paid_target', 'Invoices paid within terms that you want (set your own)', 'pct', 0.9),
    S('prepay_share', 'Share past terms that asks for pre-payment', 'pct', 0.3), S('reduce_share', 'Share past terms that asks for shorter terms', 'pct', 0.15),
]
tables = []
# 1 invoices
tables.append(T('invoices', 'Invoices', 'Invoice register with deposit, balance and days outstanding',
  'One row per invoice: job, dates, site, account, amount, deposit, method, balance and status. Days outstanding, ageing bucket, past due, chase history and the next action fill in by themselves.', [
    C('invoice_id', 'Invoice', 'text', 10, required=True), C('job_id', 'Job', 'text', 10), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 10), C('due_date', 'Due date', 'date', 11), C('site_id', 'Site', 'text', 10),
    C('site_ref', 'Site reference', 'text', 11), C('account', 'Account', 'text', 10), C('phone', 'Phone', 'text', 18), LST('site_type', 'Site type', 'sitetype', 10), LST('job_type', 'Job type', 'jobtype', 24), LST('technician', 'Technician', 'tech', 16),
    C('amount', 'Amount', 'money', 11), C('deposit_asked', 'Deposit asked', 'int', 11), C('deposit_paid', 'Deposit paid', 'int', 11), C('financing', 'Financing used', 'bool', 9), LST('method', 'Method', 'paymethod', 14),
    C('paid_amount', 'Paid amount', 'money', 11), C('paid_on', 'Paid on', 'date', 11), C('balance', 'Balance', 'int', 11), C('terms_days', 'Terms days', 'int', 8), LST('status', 'Status', 'invstatus', 11),
    CA('open', 'Open (1 or 0)', 'int', 'IF(AND({col:balance}>0,{col:status}<>%s),1,0)' % WO, 8),
    CA('days_out', 'Days outstanding', 'int', 'IF({col:open}=1,{today}-{col:date},"")', 10),
    CA('days_past_due', 'Days past due', 'int', 'IF({col:open}=1,MAX(0,{today}-{col:due_date}),"")', 9),
    CA('bucket', 'Ageing bucket', 'text', 'IF({col:open}=0,"",IF({col:days_out}<=30,%s,IF({col:days_out}<=60,%s,IF({col:days_out}<=90,%s,%s))))' % (ck('0 to 30 days'), ck('31 to 60 days'), ck('61 to 90 days'), ck('Over 90 days')), 14),
    CA('days_to_paid', 'Days to paid', 'int', 'IF(AND({col:status}=%s,{col:paid_on}<>""),{col:paid_on}-{col:date},"")' % PAID, 9),
    CA('paid_late', 'Paid late (1 or 0)', 'int', 'IF({col:days_to_paid}="","",IF({col:paid_on}>{col:due_date},1,0))', 9),
    CA('deposit_gap', 'Deposit not paid', 'money', 'MAX(0,{col:deposit_asked}-{col:deposit_paid})', 11),
    CA('chases', 'Chase contacts', 'int', 'COUNTIFS({range:chase.invoice_id},{col:invoice_id})', 8),
    CA('last_chase', 'Last chase', 'date', 'IF({col:chases}=0,"",SUMPRODUCT(MAX(({range:chase.invoice_id}={col:invoice_id})*{range:chase.date})))', 11),
    CA('promised_on', 'Promised on', 'date', 'IF({col:chases}=0,"",SUMPRODUCT(MAX(({range:chase.invoice_id}={col:invoice_id})*({range:chase.date}={col:last_chase})*{range:chase.promised_on})))', 11),
    CA('promise_open', 'Open promises', 'int', 'COUNTIFS({range:chase.invoice_id},{col:invoice_id},{range:chase.outcome},%s)' % COPEN, 8),
    CA('next_action', 'Next action', 'text', 'IF({col:open}=0,"",IF({col:days_past_due}=0,%s,IF({col:chases}=0,%s,IF({col:chases}=1,%s,IF({col:chases}=2,%s,%s)))))' % (
        ck('Not due yet'), ck('Send a friendly reminder'), ck('Call and ask for a date'), ck('Second reminder in writing'), ck('Final notice, pause new jobs')), 26),
    CA('chase_score', 'Chase rank score (amount x days)', 'int', 'IF(AND({col:open}=1,{col:days_past_due}>0),{col:balance}*{col:days_past_due}+VALUE(RIGHT({col:invoice_id},5))/100000,"")', 11),
    TECHPH(), COMPANY_COL()],
  D.invoices_d(), 1300, [A('days_past_due', '> 0', 'bad'), A('status', '= ' + WO, 'warn'), A('paid_late', '= 1', 'warn'), A('status', '= ' + PAID, 'good')]))
# 2 payments
tables.append(T('payments', 'Payments', 'Payments received by invoice, method and kind',
  'One row per payment: date, invoice, job, account, amount, method and kind (invoice, deposit or agreement fee). The site reference, phone and days after the invoice fill in by themselves.', [
    C('payment_id', 'Payment', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 10), C('invoice_id', 'Invoice', 'text', 10), C('job_id', 'Job', 'text', 10), C('account', 'Account', 'text', 10),
    C('site_id', 'Site', 'text', 10), C('amount', 'Amount', 'money', 11), LST('method', 'Method', 'paymethod', 14), LST('kind', 'Kind', 'paykind', 13),
    CA('site_ref', 'Site reference', 'text', LKT('invoices.site_ref', 'invoices.invoice_id', 'invoice_id'), 11), CA('phone', 'Phone', 'text', LKT('invoices.phone', 'invoices.invoice_id', 'invoice_id'), 18),
    CA('days_after', 'Days after the invoice', 'int', 'IFERROR({col:date}-INDEX({range:invoices.date},MATCH({col:invoice_id},{range:invoices.invoice_id},0)),"")', 10),
    CA('invoice_amount', 'Invoice amount', 'money', LKB('invoices.amount', 'invoices.invoice_id', 'invoice_id'), 11), COMPANY_COL()],
  D.payments_d(), 1100, [A('kind', '= ' + tok('paykind', 'Deposit'), 'good')]))
# 3 completed jobs and invoicing
tables.append(T('unbilled', 'Completed Jobs', 'Completed jobs and which are still not invoiced',
  'One row per completed job: type the invoice number once billed. A job with a price, no invoice and no plan cover shows as waiting with its days since the job, a flag and a rank score.', [
    C('job_id', 'Job', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('site_id', 'Site', 'text', 10), C('site_ref', 'Site reference', 'text', 11), C('phone', 'Phone', 'text', 18), LST('job_type', 'Job type', 'jobtype', 24),
    LST('technician', 'Technician', 'tech', 16), C('price', 'Price', 'money', 11), C('invoice_id', 'Invoice', 'text', 10), C('covered', 'Covered by plan or warranty', 'bool', 11),
    CA('waiting', 'Waiting (1 or 0)', 'int', 'IF(AND({col:invoice_id}="",{col:covered}<>%s,{col:price}>0),1,0)' % YES, 8),
    CA('days_since', 'Days since the job', 'int', 'IF({col:waiting}=1,{today}-{col:date},"")', 9),
    CA('flag', 'Flag', 'text', 'IF({col:waiting}=0,%s,IF({col:days_since}>{set:invoice_days},%s,%s))' % (ck('Invoiced or covered'), ck('Over the target: invoice now'), ck('Within the target')), 24),
    CA('score', 'Rank score (price x days)', 'int', 'IF({col:waiting}=1,{col:price}*MAX(1,{col:days_since})+VALUE(RIGHT({col:job_id},5))/100000,"")', 11),
    CA('in_time', 'Invoiced in time (1 or 0)', 'int', 'IF(OR({col:covered}=%s,{col:price}=0),"",IF({col:invoice_id}<>"",1,IF({today}-{col:date}<={set:invoice_days},1,0)))' % YES, 9),
    CA('waiting_count', 'Jobs waiting', 'int', 'SUM({range:unbilled.waiting})', 8), TECHPH(), CA('apprentice', 'Apprentice', 'text', ck(D.APPRENTICE), 16), CONST('apprentice_phone', 'Apprentice phone', D.APPRENTICE_PHONE),
    OFFICE_PH(), COMPANY_COL()],
  D.unbilled_d(), 400, [A('flag', '= ' + ck('Over the target: invoice now'), 'bad'), A('flag', '= ' + ck('Within the target'), 'warn')]))
# 4 customer accounts
tables.append(T('accounts', 'Customer Accounts', 'Landlord and business accounts with terms',
  'One row per landlord or business account: site type, invoice terms in days and phone. The open balance and the invoices on the register fill in by themselves.', [
    C('account', 'Account', 'text', 10, required=True), C('site_type', 'Site type', 'text', 10), C('terms_days', 'Terms days', 'int', 8), C('phone', 'Phone', 'text', 18),
    CA('open_balance', 'Open balance', 'money', 'SUMIFS({range:invoices.balance},{range:invoices.account},{col:account})', 11)],
  D.accounts_d(), 50, [A('open_balance', '> 5000', 'warn')]))
# 5 ageing by account (calculated)
AC = lambda c: '{range:invoices.%s},{col:account}' % 'account'
def AB(lo, hi=None):
    r = 'SUMIFS({range:invoices.balance},{range:invoices.account},{col:account},{range:invoices.days_out},">=%d"' % lo
    return r + (',{range:invoices.days_out},"<=%d")' % hi if hi else ')') if hi else r + ')'
tables.append(T('ageing', 'Ageing by Account', 'Ageing by account: 0-30, 31-60, 61-90 and over 90 days',
  'Pick each account: open invoices, balance, four ageing buckets (unpaid invoices grouped by days outstanding), oldest days, share past terms and a pre-pay, reduce terms or keep verdict fill in.', [
    REF('account', 'Account', 'accounts.account', 10, required=True), CA('as_of', 'As of', 'date', '{today}', 11),
    CA('site_type', 'Site type', 'text', LKT('accounts.site_type', 'accounts.account', 'account'), 10), CA('terms_days', 'Terms days', 'int', LKN('accounts.terms_days', 'accounts.account', 'account'), 8),
    CA('phone', 'Phone', 'text', LKT('accounts.phone', 'accounts.account', 'account'), 18),
    CA('open_invoices', 'Open invoices', 'int', 'COUNTIFS({range:invoices.account},{col:account},{range:invoices.open},1)', 9),
    CA('balance', 'Balance', 'money', 'SUMIFS({range:invoices.balance},{range:invoices.account},{col:account})', 11),
    CA('b0_30', '0-30 days', 'money', 'SUMIFS({range:invoices.balance},{range:invoices.account},{col:account},{range:invoices.days_out},">=0",{range:invoices.days_out},"<=30")', 11),
    CA('b31_60', '31-60 days', 'money', 'SUMIFS({range:invoices.balance},{range:invoices.account},{col:account},{range:invoices.days_out},">30",{range:invoices.days_out},"<=60")', 11),
    CA('b61_90', '61-90 days', 'money', 'SUMIFS({range:invoices.balance},{range:invoices.account},{col:account},{range:invoices.days_out},">60",{range:invoices.days_out},"<=90")', 11),
    CA('b90_plus', 'Over 90 days', 'money', 'SUMIFS({range:invoices.balance},{range:invoices.account},{col:account},{range:invoices.days_out},">90")', 11),
    CA('over60', 'Over 60 days', 'money', '{col:b61_90}+{col:b90_plus}', 11),
    CA('oldest_days', 'Oldest invoice, days', 'int', 'SUMPRODUCT(MAX(({range:invoices.account}={col:account})*({range:invoices.balance}>0)*({today}-{range:invoices.date})))', 10),
    CA('share_past', 'Share past terms', 'pct', 'IFERROR(SUMIFS({range:invoices.balance},{range:invoices.account},{col:account},{range:invoices.days_past_due},">0")/{col:balance},0)', 10),
    CA('invoices_n', 'Invoices on the register', 'int', 'COUNTIFS({range:invoices.account},{col:account})', 10),
    CA('verdict', 'Pre-pay, reduce terms or keep', 'text', 'IF({col:balance}=0,%s,IF(OR({col:share_past}>={set:prepay_share},{col:oldest_days}>{set:writeoff_days}),%s,IF({col:share_past}>={set:reduce_share},%s,%s)))' % (
        ck('Keep: nothing open'), ck('Pre-pay'), ck('Reduce terms'), ck('Keep terms')), 16),
    CA('old_score', 'Oldest account rank score', 'int', 'IF({col:balance}>0,{col:oldest_days}+VALUE(RIGHT({col:account},2))/1000,"")', 10),
    CA('past_due_count', 'Invoices past due', 'int', 'COUNTIFS({range:invoices.days_past_due},">0")', 9),
    CA('over60_total', 'Money over 60 days', 'money', 'SUMIFS({range:invoices.balance},{range:invoices.days_out},">60")', 11),
    CA('oldest_all', 'Oldest open invoice, days', 'int', 'MAX({range:invoices.days_out})', 10), OWNER_PH(), OFFICE_PH(), COMPANY_COL()],
  D.ageing_d(), 50, [A('verdict', '= ' + ck('Pre-pay'), 'bad'), A('verdict', '= ' + ck('Reduce terms'), 'warn'), A('b90_plus', '> 0', 'bad')]))
# 6 chase log
tables.append(T('chase', 'Chase Log', 'Chase log with promises, amounts and outcomes',
  'One row per chase contact: date, invoice, account, method, promised date, promised amount and outcome. Balance, days past due, broken-promise score and the phone fill in by themselves.', [
    C('chase_id', 'Chase', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('invoice_id', 'Invoice', 'text', 10), C('account', 'Account', 'text', 10), LST('method', 'Method', 'chasemethod', 9), C('promised_on', 'Promised on', 'date', 11),
    C('promised_amount', 'Promised amount', 'money', 11), LST('outcome', 'Outcome', 'chaseoutcome', 9),
    CA('balance', 'Invoice balance', 'money', LKB('invoices.balance', 'invoices.invoice_id', 'invoice_id'), 11),
    CA('days_past_due', 'Days past due', 'int', LKB('invoices.days_past_due', 'invoices.invoice_id', 'invoice_id'), 9),
    CA('promise_gap', 'Days promised', 'int', 'IF({col:promised_on}="","",{col:promised_on}-{col:date})', 9),
    CA('broken_score', 'Broken promise rank score', 'int', 'IF(AND({col:outcome}=%s,ISNUMBER({col:balance})),IF(AND({col:balance}>0,{col:date}=IFERROR(INDEX({range:invoices.last_chase},MATCH({col:invoice_id},{range:invoices.invoice_id},0)),0)),{col:promised_amount}+VALUE(RIGHT({col:chase_id},4))/10000,""),"")' % CBROKEN, 11),
    CA('due_week', 'Promise due in 7 days (1 or 0)', 'int', 'IF(AND({col:outcome}=%s,{col:promised_on}>={today},{col:promised_on}<={today}+7),1,0)' % COPEN, 10),
    CA('promises_week', 'Promises due this week', 'int', 'SUM({range:chase.due_week})', 9),
    CA('site_ref', 'Site reference', 'text', LKT('invoices.site_ref', 'invoices.invoice_id', 'invoice_id'), 11),
    CA('phone', 'Phone', 'text', 'IFERROR(INDEX({range:accounts.phone},MATCH({col:account},{range:accounts.account},0))&"",IFERROR(INDEX({range:invoices.phone},MATCH({col:invoice_id},{range:invoices.invoice_id},0))&"",""))', 18),
    OFFICE_PH(), COMPANY_COL()],
  D.chase_d(), 900, [A('outcome', '= ' + CBROKEN, 'warn'), A('outcome', '= ' + COPEN, 'bad'), A('outcome', '= ' + CKEPT, 'good')]))
# 7 days to paid by job type
tables.append(T('dtp_job', 'Days to Paid by Job Type', 'Days to paid and share paid late by job type',
  'One row per job type: paid invoices on the register, the average days to paid and the share paid after the due date, counted from the Invoices sheet.', [
    LST('job_type', 'Job type', 'jobtype', 24, required=True),
    CA('invoices', 'Paid invoices', 'int', 'COUNTIFS({range:invoices.job_type},{col:job_type},{range:invoices.days_to_paid},">=0")', 9),
    CA('avg_days', 'Average days to paid', 'num', 'IFERROR(AVERAGEIFS({range:invoices.days_to_paid},{range:invoices.job_type},{col:job_type}),0)', 10),
    CA('late_share', 'Share paid late', 'pct', 'IFERROR(COUNTIFS({range:invoices.job_type},{col:job_type},{range:invoices.paid_late},1)/{col:invoices},0)', 10)], D.dtp_job_d(), 50, [A('late_share', '>= 0.2', 'warn')]))
# 8 days to paid by technician (3 columns)
tables.append(T('dtp_tech', 'Days to Paid by Technician', 'Days to paid by technician',
  'One row per lead technician: paid invoices on the register and the average days to paid, counted from the Invoices sheet.', [
    LST('technician', 'Technician', 'tech', 16, required=True), CA('invoices', 'Paid invoices', 'int', 'COUNTIFS({range:invoices.technician},{col:technician},{range:invoices.days_to_paid},">=0")', 9),
    CA('avg_days', 'Average days to paid', 'num', 'IFERROR(AVERAGEIFS({range:invoices.days_to_paid},{range:invoices.technician},{col:technician}),0)', 10)], D.dtp_tech_d(), 50))
# 9 deposits and collections by month
tables.append(T('deposits', 'Deposits and Collections', 'Invoicing, collections and deposits by month',
  'One row per month, from your own invoices and payments: invoices, amount invoiced, cash collected by kind, deposits asked and paid, days to paid and the share paid late. Shares fill in by themselves.', [
    C('month', 'Month', 'date', 10, required=True), C('invoices', 'Invoices', 'int', 9), C('invoiced', 'Invoiced', 'money', 12), C('collected_invoices', 'Collected on invoices', 'money', 12), C('collected_deposits', 'Collected deposits', 'money', 12),
    C('collected_fees', 'Collected agreement fees', 'money', 12), C('deposits_asked', 'Deposits asked', 'money', 12), C('deposits_paid', 'Deposits paid', 'money', 12), C('avg_days', 'Average days to paid', 'num', 10), C('late_share', 'Share paid late', 'pct', 10),
    CA('collected', 'Collected', 'money', '{col:collected_invoices}+{col:collected_deposits}+{col:collected_fees}', 12),
    CA('collect_rate', 'Collected over invoiced', 'pct', 'IFERROR({col:collected}/{col:invoiced},0)', 10), CA('share_paid', 'Deposit share paid', 'pct', 'IFERROR({col:deposits_paid}/{col:deposits_asked},0)', 10),
    CA('no_deposit_count', 'Jobs with deposit not paid', 'int', 'COUNTIFS({range:invoices.deposit_gap},">0")', 9), OFFICE_PH(), COMPANY_COL()],
  D.deposits_d(), 50, [A('late_share', '> 0.1', 'warn')]))
# 10 financing used by month
tables.append(T('financing', 'Financing Used', 'Financing offers used by month',
  'One row per month: invoiced jobs, jobs paid through a financing offer, the financed amount and the amount of the other jobs. Share financed and the average ticket of each group fill in by themselves.', [
    C('month', 'Month', 'date', 10, required=True), C('invoiced_jobs', 'Invoiced jobs', 'int', 9), C('financed_jobs', 'Financed jobs', 'int', 9), C('financed_amount', 'Financed amount', 'money', 12), C('other_amount', 'Other amount', 'money', 12),
    CA('share_financed', 'Share financed', 'pct', 'IFERROR({col:financed_jobs}/{col:invoiced_jobs},0)', 9), CA('avg_financed', 'Average financed ticket', 'money', 'IFERROR({col:financed_amount}/{col:financed_jobs},0)', 12),
    CA('avg_other', 'Average other ticket', 'money', 'IFERROR({col:other_amount}/({col:invoiced_jobs}-{col:financed_jobs}),0)', 12)], D.financing_d(), 50))
# 11 profit and loss
tables.append(T('pnl', 'Profit and Loss', 'Profit and loss by month with the same month last year',
  'One row per month: revenue and costs (the last month is month to date). Gross profit, net profit, margins and the change against the same month last year fill in by themselves.', [
    C('month', 'Month', 'date', 10, required=True), LST('season', 'Season', 'season', 16), C('jobs', 'Jobs', 'int', 8), C('revenue', 'Revenue', 'money', 12), C('materials', 'Materials', 'money', 12), C('subcontract', 'Subcontract', 'money', 12),
    C('permits_disposal', 'Permits and disposal', 'money', 12), C('technician_pay', 'Technician pay', 'money', 12), C('vehicles', 'Vehicles', 'money', 12), C('overhead', 'Overhead', 'money', 12),
    CA('gross_profit', 'Gross profit', 'money', '{col:revenue}-{col:materials}-{col:subcontract}-{col:permits_disposal}-{col:technician_pay}', 12),
    CA('net_profit', 'Net profit', 'money', '{col:gross_profit}-{col:vehicles}-{col:overhead}', 12), CA('gross_pct', 'Gross margin', 'pct', 'IFERROR({col:gross_profit}/{col:revenue},0)', 9),
    CA('net_pct', 'Net margin', 'pct', 'IFERROR({col:net_profit}/{col:revenue},0)', 9),
    CA('ly_revenue', 'Revenue same month last year', 'money', 'SUMIFS({range:pnl.revenue},{range:pnl.month},EDATE({col:month},-12))', 12),
    CA('ly_net', 'Net profit same month last year', 'money', 'IF({col:ly_revenue}=0,"",SUMIFS({range:pnl.net_profit},{range:pnl.month},EDATE({col:month},-12)))', 12),
    CA('vs_ly', 'Net profit against last year', 'money', 'IF({col:ly_net}="","",{col:net_profit}-{col:ly_net})', 12),
    CA('period', 'Period', 'text', 'IF({col:month}=%s,%s,%s)' % (MS, ck('Month to date'), ck('Closed month')), 12), CONST('acct_phone', 'Accountant phone', D.ACCT_PHONE), OWNER_PH(), COMPANY_COL()],
  D.pnl_d(), 60, [A('net_profit', '< 0', 'bad'), A('vs_ly', '< 0', 'warn')]))
# 12 cash by month
tables.append(T('cash', 'Cash by Month', 'Cash in, costs, owner draw and closing cash by month',
  'One row per month: cash in, payroll, owner draw, purchases, overhead, tax paid, owner bonus and closing cash. Net cash, months of cover, cash now and the cover now fill in by themselves.', [
    C('month', 'Month', 'date', 10, required=True), C('cash_in', 'Cash in', 'money', 12), C('payroll', 'Payroll', 'money', 12), C('owner_draw', 'Owner draw', 'int', 12), C('purchases', 'Purchases', 'money', 12), C('overhead', 'Overhead', 'money', 12),
    C('tax_paid', 'Tax paid', 'int', 12), C('owner_bonus', 'Owner bonus', 'money', 12), C('closing_cash', 'Closing cash', 'money', 12),
    CA('net', 'Net cash', 'money', '{col:cash_in}-{col:payroll}-{col:owner_draw}-{col:purchases}-{col:overhead}-{col:tax_paid}-{col:owner_bonus}', 12),
    CA('cover', 'Months of cover', 'num', 'IFERROR({col:closing_cash}/IF(COUNTIFS({range:cash.month},">="&EDATE({col:month},-3),{range:cash.month},"<"&{col:month})=0,{col:payroll}+{col:overhead}+{col:owner_draw},(SUMIFS({range:cash.payroll},{range:cash.month},">="&EDATE({col:month},-3),{range:cash.month},"<"&{col:month})+SUMIFS({range:cash.overhead},{range:cash.month},">="&EDATE({col:month},-3),{range:cash.month},"<"&{col:month})+SUMIFS({range:cash.owner_draw},{range:cash.month},">="&EDATE({col:month},-3),{range:cash.month},"<"&{col:month}))/COUNTIFS({range:cash.month},">="&EDATE({col:month},-3),{range:cash.month},"<"&{col:month})),0)', 9),
    CA('cash_now', 'Cash now', 'money', CASH_NOW, 11), CA('floor', 'Cash floor', 'money', '{set:cash_floor}', 11), CA('cover_now', 'Months of cover now', 'num', 'IFERROR(%s/%s,0)' % (CASH_NOW, FIXED3), 9), OWNER_PH(), COMPANY_COL()],
  D.cash_d(), 60, [A('closing_cash', '< {set:cash_floor}', 'bad'), A('net', '< 0', 'warn')]))
# 13 upcoming bills
tables.append(T('bills', 'Upcoming Bills', 'Bills due in the next 13 weeks and cash after each',
  'One row per bill: due date, payee, category, amount, kind and paid. Days ahead, running total due, cash after each bill (cash now plus the weekly cash in you count on) and the floor check fill in.', [
    C('bill_id', 'Bill', 'text', 10, required=True), C('due_date', 'Due date', 'date', 11), C('payee', 'Payee', 'text', 24), LST('category', 'Category', 'billcat', 24), C('amount', 'Amount', 'money', 12), LST('kind', 'Kind', 'billkind', 10), C('paid', 'Paid', 'bool', 8),
    CA('days_ahead', 'Days ahead', 'int', 'IF({col:paid}=%s,"",{col:due_date}-{today})' % YES, 8),
    CA('week_no', 'Week', 'int', 'IF({col:paid}=%s,"",IF({col:days_ahead}<0,0,INT({col:days_ahead}/7)+1))' % YES, 7),
    CA('cum_due', 'Running total due', 'money', 'IF({col:paid}=%s,"",SUMIFS({range:bills.amount},{range:bills.due_date},"<="&{col:due_date},{range:bills.paid},%s))' % (YES, NO), 12),
    CA('cash_after', 'Cash after this bill', 'money', 'IF({col:paid}=%s,"",%s+%s*MAX(0,{col:days_ahead})/7-{col:cum_due})' % (YES, CASH_NOW, WEEKLY_IN), 12),
    CA('below', 'Below the floor (1 or 0)', 'int', 'IF({col:paid}=%s,"",IF({col:cash_after}<{set:cash_floor},1,0))' % YES, 9),
    CA('below_date', 'Date below the floor', 'date', 'IF({col:below}=1,{col:due_date},"")', 11),
    CA('check', 'Floor check', 'text', 'IF({col:paid}=%s,%s,IF({col:below}=1,%s,%s))' % (YES, ck('Paid'), ck('Cash below the floor'), ck('Cash above the floor')), 20),
    CA('cash_after_bill', 'Cash now less this bill', 'money', '%s-{col:amount}' % CASH_NOW, 12), CA('ask_date', 'Ask to move to', 'date', '{col:due_date}+14', 11),
    CONST('supplier_phone', 'Equipment supplier phone', D.SUP_PHONE), CONST('parts_phone', 'Parts counter phone', D.PARTS_PHONE), OWNER_PH(), COMPANY_COL()],
  D.bills_d(), 90, [A('check', '= ' + ck('Cash below the floor'), 'bad'), A('days_ahead', '< 0', 'bad')]))
# 14 purchases
tables.append(T('purchases', 'Purchases', 'Supplier and subcontractor purchases with due dates',
  'One row per purchase from your equipment supplier, your parts counter or a subcontractor: date, kind, job, amount, due date, paid on and status. Days to due and late fill in by themselves.', [
    C('po_id', 'Purchase', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 10), LST('supplier', 'Supplier', 'supplier', 24), LST('kind', 'Kind', 'pokind', 11), C('job_id', 'Job', 'text', 10),
    C('amount', 'Amount', 'money', 12), C('due_date', 'Due date', 'date', 11), C('paid_on', 'Paid on', 'date', 11), LST('status', 'Status', 'postatus', 9),
    CA('days_to_due', 'Days to due', 'int', 'IF({col:status}=%s,{col:due_date}-{today},"")' % POPEN, 8), CA('late', 'Late (1 or 0)', 'int', 'IF(AND({col:status}=%s,{col:due_date}<{today}),1,0)' % POPEN, 8),
    CA('days_paid_vs_due', 'Days paid after the due date', 'int', 'IF({col:paid_on}="","",{col:paid_on}-{col:due_date})', 10),
    CONST('parts_phone', 'Parts counter phone', D.PARTS_PHONE), CONST('elec_phone', 'Electrical subcontractor phone', D.ELEC_PHONE), CONST('sheet_phone', 'Sheet-metal subcontractor phone', D.SHEET_PHONE), COMPANY_COL()],
  D.purchases_d(), 400, [A('late', '= 1', 'bad')]))
# 15 tax set-aside
tables.append(T('tax', 'Tax Set-aside', 'Income tax set-aside by month (confirm with your adviser)',
  'One row per month: the set-aside percent (confirm with your adviser). Profit, set-aside, year to date and tax paid fill in from Profit and Loss and Cash by Month.', [
    C('month', 'Month', 'date', 10, required=True), C('set_aside_pct', 'Set-aside percent', 'pct', 10),
    CA('profit', 'Net profit', 'money', 'SUMIFS({range:pnl.net_profit},{range:pnl.month},{col:month})', 12), CA('set_aside', 'Set-aside', 'money', 'MAX(0,{col:profit})*{col:set_aside_pct}', 12),
    CA('ytd_set_aside', 'Set aside year to date', 'money', 'SUMIFS({range:tax.set_aside},{range:tax.month},">="&DATE(YEAR({col:month}),1,1),{range:tax.month},"<="&{col:month})', 12),
    CA('tax_paid', 'Tax paid', 'money', 'SUMIFS({range:cash.tax_paid},{range:cash.month},{col:month})', 12),
    CA('ytd_paid', 'Tax paid year to date', 'money', 'SUMIFS({range:cash.tax_paid},{range:cash.month},">="&DATE(YEAR({col:month}),1,1),{range:cash.month},"<="&{col:month})', 12), OWNER_PH(), COMPANY_COL()],
  D.tax_d(), 60))
# 16 seasons
tables.append(T('seasons', 'Seasons', 'Seasons with the demand index and the cash index',
  'One row per calendar month: season and demand index (1.00 is an average month). The cash index, your own average cash in for that month over the average month, fills in from Cash by Month.', [
    C('month_no', 'Month number', 'int', 9, required=True), C('month_name', 'Month', 'text', 12), LST('season', 'Season', 'season', 16), C('demand_index', 'Demand index', 'num', 10),
    CA('cash_index', 'Cash index', 'num', 'IFERROR(SUMPRODUCT((MONTH({range:cash.month})={col:month_no})*({range:cash.month}<%s)*({range:cash.month}>0)*{range:cash.cash_in})/SUMPRODUCT((MONTH({range:cash.month})={col:month_no})*({range:cash.month}<%s)*({range:cash.month}>0))/(SUMIFS({range:cash.cash_in},{range:cash.month},"<"&%s)/COUNTIFS({range:cash.month},"<"&%s,{range:cash.month},">0")),1)' % (MS, MS, MS, MS), 9)],
  D.seasons_d(), 50))
# 17 cash forecast (calculated, 12 months)
BASE_IN = '(SUMIFS({range:cash.cash_in},%s)/12)' % L12('cash.month')
PUR_RATIO = '(SUMIFS({range:cash.purchases},%s)/SUMIFS({range:cash.cash_in},%s))' % (L12('cash.month'), L12('cash.month'))
OH6 = '(SUMIFS({range:cash.overhead},%s)/6)' % L6('cash.month'); PAY6 = '(SUMIFS({range:cash.payroll},%s)/6)' % L6('cash.month')
TAXAVG = '(SUMIFS({range:cash.tax_paid},%s)/4)' % L12('cash.month'); OPEN_CASH = 'SUMIFS({range:cash.closing_cash},{range:cash.month},EDATE(%s,-1))' % MS
PROFIT_PM = '(SUMIFS({range:pnl.net_profit},%s)*(1-{set:tax_set_aside_pct})/12)' % L12('pnl.month')
tables.append(T('forecast', 'Cash Forecast', 'Cash forecast for the next 12 months from your own history',
  'Type the 12 month starts: cash in is your 12-month average times the cash index; costs, payroll, owner pay and tax follow your history. Closing cash, cover and the floor check fill in.', [
    C('month', 'Month', 'date', 10, required=True),
    CA('ahead_no', 'Month number ahead', 'int', '(YEAR({col:month})-YEAR(%s))*12+MONTH({col:month})-MONTH(%s)+1' % (MS, MS), 8),
    CA('season', 'Season', 'text', 'IFERROR(INDEX({range:seasons.season},MATCH(MONTH({col:month}),{range:seasons.month_no},0))&"","")', 16),
    CA('cash_index', 'Cash index', 'num', 'IFERROR(INDEX({range:seasons.cash_index},MATCH(MONTH({col:month}),{range:seasons.month_no},0)),1)', 8),
    CA('cash_in', 'Cash in', 'money', '%s*{col:cash_index}' % BASE_IN, 12), CA('costs', 'Costs: purchases and overhead', 'money', '{col:cash_in}*%s+%s' % (PUR_RATIO, OH6), 12), CA('payroll', 'Payroll', 'money', PAY6, 12),
    CA('owner_pay', 'Owner draw and bonus', 'money', '{set:owner_draw}+{set:bonus_plan}', 12), CA('tax', 'Tax', 'money', 'IF(MOD(MONTH({col:month}),3)=1,%s,0)' % TAXAVG, 12),
    CA('net', 'Net cash', 'money', '{col:cash_in}-{col:costs}-{col:payroll}-{col:owner_pay}-{col:tax}', 12),
    CA('closing_cash', 'Closing cash', 'money', '%s+SUMIFS({range:forecast.net},{range:forecast.month},"<="&{col:month})' % OPEN_CASH, 12),
    CA('fixed', 'Fixed costs each month', 'money', '{col:payroll}+%s+{set:owner_draw}' % OH6, 12),
    CA('months_cover', 'Months of cover', 'num', 'IFERROR({col:closing_cash}/{col:fixed},0)', 9),
    CA('below', 'Below the floor (1 or 0)', 'int', 'IF({col:closing_cash}<{set:cash_floor},1,0)', 9),
    CA('cum_in', 'Cash in to date', 'money', 'SUMIFS({range:forecast.cash_in},{range:forecast.month},"<="&{col:month})', 12),
    CA('cum_cool_net', 'Cooling cash in net of purchases', 'money', '{col:cum_cool}*(1-%s)' % PUR_RATIO, 12),
    CA('is_cooling', 'Cooling season (1 or 0)', 'int', 'IF({col:season}=%s,1,0)' % COOL, 9),
    CA('cum_cool', 'Cooling cash in to date', 'money', 'SUMIFS({range:forecast.cash_in},{range:forecast.month},"<="&{col:month},{range:forecast.is_cooling},1)', 12),
    CA('slack_per_k', 'Cash above the floor per month ahead', 'money', '({col:closing_cash}-{set:cash_floor})/{col:ahead_no}', 12),
    CA('safe_pay', 'Safe owner pay each month', 'money', 'MAX(0,MIN(%s,{col:owner_pay}+MIN({range:forecast.slack_per_k})))' % PROFIT_PM, 12),
    CA('lowest_cash', 'Lowest closing cash', 'money', 'MIN({range:forecast.closing_cash})', 12),
    CA('lowest_month', 'Lowest cash month', 'date', 'INDEX({range:forecast.month},MATCH(MIN({range:forecast.closing_cash}),{range:forecast.closing_cash},0))', 11),
    CA('verdict', 'Floor check', 'text', 'IF({col:closing_cash}<{set:cash_floor},%s,IF({col:closing_cash}<{set:cash_floor}*1.5,%s,%s))' % (ck('Below the floor'), ck('Thin: close to the floor'), ck('Above the floor')), 18), OWNER_PH(), COMPANY_COL()],
  D.forecast_d(), 50, [A('verdict', '= ' + ck('Below the floor'), 'bad'), A('verdict', '= ' + ck('Thin: close to the floor'), 'warn')]))
# 18 owner pay options (3 columns, 4 rows)
PAYPLAN = '({set:owner_draw}+{set:bonus_plan})'
tables.append(T('draw_options', 'Owner Pay Options', 'Owner pay options and the cash left at the lowest month',
  'Four options for the owner pay each month (draw and bonus together): what each costs and the months of fixed costs left in cash at the lowest month of the forecast.', [
    LST('option', 'Option', 'drawopt', 24, required=True),
    CA('monthly_draw', 'Monthly owner pay', 'money', 'IF({col:option}=%s,%s,IF({col:option}=%s,INDEX({range:forecast.safe_pay},1),IF({col:option}=%s,%s*1.1,IF({col:option}=%s,%s*0.8,%s*0.6))))' % (DR_CUR, PAYPLAN, DR_SAFE, DR_PLUS, PAYPLAN, DR_CUT, PAYPLAN, PAYPLAN), 12),
    CA('cover_left', 'Months of cover at the lowest month', 'num', 'IFERROR(MAX(0,MIN(%s)/INDEX({range:forecast.fixed},1)),0)' % ','.join('INDEX({range:forecast.closing_cash},%d)+%d*(%s-{col:monthly_draw})' % (k, k, PAYPLAN) for k in range(1, 13)), 10)],
  D.draw_d(), 50))
# 19 expenses
tables.append(T('expenses', 'Expenses', 'Expenses by category with the monthly budget',
  'One row per expense: date, category, description, amount, paid to and method. The monthly budget and the group of the category fill in from Cost Categories.', [
    C('expense_id', 'Expense', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 10), LST('category', 'Category', 'expcat', 20), C('description', 'Description', 'text', 24), C('amount', 'Amount', 'money', 12),
    C('paid_to', 'Paid to', 'text', 20), C('method', 'Method', 'text', 14),
    CA('grp', 'Group', 'text', LKT('cost_cats.grp', 'cost_cats.category', 'category'), 10), CA('monthly_budget', 'Monthly budget', 'money', LKN('cost_cats.monthly_budget', 'cost_cats.category', 'category'), 12),
    CA('budget_share', 'Share of the monthly budget', 'pct', 'IFERROR({col:amount}/{col:monthly_budget},0)', 10)], D.expenses_d(), 800, [A('budget_share', '> 1', 'warn')]))
# 20 cost categories
tables.append(T('cost_cats', 'Cost Categories', 'Cost categories with budget and the last 3 months',
  'One row per cost category: group and monthly budget (set your own). The average of the last 3 closed months and the difference to the budget fill in from the Expenses sheet.', [
    C('category', 'Category', 'text', 22, required=True), C('grp', 'Group', 'text', 10), C('monthly_budget', 'Monthly budget', 'money', 12),
    CA('avg_3m', 'Average last 3 months', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.category},{col:category},%s)/3' % L3('expenses.month'), 12),
    CA('variance', 'Against the budget', 'money', '{col:avg_3m}-{col:monthly_budget}', 12)], D.cost_cats_d(), 50, [A('variance', '> 0', 'warn')]))
assert len(tables) == 20, len(tables)
