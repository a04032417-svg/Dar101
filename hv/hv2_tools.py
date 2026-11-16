"""HVAC and plumbing suite part 2: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv2_lists import *
import hv2_data as DD


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
PB = lambda c_: '{range:price_book.%s}' % c_
ES = lambda c_: '{range:estimates.%s}' % c_
OPEN_, WON, LOST = tok('estoutcome', 'Open'), tok('estoutcome', 'Won'), tok('estoutcome', 'Lost')
GOOD, BETTER, BEST = tok('tier', 'Good'), tok('tier', 'Better'), tok('tier', 'Best')
Y1 = '%s,">="&({today}-365),%s,"<="&{today}' % (ES('date'), ES('date'))
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
_pb = {p['pb_id']: p for p in price_book}


def up(x):  # round a price up the way the price book does
    return 'IF((%s)<1000,ROUNDUP((%s)/5,0)*5,ROUNDUP((%s)/25,0)*25)' % (x, x, x)


# 1 flat-rate line builder
POS1 = 'MATCH({in:pb_no},%s,0)' % PB('task_no')
def IX1(c_): return 'INDEX(%s,%s)' % (PB(c_), POS1)
H1 = 'IF({in:hours_now}>0,{in:hours_now},%s)' % IX1('labour_hours')
PC1 = 'IF({in:parts_now}>0,{in:parts_now},%s)' % IX1('parts_cost')
RT1 = 'IF(OR(%s=%s,%s=%s,%s=%s),{set:rate_install},{set:rate_service})' % (IX1('kind'), tok('jobkind', 'Replacement'), IX1('kind'), tok('jobkind', 'Install'), IX1('kind'), tok('jobkind', 'Repipe'))
TG1 = 'IF({in:target_now}>0,{in:target_now},%s)' % IX1('target_margin')
OTH1 = '(%s+%s+%s)' % (IX1('permit_fee'), IX1('disposal'), IX1('sub_cost'))
TRIP1 = '(%s+{set:drive_hours})*{set:vehicle_hour}' % H1
COST1 = '(%s*%s+%s+%s+%s)' % (H1, RT1, PC1, OTH1, TRIP1)
NEED1 = up('%s/(1-%s)' % (COST1, TG1))
MAR1 = '(%s-%s)/%s' % (IX1('flat_price'), COST1, IX1('flat_price'))

# 3 supplier price change impact
PP3 = 'MATCH({in:part_no},{range:parts.part_no},0)'
PID3 = 'INDEX({range:parts.part_id},%s)' % PP3
CUR3 = 'INDEX({range:parts.unit_cost},%s)' % PP3
LN3 = 'MATCH(%s,%s,0)' % (PID3, PB('main_part'))
QTY3 = 'INDEX(%s,%s)' % (PB('main_qty'), LN3)
EXT3 = '(%s*({in:new_cost}-%s))' % (QTY3, CUR3)
FLAT3 = 'INDEX(%s,%s)' % (PB('flat_price'), LN3); COST3 = 'INDEX(%s,%s)' % (PB('cost'), LN3); TG3 = 'INDEX(%s,%s)' % (PB('target_margin'), LN3)
MAF3 = '((%s-%s-%s)/%s)' % (FLAT3, COST3, EXT3, FLAT3)

# 4 good-better-best builder
def EP(s, p, c_): return '({in:%s}*({in:%s}-{in:%s}))' % (s, p, c_)
def MG(p, c_): return '(({in:%s}-{in:%s})/{in:%s})' % (p, c_, p)
def SC(m, e): return 'IF(%s>={in:target},%s,-1)' % (m, e)
SG4, SB4, SS4 = SC(MG('pg', 'cg'), EP('sg', 'pg', 'cg')), SC(MG('pb', 'cb'), EP('sb', 'pb', 'cb')), SC(MG('ps', 'cs'), EP('ss', 'ps', 'cs'))
LEAD4 = 'IF(MAX(%s,%s,%s)<0,%s,IF(AND(%s>=%s,%s>=%s),%s,IF(%s>=%s,%s,%s)))' % (SG4, SB4, SS4, c2('Raise price'), SG4, SB4, SG4, SS4, c2('Lead with good'), SB4, SS4, c2('Lead with better'), c2('Lead with best'))

# 5 option mix
def WN(t_): return 'COUNTIFS(%s,%s,%s,%s,%s)' % (ES('outcome'), WON, ES('option_chosen'), t_, Y1)
def AV(t_): return 'IFERROR(AVERAGEIFS(%s,%s,%s,%s,%s,%s),0)' % (ES('price_won'), ES('outcome'), WON, ES('option_chosen'), t_, Y1)
TOT5 = 'COUNTIFS(%s,%s,%s)' % (ES('outcome'), WON, Y1)
TK5 = '(%s*%s+%s*%s+%s*%s)/%s' % (WN(GOOD), AV(GOOD), WN(BETTER), AV(BETTER), WN(BEST), AV(BEST), TOT5)

# 6 ranker
N6 = 'MIN({in:calls},COUNTIFS(%s,%s))' % (ES('outcome'), OPEN_)
def R6(k, c_): return 'IFERROR(INDEX(%s,MATCH(%d,%s,0)),"")' % (ES(c_), k, ES('open_rank'))

# 8 expiry bands
def BAND(lo, hi, c_, kind):
    w = '%s,">=%d"' % (ES('age_days'), lo) + ('' if hi is None else ',%s,"<=%d"' % (ES('age_days'), hi))
    return ('COUNTIFS(%s)' % w) if kind == 'n' else ('SUMIFS(%s,%s)' % (ES('value_open'), w))
BANDS = [(0, 7), (8, 14), (15, 30), (31, None)]
VAL8 = ['SUMIFS(%s,%s,">=%d"%s)' % (ES('value_open'), ES('age_days'), lo, '' if hi is None else ',%s,"<=%d"' % (ES('age_days'), hi)) for lo, hi in BANDS]
EXP8 = ['%s*{in:r%d}' % (VAL8[i], i + 1) for i in range(4)]

# 10 yearly review
REV10, COST10 = 'SUM(%s)' % PB('revenue_year'), 'SUM(%s)' % PB('cost_year')
PARTS10 = 'SUMPRODUCT(%s,%s)' % (PB('jobs_12m'), PB('parts_cost'))
TRIP10 = 'SUMPRODUCT(%s*(%s+{set:drive_hours}))*{set:vehicle_hour}' % (PB('jobs_12m'), PB('labour_hours'))
OTH10 = 'SUMPRODUCT(%s*(%s+%s+%s))' % (PB('jobs_12m'), PB('permit_fee'), PB('disposal'), PB('sub_cost'))
LAB10 = '(%s-%s-%s-%s)' % (COST10, PARTS10, TRIP10, OTH10)
XJ10 = '(%s*{in:lr}+%s*{in:pr}+%s*{in:fr})' % (LAB10, PARTS10, TRIP10)
XI10 = '({in:ins}*{in:ir})'
NEEDJ10 = '%s/%s' % (XJ10, COST10); NEEDI10 = '%s/%s' % (XI10, REV10)

# 11 break-even
M11 = '((%s-%s)/%s)' % (REV10, COST10, REV10)
CR12 = 'IFERROR(COUNTIFS(%s,%s,%s)/COUNTIFS(%s,"<>"&%s,%s),0)' % (ES('outcome'), WON, Y1, ES('outcome'), OPEN_, Y1)

# 12 diagnostic fee
D12 = '{range:diag_months.%s}'
DMS = '{range:diag_months.month},">="&EDATE(%s,-12)' % MS
VIS12 = 'SUMIFS(%s,%s)' % (D12 % 'visits', DMS); CONV12 = 'SUMIFS(%s,%s)' % (D12 % 'converted', DMS)
COST12 = '({in:hours}*{in:rate}+({in:hours}+{in:drive})*{set:vehicle_hour})'
NEED12 = 'IF({in:fee}>=%s,0,(%s-{in:fee})/({in:profit}+%s-{in:fee}))' % (COST12, COST12, COST12)
ACT12 = 'IFERROR(%s/%s,0)' % (CONV12, VIS12)

# 15 financing
FAC15 = 'IFERROR(INDEX({range:fin_options.monthly_factor},MATCH({in:term},{range:fin_options.term_months},0)),{set:financing_factor})'
FEE15 = '({in:amount}*{in:fee_pct}+{in:fixed})'
MAR15 = '({in:amount}*{in:margin}-%s)/{in:amount}' % FEE15

# 16 turnaround
JTS = ['Furnace replacement', 'Air conditioner replacement', 'Heat pump install', 'Water heater replacement', 'Repipe']
def TA(jt, c_): return 'IFERROR(AVERAGEIFS(%s,%s,%s,%s),0)' % (ES(c_), ES('job_type'), tok('estjt', jt), Y1)
TAS = [TA(j, 'days_to_estimate') for j in JTS]
TMAX = 'MAX(%s)' % ','.join(TAS)

# 17 phone quote
JT17 = 'AVERAGEIFS(%s,%s,{in:job_type})' % (PB('flat_price'), PB('job_type'))
PR17 = 'IFERROR(AVERAGEIFS(%s,%s,{in:job_type},%s,{in:tier}),IFERROR(%s,0))' % (PB('flat_price'), PB('job_type'), PB('tier'), JT17)
KIND17 = 'IFERROR(INDEX({range:job_types.kind},MATCH({in:job_type},{range:job_types.job_type},0)),"")'
MP17 = 'IF(AND({in:member}=1,%s=%s),ROUND(%s*(1-{set:member_discount}),0),ROUND(%s,0))' % (KIND17, tok('jobkind', 'Repair'), PR17, PR17)

# 18 tier what-if
AT18 = '({in:sg}*{in:pg}+{in:sb}*{in:pb}+{in:ss}*{in:ps})'
AC18 = '({in:sg}*{in:cg}+{in:sb}*{in:cb}+{in:ss}*{in:cs})'

_won12 = [e for e in DD._EST if e['outcome'] == 'Won' and e['date'] >= ago(365)]
_sh = {t: sum(1 for e in _won12 if e['option_chosen'] == t) / float(len(_won12)) for t in TIERS}
_jobs_m = int(round(len(_won12) / 12.0))
_dt = DD.diag_by_tech()
_wh = _pb['PB-039']

tools = [
    TOOL('line_builder', 'Flat-Rate Line Builder', 'Price a task from cost at your margin target',
         'Type a task number such as 39 for PB-039; leave hours, parts and target at 0 to use the price book, or type today\'s numbers. See the price at your target and whether to raise it.', [
        I('pb_no', 'Task number, 39 is PB-039', 39, 'int'), I('hours_now', 'Labour hours, 0 uses the book', 0, 'num'), I('parts_now', 'Parts cost today, 0 uses the book', 0), I('target_now', 'Target margin, 0 uses the job type', 0, 'pct')], [
        O('Task', 'text', IX1('task')), O('Job type', 'text', IX1('job_type')), O('Labour hours used', 'num', H1), O('Loaded labour rate per hour', 'money', RT1),
        O('Labour cost', 'money', '%s*%s' % (H1, RT1)), O('Parts cost', 'money', PC1), O('Permit, disposal and subcontract', 'money', OTH1), O('Trip cost', 'money', TRIP1),
        O('Total cost', 'money', COST1), O('Target margin used', 'pct', TG1), O('Price at the target margin', 'money', NEED1), O('Flat price in the book', 'money', IX1('flat_price')),
        O('Gap to the flat price', 'money', '%s-%s' % (NEED1, IX1('flat_price'))), O('Margin at the flat price', 'pct', MAR1),
        O('Verdict', 'text', 'IF(%s<%s-{set:margin_tolerance},%s,IF(%s<%s+0.03,%s,%s))' % (MAR1, TG1, c2('Raise price'), MAR1, TG1, c2('Hold'), c2('Fine')))],
         GR('What if', ('Water heater, parts as booked', {'pb_no': 39}), ('Furnace, high efficiency', {'pb_no': 25}), ('Parts up to 800 on PB-039', {'pb_no': 39, 'parts_now': 800}),
            ('Target 50 percent on PB-039', {'pb_no': 39, 'target_now': 0.5}), ('Heating repair, PB-001', {'pb_no': 1}))),
    TOOL('margin_check', 'Price Book Margin Check', 'Which price book lines fell under their margin target',
         'See how many lines are on target, on watch or under target, the money lost a year, and the 8 lines with the lowest margin gap.', [
        I('amber', 'Margin points above target counted as amber', 0.02, 'pct')], [
        O('Lines under target', 'int', 'COUNTIFS(%s,%s)' % (PB('status'), ca('Under target'))), O('Lines on watch', 'int', 'COUNTIFS(%s,%s)' % (PB('status'), ca('Watch'))),
        O('Lines on target within the amber range', 'int', 'COUNTIFS(%s,">=0",%s,"<"&{in:amber})' % (PB('margin_gap'), PB('margin_gap'))), O('Margin lost a year on these lines', 'money', 'SUM(%s)' % PB('lost_year'))] + [
        o for k in range(1, 8) for o in (O('Lowest margin line %d' % k, 'text', 'INDEX(%s,MATCH(%d,%s,0))' % (PB('task'), k, PB('rank_gap'))), O('Margin gap of line %d' % k, 'pct', 'INDEX(%s,MATCH(%d,%s,0))' % (PB('margin_gap'), k, PB('rank_gap'))))][:14] + [
        O('Verdict', 'text', 'IF(COUNTIFS(%s,%s)>0,%s,%s)' % (PB('status'), ca('Under target'), c2('Raise price'), c2('Fine')))],
         GR('What if', ('Amber range 1 point', {'amber': 0.01}), ('Amber range 4 points', {'amber': 0.04}), ('Amber range 8 points', {'amber': 0.08}))),
    TOOL('price_impact', 'Supplier Price Change Impact', 'What a new supplier cost does to the lines that use the part',
         'Type a part number such as 65 for PT-0065 and its new cost; see the lines that use it, the margin after the change, the price needed and the money at risk a year.', [
        I('part_no', 'Part number, 65 is PT-0065', 65, 'int'), I('new_cost', 'New unit cost', 607)], [
        O('Part', 'text', 'INDEX({range:parts.part},%s)' % PP3), O('Current unit cost', 'money', CUR3), O('Rise against the current cost', 'pct', '{in:new_cost}/%s-1' % CUR3),
        O('Lines using it as the main part', 'int', 'COUNTIFS(%s,%s)' % (PB('main_part'), PID3)), O('First line hit', 'text', 'IFERROR(INDEX(%s,%s),"")' % (PB('task'), LN3)),
        O('Extra cost per job', 'money', 'IFERROR(%s,0)' % EXT3), O('Margin now', 'pct', 'IFERROR(INDEX(%s,%s),0)' % (PB('margin'), LN3)), O('Margin after the change', 'pct', 'IFERROR(%s,0)' % MAF3),
        O('Target margin', 'pct', 'IFERROR(%s,0)' % TG3), O('Price needed after the change', 'money', 'IFERROR(%s,0)' % up('(%s+%s)/(1-%s)' % (COST3, EXT3, TG3))),
        O('Jobs a year on the line', 'int', 'IFERROR(INDEX(%s,%s),0)' % (PB('jobs_12m'), LN3)), O('Money at risk a year', 'money', 'IFERROR(%s*INDEX(%s,%s),0)' % (EXT3, PB('jobs_12m'), LN3)),
        O('Open estimates of that job type', 'int', 'IFERROR(COUNTIFS(%s,INDEX(%s,%s),%s,%s),0)' % (ES('job_type'), PB('job_type'), LN3, ES('outcome'), OPEN_)),
        O('Verdict', 'text', 'IFERROR(IF(%s<%s-{set:margin_tolerance},%s,IF(%s<%s,%s,%s)),%s)' % (MAF3, TG3, c2('Raise price'), MAF3, TG3, c2('Hold'), c2('Fine'), c2('Fine')))],
         GR('What if', ('Water heater 50 gal at 562', {'new_cost': 562}), ('Water heater 50 gal at 650', {'new_cost': 650}), ('Tankless unit at 1090', {'part_no': 66, 'new_cost': 1090}), ('Tankless unit at 1200', {'part_no': 66, 'new_cost': 1200}))),
    TOOL('gbb_builder', 'Good-Better-Best Builder', 'Which option to lead with for one job',
         'Type cost and price of the three options and the share of customers who chose each in the last 12 months; see margin, monthly payment and the option to lead with.', [
        I('cg', 'Cost, good', _pb['PB-024']['cost']), I('cb', 'Cost, better', _pb['PB-025']['cost']), I('cs', 'Cost, best', _pb['PB-026']['cost']),
        I('pg', 'Price, good', _pb['PB-024']['flat_price']), I('pb', 'Price, better', _pb['PB-025']['flat_price']), I('ps', 'Price, best', _pb['PB-026']['flat_price']),
        I('sg', 'Share choosing good', round(_sh['Good'], 2), 'pct'), I('sb', 'Share choosing better', round(_sh['Better'], 2), 'pct'), I('ss', 'Share choosing best', round(1 - round(_sh['Good'], 2) - round(_sh['Better'], 2), 2), 'pct'),
        I('target', 'Target margin', 0.38, 'pct')], [
        O('Margin, good', 'pct', MG('pg', 'cg')), O('Margin, better', 'pct', MG('pb', 'cb')), O('Margin, best', 'pct', MG('ps', 'cs')),
        O('Monthly payment, good', 'money', 'ROUND({in:pg}*{set:financing_factor},0)'), O('Monthly payment, better', 'money', 'ROUND({in:pb}*{set:financing_factor},0)'), O('Monthly payment, best', 'money', 'ROUND({in:ps}*{set:financing_factor},0)'),
        O('Expected profit per estimate, good', 'money', EP('sg', 'pg', 'cg')), O('Expected profit per estimate, better', 'money', EP('sb', 'pb', 'cb')), O('Expected profit per estimate, best', 'money', EP('ss', 'ps', 'cs')),
        O('Average ticket at these shares', 'money', '{in:sg}*{in:pg}+{in:sb}*{in:pb}+{in:ss}*{in:ps}'), O('Options at or above target', 'int', '(%s>={in:target})+(%s>={in:target})+(%s>={in:target})' % (MG('pg', 'cg'), MG('pb', 'cb'), MG('ps', 'cs'))),
        O('Verdict: option to lead with', 'text', LEAD4)],
         GR('What if', ('Better price up 150', {'pb': _pb['PB-025']['flat_price'] + 150}), ('Good price up 100', {'pg': _pb['PB-024']['flat_price'] + 100}), ('More customers choose best', {'sg': 0.2, 'sb': 0.45, 'ss': 0.35}), ('Parts cost up 10 percent on better', {'cb': round(_pb['PB-025']['cost'] * 1.1, 2)}))),
    TOOL('option_mix', 'Option Mix Analyser', 'Are customers choosing good, better or best',
         'Read the last 12 months of won estimates: share and average ticket by option, and the ticket gained when you move sales up a tier.', [
        I('shift_gb', 'Share moved from good to better', 0.10, 'pct'), I('shift_bb', 'Share moved from better to best', 0.05, 'pct')], [
        O('Estimates won, 12 months', 'int', TOT5), O('Share won at good', 'pct', '%s/%s' % (WN(GOOD), TOT5)), O('Share won at better', 'pct', '%s/%s' % (WN(BETTER), TOT5)), O('Share won at best', 'pct', '%s/%s' % (WN(BEST), TOT5)),
        O('Average ticket at good', 'money', AV(GOOD)), O('Average ticket at better', 'money', AV(BETTER)), O('Average ticket at best', 'money', AV(BEST)), O('Average ticket won', 'money', TK5),
        O('Ticket gained per won estimate after the shift', 'money', '{in:shift_gb}*(%s-%s)+{in:shift_bb}*(%s-%s)' % (AV(BETTER), AV(GOOD), AV(BEST), AV(BETTER))),
        O('Extra revenue a year after the shift', 'money', '(%s)*%s' % ('{in:shift_gb}*(%s-%s)+{in:shift_bb}*(%s-%s)' % (AV(BETTER), AV(GOOD), AV(BEST), AV(BETTER)), TOT5)),
        O('Verdict', 'text', 'IF(%s/%s>=0.3,%s,IF(%s/%s<0.25,%s,%s))' % (WN(GOOD), TOT5, c2('Lead with better'), WN(BEST), TOT5, c2('Lead with best'), c2('Mix is healthy')))],
         GR('What if', ('Move 5 points to better', {'shift_gb': 0.05, 'shift_bb': 0}), ('Move 15 points to better', {'shift_gb': 0.15, 'shift_bb': 0.05}), ('Move 10 points to best', {'shift_gb': 0, 'shift_bb': 0.10}))),
    TOOL('followup_ranker', 'Estimate Follow-up Ranker', 'Which open estimates to call today',
         'Type how many calls the office can make today and the close rate you expect on a follow-up; see the money on the table and the first estimates to call.', [
        I('calls', 'Calls the office can make today', 8, 'int'), I('exp_close', 'Close rate expected on a follow-up call', 0.35, 'pct')], [
        O('Open estimates', 'int', 'COUNTIFS(%s,%s)' % (ES('outcome'), OPEN_)), O('Money on the table', 'money', 'SUM(%s)' % ES('value_open')), O('Estimates to call today', 'int', N6),
        O('Value covered by those calls', 'money', 'SUMIFS(%s,%s,"<="&%s)' % (ES('value_open'), ES('open_rank'), N6)), O('Expected value won from the calls', 'money', 'SUMIFS(%s,%s,"<="&%s)*{in:exp_close}' % (ES('value_open'), ES('open_rank'), N6)),
        O('Open estimates with no follow-up date', 'int', 'COUNTIFS(%s,%s)' % (ES('followup_flag'), ca('No follow-up date')))] + [
        o for k in range(1, 5) for o in (O('Call first, no. %d' % k, 'text', R6(k, 'estimate_id')), O('Technician, no. %d' % k, 'text', R6(k, 'technician')), O('Value, no. %d' % k, 'money', 'IFERROR(INDEX(%s,MATCH(%d,%s,0)),0)' % (ES('est_value'), k, ES('open_rank'))))] + [
        O('Verdict', 'text', 'IF(COUNTIFS(%s,%s)>0,%s,%s)' % (ES('outcome'), OPEN_, c2('Call today'), c2('Nothing waiting')))],
         GR('What if', ('Four calls only', {'calls': 4}), ('Fifteen calls', {'calls': 15}), ('Close rate 50 percent', {'exp_close': 0.5}), ('Close rate 20 percent', {'exp_close': 0.2}))),
    TOOL('close_analyser', 'Close Rate Analyser', 'Where the close rate is weakest',
         'Compare the close rate of the last 90 days, the last 12 months and the year before with your target, and find the weakest technician, job type and option.', [
        I('amber', 'Points below target that still count as a watch', 0.05, 'pct')], [
        O('Close rate, last 90 days', 'pct', 'IFERROR(COUNTIFS(%s,%s,%s,">="&({today}-90))/COUNTIFS(%s,"<>"&%s,%s,">="&({today}-90)),0)' % (ES('outcome'), WON, ES('date'), ES('outcome'), OPEN_, ES('date'))),
        O('Close rate, last 12 months', 'pct', CR12),
        O('Close rate, year before', 'pct', 'IFERROR(COUNTIFS(%s,%s,%s,">="&({today}-730),%s,"<"&({today}-365))/COUNTIFS(%s,"<>"&%s,%s,">="&({today}-730),%s,"<"&({today}-365)),0)' % (ES('outcome'), WON, ES('date'), ES('date'), ES('outcome'), OPEN_, ES('date'), ES('date'))),
        O('Close target', 'pct', '{set:close_target}'),
        O('Weakest technician, 12 months', 'text', 'INDEX({range:close_tech.technician},MATCH(MIN({range:close_tech.rate_12m}),{range:close_tech.rate_12m},0))'), O('Their close rate', 'pct', 'MIN({range:close_tech.rate_12m})'),
        O('Weakest job type, 12 months', 'text', 'INDEX({range:close_jt.job_type},MATCH(MIN({range:close_jt.rate_12m}),{range:close_jt.rate_12m},0))'), O('Its close rate', 'pct', 'MIN({range:close_jt.rate_12m})'),
        O('Option that wins most', 'text', 'INDEX({range:close_option.option},MATCH(MAX({range:close_option.rate_12m}),{range:close_option.rate_12m},0))'), O('Its close rate at the option', 'pct', 'MAX({range:close_option.rate_12m})'),
        O('Verdict', 'text', 'IF(%s>={set:close_target},%s,IF(%s>={set:close_target}-{in:amber},%s,%s))' % (CR12, c2('Close rate on target'), CR12, c2('Hold'), c2('Close rate below target')))],
         GR('What if', ('Watch range 2 points', {'amber': 0.02}), ('Watch range 10 points', {'amber': 0.10}))),
    TOOL('expiry_planner', 'Estimate Expiry Planner', 'How much of the open money is still winnable',
         'Type the close rate you see by age of estimate; see value by age band, the expected wins and the value to drop from the list.', [
        I('r1', 'Close rate, age 0 to 7 days', 0.45, 'pct'), I('r2', 'Close rate, age 8 to 14 days', 0.30, 'pct'), I('r3', 'Close rate, age 15 to 30 days', 0.15, 'pct'), I('r4', 'Close rate, over 30 days', 0.05, 'pct'), I('drop_below', 'Drop an age band below this rate', 0.10, 'pct')], [
        O('Open estimates, 0 to 7 days', 'int', BAND(0, 7, 0, 'n')), O('Open estimates, 8 to 14 days', 'int', BAND(8, 14, 0, 'n')), O('Open estimates, 15 to 30 days', 'int', BAND(15, 30, 0, 'n')), O('Open estimates, over 30 days', 'int', BAND(31, None, 0, 'n')),
        O('Value, 0 to 7 days', 'money', VAL8[0]), O('Value, 8 to 14 days', 'money', VAL8[1]), O('Value, 15 to 30 days', 'money', VAL8[2]), O('Value, over 30 days', 'money', VAL8[3]),
        O('Expected wins, 0 to 7 days', 'money', EXP8[0]), O('Expected wins, 8 to 14 days', 'money', EXP8[1]), O('Expected wins, 15 to 30 days', 'money', EXP8[2]), O('Expected wins, over 30 days', 'money', EXP8[3]),
        O('Value still winnable', 'money', '+'.join(EXP8)),
        O('Value to drop from the list', 'money', '+'.join('IF({in:r%d}<{in:drop_below},%s,0)' % (i + 1, VAL8[i]) for i in range(4))),
        O('Verdict', 'text', 'IF(%s>0,%s,%s)' % ('+'.join(VAL8), c2('Call today'), c2('Nothing waiting')))],
         GR('What if', ('Close rates all 10 points higher', {'r1': 0.55, 'r2': 0.40, 'r3': 0.25, 'r4': 0.15}), ('Close rates all 10 points lower', {'r1': 0.35, 'r2': 0.20, 'r3': 0.05, 'r4': 0.0}), ('Drop below 20 percent', {'drop_below': 0.20}))),
    TOOL('lost_cause', 'Lost-Estimate Cause Analyser', 'Which cause of lost estimates to fix first',
         'Read the lost value of the last 12 months by cause; type the share you could win back and your margin to see the profit and the cause to fix first.', [
        I('recover', 'Share of the top cause you could win back', 0.15, 'pct'), I('margin', 'Margin on won work', 0.42, 'pct')], [
        O('Lost estimates, 12 months', 'int', 'SUM({range:lost_reasons.estimates})'), O('Lost value, 12 months', 'money', 'SUM({range:lost_reasons.lost_value})'),
        O('Top cause', 'text', 'INDEX({range:lost_reasons.reason},MATCH(MAX({range:lost_reasons.lost_value}),{range:lost_reasons.lost_value},0))'), O('Lost value of the top cause', 'money', 'MAX({range:lost_reasons.lost_value})'),
        O('Share of all lost value', 'pct', 'MAX({range:lost_reasons.lost_value})/SUM({range:lost_reasons.lost_value})'), O('Value won back', 'money', 'MAX({range:lost_reasons.lost_value})*{in:recover}'),
        O('Extra gross profit', 'money', 'MAX({range:lost_reasons.lost_value})*{in:recover}*{in:margin}'),
        O('Lost to price', 'money', 'SUMIFS({range:lost_reasons.lost_value},{range:lost_reasons.reason},%s)' % tok('estlost', 'Price')),
        O('Lost to financing declined', 'money', 'SUMIFS({range:lost_reasons.lost_value},{range:lost_reasons.reason},%s)' % tok('estlost', 'Financing declined')),
        O('Verdict: cause to fix first', 'text', 'IF(INDEX({range:lost_reasons.reason},MATCH(MAX({range:lost_reasons.lost_value}),{range:lost_reasons.lost_value},0))=%s,%s,IF(INDEX({range:lost_reasons.reason},MATCH(MAX({range:lost_reasons.lost_value}),{range:lost_reasons.lost_value},0))=%s,%s,IF(INDEX({range:lost_reasons.reason},MATCH(MAX({range:lost_reasons.lost_value}),{range:lost_reasons.lost_value},0))=%s,%s,IF(INDEX({range:lost_reasons.reason},MATCH(MAX({range:lost_reasons.lost_value}),{range:lost_reasons.lost_value},0))=%s,%s,%s))))' % (
            tok('estlost', 'Price'), c2('Fix price first'), tok('estlost', 'Went elsewhere'), c2('Fix second opinion first'), tok('estlost', 'No decision'), c2('Fix no answer first'), tok('estlost', 'Financing declined'), c2('Fix financing first'), c2('Fix timing first')))],
         GR('What if', ('Win back 25 percent', {'recover': 0.25}), ('Win back 5 percent', {'recover': 0.05}), ('Margin 35 percent', {'margin': 0.35}))),
    TOOL('yearly_review', 'Yearly Price Review', 'The price rise you need next January',
         'Type your expected cost rises and the rise you plan; see the extra cost a year, the rise needed to keep your margin and the lines to lift first.', [
        I('lr', 'Labour cost rise', 0.04, 'pct'), I('pr', 'Parts cost rise', 0.06, 'pct'), I('fr', 'Fuel and vehicle cost rise', 0.08, 'pct'), I('ir', 'Insurance rise', 0.08, 'pct'), I('ins', 'Insurance cost a year', 49200), I('plan', 'Price rise you plan', 0.04, 'pct')], [
        O('Revenue on the price book, 12 months', 'money', REV10), O('Job cost, 12 months', 'money', COST10), O('Extra job cost a year', 'money', XJ10), O('Extra insurance cost a year', 'money', XI10),
        O('Rise to keep the job margin', 'pct', NEEDJ10), O('Extra rise to cover insurance', 'pct', NEEDI10), O('Total rise needed', 'pct', '%s+%s' % (NEEDJ10, NEEDI10)), O('Shortfall against your planned rise', 'pct', '%s+%s-{in:plan}' % (NEEDJ10, NEEDI10)),
        O('Verdict', 'text', 'IF({in:plan}>=%s+%s,%s,%s)' % (NEEDJ10, NEEDI10, c2('Planned rise covers costs'), c2('Planned rise is not enough')))] + [
        o for k in range(1, 6) for o in (O('Lift first, line %d' % k, 'text', 'INDEX(%s,MATCH(%d,%s,0))' % (PB('task'), k, PB('rank_year'))), O('Margin lost a year, line %d' % k, 'money', 'INDEX(%s,MATCH(%d,%s,0))' % (PB('lost_year'), k, PB('rank_year'))))],
         GR('What if', ('All rises 2 points higher', {'lr': 0.06, 'pr': 0.08, 'fr': 0.10, 'ir': 0.10}), ('Planned rise 6 percent', {'plan': 0.06}), ('Planned rise 2 percent', {'plan': 0.02}), ('Insurance up 20 percent', {'ir': 0.20}))),
    TOOL('rise_breakeven', 'Price Rise Break-Even Solver', 'How many jobs you can lose after a price rise',
         'Type the price rise and the jobs you expect to lose; see the job loss that leaves profit unchanged and the close rate you can fall to.', [
        I('rise', 'Price rise', 0.05, 'pct'), I('jobs_lost', 'Jobs you expect to lose', 0.04, 'pct')], [
        O('Gross margin of the price book mix', 'pct', M11), O('Job loss that leaves profit unchanged', 'pct', '{in:rise}/(%s+{in:rise})' % M11),
        O('Jobs a year in the book', 'int', 'SUM(%s)' % PB('jobs_12m')), O('Jobs you can lose', 'int', 'ROUND({in:rise}/(%s+{in:rise})*SUM(%s),0)' % (M11, PB('jobs_12m'))),
        O('Gross profit now', 'money', '%s-%s' % (REV10, COST10)), O('Gross profit after the rise and the lost jobs', 'money', '(1-{in:jobs_lost})*(%s*(1+{in:rise})-%s)' % (REV10, COST10)),
        O('Change in gross profit', 'money', '(1-{in:jobs_lost})*(%s*(1+{in:rise})-%s)-(%s-%s)' % (REV10, COST10, REV10, COST10)), O('Close rate now, 12 months', 'pct', CR12),
        O('Close rate you can fall to', 'pct', '%s*(1-{in:rise}/(%s+{in:rise}))' % (CR12, M11)),
        O('Verdict', 'text', 'IF({in:jobs_lost}<={in:rise}/(%s+{in:rise}),%s,%s)' % (M11, c2('Rise pays off'), c2('Rise loses profit')))],
         GR('Sensitivity: price rise', ('Rise 2 percent', {'rise': 0.02}), ('Rise 4 percent', {'rise': 0.04}), ('Rise 6 percent', {'rise': 0.06}), ('Rise 8 percent', {'rise': 0.08}), ('Rise 10 percent', {'rise': 0.10}))),
    TOOL('diag_fee_test', 'Call-Out and Diagnostic Fee', 'Is your diagnostic fee high enough',
         'Type the fee, the visit time and the profit of a repair that follows; see the cost of a visit, the conversion you need and the verdict on the fee.', [
        I('fee', 'Diagnostic fee', DIAG_FEE), I('hours', 'Hours on site', 1.0, 'num'), I('drive', 'Drive hours', 0.45, 'num'), I('rate', 'Loaded labour cost per hour', 40), I('profit', 'Gross profit of the repair that follows', 190)], [
        O('Cost of one visit', 'money', COST12), O('Loss on a visit with no fee', 'money', COST12), O('Fee less cost on a visit that is not converted', 'money', '{in:fee}-%s' % COST12), O('Break-even fee', 'money', COST12),
        O('Fee as a multiple of cost', 'num', '{in:fee}/%s' % COST12), O('Share that must convert at this fee', 'pct', NEED12), O('Conversion, last 12 months', 'pct', ACT12),
        O('Profit per visit at that conversion', 'money', '%s*({in:profit}-%s)+(1-%s)*({in:fee}-%s)' % (ACT12, COST12, ACT12, COST12)),
        O('Verdict', 'text', 'IF(OR({in:fee}<%s,%s<%s),%s,IF({in:fee}>2*%s,%s,%s))' % (COST12, ACT12, NEED12, c2('Raise the fee'), COST12, c2('Lower the fee'), c2('Hold the fee')))],
         GR('What if', ('Fee 59', {'fee': 59}), ('Fee 129', {'fee': 129}), ('Two hours on site', {'hours': 2.0}), ('Repair profit 90', {'profit': 90}))),
    TOOL('diag_by_tech', 'Diagnostic Conversion by Tech', 'Who turns diagnostic visits into repairs',
         'Type each technician\'s diagnostic visits and the visits that became a repair or replacement estimate; see the ranking against the shop\'s last 12 months.', [
        I('v1', 'Visits, Tomasz Nowak', _dt['Tomasz Nowak'][0], 'int'), I('c1', 'Converted, Tomasz Nowak', _dt['Tomasz Nowak'][1], 'int'), I('v2', 'Visits, Kofi Mensah', _dt['Kofi Mensah'][0], 'int'), I('c2', 'Converted, Kofi Mensah', _dt['Kofi Mensah'][1], 'int'),
        I('v3', 'Visits, Elena Rossi', _dt['Elena Rossi'][0], 'int'), I('c3', 'Converted, Elena Rossi', _dt['Elena Rossi'][1], 'int'), I('target', 'Conversion you want', 0.60, 'pct')], [
        O('Conversion, Tomasz Nowak', 'pct', '{in:c1}/{in:v1}'), O('Conversion, Kofi Mensah', 'pct', '{in:c2}/{in:v2}'), O('Conversion, Elena Rossi', 'pct', '{in:c3}/{in:v3}'),
        O('Conversion of the three together', 'pct', '({in:c1}+{in:c2}+{in:c3})/({in:v1}+{in:v2}+{in:v3})'), O('Shop conversion, last 12 months', 'pct', ACT12),
        O('Visits missing to reach the target, all three', 'int', 'MAX(0,ROUND({in:target}*({in:v1}+{in:v2}+{in:v3})-({in:c1}+{in:c2}+{in:c3}),0))'),
        O('Best converter', 'text', 'IF(AND({in:c1}/{in:v1}>={in:c2}/{in:v2},{in:c1}/{in:v1}>={in:c3}/{in:v3}),{list:tech.tomasz_nowak},IF({in:c2}/{in:v2}>={in:c3}/{in:v3},{list:tech.kofi_mensah},{list:tech.elena_rossi}))'),
        O('Weakest converter', 'text', 'IF(AND({in:c1}/{in:v1}<={in:c2}/{in:v2},{in:c1}/{in:v1}<={in:c3}/{in:v3}),{list:tech.tomasz_nowak},IF({in:c2}/{in:v2}<={in:c3}/{in:v3},{list:tech.kofi_mensah},{list:tech.elena_rossi}))'),
        O('Verdict', 'text', 'IF(({in:c1}+{in:c2}+{in:c3})/({in:v1}+{in:v2}+{in:v3})>={in:target},%s,%s)' % (c2('Fine'), c2('Raise the fee')))],
         GR('What if', ('Target 55 percent', {'target': 0.55}), ('Target 70 percent', {'target': 0.70}))),
    TOOL('member_check', 'Member Price and Discount Check', 'Does the member discount push repair lines under your floor',
         'Type the member discount, your margin floor and the share of repairs sold to members; see the repair lines under the floor and the money given away.', [
        I('disc', 'Member discount', 0.10, 'pct'), I('floor', 'Margin floor', 0.30, 'pct'), I('share', 'Share of repair work sold to members', 0.30, 'pct')], [
        O('Repair lines in the book', 'int', 'COUNTIFS(%s,%s)' % (PB('kind'), tok('jobkind', 'Repair'))),
        O('Repair lines under the floor at the member price', 'int', 'COUNTIFS(%s,%s,%s,"<"&(1-(1-{in:disc})*(1-{in:floor})))' % (PB('kind'), tok('jobkind', 'Repair'), PB('margin'))),
        O('Lowest repair margin at the full price', 'pct', 'MIN(%s)' % PB('repair_margin')), O('Lowest repair margin at the member price', 'pct', '1-(1-MIN(%s))/(1-{in:disc})' % PB('repair_margin')),
        O('Line with the lowest margin', 'text', 'INDEX(%s,MATCH(MIN(%s),%s,0))' % (PB('task'), PB('repair_margin'), PB('repair_margin'))),
        O('Largest discount that keeps every repair at the floor', 'pct', 'MAX(0,1-(1-MIN(%s))/(1-{in:floor}))' % PB('repair_margin')),
        O('Repair revenue a year in the book', 'money', 'SUMIFS(%s,%s,%s)' % (PB('revenue_year'), PB('kind'), tok('jobkind', 'Repair'))),
        O('Discount given away a year', 'money', 'SUMIFS(%s,%s,%s)*{in:disc}*{in:share}' % (PB('revenue_year'), PB('kind'), tok('jobkind', 'Repair'))),
        O('Verdict', 'text', 'IF(COUNTIFS(%s,%s,%s,"<"&(1-(1-{in:disc})*(1-{in:floor})))>0,%s,%s)' % (PB('kind'), tok('jobkind', 'Repair'), PB('margin'), c2('Limit the discount'), c2('Member prices are safe')))],
         GR('What if', ('Discount 15 percent', {'disc': 0.15}), ('Discount 5 percent', {'disc': 0.05}), ('Floor 40 percent', {'floor': 0.40}), ('Half the repairs to members', {'share': 0.5}))),
    TOOL('financing_check', 'Financing Cost Check', 'Which jobs to offer financing on',
         'Type the job amount, the term, the fee you absorb and your margin; see the monthly payment, the margin after the fee and the smallest job worth financing.', [
        I('amount', 'Job amount financed', 6500), I('term', 'Term in months', 60, 'int'), I('fee_pct', 'Lender fee you absorb, share of the amount', 0.03, 'pct'), I('fixed', 'Fixed fee per financed job', 40), I('margin', 'Job margin before the fee', 0.42, 'pct')], [
        O('Monthly factor for the term', 'pct', FAC15), O('Monthly payment', 'money', '{in:amount}*%s' % FAC15), O('Total paid by the customer', 'money', '{in:amount}*%s*{in:term}' % FAC15),
        O('Fee you absorb', 'money', FEE15), O('Margin before the fee', 'money', '{in:amount}*{in:margin}'), O('Margin after the fee', 'money', '{in:amount}*{in:margin}-%s' % FEE15), O('Margin percent after the fee', 'pct', MAR15),
        O('Smallest job worth financing', 'money', 'IF({in:margin}-{in:fee_pct}-{set:margin_floor}>0,{in:fixed}/({in:margin}-{in:fee_pct}-{set:margin_floor}),0)'),
        O('Estimates lost to declined financing, 12 months', 'int', 'COUNTIFS(%s,%s,%s,%s)' % (ES('lost_reason'), tok('estlost', 'Financing declined'), ES('outcome'), LOST) if False else 'COUNTIFS(%s,%s,%s,%s,%s)' % (ES('lost_reason'), tok('estlost', 'Financing declined'), ES('outcome'), LOST, Y1)),
        O('Value lost to declined financing, 12 months', 'money', 'SUMIFS(%s,%s,%s,%s)' % (ES('lost_value'), ES('lost_reason'), tok('estlost', 'Financing declined'), Y1)),
        O('Verdict', 'text', 'IF(%s>={set:margin_floor},%s,%s)' % (MAR15, c2('Offer financing'), c2('Limit to larger jobs')))],
         GR('What if', ('Job 2,500', {'amount': 2500}), ('Job 12,000, 36 months', {'amount': 12000, 'term': 36}), ('Lender fee 6 percent', {'fee_pct': 0.06}), ('Margin 36 percent', {'margin': 0.36}))),
    TOOL('turnaround', 'Estimate Turnaround Tool', 'Which job types get their estimate out too slowly',
         'Read days from the call to the estimate and from the estimate to the job by job type over 12 months; type your target days to find the slow types.', [
        I('target_days', 'Target days from call to estimate', 2.0, 'num')], [
        O('Days to estimate, %s' % j, 'num', TAS[i]) for i, j in enumerate(JTS)] + [
        O('Days to job, %s' % j, 'num', TA(j, 'days_to_job')) for j in JTS] + [
        O('Shop average, call to estimate', 'num', 'IFERROR(AVERAGEIFS(%s,%s),0)' % (ES('days_to_estimate'), Y1)),
        O('Slowest job type', 'text', 'IF(%s=%s,%s,IF(%s=%s,%s,IF(%s=%s,%s,IF(%s=%s,%s,%s))))' % (TAS[0], TMAX, tok('estjt', JTS[0]), TAS[1], TMAX, tok('estjt', JTS[1]), TAS[2], TMAX, tok('estjt', JTS[2]), TAS[3], TMAX, tok('estjt', JTS[3]), tok('estjt', JTS[4]))),
        O('Verdict', 'text', 'IF(%s>{in:target_days},%s,%s)' % (TMAX, c2('Turnaround too slow'), c2('Turnaround on target')))][:19],
         GR('What if', ('Target 1.5 days', {'target_days': 1.5}), ('Target 3 days', {'target_days': 3.0}))),
    TOOL('phone_quote', 'Quote-by-Phone Helper', 'What to say when a customer asks the price',
         'Pick the job type and the option; see the price from the price book, the range, the deposit, the member price and the words to say. Check the current price before you quote.', [
        IN('job_type', 'Job type', 'list', key('jobtype', 'Water heater replacement'), list='jobtype'), IN('tier', 'Option', 'list', key('tier', 'Better'), list='tier'), I('member', 'Customer is a member, 1 for yes', 0, 'int')], [
        O('Price for this option', 'money', 'ROUND(%s,0)' % PR17), O('Lowest price for the job type', 'money', 'SUMPRODUCT(MIN(%s+(%s<>{in:job_type})*1000000))' % (PB('flat_price'), PB('job_type'))),
        O('Highest price for the job type', 'money', 'SUMPRODUCT(MAX(%s*(%s={in:job_type})))' % (PB('flat_price'), PB('job_type'))), O('Price to quote', 'money', MP17),
        O('Deposit to hold the date', 'money', 'ROUND(%s*{set:deposit_pct},0)' % MP17), O('Monthly payment', 'money', 'ROUND(%s*{set:financing_factor},0)' % MP17), O('Diagnostic fee', 'money', '{set:diag_fee}'),
        O('Say: price', 'text', '%s&" "&%s' % (tok('say', 'Our fixed price for this job is'), MP17)), O('Say: what it includes', 'text', tok('say', 'Prices include parts and labour')),
        O('Say: deposit', 'text', '%s&" "&ROUND(%s*{set:deposit_pct},0)' % (tok('say', 'A deposit holds your date'), MP17)), O('Say: check', 'text', tok('say', 'Please check the current price'))],
         GR('What if', ('Furnace replacement, best', {'job_type': '=' + tok('jobtype', 'Furnace replacement'), 'tier': '=' + BEST}), ('Heating repair, member', {'job_type': '=' + tok('jobtype', 'Heating repair'), 'member': 1}), ('Drain clearing', {'job_type': '=' + tok('jobtype', 'Drain clearing')}))),
    TOOL('tier_whatif', 'Margin-by-Tier What-If', 'What moving sales between good, better and best does',
         'Type price, cost and share by option and the jobs a month; see the average ticket and gross profit, with a best and a worst mix below.', [
        I('pg', 'Price, good', _pb['PB-024']['flat_price']), I('pb', 'Price, better', _pb['PB-025']['flat_price']), I('ps', 'Price, best', _pb['PB-026']['flat_price']),
        I('cg', 'Cost, good', _pb['PB-024']['cost']), I('cb', 'Cost, better', _pb['PB-025']['cost']), I('cs', 'Cost, best', _pb['PB-026']['cost']),
        I('sg', 'Share sold, good', round(_sh['Good'], 2), 'pct'), I('sb', 'Share sold, better', round(_sh['Better'], 2), 'pct'), I('ss', 'Share sold, best', round(1 - round(_sh['Good'], 2) - round(_sh['Better'], 2), 2), 'pct'),
        I('jobs', 'Jobs a month', _jobs_m, 'int'), I('target', 'Target margin', 0.40, 'pct')], [
        O('Average ticket', 'money', AT18), O('Average cost', 'money', AC18), O('Average gross profit per job', 'money', '%s-%s' % (AT18, AC18)), O('Average margin', 'pct', '(%s-%s)/%s' % (AT18, AC18, AT18)),
        O('Gross profit a month', 'money', '({in:jobs})*(%s-%s)' % (AT18, AC18)), O('Gross profit a year', 'money', '12*{in:jobs}*(%s-%s)' % (AT18, AC18)),
        O('Margin gap to target', 'pct', '(%s-%s)/%s-{in:target}' % (AT18, AC18, AT18)),
        O('Verdict', 'text', 'IF((%s-%s)/%s>={in:target},%s,%s)' % (AT18, AC18, AT18, c2('Mix is healthy'), c2('Raise price')))],
         GR('Base, best and worst mix', ('Base: shares as typed', {'sg': '={in:sg}'}), ('Best: 10 points up a tier', {'sg': '={in:sg}-0.1', 'sb': '={in:sb}+0.05', 'ss': '={in:ss}+0.05'}), ('Worst: 10 points down a tier', {'sg': '={in:sg}+0.1', 'sb': '={in:sb}-0.05', 'ss': '={in:ss}-0.05'}))),
]
assert len(tools) == 18, len(tools)
for _t in tools:
    assert len(_t['outputs']) <= 20, (_t['key'], len(_t['outputs']))
