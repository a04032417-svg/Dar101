"""Car rental suite part 8: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr8_lists import *
import cr8_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def R(t, c): return '{range:%s.%s}' % (t, c)
YES = '{list:yesno.yes}'
SOLD = tok('vstatus', 'Sold'); REPAIRS = tok('expcat', 'Maintenance and repairs')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def WIN(t, n, col='month'): return '%s,">="&EDATE(%s,-%s),%s,"<"&%s' % (R(t, col), MS, n, R(t, col), MS)
def PS(col, n, t='pnl'): return 'SUMIFS(%s,%s)' % (R(t, col), WIN(t, n))
def A3(col): return 'AVERAGEIFS(%s,%s)' % (R('pnl', col), WIN('pnl', 3))
CASH_NOW = 'INDEX(%s,MATCH(%s,%s,0))' % (R('cash', 'closing'), MS, R('cash', 'month'))
KNOWN = 'SUM(%s)' % R('known_costs', 'amount')
def VLk(col): return 'IFERROR(INDEX(%s,MATCH({in:veh},%s,0)),0)' % (R('vehicles', col), R('vehicles', 'vehicle'))
def PCT(x): return 'ROUND((%s)*100,1)&"%%"' % x
def NUM(x, n=0): return 'ROUND(%s,%d)' % (x, n)
LOWV = ST = D.ST['low_vehicle_name']
tools = []
_w = [r for r in D.PNL if iso(month_start(12)) <= r['month'] < iso(month_start(0))]
FEE_D = round(sum(r['channel_fees'] for r in _w) / sum(r['revenue'] for r in _w), 3)
FUEL_D = round(sum(r['fuel_charging'] for r in _w) / sum(r['rented_days'] for r in _w), 2)
MAINT_D = round(sum(r['maintenance'] for r in _w) / sum(r['vehicles'] for r in _w))
OVH_D = round(sum(r['staff'] + r['overhead'] for r in _w) / sum(r['vehicles'] for r in _w) * 0.5)
LOWROW = D.replace_d()[0]

# 1 ------------------------------------------------------------ replace-or-sell tool
AGE, MIL, RES, BAL = VLk('age_months'), VLk('odometer'), VLk('resale_estimate'), VLk('loan_balance')
PRICE, BOOK, RATE, INS = VLk('purchase_price'), VLk('book_value'), VLk('loan_rate'), VLk('insurance_year')
VID = 'IFERROR(INDEX(%s,MATCH({in:veh},%s,0)),"")' % (R('vehicles', 'vehicle_id'), R('vehicles', 'vehicle'))
REP1 = 'IF({in:repair}>0,{in:repair},SUMIFS(%s,%s,%s,%s,%s,%s,">="&({today}-365)))' % (R('expenses', 'amount'), R('expenses', 'vehicle_id'), VID, R('expenses', 'category'), REPAIRS, R('expenses', 'date'))
PRF = 'IFERROR(INDEX(%s,MATCH({in:veh},%s,0)),0)' % (R('replace_in', 'profit_12m'), R('replace_in', 'vehicle'))
KEEP1 = '(%s+MIN(%s*{set:dep_pct}*12,MAX(0,%s-%s*{set:dep_floor}))+%s*%s+%s)' % (REP1, PRICE, BOOK, PRICE, BAL, RATE, INS)
REPL1 = '({in:new_cost}*{set:dep_pct}*12+{in:new_cost}*0.8*{set:new_loan_rate}+%s+{set:repair_new}+%s*{set:sell_cost_pct})' % (INS, RES)
tools.append(TOOL('replace_sell', 'Replace-or-Sell Tool', 'Keep, sell this season or replace',
    'Type a vehicle and the cost of a new one: cost per day of keeping one more year against replacing, with age, miles, equity and 12-month profit. Your depreciation and replacement settings apply.', [
    I('veh', 'Vehicle', LOWV, 'text'), I('new_cost', 'New vehicle cost', LOWROW['new_cost']), I('repair', 'Repair cost, last 12 months (0 = use your expenses)', 0)], [
    O('Age in months', 'int', AGE), O('Miles on the odometer', 'int', MIL), O('Resale estimate', 'money', RES), O('Financing balance', 'money', BAL), O('Equity (resale minus balance)', 'money', '%s-%s' % (RES, BAL)),
    O('Repair cost, last 12 months', 'money', REP1), O('Profit, last 12 months', 'money', PRF), O('Monthly profit or loss of this vehicle', 'money', '%s/12' % PRF),
    O('Cost of keeping one more year', 'money', KEEP1), O('Cost of replacing, first year', 'money', REPL1), O('Keep cost a day', 'money', '%s/365' % KEEP1), O('Replace cost a day', 'money', '%s/365' % REPL1),
    O('Keep minus replace, a day', 'money', '(%s-%s)/365' % (KEEP1, REPL1)),
    O('Verdict', 'text', 'IF(%s<0,%s,IF(AND(%s>%s,OR(%s>={set:replace_months},%s>={set:replace_miles})),%s,%s))' % (PRF, va('Sell this season'), KEEP1, REPL1, AGE, MIL, va('Replace'), va('Keep')))],
    GR('What if', ('New vehicle 36,000', {'new_cost': 36000, 'repair': 900}), ('New vehicle 44,000', {'new_cost': 44000, 'repair': 900}), ('Repair cost 3,000', {'repair': 3000}), ('Repair cost 8,000', {'repair': 8000}), ('Cheaper new vehicle and repairs 1,500', {'new_cost': 33000, 'repair': 1500}))))

# 2 ------------------------------------------------------------ best month to sell
REVM = 'IFERROR(INDEX(%s,MATCH({in:veh},%s,0))/12,0)' % (R('replace_in', 'rev_12m'), R('replace_in', 'vehicle'))
COSTM = '(%s-%s/12)' % (REVM, PRF)
def G(k): return '(%s*SUMIFS(%s,%s,EDATE(%s,%d))-%s-%s*(1-{in:decay})^%d*{in:decay})' % (REVM, R('pnl', 'season_index'), R('pnl', 'month'), MS, k - 12, COSTM, RES, k - 1)
STOP = 'IF(%s<=0,0,IF(%s<=0,1,IF(%s<=0,2,IF(%s<=0,3,IF(%s<=0,4,IF(%s<=0,5,6))))))' % tuple(G(k) for k in range(1, 7))
tools.append(TOOL('best_sell', 'Best Month to Sell', 'Sell now or hold for the season',
    'The resale value lost each month against the revenue still earned in that season (last year\'s shape) less the monthly cost; the first month that loses money is the month to sell.', [
    I('veh', 'Vehicle', LOWV, 'text'), I('decay', 'Resale value lost each month, share', 0.012, 'pct')], [
    O('Resale estimate', 'money', RES), O('Revenue a month, last 12 months', 'money', REVM), O('Cost a month, last 12 months', 'money', COSTM),
    O('Result of holding month 1', 'money', G(1)), O('Result of holding month 2', 'money', G(2)), O('Result of holding month 3', 'money', G(3)), O('Result of holding month 4', 'money', G(4)),
    O('Result of holding month 5', 'money', G(5)), O('Result of holding month 6', 'money', G(6)), O('Months worth holding', 'int', STOP), O('Month to sell', 'date', 'EDATE(%s,%s)' % (MS, STOP)),
    O('Verdict', 'text', 'CHOOSE(%s+1,%s,%s,%s,%s,%s,%s,%s)' % (STOP, va('Sell now'), va('Keep until'), va('Keep until'), va('Keep until'), va('Keep until'), va('Keep until'), va('Keep')))],
    GR('What if', ('Economy 01 Silver', {'veh': '=INDEX({range:vehicles.vehicle},2)'}), ('Compact 01 Blue', {'veh': '=INDEX({range:vehicles.vehicle},3)'}), ('Midsize SUV 01 Black', {'veh': '=INDEX({range:vehicles.vehicle},5)'}), ('Resale loses 3% a month', {'decay': 0.03}))))

# 3 ------------------------------------------------------------ financing and loan view
PAYS = 'SUMIFS(%s,%s,"<>"&%s)' % (R('vehicles', 'monthly_payment'), R('vehicles', 'status'), SOLD)
REVQ = '(%s/3)' % PS('revenue', 3)
FSH = '(%s/%s)' % (PAYS, REVQ)
CMON = '(%s/%s)' % (CASH_NOW, PAYS)
tools.append(TOOL('loan_tool', 'Financing and Loan View', 'How heavy are the loan payments',
    'Monthly payments, balance, equity and the share of revenue the payments take, with the months of payments your cash covers and the car with the least equity.', [
    I('limit', 'Most financing payments you accept, share of revenue', 0.20, 'pct'), I('target', 'Months of payments your cash should cover', 3, 'int')], [
    O('Financed cars in the fleet', 'int', 'COUNTIFS(%s,%s,%s,"<>"&%s)' % (R('vehicles', 'financed'), YES, R('vehicles', 'status'), SOLD)), O('Monthly financing payments', 'money', PAYS), O('Loan balance', 'money', 'SUM(%s)' % R('vehicles', 'loan_balance')),
    O('Resale estimate of the financed cars', 'money', 'SUM(%s)' % R('loan_view', 'resale')), O('Equity in financed cars', 'money', 'SUM(%s)' % R('loan_view', 'equity')),
    O('Revenue a month, last 3 months', 'money', REVQ), O('Financing share of revenue', 'pct', FSH), O('Cash now', 'money', CASH_NOW), O('Months of payments covered by cash', 'num', CMON),
    O('Car with the least equity', 'text', 'INDEX(%s,MATCH(SMALL(%s,1),%s,0))' % (R('loan_view', 'vehicle'), R('loan_view', 'equity'), R('loan_view', 'equity'))), O('Its equity', 'money', 'SMALL(%s,1)' % R('loan_view', 'equity')),
    O('Cars with equity under 10% of resale', 'int', 'COUNTIFS(%s,"<0.1")' % R('loan_view', 'equity_share')), O('Against your limit', 'text', 'IF(%s<={in:limit},%s,%s)' % (FSH, vb('On target'), vb('Over your limit'))),
    O('Verdict', 'text', '%s&" "&%s&", "&ROUND(%s,1)&" "&%s' % (vb('Financing share'), PCT(FSH), CMON, vb('months covered')))],
    GR('What if', ('Limit 15%', {'limit': 0.15}), ('Limit 25%', {'limit': 0.25}), ('Cover 6 months', {'target': 6}), ('Limit 30%', {'limit': 0.30}))))

# 4 ------------------------------------------------------------ refinance check
NOW4 = 'NPER({in:rate}/12,-{in:payment},{in:balance})'
NP4 = '(-PMT({in:new_rate}/12,{in:new_term},{in:balance}))'
SAV4 = '({in:payment}*%s-{in:balance}-(%s*{in:new_term}-{in:balance}+{in:fee}))' % (NOW4, NP4)
tools.append(TOOL('refinance', 'Refinance Check', 'Refinance a loan or keep it',
    'A new rate and term against the loan left: the monthly saving, the interest saved after any fee and the months it takes to earn the fee back. Check the terms with your lender.', [
    I('balance', 'Loan balance', 19462), I('rate', 'Loan rate now', 0.0744, 'pct'), I('payment', 'Monthly payment now', 620.29), I('new_rate', 'New rate offered', 0.0599, 'pct'),
    I('new_term', 'New term, months', 36, 'int'), I('fee', 'Fee to refinance', 250)], [
    O('Months left on the loan now', 'num', NOW4), O('Interest left to pay now', 'money', '{in:payment}*%s-{in:balance}' % NOW4), O('New monthly payment', 'money', NP4),
    O('Monthly saving', 'money', '{in:payment}-%s' % NP4), O('Interest on the new loan plus the fee', 'money', '%s*{in:new_term}-{in:balance}+{in:fee}' % NP4), O('Total saved after the fee', 'money', SAV4),
    O('Months to earn the fee back', 'num', 'IF({in:payment}-%s>0,{in:fee}/({in:payment}-%s),0)' % (NP4, NP4)),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (SAV4, va('Refinance'), va('Keep the loan')))],
    GR('What if', ('New rate 5%', {'new_rate': 0.05}), ('New rate 7%', {'new_rate': 0.07}), ('New term 48 months', {'new_term': 48}), ('New term 60 months', {'new_term': 60}), ('Fee 800', {'fee': 800}))))

# 5 ------------------------------------------------------------ early payoff test
BAL5 = VLk('loan_balance'); RT5 = VLk('loan_rate'); PM5 = VLk('monthly_payment')
EX5 = 'MIN({in:extra},%s)' % BAL5
N5 = 'IFERROR(NPER(%s/12,-%s,%s),0)' % (RT5, PM5, BAL5)
N5B = 'IFERROR(NPER(%s/12,-%s,%s-%s),0)' % (RT5, PM5, BAL5, EX5)
SAV5 = '(%s*%s-%s-(%s*%s-(%s-%s)))' % (PM5, N5, BAL5, PM5, N5B, BAL5, EX5)
CAF5 = '(%s-%s-%s)' % (CASH_NOW, KNOWN, EX5)
tools.append(TOOL('early_payoff', 'Early Payoff Test', 'Pay down a loan early or keep the cash',
    'An extra payment on one car\'s loan against the interest it saves and the cash floor, after the next 30 days of known costs.', [
    I('veh', 'Vehicle', 'Premium 03 Blue', 'text'), I('extra', 'Extra payment', 3000)], [
    O('Loan balance', 'money', BAL5), O('Loan rate', 'pct', RT5), O('Monthly payment', 'money', PM5), O('Months left now', 'num', N5), O('Months left after the extra payment', 'num', N5B),
    O('Interest left to pay now', 'money', '%s*%s-%s' % (PM5, N5, BAL5)), O('Interest saved', 'money', SAV5), O('Cash now', 'money', CASH_NOW), O('Known costs, next 30 days', 'money', KNOWN),
    O('Cash after known costs and the extra payment', 'money', CAF5), O('Cash floor', 'money', '{set:cash_floor}'), O('Room above the floor', 'money', '%s-{set:cash_floor}' % CAF5),
    O('Verdict', 'text', 'IF(AND(%s>0,%s>={set:cash_floor}),%s&" "&{in:veh},%s)' % (SAV5, CAF5, va('Pay off'), va('Keep the cash')))],
    GR('What if', ('Extra payment 1,000', {'extra': 1000}), ('Extra payment 2,000', {'extra': 2000}), ('Extra payment 5,000', {'extra': 5000}), ('Extra payment 10,000', {'extra': 10000}))))

# 6 ------------------------------------------------------------ profit and loss by class
def CMS(col, extra=''): return 'SUMIFS(%s,%s,{in:cls},%s>="&EDATE(%s,-{in:months}),%s,"<"&%s)' % (R('class_month', col), R('class_month', 'class'), R('class_month', 'month') + ',"', MS, R('class_month', 'month'), MS)
def CMT(col): return 'SUMIFS(%s,%s,">="&EDATE(%s,-{in:months}),%s,"<"&%s)' % (R('class_month', col), R('class_month', 'month'), MS, R('class_month', 'month'), MS)
def PNN(col): return 'SUMIFS(%s,%s,">="&EDATE(%s,-{in:months}),%s,"<"&%s)' % (R('pnl', col), R('pnl', 'month'), MS, R('pnl', 'month'), MS)
REV6, COST6 = CMS('revenue'), CMS('costs')
SHR6 = '(%s/%s)' % (REV6, CMT('revenue'))
OVH6 = '(%s*(%s+%s))' % (SHR6, PNN('staff'), PNN('overhead'))
PAF6 = '(%s-%s-%s)' % (REV6, COST6, OVH6)
MRG6 = 'IFERROR(%s/%s,0)' % (PAF6, REV6)
LOWN = 'INDEX(%s,MATCH(MIN(%s),%s,0))' % (R('class_month', 'class'), R('class_month', 'margin12'), R('class_month', 'margin12'))
tools.append(TOOL('class_pl', 'Profit and Loss by Class', 'Which class earns the most and which the least',
    'Pick a class and a number of months: revenue, vehicle costs, a share of staff and overhead by revenue, profit and margin, with the class that earns the lowest margin in the last 12 months.', [
    IN('cls', 'Class', 'list', key('class', 'Premium'), list='class'), I('months', 'Months back', 12, 'int')], [
    O('Revenue of the class', 'money', REV6), O('Vehicle costs of the class', 'money', COST6), O('Profit before staff and overhead', 'money', '%s-%s' % (REV6, COST6)), O('Share of all revenue', 'pct', SHR6),
    O('Share of staff and overhead', 'money', OVH6), O('Profit after staff and overhead', 'money', PAF6), O('Margin after staff and overhead', 'pct', MRG6),
    O('Vehicles in the class now', 'int', 'COUNTIFS(%s,{in:cls},%s,"<>"&%s)' % (R('vehicles', 'class'), R('vehicles', 'status'), SOLD)),
    O('Profit per vehicle', 'money', 'IFERROR(%s/COUNTIFS(%s,{in:cls},%s,"<>"&%s),0)' % (PAF6, R('vehicles', 'class'), R('vehicles', 'status'), SOLD)),
    O('Lowest class margin, 12 months, before staff', 'pct', 'MIN(%s)' % R('class_month', 'margin12')), O('Class with the lowest margin', 'text', LOWN),
    O('Verdict', 'text', '{in:cls}&" "&%s&" "&%s&", "&%s&" "&%s' % (vb('earns'), PCT(MRG6), vb('lowest margin is'), LOWN))],
    GR('What if', ('Last 3 months', {'months': 3}), ('Last 6 months', {'months': 6}), ('Last 12 months', {'months': 12}), ('Last 18 months', {'months': 18}))))

# 7 ------------------------------------------------------------ owner draw and tax set-aside
PRL = 'SUMIFS(%s,%s,EDATE(%s,-1))' % (R('pnl', 'profit'), R('pnl', 'month'), MS)
CAK = '(%s-%s-{in:other})' % (CASH_NOW, KNOWN)
ROOM7 = '(%s-{set:cash_floor})' % CAK
tools.append(TOOL('draw_tool', 'Owner Draw and Tax Set-Aside', 'Is it safe to draw this month',
    'Profit after the tax set-aside, cash after the next 30 days of known costs and the cash floor give the draw that is safe now. Confirm the set-aside with your adviser.', [
    I('planned', 'Draw you plan', D.OWNER_DRAW), I('other', 'Other cost you expect, not on the Known Costs sheet', 0)], [
    O('Profit last month', 'money', PRL), O('Tax set-aside on it (confirm with your adviser)', 'money', 'MAX(0,%s)*{set:tax_pct}' % PRL), O('Profit after the set-aside', 'money', '%s-MAX(0,%s)*{set:tax_pct}' % (PRL, PRL)),
    O('Profit last 12 months after the set-aside', 'money', '%s-%s*{set:tax_pct}' % (PS('profit', 12), 'SUMIFS(%s,%s,">0",%s)' % (R('tax', 'profit'), R('tax', 'profit'), WIN('tax', 12)))),
    O('Cash now', 'money', CASH_NOW), O('Known costs, next 30 days', 'money', KNOWN), O('Cash after known costs', 'money', CAK), O('Cash floor', 'money', '{set:cash_floor}'), O('Room above the floor', 'money', ROOM7),
    O('Safe draw', 'money', 'MAX(0,MIN({in:planned},%s))' % ROOM7), O('Draw this month so far', 'money', 'SUMIFS(%s,%s,%s)' % (R('draw', 'total'), R('draw', 'month'), MS)),
    O('Planned draw as a share of monthly profit after set-aside', 'pct', 'IFERROR({in:planned}/((%s-SUMIFS(%s,%s,">0",%s)*{set:tax_pct})/12),0)' % (PS('profit', 12), R('tax', 'profit'), R('tax', 'profit'), WIN('tax', 12))),
    O('Verdict', 'text', 'IF(%s>={in:planned},%s&" "&ROUND({in:planned},0),%s&" "&ROUND(MAX(0,%s),0))' % (ROOM7, vb('Safe to draw'), vb('Draw less, safe amount is'), ROOM7))],
    GR('What if', ('Draw 2,000', {'planned': 2000, 'other': 500}), ('Draw 3,000', {'planned': 3000, 'other': 500}), ('Draw 8,500 with the quarterly extra', {'planned': 8500, 'other': 500}), ('Extra cost 2,000 expected', {'other': 2000}))))

# 8 ------------------------------------------------------------ tax set-aside tracker
SA12 = 'SUMIFS(%s,%s)' % (R('tax', 'set_aside'), WIN('tax', 12)); NEED12 = 'SUMIFS(%s,%s)' % (R('tax', 'needed'), WIN('tax', 12))
BALT = '(SUM(%s)-SUM(%s))' % (R('tax', 'set_aside'), R('tax', 'paid_to_tax'))
tools.append(TOOL('tax_tracker', 'Tax Set-Aside Tracker', 'Is the tax set-aside on track',
    'The set-aside held against the profit of the last 12 months and the next quarterly payment you expect. Income tax set-aside: confirm with your adviser.', [
    I('payment', 'Next quarterly payment you expect', 4000)], [
    O('Profit, last 12 months', 'money', PS('profit', 12)), O('Profit of the months that made a profit', 'money', 'SUMIFS(%s,%s,">0",%s)' % (R('tax', 'profit'), R('tax', 'profit'), WIN('tax', 12))),
    O('Set-aside needed at your setting', 'money', NEED12), O('Set aside, last 12 months', 'money', SA12), O('Paid to tax, last 12 months', 'money', 'SUMIFS(%s,%s)' % (R('tax', 'paid_to_tax'), WIN('tax', 12))),
    O('Balance held now', 'money', BALT), O('Balance after the next payment', 'money', '%s-{in:payment}' % BALT), O('Set aside minus needed, 12 months', 'money', '%s-%s' % (SA12, NEED12)),
    O('Verdict', 'text', 'IF(%s>={in:payment},%s,%s&" "&ROUND({in:payment}-%s,0))' % (BALT, vb('Set aside is on track'), vb('Short by'), BALT))],
    GR('What if', ('Payment 2,000', {'payment': 2000}), ('Payment 4,500', {'payment': 4500}), ('Payment 7,000', {'payment': 7000}), ('Payment 10,000', {'payment': 10000}))))

# 9 ------------------------------------------------------------ scenario test
SM = lambda c: R('scenario_months', c)
def SPR(i): return 'SUMIFS(%s,%s,%s)' % (SM('profit'), SM('scenario'), tok('scen', SCENARIOS[i]))
def SEC(i): return 'SUMIFS(%s,%s,%s,%s,12)' % (SM('cash'), SM('scenario'), tok('scen', SCENARIOS[i]), SM('ahead'))
MINC = 'MIN(%s)' % SM('cash')
MINN = 'INDEX(%s,MATCH(%s,%s,0))' % (SM('ahead'), MINC, SM('cash'))
tools.append(TOOL('scenario_test', 'Scenario Test', 'What if the year goes wrong',
    'A Base case and 5 scenarios (set the numbers on the Start sheet): profit and cash 12 months ahead and the lowest cash point against your floor.', [
    I('floor', 'Cash floor to test', D.CASH_FLOOR)], [
    O('Profit, next 12 months: ' + SCENARIOS[i], 'money', SPR(i)) for i in range(6)] + [
    O('Cash at month 12: ' + SCENARIOS[i], 'money', SEC(i)) for i in range(6)] + [
    O('Lowest cash in any scenario', 'money', MINC), O('Scenario with the lowest cash', 'text', 'INDEX(%s,MATCH(%s,%s,0))' % (SM('scenario'), MINC, SM('cash'))), O('Month of the lowest cash', 'int', MINN),
    O('Verdict', 'text', 'IF(%s>={in:floor},%s,%s&" "&%s)' % (MINC, vb('Worst case still above the cash floor'), vb('Dips below the floor, lowest in month'), MINN))],
    GR('What if', ('Floor 5,000', {'floor': 5000}), ('Floor 15,000', {'floor': 15000}), ('Floor 25,000', {'floor': 25000}), ('Floor 40,000', {'floor': 40000}))))

# 10 ----------------------------------------------------------- sensitivity row
RENT10, UT10, REV10 = A3('rented_days'), A3('utilisation'), A3('revenue')
ADR10 = '(%s/%s)' % (REV10, RENT10); AV10 = '(%s/%s)' % (RENT10, UT10)
VAR10 = '((%s+%s)/%s)' % (A3('channel_fees'), A3('fuel_charge'), REV10)
FIX10 = '(%s-%s-%s)' % (A3('costs'), A3('channel_fees'), A3('fuel_charge'))
def PR10(u, a): return '(%s*(%s)*(%s)*(1-%s)-%s)' % (AV10, u, a, VAR10, FIX10)
UEF = '(%s*{in:ustep}*%s*(1-%s))' % (AV10, ADR10, VAR10); AEF = '(%s*%s*{in:astep}*(1-%s))' % (AV10, UT10, VAR10)
tools.append(TOOL('sensitivity', 'Sensitivity Row', 'Which driver moves profit most',
    'Monthly profit at 5 steps of utilisation and 5 steps of average daily rate (revenue per rented day), from your last 3 months. The driver with the bigger effect per step is named.', [
    I('ustep', 'Utilisation step, points', 0.05, 'pct'), I('astep', 'Average daily rate step', 5)], [
    O('Utilisation, last 3 months', 'pct', UT10), O('Average daily rate, last 3 months', 'money', ADR10), O('Monthly profit now', 'money', PR10(UT10, ADR10))] + [
    O('Profit at utilisation %+d steps' % k, 'money', PR10('%s+(%d)*{in:ustep}' % (UT10, k), ADR10)) for k in (-2, -1, 1, 2)] + [
    O('Profit at rate %+d steps' % k, 'money', PR10(UT10, '%s+(%d)*{in:astep}' % (ADR10, k))) for k in (-2, -1, 1, 2)] + [
    O('Profit change for one utilisation step', 'money', UEF), O('Profit change for one rate step', 'money', AEF),
    O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (UEF, AEF, vb('Profit is most sensitive to utilisation'), vb('Profit is most sensitive to daily rate')))],
    GR('What if', ('Utilisation step 2 points, rate step 2', {'ustep': 0.02, 'astep': 2}), ('Utilisation step 10 points, rate step 10', {'ustep': 0.10, 'astep': 10}), ('Utilisation step 5 points, rate step 15', {'ustep': 0.05, 'astep': 15}))))

# 11 ----------------------------------------------------------- add-a-vehicle business case
AU = '((3*{in:peak}+5*{in:shoulder}+4*{in:off})/12)'; RD = '(30.4*%s)' % AU
RV = '(%s*{in:rate})' % RD
LP = 'IF({in:share}>0,-PMT({set:new_loan_rate}/12,{in:term},{in:price}*{in:share}),0)'
DEPM = '({in:price}*{set:dep_pct})'
CP11 = '(%s*(1-{in:fee})-%s*{in:fuel}-{in:ins}/12-{in:maint}-{in:overhead}-%s)' % (RV, RD, LP)
FIXD = '({in:ins}/12+{in:maint}+{in:overhead}+%s+%s)' % (LP, DEPM)
BE11 = '(%s/(({in:rate}*(1-{in:fee})-{in:fuel})*30.4))' % FIXD
tools.append(TOOL('add_vehicle', 'Add-a-Vehicle Business Case', 'Should you buy this vehicle',
    'Price, loan, utilisation by season and daily rate give profit a month, payback months and the utilisation that covers cost. Fee, fuel and staff share start from your last 12 months.', [
    I('price', 'Price', 26500), I('share', 'Financing share', 0.8, 'pct'), I('term', 'Loan term, months', 60, 'int'), I('rate', 'Daily rate', 86), I('peak', 'Utilisation in peak months', 0.85, 'pct'),
    I('shoulder', 'Utilisation in shoulder months', 0.70, 'pct'), I('off', 'Utilisation in off-peak months', 0.52, 'pct'), I('ins', 'Insurance a year', 1450), I('maint', 'Maintenance a month', MAINT_D),
    I('overhead', 'Staff and overhead the car adds a month', OVH_D), I('fee', 'Channel fee share of revenue', FEE_D, 'pct'), I('fuel', 'Fuel or charge per rented day', FUEL_D)], [
    O('Average utilisation', 'pct', AU), O('Rented days a month', 'num', RD), O('Revenue a month', 'money', RV), O('Loan payment a month', 'money', LP), O('Depreciation a month', 'money', DEPM),
    O('Cash profit a month', 'money', CP11), O('Profit a month after depreciation', 'money', '%s-%s' % (CP11, DEPM)), O('Cash you put in', 'money', '{in:price}*(1-{in:share})'),
    O('Payback months', 'num', 'IF(%s>0,{in:price}*(1-{in:share})/%s,0)' % (CP11, CP11)), O('Break-even utilisation', 'pct', BE11), O('Margin of safety, points above break-even', 'pct', '%s-%s' % (AU, BE11)),
    O('Verdict', 'text', 'IF(%s-%s<=0,%s,IF(AND({in:price}*(1-{in:share})/%s<=36,%s>=%s+0.1),%s,%s))' % (CP11, DEPM, va('Do not buy'), CP11, AU, BE11, va('Buy'), va('Wait')))],
    GR('What if', ('Utilisation 10 points higher', {'peak': 0.95, 'shoulder': 0.80, 'off': 0.62}), ('Utilisation 10 points lower', {'peak': 0.75, 'shoulder': 0.60, 'off': 0.42}), ('Bought with cash', {'share': 0}),
       ('Daily rate 78', {'rate': 78}), ('Price 31,000', {'price': 31000}), ('Premium car at 150 a day', {'price': 39000, 'rate': 150, 'peak': 0.78, 'shoulder': 0.55, 'off': 0.38, 'ins': 2300}))))

# 12 ----------------------------------------------------------- one-car host start-up case
LP12 = '(-PMT({in:rate}/12,{in:term},{in:price}*{in:share}))'
RV12 = '({in:days}*{in:day_rate})'
CASH12 = '(%s*(1-{in:fee})-{in:days}/{in:stay}*{in:clean}-{in:ins}/12-{in:maint}-%s)' % (RV12, LP12)
DEP12 = '({in:price}*{set:dep_pct})'
PR12 = '(%s-%s)' % (CASH12, DEP12)
FIX12 = '({in:ins}/12+{in:maint}+%s+%s)' % (LP12, DEP12)
BE12 = '(%s/({in:day_rate}*(1-{in:fee})-{in:clean}/{in:stay}))' % FIX12
tools.append(TOOL('one_car', 'One-Car Host Start-Up Case', 'Can one car pay for itself',
    'One car with its own cost and the rental days a month you expect: monthly profit, payback and the days a month you need to break even.', [
    I('price', 'Price of the car', 14000), I('share', 'Financing share', 0.8, 'pct'), I('rate', 'Loan rate', 0.08, 'pct'), I('term', 'Loan term, months', 48, 'int'), I('days', 'Rental days a month you expect', 22, 'int'),
    I('day_rate', 'Daily rate', 58), I('fee', 'Marketplace fee share', 0.20, 'pct'), I('stay', 'Average rental length, days', 3, 'int'), I('clean', 'Cleaning cost of each rental', 22), I('ins', 'Insurance a year', 1100), I('maint', 'Maintenance a month', 55)], [
    O('Revenue a month', 'money', RV12), O('Marketplace fees', 'money', '%s*{in:fee}' % RV12), O('Cleaning a month', 'money', '{in:days}/{in:stay}*{in:clean}'), O('Insurance a month', 'money', '{in:ins}/12'),
    O('Loan payment a month', 'money', LP12), O('Depreciation a month', 'money', DEP12), O('Cash profit a month', 'money', CASH12), O('Profit a month after depreciation', 'money', PR12),
    O('Cash you put in', 'money', '{in:price}*(1-{in:share})'), O('Payback months', 'num', 'IF(%s>0,{in:price}*(1-{in:share})/%s,0)' % (CASH12, CASH12)), O('Rental days a month needed to break even', 'num', BE12),
    O('Verdict', 'text', 'IF(%s>0,IF(%s<=0.8*{in:days},%s,%s),IF(%s<=30,%s,%s))' % (PR12, BE12, va('Start'), va('Start with a cheaper car'), BE12, va('Start with a cheaper car'), va('Wait')))],
    GR('What if', ('28 rental days', {'days': 28}), ('14 rental days', {'days': 14}), ('Cheaper car 9,500', {'price': 9500, 'day_rate': 42, 'ins': 900}), ('Bought with cash', {'share': 0}), ('Daily rate 65', {'day_rate': 65}))))

# 13 ----------------------------------------------------------- depreciation check
WD = R('vehicles', 'write_down')
tools.append(TOOL('dep_check', 'Depreciation Check', 'Does book value match the resale estimate',
    'Book value from your depreciation setting against the resale estimate of every vehicle in the fleet: the vehicles to write down and by how much.', [
    I('tol', 'Difference you accept before a write-down', 500)], [
    O('Fleet book value', 'money', 'SUM(%s)' % R('vehicles', 'book_value')), O('Fleet resale estimate', 'money', 'SUMIFS(%s,%s,"<>"&%s)' % (R('vehicles', 'resale_estimate'), R('vehicles', 'status'), SOLD)),
    O('Book value above resale, fleet', 'money', 'SUM(%s)-SUMIFS(%s,%s,"<>"&%s)' % (R('vehicles', 'book_value'), R('vehicles', 'resale_estimate'), R('vehicles', 'status'), SOLD)),
    O('Vehicles to write down', 'int', 'COUNTIFS(%s,">"&{in:tol})' % WD), O('Total write-down above the tolerance', 'money', 'SUMIFS(%s,%s,">"&{in:tol})' % (WD, WD)),
    O('Largest write-down', 'money', 'IFERROR(LARGE(%s,1),0)' % WD), O('Vehicle with the largest write-down', 'text', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,1),%s,0)),"")' % (R('vehicles', 'vehicle'), WD, WD)),
    O('Second largest write-down', 'money', 'IFERROR(LARGE(%s,2),0)' % WD), O('Vehicle with the second largest', 'text', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,2),%s,0)),"")' % (R('vehicles', 'vehicle'), WD, WD)),
    O('Depreciation, last 12 months', 'money', PS('depreciation', 12)), O('Depreciation setting a month', 'pct', '{set:dep_pct}'),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">"&{in:tol})=0,%s,%s&" "&INDEX(%s,MATCH(LARGE(%s,1),%s,0))&": "&ROUND(LARGE(%s,1),0))' % (WD, va('Consistent'), va('Write down'), R('vehicles', 'vehicle'), WD, WD, WD))],
    GR('What if', ('Tolerance 0', {'tol': 0}), ('Tolerance 250', {'tol': 250}), ('Tolerance 500', {'tol': 500}), ('Tolerance 1,000', {'tol': 1000}))))

# 14 ----------------------------------------------------------- fleet cost per day
def CMN(col): return CMS(col)
AVD, RTD, RVC, CSC = CMS('available_days'), CMS('rented_days'), CMS('revenue'), CMS('costs')
ALC = '(%s/%s*(%s+%s))' % (AVD, CMT('available_days'), PNN('staff'), PNN('overhead'))
CPD = 'IFERROR((%s+%s)/%s,0)' % (CSC, ALC, AVD); BEP = 'IFERROR((%s+%s)/%s,0)' % (CSC, ALC, RTD)
tools.append(TOOL('fleet_cost', 'Fleet Cost per Day', 'What does one car-day cost in this class',
    'All-in cost per available day by class from the vehicle months, plus a share of staff and overhead by available days; the lowest rate per rented day that breaks even follows.', [
    IN('cls', 'Class', 'list', key('class', 'Midsize SUV'), list='class'), I('months', 'Months back', 12, 'int')], [
    O('Available car-days', 'int', AVD), O('Rented days', 'int', RTD), O('Utilisation', 'pct', 'IFERROR(%s/%s,0)' % (RTD, AVD)), O('Revenue', 'money', RVC), O('Vehicle costs', 'money', CSC),
    O('Share of staff and overhead', 'money', ALC), O('All-in cost per available day', 'money', CPD), O('Revenue per available car-day', 'money', 'IFERROR(%s/%s,0)' % (RVC, AVD)),
    O('Lowest rate per rented day to break even', 'money', BEP), O('Average daily rate achieved', 'money', 'IFERROR(%s/%s,0)' % (RVC, RTD)), O('Achieved rate minus break-even rate', 'money', 'IFERROR(%s/%s,0)-%s' % (RVC, RTD, BEP)),
    O('Verdict', 'text', '{in:cls}&" "&%s&" "&ROUND(%s,2)&", "&%s&" "&ROUND(%s,2)' % (vb('costs a day'), CPD, vb('the lowest rate to break even is'), BEP))],
    GR('What if', ('Last 3 months', {'months': 3}), ('Last 6 months', {'months': 6}), ('Last 12 months', {'months': 12}), ('Last 18 months', {'months': 18}))))

# 15 ----------------------------------------------------------- break-even revenue
def AN(col): return '(%s/{in:months})' % PNN(col)
REV15, VAR15 = AN('revenue'), '(%s+%s)' % (AN('channel_fees'), AN('fuel_charge'))
FIX15 = '(%s-%s)' % (AN('costs'), VAR15); BE15 = '(%s/(1-%s/%s))' % (FIX15, VAR15, REV15)
tools.append(TOOL('breakeven', 'Break-Even Revenue', 'How much revenue covers all costs',
    'The monthly revenue that covers every cost including depreciation, from your own recent months: channel fees and fuel move with revenue, the rest is fixed.', [
    I('months', 'Months back', 3, 'int')], [
    O('Revenue a month', 'money', REV15), O('Costs a month', 'money', AN('costs')), O('Channel fees and fuel a month', 'money', VAR15), O('Share of revenue that moves with revenue', 'pct', '%s/%s' % (VAR15, REV15)),
    O('Fixed costs a month, depreciation included', 'money', FIX15), O('Break-even revenue a month', 'money', BE15), O('Break-even revenue before depreciation', 'money', '(%s-%s)/(1-%s/%s)' % (FIX15, AN('depreciation'), VAR15, REV15)),
    O('Revenue above break-even', 'money', '%s-%s' % (REV15, BE15)), O('Margin of safety', 'pct', '(%s-%s)/%s' % (REV15, BE15, REV15)), O('Average daily rate', 'money', '%s/%s' % (REV15, AN('rented_days'))),
    O('Rented days a month to break even, all cars', 'num', '%s/(%s/%s)' % (BE15, REV15, AN('rented_days'))), O('Break-even utilisation', 'pct', '%s*%s/%s' % (AN('utilisation'), BE15, REV15)),
    O('Verdict', 'text', 'IF(%s>=%s,%s&" "&ROUND(%s-%s,0),%s&" "&ROUND(%s-%s,0))' % (REV15, BE15, vb('Above break-even by'), REV15, BE15, vb('Below break-even by'), BE15, REV15))],
    GR('What if', ('Last month', {'months': 1}), ('Last 6 months', {'months': 6}), ('Last 12 months', {'months': 12}))))

# 16 ----------------------------------------------------------- fleet financing mix
INT12 = 'SUMIFS(%s,%s)' % (R('financing', 'interest'), WIN('financing', 12))
SHI = '(%s/%s)' % (INT12, PS('revenue', 12))
tools.append(TOOL('fin_mix', 'Fleet Financing Mix', 'Financed or bought with cash',
    'The share of the fleet that is financed, the loan balance, the interest paid in 12 months and its share of revenue, against the share you accept.', [
    I('limit', 'Most interest you accept, share of revenue', 0.035, 'pct')], [
    O('Vehicles in the fleet', 'int', 'COUNTIFS(%s,"<>"&%s,%s,"<>")' % (R('vehicles', 'status'), SOLD, R('vehicles', 'vehicle_id'))), O('Financed vehicles', 'int', 'COUNTIFS(%s,%s,%s,"<>"&%s)' % (R('vehicles', 'financed'), YES, R('vehicles', 'status'), SOLD)),
    O('Financed share of the fleet', 'pct', 'COUNTIFS(%s,%s,%s,"<>"&%s)/COUNTIFS(%s,"<>"&%s,%s,"<>")' % (R('vehicles', 'financed'), YES, R('vehicles', 'status'), SOLD, R('vehicles', 'status'), SOLD, R('vehicles', 'vehicle_id'))),
    O('Financed share of book value', 'pct', 'SUMIFS(%s,%s,%s)/SUM(%s)' % (R('vehicles', 'book_value'), R('vehicles', 'financed'), YES, R('vehicles', 'book_value'))),
    O('Loan balance', 'money', 'SUM(%s)' % R('vehicles', 'loan_balance')), O('Average rate on the balance', 'pct', 'SUM(%s)/SUM(%s)' % (R('vehicles', 'interest_year'), R('vehicles', 'loan_balance'))),
    O('Interest paid, last 12 months', 'money', INT12), O('Revenue, last 12 months', 'money', PS('revenue', 12)), O('Interest share of revenue', 'pct', SHI),
    O('Loan balance as a share of resale of financed cars', 'pct', 'SUM(%s)/SUMIFS(%s,%s,%s,%s,"<>"&%s)' % (R('vehicles', 'loan_balance'), R('vehicles', 'resale_estimate'), R('vehicles', 'financed'), YES, R('vehicles', 'status'), SOLD)),
    O('Verdict', 'text', 'IF(%s>{in:limit},%s,%s)' % (SHI, va('High interest cost'), va('Balanced')))],
    GR('What if', ('Limit 2%', {'limit': 0.02}), ('Limit 3%', {'limit': 0.03}), ('Limit 5%', {'limit': 0.05}))))

# 17 ----------------------------------------------------------- sale proceeds against payoff
NET17 = '({in:price}*(1-{set:sell_cost_pct})-{in:prep})'
LEFT17 = '(%s-%s)' % (NET17, BAL)
tools.append(TOOL('sale_payoff', 'Sale Proceeds vs Payoff', 'Does the sale pay off the loan',
    'The expected sale price less the cost of sale and the loan balance: the cash a sale frees or the cash it needs. Ask your lender for the payoff figure.', [
    I('veh', 'Vehicle', LOWV, 'text'), I('price', 'Expected sale price', 28500), I('prep', 'Cost to prepare the car for sale', 350)], [
    O('Loan balance to pay off', 'money', BAL), O('Resale estimate', 'money', RES), O('Cost of sale', 'money', '{in:price}*{set:sell_cost_pct}+{in:prep}'), O('Net proceeds', 'money', NET17),
    O('Cash freed by the sale (negative = cash needed)', 'money', LEFT17), O('Book value', 'money', BOOK), O('Sale price minus book value', 'money', '{in:price}-%s' % BOOK),
    O('Sale price minus resale estimate', 'money', '{in:price}-%s' % RES), O('Cash now after the sale', 'money', '%s+%s' % (CASH_NOW, LEFT17)),
    O('Verdict', 'text', 'IF(%s>=0,%s&" "&ROUND(%s,0),%s&" "&ROUND(-(%s),0)&" "&%s)' % (LEFT17, va('Sale frees'), LEFT17, va('Sale needs'), LEFT17, va('from cash')))],
    GR('What if', ('Sale price 26,000', {'price': 26000}), ('Sale price 27,500', {'price': 27500}), ('Sale price 30,000', {'price': 30000}), ('Preparation 1,200', {'prep': 1200}))))

# 18 ----------------------------------------------------------- year-end pack check
def YR(t, c='month'): return '%s,">="&DATE({in:year},1,1),%s,"<="&DATE({in:year},12,31)' % (R(t, c), R(t, c))
MP, MC, MT, MD = ['COUNTIFS(%s)' % YR(t) for t in ('pnl', 'cash', 'tax', 'draw')]
MISS = '((12-%s)+(12-%s)+(12-%s)+(12-%s))' % (MP, MC, MT, MD)
tools.append(TOOL('year_pack', 'Year-End Pack Check', 'Is the year ready for your accountant',
    'The totals your accountant asks for (revenue, costs, depreciation, tax set-aside, loan interest and owner draw) and the months still missing from each sheet. Confirm with your adviser.', [
    I('year', 'Year', D.T0.year - 1, 'int')], [
    O('Months in Profit and Loss', 'int', MP), O('Months in Cash', 'int', MC), O('Months in Tax Set-Aside', 'int', MT), O('Months in Owner Draw', 'int', MD),
    O('Revenue', 'money', 'SUMIFS(%s,%s)' % (R('pnl', 'revenue'), YR('pnl'))), O('Costs', 'money', 'SUMIFS(%s,%s)' % (R('pnl', 'costs'), YR('pnl'))), O('Depreciation', 'money', 'SUMIFS(%s,%s)' % (R('pnl', 'depreciation'), YR('pnl'))),
    O('Profit', 'money', 'SUMIFS(%s,%s)' % (R('pnl', 'profit'), YR('pnl'))), O('Tax set-aside', 'money', 'SUMIFS(%s,%s)' % (R('tax', 'set_aside'), YR('tax'))),
    O('Loan interest', 'money', 'SUMIFS(%s,%s)' % (R('financing', 'interest'), YR('financing'))), O('Owner draw', 'money', 'SUMIFS(%s,%s)' % (R('draw', 'total'), YR('draw'))),
    O('Months missing in all four sheets', 'int', MISS),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (MISS, va('Pack complete'), MISS, va('items missing, confirm with your adviser')))],
    GR('What if', ('This year so far', {'year': D.T0.year}), ('Two years back', {'year': D.T0.year - 2}))))
assert len(tools) == 18
