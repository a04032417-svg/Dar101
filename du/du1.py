"""Doula Business suite - part 1: Enquiries, Consultations and Quotes."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du1_lists import *
from du1_tables import settings, tables
from du1_tools import tools, NN, NB, NH, NS, R1_, R2_, R3_, PS
import du1_data as D

SUITE = 'fx-20261115-doula-business'
NOTE = "Sample wording: adapt it to your own business and check your local rules."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
Y12 = '">="&({today}-365)'
LOST = tok('estatus', 'Lost'); SIGNED = tok('estatus', 'Signed')
O_SIGNED = tok('outcome', 'Signed'); O_BOOKED = tok('outcome', 'Booked'); O_NOSHOW = tok('outcome', 'No-show')
Q_OPEN = tok('qstatus', 'Open'); Q_SIGNED = tok('qstatus', 'Signed')

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('enquiry_sheet', 'Enquiry Sheet', 'Enquiry with reply time and source conversion', 'enquiries.enquiry_id', F(
        ('Date', 'enquiries.date'), ('Name', 'enquiries.name'), ('Phone', 'enquiries.phone'), ('E-mail', 'enquiries.email'), ('Area', 'enquiries.area'), ('Service wanted', 'enquiries.service'),
        ('Due date wanted', 'enquiries.edd_wanted'), ('Source', 'enquiries.source'), ('Hours to the first reply', 'enquiries.first_reply_hours'), ('Reply check', 'enquiries.reply_flag'), ('Status', 'enquiries.status'),
        ('Package quoted', 'enquiries.package_quoted'), ('Quote', 'enquiries.quote'), ('Consultation date', 'enquiries.consult_date'), ('Signed on', 'enquiries.signed_on'), ('Client ID', 'enquiries.client_id')) + [
        FF('Enquiries from this source, 12 months', 'COUNTIFS({range:enquiries.source},%s,{range:enquiries.date},%s)' % (LK('enquiries', 'enquiry_id', 'source'), Y12), 'int'),
        FF('Conversion of this source, 12 months', 'IFERROR(INDEX({range:source_conv.conversion},MATCH(%s,{range:source_conv.source},0)),0)' % LK('enquiries', 'enquiry_id', 'source'), 'pct')]),
    FORM('consult_booking_sheet', 'Consultation Booking Sheet', 'Consultation day with free slots', 'consult_cal.date', F(
        ('Date', 'consult_cal.date'), ('Weekday', 'consult_cal.weekday'), ('Doula on duty', 'consult_cal.doula'), ('Consultations booked', 'consult_cal.booked'), ('Free slots', 'consult_cal.free_slots'), ('Day check', 'consult_cal.slot_flag')) + [
        FF('Consultation slots you give a day', '{set:consult_slots_day}', 'int'), FF('Consultations booked, next 7 days', 'COUNTIFS({range:consults.date},">="&{today},{range:consults.date},"<="&({today}+6),{range:consults.outcome},%s)' % O_BOOKED, 'int')],
        {"from": "consults", "match": "consults.date", "columns": ["name", "doula", "outcome"], "max": 8}),
    FORM('consult_notes_sheet', 'Consultation Notes Sheet', 'Consultation outcome and follow-up', 'consults.consult_id', F(
        ('Date', 'consults.date'), ('Name', 'consults.name'), ('Phone', 'consults.phone'), ('Doula', 'consults.doula'), ('Doula phone', 'consults.doula_phone'), ('Minutes', 'consults.minutes'), ('Outcome', 'consults.outcome'),
        ('Follow-up on', 'consults.follow_up_on'), ('Days since', 'consults.days_since'), ('Follow-up check', 'consults.follow_flag')) + [
        FF('Signed share of this doula, 12 months', 'IFERROR(INDEX({range:doula_cons.signed_share},MATCH(%s,{range:doula_cons.doula},0)),0)' % LK('consults', 'consult_id', 'doula'), 'pct'),
        FF('Days you wait before a follow-up', '{set:follow_up_days}', 'int')]),
    FORM('quote_sheet', 'Quote Sheet', 'Quote with deposit, balance and instalments', 'quotes.quote_id', F(
        ('Quote date', 'quotes.quote_date'), ('Name', 'quotes.name'), ('Phone', 'quotes.phone'), ('Package', 'quotes.package'), ('Due date wanted', 'quotes.edd_wanted'), ('List price', 'quotes.list_price'), ('Discount', 'quotes.discount'),
        ('Discount amount', 'quotes.discount_amount'), ('Add-ons', 'quotes.addons'), ('Travel fee', 'quotes.travel_fee'), ('Quote total', 'quotes.quote_total'), ('Deposit', 'quotes.deposit'), ('Balance', 'quotes.balance'),
        ('Balance due date', 'quotes.balance_due'), ('Instalments', 'quotes.instalments'), ('Instalment amount', 'quotes.instalment'), ('Valid until', 'quotes.valid_until'), ('Status', 'quotes.status'))),
    FORM('quote_followup_sheet', 'Quote Follow-up Sheet', 'Quote follow-up with days left', 'quotes.quote_id', F(
        ('Name', 'quotes.name'), ('Phone', 'quotes.phone'), ('Package', 'quotes.package'), ('Quote total', 'quotes.quote_total'), ('Quote date', 'quotes.quote_date'), ('Valid until', 'quotes.valid_until'), ('Days left', 'quotes.days_left'),
        ('Expiry check', 'quotes.expiry_flag'), ('Status', 'quotes.status')) + [
        FF('Follow-up date', '%s+{set:follow_up_days}' % LK('quotes', 'quote_id', 'quote_date'), 'date'), FF('Open quotes now', 'COUNTIFS({range:quotes.status},%s)' % Q_OPEN, 'int'),
        FF('Value of open quotes', 'SUMIFS({range:quotes.quote_total},{range:quotes.status},%s)' % Q_OPEN, 'money')]),
    FORM('package_compare_sheet', 'Package Comparison Sheet', 'Package with income per hour and win rate', 'packages.package_id', F(
        ('Package', 'packages.package'), ('Kind', 'packages.kind'), ('Price', 'packages.price'), ('Birth hours', 'packages.birth_hours'), ('Prenatal visits', 'packages.prenatal_visits'), ('Postpartum hours', 'packages.postpartum_hours'),
        ('Plan hours', 'packages.plan_hours'), ('Deposit share', 'packages.deposit_pct'), ('Income per hour', 'packages.income_hour'), ('Price for the target', 'packages.price_needed'), ('Target check', 'packages.target_flag'),
        ('Quotes, 12 months', 'packages.quotes_12m'), ('Signed, 12 months', 'packages.signed_12m'), ('Win rate at quote', 'packages.win_rate')) + [FF('Income per hour you want', '{set:target_income_hour}', 'money')]),
    FORM('intake_contact_sheet', 'Intake Contact Sheet', 'Contact details and the on-call window to plan', 'enquiries.enquiry_id', F(
        ('Name', 'enquiries.name'), ('Phone', 'enquiries.phone'), ('E-mail', 'enquiries.email'), ('Area', 'enquiries.area'), ('Service wanted', 'enquiries.service'), ('Due date wanted', 'enquiries.edd_wanted'), ('Source', 'enquiries.source')) + [
        FF('On-call window opens', '%s-{set:oncall_before_days}' % LK('enquiries', 'enquiry_id', 'edd_wanted'), 'date'), FF('On-call window closes', '%s+{set:oncall_after_days}' % LK('enquiries', 'enquiry_id', 'edd_wanted'), 'date'),
        FF('Date held until', LK('enquiries', 'enquiry_id', 'hold_until'), 'date'), FF('Reply target, hours', '{set:reply_hours_target}', 'int')]),
    FORM('referral_source_sheet', 'Referral Source Sheet', 'Enquiry source with conversion and gift', 'source_conv.source', F(
        ('Source', 'source_conv.source'), ('Enquiries, 12 months', 'source_conv.enquiries'), ('Conversion', 'source_conv.conversion')) + [
        FF('Contracts, 12 months', 'COUNTIFS({range:enquiries.source},{pick},{range:enquiries.status},%s,{range:enquiries.date},%s)' % (SIGNED, Y12), 'int'),
        FF('Share of all enquiries', 'IFERROR(INDEX({range:source_conv.enquiries},MATCH({pick},{range:source_conv.source},0))/SUM({range:source_conv.enquiries}),0)', 'pct'),
        FF('Thank-you gift value', 'IFERROR(INDEX({range:sources.gift_value},MATCH({pick},{range:sources.source},0)),0)', 'money'),
        FF('Kind of source', 'IFERROR(INDEX({range:sources.kind},MATCH({pick},{range:sources.source},0))&"","")', 'text')]),
    FORM('lost_sheet', 'Lost Enquiry Sheet', 'Lost enquiries by reason and the value lost', 'lost_reasons.reason', F(
        ('Reason', 'lost_reasons.reason'), ('Lost enquiries, 12 months', 'lost_reasons.lost_enquiries'), ('Quote value lost', 'lost_reasons.quote_value_lost')) + [
        FF('Share of all lost enquiries', 'IFERROR(INDEX({range:lost_reasons.lost_enquiries},MATCH({pick},{range:lost_reasons.reason},0))/SUM({range:lost_reasons.lost_enquiries}),0)', 'pct'),
        FF('Lost in the last 90 days', 'COUNTIFS({range:enquiries.reason},{pick},{range:enquiries.status},%s,{range:enquiries.date},">="&({today}-90))' % LOST, 'int'),
        FF('Declined share you accept', '{set:declined_max}', 'pct')]),
    FORM('date_request_sheet', 'Date Request and Waitlist Sheet', 'Due month with load against your limit', 'demand.due_month', F(
        ('Due month', 'demand.due_month'), ('Enquiries wanting it', 'demand.enquiries_wanting'), ('Clients booked', 'demand.clients_booked'), ('Open quotes', 'demand.open_quotes'), ('Load', 'demand.load'),
        ('Spaces left', 'demand.spaces'), ('Date check', 'demand.cap_flag')) + [FF('Most due dates you take in a month', '{set:agency_cap_month}', 'int'), FF('Months above the limit, next 18', 'COUNTIFS({range:demand.cap_flag},%s)' % c2('Waitlist these dates'), 'int')]),
    FORM('discount_sheet', 'Discount Approval Sheet', 'Discount on a quote against your limit', 'quotes.quote_id', F(
        ('Name', 'quotes.name'), ('Package', 'quotes.package'), ('List price', 'quotes.list_price'), ('Discount', 'quotes.discount'), ('Discount amount', 'quotes.discount_amount'), ('Quote total', 'quotes.quote_total')) + [
        FF('Discount as a share of the list price', 'IFERROR(%s/%s,0)' % (LK('quotes', 'quote_id', 'discount_amount'), LK('quotes', 'quote_id', 'list_price')), 'pct'),
        FF('Community rate set at', '{set:community_discount}', 'pct'), FF('Returning client discount set at', '{set:returning_discount}', 'pct'),
        FF('Price given up, signed quotes, 12 months', 'SUMIFS({range:quotes.discount_amount},{range:quotes.status},%s,{range:quotes.quote_date},">="&EDATE(%s,-12))' % (Q_SIGNED, MS), 'money')]),
    FORM('reply_log_sheet', 'Reply Log Sheet', 'First reply time against your target', 'enquiries.enquiry_id', F(
        ('Date', 'enquiries.date'), ('Weekday', 'enquiries.weekday'), ('Name', 'enquiries.name'), ('Hours to the first reply', 'enquiries.first_reply_hours'), ('Reply check', 'enquiries.reply_flag'), ('Reply time band', 'enquiries.reply_band')) + [
        FF('Share signed in this reply band', 'IFERROR(INDEX({range:reply_bands.signed_share},MATCH(%s,{range:reply_bands.band},0)),0)' % LK('enquiries', 'enquiry_id', 'reply_band'), 'pct'),
        FF('Average reply hours on this weekday', 'IFERROR(AVERAGEIFS({range:enquiries.first_reply_hours},{range:enquiries.weekday},%s,{range:enquiries.date},%s),0)' % (LK('enquiries', 'enquiry_id', 'weekday'), Y12), 'num'),
        FF('Reply target, hours', '{set:reply_hours_target}', 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('quote_letter', 'Quote Letter', 'Quote letter with price, deposit and dates', 'quotes.quote_id', [
        'Quote of {set:company}, dated {today}. Dear {col:quotes.name}, thank you for talking with us about {col:quotes.package}.',
        'Your quote total is {col:quotes.quote_total}, before any tax. It is made of the list price {col:quotes.list_price}, a discount of {col:quotes.discount_amount}, add-ons of {col:quotes.addons} and a travel fee of {col:quotes.travel_fee}.',
        'The deposit of {col:quotes.deposit} reserves your date and is applied to the price. The balance of {col:quotes.balance}, the rest of the price after the deposit, is due on {col:quotes.balance_due}, or in {col:quotes.instalments} instalments of {col:quotes.instalment}, the last on {col:quotes.last_inst}.',
        'This quote is valid until {col:quotes.valid_until}. After that date, please ask us to confirm the dates and the price again.'], ['Owner-doula', 'Client'], NOTE),
    DOC('consult_confirm', 'Consultation Confirmation', 'Consultation confirmation for an enquirer', 'consults.consult_id', [
        'Confirmation of {set:company}, dated {today}. Dear {col:consults.name}, your consultation is on {col:consults.date} with {col:consults.doula}.',
        'A consultation is a conversation of 30 to 60 minutes. We listen to what you need, explain the packages and the on-call window, the days around the estimated due date when the doula keeps themselves free, and answer your questions about the price.',
        'If you cannot come, please tell us at least a day ahead so that we can offer the time to another client.'], ['Doula', 'Enquirer'], NOTE),
    DOC('consult_followup', 'Consultation Follow-up Letter', 'Follow-up letter after a consultation', 'consults.consult_id', [
        'Letter of {set:company}, dated {today}. Dear {col:consults.name}, thank you for talking with {col:consults.doula} on {col:consults.date}.',
        'If you would like to go ahead, the next steps are the quote, the contract and the deposit that reserves your date. We hold your due date until {col:consults.follow_up_on} unless you tell us you need longer.',
        'Questions are welcome at any time. Please call {col:consults.owner_phone}.', 'We hope to support you.'], ['Owner-doula', 'Enquirer'], NOTE),
    DOC('package_compare', 'Package Comparison Letter', 'Package comparison for a client', 'packages.package_id', [
        'Package comparison of {set:company}, dated {today}. {col:packages.package} is a {col:packages.kind} package.',
        'Price: {col:packages.price}, before any tax. It plans {col:packages.prenatal_visits} prenatal visits, {col:packages.birth_hours} hours attended at the birth and {col:packages.postpartum_hours} postpartum hours, the weeks after a birth.',
        'All planned hours: {col:packages.plan_hours}. Price per planned hour: {col:packages.income_hour}. The deposit share is {col:packages.deposit_pct} of the price.',
        'Ask us to compare this package with another one. Please check the current price list before you decide.'], ['Owner-doula', 'Client'], NOTE),
    DOC('price_list', 'Package and Price List', 'Package and price list entry', 'packages.package_id', [
        'Price list entry of {set:company}, dated {today}.', '{col:packages.package}, {col:packages.kind}: price {col:packages.price}. Deposit share {col:packages.deposit_pct}. Planned hours {col:packages.plan_hours}.',
        'Prices are before any tax and can change. Please check the current list. A community rate, a lower price for a client who cannot pay the full price, is available on request.'], ['Owner-doula'], NOTE),
    DOC('instalment_sheet', 'Instalment Schedule Sheet', 'Instalment schedule for a quote', 'quotes.quote_id', [
        'Instalment schedule of {set:company}, dated {today}. Client: {col:quotes.name}. Package: {col:quotes.package}.',
        'Quote total {col:quotes.quote_total}. Deposit {col:quotes.deposit}. Balance {col:quotes.balance}.',
        'The balance is paid in {col:quotes.instalments} instalments of {col:quotes.instalment}, {set:instalment_days} days apart. The first is due on {col:quotes.first_inst} and the last on {col:quotes.last_inst}, before the on-call window opens.',
        'Please pay each instalment by its date. Tell us early if a date does not suit you.'], ['Owner-doula', 'Client'], NOTE),
    DOC('welcome_letter', 'Welcome Letter', 'Welcome and next-steps letter for a new client', 'clients.client_id', [
        'Welcome letter of {set:company}, dated {today}. Dear {col:clients.client}, welcome and thank you for choosing us.',
        'Your package is {col:clients.package} and your doula is {col:clients.doula}. Your estimated due date is {col:clients.edd}, a date you gave us, used only to plan the on-call window.',
        'The next steps are the signed contract, the deposit, a first visit with your doula and the dates of your payments. We will write to you about each one.', 'Please call us at any time with a question.'], ['Owner-doula', 'Client'], NOTE),
    DOC('full_letter', 'We Are Full Letter', 'Waitlist letter when your dates are full', 'enquiries.enquiry_id', [
        'Letter of {set:company}, dated {today}. Dear {col:enquiries.name}, thank you for asking about {col:enquiries.edd_wanted}.',
        'We are full around that date and cannot promise a doula. We can put you on the waitlist and write at once if a date opens, or suggest another doula or a later date.',
        'Please tell us which you prefer. We are sorry that we cannot say yes now.'], ['Owner-doula', 'Enquirer'], NOTE),
    DOC('community_letter', 'Community Rate Response', 'Community-rate response letter', 'quotes.quote_id', [
        'Letter of {set:company}, dated {today}. Dear {col:quotes.name}, thank you for asking about the community rate, a lower price for a client who cannot pay the full price.',
        'For {col:quotes.package} the list price is {col:quotes.list_price}. With the community rate the discount is {col:quotes.discount_amount} and your quote total is {col:quotes.quote_total}.',
        'The deposit is {col:quotes.deposit}. The quote is valid until {col:quotes.valid_until}. Please tell us if you would like to go ahead.'], ['Owner-doula', 'Client'], NOTE),
    DOC('referral_letter', 'Referral Note Letter', 'Thank-you note to a referral source', 'source_conv.source', [
        'Note of {set:company}, dated {today}. Dear friend, thank you for sending people to us.',
        'In the last 12 months we had {col:source_conv.enquiries} enquiries from {col:source_conv.source}, and {col:source_conv.conversion} of them became contracts.',
        'We answer every referral quickly and keep you informed in general terms only. Thank you for your trust.'], ['Owner-doula'], NOTE),
    DOC('hold_letter', 'Date-Hold Confirmation', 'Date-hold confirmation for an enquirer', 'enquiries.enquiry_id', [
        'Confirmation of {set:company}, dated {today}. Dear {col:enquiries.name}, we are holding the due date around {col:enquiries.edd_wanted} for you.',
        'We hold it until {col:enquiries.hold_until}. A signed contract and the deposit make the hold final. After that date we may offer it to another client.',
        'Please tell us if you need more time.'], ['Owner-doula', 'Enquirer'], NOTE),
    DOC('weekly_summary', 'Weekly Enquiry Summary', 'Enquiry summary for the owner-doula', 'funnel.month', [
        'Summary of {set:company}, dated {today}, for the month {col:funnel.month}.',
        'Enquiries: {col:funnel.enquiries}. Consultations booked: {col:funnel.consult_booked}, held: {col:funnel.consult_held}, no-shows: {col:funnel.noshows}. Contracts signed: {col:funnel.signed}. Lost: {col:funnel.lost}. Still open: {col:funnel.open}.',
        'Conversion: {col:funnel.conversion}. Show rate: {col:funnel.show_rate}.',
        'Your own rates over the 6 months before: booked per enquiry {col:funnel.own_book}, held per booked {col:funnel.own_held}, signed per held {col:funnel.own_sign}.'], ['Owner-doula'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('new_enquiry', 'New Enquiry Steps', 'enquiries', 'enquiries.date', [('Write the enquiry in the Enquiries sheet', 0), ('Reply within the target hours', 0), ('Offer two consultation times', 1), ('Send the package and price list', 1), ('Check the due date against your monthly limit', 1), ('Follow up if there is no answer', 3), ('Close the enquiry if nothing comes back', 30)]),
    CHK('consult_day', 'Consultation Day Steps', 'consults', 'consults.date', [('Confirm the consultation the day before', -1), ('Open the enquiry and the package list', 0), ('Hold the consultation and note the minutes', 0), ('Record the outcome', 0), ('Send the next steps the same day', 0), ('Set the follow-up date', 0), ('Offer another time after a no-show', 1)]),
    CHK('after_consult', 'After the Consultation Steps', 'consults', 'consults.date', [('Send the thank-you message', 0), ('Send the quote', 1), ('Offer instalments if the price is high', 1), ('Call if there is no answer', 5), ('Write again', 10), ('Close the enquiry or hold the date', 30)]),
    CHK('send_quote', 'Sending a Quote Steps', 'quotes', 'quotes.quote_date', [('Check the package and the add-ons', 0), ('Check the travel fee and the discount', 0), ('Check the income per hour against your target', 0), ('Send the quote with the valid-until date', 0), ('Record the quote in the Quotes sheet', 0), ('Set the follow-up date', 5)]),
    CHK('quote_followup', 'Quote Follow-up Steps', 'quotes', 'quotes.quote_date', [('Send a gentle reminder', 5), ('Call the enquirer', 8), ('Send the quote-ends reminder', 11), ('Let the quote lapse or extend it', 14), ('Record why it was lost', 15)]),
    CHK('decline_date', 'Declining a Date Steps', 'enquiries', 'enquiries.date', [('Check the load of the due month', 0), ('Check the backup cover', 0), ('Offer the waitlist', 1), ('Offer another doula or a later date', 1), ('Record the lost reason', 2), ('Write to the enquirer if a date opens', 30)]),
    CHK('discount_review', 'Discount Review Steps', 'quotes', 'quotes.quote_date', [('Check the request against your limit', 0), ('Check the discount share of the last 12 months', 1), ('Decide and note it', 1), ('Send the response letter', 2), ('Record the discount on the quote', 2), ('Review the discounts next month', 30)]),
    CHK('weekly_meeting', 'Weekly Enquiry Meeting Steps', 'consult_cal', 'consult_cal.date', [('Count the enquiries waiting for a first reply', 0), ('Check the consultations booked for the week', 0), ('Check the open quotes ending this week', 0), ('Check the due months against the limit', 0), ('Assign the calls', 0), ('Write the actions in the notes', 0)]),
    CHK('monthly_lost', 'Monthly Lost Review Steps', 'lost_month', 'lost_month.month', [('List the lost enquiries of the month', 1), ('Group them by reason', 2), ('Check the declined share against your setting', 3), ('Look at the quote value lost', 4), ('Pick one cause to fix', 5), ('Write the actions', 7)]),
    CHK('prep_consult', 'Preparing a Consultation Steps', 'consults', 'consults.date', [('Read the enquiry', -1), ('Check the free dates around the due date', -1), ('Prepare the package list and the price', -1), ('Check the doula and the backup cover', -1), ('Prepare the quote in the Quote Builder', 0)]),
    CHK('out_of_hours', 'Out-of-Hours Reply Rota Steps', 'consult_cal', 'consult_cal.date', [('Decide who covers the evening', -7), ('Decide who covers the weekend', -7), ('Check the reply target', -7), ('Write the cover rota', -3), ('Share the rota with the team', -2), ('Review the reply times', 7)]),
    CHK('yearly_price', 'Yearly Price Check Steps', 'funnel', 'funnel.month', [('Print the income per hour of each package', 1), ('Check the packages below your target', 3), ('Check your own local range for each package', 5), ('Decide raise, hold or lower', 10), ('Update the Packages sheet', 12), ('Tell the team and the enquirers', 14), ('Check again after 3 months', 90)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
EP = 'enquiries.phone'
messages = [
    M('e_thanks', 'Enquirer: thank you for contacting us', 'enquiries', EP, 'Hello {name}, thank you for contacting {company}. We will reply within {reply_hours} hours. Please tell us the date you have in mind.'),
    M('e_choose', 'Enquirer: choose a consultation time', 'enquiries', EP, 'Hello {name}, we would be glad to talk with you. A consultation takes 30 to 60 minutes. Please reply with a day and time that suit you. {company}'),
    M('e_consult', 'Enquirer: your consultation is booked', 'enquiries', EP, 'Hello {name}, your consultation with {company} is on {consult_date}. Reply if you need to change it.'),
    M('e_remind', 'Enquirer: consultation tomorrow', 'enquiries', EP, 'Hello {name}, a reminder: your consultation with {company} is tomorrow, {consult_date}. We look forward to talking with you.'),
    M('e_missed', 'Enquirer: we missed you', 'enquiries', EP, 'Hello {name}, we missed you at your consultation on {consult_date}. Would you like another time? Reply with a day that suits you. {company}'),
    M('e_next', 'Enquirer: next steps after talking', 'enquiries', EP, 'Hello {name}, thank you for talking with us on {consult_date}. The next steps are the quote, the contract and the deposit. Reply when you are ready. {company}'),
    M('q_quote', 'Enquirer: your quote', 'quotes', 'quotes.phone', 'Hello {name}, your quote for {package} is {quote_total}, valid until {valid_until}. Reply to accept or to ask a question. {company}'),
    M('q_gentle', 'Enquirer: a gentle quote reminder', 'quotes', 'quotes.phone', 'Hello {name}, a gentle reminder about your quote of {quote_total} for {package}. It stays valid until {valid_until}. {company}'),
    M('q_ends', 'Enquirer: your quote is ending', 'quotes', 'quotes.phone', 'Hello {name}, your quote of {quote_total} ends on {valid_until}, in {days_left} days. Reply if you would like us to keep it open. {company}'),
    M('q_inst', 'Enquirer: instalments offered', 'quotes', 'quotes.phone', 'Hello {name}, you can pay the balance of {balance} in {instalments} instalments of {instalment}, the last on {last_inst}. The deposit is {deposit}. {company}'),
    M('e_hold', 'Enquirer: we hold your due date', 'enquiries', EP, 'Hello {name}, we hold your due date around {edd_wanted} until {hold_until}. Have you decided? {company}'),
    M('e_full', 'Enquirer: we are full, join the waitlist', 'enquiries', EP, 'Hello {name}, we are full around {edd_wanted}. May we put you on the waitlist and write if a date opens? {company}'),
    M('e_opened', 'Enquirer: a date has opened', 'enquiries', EP, 'Hello {name}, a date has opened around {edd_wanted}. Would you like us to hold it for you? {company}'),
    M('e_list', 'Enquirer: package and price list', 'enquiries', EP, 'Hello {name}, {company} offers birth packages, postpartum hour packs and combined packages. Reply and we will send the current package and price list.'),
    M('e_addons', 'Enquirer: add-ons and what they cost', 'enquiries', EP, 'Hello {name}, {company} offers add-ons such as an extra prenatal visit, a class seat or a debrief visit. Reply for the current prices.'),
    M('e_hours', 'Enquirer: postpartum hour packs', 'enquiries', EP, 'Hello {name}, a postpartum hour pack at {company} is a set number of hours bought together, with a minimum booking. Reply for the packs and the rates.'),
    M('e_community', 'Enquirer: community rate information', 'enquiries', EP, 'Hello {name}, {company} has a community rate, a lower price for a client who cannot pay the full price. Reply and we will explain how it works.'),
    M('e_contract', 'Enquirer: your contract is ready', 'enquiries', EP, 'Hello {name}, your contract with {company} is ready to sign. Please tell us when you can sign and pay the deposit that reserves your date.'),
    M('e_signed', 'Enquirer: signed contract received', 'enquiries', EP, 'Hello {name}, we received your signed contract. Thank you for choosing {company}. We will write soon with your next steps.'),
    M('e_why', 'Enquirer: why another doula?', 'enquiries', EP, 'Hello {name}, thank you for considering {company}. If you chose another doula, may we ask what made the difference? It helps us improve.'),
    M('e_close', 'Enquirer: shall we close your enquiry', 'enquiries', EP, 'Hello {name}, we have not heard from you since {date}. Shall we close your enquiry with {company}? Reply if you still need us.'),
    M('e_class', 'Enquirer: class or workshop invitation', 'enquiries', EP, 'Hello {name}, you are invited to our next class or workshop at {company}. Reply and we will send the date and how to book a seat.'),
    M('c_welcome', 'Client: welcome and next steps', 'clients', 'clients.phone', 'Hello {client}, welcome to {company}. Your doula is {doula} and your package is {package}. We will send your next steps this week.'),
    M('c_thanks', 'Client: thank you for the referral', 'clients', 'clients.phone', 'Hello {client}, thank you for recommending {company}. It means a lot to us and to {doula}.'),
    M('ow_noreply', 'Owner: enquiry waiting for a first reply', 'enquiries', 'enquiries.owner_phone', 'Hello, {name} wrote on {date} and has no first reply yet. Please call {phone}. Reply check: {reply_flag}.'),
    M('ow_outcome', 'Owner: consultation with no outcome', 'consults', 'consults.owner_phone', 'Hello, the consultation with {name} on {date} needs an outcome. Doula: {doula}. Check: {follow_flag}.'),
    M('ow_quotes', 'Owner: quote ending this week', 'quotes', 'quotes.owner_phone', 'Hello, the quote for {name} of {quote_total} ends on {valid_until}. Check: {expiry_flag}. Please chase it or let it lapse.'),
    M('ow_demand', 'Owner: due month above your limit', 'demand', 'demand.owner_phone', 'Hello, {due_month} has {clients_booked} clients booked and {open_quotes} open quotes, a load of {load}. Check: {cap_flag}.'),
    M('ow_declined', 'Owner: the declined share', 'lost_month', 'lost_month.owner_phone', 'Hello, in {month} the declined share was {declined_share} with {lost_enquiries} lost enquiries. Please review the dates and the backup cover.'),
    M('ow_community', 'Owner: a community-rate request', 'quotes', 'quotes.owner_phone', 'Hello, a community-rate request for {name}: {package}, list price {list_price}, discount {discount_amount}. Please decide before {valid_until}.'),
    M('ad_cal', 'Admin: consultation list for the week', 'consult_cal', 'consult_cal.admin_phone', 'Hello, on {date} ({weekday}) {booked} consultations are booked and {free_slots} slots are free. Doula on duty: {doula}. {company}'),
    M('ad_quotes', 'Admin: quote to follow up today', 'quotes', 'quotes.admin_phone', 'Hello, please follow up the quote for {name}: {package}, {quote_total}, valid until {valid_until}. Phone {phone}.'),
    M('dl_consult', 'Doula: you have a consultation', 'consults', 'consults.doula_phone', 'Hello, you have a consultation with {name} on {date}. Please be ready to explain the packages and the price. {company}'),
    M('cp_thanks', 'Care-provider office: thank you', 'team', 'team.phone', 'Hello {name}, thank you for the clients you send to {company}. We reply to every enquiry within a day. {company}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30), dashboard, insights
D30 = '{range:enquiries.date},">="&({today}-30),{range:enquiries.date},"<="&{today}'
D90 = '{range:enquiries.date},">="&({today}-90),{range:enquiries.date},"<="&{today}'
C90 = '{range:consults.date},">="&({today}-90),{range:consults.date},"<="&{today}'
SRC = lambda *names: '+'.join('COUNTIFS({range:enquiries.source},%s,{range:enquiries.date},%s)' % (tok('source', n), Y12) for n in names)
EXPB = '(%s*%s*%s*%s+%s*%s*%s+%s*%s+%s*%s)' % (NN, R1_, R2_, R3_, NB, R2_, R3_, NH, R3_, NS, PS)
kpis = [
    KPI('Enquiries this month', 'COUNTIFS({range:enquiries.month},%s)' % MS, 'int'),
    KPI('Enquiries, last 30 days', 'COUNTIFS(%s)' % D30, 'int'),
    KPI('Enquiries waiting for a first reply', 'COUNTIFS({range:enquiries.reply_flag},%s)' % ca('No reply yet'), 'int'),
    KPI('Hours to a first reply, 90-day average', 'IFERROR(AVERAGEIFS({range:enquiries.first_reply_hours},%s),0)' % D90, 'num'),
    KPI('Replies within the target hours, 90 days', 'IFERROR(COUNTIFS(%s,{range:enquiries.reply_flag},%s)/(COUNTIFS(%s,{range:enquiries.reply_flag},%s)+COUNTIFS(%s,{range:enquiries.reply_flag},%s)),0)' % (D90, ca('Reply in time'), D90, ca('Reply in time'), D90, ca('Slow reply')), 'pct'),
    KPI('Consultations booked, next 7 days', 'COUNTIFS({range:consults.date},">="&{today},{range:consults.date},"<="&({today}+6),{range:consults.outcome},%s)' % O_BOOKED, 'int'),
    KPI('Consultations held this month', 'COUNTIFS({range:consults.date},">="&%s,{range:consults.date},"<="&{today},{range:consults.held},1)' % MS, 'int'),
    KPI('Consultation no-show rate, 90 days', 'IFERROR(COUNTIFS(%s,{range:consults.outcome},%s)/COUNTIFS(%s,{range:consults.outcome},"<>"&%s),0)' % (C90, O_NOSHOW, C90, O_BOOKED), 'pct'),
    KPI('Quotes sent this month', 'COUNTIFS({range:quotes.quote_date},">="&%s,{range:quotes.quote_date},"<="&{today})' % MS, 'int'),
    KPI('Quotes open', 'COUNTIFS({range:quotes.status},%s)' % Q_OPEN, 'int'),
    KPI('Value of open quotes', 'SUMIFS({range:quotes.quote_total},{range:quotes.status},%s)' % Q_OPEN, 'money'),
    KPI('Quotes ending in 7 days', 'COUNTIFS({range:quotes.expiry_flag},%s)' % ca('Ends within 7 days'), 'int'),
    KPI('Contracts signed this month', 'COUNTIFS({range:clients.signed_on},">="&%s,{range:clients.signed_on},"<="&{today})' % MS, 'int'),
    KPI('Enquiry to contract conversion, 90 days', 'IFERROR(COUNTIFS({range:enquiries.signed_on},">="&({today}-90),{range:enquiries.signed_on},"<="&{today})/COUNTIFS(%s),0)' % D90, 'pct'),
    KPI('Consultation to contract rate, 90 days', 'IFERROR(COUNTIFS(%s,{range:consults.outcome},%s)/COUNTIFS(%s,{range:consults.held},1),0)' % (C90, O_SIGNED, C90), 'pct'),
    KPI('Days from enquiry to signing, 90 days', 'IFERROR(AVERAGEIFS({range:enquiries.days_to_sign},{range:enquiries.signed_on},">="&({today}-90)),0)', 'num'),
    KPI('Average quote total, 90 days', 'IFERROR(AVERAGEIFS({range:quotes.quote_total},{range:quotes.quote_date},">="&({today}-90)),0)', 'money'),
    KPI('Lost enquiries, 90 days', 'COUNTIFS(%s,{range:enquiries.status},%s)' % (D90, LOST), 'int'),
    KPI('Declined share of enquiries, 90 days', 'IFERROR(SUMIFS({range:enquiries.declined},%s)/COUNTIFS(%s),0)' % (D90, D90), 'pct'),
    KPI('Lost to price, share, 90 days', 'IFERROR(COUNTIFS(%s,{range:enquiries.status},%s,{range:enquiries.reason},%s)/COUNTIFS(%s,{range:enquiries.status},%s),0)' % (D90, LOST, tok('lostreason', 'Price'), D90, LOST), 'pct'),
    KPI('Lost to date full, share, 90 days', 'IFERROR(COUNTIFS(%s,{range:enquiries.status},%s,{range:enquiries.reason},%s)/COUNTIFS(%s,{range:enquiries.status},%s),0)' % (D90, LOST, tok('lostreason', 'Date full'), D90, LOST), 'pct'),
    KPI('Lost to no reply, share, 90 days', 'IFERROR(COUNTIFS(%s,{range:enquiries.status},%s,{range:enquiries.reason},%s)/COUNTIFS(%s,{range:enquiries.status},%s),0)' % (D90, LOST, tok('lostreason', 'No reply'), D90, LOST), 'pct'),
    KPI('Best source by conversion', 'IFERROR(INDEX({range:source_conv.source},MATCH(MAX({range:source_conv.conversion}),{range:source_conv.conversion},0)),"")', 'text'),
    KPI('Referral share of enquiries, 12 months', 'IFERROR((%s)/COUNTIFS({range:enquiries.date},%s),0)' % (SRC('Care provider', 'Past client', 'Support professional', 'Class or workshop'), Y12), 'pct'),
    KPI('Online share of enquiries, 12 months', 'IFERROR((%s)/COUNTIFS({range:enquiries.date},%s),0)' % (SRC('Online search', 'Social media', 'Directory listing'), Y12), 'pct'),
    KPI('Signed quotes on instalments, 12 months', 'IFERROR(COUNTIFS({range:quotes.instalments},">1",{range:quotes.status},%s,{range:quotes.quote_date},">="&EDATE(%s,-12))/COUNTIFS({range:quotes.status},%s,{range:quotes.quote_date},">="&EDATE(%s,-12)),0)' % (Q_SIGNED, MS, Q_SIGNED, MS), 'pct'),
    KPI('Discount given, 12 months', 'SUMIFS({range:quotes.discount_amount},{range:quotes.status},%s,{range:quotes.quote_date},">="&EDATE(%s,-12))' % (Q_SIGNED, MS), 'money'),
    KPI('Due months above your limit, next 18', 'COUNTIFS({range:demand.cap_flag},%s)' % c2('Waitlist these dates'), 'int'),
    KPI('Expected contracts, next 30 days', EXPB, 'num'),
    KPI('Longest wait for a first reply, days', 'SUMPRODUCT(MAX(({range:enquiries.reply_flag}=%s)*({today}-{range:enquiries.date})))' % ca('No reply yet'), 'int'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Enquiry Dashboard", "kpis": kpis,
    "monthly": {"title": "Enquiries, consultations held, contracts signed and lost", "date": "funnel.month", "series": [
        {"label": "Enquiries", "sum": "funnel.enquiries", "date": "funnel.month"}, {"label": "Consultations held", "sum": "funnel.consult_held", "date": "funnel.month"},
        {"label": "Contracts signed", "sum": "funnel.signed", "date": "funnel.month"}, {"label": "Lost", "sum": "funnel.lost", "date": "funnel.month"}]},
    "breakdowns": [{"title": "Enquiries by source", "by": "enquiries.source", "value": "enquiries.quote", "agg": "count"}, {"title": "Quote value lost by reason", "by": "lost_reasons.reason", "value": "lost_reasons.quote_value_lost", "agg": "sum"},
                   {"title": "Consultations by outcome", "by": "consults.outcome", "value": "consults.minutes", "agg": "count"}, {"title": "Quote value by package", "by": "quotes.package", "value": "quotes.quote_total", "agg": "sum"}]}
insights = {"filters": [{"label": "Service", "list": "service"}, {"label": "Enquiry source", "list": "source"}, {"label": "Area", "list": "area"}],
    "gauges": [
        {"title": "Replies within the target hours", "num": AGG('count', 'enquiries', where=[('reply_flag', '=', ca('Reply in time'))]), "den": AGG('count', 'enquiries', where=[('reply_flag', '<>', ca('No reply yet'))])},
        {"title": "Consultations held as booked", "num": AGG('sum', 'consults', 'consults.held'), "den": AGG('count', 'consults', where=[('outcome', '<>', O_BOOKED)])},
        {"title": "Consultations that became contracts", "num": AGG('count', 'consults', where=[('outcome', '=', O_SIGNED)]), "den": AGG('sum', 'consults', 'consults.held')},
        {"title": "Quotes that were signed", "num": AGG('count', 'quotes', where=[('status', '=', Q_SIGNED)]), "den": AGG('count', 'quotes', where=[('status', '<>', Q_OPEN)])},
        {"title": "Declined share of enquiries", "num": AGG('sum', 'enquiries', 'enquiries.declined'), "den": AGG('count', 'enquiries')},
        {"title": "Enquiries replied within a working day", "num": AGG('sum', 'enquiries', 'enquiries.fast_reply'), "den": AGG('count', 'enquiries', where=[('reply_flag', '<>', ca('No reply yet'))])}],
    "charts": [
        CHART('Enquiries per month', 'column', 'month', [AGG('count', 'enquiries', date='enquiries.date', label='Enquiries')]),
        CHART('Enquiries by source', 'bar', 'enquiries.source', [AGG('count', 'enquiries', label='Enquiries')]),
        CHART('Enquiries by service', 'bar', 'enquiries.service', [AGG('count', 'enquiries', label='Enquiries')]),
        CHART('Enquiries by area', 'bar', 'enquiries.area', [AGG('count', 'enquiries', label='Enquiries')]),
        CHART('Enquiries by status', 'bar', 'enquiries.status', [AGG('count', 'enquiries', label='Enquiries')]),
        CHART('Lost enquiries by reason', 'bar', 'lost_reasons.reason', [AGG('sum', 'lost_reasons', 'lost_reasons.lost_enquiries', label='Lost enquiries')]),
        CHART('Contracts signed per month', 'column', 'month', [AGG('sum', 'funnel', 'funnel.signed', date='funnel.month', label='Contracts signed')]),
        CHART('Consultations per month', 'column', 'month', [AGG('count', 'consults', date='consults.date', label='Consultations')]),
        CHART('Consultations by outcome', 'bar', 'consults.outcome', [AGG('count', 'consults', label='Consultations')]),
        CHART('Consultations by doula', 'bar', 'consults.doula', [AGG('count', 'consults', label='Consultations')]),
        CHART('Quote value lost per month', 'column', 'month', [AGG('sum', 'lost_month', 'lost_month.quote_value_lost', date='lost_month.month', label='Quote value lost')]),
        CHART('Average hours to a first reply per month', 'column', 'month', [AGG('avg', 'enquiries', 'enquiries.first_reply_hours', date='enquiries.date', label='Hours to a first reply')]),
        CHART('Conversion per month', 'column', 'month', [AGG('avg', 'funnel', 'funnel.conversion', date='funnel.month', label='Conversion')]),
        CHART('Enquiries by due month wanted', 'column', 'month', [AGG('sum', 'demand', 'demand.enquiries_wanting', date='demand.due_month', label='Enquiries wanting the month')]),
        CHART('Quotes by package quoted', 'bar', 'quotes.package', [AGG('count', 'quotes', label='Quotes')]),
        CHART('Signed quotes by package', 'bar', 'quotes.package', [AGG('count', 'quotes', where=[('status', '=', Q_SIGNED)], label='Signed quotes')]),
        CHART('Contracts signed by source', 'bar', 'enquiries.source', [AGG('count', 'enquiries', where=[('status', '=', SIGNED)], label='Contracts signed')]),
        CHART('Lost enquiries by source', 'bar', 'enquiries.source', [AGG('count', 'enquiries', where=[('status', '=', LOST)], label='Lost enquiries')]),
        CHART('Consultation minutes per month', 'column', 'month', [AGG('avg', 'consults', 'consults.minutes', date='consults.date', label='Minutes')]),
        CHART('Declined share per month', 'column', 'month', [AGG('avg', 'lost_month', 'lost_month.declined_share', date='lost_month.month', label='Declined share')]),
        CHART('Instalment plans per month', 'column', 'month', [AGG('count', 'quotes', date='quotes.quote_date', where=[('instalments', '>', 1)], label='Quotes with instalments')]),
        CHART('Discount given per month', 'column', 'month', [AGG('sum', 'quotes', 'quotes.discount_amount', date='quotes.quote_date', label='Discount given')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Quote builder with income per hour", "why": "a package, extra hours, add-ons, travel and a discount on one page, with the deposit, balance and instalment dates and your income per hour", "where": "Quote Builder"},
    {"name": "Conversion funnel check", "why": "enquiry, consultation held and contract signed, each step set against your own last 6 months, with the leakiest step named", "where": "Conversion Funnel Check"},
    {"name": "Lost-enquiry cause analyser", "why": "price, date full, no backup, another doula and no reply side by side with the quote value lost and the declined share against your setting", "where": "Lost-Enquiry Cause Analyser"},
    {"name": "Due-month demand map", "why": "enquiries wanting each due month against clients booked and open quotes, with the months above your monthly limit named before you say yes", "where": "Due-Month Demand Map"},
    {"name": "Enquiry pipeline forecast", "why": "open enquiries multiplied by your own step rates give the expected contracts in 30 days, with Base, Best and Worst scenarios", "where": "Enquiry Pipeline Forecast"},
    {"name": "Reply-time impact", "why": "the share that booked and signed after a fast and a slow first reply, with the contracts a faster reply would add each month", "where": "Reply-Time Impact"},
    {"name": "Price-lost break-even", "why": "how many price-lost enquiries a discount must win back to pay for itself, worked out in closed form from your own history", "where": "Price-Lost Break-Even"},
    {"name": "Quote expiry tracker", "why": "quotes ending this week with the value at risk, so the quotes that matter are chased before they lapse", "where": "Quote Expiry Tracker"},
    {"name": "Consultation follow-up scheduler", "why": "days since the consultation and the outcome turned into call today, write today, close or wait", "where": "Consult Follow-Up Scheduler"},
    {"name": "Reply coverage by weekday", "why": "your average hours to a first reply on each weekday, so the day that needs cover is named", "where": "Reply Coverage by Weekday"}]
competitors = [
    {"what": "free client-tracker templates", "lacks": "list names and dates but never time the first reply, build a quote with a deposit and instalments or show which enquiry source signs"},
    {"what": "subscription practice-management software", "lacks": "charge a monthly fee per user for an intake module that cannot test your own discount, your own limit on due dates a month or your own income-per-hour target"},
    {"what": "single-sheet on-call calendars", "lacks": "show who is free around a date but not the enquiries wanting that month, the open quotes or when to waitlist"},
    {"what": "generic invoice spreadsheets", "lacks": "total a price but know nothing about packages, on-call windows, travel at a mileage rate or the balance date before the due date"},
    {"what": "forms and handouts bundles", "lacks": "give you printable pages but no calculations, no follow-up dates and no lost-enquiry analysis"}]
guide = [
    'Open Start and type your company name and your own limits in the yellow cells: the target hours to a first reply, the days a quote stays valid, the most due dates you take in a month and the income per hour you want from a package.',
    'Check Packages, Pay rates, Areas, Sources and Team. They hold the prices, the hours, the mileage rates and the phones that the other sheets look up. A solo doula keeps one doula and no backup.',
    'Write every enquiry in Enquiries: date, name, phone, area, service, the due date wanted (a date the enquirer gives, used only to plan the on-call window: the days around it when a doula keeps themselves free), source and first reply.',
    'Book each consultation in Consultations and check the Consultation Calendar for free slots. Record the minutes, the outcome and the follow-up date.',
    'Build each quote in the Quote Builder, then write it in Quotes. A deposit is a payment that reserves the date and is applied to the price; the balance is the rest of the price after the deposit.',
    'Read the Follow-up List every morning: it tells you who to call, write to, remind or welcome today.',
    'Use Demand by Due Month before you say yes to a date: it shows the clients booked and the open quotes against the most due dates you take in a month.',
    'Read Funnel by Month, Source Conversion, Reply Time Bands and Lost Reasons each month to see where enquiries drop out and which sources sign.',
    f'Use the {len(tools)} tools to build a quote, check the funnel, rank the lost-enquiry causes, test a discount, forecast the next 30 days and find the weekday that needs reply cover.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Replace the demo data: clear the yellow rows of each sheet and type your own. Everything calculated fills in again by itself. The workbook has no macros and works in Excel and other spreadsheet tools.',
    'Read the Enquiry Dashboard and the Charts sheet every week: enquiries, replies, consultations, quotes, contracts, lost enquiries and demand by due month.']
listing = {"title": "Doula Business Enquiries, Consultations and Quotes Excel Template: Quote Builder, Funnel, Lost Enquiries, Due-Month Demand",
    "headline": "Win more clients: from the first enquiry to a signed quote",
    "tags": ["doula business", "doula template", "enquiry tracker", "quote builder", "doula contract", "client intake", "excel template", "birth doula", "postpartum doula", "lead tracker", "consultation log", "doula packages", "doula admin"],
    "description": ("Run the front door of a doula business in one Excel workbook. Built for an owner-doula, a small doula agency or a solo doula who answers enquiries, holds consultations, sends quotes and decides which due dates to accept.\n\n"
        "Enquiries records every enquiry with the source, the service and the due date wanted, the hours to a first reply and the outcome. Consultations and the Consultation Calendar show booked, held and missed consultations and the free slots. Quotes holds the package, the discount, the add-ons, the travel fee, the deposit, the balance date, the instalment dates and the valid-until date, and the Follow-up List tells you who to call, write to or welcome today.\n\n"
        "Funnel by Month, Source Conversion, Reply Time Bands, Lost Reasons and Lost Value by Month show where enquiries drop out and which sources sign. Demand by Due Month sets the enquiries and open quotes wanting each month against your own monthly limit before you say yes to a date.\n\n"
        f"{len(tools)} tools answer the weekly questions: a quote builder with income per hour against your target, a funnel check, a lost-enquiry cause analyser, a due-month demand map, a 30-day pipeline forecast, reply-time impact, a discount cost test, quote expiry, package win rates, a travel fee check and instalment offers. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to enquirers, clients, the owner-doula, the admin, a doula and a care-provider office.\n\n"
        "This is part one of the Doula Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Clients appear by name, area, due date and package only, with no medical detail. It helps you keep track of dates, hours, money and capacity and does not promise results. Prices and targets are your own settings. Check your local rules for contracts, privacy and records."),
    "features": ["Quote builder with deposit, balance date and instalments", "Income per hour against your own target", "Follow-up list: who to call or write today", "Consultation calendar with free slots", "Due-month demand against your monthly limit",
                 "Funnel by month with your own 6-month rates", "Source conversion and reply-time bands", "Lost enquiries by reason with quote value lost", f"{len(tools)} decision tools with what-if rows", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
HINTS = {
 'quote_builder': 'Pick a package; type extra hours, extra visits, add-ons, miles, a discount and instalments; see the total, deposit, balance and instalment dates and the income per hour against your target.',
 'reply_impact': 'Type your usual hours to a first reply, the enquiries a month and a contract value; see the share that booked and signed after each reply speed and the contracts a faster reply adds.',
 'funnel_tool': 'Type the last 3 months from Funnel by Month; each step is set against your own previous 6 months and the weakest step is named with the verdict.',
 'source_compare': 'Pick an enquiry source: its enquiries and contracts over 6 months against all sources, its 12-month conversion and rank, and the verdict strong, average or weak.',
 'lost_cause': 'Lost enquiries by cause with the quote value lost, side by side; type the days for the declined share and the share you could win back; the verdict names the cause to fix first.',
 'price_lost': 'Type a discount, your yearly contracts, the average quote and the win-back share; see the break-even number of price-lost enquiries in closed form and the verdict.',
 'follow_sched': 'Type the consultation date and the outcome; see the days since, the follow-up date and the next step: call today, write today, close, offer another time or wait.',
 'noshow_tool': 'Type the consultations booked a month, a no-show rate, your signing rate and the average quote; see the contracts and value lost and the extra slots to offer.',
 'length_tool': 'Type the minutes you plan; see the consultations held and the signed share in four length bands from your last 12 months and whether longer signs more.',
 'demand_map': 'Pick a due month and the extra due dates you could take; see enquiries, clients booked, open quotes and spaces against your monthly limit, with the verdict.',
 'discount_cost': 'Type discount rates and the most you accept to give up; see what signed contracts gave up in 12 months, per discounted contract, and what your rates would give up.',
 'pipeline_fc': 'Pick Base, Best or Worst: open enquiries at each step times your own rates give the expected contracts in 30 days against what you want from the pipeline.',
 'expiry_tool': 'Type the days that count as ending soon and the days a quote stays valid; see quotes ending, the value at risk and the quotes past their date, with the verdict.',
 'pkg_mix': 'Pick a package: its quotes, contracts and win rate of the last 12 months against all packages and its rank, with the verdict wins at consultation, keep or rework.',
 'service_mix': 'Pick an area and the postpartum share you want; see birth, postpartum and both-service enquiries and signed shares over 12 months, with the verdict.',
 'area_travel': 'Pick an area, the visits per client and the share of mileage a fee should cover; see the mileage cost per client against the travel fee you quote now.',
 'inst_offer': 'Type the quote total to start from; see the signing rates with and without a payment plan and the share of contracts on a plan, with the verdict.',
 'reply_cover': 'Pick a weekday: the enquiries, the average hours to a first reply and the share replied within your target against all days, with the verdict cover or fine.',
}
for _t in tables + tools:
    if _t['key'] in HINTS: _t['hint'] = HINTS[_t['key']]
s = spec(id=f'{SUITE}-p1', slug='doula-business-enquiries', profession='Doula Business', name='Enquiries, Consultations, Quotes',
         tagline='Win more clients: from the first enquiry to a signed quote', price_usd=29,
         colors={"primary": "#4A3F6B", "accent": "#E8A87C"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 1, "of": 8, "focus": "Enquiries, consultations and quotes"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'du1.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'name', len(s['name']))
