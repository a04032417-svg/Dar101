"""Home care agency suite part 8: the 18 decision tools."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hc8_lists import *
import hc8_data as D
from hc8_tables import TG, PTS, LIGHT, HM, M0, M1, WPM, PNM
WH1_ = PNM('weekly_hours')

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, d): return IN(k, label, 'list', key(lst, d), list=lst)
O = OUT
H = D.HEALTH_NOW; RUN_NEXT = round([p for p in D.PAYRUNS if p['pay_date'] >= D.TODAY.isoformat()][0]['est_cost'] * (1 + D.BURDEN), 0)
MOVED_YEAR = round(sum(v for m, v in D.SETASIDE.items() if m[:4] == str(D.TODAY.year) and m < D.M0 and [t for t in D.TAX if t['month'] == m][0]['status'] == 'Moved'), 0)
PRIV, PAYER = int(round(D.PRIV_W, -1)), int(round(D.PAYER_W, -1))
TAXM = int(round(D.PROFIT3 * TAX_SET_ASIDE_PCT, -1)); OVH = int(round(D.LAST_OVH)); MPH = round(D.LAST_MPH, 2); RPH = round(D.LAST_RPH, 2); HRS = int(round(D.LAST_HOURS))
LASTPROFIT = int(round(D.PROFIT[D.M1])); REVLAST = int(round(D.LAST['revenue']))
GROWTH = round((D.LAST_HOURS - [r['billed_hours'] for r in D.PNL if r['month'] == month_start(7).isoformat()][0] / (52 / 12)) / 6, 1)
WEEKLY_PAY = int(round(D.CASH[-2]['pay_runs'] * 12 / 52)); WEEKLY_OVH = int(round(D.LAST_OVH * 12 / 52))
BASE, BEST, WORST = tok('scen', 'Base'), tok('scen', 'Best'), tok('scen', 'Worst')

# ---- 13-week closed form (weekly receipts, a pay run every second week, monthly overhead, draw and tax spread evenly)
F_ = 'CHOOSE({in:sc},1,1.04,0.87)'; RF_ = 'CHOOSE({in:sc},1,1,1.03)'; OUT_ = '(({in:ovh}+{in:draw}+{in:tax})*12/52)'
def CL(k): return '({in:cash}+%d*({in:priv}*%s-%s)+{in:payer}*%s*MAX(0,%d-ROUNDUP({in:delay}/7,0))-{in:run}*%s*%d)' % (k, F_, OUT_, F_, k, RF_, (k + 1) // 2)
ALLCL = ','.join(CL(k) for k in range(1, 14))
def CD(k, d): return '({in:cash}+%d*({in:priv}-%s)+{in:payer}*MAX(0,%d-ROUNDUP(%d/7,0))-{in:run}*%d)' % (k, OUT_, k, d, (k + 1) // 2)
def LOWD(d): return 'MIN(%s)' % ','.join(CD(k, d) for k in range(1, 14))
def UNDERD(d): return '+'.join('IF(%s<{set:cash_floor},1,0)' % CD(k, d) for k in range(1, 14))
FRC = lambda col, sc, extra='': 'SUMIFS({range:forecast.%s},{range:forecast.scenario},%s%s)' % (col, sc, extra)
LOWF = FRC('closing', '{in:sc}', ',{range:forecast.rank_low},1')

# ---- health
def HP(k, v): return PTS(v, tok('meas', HM[k]))
INK = {'margin_hour': 'margin', 'overtime_share': 'ot', 'fill_rate': 'fill', 'days_to_pay': 'days', 'turnover_rate': 'turn', 'cover_weeks': 'cover'}
SCORE_IN = '(%s)/%s' % ('+'.join('%s*%s' % (TG(tok('meas', HM[k]), 'Weight'), HP(k, '{in:%s}' % INK[k])) for k in HM), 'SUMIFS({range:targets.value},{range:targets.level},%s)' % tok('lvl', 'Weight'))
MIN6 = 'MIN(%s)' % ','.join(HP(k, '{in:%s}' % INK[k]) for k in HM)
DIR = {'margin_hour': 1, 'overtime_share': -1, 'fill_rate': 1, 'days_to_pay': -1, 'turnover_rate': -1, 'cover_weeks': 1}
def AVG3(k): return 'AVERAGEIFS({range:health.%s},{range:health.month},">="&EDATE(%s,-3),{range:health.month},"<"&%s)' % (k, M0, M0)
def LYV(k): return 'SUMIFS({range:health.%s},{range:health.month},EDATE(%s,-12))' % (k, M0)
def SLIP(k): return '(%d*({in:%s}/%s-1))' % (DIR[k], INK[k], AVG3(k))
MINS = 'MIN(%s)' % ','.join(SLIP(k) for k in HM)
SLIPNAME = 'CHOOSE(MOD(MIN(%s),10),%s)' % (','.join('INT(%s*10000)*10+%d' % (SLIP(k), i + 1) for i, k in enumerate(HM)), ','.join(tok('meas', HM[k]) for k in HM))
PCT = lambda k, ref: 'IFERROR(({in:%s}-%s)/%s,0)' % (INK[k], ref, ref)
HIN = lambda: [I('margin', 'Gross margin per hour', H['margin'], 'num'), I('ot', 'Overtime share of hours', H['overtime_share'], 'pct'), I('fill', 'Fill rate', H['fill_rate'], 'pct'),
               I('days', 'Days to be paid', H['days_to_pay'], 'num'), I('turn', 'Caregiver turnover, last 12 months', H['turnover_rate'], 'pct'), I('cover', 'Weeks of cash cover', H['cover_weeks'], 'num')]
VSC = 'CHOOSE(MIN(2,MAX(0,INT(({s}-{set:health_watch_score})/({set:health_healthy_score}-{set:health_watch_score}))+1))+1,%s,%s,%s)' % (vd('Act'), vd('Watch'), vd('Healthy'))
KEY6 = ','.join('INT(%s*100)*10+%d' % (HP(k, '{in:%s}' % INK[k]), i + 1) for i, k in enumerate(HM))
WORST_IN = 'CHOOSE(MOD(MIN(%s),10),%s)' % (KEY6, ','.join(tok('meas', HM[k]) for k in HM))

tools = [
 TOOL('health_now', 'Is the Agency Healthy', 'Is the agency healthy? One score, six lights',
  'Type this month\'s six measures; each is scored against Health Targets, one score from 0 to 100 gives Healthy, Watch or Act, and the worst item comes first.', HIN(),
  [O('Points: Gross margin per hour', 'num', HP('margin_hour', '{in:margin}')), O('Points: Overtime share', 'num', HP('overtime_share', '{in:ot}')), O('Points: Fill rate', 'num', HP('fill_rate', '{in:fill}')),
   O('Points: Days to be paid', 'num', HP('days_to_pay', '{in:days}')), O('Points: Caregiver turnover', 'num', HP('turnover_rate', '{in:turn}')), O('Points: Weeks of cash cover', 'num', HP('cover_weeks', '{in:cover}')),
   O('Light: Gross margin per hour', 'text', LIGHT('{in:margin}', tok('meas', HM['margin_hour']))), O('Light: Weeks of cash cover', 'text', LIGHT('{in:cover}', tok('meas', HM['cover_weeks']))),
   O('Health score, 0 to 100', 'num', 'ROUND(%s,1)' % SCORE_IN), O('Worst item, lowest points', 'text', WORST_IN),
   O('Lowest points', 'num', MIN6), O('Health score in the history, this month', 'num', 'SUMIFS({range:health.score},{range:health.latest},1)'),
   O('Verdict', 'text', VSC.replace('{s}', '(%s)' % SCORE_IN))],
  GR('What if', ('Margin per hour 13.00', {'margin': 13.0}), ('Overtime share 6 percent', {'ot': 0.06}), ('Fill rate 93 percent', {'fill': 0.93}), ('Cash cover 6 weeks', {'cover': 6}), ('Cash cover 1.5 weeks', {'cover': 1.5}), ('Turnover 40 percent', {'turn': 0.4}))),
 TOOL('health_history', 'Health Against History', 'Health against your own history: this month, 3 months, last year',
  'Type this month\'s six measures; each is compared with the average of the last three full months and with the same month last year, and the measure that slipped most is named.', HIN(),
  [O('Gross margin per hour: 3-month average', 'num', AVG3('margin_hour')), O('Gross margin per hour: change vs 3 months', 'pct', PCT('margin_hour', AVG3('margin_hour'))), O('Gross margin per hour: change vs last year', 'pct', PCT('margin_hour', LYV('margin_hour'))),
   O('Overtime share: 3-month average', 'pct', AVG3('overtime_share')), O('Overtime share: change vs 3 months', 'pct', PCT('overtime_share', AVG3('overtime_share'))), O('Overtime share: change vs last year', 'pct', PCT('overtime_share', LYV('overtime_share'))),
   O('Fill rate: 3-month average', 'pct', AVG3('fill_rate')), O('Fill rate: change vs 3 months', 'pct', PCT('fill_rate', AVG3('fill_rate'))),
   O('Days to be paid: 3-month average', 'num', AVG3('days_to_pay')), O('Days to be paid: change vs 3 months', 'pct', PCT('days_to_pay', AVG3('days_to_pay'))), O('Days to be paid: change vs last year', 'pct', PCT('days_to_pay', LYV('days_to_pay'))),
   O('Caregiver turnover: 3-month average', 'pct', AVG3('turnover_rate')), O('Caregiver turnover: change vs last year', 'pct', PCT('turnover_rate', LYV('turnover_rate'))),
   O('Weeks of cash cover: 3-month average', 'num', AVG3('cover_weeks')), O('Weeks of cash cover: change vs 3 months', 'pct', PCT('cover_weeks', AVG3('cover_weeks'))), O('Weeks of cash cover: change vs last year', 'pct', PCT('cover_weeks', LYV('cover_weeks'))),
   O('Slipped most against 3 months', 'text', SLIPNAME), O('Slip of that measure, direction adjusted', 'pct', MINS),
   O('Verdict', 'text', 'IF(%s<-0.1,%s,IF(%s<0,%s,%s))' % (MINS, vd('Act'), MINS, vd('Watch'), vd('Healthy')))],
  GR('What if', ('Overtime share 3 percent', {'ot': 0.03}), ('Days to be paid 18', {'days': 18}), ('Cash cover 2 weeks', {'cover': 2}), ('Margin per hour 11.00', {'margin': 11.0}), ('Turnover 30 percent', {'turn': 0.3}))),
 TOOL('cash_planner', '13-Week Cash Planner', '13-week cash forecast with a Base, Best or Worst switch',
  'Type cash now, weekly receipts, the pay run (every second week), monthly overhead, draw and tax, a scenario (1 Base, 2 Best, 3 Worst) and the days payers pay later; see 13 closing balances and the verdict against the floor.', [
  I('cash', 'Cash now', int(round(D.CASH_NOW)), 'money'), I('priv', 'Private pay receipts a week', PRIV, 'money'), I('payer', 'Payer receipts a week', PAYER, 'money'), I('run', 'Pay run with payroll burden, every second week', int(RUN_NEXT), 'money'),
  I('ovh', 'Overhead a month', OVH, 'money'), I('draw', 'Owner draw a month', int(OWNER_DRAW), 'money'), I('tax', 'Tax set-aside a month (confirm with your adviser)', TAXM, 'money'), I('sc', 'Scenario: 1 Base, 2 Best, 3 Worst', 1),
  I('delay', 'Days payers pay later than usual', 0)],
  [O('Closing balance, week %d' % k, 'money', CL(k)) for k in range(1, 14)] + [O('Lowest closing balance', 'money', 'MIN(%s)' % ALLCL), O('Weeks below the cash floor', 'int', '+'.join('IF(%s<{set:cash_floor},1,0)' % CL(k) for k in range(1, 14))),
   O('Credit needed to stay at the floor', 'money', 'MAX(0,{set:cash_floor}-MIN(%s))' % ALLCL), O('Verdict against the floor', 'text', 'IF(MIN(%s)>={set:cash_floor},%s,%s)' % (ALLCL, vd('Cash stays above the floor'), vd('Arrange credit'))),
   O('Cash floor', 'money', '{set:cash_floor}')],
  GR('What if', ('Worst case', {'sc': 3}), ('Best case', {'sc': 2}), ('Payers 15 days later', {'delay': 15}), ('Payers 30 days later', {'delay': 30}), ('Cash now 60,000', {'cash': 60000}), ('Pay run 46,000', {'run': 46000}), ('Owner draw 12,000', {'draw': 12000}))),
 TOOL('lowest_week', 'Lowest Cash Week', 'Lowest cash week and the credit needed, from the forecast',
  'Choose a scenario and the weeks you need to arrange credit; the 13-Week Cash Forecast gives the lowest week, the shortfall against the floor, the credit or draw to ask for and the date to arrange it.', [
  IL('sc', 'Scenario', 'scen', 'Worst'), I('lead', 'Weeks needed to arrange credit', 3), I('buffer', 'Safety buffer above the floor', 5000, 'money')],
  [O('Lowest closing balance', 'money', LOWF), O('Week number of the lowest balance', 'int', FRC('week_no', '{in:sc}', ',{range:forecast.rank_low},1')), O('That week starts', 'date', FRC('starts_on', '{in:sc}', ',{range:forecast.rank_low},1')),
   O('Cash floor', 'money', '{set:cash_floor}'), O('Shortfall against the floor', 'money', 'MAX(0,{set:cash_floor}-%s)' % LOWF),
   O('Credit or draw needed, with the buffer', 'money', 'IF({set:cash_floor}>%s,ROUNDUP(({set:cash_floor}-%s+{in:buffer})/1000,0)*1000,0)' % (LOWF, LOWF)),
   O('Arrange it by', 'date', '%s-7*{in:lead}' % FRC('starts_on', '{in:sc}', ',{range:forecast.rank_low},1')),
   O('Weeks under the floor', 'int', 'COUNTIFS({range:forecast.scenario},{in:sc},{range:forecast.closing},"<"&{set:cash_floor})'), O('Closing balance, week 13', 'money', FRC('closing', '{in:sc}', ',{range:forecast.week_no},13')),
   O('Verdict', 'text', 'IF({set:cash_floor}>%s,%s,%s)' % (LOWF, vd('Arrange credit'), vd('Cash stays above the floor')))],
  GR('Scenario', ('Base', {'sc': '=' + BASE}), ('Best', {'sc': '=' + BEST}), ('Worst', {'sc': '=' + WORST}), ('Worst, 5 weeks to arrange', {'sc': '=' + WORST, 'lead': 5}), ('Worst, buffer 10,000', {'sc': '=' + WORST, 'buffer': 10000}))),
 TOOL('payer_later', 'Payer Pays Later', 'Payer pays later: lowest cash at 0, 7, 15, 30 and 45 days',
  'Type cash now and the weekly flows; the same 13 weeks run five times with payers paying 0, 7, 15, 30 and 45 days later, showing the lowest cash, the weeks under the floor and the credit needed for each step.', [
  I('cash', 'Cash now', int(round(D.CASH_NOW)), 'money'), I('priv', 'Private pay receipts a week', PRIV, 'money'), I('payer', 'Payer receipts a week', PAYER, 'money'), I('run', 'Pay run with payroll burden, every second week', int(RUN_NEXT), 'money'),
  I('ovh', 'Overhead a month', OVH, 'money'), I('draw', 'Owner draw a month', int(OWNER_DRAW), 'money'), I('tax', 'Tax set-aside a month (confirm with your adviser)', TAXM, 'money')],
  [O('Lowest cash, paid on time', 'money', LOWD(0)), O('Lowest cash, 7 days later', 'money', LOWD(7)), O('Lowest cash, 15 days later', 'money', LOWD(15)), O('Lowest cash, 30 days later', 'money', LOWD(30)), O('Lowest cash, 45 days later', 'money', LOWD(45)),
   O('Weeks under the floor, 15 days later', 'int', UNDERD(15)), O('Weeks under the floor, 30 days later', 'int', UNDERD(30)), O('Weeks under the floor, 45 days later', 'int', UNDERD(45)),
   O('Credit needed, 15 days later', 'money', 'MAX(0,{set:cash_floor}-%s)' % LOWD(15)), O('Credit needed, 30 days later', 'money', 'MAX(0,{set:cash_floor}-%s)' % LOWD(30)), O('Credit needed, 45 days later', 'money', 'MAX(0,{set:cash_floor}-%s)' % LOWD(45)),
   O('Cash lost at the low point, 45 days later', 'money', '%s-%s' % (LOWD(0), LOWD(45))), O('Verdict at 45 days later', 'text', 'IF(%s>={set:cash_floor},%s,%s)' % (LOWD(45), vd('Cash stays above the floor'), vd('Arrange credit')))],
  GR('What if', ('Cash now 60,000', {'cash': 60000}), ('Payer receipts a week 12,000', {'payer': 12000}), ('Pay run 46,000', {'run': 46000}), ('Cash now 45,000, payers 12,000', {'cash': 45000, 'payer': 12000}), ('Owner draw 12,000', {'draw': 12000}))),
 TOOL('safe_draw', 'Safe Owner Draw', 'Safe owner draw this month: take it, take less or wait',
  'Type last month\'s profit, cash now, what comes in and goes out before the month ends and the draw you plan; the tax set-aside comes off first, and the largest draw that keeps cash above the floor is given with a verdict.', [
  I('profit', 'Profit of the last full month', LASTPROFIT, 'money'), I('cash', 'Cash now', int(round(D.CASH_NOW)), 'money'), I('inflow', 'Receipts expected before the month ends', 61000, 'money'), I('runs', 'Pay runs before the month ends', int(round(RUN_NEXT * 2 - 400)), 'money'),
  I('bills', 'Other bills before the month ends', 25700, 'money'), I('plan', 'Draw you plan to take', int(OWNER_DRAW), 'money')],
  [O('Tax set-aside first (confirm with your adviser)', 'money', 'ROUND({in:profit}*{set:tax_set_aside_pct},0)'), O('Profit after the set-aside', 'money', '{in:profit}-ROUND({in:profit}*{set:tax_set_aside_pct},0)'),
   O('Cash above the floor at month end, before any draw', 'money', '{in:cash}+{in:inflow}-{in:runs}-{in:bills}-{set:cash_floor}'),
   O('Largest safe draw', 'money', 'MAX(0,ROUNDDOWN(MIN({in:profit}-ROUND({in:profit}*{set:tax_set_aside_pct},0),{in:cash}+{in:inflow}-{in:runs}-{in:bills}-{set:cash_floor})/100,0)*100)'),
   O('Cash above the floor after the planned draw', 'money', '{in:cash}+{in:inflow}-{in:runs}-{in:bills}-{set:cash_floor}-{in:plan}'), O('Safe draw in Cash Months this month', 'money', 'SUMIFS({range:cash.safe_draw},{range:cash.latest},1)'),
   O('Verdict', 'text', 'IF(MAX(0,ROUNDDOWN(MIN({in:profit}-ROUND({in:profit}*{set:tax_set_aside_pct},0),{in:cash}+{in:inflow}-{in:runs}-{in:bills}-{set:cash_floor})/100,0)*100)>={in:plan},%s,IF(MAX(0,ROUNDDOWN(MIN({in:profit}-ROUND({in:profit}*{set:tax_set_aside_pct},0),{in:cash}+{in:inflow}-{in:runs}-{in:bills}-{set:cash_floor})/100,0)*100)>0,%s,%s))' % (vd('Take it'), vd('Take less'), vd('Wait')))],
  GR('What if', ('Cash now 60,000', {'cash': 60000}), ('Receipts only 40,000', {'inflow': 40000}), ('Plan a draw of 12,000', {'plan': 12000}), ('Pay runs 90,000', {'runs': 90000}), ('Weak month: profit 6,000', {'profit': 6000}))),
 TOOL('tax_move', 'Tax Set-Aside Planner', 'Tax set-aside: the amount to move now (confirm with your adviser)',
  'Type this month\'s profit, the set-aside share, what is already set aside this year and cash now; see the amount to move, the cash after the move and a verdict. Confirm the rate and the amounts with your adviser.', [
  I('profit', 'Profit of the month', LASTPROFIT, 'money'), I('rate', 'Set-aside share of profit', TAX_SET_ASIDE_PCT, 'pct'), I('sofar', 'Set aside so far this year', int(MOVED_YEAR), 'money'), I('cash', 'Cash now', int(round(D.CASH_NOW)), 'money')],
  [O('Amount to move', 'money', 'ROUND(MAX(0,{in:profit}*{in:rate}),0)'), O('Set aside after the move', 'money', '{in:sofar}+ROUND(MAX(0,{in:profit}*{in:rate}),0)'), O('Cash after the move', 'money', '{in:cash}-ROUND(MAX(0,{in:profit}*{in:rate}),0)'),
   O('Cash above the floor after the move', 'money', '{in:cash}-ROUND(MAX(0,{in:profit}*{in:rate}),0)-{set:cash_floor}'), O('Most you can move now and keep the floor', 'money', 'MAX(0,MIN(ROUND(MAX(0,{in:profit}*{in:rate}),0),{in:cash}-{set:cash_floor}))'),
   O('Due this month in Tax Set-Aside', 'money', 'SUMIFS({range:tax.set_aside},{range:tax.status},%s)' % tok('taxst', 'Due')),
   O('Verdict', 'text', 'IF({in:profit}*{in:rate}<=0,%s,IF({in:cash}-ROUND({in:profit}*{in:rate},0)>={set:cash_floor},%s,%s))' % (vd('Not yet'), vd('Move it now'), vd('Move part now')))],
  GR('What if', ('Profit 6,000', {'profit': 6000}), ('Share 30 percent', {'rate': 0.3}), ('Cash now 40,000', {'cash': 40000}), ('Loss month', {'profit': -2000}), ('Cash now 36,000', {'cash': 36000}))),
 TOOL('hours_target', 'Hours Target Planner', 'Hours target: weekly hours needed for overhead and the owner draw',
  'Type overhead, the owner draw, margin per hour, current weekly hours and the average hours per caregiver; see the weekly hours needed, the gap, the caregivers to add and the distance to the 1,000-hour marker.', [
  I('ovh', 'Overhead a month', OVH, 'money'), I('draw', 'Owner draw a month', int(OWNER_DRAW), 'money'), I('mph', 'Gross margin per hour', MPH, 'num'), I('hours', 'Weekly hours now', HRS), I('per', 'Average weekly hours per caregiver', 24, 'num')],
  [O('Weekly hours needed', 'int', 'ROUND(({in:ovh}+{in:draw})/(%s*{in:mph}),0)' % WPM), O('Gap in weekly hours (plus is short)', 'int', 'ROUND(({in:ovh}+{in:draw})/(%s*{in:mph}),0)-{in:hours}' % WPM),
   O('Caregivers to add', 'int', 'MAX(0,ROUNDUP((ROUND(({in:ovh}+{in:draw})/(%s*{in:mph}),0)-{in:hours})/{in:per},0))' % WPM), O('Profit a month after the draw, at current hours', 'money', 'ROUND({in:hours}*%s*{in:mph}-{in:ovh}-{in:draw},0)' % WPM),
   O('Office help marker, weekly hours', 'int', '{set:office_help_hours}'), O('Hours to the marker', 'int', 'MAX(0,{set:office_help_hours}-{in:hours})'),
   O('Caregivers needed for the marker', 'int', 'MAX(0,ROUNDUP(({set:office_help_hours}-{in:hours})/{in:per},0))'),
   O('Weekly hours needed in the last month of Profit and Loss', 'int', 'ROUND((%s+{set:owner_draw})/(%s*%s),0)' % (PNM('overhead'), WPM, PNM('margin_hour'))),
   O('Verdict', 'text', 'IF(ROUND(({in:ovh}+{in:draw})/(%s*{in:mph}),0)<={in:hours},%s,%s)' % (WPM, vd('On track'), vd('Behind')))],
  GR('What if', ('Draw 12,500', {'draw': 12500}), ('Draw 15,000', {'draw': 15000}), ('Overhead 37,000 with a scheduler', {'ovh': 37000}), ('Margin per hour 11.50', {'mph': 11.5}), ('Hours fall to 780', {'hours': 780}))),
 TOOL('office_help', 'Office Help Marker', 'Office help marker: when to hire a scheduler',
  'Type weekly hours now, the hours you add each month, the cost of office help and margin per hour; see the months until the 1,000-hour marker, the cost and the verdict. A one-person agency does not need it yet.', [
  I('hours', 'Weekly hours now', HRS), I('growth', 'Weekly hours added each month', GROWTH, 'num'), I('salary', 'Monthly pay of office help', 4200, 'money'), I('mph', 'Gross margin per hour', MPH, 'num')],
  [O('Office help marker, weekly hours', 'int', '{set:office_help_hours}'), O('Hours to the marker', 'int', 'MAX(0,{set:office_help_hours}-{in:hours})'),
   O('Months until the marker', 'int', 'IF({in:hours}>={set:office_help_hours},0,IF({in:growth}>0,ROUNDUP(({set:office_help_hours}-{in:hours})/{in:growth},0),99))'),
   O('Date the marker is reached', 'date', 'EDATE({today},IF({in:hours}>={set:office_help_hours},0,IF({in:growth}>0,ROUNDUP(({set:office_help_hours}-{in:hours})/{in:growth},0),99)))'),
   O('Cost of office help a month, with burden', 'money', '{in:salary}*(1+{set:payroll_burden})'), O('Margin a month from the hours still to add', 'money', 'MAX(0,{set:office_help_hours}-{in:hours})*%s*{in:mph}' % WPM),
   O('Weekly hours that pay for office help', 'int', 'ROUNDUP({in:salary}*(1+{set:payroll_burden})/(%s*{in:mph}),0)' % WPM), O('Months until the marker, from Profit and Loss', 'int', 'SUMIFS({range:pnl.months_to_marker},{range:pnl.month},%s)' % M1),
   O('Verdict', 'text', 'IF({in:hours}>={set:office_help_hours},%s,IF(IF({in:hours}>={set:office_help_hours},0,IF({in:growth}>0,ROUNDUP(({set:office_help_hours}-{in:hours})/{in:growth},0),99))<=3,%s,%s))' % (vd('Hire office help now'), vd('Plan it'), vd('Not yet')))],
  GR('What if', ('Growth 40 hours a month', {'growth': 40}), ('Hours now 960', {'hours': 960, 'growth': 25}), ('Hours now 1,010', {'hours': 1010}), ('No growth', {'growth': 0}), ('Cheaper office help 3,000', {'salary': 3000}))),
 TOOL('breakeven', 'Break-Even Hours', 'Break-even weekly hours at your margin and overhead',
  'Type overhead, margin per hour, revenue per hour and weekly hours now; see the break-even weekly hours, the margin of safety, the profit a month and the hours that reach your profit target.', [
  I('ovh', 'Overhead a month', OVH, 'money'), I('mph', 'Gross margin per hour', MPH, 'num'), I('rph', 'Revenue per billed hour', RPH, 'num'), I('hours', 'Weekly hours now', HRS), I('wpm', 'Weeks in a month', 4.33, 'num')],
  [O('Break-even weekly hours', 'int', 'ROUNDUP({in:ovh}/({in:wpm}*{in:mph}),0)'), O('Margin of safety, hours', 'int', '{in:hours}-ROUNDUP({in:ovh}/({in:wpm}*{in:mph}),0)'), O('Margin of safety', 'pct', '({in:hours}-{in:ovh}/({in:wpm}*{in:mph}))/{in:hours}'),
   O('Profit a month at current hours', 'money', 'ROUND({in:hours}*{in:wpm}*{in:mph}-{in:ovh},0)'), O('Profit share of revenue', 'pct', '({in:hours}*{in:wpm}*{in:mph}-{in:ovh})/({in:hours}*{in:wpm}*{in:rph})'),
   O('Weekly hours for the profit target', 'int', 'IF({in:mph}>{set:profit_target}*{in:rph},ROUNDUP({in:ovh}/({in:wpm}*({in:mph}-{set:profit_target}*{in:rph})),0),0)'), O('Break-even hours in Profit and Loss, last month', 'int', 'ROUND(SUMIFS({range:pnl.breakeven_hours},{range:pnl.month},%s),0)' % M1),
   O('Verdict', 'text', 'IF({in:hours}>ROUNDUP({in:ovh}/({in:wpm}*{in:mph}),0),%s,%s)' % (vd('Above break-even'), vd('Below break-even')))],
  GR('What if', ('Hours fall to 700', {'hours': 700}), ('Overhead 37,000', {'ovh': 37000}), ('Margin per hour 11.00', {'mph': 11.0}), ('Overhead 45,000, margin 11', {'ovh': 45000, 'mph': 11.0}), ('Hours grow to 950', {'hours': 950}))),
 TOOL('overhead_check', 'Overhead Share Check', 'Overhead share check against the target share',
  'Type overhead and revenue for a month and the target share; see the share, the gap in money, the revenue that would bring the share to the target and the extra weekly hours it needs.', [
  I('ovh', 'Overhead', OVH, 'money'), I('rev', 'Revenue', REVLAST, 'money'), I('target', 'Target share of revenue', 0.26, 'pct'), I('rph', 'Revenue per billed hour', RPH, 'num')],
  [O('Overhead share of revenue', 'pct', '{in:ovh}/{in:rev}'), O('Target share', 'pct', '{in:target}'), O('Overhead at the target share', 'money', '{in:rev}*{in:target}'), O('Gap in money (plus is above the target)', 'money', '{in:ovh}-{in:rev}*{in:target}'),
   O('Revenue needed to reach the target share', 'money', '{in:ovh}/{in:target}'), O('Extra weekly hours needed', 'int', 'MAX(0,ROUNDUP(({in:ovh}/{in:target}-{in:rev})/({in:rph}*%s),0))' % WPM),
   O('Average share, last 3 full months', 'pct', 'AVERAGEIFS({range:overhead.share_of_revenue},{range:overhead.month},">="&EDATE(%s,-3),{range:overhead.month},"<"&%s)' % (M0, M0)),
   O('Verdict', 'text', 'IF({in:ovh}/{in:rev}<={in:target},%s,%s)' % (vd('Overhead within target'), vd('Overhead above target')))],
  GR('What if', ('Overhead 37,000', {'ovh': 37000}), ('Revenue falls to 110,000', {'rev': 110000}), ('Target 22 percent', {'target': 0.22}), ('Overhead 29,000', {'ovh': 29000}), ('Revenue grows to 150,000', {'rev': 150000}))),
 TOOL('rate_rise', 'Rate Rise Scenario', 'Rate rise scenario: raise or hold',
  'Type the rate rise, the share of hours you could lose, margin and revenue per hour, weekly hours and overhead; see the profit before and after, the break-even hours lost and the verdict.', [
  I('rise', 'Rate rise', 0.03, 'pct'), I('lost', 'Hours lost after the rise', 0.02, 'pct'), I('mph', 'Gross margin per hour', MPH, 'num'), I('rph', 'Revenue per billed hour', RPH, 'num'), I('hours', 'Weekly hours now', HRS), I('ovh', 'Overhead a month', OVH, 'money')],
  [O('Profit a month before', 'money', 'ROUND({in:hours}*%s*{in:mph}-{in:ovh},0)' % WPM), O('Margin per hour after the rise', 'num', '{in:mph}+{in:rph}*{in:rise}'), O('Weekly hours after', 'int', 'ROUND({in:hours}*(1-{in:lost}),0)'),
   O('Profit a month after', 'money', 'ROUND({in:hours}*(1-{in:lost})*%s*({in:mph}+{in:rph}*{in:rise})-{in:ovh},0)' % WPM), O('Change in profit a month', 'money', 'ROUND({in:hours}*(1-{in:lost})*%s*({in:mph}+{in:rph}*{in:rise})-{in:hours}*%s*{in:mph},0)' % (WPM, WPM)),
   O('Change in profit a year', 'money', 'ROUND(12*({in:hours}*(1-{in:lost})*%s*({in:mph}+{in:rph}*{in:rise})-{in:hours}*%s*{in:mph}),0)' % (WPM, WPM)), O('Most hours you can lose before the rise stops paying', 'pct', '{in:rph}*{in:rise}/({in:mph}+{in:rph}*{in:rise})'),
   O('Break-even weekly hours after', 'int', 'ROUNDUP({in:ovh}/(%s*({in:mph}+{in:rph}*{in:rise})),0)' % WPM),
   O('Verdict', 'text', 'IF({in:hours}*(1-{in:lost})*({in:mph}+{in:rph}*{in:rise})>={in:hours}*{in:mph},%s,%s)' % (vd('Raise'), vd('Hold')))],
  GR('What if', ('Rise 5 percent, lose 6 percent', {'rise': 0.05, 'lost': 0.06}), ('Rise 2 percent, lose 0', {'rise': 0.02, 'lost': 0}), ('Rise 3 percent, lose 10 percent', {'rise': 0.03, 'lost': 0.1}), ('Rise 4 percent, lose 3 percent', {'rise': 0.04, 'lost': 0.03}), ('Rise 1 percent, lose 3 percent', {'rise': 0.01, 'lost': 0.03}))),
 TOOL('drop_client', 'Weakest Client Scenario', 'Lose the weakest client: release or keep',
  'Type the client\'s weekly hours, their margin per hour (below zero when billed below cost), the share of the freed hours you expect to replace and the agency margin; see the profit change and the verdict.', [
  I('hours', 'Client weekly hours', 12), I('cm', 'Client margin per hour', round(story()['below_cost_rate'] - story()['below_cost_cost_per_hour'], 2), 'num'), I('repl', 'Share of the freed hours replaced', 0.5, 'pct'), I('mph', 'Agency margin per hour', MPH, 'num'), I('travel', 'Travel and set-up cost a month the client adds', 40, 'money')],
  [O('Client margin a month', 'money', '{in:hours}*%s*{in:cm}-{in:travel}' % WPM), O('Margin a month from the hours you replace', 'money', '{in:hours}*{in:repl}*%s*{in:mph}' % WPM), O('Change in profit a month if released', 'money', 'ROUND(-({in:hours}*%s*{in:cm}-{in:travel})+{in:hours}*{in:repl}*%s*{in:mph},0)' % (WPM, WPM)),
   O('Change in profit a year', 'money', 'ROUND(12*(-({in:hours}*%s*{in:cm}-{in:travel})+{in:hours}*{in:repl}*%s*{in:mph}),0)' % (WPM, WPM)), O('Share of the hours to replace to break even', 'pct', 'IF({in:hours}*%s*{in:mph}>0,MAX(0,({in:hours}*%s*{in:cm}-{in:travel})/({in:hours}*%s*{in:mph})),0)' % (WPM, WPM, WPM)),
   O('Verdict', 'text', 'IF(-({in:hours}*%s*{in:cm}-{in:travel})+{in:hours}*{in:repl}*%s*{in:mph}>0,%s,%s)' % (WPM, WPM, vd('Release'), vd('Keep')))],
  GR('What if', ('Nothing replaced', {'repl': 0}), ('Client earns 3 an hour', {'cm': 3.0, 'repl': 0.3}), ('Client earns 3, replace all', {'cm': 3.0, 'repl': 1.0}), ('Client with 20 hours', {'hours': 20}), ('Replace everything', {'repl': 1.0}))),
 TOOL('add_scheduler', 'Add a Scheduler Scenario', 'Add a scheduler: profit change and the hours that pay it back',
  'Type the monthly pay, the burden, the extra weekly hours the scheduler lets you serve, margin per hour and your guess of the savings from fewer errors; see the profit change and the hours that pay it back.', [
  I('salary', 'Monthly pay of the scheduler', 4200, 'money'), I('burden', 'Payroll burden on pay', PAYROLL_BURDEN, 'pct'), I('extra', 'Extra weekly hours served', 40), I('mph', 'Gross margin per hour', MPH, 'num'), I('saving', 'Savings from fewer errors a month (your guess)', 600, 'money')],
  [O('Loaded cost a month', 'money', '{in:salary}*(1+{in:burden})'), O('Margin a month from the extra hours', 'money', '{in:extra}*%s*{in:mph}' % WPM), O('Change in profit a month', 'money', 'ROUND({in:extra}*%s*{in:mph}+{in:saving}-{in:salary}*(1+{in:burden}),0)' % WPM),
   O('Extra weekly hours that pay it back', 'int', 'MAX(0,ROUNDUP(({in:salary}*(1+{in:burden})-{in:saving})/(%s*{in:mph}),0))' % WPM), O('Weekly hours now in Profit and Loss, last month', 'int', 'ROUND(%s,0)' % WH1_),
   O('Weekly hours with the extra hours', 'int', 'ROUND(%s,0)+{in:extra}' % WH1_), O('Share of the marker reached', 'pct', '(%s+{in:extra})/{set:office_help_hours}' % WH1_),
   O('Verdict', 'text', 'IF({in:extra}*%s*{in:mph}+{in:saving}-{in:salary}*(1+{in:burden})>0,%s,%s)' % (WPM, vd('Worth adding'), vd('Not yet')))],
  GR('What if', ('Extra 90 hours', {'extra': 90}), ('Extra 100 hours, saving 1,000', {'extra': 100, 'saving': 1000}), ('Pay 3,500', {'salary': 3500}), ('No savings', {'saving': 0}), ('Extra 60 hours', {'extra': 60}))),
 TOOL('budget_actual', 'Budget Against Actual', 'Budget against actual: three largest overruns',
  'Choose the overrun you accept; the Budget sheet gives the total budget and actual last month, the variance, the three largest overruns and a verdict.', [I('tol', 'Overrun you accept', 0.05, 'pct')],
  [O('Total monthly budget', 'money', 'SUM({range:budget.budget})'), O('Total actual last month', 'money', 'SUM({range:budget.actual_last_month})'), O('Variance (plus is over)', 'money', 'SUM({range:budget.actual_last_month})-SUM({range:budget.budget})'),
   O('Variance share', 'pct', '(SUM({range:budget.actual_last_month})-SUM({range:budget.budget}))/SUM({range:budget.budget})'),
   O('Largest overrun: line', 'text', 'IFERROR(INDEX({range:budget.category},MATCH(LARGE({range:budget.variance},1),{range:budget.variance},0))&"","")'), O('Largest overrun: amount', 'money', 'LARGE({range:budget.variance},1)'),
   O('Second overrun: line', 'text', 'IFERROR(INDEX({range:budget.category},MATCH(LARGE({range:budget.variance},2),{range:budget.variance},0))&"","")'), O('Second overrun: amount', 'money', 'LARGE({range:budget.variance},2)'),
   O('Third overrun: line', 'text', 'IFERROR(INDEX({range:budget.category},MATCH(LARGE({range:budget.variance},3),{range:budget.variance},0))&"","")'), O('Third overrun: amount', 'money', 'LARGE({range:budget.variance},3)'),
   O('Lines over the accepted overrun', 'int', 'COUNTIFS({range:budget.variance_share},">"&{in:tol})'),
   O('Verdict', 'text', 'IF((SUM({range:budget.actual_last_month})-SUM({range:budget.budget}))/SUM({range:budget.budget})>{in:tol},%s,%s)' % (vd('Budget overrun'), vd('Budget on track')))],
  GR('Overrun you accept', ('0 percent', {'tol': 0}), ('2 percent', {'tol': 0.02}), ('5 percent', {'tol': 0.05}), ('10 percent', {'tol': 0.1}), ('20 percent', {'tol': 0.2}))),
 TOOL('cash_cover', 'Cash Weeks of Cover', 'Cash weeks of cover against the target',
  'Type cash, weekly payroll and weekly overhead and the weeks of cover you want; see the weeks of cover, the cash you would need and the verdict.', [
  I('cash', 'Cash now', int(round(D.CASH_NOW)), 'money'), I('pay', 'Payroll a week, with burden', WEEKLY_PAY, 'money'), I('ovh', 'Overhead a week', WEEKLY_OVH, 'money'), I('target', 'Weeks of cover wanted', 4)],
  [O('Cash out a week', 'money', '{in:pay}+{in:ovh}'), O('Weeks of cash cover', 'num', '{in:cash}/({in:pay}+{in:ovh})'), O('Gap to the target, weeks', 'num', '{in:cash}/({in:pay}+{in:ovh})-{in:target}'),
   O('Cash needed for the target', 'money', '{in:target}*({in:pay}+{in:ovh})'), O('Extra cash needed', 'money', 'MAX(0,{in:target}*({in:pay}+{in:ovh})-{in:cash})'), O('Weeks of cover above the floor', 'num', '({in:cash}-{set:cash_floor})/({in:pay}+{in:ovh})'),
   O('Weeks of cash cover in Health Score History', 'num', 'SUMIFS({range:health.cover_weeks},{range:health.latest},1)'), O('Verdict', 'text', 'IF({in:cash}/({in:pay}+{in:ovh})>={in:target},%s,%s)' % (vd('Enough cover'), vd('Build cash')))],
  GR('What if', ('Cash now 120,000', {'cash': 120000}), ('Cash now 60,000', {'cash': 60000}), ('Target 3 weeks', {'target': 3}), ('Payroll grows to 22,000', {'pay': 22000}), ('Target 6 weeks', {'target': 6}))),
 TOOL('startup_mode', 'Start-up Mode', 'Start-up mode: which pages to use and hide',
  'Type your caregivers, clients and weekly hours and whether someone else does the scheduling; Start-up Pages gives the pages to use, the pages to hide and the next page to switch on. A one-person agency can start with 7 pages.', [
  I('cg', 'Caregivers (include yourself if you give care)', 6), I('cl', 'Clients', 9), I('hours', 'Weekly care hours', 150), I('other', 'Someone else does the scheduling: 1 yes, 0 no', 0)],
  [O('Pages a one-person agency uses', 'int', 'COUNTIFS({range:startup.one_person},{list:yesno.yes})'), O('Pages to use at this size', 'int', 'COUNTIFS({range:startup.from_caregivers},"<="&{in:cg})'),
   O('Pages to hide for now', 'int', 'COUNTA({range:startup.page_id})-COUNTIFS({range:startup.from_caregivers},"<="&{in:cg})'),
   O('Next page to switch on', 'text', 'IFERROR(INDEX({range:startup.page},MATCH(SUMPRODUCT(MIN(({range:startup.from_caregivers}>{in:cg})*{range:startup.from_caregivers}+({range:startup.from_caregivers}<={in:cg})*999)),{range:startup.from_caregivers},0))&"",%s)' % vd("Full mode")),
   O('Switch it on at this many caregivers', 'int', 'SUMPRODUCT(MIN(({range:startup.from_caregivers}>{in:cg})*{range:startup.from_caregivers}+({range:startup.from_caregivers}<={in:cg})*999))'),
   O('Hours to the office help marker', 'int', 'MAX(0,{set:office_help_hours}-{in:hours})'), O('Hours per client', 'num', '{in:hours}/{in:cl}'),
   O('Verdict', 'text', 'IF(AND({in:cg}<=8,{in:hours}<{set:office_help_hours}/2,{in:other}=0),%s,%s)' % (vd('Start-up mode'), vd('Full mode')))],
  GR('What if', ('12 caregivers', {'cg': 12, 'hours': 280, 'cl': 20}), ('20 caregivers', {'cg': 20, 'hours': 480, 'cl': 30}), ('38 caregivers', {'cg': 38, 'hours': 860, 'cl': 54}), ('Someone else schedules', {'other': 1}), ('4 caregivers', {'cg': 4, 'hours': 90, 'cl': 6}))),
 TOOL('profit_grid', 'Profit What-if Grid', 'What-if grid: weekly hours against margin per hour',
  'Type overhead, the owner draw, weekly hours and margin per hour; the grid below tries 12 combinations of hours and margin and shows the profit a month in each, before and after the draw.', [
  I('ovh', 'Overhead a month', OVH, 'money'), I('draw', 'Owner draw a month', int(OWNER_DRAW), 'money'), I('hours', 'Weekly hours', HRS), I('mph', 'Gross margin per hour', MPH, 'num')],
  [O('Profit a month before the draw', 'money', 'ROUND({in:hours}*%s*{in:mph}-{in:ovh},0)' % WPM), O('Profit a month after the draw', 'money', 'ROUND({in:hours}*%s*{in:mph}-{in:ovh}-{in:draw},0)' % WPM),
   O('Break-even weekly hours', 'int', 'ROUNDUP({in:ovh}/(%s*{in:mph}),0)' % WPM), O('Weekly hours that also cover the draw', 'int', 'ROUNDUP(({in:ovh}+{in:draw})/(%s*{in:mph}),0)' % WPM),
   O('Profit for each extra 50 weekly hours', 'money', 'ROUND(50*%s*{in:mph},0)' % WPM), O('Profit for each extra 0.50 of margin per hour', 'money', 'ROUND({in:hours}*%s*0.5,0)' % WPM),
   O('Verdict', 'text', 'IF({in:hours}*%s*{in:mph}-{in:ovh}-{in:draw}>0,%s,%s)' % (WPM, vd('Above break-even'), vd('Below break-even')))],
  GR('Hours against margin', *[('Hours %d, margin %.2f' % (h, m), {'hours': h, 'mph': m}) for h in (760, 860, 960, 1060) for m in (11.5, 12.2, 13.0)]))]
assert len(tools) == 18, len(tools)
