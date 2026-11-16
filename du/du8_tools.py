"""Doula business suite part 8: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du8_lists import *
import du8_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='num', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, lab): return IN(k, label, 'list', key(lst, lab), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
LM = 'EDATE(%s,-1)' % MS
CASHNOW = 'SUMIFS({range:cash.closing},{range:cash.month},%s)' % MS
def T12(col, t='pnl'): return 'SUMIFS({range:%s.%s},{range:%s.month},">"&EDATE(%s,-12),{range:%s.month},"<="&%s)' % (t, col, t, MS, t, MS)
def A3(col, t='pnl'): return 'AVERAGEIFS({range:%s.%s},{range:%s.month},">="&EDATE(%s,-3),{range:%s.month},"<"&%s)' % (t, col, t, MS, t, MS)
def DMY(x): return 'DAY(%s)&" "&%s&" "&YEAR(%s)' % (x, MN(x), x)
def MY(x): return '%s&" "&YEAR(%s)' % (MN(x), x)
def NUM(x): return 'ROUND(%s,0)' % x
YEAR_SETASIDE = 'DATE(YEAR({today}),1,1)'
tools = []
RT = lambda k: tok('rag', k)
OPEN_ = '{range:renewals.is_open},1'

# 1 ------------------------------------------------------------ training and renewal dates
NRED = 'COUNTIFS(%s,{range:renewals.days_left},"<="&{in:red})' % OPEN_
NAMB = 'COUNTIFS(%s,{range:renewals.days_left},">"&{in:red},{range:renewals.days_left},"<="&{in:amber})' % OPEN_
NEXTD = 'SMALL({range:renewals.open_due},1)'
NXI = 'IFERROR(INDEX({range:renewals.item},MATCH(%s,{range:renewals.open_due},0))&"","")' % NEXTD
tools.append(TOOL('renew_dates', 'Training and Renewal Dates', 'Which renewals and training dates need action now',
    'Type the days that make a renewal red and amber and pick an item: the open renewals by colour, the next one due, the next date of the item you pick and the cost of renewals and training in the next 12 months; read from Renewals and Training.', [
    I('red', 'Red when due within, days', 30, 'int'), I('amber', 'Amber when due within, days', 60, 'int'), IL('item', 'Renewal item to check', 'renewal', D.DEF_RENEWAL)], [
    O('Red renewals (due soon or overdue)', 'int', NRED), O('Amber renewals', 'int', NAMB), O('Green renewals still open', 'int', 'COUNTIFS(%s,{range:renewals.days_left},">"&{in:amber})' % OPEN_),
    O('Next renewal', 'text', NXI), O('Holder of the next renewal', 'text', 'IFERROR(INDEX({range:renewals.holder},MATCH(%s,{range:renewals.open_due},0))&"","")' % NEXTD),
    O('Next renewal due on', 'date', NEXTD), O('Days to the next renewal', 'int', '%s-{today}' % NEXTD),
    O('Next date of the item you picked', 'date', 'SUMIFS({range:renewals.due_date},{range:renewals.item_key},{in:item}&"|1")'),
    O('Days to that date', 'int', 'SUMIFS({range:renewals.due_date},{range:renewals.item_key},{in:item}&"|1")-{today}'),
    O('Holder of that item', 'text', 'IFERROR(INDEX({range:renewals.holder},MATCH({in:item}&"|1",{range:renewals.item_key},0))&"","")'),
    O('Usual cost of that item', 'money', 'IFERROR(INDEX({range:renewal_items.cost},MATCH({in:item},{range:renewal_items.item},0)),0)'),
    O('Renewals due in the next 12 months, cost', 'money', 'SUMIFS({range:renewals.cost},%s,{range:renewals.days_left},"<=365")' % OPEN_),
    O('Training days planned, next 90 days', 'int', 'COUNTIFS({range:training.date},">"&{today},{range:training.date},"<="&({today}+90))'),
    O('Training cost, next 12 months', 'money', 'SUMIFS({range:training.cost},{range:training.date},">"&{today},{range:training.date},"<="&({today}+365))'),
    O('Verdict', 'text', 'IF(COUNTIFS(%s)=0,%s,%s&" "&%s&", "&%s&" "&%s&". "&%s&": "&%s&" "&%s&" "&(%s-{today})&" "&%s)' % (OPEN_, vt('No open renewals'), RT('Red'), NRED, RT('Amber'), NAMB, vt('Next renewal'), NXI, vt('in'), NEXTD, vt('days')))],
    GR('What if', ('Red within 14 days', {'red': 14}), ('Red within 45 days', {'red': 45}), ('Amber within 90 days', {'amber': 90}), ('Red 45 and amber 120 days', {'red': 45, 'amber': 120}), ('Red 60 and amber 90 days', {'red': 60, 'amber': 90}))))

# 2 ------------------------------------------------------------ expense tracker by category
EM = 'DATE(YEAR({in:month}),MONTH({in:month}),1)'
EACT = 'SUMIFS({range:expenses.amount},{range:expenses.category},{in:category},{range:expenses.month},%s)' % EM
EBUD = 'IFERROR(INDEX({range:budget.monthly_budget},MATCH({in:category},{range:budget.category},0)),0)'
ELY = 'SUMIFS({range:expenses.amount},{range:expenses.category},{in:category},{range:expenses.month},EDATE(%s,-12))' % EM
EREV = 'SUMIFS({range:pnl.revenue},{range:pnl.month},%s)' % EM
tools.append(TOOL('expense_tracker', 'Expense Tracker', 'Which expense category is over budget and how it compares with last year',
    'Pick a category and a month: the spending against the monthly budget, the 3 months before, the same month last year and the share of revenue; read from Expenses, Budget and Profit and Loss.', [
    IL('category', 'Expense category', 'expcat', D.DEF_CAT), I('month', 'Month (the 1st of the month)', I_ := D.I(D.LM0), 'date'), I('tol', 'Spending over budget that you accept', 0.10, 'pct')], [
    O('Spending in the month', 'money', EACT), O('Monthly budget', 'money', EBUD), O('Over or under budget', 'money', '%s-%s' % (EACT, EBUD)),
    O('Share of the budget used', 'pct', 'IFERROR(%s/%s,0)' % (EACT, EBUD)), O('Average of the 3 months before', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.category},{in:category},{range:expenses.month},">="&EDATE(%s,-3),{range:expenses.month},"<"&%s)/3' % (EM, EM)),
    O('Same month last year', 'money', ELY), O('Change on last year', 'money', '%s-%s' % (EACT, ELY)), O('Revenue of the month', 'money', EREV), O('Share of revenue', 'pct', 'IFERROR(%s/%s,0)' % (EACT, EREV)),
    O('Share of revenue, same month last year', 'pct', 'IFERROR(%s/SUMIFS({range:pnl.revenue},{range:pnl.month},EDATE(%s,-12)),0)' % (ELY, EM)),
    O('All expenses in the month', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.month},%s)' % EM), O('Share of all expenses', 'pct', 'IFERROR(%s/SUMIFS({range:expenses.amount},{range:expenses.month},%s),0)' % (EACT, EM)),
    O('Categories over budget in the month', 'int', 'COUNTIFS({range:expvar.month},%s,{range:expvar.variance},">0")' % EM),
    O('Categories over the share you accept', 'int', 'COUNTIFS({range:expvar.month},%s,{range:expvar.over_share},">"&{in:tol})' % EM),
    O('Verdict', 'text', 'IF(%s>%s,{in:category}&" "&%s&" "&%s&" "&%s,{in:category}&" "&%s&" "&%s&" "&%s)' % (EACT, EBUD, vt('is'), NUM('%s-%s' % (EACT, EBUD)), vt('over budget'), vt('is'), NUM('%s-%s' % (EBUD, EACT)), vt('under budget')))],
    GR('What if', ('Accept 0% over budget', {'tol': 0.0}), ('Accept 5% over budget', {'tol': 0.05}), ('Accept 25% over budget', {'tol': 0.25}), ('Accept 50% over budget', {'tol': 0.5}), ('Accept 100% over budget', {'tol': 1.0}))))

# 3 ------------------------------------------------------------ uneven-month cash forecast
BEST, WORST = tok('scen', 'Best'), tok('scen', 'Worst')
def CL(fn): return 'IF({in:scenario}=%s,%s,IF({in:scenario}=%s,%s,%s))' % (BEST, fn('{range:forecast.closing_best}'), WORST, fn('{range:forecast.closing_worst}'), fn('{range:forecast.closing}'))
LOWC = CL(lambda r: 'SMALL(%s,1)' % r)
LOWM = CL(lambda r: 'INDEX({range:forecast.month},MATCH(SMALL(%s,1),%s,0))' % (r, r))
FACT = 'IF({in:scenario}=%s,{set:best_factor},IF({in:scenario}=%s,{set:worst_factor},1))' % (BEST, WORST)
FIXAV = '(AVERAGE({range:forecast.fixed_costs})+{set:owner_draw})'
tools.append(TOOL('cash_forecast', 'Uneven-Month Cash Forecast', 'How low will cash go in the next 12 months and is the cover enough',
    'Pick a scenario and type the floor and the months of cover you want: cash in per month from payment plans, balances, new bookings and births not yet booked, less costs, owner pay and set-aside; the lowest month and the cover; read from Cash Forecast.', [
    IL('scenario', 'Scenario', 'scen', 'Base'), I('floor', 'Lowest cash you accept', CASH_FLOOR, 'money'), I('cover', 'Months of cover you want', CASH_COVER_MONTHS, 'int')], [
    O('Cash now', 'money', CASHNOW), O('Lowest closing cash ahead', 'money', LOWC), O('Month of the lowest cash', 'date', LOWM), O('Months below the floor', 'int', CL(lambda r: 'COUNTIFS(%s,"<"&{in:floor})' % r)),
    O('Months of cover at the lowest cash', 'num', 'IFERROR(%s/%s,0)' % (LOWC, FIXAV)), O('Months of cover short of your wish', 'num', 'MAX(0,{in:cover}-IFERROR(%s/%s,0))' % (LOWC, FIXAV)),
    O('Closing cash in 12 months', 'money', CL(lambda r: 'SUMIFS(%s,{range:forecast.ahead},12)' % r)),
    O('Expected cash in, 12 months', 'money', 'SUM({range:forecast.scheduled_in})+(SUM({range:forecast.new_in})+SUM({range:forecast.unbooked_in}))*%s' % FACT),
    O('Costs and owner pay, 12 months', 'money', 'SUM({range:forecast.expected_costs})+SUM({range:forecast.owner_pay})'),
    O('Busiest month for cash in', 'date', 'INDEX({range:forecast.month},MATCH(LARGE({range:forecast.expected_in},1),{range:forecast.expected_in},0))'),
    O('Quietest month for cash in', 'date', 'INDEX({range:forecast.month},MATCH(SMALL({range:forecast.expected_in},1),{range:forecast.expected_in},0))'),
    O('Cash in of the quietest month', 'money', 'SMALL({range:forecast.expected_in},1)'), O('Births due in the next 12 months', 'int', 'SUM({range:forecast.due_dates})'),
    O('Unearned cash held now', 'money', 'SUM({range:contracts.unearned})'),
    O('Verdict', 'text', '%s&" "&%s&" "&%s&" "&%s&", "&ROUND(IFERROR(%s/%s,0),1)&" "&%s' % (vt('Lowest cash'), NUM(LOWC), vt('in'), MY(LOWM), LOWC, FIXAV, vt('months of cover')))],
    GR('What if', ('Floor 25000', {'floor': 25000}), ('Floor 30000', {'floor': 30000}), ('Floor 40000', {'floor': 40000}), ('Cover of 6 months', {'cover': 6}))))

# 4 ------------------------------------------------------------ owner pay and tax set-aside
STILL = 'SUMIFS({range:tax.set_aside},{range:tax.status},%s)' % tok('taxstatus', 'Planned')
AVGP = 'IFERROR(AVERAGEIFS({range:pnl.profit},{range:pnl.month},">="&EDATE(%s,-{in:months}),{range:pnl.month},"<"&%s),0)' % (MS, MS)
ABOVE = '(%s-{in:floor}-%s)' % (CASHNOW, STILL)
AFFORD = 'MAX(0,MIN({in:draw},%s))' % ABOVE
tools.append(TOOL('owner_pay', 'Owner Pay and Tax Set-Aside', 'Can I pay myself this month and how much should I set aside',
    'Type your draw, the set-aside share and the floor: the average profit, the set-aside to move every month, the draw your profit supports and the draw your cash allows; confirm the set-aside share with your adviser.', [
    I('draw', 'Owner draw for the month', OWNER_DRAW, 'money'), I('aside', 'Set-aside share (confirm with your adviser)', TAX_SET_ASIDE_PCT, 'pct'), I('floor', 'Lowest cash you accept', CASH_FLOOR, 'money'),
    I('months', 'Months of profit to average', 6, 'int')], [
    O('Average monthly profit', 'money', AVGP), O('Set-aside to move each month', 'money', 'ROUND(MAX(0,%s)*{in:aside},0)' % AVGP), O('Profit after the set-aside', 'money', '%s-ROUND(MAX(0,%s)*{in:aside},0)' % (AVGP, AVGP)),
    O('Your draw', 'money', '{in:draw}'), O('Profit left after the draw', 'money', '%s-ROUND(MAX(0,%s)*{in:aside},0)-{in:draw}' % (AVGP, AVGP)), O('Draw your profit supports', 'money', 'MAX(0,%s-ROUND(MAX(0,%s)*{in:aside},0))' % (AVGP, AVGP)),
    O('Cash now', 'money', CASHNOW), O('Set-aside still to move', 'money', STILL), O('Cash above the floor after the set-aside', 'money', ABOVE), O('Draw your cash allows now', 'money', AFFORD),
    O('Months the draw is covered by profit', 'num', 'IFERROR(MAX(0,%s-ROUND(MAX(0,%s)*{in:aside},0))/{in:draw},0)' % (AVGP, AVGP)),
    O('Set-aside moved this year', 'money', 'SUMIFS({range:tax.set_aside},{range:tax.status},%s,{range:tax.month},">="&%s)' % (tok('taxstatus', 'Moved'), YEAR_SETASIDE)),
    O('Owner draw taken this year', 'money', 'SUMIFS({range:cash.owner_draw},{range:cash.month},">="&%s)' % YEAR_SETASIDE),
    O('Verdict', 'text', 'IF({in:draw}<=%s,%s&" "&{in:draw},%s&" "&%s&", "&%s)' % (AFFORD, vt('Yes, pay yourself'), vt('Reduce your draw to'), NUM(AFFORD), vt('cash would fall below the floor')))],
    GR('What if', ('Draw 4800', {'draw': 4800}), ('Draw 6000', {'draw': 6000}), ('Draw 30000', {'draw': 30000}), ('Set aside 30%', {'aside': 0.30}), ('Floor 38000', {'floor': 38000, 'draw': 4800}))))

# 5 ------------------------------------------------------------ profit ratios by month
PM = 'DATE(YEAR({in:month}),MONTH({in:month}),1)'
def PR(c, m=PM): return 'SUMIFS({range:pnl.%s},{range:pnl.month},%s)' % (c, m)
def PA(c): return 'IFERROR(AVERAGEIFS({range:pnl.%s},{range:pnl.month},">="&EDATE(%s,-3),{range:pnl.month},"<"&%s),0)' % (c, PM, PM)
def PL(c): return 'SUMIFS({range:pnl.%s},{range:pnl.month},EDATE(%s,-12))' % (c, PM)
tools.append(TOOL('ratios', 'Profit Ratios by Month', 'Is the profit margin above or below my own history',
    'Pick a month: the margin, the doula pay share of revenue and the cost per birth, each against the 3 months before and the same month last year; read from Profit and Loss.', [
    I('month', 'Month (the 1st of the month)', D.I(D.LM0), 'date'), I('band', 'Margin points that count as different', 0.02, 'pct')], [
    O('Revenue', 'money', PR('revenue')), O('Profit', 'money', PR('profit')), O('Profit margin', 'pct', PR('margin')), O('Margin, average of the 3 months before', 'pct', PA('margin')), O('Margin, same month last year', 'pct', PL('margin')),
    O('Margin against the 3 months before', 'pct', '%s-%s' % (PR('margin'), PA('margin'))), O('Doula pay share of revenue', 'pct', PR('doula_share')), O('Doula pay share, 3 months before', 'pct', PA('doula_share')),
    O('Doula pay share, same month last year', 'pct', PL('doula_share')), O('Cost per birth', 'money', PR('cost_birth')), O('Cost per birth, 3 months before', 'money', PA('cost_birth')), O('Cost per birth, same month last year', 'money', PL('cost_birth')),
    O('Profit per birth', 'money', PR('profit_birth')), O('Births', 'int', PR('births')),
    O('Verdict', 'text', 'IF(%s>%s+{in:band},%s,IF(%s<%s-{in:band},%s,%s))' % (PR('margin'), PA('margin'), vt('Margin is above your own history'), PR('margin'), PA('margin'), vt('Margin is below your own history'), vt('Margin matches your own history')))],
    GR('What if', ('Band of 1 point', {'band': 0.01}), ('Band of 4 points', {'band': 0.04}), ('Band of 8 points', {'band': 0.08}), ('Band of 10 points', {'band': 0.10}), ('Band of 0.5 point', {'band': 0.005}))))

# 6 ------------------------------------------------------------ compare with own history
def CPM(k, c): return 'IFERROR(INDEX({range:compare.%s},MATCH(%d,{range:compare.no},0)),0)' % (c, k)
def CMN(f, k): return 'IFERROR(INDEX({range:compare.measure},MATCH(%s({range:compare.score},%d),{range:compare.score},0))&"","")' % (f, k)
WORSE = 'COUNTIFS({range:compare.score},"<"&(-{in:drop}))'
tools.append(TOOL('own_history', 'Compare With Own History', 'Which monthly figures dropped against my own history',
    'Type the change that counts as a drop: every monthly figure for the last full month against the average of the 3 months before and the same month last year; a rise in a cost counts as a drop; read from Own History Compare.', [
    I('drop', 'Change that counts as a drop', 0.10, 'pct')], [
    O('Figures checked', 'int', 'COUNTA({range:compare.measure})'), O('Figures that dropped', 'int', WORSE), O('Figures that improved', 'int', 'COUNTIFS({range:compare.score},">"&{in:drop})'),
    O('Figures within range', 'int', 'COUNTA({range:compare.measure})-%s-COUNTIFS({range:compare.score},">"&{in:drop})' % WORSE),
    O('Biggest drop', 'text', CMN('SMALL', 1)), O('Size of the biggest drop', 'pct', 'SMALL({range:compare.score},1)'), O('Second biggest drop', 'text', CMN('SMALL', 2)), O('Size of the second drop', 'pct', 'SMALL({range:compare.score},2)'),
    O('Third biggest drop', 'text', CMN('SMALL', 3)), O('Biggest improvement', 'text', CMN('LARGE', 1)), O('Size of the biggest improvement', 'pct', 'LARGE({range:compare.score},1)'),
    O('Profit, change on the 3 months before', 'pct', CPM(12, 'change')), O('Profit, change on last year', 'pct', CPM(12, 'change_ly')), O('Revenue, change on the 3 months before', 'pct', CPM(1, 'change')),
    O('Revenue, change on last year', 'pct', CPM(1, 'change_ly')),
    O('Verdict', 'text', '%s&" "&%s&" "&ROUND({in:drop}*100,0)&"%%"' % (WORSE, vt('figures dropped over')))],
    GR('What if', ('Drop of 5%', {'drop': 0.05}), ('Drop of 15%', {'drop': 0.15}), ('Drop of 20%', {'drop': 0.20}), ('Drop of 30%', {'drop': 0.30}), ('Drop of 50%', {'drop': 0.50}))))

# 7 ------------------------------------------------------------ year-end summary and next-year plan
BIRTHS12 = T12('births'); REV12 = T12('revenue'); PROF12 = T12('profit')
RPBT = 'IFERROR(%s/%s,0)' % (REV12, BIRTHS12)
VARBT = 'IFERROR((%s+%s+%s)/%s,0)' % (T12('doula_pay'), T12('backup_pay'), T12('mileage'), BIRTHS12)
DID = '(%s/12)' % BIRTHS12
NEED = 'IFERROR(ROUNDUP({in:target}/(12*%s),1),0)' % RPBT
YR = lambda k, c: 'IFERROR(INDEX({range:yearrev.%s},MATCH(%d,{range:yearrev.no},0)),0)' % (c, k)
tools.append(TOOL('year_end', 'Year-End Summary and Plan', 'What did the year deliver and how many births a month do I need next year',
    'Type your income target and one more or one fewer birth a month: births, hours, income, profit and the best month and income stream of the last 12 months, then the births a month needed at your own revenue per birth; read from Profit and Loss and Year in Review.', [
    I('target', 'Income target for the year', 300000, 'money'), I('change', 'Births a month more or fewer', 1, 'int')], [
    O('Births, last 12 months', 'int', BIRTHS12), O('Births a month you did', 'num', DID), O('Visit hours, last 12 months', 'num', T12('visit_hours')), O('Revenue, last 12 months', 'money', REV12), O('Profit, last 12 months', 'money', PROF12),
    O('Revenue change on the 12 months before', 'pct', YR(1, 'change')), O('Profit change on the 12 months before', 'pct', YR(12, 'change')),
    O('Best income stream', 'text', 'IFERROR(INDEX({range:yearrev.measure},MATCH(MAX({range:yearrev.stream}),{range:yearrev.stream},0))&"","")'), O('Income of that stream', 'money', 'MAX({range:yearrev.stream})'),
    O('Best month for profit', 'date', 'INDEX({range:pnl.month},MATCH(MAX({range:pnl.profit12}),{range:pnl.profit12},0))'), O('Profit of that month', 'money', 'MAX({range:pnl.profit12})'),
    O('Revenue per birth', 'money', RPBT), O('Profit per birth', 'money', 'IFERROR(%s/%s,0)' % (PROF12, BIRTHS12)), O('Births a month needed for your target', 'num', NEED),
    O('Income with one more birth a month', 'money', 'ROUND((%s+{in:change})*12*%s,0)' % (DID, RPBT)), O('Income with one fewer birth a month', 'money', 'ROUND(MAX(0,%s-{in:change})*12*%s,0)' % (DID, RPBT)),
    O('Profit with one more birth a month', 'money', '%s+{in:change}*12*(%s-%s)' % (PROF12, RPBT, VARBT)), O('Profit with one fewer birth a month', 'money', '%s-{in:change}*12*(%s-%s)' % (PROF12, RPBT, VARBT)),
    O('Verdict', 'text', '%s&" "&%s&" "&%s&" "&ROUND(%s,1)' % (vt('You need'), NEED, vt('births a month, you did'), DID))],
    GR('What if', ('Target 250000', {'target': 250000}), ('Target 350000', {'target': 350000}), ('Target 400000', {'target': 400000}), ('Two births a month more', {'change': 2}), ('Three births a month more', {'change': 3}))))

# 8 ------------------------------------------------------------ cash runway
CIN3 = 'AVERAGEIFS({range:cash.cash_in},{range:cash.month},">="&EDATE(%s,-3),{range:cash.month},"<"&%s)' % (MS, MS)
VAR3 = '(%s+%s+%s)' % (A3('doula_pay'), A3('backup_pay'), A3('mileage'))
FIX3 = A3('fixed_costs')
NETF_ = '(%s*(1-{in:fall})-%s*(1-{in:fall})-%s-{in:draw})' % (CIN3, VAR3, FIX3)
BURN = 'MAX(0,-%s)' % NETF_
RUN = 'IF(%s>0,MIN(24,(%s-{in:floor})/%s),24)' % (BURN, CASHNOW, BURN)
tools.append(TOOL('runway', 'Cash Runway', 'How many months does the cash last if income falls',
    'Type the share by which income falls: cash in and costs of the last 3 months, with doula pay falling with income and fixed costs staying, and the months until cash reaches your floor (24 means more than 24); read from Cash by Month and Profit and Loss.', [
    I('fall', 'Fall in income', 0.50, 'pct'), I('draw', 'Owner draw per month', OWNER_DRAW, 'money'), I('floor', 'Lowest cash you accept', CASH_FLOOR, 'money')], [
    O('Cash now', 'money', CASHNOW), O('Cash in a month, last 3 months', 'money', CIN3), O('Cash in after the fall', 'money', '%s*(1-{in:fall})' % CIN3), O('Doula pay and mileage after the fall', 'money', '%s*(1-{in:fall})' % VAR3),
    O('Fixed costs a month', 'money', FIX3), O('Owner draw', 'money', '{in:draw}'), O('Cash change a month after the fall', 'money', NETF_), O('Cash used up a month', 'money', BURN),
    O('Months until the floor (24 = more than 24)', 'num', RUN), O('Months until cash is gone', 'num', 'IF(%s>0,MIN(24,%s/%s),24)' % (BURN, CASHNOW, BURN)),
    O('Fall in income that stops cash growing', 'pct', 'MAX(0,1-(%s+{in:draw})/(%s-%s))' % (FIX3, CIN3, VAR3)), O('Months of cover now (fixed costs and draw)', 'num', 'IFERROR(%s/(%s+{in:draw}),0)' % (CASHNOW, FIX3)),
    O('Unearned cash held now', 'money', 'SUM({range:contracts.unearned})'),
    O('Verdict', 'text', 'IF(%s>=2*{set:cash_cover_months},%s,IF(%s>={set:cash_cover_months},%s,%s))' % (RUN, vt('Comfortable'), RUN, vt('Watch'), vt('Act now')))],
    GR('What if', ('Income falls 20%', {'fall': 0.20}), ('Income falls 60%', {'fall': 0.60}), ('Income falls 80%', {'fall': 0.80}), ('Income falls 90%', {'fall': 0.90}), ('Income falls 100%', {'fall': 1.0}))))

# 9 ------------------------------------------------------------ budget variance ranker
def VC(f, k): return 'IFERROR(INDEX({range:expvar.category},MATCH(%s({range:expvar.v_last},%d),{range:expvar.v_last},0))&"","")' % (f, k)
tools.append(TOOL('ranker', 'Budget Variance Ranker', 'Which expense categories are furthest over budget',
    'Type the share over budget that you accept: the last full month ranked from the largest overspend, the most under budget and the 12-month variance of each; read from Budget vs Actual.', [
    I('tol', 'Spending over budget that you accept', 0.10, 'pct')], [
    O('Variance of all categories, last full month', 'money', 'SUM({range:expvar.v_last})'), O('Categories over budget', 'int', 'COUNTIFS({range:expvar.v_last},">0")'),
    O('Categories over the share you accept', 'int', 'COUNTIFS({range:expvar.v_last},">0",{range:expvar.over_share},">"&{in:tol})'),
    O('Largest overspend', 'text', VC('LARGE', 1)), O('Amount over budget', 'money', 'LARGE({range:expvar.v_last},1)'), O('Second overspend', 'text', VC('LARGE', 2)), O('Amount of the second', 'money', 'LARGE({range:expvar.v_last},2)'),
    O('Third overspend', 'text', VC('LARGE', 3)), O('Amount of the third', 'money', 'LARGE({range:expvar.v_last},3)'), O('Most under budget', 'text', VC('SMALL', 1)), O('Amount under budget', 'money', 'SMALL({range:expvar.v_last},1)'),
    O('Largest 12-month overspend', 'text', 'IFERROR(INDEX({range:expvar.category},MATCH(LARGE({range:expvar.v_year},1),{range:expvar.v_year},0))&"","")'), O('Amount of the 12-month overspend', 'money', 'LARGE({range:expvar.v_year},1)'),
    O('Months over budget in the last 12 months, all categories', 'int', 'COUNTIFS({range:expvar.within},0)'),
    O('Verdict', 'text', 'IF(LARGE({range:expvar.v_last},1)>0,%s&" "&%s,%s)' % (vt('Investigate'), VC('LARGE', 1), vt('No category is over budget')))],
    GR('What if', ('Accept 0%', {'tol': 0.0}), ('Accept 5%', {'tol': 0.05}), ('Accept 25%', {'tol': 0.25}), ('Accept 50%', {'tol': 0.5}), ('Accept 100%', {'tol': 1.0}))))

# 10 ----------------------------------------------------------- break-even births a month
MARG = '(%s*(1+{in:price})-%s)' % (RPBT, VARBT)
FIXY = '(%s+%s+12*{in:extra})' % (T12('admin_pay'), T12('other_costs'))
NEEDB = 'IFERROR(ROUNDUP((%s+12*{in:draw})/(12*%s),1),0)' % (FIXY, MARG)
tools.append(TOOL('breakeven', 'Break-Even Births a Month', 'How many births a month do I need to cover costs and my draw',
    'Type your draw, any extra fixed cost and a price change: the revenue and pay per birth of the last 12 months, the margin per birth and the births a month that cover fixed costs plus your draw (pay per birth stays the same); read from Profit and Loss.', [
    I('draw', 'Owner draw per month', OWNER_DRAW, 'money'), I('extra', 'Extra fixed cost per month', 0, 'money'), I('price', 'Price change on every birth', 0.0, 'pct')], [
    O('Births, last 12 months', 'int', BIRTHS12), O('Revenue per birth', 'money', 'ROUND(%s*(1+{in:price}),0)' % RPBT), O('Doula pay and mileage per birth', 'money', 'ROUND(%s,0)' % VARBT), O('Margin per birth', 'money', 'ROUND(%s,0)' % MARG),
    O('Fixed costs for a year (admin and other costs)', 'money', FIXY), O('Owner draw for a year', 'money', '12*{in:draw}'), O('Costs to cover for a year', 'money', '%s+12*{in:draw}' % FIXY),
    O('Births a year to break even', 'num', 'IFERROR(ROUNDUP((%s+12*{in:draw})/%s,0),0)' % (FIXY, MARG)), O('Births a month to break even', 'num', NEEDB), O('Births a month you did', 'num', 'ROUND(%s,1)' % DID),
    O('Room above break-even, births a month', 'num', 'ROUND(%s-%s,1)' % (DID, NEEDB)), O('Income at break-even', 'money', 'ROUND(%s*12*%s*(1+{in:price}),0)' % (NEEDB, RPBT)),
    O('Births a month to break even and set aside tax', 'num', 'IFERROR(ROUNDUP((%s+12*{in:draw})/(12*%s*(1-{set:tax_set_aside_pct})),1),0)' % (FIXY, MARG)),
    O('Verdict', 'text', '%s&" "&%s&" "&%s' % (vt('You need'), NEEDB, vt('births a month to break even')))],
    GR('What if', ('Price down 10%', {'price': -0.10}), ('Price up 5%', {'price': 0.05}), ('Price up 10%', {'price': 0.10}), ('Draw 5000', {'draw': 5000}), ('Extra fixed cost 500', {'extra': 500}))))

# 11 ----------------------------------------------------------- owner draw scenario
def FS(c, n='SMALL'): return '%s({range:forecast.%s},1)' % (n, c)
LOWUP, LOWAS, LOWDN = FS('closing_up'), FS('closing'), FS('closing_dn')
STEPD = 'ROUND({set:owner_draw}*{set:draw_step},0)'
tools.append(TOOL('draw_scenario', 'Owner Draw Scenario', 'What happens to cash if I take a lower or a higher draw',
    'Type your floor: the lowest cash month and the months below the floor with a draw of one step less, as it is and one step more (the step is in Settings); read from Cash Forecast.', [
    I('floor', 'Lowest cash you accept', CASH_FLOOR, 'money'), I('cover', 'Months of cover you want', CASH_COVER_MONTHS, 'int')], [
    O('Draw one step lower', 'money', '{set:owner_draw}-%s' % STEPD), O('Draw as it is', 'money', '{set:owner_draw}'), O('Draw one step higher', 'money', '{set:owner_draw}+%s' % STEPD),
    O('Lowest cash with the lower draw', 'money', LOWDN), O('Lowest cash as it is', 'money', LOWAS), O('Lowest cash with the higher draw', 'money', LOWUP),
    O('Months below the floor, lower draw', 'int', 'COUNTIFS({range:forecast.closing_dn},"<"&{in:floor})'), O('Months below the floor, as it is', 'int', 'COUNTIFS({range:forecast.closing},"<"&{in:floor})'),
    O('Months below the floor, higher draw', 'int', 'COUNTIFS({range:forecast.closing_up},"<"&{in:floor})'),
    O('Months of cover at the lowest cash, as it is', 'num', 'IFERROR(%s/%s,0)' % (LOWAS, FIXAV)), O('Months of cover at the lowest cash, higher draw', 'num', 'IFERROR(%s/%s,0)' % (LOWUP, FIXAV)),
    O('Highest draw that keeps the floor', 'money', 'IF(%s>={in:floor},{set:owner_draw}+%s,IF(%s>={in:floor},{set:owner_draw},IF(%s>={in:floor},{set:owner_draw}-%s,0)))' % (LOWUP, STEPD, LOWAS, LOWDN, STEPD)),
    O('Month of the lowest cash as it is', 'date', 'INDEX({range:forecast.month},MATCH(%s,{range:forecast.closing},0))' % LOWAS),
    O('Verdict', 'text', 'IF(AND(%s>={in:floor},IFERROR(%s/%s,0)>={in:cover}),%s,%s)' % (LOWAS, LOWAS, FIXAV, vt('Affordable'), vt('Not affordable')))],
    GR('What if', ('Floor 30000', {'floor': 30000}), ('Floor 36000', {'floor': 36000}), ('Floor 40000', {'floor': 40000}), ('Cover of 5 months', {'cover': 5}), ('Cover of 8 months', {'cover': 8}))))

# 12 ----------------------------------------------------------- tax set-aside check
YS = 'DATE(YEAR({today})-IF(MONTH({today})<{in:start},1,0),{in:start},1)'
PYTD = 'SUMIFS({range:pnl.profit},{range:pnl.month},">="&%s,{range:pnl.month},"<="&%s)' % (YS, MS)
NEXTT = 'SMALL({range:tax.planned_by},1)'
tools.append(TOOL('tax_check', 'Tax Set-Aside Check', 'Is my set-aside up to date and when is the next transfer',
    'Type the set-aside share and the first month of your tax year: the profit year to date, the set-aside due, what was moved and what is planned, and the next transfer date; confirm the share with your adviser; read from Tax Set-aside and Profit and Loss.', [
    I('pct', 'Set-aside share (confirm with your adviser)', TAX_SET_ASIDE_PCT, 'pct'), I('start', 'First month of your tax year (1 to 12)', 1, 'int')], [
    O('Profit, year to date', 'money', PYTD), O('Set-aside due at your share', 'money', 'ROUND(MAX(0,%s)*{in:pct},0)' % PYTD),
    O('Set-aside moved, year to date', 'money', 'SUMIFS({range:tax.set_aside},{range:tax.status},%s,{range:tax.month},">="&%s)' % (tok('taxstatus', 'Moved'), YS)),
    O('Set-aside planned, year to date', 'money', 'SUMIFS({range:tax.set_aside},{range:tax.status},%s,{range:tax.month},">="&%s)' % (tok('taxstatus', 'Planned'), YS)),
    O('Short or over the set-aside due', 'money', 'ROUND(SUMIFS({range:tax.set_aside},{range:tax.month},">="&%s)-MAX(0,%s)*{in:pct},0)' % (YS, PYTD)),
    O('Next transfer date', 'date', NEXTT), O('Days to the next transfer', 'int', '%s-{today}' % NEXTT), O('Amount to move by then', 'money', 'SUMIFS({range:tax.set_aside},{range:tax.planned_by},%s)' % NEXTT),
    O('Late transfers', 'int', 'SUM({range:tax.late})'), O('Transfers moved on time, all months', 'pct', 'IFERROR(SUM({range:tax.on_time})/SUM({range:tax.due_passed}),0)'),
    O('Set-aside of the current quarter', 'money', 'SUMIFS({range:tax.set_aside},{range:tax.month},">="&DATE(YEAR({today}),3*INT((MONTH({today})-1)/3)+1,1))'),
    O('Cash above the floor after the next transfer', 'money', '%s-{set:cash_floor}-%s' % (CASHNOW, STILL)),
    O('Verdict', 'text', 'IF(%s>0,%s&" "&%s&" "&%s&" "&%s&", "&%s,%s)' % ('SUMIFS({range:tax.set_aside},{range:tax.planned_by},%s)' % NEXTT, vt('Move'), NUM('SUMIFS({range:tax.set_aside},{range:tax.planned_by},%s)' % NEXTT), vt('by'), DMY(NEXTT), vt('confirm with your adviser'), vt('Nothing to move')))],
    GR('What if', ('Share 20%', {'pct': 0.20}), ('Share 30%', {'pct': 0.30}), ('Share 35%', {'pct': 0.35}), ('Tax year starts in April', {'start': 4}), ('Tax year starts in July', {'start': 7}))))

# 13 ----------------------------------------------------------- free cash this month
FREE = '(%s-%s-{in:payrun}-ROUND(AVERAGEIFS({range:cash.expenses_out},{range:cash.month},">="&EDATE(%s,-3),{range:cash.month},"<"&%s)*{in:days}/30,0))' % (CASHNOW, STILL, MS, MS)
tools.append(TOOL('free_cash', 'Free Cash This Month', 'How much cash is really free after set-aside, the pay run and costs',
    'Type the next pay run, the days of costs to keep and your draw: cash less the set-aside to move, the pay run and the days of expenses, then the draw and the floor; the unearned cash held is shown for comparison.', [
    I('payrun', 'Next pay run', D.CASH[-2]['pay_out'], 'money'), I('days', 'Days of costs to keep', 30, 'int'), I('draw', 'Owner draw this month', OWNER_DRAW, 'money')], [
    O('Cash now', 'money', CASHNOW), O('Set-aside still to move', 'money', STILL), O('Next pay run', 'money', '{in:payrun}'),
    O('Expenses for the days you keep', 'money', 'ROUND(AVERAGEIFS({range:cash.expenses_out},{range:cash.month},">="&EDATE(%s,-3),{range:cash.month},"<"&%s)*{in:days}/30,0)' % (MS, MS)),
    O('Free cash', 'money', FREE), O('Free cash after your draw', 'money', '%s-{in:draw}' % FREE), O('Free cash after the draw and above the floor', 'money', '%s-{in:draw}-{set:cash_floor}' % FREE),
    O('Instalments and balances expected next month', 'money', 'SUMIFS({range:forecast.scheduled_in},{range:forecast.ahead},1)'), O('Unearned cash held', 'money', 'SUM({range:contracts.unearned})'),
    O('Cash against unearned cash', 'pct', 'IFERROR(%s/SUM({range:contracts.unearned}),0)' % CASHNOW), O('Balances and instalments still to receive', 'money', 'SUM({range:contracts.owing})'),
    O('Instalments late now', 'money', 'SUMIFS({range:instalments.amount},{range:instalments.days_late},">0")'),
    O('Verdict', 'text', 'IF(%s>0,%s&" "&%s,%s)' % (FREE, vt('Free cash is'), NUM(FREE), vt('No free cash')))],
    GR('What if', ('Keep 14 days of costs', {'days': 14}), ('Keep 60 days of costs', {'days': 60}), ('Pay run 25000', {'payrun': 25000}), ('Pay run 35000', {'payrun': 35000}), ('Draw 6000', {'draw': 6000}))))

# 14 ----------------------------------------------------------- renewal and training cost plan
RCOST = 'SUMIFS({range:renewals.cost},%s,{range:renewals.due_date},">"&{today},{range:renewals.due_date},"<="&EDATE({today},{in:months}))' % OPEN_
TCOST = 'SUMIFS({range:training.cost},{range:training.date},">"&{today},{range:training.date},"<="&EDATE({today},{in:months}))'
def QC(a, b): return '(SUMIFS({range:renewals.cost},%s,{range:renewals.due_date},">"&EDATE({today},%d),{range:renewals.due_date},"<="&EDATE({today},%d))+SUMIFS({range:training.cost},{range:training.date},">"&EDATE({today},%d),{range:training.date},"<="&EDATE({today},%d)))' % (OPEN_, a, b, a, b)
tools.append(TOOL('cost_plan', 'Renewal and Training Costs', 'How much to set aside each month for renewals and training',
    'Type the months to plan: the renewal and training costs due, the quarter by quarter bill and the amount to set aside each month; read from Renewals and Training.', [
    I('months', 'Months to plan', 12, 'int')], [
    O('Renewal costs due', 'money', RCOST), O('Training costs planned', 'money', TCOST), O('Total to plan for', 'money', '%s+%s' % (RCOST, TCOST)), O('Set aside each month', 'money', 'ROUND((%s+%s)/{in:months},0)' % (RCOST, TCOST)),
    O('Next 3 months', 'money', QC(0, 3)), O('Months 4 to 6', 'money', QC(3, 6)), O('Months 7 to 9', 'money', QC(6, 9)), O('Months 10 to 12', 'money', QC(9, 12)),
    O('Renewals due in the months you plan', 'int', 'COUNTIFS(%s,{range:renewals.due_date},">"&{today},{range:renewals.due_date},"<="&EDATE({today},{in:months}))' % OPEN_),
    O('Biggest open renewal cost', 'money', 'SUMPRODUCT(MAX(({range:renewals.is_open}=1)*{range:renewals.cost}))'),
    O('Liability insurance cost in the months you plan', 'money', 'SUMIFS({range:renewals.cost},%s,{range:renewals.item},%s,{range:renewals.due_date},"<="&EDATE({today},{in:months}))' % (OPEN_, tok('renewal', 'Liability insurance'))),
    O('Training hours planned', 'num', 'SUMIFS({range:training.hours},{range:training.date},">"&{today},{range:training.date},"<="&EDATE({today},{in:months}))'),
    O('Verdict', 'text', '%s&" "&ROUND((%s+%s)/{in:months},0)&" "&%s' % (vt('Set aside'), RCOST, TCOST, vt('a month')))],
    GR('What if', ('Plan 3 months', {'months': 3}), ('Plan 6 months', {'months': 6}), ('Plan 9 months', {'months': 9}), ('Plan 18 months', {'months': 18}), ('Plan 24 months', {'months': 24}))))

# 15 ----------------------------------------------------------- time-off cash test
WKREV = '(%s/52)' % T12('revenue')
VSH = 'IFERROR((%s+%s+%s)/%s,0)' % (T12('doula_pay'), T12('backup_pay'), T12('mileage'), T12('revenue'))
HIT = 'ROUND({in:weeks}*%s*{in:stop}*(1-%s),0)' % (WKREV, VSH)
FIXM = 'ROUND(AVERAGEIFS({range:pnl.fixed_costs},{range:pnl.month},">="&EDATE(%s,-6),{range:pnl.month},"<"&%s),0)' % (MS, MS)
COVA = 'IFERROR((%s-%s)/(%s+{in:draw}),0)' % (CASHNOW, HIT, FIXM)
tools.append(TOOL('timeoff', 'Time-Off Cash Test', 'Can I afford weeks without new births attended',
    'Type the weeks off, the share of income that stops and your draw: the income lost, the pay saved, the cash left and the months of cover that fixed costs and your draw still need; read from Profit and Loss and Cash by Month.', [
    I('weeks', 'Weeks without new births attended', 4, 'int'), I('stop', 'Share of income that stops', 0.35, 'pct'), I('draw', 'Owner draw per month', OWNER_DRAW, 'money')], [
    O('Average revenue a week', 'money', 'ROUND(%s,0)' % WKREV), O('Income lost', 'money', 'ROUND({in:weeks}*%s*{in:stop},0)' % WKREV), O('Doula pay and mileage saved', 'money', 'ROUND({in:weeks}*%s*{in:stop}*%s,0)' % (WKREV, VSH)),
    O('Cash lost by the time off', 'money', HIT), O('Fixed costs that continue a month', 'money', FIXM), O('Fixed costs and draw for the time off', 'money', 'ROUND(({in:weeks}/52*12)*(%s+{in:draw}),0)' % FIXM),
    O('Cash now', 'money', CASHNOW), O('Cash after the time off', 'money', '%s-%s' % (CASHNOW, HIT)), O('Cash above the floor after the time off', 'money', '%s-%s-{set:cash_floor}' % (CASHNOW, HIT)),
    O('Months of cover after the time off', 'num', COVA), O('Months of cover you want', 'int', '{set:cash_cover_months}'), O('Longest time off that keeps the cover, weeks', 'num', 'IFERROR(MAX(0,(%s-{set:cash_cover_months}*(%s+{in:draw}))/(%s*{in:stop}*(1-%s))),0)' % (CASHNOW, FIXM, WKREV, VSH)),
    O('Unearned cash held', 'money', 'SUM({range:contracts.unearned})'),
    O('Verdict', 'text', 'IF(%s>={set:cash_cover_months},%s&" "&ROUND(%s,1)&" "&%s,%s)' % (COVA, vt('Affordable with'), COVA, vt('months of cover'), vt('Plan more cash')))],
    GR('What if', ('2 weeks off', {'weeks': 2}), ('8 weeks off', {'weeks': 8}), ('12 weeks off', {'weeks': 12}), ('All income stops, 8 weeks', {'weeks': 8, 'stop': 1.0}), ('All income stops, 20 weeks', {'weeks': 20, 'stop': 1.0}))))

# 16 ----------------------------------------------------------- seasonal cash cushion
DR1, DR2, DR3 = ['LARGE({range:cash.drop},%d)' % i for i in (1, 2, 3)]
CUSH = '(%s+IF({in:dips}>=2,%s,0)+IF({in:dips}>=3,%s,0))' % (DR1, DR2, DR3)
tools.append(TOOL('cushion', 'Seasonal Cash Cushion', 'How much cash should I keep aside for a quiet stretch',
    'Type how many of the biggest monthly falls in cash to plan for (1 to 3): the lowest and highest cash of the last 24 months, the biggest falls and the cushion to keep above your floor; read from Cash by Month.', [
    I('dips', 'Biggest monthly falls to plan for (1 to 3)', 2, 'int'), I('floor', 'Lowest cash you accept', CASH_FLOOR, 'money')], [
    O('Lowest closing cash, 24 months', 'money', 'SMALL({range:cash.closing},1)'), O('Month of the lowest cash', 'date', 'INDEX({range:cash.month},MATCH(SMALL({range:cash.closing},1),{range:cash.closing},0))'),
    O('Highest closing cash, 24 months', 'money', 'LARGE({range:cash.closing},1)'), O('Swing between the highest and the lowest', 'money', 'LARGE({range:cash.closing},1)-SMALL({range:cash.closing},1)'),
    O('Biggest fall in one month', 'money', DR1), O('Month of the biggest fall', 'date', 'INDEX({range:cash.month},MATCH(%s,{range:cash.drop},0))' % DR1), O('Second biggest fall', 'money', DR2), O('Third biggest fall', 'money', DR3),
    O('Cushion to keep above the floor', 'money', CUSH), O('Cash needed to ride out that dip', 'money', '{in:floor}+%s' % CUSH), O('Cash now', 'money', CASHNOW),
    O('Cash above the floor now', 'money', '%s-{in:floor}' % CASHNOW), O('Short of the cushion', 'money', 'MAX(0,%s-(%s-{in:floor}))' % (CUSH, CASHNOW)),
    O('Lowest cash if the dip happened now', 'money', '%s-%s' % (CASHNOW, CUSH)),
    O('Verdict', 'text', '%s&" "&%s&" "&%s' % (vt('Keep'), NUM(CUSH), vt('aside')))],
    GR('What if', ('Plan for 1 fall', {'dips': 1}), ('Plan for 3 falls', {'dips': 3}), ('Floor 20000', {'floor': 20000}), ('Floor 25000', {'floor': 25000}), ('Floor 10000', {'floor': 10000}))))

# 17 ----------------------------------------------------------- fixed cost review
FIX12 = '(%s+%s)' % (T12('admin_pay'), T12('other_costs'))
ADM12 = T12('admin_pay')
TOPC = 'LARGE({range:expvar.amt_year},1)'
tools.append(TOOL('fixed_costs', 'Fixed Cost Review', 'Are my fixed costs too high for my revenue',
    'Type the highest share of revenue you accept for fixed costs (admin pay and all overheads): the share of revenue, the cost per birth, admin pay and the largest expense category; read from Profit and Loss and Budget vs Actual.', [
    I('limit', 'Highest fixed costs as a share of revenue', 0.15, 'pct')], [
    O('Fixed costs, last 12 months', 'money', FIX12), O('Share of revenue', 'pct', 'IFERROR(%s/%s,0)' % (FIX12, REV12)), O('Fixed costs per birth', 'money', 'IFERROR(%s/%s,0)' % (FIX12, BIRTHS12)), O('Fixed costs a month', 'money', '%s/12' % FIX12),
    O('Admin pay, last 12 months', 'money', ADM12), O('Admin pay share of revenue', 'pct', 'IFERROR(%s/%s,0)' % (ADM12, REV12)),
    O('Largest expense category', 'text', 'IFERROR(INDEX({range:expvar.category},MATCH(%s,{range:expvar.amt_year},0))&"","")' % TOPC), O('Spending of that category', 'money', TOPC),
    O('Insurance, last 12 months', 'money', 'SUMIFS({range:expvar.amount},{range:expvar.category},%s)' % tok('expcat', 'Insurance')),
    O('Phone and software, last 12 months', 'money', 'SUMIFS({range:expvar.amount},{range:expvar.category},%s)' % tok('expcat', 'Phone and software')),
    O('Accounting, last 12 months', 'money', 'SUMIFS({range:expvar.amount},{range:expvar.category},%s)' % tok('expcat', 'Accounting')),
    O('Fixed costs above your limit', 'money', 'MAX(0,%s-{in:limit}*%s)' % (FIX12, REV12)), O('Revenue needed to keep fixed costs at your limit', 'money', 'IFERROR(%s/{in:limit},0)' % FIX12),
    O('Verdict', 'text', '%s&" "&ROUND(IFERROR(%s/%s,0)*100,0)&"%% "&%s&", "&%s&" "&IF(%s>%s,{list:role.admin},IFERROR(INDEX({range:expvar.category},MATCH(%s,{range:expvar.amt_year},0))&""))' % (vt('Fixed costs are'), FIX12, REV12, vt('of revenue'), vt('review'), ADM12, TOPC, TOPC))],
    GR('What if', ('Limit 10%', {'limit': 0.10}), ('Limit 12%', {'limit': 0.12}), ('Limit 18%', {'limit': 0.18}), ('Limit 20%', {'limit': 0.20}), ('Limit 25%', {'limit': 0.25}))))

# 18 ----------------------------------------------------------- accountant pack check
PER = '{range:pnl.month},">"&EDATE(%s,-{in:months}),{range:pnl.month},"<="&%s' % (MS, MS)
EPER = '{range:expenses.month},">"&EDATE(%s,-{in:months}),{range:expenses.month},"<="&%s' % (MS, MS)
CPER = '{range:cash.month},">"&EDATE(%s,-{in:months}),{range:cash.month},"<="&%s' % (MS, MS)
D1 = 'ROUND(SUMIFS({range:pnl.other_costs},%s)-SUMIFS({range:expenses.amount},%s),0)' % (PER, EPER)
D2 = 'ROUND(SUMIFS({range:cash.expenses_out},%s)-SUMIFS({range:expenses.amount},%s),0)' % (CPER, EPER)
D3 = 'ROUND(SUM({range:cash.set_aside})-SUMIFS({range:tax.set_aside},{range:tax.status},%s),0)' % tok('taxstatus', 'Moved')
D4 = 'SUMIFS({range:cash.roll_diff},%s)' % CPER
TOT = 'ABS(%s)+ABS(%s)+ABS(%s)+ABS(%s)' % (D1, D2, D3, D4)
tools.append(TOOL('pack_check', 'Accountant Pack Check', 'Do the totals in my accountant pack agree with each other',
    'Type the months to check: profit, cash and expenses totals set against the source sheets (other costs against Expenses, expenses paid in cash against Expenses, set-aside moved against Tax Set-aside, and the cash roll-forward); a difference is shown before you send the pack.', [
    I('months', 'Months to check', 12, 'int'), I('tol', 'Difference that counts as balanced', 1, 'money')], [
    O('Revenue, months checked', 'money', 'SUMIFS({range:pnl.revenue},%s)' % PER), O('Profit, months checked', 'money', 'SUMIFS({range:pnl.profit},%s)' % PER), O('Cash in, months checked', 'money', 'SUMIFS({range:cash.cash_in},%s)' % CPER),
    O('Closing cash, last month', 'money', CASHNOW), O('Expenses on the Expenses sheet', 'money', 'SUMIFS({range:expenses.amount},%s)' % EPER), O('Other costs on Profit and Loss', 'money', 'SUMIFS({range:pnl.other_costs},%s)' % PER),
    O('Difference: other costs against Expenses', 'money', D1), O('Difference: expenses paid in cash against Expenses', 'money', D2), O('Difference: set-aside moved against Tax Set-aside', 'money', D3),
    O('Difference: cash roll-forward', 'money', D4), O('Total of the differences', 'money', TOT), O('Months that do not roll forward', 'int', 'COUNTIFS({range:cash.roll_diff},"<>0",%s)' % CPER),
    O('Verdict', 'text', 'IF(%s<={in:tol},%s,%s&" "&(%s))' % (TOT, vt('Pack balances'), vt('Pack differs by'), TOT))],
    GR('What if', ('Check 6 months', {'months': 6}), ('Check 3 months', {'months': 3}), ('Check 18 months', {'months': 18}), ('Check 24 months', {'months': 24}), ('Accept a difference of 50', {'tol': 50}))))
assert len(tools) == 18, len(tools)
