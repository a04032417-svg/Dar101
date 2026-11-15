"""Author and Self-Publisher Business suite - part 4: Ads and Price Promotions."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au4_lists import *
from au4_tables import settings, tables
from au4_tools import tools
import au4_data as D

SUITE = 'fx-20261115-author-publisher'
NOTE = "Sample wording: adapt it to your own business. Confirm anything about tax, contracts or store terms with your adviser and check each store's current terms."
YES = '{list:yesno.yes}'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
RUN = tok('adstatus', 'Running'); DONE = tok('pstatus', 'Done'); PLN = tok('pstatus', 'Planned'); EBK = tok('format', 'Ebook')

# ------------------------------------------------------------------ forms (12)
def AFIRST(col, a, b):   # ad numbers of the picked campaign in a window counted from its start
    return 'SUMIFS({range:adsdays.%s},{range:adsdays.campaign_id},{pick},{range:adsdays.date},">="&(%s+%d),{range:adsdays.date},"<"&(%s+%d))' % (
        col, LK('campaigns', 'campaign_id', 'start_date'), a, LK('campaigns', 'campaign_id', 'start_date'), b)
forms = [
    FORM('campaign_setup', 'Campaign Setup Sheet', 'Campaign setup with budget, bid and target bid', 'campaigns.campaign_id', F(
        ('Campaign', 'campaigns.campaign'), ('Title', 'campaigns.title'), ('Platform', 'campaigns.platform'), ('Start date', 'campaigns.start_date'), ('Status', 'campaigns.status'), ('Daily budget', 'campaigns.daily_budget'),
        ('Bid per click', 'campaigns.bid'), ('Target bid per click', 'campaigns.target_bid'), ('Ad specialist', 'campaigns.specialist'), ('Ad specialist phone', 'campaigns.specialist_phone')) + [
        FF('Budget for 30 days', '30*%s' % LK('campaigns', 'campaign_id', 'daily_budget'), 'money'),
        FF('Break-even bid per click', 'IFERROR(INDEX({range:maxbid.break_even_bid},MATCH({pick},{range:maxbid.campaign_id},0)),0)', 'money'),
        FF('Return target', '{set:ad_return_target}', 'num')]),
    FORM('weekly_review', 'Campaign Weekly Review Sheet', 'Weekly review of one campaign', 'ledger.campaign_id', F(
        ('Campaign', 'ledger.campaign'), ('Title', 'ledger.title'), ('Platform', 'ledger.platform'), ('Status', 'ledger.status'), ('Days run', 'ledger.days_run'), ('Spend, 60 days', 'ledger.spend_60'), ('Royalties, 60 days', 'ledger.royalties_60'),
        ('Return, 60 days', 'ledger.return_60'), ('Return, 30 days', 'ledger.return_30'), ('Conversion, whole run', 'ledger.conversion'), ('Cost per sale, whole run', 'ledger.cost_per_sale'), ('Stop, hold or raise', 'ledger.verdict')) + [
        FF('Return target', '{set:ad_return_target}', 'num'), FF('Rank among all campaigns', 'INDEX({range:ledger.rank},MATCH({pick},{range:ledger.campaign_id},0))', 'int')]),
    FORM('daily_entry', 'Ad Daily Entry Sheet', 'Ad numbers of one day', 'adsdays.ad_id', F(
        ('Date', 'adsdays.date'), ('Campaign', 'adsdays.campaign'), ('Platform', 'adsdays.platform'), ('Spend', 'adsdays.spend'), ('Impressions', 'adsdays.impressions'), ('Clicks', 'adsdays.clicks'), ('Sales', 'adsdays.sales'),
        ('Page reads', 'adsdays.page_reads'), ('Royalties with page reads', 'adsdays.royalties'), ('Profit', 'adsdays.profit'), ('Cost per click', 'adsdays.cpc')) + [
        FF('Campaign daily budget', 'IFERROR(INDEX({range:campaigns.daily_budget},MATCH(%s,{range:campaigns.campaign_id},0)),0)' % LK('adsdays', 'ad_id', 'campaign_id'), 'money')]),
    FORM('stop_sheet', 'Campaign Stop Sheet', 'Stop decision for one campaign', 'rank.place', F(
        ('Place on the list', 'rank.place'), ('Campaign', 'rank.campaign'), ('Platform', 'rank.platform'), ('Status', 'rank.status'), ('Spend, 60 days', 'rank.spend_60'), ('Royalties, 60 days', 'rank.royalties_60'),
        ('Return, 60 days', 'rank.return_60'), ('Profit, 60 days', 'rank.profit_60'), ('Stop, hold or raise', 'rank.verdict'), ('Daily budget', 'rank.budget_day'), ('Budget freed a day', 'rank.freed')) + [
        FF('Budget freed in 30 days', '30*%s' % LK('rank', 'place', 'freed'), 'money'), FF('Return target', '{set:ad_return_target}', 'num')]),
    FORM('bid_sheet', 'Bid Change Sheet', 'Bid change for one campaign', 'maxbid.campaign_id', F(
        ('Campaign', 'maxbid.campaign'), ('Conversion', 'maxbid.conversion'), ('Royalty per sale', 'maxbid.royalty_per_sale'), ('Break-even bid per click', 'maxbid.break_even_bid'), ('Target bid per click', 'maxbid.target_bid'),
        ('Current bid', 'maxbid.current_bid'), ('Actual cost per click', 'maxbid.actual_cpc'), ('Bid check', 'maxbid.verdict')) + [
        FF('Change to the target bid', '%s-%s' % (LK('maxbid', 'campaign_id', 'target_bid'), LK('maxbid', 'campaign_id', 'current_bid')), 'money'), FF('Share of break-even you aim for', '{set:ad_share_of_breakeven}', 'pct')]),
    FORM('promo_plan_sheet', 'Promotion Plan Sheet', 'Promotion plan with dates, prices and cost', 'promos.promo_id', F(
        ('Title', 'promos.title'), ('Kind', 'promos.kind'), ('Start date', 'promos.start_date'), ('End date', 'promos.end_date'), ('Days', 'promos.days'), ('Normal price', 'promos.normal_price'), ('Promotion price', 'promos.promo_price'),
        ('Cost', 'promos.cost'), ('Status', 'promos.status'), ('Newsletter partner', 'promos.partner'), ('Partner phone', 'promos.partner_phone')) + [
        FF('Price drop', 'IF(%s=0,0,1-%s/%s)' % (LK('promos', 'promo_id', 'normal_price'), LK('promos', 'promo_id', 'promo_price'), LK('promos', 'promo_id', 'normal_price')), 'pct'),
        FF('Copies before, for comparison', LK('promos', 'promo_id', 'units_before'), 'int')]),
    FORM('promo_result_sheet', 'Promotion Result Sheet', 'Result of one promotion', 'promoresults.promo_id', F(
        ('Title', 'promoresults.title'), ('Kind', 'promoresults.kind'), ('Start date', 'promoresults.start_date'), ('Copies before', 'promoresults.units_before'), ('Copies during', 'promoresults.units_during'), ('Copies after', 'promoresults.units_after'),
        ('Extra copies', 'promoresults.extra_copies'), ('Extra royalties from copies', 'promoresults.extra_royalties'), ('Page-read income moved', 'promoresults.page_extra'), ('Lasting lift after', 'promoresults.after_effect'),
        ('Cost', 'promoresults.cost'), ('Net gain after cost', 'promoresults.net_gain'), ('Payback days', 'promoresults.payback_days'), ('Repeat, change or skip', 'promoresults.verdict'))),
    FORM('price_change_sheet', 'Price Change Sheet', 'Price change with the royalty it keeps', 'breakeven.edition_id', F(
        ('Title', 'breakeven.title'), ('Format', 'breakeven.format'), ('Store', 'breakeven.store'), ('List price', 'breakeven.price'), ('Unit cost', 'breakeven.unit_cost'), ('Royalty share used', 'breakeven.share_used'),
        ('Royalty per copy', 'breakeven.royalty_per_copy'), ('Break-even ad share of price', 'breakeven.break_even_share')) + [
        FF('Royalty per copy if the price rises by 1', 'MAX(0,(%s+1)*%s-%s)' % (LK('breakeven', 'edition_id', 'price'), LK('breakeven', 'edition_id', 'share_used'), LK('breakeven', 'edition_id', 'unit_cost')), 'money'),
        FF('Copies a rise can lose, same royalty', 'IFERROR(1-%s/MAX(0,(%s+1)*%s-%s),0)' % (LK('breakeven', 'edition_id', 'royalty_per_copy'), LK('breakeven', 'edition_id', 'price'), LK('breakeven', 'edition_id', 'share_used'), LK('breakeven', 'edition_id', 'unit_cost')), 'pct')]),
    FORM('price_test_sheet', 'Price Test Sheet', 'Price test with both prices and the verdict', 'pricecmp.test_id', F(
        ('Title', 'pricecmp.title'), ('Royalty a day at A', 'pricecmp.royalty_day_a'), ('Royalty a day at B', 'pricecmp.royalty_day_b'), ('Royalty change, B against A', 'pricecmp.change'), ('Copy lift B needs to match A', 'pricecmp.lift_needed'),
        ('Copy lift seen at B', 'pricecmp.lift_seen'), ('Fewest copies in a period', 'pricecmp.min_units'), ('Keep A, keep B or test longer', 'pricecmp.verdict')) + [
        FF('Price A', 'INDEX({range:pricetests.price_a},MATCH({pick},{range:pricetests.test_id},0))', 'money'), FF('Price B', 'INDEX({range:pricetests.price_b},MATCH({pick},{range:pricetests.test_id},0))', 'money'),
        FF('Days at each price', 'INDEX({range:pricetests.days_a},MATCH({pick},{range:pricetests.test_id},0))', 'int')]),
    FORM('budget_sheet', 'Ad Budget Sheet', 'Ad budget of one month', 'adsmonth.month', F(
        ('Month', 'adsmonth.month'), ('Spend', 'adsmonth.spend'), ('Royalties with page reads', 'adsmonth.royalties'), ('Profit', 'adsmonth.profit'), ('Return', 'adsmonth.return'), ('Budget', 'adsmonth.budget'), ('All royalties', 'adsmonth.all_royalties'),
        ('Ad spend share of royalties', 'adsmonth.share'), ('Spend this year so far', 'adsmonth.spend_year')) + [
        FF('Budget left', '%s-%s' % (LK('adsmonth', 'month', 'budget'), LK('adsmonth', 'month', 'spend')), 'money'), FF('Highest share you accept', '{set:ad_share_limit}', 'pct')]),
    FORM('platform_sheet', 'Platform Review Sheet', 'Platform review over 90 days', 'platforms.platform', F(
        ('Platform', 'platforms.platform'), ('Typical cost per click', 'platforms.typical_cpc'), ('Daily minimum', 'platforms.daily_min')) + [
        FF('Spend, 90 days', 'SUMIFS({range:adsdays.spend},{range:adsdays.platform},{pick},{range:adsdays.date},">="&({today}-90))', 'money'),
        FF('Royalties with page reads, 90 days', 'SUMIFS({range:adsdays.royalties},{range:adsdays.platform},{pick},{range:adsdays.date},">="&({today}-90))', 'money'),
        FF('Return, 90 days', 'IFERROR(SUMIFS({range:adsdays.royalties},{range:adsdays.platform},{pick},{range:adsdays.date},">="&({today}-90))/SUMIFS({range:adsdays.spend},{range:adsdays.platform},{pick},{range:adsdays.date},">="&({today}-90)),0)', 'num'),
        FF('Clicks, 90 days', 'SUMIFS({range:adsdays.clicks},{range:adsdays.platform},{pick},{range:adsdays.date},">="&({today}-90))', 'int'),
        FF('Sales, 90 days', 'SUMIFS({range:adsdays.sales},{range:adsdays.platform},{pick},{range:adsdays.date},">="&({today}-90))', 'int'),
        FF('Cost per click, 90 days', 'IFERROR(SUMIFS({range:adsdays.spend},{range:adsdays.platform},{pick},{range:adsdays.date},">="&({today}-90))/SUMIFS({range:adsdays.clicks},{range:adsdays.platform},{pick},{range:adsdays.date},">="&({today}-90)),0)', 'money')]),
    FORM('creative_sheet', 'Ad Creative Log Sheet', 'Ad creative log: how the ad wears out', 'campaigns.campaign_id', F(
        ('Campaign', 'campaigns.campaign'), ('Title', 'campaigns.title'), ('Platform', 'campaigns.platform'), ('Start date', 'campaigns.start_date'), ('Last reviewed on', 'campaigns.reviewed_on'), ('Bid per click', 'campaigns.bid')) + [
        FF('Weeks run', '(IF(%s>0,%s,{today})-%s)/7' % (LK('campaigns', 'campaign_id', 'end_date'), LK('campaigns', 'campaign_id', 'end_date'), LK('campaigns', 'campaign_id', 'start_date')), 'num'),
        FF('Return, first 4 weeks', 'IFERROR(%s/%s,0)' % (AFIRST('royalties', 0, 28), AFIRST('spend', 0, 28)), 'num'),
        FF('Return, weeks 5 to 8', 'IFERROR(%s/%s,0)' % (AFIRST('royalties', 28, 56), AFIRST('spend', 28, 56)), 'num'),
        FF('Click share of views, first 4 weeks', 'IFERROR(%s/%s,0)' % (AFIRST('clicks', 0, 28), AFIRST('impressions', 0, 28)), 'pct'),
        FF('Click share of views, whole run', 'IFERROR(SUMIFS({range:adsdays.clicks},{range:adsdays.campaign_id},{pick})/SUMIFS({range:adsdays.impressions},{range:adsdays.campaign_id},{pick}),0)', 'pct'),
        FF('Return, whole run', 'IFERROR(SUMIFS({range:adsdays.royalties},{range:adsdays.campaign_id},{pick})/SUMIFS({range:adsdays.spend},{range:adsdays.campaign_id},{pick}),0)', 'num')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('campaign_plan_doc', 'Campaign Plan', 'Campaign plan with budget, bid and target return', 'campaigns.campaign_id', [
        'Campaign plan of {set:company}, dated {today}. Campaign: {col:campaigns.campaign}. Title: {col:campaigns.title}. Platform: {col:campaigns.platform}.',
        'Start date: {col:campaigns.start_date}. Daily budget: {col:campaigns.daily_budget}. Bid per click: {col:campaigns.bid}. The target bid from your own conversion and royalty per sale is {col:campaigns.target_bid}.',
        'The campaign aims for a return of at least {set:ad_return_target} royalties for every unit of ad spend (your own number). It is reviewed every week and gets a verdict to stop, hold or raise after {set:min_ad_days} days.',
        'The ad specialist sends spend, clicks, sales and page reads every week. Figures from the stores are estimates until the payment arrives.'], ['Author-publisher', 'Ad specialist'], NOTE),
    DOC('weekly_report_doc', 'Weekly Ad Report', 'Weekly ad report for one campaign', 'ledger.campaign_id', [
        'Weekly ad report of {set:company}, dated {today}. Campaign: {col:ledger.campaign}, title {col:ledger.title}, platform {col:ledger.platform}, status {col:ledger.status}.',
        'Last 60 days: spend {col:ledger.spend_60}, royalties with page reads {col:ledger.royalties_60}, return {col:ledger.return_60}. Last 30 days: return {col:ledger.return_30}. The target is {set:ad_return_target}.',
        'Whole run of {col:ledger.days_run} days: spend {col:ledger.spend}, clicks {col:ledger.clicks}, sales {col:ledger.sales}, page reads {col:ledger.page_reads}, profit {col:ledger.profit}, conversion {col:ledger.conversion}, cost per sale {col:ledger.cost_per_sale}.',
        'Verdict of the sheet: {col:ledger.verdict}. Royalties are estimates until the stores pay.'], ['Author-publisher', 'Ad specialist'], NOTE),
    DOC('monthly_report_doc', 'Monthly Ad Report', 'Monthly ad report', 'adsmonth.month', [
        'Monthly ad report of {set:company} for the month starting {col:adsmonth.month}, dated {today}.',
        'Spend {col:adsmonth.spend} against a budget of {col:adsmonth.budget}. Clicks {col:adsmonth.clicks}, sales {col:adsmonth.sales}, page reads {col:adsmonth.page_reads}.',
        'Royalties with page reads {col:adsmonth.royalties}, profit {col:adsmonth.profit}, return {col:adsmonth.return}, cost per click {col:adsmonth.cpc}.',
        'Campaigns below the return target of {set:ad_return_target}: {col:adsmonth.below_count}. Ad spend share of all royalties: {col:adsmonth.share_text}. Your limit is set on the Start sheet.'], ['Author-publisher', 'Accountant'], NOTE),
    DOC('stop_report_doc', 'Stop Hold Raise Report', 'Stop, hold or raise report for one campaign', 'rank.place', [
        'Stop, hold or raise report of {set:company}, dated {today}. Place {col:rank.place} on the list: {col:rank.campaign} on {col:rank.platform}, status {col:rank.status}.',
        'Last 60 days: spend {col:rank.spend_60}, royalties with page reads {col:rank.royalties_60}, profit {col:rank.profit_60}, return {col:rank.return_60}. The return target is {set:ad_return_target}.',
        'Verdict: {col:rank.verdict}. The daily budget is {col:rank.budget_day}; a stop frees {col:rank.freed} a day.',
        'Decision of the author: stop / hold / raise (circle one). Date of the next review: ____________.'], ['Author-publisher', 'Ad specialist'], NOTE),
    DOC('promo_plan_doc', 'Promotion Plan', 'Promotion plan', 'promos.promo_id', [
        'Promotion plan of {set:company}, dated {today}. Title: {col:promos.title}. Kind: {col:promos.kind}. Status: {col:promos.status}.',
        'From {col:promos.start_date} to {col:promos.end_date}, {col:promos.days} days. Normal price {col:promos.normal_price}, promotion price {col:promos.promo_price}. Planned cost {col:promos.cost}.',
        'Steps: the assistant changes the price on the start date and restores it on the end date, the web developer changes the direct store, and the newsletter partner {col:promos.partner} is asked to feature it.',
        'Copies sold in an equal period before the promotion: {col:promos.units_before}. The result is recorded in the Promotion Results sheet.'], ['Author-publisher', 'Assistant'], NOTE),
    DOC('promo_result_doc', 'Promotion Result Report', 'Promotion result report', 'promoresults.promo_id', [
        'Promotion result report of {set:company}, dated {today}. Title: {col:promoresults.title}. Kind: {col:promoresults.kind}. Start date: {col:promoresults.start_date}.',
        'Copies before {col:promoresults.units_before}, during {col:promoresults.units_during}, after {col:promoresults.units_after}. Extra copies: {col:promoresults.extra_copies}.',
        'Extra royalties from copies {col:promoresults.extra_royalties}, page-read income moved {col:promoresults.page_extra}, lasting lift after the promotion {col:promoresults.after_effect}, cost {col:promoresults.cost}.',
        'Net gain after cost: {col:promoresults.net_gain}. Payback in {col:promoresults.payback_days} days. Verdict: {col:promoresults.verdict}. These are estimates until the stores pay.'], ['Author-publisher'], NOTE),
    DOC('price_test_doc', 'Price Test Report', 'Price test report', 'pricecmp.test_id', [
        'Price test report of {set:company}, dated {today}. Title: {col:pricecmp.title}. Test {col:pricecmp.test_id}.',
        'Royalty a day at price A: {col:pricecmp.royalty_day_a}. At price B: {col:pricecmp.royalty_day_b}. Change of B against A: {col:pricecmp.change}.',
        'Price B needs {col:pricecmp.lift_needed} more copies to match A; it sold {col:pricecmp.lift_seen} more. The fewest copies in a period were {col:pricecmp.min_units}; a test needs at least {set:test_min_units}.',
        'Verdict: {col:pricecmp.verdict}. Decision of the author: ____________.'], ['Author-publisher'], NOTE),
    DOC('budget_plan_doc', 'Ad Budget Plan', 'Ad budget plan for a month', 'adsmonth.month', [
        'Ad budget plan of {set:company} for the month starting {col:adsmonth.month}, dated {today}.',
        'Monthly budget {col:adsmonth.budget}. Spend so far {col:adsmonth.spend}; spend this year up to this month {col:adsmonth.spend_year}.',
        'Your limit for ad spend is {set:ad_share_limit} of all royalties (your own number). All royalties of the month so far: {col:adsmonth.all_royalties}.',
        'Rule for the month: raise the campaigns that return {set:ad_raise_return} or more, stop the ones below {set:ad_return_target}, and keep the rest.'], ['Author-publisher', 'Ad specialist'], NOTE),
    DOC('platform_report_doc', 'Platform Comparison Report', 'Platform comparison report', 'adsplat.line_id', [
        'Platform comparison report of {set:company}, dated {today}. Platform: {col:adsplat.platform}. Month starting {col:adsplat.month}.',
        'Spend {col:adsplat.spend}, clicks {col:adsplat.clicks}, sales {col:adsplat.sales}, royalties with page reads {col:adsplat.royalties}.',
        'Return {col:adsplat.return}, cost per click {col:adsplat.cpc}, cost per sale {col:adsplat.cps}. The return target is {set:ad_return_target}.',
        'Compare this line with the other platforms of the same month in the Ads by Platform and Month sheet before you move any budget.'], ['Author-publisher', 'Ad specialist'], NOTE),
    DOC('breakeven_doc', 'Break-Even Sheet for Ads', 'Break-even sheet for the ads of one edition', 'breakeven.edition_id', [
        'Break-even sheet for ads of {set:company}, dated {today}. Edition {col:breakeven.edition_id}: {col:breakeven.title}, {col:breakeven.format}, sold through {col:breakeven.store}.',
        'List price {col:breakeven.price}, unit cost {col:breakeven.unit_cost}, royalty share used {col:breakeven.share_used} (check each store\'s current terms). Royalty per copy after cost: {col:breakeven.royalty_per_copy}.',
        'Break-even: ads may take {col:breakeven.break_even_share} of the price, which is {col:breakeven.break_even_cps} for each sale. Your target is {col:breakeven.target_share} of the price, which is {col:breakeven.target_cps} for each sale.',
        'Verdict: {col:breakeven.verdict}. Page-read income, where the title is in a lending program, comes on top of the royalty.'], ['Author-publisher'], NOTE),
    DOC('specialist_brief_doc', 'Brief for the Ad Specialist', 'Brief for the ad specialist', 'campaigns.campaign_id', [
        'Brief of {set:company} for {col:campaigns.specialist}, dated {today}. Campaign: {col:campaigns.campaign} for {col:campaigns.title} on {col:campaigns.platform}.',
        'Daily budget {col:campaigns.daily_budget}. Bid per click {col:campaigns.bid}; please keep it at or under {col:campaigns.target_bid}, the target bid from the campaign\'s own numbers.',
        'Goal: a return of at least {set:ad_return_target} royalties for each unit of ad spend. Conversion floor: {set:conversion_floor} of clicks. Tell me at once if conversion falls below it, because the product page may be the problem and not the ad.',
        'Please send spend, clicks, sales and page reads every week, and tell me before you change a budget or a bid.'], ['Author-publisher', 'Ad specialist'], NOTE),
    DOC('partner_schedule_doc', 'Promotion Schedule for Partners', 'Promotion schedule for newsletter partners', 'promos.promo_id', [
        'Promotion schedule of {set:company} for {col:promos.partner}, dated {today}.',
        'Title: {col:promos.title}. Kind: {col:promos.kind}. The promotion runs from {col:promos.start_date} to {col:promos.end_date}. The promotion price is {col:promos.promo_price}, the normal price {col:promos.normal_price}.',
        'We would be glad if you featured the book in your newsletter on the first day. Please tell us the day you choose and send us your link, and we will send the cover, the text and the store links.',
        'Thank you for your support. We help you keep your readers informed and do not promise any result.'], ['Author-publisher', 'Newsletter partner'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('new_campaign', 'New Campaign Steps', 'campaigns', 'campaigns.start_date', [('Pick the title and check its royalty per copy in the break-even sheet', -3), ('Set the daily budget and the bid under the target bid', -2), ('Write the ad text and choose the cover image', -2),
        ('Send the brief to the ad specialist', -1), ('Check the product page, price and conversion', -1), ('Start the campaign and write it in the Campaigns sheet', 0), ('Enter the first ad numbers', 1), ('Check the first weekly review', 7), ('Give the first verdict after the days you set', 14)]),
    CHK('weekly_review', 'Weekly Ad Review Steps', 'campaigns', 'campaigns.reviewed_on', [('Enter last week\'s ad numbers in the Ad Days sheet', 0), ('Read the Campaign Rank sheet from the top', 0), ('Stop, hold or raise each running campaign', 1),
        ('Check the conversion of each title', 1), ('Tell the ad specialist what changes', 1), ('Note the next review date', 2)]),
    CHK('raise_bid', 'Raising a Bid Steps', 'campaigns', 'campaigns.reviewed_on', [('Check the return of the last 60 days against your target', 0), ('Check the conversion against your floor', 0), ('Read the break-even and target bid', 0), ('Raise the bid in one small step', 1),
        ('Tell the ad specialist and note the date', 1), ('Check the return again after a week', 8), ('Undo the raise if the return falls below the target', 8)]),
    CHK('stop_campaign', 'Stopping a Campaign Steps', 'campaigns', 'campaigns.reviewed_on', [('Check the return of 30 and 60 days and the conversion', 0), ('Decide to stop and write the reason', 0), ('Tell the ad specialist or pause the campaign yourself', 0),
        ('Set the status to Paused or Ended and write the end date', 1), ('Ask for the final numbers', 2), ('Move the freed budget to the best campaign', 2), ('Write what you learned for the next campaign', 7)]),
    CHK('monthly_close', 'Monthly Ad Close Steps', 'adsmonth', 'adsmonth.month', [('Enter every missing ad day of the month', 31), ('Compare the spend with the monthly budget', 32), ('Read the return against last month and last year', 32), ('Send the ad spend to your accountant', 33),
        ('Check the ad share of all royalties', 33), ('Set the budget of the next month', 35), ('Write what changes next month', 36)]),
    CHK('plan_promo', 'Planning a Promotion Steps', 'promos', 'promos.start_date', [('Run the Promotion Fit Check for the title', -28), ('Choose the kind, the price and the days', -26), ('Book the newsletter partners and any promotion sites', -21), ('Tell the assistant the dates', -14),
        ('Tell the web developer about the direct store price', -14), ('Plan the ads that match the promotion', -10), ('Write the promotion in the Promotions sheet', -7)]),
    CHK('promo_day', 'Promotion Day Steps', 'promos', 'promos.start_date', [('Change the price in every store the day before if a store needs time', -1), ('Check the price on every store page', 0), ('Send the newsletter and post the offer', 0), ('Check the sales at the end of the day', 0),
        ('Check the price on the last day', 1), ('Restore the normal price on the end date', 4)]),
    CHK('after_promo', 'After a Promotion Steps', 'promos', 'promos.end_date', [('Restore the normal price in every store', 0), ('Enter the copies and page reads during the promotion', 1), ('Wait for the same number of days and enter the copies after', 7), ('Read the result in Promotion Results', 8),
        ('Thank the newsletter partners', 2), ('Write repeat, change or skip and the reason', 8)]),
    CHK('price_test_setup', 'Price Test Setup Steps', 'pricetests', 'pricetests.start_date', [('Choose one title and two prices', -3), ('Choose equal periods of at least two weeks', -3), ('Do not run a promotion or new ads at the same time', -2), ('Write the test in the Price Tests sheet', 0),
        ('Enter the copies at price A', 14), ('Change to price B', 14), ('Enter the copies at price B', 28), ('Read the Price Test Comparison sheet', 29)]),
    CHK('launch_ads', 'Launch Ad Plan Steps', 'titles', 'titles.release_date', [('Set the launch ad budget and the ramp', -28), ('Check the product page and the pre-order price', -21), ('Brief the ad specialist', -14), ('Start the ads before the release', -10),
        ('Check the cost per click every day', -3), ('Raise the budget on the release day if the return holds', 0), ('Review the return after the first week', 7), ('Move the budget to the campaigns that return most', 14)]),
    CHK('creative_refresh', 'Ad Creative Refresh Steps', 'campaigns', 'campaigns.reviewed_on', [('Check the return of the latest 4 weeks against the first 4 weeks', 0), ('Write what the reader sees: image, headline and text', 0), ('Ask the ad specialist for two new versions', 1),
        ('Run the new version beside the old one', 4), ('Compare the two after a week', 11), ('Keep the better one and stop the other', 12)]),
    CHK('platform_review', 'Quarterly Platform Review Steps', 'adsplat', 'adsplat.month', [('Read the return of each platform over 90 days', 95), ('Compare the cost per click and the cost per sale', 95), ('Run the Platform Comparison tool', 96), ('Decide how much budget to move', 97),
        ('Tell the ad specialist', 98), ('Write the decision in the notes', 98)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('s_setup', 'Ad specialist: set up a campaign', 'campaigns', 'campaigns.specialist_phone', 'Hello {specialist}, please set up a campaign for {title} on {platform} with {daily_budget} a day and a bid of {bid} per click. Thank you, {imprint}'),
    M('s_lower', 'Ad specialist: lower the bid', 'campaigns', 'campaigns.specialist_phone', 'Hello {specialist}, please lower the bid of {campaign} to {target_bid}. Its return is {return_text} of its spend. Thank you, {imprint}'),
    M('s_raise', 'Ad specialist: raise the budget', 'campaigns', 'campaigns.specialist_phone', 'Hello {specialist}, please raise the daily budget of {campaign} to {new_budget}. Thank you, {imprint}'),
    M('s_pause', 'Ad specialist: pause a campaign', 'campaigns', 'campaigns.specialist_phone', 'Hello {specialist}, please pause {campaign}. The return is {return_text} of its spend. Thank you, {imprint}'),
    M('s_weekly', 'Ad specialist: weekly report due', 'campaigns', 'campaigns.specialist_phone', 'Hello {specialist}, the weekly report for {campaign} is due. Please send spend, clicks, sales and page reads. Thank you, {imprint}'),
    M('s_launch', 'Ad specialist: launch ads', 'campaigns', 'campaigns.specialist_phone', 'Hello {specialist}, please prepare the launch ads for {title} on {platform}. Thank you, {imprint}'),
    M('s_conv', 'Ad specialist: conversion is low', 'conv', 'conv.specialist_phone', 'Hello {specialist}, the conversion of {title} is {conversion_text}. Please check the ad image and text. Thank you, {imprint}'),
    M('s_budget', 'Ad specialist: the budget of a month', 'adsmonth', 'adsmonth.specialist_phone', 'Hello {specialist}, the ad budget for {month} is {budget}. Please keep the campaigns within it. Thank you, {imprint}'),
    M('s_platform', 'Ad specialist: compare a platform', 'adsplat', 'adsplat.specialist_phone', 'Hello {specialist}, please compare {platform} with the other platforms for the month of {month}: spend, clicks and sales of each. Thank you, {imprint}'),
    M('s_ended', 'Ad specialist: final numbers', 'campaigns', 'campaigns.specialist_phone', 'Hello {specialist}, the campaign {campaign} ended on {end_date}. Please send the final numbers. Thank you, {imprint}'),
    M('a_enter', 'Assistant: enter the ad numbers', 'adsdays', 'adsdays.assistant_phone', 'Hello {assistant}, please enter the ad numbers for {date} in the Ad Days sheet. Thank you, {imprint}'),
    M('a_week', 'Assistant: enter last week\'s numbers', 'adsdays', 'adsdays.assistant_phone', 'Hello {assistant}, please enter last week\'s ad numbers, up to {date}. Thank you, {imprint}'),
    M('a_pause', 'Assistant: pause a campaign today', 'campaigns', 'campaigns.assistant_phone', 'Hello {assistant}, please pause {campaign} today and tell me when it is done. Thank you, {imprint}'),
    M('a_price', 'Assistant: change a price', 'promos', 'promos.assistant_phone', 'Hello {assistant}, please change the price of {title} to {promo_price} on {start_date}. Thank you, {imprint}'),
    M('a_restore', 'Assistant: restore a price', 'promos', 'promos.assistant_phone', 'Hello {assistant}, please restore the price of {title} to {normal_price} on {end_date}. Thank you, {imprint}'),
    M('a_book', 'Assistant: book a promotion', 'promos', 'promos.assistant_phone', 'Hello {assistant}, please book the {kind} of {title} for {start_date}. Thank you, {imprint}'),
    M('a_result', 'Assistant: record the promotion result', 'promos', 'promos.assistant_phone', 'Hello {assistant}, please record the promotion result of {title}: the copies before, during and after. Thank you, {imprint}'),
    M('a_ledger', 'Assistant: update the ad ledger', 'adsmonth', 'adsmonth.assistant_phone', 'Hello {assistant}, please update the ad ledger for {month}. Thank you, {imprint}'),
    M('p_feature', 'Newsletter partner: may we feature it', 'promos', 'promos.partner_phone', 'Hello {partner}, a promotion of {title} starts on {start_date}. May we ask you to feature it in your newsletter? Thank you, {imprint}'),
    M('p_thanks', 'Newsletter partner: thank you', 'promos', 'promos.partner_phone', 'Hello {partner}, thank you for featuring {title} in the promotion that started on {start_date}. Thank you, {imprint}'),
    M('p_price', 'Newsletter partner: the promotion price', 'promos', 'promos.partner_phone', 'Hello {partner}, the promotion price of {title} is {promo_price} until {end_date}. Thank you, {imprint}'),
    M('w_add', 'Web developer: add the promotion price', 'promos', 'promos.developer_phone', 'Hello {developer}, please add the promotion price of {promo_price} for {title} on the direct store from {start_date}. Thank you, {imprint}'),
    M('w_end', 'Web developer: end the promotion', 'promos', 'promos.developer_phone', 'Hello {developer}, please end the promotion of {title} on {end_date} and restore the price of {normal_price}. Thank you, {imprint}'),
    M('c_last', 'Accountant: ad spend of a month', 'adsmonth', 'adsmonth.accountant_phone', 'Hello {accountant}, ad spend in the month of {month} was {spend}. Thank you, {imprint}'),
    M('c_year', 'Accountant: ad spend this year', 'adsmonth', 'adsmonth.accountant_phone', 'Hello {accountant}, ad spend this year up to {month} is {spend_year}. Please confirm how to book it. Thank you, {imprint}'),
    M('o_stop', 'Author: stop or hold a campaign', 'campaigns', 'campaigns.owner_phone', 'Hello {owner}, {campaign} returns {return_text} of its spend. Stop it or hold it? {imprint}'),
    M('o_raise', 'Author: raise a campaign', 'campaigns', 'campaigns.owner_phone', 'Hello {owner}, {campaign} returns {return_text}. Raise its budget to {new_budget} a day? {imprint}'),
    M('o_conv', 'Author: fix the product page', 'conv', 'conv.owner_phone', 'Hello {owner}, {title} has a conversion of {conversion_text}. Fix the product page. {imprint}'),
    M('o_promo', 'Author: promotion result', 'promoresults', 'promoresults.owner_phone', 'Hello {owner}, the promotion of {title} gave {extra_copies} extra copies. {imprint}'),
    M('o_test', 'Author: price test ended', 'pricecmp', 'pricecmp.owner_phone', 'Hello {owner}, the price test of {title} ended. Verdict: {verdict}. {imprint}'),
    M('o_share', 'Author: ad share of royalties', 'adsmonth', 'adsmonth.owner_phone', 'Hello {owner}, ad spend is {share_text} of royalties in the month of {month}. {imprint}'),
    M('o_budget', 'Author: the ad budget of a month', 'adsmonth', 'adsmonth.owner_phone', 'Hello {owner}, your ad budget for {month} is {budget}. {imprint}'),
    M('o_start', 'Author: a promotion starts soon', 'promos', 'promos.owner_phone', 'Hello {owner}, a promotion of {title} starts in {days_to_start} days. {imprint}'),
    M('o_below', 'Author: campaigns below the target', 'adsmonth', 'adsmonth.owner_phone', 'Hello {owner}, {below_count} campaigns are below the return target. {imprint}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30), dashboard
def ADS(col, crit): return 'SUMIFS({range:adsdays.%s},%s)' % (col, crit)
MC = '{range:adsdays.month},%s' % MS
D30 = '{range:adsdays.date},">="&({today}-30)'; D365 = '{range:adsdays.date},">="&({today}-365)'
P365 = '{range:promos.start_date},">="&({today}-365),{range:promos.start_date},"<="&{today}'
R365 = '{range:promoresults.start_date},">="&({today}-365),{range:promoresults.start_date},"<="&{today}'
RBAD = {"when": "< {set:ad_return_target}", "style": "bad"}
kpis = [
    KPI('Ad spend this month', ADS('spend', MC), 'money'), KPI('Ad spend, last 30 days', ADS('spend', D30), 'money'), KPI('Ad spend, last 12 months', ADS('spend', D365), 'money'),
    KPI('Ad royalties this month', ADS('royalties', MC), 'money'), KPI('Ad royalties, last 30 days', ADS('royalties', D30), 'money'),
    KPI('Return this month', 'IFERROR(%s/%s,0)' % (ADS('royalties', MC), ADS('spend', MC)), 'num', alert=RBAD), KPI('Return, last 30 days', 'IFERROR(%s/%s,0)' % (ADS('royalties', D30), ADS('spend', D30)), 'num', alert=RBAD),
    KPI('Return, last 12 months', 'IFERROR(%s/%s,0)' % (ADS('royalties', D365), ADS('spend', D365)), 'num', alert=RBAD),
    KPI('Ad profit this month', '%s-%s' % (ADS('royalties', MC), ADS('spend', MC)), 'money'), KPI('Ad profit, last 12 months', '%s-%s' % (ADS('royalties', D365), ADS('spend', D365)), 'money'),
    KPI('Clicks, last 30 days', ADS('clicks', D30), 'int'), KPI('Sales from ads, last 30 days', ADS('sales', D30), 'int'), KPI('Page reads from ads, last 30 days', ADS('page_reads', D30), 'int'),
    KPI('Average cost per click, 30 days', 'IFERROR(%s/%s,0)' % (ADS('spend', D30), ADS('clicks', D30)), 'money'), KPI('Cost per sale, last 30 days', 'IFERROR(%s/%s,0)' % (ADS('spend', D30), ADS('sales', D30)), 'money'),
    KPI('Conversion, last 30 days', 'IFERROR(%s/%s,0)' % (ADS('sales', D30), ADS('clicks', D30)), 'pct', alert={"when": "< {set:conversion_floor}", "style": "bad"}),
    KPI('Campaigns running', 'COUNTIFS({range:campaigns.status},%s)' % RUN, 'int'), KPI('Campaigns below the return target', 'SUM({range:ledger.below})', 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Campaigns to raise', 'COUNTIFS({range:ledger.verdict},%s)' % v('Raise'), 'int'), KPI('Spend below the target, 60 days', 'SUMIFS({range:ledger.spend_60},{range:ledger.below},1)', 'money'),
    KPI('Ad spend share of royalties, month', 'IFERROR(%s/(SUMIFS({range:salesmonth.royalties_home},{range:salesmonth.month},%s)+SUMIFS({range:salesmonth.page_income},{range:salesmonth.month},%s)),0)' % (ADS('spend', MC), MS, MS), 'pct',
        alert={"when": "> {set:ad_share_limit}", "style": "warn"}),
    KPI('Best running campaign return', 'MAX({range:ledger.running_return})', 'num'), KPI('Worst running campaign return', 'MIN({range:ledger.running_return})', 'num', alert=RBAD),
    KPI('Titles below the conversion floor', 'COUNTIFS({range:conv.below_floor},%s)' % YES, 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Titles with worse ads than last year', 'COUNTIFS({range:adscompare.change_year},"<0")', 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Promotions, last 12 months', 'COUNTIFS(%s)' % P365, 'int'), KPI('Promotions to repeat', 'COUNTIFS({range:promoresults.verdict},%s)' % v('Repeat'), 'int'),
    KPI('Extra copies, promotions 12 months', 'SUMIFS({range:promoresults.extra_copies},%s)' % R365, 'int'), KPI('Extra royalties, promotions 12 months', 'SUMIFS({range:promoresults.extra_total},%s)' % R365, 'money'),
    KPI('Promotion cost, last 12 months', 'SUMIFS({range:promos.cost},%s)' % P365, 'money'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Ads Dashboard", "kpis": kpis,
    "monthly": {"title": "Ad spend, royalties and profit by month", "date": "adsmonth.month", "series": [
        {"label": "Spend", "sum": "adsmonth.spend", "date": "adsmonth.month"}, {"label": "Royalties", "sum": "adsmonth.royalties", "date": "adsmonth.month"},
        {"label": "Profit", "sum": "adsmonth.profit", "date": "adsmonth.month"}]},
    "breakdowns": [{"title": "Ad spend by platform", "by": "adsplat.platform", "value": "adsplat.spend", "agg": "sum"}, {"title": "Campaigns by status", "by": "campaigns.status", "agg": "count"},
                   {"title": "Extra royalties by promotion kind", "by": "promoresults.kind", "value": "promoresults.extra_total", "agg": "sum"}, {"title": "Ad royalties by series", "by": "adstitle.series", "value": "adstitle.royalties", "agg": "sum"}]}
insights = {"filters": [{"label": "Platform", "list": "platform"}, {"label": "Series", "list": "series"}, {"label": "Promotion kind", "list": "pkind"}],
    "gauges": [
        {"title": "Running campaigns at the return target", "num": AGG('count', 'ledger', where=[('status', '=', RUN), ('return_60', '>=', '{set:ad_return_target}')]), "den": AGG('count', 'ledger', where=[('status', '=', RUN)])},
        {"title": "Titles at or above the conversion floor", "num": AGG('count', 'conv', where=[('clicks', '>', 0), ('below_floor', '=', '{list:yesno.no}')]), "den": AGG('count', 'conv', where=[('clicks', '>', 0)])},
        {"title": "Months with spend within the budget", "num": AGG('count', 'adsmonth', where=[('spend', '<=', '{set:ad_budget_month}')]), "den": AGG('count', 'adsmonth', where=[('spend', '>', 0)])},
        {"title": "Promotions that paid back", "num": AGG('count', 'promoresults', where=[('status', '=', DONE), ('net_gain', '>', 0)]), "den": AGG('count', 'promoresults', where=[('status', '=', DONE)])},
        {"title": "Spend on campaigns at the target", "num": AGG('sum', 'ledger', 'ledger.spend_60', where=[('status', '=', RUN), ('below', '=', 0)]), "den": AGG('sum', 'ledger', 'ledger.spend_60', where=[('status', '=', RUN)])},
        {"title": "Ad days with at least one sale", "num": AGG('count', 'adsdays', where=[('days', '=', 1), ('sales', '>', 0)]), "den": AGG('count', 'adsdays', where=[('days', '=', 1)])}],
    "charts": [
        CHART('Ad spend per month', 'column', 'month', [AGG('sum', 'adsmonth', 'adsmonth.spend', date='adsmonth.month', label='Spend')]),
        CHART('Ad royalties per month', 'column', 'month', [AGG('sum', 'adsmonth', 'adsmonth.royalties', date='adsmonth.month', label='Royalties')]),
        CHART('Ad profit per month', 'column', 'month', [AGG('sum', 'adsmonth', 'adsmonth.profit', date='adsmonth.month', label='Profit')]),
        CHART('Return per month', 'line', 'month', [AGG('avg', 'adsmonth', 'adsmonth.return', date='adsmonth.month', label='Return')]),
        CHART('Clicks per month', 'column', 'month', [AGG('sum', 'adsmonth', 'adsmonth.clicks', date='adsmonth.month', label='Clicks')]),
        CHART('Sales from ads per month', 'column', 'month', [AGG('sum', 'adsmonth', 'adsmonth.sales', date='adsmonth.month', label='Sales')]),
        CHART('Cost per click per month', 'line', 'month', [AGG('avg', 'adsmonth', 'adsmonth.cpc', date='adsmonth.month', label='Cost per click')]),
        CHART('Spend by platform', 'bar', 'adsplat.platform', [AGG('sum', 'adsplat', 'adsplat.spend', label='Spend')]),
        CHART('Royalties by platform', 'bar', 'adsplat.platform', [AGG('sum', 'adsplat', 'adsplat.royalties', label='Royalties')]),
        CHART('Return by platform', 'bar', 'adsplat.platform', [AGG('avg', 'adsplat', 'adsplat.return', label='Return')]),
        CHART('Spend by pen name', 'bar', 'adstitle.pen_name', [AGG('sum', 'adstitle', 'adstitle.spend', label='Spend')]),
        CHART('Royalties by series', 'bar', 'adstitle.series', [AGG('sum', 'adstitle', 'adstitle.royalties', label='Royalties')]),
        CHART('Return by series', 'bar', 'adstitle.series', [AGG('avg', 'adstitle', 'adstitle.return', where=[('spend', '>', 0)], label='Return')]),
        CHART('Campaigns by status', 'bar', 'campaigns.status', [AGG('count', 'campaigns', label='Campaigns')]),
        CHART('Campaigns by platform', 'bar', 'campaigns.platform', [AGG('count', 'campaigns', label='Campaigns')]),
        CHART('Promotions per month', 'column', 'month', [AGG('count', 'promos', date='promos.start_date', label='Promotions')]),
        CHART('Promotions by kind', 'bar', 'promos.kind', [AGG('count', 'promos', label='Promotions')]),
        CHART('Extra copies by promotion kind', 'bar', 'promoresults.kind', [AGG('sum', 'promoresults', 'promoresults.extra_copies', label='Extra copies')]),
        CHART('Promotion cost by kind', 'bar', 'promos.kind', [AGG('sum', 'promos', 'promos.cost', label='Cost')]),
        CHART('Conversion by series', 'bar', 'conv.series', [AGG('avg', 'conv', 'conv.conversion', where=[('clicks', '>', 0)], label='Conversion')]),
        CHART('Spend by series', 'bar', 'adstitle.series', [AGG('sum', 'adstitle', 'adstitle.spend', label='Spend')]),
        CHART('Page reads from ads per month', 'column', 'month', [AGG('sum', 'adsmonth', 'adsmonth.page_reads', date='adsmonth.month', label='Page reads')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

# ------------------------------------------------------------------ signature, competitors, guide, listing
signature = [
    {"name": "Break-even ad cost by edition", "why": "the royalty after cost for every edition and store, the share of the price ads may take and the highest cost per sale and per click, so a bid is never a guess", "where": "Break-Even Ad Cost Finder"},
    {"name": "Campaign rank: stop, hold or raise", "why": "every campaign ranked by its return over 60 days with a verdict and the budget a stop frees, the worst running campaign first", "where": "Campaign Rank"},
    {"name": "Stop, hold or raise ranker", "why": "change your own stop and raise limits and see how many campaigns move and how much daily budget is freed", "where": "Stop Hold Raise Ranker"},
    {"name": "Ad compare with your own history", "why": "this month against the 3 months before and the same month last year for every title, flagged when it goes beyond your limit", "where": "Ad Compare with Own History"},
    {"name": "Conversion check against your floor", "why": "clicks and sales of every title against your floor, the sales you would add at it and a verdict that separates a weak ad from a weak product page", "where": "Conversion Check"},
    {"name": "Promotion result with payback days", "why": "copies before, during and after, the extra royalties at the lower price, the page reads moved and a repeat, change or skip verdict", "where": "Promotion Result Tool"},
    {"name": "Promotion fit check from your own lift", "why": "a planned price drop tested against the lift of your own earlier promotions of the same title before you spend a cent", "where": "Promotion Fit Check"},
    {"name": "Price change break-even", "why": "the copy lift a new price needs to keep the same royalty, with a raise, hold or lower verdict at the change you expect", "where": "Price Change Break-Even"},
    {"name": "Ad budget allocator", "why": "one monthly budget split across the running campaigns by return, with a Base, Best and Worst scenario and the shift to make", "where": "Ad Budget Allocator"},
    {"name": "Page-read-aware return", "why": "the return per click with and without page reads for titles in a lending program, so a low copy return is not read as a loss", "where": "Page-Read-Aware Return"},
    {"name": "Price test verdict", "why": "two prices over equal periods compared on royalty a day, with keep A, keep B or test longer once the copies and the gap are big enough", "where": "Price Test Verdict"}]
competitors = [
    {"what": "free royalty tracking templates", "lacks": "record income but never match ad spend to the royalties it brought, so no return, no break-even bid and no stop verdict"},
    {"what": "store ad dashboards", "lacks": "show spend and clicks of one store only, never the page reads, other platforms, your own history or what a stop frees"},
    {"what": "generic budget spreadsheets", "lacks": "know categories and totals but not campaigns, conversion floors, price promotions or the royalty after print cost"},
    {"what": "single-sheet book launch plans", "lacks": "list dates for a launch but never ramp the launch ad budget, check the platform minimum or compare promotions"},
    {"what": "subscription store and ad dashboards", "lacks": "charge a monthly fee that rises with your income and cannot test a price change or a promotion against your own earlier results"}]
guide = [
    'Open Start and check the yellow settings: the return target, the raise level, the conversion floor, the monthly ad budget and the highest ad share of royalties. They are your own numbers.',
    'Check Titles, Editions, Stores and Platforms. They hold the prices, costs and royalty shares that every break-even figure reads (check each store\'s current terms).',
    'Write each ad campaign in Campaigns with its title, platform, budget and bid. Add a row to Campaign Ledger, Maximum Bid by Campaign and Campaign Rank for a new campaign.',
    'Enter the ad numbers every week in Ad Days: spend, clicks, sales, page reads and royalties. Everything else fills in by itself.',
    'Read Campaign Rank from the top: the verdict says stop, hold or raise, and the budget a stop would free.',
    'Use Break-Even by Edition and Maximum Bid by Campaign to set a bid under the highest cost per click that still meets your return.',
    'Read Ad Compare with Own History and Conversion by Title each month: a fall beyond your limit or a conversion under your floor says where to look first.',
    'Write each price promotion in Promotions with the copies before, during and after (equal periods). Promotion Results shows the extra royalties, the payback days and a repeat, change or skip verdict.',
    'Test a price in Price Tests with equal periods. Price Test Comparison keeps A, keeps B or says test longer.',
    'Fill Sales by Title and Month with your monthly totals so the ad share of royalties can be worked out. Figures from stores are estimates until the payment arrives.',
    f'Use the {len(tools)} tools to find a break-even bid, rank campaigns, split a budget, plan a launch ramp, test a promotion or a price and forecast the next 3 months.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a ready text to the ad specialist, the assistant or a partner.',
    'Read the Ads Dashboard and the Charts every week. A first-time author with one campaign and one promotion a quarter uses the same sheets with a few rows; a small press reads the pen-name columns as author columns.']
listing = {"title": "Author Ads and Price Promotion Tracker Excel Template: Return on Ad Spend, Break-Even Bid, Campaign Ledger, Promotion Results",
    "headline": "Know which book ad to stop, hold or raise, and which promotion to repeat",
    "tags": ["author ads tracker", "book ad spend", "royalty tracker", "excel template", "self publishing", "book marketing", "price promotion", "ad return", "roas tracker", "author business", "indie author", "break even bid", "book launch"],
    "description": ("Run the advertising and price promotion side of an author or self-publisher business in one Excel workbook. Built for an independent author, a virtual assistant and the ad specialist who run campaigns on store ads, social ads and search ads and plan price promotions. "
        "Campaigns and Ad Days hold every campaign, its budget, its bid and the daily spend, clicks, sales, page reads and royalties. Campaign Ledger turns them into conversion, cost per sale, profit and the return on ad spend (royalties for every unit of spend), and Campaign Rank lists the worst running campaign first with a stop, hold or raise verdict and the budget a stop would free.\n\n"
        "Break-Even by Edition and Maximum Bid by Campaign work out the royalty after cost and the highest bid per click that still meets your target. Ad Compare with Own History sets this month against the 3 months before and the same month last year, and Conversion by Title checks every title against your conversion floor. "
        "Promotions and Promotion Results show copies before, during and after, the extra royalties at the lower price, the page-read income moved, the payback days and a repeat, change or skip verdict. Price Tests and Price Test Comparison keep price A or price B.\n\n"
        f"{len(tools)} tools cover the break-even ad cost, the stop, hold or raise ranker, campaign profit and loss, conversion, daily budget, cost per click ceiling, promotion result and fit, price change break-even, platform comparison, budget allocation, launch ad ramp, a 3-month forecast, ad share of income, page-read-aware return and campaign age. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to the ad specialist, the assistant, newsletter partners, the web developer and the accountant.\n\n"
        "This is part four of the Author and Self-Publisher Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Every target is your own number. It helps you keep track of your ads and does not promise income or sales; figures from stores are estimates until the payment arrives, and each store's current terms apply."),
    "features": ["Return on ad spend by campaign, title and platform", "Stop, hold or raise rank with the budget freed", "Break-even bid by edition and store", "Ad compare with your own history", "Conversion check against your floor",
                 "Promotion results with payback days", "Price tests and price change break-even", f"{len(tools)} tools for ad and price decisions", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "Works in Excel and Google Sheets, no macros"]}
HINTS = {
 'adsdays': 'One row per campaign and day of ad numbers (older ended campaigns are kept as one row per week part, Days in row says how many); campaign, title, platform, month, profit and cost per click fill in.',
 'promos': 'One row per price promotion: title, kind, dates, prices, cost and the copies and page reads before, during and after (equal periods); the days to start and the message fields fill in by themselves.',
 'breakeven': 'One row per edition and store: the royalty per copy after cost, the share of the price ads may take at break-even and at your target, and the highest cost per sale; everything fills in by itself.',
 'ledger': 'One row per campaign: spend, clicks, sales, royalties, conversion, cost per sale, profit and return for its whole run and for 30 and 60 days, with the stop, hold or raise verdict; all calculated.',
 'rank': 'Places 1 to 30 list running campaigns from the lowest return of the last 60 days to the highest, then paused and ended ones, with the verdict and the budget a stop would free.',
 'adsmonth': 'One row per month: spend, clicks, sales, page reads, royalties, profit, return, cost per click and the share of all royalties that went to ads; everything fills in by itself.',
 'adscompare': 'One row per title: the return of this month against the 3 months before and the same month last year, the change and a flag beyond your limit; everything fills in by itself.',
 'promoresults': 'One row per promotion: extra copies, extra royalties at the lower price, page reads moved, lasting lift, net gain after cost, payback days and a repeat, change or skip verdict.',
 'budget_solver': 'Type the sales a day you want, your conversion, cost per click and royalty per sale: the daily and monthly budget needed, the return it implies and whether it fits your ad share.',
 'promo_result': 'Type the copies before, during and after (equal periods), both prices and the cost: extra copies, extra royalties, page reads moved, lasting lift, payback days and a repeat, change or skip verdict.',
 'promo_fit': 'Pick a title and type the planned price, cost and normal copies: your own earlier promotions of the title give the lift, and the verdict says run, change the price or skip.',
 'ramp': 'Type the release date, the launch budget and the shares before and on the release day: the first and last daily budget on each side, the dates and whether the platform minimum is covered.'}
for _t in tables + tools:
    if _t['key'] in HINTS: _t['hint'] = HINTS[_t['key']]
s = spec(id=f'{SUITE}-p4', slug='author-publisher-ads', profession='Author and Self-Publisher Business', name='Ads and Price Promotions',
         tagline='Know which ad to stop, hold or raise and which promotion pays back', price_usd=29,
         colors={"primary": "#2B3A55", "accent": "#CE7777"}, settings=settings, lists=build_lists(), tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 4, "of": 8, "focus": "Ads and price promotions: return on ad spend, stop, hold or raise, promotion results and price tests"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'au4.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'lists', len(s['lists']))
