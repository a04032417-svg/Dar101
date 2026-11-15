"""Short-term rental host suite part 3: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr3_lists import *
import sr3_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def OWNP(my='unit'): return CA('owner_phone', 'Owner phone', 'text', LKT('units.owner_phone', 'units.name', my), 18)
def COH(): return CA('cohost_phone', 'Co-host phone', 'text', '"%s"' % D.COHOST_PHONE, 18)
def HOST(): return CA('host_phone', 'Host phone', 'text', '"%s"' % D.OWNER_PHONE, 18)
YES = tok('yn', 'Yes'); NO = tok('yn', 'No')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; NXT = 'DATE(YEAR({today}),MONTH({today})+1,1)'; Y1 = 'DATE(YEAR({today})-1,MONTH({today}),1)'; M3 = 'DATE(YEAR({today}),MONTH({today})-3,1)'


def UMS(col, a, b, by='name'):
    return 'SUMIFS({range:unit_months.%s},{range:unit_months.unit},{col:%s},{range:unit_months.month},">="&%s,{range:unit_months.month},"<"&%s)' % (col, by, a, b)
def OCC3(me, tgt, lo=0.02):
    return 'IF({col:%s}>={col:%s}+%s,%s,IF({col:%s}<{col:%s}-%s,%s,%s))' % (me, tgt, lo, ca('Above target'), me, tgt, lo, ca('Below target'), ca('On target'))

settings = [
    S('company', 'Your company name', 'text', COMPANY), S('target_occupancy', 'Wanted occupancy', 'pct', 0.65), S('target_adr', 'Wanted average daily rate, the average price of a night sold', 'money', 140),
    S('weekend_lift', 'Price lift for Friday and Saturday nights', 'pct', 0.15), S('min_rating', 'Wanted review average, 1 to 5', 'num', 4.3),
    S('warn_days', 'Days ahead to warn of a check-in, a review or a deadline', 'int', 7), S('pace_tolerance', 'Share a unit may differ from its pace target', 'pct', 0.05),
    S('market_tolerance', 'Share of the market a unit may differ before it is flagged', 'pct', 0.05), S('target_margin', 'Wanted profit share of revenue per unit', 'pct', 0.20),
    S('cleaner_rate', 'Cleaner pay per hour', 'money', 17), S('long_block_nights', 'Nights from which a blocked period counts as long', 'int', 10),
    S('growth_band', 'Year-on-year change that counts as growth or a fall', 'pct', 0.03),
]
assert 3 <= len(settings) <= 20

tables = [
    T('unit_months', 'Unit Months', 'Unit months with occupancy, ADR and RevPAR',
      'One row per unit and month: available and booked nights and room revenue; occupancy, ADR (the average price of a night sold), RevPAR (revenue per available night) and the gap to target fill in.', [
        C('um_id', 'Row ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), REF('unit', 'Unit', 'units.name', 26), LST('city', 'City', 'city', 10), LST('unit_type', 'Unit type', 'utype', 11), LST('season', 'Season', 'season', 11),
        C('available_nights', 'Available nights', 'int', 10), C('booked_nights', 'Booked nights', 'int', 10), C('room_revenue', 'Room revenue', 'money', 12),
        CA('occupancy', 'Occupancy', 'pct', 'IF({col:available_nights}>0,{col:booked_nights}/{col:available_nights},0)', 10), CA('adr', 'ADR', 'money', 'IF({col:booked_nights}>0,{col:room_revenue}/{col:booked_nights},0)', 10),
        CA('revpar', 'RevPAR', 'money', 'IF({col:available_nights}>0,{col:room_revenue}/{col:available_nights},0)', 10), CA('target_occ', 'Target occupancy', 'pct', LKN('targets.target_occ', 'targets.unit', 'unit'), 11),
        CA('vs_target', 'Against target', 'pct', '{col:occupancy}-{col:target_occ}', 10), CA('occ_flag', 'Occupancy check', 'text', OCC3('occupancy', 'target_occ'), 14)],
      D.unit_months_d(), 600, [A('occ_flag', '= ' + ca('Below target'), 'warn'), A('occ_flag', '= ' + ca('Above target'), 'good'), A('vs_target', '< -0.25', 'bad')]),
    T('units', 'Units', 'Units with results of the last 12 months',
      'One row per unit: type, city, owner, base rate and cleaner; nights, revenue, occupancy, ADR, RevPAR, the rank this month and the target checks fill in by themselves.', [
        C('unit_id', 'Unit ID', 'text', 9, required=True), C('name', 'Name', 'text', 26), LST('unit_type', 'Unit type', 'utype', 11), LST('city', 'City', 'city', 10), C('bedrooms', 'Bedrooms', 'int', 9),
        C('owner', 'Owner', 'text', 22), C('owner_phone', 'Owner phone', 'text', 18), C('base_rate', 'Base rate', 'money', 11), C('since', 'Listed since', 'date', 11), C('cleaner', 'Cleaner', 'text', 22),
        CA('target_occ', 'Target occupancy', 'pct', LKN('targets.target_occ', 'targets.unit', 'name'), 11), CA('target_adr', 'Target ADR', 'money', LKN('targets.target_adr', 'targets.unit', 'name'), 11),
        CA('avail_12m', 'Available nights, 12 months', 'int', UMS('available_nights', Y1, MS), 12), CA('nights_12m', 'Nights sold, 12 months', 'int', UMS('booked_nights', Y1, MS), 12),
        CA('revenue_12m', 'Room revenue, 12 months', 'money', UMS('room_revenue', Y1, MS), 13), CA('occ_12m', 'Occupancy, 12 months', 'pct', 'IF({col:avail_12m}>0,{col:nights_12m}/{col:avail_12m},0)', 11),
        CA('adr_12m', 'ADR, 12 months', 'money', 'IF({col:nights_12m}>0,{col:revenue_12m}/{col:nights_12m},0)', 11), CA('revpar_12m', 'RevPAR, 12 months', 'money', 'IF({col:avail_12m}>0,{col:revenue_12m}/{col:avail_12m},0)', 11),
        CA('occ_month', 'Occupancy this month', 'pct', 'IFERROR(%s/%s,0)' % (UMS('booked_nights', MS, NXT), UMS('available_nights', MS, NXT)), 11),
        CA('revpar_month', 'RevPAR this month', 'money', 'IFERROR(%s/%s,0)' % (UMS('room_revenue', MS, NXT), UMS('available_nights', MS, NXT)), 11),
        CA('rank_month', 'RevPAR rank this month', 'int', 'COUNTIF({range:units.revpar_month},">"&{col:revpar_month})+1', 11),
        CA('adr_q', 'ADR, last 3 months', 'money', 'IFERROR(%s/%s,0)' % (UMS('room_revenue', M3, MS), UMS('booked_nights', M3, MS)), 11), CA('revenue_q', 'Room revenue, last 3 months', 'money', UMS('room_revenue', M3, MS), 13),
        CA('occ_flag', 'Occupancy check', 'text', OCC3('occ_12m', 'target_occ'), 14), CA('adr_flag', 'ADR check', 'text', 'IF({col:adr_12m}>={col:target_adr}*1.02,%s,IF({col:adr_12m}<{col:target_adr}*0.98,%s,%s))' % (ca('Above target'), ca('Below target'), ca('On target')), 14),
        CA('unit_flag', 'Unit health', 'text', 'IF(AND({col:occ_flag}=%s,{col:adr_flag}=%s),%s,IF(OR({col:occ_flag}=%s,{col:adr_flag}=%s),%s,%s))' % (ca('Below target'), ca('Below target'), ca('Weak unit'), ca('Below target'), ca('Below target'), ca('Watch unit'), ca('Healthy unit')), 14),
        CA('rating_90d', 'Rating, 90 days', 'num', 'IFERROR(AVERAGEIFS({range:review_scores.avg_rating},{range:review_scores.unit},{col:name},{range:review_scores.month},">="&%s,{range:review_scores.month},"<"&%s),0)' % (MS, NXT), 10),
        CA('rating_flag', 'Rating check', 'text', 'IF({col:rating_90d}<{set:min_rating},%s,%s)' % (ca('Under minimum'), ca('Meets minimum')), 14),
        CA('cleaner_phone', 'Cleaner phone', 'text', LKT('team.phone', 'team.name', 'cleaner'), 18), COH(), HOST(), CA('accountant_phone', 'Accountant phone', 'text', '"%s"' % D.ACCT_PHONE, 18),
        CA('handy_phone', 'Handyperson phone', 'text', '"%s"' % D.HANDY_PHONE, 18)],
      D.units_d(), 50, [A('unit_flag', '= ' + ca('Weak unit'), 'bad'), A('unit_flag', '= ' + ca('Watch unit'), 'warn'), A('unit_flag', '= ' + ca('Healthy unit'), 'good'), A('rating_flag', '= ' + ca('Under minimum'), 'warn')]),
    T('bookings', 'Bookings', 'Bookings with ADR, lead time and rate against base',
      'One row per booking: unit, guest, channel, dates, nightly rate and room revenue; the lead time, the ADR of the stay and the rate against the unit base rate fill in by themselves.', [
        C('booking_id', 'Booking ID', 'text', 10, required=True), C('guest', 'Guest', 'text', 24), C('guest_country', 'Guest country', 'text', 16), REF('unit', 'Unit', 'units.name', 26), LST('unit_type', 'Unit type', 'utype', 11),
        LST('city', 'City', 'city', 10), LST('channel', 'Channel', 'chan', 11), C('check_in', 'Check-in', 'date', 11), C('check_out', 'Check-out', 'date', 11), C('booked_on', 'Booked on', 'date', 11), C('nights', 'Nights', 'int', 8),
        C('nightly_rate', 'Nightly rate', 'money', 11), C('room_revenue', 'Room revenue', 'money', 12), LST('status', 'Status', 'bstatus', 11),
        CA('lead_days', 'Lead time, days', 'int', '{col:check_in}-{col:booked_on}', 10), CA('adr', 'ADR of the stay', 'money', 'IF({col:nights}>0,{col:room_revenue}/{col:nights},0)', 10),
        CA('base_rate', 'Unit base rate', 'money', LKN('units.base_rate', 'units.name', 'unit'), 11), CA('rate_vs_base', 'Rate against base', 'pct', 'IF({col:base_rate}>0,{col:nightly_rate}/{col:base_rate}-1,0)', 11),
        CA('rate_flag', 'Rate check', 'text', 'IF({col:rate_vs_base}>0.02,%s,IF({col:rate_vs_base}<-0.02,%s,%s))' % (cb('Rate above base'), cb('Rate below base'), cb('Rate at base')), 14)],
      D.bookings_d(), 700, [A('status', '= ' + tok('bstatus', 'Cancelled'), 'bad'), A('rate_flag', '= ' + cb('Rate below base'), 'warn'), A('rate_flag', '= ' + cb('Rate above base'), 'good')]),
    T('seasons', 'Seasons', 'Seasons with the price factor of each month',
      'Twelve calendar months with the season and the price factor against the base rate; the season planner and the season plan read these.', [
        C('month', 'Month', 'date', 11, required=True), LST('season', 'Season', 'season', 11), C('price_factor', 'Price factor', 'num', 10), HOST()],
      D.seasons_d(), 50),
    T('pace', 'Pace Rows', 'Pace of nights on the books against the target',
      'One row per unit and coming month: nights booked a month ago and now against the nights wanted by now; the pickup, the gap, occupancy on the books and the price move fill in by themselves.', [
        C('pace_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), REF('unit', 'Unit', 'units.name', 26), C('available_nights', 'Available nights', 'int', 10), C('booked_ago', 'Booked a month ago', 'int', 10),
        C('booked_now', 'Booked now', 'int', 10), C('target_nights', 'Target nights now', 'int', 10),
        CA('pickup', 'Nights picked up', 'int', '{col:booked_now}-{col:booked_ago}', 10), CA('gap', 'Pace gap', 'int', '{col:booked_now}-{col:target_nights}', 9),
        CA('gap_pct', 'Gap percent', 'pct', 'IF({col:target_nights}>0,{col:booked_now}/{col:target_nights}-1,0)', 10),
        CA('occ_books', 'Occupancy on the books', 'pct', 'IF({col:available_nights}>0,{col:booked_now}/{col:available_nights},0)', 11), CA('open_nights', 'Open nights', 'int', '{col:available_nights}-{col:booked_now}', 9),
        CA('pace_flag', 'Pace check', 'text', 'IF({col:gap_pct}>{set:pace_tolerance},%s,IF({col:gap_pct}<-{set:pace_tolerance},%s,%s))' % (ca('Ahead of pace'), ca('Behind pace'), ca('On pace')), 14),
        CA('price_move', 'Suggested price move', 'pct', 'IF({col:gap_pct}<-0.15,-0.1,IF({col:gap_pct}<-{set:pace_tolerance},-0.05,IF({col:gap_pct}>0.15,0.08,IF({col:gap_pct}>{set:pace_tolerance},0.04,0))))', 11),
        OWNP(), COH(), HOST(), CA('cleaner_phone', 'Cleaner phone', 'text', LKT('units.cleaner_phone', 'units.name', 'unit'), 18)],
      D.pace_d(), 200, [A('pace_flag', '= ' + ca('Behind pace'), 'warn'), A('pace_flag', '= ' + ca('Ahead of pace'), 'good'), A('gap_pct', '< -0.15', 'bad')]),
    T('blocked', 'Blocked Nights', 'Blocked nights with the revenue they cost',
      'One row per blocked period: unit, dates and reason; the nights, the estimated revenue lost at the unit ADR and occupancy, and whether the block is long or current fill in by themselves.', [
        C('block_id', 'Block ID', 'text', 9, required=True), REF('unit', 'Unit', 'units.name', 26), C('from_date', 'From', 'date', 11), C('to_date', 'To', 'date', 11), LST('reason', 'Reason', 'breason', 13),
        CA('nights', 'Nights blocked', 'int', '{col:to_date}-{col:from_date}+1', 9), CA('adr_12m', 'Unit ADR, 12 months', 'money', LKN('units.adr_12m', 'units.name', 'unit'), 11),
        CA('occ_12m', 'Unit occupancy, 12 months', 'pct', LKN('units.occ_12m', 'units.name', 'unit'), 11), CA('lost_revenue', 'Estimated revenue lost', 'money', '{col:nights}*{col:adr_12m}*{col:occ_12m}', 12),
        CA('block_flag', 'Length check', 'text', 'IF({col:nights}>={set:long_block_nights},%s,%s)' % (cb('Long block'), cb('Short block')), 12),
        CA('block_status', 'Block status', 'text', 'IF({col:to_date}<{today},%s,IF({col:from_date}<={today},%s,%s))' % (ca('Block ended'), ca('Blocked now'), ca('Block ahead')), 12), OWNP(), COH(), HOST()],
      D.blocked_d(), 150, [A('block_flag', '= ' + cb('Long block'), 'warn'), A('block_status', '= ' + ca('Blocked now'), 'good')]),
    T('targets', 'Targets by Unit', 'Targets by unit with the result against them',
      'One row per unit: wanted occupancy, wanted ADR and the yearly revenue goal; the target RevPAR, the results of 12 months against each target and the share of the goal reached fill in by themselves.', [
        REF('unit', 'Unit', 'units.name', 26, required=True), C('target_occ', 'Target occupancy', 'pct', 10), C('target_adr', 'Target ADR', 'money', 10), C('goal_year', 'Yearly revenue goal', 'money', 12), C('set_on', 'Set on', 'date', 11),
        CA('target_revpar', 'Target RevPAR', 'money', '{col:target_occ}*{col:target_adr}', 10), CA('revenue_12m', 'Room revenue, 12 months', 'money', LKN('units.revenue_12m', 'units.name', 'unit'), 12),
        CA('occ_12m', 'Occupancy, 12 months', 'pct', LKN('units.occ_12m', 'units.name', 'unit'), 10), CA('adr_12m', 'ADR, 12 months', 'money', LKN('units.adr_12m', 'units.name', 'unit'), 10),
        CA('revpar_12m', 'RevPAR, 12 months', 'money', LKN('units.revpar_12m', 'units.name', 'unit'), 10),
        CA('goal_pct', 'Share of goal', 'pct', 'IF({col:goal_year}>0,{col:revenue_12m}/{col:goal_year},0)', 10),
        CA('occ_flag', 'Occupancy check', 'text', OCC3('occ_12m', 'target_occ'), 14),
        CA('adr_flag', 'ADR check', 'text', 'IF({col:adr_12m}>={col:target_adr}*1.02,%s,IF({col:adr_12m}<{col:target_adr}*0.98,%s,%s))' % (ca('Above target'), ca('Below target'), ca('On target')), 14),
        CA('revpar_flag', 'RevPAR check', 'text', 'IF({col:revpar_12m}>={col:target_revpar}*1.02,%s,IF({col:revpar_12m}<{col:target_revpar}*0.98,%s,%s))' % (ca('Above target'), ca('Below target'), ca('On target')), 14),
        CA('goal_flag', 'Goal check', 'text', 'IF({col:goal_pct}>=1,%s,IF({col:goal_pct}>=0.85,%s,%s))' % (cb('Goal reached'), cb('Goal in reach'), cb('Goal far away')), 14), OWNP(), HOST()],
      D.targets_d(), 50, [A('revpar_flag', '= ' + ca('Below target'), 'warn'), A('revpar_flag', '= ' + ca('Above target'), 'good'), A('goal_flag', '= ' + cb('Goal far away'), 'bad')]),
    T('city_months', 'City Months', 'City months with occupancy, ADR and RevPAR',
      'One row per city and month, added up from all units there: available and booked nights and room revenue; occupancy, ADR and RevPAR fill in by themselves.', [
        C('cm_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('city', 'City', 'city', 10), C('available_nights', 'Available nights', 'int', 10), C('booked_nights', 'Booked nights', 'int', 10),
        C('room_revenue', 'Room revenue', 'money', 12), CA('occupancy', 'Occupancy', 'pct', 'IF({col:available_nights}>0,{col:booked_nights}/{col:available_nights},0)', 10),
        CA('adr', 'ADR', 'money', 'IF({col:booked_nights}>0,{col:room_revenue}/{col:booked_nights},0)', 10), CA('revpar', 'RevPAR', 'money', 'IF({col:available_nights}>0,{col:room_revenue}/{col:available_nights},0)', 10)],
      D.city_months_d(), 200, [A('occupancy', '< 0.4', 'warn'), A('occupancy', '> 0.85', 'good')]),
    T('type_months', 'Type Months', 'Unit type months with occupancy, ADR and RevPAR',
      'One row per unit type and month, added up from all units of that type: nights, room revenue, occupancy, ADR and RevPAR; the type with the best RevPAR shows in the charts.', [
        C('tm_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('unit_type', 'Unit type', 'utype', 11), C('available_nights', 'Available nights', 'int', 10), C('booked_nights', 'Booked nights', 'int', 10),
        C('room_revenue', 'Room revenue', 'money', 12), CA('occupancy', 'Occupancy', 'pct', 'IF({col:available_nights}>0,{col:booked_nights}/{col:available_nights},0)', 10),
        CA('adr', 'ADR', 'money', 'IF({col:booked_nights}>0,{col:room_revenue}/{col:booked_nights},0)', 10), CA('revpar', 'RevPAR', 'money', 'IF({col:available_nights}>0,{col:room_revenue}/{col:available_nights},0)', 10)],
      D.type_months_d(), 200, [A('occupancy', '< 0.4', 'warn'), A('occupancy', '> 0.85', 'good')]),
    T('weekday', 'Weekday Pattern', 'Weekday pattern of nights slept by unit',
      'One row per unit and weekday over the last 12 months: nights available, nights sold and room revenue; occupancy, ADR and the gap to the unit average show which nights are cheapest to fill.', [
        C('wd_id', 'Row ID', 'text', 9, required=True), REF('unit', 'Unit', 'units.name', 26), LST('weekday', 'Weekday', 'wday', 12), C('available_nights', 'Available nights', 'int', 10), C('booked_nights', 'Booked nights', 'int', 10),
        C('room_revenue', 'Room revenue', 'money', 12), CA('occupancy', 'Occupancy', 'pct', 'IF({col:available_nights}>0,{col:booked_nights}/{col:available_nights},0)', 10),
        CA('adr', 'ADR', 'money', 'IF({col:booked_nights}>0,{col:room_revenue}/{col:booked_nights},0)', 10),
        CA('unit_occ', 'Unit occupancy, all weekdays', 'pct', 'IFERROR(SUMIFS({range:weekday.booked_nights},{range:weekday.unit},{col:unit})/SUMIFS({range:weekday.available_nights},{range:weekday.unit},{col:unit}),0)', 12),
        CA('vs_unit', 'Against unit average', 'pct', '{col:occupancy}-{col:unit_occ}', 10),
        CA('day_flag', 'Night check', 'text', 'IF({col:occupancy}>={col:unit_occ}*1.12,%s,IF({col:occupancy}<={col:unit_occ}*0.88,%s,%s))' % (cb('Strong night'), cb('Weak night'), cb('Normal night')), 13), HOST()],
      D.weekday_d(), 150, [A('day_flag', '= ' + cb('Weak night'), 'warn'), A('day_flag', '= ' + cb('Strong night'), 'good')]),
    T('lead_time', 'Lead Time Curve', 'Lead time curve: bookings by how far ahead they were made',
      'One row per check-in month and lead time bucket: bookings, nights and revenue; the average stay, the ADR and the share of the month fill in by themselves.', [
        C('lt_id', 'Row ID', 'text', 9, required=True), C('month', 'Check-in month', 'date', 11), LST('lead_bucket', 'Lead time bucket', 'band', 18), C('bookings', 'Bookings', 'int', 9), C('nights', 'Nights', 'int', 9), C('revenue', 'Room revenue', 'money', 12),
        CA('avg_stay', 'Average stay', 'num', 'IF({col:bookings}>0,{col:nights}/{col:bookings},0)', 9), CA('adr', 'ADR', 'money', 'IF({col:nights}>0,{col:revenue}/{col:nights},0)', 10),
        CA('share_month', 'Share of the month bookings', 'pct', 'IFERROR({col:bookings}/SUMIFS({range:lead_time.bookings},{range:lead_time.month},{col:month}),0)', 12)],
      D.lead_time_d(), 150),
    T('yoy', 'Year on Year', 'Year on year by unit and month',
      'One row per unit and month with nights and revenue this year and a year earlier; the change in nights, revenue and ADR and the trend fill in by themselves.', [
        C('yy_id', 'Row ID', 'text', 9, required=True), REF('unit', 'Unit', 'units.name', 26), C('month', 'Month', 'date', 11), C('nights_this', 'Nights this year', 'int', 10), C('nights_last', 'Nights last year', 'int', 10),
        C('revenue_this', 'Revenue this year', 'money', 12), C('revenue_last', 'Revenue last year', 'money', 12),
        CA('nights_change', 'Change in nights', 'pct', 'IF({col:nights_last}>0,{col:nights_this}/{col:nights_last}-1,0)', 10), CA('change_pct', 'Change in revenue', 'pct', 'IF({col:revenue_last}>0,{col:revenue_this}/{col:revenue_last}-1,0)', 10),
        CA('adr_this', 'ADR this year', 'money', 'IF({col:nights_this}>0,{col:revenue_this}/{col:nights_this},0)', 10), CA('adr_last', 'ADR last year', 'money', 'IF({col:nights_last}>0,{col:revenue_last}/{col:nights_last},0)', 10),
        CA('adr_change', 'Change in ADR', 'pct', 'IF({col:adr_last}>0,{col:adr_this}/{col:adr_last}-1,0)', 10),
        CA('trend', 'Trend', 'text', 'IF({col:change_pct}>{set:growth_band},%s,IF({col:change_pct}<-{set:growth_band},%s,%s))' % (ca('Growing'), ca('Falling'), ca('Flat')), 10), HOST()],
      D.yoy_d(), 250, [A('trend', '= ' + ca('Falling'), 'warn'), A('trend', '= ' + ca('Growing'), 'good')]),
    T('orphan', 'Orphan Nights', 'Orphan nights: free nights between two bookings',
      'One row per free night or short gap between two bookings: unit, date, length and whether it was filled; the revenue missed at the unit ADR and the fill check fill in by themselves.', [
        C('orphan_id', 'Gap ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), REF('unit', 'Unit', 'units.name', 26), C('gap_length', 'Gap length, nights', 'int', 10), LST('filled', 'Filled', 'yn', 8), C('revenue_recovered', 'Revenue recovered', 'money', 12),
        CA('adr_12m', 'Unit ADR, 12 months', 'money', LKN('units.adr_12m', 'units.name', 'unit'), 11), CA('missed', 'Revenue missed', 'money', 'IF({col:filled}=%s,0,{col:gap_length}*{col:adr_12m})' % NO, 11),
        CA('fill_flag', 'Fill check', 'text', 'IF({col:filled}=%s,%s,%s)' % (YES, ca('Gap filled'), ca('Gap missed')), 11), COH(), HOST()],
      D.orphan_d(), 150, [A('fill_flag', '= ' + ca('Gap missed'), 'warn'), A('fill_flag', '= ' + ca('Gap filled'), 'good')]),
    T('review_scores', 'Review Scores by Unit', 'Review scores by unit and month',
      'One row per unit and month-end: reviews and the average rating of the last 90 days; the rating band and the check against your minimum rating fill in by themselves.', [
        C('rs_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), REF('unit', 'Unit', 'units.name', 26), C('reviews', 'Reviews, 90 days', 'int', 10), C('avg_rating', 'Average rating', 'num', 10),
        CA('band', 'Rating band', 'text', 'IF({col:avg_rating}>=4.7,%s,IF({col:avg_rating}>={set:min_rating},%s,IF({col:avg_rating}>=4,%s,%s)))' % (ca('Strong rating'), ca('Good rating'), ca('Weak rating'), ca('Poor rating')), 13),
        CA('min_flag', 'Minimum check', 'text', 'IF({col:avg_rating}<{set:min_rating},%s,%s)' % (ca('Under minimum'), ca('Meets minimum')), 13), CA('occ_month', 'Unit occupancy, last 12 months', 'pct', LKN('units.occ_12m', 'units.name', 'unit'), 12)],
      D.review_scores_d(), 150, [A('band', '= ' + ca('Poor rating'), 'bad'), A('band', '= ' + ca('Weak rating'), 'warn'), A('band', '= ' + ca('Strong rating'), 'good')]),
    T('channel_mix', 'Channel Mix by Unit', 'Channel mix by unit over 12 months',
      'One row per unit and channel over the last 12 months: nights sold and room revenue; the share of the unit nights, the ADR and the main channel check fill in by themselves.', [
        C('cx_id', 'Row ID', 'text', 9, required=True), REF('unit', 'Unit', 'units.name', 26), LST('channel', 'Channel', 'chan', 11), C('nights', 'Nights', 'int', 9), C('room_revenue', 'Room revenue', 'money', 12),
        CA('share_nights', 'Share of unit nights', 'pct', 'IFERROR({col:nights}/SUMIFS({range:channel_mix.nights},{range:channel_mix.unit},{col:unit}),0)', 11), CA('adr', 'ADR', 'money', 'IF({col:nights}>0,{col:room_revenue}/{col:nights},0)', 10),
        CA('channel_flag', 'Channel check', 'text', 'IF({col:share_nights}>=0.4,%s,%s)' % (cb('Main channel'), cb('Minor channel')), 13)],
      D.channel_mix_d(), 100, [A('channel_flag', '= ' + cb('Main channel'), 'good')]),
    T('cities', 'Cities', 'City and season with local occupancy tax',
      'One row per city and season: local occupancy tax (a tax on each night, collected from the guest) and a demand factor; the occupancy and ADR of your units there fill in by themselves.', [
        LST('city', 'City', 'city', 10, required=True), LST('season', 'Season', 'season', 11), C('tax_pct', 'Local tax share', 'pct', 11), C('demand_factor', 'Demand factor', 'num', 10),
        CA('occ', 'Occupancy of the units', 'pct', 'IFERROR(AVERAGEIFS({range:unit_months.occupancy},{range:unit_months.city},{col:city},{range:unit_months.season},{col:season}),0)', 11),
        CA('adr', 'ADR of the units', 'money', 'IFERROR(AVERAGEIFS({range:unit_months.adr},{range:unit_months.city},{col:city},{range:unit_months.season},{col:season},{range:unit_months.booked_nights},">0"),0)', 11)],
      D.cities_d(), 50, [A('occ', '< 0.4', 'warn')]),
    T('stay_mix', 'Length of Stay Mix', 'Length of stay mix by unit over 12 months',
      'One row per unit and stay length bucket over the last 12 months: bookings, nights and room revenue; the share of nights, the ADR and the revenue per booking fill in by themselves.', [
        C('sx_id', 'Row ID', 'text', 9, required=True), REF('unit', 'Unit', 'units.name', 26), LST('stay_bucket', 'Stay length', 'stay', 20), C('bookings', 'Bookings', 'int', 9), C('nights', 'Nights', 'int', 9), C('revenue', 'Room revenue', 'money', 12),
        CA('share_nights', 'Share of unit nights', 'pct', 'IFERROR({col:nights}/SUMIFS({range:stay_mix.nights},{range:stay_mix.unit},{col:unit}),0)', 11), CA('adr', 'ADR', 'money', 'IF({col:nights}>0,{col:revenue}/{col:nights},0)', 10),
        CA('rev_per_booking', 'Revenue per booking', 'money', 'IF({col:bookings}>0,{col:revenue}/{col:bookings},0)', 11)],
      D.stay_mix_d(), 100),
    T('perf_reviews', 'Performance Reviews', 'Performance reviews with findings and actions',
      'One row per finding on a unit: what was found, the action, who owns it, the due date and when it was done; the status, the days to the due date and the unit results fill in by themselves.', [
        C('pr_id', 'Review ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), REF('unit', 'Unit', 'units.name', 26), C('finding', 'Finding', 'text', 30), C('action', 'Action', 'text', 30), REF('owner', 'Action owner', 'team.name', 22),
        C('due_date', 'Due date', 'date', 11), C('done_on', 'Done on', 'date', 11),
        CA('status', 'Status', 'text', 'IF({col:done_on}>0,%s,IF({col:due_date}<{today},%s,IF({col:due_date}-{today}<={set:warn_days},%s,%s)))' % (ca('Done'), ca('Overdue'), ca('Due soon'), ca('Open')), 11),
        CA('days_to_due', 'Days to the due date', 'int', 'IF({col:done_on}>0,0,{col:due_date}-{today})', 10), CA('occ_12m', 'Unit occupancy, 12 months', 'pct', LKN('units.occ_12m', 'units.name', 'unit'), 12), OWNP(), HOST()],
      D.perf_reviews_d(), 100, [A('status', '= ' + ca('Overdue'), 'bad'), A('status', '= ' + ca('Due soon'), 'warn'), A('status', '= ' + ca('Done'), 'good')]),
    T('market', 'Competitor Set Summary', 'Competitor set summary: our results against the market',
      'One row per city and month: the occupancy and ADR of comparable listings from your own market checks; our own results come from City Months, with the indexes and the checks.', [
        C('mk_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('city', 'City', 'city', 10), C('market_occupancy', 'Market occupancy', 'pct', 10), C('market_adr', 'Market ADR', 'money', 10),
        CA('our_occupancy', 'Our occupancy', 'pct', 'IFERROR(SUMIFS({range:city_months.booked_nights},{range:city_months.city},{col:city},{range:city_months.month},{col:month})/SUMIFS({range:city_months.available_nights},{range:city_months.city},{col:city},{range:city_months.month},{col:month}),0)', 10),
        CA('our_adr', 'Our ADR', 'money', 'IFERROR(SUMIFS({range:city_months.room_revenue},{range:city_months.city},{col:city},{range:city_months.month},{col:month})/SUMIFS({range:city_months.booked_nights},{range:city_months.city},{col:city},{range:city_months.month},{col:month}),0)', 10),
        CA('occ_index', 'Occupancy index', 'num', 'IF({col:market_occupancy}>0,{col:our_occupancy}/{col:market_occupancy},0)', 10), CA('adr_index', 'ADR index', 'num', 'IF({col:market_adr}>0,{col:our_adr}/{col:market_adr},0)', 10),
        CA('occ_flag', 'Occupancy check', 'text', 'IF({col:occ_index}>1+{set:market_tolerance},%s,IF({col:occ_index}<1-{set:market_tolerance},%s,%s))' % (ca('Above market'), ca('Below market'), ca('Fair share')), 14),
        CA('adr_flag', 'ADR check', 'text', 'IF({col:adr_index}>1+{set:market_tolerance},%s,IF({col:adr_index}<1-{set:market_tolerance},%s,%s))' % (ca('Above market'), ca('Below market'), ca('Fair share')), 14),
        CA('owner_phone', 'Owner phone', 'text', LKT('units.owner_phone', 'units.city', 'city'), 18), HOST()],
      D.market_d(), 150, [A('occ_flag', '= ' + ca('Below market'), 'warn'), A('occ_flag', '= ' + ca('Above market'), 'good')]),
    T('team', 'Team', 'Team with the review actions owned',
      'The host, the co-host (a helper who handles guests for a fee), four cleaners, two handypeople and four outside contacts; the review actions each person owns fill in by themselves.', [
        C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 14), LST('team', 'Team', 'team', 12), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
        C('hours_week', 'Hours a week', 'int', 10), C('hourly_rate', 'Hourly rate', 'money', 10), C('speciality', 'Speciality', 'text', 26), C('country', 'Country', 'text', 14), C('start', 'Start', 'date', 11),
        CA('actions', 'Review actions owned', 'int', 'COUNTIFS({range:perf_reviews.owner},{col:name})', 10),
        CA('actions_open', 'Actions not done', 'int', 'COUNTIFS({range:perf_reviews.owner},{col:name})-COUNTIFS({range:perf_reviews.owner},{col:name},{range:perf_reviews.status},%s)' % ca('Done'), 10)],
      D.team_d(), 50),
]
assert len(tables) == 20, len(tables)
for _t in tables:
    if len(_t['hint'])>200: print(_t['key'],len(_t['hint']))
for _t in tables: assert len(_t['hint']) <= 200 and len(_t['title']) <= 60, (_t['key'], len(_t['hint']), len(_t['title']))
