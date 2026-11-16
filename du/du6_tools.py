"""Doula business suite part 6: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du6_lists import *
import du6_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='num', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, lab): return IN(k, label, 'list', key(lst, lab), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
PC = tok('basis', 'Per client'); PH = tok('basis', 'Per hour'); MIL = tok('basis', 'Mileage'); STI = tok('basis', 'Backup stipend'); CALL = tok('basis', 'Backup call-out')
PAID = tok('paystatus', 'Paid'); DUE = tok('paystatus', 'Due')
def DOU(c): return 'IFERROR(INDEX({range:doulas.%s},MATCH({in:doula},{range:doulas.doula},0)),0)' % c
def PK(c): return 'IFERROR(INDEX({range:packages.%s},MATCH({in:package},{range:packages.package},0)),0)' % c
def MD(c): return 'IFERROR(INDEX({range:margin_doula.%s},MATCH({in:doula},{range:margin_doula.doula},0)),0)' % c
def TM(c): return 'IFERROR(INDEX({range:team.%s},MATCH({in:doula},{range:team.name},0)),0)' % c
def PCT(x): return 'ROUND((%s)*100,1)&"%%"' % x
ST = D.ST
tools = []

# 1 ------------------------------------------------------------ agency doula pay calculator
tools.append(TOOL('pay_calc', 'Agency Doula Pay Calculator', 'What a package leaves the agency after doula pay, backup, mileage and overhead',
    'Type a package, pick a doula and the trips: the doula pay (agency share of the birth part plus hourly pay for postpartum hours), backup, mileage and overhead, and the margin per client against your target.', [
    I('package', 'Package', 'Birth Plus', 'text'), IL('doula', 'Doula', 'cdoula', 'Lucia Ferreira'), IL('area', 'Area', 'area', 'Northgate'), I('trips', 'Trips for the client (visits and the birth)', 8, 'int'),
    I('miles_trip', 'Miles a round trip', 24), I('backup_rate', 'Share of clients that need a backup doula', 0.1, 'pct')], [
    O('Package price', 'money', PK('price')), O('Birth part', 'money', PK('birth_value')), O('Postpartum part', 'money', PK('pp_value')), O('Agency share of the birth part', 'pct', DOU('agency_share')), O('Hourly pay of the doula', 'money', DOU('hourly_pay')),
    O('Doula pay, birth part', 'money', '%s*(1-%s)' % (PK('birth_value'), DOU('agency_share'))), O('Doula pay, postpartum hours', 'money', '%s*%s' % (PK('postpartum_hours'), DOU('hourly_pay'))),
    O('Doula pay in all', 'money', '%s*(1-%s)+%s*%s' % (PK('birth_value'), DOU('agency_share'), PK('postpartum_hours'), DOU('hourly_pay'))),
    O('Expected backup cost', 'money', '{in:backup_rate}*{set:backup_flat_pay}'), O('Mileage cost', 'money', '{in:trips}*{in:miles_trip}*IF({in:area}=%s,{set:mileage_rate_north},{set:mileage_rate_south})' % tok('area', 'Northgate')),
    O('Overhead per client', 'money', '{set:agency_cost_client}'),
    O('Margin per client', 'money', '%s-(%s*(1-%s)+%s*%s)-{in:backup_rate}*{set:backup_flat_pay}-{in:trips}*{in:miles_trip}*IF({in:area}=%s,{set:mileage_rate_north},{set:mileage_rate_south})-{set:agency_cost_client}' % (PK('price'), PK('birth_value'), DOU('agency_share'), PK('postpartum_hours'), DOU('hourly_pay'), tok('area', 'Northgate'))),
    O('Your target margin per client', 'money', '{set:target_margin_client}'),
    O('Verdict', 'text', 'IF(%s-(%s*(1-%s)+%s*%s)-{in:backup_rate}*{set:backup_flat_pay}-{in:trips}*{in:miles_trip}*IF({in:area}=%s,{set:mileage_rate_north},{set:mileage_rate_south})-{set:agency_cost_client}>={set:target_margin_client},%s,%s)&": "&ROUND(%s-(%s*(1-%s)+%s*%s)-{in:backup_rate}*{set:backup_flat_pay}-{in:trips}*{in:miles_trip}*IF({in:area}=%s,{set:mileage_rate_north},{set:mileage_rate_south})-{set:agency_cost_client},0)' % (
        PK('price'), PK('birth_value'), DOU('agency_share'), PK('postpartum_hours'), DOU('hourly_pay'), tok('area', 'Northgate'), ck('Margin per client is above the target'), ck('Margin per client is below the target'),
        PK('price'), PK('birth_value'), DOU('agency_share'), PK('postpartum_hours'), DOU('hourly_pay'), tok('area', 'Northgate')))],
    GR('What if', ('No backup needed', {'backup_rate': 0}), ('Backup on a quarter of clients', {'backup_rate': 0.25}), ('Twelve trips', {'trips': 12}), ('Four trips', {'trips': 4}), ('Long trips of 40 miles', {'miles_trip': 40}))))

# 2 ------------------------------------------------------------ agency capacity by doula
def FREE(n, col='free'): return 'SUMIFS({range:cap.%s},{range:cap.doula},%s,{range:cap.month},{in:month})' % (col, tok('doula', n))
def BEST(col): return 'MAX(%s)' % ','.join(FREE(n, col) for n in DOULA_NAMES)
def BESTN(col): return 'INDEX({range:doulas.doula},MATCH(%s,CHOOSE({1,2,3,4,5,6,7},%s),0))' % (BEST(col), ','.join(FREE(n, col) for n in DOULA_NAMES))
tools.append(TOOL('cap_tool', 'Agency Capacity by Doula', 'Which doula can take the next client in a month',
    'Pick a month and the clients to place: places left for each doula against the most due dates a month (Capacity by Doula), the best doula for a birth client and for a postpartum client, and the places left in all.', [
    I('month', 'Month of the estimated due date (1st of the month)', iso(add_months(month_start(0), 3)), 'date'), I('needed', 'Clients to place', 1, 'int')],
    [O('Places left, %s' % n, 'int', FREE(n)) for n in DOULA_NAMES] + [
    O('Places left in all', 'int', 'SUMIFS({range:cap.free},{range:cap.month},{in:month})'), O('Doulas at or over capacity', 'int', 'COUNTIFS({range:cap.month},{in:month},{range:cap.flag},%s)+COUNTIFS({range:cap.month},{in:month},{range:cap.flag},%s)' % (ck('Over capacity'), ck('At capacity'))),
    O('Best doula for a birth client', 'text', BESTN('free_birth')), O('Places left with that doula', 'int', BEST('free_birth')), O('Best doula for a postpartum client', 'text', BESTN('free_pp')),
    O('Verdict', 'text', 'IF(%s>={in:needed},%s&": "&%s,%s)' % (BEST('free_birth'), ck('Best doula to assign'), BESTN('free_birth'), ck('No room: waitlist or name a backup')))],
    GR('What if', ('Place 2 clients', {'needed': 2}), ('Place 3 clients', {'needed': 3}), ('Place 4 clients', {'needed': 4}), ('Place 1 client', {'needed': 1}), ('Place 6 clients', {'needed': 6}))))

# 3 ------------------------------------------------------------ agency split proposal
tools.append(TOOL('split_tool', 'Agency Split Proposal', 'Should the agency accept a new share for a doula',
    'Pick a doula and type the proposed agency share, the clients a year and the average birth part of a package: the effect on the owner margin and on the doula pay per client, and the share that keeps your target.', [
    IL('doula', 'Doula', 'cdoula', 'Priya Raman'), I('new_share', 'New agency share', 0.20, 'pct'), I('clients_year', 'Clients a year', 13, 'int'), I('avg_package', 'Average birth part of a package', 1880, 'money')], [
    O('Current agency share', 'pct', DOU('agency_share')), O('Clients with pay lines so far', 'int', MD('clients')), O('Margin per client now', 'money', 'IFERROR(%s/%s,0)' % (MD('margin'), MD('clients'))),
    O('Owner margin change a year', 'money', '{in:clients_year}*{in:avg_package}*({in:new_share}-%s)' % DOU('agency_share')), O('Doula pay change per client', 'money', '-{in:avg_package}*({in:new_share}-%s)' % DOU('agency_share')),
    O('Margin per client after', 'money', 'IFERROR(%s/%s,0)+{in:avg_package}*({in:new_share}-%s)' % (MD('margin'), MD('clients'), DOU('agency_share'))), O('Your target margin per client', 'money', '{set:target_margin_client}'),
    O('Share that keeps your target', 'pct', 'MAX(0,%s+({set:target_margin_client}-IFERROR(%s/%s,0))/{in:avg_package})' % (DOU('agency_share'), MD('margin'), MD('clients'))),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s,0)+{in:avg_package}*({in:new_share}-%s)>={set:target_margin_client},%s,%s&" "&%s)' % (MD('margin'), MD('clients'), DOU('agency_share'), ck('Accept the proposal'), ck('Counter at'),
        PCT('MAX(0,%s+({set:target_margin_client}-IFERROR(%s/%s,0))/{in:avg_package})' % (DOU('agency_share'), MD('margin'), MD('clients')))))],
    GR('What if', ('Share 10%', {'new_share': 0.10}), ('Share 15%', {'new_share': 0.15}), ('Share 25%', {'new_share': 0.25}), ('Share 30%', {'new_share': 0.30}), ('Share 35%', {'new_share': 0.35}))))

# 4 ------------------------------------------------------------ doula pay run
def PRL(b, c='pay_due', ex=''): return 'SUMIFS({range:pay.%s},{range:pay.doula},{in:doula},{range:pay.month},{in:month}%s%s)' % (c, ',{range:pay.basis},%s' % b if b else '', ex)
TOTL = 'SUMIFS({range:pay.pay_due},{range:pay.doula},{in:doula},{range:pay.month},{in:month})'
DN = 'SUMIFS({range:pay.differs},{range:pay.doula},{in:doula},{range:pay.month},{in:month})'
DA = 'SUMIFS({range:pay.difference},{range:pay.doula},{in:doula},{range:pay.month},{in:month})'
tools.append(TOOL('payrun_tool', 'Doula Pay Run', 'Does the month pay run of a doula balance with what was paid',
    'Pick a month and a person and type any adjustment: per-client pay, per-hour pay, mileage and backup pay due, the paid amount and the lines paid differently; read from Pay Lines.', [
    I('month', 'Month (1st of the month)', iso(D.DEF_DIFF['month']), 'date'), IL('doula', 'Doula', 'payee', D.DEF_DIFF['doula']), I('adjust', 'Adjustment to add to the pay due', 0, 'money')], [
    O('Per-client pay', 'money', PRL(PC)), O('Per-hour pay', 'money', PRL(PH)), O('Mileage', 'money', PRL(MIL)), O('Backup stipend and call-out pay', 'money', '%s+%s' % (PRL(STI), PRL(CALL))), O('Adjustment', 'money', '{in:adjust}'),
    O('Total due', 'money', '%s+{in:adjust}' % TOTL), O('Paid', 'money', PRL('', 'paid_amount')), O('Not paid yet', 'money', PRL('', 'pay_due', ',{range:pay.status},%s' % DUE)), O('Lines that differ from what was due', 'int', DN),
    O('Amount of the differences', 'money', DA), O('Total due, all doulas, this month', 'money', 'SUMIFS({range:pay.pay_due},{range:pay.month},{in:month})'),
    O('Verdict', 'text', 'IF(AND(%s=0,%s=0),%s,%s&": "&%s&" "&%s&", "&ROUND(%s,2))' % (DN, PRL('', 'pay_due', ',{range:pay.status},%s' % DUE), ck('Pay run balances'), ck('Differences found'), DN, ck('line(s)'), DA))],
    GR('What if', ('Add 50', {'adjust': 50}), ('Add 100', {'adjust': 100}), ('Deduct 40', {'adjust': -40}), ('Deduct 100', {'adjust': -100}), ('No adjustment', {'adjust': 0}))))

# 5 ------------------------------------------------------------ owner own-client load
OT4 = lambda c: 'SUMIFS({range:owner_time.%s},{range:owner_time.week},">="&({today}-28))' % c
WK = '({in:own}+{in:mgmt}+{in:admin})'
tools.append(TOOL('owner_load_tool', 'Owner Own-Client Load', 'What an hour of your work pays you when you are both a doula and the manager',
    'Type the weekly hours on your own clients, on managing and on office work, and your owner draw: hours a month, the draw per hour worked against your target and the hours to hand over.', [
    I('own', 'Own client hours a week', D.DEF_OWN), I('mgmt', 'Management hours a week', D.DEF_MGMT), I('admin', 'Admin hours a week', D.DEF_ADMIN), I('draw', 'Owner draw a month', 3600, 'money')], [
    O('Hours a week', 'num', WK), O('Hours a month', 'num', '%s*52/12' % WK), O('Owner draw per hour worked', 'money', '{in:draw}/(%s*52/12)' % WK), O('Pay per hour you want', 'money', '{set:target_income_hour}'),
    O('Hours a month that match your target', 'num', '{in:draw}/{set:target_income_hour}'), O('Hours to hand over a month', 'num', 'MAX(0,%s*52/12-{in:draw}/{set:target_income_hour})' % WK),
    O('Cost of an admin handing over those hours', 'money', 'MAX(0,%s*52/12-{in:draw}/{set:target_income_hour})*{set:admin_rate}' % WK), O('Share of hours on own clients', 'pct', '{in:own}/%s' % WK),
    O('Own client hours a week, last 4 weeks (log)', 'num', '%s/4' % OT4('own_client_hours')), O('Management and admin hours a week, last 4 weeks (log)', 'num', '(%s+%s)/4' % (OT4('management_hours'), OT4('admin_hours'))),
    O('Verdict', 'text', '%s&" "&ROUND({in:draw}/(%s*52/12),1)&", "&%s&" "&ROUND(MAX(0,%s*52/12-{in:draw}/{set:target_income_hour}),0)&" "&%s' % (ck('Owner pay per hour is'), WK, ck('delegate'), WK, ck('hours a month')))],
    GR('What if', ('Hand over 10 admin hours', {'admin': max(0, D.DEF_ADMIN - 10)}), ('Own clients 20 hours', {'own': 20}), ('Own clients 30 hours', {'own': 30}), ('Draw of 4,500', {'draw': 4500}), ('Draw of 3,000', {'draw': 3000}))))

# 6 ------------------------------------------------------------ profit by doula
PW = 'IFERROR(SUMIFS({range:profit.%s},{range:profit.doula},{in:doula},{range:profit.month},">="&EDATE(%s,-{in:months}),{range:profit.month},"<"&%s),0)' % ('%s', MS, MS)
CLW = 'COUNTIFS({range:margin.doula},{in:doula},{range:margin.edd},">="&EDATE(%s,-{in:months}),{range:margin.edd},"<"&%s)' % (MS, MS)
HW = 'SUMIFS({range:hrs.total_hours},{range:hrs.doula},{in:doula},{range:hrs.month},">="&EDATE(%s,-{in:months}),{range:hrs.month},"<"&%s)' % (MS, MS)
BESTD = 'INDEX({range:margin_doula.doula},MATCH(MAX({range:margin_doula.margin}),{range:margin_doula.margin},0))'
LOWD = 'INDEX({range:margin_doula.doula},MATCH(MIN({range:margin_doula.margin}),{range:margin_doula.margin},0))'
tools.append(TOOL('profit_tool', 'Profit by Doula', 'Which doula leaves the agency the most and which the least',
    'Pick a doula and the last months (up to 12): revenue, pay, mileage, overhead and margin, and the margin per hour worked; the best and the lowest doula of all history come from Margin by Doula.', [
    IL('doula', 'Doula', 'cdoula', 'Mei-Ling Chen'), I('months', 'Last months (up to 12)', 12, 'int')], [
    O('Revenue', 'money', PW % 'revenue'), O('Doula pay', 'money', PW % 'pay'), O('Mileage paid', 'money', PW % 'mileage'), O('Clients due in these months', 'int', CLW), O('Overhead for those clients', 'money', '%s*{set:agency_cost_client}' % CLW),
    O('Margin after pay, mileage and overhead', 'money', '%s-%s*{set:agency_cost_client}' % (PW % 'margin', CLW)), O('Hours worked', 'num', HW),
    O('Margin per hour worked', 'money', 'IFERROR((%s-%s*{set:agency_cost_client})/%s,0)' % (PW % 'margin', CLW, HW)), O('Best doula, all history', 'text', BESTD), O('Margin of the best doula', 'money', 'MAX({range:margin_doula.margin})'),
    O('Lowest doula, all history', 'text', LOWD), O('Margin of the lowest doula', 'money', 'MIN({range:margin_doula.margin})'),
    O('Verdict', 'text', '%s&" "&%s&", "&%s&" "&%s' % (ck('Best doula'), BESTD, ck('lowest'), LOWD))],
    GR('What if', ('Last 3 months', {'months': 3}), ('Last 6 months', {'months': 6}), ('Last 9 months', {'months': 9}), ('Last 12 months', {'months': 12}), ('Last month', {'months': 1}))))

# 7 ------------------------------------------------------------ losing split finder
PCPAY = 'SUMIFS({range:pay.pay_due},{range:pay.doula},{in:doula},{range:pay.basis},%s)' % PC
BASE = '(%s/(1-%s))' % (PCPAY, DOU('agency_share'))
MGN = MD('margin'); NCL = MD('clients')
def MR(c): return 'SUMIFS({range:margin.%s},{range:margin.doula},{in:doula})' % c
tools.append(TOOL('losing_split', 'Losing Split Finder', 'Which doula split loses money for the agency and what share breaks even',
    'Pick a doula and the target margin per client: revenue, pay, mileage and overhead from Agency Margin by Client, the margin, and the closed-form agency share that breaks even or reaches your target.', [
    IL('doula', 'Doula', 'cdoula', ST['split_doula']), I('target', 'Target margin per client', 250, 'money')], [
    O('Clients', 'int', NCL), O('Revenue', 'money', MR('revenue')), O('Doula pay', 'money', MR('doula_pay')), O('Mileage', 'money', MR('mileage')), O('Overhead', 'money', MR('overhead')), O('Margin after costs', 'money', MGN),
    O('Margin per client', 'money', 'IFERROR(%s/%s,0)' % (MGN, NCL)), O('Current agency share', 'pct', DOU('agency_share')), O('Birth part earned by the doula, all history', 'money', 'IFERROR(%s,0)' % BASE),
    O('Share that breaks even', 'pct', '%s+IFERROR(MAX(0,-%s)/%s,0)' % (DOU('agency_share'), MGN, BASE)), O('Share that reaches your target', 'pct', '%s+IFERROR(MAX(0,%s*{in:target}-%s)/%s,0)' % (DOU('agency_share'), NCL, MGN, BASE)),
    O('Doulas with a negative margin', 'int', 'COUNTIFS({range:margin_doula.margin},"<0")'),
    O('Verdict', 'text', 'IF(%s<0,%s&" "&{in:doula}&" "&%s&" "&%s,%s)' % (MGN, ck('Raise'), ck('share to'), PCT('%s+IFERROR(MAX(0,-%s)/%s,0)' % (DOU('agency_share'), MGN, BASE)), ck('Margin is positive: keep the split')))],
    GR('What if', ('Target 100 per client', {'target': 100}), ('Target 200 per client', {'target': 200}), ('Target 300 per client', {'target': 300}), ('Target 400 per client', {'target': 400}), ('Target 0', {'target': 0}))))

# 8 ------------------------------------------------------------ per-client vs per-hour pay
PCP = '%s*(1-%s)' % (PK('birth_value'), DOU('agency_share')); PHP = '{in:hours}*%s' % DOU('hourly_pay')
tools.append(TOOL('pc_vs_ph', 'Per-Client vs Per-Hour Pay', 'Would a doula earn more paid per client or per hour on one package',
    'Pick a doula who has both an agency share and an hourly pay, a package and the hours really worked: the pay per client against the pay per hour and the hours where both pay the same.', [
    IL('doula', 'Doula', 'cdoula', 'Mei-Ling Chen'), I('package', 'Package', 'Birth Plus', 'text'), I('hours', 'Hours really worked on the package', 26)], [
    O('Birth part of the package', 'money', PK('birth_value')), O('Agency share', 'pct', DOU('agency_share')), O('Hourly pay', 'money', DOU('hourly_pay')), O('Pay per client', 'money', PCP), O('Pay per hour at the hours worked', 'money', PHP),
    O('Per hour pays more or less, by', 'money', '%s-(%s)' % (PHP, PCP)), O('Pay per hour worked, per-client pay', 'money', 'IFERROR((%s)/{in:hours},0)' % PCP), O('Hours where both pay the same', 'num', 'IFERROR((%s)/%s,0)' % (PCP, DOU('hourly_pay'))),
    O('Agency margin change if paid per hour', 'money', '(%s)-(%s)' % (PCP, PHP)),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s>=%s,%s,%s)&" "&ROUND(ABS(%s-(%s)),0))' % (DOU('hourly_pay'), ck('No hourly pay set for this doula'), PHP, PCP, ck('Per hour pays more by'), ck('Per hour pays less by'), PHP, PCP))],
    GR('What if', ('20 hours', {'hours': 20}), ('30 hours', {'hours': 30}), ('40 hours', {'hours': 40}), ('50 hours', {'hours': 50}), ('60 hours', {'hours': 60}))))

# 9 ------------------------------------------------------------ backup pay run
def BL(b, c='pay_due', ex=''): return 'SUMIFS({range:pay.%s},{range:pay.doula},{in:backup},{range:pay.month},{in:month},{range:pay.basis},%s%s)' % (c, b, ex)
BALL = 'SUMIFS({range:pay.pay_due},{range:pay.doula},{in:backup},{range:pay.month},{in:month},{range:pay.status},%s)' % DUE
tools.append(TOOL('backup_run', 'Backup Pay Run', 'What each backup doula is due for stipends and call-outs',
    'Pick a backup doula and a month: rota weeks and stipend, call-outs and flat pay, what the Pay Lines show and what is still to pay; the pay lines and the Backup Rota are compared.', [
    IL('backup', 'Backup doula', 'backup', 'Yasmin Haddad'), I('month', 'Month (1st of the month)', iso(month_start(0)), 'date')], [
    O('Rota weeks', 'int', 'COUNTIFS({range:rota.backup},{in:backup},{range:rota.month},{in:month})'), O('Stipend on the rota', 'money', 'SUMIFS({range:rota.stipend},{range:rota.backup},{in:backup},{range:rota.month},{in:month})'),
    O('Stipend on the pay lines', 'money', BL(STI)), O('Stipend on the rota not yet on pay lines', 'money', 'SUMIFS({range:rota.stipend},{range:rota.backup},{in:backup},{range:rota.month},{in:month})-%s' % BL(STI)),
    O('Call-outs', 'int', 'COUNTIFS({range:pay.doula},{in:backup},{range:pay.month},{in:month},{range:pay.basis},%s)' % CALL), O('Call-out pay at the flat pay', 'money', 'COUNTIFS({range:pay.doula},{in:backup},{range:pay.month},{in:month},{range:pay.basis},%s)*{set:backup_flat_pay}' % CALL),
    O('Call-out pay on the pay lines', 'money', BL(CALL)), O('Total due on pay lines', 'money', 'SUMIFS({range:pay.pay_due},{range:pay.doula},{in:backup},{range:pay.month},{in:month})'),
    O('Paid', 'money', 'SUMIFS({range:pay.paid_amount},{range:pay.doula},{in:backup},{range:pay.month},{in:month})'), O('Still to pay', 'money', BALL),
    O('Still to pay, both backup doulas', 'money', 'SUMIFS({range:pay.pay_due},{range:pay.month},{in:month},{range:pay.status},%s,{range:pay.basis},%s)+SUMIFS({range:pay.pay_due},{range:pay.month},{in:month},{range:pay.status},%s,{range:pay.basis},%s)' % (DUE, STI, DUE, CALL)),
    O('Verdict', 'text', 'IF(%s>0,%s&" "&{in:backup}&" "&ROUND(%s,0),%s)' % (BALL, ck('Pay'), BALL, ck('Nothing to pay')))],
    GR('What if', ('This month', {'month': '=DATE(YEAR(TODAY()),MONTH(TODAY()),1)'}), ('Last month', {'month': '=EDATE(DATE(YEAR(TODAY()),MONTH(TODAY()),1),-1)'}), ('Two months ago', {'month': '=EDATE(DATE(YEAR(TODAY()),MONTH(TODAY()),1),-2)'}), ('Three months ago', {'month': '=EDATE(DATE(YEAR(TODAY()),MONTH(TODAY()),1),-3)'}))))

# 10 ----------------------------------------------------------- pay-due forecast
SOFAR = 'SUMIFS({range:pay.pay_due},{range:pay.month},%s)' % MS
ELAP = '(DAY({today})/DAY(EDATE(%s,1)-1))' % MS
FAC = 'IF({in:scen}=%s,1+{in:best_pct},IF({in:scen}=%s,1-{in:worst_pct},1))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
tools.append(TOOL('forecast_tool', 'Pay-Due Forecast', 'How much to set aside for the next pay run',
    'Type a scenario and the best and worst moves: the pay lines so far this month turned into the full month, the last pay run and the amount to set aside with a buffer.', [
    IL('scen', 'Scenario', 'scen', 'Base'), I('best_pct', 'Best case adds', 0.12, 'pct'), I('worst_pct', 'Worst case takes off', 0.12, 'pct'), I('buffer', 'Buffer on top', 0.05, 'pct')], [
    O('Pay due so far this month', 'money', SOFAR), O('Share of the month gone', 'pct', ELAP), O('Projected month at this pace', 'money', '%s/%s' % (SOFAR, ELAP)), O('Scenario factor', 'num', FAC),
    O('Projected pay run', 'money', '%s/%s*%s' % (SOFAR, ELAP, FAC)), O('Last month pay run', 'money', 'SUMIFS({range:pay.pay_due},{range:pay.month},EDATE(%s,-1))' % MS), O('Change against last month', 'money', '%s/%s*%s-SUMIFS({range:pay.pay_due},{range:pay.month},EDATE(%s,-1))' % (SOFAR, ELAP, FAC, MS)),
    O('Amount to set aside', 'money', '%s/%s*%s*(1+{in:buffer})' % (SOFAR, ELAP, FAC)), O('Pay lines not yet paid this month', 'int', 'COUNTIFS({range:pay.month},%s,{range:pay.status},%s)' % (MS, DUE)),
    O('Verdict', 'text', '%s&" "&ROUND(%s/%s*%s*(1+{in:buffer}),0)' % (ck('Set aside'), SOFAR, ELAP, FAC))],
    GR('What if', ('Best case adds 20%', {'best_pct': 0.2}), ('Worst case takes off 20%', {'worst_pct': 0.2}), ('No buffer', {'buffer': 0}), ('Buffer of 10%', {'buffer': 0.10}), ('Buffer of 15%', {'buffer': 0.15}))))

# 11 ----------------------------------------------------------- mileage reimbursement check
MV = 'SUMIFS({range:visits.miles},{range:visits.doula},{in:doula},{range:visits.month},{in:month})+SUMIFS({range:births.miles},{range:births.doula},{in:doula},{range:births.month},{in:month})'
MC = 'SUMIFS({range:visits.mileage_cost},{range:visits.doula},{in:doula},{range:visits.month},{in:month})+SUMIFS({range:births.mileage_cost},{range:births.doula},{in:doula},{range:births.month},{in:month})'
ML = lambda c: 'SUMIFS({range:pay.%s},{range:pay.doula},{in:doula},{range:pay.month},{in:month},{range:pay.basis},%s)' % (c, MIL)
tools.append(TOOL('mileage_tool', 'Mileage Reimbursement Check', 'Does the mileage paid to a doula match the miles logged',
    'Pick a person and a month: the miles in Visits and Births Attended at the rate of each area against the mileage lines due and paid in Pay Lines.', [
    IL('doula', 'Doula', 'payee', D.MILDIFF['doula']), I('month', 'Month (1st of the month)', iso(D.MILDIFF['month']), 'date')], [
    O('Miles logged', 'num', MV), O('Mileage cost at the area rates', 'money', MC), O('Miles on the pay line', 'num', ML('miles')), O('Mileage pay due', 'money', ML('pay_due')), O('Mileage paid', 'money', ML('paid_amount')),
    O('Due less cost at the area rates', 'money', '%s-(%s)' % (ML('pay_due'), MC)), O('Paid less due', 'money', '%s-%s' % (ML('paid_amount'), ML('pay_due'))),
    O('Mileage paid to everyone this month', 'money', 'SUMIFS({range:pay.paid_amount},{range:pay.month},{in:month},{range:pay.basis},%s)' % MIL),
    O('Verdict', 'text', 'IF(ABS(%s-%s)<={set:diff_tolerance},IF(ABS(%s-(%s))<={set:diff_tolerance},%s,%s&" "&ROUND(%s-(%s),2)),%s&" "&ROUND(%s-%s,2))' % (ML('paid_amount'), ML('pay_due'), ML('pay_due'), MC, ck('Mileage matches'), ck('Mileage due differs by'), ML('pay_due'), MC, ck('Mileage paid differs by'), ML('paid_amount'), ML('pay_due')))],
    GR('What if', ('This month', {'month': '=DATE(YEAR(TODAY()),MONTH(TODAY()),1)'}), ('Last month', {'month': '=EDATE(DATE(YEAR(TODAY()),MONTH(TODAY()),1),-1)'}), ('Two months ago', {'month': '=EDATE(DATE(YEAR(TODAY()),MONTH(TODAY()),1),-2)'}), ('Three months ago', {'month': '=EDATE(DATE(YEAR(TODAY()),MONTH(TODAY()),1),-3)'}), ('Four months ago', {'month': '=EDATE(DATE(YEAR(TODAY()),MONTH(TODAY()),1),-4)'}))))

# 12 ----------------------------------------------------------- new doula case
MPC = '({in:price}*{in:share}-IFERROR(SUM({range:margin.mileage})/COUNTIFS({range:margin.client_id},"<>"),0)-{in:backup_rate}*{set:backup_flat_pay}-{set:agency_cost_client})'
tools.append(TOOL('new_doula', 'New Doula Case', 'Should the agency add a contracted doula',
    'Type the clients a year, the agency share, the average package price and the yearly cost of adding a doula: the margin per client, the yearly margin and the clients needed to cover the cost.', [
    I('clients_year', 'Expected clients a year', 16, 'int'), I('share', 'Agency share of the price', 0.28, 'pct'), I('price', 'Average package price', 1900, 'money'), I('fixed', 'Yearly cost of adding a doula (training, insurance, tools)', 1800, 'money'),
    I('backup_rate', 'Share of clients that need a backup doula', 0.1, 'pct')], [
    O('Agency keeps per client', 'money', '{in:price}*{in:share}'), O('Mileage per client in your history', 'money', 'IFERROR(SUM({range:margin.mileage})/COUNTIFS({range:margin.client_id},"<>"),0)'), O('Expected backup cost per client', 'money', '{in:backup_rate}*{set:backup_flat_pay}'),
    O('Overhead per client', 'money', '{set:agency_cost_client}'), O('Margin per client', 'money', MPC), O('Margin a year', 'money', '{in:clients_year}*%s' % MPC), O('Margin a year after the cost of adding', 'money', '{in:clients_year}*%s-{in:fixed}' % MPC),
    O('Clients needed to cover the cost', 'int', 'IF(%s>0,ROUNDUP({in:fixed}/%s,0),0)' % (MPC, MPC)), O('Your target margin per client', 'money', '{set:target_margin_client}'),
    O('Verdict', 'text', 'IF(AND(%s>={set:target_margin_client},{in:clients_year}>=IF(%s>0,ROUNDUP({in:fixed}/%s,0),999)),%s,%s)' % (MPC, MPC, MPC, ck('Hire'), ck('Wait')))],
    GR('What if', ('8 clients a year', {'clients_year': 8}), ('12 clients a year', {'clients_year': 12}), ('24 clients a year', {'clients_year': 24}), ('Share of 20%', {'share': 0.20}), ('Share of 35%', {'share': 0.35}))))

# 13 ----------------------------------------------------------- overhead per client check
NEWC = 'COUNTIFS({range:clients.signed_on},">"&EDATE({today},-12),{range:clients.status},"<>"&%s)' % tok('cstatus', 'Cancelled')
OHC = '(({set:admin_rate}*{set:admin_hours_week}*52*{in:admin_share}+{in:other})/%s)' % NEWC
tools.append(TOOL('overhead_tool', 'Overhead per Client Check', 'Is the overhead you charge each client right',
    'Type the share of admin time on client work and the other yearly costs: the real overhead per client from the admin hours and costs against the overhead setting.', [
    I('admin_share', 'Share of admin time spent on client work', 0.5, 'pct'), I('other', 'Other yearly costs shared by clients (insurance, tools)', 1500, 'money')], [
    O('Admin cost a year', 'money', '{set:admin_rate}*{set:admin_hours_week}*52'), O('Admin cost on client work', 'money', '{set:admin_rate}*{set:admin_hours_week}*52*{in:admin_share}'), O('Other yearly costs', 'money', '{in:other}'),
    O('Clients signed, last 12 months', 'int', NEWC), O('Overhead per client from your costs', 'money', OHC), O('Overhead setting', 'money', '{set:agency_cost_client}'), O('Difference', 'money', '%s-{set:agency_cost_client}' % OHC),
    O('Verdict', 'text', 'IF(%s>{set:agency_cost_client}*1.1,%s&" "&ROUND(%s,0),IF(%s<{set:agency_cost_client}*0.9,%s&" "&ROUND(%s,0),%s))' % (OHC, ck('Raise the overhead to'), OHC, OHC, ck('Lower the overhead to'), OHC, ck('Overhead is fine')))],
    GR('What if', ('Admin share 30%', {'admin_share': 0.3}), ('Admin share 70%', {'admin_share': 0.7}), ('Admin share 100%', {'admin_share': 1}), ('Other costs 0', {'other': 0}), ('Other costs 4,000', {'other': 4000}))))

# 14 ----------------------------------------------------------- doula earnings per hour
EP = 'SUMIFS({range:pay.pay_due},{range:pay.doula},{in:doula},{range:pay.basis},%s,{range:pay.month},">="&EDATE(%s,-{in:months}),{range:pay.month},"<"&%s)' % ('%s', MS, MS)
EH = 'SUMIFS({range:visits.hours},{range:visits.doula},{in:doula},{range:visits.month},">="&EDATE(%s,-{in:months}),{range:visits.month},"<"&%s)+SUMIFS({range:births.hours},{range:births.doula},{in:doula},{range:births.month},">="&EDATE(%s,-{in:months}),{range:births.month},"<"&%s)' % (MS, MS, MS, MS)
EC = 'SUMIFS({range:oncall.contact_hours},{range:oncall.doula},{in:doula},{range:oncall.oncall_end},">="&EDATE(%s,-{in:months}),{range:oncall.oncall_end},"<"&%s)' % (MS, MS)
PAYT = '(%s+%s)' % (EP % PC, EP % PH)
tools.append(TOOL('earnings_tool', 'Doula Earnings per Hour', 'Is a doula paid fairly for all the hours worked, including on-call contact',
    'Pick a doula and the last months: pay for client work divided by visit hours, birth hours and on-call contact hours, against the lowest pay per hour you think is fair.', [
    IL('doula', 'Doula', 'cdoula', 'Sven Lindqvist'), I('months', 'Last months', 12, 'int')], [
    O('Pay for client work', 'money', PAYT), O('Visit and birth hours', 'num', EH), O('On-call contact hours', 'num', EC), O('Hours worked in all', 'num', '%s+%s' % (EH, EC)),
    O('Pay per hour worked, all hours', 'money', 'IFERROR(%s/(%s+%s),0)' % (PAYT, EH, EC)), O('Pay per visit and birth hour', 'money', 'IFERROR(%s/(%s),0)' % (PAYT, EH)), O('Lowest fair pay per hour', 'money', '{set:min_pay_hour}'),
    O('Mileage paid on top', 'money', EP % MIL),
    O('Verdict', 'text', 'IF(IFERROR(%s/(%s+%s),0)>={set:min_pay_hour},%s,%s)&" "&{in:doula}' % (PAYT, EH, EC, ck('Pay is fair for'), ck('Pay is low for')))],
    GR('What if', ('Last 3 months', {'months': 3}), ('Last 6 months', {'months': 6}), ('Last 9 months', {'months': 9}), ('Last 12 months', {'months': 12}), ('Last 2 months', {'months': 2}))))

# 15 ----------------------------------------------------------- split by package
PKN = [1, 2, 3, 8, 9, 10]
def SM(k): return 'IFERROR(SUMIFS({range:margin.margin},{range:margin.doula},{in:doula},{range:margin.package},INDEX({range:packages.package},%d))/COUNTIFS({range:margin.doula},{in:doula},{range:margin.package},INDEX({range:packages.package},%d)),0)' % (k, k)
SMX = 'MAX(%s)' % ','.join(SM(k) for k in PKN)
tools.append(TOOL('package_split', 'Split by Package Comparison', 'Which package leaves the agency the most margin with a doula',
    'Pick a doula: the average margin per client after pay, mileage and overhead for each birth and combined package they have sold, and the package to steer them to.', [
    IL('doula', 'Doula', 'cdoula', 'Mei-Ling Chen')],
    [O('Margin per client, %s' % n, 'money', SM(k)) for k, n in zip(PKN, ['Birth Essential', 'Birth Plus', 'Birth Premier', 'Combined Essential', 'Combined Plus', 'Complete Care Bundle'])] + [
    O('Clients of this doula, all packages', 'int', 'COUNTIFS({range:margin.doula},{in:doula})'), O('Best margin per client', 'money', SMX),
    O('Verdict', 'text', '%s&" "&{in:doula}&" "&%s&" "&INDEX({range:packages.package},CHOOSE(MATCH(%s,CHOOSE({1,2,3,4,5,6},%s),0),1,2,3,8,9,10))' % (ck('Steer'), ck('to'), SMX, ','.join(SM(k) for k in PKN)))]))

# 16 ----------------------------------------------------------- owner vs contracted
AP = '%s*(1-%s)+%s*%s' % (PK('birth_value'), DOU('agency_share'), PK('postpartum_hours'), DOU('hourly_pay'))
AM = '(%s-(%s)-{set:agency_cost_client}-{set:backup_flat_pay}*{in:backup_rate})' % (PK('price'), AP)
OM = '(%s-{set:agency_cost_client}-{set:backup_flat_pay}*{in:backup_rate}-{in:owner_hours}*{in:hour_value})' % PK('price')
tools.append(TOOL('owner_vs_doula', 'Owner vs Contracted Margin', 'Take a client yourself or assign a doula',
    'Type a package, a doula, the hours you would spend and what an hour of your time is worth: what the agency keeps if you take the client against what it keeps with a doula.', [
    I('package', 'Package', 'Birth Premier', 'text'), IL('doula', 'Assigned doula', 'cdoula', 'Lucia Ferreira'), I('owner_hours', 'Hours you would spend on the client', 40), I('hour_value', 'What an hour of your time is worth', 45, 'money'),
    I('backup_rate', 'Share of clients that need a backup doula', 0.1, 'pct')], [
    O('Package price', 'money', PK('price')), O('Pay to the assigned doula', 'money', AP), O('Agency margin with the doula', 'money', AM), O('Cost of your time', 'money', '{in:owner_hours}*{in:hour_value}'),
    O('Agency margin after your time, if you take it', 'money', OM), O('Difference in favour of taking it', 'money', '%s-%s' % (OM, AM)), O('Hours where both are equal', 'num', 'IFERROR((%s)/{in:hour_value},0)' % AP),
    O('Verdict', 'text', 'IF(%s>%s,%s,%s)' % (OM, AM, ck('Take the client yourself'), ck('Assign the client')))],
    GR('What if', ('Your time worth 30', {'hour_value': 30}), ('Your time worth 60', {'hour_value': 60}), ('30 hours on the client', {'owner_hours': 30}), ('50 hours on the client', {'owner_hours': 50}), ('Backup on every client', {'backup_rate': 1}))))

# 17 ----------------------------------------------------------- year-end pay summary
YP = lambda b: 'SUMIFS({range:pay.pay_due},{range:pay.basis},%s,{range:pay.month},">="&DATE({in:year},1,1),{range:pay.month},"<="&DATE({in:year},12,1))' % b
YT = 'SUMIFS({range:pay.pay_due},{range:pay.month},">="&DATE({in:year},1,1),{range:pay.month},"<="&DATE({in:year},12,1))'
YR = 'SUMIFS({range:payrun.total_due},{range:payrun.month},">="&DATE({in:year},1,1),{range:payrun.month},"<="&DATE({in:year},12,1))'
tools.append(TOOL('year_end', 'Year-End Pay Summary', 'Do the year-end pay totals tie to the pay lines',
    'Type the year: doula pay per client and per hour, mileage, backup stipends and call-outs for the accountant, the paid total, and a check against the Pay Run Statement.', [
    I('year', 'Year', TODAY.year, 'int')], [
    O('Per-client pay', 'money', YP(PC)), O('Per-hour pay', 'money', YP(PH)), O('Mileage', 'money', YP(MIL)), O('Backup stipends', 'money', YP(STI)), O('Backup call-out pay', 'money', YP(CALL)), O('Total due for the year', 'money', YT),
    O('Paid in the year', 'money', 'SUMIFS({range:pay.paid_amount},{range:pay.month},">="&DATE({in:year},1,1),{range:pay.month},"<="&DATE({in:year},12,1))'), O('Pay lines in the year', 'int', 'COUNTIFS({range:pay.month},">="&DATE({in:year},1,1),{range:pay.month},"<="&DATE({in:year},12,1))'),
    O('Total due on the Pay Run Statement', 'money', YR), O('Difference', 'money', '%s-%s' % (YT, YR)),
    O('Verdict', 'text', 'IF(ABS(%s-%s)<0.005,%s,%s&" "&ROUND(%s-%s,2))' % (YT, YR, ck('Totals tie to the pay lines'), ck('Totals differ by'), YT, YR))],
    GR('What if', ('Last year', {'year': TODAY.year - 1}), ('Two years ago', {'year': TODAY.year - 2}), ('This year', {'year': TODAY.year}), ('Year before last, again', {'year': TODAY.year - 2}), ('Last year, again', {'year': TODAY.year - 1}))))

# 18 ----------------------------------------------------------- doula scorecard
tools.append(TOOL('scorecard', 'Doula Scorecard', 'Keep the terms of a doula or review them',
    'Pick a doula and the share of clients over plan hours you accept: clients, hours, pay per hour worked, margin per client and total margin, from Team and Agency Margin by Client.', [
    IL('doula', 'Doula', 'cdoula', 'Mei-Ling Chen'), I('over_max', 'Share of clients over plan hours you accept', 0.25, 'pct')], [
    O('Clients with pay lines', 'int', MD('clients')), O('Hours worked, 12 months', 'num', TM('hours_12')), O('Pay per hour worked, 12 months', 'money', TM('pay_hour_12')), O('Share of clients over plan hours', 'pct', TM('over_share')),
    O('Margin after costs, all history', 'money', MD('margin')), O('Margin per client', 'money', TM('margin_pc')), O('Your target margin per client', 'money', '{set:target_margin_client}'),
    O('Verdict', 'text', 'IF(AND(%s>={set:target_margin_client},%s<={in:over_max}),%s,%s)' % (TM('margin_pc'), TM('over_share'), ck('Keep the terms'), ck('Review the terms')))],
    GR('What if', ('Accept 10% over plan', {'over_max': 0.10}), ('Accept 20% over plan', {'over_max': 0.20}), ('Accept 30% over plan', {'over_max': 0.30}), ('Accept 40% over plan', {'over_max': 0.40}), ('Accept 50% over plan', {'over_max': 0.50}))))
assert len(tools) == 18, len(tools)
