"""Home care agency suite part 5: the 18 decision tools (Client Invoices, Deposits and Payers)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hc5_lists import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, d): return IN(k, label, 'list', key(lst, d), list=lst)
O = OUT
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YS = 'DATE(YEAR({today}),1,1)'

# ---- 1 invoice draft
def RATE(b): return 'SUMIFS({range:rate_card.bill_rate},{range:rate_card.service},{in:svc},{range:rate_card.band},%s)*SUMIFS({range:payers.rate_share},{range:payers.payer},{in:payer})' % tok('band', b)
HK = {'Weekday': 'wee', 'Evening': 'eve', 'Weekend': 'wek', 'Night': 'nig', 'Holiday': 'hol'}
CH1 = {b: '{in:h_%s}*%s' % (HK[b], RATE(b)) for b in BANDS}
HRS1 = '({in:h_wee}+{in:h_eve}+{in:h_wek}+{in:h_nig}+{in:h_hol})'
CARE1 = '(' + '+'.join(CH1[b] for b in BANDS) + ')'
AGREED1 = '({in:weekly}*{in:weeks})'
# ---- 15 payer cash forecast
def PU(): return '(' + '+'.join('({range:claims.payer}=%s)*INDEX({range:payers.pay_days},%d)' % (tok('payer', p), n) for n, p in ((2, 'Care insurer'), (3, 'Third-party payer A'), (4, 'Third-party payer B'))) + ')'
OPEN15 = '(({range:claims.status}=%s)+({range:claims.status}=%s)+({range:claims.status}=%s))' % (tok('clmst', 'Submitted'), tok('clmst', 'Accepted'), tok('clmst', 'Resubmitted'))
EXP15 = '({range:claims.submitted_on}+ROUND(%s*CHOOSE({in:sc},1,0.9,1.2),0)+{in:extra})' % PU()
def WEEK15(w):
    lo = '' if w == 1 else '*(%s>={today}+%d)' % (EXP15, 7 * (w - 1))
    return 'SUMPRODUCT(%s*{range:claims.billed_amount}%s*(%s<{today}+%d))' % (OPEN15, lo, EXP15, 7 * w)
# ---- 8 priority
def TOPI(col, k): return 'INDEX({range:invoices.%s},MATCH(%d,{range:invoices.collect_rank},0))' % (col, k)
def TOPC(col, k): return 'INDEX({range:claims.%s},MATCH(%d,{range:claims.chase_rank},0))' % (col, k)
# ---- 9
def AVG3T(col): return 'AVERAGEIFS({range:days_to_pay.%s},{range:days_to_pay.month},">="&DATE(YEAR({today}),MONTH({today})-3,1),{range:days_to_pay.month},"<"&%s)' % (col, MS)
def LASTY(col): return 'SUMIFS({range:days_to_pay.%s},{range:days_to_pay.month},DATE(YEAR({today})-1,MONTH({today}),1))' % col
# ---- 12
SVC_MIN = 'SUMIFS({range:rate_card.bill_rate},{range:rate_card.service},{in:svc},{range:rate_card.band},%s)' % tok('band', 'Weekday')
SVC_MAX = 'SUMIFS({range:rate_card.bill_rate},{range:rate_card.service},{in:svc},{range:rate_card.band},%s)' % tok('band', 'Holiday')
SH12 = 'SUMIFS({range:payers.rate_share},{range:payers.payer},{in:payer})'
# ---- 17
REV17 = '({in:hours}*{in:rate}*((1-{in:share})+{in:share}*{in:pshare}))'
DAYS17 = '({in:share}*{in:pdays}+(1-{in:share})*{in:vdays})'

tools = [
 TOOL('invoice_draft', 'Invoice Draft Builder', 'Invoice draft from delivered hours with the agreement check',
  'Choose service and payer, type hours per time band, deposit and agreed travel charge; see the total, the gap from agreed hours and Send or Check hours. A one-person agency can use it.', [
  IL('svc', 'Service', 'svc', 'Companion care'), IL('payer', 'Payer', 'payer', 'Private pay'), I('h_wee', 'Weekday hours', 22, 'num'), I('h_eve', 'Evening hours', 6, 'num'), I('h_wek', 'Weekend hours', 8, 'num'),
  I('h_nig', 'Night hours', 0, 'num'), I('h_hol', 'Holiday hours', 2, 'num'), I('weeks', 'Weeks in the invoice period', 2), I('weekly', 'Agreed hours a week', 18, 'num'), I('travel', 'Agreed travel charge for the period', 18, 'money'),
  I('dep', 'Deposit applied', 0, 'money')], [
  O('Weekday charge', 'money', CH1['Weekday']), O('Evening charge', 'money', CH1['Evening']), O('Weekend charge', 'money', CH1['Weekend']), O('Night charge', 'money', CH1['Night']), O('Holiday charge', 'money', CH1['Holiday']),
  O('Care charge before travel and deposit', 'money', CARE1), O('Invoice total after travel and deposit', 'money', CARE1 + '+{in:travel}-{in:dep}'), O('Hours billed', 'num', HRS1), O('Agreed hours for the period', 'num', AGREED1),
  O('Difference from the agreement, hours', 'num', HRS1 + '-' + AGREED1), O('Difference, %', 'pct', '(' + HRS1 + '-' + AGREED1 + ')/' + AGREED1),
  O('Average rate per hour billed', 'money', 'IF(%s>0,%s/%s,0)' % (HRS1, CARE1, HRS1)),
  O('Verdict', 'text', 'IF(ABS(%s-%s)<={set:hours_tolerance}*%s,%s,%s)' % (HRS1, AGREED1, AGREED1, vd('Send'), vd('Check hours')))],
  GR('What if', ('Hours 8 over the agreement', {'h_wee': 30}), ('Quiet fortnight: 20 hours', {'h_wee': 12, 'h_eve': 4, 'h_wek': 4, 'h_hol': 0}), ('Care insurer pays', {'payer': '=' + tok('payer', 'Care insurer')}),
     ('Deposit applied: 520', {'dep': 520}), ('Night hours added', {'h_nig': 10}))),
 TOOL('hours_mismatch', 'Hours Mismatch Check', 'Agreed, delivered and billed hours: bill, query or credit',
  'Type the hours agreed for the month, the hours delivered and the hours you billed; see the gap, the money at stake and whether to bill, query the client or credit.', [
  I('agreed', 'Agreed hours for the month', 72, 'num'), I('deliv', 'Delivered hours (from the visits)', 66, 'num'), I('billed', 'Billed hours', 75, 'num'), I('rate', 'Bill rate per hour', 34, 'money')], [
  O('Billed minus agreed hours', 'num', '{in:billed}-{in:agreed}'), O('Billed minus delivered hours', 'num', '{in:billed}-{in:deliv}'), O('Delivered minus agreed hours', 'num', '{in:deliv}-{in:agreed}'),
  O('Billed above delivered, %', 'pct', '({in:billed}-{in:deliv})/{in:deliv}'), O('Money billed for hours not delivered', 'money', 'MAX(0,{in:billed}-{in:deliv})*{in:rate}'),
  O('Accepted gap, %', 'pct', '{set:hours_tolerance}'), O('Hours rows that mismatch, last 3 months', 'int', 'COUNTIFS({range:hours_check.flag},%s,{range:hours_check.month},">="&DATE(YEAR({today}),MONTH({today})-3,1))' % ck('Query hours')),
  O('Share of hours rows that mismatch, last 3 months', 'pct', 'IFERROR(COUNTIFS({range:hours_check.flag},%s,{range:hours_check.month},">="&DATE(YEAR({today}),MONTH({today})-3,1))/COUNTIFS({range:hours_check.month},">="&DATE(YEAR({today}),MONTH({today})-3,1)),0)' % ck('Query hours')),
  O('Verdict', 'text', 'IF(({in:billed}-{in:deliv})>{set:hours_tolerance}*{in:deliv},%s,IF(ABS({in:deliv}-{in:agreed})>{set:hours_tolerance}*{in:agreed},%s,%s))' % (vd('Credit'), vd('Query'), vd('Bill')))],
  GR('What if', ('Billed what was delivered', {'billed': 66}), ('Delivered far below the agreement', {'deliv': 52, 'billed': 52}), ('Billed 5 hours over', {'billed': 71}), ('Higher rate: 37', {'rate': 37}))),
 TOOL('travel_charge', 'Travel and Mileage Charge', 'Travel and mileage charge per visit',
  'Type km and minutes per visit, the agreed charge per km and per travel hour and visits a month; see the charge per visit and month and whether it covers your cost.', [
  I('km', 'Kilometres to the visit', 7.5, 'num'), I('rate_km', 'Agreed charge per km', 0.55, 'money'), I('mins', 'Travel minutes per visit', 22), I('rate_h', 'Agreed charge per travel hour', 20, 'money'),
  I('pay', 'Pay rate per hour for travel time', 19, 'money'), I('visits', 'Visits a month', 26)], [
  O('Mileage charge per visit', 'money', '{in:km}*{in:rate_km}'), O('Travel time charge per visit', 'money', '{in:mins}/60*{in:rate_h}'), O('Charge per visit', 'money', '{in:km}*{in:rate_km}+{in:mins}/60*{in:rate_h}'),
  O('Charge per month', 'money', '({in:km}*{in:rate_km}+{in:mins}/60*{in:rate_h})*{in:visits}'), O('Your cost per visit (mileage and paid travel)', 'money', '{in:km}*{set:mileage_rate}+{in:mins}/60*{in:pay}*(1+{set:payroll_burden})'),
  O('Margin per visit', 'money', '{in:km}*{in:rate_km}+{in:mins}/60*{in:rate_h}-({in:km}*{set:mileage_rate}+{in:mins}/60*{in:pay}*(1+{set:payroll_burden}))'),
  O('Share of the cost recovered', 'pct', '({in:km}*{in:rate_km}+{in:mins}/60*{in:rate_h})/({in:km}*{set:mileage_rate}+{in:mins}/60*{in:pay}*(1+{set:payroll_burden}))'),
  O('Charge per km that just covers the cost', 'money', '({in:km}*{set:mileage_rate}+{in:mins}/60*{in:pay}*(1+{set:payroll_burden})-{in:mins}/60*{in:rate_h})/{in:km}'),
  O('Verdict', 'text', 'IF({in:km}*{in:rate_km}+{in:mins}/60*{in:rate_h}>={in:km}*{set:mileage_rate}+{in:mins}/60*{in:pay}*(1+{set:payroll_burden}),%s,%s)' % (vd('Covers cost'), vd('Below cost')))],
  GR('What if', ('No travel time charge', {'rate_h': 0}), ('Far client: 18 km', {'km': 18, 'mins': 35}), ('Mileage only at your cost', {'rate_km': 0.40, 'rate_h': 0}), ('Higher km charge: 0.70', {'rate_km': 0.70}))),
 TOOL('deposit_balance', 'Deposit Balance Check', 'Weeks of hours the deposit still covers',
  'Type the balance held, the weekly bill and the minimum weeks of cover; see the weeks left, the date it runs out, the top-up needed and whether to top up now.', [
  I('bal', 'Balance held', 780, 'money'), I('weekly', 'Weekly bill', 520, 'money'), I('minw', 'Minimum weeks of cover', 2, 'num')], [
  O('Weeks of hours left', 'num', '{in:bal}/{in:weekly}'), O('Days of cover left', 'int', 'ROUND({in:bal}/{in:weekly}*7,0)'), O('Date the balance runs out', 'date', '{today}+ROUND({in:bal}/{in:weekly}*7,0)'),
  O('Top-up needed to reach the minimum cover', 'money', 'MAX(0,{in:minw}*{in:weekly}-{in:bal})'), O('Date the cover falls to the minimum', 'date', '{today}+MAX(0,ROUND(({in:bal}/{in:weekly}-{in:minw})*7,0))'),
  O('Prepaid and deposit balances now below the minimum', 'int', 'COUNTIFS({range:deposits.low_flag},%s)' % ck('Low balance')),
  O('Verdict', 'text', 'IF({in:bal}/{in:weekly}<{in:minw},%s,%s)' % (vd('Top up now'), vd('Fine')))],
  GR('What if', ('Balance 1,200', {'bal': 1200}), ('Weekly bill 700', {'weekly': 700}), ('Three weeks minimum', {'minw': 3}), ('Balance 300', {'bal': 300}))),
 TOOL('prepay_topup', 'Prepayment Top-up Planner', 'How much to ask a prepaid client to top up, and when',
  'Type the balance, the weekly spend, the buffer weeks you want and the rounding; see the top-up amount, the new balance and the date of the next top-up.', [
  I('bal', 'Prepaid balance now', 940, 'money'), I('weekly', 'Weekly spend', 480, 'money'), I('buffer', 'Buffer weeks wanted', 4, 'num'), I('round', 'Round the top-up up to the nearest', 100, 'money')], [
  O('Weeks of cover now', 'num', '{in:bal}/{in:weekly}'), O('Date the balance runs out', 'date', '{today}+ROUND({in:bal}/{in:weekly}*7,0)'),
  O('Top-up amount', 'money', 'ROUNDUP(MAX(0,{in:buffer}*{in:weekly}-{in:bal})/{in:round},0)*{in:round}'),
  O('Balance after the top-up', 'money', '{in:bal}+ROUNDUP(MAX(0,{in:buffer}*{in:weekly}-{in:bal})/{in:round},0)*{in:round}'),
  O('Weeks of cover after the top-up', 'num', '({in:bal}+ROUNDUP(MAX(0,{in:buffer}*{in:weekly}-{in:bal})/{in:round},0)*{in:round})/{in:weekly}'),
  O('Date of the next top-up (cover back to the minimum)', 'date', '{today}+ROUND((({in:bal}+ROUNDUP(MAX(0,{in:buffer}*{in:weekly}-{in:bal})/{in:round},0)*{in:round})/{in:weekly}-{set:deposit_weeks})*7,0)'),
  O('Prepaid balance held, all prepaid clients', 'money', 'SUMIFS({range:deposits.balance},{range:deposits.kind},%s,{range:deposits.status},%s)' % (tok('depk', 'Prepayment'), tok('depst', 'Held'))),
  O('Verdict', 'text', 'IF({in:buffer}*{in:weekly}>{in:bal},%s,%s)' % (vd('Top up now'), vd('Fine')))],
  GR('What if', ('Buffer of 6 weeks', {'buffer': 6}), ('Spend 650 a week', {'weekly': 650}), ('Round to 250', {'round': 250}), ('Balance already 2,500', {'bal': 2500}))),
 TOOL('deposit_return', 'Deposit Return at End of Care', 'What happens to the deposit when care ends',
  'Type the deposit held, the final invoice and any other open balance; see the amount applied, the refund or what the client still owes and the verdict.', [
  I('dep', 'Deposit held', 1480, 'money'), I('final', 'Final invoice', 960, 'money'), I('other', 'Other open balance', 120, 'money')], [
  O('Total owed by the client', 'money', '{in:final}+{in:other}'), O('Deposit applied to what is owed', 'money', 'MIN({in:dep},{in:final}+{in:other})'), O('Refund to the client', 'money', 'MAX(0,{in:dep}-{in:final}-{in:other})'),
  O('Client still owes after the deposit', 'money', 'MAX(0,{in:final}+{in:other}-{in:dep})'), O('Refund as a share of the deposit', 'pct', 'MAX(0,{in:dep}-{in:final}-{in:other})/{in:dep}'),
  O('Deposits held now, all clients', 'int', 'COUNTIFS({range:deposits.status},%s,{range:deposits.kind},%s)' % (tok('depst', 'Held'), tok('depk', 'Deposit'))),
  O('Verdict', 'text', 'IF({in:dep}>{in:final}+{in:other},%s,IF({in:dep}<{in:final}+{in:other},%s,%s))' % (vd('Refund due'), vd('Client owes'), vd('Hold the deposit')))],
  GR('What if', ('Bigger final invoice: 1,900', {'final': 1900}), ('No other balance', {'other': 0}), ('Deposit 520', {'dep': 520}), ('Exactly equal', {'final': 1360}))),
 TOOL('ageing_buckets', 'Ageing Bucket Calculator', 'A/R in four age buckets and the share over 60 days',
  'Type the open amounts in each age bucket (days since the invoice date); see the share over 60 days against your target, the live figure and the verdict. A/R is money owed to the agency.', [
  I('a1', 'Open amount 0-30 days', 44500, 'money'), I('a2', 'Open amount 31-60 days', 21500, 'money'), I('a3', 'Open amount 61-90 days', 2200, 'money'), I('a4', 'Open amount over 90 days', 0, 'money')], [
  O('Total A/R', 'money', '{in:a1}+{in:a2}+{in:a3}+{in:a4}'), O('Share 0-30 days', 'pct', '{in:a1}/({in:a1}+{in:a2}+{in:a3}+{in:a4})'), O('Share 31-60 days', 'pct', '{in:a2}/({in:a1}+{in:a2}+{in:a3}+{in:a4})'),
  O('Amount over 60 days', 'money', '{in:a3}+{in:a4}'), O('Share over 60 days', 'pct', '({in:a3}+{in:a4})/({in:a1}+{in:a2}+{in:a3}+{in:a4})'), O('Target share over 60 days', 'pct', '{set:over60_target}'),
  O('Amount to collect to reach the target', 'money', 'MAX(0,{in:a3}+{in:a4}-{set:over60_target}*({in:a1}+{in:a2}+{in:a3}+{in:a4}))'),
  O('Live share over 60 days in the invoices', 'pct', 'IFERROR((SUMIFS({range:invoices.balance},{range:invoices.age_band},%s)+SUMIFS({range:invoices.balance},{range:invoices.age_band},%s))/SUM({range:invoices.balance}),0)' % (tok('ageband', 'Days 61-90'), tok('ageband', 'Days over 90'))),
  O('Average share over 60 days at the last 4 month ends', 'pct', 'IFERROR(AVERAGEIFS({range:ageing_month.over60_share},{range:ageing_month.as_of},">="&({today}-125)),0)'),
  O('Verdict', 'text', 'IF(({in:a3}+{in:a4})/({in:a1}+{in:a2}+{in:a3}+{in:a4})<={set:over60_target},%s,IF(({in:a3}+{in:a4})/({in:a1}+{in:a2}+{in:a3}+{in:a4})<=2*{set:over60_target},%s,%s))' % (vd('Healthy'), vd('Watch'), vd('Act')))],
  GR('What if', ('More over 60: 9,000', {'a3': 9000}), ('Over 90 days: 4,000', {'a4': 4000}), ('Everything current', {'a2': 0, 'a3': 0, 'a4': 0}), ('Slow month: 31-60 at 40,000', {'a2': 40000}))),
 TOOL('collection_priority', 'Collection Priority List', 'The five balances to phone first',
  'Unpaid invoices past their due date are ranked by balance and days past due; type the balance above which a call is worth making and see the five to phone first with the amount at risk.', [
  I('min', 'Phone first when the top balance is above', 500, 'money')], [
  O('Phone first 1: client', 'text', 'IFERROR(%s&"","")' % TOPI('client', 1)), O('Phone first 1: balance', 'money', 'IFERROR(%s,0)' % TOPI('balance', 1)), O('Phone first 1: days past due', 'int', 'IFERROR(%s,0)' % TOPI('days_past_due', 1)),
  O('Phone first 2: client', 'text', 'IFERROR(%s&"","")' % TOPI('client', 2)), O('Phone first 2: balance', 'money', 'IFERROR(%s,0)' % TOPI('balance', 2)), O('Phone first 2: days past due', 'int', 'IFERROR(%s,0)' % TOPI('days_past_due', 2)),
  O('Phone first 3: client', 'text', 'IFERROR(%s&"","")' % TOPI('client', 3)), O('Phone first 3: balance', 'money', 'IFERROR(%s,0)' % TOPI('balance', 3)), O('Phone first 3: days past due', 'int', 'IFERROR(%s,0)' % TOPI('days_past_due', 3)),
  O('Phone first 4: client', 'text', 'IFERROR(%s&"","")' % TOPI('client', 4)), O('Phone first 4: balance', 'money', 'IFERROR(%s,0)' % TOPI('balance', 4)), O('Phone first 4: days past due', 'int', 'IFERROR(%s,0)' % TOPI('days_past_due', 4)),
  O('Phone first 5: client', 'text', 'IFERROR(%s&"","")' % TOPI('client', 5)), O('Phone first 5: balance', 'money', 'IFERROR(%s,0)' % TOPI('balance', 5)), O('Phone first 5: days past due', 'int', 'IFERROR(%s,0)' % TOPI('days_past_due', 5)),
  O('Amount at risk in the five', 'money', 'SUMIFS({range:invoices.balance},{range:invoices.collect_rank},"<=5")'), O('Invoices past due now', 'int', 'COUNTIFS({range:invoices.days_past_due},">0")'),
  O('Share of all A/R in the five', 'pct', 'IFERROR(SUMIFS({range:invoices.balance},{range:invoices.collect_rank},"<=5")/SUM({range:invoices.balance}),0)'),
  O('Verdict', 'text', 'IF(COUNT({range:invoices.collect_rank})=0,%s,IF(IFERROR(%s,0)>={in:min},%s,%s))' % (vd('No overdue balance'), TOPI('balance', 1), vd('Phone first'), vd('Watch')))],
  GR('Call threshold', ('Threshold 100', {'min': 100}), ('Threshold 1,000', {'min': 1000}), ('Threshold 2,500', {'min': 2500}), ('Threshold 5,000', {'min': 5000}))),
 TOOL('days_to_be_paid', 'Days to Be Paid', 'Days to be paid against targets and your own history',
  'Type this month\'s billing, collections and average days for private pay (self-funded) and for payers; the tool compares them with your targets, your last 3 months and the same month last year.', [
  I('billed', 'Billed this month', 90500, 'money'), I('coll', 'Collected from this month\'s invoices', 66000, 'money'), I('pd', 'Average days to be paid, private pay', 7.3, 'num'), I('qd', 'Average days to be paid, payers', 63, 'num')], [
  O('Collection rate', 'pct', '{in:coll}/{in:billed}'), O('Private pay target, days', 'int', '{set:days_to_pay_private}'), O('Private pay vs target, days', 'num', '{in:pd}-{set:days_to_pay_private}'),
  O('Private pay, 3-month average in your history', 'num', 'IFERROR(%s,0)' % AVG3T('private_days')), O('Private pay vs 3-month average, days', 'num', '{in:pd}-IFERROR(%s,0)' % AVG3T('private_days')),
  O('Private pay, same month last year', 'num', LASTY('private_days')), O('Payers target, days', 'int', '{set:days_to_pay_payer}'), O('Payers vs target, days', 'num', '{in:qd}-{set:days_to_pay_payer}'),
  O('Payers, 3-month average in your history', 'num', 'IFERROR(%s,0)' % AVG3T('payer_days')), O('Payers vs 3-month average, days', 'num', '{in:qd}-IFERROR(%s,0)' % AVG3T('payer_days')), O('Payers, same month last year', 'num', LASTY('payer_days')),
  O('Collection rate wanted', 'pct', '{set:collection_target}'),
  O('Verdict', 'text', 'IF({in:qd}>{set:payer_red_days},%s,IF(OR({in:pd}>{set:days_to_pay_private},{in:qd}>{set:days_to_pay_payer},{in:coll}/{in:billed}<{set:collection_target}),%s,%s))' % (vd('Act'), vd('Watch'), vd('Healthy')))],
  GR('What if', ('Payers pay in 45 days', {'qd': 45}), ('Private pay slows to 16 days', {'pd': 16}), ('Everything collected', {'coll': 90500}), ('Weak month: 50,000 collected', {'coll': 50000}))),
 TOOL('payment_plan', 'Late Balance Payment Plan', 'Instalments and the date a late balance clears',
  'Type the balance, the number of instalments, the first date and the days between them; see the instalment, the last instalment, the date the balance clears and whether to offer the plan.', [
  I('bal', 'Balance to clear', 6740.5, 'money'), I('inst', 'Instalments', 8), I('first', 'First instalment date', 'today+7', 'date'), I('gap', 'Days between instalments', 7), I('weekly', 'Weekly bill for current care', 520, 'money')], [
  O('Instalment', 'money', 'ROUND({in:bal}/{in:inst},2)'), O('Last instalment', 'money', '{in:bal}-ROUND({in:bal}/{in:inst},2)*({in:inst}-1)'), O('Date the balance clears', 'date', '{in:first}+{in:gap}*({in:inst}-1)'),
  O('Weeks until the balance clears', 'num', '({in:first}-{today}+{in:gap}*({in:inst}-1))/7'), O('Paid in the first 4 instalments', 'money', 'ROUND({in:bal}/{in:inst},2)*MIN(4,{in:inst})'),
  O('Instalment as a share of the weekly bill', 'pct', 'ROUND({in:bal}/{in:inst},2)/{in:weekly}'), O('Instalments needed to stay within 12 weeks', 'int', 'ROUNDUP({in:bal}/(ROUND(({in:bal}/MAX(1,INT((84-({in:first}-{today}))/{in:gap})+1)),2)),0)'),
  O('Verdict', 'text', 'IF(({in:first}-{today}+{in:gap}*({in:inst}-1))/7<=12,%s,%s)' % (vd('Offer the plan'), vd('Shorten the plan')))],
  GR('What if', ('4 instalments', {'inst': 4}), ('12 instalments', {'inst': 12}), ('Every 14 days', {'gap': 14, 'inst': 8}), ('Smaller balance: 2,200', {'bal': 2200}), ('Start in 21 days', {'first': '={today}+21'}))),
 TOOL('pause_care', 'Pause-care Decision', 'Continue, send a reminder or pause care',
  'Type the unpaid weeks, the weekly bill and the deposit held; see your exposure and Continue, Reminder or Pause (check your own local rules and agreement terms before pausing care).', [
  I('weeks', 'Unpaid weeks of care', 3, 'num'), I('weekly', 'Weekly bill', 520, 'money'), I('dep', 'Deposit held', 520, 'money')], [
  O('Unpaid amount', 'money', '{in:weeks}*{in:weekly}'), O('Weeks covered by the deposit', 'num', '{in:dep}/{in:weekly}'), O('Exposure after the deposit', 'money', 'MAX(0,{in:weeks}*{in:weekly}-{in:dep})'),
  O('Exposure in weeks of care', 'num', 'MAX(0,{in:weeks}-{in:dep}/{in:weekly})'), O('Weeks at which you remind', 'int', '{set:reminder_weeks}'), O('Weeks at which you pause', 'int', '{set:pause_weeks}'),
  O('Clients with a balance past 42 days now', 'int', 'COUNTIFS({range:invoices.days_past_due},">42")'),
  O('Verdict', 'text', 'IF(MAX(0,{in:weeks}-{in:dep}/{in:weekly})>={set:pause_weeks},%s,IF(MAX(0,{in:weeks}-{in:dep}/{in:weekly})>={set:reminder_weeks},%s,%s))' % (vd('Pause'), vd('Reminder'), vd('Continue')))],
  GR('Unpaid weeks', ('1 week unpaid', {'weeks': 1}), ('2 weeks unpaid', {'weeks': 2}), ('4 weeks unpaid', {'weeks': 4}), ('6 weeks unpaid', {'weeks': 6}), ('No deposit held', {'dep': 0}))),
 TOOL('claim_check', 'Claim Submission Check', 'Is this payer claim ready to submit',
  'Choose payer and service, type hours, claim amount, whether the authorisation reference is present and the date the period ended; see the checks and Submit or Fix first (status and amounts only).', [
  IL('payer', 'Payer', 'payer', 'Care insurer'), IL('svc', 'Service', 'svc', 'Personal care help'), I('hours', 'Hours in the claim', 63.5, 'num'), I('amount', 'Claim amount', 2190, 'money'),
  I('auth', 'Authorisation reference present (1 yes, 0 no)', 1), I('pend', 'Date the period ended', 'today-12', 'date')], [
  O('Amount per hour', 'money', '{in:amount}/{in:hours}'), O('Lowest rate per hour for this payer', 'money', SVC_MIN + '*' + SH12 + '*(1-{set:rate_tolerance})'), O('Highest rate per hour for this payer', 'money', SVC_MAX + '*' + SH12 + '*(1+{set:rate_tolerance})'),
  O('Rate inside the card range (1 yes)', 'int', 'IF(AND({in:amount}/{in:hours}>=%s*%s*(1-{set:rate_tolerance}),{in:amount}/{in:hours}<=%s*%s*(1+{set:rate_tolerance})),1,0)' % (SVC_MIN, SH12, SVC_MAX, SH12)),
  O('Days since the period ended', 'int', '{today}-{in:pend}'), O('Days left in the submission window', 'int', '{set:claim_window_days}-({today}-{in:pend})'), O('Last day to submit', 'date', '{in:pend}+{set:claim_window_days}'),
  O('Authorisation present (1 yes, 0 no)', 'int', '{in:auth}'),
  O('Verdict', 'text', 'IF(AND({in:auth}=1,{today}-{in:pend}<={set:claim_window_days},{in:hours}>0,{in:amount}/{in:hours}>=%s*%s*(1-{set:rate_tolerance}),{in:amount}/{in:hours}<=%s*%s*(1+{set:rate_tolerance})),%s,%s)' % (SVC_MIN, SH12, SVC_MAX, SH12, vd('Submit'), vd('Fix first')))],
  GR('What if', ('No authorisation reference', {'auth': 0}), ('Period ended 40 days ago', {'pend': '={today}-40'}), ('Amount too high: 3,400', {'amount': 3400}), ('Third-party payer B', {'payer': '=' + tok('payer', 'Third-party payer B')}))),
 TOOL('claim_followup', 'Claim Follow-up Ranking', 'Which open claims to chase first',
  'Open claims are ranked by amount and age against the payer\'s usual days; type how many days before the usual days you start chasing and see the five to chase with the amount and the verdict.', [
  I('lead', 'Start chasing this many days before the usual days', 7)], [
  O('Chase 1: claim', 'text', 'IFERROR(%s&"","")' % TOPC('claim_id', 1)), O('Chase 1: amount', 'money', 'IFERROR(%s,0)' % TOPC('outstanding_amount', 1)), O('Chase 1: days outstanding', 'int', 'IFERROR(%s,0)' % TOPC('days_outstanding', 1)),
  O('Chase 2: claim', 'text', 'IFERROR(%s&"","")' % TOPC('claim_id', 2)), O('Chase 2: amount', 'money', 'IFERROR(%s,0)' % TOPC('outstanding_amount', 2)), O('Chase 2: days outstanding', 'int', 'IFERROR(%s,0)' % TOPC('days_outstanding', 2)),
  O('Chase 3: claim', 'text', 'IFERROR(%s&"","")' % TOPC('claim_id', 3)), O('Chase 3: amount', 'money', 'IFERROR(%s,0)' % TOPC('outstanding_amount', 3)), O('Chase 3: days outstanding', 'int', 'IFERROR(%s,0)' % TOPC('days_outstanding', 3)),
  O('Chase 4: claim', 'text', 'IFERROR(%s&"","")' % TOPC('claim_id', 4)), O('Chase 4: amount', 'money', 'IFERROR(%s,0)' % TOPC('outstanding_amount', 4)), O('Chase 4: days outstanding', 'int', 'IFERROR(%s,0)' % TOPC('days_outstanding', 4)),
  O('Chase 5: claim', 'text', 'IFERROR(%s&"","")' % TOPC('claim_id', 5)), O('Chase 5: amount', 'money', 'IFERROR(%s,0)' % TOPC('outstanding_amount', 5)), O('Chase 5: days outstanding', 'int', 'IFERROR(%s,0)' % TOPC('days_outstanding', 5)),
  O('Usual days of the top payer', 'int', 'IFERROR(%s,0)' % TOPC('payer_days', 1)), O('Amount in the five claims', 'money', 'SUMIFS({range:claims.outstanding_amount},{range:claims.chase_rank},"<=5")'),
  O('Open claims waiting for payment', 'int', 'COUNT({range:claims.chase_rank})'),
  O('Verdict', 'text', 'IF(COUNT({range:claims.chase_rank})=0,%s,IF(IFERROR(%s,0)>=IFERROR(%s,0)-{in:lead},%s,%s))' % (vd('No open claims'), TOPC('days_outstanding', 1), TOPC('payer_days', 1), vd('Chase now'), vd('Wait')))],
  GR('Lead days', ('No lead: chase at the usual days', {'lead': 0}), ('Chase 14 days early', {'lead': 14}), ('Chase 30 days early', {'lead': 30}), ('Chase 3 days early', {'lead': 3}))),
 TOOL('short_pay', 'Short-pay Recovery', 'Resubmit, accept or write off a short payment',
  'Type the billed and the paid amount and your chance of recovering the difference; see the shortfall, the expected recovery after your cost and whether to resubmit, accept or write off.', [
  I('billed', 'Billed amount', 2041.6, 'money'), I('paid', 'Paid amount', 1892.35, 'money'), IL('reason', 'Reason given', 'clmrsn', 'Hours mismatch'), I('chance', 'Chance the payer pays on a resubmission', 0.7, 'pct')], [
  O('Shortfall', 'money', '{in:billed}-{in:paid}'), O('Shortfall as a share of the billed amount', 'pct', '({in:billed}-{in:paid})/{in:billed}'), O('Expected recovery on a resubmission', 'money', '({in:billed}-{in:paid})*{in:chance}'),
  O('Staff cost of resubmitting', 'money', '{set:collect_cost}'), O('Net expected recovery', 'money', '({in:billed}-{in:paid})*{in:chance}-{set:collect_cost}'),
  O('Chance needed to break even', 'pct', '{set:collect_cost}/({in:billed}-{in:paid})'), O('Short payments with this reason, last 12 months', 'int', 'COUNTIFS({range:claims.reason},{in:reason},{range:claims.status},%s,{range:claims.paid_on},">="&({today}-365))' % tok('clmst', 'Short-paid')),
  O('Short-paid amount, last 90 days', 'money', 'SUMIFS({range:claims.short_amount},{range:claims.paid_on},">="&({today}-90))'),
  O('Verdict', 'text', 'IF(({in:billed}-{in:paid})/{in:billed}<={set:short_pay_accept},%s,IF(({in:billed}-{in:paid})*{in:chance}>{set:collect_cost},%s,%s))' % (vd('Accept'), vd('Resubmit'), vd('Write off')))],
  GR('What if', ('Tiny difference: paid 2,030', {'paid': 2030}), ('Low chance: 5%', {'chance': 0.05}), ('Rate difference reason', {'reason': '=' + tok('clmrsn', 'Rate difference')}), ('Large shortfall: paid 1,200', {'paid': 1200}))),
 TOOL('payer_forecast', 'Payer Cash Forecast', 'Expected payer cash by week for the next 8 weeks',
  'Open claims are paid on the payer\'s usual days after submission; choose a scenario (1 Base, 2 Best, 3 Worst) and extra days to see the expected cash for each of the next 8 weeks.', [
  I('sc', 'Scenario: 1 Base, 2 Best (10% faster), 3 Worst (20% slower)', 1), I('extra', 'Extra days payers take', 0)], [
  O('Week 1 (overdue claims included)', 'money', WEEK15(1)), O('Week 2', 'money', WEEK15(2)), O('Week 3', 'money', WEEK15(3)), O('Week 4', 'money', WEEK15(4)), O('Week 5', 'money', WEEK15(5)), O('Week 6', 'money', WEEK15(6)),
  O('Week 7', 'money', WEEK15(7)), O('Week 8', 'money', WEEK15(8)), O('Expected within 8 weeks', 'money', 'SUMPRODUCT(%s*{range:claims.billed_amount}*(%s<{today}+56))' % (OPEN15, EXP15)),
  O('Open claims not rejected', 'money', 'SUMPRODUCT(%s*{range:claims.billed_amount})' % OPEN15),
  O('Share expected within 8 weeks', 'pct', 'IFERROR(SUMPRODUCT(%s*{range:claims.billed_amount}*(%s<{today}+56))/SUMPRODUCT(%s*{range:claims.billed_amount}),0)' % (OPEN15, EXP15, OPEN15)),
  O('Verdict', 'text', 'IF(IFERROR(SUMPRODUCT(%s*{range:claims.billed_amount}*(%s<{today}+56))/SUMPRODUCT(%s*{range:claims.billed_amount}),0)>=0.9,%s,%s)' % (OPEN15, EXP15, OPEN15, vd('Cash is steady'), vd('Cash is thin')))],
  GR('Scenario', ('Best case', {'sc': 2}), ('Worst case', {'sc': 3}), ('Payers 10 days later', {'extra': 10}), ('Worst case, 10 days later', {'sc': 3, 'extra': 10}))),
 TOOL('writeoff_decision', 'Write-off Decision', 'Pursue the balance or write it off',
  'Type the balance, its age, the cost to collect and your own guess of the chance of payment; see the expected recovery, who must approve and the verdict (confirm tax treatment with your adviser).', [
  I('bal', 'Balance', 1420, 'money'), I('age', 'Age of the balance, days since the invoice date', 120), I('cost', 'Cost to collect (calls, letters, staff time)', 180, 'money'), I('chance', 'Chance of payment (your own guess)', 0.35, 'pct')], [
  O('Expected recovery', 'money', '{in:bal}*{in:chance}'), O('Net after the cost to collect', 'money', '{in:bal}*{in:chance}-{in:cost}'), O('Chance needed to break even', 'pct', '{in:cost}/{in:bal}'),
  O('Approval needed', 'text', 'IF({in:bal}>{set:writeoff_limit},%s,%s)' % (ck('Owner approval'), ck('Office approval'))), O('Written off so far this year', 'money', 'SUMIFS({range:writeoffs.amount},{range:writeoffs.date},">="&%s)' % YS),
  O('Written off this year plus this balance', 'money', 'SUMIFS({range:writeoffs.amount},{range:writeoffs.date},">="&%s)+{in:bal}' % YS),
  O('Share of this year\'s billing', 'pct', 'IFERROR((SUMIFS({range:writeoffs.amount},{range:writeoffs.date},">="&%s)+{in:bal})/SUMIFS({range:days_to_pay.invoiced},{range:days_to_pay.month},">="&%s),0)' % (YS, YS)),
  O('Verdict', 'text', 'IF(AND({in:bal}*{in:chance}>{in:cost},{in:age}<=365),%s,%s)' % (vd('Pursue'), vd('Write off')))],
  GR('What if', ('Chance 10%', {'chance': 0.1}), ('Old balance: 500 days', {'age': 500}), ('Cheap to collect: 40', {'cost': 40}), ('Small balance: 300', {'bal': 300}))),
 TOOL('payer_mix', 'Payer Mix Sensitivity', 'What a larger share of payer hours does to cash and margin',
  'Type billed hours, rate and cost per hour and the share of hours paid by payers; see days to be paid, cash tied up and margin, then compare 10 to 50 percent in the table below.', [
  I('hours', 'Billed hours a month', 3900), I('rate', 'Average rate card rate per hour', 34.5, 'money'), I('cost', 'Loaded pay cost per hour (pay plus payroll burden)', 22.8, 'money'), I('share', 'Share of hours paid by payers', 0.25, 'pct'),
  I('pshare', 'Average share of the rate card payers pay', 0.9, 'pct'), I('vdays', 'Days to be paid, private pay', 8, 'num'), I('pdays', 'Days to be paid, payers', 47, 'num')], [
  O('Revenue a month', 'money', REV17), O('Gross margin a month', 'money', REV17 + '-{in:hours}*{in:cost}'), O('Gross margin, %', 'pct', '(%s-{in:hours}*{in:cost})/%s' % (REV17, REV17)),
  O('Average days to be paid', 'num', DAYS17), O('Cash tied up in unpaid invoices', 'money', REV17 + '/30*' + DAYS17),
  O('Extra cash tied up against an all private pay agency', 'money', REV17 + '/30*' + DAYS17 + '-{in:hours}*{in:rate}/30*{in:vdays}'), O('Margin lost to payer rates a month', 'money', '{in:hours}*{in:rate}*{in:share}*(1-{in:pshare})'),
  O('Wanted margin, %', 'pct', '{set:target_margin}'), O('Verdict', 'text', 'IF((%s-{in:hours}*{in:cost})/%s>={set:target_margin},%s,%s)' % (REV17, REV17, vd('Margin on target'), vd('Margin below target')))],
  GR('Share of hours paid by payers', ('10 percent', {'share': 0.10}), ('20 percent', {'share': 0.20}), ('30 percent', {'share': 0.30}), ('40 percent', {'share': 0.40}), ('50 percent', {'share': 0.50}))),
 TOOL('payer_days_grid', 'Payer Days What-if', 'Cash tied up in claims against days to be paid',
  'Type claims outstanding, claims billed a month and the days payers take; see days of billing outstanding and the cash tied up or freed, then compare 30 to 60 days in the table below.', [
  I('out', 'Claims outstanding', 32000, 'money'), I('billed', 'Claims billed a month', 38000, 'money'), I('days', 'Days payers take to pay', 52, 'num')], [
  O('Billed per day', 'money', '{in:billed}/30'), O('Days of billing outstanding', 'num', '{in:out}/({in:billed}/30)'), O('Cash tied up at these days', 'money', '{in:billed}/30*{in:days}'),
  O('Outstanding above (+) or below (-) that level', 'money', '{in:out}-{in:billed}/30*{in:days}'), O('Cash freed by payers paying one day faster', 'money', '{in:billed}/30'),
  O('Cash freed at the payer target days', 'money', 'MAX(0,{in:days}-{set:days_to_pay_payer})*{in:billed}/30'), O('Claims outstanding in the claims table now', 'money', 'SUM({range:claims.outstanding_amount})'),
  O('Verdict', 'text', 'IF({in:days}>{set:payer_red_days},%s,IF({in:days}>{set:days_to_pay_payer},%s,%s))' % (vd('Act'), vd('Watch'), vd('Healthy')))],
  GR('Days payers take', ('30 days', {'days': 30}), ('38 days', {'days': 38}), ('45 days', {'days': 45}), ('52 days', {'days': 52}), ('60 days', {'days': 60}), ('Claims 50,000 outstanding', {'out': 50000}))),
]
assert len(tools) == 18, len(tools)
