"""Travel agent suite - part 1: Enquiries, Quotes and Trip Pricing."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ta1_lists import *
from ta1_tables import settings, tables
from ta1_tools import tools
QS = lambda x: tok('quotest', x)

SUITE = 'fx-20261113-travel-agent'
NOTE = "Sample wording: adapt it to your own practice."
LN = {"from": "quote_lines", "match": "quote_lines.quote_id", "columns": ["category", "supplier", "description", "nights", "client_price", "share"], "max": 8}
forms = [
    FORM('enquiry_sheet', 'Enquiry Sheet', 'Enquiry sheet with budget, replies and follow-up', 'enquiries.enquiry_id', [
        FV('Date', 'enquiries.date'), FV('Contact', 'enquiries.contact'), FV('Phone', 'enquiries.phone'), FV('Client', 'enquiries.client'), FV('Trip type', 'enquiries.trip_type'), FV('Destination', 'enquiries.destination'),
        FV('Travellers', 'enquiries.travellers'), FV('Budget', 'enquiries.budget'), FV('Budget per person', 'enquiries.budget_pp'), FV('Budget size', 'enquiries.size_flag'), FV('Source', 'enquiries.source'),
        FV('Advisor', 'enquiries.advisor'), FV('Status', 'enquiries.status'), FV('First reply, hours', 'enquiries.first_reply_hours'), FV('Reply check', 'enquiries.reply_flag'), FV('Follow-up date', 'enquiries.follow_up_date'),
        FV('Follow-up check', 'enquiries.fu_flag'), FV('Quote timing', 'enquiries.quote_flag')]),
    FORM('call_sheet', 'Discovery Call Sheet', 'Discovery call with outcome and next step', 'discovery.call_id', [
        FV('Date', 'discovery.date'), FV('Enquiry', 'discovery.enquiry_id'), FV('Contact', 'discovery.contact'), FV('Phone', 'discovery.contact_phone'), FV('Trip type', 'discovery.trip_type'), FV('Minutes', 'discovery.minutes'),
        FV('Advisor', 'discovery.advisor'), FV('Outcome', 'discovery.outcome'), FV('Next step date', 'discovery.next_step_date'), FV('Next step check', 'discovery.step_flag'), FV('Days to quote', 'discovery.days_to_quote')]),
    FORM('brief_sheet', 'Trip Brief Sheet', 'Trip brief with window, budget and pace', 'briefs.brief_id', [
        FV('Brief date', 'briefs.brief_date'), FV('Enquiry', 'briefs.enquiry_id'), FV('Contact', 'briefs.contact'), FV('Phone', 'briefs.phone'), FV('Travellers', 'briefs.travellers'), FV('Nights', 'briefs.nights'),
        FV('Window start', 'briefs.window_start'), FV('Window end', 'briefs.window_end'), FV('Window, days', 'briefs.window_days'), FV('Window check', 'briefs.window_flag'), FV('Budget', 'briefs.budget'),
        FV('Budget per person per night', 'briefs.budget_pppn'), FV('Must-haves', 'briefs.must_haves'), FV('Avoid list', 'briefs.avoid'), FV('Pace', 'briefs.pace')]),
    FORM('quote_sheet', 'Quote Sheet', 'Quote with lines, margin and expiry', 'quotes.quote_id', [
        FV('Date sent', 'quotes.date_sent'), FV('Enquiry', 'quotes.enquiry_id'), FV('Client', 'quotes.client'), FV('Client phone', 'quotes.client_phone'), FV('Trip type', 'quotes.trip_type'), FV('Destination', 'quotes.destination'),
        FV('Travellers', 'quotes.travellers'), FV('Total quote', 'quotes.total_quote'), FV('Price per person', 'quotes.per_person'), FV('Supplier net', 'quotes.supplier_net'), FV('Service fee', 'quotes.service_fee'),
        FV('Expected commission', 'quotes.expected_commission'), FV('Margin', 'quotes.margin'), FV('Margin on net', 'quotes.margin_net'), FV('Margin check', 'quotes.margin_flag'), FV('Valid until', 'quotes.valid_until'),
        FV('Days to expiry', 'quotes.days_to_expiry'), FV('Chase check', 'quotes.chase_flag'), FV('Status', 'quotes.status'), FV('Advisor', 'quotes.advisor')], LN),
    FORM('package_sheet', 'Package Choice Sheet', 'Package choice with price per night and person', 'packages.package_id', [
        FV('Package', 'packages.name'), FV('Trip type', 'packages.trip_type'), FV('Nights', 'packages.nights'), FV('Travellers', 'packages.travellers'), FV('From price', 'packages.from_price'), FV('Price per night', 'packages.price_night'),
        FV('Price per person', 'packages.price_person'), FV('What is included', 'packages.included'),
        FF('Packages of the same type', 'COUNTIFS({range:packages.trip_type},INDEX({range:packages.trip_type},MATCH({pick},{range:packages.package_id},0)))', 'int'),
        FF('Average from price of all packages', 'AVERAGE({range:packages.from_price})', 'money')]),
    FORM('revision_sheet', 'Quote Revision Sheet', 'Quote revision with price against the lines', 'quotes.quote_id', [
        FV('Client', 'quotes.client'), FV('Trip type', 'quotes.trip_type'), FV('Destination', 'quotes.destination'), FV('Status', 'quotes.status'), FV('Total quote', 'quotes.total_quote'), FV('Lines total', 'quotes.lines_total'),
        FV('Supplier net', 'quotes.supplier_net'), FV('Service fee', 'quotes.service_fee'), FV('Margin', 'quotes.margin'), FV('Margin on net', 'quotes.margin_net'), FV('Margin check', 'quotes.margin_flag'), FV('Valid until', 'quotes.valid_until')],
        {"from": "quote_lines", "match": "quote_lines.quote_id", "columns": ["category", "supplier", "supplier_net", "client_price", "markup", "line_margin"], "max": 8}),
    FORM('lost_sheet', 'Lost Enquiry Sheet', 'Lost enquiry with reason, price gap and lesson', 'lost.lost_id', [
        FV('Enquiry', 'lost.enquiry_id'), FV('Contact', 'lost.contact'), FV('Phone', 'lost.phone'), FV('Trip type', 'lost.trip_type'), FV('Lost on', 'lost.lost_on'), FV('Reason', 'lost.reason'), FV('Budget', 'lost.budget'),
        FV('Price gap, estimate', 'lost.price_gap'), FV('Gap share of the budget', 'lost.gap_share'), FV('Gap check', 'lost.gap_flag'), FV('Who won', 'lost.won_by'), FV('What would have saved it', 'lost.saved_by')]),
    FORM('partner_sheet', 'Referral Partner Sheet', 'Referral partner with enquiries, trips and value', 'partners.partner_id', [
        FV('Name', 'partners.name'), FV('Kind', 'partners.kind'), FV('Contact', 'partners.contact'), FV('Phone', 'partners.phone'), FV('E-mail', 'partners.email'), FV('Country', 'partners.country'), FV('Partner since', 'partners.since'),
        FV('Enquiries sent', 'partners.leads'), FV('Trips booked', 'partners.bookings'), FV('Value won', 'partners.value'), FV('Conversion', 'partners.conversion'), FV('Last thank-you', 'partners.thank_you_date'),
        FV('Thank-you check', 'partners.thank_flag'), FV('Conversion check', 'partners.conv_flag')]),
    FORM('touch_sheet', 'Follow-up Sheet', 'Follow-up touch with outcome and next touch', 'followups.fu_id', [
        FV('Enquiry', 'followups.enquiry_id'), FV('Quote', 'followups.quote_id'), FV('Contact', 'followups.contact'), FV('Phone', 'followups.phone'), FV('Date', 'followups.date'), FV('Channel', 'followups.channel'),
        FV('Outcome', 'followups.outcome'), FV('Days since the touch', 'followups.days_since'), FV('Next touch date', 'followups.next_touch_date'), FV('Next touch check', 'followups.touch_flag')]),
    FORM('handover_sheet', 'Handover to Booking Sheet', 'Handover of a won trip to booking', 'trips.trip_id', [
        FV('Client', 'trips.client'), FV('Client phone', 'trips.client_phone'), FV('Trip type', 'trips.trip_type'), FV('Destination', 'trips.destination'), FV('Start', 'trips.start_date'), FV('End', 'trips.end_date'), FV('Nights', 'trips.nights'),
        FV('Travellers', 'trips.travellers'), FV('Advisor', 'trips.advisor'), FV('Advisor phone', 'trips.advisor_phone'), FV('Booked on', 'trips.booked_on'), FV('Total price', 'trips.total_price'), FV('Supplier net', 'trips.supplier_net'),
        FV('Expected commission', 'trips.commission_expected'), FV('Service fee', 'trips.service_fee'), FV('Price per person', 'trips.price_pp'), FV('Deposit due', 'trips.deposit_due'), FV('Deposit paid on', 'trips.deposit_paid_on'),
        FV('Deposit check', 'trips.deposit_flag'), FV('Days to travel', 'trips.days_to_start')]),
]
assert len(forms) == 10
documents = [
    DOC('proposal', 'Trip Proposal', 'Trip proposal and price summary', 'quotes.quote_id', [
        'Trip proposal of {set:company}, dated {today}. Quote {col:quotes.quote_id}.',
        'Dear {col:quotes.client}, thank you for the chance to plan your {col:quotes.trip_type} trip to {col:quotes.destination} for {col:quotes.travellers} travellers. This page sets out our proposal and the price.',
        'Total price: {col:quotes.total_quote}, which is {col:quotes.per_person} per person. Our service fee of {col:quotes.service_fee} is included and shown as its own line. Prices are before any tax. The components of the trip add up to {col:quotes.lines_total}.',
        'This proposal is valid until {col:quotes.valid_until}. After that date prices and availability may change. To accept it, sign below and pay the deposit we confirm with you.', 'Your advisor is {col:quotes.advisor}.'], ['Client', 'Advisor'], NOTE),
    DOC('compare', 'Quote Comparison', 'Quote comparison for a client', 'enquiries.enquiry_id', [
        'Quote comparison of {set:company} for {col:enquiries.contact}, dated {today}. Enquiry {col:enquiries.enquiry_id}: {col:enquiries.trip_type} to {col:enquiries.destination}, {col:enquiries.travellers} travellers.',
        'Your budget: {col:enquiries.budget}, which is {col:enquiries.budget_pp} per person. Our quote: {col:enquiries.quote_total}. The quote less your budget: {col:enquiries.quote_gap}.',
        'If the quote is above your budget we can shorten the trip, choose a lower hotel tier or move to cheaper dates. Tell us which matters most and we will price it.', 'Budget size check: {col:enquiries.size_flag}. Follow-up date: {col:enquiries.follow_up_date}.'], ['Advisor', 'Client'], NOTE),
    DOC('options', 'Three Package Options', 'Three package options for a budget', 'enquiries.enquiry_id', [
        'Three options of {set:company} for {col:enquiries.contact}, dated {today}. Trip: {col:enquiries.trip_type} to {col:enquiries.destination} for {col:enquiries.travellers} travellers. Your budget: {col:enquiries.budget}.',
        'Lower option: a total of about {col:enquiries.opt_low}. Simpler hotels or a shorter stay, the same destination.', 'Middle option: a total of about {col:enquiries.budget}. Our best match for what you told us.',
        'Higher option: a total of about {col:enquiries.opt_high}. Better rooms, more included and more private services.', 'Each option is a starting point. We can mix them. Reply with the one that feels closest and we will build a full quote.'], ['Advisor', 'Client'], NOTE),
    DOC('call_summary', 'Discovery Call Summary', 'Discovery call summary', 'discovery.call_id', [
        'Discovery call summary of {set:company}, dated {today}.', 'Call on {col:discovery.date}: {col:discovery.minutes} minutes with {col:discovery.advisor}. Contact: {col:discovery.contact}. Trip type: {col:discovery.trip_type}.',
        'Outcome: {col:discovery.outcome}. Next step on {col:discovery.next_step_date}. Next step check: {col:discovery.step_flag}.', 'Days from the call to the quote: {col:discovery.days_to_quote}.', 'Notes of the call, the places the contact likes and the questions they raised are written below.'], ['Advisor', 'Client'], NOTE),
    DOC('brief_summary', 'Trip Brief Summary', 'Trip brief summary for approval', 'briefs.brief_id', [
        'Trip brief summary of {set:company} for {col:briefs.contact}, dated {today}. Brief {col:briefs.brief_id}.', '{col:briefs.travellers} travellers, {col:briefs.nights} nights, travelling between {col:briefs.window_start} and {col:briefs.window_end} ({col:briefs.window_days} days of choice).',
        'Budget: {col:briefs.budget}, which is {col:briefs.budget_pppn} per person per night. Pace: {col:briefs.pace}.', 'Must-haves: {col:briefs.must_haves}. Please avoid: {col:briefs.avoid}.', 'Please check every line. Your signature approves the brief as the basis of the quote.'], ['Client', 'Advisor'], NOTE),
    DOC('terms', 'Quote Terms and Conditions', 'Quote terms and conditions', 'quotes.quote_id', [
        'Terms of {set:company} for quote {col:quotes.quote_id}, dated {today}. Client: {col:quotes.client}.',
        'Validity: this quote is valid until {col:quotes.valid_until}. After that date prices and availability may change.', 'Price changes: supplier prices can change before full payment. We tell you at once and you may accept the change or cancel.',
        'Payments: the deposit secures the price. The balance due before travel must reach us by the final payment date on your booking confirmation. Our service fee of {col:quotes.service_fee} is shown as its own line and is not refunded if you cancel.',
        'Travel documents: you are responsible for valid travel documents. Check the destination current rules before you book and before you travel. We advise travel insurance for every traveller.', 'Your signature accepts these terms for this quote.'], ['Client', 'Advisor'], NOTE),
    DOC('expiry_letter', 'Expiry Reminder Letter', 'Quote expiry reminder letter', 'quotes.quote_id', [
        'Reminder of {set:company}, dated {today}.', 'Dear {col:quotes.client}, our quote {col:quotes.quote_id} for your trip to {col:quotes.destination} is valid until {col:quotes.valid_until}, which is {col:quotes.days_to_expiry} days from today.',
        'The total is {col:quotes.total_quote} for {col:quotes.travellers} travellers. After the expiry date the price and the availability may change.', 'If you have questions or want changes, please tell us. We can ask the suppliers to extend the price once if you need more time.'], ['Advisor'], NOTE),
    DOC('partner_note', 'Referral Thank-you Note', 'Referral partner thank-you note', 'partners.partner_id', [
        'Thank-you note of {set:company}, dated {today}.', 'Dear {col:partners.contact}, thank you for the clients you send us. So far you have sent {col:partners.leads} enquiries and {col:partners.bookings} became trips, with a value of {col:partners.value}.',
        'Your last thank-you from us was on {col:partners.thank_you_date}. We report back on every trip you send and we are glad to help your own clients and customers.', 'We would be glad to meet and share ideas for the coming season.'], ['Owner advisor'], NOTE),
    DOC('fee_agreement', 'Service Fee Agreement', 'Service fee agreement for a trip', 'quotes.quote_id', [
        'Service fee agreement of {set:company}, dated {today}. Quote {col:quotes.quote_id}, client {col:quotes.client}.', 'Our service fee for planning and booking your {col:quotes.trip_type} trip to {col:quotes.destination} is {col:quotes.service_fee}, before any tax.',
        'The fee covers planning, quotes, booking, document checks and support until you travel. Suppliers may also pay us a commission. That commission does not change the price you pay.', 'A change after booking can carry a change fee. We quote it before we act. The service fee is not refunded if you cancel.', 'Your signature accepts the fee.'], ['Client', 'Advisor'], NOTE),
    DOC('pipeline_report', 'Pipeline Report', 'Sales pipeline report for one month', 'pipeline.pl_id', [
        'Sales pipeline report of {set:company}, dated {today}. Month: {col:pipeline.month}.', 'Enquiries received: {col:pipeline.enquiries}. Quotes sent: {col:pipeline.quotes}. Quotes won: {col:pipeline.won}. Quotes lost: {col:pipeline.lost}.',
        'Sales won: {col:pipeline.sales_won}. Win rate of decided quotes: {col:pipeline.win_rate}.', 'Actions for next month and the person who owns each one are written below.'], ['Owner advisor', 'Advisor'], NOTE),
]
assert len(documents) == 10
checklists = [
    CHK('enquiry_run', 'New Enquiry Steps', 'enquiries', 'enquiries.date', [('Log the enquiry and its source', 0), ('Reply to the contact', 1), ('Ask for travel dates and travellers', 1), ('Book the discovery call', 2), ('Check capacity for the planning weeks', 2), ('Set the follow-up date', 3), ('Pass a large budget to the owner', 3)]),
    CHK('call_run', 'Discovery Call Prep Steps', 'discovery', 'discovery.date', [('Read the enquiry and the budget', -2), ('Check the destination price guide', -1), ('Prepare three package ideas', -1), ('Confirm the call with the contact', -1), ('Write the call summary', 0), ('Set the next step date', 1), ('Send the trip brief for approval', 3)]),
    CHK('brief_run', 'Trip Brief Capture Steps', 'briefs', 'briefs.brief_date', [('Note travellers, nights and the travel window', 0), ('Agree the budget', 1), ('Write must-haves and the avoid list', 1), ('Choose the pace', 2), ('Check the budget against the price guide', 2), ('Send the brief for approval', 3), ('Get the written approval', 7)]),
    CHK('quote_prep', 'Quote Preparation Steps', 'quotes', 'quotes.date_sent', [('Ask suppliers for net prices', -5), ('Hold the prices where possible', -4), ('Price every line with the mark-up', -3), ('Check the margin against the target', -2), ('Add the terms from the library', -1), ('Owner approves a large quote', -1), ('Send the quote', 0)]),
    CHK('quote_follow', 'Quote Follow-up Steps', 'quotes', 'quotes.date_sent', [('Send the quote and confirm it arrived', 0), ('First follow-up call', 2), ('Answer questions or send package options', 5), ('Second follow-up', 9), ('Chase before the quote expires', 11), ('Mark it expired or extend it once', 15), ('Record the outcome and the reason', 16)]),
    CHK('deposit_run', 'Deposit and Booking Steps', 'trips', 'trips.booked_on', [('Send the deposit request', 0), ('Confirm the deposit arrived', 3), ('Book every supplier', 4), ('Send the booking confirmation', 5), ('Write the final payment dates in the diary', 5), ('Ask for traveller details', 7), ('Start the handover', 8)]),
    CHK('lost_run', 'Lost Enquiry Review Steps', 'lost', 'lost.lost_on', [('Record the reason and who won', 0), ('Note the price gap', 1), ('Send a thank-you and ask for feedback', 3), ('Decide whether to keep the contact warm', 7), ('Write what would have saved it', 7), ('Add it to the monthly review', 30)]),
    CHK('handover_run', 'Handover to Booking Steps', 'trips', 'trips.booked_on', [('Share the quote and the brief with the booking advisor', 0), ('Check supplier terms and final payment dates', 1), ('Confirm the commission expected', 2), ('Introduce the booking advisor to the client', 2), ('Open the trip folder', 3), ('Check the travel document needs', 5), ('Hold the first booking review', 7)]),
    CHK('partner_run', 'Partner Follow-up Steps', 'partners', 'partners.thank_you_date', [('Send a thank-you for each enquiry', 0), ('Report the result of each referral', 14), ('Invite the partner to a call', 30), ('Share ideas for the coming season', 60), ('Review the partner results', 90)]),
    CHK('fee_run', 'Quarterly Fee Review Steps', 'fees', 'fees.review_on', [('Export quotes won and lost', -14), ('Compare margin on net with the target', -10), ('Check which fees were waived', -7), ('Check what other advisors charge', -5), ('Decide the new fees', -2), ('Update the fee schedule and the terms', 0), ('Tell clients with open quotes', 7)]),
]
assert len(checklists) == 10
def M(key_, moment, table, phone, text): return MSG(key_, moment, table, phone, text)
messages = [
    M('m_c_thanks', 'Client: thanks for your enquiry', 'enquiries', 'enquiries.phone', 'Hello {contact}, thank you for your enquiry about {destination}. Can we talk on {follow_up_date}? Please tell me a time that suits you.'),
    M('m_c_call', 'Client: your discovery call is confirmed', 'discovery', 'discovery.contact_phone', 'Hello {contact}, your discovery call with {advisor} is confirmed for {date}, about {minutes} minutes. Please tell us if the time changes.'),
    M('m_c_docs', 'Client: send your dates and names', 'enquiries', 'enquiries.phone', 'Hello {contact}, to plan your trip please send your travel dates and the names of all {travellers} travellers as they appear on their travel documents.'),
    M('m_c_brief', 'Client: your trip brief is ready', 'briefs', 'briefs.phone', 'Hello {contact}, your trip brief is ready: {travellers} travellers, {nights} nights, a budget of {budget}. Please check it and tell us what to change.'),
    M('m_c_quote', 'Client: your quote is ready', 'quotes', 'quotes.client_phone', 'Hello {client}, your quote for {destination} is ready: {total_quote} for {travellers} travellers. Shall we go through it together?'),
    M('m_c_valid', 'Client: your quote is valid until', 'quotes', 'quotes.client_phone', 'Hello {client}, your quote for {destination} is valid until {valid_until}. After that date prices may change. Please tell us if you need more time.'),
    M('m_c_remind', 'Client: a gentle quote reminder', 'quotes', 'quotes.client_phone', 'Hello {client}, a gentle reminder about your {destination} quote sent on {date_sent}. Do you have questions, or would a call help?'),
    M('m_c_options', 'Client: three options for your budget', 'enquiries', 'enquiries.phone', 'Hello {contact}, for your budget of {budget} we can offer three options: about {opt_low}, {budget} or {opt_high} for the whole trip. Which feels closest?'),
    M('m_c_explain', 'Client: the price explained line by line', 'quotes', 'quotes.client_phone', 'Hello {client}, I will send your {destination} quote line by line. The total is {total_quote}, which is {per_person} per person. Our service fee of {service_fee} is its own line.'),
    M('m_c_deposit', 'Client: your deposit secures the price', 'trips', 'trips.client_phone', 'Hello {client}, your deposit secures the price of your {destination} trip. It is due on {deposit_due}. Please tell us when it is sent.'),
    M('m_c_depok', 'Client: your deposit has arrived', 'trips', 'trips.client_phone', 'Hello {client}, your deposit arrived on {deposit_paid_on}. Thank you. Your {destination} trip is secured.'),
    M('m_c_next', 'Client: next steps after booking', 'trips', 'trips.client_phone', 'Hello {client}, thank you for booking {destination}. Next we will send your payment dates, a travel document check and your itinerary. Your trip number is {trip_id}.'),
    M('m_c_price', 'Client: prices may change after expiry', 'quotes', 'quotes.client_phone', 'Hello {client}, prices for {destination} may change after {valid_until}. Please tell us by then if you want to book at {total_quote}.'),
    M('m_c_sorry', 'Client: sorry about your budget', 'lost', 'lost.phone', 'Hello {contact}, thank you for considering us. We are sorry we could not match your budget for your {trip_type} trip. We would be glad to help in the future.'),
    M('m_c_referral', 'Client: thank you for the referral', 'clients', 'clients.phone', 'Hello {name}, thank you for recommending us to a friend. It means a great deal to the whole team.'),
    M('m_c_change', 'Client: your quote change is attached', 'quotes', 'quotes.client_phone', 'Hello {client}, your quote change is attached. The total is now {total_quote} and it is valid until {valid_until}. Please check it and tell us.'),
    M('m_c_dates', 'Client: a question about your dates', 'briefs', 'briefs.phone', 'Hello {contact}, a quick question about your dates: can you travel any time between {window_start} and {window_end}?'),
    M('m_p_booked', 'Partner: we booked a trip you sent', 'partners', 'partners.phone', 'Hello {contact}, we booked a trip you sent, thank you. You have sent {leads} enquiries and {bookings} became trips so far. A thank-you is on its way.'),
    M('m_p_new', 'Partner: a new enquiry that may suit you', 'partners', 'partners.phone', 'Hello {contact}, we have a new enquiry that may suit you or your clients. Please call us if you would like to hear more.'),
    M('m_o_expire', 'Owner: a quote expires soon', 'quotes', 'quotes.owner_phone', 'Hello, the quote for {client} expires on {valid_until}. Total {total_quote}. Chase check: {chase_flag}. Please decide whether to ask for an extension.'),
    M('m_o_big', 'Owner: enquiry above the usual budget', 'enquiries', 'enquiries.owner_phone', 'Hello, the enquiry from {contact} is above the usual budget: {budget} for {travellers} travellers ({trip_type}, {destination}). Please join the first call.'),
    M('m_o_approve', 'Owner: a quote needs your approval', 'quotes', 'quotes.owner_phone', 'Hello, the quote for {client} needs your approval: total {total_quote}, margin {margin}. Margin check: {margin_flag}.'),
    M('m_o_week', 'Owner: the weekly sales summary is ready', 'pipeline', 'pipeline.owner_phone', 'Hello, the sales summary is ready. In {month}: {enquiries} enquiries, {quotes} quotes, {won} won, sales won {sales_won}.'),
    M('m_o_margin', 'Owner: the margin is below the target', 'quotes', 'quotes.owner_phone', 'Hello, the margin on the {destination} quote for {client} is {margin_net} of the net price, below the target. Total {total_quote}. Please review the fee.'),
    M('m_a_new', 'Advisor: new enquiry assigned to you', 'enquiries', 'enquiries.advisor_phone', 'Hello, a new enquiry is assigned to you: {contact}, {trip_type}, {destination}, budget {budget}, {travellers} travellers. Please reply within a day.'),
    M('m_a_booked', 'Advisor: trip booked, start the handover', 'trips', 'trips.advisor_phone', 'Hello, trip {trip_id} for {client} to {destination} is booked. Please start the handover and check the deposit date, {deposit_due}.'),
    M('m_a_full', 'Advisor: your capacity is full', 'capacity', 'capacity.advisor_phone', 'Hello {advisor}, your capacity is full in the week of {week}: {free_hours} free hours. Please do not take new trips in that week without asking the owner.'),
    M('m_f_avail', 'Freelance: availability for an itinerary', 'team', 'team.phone', 'Hello {name}, are you available to draw up an itinerary for a new trip? Please tell us your rate and the days you can offer.'),
]
assert len(messages) == 28
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; YS = 'DATE(YEAR({today}),1,1)'
def CNT(t, d, a, extra=''): return 'COUNTIFS({range:%s.%s},">="&%s,{range:%s.%s},"<="&{today}%s)' % (t, d, a, t, d, extra)
def SMS(t, v, d, a, extra=''): return 'SUMIFS({range:%s.%s},{range:%s.%s},">="&%s,{range:%s.%s},"<="&{today}%s)' % (t, v, t, d, a, t, d, extra)
SALE = ',{range:trips.is_sale},1'
def SHARE(tt): return 'IFERROR(COUNTIFS({range:trips.trip_type},%s,{range:trips.is_sale},1)/COUNTIFS({range:trips.is_sale},1),0)' % tt
REFS = [tok('msrc', 'Referral from past client'), tok('msrc', 'Wedding planner referral'), tok('msrc', 'Partner referral')]
NXT_A = 'DATE(YEAR({today}),MONTH({today})+1,1)'; NXT_B = 'DATE(YEAR({today}),MONTH({today})+2,1)'
kpis = [
    KPI('Enquiries this month', CNT('enquiries', 'date', MS), 'int'), KPI('Enquiries this year', CNT('enquiries', 'date', YS), 'int'),
    KPI('Open quotes', 'COUNTIFS({range:quotes.status},%s)' % tok('quotest', 'Open'), 'int'),
    KPI('Value of open quotes', 'SUMIFS({range:quotes.total_quote},{range:quotes.status},%s)' % tok('quotest', 'Open'), 'money'),
    KPI('Quotes sent this month', CNT('quotes', 'date_sent', MS), 'int'), KPI('Trips booked this month', CNT('trips', 'booked_on', MS, SALE), 'int'),
    KPI('Sales booked this month', SMS('trips', 'total_price', 'booked_on', MS, SALE), 'money'), KPI('Sales booked this year', SMS('trips', 'total_price', 'booked_on', YS, SALE), 'money'),
    KPI('Average trip price', 'IFERROR(AVERAGEIFS({range:trips.total_price},{range:trips.is_sale},1),0)', 'money'), KPI('Average service fee per trip', 'IFERROR(AVERAGEIFS({range:trips.service_fee},{range:trips.is_sale},1),0)', 'money'),
    KPI('Average margin per quote', 'IFERROR(AVERAGE({range:quotes.margin}),0)', 'money'),
    KPI('Enquiry-to-quote rate', 'IFERROR(COUNT({range:enquiries.quote_days})/COUNTA({range:enquiries.enquiry_id}),0)', 'pct'),
    KPI('Quote-to-booking rate', 'IFERROR(COUNTIFS({range:quotes.status},%s)/(COUNTA({range:quotes.quote_id})-COUNTIFS({range:quotes.status},%s)),0)' % (tok('quotest', 'Accepted'), tok('quotest', 'Open')), 'pct'),
    KPI('Enquiry-to-booking rate', 'IFERROR(SUM({range:enquiries.is_won})/COUNTA({range:enquiries.enquiry_id}),0)', 'pct'), KPI('Average days from enquiry to booking', 'IFERROR(AVERAGE({range:trips.days_to_book}),0)', 'int'),
    KPI('Average first reply time in hours', 'IFERROR(AVERAGE({range:enquiries.first_reply_hours}),0)', 'num'), KPI('Enquiries with an overdue follow-up', 'COUNTIFS({range:enquiries.fu_flag},%s)' % ca('Follow-up overdue'), 'int'),
    KPI('Quotes expiring within the warn days', 'COUNTIFS({range:quotes.status},%s,{range:quotes.days_to_expiry},">=0",{range:quotes.days_to_expiry},"<="&{set:warn_days})' % tok('quotest', 'Open'), 'int'),
    KPI('Deposits not yet paid', 'COUNTIFS({range:trips.deposit_flag},%s)+COUNTIFS({range:trips.deposit_flag},%s)' % (ca('Deposit awaited'), ca('Deposit overdue')), 'int'),
    KPI('Share of cruise bookings', SHARE(tok('ttype', 'Cruise')), 'pct'), KPI('Share of group bookings', SHARE(tok('ttype', 'Group trip')), 'pct'),
    KPI('Repeat clients share', 'IFERROR(COUNTIFS({range:clients.repeat_flag},%s)/COUNTIFS({range:clients.trips},">0"),0)' % ca('Repeat client'), 'pct'),
    KPI('Referral share of bookings', 'IFERROR((COUNTIFS({range:enquiries.is_won},1,{range:enquiries.source},%s)+COUNTIFS({range:enquiries.is_won},1,{range:enquiries.source},%s)+COUNTIFS({range:enquiries.is_won},1,{range:enquiries.source},%s))/SUM({range:enquiries.is_won}),0)' % tuple(REFS), 'pct'),
    KPI('Cost per booking from paid sources', 'IFERROR(SUMIFS({range:marketing.spend},{range:marketing.spend},">0")/SUMIFS({range:marketing.bookings},{range:marketing.spend},">0"),0)', 'money'),
    KPI('Marketing spend this year', SMS('marketing', 'spend', 'month', YS), 'money'),
    KPI('Share lost on price', 'IFERROR(COUNTIFS({range:lost.reason},%s)/COUNTA({range:lost.lost_id}),0)' % tok('lreason', 'Price too high'), 'pct'),
    KPI('Trips starting in the next 60 days', 'COUNTIFS({range:trips.start_date},">="&{today},{range:trips.start_date},"<="&({today}+60)%s)' % SALE, 'int'),
    KPI('Free advisor hours next month', 'SUMIFS({range:capacity.free_hours},{range:capacity.week},">="&%s,{range:capacity.week},"<"&%s)' % (NXT_A, NXT_B), 'int'),
    KPI('Expected commission on open quotes', 'SUMIFS({range:quotes.expected_commission},{range:quotes.status},%s)' % tok('quotest', 'Open'), 'money'),
]
assert len(kpis) == 29, len(kpis)
dashboard = {"title": "Sales Dashboard", "kpis": kpis,
    "monthly": {"title": "Trip value booked, quotes sent, service fees and marketing", "date": "trips.booked_on", "series": [
        {"label": "Trip value by booking date", "sum": "trips.total_price", "date": "trips.booked_on"}, {"label": "Value of quotes sent", "sum": "quotes.total_quote", "date": "quotes.date_sent"},
        {"label": "Service fees by booking date", "sum": "trips.service_fee", "date": "trips.booked_on"}, {"label": "Marketing spend", "sum": "marketing.spend", "date": "marketing.month"}]},
    "breakdowns": [{"title": "Trip value by trip type", "by": "trips.trip_type", "value": "trips.total_price", "agg": "sum"}, {"title": "Enquiries by source", "by": "enquiries.source", "value": "enquiries.budget", "agg": "count"},
                   {"title": "Expected commission by trip type", "by": "quotes.trip_type", "value": "quotes.expected_commission", "agg": "sum"}, {"title": "Quotes by status", "by": "quotes.status", "value": "quotes.total_quote", "agg": "count"}]}
insights = {"filters": [{"label": "Advisor", "ref": "team.name"}, {"label": "Trip type", "list": "ttype"}, {"label": "Source", "list": "msrc"}],
    "gauges": [{"title": "Quote-to-booking rate", "num": AGG('count', 'quotes', where=[('status', '=', tok('quotest', 'Accepted'))]), "den": AGG('count', 'quotes', where=[('status', '<>', tok('quotest', 'Open'))])},
               {"title": "Replies within 24 hours", "num": AGG('count', 'enquiries', where=[('reply_flag', '=', ca('Reply on time'))]), "den": AGG('count', 'enquiries')},
               {"title": "Quotes followed up on time", "num": AGG('count', 'quotes', where=[('chase_flag', '<>', ca('Expired still open'))]), "den": AGG('count', 'quotes')},
               {"title": "Deposits received", "num": AGG('count', 'trips', where=[('deposit_flag', '=', ca('Deposit paid'))]), "den": AGG('count', 'trips', where=[('deposit_flag', '<>', ca('Not needed'))])},
               {"title": "Quotes above the target margin", "num": AGG('count', 'quotes', where=[('margin_flag', '=', ca('Margin on target'))]), "den": AGG('count', 'quotes')},
               {"title": "Repeat clients share", "num": AGG('count', 'clients', where=[('repeat_flag', '=', ca('Repeat client'))]), "den": AGG('count', 'clients', where=[('trips', '>', 0)])}],
    "charts": [
        CHART('Enquiries per month', 'column', 'month', [AGG('count', 'enquiries', date='enquiries.date', label='Enquiries')]),
        CHART('Trips booked per month', 'column', 'month', [AGG('count', 'trips', date='trips.booked_on', where=[('is_sale', '=', 1)], label='Trips booked')]),
        CHART('Sales booked per month', 'column', 'month', [AGG('sum', 'trips', 'trips.total_price', date='trips.booked_on', where=[('is_sale', '=', 1)], label='Sales booked')]),
        CHART('Enquiries by source', 'bar', 'enquiries.source', [AGG('count', 'enquiries', label='Enquiries')]),
        CHART('Bookings by source', 'bar', 'enquiries.source', [AGG('count', 'enquiries', where=[('is_won', '=', 1)], label='Trips booked')]),
        CHART('Conversion rate by source', 'bar', 'enquiries.source', [AGG('avg', 'enquiries', 'enquiries.is_won', label='Enquiry to booking')]),
        CHART('Cost per booking by source', 'bar', 'marketing.source', [AGG('avg', 'marketing', 'marketing.cost_booking', where=[('bookings', '>', 0)], label='Cost per booking')]),
        CHART('Enquiries by trip type', 'bar', 'enquiries.trip_type', [AGG('count', 'enquiries', label='Enquiries')]),
        CHART('Sales by trip type', 'bar', 'trips.trip_type', [AGG('sum', 'trips', 'trips.total_price', where=[('is_sale', '=', 1)], label='Sales')]),
        CHART('Quotes by status', 'bar', 'quotes.status', [AGG('count', 'quotes', label='Quotes')]),
        CHART('Enquiries by status', 'bar', 'enquiries.status', [AGG('count', 'enquiries', label='Enquiries')]),
        CHART('Lost enquiries by reason', 'bar', 'lost.reason', [AGG('count', 'lost', label='Lost enquiries')]),
        CHART('Average trip price by trip type', 'bar', 'trips.trip_type', [AGG('avg', 'trips', 'trips.total_price', where=[('is_sale', '=', 1)], label='Average trip price')]),
        CHART('Average margin by trip type', 'bar', 'quotes.trip_type', [AGG('avg', 'quotes', 'quotes.margin', label='Average margin')]),
        CHART('Enquiries by advisor', 'bar', 'enquiries.advisor', [AGG('count', 'enquiries', label='Enquiries')]),
        CHART('Average travellers by trip type', 'bar', 'trips.trip_type', [AGG('avg', 'trips', 'trips.travellers', where=[('is_sale', '=', 1)], label='Average travellers')]),
        CHART('Days to book per month', 'line', 'month', [AGG('avg', 'trips', 'trips.days_to_book', date='trips.booked_on', where=[('is_sale', '=', 1)], label='Days to book')]),
        CHART('Free advisor hours per week, monthly average', 'line', 'month', [AGG('avg', 'capacity', 'capacity.free_hours', date='capacity.week', label='Free hours per week')])]}
signature = [
    {"name": "Trip quote builder with fee and commission", "why": "supplier net prices by component become a client price, a service fee, your commission and the host agency and advisor shares", "where": "Trip Quote Builder"},
    {"name": "Margin check before sending a quote", "why": "margin on the net price against your target, with the lowest fee or price that reaches it", "where": "Quote Margin Check"},
    {"name": "Deposit and final payment plan builder", "why": "deposit, final payment dates and amounts per supplier from the booking and travel dates", "where": "Deposit and Final Payment Plan"},
    {"name": "Budget reality check by component", "why": "hotel, daily spend and flights for a destination against the client budget, with the gap shown", "where": "Budget Reality Check"},
    {"name": "Package builder from the price guide", "why": "twelve standard offers and a destination price guide give a client a plan that fits the budget", "where": "Trip Packages"},
    {"name": "Capacity check for a new trip", "why": "free advisor hours week by week show whether the team can plan one more trip now", "where": "Capacity Check for a New Trip"},
    {"name": "Win chance and weighted pipeline", "why": "stage, source, budget fit and waiting time give a win chance and the weighted value of every quote", "where": "Win Chance and Weighted Value"},
    {"name": "Counter-offer helper for low budgets", "why": "a lower hotel tier, cheaper dates or fewer nights, with the gap left after each", "where": "Counter-Offer for a Low Budget"},
    {"name": "Source scoreboard with cost per booking", "why": "spend, enquiries and bookings by source and month give the cost per enquiry and per booking", "where": "Marketing Results"},
    {"name": "Referral partner tracker", "why": "enquiries sent, trips booked, value won and a thank-you reminder for every partner", "where": "Referral Partners"}]
competitors = [
    {"what": "free trip budget templates", "lacks": "list costs for a holiday but have no supplier net price, mark-up, service fee, commission, quote tracking or follow-up"},
    {"what": "subscription travel-agency software", "lacks": "charge every month for features built for booking, so quote margin, win chance and cost per booking are thin or missing"},
    {"what": "single-sheet commission trackers", "lacks": "track money after travel but cannot price a quote, check the margin before it goes out or show which source brings paying trips"},
    {"what": "generic project-management boards", "lacks": "show cards and tasks without prices, commission, deposit dates, service fees or the margin of a trip"},
    {"what": "plain quote documents in a word processor", "lacks": "cannot add up lines, check the margin, track expiry dates or learn from lost enquiries"}]
guide = [
    'Open Start and type your company name and your own limits in the yellow cells: mark-up, planning fee, smallest fee, target margin, reply hours, days a quote stays valid and the budget that needs the owner.',
    'Check Team, Clients, Trips and Suppliers. They hold the people, clients, trips and suppliers that every other sheet looks up.',
    'Fill Service Fee Schedule with your own services and fees, and mark the ones you waive for repeat clients.',
    'Fill Destination Price Guide with hotel, daily spend and air fare for the places you sell most, in peak and low season.',
    'Log each enquiry on Enquiries, each first call on Discovery Calls and each brief on Trip Briefs. Replies, follow-ups and budget per person are checked for you.',
    'Write each quote on Quotes and its components on Quote Lines. Margin, margin on net, expiry and chase checks fill in.',
    'Keep Trip Packages and Quote Terms Library as your standard offers and standard clauses.',
    'Record every touch on Follow-up Log and every lost enquiry on Lost Enquiries so the reasons teach you something.',
    'Track Marketing Results and Referral Partners to see which source and which partner bring trips that pay.',
    'Watch Advisor Capacity Weeks before you promise a quote date, and Seasonal Demand and Pipeline by Month for the yearly picture.',
    f'Use the {len(tools)} calculators for quotes, margins, fees, budgets, payment plans, win chance, counter-offers, add-ons, expiry dates and what-ifs.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Sales Dashboard and Charts every week: enquiries, quotes, bookings, sources, lost reasons, margin and free hours.']
listing = {"title": "Travel Agent Enquiries, Quotes and Trip Pricing Excel Template: Quote Builder, Margin Check, Service Fees, Pipeline, Capacity",
    "headline": "Turn enquiries into booked trips at a margin that pays",
    "tags": ["travel agent", "travel advisor", "trip quote", "excel template", "quote builder", "service fee", "commission tracker", "sales pipeline", "enquiry tracker", "travel business", "client quote", "margin check", "home based agent"],
    "description": ("Run the sales side of an independent travel agent or travel advisor business in one Excel workbook. Enquiries logs every contact with its source, budget and travellers, and tells you whether you replied in time, which follow-up is overdue and whether a quote went out on time. Quotes holds each trip quote with the supplier net price (the price the supplier charges before commission), your service fee and the expected commission (the share of the price a supplier pays you after travel), and Quote Lines splits it by supplier so you see the mark-up and margin of every component.\n\n"
        "The Trip Quote Builder turns supplier net prices into a client price, a service fee, your commission and the shares of the host agency (the larger agency whose booking access and supplier deals you use, for a share of each commission) and of the advisor. The Quote Margin Check shows the lowest fee or price that reaches your target before you send. The Deposit and Final Payment Plan gives every date and amount of the deposit and of the final payment (the balance due before travel), and the Budget Reality Check shows what a client budget can buy at a destination.\n\n"
        "Discovery Calls, Trip Briefs, Follow-up Log, Lost Enquiries, Trip Packages, Destination Price Guide, Service Fee Schedule, Quote Terms Library, Referral Partners, Marketing Results, Advisor Capacity Weeks, Seasonal Demand and Pipeline by Month cover the rest of the sales year: days from enquiry to quote, why you lose trips, which source costs least per booking, which partner sends paying clients and whether the team has free hours for a new trip.\n\n"
        f"{len(tools)} calculators cover quotes, margins, service fees, budgets, per-person prices, payment plans, win chance, counter-offers, two-option comparisons, source cost, capacity, add-ons, expiry dates and a what-if grid. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages that open with the details already written in.\n\n"
        "This is part one of the Travel Agent suite. A standard .xlsx workbook with no macros and no subscription, 15 languages in one purchase, with a demo copy full of sample data for a small advisor business to explore first. It helps you plan your sales and does not promise results."),
    "features": ["Enquiries with reply, quote and follow-up checks", "Quotes with margin, expiry and chase check", "Quote lines with mark-up by supplier", "Trip quote builder with commission shares",
                 "Margin check before a quote goes out", "Deposit and final payment plan", "Budget reality check by destination", "Win chance and weighted pipeline",
                 "Lost enquiry lessons and referral partners", f"{len(tools)} calculators for quotes and fees", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p1', slug='travel-agent-quotes', profession='Travel Agent', name='Enquiries, Quotes and Trip Pricing',
         tagline='Turn enquiries into booked trips at a margin that pays', price_usd=29,
         colors={"primary": "#1D3557", "accent": "#2A9D8F"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 1, "of": 8, "focus": "Enquiries, quotes and trip pricing"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ta1.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
