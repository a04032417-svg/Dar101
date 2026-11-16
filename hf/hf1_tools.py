"""Household Finance suite part 1: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf1_lists import *
import hf1_data as D
from hf1_tables import R, B0, NP, NP2, UNP, PAYIN, MS, YES, PAID_B, PAID_I, P1, P2, WIND, G_FIX, G_VAR, G_WANT, G_SAVE, G_DEBT, WEEKLY, BIWK, TWICE, UNDER, ABOVE


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, dflt): return IN(k, label, 'list', key(lst, dflt), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def BP(g): return 'SUMIFS(%s,%s,%s,%s,%s)' % (R('budget', 'planned'), R('budget', 'month'), MS, R('budget', 'group'), g)
TH = 'SUMIFS(%s,%s,0)' % (R('pay_rhythm', 'budget_income'), R('pay_rhythm', 'offset'))
BASE0 = 'SUMIFS(%s,%s,0)' % (R('baseline', 'baseline'), R('baseline', 'offset'))
SHORT, TIGHT, SAFE = c1('Short'), c1('Tight'), c1('Safe')
tools = []
_today = TODAY

# window of bills between the next two paydays, to size the default of the paycheck split
_p1 = sorted(r['date'] for r in D.PAY if r['person'] == 'Partner 1' and r['date'] >= iso(_today))
_win = sum(b['amount'] for b in D.BIL if b['status'] != 'Paid' and b['account_id'] == 'AC-01' and _p1[0] <= b['due_date'] < _p1[1])
_SPLIT_SPEND = round(D.PAYCHECK_NET - _win * 0.6 - 192 - 102 - 160)

# 1 ---------------------------------------------------------------- cash low point forecast
MIN60 = 'SUMPRODUCT(MIN(%s+(%s>59)*1000000000))' % (R('forecast', 'closing'), R('forecast', 'day_no'))
FIRST1 = 'SUMPRODUCT(MIN(%s+(%s>59)*1000000000+(%s>={in:floor}-{in:move})*1000000000))' % (R('forecast', 'day_no'), R('forecast', 'day_no'), R('forecast', 'closing'))
LOW1 = '(%s+{in:move})' % MIN60
tools.append(TOOL('cash_forecast_tool', 'Cash Low Point Forecast', 'Will the joint account go under my floor in the next 60 days',
    'Type the money you could move in and your cash floor; the 90-day forecast from today, paydays and unpaid bills gives the lowest balance, its date and the days under the floor.', [
    I('move', 'Money you move in today', 0), I('floor', 'Cash floor to test, your own number', CASH_FLOOR)], [
    O('Joint balance now', 'money', B0), O('Lowest balance in the next 60 days', 'money', LOW1),
    O('Date of the lowest balance', 'date', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (R('forecast', 'date'), MIN60, R('forecast', 'closing'))),
    O('First day under the floor', 'date', 'IF(%s>=1000000,%s,{today}+%s)' % (FIRST1, SAFE, FIRST1)), O('Days until the first day under the floor', 'int', 'IF(%s>=1000000,%s,%s)' % (FIRST1, SAFE, FIRST1)),
    O('Days under the floor in the next 60', 'int', 'COUNTIFS(%s,"<"&({in:floor}-{in:move}),%s,"<=59")' % (R('forecast', 'closing'), R('forecast', 'day_no'))),
    O('Short of the floor at the lowest point', 'money', 'MAX(0,{in:floor}-%s)' % LOW1),
    O('Balance on day 59', 'money', 'IFERROR(INDEX(%s,MATCH(59,%s,0)),0)+{in:move}' % (R('forecast', 'closing'), R('forecast', 'day_no'))),
    O('Verdict', 'text', 'IF(%s<{in:floor},%s,IF(%s<{in:floor}+{set:tight_margin},%s,%s))' % (LOW1, SHORT, LOW1, TIGHT, SAFE))],
    GR('What if', ('Move in 100', {'move': 100}), ('Move in 250', {'move': 250}), ('Move in 400', {'move': 400}), ('Floor 300', {'floor': 300}), ('Floor 800', {'floor': 800}))))

# 2 ---------------------------------------------------------------- low point before each payday
def LK(k): return 'SUMIFS(%s,%s,%d)' % (R('low_point', 'lowest'), R('low_point', 'pn'), k)
def PK(k): return 'SUMIFS(%s,%s,%d)' % (R('low_point', 'payday'), R('low_point', 'pn'), k)
X2 = '({in:floor}-{in:move})'
_f = c2('Safe until payday')
for k in range(6, 0, -1): _f = 'IF(%s<%s,%s,%s)' % (LK(k), X2, PK(k), _f)
CNT2 = 'COUNTIFS(%s,"<"&%s,%s,"<=6")' % (R('low_point', 'lowest'), X2, R('low_point', 'pn'))
MINL = 'MIN(' + ','.join(LK(k) for k in range(1, 7)) + ')'
tools.append(TOOL('low_point_tool', 'Low Point Before Each Payday', 'Is every payday reached above my floor',
    'The next six paydays with the lowest joint balance before each, set against your floor and the money you could move in; the first payday that falls short is named.', [
    I('move', 'Money you move in today', 0), I('floor', 'Cash floor to test, your own number', CASH_FLOOR)], [
    O('Payday 1', 'date', PK(1)), O('Lowest balance before payday 1', 'money', LK(1) + '+{in:move}'), O('Payday 2', 'date', PK(2)), O('Lowest balance before payday 2', 'money', LK(2) + '+{in:move}'),
    O('Payday 3', 'date', PK(3)), O('Lowest balance before payday 3', 'money', LK(3) + '+{in:move}'), O('Payday 4', 'date', PK(4)), O('Lowest balance before payday 4', 'money', LK(4) + '+{in:move}'),
    O('Paydays short of the floor, next 6', 'int', CNT2), O('Lowest balance of the next 6', 'money', MINL + '+{in:move}'), O('First payday that falls short', 'date', _f),
    O('Biggest shortfall', 'money', 'MAX(0,%s-%s)' % (X2, MINL)), O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (CNT2, c2('Safe until payday'), c2('Short before payday')))],
    GR('What if', ('Move in 100', {'move': 100}), ('Move in 300', {'move': 300}), ('Move in 600', {'move': 600}), ('Floor 300', {'floor': 300}), ('Floor 900', {'floor': 900}))))

# 3 ---------------------------------------------------------------- bill that breaks the floor
BD = R('bills_due', 'break_date')
FB = 'IFERROR(SMALL(%s,1),"")' % BD
def BX(c): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('bills_due', c), FB, BD)
LOWNP = 'SUMIFS(%s,%s,1)' % (R('low_point', 'lowest'), R('low_point', 'pn'))
tools.append(TOOL('break_floor_tool', 'Bill That Breaks the Floor', 'Which unpaid bill pushes the joint account under my floor',
    'The first unpaid bill of the joint account that leaves the balance under your cash floor, its balance after, and the amount to move in by the day before it.', [
    I('move', 'Money you could move in today', 0)], [
    O('First bill that breaks the floor', 'text', 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&"","")' % (R('bills_due', 'bill'), FB, BD)), O('Falls due on', 'date', FB), O('Amount of the bill', 'money', BX('amount')),
    O('Balance after the bill', 'money', BX('after')), O('Cash floor', 'money', '{set:cash_floor}'), O('Short of the floor after it', 'money', 'MAX(0,{set:cash_floor}-%s)' % BX('after')),
    O('Lowest balance before the next payday', 'money', LOWNP), O('Move in to stay at the floor until payday', 'money', 'MAX(0,{set:cash_floor}-%s-{in:move})' % LOWNP),
    O('Move the money in by', 'date', 'IF(%s="","",%s-1)' % (FB, FB)), O('Days left to move it', 'int', 'IF(%s="","",%s-1-{today})' % (FB, FB)),
    O('Verdict', 'text', 'IF(OR(%s="",%s+{in:move}>={set:cash_floor}),%s,%s)' % (FB, LOWNP, c2('Fine as it is'), c2('Move money in')))],
    GR('What if', ('Move in 100', {'move': 100}), ('Move in 200', {'move': 200}), ('Move in 300', {'move': 300}), ('Move in 500', {'move': 500}))))

# 4 ---------------------------------------------------------------- paycheck split
WIN4 = 'SUMIFS(%s,%s,"<>"&%s,%s,{set:joint_id},%s,">="&%s,%s,"<"&%s)' % (R('bills_due', 'amount'), R('bills_due', 'status'), PAID_B, R('bills_due', 'account_id'), R('bills_due', 'due_date'), NP, R('bills_due', 'due_date'), NP2)
COV4 = '(%s*{in:share})' % WIN4
TOT4 = '(%s+{in:sinking}+{in:debt}+{in:goals}+{in:spend})' % COV4
LEFT4 = 'IF({in:method}=%s,{in:pay}-%s,{in:pay}*(1-{set:needs_share}-{set:wants_share}-{set:savings_share}))' % (tok('smethod', 'Zero-based'), TOT4)
tools.append(TOOL('split_tool', 'Paycheck Split', 'Is every dollar of this paycheck given a job',
    'Type one paycheck and what goes to sinking funds, debt, goals and spending money; the bills due before the next paycheck are taken from Bills Due and the split ends at zero or shows what is left.', [
    I('pay', 'Take-home of this paycheck', D.PAYCHECK_NET), IL('method', 'Split method', 'smethod', 'Zero-based'), I('share', 'Share of the joint bills this paycheck covers', 0.6, 'pct'),
    I('sinking', 'Sinking funds from this paycheck', 192), I('debt', 'Extra debt payments from this paycheck', 102), I('goals', 'Goals and savings from this paycheck', 160), I('spend', 'Spending money from this paycheck', _SPLIT_SPEND)], [
    O('Bills due between this paycheck and the next', 'money', WIN4), O('Bills this paycheck covers', 'money', COV4), O('Share of the paycheck that goes to bills', 'pct', 'IFERROR(%s/{in:pay},0)' % COV4),
    O('Total given a job, zero-based', 'money', TOT4), O('Needs amount, percentage method', 'money', '{in:pay}*{set:needs_share}'), O('Wants amount, percentage method', 'money', '{in:pay}*{set:wants_share}'),
    O('Savings and debt amount, percentage method', 'money', '{in:pay}*{set:savings_share}'), O('Needs left after the bills, percentage method', 'money', '{in:pay}*{set:needs_share}-%s' % COV4),
    O('Left to assign', 'money', LEFT4),
    O('Verdict', 'text', 'IF(ABS(%s)<={set:tolerance},%s,IF(%s>0,%s,%s))' % (LEFT4, c2('Zero left to assign'), LEFT4, c2('Left to assign'), c2('Over-assigned')))],
    GR('What if', ('Spend 100 less', {'spend': _SPLIT_SPEND - 100}), ('Spend 150 more', {'spend': _SPLIT_SPEND + 150}), ('Cover all the bills', {'share': 1}), ('Percentage method', {'method': '=' + tok('smethod', 'Percentage')}), ('Extra debt 250', {'debt': 250}))))

# 5 ---------------------------------------------------------------- zero-based month check
INC5 = 'IF({in:take}>0,{in:take},%s)' % TH
PL5 = '(%s+%s+%s+%s+%s-{in:cut})' % (BP(G_FIX), BP(G_VAR), BP(G_WANT), BP(G_SAVE), BP(G_DEBT))
LF5 = '(%s-%s)' % (INC5, PL5)
tools.append(TOOL('zero_month_tool', 'Zero-Based Month Check', 'Is every dollar of this month planned',
    'Income minus every planned outgoing: the income you budget (or the amount you type) against the plan lines of this month, with what you could cut from wants to reach zero.', [
    I('take', 'Take-home to budget, 0 uses the income you budget', 0), I('cut', 'Cut from wants to test', 0)], [
    O('Income used', 'money', INC5), O('Planned fixed bills', 'money', BP(G_FIX)), O('Planned variable needs', 'money', BP(G_VAR)), O('Planned wants after the cut', 'money', '%s-{in:cut}' % BP(G_WANT)),
    O('Planned savings', 'money', BP(G_SAVE)), O('Planned debt payments', 'money', BP(G_DEBT)), O('Total planned', 'money', PL5), O('Left to assign', 'money', LF5),
    O('Planned savings and debt share of income', 'pct', 'IFERROR((%s+%s)/%s,0)' % (BP(G_SAVE), BP(G_DEBT), INC5)),
    O('Partner 2 income planned above the baseline by', 'money', '{set:p2_budget}-%s' % BASE0),
    O('Verdict', 'text', 'IF(ABS(%s)<={set:tolerance},%s,IF(%s>0,%s,%s))' % (LF5, c2('Zero left to assign'), LF5, c2('Left to assign'), c2('Over-assigned')))],
    GR('What if', ('Cut 100 from wants', {'cut': 100}), ('Cut 300 from wants', {'cut': 300}), ('Income 8000', {'take': 8000}), ('Income 9000', {'take': 9000}), ('Income 10000', {'take': 10000}))))

# 6 ---------------------------------------------------------------- needs wants savings check
BASE6 = 'IF({in:take}>0,{in:take},%s)' % TH
N6 = '(%s+%s)' % (BP(G_FIX), BP(G_VAR)); W6 = '(%s-{in:move})' % BP(G_WANT); S6 = '(%s+%s+{in:move})' % (BP(G_SAVE), BP(G_DEBT))
tools.append(TOOL('nws_tool', 'Needs Wants Savings Check', 'Are needs, wants and savings within a typical range',
    'Needs, wants and savings with debt as a share of your income against the shares in Settings, a typical range, check your own numbers; move money from wants to savings to test.', [
    I('take', 'Take-home to compare with, 0 uses the income you budget', 0), I('move', 'Move from wants to savings', 0), I('range', 'Points either side that still count as within range', 0.05, 'pct')], [
    O('Income used', 'money', BASE6), O('Needs share', 'pct', 'IFERROR(%s/%s,0)' % (N6, BASE6)), O('Wants share', 'pct', 'IFERROR(%s/%s,0)' % (W6, BASE6)), O('Savings and debt share', 'pct', 'IFERROR(%s/%s,0)' % (S6, BASE6)),
    O('Needs against the typical range, points', 'pct', 'IFERROR(%s/%s,0)-{set:needs_share}' % (N6, BASE6)), O('Wants against the typical range, points', 'pct', 'IFERROR(%s/%s,0)-{set:wants_share}' % (W6, BASE6)),
    O('Savings against the typical range, points', 'pct', 'IFERROR(%s/%s,0)-{set:savings_share}' % (S6, BASE6)), O('Needs amount', 'money', N6), O('Wants amount', 'money', W6), O('Savings and debt amount', 'money', S6),
    O('Move from wants to reach the savings share', 'money', 'MAX(0,{set:savings_share}*%s-%s)' % (BASE6, S6)),
    O('Verdict', 'text', 'IF(%s/%s>{set:needs_share}+{in:range},%s,IF(%s/%s>{set:wants_share}+{in:range},%s,IF(%s/%s<{set:savings_share}-{in:range},%s,%s)))' % (N6, BASE6, c1('Needs high'), W6, BASE6, c1('Wants high'), S6, BASE6, c1('Savings low'), c1('Within range')))],
    GR('What if', ('Move 300 to savings', {'move': 300}), ('Move 800 to savings', {'move': 800}), ('Range 2 points', {'range': 0.02}), ('Income 8000', {'take': 8000}), ('Income 11000', {'take': 11000}))))

# 7 ---------------------------------------------------------------- pay rhythm calendar
FQ, AN = '{in:freq}', '{in:anchor}'
def PM(j):
    s = 'EDATE(%s,%d)' % (MS, j); e = 'EOMONTH(%s,0)' % s
    return 'IF(%s=%s,INT((%s-%s)/7)-INT((%s-1-%s)/7),IF(%s=%s,INT((%s-%s)/14)-INT((%s-1-%s)/14),IF(%s=%s,2,1)))' % (FQ, WEEKLY, e, AN, s, AN, FQ, BIWK, e, AN, s, AN, FQ, TWICE)
STEP = 'IF(%s=%s,7,IF(%s=%s,14,0))' % (FQ, WEEKLY, FQ, BIWK)
BASEN = 'IF(%s=%s,4,IF(%s=%s,2,99))' % (FQ, WEEKLY, FQ, BIWK)
MM = R('pay_rhythm', 'month')
PARR = '((%s>0)*(INT((DATE(YEAR(%s),MONTH(%s)+1,0)-%s)/MAX(%s,1))-INT((%s-1-%s)/MAX(%s,1)))+(%s=0)*IF(%s=%s,2,1))' % (STEP, MM, MM, AN, STEP, MM, AN, STEP, STEP, FQ, TWICE)
IN12 = '(%s>=%s)*(%s<EDATE(%s,12))' % (MM, MS, MM, MS)
FIRSTX = 'SUMPRODUCT(MIN(%s+(((%s<=%s)+(%s<%s))>0)*1000000000))' % (MM, PARR, BASEN, MM, MS)
PAYS12 = 'SUMPRODUCT(%s*%s)' % (IN12, PARR)
tools.append(TOOL('rhythm_tool', 'Pay Rhythm Calendar', 'Pay days in each month and which month has an extra one',
    'Pick any pay rhythm and a pay date: pay days in each of the next six months, the number in 12 months and the extra pay month, when a third paycheck lands in one month.', [
    IL('freq', 'Pay rhythm', 'payfreq', 'Every two weeks'), I('anchor', 'A pay date, past or next', iso(PAYDAY1_NEXT), 'date'), I('net', 'Take-home of one paycheck', D.PAYCHECK_NET)], [
    O('Pay days this month', 'int', PM(0)), O('Pay days next month', 'int', PM(1)), O('Pay days in 2 months', 'int', PM(2)), O('Pay days in 3 months', 'int', PM(3)), O('Pay days in 4 months', 'int', PM(4)), O('Pay days in 5 months', 'int', PM(5)),
    O('Pay days in the next 12 months', 'int', PAYS12), O('Extra pay months in the next 12', 'int', 'SUMPRODUCT(%s*(%s>%s))' % (IN12, PARR, BASEN)),
    O('First extra pay month', 'date', 'IF(%s>=1000000000,%s,%s)' % (FIRSTX, c2('No extra pay month'), FIRSTX)), O('Extra paycheck to assign', 'money', 'IF(%s>=1000000000,0,{in:net})' % FIRSTX),
    O('Take-home in the next 12 months', 'money', '%s*{in:net}' % PAYS12), O('Average take-home a month', 'money', '%s*{in:net}/12' % PAYS12),
    O('Verdict', 'text', 'IF(%s>=1000000000,%s,%s)' % (FIRSTX, c2('No extra pay month'), c2('Extra pay month ahead')))],
    GR('What if', ('Weekly pay', {'freq': '=' + tok('payfreq', 'Weekly')}), ('Twice a month', {'freq': '=' + tok('payfreq', 'Twice a month')}), ('Monthly pay', {'freq': '=' + tok('payfreq', 'Monthly')}),
       ('Next pay in 5 days', {'anchor': '={today}+5'}), ('Next pay in 12 days', {'anchor': '={today}+12'}))))

# 8 ---------------------------------------------------------------- extra pay month planner
NEXTX = 'IFERROR(SMALL(%s,1),"")' % R('extra_pay', 'month_if_extra')
tools.append(TOOL('extra_pay_tool', 'Extra Pay Month Planner', 'What do we do with the third paycheck',
    'Type the extra paycheck and how to split it between debt, goals and the income buffer; the next extra pay month comes from the Extra Pay Months sheet and the rest goes to spending.', [
    I('extra', 'Extra paycheck, take-home', D.PAYCHECK_NET), I('debt', 'Share to debt', 0.4, 'pct'), I('goals', 'Share to goals', 0.3, 'pct'), I('buffer', 'Share to the income buffer', 0.2, 'pct')], [
    O('To debt', 'money', '{in:extra}*{in:debt}'), O('To goals', 'money', '{in:extra}*{in:goals}'), O('To the income buffer', 'money', '{in:extra}*{in:buffer}'),
    O('To spending, the rest', 'money', '{in:extra}*(1-{in:debt}-{in:goals}-{in:buffer})'), O('Share left unassigned', 'pct', '1-{in:debt}-{in:goals}-{in:buffer}'),
    O('Next extra pay month', 'date', NEXTX), O('Days until that month starts', 'int', 'IF(%s="","",MAX(0,%s-{today}))' % (NEXTX, NEXTX)),
    O('Buffer months added by this split', 'num', 'IFERROR({in:extra}*{in:buffer}/%s,0)' % BASE0), O('Extra pay months in the next 12', 'int', 'COUNTIFS(%s,">0",%s,"<12")' % (R('extra_pay', 'extra_pay'), R('extra_pay', 'offset'))),
    O('Verdict', 'text', 'IF(AND({in:debt}>={in:goals},{in:debt}>={in:buffer}),%s,IF({in:goals}>={in:buffer},%s,%s))' % (c2('Assign to debt'), c2('Assign to goals'), c2('Assign to buffer')))],
    GR('What if', ('All to debt', {'debt': 1, 'goals': 0, 'buffer': 0}), ('Buffer first', {'debt': 0.2, 'goals': 0.2, 'buffer': 0.6}), ('Goals first', {'debt': 0.2, 'goals': 0.6, 'buffer': 0.2}),
       ('Keep half to spend', {'debt': 0.2, 'goals': 0.2, 'buffer': 0.1}), ('A smaller extra', {'extra': 1500}))))

# 9 ---------------------------------------------------------------- pay per period converter
PERIODS = 'IF({in:freq}=%s,52,IF({in:freq}=%s,26,IF({in:freq}=%s,24,12)))' % (WEEKLY, BIWK, TWICE)
tools.append(TOOL('converter_tool', 'Pay per Period Converter', 'How much to set aside from each paycheck for a bill or goal',
    'Type a bill or goal, how many times a year it falls due and your pay rhythm; the amount per paycheck is shown for every rhythm, with its share of one paycheck.', [
    I('amount', 'Amount of the bill or goal each time', 1650), I('times', 'Times a year it falls due, 12 monthly, 1 yearly', 12, 'int'), IL('freq', 'Your pay rhythm', 'payfreq', 'Every two weeks')], [
    O('Paychecks in a year', 'int', PERIODS), O('Yearly total of the bill or goal', 'money', '{in:amount}*{in:times}'), O('Set aside per paycheck', 'money', 'ROUND({in:amount}*{in:times}/%s,2)' % PERIODS),
    O('Share of one paycheck', 'pct', 'IFERROR({in:amount}*{in:times}/%s/{set:paycheck_net},0)' % PERIODS), O('Per paycheck if paid weekly', 'money', 'ROUND({in:amount}*{in:times}/52,2)'),
    O('Per paycheck if paid every two weeks', 'money', 'ROUND({in:amount}*{in:times}/26,2)'), O('Per paycheck if paid twice a month', 'money', 'ROUND({in:amount}*{in:times}/24,2)'),
    O('Per paycheck if paid monthly', 'money', 'ROUND({in:amount}*{in:times}/12,2)'), O('Per month', 'money', 'ROUND({in:amount}*{in:times}/12,2)'),
    O('Verdict', 'text', c2('Set aside per paycheck'))],
    GR('What if', ('Weekly pay', {'freq': '=' + tok('payfreq', 'Weekly')}), ('Twice a month', {'freq': '=' + tok('payfreq', 'Twice a month')}), ('Monthly pay', {'freq': '=' + tok('payfreq', 'Monthly')}),
       ('A yearly premium of 1260', {'amount': 1260, 'times': 1}), ('A quarterly bill of 300', {'amount': 300, 'times': 4}))))

# 10 --------------------------------------------------------------- irregular income baseline
def TJ(j): return 'SUMIFS(%s,%s,EDATE(%s,-%d),%s,%s,%s,"<>"&%s)' % (R('income', 'net'), R('income', 'month'), MS, j, R('income', 'person'), P2, R('income', 'source'), WIND)
LOW10 = 'MIN(' + ','.join('IF({in:months}>=%d,%s,1000000000)' % (j, TJ(j)) for j in range(1, 7)) + ')'
AVG10 = '(' + '+'.join('IF({in:months}>=%d,%s,0)' % (j, TJ(j)) for j in range(1, 7)) + ')/{in:months}'
HI10 = 'MAX(' + ','.join('IF({in:months}>=%d,%s,0)' % (j, TJ(j)) for j in range(1, 7)) + ')'
REC10 = 'SUMIFS(%s,%s,%s,%s,%s,%s,"<>"&%s)' % (R('income', 'net'), R('income', 'month'), MS, R('income', 'person'), P2, R('income', 'source'), WIND)
tools.append(TOOL('baseline_tool', 'Irregular Income Baseline', 'What can we safely budget from freelance and side income',
    'Type how many recent months to look at; the lowest and average of partner 2 income (clients and side income, no windfalls) give the baseline to budget, with this month so far against it.', [
    I('months', 'Recent months to look at, 1 to 6', 6, 'int')], [
    O('Baseline to budget, the lowest month', 'money', LOW10), O('Average of those months', 'money', AVG10), O('Highest of those months', 'money', HI10), O('Spread between highest and lowest', 'money', '%s-%s' % (HI10, LOW10)),
    O('Received this month so far', 'money', REC10), O('This month so far against the baseline', 'money', '%s-%s' % (REC10, LOW10)), O('Buffer to hold, months of baseline', 'money', '{set:buffer_target}*%s' % LOW10),
    O('Months above the baseline in the last 12', 'int', 'COUNTIFS(%s,%s,%s,"<0")' % (R('baseline', 'status'), c1('Above baseline'), R('baseline', 'offset'))),
    O('Partner 2 income you plan on', 'money', '{set:p2_budget}'), O('Plan above the baseline by', 'money', '{set:p2_budget}-%s' % LOW10),
    O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (REC10, LOW10, c3('Above baseline so far'), c3('Below baseline so far')))],
    GR('What if', ('Look at 3 months', {'months': 3}), ('Look at 4 months', {'months': 4}), ('Look at 5 months', {'months': 5}), ('Look at 2 months', {'months': 2}), ('Look at 1 month', {'months': 1}))))

# 11 --------------------------------------------------------------- buffer builder
BASE11 = 'IF({in:baseline}>0,{in:baseline},%s)' % BASE0
GOAL11 = '(%s*{in:months})' % BASE11
REST11 = 'MAX(0,%s-{in:saved})' % GOAL11
NP11 = 'IFERROR(ROUNDUP(NPER({in:rate}/12,{in:add},{in:saved},-%s),0),"")' % GOAL11
tools.append(TOOL('buffer_tool', 'Buffer Builder', 'How long until the income buffer is built',
    'Type the buffer in months of baseline, what you hold and what you add each month; closed-form months to go, the date and the monthly amount to be done in a year are estimates from your numbers.', [
    I('baseline', 'Monthly baseline, 0 uses the Income Baseline sheet', 0), I('months', 'Buffer to build, months of baseline', 3, 'int'), I('saved', 'Held in the buffer now', 3000), I('add', 'Added each month', 300),
    I('rate', 'Yearly interest on the buffer, an example', 0.02, 'pct')], [
    O('Baseline used', 'money', BASE11), O('Buffer goal', 'money', GOAL11), O('Held now, in months of baseline', 'num', 'IFERROR({in:saved}/%s,0)' % BASE11), O('Still to build', 'money', REST11),
    O('Months to go', 'int', 'IF(%s=0,0,%s)' % (REST11, NP11)), O('Buffer reached around', 'date', 'IF(%s=0,{today},IF(%s="","",EDATE({today},%s)))' % (REST11, NP11, NP11)),
    O('Add each month to be done in 12 months', 'money', 'IF(%s=0,0,MAX(0,PMT({in:rate}/12,12,{in:saved},-%s)))' % (REST11, GOAL11)),
    O('Months of the buffer built so far', 'int', 'MIN({in:months},INT(IFERROR({in:saved}/%s,0)))' % BASE11), O('Months of the buffer still to go', 'int', '{in:months}-MIN({in:months},INT(IFERROR({in:saved}/%s,0)))' % BASE11),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (REST11, c2('Buffer is built'), c2('Buffer is building')))],
    GR('What if', ('Add 500 a month', {'add': 500}), ('Add 150 a month', {'add': 150}), ('Six months of buffer', {'months': 6}), ('Held 5000 now', {'saved': 5000}), ('No interest', {'rate': 0}))))

# 12 --------------------------------------------------------------- bills before the next payday
BAL12 = 'IF({in:balance}>0,{in:balance},%s)' % B0
BILLS12 = UNP(NP)
def TOPN(k): return 'IFERROR(INDEX(%s,MATCH(%d,%s,0))&"","")' % (R('bills_due', 'bill'), k, R('bills_due', 'act_rank'))
def TOPA(k): return 'IFERROR(INDEX(%s,MATCH(%d,%s,0)),0)' % (R('bills_due', 'amount'), k, R('bills_due', 'act_rank'))
tools.append(TOOL('before_payday_tool', 'Bills Before Next Payday', 'Do I have enough to cover the bills before the next paycheck',
    'The unpaid bills of the joint account due before the next payday against the balance you type (or the Accounts balance), with the five largest bills ranked so you pay the biggest first.', [
    I('balance', 'Joint balance now, 0 uses Accounts', 0)], [
    O('Balance used', 'money', BAL12), O('Next payday', 'date', 'IF(%s>0,%s,"")' % (NP, NP)), O('Unpaid bills due before it', 'money', BILLS12),
    O('Bills to pay', 'int', 'COUNTIFS(%s,"<>"&%s,%s,{set:joint_id},%s,"<"&%s,%s,">0")' % (R('bills_due', 'status'), PAID_B, R('bills_due', 'account_id'), R('bills_due', 'due_date'), NP, R('bills_due', 'amount'))),
    O('Left after the bills', 'money', '%s-%s' % (BAL12, BILLS12)), O('Largest bill', 'text', TOPN(1)), O('Largest bill, amount', 'money', TOPA(1)), O('Second largest bill', 'text', TOPN(2)), O('Second largest bill, amount', 'money', TOPA(2)),
    O('Third largest bill', 'text', TOPN(3)), O('Third largest bill, amount', 'money', TOPA(3)), O('Fourth largest bill', 'text', TOPN(4)), O('Fourth largest bill, amount', 'money', TOPA(4)),
    O('Fifth largest bill', 'text', TOPN(5)), O('Fifth largest bill, amount', 'money', TOPA(5)), O('Short of the bills by', 'money', 'MAX(0,%s-%s)' % (BILLS12, BAL12)),
    O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (BAL12, BILLS12, c2('Covered'), c2('Short of the bills')))],
    GR('What if', ('Balance 800', {'balance': 800}), ('Balance 1500', {'balance': 1500}), ('Balance 2500', {'balance': 2500}), ('Balance 400', {'balance': 400}))))

# 13 --------------------------------------------------------------- spending money until payday
BAL13 = 'IF({in:balance}>0,{in:balance},%s)' % B0
SP13 = '(%s-%s-{in:setaside}-{in:keep}*{set:cash_floor})' % (BAL13, UNP(NP))
tools.append(TOOL('spend_tool', 'Spending Money Until Payday', 'How much can I spend a day until payday',
    'The balance less unpaid bills before the next payday, the set-asides you keep and, if you choose, the cash floor, shared over the days left.', [
    I('balance', 'Joint balance now, 0 uses Accounts', 0), I('setaside', 'Set-asides to keep before payday', 100), I('keep', 'Keep the cash floor untouched, 1 for yes', 0, 'int')], [
    O('Balance used', 'money', BAL13), O('Unpaid bills due before payday', 'money', UNP(NP)), O('Set-asides kept', 'money', '{in:setaside}'), O('Cash floor kept', 'money', '{in:keep}*{set:cash_floor}'),
    O('Money you can spend', 'money', 'MAX(0,%s)' % SP13), O('Days until payday', 'int', 'IF(%s>0,%s-{today},0)' % (NP, NP)), O('Can spend a day', 'money', 'IF(%s>{today},MAX(0,%s)/(%s-{today}),0)' % (NP, SP13, NP)),
    O('Can spend a week', 'money', 'IF(%s>{today},MAX(0,%s)/(%s-{today})*7,0)' % (NP, SP13, NP)), O('Short by', 'money', 'MAX(0,-(%s))' % SP13),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (SP13, c3('Can spend per day'), c3('Nothing to spend')))],
    GR('What if', ('Keep the cash floor', {'keep': 1}), ('Set aside 100', {'setaside': 100}), ('Balance 1500', {'balance': 1500}), ('Balance 2000', {'balance': 2000}), ('Balance 700', {'balance': 700}))))

# 14 --------------------------------------------------------------- income against plan
REC14 = 'SUMIFS(%s,%s,%s)' % (R('income', 'net'), R('income', 'month'), MS)
PLAN14 = TH
TD14 = '(%s*DAY({today})/DAY(EOMONTH({today},0)))' % PLAN14
P1REM = 'SUMIFS(%s,%s,%s,%s,">="&{today},%s,"<="&EOMONTH({today},0))' % (R('pay_schedule', 'expected_net'), R('pay_schedule', 'person'), P1, R('pay_schedule', 'date'), R('pay_schedule', 'date'))
P2REM = 'MAX(0,{set:p2_budget}-SUMIFS(%s,%s,%s,%s,%s,%s,"<>"&%s))' % (R('income', 'net'), R('income', 'month'), MS, R('income', 'person'), P2, R('income', 'source'), WIND)
tools.append(TOOL('plan_tool', 'Income Against Plan', 'Are we ahead or behind the income we planned this month',
    'Money received this month against the income you budget pro-rated by days, with a month-end estimate for the Base, Best and Worst case of partner 2 income still to come.', [
    I('best', 'Best case: partner 2 income still to come is higher by', 0.15, 'pct'), I('worst', 'Worst case: partner 2 income still to come is lower by', -0.4, 'pct'), I('tol', 'Tolerance either side of the plan', 0.05, 'pct')], [
    O('Received so far this month', 'money', REC14), O('Income you budget this month', 'money', PLAN14), O('Planned by today, pro-rated by days', 'money', TD14),
    O('Received against planned by today', 'money', '%s-%s' % (REC14, TD14)), O('Partner 1 paychecks still to come', 'money', P1REM), O('Partner 2 income still to come, as planned', 'money', P2REM),
    O('Month-end estimate, Base', 'money', '%s+%s+%s' % (REC14, P1REM, P2REM)), O('Month-end estimate, Best', 'money', '%s+%s+%s*(1+{in:best})' % (REC14, P1REM, P2REM)),
    O('Month-end estimate, Worst', 'money', '%s+%s+%s*(1+{in:worst})' % (REC14, P1REM, P2REM)), O('Worst case against the plan', 'money', '%s+%s+%s*(1+{in:worst})-%s' % (REC14, P1REM, P2REM, PLAN14)),
    O('Verdict', 'text', 'IF(%s>=%s*(1+{in:tol}),%s,IF(%s>=%s*(1-{in:tol}),%s,%s))' % (REC14, TD14, c3('Ahead of plan'), REC14, TD14, c3('On plan'), c3('Behind plan')))],
    GR('What if', ('Wide tolerance', {'tol': 0.15}), ('No tolerance', {'tol': 0}), ('Best case +30%', {'best': 0.3}), ('Worst case -60%', {'worst': -0.6}), ('Worst case none', {'worst': 0}))))

# 15 --------------------------------------------------------------- freelance cash timing
OPENI = 'SUMIFS(%s,%s,"<>"&%s)' % (R('invoices', 'amount'), R('invoices', 'status'), PAID_I)
OVER = 'SUMIFS(%s,%s,"<>"&%s,%s,">0")' % (R('invoices', 'amount'), R('invoices', 'status'), PAID_I, R('invoices', 'days_late'))
LOWD = 'SUMIFS(%s,%s,1)' % (R('low_point', 'low_date'), R('low_point', 'pn'))
ARR = 'SUMIFS(%s,%s,"<>"&%s,%s,"<="&(%s-{in:delay}))' % (R('invoices', 'amount'), R('invoices', 'status'), PAID_I, R('invoices', 'expected_pay'), LOWD)
NEWLOW = '(%s+%s)' % (LOWNP, ARR)
OVN = 'COUNTIFS(%s,"<>"&%s,%s,">0")' % (R('invoices', 'status'), PAID_I, R('invoices', 'days_late'))
tools.append(TOOL('freelance_timing_tool', 'Freelance Cash Timing', 'Do I chase an invoice or wait for the payment',
    'Open freelance invoices with the date each client usually pays, and what arrives before the low point of the next payday; overdue invoices are not counted until they are paid.', [
    I('delay', 'Extra days clients take beyond their usual', 3, 'int')], [
    O('Open freelance invoices', 'money', OPENI), O('Overdue invoices', 'money', OVER), O('Overdue invoices, count', 'int', OVN),
    O('Client with the oldest overdue invoice', 'text', 'IF(%s=0,"",IFERROR(INDEX(%s,MATCH(1,%s,0))&"",""))' % (OVN, R('invoices', 'client'), R('invoices', 'chase_rank'))),
    O('Lowest balance before the next payday', 'money', LOWNP), O('Date of that low point', 'date', 'IF(%s>0,%s,"")' % (LOWD, LOWD)), O('Invoices expected before that date', 'money', ARR),
    O('Lowest balance if they arrive', 'money', NEWLOW), O('Lowest balance if the overdue invoices are paid today', 'money', '%s+%s' % (NEWLOW, OVER)),
    O('Short of the floor after the expected payments', 'money', 'MAX(0,{set:cash_floor}-%s)' % NEWLOW), O('Verdict', 'text', 'IF(%s>={set:cash_floor},%s,%s)' % (NEWLOW, c3('Wait for the payment'), c3('Chase the client')))],
    GR('What if', ('Clients pay 5 days later', {'delay': 5}), ('Clients pay 10 days later', {'delay': 10}), ('Clients pay on time', {'delay': 0}), ('Clients pay 20 days later', {'delay': 20}))))

# 16 --------------------------------------------------------------- take-home check
DED16 = '({in:tax}+{in:retirement}+{in:other})'
NET16 = '({in:gross}-%s)' % DED16
tools.append(TOOL('takehome_tool', 'Take-Home Calculator', 'Does my pay statement match what reached the account',
    'Type the gross, tax, retirement and other deductions of a pay statement and the amount that reached the account; the take-home it should be and the difference are shown.', [
    I('gross', 'Gross pay', 2850), I('tax', 'Tax withheld', 427.5), I('retirement', 'Retirement contribution', 142.5), I('other', 'Other deductions', 120), I('bank', 'Amount that reached the account', 2160)], [
    O('Total deductions', 'money', DED16), O('Take-home it should be', 'money', NET16), O('Difference to the account', 'money', '{in:bank}-%s' % NET16),
    O('Deductions share of gross', 'pct', 'IFERROR(%s/{in:gross},0)' % DED16), O('Take-home share of gross', 'pct', 'IFERROR(%s/{in:gross},0)' % NET16), O('Tax share of gross', 'pct', 'IFERROR({in:tax}/{in:gross},0)'),
    O('Retirement share of gross', 'pct', 'IFERROR({in:retirement}/{in:gross},0)'), O('Take-home of 26 paychecks', 'money', '%s*26' % NET16), O('Take-home of 24 paychecks', 'money', '%s*24' % NET16),
    O('Verdict', 'text', 'IF(ABS({in:bank}-%s)<={set:tolerance},%s,%s)' % (NET16, c3('Matches the bank'), c3('Check the take-home')))],
    GR('What if', ('The account shows 35 less', {'bank': 2125}), ('Retirement 214', {'retirement': 213.75}), ('Gross 3000', {'gross': 3000}), ('Tax 500', {'tax': 500}), ('The account shows 40 more', {'bank': 2200}))))

# 17 --------------------------------------------------------------- late paycheck test
PAYNP = 'SUMIFS(%s,%s,%s,%s,%s)' % (R('pay_schedule', 'expected_net'), R('pay_schedule', 'into_joint'), YES, R('pay_schedule', 'date'), NP)
NL17 = 'ROUND(%s+%s-%s-%s-{set:daily_spend}*MAX(0,%s+{in:days}-1-{today}),2)' % (B0, PAYIN('%s+{in:days}' % NP), PAYNP, UNP('%s+{in:days}' % NP), NP)
tools.append(TOOL('late_pay_tool', 'Late Paycheck Test', 'What if the next paycheck arrives late',
    'Move the next pay date by a number of days; the bills that fall due in the gap and the new lowest balance are set against your cash floor.', [
    I('days', 'Days the paycheck arrives late', 3, 'int'), I('floor', 'Cash floor to test, your own number', CASH_FLOOR)], [
    O('Next payday', 'date', 'IF(%s>0,%s,"")' % (NP, NP)), O('Payday if it is late', 'date', 'IF(%s>0,%s+{in:days},"")' % (NP, NP)), O('Lowest balance before the payday now', 'money', LOWNP),
    O('Bills that fall due in the gap', 'money', 'SUMIFS(%s,%s,"<>"&%s,%s,{set:joint_id},%s,">="&%s,%s,"<"&(%s+{in:days}))' % (R('bills_due', 'amount'), R('bills_due', 'status'), PAID_B, R('bills_due', 'account_id'), R('bills_due', 'due_date'), NP, R('bills_due', 'due_date'), NP)),
    O('Lowest balance if it is late', 'money', NL17), O('Short of the floor if it is late', 'money', 'MAX(0,{in:floor}-%s)' % NL17), O('Move in to stay at the floor', 'money', 'MAX(0,{in:floor}-%s)' % NL17),
    O('Change in the low point', 'money', '%s-%s' % (NL17, LOWNP)), O('Verdict', 'text', 'IF(%s>={in:floor},%s,%s)' % (NL17, c3('Safe if pay is late'), c3('Short if pay is late')))],
    GR('What if', ('One day late', {'days': 1}), ('Five days late', {'days': 5}), ('Seven days late', {'days': 7}), ('Ten days late', {'days': 10}), ('A floor of 200', {'floor': 200}))))

# 18 --------------------------------------------------------------- next three months plan
def INC18(j): return '(SUMIFS(%s,%s,EDATE(%s,%d))+(IF({in:p2}>0,{in:p2},{set:p2_budget}))*POWER(1+{in:trend},%d))' % (R('pay_rhythm', 'p1_expected'), R('pay_rhythm', 'month'), MS, j, j)
def PL18(j): return 'SUMIFS(%s,%s,EDATE(%s,%d))' % (R('budget', 'planned'), R('budget', 'month'), MS, j)
def MN(j): return 'EDATE(%s,%d)' % (MS, j)
tools.append(TOOL('three_month_tool', 'Next Three Months Plan', 'Will the next three months leave a surplus or a gap',
    'Planned outgoings of each of the next three months against the paychecks of your rhythm plus the partner 2 income you plan on, with a monthly trend you can type.', [
    I('p2', 'Partner 2 income per month, 0 uses Settings', 0), I('trend', 'Monthly change of partner 2 income', 0.0, 'pct')], [
    O('Next month', 'date', MN(1)), O('Income next month', 'money', INC18(1)), O('Planned next month', 'money', PL18(1)), O('Surplus or gap next month', 'money', '%s-%s' % (INC18(1), PL18(1))),
    O('Income in 2 months', 'money', INC18(2)), O('Planned in 2 months', 'money', PL18(2)), O('Surplus or gap in 2 months', 'money', '%s-%s' % (INC18(2), PL18(2))),
    O('Income in 3 months', 'money', INC18(3)), O('Planned in 3 months', 'money', PL18(3)), O('Surplus or gap in 3 months', 'money', '%s-%s' % (INC18(3), PL18(3))),
    O('Surplus or gap over three months', 'money', '%s+%s+%s-%s-%s-%s' % (INC18(1), INC18(2), INC18(3), PL18(1), PL18(2), PL18(3))),
    O('Verdict', 'text', 'IF(%s+%s+%s>=%s+%s+%s,%s,%s)' % (INC18(1), INC18(2), INC18(3), PL18(1), PL18(2), PL18(3), c3('Surplus'), c3('Gap')))],
    GR('What if', ('Partner 2 at 4000', {'p2': 4000}), ('Partner 2 at 6000', {'p2': 6000}), ('Partner 2 income falls 5 percent a month', {'trend': -0.05}), ('Partner 2 income grows 5 percent a month', {'trend': 0.05}), ('Partner 2 at baseline 2500', {'p2': 2500}))))
assert len(tools) == 18, len(tools)
