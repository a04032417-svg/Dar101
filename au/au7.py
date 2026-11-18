"""Author and Self-Publisher Business suite - part 7: Direct Sales, Stock, Events and Rights."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au7_lists import *
from au7_tables import settings, tables
from au7_tools import tools

SUITE = 'fx-20261115-author-publisher'
NOTE = "Sample wording: adapt it to your own business."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
MV_LOST = tok('move', 'Damaged or lost'); MV_SOLD = tok('move', 'Sold at event')
S_OFFER, S_SIGNED, S_DELIV, S_PAID, S_EXP = (tok('dstatus', m) for m in ('Offer', 'Signed', 'Delivered', 'Paid in full', 'Expired'))
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
M12 = '{range:dmonth.month},">"&EDATE(%s,-12)' % MS
E12 = '{range:events.date},">"&({today}-365)'

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('direct_order_sheet', 'Direct Order Entry Sheet', 'Direct order with its net', 'orders.order_id', F(
        ('Date', 'orders.date'), ('Country', 'orders.country'), ('Currency', 'orders.currency'), ('Edition', 'orders.edition_id'), ('Title', 'orders.title'), ('Format', 'orders.format'), ('Quantity', 'orders.qty'),
        ('Unit price', 'orders.unit_price'), ('Discount', 'orders.discount'), ('Sales tax collected (not income)', 'orders.tax_collected'), ('Shipping charged', 'orders.shipping_charged'), ('Payment fee', 'orders.payment_fee'),
        ('Delivery cost', 'orders.delivery_cost'), ('Rate', 'orders.rate'), ('Net, home currency', 'orders.net_home'), ('Net per copy', 'orders.net_per_copy')) + [
        FF('Sales tax rate of the country', 'INDEX({range:countries.sales_tax_pct},MATCH(%s,{range:countries.country},0))' % LK('orders', 'order_id', 'country'), 'pct'),
        FF('Payment fee as a share of the charge', 'IFERROR(%s/(%s*%s-%s+%s+%s),0)' % (LK('orders', 'order_id', 'payment_fee'), LK('orders', 'order_id', 'qty'), LK('orders', 'order_id', 'unit_price'), LK('orders', 'order_id', 'discount'),
                                                                                    LK('orders', 'order_id', 'shipping_charged'), LK('orders', 'order_id', 'tax_collected')), 'pct'),
        FF('Direct price of the edition today', 'INDEX({range:editions.direct_price},MATCH(%s,{range:editions.edition_id},0))' % LK('orders', 'order_id', 'edition_id'), 'money')]),
    FORM('price_check_sheet', 'Direct Price Check Sheet', 'Direct price check of one edition', 'dmargin.edition_id', F(
        ('Title', 'dmargin.title'), ('Format', 'dmargin.format'), ('List price', 'dmargin.list_price'), ('Direct price', 'dmargin.direct_price'), ('Shipping charged', 'dmargin.shipping_charged'), ('Payment fee', 'dmargin.payment_fee'),
        ('Delivery cost', 'dmargin.delivery_cost'), ('Direct net per copy', 'dmargin.net_copy'), ('Store royalty per copy', 'dmargin.store_royalty'), ('Direct minus store', 'dmargin.difference'),
        ('Lowest direct price', 'dmargin.min_price'), ('Price to set', 'dmargin.new_price'), ('Verdict', 'dmargin.verdict'), ('Recent ledger royalty per copy', 'dmargin.ledger_royalty'), ('Price checked on', 'dmargin.review_on')) + [
        FF('Direct net as a share of the price', 'IFERROR(%s/%s,0)' % (LK('dmargin', 'edition_id', 'net_copy'), LK('dmargin', 'edition_id', 'direct_price')), 'pct'),
        FF('Lowest net you accept', '{set:min_net_copy}', 'money')]),
    FORM('share_goal_sheet', 'Direct Share Goal Sheet', 'Direct share of income for one month', 'dgoal.month', F(
        ('Direct net', 'dgoal.direct_net'), ('All revenue', 'dgoal.all_revenue'), ('Direct share', 'dgoal.share'), ('Your goal', 'dgoal.target'), ('Gap to goal', 'dgoal.gap'), ('Extra direct net to reach the goal', 'dgoal.net_needed'),
        ('Status', 'dgoal.status')) + [
        FF('Orders in the month', 'INDEX({range:dmonth.orders},MATCH({pick},{range:dmonth.month},0))', 'int'), FF('Net per order', 'INDEX({range:dmonth.avg_net_order},MATCH({pick},{range:dmonth.month},0))', 'money'),
        FF('Net, 3-month average', 'INDEX({range:dmonth.net_3m},MATCH({pick},{range:dmonth.month},0))', 'money'),
        FF('Direct share a year earlier', 'IFERROR(INDEX({range:dmonth.share},MATCH(EDATE({pick},-12),{range:dmonth.month},0)),0)', 'pct')]),
    FORM('print_margin_sheet', 'Print Margin Sheet', 'Print margin of one edition', 'printm.edition_id', F(
        ('Title', 'printm.title'), ('Format', 'printm.format'), ('Pages', 'printm.pages'), ('Print cost', 'printm.print_cost'), ('List price', 'printm.list_price'), ('Store royalty per copy', 'printm.royalty_copy'),
        ('Author copy cost with shipping', 'printm.copy_cost'), ('Margin per hand-sold copy', 'printm.margin'), ('Margin percent', 'printm.margin_pct'), ('Minimum price', 'printm.min_price'), ('Verdict', 'printm.verdict'),
        ('Print cost checked on', 'printm.checked_on')) + [
        FF('Margin you want', '{set:print_margin_target}', 'pct'), FF('Price rise needed to hold the margin', 'MAX(0,%s-%s)' % (LK('printm', 'edition_id', 'min_price'), LK('printm', 'edition_id', 'list_price')), 'money')]),
    FORM('author_copy_sheet', 'Author Copy Order Sheet', 'Author copy order for one edition', 'printm.edition_id', F(
        ('Title', 'printm.title'), ('Format', 'printm.format'), ('Printer', 'printm.printer_name'), ('Printer phone', 'printm.printer_phone'), ('Usual order, copies', 'printm.order_copies'), ('Author copy cost with shipping', 'printm.copy_cost'),
        ('Cost of a usual order', 'printm.order_cost'), ('List price', 'printm.list_price'), ('Margin per hand-sold copy', 'printm.margin')) + [
        FF('Margin if every copy sells', '%s*%s' % (LK('printm', 'edition_id', 'order_copies'), LK('printm', 'edition_id', 'margin')), 'money'),
        FF('Copies you usually sell of those taken', 'ROUND(%s*SUM({range:events.copies_sold})/SUM({range:events.copies_taken}),0)' % LK('printm', 'edition_id', 'order_copies'), 'int'),
        FF('Copies on hand now', 'IFERROR(INDEX({range:stockpos.on_hand},MATCH({pick},{range:stockpos.edition_id},0)),0)', 'int')]),
    FORM('stock_count_sheet', 'Stock Count Sheet', 'Stock count of one edition', 'stockpos.edition_id', F(
        ('Title', 'stockpos.title'), ('Format', 'stockpos.format'), ('Copies in', 'stockpos.copies_in'), ('Sold at events', 'stockpos.sold'), ('Given away', 'stockpos.given'), ('Lost or damaged', 'stockpos.lost'),
        ('Copies on hand by the sheet', 'stockpos.on_hand'), ('Unit cost', 'stockpos.unit_cost'), ('Value at cost', 'stockpos.value'), ('Last counted on', 'stockpos.counted_on'), ('Days since the count', 'stockpos.days_since_count')) + [
        FF('Value of copies sold at events, at cost', '%s*%s' % (LK('stockpos', 'edition_id', 'sold'), LK('stockpos', 'edition_id', 'unit_cost')), 'money')]),
    FORM('reprint_sheet', 'Reprint Decision Sheet', 'Reprint decision for one edition', 'stockpos.edition_id', F(
        ('Title', 'stockpos.title'), ('Format', 'stockpos.format'), ('Copies on hand', 'stockpos.on_hand'), ('Sold at events, last 12 months', 'stockpos.sold_12m'), ('Copies a month', 'stockpos.per_month'),
        ('Reorder point', 'stockpos.reorder_point'), ('Copies to order', 'stockpos.to_order'), ('Verdict', 'stockpos.verdict'), ('Order by', 'stockpos.need_by'), ('Printer', 'stockpos.printer_name'), ('Printer phone', 'stockpos.printer_phone')) + [
        FF('Cost of the order at the unit cost', '%s*%s' % (LK('stockpos', 'edition_id', 'to_order'), LK('stockpos', 'edition_id', 'unit_cost')), 'money'),
        FF('Months of stock left', 'IFERROR(%s/%s,0)' % (LK('stockpos', 'edition_id', 'on_hand'), LK('stockpos', 'edition_id', 'per_month')), 'num'), FF('Printer lead time, days', '{set:printer_lead_days}', 'int')]),
    FORM('event_plan_sheet', 'Event Plan Sheet', 'Event plan from a past event as a template', 'evprofit.event_id', F(
        ('Event', 'evprofit.name'), ('Kind', 'evprofit.kind'), ('Date', 'evprofit.date'), ('Hours', 'evprofit.hours'), ('Fixed costs', 'evprofit.fixed_costs'), ('Margin per copy sold', 'evprofit.margin_copy'),
        ('Copies to break even', 'evprofit.break_even'), ('Profit if sales fall', 'evprofit.profit_cut'), ('Sell-through last time', 'evprofit.sell_through'), ('Organiser', 'evprofit.organiser_name'), ('Organiser phone', 'evprofit.organiser_phone')) + [
        FF('Copies taken last time', 'INDEX({range:events.copies_taken},MATCH({pick},{range:events.event_id},0))', 'int'), FF('Copies sold last time', 'INDEX({range:events.copies_sold},MATCH({pick},{range:events.event_id},0))', 'int'),
        FF('Fixed costs per hour', 'IFERROR(%s/%s,0)' % (LK('evprofit', 'event_id', 'fixed_costs'), LK('evprofit', 'event_id', 'hours')), 'money'), FF('Your floor per hour', '{set:event_hour_floor}', 'money')]),
    FORM('event_result_sheet', 'Event Result Sheet', 'Event result with the verdict', 'evprofit.event_id', F(
        ('Event', 'evprofit.name'), ('Kind', 'evprofit.kind'), ('Date', 'evprofit.date'), ('Hours', 'evprofit.hours'), ('Sales', 'evprofit.sales'), ('Costs', 'evprofit.costs'), ('Profit', 'evprofit.profit'),
        ('Profit per hour', 'evprofit.pph'), ('Sell-through', 'evprofit.sell_through'), ('New subscribers', 'evprofit.subscribers'), ('Rank by profit per hour', 'evprofit.rank'), ('Verdict', 'evprofit.verdict')) + [
        FF('Your floor per hour', '{set:event_hour_floor}', 'money'), FF('Profit per hour of this kind', 'INDEX({range:evkinds.pph},MATCH(%s,{range:evkinds.kind},0))' % LK('evprofit', 'event_id', 'kind'), 'money'),
        FF('Events in your history', 'COUNT({range:evprofit.pph})', 'int')]),
    FORM('event_packing_sheet', 'Event Packing Sheet', 'Packing list of an event', 'events.event_id', F(
        ('Event', 'events.name'), ('Kind', 'events.kind'), ('Date', 'events.date'), ('City', 'events.city'), ('Hours', 'events.hours'), ('Copies taken', 'events.copies_taken'), ('Copies sold', 'events.copies_sold'),
        ('Organiser', 'events.organiser_name'), ('Organiser phone', 'events.organiser_phone'), ('Assistant', 'events.va_name')) + [
        FF('Copies left over', '%s-%s' % (LK('events', 'event_id', 'copies_taken'), LK('events', 'event_id', 'copies_sold')), 'int'),
        FF('Sale lines for this event', 'COUNTIFS({range:evlines.event_id},{pick})', 'int')],
        {"from": "evlines", "match": "evlines.event_id", "columns": ["title", "format", "copies", "price", "line_total"], "max": 14}),
    FORM('rights_deal_sheet', 'Rights Deal Sheet', 'Rights deal with the money', 'deals.deal_id', F(
        ('Title', 'deals.title'), ('Kind', 'deals.kind'), ('Language', 'deals.language'), ('Territory', 'deals.territory'), ('Offered on', 'deals.offered_on'), ('Signed on', 'deals.signed_on'), ('Term, years', 'deals.term_years'),
        ('Term ends', 'deals.term_end'), ('Fee', 'deals.fee'), ('Agent share', 'deals.agent_pct'), ('Status', 'deals.status'), ('Received', 'deals.received'), ('Still to collect', 'deals.to_collect'),
        ('Effective income', 'deals.net_fee'), ('Effective income per year', 'deals.per_year'), ('Verdict', 'deals.verdict')) + [
        FF('Payments still open', 'COUNTIFS({range:instal.deal_id},{pick},{range:instal.open},1)', 'int'), FF('Rights agent', 'INDEX({range:deals.agent_name},MATCH({pick},{range:deals.deal_id},0))', 'text')]),
    FORM('rights_payment_sheet', 'Rights Payment Sheet', 'Rights payment due or received', 'instal.instalment_id', F(
        ('Deal', 'instal.deal_id'), ('Title', 'instal.title'), ('Kind', 'instal.kind'), ('Language', 'instal.language'), ('Due date', 'instal.due_date'), ('Amount', 'instal.amount'), ('Received on', 'instal.received_on'),
        ('Check', 'instal.check'), ('Rights agent', 'instal.agent_name'), ('Agent phone', 'instal.agent_phone')) + [
        FF('Fee of the whole deal', 'INDEX({range:deals.fee},MATCH(%s,{range:deals.deal_id},0))' % LK('instal', 'instalment_id', 'deal_id'), 'money'),
        FF('Received so far on the deal', 'INDEX({range:deals.received},MATCH(%s,{range:deals.deal_id},0))' % LK('instal', 'instalment_id', 'deal_id'), 'money'),
        FF('Still to collect on the deal', 'INDEX({range:deals.to_collect},MATCH(%s,{range:deals.deal_id},0))' % LK('instal', 'instalment_id', 'deal_id'), 'money')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('margin_report_doc', 'Direct Margin Report', 'Direct store margin report with a price request', 'dmargin.edition_id', [
        'Direct store margin report of {set:company}, dated {today}. For {col:dmargin.web_name}, phone {col:dmargin.web_phone}. Edition: {col:dmargin.title} ({col:dmargin.format}). Price checked on {col:dmargin.review_on}.',
        'Direct price: {col:dmargin.direct_price}. Direct net per copy after the payment fee {col:dmargin.payment_fee} and delivery {col:dmargin.delivery_cost}: {col:dmargin.net_copy}. The same edition through a store pays {col:dmargin.store_royalty}, a difference of {col:dmargin.difference}. Verdict: {col:dmargin.verdict}.',
        'Request: please set the direct price of this edition to {col:dmargin.new_price} (the lowest price that holds the net is {col:dmargin.min_price}) and tell us when it is done.',
        'Sales tax collected is not income: confirm its treatment with your adviser.'], ['Author-publisher', 'Web developer'], NOTE),
    DOC('orders_month_doc', 'Direct Orders Summary', 'Direct orders summary for one month', 'dmonth.month', [
        'Direct orders summary of {set:company}, dated {today}. Month: {col:dmonth.month}.',
        'Orders: {col:dmonth.orders}. Copies: {col:dmonth.copies}. Item sales: {col:dmonth.gross}. Discounts: {col:dmonth.discounts}. Shipping charged: {col:dmonth.shipping_charged}. Payment fees: {col:dmonth.fees}. Delivery cost: {col:dmonth.delivery}. Direct net: {col:dmonth.net}.',
        'Sales tax collected: {col:dmonth.tax_collected}. It is not income and is shown here only so that it can be passed on; confirm with your adviser how to treat it.',
        'Net per order: {col:dmonth.avg_net_order}. Net per copy: {col:dmonth.net_copy}. Fees as a share of item sales: {col:dmonth.fee_share}. Direct share of all income: {col:dmonth.share}.'], ['Author-publisher', 'Accountant'], NOTE),
    DOC('share_report_doc', 'Direct Share Report', 'Direct share report against your goal', 'dgoal.month', [
        'Direct share report of {set:company}, dated {today}. Month: {col:dgoal.month}.',
        'Direct net: {col:dgoal.direct_net}. All revenue: {col:dgoal.all_revenue}. Direct share of income: {col:dgoal.share}. Your goal: {col:dgoal.target}. Gap: {col:dgoal.gap}. Status: {col:dgoal.status}.',
        'To reach the goal in this month the direct net would have needed to be higher by {col:dgoal.net_needed}, with all other income unchanged. The goal is your own number.', 'Write the steps you will take below.'], ['Author-publisher'], NOTE),
    DOC('print_margin_doc', 'Print Margin by Edition', 'Print margin sheet for one edition', 'printm.edition_id', [
        'Print margin sheet of {set:company}, dated {today}. Edition: {col:printm.title} ({col:printm.format}, {col:printm.pages} pages). Print cost checked on {col:printm.checked_on}.',
        'Print cost: {col:printm.print_cost}. List price: {col:printm.list_price}. A store pays you {col:printm.royalty_copy} per copy. An author copy costs {col:printm.copy_cost} with shipping.',
        'Sold by hand at the list price the margin is {col:printm.margin} per copy, {col:printm.margin_pct} of the price. The lowest price that holds your margin is {col:printm.min_price}. Verdict: {col:printm.verdict}.', 'Prices and costs are your own numbers: ask your printer for a current quote.'], ['Author-publisher', 'Printer'], NOTE),
    DOC('copy_order_doc', 'Author Copy Order Note', 'Author copy order note to the printer', 'printm.edition_id', [
        'Order note of {set:company}, dated {today}. To: {col:printm.printer_name}, phone {col:printm.printer_phone}.',
        'Please quote and print {col:printm.order_copies} author copies of {col:printm.title} ({col:printm.format}, {col:printm.pages} pages). Our last known cost is {col:printm.print_cost} a copy, {col:printm.copy_cost} with shipping, so about {col:printm.order_cost} for the order.',
        'Please confirm the price, the delivery date and the shipping cost before you start, and send a proof copy if the file has changed.', 'Thank you.'], ['Author-publisher', 'Printer'], NOTE),
    DOC('count_report_doc', 'Stock Count Report', 'Stock count report for one edition', 'stockpos.edition_id', [
        'Stock count report of {set:company}, dated {today}. Edition: {col:stockpos.title} ({col:stockpos.format}). Last counted on {col:stockpos.counted_on}, {col:stockpos.days_since_count} days ago.',
        'Copies in: {col:stockpos.copies_in}. Sold at events: {col:stockpos.sold}. Given away: {col:stockpos.given}. Lost or damaged: {col:stockpos.lost}. Copies on hand by the sheet: {col:stockpos.on_hand}.',
        'Unit cost: {col:stockpos.unit_cost}. Value of the stock at cost: {col:stockpos.value}.', 'Copies counted on the shelf: ____. Difference: ____. Counted by: ____.'], ['Author-publisher', 'Assistant'], NOTE),
    DOC('reprint_note_doc', 'Reprint Decision Note', 'Reprint decision note for one edition', 'stockpos.edition_id', [
        'Reprint decision note of {set:company}, dated {today}. Edition: {col:stockpos.title} ({col:stockpos.format}).',
        'Copies on hand: {col:stockpos.on_hand}. Sold at events in the last 12 months: {col:stockpos.sold_12m}, about {col:stockpos.per_month} a month. Reorder point: {col:stockpos.reorder_point}. Verdict: {col:stockpos.verdict}.',
        'Copies to order: {col:stockpos.to_order}, at a unit cost of {col:stockpos.unit_cost}. Order by {col:stockpos.need_by} to allow for the printer lead time. Printer: {col:stockpos.printer_name}, phone {col:stockpos.printer_phone}.', 'Decision and date: ____.'], ['Author-publisher', 'Printer'], NOTE),
    DOC('event_budget_doc', 'Event Plan and Budget', 'Event plan and budget from a past event', 'evprofit.event_id', [
        'Event plan of {set:company}, dated {today}. Event: {col:evprofit.name} ({col:evprofit.kind}), last held on {col:evprofit.date}, {col:evprofit.hours} hours.',
        'Fixed costs: {col:evprofit.fixed_costs}. Margin per copy sold: {col:evprofit.margin_copy}. Copies to break even: {col:evprofit.break_even}. Profit if sales fall: {col:evprofit.profit_cut}.',
        'Last time the sales were {col:evprofit.sales}, the profit {col:evprofit.profit} and the profit per hour {col:evprofit.pph}, against your floor of {col:evprofit.floor}. Verdict: {col:evprofit.verdict}.',
        'Organiser: {col:evprofit.organiser_name}, phone {col:evprofit.organiser_phone}. Copies to pack: ____. Budget approved by: ____.'], ['Author-publisher', 'Assistant'], NOTE),
    DOC('event_result_doc', 'Event Result Report', 'Event result report', 'evprofit.event_id', [
        'Event result report of {set:company}, dated {today}. Event: {col:evprofit.name} ({col:evprofit.kind}) on {col:evprofit.date}.',
        'Hours: {col:evprofit.hours}. Sales: {col:evprofit.sales}. Costs: {col:evprofit.costs}. Profit: {col:evprofit.profit}. Profit per hour: {col:evprofit.pph}. Sell-through: {col:evprofit.sell_through}. New subscribers: {col:evprofit.subscribers}.',
        'Rank among your events by profit per hour: {col:evprofit.rank}. Verdict: {col:evprofit.verdict}. Your floor is {col:evprofit.floor} an hour.', 'Notes for the next time: ____.'], ['Author-publisher'], NOTE),
    DOC('kind_ranking_doc', 'Event History Ranking', 'Event history for one kind of event', 'evkinds.kind', [
        'Event history of {set:company}, dated {today}. Kind: {col:evkinds.kind}.',
        'Events: {col:evkinds.events}. Hours: {col:evkinds.hours}. Copies sold: {col:evkinds.copies_sold}. Costs: {col:evkinds.costs}. Profit: {col:evkinds.profit}. Profit per hour: {col:evkinds.pph}.',
        'Rank among the kinds of event: {col:evkinds.rank}. Verdict against your own floor: {col:evkinds.verdict}.', 'Write what you will do with this kind of event next year below.'], ['Author-publisher'], NOTE),
    DOC('deal_register_doc', 'Rights Deal Register', 'Rights deal register entry', 'deals.deal_id', [
        'Rights deal register of {set:company}, dated {today}. Deal {col:deals.deal_id}: {col:deals.title}, {col:deals.kind}, {col:deals.language}, territory {col:deals.territory}.',
        'Offered on {col:deals.offered_on}, signed on {col:deals.signed_on}, term {col:deals.term_years} years, ending {col:deals.term_end}. Status: {col:deals.status}.',
        'Fee: {col:deals.fee}. Agent share: {col:deals.agent_pct} ({col:deals.agent_fee}). Effective income: {col:deals.net_fee}, {col:deals.per_year} a year. Received: {col:deals.received}. Still to collect: {col:deals.to_collect}. Verdict: {col:deals.verdict}.',
        'This register keeps status and amounts only. Confirm every term of the deal with your adviser.'], ['Author-publisher', 'Rights agent'], NOTE),
    DOC('payments_due_doc', 'Rights Payments Due Report', 'Rights payment report', 'instal.instalment_id', [
        'Rights payment report of {set:company}, dated {today}. Deal: {col:instal.deal_id}, {col:instal.title} ({col:instal.kind}, {col:instal.language}).',
        'Payment {col:instal.instalment_id}: amount {col:instal.amount}, due on {col:instal.due_date}, received on {col:instal.received_on}. Check: {col:instal.check}.',
        'Payments due in the next days of your window: {col:instal.window_count}, worth {col:instal.window_amount} in all.',
        'Dear {col:instal.agent_name} (phone {col:instal.agent_phone}), please tell us the date this payment was or will be sent. If it has arrived, please ignore this report.'], ['Author-publisher', 'Rights agent'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('direct_weekly', 'Direct Store Weekly Check', 'dmonth', 'dmonth.month', [('Check that every order of the week is in Direct Orders', 7), ('Compare the payment fees with the settings', 7), ('Check the stock of printed copies before you sell more', 8),
                                                                              ('Answer customer messages and refunds', 8), ('Check the sales tax on foreign orders', 9), ('Note the direct net of the week', 9)]),
    CHK('price_change', 'Direct Price Change', 'dmargin', 'dmargin.review_on', [('Read the verdict and the lowest price of the edition', 0), ('Choose the new price and any discount', 1), ('Ask the web developer to change it', 2), ('Check the price in the store page', 3),
                                                                             ('Write the date in Price checked on', 3), ('Tell the newsletter partner if it is a promotion', 4)]),
    CHK('orders_month_end', 'Direct Orders Month-end', 'dmonth', 'dmonth.month', [('Export the orders of the month from your direct store', 31), ('Enter the monthly totals in Direct Income by Month', 32), ('Check the payment fees against the provider statement', 33),
                                                                               ('Send the sales tax collected to the accountant', 34), ('Check the direct share against your goal', 35), ('Plan one change for next month', 36)]),
    CHK('author_copy', 'Author Copy Order', 'printm', 'printm.checked_on', [('Check the stock position of the edition', 0), ('Ask the printer for a quote', 1), ('Check the margin and the minimum price', 2), ('Place the order and the shipping', 4),
                                                                         ('Order a proof copy if the file changed', 5), ('Enter the copies in Stock Movements when they arrive', 28)]),
    CHK('year_end_count', 'Stock Count at Year End', 'stockpos', 'stockpos.counted_on', [('Print the Stock Count Sheet for every edition', 0), ('Count the copies on every shelf and box', 1), ('Write the counted copies next to the sheet', 1),
                                                                                       ('Enter lost or damaged copies in Stock Movements', 2), ('Recount any edition that does not match', 3), ('Write the date in Last counted on', 3)]),
    CHK('reprint_order', 'Reprint Order', 'stockpos', 'stockpos.counted_on', [('Count the copies on hand', 0), ('Read the reorder point and the verdict', 0), ('Ask the printer for a proof copy', 1), ('Approve the proof', 7), ('Place the reprint order', 8),
                                                                           ('Enter the copies in Stock Movements on arrival', 30)]),
    CHK('before_event', 'Before an Event', 'events', 'events.date', [('Book the table and confirm the fee', -60), ('Check the break-even copies and the sales-fall profit', -45), ('Book the travel and any nights', -40), ('Ask the newsletter partner to mention the event', -14),
                                                                   ('Order author copies if the stock is low', -21), ('Confirm the date and the set-up time with the organiser', -3)]),
    CHK('event_packing', 'Packing for an Event', 'events', 'events.date', [('Print the Event Packing Sheet', -3), ('Pack the copies by edition, with spare copies', -2), ('Pack the sign-up sheet, signs and a card reader', -2), ('Pack change, pens and bookmarks', -1),
                                                                         ('Charge the phone and check the payment app', -1), ('Load the car and check the route', 0)]),
    CHK('after_event', 'After an Event', 'events', 'events.date', [('Count the copies left', 1), ('Enter the sales lines in Event Sale Lines', 1), ('Enter the costs and the new subscribers in Events', 2), ('Read the profit per hour and the verdict', 2),
                                                                 ('Return the copies to the stock sheet', 3), ('Thank the organiser or say you will not return', 4)]),
    CHK('offer_review', 'Rights Offer Steps', 'deals', 'deals.offered_on', [('Enter the offer in Rights Deals with status Offer', 0), ('Ask the rights agent for the full terms', 1), ('Run the Rights Offer Review calculator', 2), ('Confirm the terms with your adviser', 5),
                                                                          ('Counter, accept or decline in writing', 7), ('Update the status in Rights Deals', 8)]),
    CHK('new_deal', 'New Rights Deal', 'deals', 'deals.signed_on', [('Change the status to Signed and enter the signing date', 0), ('Enter every payment in Rights Instalments', 1), ('Write the term end date', 1), ('Tell the translator or producer the delivery date', 3),
                                                                   ('Tell the accountant about the new income', 7), ('Set a reminder for the term end', 8)]),
    CHK('payment_chase', 'Rights Payment Chase', 'instal', 'instal.due_date', [('Check that the payment is not yet received', 0), ('Ask the rights agent for the payment date', 3), ('Ask again and copy the accountant', 10), ('Enter the date in Received on when it arrives', 14),
                                                                            ('Tell the accountant the amount received', 15), ('Check the deal still to collect', 16)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('v_orders', 'Assistant: enter the direct orders', 'dmonth', 'dmonth.va_phone', 'Hello {va_name}, please enter the direct orders of {month} in the Direct Orders table. So far the sheet has {orders} orders for that month. {company}'),
    M('v_price', 'Assistant: change a direct price', 'dmargin', 'dmargin.va_phone', 'Hello {va_name}, please change the direct price of {title} ({format}) to {new_price} in the direct store. {company}'),
    M('v_tax', 'Assistant: check the sales tax', 'orders', 'orders.va_phone', 'Hello {va_name}, please check the sales tax on direct orders to {country}. Order {order_id} collected {tax_collected}. {company}'),
    M('v_count', 'Assistant: count the stock', 'stockpos', 'stockpos.va_phone', 'Hello {va_name}, please count the stock of {title} and enter it in Stock Movements. The sheet shows {on_hand} copies. {company}'),
    M('v_pack', 'Assistant: pack copies for an event', 'evlines', 'evlines.va_phone', 'Hello {va_name}, please pack {copies} copies of {title} for {event_name}. {company}'),
    M('v_lines', 'Assistant: enter the event sale lines', 'events', 'events.va_phone', 'Hello {va_name}, please enter the sales lines of {name} in Event Sale Lines. The event was on {date} and {copies_sold} copies were sold. {company}'),
    M('w_free', 'Web developer: free delivery', 'dmonth', 'dmonth.web_phone', 'Hello {web_name}, please add free delivery over {free_over} to the direct store. {company}'),
    M('w_bundle', 'Web developer: add a bundle', 'dmargin', 'dmargin.web_phone', 'Hello {web_name}, please add the bundle {title} to the direct store at {direct_price}. {company}'),
    M('w_fee', 'Web developer: check the payment fee', 'orders', 'orders.web_phone', 'Hello {web_name}, the payment fee on order {order_id} was {payment_fee}. Please check the fee settings of the direct store. {company}'),
    M('a_net', 'Accountant: direct net and sales tax', 'dmonth', 'dmonth.acc_phone', 'Hello {acc_name}, the direct net of {month} is {net} and the sales tax collected is {tax_collected}. {company}'),
    M('a_tax', 'Accountant: how to treat the sales tax', 'dmonth', 'dmonth.acc_phone', 'Hello {acc_name}, please confirm how to treat the {tax_collected} of sales tax collected on direct orders in {month}. {company}'),
    M('a_rights', 'Accountant: a rights payment received', 'instal', 'instal.acc_phone', 'Hello {acc_name}, please note the rights payment of {amount} received for {title}. {company}'),
    M('d_promote', 'Ad specialist: promote an edition direct', 'dmargin', 'dmargin.ad_phone', 'Hello {ad_name}, please promote {title} to the direct store. The net per copy is {net_copy}. {company}'),
    M('n_signing', 'Newsletter partner: mention the signing', 'events', 'events.va_phone', 'Hello {va_name}, please ask our newsletter partner to mention the signing at {name} on {date}. {company}'),
    M('p_quote', 'Printer: quote author copies', 'printm', 'printm.printer_phone', 'Hello {printer_name}, please quote {order_copies} author copies of {title}. {company}'),
    M('p_cost', 'Printer: confirm the print cost', 'printm', 'printm.printer_phone', 'Hello {printer_name}, please confirm the print cost of {title} at {pages} pages. Our last known cost is {print_cost}. {company}'),
    M('p_ship', 'Printer: ship the author copies', 'stockpos', 'stockpos.printer_phone', 'Hello {printer_name}, please ship the author copies of {title} by {need_by}. {company}'),
    M('p_proof', 'Printer: send a proof before the reprint', 'stockpos', 'stockpos.printer_phone', 'Hello {printer_name}, please send a proof copy of {title} before the reprint. {company}'),
    M('p_damage', 'Printer: copies damaged', 'stockpos', 'stockpos.printer_phone', 'Hello {printer_name}, our stock sheet shows {lost} copies of {title} lost or damaged. Please tell us if any left your printer damaged. {company}'),
    M('e_book', 'Event organiser: book a table', 'events', 'events.organiser_phone', 'Hello {organiser_name}, please book a table at {name} on {date}. {company}'),
    M('e_fee', 'Event organiser: confirm the table fee', 'events', 'events.organiser_phone', 'Hello {organiser_name}, please confirm the table fee of {table_fee} for {name}. {company}'),
    M('e_figures', 'Event organiser: send the figures', 'events', 'events.organiser_phone', 'Hello {organiser_name}, please send the visitor and sales figures of {name}. {company}'),
    M('e_thanks', 'Event organiser: thank you, no return', 'evprofit', 'evprofit.organiser_phone', 'Hello {organiser_name}, thank you for {name}. We do not plan to return. {company}'),
    M('r_terms', 'Rights agent: send the terms of an offer', 'deals', 'deals.agent_phone', 'Hello {agent_name}, please send the terms of the offer for {title} in {language}. {company}'),
    M('r_due', 'Rights agent: an instalment is late', 'instal', 'instal.agent_phone', 'Hello {agent_name}, the instalment of {amount} for {title} was due on {due_date}. Please tell us when it was or will be sent. {company}'),
    M('r_share', 'Rights agent: confirm the agent share', 'deals', 'deals.agent_phone', 'Hello {agent_name}, please confirm the agent share of {agent_pct} on the deal for {title}. {company}'),
    M('t_date', 'Translator: confirm the delivery date', 'deals', 'deals.translator_phone', 'Hello {translator_name}, please confirm the delivery date of {title} in {language}. {company}'),
    M('o_share', 'Author: direct share of income', 'dgoal', 'dgoal.author_phone', 'Note for the author: the direct share of income in {month} is {share}, your goal is {target}. {company}'),
    M('o_more', 'Author: direct pays more than a store', 'dmargin', 'dmargin.author_phone', 'Note for the author: {title} pays {difference} more a copy through the direct store than through a store. {company}'),
    M('o_low', 'Author: direct price below the minimum', 'dmargin', 'dmargin.author_phone', 'Reminder for the author: the direct price of {title} is {direct_price}, the minimum is {min_price}. {company}'),
    M('o_stock', 'Author: stock at the reorder point', 'stockpos', 'stockpos.author_phone', 'Reminder for the author: {title} is down to {on_hand} copies, the reorder point is {reorder_point}. {company}'),
    M('o_event', 'Author: an event below the floor', 'evprofit', 'evprofit.author_phone', 'Note for the author: {name} earned {pph} an hour, your floor is {floor}. {company}'),
    M('o_end', 'Author: a rights deal ends', 'deals', 'deals.author_phone', 'Reminder for the author: the rights deal for {title} ends on {term_end}, decide to renew or take back the rights. {company}'),
    M('o_due', 'Author: rights payments due', 'instal', 'instal.author_phone', 'Note for the author: {window_count} rights payments worth {window_amount} fall due in the window you set. {company}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30), dashboard, insights
D12 = 'SUMIFS({range:dmonth.net},%s)' % M12
R12 = 'SUMIFS({range:dmonth.all_revenue},%s)' % M12
kpis = [
    KPI('Direct net, last 12 months', D12, 'money'),
    KPI('Direct net, last full month', 'SUMIFS({range:dmonth.net},{range:dmonth.month},EDATE(%s,-1))' % MS, 'money'),
    KPI('Direct orders, last 12 months', 'SUMIFS({range:dmonth.orders},%s)' % M12, 'int'),
    KPI('Direct copies, last 12 months', 'SUMIFS({range:dmonth.copies},%s)' % M12, 'int'),
    KPI('Average net per direct order', 'IFERROR(%s/SUMIFS({range:dmonth.orders},%s),0)' % (D12, M12), 'money'),
    KPI('Average net per direct copy', 'IFERROR(%s/SUMIFS({range:dmonth.copies},%s),0)' % (D12, M12), 'money'),
    KPI('Direct share of income, last 12 months', 'IFERROR(%s/%s,0)' % (D12, R12), 'pct', alert={"when": "< {set:direct_share_target}", "style": "warn"}),
    KPI('Direct share against the goal (gap)', 'IFERROR(%s/%s,0)-{set:direct_share_target}' % (D12, R12), 'pct', alert={"when": "< 0", "style": "warn"}),
    KPI('Payment fees, last 12 months', 'SUMIFS({range:dmonth.fees},%s)' % M12, 'money'),
    KPI('Payment fees as a share of item sales', 'IFERROR(SUMIFS({range:dmonth.fees},%s)/SUMIFS({range:dmonth.gross},%s),0)' % (M12, M12), 'pct'),
    KPI('Sales tax collected, 12 months', 'SUMIFS({range:dmonth.tax_collected},%s)' % M12, 'money'),
    KPI('Discounts given, last 12 months', 'SUMIFS({range:dmonth.discounts},%s)' % M12, 'money'),
    KPI('Editions where direct pays more', 'COUNTIFS({range:dmargin.verdict},%s)' % v1('Direct pays more'), 'int'),
    KPI('Editions where direct pays less', 'COUNTIFS({range:dmargin.difference},"<0")', 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Average print margin per copy', 'AVERAGE({range:printm.margin})', 'money'),
    KPI('Lowest print margin per copy', 'MIN({range:printm.margin})', 'money'),
    KPI('Print editions below the minimum price', 'COUNTIFS({range:printm.verdict},%s)' % v1('Raise the price'), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Hand-sold copies on hand', 'SUM({range:stockpos.on_hand})', 'int'),
    KPI('Stock value at cost', 'SUM({range:stockpos.value})', 'money'),
    KPI('Editions at or below the reorder point', 'COUNTIFS({range:stockpos.verdict},%s)' % v2('Reprint now'), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Copies lost or damaged, last 12 months', '-SUMIFS({range:stockmoves.copies},{range:stockmoves.move},%s,{range:stockmoves.date},">"&({today}-365))' % MV_LOST, 'int'),
    KPI('Events, last 12 months', 'COUNTIFS(%s)' % E12, 'int'),
    KPI('Event profit, last 12 months', 'SUMIFS({range:events.profit},%s)' % E12, 'money'),
    KPI('Event hours, last 12 months', 'SUMIFS({range:events.hours},%s)' % E12, 'num'),
    KPI('Average event profit per hour', 'IFERROR(SUMIFS({range:events.profit},%s)/SUMIFS({range:events.hours},%s),0)' % (E12, E12), 'money'),
    KPI('Events below the hourly floor', 'COUNTIFS(%s,{range:events.pph},"<"&{set:event_hour_floor})' % E12, 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Event copies sold, last 12 months', 'SUMIFS({range:events.copies_sold},%s)' % E12, 'int'),
    KPI('New subscribers from events', 'SUMIFS({range:events.new_subscribers},%s)' % E12, 'int'),
    KPI('Rights income received, last 12 months', 'SUMIFS({range:instal.amount},{range:instal.received_on},">"&({today}-365))', 'money'),
    KPI('Rights payments due in the next 90 days', 'SUMIFS({range:instal.amount},{range:instal.open},1,{range:instal.due_date},"<="&({today}+{set:window_days}))', 'money'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Direct Sales Dashboard", "kpis": kpis,
    "monthly": {"title": "Direct net, payment fees and sales tax collected by month", "date": "dmonth.month", "series": [
        {"label": "Direct net", "sum": "dmonth.net", "date": "dmonth.month"}, {"label": "Payment fees", "sum": "dmonth.fees", "date": "dmonth.month"}, {"label": "Sales tax collected", "sum": "dmonth.tax_collected", "date": "dmonth.month"}]},
    "breakdowns": [{"title": "Direct net by country", "by": "orders.country", "value": "orders.net_home", "agg": "sum"}, {"title": "Event profit by kind", "by": "events.kind", "value": "events.profit", "agg": "sum"},
                   {"title": "Hand-sold copies on hand by format", "by": "stockpos.format", "value": "stockpos.on_hand", "agg": "sum"}, {"title": "Rights fees by status", "by": "deals.status", "value": "deals.fee", "agg": "sum"}]}
insights = {"filters": [{"label": "Country", "list": "country"}, {"label": "Format", "list": "format"}, {"label": "Event kind", "list": "ekind"}],
    "gauges": [
        {"title": "Direct share of income", "num": AGG('sum', 'dmonth', 'dmonth.net'), "den": AGG('sum', 'dmonth', 'dmonth.all_revenue')},
        {"title": "Editions where direct pays more", "num": AGG('count', 'dmargin', where=[('verdict', '=', v1('Direct pays more'))]), "den": AGG('count', 'dmargin')},
        {"title": "Events at or above the hourly floor", "num": AGG('count', 'evprofit', where=[('pph', '>=', '{set:event_hour_floor}')]), "den": AGG('count', 'evprofit')},
        {"title": "Hand-sold editions above reorder point", "num": AGG('count', 'stockpos', where=[('verdict', '=', v2('Wait'))]), "den": AGG('count', 'stockpos')},
        {"title": "Rights fees received of fees signed", "num": AGG('sum', 'deals', 'deals.received', where=[('status', '<>', S_OFFER)]), "den": AGG('sum', 'deals', 'deals.fee', where=[('status', '<>', S_OFFER)])},
        {"title": "Print editions at the target margin", "num": AGG('count', 'printm', where=[('verdict', '=', v1('Margin holds'))]), "den": AGG('count', 'printm')}],
    "charts": [
        CHART('Direct net per month', 'column', 'month', [AGG('sum', 'dmonth', 'dmonth.net', date='dmonth.month', label='Direct net')]),
        CHART('Direct copies per month', 'column', 'month', [AGG('sum', 'dmonth', 'dmonth.copies', date='dmonth.month', label='Copies')]),
        CHART('Direct share of income per month', 'column', 'month', [AGG('avg', 'dmonth', 'dmonth.share', date='dmonth.month', label='Direct share')]),
        CHART('Direct net by country', 'bar', 'orders.country', [AGG('sum', 'orders', 'orders.net_home', label='Direct net')]),
        CHART('Direct net by format', 'bar', 'orders.format', [AGG('sum', 'orders', 'orders.net_home', label='Direct net')]),
        CHART('Payment fees per month', 'column', 'month', [AGG('sum', 'dmonth', 'dmonth.fees', date='dmonth.month', label='Payment fees')]),
        CHART('Sales tax collected per month', 'column', 'month', [AGG('sum', 'dmonth', 'dmonth.tax_collected', date='dmonth.month', label='Sales tax collected')]),
        CHART('Discounts per month', 'column', 'month', [AGG('sum', 'dmonth', 'dmonth.discounts', date='dmonth.month', label='Discounts')]),
        CHART('Direct net per copy by format', 'bar', 'orders.format', [AGG('avg', 'orders', 'orders.net_per_copy', label='Net per copy')]),
        CHART('Print margin per copy by format', 'bar', 'printm.format', [AGG('avg', 'printm', 'printm.margin', label='Margin per copy')]),
        CHART('Stock on hand by format', 'bar', 'stockpos.format', [AGG('sum', 'stockpos', 'stockpos.on_hand', label='Copies on hand')]),
        CHART('Stock movements by kind', 'bar', 'stockmoves.move', [AGG('count', 'stockmoves', label='Movements')]),
        CHART('Stock movements per month', 'column', 'month', [AGG('count', 'stockmoves', date='stockmoves.date', label='Movements')]),
        CHART('Event profit by kind', 'bar', 'events.kind', [AGG('sum', 'events', 'events.profit', label='Profit')]),
        CHART('Event profit per hour by kind', 'bar', 'events.kind', [AGG('avg', 'events', 'events.pph', label='Profit per hour')]),
        CHART('Event copies sold by kind', 'bar', 'events.kind', [AGG('sum', 'events', 'events.copies_sold', label='Copies sold')]),
        CHART('Event profit per month', 'column', 'month', [AGG('sum', 'events', 'events.profit', date='events.date', label='Profit')]),
        CHART('Event costs by kind', 'bar', 'events.kind', [AGG('sum', 'events', 'events.costs', label='Costs')]),
        CHART('Rights fees by deal kind', 'bar', 'deals.kind', [AGG('sum', 'deals', 'deals.fee', label='Fees')]),
        CHART('Rights fees by status', 'bar', 'deals.status', [AGG('sum', 'deals', 'deals.fee', label='Fees')]),
        CHART('Rights received per month', 'column', 'month', [AGG('sum', 'instal', 'instal.amount', date='instal.received_on', where=[('received_on', '>', 0)], label='Received')]),
        CHART('Rights due per month', 'column', 'month', [AGG('sum', 'instal', 'instal.amount', date='instal.due_date', label='Due')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Direct store margin", "why": "net per item after the payment fee and delivery, against the same item through a store, with the lowest price that holds your net", "where": "Direct Margin by Edition"},
    {"name": "Direct share goal tracker", "why": "the direct share of income against your own goal, the copies to move from stores and the months the goal takes at your own growth", "where": "Direct Share Tracker"},
    {"name": "Print margin and minimum price", "why": "print cost by page count, the royalty a store pays, the margin on a hand-sold copy and the lowest price that holds it", "where": "Print Cost and Margin"},
    {"name": "Hand-sold stock ledger and reorder point", "why": "copies in, sold, given and lost add up to the copies on hand, their value at cost and a reorder point from your own sales", "where": "Stock Position"},
    {"name": "Reprint now or wait verdict", "why": "the reorder point, the copies to order and their cost turn the stock into a clear reprint decision before you run out", "where": "Reorder Point and Reprint"},
    {"name": "Event profit and go-again verdict", "why": "profit and profit per hour of every event against your floor, ranked in your own history, with go again, change it or skip", "where": "Event Profit Check"},
    {"name": "Event go or skip with a sales-fall scenario", "why": "the copies needed to break even and the profit if sales fall 20% before you book a table", "where": "Event Go or Skip"},
    {"name": "Stock to take to an event", "why": "copies by edition from your own sales at that kind of event, plus spare, limited to the copies on hand", "where": "Stock to Take to an Event"},
    {"name": "Rights deal ledger", "why": "fee, agent share, effective income per deal and per year, received and still to collect, kept as status and amounts only", "where": "Rights Deals"},
    {"name": "Rights payments due and expiry watch", "why": "the payments of the next 90 days in date order with a chase verdict, and the deals that end soon with a decide-by date", "where": "Rights Payments Due"},
    {"name": "Direct and event income forecast", "why": "the next 6 months from your own history in Base, Best and Worst scenarios against the monthly figure you want", "where": "Direct and Event Forecast"}]
competitors = [
    {"what": "free royalty tracking templates", "lacks": "stop at store royalties: no direct store net after fees and delivery, no stock ledger and no event profit per hour"},
    {"what": "subscription store dashboards", "lacks": "show sales by day but not the net per copy of your own direct orders, the cost of an author copy or the rights payments you wait for"},
    {"what": "generic budget spreadsheets", "lacks": "list income and costs but have no break-even copies for an event, no reorder point and no go-again verdict"},
    {"what": "single-sheet inventory trackers", "lacks": "count copies but not the value at cost, your own sales rate, the printer lead time or a reprint decision"},
    {"what": "contract and deal lists", "lacks": "keep names and dates but not the effective income per year, the payments due in 90 days or a decide-by date for a term end"}]
guide = [
    'Open Start and type your imprint name and your own numbers in the yellow cells: the direct share goal, payment fee, shipping, postage, the print margin you want and the profit per hour you want at an event.',
    'Check Team, Stores, Countries and Formats once. Team holds the phones for the message links; Countries holds the sales tax percent (an estimate, confirm with your adviser).',
    'Keep Editions up to date: list price, direct price, print or delivery cost, royalty share and pages. Every margin sheet reads these.',
    'Write each direct order in Direct Orders and the monthly totals with your total revenue in Direct Income by Month. The net, fee share and direct share fill in; Direct Share Goal shows 12 months against your goal.',
    'Direct Margin by Edition and Print Cost and Margin show the net per copy, the lowest price and a verdict for every edition. Write the date you checked each price in the yellow column.',
    'Write every order in from the printer, every copy sold at an event, given away or lost in Stock Movements. Stock Position adds them up, values them at cost and says reprint now or wait.',
    'Write each event in Events and its sale lines in Event Sale Lines. Event Profit ranks the events by profit per hour, and Event Kinds shows which kind of event to do more of.',
    'Write each rights deal in Rights Deals and each payment in Rights Instalments, as status and amounts only. Rights Income by Month shows what is due, received and still open.',
    f'Use the {len(tools)} calculators to judge a price, plan a print order, check a count, decide a reprint, book or skip an event, review a rights offer and forecast the next 6 months.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists, tap a message link to send a ready text. One to three books: use the direct and print margin and event profit with a few rows. Figures are estimates.']
listing = {"title": "Author and Self-Publisher Direct Sales, Stock, Events and Rights Excel Template: Direct Margin, Print Margin, Event Profit, Rights Ledger",
    "headline": "Know what your direct store, stock, events and rights deals really earn",
    "tags": ["author template", "direct store margin", "print margin", "book stock ledger", "author events", "book fair profit", "rights deal ledger", "self publishing", "indie author", "excel template", "author business", "reorder point", "author copies"],
    "description": ("Run the four income lines an author handles by hand in one Excel workbook. Built for an independent author who publishes under one or two pen names, sells from a direct store, hand-sells printed copies at events and keeps a few rights deals. "
        "Direct Orders and Direct Income by Month show the net of every order after the payment fee and delivery cost, with sales tax collected kept out of income. Direct Margin by Edition sets each edition against the same edition in a store and gives the lowest price that holds your net. "
        "Direct Share Goal tracks the share of your income that comes from the direct store against your own goal.\n\n"
        "Print Cost and Margin works out the print cost by page count, the royalty a store pays, the cost of an author copy and the margin when you sell it by hand, with the minimum price. Stock Movements and Stock Position keep a ledger of copies in, sold, given and lost, with the value at cost, a reorder point from your own sales and a reprint verdict. "
        "Events and Event Profit give the profit and the profit per hour of every fair, market, talk and signing, rank them in your own history and say go again, go again with changes or skip. Rights Deals, Rights Instalments and Rights Income by Month keep translation, audio and other deals as status and amounts: fee, agent share, effective income per year, payments due in 90 days and term ends.\n\n"
        f"{len(tools)} calculators cover the direct margin, the price solver, the share goal, moving copies to your direct store, print margin, author copy cost, minimum print price, stock count, reorder and reprint, event profit, go or skip, kind ranking, the packing list, the rights ledger, payments due, expiry watch, offer review and a 6-month forecast. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to the assistant, web developer, accountant, printer, event organiser, rights agent, translator and the author.\n\n"
        "This is part seven of the Author and Self-Publisher Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Figures are estimates until the payment arrives, and every price, share, fee and target is your own number: check each store's current terms and confirm tax and contract matters with your adviser. It helps you keep track and does not promise sales."),
    "features": ["Direct store net per order and per copy after fees and delivery", "Direct against store verdict for every edition", "Direct share of income against your own goal", "Print margin, author copy cost and the minimum price",
                 "Hand-sold stock ledger with value at cost and reorder point", "Reprint now or wait verdict", "Event profit per hour with a go-again verdict", "Event go or skip with a sales-fall scenario",
                 "Rights deal ledger with payments due and term ends", f"{len(tools)} calculators for price, stock, event and rights decisions", f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p7', slug='author-publisher-direct', profession='Author and Self-Publisher Business', name='Direct Sales, Stock, Events and Rights',
         tagline='Direct store margin, hand-sold stock, event profit and rights deals', price_usd=29,
         colors={"primary": "#2B3A55", "accent": "#CE7777"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 7, "of": 8, "focus": "Direct sales, stock, events and rights"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'au7.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
