"""Home Management suite - part 7: Documents, Contacts and Renewals."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho7_lists import *
from ho7_tables import *
from ho7_tools import tools, V, F as FX
import ho7_data as D

SUITE = 'fx-20261118-home-management'
NOTE = "Sample wording: adapt it to your own household and your local rules; check the issuing office for the papers it asks for."
def FW(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
NO = '{list:yesno.no}'

# ------------------------------------------------------------------ forms (12)
def DK(c): return LK('documents', 'doc_id', c)
forms = [
    FORM('doc_card', 'Document Card', 'One document with its dates and status', 'documents.doc_id', FW(
        ('Document', 'documents.doc'), ('Kind', 'documents.kind'), ('Holder', 'documents.holder'), ('Expiry or renewal date', 'documents.expiry'), ('Act this many days before', 'documents.renew_lead_days'),
        ('Kept where', 'documents.kept_where'), ('Status', 'documents.status'), ('Handled by', 'documents.handler'), ('Days left', 'documents.days_left'), ('Action date', 'documents.action_date'),
        ('Days to the action date', 'documents.dta'), ('Action status', 'documents.astatus')) + [
        FF('Share of the lead time left', 'IFERROR(MAX(0,MIN(1,%s/%s)),0)' % (DK('days_left'), DK('renew_lead_days')), 'pct')]),
    FORM('renewal_sheet', 'Renewal Sheet', 'One item of the next 90 days', 'renewals.no', FW(
        ('Type', 'renewals.type'), ('Name', 'renewals.name'), ('Owner', 'renewals.owner'), ('Date', 'renewals.date'), ('Days left', 'renewals.days_left'), ('Action date', 'renewals.action'),
        ('Days to the action date', 'renewals.action_in'), ('Action status', 'renewals.verdict')) + [
        FF('Items of the same type in the list', 'COUNTIFS({range:renewals.type},%s)' % LK('renewals', 'no', 'type'), 'int'), FF('Items due on or before this one', '{pick}', 'int')]),
    FORM('trip_sheet', 'Travel Document Check Sheet', 'One travel document against the family trip', 'documents.doc_id', FW(
        ('Document', 'documents.doc'), ('Holder', 'documents.holder'), ('Expiry', 'documents.expiry'), ('Family trip', 'documents.trip_date'), ('Back from the trip', 'documents.trip_end'),
        ('Days valid after the trip', 'documents.trip_margin'), ('Action date', 'documents.action_date'), ('Action status', 'documents.astatus')) + [
        FF('Days from the expiry to the trip start', '%s-%s' % (DK('expiry'), DK('trip_date')), 'int'), FF('Renew by with the usual lead time', '%s-{set:default_lead}' % DK('expiry'), 'date'),
        FF('Days from today to the trip', '%s-{today}' % DK('trip_date'), 'int')]),
    FORM('contract_sheet', 'Contract Review Sheet', 'One contract or policy: review and notice dates', 'board.no', FW(
        ('Document', 'board.doc'), ('Kind', 'board.kind'), ('Holder', 'board.holder'), ('Expiry or renewal date', 'board.expiry'), ('Days left', 'board.days_left'), ('Review by', 'board.review_by'),
        ('Give notice by', 'board.notice_by'), ('Action date', 'board.action_date'), ('Status', 'board.status'), ('Handled by', 'board.handler'), ('Kept where', 'board.kept_where')) + [
        FF('Days to the review date', '%s-{today}' % LK('board', 'no', 'review_by'), 'int'), FF('Days to give notice', '%s-{today}' % LK('board', 'no', 'notice_by'), 'int')]),
    FORM('contact_card', 'Contact Card', 'One contact: phone, last used, last job cost', 'contacts.contact_id', FW(
        ('Name', 'contacts.name'), ('Kind', 'contacts.kind'), ('Trade or role', 'contacts.trade'), ('Phone', 'contacts.phone'), ('E-mail', 'contacts.email'), ('Last used', 'contacts.last_used'),
        ('Cost line, last time', 'contacts.cost_last'), ('Would use again', 'contacts.would_use_again'), ('Days since last used', 'contacts.days_since')) + [
        FF('Days until it counts as not used', '{set:stale_days}-%s' % LK('contacts', 'contact_id', 'days_since'), 'int'), FF('Contacts of the same kind', 'COUNTIFS({range:contacts.kind},%s)' % LK('contacts', 'contact_id', 'kind'), 'int')]),
    FORM('emergency_sheet', 'Emergency Contacts Sheet', 'One emergency line: who to call and the phone', 'emergency.who', FW(
        ('Page', 'emergency.page'), ('When to call', 'emergency.when_to_call'), ('Name', 'emergency.name'), ('Phone', 'emergency.phone'), ('Number last checked', 'emergency.last_checked'),
        ('Days since checked', 'emergency.days_checked')) + [
        FF('Days until the next check', '{set:check_days}-%s' % LK('emergency', 'who', 'days_checked'), 'int'), FF('Lines on the emergency sheet', 'COUNTA({range:emergency.who})', 'int')]),
    FORM('sitter_form', 'Sitter Print Sheet', 'The one-page sitter sheet with its lines', 'sitter.sheet', FW(
        ('Sheet', 'sitter.sheet'), ('Sheet for the evening of', 'sitter.sheet_date'), ('Babysitter', 'sitter.bs_name'), ('Babysitter phone', 'sitter.bs_phone')) + [
        FF('Lines filled', 'SUMIFS({range:sitter.filled},{range:sitter.sheet},{pick})', 'int'), FF('Lines empty', 'COUNTIFS({range:sitter.sheet},{pick},{range:sitter.filled},0)', 'int'),
        FF('Days to the evening', '%s-{today}' % LK('sitter', 'sheet', 'sheet_date'), 'int')],
        {"from": "sitter", "match": "sitter.sheet", "columns": ["item", "source", "value"], "max": 20}),
    FORM('key_sheet', 'Key Handover Sheet', 'One key or remote handed to someone', 'keys.key_id', FW(
        ('Holder', 'keys.holder'), ('What', 'keys.what'), ('Since', 'keys.since'), ('Out, 1 or 0', 'keys.out'), ('Days out', 'keys.days_out'), ('Note', 'keys.note'),
        ('Family trip', 'keys.trip_date'), ('Back from the trip', 'keys.trip_end'), ('Hold the key from', 'keys.key_from')) + [
        FF('Days out beyond the key limit', 'MAX(0,%s-{set:key_days})' % LK('keys', 'key_id', 'days_out'), 'int'), FF('Keys out in all', 'SUM({range:keys.out})', 'int')]),
    FORM('location_sheet', 'Document Location Sheet', 'One storage place and the documents in it', 'storage.kept', FW(
        ('Kept where', 'storage.kept'), ('Documents', 'storage.docs'), ('Expiring in 12 months', 'storage.exp12')) + [
        FF('Share of all documents', 'IFERROR(%s/COUNTIFS({range:documents.active},1),0)' % LK('storage', 'kept', 'docs'), 'pct'), FF('Documents with no place typed', 'SUM({range:documents.kept_missing})', 'int')],
        {"from": "documents", "match": "documents.kept_where", "columns": ["doc", "holder", "expiry", "status"], "max": 30}),
    FORM('warranty_sheet', 'Warranty Paper Sheet', 'One warranty with its receipt and manual', 'warranties.item_id', FW(
        ('Item', 'warranties.item'), ('Room', 'warranties.room'), ('Warranty end', 'warranties.warranty_end'), ('Price', 'warranties.price'), ('Handled by', 'warranties.handler'),
        ('Receipt kept', 'warranties.receipt'), ('Manual kept', 'warranties.manual'), ('Days left', 'warranties.days_left'), ('In the next 90 days, 1 or 0', 'warranties.in90'), ('Note', 'warranties.note')) + [
        FF('Days of warranty left, not below 0', 'MAX(0,%s)' % LK('warranties', 'item_id', 'days_left'), 'int'), FF('Warranty ends in the next 90 days', 'SUM({range:warranties.in90})', 'int')]),
    FORM('policy_card', 'Policy Card', 'One policy or contract: lead, review and notice', 'documents.doc_id', FW(
        ('Document', 'documents.doc'), ('Kind', 'documents.kind'), ('Expiry or renewal date', 'documents.expiry'), ('Act this many days before', 'documents.renew_lead_days'), ('Action date', 'documents.action_date'),
        ('Handled by', 'documents.handler'), ('Kept where', 'documents.kept_where')) + [
        FF('Review by with the review lead', '%s-{set:review_lead}' % DK('expiry'), 'date'), FF('Give notice by with the notice period', '%s-{set:notice_days}' % DK('expiry'), 'date'),
        FF('Notice period typed in Settings, days', '{set:notice_days}', 'int'), FF('Days to the expiry', DK('days_left'), 'int')]),
    FORM('routine_sheet', 'Home Routine Sheet', 'One house routine for the sitter or a visitor', 'routines.routine', FW(
        ('Routine', 'routines.routine'), ('When', 'routines.when'), ('Last reviewed', 'routines.reviewed'), ('Days since reviewed', 'routines.age'), ('Babysitter', 'routines.bs_name'),
        ('Babysitter phone', 'routines.bs_phone'), ('Neighbour', 'routines.nb_name')) + [
        FF('Reviewed within a year, 1 or 0', 'IF(%s<=365,1,0)' % LK('routines', 'routine', 'age'), 'int'), FF('Routines on the sheet', 'COUNTA({range:routines.routine})', 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
def PG(*a): return list(a)
documents = [
    DOC('list_doc', 'Documents Renewals List', 'Documents and renewals list, by days left', 'board.no', [
        'Documents and renewals of {set:household}, dated {today}. Rank {col:board.no}: {col:board.doc}, held by {col:board.holder}, a {col:board.kind}.',
        'Expiry or renewal date: {col:board.expiry}, {col:board.days_left} days left. Action date: {col:board.action_date}. Status: {col:board.status}. Handled by {col:board.handler}.',
        'Kept where: {col:board.kept_where}. The list runs by days left, the soonest first, so the top rows are the ones to start now.',
        'Print the sheet once a month and keep it in the document box.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('next90_doc', 'Next 90 Days Page', 'Renewals of the next 90 days, one item', 'renewals.no', [
        'Renewals of {set:household}, dated {today}. Item {col:renewals.no}: {col:renewals.name} ({col:renewals.type}), owner {col:renewals.owner}.',
        'Date: {col:renewals.date}, {col:renewals.days_left} days left. Action date: {col:renewals.action}, {col:renewals.action_in} days from today. Status: {col:renewals.verdict}.',
        'The list gathers documents, contracts, warranties, vehicle dates, pet dates and filter, alarm and service tasks, sorted by date.',
        'Dates are calculated from your entries.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('trip_doc', 'Trip Travel Documents', 'Travel documents check for the trip', 'documents.doc_id', [
        'Travel document check of {set:household}, dated {today}. Traveller: {col:documents.holder}. Document: {col:documents.doc}, expiry {col:documents.expiry}.',
        'Family trip from {col:documents.trip_date} to {col:documents.trip_end}. Days valid after the trip: {col:documents.trip_margin} (a negative number means it expires before you are back).',
        'Action date: {col:documents.action_date}, status {col:documents.astatus}. Lead time typed: {col:documents.renew_lead_days} days. Check the entry rules of the country you visit.',
        'Sign when the new document is received.'], ['Traveller', 'Adult 1'], NOTE),
    DOC('contract_doc', 'Contract Review List', 'Contract and policy review page', 'board.no', [
        'Contract review of {set:household}, dated {today}. {col:board.doc}, a {col:board.kind}, held by {col:board.holder}.',
        'Ends on {col:board.expiry}, {col:board.days_left} days left. Review by {col:board.review_by}. Give notice by {col:board.notice_by} (check the notice period in your contract). Handled by {col:board.handler}.',
        'Compare the price, the term and the terms of leaving with two other offers before the review date. Kept where: {col:board.kept_where}.',
        'Write the decision and the date here.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('emergency_doc', 'Emergency Contacts Page', 'Emergency contacts page for the fridge', 'emergency.who', [
        'Emergency contacts of {set:household}, dated {today}. Page: {col:emergency.page}. Who: {col:emergency.who}, {col:emergency.name}.',
        'Phone: {col:emergency.phone}. When to call: {col:emergency.when_to_call}. Number last checked: {col:emergency.last_checked}, {col:emergency.days_checked} days ago.',
        'Print the page, put it on the fridge and give a copy to the sitter and the neighbour. Names and numbers only, no health details.',
        'Check every number again every {set:check_days} days.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('sitter_doc', 'Sitter Sheet Page', 'Sitter sheet for the evening', 'sitter.sheet', [
        'Sitter sheet of {set:household}, for the evening of {col:sitter.sheet_date}. Welcome, {col:sitter.bs_name}.',
        'Children by first name, numbers, school hours, house routines such as bin day and feed times, where things are and who to call are on the Sitter sheet sheet; this page is the cover.',
        'First call: the adults, then the neighbour. Your number is {col:sitter.bs_phone}. No health details are written down here; ask us before the evening.',
        'Thank you for looking after the children.'], ['Adult 1', 'Babysitter'], NOTE),
    DOC('handover_doc', 'House Sitter Handover', 'House-sitter handover: routines, keys, who to call', 'keys.key_id', [
        'House-sitter handover of {set:household}, dated {today}. Key: {col:keys.what}, held by {col:keys.holder} since {col:keys.since}.',
        'We are away from {col:keys.trip_date} to {col:keys.trip_end}. Please hold the key from {col:keys.key_from}. Neighbour: {col:keys.nb_name}, {col:keys.nb_phone}. Grandparent: {col:keys.gp_name}, {col:keys.gp_phone}.',
        'Routines and where things are are on the Home routines and Where things are sheets. Dog walker: {col:keys.dw_name}, {col:keys.dw_phone}.',
        'Keep this page with the keys.'], ['Adult 1', 'House sitter'], NOTE),
    DOC('keys_doc', 'Key Access List Page', 'Key and access list, one key', 'keys.key_id', [
        'Key and access record of {set:household}. {col:keys.key_id}: {col:keys.what}, held by {col:keys.holder}.',
        'Since {col:keys.since}. Out (1 yes, 0 no): {col:keys.out}. Days out: {col:keys.days_out}. Note: {col:keys.note}.',
        'A key out longer than {set:key_days} days is checked at the next review. Write the date it comes back in the Returned column.',
        'Signed by the holder when the key is returned.'], ['Holder', 'Adult 1'], NOTE),
    DOC('kinds_doc', 'Contacts By Kind Page', 'Contacts by kind page', 'contact_kind.kind', [
        'Contacts of {set:household}, dated {today}. Kind: {col:contact_kind.kind}. Contacts: {col:contact_kind.contacts}, with a phone: {col:contact_kind.with_phone}.',
        'Write the name, the trade and the phone of each contact of this kind under this line and check them once a year.',
        'Print one page per kind and keep the pages together in the document box. Update the phone numbers once a year.',
        'The vet clinic is a dates-only contact.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('holders_doc', 'Documents By Holder Page', 'Documents by holder page', 'holders.holder', [
        'Documents of {set:household}, dated {today}. Holder: {col:holders.holder}, {col:holders.name}. Kind: {col:holders.kind}. Documents held: {col:holders.docs}.',
        'Next expiry: {col:holders.next_expiry}, {col:holders.next_days} days left. Next document: {col:holders.next_doc}.',
        'Review these papers together on {col:holders.review_date} and put them back in their place.',
        'A single adult keeps only the first rows.'], ['Holder', 'Adult 1'], NOTE),
    DOC('letter_doc', 'Renewal Letter', 'Renewal letter to a contract provider', 'board.no', [
        'Dear provider, our agreement {col:board.doc} held by {set:household} ends on {col:board.expiry}.',
        'We would like to talk about renewing it and ask for the options and prices before {col:board.review_by}. If we decide to leave, we will give notice by {col:board.notice_by}.',
        'Please send the offer in writing and tell us the notice period in your terms. Our phone numbers are in the signature.',
        'Thank you, {set:household}.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('storage_doc', 'Storage List Page', 'Document copy and storage list', 'storage.kept', [
        'Document storage of {set:household}, dated {today}. Place: {col:storage.kept}. Documents kept there: {col:storage.docs}. Expiring in 12 months: {col:storage.exp12}.',
        'Keep a copy of every document in a second place, for example a saved copy online and the paper in the box. List the documents of the place on the Document Location Sheet.',
        'Check the places once a year and move what has expired.',
        'No document numbers are written here, only the places.'], ['Adult 1', 'Adult 2'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('renew_travel', 'Renew A Travel Document', 'documents', 'documents.expiry', [('Check what the new document needs', -75), ('Gather the photos and the old document', -65), ('Book the appointment', -55), ('Submit the application', -45), ('Sign the new document and the photo copy', -10), ('Collect the new document', -5), ('Type the new expiry date', 0), ('Keep the old one as the rules say', 7)]),
    CHK('before_trip', 'Before A Family Trip', 'keys', 'keys.since', [('Check every travel document against the trip', -45), ('Renew what expires before the return', -40), ('Check the entry rules of where you go', -30), ('Print the Emergency contacts page', -7), ('Give the spare key to the neighbour', -3), ('Send the dates to the school and the carpool family', -3), ('Put the sitter sheet on the fridge', -1)]),
    CHK('renew_policy', 'Renew A Policy Or Contract', 'documents', 'documents.expiry', [('Read the renewal offer', -60), ('Ask for two other offers', -50), ('Compare price, term and terms of leaving', -40), ('Give notice if you leave', -30), ('Decide and tell the provider', -21), ('Type the new dates', 0), ('File the new paper', 3)]),
    CHK('yearly_review', 'Yearly Numbers Review', 'emergency', 'emergency.last_checked', [('Ring each number on the emergency sheet', 180), ('Update the numbers that changed', 181), ('Check the places where the papers are kept', 182), ('Check every expiry on Documents', 183), ('Move expired papers out of the box', 184), ('Type the new check date', 185)]),
    CHK('monthly_glance', 'Warranty Ends Soon', 'warranties', 'warranties.warranty_end', [('Find the receipt and the manual', -60), ('Test the item and list the faults', -45), ('Call the seller or the maker about a fault', -30), ('Send the receipt and the photos', -21), ('Decide: repair, replace or let it end', -7), ('Type the outcome in the note', 0)]),
    CHK('school_papers', 'New School Year Papers', 'documents', 'documents.expiry', [('Collect the forms from the school', -30), ('Check the emergency contact form', -25), ('Sign the consent forms', -14), ('Type the new dates on Documents', -7), ('Put the copies in the document box', 0)]),
    CHK('sitter_evening', 'Sitter Evening Handover', 'team', 'team.start', [('Check every line of the sitter sheet', -2), ('Print the sheet', -1), ('Tell the sitter the bedtimes', 0), ('Leave the key and note where it goes back', 0), ('Tell the neighbour the evening', 0), ('Collect the key the next morning', 1)]),
    CHK('sitter_handover', 'House Sitter Steps', 'routines', 'routines.reviewed', [('Review the home routines', 0), ('Walk through the house with the sitter', 1), ('Show the stopcock and the fuse box', 1), ('Hand over the keys and type the date', 2), ('Give the emergency contacts page', 2), ('Check the key is returned', 14)]),
    CHK('new_contact', 'New Contact Or Trade', 'contacts', 'contacts.last_used', [('Type the name, trade and phone', 0), ('Ring the number to test it', 0), ('Add it to the emergency sheet if it matters', 1), ('Type the cost line after the first job', 7), ('Mark would use again', 7)]),
    CHK('lost_document', 'Lost Document', 'documents', 'documents.expiry', [('Look in the kept-where place and the second place', 0), ('Record the date it was lost', 0), ('Report it if the rules ask', 1), ('Ask the issuer for a replacement', 1), ('Type the new date and place', 14)]),
    CHK('move_papers', 'Move Change Of Papers', 'documents', 'documents.expiry', [('List the papers that carry the address', -56), ('Tell the school and the doctor of the move', -42), ('Tell the insurers and the bank', -30), ('Tell the vehicle and the pet registers', -21), ('Update the address on Documents', -7), ('Check every paper after the move', 14)]),
    CHK('single_first', 'Single Adult First Set Up', 'team', 'team.start', [('Replace the demo data with your own', 0), ('List your papers on Documents', 0), ('Type the expiry dates and the lead times', 1), ('Type where each paper is kept', 1), ('Type your contacts', 2), ('Leave the children and sitter rows empty', 2)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('a1_travel', 'Adult 1: travel document, start by', 'documents', 'documents.a1_phone', 'Hi {a1_name}, the travel document of {holder} expires on {expiry}, the trip is on {trip_date}, we should start by {action_date}. {household}'),
    M('a1_lead', 'Adult 1: the lead time no longer fits', 'documents', 'documents.a1_phone', 'Hi {a1_name}, the lead time of {renew_lead_days} days no longer fits for {doc}, can you apply this week? {household}'),
    M('a2_renews', 'Adult 2: the document renews', 'documents', 'documents.a2_phone', 'Hi {a2_name}, the {doc} renews on {expiry}, I added the action date {action_date}. {household}'),
    M('a2_licence', 'Adult 2: your licence is on the list', 'documents', 'documents.a2_phone', 'Hi {a2_name}, your {doc} is on the list, the renewal is on {expiry}. {household}'),
    M('a1_kept', 'Adult 1: where is the document kept', 'documents', 'documents.a1_phone', 'Hi {a1_name}, please check where the {doc} is kept, it says {kept_where}. {household}'),
    M('a2_due90', 'Adult 2: papers close to the end', 'board', 'board.a2_phone', 'Hi {a2_name}, the {doc} has {days_left} days left and its status is {status}, can you look at it this week? {household}'),
    M('c1_sign', 'Child 1: sign and photograph it', 'documents', 'documents.c1_phone', 'Hi {c1_name}, your travel document must be signed and photographed by {action_date}. {household}'),
    M('c1_form', 'Child 1: school form to sign', 'documents', 'documents.c1_phone', 'Hi {c1_name}, the school form {doc} needs a signature by {expiry}. {household}'),
    M('c2_photo', 'Child 2: your travel photo appointment', 'documents', 'documents.c2_phone', 'Hi {c2_name}, your travel photo appointment is on {action_date} at {visit_at}. {household}'),
    M('c2_letter', 'Child 2: keep the school letter', 'documents', 'documents.c2_phone', 'Hi {c2_name}, please keep the letter from school in the document box, the place is {kept_where}. {household}'),
    M('gp_key', 'Grandparent: hold the spare key', 'keys', 'keys.gp_phone', 'Hello {gp_name}, we are travelling on {trip_date}, can you hold the spare key from {key_from}? {household}'),
    M('gp_doc', 'Grandparent: look after a document', 'board', 'board.gp_phone', 'Hello {gp_name}, please look after the {doc} while we are away, it belongs to {holder}. {household}'),
    M('bs_sheet', 'Babysitter: the sitter sheet', 'sitter', 'sitter.bs_phone', 'Hello {bs_name}, the sitter sheet for {sheet_date} is attached, numbers and routines are on one page. {household}'),
    M('bs_bin', 'Babysitter: bin day and the spare key', 'routines', 'routines.bs_phone', 'Hello {bs_name}, {routine}: {when}. The spare key is with {nb_name}. {household}'),
    M('bs_call', 'Babysitter: who to call first', 'emergency', 'emergency.bs_phone', 'Hello {bs_name}, please call {name} first if there is a problem with the house, the number is {phone}. {household}'),
    M('cp_travel', 'Carpool family: our travel dates', 'board', 'board.cp_phone', 'Hello {cp_name}, our travel dates are {trip_date} to {trip_end}, we are out of the rota. {household}'),
    M('cp_number', 'Carpool family: add our number', 'emergency', 'emergency.cp_phone', 'Hello {cp_name}, please add our number to the activity list. Thank you, {household}'),
    M('so_numbers', 'School office: contact numbers updated', 'emergency', 'emergency.so_phone', 'Hello {so_name}, our contact numbers are updated, please confirm the emergency contacts. Last checked on {last_checked}. {household}'),
    M('so_form', 'School office: the form is signed', 'board', 'board.so_phone', 'Hello {so_name}, the form {doc} is signed and attached. {household}'),
    M('so_away', 'School office: a child will be away', 'board', 'board.so_phone', 'Hello {so_name}, {holder} will be away from {trip_date} to {trip_end}. {household}'),
    M('nb_key', 'Neighbour: you hold our spare key', 'keys', 'keys.nb_phone', 'Hello {nb_name}, you hold our spare key since {since}, please keep it until {trip_end}. {household}'),
    M('nb_call', 'Neighbour: who to call', 'emergency', 'emergency.nb_phone', 'Hello {nb_name}, please call {name} if there is a problem at the house, the number is {phone}. {household}'),
    M('dw_walk', 'Dog walker: the walk is cancelled', 'keys', 'keys.dw_phone', 'Hello {dw_name}, the walk on {trip_date} is cancelled, the key is with {nb_name}. {household}'),
    M('ll_copy', 'Landlord or agent: agreement copy', 'board', 'board.ll_phone', 'Hello {ll_name}, please send a copy of the {doc}, it ends on {expiry}. {household}'),
    M('ll_end', 'Landlord or agent: the agreement ends', 'board', 'board.ll_phone', 'Hello {ll_name}, the agreement {doc} ends on {expiry}, we would like to talk about renewing. {household}'),
    M('pl_stopcock', 'Plumber: add our number', 'where_things', 'where_things.pl_phone', 'Hello {pl_name}, please add our number to your contacts, the {thing} is at {place}. {household}'),
    M('he_plan', 'Heating engineer: confirm the contract', 'board', 'board.he_phone', 'Hello {he_name}, please confirm that the {doc} renews on {expiry}. {household}'),
    M('a1_policy', 'Adult 1: the policy renews', 'documents', 'documents.a1_phone', 'Hi {a1_name}, the {doc} renews on {expiry}, please compare the offers by {action_date}. {household}'),
    M('a2_mobile', 'Adult 2: the mobile contract ends', 'documents', 'documents.a2_phone', 'Hi {a2_name}, the {doc} ends on {expiry}, please ask for the options by {action_date}. {household}'),
    M('a2_broadband', 'Adult 2: the broadband contract ends', 'documents', 'documents.a2_phone', 'Hi {a2_name}, the {doc} ends on {expiry}, notice by {action_date}. {household}'),
    M('cm_test', 'Car mechanic: the annual test date', 'vehicle_dates', 'vehicle_dates.cm_phone', 'Hello {cm_name}, please send the annual test date for the {vehicle}. {household}'),
    M('guest_rules', 'Guest: the house rules', 'contacts', 'contacts.phone', 'Hello {name}, the house rules and where to find things are in the attached sheet. {household}'),
    M('hm_month', 'Household: renewals of the month', 'renew_month', 'renew_month.a1_phone', 'Hi {a1_name}, the renewals for {month} are {items}, the first is {first_doc} on {first_date}. {household}'),
    M('hm_review', 'Household: the document review', 'holders', 'holders.phone', 'Hello {name}, the document review is on {review_date}, please bring your folder, you hold {docs} documents. {household}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def C_(*a): return 'COUNTIFS(' + ','.join(a) + ')'
def SS(c, flag): return 'SUM(%s)' % R(c, flag)
SUM_ALL = lambda f: '(' + '+'.join('SUM(%s)' % R(t, f) for t in SRC) + ')'
K = lambda label, f, fmt='int', **kw: KPI(label, f, fmt, **kw)
A1H = '(' + '+'.join('COUNTIFS(%s,%s,%s,1)' % (R(t, 'handler' if t != 'tasks' else 'assigned'), H1, R(t, 'in12')) for t in SRC) + ')'
kpis = [
    K('Documents and renewals tracked', C_(DR('active'), '1')),
    K('Documents valid now', C_(DR('active'), '1', DR('days_left'), '">=0"')),
    K('Documents expiring in 30 days', C_(DR('days_left'), '">=0"', DR('days_left'), '"<=30"')),
    K('Documents expiring in 90 days', 'SUM(%s)' % DR('in90')),
    K('Documents expired', C_(DR('active'), '1', DR('days_left'), '"<0"'), alert={"when": "> 0", "style": "bad"}),
    K('Documents past the action date', C_(DR('dta'), '"<0"'), alert={"when": "> 0", "style": "warn"}),
    K('Lead time missed', C_(DR('astatus'), W_MISSED), alert={"when": "> 0", "style": "bad"}),
    K('Days to the next expiry', 'IFERROR(SMALL(%s,COUNTIF(%s,"<0")+1),"")' % (DR('days_left'), DR('days_left'))),
    K('Days to the next action date', 'IFERROR(SMALL(%s,COUNTIF(%s,"<0")+1),"")' % (DR('dta'), DR('dta'))),
    K('Travel documents ending before the trip', C_(DR('trip_margin'), '"<0"'), alert={"when": "> 0", "style": "bad"}),
    K('Days to the family trip', 'IF({set:trip_date}="","",{set:trip_date}-{today})'),
    K('Travel documents valid for the trip', C_(DR('trip_margin'), '">=0"')),
    K('Documents without a place kept', SS('documents', 'kept_missing'), alert={"when": "> 0", "style": "warn"}),
    K('Documents renewed last 12 months', C_(DR('renewed_on'), '">="&({today}-364)', DR('renewed_on'), '"<="&{today}')),
    K('Renewals in the next 90 days, all types', SUM_ALL('in90')),
    K('Renewals in the next 12 months', SUM_ALL('in12')),
    K('Warranty ends in the next 90 days', SS('warranties', 'in90')),
    K('Vehicle dates in the next 90 days', SS('vehicle_dates', 'in90')),
    K('Pet dates in the next 90 days', SS('pet_dates', 'in90')),
    K('Filters and alarm tasks due in 90 days', SS('tasks', 'in90')),
    K('Busiest renewal month, items', 'MAX(%s)' % RMR('items')),
    K('Contracts ending in 90 days', C_(DR('kind'), K_CON, DR('in90'), '1')),
    K('Policies ending in 90 days', C_(DR('kind'), K_POL, DR('in90'), '1')),
    K('Contacts in the directory', 'COUNTA(%s)' % CR('contact_id')),
    K('Contacts with a phone', 'SUM(%s)' % CR('phone_ok')),
    K('Contacts not used for 12 months', 'SUM(%s)' % CR('stale')),
    K('Contacts marked would use again', C_(CR('would_use_again'), YES)),
    K('Keys out', 'SUM(%s)' % KR('out')),
    K('Sitter sheet fields filled', 'SUM(%s)' % SR('filled')),
    K('Renewals handled by adult 1', A1H),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Documents Dashboard", "kpis": kpis,
    "monthly": {"title": "Last job cost and warranty prices by month", "date": "contacts.last_used", "series": [
        {"label": "Last job cost line", "sum": "contacts.cost_last", "date": "contacts.last_used"}, {"label": "Warranty price by month of end", "sum": "warranties.price", "date": "warranties.warranty_end"}]},
    "breakdowns": [{"title": "Renewals in the next 90 days by type", "by": "renew_type.type", "value": "renew_type.next90", "agg": "sum"},
                   {"title": "Documents by place kept", "by": "storage.kept", "value": "storage.docs", "agg": "sum"},
                   {"title": "Documents by holder", "by": "holders.holder", "value": "holders.docs", "agg": "sum"},
                   {"title": "Contacts by kind", "by": "contact_kind.kind", "value": "contact_kind.contacts", "agg": "sum"}]}
def W(c, op, v): return (c, op, v)
YESV = '{list:yesno.yes}'
insights = {"filters": [{"label": "Holder", "list": "epeople"}, {"label": "Handled by", "list": "hand"}],
    "gauges": [
        {"title": "Documents valid now", "num": AGG('count', 'documents', where=[W('active', '=', 1), W('days_left', '>=', 0)]), "den": AGG('count', 'documents', where=[W('active', '=', 1)])},
        {"title": "Documents with an action date ahead", "num": AGG('count', 'documents', where=[W('active', '=', 1), W('dta', '>=', 0)]), "den": AGG('count', 'documents', where=[W('active', '=', 1)])},
        {"title": "Travel documents valid for the trip", "num": AGG('count', 'documents', where=[W('trip_margin', '>=', 0)]), "den": AGG('count', 'documents', where=[W('trip_margin', '>=', -100000)])},
        {"title": "Contacts with a phone", "num": AGG('sum', 'contacts', 'contacts.phone_ok'), "den": AGG('count', 'contacts')},
        {"title": "Sitter sheet complete", "num": AGG('sum', 'sitter', 'sitter.filled'), "den": AGG('count', 'sitter')},
        {"title": "Renewals started before the action date", "num": AGG('count', 'documents', where=[W('early', '=', 1)]), "den": AGG('count', 'documents', where=[W('early', '>=', 0)])}],
    "charts": [
        CHART('Documents by kind', 'bar', 'documents.kind', [AGG('count', 'documents', where=[W('active', '=', 1)], label='Documents')]),
        CHART('Documents by holder', 'bar', 'documents.holder', [AGG('count', 'documents', where=[W('active', '=', 1)], label='Documents')]),
        CHART('Documents by status', 'bar', 'documents.status', [AGG('count', 'documents', label='Documents')]),
        CHART('Document expiries per month, next 12', 'column', 'renew_month.ahead', [AGG('sum', 'renew_month', 'renew_month.docs', label='Expiries')]),
        CHART('Document expiries per quarter, next 4', 'column', 'renew_month.qtr', [AGG('sum', 'renew_month', 'renew_month.docs', label='Expiries')]),
        CHART('Renewals next 90 days by type', 'bar', 'renew_type.type', [AGG('sum', 'renew_type', 'renew_type.next90', label='Next 90 days')]),
        CHART('Renewals per month, all types', 'column', 'renew_month.ahead', [AGG('sum', 'renew_month', 'renew_month.items', label='Renewals')]),
        CHART('Document renewals by owner, next 12 months', 'bar', 'documents.handler', [AGG('count', 'documents', where=[W('in12', '=', 1)], label='Renewals')]),
        CHART('Documents by place kept', 'bar', 'documents.kept_where', [AGG('count', 'documents', where=[W('active', '=', 1)], label='Documents')]),
        CHART('Action dates per month, next 12', 'column', 'renew_month.ahead', [AGG('sum', 'renew_month', 'renew_month.actions', label='Action dates')]),
        CHART('Lead time by kind, days', 'bar', 'documents.kind', [AGG('avg', 'documents', 'documents.renew_lead_days', where=[W('active', '=', 1)], label='Lead days')]),
        CHART('Contracts by month of end, next 12', 'column', 'renew_month.ahead', [AGG('sum', 'renew_month', 'renew_month.contracts', label='Contracts')]),
        CHART('Policies by month of end, next 12', 'column', 'renew_month.ahead', [AGG('sum', 'renew_month', 'renew_month.policies', label='Policies')]),
        CHART('Travel documents by holder', 'bar', 'documents.holder', [AGG('count', 'documents', where=[W('kind', '=', K_TRAV), W('active', '=', 1)], label='Travel documents')]),
        CHART('Contacts by kind', 'bar', 'contacts.kind', [AGG('count', 'contacts', label='Contacts')]),
        CHART('Contacts by month last used', 'column', 'month', [AGG('count', 'contacts', date='contacts.last_used', label='Contacts')]),
        CHART('Last job cost line by kind of contact', 'bar', 'contacts.kind', [AGG('sum', 'contacts', 'contacts.cost_last', label='Cost line')]),
        CHART('Keys out by holder', 'bar', 'keys.holder', [AGG('count', 'keys', where=[W('out', '=', 1)], label='Keys out')]),
        CHART('Warranty ends per month, next 12', 'column', 'renew_month.ahead', [AGG('sum', 'renew_month', 'renew_month.warr', label='Warranty ends')]),
        CHART('Vehicle dates per month, next 12', 'column', 'renew_month.ahead', [AGG('sum', 'renew_month', 'renew_month.veh', label='Vehicle dates')]),
        CHART('Pet dates per month, next 12', 'column', 'renew_month.ahead', [AGG('sum', 'renew_month', 'renew_month.pets', label='Pet dates')]),
        CHART('Documents renewed per month', 'column', 'month', [AGG('count', 'documents', date='documents.renewed_on', where=[W('status', '=', S_RENEWED)], label='Renewed')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Renewals next 90 days", "why": "documents, contracts, warranties, vehicle dates, pet dates and filter tasks in one ranked list with owner, days left and the action date", "where": "Renewals 90 Days Tool"},
    {"name": "Travel documents against a trip date", "why": "each travel document expiry against the trip date and your lead time: how many expire before it and the date to renew by", "where": "Trip Document Check"},
    {"name": "Action date finder", "why": "the expiry minus the days you need, with the first working day to start and the lead time left", "where": "Action Date Finder"},
    {"name": "Lead time what-if", "why": "the lead time stepped five times and the documents that fall inside each one, started or not", "where": "Lead Time What-if"},
    {"name": "Sitter sheet builder", "why": "the one-page sitter sheet checked line by line: children by first name, numbers, routines and where things are", "where": "Sitter Sheet Builder"},
    {"name": "Renewal load by adult", "why": "who handles the renewals of the next 12 months, a fairness line for a talk and not a score", "where": "Renewal Load By Adult"},
    {"name": "Key and access check", "why": "who holds a key, since when, returned or not, and the oldest key out", "where": "Key And Access Check"},
    {"name": "Contract review window", "why": "the next contract or policy to review and the date to start looking at the offers", "where": "Contract Review Window"},
    {"name": "Notice period checker", "why": "the last day to give notice on a contract and whether the window is still open", "where": "Notice Period Checker"},
    {"name": "Passports for the family trip", "why": "all four travel documents against the trip with the days each is valid after you are back", "where": "Passports For The Trip"}]
competitors = [
    {"what": "document organiser app with a yearly fee", "lacks": "stores scans in an account you pay for every year and has no lead time per document, no ranked list of what comes due and no household view"},
    {"what": "single-sheet renewals tracker template", "lacks": "a list of dates with no action date counted back, no status, no trip check and no contacts or sitter sheet"},
    {"what": "calendar reminder apps", "lacks": "ring on one date and cannot count back a lead time, rank all renewals together or show who handles what"},
    {"what": "contact book or notes on a phone", "lacks": "holds names and numbers but not the last time used, the cost line of the last job, the keys out or a one-page sitter sheet"}]
guide = [
    'Start here: this workbook tracks the papers, contacts and dates of your home. Open Start and type the household name, the trip date and the usual lead time in the yellow cells.',
    'Replace demo data: clear the yellow demo cells of Team, Documents, Contacts, Warranty dates, Vehicle dates, Pet dates, Maintenance due dates, Home routines, Where things are and Key and access list. Keep the lists and settings.',
    'Type your household on Team first: phones and first names are used by every text and by the emergency and sitter sheets.',
    'Calculated sheets (Renewals, Renewals by month, Document status board, Documents by holder, Emergency contact sheet, Sitter sheet): type the rank numbers or the keys once and the rest fills in.',
    'Every document has a typed lead time, the days before the expiry you act. The action date is the expiry minus the lead time; the status reads Act now, Soon, Lead time missed or OK.',
    'Monthly routine: open Renewals next 90 days, read the items past their action date, start the ones with the shortest lead time and tell the owner with a text.',
    'Yearly routine: check every paper on Documents, the places on Storage places and the numbers on the Emergency contact sheet, then write the next review date.',
    'Pick the tool of the question you have: renewals in 90 days, trip documents, action date finder, lead time what-if, contract review, notice period, key check, sitter sheet builder or contact lookup.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Sitter sheet: first names of the children, phone numbers you type, school hours, house routines and where things are. No health details are stored or printed anywhere in this workbook.',
    'A single adult uses documents, contacts and renewals unchanged and leaves the children, sitter and school rows empty.',
    'Renters add the tenancy agreement as a Contract with its renewal date and leave the owner-only papers; read a trade as a maintenance request to the landlord.',
    'Intervals and lead times are typical: check the manual, the issuing office and your local rules. Notice periods come from your contract.',
    'Why a workbook: one flat price, no yearly renewal, your data stays with you, nothing to link, no ads and no upsell. It runs in Excel and Google Sheets with no macros, no add-ins and no accounts.',
    'What this is not: not a reminder app, not a safety service, not legal, medical, veterinary or financial advice. Every date and total is calculated from your entries.',
]
listing = {"title": "Documents, Contacts and Renewals Excel Template: Document Expiry Tracker, Renewals Calendar, Sitter Sheet, Emergency Contacts",
    "headline": "Track every paper, contact and renewal date of your home in one workbook",
    "tags": ["document tracker", "renewals tracker", "expiry date tracker", "household documents", "emergency contacts", "sitter sheet", "travel documents", "contract renewal", "household planner", "family organiser", "key list", "no subscription", "home management"],
    "description": ("Know what expires, when to start and who handles it. Built for a single adult, a couple or a family, owners or renters: papers for the adults and the children, policies and contracts, warranty papers, vehicle and pet dates and the filters and alarms of the house. "
        "Every document has its holder, its expiry or renewal date, the place it is kept and a lead time you type: the action date is counted back from the expiry and the status reads Act now, Soon, Lead time missed or OK.\n\n"
        "One ranked list gathers the next 90 days from documents, contracts, warranties, vehicle dates, pet dates and maintenance tasks with the owner, the days left and the action date. Renewals by month and by type show the next 12 months, and a status board lists every document by days left.\n\n"
        f"{len(tools)} tools answer the questions of every month: do the travel documents last until the trip, when to start a renewal, what changes if the lead time is longer, which contract to review, is there still time to give notice, who holds a key and who handles the renewals. "
        "The contacts directory keeps trades, the school, the carpool family and the neighbour with the last time used and the cost line of the last job; the emergency sheet and the one-page sitter sheet print from the same numbers. No health details, ever.\n\n"
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to the household, the sitter, the school, the neighbour and the trades.\n\n"
        "This is part seven of the eight-part Home Management suite. A standard .xlsx workbook with no macros, no accounts and no yearly renewal, with a demo copy full of sample data and a blank copy. Dates and totals are calculated from your entries and are not advice."),
    "features": ["Action date counted back from every expiry with a typed lead time", "One ranked list of everything due in the next 90 days", "Travel documents checked against the trip date", "Contacts with last used and the cost line of the last job",
                 "One-page sitter sheet and emergency contacts page", "Key and access list with who holds what", f"{len(tools)} tools for the questions of every month", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "No macros, no accounts, no yearly renewal"]}
lists = lists_base + verdict_lists()
assert len(lists) <= 20, len(lists)
s = spec(id=f'{SUITE}-p7', slug='home-management-documents', profession='Home Management', name='Documents, Contacts and Renewals',
         tagline='Track every paper, contact and renewal date of your home and know when to start', price_usd=29,
         colors={"primary": "#3E5C76", "accent": "#E07A5F"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 7, "of": 8, "focus": "Documents, contacts and renewals"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ho7.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'lists', len(lists), 'desc', len(listing['description']), 'title', len(listing['title']))
