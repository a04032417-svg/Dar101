"""Home care agency suite part 4: the 18 decision tools (each ends with a verdict and a what-if table)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hc4_lists import *

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='num', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, d): return IN(k, label, 'list', key(lst, d), list=lst)
O = OUT
OT = '{set:overtime_hours}'; BUR = '(1+{set:payroll_burden})'; MULT = '{set:overtime_mult}'
def MS(k=0): return 'DATE(YEAR({today}),MONTH({today})-%d,1)' % k
THIS = 'DATE(YEAR({today}),MONTH({today}),1)'

# 1 payroll line
EV = 'IFERROR(AVERAGEIFS({range:paycard.pay_mult},{range:paycard.band},%s),1)' % tok('band', 'Evening')
NG = 'IFERROR(AVERAGEIFS({range:paycard.pay_mult},{range:paycard.band},%s),1)' % tok('band', 'Night')
OTH1 = '(MAX(0,{in:w1}-%s)+MAX(0,{in:w2}-%s))' % (OT, OT)
REG1 = '({in:w1}+{in:w2}-%s)' % OTH1
C1 = {'reg': 'ROUND(%s*{in:rate},2)' % REG1, 'ot': 'ROUND(%s*{in:rate}*%s,2)' % (OTH1, MULT), 'hol': 'ROUND({in:hol}*{in:rate}*({set:holiday_pay_mult}-1),2)',
      'en': 'ROUND({in:rate}*({in:eve}*(%s-1)+{in:ngt}*(%s-1)),2)' % (EV, NG), 'trv': 'ROUND({in:trav}/60*{in:rate},2)', 'mil': 'ROUND({in:km}*{set:mileage_rate},2)'}
GROSS1 = '(%s+{in:bonus})' % '+'.join(C1.values())
NET1 = '(%s-{in:ded})' % GROSS1
BURD1 = 'ROUND((%s-%s)*{set:payroll_burden},2)' % (GROSS1, C1['mil'])
# 3 midweek
FC3 = '({in:sofar}+{in:still})'
# 4 move visit
def COST4(h, t): return '((MAX(0,{in:%s}+{in:vh}-%s)-MAX(0,{in:%s}-%s))*{in:rate}*(%s-1)+{in:%s}/60*{in:rate})*%s' % (h, OT, h, OT, MULT, t, BUR)
AV4 = '(MAX(0,{in:fh}-%s)-MAX(0,{in:fh}-{in:vh}-%s))' % (OT, OT)
SAV4 = '(%s*{in:fr}*(%s-1)*%s)' % (AV4, MULT, BUR)
MINC4 = 'MIN(%s,%s,%s)' % (COST4('ah', 'at'), COST4('bh', 'bt'), COST4('ch', 'ct'))
# 5 rule test
DAYS = ['d1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7']
TOT5 = '(%s)' % '+'.join('{in:%s}' % d for d in DAYS)
WK5 = 'MAX(0,%s-{in:wline})' % TOT5
DY5 = 'IF({in:dline}>0,%s,0)' % '+'.join('MAX(0,{in:%s}-{in:dline})' % d for d in DAYS)
# 6 share
LH3 = 'SUMIFS({range:otmonth.overtime_hours},{range:otmonth.month},">="&%s,{range:otmonth.month},"<"&%s)' % (MS(3), THIS)
LP3 = 'SUMIFS({range:otmonth.hours},{range:otmonth.month},">="&%s,{range:otmonth.month},"<"&%s)' % (MS(3), THIS)
SY = 'DATE(YEAR({today})-1,MONTH({today}),1)'
# 7 cost per hour
TOT7 = '({in:pay}+{in:otp}+{in:trv}+{in:mil}+{in:bur})'
# 8 ceiling
R3 = 'SUMIFS({range:payratio.total_pay_cost},{range:payratio.month},">="&%s,{range:payratio.month},"<"&%s)/SUMIFS({range:payratio.revenue},{range:payratio.month},">="&%s,{range:payratio.month},"<"&%s)' % (MS(3), THIS, MS(3), THIS)
# 10 holiday
CH10 = '({in:hrs}*{in:bill}*{in:bm})'; CO10 = '({in:hrs}*{in:pay}*{in:pm}*%s)' % BUR
# 11 holiday premium
def CST11(p): return '({in:hrs}*{in:pay}*%s*%s)' % (p, BUR)
def EXP11(p, v): return '(({in:hrs}*{in:bill}*{in:bm}-%s)*MIN(1,{in:%s}/{in:need}))' % (CST11(p), v)
# 13 travel policy
PM13 = 'MAX(0,MIN({in:avgmin},{in:cap})-{in:unpaid})'
# 14 funding
NEED14 = '({in:gross}+{in:burden})'
# 18 grid
SCF = 'IF({in:sc}=%s,1,IF({in:sc}=%s,0.9,1.15))' % (tok('scen', 'Base'), tok('scen', 'Best'))
FH = '{range:otforecast.forecast_hours}'
LN18 = '({in:line}/%s)' % SCF
OH18 = '(%s*(SUMIFS(%s,%s,">"&%s)-%s*COUNTIFS(%s,">"&%s)))' % (SCF, FH, FH, LN18, LN18, FH, LN18)
AVR18 = 'IFERROR(AVERAGEIFS({range:caregivers.pay_rate},{range:caregivers.status},%s),0)' % tok('cgstatus', 'Active')

tools = [
 TOOL('payline', 'Payroll Line Calculator', 'Payroll line calculator with visible rules',
  'Type one caregiver pay period: weekly hours, holiday, evening and night hours, travel and kilometres, bonus and deductions. Every rule is shown line by line. Confirm pay rules with your adviser.', [
  I('rate', 'Pay rate per hour', 18.0, 'money'), I('w1', 'Hours worked, week 1', 44), I('w2', 'Hours worked, week 2', 38), I('hol', 'Holiday hours (part of the hours above)', 6), I('eve', 'Evening hours (part of the hours above)', 10),
  I('ngt', 'Night hours (part of the hours above)', 8), I('trav', 'Paid travel minutes', 95, 'int'), I('km', 'Kilometres driven', 62), I('bonus', 'Bonus', 50, 'money'), I('ded', 'Deductions', 20, 'money')], [
  O('Overtime hours (above the weekly line)', 'num', OTH1), O('Regular hours', 'num', REG1), O('Regular pay', 'money', C1['reg']), O('Overtime pay at the overtime multiplier', 'money', C1['ot']),
  O('Holiday premium (extra on holiday hours)', 'money', C1['hol']), O('Evening and night uplift', 'money', C1['en']), O('Paid travel time', 'money', C1['trv']), O('Mileage amount', 'money', C1['mil']),
  O('Gross pay (with bonus)', 'money', 'ROUND(%s,2)' % GROSS1), O('Net pay', 'money', 'ROUND(%s,2)' % NET1), O('Payroll burden', 'money', BURD1),
  O('Total cost to the agency', 'money', 'ROUND(%s+%s,2)' % (GROSS1, BURD1)), O('Cost per worked hour', 'money', 'ROUND((%s+%s)/({in:w1}+{in:w2}),2)' % (GROSS1, BURD1)),
  O('Verdict', 'text', 'IF(%s<0,%s,IF(%s>0,%s,%s))' % (NET1, ck('Negative net pay'), OTH1, vd('Overtime in this line'), vd('Ready to pay')))],
  GR('What if', ('No overtime: 40 and 40 hours', {'w1': 40, 'w2': 40}), ('Both weeks 46 hours', {'w1': 46, 'w2': 46}), ('No holiday hours', {'hol': 0}), ('Pay rate up by 1', {'rate': 19}), ('Deductions 120', {'ded': 120}))),
 TOOL('precheck', 'Pre-payroll Check', 'Pre-payroll check: ready to pay or fix first',
  'Type the totals of the pay run: hours entered, hours from check-ins, visits with no check-out, the lowest net pay and caregivers near the line; see the warnings found and the verdict.', [
  I('sheets', 'Time sheets in the pay run', 37, 'int'), I('he', 'Hours entered on time sheets', 1812.25), I('hci', 'Hours from check-ins', 1796.75), I('nco', 'Visits with no check-out', 3, 'int'),
  I('lnet', 'Lowest net pay in the run', 154.22, 'money'), I('near', 'Caregivers near the overtime line', 2, 'int')], [
  O('Hours difference (entered minus check-ins)', 'num', '{in:he}-{in:hci}'), O('Allowed difference for all time sheets', 'num', '{in:sheets}*{set:timesheet_tolerance}'),
  O('Hours check', 'text', 'IF(ABS({in:he}-{in:hci})>{in:sheets}*{set:timesheet_tolerance},%s,%s)' % (ck('Mismatch'), ck('Matches'))),
  O('Net pay check', 'text', 'IF({in:lnet}<0,%s,%s)' % (ck('Negative net pay'), ck('Net pay is fine'))),
  O('Warnings found', 'int', 'IF(ABS({in:he}-{in:hci})>{in:sheets}*{set:timesheet_tolerance},1,0)+{in:nco}+IF({in:lnet}<0,1,0)+{in:near}'),
  O('Open warnings in the log', 'int', 'COUNTIFS({range:warnings.status},%s)' % ck('Open')), O('Time sheets awaiting approval', 'int', 'COUNTIFS({range:timesheets.approval},%s)' % ck('Awaiting approval')),
  O('Verdict', 'text', 'IF(IF(ABS({in:he}-{in:hci})>{in:sheets}*{set:timesheet_tolerance},1,0)+{in:nco}+IF({in:lnet}<0,1,0)+{in:near}=0,%s,%s)' % (vd('Ready to pay'), vd('Fix first')))],
  GR('What if', ('Everything fixed', {'nco': 0, 'near': 0}), ('Hours 40 apart', {'he': 1836.75}), ('One negative net pay', {'lnet': -35, 'nco': 0, 'near': 0}), ('Ten missing check-outs', {'nco': 10}))),
 TOOL('ot_midweek', 'Midweek Overtime Forecast', 'Midweek overtime forecast: safe, near the line or over',
  'Type the hours a caregiver has worked so far this week and the hours still scheduled; see the forecast, the hours over the line, the extra cost with burden and a Safe, Near or Over verdict.', [
  I('rate', 'Pay rate per hour', 18.5, 'money'), I('sofar', 'Hours worked so far this week', 22), I('still', 'Hours still scheduled this week', 25), I('line', 'Overtime line, hours a week', 40, 'int')], [
  O('Forecast hours for the week', 'num', FC3), O('Hours over the line', 'num', 'MAX(0,%s-{in:line})' % FC3), O('Hours left before the line', 'num', 'MAX(0,{in:line}-%s)' % FC3),
  O('Overtime pay on those hours', 'money', 'ROUND(MAX(0,%s-{in:line})*{in:rate}*%s,2)' % (FC3, MULT)), O('Extra cost over normal pay, with burden', 'money', 'ROUND(MAX(0,%s-{in:line})*{in:rate}*(%s-1)*%s,2)' % (FC3, MULT, BUR)),
  O('Busiest caregiver in the Overtime Forecast page', 'num', 'MAX({range:otforecast.forecast_hours})'), O('Caregivers over the line on that page', 'int', 'COUNTIFS({range:otforecast.line_check},%s)' % ck('Over the line')),
  O('Verdict', 'text', 'IF(%s>{in:line},%s,IF(%s>={set:near_line_hours},%s,%s))' % (FC3, ck('Over the line'), FC3, ck('Near the line'), ck('Safe')))],
  GR('What if', ('Move 4 hours away', {'still': 21}), ('Move 8 hours away', {'still': 17}), ('Add a 4-hour cover', {'still': 29}), ('Line at 44', {'line': 44}))),
 TOOL('movevisit', 'Move Visit to Avoid Overtime', 'Move this visit to avoid overtime: which caregiver takes it',
  'Type the visit hours, the forecast hours of the caregiver over the line and three caregivers who could take it with their hours and extra travel minutes; see the cheapest move and Move or Keep.', [
  I('vh', 'Visit hours', 3), I('fh', 'Forecast hours of the caregiver over the line', 47), I('fr', 'Pay rate of that caregiver', 18.5, 'money'), I('rate', 'Average pay rate of the other caregivers', 17.5, 'money'),
  I('ah', 'Caregiver A: forecast hours', 30), I('at', 'Caregiver A: extra travel minutes', 10, 'int'), I('bh', 'Caregiver B: forecast hours', 38), I('bt', 'Caregiver B: extra travel minutes', 0, 'int'),
  I('ch', 'Caregiver C: forecast hours', 22), I('ct', 'Caregiver C: extra travel minutes', 25, 'int')], [
  O('Overtime hours avoided at the first caregiver', 'num', AV4), O('Overtime premium saved, with burden', 'money', 'ROUND(%s,2)' % SAV4),
  O('Cost of moving to A', 'money', 'ROUND(%s,2)' % COST4('ah', 'at')), O('Cost of moving to B', 'money', 'ROUND(%s,2)' % COST4('bh', 'bt')), O('Cost of moving to C', 'money', 'ROUND(%s,2)' % COST4('ch', 'ct')),
  O('Cheapest move (1 = A, 2 = B, 3 = C)', 'int', 'IF(%s=%s,1,IF(%s=%s,2,3))' % (COST4('ah', 'at'), MINC4, COST4('bh', 'bt'), MINC4)), O('Net saving of the cheapest move', 'money', 'ROUND(%s-%s,2)' % (SAV4, MINC4)),
  O('Verdict', 'text', 'IF(%s-%s>0,%s,%s)' % (SAV4, MINC4, vd('Move the visit'), vd('Keep the visit')))],
  GR('What if', ('A is full at 38 hours', {'ah': 38}), ('Longer visit, 6 hours', {'vh': 6}), ('Caregiver is at 41 hours', {'fh': 41}), ('Everyone is near full', {'ah': 38, 'bh': 39, 'ch': 38}))),
 TOOL('otrule', 'Overtime Rule Test', 'Overtime rule test: weekly line or daily line',
  'Type the hours of each day, the weekly line and an optional daily line (0 = off); see the overtime hours and extra cost under each rule. Check your own local rules before choosing a rule.', [
  I('d1', 'Monday hours', 8), I('d2', 'Tuesday hours', 8), I('d3', 'Wednesday hours', 9), I('d4', 'Thursday hours', 10), I('d5', 'Friday hours', 8), I('d6', 'Saturday hours', 4), I('d7', 'Sunday hours', 0),
  I('wline', 'Weekly line, hours', 40, 'int'), I('dline', 'Daily line, hours (0 = no daily rule)', 8), I('rate', 'Pay rate per hour', 18.5, 'money')], [
  O('Total hours in the week', 'num', TOT5), O('Overtime hours, weekly line rule', 'num', WK5), O('Overtime hours, daily line rule', 'num', DY5), O('Overtime hours, higher of the two', 'num', 'MAX(%s,%s)' % (WK5, DY5)),
  O('Extra cost, weekly line rule', 'money', 'ROUND((%s)*{in:rate}*(%s-1)*%s,2)' % (WK5, MULT, BUR)), O('Extra cost, daily line rule', 'money', 'ROUND((%s)*{in:rate}*(%s-1)*%s,2)' % (DY5, MULT, BUR)),
  O('Difference (weekly minus daily)', 'money', 'ROUND(((%s)-(%s))*{in:rate}*(%s-1)*%s,2)' % (WK5, DY5, MULT, BUR)),
  O('Verdict', 'text', 'IF(%s>%s,%s,IF(%s<%s,%s,%s))' % (WK5, DY5, vd('Weekly line costs more'), WK5, DY5, vd('Daily line costs more'), vd('Same cost under both')))],
  GR('What if', ('Daily line 10 hours', {'dline': 10}), ('Daily rule off', {'dline': 0}), ('Weekly line 44', {'wline': 44}), ('Weekly line 36', {'wline': 36}), ('A 12-hour Wednesday', {'d3': 12}))),
 TOOL('otshare', 'Overtime Share vs Target', 'Overtime share against the target',
  'Type the overtime hours and the paid hours of a period and your target; see the share, the gap in points, the hours of room and how it compares with your last 3 months and the same month last year.', [
  I('oth', 'Overtime hours in the period', 22.5), I('th', 'Total paid hours in the period', 1780), I('target', 'Overtime share target', 0.03, 'pct')], [
  O('Overtime share', 'pct', '{in:oth}/{in:th}'), O('Target', 'pct', '{in:target}'), O('Gap in points (share minus target)', 'num', 'ROUND(({in:oth}/{in:th}-{in:target})*100,2)'),
  O('Overtime hours allowed at the target', 'num', '{in:th}*{in:target}'), O('Hours of room before the target', 'num', '{in:th}*{in:target}-{in:oth}'),
  O('Your overtime share, last 3 months', 'pct', 'IFERROR(%s/%s,0)' % (LH3, LP3)),
  O('Your overtime share, same month last year', 'pct', 'IFERROR(SUMIFS({range:otmonth.overtime_hours},{range:otmonth.month},%s)/SUMIFS({range:otmonth.hours},{range:otmonth.month},%s),0)' % (SY, SY)),
  O('Verdict', 'text', 'IF({in:oth}/{in:th}<={in:target},%s,%s)' % (vd('Under the target'), vd('Above the target')))],
  GR('What if', ('Overtime 60 hours', {'oth': 60}), ('Overtime 90 hours', {'oth': 90}), ('Target 2%', {'target': 0.02}), ('Target 1%', {'target': 0.01}), ('Hours 2,400', {'th': 2400}))),
 TOOL('costhour', 'Payroll Cost per Hour', 'Payroll cost per hour against the bill rate',
  'Type the pay lines of a period, paid hours and bill rate; see cost per hour, share of the bill rate, gross margin per hour (bill rate minus loaded pay cost) and the rate you need.', [
  I('pay', 'Caregiver pay', 62400, 'money'), I('otp', 'Overtime pay', 310, 'money'), I('trv', 'Travel pay', 1150, 'money'), I('mil', 'Mileage amount', 780, 'money'), I('bur', 'Payroll burden amount', 13800, 'money'),
  I('hrs', 'Paid hours', 3330), I('bill', 'Average bill rate per hour', 35.8, 'money')], [
  O('Total pay cost', 'money', TOT7), O('Cost per paid hour', 'money', 'ROUND(%s/{in:hrs},2)' % TOT7), O('Share of the bill rate', 'pct', '%s/{in:hrs}/{in:bill}' % TOT7),
  O('Gross margin per hour', 'money', 'ROUND({in:bill}-%s/{in:hrs},2)' % TOT7), O('Gross margin share of the bill rate', 'pct', '1-%s/{in:hrs}/{in:bill}' % TOT7),
  O('Bill rate needed for the target margin', 'money', 'ROUND(%s/{in:hrs}/(1-{set:target_margin}),2)' % TOT7), O('Rate rise needed per hour', 'money', 'MAX(0,ROUND(%s/{in:hrs}/(1-{set:target_margin})-{in:bill},2))' % TOT7),
  O('Verdict', 'text', 'IF(%s/{in:hrs}/{in:bill}<={set:payroll_ratio_ceiling},%s,%s)' % (TOT7, vd('Under the ceiling'), vd('Over the ceiling')))],
  GR('What if', ('Overtime three times higher', {'otp': 930}), ('Caregiver pay up 3%', {'pay': 64272}), ('Bill rate up by 2', {'bill': 37.8}), ('Paid hours up 5%', {'hrs': 3496}), ('Burden 12,400', {'bur': 12400}))),
 TOOL('costceiling', 'Payroll Cost Ceiling', 'Payroll cost ceiling: room, hours to cut or revenue to add',
  'Type the revenue and the pay cost of a month and your ceiling; see the ratio, the room in money and what you must cut (hours) or add (revenue) to get under the ceiling, with a revenue sensitivity.', [
  I('rev', 'Revenue for the month', 133000, 'money'), I('cost', 'Total pay cost for the month', 87900, 'money'), I('ceil', 'Payroll cost ceiling (share of revenue)', 0.65, 'pct'), I('cph', 'Average cost per paid hour', 23.6, 'money')], [
  O('Pay cost ratio', 'pct', '{in:cost}/{in:rev}'), O('Pay cost allowed at the ceiling', 'money', '{in:rev}*{in:ceil}'), O('Room under the ceiling (negative = over)', 'money', 'ROUND({in:rev}*{in:ceil}-{in:cost},2)'),
  O('Pay cost to cut', 'money', 'MAX(0,ROUND({in:cost}-{in:rev}*{in:ceil},2))'), O('Paid hours to cut', 'int', 'ROUNDUP(MAX(0,{in:cost}-{in:rev}*{in:ceil})/{in:cph},0)'),
  O('Revenue to add at the same pay cost', 'money', 'MAX(0,ROUND({in:cost}/{in:ceil}-{in:rev},2))'), O('Your pay cost ratio, last 3 months', 'pct', 'IFERROR(%s,0)' % R3),
  O('Verdict', 'text', 'IF({in:cost}/{in:rev}<={in:ceil},%s,%s)' % (vd('Under the ceiling'), vd('Over the ceiling')))],
  GR('Revenue sensitivity', ('Revenue down 5%', {'rev': 126350}), ('Revenue down 2.5%', {'rev': 129675}), ('Revenue as typed', {'rev': 133000}), ('Revenue up 2.5%', {'rev': 136325}), ('Revenue up 5%', {'rev': 139650}))),
 TOOL('burdencheck', 'Burden Check', 'Burden check: your example split against the setting',
  "Type example shares of payroll taxes, workers' insurance and benefits and a pay base; see the total burden against your setting. Example split: confirm with your adviser.", [
  I('base', 'Pay base for the month', 68500, 'money'), I('tx', 'Payroll taxes, share of pay', 0.10, 'pct'), I('wi', "Workers' insurance, share of pay", 0.06, 'pct'), I('bf', 'Benefits, share of pay', 0.05, 'pct')], [
  O('Total burden share', 'pct', '{in:tx}+{in:wi}+{in:bf}'), O('Burden share in your settings', 'pct', '{set:payroll_burden}'), O('Difference in points', 'num', 'ROUND(({in:tx}+{in:wi}+{in:bf}-{set:payroll_burden})*100,2)'),
  O('Burden amount for the month', 'money', 'ROUND({in:base}*({in:tx}+{in:wi}+{in:bf}),2)'), O('Difference from the setting, money', 'money', 'ROUND({in:base}*({in:tx}+{in:wi}+{in:bf}-{set:payroll_burden}),2)'),
  O('Your burden share, last 12 months', 'pct', 'IFERROR(SUMIFS({range:burden.total_burden},{range:burden.month},">="&%s,{range:burden.month},"<"&%s)/SUMIFS({range:burden.pay_base},{range:burden.month},">="&%s,{range:burden.month},"<"&%s),0)' % (MS(12), THIS, MS(12), THIS)),
  O('Verdict', 'text', 'IF(ABS({in:tx}+{in:wi}+{in:bf}-{set:payroll_burden})<=0.005,%s,IF({in:tx}+{in:wi}+{in:bf}>{set:payroll_burden},%s,%s))' % (vd('Matches the setting'), vd('Burden above the setting'), vd('Burden below the setting')))],
  GR('What if', ('Payroll taxes 9%', {'tx': 0.09}), ('Benefits 3%', {'bf': 0.03}), ("Workers' insurance 4.5%", {'wi': 0.045}), ('Pay base up 10%', {'base': 75350}))),
 TOOL('holmargin', 'Holiday Margin Forecast', 'Holiday margin forecast: worth it or loses money',
  'Type the visits and hours booked on a holiday, the pay and bill multipliers and the average rates; see the extra pay, extra charge, the margin on the day and the verdict.', [
  I('vis', 'Visits booked', 40, 'int'), I('hrs', 'Hours booked', 140), I('bm', 'Bill multiplier', 1.5), I('pm', 'Pay multiplier', 1.5), I('bill', 'Average bill rate per hour', 33.8, 'money'), I('pay', 'Average pay rate per hour', 17.9, 'money')], [
  O('Charge on the day', 'money', 'ROUND(%s,2)' % CH10), O('Pay cost on the day, with burden', 'money', 'ROUND(%s,2)' % CO10), O('Margin on the day', 'money', 'ROUND(%s-%s,2)' % (CH10, CO10)),
  O('Margin share of the charge', 'pct', '(%s-%s)/%s' % (CH10, CO10, CH10)), O('Extra pay against a normal day, with burden', 'money', 'ROUND({in:hrs}*{in:pay}*({in:pm}-1)*%s,2)' % BUR),
  O('Extra charge against a normal day', 'money', 'ROUND({in:hrs}*{in:bill}*({in:bm}-1),2)'), O('Margin of a normal day, same hours', 'money', 'ROUND({in:hrs}*({in:bill}-{in:pay}*%s),2)' % BUR),
  O('Caregivers needed', 'int', 'ROUNDUP({in:hrs}/{set:holiday_shift_hours},0)'),
  O('Verdict', 'text', 'IF(%s-%s<0,%s,IF((%s-%s)/%s<{set:target_margin}*0.75,%s,%s))' % (CH10, CO10, ck('Loses money'), CH10, CO10, CH10, ck('Thin margin'), ck('Worth it')))],
  GR('What if', ('Pay at 2 times', {'pm': 2}), ('Pay at 2.5 times', {'pm': 2.5}), ('Charge only 1.25 times', {'bm': 1.25}), ('Hours up to 200', {'hrs': 200}))),
 TOOL('holprem', 'Holiday Premium Choice', 'Holiday premium choice at 1.25, 1.5 and 2 times',
  'Type the holiday hours, the rates, the caregivers needed and your guess of volunteers at each premium; see the pay cost, the margin and the expected margin of each choice and the best premium.', [
  I('hrs', 'Hours booked', 140), I('bill', 'Average bill rate per hour', 33.8, 'money'), I('pay', 'Average pay rate per hour', 17.9, 'money'), I('bm', 'Bill multiplier', 1.5), I('need', 'Caregivers needed', 22, 'int'),
  I('v1', 'Volunteers likely at 1.25 times', 9, 'int'), I('v2', 'Volunteers likely at 1.5 times', 15, 'int'), I('v3', 'Volunteers likely at 2 times', 21, 'int')], [
  O('Pay cost at 1.25 times, with burden', 'money', 'ROUND(%s,2)' % CST11('1.25')), O('Pay cost at 1.5 times, with burden', 'money', 'ROUND(%s,2)' % CST11('1.5')), O('Pay cost at 2 times, with burden', 'money', 'ROUND(%s,2)' % CST11('2')),
  O('Margin if all visits are covered at 1.25 times', 'money', 'ROUND({in:hrs}*{in:bill}*{in:bm}-%s,2)' % CST11('1.25')), O('Margin if all visits are covered at 1.5 times', 'money', 'ROUND({in:hrs}*{in:bill}*{in:bm}-%s,2)' % CST11('1.5')),
  O('Margin if all visits are covered at 2 times', 'money', 'ROUND({in:hrs}*{in:bill}*{in:bm}-%s,2)' % CST11('2')),
  O('Expected margin at 1.25 times', 'money', 'ROUND(%s,2)' % EXP11('1.25', 'v1')), O('Expected margin at 1.5 times', 'money', 'ROUND(%s,2)' % EXP11('1.5', 'v2')), O('Expected margin at 2 times', 'money', 'ROUND(%s,2)' % EXP11('2', 'v3')),
  O('Caregivers short at 1.25 times', 'int', 'MAX(0,{in:need}-{in:v1})'), O('Best premium (times the pay rate)', 'num', 'IF(AND(%s>=%s,%s>=%s),1.25,IF(%s>=%s,1.5,2))' % (EXP11('1.25', 'v1'), EXP11('1.5', 'v2'), EXP11('1.25', 'v1'), EXP11('2', 'v3'), EXP11('1.5', 'v2'), EXP11('2', 'v3'))),
  O('Verdict', 'text', 'IF(AND(%s>=%s,%s>=%s),%s,IF(%s>=%s,%s,%s))' % (EXP11('1.25', 'v1'), EXP11('1.5', 'v2'), EXP11('1.25', 'v1'), EXP11('2', 'v3'), vd('Pay 1.25 times'), EXP11('1.5', 'v2'), EXP11('2', 'v3'), vd('Pay 1.5 times'), vd('Pay 2 times')))],
  GR('What if', ('Fewer volunteers at 1.5 (11)', {'v2': 11}), ('Charge only 1.25 times', {'bm': 1.25}), ('Thirty caregivers needed', {'need': 30}), ('More volunteers at 1.25 (16)', {'v1': 16}))),
 TOOL('mileageline', 'Mileage Pay Line', 'Mileage pay line: mileage, travel time and pay per km',
  'Type the kilometres, the rate per km (or per mile), the paid travel minutes and the pay rate; see the mileage amount, the travel pay and the all-in pay per km against your own average.', [
  I('km', 'Kilometres driven', 62), I('rate', 'Mileage rate per km (or per mile)', 0.4, 'money'), I('min', 'Paid travel minutes', 95, 'int'), I('pay', 'Pay rate per hour', 18.0, 'money')], [
  O('Mileage amount', 'money', 'ROUND({in:km}*{in:rate},2)'), O('Paid travel time', 'money', 'ROUND({in:min}/60*{in:pay},2)'), O('Total travel pay', 'money', 'ROUND({in:km}*{in:rate}+{in:min}/60*{in:pay},2)'),
  O('All-in pay per km', 'money', 'ROUND(({in:km}*{in:rate}+{in:min}/60*{in:pay})/{in:km},2)'), O('Your average all-in pay per km', 'money', 'IFERROR(ROUND(AVERAGE({range:travelpay.pay_per_km}),2),0)'),
  O('Mileage rate in your settings', 'money', '{set:mileage_rate}'),
  O('Verdict', 'text', 'IF(({in:km}*{in:rate}+{in:min}/60*{in:pay})/{in:km}>IFERROR(AVERAGE({range:travelpay.pay_per_km}),0),%s,%s)' % (vd('Above your average'), vd('Within your average')))],
  GR('What if', ('Long drive, 120 km', {'km': 120, 'min': 160}), ('Short hop, 15 km', {'km': 15, 'min': 30}), ('Rate 0.55 per km', {'rate': 0.55}), ('Pay rate 21', {'pay': 21}))),
 TOOL('travelpolicy', 'Paid Travel Policy Test', 'Paid travel policy test: unpaid first minutes and a cap',
  'Type travel legs a week, average minutes, unpaid first minutes and a cap; see pay saved a year and the effect per caregiver. Check your own local rules first.', [
  I('legs', 'Travel legs a week (all caregivers)', 520, 'int'), I('avgmin', 'Average minutes per leg', 17), I('unpaid', 'Unpaid first minutes per leg', 10), I('cap', 'Most paid minutes per leg', 40), I('rate', 'Average pay rate per hour', 18.2, 'money'),
  I('cg', 'Caregivers who drive', 38, 'int')], [
  O('Paid travel minutes a week today', 'int', '{in:legs}*{in:avgmin}'), O('Paid travel minutes a week under the policy', 'int', '{in:legs}*%s' % PM13), O('Minutes saved a week', 'int', '{in:legs}*({in:avgmin}-%s)' % PM13),
  O('Share of paid travel removed', 'pct', '({in:avgmin}-%s)/{in:avgmin}' % PM13), O('Pay saved a week, with burden', 'money', 'ROUND({in:legs}*({in:avgmin}-%s)/60*{in:rate}*%s,2)' % (PM13, BUR)),
  O('Pay saved a year, with burden', 'money', 'ROUND({in:legs}*({in:avgmin}-%s)/60*{in:rate}*%s*52,2)' % (PM13, BUR)),
  O('Pay lost per caregiver a month', 'money', 'ROUND({in:legs}*({in:avgmin}-%s)/60*{in:rate}*52/12/{in:cg},2)' % PM13),
  O('Verdict', 'text', 'IF({in:avgmin}-%s>0,%s,%s)' % (PM13, vd('Saves pay'), vd('No saving')))],
  GR('What if', ('Only 5 unpaid minutes', {'unpaid': 5}), ('No unpaid minutes, cap 30', {'unpaid': 0, 'cap': 30}), ('Cap 12 minutes', {'cap': 12}), ('Longer legs, 25 minutes', {'avgmin': 25}))),
 TOOL('fundcheck', 'Pay Run Funding Check', 'Pay run funding check: fund now or wait',
  'Type the pay run, the burden due, the cash now, the invoices due before the pay date and your cash floor; see the cash after the pay run and whether to fund now or wait.', [
  I('gross', 'Pay run total (gross pay)', 34000, 'money'), I('burden', 'Payroll burden due with it', 6800, 'money'), I('cash', 'Cash now', 96000, 'money'), I('due', 'Invoices due before the pay date', 24000, 'money'),
  I('coll', 'Share of those invoices expected in time', 0.8, 'pct'), I('floor', 'Cash floor', 30000, 'money')], [
  O('Cash needed for the pay run', 'money', NEED14), O('Receipts expected before the pay date', 'money', 'ROUND({in:due}*{in:coll},2)'), O('Cash after the pay run', 'money', 'ROUND({in:cash}+{in:due}*{in:coll}-%s,2)' % NEED14),
  O('Room above the cash floor', 'money', 'ROUND({in:cash}+{in:due}*{in:coll}-%s-{in:floor},2)' % NEED14), O('Receipts needed to stay above the floor', 'money', 'MAX(0,ROUND({in:floor}+%s-{in:cash},2))' % NEED14),
  O('Weeks of pay the cash now covers', 'num', '{in:cash}/(%s/2)' % NEED14),
  O('Verdict', 'text', 'IF({in:cash}+{in:due}*{in:coll}-%s>={in:floor},%s,%s)' % (NEED14, vd('Fund now'), vd('Wait')))],
  GR('What if', ('Cash only 52,000', {'cash': 52000}), ('Cash only 45,000', {'cash': 45000}), ('Only half the invoices paid', {'coll': 0.5}), ('Bigger pay run, 55,000', {'gross': 55000, 'burden': 11000}))),
 TOOL('coverbudget', 'Cover Premium Budget', 'Cover premium budget: cost a month and a year',
  'Type call-offs a week (a caregiver cannot come), the short-notice share, premium and hours; see the cost a month and a year against your budget and history.', [
  I('co', 'Call-offs a week', 9), I('sn', 'Share covered at short notice', 0.45, 'pct'), I('prem', 'Cover premium per hour', 3, 'money'), I('hrs', 'Hours of one cover', 4.2), I('bud', 'Monthly budget for cover premium', 650, 'money')], [
  O('Short-notice covers a week', 'num', '{in:co}*{in:sn}'), O('Premium hours a week', 'num', '{in:co}*{in:sn}*{in:hrs}'), O('Cost a week', 'money', 'ROUND({in:co}*{in:sn}*{in:hrs}*{in:prem},2)'),
  O('Cost a month', 'money', 'ROUND({in:co}*{in:sn}*{in:hrs}*{in:prem}*52/12,2)'), O('Cost a year', 'money', 'ROUND({in:co}*{in:sn}*{in:hrs}*{in:prem}*52,2)'),
  O('Cost a month with burden', 'money', 'ROUND({in:co}*{in:sn}*{in:hrs}*{in:prem}*52/12*%s,2)' % BUR),
  O('Cover premium paid a month, last 3 months', 'money', 'ROUND(SUMIFS({range:payperiods.cover_premium},{range:payperiods.pay_date},">="&%s,{range:payperiods.pay_date},"<"&%s)/3,2)' % (MS(3), THIS)),
  O('Verdict', 'text', 'IF({in:co}*{in:sn}*{in:hrs}*{in:prem}*52/12*%s<={in:bud},%s,%s)' % (BUR, vd('Within budget'), vd('Over budget')))],
  GR('What if', ('Fourteen call-offs a week', {'co': 14}), ('Eighty percent short notice', {'sn': 0.8}), ('Premium of 5', {'prem': 5}), ('Budget of 200', {'bud': 200}))),
 TOOL('netcheck', 'Net Pay Check', 'Net pay check: negative net pay and a deduction limit',
  'Type gross pay, deductions and your own deduction limit; see net pay, the part to carry forward and a negative net pay warning. Check your own local rules on deductions.', [
  I('gross', 'Gross pay', 842.5, 'money'), I('ded', 'Deductions', 260, 'money'), I('limit', 'Most deductions as a share of gross pay', 0.25, 'pct')], [
  O('Net pay', 'money', 'ROUND({in:gross}-{in:ded},2)'), O('Deductions as a share of gross pay', 'pct', '{in:ded}/{in:gross}'), O('Largest deduction at the limit', 'money', 'ROUND({in:gross}*{in:limit},2)'),
  O('Deduction to carry forward', 'money', 'MAX(0,ROUND({in:ded}-{in:gross}*{in:limit},2))'), O('Net pay after the limit', 'money', 'ROUND({in:gross}-MIN({in:ded},{in:gross}*{in:limit}),2)'),
  O('Negative net pay warning', 'text', 'IF({in:gross}-{in:ded}<0,%s,%s)' % (ck('Negative net pay'), ck('Net pay is fine'))),
  O('Verdict', 'text', 'IF({in:gross}-{in:ded}<0,%s,IF({in:ded}>{in:gross}*{in:limit},%s,%s))' % (ck('Negative net pay'), vd('Carry the rest forward'), vd('Pay as entered')))],
  GR('What if', ('Deductions 90', {'ded': 90}), ('Deductions 900', {'ded': 900}), ('Limit 35%', {'limit': 0.35}), ('Gross pay 600', {'gross': 600}))),
 TOOL('otsens', 'Overtime Sensitivity', 'Overtime sensitivity: extra overtime hours and margin lost',
  'Type caregivers with overtime, hours now and extra hours each; see cost with burden and the share of gross margin lost. The what-if table shows 0 to 4 extra hours.', [
  I('ncg', 'Caregivers with overtime', 6, 'int'), I('base', 'Overtime hours a week each now', 2), I('extra', 'Extra overtime hours a week each', 2), I('rate', 'Average pay rate per hour', 18.2, 'money'),
  I('gm', 'Gross margin for a month', 45000, 'money'), I('bud', 'Monthly overtime budget', 1000, 'money')], [
  O('Overtime hours a week', 'num', '{in:ncg}*({in:base}+{in:extra})'), O('Extra cost a week, with burden', 'money', 'ROUND({in:ncg}*({in:base}+{in:extra})*{in:rate}*(%s-1)*%s,2)' % (MULT, BUR)),
  O('Extra cost a month, with burden', 'money', 'ROUND({in:ncg}*({in:base}+{in:extra})*{in:rate}*(%s-1)*%s*52/12,2)' % (MULT, BUR)),
  O('Cost of the extra hours alone, a month', 'money', 'ROUND({in:ncg}*{in:extra}*{in:rate}*(%s-1)*%s*52/12,2)' % (MULT, BUR)),
  O('Share of your monthly gross margin lost', 'pct', '{in:ncg}*({in:base}+{in:extra})*{in:rate}*(%s-1)*%s*52/12/{in:gm}' % (MULT, BUR)),
  O('Verdict', 'text', 'IF({in:ncg}*({in:base}+{in:extra})*{in:rate}*(%s-1)*%s*52/12<={in:bud},%s,%s)' % (MULT, BUR, vd('Within budget'), vd('Over budget')))],
  GR('Extra overtime hours each', ('Extra 0 hours', {'extra': 0}), ('Extra 1 hour', {'extra': 1}), ('Extra 2 hours', {'extra': 2}), ('Extra 3 hours', {'extra': 3}), ('Extra 4 hours', {'extra': 4}))),
 TOOL('ovgrid', 'Overtime Line What-if', 'What-if grid: overtime line against weekly overtime cost',
  'Pick a scenario (Base, Best or Worst) and an overtime line; see caregivers over it, overtime hours and weekly cost from Overtime Forecast. The grid tries lines of 36 to 44 hours.', [
  I('line', 'Overtime line, hours a week', 40, 'int'), IL('sc', 'Scenario', 'scen', 'Base'), I('bud', 'Weekly overtime budget', 150, 'money')], [
  O('Caregivers over this line', 'int', 'COUNTIFS(%s,">"&%s)' % (FH, LN18)), O('Overtime hours this week', 'num', 'ROUND(%s,2)' % OH18), O('Average pay rate of active caregivers', 'money', 'ROUND(%s,2)' % AVR18),
  O('Overtime cost this week, with burden', 'money', 'ROUND(%s*%s*(%s-1)*%s,2)' % (OH18, AVR18, MULT, BUR)), O('Weekly overtime budget', 'money', '{in:bud}'),
  O('Verdict', 'text', 'IF(%s*%s*(%s-1)*%s<={in:bud},%s,%s)' % (OH18, AVR18, MULT, BUR, vd('Within budget'), vd('Over budget')))],
  GR('Overtime line against weekly cost', ('Line at 36 hours', {'line': 36}), ('Line at 38 hours', {'line': 38}), ('Line at 40 hours', {'line': 40}), ('Line at 42 hours', {'line': 42}), ('Line at 44 hours', {'line': 44}),
     ('Worst case, line at 40', {'sc': '=' + tok('scen', 'Worst')}))),
]
assert len(tools) == 18
