"""Author and Self-Publisher Business suite - part 6: Series, Title and Pen-Name Performance."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au6_lists import *
from au6_tables import settings, tables, WIN, MS, REL, STEP1, KEEP, REPRICE, REPACK, RETIRE, SHARED
from au6_tools import tools

SUITE = 'fx-20261115-author-publisher'
NOTE = "Sample wording: adapt it to your own business."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
PN = [tok('penname', p) for p in PEN_NAMES]
SERIES_TOK = {s: tok('series', s) for s in SERIES}

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('series_money_form', 'Series Money Case Sheet', 'Series money case for one series', 'series.series', F(('Series', 'series.series'), ('Pen name', 'series.pen_name'), ('Books planned', 'series.books_planned')) + [
        FF('Books released', 'COUNTIFS({range:titles.series},{pick},{range:titles.status},%s)' % REL, 'int'),
        FF('Production cost of the series', 'SUMIFS({range:titles.production_cost},{range:titles.series},{pick})', 'money'),
        FF('Royalties earned so far (lifetime)', 'SUMIFS({range:titles.life_royalties},{range:titles.series},{pick})', 'money'),
        FF('Share of the cost earned back', 'IFERROR(SUMIFS({range:titles.life_royalties},{range:titles.series},{pick})/SUMIFS({range:titles.production_cost},{range:titles.series},{pick}),0)', 'pct'),
        FF('Royalties, last 12 months', 'SUMIFS({range:titles.royalties_12m},{range:titles.series},{pick})', 'money'),
        FF('Copies, last 12 months', 'SUMIFS({range:titles.copies_12m},{range:titles.series},{pick})', 'int'),
        FF('Forecast royalties, next 12 months', 'INDEX({range:sincome.forecast_12m},MATCH({pick},{range:sincome.series},0))', 'money'),
        FF('Average read-through of the series', 'IFERROR(AVERAGEIFS({range:rtstep.readthrough},{range:rtstep.series},{pick}),0)', 'pct'),
        FF('Share of all royalties', 'INDEX({range:sincome.share_total},MATCH({pick},{range:sincome.series},0))', 'pct')]),
    FORM('readthrough_form', 'Read-through Review Sheet', 'Read-through of one series step', 'rtstep.step_id', F(
        ('Series', 'rtstep.series'), ('Step', 'rtstep.stepno'), ('From title', 'rtstep.from_title'), ('To title', 'rtstep.to_title'), ('Copies of book n', 'rtstep.copies_from'), ('Copies of book n+1', 'rtstep.copies_to'),
        ('Read-through', 'rtstep.readthrough'), ('Your threshold', 'rtstep.threshold'), ('Expected read-through', 'rtstep.expected'), ('Step check', 'rtstep.flag'), ('Readers lost', 'rtstep.lost'), ('Value of the readers lost', 'rtstep.lost_value')) + [
        FF('Rank among all steps by readers lost', 'COUNTIFS({range:rtstep.lost_key},">"&%s)+1' % LK('rtstep', 'step_id', 'lost_key'), 'int')]),
    FORM('reader_value_form', 'Reader Value Sheet', 'Value of a book-1 reader at one book', 'vreader.row_id', F(
        ('Series', 'vreader.series'), ('Book', 'vreader.bookno'), ('Title', 'vreader.title'), ('Copies, last 12 months', 'vreader.copies'), ('Share of book 1 readers', 'vreader.share_b1'), ('Read-through into this book', 'vreader.rt_in'),
        ('Royalty per copy', 'vreader.roy_copy'), ('Value of this book per book-1 reader', 'vreader.value_this'), ('Cumulative value of a book-1 reader', 'vreader.value_cum'), ('Ad ceiling for book 1', 'vreader.ad_ceiling')) + [
        FF('Value over the whole series', 'SUMIFS({range:vreader.series_value},{range:vreader.series},%s)' % LK('vreader', 'row_id', 'series'), 'money'),
        FF('Share of the ad value you accept', '{set:ad_share_of_breakeven}', 'pct')]),
    FORM('pen_pl_form', 'Pen-name P&L Sheet', 'Pen-name profit and loss for one month', 'pnl.row_id', F(
        ('Pen name', 'pnl.pen_name'), ('Month', 'pnl.month'), ('Royalties', 'pnl.royalties'), ('Copies', 'pnl.copies'), ('Ad spend', 'pnl.ads'), ('Production paid', 'pnl.production'), ('Own expenses', 'pnl.own_exp'),
        ('Direct costs', 'pnl.direct'), ('Shared costs (your rule)', 'pnl.shared'), ('Shared cost rule', 'pnl.rule_name'), ('Profit', 'pnl.profit'), ('Margin', 'pnl.margin'), ('Profit, last 12 months', 'pnl.profit_12m'),
        ('Share of the 12-month profit', 'pnl.share_profit')) + [FF('Margin you want', '{set:margin_target}', 'pct')]),
    FORM('shared_rule_form', 'Shared Cost Rule Sheet', 'Shared costs split three ways, one month', 'sharesplit.row_id', F(
        ('Pen name', 'sharesplit.pen_name'), ('Month', 'sharesplit.month'), ('Shared costs of the month', 'sharesplit.shared_total'), ('Equal share', 'sharesplit.equal'), ('Share by revenue', 'sharesplit.by_rev'),
        ('Share by number of titles', 'sharesplit.by_titles'), ('Swing between rules', 'sharesplit.swing'), ('Rule you use', 'sharesplit.rule_name')) + [
        FF('Profit of the month, equal rule', 'SUMIFS({range:pnl.profit_eq},{range:pnl.pen_name},%s,{range:pnl.month},%s)' % (LK('sharesplit', 'row_id', 'pen_name'), LK('sharesplit', 'row_id', 'month')), 'money'),
        FF('Profit of the month, by revenue', 'SUMIFS({range:pnl.profit_rev},{range:pnl.pen_name},%s,{range:pnl.month},%s)' % (LK('sharesplit', 'row_id', 'pen_name'), LK('sharesplit', 'row_id', 'month')), 'money'),
        FF('Profit of the month, by titles', 'SUMIFS({range:pnl.profit_tit},{range:pnl.pen_name},%s,{range:pnl.month},%s)' % (LK('sharesplit', 'row_id', 'pen_name'), LK('sharesplit', 'row_id', 'month')), 'money')]),
    FORM('box_case_form', 'Box Set Case Sheet', 'Box set or bundle case with prices and copies', 'bundles.case_id', F(
        ('Bundle', 'bundles.bundle'), ('Series', 'bundles.series'), ('Books in it', 'bundles.books'), ('Prices of the single books', 'bundles.singles_total'), ('Bundle price', 'bundles.bundle_price'), ('Discount to the singles', 'bundles.discount'),
        ('Royalty share', 'bundles.share'), ('Bundle copies a month you expect', 'bundles.copies_month'), ('Single copies taken a month', 'bundles.taken_month'), ('Set-up cost', 'bundles.setup_cost'),
        ('Decide by', 'bundles.decide_by'), ('Royalty per bundle copy', 'bundles.bundle_roy'), ('Royalty lost per single copy taken', 'bundles.single_roy'))),
    FORM('bundle_result_form', 'Bundle Result Sheet', 'Result of a box set against its plan', 'bundles.case_id', F(
        ('Bundle', 'bundles.bundle'), ('Copies a month you planned', 'bundles.copies_month'), ('Actual copies a month', 'bundles.actual_month'), ('Extra income a month', 'bundles.extra_month'), ('Net gain per bundle copy', 'bundles.net_copy'),
        ('Break-even bundle copies', 'bundles.be_copies'), ('Months to earn back the set-up cost', 'bundles.months_pay'), ('Verdict', 'bundles.verdict')) + [
        FF('Royalties of this title, last 12 months', 'SUMIFS({range:tsales.royalties},{range:tsales.title},%s,%s)' % (LK('bundles', 'case_id', 'bundle'), WIN('tsales.month')), 'money'),
        FF('Actual against plan', 'IFERROR(INDEX({range:bundles.actual_month},MATCH({pick},{range:bundles.case_id},0))/INDEX({range:bundles.copies_month},MATCH({pick},{range:bundles.case_id},0)),0)', 'pct')]),
    FORM('cat_decision_form', 'Catalogue Decision Sheet', 'Keep, reprice, repackage or retire for one title', 'decisions.title_id', F(
        ('Title', 'decisions.title'), ('Series', 'decisions.series'), ('Role in the series', 'decisions.role'), ('Status', 'decisions.status'), ('Age (months)', 'decisions.age'), ('Royalties, last 12 months', 'decisions.roy12'),
        ('Ad spend, last 12 months', 'decisions.ad12'), ('Cost left to recover', 'decisions.cost_left'), ('Change, last 3 months', 'decisions.trend_chg'), ('Yearly return', 'decisions.ret'), ('Verdict', 'decisions.verdict'),
        ('Reason', 'decisions.reason'), ('Decision you took', 'decisions.decision'), ('Price to test', 'decisions.new_price'), ('Review on', 'decisions.review_on'))),
    FORM('title_review_form', 'Title Review Sheet', 'Review of one title with its rank and trend', 'titles.title_id', F(
        ('Title', 'titles.title'), ('Pen name', 'titles.pen_name'), ('Series', 'titles.series'), ('Book number', 'titles.series_order'), ('Release date', 'titles.release_date'), ('Status', 'titles.status'),
        ('Age (months)', 'titles.age_months'), ('Production cost', 'titles.production_cost'), ('Royalties, lifetime', 'titles.life_royalties'), ('Cost left to recover', 'titles.cost_left'), ('Copies, last 12 months', 'titles.copies_12m'),
        ('Royalties, last 12 months', 'titles.royalties_12m'), ('Ad spend, last 12 months', 'titles.ad_12m')) + [
        FF('Rank by royalties', 'COUNTIFS({range:titles.rank_key},">"&%s)+1' % LK('titles', 'title_id', 'rank_key'), 'int'),
        FF('Trend', 'IFERROR(INDEX({range:trend.flag},MATCH(%s,{range:trend.title},0)),"")' % LK('titles', 'title_id', 'title'), 'text'),
        FF('Yearly return', 'IFERROR(INDEX({range:ytest.ret},MATCH(%s,{range:ytest.title},0)),"")' % LK('titles', 'title_id', 'title'), 'pct'),
        FF('Catalogue verdict', 'IFERROR(INDEX({range:decisions.verdict},MATCH(%s,{range:decisions.title},0)),"")' % LK('titles', 'title_id', 'title'), 'text')]),
    FORM('return_test_form', 'Yearly Return Test Sheet', 'Yearly return test of one title', 'ytest.title_id', F(
        ('Title', 'ytest.title'), ('Series', 'ytest.series'), ('Status', 'ytest.status'), ('Age (months)', 'ytest.age'), ('Production cost', 'ytest.cost'), ('Royalties, last 12 months', 'ytest.roy12'), ('Yearly return', 'ytest.ret'),
        ('Your target', 'ytest.target'), ('Result', 'ytest.pass'), ('Royalties a month needed', 'ytest.need_month'), ('Short of it each month', 'ytest.gap_month'), ('Tested on', 'ytest.tested_on')) + [
        FF('Titles that fail at your target', 'COUNTIFS({range:ytest.pass},%s)' % v('Fails'), 'int')]),
    FORM('series_plan_form', 'Series Plan Review Sheet', 'Series plan against what is released', 'series.series', F(('Series', 'series.series'), ('Pen name', 'series.pen_name'), ('Books planned', 'series.books_planned')) + [
        FF('Books in the catalogue', 'COUNTIFS({range:titles.series},{pick})', 'int'), FF('Books released', 'COUNTIFS({range:titles.series},{pick},{range:titles.status},%s)' % REL, 'int'),
        FF('Books still to write', 'MAX(0,INDEX({range:series.books_planned},MATCH({pick},{range:series.series},0))-COUNTIFS({range:titles.series},{pick}))', 'int'),
        FF('Last release date', 'SUMPRODUCT(MAX(({range:titles.series}={pick})*({range:titles.status}=%s)*({range:titles.release_date})))' % REL, 'date'),
        FF('Days since the last release', '{today}-SUMPRODUCT(MAX(({range:titles.series}={pick})*({range:titles.status}=%s)*({range:titles.release_date})))' % REL, 'int'),
        FF('Read-through book 1 to 2, your own', 'IFERROR(SUMIFS({range:rtstep.readthrough},{range:rtstep.series},{pick},{range:rtstep.stepno},%s),0)' % STEP1, 'pct'),
        FF('Read-through you want', '{set:readthrough_warn_1}', 'pct'),
        FF('Readers lost along the series', 'SUMIFS({range:rtstep.lost},{range:rtstep.series},{pick})', 'int'),
        FF('Steps below your threshold', 'COUNTIFS({range:rtstep.series},{pick},{range:rtstep.flag},%s)' % v('Below the threshold'), 'int')]),
    FORM('target_income_form', 'Target Income Sheet', 'Target income step with the books needed', 'target.step_id', F(
        ('Step', 'target.tstep'), ('Target income a month', 'target.target_income'), ('Royalties a month now', 'target.now_income'), ('Gap to the target', 'target.gap'), ('Average royalties a book a month', 'target.avg_roy_book'),
        ('Added by one new book', 'target.per_book'), ('Books on sale', 'target.books_on_sale'), ('Books needed', 'target.books_needed'), ('Months at your pace', 'target.months_pace'), ('Verdict', 'target.verdict'), ('Review on', 'target.review_on')) + [
        FF('Books you can publish in a year', '{set:books_per_year}', 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('series_results_doc', 'Series Results Report', 'Series results report', 'sincome.row_id', [
        'Series results report of {set:company}, dated {today}. Series: {col:sincome.series}. Books released: {col:sincome.books_released} of {col:sincome.books_planned} planned.',
        'Last 12 months: {col:sincome.copies_12m} copies and {col:sincome.roy12} in royalties, which is {col:sincome.share_total} of all royalties. The production cost of the series is {col:sincome.cost_series}.',
        'Read-through: the average step is {col:sincome.avg_rt} and {col:sincome.lost_series} readers are lost along the series. Forecast for the next 12 months from your own last 3 months: {col:sincome.forecast_12m}.',
        'Figures are estimates until the stores pay; every target is your own number.'], ['Author-publisher', 'Accountant'], NOTE),
    DOC('readthrough_doc', 'Read-through Report', 'Read-through report for one step', 'rtstep.step_id', [
        'Read-through report of {set:company}, dated {today}. Series: {col:rtstep.series}, {col:rtstep.stepno}: {col:rtstep.from_title} into {col:rtstep.to_title}.',
        'In the last 12 months {col:rtstep.copies_from} copies of the first book and {col:rtstep.copies_to} copies of the next book were sold. Read-through is the share of readers of one book who go on to buy the next: {col:rtstep.readthrough}. Your threshold is {col:rtstep.threshold} and the expected value was {col:rtstep.expected}.',
        'Step check: {col:rtstep.flag}. Readers lost at this step: {col:rtstep.lost}, worth {col:rtstep.lost_value} in royalties.', 'Write the change you decide on below (back matter link, price, a free first book or a reader letter).'], ['Author-publisher'], NOTE),
    DOC('reader_value_doc', 'Value of a Reader Summary', 'Value of a reader summary', 'vreader.row_id', [
        'Value of a reader summary of {set:company}, dated {today}. Series: {col:vreader.series}. Book: {col:vreader.bookno}, {col:vreader.title}.',
        'Of every book-1 reader, {col:vreader.share_b1} reach this book. The royalty per copy is {col:vreader.roy_copy}, so this book adds {col:vreader.value_this} per book-1 reader and the series adds {col:vreader.value_cum} up to this book.',
        'At your share of {set:ad_share_of_breakeven} the ad ceiling for a sale of book 1 is {col:vreader.ad_ceiling}. Check it against the real cost of a sale on the ads sheet.', 'The value is an estimate from your own last 12 months.'], ['Author-publisher', 'Ad specialist'], NOTE),
    DOC('pen_pl_doc', 'Pen-name Profit Statement', 'Pen-name profit and loss statement', 'pnl.row_id', [
        'Profit and loss statement of {set:company}, dated {today}. Pen name: {col:pnl.pen_name}. Month: {col:pnl.month}.',
        'Royalties {col:pnl.royalties} from {col:pnl.copies} copies. Direct costs {col:pnl.direct}: ads {col:pnl.ads}, production {col:pnl.production}, own expenses {col:pnl.own_exp}. Shared costs {col:pnl.shared} under the rule {col:pnl.rule_name}.',
        'Profit {col:pnl.profit}, a margin of {col:pnl.margin}. Profit of the last 12 months {col:pnl.profit_12m}, which is {col:pnl.share_profit} of the profit of all pen names.',
        'Confirm the figures and the cost split with your accountant. In a small press this page is an author statement of costs.'], ['Author-publisher', 'Accountant'], NOTE),
    DOC('shared_note_doc', 'Shared Cost Split Note', 'Shared cost split note', 'sharesplit.row_id', [
        'Shared cost split note of {set:company}, dated {today}. Pen name: {col:sharesplit.pen_name}. Month: {col:sharesplit.month}.',
        'The shared costs of the month are {col:sharesplit.shared_total}. Split equally the pen name carries {col:sharesplit.equal}; by revenue {col:sharesplit.by_rev}; by the number of titles {col:sharesplit.by_titles}. The swing between the rules is {col:sharesplit.swing}.',
        'The rule in use is {col:sharesplit.rule_name}. Confirm the rule with your accountant and keep the same rule for the whole year.'], ['Author-publisher', 'Accountant'], NOTE),
    DOC('box_set_doc', 'Box Set Business Case', 'Box set business case', 'bundles.case_id', [
        'Business case of {set:company}, dated {today}. Bundle: {col:bundles.bundle} ({col:bundles.books} books, series {col:bundles.series}).',
        'The single books cost {col:bundles.singles_total} together; the bundle costs {col:bundles.bundle_price}, a discount of {col:bundles.discount}. The royalty per bundle copy is {col:bundles.bundle_roy}. Each single copy it takes from you costs {col:bundles.single_roy}.',
        'You expect {col:bundles.copies_month} bundle copies a month and {col:bundles.taken_month} single copies taken, so the extra income is {col:bundles.extra_month} a month. The set-up cost of {col:bundles.setup_cost} is earned back after {col:bundles.be_copies} bundle copies, about {col:bundles.months_pay} months.',
        'Verdict: {col:bundles.verdict}. Decide by {col:bundles.decide_by}. Check each store\'s current terms for bundle prices and royalty shares.'], ['Author-publisher', 'Formatter'], NOTE),
    DOC('title_review_doc', 'Title Review', 'Title review for one title', 'decisions.title_id', [
        'Title review of {set:company}, dated {today}. Title: {col:decisions.title} ({col:decisions.series}, {col:decisions.role}). Status: {col:decisions.status}, age {col:decisions.age} months.',
        'Last 12 months: royalties {col:decisions.roy12}, ad spend {col:decisions.ad12}. Cost left to recover: {col:decisions.cost_left}. Change of the last 3 months: {col:decisions.trend_chg}. Yearly return: {col:decisions.ret}.',
        'Verdict: {col:decisions.verdict}. Reason: {col:decisions.reason}. Decision you took: {col:decisions.decision}. Price to test if you reprice: {col:decisions.new_price}.', 'Write the next step, the owner and the date below.'], ['Author-publisher'], NOTE),
    DOC('decision_list_doc', 'Catalogue Decision List', 'Catalogue decision list for one series', 'sincome.row_id', [
        'Catalogue decision list of {set:company}, dated {today}. Series: {col:sincome.series}.',
        'Titles to keep: {col:sincome.n_keep}. Titles to reprice: {col:sincome.n_reprice}. Titles to repackage: {col:sincome.n_repack}. Titles to retire: {col:sincome.n_retire}.',
        'The verdict of each title is on the Catalogue Decisions sheet with its reason. Write below the title, the decision, the owner and the date for each title that is not kept.'], ['Author-publisher'], NOTE),
    DOC('return_report_doc', 'Yearly Return Test Report', 'Yearly return test report', 'ytest.title_id', [
        'Yearly return test of {set:company}, dated {today}. Title: {col:ytest.title} ({col:ytest.series}). Status: {col:ytest.status}.',
        'Production cost {col:ytest.cost}. Royalties of the last 12 months {col:ytest.roy12}. Yearly return {col:ytest.ret} against your own target of {col:ytest.target}. Result: {col:ytest.pass}.',
        'To pass, the title needs {col:ytest.need_month} royalties a month; it is short by {col:ytest.gap_month} a month. Tested on {col:ytest.tested_on}.', 'The target is your own number, not a standard.'], ['Author-publisher'], NOTE),
    DOC('backlist_doc', 'Backlist and Frontlist Report', 'Backlist and frontlist report for one month', 'backlist.month', [
        'Backlist and frontlist report of {set:company}, dated {today}. Month: {col:backlist.month}.',
        'Royalties of titles under 12 months old (frontlist): {col:backlist.front}. Royalties of older titles (backlist): {col:backlist.back}. Total {col:backlist.total}. The backlist carries {col:backlist.backlist_share} of the income; titles older than 24 months carry {col:backlist.older24_share}.',
        'A high backlist share means steady income from old books; a low one means income depends on the next launch.'], ['Author-publisher'], NOTE),
    DOC('series_plan_doc', 'Series Plan for Next Year', 'Series plan for next year', 'sincome.row_id', [
        'Series plan of {set:company}, dated {today}. Series: {col:sincome.series}. Planned books: {col:sincome.books_planned}; released: {col:sincome.books_released}; still to write: {col:sincome.books_to_write}.',
        'Forecast royalties for the next 12 months: {col:sincome.forecast_12m} (your own last 3 months with a trend factor). Average read-through: {col:sincome.avg_rt}; readers lost along the series: {col:sincome.lost_series}.',
        'Write below the release dates, the cost of each book and the owner of each task. Keep the gap between releases above the minimum you set in the release calendar.'], ['Author-publisher', 'Launch coordinator'], NOTE),
    DOC('target_plan_doc', 'Target Income Plan', 'Target income plan', 'target.step_id', [
        'Target income plan of {set:company}, dated {today}. Step: {col:target.tstep}. Target: {col:target.target_income} a month.',
        'Royalties a month now: {col:target.now_income}. Gap: {col:target.gap}. One new book adds about {col:target.per_book} with the lift on earlier books. Books needed: {col:target.books_needed}, about {col:target.months_pace} months at your pace. Verdict: {col:target.verdict}.',
        'Review on {col:target.review_on}. The target and the pace are your own numbers; figures are estimates.'], ['Author-publisher'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('series_quarter', 'Quarterly Series Review', 'sincome', 'sincome.month', [('Export or enter the latest sales totals', 0), ('Check the copies and royalties of the series', 1), ('Check the read-through of each step', 2), ('Check the cost of each book against its royalties', 4), ('Check the forecast against the last 3 months', 5), ('Write the decision for the next quarter', 7)]),
    CHK('new_series', 'New Series Plan', 'titles', 'titles.release_date', [('Write the number of books and the cost of each', -240), ('Set the gap between releases', -230), ('Plan the book 1 price and the reader magnet', -200), ('Write the expected read-through', -190), ('Brief the cover designer for the series look', -150), ('Plan the back matter link to book 2', -120)]),
    CHK('rt_check', 'Read-through Check', 'rtstep', 'rtstep.checked_on', [('Count the copies of book n and book n+1', 0), ('Work out the read-through of the step', 1), ('Compare it with your threshold', 1), ('Check the back matter link and the blurb', 3), ('Decide the fix for the weakest step', 5), ('Write the date of the next check', 7)]),
    CHK('pnl_month', 'Pen Profit Month', 'pnl', 'pnl.month', [('Enter the month royalties and the costs', 2), ('Mark each expense as Shared or a pen name', 3), ('Check the shared cost rule', 4), ('Read the profit and the margin of each pen name', 5), ('Send the figures to the accountant', 6), ('Write what to change next month', 8)]),
    CHK('yearly_review', 'Yearly Title Review', 'ytest', 'ytest.tested_on', [('Check the production cost of each title', 0), ('Enter the royalties of the last 12 months', 1), ('Read the yearly return of each title', 2), ('List the titles that fail your target', 3), ('Read the reason and the verdict of each', 5), ('Write the decisions and the dates', 7)]),
    CHK('boxset_decide', 'Box Set Decision', 'bundles', 'bundles.decide_by', [('Check which single books it would take copies from', -28), ('Write the bundle price and your royalty share', -24), ('Ask for the cover and files quotes', -21), ('Check the break-even copies', -14), ('Decide: make it or skip it', -7), ('Write the date to check the result', 0)]),
    CHK('reprice', 'Reprice Decision', 'decisions', 'decisions.review_on', [('Check the trend of the last 3 months', -14), ('Check the royalty share at the new price', -12), ('Pick the price to test and its dates', -10), ('Ask the assistant to change the price', -7), ('Tell the newsletter list', -3), ('Read the result after 30 days', 30)]),
    CHK('repackage', 'Repackage Decision', 'decisions', 'decisions.review_on', [('Check the cost left to recover', -21), ('Check which edition drags the title', -18), ('Ask the cover designer for a quote', -14), ('Check the blurb and the first pages', -10), ('Decide: repackage or leave as it is', -7), ('Plan the relaunch with the coordinator', 0)]),
    CHK('retire_edition', 'Retire an Edition Decision', 'decisions', 'decisions.review_on', [('Check the royalties a month against your floor', -14), ('Check that no later book needs it', -12), ('Check each store\'s current terms for removing it', -10), ('Tell the assistant which edition to retire', -7), ('Remove the back matter links to it', -3), ('Write the date and the reason', 0)]),
    CHK('backlist_review', 'Backlist Review', 'backlist', 'backlist.month', [('Enter the month royalties by title', 1), ('Read the backlist share', 2), ('List the old titles that fell most', 3), ('Pick two old titles for a price promotion', 5), ('Check the series links in the back matter', 7), ('Write the plan for next month', 9)]),
    CHK('target_review', 'Target Income Review', 'target', 'target.review_on', [('Enter the royalties a month now', -7), ('Check the average a book brings', -5), ('Check the books you can publish in a year', -3), ('Read the books needed and the months', 0), ('Decide the next book to write', 2), ('Write the date of the next review', 5)]),
    CHK('year_end', 'Year-end Performance Review', 'sharesplit', 'sharesplit.month', [('Close the books of the year with the accountant', 5), ('Check the shared costs and the rule used', 7), ('Read the profit of each pen name', 9), ('Read the yearly return of every title', 11), ('Read the backlist share and the top 3 share', 13), ('Write the plan and the targets for next year', 20)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('dz_quote', 'Cover designer: quote a new cover', 'decisions', 'decisions.dz_phone', 'Hello {dz_name}, {title} is under review. Please send a quote for a new cover by {due_date}. {company}'),
    M('dz_due', 'Cover designer: new cover due', 'decisions', 'decisions.dz_phone', 'Hello {dz_name}, the new cover of {title} is due on {due_date}. Please send it when it is ready. {company}'),
    M('dz_box', 'Cover designer: box set cover', 'bundles', 'bundles.dz_phone', 'Hello {dz_name}, please prepare a box set cover for {bundle}. {company}'),
    M('fm_box', 'Formatter: build the box set files', 'bundles', 'bundles.fm_phone', 'Hello {fm_name}, please build the box set files for {bundle}. {company}'),
    M('fm_series', 'Formatter: update the series page', 'sincome', 'sincome.fm_phone', 'Hello {fm_name}, please update the series page of {series}. {company}'),
    M('nar_quote', 'Narrator: quote the next book', 'sincome', 'sincome.nar_phone', 'Hello {nar_name}, please send a quote for the next book of {series}. {company}'),
    M('va_price', 'Assistant: change a price', 'decisions', 'decisions.va_phone', 'Hello {va_name}, please change the price of {title} to {new_price}. {company}'),
    M('va_box', 'Assistant: add the box set', 'bundles', 'bundles.va_phone', 'Hello {va_name}, please add the box set {bundle} to the stores. {company}'),
    M('va_link', 'Assistant: update the book 2 link', 'rtstep', 'rtstep.va_phone', 'Hello {va_name}, please update the book {step_no} link in the back matter of {from_title}. The next book is {to_title}. {company}'),
    M('va_sales', 'Assistant: collect the series sales', 'sincome', 'sincome.va_phone', 'Hello {va_name}, please collect the sales of {series} for the last 12 months. {company}'),
    M('va_retire', 'Assistant: retire an edition', 'decisions', 'decisions.va_phone', 'Hello {va_name}, please retire the edition of {title} after you check each store\'s current terms. {company}'),
    M('ad_ceiling', 'Ad specialist: the ceiling for book 1', 'vreader', 'vreader.ad_phone', 'Hello {ad_name}, the ad ceiling for book 1 of {series} is {ad_ceiling} a sale. {company}'),
    M('ad_stop', 'Ad specialist: stop ads on a title', 'ytest', 'ytest.ad_phone', 'Hello {ad_name}, please stop ads on {title}, it fails the yearly return test at {ret}. {company}'),
    M('ad_price', 'Ad specialist: test a lower price', 'vreader', 'vreader.ad_phone', 'Hello {ad_name}, please test a lower price for book 1 of {series}. {company}'),
    M('wd_bundle', 'Web developer: add the bundle', 'bundles', 'bundles.wd_phone', 'Hello {wd_name}, please add the bundle {bundle} to the direct store at {bundle_price}. {company}'),
    M('acc_profit', 'Accountant: profit of a pen name', 'pnl', 'pnl.acc_phone', 'Hello {acc_name}, the profit of {pen_name} for the last 12 months is {profit_12m}. {company}'),
    M('acc_rule', 'Accountant: the cost split rule', 'sharesplit', 'sharesplit.acc_phone', 'Hello {acc_name}, the shared costs are split by {rule_name}. {company}'),
    M('acc_confirm', 'Accountant: confirm the rule', 'sharesplit', 'sharesplit.acc_phone', 'Hello {acc_name}, please confirm the cost split rule for {pen_name}. The shared costs of {month} are {shared_total}. {company}'),
    M('ra_licence', 'Rights agent: is a licence an option', 'decisions', 'decisions.ra_phone', 'Hello {ra_name}, {title} has not earned back its cost (left to recover: {cost_left}). Is a licence an option? {company}'),
    M('co_relaunch', 'Launch coordinator: plan a relaunch', 'decisions', 'decisions.co_phone', 'Hello {co_name}, please plan a relaunch of {title}. A first plan is due on {due_date}. {company}'),
    M('au_rt', 'Author: read-through below threshold', 'rtstep', 'rtstep.author_phone', 'Note for the author: the read-through of {series} from book {step_no} is {readthrough}, below your threshold of {threshold}. {company}'),
    M('au_lost', 'Author: readers lost at a step', 'drops', 'drops.author_phone', 'Note for the author: {lost} readers are lost between book {step_no} and the next in {series}. {company}'),
    M('au_reader', 'Author: the value of a reader', 'vreader', 'vreader.author_phone', 'Note for the author: a reader of book 1 of {series} is worth {value_cum} over the series so far. {company}'),
    M('au_fail', 'Author: a title fails the return test', 'ytest', 'ytest.author_phone', 'Reminder for the author: {title} fails the yearly return test at {ret}. {company}'),
    M('au_pass', 'Author: a title passes the return test', 'ytest', 'ytest.author_phone', 'Note for the author: {title} passes the yearly return test at {ret}. {company}'),
    M('au_decision', 'Author: the decision for a title', 'decisions', 'decisions.author_phone', 'Reminder for the author: the decision for {title} is {verdict}. {company}'),
    M('au_box', 'Author: what the box set adds', 'bundles', 'bundles.author_phone', 'Note for the author: the box set {bundle} adds {extra_month} a month. {company}'),
    M('au_pen', 'Author: share of the profit', 'pnl', 'pnl.author_phone', 'Note for the author: {pen_name} earned {share_profit} of the profit of the last 12 months. {company}'),
    M('au_books', 'Author: books needed for the target', 'target', 'target.author_phone', 'Note for the author: {books_needed} more books are needed to reach {target_income} a month. {company}'),
    M('au_forecast', 'Author: series forecast', 'sincome', 'sincome.author_phone', 'Note for the author: the series {series} is forecast to earn {forecast_12m} in 12 months. {company}'),
    M('au_trend', 'Author: a title against last year', 'trend', 'trend.author_phone', 'Reminder for the author: {title} is {flag}, {change_ly} against the same months last year. {company}'),
    M('au_top3', 'Author: top 3 titles share', 'ranking', 'ranking.author_phone', 'Note for the author: the top 3 titles carry {top3_share} of royalties. {company}'),
    M('au_backlist', 'Author: backlist share', 'backlist', 'backlist.author_phone', 'Note for the author: the backlist carries {backlist_share} of royalties in {month}. {company}'),
    M('au_review', 'Author: a series review is due', 'sincome', 'sincome.author_phone', 'Reminder for the author: a series review is due for {series}. {company}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30), dashboard, insights
def SR(s): return 'SUMIFS({range:titles.royalties_12m},{range:titles.series},%s)' % SERIES_TOK[s]
S4 = [SR(s) for s in SERIES[:4]]
def PEN12(i, col='profit'): return 'SUMIFS({range:pnl.%s},{range:pnl.pen_name},%s,%s)' % (col, PN[i], WIN('pnl.month'))
def MG12(i): return 'IF(%s>0,%s/%s,0)' % (PEN12(i, 'royalties'), PEN12(i), PEN12(i, 'royalties'))
RELEASED_N = 'COUNTIFS({range:titles.status},%s)' % REL
kpis = [
    KPI('Best series royalties, 12 months', 'MAX(%s)' % ','.join(S4), 'money'),
    KPI('Weakest series royalties, 12 months', 'MIN(%s)' % ','.join(S4), 'money'),
    KPI('Book 1 to 2 read-through, lowest', 'MIN({range:rtstep.rt_first})', 'pct', alert={"when": "< {set:readthrough_warn_1}", "style": "bad"}),
    KPI('Book 1 to 2 read-through, average', 'AVERAGE({range:rtstep.rt_first})', 'pct'),
    KPI('Series below the book 1 target', 'COUNTIFS({range:rtstep.stepno},%s,{range:rtstep.flag},%s)' % (STEP1, v('Below the threshold')), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Steps below the later-step threshold', 'COUNTIFS({range:rtstep.stepno},"<>"&%s,{range:rtstep.flag},%s)' % (STEP1, v('Below the threshold')), 'int'),
    KPI('Readers lost at the weakest step', 'MAX({range:rtstep.lost})', 'int'),
    KPI('Value of a book-1 reader, average', 'AVERAGE({range:vreader.series_value})', 'money'),
    KPI('Ad ceiling for book 1, average', 'AVERAGE({range:vreader.series_value})*{set:ad_share_of_breakeven}', 'money'),
    KPI('%s royalties, 12 months' % PEN_NAMES[0], 'SUMIFS({range:pnl.royalties},{range:pnl.pen_name},%s,%s)' % (PN[0], WIN('pnl.month')), 'money'),
    KPI('%s royalties, 12 months' % PEN_NAMES[1], 'SUMIFS({range:pnl.royalties},{range:pnl.pen_name},%s,%s)' % (PN[1], WIN('pnl.month')), 'money'),
    KPI('Profit of the pen name with more profit', 'MAX(%s,%s)' % (PEN12(0), PEN12(1)), 'money'),
    KPI('Margin of the pen name with less margin', 'MIN(%s,%s)' % (MG12(0), MG12(1)), 'pct', alert={"when": "< {set:margin_target}", "style": "warn"}),
    KPI('Largest pen name share of profit', 'IFERROR(MAX(%s,%s)/(%s+%s),0)' % (PEN12(0), PEN12(1), PEN12(0), PEN12(1)), 'pct'),
    KPI('Shared costs, last 12 months', 'SUMIFS({range:expenses.amount},{range:expenses.pen_name},%s,%s)' % (SHARED, WIN('expenses.month')), 'money'),
    KPI('Cost left to recover, released titles', 'SUMIFS({range:titles.cost_left},{range:titles.status},%s)' % REL, 'money', alert={"when": "> 0", "style": "warn"}),
    KPI('Titles to reprice', 'COUNTIFS({range:decisions.verdict},%s)' % REPRICE, 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Titles to repackage', 'COUNTIFS({range:decisions.verdict},%s)' % REPACK, 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Titles to retire', 'COUNTIFS({range:decisions.verdict},%s)' % RETIRE, 'int'),
    KPI('Titles that earned back their cost', 'COUNTIFS({range:titles.status},%s,{range:titles.cost_left},0)' % REL, 'int'),
    KPI('Average yearly return of all titles', 'AVERAGE({range:ytest.ret})', 'pct'),
    KPI('Highest yearly return', 'MAX({range:ytest.ret})', 'pct'),
    KPI('Lowest yearly return', 'MIN({range:ytest.ret})', 'pct'),
    KPI('Top title royalties, 12 months', 'INDEX({range:ranking.roy12},1)', 'money'),
    KPI('Frontlist royalties, 12 months', 'SUMIFS({range:titles.royalties_12m},{range:titles.age_months},"<=12")', 'money'),
    KPI('Titles growing against last year', 'COUNTIFS({range:trend.change_ly},">"&{set:trend_flag_pct})', 'int'),
    KPI('Titles declining against last year', 'COUNTIFS({range:trend.change_ly},"<"&-{set:trend_flag_pct})', 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Box set royalties, 12 months', SR('Box set'), 'money'),
    KPI('Books needed to reach the target income', 'IF(SUM({range:titles.royalties_12m})/12>={set:target_income},0,ROUNDUP(({set:target_income}-SUM({range:titles.royalties_12m})/12)/(SUM({range:titles.royalties_12m})/12/%s*(1+{set:lift_pct})),0))' % RELEASED_N, 'int'),
    KPI('Average royalties a title, 12 months', 'SUM({range:titles.royalties_12m})/%s' % RELEASED_N, 'money'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Performance Dashboard", "kpis": kpis,
    "monthly": {"title": "Royalties, direct costs and profit by month", "date": "pnl.month", "series": [
        {"label": "Royalties", "sum": "pnl.royalties", "date": "pnl.month"}, {"label": "Direct costs", "sum": "pnl.direct", "date": "pnl.month"}, {"label": "Profit", "sum": "pnl.profit", "date": "pnl.month"}]},
    "breakdowns": [{"title": "Royalties by series", "by": "tsales.series", "value": "tsales.royalties", "agg": "sum"}, {"title": "Royalties by pen name", "by": "tsales.pen_name", "value": "tsales.royalties", "agg": "sum"},
                   {"title": "Expenses by category", "by": "expenses.category", "value": "expenses.amount", "agg": "sum"}, {"title": "Ad spend by pen name", "by": "tcosts.pen_name", "value": "tcosts.ad_spend", "agg": "sum"}]}
def PNL_M(col, p, label): return AGG('sum', 'pnl', 'pnl.%s' % col, date='pnl.month', where=[('pen_name', '=', tok('penname', p))], label=label)
insights = {"filters": [{"label": "Series", "list": "series"}, {"label": "Pen name", "list": "penname"}, {"label": "Catalogue decision", "list": "dverdict"}],
    "gauges": [
        {"title": "Steps at or above read-through target", "num": AGG('count', 'rtstep', where=[('flag', '=', v('Healthy step'))]), "den": AGG('count', 'rtstep')},
        {"title": "Titles passing the yearly return test", "num": AGG('count', 'ytest', where=[('pass', '=', v('Passes'))]), "den": AGG('count', 'ytest', where=[('status', '=', REL)])},
        {"title": "Titles with the verdict keep", "num": AGG('count', 'decisions', where=[('verdict', '=', KEEP)]), "den": AGG('count', 'decisions')},
        {"title": "Backlist share of royalties", "num": AGG('sum', 'backlist', 'backlist.back'), "den": AGG('sum', 'backlist', 'backlist.total')},
        {"title": "Pen-name months at your margin target", "num": AGG('count', 'pnl', where=[('margin', '>=', '{set:margin_target}')]), "den": AGG('count', 'pnl')},
        {"title": "Royalties from outside the top 3 titles", "num": AGG('sum', 'ranking', 'ranking.roy12', where=[('rank_no', '>', 3)]), "den": AGG('sum', 'ranking', 'ranking.roy12')}],
    "charts": [
        CHART('Royalties by series, last 12 months', 'bar', 'titles.series', [AGG('sum', 'titles', 'titles.royalties_12m', label='Royalties')]),
        CHART('Royalties by pen name, last 12 months', 'bar', 'titles.pen_name', [AGG('sum', 'titles', 'titles.royalties_12m', label='Royalties')]),
        CHART('Royalties by genre, last 12 months', 'bar', 'titles.genre', [AGG('sum', 'titles', 'titles.royalties_12m', label='Royalties')]),
        CHART('Royalties by title status, last 12 months', 'bar', 'titles.status', [AGG('sum', 'titles', 'titles.royalties_12m', label='Royalties')]),
        CHART('Royalties per month by pen name', 'column', 'month', [PNL_M('royalties', p, p) for p in PEN_NAMES]),
        CHART('Copies by series, last 12 months', 'bar', 'titles.series', [AGG('sum', 'titles', 'titles.copies_12m', label='Copies')]),
        CHART('Series income per month', 'column', 'month', [AGG('sum', 'sincome', 'sincome.royalties', date='sincome.month', where=[('series', '=', tok('series', s))], label=s) for s in SERIES4]),
        CHART('Read-through by series step', 'bar', 'rtstep.stepno', [AGG('avg', 'rtstep', 'rtstep.readthrough', label='Read-through')]),
        CHART('Copies by book number', 'bar', 'chain.bookno', [AGG('sum', 'chain', 'chain.copies', label='Copies')]),
        CHART('Readers lost by series', 'bar', 'rtstep.series', [AGG('sum', 'rtstep', 'rtstep.lost', label='Readers lost')]),
        CHART('Pen-name costs per month', 'stacked', 'month', [AGG('sum', 'pnl', 'pnl.direct', date='pnl.month', label='Direct costs'), AGG('sum', 'pnl', 'pnl.shared', date='pnl.month', label='Shared costs')]),
        CHART('Pen-name profit per month', 'column', 'month', [PNL_M('profit', p, p) for p in PEN_NAMES]),
        CHART('Shared costs by category', 'bar', 'expenses.category', [AGG('sum', 'expenses', 'expenses.amount', where=[('pen_name', '=', SHARED)], label='Shared costs')]),
        CHART('Production cost by series', 'bar', 'titles.series', [AGG('sum', 'titles', 'titles.production_cost', label='Production cost')]),
        CHART('Ad spend by series, last 12 months', 'bar', 'titles.series', [AGG('sum', 'titles', 'titles.ad_12m', label='Ad spend')]),
        CHART('Catalogue decisions by verdict', 'bar', 'decisions.decision', [AGG('count', 'decisions', label='Titles')]),
        CHART('Yearly return by series', 'bar', 'ytest.series', [AGG('avg', 'ytest', 'ytest.ret', label='Yearly return')]),
        CHART('Titles passing the return test by series', 'bar', 'ytest.series', [AGG('count', 'ytest', where=[('pass', '=', v('Passes'))], label='Titles passing')]),
        CHART('Box set royalties per month', 'column', 'month', [AGG('sum', 'sincome', 'sincome.royalties', date='sincome.month', where=[('series', '=', tok('series', 'Box set'))], label='Box set royalties')]),
        CHART('Target income steps by books needed', 'bar', 'target.tstep', [AGG('sum', 'target', 'target.books_needed', label='Books needed')]),
        CHART('Backlist royalties per month', 'column', 'month', [AGG('sum', 'backlist', 'backlist.back', date='backlist.month', label='Backlist royalties')]),
        CHART('Backlist share of royalties per month', 'column', 'month', [AGG('avg', 'backlist', 'backlist.backlist_share', date='backlist.month', label='Backlist share')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Series money case", "why": "planned books, cost each, release gaps and your read-through turned into 24 months of copies, the payback and the book at which to stop", "where": "Series Money Case"},
    {"name": "Books to reach a target income", "why": "the royalties you want each month and the lift a new book gives turned into books needed and months at your own pace", "where": "Books to Reach a Target"},
    {"name": "Read-through by step with flags", "why": "copies of book n and n+1 against your own thresholds, with the weak step of each series named", "where": "Read-through by Step"},
    {"name": "Where readers drop ranking", "why": "every series step ranked by readers lost and their value, so the first fix is never a guess", "where": "Where Readers Drop"},
    {"name": "Value of a reader and the ad ceiling", "why": "royalties per book-1 buyer over the series set the most a sale of book 1 may cost in ads", "where": "Reader Value and Ad Ceiling"},
    {"name": "Pen-name profit and loss", "why": "royalties, direct costs, shared costs and margin of each pen name, a small press reads it as an author view", "where": "Pen Profit"},
    {"name": "Shared cost rule comparer", "why": "the same costs split equally, by revenue and by titles, with the swing and the fairest rule named", "where": "Shared Cost Rule Comparer"},
    {"name": "Yearly return test per title", "why": "royalties of the last 12 months over production cost against your own target, with the royalties a month needed to pass", "where": "Yearly Return Test"},
    {"name": "Catalogue decision", "why": "keep, reprice, repackage or retire for every title with one reason from its age, trend, cost left and role", "where": "Catalogue Decisions"},
    {"name": "Box set case and cannibalisation check", "why": "extra income a month, break-even box set copies and whether an existing box set added income or swapped it", "where": "Box Set Case"},
    {"name": "Next book forecast in three scenarios", "why": "list size, launch share and read-through give Base, Best and Worst copies and the months to earn back the cost", "where": "Next Book Forecast"},
    {"name": "Title trend against your own history", "why": "last 3 months against the 3 before and the same months last year, flagged growing, flat or declining", "where": "Title Trend"}]
competitors = [
    {"what": "free royalty tracking templates", "lacks": "total the royalties but never show read-through by step, the value of a reader or the yearly return of each title"},
    {"what": "store sales dashboards", "lacks": "show each store alone, with no series money case, no pen-name profit and loss and no keep, reprice, repackage or retire verdict"},
    {"name": "x", "what": "generic budget spreadsheets", "lacks": "know no pen names, no shared cost rule and no break-even for a box set"},
    {"what": "subscription publishing dashboards", "lacks": "charge a tier that rises with your income and keep your numbers on their servers; this is one flat price and the data stays with you"},
    {"what": "single-sheet series planners", "lacks": "list books and dates but never turn them into forecast copies, payback or the books needed for a target income"}]
competitors[2].pop('name')
guide = [
    'Open Start and type your imprint name and your own targets in the yellow cells: yearly return, read-through thresholds, margin, the shared cost rule and the royalties you want each month. Every target is your own number.',
    'Check Titles and Series. Titles holds the facts of each title, the production cost and the expected read-through; Series holds the books you plan. A first-time author with one to three books fills a few rows.',
    'Enter or paste the copies and royalties of each title and month in Sales by Title and Month, and the ad spend and production paid in Costs by Title and Month. Page reads are an estimate that moves every month.',
    'Enter every business expense in Expenses and mark it Shared or a pen name. Shared costs are split between the pen names by the rule you choose on Start.',
    'Read Read-through by Step, Read-through Chain, Where Readers Drop and Value of a Reader: they fill in by themselves from Titles and show where readers leave a series and what a book-1 reader is worth.',
    'Read Pen Profit and Shared Costs by Rule for the profit of each pen name. A small press reads the pen-name columns as author columns.',
    'Read Yearly Return Test, Catalogue Decisions, Title Trend, Title Ranking and Backlist and Frontlist to decide which titles to keep, reprice, repackage or retire.',
    'Use Box Set and Bundle Cases and Target Income Steps to plan a box set or the books needed for the monthly royalties you want.',
    'Use the %d calculators to judge a series, the price of book 1, a box set, a title or a pen name; print %d sheets and %d documents, follow %d checklists and tap a message link to send a text with the details already written in.' % (len(tools), len(forms), len(documents), len(checklists)),
    'Figures are estimates until the stores pay and every target is your own number; confirm tax and cost split questions with your adviser. No macros, works in Excel and Google Sheets.']
listing = {"title": "Author and Self-Publisher Series, Title and Pen-Name Performance Excel Template: Read-through, Reader Value, Pen-Name P&L, Return Test",
    "headline": "See which books, series and pen names earn their keep and what to do next",
    "tags": ["author template", "read-through", "series planner", "pen name profit", "self publishing", "indie author", "excel template", "author business", "royalty tracker", "box set planner", "title review", "catalogue decisions", "kpi dashboard"],
    "description": ("Run the performance side of an author or small publishing business in one Excel workbook. Built for an independent author who publishes under one or two pen names, often with a part-time assistant and freelancers. "
        "Series Money Case turns the books you plan, the cost of each, the gap between releases and your own read-through into 24 months of copies, the payback and the book at which to stop. Read-through by Step compares the copies of book n and book n+1 with thresholds you set (read-through is the share of readers of one book who go on to buy the next), and Where Readers Drop ranks every step by readers lost.\n\n"
        "Value of a Reader multiplies your royalty per copy by the read-through chain to show what a book-1 buyer is worth over the whole series and the most a sale of book 1 may cost in ads. Pen Profit splits revenue, direct costs and shared costs by the rule you choose (equal, by revenue or by number of titles) and the Shared Cost Rule Comparer shows the swing. "
        "Yearly Return Test sets the royalties of the last 12 months against the production cost of each title, and Catalogue Decisions gives a keep, reprice, repackage or retire verdict with one reason. Box Set Case, Title Trend, Backlist against Frontlist and Next Book Forecast (Base, Best and Worst) cover the other weekly questions.\n\n"
        "%d calculators, %d printable sheets, %d documents, %d checklists and %d ready text messages to the assistant, designers, formatter, narrator, ad specialist, accountant and rights agent. This is part six of the Author and Self-Publisher Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data. Figures are estimates until the stores pay, every target is your own number and nothing here promises sales." % (len(tools), len(forms), len(documents), len(checklists), len(messages))),
    "features": ["Series money case with payback and the book to stop at", "Read-through by step with flags against your thresholds", "Where readers drop ranked by readers lost", "Value of a reader and the ad ceiling for book 1",
                 "Pen-name profit and loss with three shared cost rules", "Yearly return test for every title", "Keep, reprice, repackage or retire verdicts", "Box set case with break-even copies",
                 "Backlist and frontlist split by month", "Next book forecast in three scenarios", "%d calculators for series and title decisions" % len(tools), "%d printable sheets and %d documents" % (len(forms), len(documents)),
                 "Dashboard with %d live figures and %d charts" % (len(dashboard['kpis']), len(insights['charts']))]}
HINTS = {
 'series_money': 'Type books planned, cost each, release gap and your read-through; see 24 months of copies, royalties, payback and the book to stop at. Up to 6 books.',
 'target_books': 'Type the monthly royalties you want and what a new book brings; see the books needed, the months at your pace and the date.',
 'rt_tool': 'Pick a series and a step; see copies of book n and n+1, the read-through against your threshold and a verdict that names the step.',
 'drops_tool': 'Every series step ranked by readers lost; type the share you could win back to see the copies and royalties at stake.',
 'reader_value': 'Pick a series: royalty per copy times the read-through chain gives the value of a book-1 reader and the ad ceiling for book 1.',
 'price_test': 'Type the price and royalty share now and at the new price, the copies and the lift; later-book royalties of the readers are added.',
 'pen_pl': 'Type the months to look back; revenue, costs, shared costs, profit and margin of each pen name and which pen name to feed.',
 'rule_compare': 'Shared costs split equally, by revenue and by titles: profit of each pen name, the swing and the rule that leaves margins closest.',
 'box_case': 'Type single and box set prices, copies and set-up cost; see extra income a month, break-even copies and months to earn it back.',
 'bundle_check': 'Pick an existing box set: royalties of its single books before and after release against the box set royalties.',
 'catalogue_tool': 'Pick a title: age, royalties, ad spend, cost left, trend and role give keep, reprice, repackage or retire with one reason.',
 'return_tool': 'Pick a title and type your yearly return target; see the return, pass or fail and the royalties a month needed to pass.',
 'trend_tool': 'Pick a title: last 3 months against the 3 before, the same months last year and your own average, flagged by your limit.',
 'completion': 'Pick a series and the books left to write: new-book royalties plus the lift on earlier books against an average title elsewhere.',
 'next_book': 'Type list size, launch share, previous book copies and read-through; see Base, Best and Worst copies and months to earn back the cost.',
 'backlist_tool': 'Type the ages that count as backlist; see the share of royalties of the last 12 months from older titles, with a verdict.',
 'top3_tool': 'Type how many top titles to count and the share you accept; see their share, their names and the income lost if the top title stopped.',
 'pen_growth': 'Type the months in each period; royalties, copies and titles added by pen name against the period before, with a verdict.'}
for _t in tables + tools:
    if _t['key'] in HINTS: _t['hint'] = HINTS[_t['key']]
s = spec(id=f'{SUITE}-p6', slug='author-publisher-performance', profession='Author and Self-Publisher Business', name='Series, Title and Pen-Name Performance',
         tagline='Which books, series and pen names earn their keep', price_usd=29,
         colors={"primary": "#2B3A55", "accent": "#CE7777"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 6, "of": 8, "focus": "Series, title and pen-name performance"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'au6.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'name', len(s['name']))
