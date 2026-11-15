"""Author and Self-Publisher suite part 1: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au1_lists import *
import au1_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(k, label, f, formula, w=12, **kw): return CALC(k, label, f, formula, w, **kw)
def PHC(k, label, who): return CA(k, label, 'text', '"%s"' % D.PH[who], 18)
def IMPRINT(): return CA('imprint', 'Imprint', 'text', '{set:company}', 22)
def INM(rng_, col): return '{range:%s},">="&%s,{range:%s},"<"&EDATE(%s,1)' % (rng_, col, rng_, col)


settings = [
    S('company', 'Your imprint name', 'text', COMPANY),
    S('min_release_gap_days', 'Smallest gap between two releases, days (your own number)', 'int', MIN_RELEASE_GAP_DAYS),
    S('load_limit', 'Calendar entries a month you can carry (your own number)', 'int', 6),
    S('price_check_days', 'Days before a store price check is old', 'int', 180),
    S('price_tolerance_pct', 'Price difference you accept, share of list price', 'pct', 0.10),
    S('backlist_months', 'Months on sale before a title counts as backlist', 'int', 36),
    S('preorder_max_days', 'Longest pre-order window you want, days', 'int', 90),
    S('upload_lead_days', 'Days to upload files before a pre-order opens', 'int', 5),
    S('print_cost_share_max', 'Highest print cost as a share of the list price', 'pct', 0.45),
    S('reader_wait_months', 'Months readers will wait for the next book (your own number)', 'int', 14),
    S('draft_lead_days', 'Days from starting a draft to its release (your own number)', 'int', 200),
    S('ratio_ebook', 'Copies a relaunched ebook adds, per current ebook copy', 'num', 0.10),
    S('ratio_paperback', 'Paperback copies per ebook copy (your own number)', 'num', 0.24),
    S('ratio_hardcover', 'Hardcover copies per ebook copy (your own number)', 'num', 0.035),
    S('ratio_large_print', 'Large print copies per ebook copy (your own number)', 'num', 0.05),
    S('ratio_audio', 'Audiobook copies per ebook copy (your own number)', 'num', 0.08),
    S('payback_limit_months', 'Months a new edition should take to earn back its cost', 'int', 12),
]
assert 3 <= len(settings) <= 20

MS = 'DATE(YEAR({today}),MONTH({today}),1)'
tables = []
# ---------------------------------------------------------------- 1 titles
tables.append(T('titles', 'Titles', 'Catalogue of titles',
    'One row per title: pen name, series, genre, words, pages, release date, status and the ebook copies a month; the months on sale, days to release, open jobs and message fields fill in by themselves.', [
    C('title_id', 'Title ID', 'text', 10, required=True), C('title', 'Title', 'text', 28), LST('pen_name', 'Pen name', 'penname', 16), LST('series', 'Series', 'series', 20), C('series_order', 'Book no.', 'int', 8),
    LST('genre', 'Genre', 'genre', 14), C('words', 'Words', 'int', 10), C('pages', 'Pages', 'int', 8), C('release_date', 'Release date', 'date', 12), LST('status', 'Status', 'tstatus', 13),
    C('exclusive', 'Exclusive (page reads)', 'bool', 10), C('preorders', 'Pre-orders', 'int', 10), C('royalty_before', 'Royalties before this workbook', 'money', 14), C('ebook_copies_month', 'Ebook copies a month', 'int', 11),
    CA('months_on_sale', 'Months on sale', 'num', 'IF({col:release_date}>{today},0,ROUND(({today}-{col:release_date})/30.4,1))', 9),
    CA('days_to_release', 'Days to release', 'int', '{col:release_date}-{today}', 9),
    CA('open_jobs', 'Open jobs', 'int', 'COUNTIFS({range:deadlines.title},{col:title},{range:deadlines.delivered_on},"")', 8),
    CA('series_key', 'Series key', 'text', '{col:series}&"|"&{col:series_order}', 14), IMPRINT(),
    PHC('assistant_phone', 'Assistant phone', 'assistant'), PHC('launch_phone', 'Launch coordinator phone', 'launch'), PHC('ad_phone', 'Ad specialist phone', 'ad'), PHC('web_phone', 'Web developer phone', 'web'),
    PHC('rights_phone', 'Rights agent phone', 'rights'), PHC('printer_phone', 'Printer phone', 'printer'), PHC('organiser_phone', 'Event organiser phone', 'organiser'), PHC('author_phone', 'Author phone', 'author')],
    D.titles_d(), 60, [A('status', '= ' + tst('Pre-order'), 'warn'), A('status', '= ' + tst('In production'), 'warn'), A('open_jobs', '> 0', 'warn')]))
# ---------------------------------------------------------------- 2 editions
tables.append(T('editions', 'Editions', 'Editions by format',
    'One row per edition (a title in one format): list price, unit cost, royalty share, identifier, pages or hours and status; the royalty per copy and the series fill in by themselves.', [
    C('edition_id', 'Edition ID', 'text', 10, required=True), REF('title_id', 'Title ID', 'titles.title_id', 10), REF('title', 'Title', 'titles.title', 28), LST('format', 'Format', 'format', 12),
    C('list_price', 'List price', 'money', 11), C('unit_cost', 'Unit cost', 'money', 11), C('royalty_share', 'Royalty share', 'pct', 10), C('identifier', 'Identifier', 'text', 16), C('pages', 'Pages', 'int', 8),
    C('hours', 'Finished hours', 'num', 9), C('release_date', 'Release date', 'date', 12), LST('status', 'Status', 'estatus', 13),
    CA('royalty_per_copy', 'Royalty per copy', 'money', 'ROUND({col:list_price}*{col:royalty_share}-{col:unit_cost},2)', 11),
    CA('series', 'Series', 'text', LKT('titles.series', 'titles.title_id', 'title_id'), 20), PHC('accountant_phone', 'Accountant phone', 'accountant'), IMPRINT()],
    D.editions_d(), 120, [A('status', '= ' + est('Planned'), 'warn'), A('status', '= ' + est('Pre-order'), 'good')]))
# ---------------------------------------------------------------- 3 series
tables.append(T('series', 'Series', 'Series and books planned',
    'One row per series: the pen name and the number of books you plan; the series plan steps below hold the dates.', [
    LST('series', 'Series', 'series', 22, required=True), C('pen_name', 'Pen name', 'text', 22), C('books_planned', 'Books planned', 'int', 12)],
    D.series_d(), 50))
# ---------------------------------------------------------------- 4 series plan steps
PREV = 'SUMPRODUCT(MAX(({range:steps.series}={col:series})*({range:steps.book_number}={col:book_number}-1)*{range:steps.planned_release}))'
tables.append(T('steps', 'Series Plan Steps', 'Series plan, book by book',
    'One row per book of a series, written or planned: release date, planned cost, expected read-through into the next book and status; the gap to the previous book fills in by itself.', [
    C('step_id', 'Step ID', 'text', 9, required=True), LST('series', 'Series', 'series', 20), C('book_number', 'Book no.', 'int', 8), C('title', 'Title', 'text', 28), C('planned_release', 'Planned or actual release', 'date', 13),
    C('planned_cost', 'Planned cost', 'money', 12), C('expected_readthrough', 'Expected read-through into next book', 'pct', 12), LST('status', 'Status', 'planstatus', 13),
    CA('gap_days', 'Gap to previous book, days', 'int', 'IF(OR({col:planned_release}=0,{col:book_number}<2),"",IF(%s=0,"",{col:planned_release}-%s))' % (PREV, PREV), 12),
    CA('start_date', 'Start the draft by', 'date', 'IF({col:planned_release}>0,{col:planned_release}-{set:draft_lead_days},"")', 12), IMPRINT(), PHC('author_phone', 'Author phone', 'author')],
    D.steps_d(), 80, [A('status', '= ' + tok('planstatus', 'Planned'), 'warn'), A('gap_days', '< {set:min_release_gap_days}', 'bad')]))
# ---------------------------------------------------------------- 5 formats, 6 stores
tables.append(T('formats', 'Formats', 'Formats, royalty share and base cost',
    'One row per format: the usual royalty share (check each store\'s current terms) and the base cost of one copy; used for planned editions.', [
    LST('format', 'Format', 'format', 16, required=True), C('royalty_share', 'Royalty share', 'pct', 12), C('base_cost', 'Base cost', 'money', 12)], D.formats_d(), 50))
tables.append(T('stores', 'Stores', 'Stores, royalty share and payment delay',
    'One row per sales channel: the usual royalty share (check each store\'s current terms) and the days after month end that the store pays.', [
    LST('store', 'Store', 'store', 20, required=True), C('royalty_share', 'Royalty share', 'pct', 12), C('delay_days', 'Payment delay, days', 'int', 12)], D.stores_d(), 50))
# ---------------------------------------------------------------- 7 store price list
EDL = lambda c: LKT('editions.' + c, 'editions.edition_id', 'edition_id')
tables.append(T('storeprices', 'Store Price List', 'Store price list with checks',
    'One row per edition and store: the store page price, the rate to home currency and the day you checked it; the converted price, the difference from list price and days since the check fill in.', [
    C('price_id', 'Price ID', 'text', 9, required=True), REF('edition_id', 'Edition ID', 'editions.edition_id', 10), LST('store', 'Store', 'store', 18), LST('currency', 'Currency', 'currency', 16),
    C('price', 'Price in store currency', 'money', 12), C('rate', 'Rate to home currency', 'num', 10), C('checked_on', 'Price checked on', 'date', 12),
    CA('title', 'Title', 'text', EDL('title'), 26), CA('format', 'Format', 'text', EDL('format'), 12), CA('list_price', 'List price', 'money', LKN('editions.list_price', 'editions.edition_id', 'edition_id'), 10),
    CA('price_home', 'Price in home currency', 'money', 'ROUND({col:price}*{col:rate},2)', 12),
    CA('diff_pct', 'Difference from list price', 'pct', 'IF({col:list_price}>0,{col:price_home}/{col:list_price}-1,0)', 11),
    CA('matches', 'Price check', 'text', 'IF(ABS({col:diff_pct})<={set:price_tolerance_pct},%s,%s)' % (ck('Price matches'), ck('Price differs')), 14),
    CA('days_since', 'Days since the check', 'int', '{today}-{col:checked_on}', 9),
    CA('check_flag', 'Check due', 'text', 'IF({col:days_since}>{set:price_check_days},%s,%s)' % (ck('Check due'), ck('Checked in time')), 14),
    CA('title_age', 'Title months on sale', 'num', 'IFERROR(INDEX({range:titles.months_on_sale},MATCH(INDEX({range:editions.title_id},MATCH({col:edition_id},{range:editions.edition_id},0)),{range:titles.title_id},0)),0)', 10),
    CA('backlist_key', 'Backlist check age', 'num', 'IF({col:title_age}>={set:backlist_months},{col:days_since}+VALUE(RIGHT({col:price_id},3))/10000,"")', 10),
    PHC('assistant_phone', 'Assistant phone', 'assistant'), PHC('author_phone', 'Author phone', 'author'), IMPRINT()],
    D.storeprices_d(), 150, [A('matches', '= ' + ck('Price differs'), 'bad'), A('check_flag', '= ' + ck('Check due'), 'warn')]))
# ---------------------------------------------------------------- 8 release calendar
REL = ckd('Release')
tables.append(T('calendar', 'Release Calendar', 'Release calendar with conflicts',
    'One row per dated entry: a release, pre-order opening, promotion start, contractor deadline or planned edition; the days from today and the conflict flag against your minimum gap fill in.', [
    C('entry_id', 'Entry ID', 'text', 9, required=True), C('date', 'Date', 'date', 12), LST('kind', 'Entry kind', 'ckind', 18), REF('title', 'Title', 'titles.title', 28), C('note', 'Note', 'text', 34),
    CA('days_from_today', 'Days from today', 'int', '{col:date}-{today}', 9),
    CA('conflict', 'Conflict check', 'text', 'IF({col:kind}=%s,IF(COUNTIFS({range:calendar.kind},%s,{range:calendar.date},">"&({col:date}-{set:min_release_gap_days}),{range:calendar.date},"<"&({col:date}+{set:min_release_gap_days}))>1,%s,%s),'
       'IF(COUNTIFS({range:calendar.date},">="&({col:date}-3),{range:calendar.date},"<="&({col:date}+3))>=4,%s,%s))' % (REL, REL, ck('Too close to a release'), ck('Clear'), ck('Busy week'), ck('Clear')), 18),
    PHC('launch_phone', 'Launch coordinator phone', 'launch'), IMPRINT()],
    D.calendar_d(), 100, [A('conflict', '= ' + ck('Too close to a release'), 'bad'), A('conflict', '= ' + ck('Busy week'), 'warn')]))
# ---------------------------------------------------------------- 9 release gaps
TLR = lambda c: LKT('titles.' + c, 'titles.title', 'title')
tables.append(T('gaps', 'Release Gaps', 'Release gaps by pen name',
    'One row per title: the previous release by the same pen name, the gap in days and a check against your smallest gap; fills in from the Titles sheet.', [
    REF('title', 'Title', 'titles.title', 28, required=True), CA('pen_name', 'Pen name', 'text', TLR('pen_name'), 16), CA('release_date', 'Release date', 'date', LKN('titles.release_date', 'titles.title', 'title'), 12),
    CA('prev_release', 'Previous release, same pen name', 'date', 'IF(SUMPRODUCT(MAX(({range:titles.pen_name}={col:pen_name})*({range:titles.release_date}<{col:release_date})*{range:titles.release_date}))=0,"",'
       'SUMPRODUCT(MAX(({range:titles.pen_name}={col:pen_name})*({range:titles.release_date}<{col:release_date})*{range:titles.release_date})))', 12),
    CA('gap_days', 'Gap, days', 'int', 'IF({col:prev_release}="","",{col:release_date}-{col:prev_release})', 8),
    CA('under_min', 'Gap check', 'text', 'IF({col:gap_days}="",%s,IF({col:gap_days}<{set:min_release_gap_days},%s,%s))' % (ck('First release'), ck('Under the minimum'), ck('Above the minimum')), 16),
    CA('ahead_gap', 'Gap of a release ahead, days', 'int', 'IF(AND({col:gap_days}<>"",{col:release_date}>{today}),{col:gap_days},"")', 10), PHC('author_phone', 'Author phone', 'author'), IMPRINT()],
    D.gaps_d(), 60, [A('under_min', '= ' + ck('Under the minimum'), 'bad')]))
# ---------------------------------------------------------------- 10 edition completeness check
ED_ = lambda c: LKN('editions.' + c, 'editions.edition_id', 'edition_id')
PLN = est('Planned')
tables.append(T('completeness', 'Edition Completeness Check', 'Missing or duplicated edition fields',
    'One row per edition: whether identifier, price, pages or hours and release date are filled and whether an identifier is used twice; the completeness share and first problem fill in.', [
    REF('edition_id', 'Edition ID', 'editions.edition_id', 10, required=True), CA('title', 'Title', 'text', EDL('title'), 26), CA('format', 'Format', 'text', EDL('format'), 12), CA('status', 'Status', 'text', EDL('status'), 13),
    CA('identifier', 'Identifier', 'text', EDL('identifier'), 16),
    CA('id_missing', 'Identifier missing', 'int', 'IF({col:status}=%s,0,IF({col:identifier}="",1,0))' % PLN, 9),
    CA('id_dup', 'Identifier duplicated', 'int', 'IF(OR({col:status}=%s,{col:identifier}=""),0,IF(COUNTIF({range:editions.identifier},{col:identifier})>1,1,0))' % PLN, 9),
    CA('price_missing', 'Price missing', 'int', 'IF({col:status}=%s,0,IF(%s<=0,1,0))' % (PLN, ED_('list_price')), 9),
    CA('pages_missing', 'Pages or hours missing', 'int', 'IF({col:status}=%s,0,IF({col:format}=%s,IF(%s<=0,1,0),IF(%s<=0,1,0)))' % (PLN, fmt('Audiobook'), ED_('hours'), ED_('pages')), 9),
    CA('date_missing', 'Release date missing', 'int', 'IF({col:status}=%s,0,IF(%s=0,1,0))' % (PLN, ED_('release_date')), 9),
    CA('problems', 'Problems', 'int', '{col:id_missing}+{col:id_dup}+{col:price_missing}+{col:pages_missing}+{col:date_missing}', 8),
    CA('completeness', 'Completeness', 'pct', '1-{col:problems}/5', 10),
    CA('has_core', 'Identifier and price filled', 'int', 'IF(AND({col:identifier}<>"",{col:price_missing}=0),1,0)', 9),
    CA('issue', 'First problem', 'text', 'IF({col:status}=%s,%s,IF({col:id_missing}=1,%s,IF({col:id_dup}=1,%s,IF({col:price_missing}=1,%s,IF({col:pages_missing}=1,%s,IF({col:date_missing}=1,%s,%s))))))' % (
        PLN, ck('Planned, not checked'), ck('Identifier missing'), ck('Identifier duplicated'), ck('Price missing'), ck('Pages or hours missing'), ck('Release date missing'), ck('No problem')), 22),
    CA('pscore', 'Problem score', 'int', 'IF({col:problems}>0,1000-VALUE(RIGHT({col:edition_id},4)),0)', 8),
    CA('problem_rank', 'Problem rank', 'int', 'IF({col:problems}>0,COUNTIFS({range:completeness.pscore},">"&{col:pscore})+1,"")', 8),
    CA('missing_count', 'Editions without an identifier', 'int', 'SUM({range:completeness.id_missing})', 9), PHC('author_phone', 'Author phone', 'author'), PHC('assistant_phone', 'Assistant phone', 'assistant'), IMPRINT()],
    D.completeness_d(), 150, [A('problems', '> 0', 'bad'), A('completeness', '= 1', 'good')]))
# ---------------------------------------------------------------- 11 pipeline
tables.append(T('pipeline', 'Pipeline by Status and Format', 'Editions by status and format',
    'One row per edition status and format: how many editions and their average list price; fills in from the Editions sheet.', [
    LST('status', 'Edition status', 'estatus', 14, required=True), LST('format', 'Format', 'format', 14),
    CA('editions', 'Editions', 'int', 'COUNTIFS({range:editions.status},{col:status},{range:editions.format},{col:format})', 9),
    CA('avg_price', 'Average list price', 'money', 'IFERROR(AVERAGEIFS({range:editions.list_price},{range:editions.status},{col:status},{range:editions.format},{col:format}),0)', 11)],
    D.pipeline_d(), 50))
# ---------------------------------------------------------------- 12 format wish list
WRAT = ('IF({col:format}=%s,{set:ratio_ebook},IF({col:format}=%s,{set:ratio_paperback},IF({col:format}=%s,{set:ratio_hardcover},IF({col:format}=%s,{set:ratio_large_print},{set:ratio_audio}))))'
        % (fmt('Ebook'), fmt('Paperback'), fmt('Hardcover'), fmt('Large print')))
tables.append(T('wishlist', 'Format Wish List', 'Planned editions and their payback',
    'One row per edition you plan to add: format, planned price, release, cost and priority; the copies a month, the royalty a month, the months to earn back the cost and a verdict fill in by themselves.', [
    C('wish_id', 'Wish ID', 'text', 9, required=True), REF('title', 'Title', 'titles.title', 28), LST('format', 'Format', 'format', 12), C('planned_price', 'Planned price', 'money', 11), C('planned_release', 'Planned release', 'date', 12),
    C('planned_cost', 'Planned cost', 'money', 11), LST('priority', 'Priority', 'wprio', 9), LST('status', 'Status', 'wstatus', 11), C('note', 'Note', 'text', 34),
    CA('ebook_copies', 'Ebook copies a month', 'int', LKN('titles.ebook_copies_month', 'titles.title', 'title'), 10),
    CA('copies_month', 'Expected copies a month', 'num', 'ROUND({col:ebook_copies}*%s,1)' % WRAT, 10),
    CA('royalty_copy', 'Royalty per copy', 'money', 'ROUND({col:planned_price}*%s-%s,2)' % (LKN('formats.royalty_share', 'formats.format', 'format'), LKN('formats.base_cost', 'formats.format', 'format')), 10),
    CA('royalty_month', 'Royalty a month', 'money', 'ROUND({col:copies_month}*{col:royalty_copy},2)', 10),
    CA('months_to_earn', 'Months to earn back the cost', 'num', 'IF({col:royalty_month}>0,ROUND({col:planned_cost}/{col:royalty_month},1),99)', 10),
    CA('go_verdict', 'Verdict', 'text', 'IF({col:months_to_earn}<={set:payback_limit_months},%s,IF({col:months_to_earn}<=2*{set:payback_limit_months},%s,%s))' % (ck('Do now'), ck('Next quarter'), ck('Drop')), 13),
    CA('score', 'Go score', 'num', 'IF({col:planned_cost}>0,{col:royalty_month}/{col:planned_cost},0)-VALUE(RIGHT({col:wish_id},2))/1000000', 9),
    CA('rank', 'Rank', 'int', 'COUNTIFS({range:wishlist.score},">"&{col:score})+1', 7),
    PHC('formatter_phone', 'Formatter phone', 'formatter'), PHC('designer_phone', 'Cover designer phone', 'designer'), PHC('author_phone', 'Author phone', 'author'), IMPRINT()],
    D.wishlist_d(), 60, [A('go_verdict', '= ' + ck('Do now'), 'good'), A('go_verdict', '= ' + ck('Drop'), 'warn')]))
# ---------------------------------------------------------------- 13 price per page and print cost share
tables.append(T('pricepage', 'Price per Page', 'Price per page and print cost share',
    'One row per print edition: list price, pages and unit cost; the price per 100 pages and the print cost share of the price fill in by themselves.', [
    REF('edition_id', 'Edition ID', 'editions.edition_id', 10, required=True), CA('title', 'Title', 'text', EDL('title'), 26), CA('format', 'Format', 'text', EDL('format'), 12),
    CA('list_price', 'List price', 'money', ED_('list_price'), 10), CA('pages', 'Pages', 'int', ED_('pages'), 8),
    CA('price_per_page', 'Price per 100 pages', 'money', 'IF({col:pages}>0,ROUND({col:list_price}/{col:pages}*100,2),0)', 10), CA('unit_cost', 'Unit cost', 'money', ED_('unit_cost'), 10),
    CA('print_cost_share', 'Print cost share of price', 'pct', 'IF({col:list_price}>0,{col:unit_cost}/{col:list_price},0)', 10),
    CA('share_flag', 'Cost share check', 'text', 'IF({col:print_cost_share}>{set:print_cost_share_max},%s,%s)' % (ck('Cost share high'), ck('Cost share fine')), 14)],
    D.pricepage_d(), 80, [A('share_flag', '= ' + ck('Cost share high'), 'warn')]))
# ---------------------------------------------------------------- 14 calendar by month
def CM(kind): return 'COUNTIFS({range:calendar.kind},%s,%s)' % (ckd(kind), INM('calendar.date', '{col:month}'))
tables.append(T('calmonths', 'Calendar by Month', 'Calendar load by month',
    'One row per month: releases, pre-orders opening, promotions starting and contractor deadlines counted from the Release Calendar, with a busy flag against the load you can carry.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('releases', 'Releases', 'int', CM('Release'), 9), CA('preorders', 'Pre-orders opening', 'int', CM('Pre-order opens'), 9), CA('promos', 'Promotions starting', 'int', CM('Promotion starts'), 9),
    CA('deadlines', 'Contractor deadlines', 'int', CM('Contractor deadline'), 9), CA('editions', 'Planned editions', 'int', CM('Planned edition'), 9),
    CA('entries', 'Entries', 'int', 'COUNTIFS(%s)' % INM('calendar.date', '{col:month}'), 8),
    CA('busy_flag', 'Busy flag', 'text', 'IF({col:entries}>={set:load_limit},%s,%s)' % (ck('Busy month'), ck('Normal month')), 12),
    CA('score', 'Load score', 'int', '{col:entries}*100-ROUND(({col:month}-{today})/30,0)', 9), CA('rank', 'Busiest rank', 'int', 'COUNTIFS({range:calmonths.score},">"&{col:score})+1', 8),
    CA('busy_count', 'Busy months ahead', 'int', 'COUNTIFS({range:calmonths.busy_flag},%s,{range:calmonths.month},">="&%s)' % (ck('Busy month'), MS), 9), PHC('author_phone', 'Author phone', 'author'), IMPRINT()],
    D.calmonths_d(), 50, [A('busy_flag', '= ' + ck('Busy month'), 'warn')]))
# ---------------------------------------------------------------- 15 contractor deadlines
tables.append(T('deadlines', 'Contractor Deadlines', 'Contractor deadlines',
    'One row per production job: the title, the kind of job, the contractor, the due date and the day it was delivered; the days late, the state and the contractor phone fill in by themselves.', [
    C('job_id', 'Job ID', 'text', 9, required=True), REF('title', 'Title', 'titles.title', 28), LST('kind', 'Job kind', 'jobkind', 20), LST('contractor', 'Contractor', 'person', 18),
    C('start_date', 'Start date', 'date', 12), C('due_date', 'Due date', 'date', 12), C('delivered_on', 'Delivered on', 'date', 12),
    CA('days_late', 'Days late', 'int', 'IF({col:delivered_on}>0,MAX(0,{col:delivered_on}-{col:due_date}),MAX(0,{today}-{col:due_date}))', 8),
    CA('state', 'State', 'text', 'IF({col:delivered_on}>0,IF({col:days_late}>0,%s,%s),IF({col:due_date}<{today},%s,%s))' % (ck('Delivered late'), ck('Delivered on time'), ck('Open and late'), ck('Open')), 16),
    CA('phone', 'Contractor phone', 'text', LKT('team.phone', 'team.name', 'contractor'), 18), IMPRINT()],
    D.deadlines_d(), 80, [A('state', '= ' + ck('Open and late'), 'bad'), A('state', '= ' + ck('Delivered late'), 'warn'), A('state', '= ' + ck('Delivered on time'), 'good')]))
# ---------------------------------------------------------------- 16 promotion dates
tables.append(T('promos', 'Promotion Dates', 'Price promotions by date',
    'One row per price promotion: title, kind, start and end date, normal and promotion price; the days and the price cut fill in by themselves.', [
    C('promo_id', 'Promotion ID', 'text', 10, required=True), REF('title', 'Title', 'titles.title', 28), LST('kind', 'Kind', 'pkind', 14), C('start_date', 'Start date', 'date', 12), C('end_date', 'End date', 'date', 12),
    C('normal_price', 'Normal price', 'money', 10), C('promo_price', 'Promotion price', 'money', 10),
    CA('days', 'Days', 'int', 'IF({col:end_date}>0,{col:end_date}-{col:start_date}+1,0)', 7), CA('price_cut', 'Price cut', 'pct', 'IF({col:normal_price}>0,1-{col:promo_price}/{col:normal_price},0)', 9),
    PHC('ad_phone', 'Ad specialist phone', 'ad'), PHC('web_phone', 'Web developer phone', 'web'), IMPRINT()],
    D.promos_d(), 60, [A('start_date', '> {today}', 'good')]))
# ---------------------------------------------------------------- 17 title format coverage
def HAS(f): return 'IF(COUNTIFS({range:editions.title_id},{col:title_id},{range:editions.format},%s)-COUNTIFS({range:editions.title_id},{col:title_id},{range:editions.format},%s,{range:editions.status},%s)>0,1,0)' % (fmt(f), fmt(f), PLN)
GAIN = {'Audiobook': '{col:ebook_copies}*(1-{col:audiobook})*{set:ratio_audio}', 'Large print': '{col:ebook_copies}*(1-{col:large_print})*{set:ratio_large_print}',
        'Paperback': '{col:ebook_copies}*(1-{col:paperback})*{set:ratio_paperback}', 'Hardcover': '{col:ebook_copies}*(1-{col:hardcover})*{set:ratio_hardcover}'}
tables.append(T('coverage', 'Title Format Coverage', 'Formats on sale by title',
    'One row per title: 1 where the format exists (not only planned), 0 where it is missing; the formats missing, the best format to add and the copies a month it would add fill in by themselves.', [
    REF('title', 'Title', 'titles.title', 28, required=True), CA('title_id', 'Title ID', 'text', LKT('titles.title_id', 'titles.title', 'title'), 10), CA('status', 'Status', 'text', TLR('status'), 13),
    CA('ebook', 'Ebook', 'int', HAS('Ebook'), 7), CA('paperback', 'Paperback', 'int', HAS('Paperback'), 9), CA('hardcover', 'Hardcover', 'int', HAS('Hardcover'), 9), CA('large_print', 'Large print', 'int', HAS('Large print'), 9),
    CA('audiobook', 'Audiobook', 'int', HAS('Audiobook'), 9), CA('formats_missing', 'Formats missing', 'int', '5-{col:ebook}-{col:paperback}-{col:hardcover}-{col:large_print}-{col:audiobook}', 9),
    CA('ebook_copies', 'Ebook copies a month', 'int', LKN('titles.ebook_copies_month', 'titles.title', 'title'), 10),
    CA('best_gain', 'Best gain, copies a month', 'num', 'IF({col:status}=%s,ROUND(MAX(%s,%s,%s,%s),1),0)' % (tst('Released'), GAIN['Paperback'], GAIN['Hardcover'], GAIN['Large print'], GAIN['Audiobook']), 10),
    CA('best_format', 'Best format to add', 'text', 'IF({col:best_gain}<=0,"",IF(ROUND(%s,1)={col:best_gain},%s,IF(ROUND(%s,1)={col:best_gain},%s,IF(ROUND(%s,1)={col:best_gain},%s,%s))))' % (
        GAIN['Audiobook'], fmt('Audiobook'), GAIN['Large print'], fmt('Large print'), GAIN['Paperback'], fmt('Paperback'), fmt('Hardcover')), 14),
    CA('pscore', 'Gain score', 'num', 'IF({col:best_gain}>0,{col:best_gain}-VALUE(RIGHT({col:title_id},3))/100000,0)', 9), CA('rank', 'Rank', 'int', 'COUNTIFS({range:coverage.pscore},">"&{col:pscore})+1', 7),
    CA('core_formats', 'Ebook and paperback', 'int', 'IF(AND({col:ebook}=1,{col:paperback}=1),1,0)', 9)],
    D.coverage_d(), 60, [A('formats_missing', '= 0', 'good'), A('formats_missing', '>= 4', 'warn')]))
# ---------------------------------------------------------------- 18 titles by genre and status
tables.append(T('genre_status', 'Titles by Genre and Status', 'Titles by genre and status',
    'One row per genre and status: titles, words and editions; fills in from the Titles and Editions sheets.', [
    LST('genre', 'Genre', 'genre', 16, required=True), LST('status', 'Status', 'tstatus', 14),
    CA('titles', 'Titles', 'int', 'COUNTIFS({range:titles.genre},{col:genre},{range:titles.status},{col:status})', 8),
    CA('words', 'Words in these titles', 'int', 'SUMIFS({range:titles.words},{range:titles.genre},{col:genre},{range:titles.status},{col:status})', 10),
    CA('editions', 'Editions', 'int', 'SUMPRODUCT(({range:titles.genre}={col:genre})*({range:titles.status}={col:status})*COUNTIFS({range:editions.title_id},{range:titles.title_id}))', 9)],
    D.genre_d(), 50))
# ---------------------------------------------------------------- 19 team
tables.append(T('team', 'Team', 'Team and contacts',
    'One row per person you work with: role, phone and e-mail; message links and contractor phones read from here.', [
    C('person_id', 'Person ID', 'text', 10, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 20), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 28)],
    D.team_d(), 50))
# ---------------------------------------------------------------- 20 reading order
def PRICE(f): return 'IFERROR(AVERAGEIFS({range:editions.list_price},{range:editions.title},{col:title},{range:editions.format},%s,{range:editions.status},"<>"&%s),0)' % (fmt(f), PLN)
def NB(delta): return 'IF({col:book_number}<1,"",IFERROR(INDEX({range:titles.title},MATCH({col:series}&"|"&({col:book_number}%s),{range:titles.series_key},0)),""))' % delta
tables.append(T('reading', 'Reading Order List', 'Reading order and prices by title',
    'One row per title in reading order: pen name, series, book number, release date, editions on sale and the list price by format; the previous and next book fill in by themselves.', [
    REF('title', 'Title', 'titles.title', 28, required=True), CA('pen_name', 'Pen name', 'text', TLR('pen_name'), 16), CA('series', 'Series', 'text', TLR('series'), 20),
    CA('book_number', 'Book no.', 'int', LKN('titles.series_order', 'titles.title', 'title'), 8), CA('release_date', 'Release date', 'date', LKN('titles.release_date', 'titles.title', 'title'), 12),
    CA('editions_live', 'Editions live', 'int', 'COUNTIFS({range:editions.title},{col:title},{range:editions.status},%s)' % est('Live'), 8),
    CA('words', 'Words in the title', 'int', LKN('titles.words', 'titles.title', 'title'), 10), CA('pages', 'Pages', 'int', LKN('titles.pages', 'titles.title', 'title'), 8),
    CA('price_ebook', 'Ebook price', 'money', PRICE('Ebook'), 9), CA('price_paperback', 'Paperback price', 'money', PRICE('Paperback'), 9), CA('price_hardcover', 'Hardcover price', 'money', PRICE('Hardcover'), 9),
    CA('price_large', 'Large print price', 'money', PRICE('Large print'), 9), CA('price_audio', 'Audiobook price', 'money', PRICE('Audiobook'), 9),
    CA('prev_title', 'Previous book', 'text', NB('-1'), 26), CA('next_title', 'Next book', 'text', NB('+1'), 26), IMPRINT()],
    D.reading_d(), 60))
assert len(tables) == 20, len(tables)
