"""Car rental suite part 3: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr3_lists import *
import cr3_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def R(t, c): return '{range:%s.%s}' % (t, c)
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
BILLED = tok('feestatus', 'Billed'); WOFF = tok('feestatus', 'Written off')
KE = tok('feekind', 'Extra mileage'); KL = tok('feekind', 'Late return'); KC = tok('feekind', 'Cleaning'); KR = tok('feekind', 'Fuel or charge refill')
OPENC = ca('Open claim')
D30 = '">="&({today}-30)'; D90 = '">="&({today}-90)'; D365 = '">="&({today}-365)'
tools = []

# 1 ------------------------------------------------------------ return fee calculator
LATE1 = 'MAX(0,({in:xh}*60+{in:xm})-({in:ah}*60+{in:am}))'
LF1 = 'IF(%s>{set:late_grace_min},ROUNDUP((%s-{set:late_grace_min})/60,0)*{set:late_fee_hour},0)' % (LATE1, LATE1)
EX1 = 'MAX(0,{in:drv}-{in:inc})'; MF1 = 'ROUND(%s*{set:extra_mile_fee},2)' % EX1
SH1 = 'MAX(0,{in:outl}-{in:inl})'; RF1 = 'IF(%s>=10,{set:refill_service_fee}+{set:refill_step_fee}*ROUNDUP(%s/10,0),0)' % (SH1, SH1)
CF1 = '{in:clean}*{set:cleaning_fee}'
TOT1 = '(%s+%s+%s+%s)' % (LF1, MF1, RF1, CF1)
tools.append(TOOL('return_fee_calc', 'Return Fee Calculator', 'Which fees are due on this return',
    'Type the agreed and actual return time, the miles, the levels and a cleaning flag; extra miles, late minutes after the grace, refill steps and the total fee due appear with a verdict.', [
    I('ah', 'Agreed return hour, 24 hour clock', 10, 'int'), I('am', 'Agreed return minute', 15, 'int'), I('xh', 'Actual return hour, 24 hour clock', 11, 'int'), I('xm', 'Actual return minute', 40, 'int'),
    I('inc', 'Miles included in the rental', 600, 'int'), I('drv', 'Miles driven', 710, 'int'), I('outl', 'Level at check-out, %', 100, 'int'), I('inl', 'Level at check-in, %', 70, 'int'), I('clean', 'Cleaning needed, 1 for yes', 0, 'int')], [
    O('Late minutes', 'int', LATE1), O('Late return fee after the grace', 'money', LF1), O('Extra miles', 'int', EX1), O('Extra mileage fee', 'money', MF1), O('Level shortfall, points', 'int', SH1),
    O('Refill fee', 'money', RF1), O('Cleaning fee', 'money', CF1), O('Total fee due', 'money', TOT1),
    O('Average fee due per return, last 90 days', 'money', 'IFERROR(AVERAGEIFS(%s,%s,%s),0)' % (R('checkout', 'fee_due'), R('checkout', 'in_date'), D90)),
    O('Share of returns with a fee, last 90 days', 'pct', 'IFERROR(COUNTIFS(%s,">0",%s,%s)/COUNTIFS(%s,%s),0)' % (R('checkout', 'fee_due'), R('checkout', 'in_date'), D90, R('checkout', 'in_date'), D90)),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (TOT1, c2('Fees due'), c2('No fee')))],
    GR('What if', ('Back on time, level kept', {'xh': 10, 'xm': 15, 'drv': 500, 'inl': 100}), ('Three hours late', {'xh': 13, 'xm': 30}), ('300 extra miles', {'drv': 900}), ('Needs cleaning', {'clean': 1}), ('Low charge, 20 percent', {'inl': 20}))))

# 2 ------------------------------------------------------------ handover completeness check
MO2 = '(({in:pout}<>1)+({in:keys}<2)+({in:lout}<=0)+({in:oout}<=0)+({in:dreq}=1)*({in:dtaken}<>1))'
MI2 = '(({in:pin}<>1)+({in:lin}<=0)+({in:oin}<={in:oout}))'
tools.append(TOOL('handover_check', 'Handover Completeness Check', 'Is this handover complete before the car leaves',
    'Type what was recorded at check-out and check-in (1 for yes, 0 for no); the checks missing are counted and compared with your last 30 days. Photos are only a yes or no here.', [
    I('pout', 'Photos taken at check-out, 1 for yes', 1, 'int'), I('keys', 'Keys handed over', 2, 'int'), I('lout', 'Level at check-out, %', 100, 'int'), I('oout', 'Odometer at check-out, miles', 52340, 'int'),
    I('dreq', 'Deposit required, 1 for yes', 1, 'int'), I('dtaken', 'Deposit taken, 1 for yes', 1, 'int'), I('pin', 'Photos taken at check-in, 1 for yes', 1, 'int'), I('lin', 'Level at check-in, %', 80, 'int'),
    I('oin', 'Odometer at check-in, miles', 52900, 'int')], [
    O('Checks missing at check-out', 'int', MO2), O('Checks missing at check-in', 'int', MI2), O('Checks missing in total', 'int', '%s+%s' % (MO2, MI2)),
    O('Checks that apply', 'int', '8+{in:dreq}'), O('Checks done', 'int', '8+{in:dreq}-%s-%s' % (MO2, MI2)),
    O('Handovers last 30 days', 'int', 'COUNTIFS(%s,%s)' % (R('checkout', 'out_date'), D30)), O('Handovers missing a check, last 30 days', 'int', 'COUNTIFS(%s,%s,%s,">0")' % (R('checkout', 'out_date'), D30, R('checkout', 'missing'))),
    O('Share complete, last 30 days', 'pct', 'IFERROR(1-COUNTIFS(%s,%s,%s,">0")/COUNTIFS(%s,%s),0)' % (R('checkout', 'out_date'), D30, R('checkout', 'missing'), R('checkout', 'out_date'), D30)),
    O('Verdict', 'text', 'IF(%s+%s=0,%s,%s)' % (MO2, MI2, c2('Complete, release the car'), c2('Checks missing, do not release')))],
    GR('What if', ('No photos at check-out', {'pout': 0}), ('One key only', {'keys': 1}), ('Deposit not taken', {'dtaken': 0}), ('No photos at check-in', {'pin': 0}), ('Odometer not entered at check-in', {'oin': 0}))))

# 3 ------------------------------------------------------------ late-return fee tool
HR3 = 'IF({in:late}>{in:grace},ROUNDUP(({in:late}-{in:grace})/60,0),0)'; RAW3 = '(%s*{in:feeh})' % HR3; FEE3 = 'MIN(%s,{in:dayrate})' % RAW3
LR = '%s,">0",%s,%s' % (R('checkout', 'late_minutes'), R('checkout', 'in_date'), D90)
tools.append(TOOL('late_tool', 'Late-Return Fee Tool', 'Do I bill this late return or is it inside the grace',
    'Type the minutes late, the grace, the hourly fee and the day rate that caps the fee; started hours, the fee to bill and how your own late returns of the last 90 days split are shown.', [
    I('late', 'Minutes after the agreed return time', 140, 'int'), I('grace', 'Grace minutes', 59, 'int'), I('feeh', 'Fee per started hour', 12), I('dayrate', 'Day rate of the car, the most a late fee can reach', 78)], [
    O('Started hours billed', 'int', HR3), O('Fee before the cap', 'money', RAW3), O('Late fee to bill', 'money', FEE3), O('Taken off by the one-day cap', 'money', '%s-%s' % (RAW3, FEE3)),
    O('Late returns, last 90 days', 'int', 'COUNTIFS(%s)' % LR), O('Late returns inside the grace, last 90 days', 'int', 'COUNTIFS(%s,%s,"<="&{in:grace})' % (LR, R('checkout', 'late_minutes'))),
    O('Share inside the grace', 'pct', 'IFERROR(COUNTIFS(%s,%s,"<="&{in:grace})/COUNTIFS(%s),0)' % (LR, R('checkout', 'late_minutes'), LR)),
    O('Average late minutes, last 90 days', 'num', 'IFERROR(AVERAGEIFS(%s,%s),0)' % (R('checkout', 'late_minutes'), LR)),
    O('Late fees billed, last 90 days', 'money', 'SUMIFS(%s,%s,%s,%s,%s,%s,%s)' % (R('fee_log', 'amount_due'), R('fee_log', 'kind'), KL, R('fee_log', 'billed'), YES, R('fee_log', 'date'), D90)),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (FEE3, c2('Bill the late fee'), c2('Inside the grace')))],
    GR('What if', ('Inside the grace', {'late': 40}), ('Three hours late', {'late': 240}), ('A day late, capped', {'late': 1000}), ('Grace 15 minutes', {'grace': 15}), ('Fee 20 an hour', {'feeh': 20}))))

# 4 ------------------------------------------------------------ extra-mileage fee tool
MPD4 = 'SUMIFS(%s,%s,{in:cls})' % (R('classes', 'miles_day'), R('classes', 'class'))
ALLOW4 = 'IF({in:plan}=%s,%s*{in:days},IF({in:plan}=%s,ROUND({in:wk}*{in:days}/7,0),ROUND({in:mo}*{in:days}/30,0)))' % (tok('plan', 'Daily'), MPD4, tok('plan', 'Weekly'))
EX4 = 'MAX(0,{in:drv}-%s)' % ALLOW4
CL4 = '%s,{in:cls},%s,%s' % (R('checkout', 'class'), R('checkout', 'in_date'), D90)
USE4 = 'IFERROR(AVERAGEIFS(%s,%s)/AVERAGEIFS(%s,%s),0)' % (R('checkout', 'miles_driven'), CL4, R('checkout', 'miles_included'), CL4)
OVR4 = 'IFERROR(COUNTIFS(%s,%s,">0")/COUNTIFS(%s),0)' % (CL4, R('checkout', 'extra_miles'), CL4)
tools.append(TOOL('mile_tool', 'Extra-Mileage Fee Tool', 'Is the mileage allowance generous, fair or tight',
    'Type class, plan, days and miles driven; allowance, extra miles and fee follow, with your last 90 days of that class (miles are the demo unit, set your own).', [
    IL('cls', 'Vehicle class', 'class', 'Midsize SUV'), IL('plan', 'Plan', 'plan', 'Daily'), I('days', 'Rental days', 4, 'int'), I('drv', 'Miles driven', 760, 'int'), I('wk', 'Miles included in a week', 1000, 'int'),
    I('mo', 'Miles included in a month', 3000, 'int'), I('fee', 'Fee per extra mile', 0.35)], [
    O('Included miles a day, this class', 'int', MPD4), O('Allowance for this rental', 'int', ALLOW4), O('Extra miles', 'int', EX4), O('Extra mileage fee', 'money', 'ROUND(%s*{in:fee},2)' % EX4),
    O('Average miles driven, this class, last 90 days', 'int', 'IFERROR(AVERAGEIFS(%s,%s),0)' % (R('checkout', 'miles_driven'), CL4)), O('Average allowance, this class, last 90 days', 'int', 'IFERROR(AVERAGEIFS(%s,%s),0)' % (R('checkout', 'miles_included'), CL4)),
    O('Share of the allowance renters use', 'pct', USE4), O('Share of rentals over the allowance', 'pct', OVR4),
    O('Extra-mileage fees billed, last 90 days', 'money', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('fee_log', 'amount_due'), R('fee_log', 'kind'), KE, R('fee_log', 'date'), D90)),
    O('Verdict', 'text', 'IF(%s<=0.05,%s,IF(%s>=0.15,%s,%s))' % (OVR4, c2('Allowance generous'), OVR4, c2('Allowance tight'), c2('Allowance fair')))],
    GR('What if', ('Weekly plan, 7 days', {'plan': '=' + tok('plan', 'Weekly'), 'days': 7, 'drv': 1200}), ('Economy, 3 days', {'cls': '=' + tok('class', 'Economy'), 'days': 3, 'drv': 520}), ('Van, 5 days', {'cls': '=' + tok('class', '7-seat Van'), 'days': 5, 'drv': 900}),
       ('Fee 0.50 a mile', {'fee': 0.5}), ('Monthly plan, 30 days', {'plan': '=' + tok('plan', 'Monthly'), 'days': 30, 'drv': 3400}))))

# 5 ------------------------------------------------------------ fuel and charge shortfall tool
SH5 = 'MAX(0,{in:outl}-{in:inl})'; ST5 = 'IF(%s>=10,ROUNDUP(%s/10,0),0)' % (SH5, SH5)
FE5 = 'IF(%s>0,{in:svc}+{in:step}*%s,0)' % (ST5, ST5); CO5 = '%s*{in:cost}' % ST5
tools.append(TOOL('refill_tool', 'Fuel and Charge Shortfall Tool', 'Does the refill fee cover what a refill really costs',
    'Type the levels, your step fee, service charge and real cost of 10 points; the refill fee, your cost and the margin are shown with the margin of your last 90 days of refills.', [
    I('outl', 'Level at check-out, %', 100, 'int'), I('inl', 'Level at check-in, %', 55, 'int'), I('step', 'Fee per 10 points below the agreed level', 6), I('svc', 'Service charge for a refill', 10), I('cost', 'Your real cost of 10 points', 3.2)], [
    O('Shortfall, points', 'int', SH5), O('Refill steps of 10 points', 'int', ST5), O('Refill fee charged', 'money', FE5), O('Your real refill cost', 'money', CO5), O('Margin on this refill', 'money', '%s-%s' % (FE5, CO5)),
    O('Margin for each step', 'money', 'IF(%s>0,(%s-%s)/%s,0)' % (ST5, FE5, CO5, ST5)), O('Step fee that just covers the cost', 'money', 'IF(%s>0,MAX(0,({in:cost}*%s-{in:svc})/%s),0)' % (ST5, ST5, ST5)),
    O('Refills, last 90 days', 'int', 'COUNTIFS(%s,%s,%s,">0")' % (R('fuel_levels', 'date'), D90, R('fuel_levels', 'steps'))),
    O('Average margin per refill, last 90 days', 'money', 'IFERROR(AVERAGEIFS(%s,%s,%s,%s,">0"),0)' % (R('fuel_levels', 'margin'), R('fuel_levels', 'date'), D90, R('fuel_levels', 'steps'))),
    O('Real refill cost, last 90 days', 'money', 'SUMIFS(%s,%s,%s)' % (R('fuel_levels', 'real_cost'), R('fuel_levels', 'date'), D90)),
    O('Verdict', 'text', 'IF(%s-%s>=0,%s,%s)' % (FE5, CO5, c2('Fee covers the cost'), c2('Raise the step fee')))],
    GR('What if', ('Small shortfall, 20 points', {'inl': 80}), ('Empty, 90 points', {'inl': 10}), ('No service charge', {'svc': 0}), ('Step fee 2', {'step': 2}), ('Real cost 6 a step', {'cost': 6.0}))))

# 6 ------------------------------------------------------------ fee collection ageing
AMT6 = 'SUMIFS(%s,%s,%s)' % (R('fee_log', 'open_amount'), R('fee_log', 'status'), BILLED)
OV6 = '%s,%s,%s,">"&{in:chase}' % (R('fee_log', 'status'), BILLED, R('fee_log', 'days_since'))
OL6 = '%s,%s,%s,">"&{in:old}' % (R('fee_log', 'status'), BILLED, R('fee_log', 'days_since'))
def BAND(i): return 'INDEX(%s,%d)' % (R('fee_ageing', 'open_amount'), i)
BIL90 = 'SUMIFS(%s,%s,%s,%s,%s)' % (R('fee_log', 'amount_due'), R('fee_log', 'billed'), YES, R('fee_log', 'date'), D90)
COL90 = 'SUMIFS(%s,%s,%s)' % (R('fee_log', 'collected'), R('fee_log', 'date'), D90)
tools.append(TOOL('ageing_tool', 'Fee Collection Ageing', 'Which open fees do I chase and which do I write off',
    'Type the day you chase after and the day you review a fee for write-off; billed, collected, open and written-off fees are shown by age from the Fee Log.', [
    I('chase', 'Chase a fee after, days', 14, 'int'), I('old', 'Review a fee for write-off after, days', 90, 'int')], [
    O('Open fees now', 'int', 'COUNTIFS(%s,%s)' % (R('fee_log', 'status'), BILLED)), O('Open amount now', 'money', AMT6), O('Open fees older than the chase day', 'int', 'COUNTIFS(%s)' % OV6),
    O('Open amount older than the chase day', 'money', 'SUMIFS(%s,%s)' % (R('fee_log', 'open_amount'), OV6)), O('Open fees older than the write-off day', 'int', 'COUNTIFS(%s)' % OL6),
    O('Open amount older than the write-off day', 'money', 'SUMIFS(%s,%s)' % (R('fee_log', 'open_amount'), OL6)),
    O('Billed, last 90 days', 'money', BIL90), O('Collected, last 90 days', 'money', COL90), O('Collection rate, last 90 days', 'pct', 'IFERROR(%s/%s,0)' % (COL90, BIL90)),
    O('Written off, last 90 days', 'money', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('fee_log', 'amount_due'), R('fee_log', 'status'), WOFF, R('fee_log', 'date'), D90)),
    O('Open amount, 0 to 14 days', 'money', BAND(1)), O('Open amount, 15 to 30 days', 'money', BAND(2)), O('Open amount, 31 to 90 days', 'money', BAND(3)), O('Open amount, 91 to 180 days', 'money', BAND(4)), O('Open amount, over 180 days', 'money', BAND(5)),
    O('Verdict', 'text', 'IF(COUNTIFS(%s)=0,%s,IF(SUMIFS(%s,%s)>0,%s,%s))' % (OV6, c2('Nothing to chase'), R('fee_log', 'open_amount'), OL6, c2('Chase and review write-offs'), c2('Chase the open fees')))],
    GR('What if', ('Chase after 7 days', {'chase': 7}), ('Chase after 30 days', {'chase': 30}), ('Write-off review at 60 days', {'old': 60}), ('Write-off review at 180 days', {'old': 180}), ('Chase after 90 days', {'chase': 90}))))

# 7 ------------------------------------------------------------ money left on the table
WIN7 = '%s,">="&EDATE({today},-{in:months})' % R('fee_log', 'date')
NB7 = 'SUMIFS(%s,%s)' % (R('fee_log', 'not_billed_amt'), WIN7)
def NBK(kind): return 'SUMIFS(%s,%s,%s,%s)' % (R('fee_log', 'not_billed_amt'), R('fee_log', 'kind'), kind, WIN7)
tools.append(TOOL('left_tool', 'Money Left Finder', 'How much did I leave on the table by not billing a fee',
    'Type how many months to look back and the share you could still collect; fees that were due and never billed are added up by kind and compared with the month before.', [
    I('months', 'Months to look back', 3, 'int'), I('recover', 'Share you expect to collect when you bill late', 0.85, 'pct')], [
    O('Fees due and never billed', 'money', NB7), O('Fees never billed, count', 'int', 'COUNTIFS(%s,%s,%s)' % (R('fee_log', 'billed'), NO, WIN7)), O('Extra mileage never billed', 'money', NBK(KE)),
    O('Late return never billed', 'money', NBK(KL)), O('Cleaning never billed', 'money', NBK(KC)), O('Refill never billed', 'money', NBK(KR)),
    O('Share of all fees due that was never billed', 'pct', 'IFERROR(%s/SUMIFS(%s,%s),0)' % (NB7, R('fee_log', 'amount_due'), WIN7)),
    O('Never billed this month', 'money', 'SUMIFS(%s,%s,%s)' % (R('fee_log', 'not_billed_amt'), R('fee_log', 'month'), MS)),
    O('Never billed last month', 'money', 'SUMIFS(%s,%s,EDATE(%s,-1))' % (R('fee_log', 'not_billed_amt'), R('fee_log', 'month'), MS)),
    O('You can still collect, about', 'money', '%s*{in:recover}' % NB7), O('Left on the table in a year at this pace', 'money', 'IFERROR(%s/{in:months}*12,0)' % NB7),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (NB7, c2('Bill the fees now'), c2('Nothing missed')))],
    GR('What if', ('Look back 1 month', {'months': 1}), ('Look back 6 months', {'months': 6}), ('Look back 12 months', {'months': 12}), ('Collect half', {'recover': 0.5}), ('Collect all', {'recover': 1.0}))))

# 8 ------------------------------------------------------------ damage claim tracker
tools.append(TOOL('claim_tracker', 'Damage Claim Tracker', 'Do I chase, wait for the repair or close this claim',
    'Type days open, estimate, deposit held and amount paid; the gap and your average days to close say chase or wait (status and amounts only).', [
    I('days', 'Days the claim has been open', 52, 'int'), I('est', 'Estimate', 760), I('dep', 'Deposit still held', 350), I('paid', 'Amount paid so far', 0), I('done', 'Repair finished, 1 for yes', 0, 'int')], [
    O('Days past your chase day', 'int', '{in:days}-{set:claim_chase_days}'), O('Amount still to recover', 'money', 'MAX(0,{in:est}-{in:paid})'), O('Share of the estimate the deposit covers', 'pct', 'IF({in:est}>0,MIN(1,{in:dep}/{in:est}),0)'),
    O('Gap left after the deposit', 'money', 'MAX(0,{in:est}-{in:paid}-{in:dep})'), O('Average days to close, last 12 months', 'num', 'IFERROR(AVERAGEIFS(%s,%s,%s),0)' % (R('claims', 'days_open'), R('claims', 'closed_on'), D365)),
    O('Open claims now', 'int', 'COUNTIFS(%s,%s)' % (R('claims', 'open_flag'), OPENC)), O('Open claims past your chase day', 'int', 'COUNTIFS(%s,%s,%s,">"&{set:claim_chase_days})' % (R('claims', 'open_flag'), OPENC, R('claims', 'days_open'))),
    O('Estimate of all open claims', 'money', 'SUMIFS(%s,%s,%s)' % (R('claims', 'estimate'), R('claims', 'open_flag'), OPENC)),
    O('Verdict', 'text', 'IF({in:est}-{in:paid}<=0,%s,IF({in:days}>{set:claim_chase_days},%s,%s))' % (c2('Close the claim'), c2('Chase the claim'), c2('Wait for the repair')))],
    GR('What if', ('A fresh claim, 5 days', {'days': 5}), ('Paid in full', {'paid': 760}), ('Deposit covers it', {'est': 300}), ('Open 90 days', {'days': 90}), ('A larger estimate', {'est': 1500}))))

# 9 ------------------------------------------------------------ claim chase list
SC = R('claims', 'chase_score')
def CK(k, col): return 'IFERROR(IF(LARGE(%s,%d)>0,INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),""),"")' % (SC, k, R('claims', col), SC, k, SC)
def CKN(k, col): return 'IFERROR(IF(LARGE(%s,%d)>0,INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),0),0)' % (SC, k, R('claims', col), SC, k, SC)
tools.append(TOOL('chase_list', 'Claim Chase List', 'Which open claim do I chase first',
    'Open claims are ranked by days open times the estimate; the first three show the claim, the days, the estimate and the deposit still held. Type the days after which a claim counts as late.', [
    I('mind', 'Count a claim as late after, days', 30, 'int')], [
    O('Chase first, claim', 'text', CK(1, 'claim_id')), O('Chase first, vehicle', 'text', CK(1, 'vehicle')), O('Chase first, renter', 'text', CK(1, 'renter')), O('Chase first, days open', 'int', CKN(1, 'days_open')),
    O('Chase first, estimate', 'money', CKN(1, 'estimate')), O('Chase first, deposit still held', 'money', CKN(1, 'deposit_held_now')),
    O('Second, claim', 'text', CK(2, 'claim_id')), O('Second, days open', 'int', CKN(2, 'days_open')), O('Second, estimate', 'money', CKN(2, 'estimate')),
    O('Third, claim', 'text', CK(3, 'claim_id')), O('Third, days open', 'int', CKN(3, 'days_open')), O('Third, estimate', 'money', CKN(3, 'estimate')),
    O('Open claims now', 'int', 'COUNTIFS(%s,%s)' % (R('claims', 'open_flag'), OPENC)), O('Open claims later than your day', 'int', 'COUNTIFS(%s,%s,%s,">"&{in:mind})' % (R('claims', 'open_flag'), OPENC, R('claims', 'days_open'))),
    O('Estimate of those claims', 'money', 'SUMIFS(%s,%s,%s,%s,">"&{in:mind})' % (R('claims', 'estimate'), R('claims', 'open_flag'), OPENC, R('claims', 'days_open'))),
    O('Deposits still held on open claims', 'money', 'SUM(%s)' % R('claims', 'deposit_held_now')),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,%s)=0,%s,%s)' % (R('claims', 'open_flag'), OPENC, c2('No open claim'), c2('Chase the first claim')))],
    GR('What if', ('Late after 14 days', {'mind': 14}), ('Late after 45 days', {'mind': 45}), ('Late after 60 days', {'mind': 60}), ('Late after 7 days', {'mind': 7}), ('Late after 90 days', {'mind': 90}))))

# 10 ----------------------------------------------------------- net damage cost per 100 rentals
M10 = 'EDATE(%s,-{in:back})' % MS
RENT10 = 'SUMIFS(%s,%s,%s)' % (R('claims_month', 'rentals'), R('claims_month', 'month'), M10); NET10 = 'SUMIFS(%s,%s,%s)' % (R('claims_month', 'net_cost'), R('claims_month', 'month'), M10)
RATE10 = 'IF(%s>0,%s/%s*100,0)' % (RENT10, NET10, RENT10)
AVG10 = 'IFERROR(AVERAGEIFS(%s,%s,">="&EDATE(%s,-3),%s,"<"&%s),0)' % (R('claims_month', 'damage_rate'), R('claims_month', 'month'), M10, R('claims_month', 'month'), M10)
Y10 = 'IFERROR(SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&%s)/SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&%s)*100,0)' % (R('claims_month', 'net_cost'), R('claims_month', 'month'), MS, R('claims_month', 'month'), MS, R('claims_month', 'rentals'), R('claims_month', 'month'), MS, R('claims_month', 'month'), MS)
tools.append(TOOL('damage_rate_tool', 'Damage Cost per 100 Rentals', 'Is damage cost above, on or below my usual',
    'Choose how many months back; the net damage cost per 100 rentals (repair cost less deposit used and claims paid) is set against your own 3 months before and your last 12 months.', [
    I('back', 'Months back from this month', 1, 'int'), I('tol', 'Band around your usual', 0.15, 'pct')], [
    O('Month looked at', 'date', M10), O('Rentals started', 'int', RENT10), O('Claims reported', 'int', 'SUMIFS(%s,%s,%s)' % (R('claims_month', 'reported'), R('claims_month', 'month'), M10)),
    O('Net damage cost', 'money', NET10), O('Net damage cost per 100 rentals', 'money', RATE10), O('Your average of the 3 months before', 'money', AVG10), O('Your rate, last 12 months', 'money', Y10),
    O('Change against your usual', 'pct', 'IF(%s>0,%s/%s-1,0)' % (AVG10, RATE10, AVG10)),
    O('Verdict', 'text', 'IF(%s>%s*(1+{in:tol}),%s,IF(%s<%s*(1-{in:tol}),%s,%s))' % (RATE10, AVG10, c2('Above your usual'), RATE10, AVG10, c2('Below your usual'), c2('On your usual')))],
    GR('What if', ('Two months back', {'back': 2}), ('Three months back', {'back': 3}), ('Six months back', {'back': 6}), ('A wider band, 30 percent', {'tol': 0.3}), ('A tight band, 5 percent', {'tol': 0.05}))))

# 11 ----------------------------------------------------------- repeat-damage finder
RS = R('segments', 'rank_score')
def SG(k, col): return 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),"")' % (R('segments', col), RS, k, RS)
def SGN(k, col): return 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),0)' % (R('segments', col), RS, k, RS)
OV11 = 'IFERROR(SUMIFS(%s,%s,%s)/SUMIFS(%s,%s,%s),0)' % (R('segments', 'net_cost'), R('segments', 'kind'), tok('segkind', 'Class'), R('segments', 'rentals'), R('segments', 'kind'), tok('segkind', 'Class'))
HIGH11 = 'COUNTIFS(%s,">"&{in:ratio}*%s)' % (RS, OV11)
tools.append(TOOL('repeat_damage', 'Repeat-Damage Finder', 'Which segment needs a larger deposit',
    'Segments are ranked by net damage cost per rental over 12 months; type the multiple of the average that counts as high and a deposit increase to test.', [
    I('ratio', 'Times the average that counts as high', 1.5, 'num'), I('uplift', 'Deposit increase to test', 0.25, 'pct')], [
    O('Average net damage cost per rental', 'money', OV11), O('Highest, segment', 'text', SG(1, 'segment')), O('Highest, cost per rental', 'money', SGN(1, 'cost_rental')), O('Highest, rentals', 'int', SGN(1, 'rentals')), O('Highest, claims', 'int', SGN(1, 'claims')),
    O('Highest, times the average', 'num', 'IF(%s>0,%s/%s,0)' % (OV11, SGN(1, 'cost_rental'), OV11)), O('Second, segment', 'text', SG(2, 'segment')), O('Second, cost per rental', 'money', SGN(2, 'cost_rental')),
    O('Third, segment', 'text', SG(3, 'segment')), O('Third, cost per rental', 'money', SGN(3, 'cost_rental')), O('Segments above your multiple', 'int', HIGH11),
    O('Average deposit', 'money', 'AVERAGE(%s)' % R('classes', 'deposit')), O('Average deposit with the increase', 'money', 'AVERAGE(%s)*(1+{in:uplift})' % R('classes', 'deposit')),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (HIGH11, c2('Ask a larger deposit'), c2('No segment stands out')))],
    GR('What if', ('A lower bar, 1.2 times', {'ratio': 1.2}), ('A higher bar, 2 times', {'ratio': 2.0}), ('Deposit up 10 percent', {'uplift': 0.1}), ('Deposit up 50 percent', {'uplift': 0.5}), ('A very high bar, 3 times', {'ratio': 3.0}))))

# 12 ----------------------------------------------------------- deposit size test
DEP12 = 'SUMIFS(%s,%s,{in:cls})' % (R('classes', 'deposit'), R('classes', 'class'))
SEL12 = '(%s={in:cls})*(%s>0)*(%s>={today}-365)' % (R('claims', 'class'), R('claims', 'repair_cost'), R('claims', 'reported_on'))
N12 = 'SUMPRODUCT(%s)' % SEL12
PT12 = 'IF(%s>0,SUMPRODUCT(SMALL(%s*%s+(1-%s)*1000000,ROUNDUP({in:target}*%s,0))),0)' % (N12, SEL12, R('claims', 'repair_cost'), SEL12, N12)
tools.append(TOOL('deposit_test', 'Deposit Size Test', 'Is the deposit of this class large enough',
    'Choose a class and the share of damage cases the deposit should cover; repair costs of the last 12 months are set against the deposit held on the card (status and amounts only).', [
    IL('cls', 'Vehicle class', 'class', 'Compact'), I('target', 'Share of damage cases the deposit should cover', 0.8, 'pct')], [
    O('Deposit held', 'money', DEP12), O('Claims with a repair cost, last 12 months', 'int', N12),
    O('Average repair cost', 'money', 'IFERROR(AVERAGEIFS(%s,%s,{in:cls},%s,">0",%s,%s),0)' % (R('claims', 'repair_cost'), R('claims', 'class'), R('claims', 'repair_cost'), R('claims', 'reported_on'), D365)),
    O('Share of claims the deposit covers', 'pct', 'IF(%s>0,SUMPRODUCT(%s*(%s<=%s))/%s,0)' % (N12, SEL12, R('claims', 'repair_cost'), DEP12, N12)),
    O('Repair cost at your cover share', 'money', PT12), O('Raise the deposit by', 'money', 'MAX(0,%s-%s)' % (PT12, DEP12)), O('Deposit needed', 'money', 'MAX(%s,%s)' % (PT12, DEP12)),
    O('Net damage cost per rental, this class', 'money', 'SUMIFS(%s,%s,{in:cls})' % (R('segments', 'cost_rental'), R('segments', 'segment'))),
    O('Deposit held as a share of the average repair', 'pct', 'IFERROR(%s/AVERAGEIFS(%s,%s,{in:cls},%s,">0"),0)' % (DEP12, R('claims', 'repair_cost'), R('claims', 'class'), R('claims', 'repair_cost'))),
    O('Verdict', 'text', 'IF(%s>%s,%s,%s)' % (PT12, DEP12, c2('Raise the deposit'), c2('Keep the deposit')))],
    GR('What if', ('Premium class', {'cls': '=' + tok('class', 'Premium')}), ('Midsize SUV class', {'cls': '=' + tok('class', 'Midsize SUV')}), ('Cover 90 percent', {'target': 0.9}), ('Cover half', {'target': 0.5}), ('Economy class', {'cls': '=' + tok('class', 'Economy')}))))

# 13 ----------------------------------------------------------- cover option effect
CV = tok('segkind', 'Cover option')
def SEGV(col, flag): return 'SUMIFS(%s,%s,%s,%s,%s)' % (R('segments', col), R('segments', 'kind'), CV, R('segments', 'flag'), flag)
WITH13 = 'IFERROR(%s/%s,0)' % (SEGV('net_cost', YES), SEGV('rentals', YES)); WITHOUT13 = 'IFERROR(%s/%s,0)' % (SEGV('net_cost', NO), SEGV('rentals', NO))
tools.append(TOOL('cover_effect', 'Cover Option Effect', 'Does a cover option lower what damage costs me',
    'Net damage cost per rental with and without a cover option over 12 months (status and amounts only, check your insurance terms), set against the cover price you charge.', [
    I('price', 'Cover price a day', 11), I('days', 'Average rental days', 4, 'int'), I('gap', 'Saving per rental that counts as a real effect', 0.2, 'pct')], [
    O('Rentals with a cover option', 'int', SEGV('rentals', YES)), O('Rentals without a cover option', 'int', SEGV('rentals', NO)), O('Share of rentals with cover', 'pct', 'IFERROR(%s/(%s+%s),0)' % (SEGV('rentals', YES), SEGV('rentals', YES), SEGV('rentals', NO))),
    O('Claims with a cover option', 'int', SEGV('claims', YES)), O('Claims without a cover option', 'int', SEGV('claims', NO)), O('Net damage cost per rental, with cover', 'money', WITH13), O('Net damage cost per rental, without cover', 'money', WITHOUT13),
    O('Difference per rental', 'money', '%s-%s' % (WITHOUT13, WITH13)), O('Cover income per rental', 'money', '{in:price}*{in:days}'),
    O('Cover income less the damage difference', 'money', '{in:price}*{in:days}+(%s-%s)' % (WITHOUT13, WITH13)),
    O('Verdict', 'text', 'IF(%s-%s>={in:gap}*%s,%s,%s)' % (WITHOUT13, WITH13, WITHOUT13, c2('Promote cover'), c2('Cover is neutral')))],
    GR('What if', ('Cover price 8', {'price': 8}), ('Cover price 15', {'price': 15}), ('Rentals of 7 days', {'days': 7}), ('A small effect counts, 5 percent', {'gap': 0.05}), ('A large effect only, 50 percent', {'gap': 0.5}))))

# 14 ----------------------------------------------------------- toll and ticket pass-through
tools.append(TOOL('toll_pass', 'Toll and Ticket Pass-Through', 'Do I pass this toll or ticket on to the renter',
    'Type the amount, your admin fee and how many rentals had the car on that date; the amount to pass on and a verdict follow, with the items waiting on the Toll Match sheet.', [
    I('amount', 'Toll or ticket amount', 9.5), I('admin', 'Admin fee', 12), I('found', 'Rentals that had the car on that date', 1, 'int'), I('passed', 'Already passed on or paid, 1 for yes', 0, 'int')], [
    O('Amount to pass on', 'money', '{in:amount}+{in:admin}'), O('Admin fee share of the amount passed on', 'pct', 'IFERROR({in:admin}/({in:amount}+{in:admin}),0)'),
    O('Items to pass on now', 'int', 'COUNTIFS(%s,%s)' % (R('toll_match', 'verdict'), ca('Pass on'))), O('Amount to pass on now', 'money', 'SUMIFS(%s,%s,%s)' % (R('toll_match', 'to_pass'), R('toll_match', 'verdict'), ca('Pass on'))),
    O('Items with no rental found', 'int', 'COUNTIFS(%s,%s)' % (R('toll_match', 'verdict'), ca('No rental found'))),
    O('Passed on, last 90 days', 'money', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('tolls', 'recovered'), R('tolls', 'status'), tok('tollstatus', 'Passed on'), R('tolls', 'passed_on'), D90)),
    O('Absorbed, last 90 days', 'money', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('tolls', 'amount'), R('tolls', 'status'), tok('tollstatus', 'Absorbed'), R('tolls', 'date'), D90)),
    O('Average days to pass on, last 90 days', 'num', 'IFERROR(AVERAGEIFS(%s,%s,%s),0)' % (R('tolls', 'days_to_pass'), R('tolls', 'passed_on'), D90)),
    O('Verdict', 'text', 'IF({in:found}=0,%s,IF({in:passed}=1,%s,%s))' % (c3('No rental found'), c3('Handled by the renter'), c3('Pass on')))],
    GR('What if', ('No rental found', {'found': 0}), ('Already passed on', {'passed': 1}), ('A parking ticket, 45', {'amount': 45}), ('Admin fee 20', {'admin': 20}), ('Admin fee 0', {'admin': 0}))))

# 15 ----------------------------------------------------------- toll admin fee check
P15 = '%s,%s' % (R('tolls', 'date'), D365)
T_OPEN = tok('tollstatus', 'Open')
SH15 = 'IFERROR(COUNTIFS(%s,%s,%s)/(COUNTIFS(%s,%s,%s)+COUNTIFS(%s,%s,%s)+COUNTIFS(%s,%s,%s)),0)' % (R('tolls', 'status'), tok('tollstatus', 'Passed on'), P15, R('tolls', 'status'), tok('tollstatus', 'Passed on'), P15,
                                                                                               R('tolls', 'status'), tok('tollstatus', 'Absorbed'), P15, R('tolls', 'status'), T_OPEN, P15)
COST15 = '{in:mins}/60*{in:hour}'
NEED15 = 'IF(%s>0,%s/%s,%s)' % (SH15, COST15, SH15, COST15)
tools.append(TOOL('toll_admin_check', 'Toll Admin Fee Check', 'Does the admin fee cover the work of a toll or ticket',
    'Type the admin fee, the minutes to process one item and the cost of a staff hour; the fee is set against the work and against the share of items you really recover in 12 months.', [
    I('fee', 'Admin fee', 12), I('mins', 'Minutes to process one item', 15, 'int'), I('hour', 'Cost of one staff hour', 17)], [
    O('Cost to process one item', 'money', COST15), O('Margin on one item', 'money', '{in:fee}-%s' % COST15), O('Items, last 12 months', 'int', 'COUNTIFS(%s)' % P15), O('Items passed on, last 12 months', 'int', 'COUNTIFS(%s,%s,%s)' % (R('tolls', 'status'), tok('tollstatus', 'Passed on'), P15)),
    O('Share of items with a rental that you recover', 'pct', SH15), O('Absorbed, last 12 months', 'money', 'SUMIFS(%s,%s,%s,%s)' % (R('tolls', 'amount'), R('tolls', 'status'), tok('tollstatus', 'Absorbed'), P15)),
    O('Admin fees charged, last 12 months', 'money', 'SUMIFS(%s,%s)' % (R('tolls', 'admin_fee'), P15)), O('Fee that covers the work after unrecovered items', 'money', 'ROUNDUP(%s,0)' % NEED15),
    O('Verdict', 'text', 'IF({in:fee}>=%s,%s,%s)' % (NEED15, c3('Fee covers the work'), c3('Raise the fee')))],
    GR('What if', ('Fee 5', {'fee': 5}), ('Fee 20', {'fee': 20}), ('30 minutes an item', {'mins': 30}), ('A staff hour costs 30', {'hour': 30}), ('5 minutes an item', {'mins': 5}))))

# 16 ----------------------------------------------------------- renter go or no-go
V16 = 'IF({in:status}=%s,%s,IF(OR({in:status}=%s,{in:docs}<>1,AND({in:extra}=1,{in:extraok}<>1)),%s,%s))' % (tok('rstatus', 'Restricted'), c3('No-go'), tok('rstatus', 'Documents due'), c3('Hold, documents due'), c3('Go'))
tools.append(TOOL('go_nogo', 'Renter Go or No-Go Screen', 'Do I hand the car to this renter',
    'Choose age band and status and say whether documents and an extra driver are checked (1 for yes); the verdict is go, hold or no-go. No licence numbers are kept.', [
    IL('age', 'Age band', 'ageband', '25 and over'), IL('status', 'Renter status', 'rstatus', 'Verified'), I('docs', 'Documents checked, 1 for yes', 1, 'int'), I('extra', 'An extra driver is added, 1 for yes', 0, 'int'),
    I('extraok', 'Extra driver documents checked, 1 for yes', 1, 'int')], [
    O('Verdict', 'text', V16),
    O('Next step', 'text', 'IF(%s=%s,%s,IF(%s=%s,%s,%s))' % (V16, c3('Go'), c3('Hand over the car'), V16, c3('No-go'), c3('Do not rent'), c3('Ask for the documents'))),
    O('Young-driver check', 'text', 'IF({in:age}=%s,%s,%s)' % (tok('ageband', 'Under 25'), c3('Add the young-driver fee'), c3('No extra fee'))),
    O('Renters with documents due', 'int', 'COUNTIFS(%s,%s)' % (R('renter_status', 'status'), tok('rstatus', 'Documents due'))), O('Restricted renters', 'int', 'COUNTIFS(%s,%s)' % (R('renter_status', 'status'), tok('rstatus', 'Restricted'))),
    O('Renters under 25', 'int', 'COUNTIFS(%s,%s)' % (R('renter_status', 'age_band'), tok('ageband', 'Under 25'))), O('Share of renters ready to go', 'pct', 'IFERROR(COUNTIFS(%s,%s)/COUNTA(%s),0)' % (R('renter_status', 'verdict'), ca('Go'), R('renter_status', 'renter_id')))],
    GR('What if', ('Documents due', {'status': '=' + tok('rstatus', 'Documents due'), 'docs': 0}), ('Restricted', {'status': '=' + tok('rstatus', 'Restricted')}), ('Under 25', {'age': '=' + tok('ageband', 'Under 25')}),
       ('Extra driver not checked', {'extra': 1, 'extraok': 0}), ('Documents not checked', {'docs': 0}))))

# 17 ----------------------------------------------------------- damage write-off review
WIN17 = '%s,">="&EDATE({today},-{in:months})' % R('claims', 'reported_on')
REP17 = 'SUMIFS(%s,%s)' % (R('claims', 'repair_cost'), WIN17); REC17 = 'SUMIFS(%s,%s)' % (R('claims', 'recovered'), WIN17)
SHARE17 = 'IFERROR(%s/%s,0)' % (REC17, REP17)
def WO(ch): return 'SUMIFS(%s,%s,%s,%s)' % (R('claims', 'written_off'), R('claims', 'channel'), tok('channel', ch), WIN17)
tools.append(TOOL('writeoff_review', 'Damage Write-Off Review', 'Is enough of the repair cost coming back',
    'Choose the months to review; repair cost, the part recovered from deposits and claims and the part written off are shown by channel (status and amounts only).', [
    I('months', 'Months to review', 12, 'int'), I('target', 'Share of repair cost you want to recover', 0.8, 'pct')], [
    O('Repair cost', 'money', REP17), O('Recovered, deposits used and claims paid', 'money', REC17), O('Written off', 'money', 'SUMIFS(%s,%s)' % (R('claims', 'written_off'), WIN17)), O('Share recovered', 'pct', SHARE17),
    O('Gap to your target share', 'pct', '%s-{in:target}' % SHARE17), O('Claims reviewed', 'int', 'COUNTIFS(%s)' % WIN17),
    O('Written off, Website', 'money', WO('Website')), O('Written off, Phone', 'money', WO('Phone')), O('Written off, Corporate account', 'money', WO('Corporate account')), O('Written off, Hotel partner', 'money', WO('Hotel partner')),
    O('Written off, Marketplace A', 'money', WO('Marketplace A')), O('Written off, Marketplace B', 'money', WO('Marketplace B')),
    O('Verdict', 'text', 'IF(%s<{in:target},%s,%s)' % (SHARE17, c3('Recovery low, tighten terms'), c3('Recovery is fine')))],
    GR('What if', ('Review 6 months', {'months': 6}), ('Review 24 months', {'months': 24}), ('Target 95 percent', {'target': 0.95}), ('Target 60 percent', {'target': 0.6}), ('Review 3 months', {'months': 3}))))

# 18 ----------------------------------------------------------- photo discipline score
def SC18(st): return 'IFERROR(COUNTIFS(%s,%s,%s,%s,%s,%s,%s,">=2",%s,%s)/COUNTIFS(%s,%s,%s,%s),0)' % (R('checkout', 'handled_by'), st, R('checkout', 'photos_out'), YES, R('checkout', 'photos_in'), YES, R('checkout', 'keys'),
                                                                                                R('checkout', 'in_date'), '">="&({today}-{in:days})', R('checkout', 'handled_by'), st, R('checkout', 'in_date'), '">="&({today}-{in:days})')
ALL18 = 'IFERROR(COUNTIFS(%s,%s,%s,%s,%s,">=2",%s,%s)/COUNTIFS(%s,%s),0)' % (R('checkout', 'photos_out'), YES, R('checkout', 'photos_in'), YES, R('checkout', 'keys'), R('checkout', 'in_date'), '">="&({today}-{in:days})', R('checkout', 'in_date'), '">="&({today}-{in:days})')
tools.append(TOOL('photo_score', 'Photo Discipline Score', 'Which staff member needs a reminder on photos and keys',
    'Choose a staff member and the days to look at; the share of returned handovers with photos both ways and two keys is set against your target (photos are a yes or no here, none are stored).', [
    IL('staff', 'Handled by', 'handler', 'Jun Park'), I('days', 'Days to look at', 90, 'int')], [
    O('Handovers by this staff member', 'int', 'COUNTIFS(%s,{in:staff},%s,%s)' % (R('checkout', 'handled_by'), R('checkout', 'in_date'), '">="&({today}-{in:days})')), O('Score of this staff member', 'pct', SC18('{in:staff}')),
    O('Score of the whole team', 'pct', ALL18), O('Your target', 'pct', '{set:photo_target}'), O('Gap to the target', 'pct', '%s-{set:photo_target}' % SC18('{in:staff}')),
    O('Score, Tomas Kowalski', 'pct', SC18(tok('handler', 'Tomas Kowalski'))), O('Score, Sana Malik', 'pct', SC18(tok('handler', 'Sana Malik'))), O('Score, Jun Park', 'pct', SC18(tok('handler', 'Jun Park'))), O('Score, Nadia Haddad', 'pct', SC18(tok('handler', 'Nadia Haddad'))),
    O('Verdict', 'text', 'IF(%s<{set:photo_target},%s,%s)' % (SC18('{in:staff}'), c3('Retrain'), c3('On target')))],
    GR('What if', ('Sana Malik', {'staff': '=' + tok('handler', 'Sana Malik')}), ('Tomas Kowalski', {'staff': '=' + tok('handler', 'Tomas Kowalski')}), ('Nadia Haddad', {'staff': '=' + tok('handler', 'Nadia Haddad')}), ('Last 30 days', {'days': 30}), ('Last 180 days', {'days': 180}))))
assert len(tools) == 18, len(tools)
