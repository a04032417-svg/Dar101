"""Author and Self-Publisher Business suite - part 2: Production Costs and Break-Even."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au2_lists import *
from au2_tables import settings, tables
from au2_tools import tools

NOTE = "Sample wording: adapt it to your own business. Confirm tax and contract points with your adviser."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
def LKS(t, idc, c): return 'IFERROR(%s&"","")' % LK(t, idc, c)
def LKJ(c): return LKS('jobs', 'job_id', c)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
PAID = tok('cpaystatus', 'Paid'); JPAID = tok('jstatus', 'Paid'); JDEL = tok('jstatus', 'Delivered'); JIP = tok('jstatus', 'In progress')
K_DEV, K_COPY, K_PROOF = tok('jobkind', 'Developmental edit'), tok('jobkind', 'Copy edit'), tok('jobkind', 'Proofread')
K_COVER, K_FMT, K_NAR, K_TR = tok('jobkind', 'Cover design'), tok('jobkind', 'Formatting'), tok('jobkind', 'Narration'), tok('jobkind', 'Translation')
PB_, ONT, BEH, NOS = ca('Paid back'), ca('On track'), ca('Behind'), ca('Not on sale yet')
CASHNOW = 'SUMIFS({range:cash_month.closing},{range:cash_month.month},%s)' % MS
OWN_KIND = 'IFERROR(ROUND(SUMIFS({range:jobs.quote},{range:jobs.kind},%s,{range:jobs.units},">0")/SUMIFS({range:jobs.units},{range:jobs.kind},%s),2),0)'
def JOBF(extra=()):
    return F(('Job', 'jobs.job_id'), ('Title', 'jobs.title'), ('Kind', 'jobs.kind'), ('Contractor', 'jobs.contractor'), ('Phone', 'jobs.phone')) + list(extra)

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('job_quote_sheet', 'Job Quote Sheet', 'Job quote against your typical rate', 'jobs.job_id', JOBF(F(('Quote', 'jobs.quote'), ('Units', 'jobs.units'), ('Unit rate', 'jobs.unit_rate'), ('Start date', 'jobs.start_date'), ('Due date', 'jobs.due_date'))) + [
        FF('Quote at your typical rate', 'IFERROR(%s,0)' % LK('budget', 'job_id', 'typical_quote'), 'money'), FF('Over (+) or under (-) the typical rate', 'IFERROR(%s,0)' % LK('budget', 'job_id', 'over_amount'), 'money'),
        FF('Own average per unit for this kind', OWN_KIND % (LK('jobs', 'job_id', 'kind'), LK('jobs', 'job_id', 'kind')), 'money')],
        {"from": "jobpay", "match": "jobpay.job_id", "columns": ["stage", "date", "amount", "status"], "max": 6}),
    FORM('job_brief_sheet', 'Job Brief Sheet', 'Job brief with release date and time left', 'jobs.job_id', JOBF(F(('Title words', 'jobs.words'), ('Start date', 'jobs.start_date'), ('Due date', 'jobs.due_date'))) + [
        FF('Series', LKS('titles', 'title_id', 'series').replace('{pick}', LK('jobs', 'job_id', 'title_id')), 'text'),
        FF('Release date', 'INDEX({range:titles.release_date},MATCH(%s,{range:titles.title_id},0))' % LK('jobs', 'job_id', 'title_id'), 'date'),
        FF('Days from the due date to the release', 'INDEX({range:titles.release_date},MATCH(%s,{range:titles.title_id},0))-%s' % (LK('jobs', 'job_id', 'title_id'), LK('jobs', 'job_id', 'due_date')), 'int')]),
    FORM('cover_brief_sheet', 'Cover Brief Sheet', 'Cover job with cost and the covers of the title', 'jobs.job_id', JOBF(F(('Quote', 'jobs.quote'), ('Start date', 'jobs.start_date'), ('Due date', 'jobs.due_date'), ('Status', 'jobs.status'))) + [
        FF('Typical rate for a cover', 'SUMIFS({range:cost_cat.rate},{range:cost_cat.kind},%s)' % K_COVER, 'money'),
        FF('Average cost of your covers', 'IFERROR(AVERAGEIFS({range:jobs.quote},{range:jobs.kind},%s),0)' % K_COVER, 'money'),
        FF('Cover jobs of this title', 'COUNTIFS({range:jobs.title},%s,{range:jobs.kind},%s)' % (LK('jobs', 'job_id', 'title'), K_COVER), 'int')]),
    FORM('editing_order_sheet', 'Editing Order Sheet', 'Editing order with words, rate and own average', 'jobs.job_id', JOBF(F(('Units, thousand words', 'jobs.units'), ('Unit rate', 'jobs.unit_rate'), ('Quote', 'jobs.quote'),
                                                                                   ('Start date', 'jobs.start_date'), ('Due date', 'jobs.due_date'), ('Balance', 'jobs.balance'))) + [
        FF('Own average per 1,000 words, this kind', OWN_KIND % (LK('jobs', 'job_id', 'kind'), LK('jobs', 'job_id', 'kind')), 'money'),
        FF('Editing jobs of this contractor', 'COUNTIFS({range:jobs.contractor},%s)' % LK('jobs', 'job_id', 'contractor'), 'int')]),
    FORM('narration_order_sheet', 'Narration Order Sheet', 'Narration order with finished hours and rate', 'jobs.job_id', JOBF(F(('Finished hours', 'jobs.units'), ('Rate per finished hour', 'jobs.unit_rate'), ('Quote', 'jobs.quote'),
                                                                                      ('Start date', 'jobs.start_date'), ('Due date', 'jobs.due_date'), ('Paid', 'jobs.paid'), ('Balance', 'jobs.balance'))) + [
        FF('Own average per finished hour', OWN_KIND % (K_NAR, K_NAR), 'money'), FF('Share of the title cost', 'IFERROR(%s/SUMIFS({range:jobs.quote},{range:jobs.title},%s),0)' % (LK('jobs', 'job_id', 'quote'), LK('jobs', 'job_id', 'title')), 'pct')]),
    FORM('translation_order', 'Translation Order Sheet', 'Translation order with words and rate', 'jobs.job_id', JOBF(F(('Units, thousand words', 'jobs.units'), ('Rate per 1,000 words', 'jobs.unit_rate'), ('Quote', 'jobs.quote'),
                                                                                         ('Start date', 'jobs.start_date'), ('Due date', 'jobs.due_date'), ('Balance', 'jobs.balance'))) + [
        FF('Own average per 1,000 words', OWN_KIND % (K_TR, K_TR), 'money'), FF('Translation cases on file for the title', 'COUNTIFS({range:translation.title},%s)' % LK('jobs', 'job_id', 'title'), 'int')]),
    FORM('formatting_order', 'Formatting Order Sheet', 'Formatting order with edition and price', 'jobs.job_id', JOBF(F(('Title ID', 'jobs.title_id'), ('Quote', 'jobs.quote'), ('Start date', 'jobs.start_date'), ('Due date', 'jobs.due_date'), ('Status', 'jobs.status'))) + [
        FF('Typical rate for formatting', 'SUMIFS({range:cost_cat.rate},{range:cost_cat.kind},%s)' % K_FMT, 'money'), FF('Average cost of your formatting jobs', 'IFERROR(AVERAGEIFS({range:jobs.quote},{range:jobs.kind},%s),0)' % K_FMT, 'money')]),
    FORM('contractor_payment', 'Contractor Payment Sheet', 'Contractor payment with job balance and cash after', 'jobpay.cpay_id', F(('Contractor', 'jobpay.contractor'), ('Phone', 'jobpay.phone'), ('Job', 'jobpay.job_id'), ('Title', 'jobpay.title'),
                                                                                                    ('Job kind', 'jobpay.kind'), ('Stage', 'jobpay.stage'), ('Date', 'jobpay.date'), ('Amount', 'jobpay.amount'), ('Status', 'jobpay.status')) + [
        FF('Quote of the job', 'IFERROR(INDEX({range:jobs.quote},MATCH(%s,{range:jobs.job_id},0)),0)' % LK('jobpay', 'cpay_id', 'job_id'), 'money'),
        FF('Balance of the job', 'IFERROR(INDEX({range:jobs.balance},MATCH(%s,{range:jobs.job_id},0)),0)' % LK('jobpay', 'cpay_id', 'job_id'), 'money'),
        FF('Cash now', CASHNOW, 'money'), FF('Cash after this payment', '%s-%s' % (CASHNOW, LK('jobpay', 'cpay_id', 'amount')), 'money')]),
    FORM('job_delivery_sheet', 'Job Delivery Sheet', 'Delivery check with days late and final payment', 'jobs.job_id', JOBF(F(('Due date', 'jobs.due_date'), ('Delivered on', 'jobs.delivered_on'), ('Days late', 'jobs.days_late'), ('Quote', 'jobs.quote'),
                                                                                  ('Paid', 'jobs.paid'), ('Balance', 'jobs.balance'), ('Status', 'jobs.status'))) + [
        FF('Final payment of the job', 'SUMIFS({range:jobpay.amount},{range:jobpay.job_id},{pick},{range:jobpay.stage},%s)' % tok('stage', 'Final'), 'money'),
        FF('Final payment date', 'SUMIFS({range:jobpay.date},{range:jobpay.job_id},{pick},{range:jobpay.stage},%s)' % tok('stage', 'Final'), 'date')]),
    FORM('job_change_sheet', 'Job Change Sheet', 'Job change with release date and balance', 'jobs.job_id', JOBF(F(('Quote', 'jobs.quote'), ('Units', 'jobs.units'), ('Due date', 'jobs.due_date'), ('Status', 'jobs.status'), ('Days late', 'jobs.days_late'),
                                                                                ('Balance', 'jobs.balance'))) + [
        FF('Release date of the title', 'INDEX({range:titles.release_date},MATCH(%s,{range:titles.title_id},0))' % LK('jobs', 'job_id', 'title_id'), 'date'),
        FF('Days to the release from today', 'INDEX({range:titles.release_date},MATCH(%s,{range:titles.title_id},0))-{today}' % LK('jobs', 'job_id', 'title_id'), 'int'),
        FF('Jobs of this title', 'COUNTIFS({range:jobs.title_id},%s)' % LK('jobs', 'job_id', 'title_id'), 'int')]),
    FORM('production_budget', 'Production Budget Sheet', 'Production budget of a title by kind of job', 'cost_title.title_id', F(('Title', 'cost_title.title'), ('Editing', 'cost_title.editing'), ('Cover', 'cost_title.cover'), ('Formatting', 'cost_title.formatting'),
                                                                                                  ('Narration', 'cost_title.narration'), ('Translation', 'cost_title.translation'), ('Setup and other', 'cost_title.other'), ('Total cost', 'cost_title.total'),
                                                                                                  ('Cost per 1,000 words', 'cost_title.cost_per_1000'), ('Over (+) or under (-) typical rates', 'cost_title.over_typical'), ('Rank by amount over', 'cost_title.over_rank')) + [
        FF('Royalties to date', 'IFERROR(INDEX({range:payback.to_date},MATCH({pick},{range:payback.title_id},0)),0)', 'money'),
        FF('Share earned back', 'IFERROR(INDEX({range:payback.pct_back},MATCH({pick},{range:payback.title_id},0)),0)', 'pct'),
        FF('Verdict', 'IFERROR(INDEX({range:payback.verdict},MATCH({pick},{range:payback.title_id},0)),"")', 'text')]),
    FORM('gonogo_sheet', 'Go or No-go Sheet', 'Edition go or no-go with three cases', 'gonogo.case_id', F(('Title', 'gonogo.title'), ('New format', 'gonogo.format'), ('Opened on', 'gonogo.opened_on'), ('One-off cost', 'gonogo.one_off_cost'),
                                                                                         ('List price', 'gonogo.list_price'), ('Royalty per copy', 'gonogo.royalty_per_copy'), ('Copies a month, low', 'gonogo.copies_low'), ('Copies a month, mid', 'gonogo.copies_mid'),
                                                                                         ('Copies a month, high', 'gonogo.copies_high'), ('Payback months, low', 'gonogo.payback_low'), ('Payback months, mid', 'gonogo.payback_mid'),
                                                                                         ('Payback months, high', 'gonogo.payback_high'), ('Verdict', 'gonogo.verdict')) + [
        FF('Break-even copies', 'IFERROR(ROUNDUP(%s/%s,0),0)' % (LK('gonogo', 'case_id', 'one_off_cost'), LK('gonogo', 'case_id', 'royalty_per_copy')), 'int'),
        FF('Royalties a month, mid case', 'ROUND(%s*%s,0)' % (LK('gonogo', 'case_id', 'copies_mid'), LK('gonogo', 'case_id', 'royalty_per_copy')), 'money')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('job_order_doc', 'Job Order Letter', 'Job order letter to a contractor', 'jobs.job_id', [
        'Job order of {set:company}, dated {today}. Job {col:jobs.job_id}. Dear {col:jobs.contractor}, thank you for agreeing to work on {col:jobs.title}.',
        'Work: {col:jobs.kind}. Units: {col:jobs.units}. Quote: {col:jobs.quote}. Start date: {col:jobs.start_date}. Due date: {col:jobs.due_date}.',
        'Payment in stages: a deposit when the job starts, a milestone payment for longer jobs and a final payment after delivery and acceptance. The dates and amounts are on the payment schedule that comes with this letter.',
        'Please tell us at once if the due date is at risk. Please write back to confirm that you accept this order.'], ['Author-publisher', 'Contractor'], NOTE),
    DOC('quote_request_doc', 'Quote Request', 'Quote request to a contractor', 'quotes.quote_id', [
        'Quote request of {set:company}, dated {today}. Dear {col:quotes.contractor}, we would like a quote for this work.',
        'Work: {col:quotes.kind} for {col:quotes.title}. Units: {col:quotes.units}. Wanted within {col:quotes.days_to_deliver} days.',
        'Please send your price, your earliest start date and the stages in which you want to be paid. We compare quotes against our own average for this kind of work.', 'Thank you for your time.'], ['Author-publisher', 'Contractor'], NOTE),
    DOC('cover_brief_doc', 'Cover Brief', 'Cover brief for the cover designer', 'jobs.job_id', [
        'Cover brief of {set:company}, dated {today}. Job {col:jobs.job_id}. Designer: {col:jobs.contractor}. Title: {col:jobs.title}.',
        'Quote: {col:jobs.quote}. Start date: {col:jobs.start_date}. First draft and final files due: {col:jobs.due_date}.',
        'Please describe the mood, the series look, the trim size and the title and author lines here: ______. A series cover should match the other books of its series.',
        'Please send the front cover for the ebook and the full wrap for print. We confirm the files in writing before the final payment.'], ['Author-publisher', 'Cover designer'], NOTE),
    DOC('narration_brief_doc', 'Narration Brief', 'Narration brief and sample-read request', 'jobs.job_id', [
        'Narration brief of {set:company}, dated {today}. Job {col:jobs.job_id}. Narrator: {col:jobs.contractor}. Title: {col:jobs.title}.',
        'Finished hours: {col:jobs.units}. Rate per finished hour: {col:jobs.unit_rate}. Quote: {col:jobs.quote}. Start date: {col:jobs.start_date}. Delivery date: {col:jobs.due_date}.',
        'Please send a short sample read of the first chapter before the deposit is paid. We then agree the voices, the pronunciation list and the delivery in parts.',
        'The final payment is made after the files are checked and accepted.'], ['Author-publisher', 'Narrator'], NOTE),
    DOC('translation_brief_doc', 'Translation Brief', 'Translation brief with words and glossary', 'translation.case_id', [
        'Translation brief of {set:company}, dated {today}. Case {col:translation.case_id}. Title: {col:translation.title}. Language: {col:translation.language}.',
        'Translation cost agreed: {col:translation.translation_cost}. Edit cost: {col:translation.edit_cost}. Cover cost: {col:translation.cover_cost}. Total cost: {col:translation.total_cost}.',
        'Please keep a glossary of names, places and invented words. We send the word count and the style notes with this brief. Please tell us the delivery date you can keep.',
        'Rights: the translated edition stays under the terms we agree in writing. Confirm any rights point with your adviser.'], ['Author-publisher', 'Translator'], NOTE),
    DOC('payment_schedule_doc', 'Payment Schedule', 'Payment schedule for a job', 'jobs.job_id', [
        'Payment schedule of {set:company}, dated {today}. Job {col:jobs.job_id}, {col:jobs.kind} of {col:jobs.title}, for {col:jobs.contractor}.',
        'Quote: {col:jobs.quote}. Paid so far: {col:jobs.paid}. Balance: {col:jobs.balance}. Start date: {col:jobs.start_date}. Due date: {col:jobs.due_date}.',
        'Stages: a deposit at the start, a milestone payment halfway for longer jobs and the final payment after acceptance. The dates and amounts of each stage are on the Job Payments sheet.',
        'A stage that would take our cash under the floor we may ask to move to a later date.'], ['Author-publisher', 'Contractor'], NOTE),
    DOC('payment_advice_doc', 'Payment Advice', 'Payment advice for a contractor', 'jobpay.cpay_id', [
        'Payment advice of {set:company}, dated {today}. Payment {col:jobpay.cpay_id}. Dear {col:jobpay.contractor}.',
        'We pay {col:jobpay.amount} for the {col:jobpay.stage} stage of job {col:jobpay.job_id}, {col:jobpay.kind} of {col:jobpay.title}. Date: {col:jobpay.date}. Status: {col:jobpay.status}.',
        'The payment is made by a bank transfer. Please tell us if the amount or the reference does not match your invoice.', 'Thank you for your work.'], ['Author-publisher', 'Contractor'], NOTE),
    DOC('acceptance_doc', 'Delivery Acceptance', 'Delivery acceptance note', 'jobs.job_id', [
        'Delivery acceptance of {set:company}, dated {today}. Job {col:jobs.job_id}, {col:jobs.kind} of {col:jobs.title}, by {col:jobs.contractor}.',
        'Due date: {col:jobs.due_date}. Delivered on: {col:jobs.delivered_on}. Days late: {col:jobs.days_late}. Quote: {col:jobs.quote}. Balance still to pay: {col:jobs.balance}.',
        'We have checked the delivered work and accept it. The final payment follows on the date in the payment schedule.', 'Please tell us within a few days if anything is missing on your side.'], ['Author-publisher', 'Contractor'], NOTE),
    DOC('title_cost_doc', 'Title Cost Summary', 'Title cost and payback summary', 'payback.title_id', [
        'Title cost summary of {set:company}, dated {today}. Title: {col:payback.title}. Series: {col:payback.series}. Status: {col:payback.status}.',
        'Production cost: {col:payback.cost}. Royalties to date: {col:payback.to_date}. Still to earn back: {col:payback.gap}. Share earned back: {col:payback.pct_back}.',
        'Months on sale: {col:payback.months_on_sale}. Own monthly average, last 6 months: {col:payback.avg_monthly}. Months still needed: {col:payback.months_to_pay}. Verdict: {col:payback.verdict}.',
        'Royalties are estimates until the payment arrives. The format that drags the title, if any: {col:payback.drag_format}.'], ['Author-publisher', 'Accountant'], NOTE),
    DOC('budget_report_doc', 'Production Budget Report', 'Production budget report for a title', 'cost_title.title_id', [
        'Production budget report of {set:company}, dated {today}. Title: {col:cost_title.title}.',
        'Editing: {col:cost_title.editing}. Cover: {col:cost_title.cover}. Formatting: {col:cost_title.formatting}. Narration: {col:cost_title.narration}. Translation: {col:cost_title.translation}. Setup and other: {col:cost_title.other}.',
        'Total cost: {col:cost_title.total}. Cost per 1,000 words: {col:cost_title.cost_per_1000}. Over (+) or under (-) your typical rates: {col:cost_title.over_typical}. Rank by amount over: {col:cost_title.over_rank}.',
        'Use the report to decide which quote to renegotiate before the next title.'], ['Author-publisher', 'Assistant'], NOTE),
    DOC('gonogo_doc', 'Go or No-go Report', 'Edition go or no-go report', 'gonogo.case_id', [
        'Go or no-go report of {set:company}, dated {today}. Case {col:gonogo.case_id}. Title: {col:gonogo.title}. New format: {col:gonogo.format}. Opened on {col:gonogo.opened_on}.',
        'One-off cost: {col:gonogo.one_off_cost}. List price: {col:gonogo.list_price}. Royalty per copy: {col:gonogo.royalty_per_copy}.',
        'Copies a month: low {col:gonogo.copies_low}, mid {col:gonogo.copies_mid}, high {col:gonogo.copies_high}. Payback months: low {col:gonogo.payback_low}, mid {col:gonogo.payback_mid}, high {col:gonogo.payback_high}.',
        'Verdict: {col:gonogo.verdict}. The copies are your own estimates and not a promise of sales. Write the decision below.'], ['Author-publisher', 'Assistant'], NOTE),
    DOC('accountant_doc', 'Contractor Summary', 'Contractor payment summary for the accountant', 'contractors.contractor', [
        'Contractor payment summary of {set:company}, dated {today}. Contractor: {col:contractors.contractor}. Role: {col:contractors.role}.',
        'Jobs: {col:contractors.jobs}. Quoted: {col:contractors.quoted}. Paid in the last 12 months: {col:contractors.paid_12m}. Paid all time: {col:contractors.paid_all}. Balance owed for booked work: {col:contractors.balance_owed}.',
        'Share of production spend, last 12 months: {col:contractors.share12}. Late jobs: {col:contractors.late_jobs}.',
        'Please check the amounts against the invoices you hold and tell us about any difference. Confirm any tax point with your adviser.'], ['Author-publisher', 'Accountant'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('new_job', 'New Job Steps', 'jobs', 'jobs.start_date', [('Write the job in the Jobs sheet', 0), ('Agree the quote and the units in writing', 0), ('Send the job order letter', 0), ('Pay the deposit', 1), ('Put the due date in your calendar', 1), ('Check progress halfway', 14), ('Chase if the due date is near', 30)]),
    CHK('compare_quotes', 'Comparing Quotes Steps', 'quotes', 'quotes.asked_on', [('Ask at least two contractors for a quote', 0), ('Write each quote in the Quote Comparison sheet', 3), ('Check the price per unit against your average', 4), ('Ask for a sample or a reference', 5), ('Pick one with the Quote Chooser', 7), ('Tell the others thank you', 8)]),
    CHK('cover_briefing', 'Cover Briefing Steps', 'jobs', 'jobs.start_date', [('Send the cover brief and the series look', 0), ('Share the blurb and the trim size', 1), ('Receive the first draft', 14), ('Give one round of notes', 17), ('Receive the final files', 30), ('Check the ebook and print wrap', 32), ('Pay the final payment', 40)]),
    CHK('editing_round', 'Editing Round Steps', 'jobs', 'jobs.start_date', [('Send the manuscript with the style notes', 0), ('Pay the deposit', 1), ('Receive the edited file', 30), ('Review the changes', 35), ('Send questions back', 37), ('Accept the round', 45), ('Pay the final payment', 52)]),
    CHK('narration_run', 'Narration Production Steps', 'jobs', 'jobs.start_date', [('Receive the sample read', 0), ('Send the pronunciation list', 2), ('Pay the deposit', 3), ('Listen to the first chapters', 21), ('Pay the milestone payment', 35), ('Receive the full files', 60), ('Check the files and give notes', 70), ('Accept and pay the final payment', 80)]),
    CHK('translation_run', 'Translation Project Steps', 'jobs', 'jobs.start_date', [('Send the book and the glossary', 0), ('Pay the deposit', 1), ('Check a sample chapter', 14), ('Receive the full translation', 60), ('Send it to an editor', 62), ('Check the cover and the blurb in the language', 75), ('Pay the final payment', 85)]),
    CHK('format_handover', 'Formatting Handover Steps', 'jobs', 'jobs.start_date', [('Send the final text and the cover', 0), ('Agree the identifiers and the trim size', 1), ('Receive the files', 10), ('Check ebook and print proofs', 12), ('Upload to the stores', 14), ('Pay the formatter', 20)]),
    CHK('delivery_accept', 'Delivery Acceptance Steps', 'jobs', 'jobs.due_date', [('Check that the files are complete', 0), ('Compare the work with the brief', 1), ('Write the delivery date in the Jobs sheet', 1), ('Accept or ask for changes in writing', 3), ('Release the final payment', 7), ('File the invoice', 7)]),
    CHK('pay_contractor', 'Paying a Contractor Steps', 'jobpay', 'jobpay.date', [('Check the work is accepted', -3), ('Check cash after paying against your floor', -2), ('Ask to split if cash would go under the floor', -2), ('Make the bank transfer', 0), ('Send the payment advice', 0), ('Mark the payment paid', 1), ('File the invoice for the accountant', 2)]),
    CHK('monthly_review', 'Monthly Production Review Steps', 'cash_month', 'cash_month.month', [('Add the new jobs and payments', 1), ('Update the royalties by month', 3), ('Check jobs overdue and unpaid', 4), ('Check the invoices due against cash', 5), ('Review the titles behind on payback', 7), ('Review quotes above your average', 8), ('Send the summary to the accountant', 10)]),
    CHK('gonogo_decision', 'Edition Go or No-go Steps', 'gonogo', 'gonogo.opened_on', [('List the one-off cost and the price', 0), ('Estimate copies a month in three cases', 2), ('Check the payback months', 3), ('Compare with the other open cases', 5), ('Decide: produce, wait or skip', 7), ('Write the decision and the date', 7), ('Order the work if the answer is produce', 10)]),
    CHK('closing_review', 'Production Closing Review Steps', 'titles', 'titles.release_date', [('Check every job of the title is paid', 30), ('Write the final cost in the Cost per Title sheet', 31), ('Set the break-even copies per edition', 35), ('Review the payback at 6 months', 180), ('Review the payback at 12 months', 365), ('Note which quote to renegotiate next time', 366)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
M = MSG
messages = [
    M('ed_quote', 'Editor: please send your quote', 'jobs', 'jobs.phone', 'Hello {contractor}, please send your quote for {title}, {words} words, to start on {start_date}. Thank you. {imprint}'),
    M('ed_deposit', 'Editor: your deposit is sent', 'jobpay', 'jobpay.phone', 'Hello {contractor}, your deposit of {amount} is sent for {title}. Thank you. {imprint}'),
    M('ed_final', 'Editor: the final payment is due', 'jobpay', 'jobpay.phone', 'Hello {contractor}, the final payment of {amount} for {title} is due on {date}. {imprint}'),
    M('ed_late', 'Editor: the edit is late', 'jobs', 'jobs.phone', 'Hello {contractor}, the edit of {title} is {days_late} days late. When can you deliver? {imprint}'),
    M('ed_accept', 'Editor: the edit is accepted', 'jobs', 'jobs.phone', 'Hello {contractor}, thank you, {title} is accepted. {imprint}'),
    M('cv_quote', 'Cover designer: please send your quote', 'jobs', 'jobs.phone', 'Hello {contractor}, please send your quote for the cover of {title}, wanted by {due_date}. {imprint}'),
    M('cv_deposit', 'Cover designer: your deposit is sent', 'jobpay', 'jobpay.phone', 'Hello {contractor}, your deposit of {amount} for the cover of {title} is sent. {imprint}'),
    M('cv_final', 'Cover designer: the final payment is due', 'jobpay', 'jobpay.phone', 'Hello {contractor}, the final payment of {amount} for the cover of {title} is due on {date}. {imprint}'),
    M('cv_accept', 'Cover designer: the cover is accepted', 'jobs', 'jobs.phone', 'Hello {contractor}, the cover of {title} is accepted, thank you. {imprint}'),
    M('fm_quote', 'Formatter: please quote the formatting', 'jobs', 'jobs.phone', 'Hello {contractor}, please quote the formatting of {title}, due {due_date}. {imprint}'),
    M('fm_paid', 'Formatter: your payment is sent', 'jobpay', 'jobpay.phone', 'Hello {contractor}, your payment of {amount} for {title} is sent. {imprint}'),
    M('fm_accept', 'Formatter: the files are accepted', 'jobs', 'jobs.phone', 'Hello {contractor}, the files of {title} are accepted. Thank you. {imprint}'),
    M('nr_quote', 'Narrator: please send your quote', 'jobs', 'jobs.phone', 'Hello {contractor}, please send your quote for {title}, {units} finished hours. {imprint}'),
    M('nr_deposit', 'Narrator: your deposit is sent', 'jobpay', 'jobpay.phone', 'Hello {contractor}, your deposit of {amount} for {title} is sent. {imprint}'),
    M('nr_milestone', 'Narrator: the milestone payment is due', 'jobpay', 'jobpay.phone', 'Hello {contractor}, the milestone payment of {amount} for {title} is due on {date}. {imprint}'),
    M('nr_final', 'Narrator: the final payment is due', 'jobpay', 'jobpay.phone', 'Hello {contractor}, the final payment of {amount} for {title} is due on {date}. {imprint}'),
    M('nr_late', 'Narrator: the audio is late', 'jobs', 'jobs.phone', 'Hello {contractor}, the audio of {title} is {days_late} days late. When can you deliver? {imprint}'),
    M('nr_accept', 'Narrator: the audio files are accepted', 'jobs', 'jobs.phone', 'Hello {contractor}, the audio files of {title} are accepted. Thank you. {imprint}'),
    M('tr_quote', 'Translator: please send your quote', 'translation', 'translation.phone', 'Hello {translator}, please send your quote for {title} in {language}. {imprint}'),
    M('tr_deposit', 'Translator: your deposit is sent', 'jobpay', 'jobpay.phone', 'Hello {contractor}, your deposit of {amount} for the translation of {title} is sent. {imprint}'),
    M('tr_late', 'Translator: the translation is late', 'jobs', 'jobs.phone', 'Hello {contractor}, the translation of {title} is {days_late} days late. When can you deliver? {imprint}'),
    M('tr_final', 'Translator: the final payment is due', 'jobpay', 'jobpay.phone', 'Hello {contractor}, the final payment of {amount} for the translation of {title} is due on {date}. {imprint}'),
    M('va_chase', 'Assistant: please chase a contractor', 'attention', 'attention.va_phone', 'Hello, please chase {contractor} for {title}, due {due_date}, now {days_late} days late. {imprint}'),
    M('va_invoice', 'Assistant: please file an invoice', 'due', 'due.va_phone', 'Hello, please file the invoice of {contractor} for {amount}, due {due_date}. {imprint}'),
    M('ac_paid', 'Accountant: payments of the month', 'cash_month', 'cash_month.accountant_phone', 'Hello {accountant}, contractor payments of {paid_month} were made in {month}. Please book them. {imprint}'),
    M('ac_cost', 'Accountant: the cost of a title to date', 'cost_title', 'cost_title.accountant_phone', 'Hello {accountant}, the production cost of {title} to date is {total}. {imprint}'),
    M('au_overdue', 'Author: jobs are overdue', 'attention', 'attention.author_phone', 'Hello, {overdue_count} jobs are overdue now. This one: {title}, {contractor}, {days_late} days late. {imprint}'),
    M('au_invoice', 'Author: invoice due, cash after paying', 'due', 'due.author_phone', 'Hello, the invoice of {contractor} for {amount} is due on {due_date}. Cash after paying is {cash_after}. {imprint}'),
    M('au_behind', 'Author: a title is behind on its payback', 'payback', 'payback.author_phone', 'Hello, {title} is behind on its payback: {gap} still to earn back after {months_on_sale} months on sale. {imprint}'),
    M('au_paidback', 'Author: a title has earned back its cost', 'payback', 'payback.author_phone', 'Hello, {title} has earned back its production cost of {cost}. {imprint}'),
    M('au_quote', 'Author: a quote is above your average', 'quotes', 'quotes.author_phone', 'Hello, the quote of {contractor} for {title} is {diff_pct} against your own average per unit. {imprint}'),
    M('au_budget', 'Author: a budget is over', 'budget', 'budget.author_phone', 'Hello, the budget of {title} is over by {over_amount} on the job {kind}. {imprint}'),
    M('au_audio', 'Author: an edition is short of its cost', 'cost_edition', 'cost_edition.author_phone', 'Hello, the {format} of {title} is still {cost_gap} short of its cost. {imprint}'),
    M('au_gonogo', 'Author: a go or no-go is waiting', 'gonogo', 'gonogo.author_phone', 'Hello, a go or no-go decision is waiting for {title}: {format}, payback {payback_mid} months in the mid case. {imprint}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30), dashboard, insights
JP = '{range:jobpay.status},"<>"&%s' % PAID
def NEXT(n): return 'COUNTIFS(%s,{range:jobpay.date},"<="&({today}+%d))' % (JP, n)
def UNITS(k): return 'SUMIFS({range:jobs.units},{range:jobs.kind},%s)' % k
def QUOTE(k): return 'SUMIFS({range:jobs.quote},{range:jobs.kind},%s)' % k
kpis = [
    KPI('Production cost of all titles', 'SUM({range:jobs.quote})', 'money'),
    KPI('Production cost, last 12 months', 'SUMIFS({range:jobs.quote},{range:jobs.start_date},">="&({today}-365),{range:jobs.start_date},"<="&{today})', 'money'),
    KPI('Paid to contractors this month', 'SUMIFS({range:jobpay.amount},{range:jobpay.status},%s,{range:jobpay.date},">="&%s,{range:jobpay.date},"<="&{today})' % (PAID, MS), 'money'),
    KPI('Paid to contractors, last 30 days', 'SUMIFS({range:jobpay.amount},{range:jobpay.status},%s,{range:jobpay.date},">="&({today}-30),{range:jobpay.date},"<="&{today})' % PAID, 'money'),
    KPI('Balance owed for booked work', 'SUM({range:jobs.owed})', 'money'),
    KPI('Jobs in progress', 'COUNTIFS({range:jobs.status},%s)' % JIP, 'int'),
    KPI('Jobs overdue', 'SUM({range:jobs.late_open})', 'int'),
    KPI('Jobs delivered and unpaid', 'COUNTIFS({range:jobs.status},%s)' % JDEL, 'int'),
    KPI('Invoices due next 7 days', NEXT(7), 'int'),
    KPI('Invoices due next 30 days', NEXT(30), 'int'),
    KPI('Cash after the next invoices', '%s-SUMIFS({range:jobpay.amount},%s,{range:jobpay.date},"<="&({today}+{set:invoice_days}))' % (CASHNOW, JP), 'money'),
    KPI('Cash now above the floor', '%s-{set:cash_floor}' % CASHNOW, 'money'),
    KPI('Titles paid back', 'COUNTIFS({range:payback.verdict},%s)' % PB_, 'int'),
    KPI('Titles on track', 'COUNTIFS({range:payback.verdict},%s)' % ONT, 'int'),
    KPI('Titles behind on payback', 'COUNTIFS({range:payback.verdict},%s)' % BEH, 'int'),
    KPI('Title furthest behind', 'IFERROR(INDEX({range:payback.title},MATCH(MAX({range:payback.behind_gap}),{range:payback.behind_gap},0)),"")', 'text'),
    KPI('Months to pay back newest unpaid title', 'IFERROR(INDEX({range:payback.months_to_pay},MATCH(MAX({range:payback.unpaid_key}),{range:payback.unpaid_key},0)),0)', 'num'),
    KPI('Average cost per title', 'IFERROR(AVERAGE({range:cost_title.total}),0)', 'money'),
    KPI('Cost per released title, 24 months', 'IFERROR(AVERAGEIFS({range:titles.total_cost},{range:titles.release_date},">="&EDATE({today},-24),{range:titles.release_date},"<="&{today}),0)', 'money'),
    KPI('Cost per 1,000 words of editing', 'IFERROR((%s)/(%s),0)' % ('+'.join(QUOTE(k) for k in (K_DEV, K_COPY, K_PROOF)), '+'.join(UNITS(k) for k in (K_DEV, K_COPY, K_PROOF))), 'money'),
    KPI('Cost per finished hour of narration', 'IFERROR(%s/%s,0)' % (QUOTE(K_NAR), UNITS(K_NAR)), 'money'),
    KPI('Cost per cover', 'IFERROR(AVERAGEIFS({range:jobs.quote},{range:jobs.kind},%s),0)' % K_COVER, 'money'),
    KPI('Total over the typical-rate budget', 'SUM({range:budget.over_only})', 'money'),
    KPI('Share of cost spent on audio', 'IFERROR(SUM({range:cost_title.narration})/SUM({range:cost_title.total}),0)', 'pct'),
    KPI('Share of cost spent on editing', 'IFERROR(SUM({range:cost_title.editing})/SUM({range:cost_title.total}),0)', 'pct'),
    KPI('Share of cost spent on covers', 'IFERROR(SUM({range:cost_title.cover})/SUM({range:cost_title.total}),0)', 'pct'),
    KPI('Largest contractor share of spend', 'MAX({range:contractors.share12})', 'pct'),
    KPI('Open go or no-go cases', 'COUNTIFS({range:gonogo.status},%s)' % tok('gostatus', 'Open'), 'int'),
    KPI('Translation cost in progress', 'SUMIFS({range:jobs.quote},{range:jobs.kind},%s,{range:jobs.status},"<>"&%s)' % (K_TR, JPAID), 'money'),
    KPI('Average days late of delivered jobs', 'IFERROR(AVERAGEIFS({range:jobs.days_late},{range:jobs.delivered_on},">0"),0)', 'num'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Production KPI Dashboard", "kpis": kpis,
    "monthly": {"title": "Paid to contractors and royalties earned", "date": "jobpay.date", "series": [
        {"label": "Paid and due to contractors", "sum": "jobpay.amount", "date": "jobpay.date"}, {"label": "Royalties earned", "sum": "roy_month.royalties", "date": "roy_month.month"}]},
    "breakdowns": [{"title": "Quoted cost by kind of job", "by": "jobs.kind", "value": "jobs.quote", "agg": "sum"}, {"title": "Paid by contractor, all time", "by": "contractors.contractor", "value": "contractors.paid_all", "agg": "sum"},
                   {"title": "Production cost by series", "by": "titles.series", "value": "titles.total_cost", "agg": "sum"}, {"title": "Jobs by status", "by": "jobs.status", "value": "jobs.quote", "agg": "count"}]}
GO_OPEN = tok('gostatus', 'Open')
insights = {"filters": [{"label": "Job kind", "list": "jobkind"}, {"label": "Series", "list": "series"}],
    "gauges": [
        {"title": "Titles paid back", "num": AGG('count', 'payback', where=[('verdict', '=', PB_)]), "den": AGG('count', 'payback', where=[('verdict', '<>', NOS)])},
        {"title": "Jobs delivered on time", "num": AGG('count', 'jobs', where=[('delivered_on', '>', 0), ('days_late', '<=', 0)]), "den": AGG('count', 'jobs', where=[('delivered_on', '>', 0)])},
        {"title": "Each invoice payable above floor", "num": AGG('count', 'due', where=[('cash_alone', '>=', '{set:cash_floor}')]), "den": AGG('count', 'due', where=[('amount', '>', 0)])},
        {"title": "Spend within the typical-rate budget", "num": AGG('count', 'budget', where=[('flag', '<>', ca('Over the typical rate'))]), "den": AGG('count', 'budget')},
        {"title": "Titles on track or paid back", "num": AGG('count', 'payback', where=[('verdict', '<>', BEH), ('verdict', '<>', NOS)]), "den": AGG('count', 'payback', where=[('verdict', '<>', NOS)])},
        {"title": "Contractor payments made, of those due", "num": AGG('count', 'jobpay', where=[('status', '=', PAID)]), "den": AGG('count', 'jobpay', where=[('status', '<>', tok('cpaystatus', 'Scheduled'))])}],
    "charts": [
        CHART('Quoted cost by kind of job', 'bar', 'jobs.kind', [AGG('sum', 'jobs', 'jobs.quote', label='Quoted cost')]),
        CHART('Production paid per month', 'column', 'month', [AGG('sum', 'jobpay', 'jobpay.amount', date='jobpay.date', where=[('status', '=', PAID)], label='Paid')]),
        CHART('Production paid by contractor', 'bar', 'contractors.contractor', [AGG('sum', 'contractors', 'contractors.paid_all', label='Paid, all time')]),
        CHART('Production paid by job kind', 'bar', 'jobs.kind', [AGG('sum', 'jobs', 'jobs.paid', label='Paid')]),
        CHART('Jobs by status', 'bar', 'jobs.status', [AGG('count', 'jobs', label='Jobs')]),
        CHART('Jobs by kind', 'bar', 'jobs.kind', [AGG('count', 'jobs', label='Jobs')]),
        CHART('Job payments by status', 'bar', 'jobpay.status', [AGG('count', 'jobpay', label='Payments')]),
        CHART('Job payments by stage', 'bar', 'jobpay.stage', [AGG('sum', 'jobpay', 'jobpay.amount', label='Amount')]),
        CHART('Payments per month', 'line', 'month', [AGG('count', 'jobpay', date='jobpay.date', label='Payments')]),
        CHART('Average quote by job kind', 'bar', 'jobs.kind', [AGG('avg', 'jobs', 'jobs.quote', label='Average quote')]),
        CHART('Production cost by series', 'bar', 'titles.series', [AGG('sum', 'titles', 'titles.total_cost', label='Production cost')]),
        CHART('Production cost by pen name', 'bar', 'titles.pen_name', [AGG('sum', 'titles', 'titles.total_cost', label='Production cost')]),
        CHART('Royalties per month', 'column', 'month', [AGG('sum', 'roy_month', 'roy_month.royalties', date='roy_month.month', label='Royalties')]),
        CHART('Royalties by series', 'bar', 'roy_month.series', [AGG('sum', 'roy_month', 'roy_month.royalties', label='Royalties')]),
        CHART('Balance owed by contractor', 'bar', 'contractors.contractor', [AGG('sum', 'contractors', 'contractors.balance_owed', label='Balance owed')]),
        CHART('Late jobs by contractor', 'bar', 'contractors.contractor', [AGG('sum', 'contractors', 'contractors.late_jobs', label='Late jobs')]),
        CHART('Cost per 1,000 words by contractor', 'bar', 'contractors.contractor', [AGG('avg', 'contractors', 'contractors.cost_1000', label='Cost per 1,000 words')]),
        CHART('Cost per finished hour by contractor', 'bar', 'contractors.contractor', [AGG('avg', 'contractors', 'contractors.cost_hour', label='Cost per finished hour')]),
        CHART('Go or no-go cases by format', 'bar', 'gonogo.format', [AGG('count', 'gonogo', label='Cases')]),
        CHART('Translation cases by language', 'bar', 'translation.language', [AGG('count', 'translation', label='Cases')]),
        CHART('Price per unit of quotes by job kind', 'bar', 'quotes.kind', [AGG('avg', 'quotes', 'quotes.price_per_unit', label='Price per unit')]),
        CHART('Closing cash by month', 'line', 'month', [AGG('sum', 'cash_month', 'cash_month.closing', date='cash_month.month', label='Closing cash'), AGG('sum', 'cash_month', 'cash_month.free_cash', date='cash_month.month', label='Above the floor')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Title payback verdict", "why": "each title is set against its own royalties and last 6 months, with paid back, on track or behind and the format that drags it", "where": "Title Payback Verdict"},
    {"name": "Break-even copies solver", "why": "the copies, the pace and the price an edition needs to earn back its allocated cost in the months you allow", "where": "Break-Even Copies Solver"},
    {"name": "Budget against actual ranker", "why": "titles ranked by how far their quotes ran over your typical rates, with the item most over and a renegotiate or within-budget verdict", "where": "Budget vs Actual Ranker"},
    {"name": "Contractor invoice cash test", "why": "the invoices that fall due set against cash and your floor, with pay, ask to split or hold the next job", "where": "Invoice Cash Test"},
    {"name": "Audio, large print and hardcover go or no-go", "why": "low, mid and high payback from the title's own ebook sales before you order a new edition", "where": "Audio Go or No-go"},
    {"name": "Translation business case", "why": "translation, edit and cover cost against copies a month, and what the same book gives if you sell the rights instead", "where": "Translation Business Case"},
    {"name": "Late job impact", "why": "a late edit or narration carried through the jobs that follow, with the new release date if the delay cannot be absorbed", "where": "Late Job Impact"},
    {"name": "Unit cost check", "why": "cost per 1,000 words and per finished hour of every job against your own average for that kind", "where": "Unit Cost Check"},
    {"name": "Invoices due in order", "why": "every open payment nearest first with the cash left after paying it, flagged under your floor", "where": "Invoices Due"},
    {"name": "Break-even by series and format", "why": "allocated cost, copies and royalties per series and format, so you see which format has not paid its way", "where": "Break-Even by Series"}]
competitors = [
    {"what": "free royalty tracking template", "lacks": "adds up what stores paid but never sets a production cost against it, so no title ever shows paid back or behind"},
    {"what": "generic budget spreadsheet", "lacks": "has no jobs, deposits, milestones or typical rates by kind of work and cannot tell an editor quote from a narrator quote"},
    {"what": "subscription store dashboard", "lacks": "shows sales only: no contractor jobs, no cost per title, no break-even copies and a monthly fee that never stops"},
    {"what": "single-sheet book launch plan", "lacks": "lists tasks but not the cost of each job, the cash that invoices take or the go or no-go for a new edition"},
    {"what": "freelancer invoice tracker", "lacks": "records what you owe but not whether a quote is high for its kind, which title is over budget or whether cash stays above your floor"}]
guide = [
    'Open Start and type your imprint name and your own limits in the yellow cells: the cash floor, the months a title should take to earn back its cost and the payback months that make a new edition a go.',
    'Check Team and Cost Categories. They hold your contractors and your typical rate for each kind of job; every quote is set against them.',
    'Write each job in Jobs: title, kind, contractor, quote, units, dates and what you paid. The balance, days late and the overdue flag fill in by themselves.',
    'Write each payment in Job Payments: deposit, milestone or final, with its date and status. Open payments show in Invoices Due against your cash floor.',
    'Keep Titles and Editions up to date with price, print cost and royalty share (check each store\'s current terms).',
    'Type copies sold and royalties earned for each edition in Cost per Edition, and the royalties of each month in Royalties by Month. Cost per Title, Payback by Title and Break-Even by Series fill in.',
    'Type the closing cash of each month in Cash by Month. The invoice tests and the dashboard use it.',
    'Read Overdue and Unpaid Jobs and Invoices Due every week and use the message links to chase a contractor or send a payment note.',
    'Use Edition Go or No-go and Translation Cases to weigh a new edition before you order the work. Royalties and copies are your own estimates until the payment arrives.',
    f'Use the {len(tools)} calculators to test a title\'s payback, solve break-even copies, rank budgets, test cash, check quotes and plan stage payments.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'A first-time author with 1 to 3 books can use most sheets with a few rows; a small press can read the pen-name columns as author columns.',
    'Read the Production KPI Dashboard and the charts every month. The workbook has no macros and works in Excel and Google Sheets.']
listing = {"title": "Author and Self-Publisher Production Costs and Break-Even Excel Template: Contractor Jobs, Payback, Audio Go or No-go",
    "headline": "Know what each book cost and when it earns that back",
    "tags": ["self publishing", "author business", "book production", "break even", "royalty tracker", "excel template", "indie author", "audiobook cost", "editor invoices", "cover design cost", "book budget", "cost per title", "payback tracker"],
    "description": ("Run the production side of an independent publishing business in one Excel workbook. Built for an author-publisher who pays editors, a cover designer, a formatter, narrators and a translator per job and wants to know what each title cost and when it earns that back.\n\n"
        "The Jobs ledger holds every quote, units, due date, what was paid and the balance, with days late and an overdue flag. Job Payments records deposits, milestones and final payments, and Invoices Due lists the open ones nearest first with the cash left after paying them against your cash floor. "
        "Budget vs Actual sets every quote against your typical rate for that kind of job, and Unit Cost Check shows the cost per 1,000 words and per finished hour against your own average.\n\n"
        "Cost per Title and Cost per Edition split the production cost, Payback by Title compares it with royalties to date and your own monthly average, and Break-Even by Series shows the copies each format needs. "
        f"{len(tools)} calculators cover the title payback verdict, break-even copies, budget ranking, the invoice cash test, audio, large print and hardcover go or no-go, the translation business case, translate or write, stage payments, contractor concentration, quote choice, late job impact, a cost cap, a series budget, a cover refresh and a payback what-if. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to editors, the cover designer, the formatter, narrators, the translator, your assistant and your accountant.\n\n"
        "This is part two of the Author and Self-Publisher Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data and a blank copy. It helps you keep track of your costs; royalties and copies are estimates until the payment arrives and nothing here promises sales. Confirm tax and contract points with your adviser."),
    "features": ["Contractor job ledger with balance and days late", "Invoices due against your cash floor", "Budget against actual by kind of job", "Cost per title and per edition", "Payback by title from your own royalties", "Break-even copies by series and format",
                 "Audio, large print and hardcover go or no-go", "Translation business case", f"{len(tools)} calculators with a verdict", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
HINTS = {}
s = spec(id=f'{SUITE}-p2', slug='author-publisher-production', profession='Author and Self-Publisher Business', name='Production Costs and Break-Even',
         tagline='Know what each book cost and when it earns that back', price_usd=29,
         colors={"primary": "#2B3A55", "accent": "#CE7777"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 2, "of": 8, "focus": "Production costs, contractor jobs and break-even"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'au2.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
