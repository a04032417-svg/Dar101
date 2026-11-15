"""Part 3: settings and the 20 tables."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au3_lists import *
import au3_data as D

MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def CA(k, label, fmt, f, w=12, **kw): return CALC(k, label, fmt, f, w, **kw)
def PHN(k, label, ph): return CA(k, label, 'text', '"%s"' % ph, 18)
def VAP(): return PHN('va_phone', 'Assistant phone', D.VA_PHONE)
def ACP(): return PHN('acct_phone', 'Accountant phone', D.ACCT_PHONE)
def OWP(): return PHN('owner_phone', 'Author phone', D.OWNER_PHONE)
def IMP(): return CA('company', 'Imprint', 'text', '{set:company}', 20)
def STORE_DELAY(c): return 'SUMIFS({range:stores.delay_days},{range:stores.store},%s)' % c
UNPAID = lambda: '(({range:statements.status}=%s)+({range:statements.status}=%s))' % (tok('ststatus', 'Expected'), tok('ststatus', 'Open'))
EXP, OPN, PD, SP = tok('ststatus', 'Expected'), tok('ststatus', 'Open'), tok('ststatus', 'Paid'), tok('ststatus', 'Short-paid')
ABOVE, WITHIN = tok('flag', 'Above limit'), tok('flag', 'Within limit')
LIVE = tok('estatus', 'Live')
YES = '{list:yesno.yes}'

settings = [
    S('company', 'Your imprint name', 'text', COMPANY), S('dependence_limit', 'Largest store share you accept', 'pct', STORE_DEPENDENCE_LIMIT),
    S('fee_flag_pct', 'Flag payments whose fees and exchange loss exceed', 'pct', FEE_FLAG_PCT), S('page_read_rate', 'Pay per 1,000 pages read (your own number)', 'num', 4.2),
    S('short_tolerance', 'Short-payment tolerance, amount', 'money', 5.0), S('grace_days', 'Days after the expected date that still count as on time', 'int', 5),
    S('escalate_days', 'Days past the expected date before you escalate', 'int', 30), S('monthly_costs', 'Your monthly costs (your own number)', 'money', 3500.0),
    S('cash_now', 'Cash on hand today', 'money', 8900.0), S('cash_floor', 'Lowest cash balance you want', 'money', CASH_FLOOR),
    S('change_flag_pct', 'Flag a change against your own history beyond', 'pct', 0.20), S('rate_step_pct', 'Page-read rate step for what-if (your own number)', 'pct', 0.20),
    S('min_months_sold', 'Months with a sale (of 12) that make a sale expected', 'int', 8), S('audio_target', 'Audio share of royalties you want', 'pct', 0.08),
    S('print_target', 'Paperback share of royalties you want', 'pct', 0.15), S('upside_pct', 'Best-case change for forecasts', 'pct', 0.10),
    S('downside_pct', 'Worst-case change for forecasts', 'pct', 0.15), S('near_pct', 'Near your own average means within', 'pct', 0.05),
]
assert 3 <= len(settings) <= 20
tables = []

# 1 sales ledger
tables.append(T('sales', 'Sales ledger', 'Sales ledger by edition, store and country',
    'One row per edition, store, country and month from a store report: copies, returns, gross and royalty in the store currency and the month rate; the royalty in your home currency fills in.', [
    C('sale_id', 'Sale ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), C('edition_id', 'Edition ID', 'text', 10), C('title_id', 'Title ID', 'text', 9), REF('title', 'Title', 'titles.title', 24),
    LST('format', 'Format', 'format', 12), LST('store', 'Store', 'store', 17), LST('country', 'Country', 'country', 14), LST('currency', 'Currency', 'currency', 15), C('units', 'Copies', 'int', 8),
    C('returns', 'Returns', 'int', 8), C('gross', 'Gross, store currency', 'money', 13), C('royalty', 'Royalty, store currency', 'money', 13), C('rate', 'Rate per 100 units', 'num', 10),
    CA('royalty_home', 'Royalty, home currency', 'money', '{col:royalty}*{col:rate}/100', 13), VAP(), OWP(), IMP()],
    D.sales_d(), 3000, [A('returns', '> 0', 'warn')]))
# 2 page reads
tables.append(T('pagereads', 'Page reads', 'Page-read income by edition and month',
    'One row per ebook edition and month in the lending program: pages read and pay per 1,000 pages (your own number, it moves every month); the income is an estimate and fills in.', [
    C('read_id', 'Read ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), C('edition_id', 'Edition ID', 'text', 10), C('title_id', 'Title ID', 'text', 9), REF('title', 'Title', 'titles.title', 24),
    C('pages_read', 'Pages read', 'int', 11), C('rate', 'Pay per 1,000 pages', 'num', 12), CA('income', 'Income, estimate', 'money', '{col:pages_read}/1000*{col:rate}', 12)],
    D.pagereads_d(), 600))
# 3 statements
tables.append(T('statements', 'Statements', 'Store statements with expected and paid dates',
    'One row per store and month: statement amount, paid date, amount received and status; the expected date (month end plus the store delay), days overdue and short amount fill in.', [
    C('statement_id', 'Statement ID', 'text', 11, required=True), C('month', 'Month', 'date', 11), LST('store', 'Store', 'store', 17), C('statement_amount', 'Statement amount', 'money', 13),
    C('paid_on', 'Paid on', 'date', 11), C('received', 'Received', 'money', 12), LST('status', 'Status', 'ststatus', 11),
    CA('expected_on', 'Expected on', 'date', 'EOMONTH({col:month},0)+%s' % STORE_DELAY('{col:store}'), 11),
    CA('days_overdue', 'Days overdue', 'int', 'IF(OR({col:status}=%s,{col:status}=%s),MAX(0,{today}-{col:expected_on}),0)' % (EXP, OPN), 9),
    CA('days_to_pay', 'Days to pay', 'int', 'IF({col:paid_on}>0,{col:paid_on}-{col:expected_on},"")', 9),
    CA('short_by', 'Short by', 'money', 'IF({col:status}=%s,{col:statement_amount}-{col:received},0)' % SP, 11), VAP(), ACP(), OWP(), IMP()],
    D.statements_d(), 600, [A('status', '= ' + SP, 'bad'), A('days_overdue', '> 0', 'bad'), A('status', '= ' + PD, 'good')]))
# 4 payments
tables.append(T('payments', 'Payments received', 'Payments received with fees and exchange loss',
    'One row per payment that reached your bank: the statement, its amount, the fee, the exchange loss and the amount received; the part that no fee explains fills in.', [
    C('payment_id', 'Payment ID', 'text', 10, required=True), C('statement_id', 'Statement ID', 'text', 11), LST('store', 'Store', 'store', 17), C('month', 'Month', 'date', 11), C('received_on', 'Received on', 'date', 11),
    C('statement_amount', 'Statement amount', 'money', 13), C('fee', 'Fee', 'money', 10), C('fx_loss', 'Exchange loss', 'money', 11), C('received', 'Received', 'money', 12),
    CA('unexplained', 'Short, not explained by fees', 'money', '{col:statement_amount}-{col:fee}-{col:fx_loss}-{col:received}', 13), VAP(), ACP(), OWP(), IMP()],
    D.payments_d(), 600, [A('unexplained', '> {set:short_tolerance}', 'bad')]))
# 5-8 reference tables
tables.append(T('rates', 'Exchange rates', 'Exchange rates',
    'One row per currency: the base rate, home currency per 100 units of the store currency (Home currency is 100). Edit it when your bank rate changes; the monthly rates used live in the currency table.', [
    LST('currency', 'Currency', 'currency', 18, required=True), C('rate', 'Rate per 100 units', 'num', 14)], D.rates_d(), 50))
tables.append(T('stores', 'Stores', 'Stores with royalty share and payment delay',
    'One row per store: the typical royalty share (check each store\'s current terms) and the days it takes to pay after month end (your own number, edit it from your statements).', [
    LST('store', 'Store', 'store', 20, required=True), C('royalty_share', 'Royalty share', 'pct', 12), C('delay_days', 'Delay, days', 'int', 11)], D.stores_d(), 50))
tables.append(T('countries', 'Countries', 'Countries with currency and sales tax',
    'One row per country: its store currency and the sales tax (VAT-style tax, confirm with your adviser).', [
    LST('country', 'Country', 'country', 18, required=True), LST('currency', 'Currency', 'currency', 18), C('sales_tax_pct', 'Sales tax', 'pct', 11)], D.countries_d(), 50))
tables.append(T('formats', 'Formats', 'Formats with royalty share and base cost',
    'One row per format: the typical royalty share (check each store\'s current terms) and the base cost of one copy.', [
    LST('format', 'Format', 'format', 18, required=True), C('royalty_share', 'Royalty share', 'pct', 12), C('base_cost', 'Base cost', 'money', 11)], D.formats_d(), 50))
# 9 editions
tables.append(T('editions', 'Editions', 'Editions with list price and royalty per copy',
    'One row per edition: format, list price, cost of one copy and the royalty share; the plan royalty per copy (price x share - cost) fills in by itself.', [
    C('edition_id', 'Edition ID', 'text', 10, required=True), C('title_id', 'Title ID', 'text', 9), REF('title', 'Title', 'titles.title', 24), LST('format', 'Format', 'format', 12), C('list_price', 'List price', 'money', 11),
    C('unit_cost', 'Cost of one copy', 'money', 12), C('royalty_share', 'Royalty share', 'pct', 11), LST('status', 'Status', 'estatus', 13),
    CA('royalty_per_copy', 'Plan royalty per copy', 'money', '{col:list_price}*{col:royalty_share}-{col:unit_cost}', 13)], D.editions_d(), 300))
# 10 titles
tables.append(T('titles', 'Titles', 'Titles with royalties of the last 12 months',
    'One row per title: pen name, series, release date, status and whether it is in the page-read program; the royalties, page-read income and share of the last 12 months fill in by themselves.', [
    C('title_id', 'Title ID', 'text', 9, required=True), C('title', 'Title', 'text', 28), LST('pen_name', 'Pen name', 'penname', 16), LST('series', 'Series', 'series', 20), C('release_date', 'Release date', 'date', 12),
    LST('status', 'Status', 'tstatus', 13), C('exclusive', 'In the page-read program', 'bool', 11),
    CA('royalty_12m', 'Royalties, 12 months', 'money', 'SUMIFS({range:edroy.royalty_home},{range:edroy.title_id},{col:title_id})', 13),
    CA('pr_12m', 'Page-read income, 12 months', 'money', 'SUMIFS({range:pagereads.income},{range:pagereads.title_id},{col:title_id},{range:pagereads.month},">="&EDATE(%s,-12),{range:pagereads.month},"<"&%s)' % (MS, MS), 13),
    CA('total_12m', 'Total income, 12 months', 'money', '{col:royalty_12m}+{col:pr_12m}', 13), CA('share_12m', 'Share of all', 'pct', 'IFERROR({col:total_12m}/SUM({range:titles.total_12m}),0)', 9),
    VAP(), OWP(), IMP()], D.titles_d(), 200))
# 11 mstore
tables.append(T('mstore', 'Royalty by month and store', 'Royalty by month and store',
    'One row per month and store from the store reports (type or paste the monthly totals): copies and royalty in your home currency; the share of the month and the 12-month total fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('store', 'Store', 'store', 17), C('units', 'Copies', 'int', 9), C('royalty_home', 'Royalty, home currency', 'money', 13),
    CA('share', 'Share of the month', 'pct', 'IFERROR({col:royalty_home}/SUMIFS({range:mstore.royalty_home},{range:mstore.month},{col:month}),0)', 10),
    CA('month_total', 'Royalty of the month', 'money', 'SUMIFS({range:mstore.royalty_home},{range:mstore.month},{col:month})', 13),
    CA('store_12m', 'Store, 12 months to this month', 'money', 'SUMIFS({range:mstore.royalty_home},{range:mstore.store},{col:store},{range:mstore.month},">="&EDATE({col:month},-11),{range:mstore.month},"<="&{col:month})', 13),
    CA('is_current', 'This month', 'int', 'IF({col:month}=%s,1,0)' % MS, 8), VAP(), ACP(), OWP(), IMP()], D.mstore_d(), 600))
# 12 mformat
tables.append(T('mformat', 'Royalty by month and format', 'Royalty by month and format',
    'One row per month and format from the store reports: copies and royalty in your home currency; the share of the month fills in by itself.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('format', 'Format', 'format', 12), C('units', 'Copies', 'int', 9), C('royalty_home', 'Royalty, home currency', 'money', 13),
    CA('share', 'Share of the month', 'pct', 'IFERROR({col:royalty_home}/SUMIFS({range:mformat.royalty_home},{range:mformat.month},{col:month}),0)', 10),
    CA('format_12m', 'Format, 12 months to this month', 'money', 'SUMIFS({range:mformat.royalty_home},{range:mformat.format},{col:format},{range:mformat.month},">="&EDATE({col:month},-11),{range:mformat.month},"<="&{col:month})', 13),
    VAP(), OWP(), IMP()], D.mformat_d(), 600))
# 13 edroy
tables.append(T('edroy', 'Royalty per copy by edition', 'Royalty per copy by edition, last 12 months',
    'One row per edition: copies and royalty of the last 12 months, copies of 3 months and this month, months with a sale; royalty per copy, plan and difference fill in.', [
    C('edition_id', 'Edition ID', 'text', 10, required=True), C('units', 'Copies, 12 months', 'int', 10), C('royalty_home', 'Royalty, 12 months', 'money', 13), C('units_3m', 'Copies, 3 months', 'int', 10),
    C('units_month', 'Copies this month', 'int', 10), C('months_sold', 'Months with a sale', 'int', 10),
    CA('title_id', 'Title ID', 'text', LOOK('editions.title_id', 'editions.edition_id', 'edition_id'), 9), CA('title', 'Title', 'text', LOOK('editions.title', 'editions.edition_id', 'edition_id'), 24),
    CA('format', 'Format', 'text', LOOK('editions.format', 'editions.edition_id', 'edition_id'), 12), CA('status', 'Status', 'text', LOOK('editions.status', 'editions.edition_id', 'edition_id'), 12),
    CA('in_program', 'In the page-read program', 'text', LOOK('titles.exclusive', 'titles.title_id', 'title_id'), 10),
    CA('royalty_per_copy', 'Royalty per copy', 'money', 'IF({col:units}>0,{col:royalty_home}/{col:units},"")', 11),
    CA('plan_per_copy', 'Plan royalty per copy', 'money', LOOK('editions.royalty_per_copy', 'editions.edition_id', 'edition_id'), 12),
    CA('difference', 'Difference', 'money', 'IF({col:royalty_per_copy}="","",{col:royalty_per_copy}-{col:plan_per_copy})', 11), VAP(), OWP(), IMP()],
    D.edroy_d(), 300, [A('difference', '< 0', 'warn')]))
# 14 earned
tables.append(T('earned', 'Earned against received', 'Earned against received by month and store',
    'One row per paid statement: pick the month and the store; the statement amount, the amount received, the difference, the share and the days paid after the expected date are read from Statements.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('store', 'Store', 'store', 17),
    CA('statement_amount', 'Statement amount', 'money', 'SUMIFS({range:statements.statement_amount},{range:statements.month},{col:month},{range:statements.store},{col:store})', 13),
    CA('received', 'Received', 'money', 'SUMIFS({range:statements.received},{range:statements.month},{col:month},{range:statements.store},{col:store})', 12),
    CA('difference', 'Difference', 'money', '{col:statement_amount}-{col:received}', 11),
    CA('difference_pct', 'Difference, share', 'pct', 'IF({col:statement_amount}=0,"",{col:difference}/{col:statement_amount})', 10),
    CA('days_late', 'Days late', 'int', 'IF(SUMIFS({range:statements.paid_on},{range:statements.month},{col:month},{range:statements.store},{col:store})=0,"",SUMIFS({range:statements.paid_on},{range:statements.month},{col:month},{range:statements.store},{col:store})-SUMIFS({range:statements.expected_on},{range:statements.month},{col:month},{range:statements.store},{col:store}))', 9),
    VAP(), OWP(), IMP()], D.earned_d(), 600, [A('difference_pct', '> 0.15', 'bad')]))
# 15 oldest
OLD_C = '(({range:statements.store}={col:store})*(({range:statements.status}=%s)+({range:statements.status}=%s)))' % (EXP, OPN)
tables.append(T('oldest', 'Oldest unpaid by store', 'Oldest unpaid month by store',
    'One row per store: the oldest month still unpaid and the days past the expected date (a negative number means the money is not due yet), read from Statements.', [
    LST('store', 'Store', 'store', 20, required=True),
    CA('oldest_month', 'Oldest unpaid month', 'date', 'IF(SUMPRODUCT(%s)=0,"",SUMPRODUCT(MIN(%s*{range:statements.month}+(1-%s)*99999)))' % (OLD_C, OLD_C, OLD_C), 14),
    CA('days_past', 'Days past expected', 'int', 'IF({col:oldest_month}="","",{today}-(EOMONTH({col:oldest_month},0)+%s)-MATCH({col:store},{range:oldest.store},0)/100)' % STORE_DELAY('{col:store}'), 14)],
    D.oldest_d(), 50, [A('days_past', '> 0', 'bad')]))
# 16 fees
tables.append(T('fees', 'Fee and exchange check', 'Fee and exchange loss check per payment',
    'One row per payment: pick the payment; the store, fee, exchange loss, the share of the statement they take and the flag above your limit are read from Payments received.', [
    REF('payment_id', 'Payment ID', 'payments.payment_id', 11, required=True),
    CA('store', 'Store', 'text', LOOK('payments.store', 'payments.payment_id', 'payment_id'), 17), CA('month', 'Month', 'date', LOOK('payments.month', 'payments.payment_id', 'payment_id'), 11),
    CA('fee', 'Fee', 'money', LOOK('payments.fee', 'payments.payment_id', 'payment_id'), 10), CA('fx_loss', 'Exchange loss', 'money', LOOK('payments.fx_loss', 'payments.payment_id', 'payment_id'), 11),
    CA('statement_amount', 'Statement amount', 'money', LOOK('payments.statement_amount', 'payments.payment_id', 'payment_id'), 13),
    CA('fee_share', 'Fees and loss, share of statement', 'pct', 'IF({col:statement_amount}=0,"",({col:fee}+{col:fx_loss})/{col:statement_amount})', 11),
    CA('flag', 'Limit check', 'text', 'IF({col:fee_share}="","",IF({col:fee_share}>{set:fee_flag_pct},%s,%s))' % (ABOVE, WITHIN), 12), VAP(), ACP(), OWP(), IMP()],
    D.fees_d(), 600, [A('flag', '= ' + ABOVE, 'warn')]))
# 17 prmonth
tables.append(T('prmonth', 'Page-read income by month', 'Page-read income by month',
    'One row per month: pages read, income and rate come from Page reads; the share of all royalties and the income at the rate minus and plus your step fill in. An estimate until paid.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('pages_read', 'Pages read in the month', 'int', 'SUMIFS({range:pagereads.pages_read},{range:pagereads.month},{col:month})', 11),
    CA('income', 'Income, estimate', 'money', 'SUMIFS({range:pagereads.income},{range:pagereads.month},{col:month})', 12),
    CA('avg_rate', 'Pay per 1,000 pages', 'num', 'IF({col:pages_read}=0,"",{col:income}/{col:pages_read}*1000)', 11),
    CA('royalties', 'Royalties of the month', 'money', 'SUMIFS({range:mstore.royalty_home},{range:mstore.month},{col:month})', 13),
    CA('share_all', 'Share of all royalties', 'pct', 'IFERROR({col:income}/({col:income}+{col:royalties}),0)', 10),
    CA('income_minus', 'Income at rate minus step', 'money', '{col:income}*(1-{set:rate_step_pct})', 12), CA('income_plus', 'Income at rate plus step', 'money', '{col:income}*(1+{set:rate_step_pct})', 12),
    CA('move_step', 'Move for one step', 'money', '{col:income}*{set:rate_step_pct}', 11),
    CA('change_prev', 'Against last month', 'pct', 'IFERROR({col:income}/SUMIFS({range:pagereads.income},{range:pagereads.month},EDATE({col:month},-1))-1,"")', 10), VAP(), OWP(), IMP()],
    D.prmonth_d(), 100))
# 18 ctyfmt
tables.append(T('ctyfmt', 'Royalty by country and format', 'Royalty by country and format, last 12 months',
    'One row per country and format: copies and royalty of the last 12 months and of the 12 months before, and copies this month; the share and the growth of the country fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), LST('country', 'Country', 'country', 15), LST('format', 'Format', 'format', 12), C('units', 'Copies, 12 months', 'int', 10), C('royalty_home', 'Royalty, 12 months', 'money', 13),
    C('royalty_prev', 'Royalty, 12 months before', 'money', 13), C('units_month', 'Copies this month', 'int', 10),
    CA('share', 'Share of all', 'pct', 'IFERROR({col:royalty_home}/SUM({range:ctyfmt.royalty_home}),0)', 9),
    CA('country_total', 'Country, 12 months', 'money', 'SUMIFS({range:ctyfmt.royalty_home},{range:ctyfmt.country},{col:country})', 13),
    CA('country_growth', 'Country growth', 'pct', 'IFERROR(SUMIFS({range:ctyfmt.royalty_home},{range:ctyfmt.country},{col:country})/SUMIFS({range:ctyfmt.royalty_prev},{range:ctyfmt.country},{col:country})-1,0)', 10),
    VAP(), OWP(), IMP()], D.ctyfmt_d(), 100))
# 19 depmonth
def MAXC(n): return 'SUMPRODUCT(%s)' % n
LA = 'SUMPRODUCT(MAX(({range:mstore.month}={col:month})*{range:mstore.royalty_home}))'
SA = 'SUMPRODUCT(LARGE(({range:mstore.month}={col:month})*{range:mstore.royalty_home},2))'
tables.append(T('depmonth', 'Store dependence by month', 'Store dependence by month',
    'One row per month: the largest and second largest store, their share of the royalties and a flag above your limit are read from Royalty by month and store.', [
    C('month', 'Month', 'date', 11, required=True), CA('month_total', 'Royalty of the month', 'money', 'SUMIFS({range:mstore.royalty_home},{range:mstore.month},{col:month})', 13),
    CA('largest_amount', 'Largest store amount', 'money', LA, 13), CA('largest_store', 'Largest store', 'text', 'IFERROR(INDEX({range:mstore.store},MATCH({col:largest_amount},{range:mstore.royalty_home},0)),"")', 17),
    CA('largest_share', 'Largest store share', 'pct', 'IF({col:month_total}=0,"",{col:largest_amount}/{col:month_total})', 10),
    CA('second_amount', 'Second store amount', 'money', SA, 13), CA('second_store', 'Second store', 'text', 'IFERROR(INDEX({range:mstore.store},MATCH({col:second_amount},{range:mstore.royalty_home},0)),"")', 17),
    CA('second_share', 'Second store share', 'pct', 'IF({col:month_total}=0,"",{col:second_amount}/{col:month_total})', 10),
    CA('flag', 'Limit check', 'text', 'IF({col:largest_share}="","",IF({col:largest_share}>{set:dependence_limit},%s,%s))' % (ABOVE, WITHIN), 12),
    CA('vs_last_year', 'Against the same month last year', 'pct', 'IFERROR({col:month_total}/SUMIFS({range:mstore.royalty_home},{range:mstore.month},EDATE({col:month},-12))-1,"")', 11), VAP(), OWP(), IMP()],
    D.depmonth_d(), 100, [A('flag', '= ' + ABOVE, 'bad')]))
# 20 curmonth
tables.append(T('curmonth', 'Royalty by currency and month', 'Royalty by currency and month with the rate effect',
    'One row per currency and month: the royalty in the store currency and the rate of the month; the home amount and the effect of the rate against your base rate fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('currency', 'Currency', 'currency', 16), C('amount_store', 'Royalty, store currency', 'money', 13), C('rate_used', 'Rate used per 100', 'num', 10),
    CA('base_rate', 'Base rate per 100', 'num', 'SUMIFS({range:rates.rate},{range:rates.currency},{col:currency})', 10),
    CA('home_amount', 'Royalty, home currency', 'money', '{col:amount_store}*{col:rate_used}/100', 13),
    CA('effect_home', 'Effect of the rate', 'money', '{col:amount_store}*({col:rate_used}-{col:base_rate})/100', 12), VAP(), ACP(), OWP(), IMP()],
    D.curmonth_d(), 300))
assert len(tables) == 20
HINTS = {}
