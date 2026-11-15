"""Author and self-publisher suite part 7: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au7_lists import *
import au7_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
M12 = '{range:dmonth.month},">"&EDATE(%s,-12)' % MS
S_OFFER, S_SIGNED, S_DELIV, S_PAID, S_EXP = (tok('dstatus', m) for m in ('Offer', 'Signed', 'Delivered', 'Paid in full', 'Expired'))
FLOOR = '{set:event_hour_floor}'
tools = []

# 1 ------------------------------------------------------------ direct store margin
TAX = '(({in:price}-{in:discount}+{in:shipping})*{in:tax_pct})'
PAYS = '({in:price}-{in:discount}+{in:shipping}+%s)' % TAX
FEE = '(%s*{in:fee_pct}+{in:fee_fixed})' % PAYS
NET = '({in:price}-{in:discount}+{in:shipping}-%s-{in:delivery})' % FEE
tools.append(TOOL('direct_margin', 'Direct Store Margin', 'Does the direct store pay more than a store for this item',
    'Type the price, discount, shipping, payment fee, delivery cost and sales tax rate of one item and what a store pays you; see the net per item, the difference and a verdict. Sales tax is not income.', [
    I('price', 'Price of the item', 14.99), I('discount', 'Discount given', 0), I('shipping', 'Shipping charged', 4.0), I('fee_pct', 'Payment fee, percent of the charge', 0.029, 'pct'), I('fee_fixed', 'Payment fee, fixed part', 0.3),
    I('delivery', 'Delivery cost (print, postage)', 8.85), I('tax_pct', 'Sales tax rate collected (confirm with your adviser)', 0.1, 'pct'), I('store_net', 'What a store pays you for the same item', 3.34)], [
    O('Sales tax collected (not income)', 'money', TAX), O('Customer pays', 'money', PAYS), O('Payment fee', 'money', FEE), O('Direct net per item', 'money', NET),
    O('Same item through a store', 'money', '{in:store_net}'), O('Direct minus store', 'money', '%s-{in:store_net}' % NET), O('Direct net as a share of the price', 'pct', 'IF({in:price}>0,%s/{in:price},0)' % NET),
    O('Lowest net you accept', 'money', '{set:min_net_copy}'),
    O('Verdict', 'text', 'IF(%s<{set:min_net_copy},%s,IF(%s>={in:store_net},%s,%s))' % (NET, v1('Price too low'), NET, v1('Direct pays more'), v1('Store pays more')))],
    GR('What if', ('Discount of 3', {'discount': 3}), ('No shipping charged', {'shipping': 0}), ('Price 11.99', {'price': 11.99}), ('Delivery cost 11', {'delivery': 11}), ('A store pays 6', {'store_net': 6}), ('Ebook at 4.99', {'price': 4.99, 'shipping': 0, 'delivery': 0.12, 'store_net': 3.37}))))

# 2 ------------------------------------------------------------ direct price and discount solver
LOW = '(({in:target_net}+{in:fee_fixed}+{in:delivery})/(1-{in:fee_pct})-{in:shipping})'
def NETP(step): return '(({in:price}+(%s)*{in:step}+{in:shipping})*(1-{in:fee_pct})-{in:fee_fixed}-{in:delivery})' % step
tools.append(TOOL('direct_solver', 'Direct Price Solver', 'What is the lowest direct price that holds your net per copy',
    'Type the net per copy you want, the delivery cost and the fee; the lowest price, the largest discount and the net at five price steps come out of a closed formula, with a verdict.', [
    I('target_net', 'Net per copy you want (your own number)', 5.0), I('delivery', 'Delivery cost (print, postage)', 8.85), I('shipping', 'Shipping charged', 4.0), I('fee_pct', 'Payment fee, percent of the charge', 0.029, 'pct'),
    I('fee_fixed', 'Payment fee, fixed part', 0.3), I('price', 'Your direct price now', 14.99), I('step', 'Price step for the row below', 1.0)], [
    O('Lowest price that holds your net', 'money', LOW), O('Net per copy at your price', 'money', NETP('0')), O('Largest discount in money', 'money', 'MAX(0,{in:price}-%s)' % LOW),
    O('Largest discount as a share of the price', 'pct', 'IF({in:price}>0,MAX(0,{in:price}-%s)/{in:price},0)' % LOW),
    O('Net at 2 steps lower', 'money', NETP('-2')), O('Net at 1 step lower', 'money', NETP('-1')), O('Net at 1 step higher', 'money', NETP('1')), O('Net at 2 steps higher', 'money', NETP('2')),
    O('Verdict', 'text', 'IF({in:price}>=%s,%s,%s)' % (LOW, v1('Price holds'), v1('Raise the price')))],
    GR('What if', ('Net wanted 8', {'target_net': 8}), ('Net wanted 3', {'target_net': 3}), ('Price 10.99', {'price': 10.99}), ('Delivery 11', {'delivery': 11}), ('No shipping charged', {'shipping': 0}))))

# 3 ------------------------------------------------------------ direct share goal tracker
D12 = 'SUMIFS({range:dmonth.net},%s)' % M12
R12 = 'SUMIFS({range:dmonth.all_revenue},%s)' % M12
C12 = 'SUMIFS({range:dmonth.copies},%s)' % M12
NEEDED = '({in:target}*(%s-%s)/(1-{in:target}))' % (R12, D12)
GAIN = '(IF(%s>0,%s/%s,0)-{in:store_royalty})' % (C12, D12, C12)
MONTHS = 'IF(%s/%s>={in:target},0,NPER({in:growth},0,-%s,%s))' % (D12, R12, D12, NEEDED)
tools.append(TOOL('share_goal', 'Direct Share Tracker', 'Is the direct share of income on track for your goal',
    'Direct net of the last 12 months against all revenue and your goal; type your growth and what a store pays per copy to see the copies to move and the months the goal takes.', [
    I('target', 'Direct share you want (your own number)', 0.15, 'pct'), I('growth', 'Growth of direct net per month (your own number)', 0.02, 'pct'), I('store_royalty', 'Average royalty a store pays per copy', 3.0),
    I('months_ok', 'Months you give yourself to reach the goal', 12, 'int')], [
    O('Direct net, last 12 months', 'money', D12), O('All revenue, last 12 months', 'money', R12), O('Direct share of income', 'pct', '%s/%s' % (D12, R12)), O('Gap to your goal', 'pct', '%s/%s-{in:target}' % (D12, R12)),
    O('Direct net needed for the goal', 'money', '%s+%s' % (D12, 'MAX(0,%s-%s)' % (NEEDED, D12))), O('Extra direct net needed', 'money', 'MAX(0,%s-%s)' % (NEEDED, D12)),
    O('Direct net per copy, last 12 months', 'money', 'IF(%s>0,%s/%s,0)' % (C12, D12, C12)), O('Gain per copy moved from a store', 'money', GAIN),
    O('Copies to move from stores in a year', 'int', 'IF(%s>0,ROUNDUP(MAX(0,%s-%s)/%s,0),0)' % (GAIN, NEEDED, D12, GAIN)), O('Months to reach the goal at your growth', 'num', MONTHS),
    O('Verdict', 'text', 'IF(%s<={in:months_ok},%s,%s)' % (MONTHS, v1('On track'), v1('Behind')))],
    GR('What if', ('Growth 5% a month', {'growth': 0.05}), ('Growth 8% a month', {'growth': 0.08}), ('Goal 10%', {'target': 0.10}), ('A store pays 2', {'store_royalty': 2}), ('Give yourself 36 months', {'months_ok': 36}))))

# 4 ------------------------------------------------------------ direct against store switch
MOVED = '({in:store_copies}*{in:share_moved})'
EXTRA = '(%s*({in:direct_net}-{in:store_royalty}))' % MOVED
tools.append(TOOL('switch', 'Direct against Store Switch', 'Is it worth moving copies from a store to your direct store',
    'Type the copies a store sells a month, the share you can move to your direct store, what each channel pays per copy and the set-up cost; see the extra net, the payback and the share after the move.', [
    I('store_copies', 'Copies a store sells a month (the editions you would move)', 600, 'int'), I('share_moved', 'Share you can move (your own number)', 0.15, 'pct'), I('store_royalty', 'What a store pays per copy', 3.3),
    I('direct_net', 'What the direct store nets per copy', 5.1), I('setup', 'Set-up cost, once (web developer, pages)', 180), I('max_payback', 'Longest payback you accept, in months', 6, 'int')], [
    O('Copies moved a month', 'int', 'ROUND(%s,0)' % MOVED), O('Extra net a month', 'money', EXTRA), O('Extra net in 12 months', 'money', '%s*12' % EXTRA), O('Gain in 12 months after set-up', 'money', '%s*12-{in:setup}' % EXTRA),
    O('Payback in months', 'num', 'IF(%s>0,{in:setup}/%s,0)' % (EXTRA, EXTRA)),
    O('Direct share now', 'pct', '%s/%s' % (D12, R12)), O('Direct share after the move', 'pct', '(%s+%s*{in:direct_net}*12)/(%s+%s*12)' % (D12, MOVED, R12, EXTRA)),
    O('Verdict', 'text', 'IF(AND(%s>0,{in:setup}<=%s*{in:max_payback}),%s,%s)' % (EXTRA, EXTRA, v1('Worth moving'), v1('Keep in the store')))],
    GR('What if', ('Move 5%', {'share_moved': 0.05}), ('Move 30%', {'share_moved': 0.3}), ('Set-up 900', {'setup': 900}), ('Direct nets 3.5', {'direct_net': 3.5}), ('A store pays 5', {'store_royalty': 5}))))

# 5 ------------------------------------------------------------ print margin per copy
PCOST = '({in:fixed}+{in:pages}*{in:per_page})'
def PM(step): return '(({in:price}+(%s)*{in:step}-%s-{in:ship})/({in:price}+(%s)*{in:step}))' % (step, PCOST, step)
tools.append(TOOL('print_margin', 'Print Margin per Copy', 'Does the margin hold on a printed copy at this price',
    'Type the pages, the printer cost parts, your price and the share a store pays; see the print cost, the royalty a store pays, the margin on a copy you sell by hand and the margin at five price steps.', [
    I('pages', 'Pages', 340, 'int'), I('fixed', 'Print cost, fixed part per copy (ask your printer)', 1.0), I('per_page', 'Print cost per page (ask your printer)', 0.0125, 'num'), I('price', 'Price', 14.99), I('share', 'Share a store pays', 0.6, 'pct'),
    I('ship', 'Shipping per author copy', 0.8), I('step', 'Price step', 1.0), I('target', 'Margin you want', 0.55, 'pct')], [
    O('Print cost per copy', 'money', PCOST), O('Royalty a store pays per copy', 'money', '{in:price}*{in:share}-%s' % PCOST), O('Margin on a hand-sold copy', 'money', '{in:price}-%s-{in:ship}' % PCOST),
    O('Margin percent', 'pct', PM('0')), O('Margin percent, 2 steps lower', 'pct', PM('-2')), O('Margin percent, 1 step lower', 'pct', PM('-1')), O('Margin percent, 1 step higher', 'pct', PM('1')), O('Margin percent, 2 steps higher', 'pct', PM('2')),
    O('Lowest price that holds your margin', 'money', '(%s+{in:ship})/(1-{in:target})' % PCOST), O('Verdict', 'text', 'IF(%s>={in:target},%s,%s)' % (PM('0'), v1('Margin holds'), v1('Raise the price')))],
    GR('What if', ('400 pages', {'pages': 400}), ('600 pages', {'pages': 600}), ('Price 11.99', {'price': 11.99}), ('Price 17.99', {'price': 17.99}), ('Margin wanted 65%', {'target': 0.65}))))

# 6 ------------------------------------------------------------ author copy cost
OCOST = '({in:copies}*{in:print_cost}+{in:shipping})'
LAND = '(%s/{in:copies})' % OCOST
tools.append(TOOL('author_copy', 'Author Copy Cost', 'Should you order these author copies now',
    'Type the copies, the printer price, the shipping, your hand-sold price and the copies you expect to need; see the cost and margin per copy and per order, the copies left unsold and a verdict.', [
    I('copies', 'Copies to order', 50, 'int'), I('print_cost', 'Printer price per copy', 5.65), I('shipping', 'Shipping of the whole order', 40), I('price', 'Hand-sold price', 14.99),
    I('needed', 'Copies you expect to need in the next 3 months', 45, 'int'), I('sell_through', 'Share of the copies you usually sell (your own history)', 0.7, 'pct')], [
    O('Cost of the order', 'money', OCOST), O('Cost per copy with shipping', 'money', LAND), O('Margin per copy', 'money', '{in:price}-%s' % LAND), O('Margin percent', 'pct', 'IF({in:price}>0,({in:price}-%s)/{in:price},0)' % LAND),
    O('Margin if every copy sells', 'money', '{in:copies}*({in:price}-%s)' % LAND), O('Copies you expect to sell', 'int', 'ROUND({in:copies}*{in:sell_through},0)'),
    O('Copies left unsold', 'int', '{in:copies}-ROUND({in:copies}*{in:sell_through},0)'), O('Margin at your usual sell-through', 'money', 'ROUND({in:copies}*{in:sell_through},0)*{in:price}-%s' % OCOST),
    O('Most copies worth ordering', 'int', 'ROUNDDOWN({in:needed}*(1+{set:spare_share}),0)'),
    O('Verdict', 'text', 'IF(AND(({in:price}-%s)/{in:price}>={set:print_margin_target},{in:copies}<={in:needed}*(1+{set:spare_share})),%s,%s)' % (LAND, v1('Order now'), v1('Order fewer')))],
    GR('What if', ('Order 80 copies', {'copies': 80}), ('Order 30 copies', {'copies': 30}), ('Price 12.99', {'price': 12.99}), ('Shipping 90', {'shipping': 90}), ('Sell-through 50%', {'sell_through': 0.5}))))

# 7 ------------------------------------------------------------ minimum print price
def MINP(pages, bump='0'): return '(({in:fixed}+%d*{in:per_page})*(1+%s)+{in:ship})/(1-{in:target})' % (pages, bump)
MYMIN = '(({in:fixed}+{in:my_pages}*{in:per_page})+{in:ship})/(1-{in:target})'
bands = [200, 300, 400, 500, 600]
tools.append(TOOL('min_print_price', 'Minimum Print Price', 'What is the lowest price that holds your margin',
    'Type the margin you want and the printer cost parts; the lowest price comes out of a closed formula for five page counts and again with the print cost higher, with a verdict on your own book.', [
    I('target', 'Margin you want', 0.55, 'pct'), I('fixed', 'Print cost, fixed part per copy', 1.0), I('per_page', 'Print cost per page', 0.0125, 'num'), I('ship', 'Shipping per author copy', 0.8), I('bump', 'Rise in print cost to test', 0.1, 'pct'),
    I('my_pages', 'Pages of your book', 340, 'int'), I('my_price', 'Price of your book', 14.99)], [
    *[O('Minimum price, %d pages' % b, 'money', MINP(b)) for b in bands],
    *[O('Minimum price, %d pages, print cost higher' % b, 'money', MINP(b, '{in:bump}')) for b in bands],
    O('Minimum price for your book', 'money', MYMIN), O('Verdict', 'text', 'IF({in:my_price}>=%s,%s,%s)' % (MYMIN, v1('Price holds'), v1('Raise the price')))],
    GR('What if', ('Margin wanted 45%', {'target': 0.45}), ('Margin wanted 65%', {'target': 0.65}), ('Print cost 20% higher', {'bump': 0.2}), ('Your book at 500 pages', {'my_pages': 500}), ('Your price 17.99', {'my_price': 17.99}))))

# 8 ------------------------------------------------------------ stock count check
def SP(col): return 'INDEX({range:stockpos.%s},MATCH({in:edition},{range:stockpos.edition_id},0))' % col
def SPN(col): return 'IFERROR(%s,0)' % SP(col)
tools.append(TOOL('count_check', 'Stock Count Check', 'Does your count match the stock sheet',
    'Type the edition ID and the copies you counted on the shelf; the movements of that edition add up to the copies the sheet expects, and the difference and its value at cost give a verdict.', [
    I('edition', 'Edition ID', 'ED-0036', 'text'), I('counted', 'Copies you counted', 5, 'int'), I('tolerance', 'Copies of difference you accept', 0, 'int')], [
    O('Title', 'text', 'IFERROR(%s&"","")' % SP('title')), O('Format', 'text', 'IFERROR(%s&"","")' % SP('format')), O('Copies in (orders)', 'int', SPN('copies_in')), O('Sold at events', 'int', SPN('sold')),
    O('Given away', 'int', SPN('given')), O('Lost or damaged', 'int', SPN('lost')), O('Copies on hand by the sheet', 'int', SPN('on_hand')), O('Copies counted', 'int', '{in:counted}'),
    O('Difference (counted minus sheet)', 'int', '{in:counted}-%s' % SPN('on_hand')), O('Value of the difference at cost', 'money', '({in:counted}-%s)*%s' % (SPN('on_hand'), SPN('unit_cost'))),
    O('Value of the counted stock at cost', 'money', '{in:counted}*%s' % SPN('unit_cost')), O('Days since the last count', 'int', SPN('days_since_count')),
    O('Verdict', 'text', 'IF(ABS({in:counted}-%s)<={in:tolerance},%s,%s)' % (SPN('on_hand'), v2('Count matches'), v2('Recount')))],
    GR('What if', ('Counted 6', {'counted': 6}), ('Counted 4', {'counted': 4}), ('Counted 8', {'counted': 8}), ('Accept 1 copy of difference', {'tolerance': 1}), ('Counted 2, accept 3', {'counted': 2, 'tolerance': 3}))))

# 9 ------------------------------------------------------------ reorder point and reprint
NEED_LEAD = '({in:monthly}*{in:lead}/30+{in:events_lead})'
TARGET = '({in:monthly}*{in:cover}+{in:events_90}+{in:safety})'
RPT = 'ROUNDUP(%s+{in:safety},0)' % NEED_LEAD
ONH = SPN('on_hand')
tools.append(TOOL('reorder', 'Reorder Point and Reprint', 'Reprint now or wait',
    'Type the edition, the copies you hand-sell a month, the copies planned for events and the lead time; the reorder point, the copies to order and the cost come out with a verdict.', [
    I('edition', 'Edition ID', 'ED-0036', 'text'), I('monthly', 'Copies you hand-sell a month', 3.1, 'num'), I('events_lead', 'Copies planned for events during the lead time', 12, 'int'), I('events_90', 'Copies planned for events in the next 90 days', 30, 'int'),
    I('lead', 'Printer lead time, days', 21, 'int'), I('safety', 'Safety stock, copies', 6, 'int'), I('cover', 'Months of sales a reprint should cover', 3, 'int')], [
    O('Title', 'text', 'IFERROR(%s&"","")' % SP('title')), O('Copies on hand', 'int', ONH), O('Copies needed during the lead time', 'num', NEED_LEAD), O('Reorder point', 'int', RPT),
    O('Copies above (minus: below) the reorder point', 'int', '%s-%s' % (ONH, RPT)), O('Target stock after the reprint', 'int', 'ROUNDUP(%s,0)' % TARGET),
    O('Copies to order', 'int', 'MAX(0,ROUNDUP(%s,0)-%s)' % (TARGET, ONH)), O('Cost of the order at the current unit cost', 'money', 'MAX(0,ROUNDUP(%s,0)-%s)*%s' % (TARGET, ONH, SPN('unit_cost'))),
    O('Order by', 'date', '{today}+IF(%s<=%s,0,ROUNDDOWN((%s-%s)/MAX(0.01,{in:monthly}/30),0))' % (ONH, RPT, ONH, RPT)),
    O('Verdict', 'text', 'IF(%s<=%s,%s,%s)' % (ONH, RPT, v2('Reprint now'), v2('Wait')))],
    GR('What if', ('Hand-sell 6 a month', {'monthly': 6}), ('Hand-sell 1 a month', {'monthly': 1}), ('No events planned', {'events_lead': 0, 'events_90': 0}), ('Lead time 45 days', {'lead': 45}), ('Safety stock 2', {'safety': 2}))))

# 10 ----------------------------------------------------------- event profit
E_SALES = '({in:copies}*{in:price})'
E_FIXED = '({in:table_fee}+{in:travel}+{in:nights}*{in:night_cost})'
E_PROFIT = '(%s-{in:copies}*{in:copy_cost}-%s)' % (E_SALES, E_FIXED)
E_PPH = 'IF({in:hours}>0,%s/{in:hours},0)' % E_PROFIT
tools.append(TOOL('event_profit', 'Event Profit Check', 'Was this event worth the hours',
    'Type the fees, travel, nights, hours, copies sold, their cost and the new subscribers; see the profit, the profit per hour, the rank among your own events and a go-again verdict.', [
    I('table_fee', 'Table fee', 150), I('travel', 'Travel cost', 36), I('nights', 'Nights away', 0, 'int'), I('night_cost', 'Cost per night', 90), I('hours', 'Hours at the event', 8, 'num'),
    I('copies', 'Copies sold', 30, 'int'), I('price', 'Average price per copy', 17.26), I('copy_cost', 'Cost per copy sold', 7.28), I('subs', 'New subscribers', 33, 'int'), I('sub_value', 'Value of a new subscriber (your own number)', 0.5)], [
    O('Sales', 'money', E_SALES), O('Cost of the copies sold', 'money', '{in:copies}*{in:copy_cost}'), O('Fixed costs (table, travel, lodging)', 'money', E_FIXED), O('Profit', 'money', E_PROFIT),
    O('Profit per hour', 'money', E_PPH), O('Your floor per hour', 'money', FLOOR), O('Profit with the new subscribers valued', 'money', '%s+{in:subs}*{in:sub_value}' % E_PROFIT),
    O('Rank among your events by profit per hour', 'int', 'COUNTIFS({range:evprofit.pph},">"&%s)+1' % E_PPH), O('Events in your history', 'int', 'COUNT({range:evprofit.pph})'),
    O('Verdict', 'text', 'IF(%s>=%s,%s,IF(%s>0,%s,%s))' % (E_PPH, FLOOR, v3('Go again'), E_PROFIT, v3('Go again with changes'), v3('Skip')))],
    GR('What if', ('Ten more copies', {'copies': 40}), ('Table fee 60', {'table_fee': 60}), ('One night away', {'nights': 1}), ('Five hours', {'hours': 5}), ('Price 14.99', {'price': 14.99}))))

# 11 ----------------------------------------------------------- event go or skip
G_FIXED = '({in:table_fee}+{in:travel}+{in:nights}*{in:night_cost})'
G_MARGIN = '({in:price}-{in:copy_cost})'
G_PROFIT = '({in:copies}*%s-%s)' % (G_MARGIN, G_FIXED)
G_CUT = '({in:copies}*(1-{in:cut})*%s-%s)' % (G_MARGIN, G_FIXED)
G_PPHCUT = 'IF({in:hours}>0,%s/{in:hours},0)' % G_CUT
tools.append(TOOL('event_plan', 'Event Go or Skip', 'Should you book this event',
    'Type the fees, travel, nights and hours of an event you could book and the copies you expect to sell; see the break-even copies, the profit if sales fall and a verdict.', [
    I('table_fee', 'Table fee asked', 240), I('travel', 'Travel cost', 105), I('nights', 'Nights away', 2, 'int'), I('night_cost', 'Cost per night', 110), I('hours', 'Hours at the event', 16, 'num'),
    I('copies', 'Copies you expect to sell', 45, 'int'), I('price', 'Average price per copy', 17.5), I('copy_cost', 'Cost per copy sold', 7.3), I('cut', 'Fall in sales to test', 0.2, 'pct')], [
    O('Fixed costs', 'money', G_FIXED), O('Margin per copy', 'money', G_MARGIN), O('Copies to break even', 'int', 'IF(%s>0,ROUNDUP(%s/%s,0),0)' % (G_MARGIN, G_FIXED, G_MARGIN)),
    O('Expected profit', 'money', G_PROFIT), O('Expected profit per hour', 'money', 'IF({in:hours}>0,%s/{in:hours},0)' % G_PROFIT), O('Profit if sales fall', 'money', G_CUT), O('Profit per hour if sales fall', 'money', G_PPHCUT),
    O('Highest table fee that reaches your floor', 'money', 'MAX(0,{in:copies}*%s-{in:travel}-{in:nights}*{in:night_cost}-%s*{in:hours})' % (G_MARGIN, FLOOR)),
    O('Verdict', 'text', 'IF(%s>=%s,%s,IF(%s>0,%s,%s))' % (G_PPHCUT, FLOOR, v3('Book it'), G_PROFIT, v3('Negotiate'), v3('Skip')))],
    GR('What if', ('Table fee 60', {'table_fee': 60}), ('No night away', {'nights': 0, 'hours': 9}), ('Sell 70 copies', {'copies': 70}), ('Sell 30 copies', {'copies': 30}), ('Sales fall 40%', {'cut': 0.4}))))

# 12 ----------------------------------------------------------- event kind ranking
def KN(n, col): return 'IFERROR(INDEX({range:evkinds.%s},MATCH(%d,{range:evkinds.rank},0)),"")' % (col, n)
def KV(n, col): return 'IFERROR(INDEX({range:evkinds.%s},MATCH(%d,{range:evkinds.rank},0)),0)' % (col, n)
WORST = 'MAX({range:evkinds.rank})'
tools.append(TOOL('kind_rank', 'Event Kind Ranking', 'Which kind of event to do more of and which to drop',
    'Your event kinds ranked by profit per hour against your floor, with the profit you would add by moving hours from the weakest kind to the best one.', [
    I('hours_moved', 'Hours a year you could move to the best kind', 30, 'num'), I('min_events', 'Events a kind needs before you judge it', 2, 'int')], [
    *[x for n in (1, 2, 3, 4, 5) for x in (O('Rank %d: kind' % n, 'text', KN(n, 'kind')), O('Rank %d: profit per hour' % n, 'money', KV(n, 'pph')))],
    O('Kinds above your floor', 'int', 'COUNTIFS({range:evkinds.pph},">="&%s,{range:evkinds.rank},">0")' % FLOOR), O('Profit added by moving the hours', 'money', '{in:hours_moved}*(%s-%s)' % (KV(1, 'pph'), 'INDEX({range:evkinds.pph},MATCH(%s,{range:evkinds.rank},0))' % WORST)),
    O('Verdict', 'text', 'IF(INDEX({range:evkinds.events},MATCH(%s,{range:evkinds.rank},0))<{in:min_events},%s&": "&%s,IF(INDEX({range:evkinds.pph},MATCH(%s,{range:evkinds.rank},0))<%s,%s&": "&%s&". "&%s&": "&INDEX({range:evkinds.kind},MATCH(%s,{range:evkinds.rank},0)),%s&": "&%s))' % (
        WORST, v3('Do more'), KN(1, 'kind'), WORST, FLOOR, v3('Do more'), KN(1, 'kind'), v3('Change or drop'), WORST, v3('Do more'), KN(1, 'kind')))],
    GR('What if', ('Move 60 hours', {'hours_moved': 60}), ('Move 10 hours', {'hours_moved': 10}), ('Judge from 1 event', {'min_events': 1}), ('Judge from 4 events', {'min_events': 4}))))

# 13 ----------------------------------------------------------- stock to take to an event
def EDN(n): return 'INDEX({range:stockpos.edition_id},MATCH(%d,{range:stockpos.sold_rank},0))' % n
def NEEDN(n): return 'ROUNDUP(IFERROR(SUMIFS({range:evlines.copies},{range:evlines.edition_id},%s,{range:evlines.kind},{in:kind})/COUNTIFS({range:events.kind},{in:kind}),0)*(1+{in:spare}),0)' % EDN(n)
def HANDN(n): return 'SUMIFS({range:stockpos.on_hand},{range:stockpos.edition_id},%s)' % EDN(n)
def PACKN(n): return 'MIN(%s,%s)' % (HANDN(n), NEEDN(n))
SHORT = '+'.join('IF(%s>%s,1,0)' % (NEEDN(n), HANDN(n)) for n in range(1, 7))
tools.append(TOOL('pack_list', 'Stock to Take to an Event', 'How many copies of each edition to pack for an event',
    'Choose the kind of event and the spare share; the copies to pack for your six best sellers come from your own sales at that kind of event, limited to the copies on hand.', [
    IL('kind', 'Kind of event', 'ekind', 'Book fair'), I('spare', 'Spare copies', 0.2, 'pct')], [
    *[x for n in range(1, 7) for x in (O('Pack %d: title' % n, 'text', 'IFERROR(INDEX({range:stockpos.title},MATCH(%d,{range:stockpos.sold_rank},0))&"","")' % n), O('Pack %d: copies' % n, 'int', 'IFERROR(%s,0)' % PACKN(n)))],
    O('Copies to pack in all', 'int', '+'.join('IFERROR(%s,0)' % PACKN(n) for n in range(1, 7))), O('Editions with fewer copies than needed', 'int', 'IFERROR(%s,0)' % SHORT),
    O('Verdict', 'text', 'IF(IFERROR(%s,0)=0,%s,%s)' % (SHORT, v2('Enough stock'), v2('Reprint first')))],
    GR('What if', ('Author market', {'kind': '=' + tok('ekind', 'Author market')}), ('Genre convention', {'kind': '=' + tok('ekind', 'Genre convention')}), ('Library talk', {'kind': '=' + tok('ekind', 'Library talk')}),
       ('Signing at a shop', {'kind': '=' + tok('ekind', 'Signing at a shop')}), ('Spare 50%', {'spare': 0.5}))))

# 14 ----------------------------------------------------------- rights deal ledger
def DL(col): return 'INDEX({range:deals.%s},MATCH({in:deal},{range:deals.deal_id},0))' % col
def DLN(col): return 'IFERROR(%s,0)' % DL(col)
tools.append(TOOL('deal_ledger', 'Rights Deal Ledger Tool', 'What one rights deal is worth and what is still to collect',
    'Type a deal ID; see its fee, agent share, effective income in total and per year, what was received and what is still to collect, and the totals of all deals. Status and amounts only.', [
    I('deal', 'Deal ID', 'RD-02', 'text'), I('agent_alt', 'Agent share to test', 0.1, 'pct')], [
    O('Title', 'text', 'IFERROR(%s&"","")' % DL('title')), O('Kind', 'text', 'IFERROR(%s&"","")' % DL('kind')), O('Status', 'text', 'IFERROR(%s&"","")' % DL('status')), O('Fee', 'money', DLN('fee')),
    O('Agent share, amount', 'money', DLN('agent_fee')), O('Effective income', 'money', DLN('net_fee')), O('Effective income per year', 'money', DLN('per_year')), O('Received', 'money', DLN('received')),
    O('Still to collect', 'money', DLN('to_collect')),
    O('Effective income at the agent share to test', 'money', '%s*(1-{in:agent_alt})' % DLN('fee')),
    O('Fees of signed deals, all', 'money', 'SUMIFS({range:deals.fee},{range:deals.status},"<>"&%s)' % S_OFFER), O('Received, all deals', 'money', 'SUM({range:deals.received})'),
    O('Still to collect, all deals', 'money', 'SUM({range:deals.to_collect})'), O('Open offers', 'int', 'COUNTIFS({range:deals.status},%s)' % S_OFFER), O('Value of open offers', 'money', 'SUMIFS({range:deals.fee},{range:deals.status},%s)' % S_OFFER),
    O('Verdict', 'text', 'IFERROR(%s,"")' % DL('verdict'))],
    GR('What if', ('Agent share 5%', {'agent_alt': 0.05}), ('Agent share 10%', {'agent_alt': 0.10}), ('Agent share 20%', {'agent_alt': 0.20}), ('Agent share 25%', {'agent_alt': 0.25}))))

# 15 ----------------------------------------------------------- rights payments due
def IR(n, col): return 'IFERROR(INDEX({range:instal.%s},MATCH(%d,{range:instal.order_no},0)),"")' % (col, n)
def IRN(n, col): return 'IFERROR(INDEX({range:instal.%s},MATCH(%d,{range:instal.order_no},0)),0)' % (col, n)
OVER_N = 'COUNTIFS({range:instal.open},1,{range:instal.due_date},"<"&({today}-{in:grace}))'
tools.append(TOOL('payments_due', 'Rights Payments Due', 'Which rights payments arrive next and which to chase',
    'The open rights payments in date order (overdue ones first) with the amount due in your window; type the days of grace you give an agent before a payment counts as late.', [
    I('days', 'Days ahead to look', 90, 'int'), I('grace', 'Days of grace before you chase', 7, 'int')], [
    O('Payments due in the window', 'int', 'COUNTIFS({range:instal.open},1,{range:instal.due_date},"<="&({today}+{in:days}))'),
    O('Amount due in the window', 'money', 'SUMIFS({range:instal.amount},{range:instal.open},1,{range:instal.due_date},"<="&({today}+{in:days}))'),
    O('Payments to chase now', 'int', OVER_N), O('Amount to chase now', 'money', 'SUMIFS({range:instal.amount},{range:instal.open},1,{range:instal.due_date},"<"&({today}-{in:grace}))'),
    *[x for n in (1, 2, 3, 4) for x in (O('Next %d: title' % n, 'text', IR(n, 'title')), O('Next %d: due date' % n, 'date', IR(n, 'due_date')), O('Next %d: amount' % n, 'money', IRN(n, 'amount')))],
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (OVER_N, v4('Chase the agent'), v4('Cash arriving')))],
    GR('What if', ('Look 30 days ahead', {'days': 30}), ('Look 60 days ahead', {'days': 60}), ('Look 180 days ahead', {'days': 180}), ('No grace', {'grace': 0}))))

# 16 ----------------------------------------------------------- rights expiry watch
NXT = 'SUMPRODUCT(MIN({range:deals.term_end}+(({range:deals.term_end}<{today})+({range:deals.term_end}=0))*100000))'
def NX(col): return 'IFERROR(INDEX({range:deals.%s},MATCH(%s,{range:deals.term_end},0)),0)' % (col, NXT)
tools.append(TOOL('expiry_watch', 'Rights Expiry Watch', 'Which rights deal ends next and what to do about it',
    'Type how far ahead to look, the days of notice you need and the net a year that makes a renewal worth it; see the next deal to end, its decide-by date, a verdict and the deals expired.', [
    I('window', 'Months ahead to look', 24, 'int'), I('notice', 'Days of notice you need before the end', 90, 'int'), I('renew_min', 'Net income per year that makes a renewal worth it', 250)], [
    O('Deals ending inside the window', 'int', 'COUNTIFS({range:deals.term_end},">="&{today},{range:deals.term_end},"<="&EDATE({today},{in:window}))'),
    O('Deals already expired', 'int', 'COUNTIFS({range:deals.status},%s)' % S_EXP),
    O('Next deal to end: title', 'text', 'IF(%s>99999,"",IFERROR(INDEX({range:deals.title},MATCH(%s,{range:deals.term_end},0))&"",""))' % (NXT, NXT)),
    O('Next deal to end: term ends', 'date', 'IF(%s>99999,"",%s)' % (NXT, NXT)), O('Days to the end', 'int', 'IF(%s>99999,0,%s-{today})' % (NXT, NXT)),
    O('Decide by', 'date', 'IF(%s>99999,"",%s-{in:notice})' % (NXT, NXT)), O('Net income per year of that deal', 'money', 'IF(%s>99999,0,%s)' % (NXT, NX('per_year'))),
    O('Latest expired deal: title', 'text', 'IFERROR(INDEX({range:deals.title},MATCH(%s,{range:deals.status},0))&"","")' % S_EXP),
    O('Days since it expired', 'int', 'IFERROR({today}-INDEX({range:deals.term_end},MATCH(%s,{range:deals.status},0)),0)' % S_EXP),
    O('Verdict', 'text', 'IF(%s>99999,%s,IF(%s-{today}>{in:notice},%s,IF(%s>={in:renew_min},%s,%s)))' % (NXT, v4('No deal ends soon'), NXT, v4('Decide by date'), NX('per_year'), v4('Renew'), v4('Take back')))],
    GR('What if', ('Look 48 months ahead', {'window': 48}), ('Look 12 months ahead', {'window': 12}), ('Need 900 days of notice', {'notice': 900}), ('Renewal needs 400 a year', {'renew_min': 400}), ('Renewal needs 100 a year', {'renew_min': 100, 'notice': 700}))))

# 17 ----------------------------------------------------------- rights offer review
O_AGENT = '({in:fee}*{in:agent})'
O_NET = '({in:fee}-%s-{in:costs})' % O_AGENT
O_YEAR = 'IF({in:years}>0,%s/{in:years},0)' % O_NET
O_COUNTER = '(({in:min_year}*{in:years}+{in:costs})/(1-{in:agent}))'
tools.append(TOOL('offer_review', 'Rights Offer Review', 'Accept, counter or decline a rights offer',
    'Type the fee offered, the agent share, the term and your costs to deliver; see the net a year against your minimum, the fee to counter with and a verdict. Confirm terms with your adviser.', [
    I('fee', 'Fee offered', 1900), I('agent', 'Agent share', 0.15, 'pct'), I('years', 'Term in years', 7, 'int'), I('costs', 'Your costs to deliver (files, checks)', 150), I('min_year', 'Net income per year you want (your own number)', 250),
    I('counter_floor', 'Share of that minimum you still counter on', 0.7, 'pct')], [
    O('Agent share, amount', 'money', O_AGENT), O('Fee after the agent', 'money', '{in:fee}-%s' % O_AGENT), O('Net after your costs', 'money', O_NET), O('Net income per year', 'money', O_YEAR),
    O('Net income per year you want', 'money', '{in:min_year}'), O('Fee to counter with', 'money', O_COUNTER), O('Rise over the offer', 'pct', 'IF({in:fee}>0,%s/{in:fee}-1,0)' % O_COUNTER),
    O('Verdict', 'text', 'IF(%s>={in:min_year},%s,IF(%s>={in:min_year}*{in:counter_floor},%s,%s))' % (O_YEAR, v4('Accept'), O_YEAR, v4('Counter'), v4('Decline')))],
    GR('What if', ('Fee 2500', {'fee': 2500}), ('Fee 1200', {'fee': 1200}), ('Agent share 20%', {'agent': 0.2}), ('Term 3 years', {'years': 3}), ('Costs 400', {'costs': 400}))))

# 18 ----------------------------------------------------------- direct and event income forecast
DN3 = 'AVERAGEIFS({range:dmonth.net},{range:dmonth.month},">="&EDATE(%s,-3),{range:dmonth.month},"<"&%s)' % (MS, MS)
EV12 = 'SUMIFS({range:events.profit},{range:events.date},">"&({today}-365))/12'
SCN = 'IF({in:scenario}=%s,1+{in:best},IF({in:scenario}=%s,1-{in:worst},1))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
def MF(k): return '(%s*POWER(1+{in:growth},%d)+%s)*%s' % (DN3, k, EV12, SCN)
GS = '(' + '+'.join('POWER(1+{in:growth},%d)' % k for k in range(1, 7)) + ')'
def TOT(f): return '(%s*%s+6*%s)*%s' % (DN3, GS, EV12, f)
tools.append(TOOL('forecast', 'Direct and Event Forecast', 'Are the next 6 months of direct and event income on track',
    'The next 6 months from your own history: direct net of the last 3 full months grown by your rate plus event profit of the last 12 months, in three scenarios, against your monthly target.', [
    IL('scenario', 'Scenario', 'scen', 'Base'), I('growth', 'Growth of direct net per month (your own number)', 0.02, 'pct'), I('best', 'Best case, rise in income', 0.15, 'pct'), I('worst', 'Worst case, fall in income', 0.2, 'pct'),
    I('target', 'Direct net plus event profit you want a month', 1000)], [
    O('Direct net a month, last 3 full months', 'money', DN3), O('Event profit a month, last 12 months', 'money', EV12),
    *[O('Month %d (chosen scenario)' % k, 'money', MF(k)) for k in range(1, 7)],
    O('Six months, chosen scenario', 'money', TOT(SCN)), O('Six months, Base', 'money', TOT('1')), O('Six months, Best', 'money', TOT('(1+{in:best})')), O('Six months, Worst', 'money', TOT('(1-{in:worst})')),
    O('Average a month, chosen scenario', 'money', '%s/6' % TOT(SCN)), O('Target a month', 'money', '{in:target}'),
    O('Verdict', 'text', 'IF(%s/6>={in:target},%s,%s)' % (TOT(SCN), v4('On track for the target'), v4('Below the target')))],
    GR('What if', ('Best case', {'scenario': '=' + tok('scen', 'Best')}), ('Worst case', {'scenario': '=' + tok('scen', 'Worst')}), ('Growth 6% a month', {'growth': 0.06}), ('Target 800', {'target': 800}), ('Target 1,600', {'target': 1600}))))
assert len(tools) == 18, len(tools)
