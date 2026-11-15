"""Author and Self-Publisher suite part 4: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au4_lists import *
import au4_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": vv} for l, vv in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
RUN = tok('adstatus', 'Running'); DONE = tok('pstatus', 'Done'); EBK = tok('format', 'Ebook'); ALLP = tok('platfilter', 'All platforms')
def ROYN(price, share, cost): return 'MAX(0,(%s)*(%s)-(%s))' % (price, share, cost)
def SHARE_AT(price, share): return 'IF((%s)<{set:low_price_limit},{set:low_price_share},%s)' % (price, share)
def N(x, d=2): return 'ROUND(%s,%d)' % (x, d)
tools = []

# 1 ------------------------------------------------------------ break-even ad cost finder
PRICE = 'SUMIFS({range:editions.list_price},{range:editions.title},{in:title},{range:editions.format},{in:format})'
UCOST = 'SUMIFS({range:editions.unit_cost},{range:editions.title},{in:title},{range:editions.format},{in:format})'
SHR = 'IF(AND({in:format}=%s,%s<{set:low_price_limit}),{set:low_price_share},SUMIFS({range:stores.royalty_share},{range:stores.store},{in:store}))' % (EBK, PRICE)
ROY1 = ROYN(PRICE, SHR, UCOST)
tools.append(TOOL('be_finder', 'Break-Even Ad Cost Finder', 'How much can one sale cost in ads before you lose money',
    'Pick a title, format and store: the royalty after cost, the share of the price you can spend on ads, the highest cost per sale and per click at your conversion, and what to bid.', [
    IL('title', 'Title', 'title', 'The Drowned Ledger'), IL('format', 'Format', 'format', 'Ebook'), IL('store', 'Store', 'store', 'Ebook store'),
    I('conv', 'Click-to-sale conversion (your own history)', 0.05, 'pct'), I('share', 'Target share of break-even cost (typical 30-40%)', 0.35, 'pct')], [
    O('List price', 'money', PRICE), O('Royalty share used', 'pct', SHR), O('Unit cost', 'money', UCOST), O('Royalty per copy after cost', 'money', ROY1),
    O('Break-even ad share of the price', 'pct', 'IF(%s=0,0,(%s)/%s)' % (PRICE, ROY1, PRICE)), O('Target ad share of the price', 'pct', 'IF(%s=0,0,(%s)/%s)*{in:share}' % (PRICE, ROY1, PRICE)),
    O('Highest cost per sale, break-even', 'money', ROY1), O('Highest cost per sale, at your target', 'money', '(%s)*{in:share}' % ROY1),
    O('Highest cost per click, break-even', 'money', '{in:conv}*(%s)' % ROY1), O('Highest cost per click, at your target', 'money', '{in:conv}*(%s)*{in:share}' % ROY1),
    O('Verdict', 'text', 'IF(%s=0,%s,IF((%s)<=0,%s,%s&" "&ROUND({in:conv}*(%s)*{in:share},2)))' % (PRICE, v('No such edition'), ROY1, v('No room for ads'), v('Bid up to'), ROY1))],
    GR('What if', ('Conversion 2%', {'conv': 0.02}), ('Conversion 3%', {'conv': 0.03}), ('Conversion 8%', {'conv': 0.08}), ('Target share 25%', {'share': 0.25}), ('Target share 50%', {'share': 0.5}),
       ('Paperback, print-on-demand', {'format': '=' + tok('format', 'Paperback'), 'store': '=' + tok('store', 'Print-on-demand')}),
       ('Audiobook, audiobook store', {'format': '=' + tok('format', 'Audiobook'), 'store': '=' + tok('store', 'Audiobook store')}))))

# 2 ------------------------------------------------------------ stop, hold or raise ranker
L_ = lambda c: '{range:ledger.%s}' % c
RUNSTAT = '%s,%s' % (L_('status'), RUN)
STOP60 = 'COUNTIFS(%s,%s,"<"&{in:stop_below})' % (RUNSTAT, L_('return_60'))
RAISE60 = 'COUNTIFS(%s,%s,">="&{in:raise_at})' % (RUNSTAT, L_('return_60'))
NRUN = 'COUNTIFS(%s)' % RUNSTAT
WORST = 'INDEX(%s,MATCH(MIN(%s),%s,0))' % (L_('campaign'), L_('running_return'), L_('running_return'))
BEST = 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (L_('campaign'), L_('running_return'), L_('running_return'))
tools.append(TOOL('ranker', 'Stop Hold Raise Ranker', 'Which running campaigns to stop, hold or raise',
    'All running campaigns by their return over 30 and 60 days: how many to stop, hold or raise, the budget a stop frees, the worst and the best campaign; change the limits to see the effect.', [
    I('stop_below', 'Stop below this return (your own number)', 1.0, 'num'), I('raise_at', 'Raise at this return or higher (your own number)', 1.5, 'num')], [
    O('Running campaigns', 'int', NRUN), O('Campaigns to stop, 60 days', 'int', STOP60),
    O('Campaigns to stop, 30 days', 'int', 'COUNTIFS(%s,%s,"<"&{in:stop_below})' % (RUNSTAT, L_('return_30'))), O('Campaigns to raise, 60 days', 'int', RAISE60), O('Campaigns to hold', 'int', '%s-%s-%s' % (NRUN, STOP60, RAISE60)),
    O('Daily budget freed by the stops', 'money', 'SUMIFS(%s,%s,%s,"<"&{in:stop_below})' % (L_('daily_budget'), RUNSTAT, L_('return_60'))),
    O('Budget freed in 30 days', 'money', '30*SUMIFS(%s,%s,%s,"<"&{in:stop_below})' % (L_('daily_budget'), RUNSTAT, L_('return_60'))),
    O('Spend of the stops, 60 days', 'money', 'SUMIFS(%s,%s,%s,"<"&{in:stop_below})' % (L_('spend_60'), RUNSTAT, L_('return_60'))),
    O('Royalties of the stops, 60 days', 'money', 'SUMIFS(%s,%s,%s,"<"&{in:stop_below})' % (L_('royalties_60'), RUNSTAT, L_('return_60'))),
    O('Extra daily budget if you raise by one step', 'money', '{set:raise_step_pct}*SUMIFS(%s,%s,%s,">="&{in:raise_at})' % (L_('daily_budget'), RUNSTAT, L_('return_60'))),
    O('Worst running campaign', 'text', WORST), O('Its return', 'num', 'MIN(%s)' % L_('running_return')), O('Best running campaign', 'text', BEST), O('Its return', 'num', 'MAX(%s)' % L_('running_return')),
    O('Verdict', 'text', 'IF(%s>0,%s&": "&%s,IF(%s>0,%s&": "&%s,%s))' % (STOP60, v('Stop campaigns'), STOP60, RAISE60, v('Raise campaigns'), RAISE60, v('Hold all')))],
    GR('What if', ('Stop below 0.70', {'stop_below': 0.7}), ('Stop below 1.20', {'stop_below': 1.2}), ('Stop below 1.50', {'stop_below': 1.5}), ('Raise at 1.20', {'raise_at': 1.2}), ('Raise at 2.00', {'raise_at': 2.0}))))

# 3 ------------------------------------------------------------ campaign profit and loss
CID = 'INDEX({range:campaigns.campaign_id},MATCH({in:campaign},{range:campaigns.campaign},0))'
def CP(col): return 'SUMIFS({range:adsdays.%s},{range:adsdays.campaign_id},%s,{range:adsdays.date},">="&({today}-{in:window}))' % (col, CID)
tools.append(TOOL('campaign_pl', 'Campaign Profit and Loss', 'Is this campaign profitable over the last weeks',
    'Pick a campaign and a window of 30, 60 or 90 days: spend, clicks, sales, page reads, royalties, profit, return against your target, cost per sale and a profitable, break-even or losing verdict.', [
    IL('campaign', 'Campaign', 'campaign', 'Tidebound 1 - similar authors'), I('window', 'Days to look back (30, 60 or 90)', 60, 'int'), I('target', 'Return target (1.00 is break-even)', 1.0, 'num')], [
    O('Spend', 'money', CP('spend')), O('Clicks', 'int', CP('clicks')), O('Sales', 'int', CP('sales')), O('Page reads', 'int', CP('page_reads')), O('Royalties with page reads', 'money', CP('royalties')),
    O('Profit', 'money', '%s-%s' % (CP('royalties'), CP('spend'))), O('Return', 'num', 'IFERROR(%s/%s,0)' % (CP('royalties'), CP('spend'))), O('Cost per sale', 'money', 'IFERROR(%s/%s,0)' % (CP('spend'), CP('sales'))),
    O('Cost per click', 'money', 'IFERROR(%s/%s,0)' % (CP('spend'), CP('clicks'))), O('Conversion', 'pct', 'IFERROR(%s/%s,0)' % (CP('sales'), CP('clicks'))), O('Average spend a day', 'money', '%s/{in:window}' % CP('spend')),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s/%s>={in:target}*1.1,%s,IF(%s/%s>={in:target}*0.9,%s,%s)))' % (CP('spend'), v('No spend'), CP('royalties'), CP('spend'), v('Profitable'), CP('royalties'), CP('spend'), v('Break-even'), v('Losing')))],
    GR('What if', ('Last 30 days', {'window': 30}), ('Last 90 days', {'window': 90}), ('Target 1.50', {'target': 1.5}), ('A strong campaign', {'campaign': '=' + tok('campaign', 'Lantern Bay 1 - cosy series starters')}),
       ('A middle campaign', {'campaign': '=' + tok('campaign', 'Quiet Hollow 1 - similar authors')}))))

# 4 ------------------------------------------------------------ ad compare with own history
TID = 'INDEX({range:titles.title_id},MATCH({in:title},{range:titles.title},0))'
PC = 'IF({in:platform}=%s,"*",{in:platform})' % ALLP
def AC(col, crit): return 'SUMIFS({range:adsdays.%s},{range:adsdays.title_id},%s,{range:adsdays.platform},%s,{range:adsdays.month},%s)' % (col, TID, PC, crit)
M3_ = '">="&EDATE(%s,-3),{range:adsdays.month},"<"&%s' % (MS, MS)
RM_ = 'IFERROR(%s/%s,0)' % (AC('royalties', MS), AC('spend', MS))
R3_ = 'IFERROR(%s/%s,0)' % (AC('royalties', M3_), AC('spend', M3_))
RY_ = 'IFERROR(%s/%s,0)' % (AC('royalties', 'EDATE(%s,-12)' % MS), AC('spend', 'EDATE(%s,-12)' % MS))
tools.append(TOOL('ad_compare', 'Ad Compare Checker', 'Are this month\'s ads better or worse than your own history',
    'Pick a title and a platform: the return of this month against the average of the 3 months before and the same month last year, the change in percent and a verdict against your limit.', [
    IL('title', 'Title', 'title', 'The Orchard Key'), IL('platform', 'Platform', 'platfilter', 'All platforms'), I('limit', 'Flag a change beyond this share (your own number)', 0.20, 'pct')], [
    O('Spend this month', 'money', AC('spend', MS)), O('Royalties this month', 'money', AC('royalties', MS)), O('Return this month', 'num', RM_), O('Return, 3-month average', 'num', R3_),
    O('Return, same month last year', 'num', RY_), O('Change against 3 months', 'pct', 'IF(%s=0,0,%s/%s-1)' % (R3_, RM_, R3_)), O('Change against last year', 'pct', 'IF(%s=0,0,%s/%s-1)' % (RY_, RM_, RY_)),
    O('Spend, 3 months before', 'money', AC('spend', M3_)),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s=0,%s,IF(%s/%s-1<=-{in:limit},%s,IF(%s/%s-1>={in:limit},%s,%s))))' % (AC('spend', MS), v('No ads this month'), R3_, v('New this month'), RM_, R3_, v('Worse beyond the limit'), RM_, R3_, v('Better'), v('Flat')))],
    GR('What if', ('Limit 10%', {'limit': 0.10}), ('Limit 35%', {'limit': 0.35}), ('Store ads only', {'platform': '=' + tok('platfilter', 'Store ads')}), ('Search ads only', {'platform': '=' + tok('platfilter', 'Search ads')}),
       ('Another title', {'title': '=' + tok('title', 'Shard of the Ember Crown')}))))

# 5 ------------------------------------------------------------ conversion check
EBROY = ROYN('SUMIFS({range:editions.list_price},{range:editions.title},{in:title},{range:editions.format},%s)' % EBK,
             SHARE_AT('SUMIFS({range:editions.list_price},{range:editions.title},{in:title},{range:editions.format},%s)' % EBK, 'SUMIFS({range:stores.royalty_share},{range:stores.store},%s)' % tok('store', 'Ebook store')),
             'SUMIFS({range:editions.unit_cost},{range:editions.title},{in:title},{range:editions.format},%s)' % EBK)
tools.append(TOOL('conv_check', 'Conversion Check', 'Is the ad weak or is the product page weak',
    'Type the clicks and sales of a title: your conversion against your floor, the sales you would add at the floor, their royalty value and a verdict that says fix the product page or carry on.', [
    IL('title', 'Title', 'title', 'Crown of Last Embers'), I('clicks', 'Clicks', 3200, 'int'), I('sales', 'Sales', 52, 'int'), I('floor', 'Conversion floor (your own number)', 0.02, 'pct')], [
    O('Conversion', 'pct', 'IF({in:clicks}=0,0,{in:sales}/{in:clicks})'), O('Your floor', 'pct', '{in:floor}'), O('Points above or below the floor', 'num', '(IF({in:clicks}=0,0,{in:sales}/{in:clicks})-{in:floor})*100'),
    O('Own history of this title', 'pct', 'IFERROR(INDEX({range:conv.conversion},MATCH({in:title},{range:conv.title},0)),0)'), O('Sales at the floor', 'int', 'ROUND({in:clicks}*{in:floor},0)'),
    O('Sales you would add at the floor', 'int', 'MAX(0,ROUND({in:clicks}*{in:floor}-{in:sales},0))'), O('Royalty value of those sales', 'money', 'MAX(0,ROUND({in:clicks}*{in:floor}-{in:sales},0))*(%s)' % EBROY),
    O('Clicks for one sale at the floor', 'int', 'IF({in:floor}=0,0,ROUND(1/{in:floor},0))'),
    O('Verdict', 'text', 'IF({in:clicks}=0,%s,IF({in:sales}/{in:clicks}<{in:floor},%s,%s))' % (v('No ads yet'), v('Fix the product page'), v('Conversion is fine')))],
    GR('What if', ('52 sales become 90', {'sales': 90}), ('Floor 3%', {'floor': 0.03}), ('Floor 1%', {'floor': 0.01}), ('A title with a good page', {'title': '=' + tok('title', 'The Salt Pier Letter'), 'clicks': 3000, 'sales': 213}))))

# 6 ------------------------------------------------------------ daily budget solver
ALLOW = '{in:limit}*SUMIFS({range:salesmonth.royalties_home},{range:salesmonth.month},">="&EDATE(%s,-11),{range:salesmonth.month},"<"&%s)/11+{in:limit}*SUMIFS({range:salesmonth.page_income},{range:salesmonth.month},">="&EDATE(%s,-11),{range:salesmonth.month},"<"&%s)/11' % (MS, MS, MS, MS)
tools.append(TOOL('budget_solver', 'Daily Budget Solver', 'What daily budget buys the sales you want',
    'Type the sales a day you want, your conversion, cost per click and royalty per sale: the clicks and the daily and monthly budget needed, the return it implies and whether it fits your ad share of royalties.', [
    I('sales_day', 'Sales a day you want', 8, 'num'), I('conv', 'Click-to-sale conversion', 0.06, 'pct'), I('cpc', 'Cost per click', 0.12, 'money'), I('royalty', 'Royalty per sale with page reads', 3.2, 'money'),
    I('limit', 'Highest ad spend as a share of royalties', 0.15, 'pct')], [
    O('Clicks needed a day', 'int', 'IF({in:conv}=0,0,ROUND({in:sales_day}/{in:conv},0))'), O('Daily budget needed', 'money', 'IF({in:conv}=0,0,{in:sales_day}/{in:conv}*{in:cpc})'),
    O('Monthly budget needed, 30 days', 'money', 'IF({in:conv}=0,0,30*{in:sales_day}/{in:conv}*{in:cpc})'), O('Cost per sale', 'money', 'IF({in:conv}=0,0,{in:cpc}/{in:conv})'),
    O('Return it implies', 'num', 'IF({in:cpc}=0,0,{in:conv}*{in:royalty}/{in:cpc})'), O('Profit a day', 'money', '{in:sales_day}*{in:royalty}-IF({in:conv}=0,0,{in:sales_day}/{in:conv}*{in:cpc})'),
    O('Monthly budget you set', 'money', '{set:ad_budget_month}'), O('Most you can spend a month at your ad share', 'money', ALLOW),
    O('Return check', 'text', 'IF({in:cpc}=0,%s,IF({in:conv}*{in:royalty}/{in:cpc}>={set:ad_return_target},%s,%s))' % (v('Return is below the target'), v('Return meets the target'), v('Return is below the target'))),
    O('Verdict', 'text', 'IF(IF({in:conv}=0,0,30*{in:sales_day}/{in:conv}*{in:cpc})>%s,%s,%s)' % (ALLOW, v('Over your ad share'), v('Affordable')))],
    GR('What if', ('15 sales a day', {'sales_day': 15}), ('30 sales a day', {'sales_day': 30}), ('Conversion 3%', {'conv': 0.03}), ('Cost per click 0.25', {'cpc': 0.25}), ('Royalty per sale 1.50', {'royalty': 1.5}))))

# 7 ------------------------------------------------------------ cost per click ceiling
tools.append(TOOL('cpc_ceiling', 'Cost per Click Ceiling', 'What cost per click still meets your return',
    'Type your conversion, royalty per sale and return target: the highest cost per click that still meets it, the room against your current cost per click and a verdict to lower the bid or keep it.', [
    I('conv', 'Click-to-sale conversion', 0.05, 'pct'), I('royalty', 'Royalty per sale with page reads', 3.2, 'money'), I('target', 'Return target (1.00 is break-even)', 1.0, 'num'), I('cpc', 'Your cost per click now', 0.14, 'money')], [
    O('Highest cost per click for your target', 'money', 'IF({in:target}=0,0,{in:conv}*{in:royalty}/{in:target})'), O('Highest cost per click at break-even', 'money', '{in:conv}*{in:royalty}'),
    O('Highest cost per click at your share of break-even', 'money', '{in:conv}*{in:royalty}*{set:ad_share_of_breakeven}'),
    O('Room against your cost per click', 'money', 'IF({in:target}=0,0,{in:conv}*{in:royalty}/{in:target})-{in:cpc}'), O('Your cost per sale', 'money', 'IF({in:conv}=0,0,{in:cpc}/{in:conv})'),
    O('Your return now', 'num', 'IF({in:cpc}=0,0,{in:conv}*{in:royalty}/{in:cpc})'), O('Cost per sale at the ceiling', 'money', 'IF({in:conv}=0,0,IF({in:target}=0,0,{in:conv}*{in:royalty}/{in:target})/{in:conv})'),
    O('Verdict', 'text', 'IF({in:cpc}>IF({in:target}=0,0,{in:conv}*{in:royalty}/{in:target}),%s,%s)' % (v('Lower the bid'), v('Bid is fine')))],
    GR('Conversion up and down', ('Conversion 2%', {'conv': 0.02}), ('Conversion 3%', {'conv': 0.03}), ('Conversion 4%', {'conv': 0.04}), ('Conversion 6%', {'conv': 0.06}), ('Conversion 8%', {'conv': 0.08}),
       ('Target return 1.50', {'target': 1.5}))))

# 8 ------------------------------------------------------------ promotion result tool
RN8 = ROYN('{in:normal}', '{in:share}', '{in:unit_cost}'); RP8 = ROYN('{in:promo}', SHARE_AT('{in:promo}', '{in:share}'), '{in:unit_cost}')
XC8 = '{in:during}*(%s)-{in:before}*(%s)' % (RP8, RN8); PG8 = '({in:pages_during}-{in:pages_before})*{set:page_read_rate}'
AF8 = '({in:after}-{in:before})*(%s)' % RN8
tools.append(TOOL('promo_result', 'Promotion Result Tool', 'Did the price promotion pay for itself',
    'Type the copies before, during and after (equal periods), both prices and the cost: the extra copies, the extra royalties at the lower price, the page reads moved, the lasting lift, payback days and a repeat, change or skip verdict.', [
    I('before', 'Copies before', 58, 'int'), I('during', 'Copies during', 161, 'int'), I('after', 'Copies after', 72, 'int'), I('pages_before', 'Pages read before', 9048, 'int'), I('pages_during', 'Pages read during', 11296, 'int'),
    I('normal', 'Normal price', 2.99, 'money'), I('promo', 'Promotion price', 1.5, 'money'), I('cost', 'Promotion cost', 25, 'money'), I('days', 'Days of the promotion', 6, 'int'),
    I('share', 'Royalty share at the normal price (check terms)', 0.70, 'pct'), I('unit_cost', 'Unit cost per copy', 0.12, 'money')], [
    O('Royalty per copy, normal price', 'money', RN8), O('Royalty per copy, promotion price', 'money', RP8), O('Extra copies', 'int', '{in:during}-{in:before}'),
    O('Extra royalties from copies', 'money', XC8), O('Page-read income moved', 'money', PG8), O('Extra royalties in total', 'money', '%s+%s' % (XC8, PG8)),
    O('Lasting lift after the promotion', 'money', AF8), O('Net gain after cost', 'money', '%s+%s+%s-{in:cost}' % (XC8, PG8, AF8)),
    O('Payback days', 'num', 'IF(%s+%s<=0,0,ROUND({in:cost}/((%s+%s)/MAX(1,{in:days})),1))' % (XC8, PG8, XC8, PG8)),
    O('Verdict', 'text', 'IF(AND((%s+%s)+%s-{in:cost}>0,%s+%s>0),%s,IF(AND((%s+%s)+%s-{in:cost}<=0,%s+%s<=0),%s,%s))' % (XC8, PG8, AF8, XC8, PG8, v('Repeat'), XC8, PG8, AF8, XC8, PG8, v('Skip'), v('Change')))],
    GR('What if', ('Promotion price 0.99', {'promo': 0.99}), ('Cost 120', {'cost': 120}), ('Copies during 100', {'during': 100}), ('Copies during 300', {'during': 300}), ('No lasting lift', {'after': 58}), ('No page reads moved', {'pages_during': 9048}), ('Promotion price 2.49', {'promo': 2.49}))))

# 9 ------------------------------------------------------------ promotion fit check
PT9 = '{range:promos.title},{in:title},{range:promos.status},%s' % DONE
BEFT = 'SUMIFS({range:promos.units_before},%s)' % PT9; DURT = 'SUMIFS({range:promos.units_during},%s)' % PT9; AFTT = 'SUMIFS({range:promos.units_after},%s)' % PT9
BEFA = 'SUMIFS({range:promos.units_before},{range:promos.status},%s)' % DONE; DURA = 'SUMIFS({range:promos.units_during},{range:promos.status},%s)' % DONE; AFTA = 'SUMIFS({range:promos.units_after},{range:promos.status},%s)' % DONE
N9 = 'COUNTIFS(%s)' % PT9
LIFT9 = 'IF(%s>0,%s/%s-1,%s/%s-1)' % (N9, DURT, BEFT, DURA, BEFA)
HALO9 = 'IF(%s>0,%s/%s-1,%s/%s-1)' % (N9, AFTT, BEFT, AFTA, BEFA)
EP9 = 'SUMIFS({range:editions.list_price},{range:editions.title},{in:title},{range:editions.format},%s)' % EBK
UC9 = 'SUMIFS({range:editions.unit_cost},{range:editions.title},{in:title},{range:editions.format},%s)' % EBK
SH9 = 'SUMIFS({range:editions.royalty_share},{range:editions.title},{in:title},{range:editions.format},%s)' % EBK
RN9 = ROYN(EP9, SH9, UC9); RP9 = ROYN('{in:price}', SHARE_AT('{in:price}', SH9), UC9)
EX9 = '{in:baseline}*(1+%s)*(%s)-{in:baseline}*(%s)' % (LIFT9, RP9, RN9); LS9 = '{in:baseline}*%s*(%s)' % (HALO9, RN9)
tools.append(TOOL('promo_fit', 'Promotion Fit Check', 'Is this planned promotion worth running',
    'Pick a title and type the planned price, cost and the copies you expect in a normal period: your own earlier promotions of the title give the lift, and the royalties at the planned price say run, change the price or skip.', [
    IL('title', 'Title', 'title', 'The Salt Pier Letter'), I('price', 'Planned promotion price', 1.5, 'money'), I('cost', 'Planned cost', 45, 'money'), I('baseline', 'Copies you expect in a normal period', 160, 'int')], [
    O('Earlier promotions of this title', 'int', N9), O('Lift from your own promotions', 'pct', LIFT9), O('Lasting lift after, from your own promotions', 'pct', HALO9),
    O('Royalty per copy, normal price', 'money', RN9), O('Royalty per copy, planned price', 'money', RP9), O('Copies expected during', 'int', 'ROUND({in:baseline}*(1+%s),0)' % LIFT9),
    O('Extra royalties expected', 'money', EX9), O('Lasting lift expected', 'money', LS9), O('Net gain expected after cost', 'money', '%s+%s-{in:cost}' % (EX9, LS9)),
    O('Verdict', 'text', 'IF(%s+%s-{in:cost}>0,%s,IF(%s>0,%s,%s))' % (EX9, LS9, v('Worth running'), EX9, v('Change the price'), v('Skip')))],
    GR('What if', ('Planned price 0.99', {'price': 0.99}), ('Planned price 2.49', {'price': 2.49}), ('Cost 120', {'cost': 120}), ('Only 80 copies expected', {'baseline': 80}), ('Another title', {'title': '=' + tok('title', 'The Drowned Ledger'), 'price': 1.02}))))

# 10 ----------------------------------------------------------- price test verdict
RA = ROYN('{in:price_a}', SHARE_AT('{in:price_a}', '{in:share}'), '{in:unit_cost}'); RB = ROYN('{in:price_b}', SHARE_AT('{in:price_b}', '{in:share}'), '{in:unit_cost}')
TA = '{in:units_a}*(%s)' % RA; TB = '{in:units_b}*(%s)' % RB
DA = 'IF({in:days_a}=0,0,(%s)/{in:days_a})' % TA; DB = 'IF({in:days_b}=0,0,(%s)/{in:days_b})' % TB
tools.append(TOOL('price_test', 'Price Test Verdict', 'Which price earns more royalty, A or B',
    'Type two prices tested over equal periods with the copies sold at each: copies and royalty a day, the total royalty, the change and a verdict to keep A, keep B or test longer.', [
    I('price_a', 'Price A', 4.99, 'money'), I('price_b', 'Price B', 5.99, 'money'), I('days_a', 'Days at A', 14, 'int'), I('days_b', 'Days at B', 14, 'int'), I('units_a', 'Copies sold at A', 52, 'int'), I('units_b', 'Copies sold at B', 47, 'int'),
    I('share', 'Royalty share (check each store\'s current terms)', 0.70, 'pct'), I('unit_cost', 'Unit cost per copy', 0.12, 'money')], [
    O('Copies a day at A', 'num', 'IF({in:days_a}=0,0,{in:units_a}/{in:days_a})'), O('Copies a day at B', 'num', 'IF({in:days_b}=0,0,{in:units_b}/{in:days_b})'), O('Royalty per copy at A', 'money', RA), O('Royalty per copy at B', 'money', RB),
    O('Total royalty at A', 'money', TA), O('Total royalty at B', 'money', TB), O('Royalty a day at A', 'money', DA), O('Royalty a day at B', 'money', DB),
    O('Royalty change, B against A', 'pct', 'IF(%s=0,0,%s/(%s)-1)' % (DA, DB, DA)), O('Copy lift B needs to match A', 'pct', 'IF((%s)=0,0,(%s)/(%s)-1)' % (RB, RA, RB)),
    O('Verdict', 'text', 'IF(OR(MIN({in:units_a},{in:units_b})<{set:test_min_units},ABS(IF(%s=0,0,%s/(%s)-1))<{set:price_test_margin}),%s,IF(%s>%s,%s,%s))' % (DA, DB, DA, v('Test longer'), DB, DA, v('Keep B'), v('Keep A')))],
    GR('What if', ('B sells 60 copies', {'units_b': 60}), ('B sells 40 copies', {'units_b': 40}), ('B sells 20 copies', {'units_b': 20, 'units_a': 22}), ('B costs 6.99', {'price_b': 6.99}), ('B costs 3.99', {'price_b': 3.99, 'units_b': 75}))))

# 11 ----------------------------------------------------------- price change break-even
RC11 = ROYN('{in:current}', SHARE_AT('{in:current}', '{in:share}'), '{in:unit_cost}'); RN11 = ROYN('{in:new}', SHARE_AT('{in:new}', '{in:share}'), '{in:unit_cost}')
TOT_NEW = '{in:units}*(1+{in:expected})*(%s)' % RN11; TOT_NOW = '{in:units}*(%s)' % RC11
tools.append(TOOL('price_change', 'Price Change Break-Even', 'How many more or fewer copies a new price needs',
    'Type your price, a new price and the copies you sell: the copy lift the new price needs to keep the same royalty, the royalty at the lift you expect and a verdict to raise, hold or lower.', [
    I('current', 'Current price', 4.99, 'money'), I('new', 'New price', 5.99, 'money'), I('units', 'Copies a month at the current price', 80, 'int'), I('expected', 'Change in copies you expect (negative for fewer)', -0.10, 'pct'),
    I('share', 'Royalty share (check each store\'s current terms)', 0.70, 'pct'), I('unit_cost', 'Unit cost per copy', 0.12, 'money')], [
    O('Royalty per copy now', 'money', RC11), O('Royalty per copy at the new price', 'money', RN11), O('Copy lift needed to keep the same royalty', 'pct', 'IF((%s)=0,0,(%s)/(%s)-1)' % (RN11, RC11, RN11)),
    O('Copies a month needed', 'int', 'IF((%s)=0,0,ROUND({in:units}*(%s)/(%s),0))' % (RN11, RC11, RN11)), O('Royalty a month now', 'money', TOT_NOW), O('Royalty a month at the new price and your expected change', 'money', TOT_NEW),
    O('Change in royalty a month', 'money', '%s-%s' % (TOT_NEW, TOT_NOW)), O('Change in royalty', 'pct', 'IF((%s)=0,0,(%s)/(%s)-1)' % (TOT_NOW, TOT_NEW, TOT_NOW)),
    O('Verdict', 'text', 'IF((%s)=0,%s,IF((%s)/(%s)-1>{set:price_test_margin},IF({in:new}>{in:current},%s,%s),%s))' % (TOT_NOW, v('Hold the price'), TOT_NEW, TOT_NOW, v('Raise is worth it'), v('Lower is worth it'), v('Hold the price')))],
    GR('Copies change you expect', ('Copies fall 30%', {'expected': -0.30}), ('Copies fall 20%', {'expected': -0.20}), ('Copies fall 5%', {'expected': -0.05}), ('Copies stay', {'expected': 0.0}),
       ('Lower to 3.99, copies rise 40%', {'new': 3.99, 'expected': 0.40}), ('Lower to 3.99, copies rise 10%', {'new': 3.99, 'expected': 0.10}))))

# 12 ----------------------------------------------------------- platform comparison
def PF(pl, col): return 'SUMIFS({range:adsdays.%s},{range:adsdays.platform},%s,{range:adsdays.date},">="&({today}-{in:days}))' % (col, tok('platform', pl))
def PR(pl): return 'IFERROR(%s/%s,0)' % (PF(pl, 'royalties'), PF(pl, 'spend'))
PLS = AD_PLATFORMS
R3 = [PR(p) for p in PLS]; MXR = 'MAX(%s)' % ','.join(R3); MNR = 'MIN(%s)' % ','.join(R3)
BESTP = 'IF(%s=%s,%s,IF(%s=%s,%s,%s))' % (R3[0], MXR, tok('platform', PLS[0]), R3[1], MXR, tok('platform', PLS[1]), tok('platform', PLS[2]))
tools.append(TOOL('platform_cmp', 'Platform Comparison', 'Which ad platform returns the most',
    'Spend, royalties, return, cost per sale and cost per click for each platform over the last 30, 60 or 90 days, the best and the weakest platform and the budget to move.', [
    I('days', 'Days to look back (30, 60 or 90)', 90, 'int'), I('move', 'Share of the weakest platform budget to move', 0.5, 'pct')], [
    O('Store ads: spend', 'money', PF('Store ads', 'spend')), O('Store ads: return', 'num', R3[0]), O('Store ads: cost per sale', 'money', 'IFERROR(%s/%s,0)' % (PF('Store ads', 'spend'), PF('Store ads', 'sales'))),
    O('Store ads: cost per click', 'money', 'IFERROR(%s/%s,0)' % (PF('Store ads', 'spend'), PF('Store ads', 'clicks'))),
    O('Social ads: spend', 'money', PF('Social ads', 'spend')), O('Social ads: return', 'num', R3[1]), O('Social ads: cost per sale', 'money', 'IFERROR(%s/%s,0)' % (PF('Social ads', 'spend'), PF('Social ads', 'sales'))),
    O('Social ads: cost per click', 'money', 'IFERROR(%s/%s,0)' % (PF('Social ads', 'spend'), PF('Social ads', 'clicks'))),
    O('Search ads: spend', 'money', PF('Search ads', 'spend')), O('Search ads: return', 'num', R3[2]), O('Search ads: cost per sale', 'money', 'IFERROR(%s/%s,0)' % (PF('Search ads', 'spend'), PF('Search ads', 'sales'))),
    O('Search ads: cost per click', 'money', 'IFERROR(%s/%s,0)' % (PF('Search ads', 'spend'), PF('Search ads', 'clicks'))),
    O('Best return', 'num', MXR), O('Weakest return', 'num', MNR),
    O('Budget to move over the window', 'money', '{in:move}*IF(%s=%s,%s,IF(%s=%s,%s,%s))' % (R3[0], MNR, PF('Store ads', 'spend'), R3[1], MNR, PF('Social ads', 'spend'), PF('Search ads', 'spend'))),
    O('Verdict', 'text', '%s&" "&%s' % (v('Move budget to'), BESTP))],
    GR('What if', ('Last 30 days', {'days': 30}), ('Last 60 days', {'days': 60}), ('Move 25%', {'move': 0.25}), ('Move all of it', {'move': 1.0}))))

# 13 ----------------------------------------------------------- ad budget allocator
FAC = 'IF({in:scenario}=%s,1+{in:best},IF({in:scenario}=%s,1-{in:worst},1))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
WSUM = 'SUM({range:ledger.weight})'; CURB = 'SUMIFS({range:ledger.daily_budget},%s)' % RUNSTAT
WIDX = 'MATCH(MIN(%s),%s,0)' % (L_('running_return'), L_('running_return'))
tools.append(TOOL('allocator', 'Ad Budget Allocator', 'How to split one monthly budget across the campaigns',
    'Type a monthly ad budget and a scenario: each running campaign gets a share by its return (campaigns under your target get none), with the royalties expected at their own returns and a shift to make.', [
    I('budget', 'Monthly ad budget', 1600, 'money'), IL('scenario', 'Scenario', 'scen', 'Base'), I('best', 'Best case: returns higher by', 0.15, 'pct'), I('worst', 'Worst case: returns lower by', 0.20, 'pct')], [
    O('Running campaigns', 'int', NRUN), O('Campaigns that get budget', 'int', 'COUNTIFS(%s,">0")' % L_('weight')), O('Current monthly budget of running campaigns', 'money', '30*%s' % CURB),
    O('Budget for the best campaign', 'money', 'IF(%s=0,0,{in:budget}*MAX(%s)/%s)' % (WSUM, L_('weight'), WSUM)), O('The best campaign', 'text', 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (L_('campaign'), L_('weight'), L_('weight'))),
    O('The lowest-return campaign', 'text', 'INDEX(%s,%s)' % (L_('campaign'), WIDX)), O('Its current monthly budget', 'money', '30*INDEX(%s,%s)' % (L_('daily_budget'), WIDX)),
    O('Budget cut from the lowest-return campaign', 'money', '30*INDEX(%s,%s)-IF(%s=0,0,{in:budget}*INDEX(%s,%s)/%s)' % (L_('daily_budget'), WIDX, WSUM, L_('weight'), WIDX, WSUM)),
    O('Royalties expected with the new split', 'money', 'IF(%s=0,0,{in:budget}*SUM(%s)/%s*(%s))' % (WSUM, L_('weighted_return'), WSUM, FAC)),
    O('Royalties with your current split, same budget', 'money', 'IF(%s=0,0,{in:budget}*SUM(%s)/%s*(%s))' % (CURB, L_('budget_return'), CURB, FAC)),
    O('Return expected with the new split', 'num', 'IF(%s=0,0,SUM(%s)/%s*(%s))' % (WSUM, L_('weighted_return'), WSUM, FAC)),
    O('Verdict', 'text', 'IF(MIN(%s)<{set:ad_return_target},%s&" "&ROUND(30*INDEX(%s,%s),0)&" "&%s&" "&INDEX(%s,%s)&" "&%s&" "&INDEX(%s,MATCH(MAX(%s),%s,0)),%s)' % (
        L_('running_return'), v('Shift'), L_('daily_budget'), WIDX, v('from'), L_('campaign'), WIDX, v('to'), L_('campaign'), L_('weight'), L_('weight'), v('Keep the split')))],
    GR('What if', ('Budget 1,000', {'budget': 1000}), ('Budget 2,500', {'budget': 2500}), ('Best case', {'scenario': '=' + tok('scen', 'Best')}), ('Worst case', {'scenario': '=' + tok('scen', 'Worst')}), ('Worst case, budget 1,000', {'scenario': '=' + tok('scen', 'Worst'), 'budget': 1000}))))

# 14 ----------------------------------------------------------- launch ad ramp planner
S1 = '({in:before}*({in:before}+1)/2)'; S2 = '({in:after}*({in:after}+1)/2)'
BB = '{in:budget}*{in:share_before}'; BD = '{in:budget}*{in:share_day}'; BA = '{in:budget}*(1-{in:share_before}-{in:share_day})'
PMIN = 'SUMIFS({range:platforms.daily_min},{range:platforms.platform},{in:platform})'
OVER14 = 'MAX(0,%s*({in:before}+1+{in:after})-{in:budget})' % PMIN
tools.append(TOOL('ramp', 'Launch Ad Ramp Planner', 'How to spread a launch ad budget around the release day',
    'Type the release date, the launch budget and how much goes before the release, on the day and after: the first and last daily budget on each side, the dates and whether the budget covers the platform minimum.', [
    I('release', 'Release date', LAUNCH_DATE.isoformat(), 'date'), I('budget', 'Launch ad budget', 600, 'money'), I('before', 'Days of ads before the release', 14, 'int'), I('after', 'Days of ads after the release', 14, 'int'),
    I('share_before', 'Share of the budget before the release', 0.35, 'pct'), I('share_day', 'Share of the budget on the release day', 0.15, 'pct'), IL('platform', 'Platform', 'platform', 'Social ads')], [
    O('First day of ads', 'date', '{in:release}-{in:before}'), O('Last day of ads', 'date', '{in:release}+{in:after}'), O('Days of ads', 'int', '{in:before}+1+{in:after}'),
    O('Budget before the release', 'money', BB), O('First day, budget', 'money', 'IF({in:before}=0,0,%s/%s)' % (BB, S1)), O('Day before the release, budget', 'money', 'IF({in:before}=0,0,%s*{in:before}/%s)' % (BB, S1)),
    O('Release day, budget', 'money', BD), O('Day after the release, budget', 'money', 'IF({in:after}=0,0,%s*{in:after}/%s)' % (BA, S2)), O('Last day, budget', 'money', 'IF({in:after}=0,0,%s/%s)' % (BA, S2)),
    O('Budget after the release', 'money', BA), O('Platform daily minimum', 'money', PMIN), O('Budget needed to cover the minimum on every day', 'money', '%s*({in:before}+1+{in:after})' % PMIN),
    O('Verdict', 'text', 'IF({in:share_before}+{in:share_day}>1,%s,IF(%s>0,%s&" "&ROUND(%s,0),%s))' % (v('Shares are over 100%'), OVER14, v('Over by'), OVER14, v('Inside the budget')))],
    GR('What if', ('Budget 120', {'budget': 120}), ('Budget 300', {'budget': 300}), ('21 days before', {'before': 21}), ('More on the release day', {'share_day': 0.30}), ('Search ads', {'platform': '=' + tok('platform', 'Search ads')}))))

# 15 ----------------------------------------------------------- ad spend and royalties forecast
def MSUM(col, a, b): return 'SUMIFS({range:adsmonth.%s},{range:adsmonth.month},">="&EDATE(%s,%d),{range:adsmonth.month},"<"&EDATE(%s,%d))' % (col, MS, a, MS, b)
AS3 = '%s/3' % MSUM('spend', -3, 0); AR3 = '%s/3' % MSUM('royalties', -3, 0); PS3 = '%s/3' % MSUM('spend', -6, -3); PR3 = '%s/3' % MSUM('royalties', -6, -3)
TS = 'MIN(1.3,MAX(0.7,IFERROR((%s)/(%s),1)))' % (AS3, PS3); TRY = 'MIN(1.3,MAX(0.7,IFERROR((%s)/(%s),1)))' % (AR3, PR3)
def FS(k): return '(%s)*POWER(%s,(%d)/3)' % (AS3, TS, k + 2)
def FR(k): return '(%s)*POWER(%s,(%d)/3)*(%s)' % (AR3, TRY, k + 2, FAC)
tools.append(TOOL('ad_forecast', 'Ad Spend Forecast', 'What will the next 3 months of ads spend and bring',
    'The last 6 full months give a trend: the next 3 months of spend and royalties in a Base, Best or Worst scenario, the return they imply and a verdict on whether ads pay or are slowing down.', [
    IL('scenario', 'Scenario', 'scen', 'Base'), I('best', 'Best case: royalties higher by', 0.15, 'pct'), I('worst', 'Worst case: royalties lower by', 0.20, 'pct')], [
    O('Average spend, last 3 months', 'money', AS3), O('Average royalties, last 3 months', 'money', AR3), O('Spend trend, last 3 against the 3 before', 'num', TS), O('Royalties trend, last 3 against the 3 before', 'num', TRY),
    O('Spend, next month', 'money', FS(1)), O('Spend, month 2', 'money', FS(2)), O('Spend, month 3', 'money', FS(3)), O('Royalties, next month', 'money', FR(1)), O('Royalties, month 2', 'money', FR(2)), O('Royalties, month 3', 'money', FR(3)),
    O('Spend, 3 months', 'money', '%s+%s+%s' % (FS(1), FS(2), FS(3))), O('Royalties, 3 months', 'money', '%s+%s+%s' % (FR(1), FR(2), FR(3))),
    O('Return expected, month 2', 'num', 'IFERROR((%s)/(%s),0)' % (FR(2), FS(2))),
    O('Verdict', 'text', 'IF(AND(IFERROR((%s)/(%s),0)>={set:ad_return_target},%s>=0.95),%s,%s)' % (FR(2), FS(2), TRY, v('Ads pay'), v('Ads slow down')))],
    GR('What if', ('Best case', {'scenario': '=' + tok('scen', 'Best')}), ('Worst case', {'scenario': '=' + tok('scen', 'Worst')}), ('Best case, 30% higher', {'scenario': '=' + tok('scen', 'Best'), 'best': 0.30}),
       ('Worst case, 40% lower', {'scenario': '=' + tok('scen', 'Worst'), 'worst': 0.40}))))

# 16 ----------------------------------------------------------- ad share of income check
SPM = 'SUMIFS({range:adsdays.spend},{range:adsdays.month},%s)' % MS
RYM = 'SUMIFS({range:salesmonth.royalties_home},{range:salesmonth.month},%s)+SUMIFS({range:salesmonth.page_income},{range:salesmonth.month},%s)' % (MS, MS)
SP12 = 'SUMIFS({range:adsdays.spend},{range:adsdays.date},">="&EDATE(%s,-11))' % MS
RY12 = 'SUMIFS({range:salesmonth.royalties_home},{range:salesmonth.month},">="&EDATE(%s,-11))+SUMIFS({range:salesmonth.page_income},{range:salesmonth.month},">="&EDATE(%s,-11))' % (MS, MS)
tools.append(TOOL('ad_share', 'Ad Share of Income Check', 'How much of your royalties go back into ads',
    'Ad spend as a share of all royalties and page-read income this month and over 12 months against the limit you set: the points over or under, the spend still allowed and a verdict for each.', [
    I('limit', 'Highest ad spend as a share of royalties (your own number)', 0.15, 'pct')], [
    O('Ad spend this month', 'money', SPM), O('All royalties this month', 'money', RYM), O('Share this month', 'pct', 'IFERROR((%s)/(%s),0)' % (SPM, RYM)),
    O('Ad spend, last 12 months', 'money', SP12), O('All royalties, last 12 months', 'money', RY12), O('Share, last 12 months', 'pct', 'IFERROR((%s)/(%s),0)' % (SP12, RY12)),
    O('Points over or under the limit, this month', 'num', '(IFERROR((%s)/(%s),0)-{in:limit})*100' % (SPM, RYM)), O('Points over or under the limit, 12 months', 'num', '(IFERROR((%s)/(%s),0)-{in:limit})*100' % (SP12, RY12)),
    O('Spend still allowed this month', 'money', '{in:limit}*(%s)-(%s)' % (RYM, SPM)),
    O('Verdict, 12 months', 'text', 'IF(IFERROR((%s)/(%s),0)<={in:limit},%s,%s&" "&ROUND((IFERROR((%s)/(%s),0)-{in:limit})*100,1)&" "&%s)' % (SP12, RY12, v('Within the limit'), v('Over by'), SP12, RY12, v('points'))),
    O('Verdict, this month', 'text', 'IF(IFERROR((%s)/(%s),0)<={in:limit},%s,%s&" "&ROUND((IFERROR((%s)/(%s),0)-{in:limit})*100,1)&" "&%s)' % (SPM, RYM, v('Within the limit'), v('Over by'), SPM, RYM, v('points')))],
    GR('What if', ('Limit 10%', {'limit': 0.10}), ('Limit 12%', {'limit': 0.12}), ('Limit 20%', {'limit': 0.20}), ('Limit 25%', {'limit': 0.25}))))

# 17 ----------------------------------------------------------- page-read-aware return
TIDP = 'INDEX({range:titles.title_id},MATCH({in:title},{range:titles.title},0))'
EPP = 'SUMIFS({range:editions.list_price},{range:editions.title},{in:title},{range:editions.format},%s)' % EBK
UCP = 'SUMIFS({range:editions.unit_cost},{range:editions.title},{in:title},{range:editions.format},%s)' % EBK
SHP = 'SUMIFS({range:editions.royalty_share},{range:editions.title},{in:title},{range:editions.format},%s)' % EBK
ROYP = ROYN(EPP, SHARE_AT(EPP, SHP), UCP)
OWNPG = 'IFERROR(SUMIFS({range:adsdays.page_reads},{range:adsdays.title_id},%s)/SUMIFS({range:adsdays.sales},{range:adsdays.title_id},%s),0)' % (TIDP, TIDP)
tools.append(TOOL('pageread_return', 'Page-Read-Aware Return', 'Do ads pay once page reads are counted',
    'For a title in a lending program: the royalty per sale plus the pages read per sale at your rate, turned into the return per click at your conversion and cost per click, with and without page reads.', [
    IL('title', 'Title', 'title', 'The Orchard Key'), I('conv', 'Click-to-sale conversion', 0.05, 'pct'), I('cpc', 'Cost per click', 0.12, 'money'), I('pages', 'Pages read per sale (type your own)', 110, 'num'),
    I('rate', 'Pay per page read (your own number)', 0.0042, 'num')], [
    O('Royalty per sale from the copy', 'money', ROYP), O('Pages read per sale in your ad history', 'num', OWNPG), O('Page-read income per sale', 'money', '{in:pages}*{in:rate}'),
    O('Value of one sale with page reads', 'money', '(%s)+{in:pages}*{in:rate}' % ROYP), O('Value of one click, copy only', 'money', '{in:conv}*(%s)' % ROYP), O('Value of one click, with page reads', 'money', '{in:conv}*((%s)+{in:pages}*{in:rate})' % ROYP),
    O('Return, copy only', 'num', 'IF({in:cpc}=0,0,{in:conv}*(%s)/{in:cpc})' % ROYP), O('Return, with page reads', 'num', 'IF({in:cpc}=0,0,{in:conv}*((%s)+{in:pages}*{in:rate})/{in:cpc})' % ROYP),
    O('Highest cost per click with page reads', 'money', '{in:conv}*((%s)+{in:pages}*{in:rate})/{set:ad_return_target}' % ROYP),
    O('Verdict', 'text', 'IF(IF({in:cpc}=0,0,{in:conv}*((%s)+{in:pages}*{in:rate})/{in:cpc})<{set:ad_return_target},%s,IF(IF({in:cpc}=0,0,{in:conv}*(%s)/{in:cpc})<{set:ad_return_target},%s,%s))' % (ROYP, v('Not even with page reads'), ROYP, v('Ads pay with page reads'), v('Ads pay on royalties alone')))],
    GR('What if', ('Pages per sale 60', {'pages': 60}), ('Pages per sale 200', {'pages': 200}), ('Cost per click 0.20', {'cpc': 0.20}), ('A 0.99 title', {'title': '=' + tok('title', 'The Tidebound Cartographer'), 'pages': 115}), ('Rate 0.0030', {'rate': 0.003}))))

# 18 ----------------------------------------------------------- campaign age check
ST18 = 'INDEX({range:campaigns.start_date},MATCH({in:campaign},{range:campaigns.campaign},0))'
EN18 = 'IF(INDEX({range:campaigns.end_date},MATCH({in:campaign},{range:campaigns.campaign},0))>0,INDEX({range:campaigns.end_date},MATCH({in:campaign},{range:campaigns.campaign},0)),{today})'
def AW(col, a, b): return 'SUMIFS({range:adsdays.%s},{range:adsdays.campaign_id},%s,{range:adsdays.date},">="&(%s+%d),{range:adsdays.date},"<"&(%s+%d))' % (col, CID, ST18, a, ST18, b)
def AWR(a, b): return 'IFERROR(%s/%s,0)' % (AW('royalties', a, b), AW('spend', a, b))
LATE = 'IFERROR(SUMIFS({range:adsdays.royalties},{range:adsdays.campaign_id},%s,{range:adsdays.date},">"&(%s-28),{range:adsdays.date},"<="&%s)/SUMIFS({range:adsdays.spend},{range:adsdays.campaign_id},%s,{range:adsdays.date},">"&(%s-28),{range:adsdays.date},"<="&%s),0)' % (CID, EN18, EN18, CID, EN18, EN18)
tools.append(TOOL('age_check', 'Campaign Age Check', 'Is the return of this campaign wearing out',
    'Pick a campaign: its return in the first 4 weeks, weeks 5 to 8, weeks 9 to 12 and the latest 4 weeks, the fall from the start and a verdict to refresh the creative (the ad image and text) or keep it.', [
    IL('campaign', 'Campaign', 'campaign', 'Lantern Bay 1 - cosy series starters'), I('drop', 'Refresh when the return falls by (your own number)', 0.20, 'pct')], [
    O('Weeks run', 'num', '(%s-%s)/7' % (EN18, ST18)), O('Return, weeks 1-4', 'num', AWR(0, 28)), O('Return, weeks 5-8', 'num', AWR(28, 56)), O('Return, weeks 9-12', 'num', AWR(56, 84)),
    O('Return, latest 4 weeks', 'num', LATE), O('Spend, first 4 weeks', 'money', AW('spend', 0, 28)),
    O('Fall from the first 4 weeks to the latest 4', 'pct', 'IF(%s=0,0,%s/(%s)-1)' % (AWR(0, 28), LATE, AWR(0, 28))),
    O('Return over the whole run', 'num', 'IFERROR(SUMIFS({range:adsdays.royalties},{range:adsdays.campaign_id},%s)/SUMIFS({range:adsdays.spend},{range:adsdays.campaign_id},%s),0)' % (CID, CID)),
    O('Verdict', 'text', 'IF((%s-%s)/7<8,%s,IF(%s=0,%s,IF(%s/(%s)-1<=-{in:drop},%s,%s)))' % (EN18, ST18, v('Too early to judge'), AWR(0, 28), v('Too early to judge'), LATE, AWR(0, 28), v('Refresh the creative'), v('Keep the creative')))],
    GR('What if', ('Refresh at a 10% fall', {'drop': 0.10}), ('Refresh at a 40% fall', {'drop': 0.40}), ('Another running campaign', {'campaign': '=' + tok('campaign', 'Ember Crown 1 - similar authors')}),
       ('An ended campaign', {'campaign': '=' + tok('campaign', 'Ember Crown 4 - similar authors')}))))
assert len(tools) == 18, len(tools)
