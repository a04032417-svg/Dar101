"""Wedding Planning suite part 8: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp8_lists import *
import wp8_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def LIT(key_, label, phone): return CA(key_, label, 'text', '"%s"' % phone, 18)
def CPL(): return CA('couple', 'Couple', 'text', '{set:couple}', 20)
def PARTNER(): return LIT('partner_phone', 'Partner phone', D.PARTNER_PHONE)
def FRIEND(): return LIT('friend_phone', 'Friend helper phone', D.FRIEND_PHONE)
def AT(t, src): return 'IF({col:at}="","",INDEX({range:%s.%s},{col:at}))' % (t, src)

YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
PG = tok('basis', 'Per guest'); PT = tok('basis', 'Per table'); FXD = tok('basis', 'Fixed')
DONE_D = tok('dstatus', 'Done'); IDEA = tok('dstatus', 'Idea')
BOUGHT = tok('sstatus', 'Bought'); TOBUY = tok('sstatus', 'To buy')
REC = tok('fstatus', 'Received'); PROM = tok('fstatus', 'Promised'); NOTC = tok('fstatus', 'Not confirmed')
CASHK = tok('gkind', 'Cash gift'); HONEY = tok('cuse', 'Honeymoon fund'); BUDGU = tok('cuse', 'Wedding budget')
CASHS = tok('source', 'Cash gifts'); HCASH = tok('hsource', 'Cash gifts')
R_DONE = tok('rstatus', 'Done'); R_NOT = tok('rstatus', 'Not due')
P_DONE = tok('pstatus', 'Done')
MAKE = c('Make'); BUY = c('Buy'); HALF = c('Make half')

settings = [
    S('couple', 'Your names, for the pages and texts', 'text', 'Amara and Theo'),
    S('wedding_day', 'Wedding day', 'date', iso(WEDDING_DAY)),
    S('headcount', 'Final headcount for costing (your forecast), guests', 'int', 118),
    S('table_count', 'Tables in your seating plan (from the seating plan)', 'int', 13),
    S('diy_hour_value', 'What one hour of your own work is worth, your own number', 'money', 6),
    S('diy_buffer_days', 'Days before the wedding DIY must be done, your own number', 'int', DIY_BUFFER_DAYS),
    S('diy_hours_week', 'Hours a week you can give to DIY, your own number', 'num', 4),
    S('make_margin', 'Make only if it costs this much less than buying, your rule', 'pct', 0.15),
    S('thankyou_target_days', 'Days after a gift you want the note written, your own target', 'int', THANKYOU_TARGET_DAYS),
    S('thankyou_alert_days', 'Days after which a gift with no note is flagged, your alert', 'int', THANKYOU_ALERT_DAYS),
    S('cost_per_guest_target', 'Cost per guest you aim for, your own number', 'money', COST_PER_GUEST_TARGET),
    S('cost_per_guest_bench', 'Typical starting cost per guest, edit, not a fact about you', 'money', COST_PER_GUEST_BENCHMARK),
    S('provider_fee_pct', 'Percent fee your payment provider charges: your own figure', 'pct', 0.029),
    S('provider_fee_flat', 'Fixed fee per gift your payment provider charges, yours', 'money', 0.30),
    S('honeymoon_goal', 'Honeymoon budget you chose (for example Option A), edit', 'money', 4850),
    S('soon_days', 'Days before a date that count as due soon, your own number', 'int', 30),
    S('order_window_days', 'Days before an order-by date you start, your own number', 'int', 90),
    S('watch_pct', 'Over plan up to this share is Watch, more is Over (edit)', 'pct', 0.10),
]
assert 3 <= len(settings) <= 20
tables = []

# 1 DIY projects -----------------------------------------------------------------------------------------------------------
tables.append(T('diy', 'DIY projects', 'DIY Projects', 'One row per make-it-yourself project: hours, the cost to buy it, status, planned start and owner; supplies cost, cost to make, saving, Make or Buy and the latest start fill in.', [
    C('diy_id', 'DIY ID', 'text', 9, required=True), LST('project', 'Project', 'project', 34), LST('basis', 'Basis', 'basis', 11), C('hours', 'Hours', 'num', 8), C('buy_cost', 'Cost to buy', 'money', 11),
    LST('status', 'Status', 'dstatus', 15), C('start_by', 'Planned start', 'date', 12), LST('owner', 'Owner', 'owner', 20),
    CA('units', 'Units', 'int', 'IF({col:basis}=%s,{set:headcount},IF({col:basis}=%s,{set:table_count},1))' % (PG, PT), 8),
    CA('supplies_cost', 'Supplies cost', 'money', 'SUMIFS({range:supplies.cost},{range:supplies.diy_id},{col:diy_id})', 11),
    CA('make_cost', 'Cost to make', 'money', 'ROUND({col:supplies_cost}+{col:hours}*{set:diy_hour_value},2)', 11),
    CA('saving', 'Saving from making', 'money', '{col:buy_cost}-{col:make_cost}', 11),
    CA('ratio', 'Make cost as share of buy', 'pct', 'IF({col:buy_cost}>0,{col:make_cost}/{col:buy_cost},0)', 10),
    CA('make_or_buy', 'Make or buy', 'text', 'IF({col:ratio}<=1-{set:make_margin},%s,IF({col:ratio}>=1,%s,%s))' % (MAKE, BUY, HALF), 12),
    CA('hours_left', 'Hours left', 'num', 'IF({col:status}=%s,0,{col:hours})' % DONE_D, 8),
    CA('weeks_needed', 'Weeks of work', 'int', 'ROUNDUP({col:hours}/{set:diy_hours_week},0)', 8),
    CA('latest_start', 'Latest start', 'date', '{set:wedding_day}-{set:diy_buffer_days}-7*{col:weeks_needed}', 12),
    CA('days_to_start', 'Days to planned start', 'int', 'IF({col:status}=%s,"",{col:start_by}-{today})' % DONE_D, 9),
    CA('start_flag', 'Start check', 'text', 'IF({col:status}=%s,%s,IF({col:start_by}>{col:latest_start},%s,IF(AND({col:status}=%s,{col:start_by}<{today}),%s,%s)))' % (DONE_D, c('Done'), c('Late'), IDEA, c('Start now'), c('On time')), 11),
    CA('item', 'First supply', 'text', 'IFERROR(INDEX({range:supplies.item},MATCH({col:diy_id},{range:supplies.diy_id},0)),"")', 22),
    CPL(), FRIEND(), LIT('parent1_phone', 'Parent of partner 1 phone', D.P1PARENT_PHONE), LIT('parent2_phone', 'Parent of partner 2 phone', D.P2PARENT_PHONE),
    LIT('lead_phone', 'Wedding party lead phone', D.LEAD_PHONE), PARTNER()],
    D.diy_d(), 60, [A('make_or_buy', '= ' + MAKE, 'good'), A('make_or_buy', '= ' + BUY, 'warn'), A('start_flag', '= ' + c('Late'), 'bad'), A('start_flag', '= ' + c('Start now'), 'warn')]))

# 2 Supplies ----------------------------------------------------------------------------------------------------------------
tables.append(T('supplies', 'Supplies', 'Supplies', 'One row per supply for a DIY project: quantity per guest, table or once, unit cost and status; the quantity from your headcount and table count, the cost and what is still to buy fill in.', [
    C('supply_id', 'Supply ID', 'text', 9, required=True), REF('diy_id', 'DIY ID', 'diy.diy_id', 9), LST('project', 'Project', 'project', 30), C('item', 'Item', 'text', 28), LST('basis', 'Basis', 'basis', 11),
    C('qty_per', 'Quantity per', 'num', 9), C('unit_cost', 'Unit cost', 'money', 9), LST('status', 'Status', 'sstatus', 11), C('bought_on', 'Bought on', 'date', 11),
    CA('units', 'Units', 'int', 'IF({col:basis}=%s,{set:headcount},IF({col:basis}=%s,{set:table_count},1))' % (PG, PT), 8),
    CA('qty', 'Quantity', 'int', 'ROUNDUP({col:qty_per}*{col:units},0)', 9),
    CA('cost', 'Cost', 'money', 'ROUND({col:qty}*{col:unit_cost},2)', 10),
    CA('to_buy', 'Still to buy', 'int', 'IF({col:status}=%s,0,1)' % BOUGHT, 8),
    CA('cost_to_buy', 'Cost still to buy', 'money', 'IF({col:to_buy}=1,{col:cost},0)', 10),
    CA('buy_rank', 'Shopping order', 'int', 'IF({col:to_buy}=1,COUNTIFS({range:supplies.to_buy},1,{range:supplies.supply_id},"<"&{col:supply_id})+1,"")', 8)],
    D.supplies_d(), 150, [A('status', '= ' + TOBUY, 'warn'), A('status', '= ' + BOUGHT, 'good')]))

# 3 Shopping list -----------------------------------------------------------------------------------------------------------
tables.append(T('shopping', 'Shopping list', 'DIY Shopping List', 'Every supply not yet bought, in the order of the Supplies sheet: item, project, quantity from your headcount and tables, cost and status. Nothing to type except the row number.', [
    C('rank', 'Row', 'int', 6, required=True), CA('at', 'Row in Supplies', 'int', 'IFERROR(MATCH({col:rank},{range:supplies.buy_rank},0),"")', 9),
    CA('supply_id', 'Supply ID', 'text', AT('supplies', 'supply_id'), 9), CA('item', 'Item', 'text', AT('supplies', 'item'), 28), CA('project', 'Project', 'text', AT('supplies', 'project'), 30),
    CA('qty', 'Quantity', 'int', AT('supplies', 'qty'), 9), CA('cost', 'Cost', 'money', AT('supplies', 'cost'), 10), CA('status', 'Status', 'text', AT('supplies', 'status'), 11),
    CA('count_left', 'Items still to buy', 'int', 'COUNTIFS({range:supplies.to_buy},1)', 9), CA('cost_left', 'Cost still to buy', 'money', 'SUM({range:supplies.cost_to_buy})', 11), CPL(), FRIEND()],
    D.shopping_d(), 80, [A('status', '= ' + TOBUY, 'warn')]))

# 4 Attire shopping ---------------------------------------------------------------------------------------------------------
tables.append(T('attire', 'Attire shopping', 'Attire Shopping', 'One row per item to buy for the day (outfits, shoes, accessories, rings): cost, status, order-by date and whether it is in the budget; the action and days left fill in.', [
    C('attire_id', 'Attire ID', 'text', 9, required=True), C('item', 'Item', 'text', 34), C('for_person', 'For', 'text', 14), LST('kind', 'Kind', 'akind', 13), C('vendor_id', 'Vendor ID', 'text', 9), C('vendor', 'Vendor', 'text', 16),
    C('phone', 'Vendor phone', 'text', 18), C('cost', 'Cost', 'money', 11), LST('status', 'Status', 'sstatus', 11), C('order_by', 'Order by', 'date', 11), C('in_budget', 'In budget', 'bool', 9),
    CA('days_to_order', 'Days to order by', 'int', 'IF({col:status}=%s,{col:order_by}-{today},"")' % TOBUY, 9),
    CA('action', 'Action', 'text', 'IF({col:status}=%s,IF({col:days_to_order}<0,%s,IF({col:days_to_order}<={set:order_window_days},%s,%s)),%s)' % (TOBUY, c('Order now'), c('Order soon'), c('On time'), c('Done')), 11),
    CA('order_rank', 'Order sequence', 'int', 'IF({col:status}=%s,COUNTIFS({range:attire.status},%s,{range:attire.order_by},"<"&{col:order_by})+COUNTIFS({range:attire.status},%s,{range:attire.order_by},{col:order_by},{range:attire.attire_id},"<"&{col:attire_id})+1,"")' % (TOBUY, TOBUY, TOBUY), 9),
    CPL()],
    D.attire_d(), 60, [A('action', '= ' + c('Order now'), 'bad'), A('action', '= ' + c('Order soon'), 'warn'), A('status', '= ' + TOBUY, 'warn')]))

# 5 Gifts -------------------------------------------------------------------------------------------------------------------
tables.append(T('gifts', 'Gifts', 'Gift Log', 'One row per gift (engagement party, shower or sent early): household, event, kind, what it is and the cash amount; the thank-you state, days waiting and the fee fill in.', [
    C('gift_id', 'Gift ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), C('household_id', 'Household ID', 'text', 10), C('household', 'Household', 'text', 26),
    LST('event', 'Event', 'gevent', 16), LST('kind', 'Kind', 'gkind', 16), C('description', 'Description', 'text', 24), C('amount', 'Cash amount', 'money', 11), C('via_provider', 'Through your payment provider', 'bool', 11),
    LST('cash_use', 'Cash gift goes to', 'cuse', 16), C('contact', 'Contact', 'text', 22), C('phone', 'Phone', 'text', 18),
    CA('note_n', 'Notes written', 'int', 'COUNTIFS({range:thanks.gift_id},{col:gift_id})', 8),
    CA('thanked', 'Thanked', 'int', 'IF({col:note_n}>0,1,0)', 8),
    CA('written_on', 'Note written on', 'date', LKD('thanks.written_on', 'thanks.gift_id', 'gift_id'), 11),
    CA('sent_on', 'Note sent on', 'date', LKD('thanks.sent_on', 'thanks.gift_id', 'gift_id'), 11),
    CA('days_waiting', 'Days waiting for a note', 'int', 'IF({col:thanked}=1,"",MAX(0,{today}-{col:date}))', 10),
    CA('late', 'Past the alert', 'int', 'IF({col:thanked}=1,0,IF({col:days_waiting}>{set:thankyou_alert_days},1,0))', 8),
    CA('status', 'Thank-you state', 'text', 'IF({col:thanked}=1,IF({col:sent_on}="",%s,%s),IF({col:late}=1,%s,%s))' % (c('Not sent yet'), c('Sent'), c('Write now'), c('On time')), 13),
    CA('days_left_target', 'Days left to your target', 'int', 'IF({col:thanked}=1,"",{set:thankyou_target_days}-{col:days_waiting})', 10),
    CA('days_to_note', 'Days to write the note', 'int', 'IF({col:thanked}=1,{col:written_on}-{col:date},"")', 9),
    CA('wait_rank', 'Backlog order', 'int', 'IF({col:thanked}=0,COUNTIFS({range:gifts.thanked},0,{range:gifts.days_waiting},">"&{col:days_waiting})+COUNTIFS({range:gifts.thanked},0,{range:gifts.days_waiting},{col:days_waiting},{range:gifts.gift_id},"<"&{col:gift_id})+1,"")', 8),
    CA('cash_rank', 'Cash gift order', 'int', 'IF({col:amount}>0,COUNTIFS({range:gifts.amount},">0",{range:gifts.date},"<"&{col:date})+COUNTIFS({range:gifts.amount},">0",{range:gifts.date},{col:date},{range:gifts.gift_id},"<"&{col:gift_id})+1,"")', 8),
    CA('fee', 'Fee on this gift', 'money', 'IF(AND({col:amount}>0,{col:via_provider}=%s),ROUND({col:amount}*{set:provider_fee_pct}+{set:provider_fee_flat},2),0)' % YES, 9),
    CA('kept', 'You keep', 'money', 'IF({col:amount}>0,{col:amount}-{col:fee},"")', 9), CPL()],
    D.gifts_d(), 400, [A('status', '= ' + c('Write now'), 'bad'), A('status', '= ' + c('Not sent yet'), 'warn'), A('status', '= ' + c('Sent'), 'good')]))

# 6 Thank-you notes ---------------------------------------------------------------------------------------------------------
tables.append(T('thanks', 'Thank-you notes', 'Thank-you Notes', 'One row per note written: the gift, the household, when it was written and sent and how; days to write, days to send and whether it has gone fill in.', [
    C('note_id', 'Note ID', 'text', 9, required=True), REF('gift_id', 'Gift ID', 'gifts.gift_id', 9), C('household', 'Household', 'text', 26), C('written_on', 'Written on', 'date', 11), C('sent_on', 'Sent on', 'date', 11),
    C('month', 'Written month', 'date', 11), LST('channel', 'Channel', 'tchannel', 16),
    CA('gift_date', 'Gift date', 'date', LKD('gifts.date', 'gifts.gift_id', 'gift_id'), 11),
    CA('days_to_write', 'Days to write', 'int', 'IF({col:gift_date}="","",{col:written_on}-{col:gift_date})', 8),
    CA('days_to_send', 'Days to send', 'int', 'IF({col:sent_on}>0,{col:sent_on}-{col:written_on},"")', 8),
    CA('is_sent', 'Sent', 'int', 'IF({col:sent_on}>0,1,0)', 6),
    CA('state', 'State', 'text', 'IF({col:is_sent}=1,%s,%s)' % (c('Sent'), c('Not sent yet')), 12)],
    D.thanks_d(), 400, [A('state', '= ' + c('Not sent yet'), 'warn'), A('state', '= ' + c('Sent'), 'good')]))

# 7 Thank-you backlog -------------------------------------------------------------------------------------------------------
tables.append(T('backlog', 'Thank-you backlog', 'Thank-you Backlog', 'The gifts that still have no note, oldest first: household, event, what it is, days waiting and Write now or On time against your alert days. Nothing to type except the row number.', [
    C('rank', 'Row', 'int', 6, required=True), CA('at', 'Row in Gifts', 'int', 'IFERROR(MATCH({col:rank},{range:gifts.wait_rank},0),"")', 8),
    CA('gift_id', 'Gift ID', 'text', AT('gifts', 'gift_id'), 9), CA('household', 'Household', 'text', AT('gifts', 'household'), 26), CA('contact', 'Contact', 'text', AT('gifts', 'contact'), 22),
    CA('event', 'Event', 'text', AT('gifts', 'event'), 16), CA('description', 'Description', 'text', AT('gifts', 'description'), 24), CA('date', 'Gift date', 'date', AT('gifts', 'date'), 11),
    CA('days_waiting', 'Days waiting', 'int', AT('gifts', 'days_waiting'), 9), CA('verdict', 'Verdict', 'text', 'IF({col:at}="","",IF(INDEX({range:gifts.late},{col:at})=1,%s,%s))' % (c('Write now'), c('On time')), 11),
    CA('phone', 'Phone', 'text', AT('gifts', 'phone'), 18),
    CA('waiting_n', 'Gifts without a note', 'int', 'COUNTIFS({range:gifts.thanked},0)', 9), CA('over_n', 'Past the alert', 'int', 'COUNTIFS({range:gifts.late},1)', 9),
    CA('oldest_days', 'Oldest wait, days', 'int', 'MAX({range:gifts.days_waiting})', 9), CA('alert_days', 'Alert days', 'int', '{set:thankyou_alert_days}', 8),
    CA('written', 'Notes written', 'int', 'COUNTIFS({range:thanks.note_id},"<>")', 8), CA('total', 'Gifts received', 'int', 'COUNTIFS({range:gifts.gift_id},"<>")', 8),
    CA('target_on', 'Target date for the oldest', 'date', '{today}-{col:oldest_days}+{set:thankyou_target_days}', 11),
    CA('weeks_left', 'Weeks to the target', 'int', 'MAX(1,ROUNDUP(({col:target_on}-{today})/7,0))', 8),
    CA('rate', 'Notes a week to finish', 'int', 'ROUNDUP({col:waiting_n}/{col:weeks_left},0)', 9), CPL(), FRIEND(), PARTNER()],
    D.backlog_d(), 60, [A('verdict', '= ' + c('Write now'), 'bad'), A('verdict', '= ' + c('On time'), 'good')]))

# 8 Gifts by event ----------------------------------------------------------------------------------------------------------
def _ev(k): return tok('gevent', k)
GE_N = 'CHOOSE(MATCH({col:row},{range:gift_events.row},0),%s)'
tables.append(T('gift_events', 'Gifts by event', 'Gifts by Event', 'Gifts and thank-you notes by event, for the cash gifts and for all gifts: how many gifts came in and how many already have a note. Nothing to type.', [
    C('row', 'Group', 'text', 22, required=True),
    CA('gifts', 'Gifts', 'int', GE_N % ','.join(['COUNTIFS({range:gifts.event},%s)' % _ev(k) for k in ('Engagement party', 'Shower', 'Sent early')] + ['COUNTIFS({range:gifts.kind},%s)' % CASHK, 'COUNTIFS({range:gifts.gift_id},"<>")']), 9),
    CA('thanked', 'With a note', 'int', GE_N % ','.join(['COUNTIFS({range:gifts.event},%s,{range:gifts.thanked},1)' % _ev(k) for k in ('Engagement party', 'Shower', 'Sent early')] + ['COUNTIFS({range:gifts.kind},%s,{range:gifts.thanked},1)' % CASHK, 'COUNTIFS({range:gifts.thanked},1)']), 9)],
    D.gift_events_d(), 50))

# 9 Cash gifts --------------------------------------------------------------------------------------------------------------
tables.append(T('cash', 'Cash gifts', 'Cash Gifts', 'Every cash gift in date order with where it goes (budget, honeymoon or not decided), the fee taken and what you keep; only gifts received count. Type only the row number.', [
    C('rank', 'Row', 'int', 6, required=True), CA('at', 'Row in Gifts', 'int', 'IFERROR(MATCH({col:rank},{range:gifts.cash_rank},0),"")', 8),
    CA('gift_id', 'Gift ID', 'text', AT('gifts', 'gift_id'), 9), CA('household', 'Household', 'text', AT('gifts', 'household'), 26), CA('contact', 'Contact', 'text', AT('gifts', 'contact'), 22), CA('phone', 'Phone', 'text', AT('gifts', 'phone'), 18), CA('date', 'Date', 'date', AT('gifts', 'date'), 11),
    CA('amount', 'Cash amount', 'money', AT('gifts', 'amount'), 11), CA('use', 'Goes to', 'text', AT('gifts', 'cash_use'), 16), CA('fee', 'Fee', 'money', AT('gifts', 'fee'), 9),
    CA('kept', 'You keep', 'money', AT('gifts', 'kept'), 10), CA('status', 'Thank-you state', 'text', AT('gifts', 'status'), 13),
    CA('total_received', 'Cash gifts received', 'money', 'SUM({range:gifts.amount})', 12), CA('expected', 'Expected, not confirmed', 'money', 'SUMIFS({range:funding.amount},{range:funding.source},%s,{range:funding.status},%s)+SUMIFS({range:honeyfund.amount},{range:honeyfund.source},%s,{range:honeyfund.status},%s)' % (CASHS, NOTC, HCASH, NOTC), 12),
    CPL(), PARTNER()],
    D.cash_d(), 200, [A('status', '= ' + c('Write now'), 'bad')]))

# 10 Funding link -----------------------------------------------------------------------------------------------------------
FL = '{col:agreed}-SUMIFS({range:funding.amount},%s{range:funding.status},%s)-SUMIFS({range:funding.amount},%s{range:funding.status},%s)'
tables.append(T('fundlink', 'Funding link', 'Funding Link', 'What each source agreed to give and what is still missing after the money received and promised; cash gifts that are not confirmed are never counted. The last row is the whole wedding.', [
    C('source', 'Source', 'text', 22, required=True), C('agreed', 'Agreed amount', 'money', 13),
    CA('gap', 'Still missing, negative is ahead', 'money', 'IF(COUNTIFS({range:funding.source},{col:source})=0,%s,%s)' % (FL % ('', REC, '', PROM), FL % ('{range:funding.source},{col:source},', REC, '{range:funding.source},{col:source},', PROM)), 13)],
    D.fundlink_d(), 50, [A('gap', '> 0', 'warn')]))

# 11 Funding ----------------------------------------------------------------------------------------------------------------
tables.append(T('funding', 'Funding', 'Funding', 'One row per amount coming in for the wedding (savings, family transfers, cash gifts): date, amount and status Received, Promised or Not confirmed.', [
    C('fund_id', 'Fund ID', 'text', 9, required=True), LST('source', 'Source', 'source', 18), C('date', 'Date', 'date', 11), C('amount', 'Amount', 'money', 11), LST('status', 'Status', 'fstatus', 14)],
    D.funding_d(), 150, [A('status', '= ' + NOTC, 'warn'), A('status', '= ' + REC, 'good')]))

# 12 Honeymoon fund ---------------------------------------------------------------------------------------------------------
tables.append(T('honeyfund', 'Honeymoon fund', 'Honeymoon Fund', 'One row per amount set aside for the honeymoon (monthly savings, cash gifts): date, month, amount and status; funds so far, promised and the gap to your honeymoon budget fill in.', [
    C('hf_id', 'Fund ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), LST('source', 'Source', 'hsource', 14), C('amount', 'Amount', 'int', 11), LST('status', 'Status', 'fstatus', 14),
    CA('funds', 'Funds so far', 'money', 'SUMIFS({range:honeyfund.amount},{range:honeyfund.status},%s)+SUMIFS({range:gifts.amount},{range:gifts.cash_use},%s)' % (REC, HONEY), 12),
    CA('promised', 'Promised savings', 'money', 'SUMIFS({range:honeyfund.amount},{range:honeyfund.status},%s)' % PROM, 12),
    CA('gap', 'Gap to the honeymoon budget', 'money', '{set:honeymoon_goal}-{col:funds}-{col:promised}', 12), CPL(), PARTNER()],
    D.honeyfund_d(), 60, [A('status', '= ' + NOTC, 'warn')]))

# 13 Budget -----------------------------------------------------------------------------------------------------------------
tables.append(T('budget', 'Budget', 'Budget', 'One row per budget category: planned, committed (signed contracts) and paid. The full budget lives in the budget workbook; this copy feeds the final budget.', [
    C('line_id', 'Line ID', 'text', 9, required=True), LST('category', 'Category', 'category', 24), C('planned', 'Planned', 'money', 12), C('committed', 'Committed', 'money', 12), C('paid', 'Paid', 'money', 12)],
    D.budget_d(), 50))

# 14 Final budget against actual --------------------------------------------------------------------------------------------
def BL(c_): return LKN('budget.%s' % c_, 'budget.category', 'category')
tables.append(T('final', 'Final budget', 'Final Budget against Actual', 'One row per category: planned, committed (the final cost so far), paid and still due, the variance and Over, Watch or On track against your own limit; the total cost and cost per guest fill in.', [
    LST('category', 'Category', 'category', 24, required=True),
    CA('planned', 'Planned', 'money', BL('planned'), 12), CA('committed', 'Committed', 'money', BL('committed'), 12), CA('paid', 'Paid', 'money', BL('paid'), 12),
    CA('still_due', 'Still due', 'money', '{col:committed}-{col:paid}', 12), CA('variance', 'Over or under plan', 'money', '{col:committed}-{col:planned}', 12),
    CA('share', 'Share of final cost', 'pct', 'IFERROR({col:committed}/SUM({range:final.committed}),0)', 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:variance}<=0,%s,IF({col:variance}<={col:planned}*{set:watch_pct},%s,%s))' % (c('On track'), c('Watch'), c('Over')), 11),
    CA('total_cost', 'Final cost so far', 'money', 'SUM({range:final.committed})', 12), CA('per_guest', 'Cost per guest', 'money', 'ROUND(SUM({range:final.committed})/{set:headcount},0)', 10), CPL(), PARTNER()],
    D.final_d(), 50, [A('verdict', '= ' + c('Over'), 'bad'), A('verdict', '= ' + c('Watch'), 'warn'), A('verdict', '= ' + c('On track'), 'good')]))

# 15 Cost per guest actual --------------------------------------------------------------------------------------------------
PGN = 'CHOOSE(MATCH({col:item},{range:perguest.item},0),SUM({range:budget.planned}),SUM({range:budget.committed}),SUM({range:budget.paid}),SUM({range:budget.committed})-SUM({range:budget.paid}),SUM({range:budget.planned})-SUM({range:budget.committed}))'
tables.append(T('perguest', 'Cost per guest', 'Cost per Guest Actual', 'The plan, the final cost so far, what you paid and what is still due, each over the final headcount in your settings. Nothing to type.', [
    C('item', 'Item', 'text', 30, required=True), CA('amount', 'Amount', 'money', PGN, 12), CA('per_guest', 'Per guest', 'money', 'ROUND({col:amount}/{set:headcount},0)', 11)],
    D.perguest_d(), 50))

# 16 Vendor balances --------------------------------------------------------------------------------------------------------
tables.append(T('balances', 'Vendor balances', 'Vendor Balances', 'One row per booked vendor: contract total, paid, the next payment date and the final payment date; still due, days to the next payment and Paid, Due soon, Upcoming or Overdue fill in.', [
    C('vendor_id', 'Vendor ID', 'text', 9, required=True), C('vendor', 'Vendor', 'text', 22), C('phone', 'Phone', 'text', 18), C('contract_total', 'Contract total', 'money', 13), C('paid', 'Paid', 'money', 12),
    C('next_due', 'Next payment', 'date', 12), C('final_due', 'Final payment', 'date', 12),
    CA('still_due', 'Still due', 'money', '{col:contract_total}-{col:paid}', 12),
    CA('days_to_next', 'Days to next payment', 'int', 'IF({col:still_due}<=0,"",{col:next_due}-{today})', 9),
    CA('state', 'State', 'text', 'IF({col:still_due}<=0,%s,IF({col:next_due}<{today},%s,IF({col:next_due}-{today}<={set:soon_days},%s,%s)))' % (c('Paid'), c('Overdue'), c('Due soon'), c('Upcoming')), 11),
    CA('next_key', 'Next unpaid date', 'date', 'IF({col:still_due}>0,{col:next_due},"")', 11),
    CA('balances_n', 'Balances still due', 'int', 'COUNTIFS({range:balances.still_due},">0")', 9), CA('balances_total', 'Total still due', 'money', 'SUM({range:balances.still_due})', 12),
    CPL(), PARTNER()],
    D.balances_d(), 50, [A('state', '= ' + c('Overdue'), 'bad'), A('state', '= ' + c('Due soon'), 'warn'), A('state', '= ' + c('Paid'), 'good')]))

# 17 Returns ----------------------------------------------------------------------------------------------------------------
tables.append(T('returns', 'Returns', 'Returns and Refunds', 'One row per rental to return, deposit to claim or borrowed item to give back: vendor, due date, refund and status Not due, Arranged or Done; days left and Overdue or Due soon fill in.', [
    C('return_id', 'Return ID', 'text', 9, required=True), C('item', 'Item', 'text', 34), C('vendor_id', 'Vendor ID', 'text', 9), C('vendor', 'Vendor', 'text', 18), C('phone', 'Vendor phone', 'text', 18),
    LST('kind', 'Kind', 'rkind', 15), C('due_date', 'Due date', 'date', 11), C('refund', 'Refund', 'money', 10), LST('status', 'Status', 'rstatus', 11),
    CA('days_to_due', 'Days to due date', 'int', '{col:due_date}-{today}', 9), CA('is_done', 'Done', 'int', 'IF({col:status}=%s,1,0)' % R_DONE, 6),
    CA('arranged', 'Arranged or done', 'int', 'IF({col:status}=%s,0,1)' % R_NOT, 8),
    CA('flag', 'Flag', 'text', 'IF({col:is_done}=1,%s,IF({col:days_to_due}<0,%s,IF({col:days_to_due}<={set:soon_days},%s,%s)))' % (c('Done'), c('Overdue'), c('Due soon'), c('Upcoming')), 11),
    CA('open_key', 'Open due date', 'date', 'IF({col:is_done}=1,"",{col:due_date})', 11),
    CA('open_n', 'Items open', 'int', 'COUNTIFS({range:returns.return_id},"<>")-COUNTIFS({range:returns.status},%s)' % R_DONE, 8),
    CA('open_refund', 'Refunds expected', 'money', 'SUMIFS({range:returns.refund},{range:returns.status},"<>"&%s)' % R_DONE, 11),
    CA('first_due', 'First open due date', 'date', 'SMALL({range:returns.open_key},1)', 11), CPL(), PARTNER(), LIT('lead_phone', 'Wedding party lead phone', D.LEAD_PHONE)],
    D.returns_d(), 60, [A('flag', '= ' + c('Overdue'), 'bad'), A('flag', '= ' + c('Due soon'), 'warn'), A('flag', '= ' + c('Done'), 'good')]))

# 18 Paperwork --------------------------------------------------------------------------------------------------------------
tables.append(T('paperwork', 'Paperwork', 'Paperwork and Name Change', 'One row per paperwork or name change step in generic words: kind, optional or not, due date, status and owner. Check with your officiant or local office; edit, hide or delete any row.', [
    C('item_id', 'Step ID', 'text', 9, required=True), C('item', 'Step', 'text', 44), LST('kind', 'Kind', 'pkind', 18), C('optional', 'Optional', 'bool', 9), C('due_date', 'Due date', 'date', 11),
    LST('status', 'Status', 'pstatus', 12), LST('owner', 'Owner', 'owner', 18),
    CA('days_to_due', 'Days to due date', 'int', '{col:due_date}-{today}', 9), CA('is_done', 'Done', 'int', 'IF({col:status}=%s,1,0)' % P_DONE, 6),
    CA('flag', 'Flag', 'text', 'IF({col:is_done}=1,%s,IF({col:days_to_due}<0,%s,%s))' % (c('Done'), c('Overdue'), c('Open')), 10),
    CA('next_key', 'Open due date', 'date', 'IF({col:is_done}=1,"",{col:due_date})', 11),
    CA('steps_left', 'Wrap-up steps left', 'int', 'COUNTIFS({range:wrapup.status},%s)' % c('To finish'), 8), CPL(), PARTNER()],
    D.paperwork_d(), 60, [A('flag', '= ' + c('Overdue'), 'bad'), A('flag', '= ' + c('Done'), 'good')]))

# 19 Household gift ledger --------------------------------------------------------------------------------------------------
tables.append(T('ledger', 'Household gift ledger', 'Household Gift Ledger', 'One row per household that gave: gifts, cash given, last gift date and the share already thanked; pick the household ID and the rest fills in.', [
    REF('household_id', 'Household ID', 'gifts.household_id', 10, required=True),
    CA('household', 'Household', 'text', LKT('gifts.household', 'gifts.household_id', 'household_id'), 26), CA('contact', 'Contact', 'text', LKT('gifts.contact', 'gifts.household_id', 'household_id'), 22),
    CA('gifts', 'Gifts', 'int', 'COUNTIFS({range:gifts.household_id},{col:household_id})', 7), CA('cash', 'Cash given', 'money', 'SUMIFS({range:gifts.amount},{range:gifts.household_id},{col:household_id})', 11),
    CA('last_gift', 'Last gift', 'date', 'SUMPRODUCT(MAX(({range:gifts.household_id}={col:household_id})*{range:gifts.date}))', 11),
    CA('thanked_share', 'Thanked share', 'pct', 'IFERROR(COUNTIFS({range:gifts.household_id},{col:household_id},{range:gifts.thanked},1)/{col:gifts},0)', 9),
    CA('waiting', 'Gifts without a note', 'int', 'COUNTIFS({range:gifts.household_id},{col:household_id},{range:gifts.thanked},0)', 9),
    CA('phone', 'Phone', 'text', LKT('gifts.phone', 'gifts.household_id', 'household_id'), 18), CPL()],
    D.ledger_d(), 400, [A('waiting', '> 0', 'warn')]))

# 20 Wrap-up checks ---------------------------------------------------------------------------------------------------------
RK = lambda k: tok('rkind', k)
WN = ','.join([
    'COUNTIFS({range:balances.still_due},">0")',
    'COUNTIFS({range:returns.kind},%s,{range:returns.status},"<>"&%s)+COUNTIFS({range:returns.kind},%s,{range:returns.status},"<>"&%s)' % (RK('Rental return'), R_DONE, RK('Supplies'), R_DONE),
    'COUNTIFS({range:returns.kind},%s,{range:returns.status},"<>"&%s)' % (RK('Deposit refund'), R_DONE),
    'COUNTIFS({range:gifts.thanked},0)',
    'COUNTIFS({range:thanks.note_id},"<>")-COUNTIFS({range:thanks.sent_on},">0")',
    'COUNTIFS({range:gifts.cash_use},%s)' % tok('cuse', 'Not decided'),
    'COUNTIFS({range:paperwork.optional},%s,{range:paperwork.status},"<>"&%s)' % (NO, P_DONE),
    'COUNTIFS({range:paperwork.optional},%s,{range:paperwork.status},"<>"&%s)' % (YES, P_DONE),
    'COUNTIFS({range:diy.diy_id},"<>")-COUNTIFS({range:diy.status},%s)' % DONE_D,
    'COUNTIFS({range:final.variance},">0")'])
tables.append(T('wrapup', 'Wrap-up checks', 'Wrap-up Checks', 'Ten checks that decide when the wedding is closed: each counts what is still open and says Done or To finish. Nothing to type.', [
    C('check', 'Check', 'text', 40, required=True), CA('count', 'Still open', 'int', 'CHOOSE(MATCH({col:check},{range:wrapup.check},0),%s)' % WN, 9),
    CA('status', 'Status', 'text', 'IF({col:count}=0,%s,%s)' % (c('Done'), c('To finish')), 11)],
    D.wrapup_d(), 50, [A('status', '= ' + c('To finish'), 'warn'), A('status', '= ' + c('Done'), 'good')]))
assert len(tables) == 20
