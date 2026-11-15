"""Car rental suite part 4: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr4_lists import *
import cr4_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def CONST(key_, label, val): return CA(key_, label, 'text', '"%s"' % val, 18)
def BIZ(): return CA('company', 'Business', 'text', '{set:company}', 22)
def OWNERP(): return CONST('owner_phone', 'Owner phone', D.OWNER_PHONE)
def MANAGERP(): return CONST('manager_phone', 'Manager phone', D.MANAGER_PHONE)
def R(n): return min(3000, max(60, n + 250))
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
HELD = tok('depstatus', 'Held'); EXP = tok('payoutstatus', 'Expected'); SHORT = tok('payoutstatus', 'Short-paid'); LATE = tok('payoutstatus', 'Late')
WO = tok('istatus', 'Written off'); RENTP = tok('paykind', 'Rental payment'); BALP = tok('paykind', 'Balance and fees'); CARD = tok('method', 'Card'); CASH = tok('method', 'Cash')
WAL = tok('method', 'Mobile wallet'); TRANS = tok('method', 'Bank transfer'); PAYO = tok('method', 'Marketplace payout'); MA = tok('market', 'Marketplace A'); MB = tok('market', 'Marketplace B')
CHA = tok('channel', 'Marketplace A'); CHB = tok('channel', 'Marketplace B'); CHC = tok('channel', 'Corporate account')
BK = [tok('bucket', b) for b in BUCKETS]
KEEPC = c1('Keep for claim')

settings = [
    S('company', 'Your business name', 'text', COMPANY), S('deposit_release_days', 'Days after return to release a deposit', 'int', DEPOSIT_RELEASE_DAYS),
    S('cash_floor', 'Cash floor you want to keep, example, set your own', 'money', CASH_FLOOR), S('cash_now', 'Cash at the bank now', 'money', 24150),
    S('costs_week', 'Known costs a week, example, set your own', 'money', 6800), S('owner_draw', 'Owner draw a month', 'money', OWNER_DRAW), S('card_fee_pct', 'Card fee share of a card payment', 'pct', CARD_FEE_PCT),
    S('invoice_terms_days', 'Days to pay a corporate invoice', 'int', 30), S('collect_target', 'Collection rate you want, example, set your own', 'pct', 0.95),
    S('release_target', 'Deposits released on time you want', 'pct', 0.9), S('payout_target', 'Payouts received against expected you want', 'pct', 0.98),
    S('till_tolerance', 'Till difference you accept', 'money', 2), S('credit_limit', 'Credit limit for a corporate account, example, set your own', 'money', 3000),
    S('writeoff_days', 'Days overdue before a balance is a write-off candidate', 'int', 90), S('payout_grace_days', 'Days a payout may be late before you chase', 'int', 2),
    S('promise_grace_days', 'Days after a promised date before you escalate', 'int', 2),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 deposits -----------------------------------------------------------------
DEPD = D.deposits_d()
tables.append(T('deposits', 'Deposits', 'Deposits and card holds, held, released, kept',
    'One row per deposit (an amount held on a card or kept until the car is back): dates, status and amounts; days overdue, the release verdict and the claim link fill in.', [
    C('deposit_id', 'Deposit ID', 'text', 10, required=True), C('booking_id', 'Booking', 'text', 10), C('vehicle_id', 'Vehicle', 'text', 9), C('renter', 'Renter', 'text', 14), C('phone', 'Renter phone', 'text', 18),
    LST('class', 'Class', 'class', 12), C('amount', 'Amount', 'money', 11), C('held_on', 'Held on', 'date', 11), C('release_due', 'Release due', 'date', 11), C('released_on', 'Released on', 'date', 11),
    LST('status', 'Status', 'depstatus', 11), C('kept_amount', 'Kept amount', 'num', 11), C('refunded_amount', 'Refunded amount', 'num', 12), LST('reason', 'Kept for', 'depreason', 12),
    C('claim_id', 'Claim', 'text', 9), C('claim_amount', 'Claim amount', 'num', 11),
    CA('days_over', 'Days past release', 'int', 'IF(AND({col:status}=%s,{col:release_due}<{today}),{today}-{col:release_due},0)' % HELD, 9),
    CA('verdict', 'Release verdict', 'text', 'IF({col:status}<>%s,%s,IF({col:claim_id}<>"",%s,IF({col:release_due}<={today},%s,IF({col:release_due}<={today}+7,%s,%s))))' % (
        HELD, c1('Settled'), KEEPC, c1('Release now'), c1('Due this week'), c1('Not due yet')), 14),
    CA('on_time', 'Release timing', 'text', 'IF({col:status}=%s,%s,IF({col:released_on}<={col:release_due},%s,%s))' % (HELD, c1('Still held'), c1('On time'), c1('Released late')), 13),
    CA('hold_key', 'Release order key', 'num', 'IF({col:status}=%s,{col:release_due}-{col:amount}/10000+VALUE(RIGHT({col:deposit_id},5))/10000000,"")' % HELD, 16),
    CA('over_key', 'Past-release rank key', 'num', 'IF({col:days_over}>0,{col:days_over}+{col:amount}/100000+VALUE(RIGHT({col:deposit_id},5))/1000000000,"")', 16),
    CA('held_now', 'Held now, all deposits', 'money', 'SUMIFS({range:deposits.amount},{range:deposits.status},%s)' % HELD, 11),
    CA('overdue_n', 'Holds past release date', 'int', 'COUNTIFS({range:deposits.days_over},">0")', 9),
    CA('release_n', 'Holds to release now', 'int', 'COUNTIFS({range:deposits.verdict},%s)' % c1('Release now'), 9),
    CA('release_amount', 'Amount to release now', 'money', 'SUMIFS({range:deposits.amount},{range:deposits.verdict},%s)' % c1('Release now'), 11),
    BIZ(), OWNERP(), MANAGERP(), CONST('bookkeeper_phone', 'Bookkeeper phone', D.BOOKKEEPER_PHONE)],
    DEPD, R(len(DEPD)), [A('verdict', '= ' + c1('Release now'), 'bad'), A('verdict', '= ' + KEEPC, 'warn'), A('status', '= ' + HELD, 'good')]))
# 2 payments -----------------------------------------------------------------
PAYD = D.payments_d()
tables.append(T('payments', 'Payments', 'Payments received by day, method and kind',
    'One row per payment in: date, booking, channel, kind and method; the card fee, the renter name and the phone fill in from the booking.', [
    C('payment_id', 'Payment ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), C('booking_id', 'Booking', 'text', 10), LST('channel', 'Channel', 'channel', 16),
    LST('kind', 'Kind', 'paykind', 15), LST('method', 'Method', 'method', 16), C('amount', 'Amount', 'money', 11), C('payout_id', 'Payout', 'text', 10),
    CA('card_fee', 'Card fee', 'money', 'IF(OR({col:method}=%s,{col:method}=%s),ROUND({col:amount}*{set:card_fee_pct},2),0)' % (CARD, WAL), 10),
    CA('renter', 'Renter', 'text', LKT('bookings.renter', 'bookings.booking_id', 'booking_id'), 14), CA('phone', 'Renter phone', 'text', LKT('bookings.phone', 'bookings.booking_id', 'booking_id'), 18), BIZ()],
    PAYD, R(len(PAYD)), [A('kind', '= ' + tok('paykind', 'Payout'), 'good')]))
# 3 payouts ------------------------------------------------------------------
POD = D.payouts_d()
tables.append(T('payouts', 'Payouts', 'Marketplace payouts expected against received',
    'One row per marketplace payout (the money a marketplace pays you for a rental): booking value, fee, expected and received; the difference, days late and days to payout fill in.', [
    C('payout_id', 'Payout ID', 'text', 10, required=True), C('booking_id', 'Booking', 'text', 10), LST('channel', 'Marketplace', 'market', 15), C('returned_on', 'Returned on', 'date', 11), C('month', 'Month', 'date', 11),
    C('booking_value', 'Booking value', 'money', 12), C('fee', 'Fee', 'money', 10), C('expected_payout', 'Expected payout', 'money', 12), C('expected_on', 'Expected on', 'date', 11),
    C('received', 'Received', 'num', 11), C('paid_on', 'Paid on', 'date', 11), LST('status', 'Status', 'payoutstatus', 11),
    CA('difference', 'Difference', 'money', 'IF(OR({col:status}=%s,{col:expected_on}>{today}),0,ROUND({col:received}-{col:expected_payout},2))' % EXP, 10),
    CA('gap', 'Gap to chase', 'money', 'IF(OR({col:status}=%s,{col:status}=%s),ROUND({col:expected_payout}-{col:received},2),0)' % (SHORT, LATE), 10),
    CA('days_late', 'Days late', 'int', 'IF({col:paid_on}>0,MAX(0,{col:paid_on}-{col:expected_on}),IF({col:expected_on}<{today},{today}-{col:expected_on},0))', 8),
    CA('days_to_pay', 'Days from return to payout', 'int', 'IF({col:paid_on}>0,{col:paid_on}-{col:returned_on},"")', 10),
    CA('fee_share', 'Fee share charged', 'pct', 'IFERROR({col:fee}/{col:booking_value},0)', 9),
    CA('late_n', 'Payouts late or short now', 'int', 'COUNTIFS({range:payouts.status},%s)+COUNTIFS({range:payouts.status},%s)' % (SHORT, LATE), 9),
    CA('gap_total', 'Gap to chase, all payouts', 'money', 'SUM({range:payouts.gap})', 11),
    CA('support_phone', 'Marketplace support phone', 'text', 'IF({col:channel}=%s,"%s","%s")' % (MA, D.SUPPORT_A, D.SUPPORT_B), 18), BIZ(), OWNERP(), MANAGERP()],
    POD, R(len(POD)), [A('status', '= ' + SHORT, 'bad'), A('status', '= ' + LATE, 'warn'), A('status', '= ' + tok('payoutstatus', 'Paid'), 'good')]))
# 4 invoices -----------------------------------------------------------------
IVD = D.invoices_d()
tables.append(T('invoices', 'Invoices', 'Corporate account and long-rental invoices',
    'One row per invoice: account, dates, amount, credit and payment; the balance, days overdue, age band and what to chase fill in.', [
    C('invoice_id', 'Invoice ID', 'text', 10, required=True), C('booking_id', 'Booking', 'text', 10), LST('account', 'Account', 'account', 20), C('phone', 'Billing contact phone', 'text', 18), C('issued_on', 'Issued on', 'date', 11),
    C('due_date', 'Due date', 'date', 11), C('amount', 'Amount', 'money', 11), C('credit_amount', 'Credit note amount', 'num', 12), C('paid_amount', 'Paid amount', 'num', 11), C('paid_on', 'Paid on', 'date', 11),
    LST('status', 'Status', 'istatus', 11),
    CA('month', 'Month', 'date', 'DATE(YEAR({col:issued_on}),MONTH({col:issued_on}),1)', 11),
    CA('balance', 'Balance', 'money', 'IF({col:status}=%s,0,MAX(0,ROUND({col:amount}-{col:credit_amount}-{col:paid_amount},2)))' % WO, 11),
    CA('written_off', 'Written off', 'money', 'IF({col:status}=%s,ROUND({col:amount}-{col:credit_amount}-{col:paid_amount},2),0)' % WO, 10),
    CA('days_overdue', 'Days overdue', 'int', 'IF({col:balance}>0,MAX(0,{today}-{col:due_date}),0)', 9),
    CA('age_band', 'Age band', 'text', 'IF({col:balance}>0,IF({col:days_overdue}=0,%s,IF({col:days_overdue}<=7,%s,IF({col:days_overdue}<=30,%s,IF({col:days_overdue}<=60,%s,%s)))),%s)' % (BK[0], BK[1], BK[2], BK[3], BK[4], c1('Settled')), 12),
    CA('days_to_pay', 'Days to pay', 'int', 'IF({col:paid_on}>0,{col:paid_on}-{col:issued_on},"")', 9),
    CA('terms', 'Paid against terms', 'text', 'IF({col:status}=%s,%s,IF({col:paid_on}>0,IF({col:paid_on}<={col:due_date},%s,%s),%s))' % (WO, c1('Written off'), c1('Paid within terms'), c1('Paid after terms'), c1('Open')), 16),
    CA('collected_pct', 'Collected share', 'pct', 'IF({col:status}=%s,0,IFERROR(MIN(1,({col:paid_amount}+{col:credit_amount})/{col:amount}),0))' % WO, 9),
    CA('age_days', 'Days since issued', 'int', '{today}-{col:issued_on}', 9),
    CA('net_amount', 'Amount after credit', 'money', '{col:amount}-{col:credit_amount}', 11),
    CA('account_balance', 'Account balance', 'money', 'SUMIFS({range:invoices.balance},{range:invoices.account},{col:account})', 11),
    CA('account_overdue', 'Account overdue balance', 'money', 'SUMIFS({range:invoices.balance},{range:invoices.account},{col:account},{range:invoices.days_overdue},">0")', 11),
    CA('chase_key', 'Chase rank key', 'num', 'IF(AND({col:balance}>0,{col:days_overdue}>0),{col:days_overdue}+{col:balance}/100000+VALUE(RIGHT({col:invoice_id},4))/1000000000,"")', 16),
    CA('chase_n', 'Invoices overdue now', 'int', 'COUNTIFS({range:invoices.days_overdue},">0")', 9),
    CA('chase_amount', 'Balance overdue now', 'money', 'SUMIFS({range:invoices.balance},{range:invoices.days_overdue},">0")', 11), BIZ(), MANAGERP()],
    IVD, R(len(IVD)), [A('status', '= ' + tok('istatus', 'Unpaid'), 'warn'), A('status', '= ' + WO, 'bad'), A('status', '= ' + tok('istatus', 'Paid'), 'good')]))
# 5 invoice lines ------------------------------------------------------------
LND = D.inv_lines_d()
tables.append(T('inv_lines', 'Invoice Lines', 'Invoices split into rental, fees and damage lines',
    'One row per invoice to split: rental, add-ons and fees, and damage; the total, the check against the invoice and the balance fill in.', [
    REF('invoice_id', 'Invoice', 'invoices.invoice_id', 10, required=True), C('rental', 'Rental', 'money', 11), C('addons_fees', 'Add-ons and fees', 'num', 12), C('damage', 'Damage', 'num', 10),
    CA('total', 'Total of lines', 'money', '{col:rental}+{col:addons_fees}+{col:damage}', 11), CA('invoice_amount', 'Invoice amount', 'money', LKN('invoices.amount', 'invoices.invoice_id', 'invoice_id'), 11),
    CA('check', 'Lines check', 'text', 'IF(ABS({col:total}-{col:invoice_amount})<={set:till_tolerance},%s,%s)' % (c1('Lines match'), c1('Lines differ')), 12),
    CA('account', 'Account', 'text', LKT('invoices.account', 'invoices.invoice_id', 'invoice_id'), 20), CA('balance', 'Invoice balance', 'money', LKN('invoices.balance', 'invoices.invoice_id', 'invoice_id'), 11),
    CA('damage_share', 'Damage share', 'pct', 'IFERROR({col:damage}/{col:total},0)', 9), CA('payable_now', 'Payable now without damage', 'money', '{col:rental}+{col:addons_fees}', 12), BIZ()],
    LND, R(len(LND)), [A('damage', '> 0', 'warn')]))
# 6 bookings -----------------------------------------------------------------
BKD_ = D.bookings_d()
tables.append(T('bookings', 'Bookings', 'Recent bookings with the amount and deposit',
    'One row per booking: dates, vehicle, renter, channel, total and deposit; the rental paid so far and the balance still to pay fill in.', [
    C('booking_id', 'Booking ID', 'text', 10, required=True), C('created_on', 'Created on', 'date', 11), C('start_date', 'Start date', 'date', 11), C('end_date', 'End date', 'date', 11), C('vehicle', 'Vehicle', 'text', 24),
    LST('class', 'Class', 'class', 12), C('renter', 'Renter', 'text', 14), C('phone', 'Renter phone', 'text', 18), LST('channel', 'Channel', 'channel', 16), C('total', 'Total', 'money', 11), C('deposit', 'Deposit', 'num', 10),
    LST('status', 'Status', 'bstatus', 11),
    CA('paid_rental', 'Rental paid', 'money', 'SUMIFS({range:payments.amount},{range:payments.booking_id},{col:booking_id},{range:payments.kind},%s)' % RENTP, 11),
    CA('balance', 'Balance to pay', 'money', 'IF(AND(OR({col:status}=%s,{col:status}=%s),{col:channel}<>%s,{col:channel}<>%s,{col:channel}<>%s),MAX(0,ROUND({col:total}-{col:paid_rental},2)),0)' % (
        tok('bstatus', 'Booked'), tok('bstatus', 'Active'), CHA, CHB, CHC), 11), BIZ()],
    BKD_, R(len(BKD_)), [A('status', '= ' + tok('bstatus', 'Cancelled'), 'bad')]))
# 7 channels -----------------------------------------------------------------
tables.append(T('channels', 'Channels', 'Channels with the fee share and the payout days',
    'One row per booking channel: the share it keeps and the days it takes to pay you; the tools compare real payout days with these.', [
    LST('channel', 'Channel', 'channel', 18, required=True), C('fee_pct', 'Fee share', 'pct', 10), C('payout_days', 'Payout days', 'int', 10)], D.channels_d(), 50))
# 8 holds due to release -----------------------------------------------------
def DL(col, kind='T'):
    f = {'T': LKT, 'N': LKN, 'D': LKD}[kind]
    return f('deposits.' + col, 'deposits.deposit_id', 'deposit_id')
tables.append(T('hold_due', 'Holds to Release', 'Held deposits in release order, earliest date first',
    'Rank 1 is the held deposit with the earliest release date (larger amounts first on the same day); every other field fills in from Deposits.', [
    C('rank', 'Rank', 'int', 7, required=True),
    CA('deposit_id', 'Deposit', 'text', 'IFERROR(INDEX({range:deposits.deposit_id},MATCH(SMALL({range:deposits.hold_key},{col:rank}),{range:deposits.hold_key},0)),"")', 10),
    CA('booking_id', 'Booking', 'text', DL('booking_id'), 10), CA('renter', 'Renter', 'text', DL('renter'), 14), CA('release_due', 'Release due', 'date', DL('release_due', 'D'), 11),
    CA('days_to_go', 'Days to go', 'int', 'IF({col:release_due}="","",{col:release_due}-{today})', 9), CA('amount', 'Amount', 'money', DL('amount', 'N'), 11), CA('claim_id', 'Claim', 'text', DL('claim_id'), 9),
    CA('verdict', 'Verdict', 'text', DL('verdict'), 14), CA('phone', 'Renter phone', 'text', DL('phone'), 18), BIZ()],
    D.hold_due_d(), 80, [A('verdict', '= ' + c1('Release now'), 'bad'), A('verdict', '= ' + KEEPC, 'warn')]))
# 9 kept deposits ------------------------------------------------------------
tables.append(T('kept', 'Kept Deposits', 'Deposits kept, with the fees and claim amounts behind them',
    'One row per deposit kept in full or in part: type the fees collected for the booking; the kept amount, claim amount and the support check fill in.', [
    REF('deposit_id', 'Deposit', 'deposits.deposit_id', 10, required=True), C('fees_collected', 'Fees collected', 'num', 12),
    CA('booking_id', 'Booking', 'text', DL('booking_id'), 10), CA('reason', 'Kept for', 'text', DL('reason'), 12), CA('kept_amount', 'Kept amount', 'money', DL('kept_amount', 'N'), 11), CA('claim_id', 'Claim', 'text', DL('claim_id'), 9),
    CA('claim_amount', 'Claim amount', 'money', DL('claim_amount', 'N'), 11), CA('supported', 'Fees plus claim', 'money', '{col:fees_collected}+{col:claim_amount}', 11),
    CA('unexplained', 'To explain', 'money', 'MAX(0,ROUND({col:kept_amount}-{col:supported},2))', 10),
    CA('check', 'Support check', 'text', 'IF({col:unexplained}<={set:till_tolerance},%s,%s)' % (c1('Kept amount supported'), c1('Amount to explain')), 18)],
    D.kept_d(), 100, [A('check', '= ' + c1('Amount to explain'), 'bad')]))
# 10 liability by month ------------------------------------------------------
def EOM(): return 'EOMONTH({col:month},0)'
def DS(col, extra): return 'SUMIFS({range:deposits.%s},%s)' % (col, extra)
tables.append(T('liability', 'Deposit Liability', 'Deposits held at each month end, released and kept',
    'One row per month: deposits taken, held at month end, refunded and kept, all from Deposits; invoices unpaid at month end come from Invoices.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('placed', 'Deposits taken', 'money', DS('amount', '{range:deposits.held_on},">="&{col:month},{range:deposits.held_on},"<="&EOMONTH({col:month},0)'), 11),
    CA('held_end', 'Held at month end', 'money', DS('amount', '{range:deposits.held_on},"<="&EOMONTH({col:month},0)') + '-' + DS('amount', '{range:deposits.released_on},">0",{range:deposits.released_on},"<="&EOMONTH({col:month},0)'), 12),
    CA('released', 'Refunded', 'money', DS('refunded_amount', '{range:deposits.released_on},">="&{col:month},{range:deposits.released_on},"<="&EOMONTH({col:month},0)'), 11),
    CA('kept', 'Kept', 'money', DS('kept_amount', '{range:deposits.released_on},">="&{col:month},{range:deposits.released_on},"<="&EOMONTH({col:month},0)'), 10),
    CA('invoices_open_end', 'Invoices unpaid at month end', 'money', 'SUMIFS({range:invoices.amount},{range:invoices.issued_on},"<="&EOMONTH({col:month},0))-SUMIFS({range:invoices.amount},{range:invoices.issued_on},"<="&EOMONTH({col:month},0),{range:invoices.paid_on},">0",{range:invoices.paid_on},"<="&EOMONTH({col:month},0))', 13),
    BIZ(), CONST('bookkeeper_phone', 'Bookkeeper phone', D.BOOKKEEPER_PHONE)], D.liability_d(), 60))
# 11 payout reconciliation by month ------------------------------------------
def PS(col, extra=''): return 'SUMIFS({range:payouts.%s},{range:payouts.month},{col:month},{range:payouts.channel},{col:channel},{range:payouts.expected_on},"<="&{today}%s)' % (col, extra)
tables.append(T('recon', 'Payout Reconciliation', 'Payouts by month and marketplace',
    'One row per month and marketplace: payouts due so far, booking value, fee, expected and received; the difference and the check fill in from Payouts.', [
    C('month', 'Month', 'date', 11, required=True), LST('channel', 'Marketplace', 'market', 15),
    CA('payouts_n', 'Payouts', 'int', 'COUNTIFS({range:payouts.month},{col:month},{range:payouts.channel},{col:channel},{range:payouts.expected_on},"<="&{today})', 8),
    CA('booking_value', 'Booking value', 'money', PS('booking_value'), 12), CA('fee', 'Fee', 'money', PS('fee'), 10), CA('expected', 'Expected', 'money', PS('expected_payout'), 11), CA('received', 'Received', 'money', PS('received'), 11),
    CA('difference', 'Difference', 'money', 'ROUND({col:received}-{col:expected},2)', 10),
    CA('check', 'Check', 'text', 'IF(ABS({col:difference})<={set:till_tolerance},%s,%s)' % (c1('Payouts match'), c1('Gap to chase')), 14), BIZ(), MANAGERP()], D.recon_d(), 100,
    [A('check', '= ' + c1('Gap to chase'), 'bad')]))
# 12 fee share by month ------------------------------------------------------
def PM(col): return 'SUMIFS({range:payments.amount},{range:payments.month},{col:month},{range:payments.method},%s)' % col
FSD = D.feeshare_d()
tables.append(T('feeshare', 'Fee Share by Month', 'Marketplace fees against revenue by month',
    'One row per month: type the revenue and the hotel partner commission; the marketplace fees, the fee share and the 12-month share fill in from Payouts.', [
    C('month', 'Month', 'date', 11, required=True), C('revenue', 'Revenue', 'money', 11), C('hotel_commission', 'Hotel partner commission', 'num', 12),
    CA('marketplace_fees', 'Marketplace fees', 'money', 'SUMIFS({range:payouts.fee},{range:payouts.month},{col:month})', 11), CA('fee_share', 'Fee share of revenue', 'pct', 'IFERROR({col:marketplace_fees}/{col:revenue},0)', 10),
    CA('share_12m', 'Fee share, 12 months', 'pct', 'IFERROR(SUMIFS({range:feeshare.marketplace_fees},{range:feeshare.month},">="&EDATE({col:month},-11),{range:feeshare.month},"<="&{col:month})/SUMIFS({range:feeshare.revenue},{range:feeshare.month},">="&EDATE({col:month},-11),{range:feeshare.month},"<="&{col:month}),0)', 10),
    CA('year', 'Year', 'int', 'YEAR({col:month})', 7),
    CA('year_fees', 'Marketplace fees, year', 'money', 'SUMIFS({range:feeshare.marketplace_fees},{range:feeshare.month},">="&DATE({col:year},1,1),{range:feeshare.month},"<="&DATE({col:year},12,31))', 12),
    CA('pay_card', 'Card payments', 'money', PM(CARD), 11), CA('pay_wallet', 'Mobile wallet payments', 'money', PM(WAL), 11), CA('pay_cash', 'Cash payments', 'money', PM(CASH), 11), CA('pay_transfer', 'Bank transfer payments', 'money', PM(TRANS), 11), CA('pay_payout', 'Marketplace payouts received', 'money', PM(PAYO), 12),
    BIZ(), CONST('hotel_phone', 'Hotel partner phone', D.HOTEL_PHONE), CONST('accountant_phone', 'Accountant phone', D.ACCOUNTANT_PHONE), CONST('bookkeeper_phone', 'Bookkeeper phone', D.BOOKKEEPER_PHONE),
    CONST('lender_phone', 'Lender phone', D.LENDER_PHONE)], FSD, 60))
# 13 promises to pay ---------------------------------------------------------
def IVL(col, kind='T'): return {'T': LKT, 'N': LKN, 'D': LKD}[kind]('invoices.' + col, 'invoices.invoice_id', 'invoice_id')
PRD = D.promises_d()
tables.append(T('promises', 'Promises to Pay', 'Payment promises from accounts, kept or missed',
    'One row per promise: invoice, promised date, amount, outcome and last contact; the account, balance, days to go and the next step fill in.', [
    REF('invoice_id', 'Invoice', 'invoices.invoice_id', 10, required=True), C('promised_on', 'Promised on', 'date', 11), C('amount', 'Promised amount', 'money', 12), LST('outcome', 'Outcome', 'outcome', 10), C('last_contact', 'Last contact', 'date', 11),
    CA('account', 'Account', 'text', IVL('account'), 20), CA('phone', 'Billing contact phone', 'text', IVL('phone'), 18), CA('balance', 'Invoice balance', 'money', IVL('balance', 'N'), 11),
    CA('days_to_go', 'Days to promised date', 'int', '{col:promised_on}-{today}', 9),
    CA('verdict', 'Next step', 'text', 'IF({col:outcome}=%s,%s,IF({col:outcome}=%s,%s,IF({col:promised_on}+{set:promise_grace_days}>={today},%s,%s)))' % (
        tok('outcome', 'Kept'), c1('Promise kept'), tok('outcome', 'Missed'), c1('Escalate'), c1('Chase on promised date'), c1('Escalate')), 18), BIZ(), MANAGERP()],
    PRD, R(len(PRD)), [A('outcome', '= ' + tok('outcome', 'Missed'), 'bad'), A('outcome', '= ' + tok('outcome', 'Kept'), 'good')]))
# 14 ageing buckets ----------------------------------------------------------
tables.append(T('ageing', 'Ageing Buckets', 'Open invoice balance by days overdue',
    'Five rows: the open invoices and the balance in each ageing bucket, counted from Invoices by days overdue.', [
    LST('bucket', 'Ageing bucket', 'bucket', 14, required=True),
    CA('invoices_n', 'Invoices', 'int', 'COUNTIFS({range:invoices.age_band},{col:bucket})', 10), CA('balance', 'Balance', 'money', 'SUMIFS({range:invoices.balance},{range:invoices.age_band},{col:bucket})', 12)], D.ageing_d(), 50))
# 15 cash in by day ----------------------------------------------------------
def PD(m): return 'SUMIFS({range:payments.amount},{range:payments.date},{col:date},{range:payments.method},%s)' % m
tables.append(T('cash_day', 'Cash In by Day', 'Money in per day by method, last 60 days',
    'One row per day: card, cash, bank transfer and marketplace payouts received, all added up from Payments.', [
    C('date', 'Date', 'date', 11, required=True), CA('card', 'Card', 'money', PD(CARD), 11), CA('cash', 'Cash', 'money', PD(CASH), 11), CA('transfer', 'Bank transfer', 'money', PD(TRANS), 12),
    CA('wallet', 'Mobile wallet', 'money', PD(WAL), 11), CA('payouts', 'Marketplace payouts', 'money', PD(PAYO), 12), CA('total', 'Total in', 'money', '{col:card}+{col:cash}+{col:transfer}+{col:wallet}+{col:payouts}', 11),
    CA('payments_n', 'Payments', 'int', 'COUNTIFS({range:payments.date},{col:date})', 8)], D.cash_day_d(), 90))
# 16 till check --------------------------------------------------------------
tables.append(T('till', 'Daily Till Log', 'Cash counted against cash expected each day',
    'One row per day: type the cash counted; the cash expected comes from the cash payments of that day, with the difference and the verdict.', [
    C('till_id', 'Till ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('counted', 'Cash counted', 'money', 11),
    CA('expected', 'Cash expected', 'money', 'SUMIFS({range:payments.amount},{range:payments.date},{col:date},{range:payments.method},%s)' % CASH, 11),
    CA('difference', 'Difference', 'money', 'ROUND({col:counted}-{col:expected},2)', 10),
    CA('verdict', 'Verdict', 'text', 'IF(ABS({col:difference})<={set:till_tolerance},%s,IF({col:difference}<0,%s,%s))' % (c1('Balanced'), c1('Short'), c1('Over')), 11), BIZ(), MANAGERP()],
    D.till_d(), 90, [A('verdict', '= ' + c1('Short'), 'bad'), A('verdict', '= ' + c1('Over'), 'warn'), A('verdict', '= ' + c1('Balanced'), 'good')]))
# 17 cash forecast -----------------------------------------------------------
def WS(): return '({today}+7*({col:weekno}-1))'
def SUMW(rng, crit, lo, hi):  # sum of rng where crit date column is in [lo, hi), week 1 also takes everything earlier
    return 'SUMIFS(%s,%s,"<"&%s)-IF({col:weekno}=1,0,SUMIFS(%s,%s,"<"&%s))' % (rng, crit, hi, rng, crit, lo)
FWE = '({today}+7*{col:weekno})'
fc_cols = [
    C('weekno', 'Week', 'int', 7, required=True), CA('week_start', 'Week starts', 'date', WS(), 11),
    CA('payouts', 'Payouts expected', 'money', 'SUMIFS({range:payouts.expected_payout},{range:payouts.status},%s,{range:payouts.expected_on},">="&%s,{range:payouts.expected_on},"<"&%s)+IF({col:weekno}=1,SUM({range:payouts.gap}),0)' % (EXP, WS(), FWE), 12),
    CA('deposits_out', 'Deposits to release', 'money', 'SUMIFS({range:deposits.amount},{range:deposits.status},%s,{range:deposits.verdict},"<>"&%s,{range:deposits.release_due},"<"&%s)-IF({col:weekno}=1,0,SUMIFS({range:deposits.amount},{range:deposits.status},%s,{range:deposits.verdict},"<>"&%s,{range:deposits.release_due},"<"&%s))' % (HELD, KEEPC, FWE, HELD, KEEPC, WS()), 12),
    CA('invoices_in', 'Invoice receipts', 'money', '{set:collect_target}*(SUMIFS({range:invoices.balance},{range:invoices.due_date},"<"&%s)-IF({col:weekno}=1,0,SUMIFS({range:invoices.balance},{range:invoices.due_date},"<"&%s)))' % (FWE, WS()), 12),
    CA('rentals_in', 'Rental receipts, weekly average', 'money', '(SUMIFS({range:payments.amount},{range:payments.kind},%s,{range:payments.date},">="&({today}-56))+SUMIFS({range:payments.amount},{range:payments.kind},%s,{range:payments.date},">="&({today}-56)))/8' % (RENTP, BALP), 12),
    CA('costs_out', 'Costs due', 'money', '{set:costs_week}+{set:owner_draw}*12/52', 11),
    CA('net', 'Net', 'money', '{col:payouts}+{col:invoices_in}+{col:rentals_in}-{col:deposits_out}-{col:costs_out}', 11),
    CA('cash_end', 'Cash at week end', 'money', '{set:cash_now}+SUMIFS({range:forecast.net},{range:forecast.weekno},"<="&{col:weekno})', 12),
    CA('verdict', 'Verdict', 'text', 'IF({col:cash_end}>={set:cash_floor},%s,%s)' % (c1('Cash holds'), c1('Below the floor')), 13),
    CA('lowest_cash', 'Lowest cash, 4 weeks', 'money', 'MIN(INDEX({range:forecast.cash_end},1),INDEX({range:forecast.cash_end},2),INDEX({range:forecast.cash_end},3),INDEX({range:forecast.cash_end},4))', 12),
    CA('lowest_week', 'Lowest week', 'int', 'MATCH({col:lowest_cash},{range:forecast.cash_end},0)', 8), CA('floor', 'Cash floor', 'money', '{set:cash_floor}', 10), BIZ(), OWNERP()]
tables.append(T('forecast', 'Cash Forecast', 'Cash forecast, week by week from your own history',
    'Twelve weeks from today (the tool uses the first four): payouts, deposits to release, invoice receipts, rental receipts and costs give the net and the cash at each week end.', fc_cols,
    D.forecast_d() + [dict(weekno=n) for n in range(5, 13)], 60, [A('verdict', '= ' + c1('Below the floor'), 'bad')]))
# 18 payment methods ---------------------------------------------------------
tables.append(T('methods', 'Payment Methods', 'Payments by method',
    'Five rows: how many payments and how much came in by card, mobile wallet, cash, bank transfer and marketplace payout.', [
    LST('method', 'Method', 'method', 18, required=True), CA('payments_n', 'Payments', 'int', 'COUNTIFS({range:payments.method},{col:method})', 10),
    CA('amount', 'Amount', 'money', 'SUMIFS({range:payments.amount},{range:payments.method},{col:method})', 12)], D.methods_d(), 50))
# 19 corporate accounts ------------------------------------------------------
tables.append(T('corporate', 'Corporate Accounts', 'Balance and average days to pay per account',
    'Six rows: the open balance and the average days to pay of each corporate account, worked out from Invoices.', [
    LST('account', 'Account', 'account', 20, required=True), CA('balance', 'Open balance', 'money', 'SUMIFS({range:invoices.balance},{range:invoices.account},{col:account})', 12),
    CA('avg_days', 'Average days to pay', 'num', 'IFERROR(AVERAGEIFS({range:invoices.days_to_pay},{range:invoices.account},{col:account}),0)', 12)], D.corporate_d(), 50))
# 20 card hold calendar ------------------------------------------------------
tables.append(T('card_cal', 'Card Hold Calendar', 'Holds placed and released per day, last 30 days',
    'One row per day: card holds placed, holds released and the total still held at the end of the day, all from Deposits.', [
    C('date', 'Date', 'date', 11, required=True), CA('placed', 'Holds placed', 'money', 'SUMIFS({range:deposits.amount},{range:deposits.held_on},{col:date})', 11),
    CA('released', 'Holds released', 'money', 'SUMIFS({range:deposits.amount},{range:deposits.released_on},{col:date})', 11),
    CA('held_end', 'Held at day end', 'money', 'SUMIFS({range:deposits.amount},{range:deposits.held_on},"<="&{col:date})-SUMIFS({range:deposits.amount},{range:deposits.released_on},">0",{range:deposits.released_on},"<="&{col:date})', 12),
    CA('holds_n', 'Holds placed, count', 'int', 'COUNTIFS({range:deposits.held_on},{col:date})', 9)], D.card_cal_d(), 60))
assert len(tables) == 20, len(tables)
