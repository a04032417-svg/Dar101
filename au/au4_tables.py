"""Author and Self-Publisher suite part 4: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au4_lists import *
import au4_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def PERS(pre, label, name, phone):
    first = name if name.startswith('Partner') else name.split()[0]
    return [CA(pre, label + ' name', 'text', tok('person', first), 14), CA(pre + '_phone', label + ' phone', 'text', '"%s"' % phone, 18)]
def IMPRINT(): return CA('imprint', 'Imprint', 'text', '{set:company}', 22)


MS = 'DATE(YEAR({today}),MONTH({today}),1)'
RUN = tok('adstatus', 'Running'); PAU = tok('adstatus', 'Paused'); EBK = tok('format', 'Ebook'); DONE = tok('pstatus', 'Done'); PLN = tok('pstatus', 'Planned')
def AD(col, crit): return 'SUMIFS({range:adsdays.%s},%s)' % (col, crit)
W30 = '{range:adsdays.date},">="&({today}-30)'; W60 = '{range:adsdays.date},">="&({today}-60)'


def ROYN(price, share, cost):                 # royalty per copy after cost, never below 0
    return 'MAX(0,(%s)*(%s)-(%s))' % (price, share, cost)
def SHARE_AT(price, share): return 'IF((%s)<{set:low_price_limit},{set:low_price_share},%s)' % (price, share)


settings = [
    S('company', 'Your imprint name', 'text', COMPANY),
    S('ad_return_target', 'Return target per unit spent (your own number)', 'num', AD_RETURN_TARGET),
    S('ad_raise_return', 'Raise a campaign at this return or higher (your own number)', 'num', 1.5),
    S('ad_share_of_breakeven', 'Target share of break-even cost (typical 30-40%)', 'pct', AD_SHARE_OF_BREAKEVEN),
    S('conversion_floor', 'Conversion floor (under 2-3% is often a page problem)', 'pct', CONVERSION_FLOOR),
    S('ad_deterioration_pct', 'Flag a change in return beyond this share (your own number)', 'pct', AD_DETERIORATION_PCT),
    S('page_read_rate', 'Pay per page read (your own number, it moves every month)', 'num', PAGE_READ_RATE),
    S('ad_budget_month', 'Monthly ad budget (your own number)', 'money', 1600),
    S('ad_share_limit', 'Highest ad spend as a share of royalties (your own number)', 'pct', 0.15),
    S('min_ad_days', 'Days a campaign runs before it gets a verdict', 'int', 14),
    S('raise_step_pct', 'Budget raise step for a campaign to raise', 'pct', 0.25),
    S('low_price_limit', 'Ebook price under which the share is lower (check terms)', 'money', 1.5),
    S('low_price_share', 'Lower royalty share (a typical range, check terms)', 'pct', 0.35),
    S('price_test_margin', 'Royalty gap a price test must show (your own number)', 'pct', 0.05),
    S('test_min_units', 'Copies a price test needs in each period', 'int', 30),
]
assert 3 <= len(settings) <= 20

tables = []
# ---------------------------------------------------------------- 1 campaigns
tables.append(T('campaigns', 'Campaigns', 'Ad campaigns with budget, bid and return',
    'One row per ad campaign: title, platform, dates, status, daily budget and bid; the return of the last 60 days, the target bid, the raised budget and the message fields fill in by themselves.', [
    C('campaign_id', 'Campaign ID', 'text', 10, required=True), C('campaign', 'Campaign', 'text', 34), REF('title', 'Title', 'titles.title', 28), LST('platform', 'Platform', 'platform', 12),
    C('start_date', 'Start date', 'date', 11), C('end_date', 'End date', 'date', 11), LST('status', 'Status', 'adstatus', 10), C('daily_budget', 'Daily budget', 'money', 11), C('bid', 'Bid per click', 'money', 11),
    C('reviewed_on', 'Last reviewed on', 'date', 12),
    CA('return_60', 'Return, 60 days', 'num', LKN('ledger.return_60', 'ledger.campaign_id', 'campaign_id'), 10),
    CA('return_text', 'Return as percent text', 'text', 'ROUND({col:return_60}*100,0)&"%"', 10),
    CA('target_bid', 'Target bid', 'money', LKN('maxbid.target_bid', 'maxbid.campaign_id', 'campaign_id'), 10),
    CA('new_budget', 'Budget after a raise', 'money', 'ROUND({col:daily_budget}*(1+{set:raise_step_pct}),0)', 11)] +
    PERS('specialist', 'Ad specialist', D.SPEC['name'], D.SPEC['phone']) + PERS('assistant', 'Assistant', D.VA['name'], D.VA['phone']) + PERS('owner', 'Author', D.OWN['name'], D.OWN['phone']) + [IMPRINT()],
    D.campaigns_d(), 100, [A('status', '= ' + RUN, 'good'), A('status', '= ' + PAU, 'warn'), A('return_60', '< {set:ad_return_target}', 'bad')]))
# ---------------------------------------------------------------- 2 ad days
tables.append(T('adsdays', 'Ad Days', 'Ad days: spend, clicks, sales and royalties',
    'One row per campaign and day of ad numbers (older ended campaigns are kept as one row per week part, the Days column says how many days a row covers); the campaign, title, platform, month, profit and cost per click fill in by themselves.', [
    C('ad_id', 'Ad ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), REF('campaign_id', 'Campaign ID', 'campaigns.campaign_id', 10), C('days', 'Days in row', 'int', 8),
    C('spend', 'Spend', 'money', 10), C('impressions', 'Impressions', 'int', 11), C('clicks', 'Clicks', 'int', 9), C('sales', 'Sales', 'int', 8), C('page_reads', 'Page reads', 'int', 10), C('royalties', 'Royalties with page reads', 'money', 13),
    CA('month', 'Month', 'date', 'IF({col:date}>0,DATE(YEAR({col:date}),MONTH({col:date}),1),"")', 11),
    CA('campaign', 'Campaign', 'text', LKT('campaigns.campaign', 'campaigns.campaign_id', 'campaign_id'), 34),
    CA('title_id', 'Title ID', 'text', 'IFERROR(INDEX({range:titles.title_id},MATCH(INDEX({range:campaigns.title},MATCH({col:campaign_id},{range:campaigns.campaign_id},0)),{range:titles.title},0))&"","")', 9),
    CA('platform', 'Platform', 'text', LKT('campaigns.platform', 'campaigns.campaign_id', 'campaign_id'), 12),
    CA('profit', 'Profit', 'money', '{col:royalties}-{col:spend}', 10), CA('cpc', 'Cost per click', 'money', 'IF({col:clicks}=0,0,{col:spend}/{col:clicks})', 10)] +
    PERS('assistant', 'Assistant', D.VA['name'], D.VA['phone']) + [IMPRINT()],
    D.adsdays_d(), 2200, [A('profit', '< 0', 'warn')]))
# ---------------------------------------------------------------- 3 promotions
tables.append(T('promos', 'Promotions', 'Price promotions with before, during and after',
    'One row per price promotion: title, kind, dates, normal and promo price, cost and the copies and page reads before, during and after (equal periods); the days to start and the message fields fill in by themselves.', [
    C('promo_id', 'Promotion ID', 'text', 10, required=True), REF('title', 'Title', 'titles.title', 28), LST('kind', 'Kind', 'pkind', 13), C('start_date', 'Start date', 'date', 11), C('end_date', 'End date', 'date', 11),
    C('days', 'Days', 'int', 7), C('normal_price', 'Normal price', 'money', 11), C('promo_price', 'Promo price', 'money', 11), C('cost', 'Cost', 'money', 10), C('units_before', 'Copies before', 'int', 9),
    C('units_during', 'Copies during', 'int', 9), C('units_after', 'Copies after', 'int', 9), C('pages_before', 'Pages before', 'int', 10), C('pages_during', 'Pages during', 'int', 10), LST('status', 'Status', 'pstatus', 9),
    CA('days_to_start', 'Days to start', 'int', 'IF({col:start_date}>0,{col:start_date}-{today},"")', 9)] +
    PERS('partner', 'Newsletter partner', D.PARTNER['partner'], D.PARTNER['phone']) + PERS('developer', 'Web developer', D.DEV['name'], D.DEV['phone']) + PERS('assistant', 'Assistant', D.VA['name'], D.VA['phone']) +
    PERS('owner', 'Author', D.OWN['name'], D.OWN['phone']) + [IMPRINT()],
    D.promos_d(), 100, [A('status', '= ' + PLN, 'warn'), A('status', '= ' + DONE, 'good')]))
# ---------------------------------------------------------------- 4 price tests
tables.append(T('pricetests', 'Price Tests', 'Price tests: price A against price B',
    'One row per price test: two prices over equal periods with the copies sold and the royalty per copy at each price; copies a day and the total royalty at each price fill in by themselves.', [
    C('test_id', 'Test ID', 'text', 9, required=True), REF('title', 'Title', 'titles.title', 28), C('start_date', 'Start date', 'date', 11), C('price_a', 'Price A', 'money', 9), C('price_b', 'Price B', 'money', 9),
    C('days_a', 'Days at A', 'int', 8), C('days_b', 'Days at B', 'int', 8), C('units_a', 'Copies at A', 'int', 9), C('units_b', 'Copies at B', 'int', 9), C('royalty_a', 'Royalty per copy at A', 'money', 11),
    C('royalty_b', 'Royalty per copy at B', 'money', 11),
    CA('units_day_a', 'Copies a day at A', 'num', 'IF({col:days_a}=0,0,{col:units_a}/{col:days_a})', 10), CA('units_day_b', 'Copies a day at B', 'num', 'IF({col:days_b}=0,0,{col:units_b}/{col:days_b})', 10),
    CA('total_royalty_a', 'Total royalty at A', 'money', '{col:units_a}*{col:royalty_a}', 11), CA('total_royalty_b', 'Total royalty at B', 'money', '{col:units_b}*{col:royalty_b}', 11)],
    D.pricetests_d(), 60, []))
# ---------------------------------------------------------------- 5 titles
tables.append(T('titles', 'Titles', 'Titles with pen name, series and release date',
    'One row per title; the ad and promotion sheets look the title name up here.', [
    C('title_id', 'Title ID', 'text', 9, required=True), C('title', 'Title', 'text', 28), LST('pen_name', 'Pen name', 'penname', 16), LST('series', 'Series', 'series', 20), C('release_date', 'Release date', 'date', 12),
    LST('status', 'Status', 'tstatus', 12), C('exclusive', 'In the page-read program', 'bool', 11)],
    D.titles_d(), 60, []))
# ---------------------------------------------------------------- 6 editions
tables.append(T('editions', 'Editions', 'Editions with price, cost and royalty share',
    'One row per edition (title and format): list price, unit cost, the royalty share (check each store\'s current terms) and the status; the break-even sheets read the price and cost from here.', [
    C('edition_id', 'Edition ID', 'text', 10, required=True), REF('title', 'Title', 'titles.title', 28), LST('format', 'Format', 'format', 12), C('list_price', 'List price', 'money', 10), C('unit_cost', 'Unit cost', 'money', 10),
    C('royalty_share', 'Royalty share', 'pct', 10), LST('status', 'Status', 'estatus', 12)],
    D.editions_d(), 120, []))
# ---------------------------------------------------------------- 7 platforms
tables.append(T('platforms', 'Platforms', 'Ad platforms with typical cost per click',
    'One row per paid channel: a typical cost per click and the lowest daily budget it accepts (a typical range, check current terms); the last two rows are channels you may add later.', [
    C('platform', 'Platform', 'text', 22, required=True), C('typical_cpc', 'Typical cost per click', 'money', 12), C('daily_min', 'Daily minimum', 'money', 10)],
    D.platforms_d(), 50, []))
# ---------------------------------------------------------------- 8 stores
tables.append(T('stores', 'Stores', 'Stores with royalty share and payment delay',
    'One row per store: the typical royalty share (check each store\'s current terms) and the days it pays after month end; the break-even sheets use the share.', [
    LST('store', 'Store', 'store', 20, required=True), C('royalty_share', 'Royalty share', 'pct', 11), C('delay_days', 'Delay, days', 'int', 10)],
    D.stores_d(), 50, []))
# ---------------------------------------------------------------- 9 break-even by edition
tables.append(T('breakeven', 'Break-Even by Edition', 'Break-even ad cost by edition and store',
    'One row per edition and store: the royalty per copy after cost, the share of the price you can spend on ads at break-even, your target share and the highest cost per sale at each; everything fills in by itself.', [
    REF('edition_id', 'Edition ID', 'editions.edition_id', 10, required=True),
    CA('title', 'Title', 'text', LKT('editions.title', 'editions.edition_id', 'edition_id'), 28), CA('format', 'Format', 'text', LKT('editions.format', 'editions.edition_id', 'edition_id'), 12),
    LST('store', 'Store', 'store', 18),
    CA('price', 'List price', 'money', LKN('editions.list_price', 'editions.edition_id', 'edition_id'), 10),
    CA('unit_cost', 'Unit cost', 'money', LKN('editions.unit_cost', 'editions.edition_id', 'edition_id'), 10),
    CA('share_used', 'Royalty share used', 'pct', 'IF(AND({col:format}=%s,{col:price}<{set:low_price_limit}),{set:low_price_share},SUMIFS({range:stores.royalty_share},{range:stores.store},{col:store}))' % EBK, 11),
    CA('royalty_per_copy', 'Royalty per copy', 'money', ROYN('{col:price}', '{col:share_used}', '{col:unit_cost}'), 11),
    CA('break_even_share', 'Break-even ad share of price', 'pct', 'IF({col:price}=0,0,{col:royalty_per_copy}/{col:price})', 12),
    CA('target_share', 'Target ad share of price', 'pct', '{col:break_even_share}*{set:ad_share_of_breakeven}', 12),
    CA('break_even_cps', 'Break-even cost per sale', 'money', '{col:royalty_per_copy}', 12),
    CA('target_cps', 'Target cost per sale', 'money', '{col:royalty_per_copy}*{set:ad_share_of_breakeven}', 12),
    CA('verdict', 'Ads check', 'text', 'IF({col:royalty_per_copy}<=0,%s,IF({col:break_even_share}<0.2,%s,%s))' % (v('No room for ads'), v('Thin room for ads'), v('Room for ads')), 14)],
    D.breakeven_d(), 120, [A('verdict', '= ' + v('No room for ads'), 'bad'), A('verdict', '= ' + v('Thin room for ads'), 'warn')]))
# ---------------------------------------------------------------- 10 ledger (before maxbid and rank: they read it)
SP = lambda col, extra='': 'SUMIFS({range:adsdays.%s},{range:adsdays.campaign_id},{col:campaign_id}%s)' % (col, extra)
ledger_cols = [
    REF('campaign_id', 'Campaign ID', 'campaigns.campaign_id', 10, required=True), CA('campaign', 'Campaign', 'text', LKT('campaigns.campaign', 'campaigns.campaign_id', 'campaign_id'), 34),
    CA('title', 'Title', 'text', LKT('campaigns.title', 'campaigns.campaign_id', 'campaign_id'), 28), CA('platform', 'Platform', 'text', LKT('campaigns.platform', 'campaigns.campaign_id', 'campaign_id'), 12),
    CA('status', 'Status', 'text', LKT('campaigns.status', 'campaigns.campaign_id', 'campaign_id'), 10),
    CA('started', 'Started', 'date', LKD('campaigns.start_date', 'campaigns.campaign_id', 'campaign_id'), 11), CA('ended', 'Ended', 'date', LKD('campaigns.end_date', 'campaigns.campaign_id', 'campaign_id'), 11),
    CA('daily_budget', 'Daily budget', 'money', LKN('campaigns.daily_budget', 'campaigns.campaign_id', 'campaign_id'), 10),
    CA('spend', 'Spend', 'money', SP('spend'), 10), CA('clicks', 'Clicks', 'int', SP('clicks'), 9), CA('sales', 'Sales', 'int', SP('sales'), 8), CA('page_reads', 'Page reads', 'int', SP('page_reads'), 10),
    CA('royalties', 'Royalties with page reads', 'money', SP('royalties'), 13),
    CA('conversion', 'Conversion', 'pct', 'IF({col:clicks}=0,0,{col:sales}/{col:clicks})', 10), CA('cost_per_sale', 'Cost per sale', 'money', 'IF({col:sales}=0,0,{col:spend}/{col:sales})', 10),
    CA('profit', 'Profit', 'money', '{col:royalties}-{col:spend}', 10), CA('return', 'Return', 'num', 'IF({col:spend}=0,0,{col:royalties}/{col:spend})', 8),
    CA('spend_60', 'Spend, 60 days', 'money', SP('spend', ',' + W60), 10), CA('royalties_60', 'Royalties, 60 days', 'money', SP('royalties', ',' + W60), 11),
    CA('return_60', 'Return, 60 days', 'num', 'IF({col:spend_60}=0,0,{col:royalties_60}/{col:spend_60})', 10),
    CA('return_30', 'Return, 30 days', 'num', 'IFERROR(%s/%s,0)' % (SP('royalties', ',' + W30), SP('spend', ',' + W30)), 10),
    CA('days_run', 'Days run', 'int', 'IF({col:started}="",0,IF({col:ended}="",{today},{col:ended})-{col:started})', 8),
    CA('verdict', 'Stop, hold or raise', 'text', 'IF({col:status}=%s,IF({col:days_run}<{set:min_ad_days},%s,IF({col:return_60}<{set:ad_return_target},%s,IF(AND({col:return_60}>={set:ad_raise_return},{col:profit}>0),%s,%s))),IF({col:status}=%s,%s,%s))' % (
        RUN, v('Too early'), v('Stop'), v('Raise'), v('Hold'), PAU, v('Paused'), v('Ended')), 14),
    CA('running_return', 'Return of running campaigns', 'num', 'IF({col:status}=%s,{col:return_60},"")' % RUN, 11),
    CA('below', 'Below the target', 'int', 'IF(AND({col:status}=%s,{col:return_60}<{set:ad_return_target}),1,0)' % RUN, 8),
    CA('weight', 'Budget weight', 'num', 'IF({col:status}=%s,IF({col:return_60}<{set:ad_return_target},0,{col:return_60}),0)' % RUN, 9),
    CA('weighted_return', 'Weight times return', 'num', '{col:weight}*{col:return_60}', 9),
    CA('budget_return', 'Daily budget times return', 'num', 'IF({col:status}=%s,{col:daily_budget}*{col:return_60},0)' % RUN, 9),
    CA('sort_score', 'Sort score', 'num', 'ROUND(ROUND(IF({col:status}=%s,{col:return_60},IF({col:status}=%s,100+{col:return},200+{col:return})),4)+VALUE(RIGHT({col:campaign_id},3))/1000000,6)' % (RUN, PAU), 10),
    CA('rank', 'Rank, worst running first', 'int', 'COUNTIFS({range:ledger.sort_score},"<"&{col:sort_score})+1', 9)]
tables.append(T('ledger', 'Campaign Ledger', 'Campaign ledger: spend, royalties and return',
    'One row per campaign: spend, clicks, sales, page reads and royalties over its whole life and over 30 and 60 days, conversion, cost per sale, profit, return and the stop, hold or raise verdict; everything fills in by itself from the Ad Days sheet.',
    ledger_cols, D.ledger_d(), 100, [A('verdict', '= ' + v('Stop'), 'bad'), A('verdict', '= ' + v('Raise'), 'good'), A('profit', '< 0', 'warn')]))
# ---------------------------------------------------------------- 11 maximum bid
LG = lambda col: LKN('ledger.%s' % col, 'ledger.campaign_id', 'campaign_id')
tables.append(T('maxbid', 'Maximum Bid by Campaign', 'Maximum bid per click by campaign',
    'One row per campaign: its own conversion and royalty per sale give the highest bid per click that breaks even and the lower target bid; the current bid is checked against both.', [
    REF('campaign_id', 'Campaign ID', 'campaigns.campaign_id', 10, required=True), CA('campaign', 'Campaign', 'text', LKT('campaigns.campaign', 'campaigns.campaign_id', 'campaign_id'), 34),
    CA('conversion', 'Conversion', 'pct', LG('conversion'), 10),
    CA('royalty_per_sale', 'Royalty per sale', 'money', 'IFERROR(INDEX({range:ledger.royalties},MATCH({col:campaign_id},{range:ledger.campaign_id},0))/INDEX({range:ledger.sales},MATCH({col:campaign_id},{range:ledger.campaign_id},0)),0)', 11),
    CA('break_even_bid', 'Break-even bid per click', 'money', '{col:conversion}*{col:royalty_per_sale}', 12), CA('target_bid', 'Target bid per click', 'money', '{col:break_even_bid}*{set:ad_share_of_breakeven}', 12),
    CA('current_bid', 'Current bid', 'money', LKN('campaigns.bid', 'campaigns.campaign_id', 'campaign_id'), 10),
    CA('actual_cpc', 'Actual cost per click', 'money', 'IFERROR(INDEX({range:ledger.spend},MATCH({col:campaign_id},{range:ledger.campaign_id},0))/INDEX({range:ledger.clicks},MATCH({col:campaign_id},{range:ledger.campaign_id},0)),0)', 11),
    CA('verdict', 'Bid check', 'text', 'IF({col:royalty_per_sale}=0,%s,IF({col:current_bid}>{col:break_even_bid},%s,IF({col:current_bid}>{col:target_bid},%s,%s)))' % (v('No sales yet'), v('Lower the bid'), v('Keep the bid'), v('Room to raise')), 14)],
    D.maxbid_d(), 100, [A('verdict', '= ' + v('Lower the bid'), 'bad'), A('verdict', '= ' + v('Room to raise'), 'good')]))
# ---------------------------------------------------------------- 12 rank
RK = lambda col: LKN('ledger.%s' % col, 'ledger.campaign_id', 'campaign_id')
RT = lambda col: LKT('ledger.%s' % col, 'ledger.campaign_id', 'campaign_id')
tables.append(T('rank', 'Campaign Rank', 'Campaign rank: act on the worst first',
    'Places 1 to 30 list the running campaigns from the lowest return of the last 60 days to the highest, then paused and ended campaigns; the verdict says stop, hold or raise and the budget a stop would free.', [
    C('place', 'Place', 'int', 7, required=True), CA('campaign_id', 'Campaign ID', 'text', 'IFERROR(INDEX({range:ledger.campaign_id},MATCH({col:place},{range:ledger.rank},0))&"","")', 10),
    CA('campaign', 'Campaign', 'text', RT('campaign'), 34), CA('platform', 'Platform', 'text', RT('platform'), 12), CA('status', 'Status', 'text', RT('status'), 10),
    CA('spend_60', 'Spend, 60 days', 'money', RK('spend_60'), 10), CA('royalties_60', 'Royalties, 60 days', 'money', RK('royalties_60'), 11), CA('return_60', 'Return, 60 days', 'num', RK('return_60'), 10),
    CA('profit_60', 'Profit, 60 days', 'money', '{col:royalties_60}-{col:spend_60}', 10), CA('verdict', 'Stop, hold or raise', 'text', RT('verdict'), 14),
    CA('budget_day', 'Daily budget', 'money', RK('daily_budget'), 10), CA('freed', 'Budget freed a day', 'money', 'IF({col:verdict}=%s,{col:budget_day},0)' % v('Stop'), 11)],
    D.rank_d(), 100, [A('verdict', '= ' + v('Stop'), 'bad'), A('verdict', '= ' + v('Raise'), 'good')]))
# ---------------------------------------------------------------- 13 ads by month
AM = lambda col: 'SUMIFS({range:adsdays.%s},{range:adsdays.month},{col:month})' % col
TOTR = 'SUMIFS({range:salesmonth.royalties_home},{range:salesmonth.month},{col:month})+SUMIFS({range:salesmonth.page_income},{range:salesmonth.month},{col:month})'
tables.append(T('adsmonth', 'Ads by Month', 'Ads by month: spend, royalties and return',
    'One row per month: spend, clicks, sales, page reads, royalties, profit, return, cost per click and the share of all royalties that went to ads (when the Sales by Title and Month sheet has the month); everything fills in by itself.', [
    C('month', 'Month', 'date', 11, required=True), CA('spend', 'Spend', 'money', AM('spend'), 10), CA('clicks', 'Clicks', 'int', AM('clicks'), 9), CA('sales', 'Sales', 'int', AM('sales'), 8),
    CA('page_reads', 'Page reads', 'int', AM('page_reads'), 10), CA('royalties', 'Royalties with page reads', 'money', AM('royalties'), 13), CA('profit', 'Profit', 'money', '{col:royalties}-{col:spend}', 10),
    CA('return', 'Return', 'num', 'IF({col:spend}=0,0,{col:royalties}/{col:spend})', 8), CA('cpc', 'Cost per click', 'money', 'IF({col:clicks}=0,0,{col:spend}/{col:clicks})', 10),
    CA('budget', 'Budget', 'money', '{set:ad_budget_month}', 10),
    CA('all_royalties', 'All royalties', 'money', TOTR, 11), CA('share', 'Ad spend share of royalties', 'pct', 'IF({col:all_royalties}=0,"",{col:spend}/{col:all_royalties})', 11),
    CA('share_text', 'Share as text', 'text', 'IF({col:share}="","",ROUND({col:share}*100,1)&"%")', 9),
    CA('spend_year', 'Spend this year so far', 'money', 'SUMIFS({range:adsmonth.spend},{range:adsmonth.month},">="&DATE(YEAR({col:month}),1,1),{range:adsmonth.month},"<="&{col:month})', 12),
    CA('below_count', 'Campaigns below the target', 'int', 'SUM({range:ledger.below})', 9)] +
    PERS('specialist', 'Ad specialist', D.SPEC['name'], D.SPEC['phone']) + PERS('assistant', 'Assistant', D.VA['name'], D.VA['phone']) + PERS('accountant', 'Accountant', D.ACC['name'], D.ACC['phone']) +
    PERS('owner', 'Author', D.OWN['name'], D.OWN['phone']) + [IMPRINT()],
    D.adsmonth_d(), 60, [A('return', '< {set:ad_return_target}', 'warn'), A('spend', '> {set:ad_budget_month}', 'warn')]))
# ---------------------------------------------------------------- 14 ads by platform and month
APM = lambda col: 'SUMIFS({range:adsdays.%s},{range:adsdays.platform},{col:platform},{range:adsdays.month},{col:month})' % col
tables.append(T('adsplat', 'Ads by Platform and Month', 'Ads by platform and month',
    'One row per platform and month: spend, clicks, sales, royalties, return, cost per click and cost per sale; everything fills in by itself from the Ad Days sheet.', [
    C('line_id', 'Line ID', 'text', 9, required=True), LST('platform', 'Platform', 'platform', 12), C('month', 'Month', 'date', 11), CA('spend', 'Spend', 'money', APM('spend'), 10), CA('clicks', 'Clicks', 'int', APM('clicks'), 9),
    CA('sales', 'Sales', 'int', APM('sales'), 8), CA('royalties', 'Royalties with page reads', 'money', APM('royalties'), 13), CA('return', 'Return', 'num', 'IF({col:spend}=0,0,{col:royalties}/{col:spend})', 8),
    CA('cpc', 'Cost per click', 'money', 'IF({col:clicks}=0,0,{col:spend}/{col:clicks})', 10), CA('cps', 'Cost per sale', 'money', 'IF({col:sales}=0,0,{col:spend}/{col:sales})', 10)] +
    PERS('specialist', 'Ad specialist', D.SPEC['name'], D.SPEC['phone']) + [IMPRINT()],
    D.adsplat_d(), 120, [A('return', '< {set:ad_return_target}', 'warn')]))
# ---------------------------------------------------------------- 15 ads by title
AT = lambda col: 'SUMIFS({range:adsdays.%s},{range:adsdays.title_id},{col:title_id})' % col
tables.append(T('adstitle', 'Ads by Title', 'Ads by title: spend, royalties and return',
    'One row per title: spend, copies sold, royalties, profit and return from all its ad days, with its share of all ad spend; everything fills in by itself.', [
    REF('title_id', 'Title ID', 'titles.title_id', 9, required=True), CA('title', 'Title', 'text', LKT('titles.title', 'titles.title_id', 'title_id'), 28), LST('pen_name', 'Pen name', 'penname', 16), LST('series', 'Series', 'series', 20),
    CA('spend', 'Spend', 'money', AT('spend'), 10), CA('sales', 'Sales', 'int', AT('sales'), 8), CA('royalties', 'Royalties with page reads', 'money', AT('royalties'), 13),
    CA('profit', 'Profit', 'money', '{col:royalties}-{col:spend}', 10), CA('return', 'Return', 'num', 'IF({col:spend}=0,0,{col:royalties}/{col:spend})', 8),
    CA('spend_share', 'Share of all ad spend', 'pct', 'IFERROR({col:spend}/SUM({range:adstitle.spend}),0)', 10)],
    D.adstitle_d(), 100, [A('return', '< {set:ad_return_target}', 'warn')]))
# ---------------------------------------------------------------- 16 ad compare with own history
def CMP(col, crit): return 'SUMIFS({range:adsdays.%s},{range:adsdays.title_id},{col:title_id},{range:adsdays.month},%s)' % (col, crit)
M3 = '">="&EDATE(%s,-3),{range:adsdays.month},"<"&%s' % (MS, MS)
tables.append(T('adscompare', 'Ad Compare with Own History', 'Ad compare: this month, 3-month average, last year',
    'One row per title: the return of this month against the average of the 3 months before and the same month last year, the change and a flag when the change goes beyond your limit; everything fills in by itself.', [
    REF('title_id', 'Title ID', 'titles.title_id', 9, required=True), CA('title', 'Title', 'text', LKT('titles.title', 'titles.title_id', 'title_id'), 28),
    CA('spend_month', 'Spend this month', 'money', CMP('spend', MS), 10),
    CA('ret_month', 'Return this month', 'num', 'IFERROR(%s/%s,"")' % (CMP('royalties', MS), CMP('spend', MS)), 10),
    CA('ret_3m', 'Return, 3-month average', 'num', 'IFERROR(%s/%s,"")' % (CMP('royalties', M3), CMP('spend', M3)), 11),
    CA('ret_year', 'Return, same month last year', 'num', 'IFERROR(%s/%s,"")' % (CMP('royalties', 'EDATE(%s,-12)' % MS), CMP('spend', 'EDATE(%s,-12)' % MS)), 12),
    CA('change_3m', 'Change against 3 months', 'pct', 'IF(OR({col:ret_month}="",{col:ret_3m}=""),"",{col:ret_month}/{col:ret_3m}-1)', 11),
    CA('change_year', 'Change against last year', 'pct', 'IF(OR({col:ret_month}="",{col:ret_year}=""),"",{col:ret_month}/{col:ret_year}-1)', 11),
    CA('flag_3m', 'Flag, 3 months', 'text', 'IF({col:ret_month}="",%s,IF({col:ret_3m}="",%s,IF({col:change_3m}<=-{set:ad_deterioration_pct},%s,IF({col:change_3m}>={set:ad_deterioration_pct},%s,%s))))' % (
        v('No ads this month'), v('New this month'), v('Worse beyond the limit'), v('Better'), v('Flat')), 16),
    CA('flag_year', 'Flag, last year', 'text', 'IF({col:ret_month}="",%s,IF({col:ret_year}="",%s,IF({col:change_year}<=-{set:ad_deterioration_pct},%s,IF({col:change_year}>={set:ad_deterioration_pct},%s,%s))))' % (
        v('No ads this month'), v('No ads then'), v('Worse beyond the limit'), v('Better'), v('Flat')), 16)],
    D.adscompare_d(), 100, [A('flag_3m', '= ' + v('Worse beyond the limit'), 'bad'), A('flag_3m', '= ' + v('Better'), 'good'), A('flag_year', '= ' + v('Worse beyond the limit'), 'bad'), A('flag_year', '= ' + v('Better'), 'good')]))
# ---------------------------------------------------------------- 17 conversion by title
CV = lambda col: 'SUMIFS({range:adsdays.%s},{range:adsdays.title_id},{col:title_id})' % col
tables.append(T('conv', 'Conversion by Title', 'Conversion by title against your floor',
    'One row per title: clicks and sales from all its ad days, the conversion, whether it is below your floor, the sales you would add at the floor and the verdict; everything fills in by itself.', [
    REF('title_id', 'Title ID', 'titles.title_id', 9, required=True), CA('title', 'Title', 'text', LKT('titles.title', 'titles.title_id', 'title_id'), 28), LST('series', 'Series', 'series', 20),
    CA('clicks', 'Clicks', 'int', CV('clicks'), 9), CA('sales', 'Sales', 'int', CV('sales'), 8), CA('conversion', 'Conversion', 'pct', 'IF({col:clicks}=0,0,{col:sales}/{col:clicks})', 10),
    CA('conversion_text', 'Conversion as text', 'text', 'ROUND({col:conversion}*100,1)&"%"', 10),
    CA('below_floor', 'Below the floor', 'text', 'IF(AND({col:clicks}>0,{col:conversion}<{set:conversion_floor}),%s,%s)' % (yes(), no()), 9),
    CA('sales_at_floor', 'Sales to add at the floor', 'int', 'IF(AND({col:clicks}>0,{col:conversion}<{set:conversion_floor}),ROUND({col:clicks}*{set:conversion_floor}-{col:sales},0),0)', 11),
    CA('verdict', 'Verdict', 'text', 'IF({col:clicks}=0,%s,IF({col:conversion}<{set:conversion_floor},%s,%s))' % (v('No ads yet'), v('Fix the product page'), v('Conversion is fine')), 18)] +
    PERS('specialist', 'Ad specialist', D.SPEC['name'], D.SPEC['phone']) + PERS('owner', 'Author', D.OWN['name'], D.OWN['phone']) + [IMPRINT()],
    D.conv_d(), 100, [A('verdict', '= ' + v('Fix the product page'), 'bad'), A('verdict', '= ' + v('Conversion is fine'), 'good')]))
# ---------------------------------------------------------------- 18 promotion results
def PL(col): return LKN('promos.%s' % col, 'promos.promo_id', 'promo_id')
SHN = 'SUMIFS({range:editions.royalty_share},{range:editions.title},{col:title},{range:editions.format},%s)' % EBK
UCN = 'SUMIFS({range:editions.unit_cost},{range:editions.title},{col:title},{range:editions.format},%s)' % EBK
tables.append(T('promoresults', 'Promotion Results', 'Promotion results: extra copies, extra royalties, payback',
    'One row per promotion: copies before, during and after, the extra copies, the extra royalties at the lower price, the page reads moved, the lasting lift, the net gain after cost, the payback days and a verdict to repeat, change or skip.', [
    REF('promo_id', 'Promotion ID', 'promos.promo_id', 10, required=True), CA('title', 'Title', 'text', LKT('promos.title', 'promos.promo_id', 'promo_id'), 28), LST('kind', 'Kind', 'pkind', 13),
    CA('status', 'Status', 'text', LKT('promos.status', 'promos.promo_id', 'promo_id'), 9), CA('start_date', 'Start date', 'date', LKD('promos.start_date', 'promos.promo_id', 'promo_id'), 11),
    CA('days', 'Days', 'int', PL('days'), 6), CA('units_before', 'Copies before', 'int', PL('units_before'), 9), CA('units_during', 'Copies during', 'int', PL('units_during'), 9), CA('units_after', 'Copies after', 'int', PL('units_after'), 9),
    CA('royalty_normal', 'Royalty per copy, normal price', 'money', ROYN(PL('normal_price'), SHN, UCN), 12),
    CA('royalty_promo', 'Royalty per copy, promo price', 'money', ROYN(PL('promo_price'), SHARE_AT(PL('promo_price'), SHN), UCN), 12),
    CA('extra_copies', 'Extra copies', 'int', '{col:units_during}-{col:units_before}', 9),
    CA('extra_royalties', 'Extra royalties from copies', 'money', '{col:units_during}*{col:royalty_promo}-{col:units_before}*{col:royalty_normal}', 12),
    CA('page_extra', 'Page-read income moved', 'money', '(%s-%s)*{set:page_read_rate}' % (PL('pages_during'), PL('pages_before')), 11),
    CA('extra_total', 'Extra royalties in total', 'money', '{col:extra_royalties}+{col:page_extra}', 11),
    CA('after_effect', 'Lasting lift after', 'money', '({col:units_after}-{col:units_before})*{col:royalty_normal}', 10),
    CA('cost', 'Cost', 'money', PL('cost'), 9), CA('net_gain', 'Net gain after cost', 'money', '{col:extra_total}+{col:after_effect}-{col:cost}', 11),
    CA('payback_days', 'Payback days', 'num', 'IF({col:extra_total}<=0,"",ROUND({col:cost}/({col:extra_total}/MAX(1,{col:days})),1))', 9),
    CA('verdict', 'Repeat, change or skip', 'text', 'IF({col:status}=%s,%s,IF(AND({col:net_gain}>0,{col:extra_total}>0),%s,IF(AND({col:net_gain}<=0,{col:extra_total}<=0),%s,%s)))' % (PLN, v('Not run yet'), v('Repeat'), v('Skip'), v('Change')), 14)] +
    PERS('owner', 'Author', D.OWN['name'], D.OWN['phone']) + [IMPRINT()],
    D.promoresults_d(), 100, [A('verdict', '= ' + v('Repeat'), 'good'), A('verdict', '= ' + v('Skip'), 'bad'), A('verdict', '= ' + v('Change'), 'warn')]))
# ---------------------------------------------------------------- 19 price test comparison
def PT(col): return LKN('pricetests.%s' % col, 'pricetests.test_id', 'test_id')
tables.append(T('pricecmp', 'Price Test Comparison', 'Price test comparison: royalty a day and unit lift needed',
    'One row per price test: the royalty a day at price A and at price B, the change, the copy lift price B needs to match A, the lift seen and a verdict to keep A, keep B or test longer.', [
    REF('test_id', 'Test ID', 'pricetests.test_id', 9, required=True), CA('title', 'Title', 'text', LKT('pricetests.title', 'pricetests.test_id', 'test_id'), 28),
    CA('royalty_day_a', 'Royalty a day at A', 'money', 'IFERROR(%s/%s,0)' % (PT('total_royalty_a'), PT('days_a')), 11), CA('royalty_day_b', 'Royalty a day at B', 'money', 'IFERROR(%s/%s,0)' % (PT('total_royalty_b'), PT('days_b')), 11),
    CA('change', 'Royalty change, B against A', 'pct', 'IF({col:royalty_day_a}=0,0,{col:royalty_day_b}/{col:royalty_day_a}-1)', 11),
    CA('lift_needed', 'Copy lift B needs to match A', 'pct', 'IF(%s=0,0,%s/%s-1)' % (PT('royalty_b'), PT('royalty_a'), PT('royalty_b')), 12),
    CA('lift_seen', 'Copy lift seen at B', 'pct', 'IF(%s=0,0,%s/%s-1)' % (PT('units_day_a'), PT('units_day_b'), PT('units_day_a')), 11),
    CA('min_units', 'Fewest copies in a period', 'int', 'MIN(%s,%s)' % (PT('units_a'), PT('units_b')), 10),
    CA('verdict', 'Keep A, keep B or test longer', 'text', 'IF(OR({col:min_units}<{set:test_min_units},ABS({col:change})<{set:price_test_margin}),%s,IF({col:change}>0,%s,%s))' % (v('Test longer'), v('Keep B'), v('Keep A')), 16)] +
    PERS('owner', 'Author', D.OWN['name'], D.OWN['phone']) + [IMPRINT()],
    D.pricecmp_d(), 60, [A('verdict', '= ' + v('Keep B'), 'good'), A('verdict', '= ' + v('Keep A'), 'good'), A('verdict', '= ' + v('Test longer'), 'warn')]))
# ---------------------------------------------------------------- 20 sales by title and month
tables.append(T('salesmonth', 'Sales by Title and Month', 'Sales by title and month in home currency',
    'One row per title and month: copies, royalties in your home currency and page-read income; the ad share of royalties reads these totals (estimates until the payments arrive).', [
    C('line_id', 'Line ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), REF('title', 'Title', 'titles.title', 28), C('units', 'Copies', 'int', 8), C('royalties_home', 'Royalties', 'money', 11),
    C('page_income', 'Page-read income', 'num', 11)],
    D.salesmonth_d(), 400, []))
assert len(tables) == 20
