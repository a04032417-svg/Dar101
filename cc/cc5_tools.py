"""Childcare center suite part 5: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc5_lists import *
from cc5_tables import MS, R, UNPAID, PART, SHORT, EXPECTED, KEPT, BROKEN, PENDING, HELD, UPC, PAYROLL, CASH, ACARD, ABANK, XFER, DEPOSIT, BASEW, CASH_NOW
import cc5_data as D

ST = D.ST
def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, dl): return IN(k, label, 'list', key(lst, dl), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def GL(lst, label): return '=' + tok(lst, label)
def SM(t, c): return 'SUM(%s)' % R(t, c)
FAMN = 'INDEX(%s,{in:row})' % R('aging', 'family')
def AGL(c): return 'IFERROR(INDEX(%s,{in:row}),0)' % R('aging', c)
ROWDEF = 1
FAMILY = ST['overdue_family']
ROWIN = lambda: I('row', 'Family row in Aging by Family, 1 is the first', 1)
CASHFLOOR = '{set:cash_floor}'
FC = lambda c: R('forecast', c)
LOWB = 'MIN(%s)' % FC('closing')
PERFAM_ = '(%s/MAX(1,%s))' % (BASEW, SM('families', 'active'))
DSO = 'IFERROR(%s/SUMIFS(%s,%s,">"&({today}-90))*90,0)' % (SM('invoices', 'open_balance'), R('invoices', 'parent_due'), R('invoices', 'issued_on'))
OV = lambda t: '"<>"&' + t
def F3(x): return 'IF(%s<%s,%s,IF(%s<%s*1.25,%s,%s))' % (x, CASHFLOOR, V('Below the floor'), x, CASHFLOOR, V('Near the floor'), V('Above the floor'))
tools = []

# 1 aging of balances
tools.append(TOOL('aging_tool', 'A R Aging of Balances', 'A/R aging of balances: who owes what and what to do next',
    'Pick a family row: the bands 0-30, 31-60, 61-90 and 90+ for the center, days outstanding, the 90+ tail and the next step for that family (aging = unpaid invoices grouped by days past due).', [
    ROWIN()], [
    O('Family', 'text', 'IFERROR(%s&"","")' % FAMN), O('Open balance, all families', 'money', SM('aging', 'balance')), O('Days 0-30', 'money', SM('aging', 'd0_30')), O('Days 31-60', 'money', SM('aging', 'd31_60')), O('Days 61-90', 'money', SM('aging', 'd61_90')),
    O('Days 90+ (the tail)', 'money', SM('aging', 'd90_plus')), O('Share over your days limit', 'pct', 'IFERROR(%s/%s,0)' % (SM('aging', 'over_limit'), SM('aging', 'balance'))),
    O('Days outstanding, on the last 90 days of billing', 'num', DSO), O('Balance of this family', 'money', AGL('balance')), O('Oldest invoice of this family, days overdue', 'int', AGL('oldest_days')),
    O('Over 60 days, this family', 'money', AGL('d61_90') + '+' + AGL('d90_plus')), O('Open invoices of this family', 'int', AGL('open_invoices')),
    O('Verdict: next step for this family', 'text', 'IFERROR(INDEX(%s,{in:row}),%s)' % (R('aging', 'step'), V('Settled')))],
    GR('What if', ('Second family', {'row': 2}), ('Third family', {'row': 3}), ('Fifth family', {'row': 5}), ('Tenth family', {'row': 10}), ('A family with a young balance', {'row': 20}))))

# 2 autopay effect
NA = 'COUNTIFS(%s,1,%s,">"&({today}-365))' % (R('invoices', 'autopay'), R('invoices', 'issued_on'))
LA = 'COUNTIFS(%s,1,%s,">"&({today}-365),%s,1)' % (R('invoices', 'autopay'), R('invoices', 'issued_on'), R('invoices', 'is_late'))
NM = 'COUNTIFS(%s,0,%s,">"&({today}-365))' % (R('invoices', 'autopay'), R('invoices', 'issued_on'))
LM = 'COUNTIFS(%s,0,%s,">"&({today}-365),%s,1)' % (R('invoices', 'autopay'), R('invoices', 'issued_on'), R('invoices', 'is_late'))
RA, RM_ = 'IFERROR(%s/%s,0)' % (LA, NA), 'IFERROR(%s/%s,0)' % (LM, NM)
AVGINV = 'IFERROR(SUMIFS(%s,%s,0,%s,">"&({today}-365))/%s,0)' % (R('invoices', 'parent_due'), R('invoices', 'autopay'), R('invoices', 'issued_on'), NM)
SAVE2 = '((%s-%s)*100*{in:minutes}/60*{set:hour_value})' % (RM_, RA)
FEE2 = '(100*%s*{in:card_share}*{set:card_fee_pct})' % AVGINV
tools.append(TOOL('autopay_tool', 'Autopay and Card on File', 'Does autopay save more chasing time than the card fee costs',
    'Compares late invoices of autopay families with manual payers over 12 months, values the chasing time saved per 100 invoices moved to autopay and sets it against the card fee: pass the fee on or not.', [
    I('minutes', 'Minutes spent chasing one late invoice', 12), I('card_share', 'Share of moved families that pay by card', 0.5, 'pct')], [
    O('Autopay share of tuition paid, 12 months', 'pct', 'IFERROR(%s/%s,0)' % (SM('collect', 'autopay_paid'), SM('collect', 'total_paid'))), O('Invoices on autopay, 12 months', 'int', NA), O('Invoices of manual payers, 12 months', 'int', NM),
    O('Late share, autopay invoices', 'pct', RA), O('Late share, manual invoices', 'pct', RM_), O('Late amount, autopay, 12 months', 'money', SM('collect', 'late_autopay')), O('Late amount, manual, 12 months', 'money', SM('collect', 'late_manual')),
    O('Card processing cost, 12 months', 'money', SM('collect', 'card_cost')), O('Late invoices avoided per 100 moved to autopay', 'num', '(%s-%s)*100' % (RM_, RA)),
    O('Value of chasing time saved per 100 invoices', 'money', SAVE2), O('Card fee on 100 moved invoices', 'money', FEE2), O('Net per 100 invoices', 'money', '%s-%s' % (SAVE2, FEE2)),
    O('Verdict', 'text', 'IF(%s-%s>=0,%s,%s)' % (SAVE2, FEE2, V('Autopay pays'), V('Pass the card fee on')))],
    GR('What if', ('Chasing takes 20 minutes', {'minutes': 20}), ('Chasing takes 5 minutes', {'minutes': 5}), ('All moved families pay by card', {'card_share': 1.0}), ('Moved families pay by bank', {'card_share': 0.0}))))

# 3 government reconciliation
GMI = lambda c: 'IFERROR(INDEX(%s,MATCH({in:month},%s,0)),0)' % (R('gov_month', c), R('gov_month', 'month'))
tools.append(TOOL('gov_tool', 'Gov Payment Reconciliation', 'Did the government payments match what was expected',
    'Pick a month: expected against received, the gap, items short or waiting and the family share still owed if the payer does not pay (a government childcare payment pays part of a family\'s tuition).', [
    I('month', 'First day of the month', iso(month_start(2)), 'date')], [
    O('Expected', 'money', GMI('expected')), O('Expected, already resolved', 'money', GMI('matched')), O('Received', 'money', GMI('received')), O('Gap', 'money', GMI('gap')),
    O('Items short', 'int', GMI('items_short')), O('Items waiting for the payer', 'int', GMI('items_waiting')), O('Share of resolved items received', 'pct', GMI('match_share')),
    O('Family share still owed if the payer does not pay', 'money', 'SUMIFS(%s,%s,{in:month},%s,%s)' % (R('gov', 'gap'), R('gov', 'month'), R('gov', 'status'), SHORT)),
    O('Days since the short payment', 'int', 'SUMIFS(%s,%s,{in:month},%s,%s)' % (R('gov', 'days_since'), R('gov', 'month'), R('gov', 'status'), SHORT)),
    O('Average gap a month, last 12 months', 'money', 'SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&%s)/12' % (R('gov_month', 'gap'), R('gov_month', 'month'), MS, R('gov_month', 'month'), MS)),
    O('Months with a gap, last 12', 'int', 'COUNTIFS(%s,">0.005",%s,">="&EDATE(%s,-12),%s,"<"&%s)' % (R('gov_month', 'gap'), R('gov_month', 'month'), MS, R('gov_month', 'month'), MS)),
    O('Verdict', 'text', 'IF(%s>0.005,IF(SUMIFS(%s,%s,{in:month},%s,%s)>{set:gov_wait_days},%s,%s),%s)' % (GMI('gap'), R('gov', 'days_since'), R('gov', 'month'), R('gov', 'status'), SHORT, V('Bill the family share'), V('Chase the payer'), V('Matched')))],
    GR('What if', ('The month before', {'month': '=EDATE(%s,-3)' % MS}), ('Last month', {'month': '=EDATE(%s,-1)' % MS}), ('This month', {'month': '=%s' % MS}), ('Four months back', {'month': '=EDATE(%s,-4)' % MS}))))

# 4 13-week cash forecast
CASES = ['closing', 'closing_best', 'closing_worst', 'closing_leave']
SCI = 'IF({in:scen}=%s,1,IF({in:scen}=%s,2,IF({in:scen}=%s,3,4)))' % (tok('scen', 'Base'), tok('scen', 'Best'), tok('scen', 'Worst'))
def BYCASE(fn): return 'IF(%s=1,%s,IF(%s=2,%s,IF(%s=3,%s,%s)))' % (SCI, fn(FC(CASES[0])), SCI, fn(FC(CASES[1])), SCI, fn(FC(CASES[2])), fn(FC(CASES[3])))
LOWS = '(%s+{in:extra_in})' % BYCASE(lambda c: 'MIN(%s)' % c)
WKLOW = BYCASE(lambda c: 'INDEX(%s,MATCH(MIN(%s),%s,0))' % (FC('week_no'), c, c))
tools.append(TOOL('forecast_tool', '13 Week Cash Forecast', 'Will cash stay above the floor for 13 weeks',
    'Cash now plus your last 13 weeks of tuition, government payments due, payroll, bills, tax and the extra draw, tested as Base, Best, Worst and families leaving (set in Start).', [
    IL('scen', 'Case', 'scen', 'Base'), I('extra_in', 'Extra cash you collect, from week 1', 0, 'money')], [
    O('Cash now', 'money', CASH_NOW), O('Cash floor', 'money', CASHFLOOR), O('Lowest closing cash, base forecast', 'money', LOWB), O('Weekly tuition in, base', 'money', 'SUM(%s)/13' % FC('tuition_in')),
    O('Tuition per family a week', 'money', PERFAM_), O('Families that leave in the leave case', 'int', '{set:leave_families}'), O('Lowest closing cash, your case', 'money', LOWS),
    O('Week number of the lowest', 'int', WKLOW), O('Week of the lowest starts on', 'date', 'INDEX(%s,%s)' % (FC('week_start'), WKLOW)),
    O('Cash above the floor at the lowest week', 'money', '%s-%s' % (LOWS, CASHFLOOR)),
    O('Weeks below the floor, your case', 'int', BYCASE(lambda c: 'COUNTIFS(%s,"<"&(%s-{in:extra_in}))' % (c, CASHFLOOR))),
    O('Closing cash in week 13, your case', 'money', '%s+{in:extra_in}' % BYCASE(lambda c: 'INDEX(%s,13)' % c)),
    O('Verdict', 'text', F3(LOWS))],
    GR('What if', ('Worst case', {'scen': GL('scen', 'Worst')}), ('Best case', {'scen': GL('scen', 'Best')}), ('Families leave', {'scen': GL('scen', 'Families leave')}),
       ('Families leave and you collect 3,000', {'scen': GL('scen', 'Families leave'), 'extra_in': 3000}), ('Base and collect 3,000', {'extra_in': 3000}))))

# 5 payment plan builder
BAL5 = AGL('balance'); OVL5 = AGL('over_limit')
FIRST5 = 'ROUND(%s*{in:down_pct},2)' % BAL5
INST5 = 'ROUND((%s-%s)/{in:instalments},2)' % (BAL5, FIRST5)
CNT5 = 'MIN({in:instalments},MAX(0,INT((91-{in:start_in})/{in:gap_days})))'
tools.append(TOOL('plan_tool', 'Payment Plan Builder', 'Should this family get a plan, and what it does to cash',
    'Type the family, a first payment, the number of instalments and the days between them: the instalment, the last date, how much arrives inside 13 weeks and what is left over your days limit.', [
    ROWIN(), I('down_pct', 'First payment, share of the balance', 0.25, 'pct'), I('instalments', 'Number of instalments after the first payment', 6), I('gap_days', 'Days between instalments', 30),
    I('start_in', 'Days until the first payment', 7), I('min_down', 'First payment you ask for at least, share of the balance', 0.20, 'pct')], [
    O('Family', 'text', 'IFERROR(%s&"","")' % FAMN), O('Balance', 'money', BAL5), O('First payment', 'money', FIRST5), O('First payment you ask for at least', 'money', 'ROUND(%s*{in:min_down},2)' % BAL5), O('Instalment', 'money', INST5),
    O('First payment date', 'date', '{today}+{in:start_in}'), O('Last instalment date', 'date', '{today}+{in:start_in}+{in:gap_days}*{in:instalments}'), O('Plan length in days', 'int', '{in:start_in}+{in:gap_days}*{in:instalments}'),
    O('Instalments that arrive inside 13 weeks', 'int', '%s+IF({in:start_in}<=91,1,0)' % CNT5), O('Money in from the plan inside 13 weeks', 'money', 'IF({in:start_in}<=91,%s,0)+%s*%s' % (FIRST5, CNT5, INST5)),
    O('Share of the balance in inside 13 weeks', 'pct', 'IFERROR((IF({in:start_in}<=91,%s,0)+%s*%s)/%s,0)' % (FIRST5, CNT5, INST5, BAL5)),
    O('Lowest forecast cash with the first payment', 'money', '%s+IF({in:start_in}<=91,%s,0)' % (LOWB, FIRST5)),
    O('Over your days limit before the plan', 'money', OVL5), O('Over your days limit after the first payment', 'money', 'MAX(0,%s-%s)' % (OVL5, FIRST5)),
    O('Verdict', 'text', 'IF({in:down_pct}>={in:min_down},%s,%s)' % (V('Offer the plan'), V('Require a larger first payment')))],
    GR('What if', ('Ten percent first payment', {'down_pct': 0.10}), ('Forty percent first payment', {'down_pct': 0.40}), ('Three instalments', {'instalments': 3}), ('Twelve instalments', {'instalments': 12}),
       ('Weekly instalments', {'gap_days': 7, 'instalments': 8}), ('Second family', {'row': 2}))))

# 6 reminder ladder
EFF6 = '({in:days}+7*{in:broken})'
tools.append(TOOL('ladder_tool', 'Reminder Ladder', 'Which step of the reminder ladder is next for this invoice',
    'Type the days overdue and the promises broken: the step (friendly reminder, call, payment plan, pause care), the date of the next step and how many families stand on each step today.', [
    I('days', 'Days overdue', ST['overdue_days']), I('broken', 'Promises broken', 2), I('balance', 'Balance', ST['overdue_balance'], 'money')], [
    O('Days counted, a broken promise adds 7', 'int', EFF6),
    O('Verdict: step now', 'text', 'IF({in:days}<=0,%s,IF(%s<{set:call_day},%s,IF(%s<{set:plan_day},%s,IF(%s<{set:pause_day},%s,%s))))' % (V('Not due yet'), EFF6, V('Friendly reminder'), EFF6, V('Call today'), EFF6, V('Offer a payment plan'), V('Pause care after notice'))),
    O('Days to the next step', 'int', 'IF(%s<{set:call_day},{set:call_day}-%s,IF(%s<{set:plan_day},{set:plan_day}-%s,IF(%s<{set:pause_day},{set:pause_day}-%s,0)))' % ((EFF6,) * 6)),
    O('Date of the next step', 'date', '{today}+IF(%s<{set:call_day},{set:call_day}-%s,IF(%s<{set:plan_day},{set:plan_day}-%s,IF(%s<{set:pause_day},{set:pause_day}-%s,0)))' % ((EFF6,) * 6)),
    O('Give notice to pause care on', 'date', '{today}+MAX(0,{set:pause_day}-%s)' % EFF6), O('Balance at stake', 'money', '{in:balance}'),
    O('Invoices on friendly reminder today', 'int', 'COUNTIFS(%s,%s)' % (R('reminder', 'step'), V('Friendly reminder'))), O('Invoices on call today', 'int', 'COUNTIFS(%s,%s)' % (R('reminder', 'step'), V('Call today'))),
    O('Invoices on payment plan', 'int', 'COUNTIFS(%s,%s)' % (R('reminder', 'step'), V('Offer a payment plan'))), O('Invoices on pause care', 'int', 'COUNTIFS(%s,%s)' % (R('reminder', 'step'), V('Pause care after notice')))],
    GR('What if', ('Three days late', {'days': 3, 'broken': 0}), ('Ten days late', {'days': 10, 'broken': 0}), ('Twenty-five days late', {'days': 25, 'broken': 0}), ('Forty days late', {'days': 40, 'broken': 0}), ('Twenty-five days, two broken promises', {'days': 25, 'broken': 2}))))

# 7 promise keeper
def PC(fam, *more): return 'COUNTIFS(%s,%s%s)' % (R('promises', 'family'), fam, ''.join(',%s,%s' % (R('promises', a), b) for a, b in more))
SHR = lambda m: 'IFERROR(COUNTIFS(%s,%s,%s,%s)/COUNTIFS(%s,%s,%s,1),0)' % (R('promises', 'method'), tok('pmethod', m), R('promises', 'outcome'), KEPT, R('promises', 'method'), tok('pmethod', m), R('promises', 'settled'))
FSH = 'IFERROR(%s/(%s+%s),0)' % (PC(FAMN, ('outcome', KEPT)), PC(FAMN, ('outcome', KEPT)), PC(FAMN, ('outcome', BROKEN)))
tools.append(TOOL('promise_tool', 'Promise Keeper', 'Can you trust this family to keep a payment promise',
    'Type a family: promises kept, broken and open, the kept share against the center share and against your target, and which way of promising (phone, e-mail, message) is kept most.', [
    ROWIN(), I('target', 'Share of promises you expect to be kept', 0.85, 'pct')], [
    O('Family', 'text', 'IFERROR(%s&"","")' % FAMN), O('Promises of this family', 'int', PC(FAMN)), O('Kept', 'int', PC(FAMN, ('outcome', KEPT))), O('Broken', 'int', PC(FAMN, ('outcome', BROKEN))), O('Open', 'int', PC(FAMN, ('outcome', PENDING))),
    O('Open promised amount', 'money', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('promises', 'promised_amount'), R('promises', 'family'), FAMN, R('promises', 'outcome'), PENDING)),
    O('Kept share, this family', 'pct', FSH), O('Kept share, all families', 'pct', 'IFERROR(%s/%s,0)' % (SM('promises', 'kept_n'), SM('promises', 'settled'))),
    O('Kept share when promised by phone', 'pct', SHR('Phone')), O('Kept share when promised by e-mail', 'pct', SHR('Email')), O('Kept share when promised by message', 'pct', SHR('Message')),
    O('Your target', 'pct', '{in:target}'), O('Verdict', 'text', 'IF(%s>={in:target},%s,%s)' % (FSH, V('Trust the promise'), V('Ask for autopay')))],
    GR('What if', ('Second family', {'row': 2}), ('Third family', {'row': 3}), ('Fourth family', {'row': 4}), ('Target of 60 percent', {'target': 0.60}))))

# 8 late payer risk ranking
RK = lambda n: 'LARGE(%s,%s)' % (R('families', 'risk_key'), n)
RKF = lambda n: 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (R('families', 'family'), n, R('families', 'risk_key'))
def RKC(c, n): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('families', c), RK(n), R('families', 'risk_key'))
tools.append(TOOL('risk_tool', 'Late Payer Risk Ranking', 'Which three families to contact before they fall behind',
    'Scores every family: 10 points a step down the habit scale, 3 per day paid late on average, 2 per 100 of open balance and 10 if late prone. Pick a rank to see the score parts.', [
    I('rank', 'Rank to look at', 1)], [
    O('First to contact', 'text', RKF(RK('1'))), O('Second to contact', 'text', RKF(RK('2'))), O('Third to contact', 'text', RKF(RK('3'))),
    O('Open balance of the three', 'money', '%s+%s+%s' % (RKC('open_balance', '1'), RKC('open_balance', '2'), RKC('open_balance', '3'))),
    O('Family at this rank', 'text', RKF(RK('{in:rank}'))), O('Score', 'num', 'IFERROR(ROUND(%s,1),0)' % RK('{in:rank}')), O('Days late on average', 'num', RKC('avg_days_late', '{in:rank}')),
    O('Open balance', 'money', RKC('open_balance', '{in:rank}')), O('Families scored as active', 'int', SM('families', 'active')),
    O('Families on autopay and active', 'int', 'COUNTIFS(%s,%s,%s,1)' % (R('families', 'autopay'), YES, R('families', 'active'))), O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (RK('1'), V('Contact these three first'), V('Settled')))],
    GR('What if', ('Second family', {'rank': 2}), ('Third family', {'rank': 3}), ('Fifth family', {'rank': 5}), ('Tenth family', {'rank': 10}))))

# 9 write-off decision
BAL9 = AGL('balance')
COST9 = '({in:minutes}*{in:months}/60*{set:hour_value})'
tools.append(TOOL('writeoff_tool', 'Write-off Decision', 'Keep chasing, agree a plan or write the balance off',
    'Type the family, your honest chance of being paid, the minutes you spend each month and the months you would keep chasing: expected recovery less the cost of chasing gives the decision.', [
    ROWIN(), I('chance', 'Chance of being paid', 0.8, 'pct'), I('minutes', 'Minutes of chasing a month', 60), I('months', 'Months you would keep chasing', 3), I('plan_below', 'Below this chance offer a plan', 0.6, 'pct')], [
    O('Family', 'text', 'IFERROR(%s&"","")' % FAMN), O('Balance', 'money', BAL9), O('Oldest invoice, days overdue', 'int', AGL('oldest_days')), O('Expected recovery', 'money', '%s*{in:chance}' % BAL9), O('Cost of chasing', 'money', COST9),
    O('Net expected', 'money', '%s*{in:chance}-%s' % (BAL9, COST9)), O('Write-off amount', 'money', 'IF(%s*{in:chance}-%s<=0,%s,0)' % (BAL9, COST9, BAL9)),
    O('Expected recovery per hour of chasing', 'money', 'IFERROR(%s*{in:chance}/({in:minutes}*{in:months}/60),0)' % BAL9),
    O('Verdict', 'text', 'IF(%s*{in:chance}-%s<=0,%s,IF({in:chance}>={in:plan_below},%s,%s))' % (BAL9, COST9, V('Write off'), V('Keep chasing'), V('Agree a plan')))],
    GR('What if', ('Chance of 45 percent', {'chance': 0.45}), ('Chance of 2 percent', {'chance': 0.02}), ('Tenth family, chance 3 percent', {'row': 10, 'chance': 0.03}), ('Ten hours of chasing a month', {'minutes': 600}),
       ('Second family, chance 70 percent', {'row': 2, 'chance': 0.7}))))

# 10 cash floor warning
LOWWK = 'MATCH(%s,%s,0)' % (LOWB, FC('closing'))
LOWST = '(%s-INDEX(%s,%s)*{in:stress})' % (LOWB, FC('cum_tuition'), LOWWK)
BILLS10 = 'INDEX(%s,%s)' % (FC('rent_bills_out'), LOWWK)
GAP10 = 'MAX(0,%s-%s)' % (CASHFLOOR, LOWST)
CHA10 = '(%s+%s+%s)*{in:chase_share}' % (SM('aging', 'd31_60'), SM('aging', 'd61_90'), SM('aging', 'd90_plus'))
tools.append(TOOL('floor_tool', 'Cash Floor Warning', 'How close cash comes to the floor and what closes it',
    'Takes the lowest week of the forecast, lets you cut tuition by a stress share, and tests the two fixes against your cash floor: chase the older balances or delay part of that week\'s bills.', [
    I('stress', 'Stress: tuition below the forecast', 0.10, 'pct'), I('chase_share', 'Share of balances over 30 days you can collect in time', 0.5, 'pct'), I('delay_share', 'Share of that week\'s bills you can delay', 0.5, 'pct')], [
    O('Cash floor', 'money', CASHFLOOR), O('Lowest closing cash, base forecast', 'money', LOWB), O('Week of the lowest starts on', 'date', 'INDEX(%s,%s)' % (FC('week_start'), LOWWK)),
    O('Lowest closing cash under the stress', 'money', LOWST), O('Above the floor under the stress', 'money', '%s-%s' % (LOWST, CASHFLOOR)),
    O('Gap to the floor', 'money', GAP10), O('Bills falling in that week', 'money', BILLS10), O('Bills you could delay', 'money', '%s*{in:delay_share}' % BILLS10), O('Older balances you could collect', 'money', CHA10),
    O('Amount to chase', 'money', 'IF(AND(%s>0,%s>%s*{in:delay_share}),%s,0)' % (GAP10, GAP10, BILLS10, GAP10)),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s<=%s*{in:delay_share},%s,%s))' % (GAP10, V('Safe'), GAP10, BILLS10, V('Delay a bill'), V('Chase the balance')))],
    GR('What if', ('No stress', {'stress': 0.0}), ('Stress of 5 percent', {'stress': 0.05}), ('Stress of 15 percent', {'stress': 0.15}), ('Collect only a quarter', {'chase_share': 0.25}),
       ('Delay all bills of the week', {'delay_share': 1.0}), ('Collect everything over 30 days', {'chase_share': 1.0}))))

# 11 bill calendar
BIL = lambda: 'SUMIFS(%s,%s,%s,%s,"<="&({today}+{in:window}))' % (R('bills', 'amount'), R('bills', 'status'), UPC, R('bills', 'due_date'))
INC11 = '(SUMIFS(%s,%s,"<="&({today}+{in:window}))+SUMIFS(%s,%s,"<="&({today}+{in:window})))' % (FC('tuition_in'), FC('week_start'), FC('government_in'), FC('week_start'))
OUT11 = 'SUMIFS(%s,%s,"<="&({today}+{in:window}))' % (FC('other_out'), FC('week_start'))
NB = lambda k, c: 'IFERROR(INDEX(%s,MATCH(SMALL(%s,%d),%s,0)),0)' % (R('bills', c), R('bills', 'open_key'), k, R('bills', 'open_key'))
tools.append(TOOL('billcal_tool', 'Bill Calendar', 'Can you pay every bill due soon, and in what order',
    'Adds the bills due in the window and the cash expected in, shows what is left against the floor and lists the next three bills by due date.', [
    I('window', 'Days ahead', 30)], [
    O('Cash now', 'money', CASH_NOW), O('Bills due in the window', 'money', BIL()), O('Number of bills', 'int', 'COUNTIFS(%s,%s,%s,"<="&({today}+{in:window}))' % (R('bills', 'status'), UPC, R('bills', 'due_date'))),
    O('Tuition and government in, weeks starting in the window', 'money', INC11), O('Routine costs in the window', 'money', OUT11), O('Cash left after the bills', 'money', '%s+%s-%s-%s' % (CASH_NOW, INC11, BIL(), OUT11)),
    O('Next bill', 'text', 'IFERROR(INDEX(%s,MATCH(SMALL(%s,1),%s,0)),"")' % (R('bills', 'category'), R('bills', 'open_key'), R('bills', 'open_key'))), O('Its due date', 'date', NB(1, 'due_date')), O('Its amount', 'money', NB(1, 'amount')),
    O('Second bill amount', 'money', NB(2, 'amount')), O('Third bill amount', 'money', NB(3, 'amount')), O('Largest bill in the window', 'money', 'SUMPRODUCT(MAX((%s=%s)*(%s<={today}+{in:window})*%s))' % (R('bills', 'status'), UPC, R('bills', 'due_date'), R('bills', 'amount'))),
    O('Verdict', 'text', 'IF(%s+%s-%s-%s>={set:cash_floor},%s,%s)' % (CASH_NOW, INC11, BIL(), OUT11, V('Pay all'), V('Pay in this order')))],
    GR('What if', ('Seven days ahead', {'window': 7}), ('Fourteen days ahead', {'window': 14}), ('Sixty days ahead', {'window': 60}), ('Ninety days ahead', {'window': 90}))))

# 12 government short-pay chaser
GK = lambda n, c: 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),0)' % (R('gov', c), R('gov', 'chase_key'), n, R('gov', 'chase_key'))
tools.append(TOOL('govchase_tool', 'Government Short Pay Chaser', 'Which government payment is short or late and who do you ask',
    'Lists the items still to chase, the one with the biggest gap, the days since it was short-paid, the family share if the payer does not pay and the payments due in the next days.', [
    I('days_ahead', 'Days ahead for payments due', 14)], [
    O('Items to chase', 'int', 'COUNT(%s)' % R('gov', 'chase_key')), O('Largest item: family', 'text', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,1),%s,0)),"")' % (R('gov', 'family'), R('gov', 'chase_key'), R('gov', 'chase_key'))),
    O('Largest item: month', 'date', GK(1, 'month')), O('Expected', 'money', GK(1, 'expected')), O('Received', 'money', GK(1, 'received')), O('Gap', 'money', GK(1, 'gap')), O('Days since the short payment', 'int', GK(1, 'days_since')),
    O('Family share still owed if the payer does not pay', 'money', GK(1, 'gap')), O('Days left before you bill the family', 'int', 'MAX(0,{set:gov_wait_days}-%s)' % GK(1, 'days_since')),
    O('Payments expected in the next days', 'money', 'SUMIFS(%s,%s,%s,%s,">="&{today},%s,"<="&({today}+{in:days_ahead}))' % (R('gov', 'expected'), R('gov', 'status'), EXPECTED, R('gov', 'due_on'), R('gov', 'due_on'))),
    O('Items expected in the next days', 'int', 'COUNTIFS(%s,%s,%s,">="&{today},%s,"<="&({today}+{in:days_ahead}))' % (R('gov', 'status'), EXPECTED, R('gov', 'due_on'), R('gov', 'due_on'))),
    O('Verdict', 'text', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,1),%s,0)),%s)' % (R('gov', 'step'), R('gov', 'chase_key'), R('gov', 'chase_key'), V('Matched')))],
    GR('What if', ('Seven days ahead', {'days_ahead': 7}), ('Thirty days ahead', {'days_ahead': 30}), ('Sixty days ahead', {'days_ahead': 60}))))

# 13 deposit refund planner
REF13 = '({in:leavers}*IFERROR(%s/COUNTIFS(%s,%s),0))' % (SM('deposits', 'held'), R('deposits', 'status'), HELD)
LOW13 = '(%s-%s)' % (LOWB, REF13)
tools.append(TOOL('depref_tool', 'Deposit Refund Planner', 'Can cash cover the deposit refunds when families leave',
    'A deposit is a payment held to keep a place, applied to the last invoice or refunded. Type the families leaving and the notice: refunds due, the date, and the lowest forecast cash after paying them.', [
    I('leavers', 'Children leaving', 3), I('notice_days', 'Days of notice', 30)], [
    O('Deposits held now', 'money', SM('deposits', 'held')), O('Deposits held, number', 'int', 'COUNTIFS(%s,%s)' % (R('deposits', 'status'), HELD)), O('Average deposit held', 'money', 'IFERROR(%s/COUNTIFS(%s,%s),0)' % (SM('deposits', 'held'), R('deposits', 'status'), HELD)),
    O('Refunds if they leave', 'money', REF13), O('Refund date', 'date', '{today}+{in:notice_days}+14'), O('Refunds paid in the last 12 months', 'money', 'SUMIFS(%s,%s,">"&EDATE(%s,-12))' % (R('cash', 'deposit_refunds'), R('cash', 'month'), MS)),
    O('Lowest forecast cash if the refunds were paid now', 'money', LOW13), O('Above the floor after the refunds', 'money', '%s-%s' % (LOW13, CASHFLOOR)), O('Amount to plan for', 'money', 'MAX(0,%s-%s)' % (CASHFLOOR, LOW13)),
    O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (LOW13, CASHFLOOR, V('Refunds are covered'), V('Plan the shortfall')))],
    GR('What if', ('Six children leave', {'leavers': 6}), ('Ten children leave', {'leavers': 10}), ('Fifteen children leave, 14 days notice', {'leavers': 15, 'notice_days': 14}), ('One child leaves', {'leavers': 1}))))

# 14 tax set-aside check
Q = lambda c: 'SUMIFS(%s,%s,">="&{in:q_start},%s,"<"&EDATE({in:q_start},3))' % (R('tax', c), R('tax', 'month'), R('tax', 'month'))
REQ14 = 'ROUND(MAX(0,%s)*{in:pct},2)' % Q('profit')
q0 = month_start(0); qm = ((q0.month - 1) // 3) * 3 + 1
LASTQ = add_months(dt.date(q0.year, qm, 1), -3)
tools.append(TOOL('tax_tool', 'Tax Set Aside Check', 'Have you set aside enough of the profit for income tax',
    'Pick a quarter: revenue, costs, profit, what your share requires and what is set aside, with the date it falls due. Income tax set-aside is an estimate: confirm with your adviser.', [
    I('q_start', 'First day of the quarter', iso(LASTQ), 'date'), I('pct', 'Share of profit you set aside', TAX_SET_ASIDE_PCT, 'pct')], [
    O('Revenue', 'money', Q('revenue')), O('Costs', 'money', Q('costs')), O('Profit', 'money', Q('profit')), O('Profit margin', 'pct', 'IFERROR(%s/%s,0)' % (Q('profit'), Q('revenue'))),
    O('Your share requires', 'money', REQ14), O('Set aside', 'money', Q('set_aside')), O('Gap', 'money', '%s-%s' % (REQ14, Q('set_aside'))), O('Set aside of what is required', 'pct', 'IFERROR(%s/%s,0)' % (Q('set_aside'), REQ14)),
    O('Due date', 'date', 'SUMPRODUCT(MAX((%s>={in:q_start})*(%s<EDATE({in:q_start},3))*%s))' % (R('tax', 'month'), R('tax', 'month'), R('tax', 'due_date'))),
    O('Set aside this year', 'money', 'SUMIFS(%s,%s,">="&DATE(YEAR({today}),1,1))' % (R('tax', 'set_aside'), R('tax', 'month'))),
    O('Verdict', 'text', 'IF(%s-%s>1,%s,%s)' % (REQ14, Q('set_aside'), V('Short of your share'), V('Set aside is on track')))],
    GR('What if', ('Share of 30 percent', {'pct': 0.30}), ('Share of 20 percent', {'pct': 0.20}), ('The quarter before', {'q_start': '=EDATE(DATE(%d,%d,1),-3)' % (LASTQ.year, LASTQ.month)}), ('The current quarter', {'q_start': '=EDATE(DATE(%d,%d,1),3)' % (LASTQ.year, LASTQ.month)}))))

# 15 payment method mix
PM15 = lambda m=None: 'SUMIFS(%s,%s,">"&({today}-{in:window}),%s,%s%s)' % (R('payments', 'amount'), R('payments', 'date'), R('payments', 'kind'), OV(DEPOSIT), (',%s,%s' % (R('payments', 'method'), m)) if m else '')
TOT15 = PM15()
ACT = SM('families', 'active'); APF = 'COUNTIFS(%s,%s,%s,1)' % (R('families', 'autopay'), YES, R('families', 'active'))
MOVE15 = 'MAX(0,ROUNDUP({in:target}*%s-%s,0))' % (ACT, APF)
tools.append(TOOL('mix_tool', 'Payment Method Mix', 'How do families pay and how many should move to autopay',
    'Shares of tuition paid by autopay card, autopay bank, bank transfer and cash over the window, the handling risk of cash and how many active families would have to move to autopay to reach your target.', [
    I('window', 'Days to look back', 90), I('target', 'Share of families you want on autopay', 0.65, 'pct'), I('cash_limit', 'Cash share you accept', 0.02, 'pct')], [
    O('Paid in the window', 'money', TOT15), O('Autopay card share', 'pct', 'IFERROR(%s/%s,0)' % (PM15(ACARD), TOT15)), O('Autopay bank share', 'pct', 'IFERROR(%s/%s,0)' % (PM15(ABANK), TOT15)),
    O('Bank transfer share', 'pct', 'IFERROR(%s/%s,0)' % (PM15(XFER), TOT15)), O('Cash share', 'pct', 'IFERROR(%s/%s,0)' % (PM15(CASH), TOT15)), O('Cash received', 'money', PM15(CASH)),
    O('Active families', 'int', ACT), O('Active families on autopay', 'int', APF), O('Autopay share of families', 'pct', 'IFERROR(%s/%s,0)' % (APF, ACT)), O('Families to move to autopay', 'int', MOVE15),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (MOVE15, V('Move families to autopay'), V('Mix is on target')))],
    GR('What if', ('Target 50 percent', {'target': 0.50}), ('Target 80 percent', {'target': 0.80}), ('Look back 30 days', {'window': 30}), ('Look back one year', {'window': 365}))))

# 16 chasing time cost
REC16 = 'SUMIFS(%s,%s,">"&({today}-30),%s,1)' % (R('invoices', 'paid_amount'), R('invoices', 'paid_on'), R('invoices', 'is_late'))
COST16 = '({in:hours}*{in:weeks}*{set:hour_value})'
tools.append(TOOL('chase_tool', 'Chasing Time Cost', 'Is the time you spend chasing late payments worth it',
    'Type the hours a week you chase and the weeks: the cost of that time against what late invoices brought in during the last 30 days, and what it would take to switch those families to autopay.', [
    I('hours', 'Hours a week spent chasing', 3.5, 'num'), I('weeks', 'Weeks', 4), I('pays_ratio', 'Money recovered you want per unit of cost', 10, 'num')], [
    O('Cost of the chasing time', 'money', COST16), O('Paid on late invoices, last 30 days', 'money', REC16), O('Recovered for each unit of cost', 'num', 'IFERROR(%s/%s,0)' % (REC16, COST16)),
    O('Recovered for each hour of chasing', 'money', 'IFERROR(%s/({in:hours}*{in:weeks}),0)' % REC16), O('Late invoices of manual payers, 12 months', 'int', LM), O('Hours spent chasing one late invoice', 'num', 'IFERROR({in:hours}*{in:weeks}/COUNTIFS(%s,1,%s,">"&({today}-30)),0)' % (R('invoices', 'is_late'), R('invoices', 'due_date'))),
    O('Open balance of manual payers overdue', 'money', 'SUMIFS(%s,%s,0,%s,">0")' % (R('invoices', 'open_balance'), R('invoices', 'autopay'), R('invoices', 'days_overdue'))),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s,0)>={in:pays_ratio},%s,%s)' % (REC16, COST16, V('Chasing pays'), V('Switch to autopay')))],
    GR('What if', ('Seven hours a week', {'hours': 7}), ('One hour a week', {'hours': 1}), ('Eight weeks', {'weeks': 8}), ('Expect five times the cost', {'pays_ratio': 5}))))

# 17 payroll date cash check
PAYD = 'SUMPRODUCT(MIN((%s=%s)*(%s=%s)*%s+99999*(((%s<>%s)+(%s<>%s))>0)))' % (R('bills', 'category'), PAYROLL, R('bills', 'status'), UPC, R('bills', 'due_date'), R('bills', 'category'), PAYROLL, R('bills', 'status'), UPC)
WKI = 'MAX(1,MIN(13,COUNTIFS(%s,"<="&(%s+{in:move_days}))))' % (FC('week_start'), PAYD)
WI = lambda c: 'INDEX(%s,%s)' % (FC(c), WKI)
BEFORE17 = '(%s+%s+%s-%s-%s-%s)' % (WI('opening'), WI('tuition_in'), WI('government_in'), WI('rent_bills_out'), WI('other_out'), WI('draw_tax_out'))
PAYAMT = 'SUMIFS(%s,%s,%s,%s,%s)' % (R('bills', 'amount'), R('bills', 'category'), PAYROLL, R('bills', 'due_date'), PAYD)
tools.append(TOOL('payroll_tool', 'Payroll Date Cash Check', 'Does cash cover payroll on the pay date',
    'Takes the next payroll bill, the cash expected in its week and the bills in the same week, and shows cash after payroll against the floor; move the pay date by days to test it.', [
    I('move_days', 'Move the pay date by days', 0)], [
    O('Next pay date', 'date', PAYD), O('Pay date tested', 'date', '%s+{in:move_days}' % PAYD), O('Payroll', 'money', PAYAMT), O('Cash at the start of that week', 'money', WI('opening')),
    O('Tuition and government payments in that week', 'money', '%s+%s' % (WI('tuition_in'), WI('government_in'))), O('Rent, bills and routine costs in that week', 'money', '%s+%s+%s' % (WI('rent_bills_out'), WI('other_out'), WI('draw_tax_out'))),
    O('Cash before payroll', 'money', BEFORE17), O('Cash after payroll', 'money', '%s-%s' % (BEFORE17, PAYAMT)), O('Above the floor after payroll', 'money', '%s-%s-%s' % (BEFORE17, PAYAMT, CASHFLOOR)),
    O('Payroll as a share of cash before it', 'pct', 'IFERROR(%s/%s,0)' % (PAYAMT, BEFORE17)),
    O('Verdict', 'text', 'IF(%s-%s>=%s,%s,%s)' % (BEFORE17, PAYAMT, CASHFLOOR, V('Cash covers payroll'), V('Move the pay date')))],
    GR('What if', ('Pay three days later', {'move_days': 3}), ('Pay a week later', {'move_days': 7}), ('Pay a week earlier', {'move_days': -7}), ('Pay two weeks later', {'move_days': 14}))))

# 18 collection rate by month
CMI = lambda c: 'IFERROR(INDEX(%s,MATCH({in:month},%s,0)),0)' % (R('collect', c), R('collect', 'month'))
tools.append(TOOL('collect_tool', 'Collection Rate by Month', 'Is this month collecting better or worse than your own usual',
    'Pick a month: money due and collected, the collection rate against your last 3 months and your 12-month rate, with a band you set.', [
    I('month', 'First day of the month', iso(month_start(1)), 'date'), I('band', 'Band around your average', 0.02, 'pct'), I('target', 'Collection rate you want', 0.97, 'pct')], [
    O('Due', 'money', CMI('due')), O('Collected', 'money', CMI('collected')), O('Collection rate', 'pct', CMI('rate')), O('Rate of the 3 months before', 'pct', CMI('avg3')),
    O('Rate over 12 months', 'pct', 'IFERROR(%s/%s,0)' % (SM('collect', 'collected'), SM('collect', 'due'))), O('Your target', 'pct', '{in:target}'),
    O('Against your 3-month rate', 'pct', '%s-%s' % (CMI('rate'), CMI('avg3'))), O('Lowest monthly rate, last 12', 'pct', 'MIN(%s)' % R('collect', 'rate')), O('Amount not collected', 'money', '%s-%s' % (CMI('due'), CMI('collected'))),
    O('Verdict', 'text', 'IF(%s>%s+{in:band},%s,IF(%s<%s-{in:band},%s,%s))' % (CMI('rate'), CMI('avg3'), V('Above your average'), CMI('rate'), CMI('avg3'), V('Below your average'), V('Near your average')))],
    GR('What if', ('Two months back', {'month': '=EDATE(%s,-2)' % MS}), ('Four months back', {'month': '=EDATE(%s,-4)' % MS}), ('Eight months back', {'month': '=EDATE(%s,-8)' % MS}), ('Wider band', {'band': 0.05}))))

assert len(tools) == 18, len(tools)
