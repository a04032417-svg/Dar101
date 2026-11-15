"""Car Rental Business suite - part 1: Enquiries, Quotes and Rate Card."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cr1_lists import *
from cr1_tables import settings, tables, MS, YES, NO, OPEN, QUOTED, BOOKED, LOST, DAILY, WEEKLY, MONTHLY, FLOOR_DAY
from cr1_tools import tools, CUR7
import cr1_data as D

SUITE = 'fx-20261115-car-rental'
NOTE = "Sample wording: adapt it to your own business. Check your local rules and your insurance terms."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
def R(t, c): return '{range:%s.%s}' % (t, c)
D90 = '{range:enquiries.date},">="&({today}-90)'
def CLSRATE(cls): return 'SUMIFS({range:classes.daily_rate},{range:classes.class},%s)' % cls
OWN = first_name(OWNER); MGR = first_name(MANAGER)
ACC = first_name([t for t in team if t['role'] == 'Accountant'][0]['name']); BKP = first_name([t for t in team if t['role'] == 'Bookkeeper'][0]['name'])

# ------------------------------------------------------------------ forms (12)
def FLR(t, idc): return 'SUMIFS({range:cost_floor.floor_price},{range:cost_floor.class},%s)' % LK(t, idc, 'class')
forms = [
    FORM('quote_sheet', 'Quote Sheet', 'Quote for a renter', 'quote_log.quote_id', F(
        ('Contact', 'quote_log.contact'), ('Quote date', 'quote_log.quote_date'), ('Class', 'quote_log.class'), ('Pickup date', 'quote_log.pickup_date'), ('Days', 'quote_log.days'), ('Pickup place', 'quote_log.location'),
        ('Season', 'quote_log.season'), ('Quote amount', 'quote_log.quote_amount'), ('Floor price for the stay', 'quote_log.floor_total'), ('Verdict', 'quote_log.verdict')) + [
        FF('Price a day quoted', 'IFERROR(%s/%s,0)' % (LK('quote_log', 'quote_id', 'quote_amount'), LK('quote_log', 'quote_id', 'days')), 'money'),
        FF('Floor price a day', FLR('quote_log', 'quote_id'), 'money'), FF('Lowest price a day to quote', 'ROUNDUP(%s,0)' % FLR('quote_log', 'quote_id'), 'money'),
        FF('Deposit held at pickup', LK('quote_log', 'quote_id', 'deposit'), 'money'), FF('Quote valid until', LK('quote_log', 'quote_id', 'valid_until'), 'date')]),
    FORM('rate_change_sheet', 'Rate Change Sheet', 'Rate change for one class and plan', 'rates.rate_id', F(
        ('Class', 'rates.class'), ('Plan', 'rates.plan'), ('Rate now', 'rates.rate'), ('Rate last year', 'rates.last_year_rate'), ('Rise this year', 'rates.rise_pct'), ('Floor price a day', 'rates.floor_price'),
        ('Rate after the planned rise', 'rates.new_rate'), ('New rates start', 'rates.change_date')) + [
        FF('Extra on each rental', '%s-%s' % (LK('rates', 'rate_id', 'new_rate'), LK('rates', 'rate_id', 'rate')), 'money'),
        FF('New day equivalent', 'ROUND(%s/%s,2)' % (LK('rates', 'rate_id', 'new_rate'), LK('rates', 'rate_id', 'days')), 'money'),
        FF('New day equivalent over the floor', 'ROUND(%s/%s-%s,2)' % (LK('rates', 'rate_id', 'new_rate'), LK('rates', 'rate_id', 'days'), LK('rates', 'rate_id', 'floor_price')), 'money'),
        FF('Planned rise', '{set:planned_rise}', 'pct')]),
    FORM('addon_price_sheet', 'Add-on Price Sheet', 'Price of one add-on', 'addons.addon', F(('Price a day', 'addons.price_day'), ('Cost a day', 'addons.unit_cost_day')) + [
        FF('Profit a day', '%s-%s' % (LK('addons', 'addon', 'price_day'), LK('addons', 'addon', 'unit_cost_day')), 'money'),
        FF('Profit share of the price', 'IFERROR((%s-%s)/%s,0)' % (LK('addons', 'addon', 'price_day'), LK('addons', 'addon', 'unit_cost_day'), LK('addons', 'addon', 'price_day')), 'pct'),
        FF('Price a day after the planned rise', 'ROUND(%s*(1+{set:planned_rise}),2)' % LK('addons', 'addon', 'price_day'), 'money'),
        FF('Profit per line in the add-on lines', 'IFERROR(INDEX({range:addon_profit.profit_per_line},MATCH({pick},{range:addon_profit.addon},0)),0)', 'money'),
        FF('Lines in the add-on lines', 'COUNTIFS({range:addon_lines.addon},{pick})', 'int'), FF('Revenue in the add-on lines', 'SUMIFS({range:addon_lines.amount},{range:addon_lines.addon},{pick})', 'money')]),
    FORM('season_change_sheet', 'Season Change Sheet', 'Season of one month of the year', 'month_season.moy', F(
        ('Month number', 'month_season.month_no'), ('Season', 'month_season.season'), ('Multiplier', 'month_season.multiplier'), ('Average day rate achieved', 'month_season.avg_day_rate'),
        ('Enquiries, 24 months', 'month_season.enquiries'), ('Booked from enquiries, 24 months', 'month_season.bookings'), ('Rate against the yearly average', 'month_season.rate_index')) + [
        FF('Compact daily rate in this season', 'ROUND(%s*%s,2)' % (CLSRATE('%s' % '{list:class.compact}'), LK('month_season', 'moy', 'multiplier')), 'money'),
        FF('Midsize SUV daily rate in this season', 'ROUND(%s*%s,2)' % (CLSRATE('{list:class.midsize_suv}'), LK('month_season', 'moy', 'multiplier')), 'money'),
        FF('Premium daily rate in this season', 'ROUND(%s*%s,2)' % (CLSRATE('{list:class.premium}'), LK('month_season', 'moy', 'multiplier')), 'money'),
        FF('Share of 24-month enquiries', 'IFERROR(%s/SUM({range:month_season.enquiries}),0)' % LK('month_season', 'moy', 'enquiries'), 'pct'),
        FF('Days to the next season change', 'MAX(0,{set:season_change_date}-{today})', 'int')]),
    FORM('enquiry_sheet', 'Enquiry Sheet', 'Enquiry with its quote', 'enquiries.enquiry_id', F(
        ('Date', 'enquiries.date'), ('Source', 'enquiries.source'), ('Contact', 'enquiries.contact'), ('Class wanted', 'enquiries.class'), ('Pickup date', 'enquiries.pickup_date'), ('Days', 'enquiries.days'),
        ('Pickup place', 'enquiries.location'), ('Quote amount', 'enquiries.quote_amount'), ('First reply hours', 'enquiries.first_reply_hours'), ('Status', 'enquiries.status'), ('Handled by', 'enquiries.staff')) + [
        FF('Quote a day', 'IFERROR(%s/%s,0)' % (LK('enquiries', 'enquiry_id', 'quote_amount'), LK('enquiries', 'enquiry_id', 'days')), 'money'),
        FF('Days from the enquiry to the pickup', '%s-%s' % (LK('enquiries', 'enquiry_id', 'pickup_date'), LK('enquiries', 'enquiry_id', 'date')), 'int'),
        FF('Hours over the reply target', 'MAX(0,%s-{set:reply_hours_target})' % LK('enquiries', 'enquiry_id', 'first_reply_hours'), 'num')]),
    FORM('followup_sheet', 'Follow-up Sheet', 'Follow-up of one open quote', 'open_quotes.enquiry', F(
        ('Contact', 'open_quotes.contact'), ('Source', 'open_quotes.source'), ('Class', 'open_quotes.class'), ('Quote amount', 'open_quotes.quote_amount'), ('Days waiting', 'open_quotes.days_waiting'),
        ('Value after decay', 'open_quotes.score'), ('Chase rank', 'open_quotes.chase_rank'), ('Verdict', 'open_quotes.verdict')) + [
        FF('Quote valid until', 'INDEX({range:enquiries.valid_until},MATCH({pick},{range:enquiries.enquiry_id},0))', 'date'),
        FF('Days left on the quote', 'INDEX({range:enquiries.valid_until},MATCH({pick},{range:enquiries.enquiry_id},0))-{today}', 'int'),
        FF('Value lost if it waits another day', 'ROUND(%s*{set:chase_decay},2)' % LK('open_quotes', 'enquiry', 'quote_amount'), 'money')]),
    FORM('lost_enquiry_sheet', 'Lost Enquiry Sheet', 'Lost enquiry and its reason', 'enquiries.enquiry_id', F(
        ('Date', 'enquiries.date'), ('Source', 'enquiries.source'), ('Contact', 'enquiries.contact'), ('Class wanted', 'enquiries.class'), ('Days', 'enquiries.days'), ('Quote amount', 'enquiries.quote_amount'),
        ('Status', 'enquiries.status'), ('Lost reason', 'enquiries.lost_reason'), ('Next free day', 'enquiries.next_free'), ('Handled by', 'enquiries.staff')) + [
        FF('Quote value lost to this reason, 90 days', 'IFERROR(INDEX({range:lost_reasons.revenue_lost},MATCH(%s,{range:lost_reasons.reason},0)),0)' % LK('enquiries', 'enquiry_id', 'lost_reason'), 'money'),
        FF('Lost enquiries of this reason, 90 days', 'IFERROR(INDEX({range:lost_reasons.lost_enquiries},MATCH(%s,{range:lost_reasons.reason},0)),0)' % LK('enquiries', 'enquiry_id', 'lost_reason'), 'int'),
        FF('Floor price a day of the class', FLR('enquiries', 'enquiry_id'), 'money')]),
    FORM('corporate_rate_sheet', 'Corporate Rate Sheet', 'Corporate rate for one class and plan', 'rates.rate_id', F(
        ('Class', 'rates.class'), ('Plan', 'rates.plan'), ('Rate', 'rates.rate'), ('Corporate rate', 'rates.account_rate'), ('Deposit', 'rates.deposit'), ('Floor price a day', 'rates.floor_price')) + [
        FF('Discount for corporate accounts', '{set:corporate_discount}', 'pct'), FF('Corporate day equivalent', 'ROUND(%s/%s,2)' % (LK('rates', 'rate_id', 'account_rate'), LK('rates', 'rate_id', 'days')), 'money'),
        FF('Corporate day equivalent over the floor', 'ROUND(%s/%s-%s,2)' % (LK('rates', 'rate_id', 'account_rate'), LK('rates', 'rate_id', 'days'), LK('rates', 'rate_id', 'floor_price')), 'money'),
        FF('Days until the invoice is paid', 'INDEX({range:channels.payout_days},MATCH({list:channel.corporate_account},{range:channels.channel},0))', 'int')]),
    FORM('longhire_sheet', 'Long-hire Sheet', 'Long-hire quote on the monthly plan', 'rates.rate_id', F(
        ('Class', 'rates.class'), ('Monthly rate', 'rates.monthly_rate'), ('Daily rate', 'rates.daily_rate'), ('Miles a day included', 'rates.miles_day'), ('Floor price a day', 'rates.floor_price'), ('Deposit', 'rates.deposit')) + [
        FF('Monthly plan price a day', 'ROUND(%s/30,2)' % LK('rates', 'rate_id', 'monthly_rate'), 'money'),
        FF('Discount against 30 daily rentals', 'IFERROR(1-%s/(30*%s),0)' % (LK('rates', 'rate_id', 'monthly_rate'), LK('rates', 'rate_id', 'daily_rate')), 'pct'),
        FF('Miles included in 30 days', '30*%s' % LK('rates', 'rate_id', 'miles_day'), 'int'), FF('Extra mileage fee a mile', '{set:extra_mile_fee}', 'money'),
        FF('Monthly plan price a day over the floor', 'ROUND(%s/30-%s,2)' % (LK('rates', 'rate_id', 'monthly_rate'), LK('rates', 'rate_id', 'floor_price')), 'money')]),
    FORM('event_rate_sheet', 'Event Rate Sheet', 'Weekend or event rate', 'events.event_id', F(
        ('Event', 'events.event'), ('Kind', 'events.kind'), ('Start', 'events.start'), ('End', 'events.end'), ('Uplift', 'events.uplift'), ('Days from today', 'events.days_away'), ('Days long', 'events.length_days')) + [
        FF('Compact rate in the event', 'ROUND(%s*(1+%s),2)' % (CLSRATE('{list:class.compact}'), LK('events', 'event_id', 'uplift')), 'money'),
        FF('Midsize SUV rate in the event', 'ROUND(%s*(1+%s),2)' % (CLSRATE('{list:class.midsize_suv}'), LK('events', 'event_id', 'uplift')), 'money'),
        FF('Premium rate in the event', 'ROUND(%s*(1+%s),2)' % (CLSRATE('{list:class.premium}'), LK('events', 'event_id', 'uplift')), 'money'),
        FF('Weekend uplift on short Friday pickups', '{set:weekend_uplift}', 'pct')]),
    FORM('price_match_sheet', 'Price Match Sheet', 'Room to match a price on one quote', 'quote_log.quote_id', F(
        ('Contact', 'quote_log.contact'), ('Class', 'quote_log.class'), ('Days', 'quote_log.days'), ('Quote amount', 'quote_log.quote_amount'), ('Floor price for the stay', 'quote_log.floor_total'),
        ('Margin over floor', 'quote_log.margin'), ('Margin over floor share', 'quote_log.margin_pct'), ('Verdict', 'quote_log.verdict')) + [
        FF('Room to give', 'MAX(0,%s)' % LK('quote_log', 'quote_id', 'margin'), 'money'),
        FF('Room to give a day', 'IFERROR(MAX(0,%s)/%s,0)' % (LK('quote_log', 'quote_id', 'margin'), LK('quote_log', 'quote_id', 'days')), 'money'),
        FF('Lowest total you can match to', LK('quote_log', 'quote_id', 'floor_total'), 'money'),
        FF('Share of the quote you can give', 'IFERROR(MAX(0,%s)/%s,0)' % (LK('quote_log', 'quote_id', 'margin'), LK('quote_log', 'quote_id', 'quote_amount')), 'pct')]),
    FORM('reply_check_sheet', 'Reply Check Sheet', 'First reply of one enquiry', 'enquiries.enquiry_id', F(
        ('Date', 'enquiries.date'), ('Source', 'enquiries.source'), ('Contact', 'enquiries.contact'), ('First reply hours', 'enquiries.first_reply_hours'), ('Hours to first reply band', 'enquiries.reply_band'),
        ('Slow reply', 'enquiries.slow_reply'), ('Status', 'enquiries.status'), ('Handled by', 'enquiries.staff')) + [
        FF('Reply target hours', '{set:reply_hours_target}', 'int'), FF('Hours over the reply target', 'MAX(0,%s-{set:reply_hours_target})' % LK('enquiries', 'enquiry_id', 'first_reply_hours'), 'num'),
        FF('Conversion of this band, 90 days', 'IFERROR(INDEX({range:reply_bands.conversion},MATCH(%s,{range:reply_bands.band},0)),0)' % LK('enquiries', 'enquiry_id', 'reply_band'), 'pct'),
        FF('Bookings lost to slow replies, 90 days', LK('enquiries', 'enquiry_id', 'lost_bookings'), 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('rental_quote_doc', 'Rental Quote', 'Rental quote for a renter', 'quote_log.quote_id', [
        'Rental quote of {set:company}, dated {today}. Quote {col:quote_log.quote_id} for {col:quote_log.contact}. Class: {col:quote_log.class}. Pickup: {col:quote_log.pickup_date} for {col:quote_log.days} days. Pickup place: {col:quote_log.location}.',
        'Price for the rental: {col:quote_log.quote_amount}, before any sales tax. Deposit held on your card at pickup: {col:quote_log.deposit}. The deposit is an amount held on a card or kept until the car is back.',
        'This quote is valid until {col:quote_log.valid_until}. Included miles are set by your hire terms. Extra mileage is charged at {set:extra_mile_fee} a mile over the allowance.',
        'Please read the rental terms summary. Check your local rules and your insurance terms before you drive.'], ['Manager', 'Renter'], NOTE),
    DOC('renter_rate_card_doc', 'Renter Rate Card', 'Rate card for renters, one class', 'rates.rate_id', [
        'Rate card of {set:company}, dated {today}. Class: {col:rates.class}. Seats: {col:rates.seats}.',
        'Daily rate: {col:rates.daily_rate}. Weekly rate: {col:rates.weekly_rate}. Monthly rate: {col:rates.monthly_rate}. All rates are before any sales tax and follow the season.',
        'Deposit: {col:rates.deposit}. Miles a day included: {col:rates.miles_day} (the demo unit is miles, set your own). Extra mileage: {set:extra_mile_fee} a mile.',
        'Delivery, extras and young-driver fees are on the price list. Rates can change with the season and for events.'], ['Manager', 'Renter'], NOTE),
    DOC('corporate_rate_doc', 'Corporate Rate Doc', 'Corporate rate sheet', 'rates.rate_id', [
        'Corporate rate sheet of {set:company}, dated {today}. Class: {col:rates.class}. Plan: {col:rates.plan}.',
        'Standard rate: {col:rates.rate}. Corporate account rate: {col:rates.account_rate}, a discount of {set:corporate_discount} on the daily rate. Rates are before any sales tax.',
        'Corporate accounts are invoiced and pay after the days agreed with us. Deposit rules are set in your account terms: {col:rates.deposit} for this class.',
        'The rates are reviewed once a year and we tell you before they change. Check your local rules and your own terms.'], ['Owner', 'Account contact'], NOTE),
    DOC('longhire_doc', 'Long-hire Offer', 'Long-hire offer on the monthly plan', 'rates.rate_id', [
        'Long-hire offer of {set:company}, dated {today}. Class: {col:rates.class}. Seats: {col:rates.seats}.',
        'Monthly plan: {col:rates.monthly_rate} for 30 days, before any sales tax. The same 30 days at the daily rate would cost 30 times {col:rates.daily_rate}.',
        'Miles included: {col:rates.miles_day} a day. Extra mileage: {set:extra_mile_fee} a mile over the allowance. Deposit: {col:rates.deposit}.',
        'Service, cleaning and swaps for a long hire are agreed in your hire terms. Check your local rules and your insurance terms.'], ['Manager', 'Renter'], NOTE),
    DOC('addon_list_doc', 'Add-ons Price List', 'Add-ons and extras price list', 'addons.addon', [
        'Extras price list of {set:company}, dated {today}. Extra: {col:addons.addon}.',
        'Price a day: {col:addons.price_day}, before any sales tax. A longer rental pays for a limited number of days, set in your hire terms.',
        'A young-driver fee and cover options are priced the same way. A cover option is an optional protection the renter can add, set by your own terms.',
        'Ask us for the full price list with every extra. Check your insurance terms for what a cover option includes.'], ['Manager', 'Renter'], NOTE),
    DOC('season_notice_doc', 'Seasonal Rates Notice', 'Seasonal rates notice', 'month_season.moy', [
        'Seasonal rates notice of {set:company}, dated {today}. Month: {col:month_season.moy}. Season: {col:month_season.season}.',
        'In this season the daily rate is the rate card price times {col:month_season.multiplier}. Rates are before any sales tax.',
        'The next season change is on {set:season_change_date}. Book early for peak and holiday dates because cars go first.',
        'Event weekends and holiday periods can carry an extra uplift. Ask us for the dates.'], ['Manager', 'Renter'], NOTE),
    DOC('followup_letter_doc', 'Quote Follow-up Letter', 'Quote follow-up letter', 'open_quotes.enquiry', [
        'Dear {col:open_quotes.contact}, this is {set:company}, dated {today}. We sent you a quote for a {col:open_quotes.class}: {col:open_quotes.quote_amount}, before any sales tax.',
        'Your quote has been open for {col:open_quotes.days_waiting} days. A car can be held for you if you still need one.',
        'If your plans changed or you found a better price, please tell us. We would like to learn from it.',
        'Thank you for thinking of us.'], ['Manager'], NOTE),
    DOC('event_offer_doc', 'Event Offer', 'Weekend and event offer', 'events.event_id', [
        'Event offer of {set:company}, dated {today}. Event: {col:events.event}, from {col:events.start} to {col:events.end}, {col:events.length_days} days.',
        'Cars are in demand for this event and rates carry an uplift of {col:events.uplift}. Rates are before any sales tax.',
        'Book early to keep a car of the class you want. A deposit is held on your card at pickup.',
        'Ask us for the rate of your class on these dates.'], ['Manager', 'Renter'], NOTE),
    DOC('terms_summary_doc', 'Rental Terms Summary', 'Rental terms summary', 'rates.rate_id', [
        'Rental terms summary of {set:company}, dated {today}. Class: {col:rates.class}. Plan: {col:rates.plan}.',
        'Deposit: {col:rates.deposit}, held on a card and released after the car is back. Miles a day included: {col:rates.miles_day}. Extra mileage: {set:extra_mile_fee} a mile over the allowance.',
        'Late return: {set:late_fee_hour} for each started hour after {set:late_grace_min} minutes. Cleaning fee when extra cleaning is needed: {set:cleaning_fee}. Fuel or charge level is checked at check-in.',
        'This is a short summary only. Read the full hire terms. Check your local rules and your insurance terms.'], ['Manager', 'Renter'], NOTE),
    DOC('price_change_doc', 'Price Change Notice', 'Price change notice', 'rates.rate_id', [
        'Price change notice of {set:company}, dated {today}. Class: {col:rates.class}. Plan: {col:rates.plan}.',
        'Rate now: {col:rates.rate}. New rate from {col:rates.change_date}: {col:rates.new_rate}, a rise of {set:planned_rise}. Rates are before any sales tax.',
        'Bookings made before the new rates start keep the old price.',
        'Thank you for renting with us.'], ['Owner'], NOTE),
    DOC('hotel_rate_doc', 'Hotel Partner Rate Sheet', 'Hotel partner rate sheet', 'channels.channel', [
        'Hotel partner rate sheet of {set:company}, dated {today}. Channel: {col:channels.channel}.',
        'Commission share kept by the partner: {col:channels.fee_pct}. Days until the commission statement is settled: {col:channels.payout_days}.',
        'Your guests rent at the rate card for the season. Rates are before any sales tax and a deposit is held on the guest card at pickup.',
        'We send a statement each month. Ask us if you need a rate for a group.'], ['Owner', 'Partner'], NOTE),
    DOC('fleet_guide_doc', 'Fleet and Class Guide', 'One-page fleet and class guide', 'rates.rate_id', [
        'Fleet and class guide of {set:company}, dated {today}. Class: {col:rates.class}.',
        'Seats: {col:rates.seats}. Miles a day included: {col:rates.miles_day}. Deposit: {col:rates.deposit}.',
        'Daily rate: {col:rates.daily_rate}. Weekly rate: {col:rates.weekly_rate}. Monthly rate: {col:rates.monthly_rate}. Rates are before any sales tax.',
        'Ask us which class suits your trip. Delivery to a hotel, the airport or your home can be arranged for a fee per leg.'], ['Manager'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('new_enquiry_chk', 'New Enquiry Reply Steps', 'enquiries', 'enquiries.date', [('Read the enquiry and the dates', 0), ('Check a car of the class is free', 0), ('Reply within your target hours', 0), ('Send the quote', 0), ('Note the quote valid until date', 0), ('Follow up if no answer', 2)]),
    CHK('prepare_quote_chk', 'Preparing a Quote Steps', 'quote_log', 'quote_log.quote_date', [('Choose the class and the dates', 0), ('Check the season and any event', 0), ('Add delivery, add-ons and the young-driver fee', 0), ('Check the price against the floor price', 0), ('Send the written quote', 0), ('Set the valid until date', 0)]),
    CHK('quote_followup_chk', 'Quote Follow-up Steps', 'enquiries', 'enquiries.date', [('Call or text the quote that is worth most', 1), ('Ask if the dates changed', 1), ('Offer another class if the car is gone', 2), ('Offer the weekly price if it is cheaper', 2), ('Note the answer', 3), ('Close the quote as booked or lost', 7)]),
    CHK('weekly_rate_chk', 'Weekly Rate Review Steps', 'funnel', 'funnel.month', [('Open the Rate Card and the Cost per Day by Class', 0), ('Check each class against its floor price', 1), ('Run the Seasonal Rate Checker', 1), ('Check idle days by class', 2), ('Decide which rates move', 3), ('Write the decisions in the pricing notes', 4)]),
    CHK('season_change_chk', 'Season Change Steps', 'events', 'events.start', [('Check the multipliers of the new season', -30), ('Update the season calendar', -21), ('Tell the hotel partner and the marketplace support', -14), ('Update the online listing prices', -7), ('Send the price change notice to renters', -7), ('Check the first quotes of the season', 3)]),
    CHK('event_weekend_chk', 'Event Weekend Pricing Steps', 'events', 'events.start', [('Count cars booked against cars available', -21), ('Run the Event Uplift Planner', -21), ('Set the weekend rate', -14), ('Check the minimum stay', -14), ('Tell the manager the new rate', -14), ('Review the result after the event', 3)]),
    CHK('addon_review_chk', 'Add-on Review Steps', 'addon_lines', 'addon_lines.start_date', [('Open the Add-on Profit sheet', 0), ('Rank add-ons by profit per line', 0), ('Check the stock of the best add-ons', 3), ('Check the price against the cost', 3), ('Set the upsell target per booking', 7), ('Brief the booking assistant on what to offer', 7)]),
    CHK('corporate_setup_chk', 'Corporate Account Setup Steps', 'enquiries', 'enquiries.date', [('Agree the corporate rate with the account', 0), ('Agree the days to pay the invoice', 0), ('Record the contact and the rate card class', 1), ('Send the corporate rate sheet', 1), ('Check the first booking invoice', 14), ('Review the rate once a year', 365)]),
    CHK('longhire_chk', 'Long-hire Quote Steps', 'quote_log', 'quote_log.quote_date', [('Check the days and the miles expected', 0), ('Use the Long-hire Quote tool', 0), ('Check the plan price against the floor', 0), ('Send the long-hire offer', 1), ('Agree service and cleaning during the hire', 3), ('Follow up after three days', 4)]),
    CHK('lost_review_chk', 'Lost Enquiry Review Steps', 'enquiries', 'enquiries.date', [('Note the lost reason', 0), ('Send the polite message asking why', 1), ('Record the answer', 3), ('Check the reason in the Lost Enquiry Analyser', 7), ('Choose one cause to fix', 14), ('Review again next month', 30)]),
    CHK('pricing_meeting_chk', 'Monthly Pricing Meeting Steps', 'funnel', 'funnel.month', [('Open the Quotes Dashboard', 28), ('Read conversion and reply hours', 28), ('Check quotes below the floor price', 28), ('Check the rate rise planner', 29), ('Decide on rates and add-ons', 30), ('Tell the team what changed', 31)]),
    CHK('one_car_chk', 'One-car Host First Week Steps', 'enquiries', 'enquiries.date', [('Keep one class and one channel in the sheets', 0), ('Set your daily rate and deposit', 0), ('Work out your floor price', 1), ('Log every enquiry with the hours to reply', 1), ('Send your first quote', 2), ('Review the week and your lost enquiries', 7)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('thanks', 'Renter: thank you for your enquiry', 'enquiries', 'enquiries.phone', 'Hello {contact}, thank you for your enquiry. We will reply within {reply_hours} hours. {company}'),
    M('your_quote', 'Renter: your quote', 'enquiries', 'enquiries.phone', 'Hello {contact}, your quote for a {class} from {pickup_date} for {days} days is {quote_amount}. {company}'),
    M('booked_out', 'Renter: fully booked, next free day', 'enquiries', 'enquiries.phone', 'Hello {contact}, we are fully booked for a {class} on those dates. The next free day is {next_free}. {company}'),
    M('other_class', 'Renter: another class for your dates', 'enquiries', 'enquiries.phone', 'Hello {contact}, we can offer a {class_alt} for your dates instead of a {class}. Shall we hold it? {company}'),
    M('price_sorry', 'Renter: we could not meet your price', 'enquiries', 'enquiries.phone', 'Hello {contact}, we are sorry we could not meet your price. May we ask what you needed? {company}'),
    M('find_us', 'Renter: how did you find us', 'enquiries', 'enquiries.phone', 'Hello {contact}, how did you find us? A short answer helps us a lot. {company}'),
    M('corp_rate', 'Corporate account: your agreed rate', 'enquiries', 'enquiries.phone', 'Hello {contact}, your agreed rate for a {class} is {account_rate} a day, before any sales tax. {company}'),
    M('corp_review', 'Corporate account: the rate review', 'enquiries', 'enquiries.phone', 'Hello {contact}, we review our corporate rates for {rate_year}. May we send you our proposal? {company}'),
    M('owner_slow', 'Owner: what slow replies cost', 'enquiries', 'enquiries.owner_phone', 'Hello %s, slow replies cost about {lost_bookings} bookings in the last 90 days. {company}' % OWN),
    M('owner_weekend', 'Owner: weekend pickups booked', 'enquiries', 'enquiries.owner_phone', 'Hello %s, the weekend pickups booked in the last 90 days are {weekend_booked}. {company}' % OWN),
    M('mgr_noreply', 'Manager: enquiries with no reply', 'enquiries', 'enquiries.manager_phone', 'Hello %s, the enquiry of {contact} has had no reply for {waiting_hours} hours. Please reply today. {company}' % MGR),
    M('valid_until', 'Renter: your quote is valid until', 'quote_log', 'quote_log.phone', 'Hello {contact}, your quote of {quote_amount} for a {class} is valid until {valid_until}. {company}'),
    M('hold_car', 'Renter: shall we hold the car', 'quote_log', 'quote_log.phone', 'Hello {contact}, we still have a {class} for your dates. Shall we hold it for you? {company}'),
    M('weekly_cheaper', 'Renter: the weekly price is cheaper', 'quote_log', 'quote_log.phone', 'Hello {contact}, for {days} days a {class} costs {daily_total} at the daily rate. The weekly price is {weekly_price}. {company}'),
    M('addon_seat', 'Renter: add a child seat', 'quote_log', 'quote_log.phone', 'Hello {contact}, a child seat can be added for {addon_price} a day. {company}'),
    M('delivery_fee', 'Renter: delivery fee', 'quote_log', 'quote_log.phone', 'Hello {contact}, delivery to {location} costs {fee_leg} each way. {company}'),
    M('deposit_held', 'Renter: deposit held at pickup', 'quote_log', 'quote_log.phone', 'Hello {contact}, a deposit of {deposit} is held on your card at pickup and released after the return. {company}'),
    M('price_change', 'Renter: prices change, book now', 'quote_log', 'quote_log.phone', 'Hello {contact}, our prices change on {change_date}. Booking now saves about {saving}. {company}'),
    M('confirmed', 'Renter: your booking is confirmed', 'quote_log', 'quote_log.phone', 'Hello {contact}, thank you, your booking from {pickup_date} is confirmed. {company}'),
    M('weekend_rate', 'Renter: a weekend rate applies', 'quote_log', 'quote_log.phone', 'Hello {contact}, a weekend rate applies from {event_start}. Booking early keeps your price. {company}'),
    M('monthly_plan', 'Renter: our monthly plan', 'quote_log', 'quote_log.phone', 'Hello {contact}, our monthly plan for a {class} is {monthly_price}. {company}'),
    M('young_fee', 'Renter: young-driver fee', 'quote_log', 'quote_log.phone', 'Hello {contact}, a young-driver fee of {young_fee} a day applies. {company}'),
    M('unanswered', 'Renter: your quote has not been answered', 'open_quotes', 'open_quotes.phone', 'Hello {contact}, your quote of {quote_amount} for a {class} is still open. Do you still need a car? {company}'),
    M('owner_open', 'Owner: quotes waiting for a reply', 'open_quotes', 'open_quotes.owner_phone', 'Hello %s, {open_n} quotes worth {open_value} are waiting for a reply. {company}' % OWN),
    M('mgr_chase', 'Manager: chase the open quotes today', 'open_quotes', 'open_quotes.manager_phone', 'Hello %s, please chase the open quotes today: {open_n} are waiting, worth {open_value}. {company}' % MGR),
    M('owner_floor', 'Owner: the cost floor of a class', 'rates', 'rates.owner_phone', 'Hello %s, the cost floor for {class} is {floor_price} a day. {company}' % OWN),
    M('mgr_newcard', 'Manager: the new rate card starts', 'rates', 'rates.manager_phone', 'Hello %s, the new rate card starts on {change_date}. {company}' % MGR),
    M('market_price', 'Marketplace support: listing prices', 'rates', 'rates.market_phone', 'Hello, the listing price for {class} changes on {change_date}. The new {plan} rate is {new_rate}. {company}'),
    M('acc_rates', 'Accountant: rate card changes', 'rates', 'rates.accountant_phone', 'Hello %s, rate card changes for {rate_year}: {class}, {plan}, from {rate} to {new_rate}. {company}' % ACC),
    M('hotel_season', 'Hotel partner: guests rates for a season', 'month_season', 'month_season.hotel_phone', 'Hello, your guests rates for the {season} season are the rate card times {multiplier}. {company}'),
    M('hotel_statement', 'Hotel partner: commission statement', 'month_season', 'month_season.hotel_phone', 'Hello, the commission statement for {moy} is ready for you. {company}'),
    M('mgr_addons', 'Manager: what add-ons earned', 'addon_lines', 'addon_lines.manager_phone', 'Hello %s, add-ons earned {addon_profit} in profit last month. {company}' % MGR),
    M('acc_addons', 'Accountant: add-on revenue by month', 'addon_lines', 'addon_lines.accountant_phone', 'Hello %s, add-on revenue for the month of {month} was {month_revenue}. {company}' % ACC),
    M('bkp_seasons', 'Bookkeeper: record the new season dates', 'events', 'events.bookkeeper_phone', 'Hello %s, please record the new season dates: {event} from {start} to {end}. {company}' % BKP),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
EN = lambda c: '{range:enquiries.%s}' % c
BOOK90 = 'COUNTIFS(%s,%s,%s)' % (EN('status'), BOOKED, D90)
Q90 = 'COUNTIFS(%s,">0",%s)' % (EN('quote_amount'), D90)
LOSTSUM = 'SUM({range:lost_reasons.lost_enquiries})'
def LSH(r): return 'IFERROR(SUMIFS({range:lost_reasons.lost_enquiries},{range:lost_reasons.reason},%s)/%s,0)' % (tok('lostreason', r), LOSTSUM)
UPT3 = 'IFERROR(COUNTIFS({range:addon_lines.first_line},%s,{range:addon_lines.month},">="&EDATE(%s,-2))/SUMIFS({range:funnel.bookings_all},{range:funnel.month},">="&EDATE(%s,-2)),0)' % (YES, MS, MS)
kpis = [
    KPI('Enquiries this month', 'COUNTIFS(%s,%s)' % (EN('month'), MS), 'int'),
    KPI('Enquiries last 30 days', 'COUNTIFS(%s,">="&({today}-30))' % EN('date'), 'int'),
    KPI('Enquiries waiting for a first reply', 'COUNTIFS(%s,%s)' % (EN('status'), OPEN), 'int', alert={"when": "> 5", "style": "warn"}),
    KPI('Average hours to first reply, 90 days', 'IFERROR(AVERAGEIFS(%s,%s,%s,"<>"&%s),0)' % (EN('first_reply_hours'), D90, EN('status'), OPEN), 'num'),
    KPI('Replies within the target hours, 90 days', 'IFERROR(COUNTIFS(%s,"<="&{set:reply_hours_target},%s,"<>"&%s,%s)/COUNTIFS(%s,"<>"&%s,%s),0)' % (EN('first_reply_hours'), EN('status'), OPEN, D90, EN('status'), OPEN, D90), 'pct'),
    KPI('Open quotes now', 'COUNTIFS(%s,%s)' % (EN('status'), QUOTED), 'int'),
    KPI('Value of open quotes', 'SUMIFS(%s,%s,%s)' % (EN('quote_amount'), EN('status'), QUOTED), 'money'),
    KPI('Quotes sent this month', 'COUNTIFS(%s,%s,%s,">0")' % (EN('month'), MS, EN('quote_amount')), 'int'),
    KPI('Quote to booking conversion, 90 days', 'IFERROR(%s/%s,0)' % (BOOK90, Q90), 'pct'),
    KPI('Enquiry to booking conversion, 90 days', 'IFERROR(%s/COUNTIFS(%s),0)' % (BOOK90, D90), 'pct', alert={"when": "< {set:conv_target}", "style": "warn"}),
    KPI('Bookings from own channels, 90 days', BOOK90, 'int'),
    KPI('Lost enquiries, 90 days', 'COUNTIFS(%s,%s,%s)' % (EN('status'), LOST, D90), 'int'),
    KPI('Quote value lost, 90 days', 'SUMIFS(%s,%s,%s,%s)' % (EN('quote_amount'), EN('status'), LOST, D90), 'money'),
    KPI('Share lost to price, 90 days', LSH('Price'), 'pct'), KPI('Share lost to no car free, 90 days', LSH('No car free'), 'pct'), KPI('Share lost to no reply, 90 days', LSH('No reply'), 'pct'),
    KPI('Best source by booked value', 'IFERROR(INDEX({range:sources.source},MATCH(MAX({range:sources.revenue}),{range:sources.revenue},0)),"")', 'text'),
    KPI('Average quote amount, 90 days', 'IFERROR(AVERAGEIFS(%s,%s,">0",%s),0)' % (EN('quote_amount'), EN('quote_amount'), D90), 'money'),
    KPI('Average days quoted, 90 days', 'IFERROR(AVERAGEIFS(%s,%s,">0",%s),0)' % (EN('days'), EN('quote_amount'), D90), 'num'),
    KPI('Quotes below the floor price this month', 'COUNTIFS({range:quote_log.verdict},%s,{range:quote_log.quote_date},">="&%s)' % (ka('Below floor'), MS), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Rate card rise this year', 'IFERROR(SUM({range:rates.rate})/SUM({range:rates.last_year_rate})-1,0)', 'pct'),
    KPI('Weekend share of bookings, 90 days', 'IFERROR(COUNTIFS(%s,%s,%s,%s,%s)/%s,0)' % (EN('weekend'), YES, EN('status'), BOOKED, D90, BOOK90), 'pct'),
    KPI('Add-on revenue this month', 'SUMIFS({range:addon_lines.amount},{range:addon_lines.month},%s)' % MS, 'money'),
    KPI('Add-on revenue per booking, 3 months', CUR7, 'money', alert={"when": "< {set:addon_target}", "style": "warn"}),
    KPI('Best add-on by profit', 'IFERROR(INDEX({range:addon_profit.addon},MATCH(MAX({range:addon_profit.profit}),{range:addon_profit.profit},0)),"")', 'text'),
    KPI('Add-on uptake, 3 months', UPT3, 'pct'),
    KPI('Young-driver bookings, 90 days', 'COUNTIFS({range:addon_lines.addon},%s,{range:addon_lines.start_date},">="&({today}-90),{range:addon_lines.start_date},"<="&{today})' % tok('addon', 'Young-driver fee'), 'int'),
    KPI('Next event, days away', 'IFERROR(SMALL({range:events.start},COUNTIFS({range:events.start},"<"&{today})+1)-{today},0)', 'int'),
    KPI('Days to the next season change', 'MAX(0,{set:season_change_date}-{today})', 'int'),
    KPI('Cost floor for the Premium class', 'SUMIFS({range:cost_floor.floor_price},{range:cost_floor.class},%s)' % tok('class', 'Premium'), 'money'),
]
assert len(kpis) == 30
dashboard = {"title": "Quotes Dashboard", "kpis": kpis,
    "monthly": {"title": "Enquiries, quotes and bookings by month", "date": "funnel.month", "series": [
        {"label": "Enquiries", "sum": "funnel.enquiries", "date": "funnel.month"}, {"label": "Quoted", "sum": "funnel.quoted", "date": "funnel.month"},
        {"label": "Booked from enquiries", "sum": "funnel.booked", "date": "funnel.month"}, {"label": "Lost", "sum": "funnel.lost", "date": "funnel.month"}]},
    "breakdowns": [{"title": "Enquiries by source", "by": "enquiries.source", "agg": "count"}, {"title": "Enquiries by status", "by": "enquiries.status", "agg": "count"},
                   {"title": "Quote value lost by reason", "by": "lost_reasons.reason", "value": "lost_reasons.revenue_lost", "agg": "sum"}, {"title": "Add-on profit by add-on", "by": "addon_lines.addon", "value": "addon_lines.profit", "agg": "sum"}]}
OPENS, NOTOPEN = OPEN, '{list:estatus.open}'
insights = {"filters": [{"label": "Class", "list": "class"}, {"label": "Source", "list": "source"}, {"label": "Season", "list": "season"}],
    "gauges": [
        {"title": "Replies within the target hours", "num": AGG('count', 'enquiries', where=[('first_reply_hours', '<=', '{set:reply_hours_target}'), ('status', '<>', OPEN)]), "den": AGG('count', 'enquiries', where=[('status', '<>', OPEN)])},
        {"title": "Quotes that became bookings", "num": AGG('count', 'enquiries', where=[('status', '=', BOOKED)]), "den": AGG('count', 'enquiries', where=[('quote_amount', '>', 0)])},
        {"title": "Quotes above the floor price", "num": AGG('count', 'quote_log', where=[('margin', '>=', 0)]), "den": AGG('count', 'quote_log')},
        {"title": "Add-on profit kept from revenue", "num": AGG('sum', 'addon_lines', 'addon_lines.profit'), "den": AGG('sum', 'addon_lines', 'addon_lines.amount')},
        {"title": "Enquiries answered the same day", "num": AGG('count', 'enquiries', where=[('first_reply_hours', '<=', 12), ('status', '<>', OPEN)]), "den": AGG('count', 'enquiries', where=[('status', '<>', OPEN)])},
        {"title": "Weekend cars booked", "num": AGG('count', 'enquiries', where=[('weekend', '=', YES), ('status', '=', BOOKED)]), "den": AGG('count', 'enquiries', where=[('weekend', '=', YES)])}],
    "charts": [
        CHART('Enquiries per month', 'column', 'month', [AGG('sum', 'funnel', 'funnel.enquiries', date='funnel.month', label='Enquiries')]),
        CHART('Enquiries by source', 'bar', 'enquiries.source', [AGG('count', 'enquiries', label='Enquiries')]),
        CHART('Enquiries by class wanted', 'bar', 'enquiries.class', [AGG('count', 'enquiries', label='Enquiries')]),
        CHART('Enquiries by status', 'bar', 'enquiries.status', [AGG('count', 'enquiries', label='Enquiries')]),
        CHART('Lost enquiries by reason, 90 days', 'bar', 'lost_reasons.reason', [AGG('sum', 'lost_reasons', 'lost_reasons.lost_enquiries', label='Lost enquiries')]),
        CHART('Quote value lost by reason, 90 days', 'bar', 'lost_reasons.reason', [AGG('sum', 'lost_reasons', 'lost_reasons.revenue_lost', label='Quote value lost')]),
        CHART('Bookings from enquiries per month', 'column', 'month', [AGG('sum', 'funnel', 'funnel.booked', date='funnel.month', label='Booked from enquiries')]),
        CHART('Conversion per month', 'line', 'month', [AGG('avg', 'funnel', 'funnel.conversion', date='funnel.month', label='Conversion')]),
        CHART('Average first reply hours per month', 'line', 'month', [AGG('avg', 'funnel', 'funnel.avg_reply_hours', date='funnel.month', label='Reply hours')]),
        CHART('Average quote amount per month', 'line', 'month', [AGG('avg', 'funnel', 'funnel.avg_quote', date='funnel.month', label='Average quote')]),
        CHART('Enquiries by pickup weekday', 'bar', 'weekday_demand.weekday', [AGG('sum', 'weekday_demand', 'weekday_demand.enquiries', label='Enquiries')]),
        CHART('Quotes sent by class', 'bar', 'enquiries.class', [AGG('count', 'enquiries', where=[('quote_amount', '>', 0)], label='Quotes')]),
        CHART('Add-on revenue per month', 'column', 'month', [AGG('sum', 'addon_lines', 'addon_lines.amount', date='addon_lines.month', label='Add-on revenue')]),
        CHART('Add-on profit by add-on', 'bar', 'addon_lines.addon', [AGG('sum', 'addon_lines', 'addon_lines.profit', label='Add-on profit')]),
        CHART('Add-on lines by add-on', 'bar', 'addon_lines.addon', [AGG('count', 'addon_lines', label='Add-on lines')]),
        CHART('Add-on revenue by channel', 'bar', 'addon_lines.channel', [AGG('sum', 'addon_lines', 'addon_lines.amount', label='Add-on revenue')]),
        CHART('Enquiries by season of the pickup', 'bar', 'enquiries.season', [AGG('count', 'enquiries', label='Enquiries')]),
        CHART('Enquiries by staff member', 'bar', 'enquiries.staff', [AGG('count', 'enquiries', label='Enquiries')]),
        CHART('Daily rate by class', 'bar', 'rates.class', [AGG('sum', 'rates', 'rates.rate', where=[('plan', '=', DAILY)], label='Daily rate')]),
        CHART('Day equivalent by plan', 'bar', 'rates.plan', [AGG('avg', 'rates', 'rates.day_equivalent', label='Day equivalent')]),
        CHART('Rate rise by class', 'bar', 'rates.class', [AGG('avg', 'rates', 'rates.rise_pct', label='Rate rise')]),
        CHART('Open quotes by class', 'bar', 'enquiries.class', [AGG('count', 'enquiries', where=[('status', '=', QUOTED)], label='Open quotes')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Instant quote builder", "why": "class, dates, season, delivery and add-ons give a total, the deposit and a floor price check in one step", "where": "Instant Quote Builder"},
    {"name": "Cost-based floor price", "why": "the lowest price a day that covers your own cost at your utilisation, with five utilisation steps", "where": "Cost-Based Floor Price"},
    {"name": "Seasonal rate card checker", "why": "every class and season set against the floor and what booked quotes paid, with raise, hold or lower", "where": "Seasonal Rate Checker"},
    {"name": "Weekly and monthly discount tester", "why": "short rentals against a week and a month by revenue per available day, so a step is never guessed", "where": "Discount Step Tester"},
    {"name": "Add-on profit ranker", "why": "add-ons ranked by profit per line with the uptake that pays for the stock", "where": "Add-on Profit Ranker"},
    {"name": "Lost-enquiry cause analyser", "why": "quote value lost by cause and the cause worth fixing first, from your own enquiries", "where": "Lost Enquiry Analyser"},
    {"name": "Four-week quote forecast", "why": "your own enquiries, trend and conversion give bookings and revenue per week in Base, Best and Worst", "where": "Four-Week Forecast"},
    {"name": "Reply-time impact", "why": "conversion by hours to the first reply and the bookings a year slow replies cost", "where": "Reply Time Impact"},
    {"name": "Quote follow-up list", "why": "open quotes ranked by value after a decay for each day they wait, so the best call comes first", "where": "Quote Follow-up List"},
    {"name": "Minimum rental days solver", "why": "the days a rental must last to pay for the preparation, cleaning and delivery of the pickup", "where": "Minimum Days Solver"}]
competitors = [
    {"what": "generic booking calendar templates", "lacks": "hold dates but know nothing of quotes, floor prices, seasons, add-ons or lost enquiries"},
    {"what": "subscription rental-management software", "lacks": "charge each month or per vehicle and cannot test a rate, a discount step or a minimum stay before you use it"},
    {"what": "single-sheet vehicle expense logs", "lacks": "list costs but never turn them into a cost per rented day and a floor price for a quote"},
    {"what": "budget-model templates", "lacks": "plan a year of money but have no enquiry log, no reply times and no conversion by source"},
    {"what": "free rate-card tables", "lacks": "show one price and never the weekly and monthly day equivalents, the rise against last year or the season multipliers"}]
guide = [
    'Open Start and type your business name, your reply target, the margin you add on cost and the date of your next rate rise in the yellow cells.',
    'Check Vehicle Classes, Seasons, Add-ons, Delivery Zones and Channels: they hold the daily rates, deposits, multipliers and fees every quote uses.',
    'Open Rate Card and Cost per Day by Class. Type your own cost per rented day and the floor price of each class is worked out.',
    'Log every enquiry in Enquiries with the source, the class wanted, the dates, the quote and the hours to the first reply.',
    'Add each quote you send to Quote Log and read the verdict: above floor, thin margin or below floor.',
    'List the quotes still open in Open Quotes and call the one ranked first.',
    'Update Funnel by Month each month with the totals of the month so conversion and reply hours stay current.',
    'Keep Add-on Lines up to date, then rank add-ons in Add-on Profit and use the Upsell Target.',
    'Use the Instant Quote Builder for every quote and the Price Match Test when a renter shows a lower price.',
    f'Use the {len(tools)} calculators for pricing decisions, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'Read the Quotes Dashboard and the Charts sheet every week: conversion, reply hours, lost enquiries, add-ons and open quotes.',
    'A one-car host can use the same sheets with one class and one channel and delete the rows that do not apply.']
listing = {"title": "Car Rental Quotes and Rate Card Excel Template: Enquiry Log, Cost Floor Price, Seasonal Rates, Add-on Profit, Lost Enquiries",
    "headline": "Quote every rental at a price that clears your cost and win more enquiries",
    "tags": ["car rental", "rental quote", "rate card", "excel template", "car hire", "fleet pricing", "floor price", "enquiry tracker", "van rental", "rental business", "seasonal rates", "add-on profit", "car sharing host"],
    "description": ("Run the pricing and enquiry side of a small car or van rental in one Excel workbook. Built for an owner-operator and a manager who answer enquiries, send quotes and keep a rate card by class, plan and season. "
        "Enquiries logs every enquiry with its source, class wanted, dates, quote and hours to the first reply, and works out the reply band and a weekend flag. Quote Log sets every quote against the floor price for the stay and gives a verdict. "
        "Rate Card holds the daily, weekly and monthly rate of every class against last year with the day equivalent and the rise. Cost per Day by Class turns your loan, insurance, upkeep, cleaning, energy and depreciation into a cost per rented day and a floor price.\n\n"
        "Season Calendar and Month Seasonality show multipliers, holiday periods and event weekends. Add-on Lines and Add-on Profit rank add-ons by profit per line. Funnel by Month, Lost Reasons, Source Conversion, Reply Time Bands, Open Quotes, Discount Steps and Weekday Demand show where enquiries are won and lost.\n\n"
        f"{len(tools)} calculators answer weekly questions with a clear verdict: the instant quote, the cost floor, the seasonal rate check, the weekly and monthly discount step, the add-on ranking, the upsell target, the young-driver fee, the funnel, lost enquiries, reply time, sources, follow-ups, price match, rate rise, long hire, minimum days and a four-week forecast. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to renters, corporate accounts, a hotel partner, marketplace support, the owner, the manager, the accountant and the bookkeeper.\n\n"
        "This is part one of the Car Rental Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Renters appear by first name and initial only. It helps you keep track of your pricing and does not promise results. Check your local rules and your insurance terms; confirm tax questions with your adviser."),
    "features": ["Enquiry log with hours to first reply", "Instant quote with a floor price check", "Cost per rented day by class", "Rate card by class, plan and season", "Add-on profit per line and upsell target",
                 "Lost enquiries by reason and revenue lost", "Weekly and monthly discount step tester", f"{len(tools)} calculators for pricing decisions", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "Four-week forecast with Base, Best and Worst"]}
s = spec(id=f'{SUITE}-p1', slug='car-rental-quotes', profession='Car Rental Business', name='Enquiries, Quotes and Rate Card',
         tagline='Quote every rental at a price that clears your cost and win more enquiries', price_usd=29,
         colors={"primary": "#1D3557", "accent": "#E63946"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 1, "of": 8, "focus": "Enquiries, quotes and rate card"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cr1.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
