"""Doula business suite part 3: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du3_lists import *
import du3_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IF(%s=0,"",%s)' % (LKN(src, kc, my), LKN(src, kc, my))
def LKX(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),"")' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def CO(): return CA('company', 'Company', 'text', '{set:company}', 22)
def OWNER_PH(): return CA('owner_phone', 'Owner-doula phone', 'text', '"%s"' % D.OWNER_PHONE, 18)
def ADMIN_PH(): return CA('admin_phone', 'Admin phone', 'text', '"%s"' % D.ADMIN_PHONE, 18)
def ACC_PH(): return CA('accountant_phone', 'Accountant phone', 'text', '"%s"' % D.ACCOUNTANT_PHONE, 18)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YES = '{list:yesno.yes}'
UN, PD = tok('istatus', 'Unpaid'), tok('istatus', 'Paid')
PIF, INS = tok('plan', 'Pay in full'), tok('plan', 'Instalments')
CAN, SIG, COM = tok('ctstatus', 'Cancelled'), tok('ctstatus', 'Signed'), tok('ctstatus', 'Completed')
KDEP, KBAL, KINS, KHRS, KADD = [tok('paykind', k) for k in ('Deposit', 'Balance', 'Instalment', 'Hours invoice', 'Add-on')]
B0, B1, B2, B3 = [tok('band', b) for b in AGE[:4]]
KPP = tok('ckind', 'Postpartum')
PAY3 = '+'.join('SUMIFS({range:payments.amount},{range:payments.client_id},{col:client_id},{range:payments.kind},%s)' % k for k in (KDEP, KBAL, KINS))
COND_U = '({range:instalments.client_id}={col:client_id})*({range:instalments.status}=%s)' % UN
MINU = 'SUMPRODUCT(MIN(%s*{range:instalments.due_date}+(1-%s)*99999))' % (COND_U, COND_U)
MAXA = 'SUMPRODUCT(MAX(({range:instalments.client_id}={col:client_id})*{range:instalments.due_date}))'
MINA = 'SUMPRODUCT(MIN(({range:instalments.client_id}={col:client_id})*{range:instalments.due_date}+(1-({range:instalments.client_id}={col:client_id}))*99999))'
INM = '{range:%s},">="&{col:month},{range:%s},"<"&EDATE({col:month},1)'

settings = [
    S('company', 'Your business name', 'text', COMPANY), S('oncall_before_days', 'On-call window starts this many days before the due date', 'int', ONCALL_BEFORE),
    S('balance_weeks', 'Balance due this many weeks before the due date', 'int', BALANCE_WEEKS), S('instalment_days', 'Days between payment plan instalments', 'int', 28),
    S('deposit_days', 'Days a client has to pay the deposit', 'int', 7), S('reminder_days', 'Send a balance reminder this many days before', 'int', 7),
    S('on_time_share', 'Share of money that arrives on time, your own history', 'pct', 0.85), S('cancel_rate_max', 'Highest change and cancellation rate you accept', 'pct', CANCEL_RATE_MAX),
    S('cash_floor', 'Cash you never let the bank balance fall below', 'money', CASH_FLOOR), S('cash_cover_months', 'Months of costs you want covered by cash', 'int', CASH_COVER_MONTHS),
    S('pack_expiry_days', 'Days an hour pack runs after the due date', 'int', PACK_EXPIRY_DAYS), S('pack_near_days', 'Days before expiry that count as near expiry', 'int', 45),
    S('alloc_prenatal', 'Share earned in the prenatal phase, example', 'pct', ALLOC['prenatal']), S('alloc_oncall', 'Share earned inside the on-call window, example', 'pct', ALLOC['oncall']),
    S('alloc_birth', 'Share earned at the birth, example', 'pct', ALLOC['birth']), S('alloc_postpartum', 'Share earned in the weeks after, example', 'pct', ALLOC['postpartum']),
    S('card_fee_pct', 'Fee your payment provider takes on a card payment', 'pct', 0.03), S('window_entry_days', 'Days ahead that count as entering the window', 'int', 14),
]
assert 3 <= len(settings) <= 20

tables = []
# ---------------------------------------------------------------- 1 contracts
tables.append(T('contracts', 'Contracts', 'Contracts with price, deposit, balance and plan',
    'One row per signed package: price, deposit, balance due date and plan; paid so far, the balance outstanding, what is overdue, the ageing band and the message fields fill in by themselves.', [
    C('contract_id', 'Contract ID', 'text', 10, required=True), REF('client_id', 'Client ID', 'clients.client_id', 10), REF('client', 'Client', 'clients.client', 24), LST('package', 'Package', 'package', 22), LST('kind', 'Kind', 'ckind', 11),
    C('list_price', 'List price', 'money', 11), LST('discount', 'Discount', 'discount', 16), C('price', 'Price', 'money', 11), C('deposit', 'Deposit', 'money', 11), C('signed_on', 'Signed on', 'date', 11),
    C('deposit_paid_on', 'Deposit paid on', 'date', 11), C('balance_due', 'Balance due', 'date', 11), C('balance_paid_on', 'Balance paid on', 'date', 11), LST('plan', 'Plan', 'plan', 12), C('instalments', 'Instalments', 'int', 9),
    LST('status', 'Status', 'ctstatus', 11),
    CA('paid_to_date', 'Paid so far', 'money', 'ROUND(%s,2)' % PAY3, 11),
    CA('balance', 'Balance outstanding', 'money', 'IF({col:status}=%s,0,MAX(0,ROUND({col:price}-{col:paid_to_date},2)))' % CAN, 12),
    CA('next_due', 'Next payment due', 'date', 'IF({col:balance}<=0,"",IF({col:plan}=%s,IF({col:balance_due}>0,{col:balance_due},""),IF(%s>=99999,"",%s)))' % (PIF, MINU, MINU), 11),
    CA('overdue_amount', 'Overdue amount', 'money', 'IF(OR({col:next_due}="",{col:balance}<=0),0,IF({col:plan}=%s,IF({col:next_due}<{today},{col:balance},0),SUMIFS({range:instalments.amount},{range:instalments.client_id},{col:client_id},{range:instalments.status},%s,{range:instalments.due_date},"<"&{today})))' % (PIF, UN), 12),
    CA('overdue_days', 'Days overdue', 'int', 'IF({col:overdue_amount}>0,{today}-{col:next_due},0)', 9),
    CA('due_30', 'Due in the next 30 days', 'money', 'IF({col:balance}<=0,0,IF({col:plan}=%s,IF(AND({col:balance_due}>={today},{col:balance_due}<={today}+30),{col:balance},0),SUMIFS({range:instalments.amount},{range:instalments.client_id},{col:client_id},{range:instalments.status},%s,{range:instalments.due_date},">="&{today},{range:instalments.due_date},"<="&({today}+30))))' % (PIF, UN), 12),
    CA('ageing_band', 'Ageing band', 'text', 'IF({col:overdue_days}>60,%s,IF({col:overdue_days}>30,%s,IF({col:overdue_days}>0,%s,IF({col:due_30}>0,%s,""))))' % (B3, B2, B1, B0), 20),
    CA('due_week', 'Week of the balance', 'int', 'IF(AND({col:plan}=%s,{col:balance}>0,{col:balance_due}>={today}),INT(({col:balance_due}-{today})/7)+1,"")' % PIF, 9),
    CA('deposit_due', 'Deposit due', 'date', '{col:signed_on}+{set:deposit_days}', 11),
    CA('days_to_deposit', 'Days to pay the deposit', 'int', 'IF({col:deposit_paid_on}>0,{col:deposit_paid_on}-{col:signed_on},"")', 9),
    CA('days_late_balance', 'Days late on the balance', 'int', 'IF(AND({col:balance_paid_on}>0,{col:balance_due}>0),MAX(0,{col:balance_paid_on}-{col:balance_due}),"")', 9),
    CA('window_start', 'On-call start', 'date', LKD('clients.oncall_start', 'clients.client_id', 'client_id'), 11),
    CA('phone', 'Phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18), CO(), OWNER_PH()],
    D.contracts_d(), 400, [A('ageing_band', '= ' + B3, 'bad'), A('ageing_band', '= ' + B2, 'bad'), A('ageing_band', '= ' + B1, 'warn'), A('status', '= ' + CAN, 'warn'), A('status', '= ' + COM, 'good')]))
# ---------------------------------------------------------------- 2 instalments
tables.append(T('instalments', 'Instalments', 'Instalments with due date, payment and days late',
    'One row per instalment of a payment plan: due date, amount and the date it was paid; the days overdue, the days late, the ageing band and the message fields fill in by themselves.', [
    C('inst_id', 'Instalment ID', 'text', 10, required=True), REF('client_id', 'Client ID', 'clients.client_id', 10), REF('client', 'Client', 'clients.client', 24), C('no', 'No', 'int', 6), C('of', 'Of', 'int', 6),
    C('due_date', 'Due date', 'date', 11), C('amount', 'Amount', 'money', 11), C('paid_on', 'Paid on', 'date', 11), LST('status', 'Status', 'istatus', 10),
    CA('days_overdue', 'Days overdue', 'int', 'IF({col:status}=%s,MAX(0,{today}-{col:due_date}),0)' % UN, 9),
    CA('days_late', 'Days late', 'int', 'IF({col:paid_on}>0,MAX(0,{col:paid_on}-{col:due_date}),{col:days_overdue})', 9),
    CA('ageing_band', 'Ageing band', 'text', 'IF({col:days_overdue}>60,%s,IF({col:days_overdue}>30,%s,IF({col:days_overdue}>0,%s,IF(AND({col:status}=%s,{col:due_date}<={today}+30),%s,""))))' % (B3, B2, B1, UN, B0), 20),
    CA('due_week', 'Week due', 'int', 'IF(AND({col:status}=%s,{col:due_date}>={today}),INT(({col:due_date}-{today})/7)+1,"")' % UN, 8),
    CA('client_unpaid', 'Unpaid by this client', 'money', 'SUMIFS({range:instalments.amount},{range:instalments.client_id},{col:client_id},{range:instalments.status},%s)' % UN, 12),
    CA('phone', 'Phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18), CO(), OWNER_PH()],
    D.instalments_d(), 450, [A('days_overdue', '> 60', 'bad'), A('days_overdue', '> 0', 'warn'), A('status', '= ' + PD, 'good')]))
# ---------------------------------------------------------------- 3 payments
tables.append(T('payments', 'Payments', 'Payments received by kind and method',
    'One row per payment received: date, client, kind (deposit, balance, instalment, hours invoice or add-on), amount and method; the provider fee and the message fields fill in by themselves.', [
    C('payment_id', 'Payment ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), REF('client_id', 'Client ID', 'clients.client_id', 10), REF('client', 'Client', 'clients.client', 24),
    LST('kind', 'Kind', 'paykind', 14), C('amount', 'Amount', 'money', 11), LST('method', 'Method', 'method', 14),
    CA('fee_cost', 'Provider fee', 'money', 'IF(OR({col:method}=%s,{col:method}=%s),ROUND({col:amount}*{set:card_fee_pct},2),0)' % (tok('method', 'Card payment'), tok('method', 'Payment link')), 11),
    CA('phone', 'Phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18), CO(), ADMIN_PH()],
    D.payments_d(), 900, [A('kind', '= ' + KDEP, 'good')]))
# ---------------------------------------------------------------- 4 clients
tables.append(T('clients', 'Clients', 'Clients with package, due date and on-call start',
    'One row per client: package, estimated due date (a date the client gives), doula, status and on-call dates; the days to the window, the balance outstanding and the window check fill in by themselves.', [
    C('client_id', 'Client ID', 'text', 10, required=True), C('client', 'Client', 'text', 24), LST('kind', 'Kind', 'ckind', 11), LST('package', 'Package', 'package', 22), C('edd', 'Estimated due date', 'date', 11),
    LST('doula', 'Doula', 'doula', 17), C('signed_on', 'Signed on', 'date', 11), LST('status', 'Status', 'cstatus', 15), C('oncall_start', 'On-call start', 'date', 11), C('oncall_end', 'On-call end', 'date', 11),
    C('attended_on', 'Birth attended on', 'date', 11), C('phone', 'Phone', 'text', 18),
    CA('days_to_window', 'Days to the window', 'int', 'IF({col:oncall_start}>0,{col:oncall_start}-{today},"")', 9),
    CA('price', 'Price', 'money', LKN('contracts.price', 'contracts.client_id', 'client_id'), 11), CA('paid', 'Paid so far', 'money', LKN('contracts.paid_to_date', 'contracts.client_id', 'client_id'), 11),
    CA('outstanding', 'Balance outstanding', 'money', LKN('contracts.balance', 'contracts.client_id', 'client_id'), 12),
    CA('window_check', 'Window check', 'text', 'IF(AND({col:oncall_start}>0,{col:oncall_start}<={today},{col:status}<>%s,{col:status}<>%s,{col:outstanding}>0),%s,IF(AND({col:status}=%s,{col:oncall_start}>={today},{col:oncall_start}<={today}+{set:window_entry_days}),IF({col:outstanding}>0,%s,%s),%s))' % (
        tok('cstatus', 'Completed'), tok('cstatus', 'Cancelled'), ca('Unpaid inside the window'), tok('cstatus', 'Booked'), ca('Collect before the window'), ca('Paid before the window'), ca('Window not near')), 22),
    CA('soon_days', 'Days to window if unpaid', 'int', 'IF(AND({col:status}=%s,{col:outstanding}>0,{col:oncall_start}>={today}),{col:days_to_window},"")' % tok('cstatus', 'Booked'), 9), CO(), OWNER_PH()],
    D.clients_d(), 400, [A('window_check', '= ' + ca('Unpaid inside the window'), 'bad'), A('window_check', '= ' + ca('Collect before the window'), 'warn'), A('status', '= ' + tok('cstatus', 'Completed'), 'good')]))
# ---------------------------------------------------------------- 5 hour packs
tables.append(T('packs', 'Hour Packs', 'Hour packs with hours used, left and unearned cash',
    'One row per prepaid hour pack (a set number of postpartum hours bought together): hours bought, used and the expiry date; the hours left, the earned and unearned cash and the pack check fill in by themselves.', [
    C('pack_id', 'Pack ID', 'text', 10, required=True), REF('client_id', 'Client ID', 'clients.client_id', 10), REF('client', 'Client', 'clients.client', 24), LST('doula', 'Doula', 'doula', 17), LST('package', 'Package', 'hpackage', 22),
    C('hours_bought', 'Hours bought', 'num', 9), C('price', 'Price', 'money', 11), C('bought_on', 'Bought on', 'date', 11), C('expires_on', 'Expires on', 'date', 11), C('hours_used', 'Hours used', 'num', 9), C('extra_hours', 'Extra hours billed', 'num', 9),
    CA('hours_left', 'Hours left', 'num', 'MAX(0,{col:hours_bought}-{col:hours_used})', 9),
    CA('earned', 'Earned so far', 'money', 'IF({col:expires_on}<{today},{col:price},ROUND({col:price}*MIN(1,{col:hours_used}/{col:hours_bought}),2))', 11),
    CA('unearned', 'Unearned cash', 'money', 'ROUND({col:price}-{col:earned},2)', 11), CA('days_to_expiry', 'Days to expiry', 'int', '{col:expires_on}-{today}', 9),
    CA('pack_flag', 'Pack check', 'text', 'IF({col:hours_left}<=0,%s,IF({col:expires_on}<{today},%s,IF({col:days_to_expiry}<={set:pack_near_days},%s,%s)))' % (ca('Used up'), ca('Ended'), ca('Near expiry'), ca('Hours left')), 14),
    CA('rate_hour', 'Price per hour', 'money', 'ROUND({col:price}/{col:hours_bought},2)', 10), CA('phone', 'Phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18), CO(), ADMIN_PH()],
    D.packs_d(), 200, [A('pack_flag', '= ' + ca('Near expiry'), 'warn'), A('pack_flag', '= ' + ca('Used up'), 'good')]))
# ---------------------------------------------------------------- 6 packages
tables.append(T('packages', 'Packages', 'Packages with price, parts and deposit share',
    'One row per package: the list price, the part earned at the birth, the part earned as postpartum hours or add-ons are delivered, and the deposit share; contracts and hour packs read these.', [
    C('package_id', 'Package ID', 'text', 10, required=True), C('package', 'Package', 'text', 24), LST('kind', 'Kind', 'pkind', 13), C('price', 'Price', 'money', 11), C('birth_value', 'Birth part', 'money', 11),
    C('pp_value', 'Postpartum part', 'money', 11), C('deposit_pct', 'Deposit share', 'pct', 9)],
    D.packages_d(), 50))
# ---------------------------------------------------------------- 7 refunds and changes
tables.append(T('cancels', 'Refunds and Changes', 'Cancellations, package changes and hour reductions',
    'One row per cancellation, package change or reduction of hours: reason, cash paid, the amount kept and the amount refunded; the refund share and the message fields fill in by themselves.', [
    C('cancel_id', 'Change ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), REF('client_id', 'Client ID', 'clients.client_id', 10), REF('client', 'Client', 'clients.client', 24),
    LST('kind', 'Kind', 'cxkind', 16), LST('reason', 'Reason', 'cxreason', 19), C('paid', 'Paid', 'money', 11), C('kept', 'Kept', 'money', 11), C('refunded', 'Refunded', 'money', 11),
    CA('refund_share', 'Refund share of paid', 'pct', 'IF({col:paid}>0,{col:refunded}/{col:paid},0)', 10), CA('phone', 'Phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18), CO()],
    D.cancels_d(), 80, [A('kind', '= ' + tok('cxkind', 'Cancelled'), 'warn')]))
# ---------------------------------------------------------------- 8 profit and loss
tables.append(T('pnl', 'Profit and Loss', 'Earned revenue and costs by month',
    'One row per month: revenue earned when the work is done (birth, postpartum hours, add-ons, classes, kept deposits) and the costs; the contract income earned in the month fills in by itself.', [
    C('month', 'Month', 'date', 11, required=True), C('revenue', 'Revenue earned', 'money', 12), C('birth_income', 'Birth income', 'money', 12), C('postpartum_income', 'Postpartum income', 'money', 12),
    C('addon_income', 'Add-on income', 'money', 11), C('class_income', 'Class income', 'money', 11), C('other_income', 'Kept deposits less refunds', 'money', 12), C('costs', 'Costs', 'money', 12),
    CA('earned', 'Contract income earned', 'money', '{col:birth_income}+{col:postpartum_income}+{col:addon_income}+{col:other_income}', 12)],
    D.pnl_d(), 60))
# ---------------------------------------------------------------- 9 team
tables.append(T('team', 'Team', 'Team with roles and phones',
    'One row per person: the owner-doula, contracted and backup doulas, the admin and outside contacts such as the accountant; the message links read these phones.', [
    C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 20), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26)],
    D.team_d(), 50))
# ---------------------------------------------------------------- 10 deposit tracker
tables.append(T('deposits', 'Deposit Tracker', 'Deposits due, paid and late for the latest contracts',
    'One row per recent contract: the deposit, when it was due and paid; the days to pay and the status (paid on time, paid late, due or overdue) fill in by themselves.', [
    REF('contract_id', 'Contract', 'contracts.contract_id', 10, required=True),
    CA('client', 'Client', 'text', LKT('contracts.client', 'contracts.contract_id', 'contract_id'), 24), CA('signed_on', 'Signed on', 'date', LKD('contracts.signed_on', 'contracts.contract_id', 'contract_id'), 11),
    CA('deposit', 'Deposit', 'money', LKN('contracts.deposit', 'contracts.contract_id', 'contract_id'), 11), CA('due_on', 'Deposit due', 'date', 'IF({col:signed_on}="","",{col:signed_on}+{set:deposit_days})', 11),
    CA('paid_on', 'Paid on', 'date', LKD('contracts.deposit_paid_on', 'contracts.contract_id', 'contract_id'), 11), CA('days_to_pay', 'Days to pay', 'int', 'IF({col:paid_on}="","",{col:paid_on}-{col:signed_on})', 9),
    CA('status', 'Deposit status', 'text', 'IF({col:paid_on}<>"",IF({col:paid_on}<={col:due_on},%s,%s),IF({today}>{col:due_on},%s,%s))' % (ca('Paid on time'), ca('Paid late'), ca('Deposit overdue'), ca('Deposit due')), 16),
    CA('phone', 'Phone', 'text', LKT('contracts.phone', 'contracts.contract_id', 'contract_id'), 18), CO()],
    D.deposits_d(), 100, [A('status', '= ' + ca('Deposit overdue'), 'bad'), A('status', '= ' + ca('Deposit due'), 'warn'), A('status', '= ' + ca('Paid on time'), 'good')]))
# ---------------------------------------------------------------- 11 balance due list
tables.append(T('balances', 'Balance Due List', 'Unpaid balances ranked by amount overdue and days',
    'One row per contract with an unpaid balance: the next payment date, the amount overdue and the days; the ageing band and the chase rank (amount times days, 1 is chased first) fill in by themselves.', [
    REF('contract_id', 'Contract', 'contracts.contract_id', 10, required=True),
    CA('client', 'Client', 'text', LKT('contracts.client', 'contracts.contract_id', 'contract_id'), 24), CA('balance_due', 'Next payment due', 'date', LKD('contracts.next_due', 'contracts.contract_id', 'contract_id'), 11),
    CA('price', 'Price', 'money', LKN('contracts.price', 'contracts.contract_id', 'contract_id'), 11), CA('paid', 'Paid so far', 'money', LKN('contracts.paid_to_date', 'contracts.contract_id', 'contract_id'), 11),
    CA('outstanding', 'Balance outstanding', 'money', LKN('contracts.balance', 'contracts.contract_id', 'contract_id'), 12), CA('overdue_amount', 'Overdue amount', 'money', LKN('contracts.overdue_amount', 'contracts.contract_id', 'contract_id'), 12),
    CA('overdue_days', 'Days overdue', 'int', LKN('contracts.overdue_days', 'contracts.contract_id', 'contract_id'), 9), CA('band', 'Ageing band', 'text', LKT('contracts.ageing_band', 'contracts.contract_id', 'contract_id'), 20),
    CA('status', 'Check', 'text', 'IF({col:overdue_amount}>0,%s,IF(AND({col:balance_due}<>"",{col:balance_due}<={today}+30),%s,%s))' % (ca('Overdue'), ca('Due soon'), ca('Not due yet')), 12),
    CA('chase_score', 'Chase score', 'num', '{col:overdue_amount}*{col:overdue_days}-VALUE(RIGHT({col:contract_id},4))/1000000', 11), CA('rank', 'Chase rank', 'int', 'COUNTIFS({range:balances.chase_score},">"&{col:chase_score})+1', 8),
    CA('phone', 'Phone', 'text', LKT('contracts.phone', 'contracts.contract_id', 'contract_id'), 18), OWNER_PH(), ADMIN_PH(), CO()],
    D.balances_d(), 100, [A('status', '= ' + ca('Overdue'), 'bad'), A('status', '= ' + ca('Due soon'), 'warn'), A('rank', '= 1', 'bad')]))
# ---------------------------------------------------------------- 12 ageing buckets
tables.append(T('ageing', 'Ageing Buckets', 'Unpaid amount by ageing band',
    'One row per ageing band: the amount unpaid and the number of contracts in it, counted from Contracts; money due in the next 30 days sits beside what is already late.', [
    LST('band', 'Ageing band', 'band', 24, required=True),
    CA('unpaid_amount', 'Unpaid amount', 'money', 'IF({col:band}=%s,SUMIFS({range:contracts.due_30},{range:contracts.ageing_band},{col:band}),SUMIFS({range:contracts.overdue_amount},{range:contracts.ageing_band},{col:band}))' % B0, 13),
    CA('clients', 'Contracts', 'int', 'COUNTIFS({range:contracts.ageing_band},{col:band})', 10)],
    D.ageing_d(), 50))
# ---------------------------------------------------------------- 13 plans before the window
tables.append(T('inst_window', 'Plans Before the Window', 'Payment plans against the on-call start',
    'One row per client on a payment plan: the first and last instalment date against the on-call start; the days before the window, the amount unpaid and the plan check fill in by themselves.', [
    REF('client_id', 'Client ID', 'clients.client_id', 10, required=True),
    CA('client', 'Client', 'text', LKT('clients.client', 'clients.client_id', 'client_id'), 24), CA('n_inst', 'Instalments', 'int', 'COUNTIFS({range:instalments.client_id},{col:client_id})', 10),
    CA('first_due', 'First due', 'date', 'IF(%s>=99999,"",%s)' % (MINA, MINA), 11), CA('last_due', 'Last instalment due', 'date', 'IF(%s=0,"",%s)' % (MAXA, MAXA), 11),
    CA('oncall_start', 'On-call start', 'date', LKD('clients.oncall_start', 'clients.client_id', 'client_id'), 11), CA('days_before', 'Days before the window', 'int', 'IF(OR({col:last_due}="",{col:oncall_start}=""),"",{col:oncall_start}-{col:last_due})', 10),
    CA('unpaid_amount', 'Unpaid amount', 'money', 'SUMIFS({range:instalments.amount},{range:instalments.client_id},{col:client_id},{range:instalments.status},%s)' % UN, 11),
    CA('overdue_unpaid', 'Overdue unpaid', 'money', 'SUMIFS({range:instalments.amount},{range:instalments.client_id},{col:client_id},{range:instalments.status},%s,{range:instalments.due_date},"<"&{today})' % UN, 11),
    CA('plan_flag', 'Plan check', 'text', 'IF({col:days_before}="",%s,IF({col:days_before}<0,%s,IF({col:days_before}<7,%s,%s)))' % (ca('Ends before the window'), ca('Ends after the window'), ca('Ends within 7 days of it'), ca('Ends before the window')), 22),
    CA('phone', 'Phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18), CO()],
    D.inst_window_d(), 80, [A('plan_flag', '= ' + ca('Ends after the window'), 'bad'), A('plan_flag', '= ' + ca('Ends within 7 days of it'), 'warn'), A('overdue_unpaid', '> 0', 'bad')]))
# ---------------------------------------------------------------- 14 unearned by client
CLK = lambda c: LKN('clients.' + c, 'clients.client_id', 'client_id')
tables.append(T('unearned_client', 'Unearned by Client', 'Earned and unearned cash for each open client',
    'One row per open client: cash paid, the part earned by phase (prenatal, on-call, birth, weeks after) and by pack hours used, and the unearned balance (cash received for work not yet done); all fill in by themselves.', [
    REF('client_id', 'Client ID', 'clients.client_id', 10, required=True),
    CA('client', 'Client', 'text', LKT('clients.client', 'clients.client_id', 'client_id'), 24), CA('kind', 'Kind', 'text', LKT('clients.kind', 'clients.client_id', 'client_id'), 11),
    CA('price', 'Price', 'money', LKN('contracts.price', 'contracts.client_id', 'client_id'), 11), CA('paid', 'Paid so far', 'money', LKN('contracts.paid_to_date', 'contracts.client_id', 'client_id'), 11),
    CA('signed_on', 'Signed on', 'date', LKD('clients.signed_on', 'clients.client_id', 'client_id'), 11), CA('oncall_start', 'On-call start', 'date', LKD('clients.oncall_start', 'clients.client_id', 'client_id'), 11),
    CA('oncall_end', 'On-call end', 'date', LKD('clients.oncall_end', 'clients.client_id', 'client_id'), 11), CA('attended_on', 'Birth attended on', 'date', LKD('clients.attended_on', 'clients.client_id', 'client_id'), 11),
    CA('edd', 'Estimated due date', 'date', LKD('clients.edd', 'clients.client_id', 'client_id'), 11),
    CA('pack_price', 'Hour pack price', 'money', 'SUMIFS({range:packs.price},{range:packs.client_id},{col:client_id})', 11), CA('pack_hours', 'Pack hours bought', 'num', 'SUMIFS({range:packs.hours_bought},{range:packs.client_id},{col:client_id})', 9),
    CA('pack_used', 'Pack hours used', 'num', 'SUMIFS({range:packs.hours_used},{range:packs.client_id},{col:client_id})', 9), CA('birth_part', 'Birth part of the price', 'money', 'MAX(0,{col:price}-{col:pack_price})', 11),
    CA('phase_share', 'Share of the birth part earned', 'pct', 'IF(OR({col:birth_part}<=0,{col:oncall_start}=""),0,{set:alloc_prenatal}*MIN(1,MAX(0,({today}-{col:signed_on})/MAX(1,{col:oncall_start}-{col:signed_on})))+{set:alloc_oncall}*MIN(1,MAX(0,({today}-{col:oncall_start})/MAX(1,{col:oncall_end}-{col:oncall_start})))+IF({col:attended_on}="",0,{set:alloc_birth}+{set:alloc_postpartum}*MIN(1,MAX(0,({today}-{col:attended_on})/42))))', 10),
    CA('earned', 'Earned to date', 'money', 'ROUND({col:birth_part}*{col:phase_share}+{col:pack_price}*IF({col:pack_hours}>0,MIN(1,{col:pack_used}/{col:pack_hours}),0),2)', 11),
    CA('unearned', 'Unearned cash', 'money', 'MAX(0,ROUND({col:paid}-{col:earned},2))', 11), CA('unearned_share', 'Unearned share of cash paid', 'pct', 'IF({col:paid}>0,{col:unearned}/{col:paid},0)', 10),
    CA('release_month', 'Month it is earned', 'date', 'MAX(%s,DATE(YEAR(IF({col:kind}=%s,{col:edd}+60,{col:edd})),MONTH(IF({col:kind}=%s,{col:edd}+60,{col:edd})),1))' % (MS, KPP, KPP), 11)],
    D.unearned_client_d(), 100, [A('unearned_share', '> 0.7', 'warn')]))
# ---------------------------------------------------------------- 15 unearned by month
tables.append(T('unearned_month', 'Unearned by Month', 'Cash received against revenue earned by month',
    'One row per month: the cash received, the revenue earned in the month and the change in unearned cash (cash received less earned); the unearned cash held now fills in beside it.', [
    C('month', 'Month', 'date', 11, required=True), CA('cash_received', 'Cash received', 'money', 'SUMIFS({range:payments.amount},{range:payments.month},{col:month})', 12),
    CA('earned', 'Contract income earned', 'money', 'SUMIFS({range:pnl.earned},{range:pnl.month},{col:month})', 12), CA('unearned_change', 'Change in unearned cash', 'money', '{col:cash_received}-{col:earned}', 12),
    CA('unearned_now', 'Unearned cash held now', 'money', 'SUM({range:unearned_client.unearned})', 12), OWNER_PH(), ACC_PH(), CO()],
    D.months_d(), 60, [A('unearned_change', '< 0', 'warn')]))
# ---------------------------------------------------------------- 16 cash receipts by month
tables.append(T('receipts', 'Cash Receipts by Month', 'Cash received by month and kind',
    'One row per month: deposits, balances, instalments, hours invoices and add-ons received, counted from Payments; the total, the money due in the next 7 days and the unearned cash held fill in beside it.', [
    C('month', 'Month', 'date', 11, required=True)] + [CA(k, l, 'money', 'SUMIFS({range:payments.amount},{range:payments.month},{col:month},{range:payments.kind},%s)' % t, 11) for k, l, t in
    (('deposits', 'Deposits', KDEP), ('balances', 'Balances', KBAL), ('instalments', 'Instalments', KINS), ('hours_invoices', 'Hours invoices', KHRS), ('addons', 'Add-ons', KADD))] + [
    CA('total', 'Total received', 'money', '{col:deposits}+{col:balances}+{col:instalments}+{col:hours_invoices}+{col:addons}', 12),
    CA('due_next_7', 'Due in the next 7 days', 'money', 'SUMIFS({range:instalments.amount},{range:instalments.status},%s,{range:instalments.due_date},">="&{today},{range:instalments.due_date},"<="&({today}+7))+SUMIFS({range:contracts.balance},{range:contracts.plan},%s,{range:contracts.status},%s,{range:contracts.balance_due},">="&{today},{range:contracts.balance_due},"<="&({today}+7))' % (UN, PIF, SIG), 12),
    CA('unearned_now', 'Unearned cash held now', 'money', 'SUM({range:unearned_client.unearned})', 12), OWNER_PH(), ACC_PH(), CO()],
    D.months_d(), 60))
# ---------------------------------------------------------------- 17 refund reasons
tables.append(T('refund_reasons', 'Refund Reasons', 'Refunds and changes by reason, last 12 months',
    'One row per reason a client cancelled or changed: the count and the amount refunded in the last 12 months, counted from Refunds and Changes.', [
    LST('reason', 'Reason', 'cxreason', 20, required=True),
    CA('count', 'Changes', 'int', 'COUNTIFS({range:cancels.reason},{col:reason},{range:cancels.date},">="&({today}-365))', 10),
    CA('refunded', 'Refunded', 'money', 'SUMIFS({range:cancels.refunded},{range:cancels.reason},{col:reason},{range:cancels.date},">="&({today}-365))', 12)],
    D.refund_reasons_d(), 50))
# ---------------------------------------------------------------- 18 change rate by month
tables.append(T('change_rate', 'Change Rate by Month', 'Contracts signed against changes and cancellations',
    'One row per month: contracts signed, changes and cancellations logged and the rate against your setting; the rate check fills in by itself.', [
    C('month', 'Month', 'date', 11, required=True), CA('contracts_signed', 'Contracts signed', 'int', 'COUNTIFS(%s)' % (INM % ('contracts.signed_on', 'contracts.signed_on')), 10),
    CA('changes', 'Changes and cancellations', 'int', 'COUNTIFS(%s)' % (INM % ('cancels.date', 'cancels.date')), 12), CA('rate', 'Change rate', 'pct', 'IF({col:contracts_signed}>0,{col:changes}/{col:contracts_signed},0)', 9),
    CA('rate_flag', 'Rate check', 'text', 'IF({col:rate}<={set:cancel_rate_max},%s,%s)' % (ca('Within the setting'), ca('Above the setting')), 16), OWNER_PH(), CO()],
    D.months_d(), 60, [A('rate_flag', '= ' + ca('Above the setting'), 'warn')]))
# ---------------------------------------------------------------- 19 payment methods
tables.append(T('methods', 'Payment Methods', 'Payments and amounts by method',
    'One row per payment method: the payments and the amount received, counted from Payments.', [
    LST('method', 'Method', 'method', 16, required=True), CA('payments', 'Payments', 'int', 'COUNTIFS({range:payments.method},{col:method})', 10),
    CA('amount', 'Amount', 'money', 'SUMIFS({range:payments.amount},{range:payments.method},{col:method})', 13)],
    D.methods_d(), 50))
# ---------------------------------------------------------------- 20 contract status
tables.append(T('ct_status', 'Contract Status', 'Contracts and price by status',
    'One row per contract status (signed, completed, cancelled): the contracts and the price, counted from Contracts.', [
    LST('status', 'Status', 'ctstatus', 14, required=True), CA('contracts', 'Contracts', 'int', 'COUNTIFS({range:contracts.status},{col:status})', 10),
    CA('price', 'Price', 'money', 'SUMIFS({range:contracts.price},{range:contracts.status},{col:status})', 13)],
    D.ct_status_d(), 50))
assert len(tables) == 20, len(tables)
