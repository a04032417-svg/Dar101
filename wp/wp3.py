"""Wedding Planning suite - part 3: Vendors, Quotes and Contracts."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp3_lists import *
from wp3_tables import *
from wp3_tools import tools
import wp3_data as D

SUITE = 'fx-20261116-wedding'
NOTE = "Sample wording: adapt it to your own wedding."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c_): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c_, t, idc)
VNAME_OF_PICK = 'INDEX({range:vendors.vendor},MATCH({pick},{range:vendors.vendor_id},0))'

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('vendor_sheet', 'Vendor Sheet', 'One vendor with its quotes', 'vendors.vendor_id', F(('Vendor', 'vendors.vendor'), ('Category', 'vendors.category'), ('Contact', 'vendors.contact'), ('Phone', 'vendors.phone'), ('E-mail', 'vendors.email'),
        ('Status', 'vendors.status'), ('Booked on', 'vendors.booked_on'), ('Contract total', 'vendors.contract_total'), ('Typical lead months', 'vendors.lead_months'), ('Payer', 'vendors.payer'),
        ('Last contact', 'vendors.last_contact'), ('Days since contact', 'vendors.days_since'), ('Confirmed for the day', 'vendors.confirmed')),
        {"from": "quotes", "match": "quotes.vendor_id", "columns": ["option", "status", "base_price", "true_total", "valid_until"], "max": 6}),
    FORM('quote_sheet', 'Quote Sheet', 'One quote with every extra', 'quotes.quote_id', F(('Vendor', 'quotes.vendor'), ('Category', 'quotes.category'), ('Option', 'quotes.option'), ('Status', 'quotes.status'), ('Quote date', 'quotes.quote_date'),
        ('Base price', 'quotes.base_price'), ('Service charge', 'quotes.service_amt'), ('Taxes', 'quotes.tax_amt'), ('Delivery', 'quotes.delivery'), ('Overtime estimate', 'quotes.overtime'), ('Travel', 'quotes.travel'),
        ('Expected tip', 'quotes.tip_amt'), ('True total', 'quotes.true_total'), ('Extras over the base price', 'quotes.extras'), ('Valid until', 'quotes.valid_until')) + [
        FF('Days the quote is valid', '%s-%s' % (LK('quotes', 'quote_id', 'valid_until'), LK('quotes', 'quote_id', 'quote_date')), 'int')]),
    FORM('compare_sheet', 'Quote Comparison Sheet', 'One vendor slot, quotes side by side', 'vendors.vendor_id', F(('Vendor', 'vendors.vendor'), ('Category', 'vendors.category'), ('Status', 'vendors.status')) + [
        FF('Best value on your weights', 'IFERROR(INDEX({range:winners.best_value},MATCH(%s,{range:winners.vendor},0)),"")' % VNAME_OF_PICK, 'text'),
        FF('Best value true total', 'IFERROR(INDEX({range:winners.best_total},MATCH(%s,{range:winners.vendor},0)),0)' % VNAME_OF_PICK, 'money'),
        FF('Lowest price', 'IFERROR(INDEX({range:winners.lowest_price},MATCH(%s,{range:winners.vendor},0)),"")' % VNAME_OF_PICK, 'text'),
        FF('Lowest true total', 'IFERROR(INDEX({range:winners.lowest_total},MATCH(%s,{range:winners.vendor},0)),0)' % VNAME_OF_PICK, 'money'),
        FF('Best fit', 'IFERROR(INDEX({range:winners.best_fit},MATCH(%s,{range:winners.vendor},0)),"")' % VNAME_OF_PICK, 'text'),
        FF('Best value above the lowest price', 'IFERROR(INDEX({range:winners.extra_for_best},MATCH(%s,{range:winners.vendor},0)),0)' % VNAME_OF_PICK, 'money')],
        {"from": "quotes", "match": "quotes.vendor_id", "columns": ["option", "status", "true_total", "fit", "reviews", "valid_until"], "max": 4}),
    FORM('terms_sheet', 'Contract Terms Sheet', 'The terms of one contract', 'vendors.vendor_id', F(('Vendor', 'vendors.vendor'), ('Status', 'vendors.status'), ('Contract total', 'vendors.contract_total'), ('What is included', 'vendors.included'),
        ('What is not included', 'vendors.excluded'), ('Cancellation terms', 'vendors.cancel_terms'), ('Final payment date', 'vendors.final_pay_date'), ('Final headcount date', 'vendors.headcount_date'),
        ('Arrival and set-up', 'vendors.arrival_note'), ('Overtime rate per hour', 'vendors.ot_rate')),
        {"from": "contracts", "match": "contracts.vendor_id", "columns": ["kind", "detail", "item_date", "amount"], "max": 10}),
    FORM('date_sheet', 'Contract Date Sheet', 'One contract date', 'deadlines.ref_id', F(('Source', 'deadlines.source'), ('Vendor', 'deadlines.vendor'), ('Kind', 'deadlines.kind'), ('Date', 'deadlines.date'), ('Amount due', 'deadlines.amount'),
        ('Days left', 'deadlines.days_left'), ('Flag', 'deadlines.flag'), ('Done', 'deadlines.done'))),
    FORM('booking_sheet', 'Booking Sheet', 'One booking with its payments', 'vendors.vendor_id', F(('Vendor', 'vendors.vendor'), ('Status', 'vendors.status'), ('Booked on', 'vendors.booked_on'), ('Contract total', 'vendors.contract_total'), ('Deposit', 'vendors.deposit_due'),
        ('Paid so far', 'vendors.paid_so_far'), ('Still due', 'vendors.still_due'), ('Final payment date', 'vendors.final_pay_date'), ('Payer', 'vendors.payer'), ('Phone', 'vendors.phone')),
        {"from": "schedule", "match": "schedule.vendor_id", "columns": ["kind", "due_date", "amount_due", "amount_paid", "status"], "max": 6}),
    FORM('contact_sheet', 'Vendor Contact Sheet', 'One vendor for the day', 'contact.vendor', F(('Vendor ID', 'contact.vendor_id'), ('Contact', 'contact.contact'), ('Phone', 'contact.phone'), ('Status', 'contact.status'), ('First arrival', 'contact.arrival'),
        ('Meeting point', 'contact.meeting_point'), ('First task on the day', 'contact.first_task'), ('Steps in the run of show', 'contact.steps'), ('Last step ends', 'contact.last_out'), ('Confirmed for the day', 'contact.confirmed'))),
    FORM('followup_sheet', 'Vendor Follow-up Sheet', 'One vendor to chase', 'followups.vendor', F(('Status', 'followups.status'), ('Last contact', 'followups.last_contact'), ('Days since contact', 'followups.days_since'), ('Follow-up date', 'followups.follow_up'),
        ('Open quote valid until', 'followups.quote_valid'), ('Days to quote expiry', 'followups.quote_days'), ('Urgency', 'followups.urgency'), ('Chase order', 'followups.rank'), ('Flag', 'followups.flag'))),
    FORM('arrival_sheet', 'Arrival and Set-up Sheet', 'One step with a vendor', 'arrivals.step_id', F(('Vendor', 'arrivals.vendor'), ('Start', 'arrivals.start'), ('Minutes', 'arrivals.minutes'), ('End', 'arrivals.end'), ('Place', 'arrivals.place'),
        ('Block', 'arrivals.block'), ('Steps it overlaps', 'arrivals.overlaps'), ('Minutes before the next vendor', 'arrivals.gap_next'), ('Flag', 'arrivals.flag'))),
    FORM('meal_sheet', 'Vendor Meal Sheet', 'One vendor and its meals', 'meals.vendor', F(('People on site', 'meals.crew'), ('Arrives', 'meals.first_in'), ('Last step ends', 'meals.last_out'), ('Hours on site', 'meals.hours'),
        ('Meal needed', 'meals.needed'), ('Meals to order', 'meals.count'))),
    FORM('cancel_sheet', 'Cancellation Request Sheet', 'One cancellation, what is at risk', 'cancel.vendor', F(('Category', 'cancel.category'), ('Contract total', 'cancel.contract_total'), ('Deposit paid', 'cancel.deposit_paid'), ('Paid in total', 'cancel.paid_total'),
        ('Non-refundable estimate', 'cancel.non_refundable'), ('At risk if you cancel', 'cancel.at_risk'), ('Share of paid at risk', 'cancel.share_lost'), ('Cancellation terms', 'cancel.terms'))),
    FORM('decline_sheet', 'Decline Note Sheet', 'One quote you decline', 'quotes.quote_id', F(('Vendor', 'quotes.vendor'), ('Category', 'quotes.category'), ('Option', 'quotes.option'), ('Status', 'quotes.status'), ('Quote date', 'quotes.quote_date'),
        ('Base price', 'quotes.base_price'), ('True total', 'quotes.true_total'), ('Contact', 'quotes.contact'))),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('shortlist_page', 'Vendor Shortlist Page', 'Vendor shortlist for one slot', 'winners.vendor', [
        '{set:couple}, dated {today}. Shortlist for the {col:winners.vendor}, category {col:winners.category}.',
        'Best value on our weights: {col:winners.best_value}, true total {col:winners.best_total}. Lowest price: {col:winners.lowest_price}, true total {col:winners.lowest_total}. Best fit: {col:winners.best_fit}.',
        'The best value costs {col:winners.extra_for_best} more than the lowest price. The true total is the quote plus service charge, taxes, delivery, overtime and travel. Quotes are estimates.'], ['The couple', 'Parent'], NOTE),
    DOC('compare_page', 'Quote Comparison Page', 'Quote comparison for one slot', 'winners.vendor', [
        '{set:couple}, dated {today}. Quotes for the {col:winners.vendor}, side by side.',
        'True total: Option A {col:winners.total_a}, Option B {col:winners.total_b}, Option C {col:winners.total_c}. Best value: {col:winners.best_value}. Lowest price: {col:winners.lowest_price}.',
        'Second best: {col:winners.second_value}, true total {col:winners.second_total}. Check each quote for what is included and its valid-until date.'], ['The couple', 'Parent'], NOTE),
    DOC('booking_request', 'Booking Confirmation Request', 'Booking confirmation request to a vendor', 'vendors.vendor_id', [
        'Dear {col:vendors.contact}, dated {today}.',
        'We would like to confirm the booking of the {col:vendors.vendor} for our wedding on {set:wedding_day}, for {set:headcount} guests. Agreed total: {col:vendors.contract_total}. Deposit: {col:vendors.deposit_due}.',
        'Please confirm the date, the price and what is included: {col:vendors.included}. Please also send the final payment date and the cancellation terms in writing.',
        'With thanks, {set:couple}.'], ['The couple', 'The vendor'], NOTE),
    DOC('contract_summary', 'Contract Summary Page', 'Contract summary for one vendor', 'vendors.vendor_id', [
        '{set:couple}, dated {today}. Contract summary for the {col:vendors.vendor}, contact {col:vendors.contact}.',
        'Included: {col:vendors.included}. Not included: {col:vendors.excluded}. Cancellation terms: {col:vendors.cancel_terms}.',
        'Final payment date: {col:vendors.final_pay_date}. Final headcount date: {col:vendors.headcount_date}. Arrival and set-up: {col:vendors.arrival_note}. Overtime rate per hour: {col:vendors.ot_rate}.',
        'This is a summary of what you recorded. Check your contract for the exact wording.'], ['The couple'], NOTE),
    DOC('deadline_page', 'Contract Deadline Page', 'One contract deadline', 'deadlines.ref_id', [
        '{set:couple}, dated {today}. Item {col:deadlines.ref_id}: {col:deadlines.source} for the {col:deadlines.vendor}.',
        'Kind: {col:deadlines.kind}. Date: {col:deadlines.date}. Days left: {col:deadlines.days_left}. Flag: {col:deadlines.flag}. Amount due: {col:deadlines.amount}.',
        'Red, amber and green follow the limits you set in Settings. Check your contract for the exact date.'], ['The couple', 'Day-of coordinator'], NOTE),
    DOC('contact_page', 'Vendor Day-of Contact Page', 'Vendor day-of contact sheet', 'contact.vendor', [
        '{set:couple}, wedding on {set:wedding_day}. Contact for the {col:contact.vendor}: {col:contact.contact}, {col:contact.phone}.',
        'First arrival: {col:contact.arrival}. Meeting point: {col:contact.meeting_point}. First task: {col:contact.first_task}.',
        'Last step ends: {col:contact.last_out}. Confirmed for the day: {col:contact.confirmed}. Share this page only with the day-of coordinator.'], ['The couple', 'Day-of coordinator'], NOTE),
    DOC('arrival_page', 'Vendor Arrival Page', 'Vendor arrival schedule', 'arrivals.step_id', [
        '{set:couple}, wedding on {set:wedding_day}. Step {col:arrivals.step_id}: {col:arrivals.vendor}.',
        'Starts {col:arrivals.start}, {col:arrivals.minutes} minutes, ends {col:arrivals.end}. Place: {col:arrivals.place}. Block: {col:arrivals.block}.',
        'Steps it overlaps: {col:arrivals.overlaps}. Minutes before the next vendor in the same place: {col:arrivals.gap_next}. Flag: {col:arrivals.flag}.'], ['The couple', 'Day-of coordinator'], NOTE),
    DOC('meal_page', 'Vendor Meal List Page', 'Vendor meal list', 'meals.vendor', [
        '{set:couple}, wedding on {set:wedding_day}. Vendor meals for the {col:meals.vendor}.',
        'People on site: {col:meals.crew}. Arrives {col:meals.first_in}, last step ends {col:meals.last_out}, {col:meals.hours} hours on site. Meal needed: {col:meals.needed}. Meals to order: {col:meals.count}.',
        'Tell the caterer about any dietary note when you send the count.'], ['The couple', 'The caterer'], NOTE),
    DOC('cancel_page', 'Cancellation Exposure Page', 'Cancellation exposure for one vendor', 'cancel.vendor', [
        '{set:couple}, dated {today}. Cancellation exposure for the {col:cancel.vendor}, category {col:cancel.category}.',
        'Contract total: {col:cancel.contract_total}. Deposit paid: {col:cancel.deposit_paid}. Paid in total: {col:cancel.paid_total}. Non-refundable estimate: {col:cancel.non_refundable}. At risk if you cancel: {col:cancel.at_risk}.',
        'Cancellation terms: {col:cancel.terms}. This is an estimate. Check your contract before you cancel.'], ['The couple'], NOTE),
    DOC('decline_note', 'Decline Note', 'Decline note to a vendor', 'quotes.quote_id', [
        'Dear {col:quotes.contact}, dated {today}.',
        'Thank you for your quote for {col:quotes.category}, {col:quotes.option}, dated {col:quotes.quote_date}. After careful thought we have chosen another vendor for our wedding on {set:wedding_day}.',
        'We appreciate the time you took and wish you well. With thanks, {set:couple}.'], ['The couple'], NOTE),
    DOC('vendor_brief', 'Vendor Brief', 'Vendor brief for the day', 'vendors.vendor_id', [
        'Dear {col:vendors.contact}, dated {today}. This is what we need from you on {set:wedding_day}.',
        'Your first step is at {col:vendors.arrival} at the {col:vendors.meeting_point}: {col:vendors.first_task}. You have {col:vendors.steps} steps in the run of show.',
        'Please arrive on time and tell our day-of coordinator, {col:vendors.coordinator}, when you are set up. Please tell us if anything on this page needs to change. With thanks, {set:couple}.'], ['The couple', 'The vendor'], NOTE),
    DOC('final_confirmation', 'Vendor Final Confirmation', 'Vendor final confirmation, one week before', 'vendors.vendor_id', [
        'Dear {col:vendors.contact}, dated {today}. Our wedding is on {set:wedding_day}, and we would like to confirm the last details.',
        'Please confirm your arrival at {col:vendors.arrival} at the {col:vendors.meeting_point}, the number of guests, {set:headcount}, and what is included: {col:vendors.included}.',
        'Amount still due to you: {col:vendors.still_due}. Please send the final invoice and tell us if any detail has changed. With thanks, {set:couple}.'], ['The couple', 'The vendor'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('new_enquiry', 'New vendor enquiry', 'vendors', 'vendors.last_contact', [('Write down what you need, your date and your headcount', 0), ('Ask for a quote in writing', 1), ('Ask what is included and what is not', 2),
        ('Ask for service charge, taxes, delivery, overtime and travel', 3), ('Note the date the quote is valid until', 4), ('Add the quote to Quotes', 5), ('Note how many days they took to reply', 7)]),
    CHK('compare_quotes', 'Compare quotes', 'quotes', 'quotes.quote_date', [('Enter every extra so the true total is complete', 1), ('Rate fit, reply and reviews from 1 to 5', 2), ('Look at the True-Cost Comparison', 3),
        ('Run the Weighted Score Ranker', 4), ('Run the Price against Fit tool', 5), ('Ask the second quote for a better price', 7), ('Choose before the quote expires', 10)]),
    CHK('before_signing', 'Before signing a contract', 'vendors', 'vendors.booked_on', [('Read the whole contract, check your contract for anything unclear', -14), ('Check the date, the price and what is included', -12), ('Check the cancellation terms', -10),
        ('Check the final payment date and the final headcount date', -8), ('Check the overtime rate and the arrival and set-up times', -6), ('Ask about insurance and venue rules', -4), ('Ask the questions that are open', -2), ('Sign and keep a copy', 0)]),
    CHK('after_signing', 'After signing, record the terms', 'vendors', 'vendors.booked_on', [('Mark the vendor Booked and enter the contract total', 0), ('Add what is included and not included to Contract Items', 1), ('Add the cancellation terms', 1),
        ('Add the final payment date and final headcount date', 2), ('Add the arrival and set-up times and the overtime rate', 2), ('Add the payments to the Payment Schedule', 3), ('Tell the day-of coordinator', 7)]),
    CHK('deposit_receipt', 'Deposit and receipt', 'schedule', 'schedule.due_date', [('Check the amount against your contract', -7), ('Ask for an invoice', -5), ('Pay and keep the payment confirmation', 0), ('Ask the vendor to confirm receipt', 1), ('Enter the payment in your money workbook', 2), ('File the receipt', 3)]),
    CHK('weekly_followup', 'Weekly vendor follow-up', 'vendors', 'vendors.last_contact', [('Open the Follow-up Ranker', 7), ('Call or message the first vendor on the list', 8), ('Note the answer in Vendors', 8), ('Check which quotes expire this month', 9), ('Chase any vendor silent for more than your limit', 10), ('Tell your partner what changed', 14)]),
    CHK('deadline_review', 'Contract deadline review', 'schedule', 'schedule.due_date', [('Check the final payment date in your contract', -60), ('Check the final headcount date', -45), ('Run the Contract Deadline Countdown', -30), ('Ask for the final invoice', -21), ('Check the money set aside covers it', -14), ('Pay', -3), ('Ask the vendor to confirm', 0)]),
    CHK('week_before', 'Week-before vendor confirmation', 'run', 'run.date', [('Send each vendor the Vendor Brief', -14), ('Ask each vendor to confirm the arrival time', -10), ('Send the final headcount where it is due', -9), ('Print the Day-of Contact Sheet', -7), ('Give the day-of coordinator the contact sheet', -6), ('Confirm the final payments and tips', -5), ('Check the weather plan with the venue', -3)]),
    CHK('meals_access', 'Vendor meals and access', 'run', 'run.date', [('Run the Vendor Meals Count', -30), ('Tell the caterer how many vendor meals', -21), ('Ask the venue about parking and loading access', -21), ('Share the arrival times with each vendor', -14), ('Name one person who greets the vendors', -7), ('Put the meal list in the coordinator folder', -2)]),
    CHK('rules_insurance', 'Vendor insurance and rules', 'run', 'run.date', [('Ask the venue what its vendors must show, check your contract', -90), ('Ask each vendor if they carry their own cover', -75), ('Ask about noise limits and the finish time', -60), ('Ask about decor rules, such as candles', -45), ('Write the answers in Contract Items', -40), ('Share the rules with the vendors', -14)]),
    CHK('decline_politely', 'Decline politely', 'quotes', 'quotes.quote_date', [('Decide and mark the quote Declined', 14), ('Write the Decline Note', 15), ('Thank the vendor for the time', 15), ('Do not give reasons you do not need to', 16), ('Keep the quote in case you need a second choice', 20)]),
    CHK('small_first3', 'Small wedding first vendors', 'vendors', 'vendors.booked_on', [('List five vendors: venue, caterer, photographer, officiant, music', 0), ('Ask each for a quote for your headcount', 1), ('Compare the true totals', 3), ('Book the venue first', 7), ('Book the caterer', 10), ('Book the photographer', 14)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
M = MSG
messages = [
    M('m_ven_quote', 'Venue: ask for a quote', 'contact', 'contact.ph_venue', 'Hello {contact}, we would like a quote for {wedding_day} for {guests} guests. Please send the price and what it includes. {couple}'),
    M('m_ven_inc', 'Venue: what is included', 'contact', 'contact.ph_venue', 'Hello {contact}, please send in writing what the booking includes and excludes. {couple}'),
    M('m_ven_final', 'Venue: final payment and cancellation', 'contact', 'contact.ph_venue', 'Hello {contact}, please confirm the final payment date and the cancellation terms. {couple}'),
    M('m_ven_access', 'Venue: access and set-up times', 'contact', 'contact.ph_venue', 'Hello {contact}, please confirm access and set-up times for {wedding_day}. {couple}'),
    M('m_ven_rules', 'Venue: rules for vendors', 'contact', 'contact.ph_venue', 'Hello {contact}, please confirm your rules for vendors, noise and overtime. {couple}'),
    M('m_cat_quote', 'Caterer: quote with price per person', 'contact', 'contact.ph_caterer', 'Hello {contact}, we need a quote for {guests} guests with the price per person. {couple}'),
    M('m_cat_guar', 'Caterer: minimum guarantee and count', 'contact', 'contact.ph_caterer', 'Hello {contact}, please confirm the minimum guarantee and the final count date. {couple}'),
    M('m_cat_arr', 'Caterer: arrival time', 'contact', 'contact.ph_caterer', 'Hello {contact}, please confirm your arrival at {arrival} on {wedding_day}. {couple}'),
    M('m_ph_avail', 'Photographer: availability and quote', 'contact', 'contact.ph_photog', 'Hello {contact}, are you free on {wedding_day}? Please send your quote. {couple}'),
    M('m_ph_shot', 'Photographer: shot list and arrival', 'contact', 'contact.ph_photog', 'Hello {contact}, please confirm the shot list and your arrival at {arrival}. {couple}'),
    M('m_band_sound', 'Band or DJ: sound check', 'contact', 'contact.ph_band', 'Hello {contact}, please confirm the sound check at {arrival} and the date of the music list. {couple}'),
    M('m_band_ot', 'Band or DJ: overtime and finish', 'contact', 'contact.ph_band', 'Hello {contact}, please confirm your overtime rate and the finish time. {couple}'),
    M('m_flo_quote', 'Florist: quote for the design brief', 'contact', 'contact.ph_florist', 'Hello {contact}, please send your quote for our design brief. {couple}'),
    M('m_flo_deliv', 'Florist: delivery and set-up', 'contact', 'contact.ph_florist', 'Hello {contact}, please confirm delivery and set-up at {arrival} on {wedding_day}. {couple}'),
    M('m_off', 'Officiant: ceremony date and time', 'contact', 'contact.ph_officiant', 'Hello {contact}, please confirm the ceremony date, {wedding_day}, and the start time. {couple}'),
    M('m_cake', 'Cake baker: delivery', 'contact', 'contact.ph_cake', 'Hello {contact}, please confirm delivery of the cake before the cutting at {arrival} on {wedding_day}. {couple}'),
    M('m_hair', 'Hair and makeup: trial and day times', 'contact', 'contact.ph_hair', 'Hello {contact}, please confirm the trial and the start at {arrival} on {wedding_day}. {couple}'),
    M('m_attire', 'Attire shop: order and pick-up', 'contact', 'contact.ph_attire', 'Hello {contact}, please confirm our order and the pick-up date. {couple}'),
    M('m_stat', 'Stationery printer: proof and print', 'contact', 'contact.ph_stat', 'Hello {contact}, please confirm the proof and the print date. {couple}'),
    M('m_rent', 'Rentals: quantities and delivery', 'contact', 'contact.ph_rent', 'Hello {contact}, please confirm quantities and the delivery window on {wedding_day}. {couple}'),
    M('m_trans', 'Transport: ask for a quote', 'contact', 'contact.ph_trans', 'Hello {contact}, we need a quote for {guests} guests on {wedding_day}. {couple}'),
    M('m_coord_dates', 'Coordinator: contract dates', 'contact', 'contact.ph_coord', 'Hello {contact}, we will send you the contract dates for the vendors. Please check them against your timeline. {couple}'),
    M('m_coord_arr', 'Coordinator: arrival times we share', 'contact', 'contact.ph_coord', 'Hello {contact}, please confirm the arrival times we share with the vendors for {wedding_day}. {couple}'),
    M('m_hotel', 'Hotel contact: block and cut-off', 'contact', 'contact.ph_hotel', 'Hello {contact}, please confirm the block size and the cut-off date. {couple}'),
    M('m_cancel', 'Vendor: we need to cancel', 'contact', 'contact.ph_cancel', 'Hello {contact}, we need to cancel our booking. Please send the cancellation terms. {couple}'),
    M('m_vid_valid', 'Videographer: your quote is valid', 'quotes', 'quotes.ph_vq', 'Hello {contact}, your quote of {base_price} is valid until {valid_until}. Can we talk this week? {couple}'),
    M('m_vid_inc', 'Videographer: what the quote includes', 'quotes', 'quotes.ph_vinc', 'Hello {contact}, please confirm what your quote includes: {included}. {couple}'),
    M('m_tailor', 'Tailor: quote and fitting', 'quotes', 'quotes.ph_tq', 'Hello {contact}, your quote of {base_price} is valid until {valid_until}. Can we book the fitting? {couple}'),
    M('m_decline', 'Vendor: we chose another vendor', 'quotes', 'quotes.ph_decl', 'Hello {contact}, thank you. We have chosen another vendor for {category}. {couple}'),
    M('m_confirm', 'Vendor: confirm the booking and deposit', 'schedule', 'schedule.ph_conf', 'Hello {contact}, we are happy to confirm the booking. The deposit of {amount_due} is due on {due_date}. {couple}'),
    M('m_receipt', 'Vendor: confirm the deposit received', 'schedule', 'schedule.ph_rec', 'Hello {contact}, please confirm you received our deposit of {amount_paid}. {couple}'),
    M('m_final_pay', 'Vendor: your final payment', 'schedule', 'schedule.ph_final', 'Hello {contact}, your final payment of {amount_due} is due on {due_date}. We will pay on {pay_on}. {couple}'),
    M('m_partner_date', 'Partner: the next vendor date', 'deadlines', 'deadlines.ph_next', 'Hi, the next vendor date is {kind} for {vendor} on {date}. {couple}'),
    M('m_partner_silent', 'Partner: a vendor has not replied', 'followups', 'followups.ph_partner', 'Hi, {vendor} has not replied in {days_since} days. Who calls? {couple}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
DUE = lambda col: R('schedule', col)
kpis = [
    KPI('Vendors listed', 'COUNTIFS(%s,"<>")' % R('vendors', 'vendor_id'), 'int'),
    KPI('Vendors booked', 'COUNTIFS(%s,%s)' % (R('vendors', 'status'), BOOKED), 'int'),
    KPI('Categories still open', 'COUNTIFS(%s,">0")' % R('pipeline', 'open'), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Quotes received', 'COUNTIFS(%s,"<>")' % R('quotes', 'quote_id'), 'int'),
    KPI('Open quotes per open category', 'IFERROR(SUM(%s)/COUNTIFS(%s,">0"),0)' % (R('quotes', 'open_flag'), R('pipeline', 'open')), 'num'),
    KPI('Quotes expiring soon', 'COUNTIFS(%s,">=0",%s,"<="&{set:expiry_days})' % (R('quotes', 'days_to_expiry'), R('quotes', 'days_to_expiry')), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Quotes expired', 'COUNTIFS(%s,"<0")' % R('quotes', 'days_to_expiry'), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Booked contract total', 'SUM(%s)' % R('vendors', 'contract_total'), 'money'),
    KPI('Booked total against the plan', 'IFERROR(SUM(%s)/SUM(%s),0)' % (R('vendors', 'contract_total'), R('budget', 'planned')), 'pct'),
    KPI('Lowest quote total for open slots', 'SUM(%s)' % R('compare', 'low_open'), 'money'),
    KPI('Best-value quote total for open slots', 'SUM(%s)' % R('compare', 'lead_open'), 'money'),
    KPI('Average days to reply', 'IFERROR(AVERAGE(%s),0)' % R('quotes', 'response_days'), 'num'),
    KPI('Slowest reply, days', 'MAX(%s)' % R('quotes', 'response_days'), 'int'),
    KPI('Vendors silent for too long', 'COUNTIFS(%s,">"&{set:stale_days})' % R('vendors', 'days_since'), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Follow-ups due this week', 'COUNTIFS(%s,">="&{today},%s,"<="&{today}+7)' % (R('vendors', 'follow_up'), R('vendors', 'follow_up')), 'int'),
    KPI('Contract items recorded', 'COUNTIFS(%s,"<>")' % R('contracts', 'contract_id'), 'int'),
    KPI('Vendors missing a cancellation term', 'SUM(%s)' % R('vendors', 'missing_cancel'), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Vendors missing a final payment date', 'SUM(%s)' % R('vendors', 'missing_final'), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Next contract date', 'IFERROR(SMALL(%s,1),"")' % R('deadlines', 'next_contract'), 'date'),
    KPI('Days to the next contract date', 'IFERROR(SMALL(%s,1)-{today},"")' % R('deadlines', 'next_contract'), 'int'),
    KPI('Days to the final headcount date', 'IFERROR(SMALL(%s,1)-{today},"")' % R('deadlines', 'hc_next'), 'int'),
    KPI('Deposits paid', 'SUMIFS(%s,%s,%s)' % (DUE('amount_paid'), DUE('kind'), DEP), 'money'),
    KPI('Final balances due in 60 days', 'SUMIFS(%s,%s,%s,%s,"<>"&%s,%s,"<="&{today}+60)' % (DUE('amount_due'), DUE('kind'), FB, DUE('status'), PAID, DUE('due_date')), 'money', alert={"when": "> 0", "style": "warn"}),
    KPI('Cancellation exposure total', 'SUM(%s)' % R('cancel', 'at_risk'), 'money'),
    KPI('Overtime if the day runs over', '{set:overtime_hours}*SUMIFS(%s,%s,%s)' % (R('contracts', 'amount'), R('contracts', 'kind'), K_OT), 'money'),
    KPI('Extras added to the best-value quotes', 'SUM(%s)' % R('compare', 'lead_extras'), 'money'),
    KPI('Vendors on site on the day', 'COUNTIFS(%s,">0")' % R('contact', 'steps'), 'int'),
    KPI('Vendor meals needed', 'SUM(%s)' % R('meals', 'count'), 'int'),
    KPI('Arrival overlaps', 'COUNTIFS(%s,">0")' % R('arrivals', 'overlaps'), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Vendors booked in time', 'SUM(%s)' % R('lead', 'ok'), 'int'),
]
assert len(kpis) == 30
dashboard = {"title": "Vendor Dashboard", "kpis": kpis,
    "monthly": {"title": "Payments due, paid and contracts booked by month", "date": "schedule.due_date", "series": [
        {"label": "Payments due", "sum": "schedule.amount_due", "date": "schedule.due_date"}, {"label": "Paid", "sum": "schedule.amount_paid", "date": "schedule.due_date"},
        {"label": "Contracts booked", "sum": "vendors.contract_total", "date": "vendors.booked_on"}]},
    "breakdowns": [{"title": "Contract total by category", "by": "vendors.category", "value": "vendors.contract_total", "agg": "sum"}, {"title": "Quotes by status", "by": "quotes.status", "value": "quotes.quote_id", "agg": "count"},
                   {"title": "Payments due by category", "by": "schedule.category", "value": "schedule.amount_due", "agg": "sum"}, {"title": "Vendors by payer", "by": "vendors.payer", "value": "vendors.vendor_id", "agg": "count"}]}


def AG(kind, table, value=None, date=None, label=None, where=None): return AGG(kind, table, value, date, where, label)
insights = {"filters": [{"label": "Category", "list": "vcat"}, {"label": "Vendor", "list": "vname"}, {"label": "Status", "list": "vstatus"}],
    "gauges": [
        {"title": "Vendor slots booked", "num": AG('count', 'vendors', where=[('status', '=', BOOKED)]), "den": AG('count', 'vendors', where=[('lead_months', '>', 0)])},
        {"title": "Booked total against plan", "num": AG('sum', 'vendors', 'vendors.contract_total'), "den": AG('sum', 'budget', 'budget.planned')},
        {"title": "Contract terms recorded against needed", "num": AG('sum', 'vendors', 'vendors.terms_found'), "den": AG('sum', 'vendors', 'vendors.terms_needed')},
        {"title": "Open quotes still valid", "num": AG('sum', 'quotes', 'quotes.valid_n'), "den": AG('sum', 'quotes', 'quotes.open_flag')},
        {"title": "Vendors confirmed for the day", "num": AG('count', 'vendors', where=[('confirmed', '=', YES)]), "den": AG('count', 'vendors', where=[('status', '=', BOOKED)])},
        {"title": "Deposits paid against due", "num": AG('sum', 'schedule', 'schedule.amount_paid', where=[('kind', '=', DEP)]), "den": AG('sum', 'schedule', 'schedule.amount_due', where=[('kind', '=', DEP)])}],
    "charts": [
        CHART('Vendors by status', 'bar', 'vendors.status', [AG('count', 'vendors', label='Vendors')]),
        CHART('Vendors by category', 'bar', 'vendors.category', [AG('count', 'vendors', label='Vendors')]),
        CHART('Contract total by category', 'bar', 'vendors.category', [AG('sum', 'vendors', 'vendors.contract_total', label='Contract total')]),
        CHART('Planned against committed by category', 'bar', 'budget.category', [AG('sum', 'budget', 'budget.planned', label='Planned'), AG('sum', 'budget', 'budget.committed', label='Committed')]),
        CHART('Quotes by status', 'bar', 'quotes.status', [AG('count', 'quotes', label='Quotes')]),
        CHART('Quotes by category', 'bar', 'quotes.category', [AG('count', 'quotes', label='Quotes')]),
        CHART('True total of quotes by category', 'bar', 'quotes.category', [AG('sum', 'quotes', 'quotes.true_total', label='True total')]),
        CHART('Base price by option', 'bar', 'quotes.option', [AG('avg', 'quotes', 'quotes.base_price', label='Average base price')]),
        CHART('Overtime estimate by category', 'bar', 'quotes.category', [AG('sum', 'quotes', 'quotes.overtime', label='Overtime estimate')]),
        CHART('Quotes by month', 'column', 'month', [AG('count', 'quotes', date='quotes.quote_date', label='Quotes')]),
        CHART('Contracts booked by month', 'column', 'month', [AG('sum', 'vendors', 'vendors.contract_total', date='vendors.booked_on', label='Contract total')]),
        CHART('Days to reply by category', 'bar', 'quotes.category', [AG('avg', 'quotes', 'quotes.response_days', label='Average days to reply')]),
        CHART('Fit rating by category', 'bar', 'quotes.category', [AG('avg', 'quotes', 'quotes.fit', label='Average fit rating')]),
        CHART('Contract items by kind', 'bar', 'contracts.kind', [AG('count', 'contracts', label='Items')]),
        CHART('Contract dates by month', 'column', 'month', [AG('count', 'contracts', date='contracts.item_date', label='Dated items')]),
        CHART('Payments due by month', 'column', 'month', [AG('sum', 'schedule', 'schedule.amount_due', date='schedule.due_date', label='Payments due')]),
        CHART('Deposits paid by category', 'bar', 'schedule.category', [AG('sum', 'schedule', 'schedule.amount_paid', where=[('kind', '=', DEP)], label='Deposits paid')]),
        CHART('Cancellation exposure by category', 'bar', 'cancel.category', [AG('sum', 'cancel', 'cancel.at_risk', label='At risk')]),
        CHART('Vendors by payer', 'bar', 'vendors.payer', [AG('count', 'vendors', label='Vendors')]),
        CHART('Run-of-show steps by block', 'bar', 'run.block', [AG('count', 'run', label='Steps')]),
        CHART('Lead months by category', 'bar', 'vendors.category', [AG('avg', 'vendors', 'vendors.lead_months', label='Typical lead months')]),
        CHART('Last contacts and follow-ups by month', 'column', 'month', [AG('count', 'vendors', date='vendors.last_contact', label='Last contact'), AG('count', 'vendors', date='vendors.follow_up', label='Follow-up planned')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "True-cost comparison", "why": "every quote with service charge, taxes, delivery, overtime, travel and tip added, so the cheapest quote is really the cheapest", "where": "True-Cost Comparison"},
    {"name": "Weighted score ranker", "why": "price plus your own ratings for fit, reply and reviews with weights you edit, so you see the best fit and not only the lowest price", "where": "Weighted Score Ranker"},
    {"name": "Quote negotiation lever", "why": "a closed-form drop that lets the second-best quote win, so you know whom to ask and for how much", "where": "Quote Negotiation Lever"},
    {"name": "Contract completeness check", "why": "each booked vendor has what is included, cancellation terms, the final payment date and arrival, and the check names what is missing", "where": "Contract Completeness Check"},
    {"name": "Final headcount date alarm", "why": "the date the caterer, venue and rentals need the count, with the figure to send and the days left", "where": "Final Headcount Alarm"},
    {"name": "Cancellation exposure", "why": "the deposits and payments you could lose if you cancelled, per vendor and in total, using your own refund window", "where": "Cancellation Exposure"},
    {"name": "Arrival overlap finder", "why": "two vendors setting up in the same place at the same time are found before the day, with the first clash time", "where": "Arrival Overlap Finder"},
    {"name": "Contract deadline countdown", "why": "contract dates, unpaid payments and quote expiry dates in one list with red, amber and green from your own limits", "where": "Contract Deadlines"},
    {"name": "Booking deadline ranker", "why": "open categories ranked by the days left before the latest booking date from each typical lead time", "where": "Booking Deadline Ranker"},
    {"name": "Plan fit by category", "why": "booked contracts plus the leading quote of every open slot against each budget line, with the room left", "where": "Plan Fit by Category"}]
competitors = [
    {"what": "a free planning app", "lacks": "keeps a vendor list but cannot compare quotes on a true total, has no contract deadline list and no cancellation exposure"},
    {"what": "a single budget spreadsheet", "lacks": "has one price per vendor, no service charge, taxes or overtime, no scoring and no contract dates"},
    {"what": "a printable wedding binder", "lacks": "has blank vendor pages but does no sums, no quote comparison and no arrival overlap check"},
    {"what": "a wedding website with a registry", "lacks": "lists vendors for you to pay for, shares your plans with a company and has no true-cost comparison or private contract record"}]
guide = [
    'Open Start here and type your names, the wedding day and your headcount in the yellow cells. Replace demo data: clear the sample rows and type your own.',
    'List every vendor in Vendors with its status, contact, typical lead time and last contact. Days since contact and the first arrival on the day fill in by themselves.',
    'Enter up to three quotes for each vendor in Quotes with every extra: service charge, taxes, delivery, overtime, travel and an optional tip. The true total and the days to expiry fill in.',
    'Edit the weights in Scoring Weights, then read True-Cost Table and Category Winners for the best value, the lowest price and the best fit of each vendor.',
    'When you book, mark the vendor Booked and add what the contract says to Contract Items: included, cancellation terms, final dates, arrival and overtime rate. Check your contract.',
    'Keep Payment Schedule, Budget Lines and Run of Show the same as your money and run-of-show workbooks; they are copies the vendor checks use.',
    'Open Contract Deadlines for every date that matters, Pipeline by Category for the latest booking dates and Follow-up List for who to call.',
    'Use Vendor Arrivals, Vendor Meals List and Day-of Contact Sheet to prepare the day, and Cancellation by Vendor to see what is at risk.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'A couple with a small wedding (30 guests, no wedding party) uses the same sheets with about five vendors and a few rows.',
    'This workbook has no macros and works in Excel and Google Sheets. Print any page for a parent or a helper.',
    'Why a workbook: one flat price, no vendor ever sees your details, your own numbers, and it works offline.',
    'What this is not: not a booking service, not a payment service, and not legal, tax or insurance advice. Every default is a typical starting value you can edit, never a promise.']
listing = {"title": "Wedding Vendor Tracker Excel Template: Quote Comparison, True Cost, Contract Deadlines, Vendor Contact Sheet, Cancellation Terms",
    "headline": "Compare every quote on its true cost and never miss a contract date",
    "tags": ["wedding vendors", "vendor tracker", "quote comparison", "wedding planner", "contract deadlines", "vendor contacts", "wedding spreadsheet", "excel template", "true cost", "wedding checklist", "vendor contract", "day of timeline", "small wedding"],
    "description": ("Keep every wedding vendor in one Excel workbook. Built for an engaged couple planning their own wedding, with a parent or a day-of coordinator who gets a printed page. No vendor ever sees your details.\n\n"
        "Vendors holds every slot from first enquiry to the day: venue, caterer, photographer, videographer, band or DJ, florist, officiant, cake baker, hair and makeup, attire shop, tailor, stationery printer, rentals, transport, day-of coordinator and hotel room block. Quotes holds up to three options for each with every extra: service charge, taxes, delivery, overtime, travel and an optional tip, so the true total of each quote is clear. "
        "Scoring Weights, True-Cost Table and Category Winners rank the quotes on price and on your own ratings of fit, reply and reviews, with weights you edit.\n\n"
        "Contract Items records what each booked contract includes and excludes, the cancellation terms, the final headcount and final payment dates, arrival and set-up and the overtime rate. Contract Deadlines puts every date, unpaid payment and quote expiry in one list with red, amber and green from your own limits. Pipeline by Category shows the latest booking date for each open category from its typical lead time.\n\n"
        f"{len(tools)} tools answer weekly questions: which quote is really cheapest, which fits best, how much the second quote must drop to win, whether a quote fits its budget line, which vendor has missing terms, when the final headcount is due, what a cancellation could cost, whether two vendors clash on the day and who to call today. Print {len(forms)} sheets and {len(documents)} pages, follow {len(checklists)} checklists and send {len(messages)} ready text messages to vendors, the day-of coordinator and your partner.\n\n"
        "A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Every default is a typical starting value you can edit, and every estimate is your own. It is not a booking service, not a payment service and not legal, tax or insurance advice. This is part three of the Wedding Planning suite."),
    "features": ["True-cost comparison of every quote", "Weighted score on price, fit, reply and reviews", "Quote negotiation lever", "Contract items with cancellation terms", "Contract deadlines with red, amber and green", "Final headcount date alarm",
                 "Cancellation exposure by vendor", "Vendor arrival overlap finder", "Day-of vendor contact sheet", f"{len(tools)} decision tools", f"{len(forms)} printable sheets and {len(documents)} pages",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}

lists = BASE_LISTS + verdict_lists()
assert len(lists) <= 20, len(lists)
s = spec(id=f'{SUITE}-p3', slug='wedding-vendors', profession='Wedding Planning', name='Vendors, Quotes and Contracts',
         tagline='Compare quotes on true cost and track every vendor contract date', price_usd=29,
         colors={"primary": "#7A4B68", "accent": "#D9A86C"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 3, "of": 8, "focus": "Vendors, quotes and contracts"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wp3.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'lists', len(lists), 'desc', len(listing['description']), 'title', len(listing['title']), 'tag', len(s['tagline']))
