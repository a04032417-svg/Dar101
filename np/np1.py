"""Nonprofit Organization suite - part 1: Donor Book and Gift Log."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np1_lists import *
from np1_tables import settings, tables, MS, Y0F, ONE, DUE, OVERD, PAIDS, OPENP, BANKED, ACTIVE, FAILED, EXPECTED, REQUESTED, RECEIVED, NOTREC
from np1_tools import tools, R, MED90
import np1_data as D

SUITE = 'fx-20261115-nonprofit'
NOTE = "Sample wording: adapt it to your own organization and check your local rules."
YES = '{list:yesno.yes}'
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c_): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c_, t, idc)

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('gift_entry_sheet', 'Gift Entry Sheet', 'Gift with its checks', 'gifts.gift_id', F(
        ('Date', 'gifts.date'), ('Donor ID', 'gifts.donor_id'), ('Donor', 'gifts.donor'), ('Amount', 'gifts.amount'), ('Fund', 'gifts.fund'), ('Campaign', 'gifts.campaign'), ('Appeal', 'gifts.appeal'),
        ('Channel', 'gifts.channel'), ('Method', 'gifts.method'), ('Gift type', 'gifts.gift_type'), ('Batch ID', 'gifts.batch_id'), ('Check', 'gifts.check')) + [
        FF('Thank-you due by', 'WORKDAY(%s,{set:thankyou_days})' % LK('gifts', 'gift_id', 'date'), 'date'), FF('Written letter needed', 'IF(%s>{set:ack_over},{list:cka.letter_needed},{list:cka.note_enough})' % LK('gifts', 'gift_id', 'amount'), 'text')]),
    FORM('pledge_sheet', 'Pledge Sheet', 'Pledge with its schedule', 'pledges.pledge_id', F(
        ('Donor', 'pledges.donor'), ('Pledged on', 'pledges.pledged_on'), ('Total', 'pledges.total'), ('Instalments', 'pledges.instalments'), ('Every months', 'pledges.every_months'), ('Fund', 'pledges.fund'), ('Status', 'pledges.status'),
        ('Paid', 'pledges.paid'), ('Balance', 'pledges.balance'), ('Next due', 'pledges.next_due'), ('Action', 'pledges.action')) + [
        FF('Amount of one instalment', 'ROUND(%s/%s,2)' % (LK('pledges', 'pledge_id', 'total'), LK('pledges', 'pledge_id', 'instalments')), 'money'), FF('Share paid', 'IFERROR(%s/%s,0)' % (LK('pledges', 'pledge_id', 'paid'), LK('pledges', 'pledge_id', 'total')), 'pct')]),
    FORM('pledge_payment_sheet', 'Pledge Payment Sheet', 'One pledge instalment', 'instalments.pp_id', F(
        ('Pledge ID', 'instalments.pledge_id'), ('Donor', 'instalments.donor'), ('Instalment number', 'instalments.seq'), ('Due date', 'instalments.due_date'), ('Amount due', 'instalments.amount_due'), ('Paid on', 'instalments.paid_on'),
        ('Amount paid', 'instalments.amount_paid'), ('Status', 'instalments.status'), ('Action', 'instalments.action')) + [
        FF('Still to pay on this instalment', 'MAX(0,%s-%s)' % (LK('instalments', 'pp_id', 'amount_due'), LK('instalments', 'pp_id', 'amount_paid')), 'money'), FF('Days between due date and payment', '%s-%s' % (LK('instalments', 'pp_id', 'paid_on'), LK('instalments', 'pp_id', 'due_date')), 'int')]),
    FORM('recurring_gift_sheet', 'Recurring Gift Sheet', 'Monthly donor with the plan', 'recurring.recurring_id', F(
        ('Donor', 'recurring.donor'), ('Monthly amount', 'recurring.amount'), ('Start date', 'recurring.start_date'), ('Day of the month', 'recurring.day'), ('Channel', 'recurring.channel'), ('Fund', 'recurring.fund'), ('Status', 'recurring.status'),
        ('Last received', 'recurring.last_received'), ('Missed', 'recurring.missed')) + [
        FF('Yearly value', '12*%s' % LK('recurring', 'recurring_id', 'amount'), 'money'), FF('Months on the plan', 'DATEDIF(%s,{today},"M")' % LK('recurring', 'recurring_id', 'start_date'), 'int')]),
    FORM('failed_payment_sheet', 'Failed Payment Follow-up Sheet', 'Failed or missed monthly gift', 'recurring.recurring_id', F(
        ('Donor', 'recurring.donor'), ('Donor contact', 'recurring.contact'), ('Monthly amount', 'recurring.amount'), ('Status', 'recurring.status'), ('Last received', 'recurring.last_received'), ('Missed', 'recurring.missed'), ('Action', 'recurring.action')) + [
        FF('Months since the last gift', 'DATEDIF(%s,{today},"M")' % LK('recurring', 'recurring_id', 'last_received'), 'int'), FF('Amount missed so far', '%s*%s' % (LK('recurring', 'recurring_id', 'amount'), LK('recurring', 'recurring_id', 'missed')), 'money'),
        FF('Missed gifts before you contact', '{set:missed_contact}', 'int')]),
    FORM('inkind_sheet', 'In-kind Gift Sheet', 'In-kind gift with its value', 'inkind.inkind_id', F(
        ('Date', 'inkind.date'), ('Donor', 'inkind.donor'), ('Kind', 'inkind.kind'), ('Item', 'inkind.item'), ('Quantity', 'inkind.qty'), ('Fair value', 'inkind.fair_value'), ('Value basis', 'inkind.value_basis'),
        ('Value check', 'inkind.basis_check'), ('Thank-you sent', 'inkind.ack_sent')) + [
        FF('Value of one', 'ROUND(%s/MAX(1,%s),2)' % (LK('inkind', 'inkind_id', 'fair_value'), LK('inkind', 'inkind_id', 'qty')), 'money'), FF('In-kind value this year', 'SUMIFS({range:inkind.fair_value},{range:inkind.date},">="&%s)' % Y0F, 'money')]),
    FORM('match_request_sheet', 'Matching Gift Request Sheet', 'Matching gift request', 'matching.match_id', F(
        ('Donor', 'matching.donor'), ('Employer', 'matching.employer'), ('Ratio', 'matching.ratio'), ('Expected', 'matching.expected'), ('Requested on', 'matching.requested_on'), ('Status', 'matching.status'), ('Next step', 'matching.next_step')) + [
        FF('Donor gift behind the match', 'IFERROR(%s/%s,0)' % (LK('matching', 'match_id', 'expected'), LK('matching', 'match_id', 'ratio')), 'money'), FF('Days since the request', '{today}-%s' % LK('matching', 'match_id', 'requested_on'), 'int'),
        FF('Chase after days', '{set:match_chase_days}', 'int')]),
    FORM('donor_record_sheet', 'Donor Record Sheet', 'Donor record', 'donors.donor_id', F(
        ('Donor', 'donors.donor'), ('Type', 'donors.type'), ('Contact person', 'donors.contact'), ('Phone', 'donors.phone'), ('E-mail', 'donors.email'), ('Contact preference', 'donors.contact_pref'), ('Status', 'donors.status'),
        ('First gift', 'donors.first_gift'), ('Last gift', 'donors.last_gift'), ('Gifts', 'donors.gifts'), ('Total given', 'donors.total_given'), ('Giving state', 'donors.giving_state')) + [
        FF('Average gift', 'IFERROR(%s/%s,0)' % (LK('donors', 'donor_id', 'total_given'), LK('donors', 'donor_id', 'gifts')), 'money')]),
    FORM('duplicate_merge_sheet', 'Duplicate Merge Sheet', 'Two records of one donor', 'duplicates.donor_id', F(
        ('Donor', 'duplicates.donor'), ('E-mail', 'duplicates.email'), ('Records with the same name', 'duplicates.same_name'), ('Records with the same e-mail and type', 'duplicates.same_email'), ('First record', 'duplicates.keep_id'),
        ('Gift pairs on the same day', 'duplicates.gift_pairs'), ('Gifts on this record', 'duplicates.records_gifts'), ('Verdict', 'duplicates.flag'), ('Found on', 'duplicates.found_on')) + [
        FF('Move the gifts to', 'IF(%s="","keep",%s)' % (LK('duplicates', 'donor_id', 'merge_into'), LK('duplicates', 'donor_id', 'merge_into')) if False else LK('duplicates', 'donor_id', 'keep_id'), 'text')]),
    FORM('banking_batch_sheet', 'Banking Batch Sheet', 'Weekly banking batch', 'batches.batch_id', F(
        ('Week start', 'batches.week_start'), ('Gifts', 'batches.gift_count'), ('Logged amount', 'batches.logged_amount'), ('Banked on', 'batches.banked_on'), ('Banked amount', 'batches.banked_amount'), ('Status', 'batches.status'),
        ('Banked less logged', 'batches.gap'), ('Tie-out', 'batches.check')) + [
        FF('Gap you accept', '{set:bank_tolerance}', 'money'), FF('Days from week start to bank', '%s-%s' % (LK('batches', 'batch_id', 'banked_on'), LK('batches', 'batch_id', 'week_start')), 'int')]),
    FORM('ack_log_sheet', 'Acknowledgement Log Sheet', 'Thank-you and letter record', 'gifts.gift_id', F(
        ('Donor', 'gifts.donor'), ('Donor contact', 'gifts.contact'), ('Gift date', 'gifts.date'), ('Amount', 'gifts.amount'), ('Thank-you sent', 'gifts.ack_sent'), ('Days to thank', 'gifts.days_to_thank'), ('Thanked on time', 'gifts.thank_ok')) + [
        FF('Letter amount, your rule', '{set:ack_over}', 'money'), FF('Written letter needed', 'IF(%s>{set:ack_over},{list:cka.letter_needed},{list:cka.note_enough})' % LK('gifts', 'gift_id', 'amount'), 'text'),
        FF('Working days you allow', '{set:thankyou_days}', 'int')]),
    FORM('statement_request', 'Year-end Statement Request', 'Yearly statement of one donor', 'giving_years.donor_id', F(
        ('Donor', 'giving_years.donor'), ('Donor contact', 'giving_years.contact'), ('Statement year', 'giving_years.year'), ('Statement total', 'giving_years.statement_total'), ('Gifts in the year', 'giving_years.gifts'),
        ('Gifts missing a fund', 'giving_years.missing_fund'), ('This year', 'giving_years.this_year'), ('Last year', 'giving_years.last_year'), ('Statement flag', 'giving_years.flag')) + [
        FF('Change on last year', 'IFERROR(%s/%s-1,0)' % (LK('giving_years', 'donor_id', 'this_year'), LK('giving_years', 'donor_id', 'last_year')), 'pct')],
        {"from": "gifts", "match": "gifts.donor_id", "columns": ["date", "amount", "fund", "campaign", "method"], "max": 40}),
]
assert len(forms) == 12
forms[8]['fields'][-1] = FF('Move the gifts to', LK('duplicates', 'donor_id', 'keep_id'), 'text')

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('thankyou_letter', 'Thank-you Letter', 'Thank-you letter for a gift', 'gifts.gift_id', [
        '{set:org}, dated {today}. Dear {col:gifts.contact},',
        'Thank you for your gift of {col:gifts.amount} on {col:gifts.date} to {col:gifts.fund}. It was recorded as gift {col:gifts.gift_id} in our gift log.',
        'Your gift helps us keep our programs running for the people in our community. We are grateful that you chose to support us.',
        'This letter is a record of your gift that you can keep. Check with your accountant what your own rules need.'], ['Executive director', 'Donor'], NOTE),
    DOC('written_ack', 'Written Acknowledgement', 'Written acknowledgement for a larger gift', 'gifts.gift_id', [
        '{set:org}, dated {today}. Written acknowledgement of gift {col:gifts.gift_id}.',
        'We received {col:gifts.amount} from {col:gifts.donor} on {col:gifts.date} by {col:gifts.method}, given to {col:gifts.fund}.',
        'We give written acknowledgements for gifts above {set:ack_over}. This is a record of the gift you can keep. Check with your accountant what your own rules need.',
        'Thank you for standing with us.'], ['Executive director', 'Donor'], NOTE),
    DOC('giving_statement', 'Year-end Giving Statement', 'Year-end giving statement of one donor', 'giving_years.donor_id', [
        '{set:org}, dated {today}. Giving statement for {col:giving_years.donor}, year {col:giving_years.year}.',
        'Gifts in the year: {col:giving_years.gifts}. Total given in the year: {col:giving_years.statement_total}. The gifts are listed by date on the request sheet for this donor.',
        'This statement is a record of your gifts that you can keep. Please ask your accountant what your own rules need. Tell us if a gift is missing or wrong.',
        'Thank you for your support this year.'], ['Bookkeeper', 'Donor'], NOTE),
    DOC('statement_cover', 'Statement Cover Note', 'Cover note for a giving statement', 'giving_years.donor_id', [
        '{set:org}, dated {today}. Dear {col:giving_years.contact},',
        'Enclosed is your giving statement for {col:giving_years.year}. It shows {col:giving_years.gifts} gifts with a total of {col:giving_years.statement_total}.',
        'If anything looks wrong or a gift is missing, please tell us and we will correct it. Thank you for giving.'], ['Development manager'], NOTE),
    DOC('pledge_confirmation', 'Pledge Confirmation', 'Pledge confirmation letter', 'pledges.pledge_id', [
        '{set:org}, dated {today}. Dear {col:pledges.contact},',
        'Thank you for your pledge, a promise to give, paid in instalments. Pledge {col:pledges.pledge_id} was made on {col:pledges.pledged_on} for a total of {col:pledges.total}, in {col:pledges.instalments} instalments, one every {col:pledges.every_months} months.',
        'Your next instalment is due on {col:pledges.next_due}. So far {col:pledges.paid} has been paid and the balance is {col:pledges.balance}.',
        'Please tell us if you need to change the dates.'], ['Development manager', 'Donor'], NOTE),
    DOC('pledge_reminder', 'Pledge Reminder', 'Pledge reminder letter', 'instalments.pp_id', [
        '{set:org}, dated {today}. Dear {col:instalments.contact},',
        'This is a friendly reminder about instalment {col:instalments.pp_id} of your pledge {col:instalments.pledge_id}. An amount of {col:instalments.amount_due} was due on {col:instalments.due_date}.',
        'It is now {col:instalments.days_overdue} days past the due date. If you have already paid, thank you and please ignore this note. If you would like a new date, please tell us.'], ['Development manager', 'Donor'], NOTE),
    DOC('pledge_final', 'Final Pledge Notice', 'Final pledge notice', 'instalments.pp_id', [
        '{set:org}, dated {today}. Dear {col:instalments.contact},',
        'This is a final notice about instalment {col:instalments.pp_id} of pledge {col:instalments.pledge_id}. The amount of {col:instalments.amount_due} was due on {col:instalments.due_date} and is {col:instalments.days_overdue} days late.',
        'If we do not hear from you, we will propose to close the pledge at the amount paid so far. The proposal date is {col:instalments.writeoff_on}. Please contact us before then.'], ['Executive director', 'Donor'], NOTE),
    DOC('recurring_welcome', 'Monthly Giving Welcome', 'Welcome note for a monthly donor', 'recurring.recurring_id', [
        '{set:org}, dated {today}. Dear {col:recurring.contact},',
        'Welcome, and thank you for giving every month. Your monthly gift of {col:recurring.amount} starts on {col:recurring.start_date} and is taken on day {col:recurring.day} of each month, for {col:recurring.fund}.',
        'You can pause or stop at any time by telling us. A record of each gift is kept in our gift log.'], ['Development manager', 'Donor'], NOTE),
    DOC('failed_payment_note', 'Failed Payment Note', 'Note about a failed monthly gift', 'recurring.recurring_id', [
        '{set:org}, dated {today}. Dear {col:recurring.contact},',
        'Your monthly gift of {col:recurring.amount} did not go through. The last gift we received was on {col:recurring.last_received}, and {col:recurring.missed} gift(s) have been missed since.',
        'Please update your payment details or tell us if you would like to pause. We are happy to help.'], ['Development manager', 'Donor'], NOTE),
    DOC('inkind_record', 'In-kind Gift Record', 'Record of an in-kind gift', 'inkind.inkind_id', [
        '{set:org}, dated {today}. Record of in-kind gift {col:inkind.inkind_id} from {col:inkind.donor}, received on {col:inkind.date}.',
        'Item: {col:inkind.item}. Kind: {col:inkind.kind}. Quantity: {col:inkind.qty}. Value entered: {col:inkind.fair_value}. Value set by: {col:inkind.value_basis}.',
        'We record the value as entered above and do not set a value for you. This is a record of the gift you can keep. Check with your accountant what your own rules need.'], ['Executive director', 'Donor'], NOTE),
    DOC('match_request_letter', 'Matching Gift Request', 'Matching gift request to an employer', 'matching.match_id', [
        '{set:org}, dated {today}. To {col:matching.employer},',
        'Your employee {col:matching.donor} gave {col:matching.gift_amount} to our organization. We understand your matching program can add money to a gift. At a ratio of {col:matching.ratio}, the expected match is {col:matching.expected}.',
        'Please tell us what you need from us to process the match, and where to send it. Thank you for supporting our community.'], ['Development manager'], NOTE),
    DOC('weekly_banking', 'Weekly Banking Summary', 'Weekly banking summary', 'batches.batch_id', [
        '{set:org}, dated {today}. Banking summary for batch {col:batches.batch_id}, week starting {col:batches.week_start}.',
        'Gifts logged: {col:batches.gift_count}. Amount logged: {col:batches.logged_amount}. Amount banked: {col:batches.banked_amount} on {col:batches.banked_on}. Banked less logged: {col:batches.gap}. Tie-out: {col:batches.check}.',
        'Gaps above {set:bank_tolerance} are checked against the bank slip before the batch is closed.'], ['Bookkeeper', 'Executive director'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('daily_gift_entry', 'Daily Gift Entry', 'gifts', 'gifts.date', [('Enter the gift with donor, fund, campaign and channel', 0), ('Check the Check column for a missing donor or fund', 0), ('Add the gift to the weekly batch', 1), ('Send the thank-you', 2)]),
    CHK('weekly_banking', 'Banking Tie-out Steps', 'batches', 'batches.week_start', [('Total the gifts logged for the week', 5), ('Compare with the bank slip', 7), ('Fix or explain any gap above the allowed amount', 9), ('Close the batch and tell the board chair', 10)]),
    CHK('thankyou_clearout', 'Thank-you Clear-out', 'gifts', 'gifts.date', [('Open the Thank-you Backlog', 0), ('Write letters for gifts above the letter amount', 1), ('Send notes for the other gifts', 2), ('Mark each gift as thanked', 3)]),
    CHK('monthly_summary', 'Monthly Gift Summary', 'gift_months', 'gift_months.month', [('Close the last gift batch of the month', 30), ('Check gifts missing a donor or fund', 31), ('Review the Gift Summary by Month', 33), ('Send gift totals to the accountant', 35)]),
    CHK('statements_run', 'Year-end Statements Run', 'campaigns', 'campaigns.end_date', [('Fix gifts missing a fund', 5), ('Check the Statement Batch List', 10), ('Print the statements and cover notes', 14), ('Send them and note the date', 20), ('Ask your accountant what your rules need', 25)]),
    CHK('pledge_followup', 'Pledge Follow-up', 'instalments', 'instalments.due_date', [('Send a reminder on the due date', 0), ('Call after the chase days', 30), ('Send a final notice', 90), ('Propose a write-off to the board', 180)]),
    CHK('recurring_followup', 'Recurring Failure Follow-up', 'recurring', 'recurring.last_received', [('Check the payment status', 32), ('Contact the donor', 35), ('Update the details and record the next gift', 45), ('Pause or stop if no answer', 75)]),
    CHK('inkind_handling', 'In-kind Gift Handling', 'inkind', 'inkind.date', [('Record item, quantity and who set the value', 0), ('Ask the donor to confirm the value', 3), ('Send the thank-you and record', 5), ('Give the totals to the accountant at year end', 60)]),
    CHK('match_chase', 'Matching Gift Chase', 'matching', 'matching.requested_on', [('Send the request to the employer', 0), ('Check for a reply', 21), ('Chase by phone', 45), ('Thank the employer when it arrives', 60)]),
    CHK('duplicate_check', 'Duplicate Check', 'duplicates', 'duplicates.found_on', [('Compare e-mail, name and type', 0), ('Decide merge or keep both', 2), ('Move the gifts to the first record', 3), ('Tell the donor if the contact changes', 7)]),
    CHK('new_donor', 'New Donor Record', 'donors', 'donors.first_gift', [('Enter name, type and contact person', 0), ('Pick the contact preference', 0), ('Send the thank-you', 2), ('Add to the next appeal list', 30)]),
    CHK('founder_first_week', 'Founder First Gift Week', 'gifts', 'gifts.date', [('Use one fund and a short donor list', 0), ('Enter every gift the day it arrives', 0), ('Thank each donor within the week', 5), ('Bank the gifts and compare with the slip', 7)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(key_, moment, table, phone, text): return MSG(key_, moment, table, phone, text)
messages = [
    M('m_thanks', 'Donor: thank you for your gift', 'gifts', 'gifts.phone', 'Hello {contact}, thank you for your gift of {amount} on {date}. {org}'),
    M('m_recorded', 'Donor: gift recorded to a fund', 'gifts', 'gifts.phone', 'Hello {contact}, your gift of {amount} was recorded to {fund}. {org}'),
    M('m_ack', 'Donor: written acknowledgement', 'gifts', 'gifts.phone', 'Hello {contact}, your gift of {amount} on {date} is acknowledged in writing. Please keep this message as your record. {org}'),
    M('m_statement', 'Donor: yearly statement is ready', 'giving_years', 'giving_years.phone', 'Hello {contact}, your giving statement for {year} is ready. Total {statement_total}. {org}'),
    M('m_statement_gifts', 'Donor: check your statement', 'giving_years', 'giving_years.phone', 'Hello {contact}, your statement for {year} shows {gifts} gifts. Please tell us if anything is missing. {org}'),
    M('m_monthly_thanks', 'Donor: thank you for monthly gift', 'recurring', 'recurring.phone', 'Hello {contact}, thank you for your monthly gift of {amount}. {org}'),
    M('m_welcome_monthly', 'Donor: welcome as a monthly donor', 'recurring', 'recurring.phone', 'Hello {contact}, welcome as a monthly donor. Your first gift of {amount} is on {start_date}. {org}'),
    M('m_failed', 'Donor: monthly gift failed', 'recurring', 'recurring.phone', 'Hello {contact}, your monthly gift of {amount} did not go through. Please update your details or tell us if we can help. {org}'),
    M('m_missed', 'Donor: monthly gift missed', 'recurring', 'recurring.phone', 'Hello {contact}, we missed your monthly gift of {amount}. The last one we received was on {last_received}. Can we help? {org}'),
    M('m_pledge_rec', 'Donor: pledge recorded', 'pledges', 'pledges.phone', 'Hello {contact}, your pledge of {total} is recorded with {instalments} instalments. Thank you. {org}'),
    M('m_pledge_due', 'Donor: instalment was due', 'instalments', 'instalments.phone', 'Hello {contact}, your pledge instalment of {amount_due} was due on {due_date}. Please tell us when we can expect it. {org}'),
    M('m_pledge_late', 'Donor: instalment is late', 'instalments', 'instalments.phone', 'Hello {contact}, your pledge instalment of {amount_due} is {days_overdue} days late. Can we agree a new date? {org}'),
    M('m_pledge_final', 'Donor: final pledge reminder', 'pledges', 'pledges.phone', 'Hello {contact}, this is a final reminder for your pledge balance of {balance}. Please get in touch. {org}'),
    M('m_pledge_close', 'Donor: propose to close a pledge', 'pledges', 'pledges.phone', 'Hello {contact}, we propose to close your pledge at {paid} given so far. Please tell us if you disagree. {org}'),
    M('m_inkind_thanks', 'Donor: thank you for in-kind gift', 'inkind', 'inkind.phone', 'Hello {contact}, thank you for your gift of {item}. We recorded it at {fair_value}. {org}'),
    M('m_inkind_value', 'Donor: confirm the value', 'inkind', 'inkind.phone', 'Hello {contact}, please confirm the value of your gift of {item}. We have {fair_value}. {org}'),
    M('m_match_ask', 'Donor: ask about employer match', 'matching', 'matching.phone', 'Hello {contact}, your employer {employer} may match your gift of {gift_amount}. Please tell us if you would like us to ask them. {org}'),
    M('m_match_request', 'Employer: matching gift request', 'matching', 'matching.employer_phone', 'Hello {employer}, we request the matching gift for {donor}, {gift_amount} given on {requested_on}. Expected match {expected}. {org}'),
    M('m_match_remind', 'Employer: reminder, match still open', 'matching', 'matching.employer_phone', 'Hello {employer}, a reminder: the match of {expected} for {donor} is still open. {org}'),
    M('m_match_thanks', 'Employer: thank you for the match', 'matching', 'matching.employer_phone', 'Hello {employer}, thank you for the matching gift of {received} for {donor}. {org}'),
    M('m_merge', 'Donor: may we merge two records', 'duplicates', 'duplicates.phone', 'Hello {contact}, we have two records under your name. May we merge them? {org}'),
    M('m_confirm_details', 'Donor: confirm contact details', 'donors', 'donors.phone', 'Hello {contact}, please confirm that your contact details are right. {org}'),
    M('m_pref', 'Donor: contact preference updated', 'donors', 'donors.phone', 'Hello {contact}, we updated your contact preference to {contact_pref}. {org}'),
    M('m_household', 'Household: contacts listed', 'households', 'households.phone', 'Hello {contact}, we now list {contacts} contacts under {donor}. Please tell us if that is wrong. {org}'),
    M('m_board_bank', 'Board member: weekly banking summary', 'batches', 'batches.board_phone', 'Banking summary for the week of {week_start}: logged {logged_amount}, banked {banked_amount}. {org}'),
    M('m_book_off', 'Bookkeeper: batch is off', 'batches', 'batches.bookkeeper_phone', 'Batch {batch_id}, week of {week_start}, is off by {gap}. Please check the bank slip. {org}'),
    M('m_book_fund', 'Bookkeeper: gifts to a fund', 'gifts', 'gifts.bookkeeper_phone', 'Gifts to {fund} this month total {fund_month_total}. {org}'),
    M('m_book_missing', 'Bookkeeper: gift needs a fix', 'gift_checks', 'gift_checks.bookkeeper_phone', 'Gift {gift_id} of {amount} needs a fix: {fix}. {org}'),
    M('m_dev_thanks', 'Development manager: thank-yous overdue', 'thankyou', 'thankyou.dev_phone', '{over_n} thank-yous are overdue. The oldest has waited {oldest_days} days. {org}'),
    M('m_dev_pledges', 'Development manager: pledges late', 'instalments', 'instalments.dev_phone', '{over_count} pledge instalments are over {limit_days} days late. This one: {donor}, {days_overdue} days. {org}'),
    M('m_dev_recurring', 'Development manager: recurring income', 'recurring_months', 'recurring_months.dev_phone', 'Recurring income for {month} is {recurring_amount}. {org}'),
    M('m_acc_totals', 'Accountant: gift totals are ready', 'gift_months', 'gift_months.accountant_phone', 'Gift totals for {month} are ready: {gifts} gifts, {amount}. {org}'),
    M('m_acc_inkind', 'Accountant: in-kind total', 'inkind', 'inkind.accountant_phone', 'In-kind gifts for the year total {year_value}. {org}'),
    M('m_volunteer', 'Volunteer: thank-you card session', 'thankyou', 'thankyou.volunteer_phone', 'Hello, please help with the thank-you card session on {session_date}. {org}'),
]
assert len(messages) == 34

# ------------------------------------------------------------------ dashboard
AMT = lambda col: 'SUMIFS({range:gifts.amount},%s)' % col
D90 = '{range:gifts.date},">="&({today}-90)'
D30 = '{range:gifts.date},">="&({today}-30)'
kpis = [
    KPI('Gifts this month', 'COUNTIFS({range:gifts.month},%s)' % MS, 'int'),
    KPI('Gift amount this month', AMT('{range:gifts.month},%s' % MS), 'money'),
    KPI('Gifts last 30 days', 'COUNTIFS(%s)' % D30, 'int'),
    KPI('Gift amount last 30 days', AMT(D30), 'money'),
    KPI('Donors giving this month', 'COUNTIFS({range:donors.last_gift},">="&%s)' % MS, 'int'),
    KPI('Average gift last 90 days', 'IFERROR(AVERAGEIFS({range:gifts.amount},%s),0)' % D90, 'money'),
    KPI('Median gift last 90 days', MED90, 'money'),
    KPI('Gifts waiting for a thank-you', 'COUNTIFS({range:gifts.days_waiting},">=0")', 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Oldest wait for a thank-you, days', 'MAX({range:gifts.days_waiting})', 'int'),
    KPI('Large gifts without a letter', 'COUNTIFS({range:gifts.letter_due},1)', 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Gifts missing a donor', 'COUNTIFS({range:gifts.issue},1)', 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Gifts missing a fund', 'COUNTIFS({range:gifts.issue},2)', 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Possible duplicate gifts', 'COUNTIFS({range:gifts.issue},3)', 'int'),
    KPI('Batches off, last 12 months', 'COUNTIFS({range:batches.off},1,{range:batches.week_start},">="&({today}-365))', 'int'),
    KPI('Logged less banked, last 90 days', 'SUMIFS({range:batches.logged_amount},{range:batches.status},%s,{range:batches.week_start},">="&({today}-90))-SUMIFS({range:batches.banked_amount},{range:batches.status},%s,{range:batches.week_start},">="&({today}-90))' % (BANKED, BANKED), 'money'),
    KPI('Open pledge balance', 'SUMIFS({range:pledges.balance},{range:pledges.status},%s)' % OPENP, 'money'),
    KPI('Pledge instalments overdue now', 'COUNTIFS({range:instalments.days_overdue},">0")', 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Pledge amount overdue now', 'SUMIFS({range:instalments.amount_due},{range:instalments.days_overdue},">0")', 'money'),
    KPI('Instalments due, next 90 days', 'SUMIFS({range:instalments.amount_due},{range:instalments.status},%s,{range:instalments.due_date},">="&{today},{range:instalments.due_date},"<="&({today}+90))' % DUE, 'money'),
    KPI('Write-off dates within 120 days', 'COUNTIFS({range:instalments.writeoff_on},">="&{today},{range:instalments.writeoff_on},"<="&({today}+120))', 'int'),
    KPI('Recurring donors active', 'COUNTIFS({range:recurring.status},%s)' % ACTIVE, 'int'),
    KPI('Monthly recurring income', 'SUMIFS({range:recurring.amount},{range:recurring.status},%s)' % ACTIVE, 'money'),
    KPI('Recurring share of gift amount, 90 days', 'IFERROR(SUMIFS({range:gifts.amount},{range:gifts.gift_type},%s,%s)/SUMIFS({range:gifts.amount},%s),0)' % (tok('gtype', 'Recurring'), D90, D90), 'pct'),
    KPI('Annualised recurring value', '12*SUMIFS({range:recurring.amount},{range:recurring.status},%s)' % ACTIVE, 'money'),
    KPI('Failed or missed recurring now', 'COUNTIFS({range:recurring.needs},1)', 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('In-kind gifts this year', 'COUNTIFS({range:inkind.date},">="&%s)' % Y0F, 'int'),
    KPI('In-kind value this year', 'SUMIFS({range:inkind.fair_value},{range:inkind.date},">="&%s)' % Y0F, 'money'),
    KPI('Matching gifts expected, not received', 'COUNTIFS({range:matching.open},1)', 'int'),
    KPI('Match amount to chase', 'SUMIFS({range:matching.expected},{range:matching.chase},1)', 'money'),
    KPI('Possible duplicate donors', 'COUNTIFS({range:donors.dup_extra},1)', 'int'),
]
assert len(kpis) == 30
dashboard = {"title": "Gift Dashboard", "kpis": kpis,
    "monthly": {"title": "Gift amount, recurring and restricted", "date": "gift_months.month", "series": [
        {"label": "Gift amount", "sum": "gift_months.amount", "date": "gift_months.month"}, {"label": "Recurring", "sum": "gift_months.recurring_amount", "date": "gift_months.month"},
        {"label": "Restricted", "sum": "gift_months.restricted_amount", "date": "gift_months.month"}]},
    "breakdowns": [{"title": "Gift amount by fund, this year", "by": "gifts.fund", "value": "gifts.amount", "agg": "sum"}, {"title": "Pledge amount due by status", "by": "instalments.status", "value": "instalments.amount_due", "agg": "sum"},
                   {"title": "Recurring donors by status", "by": "recurring.status", "agg": "count"}, {"title": "Matching gifts expected by status", "by": "matching.status", "value": "matching.expected", "agg": "sum"}]}
insights = {"filters": [{"label": "Fund", "list": "fund"}, {"label": "Channel", "list": "channel"}, {"label": "Campaign", "list": "campaign"}],
    "gauges": [
        {"title": "Gifts thanked on time", "num": AGG('count', 'gifts', where=[('thank_ok', '=', 1)]), "den": AGG('count', 'gifts', where=[('thank_ok', '>=', 0)])},
        {"title": "Gifts with donor and fund filled", "num": AGG('count', 'gifts', where=[('filled', '=', 1)]), "den": AGG('count', 'gifts', where=[('filled', '>=', 0)])},
        {"title": "Banked against logged", "num": AGG('sum', 'batches', 'batches.banked_amount', where=[('status', '=', BANKED)]), "den": AGG('sum', 'batches', 'batches.logged_amount', where=[('status', '=', BANKED)])},
        {"title": "Pledge money collected", "num": AGG('sum', 'instalments', 'instalments.amount_paid', where=[('due_date', '<=', '{today}')]), "den": AGG('sum', 'instalments', 'instalments.amount_due', where=[('due_date', '<=', '{today}')])},
        {"title": "Recurring gifts received on time", "num": AGG('count', 'recurring', where=[('status', '=', ACTIVE), ('missed', '=', 0)]), "den": AGG('count', 'recurring', where=[('status', '=', ACTIVE)])},
        {"title": "Matching gifts received", "num": AGG('count', 'matching', where=[('status', '=', RECEIVED)]), "den": AGG('count', 'matching', where=[('status', '<>', tok('mstatus', 'Declined'))])}],
    "charts": [
        CHART('Gift amount per month', 'column', 'month', [AGG('sum', 'gift_months', 'gift_months.amount', date='gift_months.month', label='Gift amount')]),
        CHART('Gifts per month', 'column', 'month', [AGG('sum', 'gift_months', 'gift_months.gifts', date='gift_months.month', label='Gifts')]),
        CHART('Gift amount by fund', 'bar', 'gifts.fund', [AGG('sum', 'gifts', 'gifts.amount', label='Gift amount')]),
        CHART('Gift amount by campaign', 'bar', 'gifts.campaign', [AGG('sum', 'gifts', 'gifts.amount', label='Gift amount')]),
        CHART('Gift amount by appeal', 'bar', 'gifts.appeal', [AGG('sum', 'gifts', 'gifts.amount', label='Gift amount')]),
        CHART('Gift amount by channel', 'bar', 'gifts.channel', [AGG('sum', 'gifts', 'gifts.amount', label='Gift amount')]),
        CHART('Gift amount by method', 'bar', 'gifts.method', [AGG('sum', 'gifts', 'gifts.amount', label='Gift amount')]),
        CHART('Gifts by gift type', 'bar', 'gifts.gift_type', [AGG('count', 'gifts', label='Gifts')]),
        CHART('Average gift per month', 'column', 'month', [AGG('sum', 'gift_months', 'gift_months.avg_gift', date='gift_months.month', label='Average gift')]),
        CHART('Restricted gift amount per month', 'column', 'month', [AGG('sum', 'gift_months', 'gift_months.restricted_amount', date='gift_months.month', label='Restricted')]),
        CHART('Gifts by weekday', 'bar', 'gifts.weekday', [AGG('count', 'gifts', label='Gifts')]),
        CHART('Days to thank per month', 'column', 'month', [AGG('sum', 'gift_months', 'gift_months.avg_wait', date='gift_months.month', label='Average days to thank')]),
        CHART('Logged and banked per month', 'column', 'month', [AGG('sum', 'batches', 'batches.logged_amount', date='batches.week_start', label='Logged'), AGG('sum', 'batches', 'batches.banked_amount', date='batches.week_start', label='Banked')]),
        CHART('Pledge amount due by month', 'column', 'month', [AGG('sum', 'instalments', 'instalments.amount_due', date='instalments.due_date', label='Amount due')]),
        CHART('Pledge instalments by status', 'bar', 'instalments.status', [AGG('count', 'instalments', label='Instalments')]),
        CHART('Recurring amount per month', 'column', 'month', [AGG('sum', 'recurring_months', 'recurring_months.recurring_amount', date='recurring_months.month', label='Recurring amount')]),
        CHART('Recurring donors by status', 'bar', 'recurring.status', [AGG('count', 'recurring', label='Recurring donors')]),
        CHART('In-kind value per month', 'column', 'month', [AGG('sum', 'inkind', 'inkind.fair_value', date='inkind.date', label='In-kind value')]),
        CHART('In-kind value by kind', 'bar', 'inkind.kind', [AGG('sum', 'inkind', 'inkind.fair_value', label='In-kind value')]),
        CHART('Matching received per month', 'column', 'month', [AGG('sum', 'matching', 'matching.received', date='matching.received_on', label='Received')]),
        CHART('Matching gifts by status', 'bar', 'matching.status', [AGG('count', 'matching', label='Matching gifts')]),
        CHART('Donors by type', 'bar', 'donors.type', [AGG('count', 'donors', label='Donors')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Thank-you backlog ranker", "why": "every gift without a thank-you ranked oldest first against your own working-day rule, with Send today or On time", "where": "Thank-you Backlog Ranker"},
    {"name": "Weekly banking tie-out", "why": "gifts logged against the bank slip batch by batch, with the batches off by more than the gap you accept", "where": "Weekly Banking Tie-out"},
    {"name": "Overdue pledge ranker", "why": "open instalments ranked by days overdue and amount, with chase, final notice and a write-off proposal date", "where": "Overdue Pledge Ranker"},
    {"name": "Year-end statement builder", "why": "one donor and one year: gifts, total, funds and a flag when a gift has no fund, as a record you can keep", "where": "Year-end Statement Builder"},
    {"name": "Failed payment chaser", "why": "monthly donors with a failed or missed gift ranked by amount, with Contact today or Wait one more cycle", "where": "Failed Payment Chaser"},
    {"name": "Match chase ranker", "why": "employer matches still open ranked by amount, with the biggest one to chase named", "where": "Match Chase Ranker"},
    {"name": "Duplicate donor finder", "why": "records with the same e-mail and type found, with a merge plan into the first record or keep both", "where": "Duplicate Donor Finder"},
    {"name": "Gift entry check", "why": "a new gift tested for donor, fund, duplicate and unusual size before you save it", "where": "Gift Entry Check"},
    {"name": "Recurring conversion planner", "why": "how many donors to ask to give monthly for the income you want, from your own yes rate", "where": "Recurring Conversion Planner"},
    {"name": "Data health score", "why": "a score for this month against your own last month, with the rows to fix", "where": "Data Health Score"}]
competitors = [
    {"what": "donor-management software", "lacks": "charges per contact every month and hides the banking tie-out, the pledge write-off dates and the checks behind a report you cannot change"},
    {"what": "generic donation log spreadsheets", "lacks": "list gifts but never check a missing donor or fund, a duplicate, a batch that is off or a thank-you that is late"},
    {"what": "single-purpose pledge trackers", "lacks": "hold instalments but have no chase, final notice and write-off steps, no recurring or matching gifts and no statements"},
    {"what": "nonprofit accounting add-ons", "lacks": "post totals to the books but give no thank-you backlog, no duplicate finder and no household view"}]
guide = [
    'Open Start and type your organization name, your thank-you days, your letter amount and your pledge chase days in the yellow cells. Replace demo data: clear the sample rows and type your own.',
    'Fill Funds, Campaigns and Appeals first. Funds are money given for one purpose or free money the board can use for anything in the mission.',
    'Enter every donor in Donors and add contact people for households and businesses in Donor Contacts.',
    'Log each gift in Gifts the day it arrives. The Check column shows a missing donor, a missing fund, a possible duplicate or a batch that is off.',
    'Group gifts into a weekly batch in Gift Batches and type the amount on the bank slip; the Weekly Banking Tie-out names the gaps.',
    'Open Thank-you Backlog every morning: it lists the gifts still without a thank-you, oldest first.',
    'Record each pledge in Pledges and its instalments in Pledge Instalments; the Overdue Pledge Ranker says chase, final notice or propose a write-off.',
    'Keep monthly donors in Recurring Donors; the Failed Payment Chaser ranks the ones to contact.',
    'Record in-kind gifts and matching gifts; the Match Chase List shows which employers to chase.',
    'Use Duplicate Finder and Household View to keep one record for each donor.',
    'Run the Statement Batch List and the Year-end Statement Builder once a year. A statement is a record of the gifts you can keep; ask your accountant what your rules need.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'This workbook has no macros and works in Excel and Google Sheets. A founder with volunteers and no staff can use the same sheets with one fund and a short donor list.',
    'Why a workbook: a flat price, no per-contact fee, no paid add-ons for grants or volunteers, and your data stays with you.',
    'What this is not: not a mass-email tool, not a payment service, and not accounting or legal advice.']
listing = {"title": "Nonprofit Donor Book and Gift Log Excel Template: Gifts, Thank-yous, Pledges, Recurring Donors, Matching Gifts, Statements",
    "headline": "Log every gift, thank every donor and chase every pledge in one workbook",
    "tags": ["nonprofit", "donor tracker", "gift log", "donation tracker", "pledge tracker", "charity excel", "fundraising", "thank you letter", "recurring donors", "matching gifts", "giving statement", "donor database", "excel template"],
    "description": ("Run the gift side of a small nonprofit in one Excel workbook. Built for an executive director, a development manager, a bookkeeper or a founder with volunteers who log gifts, thank donors, bank each week and follow up pledges. "
        "Gifts holds each gift with donor, fund, campaign, appeal, channel and method, and a Check column that finds a missing donor, a missing fund, a possible duplicate and a batch that is off. Gift Batches compares what you logged with the bank slip. Thank-you Backlog lists the gifts still waiting, oldest first.\n\n"
        "Pledges and Pledge Instalments track a promise to give, paid in instalments, with days overdue, chase, final notice and a write-off proposal date. Recurring Donors shows monthly gifts that failed or were missed. In-kind Gifts records goods or services given instead of money with who set the value. Matching Gifts tracks money an employer adds to a donor gift, with a chase list. "
        "Giving by Donor and Year, Donor Contacts, Duplicate Finder and Household View keep one clean record for each donor.\n\n"
        f"{len(tools)} tools answer weekly questions: which gifts need a thank-you, does the banking tie out, which pledges to chase, which statements are ready, which monthly donors to call and which employers to chase. Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to donors, employers, the bookkeeper, the accountant and your team.\n\n"
        "A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Donors appear as names, contact people, amounts and dates only. Statements and letters are records of gifts you can keep; ask your accountant what your own rules need. It helps you keep track and does not promise results. This is part one of the Nonprofit Organization suite."),
    "features": ["Gift log with a built-in check column", "Weekly banking tie-out", "Thank-you backlog, oldest first", "Pledge schedules with write-off dates", "Failed payment chaser for monthly donors",
                 "Matching gift chase list", "Duplicate donor finder with merge plan", "Year-end giving statements", f"{len(tools)} decision tools", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p1', slug='nonprofit-gifts', profession='Nonprofit Organization', name='Donor Book and Gift Log',
         tagline='Log every gift, thank every donor and chase every pledge in one workbook', price_usd=29,
         colors={"primary": "#22577A", "accent": "#F2A541"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 1, "of": 8, "focus": "Donor book and gift log"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'np1.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
