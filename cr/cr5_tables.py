"""Car rental suite part 5: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr5_lists import *
import cr5_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)
def VT(c, my='vehicle'): return LKT('vehicles.' + c, 'vehicles.vehicle', my)
def VN(c, my='vehicle'): return LKN('vehicles.' + c, 'vehicles.vehicle', my)
def VD(c, my='vehicle'): return LKD('vehicles.' + c, 'vehicles.vehicle', my)
def PHONE(k, label, role): return CA(k, label, 'text', '"%s"' % D.PH[role], 18)
def MECH(): return PHONE('mechanic_phone', 'Mechanic phone', 'Mechanic')
def MGR(): return PHONE('manager_phone', 'Manager phone', 'Manager')
def OWN(): return PHONE('owner_phone', 'Owner phone', 'Owner-operator')
def BROKER(): return PHONE('broker_phone', 'Insurance broker phone', 'Insurance broker')
def LENDER(): return PHONE('lender_phone', 'Lender phone', 'Lender')
def COMPANYC(): return CA('business', 'Business', 'text', '{set:company}', 22)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YES = '{list:yesno.yes}'
SOLD = tok('vstatus', 'Sold'); ACT = tok('vstatus', 'Active'); WSH = tok('vstatus', 'In workshop')
UP = tok('rstatus2', 'Upcoming'); DONE = tok('rstatus2', 'Done')
def G(x): return tok('mgroup', x)
REGK = tok('renewal', 'Registration renewal'); INSK = tok('renewal', 'Insurance renewal'); INSPK = tok('renewal', 'Inspection due')
TYRE = tok('mkind', 'Tyre set')
def ADR(c):
    f = '0'
    for cl in reversed(CLASSES):
        f = 'IF(%s=%s,{set:adr_%s},%s)' % (c, tok('class', cl), key('class', cl), f)
    return f
def L12(): return '{today}-365'


CLS_ = {c['class']: c for c in classes}
settings = [S('company', 'Your business name', 'text', COMPANY), S('service_warn_miles', 'Miles before a service that count as due soon', 'int', 500),
            S('service_warn_days', 'Days before a service date that count as due soon', 'int', 30), S('renewal_warn_days', 'Days ahead the renewals review looks', 'int', 45),
            S('renew_soon_days', 'Renewals in red or amber: due within this many days', 'int', 30), S('renew_later_days', 'Renewals in yellow: due within this many days', 'int', 60),
            S('maint_budget_vm', 'Maintenance budget per vehicle a month, set your own', 'money', 200), S('workshop_days_limit', 'Most workshop days per vehicle in 12 months, set your own', 'int', 12),
            S('slots_per_week', 'Workshop slots you can use each week', 'int', 5), S('tyre_warn_miles', 'Miles before a tyre change that count as due', 'int', 3000),
            S('set_aside_month', 'Amount you set aside each month for renewals', 'money', 3500), S('trend_rise_pct', 'Rise in cost that counts as a rising trend', 'pct', 0.15),
            S('season_change', 'Date of the next tyre season change', 'date', ahead(40))] + [
           S('adr_' + key('class', c), 'Average daily rate (ADR), %s' % c, 'money', CLS_[c]['daily_rate']) for c in CLASSES]
assert 3 <= len(settings) <= 20

tables = []
# 1 vehicles ----------------------------------------------------------------
GAPS = ('IF({col:status}=%s,0,({col:plate}="")+({col:odometer}<=0)+({col:interval_miles}<=0)+({col:interval_months}<=0)+({col:last_service_date}=0)+({col:insurance_year}<=0)'
        '+3-(COUNTIFS({range:renewals.vehicle},{col:vehicle},{range:renewals.kind},%s,{range:renewals.status},%s)>0)-(COUNTIFS({range:renewals.vehicle},{col:vehicle},{range:renewals.kind},%s,{range:renewals.status},%s)>0)'
        '-(COUNTIFS({range:renewals.vehicle},{col:vehicle},{range:renewals.kind},%s,{range:renewals.status},%s)>0))') % (SOLD, REGK, UP, INSK, UP, INSPK, UP)
tables.append(T('vehicles', 'Vehicle Register', 'Vehicle register: one row per vehicle',
    'One row per vehicle: class, purchase or financing, odometer, last service and insurance; miles since service, miles to the next service, the next service date and the register gaps fill in.', [
    C('vehicle_id', 'Vehicle ID', 'text', 10, required=True), C('vehicle', 'Vehicle', 'text', 24), C('plate', 'Plate', 'text', 11), LST('class', 'Class', 'class', 12), LST('fuel', 'Fuel', 'fuel', 10),
    LST('year', 'Model year', 'vyear', 10), C('purchase_date', 'Purchase date', 'date', 12), C('purchase_price', 'Purchase price', 'money', 12), C('financed', 'Financed', 'bool', 9), C('monthly_payment', 'Loan payment a month', 'num', 12),
    C('odometer', 'Odometer, miles', 'int', 11), LST('status', 'Status', 'vstatus', 12), C('sold_date', 'Sold on', 'date', 11), C('interval_miles', 'Service interval, miles', 'int', 11),
    C('interval_months', 'Service interval, months', 'int', 11), C('last_service_date', 'Last service date', 'date', 12), C('last_service_odometer', 'Odometer at last service', 'int', 12),
    C('insurance_year', 'Insurance a year', 'money', 12), C('resale_estimate', 'Resale estimate', 'money', 12), C('miles_12m', 'Miles, last 12 months', 'int', 11), C('util_12m', 'Utilisation, last 12 months', 'pct', 11),
    CA('age_months', 'Age, months', 'int', 'INT((IF({col:sold_date}>0,{col:sold_date},{today})-{col:purchase_date})/30.4375)', 9),
    CA('miles_since', 'Miles since service', 'int', '{col:odometer}-{col:last_service_odometer}', 11), CA('miles_to', 'Miles to next service', 'int', '{col:interval_miles}-{col:miles_since}', 11),
    CA('next_date', 'Next service date, by months', 'date', 'EDATE(IF({col:last_service_date}>0,{col:last_service_date},{col:purchase_date}),{col:interval_months})', 12),
    CA('days_to', 'Days to the service date', 'int', '{col:next_date}-{today}', 10),
    CA('service_flag', 'Service check', 'text', 'IF({col:status}=%s,%s,IF(OR({col:miles_to}<=0,{col:days_to}<=0),%s,IF(OR({col:miles_to}<={set:service_warn_miles},{col:days_to}<={set:service_warn_days}),%s,%s)))' % (SOLD, ca('Sold'), ca('Service now'), ca('Book soon'), ca('Current')), 12),
    CA('gaps', 'Register gaps', 'int', GAPS, 9), CA('swap_class', 'Class free to swap', 'text', 'IF(AND({col:status}=%s,{col:service_flag}=%s),{col:class},"")' % (ACT, ca('Current')), 12),
    CA('last_tyre', 'Last tyre set', 'date', LKD('tyres.tyre_date', 'tyres.vehicle', 'vehicle'), 11), BROKER(), LENDER(), COMPANYC()],
    D.vehicles_d(), 80, [A('service_flag', '= ' + ca('Service now'), 'bad'), A('service_flag', '= ' + ca('Book soon'), 'warn'), A('status', '= ' + WSH, 'warn'), A('gaps', '> 0', 'warn')]))
# 2 service log -------------------------------------------------------------
tables.append(T('service_log', 'Service Log', 'Service and repair log of every workshop visit',
    'One row per workshop visit: date, kind, odometer, cost, days off road and vendor; the booked days lost fill in from the vehicle utilisation.', [
    C('maint_id', 'Maint ID', 'text', 10, required=True), C('vehicle_id', 'Vehicle ID', 'text', 10), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24), LST('class', 'Class', 'class', 12), C('date', 'Date', 'date', 11),
    C('month', 'Month', 'date', 11), LST('kind', 'Kind', 'mkind', 14), LST('group', 'Cost group', 'mgroup', 11), C('odometer', 'Odometer, miles', 'int', 11), C('cost', 'Cost', 'money', 11),
    C('days_off_road', 'Days off road', 'int', 9), LST('vendor', 'Vendor', 'vendor', 14), C('on_time', 'Service on time', 'bool', 9),
    CA('lost_days', 'Booked days lost', 'num', 'ROUND({col:days_off_road}*%s,1)' % VN('util_12m'), 10), CA('since_days', 'Days ago', 'int', '{today}-{col:date}', 9)],
    D.service_log_d(), 1000, [A('on_time', '= ' + '{list:yesno.no}', 'warn'), A('days_off_road', '> 3', 'warn')]))
# 3 service types -----------------------------------------------------------
tables.append(T('service_types', 'Service Types', 'Service types with their interval in miles and months',
    'One row per kind of work: the interval in miles and months that the service planner and the tyre planner read; zero means no fixed interval.', [
    LST('service_type', 'Service type', 'mkind', 16, required=True), C('interval_miles', 'Interval, miles', 'int', 12), C('interval_months', 'Interval, months', 'int', 12)], D.service_types_d(), 50))
# 4 service due -------------------------------------------------------------
def NS(): return 'IFERROR(INDEX({range:bookings14.start_date},MATCH({col:vehicle},{range:bookings14.first_key},0)),"")'
def DUEX(f): return 'MAX({today},INT(MIN(%s,{today}+' % VN('next_date') + 'MAX(0,{col:miles_to})/({col:mpd}*%s))))' % f
def WKX(c): return 'IF({col:%s}<{today}+84,MAX(1,INT(({col:%s}-{today})/7)+1),0)' % (c, c)
tables.append(T('service_due', 'Service Due List', 'Service due by miles or months, whichever comes first',
    'One row per vehicle in the fleet: miles and days to the next service, the date it falls due, the next booking and a flag; Pull from booking marks a car past its interval that is booked this week.', [
    REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24, required=True), CA('vehicle_id', 'Vehicle ID', 'text', VT('vehicle_id'), 10), CA('class', 'Class', 'text', VT('class'), 12),
    CA('miles_to', 'Miles to service', 'int', VN('miles_to'), 10), CA('days_to', 'Days to service', 'int', VN('days_to'), 10), CA('mpd', 'Miles a day', 'int', 'MAX(20,ROUND(%s/365,0))' % VN('miles_12m'), 9),
    CA('due_date', 'Service due by', 'date', DUEX('1'), 11), CA('miles_over', 'Miles over the interval', 'int', 'MAX(0,-{col:miles_to})', 10), CA('due_by', 'Service check', 'text', VT('service_flag'), 12),
    CA('next_start', 'Next booking starts', 'date', NS(), 11), CA('next_booking', 'Next booking', 'text', 'IFERROR(INDEX({range:bookings14.booking_id},MATCH({col:vehicle},{range:bookings14.first_key},0)),"")', 11),
    CA('booked_week', 'Booked within 7 days', 'int', 'IF(ISNUMBER({col:next_start}),IF({col:next_start}<={today}+7,1,0),0)', 9),
    CA('flag', 'Flag', 'text', 'IF({col:due_by}=%s,IF({col:booked_week}=1,%s,%s),{col:due_by})' % (ca('Service now'), ca('Pull from booking'), ca('Book a slot')), 14),
    CA('rank_score', 'Act-first score', 'num', 'IF(AND({col:due_by}=%s,{col:booked_week}=1),{col:miles_over}+VALUE(RIGHT({col:vehicle_id},3))/1000,0)' % ca('Service now'), 10),
    CA('due_best', 'Due date, best case', 'date', DUEX('0.85'), 11), CA('due_worst', 'Due date, worst case', 'date', DUEX('1.2'), 11),
    CA('wk_base', 'Week due, base', 'int', WKX('due_date'), 8), CA('wk_best', 'Week due, best', 'int', WKX('due_best'), 8), CA('wk_worst', 'Week due, worst', 'int', WKX('due_worst'), 8),
    CA('peers_base', 'Cars due that week, base', 'int', 'IF({col:wk_base}>0,COUNTIFS({range:service_due.wk_base},{col:wk_base}),0)', 9),
    CA('peers_best', 'Cars due that week, best', 'int', 'IF({col:wk_best}>0,COUNTIFS({range:service_due.wk_best},{col:wk_best}),0)', 9),
    CA('peers_worst', 'Cars due that week, worst', 'int', 'IF({col:wk_worst}>0,COUNTIFS({range:service_due.wk_worst},{col:wk_worst}),0)', 9),
    CA('overdue_n', 'Services overdue', 'int', 'COUNTIFS({range:service_due.due_by},%s)' % ca('Service now'), 9), CA('booked_n', 'Overdue and booked this week', 'int', 'COUNTIFS({range:service_due.flag},%s)' % ca('Pull from booking'), 9),
    OWN(), MGR(), MECH(), PHONE('driver_phone', 'Driver phone', 'Delivery driver'), PHONE('detailer_phone', 'Detailer phone', 'Detailer'), COMPANYC()],
    D.service_due_d(), 60, [A('flag', '= ' + ca('Pull from booking'), 'bad'), A('flag', '= ' + ca('Book a slot'), 'warn'), A('flag', '= ' + ca('Book soon'), 'warn'), A('flag', '= ' + ca('Current'), 'good')]))
# 5 renewals ----------------------------------------------------------------
tables.append(T('renewals', 'Renewals', 'Registration, insurance and inspection renewals',
    'One row per renewal: vehicle, kind, due date, renewed on, cost and status; days to due, the colour band and the paid-on-time check fill in by themselves.', [
    C('renewal_id', 'Renewal ID', 'text', 10, required=True), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24), LST('kind', 'Kind', 'renewal', 20), C('due_date', 'Due date', 'date', 11),
    C('renewed_on', 'Renewed on', 'date', 11), C('cost', 'Cost', 'money', 11), LST('status', 'Status', 'rstatus2', 10),
    CA('class', 'Class', 'text', VT('class'), 12), CA('days_to_due', 'Days to due', 'int', '{col:due_date}-{today}', 9),
    CA('band', 'Colour band', 'text', 'IF({col:status}=%s,%s,IF({col:due_date}<{today},%s,IF({col:due_date}<={today}+{set:renew_soon_days},%s,IF({col:due_date}<={today}+{set:renew_later_days},%s,%s))))' % (DONE, ca('Done'), ca('Overdue'), ca('Due in 30 days'), ca('Due in 60 days'), ca('Later')), 14),
    CA('paid_check', 'Paid check', 'text', 'IF({col:status}=%s,IF({col:renewed_on}<={col:due_date},%s,%s),%s)' % (DONE, ca('Paid on time'), ca('Paid late'), ca('Open renewal')), 13),
    CA('sort_key', 'Sort key, open renewals', 'num', 'IF({col:status}=%s,{col:due_date}+VALUE(RIGHT({col:renewal_id},3))/1000,"")' % UP, 11), BROKER(), MGR(), COMPANYC()],
    D.renewals_d(), 500, [A('band', '= ' + ca('Overdue'), 'bad'), A('band', '= ' + ca('Due in 30 days'), 'warn'), A('band', '= ' + ca('Due in 60 days'), 'warn'), A('paid_check', '= ' + ca('Paid late'), 'warn')]))
# 6 renewal cost by month ahead ---------------------------------------------
def RC(kind): return 'SUMIFS({range:renewals.cost},{range:renewals.kind},%s,{range:renewals.status},%s,{range:renewals.due_date},">="&{col:month},{range:renewals.due_date},"<"&EDATE({col:month},1))' % (kind, UP)
tables.append(T('renew_cost', 'Renewal Cost by Month', 'Cost of renewals due in each of the next 12 months',
    'One row per month ahead: the registration, insurance and inspection cost of open renewals due that month, the running total and what you must set aside each month.', [
    C('month', 'Month', 'date', 11, required=True), LST('slot', 'Month ahead', 'mahead', 10),
    CA('registration', 'Registration', 'money', RC(REGK), 11), CA('insurance', 'Insurance', 'money', RC(INSK), 11), CA('inspection', 'Inspection', 'money', RC(INSPK), 11),
    CA('total', 'Total', 'money', '{col:registration}+{col:insurance}+{col:inspection}', 11),
    CA('due_n', 'Renewals due', 'int', 'COUNTIFS({range:renewals.status},%s,{range:renewals.due_date},">="&{col:month},{range:renewals.due_date},"<"&EDATE({col:month},1))' % UP, 9),
    CA('months_n', 'Months from now', 'int', 'COUNTIFS({range:renew_cost.month},"<="&{col:month})', 9),
    CA('cumulative', 'Running total', 'money', 'SUMIFS({range:renew_cost.total},{range:renew_cost.month},"<="&{col:month})', 12), CA('avg_to_date', 'Set aside needed a month', 'money', '{col:cumulative}/{col:months_n}', 12),
    CA('amount30', 'Renewals cost, next 30 days', 'money', 'SUMIFS({range:renewals.cost},{range:renewals.status},%s,{range:renewals.due_date},">="&{today},{range:renewals.due_date},"<="&({today}+{set:renew_soon_days}))' % UP, 12),
    CA('gap', 'Set-aside gap', 'money', '{col:cumulative}-{set:set_aside_month}*{col:months_n}', 11), PHONE('bookkeeper_phone', 'Bookkeeper phone', 'Bookkeeper'), OWN(), COMPANYC()],
    D.renew_cost_ahead_d(), 50, [A('gap', '> 0', 'warn')]))
# 7 workshop slots ----------------------------------------------------------
BL = '+'.join('IF({col:days}>%d,COUNTIFS({range:bookings14.vehicle},{col:vehicle},{range:bookings14.start_date},"<="&({col:date}+%d),{range:bookings14.end_date},">="&({col:date}+%d)),0)' % (k, k, k) for k in range(3))
NXT = '100000-SUMPRODUCT(MAX(({range:bookings14.vehicle}={col:vehicle})*({range:bookings14.start_date}>={col:date}+{col:days})*(100000-{range:bookings14.start_date})))'
tables.append(T('slots', 'Workshop Slots', 'Candidate workshop slots and the booked days each one loses',
    'One row per candidate slot (a vehicle, a date and the days it needs): the booked days lost, the free days after and the verdict fill in; the slot with the fewest lost days is marked Best slot.', [
    C('slot_id', 'Slot ID', 'text', 9, required=True), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24), C('date', 'Candidate date', 'date', 12), LST('kind', 'Work', 'mkind', 14), C('days', 'Days needed', 'int', 9),
    C('drop_time', 'Drop-off time', 'text', 9), C('planned', 'Planned with workshop', 'bool', 10),
    CA('class', 'Class', 'text', VT('class'), 12), CA('adr', 'Average daily rate', 'money', ADR(VT('class')), 10), CA('return_date', 'Back on', 'date', '{col:date}+{col:days}', 11),
    CA('lost', 'Booked days lost', 'int', BL, 9), CA('revenue_lost', 'Revenue lost', 'money', '{col:lost}*{col:adr}', 11),
    CA('free_after', 'Free days after', 'int', 'IF((%s)>=100000,14,MIN(14,(%s)-({col:date}+{col:days})))' % (NXT, NXT), 9),
    CA('verdict', 'Verdict', 'text', 'IF(COUNTIFS({range:slots.vehicle},{col:vehicle},{range:slots.lost},"<"&{col:lost})+COUNTIFS({range:slots.vehicle},{col:vehicle},{range:slots.lost},{col:lost},{range:slots.date},"<"&{col:date})=0,%s,IF({col:lost}=0,%s,IF({col:lost}<=1,%s,%s)))' % (ca('Best slot'), ca('Free slot'), ca('Acceptable'), ca('Loses bookings')), 14),
    MECH(), PHONE('driver_phone', 'Driver phone', 'Delivery driver'), MGR(), PHONE('detailer_phone', 'Detailer phone', 'Detailer'), COMPANYC()],
    D.slots_d(), 100, [A('verdict', '= ' + ca('Best slot'), 'good'), A('verdict', '= ' + ca('Loses bookings'), 'bad'), A('verdict', '= ' + ca('Acceptable'), 'warn')]))
# 8 repair log --------------------------------------------------------------
tables.append(T('repair_log', 'Repair Log', 'Repairs, body work, towing and brake jobs',
    'One row per repair job: date, kind, cost, days off road and place; the class and the cost per 1,000 miles of the vehicle fill in.', [
    C('maint_id', 'Maint ID', 'text', 10, required=True), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24), C('date', 'Date', 'date', 11), LST('kind', 'Kind', 'mkind', 14), C('cost', 'Cost', 'money', 11),
    C('days_off_road', 'Days off road', 'int', 9), C('claim_id', 'Claim ID', 'text', 10), LST('location', 'Location', 'location', 14),
    CA('class', 'Class', 'text', VT('class'), 12), CA('cost_1000', 'Cost per 1,000 miles', 'money', 'IFERROR({col:cost}/%s*1000,0)' % VN('miles_12m'), 11),
    MECH(), PHONE('body_phone', 'Body repair shop phone', 'Body repair shop'), PHONE('towing_phone', 'Towing service phone', 'Towing service'), COMPANYC()],
    D.repair_log_d(), 300, [A('days_off_road', '> 3', 'warn')]))
# 9 repair cost by vehicle and month ----------------------------------------
def RM(groups): return '+'.join('SUMIFS({range:service_log.cost},{range:service_log.vehicle},{col:vehicle},{range:service_log.month},{col:month},{range:service_log.group},%s)' % G(g) for g in groups)
tables.append(T('repair_month', 'Repair Cost by Vehicle', 'Repair, tyre and service cost by vehicle and month',
    'One row per vehicle and month: the repair, tyre and service cost add up from the Service Log by themselves.', [
    REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24, required=True), C('month', 'Month', 'date', 11),
    CA('repair_cost', 'Repair cost', 'money', RM(['Repair', 'Towing']), 11), CA('tyre_cost', 'Tyre cost', 'money', RM(['Tyres']), 11), CA('service_cost', 'Service cost', 'money', RM(['Service', 'Inspection']), 11),
    CA('total', 'Total', 'money', '{col:repair_cost}+{col:tyre_cost}+{col:service_cost}', 11), CA('class', 'Class', 'text', VT('class'), 12)], D.repair_month_d(), 400))
# 10 tyre dates -------------------------------------------------------------
tables.append(T('tyres', 'Tyre Dates', 'Last tyre set and miles to the next one',
    'One row per vehicle: the date and odometer of the last tyre set; miles since, miles to the next set and the date they run out fill in.', [
    REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24, required=True), C('tyre_date', 'Last tyre set', 'date', 11), C('odo_then', 'Odometer then, miles', 'int', 11),
    CA('class', 'Class', 'text', VT('class'), 12), CA('odometer', 'Odometer now', 'int', VN('odometer'), 10), CA('miles_since', 'Miles since', 'int', '{col:odometer}-{col:odo_then}', 10),
    CA('next_tyre_miles', 'Miles to next set', 'int', 'SUMIFS({range:service_types.interval_miles},{range:service_types.service_type},%s)-{col:miles_since}' % TYRE, 11),
    CA('mpd', 'Miles a day', 'int', 'MAX(20,ROUND(%s/365,0))' % VN('miles_12m'), 8), CA('due_on', 'Tyres due on', 'date', 'INT({today}+MAX(0,{col:next_tyre_miles})/{col:mpd})', 11),
    CA('tyre_flag', 'Tyre check', 'text', 'IF({col:next_tyre_miles}<={set:tyre_warn_miles},%s,%s)' % (ca('Tyres due'), ca('Tyres fine')), 11),
    CA('sets_due', 'Sets due before the season change', 'int', 'COUNTIFS({range:tyres.due_on},"<="&{set:season_change})', 10),
    CA('season_date', 'Season change', 'date', '{set:season_change}', 11), PHONE('tyre_phone', 'Tyre supplier phone', 'Tyre supplier'), COMPANYC()],
    D.tyres_d(), 80, [A('tyre_flag', '= ' + ca('Tyres due'), 'warn'), A('next_tyre_miles', '< 0', 'bad')]))
# 11 rental days lost -------------------------------------------------------
def DL(groups): return '+'.join('SUMIFS({range:service_log.days_off_road},{range:service_log.vehicle},{col:vehicle},{range:service_log.date},">="&({today}-365),{range:service_log.group},%s)' % G(g) for g in groups)
tables.append(T('days_lost', 'Rental Days by Vehicle', 'Rental days lost to service and repair, per vehicle',
    'One row per vehicle: workshop days of 12 months, booked days lost at its utilisation and the revenue lost at the class average daily rate (ADR: revenue per rented day).', [
    REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24, required=True), CA('class', 'Class', 'text', VT('class'), 12), CA('util', 'Utilisation, 12 months', 'pct', VN('util_12m'), 10),
    CA('service_days', 'Service days', 'int', DL(['Service', 'Inspection', 'Tyres']), 9), CA('repair_days', 'Repair days', 'int', DL(['Repair', 'Towing']), 9),
    CA('days', 'Workshop days', 'int', '{col:service_days}+{col:repair_days}', 9), CA('booked_lost', 'Booked days lost', 'num', 'ROUND({col:days}*{col:util},1)', 9),
    CA('adr', 'Average daily rate', 'money', ADR('{col:class}'), 10), CA('lost_revenue', 'Revenue lost', 'money', 'ROUND({col:booked_lost}*{col:adr},0)', 11),
    CA('share_year', 'Share of the year', 'pct', '{col:days}/365', 9), CA('limit_days', 'Days allowed', 'int', 'IF(%s=%s,0,{set:workshop_days_limit})' % (VT('status'), SOLD), 9),
    CA('limit_check', 'Limit check', 'text', 'IF({col:days}>{set:workshop_days_limit},%s,%s)' % (ca('Over the limit'), ca('Within the limit')), 12), OWN(), COMPANYC()],
    D.days_lost_d(), 80, [A('limit_check', '= ' + ca('Over the limit'), 'warn')]))
# 12 cost per 1,000 miles ---------------------------------------------------
def CW(a, b=None):
    return 'SUMIFS({range:service_log.cost},{range:service_log.vehicle},{col:vehicle},{range:service_log.date},">="&({today}-%d)%s)' % (a, ',{range:service_log.date},"<"&({today}-%d)' % b if b else '')
tables.append(T('cost1000', 'Cost per 1,000 Miles', 'Maintenance cost per 1,000 miles, per vehicle',
    'One row per vehicle: maintenance cost and miles of the last 12 months; the cost per 1,000 miles, the class average, the trend and the rank fill in.', [
    REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24, required=True), CA('class', 'Class', 'text', VT('class'), 12), CA('miles_12m', 'Miles, 12 months', 'int', VN('miles_12m'), 10),
    CA('maint_cost', 'Maintenance cost, 12 months', 'money', CW(365), 12), CA('cost_6m', 'Cost, last 6 months', 'money', CW(180), 11), CA('prev_6m', 'Cost, 6 months before', 'money', CW(360, 180), 11),
    CA('cost_1000', 'Cost per 1,000 miles', 'money', 'IF({col:miles_12m}>0,{col:maint_cost}/{col:miles_12m}*1000,0)', 11),
    CA('class_avg', 'Class average per 1,000 miles', 'money', 'IFERROR(SUMIFS({range:cost1000.maint_cost},{range:cost1000.class},{col:class})/SUMIFS({range:cost1000.miles_12m},{range:cost1000.class},{col:class})*1000,0)', 12),
    CA('vs_class', 'Above the class', 'money', '{col:cost_1000}-{col:class_avg}', 10),
    CA('class_flag', 'Class check', 'text', 'IF({col:cost_1000}>{col:class_avg},%s,%s)' % (ca('Above class average'), ca('At or below class')), 14),
    CA('trend', 'Trend', 'text', 'IF(AND({col:prev_6m}>0,{col:cost_6m}>{col:prev_6m}*(1+{set:trend_rise_pct})),%s,IF(AND({col:prev_6m}>0,{col:cost_6m}<{col:prev_6m}*(1-{set:trend_rise_pct})),%s,%s))' % (ca('Rising'), ca('Falling'), ca('Steady')), 9),
    CA('rank', 'Rank, 1 is dearest', 'int', 'COUNTIFS({range:cost1000.cost_1000},">"&{col:cost_1000})+1', 8),
    CA('budget', 'Budget, 12 months', 'money', 'IF(%s=%s,0,{set:maint_budget_vm}*12)' % (VT('status'), SOLD), 11),
    CA('repairs_tyres', 'Repairs and tyres, 12 months', 'money', '+'.join('SUMIFS({range:service_log.cost},{range:service_log.vehicle},{col:vehicle},{range:service_log.date},">="&({today}-365),{range:service_log.group},%s)' % G(g) for g in ('Repair', 'Towing', 'Tyres')), 12),
    CA('year', 'Year', 'int', 'YEAR({today})', 7), PHONE('accountant_phone', 'Accountant phone', 'Accountant'), OWN(), COMPANYC()],
    D.cost1000_d(), 80, [A('trend', '= ' + ca('Rising'), 'warn'), A('class_flag', '= ' + ca('Above class average'), 'warn')]))
# 13 vehicles by class ------------------------------------------------------
tables.append(T('class_mix', 'Vehicles by Class', 'Vehicles and average age by class',
    'One row per class: the vehicles in the fleet and their average age in months fill in from the Vehicle Register.', [
    LST('class', 'Class', 'class', 14, required=True),
    CA('vehicles', 'Vehicles', 'int', 'COUNTIFS({range:vehicles.class},{col:class},{range:vehicles.status},"<>"&%s)' % SOLD, 9),
    CA('avg_age', 'Average age, months', 'int', 'IFERROR(ROUND(AVERAGEIFS({range:vehicles.age_months},{range:vehicles.class},{col:class},{range:vehicles.status},"<>"&%s),0),0)' % SOLD, 11)], D.class_mix_d(), 50))
# 14 fleet age mix ----------------------------------------------------------
LO = 'CHOOSE(MATCH({col:band},{range:age_mix.band},0),0,13,25,37,49)'; HI = 'CHOOSE(MATCH({col:band},{range:age_mix.band},0),12,24,36,48,999)'
AM = '{range:vehicles.age_months},">="&%s,{range:vehicles.age_months},"<="&%s,{range:vehicles.vehicle_id},"<>",{range:vehicles.status},"<>"&%s' % (LO, HI, SOLD)
tables.append(T('age_mix', 'Fleet Age Mix', 'Vehicles and average odometer by age band',
    'One row per age band: the vehicles in the fleet and their average miles fill in from the Vehicle Register.', [
    LST('band', 'Age band', 'fleetage', 16, required=True), CA('vehicles', 'Vehicles', 'int', 'COUNTIFS(%s)' % AM, 9), CA('avg_miles', 'Average miles', 'int', 'IFERROR(ROUND(AVERAGEIFS({range:vehicles.odometer},%s),0),0)' % AM, 11)], D.age_mix_d(), 50))
# 15 inspection log ---------------------------------------------------------
tables.append(T('inspections', 'Inspection Log', 'Inspections done, with cost and days off road',
    'One row per inspection: vehicle, date, cost and days off road; the class and the date the next one falls due fill in.', [
    C('maint_id', 'Maint ID', 'text', 10, required=True), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24), C('date', 'Date', 'date', 11), C('cost', 'Cost', 'money', 11), C('days_off_road', 'Days off road', 'int', 9),
    CA('class', 'Class', 'text', VT('class'), 12), CA('next_due', 'Next inspection due', 'date', 'EDATE({col:date},12)', 12)], D.inspections_d(), 120))
# 16 bookings next 14 days --------------------------------------------------
tables.append(T('bookings14', 'Bookings Next 14 Days', 'Bookings in the next 14 days, by vehicle',
    'One row per booked or active rental in the next 14 days: vehicle, dates and renter; the first booking of each vehicle and the swap car for a vehicle that needs service fill in.', [
    C('booking_id', 'Booking ID', 'text', 10, required=True), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24), LST('class', 'Class', 'class', 12), C('start_date', 'Start date', 'date', 11), C('end_date', 'End date', 'date', 11),
    LST('status', 'Status', 'bstat2', 10), C('renter', 'Renter', 'text', 14), C('phone', 'Renter phone', 'text', 18),
    CA('days', 'Days', 'int', '{col:end_date}-{col:start_date}+1', 7), CA('vkey', 'Vehicle and start', 'text', '{col:vehicle}&"|"&{col:start_date}', 14),
    CA('first_key', 'First booking of vehicle', 'text', 'IF(AND({col:start_date}>={today},COUNTIFS({range:bookings14.vehicle},{col:vehicle},{range:bookings14.start_date},">="&{today},{range:bookings14.start_date},"<"&{col:start_date})=0),{col:vehicle},"")', 14),
    CA('needs', 'Service check', 'text', VT('service_flag'), 12), CA('miles_over', 'Miles over the interval', 'int', 'MAX(0,-%s)' % VN('miles_to'), 10),
    CA('swap_to', 'Swap car, same class', 'text', 'IFERROR(INDEX({range:vehicles.vehicle},MATCH({col:class},{range:vehicles.swap_class},0)),"")', 22),
    CA('vehicle_alt', 'Replacement car', 'text', 'IF({col:needs}=%s,{col:swap_to},"")' % ca('Service now'), 22), MGR(), COMPANYC()],
    D.bookings14_d(), 150, [A('needs', '= ' + ca('Service now'), 'bad'), A('status', '= ' + tok('bstat2', 'Active'), 'good')]))
# 17 workshop calendar ------------------------------------------------------
tables.append(T('wk_cal', 'Workshop Calendar', 'Workshop load for the next 30 days',
    'One row per day: the visits planned with the workshop, the vehicles that fall due and the bookings starting; a busy-day flag shows when the slots are full.', [
    C('date', 'Date', 'date', 11, required=True), CA('weekday', 'Weekday, 1 is Monday', 'int', 'WEEKDAY({col:date},2)', 9),
    CA('planned', 'Visits planned', 'int', 'COUNTIFS({range:slots.date},{col:date},{range:slots.planned},%s)' % YES, 9), CA('due_n', 'Vehicles falling due', 'int', 'COUNTIFS({range:service_due.due_date},{col:date})', 9),
    CA('starts', 'Bookings starting', 'int', 'COUNTIFS({range:bookings14.start_date},{col:date})', 9),
    CA('load', 'Load', 'text', 'IF({col:planned}>=ROUNDUP({set:slots_per_week}/5,0),%s,%s)' % (ca('Busy day'), ca('Free day')), 10)], D.wk_cal_d(), 50, [A('load', '= ' + ca('Busy day'), 'warn')]))
# 18 workshop vendors -------------------------------------------------------
tables.append(T('vendors', 'Workshop Vendors', 'Workshop vendors and what you spent with each',
    'One row per vendor: the role and the spend of the last 12 months fill in from the Service Log.', [
    C('vendor', 'Vendor', 'text', 24, required=True), C('role', 'Role', 'text', 30),
    CA('spend_12m', 'Spend, 12 months', 'money', 'SUMIFS({range:service_log.cost},{range:service_log.vendor},{col:vendor},{range:service_log.date},">="&({today}-365))', 12)], D.vendors_d(), 50))
# 19 renewals by vehicle ----------------------------------------------------
def NX(kind): return 'IF(COUNTIFS({range:renewals.vehicle},{col:vehicle},{range:renewals.kind},%s,{range:renewals.status},%s)=0,"",100000-SUMPRODUCT(MAX(({range:renewals.vehicle}={col:vehicle})*({range:renewals.kind}=%s)*({range:renewals.status}=%s)*(100000-{range:renewals.due_date}))))' % (kind, UP, kind, UP)
def CX(kind, d): return 'IF({col:%s}="",0,SUMIFS({range:renewals.cost},{range:renewals.vehicle},{col:vehicle},{range:renewals.kind},%s,{range:renewals.status},%s,{range:renewals.due_date},{col:%s}))' % (d, kind, UP, d)
tables.append(T('renewals_by_veh', 'Renewals by Vehicle', 'Next registration, insurance and inspection date per vehicle',
    'One row per vehicle: the next registration, insurance and inspection date, the soonest one with its colour band and what they cost fill in from the Renewals sheet.', [
    REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24, required=True), CA('class', 'Class', 'text', VT('class'), 12),
    CA('next_reg', 'Next registration', 'date', NX(REGK), 11), CA('next_ins', 'Next insurance', 'date', NX(INSK), 11), CA('next_insp', 'Next inspection', 'date', NX(INSPK), 11),
    CA('soonest', 'Soonest', 'date', 'MIN({col:next_reg},{col:next_ins},{col:next_insp})', 11), CA('days_soonest', 'Days to soonest', 'int', '{col:soonest}-{today}', 9),
    CA('band', 'Colour band', 'text', 'IF({col:soonest}<{today},%s,IF({col:soonest}<={today}+{set:renew_soon_days},%s,IF({col:soonest}<={today}+{set:renew_later_days},%s,%s)))' % (ca('Overdue'), ca('Due in 30 days'), ca('Due in 60 days'), ca('Later')), 14),
    CA('overdue_n', 'Overdue', 'int', 'IF({col:soonest}<{today},1,0)', 8), CA('cost_reg', 'Registration cost', 'money', CX(REGK, 'next_reg'), 11), CA('cost_ins', 'Insurance cost', 'money', CX(INSK, 'next_ins'), 11),
    CA('cost_insp', 'Inspection cost', 'money', CX(INSPK, 'next_insp'), 11),
    CA('last_insp', 'Last inspection', 'date', 'IF(SUMPRODUCT(MAX(({range:inspections.vehicle}={col:vehicle})*{range:inspections.date}))=0,"",SUMPRODUCT(MAX(({range:inspections.vehicle}={col:vehicle})*{range:inspections.date})))', 11),
    CA('cost_12m', 'Renewals cost, next 12 months', 'money', 'SUMIFS({range:renewals.cost},{range:renewals.vehicle},{col:vehicle},{range:renewals.status},%s,{range:renewals.due_date},"<="&({today}+365))' % UP, 12),
    CA('insurance_year', 'Insurance a year', 'money', VN('insurance_year'), 11), MGR(), BROKER(), COMPANYC()],
    D.renewals_by_veh_d(), 80, [A('band', '= ' + ca('Overdue'), 'bad'), A('band', '= ' + ca('Due in 30 days'), 'warn'), A('band', '= ' + ca('Due in 60 days'), 'warn')]))
# 20 fleet changes ----------------------------------------------------------
tables.append(T('fleet_changes', 'Fleet Changes', 'Vehicles bought and sold',
    'One row per purchase or sale: vehicle, event, date and amount; the purchase price, the result against it and the months held fill in.', [
    C('change_id', 'Change ID', 'text', 10, required=True), REF('vehicle', 'Vehicle', 'vehicles.vehicle', 24), LST('event', 'Event', 'fevent', 10), C('date', 'Date', 'date', 11), C('amount', 'Amount', 'money', 12),
    CA('class', 'Class', 'text', VT('class'), 12), CA('purchase_price', 'Purchase price', 'money', VN('purchase_price'), 12), CA('vs_price', 'Amount against purchase price', 'money', '{col:amount}-{col:purchase_price}', 12),
    CA('held_months', 'Months held', 'int', 'INT(({col:date}-%s)/30.4375)' % VN('purchase_date'), 9), BROKER(), LENDER(), COMPANYC()],
    D.fleet_changes_d(), 60, [A('event', '= ' + tok('fevent', 'Sold'), 'warn'), A('event', '= ' + tok('fevent', 'Bought'), 'good')]))
assert len(tables) == 20, len(tables)
