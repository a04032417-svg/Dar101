"""Therapy practice suite part 3: the 18 decision tools (client fees, accounts and packages)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th3_lists import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, d): return IN(k, label, 'list', key(lst, d), list=lst)
O = OUT
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def FEEY(x): return 'SUMIFS({range:fees.fee},{range:fees.service},%s,{range:fees.year},YEAR({today}))' % x
def MINY(x): return 'SUMIFS({range:fees.minutes},{range:fees.service},%s,{range:fees.year},YEAR({today}))' % x
def SCN(a, b, c): return 'IF({in:sc}=%s,%s,IF({in:sc}=%s,%s,%s))' % (tok('scn', 'Base'), a, tok('scn', 'Best'), b, c)
def IFV(cond, a, b): return 'IF(%s,%s,%s)' % (cond, a, b)
def EQ(x, lst, lab): return '{in:%s}=%s' % (x, tok(lst, lab))

# 1 fee quote
BASE1 = FEEY('{in:svc}')
PK1 = '(1-IF({in:pk}>=10,0.1,IF({in:pk}>=6,0.05,0)))'
FEE1 = 'IF(%s,%s,IF(%s,%s*{in:sl},IF(%s,%s*%s,{in:cp})))' % (EQ('ft', 'feetype', 'Standard'), BASE1, EQ('ft', 'feetype', 'Sliding scale'), BASE1, EQ('ft', 'feetype', 'Package'), BASE1, PK1)
# 2 sliding
PP2 = '({in:inc}/{in:hh})'
POS2 = 'MATCH(%s,{range:bands.income_from},1)' % PP2
SH2 = 'INDEX({range:bands.share},%s)' % POS2
# 3 package
UN3 = '{in:un}'
CS3 = SCN('1', '0.9', '1.15')
DMAX3 = '(1-(1-%s)*{in:cost}*%s/((1-{set:package_margin})*{in:fee}))' % (UN3, CS3)
PRICE3 = '({in:num}*{in:fee}*(1-{in:disc}))'
COST3 = '({in:num}*(1-%s)*{in:cost}*%s)' % (UN3, CS3)
# 4 invoice
SUB4 = '({in:num}*{in:fee}*{in:share}+{in:lc}*{in:fee}*{in:share}*{set:late_fee_pct})'
# 5 A/R
INVN5 = 'SUMIFS({range:invoices.amount_due},{range:invoices.issued_on},">"&({today}-{in:win}),{range:invoices.issued_on},"<="&{today})'
BAL5 = 'SUM({range:invoices.balance})'
def BK5(b): return 'SUMIFS({range:invoices.balance},{range:invoices.age_band},%s)' % ab(b)
DIA5 = 'IFERROR(%s/%s*{in:win},0)' % (BAL5, INVN5)
O30 = 'SUMIFS({range:invoices.balance},{range:invoices.days_overdue},">30")'
def TOP5(k, col): return 'IFERROR(INDEX({range:ar_clients.%s},MATCH(%d,{range:ar_clients.chase_rank},0)),"")' % (col, k)
# 6 plan
M6 = 'IF({in:inst}>0,-INT(-{in:bal}/{in:inst}),{in:months})'
IN6 = 'ROUND({in:bal}/%s,2)' % M6
MAX6 = '({set:plan_max_share}*{in:mfee})'
# 7 reminders
DO7 = '({today}-{in:due})'
PR7 = 'IF({in:pw}=0,0,{today}+{in:pw})'
NXT7 = 'IF(%s<{in:gap},{in:due}+{in:gap},IF(%s<2*{in:gap},{in:due}+2*{in:gap},IF(%s<3*{in:gap},{in:due}+3*{in:gap},{in:due}+{set:final_notice_days})))' % (DO7, DO7, DO7)
# 8 card on file
MV8 = '({in:late}*{in:mv})'
NET8 = '({in:num}*{in:mv}*{in:att}*{set:chase_cost}+%s*{in:wo}-%s*{in:cf})' % (MV8, MV8)
# 10 fee rise
FNEW10 = '({in:fee}*(1+{in:rise}))'
BE10 = 'IFERROR({in:rise}*{in:fee}/(%s-{in:cost}),0)' % FNEW10
# 11 write-off
GONE11 = '(IF(%s,1,0)+IF(%s,1,0))' % (EQ('st', 'cstatus', 'Discharged'), EQ('st', 'cstatus', 'Referred out'))
P11 = 'MAX(0.05,0.9-{in:days}/200-{in:broken}*0.15-%s*0.2)' % GONE11
NET11 = '({in:bal}*%s-{in:att}*{in:cost})' % P11
# 13 forecast
WIN13 = '{range:invoices.issued_on},">="&({today}-120),{range:invoices.issued_on},"<="&({today}-30)'
ALL13 = 'COUNTIFS(%s)' % WIN13
PR13 = 'IFERROR(COUNTIFS(%s,{range:invoices.days_to_pay},"<=14")/%s,0)' % (WIN13, ALL13)
NO13 = 'IFERROR(COUNTIFS(%s,{range:invoices.days_to_pay},">14",{range:invoices.days_to_pay},"<=30")/%s,0)' % (WIN13, ALL13)
PS13 = 'MAX(0,MIN(1,%s+%s))' % (PR13, SCN('0', '0.1', '-0.1'))
PN13 = 'MIN(%s,%s)' % (NO13, '(1-%s)' % PS13)
SL13 = '(1-%s-%s)' % (PS13, PN13)
def WK13(k):
    # week 1-2 prompt, weeks 3-4 normal, weeks 5-8 slow (a share of them pays)
    parts = []
    if k <= 2: parts.append('%s/2' % PS13)
    if 3 <= k <= 4: parts.append('%s/2' % PN13)
    if k >= 5: parts.append('%s*{in:slowpay}/4' % SL13)
    return 'ROUND({in:inv}*(%s),0)' % '+'.join(parts)
# 14 revenue per hour
FEE14 = FEEY('{in:svc}'); MIN14 = MINY('{in:svc}')
RH14 = '(%s*(1-{in:disc})*{in:att}*60/(%s+{in:buf}))' % (FEE14, MIN14)
# 15 days to cash
OWN15 = 'IFERROR(AVERAGEIFS({range:invoices.days_to_pay},{range:invoices.issued_on},">="&({today}-120),{range:invoices.issued_on},"<="&{today}),0)'
AVG15 = '({in:da}+(1-{in:cs})*{in:db})'
# 16 concession
CON16 = '({in:num}*{in:sess}*{in:fee}*(1-{in:share}))'
# 17 late fee
# 18 net
def GAPC(c): return 'SUMIFS({range:gap.amount},{range:gap.month},DATE(YEAR({today}),MONTH({today})-1,1),{range:gap.cause},%s)' % tok('gapcause', c)
GA, GB, GC, GD = GAPC('Sliding scale'), GAPC('Waived late fee'), GAPC('Written off'), GAPC('Unpaid')
MX18 = 'MAX(%s,%s,%s,%s)' % (GA, GB, GC, GD)
def BM(k): return 'DATE(YEAR({today}),MONTH({today})-%d,1)' % k
def NETM(m, col='collected'): return 'SUMIFS({range:billing.%s},{range:billing.month},%s)' % (col, m)

tools = [
 TOOL('fee_quote', 'Session Fee Quote', 'Session fee quote: what the client pays per session',
  'Choose the service and the fee type, with the sliding share, package size, co-pay and card on file; see the fee per session, the late-cancel fee, the deposit and the verdict.', [
  IL('svc', 'Service', 'svc', 'Individual session'), IL('ft', 'Fee type', 'feetype', 'Sliding scale'), I('sl', 'Sliding share of the fee', 0.7, 'pct'), I('pk', 'Package size (sessions)', 6), I('cp', 'Payer co-pay per session', 15, 'money'),
  I('card', 'Card on file: 1 yes, 0 no', 0)], [
  O('List fee this year', 'money', BASE1), O('Fee per session the client pays', 'money', FEE1), O('Saving per session against the list fee', 'money', BASE1 + '-' + FEE1),
  O('Price of a package of this size', 'money', '{in:pk}*%s*%s' % (BASE1, PK1)),
  O('Late-cancel fee', 'money', FEE1 + '*{set:late_fee_pct}'), O('Deposit to take at booking', 'money', 'IF({in:card}=1,0,{set:deposit})'),
  O('Verdict', 'text', 'IF(%s,%s,IF(%s,%s,IF(%s,%s,%s)))' % (EQ('ft', 'feetype', 'Standard'), vb('Standard fee'), EQ('ft', 'feetype', 'Sliding scale'), vb('Sliding scale applies'), EQ('ft', 'feetype', 'Package'), vb('Package price applies'), vb('Payer co-pay applies')))],
  GR('What if', ('Standard fee', {'ft': '=' + tok('feetype', 'Standard')}), ('Sliding scale at 60%', {'sl': 0.6}), ('Package of 10', {'ft': '=' + tok('feetype', 'Package'), 'pk': 10}),
         ('Payer co-pay of 25', {'ft': '=' + tok('feetype', 'Third-party payer'), 'cp': 25}), ('Couples session, card on file', {'svc': '=' + tok('svc', 'Couples session'), 'card': 1}))),
 TOOL('sliding_calc', 'Sliding Scale Calculator', 'Sliding scale calculator: band, share and review date',
  'Type the household income, household size and the date of the last assessment; see the income band, the share of the fee, the fee per session and whether the band is still confirmed.', [
  I('inc', 'Household income a year', 36000, 'money'), I('hh', 'People in the household', 3), I('asd', 'Date of the last assessment', 'today-200', 'date')], [
  O('Income per person', 'money', PP2), O('Band number', 'int', POS2), O('Share of the fee', 'pct', SH2), O('Fee per individual session', 'money', 'ROUND(%s*%s,2)' % (SH2, FEEY(tok('svcall', 'Individual session')))),
  O('Concession per session', 'money', '%s*(1-%s)' % (FEEY(tok('svcall', 'Individual session')), SH2)), O('Review due on', 'date', 'EDATE({in:asd},{set:sliding_review_months})'),
  O('Days until the review', 'int', 'EDATE({in:asd},{set:sliding_review_months})-{today}'),
  O('Verdict', 'text', 'IF(EDATE({in:asd},{set:sliding_review_months})>={today},%s,%s)' % (vb('Band confirmed'), vb('Review at the next assessment')))],
  GR('What if', ('Income 18000', {'inc': 18000}), ('Income 60000', {'inc': 60000}), ('Household of 5', {'hh': 5}), ('Assessed 14 months ago', {'asd': '={today}-427'}), ('Income 90000, single', {'inc': 90000, 'hh': 1}))),
 TOOL('package_price', 'Package Price Builder', 'Package price builder with the deepest safe discount',
  'Type the fee, sessions, discount, share never used and your cost per session; pick Base, Best or Worst; see the price, the saving and the largest discount that keeps the margin target.', [
  I('fee', 'List fee per session', 125, 'money'), I('num', 'Sessions in the package', 6), I('disc', 'Discount offered', 0.05, 'pct'), I('un', 'Share of sessions never used', 0.08, 'pct'), I('cost', 'Cost per delivered session', 85, 'money'),
  IL('sc', 'Scenario', 'scn', 'Base')], [
  O('Value at full fees', 'money', '{in:num}*{in:fee}'), O('Package price', 'money', PRICE3), O('Price per session', 'money', '{in:fee}*(1-{in:disc})'), O('Saving for the client', 'money', '{in:num}*{in:fee}*{in:disc}'),
  O('Expected cost of delivery', 'money', COST3), O('Margin on the package', 'money', PRICE3 + '-' + COST3), O('Margin share', 'pct', 'IFERROR((%s-%s)/%s,0)' % (PRICE3, COST3, PRICE3)),
  O('Money kept against full fees of the sessions used', 'money', '%s-{in:num}*(1-%s)*{in:fee}' % (PRICE3, UN3)), O('Largest discount that keeps the margin target', 'pct', 'MAX(0,%s)' % DMAX3),
  O('Verdict', 'text', 'IF({in:disc}<=%s,%s,%s)' % (DMAX3, vb('Offer it'), vb('Discount too deep')))],
  GR('What if', ('Discount 10%', {'disc': 0.1}), ('Discount 15%', {'disc': 0.15}), ('Worst case', {'sc': '=' + tok('scn', 'Worst')}), ('Package of 10 at 10%', {'num': 10, 'disc': 0.1}), ('Best case at 12%', {'sc': '=' + tok('scn', 'Best'), 'disc': 0.12}))),
 TOOL('invoice_builder', 'Monthly Invoice Builder', 'Monthly invoice builder: amount due after the deposit',
  'Type the sessions, the fee, the client share, late cancels, the deposit and the sessions with no fee; see the late-cancel fees, the amount due, the due date and whether to send the invoice.', [
  I('num', 'Attended sessions this month', 5), I('fee', 'Fee per session', 125, 'money'), I('share', 'Share of the fee the client pays', 0.75, 'pct'), I('lc', 'Late cancels and no-shows charged', 1), I('dep', 'Deposit applied', 50, 'money'),
  I('nofee', 'Sessions with no fee set', 0), I('iss', 'Issue date', 'today', 'date')], [
  O('Session charges', 'money', '{in:num}*{in:fee}*{in:share}'), O('Late-cancel fees', 'money', '{in:lc}*{in:fee}*{in:share}*{set:late_fee_pct}'), O('Subtotal', 'money', SUB4), O('Deposit applied', 'money', 'MIN({in:dep},%s)' % SUB4),
  O('Amount due', 'money', 'MAX(0,%s-{in:dep})' % SUB4), O('Share of the invoice covered by the deposit', 'pct', 'IFERROR(MIN({in:dep},%s)/%s,0)' % (SUB4, SUB4)), O('Due date', 'date', '{in:iss}+{set:invoice_days}'),
  O('Verdict', 'text', 'IF({in:nofee}>0,%s,%s)' % (vb('Check first'), vb('Send now')))],
  GR('What if', ('No deposit', {'dep': 0}), ('8 sessions', {'num': 8}), ('Two late cancels', {'lc': 2}), ('A session with no fee', {'nofee': 1}), ('Full fee, standard client', {'share': 1}))),
 TOOL('ar_chase', 'AR Aging and Chase-first List', 'A/R aging, Days in A/R and the five clients to chase first',
  'Reads your invoices: balance by age band (days since issue), Days in A/R against your maximum and the five clients to chase first, ranked by overdue balance times days past due.', [
  I('win', 'Days of billing to compare with', 90), I('max', 'Most Days in A/R you accept', 40), I('collect', 'Money you collect from the chase', 3000, 'money')], [
  O('Balance 0-30 days', 'money', BK5('0-30')), O('Balance 31-60 days', 'money', BK5('31-60')), O('Balance 61-90 days', 'money', BK5('61-90')), O('Balance 90+ days', 'money', BK5('90+')), O('Balance outstanding', 'money', BAL5),
  O('Days in A/R now', 'num', DIA5), O('Days in A/R after the chase', 'num', 'IFERROR(MAX(0,%s-{in:collect})/%s*{in:win},0)' % (BAL5, INVN5)), O('Balance over 30 days overdue', 'money', O30),
  O('Chase first: 1', 'text', TOP5(1, 'client')), O('Overdue balance: 1', 'money', TOP5(1, 'overdue')), O('Chase first: 2', 'text', TOP5(2, 'client')), O('Overdue balance: 2', 'money', TOP5(2, 'overdue')),
  O('Chase first: 3', 'text', TOP5(3, 'client')), O('Chase first: 4', 'text', TOP5(4, 'client')), O('Chase first: 5', 'text', TOP5(5, 'client')),
  O('Verdict', 'text', 'IF(OR(%s>{in:max},%s>0),%s,%s)' % (DIA5, O30, vb('Chase first'), vb('On track')))],
  GR('What if', ('Collect 1000', {'collect': 1000}), ('Collect 6000', {'collect': 6000}), ('Compare with 60 days', {'win': 60}), ('Maximum of 10 days', {'max': 10}), ('Compare with 120 days', {'win': 120}))),
 TOOL('plan_builder', 'Payment Plan Builder', 'Payment plan builder: instalments, end date and a fit check',
  'Type the balance, the number of months (or an instalment) and a month of the client\'s fees; see the instalment, the last date and whether the instalment is within a quarter of a month of fees.', [
  I('bal', 'Balance to spread', 960, 'money'), I('months', 'Number of monthly instalments', 6), I('inst', 'Or a fixed instalment (0 to use the months)', 0, 'money'), I('mfee', 'One month of the client\'s fees', 640, 'money'), I('start', 'First instalment date', 'today+7', 'date')], [
  O('Instalments', 'int', M6), O('Instalment', 'money', IN6), O('Largest instalment allowed', 'money', MAX6), O('Instalment as a share of a month of fees', 'pct', IN6 + '/{in:mfee}'),
  O('Fewest months that fit', 'int', 'MAX(1,-INT(-{in:bal}/%s))' % MAX6), O('Last instalment due', 'date', 'EDATE({in:start},%s-1)' % M6),
  O('Verdict', 'text', 'IF(%s<=%s,%s,%s)' % (IN6, MAX6, vb('Plan fits'), vb('Extend the term')))],
  GR('What if', ('3 months', {'months': 3}), ('12 months', {'months': 12}), ('Balance 1500', {'bal': 1500}), ('Instalment of 100', {'inst': 100}), ('A month of fees at 1000', {'mfee': 1000, 'months': 4}))),
 TOOL('reminder_sched', 'Payment Reminder Schedule', 'Payment reminder schedule with the final notice date',
  'Type the invoice due date, the days between reminders and the days until a promised date; see the three reminder dates, the final notice date, the next date to send and what to do today.', [
  I('due', 'Invoice due date', 'today-10', 'date'), I('gap', 'Days between reminders', 7), I('pw', 'Days until the promised date (0 if none)', 0)], [
  O('Days past the due date', 'int', DO7), O('Reminder 1 on', 'date', '{in:due}+{in:gap}'), O('Reminder 2 on', 'date', '{in:due}+2*{in:gap}'), O('Reminder 3 on', 'date', '{in:due}+3*{in:gap}'),
  O('Final notice on', 'date', '{in:due}+{set:final_notice_days}'), O('Next date to send', 'date', NXT7), O('Days until the next date to send', 'int', NXT7 + '-{today}'),
  O('Verdict', 'text', 'IF(%s>{today},%s,IF(%s>={set:final_notice_days},%s,IF(%s>={in:gap},%s,%s)))' % (PR7, vb('Wait for the promised date'), DO7, vb('Final notice due'), DO7, vb('Send reminder'), vb('Not due yet')))],
  GR('What if', ('21 days past due', {'due': '={today}-21'}), ('Due in 3 days', {'due': '={today}+3'}), ('Promised in 5 days', {'pw': 5}), ('Reminders every 3 days', {'gap': 3}), ('30 days past due', {'due': '={today}-30'}))),
 TOOL('card_effect', 'Card on File Effect', 'Card on file effect: chasing saved against the card fee',
  'Type the late-pay balance, the late payers, the share expected to move to a card on file and the card fee; see the money no longer chased, the cost and the net effect.', [
  I('late', 'Late-pay balance now', 6000, 'money'), I('num', 'Clients who pay late', 14), I('mv', 'Share expected to move to a card on file', 0.4, 'pct'), I('cf', 'Card fee share', 0.025, 'pct'), I('att', 'Chase attempts per late payer', 3),
  I('wo', 'Share of late balance that ends in a write-off', 0.06, 'pct')], [
  O('Balance no longer chased', 'money', MV8), O('Chase attempts saved', 'num', '{in:num}*{in:mv}*{in:att}'), O('Chasing cost saved', 'money', '{in:num}*{in:mv}*{in:att}*{set:chase_cost}'),
  O('Write-offs avoided', 'money', MV8 + '*{in:wo}'), O('Card fees paid on it', 'money', MV8 + '*{in:cf}'), O('Net effect', 'money', NET8),
  O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (NET8, vb('Ask at booking'), vb('Not worth it')))],
  GR('Share moved to a card on file', ('10%', {'mv': 0.1}), ('25%', {'mv': 0.25}), ('50%', {'mv': 0.5}), ('75%', {'mv': 0.75}), ('100%', {'mv': 1}))),
 TOOL('method_cost', 'Payment Method Cost', 'Payment method cost: what card fees cost a year',
  'Type the card payments a month, the card fee share and the share you could move to bank transfer; see the yearly card cost, the saving and whether a nudge is worth it.', [
  I('card', 'Card payments a month', 18000, 'money'), I('cf', 'Card fee share', 0.025, 'pct'), I('mv', 'Share you could move to bank transfer', 0.3, 'pct'), I('worth', 'Smallest yearly saving worth the effort', 500, 'money')], [
  O('Card fees a month', 'money', '{in:card}*{in:cf}'), O('Card fees a year', 'money', '{in:card}*12*{in:cf}'), O('Yearly saving if the share moves', 'money', '{in:card}*12*{in:cf}*{in:mv}'),
  O('Card fees a year after the move', 'money', '{in:card}*12*{in:cf}*(1-{in:mv})'), O('Cost per 100 of card payments', 'money', '100*{in:cf}'),
  O('Verdict', 'text', 'IF({in:card}*12*{in:cf}*{in:mv}>={in:worth},%s,%s)' % (vb('Nudge to transfer'), vb('Keep card')))],
  GR('What if', ('Move 10%', {'mv': 0.1}), ('Move 50%', {'mv': 0.5}), ('Fee of 3%', {'cf': 0.03}), ('Card payments of 3000', {'card': 3000}), ('Card payments of 30000', {'card': 30000}))),
 TOOL('fee_rise', 'Fee Rise Impact', 'Fee rise impact with the break-even share of clients lost',
  'Type the fee, the rise, the clients, the sessions a year, your cost per session and the clients you expect to leave; see the yearly change, the break-even share of clients lost and the verdict.', [
  I('fee', 'Current fee per session', 125, 'money'), I('rise', 'Rise', 0.04, 'pct'), I('cl', 'Active clients', 120), I('sps', 'Sessions a year per client', 30), I('cost', 'Cost per delivered session', 80, 'money'), I('lost', 'Clients expected to leave', 3)], [
  O('New fee', 'money', FNEW10), O('Yearly revenue before', 'money', '{in:cl}*{in:sps}*{in:fee}'), O('Yearly revenue after', 'money', '({in:cl}-{in:lost})*{in:sps}*%s' % FNEW10),
  O('Yearly revenue change', 'money', '({in:cl}-{in:lost})*{in:sps}*%s-{in:cl}*{in:sps}*{in:fee}' % FNEW10),
  O('Yearly contribution change', 'money', '({in:cl}-{in:lost})*{in:sps}*(%s-{in:cost})-{in:cl}*{in:sps}*({in:fee}-{in:cost})' % FNEW10),
  O('Break-even share of clients lost', 'pct', BE10), O('Break-even clients lost', 'num', BE10 + '*{in:cl}'), O('Share you expect to lose', 'pct', '{in:lost}/{in:cl}'),
  O('Verdict', 'text', 'IF({in:lost}/{in:cl}<%s,%s,%s)' % (BE10, vb('Raise'), vb('Hold')))],
  GR('Five rise steps', ('Rise 2%', {'rise': 0.02}), ('Rise 3%', {'rise': 0.03}), ('Rise 5%', {'rise': 0.05}), ('Rise 7%', {'rise': 0.07}), ('Rise 10%, 12 clients leave', {'rise': 0.1, 'lost': 12}))),
 TOOL('writeoff_decision', 'Write-off Decision', 'Write-off decision: chase, offer a plan or write off',
  'Type the balance, the days overdue, the client status, the chase attempts and cost and the broken promises; see the chance of recovery, the expected net recovery and the verdict.', [
  I('bal', 'Balance', 240, 'money'), I('days', 'Days overdue', 75), IL('st', 'Client status', 'cstatus', 'Active'), I('att', 'Chase attempts still needed', 3), I('cost', 'Cost per chase attempt', 8, 'money'), I('broken', 'Broken promises', 1)], [
  O('Chance of recovery', 'pct', P11), O('Expected recovery', 'money', '{in:bal}*' + P11), O('Chasing cost', 'money', '{in:att}*{in:cost}'), O('Expected net recovery', 'money', NET11),
  O('Above the owner limit by', 'money', 'MAX(0,{in:bal}-{set:writeoff_limit})'),
  O('Verdict', 'text', 'IF(%s<=0,%s,IF({in:broken}>=1,%s,%s))' % (NET11, vb('Write off'), vb('Offer a plan'), vb('Chase')))],
  GR('What if', ('Small balance, 150 days', {'bal': 60, 'days': 150}), ('No broken promises', {'broken': 0}), ('Client discharged', {'st': '=' + tok('cstatus', 'Discharged')}), ('30 days overdue', {'days': 30}), ('Large balance of 900', {'bal': 900}))),
 TOOL('prepaid_check', 'Prepaid Balance Check', 'Prepaid balance check: can the sessions still be delivered?',
  'Type the package price, the sessions bought and used, the free sessions a week and the weeks to expiry; see the value still owed, the weeks to deliver it and the verdict.', [
  I('price', 'Package price', 1530, 'money'), I('num', 'Sessions bought', 10), I('used', 'Sessions used', 4), I('free', 'Free sessions a week for this client', 1.5, 'num'), I('wk', 'Weeks until the package expires', 12)], [
  O('Sessions left', 'int', '{in:num}-{in:used}'), O('Value still owed as sessions', 'money', '{in:price}*({in:num}-{in:used})/{in:num}'), O('Weeks to deliver them', 'num', 'IFERROR(({in:num}-{in:used})/{in:free},0)'),
  O('Weeks to spare before expiry', 'num', '{in:wk}-IFERROR(({in:num}-{in:used})/{in:free},0)'), O('Sessions a week needed', 'num', 'IFERROR(({in:num}-{in:used})/{in:wk},0)'),
  O('Verdict', 'text', 'IF(IFERROR(({in:num}-{in:used})/{in:free},999)<={in:wk},%s,%s)' % (vb('Deliverable'), vb('Too much prepaid')))],
  GR('What if', ('A quarter session a week', {'free': 0.25}), ('2 weeks left', {'wk': 2}), ('Nothing used', {'used': 0}), ('Almost used up', {'used': 9}), ('Package of 6', {'num': 6, 'used': 1, 'price': 912}))),
 TOOL('collect_forecast', 'Collection Forecast', 'Collection forecast: weekly money against the pay run',
  'Type the invoices issued, the share of slow payers who pay and the pay run; prompt, normal and slow payer shares come from your own invoices of 1 to 4 months ago; pick Base, Best or Worst.', [
  I('inv', 'Invoices issued this month', 35150, 'money'), I('slowpay', 'Share of slow payers who pay within 8 weeks', 0.85, 'pct'), I('pay', 'Pay run to cover', 26000, 'money'), IL('sc', 'Scenario', 'scn', 'Base')], [
  O('Prompt payers (paid within 14 days)', 'pct', PS13), O('Normal payers (15 to 30 days)', 'pct', PN13), O('Slow payers (over 30 days)', 'pct', SL13)] + [
  O('Expected in week %d' % k, 'money', WK13(k)) for k in range(1, 9)] + [
  O('Expected in 4 weeks', 'money', 'ROUND({in:inv}*(%s+%s),0)' % (PS13, PN13)), O('Expected in 8 weeks', 'money', 'ROUND({in:inv}*(%s+%s+%s*{in:slowpay}),0)' % (PS13, PN13, SL13)),
  O('Money left after the pay run (negative: short)', 'money', 'ROUND({in:inv}*(%s+%s),0)-{in:pay}' % (PS13, PN13)),
  O('Verdict', 'text', 'IF(ROUND({in:inv}*(%s+%s),0)>={in:pay},%s,%s)' % (PS13, PN13, vb('Covers the pay run'), vc('Short of the pay run')))],
  GR('What if', ('Best case', {'sc': '=' + tok('scn', 'Best')}), ('Worst case', {'sc': '=' + tok('scn', 'Worst')}), ('Invoices of 25000', {'inv': 25000}), ('Pay run of 33000', {'pay': 33000}), ('Slow payers pay 60%', {'slowpay': 0.6}))),
 TOOL('rev_hour', 'Revenue per Clinical Hour', 'Revenue per clinical hour and the fee that hits target',
  'Pick a service (fee and minutes come from the fee schedule); add admin minutes, the share attended and your hourly target; see the fee per clinical hour and the verdict.', [
  IL('svc', 'Service', 'svc', 'Individual session'), I('buf', 'Minutes of notes and admin per session', 10), I('att', 'Share of booked sessions attended', 0.9, 'pct'), I('disc', 'Average sliding or package discount', 0, 'pct'), I('target', 'Target fee per clinical hour', 120, 'money')], [
  O('Fee this year', 'money', FEE14), O('Session minutes', 'int', MIN14), O('Fee per clinical hour', 'money', RH14), O('Gap to the target per hour', 'money', RH14 + '-{in:target}'),
  O('Fee that hits the target', 'money', 'IFERROR({in:target}*(%s+{in:buf})/(60*{in:att}*(1-{in:disc})),0)' % MIN14), O('Rise needed', 'pct', 'MAX(0,IFERROR({in:target}*(%s+{in:buf})/(60*{in:att}*(1-{in:disc}))/%s-1,0))' % (MIN14, FEE14)),
  O('Verdict', 'text', 'IF(%s>={in:target},%s,%s)' % (RH14, vc('At target'), vc('Below target')))],
  GR('What if', ('Extended individual', {'svc': '=' + tok('svc', 'Extended individual')}), ('Couples session', {'svc': '=' + tok('svc', 'Couples session')}), ('Behaviour therapy', {'svc': '=' + tok('svc', 'Behaviour therapy')}), ('Everyone attends', {'att': 1}), ('20% average discount', {'disc': 0.2}))),
 TOOL('days_cash', 'Days to Cash', 'Days to cash: from the session to money in the bank',
  'Type the days from session to invoice, from invoice to payment and the share of clients on a card on file who pay at invoice; see the average days to cash against your maximum and your own history.', [
  I('da', 'Days from session to invoice', 15), I('db', 'Days from invoice to payment', 12), I('cs', 'Share of clients paying by card on file at invoice', 0.35, 'pct'), I('max', 'Most days to cash you accept', 40)], [
  O('Days to cash, clients who pay later', 'num', '{in:da}+{in:db}'), O('Days to cash, card on file', 'num', '{in:da}'), O('Average days to cash', 'num', AVG15), O('Your own days to pay (invoices of the last 120 days)', 'num', OWN15),
  O('Days to spare against the maximum', 'num', '{in:max}-' + AVG15), O('Days saved by moving 10% more to a card on file', 'num', '0.1*{in:db}'),
  O('Verdict', 'text', 'IF(%s<={in:max},%s,%s)' % (AVG15, vc('Within the maximum'), vc('Slow')))],
  GR('What if', ('Pay in 30 days', {'db': 30}), ('80% on card on file', {'cs': 0.8}), ('Invoice 30 days late', {'da': 30, 'db': 25}), ('Invoice in 5 days', {'da': 5}), ('Maximum of 20 days', {'max': 20}))),
 TOOL('concession_budget', 'Concession Budget', 'Concession budget: what the sliding scale costs a year',
  'Type the sliding-scale clients, their average share, the fee, the sessions a year and your yearly billing; see the yearly concession given, its share of list fees and the verdict.', [
  I('num', 'Sliding scale clients', 48), I('share', 'Average sliding share of the fee', 0.7, 'pct'), I('fee', 'Average list fee', 125, 'money'), I('sess', 'Sessions a year per client', 28), I('bill', 'Yearly billing after concessions', 420000, 'money'),
  I('maxs', 'Most you give away as a share of list fees', 0.15, 'pct')], [
  O('Yearly concession given', 'money', CON16), O('Share of list fees', 'pct', '%s/({in:bill}+%s)' % (CON16, CON16)), O('Concession per client a year', 'money', '{in:sess}*{in:fee}*(1-{in:share})'),
  O('Highest Client payment collection rate possible', 'pct', '1-%s/({in:bill}+%s)' % (CON16, CON16)), O('Net collection target', 'pct', '{set:net_collection_target}'), O('Room left under the limit', 'money', '{in:maxs}*({in:bill}+%s)-%s' % (CON16, CON16)),
  O('Verdict', 'text', 'IF(%s/({in:bill}+%s)<={in:maxs},%s,%s)' % (CON16, CON16, vc('Within target'), vc('Above target')))],
  GR('What if', ('Average share 60%', {'share': 0.6}), ('80 sliding clients', {'num': 80}), ('Average share 80%', {'share': 0.8}), ('Fee of 150', {'fee': 150}), ('Limit of 10%', {'maxs': 0.1}))),
 TOOL('latefee_recovery', 'Late-fee Recovery', 'Late-fee recovery: late-cancel fees really collected',
  'Type the late-cancel fees charged, waived and collected; see the waived share, the recovery rate on the fees still due and whether the policy is holding.', [
  I('ch', 'Late-cancel fees charged', 3600, 'money'), I('wv', 'Fees waived', 1100, 'money'), I('co', 'Fees collected', 2200, 'money'), I('maxw', 'Most you allow to be waived', 0.25, 'pct')], [
  O('Fees due after waivers', 'money', '{in:ch}-{in:wv}'), O('Waived share', 'pct', 'IFERROR({in:wv}/{in:ch},0)'), O('Recovery rate on fees due', 'pct', 'IFERROR({in:co}/({in:ch}-{in:wv}),0)'),
  O('Fees still uncollected', 'money', '{in:ch}-{in:wv}-{in:co}'), O('Collected as a share of fees charged', 'pct', 'IFERROR({in:co}/{in:ch},0)'),
  O('Extra collected if waivers fall to the limit', 'money', 'MAX(0,{in:wv}-{in:maxw}*{in:ch})*IFERROR({in:co}/({in:ch}-{in:wv}),0)'),
  O('Verdict', 'text', 'IF(IFERROR({in:wv}/{in:ch},0)<={in:maxw},%s,%s)' % (vc('Policy holding'), vc('Too many waived')))],
  GR('What if', ('Waive 1800', {'wv': 1800}), ('Collect 1500', {'co': 1500}), ('Waive nothing', {'wv': 0}), ('Charge 5000', {'ch': 5000}), ('Limit of 20%', {'maxw': 0.2}))),
 TOOL('net_check', 'Net Collection Rate Check', 'Net collection rate check with the gap and its cause',
  'Type invoiced, concessions and money received (last month is filled in); see the Net collection rate, the Client payment collection rate, the gap to target in money and its largest cause.', [
  I('inv', 'Invoiced', 29396, 'money'), I('conc', 'Concessions given', 2662.5, 'money'), I('rec', 'Money received', 28601, 'money'), I('tg', 'Net collection target', 0.95, 'pct')], [
  O('Net collection rate', 'pct', 'IFERROR({in:rec}/{in:inv},0)'), O('Client payment collection rate', 'pct', 'IFERROR({in:rec}/({in:inv}+{in:conc}),0)'), O('Money needed to reach the target', 'money', '{in:tg}*{in:inv}'),
  O('Money above (+) or below (-) the target', 'money', '{in:rec}-{in:tg}*{in:inv}'), O('Net collection rate last month (billing sheet)', 'pct', 'IFERROR(%s/%s,0)' % (NETM(BM(1)), NETM(BM(1), 'invoiced'))),
  O('Net collection rate, average of the last 3 months', 'pct', 'IFERROR((%s+%s+%s)/(%s+%s+%s),0)' % (NETM(BM(1)), NETM(BM(2)), NETM(BM(3)), NETM(BM(1), 'invoiced'), NETM(BM(2), 'invoiced'), NETM(BM(3), 'invoiced'))),
  O('Net collection rate, same month last year', 'pct', 'IFERROR(%s/%s,0)' % (NETM('DATE(YEAR({today})-1,MONTH({today})-1,1)'), NETM('DATE(YEAR({today})-1,MONTH({today})-1,1)', 'invoiced'))),
  O('Largest cause of last month\'s gap', 'text', 'IF(%s>=%s,%s,IF(%s>=%s,%s,IF(%s>=%s,%s,%s)))' % (GA, MX18, tok('gapcause', 'Sliding scale'), GB, MX18, tok('gapcause', 'Waived late fee'), GC, MX18, tok('gapcause', 'Written off'), tok('gapcause', 'Unpaid'))),
  O('Verdict', 'text', 'IF({in:rec}/{in:inv}>={in:tg},%s,%s)' % (vc('On target'), vc('Below target')))],
  GR('What if', ('Received 26000', {'rec': 26000}), ('Received 30000', {'rec': 30000}), ('Invoiced 35150, received 29062.5', {'inv': 35150, 'rec': 29062.5, 'conc': 2627.5}), ('Target 90%', {'tg': 0.9}), ('Target 98%', {'tg': 0.98}))),
]
assert len(tools) == 18, len(tools)
