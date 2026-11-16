"""HVAC suite part 7: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv7_lists import *
from hv7_tables import MS, L12, L6, L3, CASH_NOW, FIXED3, WEEKLY_IN, TAXAVG, OPEN_CASH, PROFIT_PM, PUR_RATIO
import hv7_data as D

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
YES, NO = '{list:yesno.yes}', '{list:yesno.no}'
PAID, PART, WO = (tok('invstatus', s) for s in ('Paid', 'Part paid', 'Written off'))
COPEN, CBROKEN = tok('chaseoutcome', 'Open'), tok('chaseoutcome', 'Broken')
INV = lambda c: '{range:invoices.%s}' % c
DW = '{range:invoices.date},">="&({today}-{in:days})'
def RK(tbl, col, k): return 'MATCH(LARGE({range:%s.%s},%d),{range:%s.%s},0)' % (tbl, col, k, tbl, col)
def PICK(tbl, col, scol, k, num=False):
    f = 'INDEX({range:%s.%s},%s)' % (tbl, col, RK(tbl, scol, k))
    return 'IFERROR(%s+0,0)' % f if num else 'IFERROR(%s&"",""))' % f
def PT(tbl, col, scol, k): return 'IFERROR(INDEX({range:%s.%s},%s)&"","")' % (tbl, col, RK(tbl, scol, k))
def PN(tbl, col, scol, k): return 'IFERROR(INDEX({range:%s.%s},%s)+0,0)' % (tbl, col, RK(tbl, scol, k))
FLOOR = '{set:cash_floor}'
tools = []
# 1 invoice register check
tools.append(TOOL('register_check', 'Invoice Register Check', 'Invoice register check: what is open, past due and the verdict',
  'Type the days to look back and the share of invoiced money past due that you accept: invoices, amounts, deposits asked and paid, the open and past due balance and a chase now or on track verdict.', [
    I('days', 'Look back, days', 90, 'int'), I('accept', 'Share of invoiced money past due that you accept', 0.1, 'pct')], [
    O('Invoices in the period', 'int', 'COUNTIFS(%s)' % DW), O('Invoiced amount', 'money', 'SUMIFS(%s,%s)' % (INV('amount'), DW)),
    O('Paid in full', 'int', 'COUNTIFS(%s,%s,%s)' % (DW, INV('status'), PAID)), O('Open invoices (part paid or unpaid)', 'int', 'COUNTIFS(%s,%s,1)' % (DW, INV('open'))),
    O('Open balance', 'money', 'SUMIFS(%s,%s)' % (INV('balance'), DW)), O('Past due balance', 'money', 'SUMIFS(%s,%s,%s,">0")' % (INV('balance'), DW, INV('days_past_due'))),
    O('Share of invoiced money past due', 'pct', 'IFERROR(SUMIFS(%s,%s,%s,">0")/SUMIFS(%s,%s),0)' % (INV('balance'), DW, INV('days_past_due'), INV('amount'), DW)),
    O('Deposits asked', 'money', 'SUMIFS(%s,%s)' % (INV('deposit_asked'), DW)), O('Deposits paid', 'money', 'SUMIFS(%s,%s)' % (INV('deposit_paid'), DW)),
    O('Part paid invoices', 'int', 'COUNTIFS(%s,%s,%s)' % (DW, INV('status'), PART)),
    O('Verdict', 'text', 'IF(IFERROR(SUMIFS(%s,%s,%s,">0")/SUMIFS(%s,%s),0)>{in:accept},%s,IF(SUMIFS(%s,%s,%s,">0")>0,%s,%s))' % (
        INV('balance'), DW, INV('days_past_due'), INV('amount'), DW, ck('Chase now'), INV('balance'), DW, INV('days_past_due'), ck('Chase the few late invoices'), ck('On track')))],
  GR('What if', ('Last 30 days', {'days': 30}), ('Last 60 days', {'days': 60}), ('Accept 5 percent', {'accept': 0.05}), ('Accept 20 percent', {'accept': 0.2}))))
# 2 complete but not invoiced
OUT2 = []
for k in range(1, 4):
    OUT2 += [O('%d. Job, technician and flag' % k, 'text', 'IFERROR(INDEX({range:unbilled.job_id},%s)&" "&INDEX({range:unbilled.technician},%s)&": "&INDEX({range:unbilled.flag},%s),"")' % (RK('unbilled', 'score', k), RK('unbilled', 'score', k), RK('unbilled', 'score', k))),
             O('%d. Price' % k, 'money', PN('unbilled', 'price', 'score', k)), O('%d. Days since the job' % k, 'int', PN('unbilled', 'days_since', 'score', k))]
tools.append(TOOL('unbilled_check', 'Not Invoiced Warning', 'Complete but not invoiced: the money not yet billed and who to call',
  'Type the days a job may wait: completed jobs with no invoice, the money not yet billed, those past the limit and the five to invoice first ranked by value and age, with the office manager call list.', [
    I('limit', 'Days a job may wait for its invoice', 2, 'int')], [
    O('Completed jobs not invoiced', 'int', 'SUM({range:unbilled.waiting})'), O('Money not yet invoiced', 'money', 'SUMIFS({range:unbilled.price},{range:unbilled.waiting},1)'),
    O('Jobs waiting longer than the limit', 'int', 'COUNTIFS({range:unbilled.days_since},">"&{in:limit})'), O('Money on those jobs', 'money', 'SUMIFS({range:unbilled.price},{range:unbilled.days_since},">"&{in:limit})'),
    O('Oldest waiting job, days', 'int', 'MAX({range:unbilled.days_since})'), O('Share of billable jobs invoiced in time', 'pct', 'IFERROR(SUM({range:unbilled.in_time})/COUNT({range:unbilled.in_time}),0)'),
    O('Verdict', 'text', 'IF(SUM({range:unbilled.waiting})=0,%s,IF(COUNTIFS({range:unbilled.days_since},">"&{in:limit})>0,%s,%s))' % (ck('Nothing waiting'), ck('Invoice the oldest jobs today'), ck('Invoice within the limit')))] + OUT2,
  GR('What if', ('Limit 1 day', {'limit': 1}), ('Limit 7 days', {'limit': 7}), ('Limit 30 days', {'limit': 30}))))
# 3 deposit tool
LJ = '{range:invoices.amount},">="&{in:min_job}'
tools.append(TOOL('deposit_check', 'Deposit Coverage Check', 'Deposits on large jobs: started without one, cash tied up and the percent that covers equipment',
  'Type the job size that needs a deposit, the deposit percent you ask and the share of the price that is equipment: large jobs without a deposit, the cash tied up and whether your percent covers the equipment.', [
    I('min_job', 'Jobs from this amount need a deposit', 2000), I('pct', 'Deposit percent you ask', DEPOSIT_PCT, 'pct'), I('equip', 'Equipment share of the price', D.DEF['equip_share'], 'pct')], [
    O('Large jobs on the register', 'int', 'COUNTIFS(%s)' % LJ), O('With a deposit asked', 'int', 'COUNTIFS(%s,%s,">0")' % (LJ, INV('deposit_asked'))),
    O('Started without a deposit', 'int', 'COUNTIFS(%s,%s,0)' % (LJ, INV('deposit_asked'))), O('Value of jobs without a deposit', 'money', 'SUMIFS(%s,%s,%s,0)' % (INV('amount'), LJ, INV('deposit_asked'))),
    O('Equipment cash tied up without a deposit', 'money', 'SUMIFS(%s,%s,%s,0)*{in:equip}' % (INV('amount'), LJ, INV('deposit_asked'))),
    O('Deposits asked on large jobs', 'money', 'SUMIFS(%s,%s)' % (INV('deposit_asked'), LJ)), O('Deposits paid on large jobs', 'money', 'SUMIFS(%s,%s)' % (INV('deposit_paid'), LJ)),
    O('Average large job', 'money', 'IFERROR(AVERAGEIFS(%s,%s),0)' % (INV('amount'), LJ)), O('Deposit on the average large job at your percent', 'money', 'IFERROR(AVERAGEIFS(%s,%s),0)*{in:pct}' % (INV('amount'), LJ)),
    O('Deposit percent that covers the equipment', 'pct', '{in:equip}'),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,%s,0)>0,%s,IF({in:pct}<{in:equip},%s,%s))' % (LJ, INV('deposit_asked'), ck('Ask for a deposit before ordering'), ck('Raise the deposit percent'), ck('Deposits cover the equipment')))],
  GR('What if', ('Deposit 40 percent', {'pct': 0.4}), ('Deposit 20 percent', {'pct': 0.2}), ('Jobs from 1000', {'min_job': 1000}), ('Jobs from 4000', {'min_job': 4000}))))
# 4 financing offer check
FY = '{range:financing.month},">="&EDATE(%s,-12),{range:financing.month},"<"&%s' % (MS, MS)
FJ, FI = 'SUMIFS({range:financing.financed_jobs},%s)' % FY, 'SUMIFS({range:financing.invoiced_jobs},%s)' % FY
AVF = 'IFERROR(SUMIFS({range:financing.financed_amount},%s)/%s,0)' % (FY, FJ)
AVO = 'IFERROR(SUMIFS({range:financing.other_amount},%s)/(%s-%s),0)' % (FY, FI, FJ)
tools.append(TOOL('financing_check', 'Financing Offer Check', 'Financing offer: share used, ticket with and without it and where to offer it',
  'Type the close rate you see with a financing offer and without one (your own estimates): jobs financed, the average ticket of each group, the monthly payment and an offer on larger jobs, offer on all or stop verdict.', [
    I('close_with', 'Close rate when you offer financing (your estimate)', 0.62, 'pct'), I('close_without', 'Close rate without it (your estimate)', 0.55, 'pct'), I('ratio_min', 'Ticket ratio that marks a larger job', 1.5, 'num')], [
    O('Financed jobs, last 12 months', 'int', FJ), O('Invoiced jobs, last 12 months', 'int', FI), O('Share of jobs financed', 'pct', 'IFERROR(%s/%s,0)' % (FJ, FI)),
    O('Average financed ticket', 'money', AVF), O('Average ticket without financing', 'money', AVO), O('Ticket ratio', 'num', 'IFERROR(%s/%s,0)' % (AVF, AVO)),
    O('Monthly payment on the average financed ticket', 'money', '%s*{set:financing_factor}' % AVF), O('Extra jobs won per 100 estimates', 'num', '({in:close_with}-{in:close_without})*100'),
    O('Verdict', 'text', 'IF({in:close_with}<={in:close_without},%s,IF(IFERROR(%s/%s,0)>={in:ratio_min},%s,%s))' % (ck('Stop offering financing'), AVF, AVO, ck('Offer on larger jobs'), ck('Offer on all jobs')))],
  GR('What if', ('No close rate gain', {'close_with': 0.55}), ('Close rate 70 percent', {'close_with': 0.7}), ('Larger means 3 times', {'ratio_min': 3}))))
# 5 payment method mix
MET = ['Card on site', 'Card online', 'Bank transfer', 'Cash or cheque', 'Financing offer']
def MC(m): return 'COUNTIFS(%s,%s,%s)' % (DW, INV('method'), tok('paymethod', m))
def MD(m): return 'IFERROR(AVERAGEIFS(%s,%s,%s),0)' % (INV('days_to_paid'), DW + ',' + INV('method'), tok('paymethod', m))
MDAYS = [MD(m) for m in MET]
MX = 'MAX(%s)' % ','.join(MDAYS)
slow = ck('Slowest: ' + MET[4])
for m in reversed(MET[:4]): slow = 'IF(%s=%s,%s,%s)' % (MD(m), MX, ck('Slowest: ' + m), slow)
tools.append(TOOL('method_mix', 'Payment Method Mix', 'Payment methods: how many invoices and how fast each one is paid',
  'Type the days to look back and the days to paid you accept: invoices and share by method (card on site, card online, bank transfer, cash or cheque, financing) and the average days to paid, with the slowest method named.', [
    I('days', 'Look back, days', 90, 'int'), I('limit', 'Days to paid you accept', 10, 'num')],
  sum([[O('%s: invoices' % m, 'int', MC(m)), O('%s: share of invoices' % m, 'pct', 'IFERROR(%s/COUNTIFS(%s,%s,">=0"),0)' % (MC(m), DW, INV('days_to_paid'))), O('%s: average days to paid' % m, 'num', MD(m))] for m in MET], []) + [
    O('Slowest average days to paid', 'num', MX), O('Verdict', 'text', 'IF(%s>{in:limit},%s,%s)' % (MX, slow, ck('All methods are on pace')))],
  GR('What if', ('Look back 60 days', {'days': 60}), ('Accept 5 days', {'limit': 5}), ('Accept 20 days', {'limit': 20}))))
# 6 ageing analyser
OUT6 = []
for k in range(1, 4):
    OUT6 += [O('%d. Account with the oldest invoice' % k, 'text', PT('ageing', 'account', 'old_score', k)), O('%d. Oldest invoice, days' % k, 'int', PN('ageing', 'oldest_days', 'old_score', k)), O('%d. Balance' % k, 'money', PN('ageing', 'balance', 'old_score', k))]
tools.append(TOOL('ageing_analyser', 'Ageing Analyser', 'Ageing: open invoices by days outstanding with the oldest accounts first',
  'Type the shares of open money over 60 days that turn amber and red: open invoices in four buckets (unpaid invoices grouped by days outstanding), the oldest invoice, the three oldest accounts and a traffic light.', [
    I('amber', 'Share over 60 days that turns amber', 0.02, 'pct'), I('red', 'Share over 60 days that turns red', 0.1, 'pct')], [
    O('Open invoices', 'int', 'SUM({range:invoices.open})'), O('Open balance', 'money', 'SUM({range:invoices.balance})'),
    O('0 to 30 days', 'money', 'SUMIFS(%s,%s,">=0",%s,"<=30")' % (INV('balance'), INV('days_out'), INV('days_out'))), O('31 to 60 days', 'money', 'SUMIFS(%s,%s,">30",%s,"<=60")' % (INV('balance'), INV('days_out'), INV('days_out'))),
    O('61 to 90 days', 'money', 'SUMIFS(%s,%s,">60",%s,"<=90")' % (INV('balance'), INV('days_out'), INV('days_out'))), O('Over 90 days', 'money', 'SUMIFS(%s,%s,">90")' % (INV('balance'), INV('days_out'))),
    O('Balance over 60 days', 'money', 'SUMIFS(%s,%s,">60")' % (INV('balance'), INV('days_out'))), O('Share of open money over 60 days', 'pct', 'IFERROR(SUMIFS(%s,%s,">60")/SUM(%s),0)' % (INV('balance'), INV('days_out'), INV('balance'))),
    O('Oldest open invoice, days', 'int', 'MAX(%s)' % INV('days_out')), O('Accounts with money over 60 days', 'int', 'COUNTIFS({range:ageing.over60},">0")'),
    O('Verdict', 'text', 'IF(IFERROR(SUMIFS(%s,%s,">60")/SUM(%s),0)>={in:red},%s,IF(IFERROR(SUMIFS(%s,%s,">60")/SUM(%s),0)>={in:amber},%s,%s))' % (
        INV('balance'), INV('days_out'), INV('balance'), ck('Red: chase the oldest first'), INV('balance'), INV('days_out'), INV('balance'), ck('Amber: chase this week'), ck('Green: on track')))] + OUT6,
  GR('What if', ('Amber 5 percent', {'amber': 0.05}), ('Red 5 percent', {'red': 0.05}), ('Red 20 percent', {'red': 0.2}))))
# 7 chase list
OUT7 = []
for k in range(1, 11):
    OUT7 += [O('%d. Invoice, account and next action' % k, 'text', 'IFERROR(INDEX({range:invoices.invoice_id},%s)&" "&INDEX({range:invoices.account},%s)&": "&INDEX({range:invoices.next_action},%s),"")' % ((RK('invoices', 'chase_score', k),) * 3))]
    if k <= 3: OUT7 += [O('%d. Balance' % k, 'money', PN('invoices', 'balance', 'chase_score', k))]
tools.append(TOOL('chase_list', 'Chase List', 'Who to chase first: overdue invoices ranked by amount times days past due',
  'Type the chase calls you can make in a week: invoices past due, the money at stake, the share the calls cover and the ten to chase first with the last next action; a verdict says chase first or clear.', [
    I('calls', 'Chase calls you can make in a week', 10, 'int')], [
    O('Invoices past due', 'int', 'COUNTIFS(%s,">0")' % INV('days_past_due')), O('Money past due', 'money', 'SUMIFS(%s,%s,">0")' % (INV('balance'), INV('days_past_due'))),
    O('Money covered by your weekly calls', 'money', 'SUMIFS(%s,%s,">="&IFERROR(LARGE(%s,{in:calls}),0))' % (INV('balance'), INV('chase_score'), INV('chase_score'))),
    O('Share of past due money covered', 'pct', 'IFERROR(SUMIFS(%s,%s,">="&IFERROR(LARGE(%s,{in:calls}),0))/SUMIFS(%s,%s,">0"),0)' % (INV('balance'), INV('chase_score'), INV('chase_score'), INV('balance'), INV('days_past_due'))),
    O('Money at stake in the top 10', 'money', 'SUMIFS(%s,%s,">="&IFERROR(LARGE(%s,10),0))' % (INV('balance'), INV('chase_score'), INV('chase_score'))),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">0")=0,%s,IF(COUNTIFS(%s,">0")>{in:calls},%s,%s))' % (INV('days_past_due'), ck('Nothing to chase'), INV('days_past_due'), ck('Chase first: start at the top'), ck('Chase all this week')))] + OUT7,
  GR('What if', ('5 calls a week', {'calls': 5}), ('20 calls a week', {'calls': 20}), ('40 calls a week', {'calls': 40}))))
# 8 promise tracker
OUT8 = []
for k in range(1, 4):
    OUT8 += [O('%d. Broken promise: invoice and account' % k, 'text', 'IFERROR(INDEX({range:chase.invoice_id},%s)&" "&INDEX({range:chase.account},%s),"")' % ((RK('chase', 'broken_score', k),) * 2)), O('%d. Promised amount' % k, 'money', PN('chase', 'promised_amount', 'broken_score', k))]
tools.append(TOOL('promise_tracker', 'Promise Tracker', 'Promises due soon and broken promises on invoices still open',
  'Type the days ahead to watch: promises due in that time with the amount, broken promises on invoices still open, the three largest and a call today or wait verdict.', [
    I('ahead', 'Days ahead to watch', 7, 'int')], [
    O('Promises due in the window', 'int', 'COUNTIFS({range:chase.outcome},%s,{range:chase.promised_on},">="&{today},{range:chase.promised_on},"<="&({today}+{in:ahead}))' % COPEN),
    O('Amount promised in the window', 'money', 'SUMIFS({range:chase.promised_amount},{range:chase.outcome},%s,{range:chase.promised_on},">="&{today},{range:chase.promised_on},"<="&({today}+{in:ahead}))' % COPEN),
    O('Open invoices with a broken last promise', 'int', 'COUNT({range:chase.broken_score})'), O('Amount of those promises', 'money', 'SUMIFS({range:chase.promised_amount},{range:chase.broken_score},">0")'),
    O('Verdict', 'text', 'IF(COUNT({range:chase.broken_score})>0,%s,IF(COUNTIFS({range:chase.outcome},%s,{range:chase.promised_on},">="&{today},{range:chase.promised_on},"<="&({today}+{in:ahead}))>0,%s,%s))' % (
        ck('Call today'), COPEN, ck('Wait for the promised dates'), ck('No promises open')))] + OUT8,
  GR('What if', ('Watch 3 days', {'ahead': 3}), ('Watch 14 days', {'ahead': 14}))))
# 9 days to paid analyser
SHOP12 = 'IFERROR(SUMPRODUCT(({range:deposits.month}>=EDATE(%s,-12))*({range:deposits.month}<%s)*{range:deposits.avg_days}*{range:deposits.invoices})/SUMIFS({range:deposits.invoices},%s),0)' % (MS, MS, inwin_dep if False else '{range:deposits.month},">="&EDATE(%s,-12),{range:deposits.month},"<"&%s' % (MS, MS))
P90 = '{range:invoices.paid_on},">="&({today}-90)'
def STD(st): return 'IFERROR(AVERAGEIFS(%s,%s,%s),0)' % (INV('days_to_paid'), INV('site_type') + ',' + tok('sitetype', st), P90) if False else 'IFERROR(AVERAGEIFS(%s,%s,%s,%s),0)' % (INV('days_to_paid'), INV('site_type'), tok('sitetype', st), P90.replace('{range:invoices.paid_on}', INV('paid_on')) if False else P90)
STY = ['Home', 'Rental', 'Shop', 'Office']
SMX = 'MAX(%s)' % ','.join(STD(s) for s in STY)
sname = tok('sitetype', STY[3])
for s in reversed(STY[:3]): sname = 'IF(%s=%s,%s,%s)' % (STD(s), SMX, tok('sitetype', s), sname)
tools.append(TOOL('dtp_analyser', 'Days to Paid Analyser', 'Days to paid by job type, technician and site type against your own last 12 months',
  'Type the days to paid you want and the margin over your average that marks a slow segment: your 12-month average, the last 90 days, the slowest job type, technician and site type and a verdict.', [
    I('target', 'Days to paid you want', 14, 'num'), I('slow', 'Slow segment: times your average', 1.25, 'num')], [
    O('Your average days to paid, last 12 months', 'num', SHOP12), O('Average days to paid, last 90 days', 'num', 'IFERROR(AVERAGEIFS(%s,%s),0)' % (INV('days_to_paid'), P90)),
    O('Share paid late, last 90 days', 'pct', 'IFERROR(COUNTIFS(%s,%s,1)/COUNTIFS(%s,%s,">=0"),0)' % (P90, INV('paid_late'), P90, INV('days_to_paid'))),
    O('Slowest job type', 'text', 'IFERROR(INDEX({range:dtp_job.job_type},MATCH(MAX({range:dtp_job.avg_days}),{range:dtp_job.avg_days},0))&"","")'), O('Its average days to paid', 'num', 'MAX({range:dtp_job.avg_days})'),
    O('Slowest technician', 'text', 'IFERROR(INDEX({range:dtp_tech.technician},MATCH(MAX({range:dtp_tech.avg_days}),{range:dtp_tech.avg_days},0))&"","")'), O('Its average days to paid', 'num', 'MAX({range:dtp_tech.avg_days})'),
    O('Slowest site type', 'text', sname), O('Its average days to paid', 'num', SMX),
    O('Verdict', 'text', 'IF(MAX(MAX({range:dtp_job.avg_days}),MAX({range:dtp_tech.avg_days}),%s)>%s*{in:slow},%s,IF(%s>{in:target},%s,%s))' % (SMX, SHOP12, ck('Chase the slowest segment first'), SHOP12, ck('Above your target: tighten terms'), ck('On target')))],
  GR('What if', ('Target 7 days', {'target': 7}), ('Slow means 1.5 times', {'slow': 1.5}), ('Slow means 2 times', {'slow': 2}))))
# 10 landlord account review
def AGN(c): return 'IFERROR(INDEX({range:ageing.%s},MATCH({in:account},{range:ageing.account},0))+0,0)' % c
def AGT(c): return 'IFERROR(INDEX({range:ageing.%s},MATCH({in:account},{range:ageing.account},0))&"","")' % c
tools.append(TOOL('landlord_review', 'Landlord Account Review', 'Landlord and business account: balance, oldest invoice and pre-pay, reduce terms or keep',
  'Type an account number and your limits: its balance, open invoices, the oldest invoice, the money over 60 days and the share past its terms, with a pre-pay, reduce terms or keep terms verdict.', [
    I('account', 'Account', D.DEF['account'], 'text'), I('prepay', 'Share past terms that asks for pre-payment', 0.3, 'pct'), I('reduce', 'Share past terms that asks for shorter terms', 0.15, 'pct'), I('old', 'Oldest invoice that asks for pre-payment, days', 90, 'int')], [
    O('Site type', 'text', AGT('site_type')), O('Phone', 'text', AGT('phone')), O('Terms, days', 'int', AGN('terms_days')), O('Open invoices', 'int', AGN('open_invoices')), O('Balance', 'money', AGN('balance')),
    O('Balance over 60 days', 'money', AGN('over60')), O('Oldest invoice, days', 'int', AGN('oldest_days')), O('Share of the balance past terms', 'pct', AGN('share_past')), O('Invoices on the register', 'int', AGN('invoices_n')),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(OR(%s>={in:prepay},%s>{in:old}),%s,IF(%s>={in:reduce},%s,%s)))' % (AGN('balance'), ck('Keep: nothing open'), AGN('share_past'), AGN('oldest_days'), ck('Pre-pay'), AGN('share_past'), ck('Reduce terms'), ck('Keep terms')))],
  GR('What if', ('Pre-pay from 20 percent', {'prepay': 0.2}), ('Pre-pay from 50 percent', {'prepay': 0.5}), ('Old means 120 days', {'old': 120}))))
# 11 write-off check
RISK = '{range:invoices.days_out},">"&{in:older},{range:invoices.promise_open},0'
tools.append(TOOL('writeoff_check', 'Write-off Check', 'Invoices at risk of loss: no promise, long outstanding, and what the debt really costs',
  'Type the days outstanding and the job margin: invoices older than that with no open promise, the balance at risk and the extra sales needed to win that money back, with the oldest invoice shown.', [
    I('older', 'Days outstanding that count as at risk', 90, 'int'), I('margin', 'Margin on the job', D.DEF['margin'], 'pct')], [
    O('Invoices at risk', 'int', 'COUNTIFS(%s)' % RISK), O('Balance at risk', 'money', 'SUMIFS(%s,%s)' % (INV('balance'), RISK)),
    O('Share of the open balance', 'pct', 'IFERROR(SUMIFS(%s,%s)/SUM(%s),0)' % (INV('balance'), RISK, INV('balance'))), O('Extra sales needed to earn that money back', 'money', 'IFERROR(SUMIFS(%s,%s)/{in:margin},0)' % (INV('balance'), RISK)),
    O('Oldest open invoice', 'text', 'IFERROR(INDEX({range:invoices.invoice_id},MATCH(MAX(%s),%s,0))&"","")' % (INV('days_out'), INV('days_out'))), O('Its account', 'text', 'IFERROR(INDEX({range:invoices.account},MATCH(MAX(%s),%s,0))&"","")' % (INV('days_out'), INV('days_out'))),
    O('Its balance', 'money', 'IFERROR(INDEX({range:invoices.balance},MATCH(MAX(%s),%s,0))+0,0)' % (INV('days_out'), INV('days_out'))), O('Its days outstanding', 'int', 'MAX(%s)' % INV('days_out')),
    O('Verdict', 'text', 'IF(COUNTIFS(%s)=0,%s,IF(MAX(%s)>{in:older}*1.5,%s,%s))' % (RISK, ck('Nothing at risk'), INV('days_out'), ck('Settle or write off'), ck('Send a final notice, then decide')))],
  GR('What if', ('At risk from 60 days', {'older': 60}), ('At risk from 120 days', {'older': 120}), ('Margin 35 percent', {'margin': 0.35}))))
# 12 seasonal cash forecast (twelve explicit terms: the forecast range may hold blank rows)
def ADJ(k): return '(INDEX({range:forecast.closing_cash},%d)+{in:chg}*INDEX({range:forecast.cum_in},%d)-{in:extra}*%d)' % (k, k, k)
LOW = 'MIN(%s)' % ','.join(ADJ(k) for k in range(1, 13))
BELOW = '(%s)' % '+'.join('(%s<%s)' % (ADJ(k), FLOOR) for k in range(1, 13))
FIRST = 'MIN(%s)' % ','.join('INDEX({range:forecast.month},%d)+(%s>=%s)*100000' % (k, ADJ(k), FLOOR) for k in range(1, 13))
tools.append(TOOL('cash_forecast', 'Seasonal Cash Forecast', 'Seasonal cash forecast: closing cash, the lowest month and months of cover',
  'x', [
    I('chg', 'Change in cash in against your history', 0, 'pct'), I('extra', 'Extra cost each month', 0)], [
    O('Cash at the end of last month', 'money', OPEN_CASH), O('Closing cash after 3 months', 'money', ADJ(3)), O('Closing cash after 6 months', 'money', ADJ(6)), O('Closing cash after 12 months', 'money', ADJ(12)),
    O('Lowest closing cash', 'money', LOW), O('Lowest cash month in your plan', 'date', 'INDEX({range:forecast.lowest_month},1)'),
    O('Months below the cash floor', 'int', BELOW), O('Lowest cash above or below the floor', 'money', '%s-%s' % (LOW, FLOOR)),
    O('Months of fixed costs in cash at the lowest month', 'num', 'IFERROR(%s/INDEX({range:forecast.fixed},1),0)' % LOW),
    O('Verdict', 'text', 'IF(%s<%s,%s,IF(%s<%s*1.5,%s,%s))' % (LOW, FLOOR, ck('Below the floor: act before the dip'), LOW, FLOOR, ck('Above the floor but thin'), ck('Above the floor')))],
  GR('What if', ('Cash in minus 10 percent', {'chg': -0.1}), ('Cash in plus 10 percent', {'chg': 0.1}), ('Extra cost 5000 a month', {'extra': 5000}))))
# 13 slow summer test
def CADJ(k, c='{in:cut}'): return '(INDEX({range:forecast.closing_cash},%d)-%s*INDEX({range:forecast.cum_cool_net},%d))' % (k, c, k)
def CUTLOW(c): return 'MIN(%s)' % ','.join(CADJ(k, c) for k in range(1, 13))
CLOW = CUTLOW('{in:cut}')
tools.append(TOOL('slow_summer', 'Slow-Summer Test', 'Slow-summer test: cooling season cash in cut with costs held fixed',
  'x', [I('cut', 'Cut in cooling season cash in', 0.15, 'pct')], [
    O('Cooling season months in the forecast', 'int', 'SUM({range:forecast.is_cooling})'), O('Cooling season cash in', 'money', 'SUMIFS({range:forecast.cash_in},{range:forecast.is_cooling},1)'),
    O('Cash lost with the cut, net of purchases saved', 'money', 'SUMIFS({range:forecast.cash_in},{range:forecast.is_cooling},1)*{in:cut}*(1-%s)' % PUR_RATIO), O('Lowest cash in your plan', 'money', 'MIN({range:forecast.closing_cash})'),
    O('Lowest cash with the cut', 'money', CLOW),
    O('Months below the floor with the cut', 'int', '(%s)' % '+'.join('(%s<%s)' % (CADJ(k), FLOOR) for k in range(1, 13))), O('Months of fixed costs in cash at that low', 'num', 'IFERROR(MAX(0,%s)/INDEX({range:forecast.fixed},1),0)' % CLOW),
    O('Base: lowest cash at your cut', 'money', CUTLOW('{in:cut}')), O('Best: lowest cash at half the cut', 'money', CUTLOW('({in:cut}/2)')), O('Worst: lowest cash at twice the cut', 'money', CUTLOW('({in:cut}*2)'))] +
    [O('Sensitivity: lowest cash with a %d percent cut' % p, 'money', CUTLOW(str(p / 100))) for p in (5, 10, 15, 20, 25)] + [
    O('Verdict', 'text', 'IF(%s>=%s,%s,IF(%s>=0,%s,%s))' % (CLOW, FLOOR, ck('Safe: stays above the floor'), CLOW, ck('Tight: ask deposits, hold buying'), ck('Below zero: build a cushion')))],
  GR('What if', ('Cut 5 percent', {'cut': 0.05}), ('Cut 25 percent', {'cut': 0.25}), ('Cut 40 percent', {'cut': 0.4}))))
# 14 supplier bill and cash floor check
BM = 'MATCH({in:bill_ref},{range:bills.bill_id},0)'
BAMT = 'IFERROR(INDEX({range:bills.amount},%s)+0,0)' % BM; BDUE = 'IFERROR(INDEX({range:bills.due_date},%s)+0,0)' % BM
AFTER = '(%s+%s*MAX(0,%s-{today}+{in:move})/7-(SUMIFS({range:bills.amount},{range:bills.due_date},"<="&(%s+{in:move}),{range:bills.paid},%s)+IF({in:move}<0,%s,0))+{in:extra})' % (CASH_NOW, WEEKLY_IN, BDUE, BDUE, NO, BAMT)
FSTB = 'MIN({range:bills.below_date})'
tools.append(TOOL('bill_check', 'Supplier Bill Check', 'Can you pay this supplier bill: pay now, pay on the due date, negotiate terms or delay and ask',
  'Type a bill number, days to move the payment and any extra cash: the bill, cash after paying it alone, cash on the due date counting your usual weekly cash in, bills due in 7 and 14 days, the first date cash falls below the floor and a verdict.', [
    I('bill_ref', 'Bill', D.DEF['bill'], 'text'), I('move', 'Move the payment by days', 0, 'int'), I('extra', 'Extra cash you can add', 0)], [
    O('Payee', 'text', 'IFERROR(INDEX({range:bills.payee},%s)&"","")' % BM), O('Bill amount', 'money', BAMT), O('Due date', 'date', BDUE), O('Days until due', 'int', '%s-{today}' % BDUE),
    O('Cash now', 'money', CASH_NOW), O('Cash after paying this bill alone', 'money', '%s-%s+{in:extra}' % (CASH_NOW, BAMT)), O('Short of the floor if paid now', 'money', 'MAX(0,%s-(%s-%s+{in:extra}))' % (FLOOR, CASH_NOW, BAMT)),
    O('Cash on the payment date, counting your weekly cash in', 'money', AFTER), O('Short of the floor on that date', 'money', 'MAX(0,%s-%s)' % (FLOOR, AFTER)),
    O('Bills due in the next 7 days', 'money', 'SUMIFS({range:bills.amount},{range:bills.due_date},"<="&({today}+7),{range:bills.paid},%s)' % NO), O('Bills due in the next 14 days', 'money', 'SUMIFS({range:bills.amount},{range:bills.due_date},"<="&({today}+14),{range:bills.paid},%s)' % NO),
    O('Lowest cash after any bill in 13 weeks', 'money', 'MIN({range:bills.cash_after})+{in:extra}'), O('First date cash falls below the floor', 'date', 'IF(%s=0,"",%s)' % (FSTB, FSTB)),
    O('Verdict', 'text', 'IF(%s>=%s,IF(%s-{today}<=0,%s,%s),IF(%s-%s<=%s/2,%s,%s))' % (AFTER, FLOOR, BDUE, ck('Pay now'), ck('Pay on the due date'), FLOOR, AFTER, BAMT, ck('Negotiate terms with the supplier'), ck('Delay and ask the supplier')))],
  GR('What if', ('Move 14 days', {'move': 14}), ('Move 30 days', {'move': 30}), ('Add 10000 of cash', {'extra': 10000}))))
# 15 safe owner draw
CASHSAFE = 'INDEX({range:forecast.owner_pay},1)+MIN({range:forecast.slack_per_k})'
PPM = '(SUMIFS({range:pnl.net_profit},%s)*(1-{in:tax})/12)' % L12('pnl.month')
SAFE = 'MAX(0,MIN(%s,%s))' % (PPM, CASHSAFE)
tools.append(TOOL('safe_draw', 'Safe Owner Draw', 'Safe owner draw: the monthly owner pay that profit and cash can both carry',
  'Type your tax set-aside percent (confirm with your adviser) and the owner pay you take each month, draw and bonus together: profit after tax, the pay your cash plan can carry all year and a cut, hold or raise verdict.', [
    I('tax', 'Tax set-aside percent', TAX_SET_ASIDE_PCT, 'pct'), I('pay', 'Owner pay each month, draw and bonus', OWNER_DRAW + 24000)], [
    O('Net profit, last 12 months', 'money', 'SUMIFS({range:pnl.net_profit},%s)' % L12('pnl.month')), O('Tax set-aside on that profit', 'money', 'MAX(0,SUMIFS({range:pnl.net_profit},%s))*{in:tax}' % L12('pnl.month')),
    O('Profit after tax set-aside, each month', 'money', PPM), O('Owner pay taken, last 12 months average', 'money', '(SUMIFS({range:cash.owner_draw},%s)+SUMIFS({range:cash.owner_bonus},%s))/12' % (L12('cash.month'), L12('cash.month'))),
    O('Lowest closing cash in your plan', 'money', 'MIN({range:forecast.closing_cash})'), O('Cash above the floor at the lowest month', 'money', 'MIN({range:forecast.closing_cash})-%s' % FLOOR),
    O('Owner pay the cash plan can carry, each month', 'money', CASHSAFE), O('Safe owner pay each month', 'money', SAFE), O('Owner pay now against the safe pay', 'money', '{in:pay}-%s' % SAFE),
    O('Profit left each month after owner pay and tax', 'money', '%s-{in:pay}' % PPM),
    O('Verdict', 'text', 'IF({in:pay}>%s*1.05,%s,IF({in:pay}<%s*0.8,%s,%s))' % (SAFE, ck('Cut the owner pay'), SAFE, ck('Room to raise the owner pay'), ck('Hold the owner pay')))],
  GR('What if', ('Pay 25000', {'pay': 25000}), ('Pay 45000', {'pay': 45000}), ('Tax 30 percent', {'tax': 0.3}))))
# 16 tax set-aside tool
LASTPAY = 'SUMPRODUCT(MAX(({range:cash.tax_paid}>0)*({range:cash.month}<=%s)*{range:cash.month}))' % MS
NEXTQ = 'DATE(YEAR({today}),(INT((MONTH({today})-1)/3)+1)*3+1,1)'
MUNT = '((YEAR(%s)-YEAR({today}))*12+MONTH(%s)-MONTH({today}))' % (NEXTQ, NEXTQ)
SINCE = '{in:pct}*SUMIFS({range:pnl.net_profit},{range:pnl.month},">"&%s,{range:pnl.net_profit},">0")' % LASTPAY
STILL = 'MAX(0,%s-%s)' % (TAXAVG, SINCE)
AVG3 = '{in:pct}*SUMIFS({range:pnl.net_profit},%s,{range:pnl.net_profit},">0")/3' % L3('pnl.month')
YR = '{range:pnl.month},">="&DATE(YEAR({today}),1,1),{range:pnl.month},"<="&%s' % MS
tools.append(TOOL('tax_check', 'Tax Set-aside Tool', 'Tax set-aside: how much to put aside before the next payment (confirm with your adviser)',
  'Type your set-aside percent (confirm with your adviser): profit and tax set aside this year, tax paid, the estimate of the next payment from your history, what is still to set aside each month and an on track or set aside more verdict.', [
    I('pct', 'Set-aside percent of profit (confirm with your adviser)', TAX_SET_ASIDE_PCT, 'pct')], [
    O('Net profit this year to date', 'money', 'SUMIFS({range:pnl.net_profit},%s)' % YR), O('Set aside this year at your percent', 'money', '{in:pct}*SUMIFS({range:pnl.net_profit},%s,{range:pnl.net_profit},">0")' % YR),
    O('Tax paid this year', 'money', 'SUMIFS({range:cash.tax_paid},{range:cash.month},">="&DATE(YEAR({today}),1,1),{range:cash.month},"<="&%s)' % MS), O('Last payment month', 'date', LASTPAY), O('Next payment month', 'date', NEXTQ),
    O('Months until the next payment', 'int', MUNT), O('Estimate of the next payment, from your history', 'money', TAXAVG), O('Set aside since the last payment', 'money', SINCE), O('Still to set aside', 'money', STILL),
    O('To set aside each month until then', 'money', 'IFERROR(%s/%s,0)' % (STILL, MUNT)), O('Average set aside, last 3 closed months', 'money', AVG3),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(IFERROR(%s/%s,0)<=%s,%s,%s))' % (STILL, ck('Covered for the next payment'), STILL, MUNT, AVG3, ck('On track'), ck('Set aside more each month')))],
  GR('What if', ('Set aside 20 percent', {'pct': 0.2}), ('Set aside 30 percent', {'pct': 0.3}), ('Set aside 35 percent', {'pct': 0.35}))))
# 17 break-even revenue solver
BE = '((({in:fixed}+{in:draw})/{in:margin}))'
REV12 = '(SUMIFS({range:pnl.revenue},%s)/12)' % L12('pnl.month')
tools.append(TOOL('break_even', 'Break-even Revenue Solver', 'Break-even revenue: what each month must bill to cover costs and the owner draw',
  'Type fixed costs, the owner draw, your gross margin and the average ticket: the revenue each month and week you must bill, the jobs a week, your 12-month average against it and the same at minus and plus 10 percent margin.', [
    I('fixed', 'Fixed costs each month: overhead and vehicles', D.DEF['fixed']), I('draw', 'Owner draw each month', OWNER_DRAW), I('margin', 'Gross margin after technician pay, materials and permits', D.DEF['margin'], 'pct'), I('ticket', 'Average ticket', D.DEF['ticket'])], [
    O('Revenue needed each month', 'money', BE), O('Revenue needed each week', 'money', BE + '/4.345'), O('Jobs needed each week', 'num', 'IFERROR(%s/{in:ticket}/4.345,0)' % BE),
    O('Your average revenue, last 12 months', 'money', REV12), O('Above or below break-even', 'pct', 'IFERROR(%s/%s-1,0)' % (REV12, BE)),
    O('Margin minus 10 percent: revenue needed', 'money', '({in:fixed}+{in:draw})/({in:margin}*0.9)'), O('Margin minus 10 percent: jobs a week', 'num', 'IFERROR(({in:fixed}+{in:draw})/({in:margin}*0.9)/{in:ticket}/4.345,0)'),
    O('Margin plus 10 percent: revenue needed', 'money', '({in:fixed}+{in:draw})/({in:margin}*1.1)'), O('Margin plus 10 percent: jobs a week', 'num', 'IFERROR(({in:fixed}+{in:draw})/({in:margin}*1.1)/{in:ticket}/4.345,0)'),
    O('Verdict', 'text', 'IF(%s<%s,%s,IF(%s<%s*1.15,%s,%s))' % (REV12, BE, ck('Below break-even'), REV12, BE, ck('Just above break-even'), ck('Comfortably above break-even')))],
  GR('What if', ('Fixed costs plus 5000', {'fixed': D.DEF['fixed'] + 5000}), ('Margin 35 percent', {'margin': 0.35}), ('Draw 12000', {'draw': 12000}))))
# 18 profit and loss by season
SE = ['Heating season', 'Cooling season', 'Shoulder season']
def SN(c, s, lo, hi): return 'SUMIFS({range:pnl.%s},{range:pnl.season},%s,{range:pnl.month},">="&EDATE(%s,%d),{range:pnl.month},"<"&EDATE(%s,%d))' % (c, tok('season', s), MS, lo, MS, hi)
NET = [SN('net_profit', s, -12, 0) for s in SE]
def pickname(f):
    return 'IF(%s=%s(%s),%s,IF(%s=%s(%s),%s,%s))' % (NET[0], f, ','.join(NET), tok('season', SE[0]), NET[1], f, ','.join(NET), tok('season', SE[1]), tok('season', SE[2]))
tools.append(TOOL('season_pnl', 'Profit and Loss by Season', 'Profit and loss by season against the same months a year earlier',
  'Type the net margin you want: revenue, net profit and net margin of the heating, cooling and shoulder seasons over the last 12 closed months, the same months a year earlier, the season carrying the year and the weakest.', [
    I('target', 'Net margin you want', 0.12, 'pct')],
  sum([[O('%s: revenue' % s, 'money', SN('revenue', s, -12, 0)), O('%s: net profit' % s, 'money', SN('net_profit', s, -12, 0)),
        O('%s: net margin' % s, 'pct', 'IFERROR(%s/%s,0)' % (SN('net_profit', s, -12, 0), SN('revenue', s, -12, 0))), O('%s: net profit a year earlier' % s, 'money', SN('net_profit', s, -24, -12))] for s in SE], []) + [
    O('Season carrying the year', 'text', pickname('MAX')), O('Weakest season', 'text', pickname('MIN')),
    O('Verdict', 'text', 'IF(MIN(%s)<0,%s,IF(IFERROR(MIN(%s)/MIN(%s,%s,%s),0)<{in:target},%s,%s))' % (','.join(NET), ck('A season loses money'), ','.join(NET), SN('revenue', SE[0], -12, 0), SN('revenue', SE[1], -12, 0), SN('revenue', SE[2], -12, 0), ck('Weak season'), ck('Every season makes money')))],
  GR('What if', ('Target 8 percent', {'target': 0.08}), ('Target 20 percent', {'target': 0.2}))))
assert len(tools) == 18, len(tools)
TT = {'register_check': ('Invoice register check: open, past due, verdict', 'Type the days to look back and the share of invoiced money past due you accept: invoices, amounts, deposits, the open and past due balance and a chase now or on track verdict.'),
 'unbilled_check': ('Complete but not invoiced: money not yet billed', 'Type the days a job may wait: completed jobs with no invoice, the money not yet billed, those past the limit and the three to invoice first, ranked by value and age.'),
 'deposit_check': ('Deposits on large jobs: cash tied up and cover', 'Type the job size, your deposit percent and the equipment share of the price: large jobs without a deposit, the cash tied up and whether your percent covers the equipment.'),
 'financing_check': ('Financing offer: share used and where to offer it', 'Type the close rates you see with and without financing (your own estimates): share financed, the ticket of each group, the monthly payment and an offer on larger jobs, all or stop verdict.'),
 'method_mix': ('Payment methods: invoices and days to paid', 'Type the days to look back and the days to paid you accept: invoices, share and average days to paid for each method, the slowest method named and a verdict.'),
 'ageing_analyser': ('Ageing: open invoices by days outstanding', 'Type the shares over 60 days that turn amber and red: open invoices in four buckets, the oldest invoice, the three oldest accounts and a traffic light.'),
 'chase_list': ('Chase list: who to chase first', 'Type the chase calls you can make in a week: invoices past due, the money at stake, the share your calls cover and the ten to chase first with the next action; a verdict follows.'),
 'promise_tracker': ('Promise tracker: due soon and broken', 'Type the days ahead to watch: promises due in that time with the amount, broken promises on invoices still open, the three largest and a call today or wait verdict.'),
 'dtp_analyser': ('Days to paid by segment against your last 12 months', 'Type the days to paid you want and what marks a slow segment: your 12-month average, the last 90 days, the slowest job type, technician and site type and a verdict.'),
 'landlord_review': ('Landlord account: pre-pay, reduce terms or keep', 'Type an account number and your limits: balance, open invoices, oldest invoice, money over 60 days and share past terms, with a pre-pay, reduce terms or keep terms verdict.'),
 'writeoff_check': ('Write-off check: invoices at risk of loss', 'Type the days outstanding and the job margin: invoices older than that with no open promise, the balance at risk, the extra sales needed to win it back and the oldest invoice.'),
 'cash_forecast': ('Seasonal cash forecast: lowest month and cover', 'Type a change in cash in and an extra monthly cost: closing cash after 3, 6 and 12 months from your own history, the lowest month, months below the floor and a verdict.'),
 'slow_summer': ('Slow-summer test: cooling cash in cut', 'Type the cut in cooling season cash in: cash lost, lowest cash with the cut, months below the floor, base, best and worst rows and a sensitivity row from 5 to 25 percent.'),
 'bill_check': ('Supplier bill: pay now, on due date or negotiate', 'Type a bill number, days to move the payment and extra cash: cash after the bill, cash on the due date, bills due in 7 and 14 days, the first date below the floor and a verdict.'),
 'safe_draw': ('Safe owner draw: what profit and cash can carry', 'Type your tax set-aside percent (confirm with your adviser) and your owner pay: profit after tax, the pay your cash plan can carry all year and a cut, hold or raise verdict.'),
 'tax_check': ('Tax set-aside: put aside before the next payment', 'Type your set-aside percent (confirm with your adviser): profit and set-aside this year, tax paid, the next payment estimate, what is still to set aside each month and a verdict.'),
 'break_even': ('Break-even revenue: what each month must bill', 'Type fixed costs, owner draw, gross margin and average ticket: revenue and jobs a week needed, your 12-month average against it and the same at minus and plus 10 percent margin.'),
 'season_pnl': ('Profit and loss by season against last year', 'Type the net margin you want: revenue, net profit and margin of the heating, cooling and shoulder seasons, the same months a year earlier, the season carrying the year and the weakest.')}
for _t in tools: _t['title'], _t['hint'] = TT[_t['key']]
