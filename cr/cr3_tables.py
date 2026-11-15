"""Car rental suite part 3: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr3_lists import *
import cr3_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)
def CENTER(): return CA('center', 'Business', 'text', '{set:company}', 24)
def PH(k, label, phone): return CA(k, label, 'text', '"%s"' % phone, 18)
def OWNER_PH(): return PH('owner_phone', 'Owner phone', D.OWNER_PHONE)
def MANAGER_PH(): return PH('manager_phone', 'Manager phone', D.MANAGER_PHONE)
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
BILLED = tok('feestatus', 'Billed'); WOFF = tok('feestatus', 'Written off'); NOTB = tok('feestatus', 'Not billed')
K_EXTRA = tok('feekind', 'Extra mileage'); K_LATE = tok('feekind', 'Late return'); K_CLEAN = tok('feekind', 'Cleaning'); K_REFILL = tok('feekind', 'Fuel or charge refill')
T_OPEN = tok('tollstatus', 'Open'); T_PASSED = tok('tollstatus', 'Passed on'); T_ABS = tok('tollstatus', 'Absorbed'); T_NONE = tok('tollstatus', 'No rental found')
CS_REP = tok('claimstatus', 'Reported'); CS_EST = tok('claimstatus', 'Estimate'); CS_REPAIR = tok('claimstatus', 'In repair')
OPENC = ca('Open claim')
B_CANC = tok('bstatus', 'Cancelled'); B_NOSHOW = tok('bstatus', 'No-show')

settings = [
    S('company', 'Your business name', 'text', COMPANY), S('extra_mile_fee', 'Extra mileage fee per mile', 'money', EXTRA_MILE_FEE), S('late_grace_min', 'Grace minutes before a late fee', 'int', LATE_GRACE_MIN),
    S('late_fee_hour', 'Late return fee per started hour', 'money', LATE_FEE_HOUR), S('cleaning_fee', 'Cleaning fee', 'money', CLEANING_FEE), S('refill_step_fee', 'Refill fee per 10 points below the agreed level', 'money', REFILL_STEP_FEE),
    S('refill_service_fee', 'Refill service charge', 'money', REFILL_SERVICE_FEE), S('toll_admin_fee', 'Toll and ticket admin fee', 'money', TOLL_ADMIN_FEE),
    S('fee_collect_days', 'Days before an open fee is chased, set your own', 'int', FEE_COLLECT_DAYS), S('claim_chase_days', 'Days before an open claim is chased, set your own', 'int', 30),
    S('refill_cost_step', 'Your real cost of 10 points of fuel', 'money', 3.2), S('refill_cost_ev', 'Your real cost of 10 points of charge', 'money', 2.0),
    S('handle_minutes', 'Minutes to process one toll or ticket', 'int', 15), S('staff_hour_cost', 'Cost of one staff hour', 'money', 17), S('photo_target', 'Share of handovers with photos both ways, example', 'pct', 0.95),
    S('recovery_target', 'Share of repair cost you want to recover, example', 'pct', 0.80), S('seg_min_rentals', 'Rentals a segment needs to be ranked', 'int', 30), S('seg_ratio', 'Times the average cost that marks a segment as high', 'num', 1.5),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 check-out and check-in ---------------------------------------------------
tables.append(T('checkout', 'Check-out and Check-in', 'Check-out and check-in log with the fee due',
    'One row per rental handover: out and in time, odometer, level, photos and keys; miles driven, late minutes, each fee and the fee due fill in by themselves (miles are the demo unit, set your own).', [
    C('handover_id', 'Handover ID', 'text', 10, required=True), C('booking_id', 'Booking ID', 'text', 10), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 22), LST('class', 'Class', 'class', 11), C('renter', 'Renter', 'text', 14),
    C('out_date', 'Out date', 'date', 11), C('out_time', 'Out time', 'time', 8), C('agreed_time', 'Return time agreed', 'time', 9), C('out_odometer', 'Out odometer, miles', 'int', 10), C('out_level', 'Out level, %', 'int', 8),
    C('photos_out', 'Photos out', 'bool', 8), C('keys', 'Keys', 'int', 6), C('deposit_taken', 'Deposit taken', 'bool', 9), LST('handled_by', 'Handled by', 'handler', 15),
    C('in_date', 'In date', 'date', 11), C('in_time', 'In time', 'time', 8), C('in_odometer', 'In odometer, miles', 'int', 10), C('in_level', 'In level, %', 'int', 8), C('photos_in', 'Photos in', 'bool', 8),
    C('damage_seen', 'Damage seen', 'bool', 8), C('cleaning', 'Cleaning needed', 'bool', 9), C('miles_included', 'Miles included', 'int', 9), C('phone', 'Renter phone', 'text', 18),
    CA('miles_driven', 'Miles driven', 'int', 'IF({col:in_odometer}>0,{col:in_odometer}-{col:out_odometer},"")', 9),
    CA('extra_miles', 'Extra miles', 'int', 'IF({col:miles_driven}="","",MAX(0,{col:miles_driven}-{col:miles_included}))', 9),
    CA('late_minutes', 'Late minutes', 'int', 'IF({col:in_date}>0,MAX(0,ROUND(({col:in_time}-{col:agreed_time})*1440,0)),"")', 9),
    CA('shortfall', 'Level shortfall, points', 'int', 'IF({col:in_date}>0,MAX(0,{col:out_level}-{col:in_level}),"")', 10),
    CA('mile_fee', 'Extra mileage fee', 'money', 'IF({col:in_date}>0,ROUND({col:extra_miles}*{set:extra_mile_fee},2),"")', 11),
    CA('late_fee', 'Late return fee', 'money', 'IF({col:in_date}>0,IF({col:late_minutes}>{set:late_grace_min},ROUNDUP(({col:late_minutes}-{set:late_grace_min})/60,0)*{set:late_fee_hour},0),"")', 11),
    CA('refill_fee', 'Refill fee', 'money', 'IF({col:in_date}>0,IF({col:shortfall}>=10,{set:refill_service_fee}+{set:refill_step_fee}*ROUNDUP({col:shortfall}/10,0),0),"")', 10),
    CA('clean_fee', 'Cleaning fee', 'money', 'IF({col:in_date}>0,IF({col:cleaning}=%s,{set:cleaning_fee},0),"")' % YES, 10),
    CA('fee_due', 'Fee due', 'money', 'IF({col:in_date}>0,{col:mile_fee}+{col:late_fee}+{col:refill_fee}+{col:clean_fee},"")', 10),
    CA('missing', 'Checks missing', 'int', 'IF({col:photos_out}=%s,0,1)+IF({col:keys}>=2,0,1)+IF({col:in_date}>0,IF({col:photos_in}=%s,0,1),0)' % (YES, YES), 9),
    MANAGER_PH(), PH('detailer_phone', 'Detailer phone', D.DETAILER_PHONE), PH('hotel_phone', 'Hotel partner phone', D.HOTEL_PHONE), PH('corp_phone', 'Corporate account phone', D.CORP_PHONE), CENTER()],
    D.handover_d(), 2300, [A('missing', '> 0', 'bad'), A('late_minutes', '> 59', 'warn'), A('damage_seen', '= ' + YES, 'bad'), A('fee_due', '> 0', 'warn')]))
# 2 bookings -----------------------------------------------------------------
tables.append(T('bookings', 'Bookings', 'Recent and booked rentals with the handover checks',
    'One row per booking of the last weeks and the next weeks: dates, vehicle, renter, channel, deposit and status; the days, handover and checks missing fill in by themselves.', [
    C('booking_id', 'Booking ID', 'text', 10, required=True), C('bk_no', 'Booking number', 'int', 9), C('start_date', 'Start date', 'date', 11), C('end_date', 'End date', 'date', 11), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 22),
    LST('class', 'Class', 'class', 11), C('renter', 'Renter', 'text', 14), LST('channel', 'Channel', 'channel', 15), C('return_time', 'Return time', 'time', 9), C('deposit', 'Deposit', 'money', 10), LST('status', 'Status', 'bstatus', 11),
    CA('days', 'Days', 'int', '{col:end_date}-{col:start_date}+1', 7), CA('handover_id', 'Handover', 'text', LKT('checkout.handover_id', 'checkout.booking_id', 'booking_id'), 10),
    CA('missing_checks', 'Checks missing', 'int', 'IFERROR(INDEX({range:checkout.missing},MATCH({col:booking_id},{range:checkout.booking_id},0)),"")', 9),
    CA('fee_due', 'Fee due', 'money', 'IFERROR(INDEX({range:checkout.fee_due},MATCH({col:booking_id},{range:checkout.booking_id},0)),"")', 10)],
    D.bookings_d(), 600, [A('status', '= ' + B_CANC, 'bad'), A('status', '= ' + B_NOSHOW, 'warn')]))
# 3 fees ---------------------------------------------------------------------
tables.append(T('fees', 'Fees', 'Fees and the rule behind each one',
    'One row per fee: extra mileage, late return, cleaning, refill, toll and ticket admin, key replacement and late cancellation; amounts are your own defaults, set on the Start sheet.', [
    C('fee', 'Fee', 'text', 24, required=True), C('amount', 'Amount', 'money', 11), C('basis', 'Basis', 'text', 30)], D.fees_d(), 50))
# 4 fee log ------------------------------------------------------------------
tables.append(T('fee_log', 'Fee Log', 'Fees due at return and what happened to them',
    'One row per fee due: kind, amount, billed yes or no and collected; days since return, the open amount and the amount left unbilled fill in by themselves.', [
    C('fee_id', 'Fee ID', 'text', 10, required=True), C('booking_id', 'Booking ID', 'text', 10), C('vehicle_id', 'Vehicle ID', 'text', 9), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), LST('kind', 'Kind', 'feekind', 18),
    C('amount_due', 'Amount due', 'money', 11), C('billed', 'Billed', 'bool', 8), C('collected', 'Collected', 'money', 11), LST('status', 'Status', 'feestatus', 12), C('renter', 'Renter', 'text', 14), C('phone', 'Renter phone', 'text', 18),
    CA('days_since', 'Days since return', 'int', '{today}-{col:date}', 9), CA('open_amount', 'Open amount', 'money', 'IF({col:status}=%s,{col:amount_due}-{col:collected},0)' % BILLED, 11),
    CA('not_billed_amt', 'Not billed amount', 'money', 'IF({col:billed}=%s,0,{col:amount_due})' % YES, 11),
    CA('open_fees', 'Open fees, all', 'int', 'COUNTIFS({range:fee_log.status},%s)' % BILLED, 9), CA('open_total', 'Open amount, all', 'money', 'SUM({range:fee_log.open_amount})', 11),
    MANAGER_PH(), OWNER_PH(), CENTER()], D.fee_log_d(), 1300, [A('status', '= ' + BILLED, 'warn'), A('status', '= ' + NOTB, 'bad'), A('status', '= ' + tok('feestatus', 'Collected'), 'good')]))
# 5 fee ageing ---------------------------------------------------------------
IDX5 = 'MATCH({col:band},{range:fee_ageing.band},0)'
AGE5 = '{range:fee_log.status},%s,{range:fee_log.days_since},">="&CHOOSE(%s,0,15,31,91,181),{range:fee_log.days_since},"<="&CHOOSE(%s,14,30,90,180,99999)' % (BILLED, IDX5, IDX5)
tables.append(T('fee_ageing', 'Fee Ageing', 'Open fees by age band',
    'Four age bands of fees that were billed and not collected; the number of open fees and the open amount of each band fill in from the Fee Log.', [
    C('band', 'Age band', 'text', 22, required=True), CA('open_fees', 'Open fees', 'int', 'COUNTIFS(%s)' % AGE5, 10), CA('open_amount', 'Open amount', 'money', 'SUMIFS({range:fee_log.open_amount},%s)' % AGE5, 12)], D.fee_ageing_d(), 50))
# 6 money left on the table ---------------------------------------------------
tables.append(T('money_left', 'Money Left on the Table', 'Fees due but never billed, month by month',
    'One row per month: fees due, billed, collected, written off and the amount that was due but never billed; every figure fills in from the Fee Log.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('due', 'Fees due', 'money', 'SUMIFS({range:fee_log.amount_due},{range:fee_log.month},{col:month})', 11), CA('billed', 'Billed', 'money', 'SUMIFS({range:fee_log.amount_due},{range:fee_log.month},{col:month},{range:fee_log.billed},%s)' % YES, 11),
    CA('collected', 'Collected', 'money', 'SUMIFS({range:fee_log.collected},{range:fee_log.month},{col:month})', 11), CA('written_off', 'Written off', 'money', 'SUMIFS({range:fee_log.amount_due},{range:fee_log.month},{col:month},{range:fee_log.status},%s)' % WOFF, 11),
    CA('not_billed', 'Not billed', 'money', 'SUMIFS({range:fee_log.not_billed_amt},{range:fee_log.month},{col:month})', 11),
    CA('not_billed_share', 'Share not billed', 'pct', 'IF({col:due}>0,{col:not_billed}/{col:due},0)', 9), OWNER_PH(), PH('accountant_phone', 'Accountant phone', D.ACCOUNTANT['phone']), CENTER()],
    D.money_left_d(), 50, [A('not_billed_share', '> 0.1', 'warn')]))
# 7 damage claims -------------------------------------------------------------
tables.append(T('claims', 'Damage Claims', 'Damage claims as status and amounts',
    'One row per claim: status, estimate, repair cost, deposit used, amount paid and written off (status and amounts only, check your insurance terms); days open, net cost and the chase action fill in.', [
    C('claim_id', 'Claim ID', 'text', 9, required=True), C('booking_id', 'Booking ID', 'text', 10), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 22), C('renter', 'Renter', 'text', 14), LST('class', 'Class', 'class', 11),
    LST('channel', 'Channel', 'channel', 15), LST('plan', 'Plan', 'plan', 9), C('young', 'Young driver', 'bool', 8), C('cover', 'Cover option', 'bool', 8), C('reported_on', 'Reported on', 'date', 11), C('month', 'Month', 'date', 11),
    LST('kind', 'Kind', 'claimkind', 15), LST('status', 'Status', 'claimstatus', 12), C('estimate', 'Estimate', 'money', 10), C('repair_cost', 'Repair cost', 'num', 10), C('deposit', 'Deposit held on the booking', 'money', 11),
    C('deposit_used', 'Deposit used', 'num', 10), C('claim_paid', 'Claim paid', 'num', 10), C('written_off', 'Written off', 'num', 10), C('closed_on', 'Closed on', 'date', 11), C('slot_date', 'Repair slot', 'date', 11),
    C('phone', 'Renter phone', 'text', 18),
    CA('open_flag', 'Open or closed', 'text', 'IF(OR({col:status}=%s,{col:status}=%s,{col:status}=%s),%s,%s)' % (CS_REP, CS_EST, CS_REPAIR, OPENC, ca('Closed claim')), 12),
    CA('days_open', 'Days open', 'int', 'IF({col:closed_on}>0,{col:closed_on}-{col:reported_on},{today}-{col:reported_on})', 8),
    CA('net_cost', 'Net cost', 'money', 'MAX(0,{col:repair_cost}-{col:deposit_used}-{col:claim_paid})', 10), CA('recovered', 'Recovered', 'money', '{col:deposit_used}+{col:claim_paid}', 10),
    CA('chase_score', 'Chase score', 'money', 'IF({col:open_flag}=%s,{col:days_open}*{col:estimate},0)' % OPENC, 10),
    CA('action', 'Action', 'text', 'IF({col:open_flag}=%s,IF({col:days_open}>{set:claim_chase_days},%s,%s),%s)' % (OPENC, ca('Chase'), ca('Wait'), ca('Closed claim')), 11),
    CA('deposit_held_now', 'Deposit still held', 'money', 'IF({col:open_flag}=%s,MAX(0,{col:deposit}-{col:deposit_used}),0)' % OPENC, 10),
    PH('market_phone', 'Marketplace support phone', D.MARKET_PHONE), PH('body_phone', 'Body repair shop phone', D.BODYSHOP['phone']), PH('broker_phone', 'Insurance broker phone', D.BROKER['phone']),
    MANAGER_PH(), OWNER_PH(), CENTER()],
    D.claims_d(), 300, [A('action', '= ' + ca('Chase'), 'bad'), A('open_flag', '= ' + OPENC, 'warn')]))
# 8 claims by month ----------------------------------------------------------
tables.append(T('claims_month', 'Claims by Month', 'Claims reported, closed and still open by month',
    'One row per month: rentals started (type them), claims reported, closed and still open, the amount and the net damage cost per 100 rentals against your own 3-month average.', [
    C('month', 'Month', 'date', 11, required=True), C('rentals', 'Rentals started', 'int', 10),
    CA('reported', 'Reported', 'int', 'COUNTIFS({range:claims.month},{col:month})', 9),
    CA('closed', 'Closed', 'int', 'COUNTIFS({range:claims.closed_on},">="&{col:month},{range:claims.closed_on},"<="&EOMONTH({col:month},0))', 9),
    CA('still_open', 'Still open at month end', 'int', 'COUNTIFS({range:claims.reported_on},"<="&EOMONTH({col:month},0))-COUNTIFS({range:claims.closed_on},"<="&EOMONTH({col:month},0))', 10),
    CA('amount', 'Estimates', 'money', 'SUMIFS({range:claims.estimate},{range:claims.month},{col:month})', 11), CA('net_cost', 'Net damage cost', 'money', 'SUMIFS({range:claims.net_cost},{range:claims.month},{col:month})', 11),
    CA('damage_rate', 'Net cost per 100 rentals', 'money', 'IF({col:rentals}>0,{col:net_cost}/{col:rentals}*100,0)', 11),
    CA('avg_3m', 'Average of the 3 months before', 'money', 'IFERROR(AVERAGEIFS({range:claims_month.damage_rate},{range:claims_month.month},">="&EDATE({col:month},-3),{range:claims_month.month},"<"&{col:month}),0)', 12),
    CA('vs_usual', 'Against your usual', 'text', 'IF({col:avg_3m}=0,%s,IF({col:damage_rate}>{col:avg_3m}*1.15,%s,IF({col:damage_rate}<{col:avg_3m}*0.85,%s,%s)))' % (ca('On your usual'), ca('Above your usual'), ca('Below your usual'), ca('On your usual')), 14),
    OWNER_PH(), CENTER()], D.claims_month_d(), 50, [A('vs_usual', '= ' + ca('Above your usual'), 'warn')]))
# 9 damage by segment --------------------------------------------------------
SK = {n: tok('segkind', n) for n in SEGKINDS}
def SEG(fn):
    return 'IF({col:kind}=%s,%s,IF({col:kind}=%s,%s,IF({col:kind}=%s,%s,IF({col:kind}=%s,%s,%s))))' % (SK['Class'], fn('class', '{col:segment}'), SK['Channel'], fn('channel', '{col:segment}'), SK['Plan'], fn('plan', '{col:segment}'),
                                                                                                         SK['Young driver'], fn('young', '{col:flag}'), fn('cover', '{col:flag}'))
W12 = '{range:claims.reported_on},">="&({today}-365)'
OVERALL = 'IFERROR(SUMIFS({range:segments.net_cost},{range:segments.kind},%s)/SUMIFS({range:segments.rentals},{range:segments.kind},%s),0)' % (SK['Class'], SK['Class'])
tables.append(T('segments', 'Damage by Segment', 'Damage cost per rental by segment',
    'One row per segment: rentals of the last 12 months (type them); claims, repair cost and net cost fill in from Damage Claims, with cost per rental and a deposit flag.', [
    C('segment', 'Segment', 'text', 22, required=True), LST('kind', 'Segment kind', 'segkind', 14), C('flag', 'Yes or no', 'bool', 8), C('rentals', 'Rentals, 12 months', 'int', 10),
    CA('claims', 'Claims, 12 months', 'int', SEG(lambda c, x: 'COUNTIFS({range:claims.%s},%s,%s)' % (c, x, W12)), 9),
    CA('repair_cost', 'Repair cost', 'money', SEG(lambda c, x: 'SUMIFS({range:claims.repair_cost},{range:claims.%s},%s,%s)' % (c, x, W12)), 11),
    CA('net_cost', 'Net cost', 'money', SEG(lambda c, x: 'SUMIFS({range:claims.net_cost},{range:claims.%s},%s,%s)' % (c, x, W12)), 11),
    CA('cost_rental', 'Net cost per rental', 'money', 'IF({col:rentals}>0,{col:net_cost}/{col:rentals},0)', 10), CA('cost_100', 'Net cost per 100 rentals', 'money', '{col:cost_rental}*100', 11),
    CA('kind_share', 'Share of the kind total', 'pct', 'IFERROR({col:net_cost}/SUMIFS({range:segments.net_cost},{range:segments.kind},{col:kind}),0)', 10),
    CA('rank_score', 'Rank score', 'money', 'IF({col:rentals}>={set:seg_min_rentals},{col:cost_rental},0)', 9),
    CA('verdict', 'Deposit check', 'text', 'IF({col:rank_score}>{set:seg_ratio}*%s,%s,%s)' % (OVERALL, ca('Ask a larger deposit'), ca('Keep the deposit')), 18)],
    D.segments_d(), 50, [A('verdict', '= ' + ca('Ask a larger deposit'), 'bad')]))
# 10 claim ageing ------------------------------------------------------------
IDX10 = 'MATCH({col:band},{range:claim_ageing.band},0)'
AGE10 = '{range:claims.open_flag},%s,{range:claims.days_open},">="&CHOOSE(%s,0,15,31,46,91),{range:claims.days_open},"<="&CHOOSE(%s,14,30,45,90,99999)' % (OPENC, IDX10, IDX10)
tables.append(T('claim_ageing', 'Claim Ageing', 'Open claims by age band',
    'Four age bands of claims that are still open; the number of open claims and their estimate fill in from Damage Claims.', [
    C('band', 'Age band', 'text', 22, required=True), CA('open_claims', 'Open claims', 'int', 'COUNTIFS(%s)' % AGE10, 10), CA('estimate', 'Estimate', 'money', 'SUMIFS({range:claims.estimate},%s)' % AGE10, 12)], D.claim_ageing_d(), 50))
# 11 tolls and tickets -------------------------------------------------------
tables.append(T('tolls', 'Tolls and Tickets', 'Tolls and tickets passed on to the renter with an admin fee',
    'One row per toll or ticket: date, vehicle, amount, status and what was recovered; days to pass on, the admin fee and the amount to pass on fill in by themselves.', [
    C('toll_id', 'Toll ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 22), LST('kind', 'Kind', 'tollkind', 14), C('amount', 'Amount', 'money', 10),
    C('booking_id', 'Booking ID', 'text', 10), C('renter', 'Renter', 'text', 14), LST('status', 'Status', 'tollstatus', 14), C('admin_fee', 'Admin fee charged', 'num', 10), C('recovered', 'Recovered', 'num', 10),
    C('passed_on', 'Passed on', 'date', 11), C('phone', 'Renter phone', 'text', 18),
    CA('days_to_pass', 'Days to pass on', 'int', 'IF({col:passed_on}>0,{col:passed_on}-{col:date},"")', 9), CA('admin_due', 'Admin fee', 'money', '{set:toll_admin_fee}', 9),
    CA('to_pass', 'Amount to pass on', 'money', '{col:amount}+{set:toll_admin_fee}', 11), CA('open_tolls', 'Items to pass on, all', 'int', 'COUNTIFS({range:tolls.status},%s)' % T_OPEN, 9),
    CA('month_passed', 'Passed on in the month', 'money', 'SUMIFS({range:tolls.recovered},{range:tolls.month},{col:month},{range:tolls.status},%s)' % T_PASSED, 11),
    MANAGER_PH(), PH('bookkeeper_phone', 'Bookkeeper phone', D.BOOKKEEPER_PHONE), CENTER()], D.tolls_d(), 800, [A('status', '= ' + T_OPEN, 'warn'), A('status', '= ' + T_NONE, 'bad'), A('status', '= ' + T_PASSED, 'good')]))
# 12 toll match ---------------------------------------------------------------
HIT = '({range:bookings.vehicle}={col:vehicle})*({range:bookings.start_date}<={col:date})*({range:bookings.end_date}>={col:date})*({range:bookings.status}<>%s)*({range:bookings.status}<>%s)' % (B_CANC, B_NOSHOW)
tables.append(T('toll_match', 'Toll Match', 'Each toll or ticket matched to the rental that had the car',
    'One row per recent toll or ticket: the rentals that had the vehicle on that date are counted, the renter is named and a verdict says pass on, already passed on, absorbed or no rental found.', [
    REF('toll_id', 'Toll ID', 'tolls.toll_id', 10, required=True), CA('vehicle', 'Vehicle', 'text', LKT('tolls.vehicle', 'tolls.toll_id', 'toll_id'), 22), CA('date', 'Date', 'date', LKD('tolls.date', 'tolls.toll_id', 'toll_id'), 11),
    CA('status', 'Status', 'text', LKT('tolls.status', 'tolls.toll_id', 'toll_id'), 14), CA('hits', 'Rentals found', 'int', 'SUMPRODUCT(%s)' % HIT, 9),
    CA('bk_no', 'Booking number', 'int', 'SUMPRODUCT(%s*{range:bookings.bk_no})' % HIT, 9),
    CA('booking', 'Booking found', 'text', 'IF({col:hits}=1,IFERROR(INDEX({range:bookings.booking_id},MATCH({col:bk_no},{range:bookings.bk_no},0)),""),"")', 11),
    CA('renter', 'Renter', 'text', 'IF({col:hits}=1,IFERROR(INDEX({range:bookings.renter},MATCH({col:bk_no},{range:bookings.bk_no},0)),""),"")', 14),
    CA('to_pass', 'Amount to pass on', 'money', 'IFERROR(INDEX({range:tolls.amount},MATCH({col:toll_id},{range:tolls.toll_id},0))+{set:toll_admin_fee},0)', 11),
    CA('verdict', 'Verdict', 'text', 'IF({col:hits}=0,%s,IF({col:hits}>1,%s,IF({col:status}=%s,%s,IF({col:status}=%s,%s,%s))))' % (ca('No rental found'), ca('Check overlap'), T_PASSED, ca('Already passed on'), T_ABS, ca('Absorbed'), ca('Pass on')), 16)],
    D.toll_match_d(), 100, [A('verdict', '= ' + ca('Pass on'), 'warn'), A('verdict', '= ' + ca('No rental found'), 'bad')]))
# 13 renter status -----------------------------------------------------------
tables.append(T('renter_status', 'Renter Status', 'Renter status with a go or no-go verdict',
    'One row per renter (first name and initial): age band, status, documents checked and the booking start; the go or no-go verdict fills in. No addresses, licence or card numbers are kept.', [
    C('renter_id', 'Renter ID', 'text', 10, required=True), C('renter', 'Renter', 'text', 14), LST('age_band', 'Age band', 'ageband', 12), LST('status', 'Status', 'rstatus', 13), C('documents_checked', 'Documents checked', 'bool', 10),
    C('account', 'Corporate account', 'text', 22), C('rentals', 'Rentals', 'int', 8), C('start_date', 'Booking start', 'date', 11), C('phone', 'Renter phone', 'text', 18),
    CA('verdict', 'Go or no-go', 'text', 'IF({col:status}=%s,%s,IF(OR({col:status}=%s,{col:documents_checked}<>%s),%s,%s))' % (tok('rstatus', 'Restricted'), ca('No-go'), tok('rstatus', 'Documents due'), YES, ca('Hold, documents due'), ca('Go')), 18),
    CENTER()], D.renter_status_d(), 300, [A('verdict', '= ' + ca('No-go'), 'bad'), A('verdict', '= ' + ca('Hold, documents due'), 'warn'), A('verdict', '= ' + ca('Go'), 'good')]))
# 14 vehicle classes -----------------------------------------------------------
tables.append(T('classes', 'Vehicle Classes', 'Deposit and included miles by class',
    'One row per vehicle class: the deposit held on a card and the miles included each day (miles are the demo unit, set your own); the deposit size and mileage tools read them.', [
    LST('class', 'Class', 'class', 14, required=True), C('deposit', 'Deposit', 'money', 11), C('miles_day', 'Included miles a day', 'int', 12)], D.classes_d(), 50))
# 15 late returns -------------------------------------------------------------
tables.append(T('late_returns', 'Late Returns', 'Late returns with the fee after the grace',
    'One row per late return: agreed and actual return time; late minutes, started hours and the fee after your grace fill in by themselves.', [
    C('booking_id', 'Booking ID', 'text', 10, required=True), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 22), C('date', 'Return date', 'date', 11), C('agreed_time', 'Agreed time', 'time', 9), C('actual_time', 'Actual time', 'time', 9),
    CA('late_minutes', 'Late minutes', 'int', 'MAX(0,ROUND(({col:actual_time}-{col:agreed_time})*1440,0))', 9),
    CA('hours', 'Started hours billed', 'int', 'IF({col:late_minutes}>{set:late_grace_min},ROUNDUP(({col:late_minutes}-{set:late_grace_min})/60,0),0)', 10),
    CA('fee_due', 'Fee due', 'money', '{col:hours}*{set:late_fee_hour}', 10)], D.late_returns_d(), 300, [A('late_minutes', '> 59', 'warn')]))
# 16 fuel and charge levels ----------------------------------------------------
tables.append(T('fuel_levels', 'Fuel and Charge Levels', 'Levels at check-out and check-in, refill fee and cost',
    'One row per return below the agreed level: out and in level; the shortfall, refill steps, refill fee, your real cost and the margin fill in by themselves.', [
    C('booking_id', 'Booking ID', 'text', 10, required=True), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 22), C('date', 'Return date', 'date', 11), LST('fuel', 'Fuel type', 'fuel', 10), C('out_level', 'Out level, %', 'int', 9), C('in_level', 'In level, %', 'int', 9),
    CA('shortfall', 'Shortfall, points', 'int', 'MAX(0,{col:out_level}-{col:in_level})', 9), CA('steps', 'Refill steps of 10', 'int', 'IF({col:shortfall}>=10,ROUNDUP({col:shortfall}/10,0),0)', 9),
    CA('refill_fee', 'Refill fee', 'money', 'IF({col:steps}>0,{set:refill_service_fee}+{set:refill_step_fee}*{col:steps},0)', 10),
    CA('real_cost', 'Real refill cost', 'money', '{col:steps}*IF({col:fuel}=%s,{set:refill_cost_ev},{set:refill_cost_step})' % tok('fuel', 'Electric'), 10), CA('margin', 'Margin', 'money', '{col:refill_fee}-{col:real_cost}', 10)],
    D.fuel_levels_d(), 300, [A('margin', '< 0', 'bad')]))
# 17 extra mileage -----------------------------------------------------------
tables.append(T('extra_mileage', 'Extra Mileage', 'Rentals that went over the included miles',
    'One row per rental over its allowance: class, plan, miles included and miles driven (miles are the demo unit, set your own); extra miles, the fee and the overrun share fill in.', [
    C('booking_id', 'Booking ID', 'text', 10, required=True), C('date', 'Return date', 'date', 11), LST('class', 'Class', 'class', 12), LST('plan', 'Plan', 'plan', 9), C('miles_included', 'Miles included', 'int', 10), C('miles_driven', 'Miles driven', 'int', 10),
    CA('extra_miles', 'Extra miles', 'int', 'MAX(0,{col:miles_driven}-{col:miles_included})', 9), CA('fee', 'Fee', 'money', 'ROUND({col:extra_miles}*{set:extra_mile_fee},2)', 10),
    CA('over_share', 'Overrun share', 'pct', 'IF({col:miles_included}>0,{col:extra_miles}/{col:miles_included},0)', 9)], D.extra_mileage_d(), 300))
# 18 photos and keys -----------------------------------------------------------
tables.append(T('photos_keys', 'Photos and Keys', 'Photos and keys checked at each handover',
    'One row per returned rental: who handled it, photos out and in yes or no (no photos are stored here) and keys; checks missing and a complete or missing result fill in.', [
    C('booking_id', 'Booking ID', 'text', 10, required=True), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 22), LST('handled_by', 'Handled by', 'handler', 15), C('date', 'Return date', 'date', 11), C('photos_out', 'Photos out', 'bool', 9),
    C('photos_in', 'Photos in', 'bool', 9), C('keys', 'Keys', 'int', 7),
    CA('missing_checks', 'Checks missing', 'int', 'IF({col:photos_out}=%s,0,1)+IF({col:photos_in}=%s,0,1)+IF({col:keys}>=2,0,1)' % (YES, YES), 9),
    CA('result', 'Result', 'text', 'IF({col:missing_checks}=0,%s,%s)' % (ca('Complete'), ca('Checks missing')), 14)], D.photos_keys_d(), 300, [A('result', '= ' + ca('Checks missing'), 'bad')]))
# 19 vehicles -------------------------------------------------------------------
tables.append(T('vehicles', 'Vehicles', 'The vehicles of the fleet',
    'One row per vehicle with class, fuel, status and odometer in miles; every other sheet picks the vehicle from this list.', [
    C('vehicle_id', 'Vehicle ID', 'text', 9, required=True), C('vehicle', 'Vehicle', 'text', 24), C('plate', 'Plate', 'text', 11), LST('class', 'Class', 'class', 12), LST('fuel', 'Fuel type', 'fuel', 10), LST('status', 'Status', 'vstatus', 12),
    C('odometer', 'Odometer, miles', 'int', 10)], D.vehicles_d(), 100, [A('status', '= ' + tok('vstatus', 'In workshop'), 'warn'), A('status', '= ' + tok('vstatus', 'Sold'), 'bad')]))
# 20 fees by kind and month ------------------------------------------------------
tables.append(T('fees_month', 'Fees by Kind and Month', 'Fees due and collected by kind and month',
    'One row per month and fee kind: the amount due, collected, left unbilled and the share collected fill in from the Fee Log.', [
    C('month', 'Month', 'date', 11, required=True), LST('kind', 'Kind', 'feekind', 18),
    CA('due', 'Due', 'money', 'SUMIFS({range:fee_log.amount_due},{range:fee_log.month},{col:month},{range:fee_log.kind},{col:kind})', 11),
    CA('collected', 'Collected', 'money', 'SUMIFS({range:fee_log.collected},{range:fee_log.month},{col:month},{range:fee_log.kind},{col:kind})', 11),
    CA('not_billed', 'Not billed', 'money', 'SUMIFS({range:fee_log.not_billed_amt},{range:fee_log.month},{col:month},{range:fee_log.kind},{col:kind})', 11),
    CA('collect_share', 'Share collected', 'pct', 'IF({col:due}>0,{col:collected}/{col:due},0)', 9)], D.fees_month_d(), 150))
assert len(tables) == 20
