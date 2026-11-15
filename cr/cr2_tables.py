"""Car rental suite part 2: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr2_lists import *
import cr2_data as D


def R(t, c): return '{range:%s.%s}' % (t, c)
def Cc(c): return '{col:%s}' % c
B = lambda c: R('bookings', c)
BL = lambda c: R('service_blocks', c)
VH = lambda c: R('vehicles', c)
CVD = lambda c: R('cal_vehicle', c)
CCD = lambda c: R('cal_class', c)
CAN, NOS, ACT, BKD, CMP = (tok('bstatus', x) for x in ('Cancelled', 'No-show', 'Active', 'Booked', 'Completed'))
SOLD = tok('vstatus', 'Sold'); MAIN = tok('location', 'Main lot')
CH = {c: tok('channel', c) for c in CHANNELS}
FREE, SERV, RENT, RESV = (tok('calst', x) for x in ('Free', 'Service', 'Rented', 'Reserved'))
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
HOLDC = ',%s,"<>"&%s,%s,"<>"&%s' % (B('status'), CAN, B('status'), NOS)          # appended to a COUNTIFS or SUMIFS over Bookings: the booking holds a car
HOLDA = '(%s<>%s)*(%s<>%s)' % (B('status'), CAN, B('status'), NOS)               # the same inside SUMPRODUCT
YES, NO = '{list:yesno.yes}', '{list:yesno.no}'


def OVL(lo, hi, S, E):
    """days (as an array) that [S,E] shares with [lo,hi], no MIN or MAX needed: min(a,b)=(a+b-|a-b|)/2"""
    a = '((%s+%s+ABS(%s-%s))/2)' % (S, lo, S, lo); b = '((%s+%s-ABS(%s-%s))/2)' % (E, hi, E, hi)
    return '(((%s-%s+1)+ABS(%s-%s+1))/2)' % (b, a, b, a)
def MINV(cond, col): return 'IFERROR(1000000-ROUND(1/(1/SUMPRODUCT(MAX((%s)*(1000000-%s)))),0),"")' % (cond, col)
def MAXV(cond, col): return 'IFERROR(ROUND(1/(1/SUMPRODUCT(MAX((%s)*(%s)))),0),"")' % (cond, col)
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)
def CENTER(): return CA('center', 'Business', 'text', '{set:company}', 22)
def PHONE_IF(cond, phone, k, label): return CA(k, label, 'text', 'IF(%s,%s,"")' % (cond, phone), 18)
def LIT(p): return '"%s"' % p
def CARS(x): return '(COUNTIFS(%s,"<="&%s)-COUNTIFS(%s,"<"&%s))' % (VH('purchase_date'), x, VH('sold_date'), x)         # cars in the fleet on a date
def SVC(x): return 'COUNTIFS(%s,"<="&%s,%s,">="&%s)' % (BL('date'), x, BL('end_date'), x)                              # cars in a service block on a date
def CLS_BUF(x): return 'IFERROR(INDEX({range:classes.buffer_min},MATCH(%s,{range:classes.class},0)),0)' % x

settings = [
    S('company', 'Your business name', 'text', COMPANY), S('util_target', 'Fleet utilisation target (example, set your own)', 'pct', 0.75),
    S('util_red', 'Utilisation below this is red (example, set your own)', 'pct', UTIL_RED), S('util_green', 'Utilisation at or above this is green (example)', 'pct', UTIL_GREEN),
    S('late_grace_min', 'Late return grace in minutes', 'int', LATE_GRACE_MIN), S('late_fee_hour', 'Late return fee for each started hour', 'money', LATE_FEE_HOUR),
    S('free_cancel_days', 'Days of notice for a free cancellation', 'int', 2), S('cancel_fee', 'Late cancellation fee', 'money', 20), S('cancel_limit', 'Most cancellations you accept, share of bookings', 'pct', 0.08),
    S('net_adr_target', 'Net daily rate you want to hold, after fees', 'money', 72), S('weekend_target', 'Weekend booked share that closes a listing', 'pct', 0.85),
    S('margin_cars', 'Cars you keep back for late returns', 'int', 1), S('hour_capacity', 'Pickups and returns one staff member handles in an hour', 'int', 3),
    S('idle_gap_days', 'Idle days in a row that need action', 'int', 3), S('tight_turn_hours', 'A turn under this many hours is tight (example)', 'int', 20),
    S('miles_day', 'Included miles a day (miles are the demo unit, set your own)', 'int', 150), S('rebook_pct', 'Discount for a renter who books again', 'pct', 0.05),
    S('upgrade_free', 'Most a day you absorb in a free upgrade', 'money', 20), S('pace_tol', 'Booking pace counted as on pace within', 'pct', 0.05),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 bookings ------------------------------------------------------------------
H = 'AND({col:status}<>%s,{col:status}<>%s)' % (CAN, NOS)
VEQ = '(%s={col:vehicle})' % B('vehicle'); IDN = '(%s<>{col:booking_id})' % B('booking_id')
tables.append(T('bookings', 'Bookings', 'Bookings of the last 13 months and the next 7 weeks',
    'One row per booking: dates, times, car, renter, channel and total; days, fees, net rate, overlap and turnaround verdict fill in by themselves (miles are the demo unit).', [
    C('booking_id', 'Booking ID', 'text', 10, required=True), C('created_on', 'Booked on', 'date', 11), C('start_date', 'Start date', 'date', 11), C('end_date', 'End date', 'date', 11), C('pickup_time', 'Pickup time', 'time', 9),
    C('return_time', 'Return time', 'time', 9), C('vehicle_id', 'Vehicle ID', 'text', 9), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 22), LST('class', 'Class', 'class', 12), C('renter', 'Renter', 'text', 16), C('phone', 'Renter phone', 'text', 18),
    LST('channel', 'Channel', 'channel', 16), LST('plan', 'Plan', 'plan', 9), LST('season', 'Season', 'season', 10), C('total', 'Total', 'money', 11), LST('pickup_location', 'Pickup location', 'location', 16),
    LST('start_day', 'Pickup weekday', 'wday', 11), LST('end_day', 'Return weekday', 'wday', 11), LST('status', 'Status', 'bstatus', 11),
    CA('days', 'Days', 'int', '{col:end_date}-{col:start_date}+1', 7), CA('lead_days', 'Lead time days', 'int', '{col:start_date}-{col:created_on}', 9),
    CA('fee_pct', 'Channel fee share', 'pct', 'IFERROR(INDEX({range:channels.fee_pct},MATCH({col:channel},{range:channels.channel},0)),0)', 9),
    CA('channel_fee', 'Channel fee', 'money', 'ROUND({col:total}*{col:fee_pct},2)', 10), CA('net_amount', 'Net amount', 'money', '{col:total}-{col:channel_fee}', 11),
    CA('net_per_day', 'Net rate per day', 'money', 'IF({col:days}>0,ROUND({col:net_amount}/{col:days},2),0)', 10), CA('buffer_min', 'Buffer minutes', 'int', CLS_BUF('{col:class}'), 9),
    CA('overlap_n', 'Overlapping bookings', 'int', 'IF(%s,COUNTIFS(%s,{col:vehicle},%s,"<="&{col:end_date},%s,">="&{col:start_date}%s)-1,0)' % (H, B('vehicle'), B('start_date'), B('end_date'), HOLDC), 10),
    CA('prev_end', 'Previous booking ended', 'date', 'IF(%s,IFERROR(ROUND(1/(1/SUMPRODUCT(MAX(%s*%s*%s*(%s<={col:start_date})*%s))),0),""),"")' % (H, VEQ, IDN, HOLDA, B('end_date'), B('end_date')), 11),
    CA('gap_min', 'Minutes since the previous return', 'int', 'IF({col:prev_end}="","",ROUND((({col:start_date}+{col:pickup_time})-({col:prev_end}+SUMPRODUCT(%s*%s*%s*(%s={col:prev_end})*%s)))*1440,0))' % (VEQ, IDN, HOLDA, B('end_date'), B('return_time')), 11),
    CA('clash_with', 'Overlaps booking', 'text', 'IF({col:overlap_n}>0,IFERROR(INDEX(%s,MATCH({col:vehicle}&"|"&SUMPRODUCT(MAX(%s*%s*%s*(%s<={col:end_date})*(%s>={col:start_date})*%s)),%s,0)),""),"")' % (
        B('booking_id'), VEQ, IDN, HOLDA, B('start_date'), B('end_date'), B('start_date'), B('vkey')), 11),
    CA('vkey', 'Vehicle and start key', 'text', 'IF(%s,{col:vehicle}&"|"&{col:start_date},"")' % H, 12),
    CA('turn', 'Turnaround verdict', 'text', 'IF(NOT(%s),%s,IF({col:overlap_n}>0,%s,IF({col:gap_min}="",%s,IF({col:gap_min}<{col:buffer_min},%s,IF({col:gap_min}<{set:tight_turn_hours}*60,%s,%s)))))' % (
        H, v('Not holding the car'), v('Overlaps another booking'), v('Clear'), v('Inside turnaround time'), v('Tight turn'), v('Clear')), 22),
    CA('saving', 'Rebook saving', 'money', 'ROUND({col:total}*{set:rebook_pct},0)', 9),
    PHONE_IF('AND({col:pickup_location}<>%s,%s)' % (MAIN, H), '{col:phone}', 'deliv_phone', 'Delivery phone'),
    PHONE_IF('AND({col:status}=%s,{col:created_on}>={today}-2)' % BKD, '{col:phone}', 'pay_phone', 'Payment reminder phone'),
    PHONE_IF('AND({col:status}=%s,{col:end_date}>={today}-30)' % CMP, '{col:phone}', 'rebook_phone', 'Rebook phone'),
    PHONE_IF('AND({col:channel}=%s,{col:status}=%s)' % (CH['Corporate account'], BKD), '{col:phone}', 'corp_phone', 'Corporate phone'),
    PHONE_IF('AND({col:channel}=%s,{col:status}=%s)' % (CH['Hotel partner'], BKD), LIT(D.HOTEL_PHONE), 'hotel_phone', 'Hotel partner phone'), CENTER()],
    D.bookings_d(), 2000, [A('overlap_n', '> 0', 'bad'), A('turn', '= ' + v('Tight turn'), 'warn'), A('turn', '= ' + v('Inside turnaround time'), 'bad'), A('status', '= ' + CAN, 'warn'), A('status', '= ' + NOS, 'bad'), A('status', '= ' + ACT, 'good')]))
# 2 vehicles ------------------------------------------------------------------
LO90 = 'MAX({col:purchase_date},{today}-90)'
tables.append(T('vehicles', 'Vehicles', 'Vehicles with status today and utilisation',
    'One row per vehicle with its class, dates and odometer; the status today, the next booking and the utilisation of the last 90 days fill in.', [
    C('vehicle_id', 'Vehicle ID', 'text', 9, required=True), C('fleet_no', 'Fleet number', 'int', 8), C('vehicle', 'Vehicle', 'text', 22), C('plate', 'Plate', 'text', 11), LST('class', 'Class', 'class', 12), LST('status', 'Status', 'vstatus', 12),
    C('purchase_date', 'Purchase date', 'date', 11), C('sold_date', 'Sold date', 'date', 11), C('odometer', 'Odometer miles', 'int', 10),
    CA('today_status', 'Status today', 'text', 'IF({col:status}=%s,%s,IF(%s>0,%s,IF(COUNTIFS(%s,{col:vehicle},%s,"<="&{today},%s,">="&{today},%s,%s)>0,%s,IF(COUNTIFS(%s,{col:vehicle},%s,"<="&{today},%s,">="&{today},%s,%s)>0,%s,%s))))' % (
        SOLD, '{list:vstatus.sold}', 'COUNTIFS(%s,{col:vehicle},%s,"<="&{today},%s,">="&{today})' % (BL('vehicle'), BL('date'), BL('end_date')), SERV,
        B('vehicle'), B('start_date'), B('end_date'), B('status'), ACT, RENT, B('vehicle'), B('start_date'), B('end_date'), B('status'), BKD, RESV, FREE), 12),
    CA('next_start', 'Next booking starts', 'date', 'IF({col:status}=%s,"",%s)' % (SOLD, MINV('%s*%s*(%s>={today})' % (VEQ, HOLDA, B('start_date')), B('start_date'))), 11),
    CA('util_90', 'Utilisation, last 90 days', 'pct', 'IF({col:status}=%s,"",ROUND(SUMPRODUCT(%s*%s*%s)/MAX(1,{today}-%s),3))' % (SOLD, VEQ, HOLDA, OVL(LO90, '({today}-1)', B('start_date'), B('end_date')), LO90), 10), CENTER()],
    D.vehicles_d(), 60, [A('status', '= ' + SOLD, 'bad'), A('status', '= ' + tok('vstatus', 'In workshop'), 'warn'), A('util_90', '< {set:util_red}', 'bad'), A('util_90', '>= {set:util_green}', 'good')]))
# 3 vehicle classes -----------------------------------------------------------
tables.append(T('classes', 'Vehicle classes', 'Vehicle classes with the turnaround buffer',
    'One row per vehicle class: the minutes the car needs between a return and the next pickup (cleaning and checks, your own setting) and the seats.', [
    LST('class', 'Class', 'class', 14, required=True), C('buffer_min', 'Buffer minutes', 'int', 10), C('seats', 'Seats', 'int', 8)], D.classes_d(), 50))
# 4 service blocks ------------------------------------------------------------
tables.append(T('service_blocks', 'Service blocks', 'Service blocks that take a car off the calendar',
    'One row per service or repair block: the car, the start date and the days off the road; the end date, class and the messages for the manager and a marketplace fill in.', [
    C('block_id', 'Block ID', 'text', 9, required=True), C('vehicle_id', 'Vehicle ID', 'text', 9), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 22), C('date', 'Start date', 'date', 11), LST('kind', 'Service kind', 'mkind', 14),
    C('days_off_road', 'Days off road', 'int', 8),
    CA('end_date', 'End date', 'date', '{col:date}+{col:days_off_road}-1', 11), CA('class', 'Class', 'text', LKT('vehicles.class', 'vehicles.vehicle', 'vehicle'), 12),
    PHONE_IF('{col:date}>={today}', LIT(D.MANAGER_PHONE), 'mgr_phone', 'Manager phone'), PHONE_IF('{col:date}>={today}', LIT(D.MKT_PHONE), 'mkt_phone', 'Marketplace support phone'), CENTER()],
    D.blocks_d(), 400, [A('date', '> {today}', 'warn'), A('days_off_road', '>= 3', 'bad')]))
# 5 calendar by vehicle and day -----------------------------------------------
CVEH = '(%s={col:vehicle})' % CVD('vehicle')
tables.append(T('cal_vehicle', 'Calendar by vehicle and day', 'Booking calendar by vehicle for the next 14 days',
    'One row per vehicle and day: rented, reserved, service or free, with the booking and channel; every row fills in from Bookings and Service blocks.', [
    C('row_id', 'Row', 'text', 9, required=True), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 22), C('date', 'Date', 'date', 11),
    CA('class', 'Class', 'text', LKT('vehicles.class', 'vehicles.vehicle', 'vehicle'), 12),
    CA('b_start', 'Booking started', 'date', 'IFERROR(ROUND(1/(1/SUMPRODUCT(MAX(%s*%s*(%s<={col:date})*(%s>={col:date})*%s))),0),"")' % (VEQ.replace('{col:vehicle}', '{col:vehicle}'), HOLDA, B('start_date'), B('end_date'), B('start_date')), 11),
    CA('booking_id', 'Booking', 'text', 'IF({col:b_start}="","",IFERROR(INDEX(%s,MATCH({col:vehicle}&"|"&{col:b_start},%s,0)),""))' % (B('booking_id'), B('vkey')), 10),
    CA('status', 'Status', 'text', 'IF(%s>0,%s,IF({col:booking_id}="",%s,IF(IFERROR(INDEX(%s,MATCH({col:booking_id},%s,0)),"")=%s,%s,%s)))' % (
        'COUNTIFS(%s,{col:vehicle},%s,"<="&{col:date},%s,">="&{col:date})' % (BL('vehicle'), BL('date'), BL('end_date')), SERV, FREE, B('status'), B('booking_id'), ACT, RENT, RESV), 10),
    CA('channel', 'Channel', 'text', 'IF({col:booking_id}="","",IFERROR(INDEX(%s,MATCH({col:booking_id},%s,0)),""))' % (B('channel'), B('booking_id')), 16),
    CA('free_cum', 'Free day number', 'int', 'IF({col:status}=%s,COUNTIFS(%s,{col:vehicle},%s,"<="&{col:date},%s,%s),"")' % (FREE, CVD('vehicle'), CVD('date'), CVD('status'), FREE), 9)],
    D.cal_vehicle_d(), 450, [A('status', '= ' + FREE, 'good'), A('status', '= ' + SERV, 'warn'), A('status', '= ' + RENT, 'bad')]))
# 6 calendar by class and day -------------------------------------------------
tables.append(T('cal_class', 'Calendar by class and day', 'Booking calendar by class for the next 14 days',
    'One row per class and day: cars in the fleet, booked, in service and free; the free share and the first free day of each class fill in.', [
    C('row_id', 'Row', 'text', 9, required=True), LST('class', 'Class', 'class', 13), C('date', 'Date', 'date', 11),
    CA('vehicles', 'Cars in the fleet', 'int', '(COUNTIFS(%s,{col:class},%s,"<="&{col:date})-COUNTIFS(%s,{col:class},%s,"<"&{col:date}))' % (VH('class'), VH('purchase_date'), VH('class'), VH('sold_date')), 9),
    CA('booked', 'Cars booked', 'int', 'COUNTIFS(%s,{col:class},%s,"<="&{col:date},%s,">="&{col:date}%s)' % (B('class'), B('start_date'), B('end_date'), HOLDC), 9),
    CA('service', 'Cars in service', 'int', 'COUNTIFS(%s,{col:class},%s,"<="&{col:date},%s,">="&{col:date})' % (BL('class'), BL('date'), BL('end_date')), 9),
    CA('free', 'Cars free', 'int', 'MAX(0,{col:vehicles}-{col:booked}-{col:service})', 8), CA('free_share', 'Free share', 'pct', 'IF({col:vehicles}>0,{col:free}/{col:vehicles},0)', 9),
    CA('free_cum', 'Free day number', 'int', 'IF({col:free}>0,COUNTIFS(%s,{col:class},%s,"<="&{col:date},%s,">0"),"")' % (CCD('class'), CCD('date'), CCD('free')), 9),
    CA('free_key', 'Free day key', 'num', 'IF({col:free}>0,MATCH({col:class},{range:classes.class},0)*100000+{col:date},"")', 10),
    CA('full_date', 'Full on', 'date', 'IF({col:free}=0,{col:date},"")', 11),
    PHONE_IF('AND({col:free}=0,{col:date}>={today})', LIT(D.OWNER_PHONE), 'owner_phone', 'Owner phone'), CENTER()],
    D.cal_class_d(), 100, [A('free', '= 0', 'bad'), A('free_share', '< 0.2', 'warn')]))
# 7 next free date by vehicle -------------------------------------------------
tables.append(T('next_free_veh', 'Next free date by vehicle', 'Next free date of every car',
    'One row per car in the fleet: the status today, the first free date from the calendar, the next booking after it and the days free before that.', [
    C('vehicle_id', 'Vehicle ID', 'text', 9, required=True),
    CA('vehicle', 'Vehicle', 'text', LKT('vehicles.vehicle', 'vehicles.vehicle_id', 'vehicle_id'), 22), CA('class', 'Class', 'text', LKT('vehicles.class', 'vehicles.vehicle_id', 'vehicle_id'), 12),
    CA('state', 'Status today', 'text', LKT('vehicles.today_status', 'vehicles.vehicle_id', 'vehicle_id'), 11),
    CA('first_free', 'First free date', 'date', 'IF(SUMIFS(%s,%s,{col:vehicle},%s,1,%s,%s)>0,SUMIFS(%s,%s,{col:vehicle},%s,1,%s,%s),IFERROR(ROUND(1/(1/SUMPRODUCT(MAX((%s={col:vehicle})*%s*(%s<={today}+13)*(%s>={today}+13)*%s))),0)+1,{today}+14))' % (
        CVD('date'), CVD('vehicle'), CVD('free_cum'), CVD('status'), FREE, CVD('date'), CVD('vehicle'), CVD('free_cum'), CVD('status'), FREE, B('vehicle'), HOLDA, B('start_date'), B('end_date'), B('end_date')), 11),
    CA('wait_days', 'Days until free', 'int', '{col:first_free}-{today}', 8),
    CA('next_start', 'Next booking after it', 'date', MINV('(%s={col:vehicle})*%s*(%s>{col:first_free})' % (B('vehicle'), HOLDA, B('start_date')), B('start_date')), 11),
    CA('free_days', 'Days free before it', 'int', 'IF({col:next_start}="","",{col:next_start}-{col:first_free})', 9),
    PHONE_IF('{col:wait_days}>=0', LIT(D.MECHANIC_PHONE), 'mech_phone', 'Mechanic phone'), CENTER()],
    D.next_free_veh_d(), 60, [A('wait_days', '> 7', 'warn'), A('wait_days', '= 0', 'good')]))
# 8 next free date by class ---------------------------------------------------
tables.append(T('next_free_class', 'Next free date by class', 'Next free date of every class',
    'One row per class: the first day in the next 14 days with a free car and how many cars are free that day.', [
    LST('class', 'Class', 'class', 14, required=True),
    CA('first_free', 'First free date', 'date', 'IF(SUMIFS(%s,%s,{col:class},%s,1)>0,SUMIFS(%s,%s,{col:class},%s,1),"")' % (CCD('date'), CCD('class'), CCD('free_cum'), CCD('date'), CCD('class'), CCD('free_cum')), 12),
    CA('free_cars', 'Free cars that day', 'int', 'IF({col:first_free}="",0,SUMIFS(%s,%s,{col:class},%s,{col:first_free}))' % (CCD('free'), CCD('class'), CCD('date')), 10)],
    D.next_free_class_d(), 50))
# 9 overlap check -------------------------------------------------------------
def LKB(c): return LKT('bookings.' + c, 'bookings.booking_id', 'booking_id')
def LKBN(c): return LKN('bookings.' + c, 'bookings.booking_id', 'booking_id')
def LKBD(c): return LKD('bookings.' + c, 'bookings.booking_id', 'booking_id')
tables.append(T('overlap_check', 'Overlap check', 'Double-booking check of the next 14 days',
    'One row per booking out now or starting in the next 14 days: the previous booking, the gap in minutes and a verdict; the owner and manager messages go out only for an overlap.', [
    C('booking_id', 'Booking ID', 'text', 10, required=True), CA('vehicle', 'Vehicle', 'text', LKB('vehicle'), 22), CA('class', 'Class', 'text', LKB('class'), 12), CA('channel', 'Channel', 'text', LKB('channel'), 16),
    CA('start_date', 'Start date', 'date', LKBD('start_date'), 11), CA('end_date', 'End date', 'date', LKBD('end_date'), 11), CA('created_on', 'Booked on', 'date', LKBD('created_on'), 11),
    CA('prev_end', 'Previous booking ended', 'date', LKBD('prev_end'), 11), CA('gap_min', 'Minutes since the previous return', 'int', 'IFERROR(INDEX(%s,MATCH({col:booking_id},%s,0)),"")' % (B('gap_min'), B('booking_id')), 11),
    CA('buffer_min', 'Buffer minutes', 'int', LKBN('buffer_min'), 9), CA('verdict', 'Verdict', 'text', LKB('turn'), 24), CA('clash_with', 'Overlaps booking', 'text', LKB('clash_with'), 11),
    CA('overlap_count', 'Overlapping bookings now', 'int', 'COUNTIFS(%s,">0",%s,">="&{today})' % (B('overlap_n'), B('end_date')), 10),
    PHONE_IF('{col:clash_with}<>""', LIT(D.OWNER_PHONE), 'owner_phone', 'Owner phone'), PHONE_IF('{col:clash_with}<>""', LIT(D.MANAGER_PHONE), 'mgr_phone', 'Manager phone'), CENTER()],
    D.overlap_d(), 150, [A('verdict', '= ' + v('Overlaps another booking'), 'bad'), A('verdict', '= ' + v('Inside turnaround time'), 'bad'), A('verdict', '= ' + v('Tight turn'), 'warn'), A('verdict', '= ' + v('Clear'), 'good')]))
# 10 pickups and returns ------------------------------------------------------
PKT = tok('pkind', 'Pickup'); RTT = tok('pkind', 'Return')
NXT = '(%s={col:vehicle})*%s*(%s>={col:date})*(%s<>{col:booking_id})' % (B('vehicle'), HOLDA, B('start_date'), B('booking_id'))
tables.append(T('pickups_returns', 'Pickups and returns', 'Pickups and returns of the next 7 days',
    'One row per pickup or return: time, location, renter and, for a return, the next pickup of the same car and what a late return does to it.', [
    C('slot_id', 'Slot', 'text', 9, required=True), C('date', 'Date', 'date', 11), LST('kind', 'Pickup or return', 'pkind', 10), C('booking_id', 'Booking ID', 'text', 10), C('late_minutes', 'Late minutes reported', 'int', 10),
    CA('vehicle', 'Vehicle', 'text', LKB('vehicle'), 22), CA('class', 'Class', 'text', LKB('class'), 12), CA('renter', 'Renter', 'text', LKB('renter'), 16), CA('phone', 'Renter phone', 'text', LKB('phone'), 18),
    CA('location', 'Location', 'text', LKB('pickup_location'), 16),
    CA('time', 'Time', 'time', 'IF({col:kind}=%s,%s,%s)' % (PKT, LKBN('pickup_time'), LKBN('return_time')), 8), CA('hour', 'Hour', 'int', 'INT(ROUND(MOD({col:time},1)*24,4))', 6), CA('hour_load', 'Pickups and returns in that hour', 'int', 'COUNTIFS(%s,{col:date},%s,{col:hour})' % (R('pickups_returns', 'date'), R('pickups_returns', 'hour')), 9),
    CA('gap_in', 'Minutes since the previous return', 'int', 'IF({col:kind}=%s,%s,"")' % (PKT, 'IFERROR(INDEX(%s,MATCH({col:booking_id},%s,0)),"")' % (B('gap_min'), B('booking_id'))), 11),
    CA('next_start', 'Next pickup of the car', 'date', 'IF({col:kind}=%s,%s,"")' % (RTT, MINV(NXT, B('start_date'))), 11),
    CA('next_time', 'Next pickup time', 'time', 'IF({col:next_start}="","",SUMPRODUCT((%s={col:vehicle})*%s*(%s={col:next_start})*(%s<>{col:booking_id})*%s))' % (B('vehicle'), HOLDA, B('start_date'), B('booking_id'), B('pickup_time')), 9),
    CA('gap_after', 'Minutes to next pickup after delay', 'int', 'IF({col:next_start}="","",ROUND((({col:next_start}+{col:next_time})-({col:date}+%s+{col:late_minutes}/1440))*1440,0))' % LKBN('return_time'), 11),
    CA('knock_on', 'Knock-on of a late return', 'text', 'IF({col:gap_after}="",%s,IF({col:gap_after}<%s,%s,IF({col:gap_after}<{set:tight_turn_hours}*60,%s,%s)))' % (
        v('No effect'), CLS_BUF('{col:class}'), v('Move the next pickup'), v('Call the renter'), v('No effect')), 22),
    CA('ready', 'Car ready on time', 'text', 'IF({col:kind}=%s,IF(OR({col:gap_in}="",{col:gap_in}>={set:tight_turn_hours}*60),%s,%s),IF({col:knock_on}=%s,%s,%s))' % (PKT, v('Car ready'), v('Check the car'), v('No effect'), v('Car ready'), v('Check the car')), 12),
    PHONE_IF('AND({col:kind}=%s,{col:date}={today}+1)' % PKT, '{col:phone}', 'pickup_phone', 'Pickup reminder phone'), PHONE_IF('AND({col:kind}=%s,{col:date}>={today})' % RTT, '{col:phone}', 'return_phone', 'Return reminder phone'),
    PHONE_IF('AND({col:kind}=%s,{col:late_minutes}>0)' % RTT, '{col:phone}', 'late_phone', 'Late return phone'),
    PHONE_IF('AND({col:kind}=%s,{col:location}<>%s)' % (PKT, MAIN), LIT(D.DRIVER_PHONE), 'delivery_phone', 'Driver delivery phone'), PHONE_IF('AND({col:kind}=%s,{col:location}<>%s)' % (RTT, MAIN), LIT(D.DRIVER_PHONE), 'collect_phone', 'Driver collection phone'),
    PHONE_IF('{col:kind}=%s' % RTT, LIT(D.DETAILER_PHONE), 'detailer_phone', 'Detailer phone'),
    PHONE_IF('AND({col:kind}=%s,ISNUMBER({col:gap_in}),{col:gap_in}<{set:tight_turn_hours}*120)' % PKT, LIT(D.DETAILER_PHONE), 'rush_phone', 'Detailer rush phone'), CENTER()],
    D.pr_d(), 150, [A('knock_on', '= ' + v('Call the renter'), 'warn'), A('knock_on', '= ' + v('Move the next pickup'), 'bad'), A('late_minutes', '> 0', 'warn')]))
# 11 extension requests -------------------------------------------------------
EX_LIM = 'IF({col:next_start}="",{col:next_block},IF({col:next_block}="",{col:next_start},MIN({col:next_start},{col:next_block})))'
def FREEVEH(cls, lo, hi, extra=''):
    """cars of a class that no booking and no service block touches between lo and hi (array formula inside SUMPRODUCT, no CSE needed)"""
    return ('(%s=%s)*(%s<>%s)*(%s<=%s)%s*(COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s%s)=0)*(COUNTIFS(%s,%s,%s,"<="&%s,%s,">="&%s)=0)' % (
        VH('class'), cls, VH('status'), SOLD, VH('purchase_date'), hi, extra, B('vehicle'), VH('vehicle'), B('start_date'), hi, B('end_date'), lo, HOLDC, BL('vehicle'), VH('vehicle'), BL('date'), hi, BL('end_date'), lo))
tables.append(T('extensions', 'Extension requests', 'Extension requests and what the calendar allows',
    'One row per request to keep a car longer: the current and requested end; the next booking and service block, the free cars of the class, the extra revenue and a verdict fill in.', [
    C('ext_id', 'Request', 'text', 9, required=True), C('booking_id', 'Booking ID', 'text', 10), C('requested_on', 'Requested on', 'date', 11), C('current_end', 'Current end date', 'date', 11), C('requested_end', 'Requested end date', 'date', 11),
    LST('decision', 'Decision', 'extdec', 10),
    CA('vehicle', 'Vehicle', 'text', LKB('vehicle'), 22), CA('class', 'Class', 'text', LKB('class'), 12), CA('renter', 'Renter', 'text', LKB('renter'), 16), CA('phone', 'Renter phone', 'text', LKB('phone'), 18),
    CA('extra_days', 'Extra days', 'int', '{col:requested_end}-{col:current_end}', 7),
    CA('next_start', 'Next booking starts', 'date', MINV('(%s={col:vehicle})*%s*(%s>{col:current_end})*(%s<>{col:booking_id})' % (B('vehicle'), HOLDA, B('start_date'), B('booking_id')), B('start_date')), 11),
    CA('next_block', 'Next service block', 'date', MINV('(%s={col:vehicle})*(%s>{col:current_end})' % (BL('vehicle'), BL('date')), BL('date')), 11),
    CA('day_rate', 'Day rate booked', 'money', 'IFERROR(ROUND(%s/%s,2),0)' % ('INDEX(%s,MATCH({col:booking_id},%s,0))' % (B('total'), B('booking_id')), 'INDEX(%s,MATCH({col:booking_id},%s,0))' % (B('days'), B('booking_id'))), 10),
    CA('extra_amount', 'Extra amount', 'money', 'ROUND({col:extra_days}*{col:day_rate},2)', 10),
    CA('free_alt', 'Free cars of the class', 'int', 'SUMPRODUCT(%s)' % FREEVEH('{col:class}', '({col:current_end}+1)', '{col:requested_end}'), 9),
    CA('alt_no', 'Alternative fleet number', 'int', 'IF({col:free_alt}>0,SUMPRODUCT(MIN(%s*%s+(1-%s)*1000000)),"")' % ('(%s)' % FREEVEH('{col:class}', '({col:current_end}+1)', '{col:requested_end}'), VH('fleet_no'), '(%s)' % FREEVEH('{col:class}', '({col:current_end}+1)', '{col:requested_end}')), 9),
    CA('vehicle_alt', 'Alternative vehicle', 'text', 'IF({col:alt_no}="","",IFERROR(INDEX(%s,MATCH({col:alt_no},%s,0)),""))' % (VH('vehicle'), VH('fleet_no')), 22),
    CA('can', 'Fit code, 1 same car, 2 swap, 0 none', 'int', 'IF(OR(%s="",{col:requested_end}<%s),1,IF({col:free_alt}>0,2,0))' % (EX_LIM, EX_LIM), 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:can}=1,%s,IF({col:can}=2,%s&" "&{col:vehicle_alt},%s))' % (v('Extend'), v('Extend with a swap to'), v('Cannot extend')), 30),
    PHONE_IF('AND({col:can}=1,{col:decision}=%s)' % tok('extdec', 'Approved'), '{col:phone}', 'ok_phone', 'Extension confirmed phone'), PHONE_IF('AND({col:can}=0,{col:decision}<>%s)' % tok('extdec', 'Approved'), '{col:phone}', 'no_phone', 'Cannot extend phone'),
    PHONE_IF('AND({col:can}=2,{col:decision}<>%s)' % tok('extdec', 'Approved'), '{col:phone}', 'alt_phone', 'Offer alternative phone'), CENTER()],
    D.ext_d(), 80, [A('verdict', '= ' + v('Cannot extend'), 'bad'), A('decision', '= ' + tok('extdec', 'Open'), 'warn'), A('decision', '= ' + tok('extdec', 'Declined'), 'bad')]))
# 12 vehicle swaps ------------------------------------------------------------
def ADR_CLASS(cls): return 'IFERROR(SUMIFS(%s,%s,%s,%s,">="&({today}-180),%s,"<="&{today}%s)/SUMIFS(%s,%s,%s,%s,">="&({today}-180),%s,"<="&{today}%s),0)' % (
    B('total'), B('class'), cls, B('start_date'), B('start_date'), HOLDC, B('days'), B('class'), cls, B('start_date'), B('start_date'), HOLDC)
tables.append(T('swaps', 'Vehicle swaps', 'Mid-rental vehicle swaps',
    'One row per swap of the car during a rental: the old and new car and the swap date; the class, the day rate and the miles allowance from the swap day fill in.', [
    C('swap_id', 'Swap', 'text', 9, required=True), C('booking_id', 'Booking ID', 'text', 10), REF('from_vehicle', 'From vehicle', 'vehicles.vehicle', 22), REF('to_vehicle', 'To vehicle', 'vehicles.vehicle', 22), C('swap_date', 'Swap date', 'date', 11),
    LST('reason', 'Reason', 'swapwhy', 14),
    CA('from_class', 'From class', 'text', LKT('vehicles.class', 'vehicles.vehicle', 'from_vehicle'), 12), CA('to_class', 'To class', 'text', LKT('vehicles.class', 'vehicles.vehicle', 'to_vehicle'), 12),
    CA('same_class', 'Same class', 'text', 'IF({col:from_class}={col:to_class},%s,%s)' % (YES, NO), 9), CA('renter', 'Renter', 'text', LKB('renter'), 16), CA('phone', 'Renter phone', 'text', LKB('phone'), 18),
    CA('end_date', 'Rental ends', 'date', LKBD('end_date'), 11), CA('days_left', 'Days left', 'int', 'MAX(0,{col:end_date}-{col:swap_date}+1)', 8),
    CA('old_rate', 'Day rate booked', 'money', 'IFERROR(ROUND(INDEX(%s,MATCH({col:booking_id},%s,0))/INDEX(%s,MATCH({col:booking_id},%s,0)),2),0)' % (B('total'), B('booking_id'), B('days'), B('booking_id')), 10),
    CA('from_adr', 'Average rate of the old class', 'money', ADR_CLASS('{col:from_class}'), 10), CA('to_adr', 'Average rate of the new class', 'money', ADR_CLASS('{col:to_class}'), 10),
    CA('new_rate', 'New day rate', 'money', 'IF({col:same_class}=%s,{col:old_rate},IF({col:from_adr}>0,ROUND({col:old_rate}*{col:to_adr}/{col:from_adr},2),{col:old_rate}))' % YES, 10),
    CA('miles_allowance', 'Miles allowance from the swap', 'int', '{col:days_left}*{set:miles_day}', 10), CA('rate_change', 'Change in the rental amount', 'money', 'ROUND(({col:new_rate}-{col:old_rate})*{col:days_left},2)', 11),
    PHONE_IF('{col:swap_date}>={today}-3', '{col:phone}', 'swap_phone', 'Swap notice phone'), PHONE_IF('{col:swap_date}>={today}-3', LIT(D.MANAGER_PHONE), 'mgr_phone', 'Manager phone'), CENTER()],
    D.swaps_d(), 80, [A('same_class', '= ' + NO, 'warn')]))
# 13 channel revenue by month -------------------------------------------------
W3 = '{range:channel_month.month},">="&EDATE(%s,-2),{range:channel_month.month},"<="&%s'
CMW = '%s,{col:channel},%s,">="&{col:month},%s,"<"&EDATE({col:month},1)%s' % (B('channel'), B('start_date'), B('start_date'), HOLDC)
tables.append(T('channel_month', 'Channel revenue by month', 'Revenue, fee and net rate per day by channel and month',
    'One row per month and channel: bookings, rented days, revenue, fee and net; the net rate per day and what the fee costs a rented day fill in from Bookings.', [
    C('row_id', 'Row', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('channel', 'Channel', 'channel', 16),
    CA('bookings', 'Bookings', 'int', 'COUNTIFS(%s)' % CMW, 9), CA('rented_days', 'Rented days', 'int', 'SUMIFS(%s,%s)' % (B('days'), CMW), 9), CA('revenue', 'Revenue', 'money', 'SUMIFS(%s,%s)' % (B('total'), CMW), 12),
    CA('fee', 'Channel fee', 'money', 'SUMIFS(%s,%s)' % (B('channel_fee'), CMW), 11), CA('net', 'Net', 'money', '{col:revenue}-{col:fee}', 12), CA('net_per_day', 'Net rate per day', 'money', 'IF({col:rented_days}>0,ROUND({col:net}/{col:rented_days},2),0)', 10),
    CA('own', 'Own channel', 'int', 'IF(OR({col:channel}=%s,{col:channel}=%s,{col:channel}=%s),1,0)' % (CH['Website'], CH['Phone'], CH['Corporate account']), 7),
    CA('market', 'Marketplace', 'int', 'IF(OR({col:channel}=%s,{col:channel}=%s),1,0)' % (CH['Marketplace A'], CH['Marketplace B']), 7),
    CA('own_nd3', 'Own channels net per day, last 3 months', 'money', 'IFERROR(SUMIFS({range:channel_month.net},%s,{range:channel_month.own},1)/SUMIFS({range:channel_month.rented_days},%s,{range:channel_month.own},1),0)' % (W3 % (MS, MS), W3 % (MS, MS)), 11),
    CA('mkt_nd3', 'Marketplaces net per day, last 3 months', 'money', 'IFERROR(SUMIFS({range:channel_month.net},%s,{range:channel_month.market},1)/SUMIFS({range:channel_month.rented_days},%s,{range:channel_month.market},1),0)' % (W3 % (MS, MS), W3 % (MS, MS)), 11),
    CA('days3', 'Rented days, last 3 months', 'int', 'SUMIFS({range:channel_month.rented_days},%s)' % (W3 % (MS, MS)), 9),
    CA('mkt_share3', 'Marketplace share of days, last 3 months', 'pct', 'IFERROR(SUMIFS({range:channel_month.rented_days},%s,{range:channel_month.market},1)/{col:days3},0)' % (W3 % (MS, MS)), 10),
    CA('fee_per_day', 'Fee a rented day', 'money', 'IF({col:rented_days}>0,ROUND({col:fee}/{col:rented_days},2),0)', 10),
    PHONE_IF('AND({col:channel}=%s,{col:bookings}>0)' % CH['Corporate account'], LIT(D.CORP_PHONE), 'corp_phone', 'Corporate account phone'), PHONE_IF('AND({col:channel}=%s,{col:bookings}>0)' % CH['Hotel partner'], LIT(D.HOTEL_PHONE), 'hotel_phone', 'Hotel partner phone'),
    PHONE_IF('AND(OR({col:channel}=%s,{col:channel}=%s),{col:month}=%s,{col:fee}>0)' % (CH['Marketplace A'], CH['Marketplace B'], MS), LIT(D.OWNER_PHONE), 'owner_phone', 'Owner phone'),
    PHONE_IF('AND({col:month}=%s,{col:bookings}>0)' % MS, LIT(D.BOOKKEEPER_PHONE), 'bookkeeper_phone', 'Bookkeeper phone'), CENTER()],
    D.channel_month_d(), 100, [A('fee_per_day', '> 15', 'warn')]))
# 14 channels -----------------------------------------------------------------
tables.append(T('channels', 'Channels', 'Booking channels with the fee share and payout days',
    'One row per channel: the share it keeps (a car-sharing marketplace keeps a share of every rental) and the days until it pays you.', [
    LST('channel', 'Channel', 'channel', 18, required=True), C('fee_pct', 'Channel fee share', 'pct', 11), C('payout_days', 'Payout days', 'int', 9)], D.channels_d(), 50))
# 15 idle gaps ----------------------------------------------------------------
tables.append(T('idle_gaps', 'Idle gaps', 'Idle gaps of the next 14 days',
    'One row per run of free days of a car: the first free day; the last free day, the idle days and a verdict fill in from the calendar by vehicle (idle days: days a car is available but not rented).', [
    C('gap_id', 'Gap', 'text', 9, required=True), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 22), C('gap_from', 'From', 'date', 11), LST('class', 'Class', 'class', 12),
    CA('gap_to', 'To', 'date', 'MIN({today}+13,SUMPRODUCT(MIN((%s=%s)*(%s>{col:gap_from})*(%s<>%s)*%s+(1-(%s=%s)*(%s>{col:gap_from})*(%s<>%s))*1000000))-1)' % (
        CVD('vehicle'), Cc('vehicle'), CVD('date'), CVD('status'), FREE, CVD('date'), CVD('vehicle'), Cc('vehicle'), CVD('date'), CVD('status'), FREE), 11),
    CA('idle_days', 'Idle days', 'int', '{col:gap_to}-{col:gap_from}+1', 8),
    CA('verdict', 'Verdict', 'text', 'IF({col:idle_days}>={set:idle_gap_days},%s,%s)' % (v('Fill this gap'), v('Short gap')), 14)],
    D.idle_d(), 200, [A('verdict', '= ' + v('Fill this gap'), 'warn')]))
# 16 weekend pressure ---------------------------------------------------------
SAT, SUN = '({col:week}+5)', '({col:week}+6)'
tables.append(T('weekend', 'Weekend pressure', 'Weekend pressure by week',
    'One row per week: the fleet days of the weekend, the booked days and the share; the free cars each day and a verdict (close listing, hold, promote) fill in.', [
    C('week', 'Week starting Monday', 'date', 13, required=True),
    CA('fleet_days', 'Fleet days, Saturday and Sunday', 'int', '%s+%s-%s-%s' % (CARS(SAT), CARS(SUN), SVC(SAT), SVC(SUN)), 11),
    CA('booked_days', 'Booked weekend days', 'int', 'SUMPRODUCT(%s*%s)' % (HOLDA, OVL(SAT, SUN, B('start_date'), B('end_date'))), 11),
    CA('share', 'Weekend booked share', 'pct', 'IF({col:fleet_days}>0,MIN(1,{col:booked_days}/{col:fleet_days}),0)', 10),
    CA('spare_cars', 'Free cars each day', 'num', 'ROUND(MAX(0,{col:fleet_days}-{col:booked_days})/2,1)', 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:share}>={set:weekend_target},%s,IF({col:share}<{set:util_red},%s,%s))' % (v('Close listing'), v('Promote'), v('Hold')), 14)],
    D.weekend_d(), 50, [A('verdict', '= ' + v('Close listing'), 'bad'), A('verdict', '= ' + v('Promote'), 'warn')]))
# 17 bookings by class and month ----------------------------------------------
PE = 'MIN(EOMONTH({col:month},0),{today})'
tables.append(T('class_month', 'Bookings by class and month', 'Bookings, rented days and utilisation by class and month',
    'One row per month and class: bookings, rented days, available days and utilisation (rented days as a share of available days) from Bookings and Vehicles.', [
    C('row_id', 'Row', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('class', 'Class', 'class', 13),
    CA('bookings', 'Bookings started', 'int', 'COUNTIFS(%s,{col:class},%s,">="&{col:month},%s,"<"&EDATE({col:month},1)%s)' % (B('class'), B('start_date'), B('start_date'), HOLDC), 9),
    CA('rented_days', 'Rented days', 'int', 'SUMPRODUCT((%s={col:class})*%s*%s)' % (B('class'), HOLDA, OVL('{col:month}', PE, B('start_date'), B('end_date'))), 9),
    CA('available_days', 'Available days', 'int', 'SUMPRODUCT((%s={col:class})*%s)' % (VH('class'), OVL('{col:month}', PE, VH('purchase_date'), '(%s+(%s=0)*1000000)' % (VH('sold_date'), VH('sold_date')))), 9),
    CA('utilisation', 'Utilisation', 'pct', 'IF({col:available_days}>0,MIN(1,{col:rented_days}/{col:available_days}),0)', 10),
    CA('adr', 'Average daily rate', 'money', 'IFERROR(SUMIFS(%s,%s,{col:class},%s,">="&{col:month},%s,"<"&EDATE({col:month},1)%s)/SUMIFS(%s,%s,{col:class},%s,">="&{col:month},%s,"<"&EDATE({col:month},1)%s),0)' % (
        B('total'), B('class'), B('start_date'), B('start_date'), HOLDC, B('days'), B('class'), B('start_date'), B('start_date'), HOLDC), 11)],
    D.class_month_d(), 100, [A('utilisation', '< {set:util_red}', 'bad'), A('utilisation', '>= {set:util_green}', 'good')]))
# 18 daily fleet status -------------------------------------------------------
tables.append(T('daily_fleet', 'Daily fleet status', 'Daily fleet status, 30 days back and 14 days ahead',
    'One row per day: cars in the fleet, rented, in service and free, the utilisation and the pickups and returns; the owner and manager messages go out for the days ahead.', [
    C('date', 'Date', 'date', 11, required=True), LST('weekday', 'Weekday', 'wday', 11),
    CA('fleet', 'Cars in the fleet', 'int', CARS('{col:date}'), 9),
    CA('rented', 'Cars rented', 'int', 'COUNTIFS(%s,"<="&{col:date},%s,">="&{col:date}%s)' % (B('start_date'), B('end_date'), HOLDC), 9),
    CA('service', 'Cars in service', 'int', SVC('{col:date}'), 9), CA('free', 'Cars free', 'int', 'MAX(0,{col:fleet}-{col:rented}-{col:service})', 8),
    CA('utilisation', 'Fleet utilisation', 'pct', 'IF({col:fleet}-{col:service}>0,MIN(1,{col:rented}/({col:fleet}-{col:service})),0)', 10),
    CA('pickups', 'Pickups', 'int', 'COUNTIFS(%s,{col:date}%s)' % (B('start_date'), HOLDC), 8), CA('returns', 'Returns', 'int', 'COUNTIFS(%s,{col:date}%s)' % (B('end_date'), HOLDC), 8),
    PHONE_IF('{col:date}>={today}', LIT(D.OWNER_PHONE), 'owner_phone', 'Owner phone'), PHONE_IF('{col:date}={today}+1', LIT(D.MANAGER_PHONE), 'mgr_phone', 'Manager phone'), CENTER()],
    D.daily_d(), 70, [A('utilisation', '< {set:util_red}', 'bad'), A('utilisation', '>= {set:util_green}', 'good'), A('free', '= 0', 'bad')]))
# 19 cancellations and no-shows -----------------------------------------------
tables.append(T('cancellations', 'Cancellations and no-shows', 'Cancellations and no-shows with the revenue lost',
    'One row per cancelled or missed booking: the date, the channel and the fee you kept; the notice days, the notice check and the revenue lost fill in.', [
    C('booking_id', 'Booking ID', 'text', 10, required=True), C('cancelled_on', 'Cancelled on', 'date', 11), LST('channel', 'Channel', 'channel', 16), LST('kind', 'Kind', 'cxkind', 11), C('fee_charged', 'Fee charged', 'money', 10),
    CA('vehicle', 'Vehicle', 'text', LKB('vehicle'), 22), CA('class', 'Class', 'text', LKB('class'), 12), CA('renter', 'Renter', 'text', LKB('renter'), 16), CA('phone', 'Renter phone', 'text', LKB('phone'), 18),
    CA('start_date', 'Start date', 'date', LKBD('start_date'), 11), CA('total', 'Booking total', 'money', LKBN('total'), 11),
    CA('notice_days', 'Notice days', 'int', 'MAX(0,{col:start_date}-{col:cancelled_on})', 8),
    CA('notice_check', 'Notice check', 'text', 'IF({col:kind}=%s,%s,IF({col:notice_days}>={set:free_cancel_days},%s,%s))' % (tok('cxkind', 'No-show'), v('No-show fee'), v('Free notice'), v('Late cancellation')), 16),
    CA('revenue_lost', 'Revenue lost', 'money', 'MAX(0,{col:total}-{col:fee_charged})', 11),
    PHONE_IF('{col:kind}=%s' % tok('cxkind', 'Cancelled'), '{col:phone}', 'cancel_phone', 'Cancellation phone'), PHONE_IF('{col:kind}=%s' % tok('cxkind', 'No-show'), '{col:phone}', 'noshow_phone', 'No-show phone'),
    PHONE_IF('AND({col:kind}=%s,OR({col:channel}=%s,{col:channel}=%s))' % (tok('cxkind', 'Cancelled'), CH['Marketplace A'], CH['Marketplace B']), LIT(D.MKT_PHONE), 'mkt_phone', 'Marketplace support phone'), CENTER()],
    D.cancel_d(), 250, [A('notice_check', '= ' + v('Late cancellation'), 'warn'), A('kind', '= ' + tok('cxkind', 'No-show'), 'bad')]))
# 20 lead time bands ----------------------------------------------------------
def LBC(lo, hi):
    c = '%s,">=%d"' % (B('lead_days'), lo) + (',%s,"<=%d"' % (B('lead_days'), hi) if hi else '')
    return 'COUNTIFS(%s,%s,">="&({today}-90)%s)' % (c, B('created_on'), HOLDC)
_BR = [('Same or next day', -999, 1), ('2 to 7 days', 2, 7), ('8 to 14 days', 8, 14), ('15 to 30 days', 15, 30)]
_BF = LBC(31, None)
for _n, _lo, _hi in reversed(_BR):
    _BF = 'IF({col:band}=%s,%s,%s)' % (tok('band', _n), LBC(_lo, _hi), _BF)
tables.append(T('lead_bands', 'Lead time bands', 'Lead time of the bookings made in the last 90 days',
    'One row per lead time band: how many bookings were made that far ahead and their share.', [
    LST('band', 'Lead time band', 'band', 18, required=True),
    CA('bookings', 'Bookings made, last 90 days', 'int', _BF, 12),
    CA('share', 'Share', 'pct', 'IFERROR({col:bookings}/SUM({range:lead_bands.bookings}),0)', 9)], D.bands_d(), 50))
assert len(tables) == 20
