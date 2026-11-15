"""Author and self-publisher suite part 7: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au7_lists import *
import au7_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def BYROLE(role): return 'IFERROR(INDEX({range:team.phone},MATCH(%s,{range:team.role},0))&"","")' % tok('role', role)
def NAMEROLE(role): return 'IFERROR(INDEX({range:team.name},MATCH(%s,{range:team.role},0))&"","")' % tok('role', role)
def PH(key_, label, role): return CA(key_, label, 'text', BYROLE(role), 18)
def NM(key_, label, role): return CA(key_, label, 'text', NAMEROLE(role), 20)
def VA_PH(): return PH('va_phone', 'Assistant phone', 'Virtual assistant')
def VA_NM(): return NM('va_name', 'Assistant name', 'Virtual assistant')
def AU_PH(): return PH('author_phone', 'Author phone', 'Author-publisher')
def WD_PH(): return PH('web_phone', 'Web developer phone', 'Web developer')
def WD_NM(): return NM('web_name', 'Web developer name', 'Web developer')
def AC_PH(): return PH('acc_phone', 'Accountant phone', 'Accountant')
def AC_NM(): return NM('acc_name', 'Accountant name', 'Accountant')
def PR_PH(): return PH('printer_phone', 'Printer phone', 'Printer')
def PR_NM(): return NM('printer_name', 'Printer name', 'Printer')
def EO_PH(): return PH('organiser_phone', 'Event organiser phone', 'Event organiser')
def EO_NM(): return NM('organiser_name', 'Event organiser name', 'Event organiser')
def RA_PH(): return PH('agent_phone', 'Rights agent phone', 'Rights agent')
def RA_NM(): return NM('agent_name', 'Rights agent name', 'Rights agent')
def TR_PH(): return PH('translator_phone', 'Translator phone', 'Translator')
def TR_NM(): return NM('translator_name', 'Translator name', 'Translator')
def AD_PH(): return PH('ad_phone', 'Ad specialist phone', 'Ad specialist')
def AD_NM(): return NM('ad_name', 'Ad specialist name', 'Ad specialist')
def COMPANY_(): return CA('company', 'Imprint', 'text', '{set:company}', 20)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
PRINT_ = ('Paperback', 'Hardcover', 'Large print')
def ISPRINT(col='format'): return 'OR(' + ','.join('{col:%s}=%s' % (col, tok('format', f)) for f in PRINT_) + ')'
MV_IN, MV_SOLD, MV_GIFT, MV_LOST = (tok('move', m) for m in ('Order in', 'Sold at event', 'Gift or review copy', 'Damaged or lost'))
S_OFFER, S_SIGNED, S_DELIV, S_PAID, S_EXP = (tok('dstatus', m) for m in ('Offer', 'Signed', 'Delivered', 'Paid in full', 'Expired'))

settings = [
    S('company', 'Your imprint name', 'text', COMPANY),
    S('direct_share_target', 'Direct share of income you want (your own number)', 'pct', DIRECT_SHARE_TARGET),
    S('payment_fee_pct', 'Payment fee percent (check your provider)', 'pct', PAYMENT_FEE_PCT),
    S('payment_fee_fixed', 'Payment provider fee, fixed part per order', 'money', PAYMENT_FEE_FIXED),
    S('shipping_charge', 'Shipping you charge on a printed copy', 'money', SHIPPING_CHARGE),
    S('postage_cost', 'Postage you pay for a printed copy (your own number)', 'money', 3.2),
    S('min_net_copy', 'Lowest direct net per copy you accept (your own number)', 'money', 2.0),
    S('direct_growth', 'Growth of direct sales per month (your own number)', 'pct', 0.02),
    S('print_margin_target', 'Margin you want on a hand-sold copy (your own number)', 'pct', 0.55),
    S('author_copy_ship', 'Shipping per author copy from the printer', 'money', 0.8),
    S('author_order', 'Usual size of an author copy order, in copies', 'int', 50),
    S('event_hour_floor', 'Lowest profit per hour you accept at an event', 'money', EVENT_PROFIT_PER_HOUR_FLOOR),
    S('sales_cut', 'Fall in event sales for the cautious scenario', 'pct', 0.2),
    S('printer_lead_days', 'Days the printer needs for a reprint', 'int', 21),
    S('safety_stock', 'Safety stock per edition, in copies', 'int', 6),
    S('cover_months', 'Months of hand sales a reprint should cover', 'int', 3),
    S('spare_share', 'Spare copies to pack for an event', 'pct', 0.2),
    S('window_days', 'Days ahead for rights payments due', 'int', 90),
    S('expiry_months', 'Months ahead for rights deals ending', 'int', 24),
    S('renew_min_year', 'Net a year that makes a renewal worth it (your own number)', 'money', 250),
]
assert 3 <= len(settings) <= 20

tables = []
# ---------------------------------------------------------------- 1 team
tables.append(T('team', 'Team', 'The author, assistant, freelancers and service providers',
    'One row per person you work with: role, phone, e-mail and usual rate; the phones feed the message links to the assistant, the printer, the event organiser, the rights agent and the accountant.', [
    C('person_id', 'Person ID', 'text', 10, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 18), LST('team', 'Team', 'team', 15), LST('pay_type', 'Pay type', 'paytype', 12), C('phone', 'Phone', 'text', 18),
    C('email', 'E-mail', 'text', 26), C('rate', 'Usual rate', 'money', 11), C('rate_unit', 'Rate unit', 'text', 22), C('country', 'Country', 'text', 14), C('since', 'Working together since', 'date', 12)],
    D.team_d(), 50))
# ---------------------------------------------------------------- 2 stores
tables.append(T('stores', 'Stores', 'Stores with the typical royalty share and payment delay',
    'One row per store: the share of the price it pays you and the days it takes to pay after month end; typical demo values, check each store\'s current terms.', [
    LST('store', 'Store', 'store', 20, required=True), C('royalty_share', 'Royalty share', 'pct', 12), C('delay_days', 'Payment delay (days)', 'int', 12)], D.stores_d(), 50))
# ---------------------------------------------------------------- 3 countries
tables.append(T('countries', 'Countries', 'Countries with currency and sales tax percent',
    'One row per country you sell to: its currency and the sales tax percent a direct order collects (an estimate, confirm with your adviser); the assistant checks the tax before an order.', [
    LST('country', 'Country', 'country', 18, required=True), LST('currency', 'Currency', 'currency', 18), C('sales_tax_pct', 'Sales tax', 'pct', 10)], D.countries_d(), 50))
# ---------------------------------------------------------------- 4 formats
tables.append(T('formats', 'Formats', 'Formats with the typical royalty share and base cost',
    'One row per format: the typical royalty share and the base cost of making one copy; demo values, check each store\'s current terms.', [
    LST('format', 'Format', 'format', 16, required=True), C('royalty_share', 'Royalty share', 'pct', 12), C('base_cost', 'Base cost per copy', 'money', 12)], D.formats_d(), 50))
# ---------------------------------------------------------------- 5 editions
tables.append(T('editions', 'Editions', 'Editions with list price, direct price and print cost',
    'One row per edition (a title in one format): the list price, the price in your direct store, the print or delivery cost, the royalty share and the pages; the margin sheets read these.', [
    C('edition_id', 'Edition ID', 'text', 10, required=True), C('title_id', 'Title ID', 'text', 9), C('title', 'Title', 'text', 28), LST('format', 'Format', 'format', 12), C('list_price', 'List price', 'money', 10),
    C('direct_price', 'Direct price', 'money', 10), C('unit_cost', 'Unit cost', 'money', 10), C('royalty_share', 'Royalty share', 'pct', 10), C('pages', 'Pages', 'int', 8), C('release_date', 'Release date', 'date', 11),
    LST('status', 'Status', 'estatus', 13)], D.editions_d(), 150, [A('direct_price', '< 3', 'warn')]))
# ---------------------------------------------------------------- 6 direct orders
tables.append(T('orders', 'Direct Orders', 'Direct store orders with fees, delivery and net',
    'One row per direct order (recent rows; older months are in Direct Income by Month): price, discount, shipping, payment fee and delivery cost; the net fills in, sales tax collected is not income.', [
    C('order_id', 'Order ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), LST('country', 'Country', 'country', 16), LST('currency', 'Currency', 'currency', 16), REF('edition_id', 'Edition ID', 'editions.edition_id', 10),
    C('title', 'Title', 'text', 26), LST('format', 'Format', 'format', 12), C('qty', 'Quantity', 'int', 8), C('unit_price', 'Unit price', 'money', 10), C('discount', 'Discount', 'num', 9), C('tax_collected', 'Sales tax collected', 'money', 11),
    C('shipping_charged', 'Shipping charged', 'num', 10), C('payment_fee', 'Payment fee', 'money', 10), C('delivery_cost', 'Delivery cost', 'money', 10), C('rate', 'Rate', 'num', 8),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    CA('net_home', 'Net, home currency', 'money', '({col:qty}*{col:unit_price}-{col:discount}+{col:shipping_charged}-{col:payment_fee})*{col:rate}-{col:delivery_cost}', 12),
    CA('net_per_copy', 'Net per copy', 'money', 'IF({col:qty}>0,{col:net_home}/{col:qty},0)', 10), WD_PH(), WD_NM(), VA_PH(), VA_NM(), COMPANY_()],
    D.orders_d(), 2500, [A('net_home', '< 0', 'bad'), A('payment_fee', '> 1.5', 'warn')]))
# ---------------------------------------------------------------- 7 sales ledger, recent
tables.append(T('ledger', 'Sales Ledger Recent', 'Recent store ledger rows by edition and store',
    'The latest months with sales of each edition from the stores (royalty in your home currency, an estimate until the payment arrives); the margin sheet compares them with the direct store.', [
    C('sale_id', 'Sale ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), REF('edition_id', 'Edition ID', 'editions.edition_id', 10), C('title', 'Title', 'text', 26), LST('format', 'Format', 'format', 12),
    LST('store', 'Store', 'store', 18), C('units', 'Copies', 'int', 8), C('royalty_home', 'Royalty, home currency', 'money', 12),
    CA('royalty_copy', 'Royalty per copy', 'money', 'IF({col:units}>0,{col:royalty_home}/{col:units},0)', 10)], D.ledger_d(), 1500))
# ---------------------------------------------------------------- 8 direct margin by edition
tables.append(T('dmargin', 'Direct Margin by Edition', 'Direct net per copy against the same edition in a store',
    'One row per edition: the direct price less the payment fee and delivery gives the net per copy; it is set against the royalty a store pays, with the lowest price that holds your net and a verdict.', [
    REF('edition_id', 'Edition ID', 'editions.edition_id', 10, required=True), LST('format', 'Format', 'format', 12), C('review_on', 'Price checked on', 'date', 11),
    CA('title', 'Title', 'text', LKT('editions.title', 'editions.edition_id', 'edition_id'), 28),
    CA('list_price', 'List price', 'money', LKN('editions.list_price', 'editions.edition_id', 'edition_id'), 10), CA('direct_price', 'Direct price', 'money', LKN('editions.direct_price', 'editions.edition_id', 'edition_id'), 10),
    CA('shipping_charged', 'Shipping charged', 'money', 'IF(%s,{set:shipping_charge},0)' % ISPRINT(), 10),
    CA('payment_fee', 'Payment fee', 'money', '({col:direct_price}+{col:shipping_charged})*{set:payment_fee_pct}+{set:payment_fee_fixed}', 10),
    CA('delivery_cost', 'Delivery cost', 'money', '%s+IF(%s,{set:postage_cost},0)' % (LKN('editions.unit_cost', 'editions.edition_id', 'edition_id'), ISPRINT()), 10),
    CA('net_copy', 'Direct net per copy', 'money', '{col:direct_price}+{col:shipping_charged}-{col:payment_fee}-{col:delivery_cost}', 11),
    CA('store_royalty', 'Store royalty per copy', 'money', '{col:list_price}*%s-%s' % (LKN('editions.royalty_share', 'editions.edition_id', 'edition_id'), LKN('editions.unit_cost', 'editions.edition_id', 'edition_id')), 11),
    CA('difference', 'Direct minus store', 'money', '{col:net_copy}-{col:store_royalty}', 10),
    CA('min_price', 'Lowest direct price', 'money', '({set:min_net_copy}+{set:payment_fee_fixed}+{col:delivery_cost})/(1-{set:payment_fee_pct})-{col:shipping_charged}', 10),
    CA('new_price', 'Price to set', 'money', 'IF({col:direct_price}<{col:min_price},ROUNDUP({col:min_price},0)-0.01,{col:direct_price})', 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:net_copy}<{set:min_net_copy},%s,IF({col:difference}>=0,%s,%s))' % (v1('Price too low'), v1('Direct pays more'), v1('Store pays more')), 18),
    CA('ledger_royalty', 'Recent ledger royalty per copy', 'money', 'IFERROR(SUMIFS({range:ledger.royalty_home},{range:ledger.edition_id},{col:edition_id})/SUMIFS({range:ledger.units},{range:ledger.edition_id},{col:edition_id}),0)', 12),
    CA('days_since_check', 'Days since price check', 'int', '{today}-{col:review_on}', 10), VA_PH(), VA_NM(), WD_PH(), WD_NM(), AD_PH(), AD_NM(), AU_PH(), COMPANY_()],
    D.dmargin_d(), 150, [A('verdict', '= ' + v1('Price too low'), 'bad'), A('verdict', '= ' + v1('Store pays more'), 'warn'), A('verdict', '= ' + v1('Direct pays more'), 'good')]))
# ---------------------------------------------------------------- 9 direct income by month
tables.append(T('dmonth', 'Direct Income by Month', 'Direct store income by month with the share of all income',
    'One row per month: type or paste the monthly totals of your direct store and your total revenue; the net, the net per order and copy, the fee share and the direct share of income fill in.', [
    C('month', 'Month', 'date', 11, required=True), C('orders', 'Orders', 'int', 8), C('copies', 'Copies', 'int', 8), C('gross', 'Item sales', 'money', 11), C('discounts', 'Discounts', 'money', 10),
    C('shipping_charged', 'Shipping charged', 'money', 10), C('tax_collected', 'Sales tax collected', 'money', 11), C('fees', 'Payment fees', 'money', 10), C('delivery', 'Delivery cost', 'money', 10),
    C('all_revenue', 'All revenue', 'money', 12),
    CA('net', 'Direct net', 'money', '{col:gross}-{col:discounts}+{col:shipping_charged}-{col:fees}-{col:delivery}', 11),
    CA('avg_net_order', 'Net per order', 'money', 'IF({col:orders}>0,{col:net}/{col:orders},0)', 10), CA('net_copy', 'Net per copy', 'money', 'IF({col:copies}>0,{col:net}/{col:copies},0)', 10),
    CA('fee_share', 'Fees as share of item sales', 'pct', 'IF({col:gross}>0,{col:fees}/{col:gross},0)', 11),
    CA('share', 'Direct share of income', 'pct', 'IF({col:all_revenue}>0,{col:net}/{col:all_revenue},0)', 11),
    CA('net_3m', 'Net, 3-month average', 'money', 'AVERAGEIFS({range:dmonth.net},{range:dmonth.month},">"&EDATE({col:month},-3),{range:dmonth.month},"<="&{col:month})', 11),
    CA('free_over', 'Free delivery over', 'money', 'ROUND(IF({col:orders}>0,({col:gross}-{col:discounts}+{col:shipping_charged})/{col:orders},0)*1.25,0)', 10),
    VA_PH(), VA_NM(), WD_PH(), WD_NM(), AC_PH(), AC_NM(), COMPANY_()],
    D.dmonth_d(), 60, [A('share', '< {set:direct_share_target}', 'warn')]))
# ---------------------------------------------------------------- 10 direct share goal
tables.append(T('dgoal', 'Direct Share Goal', 'Direct share of income against your own goal, month by month',
    'One row per month of the last year: the direct net, all revenue and the direct share against your goal on Start; the extra direct net that would reach the goal fills in.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('direct_net', 'Direct net', 'money', 'SUMIFS({range:dmonth.net},{range:dmonth.month},{col:month})', 11), CA('all_revenue', 'All revenue', 'money', 'SUMIFS({range:dmonth.all_revenue},{range:dmonth.month},{col:month})', 11),
    CA('share', 'Direct share', 'pct', 'IF({col:all_revenue}>0,{col:direct_net}/{col:all_revenue},0)', 10), CA('target', 'Your goal', 'pct', '{set:direct_share_target}', 10),
    CA('gap', 'Gap to goal', 'pct', '{col:share}-{col:target}', 10),
    CA('net_needed', 'Extra direct net to reach the goal', 'money', 'MAX(0,{col:target}/(1-{col:target})*({col:all_revenue}-{col:direct_net})-{col:direct_net})', 13),
    CA('status', 'Status', 'text', 'IF({col:share}>={col:target},%s,%s)' % (v1('On track'), v1('Behind')), 12), AU_PH(), COMPANY_()],
    D.dgoal_d(), 50, [A('status', '= ' + v1('Behind'), 'warn'), A('status', '= ' + v1('On track'), 'good')]))
# ---------------------------------------------------------------- 11 print cost and margin
tables.append(T('printm', 'Print Cost and Margin', 'Print cost, hand-sold margin and minimum price by edition',
    'One row per printed edition: print cost by page count, the royalty a store pays, the author copy cost, the margin when you sell by hand and the lowest price that holds it.', [
    REF('edition_id', 'Edition ID', 'editions.edition_id', 10, required=True), LST('format', 'Format', 'pformat', 12), C('checked_on', 'Print cost checked on', 'date', 11),
    CA('title', 'Title', 'text', LKT('editions.title', 'editions.edition_id', 'edition_id'), 28), CA('pages', 'Pages', 'int', LKN('editions.pages', 'editions.edition_id', 'edition_id'), 8),
    CA('print_cost', 'Print cost', 'money', LKN('editions.unit_cost', 'editions.edition_id', 'edition_id'), 10), CA('list_price', 'List price', 'money', LKN('editions.list_price', 'editions.edition_id', 'edition_id'), 10),
    CA('royalty_copy', 'Store royalty per copy', 'money', '{col:list_price}*%s-{col:print_cost}' % LKN('editions.royalty_share', 'editions.edition_id', 'edition_id'), 11),
    CA('copy_cost', 'Author copy cost with shipping', 'money', '{col:print_cost}+{set:author_copy_ship}', 11), CA('margin', 'Margin per hand-sold copy', 'money', '{col:list_price}-{col:copy_cost}', 11),
    CA('margin_pct', 'Margin percent', 'pct', 'IF({col:list_price}>0,{col:margin}/{col:list_price},0)', 10),
    CA('min_price', 'Minimum price', 'money', '{col:copy_cost}/(1-{set:print_margin_target})', 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:margin_pct}>={set:print_margin_target},%s,%s)' % (v1('Margin holds'), v1('Raise the price')), 16),
    CA('order_copies', 'Usual order, copies', 'int', '{set:author_order}', 9), CA('order_cost', 'Cost of a usual order', 'money', '{col:order_copies}*{col:copy_cost}', 11), PR_PH(), PR_NM(), VA_PH(), AU_PH(), COMPANY_()],
    D.printm_d(), 100, [A('verdict', '= ' + v1('Raise the price'), 'warn'), A('verdict', '= ' + v1('Margin holds'), 'good')]))
# ---------------------------------------------------------------- 12 stock movements
tables.append(T('stockmoves', 'Stock Movements', 'Copies in, sold, given and lost, one row per movement',
    'One row per movement of the copies you hold: an order in from the printer is plus, copies sold at an event, given away or lost are minus; Stock Position adds them up.', [
    C('stock_id', 'Stock ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), REF('edition_id', 'Edition ID', 'editions.edition_id', 10), C('title', 'Title', 'text', 26), LST('format', 'Format', 'pformat', 12),
    LST('move', 'Move', 'move', 18), C('copies', 'Copies (minus is out)', 'int', 11), C('unit_cost', 'Unit cost', 'money', 10),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11), CA('value', 'Value at cost', 'money', '{col:copies}*{col:unit_cost}', 11), VA_PH(), VA_NM(), COMPANY_()],
    D.stockmoves_d(), 600, [A('move', '= ' + tok('move', 'Damaged or lost'), 'warn')]))
# ---------------------------------------------------------------- 13 stock position
def SMV(move, extra=''): return 'SUMIFS({range:stockmoves.copies},{range:stockmoves.edition_id},{col:edition_id},{range:stockmoves.move},%s%s)' % (move, extra)
tables.append(T('stockpos', 'Stock Position', 'Copies on hand, value, reorder point and reprint verdict',
    'One row per edition you hold: copies in, sold at events, given and lost add up to the copies on hand; the value at cost, your own sales rate, the reorder point and a reprint verdict fill in.', [
    REF('edition_id', 'Edition ID', 'editions.edition_id', 10, required=True), LST('format', 'Format', 'pformat', 12), C('counted_on', 'Last counted on', 'date', 11),
    CA('title', 'Title', 'text', LKT('editions.title', 'editions.edition_id', 'edition_id'), 28),
    CA('copies_in', 'Copies in', 'int', SMV(MV_IN), 8), CA('sold', 'Sold at events', 'int', '-' + SMV(MV_SOLD), 9), CA('given', 'Given away', 'int', '-' + SMV(MV_GIFT), 9), CA('lost', 'Lost or damaged', 'int', '-' + SMV(MV_LOST), 9),
    CA('on_hand', 'On hand', 'int', 'SUMIFS({range:stockmoves.copies},{range:stockmoves.edition_id},{col:edition_id})', 8),
    CA('unit_cost', 'Unit cost', 'money', LKN('editions.unit_cost', 'editions.edition_id', 'edition_id'), 10), CA('value', 'Value at cost', 'money', '{col:on_hand}*{col:unit_cost}', 11),
    CA('sold_12m', 'Sold, last 12 months', 'int', '-' + SMV(MV_SOLD, ',{range:stockmoves.date},">"&({today}-365)'), 10), CA('per_month', 'Copies a month', 'num', '{col:sold_12m}/12', 9),
    CA('reorder_point', 'Reorder point', 'int', 'ROUNDUP({col:per_month}*{set:printer_lead_days}/30+{set:safety_stock},0)', 9),
    CA('to_order', 'Copies to order', 'int', 'IF({col:on_hand}<={col:reorder_point},MAX(0,ROUNDUP({col:per_month}*{set:cover_months}+{set:safety_stock}-{col:on_hand},0)),0)', 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:on_hand}<={col:reorder_point},%s,%s)' % (v2('Reprint now'), v2('Wait')), 14),
    CA('need_by', 'Order by', 'date', '{today}', 11),
    CA('days_since_count', 'Days since count', 'int', '{today}-{col:counted_on}', 9),
    CA('sold_rank', 'Rank by sales', 'int', 'COUNTIFS({range:stockpos.sold_12m},">"&{col:sold_12m})+COUNTIFS({range:stockpos.sold_12m},{col:sold_12m},{range:stockpos.edition_id},"<"&{col:edition_id})+1', 9),
    PR_PH(), PR_NM(), VA_PH(), VA_NM(), AU_PH(), COMPANY_()],
    D.stockpos_d(), 60, [A('verdict', '= ' + v2('Reprint now'), 'bad'), A('verdict', '= ' + v2('Wait'), 'good')]))
# ---------------------------------------------------------------- 14 events
tables.append(T('events', 'Events', 'Events and fairs with costs, sales and profit per hour',
    'One row per event, fair, talk or signing: hours, table fee, travel, nights, copies taken and sold, sales, cost of the copies sold and new subscribers; the costs, profit and profit per hour fill in.', [
    C('event_id', 'Event ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('name', 'Event', 'text', 26), LST('kind', 'Kind', 'ekind', 17), C('city', 'City', 'text', 14), C('hours', 'Hours', 'num', 7),
    C('table_fee', 'Table fee', 'money', 10), C('travel_cost', 'Travel', 'money', 9), C('nights', 'Nights', 'int', 7), C('lodging_cost', 'Lodging', 'num', 9), C('copies_taken', 'Copies taken', 'int', 9),
    C('copies_sold', 'Copies sold', 'int', 9), C('sales', 'Sales', 'money', 10), C('cost_of_copies', 'Cost of copies sold', 'money', 11), C('new_subscribers', 'New subscribers', 'int', 10),
    CA('costs', 'Total costs', 'money', '{col:table_fee}+{col:travel_cost}+{col:lodging_cost}+{col:cost_of_copies}', 10), CA('profit', 'Profit', 'money', '{col:sales}-{col:costs}', 10),
    CA('pph', 'Profit per hour', 'money', 'IF({col:hours}>0,{col:profit}/{col:hours},0)', 10),
    EO_PH(), EO_NM(), VA_PH(), VA_NM(), AU_PH(), COMPANY_()],
    D.events_d(), 100, [A('profit', '< 0', 'bad'), A('pph', '< {set:event_hour_floor}', 'warn')]))
# ---------------------------------------------------------------- 15 event sale lines
tables.append(T('evlines', 'Event Sale Lines', 'Copies sold at each event by edition and price',
    'One row per edition sold at an event: copies and the price; the event name and kind and the line total fill in, and the packing plan reads these lines.', [
    C('line_id', 'Line ID', 'text', 9, required=True), REF('event_id', 'Event ID', 'events.event_id', 9), C('date', 'Date', 'date', 11), REF('edition_id', 'Edition ID', 'editions.edition_id', 10), C('title', 'Title', 'text', 26),
    LST('format', 'Format', 'format', 12), C('copies', 'Copies', 'int', 8), C('price', 'Price', 'money', 9),
    CA('event_name', 'Event', 'text', LKT('events.name', 'events.event_id', 'event_id'), 26), CA('kind', 'Kind', 'text', LKT('events.kind', 'events.event_id', 'event_id'), 17),
    CA('line_total', 'Line total', 'money', '{col:copies}*{col:price}', 10), VA_PH(), VA_NM(), COMPANY_()], D.evlines_d(), 400))
# ---------------------------------------------------------------- 16 event profit
tables.append(T('evprofit', 'Event Profit', 'Each event ranked by profit per hour with a go-again verdict',
    'One row per event: sales, costs, profit and profit per hour against your floor, copies to break even, the profit if sales fall, a verdict and the rank in your own history.', [
    REF('event_id', 'Event ID', 'events.event_id', 9, required=True),
    CA('name', 'Event', 'text', LKT('events.name', 'events.event_id', 'event_id'), 26), CA('kind', 'Kind', 'text', LKT('events.kind', 'events.event_id', 'event_id'), 17), CA('date', 'Date', 'date', LKD('events.date', 'events.event_id', 'event_id'), 11),
    CA('hours', 'Hours', 'num', LKN('events.hours', 'events.event_id', 'event_id'), 7), CA('sales', 'Sales', 'money', LKN('events.sales', 'events.event_id', 'event_id'), 10),
    CA('costs', 'Costs', 'money', LKN('events.costs', 'events.event_id', 'event_id'), 10), CA('profit', 'Profit', 'money', LKN('events.profit', 'events.event_id', 'event_id'), 10),
    CA('pph', 'Profit per hour', 'money', LKN('events.pph', 'events.event_id', 'event_id'), 10),
    CA('sell_through', 'Sell-through', 'pct', 'IFERROR(%s/%s,0)' % (LKN('events.copies_sold', 'events.event_id', 'event_id'), LKN('events.copies_taken', 'events.event_id', 'event_id')), 10),
    CA('subscribers', 'New subscribers', 'int', LKN('events.new_subscribers', 'events.event_id', 'event_id'), 10),
    CA('fixed_costs', 'Fixed costs', 'money', '%s+%s+%s' % (LKN('events.table_fee', 'events.event_id', 'event_id'), LKN('events.travel_cost', 'events.event_id', 'event_id'), LKN('events.lodging_cost', 'events.event_id', 'event_id')), 10),
    CA('margin_copy', 'Margin per copy sold', 'money', 'IFERROR((%s-%s)/%s,0)' % (LKN('events.sales', 'events.event_id', 'event_id'), LKN('events.cost_of_copies', 'events.event_id', 'event_id'), LKN('events.copies_sold', 'events.event_id', 'event_id')), 10),
    CA('break_even', 'Copies to break even', 'int', 'IF({col:margin_copy}>0,ROUNDUP({col:fixed_costs}/{col:margin_copy},0),0)', 10),
    CA('profit_cut', 'Profit if sales fall', 'money', '({col:sales}-%s)*(1-{set:sales_cut})-{col:fixed_costs}' % LKN('events.cost_of_copies', 'events.event_id', 'event_id'), 11),
    CA('rank', 'Rank by profit per hour', 'int', 'COUNTIFS({range:evprofit.pph},">"&{col:pph})+1', 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:pph}>={set:event_hour_floor},%s,IF({col:profit}>0,%s,%s))' % (v3('Go again'), v3('Go again with changes'), v3('Skip')), 20),
    CA('floor', 'Your floor per hour', 'money', '{set:event_hour_floor}', 10), EO_PH(), EO_NM(), VA_PH(), AU_PH(), COMPANY_()],
    D.evprofit_d(), 100, [A('verdict', '= ' + v3('Skip'), 'bad'), A('verdict', '= ' + v3('Go again with changes'), 'warn'), A('verdict', '= ' + v3('Go again'), 'good')]))
# ---------------------------------------------------------------- 17 event kinds
tables.append(T('evkinds', 'Event Kinds', 'Profit per hour by kind of event',
    'One row per kind of event and period (all history, last 12 months, before that): events, profit, hours and profit per hour against your floor, with a verdict to do more or change or drop.', [
    LST('kind', 'Kind', 'ekind', 20, required=True), LST('period', 'Period', 'period', 15),
    CA('from_date', 'From', 'date', 'IF({col:period}=%s,{today}-365,0)' % tok('period', 'Last 12 months'), 10), CA('to_date', 'To', 'date', 'IF({col:period}=%s,{today}-365,{today})' % tok('period', 'Before that'), 10),
    CA('events', 'Events', 'int', 'COUNTIFS({range:events.kind},{col:kind},{range:events.date},">"&{col:from_date},{range:events.date},"<="&{col:to_date})', 8),
    CA('profit', 'Profit', 'money', 'SUMIFS({range:events.profit},{range:events.kind},{col:kind},{range:events.date},">"&{col:from_date},{range:events.date},"<="&{col:to_date})', 11),
    CA('hours', 'Hours', 'num', 'SUMIFS({range:events.hours},{range:events.kind},{col:kind},{range:events.date},">"&{col:from_date},{range:events.date},"<="&{col:to_date})', 8), CA('pph', 'Profit per hour', 'money', 'IF({col:hours}>0,{col:profit}/{col:hours},0)', 10),
    CA('copies_sold', 'Copies sold', 'int', 'SUMIFS({range:events.copies_sold},{range:events.kind},{col:kind},{range:events.date},">"&{col:from_date},{range:events.date},"<="&{col:to_date})', 9),
    CA('costs', 'Costs', 'money', 'SUMIFS({range:events.costs},{range:events.kind},{col:kind},{range:events.date},">"&{col:from_date},{range:events.date},"<="&{col:to_date})', 11),
    CA('rank', 'Rank by profit per hour (all history)', 'int', 'IF({col:period}=%s,COUNTIFS({range:evkinds.pph},">"&{col:pph},{range:evkinds.period},{col:period})+1,0)' % tok('period', 'All history'), 11),
    CA('verdict', 'Verdict', 'text', 'IF({col:pph}>={set:event_hour_floor},%s,%s)' % (v3('Do more'), v3('Change or drop')), 16)],
    D.evkinds_d(), 50, [A('verdict', '= ' + v3('Change or drop'), 'warn'), A('verdict', '= ' + v3('Do more'), 'good')]))
# ---------------------------------------------------------------- 18 rights deals
def INSTSUM(extra=''): return 'SUMIFS({range:instal.amount},{range:instal.deal_id},{col:deal_id}%s)' % extra
tables.append(T('deals', 'Rights Deals', 'Rights deal ledger: translation, audio and other licences',
    'One row per deal, as status and amounts only: fee, agent share and term; what is received, still to collect, the income per year and a verdict fill in. Confirm terms with your adviser.', [
    C('deal_id', 'Deal ID', 'text', 9, required=True), C('title', 'Title', 'text', 26), LST('kind', 'Kind', 'dkind', 14), C('language', 'Language', 'text', 12), C('territory', 'Territory', 'text', 26),
    C('offered_on', 'Offered on', 'date', 11), C('signed_on', 'Signed on', 'date', 11), C('term_years', 'Term (years)', 'int', 8), C('term_end', 'Term ends', 'date', 11), C('fee', 'Fee', 'money', 10),
    C('agent_pct', 'Agent share', 'pct', 9), LST('status', 'Status', 'dstatus', 13),
    CA('received', 'Received', 'money', INSTSUM(',{range:instal.received_on},">0"'), 10),
    CA('to_collect', 'Still to collect', 'money', 'IF(OR({col:status}=%s,{col:status}=%s),MAX(0,{col:fee}-{col:received}),0)' % (S_SIGNED, S_DELIV), 11),
    CA('agent_fee', 'Agent share, amount', 'money', '{col:fee}*{col:agent_pct}', 10), CA('net_fee', 'Effective income', 'money', '{col:fee}-{col:agent_fee}', 11),
    CA('per_year', 'Effective income per year', 'money', 'IF({col:term_years}>0,{col:net_fee}/{col:term_years},0)', 11),
    CA('days_to_end', 'Days to term end', 'int', 'IF({col:term_end}>0,{col:term_end}-{today},"")', 9),
    CA('ending_soon', 'Ends within the window', 'int', 'IF(AND({col:term_end}>0,{col:term_end}>={today},{col:term_end}<=EDATE({today},{set:expiry_months})),1,0)', 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:status}=%s,%s,IF(OR({col:status}=%s,{col:status}=%s),%s,%s))' % (S_OFFER, v2('Wait'), S_PAID, S_EXP, v2('Closed'), v2('Collect')), 12),
    RA_PH(), RA_NM(), TR_PH(), TR_NM(), AC_PH(), AU_PH(), COMPANY_()],
    D.deals_d(), 60, [A('status', '= ' + S_EXP, 'bad'), A('status', '= ' + S_OFFER, 'warn'), A('verdict', '= ' + v2('Collect'), 'good')]))
# ---------------------------------------------------------------- 19 rights instalments
tables.append(T('instal', 'Rights Instalments', 'Payments due and received for each rights deal',
    'One row per payment of a deal: due date, amount and the date it arrived; the days to due, a check and the order to chase fill in, and the payments due in your window are counted.', [
    C('instalment_id', 'Instalment ID', 'text', 10, required=True), REF('deal_id', 'Deal ID', 'deals.deal_id', 9), C('due_date', 'Due date', 'date', 11), C('amount', 'Amount', 'money', 10), C('received_on', 'Received on', 'date', 11),
    CA('title', 'Title', 'text', LKT('deals.title', 'deals.deal_id', 'deal_id'), 26), CA('kind', 'Kind', 'text', LKT('deals.kind', 'deals.deal_id', 'deal_id'), 14), CA('language', 'Language', 'text', LKT('deals.language', 'deals.deal_id', 'deal_id'), 12),
    CA('open', 'Open', 'int', 'IF({col:received_on}>0,0,1)', 6), CA('days_to_due', 'Days to due', 'int', 'IF({col:open}=1,{col:due_date}-{today},"")', 8),
    CA('check', 'Check', 'text', 'IF({col:open}=0,%s,IF({col:due_date}<{today},%s,IF({col:due_date}-{today}<=30,%s,IF({col:due_date}-{today}<={set:window_days},%s,%s))))' % (v4('Received'), v4('Overdue'), v4('Due in 30 days'), v4('Due soon'), v4('Later')), 15),
    CA('open_key', 'Order key', 'num', 'IF({col:open}=1,{col:due_date}+VALUE(RIGHT({col:instalment_id},3))/1000,99999)', 9),
    CA('order_no', 'Order to chase', 'int', 'IF({col:open}=1,COUNTIFS({range:instal.open_key},"<"&{col:open_key})+1,0)', 8),
    CA('window_count', 'Payments due in the window', 'int', 'COUNTIFS({range:instal.open},1,{range:instal.due_date},"<="&({today}+{set:window_days}))', 10),
    CA('window_amount', 'Amount due in the window', 'money', 'SUMIFS({range:instal.amount},{range:instal.open},1,{range:instal.due_date},"<="&({today}+{set:window_days}))', 11),
    RA_PH(), RA_NM(), AC_PH(), AC_NM(), AU_PH(), COMPANY_()],
    D.instal_d(), 80, [A('check', '= ' + v4('Overdue'), 'bad'), A('check', '= ' + v4('Due in 30 days'), 'warn'), A('check', '= ' + v4('Received'), 'good')]))
# ---------------------------------------------------------------- 20 rights income by month
tables.append(T('rmonth', 'Rights Income by Month', 'Rights payments due, received and open by month',
    'One row per month: the payments due, the amount received, what is still open and the deals whose term ends; a month with open money is the month to chase.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('due', 'Due', 'money', 'SUMIFS({range:instal.amount},{range:instal.due_date},">="&{col:month},{range:instal.due_date},"<"&EDATE({col:month},1))', 11),
    CA('received', 'Received', 'money', 'SUMIFS({range:instal.amount},{range:instal.received_on},">="&{col:month},{range:instal.received_on},"<"&EDATE({col:month},1))', 11),
    CA('open', 'Open', 'money', '{col:due}-SUMIFS({range:instal.amount},{range:instal.due_date},">="&{col:month},{range:instal.due_date},"<"&EDATE({col:month},1),{range:instal.received_on},">0")', 11),
    CA('expiring', 'Deals ending', 'int', 'COUNTIFS({range:deals.term_end},">="&{col:month},{range:deals.term_end},"<"&EDATE({col:month},1))', 9),
    CA('signed', 'Deals signed', 'int', 'COUNTIFS({range:deals.signed_on},">="&{col:month},{range:deals.signed_on},"<"&EDATE({col:month},1))', 9)],
    D.rmonth_d(), 50, [A('open', '> 0', 'warn')]))
assert len(tables) == 20, len(tables)
