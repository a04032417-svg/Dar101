"""Car rental suite part 1: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr1_lists import *
import cr1_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def PH(key_, label, phone): return CA(key_, label, 'text', '"%s"' % phone, 18)
def COMPANY_COL(): return CA('company', 'Business', 'text', '{set:company}', 26)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
OPEN = tok('estatus', 'Open'); QUOTED = tok('estatus', 'Quoted'); BOOKED = tok('estatus', 'Booked'); LOST = tok('estatus', 'Lost')
D90 = '{range:enquiries.date},">="&({today}-90)'
CL = lambda c: tok('class', c)
def CLS_RATE(cls): return 'SUMIFS({range:classes.daily_rate},{range:classes.class},%s)' % cls
def PLAN_RATE(cls, plan): return 'SUMIFS({range:rates.rate},{range:rates.class},%s,{range:rates.plan},%s)' % (cls, plan)
DAILY = tok('plan', 'Daily'); WEEKLY = tok('plan', 'Weekly'); MONTHLY = tok('plan', 'Monthly')
def FLOOR_DAY(cls): return 'SUMIFS({range:cost_floor.floor_price},{range:cost_floor.class},%s)' % cls
NEXT_EVENT = 'IFERROR(SMALL({range:events.start},COUNTIFS({range:events.start},"<"&{today})+1),"")'

settings = [
    S('company', 'Your business name', 'text', COMPANY), S('reply_hours_target', 'Hours to the first reply you aim for, set your own', 'int', 4),
    S('quote_valid_days', 'Days a quote stays valid', 'int', 7), S('floor_margin', 'Margin added on cost for the floor price, set your own', 'pct', 0.10),
    S('thin_margin', 'Margin over the floor price that counts as thin', 'pct', 0.05), S('corporate_discount', 'Corporate account discount on the daily rate', 'pct', 0.08),
    S('weekend_uplift', 'Weekend uplift on short Friday pickups', 'pct', WEEKEND_UPLIFT), S('planned_rise', 'Planned rate rise', 'pct', 0.04),
    S('rise_date', 'Date the planned rate rise starts', 'date', ahead(30)), S('season_change_date', 'Date of the next season change', 'date', D.SEASON_CHANGE),
    S('addon_target', 'Add-on revenue per booking you aim for, set your own', 'money', 42), S('conv_target', 'Enquiry to booking conversion you aim for', 'pct', 0.60),
    S('util_target', 'Utilisation you plan for, set your own', 'pct', 0.75), S('prep_cost', 'Cost of preparing a car for a pickup (staff time)', 'money', 14),
    S('young_damage_day', 'Extra cost a day of young-driver rentals, set your own', 'money', 4.5), S('chase_decay', 'Value an open quote loses each day it waits', 'pct', 0.08),
    S('cleaning_fee', 'Cleaning fee charged to a renter', 'money', CLEANING_FEE), S('extra_mile_fee', 'Extra mileage fee per mile over the allowance', 'money', EXTRA_MILE_FEE),
    S('late_fee_hour', 'Late return fee per started hour', 'money', LATE_FEE_HOUR), S('late_grace_min', 'Grace minutes before a late return fee', 'int', LATE_GRACE_MIN),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 enquiries ------------------------------------------------------------------
BAND = lambda b: tok('band', b)
def _fast(i): return 'INDEX({range:reply_bands.conversion},MATCH(%s,{range:reply_bands.band},0))' % BAND(i)
def _n(i): return 'INDEX({range:reply_bands.enquiries},MATCH(%s,{range:reply_bands.band},0))' % BAND(i)
B1, B2, B3, B4 = BANDS[:4]
LOSTBK = 'ROUND(%s*MAX(0,%s-%s)+%s*MAX(0,%s-%s)+%s*MAX(0,%s-%s),0)' % (_n(B2), _fast(B1), _fast(B2), _n(B3), _fast(B1), _fast(B3), _n(B4), _fast(B1), _fast(B4))
tables.append(T('enquiries', 'Enquiries', 'Enquiry Log and First Reply Speed',
    'One row per enquiry: source, class wanted, dates, quote, hours to the first reply and the result; reply band, weekend flag and the message figures fill in.', [
    C('enquiry_id', 'Enquiry', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), LST('source', 'Source', 'source', 16), C('contact', 'Contact', 'text', 18),
    C('phone', 'Phone', 'text', 18), LST('class', 'Class wanted', 'class', 12), C('pickup_date', 'Pickup date', 'date', 11), C('days', 'Days', 'int', 7), LST('location', 'Pickup place', 'location', 16),
    LST('season', 'Season', 'season', 10), C('quote_amount', 'Quote amount', 'money', 12), C('first_reply_hours', 'First reply hours', 'num', 10), LST('status', 'Status', 'estatus', 10),
    LST('lost_reason', 'Lost reason', 'lostreason', 12), C('booking_id', 'Booking', 'text', 10), LST('staff', 'Handled by', 'handler', 15), C('next_free', 'Next free day', 'date', 11),
    CA('reply_band', 'Hours to first reply band', 'text', 'IF({col:status}=%s,%s,IF({col:first_reply_hours}<=1,%s,IF({col:first_reply_hours}<=4,%s,IF({col:first_reply_hours}<=24,%s,%s))))' % (OPEN, BAND(BANDS[4]), BAND(B1), BAND(B2), BAND(B3), BAND(B4)), 14),
    CA('slow_reply', 'Slow reply', 'text', 'IF({col:status}=%s,"",IF({col:first_reply_hours}>{set:reply_hours_target},%s,%s))' % (OPEN, YES, NO), 9),
    CA('weekend', 'Weekend pickup', 'text', 'IF(WEEKDAY({col:pickup_date},2)>=6,%s,%s)' % (YES, NO), 9),
    CA('waiting_hours', 'Hours waiting, open', 'int', 'IF({col:status}=%s,MAX(0,({today}-{col:date})*24),"")' % OPEN, 10),
    CA('reply_hours', 'Reply target hours', 'int', '{set:reply_hours_target}', 9), CA('valid_until', 'Quote valid until', 'date', '{col:date}+{set:quote_valid_days}', 11),
    CA('class_alt', 'Other class to offer', 'text', 'IFERROR(INDEX({range:classes.class},CHOOSE(MATCH({col:class},{range:classes.class},0),2,1,4,3,6,5)),"")', 12),
    CA('account_rate', 'Corporate daily rate', 'money', 'ROUND(%s*(1-{set:corporate_discount}),2)' % CLS_RATE('{col:class}'), 11), CA('rate_year', 'Rate review year', 'int', 'YEAR({today})+1', 9),
    CA('lost_bookings', 'Bookings lost to slow replies, 90 days', 'int', LOSTBK, 11),
    CA('weekend_booked', 'Weekend pickups booked, 90 days', 'pct', 'IFERROR(COUNTIFS({range:enquiries.weekend},%s,{range:enquiries.status},%s,%s)/COUNTIFS({range:enquiries.weekend},%s,%s),0)' % (YES, BOOKED, D90, YES, D90), 11),
    COMPANY_COL(), PH('owner_phone', 'Owner phone', D.OWNER_PHONE), PH('manager_phone', 'Manager phone', D.MANAGER_PHONE)],
    D.enquiries_d(), 1500, [A('status', '= ' + OPEN, 'warn'), A('slow_reply', '= ' + YES, 'bad'), A('first_reply_hours', '> {set:reply_hours_target}', 'warn')]))
# 2 rate card ------------------------------------------------------------------
tables.append(T('rates', 'Rate Card', 'Rate Card by Class and Plan',
    'One row per class and plan: this year and last year, deposit and buffer; day equivalent, rise, floor price and the figures for notices fill in.', [
    C('rate_id', 'Rate', 'text', 9, required=True), LST('class', 'Class', 'class', 12), LST('plan', 'Plan', 'plan', 9), C('rate', 'Rate', 'money', 11), C('last_year_rate', 'Last year rate', 'money', 12),
    C('days', 'Days in plan', 'int', 8), C('deposit', 'Deposit', 'money', 10), C('buffer_min', 'Buffer minutes', 'int', 9), C('seats', 'Seats', 'int', 7), C('miles_day', 'Miles a day included', 'int', 10),
    CA('day_equivalent', 'Day equivalent', 'money', 'ROUND({col:rate}/{col:days},2)', 11), CA('rise_pct', 'Rise this year', 'pct', 'IFERROR({col:rate}/{col:last_year_rate}-1,0)', 9),
    CA('floor_price', 'Floor price a day', 'money', FLOOR_DAY('{col:class}'), 11), CA('gap_to_floor', 'Day equivalent over the floor', 'money', '{col:day_equivalent}-{col:floor_price}', 12),
    CA('daily_rate', 'Daily rate', 'money', PLAN_RATE('{col:class}', DAILY), 10), CA('weekly_rate', 'Weekly rate', 'money', PLAN_RATE('{col:class}', WEEKLY), 10),
    CA('monthly_rate', 'Monthly rate', 'money', PLAN_RATE('{col:class}', MONTHLY), 11), CA('account_rate', 'Corporate rate', 'money', 'ROUND({col:rate}*(1-{set:corporate_discount}),2)', 11),
    CA('new_rate', 'Rate after the planned rise', 'money', 'ROUND({col:rate}*(1+{set:planned_rise}),0)', 11), CA('change_date', 'New rates start', 'date', '{set:rise_date}', 11),
    CA('rate_year', 'Rate year', 'int', 'YEAR({today})', 8), COMPANY_COL(), PH('owner_phone', 'Owner phone', D.OWNER_PHONE), PH('manager_phone', 'Manager phone', D.MANAGER_PHONE),
    PH('accountant_phone', 'Accountant phone', D.ACCOUNTANT_PHONE), PH('market_phone', 'Marketplace support phone', D.MARKET_PHONE)],
    D.rates_d(), 100, [A('gap_to_floor', '< 0', 'bad'), A('rise_pct', '< 0.02', 'warn')]))
# 3 vehicle classes ------------------------------------------------------------
tables.append(T('classes', 'Vehicle Classes', 'Vehicle Classes', 'One row per class with the daily rate and the deposit held on a card at pickup (direct bookings).', [
    LST('class', 'Class', 'class', 14, required=True), C('daily_rate', 'Daily rate', 'money', 12), C('deposit', 'Deposit', 'money', 12)], D.classes_d(), 50))
# 4 seasons --------------------------------------------------------------------
tables.append(T('seasons', 'Seasons', 'Seasons', 'The four seasons with the multiplier applied to the daily rate and the months each covers.', [
    C('season', 'Season', 'text', 16, required=True), C('multiplier', 'Multiplier', 'num', 10), C('months', 'Months', 'text', 46)], D.seasons_d(), 50))
# 5 season calendar ------------------------------------------------------------
tables.append(T('events', 'Season Calendar', 'Season Calendar', 'Holiday periods, long weekends and event weekends with their uplift; days away and length fill in.', [
    C('event_id', 'Event', 'text', 9, required=True), C('event', 'Event name', 'text', 26), LST('kind', 'Kind', 'ekind', 14), C('start', 'Start', 'date', 11), C('end', 'End', 'date', 11), C('uplift', 'Uplift', 'pct', 9),
    CA('days_away', 'Days from today', 'int', '{col:start}-{today}', 9), CA('length_days', 'Days long', 'int', '{col:end}-{col:start}+1', 9),
    COMPANY_COL(), PH('bookkeeper_phone', 'Bookkeeper phone', D.BOOKKEEPER_PHONE)], D.events_d(), 60))
# 6 add-ons --------------------------------------------------------------------
tables.append(T('addons', 'Add-ons', 'Add-ons', 'Each add-on with its price a day and what it costs you a day.', [
    LST('addon', 'Add-on', 'addon', 20, required=True), C('price_day', 'Price a day', 'money', 11), C('unit_cost_day', 'Cost a day', 'money', 11)], D.addons_d(), 50))
# 7 add-on lines ---------------------------------------------------------------
MLAST = 'EDATE(%s,-1)' % MS
tables.append(T('addon_lines', 'Add-on Lines', 'Add-on Lines by Booking',
    'One row per add-on on a booking with days, revenue and cost; profit fills in. The first line of a booking is ticked so bookings with an add-on can be counted.', [
    C('line_id', 'Line', 'text', 9, required=True), C('booking_id', 'Booking', 'text', 10), C('start_date', 'Start date', 'date', 11), C('month', 'Month', 'date', 11), LST('channel', 'Channel', 'channel', 17),
    LST('addon', 'Add-on', 'addon', 19), C('days', 'Days', 'int', 7), C('amount', 'Amount', 'money', 11), C('cost', 'Cost', 'money', 11), C('first_line', 'First line of booking', 'bool', 10),
    CA('profit', 'Profit', 'money', '{col:amount}-{col:cost}', 11),
    CA('month_revenue', 'Add-on revenue of the month', 'money', 'SUMIFS({range:addon_lines.amount},{range:addon_lines.month},{col:month})', 12),
    CA('addon_profit', 'Add-on profit last month', 'money', 'SUMIFS({range:addon_lines.profit},{range:addon_lines.month},%s)' % MLAST, 12),
    COMPANY_COL(), PH('manager_phone', 'Manager phone', D.MANAGER_PHONE), PH('accountant_phone', 'Accountant phone', D.ACCOUNTANT_PHONE)], D.addon_lines_d(), 1500))
# 8 add-on profit --------------------------------------------------------------
tables.append(T('addon_profit', 'Add-on Profit', 'Add-on Profit by Add-on', 'Profit and profit per line of every add-on from the add-on lines.', [
    LST('addon', 'Add-on', 'addon', 20, required=True),
    CA('profit', 'Profit', 'money', 'SUMIFS({range:addon_lines.profit},{range:addon_lines.addon},{col:addon})', 12),
    CA('profit_per_line', 'Profit per line', 'money', 'IFERROR(SUMIFS({range:addon_lines.profit},{range:addon_lines.addon},{col:addon})/COUNTIFS({range:addon_lines.addon},{col:addon}),0)', 12)],
    D.addon_profit_d(), 50, [A('profit_per_line', '< 5', 'warn')]))
# 9 delivery zones -------------------------------------------------------------
tables.append(T('zones', 'Delivery Zones', 'Delivery Zones', 'Each pickup place with the delivery fee for one leg and the run time in minutes.', [
    LST('location', 'Pickup place', 'location', 18, required=True), C('fee_leg', 'Fee per leg', 'money', 11), C('run_minutes', 'Run minutes', 'int', 10)], D.zones_d(), 50))
# 10 channels ------------------------------------------------------------------
tables.append(T('channels', 'Channels', 'Channels', 'Each channel with the share it keeps and the days until you are paid.', [
    LST('channel', 'Channel', 'channel', 18, required=True), C('fee_pct', 'Fee share', 'pct', 10), C('payout_days', 'Days to be paid', 'int', 11)], D.channels_d(), 50))
# 11 cost per day by class -----------------------------------------------------
tables.append(T('cost_floor', 'Cost per Day by Class', 'Cost per Rented Day and Floor Price', 'Cost per rented day of each class over 12 months (loan, insurance, upkeep, cleaning, energy, depreciation) and the floor price with your margin.', [
    LST('class', 'Class', 'class', 14, required=True), C('cost_day', 'Cost per rented day', 'money', 12),
    CA('floor_price', 'Floor price a day', 'money', 'ROUND({col:cost_day}*(1+{set:floor_margin}),2)', 12)], D.cost_floor_d(), 50))
# 12 quote log -----------------------------------------------------------------
FLOOR_TOTAL = 'ROUND(%s*{col:days},2)' % FLOOR_DAY('{col:class}')
tables.append(T('quote_log', 'Quote Log', 'Quote Log against the Floor Price',
    'One row per quote sent: class, days, season and amount; the floor price for the stay, the margin over it and a verdict fill in, with the figures for renter messages.', [
    C('quote_id', 'Quote', 'text', 9, required=True), C('quote_date', 'Quote date', 'date', 11), C('contact', 'Contact', 'text', 18), C('phone', 'Phone', 'text', 18), LST('class', 'Class', 'class', 12),
    C('pickup_date', 'Pickup date', 'date', 11), C('days', 'Days', 'int', 7), LST('location', 'Pickup place', 'location', 16), LST('season', 'Season', 'season', 10), C('quote_amount', 'Quote amount', 'money', 12),
    CA('floor_total', 'Floor price for the stay', 'money', FLOOR_TOTAL, 12), CA('margin', 'Margin over floor', 'money', '{col:quote_amount}-%s' % FLOOR_TOTAL, 11),
    CA('margin_pct', 'Margin over floor share', 'pct', 'IFERROR(({col:quote_amount}-%s)/%s,0)' % (FLOOR_TOTAL, FLOOR_TOTAL), 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:margin}<0,%s,IF({col:margin_pct}<{set:thin_margin},%s,%s))' % (ka('Below floor'), ka('Thin margin'), ka('Above floor')), 12),
    CA('valid_until', 'Quote valid until', 'date', '{col:quote_date}+{set:quote_valid_days}', 11), CA('daily_total', 'Days at the daily rate', 'money', '%s*{col:days}' % CLS_RATE('{col:class}'), 11),
    CA('weekly_price', 'Weekly price', 'money', PLAN_RATE('{col:class}', WEEKLY), 10), CA('monthly_price', 'Monthly price', 'money', PLAN_RATE('{col:class}', MONTHLY), 10),
    CA('addon_price', 'Child seat a day', 'money', 'SUMIFS({range:addons.price_day},{range:addons.addon},%s)' % tok('addon', 'Child seat'), 10),
    CA('young_fee', 'Young-driver fee a day', 'money', 'SUMIFS({range:addons.price_day},{range:addons.addon},%s)' % tok('addon', 'Young-driver fee'), 10),
    CA('fee_leg', 'Delivery fee per leg', 'money', 'SUMIFS({range:zones.fee_leg},{range:zones.location},{col:location})', 10),
    CA('deposit', 'Deposit', 'money', 'SUMIFS({range:classes.deposit},{range:classes.class},{col:class})', 10), CA('event_start', 'Next event starts', 'date', NEXT_EVENT, 11),
    CA('change_date', 'Price change date', 'date', '{set:rise_date}', 11), CA('saving', 'Saved by booking now', 'money', 'ROUND({col:quote_amount}*{set:planned_rise}/(1+{set:planned_rise}),0)', 10), COMPANY_COL()],
    D.quote_log_d(), 200, [A('verdict', '= ' + ka('Below floor'), 'bad'), A('verdict', '= ' + ka('Thin margin'), 'warn')]))
# 13 funnel by month -----------------------------------------------------------
tables.append(T('funnel', 'Funnel by Month', 'Enquiry Funnel by Month',
    'One row per month: enquiries, quotes, bookings, lost enquiries, reply hours, average quote and all bookings that month; conversion fills in.', [
    C('month', 'Month', 'date', 11, required=True), C('enquiries', 'Enquiries', 'int', 10), C('quoted', 'Quoted', 'int', 9), C('booked', 'Booked from enquiries', 'int', 10), C('lost', 'Lost', 'int', 8),
    C('avg_reply_hours', 'Average reply hours', 'num', 10), C('avg_quote', 'Average quote', 'money', 11), C('bookings_all', 'All bookings starting', 'int', 10),
    CA('conversion', 'Conversion', 'pct', 'IFERROR({col:booked}/{col:enquiries},0)', 10), CA('quote_to_booking', 'Quote to booking', 'pct', 'IFERROR({col:booked}/{col:quoted},0)', 10),
    CA('enq_avg3', 'Enquiries a month, 3 months before', 'num', 'SUMIFS({range:funnel.enquiries},{range:funnel.month},">="&EDATE({col:month},-3),{range:funnel.month},"<"&{col:month})/3', 12),
    CA('conv_avg3', 'Conversion, 3 months before', 'pct', 'IFERROR(SUMIFS({range:funnel.booked},{range:funnel.month},">="&EDATE({col:month},-3),{range:funnel.month},"<"&{col:month})/SUMIFS({range:funnel.enquiries},{range:funnel.month},">="&EDATE({col:month},-3),{range:funnel.month},"<"&{col:month}),0)', 12),
    CA('quote_avg3', 'Average quote, 3 months before', 'money', 'IFERROR(AVERAGEIFS({range:funnel.avg_quote},{range:funnel.month},">="&EDATE({col:month},-3),{range:funnel.month},"<"&{col:month}),0)', 12),
    CA('trend', 'Trend against the 3 months before', 'num', 'MAX(0.8,MIN(1.2,IFERROR({col:enquiries}/{col:enq_avg3},1)))', 11)], D.funnel_d(), 60,
    [A('conversion', '< {set:conv_target}', 'warn')]))
# 14 lost reasons --------------------------------------------------------------
tables.append(T('lost_reasons', 'Lost Reasons', 'Lost Enquiries by Reason', 'The five reasons an enquiry is lost with the count and the quote value lost in the last 90 days.', [
    LST('reason', 'Reason', 'lostreason', 16, required=True),
    CA('lost_enquiries', 'Lost enquiries, 90 days', 'int', 'COUNTIFS({range:enquiries.lost_reason},{col:reason},%s)' % D90, 12),
    CA('revenue_lost', 'Quote value lost, 90 days', 'money', 'SUMIFS({range:enquiries.quote_amount},{range:enquiries.lost_reason},{col:reason},%s)' % D90, 13)], D.lost_reasons_d(), 50))
# 15 source conversion ---------------------------------------------------------
tables.append(T('sources', 'Source Conversion', 'Conversion by Source', 'Every channel with the share of its enquiries that became bookings and the booked quote value in 90 days; a marketplace sends bookings, not enquiries.', [
    LST('source', 'Source', 'channel', 18, required=True),
    CA('conversion', 'Conversion, 90 days', 'pct', 'IFERROR(COUNTIFS({range:enquiries.source},{col:source},{range:enquiries.status},%s,%s)/COUNTIFS({range:enquiries.source},{col:source},%s),"")' % (BOOKED, D90, D90), 12),
    CA('revenue', 'Booked quote value, 90 days', 'money', 'SUMIFS({range:enquiries.quote_amount},{range:enquiries.source},{col:source},{range:enquiries.status},%s,%s)' % (BOOKED, D90), 13)], D.sources_d(), 50))
# 16 reply time bands ----------------------------------------------------------
tables.append(T('reply_bands', 'Reply Time Bands', 'Conversion by Reply Time', 'Four bands of hours to the first reply with the enquiries and the share booked in 90 days.', [
    LST('band', 'Band', 'band', 16, required=True),
    CA('enquiries', 'Enquiries, 90 days', 'int', 'COUNTIFS({range:enquiries.reply_band},{col:band},%s)' % D90, 12),
    CA('conversion', 'Conversion, 90 days', 'pct', 'IFERROR(COUNTIFS({range:enquiries.reply_band},{col:band},{range:enquiries.status},%s,%s)/COUNTIFS({range:enquiries.reply_band},{col:band},%s),0)' % (BOOKED, D90, D90), 12)],
    D.bands_d(), 50))
# 17 open quotes ---------------------------------------------------------------
def OQ(c): return LKT('enquiries.%s' % c, 'enquiries.enquiry_id', 'enquiry')
def OQN(c): return LKN('enquiries.%s' % c, 'enquiries.enquiry_id', 'enquiry')
tables.append(T('open_quotes', 'Open Quotes', 'Open Quotes to Follow Up',
    'List the enquiries whose quote is still open; days waiting, the value after decay and the rank to chase fill in from the enquiry log.', [
    REF('enquiry', 'Enquiry', 'enquiries.enquiry_id', 10, required=True),
    CA('contact', 'Contact', 'text', OQ('contact'), 18), CA('phone', 'Phone', 'text', OQ('phone'), 18), CA('source', 'Source', 'text', OQ('source'), 16), CA('class', 'Class', 'text', OQ('class'), 12),
    CA('quote_amount', 'Quote amount', 'money', OQN('quote_amount'), 12), CA('days_waiting', 'Days waiting', 'int', '{today}-' + OQN('date'), 9),
    CA('score', 'Value after decay', 'money', 'ROUND(%s*POWER(1-{set:chase_decay},{today}-%s),2)' % (OQN('quote_amount'), OQN('date')), 12),
    CA('chase_rank', 'Chase rank', 'int', '1+COUNTIFS({range:open_quotes.score},">"&{col:score})', 8),
    CA('verdict', 'Verdict', 'text', 'IF({col:days_waiting}>=3,%s,IF({col:days_waiting}>=1,%s,%s))' % (ka('Chase now'), ka('Chase soon'), ka('Fresh quote')), 12),
    CA('open_n', 'Open quotes now', 'int', 'COUNTIFS({range:enquiries.status},%s)' % QUOTED, 9),
    CA('open_value', 'Value of open quotes', 'money', 'SUMIFS({range:enquiries.quote_amount},{range:enquiries.status},%s)' % QUOTED, 12),
    COMPANY_COL(), PH('owner_phone', 'Owner phone', D.OWNER_PHONE), PH('manager_phone', 'Manager phone', D.MANAGER_PHONE)], D.open_quotes_d(), 100,
    [A('verdict', '= ' + ka('Chase now'), 'bad'), A('verdict', '= ' + ka('Chase soon'), 'warn')]))
# 18 discount steps ------------------------------------------------------------
DS = lambda c: LKN('rates.%s' % c, 'rates.rate_id', 'rate_id')
tables.append(T('discount_steps', 'Discount Steps', 'Weekly and Monthly Discount Steps',
    'Every rate with its day equivalent, the step below the daily rate and the idle days a plan must save to pay for that step.', [
    REF('rate_id', 'Rate', 'rates.rate_id', 9, required=True), CA('class', 'Class', 'text', LKT('rates.class', 'rates.rate_id', 'rate_id'), 12), CA('plan', 'Plan', 'text', LKT('rates.plan', 'rates.rate_id', 'rate_id'), 9),
    CA('rate', 'Rate', 'money', DS('rate'), 10), CA('day_equivalent', 'Day equivalent', 'money', DS('day_equivalent'), 11), CA('daily_rate', 'Daily rate of class', 'money', DS('daily_rate'), 11),
    CA('step_pct', 'Step below the daily rate', 'pct', 'IFERROR(1-{col:day_equivalent}/{col:daily_rate},0)', 11),
    CA('idle_days_pay', 'Idle days that pay for the step', 'num', 'IFERROR(({col:daily_rate}*%s-{col:rate})/{col:day_equivalent},0)' % DS('days'), 12)], D.discount_steps_d(), 100,
    [A('idle_days_pay', '> 3', 'warn')]))
# 19 month seasonality ---------------------------------------------------------
tables.append(T('month_season', 'Month Seasonality', 'Seasonality by Month of the Year',
    'One row per month of the year: its season, multiplier, enquiries and bookings over 24 months and the average day rate achieved; the hotel partner texts use it.', [
    LST('moy', 'Month', 'moy', 12, required=True), C('month_no', 'Month number', 'int', 8), LST('season', 'Season', 'season', 10), C('avg_day_rate', 'Average day rate', 'money', 11),
    CA('multiplier', 'Multiplier', 'num', 'SUMIFS({range:seasons.multiplier},{range:seasons.season},{col:season})', 9),
    CA('enquiries', 'Enquiries, 24 months', 'int', 'SUMPRODUCT((MONTH({range:funnel.month})={col:month_no})*{range:funnel.enquiries})', 11),
    CA('bookings', 'Booked from enquiries, 24 months', 'int', 'SUMPRODUCT((MONTH({range:funnel.month})={col:month_no})*{range:funnel.booked})', 12),
    CA('rate_index', 'Rate against the yearly average', 'num', 'IFERROR({col:avg_day_rate}/AVERAGE({range:month_season.avg_day_rate}),0)', 11),
    COMPANY_COL(), PH('hotel_phone', 'Hotel partner phone', D.HOTEL_PHONE)], D.month_season_d(), 50))
# 20 weekday demand ------------------------------------------------------------
WD = lambda: 'IF({col:weekday}=%s,1,IF({col:weekday}=%s,2,IF({col:weekday}=%s,3,IF({col:weekday}=%s,4,IF({col:weekday}=%s,5,IF({col:weekday}=%s,6,7))))))' % tuple(tok('wday', w) for w in WEEKDAYS[:6])
tables.append(T('weekday_demand', 'Weekday Demand', 'Demand by Pickup Weekday', 'Enquiries and bookings by the weekday of the pickup, from the enquiry log.', [
    LST('weekday', 'Weekday', 'wday', 13, required=True),
    CA('enquiries', 'Enquiries', 'int', 'SUMPRODUCT((WEEKDAY({range:enquiries.pickup_date},2)=%s)*({range:enquiries.enquiry_id}<>""))' % WD(), 10),
    CA('bookings', 'Bookings', 'int', 'SUMPRODUCT((WEEKDAY({range:enquiries.pickup_date},2)=%s)*({range:enquiries.status}=%s))' % (WD(), BOOKED), 10)], D.weekday_d(), 50))
assert len(tables) == 20
TBL = {t['key']: t for t in tables}
