"""Therapy practice suite part 8: the 18 decision tools (every one ends in a verdict and has a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th8_lists import *
import th8_data as D

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, d): return IN(k, label, 'list', key(lst, d), list=lst)
O = OUT
ST = D.STATS; LMV = ST['lm']
LMS = 'DATE(YEAR({today}),MONTH({today})-1,1)'
def LMX(c): return 'SUMIFS({range:pnl.%s},{range:pnl.month},%s)' % (c, LMS)
def P3(c): return 'SUMIFS({range:pnl.%s},{range:pnl.month},">="&DATE(YEAR({today}),MONTH({today})-4,1),{range:pnl.month},"<"&%s)' % (c, LMS)
def LYX(c): return 'SUMIFS({range:pnl.%s},{range:pnl.month},DATE(YEAR({today})-1,MONTH({today})-1,1))' % c
def R12(c): return 'SUMIFS({range:pnl.%s},{range:pnl.month},">="&DATE(YEAR({today}),MONTH({today})-12,1),{range:pnl.month},"<"&DATE(YEAR({today}),MONTH({today}),1))' % c
W12 = '{range:svc_months.month},">="&DATE(YEAR({today}),MONTH({today})-12,1),{range:svc_months.month},"<"&DATE(YEAR({today}),MONTH({today}),1)'
def ro(x, n=0): return round(x, n)
G, A_, R_ = lt('Green'), lt('Amber'), lt('Red')
def SCN(x='{in:sc}'): return 'IF(%s=%s,2,IF(%s=%s,3,1))' % (x, tok('scen', 'Best'), x, tok('scen', 'Worst'))

lm_rev = ST['lm_revenue']; lm_cost = LMV['clinician_pay'] + LMV['staff_pay'] + LMV['rent'] + LMV['other_expenses']
bt = ST['bt']
clin_oct = {r['clinician']: r for r in D.CMR if r['month'] == D.LM0}
kenji = clin_oct['Kenji Watanabe']
tools = []

# 1 ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
LG = lambda g, a: 'IF(%s,%s,IF(%s,%s,%s))' % (g, G, a, A_, R_)
LP = LG('{in:pay}<={set:pay_share_target}+{set:target_tolerance}', '{in:pay}<={set:pay_share_target}+2*{set:target_tolerance}')
LO = LG('{in:ovh}<={set:overhead_target}+{set:target_tolerance}', '{in:ovh}<={set:overhead_target}+2*{set:target_tolerance}')
LM_ = LG('{in:mar}>={set:profit_target}', '{in:mar}>={set:profit_target}-{set:target_tolerance}')
LC = LG('{in:cov}>={set:reserve_low_months}', '{in:cov}>={set:cover_min_months}')
LB = LG('{in:bk}>={set:target_utilisation}-{set:target_tolerance}', '{in:bk}>={set:target_utilisation}-2*{set:target_tolerance}')
SC1 = '((%s=%s)+(%s=%s)+(%s=%s)+(%s=%s)+(%s=%s))' % (LP, G, LO, G, LM_, G, LC, G, LB, G)
tools.append(TOOL('health_check', 'Is the Practice Healthy', 'Is the practice healthy? Five traffic lights',
    'Type this month\'s pay share, overhead share, profit margin, months of expenses in cash and booked share of the session cap; see five traffic lights against your editable targets, the score and how this month compares with the 3-month average and the same month last year.', [
    I('pay', 'Pay share of revenue (clinician and staff pay)', ro(LMV['clinician_pay'] / lm_rev + LMV['staff_pay'] / lm_rev, 3), 'pct'), I('ovh', 'Overhead share of revenue (rent and other expenses)', ro((LMV['rent'] + LMV['other_expenses']) / lm_rev, 3), 'pct'),
    I('mar', 'Profit margin', ro((lm_rev - lm_cost) / lm_rev, 3), 'pct'), I('cov', 'Months of expenses in cash', 1.57, 'num'), I('bk', 'Booked share of the session cap', 0.978, 'pct')], [
    O('Pay share light', 'text', LP), O('Overhead light', 'text', LO), O('Profit margin light', 'text', LM_), O('Cash cover light', 'text', LC), O('Booked share light', 'text', LB),
    O('Targets met (0 to 5)', 'int', SC1),
    O('Profit margin, average of the 3 months before last month', 'pct', 'IFERROR(%s/%s,0)' % (P3('profit'), P3('revenue'))), O('Profit margin, same month last year', 'pct', 'IFERROR(%s/%s,0)' % (LYX('profit'), LYX('revenue'))),
    O('Margin against the 3-month average (points)', 'pct', '{in:mar}-IFERROR(%s/%s,0)' % (P3('profit'), P3('revenue'))),
    O('Pay share, average of the 3 months before last month', 'pct', 'IFERROR((%s+%s)/%s,0)' % (P3('clinician_pay'), P3('staff_pay'), P3('revenue'))),
    O('Verdict', 'text', 'IF(%s>=4,%s,IF(%s=3,%s,%s))' % (SC1, vd('Healthy'), SC1, vd('Watch'), vd('Act now')))],
    GR('What if', ('Pay share rises to 62%', {'pay': 0.62}), ('Overhead rises to 30%', {'ovh': 0.30}), ('Margin falls to 8%', {'mar': 0.08}), ('Cash cover grows to 3.2 months', {'cov': 3.2}), ('Booked share falls to 72%', {'bk': 0.72}))))

# 2 ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
REV2 = '({in:sess}+{in:grp}+{in:sub}-{in:wo})'; COST2 = '({in:cp}+{in:sp}+{in:rent}+{in:oth}+{in:own})'; PROF2 = '(%s-%s)' % (REV2, COST2)
tools.append(TOOL('pnl_statement', 'Practice P&L Statement', 'Practice P&L with owner pay plus profit',
    'Type the month\'s revenue lines and costs (the demo shows last month); see profit, margin and owner pay plus profit as one line, compared with the 3-month average and the same month last year.', [
    I('sess', 'Session revenue', ro(LMV['session_revenue']), 'money'), I('grp', 'Group revenue', ro(LMV['group_revenue']), 'money'), I('sub', 'Sublet income', ro(LMV['sublet_income']), 'money'), I('wo', 'Write-offs', ro(LMV['write_offs']), 'money'),
    I('cp', 'Clinician pay', ro(LMV['clinician_pay']), 'money'), I('sp', 'Staff pay', ro(LMV['staff_pay']), 'money'), I('rent', 'Rent', ro(LMV['rent']), 'money'), I('oth', 'Other expenses', ro(LMV['other_expenses']), 'money'),
    I('own', 'Owner pay booked as a cost (0 if you draw it from profit)', 2500, 'money')], [
    O('Revenue', 'money', REV2), O('Total costs, owner pay included', 'money', COST2), O('Profit', 'money', PROF2), O('Profit margin', 'pct', '%s/%s' % (PROF2, REV2)),
    O('Owner pay plus profit', 'money', '%s+{in:own}' % PROF2), O('Owner pay plus profit, share of revenue', 'pct', '(%s+{in:own})/%s' % (PROF2, REV2)),
    O('Profit margin, average of the 3 months before last month', 'pct', 'IFERROR(%s/%s,0)' % (P3('profit'), P3('revenue'))), O('Profit margin, same month last year', 'pct', 'IFERROR(%s/%s,0)' % (LYX('profit'), LYX('revenue'))),
    O('Margin against the 3-month average (points)', 'pct', '%s/%s-IFERROR(%s/%s,0)' % (PROF2, REV2, P3('profit'), P3('revenue'))), O('Profit wanted at the profit target', 'money', '{set:profit_target}*%s' % REV2),
    O('Profit above (+) or below (-) the target', 'money', '%s-{set:profit_target}*%s' % (PROF2, REV2)),
    O('Verdict', 'text', 'IF(%s/%s>={set:profit_target},%s,%s)' % (PROF2, REV2, vd('Above the profit target'), vd('Below the profit target')))],
    GR('What if', ('Revenue 10% lower', {'sess': ro(LMV['session_revenue'] * 0.9)}), ('Owner pay of 5,000', {'own': 5000}), ('Rent up by 500', {'rent': ro(LMV['rent']) + 500}), ('Clinician pay up 10%', {'cp': ro(LMV['clinician_pay'] * 1.1)}),
       ('A month like August', {'sess': 31000, 'grp': 2200, 'cp': 19200}))))

# 3 ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
PAY3 = '({in:ch}*{in:split})'; ROOM3 = '({set:room_cost_hour}*{in:rmin}/60)'; PS3 = '({in:ch}-%s-%s-{in:mat}-{in:adm})' % (PAY3, ROOM3)
ARR3 = 'SUMIFS({range:svc_months.profit},{range:svc_months.service},{range:services.service},%s)' % W12
tools.append(TOOL('svc_profit', 'Profit per Service Type', 'Profit per service type: grow, fix or drop',
    'Type a service\'s sessions a month, average charge, clinician pay share, room minutes, materials and admin cost; see profit per session and per month, where the service would rank among your ten service types, and a Grow, Fix or Drop verdict.', [
    I('sess', 'Sessions a month', ro(bt['n'] / 12.0), 'num'), I('ch', 'Average charge per session', ro(bt['charge'], 1), 'money'), I('split', 'Clinician pay share of the charge', ro(bt['split'], 3), 'pct'),
    I('rmin', 'Room minutes per session (session plus set-up)', 85), I('mat', 'Materials and claim admin per session', ro(bt['other'] - 7.2, 1), 'money'), I('adm', 'Booking and billing cost per attended session', 7.2, 'money')], [
    O('Clinician pay per session', 'money', PAY3), O('Room cost per session', 'money', ROOM3), O('Profit per session', 'money', PS3), O('Profit per month', 'money', '%s*{in:sess}' % PS3),
    O('Profit margin', 'pct', '%s/{in:ch}' % PS3), O('Profit per year', 'money', '12*{in:sess}*%s' % PS3),
    O('Charge that breaks even', 'money', '(%s+{in:mat}+{in:adm})/(1-{in:split})' % ROOM3),
    O('Rank against your 10 services (11 = below all)', 'int', '1+SUMPRODUCT(({range:services.service}<>"")*(%s>12*{in:sess}*%s))' % (ARR3, PS3)),
    O('Verdict', 'text', 'IF(%s/{in:ch}>={set:profit_target},%s,IF(%s/{in:ch}>=-2*{set:target_tolerance},%s,%s))' % (PS3, vd('Grow'), PS3, vd('Fix'), vd('Drop')))],
    GR('What if', ('Charge up by 10', {'ch': ro(bt['charge'], 1) + 10}), ('Clinician share cut to 55%', {'split': 0.55}), ('Room time cut to 70 minutes', {'rmin': 70}), ('More sessions: 40 a month', {'sess': 40}),
       ('Clinician share cut to 50%', {'split': 0.5}))))

# 4 ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
RM4 = '({set:room_cost_hour}*({in:mins}+{in:setup})/60)'; AD4 = '({set:admin_cost}/(1-{in:ns}))'
def PS4(chg, spl, rmq, mat): return '(%s*(1-%s)-{set:room_cost_hour}*%s/60-%s-%s)' % (chg, spl, rmq, mat, AD4)
CH_UP = '({in:ch}*({in:list}+{in:fstep})/{in:list})'
P0 = PS4('{in:ch}', '{in:split}', '({in:mins}+{in:setup})', '{in:mat}')
P1 = PS4(CH_UP, '{in:split}', '({in:mins}+{in:setup})', '{in:mat}')
P2 = PS4('{in:ch}', '({in:split}-{in:scut})', '({in:mins}+{in:setup})', '{in:mat}')
P3_ = PS4('{in:ch}', '{in:split}', '({in:mins}+{in:setup}-{in:ssave})', '{in:mat}')
P4 = PS4('{in:ch}', '{in:split}', '({in:mins}+{in:setup})', '({in:mat}-{in:msave})')
P5 = PS4(CH_UP, '({in:split}-{in:scut})', '({in:mins}+{in:setup}-{in:ssave})', '({in:mat}-{in:msave})')
BE4 = '(({set:room_cost_hour}*({in:mins}+{in:setup})/60+{in:mat}+%s)/(1-{in:split})*{in:list}/{in:ch})' % AD4
C4 = '({in:ch}*(1-{in:split})-{in:mat})'
tools.append(TOOL('losing_fix', 'Losing Service Fix', 'Losing service fix: fee, split and savings',
    'Type the weak service\'s charge, list fee, clinician split, session and set-up minutes, materials, no-show rate and the size of each change; see profit per session after each change, the break-even fee and the sessions a week needed.', [
    I('ch', 'Average charge per attended session', ro(bt['charge'], 1), 'money'), I('list', 'List fee', 90, 'money'), I('split', 'Clinician pay share of the charge', ro(bt['split'], 3), 'pct'), I('mins', 'Session minutes', 60),
    I('setup', 'Set-up and tidy minutes in the room', 25), I('mat', 'Materials and claim admin per session', ro(bt['other'] - 7.2, 1), 'money'), I('ns', 'No-show and late-cancel rate of booked sessions', 0.17, 'pct'),
    I('sw', 'Sessions a week now', 7), I('fstep', 'Fee rise to test', 10, 'money'), I('scut', 'Split cut to test (points)', 0.05, 'pct'), I('ssave', 'Set-up minutes saved', 10), I('msave', 'Materials saved per session', 3, 'money')], [
    O('Profit per session today', 'money', P0), O('Profit per session after the fee rise', 'money', P1), O('Profit per session after the split cut', 'money', P2), O('Profit per session after the set-up saving', 'money', P3_),
    O('Profit per session after the materials saving', 'money', P4), O('Profit per session after all four changes', 'money', P5), O('List fee that breaks even, nothing else changed', 'money', BE4),
    O('Rise in the list fee needed', 'pct', '%s/{in:list}-1' % BE4), O('Loss per month today', 'money', '%s*{in:sw}*52/12' % P0),
    O('Sessions a week needed to break even at today\'s terms', 'num', 'IF(%s<=0,0,ROUNDUP({in:sw}*(%s+%s)/%s,1))' % (C4, RM4, AD4, C4)),
    O('Verdict', 'text', 'IF(%s<={set:market_fee_high},%s&" "&ROUNDUP(%s,0),IF(%s>=0,%s,%s))' % (BE4, vd('Raise the fee to'), BE4, P2, vd('Change the split'), vd('Stop offering it')))],
    GR('What if', ('Fee rise of 20', {'fstep': 20}), ('Split cut of 8 points', {'scut': 0.08}), ('Fewer no-shows: 8%', {'ns': 0.08}), ('Busier: 10 sessions a week', {'sw': 10}), ('Weak case: split 0.7, no changes', {'split': 0.7, 'ssave': 0, 'msave': 0, 'scut': 0, 'fstep': 0}))))

# 5 ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
ACH5 = '({in:fee}*{in:recv})'; COST5 = '({in:dir}+{in:ovh})'; NEED5 = '(%s/((1-{set:profit_target})*{in:recv}))' % COST5
tools.append(TOOL('fee_right', 'Is My Fee Right', 'Is my fee right? Fee, margin and market band',
    'Type a service\'s list fee, the share of it you actually receive, the direct cost and the overhead per session; see the fee that keeps your target margin, where your fee sits in your local market band and five fee steps.', [
    I('fee', 'List fee of the service', 90, 'money'), I('recv', 'Share of the list fee you actually receive', ro(bt['charge'] / 90.0, 3), 'pct'),
    I('dir', 'Direct cost per session (pay, room, materials, admin)', ro(bt['charge'] * bt['split'] + bt['room'] + bt['other']), 'money'),
    I('ovh', 'Overhead per attended session (rent and other expenses)', ro((LMV['rent'] + LMV['other_expenses']) / LMV['sessions']), 'money')], [
    O('Average charge you receive', 'money', ACH5), O('All-in cost per session', 'money', COST5), O('Profit per session today', 'money', '%s-%s' % (ACH5, COST5)), O('Profit margin today', 'pct', '(%s-%s)/%s' % (ACH5, COST5, ACH5)),
    O('List fee that keeps the target margin', 'money', NEED5), O('Change in the list fee needed', 'pct', '%s/{in:fee}-1' % NEED5), O('Market band, low', 'money', '{set:market_fee_low}'), O('Market band, high', 'money', '{set:market_fee_high}'),
    O('Fee position in the band (0 low end, 1 high end)', 'num', '({in:fee}-{set:market_fee_low})/({set:market_fee_high}-{set:market_fee_low})'),
    O('Verdict', 'text', 'IF({in:fee}<%s,%s,IF({in:fee}>{set:market_fee_high},%s,%s))' % (NEED5, vd('Raise'), vd('Hold'), vd('Right')))],
    GR('Five fee steps', ('List fee 100', {'fee': 100}), ('List fee 110', {'fee': 110}), ('List fee 125', {'fee': 125}), ('List fee 140', {'fee': 140}), ('List fee 155', {'fee': 155}))))

# 6 ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
K = kenji; kch = ro(K['revenue'] / K['attended'], 1)
REV6 = '({in:att}*{in:ch})'
PAY6 = 'IF({in:pt}=%s,{in:sal}*(1+{set:employer_cost_pct}),IF({in:pt}=%s,{in:split}*%s,{in:att}*{in:sp}))' % (tok('hpay', 'Salary'), tok('hpay', 'Percentage split'), REV6)
RM6 = '({in:att}*{set:room_cost_hour}*{in:rmin}/60)'; AD6 = '({in:att}*{set:admin_cost}*{in:bk})'
PRO6 = '(%s-%s-%s-%s)' % (REV6, PAY6, RM6, AD6)
ARR6 = 'SUMIFS({range:clin_months.profit},{range:clin_months.clinician},{range:team.name},{range:clin_months.month},">="&DATE(YEAR({today}),MONTH({today})-12,1),{range:clin_months.month},"<"&DATE(YEAR({today}),MONTH({today}),1))'
tools.append(TOOL('clin_profit', 'Profit per Clinician', 'Profit per clinician after pay, room time and admin',
    'Choose a pay type and type a clinician\'s sessions a month, charge, pay terms and room minutes; see revenue, all-in pay cost, profit and margin, where the clinician would rank among your six clinicians, and whether the margin covers overhead and the profit target.', [
    IL('pt', 'Pay type', 'hpay', 'Percentage split'), I('att', 'Attended sessions a month', K['attended'], 'num'), I('ch', 'Average charge per session', kch, 'money'), I('split', 'Share of the charge paid (percentage split)', 0.6, 'pct'),
    I('sal', 'Monthly salary (salary)', 4800, 'money'), I('sp', 'Pay per session (per session)', 45, 'money'), I('rmin', 'Room minutes per session', 55), I('bk', 'Booked sessions per attended session', ro(K['booked'] / K['attended'], 2), 'num')], [
    O('Revenue a month', 'money', REV6), O('All-in pay cost a month', 'money', PAY6), O('Room cost a month', 'money', RM6), O('Admin cost a month', 'money', AD6), O('Profit a month', 'money', PRO6),
    O('Profit margin', 'pct', '%s/%s' % (PRO6, REV6)), O('Profit per attended session', 'money', '%s/{in:att}' % PRO6),
    O('Rank against your 6 clinicians (7 = below all)', 'int', '1+SUMPRODUCT(({range:team.name}<>"")*(COUNTIFS({range:clin_months.clinician},{range:team.name})>0)*(%s>12*%s))' % (ARR6, PRO6)),
    O('Margin wanted to cover overhead and the profit target', 'pct', '{set:overhead_target}+{set:profit_target}'),
    O('Verdict', 'text', 'IF(%s/%s>={set:overhead_target}+{set:profit_target},%s,%s)' % (PRO6, REV6, vd('Above target'), vd('Below target')))],
    GR('What if', ('Salary type, 4,800 a month', {'pt': '=' + tok('hpay', 'Salary')}), ('Per session type, 45 a session', {'pt': '=' + tok('hpay', 'Per session')}), ('Split raised to 65%', {'split': 0.65}),
       ('Fewer sessions: 60 a month', {'att': 60}), ('Charge up by 10', {'ch': kch + 10}))))

# 7 ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
rcm = [r for r in D.room_costs_d() if r['month'] == D.LM0][0]
TOT7 = '({in:rent}+{in:clean}+{in:power})'
tools.append(TOOL('room_hour', 'Cost per Room Hour Used', 'Cost per room hour used against the rate you charge sessions',
    'Type a month\'s rent, cleaning, power, open room hours and room hours used; see the cost per open hour, per used hour, the idle cost, how far the cost per used hour is above the rate you charge sessions and a Room use low or healthy verdict.', [
    I('rent', 'Rent', ro(rcm['rent']), 'money'), I('clean', 'Cleaning', ro(rcm['cleaning']), 'money'), I('power', 'Power, water and heating', ro(rcm['utilities']), 'money'), I('open', 'Open room hours', ro(rcm['open_hours']), 'num'),
    I('used', 'Room hours used (sessions, groups and sublets)', ro(rcm['used_hours']), 'num')], [
    O('Total room cost', 'money', TOT7), O('Cost per open hour', 'money', '%s/{in:open}' % TOT7), O('Cost per used hour', 'money', '%s/{in:used}' % TOT7), O('Use share of open hours', 'pct', '{in:used}/{in:open}'),
    O('Rate charged to sessions per used hour', 'money', '{set:room_cost_hour}'), O('Cost per used hour above (+) the rate charged', 'money', '%s/{in:used}-{set:room_cost_hour}' % TOT7),
    O('Cost of the hours not used', 'money', '({in:open}-{in:used})*%s/{in:open}' % TOT7), O('Used hours needed for the use target', 'int', 'MAX(0,ROUNDUP({set:room_use_target}*{in:open}-{in:used},0))'),
    O('Cost per used hour at the use target', 'money', '%s/MAX({in:used},{set:room_use_target}*{in:open})' % TOT7),
    O('Verdict', 'text', 'IF({in:used}/{in:open}<{set:room_use_target},%s,%s)' % (vd('Room use low'), vd('Room use healthy')))],
    GR('What if', ('Used hours up 20%', {'used': ro(rcm['used_hours'] * 1.2)}), ('Close evenings: open hours down 20%', {'open': ro(rcm['open_hours'] * 0.8)}), ('Rent cut by 10%', {'rent': ro(rcm['rent'] * 0.9)}),
       ('A busy room month: 600 hours used', {'used': 600}))))

# 8 ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
oth_ovh = ro(LMV['other_expenses'] - 640 - 274 - 230)
OV8 = '({in:rent}+{in:clean}+{in:soft}+{in:ins}+{in:adm}+{in:oth})'
tools.append(TOOL('overhead_check', 'Overhead Share Check', 'Overhead share check against the 15 to 25 percent band',
    'Type a month\'s rent, cleaning, software, insurance, admin pay counted as overhead, other overhead and revenue; see the overhead share against the band around your target, the revenue or saving that brings it to target, and a Lean, In band or Heavy verdict.', [
    I('rent', 'Rent', ro(LMV['rent']), 'money'), I('clean', 'Cleaning', 640, 'money'), I('soft', 'Practice software', 274, 'money'), I('ins', 'Insurance', 230, 'money'),
    I('adm', 'Admin pay counted as overhead (0 if it is in your pay share)', 0, 'money'), I('oth', 'Other overhead (phone, supplies, fees, training)', oth_ovh, 'money'), I('rev', 'Revenue', ro(lm_rev), 'money')], [
    O('Total overhead', 'money', OV8), O('Overhead share of revenue', 'pct', '%s/{in:rev}' % OV8), O('Band, low', 'pct', '{set:overhead_target}-{set:target_tolerance}'), O('Band, high', 'pct', '{set:overhead_target}+{set:target_tolerance}'),
    O('Revenue needed for the target share', 'money', '%s/{set:overhead_target}' % OV8), O('Overhead to cut for the top of the band', 'money', 'MAX(0,%s-({set:overhead_target}+{set:target_tolerance})*{in:rev})' % OV8),
    O('Overhead share, average of the 3 months before last month', 'pct', 'IFERROR(%s/%s,0)' % ('(%s+%s)' % (P3('rent'), P3('other_expenses')), P3('revenue'))),
    O('Overhead share, same month last year', 'pct', 'IFERROR((%s+%s)/%s,0)' % (LYX('rent'), LYX('other_expenses'), LYX('revenue'))),
    O('Verdict', 'text', 'IF(%s/{in:rev}<{set:overhead_target}-{set:target_tolerance},%s,IF(%s/{in:rev}<={set:overhead_target}+{set:target_tolerance},%s,%s))' % (OV8, vd('Lean'), OV8, vd('In band'), vd('Heavy')))],
    GR('What if', ('A quiet month: revenue 36,000', {'rev': 36000}), ('Rent up by 10%', {'rent': ro(LMV['rent'] * 1.1)}), ('Add admin pay of 2,700', {'adm': 2700}), ('Cut other overhead by 800', {'oth': oth_ovh - 800}))))

# 9 ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
fixed_m = ro(6800 + 9300 * 1.12 + LMV['staff_pay'] + 3000, -2)
var_m = ro((lm_cost - fixed_m) / LMV['sessions'])
CT9 = '({in:ch}-{in:var})'
tools.append(TOOL('breakeven', 'Break-even Sessions a Month', 'Break-even sessions a month and the margin of safety',
    'Type the fixed costs a month, the average charge and the variable cost per session; see the sessions you need to break even, to reach the profit target, the margin of safety against last month\'s attended sessions and five charge steps.', [
    I('fix', 'Fixed costs a month (rent, salaries, staff pay, overhead)', fixed_m, 'money'), I('ch', 'Average charge per attended session', ro(lm_rev / LMV['sessions']), 'money'), I('var', 'Variable cost per session (pay, materials, admin)', var_m, 'money')], [
    O('Contribution per session', 'money', CT9), O('Break-even sessions a month', 'int', 'ROUNDUP({in:fix}/%s,0)' % CT9), O('Break-even sessions a week', 'num', '{in:fix}/%s*12/52' % CT9),
    O('Attended sessions last month', 'int', LMX('sessions')), O('Margin of safety against last month', 'pct', '(%s-{in:fix}/%s)/%s' % (LMX('sessions'), CT9, LMX('sessions'))),
    O('Sessions a month for the profit target', 'int', 'IF(%s-{set:profit_target}*{in:ch}<=0,0,ROUNDUP({in:fix}/(%s-{set:profit_target}*{in:ch}),0))' % (CT9, CT9)),
    O('Profit at last month\'s sessions', 'money', '%s*%s-{in:fix}' % (LMX('sessions'), CT9)),
    O('Verdict', 'text', 'IF(%s>={in:fix}/%s,%s,%s)' % (LMX('sessions'), CT9, vd('Above break-even'), vd('Below break-even')))],
    GR('Five charge steps', ('Charge 100', {'ch': 100}), ('Charge 110', {'ch': 110}), ('Charge 122', {'ch': 122}), ('Charge 135', {'ch': 135}), ('Charge 150', {'ch': 150}))))

# 10 -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
CASHNOW = ST['cash_now']
LOWC = 'MIN({range:forecast.closing})'; POS10 = 'MATCH(%s,{range:forecast.closing},0)' % LOWC
WS10 = 'INDEX({range:forecast.week_start},%s)' % POS10
RECV10 = 'SUMPRODUCT(({range:forecast.week_start}<=%s)*({range:forecast.week_start}>0)*({range:forecast.client_payments}+{range:forecast.payer_payments}))' % WS10
COST10 = 'SUMPRODUCT(({range:forecast.week_start}<=%s)*({range:forecast.week_start}>0)*({range:forecast.pay}+{range:forecast.rent_costs}+{range:forecast.tax_set_aside}+{range:forecast.owner_draw}))' % WS10
RF = 'CHOOSE(%s,1,1.08,0.85)' % SCN(); CF = 'CHOOSE(%s,1,0.98,1.04)' % SCN()
LOW10 = '(%s+({in:open}-INDEX({range:cash.closing},MATCH(MAX({range:cash.month}),{range:cash.month},0)))+%s*(%s-1)-%s*(%s-1)-IF({in:wk}<=%s,{in:one},0))' % (LOWC, RECV10, RF, COST10, CF, POS10)
tools.append(TOOL('cash_forecast', '13-week Cash Flow Forecast', '13-week cash flow forecast with scenarios',
    'Type today\'s cash, a scenario (Base, Best or Worst) and a one-off payment and its week; the 13-week table on its own sheet gives the base case from your history, and the lowest week, the headroom above the cash floor and a floor verdict show here.', [
    I('open', 'Cash today', ro(CASHNOW), 'money'), IL('sc', 'Scenario', 'scen', 'Base'), I('one', 'One-off payment (equipment, deposit, tax catch-up)', 4500, 'money'), I('wk', 'Week of the one-off payment (1 to 13)', 6)], [
    O('Lowest closing cash in the base case', 'money', LOWC), O('Lowest week in the base case', 'text', 'INDEX({range:forecast.week},%s)' % POS10), O('Lowest closing cash in the scenario, with payment', 'money', LOW10),
    O('Closing cash in week 13, scenario', 'money', '(INDEX({range:forecast.closing},13)+({in:open}-INDEX({range:cash.closing},MATCH(MAX({range:cash.month}),{range:cash.month},0)))+SUMPRODUCT(({range:forecast.week_start}>0)*({range:forecast.client_payments}+{range:forecast.payer_payments}))*(%s-1)-SUMPRODUCT(({range:forecast.week_start}>0)*({range:forecast.pay}+{range:forecast.rent_costs}+{range:forecast.tax_set_aside}+{range:forecast.owner_draw}))*(%s-1)-{in:one})' % (RF, CF)),
    O('Cash floor', 'money', '{set:cash_floor}'), O('Headroom above the floor at the lowest point', 'money', '%s-{set:cash_floor}' % LOW10), O('Weeks below the floor in the base case', 'int', 'COUNTIFS({range:forecast.below_floor},%s)' % vd('Below the floor')),
    O('Verdict', 'text', 'IF(%s>={set:cash_floor},%s,%s&" "&%s)' % (LOW10, vd('Above the floor'), vd('Below the floor in week'), POS10))],
    GR('What if', ('Worst case', {'sc': '=' + tok('scen', 'Worst')}), ('Best case', {'sc': '=' + tok('scen', 'Best')}), ('One-off payment of 40,000 in week 3', {'one': 40000, 'wk': 3}), ('Low cash start of 30,000', {'open': 30000}), ('Worst case, payment of 25,000 in week 2', {'sc': '=' + tok('scen', 'Worst'), 'one': 25000, 'wk': 2}))))

# 11 -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
exp_m = ro(CASH_ROW := (D.CASH[-2]['staff_pay'] + D.CASH[-2]['contractor_pay'] + D.CASH[-2]['rent'] + D.CASH[-2]['other_expenses']), -2)
MOS = '({in:cash}/{in:exp})'
tools.append(TOOL('cash_cover', 'Cash Cover Check', 'Cash cover: months of expenses against the band',
    'Type cash now, the expenses you pay in a month and what you can put into the reserve each month; see the months of expenses in cash against the reserve band, the gap to the band and to your wanted months, and how long it takes to close it.', [
    I('cash', 'Cash now', ro(CASHNOW), 'money'), I('exp', 'Expenses paid in a month (pay, rent, other expenses)', exp_m, 'money'), I('save', 'Cash you can put into the reserve each month', 3000, 'money')], [
    O('Months of expenses in cash', 'num', MOS), O('Days of expenses in cash', 'int', '{in:cash}/({in:exp}/30)'), O('Reserve band, low (cash)', 'money', '{set:reserve_low_months}*{in:exp}'), O('Reserve band, high (cash)', 'money', '{set:reserve_high_months}*{in:exp}'),
    O('Gap to the low end of the band', 'money', 'MAX(0,{set:reserve_low_months}*{in:exp}-{in:cash})'), O('Gap to your wanted months', 'money', 'MAX(0,{set:cash_cover_months}*{in:exp}-{in:cash})'),
    O('Months to reach the low end of the band at this saving', 'int', 'IF({in:save}<=0,0,ROUNDUP(MAX(0,{set:reserve_low_months}*{in:exp}-{in:cash})/{in:save},0))'), O('Cash above the floor', 'money', '{in:cash}-{set:cash_floor}'),
    O('Verdict', 'text', 'IF(%s>={set:reserve_low_months},%s,%s)' % (MOS, vd('Reserve met'), vd('Build the reserve')))],
    GR('What if', ('Save 6,000 a month', {'save': 6000}), ('Cash grows to 110,000', {'cash': 110000}), ('Expenses cut to 30,000 a month', {'exp': 30000}), ('Low cash: 25,000', {'cash': 25000}))))

# 12 -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
bills28 = 'SUMIFS({range:bills.amount},{range:bills.due_date},">="&{today},{range:bills.due_date},"<="&{today}+28)'
NET12 = '({in:cash}-{set:cash_floor}-{in:tax}-%s)' % bills28
prof12 = ro(sum(r['profit'] for r in D.TAX if D.C.iso(D.C.month_start(12)) <= r['month'] < D.MS0) / 12.0, -2)
SAFE12 = 'MIN({in:plan},MAX(0,%s),MAX(0,{in:prof}*(1-{set:tax_set_aside_pct})))' % NET12
tools.append(TOOL('safe_draw', 'Safe Owner Draw', 'Safe owner draw that keeps cash above the floor',
    'Type cash now, the tax set-aside still to transfer, the profit you expect this month and the draw you plan; see the draw that keeps cash above the floor after the tax set-aside and the bills due in the next 4 weeks, and a Take the full draw, Take less or Wait verdict.', [
    I('cash', 'Cash now', ro(CASHNOW), 'money'), I('tax', 'Tax set-aside still to transfer (confirm with your adviser)', ro(D.TAX[-2]['set_aside']), 'money'), I('prof', 'Profit you expect this month', prof12, 'money'), I('plan', 'Draw you plan', 7000, 'money')], [
    O('Cash above the floor', 'money', '{in:cash}-{set:cash_floor}'), O('Bills due in the next 4 weeks', 'money', bills28), O('Cash free for a draw after tax and bills', 'money', 'MAX(0,%s)' % NET12),
    O('Draw the profit allows after the tax set-aside', 'money', 'MAX(0,{in:prof}*(1-{set:tax_set_aside_pct}))'), O('Safe draw', 'money', SAFE12), O('Draw held back', 'money', '{in:plan}-%s' % SAFE12),
    O('Cash after the draw', 'money', '{in:cash}-%s' % SAFE12), O('Owner draw taken this year', 'money', 'SUMIFS({range:cash.owner_draw},{range:cash.month},">="&DATE(YEAR({today}),1,1))'),
    O('Verdict', 'text', 'IF(%s>={in:plan},%s,IF(%s>0,%s,%s))' % (SAFE12, vd('Take the full draw'), SAFE12, vd('Take less'), vd('Wait')))],
    GR('What if', ('A larger draw of 15,000', {'plan': 15000}), ('A quiet month: profit 2,000', {'prof': 2000}), ('Low cash of 30,000', {'cash': 30000}), ('Cash just above the floor: 29,000', {'cash': 29000}), ('Large tax payment of 12,000', {'tax': 12000}))))

# 13 -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
ytd_p = round(sum(r['profit'] for r in D.TAX if D.MS0[:4] + '-01-01' <= r['month'] <= D.LM0), 2)
paid_p = round(sum(r['set_aside'] for r in D.TAX if D.MS0[:4] + '-01-01' <= r['month'] < D.LM0), 2)
HOLD13 = 'MAX(0,{in:prof}*{in:share}-{in:paid})'
tools.append(TOOL('tax_setaside', 'Income Tax Set-aside', 'Income tax set-aside to hold now (confirm with your adviser)',
    'Type the profit to date this year, your set-aside share and what you already set aside; see what to hold now, when the next transfer is due and a Transfer now or Funded verdict. Confirm the share with your adviser.', [
    I('prof', 'Profit to date this year', ro(ytd_p), 'money'), I('share', 'Set-aside share of profit (confirm with your adviser)', 0.25, 'pct'), I('paid', 'Already set aside this year', ro(paid_p), 'money')], [
    O('Set-aside due on the profit to date', 'money', '{in:prof}*{in:share}'), O('Amount to hold now', 'money', HOLD13), O('Share already funded', 'pct', 'MIN(1,{in:paid}/({in:prof}*{in:share}))'),
    O('Next transfer due on', 'date', 'SUMPRODUCT(MIN(({range:tax.status}<>%s)*({range:tax.due_date}>0)*{range:tax.due_date}+((({range:tax.status}=%s)+({range:tax.due_date}=0))>0)*99999))' % (tok('taxst', 'Paid'), tok('taxst', 'Paid'))),
    O('Set-aside for the whole year at this pace', 'money', '{in:prof}/MAX(1,MONTH({today})-1)*12*{in:share}'), O('Set-aside from the profit of last month', 'money', '%s*{in:share}' % LMX('profit')),
    O('Verdict', 'text', 'IF(%s>1,%s,%s)' % (HOLD13, vd('Transfer now'), vd('Funded')))],
    GR('What if', ('Share of 30%', {'share': 0.30}), ('Already funded in full', {'paid': ro(ytd_p * 0.25) + 100}), ('Strong profit: 160,000 to date', {'prof': 160000}), ('Nothing set aside yet', {'paid': 0}))))

# 14 -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
VOL14 = 'CHOOSE(%s,1,1.1,0.8)' % SCN()
PS14 = 'IF({in:pt}=%s,{in:split}*{in:ch},IF({in:pt}=%s,{in:sp},0))' % (tok('hpay', 'Percentage split'), tok('hpay', 'Per session'))
SAL14 = 'IF({in:pt}=%s,{in:sal}*(1+{set:employer_cost_pct}),0)' % tok('hpay', 'Salary')
S14 = '({in:sw}*52/12*%s)' % VOL14; U14 = '({in:ch}-%s-{set:room_cost_hour}*50/60-{set:admin_cost})' % PS14
RAMP14 = '(0.5*%s*%s-%s)' % (S14, U14, SAL14); FULL14 = '(%s*%s-%s)' % (S14, U14, SAL14)
YR14 = '({in:ramp}*%s+(12-{in:ramp})*%s-{in:setup})' % (RAMP14, FULL14)
BE14 = 'IF(%s<=0,0,IF(AND(%s>0,{in:setup}<={in:ramp}*%s),ROUNDUP({in:setup}/%s,0),{in:ramp}+ROUNDUP(({in:setup}-{in:ramp}*%s)/%s,0)))' % (FULL14, RAMP14, RAMP14, RAMP14, RAMP14, FULL14)
PAYTIE = '({in:psh}*%s*{in:ch}*{in:lag})' % S14
tools.append(TOOL('hire_case', 'Hire a Clinician Business Case', 'Hire a clinician: business case and payer wait',
    'Choose a pay type and scenario and type the sessions a week, charge, ramp-up months, pay terms, set-up cost and the months before a new clinician can bill a third-party payer; see first-year profit, the break-even month, the cash tied up and a Hire now or Wait verdict.', [
    IL('pt', 'Pay type', 'hpay', 'Salary'), IL('sc', 'Scenario', 'scen', 'Base'), I('sw', 'Sessions a week at full volume', 20), I('ch', 'Average charge per session', 118, 'money'), I('ramp', 'Ramp-up months at half volume', 4),
    I('sal', 'Monthly salary (salary)', 4800, 'money'), I('split', 'Share of the charge paid (percentage split)', 0.6, 'pct'), I('sp', 'Pay per session (per session)', 45, 'money'), I('setup', 'Set-up cost (laptop, furniture, recruiting)', 3200, 'money'),
    I('psh', 'Share of the new clinician\'s sessions billed to a payer', 0.3, 'pct'), I('lag', 'Months before the new clinician can bill a payer', 3)], [
    O('Sessions a month at full volume', 'int', S14), O('Pay cost per session', 'money', PS14), O('Monthly salary cost with employer costs', 'money', SAL14), O('Profit a month at half volume', 'money', RAMP14), O('Profit a month at full volume', 'money', FULL14),
    O('First-year profit', 'money', YR14), O('Break-even month (0 means never)', 'int', BE14), O('Cash tied up while payer billing waits', 'money', PAYTIE),
    O('Cash needed before it pays back', 'money', '{in:setup}+%s+MAX(0,-{in:ramp}*%s)' % (PAYTIE, RAMP14)),
    O('Verdict', 'text', 'IF(AND(%s>0,%s>0,%s<=9),%s,%s)' % (YR14, BE14, BE14, vd('Hire now'), vd('Wait')))],
    GR('What if', ('Best case', {'sc': '=' + tok('scen', 'Best')}), ('Worst case', {'sc': '=' + tok('scen', 'Worst')}), ('Contract clinician, 60 percent split', {'pt': '=' + tok('hpay', 'Percentage split')}), ('Associate paid per session', {'pt': '=' + tok('hpay', 'Per session'), 'ch': 100, 'sw': 15}),
       ('Slow start: 6 months, 14 sessions', {'ramp': 6, 'sw': 14}))))

# 15 -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
CM15 = '({in:es}*52/12*({in:ch}*(1-{in:paysh})-{set:admin_cost})+{in:sh}*52/12*{in:sr}-{in:rent})'
UN15 = '({in:ch}*(1-{in:paysh})-{set:admin_cost})'
tools.append(TOOL('add_room', 'Add a Room', 'Add a room: yearly profit and payback months',
    'Type the extra rent, room hours, expected sessions and sublet hours a week, charge and set-up cost; see profit a month and a year, the payback months, the sessions a week the room must fill to pay its rent and an Add the room or Wait verdict.', [
    I('rent', 'Extra rent a month', 1250, 'money'), I('rh', 'Room hours open a week', 55), I('es', 'Expected sessions a week in the room', 14), I('sh', 'Sublet hours a week', 0), I('sr', 'Sublet rate an hour', 22, 'money'),
    I('ch', 'Average charge per session', 122, 'money'), I('paysh', 'Clinician pay share of the charge', 0.52, 'pct'), I('setup', 'Set-up cost', 4800, 'money')], [
    O('Profit a session after pay and admin', 'money', UN15), O('Profit a month', 'money', CM15), O('First-year profit after the set-up cost', 'money', '12*%s-{in:setup}' % CM15),
    O('Payback months', 'int', 'IF(%s<=0,0,ROUNDUP({in:setup}/%s,0))' % (CM15, CM15)), O('Sessions a week the room must fill to pay its rent', 'num', '({in:rent}-{in:sh}*52/12*{in:sr})/(52/12*%s)' % UN15),
    O('Use share of the room hours', 'pct', '({in:es}*50/60+{in:sh})/{in:rh}'),
    O('Verdict', 'text', 'IF(AND(%s>0,{in:setup}/%s<=18),%s,%s)' % (CM15, CM15, vd('Add the room'), vd('Wait')))],
    GR('What if', ('Quarter use: 5 sessions a week', {'es': 5}), ('Sublet 12 hours instead', {'es': 0, 'sh': 12}), ('Large room: rent 1,800', {'rent': 1800}), ('Full use: 22 sessions a week', {'es': 22}), ('Fees 10% higher', {'ch': 134}))))

# 16 -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
ON16 = '({in:add}*{in:onl})'; NEED16 = '({in:add}-%s)' % ON16; UN16 = '({in:ch}*(1-{in:paysh})-{set:admin_cost})'
INC16 = '(%s*52*%s-12*{in:rent}-{in:rsetup})' % (NEED16, UN16)
tools.append(TOOL('online_or_room', 'Online Capacity or a New Room', 'Online capacity or a new room: cheaper way',
    'Type the sessions a week to add, the share clients accept online, a new room\'s rent and set-up, online set-up, charge and pay share; see the capacity each way adds, the yearly cost of each and a Go online first or Add a room verdict.', [
    I('add', 'Sessions a week to add', 12), I('onl', 'Share of the added sessions that clients accept online', 0.5, 'pct'), I('rent', 'New room: extra rent a month', 1250, 'money'), I('rsetup', 'New room: set-up cost', 4800, 'money'),
    I('osetup', 'Online: set-up cost (headset, camera, software seat)', 700, 'money'), I('ch', 'Average charge per session', 122, 'money'), I('paysh', 'Clinician pay share of the charge', 0.52, 'pct')], [
    O('Sessions a week that fit online', 'num', ON16), O('Sessions a week that still need a room', 'num', NEED16), O('Profit a year, online first (online sessions only)', 'money', '%s*52*%s-{in:osetup}' % (ON16, UN16)),
    O('Profit a year, new room (all added sessions)', 'money', '{in:add}*52*%s-12*{in:rent}-{in:rsetup}' % UN16), O('Yearly cost of the new room (rent and set-up)', 'money', '12*{in:rent}+{in:rsetup}'),
    O('Extra profit a year of the room over online first', 'money', INC16), O('Cost of the room per session it adds beyond online', 'money', 'IF(%s<=0,0,(12*{in:rent}+{in:rsetup})/(%s*52))' % (NEED16, NEED16)),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (INC16, vd('Add a room'), vd('Go online first')))],
    GR('What if', ('Fewer clients accept online: 30%', {'onl': 0.3}), ('More sessions to add: 20', {'add': 20}), ('Cheaper room: rent 900', {'rent': 900}), ('Most clients online: 80%', {'onl': 0.8}), ('Add 16 sessions with 40% online', {'add': 16, 'onl': 0.4}))))

# 17 -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
CAT17 = lambda c: 'IFERROR(INDEX({range:budget.%s},MATCH({in:cat},{range:budget.category},0)),0)' % c
FR17 = '(({today}-DATE(YEAR({today}),1,1)+1)/365)'
TOP = lambda n: 'IFERROR(INDEX({range:budget.category},MATCH(LARGE({range:budget.variance},%d),{range:budget.variance},0))&"","")' % n
TOPV = lambda n: 'IFERROR(LARGE({range:budget.variance},%d),0)' % n
tools.append(TOOL('budget_actual', 'Budget against Actual', 'Budget against actual and the top overspends',
    'Choose a category and a saving; see its yearly budget, the budget to date, what was spent, the year-end projection at this pace and a Within budget, Watch or Over budget verdict, plus the three largest overspends of all categories.', [
    IL('cat', 'Category', 'ecat', 'Marketing'), I('cut', 'Cut in the monthly spend from now on', 0.1, 'pct')], [
    O('Yearly budget', 'money', CAT17('yearly_budget')), O('Budget to date', 'money', CAT17('budget_to_date')), O('Spent this year', 'money', CAT17('spent')), O('Spent over (+) or under (-) the budget to date', 'money', CAT17('variance')),
    O('Left in the yearly budget', 'money', CAT17('left')), O('Projected spend for the year at this pace', 'money', '%s/%s' % (CAT17('spent'), FR17)),
    O('Projected spend after the cut', 'money', '%s+(%s/%s-%s)*(1-{in:cut})' % (CAT17('spent'), CAT17('spent'), FR17, CAT17('spent'))),
    O('Largest overspend, category', 'text', TOP(1)), O('Largest overspend, amount', 'money', TOPV(1)), O('Second largest overspend, category', 'text', TOP(2)), O('Second largest overspend, amount', 'money', TOPV(2)),
    O('Third largest overspend, category', 'text', TOP(3)), O('Third largest overspend, amount', 'money', TOPV(3)),
    O('Verdict for the category', 'text', 'IF(%s<=%s,%s,IF(%s<=1.1*%s,%s,%s))' % (CAT17('spent'), CAT17('budget_to_date'), vd('Within budget'), CAT17('spent'), CAT17('budget_to_date'), vd('Watch'), vd('Over budget')))],
    GR('What if', ('Training', {'cat': '=' + tok('ecat', 'Training')}), ('Therapy materials', {'cat': '=' + tok('ecat', 'Therapy materials')}), ('Rent', {'cat': '=' + tok('ecat', 'Rent')}), ('Marketing with a 25% cut', {'cut': 0.25}), ('Supervision', {'cat': '=' + tok('ecat', 'Supervision')}))))

# 18 -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
AV12 = '(%s/12)' % R12('sessions')
TR18 = 'MAX(0.9,MIN(1.1,IFERROR(SUMIFS({range:pnl.sessions},{range:pnl.month},">="&DATE(YEAR({today}),MONTH({today})-3,1),{range:pnl.month},"<"&DATE(YEAR({today}),MONTH({today}),1))/SUMIFS({range:pnl.sessions},{range:pnl.month},">="&DATE(YEAR({today})-1,MONTH({today})-3,1),{range:pnl.month},"<"&DATE(YEAR({today})-1,MONTH({today}),1)),1)))'
SES18 = '(%s*%s*CHOOSE(%s,1,1.06,0.92))' % (AV12, TR18, SCN())
REV18 = '(12*%s*{in:ch})' % SES18
PAYS18 = 'IFERROR((%s+%s)/%s,0)' % (R12('clinician_pay'), R12('staff_pay'), R12('revenue'))
FIX18 = '((%s+%s)*(1+{in:cg}))' % (R12('rent'), R12('other_expenses'))
PRO18 = '(%s-%s*%s-%s)' % (REV18, REV18, PAYS18, FIX18)
tools.append(TOOL('profit_forecast', '12-month Profit Forecast', '12-month profit forecast with scenarios',
    'Type an average charge, the cost growth and a scenario (Base, Best or Worst); sessions come from your last 12 months and their trend, and you see yearly revenue, costs, profit, margin, the closing cash after draws and tax, and a Meets the profit target or Below the target verdict.', [
    I('ch', 'Average revenue per attended session', 121, 'money'), I('cg', 'Growth of rent and other expenses', 0.03, 'pct'), IL('sc', 'Scenario', 'scen', 'Base')], [
    O('Attended sessions a month from your own history', 'int', SES18), O('Trend factor of the last 3 months against a year earlier', 'num', TR18), O('Revenue for the next 12 months', 'money', REV18),
    O('Pay share of revenue in the last 12 months', 'pct', PAYS18), O('Rent and other expenses with growth', 'money', FIX18), O('Profit for the next 12 months', 'money', PRO18), O('Profit margin', 'pct', '%s/%s' % (PRO18, REV18)),
    O('Profit wanted at the profit target', 'money', '{set:profit_target}*%s' % REV18),
    O('Closing cash after 12 months (draw and tax set-aside taken)', 'money', 'INDEX({range:cash.closing},MATCH(MAX({range:cash.month}),{range:cash.month},0))+%s-12*{set:owner_draw}-MAX(0,%s)*{set:tax_set_aside_pct}' % (PRO18, PRO18)),
    O('Verdict', 'text', 'IF(%s/%s>={set:profit_target},%s,%s)' % (PRO18, REV18, vd('Meets the profit target'), vd('Below the target')))],
    GR('What if', ('Best case', {'sc': '=' + tok('scen', 'Best')}), ('Worst case', {'sc': '=' + tok('scen', 'Worst')}), ('Cost growth of 8%', {'cg': 0.08}), ('Fees 5% higher', {'ch': 127}), ('Worst case, costs up 8%', {'sc': '=' + tok('scen', 'Worst'), 'cg': 0.08}))))

assert len(tools) == 18, len(tools)
