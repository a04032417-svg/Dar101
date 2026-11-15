"""Car rental suite part 6: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr6_lists import *
import cr6_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, dl): return IN(k, label, 'list', key(lst, dl), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def R(t, c): return '{range:%s.%s}' % (t, c)
TN = lambda c: R('turnaround', c); DR = lambda c: R('delivery_runs', c); SH = lambda c: R('shifts', c); PY = lambda c: R('pay', c)
SN = lambda c: R('staff_need', c); TK = lambda c: R('task_log', c); TM = lambda c: R('team', c); HM = lambda c: R('hours_month', c)
def LK(t, idc, c, val): return 'INDEX(%s,MATCH(%s,%s,0))' % (R(t, c), val, R(t, idc))
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
OWND = tok('paytype', 'Owner draw'); DONE = tok('runstatus', 'Done')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
D90 = lambda t, c: '%s,">="&({today}-90),%s,"<="&{today}' % (R(t, c), R(t, c))
tools = []

# 1 turnaround check --------------------------------------------------------------------------------------
S0 = 'IFERROR(INDEX(%s,MATCH({in:turn},%s,0)),"")' % (TN('slack_minutes'), TN('turn_id'))
def L1(c): return 'IFERROR(INDEX(%s,MATCH({in:turn},%s,0)),"")' % (TN(c), TN('turn_id'))
def L1D(c): return 'IFERROR(IF(INDEX(%s,MATCH({in:turn},%s,0))=0,"",INDEX(%s,MATCH({in:turn},%s,0))),"")' % (TN(c), TN('turn_id'), TN(c), TN('turn_id'))
SA = 'IF(%s="","",%s-{in:delay})' % (S0, S0)
tools.append(TOOL('turnaround_check', 'Turnaround Check', 'Is this car ready for its next pickup',
    'Type a turn ID from the Turnaround Board and a late start; the slack against the next pickup, the clean-by time and the verdict (ready on time, tight or late) appear.', [
    I('turn', 'Turn ID', D.TIGHT_ID, 'text'), I('delay', 'Minutes the detailer starts late', 0, 'int'), I('spare', 'Spare minutes you want before the pickup', 60, 'int')], [
    O('Vehicle', 'text', L1('vehicle')), O('Returned at', 'time', L1('returned_time')), O('Detailer', 'text', L1('cleaner')), O('Clean ends at, after the late start', 'time', 'IFERROR(MOD(%s+{in:delay}/1440,1),"")' % L1('clean_end')),
    O('Next pickup date', 'date', L1D('next_pickup')), O('Next pickup time', 'time', L1('next_pickup_time')), O('Slack now, minutes', 'int', S0), O('Slack after the late start, minutes', 'int', SA),
    O('Minutes above or below the spare you want', 'int', 'IF(%s="","",%s-{in:spare})' % (SA, SA)), O('Clean by', 'time', 'IFERROR(MOD(%s-{in:spare}/1440,1),"")' % L1('next_pickup_time')),
    O('Verdict', 'text', 'IF(%s="",%s,IF(%s<0,%s,IF(%s<{in:spare},%s,%s)))' % (SA, va('No pickup booked'), SA, va('Late, clean first'), SA, va('Tight, under the minimum'), va('Ready on time')))],
    GR('What if', ('Detailer starts 15 minutes late', {'delay': 15}), ('Detailer starts 30 minutes late', {'delay': 30}), ('Detailer starts 60 minutes late', {'delay': 60}),
       ('Want 30 spare minutes', {'spare': 30}), ('Want 120 spare minutes', {'spare': 120}))))

# 2 late-ready risk list ---------------------------------------------------------------------------------------
def RK(k, c): return 'IFERROR(INDEX(%s,MATCH(SMALL(%s,%d),%s,0)),"")' % (TN(c), TN('risk_key'), k, TN('risk_key'))
def RKD(c): return 'IFERROR(IF(INDEX(%s,MATCH(SMALL(%s,1),%s,0))=0,"",INDEX(%s,MATCH(SMALL(%s,1),%s,0))),"")' % (TN(c), TN('risk_key'), TN('risk_key'), TN(c), TN('risk_key'), TN('risk_key'))
RC = 'COUNTIFS(%s,">="&{today},%s,"<="&({today}+{in:days}),%s,"<"&{in:limit})' % (TN('next_pickup'), TN('next_pickup'), TN('slack_minutes'))
tools.append(TOOL('late_ready_list', 'Late-Ready Risk List', 'Which car do I clean first',
    'Cars with the least time left before their next pickup, in order: the three tightest cars, their slack and the verdict that names what to clean first.', [
    I('days', 'Look at pickups in the next days', 2, 'int'), I('limit', 'Slack minutes under which a car is at risk', 60, 'int')], [
    O('Cars at risk', 'int', RC), O('Cars already late', 'int', 'COUNTIFS(%s,">="&{today},%s,"<="&({today}+{in:days}),%s,"<0")' % (TN('next_pickup'), TN('next_pickup'), TN('slack_minutes'))),
    O('Tightest car', 'text', RK(1, 'vehicle')), O('Its slack, minutes', 'int', RK(1, 'slack_minutes')), O('Its class', 'text', RK(1, 'class')), O('Its next pickup', 'date', RKD('next_pickup')), O('Pickup time', 'time', RK(1, 'next_pickup_time')),
    O('Second tightest car', 'text', RK(2, 'vehicle')), O('Its slack, minutes', 'int', RK(2, 'slack_minutes')), O('Third tightest car', 'text', RK(3, 'vehicle')), O('Its slack, minutes', 'int', RK(3, 'slack_minutes')),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (RC, va('Clean the first car now'), va('No car at risk')))],
    GR('What if', ('Look 1 day ahead', {'days': 1}), ('Look 5 days ahead', {'days': 5}), ('Risk under 30 minutes', {'limit': 30}), ('Risk under 120 minutes', {'limit': 120}), ('Risk under 600 minutes', {'limit': 600}))))

# 3 turnaround against the buffer ---------------------------------------------------------------------------------------
SHR = 'IFERROR(COUNTIFS(%s,"<="&{in:buffer})/COUNT(%s),0)' % (TN('turn_minutes'), TN('turn_minutes'))
tools.append(TOOL('buffer_check', 'Turnaround Against the Buffer', 'Is my buffer long enough',
    'The share of cars ready within your buffer, the slowest class and the buffer it needs, with the tight and late shares of the last 90 days; the verdict says keep or raise.', [
    I('buffer', 'Buffer minutes after a return', 90, 'int'), I('target', 'Share of cars that must be ready within the buffer', 0.85, 'pct')], [
    O('Share ready within the buffer', 'pct', SHR), O('Average minutes from return to ready', 'num', 'IFERROR(AVERAGE(%s),0)' % TN('turn_minutes')),
    O('Slowest class', 'text', 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (R('turn_class', 'class'), R('turn_class', 'avg_turn'), R('turn_class', 'avg_turn'))), O('Its average minutes to ready', 'num', 'MAX(%s)' % R('turn_class', 'avg_turn')),
    O('Its share over the buffer on the Start sheet', 'pct', 'MAX(%s)' % R('turn_class', 'over_buffer')), O('Buffer that class needs, minutes', 'int', 'ROUNDUP((MAX(%s)+15)/15,0)*15' % R('turn_class', 'avg_turn')),
    O('Tight share, last 90 days', 'pct', 'IFERROR(COUNTIFS(%s,%s,"<"&{set:tight_min})/COUNTIFS(%s,%s,">=-100000"),0)' % (D90('turnaround', 'return_date'), TN('slack_minutes'), D90('turnaround', 'return_date'), TN('slack_minutes'))),
    O('Late share, last 90 days', 'pct', 'IFERROR(COUNTIFS(%s,%s,"<0")/COUNTIFS(%s,%s,">=-100000"),0)' % (D90('turnaround', 'return_date'), TN('slack_minutes'), D90('turnaround', 'return_date'), TN('slack_minutes'))),
    O('Average slack when the next pickup is within a day, minutes', 'int', 'IFERROR(AVERAGEIFS(%s,%s,"<1440"),0)' % (TN('slack_minutes'), TN('slack_minutes'))),
    O('Verdict', 'text', 'IF(%s>={in:target},%s,%s)' % (SHR, va('Keep the buffer'), va('Raise the buffer')))],
    GR('What if', ('Buffer 60 minutes', {'buffer': 60}), ('Buffer 75 minutes', {'buffer': 75}), ('Buffer 120 minutes', {'buffer': 120}), ('Buffer 150 minutes', {'buffer': 150}), ('Target 95 percent', {'target': 0.95}))))

# 4 cleaning cost per rental ---------------------------------------------------------------------------------------------
CM = lambda extra='': 'IFERROR(AVERAGEIFS(%s,%s,{in:class}%s),0)' % (TN('clean_minutes'), TN('class'), extra)
DIRTY = ',%s,%s' % (TN('dirty'), YES); NORM = ',%s,%s' % (TN('dirty'), NO)
EXTRA_COST = '((%s-%s)/60*{in:rate}*(1+{set:employer_cost_pct}))' % (CM(DIRTY), CM(NORM))
SHARE_D = 'IFERROR(COUNTIFS(%s,{in:class},%s,%s)/COUNTIFS(%s,{in:class}),0)' % (TN('class'), TN('dirty'), YES, TN('class'))
tools.append(TOOL('cleaning_cost', 'Cleaning Cost per Rental', 'Does my cleaning fee cover the extra work',
    'Pick a class and the detailer pay; average clean minutes, cost per rental, the share of very dirty cars and the extra cost of one very dirty car against your cleaning fee.', [
    IL('class', 'Vehicle class', 'class', '7-seat Van'), I('rate', 'Detailer pay for one hour', 17.0)], [
    O('Average clean minutes', 'num', CM()), O('Cleaning cost per rental, with employer costs', 'money', '%s/60*{in:rate}*(1+{set:employer_cost_pct})' % CM()), O('Share of very dirty cars', 'pct', SHARE_D),
    O('Average minutes of a very dirty car', 'num', CM(DIRTY)), O('Average minutes of a normal car', 'num', CM(NORM)), O('Extra minutes for a very dirty car', 'num', '%s-%s' % (CM(DIRTY), CM(NORM))),
    O('Extra cost of a very dirty car', 'money', EXTRA_COST), O('Cleaning fee you charge', 'money', '{set:cleaning_fee}'), O('Cleaning fee that covers the extra cost', 'money', 'ROUNDUP(%s,0)' % EXTRA_COST),
    O('Fee income per rental', 'money', '%s*{set:cleaning_fee}' % SHARE_D),
    O('Cleaning cost per rental after fee income', 'money', '%s/60*{in:rate}*(1+{set:employer_cost_pct})-%s*{set:cleaning_fee}' % (CM(), SHARE_D)),
    O('Verdict', 'text', 'IF({set:cleaning_fee}>=ROUNDUP(%s,0),%s,%s)' % (EXTRA_COST, va('Cleaning fee covers the extra work'), va('Price the cleaning fee higher')))],
    GR('What if', ('Midsize SUV', {'class': '=' + tok('class', 'Midsize SUV')}), ('Economy', {'class': '=' + tok('class', 'Economy')}), ('Premium', {'class': '=' + tok('class', 'Premium')}), ('Detailer pay 20', {'rate': 20}), ('Detailer pay 25', {'rate': 25}))))

# 5 cleaning queue planner ------------------------------------------------------------------------------------------------
def QV(k, c): return 'IFERROR(INDEX(%s,MATCH({in:date}*100+%d,%s,0)),"")' % (TN(c), k, TN('day_pos'))
NEED5 = 'SUMIFS(%s,%s,{in:date})/60' % (TN('clean_minutes'), TN('return_date'))
tools.append(TOOL('cleaning_queue', 'Cleaning Queue Planner', 'Do I have enough detailer hours for the returns of the day',
    'Pick a day and the detailer hours you have; the returns of that day come in the order of their next pickup, with the cleaning hours needed against the hours you have.', [
    I('date', 'Day', 'today', 'date'), I('hours', 'Detailer hours available that day', 4.0, 'num')], [
    O('Returns to clean', 'int', 'COUNTIFS(%s,{in:date})' % TN('return_date')), O('Cleaning minutes needed', 'int', 'SUMIFS(%s,%s,{in:date})' % (TN('clean_minutes'), TN('return_date'))),
    O('Cleaning hours needed', 'num', NEED5), O('Hours short', 'num', 'MAX(0,%s-{in:hours})' % NEED5), O('Hours to spare', 'num', 'MAX(0,{in:hours}-%s)' % NEED5),
    O('Clean first', 'text', QV(1, 'vehicle')), O('Its pickup time', 'time', QV(1, 'next_pickup_time')), O('Clean second', 'text', QV(2, 'vehicle')), O('Its pickup time', 'time', QV(2, 'next_pickup_time')),
    O('Clean third', 'text', QV(3, 'vehicle')), O('Its pickup time', 'time', QV(3, 'next_pickup_time')),
    O('Cost of the cleaning at your rate', 'money', '%s*{set:detailer_rate}*(1+{set:employer_cost_pct})' % NEED5),
    O('Verdict', 'text', 'IF(%s>{in:hours},%s,%s)' % (NEED5, va('Add detailer hours'), va('Enough detailer hours')))],
    GR('What if', ('Detailer hours 1', {'hours': 1}), ('Detailer hours 2', {'hours': 2}), ('Detailer hours 3', {'hours': 3}), ('Detailer hours 6', {'hours': 6}), ('Detailer hours 10', {'hours': 10}))))

# 6 delivery run planner -------------------------------------------------------------------------------------------------------
RD = lambda extra='': 'COUNTIFS(%s,{in:date}%s)' % (DR('date'), extra)
COST6 = '(SUMIFS(%s,%s,{in:date})+{in:wait}*%s/60*{set:driver_rate})' % (DR('driver_cost'), DR('date'), RD())
FEE6 = 'SUMIFS(%s,%s,{in:date})*(1+{in:fee_rise})' % (DR('fee_charged'), DR('date'))
tools.append(TOOL('run_planner', 'Delivery Run Planner', 'Do the fees of the day cover driver time and fuel',
    'Pick a day: its deliveries and collections, minutes, miles, driver cost and the fees collected; add waiting time or a fee rise to test the day.', [
    I('date', 'Day', 'today+1', 'date'), I('wait', 'Extra waiting minutes for each run', 0, 'int'), I('fee_rise', 'Fee rise to test', 0.0, 'pct')], [
    O('Runs that day', 'int', RD()), O('Deliveries', 'int', RD(',%s,%s' % (DR('kind'), tok('runkind', 'Delivery')))), O('Collections', 'int', RD(',%s,%s' % (DR('kind'), tok('runkind', 'Collection')))),
    O('Run minutes', 'int', 'SUMIFS(%s,%s,{in:date})+{in:wait}*%s' % (DR('minutes'), DR('date'), RD())), O('Run miles', 'int', 'SUMIFS(%s,%s,{in:date})' % (DR('miles'), DR('date'))),
    O('Driver hours', 'num', '(SUMIFS(%s,%s,{in:date})+{in:wait}*%s)/60' % (DR('minutes'), DR('date'), RD())), O('Driver cost with fuel', 'money', COST6), O('Delivery fees collected', 'money', FEE6),
    O('Fees minus cost', 'money', '%s-%s' % (FEE6, COST6)), O('Fees against cost', 'pct', 'IFERROR(%s/%s,0)' % (FEE6, COST6)), O('Short by', 'money', 'MAX(0,%s-%s)' % (COST6, FEE6)),
    O('Cost per run', 'money', 'IFERROR(%s/%s,0)' % (COST6, RD())), O('Fee per run', 'money', 'IFERROR(%s/%s,0)' % (FEE6, RD())),
    O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (FEE6, COST6, va('Fees cover driver time and fuel'), va('Fees are short of the cost')))],
    GR('What if', ('Waiting 10 minutes a run', {'wait': 10}), ('Waiting 20 minutes a run', {'wait': 20}), ('Fee rise 10 percent', {'fee_rise': 0.10}), ('Fee rise 25 percent', {'fee_rise': 0.25}), ('Today', {'date': '={today}'}))))

# 7 delivery fee check by zone -----------------------------------------------------------------------------------------------------
ZW = lambda c, e='': 'AVERAGEIFS(%s,%s,{in:zone},%s,">="&({today}-{set:window_days}),%s,"<="&{today}%s)' % (DR(c), DR('location'), DR('date'), DR('date'), e)
COST7 = '(IFERROR(%s,0)/60*{in:rate}+IFERROR(%s,0)*{in:mile_cost})' % (ZW('minutes'), ZW('miles'))
tools.append(TOOL('zone_fee_check', 'Delivery Fee Check by Zone', 'Does the fee of this zone cover the run',
    'Pick a zone and a fee for one leg; the average run minutes and miles of the last days become driver time and fuel, so you see profit per run and the fee that covers it.', [
    IL('zone', 'Zone', 'zone', 'Airport delivery'), I('fee', 'Fee for one leg', 18.0), I('rate', 'Driver pay for one hour', 16.0), I('mile_cost', 'Fuel or charge cost of one mile', 0.2), I('margin', 'Margin you want above the cost', 0.10, 'pct')], [
    O('Runs in the period', 'int', 'COUNTIFS(%s,{in:zone},%s,">="&({today}-{set:window_days}),%s,"<="&{today})' % (DR('location'), DR('date'), DR('date'))),
    O('Average run minutes', 'num', 'IFERROR(%s,0)' % ZW('minutes')), O('Average run miles', 'num', 'IFERROR(%s,0)' % ZW('miles')), O('Driver time cost', 'money', 'IFERROR(%s,0)/60*{in:rate}' % ZW('minutes')),
    O('Fuel or charge cost', 'money', 'IFERROR(%s,0)*{in:mile_cost}' % ZW('miles')), O('Cost of one run', 'money', COST7), O('Fee for one leg', 'money', '{in:fee}'), O('Profit per run', 'money', '{in:fee}-%s' % COST7),
    O('Fee against cost', 'pct', 'IFERROR({in:fee}/%s,0)' % COST7), O('Fee that covers cost and margin', 'money', 'ROUNDUP(%s*(1+{in:margin}),0)' % COST7),
    O('Raise the fee by', 'money', 'MAX(0,ROUNDUP(%s*(1+{in:margin}),0)-{in:fee})' % COST7),
    O('Verdict', 'text', 'IF({in:fee}>=%s*(1+{in:margin}),%s,%s)' % (COST7, va('Fee covers the cost'), va('Raise the fee')))],
    GR('What if', ('Fee 20', {'fee': 20}), ('Fee 22', {'fee': 22}), ('Fee 25', {'fee': 25}), ('Home delivery, fee 20', {'zone': '=' + tok('zone', 'Home delivery'), 'fee': 20}), ('Hotel district, fee 12', {'zone': '=' + tok('zone', 'Hotel district'), 'fee': 12}))))

# 8 least profitable zones -------------------------------------------------------------------------------------------------------------
ZPR = R('zone_profit', 'profit_run'); ZZ = R('zone_profit', 'zone')
def ZN(k): return 'INDEX(%s,MATCH(SMALL(%s,%d),%s,0))' % (ZZ, ZPR, k, ZPR)
ZMIN = lambda: 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('zones', 'run_minutes'), ZN(1), R('zones', 'location'))
tools.append(TOOL('least_profit_zones', 'Least Profitable Zones', 'Which zone do I reprice or drop',
    'The four delivery zones ranked by profit per run (fees minus driver time and fuel) and by profit per driver hour, with the fee rise that brings the weakest zone to your target.', [
    I('target', 'Profit per run you want', 5.0)], [
    O('Least profitable zone', 'text', ZN(1)), O('Its profit per run', 'money', 'SMALL(%s,1)' % ZPR), O('Its profit per driver hour', 'money', 'IFERROR(SMALL(%s,1)/(%s/60),0)' % (ZPR, ZMIN())),
    O('Second least profitable zone', 'text', ZN(2)), O('Its profit per run', 'money', 'SMALL(%s,2)' % ZPR), O('Third zone', 'text', ZN(3)), O('Its profit per run', 'money', 'SMALL(%s,3)' % ZPR),
    O('Most profitable zone', 'text', ZN(4)), O('Its profit per run', 'money', 'SMALL(%s,4)' % ZPR), O('Spread from best to worst', 'money', 'SMALL(%s,4)-SMALL(%s,1)' % (ZPR, ZPR)),
    O('Zones under your target', 'int', 'COUNTIFS(%s,"<"&{in:target})' % ZPR), O('Fee rise for the weakest zone to reach the target', 'money', 'MAX(0,{in:target}-SMALL(%s,1))' % ZPR),
    O('Runs of the weakest zone in the period', 'int', 'INDEX(%s,MATCH(SMALL(%s,1),%s,0))' % (R('zone_profit', 'runs'), ZPR, ZPR)),
    O('Verdict', 'text', 'IF(SMALL(%s,1)<{in:target},%s,%s)' % (ZPR, va('Reprice the weakest zone'), va('All zones earn the target')))],
    GR('What if', ('Target 2', {'target': 2}), ('Target 3', {'target': 3}), ('Target 8', {'target': 8}), ('Target 10', {'target': 10}), ('Target 0', {'target': 0}))))

# 9 driver assignment planner ----------------------------------------------------------------------------------------------------------------
FK = 'SMALL(%s,COUNTIFS(%s,"<"&{in:date})+1)' % (DR('fix_key'), DR('fix_key'))
def FX(c): return 'IFERROR(IF(INT(%s)={in:date},INDEX(%s,MATCH(%s,%s,0)),""),"")' % (FK, DR(c), FK, DR('fix_key'))
CLN = 'COUNTIFS(%s,">0",%s,{in:date})' % (DR('clash'), DR('date'))
tools.append(TOOL('driver_assignment', 'Driver Assignment Planner', 'Which driver takes the run that clashes',
    'Pick a day; the first run that clashes for its driver, its time and zone, and whether the other driver is free for it, with the verdict that names the run to move.', [
    I('date', 'Day', 'today+1', 'date')], [
    O('Runs that day', 'int', 'COUNTIFS(%s,{in:date})' % DR('date')), O('Runs that clash for their driver', 'int', CLN), O('Run to move', 'text', FX('run_id')), O('Its start time', 'time', FX('start_time')),
    O('Its zone', 'text', FX('location')), O('Its driver now', 'text', FX('driver')), O('Other driver', 'text', FX('other_driver')), O('Other driver free for it, 1 for yes', 'int', FX('other_free')),
    O('Runs of the other driver that day', 'int', 'IFERROR(COUNTIFS(%s,%s,%s,{in:date}),0)' % (DR('driver'), FX('other_driver'), DR('date'))),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s=1,%s,%s))' % (CLN, va('No clash, keep the plan'), FX('other_free'), va('Assign the run to the other driver'), va('Move the run to another time')))],
    GR('What if', ('Today', {'date': '={today}'}), ('In 2 days', {'date': '={today}+2'}), ('In 3 days', {'date': '={today}+3'}))))

# 10 run clash check ---------------------------------------------------------------------------------------------------------------------------
BOUND = '(IF({in:driver}=%s,1,2)*100000+{in:date})' % '{list:driver.jun_park}'
FKD = 'SMALL(%s,COUNTIFS(%s,"<"&%s)+1)' % (DR('drv_key'), DR('drv_key'), BOUND)
def FXD(c): return 'IFERROR(IF(INT(%s)=%s,INDEX(%s,MATCH(%s,%s,0)),""),"")' % (FKD, BOUND, DR(c), FKD, DR('drv_key'))
DC = 'COUNTIFS(%s,{in:driver},%s,{in:date})' % (DR('driver'), DR('date'))
DCL = 'COUNTIFS(%s,{in:driver},%s,{in:date},%s,">0")' % (DR('driver'), DR('date'), DR('clash'))
tools.append(TOOL('run_clash_check', 'Run Clash Check', 'Does this driver have runs that overlap',
    'Pick a driver and a day: runs, runs that overlap or leave too little travel time, driver hours against your shift limit and the first run to move.', [
    IL('driver', 'Driver', 'driver', 'Jun Park'), I('date', 'Day', 'today+1', 'date')], [
    O('Runs of the driver', 'int', DC), O('Runs that clash', 'int', DCL), O('Run minutes', 'int', 'SUMIFS(%s,%s,{in:driver},%s,{in:date})' % (DR('minutes'), DR('driver'), DR('date'))),
    O('Driver hours with 5 minutes between runs', 'num', '(SUMIFS(%s,%s,{in:driver},%s,{in:date})+5*%s)/60' % (DR('minutes'), DR('driver'), DR('date'), DC)),
    O('Hours above your shift limit', 'num', 'MAX(0,(SUMIFS(%s,%s,{in:driver},%s,{in:date})+5*%s)/60-{set:hours_limit})' % (DR('minutes'), DR('driver'), DR('date'), DC)),
    O('First run to move', 'text', FXD('run_id')), O('Its start time', 'time', FXD('start_time')), O('Its end time', 'time', FXD('end_time')), O('Its zone', 'text', FXD('location')),
    O('Minutes you need between runs', 'int', '{set:clash_min}'), O('Day', 'date', '{in:date}'),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (DCL, va('Clash found'), va('No clash, keep the plan')))],
    GR('What if', ('Today', {'date': '={today}'}), ('Ravi Chandran in 2 days', {'driver': '=' + tok('driver', 'Ravi Chandran'), 'date': '={today}+2'}))))

# 11 roster check against bookings ------------------------------------------------------------------------------------------------------------------
SW = lambda c: 'SUMIFS(%s,%s,">="&{in:from},%s,"<"&({in:from}+{in:days}))' % (SN(c), SN('date'), SN('date'))
SHORTN = 'COUNTIFS(%s,%s,%s,">="&{in:from},%s,"<"&({in:from}+{in:days}))' % (SN('status'), vb('Short'), SN('date'), SN('date'))
FS = 'SMALL(%s,COUNTIFS(%s,"<"&{in:from})+1)' % (SN('short_key'), SN('short_key'))
def FSD(c): return 'IFERROR(IF(%s<{in:from}+{in:days},INDEX(%s,MATCH(%s,%s,0)),""),"")' % (FS, SN(c), FS, SN('short_key'))
tools.append(TOOL('roster_check', 'Roster Check Against Bookings', 'Which days are short of staff',
    'Pick a start day and how many days to check; pickups, returns and runs become hours needed, set against the hours rostered, and the first short day is named.', [
    I('from', 'First day', 'today', 'date'), I('days', 'Days to check', 14, 'int')], [
    O('Days short of staff', 'int', SHORTN), O('Hours needed', 'num', SW('hours_needed')), O('Hours rostered', 'num', SW('hours_rostered')), O('Hours short, on short days only', 'num', 'SUMIFS(%s,%s,%s,%s,">="&{in:from},%s,"<"&({in:from}+{in:days}))' % (SN('gap'), SN('status'), vb('Short'), SN('date'), SN('date'))),
    O('First short day', 'date', FSD('date')), O('Hours short that day', 'num', FSD('gap')), O('Pickups that day', 'int', FSD('pickups')), O('Returns that day', 'int', FSD('returns')), O('Runs that day', 'int', FSD('runs')),
    O('Share of days covered', 'pct', 'IFERROR(1-%s/{in:days},0)' % SHORTN),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (SHORTN, vb('Add a shift'), vb('Staff cover is enough')))],
    GR('What if', ('Check 7 days', {'days': 7}), ('Check 21 days', {'days': 21}), ('Check 28 days', {'days': 28}), ('Check 10 days', {'days': 10}))))

# 12 hours cost per rental -----------------------------------------------------------------------------------------------------------------------------
MSI = 'DATE(YEAR({in:month}),MONTH({in:month}),1)'
CR = lambda a, b: 'IFERROR(SUMIFS(%s,%s,">="&%s,%s,"<"&%s)/SUMIFS(%s,%s,">="&%s,%s,"<"&%s),0)' % (HM('pay'), HM('month'), a, HM('month'), b, HM('rentals'), HM('month'), a, HM('month'), b)
NOW12 = CR(MSI, 'EDATE(%s,1)' % MSI); L3 = CR('EDATE(%s,-3)' % MSI, MSI); LY = CR('EDATE(%s,-12)' % MSI, 'EDATE(%s,-11)' % MSI)
tools.append(TOOL('hours_cost_check', 'Hours Cost per Rental', 'Is the cost of hours per rental above my usual',
    'Pick a month: shift pay and hours per rental against your last 3 months and the same month last year, and against your own target.', [
    I('month', 'Month', 'today', 'date'), I('band', 'Band around your usual', 0.05, 'pct')], [
    O('Hours cost per rental', 'money', NOW12), O('Hours per rental', 'num', 'IFERROR(SUMIFS(%s,%s,%s)/SUMIFS(%s,%s,%s),0)' % (HM('hours'), HM('month'), MSI, HM('rentals'), HM('month'), MSI)),
    O('Pay per hour', 'money', 'IFERROR(SUMIFS(%s,%s,%s)/SUMIFS(%s,%s,%s),0)' % (HM('pay'), HM('month'), MSI, HM('hours'), HM('month'), MSI)), O('Rentals started', 'int', 'SUMIFS(%s,%s,%s)' % (HM('rentals'), HM('month'), MSI)),
    O('Average of the last 3 months', 'money', L3), O('Same month last year', 'money', LY), O('Against the last 3 months', 'pct', 'IFERROR(%s/%s-1,0)' % (NOW12, L3)), O('Against last year', 'pct', 'IFERROR(%s/%s-1,0)' % (NOW12, LY)),
    O('Your target', 'money', '{set:cost_target}'), O('Over the target by', 'money', 'MAX(0,%s-{set:cost_target})' % NOW12),
    O('Extra pay against your usual', 'money', 'MAX(0,(%s-%s)*SUMIFS(%s,%s,%s))' % (NOW12, L3, HM('rentals'), HM('month'), MSI)),
    O('Verdict', 'text', 'IF(%s>%s*(1+{in:band}),%s,IF(%s<%s*(1-{in:band}),%s,%s))' % (NOW12, L3, vb('Above your usual'), NOW12, L3, vb('Below your usual'), vb('On your usual')))],
    GR('What if', ('Last month', {'month': '={today}-30'}), ('Two months ago', {'month': '={today}-60'}), ('Same month last year', {'month': '={today}-365'}), ('Band 10 percent', {'band': 0.10}), ('Band 20 percent', {'band': 0.20}))))

# 13 pay calculator --------------------------------------------------------------------------------------------------------------------------------------
MSP = 'DATE(YEAR({in:month}),MONTH({in:month}),1)'
HOURS13 = 'SUMIFS(%s,%s,{in:staff},%s,%s)' % (PY('hours'), PY('staff'), PY('month'), MSP)
RATE13 = 'IFERROR(INDEX(%s,MATCH({in:staff},%s,0)),0)' % (TM('hourly_rate'), TM('name'))
JOBS13 = '(COUNTIFS(%s,{in:staff},%s,">="&%s,%s,"<"&EDATE(%s,1),%s,%s)+COUNTIFS(%s,{in:staff},%s,">="&%s,%s,"<"&EDATE(%s,1)))' % (
    DR('driver'), DR('date'), MSP, DR('date'), MSP, DR('status'), DONE, TN('cleaner'), TN('return_date'), MSP, TN('return_date'), MSP)
G13 = 'IF({in:method}=2,%s*{in:job_rate},ROUND(%s*%s,2))' % (JOBS13, HOURS13, RATE13)
REC13 = 'SUMIFS(%s,%s,{in:staff},%s,%s)' % (PY('total'), PY('staff'), PY('month'), MSP)
RUN13 = 'SUMIFS(%s,%s,%s,%s,"<>"&%s)' % (PY('total'), PY('month'), MSP, PY('pay_type'), OWND)
tools.append(TOOL('pay_calculator', 'Pay Calculator', 'What does this staff member cost for the month',
    'Pick a staff member and a month: hours times the hourly rate, or jobs times a per-job rate, plus employer costs, against the pay recorded and the whole pay run of the month.', [
    IL('staff', 'Staff member', 'staff', 'Jun Park'), I('month', 'Month', 'today-30', 'date'), I('method', 'Pay by: 1 for hours, 2 for jobs', 1, 'int'), I('job_rate', 'Pay for one job, a run or a cleaned car', 9.0)], [
    O('Hours recorded', 'num', HOURS13), O('Hourly rate', 'money', RATE13), O('Jobs done, runs or cleaned cars', 'int', JOBS13), O('Gross pay', 'money', G13),
    O('Employer costs', 'money', '%s*{set:employer_cost_pct}' % G13), O('Total cost', 'money', '%s*(1+{set:employer_cost_pct})' % G13), O('Total recorded in the Pay sheet', 'money', REC13),
    O('Difference to the recorded total', 'money', '%s*(1+{set:employer_cost_pct})-%s' % (G13, REC13)), O('Pay run of the month, staff pay', 'money', RUN13),
    O('Share of the pay run', 'pct', 'IFERROR(%s*(1+{set:employer_cost_pct})/%s,0)' % (G13, RUN13)), O('Pay per hour with employer costs', 'money', 'IFERROR(%s*(1+{set:employer_cost_pct})/%s,0)' % (G13, HOURS13)),
    O('Verdict', 'text', 'IF(%s>0,IF(ABS(%s*(1+{set:employer_cost_pct})-%s)>{set:pay_tolerance},%s,%s),%s)' % (HOURS13, G13, REC13, vb('Check this pay line'), vb('Pay run is ready'), vb('Check the hours first')))],
    GR('What if', ('Pay by jobs', {'method': 2}), ('Jobs at 12', {'method': 2, 'job_rate': 12}), ('Detailer Lucia Fernandes', {'staff': '=' + tok('staff', 'Lucia Fernandes')}), ('Assistant Sana Malik', {'staff': '=' + tok('staff', 'Sana Malik')}), ('Two months ago', {'month': '={today}-60'}))))

# 14 long-day check ---------------------------------------------------------------------------------------------------------------------------------------------
LD = 'COUNTIFS(%s,">"&{in:limit},%s,">="&({today}-30),%s,"<="&{today})' % (SH('hours'), SH('date'), SH('date'))
MX = 'MATCH(LARGE(%s,1),%s,0)' % (SH('hours'), SH('hours'))
tools.append(TOOL('long_day_check', 'Long-Day Check', 'Which shifts are too long',
    'Type your longest shift and the most days in a week: shifts above the limit in the last 30 days, the longest shift and the weeks with no day off.', [
    I('limit', 'Longest shift in hours', 5.5, 'num'), I('days_max', 'Most days one person works in a week', 6, 'int')], [
    O('Shifts above the limit, last 30 days', 'int', LD), O('Hours above the limit, last 30 days', 'num', 'SUMIFS(%s,%s,">"&{in:limit},%s,">="&({today}-30),%s,"<="&{today})-{in:limit}*%s' % (SH('hours'), SH('hours'), SH('date'), SH('date'), LD)),
    O('Longest shift, hours', 'num', 'LARGE(%s,1)' % SH('hours')), O('Staff member of the longest shift', 'text', 'INDEX(%s,%s)' % (SH('staff'), MX)), O('Date of the longest shift', 'date', 'INDEX(%s,%s)' % (SH('date'), MX)),
    O('Shift ID', 'text', 'INDEX(%s,%s)' % (SH('shift_id'), MX)), O('Shifts in weeks with no day off, last 8 weeks', 'int', 'COUNTIFS(%s,">="&{in:days_max},%s,">="&({today}-56),%s,"<="&{today})' % (SH('days_week'), SH('date'), SH('date'))),
    O('Shifts in the period', 'int', 'COUNTIFS(%s,">="&({today}-30),%s,"<="&{today})' % (SH('date'), SH('date'))), O('Share of shifts above the limit', 'pct', 'IFERROR(%s/COUNTIFS(%s,">="&({today}-30),%s,"<="&{today}),0)' % (LD, SH('date'), SH('date'))),
    O('Verdict', 'text', 'IF(OR(%s>0,COUNTIFS(%s,">="&{in:days_max},%s,">="&({today}-56),%s,"<="&{today})>0),%s,%s)' % (LD, SH('days_week'), SH('date'), SH('date'), vb('Shorten the longest shift'), vb('Shifts are within limits')))],
    GR('What if', ('Limit 5 hours', {'limit': 5}), ('Limit 6 hours', {'limit': 6}), ('Limit 7 hours', {'limit': 7}), ('Most 5 days', {'days_max': 5}), ('Most 7 days', {'days_max': 7}))))

# 15 task completion score --------------------------------------------------------------------------------------------------------------------------------------------
TW = lambda extra='': 'COUNTIFS(%s,">="&({today}-{set:task_days})%s)' % (TK('date'), extra)
RL = ',%s,{in:role}' % TK('role')
tools.append(TOOL('task_score', 'Task Completion Score', 'Which role missed tasks this week',
    'Done against missed tasks of the last days set on the Start sheet: the whole team, one role you pick, the role that missed most and the verdict against your target.', [
    IL('role', 'Role', 'payrole', 'Delivery driver'), I('target', 'Share of tasks that must be done', 0.9, 'pct')], [
    O('Tasks planned', 'int', TW()), O('Tasks done', 'int', TW(',%s,%s' % (TK('done'), YES))), O('Tasks missed', 'int', TW(',%s,%s' % (TK('done'), NO))),
    O('Done share', 'pct', 'IFERROR(%s/%s,0)' % (TW(',%s,%s' % (TK('done'), YES)), TW())), O('Tasks of the role', 'int', TW(RL)), O('Tasks missed by the role', 'int', TW(RL + ',%s,%s' % (TK('done'), NO))),
    O('Done share of the role', 'pct', 'IFERROR(%s/%s,0)' % (TW(RL + ',%s,%s' % (TK('done'), YES)), TW(RL))),
    O('Role that missed most', 'text', 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (R('tasks_role', 'role'), R('tasks_role', 'tasks_missed'), R('tasks_role', 'tasks_missed'))), O('Tasks it missed', 'int', 'MAX(%s)' % R('tasks_role', 'tasks_missed')),
    O('Tasks missed, last 30 days', 'int', 'COUNTIFS(%s,">="&({today}-30),%s,%s)' % (TK('date'), TK('done'), NO)),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s,0)>={in:target},%s,%s)' % (TW(',%s,%s' % (TK('done'), YES)), TW(), vb('Tasks are on track'), vb('Review the missed tasks')))],
    GR('What if', ('Detailer', {'role': '=' + tok('payrole', 'Detailer')}), ('Manager', {'role': '=' + tok('payrole', 'Manager')}), ('Booking assistant', {'role': '=' + tok('payrole', 'Booking assistant')}), ('Target 80 percent', {'target': 0.8}), ('Target 95 percent', {'target': 0.95}))))

# 16 weekend cover planner ---------------------------------------------------------------------------------------------------------------------------------------------------
WE = lambda c: 'SUMIFS(%s,%s,">="&{in:start},%s,"<="&({in:start}+1))' % (SN(c), SN('date'), SN('date'))
WSH = lambda role: 'SUMIFS(%s,%s,">="&{in:start},%s,"<="&({in:start}+1),%s,%s)' % (SH('hours'), SH('date'), SH('date'), SH('role'), tok('payrole', role))
SHORT16 = 'MAX(0,SUMIFS(%s,%s,%s,%s,">="&{in:start},%s,"<="&({in:start}+1))-{in:extra})' % (SN('gap'), SN('status'), vb('Short'), SN('date'), SN('date'))
FS16 = 'SMALL(%s,COUNTIFS(%s,"<"&{in:start})+1)' % (SN('short_key'), SN('short_key'))
tools.append(TOOL('weekend_cover', 'Weekend Cover Planner', 'Is the weekend covered',
    'Pick a Saturday: weekend pickups, returns and runs turned into hours needed for cleaning, delivery and the counter, against detailer, driver and assistant hours rostered; add hours to test cover.', [
    I('start', 'Saturday', 'today+6', 'date'), I('extra', 'Extra hours you could add', 0.0, 'num')], [
    O('Pickups on the weekend', 'int', WE('pickups')), O('Returns on the weekend', 'int', WE('returns')), O('Runs on the weekend', 'int', WE('runs')), O('Hours needed', 'num', WE('hours_needed')),
    O('Hours rostered', 'num', WE('hours_rostered')), O('Assistant hours rostered', 'num', WSH('Booking assistant')), O('Driver hours rostered', 'num', WSH('Delivery driver')), O('Detailer hours rostered', 'num', WSH('Detailer')),
    O('Hours short on short days, after the extra hours', 'num', SHORT16), O('Days short on the weekend', 'int', 'COUNTIFS(%s,%s,%s,">="&{in:start},%s,"<="&({in:start}+1))' % (SN('status'), vb('Short'), SN('date'), SN('date'))), O('First short day', 'date', 'IFERROR(IF(%s<={in:start}+1,%s,""),"")' % (FS16, FS16)),
    O('Counter hours needed', 'num', WE('counter_need')), O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (SHORT16, vb('Add cover'), vb('Weekend is covered')))],
    GR('What if', ('Add 2 hours', {'extra': 2}), ('Add 4 hours', {'extra': 4}), ('Add 6 hours', {'extra': 6}), ('Add 8 hours', {'extra': 8}))))

# 17 peak-day staffing forecast ----------------------------------------------------------------------------------------------------------------------------------------------
W0 = '({today}+8-WEEKDAY({today},2))'
F17 = 'IF({in:scen}=%s,{in:base},IF({in:scen}=%s,{in:best},{in:worst}))' % (tok('scen', 'Base'), tok('scen', 'Best'))
def WN0(k, c): return 'SUMIFS(%s,%s,">="&(%s+%d),%s,"<"&(%s+%d))' % (SN(c), SN('date'), W0, 7 * (k - 1), SN('date'), W0, 7 * k)
def WN(k, c): return WN0(k, c) if c != 'hours_needed' else '(%s*(1+%s*%d))' % (WN0(k, c), F17, k)
def GP(k): return '(%s-%s)' % (WN(k, 'hours_needed'), WN(k, 'hours_rostered'))
tools.append(TOOL('peak_forecast', 'Peak-Day Staffing Forecast', 'Do I need part-time hours in the next 4 weeks',
    'The next four weeks of booked pickups, returns and runs turned into hours needed, with a Base, Best or Worst rise for bookings still to come, against the hours rostered.', [
    IL('scen', 'Scenario', 'scen', 'Base'), I('base', 'Base: bookings still to come, each week ahead', 0.25, 'pct'), I('best', 'Best: bookings still to come, each week ahead', 0.10, 'pct'), I('worst', 'Worst: bookings still to come, each week ahead', 0.45, 'pct')], [
    O('Rise for each week ahead', 'pct', F17), O('Week 1 hours needed', 'num', WN(1, 'hours_needed')), O('Week 1 hours rostered', 'num', WN(1, 'hours_rostered')), O('Week 1 gap', 'num', GP(1)),
    O('Week 2 hours needed', 'num', WN(2, 'hours_needed')), O('Week 2 hours rostered', 'num', WN(2, 'hours_rostered')), O('Week 2 gap', 'num', GP(2)),
    O('Week 3 hours needed', 'num', WN(3, 'hours_needed')), O('Week 3 hours rostered', 'num', WN(3, 'hours_rostered')), O('Week 3 gap', 'num', GP(3)),
    O('Week 4 hours needed', 'num', WN(4, 'hours_needed')), O('Week 4 hours rostered', 'num', WN(4, 'hours_rostered')), O('Week 4 gap', 'num', GP(4)),
    O('First week short, 0 for none', 'int', 'IF(%s>0,1,IF(%s>0,2,IF(%s>0,3,IF(%s>0,4,0))))' % (GP(1), GP(2), GP(3), GP(4))),
    O('Part-time hours to hire in the worst week', 'num', 'MAX(0,%s,%s,%s,%s)' % (GP(1), GP(2), GP(3), GP(4))),
    O('Verdict', 'text', 'IF(MAX(%s,%s,%s,%s)>0,%s,%s)' % (GP(1), GP(2), GP(3), GP(4), vb('Hire part-time hours'), vb('Enough staff')))],
    GR('What if', ('Best scenario', {'scen': '=' + tok('scen', 'Best')}), ('Worst scenario', {'scen': '=' + tok('scen', 'Worst')}), ('Worst, 60 percent a week', {'scen': '=' + tok('scen', 'Worst'), 'worst': 0.6}),
       ('Base, 10 percent a week', {'base': 0.10}), ('Base, 30 percent a week', {'base': 0.30}))))

# 18 cleaning supplies use -----------------------------------------------------------------------------------------------------------------------------------------------------
SP = lambda a, b: 'SUMIFS(%s,%s,">="&%s,%s,"<"&%s)' % (HM('supplies'), HM('month'), a, HM('month'), b)
RN_ = lambda a, b: 'SUMIFS(%s,%s,">="&%s,%s,"<"&%s)' % (HM('rentals'), HM('month'), a, HM('month'), b)
M18 = 'DATE(YEAR({in:month}),MONTH({in:month}),1)'; N18 = 'EDATE(%s,1)' % M18; P6 = 'EDATE(%s,-6)' % M18
NOW18 = 'IFERROR(%s/%s,0)' % (SP(M18, N18), RN_(M18, N18)); US18 = 'IFERROR(%s/%s,0)' % (SP(P6, M18), RN_(P6, M18))
tools.append(TOOL('supplies_check', 'Cleaning Supplies Use', 'Am I using more cleaning supplies than usual',
    'Pick a month: supplies spend per rental against your own last 6 months, the extra spend above your usual and the order that month.', [
    I('month', 'Month', 'today', 'date'), I('band', 'Band around your usual', 0.10, 'pct')], [
    O('Supplies spend this month', 'money', SP(M18, N18)), O('Rentals started', 'int', RN_(M18, N18)), O('Supplies per rental', 'money', NOW18), O('Your usual per rental, last 6 months', 'money', US18),
    O('Against your usual', 'pct', 'IFERROR(%s/%s-1,0)' % (NOW18, US18)), O('Above your usual by', 'money', 'MAX(0,(%s-%s)*%s)' % (NOW18, US18, RN_(M18, N18))),
    O('Average spend of the last 6 months', 'money', 'IFERROR(%s/6,0)' % SP(P6, M18)), O('Orders that month', 'int', 'COUNTIFS(%s,%s)' % (R('supplies', 'month'), M18)),
    O('Verdict', 'text', 'IF(%s>%s*(1+{in:band}),%s,%s)' % (NOW18, US18, vb('Above your usual spend'), vb('On track')))],
    GR('What if', ('Last month', {'month': '={today}-30'}), ('Two months ago', {'month': '={today}-60'}), ('Three months ago', {'month': '={today}-90'}), ('Band 5 percent', {'band': 0.05}), ('Band 25 percent', {'band': 0.25}))))
assert len(tools) == 18, len(tools)
