"""HVAC suite part 4: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv4_lists import *
from hv4_tables import TS, JB, WK, LW, J13, W12M, MS, COMP, NO, YES, CWK, WON, LOST, OWNDRAW
import hv4_data as DD

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
SC = lambda c_: '{range:scorecard.%s}' % c_
SCM = 'MATCH({in:tech},{range:scorecard.technician},0)'
def SCV(c_, per='Last 13 weeks'): return 'SUMIFS(%s,%s,{in:tech},%s,%s)' % (SC(c_), SC('technician'), SC('period'), tok('period', per))
ST_ = lambda c_: '{range:comm_stmts.%s}' % c_
HW = lambda c_: '{range:hours_week.%s}' % c_
CB = lambda c_: '{range:callbacks.%s}' % c_
TW = '(%s+7)' % LW                      # Monday of this week
TECHD = key('crew', 'Kofi Mensah')
tools = []

# 1 technician hours analyser
WKN = '%s,">="&(%s-7*({in:weeks}-1)),%s,"<="&%s' % (TS('week'), LW, TS('week'), LW)
def H1(c_): return 'SUMIFS(%s,%s,{in:tech},%s)' % (TS(c_), TS('technician'), WKN)
UT1 = 'IFERROR(%s/%s,0)' % (H1('billed_hours'), H1('clock_hours'))
M1 = 'INDEX(%s,MATCH(LARGE(%s,1),%s,0))' % (SC('technician'), SC('idle_13'), SC('idle_13'))
M2 = 'INDEX(%s,MATCH(LARGE(%s,2),%s,0))' % (SC('technician'), SC('idle_13'), SC('idle_13'))
tools.append(TOOL('hours_analyser', 'Technician Hours Analyser', 'Where the clock hours of a technician went',
  'Pick a technician and the number of weeks: see clock, billed, drive, shop and idle hours, the utilisation against your target, what the idle time costs and which technician has the most idle hours to take the jobs.', [
    I('tech', 'Technician', key('crew', 'Kofi Mensah'), 'list', list='crew'), I('weeks', 'Weeks to look back (1 to 26)', 4, 'int')], [
    O('Clock hours', 'num', H1('clock_hours')), O('Billed hours', 'num', H1('billed_hours')), O('Drive hours', 'num', H1('drive_hours')), O('Shop hours', 'num', H1('shop_hours')), O('Idle hours', 'num', H1('idle_hours')),
    O('Utilisation', 'pct', UT1), O('Utilisation target', 'pct', '{set:util_target}'), O('Gap to the target, points', 'pct', UT1 + '-{set:util_target}'),
    O('Hours to fill to reach the target', 'num', 'MAX(0,{set:util_target}*%s-%s)' % (H1('clock_hours'), H1('billed_hours'))),
    O('Idle time cost', 'money', H1('idle_cost')), O('Idle time cost a week', 'money', H1('idle_cost') + '/{in:weeks}'),
    O('Move jobs to (most idle hours, 4 weeks)', 'text', 'IF(%s={in:tech},%s,%s)' % (M1, M2, M1)),
    O('Verdict', 'text', 'IF(%s>={set:util_target},%s,%s)' % (UT1, ck('On target'), ck('Move jobs to the idle technician')))],
  GR('What if', ('Tomasz Nowak, 4 weeks', {'tech': '=' + tok('crew', 'Tomasz Nowak')}), ('Diego Morales, 4 weeks', {'tech': '=' + tok('crew', 'Diego Morales')}), ('Amira Haddad, 4 weeks', {'tech': '=' + tok('crew', 'Amira Haddad')}),
     ('Kofi Mensah, 13 weeks', {'weeks': 13}), ('Jamal Whitfield, 13 weeks', {'tech': '=' + tok('crew', 'Jamal Whitfield'), 'weeks': 13}))))

# 2 paid versus billed gap
def G2(c_): return 'SUMIFS(%s,%s,{in:tech},%s,{in:month})' % (TS(c_), TS('technician'), TS('month'))
UB2 = G2('unbilled_cost')
SHOP2 = 'SUMIFS(%s,%s,{in:month})' % (TS('unbilled_cost'), TS('month'))
def RK(k, c_): return 'IFERROR(INDEX(%s,MATCH({in:month}*10+%d,%s,0)),%s)' % (TS(c_), k, TS('rank_key'), '""' if c_ == 'technician' else '0')
tools.append(TOOL('paid_billed_gap', 'Paid vs Billed Gap', 'Hours you paid for and did not bill, in money',
  'Pick a technician and a month: see paid hours against billed hours, the unbilled labour cost, the share of the shop total, the rank of the month and the three people with the biggest gap.', [
    I('tech', 'Technician', key('crew', 'Kofi Mensah'), 'list', list='crew'), I('month', 'Month (the 1st)', iso(month_start(1)), 'date'), I('amber', 'Unbilled cost counted as amber', 2500)], [
    O('Paid hours', 'num', G2('paid_hours')), O('Billed hours', 'num', G2('billed_hours')), O('Paid minus billed hours', 'num', G2('unbilled_hours')), O('Unbilled labour cost', 'money', UB2),
    O('Unbilled labour cost of the whole crew', 'money', SHOP2), O('Share of the crew total', 'pct', 'IFERROR(%s/%s,0)' % (UB2, SHOP2)),
    O('Rank in the month (1 is the biggest gap)', 'int', 'IFERROR(AVERAGEIFS(%s,%s,{in:tech},%s,{in:month}),0)' % (TS('tm_rank'), TS('technician'), TS('month'))),
    O('Biggest gap: person', 'text', RK(1, 'technician')), O('Biggest gap: cost', 'money', RK(1, 'tm_unbilled')), O('Second gap: person', 'text', RK(2, 'technician')), O('Second gap: cost', 'money', RK(2, 'tm_unbilled')),
    O('Third gap: person', 'text', RK(3, 'technician')), O('Third gap: cost', 'money', RK(3, 'tm_unbilled')),
    O('Traffic light', 'text', 'IF(%s>=2*{in:amber},%s,IF(%s>={in:amber},%s,%s))' % (UB2, ck('Red'), UB2, ck('Amber'), ck('Green')))],
  GR('What if', ('Diego Morales', {'tech': '=' + tok('crew', 'Diego Morales')}), ('Liam O\'Connell', {'tech': '=' + tok('crew', "Liam O'Connell")}), ('Tomasz Nowak', {'tech': '=' + tok('crew', 'Tomasz Nowak')}),
     ('Amber at 1500', {'amber': 1500}), ('Amber at 4000', {'amber': 4000}))))

# 3 utilisation trend
def HWN(c_): return 'SUMIFS(%s,%s,">="&(%s-7*({in:weeks}-1)),%s,"<="&%s)' % (HW(c_), HW('week'), LW, HW('week'), LW)
UT3 = 'IFERROR(%s/%s,0)' % (HWN('billed_hours'), HWN('clock_hours'))
LY3 = 'IFERROR(AVERAGEIFS(%s,%s,">="&(%s-7*({in:weeks}-1)),%s,"<="&%s),0)' % (HW('util_ly'), HW('week'), LW, HW('week'), LW)
tools.append(TOOL('util_trend', 'Utilisation Trend', 'Utilisation by week against the target and last year',
  'Type how many weeks to look back: see utilisation against the target and against the same weeks last year, the weeks below the target and the hours to fill with tune-ups.', [
    I('weeks', 'Weeks to look back (1 to 26)', 13, 'int'), I('tuneup_hours', 'Hours of one tune-up, drive included', 1.6, 'num')], [
    O('Billed hours', 'num', HWN('billed_hours')), O('Clock hours', 'num', HWN('clock_hours')), O('Utilisation', 'pct', UT3), O('Utilisation target', 'pct', '{set:util_target}'), O('Gap to the target, points', 'pct', UT3 + '-{set:util_target}'),
    O('Same weeks last year', 'pct', LY3), O('Change against last year, points', 'pct', UT3 + '-' + LY3),
    O('Weeks below the target', 'int', 'COUNTIFS(%s,">="&(%s-7*({in:weeks}-1)),%s,"<="&%s,%s,"<0")' % (HW('week'), LW, HW('week'), LW, HW('gap_to_target'))),
    O('Lowest week of the last 26', 'pct', 'SMALL(%s,1)' % HW('utilisation')), O('Week of the lowest utilisation', 'date', 'INDEX(%s,MATCH(SMALL(%s,1),%s,0))' % (HW('week'), HW('utilisation'), HW('utilisation'))),
    O('Hours to fill to reach the target', 'num', HWN('shortfall')), O('Tune-ups to book to fill them', 'int', 'ROUNDUP(%s/{in:tuneup_hours},0)' % HWN('shortfall')),
    O('Verdict', 'text', 'IF(%s>={set:util_target},%s,IF(%s>%s,%s,%s))' % (UT3, ck('On target'), UT3, LY3, ck('Below target but better than last year'), ck('Fill the slow weeks with tune-ups')))],
  GR('What if', ('Last 4 weeks', {'weeks': 4}), ('Last 8 weeks', {'weeks': 8}), ('Last 26 weeks', {'weeks': 26}), ('Tune-up of 2.2 hours', {'tuneup_hours': 2.2}))))

# 4 pay calculator
PM = 'IF({in:model}=%s,%s,IF({in:model}=%s,%s,IF({in:model}=%s,%s,%s)))'
HOURLY = '(MIN({in:hours},{set:overtime_after})*{in:rate}+MAX(0,{in:hours}-{set:overtime_after})*{in:rate}*{set:overtime_mult})'
FLATP = '({in:billed}*{in:flat})'
SALCOM = '({in:salary}+{in:sold}*{in:comm})'
MIXED = '({in:mix}*%s+(1-{in:mix})*%s)' % (HOURLY, FLATP)
GROSS4 = PM % (tok('paymodel', 'Hourly'), HOURLY, tok('paymodel', 'Flat rate'), FLATP, tok('paymodel', 'Salary plus commission'), SALCOM, MIXED)
PAYIN = [I('model', 'Pay model', key('paymodel', 'Mixed'), 'list', list='paymodel'), I('hours', 'Hours on the clock in the week', 44, 'num'), I('billed', 'Billed hours in the week', 31, 'num'),
         I('rate', 'Hourly rate', 34), I('flat', 'Pay for each billed hour (flat rate)', 46), I('salary', 'Weekly salary', 1050), I('sold', 'Work sold in the week', 6000), I('comm', 'Commission percent', 0.02, 'pct'), I('mix', 'Share paid by the clock hour (mixed)', 0.6, 'pct')]
tools.append(TOOL('pay_calc', 'Pay Calculator', 'Weekly pay and all-in cost under any pay model',
  'Pick a pay model and type the hours, billed hours, rates and sales of the week: see gross pay, overtime, employer extras from Settings, the all-in cost per clock hour and per billed hour. Confirm pay rules with your adviser.', PAYIN, [
    O('Gross pay for the model', 'money', GROSS4), O('Overtime hours', 'num', 'MAX(0,{in:hours}-{set:overtime_after})'), O('Overtime pay, if paid by the hour', 'money', 'MAX(0,{in:hours}-{set:overtime_after})*{in:rate}*{set:overtime_mult}'),
    O('Employer extras', 'money', GROSS4 + '*{set:burden_pct}'), O('All-in cost of the week', 'money', GROSS4 + '*(1+{set:burden_pct})'),
    O('All-in cost per clock hour', 'money', 'IFERROR(%s*(1+{set:burden_pct})/{in:hours},0)' % GROSS4), O('All-in cost per billed hour', 'money', 'IFERROR(%s*(1+{set:burden_pct})/{in:billed},0)' % GROSS4),
    O('Gross pay if paid by the hour', 'money', HOURLY), O('Difference against hourly pay', 'money', GROSS4 + '-' + HOURLY),
    O('Verdict', 'text', 'IF(%s<=%s,%s,%s)' % (GROSS4, HOURLY, ck('Cheaper than hourly pay'), ck('Dearer than hourly pay'))), O('Reminder', 'text', ck('Confirm pay rules with your adviser'))],
  GR('What if', ('Hourly', {'model': '=' + tok('paymodel', 'Hourly')}), ('Flat rate', {'model': '=' + tok('paymodel', 'Flat rate')}), ('Salary plus commission', {'model': '=' + tok('paymodel', 'Salary plus commission')}),
     ('Mixed, 40 hours', {'hours': 40}), ('Mixed, 50 hours', {'hours': 50, 'billed': 36}))))

# 5 margin per technician
tools.append(TOOL('tech_margin', 'Margin per Technician', 'Does a technician cover the all-in cost',
  'Pick a lead technician: see revenue and job margin of the last 13 weeks, the cost of paid but unbilled time, the margin after it, the rank and a verdict against your overhead share.', [
    I('tech', 'Technician', key('tech', 'Jamal Whitfield'), 'list', list='tech'), I('overhead', 'Overhead share to cover in 13 weeks (your own)', 14000)], [
    O('Revenue, 13 weeks', 'money', SCV('revenue_w')), O('Job margin, 13 weeks', 'money', SCV('gp_w')), O('Loaded pay, 13 weeks', 'money', 'SUMIFS(%s,%s,{in:tech},%s)' % (TS('loaded_cost'), TS('technician'), WK(13))),
    O('Cost of paid but unbilled time', 'money', SCV('unbilled_w')), O('Margin after unbilled time', 'money', SCV('net_margin')), O('Margin after unbilled time, share of revenue', 'pct', 'IFERROR(%s/%s,0)' % (SCV('net_margin'), SCV('revenue_w'))),
    O('Rank among the lead technicians', 'int', 'COUNTIF(%s,">"&%s)+1' % (SC('net_13'), SCV('net_margin'))),
    O('Best technician', 'text', 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (SC('technician'), SC('net_13'), SC('net_13'))), O('Lowest technician', 'text', 'INDEX(%s,MATCH(MIN(%s),%s,0))' % (SC('technician'), SC('net_13'), SC('net_13'))),
    O('Covers the overhead share with', 'money', 'MAX(0,%s-{in:overhead})' % SCV('net_margin')), O('Below the overhead share by', 'money', 'MAX(0,{in:overhead}-%s)' % SCV('net_margin')),
    O('Verdict', 'text', 'IF(%s>={in:overhead},%s,%s)' % (SCV('net_margin'), ck('Covers cost'), ck('Below cost')))],
  GR('What if', ('Diego Morales', {'tech': '=' + tok('tech', 'Diego Morales')}), ('Tomasz Nowak', {'tech': '=' + tok('tech', 'Tomasz Nowak')}), ('Sven Andersson', {'tech': '=' + tok('tech', 'Sven Andersson')}),
     ('Overhead 20000', {'overhead': 20000}), ('Overhead 8000', {'overhead': 8000}))))

# 6 pay model comparison
CMP_IN = [i for i in PAYIN if i['key'] != 'model']
GM = [HOURLY, FLATP, SALCOM, MIXED]; MNAMES = ['Hourly', 'Flat rate', 'Salary plus commission', 'Mixed']
MIN6 = 'MIN(%s)' % ','.join(GM); MAX6 = 'MAX(%s)' % ','.join(GM)
def PICK6(target): return 'IF(%s=%s,%s,IF(%s=%s,%s,IF(%s=%s,%s,%s)))' % (GM[0], target, tok('paymodel', MNAMES[0]), GM[1], target, tok('paymodel', MNAMES[1]), GM[2], target, tok('paymodel', MNAMES[2]), tok('paymodel', MNAMES[3]))
tools.append(TOOL('pay_compare', 'Pay Model Comparison', 'The same week under each pay model',
  'Type one week of hours, billed hours and sales: see gross pay and the all-in cost of the shop under each pay model, the cheapest model for the shop and the best for the technician. Confirm pay rules with your adviser.', CMP_IN, [
    O('Gross pay, hourly', 'money', GM[0]), O('Gross pay, flat rate', 'money', GM[1]), O('Gross pay, salary plus commission', 'money', GM[2]), O('Gross pay, mixed', 'money', GM[3]),
    O('All-in cost, hourly', 'money', GM[0] + '*(1+{set:burden_pct})'), O('All-in cost, flat rate', 'money', GM[1] + '*(1+{set:burden_pct})'), O('All-in cost, salary plus commission', 'money', GM[2] + '*(1+{set:burden_pct})'),
    O('All-in cost, mixed', 'money', GM[3] + '*(1+{set:burden_pct})'), O('Cheapest model for the shop', 'text', PICK6(MIN6)), O('Best model for the technician', 'text', PICK6(MAX6)),
    O('Gap between the best and the cheapest, gross', 'money', MAX6 + '-' + MIN6), O('Verdict', 'text', 'IF(%s=%s,%s,%s)' % (PICK6(MIN6), PICK6(MAX6), ck('One model suits both'), ck('Models pull apart')))],
  GR('What if', ('Busy week, 50 hours', {'hours': 50, 'billed': 38, 'sold': 9000}), ('Slow week, 32 hours', {'hours': 32, 'billed': 14, 'sold': 1500}), ('Higher flat pay', {'flat': 55}), ('Higher commission', {'comm': 0.035}))))

# 7 commission calculator
SM = lambda c_: 'SUMIFS(%s,%s,{in:tech},%s,{in:month})' % (ST_(c_), ST_('technician'), ST_('month'))
BASE7 = 'IF({in:base}=%s,%s,%s)' % (tok('cbase', 'Sold'), SM('sold'), SM('collected'))
RATE7 = 'IFERROR(INDEX({range:team.commission_pct},MATCH({in:tech},{range:team.name},0)),0)'
EXTRA7 = 'MAX(0,%s-{in:threshold})*{in:extra}' % BASE7
tools.append(TOOL('commission_calc', 'Commission Calculator', 'Commission on sold or collected work with a higher tier',
  'Pick a technician, a month and the base: see commission at the technician percent, the extra percent above your threshold, spiffs, clawback and the total for the statement. Set your own rules, confirm with your adviser.', [
    I('tech', 'Technician', key('tech', 'Tomasz Nowak'), 'list', list='tech'), I('month', 'Month (the 1st)', iso(month_start(1)), 'date'), I('base', 'Paid on', key('cbase', 'Sold'), 'list', list='cbase'),
    I('threshold', 'Tier threshold: work above this earns the extra percent', 20000), I('extra', 'Extra percent above the threshold', 0.005, 'pct')], [
    O('Sold in the month', 'money', SM('sold')), O('Collected in the month', 'money', SM('collected')), O('Base used', 'money', BASE7), O('Commission percent of the technician', 'pct', RATE7),
    O('Commission at the flat percent', 'money', BASE7 + '*' + RATE7), O('Extra above the threshold', 'money', EXTRA7), O('Commission with the tier', 'money', '%s*%s+%s' % (BASE7, RATE7, EXTRA7)),
    O('Spiffs', 'money', SM('spiffs')), O('Clawback', 'money', SM('clawback')), O('Total for the statement', 'money', '%s*%s+%s+%s-%s' % (BASE7, RATE7, EXTRA7, SM('spiffs'), SM('clawback'))),
    O('Commission if paid on the other base', 'money', 'IF({in:base}=%s,%s,%s)*%s' % (tok('cbase', 'Sold'), SM('collected'), SM('sold'), RATE7)),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (EXTRA7, ck('The tier applies'), ck('Below the tier')))],
  GR('What if', ('Paid on collected', {'base': '=' + tok('cbase', 'Collected')}), ('Threshold 10000', {'threshold': 10000}), ('Extra percent 1', {'extra': 0.01}), ('Diego Morales', {'tech': '=' + tok('tech', 'Diego Morales')}),
     ('Jamal Whitfield', {'tech': '=' + tok('tech', 'Jamal Whitfield')}))))

# 8 clawback tool
MN8 = '%s,">="&{in:month},%s,"<"&EDATE({in:month},1)' % (CB('date'), CB('date'))
CBN = 'COUNTIFS(%s,{in:tech},%s)' % (CB('technician'), MN8)
CBW = 'COUNTIFS(%s,{in:tech},%s,%s,"<="&{in:days})' % (CB('technician'), MN8, CB('days_after'))
CBV = 'SUMIFS(%s,%s,{in:tech},%s,%s,"<="&{in:days})' % (CB('job_price'), CB('technician'), MN8, CB('days_after'))
UNP8 = 'SUMIFS(%s,%s,{in:tech},%s,{in:month})' % (ST_('unpaid_base'), ST_('technician'), ST_('month'))
CLW = '((%s+%s)*%s*{in:pct})' % (CBV, UNP8, RATE7)
tools.append(TOOL('clawback_tool', 'Clawback Tool', 'Commission to hold back for callbacks and unpaid invoices',
  'Pick a technician and a month: see the callbacks and unpaid invoices inside your clawback days, the value of the commissioned jobs hit, the amount to hold back and the rule that applied. Set your own rule, confirm with your adviser.', [
    I('tech', 'Technician', key('tech', 'Diego Morales'), 'list', list='tech'), I('month', 'Month (the 1st)', iso(month_start(0)), 'date'), I('days', 'Clawback days', 60, 'int'), I('pct', 'Share of the commission taken back', 0.5, 'pct')], [
    O('Callbacks in the month', 'int', CBN), O('Callbacks inside the clawback days', 'int', CBW), O('Value of the commissioned jobs hit', 'money', CBV), O('Unpaid invoices over the clawback days', 'money', UNP8),
    O('Commission percent', 'pct', RATE7), O('Amount to hold back', 'money', CLW), O('Commission of the month', 'money', 'SUMIFS(%s,%s,{in:tech},%s,{in:month})' % (ST_('commission'), ST_('technician'), ST_('month'))),
    O('Share of the commission held back', 'pct', 'IFERROR(%s/SUMIFS(%s,%s,{in:tech},%s,{in:month}),0)' % (CLW, ST_('commission'), ST_('technician'), ST_('month'))),
    O('Rule that applied', 'text', 'IF(AND(%s>0,%s>0),%s,IF(%s>0,%s,IF(%s>0,%s,%s)))' % (CBV, UNP8, ck('Callback and unpaid invoice'), CBV, ck('Callback inside the window'), UNP8, ck('Unpaid invoice'), ck('No clawback'))),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (CLW, ck('Hold back'), ck('No hold back')))],
  GR('What if', ('Jamal Whitfield', {'tech': '=' + tok('tech', 'Jamal Whitfield')}), ('Window of 30 days', {'days': 30}), ('Window of 90 days', {'days': 90}), ('Take back all', {'pct': 1}), ('Kofi Mensah', {'tech': '=' + tok('tech', 'Kofi Mensah')}))))

# 9 technician statement
SM9 = lambda c_: 'SUMIFS(%s,%s,{in:tech},%s,{in:month})' % (ST_(c_), ST_('technician'), ST_('month'))
tools.append(TOOL('tech_statement', 'Technician Statement', 'A month a technician can read: hours, sales and pay',
  'Pick a technician and a month: see hours, jobs, sales, collections, commission, spiffs, clawbacks and the total to pay, written so the technician can follow it. Confirm pay rules with your adviser.', [
    I('tech', 'Technician', key('tech', 'Tomasz Nowak'), 'list', list='tech'), I('month', 'Month (the 1st)', iso(month_start(1)), 'date')], [
    O('Hours on the clock', 'num', 'SUMIFS(%s,%s,{in:tech},%s,{in:month})' % (TS('clock_hours'), TS('technician'), TS('month'))), O('Billed hours', 'num', 'SUMIFS(%s,%s,{in:tech},%s,{in:month})' % (TS('billed_hours'), TS('technician'), TS('month'))),
    O('Jobs done', 'int', SM9('jobs_done')), O('Sales', 'money', SM9('sold')), O('Collected', 'money', SM9('collected')), O('Commission', 'money', SM9('commission')), O('Spiffs', 'money', SM9('spiffs')),
    O('Clawback', 'money', SM9('clawback')), O('Total commission and spiffs after clawback', 'money', SM9('total')), O('Gross pay for the hours', 'money', 'SUMIFS(%s,%s,{in:tech},%s,{in:month})' % (TS('gross_pay'), TS('technician'), TS('month'))),
    O('Gross pay plus commission and spiffs', 'money', 'SUMIFS(%s,%s,{in:tech},%s,{in:month})+%s' % (TS('gross_pay'), TS('technician'), TS('month'), SM9('total'))), O('Reminder', 'text', ck('Confirm pay rules with your adviser'))],
  GR('What if', ('Kofi Mensah', {'tech': '=' + tok('tech', 'Kofi Mensah')}), ('Elena Rossi', {'tech': '=' + tok('tech', 'Elena Rossi')}), ('Jamal Whitfield', {'tech': '=' + tok('tech', 'Jamal Whitfield')}), ('Sven Andersson', {'tech': '=' + tok('tech', 'Sven Andersson')}), ('Diego Morales', {'tech': '=' + tok('tech', 'Diego Morales')}))))

# 10 spiff tracker
AG10 = 'SUMIFS(%s,%s,{in:tech},%s,">="&EDATE(%s,-{in:months}),%s,"<="&%s)' % (ST_('agreements'), ST_('technician'), ST_('month'), MS, ST_('month'), MS)
AGALL = 'SUMIFS(%s,%s,">="&EDATE(%s,-{in:months}),%s,"<="&%s)' % (ST_('agreements'), ST_('month'), MS, ST_('month'), MS)
SP = lambda it: 'SUMIFS({range:spiffs.amount},{range:spiffs.item},%s)' % tok('spiffitem', it)
OTH10 = '({in:thermostats}*%s+{in:filters}*%s+{in:better}*%s+{in:best}*%s)' % (SP('Thermostat added'), SP('Water filter added'), SP('Better option sold'), SP('Best option sold'))
tools.append(TOOL('spiff_tracker', 'Spiff Tracker', 'Spiffs earned and what a spiff costs the shop',
  'Pick a technician and a number of months: see the maintenance agreements sold and their spiffs, the cost of a spiff against the value of an agreement, and what typed add-ons and options would pay.', [
    I('tech', 'Technician', key('tech', 'Sven Andersson'), 'list', list='tech'), I('months', 'Months to look back', 6, 'int'), I('plan_price', 'Average yearly price of an agreement', 249),
    I('thermostats', 'Thermostats added (what if)', 4, 'int'), I('filters', 'Water filters added (what if)', 3, 'int'), I('better', 'Better options sold (what if)', 5, 'int'), I('best', 'Best options sold (what if)', 2, 'int')], [
    O('Agreements sold', 'int', AG10), O('Spiffs for agreements', 'money', AG10 + '*' + SP('Maintenance agreement sold')), O('Agreements sold by the whole crew', 'int', AGALL),
    O('Share of the agreements sold', 'pct', 'IFERROR(%s/%s,0)' % (AG10, AGALL)), O('Value of the agreements sold, first year', 'money', AG10 + '*{in:plan_price}'),
    O('Spiff cost per agreement sold', 'money', SP('Maintenance agreement sold')), O('Spiff as a share of the agreement value', 'pct', 'IFERROR(%s/{in:plan_price},0)' % SP('Maintenance agreement sold')),
    O('Spiffs for the add-ons typed', 'money', OTH10), O('All spiffs, agreements and add-ons typed', 'money', AG10 + '*' + SP('Maintenance agreement sold') + '+' + OTH10),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s/{in:plan_price}<=0.15,%s,%s))' % (AG10, ck('Ask for agreements'), SP('Maintenance agreement sold'), ck('The spiff pays for itself'), ck('The spiff is rich')))],
  GR('What if', ('Tomasz Nowak', {'tech': '=' + tok('tech', 'Tomasz Nowak')}), ('Kofi Mensah', {'tech': '=' + tok('tech', 'Kofi Mensah')}), ('Last 3 months', {'months': 3}), ('Last 9 months', {'months': 9}), ('Cheap plan at 189', {'plan_price': 189}))))

# 11 scorecard tool
def PT(a, op, b): return 'IF(%s%s%s,%s,%s)' % (a, op, b, ck('Good'), ck('Check'))
tools.append(TOOL('scorecard_tool', 'Technician Scorecard', 'Six measures against your targets and each own history',
  'Pick a lead technician: see ticket, close rate, callback rate, utilisation, revenue per day and reviews against your targets and the technician own 12 months, the points, the rank, the verdict and the topic for the one-to-one talk.', [
    I('tech', 'Technician', key('tech', 'Kofi Mensah'), 'list', list='tech'), I('note', 'Note for the one-to-one talk', 'Agree one change to try this month', 'text')], [
    O('Average ticket, 13 weeks', 'money', SCV('ticket')), O('Average ticket, own 12 months', 'money', SCV('ticket_12m')), O('Close rate', 'pct', SCV('close_rate')), O('Callback rate', 'pct', SCV('callback_rate')),
    O('Utilisation, 4 weeks', 'pct', SCV('util_w', 'Last 4 weeks')), O('Utilisation, own 12 months', 'pct', SCV('util_12m')), O('Revenue per day, 13 weeks', 'money', SCV('rev_day')), O('Revenue per day, own 12 months', 'money', SCV('rev_day_12m')),
    O('Reviews, last 3 months', 'int', SCV('reviews_90')), O('Points of 6', 'int', SCV('points')), O('Rank among the lead technicians', 'int', SCV('rank_pts')),
    O('Talk about first', 'text', 'IF(%s>{set:callback_target},%s,IF(%s<{set:close_target},%s,IF(%s<{set:util_target},%s,IF(%s<%s,%s,%s))))' % (SCV('callback_rate'), ck('Callback rate'), SCV('close_rate'), ck('Close rate'), SCV('util_w', 'Last 4 weeks'), ck('Utilisation'), SCV('ticket'), SCV('ticket_12m'), ck('Ticket'), ck('Reviews'))),
    O('Verdict', 'text', 'IF(%s>=5,%s,IF(%s>=3,%s,%s))' % (SCV('points'), ck('Strong'), SCV('points'), ck('Watch'), ck('Talk'))), O('Your note', 'text', '{in:note}')],
  GR('What if', ('Tomasz Nowak', {'tech': '=' + tok('tech', 'Tomasz Nowak')}), ('Elena Rossi', {'tech': '=' + tok('tech', 'Elena Rossi')}), ('Jamal Whitfield', {'tech': '=' + tok('tech', 'Jamal Whitfield')}),
     ('Sven Andersson', {'tech': '=' + tok('tech', 'Sven Andersson')}), ('Diego Morales', {'tech': '=' + tok('tech', 'Diego Morales')}))))

# 12 revenue per day
SHOPRD = 'IFERROR(SUM(%s)/SUM(%s),0)' % (SC('rev_13'), SC('days_13'))
tools.append(TOOL('rev_day_tool', 'Revenue per Day', 'Revenue and margin per working day',
  'Pick a lead technician: see revenue, job margin and jobs per working day of the last 13 weeks against the shop average and the technician own last 12 months.', [
    I('tech', 'Technician', key('tech', 'Elena Rossi'), 'list', list='tech')], [
    O('Working days, 13 weeks', 'num', SCV('days_w')), O('Revenue per day', 'money', SCV('rev_day')), O('Job margin per day', 'money', 'IFERROR(%s/%s,0)' % (SCV('gp_w'), SCV('days_w'))),
    O('Jobs per day', 'num', 'IFERROR(%s/%s,0)' % (SCV('jobs_w'), SCV('days_w'))), O('Shop average revenue per day', 'money', SHOPRD), O('Against the shop average', 'pct', 'IFERROR(%s/%s-1,0)' % (SCV('rev_day'), SHOPRD)),
    O('Own revenue per day, 12 months', 'money', SCV('rev_day_12m')), O('Against the own 12 months', 'pct', 'IFERROR(%s/%s-1,0)' % (SCV('rev_day'), SCV('rev_day_12m'))),
    O('Verdict', 'text', 'IF(AND(%s>=%s,%s>=%s),%s,IF(%s<%s,%s,%s))' % (SCV('rev_day'), SHOPRD, SCV('rev_day'), SCV('rev_day_12m'), ck('Above shop and own history'), SCV('rev_day'), SHOPRD, ck('Below the shop average'), ck('Below own history')))],
  GR('What if', ('Tomasz Nowak', {'tech': '=' + tok('tech', 'Tomasz Nowak')}), ('Kofi Mensah', {'tech': '=' + tok('tech', 'Kofi Mensah')}), ('Jamal Whitfield', {'tech': '=' + tok('tech', 'Jamal Whitfield')}),
     ('Sven Andersson', {'tech': '=' + tok('tech', 'Sven Andersson')}), ('Diego Morales', {'tech': '=' + tok('tech', 'Diego Morales')}))))

# 13 overtime warning
OT_ = lambda c_: '{range:overtime_tech.%s}' % c_
TOPN = 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (OT_('technician'), OT_('overtime_hours'), OT_('overtime_hours'))
TOPR = 'IFERROR(INDEX({range:team.hourly_rate},MATCH(%s,{range:team.name},0)),0)' % TOPN
tools.append(TOOL('overtime_warning', 'Overtime and Capacity Warning', 'Who works too many hours and what it costs',
  'Type the weekly hour threshold and the 4-week limit: see the people over the threshold, overtime hours and cost, the technician with the most overtime and a verdict to spread jobs, hire or leave it. Confirm overtime rules with your adviser.', [
    I('threshold', 'Paid hours a week that count as overtime', 40, 'int'), I('limit', 'Overtime hours in 4 weeks that trigger a talk', 8, 'int'), I('mult', 'Overtime pay multiplier', 1.5, 'num')], [
    O('Person-weeks over the threshold, last 12 weeks', 'int', 'COUNTIFS(%s,">"&{in:threshold},%s)' % (TS('paid_hours'), WK(12))), O('Overtime hours, last 4 weeks', 'num', 'SUM(%s)' % OT_('overtime_hours')),
    O('Overtime cost, last 4 weeks', 'money', 'SUM(%s)' % OT_('overtime_cost')), O('Technicians over the limit', 'int', 'COUNTIFS(%s,">"&{in:limit})' % OT_('overtime_hours')),
    O('Technician with the most overtime', 'text', TOPN), O('Overtime hours of that technician', 'num', 'MAX(%s)' % OT_('overtime_hours')),
    O('Cost of those hours at the multiplier', 'money', 'MAX(%s)*%s*{in:mult}*(1+{set:burden_pct})' % (OT_('overtime_hours'), TOPR)),
    O('Weeks over the threshold, last 12 weeks', 'int', 'COUNTIFS(%s,%s,%s,">"&{in:threshold},%s)' % (TS('technician'), TOPN, TS('paid_hours'), WK(12))),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">"&{in:limit})=0,%s,IF(COUNTIFS(%s,%s,%s,">"&{in:threshold},%s)>=3,%s,%s))' % (OT_('overtime_hours'), ck('Fine'), TS('technician'), TOPN, TS('paid_hours'), WK(12), ck('Hire'), ck('Spread the jobs')))],
  GR('What if', ('Threshold 38', {'threshold': 38}), ('Threshold 44', {'threshold': 44}), ('Limit 4', {'limit': 4}), ('Limit 14', {'limit': 14}), ('Multiplier 2', {'mult': 2}))))

# 14 booked versus available
CW = lambda c_: '{range:capacity_week.%s}' % c_
WN14 = '%s,">="&%s,%s,"<="&(%s+7*({in:weeks}-1))' % (CW('week'), TW, CW('week'), TW)
AV14, BK14 = 'SUMIFS(%s,%s)' % (CW('available_hours'), WN14), 'SUMIFS(%s,%s)+{in:extra}*{in:weeks}' % (CW('booked_hours'), WN14)
tools.append(TOOL('booked_available', 'Booked vs Available Hours', 'Weeks over capacity and weeks with room',
  'Type the weeks ahead and any extra hours a week: see booked hours against the hours your technicians can work, the weeks over capacity, the tightest and the roomiest week and a verdict.', [
    I('weeks', 'Weeks ahead (1 to 25)', 13, 'int'), I('extra', 'Extra booked hours a week (what if)', 0, 'num')], [
    O('Available hours', 'num', AV14), O('Booked and expected hours', 'num', BK14), O('Gap', 'num', AV14 + '-(' + BK14 + ')'), O('Capacity used', 'pct', 'IFERROR((%s)/%s,0)' % (BK14, AV14)),
    O('Weeks over capacity', 'int', 'COUNTIFS(%s,%s,"<"&{in:extra})' % (WN14, CW('gap'))), O('Weeks with more than 20 percent room', 'int', 'COUNTIFS(%s,%s,">"&(0.2*AVERAGEIFS(%s,%s)+{in:extra}))' % (WN14, CW('gap'), CW('available_hours'), WN14)),
    O('Tightest week', 'date', 'INDEX(%s,MATCH(SMALL(%s,1),%s,0))' % (CW('week'), CW('fgap'), CW('fgap'))), O('Gap in the tightest week', 'num', 'SMALL(%s,1)-{in:extra}' % CW('fgap')),
    O('Roomiest week', 'date', 'INDEX(%s,MATCH(LARGE(%s,1),%s,0))' % (CW('week'), CW('fgap'), CW('fgap'))), O('Gap in the roomiest week', 'num', 'LARGE(%s,1)-{in:extra}' % CW('fgap')),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,%s,"<"&{in:extra})=0,%s,IF(COUNTIFS(%s,%s,"<"&{in:extra})>=3,%s,%s))' % (WN14, CW('gap'), ck('Enough capacity'), WN14, CW('gap'), ck('Add capacity'), ck('Spread the work')))],
  GR('What if', ('4 weeks ahead', {'weeks': 4}), ('8 weeks ahead', {'weeks': 8}), ('25 weeks ahead', {'weeks': 25}), ('10 extra hours a week', {'extra': 10}), ('30 extra hours a week', {'extra': 30}))))

# 15 capacity and hire
HS = lambda c_: 'AVERAGEIFS({range:hire_scenarios.%s},{range:hire_scenarios.option},{in:option})' % c_
W4N = 'COUNTIFS(%s,%s,%s,">"&%s,%s,"<="&(%s+28),%s,"<0")' % (CW('week'), CW('week'), CW('week'), LW, CW('week'), LW, CW('gap')) if False else 'COUNTIFS(%s,">"&%s,%s,"<="&(%s+28),%s,"<0")' % (CW('week'), LW, CW('week'), LW, CW('gap'))
W13N = 'COUNTIFS(%s,">"&%s,%s,"<="&(%s+91),%s,"<0")' % (CW('week'), LW, CW('week'), LW, CW('gap'))
SHORT13 = '-SUMIFS(%s,%s,">"&%s,%s,"<="&(%s+91),%s,"<0")' % (CW('gap'), CW('week'), LW, CW('week'), LW, CW('gap'))
ADD = '5*{set:capacity_hours}*IF({in:option}=%s,0.5,1)' % tok('hireopt', 'Apprentice')
tools.append(TOOL('hire_tool', 'Capacity and Hire Tool', 'Hire a technician or an apprentice?',
  'Pick a hire option and a ramp-up: see the monthly cost, the jobs a week needed to break even, the hours added a week, the weeks you are over capacity and a verdict to hire now, hire before the season or wait.', [
    I('option', 'Hire option', key('hireopt', 'HVAC technician'), 'list', list='hireopt'), I('ramp', 'Ramp-up months before full productivity', 4, 'int')], [
    O('Monthly cost, all in', 'money', HS('monthly_cost')), O('Cost of the ramp-up', 'money', HS('monthly_cost') + '*{in:ramp}*0.5'), O('Margin a job adds before technician pay', 'money', HS('contribution')),
    O('Jobs a week to break even', 'num', HS('jobs_week')), O('Jobs a week the shop does now, 13 weeks', 'num', 'COUNTIFS(%s,%s,%s,%s,%s)/13' % (JB('status'), COMP, JB('callback'), NO, J13)),
    O('Hours added a week', 'num', ADD), O('Weeks over capacity, next 4', 'int', W4N), O('Weeks over capacity, next 13', 'int', W13N), O('Hours short in the next 13 weeks', 'num', SHORT13),
    O('Hours the hire adds in 13 weeks', 'num', ADD + '*13'),
    O('Verdict', 'text', 'IF(%s>=2,%s,IF(%s>=1,%s,%s))' % (W4N, ck('Hire now'), W13N, ck('Hire before the season'), ck('Wait')))],
  GR('What if', ('Apprentice', {'option': '=' + tok('hireopt', 'Apprentice')}), ('Service plumber', {'option': '=' + tok('hireopt', 'Service plumber')}), ('Lead HVAC tech', {'option': '=' + tok('hireopt', 'Lead HVAC tech')}),
     ('Ramp-up of 2 months', {'ramp': 2}), ('Ramp-up of 6 months', {'ramp': 6}))))

# 16 hire break-even solver
UF = '(1+{in:util_change})'
J16 = 'IFERROR({in:cost}/({in:contribution}*%s),0)' % UF
J16T = 'IF({in:contribution}-{in:net}*{in:price}>0,{in:cost}/(({in:contribution}-{in:net}*{in:price})*%s),0)' % UF
tools.append(TOOL('hire_breakeven', 'Hire Break-Even Solver', 'Extra jobs a week a new technician must bring',
  'Type the monthly all-in cost of a hire, the margin a job adds and the price: see the jobs a week that cover the cost, the jobs that also earn your net target, and the same at 10 percent less or more utilisation.', [
    I('cost', 'Monthly cost of the hire, all in', 7700), I('contribution', 'Margin a job adds before technician pay', 390), I('price', 'Average price of a job', 610), I('net', 'Net profit wanted on the new work', 0.12, 'pct'),
    I('hours_job', 'Hours of one job, drive included', 2.3, 'num'), I('util_change', 'Utilisation change, plus or minus', 0, 'pct')], [
    O('Jobs a month to cover the cost', 'num', J16), O('Jobs a week to cover the cost', 'num', J16 + '/(52/12)'), O('Revenue a month needed', 'money', J16 + '*{in:price}'),
    O('Jobs a week to cover the cost and the net target', 'num', J16T + '/(52/12)'), O('Revenue a month to earn the net target', 'money', J16T + '*{in:price}'),
    O('Jobs a week one technician can do', 'num', '5*{set:capacity_hours}*{set:util_target}*%s/{in:hours_job}' % UF), O('Share of one technician capacity needed', 'pct', 'IFERROR((%s/(52/12))/(5*{set:capacity_hours}*{set:util_target}*%s/{in:hours_job}),0)' % (J16T, UF)),
    O('Jobs a week at 10 percent less utilisation', 'num', 'IFERROR({in:cost}/({in:contribution}*(1+{in:util_change}-0.1)),0)/(52/12)'), O('Jobs a week at 10 percent more utilisation', 'num', 'IFERROR({in:cost}/({in:contribution}*(1+{in:util_change}+0.1)),0)/(52/12)'),
    O('Verdict', 'text', 'IF(%s/(52/12)<=5*{set:capacity_hours}*{set:util_target}*%s/{in:hours_job},%s,%s)' % (J16T, UF, ck('The hire can pay for itself'), ck('The hire cannot pay for itself')))],
  GR('What if', ('Utilisation minus 10 percent', {'util_change': -0.1}), ('Utilisation plus 10 percent', {'util_change': 0.1}), ('Apprentice cost', {'cost': 4500, 'contribution': 390}), ('Net target 20 percent', {'net': 0.2}), ('Lower job margin', {'contribution': 300}))))

# 17 apprentice ramp
RS = ['r%d' % i for i in range(1, 7)]
MON = lambda i: '({in:hours}*{in:%s}*{in:margin_hour}-{in:hours}*{in:rate}*(1+{set:burden_pct}))' % RS[i]
CUM6 = '(' + '+'.join(MON(i) for i in range(6)) + ')'
GSS = '({in:hours}*{in:steady}*{in:margin_hour}-{in:hours}*{in:rate}*(1+{set:burden_pct}))'
PAYB = 'IF(%s>=0,6,IF(%s>0,6+ROUNDUP(-%s/%s,0),0))' % (CUM6, GSS, CUM6, GSS)
tools.append(TOOL('apprentice_ramp', 'Apprentice Ramp', 'When an apprentice starts to pay back',
  'Type the apprentice rate, the hours and the share of hours billed alongside a lead in each month: see the monthly result, the total after 6 months, the months to pay back and a verdict to invest or delay. Your own estimates; confirm pay rules with your adviser.', [
    I('rate', 'Hourly rate of the apprentice', 21), I('hours', 'Hours on the clock a month', 170, 'num'), I('margin_hour', 'Extra margin per billed hour with a lead (your own)', 45),
    I('r1', 'Billed share, month 1', 0.15, 'pct'), I('r2', 'Billed share, month 2', 0.25, 'pct'), I('r3', 'Billed share, month 3', 0.35, 'pct'), I('r4', 'Billed share, month 4', 0.45, 'pct'), I('r5', 'Billed share, month 5', 0.55, 'pct'),
    I('r6', 'Billed share, month 6', 0.6, 'pct'), I('steady', 'Billed share from month 7', 0.75, 'pct'), I('max_months', 'Longest payback you accept, months', 18, 'int')], [
    O('Monthly cost, all in', 'money', '{in:hours}*{in:rate}*(1+{set:burden_pct})')] + [O('Result of month %d' % (i + 1), 'money', MON(i)) for i in range(6)] + [
    O('Result after 6 months', 'money', CUM6), O('Result of a month from month 7', 'money', GSS), O('Months to pay back (0 means never)', 'int', PAYB),
    O('Verdict', 'text', 'IF(AND(%s>0,%s<={in:max_months}),%s,%s)' % (PAYB, PAYB, ck('Invest'), ck('Delay')))],
  GR('What if', ('Faster ramp', {'r1': 0.25, 'r2': 0.4, 'r3': 0.5, 'r4': 0.6, 'r5': 0.7, 'r6': 0.75, 'steady': 0.85}), ('Slower ramp', {'r1': 0.1, 'r2': 0.15, 'r3': 0.2, 'r4': 0.3, 'r5': 0.4, 'r6': 0.45, 'steady': 0.55}),
     ('Higher rate 24', {'rate': 24}), ('Margin of 35 an hour', {'margin_hour': 35}))))

# 18 payroll cost forecast
SH = lambda c_: '{range:season_hours.%s}' % c_
P13 = 'SUMIFS({range:payroll.total},{range:payroll.month},">="&EDATE(%s,-6),{range:payroll.month},"<"&%s,{range:payroll.pay_type},"<>"&%s)' % (MS, MS, OWNDRAW)
COM6 = 'SUMIFS({range:payroll.commission},{range:payroll.month},">="&EDATE(%s,-6),{range:payroll.month},"<"&%s)*(1+{set:burden_pct})' % (MS, MS)
RATIO = 'IFERROR(AVERAGEIFS(%s,%s,">"&%s,%s,"<="&(%s+91))/AVERAGEIFS(%s,%s,">"&(%s-182),%s,"<="&%s),1)' % (CW('idx'), CW('week'), LW, CW('week'), LW, CW('idx'), CW('week'), LW, CW('week'), LW)
FIX = '((%s-%s)/26)' % (P13, COM6); VAR = '(%s/26)' % COM6
PAY13 = '(13*(%s+%s*%s*{in:mult})+3*{in:extra})' % (FIX, VAR, RATIO)
CASH13 = '({set:cash_now}+13*({in:cash_in}*%s*{in:mult}-{in:other_out})-%s)' % (RATIO, PAY13)
tools.append(TOOL('payroll_forecast', 'Payroll Cost Forecast', 'Payroll for 13 weeks and your cash floor',
  'Type a demand multiplier, any extra monthly cost of a hire and your weekly cash in and other cash out: see payroll for the next 13 weeks from your last 6 months and the season, and the cash left against your floor. Use Base, Best and Worst.', [
    I('mult', 'Demand multiplier (1 is base)', 1, 'num'), I('extra', 'Extra monthly cost of a hire', 0), I('cash_in', 'Cash in a week, average', 44000), I('other_out', 'Other cash out a week, without payroll', 31000)], [
    O('Payroll, last 6 months', 'money', P13), O('Fixed part of payroll a week', 'money', FIX), O('Commission part of payroll a week', 'money', VAR), O('Season factor for the next 13 weeks', 'num', RATIO),
    O('Payroll, next 13 weeks', 'money', PAY13), O('Payroll a week, next 13 weeks', 'money', PAY13 + '/13'), O('Change against the last 6 months a week', 'pct', 'IFERROR(%s/13/((%s)/26)-1,0)' % (PAY13, P13)),
    O('Cash today', 'money', '{set:cash_now}'), O('Cash after 13 weeks', 'money', CASH13), O('Cash floor', 'money', '{set:cash_floor}'), O('Cash after 13 weeks above the floor by', 'money', CASH13 + '-{set:cash_floor}'),
    O('Verdict', 'text', 'IF(%s>={set:cash_floor},%s,%s)' % (CASH13, ck('Above the cash floor'), ck('Below the cash floor')))],
  GR('Scenarios', ('Base', {'mult': 1}), ('Best: demand plus 10 percent', {'mult': 1.1}), ('Worst: demand minus 15 percent', {'mult': 0.85}), ('Base with a hire', {'extra': 7700}), ('Worst with a hire', {'mult': 0.85, 'extra': 7700}))))
assert len(tools) == 18, len(tools)

_H = {
 'hours_analyser': 'Pick a technician and the weeks to look back: clock, billed, drive, shop and idle hours, utilisation against your target, the cost of idle time and who has the most idle hours to take jobs.',
 'pay_calc': 'Pick a pay model and type the week: gross pay, overtime, employer extras, and the all-in cost per clock hour and per billed hour. Confirm pay rules with your adviser.',
 'pay_compare': 'Type one week of hours, billed hours and sales: gross pay and all-in cost under each pay model, the cheapest model for the shop and the best for the technician. Confirm with your adviser.',
 'commission_calc': 'Pick a technician, a month and a base: commission at the technician percent, an extra percent above your threshold, spiffs, clawback and the total. Set your own rules, confirm with your adviser.',
 'clawback_tool': 'Pick a technician and a month: callbacks and unpaid invoices inside your clawback days, the commissioned value hit, the amount to hold back and the rule that applied. Confirm with your adviser.',
 'scorecard_tool': 'Pick a lead technician: six measures against your targets and own 12 months, points, rank, verdict, the first topic for the one-to-one talk and a note box.',
 'overtime_warning': 'Type the weekly threshold and the 4-week limit: people over the threshold, overtime hours and cost, the top technician and a verdict. Confirm overtime rules with your adviser.',
 'hire_tool': 'Pick a hire option and a ramp-up: monthly cost, jobs a week to break even, hours added, weeks over capacity and a verdict: hire now, hire before the season or wait.',
 'hire_breakeven': 'Type the monthly cost of a hire, the margin a job adds and the price: jobs a week to cover the cost and your net target, and the same at 10 percent less or more utilisation.',
 'apprentice_ramp': 'Type the apprentice rate, hours and billed share by month: monthly result, total after 6 months, months to pay back and a verdict. Your own estimates; confirm pay rules with your adviser.',
 'payroll_forecast': 'Type a demand multiplier, extra hire cost and weekly cash flows: payroll for 13 weeks from your last 6 months and the season, and the cash left against your floor. Try Base, Best, Worst.'}
for _t in tools:
    if _t['key'] in _H: _t['hint'] = _H[_t['key']]
    assert len(_t['hint']) <= 200, (_t['key'], len(_t['hint']))
