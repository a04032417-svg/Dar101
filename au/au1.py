"""Author and Self-Publisher Business suite - part 1: Catalogue, Series Plan and Releases."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au1_lists import *
from au1_tables import settings, tables
from au1_tools import tools

SUITE = 'fx-20261115-author-publisher'
NOTE = "Sample wording: adapt it to your own business. Check each store's current terms and confirm any tax or rights point with your adviser."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LKP(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
LIVE = est('Live'); PLN = est('Planned'); RELD = tst('Released'); PRE = tst('Pre-order'); PROD = tst('In production')
GAP = '{set:min_release_gap_days}'

# ------------------------------------------------------------------ forms (12)
TD = lambda c: LKP('titles', 'title_id', c)
ED = lambda c: LKP('editions', 'edition_id', c)
forms = [
    FORM('title_sheet', 'Title Sheet', 'Title Sheet', 'titles.title_id', F(
        ('Title', 'titles.title'), ('Pen name', 'titles.pen_name'), ('Series', 'titles.series'), ('Book number', 'titles.series_order'), ('Genre', 'titles.genre'), ('Words', 'titles.words'), ('Pages', 'titles.pages'),
        ('Release date', 'titles.release_date'), ('Status', 'titles.status'), ('Months on sale', 'titles.months_on_sale'), ('Days to release (negative once released)', 'titles.days_to_release'),
        ('Pre-orders', 'titles.preorders')) + [
        FF('Editions of this title', 'COUNTIFS({range:editions.title_id},{pick})', 'int'),
        FF('Editions on sale', 'COUNTIFS({range:editions.title_id},{pick},{range:editions.status},%s)' % LIVE, 'int')]),
    FORM('edition_sheet', 'Edition Sheet', 'Edition Sheet', 'editions.edition_id', F(
        ('Title', 'editions.title'), ('Format', 'editions.format'), ('List price', 'editions.list_price'), ('Unit cost', 'editions.unit_cost'), ('Royalty share', 'editions.royalty_share'),
        ('Royalty per copy', 'editions.royalty_per_copy'), ('Identifier', 'editions.identifier'), ('Pages', 'editions.pages'), ('Finished hours', 'editions.hours'), ('Release date', 'editions.release_date'),
        ('Status', 'editions.status')) + [
        FF('Royalty on 100 copies, estimate', 'ROUND(100*%s,2)' % ED('royalty_per_copy'), 'money'),
        FF('Editions of this title', 'COUNTIFS({range:editions.title_id},%s)' % ED('title_id'), 'int')]),
    FORM('series_plan_sheet', 'Series Plan Sheet', 'Series Plan Sheet', 'steps.step_id', F(
        ('Series', 'steps.series'), ('Book number', 'steps.book_number'), ('Title', 'steps.title'), ('Planned or actual release', 'steps.planned_release'), ('Planned cost', 'steps.planned_cost'),
        ('Expected read-through into the next book', 'steps.expected_readthrough'), ('Status', 'steps.status'), ('Start the draft by', 'steps.start_date')) + [
        FF('Books in this series plan', 'COUNTIFS({range:steps.series},%s)' % LKP('steps', 'step_id', 'series'), 'int'),
        FF('Planned cost of the whole series plan', 'SUMIFS({range:steps.planned_cost},{range:steps.series},%s)' % LKP('steps', 'step_id', 'series'), 'money')]),
    FORM('release_plan_sheet', 'Release Plan Sheet', 'Release Plan Sheet', 'titles.title_id', F(
        ('Title', 'titles.title'), ('Series', 'titles.series'), ('Release date', 'titles.release_date'), ('Status', 'titles.status'), ('Days to release (negative once released)', 'titles.days_to_release'),
        ('Open jobs', 'titles.open_jobs')) + [
        FF('Other releases inside the minimum gap', 'COUNTIFS({range:titles.release_date},">"&(%s-%s),{range:titles.release_date},"<"&(%s+%s))-1' % (TD('release_date'), GAP, TD('release_date'), GAP), 'int'),
        FF('Calendar entries within 7 days', 'COUNTIFS({range:calendar.date},">="&(%s-7),{range:calendar.date},"<="&(%s+7))' % (TD('release_date'), TD('release_date')), 'int'),
        FF('Smallest gap you accept, days', GAP, 'int')]),
    FORM('preorder_sheet', 'Pre-order Setup Sheet', 'Pre-order Setup Sheet', 'titles.title_id', F(
        ('Title', 'titles.title'), ('Pen name', 'titles.pen_name'), ('Release date', 'titles.release_date'), ('Status', 'titles.status'), ('Pre-orders so far', 'titles.preorders'),
        ('Assistant phone', 'titles.assistant_phone')) + [
        FF('Earliest pre-order opening', '%s-{set:preorder_max_days}' % TD('release_date'), 'date'),
        FF('Upload the files by', '%s-{set:preorder_max_days}-{set:upload_lead_days}' % TD('release_date'), 'date'),
        FF('Days left to upload', '%s-{set:preorder_max_days}-{set:upload_lead_days}-{today}' % TD('release_date'), 'int')]),
    FORM('price_check_sheet', 'Store Price Check Sheet', 'Store Price Check Sheet', 'storeprices.price_id', F(
        ('Edition', 'storeprices.edition_id'), ('Title', 'storeprices.title'), ('Format', 'storeprices.format'), ('Store', 'storeprices.store'), ('Currency', 'storeprices.currency'),
        ('Price in store currency', 'storeprices.price'), ('Rate to home currency', 'storeprices.rate'), ('Price in home currency', 'storeprices.price_home'), ('List price', 'storeprices.list_price'),
        ('Difference from list price', 'storeprices.diff_pct'), ('Price check', 'storeprices.matches'), ('Price checked on', 'storeprices.checked_on'), ('Days since the check', 'storeprices.days_since')) + [
        FF('Store prices of this edition', 'COUNTIFS({range:storeprices.edition_id},%s)' % LKP('storeprices', 'price_id', 'edition_id'), 'int')]),
    FORM('wish_sheet', 'Planned Edition Request Sheet', 'Planned Edition Request Sheet', 'wishlist.wish_id', F(
        ('Title', 'wishlist.title'), ('Format', 'wishlist.format'), ('Planned price', 'wishlist.planned_price'), ('Planned release', 'wishlist.planned_release'), ('Planned cost', 'wishlist.planned_cost'),
        ('Priority', 'wishlist.priority'), ('Status', 'wishlist.status'), ('Expected copies a month', 'wishlist.copies_month'), ('Royalty per copy', 'wishlist.royalty_copy'),
        ('Royalty a month', 'wishlist.royalty_month'), ('Months to earn back the cost', 'wishlist.months_to_earn'), ('Verdict', 'wishlist.go_verdict')) + [
        FF('Planned editions of this format', 'COUNTIFS({range:wishlist.format},%s)' % LKP('wishlist', 'wish_id', 'format'), 'int')]),
    FORM('identifier_sheet', 'Identifier Assignment Sheet', 'Identifier Assignment Sheet', 'editions.edition_id', F(
        ('Title', 'editions.title'), ('Format', 'editions.format'), ('Status', 'editions.status'), ('Identifier', 'editions.identifier'), ('Release date', 'editions.release_date')) + [
        FF('Editions sharing this identifier', 'COUNTIF({range:editions.identifier},%s)' % ED('identifier'), 'int'),
        FF('Editions without an identifier', 'SUM({range:completeness.id_missing})', 'int'),
        FF('Editions of this format', 'COUNTIFS({range:editions.format},%s)' % ED('format'), 'int')]),
    FORM('date_change_sheet', 'Release Date Change Sheet', 'Release Date Change Sheet', 'calendar.entry_id', F(
        ('Date', 'calendar.date'), ('Entry kind', 'calendar.kind'), ('Title', 'calendar.title'), ('Note', 'calendar.note'), ('Days from today', 'calendar.days_from_today'), ('Conflict check', 'calendar.conflict'),
        ('Launch coordinator phone', 'calendar.launch_phone')) + [
        FF('Releases inside the minimum gap', 'COUNTIFS({range:calendar.kind},%s,{range:calendar.date},">"&(%s-%s),{range:calendar.date},"<"&(%s+%s))' % (
            ckd('Release'), LKP('calendar', 'entry_id', 'date'), GAP, LKP('calendar', 'entry_id', 'date'), GAP), 'int'),
        FF('Calendar entries within 7 days', 'COUNTIFS({range:calendar.date},">="&(%s-7),{range:calendar.date},"<="&(%s+7))' % (LKP('calendar', 'entry_id', 'date'), LKP('calendar', 'entry_id', 'date')), 'int')]),
    FORM('catalogue_sheet', 'Catalogue Update Sheet', 'Catalogue Update Sheet', 'completeness.edition_id', F(
        ('Title', 'completeness.title'), ('Format', 'completeness.format'), ('Status', 'completeness.status'), ('Identifier', 'completeness.identifier'), ('Problems found', 'completeness.problems'),
        ('Completeness', 'completeness.completeness'), ('First problem', 'completeness.issue')) + [
        FF('Editions with a problem', 'COUNTIFS({range:completeness.problems},">0")', 'int'),
        FF('Share of editions complete', 'IFERROR(COUNTIFS({range:completeness.problems},0)/COUNTA({range:completeness.edition_id}),0)', 'pct')]),
    FORM('alsoby_sheet', 'Also-by Page Sheet', 'Also-by Page Sheet', 'reading.title', F(
        ('Pen name', 'reading.pen_name'), ('Series', 'reading.series'), ('Book number', 'reading.book_number'), ('Release date', 'reading.release_date'), ('Next book', 'reading.next_title'),
        ('Ebook price', 'reading.price_ebook'), ('Paperback price', 'reading.price_paperback'), ('Audiobook price', 'reading.price_audio')) + [
        FF('Other titles by this pen name', 'COUNTIFS({range:reading.pen_name},%s)-1' % LKP('reading', 'title', 'pen_name'), 'int'),
        FF('Titles in this series', 'COUNTIFS({range:reading.series},%s)' % LKP('reading', 'title', 'series'), 'int')]),
    FORM('metadata_sheet', 'Metadata Check Sheet', 'Metadata Check Sheet', 'pricepage.edition_id', F(
        ('Title', 'pricepage.title'), ('Format', 'pricepage.format'), ('List price', 'pricepage.list_price'), ('Pages', 'pricepage.pages'), ('Price per 100 pages', 'pricepage.price_per_page'),
        ('Unit cost', 'pricepage.unit_cost'), ('Print cost share of price', 'pricepage.print_cost_share'), ('Cost share check', 'pricepage.share_flag')) + [
        FF('Identifier', 'INDEX({range:editions.identifier},MATCH({pick},{range:editions.edition_id},0))&""', 'text'),
        FF('Your highest print cost share', '{set:print_cost_share_max}', 'pct')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
def DC(*a): return DOC(*a)
documents = [
    DC('title_info_doc', 'Title Information Sheet', 'Title information sheet for a store page', 'reading.title', [
        'Title information sheet of {set:company}, dated {today}. Title: {col:reading.title}. Pen name: {col:reading.pen_name}. Series: {col:reading.series}, book {col:reading.book_number}.',
        'Words: {col:reading.words}. Pages: {col:reading.pages}. Release date: {col:reading.release_date}. Editions on sale: {col:reading.editions_live}.',
        'List price by format: ebook {col:reading.price_ebook}, paperback {col:reading.price_paperback}, hardcover {col:reading.price_hardcover}, large print {col:reading.price_large}, audiobook {col:reading.price_audio}. A price of 0 means that format is not on sale.',
        'Use this sheet to fill a store page: the series line, the reading order and the prices come from your catalogue. Check each store\'s current terms for prices and formats.'], ['Author-publisher', 'Assistant'], NOTE),
    DC('reading_order_doc', 'Series Reading Order Page', 'Series reading order page for the back of a book', 'reading.title', [
        'Reading order page of {set:company}, dated {today}. Pen name: {col:reading.pen_name}. Series: {col:reading.series}.',
        'This is book {col:reading.book_number} of the series (0 means a standalone or a box set): {col:reading.title}, released {col:reading.release_date}.',
        'Book before it: {col:reading.prev_title}. Book after it: {col:reading.next_title}. Leave a line blank where there is none.',
        'Add this page to the back of the book so a reader who finished it knows what to read next.'], ['Author-publisher', 'Formatter'], NOTE),
    DC('press_kit_doc', 'Press Kit Page', 'Press kit page for a title', 'reading.title', [
        'Press kit page of {set:company}, dated {today}. {col:reading.title} by {col:reading.pen_name}.',
        'Part of {col:reading.series}, book {col:reading.book_number}, {col:reading.words} words and {col:reading.pages} pages, released {col:reading.release_date}.',
        'Available as ebook at {col:reading.price_ebook} and paperback at {col:reading.price_paperback}; audiobook at {col:reading.price_audio} where it exists. Prices are list prices and can differ by store.',
        'Contact the imprint {set:company} for review copies and interview requests.'], ['Author-publisher', 'Reviewer or blogger'], NOTE),
    DC('edition_list_doc', 'Edition List for Distribution', 'Edition list for a distribution request', 'editions.edition_id', [
        'Edition record of {set:company}, dated {today}, for a distribution request. Edition {col:editions.edition_id}: {col:editions.title}.',
        'Format: {col:editions.format}. Identifier: {col:editions.identifier}. List price: {col:editions.list_price}. Pages: {col:editions.pages}. Finished hours: {col:editions.hours}.',
        'Release date: {col:editions.release_date}. Status: {col:editions.status}. Royalty share: {col:editions.royalty_share} (check each store\'s current terms).',
        'Please confirm that the identifier, price and release date match your system before the files go live.'], ['Author-publisher', 'Distribution contact'], NOTE),
    DC('year_calendar_doc', 'Release Calendar Page', 'Release calendar page for one month', 'calmonths.month', [
        'Release calendar of {set:company}, dated {today}. Month starting {col:calmonths.month}.',
        'Releases: {col:calmonths.releases}. Pre-orders opening: {col:calmonths.preorders}. Promotions starting: {col:calmonths.promos}. Planned editions: {col:calmonths.editions}. Contractor deadlines: {col:calmonths.deadlines}.',
        'Entries in the month: {col:calmonths.entries}, against {set:load_limit} that you can carry. Load check: {col:calmonths.busy_flag}.',
        'Print one page for each month of the year and pin it where the team can see it.'], ['Author-publisher', 'Assistant'], NOTE),
    DC('preorder_text_doc', 'Pre-order Announcement', 'Pre-order announcement text', 'titles.title_id', [
        'Pre-order announcement of {set:company}, dated {today}. {col:titles.title} by {col:titles.pen_name}.',
        'The next book in {col:titles.series} (book {col:titles.series_order}) is on its way and arrives on {col:titles.release_date}. A pre-order is a sale taken before the release date, so you get the book the moment it is released.',
        'Pre-orders taken so far: {col:titles.preorders}. Days to release: {col:titles.days_to_release}.',
        'Share this text in your newsletter and on your social pages. Check each store\'s current terms before you quote a price.'], ['Author-publisher', 'Launch coordinator'], NOTE),
    DC('series_plan_doc', 'Series Plan Summary', 'Series plan summary for one book', 'steps.step_id', [
        'Series plan summary of {set:company}, dated {today}. Series: {col:steps.series}. Book {col:steps.book_number}: {col:steps.title}.',
        'Planned or actual release: {col:steps.planned_release}. Gap to the previous book: {col:steps.gap_days} days. Status: {col:steps.status}.',
        'Planned cost: {col:steps.planned_cost}. Expected read-through into the next book: {col:steps.expected_readthrough}, which is your own estimate of the readers who go on to buy the next book.',
        'Start the draft by {col:steps.start_date} to keep the date. Review the plan every quarter.'], ['Author-publisher', 'Assistant'], NOTE),
    DC('price_list_doc', 'Catalogue Price List', 'Catalogue price list line for one store', 'storeprices.price_id', [
        'Catalogue price list of {set:company}, dated {today}. Price line {col:storeprices.price_id}.',
        '{col:storeprices.title}, {col:storeprices.format}, in {col:storeprices.store}. Price in store currency: {col:storeprices.price} ({col:storeprices.currency}) at a rate of {col:storeprices.rate}, which is {col:storeprices.price_home} in home currency.',
        'List price: {col:storeprices.list_price}. Difference from the list price: {col:storeprices.diff_pct}. Check: {col:storeprices.matches}. Last checked on {col:storeprices.checked_on}.',
        'Store prices can change without notice. Check each store\'s current terms.'], ['Author-publisher', 'Assistant'], NOTE),
    DC('format_sheet_doc', 'Format Availability Sheet', 'Format availability sheet for a title', 'coverage.title', [
        'Format availability sheet of {set:company}, dated {today}. Title: {col:coverage.title} ({col:coverage.title_id}), status {col:coverage.status}.',
        'On sale or on the way (1 yes, 0 no): ebook {col:coverage.ebook}, paperback {col:coverage.paperback}, hardcover {col:coverage.hardcover}, large print {col:coverage.large_print}, audiobook {col:coverage.audiobook}.',
        'Formats missing: {col:coverage.formats_missing}. Best format to add: {col:coverage.best_format}, an estimate of {col:coverage.best_gain} extra copies a month.',
        'The estimate uses your own ratios of copies per ebook copy; it helps you decide, it is not a promise of sales.'], ['Author-publisher', 'Assistant'], NOTE),
    DC('handover_doc', 'Cover and Metadata Handover', 'Cover and metadata handover to the formatter', 'titles.title_id', [
        'Handover of {set:company}, dated {today}, to the cover designer and the formatter. Title: {col:titles.title}. Pen name: {col:titles.pen_name}.',
        'Series: {col:titles.series}, book {col:titles.series_order}. Genre: {col:titles.genre}. Words: {col:titles.words}. Pages: {col:titles.pages}. Release date: {col:titles.release_date}.',
        'Please put the pen name, the title and the series line on the cover and the title page, and send back the files before the release date. Open jobs on this title: {col:titles.open_jobs}.',
        'Reply to confirm the date. The identifier of each edition is in your edition list.'], ['Author-publisher', 'Formatter'], NOTE),
    DC('date_change_doc', 'Release Date Change Notice', 'Release date change notice to the team', 'calendar.entry_id', [
        'Notice of {set:company}, dated {today}. Entry {col:calendar.entry_id}: {col:calendar.kind} for {col:calendar.title}.',
        'The date is {col:calendar.date}, which is {col:calendar.days_from_today} days from today. Note: {col:calendar.note}.',
        'Conflict check: {col:calendar.conflict}. If the date moves, every contractor deadline and the pre-order date move with it.',
        'Please confirm that you have seen the new date and tell us at once if it breaks your plans.'], ['Author-publisher', 'Team member'], NOTE),
    DC('audit_doc', 'Catalogue Audit Report', 'Catalogue audit report for one edition', 'completeness.edition_id', [
        'Catalogue audit report of {set:company}, dated {today}. Edition {col:completeness.edition_id}: {col:completeness.title}, {col:completeness.format}, status {col:completeness.status}.',
        'Identifier: {col:completeness.identifier}. Identifier missing: {col:completeness.id_missing}. Identifier used twice: {col:completeness.id_dup}. Price missing: {col:completeness.price_missing}. Pages or hours missing: {col:completeness.pages_missing}. Release date missing: {col:completeness.date_missing}.',
        'Problems found: {col:completeness.problems}. Completeness: {col:completeness.completeness}. First problem: {col:completeness.issue}.',
        'Fix every problem before the files are uploaded.'], ['Author-publisher', 'Assistant'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('new_title', 'New Title Registered', 'titles', 'titles.release_date', [('Add the title to the Titles sheet with pen name, series and book number', -120), ('Enter words, pages and the planned release date', -120),
        ('Add the title to the Series Plan Steps sheet', -115), ('Book the editor, cover designer and formatter', -110), ('Add the production jobs to Contractor Deadlines', -105), ('Add the release to the Release Calendar', -100),
        ('Check the gap to the previous release', -100), ('Add the title to the Reading Order List', -90)]),
    CHK('new_edition', 'New Edition Added', 'editions', 'editions.release_date', [('Add the edition to the Editions sheet', -60), ('Enter the list price and the unit cost', -60), ('Assign the identifier and check it is not used twice', -55),
        ('Enter pages or finished hours', -55), ('Add the store prices to the Store Price List', -45), ('Check the Edition Completeness Check', -30), ('Add the edition to the Release Calendar', -30), ('Tell the assistant to upload the files', -14)]),
    CHK('preorder_run', 'Pre-order Setup', 'titles', 'titles.release_date', [('Confirm the release date against the Release Slot Finder', -75), ('Run the Pre-Order Readiness Check', -70), ('Upload the files and the cover', -67), ('Set the pre-order price on each store', -65),
        ('Open the pre-order and check each store page', -60), ('Tell the newsletter list and the launch coordinator', -58), ('Add the pre-order link to the back of the previous book', -55), ('Check the pre-order count every week', -30)]),
    CHK('release_week', 'Release Week', 'titles', 'titles.release_date', [('Check that the final files are live on every store', -7), ('Confirm the launch price with the web developer', -6), ('Confirm the ads with the ad specialist', -5),
        ('Send reviewer reminders', -4), ('Prepare the launch day newsletter', -3), ('Check the direct store page', -2), ('Update the also-by page of the previous book', -1), ('Check that the release date is clear of other entries', -7)]),
    CHK('release_day', 'Release Day', 'titles', 'titles.release_date', [('Check every store page shows the right title, price and cover', 0), ('Send the launch day newsletter', 0), ('Post the release on your social pages', 0), ('Check the series page links the new book', 0),
        ('Answer reviewers and readers', 1), ('Check the store prices again', 1), ('Thank the launch team', 7), ('Write what you learned in the Notes of the Release Calendar', 14)]),
    CHK('price_change', 'Price Change', 'promos', 'promos.start_date', [('Decide the new price and the end date', -14), ('Tell the ad specialist', -10), ('Tell the web developer to update the direct store', -7), ('Tell the newsletter list', -5), ('Update the price on each store', -1),
        ('Check each store page shows the new price', 0), ('Update the Store Price List check date', 1), ('Return the price on the end date', 7)]),
    CHK('format_added', 'Format Added', 'wishlist', 'wishlist.planned_release', [('Check the Planned Edition Go List', -90), ('Get the quote and book the contractor', -80), ('Send the files and the metadata handover', -60), ('Assign the identifier', -45),
        ('Add the edition to the Editions sheet', -40), ('Upload and check the proof', -20), ('Set the price on each store', -10), ('Add the new format to the also-by page', 0)]),
    CHK('monthly_audit', 'Monthly Catalogue Audit', 'calmonths', 'calmonths.month', [('Open the Edition Completeness Check and fix every problem', 1), ('Check the identifiers for duplicates', 1), ('Check the Store Price List for old checks', 3),
        ('Check the Release Gaps sheet', 4), ('Check the Calendar by Month for busy months', 5), ('Check Contractor Deadlines for late jobs', 5), ('Update the ebook copies a month in the Titles sheet', 7), ('Write the figures in your notes', 10)]),
    CHK('series_review', 'Quarterly Series Plan Review', 'steps', 'steps.planned_release', [('Check the planned date of each book against its gap', -90), ('Update the expected read-through from your own sales', -85), ('Check the planned cost against the last book', -80),
        ('Run the Series Reader Wait Check', -75), ('Run the Next Book Date Solver', -70), ('Move any book that is behind plan', -60), ('Tell the team about every change', -55), ('Write the new plan in the Series Plan Steps sheet', -50)]),
    CHK('retire_edition', 'Retiring an Edition', 'calendar', 'calendar.date', [('Decide the last day of sale', -30), ('Tell the assistant and the web developer', -28), ('Take the edition off the direct store', -7), ('Take it off each other store', 0), ('Mark the edition as retired in your notes', 1),
        ('Update the also-by page and the reading order', 3), ('Check that no store still sells it', 14), ('Keep the identifier on record', 14)]),
    CHK('metadata_check', 'Metadata Check Before Upload', 'editions', 'editions.release_date', [('Check the title, pen name and series line', -10), ('Check the identifier is filled and used once', -10), ('Check the list price and the price per store', -9), ('Check the pages or the finished hours', -9),
        ('Check the release date', -8), ('Check the description and the categories', -8), ('Check the cover file and the interior files', -7), ('Run the Identifier and Field Gap Finder', -7)]),
    CHK('year_end', 'Year-End Catalogue Review', 'calmonths', 'calmonths.month', [('Count the titles and editions at year end', 0), ('Check which formats are still missing', 3), ('Refresh the backlist prices', 5), ('Review the series plan for next year', 8),
        ('Plan next year\'s releases on the Release Calendar', 10), ('Spread any busy month', 12), ('Book next year\'s contractors', 15), ('Save a copy of the workbook', 20)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
DEAD = 'deadlines.phone'
messages = [
    M('f_files', 'Formatter: files due', 'deadlines', DEAD, 'Hello {contractor}, the files for {title} are due on {due_date}. Please confirm. {imprint}'),
    M('f_large', 'Formatter: add a large print', 'wishlist', 'wishlist.formatter_phone', 'Hello, please prepare a large print version of {title}, planned for {planned_release}. {imprint}'),
    M('f_fixed', 'Formatter: corrected files', 'deadlines', DEAD, 'Hello {contractor}, the corrected files for {title} are with you. Please check them by {due_date}. {imprint}'),
    M('c_due', 'Cover designer: cover due', 'deadlines', DEAD, 'Hello {contractor}, the cover for {title} is due on {due_date}. Please confirm. {imprint}'),
    M('c_wrap', 'Cover designer: print wrap', 'wishlist', 'wishlist.designer_phone', 'Hello, please prepare the print wrap for {title}, {format} planned for {planned_release}. {imprint}'),
    M('e_ready', 'Editor: manuscript ready', 'deadlines', DEAD, 'Hello {contractor}, the manuscript of {title} is ready from {start_date}. {imprint}'),
    M('e_edit', 'Editor: edit due', 'deadlines', DEAD, 'Hello {contractor}, your edit of {title} is due on {due_date}. Please confirm. {imprint}'),
    M('e_proof', 'Editor: proofread due', 'deadlines', DEAD, 'Hello {contractor}, the proofread of {title} is due on {due_date}. {imprint}'),
    M('n_audio', 'Narrator: audio files due', 'deadlines', DEAD, 'Hello {contractor}, the audio files for {title} are due on {due_date}. {imprint}'),
    M('n_studio', 'Narrator: studio dates', 'deadlines', DEAD, 'Hello {contractor}, please confirm your studio dates for {title} before {due_date}. {imprint}'),
    M('t_due', 'Translator: translation due', 'deadlines', DEAD, 'Hello {contractor}, the translation of {title} is due on {due_date}. {imprint}'),
    M('va_preorder', 'Assistant: upload the pre-order', 'titles', 'titles.assistant_phone', 'Hello, please upload {title} as a pre-order for {release_date}. {imprint}'),
    M('va_pages', 'Assistant: check the store pages', 'titles', 'titles.assistant_phone', 'Hello, please check the store pages of {title} today. {imprint}'),
    M('va_price', 'Assistant: update a store price', 'storeprices', 'storeprices.assistant_phone', 'Hello, please update the price of {title} on {store} to {price}. {imprint}'),
    M('va_ids', 'Assistant: identifiers missing', 'completeness', 'completeness.assistant_phone', 'Hello, the identifiers are missing for {missing_count} editions. Please add them today. {imprint}'),
    M('va_alsoby', 'Assistant: also-by page', 'titles', 'titles.assistant_phone', 'Hello, please add the also-by page to {title}. {imprint}'),
    M('lc_review', 'Launch coordinator: reviewer plan', 'titles', 'titles.launch_phone', 'Hello, {title} releases on {release_date}. Please confirm the reviewer plan. {imprint}'),
    M('lc_preorder', 'Launch coordinator: pre-order opens', 'calendar', 'calendar.launch_phone', 'Hello, the pre-order for {title} opens on {date}. Please confirm the plan. {imprint}'),
    M('ad_launch', 'Ad specialist: launch ads', 'titles', 'titles.ad_phone', 'Hello, {title} releases on {release_date}. Please plan the launch ads. {imprint}'),
    M('ad_promo', 'Ad specialist: promotion starts', 'promos', 'promos.ad_phone', 'Hello, a price promotion of {title} starts on {start_date}. Please plan the ads. {imprint}'),
    M('web_add', 'Web developer: add to the direct store', 'titles', 'titles.web_phone', 'Hello, please add {title} to the direct store before {release_date}. {imprint}'),
    M('web_price', 'Web developer: new price live', 'promos', 'promos.web_phone', 'Hello, the new price of {title} goes live on {start_date}: {promo_price}. {imprint}'),
    M('rights', 'Rights agent: available for a licence', 'titles', 'titles.rights_phone', 'Hello, {title} is available for a licence from {release_date}. {imprint}'),
    M('acct', 'Accountant: new edition cost', 'editions', 'editions.accountant_phone', 'Hello, the new edition {title}, {format}, has a unit cost of {unit_cost}. {imprint}'),
    M('printer', 'Printer: author-copy quote', 'titles', 'titles.printer_phone', 'Hello, please quote an author-copy run for {title}. {imprint}'),
    M('organiser', 'Event organiser: new titles', 'titles', 'titles.organiser_phone', 'Hello, new titles are available for your table from {release_date}: {title}. {imprint}'),
    M('au_launch', 'Author: release in days', 'titles', 'titles.author_phone', 'Reminder: {title} releases in {days_to_release} days, {open_jobs} steps are open. {imprint}'),
    M('au_gap', 'Author: two releases close together', 'gaps', 'gaps.author_phone', 'Reminder: {title} comes only {gap_days} days after the previous release. {imprint}'),
    M('au_ids', 'Author: editions without an identifier', 'completeness', 'completeness.author_phone', 'Reminder: {missing_count} editions have no identifier. {imprint}'),
    M('au_price', 'Author: a store price differs', 'storeprices', 'storeprices.author_phone', 'Reminder: the price of {title} on {store} differs from the list price: {price}. {imprint}'),
    M('au_series', 'Author: next book start date', 'steps', 'steps.author_phone', 'Reminder: the next book in {series} is due to start on {start_date}. {imprint}'),
    M('au_large', 'Author: large print planned', 'wishlist', 'wishlist.author_phone', 'Reminder: the {format} of {title} is planned for {planned_release}. {imprint}'),
    M('au_preorder', 'Author: pre-order closes soon', 'titles', 'titles.author_phone', 'Reminder: the pre-order of {title} ends on release day, {release_date}. {imprint}'),
    M('au_busy', 'Author: busy months ahead', 'calmonths', 'calmonths.author_phone', 'Reminder: {busy_count} busy months are ahead on the calendar. {imprint}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30), dashboard, insights
NOW = '{today}'
YR = '{range:titles.release_date},">"&EDATE({today},-12),{range:titles.release_date},"<="&{today}'
BOX = sr('Box set')
kpis = [
    KPI('Titles in the catalogue', 'COUNTA({range:titles.title_id})', 'int'),
    KPI('Titles released', 'COUNTIFS({range:titles.status},%s)' % RELD, 'int'),
    KPI('Titles in production or pre-order', 'COUNTIFS({range:titles.status},%s)+COUNTIFS({range:titles.status},%s)' % (PRE, PROD), 'int'),
    KPI('Editions live', 'COUNTIFS({range:editions.status},%s)' % LIVE, 'int'),
    KPI('Editions planned or in production', 'COUNTIFS({range:editions.status},%s)+COUNTIFS({range:editions.status},%s)' % (PLN, est('In production')), 'int'),
    KPI('Editions per title', 'IFERROR(ROUND(COUNTA({range:editions.edition_id})/COUNTA({range:titles.title_id}),1),0)', 'num'),
    KPI('Formats missing across released titles', 'SUMIFS({range:coverage.formats_missing},{range:coverage.status},%s)' % RELD, 'int'),
    KPI('Titles with all five formats', 'COUNTIFS({range:coverage.formats_missing},0,{range:coverage.status},%s)' % RELD, 'int'),
    KPI('Releases in the next 90 days', 'COUNTIFS({range:titles.release_date},">"&{today},{range:titles.release_date},"<="&({today}+90))', 'int'),
    KPI('Days to the next release', 'SUMPRODUCT(MIN(({range:titles.release_date}>{today})*{range:titles.release_date}+({range:titles.release_date}<={today})*999999))-{today}', 'int'),
    KPI('Release gaps under the minimum', 'COUNTIFS({range:gaps.under_min},%s)' % ck('Under the minimum'), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Smallest gap between releases ahead', 'IFERROR(SMALL({range:gaps.ahead_gap},1),0)', 'int'),
    KPI('Pre-orders taken so far', 'SUM({range:titles.preorders})', 'int'),
    KPI('Titles released, last 12 months', 'COUNTIFS(%s)' % YR, 'int'),
    KPI('Words published, last 12 months', 'SUMIFS({range:titles.words},%s)' % YR, 'int'),
    KPI('Average words per book', 'IFERROR(AVERAGEIFS({range:titles.words},{range:titles.series},"<>"&%s,{range:titles.status},%s),0)' % (BOX, RELD), 'int'),
    KPI('Average paperback list price', 'IFERROR(AVERAGEIFS({range:editions.list_price},{range:editions.format},%s,{range:editions.status},%s),0)' % (fmt('Paperback'), LIVE), 'money'),
    KPI('Average ebook list price', 'IFERROR(AVERAGEIFS({range:editions.list_price},{range:editions.format},%s,{range:editions.status},%s),0)' % (fmt('Ebook'), LIVE), 'money'),
    KPI('Average price per 100 pages, paperback', 'IFERROR(AVERAGEIFS({range:pricepage.price_per_page},{range:pricepage.format},%s),0)' % fmt('Paperback'), 'money'),
    KPI('Share of editions complete', 'IFERROR(COUNTIFS({range:completeness.problems},0)/COUNTA({range:completeness.edition_id}),0)', 'pct'),
    KPI('Store prices past the check limit', 'COUNTIFS({range:storeprices.check_flag},%s)' % ck('Check due'), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Contractor deadlines in the next 14 days', 'COUNTIFS({range:deadlines.due_date},">="&{today},{range:deadlines.due_date},"<="&({today}+14),{range:deadlines.delivered_on},"")', 'int'),
    KPI('Contractor deadlines overdue', 'COUNTIFS({range:deadlines.state},%s)' % ck('Open and late'), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Promotions starting in the next 30 days', 'COUNTIFS({range:promos.start_date},">="&{today},{range:promos.start_date},"<="&({today}+30))', 'int'),
    KPI('Titles on sale 18 months or more', 'COUNTIFS({range:titles.months_on_sale},">=18")', 'int'),
    KPI('Titles under 6 months on sale', 'COUNTIFS({range:titles.status},%s,{range:titles.months_on_sale},"<6")' % RELD, 'int'),
    KPI('Series plan books already released', 'IFERROR(COUNTIFS({range:steps.status},%s)/COUNTA({range:steps.step_id}),0)' % tok('planstatus', 'Released'), 'pct'),
    KPI('Planned books without a date', 'COUNTIFS({range:steps.status},%s,{range:steps.planned_release},"")' % tok('planstatus', 'Planned'), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Average gap between releases, days', 'IFERROR(ROUND(AVERAGE({range:gaps.gap_days}),0),0)', 'int'),
    KPI('Share of titles with an audiobook', 'IFERROR(SUM({range:coverage.audiobook})/COUNTA({range:coverage.title}),0)', 'pct'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Catalogue Dashboard", "kpis": kpis,
    "monthly": {"title": "Releases, pre-orders, promotions and deadlines by month", "date": "calmonths.month", "series": [
        {"label": "Releases", "sum": "calmonths.releases", "date": "calmonths.month"}, {"label": "Pre-orders opening", "sum": "calmonths.preorders", "date": "calmonths.month"},
        {"label": "Promotions starting", "sum": "calmonths.promos", "date": "calmonths.month"}, {"label": "Contractor deadlines", "sum": "calmonths.deadlines", "date": "calmonths.month"}]},
    "breakdowns": [{"title": "Titles by series", "by": "titles.series", "agg": "count"}, {"title": "Editions by format", "by": "editions.format", "agg": "count"},
                   {"title": "Editions by status", "by": "editions.status", "agg": "count"}, {"title": "Promotions by kind", "by": "promos.kind", "agg": "count"}]}
CH = lambda *a, **k: CHART(*a, **k)
insights = {"filters": [{"label": "Pen name", "list": "penname"}, {"label": "Series", "list": "series"}, {"label": "Format", "list": "format"}],
    "gauges": [
        {"title": "Editions with identifier and price", "num": AGG('count', 'completeness', where=[('has_core', '=', 1)]), "den": AGG('count', 'completeness')},
        {"title": "Store prices checked in time", "num": AGG('count', 'storeprices', where=[('days_since', '<=', '{set:price_check_days}')]), "den": AGG('count', 'storeprices')},
        {"title": "Contractor deadlines met on time", "num": AGG('count', 'deadlines', where=[('state', '=', ck('Delivered on time'))]), "den": AGG('count', 'deadlines', where=[('delivered_on', '>', 0)])},
        {"title": "Release gaps at or above the minimum", "num": AGG('count', 'gaps', where=[('gap_days', '>=', '{set:min_release_gap_days}')]), "den": AGG('count', 'gaps', where=[('gap_days', '>', 0)])},
        {"title": "Planned books with a date", "num": AGG('count', 'steps', where=[('status', '=', tok('planstatus', 'Planned')), ('planned_release', '>', 0)]), "den": AGG('count', 'steps', where=[('status', '=', tok('planstatus', 'Planned'))])},
        {"title": "Titles with ebook and paperback", "num": AGG('count', 'coverage', where=[('core_formats', '=', 1)]), "den": AGG('count', 'coverage')}],
    "charts": [
        CH('Titles by series', 'bar', 'titles.series', [AGG('count', 'titles', label='Titles')]),
        CH('Titles by pen name', 'bar', 'titles.pen_name', [AGG('count', 'titles', label='Titles')]),
        CH('Titles by genre', 'bar', 'titles.genre', [AGG('count', 'titles', label='Titles')]),
        CH('Titles by status', 'bar', 'titles.status', [AGG('count', 'titles', label='Titles')]),
        CH('Editions by format', 'bar', 'editions.format', [AGG('count', 'editions', label='Editions')]),
        CH('Editions by status', 'bar', 'editions.status', [AGG('count', 'editions', label='Editions')]),
        CH('Words by series', 'bar', 'titles.series', [AGG('sum', 'titles', 'titles.words', label='Words')]),
        CH('Releases per month', 'column', 'month', [AGG('count', 'titles', date='titles.release_date', label='Releases')]),
        CH('Planned cost by series', 'bar', 'steps.series', [AGG('sum', 'steps', 'steps.planned_cost', label='Planned cost')]),
        CH('Series plan steps by status', 'bar', 'steps.status', [AGG('count', 'steps', label='Books')]),
        CH('Average list price by format', 'bar', 'editions.format', [AGG('avg', 'editions', 'editions.list_price', label='Average list price')]),
        CH('Average pages by format', 'bar', 'editions.format', [AGG('avg', 'editions', 'editions.pages', label='Average pages')]),
        CH('Wish list by format', 'bar', 'wishlist.format', [AGG('count', 'wishlist', label='Planned editions')]),
        CH('Wish list by status', 'bar', 'wishlist.status', [AGG('count', 'wishlist', label='Planned editions')]),
        CH('Promotions per month', 'line', 'month', [AGG('count', 'promos', date='promos.start_date', label='Promotions')]),
        CH('Promotions by kind', 'bar', 'promos.kind', [AGG('count', 'promos', label='Promotions')]),
        CH('Contractor deadlines per month', 'column', 'month', [AGG('count', 'deadlines', date='deadlines.due_date', label='Deadlines')]),
        CH('Deadlines by contractor', 'bar', 'deadlines.contractor', [AGG('count', 'deadlines', label='Deadlines')]),
        CH('Store price checks by store', 'bar', 'storeprices.store', [AGG('count', 'storeprices', label='Store prices')]),
        CH('Store price rows by currency', 'bar', 'storeprices.currency', [AGG('count', 'storeprices', label='Store prices')]),
        CH('Calendar entries per month', 'column', 'month', [AGG('count', 'calendar', date='calendar.date', label='Entries')]),
        CH('Calendar entries by kind', 'bar', 'calendar.kind', [AGG('count', 'calendar', label='Entries')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Release slot finder", "why": "a proposed date is tested against every release, promotion and deadline, with the earliest clear date and a verdict", "where": "Release Slot Finder"},
    {"name": "Release calendar with conflicts", "why": "releases, pre-orders, promotions and contractor deadlines in one list, each flagged when it breaks your minimum gap", "where": "Release Calendar"},
    {"name": "Series timeline builder", "why": "type a first date, a gap and a cost: every book gets a date, the series a total cost and a verdict on plan", "where": "Series Timeline Builder"},
    {"name": "Next book date solver", "why": "your own gaps between the last four books give the next release and the day you must start the draft", "where": "Next Book Date Solver"},
    {"name": "Edition coverage ranker", "why": "titles missing a format are ranked by the copies a month it would add, with the format to add first", "where": "Edition Coverage Ranker"},
    {"name": "Pre-order readiness check", "why": "the jobs of a title are set against the last safe upload date, so a pre-order is never opened on late files", "where": "Pre-Order Readiness Check"},
    {"name": "Price consistency checker", "why": "editions of one format in a series are held against the series median price, with the ones to align named", "where": "Price Consistency Checker"},
    {"name": "Planned edition go list", "why": "every planned edition ranked by royalty a month per unit of cost, with months to earn back and a do now, next quarter or drop verdict", "where": "Planned Edition Go List"},
    {"name": "Format launch order", "why": "the copies and royalty a month a format adds to a series, against what it costs to make", "where": "Format Launch Order"},
    {"name": "Identifier and field gap finder", "why": "missing or duplicated identifiers, prices, pages and dates counted, with the first five problems to fix before upload", "where": "Identifier and Field Gap Finder"},
    {"name": "Series reader wait check", "why": "the gap between books and the months readers wait for the next one, set against the wait you accept", "where": "Series Reader Wait Check"}]
competitors = [
    {"what": "free catalogue spreadsheet templates", "lacks": "list titles and prices but never check identifiers, price differences between stores or the gap between two releases"},
    {"what": "subscription store dashboards", "lacks": "show each store's own sales only, with no series plan, no release calendar and a fee that rises with your income"},
    {"what": "generic content calendar templates", "lacks": "have no release gap rule, no pre-order window, no contractor deadlines and no link to editions or formats"},
    {"what": "single-sheet book launch plans", "lacks": "plan one launch only, with no catalogue, no format coverage and no view of a second release that lands too close"},
    {"what": "generic project trackers", "lacks": "know tasks and dates but not titles, editions, series order, pen names or what an extra format would add"}]
guide = [
    'Open Start and type your imprint name and your own limits in the yellow cells: the smallest gap between two releases, how many calendar entries you can carry in a month and how old a store price check may be.',
    'Write every title in Titles: pen name, series, book number, words, pages, release date, status and the ebook copies a month from your sales sheet. Months on sale, days to release and open jobs fill in by themselves.',
    'Write every edition in Editions: format, list price, unit cost, royalty share (check each store\'s current terms), identifier and pages or finished hours. The royalty per copy fills in.',
    'Keep the series in Series and Series Plan Steps: one row per book with its planned or actual release, planned cost and the read-through you expect into the next book.',
    'Add the production jobs to Contractor Deadlines and the price promotions to Promotion Dates. They appear on the Release Calendar with the dates that matter.',
    'Fill the Release Calendar with releases, pre-order openings, planned editions, promotions and deadlines. The conflict check flags two releases closer than your smallest gap.',
    'Check Release Gaps, Calendar by Month and Edition Completeness Check each month: they show gaps under the minimum, busy months and editions with a missing or duplicated identifier.',
    'Enter the price on each store in Store Price List and the day you checked it. The sheet shows prices that differ from the list price and checks that are too old.',
    'Use Title Format Coverage, Format Wish List and Price per Page to decide which format to add next and what a print price should be.',
    f'Use the {len(tools)} tools to test a release date, build a series timeline, find the date to start the next book, rank missing formats and check that a pre-order is safe.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Catalogue Dashboard and the charts every week. A first-time author with one to three books can use most sheets with a few rows; a small press can read the pen-name column as an author column.',
    'To replace the demo data: clear the yellow cells of the blank copy, paste your own rows and keep the formulas as they are. Nothing needs a macro or a login.']
listing = {"title": "Author Catalogue, Series Plan and Release Calendar Excel Template: Editions, Pre-order Planner, Price Checks, Format Wish List",
    "headline": "Every title, edition and release date in one workbook, with conflicts flagged",
    "tags": ["author catalogue", "release calendar", "series planner", "self publishing", "book launch", "excel template", "indie author", "pre-order planner", "edition tracker", "publishing business", "price checker", "release schedule", "author business"],
    "description": ("Run the catalogue side of an author and self-publisher business in one Excel workbook. Built for an independent author who publishes under one or two pen names, often with a part-time assistant and freelancers paid per job, and for a small press that reads the pen-name column as an author column. "
        "Titles and Editions hold every book and every format with its list price, unit cost, royalty share, identifier, pages or finished hours and status. Series Plan Steps keeps the planned books of each series with planned release, planned cost and the read-through you expect into the next book.\n\n"
        "The Release Calendar puts releases, pre-order openings, planned editions, price promotions and contractor deadlines in one list and flags two releases closer than your smallest gap. Release Gaps, Calendar by Month, Edition Completeness Check, Store Price List, Title Format Coverage, Format Wish List and Price per Page show gaps, busy months, missing or duplicated identifiers, store prices that differ from the list price, formats still missing and print cost shares. "
        f"{len(tools)} tools answer the questions an author asks every week: is this release date free, when does each book of a series land, when must the next book start, which missing format adds the most copies, is the pre-order safe, are the prices consistent and which planned edition should be made first. Every tool ends in a plain verdict and a what-if table.\n\n"
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to the assistant, editors, the cover designer, the formatter, narrators, the translator, the launch coordinator, the ad specialist, the web developer, the rights agent, the printer and yourself. "
        "This is part one of an eight-workbook suite for the Author and Self-Publisher Business. A standard .xlsx workbook with no macros, no login and one flat price, with a demo copy full of sample data to explore first. It helps you keep track of your catalogue and plan your releases; it makes no promise of sales or income. Royalty shares, delays and tax points are your own numbers: check each store's current terms and confirm any tax point with your adviser."),
    "features": ["Release calendar with conflict flags", "Release slot finder with a verdict", "Series plan with dates and costs", "Edition register with identifier checks", "Store price list with age checks",
                 "Format coverage ranked by copies added", "Pre-order readiness check", "Planned edition go list", f"{len(tools)} decision tools with what-if tables", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
assert len(listing['title']) <= 140 and len(listing['headline']) <= 80 and all(len(t) <= 20 for t in listing['tags']) and len(listing['tags']) == 13 and 900 <= len(listing['description']) <= 2500, (len(listing['title']), len(listing['headline']), len(listing['description']))
HINTS = {
 'slot': 'Type a proposed release date: it is set against every release, promotion and deadline, with the neighbours, the earliest clear date and a verdict.',
 'timeline': 'Type the first release date, books planned, gap and cost of a book: see each release date, the last date, the total cost and whether the series is on plan.',
 'nextbook': 'Pick a series: your own average gap between its last four releases gives the expected next release; your writing pace gives the date to start by.',
}
for _t in tables + tools:
    if _t['key'] in HINTS: _t['hint'] = HINTS[_t['key']]
TAGLINE = 'Every title, edition and release date in one workbook, conflicts flagged'
assert len(TAGLINE) <= 80
s = spec(id=f'{SUITE}-p1', slug='author-publisher-catalogue', profession='Author and Self-Publisher Business', name='Catalogue, Series Plan and Releases', tagline=TAGLINE, price_usd=29,
         colors={"primary": "#2B3A55", "accent": "#CE7777"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 1, "of": 8, "focus": "Catalogue, series plan and releases"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'au1.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
