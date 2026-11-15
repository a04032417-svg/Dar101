"""Short-term rental host suite - part 1: Listings, Rates and Pricing Calendar."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr1_lists import *
from sr1_tables import settings, tables
from sr1_tools import tools

SUITE = 'fx-20261113-short-term-rental'
NOTE = "Sample wording: adapt it to your own practice and check your own local rules."
BS = lambda s: tok('bstatus', s)
FORMS_SRC = None
def F(*pairs): return [FV(a, b) for a, b in pairs]
forms = [
    FORM('rate_change_sheet', 'Rate Change Sheet', 'Rate change with reason and bookings after', 'rate_changes.rc_id', F(
        ('Date', 'rate_changes.date'), ('Unit', 'rate_changes.unit'), ('Old rate', 'rate_changes.old_rate'), ('New rate', 'rate_changes.new_rate'), ('Change percent', 'rate_changes.change_pct'), ('Direction', 'rate_changes.direction'),
        ('Reason', 'rate_changes.reason'), ('Changed by', 'rate_changes.changed_by'), ('Bookings in the next 14 days', 'rate_changes.bookings_14d'), ('Owner phone', 'rate_changes.owner_phone')) + [
        FF('Rate changes on this unit', 'COUNTIFS({range:rate_changes.unit},INDEX({range:rate_changes.unit},MATCH({pick},{range:rate_changes.rc_id},0)))', 'int'),
        FF('Average change, all rate changes', 'AVERAGE({range:rate_changes.change_pct})', 'pct')]),
    FORM('event_sheet', 'Event Pricing Sheet', 'Event with demand lift and free nights', 'events.event_id', F(
        ('Event', 'events.event'), ('City', 'events.city'), ('Start', 'events.start_date'), ('End', 'events.end_date'), ('Event nights', 'events.event_nights'), ('Demand lift', 'events.demand_lift'), ('Days to the event', 'events.days_to_event'),
        ('Event check', 'events.event_flag'), ('Free nights still listed', 'events.free_listed'), ('Co-host phone', 'events.cohost_phone'))),
    FORM('gap_sheet', 'Gap Night Offer Sheet', 'Gap night with offer rate and revenue', 'gaps.gap_id', F(
        ('Date', 'gaps.date'), ('Unit', 'gaps.unit'), ('Nights free', 'gaps.nights_free'), ('Usual rate', 'gaps.usual_rate'), ('Discount offered', 'gaps.discount_pct'), ('Offer rate', 'gaps.offer_rate'), ('Filled', 'gaps.filled'),
        ('Revenue recovered', 'gaps.recovered'), ('Revenue missed', 'gaps.missed'), ('Gap status', 'gaps.status'), ('Co-host phone', 'gaps.cohost_phone'))),
    FORM('lastmin_sheet', 'Last-minute Deal Sheet', 'Last-minute deal with discount and revenue', 'lastmin.lm_id', F(
        ('Unit', 'lastmin.unit'), ('Check-in', 'lastmin.check_in'), ('Days before check-in', 'lastmin.days_before'), ('Nights', 'lastmin.nights'), ('Usual rate', 'lastmin.usual_rate'), ('Rate booked', 'lastmin.rate'),
        ('Discount given', 'lastmin.discount_pct'), ('Revenue', 'lastmin.revenue'), ('Channel', 'lastmin.channel'), ('Fill timing', 'lastmin.fill_flag'))),
    FORM('minstay_sheet', 'Minimum Stay Change Sheet', 'Minimum stay by unit and season', 'minstay.ms_id', F(
        ('Unit', 'minstay.unit'), ('Season', 'minstay.season'), ('Weekday minimum', 'minstay.weekday_min'), ('Weekend minimum', 'minstay.weekend_min'), ('Gap-night minimum', 'minstay.gap_min'), ('Strictest minimum', 'minstay.strictest'),
        ('Gap check', 'minstay.gap_flag'), ('Reviewed on', 'minstay.review_on'), ('Review check', 'minstay.review_flag'), ('Owner phone', 'minstay.owner_phone'))),
    FORM('direct_sheet', 'Direct Booking Offer Sheet', 'Direct offer with bookings and revenue', 'direct_offers.offer_id', F(
        ('Code', 'direct_offers.code'), ('Unit', 'direct_offers.unit'), ('Discount', 'direct_offers.discount_pct'), ('Valid from', 'direct_offers.valid_from'), ('Valid until', 'direct_offers.valid_until'), ('Bookings', 'direct_offers.bookings'),
        ('Revenue', 'direct_offers.revenue'), ('Offer status', 'direct_offers.status'), ('Revenue per booking', 'direct_offers.rev_per_booking'), ('Days left', 'direct_offers.days_left'))),
    FORM('comp_sheet', 'Comparable Check Sheet', 'Comparable listing against our rate', 'comps.comp_id', F(
        ('Our unit', 'comps.unit'), ('Comparable', 'comps.comparable'), ('City', 'comps.city'), ('Bedrooms', 'comps.bedrooms'), ('Weekday rate', 'comps.weekday_rate'), ('Weekend rate', 'comps.weekend_rate'), ('Review score', 'comps.review_score'),
        ('Our base rate', 'comps.our_rate'), ('Gap to our rate', 'comps.gap_to_our_rate'), ('Gap percent', 'comps.gap_pct'), ('Position', 'comps.position'), ('Checked on', 'comps.checked_on'))),
    FORM('experiment_sheet', 'Price Experiment Sheet', 'Price test with result', 'experiments.ex_id', F(
        ('Unit', 'experiments.unit'), ('Start', 'experiments.start_date'), ('Weeks', 'experiments.weeks'), ('Rate before', 'experiments.rate_before'), ('Rate tested', 'experiments.rate_tested'), ('Rate change', 'experiments.change_pct'),
        ('Nights booked', 'experiments.nights_booked'), ('Occupancy in the test', 'experiments.occ_test'), ('Revenue per week', 'experiments.rev_week'), ('Result', 'experiments.result'), ('Test check', 'experiments.test_flag'))),
    FORM('fee_sheet', 'Cleaning Fee Review Sheet', 'Cleaning fee with cost and margin', 'clean_fee.unit', F(
        ('Unit type', 'clean_fee.unit_type'), ('Cleaner hours', 'clean_fee.cleaner_hours'), ('Supplies', 'clean_fee.supplies'), ('Linen', 'clean_fee.linen_cost'), ('Fee charged', 'clean_fee.fee'), ('Cleaner cost', 'clean_fee.cleaner_cost'),
        ('Total cost', 'clean_fee.cost_total'), ('Margin on the fee', 'clean_fee.margin'), ('Margin percent', 'clean_fee.margin_pct'), ('Margin check', 'clean_fee.margin_flag'), ('Fee for the margin target', 'clean_fee.suggested_fee'))),
    FORM('listing_sheet', 'New Listing Pricing Sheet', 'Unit with base rate, rate card and break-even', 'units.unit_id', F(
        ('Name', 'units.name'), ('Unit type', 'units.unit_type'), ('City', 'units.city'), ('Bedrooms', 'units.bedrooms'), ('Guests', 'units.max_guests'), ('Owner', 'units.owner'), ('Base rate', 'units.base_rate'), ('Cleaning fee', 'units.cleaning_fee'),
        ('Lowest season rate', 'units.low_rate'), ('Peak season rate', 'units.peak_rate'), ('Peak weekend rate', 'units.peak_weekend'), ('Break-even rate', 'units.break_even'), ('ADR, 12 months', 'units.adr_12m'), ('Occupancy, 12 months', 'units.occ_12m'),
        ('Break-even check', 'units.be_flag'))),
]
assert len(forms) == 10
documents = [
    DOC('rate_card_doc', 'Seasonal Rate Card', 'Seasonal rate card for one unit', 'units.unit_id', [
        'Seasonal rate card of {set:company}, dated {today}. Unit {col:units.unit_id}: {col:units.name}, a {col:units.unit_type} with {col:units.bedrooms} bedrooms for up to {col:units.max_guests} guests.',
        'Base rate: {col:units.base_rate} a night. Lowest season rate: {col:units.low_rate}. Peak season rate: {col:units.peak_rate}. Peak weekend rate: {col:units.peak_weekend}. Cleaning fee: {col:units.cleaning_fee}. Rates are before any local tax.',
        'Friday and Saturday nights carry a lift of {set:weekend_lift}. Rates move with the season, local events and the days left before check-in. Owner: {col:units.owner}.', 'The rate card is reviewed at every season change and written in the rate change log.'], ['Host', 'Owner'], NOTE),
    DOC('review_doc', 'Unit Pricing Review', 'Pricing review for one unit', 'units.unit_id', [
        'Pricing review of {set:company}, dated {today}. Unit: {col:units.name} ({col:units.city}).', 'Last 12 months: {col:units.nights_12m} nights booked of {col:units.avail_12m} available, which is occupancy of {col:units.occ_12m}. Room revenue: {col:units.revenue_12m}.',
        'ADR, the average price of a night sold: {col:units.adr_12m}, against a base rate of {col:units.base_rate}. Check: {col:units.adr_flag}. Break-even rate: {col:units.break_even}. Break-even check: {col:units.be_flag}.',
        'Revenue on the books for the next 13 weeks: {col:units.books_13w}. Free nights in those weeks: {col:units.free_13w}.', 'Decisions on the base rate, the minimum stay and discounts are written below with the date.'], ['Host', 'Owner'], NOTE),
    DOC('event_doc', 'Event Pricing Plan', 'Event week pricing plan', 'events.event_id', [
        'Event pricing plan of {set:company}, dated {today}. Event: {col:events.event} in {col:events.city}, from {col:events.start_date} to {col:events.end_date}, {col:events.event_nights} nights.',
        'Expected demand lift: {col:events.demand_lift}. Days to the event: {col:events.days_to_event}. Check: {col:events.event_flag}. Free nights still listed in the event: {col:events.free_listed}.',
        'Actions: raise the rates for the event nights, set a longer minimum stay, close gaps around the event and tell the co-host which price to quote. Do not discount event nights.', 'Owners are told about the new rates before the event starts.'], ['Host', 'Co-host'], NOTE),
    DOC('direct_letter', 'Direct Offer Letter', 'Direct booking offer letter', 'direct_offers.offer_id', [
        'Direct booking offer of {set:company}, dated {today}. Offer code: {col:direct_offers.code}.', 'Thank you for staying with us. Book {col:direct_offers.unit} directly and take {col:direct_offers.discount_pct} off the nightly rate, with no platform fee added.',
        'The offer is valid from {col:direct_offers.valid_from} until {col:direct_offers.valid_until}. Quote the code when you write to us. Prices are before any local tax.', 'We will confirm your dates and the total price in writing.'], ['Host', 'Guest'], NOTE),
    DOC('meeting_doc', 'Pricing Meeting Sheet', 'Weekly pricing meeting sheet for one unit week', 'pricing.price_id', [
        'Weekly pricing meeting of {set:company}, dated {today}. Unit: {col:pricing.unit}. Week of {col:pricing.week}. Season: {col:pricing.season}.',
        'Base rate {col:pricing.base_rate}, listed rate {col:pricing.listed_rate}, suggested rate {col:pricing.suggested_rate}. Rate check: {col:pricing.rate_flag}. Gap to the suggested rate: {col:pricing.gap_to_suggested}.',
        'Booked nights {col:pricing.booked_nights}, free nights {col:pricing.free_nights}, occupancy {col:pricing.occupancy}. Fill check: {col:pricing.fill_flag}. Local event: {col:pricing.event}. Minimum stay: {col:pricing.min_stay}.',
        'Revenue left at the booked rate: {col:pricing.left_on_table}. Decision and owner of the action are written below.'], ['Host', 'Co-host'], NOTE),
    DOC('breakeven_doc', 'Break-Even Summary', 'Break-even summary for one unit', 'breakeven.unit', [
        'Break-even summary of {set:company}, dated {today}. Unit: {col:breakeven.unit}.', 'Fixed cost per month: {col:breakeven.fixed_monthly}, of which other fixed cost {col:breakeven.other_fixed}. Variable cost per night: {col:breakeven.var_per_night}. Target occupancy: {col:breakeven.target_occ}.',
        'Break-even rate after platform fees: {col:breakeven.break_even_rate}. Base rate: {col:breakeven.base_rate}. Base rate less break-even: {col:breakeven.margin_per_night}. Check: {col:breakeven.rate_flag}.',
        'Occupancy needed at the base rate: {col:breakeven.occ_needed}. If this is above your target, raise the rate or cut the cost before the next season.'], ['Host', 'Owner'], NOTE),
    DOC('change_log_doc', 'Rate Change Log', 'Rate change log entry', 'rate_changes.rc_id', [
        'Rate change log of {set:company}, dated {today}. Change {col:rate_changes.rc_id} on {col:rate_changes.date} for {col:rate_changes.unit}.', 'The rate moved from {col:rate_changes.old_rate} to {col:rate_changes.new_rate}, a change of {col:rate_changes.change_pct} ({col:rate_changes.direction}).',
        'Reason: {col:rate_changes.reason}. Changed by {col:rate_changes.changed_by}. Bookings in the next 14 days: {col:rate_changes.bookings_14d}.', 'The owner was told on the date of the change.'], ['Host', 'Owner'], NOTE),
    DOC('policy_doc', 'Discount Policy', 'Discount and minimum-stay policy for one rule', 'discounts.rule_id', [
        'Discount policy of {set:company}, dated {today}. Rule {col:discounts.rule_id}: {col:discounts.rule}.', 'Trigger: {col:discounts.trigger}. Units covered: {col:discounts.unit_scope}. Days before check-in: {col:discounts.trigger_days}. Discount: {col:discounts.discount_pct}. Minimum nights: {col:discounts.min_nights}.',
        'Example: on an average unit the rate becomes {col:discounts.example_rate} a night. The rule is {col:discounts.rule_flag}.', 'No discount is given below the break-even rate of the unit unless the host agrees. Every discount is written in the rate change log.'], ['Host', 'Co-host'], NOTE),
    DOC('comp_doc', 'Comparables Review', 'Comparable listing review', 'comps.comp_id', [
        'Comparable listings review of {set:company}, dated {today}. Our unit: {col:comps.unit}. Comparable: {col:comps.comparable} in {col:comps.city}.', 'Comparable weekday rate {col:comps.weekday_rate}, weekend rate {col:comps.weekend_rate}, review score {col:comps.review_score}. Our base rate: {col:comps.our_rate}.',
        'Gap to our rate: {col:comps.gap_to_our_rate} ({col:comps.gap_pct}). Position: {col:comps.position}. Checked on {col:comps.checked_on}.', 'Action on our rate and the reason are written below.'], ['Host'], NOTE),
    DOC('forecast_doc', 'Revenue Forecast', 'Revenue forecast by unit', 'units.unit_id', [
        'Revenue forecast of {set:company}, dated {today}. Unit: {col:units.name} ({col:units.city}), owner {col:units.owner}.', 'Revenue on the books for the next 13 weeks: {col:units.books_13w}. Free nights still to fill: {col:units.free_13w}. Base rate {col:units.base_rate}, peak season rate {col:units.peak_rate}.',
        'Room revenue of the last 12 months was {col:units.revenue_12m} at an ADR of {col:units.adr_12m} and occupancy of {col:units.occ_12m}.', 'The forecast counts only what is booked. Free nights are filled with gap night and last-minute offers.'], ['Host', 'Owner'], NOTE),
]
assert len(documents) == 10
def S(*st): return list(st)
checklists = [
    CHK('weekly_review', 'Weekly Pricing Review Steps', 'pricing', 'pricing.week', [('Check booked and free nights of every unit', 0), ('Compare listed rates with the suggested rates', 0), ('Update units priced below the suggestion', 1), ('Look at local events in the next 8 weeks', 1),
        ('Fill gap nights with a discount', 2), ('Check last-minute nights for the next 7 days', 2), ('Look at comparable listings of units that are not filling', 3), ('Write every rate change in the log with its reason', 4), ('Send the pricing summary to the owners', 6)]),
    CHK('event_run', 'Event Week Preparation Steps', 'events', 'events.start_date', [('Check the dates and the demand lift', -45), ('Raise the rates for the event nights', -40), ('Set a longer minimum stay', -40), ('Close gap nights around the event', -30), ('Tell the owners about the new rates', -28),
        ('Brief the co-host on prices and the minimum stay', -21), ('Book cleaners for the busy turnovers', -14), ('Check free nights and fill them at the new rate', -7), ('Review what the event earned', 7)]),
    CHK('season_run', 'Season Change Rate Update Steps', 'seasons', 'seasons.month', [('Open the Seasons sheet and check the price factor', -14), ('Update the base rates that need a change', -10), ('Update weekday and weekend rates in the listings', -7), ('Check minimum stays for the new season', -7),
        ('Tell the co-host and the owners', -5), ('Review discount rules for the season', -3), ('Check the first week of bookings at the new rates', 7)]),
    CHK('gap_run', 'Gap Night Check Steps', 'gaps', 'gaps.date', [('List the free nights between two bookings', -14), ('Offer the gap rate to guests who stay before or after', -10), ('Relax the minimum stay for the gap', -7), ('Lower the rate on the platform', -5), ('Ask the co-host to answer enquiries the same day', -3), ('Record whether the gap filled', 1)]),
    CHK('lastmin_run', 'Last-Minute Fill Check Steps', 'lastmin', 'lastmin.check_in', [('List the free nights in the next 7 days', -7), ('Check the occupancy of the next 30 days', -6), ('Apply the last-minute discount if the month is behind target', -3), ('Check the cleaner can turn the unit', -2), ('Answer every enquiry within the target time', -1), ('Record the rate and the discount given', 1)]),
    CHK('listing_run', 'New Listing Pricing Steps', 'units', 'units.since', [('Collect rates of five comparable listings', -14), ('Set the base rate and the cleaning fee', -10), ('Work out the break-even rate', -10), ('Set season factors and the weekend lift', -7), ('Set minimum stays by season', -7), ('Set discount rules', -5), ('Publish the listing at a launch rate', 0), ('Review the rate after 30 days', 30)]),
    CHK('minstay_run', 'Minimum-Stay Review Steps', 'minstay', 'minstay.review_on', [('Check the gaps left by the current minimum stay', 0), ('Check the share of one-night stays and their cleaning cost', 2), ('Compare the season with last year', 5), ('Set the new weekday and weekend minimum', 7), ('Tell the co-host and the owner', 8), ('Review again in 90 days', 90)]),
    CHK('comp_run', 'Comparable Listings Check Steps', 'comps', 'comps.checked_on', [('Open the comparable listing and read its rates', 0), ('Compare the weekday and weekend rate with ours', 0), ('Compare the review score and the photos', 1), ('Note a rate drop or a rise', 1), ('Change our rate if the gap is over 5 percent', 2), ('Check again in 30 days', 30)]),
    CHK('fee_run', 'Cleaning Fee Review Steps', 'clean_fee', 'clean_fee.review_on', [('Read the cleaner hours of the last ten turnovers', -7), ('Check supplies and linen cost', -5), ('Work out the fee for the margin target', -3), ('Compare the fee with similar units', -2), ('Update the fee in the listing', 0), ('Tell the owner about the new fee', 1), ('Review again in six months', 180)]),
    CHK('year_run', 'Year-End Rate Review Steps', 'breakeven', 'breakeven.review_on', [('List the ADR and occupancy of each unit', -21), ('Compare each unit with its break-even rate', -18), ('Review the discounts and what they gave away', -14), ('Review price tests and keep the ones that worked', -10),
        ('Set base rates for the new year', -7), ('Update the Seasons sheet', -5), ('Send the new rate cards to the owners and the accountant', 0)]),
]
assert len(checklists) == 10
def M(key_, moment, table, phone, text): return MSG(key_, moment, table, phone, text)
messages = [
    M('g_direct', 'Guest: direct price beats the platform', 'bookings', 'bookings.guest_phone', 'Hello {guest}, booking {unit} direct costs {direct_rate} a night instead of {nightly_rate}, with no platform fee. Shall I hold your dates?'),
    M('g_gap', 'Guest: discount on the night before', 'bookings', 'bookings.guest_phone', 'Hello {guest}, {unit} is free the night before your stay from {check_in}. You can add it at {gap_rate} a night. Would you like it?'),
    M('g_lastmin', 'Guest: last-minute offer', 'bookings', 'bookings.guest_phone', 'Hello {guest}, {unit} has dates free at the last-minute rate of {lastmin_rate} a night. Reply if you would like to book.'),
    M('g_week', 'Guest: a weekly stay discount for you', 'bookings', 'bookings.guest_phone', 'Hello {guest}, stay 7 nights or more in {unit} and pay {weekly_rate} a night instead of {nightly_rate}. Shall I check your dates?'),
    M('g_return', 'Guest: a returning guest offer', 'bookings', 'bookings.guest_phone', 'Hello {guest}, thank you for staying in {unit}. Come back and book direct for {direct_rate} a night.'),
    M('g_free', 'Guest: your dates are free at a new rate', 'bookings', 'bookings.guest_phone', 'Hello {guest}, your dates in {unit} are free again at {nightly_rate} a night for {nights} nights. Would you like to book?'),
    M('g_change', 'Guest: the price for the unit changes', 'bookings', 'bookings.guest_phone', 'Hello {guest}, the price of {unit} for stays from {check_in} will change soon. Your quote is {nightly_rate} a night. Reply today to keep it.'),
    M('g_minstay', 'Guest: a minimum stay applies', 'bookings', 'bookings.guest_phone', 'Hello {guest}, your dates in {unit} need a stay of at least {nights} nights. Can you extend your stay?'),
    M('g_quote', 'Guest: your quote is ready', 'bookings', 'bookings.guest_phone', 'Hello {guest}, your quote for {unit}: {nights} nights from {check_in} at {nightly_rate} a night, cleaning fee {cleaning_fee}, total {gross}.'),
    M('g_thanks', 'Guest: thanks for booking direct', 'bookings', 'bookings.guest_phone', 'Hello {guest}, thank you for booking {unit} direct. Your total is {gross}. We look forward to your stay on {check_in}.'),
    M('g_after', 'Guest: a night is open after your stay', 'bookings', 'bookings.guest_phone', 'Hello {guest}, the night after your stay, {check_out}, is free in {unit}. Stay one more night at {gap_rate}.'),
    M('g_event', 'Guest: festival week, book early', 'bookings', 'bookings.guest_phone', 'Hello {guest}, a local festival week is coming and {unit} fills fast. Book early: the rate is {nightly_rate} a night now.'),
    M('o_changed', 'Owner: the rate for your unit changed', 'rate_changes', 'rate_changes.owner_phone', 'Hello, the rate for {unit} changed from {old_rate} to {new_rate} on {date}. Reason: {reason}.'),
    M('o_card', 'Owner: the seasonal rate card is ready', 'units', 'units.owner_phone', 'Hello {owner}, the rate card for {name} is ready: lowest season {low_rate}, peak season {peak_rate}, peak weekend {peak_weekend}.'),
    M('o_sold', 'Owner: sold out in the event week', 'pricing', 'pricing.owner_phone', 'Hello, {unit} has {booked_nights} nights booked in the week of {week} ({event}) at {avg_booked_rate}. The suggested rate was {suggested_rate}.'),
    M('o_below', 'Owner: priced below comparables', 'comps', 'comps.owner_phone', 'Hello, {comparable} charges {weekday_rate} on weekdays against our {our_rate} for {unit}. I am looking at the price.'),
    M('o_be', 'Owner: break-even above the rate', 'breakeven', 'breakeven.owner_phone', 'Hello, the break-even rate for {unit} is {break_even_rate} and the base rate is {base_rate}. We need to talk about the price.'),
    M('o_test', 'Owner: your price test has ended', 'experiments', 'experiments.owner_phone', 'Hello, the price test on {unit} has ended. We tested {rate_tested} for {weeks} weeks and booked {nights_booked} nights.'),
    M('o_adr', 'Owner: average rate below base rate', 'units', 'units.owner_phone', 'Hello {owner}, the average price of a night sold at {name} over 12 months is {adr_12m}, against a base rate of {base_rate}.'),
    M('o_min', 'Owner: your minimum stay changes', 'minstay', 'minstay.owner_phone', 'Hello, the minimum stay for {unit} changes to {weekday_min} nights on weekdays and {weekend_min} on weekends.'),
    M('c_rate', 'Co-host: update the listed rate', 'pricing', 'pricing.cohost_phone', 'Hello, please set the listed rate for {unit} in the week of {week} to {suggested_rate}. It is {listed_rate} now.'),
    M('c_event', 'Co-host: guests ask about the event', 'events', 'events.cohost_phone', 'Hello, guests are asking about {event} from {start_date}. Please answer with the new rate and the minimum stay. Demand lift: {demand_lift}.'),
    M('c_gap', 'Co-host: gap nights to fill this week', 'gaps', 'gaps.cohost_phone', 'Hello, {nights_free} free nights in {unit} on {date}. Please offer them at {offer_rate} a night.'),
    M('c_min', 'Co-host: confirm the new minimum stay', 'minstay', 'minstay.cohost_phone', 'Hello, please confirm that {unit} now has a minimum of {weekday_min} nights on weekdays and {weekend_min} on weekends.'),
    M('h_review', 'Host: the weekly pricing review is ready', 'pricing', 'pricing.host_phone', 'Hello, the pricing review is ready. {unit}, week of {week}: listed {listed_rate}, suggested {suggested_rate}.'),
    M('h_free', 'Host: a unit has free nights next week', 'pricing', 'pricing.host_phone', 'Hello, {unit} has {free_nights} free nights in the week of {week}. Please consider a gap or last-minute offer.'),
    M('h_comp', 'Host: a competitor rate dropped', 'comps', 'comps.host_phone', 'Hello, {comparable} near {unit} now charges {weekday_rate} on weekdays. Our base rate is {our_rate}.'),
    M('a_card', 'Accountant: the new rate card', 'units', 'units.accountant_phone', 'Hello, the rate card for {name} is ready for the new tax year: lowest season {low_rate}, peak season {peak_rate}. Room revenue of 12 months: {revenue_12m}.'),
]
assert len(messages) == 28
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; NXT = 'DATE(YEAR({today}),MONTH({today})+1,1)'; Y1 = 'DATE(YEAR({today})-1,MONTH({today}),1)'
NC = '{range:bookings.status},"<>"&' + BS('Cancelled')
WK0 = '{range:pricing.week},">"&({today}-7),{range:pricing.week},"<="&{today}'
def WKN(n): return '{range:pricing.week},">"&({today}-7),{range:pricing.week},"<="&({today}+%d)' % n
def BKR(a, b): return '{range:bookings.check_in},">="&%s,{range:bookings.check_in},"<"&%s' % (a, b)
FR, SA = tok('wday', 'Friday'), tok('wday', 'Saturday')
WE_ADR = '(SUMIFS({range:weekday.adr},{range:weekday.weekday},%s)+SUMIFS({range:weekday.adr},{range:weekday.weekday},%s))/(COUNTIFS({range:weekday.weekday},%s)+COUNTIFS({range:weekday.weekday},%s))' % (FR, SA, FR, SA)
WD_ADR = '(SUM({range:weekday.adr})-SUMIFS({range:weekday.adr},{range:weekday.weekday},%s)-SUMIFS({range:weekday.adr},{range:weekday.weekday},%s))/(COUNT({range:weekday.adr})-COUNTIFS({range:weekday.weekday},%s)-COUNTIFS({range:weekday.weekday},%s))' % (FR, SA, FR, SA)
kpis = [
    KPI('Average nightly rate this month', 'IFERROR(AVERAGEIFS({range:bookings.nightly_rate},%s,%s),0)' % (BKR(MS, NXT), NC), 'money'),
    KPI('Average nightly rate, last 12 months', 'IFERROR(AVERAGEIFS({range:bookings.nightly_rate},%s,%s),0)' % (BKR(Y1, MS), NC), 'money'),
    KPI('ADR against base rate, last 12 months', 'IFERROR(AVERAGEIFS({range:bookings.rate_vs_base},%s,%s),0)' % (BKR(Y1, MS), NC), 'pct'),
    KPI('Units below suggested rate this week', 'COUNTIFS(%s,{range:pricing.rate_flag},%s)' % (WK0, ca('Below suggested rate')), 'int'),
    KPI('Units above suggested rate this week', 'COUNTIFS(%s,{range:pricing.rate_flag},%s)' % (WK0, ca('Above suggested rate')), 'int'),
    KPI('Free nights this week', 'SUMIFS({range:pricing.free_nights},%s)' % WK0, 'int'),
    KPI('Free nights this week and next', 'SUMIFS({range:pricing.free_nights},%s)' % WKN(7), 'int'),
    KPI('Free nights in the next 4 weeks', 'SUMIFS({range:pricing.free_nights},%s)' % WKN(21), 'int'),
    KPI('Occupancy of the next 4 weeks', 'IFERROR(SUMIFS({range:pricing.booked_nights},%s)/SUMIFS({range:pricing.week_nights},%s),0)' % (WKN(21), WKN(21)), 'pct'),
    KPI('Revenue on the books, next 4 weeks', 'SUMPRODUCT(({range:pricing.week}>{today}-7)*({range:pricing.week}<={today}+21)*{range:pricing.booked_nights}*{range:pricing.avg_booked_rate})', 'money'),
    KPI('Revenue on the books, next 13 weeks', 'SUMPRODUCT({range:pricing.booked_nights},{range:pricing.avg_booked_rate})', 'money'),
    KPI('Rate changes this month', 'COUNTIFS({range:rate_changes.date},">="&%s,{range:rate_changes.date},"<="&{today})' % MS, 'int'),
    KPI('Average rate change, last 90 days', 'IFERROR(AVERAGEIFS({range:rate_changes.change_pct},{range:rate_changes.date},">="&({today}-90)),0)', 'pct'),
    KPI('Gap nights filled this month', 'SUMIFS({range:gaps.nights_free},{range:gaps.filled},%s,{range:gaps.date},">="&%s,{range:gaps.date},"<="&{today})' % (tok('yn', 'Yes'), MS), 'int'),
    KPI('Gap night revenue, 12 months', 'SUMIFS({range:gaps.recovered},{range:gaps.date},">="&({today}-365),{range:gaps.date},"<="&{today})', 'money'),
    KPI('Last-minute bookings this month', 'COUNTIFS({range:lastmin.check_in},">="&%s,{range:lastmin.check_in},"<"&%s)' % (MS, NXT), 'int'),
    KPI('Average last-minute discount', 'IFERROR(AVERAGE({range:lastmin.discount_pct}),0)', 'pct'),
    KPI('Direct bookings share this month', 'IFERROR(COUNTIFS({range:bookings.booked_on},">="&%s,{range:bookings.booked_on},"<"&%s,{range:bookings.channel},%s)/COUNTIFS({range:bookings.booked_on},">="&%s,{range:bookings.booked_on},"<"&%s),0)' % (MS, NXT, tok('chan', 'Direct'), MS, NXT), 'pct'),
    KPI('Average lead time in days', 'IFERROR(AVERAGEIFS({range:bookings.lead_days},%s),0)' % NC, 'int'),
    KPI('Average stay in nights', 'IFERROR(AVERAGEIFS({range:bookings.nights},%s),0)' % NC, 'num'),
    KPI('Weekend premium achieved', 'IFERROR((%s)/(%s)-1,0)' % (WE_ADR, WD_ADR), 'pct'),
    KPI('Event unit weeks sold out', 'COUNTIFS({range:pricing.demand_index},">=1.3",{range:pricing.free_nights},0)', 'int'),
    KPI('Units below break-even rate', 'COUNTIFS({range:breakeven.rate_flag},%s)' % ca('Below break-even'), 'int'),
    KPI('Average cleaning fee margin', 'IFERROR(AVERAGE({range:clean_fee.margin_pct}),0)', 'pct'),
    KPI('Comparable listings priced above us', 'COUNTIFS({range:comps.position},%s)' % ca('Priced above us'), 'int'),
    KPI('Active discount rules', 'COUNTIFS({range:discounts.active},%s)' % tok('yn', 'Yes'), 'int'),
    KPI('Price tests running', 'COUNTIFS({range:experiments.result},%s)' % tok('expres', 'Running'), 'int'),
    KPI('Average minimum stay on weekdays', 'IFERROR(AVERAGE({range:minstay.weekday_min}),0)', 'num'),
    KPI('Unit weeks on suggested rate', 'IFERROR(COUNTIFS(%s,{range:pricing.rate_flag},%s)/COUNTIFS(%s),0)' % (WKN(21), ca('On suggested rate'), WKN(21)), 'pct'),
]
assert len(kpis) == 29, len(kpis)
dashboard = {"title": "Pricing Dashboard", "kpis": kpis,
    "monthly": {"title": "Room, gap night, last-minute and direct offer revenue", "date": "unit_months.month", "series": [
        {"label": "Room revenue by month", "sum": "unit_months.room_revenue", "date": "unit_months.month"}, {"label": "Gap night revenue recovered", "sum": "gaps.recovered", "date": "gaps.date"},
        {"label": "Last-minute revenue", "sum": "lastmin.revenue", "date": "lastmin.check_in"}, {"label": "Direct offer revenue", "sum": "direct_offers.revenue", "date": "direct_offers.valid_from"}]},
    "breakdowns": [{"title": "Room revenue by city", "by": "unit_months.city", "value": "unit_months.room_revenue", "agg": "sum"}, {"title": "Nights booked by unit type", "by": "bookings.unit_type", "value": "bookings.nights", "agg": "sum"},
                   {"title": "Bookings by channel", "by": "bookings.channel", "value": "bookings.gross", "agg": "count"}, {"title": "Free nights ahead by unit", "by": "pricing.unit", "value": "pricing.free_nights", "agg": "sum"}]}
NCW = ('status', '<>', BS('Cancelled'))
insights = {"filters": [{"label": "Unit", "ref": "units.name"}, {"label": "City", "list": "city"}, {"label": "Channel", "list": "chan"}],
    "gauges": [{"title": "Occupancy of the weeks ahead", "num": AGG('sum', 'pricing', 'pricing.booked_nights', where=[('week', '>=', '{today}')]), "den": AGG('sum', 'pricing', 'pricing.week_nights', where=[('week', '>=', '{today}')])},
               {"title": "Unit weeks on the suggested rate", "num": AGG('count', 'pricing', where=[('rate_flag', '=', ca('On suggested rate'))]), "den": AGG('count', 'pricing')},
               {"title": "Gap nights filled", "num": AGG('count', 'gaps', where=[('filled', '=', tok('yn', 'Yes'))]), "den": AGG('count', 'gaps')},
               {"title": "Bookings at or above the wanted ADR", "num": AGG('count', 'bookings', where=[NCW, ('nightly_rate', '>=', '{set:target_adr}')]), "den": AGG('count', 'bookings', where=[NCW])},
               {"title": "Direct bookings share", "num": AGG('count', 'bookings', where=[NCW, ('channel', '=', tok('chan', 'Direct'))]), "den": AGG('count', 'bookings', where=[NCW])},
               {"title": "Weekend premium achieved", "num": AGG('count', 'weekday', where=[('lift_flag', '=', ca('Lift achieved'))]), "den": AGG('count', 'weekday', where=[('lift_flag', '<>', ca('Not a weekend'))])}],
    "charts": [
        CHART('Average nightly rate per month', 'line', 'month', [AGG('avg', 'bookings', 'bookings.nightly_rate', date='bookings.check_in', where=[NCW], label='Average nightly rate')]),
        CHART('ADR by season', 'bar', 'unit_months.season', [AGG('avg', 'unit_months', 'unit_months.adr', where=[('booked_nights', '>', 0)], label='ADR')]),
        CHART('ADR by city', 'bar', 'bookings.city', [AGG('avg', 'bookings', 'bookings.nightly_rate', where=[NCW], label='Average nightly rate')]),
        CHART('ADR by unit type', 'bar', 'bookings.unit_type', [AGG('avg', 'bookings', 'bookings.nightly_rate', where=[NCW], label='Average nightly rate')]),
        CHART('Occupancy by season', 'bar', 'unit_months.season', [AGG('avg', 'unit_months', 'unit_months.occupancy', label='Occupancy')]),
        CHART('Free nights per month ahead', 'column', 'month', [AGG('sum', 'pricing', 'pricing.free_nights', date='pricing.week', label='Free nights')]),
        CHART('Booked nights per month ahead', 'column', 'month', [AGG('sum', 'pricing', 'pricing.booked_nights', date='pricing.week', label='Booked nights')]),
        CHART('Room revenue per month', 'column', 'month', [AGG('sum', 'bookings', 'bookings.room_revenue', date='bookings.check_in', where=[NCW], label='Room revenue')]),
        CHART('Rate changes per month', 'column', 'month', [AGG('count', 'rate_changes', date='rate_changes.date', label='Rate changes')]),
        CHART('Average discount by rule type', 'bar', 'discounts.trigger', [AGG('avg', 'discounts', 'discounts.discount_pct', label='Discount')]),
        CHART('Bookings by lead time band', 'bar', 'bookings.lead_band', [AGG('count', 'bookings', where=[NCW], label='Bookings')]),
        CHART('Booked nights by check-in weekday', 'bar', 'weekday.weekday', [AGG('sum', 'weekday', 'weekday.booked_nights', label='Booked nights')]),
        CHART('Average stay by unit type', 'bar', 'bookings.unit_type', [AGG('avg', 'bookings', 'bookings.nights', where=[NCW], label='Average nights')]),
        CHART('Gap nights filled per month', 'column', 'month', [AGG('sum', 'gaps', 'gaps.nights_free', date='gaps.date', where=[('filled', '=', tok('yn', 'Yes'))], label='Gap nights filled')]),
        CHART('Comparable rate against our rate by city', 'bar', 'comps.city', [AGG('avg', 'comps', 'comps.gap_to_our_rate', label='Gap to our rate')]),
        CHART('Cleaning fee margin by unit type', 'bar', 'clean_fee.unit_type', [AGG('avg', 'clean_fee', 'clean_fee.margin_pct', label='Margin on the fee')]),
        CHART('Direct bookings share per month', 'line', 'month', [AGG('avg', 'bookings', 'bookings.is_direct', date='bookings.booked_on', where=[NCW], label='Direct share')]),
        CHART('RevPAR per month', 'line', 'month', [AGG('avg', 'unit_months', 'unit_months.revpar', date='unit_months.month', label='RevPAR')])]}
signature = [
    {"name": "Pricing calendar with season and event lifts", "why": "every unit and week shows the base rate, season factor, demand index, local event and the rate you listed", "where": "Pricing Calendar"},
    {"name": "Suggested rate per night", "why": "base rate, season, night type, demand, event and days to check-in become one rate to list, with raise, hold or lower", "where": "Nightly Rate Suggester"},
    {"name": "Event week pricing alert", "why": "local events with their demand lift, days to go and the free nights still listed, plus the rate to ask when few nights are left", "where": "Event Week Pricing"},
    {"name": "Gap-night discount engine", "why": "a free night between two bookings gets a discount that depends on how close it is, with the revenue gained and the lowest rate that still pays", "where": "Gap-Night Discount"},
    {"name": "Last-minute fill desk", "why": "days to check-in, free nights and occupancy decide whether to discount, with the profit of one stay after fees and turnover", "where": "Last-Minute Discount Decision"},
    {"name": "Break-even rate by unit", "why": "rent, utilities, other fixed cost and platform fees give the nightly rate and the occupancy at which each unit stops losing money", "where": "Break-Even Rates"},
    {"name": "Comparable listing position", "why": "weekday and weekend rates and review scores of listings near each unit, with the gap to your rate", "where": "Comparable Listings"},
    {"name": "Direct booking price against the platform", "why": "guest price, host income on each route, the platform fee saved and the largest discount that still earns the same", "where": "Direct Booking Price and Saving"},
    {"name": "Cleaning fee margin check", "why": "cleaner hours, supplies and linen against the fee charged, with the fee that reaches your margin target", "where": "Cleaning Fee Review"},
    {"name": "Price experiment log", "why": "each rate test with the nights booked, the occupancy and the revenue a week, so you keep the rates that worked", "where": "Price Experiments"}]
competitors = [
    {"what": "free occupancy templates", "lacks": "count nights and revenue but have no season factors, event lifts, suggested rates, gap-night or last-minute pricing and no break-even rate"},
    {"what": "subscription property-management software", "lacks": "charge every month and set rates by a hidden rule, so you cannot see why a rate was chosen or test your own discount rules"},
    {"what": "single-sheet booking trackers", "lacks": "list bookings but never compare the rate with the suggested rate, the comparables or the unit's break-even rate"},
    {"what": "generic expense spreadsheets", "lacks": "track costs but cannot turn rent, utilities and platform fees into the lowest rate a unit can charge"},
    {"what": "automatic pricing tools", "lacks": "move rates for you without the owner seeing the cleaning fee margin, the minimum stay rules or what each rate change earned"}]
guide = [
    'Open Start and type your company name and your own limits in the yellow cells: wanted occupancy and ADR, weekend lift, the discounts you usually give, the cleaner pay and your cleaning fee margin target.',
    'Check Units, Channels, Cities and Team. They hold your units, base rates and fixed costs, the platform fees and the people the other sheets look up.',
    'Fill Seasons with the price factor of each month. The suggested rates, the rate cards and the calculators read it.',
    'Keep the Pricing Calendar up to date every week: season, demand, local event, listed rate and the nights booked and free. Suggested rate, gap and fill check fill in.',
    'Log every booking on Bookings and each month of every unit on Unit Months. Occupancy, ADR (the average price of a night sold) and RevPAR (revenue per available night) calculate themselves.',
    'Write each rate change on Rate Changes with its reason. You see the change percent and the bookings made in the next 14 days.',
    'List local events on Local Events and read Comparable Listings after each check of nearby rates.',
    'Set discount rules on Discount Rules and minimum stays on Minimum-Stay Rules. Record each free night between two bookings on Gap Nights and each last-minute booking on Last-Minute Fills.',
    'Review Cleaning Fee Review and Break-Even Rates for every unit. Units below their break-even rate are flagged red.',
    'Use Direct Offers and Price Experiments to see which offers and which rate tests earned money. Weekday Pattern shows which check-in days fill.',
    f'Use the {len(tools)} calculators for the rate to list, event weeks, gap nights, last-minute offers, long stays, minimum stays, fees, break-even, comparables, direct prices and what-ifs.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Pricing Dashboard and Charts every week: rates, ADR, occupancy, free nights, discounts, gaps, direct share and RevPAR.']
listing = {"title": "Short-Term Rental Pricing Excel Template: Nightly Rates, Season Calendar, Break-Even, Gap Nights, Event Weeks, Direct Offers",
    "headline": "Price every unit and every week so no night is sold too cheap",
    "tags": ["short term rental", "vacation rental", "rental host", "pricing calendar", "nightly rate", "excel template", "rental pricing", "adr revpar", "occupancy tracker", "break even rate", "gap nights", "holiday let", "property host"],
    "description": ("Run the pricing side of a short-term or vacation rental business in one Excel workbook. Built for a host or co-host with 3 to 15 furnished units rented by the night through booking platforms and direct bookings. "
        "The Pricing Calendar shows every unit and every week with its base rate, season factor, demand index, local event, listed rate and booked and free nights, and works out the suggested rate, the gap to it and the revenue left on the table.\n\n"
        "Units, Unit Months and Bookings give occupancy, ADR (the average price of a night sold) and RevPAR (revenue per available night) for each unit and each month. Rate Changes logs every change with its reason and counts the bookings made in the next 14 days. "
        "Local Events and Comparable Listings show when demand rises and where your rate sits against nearby listings. Discount Rules, Minimum-Stay Rules, Gap Nights and Last-Minute Fills control discounts, and a gap night is a free night between two bookings. "
        "Cleaning Fee Review checks the margin on the cleaning fee, and Break-Even Rates finds the nightly rate and the occupancy at which each unit stops losing money after rent, utilities and platform fees. Direct Offers, Price Experiments and Weekday Pattern show which offers, tests and check-in days earn most.\n\n"
        f"{len(tools)} calculators cover the nightly rate to list, season and weekend lift, event weeks, gap nights, last-minute offers, long stays, minimum stays, cleaning fees, break-even, comparable listings, direct booking prices, the revenue impact of a rate change, rate cards and a rate and occupancy grid. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to guests, owners, the co-host (a helper who handles guests for a fee), the host and the accountant.\n\n"
        "This is part one of the Short-Term Rental Host suite. A standard .xlsx workbook with no macros and no subscription, 15 languages in one purchase, with a demo copy full of sample data for a small portfolio to explore first. It helps you plan your pricing and does not promise results."),
    "features": ["Pricing calendar with suggested rate per unit and week", "Season, weekend and event lifts", "ADR, occupancy and RevPAR by unit and month", "Break-even rate and occupancy by unit", "Gap-night and last-minute discount tools",
                 "Comparable listings and direct offers", "Cleaning fee margin check", "Price experiment log", f"{len(tools)} calculators for rates and discounts", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p1', slug='short-term-rental-pricing', profession='Short-Term Rental Host', name='Listings, Rates and Pricing Calendar',
         tagline='Price every unit and every week so no night is sold too cheap', price_usd=29,
         colors={"primary": "#264653", "accent": "#E9C46A"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 1, "of": 8, "focus": "Listings, rates and pricing calendar"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sr1.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
