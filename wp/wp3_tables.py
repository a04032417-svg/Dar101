"""Wedding suite part 3: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp3_lists import *
import wp3_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def R(t, c_): return '{range:%s.%s}' % (t, c_)
def CPL(): return CA('couple', 'Couple', 'text', '{set:couple}', 20)
def VT(n): return tok('vname', n)
def SC(key_, label, cond, phone): return CA(key_, label, 'text', 'IF(%s,%s,"")' % (cond, phone if phone.startswith('{') else '"%s"' % phone), 18)
def RK(rng, col, key_, tie=True, desc=True):
    """unique rank of {col:col} inside the range of its own table (1 = largest when desc)"""
    return None


YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
V = lambda label: v(label)
BOOKED = tok('vstatus', 'Booked'); VQR = tok('vstatus', 'Quote received'); VSL = tok('vstatus', 'Shortlisted')
QBOOK = tok('qstatus', 'Booked'); QDECL = tok('qstatus', 'Declined'); QQR = tok('qstatus', 'Quote received'); QSL = tok('qstatus', 'Shortlisted')
DEP = tok('paykind', 'Deposit'); FB = tok('paykind', 'Final balance'); PAID = tok('paystatus', 'Paid')
PREP = tok('block', 'Preparation'); CLOSE = tok('block', 'Close')
K_INC = tok('ckind', 'Included'); K_EXC = tok('ckind', 'Not included'); K_CAN = tok('ckind', 'Cancellation terms'); K_FHC = tok('ckind', 'Final headcount date')
K_FPD = tok('ckind', 'Final payment date'); K_ARR = tok('ckind', 'Arrival and set-up'); K_OT = tok('ckind', 'Overtime rate'); K_INS = tok('ckind', 'Insurance or permit')
OPT_A, OPT_B, OPT_C = tok('option', 'Option A'), tok('option', 'Option B'), tok('option', 'Option C')

settings = [
    S('couple', 'Your names as the couple', 'text', COUPLE),
    S('wedding_day', 'Wedding day', 'date', iso(WEDDING_DAY)),
    S('headcount', 'Headcount for meals and costing, from your guest list', 'int', 118),
    S('expiry_days', 'Days left that count as a quote about to expire', 'int', 14),
    S('stale_days', 'Days without contact before you chase a vendor', 'int', 30),
    S('meal_hours', 'Hours on site before a vendor gets a meal, typical, edit', 'int', 5),
    S('overtime_hours', 'Hours the day might run over, your estimate', 'int', 1),
    S('venue_end_hour', 'Venue hours end, 24-hour clock, 23.5 is 23:30', 'num', 23.5),
    S('refund_days', 'Days before the wedding after which payments may be lost', 'int', 60),
    S('red_days', 'Days left for a red contract date, your own number', 'int', 14),
    S('amber_days', 'Days left for an amber contract date, your own number', 'int', 30),
    S('setup_buffer', 'Minutes between two vendors in one place, typical, edit', 'int', 10),
    S('slow_days', 'Average days to reply that count as slow, your own number', 'int', 6),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 vendors ------------------------------------------------------------------
def LKC(kind): return 'IFERROR(INDEX({range:contracts.detail},MATCH({col:vendor_id}&"|"&%s,{range:contracts.ckey},0))&"","")' % kind
def LKCD(kind): return 'IFERROR(IF(INDEX({range:contracts.item_date},MATCH({col:vendor_id}&"|"&%s,{range:contracts.ckey},0))=0,"",INDEX({range:contracts.item_date},MATCH({col:vendor_id}&"|"&%s,{range:contracts.ckey},0))),"")' % (kind, kind)
def VPH(k, label, name): return CA(k, label, 'text', 'IF({col:vendor}=%s,{col:phone},"")' % VT(name), 18)
RUNM = 'MATCH({col:vendor_id},{range:run.vendor_id},0)'
tables.append(T('vendors', 'Vendors', 'Vendors', 'One row per vendor slot (one job; its alternatives are on Quotes): status, booked date, contract total and lead time. Days since contact, terms found and arrival fill in.', [
    C('vendor_id', 'Vendor ID', 'text', 9, required=True), LST('vendor', 'Vendor', 'vname', 22), LST('category', 'Category', 'vcat', 24), C('contact', 'Contact', 'text', 22), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
    LST('status', 'Status', 'vstatus', 14), C('booked_on', 'Booked on', 'date', 11), C('contract_total', 'Contract total', 'money', 12), C('lead_months', 'Lead months, typical, edit', 'int', 10), LST('payer', 'Payer', 'payer', 16),
    C('last_contact', 'Last contact', 'date', 11), C('follow_up', 'Follow up', 'date', 11), C('confirmed', 'Confirmed for the day', 'bool', 10),
    CA('days_since', 'Days since contact', 'int', 'IF({col:last_contact}="","",{today}-{col:last_contact})', 9),
    CA('booked', 'Booked', 'int', 'IF({col:status}=%s,1,0)' % BOOKED, 8),
    CA('included', 'What is included', 'text', LKC(K_INC), 30), CA('excluded', 'What is not included', 'text', LKC(K_EXC), 30), CA('cancel_terms', 'Cancellation terms', 'text', LKC(K_CAN), 30),
    CA('final_pay_date', 'Final payment date', 'date', LKCD(K_FPD), 11), CA('headcount_date', 'Final headcount date', 'date', LKCD(K_FHC), 11), CA('arrival_note', 'Arrival and set-up', 'text', LKC(K_ARR), 30),
    CA('ot_rate', 'Overtime rate per hour', 'money', 'IFERROR(INDEX({range:contracts.amount},MATCH({col:vendor_id}&"|"&%s,{range:contracts.ckey},0)),0)' % K_OT, 11),
    CA('terms_needed', 'Terms needed', 'int', '{col:booked}*4', 8),
    CA('core_found', 'Core terms found', 'int', 'IF({col:booked}=1,(LEN({col:included})>0)+(LEN({col:cancel_terms})>0)+({col:final_pay_date}<>""),0)', 8),
    CA('terms_found', 'Terms found', 'int', '{col:core_found}+IF({col:booked}=1,IF(LEN({col:arrival_note})>0,1,0),0)', 8),
    CA('missing_cancel', 'Missing a cancellation term', 'int', 'IF({col:booked}=1,IF(LEN({col:cancel_terms})=0,1,0),0)', 8),
    CA('missing_final', 'Missing a final payment date', 'int', 'IF({col:booked}=1,IF({col:final_pay_date}="",1,0),0)', 8),
    CA('arrival', 'First arrival', 'time', 'IFERROR(INDEX({range:run.start},%s),"")' % RUNM, 9),
    CA('meeting_point', 'Meeting point', 'text', 'IFERROR(INDEX({range:run.place},%s)&"","")' % RUNM, 12),
    CA('first_task', 'First task on the day', 'text', 'IFERROR(INDEX({range:run.what},%s)&"","")' % RUNM, 30),
    CA('steps', 'Steps in the run of show', 'int', 'COUNTIFS({range:run.vendor_id},{col:vendor_id})', 8),
    CA('deposit_due', 'Deposit', 'money', 'SUMIFS({range:schedule.amount_due},{range:schedule.vendor_id},{col:vendor_id},{range:schedule.kind},%s)' % DEP, 11),
    CA('paid_so_far', 'Paid so far', 'money', 'SUMIFS({range:schedule.amount_paid},{range:schedule.vendor_id},{col:vendor_id})', 11),
    CA('still_due', 'Still due', 'money', 'SUMIFS({range:schedule.amount_due},{range:schedule.vendor_id},{col:vendor_id})-{col:paid_so_far}', 11),
    CA('coordinator', 'Day-of coordinator', 'text', 'IFERROR(INDEX({range:vendors.contact},MATCH(%s,{range:vendors.vendor},0))&"","")' % VT('Day-of coordinator'), 20),
    ], D.vendors_d(), 40, [A('status', '= ' + BOOKED, 'good'), A('days_since', '> {set:stale_days}', 'warn')]))

# 2 quotes -------------------------------------------------------------------
OPENQ = 'OR({col:status}=%s,{col:status}=%s)' % (QQR, QSL)
QPH = lambda k, label, name, cond: CA(k, label, 'text', 'IF(AND({col:vendor}=%s,%s),{col:vendor_phone},"")' % (VT(name), cond), 18)
tables.append(T('quotes', 'Quotes', 'Quotes', 'Up to three options per vendor slot with every extra: service charge, taxes, delivery, overtime, travel and a tip. True total and days to expiry fill in by themselves.', [
    C('quote_id', 'Quote ID', 'text', 9, required=True), C('vendor_id', 'Vendor ID', 'text', 9), LST('vendor', 'Vendor', 'vname', 22), LST('category', 'Category', 'vcat', 24), LST('option', 'Option', 'option', 10),
    LST('status', 'Status', 'qstatus', 14), C('quote_date', 'Quote date', 'date', 11), C('base_price', 'Base price', 'money', 11), C('service_pct', 'Service charge', 'pct', 10), C('tax_pct', 'Taxes', 'pct', 9),
    C('delivery', 'Delivery', 'int', 10), C('overtime', 'Overtime, estimate', 'int', 10), C('travel', 'Travel', 'int', 9), C('tip_pct', 'Expected tip, optional', 'pct', 10),
    C('response_days', 'Days to reply', 'int', 9), C('fit', 'Fit, 1 to 5', 'int', 9), C('response', 'Response, 1 to 5', 'int', 9), C('reviews', 'Reviews, 1 to 5', 'int', 9), C('chosen', 'Chosen', 'bool', 9),
    C('included', 'Included', 'text', 26), C('excluded', 'Excluded', 'text', 26), C('valid_until', 'Valid until', 'date', 11),
    CA('service_amt', 'Service charge amount', 'money', 'ROUND({col:base_price}*{col:service_pct},0)', 11),
    CA('tax_amt', 'Taxes amount', 'money', 'ROUND(({col:base_price}+{col:service_amt})*{col:tax_pct},0)', 11),
    CA('tip_amt', 'Expected tip amount', 'money', 'ROUND({col:base_price}*{col:tip_pct},0)', 11),
    CA('true_total', 'True total', 'money', '{col:base_price}+{col:service_amt}+{col:tax_amt}+{col:delivery}+{col:overtime}+{col:travel}+{col:tip_amt}', 11),
    CA('extras', 'Extras over the base price', 'money', '{col:true_total}-{col:base_price}', 11),
    CA('open_flag', 'Open', 'int', 'IF(%s,1,0)' % OPENQ, 7),
    CA('days_to_expiry', 'Days to expiry', 'int', 'IF({col:open_flag}=1,{col:valid_until}-{today},"")', 9),
    CA('open_days', 'Days left, not expired', 'int', 'IF({col:open_flag}=1,IF({col:days_to_expiry}>=0,{col:days_to_expiry},""),"")', 9),
    CA('valid_n', 'Open and valid', 'int', 'IF({col:open_flag}=1,IF({col:days_to_expiry}>=0,1,0),0)', 7),
    CA('vendor_phone', 'Vendor phone', 'text', LKT('vendors.phone', 'vendors.vendor_id', 'vendor_id'), 18), CA('contact', 'Contact', 'text', LKT('vendors.contact', 'vendors.vendor_id', 'vendor_id'), 20),
    QPH('ph_vq', 'Videographer phone, quote', 'Videographer', '{col:open_flag}=1'), QPH('ph_vinc', 'Videographer phone, includes', 'Videographer', '{col:open_flag}=1'), QPH('ph_tq', 'Tailor phone, quote', 'Tailor', '{col:open_flag}=1'),
    CA('ph_decl', 'Phone, declined quote', 'text', 'IF({col:status}=%s,{col:vendor_phone},"")' % QDECL, 18), CPL()],
    D.quotes_d(), 60, [A('days_to_expiry', '< 0', 'bad'), A('days_to_expiry', '<= {set:expiry_days}', 'warn'), A('status', '= ' + QBOOK, 'good')]))

# 3 contract items -----------------------------------------------------------
tables.append(T('contracts', 'Contract Items', 'Contract Items', 'What each booked contract says: included, not included, cancellation terms, final headcount and payment dates, arrival and overtime rate. Check your contract for the wording.', [
    C('contract_id', 'Contract ID', 'text', 10, required=True), C('vendor_id', 'Vendor ID', 'text', 9), LST('vendor', 'Vendor', 'vname', 22), LST('kind', 'Kind', 'ckind', 20), C('detail', 'Detail', 'text', 40),
    C('item_date', 'Item date', 'date', 11), C('amount', 'Amount', 'int', 9), CA('ckey', 'Vendor and kind', 'text', '{col:vendor_id}&"|"&{col:kind}', 24)], D.contracts_d(), 90))

# 4 pipeline by category -----------------------------------------------------
LEAD_OPEN = 'SUMPRODUCT(MAX(({range:vendors.category}={col:category})*({range:vendors.status}<>%s)*({range:vendors.vendor_id}<>"")*{range:vendors.lead_months}))' % BOOKED
tables.append(T('pipeline', 'Pipeline by Category', 'Pipeline by Category', 'One row per budget category: vendors listed, quotes, how many are booked and the latest date to book the open ones, from the typical lead time you can edit on Vendors.', [
    LST('category', 'Category', 'category', 24, required=True),
    CA('vendors', 'Vendors listed', 'int', 'COUNTIFS({range:vendors.category},{col:category})', 9), CA('quotes_n', 'Quotes', 'int', 'COUNTIFS({range:quotes.category},{col:category})', 9),
    CA('quote_received', 'Quote received', 'int', 'COUNTIFS({range:vendors.category},{col:category},{range:vendors.status},%s)' % VQR, 9),
    CA('shortlisted', 'Shortlisted', 'int', 'COUNTIFS({range:vendors.category},{col:category},{range:vendors.status},%s)' % VSL, 9),
    CA('booked', 'Booked', 'int', 'COUNTIFS({range:vendors.category},{col:category},{range:vendors.status},%s)' % BOOKED, 9),
    CA('declined', 'Declined quotes', 'int', 'COUNTIFS({range:quotes.category},{col:category},{range:quotes.status},%s)' % QDECL, 9),
    CA('open', 'Open', 'int', '{col:vendors}-{col:booked}', 7), CA('lead_months', 'Lead months of the open vendor', 'int', LEAD_OPEN, 9),
    CA('deadline', 'Latest booking date', 'date', 'IF({col:open}>0,EDATE({set:wedding_day},-{col:lead_months}),"")', 11),
    CA('days_left', 'Days left', 'int', 'IF({col:deadline}="","",{col:deadline}-{today})', 8),
    CA('status', 'Status', 'text', 'IF({col:vendors}=0,%s,IF({col:open}=0,%s,IF({col:days_left}<0,%s,IF({col:days_left}<=60,%s,%s))))' % (V('No vendor listed'), V('Booked'), V('Book now'), V('Book soon'), V('Open')), 14),
    CA('rank', 'Order to decide', 'int', 'IF({col:deadline}="","",COUNTIFS({range:pipeline.deadline},"<"&{col:deadline})+1+SUMPRODUCT(({range:pipeline.deadline}={col:deadline})*({range:pipeline.category}<{col:category})))', 8)],
    D.pipeline_d(), 40, [A('status', '= ' + V('Book now'), 'bad'), A('status', '= ' + V('Book soon'), 'warn'), A('status', '= ' + V('Booked'), 'good')]))

# 5 scoring weights ----------------------------------------------------------
tables.append(T('weights', 'Scoring Weights', 'Scoring Weights', 'How much each factor counts when quotes are scored. Change the weights to match what matters to you; they are used as shares of the total.', [
    C('factor', 'Factor', 'text', 22, required=True), C('weight', 'Weight', 'pct', 10), C('note', 'How it is scored', 'text', 50)], D.weights_d(), 12))

# 6 true-cost comparison -----------------------------------------------------
W = lambda i: 'INDEX({range:weights.weight},%d)' % i
WS = 'SUM({range:weights.weight})'
SAME = '({range:compare.vendor}={col:vendor})'
tables.append(T('compare', 'True-Cost Table', 'True-Cost Table', 'Every quote scored on its true total (price against the lowest in its vendor slot) and on your ratings with the weights from Scoring Weights; ranks inside the slot and a verdict fill in.', [
    C('quote_id', 'Quote ID', 'text', 9, required=True),
    CA('vendor', 'Vendor', 'text', LKT('quotes.vendor', 'quotes.quote_id', 'quote_id'), 22), CA('vendor_id', 'Vendor ID', 'text', LKT('quotes.vendor_id', 'quotes.quote_id', 'quote_id'), 9),
    CA('category', 'Category', 'text', LKT('quotes.category', 'quotes.quote_id', 'quote_id'), 22), CA('option', 'Option', 'text', LKT('quotes.option', 'quotes.quote_id', 'quote_id'), 10),
    CA('status', 'Status', 'text', LKT('quotes.status', 'quotes.quote_id', 'quote_id'), 12), CA('label', 'Quote', 'text', '{col:vendor}&" "&{col:option}', 24),
    CA('base_price', 'Base price', 'money', LKN('quotes.base_price', 'quotes.quote_id', 'quote_id'), 11), CA('true_total', 'True total', 'money', LKN('quotes.true_total', 'quotes.quote_id', 'quote_id'), 11),
    CA('fit', 'Fit', 'int', LKN('quotes.fit', 'quotes.quote_id', 'quote_id'), 6), CA('response', 'Response', 'int', LKN('quotes.response', 'quotes.quote_id', 'quote_id'), 8),
    CA('reviews', 'Reviews', 'int', LKN('quotes.reviews', 'quotes.quote_id', 'quote_id'), 8), CA('response_days', 'Days to reply', 'int', LKN('quotes.response_days', 'quotes.quote_id', 'quote_id'), 8),
    CA('price_rank', 'Price rank in the slot', 'int', 'COUNTIFS({range:compare.vendor},{col:vendor},{range:compare.true_total},"<"&{col:true_total})+1+SUMPRODUCT(%s*({range:compare.true_total}={col:true_total})*({range:compare.quote_id}<{col:quote_id}))' % SAME, 8),
    CA('pkey', 'Price key', 'text', '{col:vendor}&"||"&{col:price_rank}', 22),
    CA('low_total', 'Lowest true total in the slot', 'money', 'IFERROR(INDEX({range:compare.true_total},MATCH({col:vendor}&"||1",{range:compare.pkey},0)),0)', 11),
    CA('price_gap', 'Above the lowest', 'money', '{col:true_total}-{col:low_total}', 10),
    CA('p_raw', 'Price score, 0 to 1', 'num', 'IF({col:true_total}>0,{col:low_total}/{col:true_total},0)', 8),
    CA('r_raw', 'Rating score, 0 to 1', 'num', '(%s*{col:fit}/5+%s*{col:response}/5+%s*{col:reviews}/5+%s*MAX(0,1-{col:response_days}/10))/(%s-%s)' % (W(2), W(3), W(4), W(5), WS, W(1)), 8),
    CA('price_part', 'Price part', 'num', '%s/%s*{col:p_raw}' % (W(1), WS), 8), CA('rating_part', 'Rating part', 'num', '(1-%s/%s)*{col:r_raw}' % (W(1), WS), 8),
    CA('score', 'Weighted score', 'num', 'ROUND(100*({col:price_part}+{col:rating_part}),1)', 9),
    CA('rank', 'Rank in the slot', 'int', 'COUNTIFS({range:compare.vendor},{col:vendor},{range:compare.score},">"&{col:score})+1+SUMPRODUCT(%s*({range:compare.score}={col:score})*({range:compare.quote_id}<{col:quote_id}))' % SAME, 8),
    CA('vkey', 'Rank key', 'text', '{col:vendor}&"|"&{col:rank}', 22),
    CA('fitscore', 'Fit then score', 'num', '{col:fit}*1000+{col:score}', 9),
    CA('fit_rank', 'Fit rank in the slot', 'int', 'COUNTIFS({range:compare.vendor},{col:vendor},{range:compare.fitscore},">"&{col:fitscore})+1+SUMPRODUCT(%s*({range:compare.fitscore}={col:fitscore})*({range:compare.quote_id}<{col:quote_id}))' % SAME, 8),
    CA('fkey', 'Fit key', 'text', '{col:vendor}&"|||"&{col:fit_rank}', 22),
    CA('verdict', 'Verdict', 'text', 'IF({col:rank}=1,IF({col:price_rank}=1,%s,%s),IF({col:price_rank}=1,%s,%s))' % (V('Best value and lowest price'), V('Best value'), V('Lowest price'), V('Other option')), 22),
    CA('slot_booked', 'Slot booked', 'int', 'IF(IFERROR(INDEX({range:vendors.status},MATCH({col:vendor_id},{range:vendors.vendor_id},0)),"")=%s,1,0)' % BOOKED, 7),
    CA('slot_cost', 'Cost of the slot, booked or leading', 'money', 'IF({col:rank}=1,IF({col:slot_booked}=1,IFERROR(INDEX({range:vendors.contract_total},MATCH({col:vendor_id},{range:vendors.vendor_id},0)),0),{col:true_total}),"")', 11),
    CA('low_open', 'Lowest total of an open slot', 'money', 'IF({col:slot_booked}=0,IF({col:price_rank}=1,{col:true_total},""),"")', 11),
    CA('lead_open', 'Leading total of an open slot', 'money', 'IF({col:slot_booked}=0,IF({col:rank}=1,{col:true_total},""),"")', 11),
    CA('lead_extras', 'Extras of the leading quote', 'money', 'IF({col:rank}=1,{col:true_total}-{col:base_price},"")', 11)],
    D.compare_d(), 60, [A('verdict', '= ' + V('Best value and lowest price'), 'good'), A('verdict', '= ' + V('Best value'), 'good'), A('verdict', '= ' + V('Lowest price'), 'warn')]))

# 7 category winners ---------------------------------------------------------
def CMP(col, kc): return 'IFERROR(INDEX({range:compare.%s},MATCH({col:vendor}&"%s",{range:compare.%s},0)),%s)'
def WIN(col, suffix, keycol, num=False): return 'IFERROR(INDEX({range:compare.%s},MATCH({col:vendor}&"%s",{range:compare.%s},0))%s,%s)' % (col, suffix, keycol, '' if num else '&""', '0' if num else '""')
def QOP(opt): return 'SUMIFS({range:quotes.true_total},{range:quotes.vendor},{col:vendor},{range:quotes.option},%s)' % opt
tables.append(T('winners', 'Category Winners', 'Category Winners', 'For each vendor slot: the best-value option on your weights, the lowest price and the best fit, with what the best value costs above the lowest price. It fills in from the True-Cost Table.', [
    LST('vendor', 'Vendor', 'vname', 22, required=True), CA('category', 'Category', 'text', 'IFERROR(INDEX({range:vendors.category},MATCH({col:vendor},{range:vendors.vendor},0))&"","")', 22),
    CA('best_value', 'Best value', 'text', WIN('option', '|1', 'vkey'), 10), CA('best_total', 'Best value true total', 'money', WIN('true_total', '|1', 'vkey', True), 11),
    CA('lowest_price', 'Lowest price', 'text', WIN('option', '||1', 'pkey'), 10), CA('lowest_total', 'Lowest true total', 'money', WIN('true_total', '||1', 'pkey', True), 11),
    CA('best_fit', 'Best fit', 'text', WIN('option', '|||1', 'fkey'), 10), CA('extra_for_best', 'Best value above the lowest', 'money', '{col:best_total}-{col:lowest_total}', 11),
    CA('second_value', 'Second best', 'text', WIN('option', '|2', 'vkey'), 10), CA('second_total', 'Second best true total', 'money', WIN('true_total', '|2', 'vkey', True), 11),
    CA('lead_s', 'Leading score, 0 to 1', 'num', 'SUMIFS({range:compare.price_part},{range:compare.vkey},{col:vendor}&"|1")+SUMIFS({range:compare.rating_part},{range:compare.vkey},{col:vendor}&"|1")', 9),
    CA('second_r', 'Second rating part', 'num', 'SUMIFS({range:compare.rating_part},{range:compare.vkey},{col:vendor}&"|2")', 9),
    CA('second_low', 'Lowest total in the slot', 'money', 'SUMIFS({range:compare.low_total},{range:compare.vkey},{col:vendor}&"|2")', 11),
    CA('need_price', 'Price score the second needs', 'num', 'IF({col:second_total}=0,"",({col:lead_s}-{col:second_r})/(%s/%s))' % (W(1), WS), 9),
    CA('drop_needed', 'Drop that lets the second win', 'money', 'IF({col:need_price}="","",IF({col:need_price}>1,"",ROUNDUP(MAX(0,{col:second_total}-{col:second_low}/{col:need_price}),0)+1))', 11),
    CA('total_a', 'True total, Option A', 'money', QOP(OPT_A), 11), CA('total_b', 'True total, Option B', 'money', QOP(OPT_B), 11), CA('total_c', 'True total, Option C', 'money', QOP(OPT_C), 11)],
    D.winners_d(), 40))

# 8 contract deadlines -------------------------------------------------------
CTM = 'MATCH({col:ref_id},{range:contracts.contract_id},0)'; PYM = 'MATCH({col:ref_id},{range:schedule.pay_id},0)'; QTM = 'MATCH({col:ref_id},{range:quotes.quote_id},0)'
PH_NEXT = 'IF({col:next_all}="","",IF({col:days_left}<={set:amber_days},"%s",""))' % D.P2_PHONE
tables.append(T('deadlines', 'Contract Deadlines', 'Contract Deadlines', 'Every date that matters: contract dates, unpaid payments and quote expiry, with days left and a red, amber or green flag from your own limits.', [
    C('ref_id', 'Item ID', 'text', 10, required=True),
    CA('source', 'Source', 'text', 'IF(ISNUMBER(%s),%s,IF(ISNUMBER(%s),%s,%s))' % (CTM, V('Contract date'), PYM, V('Payment due'), V('Quote expiry')), 14),
    CA('vendor', 'Vendor', 'text', 'IFERROR(INDEX({range:contracts.vendor},%s),IFERROR(INDEX({range:schedule.vendor},%s),IFERROR(INDEX({range:quotes.vendor},%s),"")))&""' % (CTM, PYM, QTM), 22),
    CA('kind', 'Kind', 'text', 'IFERROR(INDEX({range:contracts.kind},%s),IFERROR(INDEX({range:schedule.kind},%s),IF(ISNUMBER(%s),%s,"")))&""' % (CTM, PYM, QTM, V('Quote valid until')), 20),
    CA('date', 'Date', 'date', 'IFERROR(IF(INDEX({range:contracts.item_date},%s)=0,"",INDEX({range:contracts.item_date},%s)),IFERROR(INDEX({range:schedule.due_date},%s),IFERROR(INDEX({range:quotes.valid_until},%s),"")))' % (CTM, CTM, PYM, QTM), 11),
    CA('amount', 'Amount due', 'money', 'IFERROR(INDEX({range:schedule.amount_due},%s),0)' % PYM, 11),
    CA('done', 'Done', 'int', 'IF(ISNUMBER(%s),IF(INDEX({range:schedule.status},%s)=%s,1,0),IF(ISNUMBER(%s),IF(INDEX({range:quotes.open_flag},%s)=1,0,1),IF({col:date}="",1,IF({col:date}<{today},1,0))))' % (PYM, PYM, PAID, QTM, QTM), 7),
    CA('days_left', 'Days left', 'int', 'IF({col:date}="","",{col:date}-{today})', 9),
    CA('flag', 'Flag', 'text', 'IF({col:date}="",%s,IF({col:done}=1,%s,IF({col:days_left}<0,%s,IF({col:days_left}<={set:red_days},%s,IF({col:days_left}<={set:amber_days},%s,%s)))))' % (V('No date'), V('Done'), V('Overdue'), V('Red'), V('Amber'), V('Green')), 10),
    CA('next_all', 'Next date', 'date', 'IF({col:date}="","",IF({col:done}=0,IF({col:days_left}>=0,{col:date},""),""))', 11),
    CA('next_contract', 'Next contract date', 'date', 'IF(ISNUMBER(%s),{col:next_all},"")' % CTM, 11),
    CA('hc_next', 'Next final headcount date', 'date', 'IF(ISNUMBER(%s),IF({col:kind}=%s,{col:next_all},""),"")' % (CTM, K_FHC), 11),
    CA('seq', 'Order', 'int', 'IF({col:next_all}="","",COUNTIFS({range:deadlines.next_all},"<"&{col:next_all})+1+SUMPRODUCT(({range:deadlines.next_all}={col:next_all})*({range:deadlines.ref_id}<{col:ref_id})))', 8),
    CA('ph_next', 'Partner phone, next date', 'text', PH_NEXT, 18), CPL()],
    D.deadlines_d(), 70, [A('flag', '= ' + V('Overdue'), 'bad'), A('flag', '= ' + V('Red'), 'bad'), A('flag', '= ' + V('Amber'), 'warn'), A('flag', '= ' + V('Green'), 'good')]))

# 9 payment schedule (reference copy) -----------------------------------------
tables.append(T('schedule', 'Payment Schedule', 'Payment Schedule', 'A copy of the payment schedule from the budget workbook: every deposit, instalment and final balance with its due date and what is paid. Keep it the same as the money workbook.', [
    C('pay_id', 'Pay ID', 'text', 9, required=True), C('vendor_id', 'Vendor ID', 'text', 9), LST('vendor', 'Vendor', 'vname', 22), LST('category', 'Category', 'vcat', 24), LST('kind', 'Kind', 'paykind', 12),
    C('due_date', 'Due date', 'date', 11), C('amount_due', 'Amount due', 'money', 11), C('amount_paid', 'Amount paid', 'money', 11), LST('status', 'Status', 'paystatus', 11),
    CA('days_to_due', 'Days to due', 'int', 'IF({col:status}<>%s,{col:due_date}-{today},"")' % PAID, 9),
    CA('vendor_phone', 'Vendor phone', 'text', LKT('vendors.phone', 'vendors.vendor_id', 'vendor_id'), 18), CA('contact', 'Contact', 'text', LKT('vendors.contact', 'vendors.vendor_id', 'vendor_id'), 20),
    CA('pay_on', 'We will pay on', 'date', 'IF({col:status}<>%s,MAX({today},{col:due_date}-3),"")' % PAID, 11),
    CA('ph_conf', 'Vendor phone, deposit', 'text', 'IF({col:kind}=%s,{col:vendor_phone},"")' % DEP, 18),
    CA('ph_rec', 'Vendor phone, deposit paid', 'text', 'IF({col:kind}=%s,IF({col:status}=%s,{col:vendor_phone},""),"")' % (DEP, PAID), 18),
    CA('ph_final', 'Vendor phone, final balance', 'text', 'IF({col:kind}=%s,IF({col:status}<>%s,{col:vendor_phone},""),"")' % (FB, PAID), 18), CPL()],
    D.schedule_d(), 60, [A('status', '= ' + tok('paystatus', 'Overdue'), 'bad'), A('status', '= ' + PAID, 'good')]))

# 10 run of show (reference copy) --------------------------------------------
tables.append(T('run', 'Run of Show', 'Run of Show', 'A copy of the minute-by-minute plan of the day from the run-of-show workbook: when each step starts, how long it takes, where and which vendor is there.', [
    C('step_id', 'Step ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('start', 'Start', 'time', 9), C('minutes', 'Minutes', 'int', 9), LST('block', 'Block', 'block', 14), LST('place', 'Place', 'place', 11),
    C('vendor_id', 'Vendor ID', 'text', 9), C('what', 'What happens', 'text', 40),
    CA('end', 'End', 'time', '{col:start}+{col:minutes}/1440', 9)], D.run_d(), 60))

# 11 vendor arrivals and overlaps --------------------------------------------
SM = 'ROUND({col:start}*1440,0)'; EM = '(ROUND({col:start}*1440,0)+{col:minutes})'
OS = 'ROUND({range:run.start}*1440,0)'; OE = '(ROUND({range:run.start}*1440,0)+{range:run.minutes})'
MASK = '({range:run.place}={col:place})*({range:run.vendor_id}<>{col:vendor_id})*({range:run.vendor_id}<>"")*((({range:run.block}=%s)+({range:run.block}=%s))>0)*{col:setup}' % (PREP, CLOSE)
tables.append(T('arrivals', 'Vendor Arrivals', 'Vendor Arrivals', 'Every step with a vendor on the day. Set-up and load-out steps in the same place are checked for overlaps and for less than your buffer between two vendors; the first clash time fills in.', [
    C('step_id', 'Step ID', 'text', 9, required=True),
    CA('start', 'Start', 'time', LKN('run.start', 'run.step_id', 'step_id'), 9), CA('minutes', 'Minutes', 'int', LKN('run.minutes', 'run.step_id', 'step_id'), 8),
    CA('end', 'End', 'time', '{col:start}+{col:minutes}/1440', 9), CA('vendor_id', 'Vendor ID', 'text', LKT('run.vendor_id', 'run.step_id', 'step_id'), 9),
    CA('vendor', 'Vendor', 'text', 'IFERROR(INDEX({range:vendors.vendor},MATCH({col:vendor_id},{range:vendors.vendor_id},0))&"","")', 22),
    CA('place', 'Place', 'text', LKT('run.place', 'run.step_id', 'step_id'), 11), CA('block', 'Block', 'text', LKT('run.block', 'run.step_id', 'step_id'), 14),
    CA('setup', 'Set-up or load-out', 'int', 'IF(OR({col:block}=%s,{col:block}=%s),1,0)' % (PREP, CLOSE), 7),
    CA('overlaps', 'Steps it overlaps', 'int', 'SUMPRODUCT(%s*(%s<%s)*(%s>%s))' % (MASK, OS, EM, OE, SM), 8),
    CA('gap_next', 'Minutes before the next vendor', 'int', 'IF({col:setup}=0,"",IF(SUMPRODUCT(MIN(%s*(%s>=%s)*(%s-%s)+(1-%s*(%s>=%s))*9999))>=9999,"",SUMPRODUCT(MIN(%s*(%s>=%s)*(%s-%s)+(1-%s*(%s>=%s))*9999))))' % (
        MASK, OS, SM, OS, EM, MASK, OS, SM, MASK, OS, SM, OS, EM, MASK, OS, SM), 9),
    CA('clash_at', 'Clash at', 'time', 'IF({col:overlaps}>0,MAX(%s,SUMPRODUCT(MAX(%s*(%s<%s)*(%s>%s)*%s)))/1440,"")' % (SM, MASK, OS, EM, OE, SM, OS), 9),
    CA('flag', 'Flag', 'text', 'IF({col:overlaps}>0,%s,IF({col:gap_next}="",%s,IF({col:gap_next}<{set:setup_buffer},%s,%s)))' % (V('Overlap'), V('Clear'), V('Tight'), V('Clear')), 10)],
    D.arrivals_d(), 50, [A('flag', '= ' + V('Overlap'), 'bad'), A('flag', '= ' + V('Tight'), 'warn')]))

# 12 day-of contact sheet ----------------------------------------------------
VM = 'MATCH({col:vendor},{range:vendors.vendor},0)'
def VLK(c_, txt=True): return 'IFERROR(INDEX({range:vendors.%s},%s)%s,%s)' % (c_, VM, '&""' if txt else '', '""' if txt else '0')
tables.append(T('contact', 'Day-of Contact Sheet', 'Day-of Contact Sheet', 'One row per vendor for the page you print for the day: contact, phone, first arrival, meeting point and the first job. Share the printed page with the day-of coordinator; no vendor sees your details.', [
    LST('vendor', 'Vendor', 'vname', 22, required=True), CA('vendor_id', 'Vendor ID', 'text', VLK('vendor_id'), 9), CA('contact', 'Contact', 'text', VLK('contact'), 22), CA('phone', 'Phone', 'text', VLK('phone'), 18),
    CA('status', 'Status', 'text', VLK('status'), 12), CA('arrival', 'First arrival', 'time', 'IFERROR(INDEX({range:vendors.arrival},%s),"")' % VM, 9),
    CA('meeting_point', 'Meeting point', 'text', VLK('meeting_point'), 12), CA('first_task', 'First task on the day', 'text', VLK('first_task'), 36),
    CA('steps', 'Steps', 'int', VLK('steps', False), 7),
    CA('last_out', 'Last step ends', 'time', 'IF({col:steps}=0,"",SUMPRODUCT(MAX(({range:run.vendor_id}={col:vendor_id})*({range:run.start}+{range:run.minutes}/1440))))', 9),
    CA('confirmed', 'Confirmed for the day', 'text', 'IF(IFERROR(INDEX({range:vendors.confirmed},%s),FALSE)=%s,%s,%s)' % (VM, YES, YES, NO), 10),
    CA('wedding_day', 'Wedding day', 'date', '{set:wedding_day}', 11), CA('guests', 'Guests', 'int', '{set:headcount}', 9),
    VPH('ph_venue', 'Venue phone', 'Venue'), VPH('ph_caterer', 'Caterer phone', 'Caterer'), VPH('ph_photog', 'Photographer phone', 'Photographer'), VPH('ph_band', 'Band or DJ phone', 'Band or DJ'),
    VPH('ph_florist', 'Florist phone', 'Florist'), VPH('ph_officiant', 'Officiant phone', 'Officiant'), VPH('ph_cake', 'Cake baker phone', 'Cake baker'), VPH('ph_hair', 'Hair and makeup phone', 'Hair and makeup'),
    VPH('ph_attire', 'Attire shop phone', 'Attire shop'), VPH('ph_stat', 'Stationery printer phone', 'Stationery printer'), VPH('ph_rent', 'Rentals phone', 'Rentals'), VPH('ph_trans', 'Transport phone', 'Transport'),
    VPH('ph_coord', 'Coordinator phone', 'Day-of coordinator'), VPH('ph_hotel', 'Hotel phone', 'Hotel room block'),
    CA('ph_cancel', 'Phone of a booked vendor', 'text', 'IF({col:status}=%s,{col:phone},"")' % BOOKED, 18), CPL()], D.contact_d(), 40))

# 13 vendor meals ------------------------------------------------------------
tables.append(T('meals', 'Vendor Meals List', 'Vendor Meals List', 'How long each vendor is on site, whether a vendor meal is needed after your hours limit and how many meals to order; type the crew size for each vendor.', [
    LST('vendor', 'Vendor', 'vname', 22, required=True), C('crew', 'People on site', 'int', 10),
    CA('vendor_id', 'Vendor ID', 'text', VLK('vendor_id'), 9),
    CA('first_in', 'Arrives', 'time', 'IFERROR(INDEX({range:run.start},MATCH({col:vendor_id},{range:run.vendor_id},0)),"")', 9),
    CA('last_out', 'Last step ends', 'time', 'IF({col:first_in}="","",SUMPRODUCT(MAX(({range:run.vendor_id}={col:vendor_id})*({range:run.start}+{range:run.minutes}/1440))))', 9),
    CA('hours', 'Hours on site', 'hours', 'IF({col:first_in}="","",ROUND(({col:last_out}-{col:first_in})*24,1))', 9),
    CA('needed', 'Meal needed', 'text', 'IF({col:hours}="",%s,IF({col:hours}>={set:meal_hours},%s,%s))' % (NO, YES, NO), 10),
    CA('count', 'Meals to order', 'int', 'IF({col:needed}=%s,{col:crew},0)' % YES, 8)], D.meals_d(), 40))

# 14 follow-up list ----------------------------------------------------------
tables.append(T('followups', 'Follow-up List', 'Follow-up List', 'Vendors to chase, ranked: days since the last contact, whether the vendor is still open and how soon an open quote expires. Rank 1 is the first call.', [
    LST('vendor', 'Vendor', 'vname', 22, required=True),
    CA('vendor_id', 'Vendor ID', 'text', VLK('vendor_id'), 9), CA('status', 'Status', 'text', VLK('status'), 14),
    CA('last_contact', 'Last contact', 'date', 'IFERROR(IF(INDEX({range:vendors.last_contact},%s)=0,"",INDEX({range:vendors.last_contact},%s)),"")' % (VM, VM), 11),
    CA('days_since', 'Days since contact', 'int', 'IF({col:last_contact}="","",{today}-{col:last_contact})', 9),
    CA('follow_up', 'Follow-up date', 'date', 'IFERROR(IF(INDEX({range:vendors.follow_up},%s)=0,"",INDEX({range:vendors.follow_up},%s)),"")' % (VM, VM), 11),
    CA('quote_valid', 'Open quote valid until', 'date', 'IF(SUMPRODUCT(MIN(({range:quotes.vendor_id}={col:vendor_id})*({range:quotes.open_flag}=1)*{range:quotes.valid_until}+(1-({range:quotes.vendor_id}={col:vendor_id})*({range:quotes.open_flag}=1))*999999))>=999999,"",SUMPRODUCT(MIN(({range:quotes.vendor_id}={col:vendor_id})*({range:quotes.open_flag}=1)*{range:quotes.valid_until}+(1-({range:quotes.vendor_id}={col:vendor_id})*({range:quotes.open_flag}=1))*999999)))', 11),
    CA('quote_days', 'Days to quote expiry', 'int', 'IF({col:quote_valid}="","",{col:quote_valid}-{today})', 9),
    CA('urgency', 'Urgency', 'int', '{col:days_since}+IF({col:status}=%s,0,20)+IF({col:quote_days}="",0,MAX(0,30-{col:quote_days}))' % BOOKED, 8),
    CA('rank', 'Chase order', 'int', 'COUNTIFS({range:followups.urgency},">"&{col:urgency})+1+SUMPRODUCT(({range:followups.urgency}={col:urgency})*({range:followups.vendor}<{col:vendor}))', 8),
    CA('flag', 'Flag', 'text', 'IF({col:days_since}>{set:stale_days},%s,IF({col:status}=%s,%s,%s))' % (V('Chase'), BOOKED, V('Fine'), V('Open, watch')), 12),
    CA('ph_partner', 'Partner phone, silent vendor', 'text', 'IF({col:days_since}>{set:stale_days},"%s","")' % D.P2_PHONE, 18), CPL()],
    D.followups_d(), 30, [A('flag', '= ' + V('Chase'), 'bad'), A('flag', '= ' + V('Open, watch'), 'warn')]))

# 15 cancellation exposure ---------------------------------------------------
tables.append(T('cancel', 'Cancellation by Vendor', 'Cancellation by Vendor', 'For each booked vendor: the deposit paid, everything paid and the part you could lose if you cancelled, using your refund window. Check your contract for the real terms.', [
    LST('vendor', 'Vendor', 'vname', 22, required=True), LST('category', 'Category', 'vcat', 24),
    CA('contract_total', 'Contract total', 'money', VLK('contract_total', False), 11),
    CA('deposit_paid', 'Deposit paid', 'money', 'SUMIFS({range:schedule.amount_paid},{range:schedule.vendor},{col:vendor},{range:schedule.kind},%s)' % DEP, 11),
    CA('paid_total', 'Paid in total', 'money', 'SUMIFS({range:schedule.amount_paid},{range:schedule.vendor},{col:vendor})', 11),
    CA('non_refundable', 'Non-refundable estimate', 'money', '{col:deposit_paid}', 11),
    CA('at_risk', 'At risk if you cancel', 'money', '{col:deposit_paid}+IF({set:wedding_day}-{today}<{set:refund_days},{col:paid_total}-{col:deposit_paid},0)', 11),
    CA('share_lost', 'Share of paid at risk', 'pct', 'IF({col:paid_total}>0,{col:at_risk}/{col:paid_total},0)', 9),
    CA('terms', 'Cancellation terms', 'text', VLK('cancel_terms'), 40)], D.cancel_d(), 30))

# 16 budget lines (reference copy) -------------------------------------------
tables.append(T('budget', 'Budget Lines', 'Budget Lines', 'A copy of the budget lines from the budget workbook: planned, committed and paid for each category. Keep it the same as the money workbook.', [
    C('line_id', 'Line ID', 'text', 9, required=True), LST('category', 'Category', 'category', 24), C('planned', 'Planned', 'money', 11), C('committed', 'Committed', 'money', 11), C('paid', 'Paid', 'money', 11)], D.budget_d(), 30))

# 17 plan fit by category ----------------------------------------------------
BL = lambda c_: 'IFERROR(INDEX({range:budget.%s},MATCH({col:category},{range:budget.category},0)),0)' % c_
tables.append(T('planfit', 'Plan Fit by Category', 'Plan Fit by Category', 'Each budget category against what its vendors cost: booked contract totals plus the leading quote of every open slot, the room left in the plan and a verdict.', [
    LST('category', 'Category', 'category', 24, required=True), CA('planned', 'Planned', 'money', BL('planned'), 11), CA('committed', 'Committed', 'money', BL('committed'), 11),
    CA('slots', 'Vendor slots', 'int', 'COUNTIFS({range:vendors.category},{col:category})', 8),
    CA('best_total', 'Booked and leading quotes', 'money', 'SUMIFS({range:compare.slot_cost},{range:compare.category},{col:category})', 11),
    CA('expected', 'Expected cost', 'money', 'IF({col:slots}>0,{col:best_total},{col:committed})', 11), CA('room', 'Room left in the plan', 'money', '{col:planned}-{col:expected}', 11),
    CA('over_pct', 'Over plan', 'pct', 'IF({col:planned}>0,MAX(0,-{col:room})/{col:planned},0)', 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:room}>=0,%s,IF({col:over_pct}<=0.1,%s,%s))' % (V('Fits the line'), V('Watch'), V('Over')), 14)],
    D.planfit_d(), 40, [A('verdict', '= ' + V('Over'), 'bad'), A('verdict', '= ' + V('Watch'), 'warn'), A('verdict', '= ' + V('Fits the line'), 'good')]))

# 18 response times ----------------------------------------------------------
tables.append(T('response', 'Response Times', 'Response Times', 'How fast each vendor answers: the average days to reply over its quotes, the rank (1 is the slowest) and a flag from your slow-reply limit; open vendors get their own order.', [
    LST('vendor', 'Vendor', 'vname', 22, required=True), CA('category', 'Category', 'text', VLK('category'), 22), CA('status', 'Status', 'text', VLK('status'), 14),
    CA('quotes', 'Quotes', 'int', 'COUNTIFS({range:quotes.vendor},{col:vendor})', 8),
    CA('avg_days', 'Average days to reply', 'num', 'IFERROR(ROUND(AVERAGEIFS({range:quotes.response_days},{range:quotes.vendor},{col:vendor}),1),0)', 9),
    CA('rank', 'Slowest first', 'int', 'COUNTIFS({range:response.avg_days},">"&{col:avg_days})+1+SUMPRODUCT(({range:response.avg_days}={col:avg_days})*({range:response.vendor}<{col:vendor}))', 8),
    CA('open', 'Open', 'int', 'IF({col:status}=%s,0,1)' % BOOKED, 6),
    CA('open_score', 'Open score', 'num', '{col:open}*{col:avg_days}', 8),
    CA('open_rank', 'Slowest open first', 'int', 'IF({col:open}=1,COUNTIFS({range:response.open_score},">"&{col:open_score})+1+SUMPRODUCT(({range:response.open_score}={col:open_score})*({range:response.vendor}<{col:vendor})),"")', 8),
    CA('flag', 'Flag', 'text', 'IF({col:avg_days}>{set:slow_days},%s,IF({col:avg_days}<=3,%s,%s))' % (V('Slow'), V('Fast'), V('Normal')), 10)],
    D.response_d(), 30, [A('flag', '= ' + V('Slow'), 'warn'), A('flag', '= ' + V('Fast'), 'good')]))

# 19 booking lead check ------------------------------------------------------
tables.append(T('lead', 'Booking Lead Check', 'Booking Lead Check', 'Was each vendor booked far enough ahead of the wedding for its typical lead time (typical, edit), and are the open vendors still in time? The latest booking date fills in.', [
    LST('vendor', 'Vendor', 'vname', 22, required=True), CA('status', 'Status', 'text', VLK('status'), 14),
    CA('booked_on', 'Booked on', 'date', 'IFERROR(IF(INDEX({range:vendors.booked_on},%s)=0,"",INDEX({range:vendors.booked_on},%s)),"")' % (VM, VM), 11),
    CA('months_before', 'Months before the wedding', 'num', 'IF({col:booked_on}="","",ROUND(({set:wedding_day}-{col:booked_on})/30.4,1))', 9),
    CA('lead_months', 'Typical lead months', 'int', VLK('lead_months', False), 9), CA('latest_date', 'Latest booking date', 'date', 'EDATE({set:wedding_day},-{col:lead_months})', 11),
    CA('months_now', 'Months left now', 'num', 'ROUND(({set:wedding_day}-{today})/30.4,1)', 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:booked_on}<>"",IF({col:months_before}>={col:lead_months},%s,%s),IF({col:months_now}>={col:lead_months},%s,%s))' % (V('Booked in time'), V('Booked late'), V('Open, in time'), V('Open, late')), 14),
    CA('ok', 'Booked in time', 'int', 'IF({col:verdict}=%s,1,0)' % V('Booked in time'), 8)],
    D.lead_d(), 30, [A('verdict', '= ' + V('Open, late'), 'bad'), A('verdict', '= ' + V('Booked late'), 'warn'), A('verdict', '= ' + V('Booked in time'), 'good')]))

# 20 vendor status summary ---------------------------------------------------
tables.append(T('statusum', 'Vendor Status Summary', 'Vendor Status Summary', 'Vendors and contract totals for each stage of the pipeline.', [
    LST('status', 'Stage', 'vstage', 20, required=True), CA('vendors', 'Vendors', 'int', 'COUNTIFS({range:vendors.status},{col:status})', 9),
    CA('contract_total', 'Contract total', 'money', 'SUMIFS({range:vendors.contract_total},{range:vendors.status},{col:status})', 12)], D.statusum_d(), 12))
for _t in tables: _t['rows'] = max(50, _t['rows'])
assert len(tables) == 20, len(tables)
