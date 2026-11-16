"""Household Finance suite part 2: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf2_lists import *
from hf2_tables import MS, YES, NO, PAID, UNPAID, LATE, MO, YR, KEEP, REVIEW, CANCEL, INS, UTIL, KIND_INS, PAYDAY, PAYGAP, PERIODS, JB, DOM
import hf2_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def R(t, c): return '{range:%s.%s}' % (t, c)
def TXT(*parts): return '&" "&'.join(parts)
def PER(r): return 'IF(%s=%s,52,IF(%s=%s,26,IF(%s=%s,24,12)))' % (r, tok('payfreq', 'Weekly'), r, tok('payfreq', 'Every two weeks'), r, tok('payfreq', 'Twice a month'))
tools = []
BD = lambda c: R('bill_due', c)
BLR = lambda c: R('bills', c)
SBR = lambda c: R('subs', c)
ID = '%s,"<>"' % BD('due_id')

# 1 ------------------------------------------------------------ bills calendar
W1 = '%s,">="&{today},%s,"<="&({today}+{in:days}),%s' % (BD('due_date'), BD('due_date'), ID)
N1 = 'COUNTIFS(%s)' % W1; T1 = 'SUMIFS(%s,%s)' % (BD('amount'), W1)
tools.append(TOOL('cal_tool', 'Bills Calendar Planner', 'How many bills fall due in the next days and how much',
    'Type how many days ahead to look; the bills due, the total, how many are unpaid, autopay or manual and the largest bill fill in from the Bills Due sheet.', [
    I('days', 'Days ahead', 14, 'int')], [
    O('Bills due in the window', 'int', N1), O('Total amount due', 'money', T1), O('Still unpaid', 'int', 'COUNTIFS(%s,%s,"<>"&%s)' % (W1, BD('status'), PAID)),
    O('On autopay', 'int', 'COUNTIFS(%s,%s,%s)' % (W1, BD('autopay'), YES)), O('Manual', 'int', 'COUNTIFS(%s,%s,%s)' % (W1, BD('autopay'), NO)),
    O('Share of the total on autopay', 'pct', 'IFERROR(SUMIFS(%s,%s,%s,%s)/%s,0)' % (BD('amount'), W1, BD('autopay'), YES, T1)),
    O('Largest bill in the window', 'money', 'SUMPRODUCT(MAX((%s>={today})*(%s<={today}+{in:days})*%s))' % (BD('due_date'), BD('due_date'), BD('amount'))),
    O('Next bill', 'text', 'INDEX(%s,1)' % R('bills_cal', 'bill')), O('Next due date', 'date', 'INDEX(%s,1)' % R('bills_cal', 'due_date')), O('Days to the next bill', 'int', 'INDEX(%s,1)' % R('bills_cal', 'days_away')),
    O('Average bill in the window', 'money', 'IFERROR(%s/%s,0)' % (T1, N1)),
    O('Verdict', 'text', TXT(N1, V('bills due, total'), 'ROUND(%s,0)' % T1))],
    GR('What if', ('Next 7 days', {'days': 7}), ('Next 21 days', {'days': 21}), ('Next 30 days', {'days': 30}), ('Next 45 days', {'days': 45}), ('Next 60 days', {'days': 60}))))

# 2 ------------------------------------------------------------ unpaid before payday
OPEN2 = 'SUMIFS(%s,%s,"<>"&%s,%s,"<"&%s,%s,{set:joint_account_id},%s)' % (BD('amount'), BD('status'), PAID, BD('due_date'), PAYDAY, BD('account_id'), ID)
AFT2 = '(%s+{in:move_in}-(%s-{in:delay}))' % (JB, OPEN2)
tools.append(TOOL('payday_cover', 'Payday Cover Check', 'Will the joint balance cover the bills before payday',
    'Type money you can move in and a bill you can delay; open bills due before payday are set against the joint balance and the cash floor, with the first bill that breaks the floor.', [
    I('move_in', 'Money you can move into the joint account', 0), I('delay', 'Amount of a bill you can delay past payday', 0)], [
    O('Joint balance now', 'money', JB), O('Open bills due before payday', 'money', OPEN2), O('Bills still open before payday', 'int', 'COUNTIFS(%s,"<>"&%s,%s,"<"&%s,%s,{set:joint_account_id},%s)' % (BD('status'), PAID, BD('due_date'), PAYDAY, BD('account_id'), ID)),
    O('Balance at payday', 'money', AFT2), O('Your cash floor', 'money', '{set:cash_floor}'), O('Gap to the cash floor', 'money', '%s-{set:cash_floor}' % AFT2),
    O('Lowest balance before payday', 'money', 'IFERROR(MIN(%s),0)' % R('unpaid_pay', 'balance_after')),
    O('First bill that breaks the floor', 'text', 'IFERROR(INDEX(%s,MATCH(1,%s,0)),"")' % (R('unpaid_pay', 'bill'), R('unpaid_pay', 'under'))),
    O('Date it breaks the floor', 'date', 'IFERROR(INDEX(%s,MATCH(1,%s,0)),"")' % (R('unpaid_pay', 'due_date'), R('unpaid_pay', 'under'))),
    O('Amount to move in to stay above the floor', 'money', 'MAX(0,{set:cash_floor}-%s)' % AFT2), O('Next payday', 'date', PAYDAY),
    O('Verdict', 'text', 'IF(%s>={set:cash_floor},%s,%s&" "&ROUND({set:cash_floor}-%s,0))' % (AFT2, V('Covered'), V('Short by'), AFT2))],
    GR('What if', ('Move in 300', {'move_in': 300}), ('Move in 600', {'move_in': 600}), ('Delay a 140 bill', {'delay': 140}), ('Delay the 560 bill', {'delay': 560}), ('Move in 600 and delay 140', {'move_in': 600, 'delay': 140}))))

# 3 ------------------------------------------------------------ late bill chaser
LN3 = 'COUNTIFS(%s,"<>"&%s,%s,"<"&{today},%s)' % (BD('status'), PAID, BD('due_date'), ID)
LA3 = 'SUMIFS(%s,%s,"<>"&%s,%s,"<"&{today},%s)' % (BD('amount'), BD('status'), PAID, BD('due_date'), ID)
tools.append(TOOL('late_tool', 'Late Bill Chaser', 'Which late bill do we deal with first',
    'Type extra cash you can add today; late bills are counted, the oldest and its contact are named, and the verdict says whether to pay today or call to agree a date.', [
    I('extra', 'Extra cash you can add today', 0)], [
    O('Late bills now', 'int', LN3), O('Amount late', 'money', LA3),
    O('Days late of the oldest', 'int', 'SUMPRODUCT(MAX((%s<>"")*(%s<>%s)*(%s<{today})*({today}-%s)))' % (BD('due_id'), BD('status'), PAID, BD('due_date'), BD('due_date'))),
    O('Latest late bill', 'text', 'IF(%s>0,INDEX(%s,1),"")' % (LN3, R('late_list', 'bill'))), O('Its contact', 'text', 'IF(%s>0,INDEX(%s,1),"")' % (LN3, R('late_list', 'contact'))),
    O('Its amount', 'money', 'IF(%s>0,INDEX(%s,1),0)' % (LN3, R('late_list', 'amount'))), O('Joint balance now', 'money', JB), O('Cash you can use', 'money', '%s+{in:extra}' % JB),
    O('Bills paid late, last 12 months', 'int', 'COUNTIFS(%s,%s,%s,">="&({today}-365))' % (BD('flag'), V('Paid late'), BD('due_date'))),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s<=%s+{in:extra},%s,%s&" "&INDEX(%s,1)))' % (LN3, V('Fine'), LA3, JB, V('Pay today'), V('Call'), R('late_list', 'contact')))],
    GR('What if', ('No extra cash', {'extra': 0}), ('Add 50', {'extra': 50}), ('Add 200', {'extra': 200}), ('Add 1000', {'extra': 1000}))))

# 4 ------------------------------------------------------------ autopay review
tools.append(TOOL('autopay_tool', 'Autopay Review', 'Which manual bills should move to autopay',
    'Type how many days before payday make a bill risky; manual bills falling just before payday are counted with their monthly cost, and the first one on the Autopay Map is named.', [
    I('gap', 'Days before payday that make a bill risky', 3, 'int')], [
    O('Bills on autopay', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (BLR('autopay'), YES, BLR('bill_id'))), O('Manual bills', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (BLR('autopay'), NO, BLR('bill_id'))),
    O('Share of bills on autopay', 'pct', 'IFERROR(COUNTIFS(%s,%s,%s,"<>")/COUNTIFS(%s,"<>"),0)' % (BLR('autopay'), YES, BLR('bill_id'), BLR('bill_id'))),
    O('Manual bills due just before payday', 'int', 'COUNTIFS(%s,%s,%s,">=1",%s,"<="&{in:gap},%s,"<>")' % (BLR('autopay'), NO, BLR('days_before_pay'), BLR('days_before_pay'), BLR('bill_id'))),
    O('Their cost per month', 'money', 'SUMIFS(%s,%s,%s,%s,">=1",%s,"<="&{in:gap},%s,"<>")' % (BLR('monthly_cost'), BLR('autopay'), NO, BLR('days_before_pay'), BLR('days_before_pay'), BLR('bill_id'))),
    O('Autopay bills landing just before payday', 'int', 'COUNTIFS(%s,%s,%s,">=1",%s,"<="&{in:gap},%s,"<>")' % (BLR('autopay'), YES, BLR('days_before_pay'), BLR('days_before_pay'), BLR('bill_id'))),
    O('Their cost per month on autopay', 'money', 'SUMIFS(%s,%s,%s,%s,">=1",%s,"<="&{in:gap},%s,"<>")' % (BLR('monthly_cost'), BLR('autopay'), YES, BLR('days_before_pay'), BLR('days_before_pay'), BLR('bill_id'))),
    O('First manual bill to switch', 'text', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (R('autopay_map', 'bill'), V('Manual, due just before payday'), R('autopay_map', 'check'))),
    O('Your autopay target', 'pct', '{set:autopay_target}'),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,%s,%s,">=1",%s,"<="&{in:gap},%s,"<>")>0,%s,%s)' % (BLR('autopay'), NO, BLR('days_before_pay'), BLR('days_before_pay'), BLR('bill_id'), V('Switch to autopay, first'), V('Keep manual')) + '&IF(COUNTIFS(%s,%s,%s,">=1",%s,"<="&{in:gap},%s,"<>")>0," "&IFERROR(INDEX(%s,MATCH(%s,%s,0)),""),"")' % (
        BLR('autopay'), NO, BLR('days_before_pay'), BLR('days_before_pay'), BLR('bill_id'), R('autopay_map', 'bill'), V('Manual, due just before payday'), R('autopay_map', 'check')))],
    GR('What if', ('1 day', {'gap': 1}), ('2 days', {'gap': 2}), ('5 days', {'gap': 5}), ('7 days', {'gap': 7}), ('10 days', {'gap': 10}))))

# 5 ------------------------------------------------------------ due day mover
BX5 = 'MATCH({in:bill},%s,0)' % BLR('bill')
DBP5 = 'IFERROR(INDEX(%s,%s),"")' % (BLR('days_before_pay'), BX5)
tools.append(TOOL('dueday_tool', 'Due Day Mover', 'Which due day to ask for so a bill falls after payday',
    'Type a bill exactly as on the Bills sheet and the cushion days after payday; the day of the month that follows payday is worked out and the verdict says whether to ask for a move.', [
    I('bill', 'Bill, as written on the Bills sheet', 'Childcare provider', 'text'), I('gap', 'Days before payday that make a bill risky', 3, 'int'), I('cushion', 'Days after payday you want it due', 1, 'int')], [
    O('Due day now', 'int', 'IFERROR(INDEX(%s,%s),"")' % (BLR('due_day'), BX5)), O('Next due date', 'date', 'IFERROR(INDEX(%s,%s),"")' % (BLR('next_due'), BX5)), O('Amount', 'money', 'IFERROR(INDEX(%s,%s),0)' % (BLR('amount'), BX5)),
    O('Next payday', 'date', PAYDAY), O('Days before a payday it falls', 'int', DBP5), O('Day of the month to ask for', 'int', 'DAY(%s+{in:cushion})' % PAYDAY), O('Date of that day after the next payday', 'date', '%s+{in:cushion}' % PAYDAY),
    O('Contact', 'text', 'IFERROR(INDEX(%s,%s),"")' % (BLR('contact'), BX5)),
    O('Verdict', 'text', 'IF(%s="",%s,IF(AND(%s>=1,%s<={in:gap}),%s&" "&DAY(%s+{in:cushion}),%s))' % (DBP5, V('Bill not found'), DBP5, DBP5, V('Ask to move to day'), PAYDAY, V('Due day is fine')))],
    GR('What if', ('Gap of 1 day', {'gap': 1}), ('Gap of 7 days', {'gap': 7}), ('Cushion of 3 days', {'cushion': 3}), ('Cushion of 0 days', {'cushion': 0}), ('Gap of 10 days', {'gap': 10}))))

# 6 ------------------------------------------------------------ bill total per paycheck
MON6 = 'SUMIFS(%s,%s,%s)' % (BLR('amount'), BLR('cycle'), MO); YRL6 = 'SUMIFS(%s,%s,%s)/12' % (BLR('amount'), BLR('cycle'), YR)
PP6 = '((%s+%s)*12/%s)' % (MON6, YRL6, PER('{in:rhythm}'))
tools.append(TOOL('paycheck_tool', 'Bill Total per Paycheck', 'How much of each paycheck goes to bills',
    'Pick how you are paid and a buffer for price rises; all monthly bills and one twelfth of the yearly bills become one amount to set aside from each paycheck.', [
    IL('rhythm', 'How you are paid', 'payfreq', 'Every two weeks'), I('buffer', 'Buffer for price rises', 0.05, 'pct')], [
    O('Monthly bills', 'money', MON6), O('Yearly bills, one twelfth a month', 'money', YRL6), O('All bills per month', 'money', '%s+%s' % (MON6, YRL6)), O('Paychecks per year', 'int', PER('{in:rhythm}')),
    O('Paychecks per month, on average', 'num', '%s/12' % PER('{in:rhythm}')), O('Set aside per paycheck', 'money', PP6), O('Set aside per paycheck with the buffer', 'money', '%s*(1+{in:buffer})' % PP6),
    O('Bills per week', 'money', '(%s+%s)*12/52' % (MON6, YRL6)), O('Bills due per day, on average', 'money', '(%s+%s)*12/365' % (MON6, YRL6)),
    O('Verdict', 'text', TXT(V('Set aside, per paycheck:'), 'ROUND(%s*(1+{in:buffer}),0)' % PP6))],
    GR('Pay rhythm', ('Weekly', {'rhythm': '=' + tok('payfreq', 'Weekly')}), ('Every two weeks', {'rhythm': '=' + tok('payfreq', 'Every two weeks')}), ('Twice a month', {'rhythm': '=' + tok('payfreq', 'Twice a month')}),
       ('Monthly', {'rhythm': '=' + tok('payfreq', 'Monthly')}), ('Every two weeks, buffer 10 percent', {'buffer': 0.10}))))

# 7 ------------------------------------------------------------ yearly bills to monthly
YT7 = 'SUMIFS(%s,%s,%s)' % (BLR('amount'), BLR('cycle'), YR)
NX7 = 'MATCH(SMALL(%s,1),%s,0)' % (BLR('yearly_next'), BLR('yearly_next'))
AM7 = 'IFERROR(INDEX(%s,%s),0)' % (BLR('amount'), NX7)
MU7 = 'MAX(1,ROUND((SMALL(%s,1)-{today})/30.4,0))' % BLR('yearly_next')
tools.append(TOOL('yearly_tool', 'Yearly Bills to Monthly', 'How much to save each month for the yearly bills',
    'Pick how you are paid and the money already saved for the next yearly bill; every yearly bill becomes a monthly and per-paycheck amount and the next one is named with the months left.', [
    IL('rhythm', 'How you are paid', 'payfreq', 'Every two weeks'), I('saved', 'Saved so far for the next yearly bill', 600)], [
    O('Yearly bills in total', 'money', YT7), O('Number of yearly bills', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (BLR('cycle'), YR, BLR('bill_id'))), O('Put aside each month', 'money', '%s/12' % YT7),
    O('Put aside per paycheck', 'money', '%s/%s' % (YT7, PER('{in:rhythm}'))), O('Next yearly bill', 'text', 'IFERROR(INDEX(%s,%s),"")' % (BLR('bill'), NX7)), O('Its due date', 'date', 'IFERROR(SMALL(%s,1),"")' % BLR('yearly_next')),
    O('Its amount', 'money', AM7), O('Months until it is due', 'int', 'IFERROR(%s,0)' % MU7), O('Still to save for it', 'money', 'MAX(0,%s-{in:saved})' % AM7),
    O('Needed each month to be ready', 'money', 'IFERROR(MAX(0,%s-{in:saved})/%s,0)' % (AM7, MU7)),
    O('Verdict', 'text', TXT(V('Save'), 'ROUND(%s/12,0)' % YT7, V('a month for yearly bills')))],
    GR('What if', ('Nothing saved yet', {'saved': 0}), ('Half saved', {'saved': 630}), ('Fully saved', {'saved': 1260}), ('Paid weekly', {'rhythm': '=' + tok('payfreq', 'Weekly')}), ('Paid monthly', {'rhythm': '=' + tok('payfreq', 'Monthly')}))))

# 8 ------------------------------------------------------------ price rise finder
tools.append(TOOL('price_tool', 'Price Rise Finder', 'Which bills went up and what to ask for',
    'Type the rise that bothers you; bills that rose against a year ago are counted, the extra cost over a year is added up and the largest rise is named for a call.', [
    I('threshold', 'Rise you want to act on', 0.05, 'pct')], [
    O('Bills compared with a year ago', 'int', 'COUNTIFS(%s,">0")' % BLR('last_amount')), O('Bills that rose', 'int', 'COUNTIFS(%s,">0")' % BLR('change_share')),
    O('Bills that rose above your limit', 'int', 'COUNTIFS(%s,">="&{in:threshold})' % BLR('change_share')),
    O('Extra cost a year from those', 'money', 'SUMIFS(%s,%s,">="&{in:threshold},%s,%s)*12+SUMIFS(%s,%s,">="&{in:threshold},%s,%s)' % (BLR('change'), BLR('change_share'), BLR('cycle'), MO, BLR('change'), BLR('change_share'), BLR('cycle'), YR)),
    O('Largest rise', 'pct', 'IFERROR(MAX(%s),0)' % BLR('change_share')), O('Bill with the largest rise', 'text', 'INDEX(%s,1)' % R('price_changes', 'bill')), O('Its amount a year ago', 'money', 'INDEX(%s,1)' % R('price_changes', 'last_amount')),
    O('Its amount now', 'money', 'INDEX(%s,1)' % R('price_changes', 'amount')), O('Its contact', 'text', 'INDEX(%s,1)' % R('price_changes', 'contact')),
    O('Average rise of the bills that rose', 'pct', 'IFERROR(AVERAGEIFS(%s,%s,">0"),0)' % (BLR('change_share'), BLR('change_share'))),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">="&{in:threshold})>0,%s&" "&INDEX(%s,1),%s)' % (BLR('change_share'), V('Ask for a better price on'), R('price_changes', 'bill'), V('No rise above your limit')))],
    GR('What if', ('Limit 2 percent', {'threshold': 0.02}), ('Limit 8 percent', {'threshold': 0.08}), ('Limit 15 percent', {'threshold': 0.15}), ('Any rise', {'threshold': 0.0001}))))

# 9 ------------------------------------------------------------ subscriptions audit
UN9 = 'COUNTIFS(%s,">="&{in:days})' % SBR('days_since_use')
MK9 = 'COUNTIFS(%s,"<>"&%s,%s,"<"&{in:days},%s,"<>")' % (SBR('decision'), KEEP, SBR('days_since_use'), SBR('sub_id'))
ST9 = 'SUMIFS(%s,%s,">="&{in:days})+SUMIFS(%s,%s,"<>"&%s,%s,"<"&{in:days},%s,"<>")' % (SBR('yearly_cost'), SBR('days_since_use'), SBR('yearly_cost'), SBR('decision'), KEEP, SBR('days_since_use'), SBR('sub_id'))
tools.append(TOOL('audit_tool', 'Subscriptions Audit', 'Which subscriptions deserve a second look',
    'Type the unused days; every subscription is totalled per month and year and those unused or already marked review or cancel are counted with the yearly cost at stake.', [
    I('days', 'Unused days that make a subscription a candidate', 60, 'int')], [
    O('Active subscriptions', 'int', 'COUNTIFS(%s,"<>")' % SBR('sub_id')), O('Cost per month', 'money', 'SUM(%s)' % SBR('monthly_cost')), O('Cost per year', 'money', 'SUM(%s)' % SBR('yearly_cost')),
    O('Not used for the set days', 'int', UN9), O('Marked review or cancel but in use', 'int', MK9), O('Subscriptions to review', 'int', '%s+%s' % (UN9, MK9)), O('Yearly cost at stake', 'money', ST9),
    O('Share of the yearly cost at stake', 'pct', 'IFERROR((%s)/SUM(%s),0)' % (ST9, SBR('yearly_cost'))), O('Dearest subscription', 'text', 'INDEX(%s,1)' % R('subs_rank', 'name')),
    O('Its cost per year', 'money', 'INDEX(%s,1)' % R('subs_rank', 'yearly_cost')), O('Share of the yearly cost of the top three', 'pct', 'IFERROR(SUMIFS(%s,%s,"<=3")/SUM(%s),0)' % (R('subs_rank', 'yearly_cost'), R('subs_rank', 'rank'), R('subs_rank', 'yearly_cost'))),
    O('Verdict', 'text', TXT('(%s+%s)' % (UN9, MK9), V('to review,'), 'ROUND(%s,0)' % ST9, V('a year at stake')))],
    GR('What if', ('30 days', {'days': 30}), ('45 days', {'days': 45}), ('90 days', {'days': 90}), ('120 days', {'days': 120}), ('15 days', {'days': 15}))))

# 10 ----------------------------------------------------------- unused subscription finder
D1 = 'INDEX(%s,1)' % R('unused_subs', 'days_since_use')
tools.append(TOOL('unused_tool', 'Unused Subscription Finder', 'Cancel, review or keep the longest unused subscription',
    'Type the unused days; the three subscriptions not used for longest are named with days and yearly cost, and the verdict says cancel, review or keep for the first.', [
    I('days', 'Unused days that call for a cancel', 60, 'int')], [
    O('Subscriptions not used for the set days', 'int', 'COUNTIFS(%s,">="&{in:days})' % SBR('days_since_use')), O('Their cost per year', 'money', 'SUMIFS(%s,%s,">="&{in:days})' % (SBR('yearly_cost'), SBR('days_since_use'))),
    O('Share of all subscription cost', 'pct', 'IFERROR(SUMIFS(%s,%s,">="&{in:days})/SUM(%s),0)' % (SBR('yearly_cost'), SBR('days_since_use'), SBR('yearly_cost'))),
    O('Longest unused', 'text', 'INDEX(%s,1)' % R('unused_subs', 'name')), O('Days since it was used', 'int', D1), O('Its cost per year', 'money', 'INDEX(%s,1)' % R('unused_subs', 'yearly_cost')),
    O('Second longest unused', 'text', 'INDEX(%s,2)' % R('unused_subs', 'name')), O('Days since it was used, second', 'int', 'INDEX(%s,2)' % R('unused_subs', 'days_since_use')),
    O('Third longest unused', 'text', 'INDEX(%s,3)' % R('unused_subs', 'name')), O('Days since it was used, third', 'int', 'INDEX(%s,3)' % R('unused_subs', 'days_since_use')),
    O('Verdict', 'text', 'IF(%s>={in:days},%s,IF(%s>=ROUND({in:days}/2,0),%s,%s))' % (D1, CANCEL, D1, REVIEW, KEEP))],
    GR('What if', ('30 days', {'days': 30}), ('45 days', {'days': 45}), ('90 days', {'days': 90}), ('100 days', {'days': 100}), ('200 days', {'days': 200}))))

# 11 ----------------------------------------------------------- cancel savings calculator
MK11 = 'SUMIFS(%s,%s,%s)' % (SBR('monthly_cost'), SBR('decision'), CANCEL)
UU11 = 'SUMIFS(%s,%s,">="&{set:sub_unused_days},%s,"<>"&%s)' % (SBR('monthly_cost'), SBR('days_since_use'), SBR('decision'), CANCEL)
TM11 = '(%s+{in:include}*%s)' % (MK11, UU11)
tools.append(TOOL('cancel_tool', 'Cancel Savings Calculator', 'What we save if the chosen subscriptions are cancelled',
    'Type whether to include the unused ones and the months left; the ones marked cancel, and optionally the unused, become a saving per month and year. A calculation, not a promise.', [
    I('include', 'Include unused subscriptions, 1 for yes', 1, 'int'), I('months_left', 'Months of savings you count', 12, 'int')], [
    O('Marked cancel', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (SBR('decision'), CANCEL, SBR('sub_id'))), O('Their cost per month', 'money', MK11),
    O('Unused and not yet marked', 'int', 'COUNTIFS(%s,">="&{set:sub_unused_days},%s,"<>"&%s,%s,"<>")' % (SBR('days_since_use'), SBR('decision'), CANCEL, SBR('sub_id'))), O('Their cost per month, unused', 'money', UU11),
    O('Saved per month', 'money', TM11), O('Saved over the months you count', 'money', '%s*{in:months_left}' % TM11), O('Saved per year', 'money', '%s*12' % TM11),
    O('Share of the subscription bill', 'pct', 'IFERROR(%s/SUM(%s),0)' % (TM11, SBR('monthly_cost'))), O('Subscription cost per month after', 'money', 'SUM(%s)-%s' % (SBR('monthly_cost'), TM11)),
    O('Verdict', 'text', TXT(V('Saves'), 'ROUND(%s*12,0)' % TM11, V('a year, an estimate')))],
    GR('What if', ('Marked ones only', {'include': 0}), ('Marked and unused', {'include': 1}), ('Six months only', {'months_left': 6}), ('Three months only', {'months_left': 3}), ('Marked only, 6 months', {'include': 0, 'months_left': 6}))))

# 12 ----------------------------------------------------------- subscription creep check
SC12 = lambda m: 'SUMIFS(%s,%s,%s)' % (R('sub_charges', 'amount'), R('sub_charges', 'month'), m)
L12 = SC12('EDATE(%s,-1)' % MS); S12 = SC12('EDATE(%s,-7)' % MS)
A12 = '(SUMIFS(%s,%s,">="&EDATE(%s,-4),%s,"<"&EDATE(%s,-1))/3)' % (R('sub_charges', 'amount'), R('sub_charges', 'month'), MS, R('sub_charges', 'month'), MS)
CR12 = 'IFERROR(SUM(%s)/SUM(%s)-1,0)' % (SBR('monthly_cost'), SBR('then_monthly'))
tools.append(TOOL('creep_tool', 'Subscription Creep Check', 'Are subscriptions creeping up',
    'Type the growth you call creep; the last complete month of charges is set against 6 months earlier and the 3 months before it, and today\'s monthly cost against 6 months ago.', [
    I('alert', 'Growth you call creep', 0.10, 'pct')], [
    O('Charges last complete month', 'money', L12), O('Charges the same month 6 months earlier', 'money', S12), O('Change on 6 months earlier', 'pct', 'IFERROR(%s/%s-1,0)' % (L12, S12)),
    O('Average of the 3 months before', 'money', A12), O('Change on that average', 'pct', 'IFERROR(%s/%s-1,0)' % (L12, A12)), O('Cost per month now', 'money', 'SUM(%s)' % SBR('monthly_cost')),
    O('Cost per month 6 months ago', 'money', 'SUM(%s)' % SBR('then_monthly')), O('Creep against 6 months ago', 'pct', CR12), O('Subscriptions that cost more than 6 months ago', 'int', 'COUNTIFS(%s,">0")' % SBR('change_6m')),
    O('Extra cost a year from the creep', 'money', '(SUM(%s)-SUM(%s))*12' % (SBR('monthly_cost'), SBR('then_monthly'))),
    O('Verdict', 'text', 'IF(%s>={in:alert},%s&" "&ROUND(%s*100,0)&" "&%s,%s)' % (CR12, V('Creeping up'), CR12, V('percent'), V('Steady')))],
    GR('What if', ('Creep means 5 percent', {'alert': 0.05}), ('Creep means 25 percent', {'alert': 0.25}), ('Creep means 50 percent', {'alert': 0.5}), ('Creep means 1 percent', {'alert': 0.01}))))

# 13 ----------------------------------------------------------- renewal alert
RW13 = '%s,">="&{today},%s,"<="&({today}+{in:days})' % (SBR('renewal_date'), SBR('renewal_date'))
tools.append(TOOL('renewal_tool', 'Renewal Alert', 'Which subscription renews next and when to decide',
    'Type how many days ahead to look; renewals in that window are counted and priced, the next one is named with its renewal date and the date to decide by.', [
    I('days', 'Days ahead', 30, 'int')], [
    O('Renewals in the window', 'int', 'COUNTIFS(%s)' % RW13), O('Amount renewing', 'money', 'SUMIFS(%s,%s)' % (SBR('price'), RW13)), O('Next renewal', 'text', 'INDEX(%s,1)' % R('renewals', 'name')),
    O('Renewal date', 'date', 'INDEX(%s,1)' % R('renewals', 'renewal_date')), O('Days away', 'int', 'INDEX(%s,1)' % R('renewals', 'days_away')), O('Decide by', 'date', 'INDEX(%s,1)' % R('renewals', 'decide_by')),
    O('Price of the next renewal', 'money', 'INDEX(%s,1)' % R('renewals', 'price')), O('Your decision on it', 'text', 'INDEX(%s,1)' % R('renewals', 'decision')),
    O('Renewals marked cancel in the window', 'int', 'COUNTIFS(%s,%s,%s)' % (RW13, SBR('decision'), CANCEL)),
    O('Verdict', 'text', 'IF(COUNTIFS(%s)=0,%s,IF(INDEX(%s,1)<={today},%s,%s))' % (RW13, V('Nothing renews'), R('renewals', 'decide_by'), V('Decide today'), V('Decide by the date shown')))],
    GR('What if', ('7 days', {'days': 7}), ('14 days', {'days': 14}), ('45 days', {'days': 45}), ('60 days', {'days': 60}), ('2 days', {'days': 2}))))

# 14 ----------------------------------------------------------- annual plan switch
tools.append(TOOL('plan_tool', 'Annual Plan Switch', 'Monthly or yearly plan: which costs less',
    'Type the monthly price, the yearly price and the months you expect to use it; the cost of each way, the saving and the break-even month are worked out.', [
    I('monthly', 'Monthly price', 15.99), I('yearly', 'Yearly price', 159.0), I('use_months', 'Months you expect to keep it', 12, 'int')], [
    O('Cost of the monthly plan for a year', 'money', '{in:monthly}*12'), O('Cost of the yearly plan', 'money', '{in:yearly}'), O('Saving over a year', 'money', '{in:monthly}*12-{in:yearly}'),
    O('Share saved', 'pct', 'IFERROR(({in:monthly}*12-{in:yearly})/({in:monthly}*12),0)'), O('Break-even month', 'num', 'IFERROR({in:yearly}/{in:monthly},0)'),
    O('Monthly plan for the months you keep it', 'money', '{in:monthly}*{in:use_months}'), O('Saving for the months you keep it', 'money', '{in:monthly}*{in:use_months}-{in:yearly}'),
    O('Yearly price per month', 'money', '{in:yearly}/12'),
    O('Verdict', 'text', 'IF(AND({in:monthly}*{in:use_months}>{in:yearly},{in:use_months}>={in:yearly}/{in:monthly}),%s&" "&ROUND({in:monthly}*{in:use_months}-{in:yearly},0),%s)' % (V('Yearly saves'), V('Stay monthly')))],
    GR('What if', ('Keep it 6 months', {'use_months': 6}), ('Keep it 9 months', {'use_months': 9}), ('Yearly price 200', {'yearly': 200}), ('Yearly price 120', {'yearly': 120}), ('Cheaper monthly price', {'monthly': 9.99, 'yearly': 99.0}))))

# 15 ----------------------------------------------------------- contract review alert
NX15 = 'IFERROR(SMALL(%s,COUNTIF(%s,"<"&{today})+1),"")' % (R('contracts', 'renewal_date'), R('contracts', 'renewal_date'))
RV15 = 'COUNTIFS(%s,">"&{today},%s,"<="&({today}+{in:days}),%s,%s,%s,"<>")' % (R('contracts', 'renewal_date'), R('contracts', 'renewal_date'), R('contracts', 'reviewed'), NO, R('contracts', 'contract_id'))
tools.append(TOOL('review_tool', 'Contract Review Alert', 'Which contract do we review before it renews',
    'Type your review days; contracts not yet reviewed that renew inside that many days are counted and the next renewal is named with its review date.', [
    I('days', 'Review this many days before renewal', 45, 'int')], [
    O('Contracts to review now', 'int', RV15), O('Contracts renewing in 90 days', 'int', 'COUNTIFS(%s,">"&{today},%s,"<="&({today}+90),%s,"<>")' % (R('contracts', 'renewal_date'), R('contracts', 'renewal_date'), R('contracts', 'contract_id'))),
    O('Their cost per year', 'money', 'SUMIFS(%s,%s,">"&{today},%s,"<="&({today}+{in:days}),%s,%s)' % (R('contracts', 'yearly_cost'), R('contracts', 'renewal_date'), R('contracts', 'renewal_date'), R('contracts', 'reviewed'), NO)),
    O('Next renewal', 'date', NX15), O('Contract renewing next', 'text', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (R('contracts', 'contract'), NX15, R('contracts', 'renewal_date'))),
    O('Review date', 'date', 'IF(%s="","",%s-{in:days})' % (NX15, NX15)), O('Days to the review date', 'int', 'IF(%s="","",%s-{in:days}-{today})' % (NX15, NX15)),
    O('Its cost per year', 'money', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('contracts', 'yearly_cost'), NX15, R('contracts', 'renewal_date'))),
    O('Contracts reviewed this cycle', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (R('contracts', 'reviewed'), YES, R('contracts', 'contract_id'))),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (RV15, V('Review now'), V('Review on the date shown')))],
    GR('What if', ('30 days', {'days': 30}), ('60 days', {'days': 60}), ('90 days', {'days': 90}), ('120 days', {'days': 120}), ('15 days', {'days': 15}))))

# 16 ----------------------------------------------------------- insurance cost share
IN16 = lambda a, b: 'SUMIFS(%s,%s,%s,%s,">="&EDATE(%s,%d),%s,"<"&EDATE(%s,%d))' % (BD('amount'), BD('category'), INS, BD('month'), MS, a, BD('month'), MS, b)
AL16 = lambda a, b: 'SUMIFS(%s,%s,">="&EDATE(%s,%d),%s,"<"&EDATE(%s,%d))' % (BD('amount'), BD('month'), MS, a, BD('month'), MS, b)
tools.append(TOOL('insurance_tool', 'Insurance Cost Share', 'Is insurance taking a bigger share of our spending',
    'Type the rise you accept; insurance bills of the last 12 months are set against the 12 months before and against all bills, so you see your own change.', [
    I('tolerance', 'Rise in share you accept', 0.05, 'pct')], [
    O('Insurance premiums, last 12 months', 'money', IN16(-12, 0)), O('Insurance premiums, the 12 months before', 'money', IN16(-24, -12)), O('Change in premiums', 'pct', 'IFERROR(%s/%s-1,0)' % (IN16(-12, 0), IN16(-24, -12))),
    O('All bills, last 12 months', 'money', AL16(-12, 0)), O('Insurance share of bills now', 'pct', 'IFERROR(%s/%s,0)' % (IN16(-12, 0), AL16(-12, 0))),
    O('Insurance share of bills a year earlier', 'pct', 'IFERROR(%s/%s,0)' % (IN16(-24, -12), AL16(-24, -12))), O('Insurance contracts per year', 'money', 'SUMIFS(%s,%s,%s)' % (R('contracts', 'yearly_cost'), R('contracts', 'kind'), KIND_INS)),
    O('Insurance cost per month', 'money', 'SUMIFS(%s,%s,%s)/12' % (R('contracts', 'yearly_cost'), R('contracts', 'kind'), KIND_INS)),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s,0)-IFERROR(%s/%s,0)>{in:tolerance},%s&" "&ROUND((IFERROR(%s/%s,0)-IFERROR(%s/%s,0))*100,1)&" "&%s,%s)' % (
        IN16(-12, 0), AL16(-12, 0), IN16(-24, -12), AL16(-24, -12), V('Up'), IN16(-12, 0), AL16(-12, 0), IN16(-24, -12), AL16(-24, -12), V('points'), V('Steady')))],
    GR('What if', ('Accept 1 point', {'tolerance': 0.01}), ('Accept 2 points', {'tolerance': 0.02}), ('Accept 10 points', {'tolerance': 0.10}), ('Accept nothing', {'tolerance': 0.0}))))

# 17 ----------------------------------------------------------- utility seasons check
UT17 = lambda m: 'SUMIFS(%s,%s,%s,%s,%s)' % (BD('amount'), BD('category'), UTIL, BD('month'), m)
TH17 = UT17(MS); LY17 = UT17('EDATE(%s,-12)' % MS)
AV17 = '(SUMIFS(%s,%s,%s,%s,">="&EDATE(%s,-12),%s,"<"&%s)/12)' % (BD('amount'), BD('category'), UTIL, BD('month'), MS, BD('month'), MS)
tools.append(TOOL('utility_tool', 'Utility Seasons Check', 'Is this month utility cost normal for the season',
    'Type the rise that worries you; utilities this month are set against the same month last year and the 12-month average, and the dearest month of your history is named.', [
    I('alert', 'Rise that worries you', 0.10, 'pct')], [
    O('Utilities this month', 'money', TH17), O('Utilities the same month last year', 'money', LY17), O('Change on last year', 'pct', 'IFERROR(%s/%s-1,0)' % (TH17, LY17)),
    O('Average per month, last 12 months', 'money', AV17), O('This month against the average', 'pct', 'IFERROR(%s/%s-1,0)' % (TH17, AV17)), O('Dearest month in your history', 'money', 'MAX(%s)' % R('bills_month', 'utilities')),
    O('Month of that peak', 'date', 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0)),"")' % (R('bills_month', 'month'), R('bills_month', 'utilities'), R('bills_month', 'utilities'))),
    O('Utilities, last 12 months', 'money', '%s*12' % AV17),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s-1,0)>={in:alert},%s,IF(IFERROR(%s/%s-1,0)>={in:alert},%s,%s))' % (TH17, LY17, V('Higher than last year'), TH17, AV17, V('Seasonal peak'), V('Normal')))],
    GR('What if', ('Worry at 3 percent', {'alert': 0.03}), ('Worry at 5 percent', {'alert': 0.05}), ('Worry at 20 percent', {'alert': 0.20}), ('Worry at 40 percent', {'alert': 0.40}))))

# 18 ----------------------------------------------------------- bills health score
OT18 = lambda a, b: 'COUNTIFS(%s,%s,%s,">="&EDATE(%s,%d),%s,"<"&EDATE(%s,%d))' % (BD('flag'), V('Paid on time'), BD('month'), MS, a, BD('month'), MS, b)
PL18 = lambda a, b: 'COUNTIFS(%s,%s,%s,">="&EDATE(%s,%d),%s,"<"&EDATE(%s,%d))' % (BD('flag'), V('Paid late'), BD('month'), MS, a, BD('month'), MS, b)
SH12 = 'IFERROR(%s/(%s+%s),0)' % (OT18(-12, 0), OT18(-12, 0), PL18(-12, 0)); SH3 = 'IFERROR(%s/(%s+%s),0)' % (OT18(-3, 0), OT18(-3, 0), PL18(-3, 0))
AU18 = 'IFERROR(COUNTIFS(%s,%s,%s,"<>")/COUNTIFS(%s,"<>"),0)' % (BLR('autopay'), YES, BLR('bill_id'), BLR('bill_id'))
LT18 = 'COUNTIFS(%s,"<>"&%s,%s,"<"&{today},%s)' % (BD('status'), PAID, BD('due_date'), ID)
SC18 = 'ROUND(100*(0.5*%s+0.3*%s+0.2*MAX(0,1-%s/MAX(1,{in:late_limit}))),0)' % (SH12, AU18, LT18)
tools.append(TOOL('health_tool', 'Bills Health Score', 'How healthy is the way we pay bills',
    'Type how many late bills you accept; the share paid on time, the autopay share and late bills now become a score out of 100, set against your last 3 months and your own targets.', [
    I('late_limit', 'Late bills you accept at once', 2, 'int')], [
    O('Paid on time, last 12 months', 'pct', SH12), O('Paid on time, last 3 months', 'pct', SH3), O('Your on-time target', 'pct', '{set:on_time_target}'), O('Bills on autopay', 'pct', AU18), O('Late bills now', 'int', LT18),
    O('Bills paid late, last 3 months', 'int', PL18(-3, 0)), O('Bills paid late, last 12 months', 'int', PL18(-12, 0)), O('Score out of 100', 'int', SC18),
    O('Last 3 months against the 12 months', 'pct', '%s-%s' % (SH3, SH12)),
    O('Verdict', 'text', 'IF(AND(%s>={set:on_time_target},%s=0),%s,%s&" "&(%s+%s))' % (SH12, LT18, V('Healthy'), V('Fix bills:'), LT18, PL18(-3, 0)))],
    GR('What if', ('Accept 0 late bills', {'late_limit': 0}), ('Accept 1 late bill', {'late_limit': 1}), ('Accept 5 late bills', {'late_limit': 5}), ('Accept 10 late bills', {'late_limit': 10}))))
assert len(tools) == 18, len(tools)
