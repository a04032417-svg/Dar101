"""Doula business suite part 3: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du3_lists import *
import du3_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
UN, PD = tok('istatus', 'Unpaid'), tok('istatus', 'Paid')
PIF, INS = tok('plan', 'Pay in full'), tok('plan', 'Instalments')
CAN, SIG = tok('ctstatus', 'Cancelled'), tok('ctstatus', 'Signed')
KPP = tok('ckind', 'Postpartum'); BOOKED = tok('cstatus', 'Booked')
B0, B1, B2, B3 = [tok('band', b) for b in AGE[:4]]
CARD, LINK, BANK, CASH = [tok('method', m) for m in ('Card payment', 'Payment link', 'Bank transfer', 'Cash')]
def MX(rng, col, val): return 'MATCH(%s,{range:%s.%s},0)' % (val, rng, col)
tools = []

# 1 ------------------------------------------------------------ deposit and balance tracker
OVD = 'SUM({range:contracts.overdue_amount})'
TOPR = 'MATCH(1,{range:balances.rank},0)'
DS = ('SUMIFS({range:instalments.amount},{range:instalments.status},%s,{range:instalments.due_date},">="&{today},{range:instalments.due_date},"<="&({today}+{in:soon}))'
      '+SUMIFS({range:contracts.balance},{range:contracts.plan},%s,{range:contracts.status},%s,{range:contracts.balance_due},">="&{today},{range:contracts.balance_due},"<="&({today}+{in:soon}))') % (UN, PIF, SIG)
tools.append(TOOL('deposit_track', 'Deposit and Balance Tracker', 'Which deposits and balances need a call today',
    'Type how many days ahead count as due soon and the smallest overdue amount worth a call; see deposits unpaid, balances overdue in the ageing bands 0 to 30, 31 to 60 and 61 or more days, and who to chase first.', [
    I('soon', 'Days ahead that count as due soon', 30, 'int'), I('min_chase', 'Smallest overdue amount worth a call', 100)], [
    O('Deposits due and unpaid', 'int', 'COUNTIFS({range:deposits.status},%s)+COUNTIFS({range:deposits.status},%s)' % (ca('Deposit due'), ca('Deposit overdue'))),
    O('Deposit amount unpaid', 'money', 'SUMIFS({range:deposits.deposit},{range:deposits.status},%s)+SUMIFS({range:deposits.deposit},{range:deposits.status},%s)' % (ca('Deposit due'), ca('Deposit overdue'))),
    O('Balances overdue', 'money', OVD), O('Clients overdue', 'int', 'COUNTIFS({range:contracts.overdue_amount},">0")'),
    O('Clients overdue by the amount you set or more', 'int', 'COUNTIFS({range:contracts.overdue_amount},">="&{in:min_chase})'),
    O('Balances and instalments due in the days you set', 'money', DS),
    O('Overdue 0 to 30 days late', 'money', 'SUMIFS({range:contracts.overdue_amount},{range:contracts.ageing_band},%s)' % B1),
    O('Overdue 31 to 60 days late', 'money', 'SUMIFS({range:contracts.overdue_amount},{range:contracts.ageing_band},%s)' % B2),
    O('Overdue 61 days or more late', 'money', 'SUMIFS({range:contracts.overdue_amount},{range:contracts.ageing_band},%s)' % B3),
    O('Oldest overdue, days', 'int', 'MAX({range:contracts.overdue_days})'),
    O('Chase first', 'text', 'IF(%s=0,"-",IFERROR(INDEX({range:balances.client},%s),"-"))' % (OVD, TOPR)),
    O('Amount overdue, first client', 'money', 'IFERROR(INDEX({range:balances.overdue_amount},%s),0)' % TOPR), O('Days overdue, first client', 'int', 'IFERROR(INDEX({range:balances.overdue_days},%s),0)' % TOPR),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&": "&IFERROR(INDEX({range:balances.client},%s),"-"))' % (OVD, va('Nothing overdue'), va('Chase first'), TOPR))],
    GR('What if', ('Due in the next 7 days', {'soon': 7}), ('Due in the next 14 days', {'soon': 14}), ('Due in the next 60 days', {'soon': 60}), ('Call only at 500 or more', {'min_chase': 500}), ('Call only at 1,000 or more', {'min_chase': 1000}))))

# 2 ------------------------------------------------------------ payment plan builder
OS2 = '({in:edd}-{set:oncall_before_days})'
FITN = 'IF(%s>{in:start},MIN({in:parts},INT((%s-1-{in:start})/{in:gap})+1),0)' % (OS2, OS2)
FITMAX = 'IF(%s>{in:start},MIN(6,INT((%s-1-{in:start})/{in:gap})+1),0)' % (OS2, OS2)
tools.append(TOOL('plan_builder', 'Payment Plan Builder', 'Does this payment plan end before the window opens',
    'Type the balance, the number of instalments, the first date, the days between and the estimated due date; see the schedule, the on-call start and what would still be unpaid when the window opens.', [
    I('balance', 'Balance to split', 1330), I('parts', 'Number of instalments, 2 to 6', 3, 'int'), I('start', 'First instalment date', ahead(7), 'date'), I('gap', 'Days between instalments', 28, 'int'),
    I('edd', 'Estimated due date (a date the client gives)', ahead(120), 'date')], [
    O('On-call start', 'date', OS2), O('Balance due date at the balance weeks', 'date', '{in:edd}-7*{set:balance_weeks}'), O('Instalment amount', 'money', 'ROUND({in:balance}/{in:parts},2)'),
    O('Second instalment due', 'date', '{in:start}+{in:gap}'), O('Last instalment due', 'date', '{in:start}+{in:gap}*({in:parts}-1)'), O('Days before the window the plan ends', 'int', '%s-({in:start}+{in:gap}*({in:parts}-1))' % OS2),
    O('Instalments that fit before the window', 'int', FITN), O('Unpaid when the window opens', 'money', '({in:parts}-%s)*ROUND({in:balance}/{in:parts},2)' % FITN),
    O('Most instalments that fit at this gap', 'int', 'MAX(1,%s)' % FITMAX), O('Latest first instalment date for this plan', 'date', '%s-1-{in:gap}*({in:parts}-1)' % OS2),
    O('Longest gap in days that still fits', 'int', 'MAX(0,INT((%s-1-{in:start})/({in:parts}-1)))' % OS2), O('Share of the balance paid before the window', 'pct', '%s/{in:parts}' % FITN),
    O('Gap you set for all plans', 'int', '{set:instalment_days}'),
    O('Verdict', 'text', 'IF(%s>={in:parts},%s,IF(%s>=2,%s&": "&%s,%s))' % (FITN, va('Plan fits'), FITMAX, va('Use fewer instalments'), FITMAX, va('Start earlier')))],
    GR('What if', ('Two instalments', {'parts': 2}), ('Four instalments', {'parts': 4}), ('Six instalments', {'parts': 6}), ('Start 60 days later', {'start': '={today}+67'}), ('Due date in 60 days', {'edd': '={today}+60'}), ('45 days between', {'gap': 45}))))

# 3 ------------------------------------------------------------ prepaid earned vs unearned
M3 = 'MATCH({in:client},{range:unearned_client.client},0)'
def U3(c, d='0'): return 'IFERROR(INDEX({range:unearned_client.%s},%s),%s)' % (c, M3, d)
AFT3 = '(%s+%s*(IF(%s>0,MIN(1,(%s+{in:extra})/%s)-MIN(1,%s/%s),0)))' % (U3('earned'), U3('pack_price'), U3('pack_hours'), U3('pack_used'), U3('pack_hours', '1'), U3('pack_used'), U3('pack_hours', '1'))
tools.append(TOOL('prepaid', 'Prepaid Earned vs Unearned', 'How much of this prepaid cash is still unearned',
    'Type a client and the hours you will deliver next month; see the cash paid, what is earned by phase and by pack hours used, the unearned cash (money received for work not yet done) and the total held for all open clients.', [
    I('client', 'Client name', ST['prepaid_client'] if False else D.ST['prepaid_client'], 'text'), I('extra', 'Hours you deliver next month', 20, 'num')], [
    O('Price', 'money', U3('price')), O('Paid so far', 'money', U3('paid')), O('Earned to date', 'money', U3('earned')), O('Unearned cash', 'money', U3('unearned')), O('Unearned share of the cash paid', 'pct', U3('unearned_share')),
    O('Pack hours bought', 'num', U3('pack_hours')), O('Pack hours used', 'num', U3('pack_used')), O('Pack hours left', 'num', '%s-%s' % (U3('pack_hours'), U3('pack_used'))),
    O('Earned after the extra hours', 'money', AFT3), O('Unearned after the extra hours', 'money', 'MAX(0,%s-%s)' % (U3('paid'), AFT3)),
    O('Pack expires on', 'date', 'IFERROR(INDEX({range:packs.expires_on},MATCH({in:client},{range:packs.client},0)),{today})'),
    O('Unearned cash, all open clients', 'money', 'SUM({range:unearned_client.unearned})'), O('Open clients holding unearned cash', 'int', 'COUNTIFS({range:unearned_client.unearned},">0")'),
    O('Largest unearned balance', 'text', 'IFERROR(INDEX({range:unearned_client.client},MATCH(MAX({range:unearned_client.unearned}),{range:unearned_client.unearned},0)),"-")'),
    O('Verdict', 'text', 'IF(%s>0,%s&" "&ROUND(%s,0),%s)' % (U3('unearned'), va('Keep aside'), U3('unearned'), va('Nothing unearned')))],
    GR('What if', ('Deliver 40 hours next month', {'extra': 40}), ('Deliver 80 hours', {'extra': 80}), ('Deliver all 106 hours left', {'extra': 106}), ('Deliver nothing', {'extra': 0}))))

# 4 ------------------------------------------------------------ refund and change analyser
C12 = 'COUNTIFS({range:contracts.signed_on},">="&({today}-365),{range:contracts.signed_on},"<="&{today})'
H12 = 'COUNTIFS({range:cancels.date},">="&({today}-365))'
def K12(k): return 'COUNTIFS({range:cancels.date},">="&({today}-365),{range:cancels.kind},%s)' % tok('cxkind', k)
S12 = lambda c: 'SUMIFS({range:cancels.%s},{range:cancels.date},">="&({today}-365))' % c
TOPREASON = 'IFERROR(INDEX({range:refund_reasons.reason},MATCH(MAX({range:refund_reasons.count}),{range:refund_reasons.count},0)),"-")'
tools.append(TOOL('refund_tool', 'Refund and Change Analyser', 'Is the change rate inside your setting',
    'Type the highest change rate you accept and the contracts you expect next year; see the last 12 months of cancellations, package changes and hour cuts, the cash kept and refunded, the top reason and the expected refunds.', [
    I('rate_max', 'Highest change rate you accept', 0.12, 'pct'), I('next', 'Contracts you expect to sign in the next 12 months', 120, 'int')], [
    O('Contracts signed, last 12 months', 'int', C12), O('Changes and cancellations, last 12 months', 'int', H12), O('Change and cancellation rate', 'pct', 'IFERROR(%s/%s,0)' % (H12, C12)),
    O('Rate you accept', 'pct', '{in:rate_max}'), O('Cancellations', 'int', K12('Cancelled')), O('Package changes', 'int', K12('Package changed')), O('Hours reduced', 'int', K12('Hours reduced')),
    O('Cash paid by those clients', 'money', S12('paid')), O('Amount kept', 'money', S12('kept')), O('Amount refunded', 'money', S12('refunded')), O('Refunded share of the cash paid', 'pct', 'IFERROR(%s/%s,0)' % (S12('refunded'), S12('paid'))),
    O('Top reason by number of changes', 'text', TOPREASON), O('Changes expected in the next 12 months', 'num', '{in:next}*IFERROR(%s/%s,0)' % (H12, C12)),
    O('Refunds expected in the next 12 months', 'money', '{in:next}*IFERROR(%s/%s,0)*IFERROR(%s/%s,0)' % (H12, C12, S12('refunded'), H12)),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s,0)<={in:rate_max},%s,%s)&": "&%s' % (H12, C12, va('Rate inside the setting'), va('Rate above the setting'), TOPREASON))],
    GR('What if', ('Accept only 8 percent', {'rate_max': 0.08}), ('Accept 15 percent', {'rate_max': 0.15}), ('80 contracts next year', {'next': 80}), ('200 contracts next year', {'next': 200}))))

# 5 ------------------------------------------------------------ cancellation settlement
M5 = 'MATCH({in:client},{range:contracts.client},0)'
def C5(c, d='0'): return 'IFERROR(INDEX({range:contracts.%s},%s),%s)' % (c, M5, d)
DAYS5 = 'IFERROR(%s-{in:cancel_on},999)' % C5('window_start')
SHARE5 = 'IF(%s<=0,1,IF(%s<30,{in:keep_b},IF(%s<60,{in:keep_a},0)))' % (DAYS5, DAYS5, DAYS5)
EARN5 = 'IFERROR(INDEX({range:unearned_client.earned},MATCH({in:client},{range:unearned_client.client},0)),0)'
KEPT5 = 'MIN(%s,IF(%s=%s,%s,MAX(%s,%s+%s*MAX(0,%s-%s))))' % (C5('paid_to_date'), C5('kind', '""'), KPP, EARN5, EARN5, C5('deposit'), SHARE5, C5('paid_to_date'), C5('deposit'))
tools.append(TOOL('cancel_settle', 'Cancellation Settlement', 'What you keep and refund if this client cancels today',
    'Type a client, the cancellation date and the share of the cash beyond the deposit you keep 30 to 59 days and under 30 days before the on-call start; see the cash kept, the refund and the unearned cash released.', [
    I('client', 'Client name', 'Ngozi Nwosu', 'text'), I('cancel_on', 'Cancellation date', ahead(0), 'date'), I('keep_a', 'Share kept beyond the deposit, 30 to 59 days before', 0.25, 'pct'), I('keep_b', 'Share kept beyond the deposit, under 30 days before', 0.50, 'pct')], [
    O('Package', 'text', C5('package', '"-"')), O('Price', 'money', C5('price')), O('Paid so far', 'money', C5('paid_to_date')), O('Deposit', 'money', C5('deposit')), O('Days to the on-call start', 'int', DAYS5),
    O('Share kept beyond the deposit', 'pct', SHARE5), O('Earned to date', 'money', EARN5), O('Cash kept', 'money', KEPT5), O('Refund', 'money', '%s-%s' % (C5('paid_to_date'), KEPT5)),
    O('Unearned cash released', 'money', 'MAX(0,%s-%s)' % (C5('paid_to_date'), EARN5)), O('Revenue recognised from the cash kept', 'money', 'MAX(0,%s-%s)' % (KEPT5, EARN5)),
    O('Price you will not collect', 'money', '%s-%s' % (C5('price'), KEPT5)),
    O('Verdict', 'text', 'IF(%s-%s>0,%s&" "&ROUND(%s-%s,0),%s)' % (C5('paid_to_date'), KEPT5, va('Refund due'), C5('paid_to_date'), KEPT5, va('Keep everything')))],
    GR('What if', ('Cancel in 40 days', {'cancel_on': '={today}+40'}), ('Cancel in 70 days', {'cancel_on': '={today}+70'}), ('Cancel in 120 days', {'cancel_on': '={today}+120'}), ('Keep 50 and 75 percent', {'keep_a': 0.5, 'keep_b': 0.75}), ('Keep only the deposit', {'keep_a': 0.0, 'keep_b': 0.0}))))

# 6 ------------------------------------------------------------ overdue chase ranking
def RK(k, c, d): return 'IFERROR(INDEX({range:balances.%s},MATCH(%d,{range:balances.rank},0)),%s)' % (c, k, d)
outs6 = []
for k in range(1, 6):
    outs6 += [O('Rank %d client' % k, 'text', RK(k, 'client', '"-"')), O('Rank %d overdue amount' % k, 'money', RK(k, 'overdue_amount', '0')), O('Rank %d days overdue' % k, 'int', RK(k, 'overdue_days', '0'))]
outs6 += [O('Overdue in total', 'money', OVD), O('Clients overdue for the days you set or more', 'int', 'COUNTIFS({range:balances.overdue_days},">="&{in:min_days})'),
          O('Share of the overdue amount in the top 3', 'pct', 'IFERROR((%s+%s+%s)/%s,0)' % (RK(1, 'overdue_amount', '0'), RK(2, 'overdue_amount', '0'), RK(3, 'overdue_amount', '0'), OVD)),
          O('Verdict', 'text', 'IF(%s=0,%s,%s&": "&%s)' % (OVD, va('Nothing overdue'), va('Chase first'), RK(1, 'client', '"-"')))]
tools.append(TOOL('chase_rank', 'Overdue Chase Ranking', 'Which unpaid balances to chase first',
    'Type the days overdue before you chase; the five unpaid balances with the highest amount times days overdue are ranked, with the share of the overdue money they hold and the client to call first.', [
    I('min_days', 'Days overdue before you chase', 1, 'int')], outs6,
    GR('What if', ('Chase after 7 days', {'min_days': 7}), ('Chase after 15 days', {'min_days': 15}), ('Chase after 30 days', {'min_days': 30}), ('Chase after 61 days', {'min_days': 61}))))

# 7 ------------------------------------------------------------ balance reminder timing
NXT7 = 'SMALL({range:balances.balance_due},COUNTIF({range:balances.balance_due},"<"&{today})+1)'
D2 = '{range:balances.balance_due},">="&{today},{range:balances.balance_due},"<="&({today}+{in:d2})'
D1 = '{range:balances.balance_due},">="&{today},{range:balances.balance_due},"<="&({today}+{in:d1})'
EX1 = '{range:balances.balance_due},{today}+{in:d1}'
REM7 = 'COUNTIFS(%s)+COUNTIFS(%s)+COUNTIFS({range:balances.overdue_amount},">0")' % (D2, EX1)
tools.append(TOOL('reminder_timing', 'Balance Reminder Timing', 'Who to remind today, this week and tomorrow',
    'Type the days before the due date for your first and last reminder; see the payments due soon, who is next, the reminders to send today and the overdue balances that need a call instead.', [
    I('d1', 'First reminder, days before the due date', 7, 'int'), I('d2', 'Last reminder, days before the due date', 1, 'int')], [
    O('Payments overdue now', 'int', 'COUNTIFS({range:balances.overdue_amount},">0")'), O('Payments due within the last reminder days', 'int', 'COUNTIFS(%s)' % D2),
    O('Amount due within the last reminder days', 'money', 'SUMIFS({range:balances.outstanding},%s)' % D2), O('Payments due exactly on the first reminder day', 'int', 'COUNTIFS(%s)' % EX1),
    O('Payments due within the first reminder days', 'int', 'COUNTIFS(%s)' % D1), O('Balance outstanding for those payments', 'money', 'SUMIFS({range:balances.outstanding},%s)' % D1),
    O('Next payment due', 'date', 'IFERROR(%s,{today})' % NXT7), O('Days until it is due', 'int', 'IFERROR(%s-{today},0)' % NXT7),
    O('Next client to remind', 'text', 'IFERROR(INDEX({range:balances.client},MATCH(%s,{range:balances.balance_due},0)),"-")' % NXT7),
    O('Balance outstanding for that client', 'money', 'IFERROR(INDEX({range:balances.outstanding},MATCH(%s,{range:balances.balance_due},0)),0)' % NXT7),
    O('Reminder days in your settings', 'int', '{set:reminder_days}'), O('Reminders and calls to make today', 'int', REM7),
    O('Verdict', 'text', 'IF(%s>0,%s&": "&(%s),%s)' % (REM7, va('Send reminders today'), REM7, va('No reminder today')))],
    GR('What if', ('First reminder 14 days before', {'d1': 14}), ('First reminder 30 days before', {'d1': 30}), ('Last reminder 3 days before', {'d2': 3}), ('Last reminder on the day', {'d2': 0}))))

# 8 ------------------------------------------------------------ payment plan risk check
tools.append(TOOL('plan_risk', 'Payment Plan Risk Check', 'Which payment plans end too late or run late',
    'Type how many days before the on-call start a plan should end and how many days late a payment counts as late; see the plans that end late, plans with an overdue instalment and the share of instalments paid late.', [
    I('margin', 'Days a plan should end before the window', 7, 'int'), I('late_after', 'Days after the due date that count as late', 7, 'int')], [
    O('Clients on a payment plan', 'int', 'COUNTIFS({range:inst_window.n_inst},">0")'), O('Plans ending after the window starts', 'int', 'COUNTIFS({range:inst_window.days_before},"<0")'),
    O('Plans ending within the margin you set', 'int', 'COUNTIFS({range:inst_window.days_before},">=0",{range:inst_window.days_before},"<"&{in:margin})'),
    O('Plans with an overdue instalment', 'int', 'COUNTIFS({range:inst_window.overdue_unpaid},">0")'),
    O('Plans to move or chase', 'int', 'COUNTIFS({range:inst_window.days_before},"<"&{in:margin})+COUNTIFS({range:inst_window.overdue_unpaid},">0",{range:inst_window.days_before},">="&{in:margin})'),
    O('Unpaid amount on plans that end too late', 'money', 'SUMIFS({range:inst_window.unpaid_amount},{range:inst_window.days_before},"<"&{in:margin})'),
    O('Plan that ends closest to the window', 'text', 'IFERROR(INDEX({range:inst_window.client},MATCH(MIN({range:inst_window.days_before}),{range:inst_window.days_before},0)),"-")'),
    O('Fewest days before the window', 'int', 'MIN({range:inst_window.days_before})'), O('Average days before the window', 'num', 'AVERAGE({range:inst_window.days_before})'),
    O('Instalments paid later than the days you set', 'int', 'COUNTIFS({range:instalments.days_late},">"&{in:late_after},{range:instalments.status},%s)' % PD),
    O('Share of paid instalments that were late', 'pct', 'IFERROR(COUNTIFS({range:instalments.days_late},">"&{in:late_after},{range:instalments.status},%s)/COUNTIFS({range:instalments.status},%s),0)' % (PD, PD)),
    O('Verdict', 'text', 'IF(COUNTIFS({range:inst_window.days_before},"<"&{in:margin})+COUNTIFS({range:inst_window.overdue_unpaid},">0",{range:inst_window.days_before},">="&{in:margin})>0,%s&": "&(COUNTIFS({range:inst_window.days_before},"<"&{in:margin})+COUNTIFS({range:inst_window.overdue_unpaid},">0",{range:inst_window.days_before},">="&{in:margin})),%s)' % (va('Move dates earlier'), va('All plans fit')))],
    GR('What if', ('Plans should end 14 days before', {'margin': 14}), ('Plans should end 30 days before', {'margin': 30}), ('Plans may end on the day', {'margin': 0}), ('Late means 3 days', {'late_after': 3}), ('Late means 14 days', {'late_after': 14}))))

# 9 ------------------------------------------------------------ cash receipts forecast
FAC = '({set:on_time_share}+IF({in:scen}=%s,0.1,IF({in:scen}=%s,-0.15,0)))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
def WK(k): return 'SUMIFS({range:instalments.amount},{range:instalments.due_week},%d)+SUMIFS({range:contracts.balance},{range:contracts.due_week},%d)' % (k, k)
def EXP(k): return '(%s%s)*%s' % (WK(k), ('+%s/4' % OVD) if k <= 4 else '', FAC)
FIRSTGAP = '0'
for k in range(12, 0, -1): FIRSTGAP = 'IF((%s)<{in:week_min},%d,%s)' % (WK(k), k, FIRSTGAP)
TOT12 = '+'.join('(%s)' % EXP(k) for k in range(1, 13))
tools.append(TOOL('cash_forecast', 'Cash Receipts Forecast', 'How much cash arrives in each of the next 12 weeks',
    'Pick Base, Best or Worst and the lowest weekly receipts you can live with; instalments and balances due in the next 12 weeks and the overdue amount are set against your own on-time share and the first thin week is named.', [
    IN('scen', 'Scenario', 'list', key('scen', 'Base'), list='scen'), I('week_min', 'Lowest weekly receipts you can live with', 1000)],
    [O('Week %d receipts expected' % k, 'money', 'ROUND(%s,0)' % EXP(k)) for k in range(1, 13)] + [
    O('Receipts expected in the next 12 weeks', 'money', 'ROUND(%s,0)' % TOT12), O('Instalments and balances due in 12 weeks, face value', 'money', 'SUM({range:instalments.amount})*0+' + '+'.join('(%s)' % WK(k) for k in range(1, 13))),
    O('Overdue amount still to collect', 'money', OVD), O('Share of the money expected on time', 'pct', FAC), O('First week below your minimum', 'int', FIRSTGAP),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&(%s))' % (FIRSTGAP, va('Cash arrives every week'), va('Gap in week'), FIRSTGAP))][:20],
    GR('What if', ('Best case', {'scen': '=' + tok('scen', 'Best')}), ('Worst case', {'scen': '=' + tok('scen', 'Worst')}), ('Need 2,500 a week', {'week_min': 2500}), ('Need 500 a week', {'week_min': 500}))))

# 10 ----------------------------------------------------------- deposit share test
OWNC = 'IFERROR(INDEX({range:ct_status.contracts},MATCH(%s,{range:ct_status.status},0))/SUM({range:ct_status.contracts}),0)' % CAN
CURSH = 'IFERROR((SUM({range:contracts.deposit})-SUMIFS({range:contracts.deposit},{range:contracts.kind},%s))/(SUM({range:contracts.price})-SUMIFS({range:contracts.price},{range:contracts.kind},%s)),0)' % (KPP, KPP)
NEED = 'ROUNDUP(MAX(0,1-{in:max_loss}/{in:price})*20,0)/20'
outs10 = []
for s_ in (20, 30, 40, 50):
    outs10 += [O('Deposit at %d percent' % s_, 'money', '{in:price}*%s' % (s_ / 100)), O('Price not yet secured at %d percent' % s_, 'money', '{in:price}*(1-%s)' % (s_ / 100)),
               O('Expected loss at %d percent, own cancelled share' % s_, 'money', '{in:price}*(1-%s)*%s' % (s_ / 100, OWNC))]
outs10 += [O('Share of your contracts that were cancelled', 'pct', OWNC), O('Your current deposit share, birth and combined', 'pct', CURSH), O('Deposit share the loss you accept needs', 'pct', 'MAX(0,1-{in:max_loss}/{in:price})'),
           O('Needed share rounded up to the next 5 percent', 'pct', NEED),
           O('Verdict', 'text', 'IF(%s>%s+0.005,%s&" "&ROUND(%s*100,0)&"%%",%s)' % (NEED, CURSH, va('Raise the deposit to'), NEED, va('Keep the deposit')))]
tools.append(TOOL('deposit_share', 'Deposit Share Test', 'Is your deposit big enough if a client cancels',
    'Type a package price and the largest loss you accept if the client cancels; see the cash at signing for deposits of 20, 30, 40 and 50 percent, the price left unsecured and the deposit share your own history needs.', [
    I('price', 'Package price', 1900), I('max_loss', 'Largest loss you accept if a client cancels', 1300)], outs10[:20],
    GR('What if', ('Price 1,400', {'price': 1400}), ('Price 2,400', {'price': 2400}), ('Price 4,400', {'price': 4400}), ('Accept a loss of 800', {'max_loss': 800}), ('Accept a loss of 2,000', {'max_loss': 2000}))))

# 11 ----------------------------------------------------------- prepay discount break-even
R11 = '({in:cash_cost}*{in:months}/12)'
NET11 = '({in:price}*(1-{in:disc})*%s-{in:price}*{in:disc})' % R11
tools.append(TOOL('prepay_discount', 'Prepay Discount Break-even', 'Is a discount for paying in full worth the earlier cash',
    'Type the price, the discount, how many months earlier the cash arrives and what money costs you a year; see the discount you give, the value of the earlier cash, the break-even discount and months, and the yearly effect.', [
    I('price', 'Package price', 1900), I('disc', 'Discount for paying in full', 0.05, 'pct'), I('months', 'Months earlier the cash arrives', 3, 'num'), I('cash_cost', 'What money costs you a year', 0.10, 'pct'), I('takeup', 'Share of clients who would prepay', 0.25, 'pct')], [
    O('Discount given per client', 'money', '{in:price}*{in:disc}'), O('Value of the earlier cash per client', 'money', '{in:price}*(1-{in:disc})*%s' % R11), O('Net gain or loss per client', 'money', NET11),
    O('Break-even discount, closed form', 'pct', '%s/(1+%s)' % (R11, R11)), O('Break-even months at this discount', 'num', '{in:disc}/(1-{in:disc})/{in:cash_cost}*12'),
    O('Share of your contracts on instalments', 'pct', 'IFERROR(COUNTIFS({range:contracts.plan},%s)/COUNTIFS({range:contracts.contract_id},"<>"),0)' % INS),
    O('Contracts signed, last 12 months', 'int', 'COUNTIFS({range:contracts.signed_on},">="&({today}-365),{range:contracts.signed_on},"<="&{today})'),
    O('Clients who would prepay in a year', 'num', '{in:takeup}*COUNTIFS({range:contracts.signed_on},">="&({today}-365),{range:contracts.signed_on},"<="&{today})'),
    O('Yearly discount cost', 'money', '{in:takeup}*COUNTIFS({range:contracts.signed_on},">="&({today}-365),{range:contracts.signed_on},"<="&{today})*{in:price}*{in:disc}'),
    O('Yearly net gain or loss', 'money', '{in:takeup}*COUNTIFS({range:contracts.signed_on},">="&({today}-365),{range:contracts.signed_on},"<="&{today})*%s' % NET11),
    O('Verdict', 'text', 'IF(%s>=0,%s,%s)' % (NET11, va('Offer the discount'), va('Do not offer the discount')))],
    GR('What if', ('Discount 2 percent', {'disc': 0.02}), ('Discount 3 percent', {'disc': 0.03}), ('Cash arrives 6 months earlier', {'months': 6}), ('Cash arrives 9 months earlier', {'months': 9}), ('Money costs 20 percent', {'cash_cost': 0.2}))))

# 12 ----------------------------------------------------------- contract change impact
OLD12, PAID12 = C5('price'), C5('paid_to_date')
NEWDEP = '({in:new_price}*{in:dep_pct})'
BAL12 = 'MAX(0,{in:new_price}-MAX(%s,%s))' % (PAID12, NEWDEP)
REF12 = 'MAX(0,%s-{in:new_price})' % PAID12
tools.append(TOOL('contract_change', 'Contract Change Impact', 'What a package upgrade or downgrade means in cash',
    'Type a client, the new price, the new deposit share and the instalments; see the difference, the deposit to collect now, the balance left, the new instalment and whether you collect or refund.', [
    I('client', 'Client name', 'Ngozi Nwosu', 'text'), I('new_price', 'Price of the new package', 2400), I('dep_pct', 'Deposit share of the new package', 0.30, 'pct'), I('parts', 'Instalments for the new balance', 3, 'int')], [
    O('Package now', 'text', C5('package', '"-"')), O('Price now', 'money', OLD12), O('Paid so far', 'money', PAID12), O('Difference in price', 'money', '{in:new_price}-%s' % OLD12), O('New deposit', 'money', NEWDEP),
    O('Collect now to reach the new deposit', 'money', 'MAX(0,%s-%s)' % (NEWDEP, PAID12)), O('Balance after the change', 'money', BAL12), O('New instalment amount', 'money', 'ROUND(%s/{in:parts},2)' % BAL12),
    O('Refund if the new price is below the cash paid', 'money', REF12), O('Old balance outstanding', 'money', C5('balance')),
    O('Verdict', 'text', 'IF(%s>0,%s&" "&ROUND(%s,0),IF({in:new_price}-%s>0,%s&" "&ROUND({in:new_price}-%s,0),IF({in:new_price}-%s<0,%s,%s)))' % (
        REF12, vb('Refund the difference'), REF12, OLD12, vb('Collect the difference'), OLD12, OLD12, vb('Balance falls'), vb('No change in price')))],
    GR('What if', ('Downgrade to 1,400', {'new_price': 1400}), ('Stay at 1,900', {'new_price': 1900}), ('Upgrade to 4,400', {'new_price': 4400}), ('Deposit 50 percent', {'dep_pct': 0.5}), ('Four instalments', {'parts': 4}))))

# 13 ----------------------------------------------------------- hour pack revenue release
ACT = '{range:packs.expires_on},">="&{today}'
NEAR13 = '{range:packs.days_to_expiry},">=0",{range:packs.days_to_expiry},"<="&{in:near_days},{range:packs.hours_left},">0"'
RATE13 = 'IFERROR(SUMIFS({range:packs.price},%s)/SUMIFS({range:packs.hours_bought},%s),0)' % (ACT, ACT)
tools.append(TOOL('pack_release', 'Hour Pack Revenue Release', 'How much pack cash you can release as earned',
    'Type the pack hours you delivered this month and the days that count as near expiry; see the cash earned, the unearned pack balance left, the packs near expiry with unused hours and who to chase.', [
    I('hours', 'Pack hours delivered this month', 160, 'num'), I('near_days', 'Days before expiry that count as near', 45, 'int')], [
    O('Average price per pack hour', 'money', RATE13), O('Earned by the hours delivered', 'money', '{in:hours}*%s' % RATE13), O('Unearned pack cash now', 'money', 'SUM({range:packs.unearned})'),
    O('Unearned pack cash after the release', 'money', 'MAX(0,SUM({range:packs.unearned})-{in:hours}*%s)' % RATE13),
    O('Packs still running', 'int', 'COUNTIFS(%s,{range:packs.hours_left},">0")' % ACT), O('Packs near expiry with hours left', 'int', 'COUNTIFS(%s)' % NEAR13),
    O('Unused hours in those packs', 'num', 'SUMIFS({range:packs.hours_left},%s)' % NEAR13), O('Cash held in those packs', 'money', 'SUMIFS({range:packs.unearned},%s)' % NEAR13),
    O('Hours that expired unused, last 12 months', 'num', 'SUMIFS({range:packs.hours_left},{range:packs.expires_on},"<"&{today},{range:packs.expires_on},">="&({today}-365))'),
    O('Pack with the most unused hours near expiry', 'text', 'IFERROR(INDEX({range:packs.client},MATCH(MAX(INDEX(({range:packs.days_to_expiry}>=0)*({range:packs.days_to_expiry}<={in:near_days})*{range:packs.hours_left},0)),INDEX(({range:packs.days_to_expiry}>=0)*({range:packs.days_to_expiry}<={in:near_days})*{range:packs.hours_left},0),0)),"-")'),
    O('Verdict', 'text', 'IF(SUMIFS({range:packs.hours_left},%s)>0,%s&" "&ROUND(SUMIFS({range:packs.hours_left},%s),0),%s&" "&ROUND({in:hours}*%s,0))' % (NEAR13, vb('Chase use of unused hours'), NEAR13, vb('Release the amount'), RATE13))],
    GR('What if', ('Deliver 80 hours', {'hours': 80}), ('Deliver 240 hours', {'hours': 240}), ('Near expiry means 14 days', {'near_days': 14}), ('Near expiry means 90 days', {'near_days': 90}))))

# 14 ----------------------------------------------------------- late-payer pattern
LP = D.late_payer()
IC = '{range:instalments.client},{in:client}'
tools.append(TOOL('late_payer', 'Late-Payer Pattern', 'Does this client pay instalments late',
    'Type a client and the days after the due date that count as late; see the instalments paid and unpaid, how many were late, the average and worst days late and whether to offer a standing payment instead.', [
    I('client', 'Client name', LP, 'text'), I('late_after', 'Days after the due date that count as late', 5, 'int')], [
    O('Instalments on the plan', 'int', 'COUNTIFS(%s)' % IC), O('Paid', 'int', 'COUNTIFS(%s,{range:instalments.status},%s)' % (IC, PD)), O('Unpaid', 'int', 'COUNTIFS(%s,{range:instalments.status},%s)' % (IC, UN)),
    O('Paid later than the days you set', 'int', 'COUNTIFS(%s,{range:instalments.days_late},">"&{in:late_after},{range:instalments.status},%s)' % (IC, PD)),
    O('Average days late, paid instalments', 'num', 'IFERROR(AVERAGEIFS({range:instalments.days_late},%s,{range:instalments.status},%s),0)' % (IC, PD)),
    O('Worst days late', 'int', 'SUMPRODUCT(MAX(({range:instalments.client}={in:client})*({range:instalments.paid_on}>0)*({range:instalments.paid_on}-{range:instalments.due_date})))'),
    O('Unpaid amount', 'money', 'SUMIFS({range:instalments.amount},%s,{range:instalments.status},%s)' % (IC, UN)),
    O('Share of all paid instalments that were late', 'pct', 'IFERROR(COUNTIFS({range:instalments.days_late},">"&{in:late_after},{range:instalments.status},%s)/COUNTIFS({range:instalments.status},%s),0)' % (PD, PD)),
    O('Average days late, all clients', 'num', 'IFERROR(AVERAGEIFS({range:instalments.days_late},{range:instalments.status},%s),0)' % PD),
    O('Verdict', 'text', 'IF(OR(COUNTIFS(%s,{range:instalments.days_late},">"&{in:late_after},{range:instalments.status},%s)>=2,IFERROR(AVERAGEIFS({range:instalments.days_late},%s,{range:instalments.status},%s),0)>{in:late_after}),%s,%s)' % (IC, PD, IC, PD, vb('Offer autopay'), vb('Payer is on time')))],
    GR('What if', ('Late means 2 days', {'late_after': 2}), ('Late means 10 days', {'late_after': 10}), ('Late means 20 days', {'late_after': 20}))))

# 15 ----------------------------------------------------------- payment method fee check
Y1 = '{range:payments.date},">="&({today}-365)'
def PM(m, extra=''): return 'SUMIFS({range:payments.amount},%s,{range:payments.method},%s%s)' % (Y1, m, extra)
BIG = ',{range:payments.amount},">"&{in:ask_above}'
CARDALL = '(%s+%s)' % (PM(CARD), PM(LINK)); CARDBIG = '(%s+%s)' % (PM(CARD, BIG), PM(LINK, BIG))
tools.append(TOOL('method_fee', 'Payment Method Fee Check', 'What card fees cost and when to ask for a bank transfer',
    'Type your card fee, the payment size above which you ask for a bank transfer and the share of clients who agree; see the 12-month cash by method, the fees and the saving from moving large payments.', [
    I('ask_above', 'Ask for a bank transfer above this amount', 1000), I('fee_pct', 'Fee on a card payment', 0.03, 'pct'), I('switch', 'Share of those clients who agree to switch', 0.5, 'pct'), I('min_saving', 'Smallest yearly saving worth the effort', 150)], [
    O('Card and payment link receipts, 12 months', 'money', CARDALL), O('Bank transfer receipts, 12 months', 'money', PM(BANK)), O('Cash receipts, 12 months', 'money', PM(CASH)),
    O('Share of receipts paid by card or link', 'pct', 'IFERROR(%s/(%s+%s+%s),0)' % (CARDALL, CARDALL, PM(BANK), PM(CASH))), O('Fees at the rate you set', 'money', '%s*{in:fee_pct}' % CARDALL),
    O('Card payments above the amount you set', 'int', 'COUNTIFS(%s,{range:payments.method},%s%s)+COUNTIFS(%s,{range:payments.method},%s%s)' % (Y1, CARD, BIG, Y1, LINK, BIG)),
    O('Receipts in those payments', 'money', CARDBIG), O('Fees on those payments', 'money', '%s*{in:fee_pct}' % CARDBIG), O('Fees you could save in a year', 'money', '%s*{in:fee_pct}*{in:switch}' % CARDBIG),
    O('Fees recorded in Payments, 12 months', 'money', 'SUMIFS({range:payments.fee_cost},%s)' % Y1),
    O('Verdict', 'text', 'IF(%s*{in:fee_pct}*{in:switch}>={in:min_saving},%s&" "&ROUND({in:ask_above},0),%s)' % (CARDBIG, vb('Ask for bank transfer'), vb('Card fees are small')))],
    GR('What if', ('Ask above 500', {'ask_above': 500}), ('Ask above 2,000', {'ask_above': 2000}), ('Fee of 5 percent', {'fee_pct': 0.05}), ('80 percent agree', {'switch': 0.8}))))

# 16 ----------------------------------------------------------- window-entry balance check
WE = '{range:clients.days_to_window},">=0",{range:clients.days_to_window},"<="&{in:days},{range:clients.status},%s,{range:clients.outstanding},">="&{in:min_unpaid}' % BOOKED
tools.append(TOOL('window_entry', 'Window-Entry Balance Check', 'Who enters the on-call window with a balance unpaid',
    'Type how many days ahead to look and the smallest unpaid balance that matters; see the clients whose window opens in that time with money still owed, who is soonest and who is already inside the window unpaid.', [
    I('days', 'Days ahead to look', 14, 'int'), I('min_unpaid', 'Smallest unpaid balance that matters', 100)], [
    O('Clients entering the window in the days you set', 'int', 'COUNTIFS({range:clients.days_to_window},">=0",{range:clients.days_to_window},"<="&{in:days},{range:clients.status},%s)' % BOOKED),
    O('Of them with a balance unpaid', 'int', 'COUNTIFS(%s)' % WE), O('Balance unpaid before the window', 'money', 'SUMIFS({range:clients.outstanding},%s)' % WE),
    O('Inside the window with a balance unpaid', 'int', 'COUNTIFS({range:clients.window_check},%s)' % ca('Unpaid inside the window')),
    O('Amount unpaid inside the window', 'money', 'SUMIFS({range:clients.outstanding},{range:clients.window_check},%s)' % ca('Unpaid inside the window')),
    O('First client to chase', 'text', 'IFERROR(INDEX({range:clients.client},MATCH(SMALL({range:clients.soon_days},1),{range:clients.soon_days},0)),"-")'),
    O('Days until their window opens', 'int', 'IFERROR(SMALL({range:clients.soon_days},1),0)'),
    O('Balance outstanding for that client', 'money', 'IFERROR(INDEX({range:clients.outstanding},MATCH(SMALL({range:clients.soon_days},1),{range:clients.soon_days},0)),0)'),
    O('Window opens on', 'date', 'IFERROR(INDEX({range:clients.oncall_start},MATCH(SMALL({range:clients.soon_days},1),{range:clients.soon_days},0)),{today})'),
    O('Booked clients with a balance unpaid, any date', 'int', 'COUNTIFS({range:clients.soon_days},">=0")'),
    O('Verdict', 'text', 'IF(COUNTIFS(%s)>0,%s&": "&IFERROR(INDEX({range:clients.client},MATCH(SMALL({range:clients.soon_days},1),{range:clients.soon_days},0)),"-"),%s)' % (WE, vb('Collect before the window'), vb('All balances paid')))],
    GR('What if', ('Look 7 days ahead', {'days': 7}), ('Look 30 days ahead', {'days': 30}), ('Look 60 days ahead', {'days': 60}), ('Only balances of 1,000 or more', {'min_unpaid': 1000}))))

# 17 ----------------------------------------------------------- unearned cash by month
COST3 = 'IFERROR(AVERAGEIFS({range:pnl.costs},{range:pnl.month},">="&EDATE(%s,-3),{range:pnl.month},"<"&%s),0)' % (MS, MS)
UNE = 'SUM({range:unearned_client.unearned})'
def REL(k): return 'SUMIFS({range:unearned_client.unearned},{range:unearned_client.release_month},EDATE(%s,%d))' % (MS, k)
REL6 = 'SUMIFS({range:unearned_client.unearned},{range:unearned_client.release_month},"<"&EDATE(%s,6))' % MS
tools.append(TOOL('unearned_cash', 'Unearned Cash by Month', 'How long the unearned cash lasts and when it is earned',
    'Type the new unearned cash you expect each month; see the unearned cash now against your costs and cash floor, when it is earned over the next six months and the balance left after six months.', [
    I('new_cash', 'New unearned cash added each month', 3000)], [
    O('Unearned cash now', 'money', UNE), O('Monthly costs, average of the last 3 months', 'money', COST3), O('Months of costs the unearned cash covers', 'num', 'IFERROR(%s/%s,0)' % (UNE, COST3)),
    O('Months of costs you want covered', 'int', '{set:cash_cover_months}'), O('Unearned cash above your cash floor', 'money', '%s-{set:cash_floor}' % UNE)] + [
    O('Earned this month' if k == 0 else 'Earned in month %d ahead' % k, 'money', REL(k)) for k in range(6)] + [
    O('Balance after 6 months with the new cash', 'money', 'MAX(0,%s-%s+6*{in:new_cash})' % (UNE, REL6)),
    O('Verdict', 'text', 'IF(%s>={set:cash_cover_months}*%s,%s,%s)&" "&ROUND(IFERROR(%s/%s,0),1)' % (UNE, COST3, vb('Unearned cash above the cover'), vb('Unearned cash below the cover'), UNE, COST3))],
    GR('What if', ('No new unearned cash', {'new_cash': 0}), ('6,000 a month', {'new_cash': 6000}), ('10,000 a month', {'new_cash': 10000}))))

# 18 ----------------------------------------------------------- paid-up reconciliation
DUE18 = 'IF(%s<={in:as_of},%s,0)+IF(%s=%s,IF(AND(%s>0,%s<={in:as_of}),%s-%s,0),SUMIFS({range:instalments.amount},{range:instalments.client},{in:client},{range:instalments.due_date},"<="&{in:as_of}))' % (
    C5('signed_on'), C5('deposit'), C5('plan', '""'), PIF, C5('balance_due'), C5('balance_due'), C5('price'), C5('deposit'))
DIF18 = '(%s-(%s))' % (PAID12, DUE18)
tools.append(TOOL('reconcile', 'Paid-Up Reconciliation', 'Is this client paid up to the date you choose',
    'Type a client and a date; the price is set against the cash paid and the cash due by that date (deposit, balance or instalments), so you see if the client is on track, short or paid ahead.', [
    I('client', 'Client name', D.ST['plan_client'], 'text'), I('as_of', 'Check the account on this date', ahead(5), 'date')], [
    O('Package', 'text', C5('package', '"-"')), O('Price', 'money', OLD12), O('Paid so far', 'money', PAID12), O('Due by that date', 'money', DUE18), O('Not yet due at that date', 'money', '%s-(%s)' % (OLD12, DUE18)),
    O('Share of the price paid', 'pct', 'IFERROR(%s/%s,0)' % (PAID12, OLD12)), O('Paid less due', 'money', DIF18), O('Next payment due', 'date', 'IFERROR(IF(INDEX({range:contracts.next_due},%s)="",{today},INDEX({range:contracts.next_due},%s)),{today})' % (M5, M5)),
    O('Payments received', 'int', 'COUNTIFS({range:payments.client},{in:client})'), O('Last payment on', 'date', 'SUMPRODUCT(MAX(({range:payments.client}={in:client})*{range:payments.date}))'),
    O('Instalments paid', 'int', 'COUNTIFS({range:instalments.client},{in:client},{range:instalments.status},%s)' % PD), O('Instalments still unpaid', 'int', 'COUNTIFS({range:instalments.client},{in:client},{range:instalments.status},%s)' % UN),
    O('Verdict', 'text', 'IF(ABS(%s)<0.5,%s,IF(%s<0,%s&" "&ROUND(-%s,0),%s&" "&ROUND(%s,0)))' % (DIF18, vb('On track'), DIF18, vb('Short by'), DIF18, vb('Paid ahead by'), DIF18))],
    GR('What if', ('Check today', {'as_of': '={today}'}), ('Check in 30 days', {'as_of': '={today}+30'}), ('Check in 60 days', {'as_of': '={today}+60'}), ('Check in 90 days', {'as_of': '={today}+90'}))))

assert len(tools) == 18, len(tools)
