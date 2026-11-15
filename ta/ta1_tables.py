"""Travel agent suite part 1: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ta1_lists import *
import ta1_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def OWN(): return CA('owner_phone', 'Owner phone', 'text', '"%s"' % D.OWNER_PHONE, 18)
def ADV(my='advisor'): return CA('advisor_phone', 'Advisor phone', 'text', LKT('team.phone', 'team.name', my), 18)
EQ = lambda s: tok('enqst', s)
QS = lambda s: tok('quotest', s)
TT = lambda s: tok('ttype', s)

settings = [
    S('company', 'Your company name', 'text', COMPANY), S('host_pct', 'Share of every commission kept by the host agency', 'pct', 0.20), S('advisor_pct', 'Advisor share of the agency share', 'pct', 0.50),
    S('markup_pct', 'Mark-up on supplier net price for bookings you collect', 'pct', 0.06), S('planning_fee', 'Standard trip planning fee', 'money', 250), S('air_ticket_fee', 'Booking fee per air ticket', 'money', 35),
    S('min_fee', 'Smallest service fee on a trip', 'money', 90), S('quote_valid_days', 'Days a quote stays valid', 'int', 14), S('warn_days', 'Days ahead to warn of an expiry, a deadline or a start', 'int', 14),
    S('target_commission_pct', 'Wanted commission as a share of sales', 'pct', 0.10), S('target_margin', 'Wanted margin on the supplier net price of a trip', 'pct', 0.15),
    S('reply_hours', 'Hours within which a new enquiry should get a first reply', 'int', 24), S('quote_days', 'Days within which a quote should follow an enquiry', 'int', 7),
    S('quote_chase_days', 'Days before a quote expires to chase it', 'int', 4), S('big_budget', 'Budget above which an enquiry needs the owner', 'money', 30000),
    S('trip_hours', 'Advisor hours a new trip needs each week while it is planned', 'int', 6), S('stale_days', 'Days without a touch before a quote is stale', 'int', 7),
]
assert 3 <= len(settings) <= 20

OPEN_E = 'OR({col:status}=%s,{col:status}=%s)' % (EQ('New'), EQ('Quoted'))
NXT = 'DATE(YEAR({col:month}),MONTH({col:month})+1,1)'
def PIPE(t, d, extra=''): return 'COUNTIFS({range:%s.%s},">="&{col:month},{range:%s.%s},"<"&%s%s)' % (t, d, t, d, NXT, extra)

tables = [
    T('enquiries', 'Enquiries', 'Enquiries with budget, replies and follow-ups',
      'One row per enquiry: contact, trip type, destination, budget, source and advisor; reply and quote timing, follow-up checks, budget per person and the value of a won trip fill in by themselves.', [
        C('enquiry_id', 'Enquiry ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), C('contact', 'Contact', 'text', 24), C('phone', 'Phone', 'text', 18), REF('client', 'Client', 'clients.name', 24),
        LST('trip_type', 'Trip type', 'ttype', 18), C('destination', 'Destination', 'text', 22), C('travellers', 'Travellers', 'int', 10), C('budget', 'Budget', 'money', 12), LST('source', 'Source', 'msrc', 26),
        REF('advisor', 'Advisor', 'team.name', 24), LST('status', 'Status', 'enqst', 22), C('follow_up_date', 'Follow-up date', 'date', 13), REF('converted_trip', 'Converted trip', 'trips.trip_id', 11),
        REF('partner', 'Referral partner', 'partners.name', 28), C('first_reply_hours', 'First reply, hours', 'int', 11),
        CA('days_since', 'Days since enquiry', 'int', '{today}-{col:date}', 10), CA('budget_pp', 'Budget per person', 'money', 'IF({col:travellers}>0,{col:budget}/{col:travellers},0)', 12),
        CA('size_flag', 'Budget size', 'text', 'IF({col:budget}>={set:big_budget},%s,%s)' % (ca('Above usual budget'), ca('Usual budget')), 18),
        CA('reply_flag', 'Reply check', 'text', 'IF({col:first_reply_hours}<={set:reply_hours},%s,%s)' % (ca('Reply on time'), ca('Reply late')), 14),
        CA('fu_flag', 'Follow-up check', 'text', 'IF(%s,IF({col:follow_up_date}="",%s,IF({col:follow_up_date}<{today},%s,%s)),%s)' % (OPEN_E, ca('No follow-up set'), ca('Follow-up overdue'), ca('Follow-up planned'), ca('Closed')), 18),
        CA('quote_days', 'Quote sent after, days', 'int', 'IFERROR(INDEX({range:quotes.date_sent},MATCH({col:enquiry_id},{range:quotes.enquiry_id},0))-{col:date},"")', 11),
        CA('quote_flag', 'Quote timing', 'text', 'IF({col:quote_days}="",%s,IF({col:quote_days}<={set:quote_days},%s,%s))' % (ca('No quote yet'), ca('Quote on time'), ca('Quote late')), 16),
        CA('is_open', 'Open', 'int', 'IF(%s,1,0)' % OPEN_E, 8), CA('is_won', 'Won', 'int', 'IF({col:status}=%s,1,0)' % EQ('Won'), 8),
        CA('trip_value', 'Trip value', 'money', LKN('trips.total_price', 'trips.trip_id', 'converted_trip'), 12),
        CA('quote_total', 'Quote total', 'money', LKN('quotes.total_quote', 'quotes.enquiry_id', 'enquiry_id'), 12), CA('quote_gap', 'Quote less budget', 'money', 'IF({col:quote_total}>0,{col:quote_total}-{col:budget},0)', 12),
        CA('opt_low', 'Lower option budget', 'money', '{col:budget}*0.85', 12), CA('opt_high', 'Higher option budget', 'money', '{col:budget}*1.15', 12), ADV(), OWN()],
      D.enquiries_d(), 400, [A('fu_flag', '= ' + ca('Follow-up overdue'), 'bad'), A('fu_flag', '= ' + ca('No follow-up set'), 'warn'), A('reply_flag', '= ' + ca('Reply late'), 'warn'), A('size_flag', '= ' + ca('Above usual budget'), 'good')]),
    T('quotes', 'Quotes', 'Quotes with margin, expiry and chase check',
      'One row per quote sent: price, supplier net, service fee and expected commission; the margin, margin on net, days to expiry and who to chase fill in by themselves.', [
        C('quote_id', 'Quote ID', 'text', 10, required=True), C('date_sent', 'Date sent', 'date', 11), REF('enquiry_id', 'Enquiry', 'enquiries.enquiry_id', 10), REF('client', 'Client', 'clients.name', 24),
        REF('trip_id', 'Trip', 'trips.trip_id', 10), LST('trip_type', 'Trip type', 'ttype', 18), C('destination', 'Destination', 'text', 22), C('travellers', 'Travellers', 'int', 10),
        C('total_quote', 'Total quote', 'money', 13, visual='bar'), C('supplier_net', 'Supplier net', 'money', 12), C('service_fee', 'Service fee', 'money', 11), C('expected_commission', 'Expected commission', 'money', 12),
        C('valid_until', 'Valid until', 'date', 11), LST('status', 'Status', 'quotest', 12), REF('advisor', 'Advisor', 'team.name', 24),
        CA('margin', 'Margin', 'money', '{col:expected_commission}+{col:service_fee}', 11), CA('margin_net', 'Margin on net', 'pct', 'IF({col:supplier_net}>0,({col:expected_commission}+{col:service_fee})/{col:supplier_net},0)', 11),
        CA('margin_flag', 'Margin check', 'text', 'IF({col:margin_net}>={set:target_margin},%s,%s)' % (ca('Margin on target'), ca('Margin under target')), 16),
        CA('per_person', 'Price per person', 'money', 'IF({col:travellers}>0,{col:total_quote}/{col:travellers},0)', 12), CA('days_to_expiry', 'Days to expiry', 'int', '{col:valid_until}-{today}', 10),
        CA('chase_flag', 'Chase check', 'text', 'IF({col:status}=%s,IF({col:days_to_expiry}<0,%s,IF({col:days_to_expiry}<={set:quote_chase_days},%s,%s)),%s)' % (QS('Open'), ca('Expired still open'), ca('Chase now'), ca('Waiting'), ca('Closed')), 18),
        CA('lines_total', 'Lines total', 'money', 'SUMIFS({range:quote_lines.client_price},{range:quote_lines.quote_id},{col:quote_id})', 12),
        CA('client_phone', 'Client phone', 'text', LKT('clients.phone', 'clients.name', 'client'), 18), ADV(), OWN()],
      D.quotes_d(), 400, [A('chase_flag', '= ' + ca('Chase now'), 'warn'), A('chase_flag', '= ' + ca('Expired still open'), 'bad'), A('margin_flag', '= ' + ca('Margin under target'), 'warn'), A('days_to_expiry', '<= {set:warn_days}', 'warn')]),
    T('quote_lines', 'Quote Lines', 'Quote lines by supplier with mark-up and margin',
      'One row per component of a quote: supplier category, supplier, nights, net and client price; the mark-up on net, the line margin and the share of the quote fill in by themselves.', [
        C('line_id', 'Line ID', 'text', 10, required=True), REF('quote_id', 'Quote', 'quotes.quote_id', 10), LST('category', 'Category', 'scat', 20), REF('supplier', 'Supplier', 'suppliers.name', 28), C('description', 'Description', 'text', 44),
        C('nights', 'Nights', 'int', 8), C('supplier_net', 'Supplier net', 'money', 12), C('client_price', 'Client price', 'money', 12),
        CA('markup', 'Mark-up on net', 'pct', 'IF({col:supplier_net}>0,{col:client_price}/{col:supplier_net}-1,0)', 11), CA('line_margin', 'Line margin', 'money', '{col:client_price}-{col:supplier_net}', 11),
        CA('share', 'Share of the quote', 'pct', 'IFERROR({col:client_price}/SUMIFS({range:quote_lines.client_price},{range:quote_lines.quote_id},{col:quote_id}),0)', 11),
        CA('client', 'Client', 'text', LKT('quotes.client', 'quotes.quote_id', 'quote_id'), 24), CA('total_quote', 'Quote total', 'money', LKN('quotes.total_quote', 'quotes.quote_id', 'quote_id'), 12)],
      D.quote_lines_d(), 1500),
    T('discovery', 'Discovery Calls', 'Discovery calls with outcome and days to quote',
      'One row per first call with a prospect: enquiry, minutes, advisor and outcome; the contact, phone, days until the quote and the next-step check fill in by themselves.', [
        C('call_id', 'Call ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('enquiry_id', 'Enquiry', 'enquiries.enquiry_id', 10), C('minutes', 'Minutes', 'int', 9), REF('advisor', 'Advisor', 'team.name', 24),
        LST('outcome', 'Outcome', 'outcome', 22), C('next_step_date', 'Next step date', 'date', 13),
        CA('contact', 'Contact', 'text', LKT('enquiries.contact', 'enquiries.enquiry_id', 'enquiry_id'), 24), CA('contact_phone', 'Contact phone', 'text', LKT('enquiries.phone', 'enquiries.enquiry_id', 'enquiry_id'), 18),
        CA('trip_type', 'Trip type', 'text', LKT('enquiries.trip_type', 'enquiries.enquiry_id', 'enquiry_id'), 18),
        CA('days_to_quote', 'Days to quote', 'int', 'IFERROR(INDEX({range:quotes.date_sent},MATCH({col:enquiry_id},{range:quotes.enquiry_id},0))-{col:date},"")', 11),
        CA('step_flag', 'Next step check', 'text', 'IF({col:next_step_date}="",%s,IF({col:next_step_date}<{today},%s,%s))' % (cb('No next step'), cb('Next step passed'), cb('Next step planned')), 16), ADV()],
      D.discovery_d(), 400, [A('step_flag', '= ' + cb('Next step passed'), 'warn')]),
    T('briefs', 'Trip Briefs', 'Trip briefs with budget per person per night',
      'One row per trip brief: travellers, nights, travel window, budget, must-haves, avoid list and pace; the contact, travel window length and budget per person per night fill in by themselves.', [
        C('brief_id', 'Brief ID', 'text', 10, required=True), C('brief_date', 'Brief date', 'date', 11), REF('enquiry_id', 'Enquiry', 'enquiries.enquiry_id', 10), C('travellers', 'Travellers', 'int', 10), C('nights', 'Nights', 'int', 8),
        C('window_start', 'Window start', 'date', 12), C('window_end', 'Window end', 'date', 12), C('budget', 'Budget', 'money', 12), C('must_haves', 'Must-haves', 'text', 40), C('avoid', 'Avoid list', 'text', 26), LST('pace', 'Pace', 'pace', 11),
        CA('contact', 'Contact', 'text', LKT('enquiries.contact', 'enquiries.enquiry_id', 'enquiry_id'), 24), CA('phone', 'Phone', 'text', LKT('enquiries.phone', 'enquiries.enquiry_id', 'enquiry_id'), 18),
        CA('window_days', 'Window, days', 'int', '{col:window_end}-{col:window_start}', 10), CA('budget_pppn', 'Budget per person per night', 'money', 'IF({col:travellers}*{col:nights}>0,{col:budget}/({col:travellers}*{col:nights}),0)', 13),
        CA('window_flag', 'Window check', 'text', 'IF({col:window_days}<{col:nights}+10,%s,%s)' % (cb('Window is short'), cb('Window is wide')), 15)],
      D.briefs_d(), 300),
    T('clients', 'Clients', 'Clients with trips, sales and repeat flag',
      'One row per client: kind, home airport, interest, stage and who referred them; the number of trips, total sales and the repeat-client flag fill in by themselves.', [
        C('client_id', 'Client ID', 'text', 10, required=True), C('name', 'Name', 'text', 24), LST('kind', 'Kind', 'ckind', 15), C('contact', 'Contact', 'text', 24), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26), C('country', 'Country', 'text', 16),
        C('home_airport', 'Home airport', 'text', 16), C('interest', 'Interest', 'text', 22), C('since', 'Since', 'date', 11), LST('stage', 'Stage', 'stage', 13), REF('referred_by', 'Referred by', 'clients.name', 24),
        CA('trips', 'Trips', 'int', 'COUNTIFS({range:trips.client_id},{col:client_id},{range:trips.is_sale},1)', 8), CA('sales', 'Total sales', 'money', 'SUMIFS({range:trips.total_price},{range:trips.client_id},{col:client_id},{range:trips.is_sale},1)', 13),
        CA('repeat_flag', 'Repeat check', 'text', 'IF({col:trips}>=2,%s,IF({col:trips}=1,%s,%s))' % (ca('Repeat client'), ca('One trip'), ca('No trip yet')), 14)],
      D.clients_d(), 300, [A('repeat_flag', '= ' + ca('Repeat client'), 'good')]),
    T('trips', 'Trips', 'Trips with price, commission and deposit check',
      'One row per trip: client, type, dates, advisor, price, supplier net, expected commission and service fee; the commission share, price per person, days to book and deposit check fill in by themselves.', [
        C('trip_id', 'Trip ID', 'text', 10, required=True), REF('client', 'Client', 'clients.name', 24), C('client_id', 'Client ID', 'text', 10), LST('trip_type', 'Trip type', 'ttype', 18), C('destination', 'Destination', 'text', 22),
        C('start_date', 'Start', 'date', 11), C('end_date', 'End', 'date', 11), C('nights', 'Nights', 'int', 8), C('travellers', 'Travellers', 'int', 10), LST('status', 'Status', 'tstatus', 12), REF('advisor', 'Advisor', 'team.name', 24),
        C('booked_on', 'Booked on', 'date', 11), C('cancelled_on', 'Cancelled on', 'date', 12), C('group_id', 'Group', 'text', 9), C('total_price', 'Total price', 'money', 13, visual='bar'), C('supplier_net', 'Supplier net', 'money', 12),
        C('commission_expected', 'Expected commission', 'money', 12), C('service_fee', 'Service fee', 'money', 11), C('host_pct', 'Host share', 'pct', 9), REF('enquiry_id', 'Enquiry', 'enquiries.enquiry_id', 10),
        C('deposit_due', 'Deposit due', 'date', 11), C('deposit_paid_on', 'Deposit paid on', 'date', 12),
        CA('comm_share', 'Commission share of price', 'pct', 'IF({col:total_price}>0,{col:commission_expected}/{col:total_price},0)', 11), CA('price_pp', 'Price per person', 'money', 'IF({col:travellers}>0,{col:total_price}/{col:travellers},0)', 12),
        CA('is_sale', 'Booked sale', 'int', 'IF(OR({col:status}=%s,{col:status}=%s),0,1)' % (tok('tstatus', 'Quoted'), tok('tstatus', 'Cancelled')), 8),
        CA('days_to_start', 'Days to travel', 'int', '{col:start_date}-{today}', 10),
        CA('days_to_book', 'Days enquiry to booking', 'int', 'IF({col:is_sale}=1,IFERROR({col:booked_on}-INDEX({range:enquiries.date},MATCH({col:enquiry_id},{range:enquiries.enquiry_id},0)),""),"")', 11),
        CA('deposit_flag', 'Deposit check', 'text', 'IF({col:status}=%s,%s,IF({col:deposit_paid_on}<>"",%s,IF({col:deposit_due}<{today},%s,%s)))' % (tok('tstatus', 'Cancelled'), ca('Not needed'), ca('Deposit paid'), ca('Deposit overdue'), ca('Deposit awaited')), 15),
        CA('client_phone', 'Client phone', 'text', LKT('clients.phone', 'clients.client_id', 'client_id'), 18), ADV(), OWN()],
      D.trips_d(), 300, [A('deposit_flag', '= ' + ca('Deposit overdue'), 'bad'), A('deposit_flag', '= ' + ca('Deposit awaited'), 'warn'), A('status', '= ' + tok('tstatus', 'Cancelled'), 'bad')]),
    T('suppliers', 'Suppliers', 'Suppliers with commission rate and quoted value',
      'One row per supplier: category, commission rate, deposit and final payment terms, who collects the money and days until commission is paid; the lines quoted and their value fill in by themselves.', [
        C('supplier_id', 'Supplier ID', 'text', 10, required=True), C('name', 'Name', 'text', 28), LST('category', 'Category', 'scat', 20), C('country', 'Country', 'text', 16), C('contact', 'Contact', 'text', 22), C('phone', 'Phone', 'text', 18),
        C('email', 'E-mail', 'text', 26), C('commission_pct', 'Commission rate', 'pct', 11), C('deposit_pct', 'Deposit', 'pct', 9), C('final_days', 'Final payment, days before travel', 'int', 11), C('collect', 'Who collects', 'text', 10),
        C('terms_days', 'Commission paid, days after travel', 'int', 11), C('rating', 'Rating', 'num', 8), C('since', 'Since', 'date', 11),
        CA('lines', 'Lines quoted', 'int', 'COUNTIFS({range:quote_lines.supplier},{col:name})', 9), CA('quoted', 'Value quoted', 'money', 'SUMIFS({range:quote_lines.client_price},{range:quote_lines.supplier},{col:name})', 13),
        CA('commission_quoted', 'Commission on lines quoted', 'money', '{col:quoted}*{col:commission_pct}', 13)],
      D.suppliers_d(), 100),
    T('fees', 'Service Fee Schedule', 'Service fee schedule with repeat-client waivers',
      'One row per paid service: unit, fee and whether it is waived for a repeat client; the fee for a repeat client, its share of the average trip and the review check fill in by themselves.', [
        C('fee_id', 'Fee ID', 'text', 9, required=True), C('service', 'Service', 'text', 38), C('unit', 'Unit', 'text', 10), C('fee', 'Fee', 'money', 10), LST('waived_repeat', 'Waived for repeat clients', 'yn', 12), C('review_on', 'Review on', 'date', 11),
        CA('fee_repeat', 'Fee for a repeat client', 'money', 'IF({col:waived_repeat}=%s,0,{col:fee})' % tok('yn', 'Yes'), 12),
        CA('fee_share', 'Share of the average trip price', 'pct', 'IFERROR({col:fee}/AVERAGEIFS({range:trips.total_price},{range:trips.is_sale},1),0)', 12),
        CA('review_flag', 'Review check', 'text', 'IF({col:review_on}<{today},%s,%s)' % (cb('Review due'), cb('Review planned')), 14)],
      D.fees_d(), 60, [A('review_flag', '= ' + cb('Review due'), 'warn')]),
    T('packages', 'Trip Packages', 'Standard trip packages with price per night',
      'Twelve standard offers to show a client who has a budget but no plan: type, nights, travellers and from price; the price per night and per person fill in by themselves.', [
        C('package_id', 'Package ID', 'text', 10, required=True), C('name', 'Package', 'text', 40), LST('trip_type', 'Trip type', 'ttype', 18), C('nights', 'Nights', 'int', 8), C('travellers', 'Travellers', 'int', 10), C('from_price', 'From price', 'money', 12),
        C('included', 'What is included', 'text', 44),
        CA('price_night', 'Price per night', 'money', 'IF({col:nights}>0,{col:from_price}/{col:nights},0)', 12), CA('price_person', 'Price per person', 'money', 'IF({col:travellers}>0,{col:from_price}/{col:travellers},0)', 12)],
      D.packages_d(), 60),
    T('price_guide', 'Destination Price Guide', 'Destination prices by season for a quick budget check',
      'Eight popular destinations in peak, shoulder and low season: hotel night, daily spend and air fare per person; the trip cost per person for 7 nights fills in by itself.', [
        C('guide_id', 'Guide ID', 'text', 10, required=True), C('destination', 'Destination', 'text', 24), LST('season', 'Season', 'season', 10), C('hotel_night', 'Hotel night, per room', 'money', 12), C('daily_budget', 'Daily spend per person', 'money', 12),
        C('air_fare', 'Air fare per person', 'money', 12), CA('cost_pp7', 'Trip cost per person, 7 nights', 'money', '{col:air_fare}+7*({col:hotel_night}/2+{col:daily_budget})', 13)],
      D.guide_d(), 60),
    T('lost', 'Lost Enquiries', 'Lost enquiries with reason and price gap',
      'One row per enquiry that did not book: reason, estimated price gap, who won and what would have saved it; the contact, budget and gap share fill in by themselves.', [
        C('lost_id', 'Lost ID', 'text', 9, required=True), REF('enquiry_id', 'Enquiry', 'enquiries.enquiry_id', 10), C('lost_on', 'Lost on', 'date', 11), LST('reason', 'Reason', 'lreason', 28), C('price_gap', 'Price gap, estimate', 'money', 12),
        C('won_by', 'Who won', 'text', 26), C('saved_by', 'What would have saved it', 'text', 40),
        CA('contact', 'Contact', 'text', LKT('enquiries.contact', 'enquiries.enquiry_id', 'enquiry_id'), 24), CA('phone', 'Phone', 'text', LKT('enquiries.phone', 'enquiries.enquiry_id', 'enquiry_id'), 18),
        CA('trip_type', 'Trip type', 'text', LKT('enquiries.trip_type', 'enquiries.enquiry_id', 'enquiry_id'), 18), CA('budget', 'Budget', 'money', LKN('enquiries.budget', 'enquiries.enquiry_id', 'enquiry_id'), 12),
        CA('gap_share', 'Gap share of the budget', 'pct', 'IF({col:budget}>0,{col:price_gap}/{col:budget},0)', 11),
        CA('gap_flag', 'Gap check', 'text', 'IF({col:gap_share}>=0.1,%s,%s)' % (cb('Gap is large'), cb('Gap is small')), 13)],
      D.lost_d(), 100, [A('gap_flag', '= ' + cb('Gap is large'), 'warn')]),
    T('followups', 'Follow-up Log', 'Follow-up log of every touch with the next one planned',
      'One row per call, message or visit after an enquiry or a quote: channel, outcome and the next touch date; the contact, phone, days since the touch and the next-touch check fill in by themselves.', [
        C('fu_id', 'Touch ID', 'text', 10, required=True), REF('enquiry_id', 'Enquiry', 'enquiries.enquiry_id', 10), C('quote_id', 'Quote', 'text', 10), C('date', 'Date', 'date', 11), LST('channel', 'Channel', 'channel', 14), LST('outcome', 'Outcome', 'outcome', 22),
        C('next_touch_date', 'Next touch date', 'date', 13),
        CA('contact', 'Contact', 'text', LKT('enquiries.contact', 'enquiries.enquiry_id', 'enquiry_id'), 24), CA('phone', 'Phone', 'text', LKT('enquiries.phone', 'enquiries.enquiry_id', 'enquiry_id'), 18),
        CA('days_since', 'Days since the touch', 'int', '{today}-{col:date}', 10),
        CA('touch_flag', 'Next touch check', 'text', 'IF({col:next_touch_date}="",%s,IF({col:next_touch_date}<{today},%s,%s))' % (ca('No next touch'), ca('Touch overdue'), ca('Touch planned')), 16)],
      D.followups_d(), 600, [A('touch_flag', '= ' + ca('Touch overdue'), 'bad')]),
    T('partners', 'Referral Partners', 'Referral partners with enquiries, bookings and value',
      'One row per partner who sends clients: kind, contact and thank-you date; the enquiries sent, trips booked, value won, conversion and the thank-you check fill in by themselves.', [
        C('partner_id', 'Partner ID', 'text', 10, required=True), C('name', 'Name', 'text', 28), LST('kind', 'Kind', 'pkind', 18), C('contact', 'Contact', 'text', 24), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
        C('country', 'Country', 'text', 16), C('since', 'Partner since', 'date', 12), C('thank_you_date', 'Last thank-you', 'date', 12),
        CA('leads', 'Enquiries sent', 'int', 'COUNTIFS({range:enquiries.partner},{col:name})', 10), CA('bookings', 'Trips booked', 'int', 'COUNTIFS({range:enquiries.partner},{col:name},{range:enquiries.is_won},1)', 10),
        CA('value', 'Value won', 'money', 'SUMIFS({range:enquiries.trip_value},{range:enquiries.partner},{col:name})', 13), CA('conversion', 'Conversion', 'pct', 'IF({col:leads}>0,{col:bookings}/{col:leads},0)', 10),
        CA('thank_flag', 'Thank-you check', 'text', 'IF({today}-{col:thank_you_date}>60,%s,%s)' % (cb('Thank-you due'), cb('Thanked')), 14), CA('conv_flag', 'Conversion check', 'text', 'IF({col:conversion}>=0.5,%s,%s)' % (cb('Converts well'), cb('Low conversion')), 15)],
      D.partners_d(), 60, [A('thank_flag', '= ' + cb('Thank-you due'), 'warn'), A('conv_flag', '= ' + cb('Converts well'), 'good')]),
    T('marketing', 'Marketing Results', 'Marketing results by month and source',
      'One row per source and month: spend, leads, enquiries, bookings and revenue; the cost per enquiry and the cost per booking fill in by themselves.', [
        C('mk_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('source', 'Source', 'msrc', 28), C('spend', 'Spend', 'money', 11), C('leads', 'Leads', 'int', 8), C('enquiries', 'Enquiries', 'int', 10),
        C('bookings', 'Bookings', 'int', 10), C('revenue', 'Revenue', 'num', 12),
        CA('cost_enquiry', 'Cost per enquiry', 'money', 'IF({col:enquiries}>0,{col:spend}/{col:enquiries},0)', 12), CA('cost_booking', 'Cost per booking', 'money', 'IF({col:bookings}>0,{col:spend}/{col:bookings},0)', 12)],
      D.marketing_d(), 400),
    T('terms', 'Quote Terms Library', 'Quote terms library of standard clauses',
      'Twelve standard clauses to paste under a quote: validity, price changes, deposit, final payment, cancellation, entry documents and insurance advice; the review check fills in by itself.', [
        C('term_id', 'Clause ID', 'text', 9, required=True), C('clause', 'Clause', 'text', 24), C('wording', 'Sample wording', 'text', 44), C('applies_to', 'Applies to', 'text', 12), C('review_on', 'Review on', 'date', 11),
        CA('review_flag', 'Review check', 'text', 'IF({col:review_on}<{today},%s,%s)' % (cb('Review due'), cb('Review planned')), 14)],
      D.terms_d(), 60, [A('review_flag', '= ' + cb('Review due'), 'warn')]),
    T('capacity', 'Advisor Capacity Weeks', 'Advisor capacity by week with free hours',
      'One row per advisor and week: hours available for clients and hours committed to planning; the free hours, the week status and whether a new trip fits fill in by themselves.', [
        C('cap_id', 'Row ID', 'text', 9, required=True), C('week', 'Week (Monday)', 'date', 12), REF('advisor', 'Advisor', 'team.name', 24), C('hours_avail', 'Hours available', 'int', 10), C('hours_committed', 'Hours committed', 'int', 10),
        CA('free_hours', 'Free hours', 'int', '{col:hours_avail}-{col:hours_committed}', 10), CA('use_pct', 'Use of the hours', 'pct', 'IF({col:hours_avail}>0,{col:hours_committed}/{col:hours_avail},0)', 10),
        CA('status', 'Week status', 'text', 'IF({col:free_hours}<0,%s,IF({col:free_hours}<{col:hours_avail}*0.15,%s,%s))' % (cb('Over capacity'), cb('Tight week'), cb('Free capacity')), 14),
        CA('can_start', 'New trip fits', 'text', 'IF({col:free_hours}>={set:trip_hours},%s,%s)' % (cb('Fits this week'), cb('Does not fit this week')), 18), ADV()],
      D.capacity_d(), 400, [A('status', '= ' + cb('Over capacity'), 'bad'), A('status', '= ' + cb('Tight week'), 'warn')]),
    T('seasonal', 'Seasonal Demand', 'Seasonal demand by calendar month',
      'Twelve months of enquiries, quotes and bookings counted over every year of history, so the busy months show; the quote-to-booking rate and the month type fill in by themselves.', [
        C('sea_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), C('enquiries', 'Enquiries', 'int', 10), C('quotes', 'Quotes', 'int', 9), C('bookings', 'Bookings', 'int', 10),
        CA('rate', 'Quote to booking', 'pct', 'IF({col:quotes}>0,{col:bookings}/{col:quotes},0)', 11),
        CA('season_flag', 'Month type', 'text', 'IF({col:enquiries}>=AVERAGE({range:seasonal.enquiries})*1.15,%s,IF({col:enquiries}<=AVERAGE({range:seasonal.enquiries})*0.85,%s,%s))' % (cb('Peak month'), cb('Quiet month'), cb('Normal month')), 13)],
      D.seasonal_d(), 60, [A('season_flag', '= ' + cb('Peak month'), 'good')]),
    T('team', 'Team', 'Team with hours, advisor share and open work',
      'The owner advisor, four advisors and seven freelance specialists with hours a week and advisor share of the agency commission; the open quotes and the sales of each advisor fill in by themselves.', [
        C('staff_id', 'Staff ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 20), LST('team', 'Team', 'team', 12), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 28),
        C('hours_week', 'Hours a week', 'int', 10), C('advisor_pct', 'Advisor share', 'pct', 10), C('speciality', 'Speciality', 'text', 24), C('country', 'Country', 'text', 14), C('start', 'Start', 'date', 11),
        CA('open_quotes', 'Open quotes', 'int', 'COUNTIFS({range:quotes.advisor},{col:name},{range:quotes.status},%s)' % QS('Open'), 9),
        CA('sales', 'Sales booked', 'money', 'SUMIFS({range:trips.total_price},{range:trips.advisor},{col:name},{range:trips.is_sale},1)', 13)],
      D.team_d(), 60),
    T('pipeline', 'Pipeline by Month', 'Pipeline by month with win rate',
      'One row per month for the last 14 months; enquiries, quotes, wins, losses, sales won and the win rate all count themselves from Enquiries and Quotes.', [
        C('pl_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11),
        CA('enquiries', 'Enquiries', 'int', PIPE('enquiries', 'date'), 10), CA('quotes', 'Quotes sent', 'int', PIPE('quotes', 'date_sent'), 10),
        CA('won', 'Won', 'int', PIPE('quotes', 'date_sent', ',{range:quotes.status},%s' % QS('Accepted')), 8),
        CA('lost', 'Lost', 'int', PIPE('quotes', 'date_sent', ',{range:quotes.status},%s' % QS('Declined')) + '+' + PIPE('quotes', 'date_sent', ',{range:quotes.status},%s' % QS('Expired')), 8),
        CA('sales_won', 'Sales won', 'money', 'SUMIFS({range:quotes.total_quote},{range:quotes.date_sent},">="&{col:month},{range:quotes.date_sent},"<"&%s,{range:quotes.status},%s)' % (NXT, QS('Accepted')), 13),
        CA('win_rate', 'Win rate', 'pct', 'IF({col:won}+{col:lost}>0,{col:won}/({col:won}+{col:lost}),0)', 9), OWN()],
      D.pipeline_d(), 60),
]
assert len(tables) == 20, len(tables)
