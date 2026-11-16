"""Wedding Planning suite part 8: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp8_lists import *
import wp8_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def R(t, c_): return '{range:%s.%s}' % (t, c_)
YES = '{list:yesno.yes}'
PG = tok('basis', 'Per guest'); PT = tok('basis', 'Per table'); FXD = tok('basis', 'Fixed')
DONE_D = tok('dstatus', 'Done'); BOUGHT = tok('sstatus', 'Bought'); TOBUY = tok('sstatus', 'To buy'); ORDERED = tok('sstatus', 'Ordered')
REC = tok('fstatus', 'Received'); PROM = tok('fstatus', 'Promised'); NOTC = tok('fstatus', 'Not confirmed')
HONEY = tok('cuse', 'Honeymoon fund'); BUDGU = tok('cuse', 'Wedding budget'); NOTD = tok('cuse', 'Not decided'); CASHS = tok('source', 'Cash gifts'); HCASH = tok('hsource', 'Cash gifts')
R_DONE = tok('rstatus', 'Done'); R_ARR = tok('rstatus', 'Arranged'); P_DONE = tok('pstatus', 'Done'); P_PROG = tok('pstatus', 'In progress'); P_NOT = tok('pstatus', 'Not started')
tools = []
TODAYS = '{today}'
STORY_GIFT = D.ST['gifts'][0]

# 1 ------------------------------------------------------------ DIY make or buy
SUP1 = 'SUMIFS(%s,%s,{in:project})' % (R('supplies', 'cost'), R('supplies', 'project'))
HRS1 = 'SUMIFS(%s,%s,{in:project})' % (R('diy', 'hours'), R('diy', 'project'))
BUY1 = 'SUMIFS(%s,%s,{in:project})' % (R('diy', 'buy_cost'), R('diy', 'project'))
MAKE1 = 'ROUND(%s+%s*{in:hour_value},2)' % (SUP1, HRS1)
tools.append(TOOL('diy_make_buy', 'DIY Make or Buy', 'Make it or buy it?', 'Pick a project and the value of one hour of your own work; supplies plus your hours are set against the cost to buy it, and the verdict says Make, Buy or Make half.', [
    IL('project', 'DIY project', 'project', 'Ceremony programs'), I('hour_value', 'Value of one hour of your work', 6), I('margin', 'Make only if it costs this much less than buying', 0.15, 'pct')], [
    O('Supplies cost at your headcount and tables', 'money', SUP1), O('Hours of work', 'num', HRS1), O('Value of your hours', 'money', '%s*{in:hour_value}' % HRS1), O('Cost to make', 'money', MAKE1),
    O('Cost to buy or rent', 'money', BUY1), O('Saving from making, a negative number is a loss', 'money', 'ROUND(%s-%s,2)' % (BUY1, MAKE1)), O('Cost to make as share of buying', 'pct', 'IFERROR(%s/%s,0)' % (MAKE1, BUY1)),
    O('Hour value at which making and buying tie', 'money', 'IFERROR(ROUND((%s-%s)/%s,2),0)' % (BUY1, SUP1, HRS1)),
    O('Verdict', 'text', 'IF(%s<=%s*(1-{in:margin}),%s,IF(%s>=%s,%s,%s))' % (MAKE1, BUY1, c('Make'), MAKE1, BUY1, c('Buy'), c('Make half')))],
    GR('What if one hour of your work is worth', ('Nothing', {'hour_value': 0}), ('3 an hour', {'hour_value': 3}), ('6 an hour', {'hour_value': 6}), ('12 an hour', {'hour_value': 12}), ('20 an hour', {'hour_value': 20}))))

# 2 ------------------------------------------------------------ DIY shopping list
def QTY(g, t): return 'ROUNDUP(%s*((%s=%s)*%s+(%s=%s)*%s+(%s=%s)),0)' % (R('supplies', 'qty_per'), R('supplies', 'basis'), PG, g, R('supplies', 'basis'), PT, t, R('supplies', 'basis'), FXD)
UNBOUGHT = '(%s<>%s)*(%s<>"")' % (R('supplies', 'status'), BOUGHT, R('supplies', 'supply_id'))
BUYSC = 'SUMPRODUCT(%s*%s*%s)' % (UNBOUGHT, QTY('{in:guests}', '{in:tables}'), R('supplies', 'unit_cost'))
NITEMS = 'COUNTIFS(%s,"<>"&%s,%s,"<>")' % (R('supplies', 'status'), BOUGHT, R('supplies', 'supply_id'))
tools.append(TOOL('diy_shopping', 'DIY Shopping Run', 'What is still to buy for the DIY projects', 'Type the guests and tables you are buying for; every supply not yet bought is counted and costed, with what is already bought and the verdict Buy [n] items.', [
    I('guests', 'Guests to buy for', 118, 'int'), I('tables', 'Tables to buy for', 13, 'int')], [
    O('Supplies still to buy or collect', 'int', NITEMS), O('Cost still to buy at these numbers', 'money', BUYSC), O('Cost still to buy at your settings', 'money', 'SUM(%s)' % R('supplies', 'cost_to_buy')),
    O('Difference from your settings', 'money', '%s-SUM(%s)' % (BUYSC, R('supplies', 'cost_to_buy'))), O('Ordered, waiting to arrive', 'int', 'COUNTIFS(%s,%s)' % (R('supplies', 'status'), ORDERED)),
    O('Cost already bought', 'money', 'SUMIFS(%s,%s,%s)' % (R('supplies', 'cost'), R('supplies', 'status'), BOUGHT)),
    O('Share of the supplies cost already bought', 'pct', 'IFERROR(SUMIFS(%s,%s,%s)/SUM(%s),0)' % (R('supplies', 'cost'), R('supplies', 'status'), BOUGHT, R('supplies', 'cost'))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s&" "&%s&", "&ROUND(%s,0))' % (NITEMS, c('Nothing to buy'), c('Buy'), NITEMS, c('items'), BUYSC))],
    GR('What if the numbers change', ('80 guests, 8 tables', {'guests': 80, 'tables': 8}), ('100 guests, 10 tables', {'guests': 100, 'tables': 10}), ('118 guests, 13 tables', {'guests': 118, 'tables': 13}),
       ('130 guests, 13 tables', {'guests': 130, 'tables': 13}), ('150 guests, 15 tables', {'guests': 150, 'tables': 15}))))

# 3 ------------------------------------------------------------ DIY start date
WEEKS3 = 'ROUNDUP({in:hours}/{in:hours_week},0)'
LATEST3 = '({set:wedding_day}-{in:buffer}-7*%s)' % WEEKS3
tools.append(TOOL('diy_start', 'DIY Start Date', 'When must a project start to finish early', 'Type the hours, the hours a week you can give and the days before the wedding it must be done; the latest start date and the verdict Start by or Late by are worked out.', [
    I('hours', 'Hours of work in the project', 14, 'num'), I('hours_week', 'Hours a week you can give', 4, 'num'), I('buffer', 'Days before the wedding it must be done', 14, 'int'),
    I('planned', 'Your planned start date', iso(WEDDING_DAY - D.day(50)), 'date')], [
    O('Weeks of work', 'int', WEEKS3), O('Work must be done by', 'date', '{set:wedding_day}-{in:buffer}'), O('Latest start', 'date', LATEST3), O('Days from today to the latest start', 'int', '%s-{today}' % LATEST3),
    O('Your planned start', 'date', '{in:planned}'), O('Days of room before the latest start', 'int', 'MAX(0,%s-{in:planned})' % LATEST3), O('Days late', 'int', 'MAX(0,{in:planned}-%s)' % LATEST3),
    O('Projects already past their latest start', 'int', 'COUNTIFS(%s,%s)' % (R('diy', 'start_flag'), c('Late'))),
    O('Verdict', 'text', 'IF({in:planned}<=%s,%s,%s&" "&({in:planned}-%s)&" "&%s)' % (LATEST3, c('Start by'), c('Late by'), LATEST3, c('days')))],
    GR('What if you give hours a week', ('2 hours a week', {'hours_week': 2}), ('3 hours a week', {'hours_week': 3}), ('4 hours a week', {'hours_week': 4}), ('6 hours a week', {'hours_week': 6}), ('8 hours a week', {'hours_week': 8}))))

# 4 ------------------------------------------------------------ DIY hours load
LEFT4 = 'SUM(%s)' % R('diy', 'hours_left')
WEEKS4 = 'MAX(1,INT(({set:wedding_day}-{in:buffer}-{today})/7))'
def OWN(k): return 'SUMIFS(%s,%s,%s)' % (R('diy', 'hours_left'), R('diy', 'owner'), tok('owner', k))
tools.append(TOOL('diy_load', 'DIY Hours Load', 'Can we fit the DIY hours before the wedding', 'Type the hours a week you can give and the days before the wedding the work must end; hours left, weeks left and each owner share are shown, with the verdict Doable or the hours needed.', [
    I('hours_week', 'Hours a week you can give', 4, 'num'), I('buffer', 'Days before the wedding the work must end', 14, 'int')], [
    O('Hours left on projects not done', 'num', LEFT4), O('Weeks left for the work', 'int', WEEKS4), O('Hours a week needed', 'num', 'ROUND(%s/%s,1)' % (LEFT4, WEEKS4)), O('Hours a week you can give', 'num', '{in:hours_week}'),
    O('Spare hours a week, a negative number is a shortfall', 'num', 'ROUND({in:hours_week}-%s/%s,1)' % (LEFT4, WEEKS4)),
    O('Hours left with partner 1', 'num', OWN('Partner 1')), O('Hours left with partner 2', 'num', OWN('Partner 2')), O('Hours left with the parent of partner 1', 'num', OWN('Parent of partner 1')),
    O('Hours left with the wedding party lead', 'num', OWN('Wedding party lead')), O('Hours left with a friend or relative', 'num', OWN('Friend or relative')),
    O('Verdict', 'text', 'IF(%s/%s<={in:hours_week},%s,ROUNDUP(%s/%s,0)&" "&%s)' % (LEFT4, WEEKS4, c('Doable'), LEFT4, WEEKS4, c('hours a week')))],
    GR('What if you give hours a week', ('1 hour a week', {'hours_week': 1}), ('2 hours a week', {'hours_week': 2}), ('3 hours a week', {'hours_week': 3}), ('4 hours a week', {'hours_week': 4}), ('6 hours a week', {'hours_week': 6}))))

# 5 ------------------------------------------------------------ DIY quantity rescale
ALLQ = '(%s<>"")' % R('supplies', 'supply_id')
NEWC = 'SUMPRODUCT(%s*%s*%s)' % (ALLQ, QTY('{in:guests}', '{in:tables}'), R('supplies', 'unit_cost'))
OLDC = 'SUM(%s)' % R('supplies', 'cost')
BOUGHTX = 'SUMPRODUCT((%s=%s)*(%s-%s)*%s)' % (R('supplies', 'status'), BOUGHT, QTY('{in:guests}', '{in:tables}'), QTY('{set:headcount}', '{set:table_count}'), R('supplies', 'unit_cost'))
tools.append(TOOL('diy_rescale', 'DIY Quantity Rescale', 'What changes if guests or tables change', 'Type the new guest and table counts; every supply quantity is worked out again from them and set against your settings, so you know the extra to order and the verdict Order for [n] tables.', [
    I('guests', 'New number of guests', 130, 'int'), I('tables', 'New number of tables', 13, 'int')], [
    O('Guests in your settings', 'int', '{set:headcount}'), O('Tables in your settings', 'int', '{set:table_count}'), O('Supplies cost at your settings', 'money', OLDC), O('Supplies cost at the new numbers', 'money', NEWC),
    O('Change in cost', 'money', '%s-%s' % (NEWC, OLDC)), O('Extra to buy on supplies you already bought', 'money', BOUGHTX),
    O('Per-guest supplies for each added guest', 'money', 'IFERROR((SUMPRODUCT(%s*(%s=%s)*%s*%s)/{set:headcount}),0)' % (ALLQ, R('supplies', 'basis'), PG, R('supplies', 'qty_per'), R('supplies', 'unit_cost'))),
    O('Verdict', 'text', '%s&" "&{in:tables}&" "&%s' % (c('Order for'), c('tables')))],
    GR('What if the numbers change', ('60 guests, 6 tables', {'guests': 60, 'tables': 6}), ('100 guests, 10 tables', {'guests': 100, 'tables': 10}), ('118 guests, 13 tables', {'guests': 118, 'tables': 13}),
       ('130 guests, 13 tables', {'guests': 130, 'tables': 13}), ('150 guests, 15 tables', {'guests': 150, 'tables': 15}))))

# 6 ------------------------------------------------------------ attire tracker
FIRST6 = 'MATCH(1,%s,0)' % R('attire', 'order_rank')
NTO = 'COUNTIFS(%s,%s)' % (R('attire', 'status'), TOBUY)
tools.append(TOOL('attire_order', 'Attire Order Planner', 'Which attire item do we order next', 'Type how many days ahead you look; items still to order are counted and costed, the next order-by date is named and the verdict says Order [item] or Nothing to order.', [
    I('days', 'Days ahead to look', 90, 'int')], [
    O('Items still to order', 'int', NTO), O('Cost of items still to order', 'money', 'SUMIFS(%s,%s,%s)' % (R('attire', 'cost'), R('attire', 'status'), TOBUY)), O('Items ordered, waiting to arrive', 'int', 'COUNTIFS(%s,%s)' % (R('attire', 'status'), ORDERED)),
    O('Items bought', 'int', 'COUNTIFS(%s,%s)' % (R('attire', 'status'), BOUGHT)), O('Next item to order', 'text', 'IFERROR(INDEX(%s,%s),"")' % (R('attire', 'item'), FIRST6)),
    O('Order it by', 'date', 'IFERROR(INDEX(%s,%s),"")' % (R('attire', 'order_by'), FIRST6)), O('Days left to order it', 'int', 'IFERROR(INDEX(%s,%s)-{today},"")' % (R('attire', 'order_by'), FIRST6)),
    O('Items to order within the days ahead', 'int', 'COUNTIFS(%s,%s,%s,"<="&({today}+{in:days}))' % (R('attire', 'status'), TOBUY, R('attire', 'order_by'))),
    O('Their cost', 'money', 'SUMIFS(%s,%s,%s,%s,"<="&({today}+{in:days}))' % (R('attire', 'cost'), R('attire', 'status'), TOBUY, R('attire', 'order_by'))),
    O('Attire cost inside the budget', 'money', 'SUMIFS(%s,%s,%s)' % (R('attire', 'cost'), R('attire', 'in_budget'), YES)),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&IFERROR(INDEX(%s,%s),""))' % (NTO, c('Nothing to order'), c('Order'), R('attire', 'item'), FIRST6))],
    GR('What if you look ahead', ('30 days', {'days': 30}), ('60 days', {'days': 60}), ('90 days', {'days': 90}), ('120 days', {'days': 120}), ('180 days', {'days': 180}))))

# 7 ------------------------------------------------------------ gift and thank-you tracker
GM = 'MATCH({in:gift_id},%s,0)' % R('gifts', 'gift_id')
def GI(c_): return 'IFERROR(INDEX(%s,%s),"")' % (R('gifts', c_), GM)
tools.append(TOOL('gift_tracker', 'Gift and Thank-you Tracker', 'Has this household been thanked', 'Type a gift ID; the household, the gift, the days since it arrived, the note written and sent dates and the days left to your own target are shown, with the verdict Write now or On time.', [
    I('gift_id', 'Gift ID', STORY_GIFT, 'text')], [
    O('Household', 'text', GI('household')), O('Event', 'text', GI('event')), O('Gift', 'text', GI('description')), O('Gift date', 'date', GI('date')),
    O('Days since the gift', 'int', 'IFERROR({today}-INDEX(%s,%s),"")' % (R('gifts', 'date'), GM)), O('Your target, days', 'int', '{set:thankyou_target_days}'),
    O('Days left to your target', 'int', 'IFERROR({set:thankyou_target_days}-({today}-INDEX(%s,%s)),"")' % (R('gifts', 'date'), GM)),
    O('Note written on', 'date', 'IFERROR(IF(INDEX(%s,%s)="",%s,INDEX(%s,%s)),"")' % (R('gifts', 'written_on'), GM, c('Write now'), R('gifts', 'written_on'), GM)),
    O('Note sent on', 'date', 'IFERROR(IF(INDEX(%s,%s)="",IF(INDEX(%s,%s)=1,%s,%s),INDEX(%s,%s)),"")' % (R('gifts', 'sent_on'), GM, R('gifts', 'thanked'), GM, c('Not sent yet'), c('Open'), R('gifts', 'sent_on'), GM)),
    O('Verdict', 'text', 'IFERROR(IF(INDEX(%s,%s)=1,IF(INDEX(%s,%s)="",%s,%s),IF(INDEX(%s,%s)=1,%s,%s)),"")' % (R('gifts', 'thanked'), GM, R('gifts', 'sent_on'), GM, c('Not sent yet'), c('Sent'), R('gifts', 'late'), GM, c('Write now'), c('On time')))]))

# 8 ------------------------------------------------------------ thank-you backlog ranker
LATE8 = 'COUNTIFS(%s,0,%s,">"&{in:days})' % (R('gifts', 'thanked'), R('gifts', 'days_waiting'))
WAIT8 = 'COUNTIFS(%s,0)' % R('gifts', 'thanked')
def TOP8(k):
    m = 'MATCH(%d,%s,0)' % (k, R('gifts', 'wait_rank'))
    return 'IFERROR(INDEX(%s,%s)&" "&INDEX(%s,%s)&" "&INDEX(%s,%s),"")' % (R('gifts', 'gift_id'), m, R('gifts', 'household'), m, R('gifts', 'days_waiting'), m)
tools.append(TOOL('backlog_ranker', 'Thank-you Backlog Ranker', 'Which gifts need a note first', 'Type the days after which a gift without a note is late; the gifts waiting are counted, the oldest five are named with their wait, and the verdict says how many notes to write this week.', [
    I('days', 'Days after which a note is late', 14, 'int')], [
    O('Gifts without a note', 'int', WAIT8), O('Late under your days', 'int', LATE8), O('Oldest wait, days', 'int', 'MAX(%s)' % R('gifts', 'days_waiting')),
    O('Average wait, days', 'num', 'IFERROR(AVERAGEIFS(%s,%s,0),0)' % (R('gifts', 'days_waiting'), R('gifts', 'thanked'))), O('Cash among the gifts waiting', 'money', 'SUMIFS(%s,%s,0)' % (R('gifts', 'amount'), R('gifts', 'thanked'))),
    O('First: gift, household, days waiting', 'text', TOP8(1)), O('Second: gift, household, days waiting', 'text', TOP8(2)), O('Third: gift, household, days waiting', 'text', TOP8(3)),
    O('Fourth: gift, household, days waiting', 'text', TOP8(4)), O('Fifth: gift, household, days waiting', 'text', TOP8(5)),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s=0,%s,%s&" "&%s&" "&%s))' % (WAIT8, c('Nothing waiting'), LATE8, c('On time'), c('Write'), LATE8, c('notes this week')))],
    GR('What if a note is late after', ('7 days', {'days': 7}), ('14 days', {'days': 14}), ('21 days', {'days': 21}), ('28 days', {'days': 28}), ('35 days', {'days': 35}))))

# 9 ------------------------------------------------------------ thank-you pace
WAIT9 = 'COUNTIFS(%s,0)' % R('gifts', 'thanked')
TGT9 = '({today}-MAX(%s)+{set:thankyou_target_days})' % R('gifts', 'days_waiting')
WK9 = 'MAX(1,ROUNDUP((%s-{today})/7,0))' % TGT9
tools.append(TOOL('thankyou_pace', 'Thank-you Pace', 'How many notes a week to finish on time', 'Type the weeks you give yourself; the notes waiting are divided by the weeks, and the pace is also worked out for your own target date counted from the oldest gift.', [
    I('weeks', 'Weeks you give yourself', 3, 'int')], [
    O('Gifts without a note', 'int', WAIT9), O('Finish by', 'date', '{today}+7*{in:weeks}'), O('Notes a week to finish by then', 'int', 'ROUNDUP(%s/{in:weeks},0)' % WAIT9),
    O('Your target date for the oldest gift', 'date', TGT9), O('Weeks to that date', 'int', WK9), O('Notes a week to meet that date', 'int', 'ROUNDUP(%s/%s,0)' % (WAIT9, WK9)),
    O('Notes written so far', 'int', 'COUNTIFS(%s,"<>")' % R('thanks', 'note_id')), O('Gifts received', 'int', 'COUNTIFS(%s,"<>")' % R('gifts', 'gift_id')),
    O('Written, not sent yet', 'int', 'COUNTIFS(%s,"<>")-COUNTIFS(%s,">0")' % (R('thanks', 'note_id'), R('thanks', 'sent_on'))),
    O('Verdict', 'text', 'IF(%s=0,%s,ROUNDUP(%s/{in:weeks},0)&" "&%s)' % (WAIT9, c('Finished'), WAIT9, c('a week to finish by')))],
    GR('What if you give yourself', ('1 week', {'weeks': 1}), ('2 weeks', {'weeks': 2}), ('3 weeks', {'weeks': 3}), ('4 weeks', {'weeks': 4}), ('6 weeks', {'weeks': 6}))))

# 10 ----------------------------------------------------------- cash gifts and funding link
GAP10 = 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (R('fundlink', 'gap'), R('fundlink', 'agreed'), R('fundlink', 'agreed'))
EXP10 = 'SUMIFS(%s,%s,%s,%s,%s)' % (R('funding', 'amount'), R('funding', 'source'), CASHS, R('funding', 'status'), NOTC)
REC10 = 'SUM(%s)' % R('gifts', 'amount')
tools.append(TOOL('cash_funding', 'Cash Gifts and Funding', 'What do cash gifts do for the budget gap', 'Cash gifts received are split between the budget and the honeymoon; expected gifts are never counted until they arrive, and the share you type is only a what-if on the budget gap.', [
    I('arrive', 'Share of expected cash gifts you assume arrive', 0.5, 'pct')], [
    O('Cash gifts received', 'money', REC10), O('Cash gifts received, count', 'int', 'COUNTIFS(%s,">0")' % R('gifts', 'amount')), O('Received for the wedding budget', 'money', 'SUMIFS(%s,%s,%s)' % (R('gifts', 'amount'), R('gifts', 'cash_use'), BUDGU)),
    O('Received for the honeymoon', 'money', 'SUMIFS(%s,%s,%s)' % (R('gifts', 'amount'), R('gifts', 'cash_use'), HONEY)), O('Received, no plan yet', 'money', 'SUMIFS(%s,%s,%s)' % (R('gifts', 'amount'), R('gifts', 'cash_use'), NOTD)),
    O('Expected for the budget, not confirmed', 'money', EXP10), O('Budget gap before cash gifts', 'money', GAP10),
    O('Budget gap after the cash gifts received for the budget', 'money', '%s-SUMIFS(%s,%s,%s)' % (GAP10, R('gifts', 'amount'), R('gifts', 'cash_use'), BUDGU)),
    O('Budget gap if your share of the expected gifts arrives', 'money', '%s-SUMIFS(%s,%s,%s)-{in:arrive}*%s' % (GAP10, R('gifts', 'amount'), R('gifts', 'cash_use'), BUDGU, EXP10)),
    O('Verdict', 'text', '%s&" "&ROUND(%s,0)&", "&%s' % (c('Received'), REC10, c('expected gifts count only when received')))],
    GR('What if the expected gifts arrive', ('None arrive', {'arrive': 0}), ('A quarter arrive', {'arrive': 0.25}), ('Half arrive', {'arrive': 0.5}), ('Three quarters arrive', {'arrive': 0.75}), ('All arrive', {'arrive': 1}))))

# 11 ----------------------------------------------------------- payment service fee
VIA11 = 'SUMIFS(%s,%s,%s)' % (R('gifts', 'amount'), R('gifts', 'via_provider'), YES)
NV11 = 'COUNTIFS(%s,%s,%s,">0")' % (R('gifts', 'via_provider'), YES, R('gifts', 'amount'))
FEE11 = '(%s*{in:fee_pct}+%s*{in:fee_flat})' % (VIA11, NV11)
tools.append(TOOL('cash_fee', 'Payment Service Fee', 'What do we keep of the cash gifts', 'Type the percent and the fixed fee your payment provider charges on a cash gift; only gifts marked as paid through it carry a fee, and the verdict shows what you keep.', [
    I('fee_pct', 'Fee your provider charges, percent', 0.029, 'pct'), I('fee_flat', 'Fixed fee per gift your provider charges', 0.30)], [
    O('Cash gifts through your provider', 'money', VIA11), O('Number of those gifts', 'int', NV11), O('Fee in total', 'money', 'ROUND(%s,2)' % FEE11), O('You keep from those gifts', 'money', 'ROUND(%s-%s,2)' % (VIA11, FEE11)),
    O('Fee as share of those gifts', 'pct', 'IFERROR(%s/%s,0)' % (FEE11, VIA11)), O('Average fee per gift', 'money', 'IFERROR(ROUND(%s/%s,2),0)' % (FEE11, NV11)),
    O('All cash gifts received', 'money', 'SUM(%s)' % R('gifts', 'amount')), O('You keep from all cash gifts', 'money', 'ROUND(SUM(%s)-%s,2)' % (R('gifts', 'amount'), FEE11)),
    O('Verdict', 'text', '%s&" "&ROUND(SUM(%s)-%s,2)' % (c('You keep'), R('gifts', 'amount'), FEE11))],
    GR('What if your provider charges', ('No fee', {'fee_pct': 0, 'fee_flat': 0}), ('1.5 percent', {'fee_pct': 0.015}), ('2.9 percent', {'fee_pct': 0.029}), ('4 percent', {'fee_pct': 0.04}), ('5 percent and a fixed fee of 0.5', {'fee_pct': 0.05, 'fee_flat': 0.5}))))

# 12 ----------------------------------------------------------- gifts toward the honeymoon
FUNDS12 = '(SUMIFS(%s,%s,%s)+SUMIFS(%s,%s,%s))' % (R('honeyfund', 'amount'), R('honeyfund', 'status'), REC, R('gifts', 'amount'), R('gifts', 'cash_use'), HONEY)
PROM12 = 'SUMIFS(%s,%s,%s)' % (R('honeyfund', 'amount'), R('honeyfund', 'status'), PROM)
GAP12 = '({in:goal}-%s-%s)' % (FUNDS12, PROM12)
MON12 = 'MAX(1,DATEDIF({today},{set:wedding_day},"M"))'
tools.append(TOOL('honeymoon_gap', 'Honeymoon Gap', 'Can the cash gifts close the honeymoon gap', 'Type the honeymoon budget and the extra you could save each month; funds received and promised savings are set against it, and the verdict says Gap closed or Short by an amount.', [
    I('goal', 'Honeymoon budget', 4850), I('extra', 'Extra you could save a month', 0)], [
    O('Honeymoon budget', 'money', '{in:goal}'), O('Funds received, savings and cash gifts for the honeymoon', 'money', FUNDS12), O('Cash gifts received for the honeymoon', 'money', 'SUMIFS(%s,%s,%s)' % (R('gifts', 'amount'), R('gifts', 'cash_use'), HONEY)),
    O('Savings promised', 'money', PROM12), O('Gap, a negative number is a surplus', 'money', GAP12), O('Cash gifts expected for the honeymoon, not confirmed', 'money', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('honeyfund', 'amount'), R('honeyfund', 'source'), HCASH, R('honeyfund', 'status'), NOTC)),
    O('Months to the wedding', 'int', MON12), O('Saving needed a month to close the gap', 'money', 'ROUND(MAX(0,%s)/%s,0)' % (GAP12, MON12)), O('Gap after your extra savings', 'money', '%s-{in:extra}*%s' % (GAP12, MON12)),
    O('Verdict', 'text', 'IF(%s-{in:extra}*%s<=0,%s,%s&" "&ROUND(%s-{in:extra}*%s,0))' % (GAP12, MON12, c('Gap closed'), c('Short by'), GAP12, MON12))],
    GR('What if you save a month', ('Nothing extra', {'extra': 0}), ('50 extra', {'extra': 50}), ('100 extra', {'extra': 100}), ('150 extra', {'extra': 150}), ('200 extra', {'extra': 200}))))

# 13 ----------------------------------------------------------- final budget against actual
TP = 'SUM(%s)' % R('final', 'planned'); TC = 'SUM(%s)' % R('final', 'committed'); TPD = 'SUM(%s)' % R('final', 'paid')
def FC(c_): return 'IFERROR(INDEX(%s,MATCH({in:category},%s,0)),0)' % (R('final', c_), R('final', 'category'))
tools.append(TOOL('final_vs_plan', 'Final Budget Check', 'Where did the budget end up against the plan', 'Pick a category and type an extra cost you are thinking of; plan, final cost so far and variance are shown in total and for the category, with the verdict over or under plan.', [
    IL('category', 'Budget category', 'category', 'Flowers and decor'), I('extra', 'Extra cost you are thinking of', 0)], [
    O('Planned in total', 'money', TP), O('Committed in total, the final cost so far', 'money', TC), O('Paid in total', 'money', TPD), O('Still due in total', 'money', '%s-%s' % (TC, TPD)),
    O('Over or under plan in total, a negative number is under', 'money', '%s-%s' % (TC, TP)), O('Over or under plan as a share of the plan', 'pct', 'IFERROR((%s-%s)/%s,0)' % (TC, TP, TP)),
    O('Budget lines over plan', 'int', 'COUNTIFS(%s,">0")' % R('final', 'variance')), O('Planned for the category', 'money', FC('planned')), O('Committed for the category', 'money', FC('committed')),
    O('Over or under plan for the category', 'money', FC('variance')), O('Over or under plan for the category, share', 'pct', 'IFERROR(%s/%s,0)' % (FC('variance'), FC('planned'))),
    O('Largest overrun, a category', 'text', 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0)),"")' % (R('final', 'category'), R('final', 'variance'), R('final', 'variance'))),
    O('Final cost with your extra', 'money', '%s+{in:extra}' % TC),
    O('Verdict', 'text', '%s&" "&ROUND(%s+{in:extra},0)&", "&ROUND(ABS(%s+{in:extra}-%s),0)&" "&IF(%s+{in:extra}-%s<=0,%s,%s)' % (c('Final cost'), TC, TC, TP, TC, TP, c('under plan'), c('over plan')))],
    GR('What if the extra cost is', ('Nothing', {'extra': 0}), ('250', {'extra': 250}), ('500', {'extra': 500}), ('1000', {'extra': 1000}), ('2000', {'extra': 2000}))))

# 14 ----------------------------------------------------------- cost per guest
tools.append(TOOL('cost_per_guest', 'Cost per Guest Check', 'What did the wedding really cost per guest', 'Type the final cost and the final headcount; the cost per guest is set against your own target and the typical starting value, with the verdict per guest and above or below target.', [
    I('cost', 'Final cost so far', sum(b['committed'] for b in D.BUD)), I('guests', 'Final headcount', 118, 'int')], [
    O('Cost per guest', 'money', 'ROUND({in:cost}/{in:guests},0)'), O('Your target per guest', 'money', '{set:cost_per_guest_target}'), O('Above or below your target, per guest', 'money', 'ROUND({in:cost}/{in:guests}-{set:cost_per_guest_target},0)'),
    O('Typical starting value per guest, edit', 'money', '{set:cost_per_guest_bench}'), O('Above or below the typical value, per guest', 'money', 'ROUND({in:cost}/{in:guests}-{set:cost_per_guest_bench},0)'),
    O('Above or below your target, in total', 'money', '{in:cost}-{in:guests}*{set:cost_per_guest_target}'), O('Guests the cost would cover at your target', 'int', 'ROUND({in:cost}/{set:cost_per_guest_target},0)'),
    O('Catering and bar per guest', 'money', 'ROUND(SUMIFS(%s,%s,%s)/{in:guests},0)' % (R('budget', 'committed'), R('budget', 'category'), tok('category', 'Catering and bar'))),
    O('Verdict', 'text', 'ROUND({in:cost}/{in:guests},0)&" "&%s&", "&ABS(ROUND({in:cost}/{in:guests}-{set:cost_per_guest_target},0))&" "&IF(ROUND({in:cost}/{in:guests}-{set:cost_per_guest_target},0)>0,%s,IF(ROUND({in:cost}/{in:guests}-{set:cost_per_guest_target},0)<0,%s,%s))' % (c('per guest'), c('above target'), c('below target'), c('On target')))],
    GR('What if the final headcount is', ('100 guests', {'guests': 100}), ('110 guests', {'guests': 110}), ('118 guests', {'guests': 118}), ('130 guests', {'guests': 130}), ('150 guests', {'guests': 150}))))

# 15 ----------------------------------------------------------- unpaid vendor balances
WIN15 = 'COUNTIFS(%s,">0",%s,"<="&({today}+{in:days}))' % (R('balances', 'still_due'), R('balances', 'next_due'))
AMT15 = 'SUMIFS(%s,%s,">0",%s,"<="&({today}+{in:days}))' % (R('balances', 'still_due'), R('balances', 'still_due'), R('balances', 'next_due'))
tools.append(TOOL('vendor_balances', 'Vendor Balance Check', 'Which vendors do we still owe', 'Type the days ahead you look; the vendors with a balance, the total still due, what falls due soon or is overdue and the next payment date are shown, with the verdict Pay [n] balances.', [
    I('days', 'Days ahead to look', 30, 'int')], [
    O('Vendors with a balance', 'int', 'COUNTIFS(%s,">0")' % R('balances', 'still_due')), O('Total still due', 'money', 'SUM(%s)' % R('balances', 'still_due')), O('Paid so far', 'money', 'SUM(%s)' % R('balances', 'paid')),
    O('Share of the contracts paid', 'pct', 'IFERROR(SUM(%s)/SUM(%s),0)' % (R('balances', 'paid'), R('balances', 'contract_total'))), O('Vendors with a payment due in the days ahead or overdue', 'int', WIN15),
    O('Their balance in total', 'money', AMT15), O('Vendors overdue', 'int', 'COUNTIFS(%s,%s)' % (R('balances', 'state'), c('Overdue'))), O('Next payment date', 'date', 'SMALL(%s,1)' % R('balances', 'next_key')),
    O('Largest balance', 'money', 'MAX(%s)' % R('balances', 'still_due')), O('Vendor with the largest balance', 'text', 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0)),"")' % (R('balances', 'vendor'), R('balances', 'still_due'), R('balances', 'still_due'))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s&" "&%s&", "&ROUND(%s,0))' % (WIN15, c('Nothing to pay'), c('Pay'), WIN15, c('balances'), AMT15))],
    GR('What if you look ahead', ('14 days', {'days': 14}), ('30 days', {'days': 30}), ('60 days', {'days': 60}), ('120 days', {'days': 120}), ('200 days', {'days': 200}))))

# 16 ----------------------------------------------------------- returns and refunds tracker
NOP16 = 'COUNTIFS(%s,"<>")-COUNTIFS(%s,%s)' % (R('returns', 'return_id'), R('returns', 'status'), R_DONE)
WIN16 = 'COUNTIFS(%s,"<="&({today}+{in:days}))' % R('returns', 'open_key')
tools.append(TOOL('returns_tracker', 'Returns and Refunds Tracker', 'What must go back and which deposits do we claim', 'Type the days ahead you look; rentals, borrowed items and deposits not yet done are counted, the first and last due dates are named, and the verdict says Return [n] items and the refunds expected.', [
    I('days', 'Days ahead to look', 365, 'int')], [
    O('Items not yet done', 'int', NOP16), O('Items due in the days ahead', 'int', WIN16), O('Refunds expected', 'money', 'SUMIFS(%s,%s,"<>"&%s)' % (R('returns', 'refund'), R('returns', 'status'), R_DONE)),
    O('Deposits and credits to claim', 'int', 'COUNTIFS(%s,%s,%s,"<>"&%s)' % (R('returns', 'kind'), tok('rkind', 'Deposit refund'), R('returns', 'status'), R_DONE)), O('First due date', 'date', 'SMALL(%s,1)' % R('returns', 'open_key')),
    O('Days to the first due date', 'int', 'SMALL(%s,1)-{today}' % R('returns', 'open_key')), O('Last due date', 'date', 'LARGE(%s,1)' % R('returns', 'open_key')), O('Items with a pick-up or return arranged', 'int', 'COUNTIFS(%s,%s)' % (R('returns', 'status'), R_ARR)),
    O('Items overdue', 'int', 'COUNTIFS(%s,%s)' % (R('returns', 'flag'), c('Overdue'))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s&" "&%s&", "&%s&" "&ROUND(SUMIFS(%s,%s,"<>"&%s),0))' % (WIN16, c('Nothing to return'), c('Return'), WIN16, c('items'), c('refunds'), R('returns', 'refund'), R('returns', 'status'), R_DONE))],
    GR('What if you look ahead', ('30 days', {'days': 30}), ('120 days', {'days': 120}), ('210 days', {'days': 210}), ('240 days', {'days': 240}), ('365 days', {'days': 365}))))

# 17 ----------------------------------------------------------- paperwork and name change tracker
OPEN17 = '(COUNTIFS(%s,"<>")-COUNTIFS(%s,%s)-(1-{in:optional})*COUNTIFS(%s,%s,%s,"<>"&%s))' % (R('paperwork', 'item_id'), R('paperwork', 'status'), P_DONE, R('paperwork', 'optional'), YES, R('paperwork', 'status'), P_DONE)
tools.append(TOOL('paperwork_tracker', 'Paperwork Tracker', 'Where are we on the paperwork and name change steps', 'Type 1 to count the optional steps or 0 to leave them out; steps are counted by status and the verdict says how many are done and open. Check with your officiant or local office.', [
    I('optional', 'Count the optional steps, 1 for yes and 0 for no', 1, 'int')], [
    O('Steps in total', 'int', 'COUNTIFS(%s,"<>")' % R('paperwork', 'item_id')), O('Done', 'int', 'COUNTIFS(%s,%s)' % (R('paperwork', 'status'), P_DONE)), O('In progress', 'int', 'COUNTIFS(%s,%s)' % (R('paperwork', 'status'), P_PROG)),
    O('Not started', 'int', 'COUNTIFS(%s,%s)' % (R('paperwork', 'status'), P_NOT)), O('Required steps still open', 'int', 'COUNTIFS(%s,{list:yesno.no},%s,"<>"&%s)' % (R('paperwork', 'optional'), R('paperwork', 'status'), P_DONE)),
    O('Optional steps still open', 'int', 'COUNTIFS(%s,%s,%s,"<>"&%s)' % (R('paperwork', 'optional'), YES, R('paperwork', 'status'), P_DONE)), O('Steps overdue', 'int', 'COUNTIFS(%s,%s)' % (R('paperwork', 'flag'), c('Overdue'))),
    O('Next due date', 'date', 'SMALL(%s,1)' % R('paperwork', 'next_key')), O('Days to the next due date', 'int', 'SMALL(%s,1)-{today}' % R('paperwork', 'next_key')),
    O('Verdict', 'text', '%s&" "&COUNTIFS(%s,%s)&", "&%s&" "&%s' % (c('Done'), R('paperwork', 'status'), P_DONE, c('open'), OPEN17))],
    GR('What if the optional steps are', ('Left out', {'optional': 0}), ('Counted', {'optional': 1}))))

# 18 ----------------------------------------------------------- wrap-up readiness
OPEN18 = '(COUNTIFS(%s,%s)-{in:skip}*(COUNTIFS(%s,%s,%s,"<>"&%s)>0))' % (R('wrapup', 'status'), c('To finish'), R('paperwork', 'optional'), YES, R('paperwork', 'status'), P_DONE)
tools.append(TOOL('wrapup_ready', 'Wrap-up Readiness', 'Can we close the wedding', 'Type 1 to leave the optional name change steps out of the count; the ten wrap-up checks are counted, the main open items are shown and the verdict says Close the wedding or how many checks are left.', [
    I('skip', 'Leave out the optional steps, 1 for yes and 0 for no', 0, 'int')], [
    O('Checks in total', 'int', 'COUNTIFS(%s,"<>")' % R('wrapup', 'check')), O('Checks done', 'int', 'COUNTIFS(%s,%s)' % (R('wrapup', 'status'), c('Done'))), O('Checks still to finish', 'int', OPEN18),
    O('Vendor balances unpaid', 'int', 'COUNTIFS(%s,">0")' % R('balances', 'still_due')), O('Returns and deposits not done', 'int', 'COUNTIFS(%s,"<>")-COUNTIFS(%s,%s)' % (R('returns', 'return_id'), R('returns', 'status'), R_DONE)),
    O('Gifts without a thank-you note', 'int', 'COUNTIFS(%s,0)' % R('gifts', 'thanked')), O('Notes written, not sent', 'int', 'COUNTIFS(%s,"<>")-COUNTIFS(%s,">0")' % (R('thanks', 'note_id'), R('thanks', 'sent_on'))),
    O('Budget lines over plan', 'int', 'COUNTIFS(%s,">0")' % R('final', 'variance')),
    O('Share of the checks done', 'pct', 'IFERROR(COUNTIFS(%s,%s)/COUNTIFS(%s,"<>"),0)' % (R('wrapup', 'status'), c('Done'), R('wrapup', 'check'))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (OPEN18, c('Close the wedding'), OPEN18, c('to finish')))],
    GR('What if the optional steps are', ('Counted', {'skip': 0}), ('Left out', {'skip': 1}))))
assert len(tools) == 18
