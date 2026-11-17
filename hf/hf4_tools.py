"""Household Finance suite part 4: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf4_lists import *
from hf4_tables import R, MS, DB, TH12, GR12, MINS, EXTRAS, PAYTOT, CARDPAY, CARDBAL, BAL, CARD, LOAN_K, EXTRA, NP, ANN
import hf4_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
SN, AV, XT, WF, EP = (lambda c, t=t: R(t, c) for t in ('snow_order', 'aval_order', 'extra_test', 'windfall', 'extra_plan'))
SS, SA, HI, DM, MO = (lambda c, t=t: R(t, c) for t in ('sched_snow', 'sched_aval', 'history', 'due_map', 'min_only'))
def DATEM(m): return 'IF(OR((%s)=0,(%s)>=999),"",EOMONTH(%s,%s))' % (m, m, MS, m)
def F1(rng): return 'INDEX(%s,1)' % rng
tools = []
VERD_FREE = lambda m: 'IF(%s>=999,%s,%s)' % (m, vd('Not paid off within the schedule'), vd('Debt-free date and interest shown'))
# 1 and 2 snowball and avalanche payoff -----------------------------------------------------------------------------------------------------
for key_, name, order, sched, title, hint in (
        ('snowball', 'Snowball Payoff', SN, SS, 'When are we debt-free if the smallest balance goes first',
         'Debts paid smallest balance first, the extra payment rolled forward: debt-free date, months, interest and the balance after the months you choose. An estimate.'),
        ('avalanche', 'Avalanche Payoff', AV, SA, 'When are we debt-free if the highest rate goes first',
         'Debts paid highest rate first, the extra payment rolled forward: debt-free date, months, interest and the balance after the months you choose. An estimate.')):
    tools.append(TOOL(key_, name, title, hint, [I('look', 'Months to look ahead', 12, 'int')], [
        O('Payment each month, all debts', 'money', F1(order('budget'))), O('Debt paid first', 'text', F1(order('debt'))), O('Cleared in month', 'int', F1(order('payoff_month'))),
        O('Months to debt-free', 'int', F1(order('months_all'))), O('Debt-free date', 'date', F1(order('free_date'))), O('Total interest', 'money', F1(order('interest_all'))),
        O('Balance after the months you chose', 'money', 'IFERROR(INDEX(%s,{in:look})+0,0)' % sched('balance')), O('Debts left after those months', 'int', 'IFERROR(INDEX(%s,{in:look})+0,0)' % sched('debts_left')),
        O('Verdict', 'text', VERD_FREE(F1(order('months_all'))))],
        GR('What if you look ahead', ('6 months', {'look': 6}), ('12 months', {'look': 12}), ('24 months', {'look': 24}), ('36 months', {'look': 36}), ('48 months', {'look': 48}))))
# 3 snowball against avalanche -----------------------------------------------------------------------------------------------------------------
tools.append(TOOL('snow_vs_aval', 'Snowball Against Avalanche', 'Which order costs less, balance or rate first',
    'Both orders side by side with the same payment each month: months, debt-free date, interest, the debt each clears first and the balance after the months you choose. Estimates from your numbers.', [I('look', 'Months to look ahead', 12, 'int')], [
    O('Avalanche: months to debt-free', 'int', F1(AV('months_all'))), O('Snowball: months to debt-free', 'int', F1(SN('months_all'))), O('Months saved by avalanche', 'int', '%s-%s' % (F1(SN('months_all')), F1(AV('months_all')))),
    O('Avalanche: debt-free date', 'date', F1(AV('free_date'))), O('Snowball: debt-free date', 'date', F1(SN('free_date'))),
    O('Avalanche: total interest', 'money', F1(AV('interest_all'))), O('Snowball: total interest', 'money', F1(SN('interest_all'))), O('Interest saved by avalanche', 'money', '%s-%s' % (F1(SN('interest_all')), F1(AV('interest_all')))),
    O('Avalanche clears first', 'text', F1(AV('debt'))), O('Snowball clears first', 'text', F1(SN('debt'))),
    O('Avalanche: balance after the months you chose', 'money', 'IFERROR(INDEX(%s,{in:look})+0,0)' % SA('balance')), O('Snowball: balance after the months you chose', 'money', 'IFERROR(INDEX(%s,{in:look})+0,0)' % SS('balance')),
    O('Verdict', 'text', 'IF(ABS(%s-%s)<1,%s,IF(%s<%s,%s,%s))' % (F1(AV('interest_all')), F1(SN('interest_all')), vd('Both cost the same'), F1(AV('interest_all')), F1(SN('interest_all')), vd('Avalanche costs less interest'), vd('Snowball costs less interest')))],
    GR('What if you look ahead', ('6 months', {'look': 6}), ('12 months', {'look': 12}), ('24 months', {'look': 24}), ('36 months', {'look': 36}))))
# 4 extra payment test -----------------------------------------------------------------------------------------------------------------------------
IX4 = 'MATCH({in:extra},%s,1)' % XT('xtr')
tools.append(TOOL('extra_test', 'Extra Payment Test', 'What if we pay this much more each month',
    'Type an extra amount: the avalanche plan at the nearest step at or below it, with the debt-free date and the months and interest saved against minimums.', [
    I('extra', 'Extra payment a month to test', 400)], [
    O('Step used, extra a month', 'money', 'INDEX(%s,%s)' % (XT('xtr'), IX4)), O('Debt-free date', 'date', 'INDEX(%s,%s)' % (XT('debt_free'), IX4)), O('Months to debt-free', 'int', 'INDEX(%s,%s)' % (XT('months'), IX4)),
    O('Total interest', 'money', 'INDEX(%s,%s)' % (XT('interest'), IX4)), O('Months saved against minimums only', 'int', 'INDEX(%s,%s)' % (XT('months_saved'), IX4)),
    O('Interest saved against minimums only', 'money', 'INDEX(%s,%s)' % (XT('interest_saved'), IX4)), O('Months at the extra payment in Settings', 'int', F1(AV('months_all'))),
    O('Extra above the Settings amount', 'money', 'INDEX(%s,%s)-%s' % (XT('xtr'), IX4, EXTRA)),
    O('Verdict', 'text', 'IF(INDEX(%s,%s)>=999,%s,IF(INDEX(%s,%s)>0,%s,%s))' % (XT('months'), IX4, vd('Not paid off within the schedule'), XT('months_saved'), IX4, vd('Extra payment shortens the plan'), vd('Debt-free date and interest shown')))],
    GR('What if the extra payment is', ('Nothing', {'extra': 0}), ('100', {'extra': 100}), ('300', {'extra': 300}), ('500', {'extra': 500}), ('1000', {'extra': 1000}))))
# 5 extra payment solver ----------------------------------------------------------------------------------------------------------------------------
IX5 = 'COUNTIFS(%s,">"&{in:target})+1' % XT('months')
RBAR = 'SUMPRODUCT(%s,%s)/SUM(%s)' % (DB('balance'), DB('rate'), DB('balance'))
tools.append(TOOL('extra_solver', 'Extra Payment Solver', 'How much extra a month to be debt-free by a set time',
    'Type the number of months you want: the smallest step of the Extra payment test that gets there, with a second estimate that treats all debts as one loan. Estimates from your numbers.', [
    I('target', 'Months until you want to be debt-free', 30, 'int')], [
    O('Months at the extra payment in Settings', 'int', F1(AV('months_all'))), O('Extra needed, smallest step that gets there', 'money', 'IFERROR(INDEX(%s,%s),"")' % (XT('xtr'), IX5)),
    O('Extra above the Settings amount', 'money', 'IFERROR(INDEX(%s,%s)-%s,"")' % (XT('xtr'), IX5, EXTRA)), O('Debt-free date at that step', 'date', 'IFERROR(INDEX(%s,%s),"")' % (XT('debt_free'), IX5)),
    O('Interest at that step', 'money', 'IFERROR(INDEX(%s,%s),"")' % (XT('interest'), IX5)),
    O('Second estimate: extra if all debts were one loan', 'money', 'MAX(0,-PMT(%s/12,{in:target},%s)-%s)' % (RBAR, BAL(), MINS)),
    O('Verdict', 'text', 'IF(%s>COUNT(%s),%s,%s)' % (IX5, XT('months'), vd('Not within reach with the steps tested'), vd('Pay the extra shown')))],
    GR('What if you want to be debt-free in', ('24 months', {'target': 24}), ('30 months', {'target': 30}), ('36 months', {'target': 36}), ('42 months', {'target': 42}), ('60 months', {'target': 60}))))
# 6 debt-free date finder -----------------------------------------------------------------------------------------------------------------------------
MX = lambda c: 'MAX(%s)' % DB(c)
WISH = 'EOMONTH(%s,{in:wish})' % MS
tools.append(TOOL('debt_free', 'Debt-free Date Finder', 'When are we debt-free at each plan',
    'The debt-free date at the minimums, the current plan, snowball and avalanche, and the days from the date you want (a minus is ahead of it). Estimates.', [
    I('wish', 'Months until you want to be debt-free', 36, 'int')], [
    O('Date you want', 'date', WISH), O('At the minimums', 'date', DATEM(MX('months_min'))), O('At the current plan', 'date', DATEM(MX('plan_months'))), O('By snowball', 'date', F1(SN('free_date'))), O('By avalanche', 'date', F1(AV('free_date'))),
    O('Current plan: days after your date', 'int', '%s-%s' % (DATEM(MX('plan_months')), WISH)), O('Avalanche: days after your date', 'int', '%s-%s' % (F1(AV('free_date')), WISH)),
    O('Months saved, avalanche against the current plan', 'int', '%s-%s' % (MX('plan_months'), F1(AV('months_all')))),
    O('Verdict', 'text', 'IF(%s<=%s,%s,%s)' % (F1(AV('free_date')), WISH, vd('Within your limit'), vd('Above your limit')))],
    GR('What if you want to be debt-free in', ('24 months', {'wish': 24}), ('36 months', {'wish': 36}), ('48 months', {'wish': 48}), ('60 months', {'wish': 60}))))
# 7 avalanche order check ----------------------------------------------------------------------------------------------------------------------------
TOPI = 'MATCH(1,%s,0)' % DB('aval_rank')
tools.append(TOOL('aval_check', 'Avalanche Order Check', 'Is the extra payment on the highest rate',
    'Finds the debt with the highest rate, the extra it gets now against all the extra you pay, and the interest the split costs you over the months you choose. An estimate from your numbers.', [
    I('months', 'Months to look at', 12, 'int')], [
    O('Highest-rate debt', 'text', 'INDEX(%s,%s)' % (DB('debt'), TOPI)), O('Its yearly rate', 'pct', 'INDEX(%s,%s)' % (DB('rate'), TOPI)), O('Extra it gets now', 'money', 'INDEX(%s,%s)' % (DB('extra_planned'), TOPI)),
    O('All the extra you pay', 'money', EXTRAS), O('Move to the highest rate', 'money', '%s-INDEX(%s,%s)' % (EXTRAS, DB('extra_planned'), TOPI)),
    O('Interest lost in 12 months by the current split', 'money', 'SUM(%s)' % EP('interest_lost_year')), O('Interest lost over the months you chose', 'money', 'SUM(%s)*{in:months}/12' % EP('interest_lost_year')),
    O('Debt that gets the most extra now', 'text', 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (DB('debt'), DB('extra_planned'), DB('extra_planned'))),
    O('Verdict', 'text', 'IF(%s-INDEX(%s,%s)>0,%s,%s)' % (EXTRAS, DB('extra_planned'), TOPI, vd('Move the extra to the highest rate'), vd('Extra already on the highest rate')))],
    GR('What if you look at', ('6 months', {'months': 6}), ('12 months', {'months': 12}), ('24 months', {'months': 24}), ('36 months', {'months': 36}))))
# 8 minimum payments check ------------------------------------------------------------------------------------------------------------------------------
TH8 = '(%s)*(1-{in:drop})' % TH12
tools.append(TOOL('mins_check', 'Minimum Payments Check', 'Can we carry the minimum payments if income falls',
    'The total of the minimum payments against your take-home pay (the last twelve complete months), the limit in Settings and what happens if take-home falls by the share you type.', [
    I('drop', 'What if take-home falls by', 0, 'pct')], [
    O('Minimum payments each month', 'money', MINS), O('Take-home a month, last 12 months', 'money', TH8), O('Share of take-home', 'pct', '%s/(%s)' % (MINS, TH8)), O('Your limit in Settings', 'pct', '{set:minimums_range}'),
    O('Above (+) or below (-) your limit, points', 'pct', '%s/(%s)-{set:minimums_range}' % (MINS, TH8)), O('Months to debt-free at the minimums', 'int', MX('months_min')),
    O('Debt-free date at the minimums', 'date', DATEM(MX('months_min'))), O('Total interest at the minimums', 'money', 'SUM(%s)' % DB('min_interest')),
    O('Verdict', 'text', 'IF(%s/(%s)<={set:minimums_range},%s,%s)' % (MINS, TH8, vd('Within your limit'), vd('Above your limit')))],
    GR('What if take-home falls by', ('Nothing', {'drop': 0}), ('10 percent', {'drop': 0.1}), ('30 percent', {'drop': 0.3}), ('50 percent', {'drop': 0.5}), ('70 percent', {'drop': 0.7}))))
# 9 minimum only payoff ----------------------------------------------------------------------------------------------------------------------------------
tools.append(TOOL('min_payoff', 'Minimum Only Payoff', 'How long does each debt take at the minimum',
    'Pick a debt by its row number in the Debts sheet: the months, the payoff date and the interest if you pay only the minimum, and whether the minimum covers the monthly interest.', [
    I('row', 'Debt row number in the Debts sheet', 1, 'int')], [
    O('Debt', 'text', 'INDEX(%s,{in:row})' % MO('debt')), O('Minimum payment', 'money', 'INDEX(%s,{in:row})' % MO('min_payment')), O('Interest each month now', 'money', 'INDEX(%s,{in:row})' % MO('monthly_interest')),
    O('Months at the minimum', 'int', 'INDEX(%s,{in:row})' % MO('months')), O('Payoff date at the minimum', 'date', 'INDEX(%s,{in:row})' % MO('payoff_date')), O('Interest at the minimum', 'money', 'INDEX(%s,{in:row})' % MO('interest')),
    O('Debts whose minimum does not cover the interest', 'int', 'COUNTIFS(%s,%s)' % (DB('covers'), st('Below interest'))), O('Longest debt at the minimum, months', 'int', MX('months_min')),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,%s)>0,%s,%s)' % (DB('covers'), st('Below interest'), vd('A minimum does not cover the interest'), vd('Every minimum covers the interest')))],
    GR('What if you look at row', ('Row 1', {'row': 1}), ('Row 2', {'row': 2}), ('Row 3', {'row': 3}), ('Row 4', {'row': 4}), ('Row 5', {'row': 5}))))
# 10 debt ratios --------------------------------------------------------------------------------------------------------------------------------------------
GR10 = '(%s)*(1+{in:chg})' % GR12; TH10 = '(%s)*(1+{in:chg})' % TH12
tools.append(TOOL('ratios', 'Debt Ratios', 'Are our debt payments within the typical ranges',
    'Debt payments over gross income and card payments over take-home against the typical ranges in Settings, with the income change you type; a typical range, check your own numbers, never advice.', [
    I('chg', 'What if income changes by', 0, 'pct')], [
    O('Debt payments over gross income', 'pct', '%s/%s' % (PAYTOT, GR10)), O('Typical range in Settings', 'pct', '{set:debt_gross_range}'),
    O('Above (+) or below (-) the range, points', 'pct', '%s/%s-{set:debt_gross_range}' % (PAYTOT, GR10)), O('Card payments over take-home', 'pct', '%s/%s' % (CARDPAY, TH10)),
    O('Typical card range in Settings', 'pct', '{set:consumer_debt_range}'), O('Above (+) or below (-) the card range, points', 'pct', '%s/%s-{set:consumer_debt_range}' % (CARDPAY, TH10)),
    O('Minimum payments over take-home', 'pct', '%s/%s' % (MINS, TH10)), O('Average rate weighted by balance', 'pct', RBAR),
    O('Verdict', 'text', 'IF(AND(%s/%s<={set:debt_gross_range},%s/%s<={set:consumer_debt_range}),%s,%s)' % (PAYTOT, GR10, CARDPAY, TH10, vd('Within the typical range'), vd('Above the typical range')))],
    GR('What if income changes by', ('Down 30 percent', {'chg': -0.3}), ('Down 10 percent', {'chg': -0.1}), ('No change', {'chg': 0}), ('Up 10 percent', {'chg': 0.1}), ('Down 60 percent', {'chg': -0.6}))))
# 11 interest cost ranker -----------------------------------------------------------------------------------------------------------------------------------
def RK(k): return 'MATCH(LARGE(%s,%d),%s,0)' % (DB('int_key'), k, DB('int_key'))
tools.append(TOOL('interest_rank', 'Interest Cost Ranker', 'Which debt costs the most interest each month',
    'The debts ranked by the interest they charge each month, highest first, with the share of the total and the interest over the months you choose. An estimate from your numbers.', [
    I('months', 'Months to look at', 12, 'int')], [
    O('Highest: debt', 'text', 'INDEX(%s,%s)' % (DB('debt'), RK(1))), O('Highest: interest a month', 'money', 'INDEX(%s,%s)' % (DB('monthly_interest'), RK(1))),
    O('Second: debt', 'text', 'INDEX(%s,%s)' % (DB('debt'), RK(2))), O('Second: interest a month', 'money', 'INDEX(%s,%s)' % (DB('monthly_interest'), RK(2))),
    O('Third: debt', 'text', 'INDEX(%s,%s)' % (DB('debt'), RK(3))), O('Third: interest a month', 'money', 'INDEX(%s,%s)' % (DB('monthly_interest'), RK(3))),
    O('Interest a month, all debts', 'money', 'SUM(%s)' % DB('monthly_interest')), O('Share of the highest', 'pct', 'INDEX(%s,%s)/SUM(%s)' % (DB('monthly_interest'), RK(1), DB('monthly_interest'))),
    O('Interest over the months you chose', 'money', 'SUM(%s)*{in:months}' % DB('monthly_interest')), O('Verdict', 'text', vd('Highest interest cost is first'))],
    GR('What if you look at', ('6 months', {'months': 6}), ('12 months', {'months': 12}), ('24 months', {'months': 24}), ('36 months', {'months': 36}))))
# 12 payment calendar ------------------------------------------------------------------------------------------------------------------------------------------
TI = 'MATCH(SMALL(%s,1),%s,0)' % (DM('days_before'), DM('days_before'))
tools.append(TOOL('pay_calendar', 'Payment Calendar', 'Which due dates fall just before payday',
    'The due dates of the next days against your payday: the debts due, the tightest one, the date to pay it and a suggested due day if you ask your lender to move it. Estimates from your dates.', [
    I('days', 'Days to look ahead', 30, 'int')], [
    O('Next payday in Settings', 'date', '{set:next_payday}'), O('Debts due in the days you chose', 'int', 'COUNTIFS(%s,"<="&{in:days},%s,">=0")' % (DM('days_to_due'), DM('days_to_due'))),
    O('Tight due dates, within the margin before payday', 'int', 'COUNTIFS(%s,%s)' % (DM('flag'), st('Tight'))), O('Tightest debt', 'text', 'INDEX(%s,%s)' % (DM('debt'), TI)),
    O('Its due date', 'date', 'INDEX(%s,%s)' % (DM('next_due'), TI)), O('Days before payday', 'int', 'SMALL(%s,1)' % DM('days_before')), O('Pay on', 'date', 'INDEX(%s,%s)' % (DM('pay_on'), TI)),
    O('Suggested due day to ask for', 'int', 'INDEX(%s,%s)' % (DM('new_day'), TI)),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,%s)>0,%s,%s)' % (DM('flag'), st('Tight'), vd('Move the due date'), vd('Pay on the date shown')))],
    GR('What if you look ahead', ('14 days', {'days': 14}), ('30 days', {'days': 30}), ('45 days', {'days': 45}), ('60 days', {'days': 60}), ('90 days', {'days': 90}))))
# 13 windfall to debt -------------------------------------------------------------------------------------------------------------------------------------------
IX13 = 'IFERROR(MATCH({in:windfall},%s,1),1)' % WF('wfa')
tools.append(TOOL('windfall', 'Windfall to Debt', 'What if a windfall goes to the highest-rate debt',
    'Type a windfall: it goes to the highest-rate debt first (the nearest step at or below it is used), with the new debt-free date and the months and interest saved.', [
    I('windfall', 'Windfall amount', 1500)], [
    O('Step used', 'money', 'INDEX(%s,%s)' % (WF('wfa'), IX13)), O('First debt it goes to', 'text', 'INDEX(%s,%s)' % (WF('target'), IX13)), O('Applied to debts', 'money', 'INDEX(%s,%s)' % (WF('applied'), IX13)),
    O('New debt-free date', 'date', 'INDEX(%s,%s)' % (WF('debt_free'), IX13)), O('Months saved', 'int', 'INDEX(%s,%s)' % (WF('months_saved'), IX13)), O('Interest saved', 'money', 'INDEX(%s,%s)' % (WF('interest_saved'), IX13)),
    O('Debt-free date without the windfall', 'date', F1(AV('free_date'))), O('Verdict', 'text', 'IF(INDEX(%s,%s)>0,%s,%s)' % (WF('interest_saved'), IX13, vd('Windfall saves interest and months'), vd('Debt-free date and interest shown')))],
    GR('What if the windfall is', ('500', {'windfall': 500}), ('1500', {'windfall': 1500}), ('3000', {'windfall': 3000}), ('5000', {'windfall': 5000}), ('10000', {'windfall': 10000}))))
# 14 payoff milestones --------------------------------------------------------------------------------------------------------------------------------------------
def SCH(c): return 'IF({in:method}=%s,%s,%s)' % (tok('method', 'Snowball'), SS(c), SA(c))
def MS_N(p): return 'COUNTIF(%s,">"&%s*SUM(%s))+1' % (SCH('balance'), p, DB('balance'))
def MSD(p): return 'IF(%s>60,"",EOMONTH(%s,%s))' % (MS_N(p), MS, MS_N(p))
tools.append(TOOL('milestones', 'Payoff Milestones', 'When has half of the debt been paid',
    'The dates the total balance falls under the shares of today\'s debt you choose, for the payoff method you choose. An estimate from your numbers.', [
    IN('method', 'Payoff method', 'list', key('method', 'Avalanche'), list='method'), I('p1', 'First level, share of debt left', 0.75, 'pct'), I('p2', 'Second level, share of debt left', 0.5, 'pct'), I('p3', 'Third level, share of debt left', 0.25, 'pct')], [
    O('Total debt now', 'money', BAL()), O('First level: month number', 'int', MS_N('{in:p1}')), O('First level: date', 'date', MSD('{in:p1}')),
    O('Second level: month number', 'int', MS_N('{in:p2}')), O('Second level: date', 'date', MSD('{in:p2}')), O('Third level: month number', 'int', MS_N('{in:p3}')), O('Third level: date', 'date', MSD('{in:p3}')),
    O('Debt-free date by this method', 'date', 'IF({in:method}=%s,%s,%s)' % (tok('method', 'Snowball'), F1(SN('free_date')), F1(AV('free_date')))), O('Verdict', 'text', vd('Half paid by the date shown'))],
    GR('What if the first level is', ('90 percent left', {'p1': 0.9}), ('75 percent left', {'p1': 0.75}), ('60 percent left', {'p1': 0.6}))))
# 15 balance trend -----------------------------------------------------------------------------------------------------------------------------------------------
H = lambda c, back: 'SUMIFS(%s,%s,EDATE(%s,-%s))' % (HI(c), HI('month'), MS, back)
tools.append(TOOL('trend', 'Balance Trend', 'Is our total debt going down',
    'The total debt this month against the month you choose and against a year ago, split into cards and loans, from the Balance history sheet.', [I('back', 'Months back to compare', 3, 'int')], [
    O('Total debt now', 'money', H('total_debt', 0)), O('Total debt then', 'money', H('total_debt', '{in:back}')), O('Change since then', 'money', '%s-%s' % (H('total_debt', 0), H('total_debt', '{in:back}'))),
    O('Change since then, percent', 'pct', 'IFERROR((%s-%s)/%s,0)' % (H('total_debt', 0), H('total_debt', '{in:back}'), H('total_debt', '{in:back}'))), O('Total debt a year ago', 'money', H('total_debt', 12)),
    O('Change in the year', 'money', '%s-%s' % (H('total_debt', 0), H('total_debt', 12))), O('Card balances change since then', 'money', '%s-%s' % (H('cards', 0), H('cards', '{in:back}'))),
    O('Loan balances change since then', 'money', '%s-%s' % (H('loans', 0), H('loans', '{in:back}'))),
    O('Verdict', 'text', 'IF(%s<%s,%s,IF(%s>%s,%s,%s))' % (H('total_debt', 0), H('total_debt', '{in:back}'), vd('Total debt is down'), H('total_debt', 0), H('total_debt', '{in:back}'), vd('Total debt is up'), vd('Total debt is the same')))],
    GR('What if you compare with', ('1 month back', {'back': 1}), ('3 months back', {'back': 3}), ('6 months back', {'back': 6}), ('12 months back', {'back': 12}), ('24 months back', {'back': 24}))))
# 16 loan end check -------------------------------------------------------------------------------------------------------------------------------------------------
LR = lambda c: 'INDEX(%s,{in:row})' % DB(c)
ELAP = '((YEAR({today})-YEAR(%s))*12+MONTH({today})-MONTH(%s))' % (LR('opened'), LR('opened')); LEFT16 = 'MAX(0,%s-%s)' % (LR('term_months'), ELAP)
NEED16 = '-PMT(%s/12,%s,%s)' % (LR('rate'), LEFT16, LR('balance'))
N16 = 'ROUNDUP(NPER(MAX(%s/12,0.000000001),-(%s+{in:extra}),%s),0)' % (LR('rate'), LR('min_payment'), LR('balance'))
tools.append(TOOL('loan_end', 'Loan End Check', 'When does this loan end and is the payment enough',
    'Pick a loan by its row number in the Debts sheet: the months left at the payment you make (with an extra if you type one), the end date, and the payment needed to end when the term ends.', [
    I('row', 'Debt row number in the Debts sheet', 4, 'int'), I('extra', 'Extra payment a month on it', 0)], [
    O('Loan', 'text', LR('debt')), O('Balance', 'money', LR('balance')), O('Payment a month', 'money', LR('min_payment')), O('Months left at the payment and extra', 'int', N16),
    O('End date at the payment and extra', 'date', 'EOMONTH(%s,%s)' % (MS, N16)), O('Months left on the term', 'int', LEFT16), O('Payment needed to end with the term', 'money', NEED16),
    O('Months saved by the extra', 'int', 'ROUNDUP(NPER(MAX(%s/12,0.000000001),-%s,%s),0)-%s' % (LR('rate'), LR('min_payment'), LR('balance'), N16)),
    O('Verdict', 'text', 'IF(%s+{in:extra}>=%s-0.5,%s,%s)' % (LR('min_payment'), NEED16, vd('Ends on schedule'), vd('Check the payment')))],
    GR('What if the extra payment is', ('Nothing', {'extra': 0}), ('50', {'extra': 50}), ('100', {'extra': 100}), ('200', {'extra': 200}), ('400', {'extra': 400}))))
# 17 debt or savings ------------------------------------------------------------------------------------------------------------------------------------------------
MON17 = '{in:fund}/{in:essential}'
tools.append(TOOL('debt_or_save', 'Debt or Savings Balance', 'Extra to debt or to the emergency fund first',
    'The emergency fund in months of essential spending against a typical range, check your own numbers, and what 1,000 on the highest rate saves in a year.', [
    I('fund', 'Emergency fund balance', D.EMERGENCY), I('essential', 'Essential spending a month', D.ESSENTIAL), I('put', 'Amount you can add each month', 300)], [
    O('Emergency fund in months', 'num', MON17), O('Typical range, low end, months', 'int', '{set:emergency_low}'), O('Typical range, high end, months', 'int', '{set:emergency_high}'),
    O('Amount to reach the low end', 'money', 'MAX(0,{set:emergency_low}*{in:essential}-{in:fund})'), O('Months to reach the low end at your amount', 'num', 'IFERROR(MAX(0,{set:emergency_low}*{in:essential}-{in:fund})/{in:put},0)'),
    O('Highest rate on your debts', 'pct', 'SUMPRODUCT(MAX((%s>0)*%s))' % (DB('balance'), DB('rate'))), O('Interest a year on 1,000 at that rate', 'money', '1000*SUMPRODUCT(MAX((%s>0)*%s))' % (DB('balance'), DB('rate'))),
    O('Verdict', 'text', 'IF(%s<{set:emergency_low},%s,%s)' % (MON17, vd('Fund the emergency fund first'), vd('Debt first, typical range only')))],
    GR('What if the emergency fund balance is', ('5000', {'fund': 5000}), ('11800', {'fund': 11800}), ('15000', {'fund': 15000}), ('20000', {'fund': 20000}), ('30000', {'fund': 30000}))))
# 18 payoff sensitivity ----------------------------------------------------------------------------------------------------------------------------------------------
def XM(sign, c): return 'INDEX(%s,MATCH(%sVALUE({in:step}),%s,0))' % (XT(c), sign, XT('offset'))
def XZ(c): return 'INDEX(%s,MATCH(0,%s,0))' % (XT(c), XT('offset'))
tools.append(TOOL('sensitivity', 'Payoff Sensitivity', 'What does each step of extra payment change',
    'The same avalanche plan with the extra payment moved down and up by the step you choose (50, 100 or 200): months, debt-free date and interest at each, and what each step up saves.', [
    IN('step', 'Step size', 'list', key('stepsz', '100'), list='stepsz')], [
    O('Months, extra down one step', 'int', 'IFERROR(%s,"")' % XM('-', 'months')), O('Months at the Settings amount', 'int', XZ('months')), O('Months, extra up one step', 'int', 'IFERROR(%s,"")' % XM('', 'months')),
    O('Interest, extra down one step', 'money', 'IFERROR(%s,"")' % XM('-', 'interest')), O('Interest at the Settings amount', 'money', XZ('interest')), O('Interest, extra up one step', 'money', 'IFERROR(%s,"")' % XM('', 'interest')),
    O('Months saved by one step up', 'int', 'IFERROR(%s-%s,"")' % (XZ('months'), XM('', 'months'))), O('Interest saved by one step up', 'money', 'IFERROR(%s-%s,"")' % (XZ('interest'), XM('', 'interest'))),
    O('Debt-free date, extra up one step', 'date', 'IFERROR(%s,"")' % XM('', 'debt_free')),
    O('Verdict', 'text', 'IF(ISNUMBER(%s),%s,%s)' % (XM('', 'months'), vd('Extra payment shortens the plan'), vd('Type 50, 100 or 200')))]))
assert len(tools) == 18, len(tools)
