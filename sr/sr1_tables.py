"""Short-term rental host suite part 1: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr1_lists import *
import sr1_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def OWNP(my='unit'): return CA('owner_phone', 'Owner phone', 'text', LKT('units.owner_phone', 'units.name', my), 18)
def COH(): return CA('cohost_phone', 'Co-host phone', 'text', '"%s"' % D.COHOST_PHONE, 18)
def HOST(): return CA('host_phone', 'Host phone', 'text', '"%s"' % D.OWNER_PHONE, 18)
BS = lambda s: tok('bstatus', s)
YES = tok('yn', 'Yes')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; NXT = 'DATE(YEAR({today}),MONTH({today})+1,1)'; Y1 = 'DATE(YEAR({today})-1,MONTH({today}),1)'

settings = [
    S('company', 'Your company name', 'text', COMPANY), S('target_occupancy', 'Wanted occupancy', 'pct', 0.65), S('target_adr', 'Wanted average daily rate, the average price of a night sold', 'money', 140),
    S('weekend_lift', 'Price lift for Friday and Saturday nights', 'pct', 0.15), S('rate_tolerance', 'Share a listed rate may differ from the suggested rate', 'pct', 0.08),
    S('warn_days', 'Days ahead to warn of a check-in, a review or a deadline', 'int', 7), S('event_days', 'Days ahead to treat a local event as coming soon', 'int', 45),
    S('cleaner_rate', 'Cleaner pay per hour', 'money', 17), S('fee_margin_target', 'Wanted margin of the cleaning fee over its cost', 'pct', 0.30),
    S('gap_discount', 'Usual discount for a free night between two bookings', 'pct', 0.10), S('lastmin_days', 'Days before check-in that count as last minute', 'int', 3),
    S('lastmin_discount', 'Usual last-minute discount', 'pct', 0.15), S('weekly_discount', 'Usual discount for a stay of 7 nights or more', 'pct', 0.08),
    S('direct_discount', 'Usual discount for a direct booking', 'pct', 0.05),
]
assert 3 <= len(settings) <= 20

PRICE_COLS = [C('price_id', 'Row ID', 'text', 10, required=True), C('week', 'Week (Monday)', 'date', 12), REF('unit', 'Unit', 'units.name', 26), C('season_factor', 'Season factor', 'num', 9),
              C('demand_index', 'Demand index', 'num', 9), C('event', 'Local event', 'text', 22), C('base_rate', 'Base rate', 'money', 11), C('listed_rate', 'Listed rate', 'money', 11), C('booked_nights', 'Booked nights', 'int', 9),
              C('free_nights', 'Free nights', 'int', 9), C('avg_booked_rate', 'Average booked rate', 'money', 12), C('min_stay', 'Minimum stay', 'int', 9)]
SUG = 'ROUND({col:base_rate}*{col:season_factor}*{col:demand_index},0)'

tables = [
    T('units', 'Units', 'Units with rates and results of the last 12 months',
      'One row per unit: type, city, owner, base rate, cleaning fee and fixed costs; nights, revenue, the average price of a night sold (ADR), occupancy, break-even rate and the rate card figures fill in by themselves.', [
        C('unit_id', 'Unit ID', 'text', 9, required=True), C('name', 'Name', 'text', 26), LST('unit_type', 'Unit type', 'utype', 11), LST('city', 'City', 'city', 10), C('bedrooms', 'Bedrooms', 'int', 9), C('max_guests', 'Guests', 'int', 8),
        C('owner', 'Owner', 'text', 22), C('owner_phone', 'Owner phone', 'text', 18), C('base_rate', 'Base rate', 'money', 11), C('cleaning_fee', 'Cleaning fee', 'money', 11), C('mgmt_pct', 'Management fee', 'pct', 10),
        C('rent', 'Rent per month', 'money', 11), C('utilities', 'Utilities per month', 'money', 11), C('internet', 'Internet per month', 'money', 11), C('since', 'Listed since', 'date', 11), LST('cohost', 'Co-host', 'yn', 8),
        CA('nights_12m', 'Nights, 12 months', 'int', 'SUMIFS({range:unit_months.booked_nights},{range:unit_months.unit},{col:name},{range:unit_months.month},">="&%s,{range:unit_months.month},"<"&%s)' % (Y1, MS), 11),
        CA('avail_12m', 'Available nights, 12 months', 'int', 'SUMIFS({range:unit_months.available_nights},{range:unit_months.unit},{col:name},{range:unit_months.month},">="&%s,{range:unit_months.month},"<"&%s)' % (Y1, MS), 12),
        CA('revenue_12m', 'Room revenue, 12 months', 'money', 'SUMIFS({range:unit_months.room_revenue},{range:unit_months.unit},{col:name},{range:unit_months.month},">="&%s,{range:unit_months.month},"<"&%s)' % (Y1, MS), 13),
        CA('adr_12m', 'ADR, 12 months', 'money', 'IF({col:nights_12m}>0,{col:revenue_12m}/{col:nights_12m},0)', 11),
        CA('occ_12m', 'Occupancy, 12 months', 'pct', 'IF({col:avail_12m}>0,{col:nights_12m}/{col:avail_12m},0)', 11),
        CA('adr_vs_base', 'ADR against base rate', 'pct', 'IF({col:base_rate}>0,{col:adr_12m}/{col:base_rate}-1,0)', 11),
        CA('adr_flag', 'ADR check', 'text', 'IF({col:adr_vs_base}>0.02,%s,IF({col:adr_vs_base}<-0.02,%s,%s))' % (cb('Rate above base'), cb('Rate below base'), cb('Rate at base')), 15),
        CA('break_even', 'Break-even rate', 'money', LKN('breakeven.break_even_rate', 'breakeven.unit', 'name'), 11),
        CA('be_flag', 'Break-even check', 'text', 'IF({col:adr_12m}>={col:break_even},%s,%s)' % (ca('Above break-even'), ca('Below break-even')), 16),
        CA('low_rate', 'Lowest season rate', 'money', 'ROUND({col:base_rate}*MIN({range:seasons.price_factor}),0)', 11),
        CA('peak_rate', 'Peak season rate', 'money', 'ROUND({col:base_rate}*MAX({range:seasons.price_factor}),0)', 11),
        CA('peak_weekend', 'Peak weekend rate', 'money', 'ROUND({col:peak_rate}*(1+{set:weekend_lift}),0)', 11),
        CA('books_13w', 'Revenue on the books, 13 weeks', 'money', 'SUMPRODUCT(({range:pricing.unit}={col:name})*{range:pricing.booked_nights}*{range:pricing.avg_booked_rate})', 14),
        CA('free_13w', 'Free nights, 13 weeks', 'int', 'SUMIFS({range:pricing.free_nights},{range:pricing.unit},{col:name})', 11),
        CA('cohost_phone', 'Co-host phone', 'text', '"%s"' % D.COHOST_PHONE, 18), CA('accountant_phone', 'Accountant phone', 'text', '"%s"' % D.ACCT_PHONE, 18)],
      D.units_d(), 50, [A('be_flag', '= ' + ca('Below break-even'), 'bad'), A('adr_flag', '= ' + cb('Rate below base'), 'warn'), A('adr_flag', '= ' + cb('Rate above base'), 'good')]),
    T('pricing', 'Pricing Calendar', 'Pricing calendar by unit and week with suggested rate',
      'One row per unit and week: base rate, season and demand factors, local event, listed rate and booked and free nights; the suggested rate, the gap to it, the fill check and the revenue left on the table fill in by themselves.',
      PRICE_COLS + [
        CA('season', 'Season', 'text', 'IFERROR(INDEX({range:seasons.season},MONTH({col:week}+3)),"")', 11),
        CA('suggested_rate', 'Suggested rate', 'money', SUG, 11), CA('gap_to_suggested', 'Gap to suggested', 'money', '{col:listed_rate}-' + SUG, 11),
        CA('rate_flag', 'Rate check', 'text', 'IF({col:listed_rate}<%s*(1-{set:rate_tolerance}),%s,IF({col:listed_rate}>%s*(1+{set:rate_tolerance}),%s,%s))' % (SUG, ca('Below suggested rate'), SUG, ca('Above suggested rate'), ca('On suggested rate')), 18),
        CA('week_nights', 'Nights in the week', 'int', '{col:booked_nights}+{col:free_nights}', 9), CA('occupancy', 'Occupancy', 'pct', 'IF({col:booked_nights}+{col:free_nights}>0,{col:booked_nights}/({col:booked_nights}+{col:free_nights}),0)', 10),
        CA('fill_flag', 'Fill check', 'text', 'IF({col:free_nights}=0,%s,IF({col:free_nights}<=2,%s,%s))' % (ca('Fully booked'), ca('Few free nights'), ca('Many free nights')), 16),
        CA('left_on_table', 'Revenue left at the booked rate', 'money', '{col:booked_nights}*MAX(0,%s-{col:avg_booked_rate})' % SUG, 13),
        OWNP(), COH(), HOST()],
      D.pricing_d(), 400, [A('rate_flag', '= ' + ca('Below suggested rate'), 'warn'), A('fill_flag', '= ' + ca('Many free nights'), 'warn'), A('left_on_table', '> 300', 'bad'), A('fill_flag', '= ' + ca('Fully booked'), 'good')]),
    T('seasons', 'Seasons', 'Seasons with the price factor of each month',
      'Twelve calendar months with the season and the price factor against the base rate; the rate card tools and the unit rate cards read these.', [
        C('month', 'Month', 'date', 11, required=True), LST('season', 'Season', 'season', 11), C('price_factor', 'Price factor', 'num', 10)],
      D.seasons_d(), 50),
    T('bookings', 'Bookings', 'Bookings with channel, rate and lead time',
      'One row per booking: unit, guest, channel, dates, nightly rate, room revenue and cleaning fee; the lead time, the rate against the base rate, the platform fee and the guest offer prices fill in by themselves.', [
        C('booking_id', 'Booking ID', 'text', 10, required=True), C('guest', 'Guest', 'text', 24), C('guest_phone', 'Guest phone', 'text', 18), C('guest_country', 'Guest country', 'text', 16), REF('unit', 'Unit', 'units.name', 26),
        LST('unit_type', 'Unit type', 'utype', 11), LST('city', 'City', 'city', 10), LST('channel', 'Channel', 'chan', 11), C('check_in', 'Check-in', 'date', 11), C('check_out', 'Check-out', 'date', 11), C('booked_on', 'Booked on', 'date', 11),
        C('nights', 'Nights', 'int', 8), LST('lead_band', 'Lead time band', 'band', 14), C('nightly_rate', 'Nightly rate', 'money', 11), C('room_revenue', 'Room revenue', 'money', 12), C('cleaning_fee', 'Cleaning fee', 'money', 11),
        C('gross', 'Gross', 'money', 11), LST('status', 'Status', 'bstatus', 11),
        CA('lead_days', 'Lead time, days', 'int', '{col:check_in}-{col:booked_on}', 10), CA('base_rate', 'Unit base rate', 'money', LKN('units.base_rate', 'units.name', 'unit'), 11),
        CA('rate_vs_base', 'Rate against base', 'pct', 'IF({col:base_rate}>0,{col:nightly_rate}/{col:base_rate}-1,0)', 11), CA('is_direct', 'Direct', 'int', 'IF({col:channel}=%s,1,0)' % tok('chan', 'Direct'), 8),
        CA('fee_pct', 'Channel fee', 'pct', LKN('channels.fee_pct', 'channels.channel', 'channel'), 9), CA('platform_fee', 'Platform fee', 'money', '{col:room_revenue}*{col:fee_pct}', 11),
        CA('direct_rate', 'Direct offer rate', 'money', 'ROUND({col:nightly_rate}*(1-{set:direct_discount}),0)', 11), CA('weekly_rate', 'Weekly stay rate', 'money', 'ROUND({col:nightly_rate}*(1-{set:weekly_discount}),0)', 11),
        CA('lastmin_rate', 'Last-minute rate', 'money', 'ROUND({col:nightly_rate}*(1-{set:lastmin_discount}),0)', 11), CA('gap_rate', 'Gap night rate', 'money', 'ROUND({col:nightly_rate}*(1-{set:gap_discount}),0)', 11)],
      D.bookings_d(), 700, [A('status', '= ' + BS('Cancelled'), 'bad'), A('rate_vs_base', '< -0.1', 'warn'), A('rate_vs_base', '> 0.3', 'good')]),
    T('unit_months', 'Unit Months', 'Unit months with occupancy, ADR and RevPAR',
      'One row per unit and month: available and booked nights and room revenue; occupancy, ADR (the average price of a night sold), RevPAR (revenue per available night) and the gap to your occupancy target fill in by themselves.', [
        C('um_id', 'Row ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), REF('unit', 'Unit', 'units.name', 26), LST('city', 'City', 'city', 10), LST('season', 'Season', 'season', 11),
        C('available_nights', 'Available nights', 'int', 10), C('booked_nights', 'Booked nights', 'int', 10), C('room_revenue', 'Room revenue', 'money', 12),
        CA('occupancy', 'Occupancy', 'pct', 'IF({col:available_nights}>0,{col:booked_nights}/{col:available_nights},0)', 10), CA('adr', 'ADR', 'money', 'IF({col:booked_nights}>0,{col:room_revenue}/{col:booked_nights},0)', 10),
        CA('revpar', 'RevPAR', 'money', 'IF({col:available_nights}>0,{col:room_revenue}/{col:available_nights},0)', 10), CA('vs_target', 'Against occupancy target', 'pct', '{col:occupancy}-{set:target_occupancy}', 12)],
      D.unit_months_d(), 600, [A('vs_target', '< -0.25', 'warn'), A('vs_target', '> 0.1', 'good')]),
    T('rate_changes', 'Rate Changes', 'Rate changes with change percent and bookings after',
      'One row per rate change: unit, old and new rate, reason and who changed it; the change percent, the direction and the bookings made in the next 14 days fill in by themselves.', [
        C('rc_id', 'Change ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('unit', 'Unit', 'units.name', 26), C('old_rate', 'Old rate', 'money', 10), C('new_rate', 'New rate', 'money', 10),
        LST('reason', 'Reason', 'reason', 16), REF('changed_by', 'Changed by', 'team.name', 22),
        CA('change_pct', 'Change percent', 'pct', 'IF({col:old_rate}>0,{col:new_rate}/{col:old_rate}-1,0)', 10),
        CA('direction', 'Direction', 'text', 'IF({col:new_rate}>{col:old_rate},%s,IF({col:new_rate}<{col:old_rate},%s,%s))' % (cb('Rate raised'), cb('Rate cut'), cb('Rate unchanged')), 13),
        CA('bookings_14d', 'Bookings in the next 14 days', 'int', 'COUNTIFS({range:bookings.unit},{col:unit},{range:bookings.booked_on},">="&{col:date},{range:bookings.booked_on},"<="&({col:date}+14),{range:bookings.status},"<>"&%s)' % BS('Cancelled'), 12),
        OWNP()],
      D.rate_changes_d(), 400, [A('direction', '= ' + cb('Rate cut'), 'warn'), A('change_pct', '> 0.3', 'good')]),
    T('events', 'Local Events', 'Local events with demand lift and days to the event',
      'One row per local event that changes demand: city, dates and the demand lift; the days to the event, its nights, the check and the free nights still listed in the event week fill in by themselves.', [
        C('event_id', 'Event ID', 'text', 9, required=True), C('event', 'Event', 'text', 26), LST('city', 'City', 'city', 10), C('start_date', 'Start', 'date', 11), C('end_date', 'End', 'date', 11), C('demand_lift', 'Demand lift', 'pct', 10),
        CA('days_to_event', 'Days to the event', 'int', '{col:start_date}-{today}', 10), CA('event_nights', 'Event nights', 'int', '{col:end_date}-{col:start_date}+1', 9),
        CA('event_flag', 'Event check', 'text', 'IF({col:end_date}<{today},%s,IF({col:start_date}<={today},%s,IF({col:days_to_event}<={set:event_days},%s,%s)))' % (ca('Past event'), ca('Happening now'), ca('Coming soon'), ca('Later')), 14),
        CA('free_listed', 'Free nights listed in the event', 'int', 'SUMIFS({range:pricing.free_nights},{range:pricing.event},{col:event})', 13), COH()],
      D.events_d(), 60, [A('event_flag', '= ' + ca('Coming soon'), 'warn'), A('event_flag', '= ' + ca('Happening now'), 'good')]),
    T('comps', 'Comparable Listings', 'Comparable listings with the gap to our rate',
      'One row per comparable listing near one of your units: its weekday and weekend rate and review score; our base rate, the gap to it and who is priced above or below us fill in by themselves.', [
        C('comp_id', 'Comparable ID', 'text', 11, required=True), REF('unit', 'Our unit', 'units.name', 26), C('comparable', 'Comparable', 'text', 34), LST('city', 'City', 'city', 10), C('bedrooms', 'Bedrooms', 'int', 9),
        C('weekday_rate', 'Weekday rate', 'money', 11), C('weekend_rate', 'Weekend rate', 'money', 11), C('review_score', 'Review score', 'num', 9), C('checked_on', 'Checked on', 'date', 11),
        CA('our_rate', 'Our base rate', 'money', LKN('units.base_rate', 'units.name', 'unit'), 11), CA('gap_to_our_rate', 'Gap to our rate', 'money', '{col:weekday_rate}-{col:our_rate}', 11),
        CA('gap_pct', 'Gap percent', 'pct', 'IF({col:our_rate}>0,{col:weekday_rate}/{col:our_rate}-1,0)', 10),
        CA('position', 'Position', 'text', 'IF({col:gap_pct}>0.05,%s,IF({col:gap_pct}<-0.05,%s,%s))' % (ca('Priced above us'), ca('Priced below us'), ca('Close to our rate')), 15),
        CA('weekend_premium', 'Weekend premium', 'pct', 'IF({col:weekday_rate}>0,{col:weekend_rate}/{col:weekday_rate}-1,0)', 10), OWNP(), HOST()],
      D.comps_d(), 80, [A('position', '= ' + ca('Priced below us'), 'warn'), A('position', '= ' + ca('Priced above us'), 'good')]),
    T('discounts', 'Discount Rules', 'Discount rules with the example price',
      'One row per discount rule: trigger, which units it covers, the days before check-in, the percent off, the minimum nights and whether it is on; the example price on an average unit and the rule check fill in by themselves.', [
        C('rule_id', 'Rule ID', 'text', 9, required=True), C('rule', 'Rule', 'text', 36), LST('trigger', 'Trigger', 'dtrig', 16), C('unit_scope', 'Units covered', 'text', 20), C('trigger_days', 'Trigger days before check-in', 'int', 12),
        C('discount_pct', 'Discount', 'pct', 10), C('min_nights', 'Minimum nights', 'int', 10), LST('active', 'Active', 'yn', 8),
        CA('example_rate', 'Example rate on an average unit', 'money', 'ROUND(AVERAGE({range:units.base_rate})*(1-{col:discount_pct}),0)', 13),
        CA('rule_flag', 'Rule check', 'text', 'IF({col:active}=%s,%s,%s)' % (YES, cb('Rule is on'), cb('Rule is off')), 12)],
      D.discounts_d(), 50, [A('rule_flag', '= ' + cb('Rule is off'), 'warn')]),
    T('minstay', 'Minimum-Stay Rules', 'Minimum-stay rules by unit and season',
      'One row per unit and season: the shortest stay accepted on weekdays, on weekends and for a free night between two bookings; the strictest rule, the gap check and the review check fill in by themselves.', [
        C('ms_id', 'Rule ID', 'text', 9, required=True), REF('unit', 'Unit', 'units.name', 26), LST('season', 'Season', 'season', 11), C('weekday_min', 'Weekday minimum', 'int', 10), C('weekend_min', 'Weekend minimum', 'int', 10),
        C('gap_min', 'Gap-night minimum', 'int', 10), C('review_on', 'Reviewed on', 'date', 11),
        CA('strictest', 'Strictest minimum', 'int', 'MAX({col:weekday_min},{col:weekend_min},{col:gap_min})', 10),
        CA('gap_flag', 'Gap check', 'text', 'IF({col:gap_min}<{col:weekday_min},%s,%s)' % (ca('Gap nights allowed'), ca('Gap nights blocked')), 16),
        CA('review_flag', 'Review check', 'text', 'IF({today}-{col:review_on}>90,%s,%s)' % (cb('Review due'), cb('Review planned')), 13), OWNP(), COH()],
      D.minstay_d(), 60, [A('review_flag', '= ' + cb('Review due'), 'warn'), A('gap_flag', '= ' + ca('Gap nights blocked'), 'warn')]),
    T('gaps', 'Gap Nights', 'Gap nights with offer rate and revenue recovered',
      'One row per free night or run of free nights between two bookings: unit, usual rate and the discount offered; the offer rate, the revenue recovered when it filled and the revenue missed when it did not fill in by themselves.', [
        C('gap_id', 'Gap ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), REF('unit', 'Unit', 'units.name', 26), C('nights_free', 'Nights free', 'int', 9), C('usual_rate', 'Usual rate', 'money', 11),
        C('discount_pct', 'Discount offered', 'pct', 10), LST('filled', 'Filled', 'yn', 8),
        CA('offer_rate', 'Offer rate', 'money', 'ROUND({col:usual_rate}*(1-{col:discount_pct}),0)', 10), CA('recovered', 'Revenue recovered', 'money', 'IF({col:filled}=%s,{col:nights_free}*ROUND({col:usual_rate}*(1-{col:discount_pct}),0),0)' % YES, 12),
        CA('missed', 'Revenue missed', 'money', 'IF(AND({col:filled}<>%s,{col:date}<{today}),{col:nights_free}*{col:usual_rate},0)' % YES, 12),
        CA('status', 'Gap status', 'text', 'IF({col:filled}=%s,%s,IF({col:date}<{today},%s,%s))' % (YES, ca('Filled'), ca('Missed'), ca('Open')), 11), COH()],
      D.gaps_d(), 300, [A('status', '= ' + ca('Missed'), 'warn'), A('status', '= ' + ca('Filled'), 'good'), A('status', '= ' + ca('Open'), 'bad')]),
    T('lastmin', 'Last-Minute Fills', 'Last-minute fills with discount and revenue',
      'One row per booking made close to check-in: unit, usual and booked rate, nights and channel; the discount given, the revenue and how late the fill was fill in by themselves.', [
        C('lm_id', 'Fill ID', 'text', 9, required=True), REF('unit', 'Unit', 'units.name', 26), C('check_in', 'Check-in', 'date', 11), C('days_before', 'Days before check-in', 'int', 10), C('nights', 'Nights', 'int', 8),
        C('usual_rate', 'Usual rate', 'money', 11), C('rate', 'Rate', 'money', 10), LST('channel', 'Channel', 'chan', 11),
        CA('discount_pct', 'Discount given', 'pct', 'IF({col:usual_rate}>0,1-{col:rate}/{col:usual_rate},0)', 10), CA('revenue', 'Revenue', 'money', '{col:rate}*{col:nights}', 11),
        CA('fill_flag', 'Fill timing', 'text', 'IF({col:days_before}<=1,%s,IF({col:days_before}<={set:lastmin_days},%s,%s))' % (cb('Very late fill'), cb('Late fill'), cb('Early fill')), 13), COH()],
      D.lastmin_d(), 200),
    T('clean_fee', 'Cleaning Fee Review', 'Cleaning fee review with margin on the fee',
      'One row per unit: cleaner hours, supplies and linen for one turnover (the clean and reset between two stays); the fee charged, the cost, the margin on the fee and the fee that reaches your margin target fill in by themselves.', [
        REF('unit', 'Unit', 'units.name', 26, required=True), LST('unit_type', 'Unit type', 'utype', 11), C('cleaner_hours', 'Cleaner hours', 'num', 9), C('supplies', 'Supplies', 'money', 10), C('linen_cost', 'Linen', 'money', 10),
        C('review_on', 'Reviewed on', 'date', 11),
        CA('fee', 'Cleaning fee charged', 'money', LKN('units.cleaning_fee', 'units.name', 'unit'), 11), CA('cleaner_cost', 'Cleaner cost', 'money', '{col:cleaner_hours}*{set:cleaner_rate}', 10),
        CA('cost_total', 'Total cost', 'money', '{col:cleaner_hours}*{set:cleaner_rate}+{col:supplies}+{col:linen_cost}', 10), CA('margin', 'Margin on the fee', 'money', '{col:fee}-{col:cleaner_hours}*{set:cleaner_rate}-{col:supplies}-{col:linen_cost}', 11),
        CA('margin_pct', 'Margin percent', 'pct', 'IF({col:fee}>0,({col:fee}-{col:cleaner_hours}*{set:cleaner_rate}-{col:supplies}-{col:linen_cost})/{col:fee},0)', 10),
        CA('margin_flag', 'Margin check', 'text', 'IF({col:margin_pct}>={set:fee_margin_target},%s,%s)' % (ca('Margin on target'), ca('Margin too thin')), 14),
        CA('suggested_fee', 'Fee for the margin target', 'money', 'ROUND(({col:cleaner_hours}*{set:cleaner_rate}+{col:supplies}+{col:linen_cost})/(1-{set:fee_margin_target}),0)', 12), OWNP()],
      D.clean_fee_d(), 50, [A('margin_flag', '= ' + ca('Margin too thin'), 'warn')]),
    T('channels', 'Channels', 'Channels with platform fee and payout days',
      'Booking platforms and direct routes with the fee and the days to the payout (the money a platform sends the host after a stay starts); the booking and break-even sheets read these.', [
        C('channel', 'Channel', 'text', 24, required=True), C('fee_pct', 'Platform fee', 'pct', 11), C('payout_days', 'Payout days after check-in', 'int', 13)],
      D.channels_d(), 50),
    T('cities', 'Cities', 'City and season rates with local occupancy tax',
      'One row per city and season: local occupancy tax (a tax on each night, collected from the guest) and a demand factor; the ADR and occupancy of your units there fill in by themselves.', [
        LST('city', 'City', 'city', 10, required=True), LST('season', 'Season', 'season', 11), C('tax_pct', 'Local tax share', 'pct', 11), C('demand_factor', 'Demand factor', 'num', 10),
        CA('adr', 'ADR of the units', 'money', 'IFERROR(AVERAGEIFS({range:unit_months.adr},{range:unit_months.city},{col:city},{range:unit_months.season},{col:season},{range:unit_months.booked_nights},">0"),0)', 11),
        CA('occ', 'Occupancy of the units', 'pct', 'IFERROR(AVERAGEIFS({range:unit_months.occupancy},{range:unit_months.city},{col:city},{range:unit_months.season},{col:season}),0)', 11),
        CA('tax_night', 'Local tax on an ADR night', 'money', '{col:adr}*{col:tax_pct}', 11)],
      D.cities_d(), 50, [A('occ', '< 0.4', 'warn')]),
    T('breakeven', 'Break-Even Rates', 'Break-even rate and occupancy for each unit',
      'One row per unit: other fixed costs, variable cost per night and your target occupancy; the fixed cost, the break-even nightly rate after platform fees, the margin against the base rate and the occupancy needed fill in by themselves.', [
        REF('unit', 'Unit', 'units.name', 26, required=True), C('other_fixed', 'Other fixed cost per month', 'money', 12), C('var_per_night', 'Variable cost per night', 'money', 11), C('target_occ', 'Target occupancy', 'pct', 10),
        C('review_on', 'Reviewed on', 'date', 11),
        CA('fixed_monthly', 'Fixed cost per month', 'money', LKN('units.rent', 'units.name', 'unit') + '+' + LKN('units.utilities', 'units.name', 'unit') + '+' + LKN('units.internet', 'units.name', 'unit') + '+{col:other_fixed}', 12),
        CA('break_even_rate', 'Break-even rate', 'money', 'ROUND((({col:fixed_monthly})/(30.4*{col:target_occ})+{col:var_per_night})/(1-AVERAGE({range:channels.fee_pct})),0)', 11),
        CA('base_rate', 'Base rate', 'money', LKN('units.base_rate', 'units.name', 'unit'), 10), CA('margin_per_night', 'Base rate less break-even', 'money', '{col:base_rate}-ROUND((({col:fixed_monthly})/(30.4*{col:target_occ})+{col:var_per_night})/(1-AVERAGE({range:channels.fee_pct})),0)', 12),
        CA('rate_flag', 'Break-even check', 'text', 'IF({col:base_rate}>={col:break_even_rate},%s,%s)' % (ca('Above break-even'), ca('Below break-even')), 16),
        CA('occ_needed', 'Occupancy needed at the base rate', 'pct', 'IF({col:base_rate}*(1-AVERAGE({range:channels.fee_pct}))-{col:var_per_night}>0,{col:fixed_monthly}/(({col:base_rate}*(1-AVERAGE({range:channels.fee_pct}))-{col:var_per_night})*30.4),0)', 13), OWNP()],
      D.breakeven_d(), 50, [A('rate_flag', '= ' + ca('Below break-even'), 'bad')]),
    T('direct_offers', 'Direct Offers', 'Direct offers with bookings and revenue',
      'One row per direct booking offer code: unit, discount, the dates it is valid and the bookings and revenue it brought; whether it is active, the revenue per booking and the days left fill in by themselves.', [
        C('offer_id', 'Offer ID', 'text', 9, required=True), C('code', 'Code', 'text', 20), REF('unit', 'Unit', 'units.name', 26), C('discount_pct', 'Discount', 'pct', 9), C('valid_from', 'Valid from', 'date', 11),
        C('valid_until', 'Valid until', 'date', 11), C('bookings', 'Bookings', 'int', 9), C('revenue', 'Revenue', 'money', 12),
        CA('status', 'Offer status', 'text', 'IF({col:valid_until}<{today},%s,IF({col:valid_from}>{today},%s,%s))' % (ca('Offer ended'), ca('Offer not started'), ca('Offer active')), 15),
        CA('rev_per_booking', 'Revenue per booking', 'money', 'IF({col:bookings}>0,{col:revenue}/{col:bookings},0)', 12), CA('days_left', 'Days left', 'int', 'IF({col:valid_until}>={today},{col:valid_until}-{today},0)', 9), OWNP()],
      D.direct_offers_d(), 120, [A('status', '= ' + ca('Offer active'), 'good'), A('bookings', '= 0', 'warn')]),
    T('experiments', 'Price Experiments', 'Price experiments with result',
      'One row per price test: unit, start date, weeks, the rate before and the rate tested, the nights booked and the result; the change percent, the occupancy during the test and the revenue per week fill in by themselves.', [
        C('ex_id', 'Test ID', 'text', 9, required=True), REF('unit', 'Unit', 'units.name', 26), C('start_date', 'Start', 'date', 11), C('weeks', 'Weeks', 'int', 8), C('rate_before', 'Rate before', 'money', 10),
        C('rate_tested', 'Rate tested', 'money', 10), C('nights_booked', 'Nights booked', 'int', 10), LST('result', 'Result', 'expres', 16),
        CA('change_pct', 'Rate change', 'pct', 'IF({col:rate_before}>0,{col:rate_tested}/{col:rate_before}-1,0)', 10), CA('occ_test', 'Occupancy in the test', 'pct', 'IF({col:weeks}>0,MIN(1,{col:nights_booked}/({col:weeks}*7)),0)', 11),
        CA('revenue_test', 'Revenue in the test', 'money', '{col:rate_tested}*{col:nights_booked}', 11), CA('rev_week', 'Revenue per week', 'money', 'IF({col:weeks}>0,{col:rate_tested}*{col:nights_booked}/{col:weeks},0)', 11),
        CA('test_flag', 'Test check', 'text', 'IF({col:result}=%s,%s,%s)' % (tok('expres', 'Running'), ca('Test running'), ca('Test ended')), 13), OWNP()],
      D.experiments_d(), 80, [A('test_flag', '= ' + ca('Test running'), 'warn'), A('result', '= ' + tok('expres', 'Rate worked'), 'good')]),
    T('weekday', 'Weekday Pattern', 'Check-in weekday pattern by unit',
      'One row per unit and check-in weekday over the last 12 months: nights booked and ADR (the average price of a night sold); the share of nights, the premium against the unit average and the weekend lift check fill in by themselves.', [
        C('wd_id', 'Row ID', 'text', 9, required=True), REF('unit', 'Unit', 'units.name', 26), LST('weekday', 'Check-in weekday', 'wday', 14), C('booked_nights', 'Booked nights', 'int', 10), C('adr', 'ADR at season factor 1', 'money', 12),
        CA('unit_nights', 'Unit nights', 'int', 'SUMIFS({range:weekday.booked_nights},{range:weekday.unit},{col:unit})', 9),
        CA('share_nights', 'Share of nights', 'pct', 'IF(SUMIFS({range:weekday.booked_nights},{range:weekday.unit},{col:unit})>0,{col:booked_nights}/SUMIFS({range:weekday.booked_nights},{range:weekday.unit},{col:unit}),0)', 10),
        CA('premium', 'Premium against unit average', 'pct', 'IFERROR({col:adr}/AVERAGEIFS({range:weekday.adr},{range:weekday.unit},{col:unit})-1,0)', 12),
        CA('day_flag', 'Day check', 'text', 'IF({col:share_nights}>=1.25/7,%s,IF({col:share_nights}<=0.75/7,%s,%s))' % (cb('Busy check-in day'), cb('Quiet check-in day'), cb('Normal check-in day')), 16),
        CA('lift_flag', 'Weekend lift check', 'text', 'IF(OR({col:weekday}=%s,{col:weekday}=%s),IF({col:premium}>0,%s,%s),%s)' % (tok('wday', 'Friday'), tok('wday', 'Saturday'), ca('Lift achieved'), ca('Lift missed'), ca('Not a weekend')), 16)],
      D.weekday_d(), 120, [A('lift_flag', '= ' + ca('Lift missed'), 'warn'), A('lift_flag', '= ' + ca('Lift achieved'), 'good')]),
    T('team', 'Team', 'Team with hours and rate changes made',
      'The host, the co-host (a helper who handles guests for a fee), four cleaners, two handypeople and four outside contacts; the rate changes each person made fill in by themselves.', [
        C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 14), LST('team', 'Team', 'team', 12), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
        C('hours_week', 'Hours a week', 'int', 10), C('hourly_rate', 'Hourly rate', 'money', 10), C('speciality', 'Speciality', 'text', 26), C('country', 'Country', 'text', 14), C('start', 'Start', 'date', 11),
        CA('rate_changes', 'Rate changes made', 'int', 'COUNTIFS({range:rate_changes.changed_by},{col:name})', 10),
        CA('changes_90d', 'Rate changes, 90 days', 'int', 'COUNTIFS({range:rate_changes.changed_by},{col:name},{range:rate_changes.date},">="&({today}-90))', 11)],
      D.team_d(), 50),
]
assert len(tables) == 20, len(tables)

HINTS = {
 'units': 'One row per unit with rates and fixed costs; nights, revenue, ADR (the average price of a night sold), occupancy, break-even rate and rate card figures fill in by themselves.',
 'pricing': 'One row per unit and week: base rate, season, demand, local event, listed rate, booked and free nights; the suggested rate, gap to it and fill check fill in by themselves.',
 'bookings': 'One row per booking: unit, guest, channel, dates, nightly rate and revenue; lead time, rate against base, platform fee and guest offer prices fill in by themselves.',
 'unit_months': 'One row per unit and month: available and booked nights and room revenue; occupancy, ADR, RevPAR (revenue per available night) and the gap to your target fill in by themselves.',
 'discounts': 'One row per discount rule: trigger, units covered, days before check-in, percent off and minimum nights; the example price and the rule check fill in by themselves.',
 'minstay': 'One row per unit and season: the shortest stay on weekdays, weekends and for a gap; the strictest rule, gap check and review check fill in by themselves.',
 'gaps': 'One row per free night between two bookings: unit, usual rate and discount offered; the offer rate, revenue recovered and revenue missed fill in by themselves.',
 'clean_fee': 'One row per unit: cleaner hours, supplies and linen for one turnover (the clean and reset between stays); cost, margin on the fee and the fee for your target fill in by themselves.',
 'breakeven': 'One row per unit: other fixed cost, cost per night and target occupancy; fixed cost, break-even rate after platform fees, margin and occupancy needed fill in by themselves.',
 'direct_offers': 'One row per direct offer code: unit, discount, valid dates, bookings and revenue; the offer status, revenue per booking and days left fill in by themselves.',
 'experiments': 'One row per price test: unit, start, weeks, rate before and tested, nights booked and result; change percent, occupancy and revenue per week fill in by themselves.',
 'weekday': 'One row per unit and check-in weekday over 12 months: nights and ADR with the season taken out; share of nights, premium and the weekend lift check fill in by themselves.',
}
for _t in tables:
    if _t['key'] in HINTS: _t['hint'] = HINTS[_t['key']]
    assert len(_t['hint']) <= 200, (_t['key'], len(_t['hint']))
