"""Short-term rental host suite - part 3: Occupancy, ADR and RevPAR."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr3_lists import *
from sr3_tables import settings, tables
from sr3_tools import tools

SUITE = 'fx-20261113-short-term-rental'
NOTE = "Sample wording: adapt it to your own practice and check your own local rules."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def PK(t, c, k): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, k)
forms = [
    FORM('unit_review', 'Unit Review Sheet', 'Unit review with results, ranks and checks', 'units.unit_id', F(
        ('Name', 'units.name'), ('Unit type', 'units.unit_type'), ('City', 'units.city'), ('Owner', 'units.owner'), ('Base rate', 'units.base_rate'), ('Target occupancy', 'units.target_occ'), ('Occupancy, 12 months', 'units.occ_12m'),
        ('Occupancy check', 'units.occ_flag'), ('Target ADR', 'units.target_adr'), ('ADR, 12 months', 'units.adr_12m'), ('ADR check', 'units.adr_flag'), ('RevPAR, 12 months', 'units.revpar_12m'), ('Occupancy this month', 'units.occ_month'),
        ('RevPAR rank this month', 'units.rank_month'), ('Rating, 90 days', 'units.rating_90d'), ('Unit health', 'units.unit_flag')) + [
        FF('Occupancy points against target', PK('units', 'occ_12m', 'unit_id') + '-' + PK('units', 'target_occ', 'unit_id'), 'pct'), FF('Units in the portfolio', 'COUNTA({range:units.unit_id})', 'int')]),
    FORM('target_sheet', 'Target Setting Sheet', 'Targets of a unit with the result against them', 'targets.unit', F(
        ('Set on', 'targets.set_on'), ('Target occupancy', 'targets.target_occ'), ('Target ADR', 'targets.target_adr'), ('Target RevPAR', 'targets.target_revpar'), ('Yearly revenue goal', 'targets.goal_year'), ('Room revenue, 12 months', 'targets.revenue_12m'),
        ('Occupancy, 12 months', 'targets.occ_12m'), ('Occupancy check', 'targets.occ_flag'), ('ADR, 12 months', 'targets.adr_12m'), ('ADR check', 'targets.adr_flag'), ('RevPAR, 12 months', 'targets.revpar_12m'),
        ('RevPAR check', 'targets.revpar_flag'), ('Share of the goal', 'targets.goal_pct'), ('Goal check', 'targets.goal_flag')) + [
        FF('Revenue still to earn for the goal', 'MAX(0,' + PK('targets', 'goal_year', 'unit') + '-' + PK('targets', 'revenue_12m', 'unit') + ')', 'money')]),
    FORM('blocked_sheet', 'Blocked Nights Sheet', 'Blocked period with the revenue it cost', 'blocked.block_id', F(
        ('Unit', 'blocked.unit'), ('From', 'blocked.from_date'), ('To', 'blocked.to_date'), ('Reason', 'blocked.reason'), ('Nights blocked', 'blocked.nights'), ('Unit ADR, 12 months', 'blocked.adr_12m'), ('Unit occupancy, 12 months', 'blocked.occ_12m'),
        ('Estimated revenue lost', 'blocked.lost_revenue'), ('Length check', 'blocked.block_flag'), ('Block status', 'blocked.block_status'), ('Co-host phone', 'blocked.cohost_phone'))),
    FORM('pace_sheet', 'Pace Check Sheet', 'Pace of one unit and month against the target', 'pace.pace_id', F(
        ('Month', 'pace.month'), ('Unit', 'pace.unit'), ('Available nights', 'pace.available_nights'), ('Booked a month ago', 'pace.booked_ago'), ('Booked now', 'pace.booked_now'), ('Target nights now', 'pace.target_nights'), ('Nights picked up', 'pace.pickup'),
        ('Pace gap', 'pace.gap'), ('Gap percent', 'pace.gap_pct'), ('Occupancy on the books', 'pace.occ_books'), ('Open nights', 'pace.open_nights'), ('Pace check', 'pace.pace_flag'), ('Suggested price move', 'pace.price_move'))),
    FORM('weak_sheet', 'Weak Unit Action Sheet', 'Finding and action on a unit, with owner', 'perf_reviews.pr_id', F(
        ('Date', 'perf_reviews.date'), ('Unit', 'perf_reviews.unit'), ('Finding', 'perf_reviews.finding'), ('Action', 'perf_reviews.action'), ('Action owner', 'perf_reviews.owner'), ('Due date', 'perf_reviews.due_date'), ('Done on', 'perf_reviews.done_on'),
        ('Status', 'perf_reviews.status'), ('Days to the due date', 'perf_reviews.days_to_due'), ('Unit occupancy, 12 months', 'perf_reviews.occ_12m'))),
    FORM('market_sheet', 'Market Check Sheet', 'Our results against the market, city and month', 'market.mk_id', F(
        ('Month', 'market.month'), ('City', 'market.city'), ('Market occupancy', 'market.market_occupancy'), ('Our occupancy', 'market.our_occupancy'), ('Occupancy index', 'market.occ_index'), ('Occupancy check', 'market.occ_flag'),
        ('Market ADR', 'market.market_adr'), ('Our ADR', 'market.our_adr'), ('ADR index', 'market.adr_index'), ('ADR check', 'market.adr_flag')) + [
        FF('RevPAR against the market, index', 'IFERROR(' + PK('market', 'occ_index', 'mk_id') + '*' + PK('market', 'adr_index', 'mk_id') + ',0)', 'num')]),
    FORM('season_sheet', 'Season Plan Sheet', 'Season of a month with the rate it brings', 'seasons.month', F(('Season', 'seasons.season'), ('Price factor', 'seasons.price_factor'), ('Host phone', 'seasons.host_phone')) + [
        FF('Average base rate of the units', 'AVERAGE({range:units.base_rate})', 'money'), FF('Average weekday rate in this month', 'ROUND(AVERAGE({range:units.base_rate})*' + PK('seasons', 'price_factor', 'month') + ',0)', 'money'),
        FF('Average weekend rate in this month', 'ROUND(AVERAGE({range:units.base_rate})*' + PK('seasons', 'price_factor', 'month') + '*(1+{set:weekend_lift}),0)', 'money'),
        FF('Months of the year in this season', 'COUNTIFS({range:seasons.season},' + PK('seasons', 'season', 'month') + ')', 'int'), FF('Wanted occupancy', '{set:target_occupancy}', 'pct')]),
    FORM('orphan_sheet', 'Orphan Night Sheet', 'Free night between two bookings with the revenue', 'orphan.orphan_id', F(
        ('Date', 'orphan.date'), ('Unit', 'orphan.unit'), ('Gap length, nights', 'orphan.gap_length'), ('Filled', 'orphan.filled'), ('Revenue recovered', 'orphan.revenue_recovered'), ('Unit ADR, 12 months', 'orphan.adr_12m'),
        ('Revenue missed', 'orphan.missed'), ('Fill check', 'orphan.fill_flag'), ('Co-host phone', 'orphan.cohost_phone'))),
    FORM('owner_sheet', 'Owner Performance Sheet', 'Owner view of one unit over 12 months and 3 months', 'units.unit_id', F(
        ('Owner', 'units.owner'), ('Owner phone', 'units.owner_phone'), ('Name', 'units.name'), ('Room revenue, 12 months', 'units.revenue_12m'), ('Room revenue, last 3 months', 'units.revenue_q'), ('ADR, 12 months', 'units.adr_12m'), ('ADR, last 3 months', 'units.adr_q'),
        ('Occupancy, 12 months', 'units.occ_12m'), ('Occupancy this month', 'units.occ_month'), ('Rating, 90 days', 'units.rating_90d'), ('Rating check', 'units.rating_flag'), ('Unit health', 'units.unit_flag')) + [
        FF('Share of all room revenue', 'IFERROR(' + PK('units', 'revenue_12m', 'unit_id') + '/SUM({range:units.revenue_12m}),0)', 'pct')]),
    FORM('quarter_sheet', 'Quarter Review Sheet', 'City month results for the quarter review', 'city_months.cm_id', F(
        ('Month', 'city_months.month'), ('City', 'city_months.city'), ('Available nights', 'city_months.available_nights'), ('Booked nights', 'city_months.booked_nights'), ('Room revenue', 'city_months.room_revenue'),
        ('Occupancy', 'city_months.occupancy'), ('ADR', 'city_months.adr'), ('RevPAR', 'city_months.revpar')) + [
        FF('Share of the revenue of all cities', 'IFERROR(' + PK('city_months', 'room_revenue', 'cm_id') + '/SUMIFS({range:city_months.room_revenue},{range:city_months.month},' + PK('city_months', 'month', 'cm_id') + '),0)', 'pct')]),
]
assert len(forms) == 10
documents = [
    DOC('monthly_report', 'Monthly Performance Report', 'Monthly performance report for one unit', 'unit_months.um_id', [
        'Monthly performance report of {set:company}, dated {today}. Unit: {col:unit_months.unit} in {col:unit_months.city}, month starting {col:unit_months.month} ({col:unit_months.season} season).',
        'Nights available: {col:unit_months.available_nights}. Nights sold: {col:unit_months.booked_nights}. Room revenue: {col:unit_months.room_revenue}.',
        'Occupancy: {col:unit_months.occupancy} against a target of {col:unit_months.target_occ} ({col:unit_months.occ_flag}). ADR, the average price of a night sold: {col:unit_months.adr}. RevPAR, revenue per available night: {col:unit_months.revpar}.',
        'Notes on the month and the actions for the next month are written below.'], ['Host', 'Owner'], NOTE),
    DOC('unit_summary', 'Unit Performance Summary', 'Performance summary of one unit', 'units.unit_id', [
        'Unit performance summary of {set:company}, dated {today}. Unit {col:units.unit_id}: {col:units.name}, a {col:units.unit_type} in {col:units.city} with {col:units.bedrooms} bedrooms. Owner: {col:units.owner}.',
        'Last 12 months: {col:units.nights_12m} nights sold of {col:units.avail_12m} available, occupancy {col:units.occ_12m} against a target of {col:units.target_occ} ({col:units.occ_flag}).',
        'ADR {col:units.adr_12m} against a target of {col:units.target_adr} ({col:units.adr_flag}). RevPAR {col:units.revpar_12m}. Room revenue {col:units.revenue_12m}.',
        'This month: occupancy {col:units.occ_month}, RevPAR {col:units.revpar_month}, rank {col:units.rank_month} of the units. Review rating of the last 90 days: {col:units.rating_90d} ({col:units.rating_flag}). Unit health: {col:units.unit_flag}.'], ['Host', 'Owner'], NOTE),
    DOC('owner_letter', 'Owner Performance Letter', 'Performance letter to the owner of a unit', 'units.unit_id', [
        'Letter of {set:company} to {col:units.owner}, dated {today}. Subject: performance of {col:units.name}.',
        'Over the last 12 months your unit sold {col:units.nights_12m} nights at an ADR of {col:units.adr_12m}, which is occupancy of {col:units.occ_12m} and room revenue of {col:units.revenue_12m}.',
        'In the last three months the ADR was {col:units.adr_q} and the room revenue {col:units.revenue_q}. This month the occupancy is {col:units.occ_month}.',
        'Our targets for the unit are occupancy of {col:units.target_occ} and an ADR of {col:units.target_adr}. We will tell you before we change the rates or block nights.'], ['Host', 'Owner'], NOTE),
    DOC('season_doc', 'Season Plan', 'Season plan for one month', 'seasons.month', [
        'Season plan of {set:company}, dated {today}. Month starting {col:seasons.month}: season {col:seasons.season}, price factor {col:seasons.price_factor}.',
        'Wanted occupancy: {set:target_occupancy}. Wanted ADR: {set:target_adr}. Weekend lift: {set:weekend_lift}.',
        'Before the month starts: check the base rates, the minimum stays and the blocked nights, brief the co-host and the cleaners, and tell the owners about the plan.', 'The results of the month are compared with this plan at the monthly review.'], ['Host', 'Co-host'], NOTE),
    DOC('pace_doc', 'Pace Report Next 3 Months', 'Pace report for one unit and month ahead', 'pace.pace_id', [
        'Pace report of {set:company}, dated {today}. Unit: {col:pace.unit}. Month starting {col:pace.month}.',
        'Available nights: {col:pace.available_nights}. Booked a month ago: {col:pace.booked_ago}. Booked now: {col:pace.booked_now}. Picked up in a month: {col:pace.pickup}. Target nights now: {col:pace.target_nights}.',
        'Pace gap: {col:pace.gap} nights, {col:pace.gap_pct}. Pace check: {col:pace.pace_flag}. Occupancy on the books: {col:pace.occ_books}. Open nights: {col:pace.open_nights}.',
        'Suggested price move: {col:pace.price_move}. The decision and the date of the next check are written below.'], ['Host', 'Co-host'], NOTE),
    DOC('weak_plan', 'Weak Unit Action Plan', 'Action plan for a weak unit', 'perf_reviews.pr_id', [
        'Action plan of {set:company}, dated {today}. Review {col:perf_reviews.pr_id} of {col:perf_reviews.date} for {col:perf_reviews.unit}.',
        'Finding: {col:perf_reviews.finding}. Action: {col:perf_reviews.action}. Owner of the action: {col:perf_reviews.owner}. Due date: {col:perf_reviews.due_date}. Status: {col:perf_reviews.status}.',
        'The occupancy of the unit over 12 months is {col:perf_reviews.occ_12m}. The action is checked at the next monthly review and the owner of the unit is told what changed.', 'Result of the action and the date it was done are written below.'], ['Host', 'Owner'], NOTE),
    DOC('yoy_doc', 'Year-on-Year Report', 'Year-on-year report for one unit and month', 'yoy.yy_id', [
        'Year-on-year report of {set:company}, dated {today}. Unit: {col:yoy.unit}. Month starting {col:yoy.month}.',
        'Nights sold: {col:yoy.nights_this} this year against {col:yoy.nights_last} a year earlier, a change of {col:yoy.nights_change}. Room revenue: {col:yoy.revenue_this} against {col:yoy.revenue_last}, a change of {col:yoy.change_pct}.',
        'ADR: {col:yoy.adr_this} against {col:yoy.adr_last}, a change of {col:yoy.adr_change}. Trend: {col:yoy.trend}.', 'Causes of the change and the actions for the next year are written below.'], ['Host', 'Owner'], NOTE),
    DOC('market_doc', 'Market Comparison Report', 'Market comparison for a city and month', 'market.mk_id', [
        'Market comparison of {set:company}, dated {today}. City: {col:market.city}. Month starting {col:market.month}.',
        'Market occupancy {col:market.market_occupancy}, our occupancy {col:market.our_occupancy}, index {col:market.occ_index} ({col:market.occ_flag}).',
        'Market ADR {col:market.market_adr}, our ADR {col:market.our_adr}, index {col:market.adr_index} ({col:market.adr_flag}).', 'The market figures come from our own checks of comparable listings. Actions on our rates are written below.'], ['Host'], NOTE),
    DOC('yearly_review', 'Yearly Review', 'Yearly review of one unit against its goal', 'targets.unit', [
        'Yearly review of {set:company}, dated {today}. Unit: {col:targets.unit}. Targets set on {col:targets.set_on}.',
        'Room revenue of the last 12 months: {col:targets.revenue_12m} against a goal of {col:targets.goal_year}, which is {col:targets.goal_pct} of the goal ({col:targets.goal_flag}).',
        'Occupancy {col:targets.occ_12m} against {col:targets.target_occ} ({col:targets.occ_flag}). ADR {col:targets.adr_12m} against {col:targets.target_adr} ({col:targets.adr_flag}). RevPAR {col:targets.revpar_12m} against {col:targets.target_revpar} ({col:targets.revpar_flag}).',
        'Targets for the next year are written below.'], ['Host', 'Owner'], NOTE),
    DOC('target_doc', 'Target Sheet by Unit', 'Target sheet for one unit', 'targets.unit', [
        'Target sheet of {set:company}, dated {today}. Unit: {col:targets.unit}.', 'Wanted occupancy: {col:targets.target_occ}. Wanted ADR: {col:targets.target_adr}. Wanted RevPAR: {col:targets.target_revpar}. Yearly revenue goal: {col:targets.goal_year}.',
        'Targets are reviewed every quarter. They are agreed with the owner of the unit and written in the targets sheet with the date.', 'Agreed on the date below.'], ['Host', 'Owner'], NOTE),
]
assert len(documents) == 10
checklists = [
    CHK('monthly_run', 'Monthly Performance Review', 'unit_months', 'unit_months.month', [('Close the month: check nights, blocked nights and revenue of every unit', 31), ('Check occupancy, ADR and RevPAR against the targets', 32), ('Rank the units and note the best and the weakest', 33),
        ('Compare the month with last year', 34), ('Check the market comparison for each city', 35), ('Write findings and actions in the performance reviews', 36), ('Send the monthly report to the owners', 38)]),
    CHK('weak_run', 'Weak Unit Review Steps', 'perf_reviews', 'perf_reviews.date', [('Read the occupancy, ADR and rating of the unit', 0), ('Check the rate against comparable listings', 1), ('Check the reviews of the last 90 days', 2), ('Check the weekday and weekend nights', 3),
        ('Choose one action and its owner', 4), ('Tell the owner of the unit', 5), ('Check the result after 30 days', 30)]),
    CHK('pace_run', 'Pace Check Steps', 'pace', 'pace.month', [('Count the nights booked for the next three months', -60), ('Compare them with the nights booked a month ago', -59), ('Compare them with the target for each unit', -58), ('Flag the units behind pace', -57),
        ('Move the rate of the units behind pace', -56), ('Ask the co-host to answer enquiries the same day', -55), ('Check the pace again after two weeks', -45)]),
    CHK('season_run', 'Season Change Steps', 'seasons', 'seasons.month', [('Check the price factor of the new season', -21), ('Update the base rates and the weekend lift', -14), ('Check the minimum stays', -14), ('Open the dates for the new season', -10), ('Tell the co-host, the cleaners and the owners', -7),
        ('Book extra turnovers for the busy weeks', -7), ('Review the first week of bookings at the new rates', 7)]),
    CHK('block_run', 'Blocked Nights Review Steps', 'blocked', 'blocked.from_date', [('Confirm the reason with the owner or the handyperson', -7), ('Check the cost of the blocked nights', -7), ('Move the work to a quiet week if you can', -5), ('Block the nights in every calendar', -3),
        ('Tell the co-host and the cleaner', -3), ('Reopen the nights when the work ends', 0)]),
    CHK('orphan_run', 'Orphan Night Check Steps', 'orphan', 'orphan.date', [('List the free nights between two bookings', -14), ('Relax the minimum stay for the gap', -10), ('Offer a gap discount to guests nearby', -7), ('Lower the rate for the gap', -5), ('Ask the co-host to follow up', -3), ('Record if the gap was filled', 1)]),
    CHK('target_run', 'Target Setting Steps', 'targets', 'targets.set_on', [('Collect the results of the last 12 months', 0), ('Check the market occupancy and ADR', 1), ('Set the wanted occupancy and ADR for each unit', 3), ('Work out the yearly revenue goal', 4),
        ('Agree the targets with the owner', 7), ('Write the targets in the sheet', 8), ('Review the targets every quarter', 90)]),
    CHK('market_run', 'Market Check Steps', 'market', 'market.month', [('Open the comparable listings in each city', 20), ('Note their occupancy and rate', 21), ('Write the market figures in the sheet', 22), ('Check our indexes', 23), ('Choose the units to reprice', 24), ('Tell the owners', 26)]),
    CHK('quarter_run', 'Quarter Review Steps', 'review_scores', 'review_scores.month', [('Collect the results of the quarter', 30), ('Compare occupancy, ADR and RevPAR with the targets', 31), ('Check the review scores of every unit', 32), ('Check the blocked nights and the orphan nights', 33),
        ('Decide the actions for the next quarter', 35), ('Send the quarter report to the owners', 37)]),
    CHK('year_run', 'Year-End Review Steps', 'units', 'units.since', [('List the nights, revenue, ADR and RevPAR of each unit', 365), ('Compare the year with the targets and with last year', 366), ('Find the best and the weakest units', 367), ('Review the seasons and the price factors', 370),
        ('Set the targets for the new year', 375), ('Send the yearly review to the owners and the accountant', 380)]),
]
assert len(checklists) == 10
def M(key_, moment, table, phone, text): return MSG(key_, moment, table, phone, text)
messages = [
    M('o_occ', 'Owner: your unit occupancy this month', 'units', 'units.owner_phone', 'Hello {owner}, the occupancy of {name} this month is {occ_month} against a target of {target_occ}.'),
    M('o_report', 'Owner: your monthly report is ready', 'units', 'units.owner_phone', 'Hello {owner}, the monthly report for {name} is ready: occupancy {occ_month} this month, ADR {adr_q} over 3 months, RevPAR {revpar_month}.'),
    M('o_pace', 'Owner: your unit is behind pace', 'pace', 'pace.owner_phone', 'Hello, {unit} has {booked_now} nights booked for {month} against {target_nights} wanted by now. We are working on a plan.'),
    M('o_beat', 'Owner: your unit beat its target', 'targets', 'targets.owner_phone', 'Hello, {unit} beat its target: occupancy of {occ_12m} against {target_occ} and RevPAR of {revpar_12m} against {target_revpar}.'),
    M('o_adr', 'Owner: your average rate this quarter', 'units', 'units.owner_phone', 'Hello {owner}, the average rate of {name} over the last 3 months is {adr_q}, against {adr_12m} over 12 months.'),
    M('o_plan', 'Owner: a plan to lift occupancy', 'perf_reviews', 'perf_reviews.owner_phone', 'Hello, a plan to lift occupancy for {unit}: {action}. We will finish it by {due_date}.'),
    M('o_blocked', 'Owner: blocked nights cost revenue', 'blocked', 'blocked.owner_phone', 'Hello, {unit} is blocked from {from_date} to {to_date}, {nights} nights. The estimated revenue lost is {lost_revenue}.'),
    M('o_yearly', 'Owner: your yearly review is ready', 'targets', 'targets.owner_phone', 'Hello, the yearly review of {unit} is ready: room revenue {revenue_12m} against a goal of {goal_year}.'),
    M('o_market', 'Owner: market occupancy in your city', 'market', 'market.owner_phone', 'Hello, market occupancy in {city} for {month} is {market_occupancy} against our {our_occupancy}.'),
    M('o_rate', 'Owner: we suggest a rate change', 'units', 'units.owner_phone', 'Hello {owner}, we suggest a rate change for {name}: the ADR is {adr_12m} against a target of {target_adr}.'),
    M('c_fill', 'Co-host: fill the open nights this week', 'pace', 'pace.cohost_phone', 'Hello, {unit} still has {open_nights} open nights in {month}. Please fill them this week.'),
    M('c_cal', 'Co-host: block these nights', 'blocked', 'blocked.cohost_phone', 'Hello, please block {unit} in the calendar from {from_date} to {to_date}. Reason: {reason}.'),
    M('c_behind', 'Co-host: a unit is behind pace', 'pace', 'pace.cohost_phone', 'Hello, {unit} is behind pace for {month}: {booked_now} nights booked against {target_nights}.'),
    M('c_orphan', 'Co-host: orphan nights to fill', 'orphan', 'orphan.cohost_phone', 'Hello, there is a free gap of {gap_length} nights in {unit} on {date}. Please offer it to guests who stay nearby.'),
    M('h_weak', 'Host: a unit is the weakest this month', 'units', 'units.host_phone', 'Hello, {name} is ranked {rank_month} of the units for RevPAR this month at {revpar_month}. It needs attention.'),
    M('h_strong', 'Host: a unit is the strongest this month', 'units', 'units.host_phone', 'Hello, {name} is ranked {rank_month} of the units for RevPAR this month at {revpar_month}. Check what works there.'),
    M('h_next', 'Host: next month is behind target', 'pace', 'pace.host_phone', 'Hello, {unit} has {occ_books} occupancy on the books for {month} and {booked_now} nights against {target_nights} wanted by now.'),
    M('h_action', 'Host: a weak unit action is due', 'perf_reviews', 'perf_reviews.host_phone', 'Hello, the action for {unit} is due on {due_date}: {action}.'),
    M('h_quarter', 'Host: the quarter review is ready', 'units', 'units.host_phone', 'Hello, the quarter review of {name} is ready: room revenue {revenue_q}, ADR {adr_q}, occupancy {occ_12m}.'),
    M('h_adr', 'Host: ADR fell against last year', 'yoy', 'yoy.host_phone', 'Hello, for {unit} in {month} the ADR is {adr_this} against {adr_last} a year ago.'),
    M('h_weekday', 'Host: weekday occupancy is low', 'weekday', 'weekday.host_phone', 'Hello, {unit} has occupancy of {occupancy} on {weekday} nights over 12 months. Consider a midweek offer.'),
    M('h_block', 'Host: a unit is blocked for 10 nights', 'blocked', 'blocked.host_phone', 'Hello, {unit} is blocked for {nights} nights from {from_date}. Reason: {reason}.'),
    M('h_market', 'Host: market data updated', 'market', 'market.host_phone', 'Hello, market data for {city} in {month} was updated: market occupancy {market_occupancy}, market ADR {market_adr}.'),
    M('h_season', 'Host: the season starts', 'seasons', 'seasons.host_phone', 'Hello, the {season} season starts in {month}. The price factor is {price_factor}. Please check the rates.'),
    M('cl_busy', 'Cleaner: busy weeks are coming', 'pace', 'pace.cleaner_phone', 'Hello, busy weeks are coming in {unit}: {booked_now} nights are booked for {month}. Please keep your calendar free.'),
    M('hp_fix', 'Handyperson: fix before the high season', 'units', 'units.handy_phone', 'Hello, please check {name} before the high season. Its occupancy over 12 months is {occ_12m}, so every closed day costs revenue.'),
    M('a_year', 'Accountant: yearly performance attached', 'units', 'units.accountant_phone', 'Hello, the yearly performance of {name}: room revenue {revenue_12m}, ADR {adr_12m}, occupancy {occ_12m}.'),
    M('o_thanks', 'Owner: thank you for a good quarter', 'units', 'units.owner_phone', 'Hello {owner}, thank you for another good quarter. {name} earned {revenue_q} in room revenue over the last 3 months.'),
]
assert len(messages) == 28
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; NXT = 'DATE(YEAR({today}),MONTH({today})+1,1)'; N2 = 'DATE(YEAR({today}),MONTH({today})+2,1)'; PRV = 'DATE(YEAR({today}),MONTH({today})-1,1)'; Y1 = 'DATE(YEAR({today})-1,MONTH({today}),1)'
P60 = 'DATE(YEAR({today}+60),MONTH({today}+60),1)'; P60N = 'DATE(YEAR({today}+60),MONTH({today}+60)+1,1)'
def UMW(col, a, b): return 'SUMIFS({range:unit_months.%s},{range:unit_months.month},">="&%s,{range:unit_months.month},"<"&%s)' % (col, a, b)
def OCCW(a, b): return 'IFERROR(%s/%s,0)' % (UMW('booked_nights', a, b), UMW('available_nights', a, b))
def ADRW(a, b): return 'IFERROR(%s/%s,0)' % (UMW('room_revenue', a, b), UMW('booked_nights', a, b))
def RPW(a, b): return 'IFERROR(%s/%s,0)' % (UMW('room_revenue', a, b), UMW('available_nights', a, b))
def PCW(col, a, b): return 'SUMIFS({range:pace.%s},{range:pace.month},">="&%s,{range:pace.month},"<"&%s)' % (col, a, b)
def PCF(flag, a, b): return 'COUNTIFS({range:pace.month},">="&%s,{range:pace.month},"<"&%s,{range:pace.pace_flag},%s)' % (a, b, ca(flag))
def WDN(col, d): return 'SUMIFS({range:weekday.%s},{range:weekday.weekday},%s)' % (col, tok('wday', d))
WEB = WDN('booked_nights', 'Friday') + '+' + WDN('booked_nights', 'Saturday'); WEA = WDN('available_nights', 'Friday') + '+' + WDN('available_nights', 'Saturday')
kpis = [
    KPI('Occupancy this month', OCCW(MS, NXT), 'pct'), KPI('Occupancy last month', OCCW(PRV, MS), 'pct'), KPI('Occupancy, last 12 months', OCCW(Y1, MS), 'pct'),
    KPI('ADR this month', ADRW(MS, NXT), 'money'), KPI('ADR, last 12 months', ADRW(Y1, MS), 'money'), KPI('RevPAR this month', RPW(MS, NXT), 'money'), KPI('RevPAR, last 12 months', RPW(Y1, MS), 'money'),
    KPI('Room revenue this month', UMW('room_revenue', MS, NXT), 'money'), KPI('Room revenue, last 12 months', UMW('room_revenue', Y1, MS), 'money'),
    KPI('Nights sold this month', UMW('booked_nights', MS, NXT), 'int'), KPI('Available nights this month', UMW('available_nights', MS, NXT), 'int'),
    KPI('Blocked nights this month', 'SUMIFS({range:blocked.nights},{range:blocked.from_date},">="&%s,{range:blocked.from_date},"<"&%s)' % (MS, NXT), 'int'),
    KPI('Occupancy next month on the books', 'IFERROR(%s/%s,0)' % (PCW('booked_now', NXT, N2), PCW('available_nights', NXT, N2)), 'pct'),
    KPI('Occupancy in 60 days on the books', 'IFERROR(%s/%s,0)' % (PCW('booked_now', P60, P60N), PCW('available_nights', P60, P60N)), 'pct'),
    KPI('Units behind pace this month', PCF('Behind pace', MS, NXT), 'int'), KPI('Units ahead of pace this month', PCF('Ahead of pace', MS, NXT), 'int'),
    KPI('Best unit RevPAR, 12 months', 'MAX({range:units.revpar_12m})', 'money'), KPI('Weakest unit RevPAR, 12 months', 'MIN({range:units.revpar_12m})', 'money'),
    KPI('Units below target occupancy', 'COUNTIFS({range:units.occ_flag},%s)' % ca('Below target'), 'int'), KPI('Units below target ADR', 'COUNTIFS({range:units.adr_flag},%s)' % ca('Below target'), 'int'),
    KPI('Occupancy against market this month', 'IFERROR(AVERAGEIFS({range:market.occ_index},{range:market.month},">="&%s,{range:market.month},"<"&%s)-1,0)' % (MS, NXT), 'pct'),
    KPI('ADR against market this month', 'IFERROR(AVERAGEIFS({range:market.adr_index},{range:market.month},">="&%s,{range:market.month},"<"&%s)-1,0)' % (MS, NXT), 'pct'),
    KPI('Weekend occupancy, Friday and Saturday', 'IFERROR((%s)/(%s),0)' % (WEB, WEA), 'pct'),
    KPI('Weekday occupancy, other nights', 'IFERROR((SUM({range:weekday.booked_nights})-%s)/(SUM({range:weekday.available_nights})-%s),0)' % (WEB, WEA), 'pct'),
    KPI('Average lead time in days', 'IFERROR(AVERAGEIFS({range:bookings.lead_days},{range:bookings.status},"<>"&%s),0)' % tok('bstatus', 'Cancelled'), 'int'),
    KPI('Share of stays over 7 nights', 'IFERROR(SUMIFS({range:stay_mix.bookings},{range:stay_mix.stay_bucket},%s)/SUM({range:stay_mix.bookings}),0)' % tok('stay', 'Over seven nights'), 'pct'),
    KPI('Orphan nights filled this month', 'SUMIFS({range:orphan.gap_length},{range:orphan.filled},%s,{range:orphan.date},">="&%s,{range:orphan.date},"<="&{today})' % (tok('yn', 'Yes'), MS), 'int'),
    KPI('Revenue change against last year', 'IFERROR(SUM({range:yoy.revenue_this})/SUM({range:yoy.revenue_last})-1,0)', 'pct'),
    KPI('Units with a rating below the minimum', 'COUNTIFS({range:review_scores.month},">="&%s,{range:review_scores.month},"<"&%s,{range:review_scores.min_flag},%s)' % (MS, NXT, ca('Under minimum')), 'int'),
]
assert len(kpis) == 29, len(kpis)
dashboard = {"title": "Performance Dashboard", "kpis": kpis,
    "monthly": {"title": "Room revenue, blocked night loss and orphan night recovery", "date": "unit_months.month", "series": [
        {"label": "Room revenue by month", "sum": "unit_months.room_revenue", "date": "unit_months.month"}, {"label": "Revenue lost on blocked nights", "sum": "blocked.lost_revenue", "date": "blocked.from_date"},
        {"label": "Orphan night revenue recovered", "sum": "orphan.revenue_recovered", "date": "orphan.date"}]},
    "breakdowns": [{"title": "Room revenue by city", "by": "city_months.city", "value": "city_months.room_revenue", "agg": "sum"}, {"title": "Room revenue by unit type", "by": "type_months.unit_type", "value": "type_months.room_revenue", "agg": "sum"},
                   {"title": "Nights sold by channel", "by": "channel_mix.channel", "value": "channel_mix.nights", "agg": "sum"}, {"title": "Open nights ahead by unit", "by": "pace.unit", "value": "pace.open_nights", "agg": "sum"}]}
TD = ('month', '<=', '{today}')
insights = {"filters": [{"label": "Unit", "ref": "units.name"}, {"label": "City", "list": "city"}, {"label": "Channel", "list": "chan"}],
    "gauges": [{"title": "Occupancy this month", "num": AGG('sum', 'pace', 'pace.booked_now', where=[TD]), "den": AGG('sum', 'pace', 'pace.available_nights', where=[TD])},
               {"title": "Units at or above the target ADR", "num": AGG('count', 'targets', where=[('adr_flag', '<>', ca('Below target'))]), "den": AGG('count', 'targets')},
               {"title": "Units at or above the target RevPAR", "num": AGG('count', 'targets', where=[('revpar_flag', '<>', ca('Below target'))]), "den": AGG('count', 'targets')},
               {"title": "Units on pace this month", "num": AGG('count', 'pace', where=[TD, ('pace_flag', '<>', ca('Behind pace'))]), "den": AGG('count', 'pace', where=[TD])},
               {"title": "Months at or above the market occupancy", "num": AGG('count', 'market', where=[('occ_flag', '<>', ca('Below market'))]), "den": AGG('count', 'market')},
               {"title": "Ratings at or above the minimum", "num": AGG('count', 'review_scores', where=[('min_flag', '=', ca('Meets minimum'))]), "den": AGG('count', 'review_scores')}],
    "charts": [
        CHART('Occupancy per month', 'line', 'month', [AGG('avg', 'unit_months', 'unit_months.occupancy', date='unit_months.month', where=[TD], label='Occupancy')]),
        CHART('ADR per month', 'line', 'month', [AGG('avg', 'unit_months', 'unit_months.adr', date='unit_months.month', where=[TD, ('booked_nights', '>', 0)], label='ADR')]),
        CHART('RevPAR per month', 'line', 'month', [AGG('avg', 'unit_months', 'unit_months.revpar', date='unit_months.month', where=[TD], label='RevPAR')]),
        CHART('Room revenue per month', 'column', 'month', [AGG('sum', 'unit_months', 'unit_months.room_revenue', date='unit_months.month', where=[TD], label='Room revenue')]),
        CHART('Occupancy by city', 'bar', 'city_months.city', [AGG('avg', 'city_months', 'city_months.occupancy', where=[TD], label='Occupancy')]),
        CHART('ADR by city', 'bar', 'city_months.city', [AGG('avg', 'city_months', 'city_months.adr', where=[TD], label='ADR')]),
        CHART('RevPAR by unit type', 'bar', 'type_months.unit_type', [AGG('avg', 'type_months', 'type_months.revpar', where=[TD], label='RevPAR')]),
        CHART('Occupancy by season', 'bar', 'unit_months.season', [AGG('avg', 'unit_months', 'unit_months.occupancy', where=[TD], label='Occupancy')]),
        CHART('Weekday occupancy', 'bar', 'weekday.weekday', [AGG('avg', 'weekday', 'weekday.occupancy', label='Occupancy')]),
        CHART('Nights by stay length bucket', 'bar', 'stay_mix.stay_bucket', [AGG('sum', 'stay_mix', 'stay_mix.nights', label='Nights')]),
        CHART('Bookings by lead time bucket', 'bar', 'lead_time.lead_bucket', [AGG('sum', 'lead_time', 'lead_time.bookings', label='Bookings')]),
        CHART('Blocked nights per month', 'column', 'month', [AGG('sum', 'blocked', 'blocked.nights', date='blocked.from_date', label='Blocked nights')]),
        CHART('Pace gap per month', 'column', 'month', [AGG('sum', 'pace', 'pace.gap', date='pace.month', label='Nights ahead or behind target')]),
        CHART('Revenue this year against last year', 'column', 'month', [AGG('sum', 'yoy', 'yoy.revenue_this', date='yoy.month', label='This year'), AGG('sum', 'yoy', 'yoy.revenue_last', date='yoy.month', label='A year earlier')]),
        CHART('Our occupancy against the market', 'line', 'month', [AGG('avg', 'market', 'market.our_occupancy', date='market.month', label='Our occupancy'), AGG('avg', 'market', 'market.market_occupancy', date='market.month', label='Market occupancy')]),
        CHART('Our ADR against the market', 'line', 'month', [AGG('avg', 'market', 'market.our_adr', date='market.month', label='Our ADR'), AGG('avg', 'market', 'market.market_adr', date='market.month', label='Market ADR')]),
        CHART('Orphan nights filled per month', 'column', 'month', [AGG('sum', 'orphan', 'orphan.gap_length', date='orphan.date', where=[('filled', '=', tok('yn', 'Yes'))], label='Orphan nights filled')]),
        CHART('Average rating per month', 'line', 'month', [AGG('avg', 'review_scores', 'review_scores.avg_rating', date='review_scores.month', label='Average rating')])]}
signature = [
    {"name": "Occupancy, ADR and RevPAR by unit and month", "why": "every unit and month shows nights sold, the average price of a night sold and revenue per available night against the target for that unit", "where": "Unit Months"},
    {"name": "Unit health score", "why": "occupancy, ADR, rating and margin become one score out of 100 and name the weakest part of a unit", "where": "Unit Health Score"},
    {"name": "Pace report against target", "why": "nights on the books now and a month ago against the nights wanted, with the gap and the price move to make for each unit and coming month", "where": "Pace Rows"},
    {"name": "Occupancy needed for a revenue goal", "why": "a revenue goal and an ADR become the occupancy you must reach, and tell you if the goal is realistic", "where": "Occupancy Needed"},
    {"name": "Rate or occupancy trade-off", "why": "a price cut shows the extra occupancy needed to earn the same profit and whether the response you expect pays for it", "where": "Rate or Occupancy Trade-off"},
    {"name": "Blocked night cost", "why": "every blocked period shows the revenue it cost at the ADR and occupancy of that unit, so owner stays and repairs are priced", "where": "Blocked Nights"},
    {"name": "Weak unit diagnosis", "why": "occupancy, rate against the market, rating, lead time and weekday gaps point to the likely cause and the fix to try first", "where": "Weak Unit Diagnosis"},
    {"name": "Market comparison index", "why": "your occupancy, ADR and RevPAR against comparable listings by city and month, with the index and a fair share check", "where": "Competitor Set Summary"},
    {"name": "Weekday gap finder", "why": "occupancy by weekday and unit shows the cheapest nights to fill and what they are worth in a year", "where": "Weekday Gap Finder"},
    {"name": "Year-on-year change", "why": "nights and revenue against a year earlier split into more nights and a better rate, so you know what drove the change", "where": "Year-on-Year Change"}]
competitors = [
    {"what": "free occupancy templates", "lacks": "count nights sold but have no ADR or RevPAR, no targets by unit, no pace against target and no market comparison"},
    {"what": "subscription property-management software", "lacks": "charge every month and show averages for the whole portfolio, so you cannot see why one unit is weak or test your own targets"},
    {"what": "single-sheet booking trackers", "lacks": "list bookings but never turn them into occupancy by month, season, city and weekday, or show blocked nights and orphan nights"},
    {"what": "generic expense spreadsheets", "lacks": "track costs but cannot say how many nights a unit must sell, or at what ADR, to reach a revenue goal"},
    {"what": "automatic pricing tools", "lacks": "move rates for you without showing the pace gap, the year-on-year change or the revenue lost on blocked nights"}]
guide = [
    'Open Start and type your company name and your own limits in the yellow cells: wanted occupancy and ADR, the review rating you want, the pace tolerance and the length of a long block.',
    'Check Units, Targets by Unit, Seasons, Cities and Team. They hold your units, the target of each unit, the price factor of each month and the people the other sheets look up.',
    'Fill Unit Months every month: nights available, nights sold and room revenue of each unit. Occupancy, ADR (the average price of a night sold) and RevPAR (revenue per available night) calculate themselves.',
    'Log your bookings on Bookings. Lead time, the ADR of each stay and the rate against the unit base rate fill in.',
    'Update Pace Rows once a week: the nights booked now and a month ago for each unit and coming month. The pace gap, the open nights and the price move to make fill in.',
    'Write every blocked period on Blocked Nights and every free night between two bookings on Orphan Nights. You see the revenue lost and the revenue missed.',
    'Use City Months, Type Months, Weekday Pattern, Lead Time Curve, Length of Stay Mix and Channel Mix by Unit to see where the nights and the revenue come from.',
    'Compare each month with a year earlier on Year on Year, and with comparable listings on Competitor Set Summary.',
    'Record each finding and action on Performance Reviews, with an owner and a due date. Overdue actions turn red.',
    'Keep the review scores of each unit on Review Scores by Unit. Units under your minimum rating are flagged.',
    f'Use the {len(tools)} calculators for the health score, pace, the occupancy needed for a goal, price cuts, seasons, blocked nights, market comparison, weak units, weekday gaps and lead time.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Performance Dashboard and Charts every week: occupancy, ADR, RevPAR, pace, blocked nights, orphan nights and the market.']
listing = {"title": "Short-Term Rental Occupancy, ADR and RevPAR Excel Template: Unit Performance, Pace, Targets, Market Comparison, Blocked Nights",
    "headline": "See which units earn, which lag and what to do about it",
    "tags": ["short term rental", "vacation rental", "rental host", "occupancy rate", "adr revpar", "excel template", "unit performance", "occupancy tracker", "pace report", "property host", "holiday let", "rental analytics", "revenue per night"],
    "description": ("Measure how every unit of a short-term or vacation rental business performs in one Excel workbook. Built for a host or co-host with 3 to 15 furnished units rented by the night through booking platforms and direct bookings. "
        "Unit Months turns the nights available, the nights sold and the room revenue of every unit and month into occupancy, ADR (the average price of a night sold) and RevPAR (revenue per available night), checked against a target for each unit.\n\n"
        "Pace Rows compares the nights on the books now and a month ago with the nights you wanted, flags the units behind pace and suggests the price move. Blocked Nights prices every owner stay, repair and renovation, and Orphan Nights tracks the free nights between two bookings. "
        "City Months, Type Months, Weekday Pattern, Lead Time Curve, Length of Stay Mix and Channel Mix show where the nights and the revenue come from. Year on Year and Competitor Set Summary compare each month with last year and with comparable listings, and Performance Reviews keeps every finding with an owner and a due date.\n\n"
        f"{len(tools)} calculators cover a unit health score, pace, the occupancy needed for a revenue goal, a price cut against occupancy, seasonality, blocked night cost, market comparison, weak unit diagnosis, weekday gaps, lead time and a RevPAR grid. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to owners, the co-host (a helper who handles guests for a fee), the host, cleaners, a handyperson and the accountant.\n\n"
        "This is part three of the Short-Term Rental Host suite. A standard .xlsx workbook with no macros and no subscription, 15 languages in one purchase, with a demo copy full of sample data for a small portfolio to explore first. It helps you understand your performance and does not promise results."),
    "features": ["Occupancy, ADR and RevPAR by unit and month", "Targets by unit with checks", "Pace report against target", "Blocked night and orphan night cost", "City, unit type, weekday and season views",
                 "Year-on-year and market comparison", "Weak unit diagnosis", "Performance reviews with owners and due dates", f"{len(tools)} calculators for performance decisions", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p3', slug='short-term-rental-performance', profession='Short-Term Rental Host', name='Occupancy, ADR and RevPAR',
         tagline='See which units earn, which lag and what to do about it', price_usd=29,
         colors={"primary": "#264653", "accent": "#E9C46A"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 3, "of": 8, "focus": "Occupancy, ADR and RevPAR by unit, city, type, month and season; pace, blocked and orphan nights, year on year and market comparison"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sr3.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
