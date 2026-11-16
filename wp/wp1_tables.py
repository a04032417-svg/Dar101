"""Wedding suite part 1: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp1_lists import *
import wp1_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def R(t, c_): return '{range:%s.%s}' % (t, c_)
def CPL(): return CA('couple', 'Couple', 'text', '{set:couple}', 20)
def VN(n): return tok('vname', n)
def SC(key_, label, cond, phone): return CA(key_, label, 'text', 'IF(%s,%s,"")' % (cond, phone if phone.startswith('{') else '"%s"' % phone), 18)


MS = 'DATE(YEAR({today}),MONTH({today}),1)'
PAID = tok('paystatus', 'Paid'); UPC = tok('paystatus', 'Upcoming'); OVD = tok('paystatus', 'Overdue')
FB = tok('paykind', 'Final balance'); INST = tok('paykind', 'Instalment'); DEP = tok('paykind', 'Deposit')
RECV = tok('fstatus', 'Received'); PROM = tok('fstatus', 'Promised'); NOTC = tok('fstatus', 'Not confirmed')
PC = tok('payer', 'The couple'); P1F = tok('payer', 'Partner 1 family'); P2F = tok('payer', 'Partner 2 family')
SP1 = tok('source', 'Partner 1 savings'); SP2 = tok('source', 'Partner 2 savings'); SF1 = tok('source', 'Partner 1 family'); SF2 = tok('source', 'Partner 2 family'); SGIFT = tok('source', 'Cash gifts')
EXPECTED = tok('hstatus', 'Expected')
PCT = tok('tipbasis', 'Percent'); FLAT = tok('tipbasis', 'Flat amount')
PERGUEST = tok('ctype', 'Per guest')
CATERING = tok('category', 'Catering and bar'); RESERVE = tok('category', 'Reserve'); TIPSFEES = tok('category', 'Tips and fees')
OPT_A = tok('dopt', 'Option A: current Saturday')
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
V = lambda label: v(label)

# the money set aside now and the Tips planned and a few shared building blocks
CASH_NOW = '(SUMIFS(%s,%s,%s,%s,"<="&{today})-SUMIFS(%s,%s,"<="&{today}))' % (R('funding', 'amount'), R('funding', 'status'), RECV, R('funding', 'date'), R('payments', 'amount'), R('payments', 'date'))
UNPAID_DUE = 'SUMIFS(%s,%s,"<>"&%s)' % (R('schedule', 'amount_due'), R('schedule', 'status'), PAID)
FUND_OK = 'SUMIFS(%s,%s,"<>"&%s)' % (R('funding', 'amount'), R('funding', 'status'), NOTC)
EXP_TOTAL = 'SUM(%s)' % R('budget', 'expected')
PG0 = 'SUMIFS(%s,%s,%s)' % (R('budget', 'expected'), R('budget', 'cost_type'), PERGUEST)
CAT0 = 'SUMIFS(%s,%s,%s)' % (R('budget', 'expected'), R('budget', 'category'), CATERING)
H0 = '{set:headcount}'
def BILLED(h): return 'MAX(%s,{set:min_guarantee})' % h
def SEATS(h): return '(ROUNDUP(%s/{set:table_size},0)*{set:table_size})' % h
def TOTAL_AT(h):
    """total wedding cost at headcount h: fixed lines stay, catering follows the guaranteed headcount, other per-guest lines follow the tables"""
    return '(%s-%s+IFERROR(%s/%s*%s,0)+IFERROR((%s-%s)/%s*%s,0))' % (EXP_TOTAL, PG0, CAT0, BILLED(H0), BILLED(h), PG0, CAT0, SEATS(H0), SEATS(h))

settings = [
    S('couple', 'Your names as the couple', 'text', COUPLE),
    S('wedding_day', 'Wedding day', 'date', iso(WEDDING_DAY)),
    S('total_budget', 'Total budget, your own number', 'money', TOTAL_BUDGET),
    S('reserve_pct', 'Reserve as a share of the budget, typical, edit', 'pct', RESERVE_PCT),
    S('hidden_cost_pct', 'Hidden costs as a share of spend, typical, edit', 'pct', HIDDEN_COST_PCT),
    S('headcount', 'Headcount for costing: your forecast from the guest list', 'int', 118),
    S('headcount_low', 'Low headcount for the Best case, your estimate', 'int', 100),
    S('headcount_high', 'High headcount for the Worst case, your estimate', 'int', 135),
    S('min_guarantee', 'Guests you pay for at least, check your contract', 'int', 100),
    S('table_size', 'Guests per table, typical, edit', 'int', TABLE_SIZE),
    S('cost_per_guest_target', 'Cost per guest you aim for, your own number', 'money', COST_PER_GUEST_TARGET),
    S('cpg_benchmark', 'Cost per guest, a typical starting value, edit', 'money', COST_PER_GUEST_BENCHMARK),
    S('tip_pct', 'Tip percent, optional, varies by market, typical, edit', 'pct', TIP_PCT),
    S('priority_gap', 'Points of difference you flag, your own number', 'int', PRIORITY_GAP),
    S('priority_swing', 'Share each priority point moves a budget band, typical, edit', 'pct', 0.10),
    S('over_pct', 'Share over plan that counts as Over, typical, edit', 'pct', 0.10),
    S('cash_floor', 'Cash you keep at each month end, your own number', 'money', 0),
    S('move_days', 'Days a vendor may let a payment move later, ask each vendor', 'int', 30),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 budget -------------------------------------------------------------------
tables.append(T('budget', 'Budget', 'Budget', 'One row per budget category: planned, committed (signed contracts) and paid; still due, variance and the status fill in by themselves. Event costs paid directly sit on the Other events line.', [
    C('line_id', 'Line ID', 'text', 9, required=True), LST('category', 'Category', 'category', 24), C('planned', 'Planned', 'money', 11), C('committed', 'Committed', 'money', 11), C('paid', 'Paid', 'money', 11),
    C('share_couple', 'Couple share', 'pct', 10), C('share_p1_family', 'Partner 1 family share', 'pct', 10), C('share_p2_family', 'Partner 2 family share', 'pct', 10), C('priority', 'Priority 1 to 5', 'int', 9),
    CA('still_due', 'Still due', 'money', '{col:committed}-{col:paid}', 11), CA('expected', 'Expected cost', 'money', 'MAX({col:planned},{col:committed})', 11),
    CA('variance', 'Variance', 'money', 'IF({col:committed}=0,0,{col:committed}-{col:planned})', 11),
    CA('variance_pct', 'Variance percent', 'pct', 'IF({col:planned}>0,{col:variance}/{col:planned},0)', 10),
    CA('status', 'Status', 'text', 'IF({col:variance}<=0,%s,IF({col:variance_pct}<={set:over_pct},%s,%s))' % (V('On track'), V('Watch'), V('Over')), 10),
    CA('cost_type', 'Cost type', 'text', LKT('bands.cost_type', 'bands.category', 'category'), 10),
    CA('hidden_expected', 'Hidden costs expected', 'money', 'SUMIFS(%s,%s,{col:category},%s,%s)' % (R('hidden', 'expected'), R('hidden', 'category'), R('hidden', 'status'), EXPECTED), 12),
    CA('vendor_total', 'Vendor contracts', 'money', 'SUMIFS(%s,%s,{col:category})' % (R('vendors', 'contract_total'), R('vendors', 'category')), 12),
    CA('final_due', 'Final balances due', 'money', 'SUMIFS(%s,%s,{col:category},%s,%s,%s,"<>"&%s)' % (R('schedule', 'amount_due'), R('schedule', 'category'), R('schedule', 'kind'), FB, R('schedule', 'status'), PAID), 12),
    CA('total_planned', 'Planned total', 'money', 'SUM({range:budget.planned})', 11), CA('total_paid', 'Paid total', 'money', 'SUM({range:budget.paid})', 11),
    CA('total_still_due', 'Still due total', 'money', 'SUM({range:budget.still_due})', 11), CA('true_total', 'True budget', 'money', 'SUM(%s)' % R('truebud', 'true_budget'), 11),
    CA('cost_per_guest', 'Cost per guest', 'money', 'IFERROR(ROUND(SUM({range:budget.expected})/{set:headcount},0),0)', 11),
    SC('ph_over', 'Partner phone if over plan', '{col:variance}>0', D.P2_PHONE),
    SC('ph_first_p2', 'Partner phone, first row', '{col:line_id}=INDEX({range:budget.line_id},1)', D.P2_PHONE),
    SC('ph_parent', 'Parent phone, first row', '{col:line_id}=INDEX({range:budget.line_id},1)', D.PAR1_PHONE), CPL()],
    D.budget_d(), 60, [A('status', '= ' + V('Over'), 'bad'), A('status', '= ' + V('Watch'), 'warn'), A('status', '= ' + V('On track'), 'good')]))

# 2 payers -------------------------------------------------------------------
tables.append(T('payers', 'Payers', 'Payers', 'Who pays for the wedding and each payer\'s agreed share of the total budget. Your own agreement: edit the shares and amounts.', [
    LST('payer', 'Payer', 'payerx', 24, required=True), C('share', 'Agreed share', 'pct', 12), C('agreed_amount', 'Agreed amount', 'money', 14)], D.payers_d(), 20))

# 3 funding ------------------------------------------------------------------
FAM = 'OR({col:source}=%s,{col:source}=%s)' % (SF1, SF2)
tables.append(T('funding', 'Funding Plan', 'Funding Plan', 'Every amount that pays for the wedding: savings each month, family transfers and cash gifts. Only Received and Promised count as funding; Not confirmed cash gifts never do.', [
    C('fund_id', 'Fund ID', 'text', 9, required=True), LST('source', 'Source', 'source', 18), C('date', 'Date', 'date', 11), C('amount', 'Amount', 'money', 11), LST('status', 'Status', 'fstatus', 14),
    CA('payer', 'Payer', 'text', 'IF({col:source}=%s,%s,IF({col:source}=%s,%s,%s))' % (SF1, P1F, SF2, P2F, PC), 16),
    CA('agreed_amount', 'Agreed amount of the payer', 'money', 'IFERROR(INDEX({range:payers.agreed_amount},MATCH({col:payer},{range:payers.payer},0)),0)', 12),
    CA('family_paid', 'Paid so far by the payer', 'money', 'SUMIFS(%s,%s,{col:payer})' % (R('payments', 'amount'), R('payments', 'paid_by')), 12),
    SC('ph_p1next', 'Partner 1 family phone, promised', 'AND({col:source}=%s,{col:status}=%s)' % (SF1, PROM), D.PAR1_PHONE),
    SC('ph_p2next', 'Partner 2 family phone, promised', 'AND({col:source}=%s,{col:status}=%s)' % (SF2, PROM), D.PAR2_PHONE),
    CA('ph_thanks', 'Parent phone, received', 'text', 'IF(AND({col:status}=%s,%s),IF({col:source}=%s,"%s","%s"),"")' % (RECV, FAM, SF1, D.PAR1_PHONE, D.PAR2_PHONE), 18),
    CA('ph_share', 'Parent phone, family rows', 'text', 'IF(%s,IF({col:source}=%s,"%s","%s"),"")' % (FAM, SF1, D.PAR1_PHONE, D.PAR2_PHONE), 18),
    CA('ph_saving', 'Partner phone, savings promised', 'text', 'IF(AND({col:status}=%s,OR({col:source}=%s,{col:source}=%s)),IF({col:source}=%s,"%s","%s"),"")' % (PROM, SP1, SP2, SP1, D.P1_PHONE, D.P2_PHONE), 18),
    CPL()],
    D.funding_d(), 100, [A('status', '= ' + RECV, 'good'), A('status', '= ' + NOTC, 'warn')]))

# 4 funding summary ----------------------------------------------------------
tables.append(T('fsum', 'Funding Summary', 'Funding Summary', 'One row per funding source: the money received and the money promised, added up from the Funding Plan.', [
    LST('source', 'Source', 'source', 20, required=True),
    CA('received', 'Received', 'money', 'SUMIFS(%s,%s,{col:source},%s,%s)' % (R('funding', 'amount'), R('funding', 'source'), R('funding', 'status'), RECV), 12),
    CA('promised', 'Promised', 'money', 'SUMIFS(%s,%s,{col:source},%s,%s)' % (R('funding', 'amount'), R('funding', 'source'), R('funding', 'status'), PROM), 12)], D.fsum_d(), 20))

# 5 payment schedule ---------------------------------------------------------
UNP = '{col:status}<>%s' % PAID
EARLIER = '(({range:schedule.due_date}<{col:due_date})+({range:schedule.due_date}={col:due_date})*({range:schedule.pay_id}<{col:pay_id})>0)'
UNPAID_ARR = '({range:schedule.status}<>%s)*({range:schedule.pay_id}<>"")' % PAID
VPH = lambda name, label, vendor, cond: CA(name, label, 'text', 'IF(AND({col:vendor}=%s,%s),{col:vendor_phone},"")' % (VN(vendor), cond), 18)
PAIDROW = '{col:amount_paid}>0'
UNPFB = 'AND({col:status}<>%s,{col:kind}=%s)' % (PAID, FB)
tables.append(T('schedule', 'Payment Schedule', 'Payment Schedule', 'Every deposit, instalment and final balance with its due date, payer and status; days to due, a flag, the money set aside on the due date and any shortfall fill in by themselves.', [
    C('pay_id', 'Pay ID', 'text', 9, required=True), C('vendor_id', 'Vendor ID', 'text', 9), LST('vendor', 'Vendor', 'vname', 22), LST('category', 'Category', 'category', 24), LST('kind', 'Kind', 'paykind', 12),
    C('due_date', 'Due date', 'date', 11), C('amount_due', 'Amount due', 'money', 11), LST('payer', 'Payer', 'payer', 16), C('paid_on', 'Paid on', 'date', 11), C('amount_paid', 'Amount paid', 'money', 11),
    LST('method', 'Method', 'method', 14), LST('status', 'Status', 'paystatus', 11), LST('paid_by', 'Paid by', 'payer', 16),
    CA('days_to_due', 'Days to due', 'int', 'IF(%s,{col:due_date}-{today},"")' % UNP, 9),
    CA('flag', 'Flag', 'text', 'IF({col:status}=%s,%s,IF({col:days_to_due}<0,%s,IF({col:days_to_due}<=14,%s,%s)))' % (PAID, V('Paid'), V('Late'), V('Due soon'), V('On time')), 10),
    CA('seq', 'Order of unpaid', 'int', 'IF(%s,SUMPRODUCT(%s*%s)+1,"")' % (UNP, UNPAID_ARR, EARLIER), 9),
    CA('cash_at_due', 'Set aside on due date', 'money', 'IF(%s,SUMIFS(%s,%s,"<>"&%s,%s,"<="&MAX({col:due_date},{today}))-SUM(%s)-SUMPRODUCT(%s*%s*{range:schedule.amount_due}),"")' % (
        UNP, R('funding', 'amount'), R('funding', 'status'), NOTC, R('funding', 'date'), R('payments', 'amount'), UNPAID_ARR, EARLIER), 12),
    CA('fb_short', 'Final balance short by', 'money', 'IF(%s,IF({col:kind}=%s,MAX(0,{col:amount_due}-{col:cash_at_due}),""),"")' % (UNP, FB), 11),
    CA('short_date', 'Date of a final balance not covered', 'date', 'IF({col:fb_short}="","",IF({col:fb_short}>0,{col:due_date},""))', 11),
    CA('mover_score', 'Move score', 'money', 'IF(%s,IFERROR(IF({col:due_date}<EDATE(SMALL(%s,1),1),{col:amount_due}*IF({col:kind}=%s,1,IF({col:kind}=%s,0.5,0.25)),""),""),"")' % (UNP, R('cash', 'neg_month'), INST, DEP), 10),
    CA('vendor_phone', 'Vendor phone', 'text', LKT('vendors.phone', 'vendors.vendor_id', 'vendor_id'), 18),
    CA('vendor_total', 'Vendor contract total', 'money', LKN('vendors.contract_total', 'vendors.vendor_id', 'vendor_id'), 11),
    CA('final_date', 'Final balance date of the vendor', 'date', 'IF(SUMIFS({range:schedule.due_date},{range:schedule.vendor_id},{col:vendor_id},{range:schedule.kind},%s)=0,"",SUMIFS({range:schedule.due_date},{range:schedule.vendor_id},{col:vendor_id},{range:schedule.kind},%s))' % (FB, FB), 11),
    CA('moved_date', 'Date if moved later', 'date', 'IF({col:due_date}="","",{col:due_date}+{set:move_days})', 11),
    CA('cash', 'Money set aside now', 'money', CASH_NOW, 11),
    VPH('ph_v_paid', 'Venue phone, paid', 'Venue', PAIDROW), VPH('ph_v_inv', 'Venue phone, final balance', 'Venue', UNPFB),
    VPH('ph_c_paid', 'Caterer phone, paid', 'Caterer', PAIDROW), VPH('ph_c_move', 'Caterer phone, instalment', 'Caterer', 'AND({col:status}<>%s,{col:kind}=%s)' % (PAID, INST)),
    VPH('ph_ph_paid', 'Photographer phone, paid', 'Photographer', PAIDROW),
    VPH('ph_f_inst', 'Florist phone, instalment', 'Florist', 'AND({col:status}<>%s,{col:kind}=%s)' % (PAID, INST)),
    VPH('ph_b_paid', 'Band or DJ phone, paid', 'Band or DJ', PAIDROW), VPH('ph_att', 'Attire shop phone, final balance', 'Attire shop', UNPFB),
    VPH('ph_r_dep', 'Rentals phone, deposit', 'Rentals', 'AND({col:kind}=%s,%s)' % (DEP, PAIDROW)),
    VPH('ph_d_fb', 'Coordinator phone, final balance', 'Day-of coordinator', UNPFB), VPH('ph_h_dep', 'Hotel phone, paid', 'Hotel room block', PAIDROW),
    VPH('ph_o_paid', 'Officiant phone, paid', 'Officiant', PAIDROW),
    SC('ph_partner_att', 'Partner phone, attire balance', 'AND({col:vendor}='+VN('Attire shop')+',%s)' % UNPFB, D.P2_PHONE), CPL()],
    D.schedule_d(), 120, [A('flag', '= ' + V('Late'), 'bad'), A('flag', '= ' + V('Due soon'), 'warn'), A('flag', '= ' + V('Paid'), 'good')]))

# 6 payments -----------------------------------------------------------------
tables.append(T('payments', 'Payments', 'Payments', 'One row per money movement that paid a vendor: a deposit can be paid in two pieces by two payers. The vendor fills in from the schedule.', [
    C('payment_id', 'Payment ID', 'text', 9, required=True), C('pay_id', 'Pay ID', 'text', 9), C('date', 'Date', 'date', 11), C('amount', 'Amount', 'money', 11), LST('paid_by', 'Paid by', 'payer', 16), LST('method', 'Method', 'method', 14),
    CA('vendor', 'Vendor', 'text', LKT('schedule.vendor', 'schedule.pay_id', 'pay_id'), 22)], D.payments_d(), 100))

# 7 vendors ------------------------------------------------------------------
tables.append(T('vendors', 'Vendors', 'Vendors', 'One row per vendor with its contract total, status and payer; what is scheduled, paid and still due fills in from the Payment Schedule.', [
    C('vendor_id', 'Vendor ID', 'text', 9, required=True), LST('vendor', 'Vendor', 'vname', 22), LST('category', 'Category', 'category', 24), C('contract_total', 'Contract total', 'money', 12), LST('status', 'Status', 'vstatus', 14),
    LST('payer', 'Payer', 'payer', 16), C('booked_on', 'Booked on', 'date', 11), C('phone', 'Contact phone', 'text', 18),
    CA('scheduled', 'Scheduled payments', 'money', 'SUMIFS(%s,%s,{col:vendor_id})' % (R('schedule', 'amount_due'), R('schedule', 'vendor_id')), 12),
    CA('paid_so_far', 'Paid so far', 'money', 'SUMIFS(%s,%s,{col:vendor_id})' % (R('schedule', 'amount_paid'), R('schedule', 'vendor_id')), 12),
    CA('still_due', 'Still due', 'money', '{col:scheduled}-{col:paid_so_far}', 11), CA('headcount', 'Headcount', 'int', '{set:headcount}', 9),
    SC('ph_f_rev', 'Florist phone', '{col:vendor}='+VN('Florist')+'', '{col:phone}'), SC('ph_c_head', 'Caterer phone', '{col:vendor}='+VN('Caterer')+'', '{col:phone}'), SC('ph_stat', 'Stationery printer phone', '{col:vendor}='+VN('Stationery printer')+'', '{col:phone}'), CPL()], D.vendors_d(), 60, [A('status', '= ' + tok('vstatus', 'Booked'), 'good')]))

# 8 hidden costs -------------------------------------------------------------
tables.append(T('hidden', 'Hidden Costs', 'Hidden Costs', 'Extra costs that are not in the first quote: what you expect, whether it is still expected, paid or not needed, and the budget category it belongs to.', [
    C('hidden_id', 'Hidden ID', 'text', 9, required=True), C('item', 'Item', 'text', 34), C('expected', 'Expected', 'money', 11), LST('status', 'Status', 'hstatus', 12), LST('category', 'Category', 'category', 24),
    CA('counted', 'Counted in the true budget', 'money', 'IF({col:status}=%s,{col:expected},0)' % EXPECTED, 12)], D.hidden_d(), 60, [A('status', '= ' + EXPECTED, 'warn')]))

# 9 tips ---------------------------------------------------------------------
tables.append(T('tips', 'Tips', 'Tips', 'One row per vendor: whether a gratuity is already included, the tip basis (optional, tipping varies by market), who hands the envelope out and whether it is ready; the planned tip fills in.', [
    C('tip_id', 'Tip ID', 'text', 9, required=True), C('vendor_id', 'Vendor ID', 'text', 9), LST('vendor', 'Vendor', 'vname', 22), C('gratuity_included', 'Gratuity included', 'bool', 10), LST('basis', 'Basis', 'tipbasis', 12),
    C('pct', 'Percent', 'pct', 9), C('flat', 'Flat amount', 'int', 10), C('bill', 'Vendor bill', 'money', 11), LST('handed_by', 'Handed out by', 'owner', 18), C('envelope_ready', 'Envelope ready', 'bool', 10),
    CA('planned_tip', 'Planned tip', 'money', 'IF({col:gratuity_included}=%s,0,IF({col:basis}=%s,ROUND({col:bill}*IF({col:pct}>0,{col:pct},{set:tip_pct}),0),IF({col:basis}=%s,{col:flat},0)))' % (YES, PCT, FLAT), 10),
    CA('category', 'Budget category', 'text', LKT('vendors.category', 'vendors.vendor_id', 'vendor_id'), 22),
    CA('all_tips', 'Tips total', 'money', 'SUM({range:tips.planned_tip})', 10), CA('tip_count', 'Envelopes to hand out', 'int', 'COUNTIFS({range:tips.planned_tip},">0")', 9),
    CA('ready_count', 'Envelopes ready', 'int', 'COUNTIFS({range:tips.planned_tip},">0",{range:tips.envelope_ready},%s)' % YES, 9), CA('wedding_day', 'Wedding day', 'date', '{set:wedding_day}', 11),
    SC('ph_p2first', 'Partner phone, first row', '{col:tip_id}=INDEX({range:tips.tip_id},1)', D.P2_PHONE), SC('ph_friend', 'Friend helper phone, first row', '{col:tip_id}=INDEX({range:tips.tip_id},1)', D.FRIEND_PHONE),
    SC('ph_parent', 'Parent phone, first row', '{col:tip_id}=INDEX({range:tips.tip_id},1)', D.PAR1_PHONE), CPL()], D.tips_d(), 60))

# 10 priority scores ---------------------------------------------------------
tables.append(T('pscore', 'Priority Scores', 'Priority Scores', 'Each partner scores every area from 1 (least important) to 5 (most important). Score on your own first, then compare.', [
    LST('area', 'Area', 'parea', 26, required=True), C('score_p1', 'Partner 1 score', 'int', 12), C('score_p2', 'Partner 2 score', 'int', 12)], D.pscore_d(), 20))

# 11 priority ranking --------------------------------------------------------
AVG = '(INDEX({range:pscore.score_p1},MATCH({col:area},{range:pscore.area},0))+INDEX({range:pscore.score_p2},MATCH({col:area},{range:pscore.area},0)))/2'
tables.append(T('prank', 'Priority Ranking', 'Priority Ranking', 'The two partners\' scores averaged for each area and ranked, 1 being what matters most to both.', [
    LST('area', 'Area', 'parea', 26, required=True), CA('avg', 'Average score', 'num', 'IFERROR(%s,"")' % AVG, 12),
    CA('rank', 'Rank', 'int', 'IF({col:avg}="","",COUNTIFS({range:prank.avg},">"&{col:avg})+1+SUMPRODUCT(({range:prank.avg}={col:avg})*({range:prank.area}<{col:area})))', 9)], D.prank_d(), 20))

# 12 split bands -------------------------------------------------------------
tables.append(T('bands', 'Split Bands', 'Split Bands', 'Typical starting shares for each category (typical, edit); the suggested amount follows your total budget and both partners\' priorities, and the difference from your plan fills in.', [
    LST('category', 'Category', 'category', 24, required=True), C('typical_share', 'Typical share', 'pct', 10), LST('cost_type', 'Cost type', 'ctype', 10), LST('priority_area', 'Priority area', 'parea', 22),
    CA('planned', 'Planned', 'money', LKN('budget.planned', 'budget.category', 'category'), 11),
    CA('avg_score', 'Average priority score', 'num', 'IFERROR((INDEX({range:pscore.score_p1},MATCH({col:priority_area},{range:pscore.area},0))+INDEX({range:pscore.score_p2},MATCH({col:priority_area},{range:pscore.area},0)))/2,3)', 10),
    CA('weight', 'Weight', 'num', '{col:typical_share}*(1+{set:priority_swing}*({col:avg_score}-3))', 9),
    CA('suggest_share', 'Suggested share', 'pct', 'IFERROR({col:weight}/SUM({range:bands.weight}),0)', 10), CA('suggested', 'Suggested amount', 'money', 'ROUND({set:total_budget}*{col:suggest_share},0)', 11),
    CA('difference', 'Plan less suggested', 'money', '{col:planned}-{col:suggested}', 11),
    CA('gap', 'Partners\' score gap', 'int', 'IFERROR(ABS(INDEX({range:pscore.score_p1},MATCH({col:priority_area},{range:pscore.area},0))-INDEX({range:pscore.score_p2},MATCH({col:priority_area},{range:pscore.area},0))),0)', 9),
    CA('score_by', 'Score by', 'date', '{today}+7', 11),
    SC('ph_score', 'Partner phone, first row', '{col:category}=INDEX({range:bands.category},1)', D.P2_PHONE), SC('ph_gap', 'Partner phone, gap', '{col:gap}>={set:priority_gap}', D.P2_PHONE), CPL()], D.bands_d(), 40))

# 13 cash by month -----------------------------------------------------------
def FIN(src_list, m='{col:month}'):
    return '+'.join('SUMIFS(%s,%s,">="&%s,%s,"<"&EDATE(%s,1),%s,%s,%s,"<>"&%s)' % (R('funding', 'amount'), R('funding', 'date'), m, R('funding', 'date'), m, R('funding', 'source'), s_, R('funding', 'status'), NOTC) for s_ in src_list)
PAYOUT = ('SUMIFS(%s,%s,">="&{col:month},%s,"<"&EDATE({col:month},1))+IF({col:month}<%s,0,SUMIFS(%s,%s,"<>"&%s,%s,">="&IF({col:month}=%s,0,{col:month}),%s,"<"&EDATE({col:month},1)))') % (
    R('payments', 'amount'), R('payments', 'date'), R('payments', 'date'), MS, R('schedule', 'amount_due'), R('schedule', 'status'), PAID, R('schedule', 'due_date'), MS, R('schedule', 'due_date'))
CLOSING = ('SUMIFS(%s,%s,"<"&EDATE({col:month},1),%s,"<>"&%s)-SUMIFS(%s,%s,"<"&EDATE({col:month},1))-IF({col:month}<%s,0,SUMIFS(%s,%s,"<>"&%s,%s,"<"&EDATE({col:month},1)))') % (
    R('funding', 'amount'), R('funding', 'date'), R('funding', 'status'), NOTC, R('payments', 'amount'), R('payments', 'date'), MS, R('schedule', 'amount_due'), R('schedule', 'status'), PAID, R('schedule', 'due_date'))
NEXTDUE = 'SUMIFS(%s,%s,"<>"&%s,%s,">="&EDATE({col:month},1),%s,"<"&EDATE({col:month},2))' % (R('schedule', 'amount_due'), R('schedule', 'status'), PAID, R('schedule', 'due_date'), R('schedule', 'due_date'))
tables.append(T('cash', 'Cash by Month', 'Cash by Month', 'One row per month: money coming in (received and promised), payments going out (paid, plus what is still due), net and closing cash with a flag.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('savings_in', 'Savings in', 'money', FIN([SP1, SP2]), 11), CA('family_in', 'Family transfers in', 'money', FIN([SF1, SF2]), 12), CA('gifts_in', 'Cash gifts in', 'money', FIN([SGIFT]), 11),
    CA('funding_in', 'Total in', 'money', '{col:savings_in}+{col:family_in}+{col:gifts_in}', 11), CA('payments_out', 'Payments out', 'money', PAYOUT, 11),
    CA('net', 'Net', 'money', '{col:funding_in}-{col:payments_out}', 11), CA('closing', 'Closing cash', 'money', CLOSING, 12),
    CA('ahead', 'Closing cash, this month on', 'money', 'IF({col:month}>=%s,{col:closing},"")' % MS, 12),
    CA('neg_month', 'Month below the floor', 'date', 'IF({col:month}<%s,"",IF({col:closing}<{set:cash_floor},{col:month},""))' % MS, 11), CA('short', 'Short by', 'money', 'IF({col:month}<%s,0,MAX(0,{set:cash_floor}-{col:closing}))' % MS, 10),
    CA('flag', 'Flag', 'text', 'IF({col:month}<%s,%s,IF({col:closing}<{set:cash_floor},%s,IF({col:closing}<%s,%s,%s)))' % (MS, V('Past'), V('Negative'), NEXTDUE, V('Tight'), V('Covered')), 10),
    SC('ph_month', 'Partner phone, this month', '{col:month}=%s' % MS, D.P2_PHONE), SC('ph_neg', 'Partner phone, short', '{col:short}>0', D.P2_PHONE), CPL()],
    D.cash_d(), 40, [A('flag', '= ' + V('Negative'), 'bad'), A('flag', '= ' + V('Tight'), 'warn'), A('flag', '= ' + V('Covered'), 'good')]))

# 14 category by payer -------------------------------------------------------
def SHARE(c_): return 'ROUND(IFERROR(INDEX({range:budget.planned},MATCH({col:category},{range:budget.category},0))*INDEX({range:budget.%s},MATCH({col:category},{range:budget.category},0)),0),0)' % c_
tables.append(T('catpay', 'Category by Payer', 'Category by Payer', 'Each category\'s planned amount split between the couple and the two families by the shares you set on the Budget sheet.', [
    LST('category', 'Category', 'category', 24, required=True), CA('planned', 'Planned', 'money', LKN('budget.planned', 'budget.category', 'category'), 11),
    CA('by_couple', 'The couple', 'money', SHARE('share_couple'), 11), CA('by_p1', 'Partner 1 family', 'money', SHARE('share_p1_family'), 12), CA('by_p2', 'Partner 2 family', 'money', SHARE('share_p2_family'), 12)], D.catpay_d(), 40))

# 15 settle-up ---------------------------------------------------------------
tables.append(T('settle', 'Settle-up by Payer', 'Settle-up by Payer', 'For each payer: the agreed share of what has been paid so far and what that payer actually paid, from the Payments sheet.', [
    LST('payer', 'Payer', 'payerx', 24, required=True),
    CA('agreed', 'Agreed share of paid', 'money', 'ROUND(SUM(%s)*IFERROR(INDEX({range:payers.share},MATCH({col:payer},{range:payers.payer},0)),0),0)' % R('payments', 'amount'), 14),
    CA('paid', 'Actually paid', 'money', 'SUMIFS(%s,%s,{col:payer})' % (R('payments', 'amount'), R('payments', 'paid_by')), 14)], D.settle_d(), 20))

# 16 guest cut ladder --------------------------------------------------------
tables.append(T('ladder', 'Guest Cut Ladder', 'Guest Cut Ladder', 'What happens to the cost if you remove guests in steps of five: fixed lines stay, the caterer charges at least the minimum guarantee and tables round up.', [
    LST('step', 'Step', 'cstep', 16, required=True), C('removed', 'Guests removed', 'int', 10),
    CA('headcount', 'Headcount', 'int', 'MAX(0,%s-{col:removed})' % H0, 10), CA('tables', 'Tables', 'int', 'ROUNDUP({col:headcount}/{set:table_size},0)', 8),
    CA('billed', 'Guests charged', 'int', BILLED('{col:headcount}'), 10),
    CA('catering', 'Catering', 'money', 'ROUND(IFERROR(%s/%s*{col:billed},0),0)' % (CAT0, BILLED(H0)), 11),
    CA('other_pg', 'Other per-guest lines', 'money', 'ROUND(IFERROR((%s-%s)/%s*({col:tables}*{set:table_size}),0),0)' % (PG0, CAT0, SEATS(H0)), 12),
    CA('per_guest_cost', 'Per-guest cost', 'money', '{col:catering}+{col:other_pg}', 11), CA('fixed', 'Fixed cost', 'money', 'ROUND(%s-%s,0)' % (EXP_TOTAL, PG0), 11),
    CA('total', 'Total', 'money', '{col:per_guest_cost}+{col:fixed}', 11), CA('saving', 'Saving', 'money', 'ROUND(%s-{col:total},0)' % EXP_TOTAL, 10),
    CA('cost_per_guest', 'Cost per guest', 'money', 'IF({col:headcount}>0,ROUND({col:total}/{col:headcount},0),0)', 10)], D.ladder_d(), 20))

# 17 date options ------------------------------------------------------------
tables.append(T('dates', 'Date Options', 'Date Options', 'Quotes for the big five vendors on each date you are considering, with the lead time you were told. Totals, the saving against your current date and a lead-time flag fill in.', [
    LST('option', 'Option', 'dopt', 34, required=True), LST('category', 'Category', 'category', 24), C('quote', 'Quote', 'money', 11), C('lead_months', 'Lead months', 'int', 9), C('note', 'Note', 'text', 30), C('option_date', 'Date of the option', 'date', 11),
    CA('option_total', 'Option total', 'money', 'SUMIFS({range:dates.quote},{range:dates.option},{col:option})', 12),
    CA('vs_current', 'Against the current date', 'money', '{col:option_total}-SUMIFS({range:dates.quote},{range:dates.option},%s)' % OPT_A, 12),
    CA('days_to', 'Days to the date', 'int', '{col:option_date}-{today}', 9), CA('months_to', 'Months to the date', 'num', 'ROUND({col:days_to}/30.4,1)', 9),
    CA('lead_flag', 'Lead time', 'text', 'IF({col:months_to}>={col:lead_months},%s,%s)' % (V('On time'), V('Check lead time')), 14),
    SC('ph_p2', 'Partner phone', '{col:option}=INDEX({range:dates.option},1)', D.P2_PHONE), CPL()], D.dates_d(), 40, [A('lead_flag', '= ' + V('Check lead time'), 'warn')]))

# 18 rebalance candidates ----------------------------------------------------
BP = 'IFERROR(INDEX({range:budget.planned},MATCH({col:category},{range:budget.category},0)),0)'
BC = 'IFERROR(INDEX({range:budget.committed},MATCH({col:category},{range:budget.category},0)),0)'
tables.append(T('rebal', 'Rebalance Candidates', 'Rebalance Candidates', 'Where money can come from when a line runs over: how easy each category is to cut (1 hard to 5 easy, your own score), the room left in the plan and a rank.', [
    LST('category', 'Category', 'category', 24, required=True), C('flex', 'Flexibility 1 to 5', 'int', 10),
    CA('committed_share', 'Committed share of plan', 'pct', 'IF(%s>0,%s/%s,0)' % (BP, BC, BP), 11), CA('room', 'Room to cut', 'money', 'MAX(0,%s-%s)' % (BP, BC), 11),
    CA('score', 'Cut score', 'money', '{col:room}*{col:flex}', 10),
    CA('rank', 'Rank', 'int', 'IF({col:score}="","",COUNTIFS({range:rebal.score},">"&{col:score})+1+SUMPRODUCT(({range:rebal.score}={col:score})*({range:rebal.category}<{col:category})))', 8)], D.rebal_d(), 40))

# 19 next payments -----------------------------------------------------------
def DUEIN(n): return 'SUMIFS(%s,%s,"<>"&%s,%s,"<="&{today}+%d)' % (R('schedule', 'amount_due'), R('schedule', 'status'), PAID, R('schedule', 'due_date'), n)
tables.append(T('due60', 'Next Payments Due', 'Next Payments Due', 'The next 15 unpaid payments in date order with the days left and a flag for the 30 and 60 day windows. It fills in from the Payment Schedule.', [
    C('seqno', 'Order', 'int', 8, required=True), CA('pay_id', 'Pay ID', 'text', 'IFERROR(INDEX({range:schedule.pay_id},MATCH({col:seqno},{range:schedule.seq},0))&"","")', 9),
    CA('vendor', 'Vendor', 'text', 'IFERROR(INDEX({range:schedule.vendor},MATCH({col:seqno},{range:schedule.seq},0))&"","")', 22),
    CA('due_date', 'Due date', 'date', LKD('schedule.due_date', 'schedule.pay_id', 'pay_id'), 11), CA('amount', 'Amount', 'money', LKN('schedule.amount_due', 'schedule.pay_id', 'pay_id'), 11),
    CA('days_left', 'Days left', 'int', 'IF({col:due_date}="","",{col:due_date}-{today})', 9),
    CA('flag', 'Flag', 'text', 'IF({col:due_date}="","",IF({col:days_left}<0,%s,IF({col:days_left}<=30,%s,IF({col:days_left}<=60,%s,%s))))' % (V('Overdue'), V('Within 30 days'), V('Within 60 days'), V('Later')), 14),
    CA('due30', 'Due in 30 days', 'money', DUEIN(30), 11), CA('due60', 'Due in 60 days', 'money', DUEIN(60), 11), CA('due90', 'Due in 90 days', 'money', DUEIN(90), 11),
    CA('overdue', 'Overdue now', 'money', 'SUMIFS(%s,%s,"<>"&%s,%s,"<"&{today})' % (R('schedule', 'amount_due'), R('schedule', 'status'), PAID, R('schedule', 'due_date')), 11)],
    D.due60_d(), 40, [A('flag', '= ' + V('Overdue'), 'bad'), A('flag', '= ' + V('Within 30 days'), 'warn')]))

# 20 true budget by category -------------------------------------------------
tables.append(T('truebud', 'True Budget by Category', 'True Budget by Category', 'Plan plus the hidden costs you still expect plus planned tips for each category. The Tips and fees line already holds money for tips, so it is credited.', [
    LST('category', 'Category', 'category', 24, required=True), CA('planned', 'Planned', 'money', LKN('budget.planned', 'budget.category', 'category'), 11),
    CA('hidden_exp', 'Hidden costs expected', 'money', 'SUMIFS(%s,%s,{col:category},%s,%s)' % (R('hidden', 'expected'), R('hidden', 'category'), R('hidden', 'status'), EXPECTED), 12),
    CA('planned_tips', 'Planned tips', 'money', 'IF({col:category}=%s,-MIN(SUM(%s),{col:planned}),SUMIFS(%s,%s,{col:category}))' % (TIPSFEES, R('tips', 'planned_tip'), R('tips', 'planned_tip'), R('tips', 'category')), 11),
    CA('true_budget', 'True budget', 'money', '{col:planned}+{col:hidden_exp}+{col:planned_tips}', 11),
    CA('share', 'Share of total', 'pct', 'IFERROR({col:true_budget}/SUM({range:truebud.true_budget}),0)', 10)], D.truebud_d(), 40))
for _t in tables: _t['rows'] = max(50, _t['rows'])
assert len(tables) == 20
