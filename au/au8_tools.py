"""Author and self-publisher suite part 8: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au8_lists import *
from au8_tables import MIN12, MS, LM, WIN, W12, SUM12, SUMN, CASHNOW, PAID, EXPD, OPEN, NOTPAID, DUE_IN, STMT_RECV, POT_NOW, AVGCOST12, SCA, NAMEROLE
import au8_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
FM = '{range:forecast.month}'
FC = '{range:forecast.closing}'
def PICK3(a, b, c, sc='{in:scenario}'): return 'CHOOSE(MATCH(%s,{range:scenarios.scenario},0),%s,%s,%s)' % (sc, a, b, c)
def CLOSE_RNG(col): return '{range:forecast.%s}' % col
tools = []

# 1 ------------------------------------------------------------ cash flow forecast
LOWS = lambda: PICK3('MIN(%s)' % CLOSE_RNG('close_base'), 'MIN(%s)' % CLOSE_RNG('close_best'), 'MIN(%s)' % CLOSE_RNG('close_worst'))
BELOW = lambda: PICK3(*['COUNTIFS(%s,"<"&{in:floor})' % CLOSE_RNG(c) for c in ('close_base', 'close_best', 'close_worst')])
LOWMONTH = lambda: PICK3(*['INDEX(%s,MATCH(MIN(%s),%s,0))' % (FM, CLOSE_RNG(c), CLOSE_RNG(c)) for c in ('close_base', 'close_best', 'close_worst')])
tools.append(TOOL('cashflow', 'Cash Flow Forecast Tool', 'Will your cash hold for the next 12 months',
    'Pick Base, Best or Worst (sales minus 20 percent) and your floor: the lowest closing cash, its month, the months below your floor and the cash at month 12.', [
    IL('scenario', 'Scenario', 'scen3', 'Base'), I('floor', 'Lowest cash you accept (your own number)', CASH_FLOOR)], [
    O('Cash today', 'money', CASHNOW), O('Cash at the start of the forecast, after known payments', 'money', 'INDEX({range:forecast.start_cash},1)'),
    O('Lowest closing cash, Base', 'money', 'MIN(%s)' % CLOSE_RNG('close_base')), O('Lowest closing cash, Best', 'money', 'MIN(%s)' % CLOSE_RNG('close_best')), O('Lowest closing cash, Worst (sales minus 20%)', 'money', 'MIN(%s)' % CLOSE_RNG('close_worst')),
    O('Sales change of the scenario', 'pct', 'INDEX({range:scenarios.sales_change},MATCH({in:scenario},{range:scenarios.scenario},0))'),
    O('Lowest closing cash, this scenario', 'money', LOWS()), O('Closing cash in month 12, this scenario', 'money', PICK3(*['INDEX(%s,12)' % CLOSE_RNG(c) for c in ('close_base', 'close_best', 'close_worst')])),
    O('Months below your floor', 'int', BELOW()), O('Month of the lowest cash', 'date', LOWMONTH()),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (BELOW(), vc('Cash holds'), vc('Low-cash month')))],
    GR('What if', ('Best scenario', {'scenario': '=' + tok('scen', 'Best')}), ('Worst scenario, sales minus 20%', {'scenario': '=' + tok('scen', 'Worst')}), ('Floor 5,000', {'floor': 5000}), ('Floor 10,000', {'floor': 10000}), ('Floor 3,000', {'floor': 3000}))))

# 2 ------------------------------------------------------------ cash for the next 30 days
DUES = 'SUMIFS({range:jobpay.amount},{range:jobpay.status},%s,{range:jobpay.date},"<="&({today}+{in:window}))' % NOTPAID
DUES1 = 'SUMIFS({range:jobpay.amount},{range:jobpay.status},%s,{range:jobpay.date},"<="&({today}+{in:first_days}))' % NOTPAID
LARGEST = 'SUMPRODUCT(MAX(({range:jobpay.status}<>%s)*({range:jobpay.date}<={today}+{in:window})*{range:jobpay.amount}))' % PAID
RECV = STMT_RECV('{in:window}')
A_ = '(%s-%s)' % (CASHNOW, DUES1)
B_ = '(%s+%s-%s)' % (CASHNOW, RECV, DUES)
tools.append(TOOL('cash30', 'Cash for the Next 30 Days', 'Can you pay what is due and keep your floor',
    'Early payments come from cash alone; later ones can wait for receipts. See both balances against your floor and one verdict: pay now, pay in parts or hold the draw.', [
    I('window', 'Days to look ahead', 30, 'int'), I('first_days', 'Days in which you count no receipts', 7, 'int'), I('draw', 'Owner draw you plan in this window', DRAW_PLAN), I('floor', 'Lowest cash you accept (your own number)', CASH_FLOOR)], [
    O('Cash today', 'money', CASHNOW), O('Payments due in the first days', 'money', DUES1), O('Cash left after them, no receipts counted', 'money', A_), O('Largest payment due in the window', 'money', LARGEST),
    O('Cash left after the largest payment', 'money', '%s-%s' % (CASHNOW, LARGEST)), O('Payments due in the whole window', 'money', DUES), O('Number of payments due in the window', 'int', 'COUNTIFS({range:jobpay.status},%s,{range:jobpay.date},"<="&({today}+{in:window}))' % NOTPAID),
    O('Receipts expected in the window', 'money', RECV), O('Balance at the end of the window', 'money', B_), O('Balance at the end of the window, after the draw', 'money', '%s-{in:draw}' % B_),
    O('Verdict', 'text', 'IF(%s>={in:floor},IF(%s-{in:draw}>={in:floor},%s,%s),IF(%s-{in:draw}>={in:floor},%s,%s))' % (A_, B_, vc('Pay now'), vc('Hold the draw'), B_, vc('Pay in parts'), vc('Hold the draw')))],
    GR('What if', ('Draw 0', {'draw': 0}), ('Draw 12,000', {'draw': 12000}), ('No receipts counted for 30 days', {'first_days': 30}), ('Look ahead 60 days', {'window': 60}), ('Floor 3,000', {'floor': 3000}))))

# 3 ------------------------------------------------------------ cash cover months
CST = '(%s*(1+{in:cost_change}))' % AVGCOST12
tools.append(TOOL('cover', 'Cash Cover Months', 'How many months of costs does your cash cover',
    'Cash today divided by your average monthly costs of the last 12 complete months, against the months you want; type a cost change to test five cost levels.', [
    I('months_target', 'Months of cover you want (your own number)', CASH_COVER_MONTHS, 'num'), I('cost_change', 'Change of your monthly costs', 0.0, 'pct'), I('thin_share', 'Share of the target that counts as thin', 0.75, 'pct')], [
    O('Cash today', 'money', CASHNOW), O('Average monthly costs, last 12 months', 'money', AVGCOST12), O('Monthly costs used', 'money', CST), O('Months of cover', 'num', 'IFERROR(%s/%s,0)' % (CASHNOW, CST)),
    O('Months of cover you want', 'num', '{in:months_target}'), O('Cash needed for your target', 'money', '{in:months_target}*%s' % CST), O('Cash above (+) or below (-) the target', 'money', '%s-{in:months_target}*%s' % (CASHNOW, CST)),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s,0)>={in:months_target},%s,IF(IFERROR(%s/%s,0)>={in:months_target}*{in:thin_share},%s,%s))' % (CASHNOW, CST, vc('Covered'), CASHNOW, CST, vc('Thin'), vc('Short')))],
    GR('What if: five cost levels', ('Costs minus 20%', {'cost_change': -0.2}), ('Costs minus 10%', {'cost_change': -0.1}), ('Costs plus 10%', {'cost_change': 0.1}), ('Costs plus 20%', {'cost_change': 0.2}), ('Costs plus 40%', {'cost_change': 0.4}),
       ('Want 2 months', {'months_target': 2}))))

# 4 ------------------------------------------------------------ receipts by pay month
RX = '{range:receipts.expected}'
GAPN = '(' + '+'.join('(INDEX(%s,%d)*(1+{in:trend_change})<INDEX({range:receipts.needed},%d))' % (RX, k, k) for k in range(1, 13)) + ')'
tools.append(TOOL('rcp_tool', 'Receipts by Pay Month Tool', 'In which month do your store payments fall short',
    'Expected royalties by pay month from the store delays against what you pay out in a usual month; type a change of the payments to test a slower or better stretch.', [
    I('month_no', 'Pay month to read (1 = next month)', 1, 'int'), I('trend_change', 'Change of the expected payments', 0.0, 'pct')], [
    O('Pay month read', 'date', 'INDEX({range:receipts.month},{in:month_no})'), O('Earned in that month (estimate)', 'money', 'INDEX({range:receipts.earned_est},{in:month_no})'),
    O('Expected in that month by store delay', 'money', 'INDEX(%s,{in:month_no})*(1+{in:trend_change})' % RX), O('Paid out in a usual month', 'money', 'INDEX({range:receipts.needed},{in:month_no})'),
    O('Lowest expected month', 'date', 'INDEX({range:receipts.month},MATCH(MIN(%s),%s,0))' % (RX, RX)), O('Lowest expected amount', 'money', 'MIN(%s)*(1+{in:trend_change})' % RX),
    O('Expected in the next 12 months', 'money', 'SUM(%s)*(1+{in:trend_change})' % RX), O('Earned in the next 12 months (estimate)', 'money', 'SUM({range:receipts.earned_est})'),
    O('Expected in the next 3 months', 'money', 'SUMIFS(%s,{range:receipts.month},"<"&EDATE(%s,4))*(1+{in:trend_change})' % (RX, MS)),
    O('Months that fall short', 'int', GAPN), O('Least spare cash in a month', 'money', MIN12(lambda k: 'INDEX(%s,%d)*(1+{in:trend_change})-INDEX({range:receipts.needed},%d)' % (RX, k, k))),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (GAPN, vc('A gap in the month'), vc('No gap')))],
    GR('What if', ('Payments 10% lower', {'trend_change': -0.1}), ('Payments 25% lower', {'trend_change': -0.25}), ('Payments 40% lower', {'trend_change': -0.4}), ('Payments 10% higher', {'trend_change': 0.1}), ('Read month 6', {'month_no': 6}))))

# 5 ------------------------------------------------------------ contractor payments due
CROSS = 'COUNTIFS({range:due.balance_after},"<"&({set:cash_floor}-{in:extra_cash}))'
FIRSTX = 'COUNTIFS({range:due.balance_after},">="&({set:cash_floor}-{in:extra_cash}))+1'
tools.append(TOOL('payq', 'Contractor Payments Due', 'In which order to pay and which payment crosses your floor',
    'Open payments to freelancers and providers by due date: the next payment, the total, the first payment that takes your cash below the floor, and what extra cash would move it.', [
    I('extra_cash', 'Extra cash you could add (a transfer or an early payment)', 0)], [
    O('Open payments', 'int', 'COUNTIFS({range:jobpay.status},%s,{range:jobpay.amount},">0")' % NOTPAID), O('Total of the open payments', 'money', 'SUMIFS({range:jobpay.amount},{range:jobpay.status},%s)' % NOTPAID), O('Due in the next 30 days', 'money', DUE_IN(30)),
    O('Next payment on', 'date', 'INDEX({range:due.due_date},1)'), O('Next payment to', 'text', 'INDEX({range:due.contractor},1)'), O('Next payment amount', 'money', 'INDEX({range:due.amount},1)'),
    O('Cash today plus the extra cash', 'money', '%s+{in:extra_cash}' % CASHNOW), O('Payments that take cash below the floor', 'int', CROSS),
    O('First payment below the floor: to', 'text', 'IF(%s=0,%s,INDEX({range:due.contractor},%s))' % (CROSS, vc('Above the floor'), FIRSTX)), O('First payment below the floor: amount', 'money', 'IF(%s=0,0,INDEX({range:due.amount},%s))' % (CROSS, FIRSTX)),
    O('First payment below the floor: days from today', 'int', 'IF(%s=0,0,INDEX({range:due.due_date},%s)-{today})' % (CROSS, FIRSTX)), O('Cash left after that payment', 'money', 'IF(%s=0,0,INDEX({range:due.balance_after},%s)+{in:extra_cash})' % (CROSS, FIRSTX)),
    O('Verdict', 'text', 'IF(COUNTIFS({range:jobpay.status},%s)=0,%s,%s)' % (NOTPAID, vc('Nothing due'), vc('Pay in this order')))],
    GR('What if', ('Add 1,000', {'extra_cash': 1000}), ('Add 2,500', {'extra_cash': 2500}), ('Add 5,000', {'extra_cash': 5000}), ('Add 10,000', {'extra_cash': 10000}))))

# 6 ------------------------------------------------------------ owner draw planner
KDRAW = '({set:owner_draw_plan}-{in:draw_now})'
DSTAR = '({set:owner_draw_plan}+%s)' % MIN12(lambda k: '(INDEX(%s,%d)-{in:floor})/%d' % (FC, k, k))
LOWD = MIN12(lambda k: 'INDEX(%s,%d)+%s*%d' % (FC, k, KDRAW, k))
BELOWD = '(' + '+'.join('(INDEX(%s,%d)+%s*%d<{in:floor})' % (FC, k, KDRAW, k) for k in range(1, 13)) + ')'
tools.append(TOOL('drawplan', 'Owner Draw Planner', 'How much can you take out and keep your floor',
    'The largest steady monthly draw that keeps cash at or above your floor in every forecast month (the scenario on Start), and the lowest cash with the draw you have in mind; five draws tested below.', [
    I('draw_now', 'Owner draw you have in mind', DRAW_PLAN), I('floor', 'Lowest cash you accept (your own number)', CASH_FLOOR)], [
    O('Draw planned on Start', 'money', '{set:owner_draw_plan}'), O('Largest steady draw that holds the floor', 'money', 'MAX(0,%s)' % DSTAR),
    O('Lowest closing cash with your draw', 'money', LOWD), O('Months below the floor with your draw', 'int', BELOWD),
    O('Extra cash needed to hold the floor', 'money', 'MAX(0,{in:floor}-%s)' % LOWD), O('Draw to cut each month', 'money', 'MAX(0,{in:draw_now}-MAX(0,%s))' % DSTAR),
    O('Verdict', 'text', 'IF({in:draw_now}<=%s,%s,%s)' % (DSTAR, vc('Draw fits'), vc('Reduce the draw')))],
    GR('What if: five draws', ('Draw 0', {'draw_now': 0}), ('Draw 1,000', {'draw_now': 1000}), ('Draw 2,000', {'draw_now': 2000}), ('Draw 3,000', {'draw_now': 3000}), ('Draw 4,500', {'draw_now': 4500}))))

# 7 ------------------------------------------------------------ tax set-aside
PROF12 = SUM12('pnl', 'profit'); MPAY = 'MAX(0,({set:next_tax_on}-{today})/30.4)'
PROJ = '(%s+%s*%s/12*{in:pct})' % (POT_NOW, MPAY, PROF12)
tools.append(TOOL('taxsa', 'Tax Set-aside Check', 'Is the tax pot big enough for the next payment',
    'Type a set-aside percent to test (confirm it with your tax adviser): the set-aside it implies, what you set aside, the pot and the shortfall against the next payment.', [
    I('pct', 'Set-aside percent of profit (confirm with your tax adviser)', TAX_SET_ASIDE_PCT, 'pct')], [
    O('Profit, last 12 months', 'money', PROF12), O('Set-aside at this percent, 12 months', 'money', '%s*{in:pct}' % PROF12), O('Really set aside, last 12 months', 'money', SUM12('taxmonth', 'set_aside')),
    O('Difference (really set aside minus this percent)', 'money', '%s-%s*{in:pct}' % (SUM12('taxmonth', 'set_aside'), PROF12)), O('Tax pot now', 'money', POT_NOW), O('Next payment', 'money', '{set:next_tax_amount}'),
    O('Months until the payment', 'num', MPAY), O('Monthly set-aside at this percent', 'money', '%s/12*{in:pct}' % PROF12), O('Pot on the payment day', 'money', PROJ),
    O('Short by', 'money', 'MAX(0,{set:next_tax_amount}-%s)' % PROJ), O('Verdict', 'text', 'IF(%s>={set:next_tax_amount},%s,%s)' % (PROJ, vt('Pot covers the payment'), vt('Pot is short')))],
    GR('What if', ('20 percent', {'pct': 0.20}), ('30 percent', {'pct': 0.30}), ('35 percent', {'pct': 0.35}), ('40 percent', {'pct': 0.40}), ('15 percent', {'pct': 0.15}))))

# 8 ------------------------------------------------------------ tax payment planner
FILL = 'MAX(0,{in:payment}-%s-{in:extra_deposit})' % POT_NOW
MLEFT = 'MAX(0.5,({set:next_tax_on}-{today})/30.4)'
MPROF = '(%s/12)' % PROF12
tools.append(TOOL('taxplan', 'Tax Payment Planner', 'What percent fills the pot by the payment day',
    'Type the payment and a lump sum you could add: the amount still to fill, the percent of profit you need and the months to fill at your own percent.', [
    I('payment', 'Amount of the next tax payment', 6300), I('extra_deposit', 'Lump sum you could add to the pot now', 0)], [
    O('Next payment on', 'date', '{set:next_tax_on}'), O('Days to the payment', 'int', '{set:next_tax_on}-{today}'), O('Tax pot now', 'money', POT_NOW), O('Amount still to fill', 'money', FILL),
    O('Months left (at least half a month)', 'num', MLEFT), O('Average monthly profit, last 12 months', 'money', MPROF), O('Monthly set-aside you need', 'money', '%s/%s' % (FILL, MLEFT)),
    O('Percent of profit you need', 'pct', 'IFERROR(%s/%s/%s,0)' % (FILL, MLEFT, MPROF)), O('Your percent on Start', 'pct', '{set:tax_set_aside_pct}'),
    O('Months to fill at your percent', 'num', 'IFERROR(%s/(%s*{set:tax_set_aside_pct}),0)' % (FILL, MPROF)),
    O('Verdict', 'text', 'IF(IFERROR(%s/(%s*{set:tax_set_aside_pct}),0)<=%s,%s,%s)' % (FILL, MPROF, MLEFT, vt('On track'), vt('Raise the percent')))],
    GR('What if', ('Payment 5,000', {'payment': 5000}), ('Payment 8,000', {'payment': 8000}), ('Payment 10,000', {'payment': 10000}), ('Add 1,500 now', {'extra_deposit': 1500}), ('Add 4,000 now', {'extra_deposit': 4000}))))

# 9 ------------------------------------------------------------ expense log check
EM = '{range:expmonth.month}'
def TOPC(n, col): return 'IFERROR(INDEX({range:expmonth.%s},MATCH(%d,{range:expmonth.rank_last},0)),"")' % (col, n)
OVERN = 'COUNTIFS(%s,%s,{range:expmonth.used},">"&(1+{in:margin}))' % (EM, LM)
tools.append(TOOL('expcheck', 'Expense Log Check', 'Which category is over your own budget',
    'Last complete month by category against your own budget, ranked from the most over to the least; type the margin over budget you accept and read the top three with their own 12-month average.', [
    I('margin', 'Margin over budget you accept', 0.10, 'pct')], [
    O('Month checked', 'date', LM), O('Categories over budget', 'int', OVERN), O('Total over budget', 'money', 'SUMIFS({range:expmonth.difference},%s,%s,{range:expmonth.difference},">0")' % (EM, LM)),
    O('Most over: category', 'text', TOPC(1, 'category')), O('Most over: amount over', 'money', TOPC(1, 'difference')), O('Most over: spend against its 12-month average', 'pct', 'IFERROR(%s/%s-1,0)' % (TOPC(1, 'amount'), TOPC(1, 'cat_avg'))),
    O('Second: category', 'text', TOPC(2, 'category')), O('Second: amount over', 'money', TOPC(2, 'difference')), O('Third: category', 'text', TOPC(3, 'category')), O('Third: amount over', 'money', TOPC(3, 'difference')),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (OVERN, vt('Over budget'), vt('Within budget')))],
    GR('What if', ('Accept 0 over', {'margin': 0.0}), ('Accept 25 percent over', {'margin': 0.25}), ('Accept 50 percent over', {'margin': 0.5}), ('Accept 100 percent over', {'margin': 1.0}))))

# 10 ----------------------------------------------------------- recurring cost review
VB = '{range:expenses.vendor}={in:vendor}'
V12 = 'SUMIFS({range:expenses.amount},{range:expenses.vendor},{in:vendor},{range:expenses.date},">"&({today}-365))'
VN12 = 'COUNTIFS({range:expenses.vendor},{in:vendor},{range:expenses.date},">"&({today}-365))'
LASTB = 'SUMPRODUCT(MAX((%s)*{range:expenses.date}))' % VB
tools.append(TOOL('recur', 'Recurring Cost Review', 'Keep, ask for a lower price or cancel a recurring cost',
    'Type a vendor as written in Expenses and the share of the service you use: the bills and cost in 12 months, the unused part and a keep, lower price or cancel verdict.', [
    I('vendor', 'Vendor (as written in Expenses)', 'Writing and design tools', 'text'), I('use_share', 'Share of the service you really use', 0.4, 'pct'),
    I('keep_at', 'Keep from this use share', 0.6, 'pct'), I('cancel_below', 'Cancel below this use share', 0.3, 'pct')], [
    O('Bills in the last 12 months', 'int', VN12), O('Average bill', 'money', 'IFERROR(%s/%s,0)' % (V12, VN12)), O('Cost, last 12 months', 'money', V12),
    O('Share of all expenses', 'pct', 'IFERROR(%s/%s,0)' % (V12, 'SUMIFS({range:expenses.amount},{range:expenses.date},">"&({today}-365))')), O('Last bill on', 'date', 'IF(%s=0,"",%s)' % (LASTB, LASTB)),
    O('Days since the last bill', 'int', 'IF(%s=0,0,{today}-%s)' % (LASTB, LASTB)), O('Cost of the part you do not use, a year', 'money', '%s*(1-{in:use_share})' % V12),
    O('Verdict', 'text', 'IF(%s=0,%s,IF({in:use_share}>={in:keep_at},%s,IF({in:use_share}<{in:cancel_below},%s,%s)))' % (VN12, vt('Cancel'), vt('Keep'), vt('Cancel'), vt('Ask for a lower price')))],
    GR('What if', ('Use 10 percent', {'use_share': 0.1}), ('Use 30 percent', {'use_share': 0.3}), ('Use 60 percent', {'use_share': 0.6}), ('Use 90 percent', {'use_share': 0.9}))))

# 11 ----------------------------------------------------------- year-end summary
YW = '{range:%s.%s},">="&EDATE(' + MS + ',-{in:months}),{range:%s.%s},"<"&' + MS
def YS(t, col, dc='month'): return 'SUMIFS({range:%s.%s},{range:%s.%s},">="&EDATE(%s,-{in:months}),{range:%s.%s},"<"&%s)' % (t, col, t, dc, MS, t, dc, MS)
MISSN = 'COUNTIFS({range:expenses.receipt},{list:yesno.no},{range:expenses.month},">="&EDATE(%s,-{in:months}),{range:expenses.month},"<"&%s)' % (MS, MS)
MISSA = 'SUMIFS({range:expenses.amount},{range:expenses.receipt},{list:yesno.no},{range:expenses.month},">="&EDATE(%s,-{in:months}),{range:expenses.month},"<"&%s)' % (MS, MS)
tools.append(TOOL('yeartool', 'Year-end Summary Check', 'Is your year-end pack complete for your adviser',
    'Type the months the pack covers (12 for a year): income, costs, profit, set-aside, tax paid and draws in plain words, plus the expense lines that still miss a receipt and the check against the log.', [
    I('months', 'Months the pack covers', 12, 'int'), I('receipt_limit', 'Missing receipts you accept', 0, 'int')], [
    O('Revenue', 'money', YS('pnl', 'revenue')), O('Costs', 'money', YS('pnl', 'costs')), O('Profit', 'money', YS('pnl', 'profit')), O('Profit margin', 'pct', 'IFERROR(%s/%s,0)' % (YS('pnl', 'profit'), YS('pnl', 'revenue'))),
    O('Tax set-aside', 'money', YS('taxmonth', 'set_aside')), O('Tax paid', 'money', YS('taxmonth', 'tax_paid')), O('Owner draws', 'money', YS('cash', 'owner_draw')),
    O('Expenses in the log', 'money', YS('expenses', 'amount')), O('Expenses in Profit and Loss', 'money', YS('pnl', 'expenses')), O('Difference between the log and Profit and Loss', 'money', '%s-%s' % (YS('expenses', 'amount'), YS('pnl', 'expenses'))),
    O('Expense lines without a receipt', 'int', MISSN), O('Amount without a receipt', 'money', MISSA),
    O('Verdict', 'text', 'IF(%s<={in:receipt_limit},%s,%s)' % (MISSN, vt('Complete'), vt('Missing receipts')))],
    GR('What if', ('Last 3 months', {'months': 3}), ('Last 6 months', {'months': 6}), ('Last 18 months', {'months': 18}), ('Accept 5 missing receipts', {'receipt_limit': 5}), ('Accept 10 missing receipts', {'receipt_limit': 10}))))

# 12 ----------------------------------------------------------- owner health check
HVD = lambda n: 'INDEX({range:health.verdict},%d)' % n
tools.append(TOOL('health_tool', 'Owner Health Check', 'How healthy is the business against your own targets',
    'Green, amber or red for each area against your own targets and a score from 0 to 100 (green 100, amber 50, red 0); type the scores that count as green and amber.', [
    I('green_score', 'Score that counts as green', 75, 'int'), I('amber_score', 'Score that counts as amber', 50, 'int')], [
    O('Areas in green', 'int', 'COUNTIFS({range:health.verdict},%s)' % vh('Green')), O('Areas in amber', 'int', 'COUNTIFS({range:health.verdict},%s)' % vh('Amber')), O('Areas in red', 'int', 'COUNTIFS({range:health.verdict},%s)' % vh('Red')),
    O('Score', 'int', 'AVERAGE({range:health.points})'), O('Profit margin, last 12 months', 'text', HVD(1)), O('Ad return', 'text', HVD(3)), O('Months of cash cover', 'text', HVD(5)), O('Store dependence', 'text', HVD(7)),
    O('Read-through, book 1 to book 2', 'text', HVD(8)), O('Titles under break-even', 'text', HVD(10)), O('Area furthest from the target', 'text', 'INDEX({range:health.top_area},1)'),
    O('Verdict', 'text', 'IF(AVERAGE({range:health.points})>={in:green_score},%s,IF(AVERAGE({range:health.points})>={in:amber_score},%s,%s))' % (vh('Green'), vh('Amber'), vh('Red')))],
    GR('What if', ('Green from 90', {'green_score': 90}), ('Green from 60', {'green_score': 60}), ('Amber from 30', {'amber_score': 30}), ('Amber from 65', {'amber_score': 65}))))

# 13 ----------------------------------------------------------- three actions of the month
def ACT(n, col): return 'IF(IFERROR(INDEX({range:health.gap},MATCH(%d,{range:health.rank},0)),0)>{in:min_gap},INDEX({range:health.%s},MATCH(%d,{range:health.rank},0)),%s)' % (n, col, n, act('Keep going'))
tools.append(TOOL('actions3', 'Three Actions of the Month', 'What to fix first this month',
    'The areas ranked by how far they sit from your target, with one action for each of the worst three; type the distance under which an area is left alone.', [
    I('min_gap', 'Distance from target under which you leave an area alone', 0.0, 'pct')], [
    O('Areas that need action', 'int', 'COUNTIFS({range:health.gap},">"&{in:min_gap})'), O('Action 1: area', 'text', ACT(1, 'area')), O('Action 1: what to do', 'text', ACT(1, 'action')), O('Action 1: distance from the target', 'pct', 'IF(%s="",0,INDEX({range:health.gap},MATCH(1,{range:health.rank},0)))' % ACT(1, 'area')),
    O('Action 2: area', 'text', ACT(2, 'area')), O('Action 2: what to do', 'text', ACT(2, 'action')), O('Action 2: distance from the target', 'pct', 'IF(%s=%s,0,INDEX({range:health.gap},MATCH(2,{range:health.rank},0)))' % (ACT(2, 'area'), act('Keep going'))),
    O('Action 3: area', 'text', ACT(3, 'area')), O('Action 3: what to do', 'text', ACT(3, 'action')), O('Action 3: distance from the target', 'pct', 'IF(%s=%s,0,INDEX({range:health.gap},MATCH(3,{range:health.rank},0)))' % (ACT(3, 'area'), act('Keep going'))),
    O('Verdict', 'text', 'IF(COUNTIFS({range:health.gap},">"&{in:min_gap})=0,%s,%s)' % (act('Keep going'), vh('Check')))],
    GR('What if', ('Leave areas within 10 percent', {'min_gap': 0.1}), ('Leave areas within 25 percent', {'min_gap': 0.25}), ('Leave areas within 50 percent', {'min_gap': 0.5}), ('Leave areas within 100 percent', {'min_gap': 1.0}))))

# 14 ----------------------------------------------------------- margin and profit trend
P3 = SUMN('pnl', 'profit', 3); R3 = SUMN('pnl', 'revenue', 3); P12 = SUM12('pnl', 'profit'); R12 = SUM12('pnl', 'revenue')
PP = 'SUMIFS({range:pnl.profit},{range:pnl.month},">="&EDATE(%s,-24),{range:pnl.month},"<"&EDATE(%s,-12))' % (MS, MS)
RP = 'SUMIFS({range:pnl.revenue},{range:pnl.month},">="&EDATE(%s,-24),{range:pnl.month},"<"&EDATE(%s,-12))' % (MS, MS)
tools.append(TOOL('trend', 'Margin and Profit Trend', 'Is your profit improving, flat or falling',
    'Profit a month and margin for the last 3 months against the last 12 months against the year before (complete months only); type the change you count as flat.', [
    I('tolerance', 'Change you count as flat', 0.05, 'pct')], [
    O('Profit a month, last 3 months', 'money', '%s/3' % P3), O('Profit a month, last 12 months', 'money', '%s/12' % P12), O('Profit a month, the 12 months before', 'money', '%s/12' % PP),
    O('Margin, last 3 months', 'pct', 'IFERROR(%s/%s,0)' % (P3, R3)), O('Margin, last 12 months', 'pct', 'IFERROR(%s/%s,0)' % (P12, R12)), O('Margin, the 12 months before', 'pct', 'IFERROR(%s/%s,0)' % (PP, RP)),
    O('Last 3 months against last 12 months', 'pct', 'IFERROR((%s/3)/(%s/12)-1,0)' % (P3, P12)), O('Last 12 months against the year before', 'pct', 'IFERROR(%s/%s-1,0)' % (P12, PP)),
    O('Verdict', 'text', 'IF(IFERROR((%s/3)/(%s/12)-1,0)>{in:tolerance},%s,IF(IFERROR((%s/3)/(%s/12)-1,0)<-{in:tolerance},%s,%s))' % (P3, P12, vt('Improving'), P3, P12, vt('Falling'), vt('Flat')))],
    GR('What if', ('Flat within 0 percent', {'tolerance': 0.0}), ('Flat within 2 percent', {'tolerance': 0.02}), ('Flat within 10 percent', {'tolerance': 0.10}), ('Flat within 25 percent', {'tolerance': 0.25}))))

# 15 ----------------------------------------------------------- author statement
def AU(col): return 'SUMIFS({range:authstmt.%s},{range:authstmt.pen_name},{in:pen_name},{range:authstmt.month},{in:month})' % col
tools.append(TOOL('author_stmt', 'Author Statement Tool', 'What is payable to one author for one month',
    'Pick a pen name (an author in a small press) and a month: royalties earned, share, advance recouped and left, costs charged back and the amount payable.', [
    IL('pen_name', 'Pen name', 'penname', 'Corvin Ashdale'), I('month', 'Month (the 1st)', iso(month_start(1)), 'date')], [
    O('Royalties earned', 'money', AU('royalties_earned')), O('Author share', 'pct', 'IFERROR(%s/%s,0)' % (AU('author_part'), AU('royalties_earned'))), O('Author part', 'money', AU('author_part')),
    O('Advance recouped this month', 'money', AU('advance_recouped')), O('Advance left', 'money', AU('advance_left')), O('Costs charged back', 'money', AU('costs_charged_back')),
    O('Payable', 'money', AU('payable')), O('Press share', 'money', AU('press_share')), O('Payable against the last 3 months average', 'pct', 'IFERROR(%s/AVERAGEIFS({range:authstmt.payable},{range:authstmt.pen_name},{in:pen_name},%s)-1,0)' % (AU('payable'), WIN('{range:authstmt.month}', 3))),
    O('Verdict', 'text', 'IF(AND(%s>0,%s>0),%s,%s)' % (AU('royalties_earned'), AU('payable'), vh('Ready to pay'), vh('Check')))],
    GR('What if', ('Tamsin Hartwell', {'pen_name': '=' + tok('penname', 'Tamsin Hartwell')}))))

# 16 ----------------------------------------------------------- shares check
def AM(col): return 'SUMIFS({range:authstmt.%s},{range:authstmt.month},{in:month})' % col
PNLR = '(SUMIFS({range:pnl.royalties},{range:pnl.month},{in:month})+SUMIFS({range:pnl.page_reads},{range:pnl.month},{in:month}))'
ALLOC = '(%s+%s+%s+%s)' % (AM('payable'), AM('advance_recouped'), AM('costs_charged_back'), AM('press_share'))
DIFFN = '(%s-%s)' % (AM('royalties_earned'), PNLR)
OKS = 'AND(MAX({range:authors.author_share})<=1,MIN({range:authors.author_share})>=0)'
tools.append(TOOL('sharescheck', 'Shares Check', 'Do the shares and the money add up',
    'For one month: shares between 0 and 100 percent, the parts add up to the royalties earned, and they match your Profit and Loss within your tolerance.', [
    I('month', 'Month (the 1st)', iso(month_start(1)), 'date'), I('tolerance', 'Difference to Profit and Loss that you accept', 0.03, 'pct')], [
    O('Highest author share', 'pct', 'MAX({range:authors.author_share})'), O('Lowest author share', 'pct', 'MIN({range:authors.author_share})'), O('Royalties earned, all authors', 'money', AM('royalties_earned')),
    O('Payable plus advance plus costs plus press share', 'money', ALLOC), O('Difference inside the statements', 'money', '%s-%s' % (AM('royalties_earned'), ALLOC)),
    O('Royalties and page reads in Profit and Loss', 'money', PNLR), O('Difference to Profit and Loss', 'money', DIFFN), O('Difference share', 'pct', 'IFERROR(%s/%s,0)' % (DIFFN, PNLR)),
    O('Verdict', 'text', 'IF(AND(%s,ABS(%s-%s)<0.01,ABS(IFERROR(%s/%s,0))<={in:tolerance}),%s,%s)' % (OKS, AM('royalties_earned'), ALLOC, DIFFN, PNLR, vh('Adds up'), vh('Does not add up')))],
    GR('What if', ('Accept 0.5 percent', {'tolerance': 0.005}), ('Accept 1 percent', {'tolerance': 0.01}), ('Accept 5 percent', {'tolerance': 0.05}))))

# 17 ----------------------------------------------------------- advance recoup tracker
def AV(col): return 'SUMIFS({range:authstmt.%s},{range:authstmt.pen_name},{in:pen_name})' % col
ADVP = 'SUMPRODUCT(MAX(({range:authstmt.pen_name}={in:pen_name})*{range:authstmt.advance_paid}))'
ADVL = '(%s-%s)' % (ADVP, AV('advance_recouped'))
PACE = '(SUMIFS({range:authstmt.advance_recouped},{range:authstmt.pen_name},{in:pen_name},%s)/3)' % WIN('{range:authstmt.month}', 3)
tools.append(TOOL('advrecoup', 'Advance Recoup Tracker', 'When is the advance earned back at your pace',
    'Pick a pen name: the advance paid, the part recouped, what is left, the average recouped in the last 3 months and the month it is recouped at that pace, against the months you accept.', [
    IL('pen_name', 'Pen name', 'penname', 'Corvin Ashdale'), I('target_months', 'Months in which you want it recouped', 12, 'int')], [
    O('Advance paid', 'money', ADVP), O('Recouped so far', 'money', AV('advance_recouped')), O('Advance left', 'money', ADVL), O('Share recouped', 'pct', 'IFERROR(%s/%s,0)' % (AV('advance_recouped'), ADVP)),
    O('Average recouped a month, last 3 months', 'money', PACE), O('Months left at that pace', 'num', 'IFERROR(%s/%s,0)' % (ADVL, PACE)),
    O('Month it is recouped', 'date', 'IF(AND(%s>0,%s>0),EDATE(%s,ROUNDUP(%s/%s,0)),%s)' % (ADVL, PACE, MS, ADVL, PACE, vh('No advance'))),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s<=0.005,%s,IF(IFERROR(%s/%s,99)<={in:target_months},%s,%s)))' % (ADVP, vh('No advance'), ADVL, vh('Recouped'), ADVL, PACE, vh('On pace'), vh('Slow')))],
    GR('What if', ('Want it in 2 months', {'target_months': 2}), ('Want it in 6 months', {'target_months': 6}), ('Tamsin Hartwell', {'pen_name': '=' + tok('penname', 'Tamsin Hartwell')}))))

# 18 ----------------------------------------------------------- author payments schedule
CB = '{range:authsched.cash_before}'; MT = '{range:authsched.month_total}'
LOWA = MIN12(lambda k: 'INDEX(%s,%d)-INDEX(%s,%d)*{in:share_now}' % (CB, k, MT, k))
tools.append(TOOL('authpay', 'Author Payments Schedule Tool', 'Can you pay every author in full each month',
    'The payable to all authors for the next 6 months against the forecast cash: type the share you pay at month end and your floor; a one-author business reads it as a split of the draw.', [
    I('share_now', 'Share you pay at month end', 1.0, 'pct'), I('floor', 'Lowest cash you accept (your own number)', CASH_FLOOR)], [
    O('Payable to all authors, next 6 months', 'money', 'SUM({range:authsched.payable})'), O('Highest month, all authors', 'money', 'MAX(%s)' % MT), O('Lowest cash after paying', 'money', LOWA),
    O('Months below the floor', 'int', '(' + '+'.join('(INDEX(%s,%d)-INDEX(%s,%d)*{in:share_now}<{in:floor})' % (CB, k, MT, k) for k in range(1, 13)) + ')/COUNTIFS({range:authsched.month},INDEX({range:authsched.month},1))'), O('Cash needed to hold the floor', 'money', 'MAX(0,{in:floor}-%s)' % LOWA),
    O('Verdict', 'text', 'IF(%s>={in:floor},%s,%s)' % (LOWA, vc('Pay in full'), vc('Pay in two parts')))],
    GR('What if', ('Pay half at month end', {'share_now': 0.5}), ('Pay 70 percent at month end', {'share_now': 0.7}), ('Pay nothing now', {'share_now': 0.0}), ('Floor 5,000', {'floor': 5000}))))
assert len(tools) == 18, len(tools)
