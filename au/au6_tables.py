"""Author and self-publisher suite part 6: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au6_lists import *
import au6_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def BYROLE(role): return 'IFERROR(INDEX({range:team.phone},MATCH(%s,{range:team.role},0))&"","")' % tok('role', role)
def NAMEROLE(role): return 'IFERROR(INDEX({range:team.name},MATCH(%s,{range:team.role},0))&"","")' % tok('role', role)
def PH(prefix, role, w=18):
    return [CA(prefix + '_phone', role + ' phone', 'text', BYROLE(role), w), CA(prefix + '_name', role + ' name', 'text', NAMEROLE(role), 20)]
def AU_PH(): return CA('author_phone', 'Author phone', 'text', BYROLE('Author-publisher'), 18)
def COMPANY_(): return CA('company', 'Imprint', 'text', '{set:company}', 20)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def WIN(rng, a=12, b=0):
    """criteria of the complete months from a months back up to (not including) b months back"""
    return '{range:%s},">="&EDATE(%s,-%d),{range:%s},"<"&%s' % (rng, MS, a, rng, MS if b == 0 else 'EDATE(%s,-%d)' % (MS, b))
REL = tok('tstatus', 'Released')
KEEP = tok('dverdict', 'Keep'); REPRICE = tok('dverdict', 'Reprice'); REPACK = tok('dverdict', 'Repackage'); RETIRE = tok('dverdict', 'Retire')
STEP1 = tok('bstep', 'Step 1')
SHARED = tok('xpen', 'Shared')

settings = [
    S('company', 'Your imprint name', 'text', COMPANY),
    S('return_target', 'Yearly return a title should earn (your own number)', 'pct', 0.10),
    S('readthrough_warn_1', 'Read-through you want, book 1 to 2 (your own number)', 'pct', READTHROUGH_WARN_1),
    S('readthrough_warn', 'Read-through you want at later steps (your own number)', 'pct', READTHROUGH_WARN),
    S('ad_share_of_breakeven', 'Share of a reader value you accept as ad cost', 'pct', AD_SHARE_OF_BREAKEVEN),
    S('cost_rule', 'Rule that splits shared costs between pen names', 'list', key('rule', 'By revenue'), list='rule'),
    S('target_income', 'Royalties you want each month (your own number)', 'money', 14000),
    S('trend_flag_pct', 'Change that makes a title growing or declining', 'pct', 0.20),
    S('margin_target', 'Profit margin you want for each pen name (your own number)', 'pct', 0.35),
    S('top3_limit', 'Highest share of royalties you accept from your top 3 titles', 'pct', 0.40),
    S('books_per_year', 'Books you can publish in a year', 'int', 2),
    S('lift_pct', 'Lift a new book gives earlier books (your own number)', 'pct', 0.05),
    S('reprice_pct', 'Price cut you test when sales fall', 'pct', 0.20),
    S('retire_floor', 'Royalties a month under which a title is not worth new spend', 'money', 310),
    S('payback_months', 'Months you accept to earn back a box set cost', 'int', 12),
    S('task_days', 'Days you give a freelancer for a review task', 'int', 30),
]
assert 3 <= len(settings) <= 20

tables = []
T0 = lambda *a, **k: tables.append(T(*a, **k))
# ---------------------------------------------------------------- 1 titles
T0('titles', 'Titles', 'Titles with cost, copies and royalties',
   'One row per title: your catalogue facts and production cost; the age, copies, royalties and ad spend of the last 12 months, the cost left to recover and the ranking key fill in by themselves.', [
    C('title_id', 'Title ID', 'text', 10, required=True), C('title', 'Title', 'text', 28), LST('pen_name', 'Pen name', 'penname', 16), LST('series', 'Series', 'series', 20), C('series_order', 'Book number', 'int', 8),
    LST('genre', 'Genre', 'genre', 14), C('release_date', 'Release date', 'date', 11), LST('status', 'Status', 'tstatus', 13), C('words', 'Words', 'int', 9), C('ebook_price', 'Ebook price', 'money', 10),
    C('royalty_before', 'Royalties before this workbook', 'money', 13), C('production_cost', 'Production cost', 'money', 12), C('expected_rt', 'Expected read-through into the next book', 'pct', 12),
    CA('age_months', 'Age (months)', 'int', 'MAX(0,(YEAR({today})-YEAR({col:release_date}))*12+MONTH({today})-MONTH({col:release_date}))', 8),
    CA('copies_12m', 'Copies, last 12 months', 'int', 'SUMIFS({range:tsales.units},{range:tsales.title},{col:title},%s)' % WIN('tsales.month'), 11),
    CA('royalties_12m', 'Royalties, last 12 months', 'money', 'SUMIFS({range:tsales.royalties},{range:tsales.title},{col:title},%s)' % WIN('tsales.month'), 13),
    CA('ad_12m', 'Ad spend, last 12 months', 'money', 'SUMIFS({range:tcosts.ad_spend},{range:tcosts.title},{col:title},%s)' % WIN('tcosts.month'), 12),
    CA('life_royalties', 'Royalties, lifetime', 'money', '{col:royalty_before}+SUMIFS({range:tsales.royalties},{range:tsales.title},{col:title})', 12),
    CA('cost_left', 'Cost left to recover', 'money', 'MAX(0,{col:production_cost}-{col:life_royalties})', 12),
    CA('rank_key', 'Ranking key', 'num', '{col:royalties_12m}+VALUE(RIGHT({col:title_id},3))/1000000', 11)],
   D.titles_d(), 50)
# ---------------------------------------------------------------- 2 series (reference)
T0('series', 'Series', 'Series and books planned', 'One row per series with the pen name and the books you plan; planned books feed the series money case and the books left to write.', [
    LST('series', 'Series', 'series', 22, required=True), C('pen_name', 'Pen name', 'text', 18), C('books_planned', 'Books planned', 'int', 10)], D.series_d(), 50)
# ---------------------------------------------------------------- 3 team
T0('team', 'Team', 'The author, assistant, freelancers and service providers',
   'The people you message from this workbook; the phone numbers feed the message links.', [
    C('person_id', 'Person ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 18), LST('team', 'Team', 'team', 14), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26)],
   D.team_d(), 50)
# ---------------------------------------------------------------- 4 sales by title and month
T0('tsales', 'Sales by Title and Month', 'Copies and royalties by title and month',
   'One row per title and month from your sales ledger (royalties in the home currency, page reads included); enter or paste your own monthly totals to replace a store import.', [
    C('row_id', 'Row ID', 'text', 9, required=True), REF('title', 'Title', 'titles.title', 28), C('month', 'Month', 'date', 10), LST('pen_name', 'Pen name', 'penname', 16), LST('series', 'Series', 'series', 20),
    C('units', 'Copies', 'int', 8), C('royalties', 'Royalties', 'money', 11),
    CA('release_date', 'Release date', 'date', LKD('titles.release_date', 'titles.title', 'title'), 11), CA('book_no', 'Book number', 'int', LKN('titles.series_order', 'titles.title', 'title'), 8)],
   D.tsales_d(), 800, [])
# ---------------------------------------------------------------- 5 costs by title and month
T0('tcosts', 'Costs by Title and Month', 'Ad spend and production paid by title and month',
   'One row per title and month with the ad spend and the production costs you paid (editors, cover, formatting, narration); titles and the pen-name profit and loss read these.', [
    C('row_id', 'Row ID', 'text', 9, required=True), REF('title', 'Title', 'titles.title', 28), C('month', 'Month', 'date', 10), LST('pen_name', 'Pen name', 'penname', 16), C('ad_spend', 'Ad spend', 'money', 11),
    C('production_paid', 'Production paid', 'money', 12)], D.tcosts_d(), 500)
# ---------------------------------------------------------------- 6 expenses
T0('expenses', 'Expenses', 'Business expenses with the pen name or Shared',
   'One row per expense: Shared means a cost of the whole imprint that the shared cost rule splits between the pen names; a pen name means a direct cost.', [
    C('expense_id', 'Expense ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 10), LST('category', 'Category', 'expcat', 20), C('vendor', 'Vendor', 'text', 26),
    C('amount', 'Amount', 'money', 11), LST('pen_name', 'Cost belongs to', 'xpen', 16)], D.expenses_d(), 400)
# ---------------------------------------------------------------- 7 read-through by step
T0('rtstep', 'Read-through by Step', 'Read-through of each series step against your thresholds',
   'One row per step of a series (book n to book n+1); copies of each in the last 12 months, the read-through, the flag against your thresholds, the readers lost and their value fill in by themselves.', [
    C('step_id', 'Step ID', 'text', 9, required=True), LST('series', 'Series', 'series4', 20), LST('stepno', 'Step', 'bstep', 9), REF('from_title', 'From title', 'titles.title', 28), REF('to_title', 'To title', 'titles.title', 28),
    C('checked_on', 'Checked on', 'date', 11),
    CA('copies_from', 'Copies of book n', 'int', LKN('titles.copies_12m', 'titles.title', 'from_title'), 10), CA('copies_to', 'Copies of book n+1', 'int', LKN('titles.copies_12m', 'titles.title', 'to_title'), 10),
    CA('readthrough', 'Read-through', 'pct', 'IF({col:copies_from}>0,{col:copies_to}/{col:copies_from},0)', 10),
    CA('rt_first', 'Book 1 to 2 read-through', 'pct', 'IF({col:stepno}=%s,{col:readthrough},"")' % STEP1, 10),
    CA('expected', 'Expected read-through', 'pct', LKN('titles.expected_rt', 'titles.title', 'from_title'), 10),
    CA('threshold', 'Your threshold', 'pct', 'IF({col:stepno}=%s,{set:readthrough_warn_1},{set:readthrough_warn})' % STEP1, 10),
    CA('flag', 'Step check', 'text', 'IF({col:readthrough}>={col:threshold},%s,%s)' % (v('Healthy step'), v('Below the threshold')), 18),
    CA('gap_pts', 'Gap to threshold (points)', 'pct', '{col:readthrough}-{col:threshold}', 10),
    CA('lost', 'Readers lost', 'int', 'MAX(0,{col:copies_from}-{col:copies_to})', 9),
    CA('lost_key', 'Ranking key', 'num', '{col:lost}+VALUE(RIGHT({col:step_id},2))/10000', 10),
    CA('royalty_copy', 'Royalty per copy of book n+1', 'money', 'IFERROR(INDEX({range:titles.royalties_12m},MATCH({col:to_title},{range:titles.title},0))/{col:copies_to},0)', 11),
    CA('lost_value', 'Value of the readers lost', 'money', '{col:lost}*{col:royalty_copy}', 11),
    CA('step_no', 'Step number', 'int', LKN('titles.series_order', 'titles.title', 'from_title'), 7)] + PH('va', 'Virtual assistant') + [AU_PH(), COMPANY_()],
   D.rtstep_d(), 50, [A('flag', '= ' + v('Below the threshold'), 'bad'), A('flag', '= ' + v('Healthy step'), 'good')])
# ---------------------------------------------------------------- 8 read-through chain
T0('chain', 'Read-through Chain', 'Copies by book number and the share of book 1',
   'One row per released book of a series: copies of the last 12 months, the share of book 1 that reaches it and the drop from the previous book fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 8, required=True), LST('series', 'Series', 'series4', 20), LST('bookno', 'Book', 'bookno', 9), REF('title', 'Title', 'titles.title', 28),
    CA('no', 'Book number', 'int', LKN('titles.series_order', 'titles.title', 'title'), 8), CA('copies', 'Copies, last 12 months', 'int', LKN('titles.copies_12m', 'titles.title', 'title'), 11),
    CA('book1', 'Copies of book 1', 'int', 'SUMIFS({range:titles.copies_12m},{range:titles.series},{col:series},{range:titles.series_order},1)', 10),
    CA('share_b1', 'Share of book 1', 'pct', 'IF({col:book1}>0,{col:copies}/{col:book1},0)', 9),
    CA('prev_copies', 'Copies of the previous book', 'int', 'IF({col:no}<=1,"",SUMIFS({range:titles.copies_12m},{range:titles.series},{col:series},{range:titles.series_order},{col:no}-1))', 11),
    CA('drop_prev', 'Drop from the previous book', 'pct', 'IF({col:no}<=1,"",IF({col:prev_copies}>0,1-{col:copies}/{col:prev_copies},0))', 11)], D.chain_d(), 50)
# ---------------------------------------------------------------- 9 where readers drop
T0('drops', 'Where Readers Drop', 'Series steps ranked by readers lost',
   'Rows 1 to 12 rank every series step by the readers lost (copies of book n minus copies of book n+1); the share of all readers lost, their value and a fix first verdict fill in by themselves.', [
    C('rank_no', 'Rank', 'int', 7, required=True),
    CA('pos', 'Row in read-through by step', 'int', 'IFERROR(MATCH(LARGE({range:rtstep.lost_key},{col:rank_no}),{range:rtstep.lost_key},0),"")', 9),
    CA('series', 'Series', 'text', 'IF({col:pos}="","",INDEX({range:rtstep.series},{col:pos}))', 20), CA('stepno', 'Step', 'text', 'IF({col:pos}="","",INDEX({range:rtstep.stepno},{col:pos}))', 9),
    CA('step_no', 'Step number', 'int', 'IF({col:pos}="","",INDEX({range:rtstep.step_no},{col:pos}))', 7),
    CA('from_title', 'From title', 'text', 'IF({col:pos}="","",INDEX({range:rtstep.from_title},{col:pos}))', 26), CA('to_title', 'To title', 'text', 'IF({col:pos}="","",INDEX({range:rtstep.to_title},{col:pos}))', 26),
    CA('lost', 'Readers lost', 'int', 'IF({col:pos}="","",INDEX({range:rtstep.lost},{col:pos}))', 9),
    CA('share_all', 'Share of all readers lost', 'pct', 'IF({col:pos}="","",IF(SUM({range:rtstep.lost})>0,{col:lost}/SUM({range:rtstep.lost}),0))', 11),
    CA('lost_value', 'Value of the readers lost', 'money', 'IF({col:pos}="","",INDEX({range:rtstep.lost_value},{col:pos}))', 11),
    CA('verdict', 'Verdict', 'text', 'IF({col:pos}="","",IF({col:rank_no}=1,%s,IF({col:rank_no}<=3,%s,%s)))' % (v('Fix first'), v('Fix next'), v('Fix later')), 11)] + [AU_PH(), COMPANY_()],
   D.drops_d(), 50, [A('verdict', '= ' + v('Fix first'), 'bad'), A('verdict', '= ' + v('Fix next'), 'warn')])
# ---------------------------------------------------------------- 10 value of a reader
T0('vreader', 'Value of a Reader', 'Royalties per book-1 reader along the series',
   'One row per released book: the share of book 1 readers who reach it, your royalty per copy, the cumulative value of a book-1 reader and the ad ceiling for book 1 fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 8, required=True), LST('series', 'Series', 'series4', 20), LST('bookno', 'Book', 'bookno', 9), REF('title', 'Title', 'titles.title', 28),
    CA('no', 'Book number', 'int', LKN('titles.series_order', 'titles.title', 'title'), 8), CA('copies', 'Copies, last 12 months', 'int', LKN('titles.copies_12m', 'titles.title', 'title'), 11),
    CA('share_b1', 'Share of book 1 readers', 'pct', 'IFERROR({col:copies}/SUMIFS({range:titles.copies_12m},{range:titles.series},{col:series},{range:titles.series_order},1),0)', 11),
    CA('rt_in', 'Read-through into this book', 'pct', 'IFERROR(INDEX({range:rtstep.readthrough},MATCH({col:title},{range:rtstep.to_title},0)),"")', 11),
    CA('roy_copy', 'Royalty per copy', 'money', 'IF({col:copies}>0,INDEX({range:titles.royalties_12m},MATCH({col:title},{range:titles.title},0))/{col:copies},0)', 10),
    CA('value_this', 'Value of this book per book-1 reader', 'money', '{col:share_b1}*{col:roy_copy}', 11),
    CA('value_cum', 'Cumulative value of a book-1 reader', 'money', 'SUMIFS({range:vreader.value_this},{range:vreader.series},{col:series},{range:vreader.no},"<="&{col:no})', 12),
    CA('series_value', 'Value over the whole series', 'money', 'IF({col:no}=COUNTIFS({range:titles.series},{col:series},{range:titles.status},%s),{col:value_cum},"")' % REL, 12),
    CA('ad_ceiling', 'Ad ceiling for book 1', 'money', '{col:value_cum}*{set:ad_share_of_breakeven}', 11)] + PH('ad', 'Ad specialist') + [AU_PH(), COMPANY_()], D.vreader_d(), 50)
# ---------------------------------------------------------------- 11 series income by month
T0('sincome', 'Series Income by Month', 'Series copies, royalties and 12-month forecast',
   'One row per series and month: copies and royalties from the sales sheet, the last 12 months, the books still to write and a forecast from your own last 3 months with a trend factor.', [
    C('row_id', 'Row ID', 'text', 8, required=True), LST('series', 'Series', 'series', 20), C('month', 'Month', 'date', 10),
    CA('copies', 'Copies', 'int', 'SUMIFS({range:tsales.units},{range:tsales.series},{col:series},{range:tsales.month},{col:month})', 8),
    CA('royalties', 'Royalties', 'money', 'SUMIFS({range:tsales.royalties},{range:tsales.series},{col:series},{range:tsales.month},{col:month})', 11),
    CA('copies_12m', 'Copies, last 12 months', 'int', 'SUMIFS({range:tsales.units},{range:tsales.series},{col:series},%s)' % WIN('tsales.month'), 11),
    CA('roy12', 'Royalties, last 12 months', 'money', 'SUMIFS({range:tsales.royalties},{range:tsales.series},{col:series},%s)' % WIN('tsales.month'), 12),
    CA('share_total', 'Share of all royalties', 'pct', 'IFERROR({col:roy12}/SUM({range:titles.royalties_12m}),0)', 9),
    CA('books_released', 'Books released', 'int', 'COUNTIFS({range:titles.series},{col:series},{range:titles.status},%s)' % REL, 9),
    CA('books_planned', 'Books planned', 'int', 'IFERROR(INDEX({range:series.books_planned},MATCH({col:series},{range:series.series},0)),0)', 9),
    CA('books_to_write', 'Books left to write', 'int', 'MAX(0,{col:books_planned}-COUNTIFS({range:titles.series},{col:series}))', 9),
    CA('cost_series', 'Production cost of the series', 'money', 'SUMIFS({range:titles.production_cost},{range:titles.series},{col:series})', 12),
    CA('avg_rt', 'Average read-through', 'pct', 'IFERROR(AVERAGEIFS({range:rtstep.readthrough},{range:rtstep.series},{col:series}),"")', 10),
    CA('lost_series', 'Readers lost in the series', 'int', 'SUMIFS({range:rtstep.lost},{range:rtstep.series},{col:series})', 10),
    CA('last3', 'Royalties, last 3 months', 'money', 'SUMIFS({range:tsales.royalties},{range:tsales.series},{col:series},%s)' % WIN('tsales.month', 3), 11),
    CA('prev3', 'Royalties, previous 3 months', 'money', 'SUMIFS({range:tsales.royalties},{range:tsales.series},{col:series},%s)' % WIN('tsales.month', 6, 3), 11),
    CA('forecast_12m', 'Forecast, next 12 months', 'money', 'IF({col:prev3}>0,{col:last3}/3*12*MIN(1.15,MAX(0.85,{col:last3}/{col:prev3})),{col:last3}/3*12)', 12),
    CA('n_keep', 'Titles to keep', 'int', 'COUNTIFS({range:decisions.series},{col:series},{range:decisions.verdict},%s)' % KEEP, 8),
    CA('n_reprice', 'Titles to reprice', 'int', 'COUNTIFS({range:decisions.series},{col:series},{range:decisions.verdict},%s)' % REPRICE, 8),
    CA('n_repack', 'Titles to repackage', 'int', 'COUNTIFS({range:decisions.series},{col:series},{range:decisions.verdict},%s)' % REPACK, 8),
    CA('n_retire', 'Titles to retire', 'int', 'COUNTIFS({range:decisions.series},{col:series},{range:decisions.verdict},%s)' % RETIRE, 8)] +
   PH('fm', 'Formatter') + PH('nar', 'Narrator') + PH('va', 'Virtual assistant') + [AU_PH(), COMPANY_()], D.sincome_d(), 120)
# ---------------------------------------------------------------- 12 pen-name profit and loss
RULE_SHARE = 'IF({set:cost_rule}=%s,SUMIFS({range:sharesplit.equal},{range:sharesplit.pen_name},{col:pen_name},{range:sharesplit.month},{col:month}),IF({set:cost_rule}=%s,SUMIFS({range:sharesplit.by_rev},{range:sharesplit.pen_name},{col:pen_name},{range:sharesplit.month},{col:month}),SUMIFS({range:sharesplit.by_titles},{range:sharesplit.pen_name},{col:pen_name},{range:sharesplit.month},{col:month})))' % (tok('rule', 'Equal'), tok('rule', 'By revenue'))
T0('pnl', 'Pen Profit', 'Pen-name revenue, costs and profit by month',
   'One row per pen name and month: royalties from the sales sheet, ads, production and own expenses as direct costs, shared costs under the rule you choose on Start, the profit and the margin.', [
    C('row_id', 'Row ID', 'text', 8, required=True), LST('pen_name', 'Pen name', 'penname', 16), C('month', 'Month', 'date', 10),
    CA('royalties', 'Royalties', 'money', 'SUMIFS({range:tsales.royalties},{range:tsales.pen_name},{col:pen_name},{range:tsales.month},{col:month})', 11),
    CA('copies', 'Copies', 'int', 'SUMIFS({range:tsales.units},{range:tsales.pen_name},{col:pen_name},{range:tsales.month},{col:month})', 8),
    CA('ads', 'Ad spend', 'money', 'SUMIFS({range:tcosts.ad_spend},{range:tcosts.pen_name},{col:pen_name},{range:tcosts.month},{col:month})', 10),
    CA('production', 'Production paid', 'money', 'SUMIFS({range:tcosts.production_paid},{range:tcosts.pen_name},{col:pen_name},{range:tcosts.month},{col:month})', 11),
    CA('own_exp', 'Own expenses', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.pen_name},{col:pen_name},{range:expenses.month},{col:month})', 10),
    CA('direct', 'Direct costs', 'money', '{col:ads}+{col:production}+{col:own_exp}', 10),
    CA('shared', 'Shared costs (your rule)', 'money', RULE_SHARE, 11),
    CA('profit', 'Profit', 'money', '{col:royalties}-{col:direct}-{col:shared}', 11),
    CA('margin', 'Margin', 'pct', 'IF({col:royalties}>0,{col:profit}/{col:royalties},0)', 8),
    CA('profit_eq', 'Profit, equal rule', 'money', '{col:royalties}-{col:direct}-SUMIFS({range:sharesplit.equal},{range:sharesplit.pen_name},{col:pen_name},{range:sharesplit.month},{col:month})', 11),
    CA('profit_rev', 'Profit, by revenue', 'money', '{col:royalties}-{col:direct}-SUMIFS({range:sharesplit.by_rev},{range:sharesplit.pen_name},{col:pen_name},{range:sharesplit.month},{col:month})', 11),
    CA('profit_tit', 'Profit, by titles', 'money', '{col:royalties}-{col:direct}-SUMIFS({range:sharesplit.by_titles},{range:sharesplit.pen_name},{col:pen_name},{range:sharesplit.month},{col:month})', 11),
    CA('profit_12m', 'Profit, last 12 months', 'money', 'SUMIFS({range:pnl.profit},{range:pnl.pen_name},{col:pen_name},%s)' % WIN('pnl.month'), 12),
    CA('share_profit', 'Share of 12-month profit', 'pct', 'IFERROR({col:profit_12m}/SUMIFS({range:pnl.profit},%s),0)' % WIN('pnl.month'), 10),
    CA('rule_name', 'Shared cost rule', 'text', '{set:cost_rule}', 12)] + PH('acc', 'Accountant') + [AU_PH(), COMPANY_()], D.pnl_d(), 80,
   [A('margin', '< {set:margin_target}', 'warn'), A('profit', '< 0', 'bad')])
# ---------------------------------------------------------------- 13 shared costs by rule
T0('sharesplit', 'Shared Costs by Rule', 'Shared costs split three ways for each pen name and month',
   'One row per pen name and month: the shared costs of the month split equally, by revenue and by the number of titles released, and the swing between the three rules.', [
    C('row_id', 'Row ID', 'text', 8, required=True), LST('pen_name', 'Pen name', 'penname', 16), C('month', 'Month', 'date', 10),
    CA('shared_total', 'Shared costs of the month', 'money', 'SUMIFS({range:expenses.amount},{range:expenses.pen_name},%s,{range:expenses.month},{col:month})' % SHARED, 12),
    CA('equal', 'Equal share', 'money', 'IFERROR({col:shared_total}/COUNTIFS({range:sharesplit.month},{col:month}),0)', 10),
    CA('by_rev', 'Share by revenue', 'money', 'IFERROR({col:shared_total}*SUMIFS({range:tsales.royalties},{range:tsales.pen_name},{col:pen_name},{range:tsales.month},{col:month})/SUMIFS({range:tsales.royalties},{range:tsales.month},{col:month}),0)', 11),
    CA('by_titles', 'Share by number of titles', 'money', 'IFERROR({col:shared_total}*COUNTIFS({range:titles.pen_name},{col:pen_name},{range:titles.release_date},"<="&EOMONTH({col:month},0))/COUNTIFS({range:titles.release_date},"<="&EOMONTH({col:month},0)),0)', 12),
    CA('swing', 'Swing between rules', 'money', 'MAX({col:equal},{col:by_rev},{col:by_titles})-MIN({col:equal},{col:by_rev},{col:by_titles})', 10),
    CA('rule_name', 'Shared cost rule', 'text', '{set:cost_rule}', 12)] + PH('acc', 'Accountant') + [COMPANY_()], D.sharesplit_d(), 80)
# ---------------------------------------------------------------- 14 box set and bundle cases
T0('bundles', 'Box Set and Bundle Cases', 'Box sets and bundles: income added and break-even',
   'One row per box set or bundle case: the prices, the copies you expect and the single-book copies it takes; the extra income a month, the break-even bundle copies and a verdict fill in by themselves.', [
    C('case_id', 'Case ID', 'text', 8, required=True), C('bundle', 'Bundle', 'text', 34), LST('series', 'Series', 'series', 20), C('books', 'Books in it', 'int', 8), C('singles_total', 'Prices of the single books', 'money', 11),
    C('bundle_price', 'Bundle price', 'money', 10), C('share', 'Royalty share', 'pct', 9), C('copies_month', 'Bundle copies a month', 'int', 10), C('taken_month', 'Single copies taken a month', 'int', 10),
    C('setup_cost', 'Set-up cost', 'money', 10), C('decide_by', 'Decide by', 'date', 11),
    CA('actual_month', 'Actual copies a month', 'int', 'IF(COUNTIFS({range:titles.title},{col:bundle})>0,ROUND(SUMIFS({range:tsales.units},{range:tsales.title},{col:bundle},%s)/12,0),"")' % WIN('tsales.month'), 10),
    CA('discount', 'Discount to the singles', 'pct', 'IF({col:singles_total}>0,1-{col:bundle_price}/{col:singles_total},0)', 9),
    CA('bundle_roy', 'Royalty per bundle copy', 'money', '{col:bundle_price}*{col:share}', 10),
    CA('single_roy', 'Royalty lost per single copy taken', 'money', 'IF({col:books}>0,{col:singles_total}/{col:books}*{col:share},0)', 11),
    CA('extra_month', 'Extra income a month', 'money', '{col:copies_month}*{col:bundle_roy}-{col:taken_month}*{col:single_roy}', 11),
    CA('net_copy', 'Net gain per bundle copy', 'money', 'IF({col:copies_month}>0,{col:bundle_roy}-{col:taken_month}/{col:copies_month}*{col:single_roy},0)', 11),
    CA('be_copies', 'Break-even bundle copies', 'int', 'IF({col:net_copy}>0,ROUNDUP({col:setup_cost}/{col:net_copy},0),"")', 10),
    CA('months_pay', 'Months to earn back', 'num', 'IF({col:extra_month}>0,{col:setup_cost}/{col:extra_month},"")', 9),
    CA('verdict', 'Verdict', 'text', 'IF(AND({col:extra_month}>0,{col:months_pay}<={set:payback_months}),%s,%s)' % (v('Make the box set'), v('Skip the box set')), 16)] +
   PH('dz', 'Cover designer') + PH('fm', 'Formatter') + PH('va', 'Virtual assistant') + PH('wd', 'Web developer') + [AU_PH(), COMPANY_()], D.bundles_d(), 50,
   [A('verdict', '= ' + v('Skip the box set'), 'bad'), A('verdict', '= ' + v('Make the box set'), 'good')])
# ---------------------------------------------------------------- 15 catalogue decisions
T0('decisions', 'Catalogue Decisions', 'Keep, reprice, repackage or retire for every title',
   'One row per title: age, royalties and ad spend of the last 12 months, the cost left, the trend, the role in the series and a calculated verdict with one reason; type the decision you took.', [
    C('title_id', 'Title ID', 'text', 9, required=True), REF('title', 'Title', 'titles.title', 28), LST('decision', 'Decision taken', 'dverdict', 11), C('review_on', 'Review on', 'date', 11),
    CA('status', 'Status', 'text', LKT('titles.status', 'titles.title', 'title'), 12), CA('series', 'Series', 'text', LKT('titles.series', 'titles.title', 'title'), 20),
    CA('order', 'Book number', 'int', LKN('titles.series_order', 'titles.title', 'title'), 8), CA('age', 'Age (months)', 'int', LKN('titles.age_months', 'titles.title', 'title'), 8),
    CA('roy12', 'Royalties, last 12 months', 'money', LKN('titles.royalties_12m', 'titles.title', 'title'), 12), CA('ad12', 'Ad spend, last 12 months', 'money', LKN('titles.ad_12m', 'titles.title', 'title'), 12),
    CA('cost_left', 'Cost left to recover', 'money', LKN('titles.cost_left', 'titles.title', 'title'), 12),
    CA('trend_chg', 'Change, last 3 months', 'pct', 'IFERROR(INDEX({range:trend.change_prev},MATCH({col:title},{range:trend.title},0)),"")', 10),
    CA('ret', 'Yearly return', 'pct', 'IFERROR(INDEX({range:ytest.ret},MATCH({col:title},{range:ytest.title},0)),"")', 9),
    CA('role', 'Role in the series', 'text', 'IF({col:series}=%s,%s,IF({col:series}=%s,%s,IF({col:order}=1,%s,%s)))' % (tok('series', 'Box set'), v('Box set'), tok('series', 'Standalone'), v('Standalone book'), v('Book 1'), v('Later book')), 14),
    CA('later_open', 'Later books not yet released', 'int', 'IF({col:order}>0,COUNTIFS({range:titles.series},{col:series},{range:titles.series_order},">"&{col:order},{range:titles.status},"<>"&%s),0)' % REL, 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:status}<>%s,%s,IF(AND({col:cost_left}>0,{col:age}>=18),%s,IF(AND({col:roy12}/12<{set:retire_floor},{col:role}<>%s,{col:later_open}=0,OR({col:trend_chg}="",{col:trend_chg}<={set:trend_flag_pct})),%s,IF(AND({col:ret}<>"",{col:ret}<{set:return_target}),%s,IF(AND({col:trend_chg}<>"",{col:trend_chg}<-{set:trend_flag_pct},{col:age}>=6),%s,%s)))))' % (
        REL, KEEP, REPACK, v('Book 1'), RETIRE, REPACK, REPRICE, KEEP), 11),
    CA('reason', 'Reason', 'text', 'IF({col:verdict}=%s,IF({col:status}<>%s,%s,%s),IF({col:verdict}=%s,IF(AND({col:cost_left}>0,{col:age}>=18),%s,%s),IF({col:verdict}=%s,%s,%s)))' % (
        KEEP, REL, v('Not released yet'), v('Earns its cost and holds its sales'), REPACK, v('Cost not earned back'), v('Fails the return test'), REPRICE, v('Sales are falling, test a price'), v('Earns little, no series needs it')), 30),
    CA('new_price', 'Price to test', 'money', 'IFERROR(ROUND(INDEX({range:titles.ebook_price},MATCH({col:title},{range:titles.title},0))*(1-{set:reprice_pct}),2),0)', 10),
    CA('due_date', 'Task due date', 'date', '{today}+{set:task_days}', 11)] +
   PH('dz', 'Cover designer') + PH('va', 'Virtual assistant') + PH('ra', 'Rights agent') + PH('co', 'Launch coordinator') + [AU_PH(), COMPANY_()], D.decisions_d(), 50,
   [A('verdict', '= ' + RETIRE, 'bad'), A('verdict', '= ' + REPACK, 'warn'), A('verdict', '= ' + REPRICE, 'warn'), A('verdict', '= ' + KEEP, 'good')])
# ---------------------------------------------------------------- 16 yearly return test
T0('ytest', 'Yearly Return Test', 'Royalties of the last 12 months against production cost',
   'One row per title: production cost, royalties of the last 12 months, the yearly return against your target, pass or fail and the royalties a month a title needs to pass.', [
    C('title_id', 'Title ID', 'text', 9, required=True), REF('title', 'Title', 'titles.title', 28), LST('series', 'Series', 'series', 20), C('tested_on', 'Tested on', 'date', 11),
    CA('status', 'Status', 'text', LKT('titles.status', 'titles.title', 'title'), 12), CA('cost', 'Production cost', 'money', LKN('titles.production_cost', 'titles.title', 'title'), 11),
    CA('roy12', 'Royalties, last 12 months', 'money', LKN('titles.royalties_12m', 'titles.title', 'title'), 12), CA('age', 'Age (months)', 'int', LKN('titles.age_months', 'titles.title', 'title'), 8),
    CA('ret', 'Yearly return', 'pct', 'IF(AND({col:status}=%s,{col:cost}>0),{col:roy12}/{col:cost},"")' % REL, 9),
    CA('target', 'Your target', 'pct', '{set:return_target}', 8),
    CA('pass', 'Result', 'text', 'IF({col:ret}="",%s,IF({col:ret}>={col:target},%s,%s))' % (v('Not tested'), v('Passes'), v('Fails')), 12),
    CA('need_month', 'Royalties a month needed', 'money', '{col:target}*{col:cost}/12', 11),
    CA('gap_month', 'Short of it each month', 'money', 'IF({col:ret}="","",MAX(0,{col:need_month}-{col:roy12}/12))', 11)] + PH('ad', 'Ad specialist') + [AU_PH(), COMPANY_()],
   D.ytest_d(), 50, [A('pass', '= ' + v('Fails'), 'bad'), A('pass', '= ' + v('Passes'), 'good')])
# ---------------------------------------------------------------- 17 title trend
T0('trend', 'Title Trend', 'Last 3 months against your own history',
   'One row per title: royalties of the last 3 months, the 3 months before and the same 3 months a year ago; the change against each and a growing, flat or declining flag fill in by themselves.', [
    C('title_id', 'Title ID', 'text', 9, required=True), REF('title', 'Title', 'titles.title', 28),
    CA('last3', 'Last 3 months', 'money', 'SUMIFS({range:tsales.royalties},{range:tsales.title},{col:title},%s)' % WIN('tsales.month', 3), 11),
    CA('prev3', 'Previous 3 months', 'money', 'SUMIFS({range:tsales.royalties},{range:tsales.title},{col:title},%s)' % WIN('tsales.month', 6, 3), 11),
    CA('ly3', 'Same 3 months last year', 'money', 'SUMIFS({range:tsales.royalties},{range:tsales.title},{col:title},%s)' % WIN('tsales.month', 15, 12), 11),
    CA('change_prev', 'Change against previous 3 months', 'pct', 'IF({col:prev3}>0,{col:last3}/{col:prev3}-1,"")', 11), CA('change_ly', 'Change against last year', 'pct', 'IF({col:ly3}>0,{col:last3}/{col:ly3}-1,"")', 11),
    CA('avg3', 'Your 3-month average', 'money', 'INDEX({range:titles.royalties_12m},MATCH({col:title},{range:titles.title},0))/4', 11),
    CA('vs_avg', 'Last 3 months against your average', 'pct', 'IF({col:avg3}>0,{col:last3}/{col:avg3}-1,"")', 11),
    CA('flag', 'Trend', 'text', 'IF({col:change_prev}="",%s,IF({col:change_prev}>{set:trend_flag_pct},%s,IF({col:change_prev}<-{set:trend_flag_pct},%s,%s)))' % (v('Too new to judge'), v('Growing'), v('Declining'), v('Flat')), 14),
    AU_PH(), COMPANY_()], D.trend_d(), 50, [A('flag', '= ' + v('Declining'), 'bad'), A('flag', '= ' + v('Growing'), 'good')])
# ---------------------------------------------------------------- 18 target income steps
T0('target', 'Target Income Steps', 'Books needed to reach each monthly income target',
   'One row per target step: the royalties you want a month, the average a book brings and the books on sale; the books needed at your lift and the months at your publishing pace fill in by themselves.', [
    C('step_id', 'Step ID', 'text', 8, required=True), LST('tstep', 'Step', 'tstep', 9), C('target_income', 'Target income a month', 'money', 11), C('avg_roy_book', 'Average royalties a book a month', 'money', 12),
    C('books_on_sale', 'Books on sale', 'int', 9), C('review_on', 'Review on', 'date', 11),
    CA('now_income', 'Royalties a month now', 'money', 'SUM({range:titles.royalties_12m})/12', 11), CA('gap', 'Gap to the target', 'money', 'MAX(0,{col:target_income}-{col:now_income})', 11),
    CA('per_book', 'Added by one new book', 'money', '{col:avg_roy_book}*(1+{set:lift_pct})', 11),
    CA('books_needed', 'Books needed', 'int', 'IF({col:gap}<=0,0,ROUNDUP({col:gap}/{col:per_book},0))', 9),
    CA('months_pace', 'Months at your pace', 'num', '{col:books_needed}/MAX(1,{set:books_per_year})*12', 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:gap}<=0,%s,IF({col:months_pace}<=24,%s,%s))' % (v('Target reached'), v('Reachable'), v('Far away')), 13), AU_PH(), COMPANY_()], D.target_d(), 50,
   [A('verdict', '= ' + v('Far away'), 'warn'), A('verdict', '= ' + v('Reachable'), 'good')])
# ---------------------------------------------------------------- 19 title ranking
T0('ranking', 'Title Ranking', 'Titles ranked by royalties of the last 12 months',
   'Rows 1 to 22 rank every title by royalties of the last 12 months; the share and the cumulative share, so the dependence on the top titles is visible.', [
    C('rank_no', 'Rank', 'int', 7, required=True),
    CA('pos', 'Row in titles', 'int', 'IFERROR(MATCH(LARGE({range:titles.rank_key},{col:rank_no}),{range:titles.rank_key},0),"")', 9),
    CA('title', 'Title', 'text', 'IF({col:pos}="","",INDEX({range:titles.title},{col:pos}))', 28), CA('pen_name', 'Pen name', 'text', 'IF({col:pos}="","",INDEX({range:titles.pen_name},{col:pos}))', 16),
    CA('series', 'Series', 'text', 'IF({col:pos}="","",INDEX({range:titles.series},{col:pos}))', 20), CA('roy12', 'Royalties, last 12 months', 'money', 'IF({col:pos}="","",INDEX({range:titles.royalties_12m},{col:pos}))', 12),
    CA('share', 'Share of royalties', 'pct', 'IF({col:pos}="","",IFERROR({col:roy12}/SUM({range:titles.royalties_12m}),0))', 9),
    CA('cum_share', 'Cumulative share', 'pct', 'IF({col:pos}="","",IFERROR(SUMIFS({range:titles.royalties_12m},{range:titles.rank_key},">="&LARGE({range:titles.rank_key},{col:rank_no}))/SUM({range:titles.royalties_12m}),0))', 10),
    CA('top3_share', 'Share of the top 3 titles', 'pct', 'IFERROR(SUMIFS({range:titles.royalties_12m},{range:titles.rank_key},">="&LARGE({range:titles.rank_key},3))/SUM({range:titles.royalties_12m}),0)', 11),
    AU_PH(), COMPANY_()], D.ranking_d(), 50)
# ---------------------------------------------------------------- 20 backlist and frontlist
T0('backlist', 'Backlist and Frontlist', 'Royalties of older titles against titles under 12 months',
   'One row per month: royalties of titles released in the last 12 months (frontlist) and of older titles (backlist) and the backlist share, so you see how much of your income the old books carry.', [
    C('month', 'Month', 'date', 10, required=True),
    CA('front', 'Frontlist royalties', 'money', 'SUMIFS({range:tsales.royalties},{range:tsales.month},{col:month},{range:tsales.release_date},">"&EDATE({col:month},-12))', 12),
    CA('back', 'Backlist royalties', 'money', 'SUMIFS({range:tsales.royalties},{range:tsales.month},{col:month},{range:tsales.release_date},"<="&EDATE({col:month},-12))', 12),
    CA('total', 'Total royalties', 'money', '{col:front}+{col:back}', 11), CA('backlist_share', 'Backlist share', 'pct', 'IF({col:total}>0,{col:back}/{col:total},0)', 9),
    CA('older24', 'Titles older than 24 months', 'money', 'SUMIFS({range:tsales.royalties},{range:tsales.month},{col:month},{range:tsales.release_date},"<="&EDATE({col:month},-24))', 12),
    CA('older24_share', 'Share older than 24 months', 'pct', 'IF({col:total}>0,{col:older24}/{col:total},0)', 10), AU_PH(), COMPANY_()], D.backlist_d(), 50)
assert len(tables) == 20, len(tables)
