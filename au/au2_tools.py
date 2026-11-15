"""Author and Self-Publisher suite, part 2: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au2_lists import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
PAID = tok('cpaystatus', 'Paid'); JPAID = tok('jstatus', 'Paid')
F_EB = tok('format', 'Ebook'); F_AU = tok('format', 'Audiobook'); F_LP = tok('format', 'Large print'); F_HC = tok('format', 'Hardcover')
RELEASED = tok('tstatus', 'Released')
PB_, ONT, BEH, NOS = ca('Paid back'), ca('On track'), ca('Behind'), ca('Not on sale yet')
CASHNOW = 'SUMIFS({range:cash_month.closing},{range:cash_month.month},%s)' % MS
TITLE_DEF = "The Glassmaker's Orchard"
tools = []


def PBX(col, d='0'): return 'IFERROR(INDEX({range:payback.%s},MATCH({in:title},{range:payback.title},0)),%s)' % (col, d)
def TLX(col, d='0'): return 'IFERROR(INDEX({range:titles.%s},MATCH({in:title},{range:titles.title},0)),%s)' % (col, d)
def OWNAVG(kind_expr): return 'IFERROR(SUMIFS({range:jobs.quote},{range:jobs.kind},%s,{range:jobs.units},">0")/SUMIFS({range:jobs.units},{range:jobs.kind},%s),0)' % (kind_expr, kind_expr)


# 1 ------------------------------------------------------------ title payback verdict
GAP = PBX('gap'); AVG2 = '(%s*(1+{in:chg}))' % PBX('avg_monthly'); MON = 'IF(%s<=0,0,IF(%s>0,ROUND(%s/%s,1),""))' % (GAP, AVG2, GAP, AVG2)
tools.append(TOOL('payback_verdict', 'Title Payback Verdict', 'Has this title earned back its cost',
    'Pick a title and a sales change: cost, royalties to date, your own monthly average and the months still needed; see paid back, on track or behind and the format that drags the title.', [
    IL('title', 'Title', 'title', TITLE_DEF), I('chg', 'Sales change from your own average', 0.0, 'pct')], [
    O('Production cost', 'money', PBX('cost')), O('Royalties to date', 'money', PBX('to_date')), O('Still to earn back', 'money', GAP), O('Share earned back', 'pct', PBX('pct_back')),
    O('Months on sale', 'int', PBX('months_on_sale')), O('Own monthly average, last 6 months', 'money', PBX('avg_monthly')), O('Monthly average with the sales change', 'money', AVG2),
    O('Months still needed at that pace', 'num', MON),
    O('Status of the title', 'text', PBX('status', '""')),
    O('Format that drags the title', 'text', PBX('drag_format', '""')), O('Royalties minus cost of that format', 'money', PBX('drag_net')),
    O('Verdict', 'text', 'IF(%s<=0,%s,IF(%s<=0,%s,IF(%s+%s<={set:payback_target_months},%s,%s)))' % (GAP, PB_, AVG2, NOS, PBX('months_on_sale'), MON, ONT, BEH))],
    GR('What if', ('Sales down 20%', {'chg': -0.2}), ('Sales down 10%', {'chg': -0.1}), ('Sales up 10%', {'chg': 0.1}), ('Sales up 25%', {'chg': 0.25}), ('Sales double', {'chg': 1.0}),
       ('Crown of Last Embers', {'title': '=' + tok('title', 'Crown of Last Embers')}), ('The Tidebound Cartographer', {'title': '=' + tok('title', 'The Tidebound Cartographer')}))))

# 2 ------------------------------------------------------------ break-even copies solver
RPC = 'MAX(0,{in:price}*{in:share}-{in:ucost})'; BE = 'IF(%s>0,ROUNDUP({in:cost}/%s,0),"")' % (RPC, RPC)
STILL = 'IF(%s="","",MAX(0,%s-{in:sold}))' % (BE, BE); MLEFT = 'IF(OR(%s="",{in:pace}<=0),"",ROUND(%s/{in:pace},1))' % (STILL, STILL)
tools.append(TOOL('breakeven', 'Break-Even Copies Solver', 'How many copies does this edition need',
    'Type the cost allocated to an edition, its price, royalty share and sales so far: break-even copies, the months left at your pace, the pace and the price that pay it back in time.', [
    I('cost', 'Cost allocated to the edition', 5720), I('price', 'List price', 22.99, 'money'), I('share', 'Royalty share (check each store\'s current terms)', 0.40, 'pct'), I('ucost', 'Unit cost per copy', 0.0),
    I('sold', 'Copies sold so far', 10, 'int'), I('pace', 'Copies a month now', 2, 'int'), I('target', 'Months you allow to pay back', 24, 'int')], [
    O('Royalty per copy', 'money', RPC), O('Break-even copies', 'int', BE), O('Copies still needed', 'int', STILL), O('Months left at the pace', 'num', MLEFT),
    O('Cost still to earn', 'money', 'MAX(0,{in:cost}-{in:sold}*%s)' % RPC),
    O('Copies a month needed to pay back in time', 'num', 'IF(%s="","",ROUND(%s/{in:target},1))' % (STILL, STILL)),
    O('List price that pays back in time at this pace', 'money', 'IF(OR({in:share}<=0,{in:pace}<=0),"",ROUND(({in:ucost}+MAX(0,{in:cost}-{in:sold}*%s)/({in:pace}*{in:target}))/{in:share},2))' % RPC),
    O('Share of break-even reached', 'pct', 'IF(%s="","",{in:sold}/%s)' % (BE, BE)),
    O('Verdict', 'text', 'IF(%s="",%s,IF(%s=0,%s,IF(AND(%s<>"",%s<={in:target}),%s,%s)))' % (BE, BEH, STILL, PB_, MLEFT, MLEFT, ONT, BEH))],
    GR('What if', ('4 copies a month', {'pace': 4}), ('8 copies a month', {'pace': 8}), ('20 copies a month', {'pace': 20}), ('Price 14.99', {'price': 14.99}), ('Price 29.99', {'price': 29.99}),
       ('Print edition, price 13.99', {'cost': 3400, 'price': 13.99, 'share': 0.6, 'ucost': 5.2, 'sold': 180, 'pace': 14}))))

# 3 ------------------------------------------------------------ budget against actual ranker
RT = 'IFERROR(INDEX({range:cost_title.title_id},MATCH({in:rank},{range:cost_title.over_rank},0)),"")'
OVR = 'IFERROR(INDEX({range:cost_title.over_typical},MATCH({in:rank},{range:cost_title.over_rank},0)),0)'
TCOST = 'IFERROR(INDEX({range:cost_title.total},MATCH({in:rank},{range:cost_title.over_rank},0)),0)'
tools.append(TOOL('budget_ranker', 'Budget vs Actual Ranker', 'Which title ran furthest over your typical rates',
    'Titles are ranked by the amount their quotes ran over your typical rates; pick a rank to see the title, the item most over and whether to renegotiate the next quote.', [
    I('rank', 'Rank to show (1 is the most over)', 1, 'int'), I('tol', 'Over the typical rate that you accept', 0.10, 'pct')], [
    O('Title at this rank', 'text', 'IFERROR(INDEX({range:cost_title.title},MATCH({in:rank},{range:cost_title.over_rank},0))&"","")'), O('Production cost of the title', 'money', TCOST),
    O('Over (+) or under (-) your typical rates', 'money', OVR), O('Over or under as a share of the cost', 'pct', 'IF(%s>0,%s/%s,0)' % (TCOST, OVR, TCOST)),
    O('Item most over', 'text', 'IFERROR(INDEX({range:budget.kind},MATCH(%s&"|1",{range:budget.rank_key},0))&"","")' % RT),
    O('Amount that item ran over', 'money', 'IFERROR(INDEX({range:budget.over_amount},MATCH(%s&"|1",{range:budget.rank_key},0)),0)' % RT),
    O('Total over your typical rates, all jobs', 'money', 'SUM({range:budget.over_only})'), O('Jobs quoted over the tolerance', 'int', 'COUNTIFS({range:budget.over_pct},">"&{in:tol})'),
    O('Verdict', 'text', 'IF(%s>{in:tol}*%s,%s,%s)' % (OVR, TCOST, c2('Renegotiate the next quote'), c2('Within budget')))],
    GR('What if', ('Rank 2', {'rank': 2}), ('Rank 3', {'rank': 3}), ('Rank 5', {'rank': 5}), ('Rank 10', {'rank': 10}), ('Accept 25% over', {'tol': 0.25}), ('Accept 5% over', {'tol': 0.05}))))

# 4 ------------------------------------------------------------ contractor invoice cash test
OPEN = '{range:jobpay.status},"<>"&%s,{range:jobpay.date},"<="&({today}+{in:days})' % PAID
DUE_AMT = 'SUMIFS({range:jobpay.amount},%s)' % OPEN
LARGE = 'SUMPRODUCT(MAX(({range:jobpay.status}<>%s)*({range:jobpay.date}<={today}+{in:days})*{range:jobpay.amount}))' % PAID
AFTER = '(%s-%s-{in:other})' % (CASHNOW, DUE_AMT)
SHORT = 'MAX(0,{in:floor}-%s)' % AFTER
tools.append(TOOL('invoice_cash', 'Invoice Cash Test', 'Can I pay the invoices that fall due and keep my cash floor',
    'Type the days ahead and any other cash out: the invoices due, the cash after paying them against your floor, and whether to pay on the due date, ask a contractor to split or hold the next job.', [
    I('days', 'Days ahead to test', 3, 'int'), I('other', 'Other cash out in that time', 0.0), I('floor', 'Lowest cash balance you want to keep', CASH_FLOOR)], [
    O('Cash now', 'money', CASHNOW), O('Invoices due in that time', 'int', 'COUNTIFS(%s)' % OPEN), O('Amount due', 'money', DUE_AMT), O('Largest invoice', 'money', LARGE),
    O('Contractor of the largest invoice', 'text', 'IFERROR(INDEX({range:due.contractor},MATCH(%s,{range:due.amount},0))&"","")' % LARGE),
    O('Cash after paying them all', 'money', AFTER), O('Cash after paying the largest invoice alone', 'money', '%s-%s-{in:other}' % (CASHNOW, LARGE)),
    O('Above (+) or below (-) the floor after paying all', 'money', '%s-{in:floor}' % AFTER), O('Amount to move to a later date', 'money', SHORT),
    O('Verdict', 'text', 'IF(%s>={in:floor},%s,IF(%s<=%s,%s,%s))' % (AFTER, c2('Pay on the due date'), SHORT, LARGE, c2('Ask to split'), c2('Hold the next job')))],
    GR('What if', ('Next 7 days', {'days': 7}), ('Next 14 days', {'days': 14}), ('Next 30 days', {'days': 30}), ('Next 3 days, 500 other cash out', {'other': 500}), ('Next 3 days, floor 5000', {'floor': 5000}),
       ('Next 7 days, floor 3000', {'days': 7, 'floor': 3000}))))

# 5 ------------------------------------------------------------ cost per finished hour and per 1,000 words
OA = OWNAVG('{in:kind}')
tools.append(TOOL('unit_cost', 'Unit Cost Test', 'Is this quote fair per 1,000 words or per finished hour',
    'Pick the kind of job and type the quote and its units (thousand words or finished hours): the cost per unit against your own average for that kind, the quote that matches the average and a verdict.', [
    IL('kind', 'Kind of job', 'jobkind', 'Narration'), I('quote', 'Quote', 5000), I('units', 'Units, thousand words or finished hours', 11, 'num')], [
    O('Cost per unit', 'money', 'IF({in:units}>0,ROUND({in:quote}/{in:units},2),0)'), O('Own average per unit for this kind', 'money', 'ROUND(%s,2)' % OA),
    O('Your typical rate for this kind', 'money', 'SUMIFS({range:cost_cat.rate},{range:cost_cat.kind},{in:kind})'),
    O('Difference from your own average', 'pct', 'IF(%s>0,({in:quote}/{in:units})/%s-1,0)' % (OA, OA)), O('Quote that matches your average', 'money', 'ROUND(%s*{in:units},0)' % OA),
    O('Quote above (+) or below (-) that', 'money', '{in:quote}-ROUND(%s*{in:units},0)' % OA), O('Jobs of this kind in your ledger', 'int', 'COUNTIFS({range:jobs.kind},{in:kind})'),
    O('Verdict', 'text', 'IF(%s<=0,%s,IF(({in:quote}/{in:units})/%s-1>{set:unit_tolerance_pct},%s,IF(({in:quote}/{in:units})/%s-1<-{set:unit_tolerance_pct},%s,%s)))' % (OA, c2('Fair'), OA, c2('High'), OA, c2('Low'), c2('Fair')))],
    GR('What if', ('Copy edit, 98 units, 1,800', {'kind': '=' + tok('jobkind', 'Copy edit'), 'units': 98, 'quote': 1800}), ('Copy edit, 98 units, 2,600', {'kind': '=' + tok('jobkind', 'Copy edit'), 'units': 98, 'quote': 2600}),
       ('Narration, 11 hours, 3,300', {'quote': 3300}), ('Narration, 11 hours, 6,000', {'quote': 6000}), ('Translation, 90 units, 4,900', {'kind': '=' + tok('jobkind', 'Translation'), 'units': 90, 'quote': 4900}),
       ('Proofread, 90 units, 500', {'kind': '=' + tok('jobkind', 'Proofread'), 'units': 90, 'quote': 500}))))


# 6-8 ---------------------------------------------------------- go or no-go for a new format
def go_tool(k, sheet, title, hint, fmt_tok, fmt_name, ratio, inputs, cost_f, rpc_f, grid):
    EBM = 'SUMIFS({range:cost_edition.copies_month},{range:cost_edition.title},{in:title},{range:cost_edition.format},%s)' % F_EB
    def cp(f): return '%s*{in:ratio}*%s' % (EBM, f)
    def pay(f): return 'IF(%s*(%s)>0,ROUND((%s)/(%s*(%s)),1),"")' % (cp(f), rpc_f, cost_f, cp(f), rpc_f)
    mid = pay('1')
    hasf = 'has_' + {'Audiobook': 'audio', 'Large print': 'lp', 'Hardcover': 'hc'}[fmt_name]
    return TOOL(k, sheet, title, hint, [IL('title', 'Title', 'title', 'The Pale Bell Ringers')] + inputs + [I('ratio', 'Copies of the new format per ebook copy (your own number)', ratio, 'num'),
                                                                                                          I('low', 'Low case, share of the mid case', 0.5, 'num'), I('high', 'High case, share of the mid case', 1.6, 'num')], [
        O('Ebook copies a month for this title', 'num', EBM), O('One-off cost', 'money', cost_f), O('Royalty per copy', 'money', rpc_f),
        O('Copies a month, low', 'num', 'ROUND(%s*{in:low},1)' % cp('1')), O('Copies a month, mid', 'num', 'ROUND(%s,1)' % cp('1')), O('Copies a month, high', 'num', 'ROUND(%s*{in:high},1)' % cp('1')),
        O('Payback months, low', 'num', pay('{in:low}')), O('Payback months, mid', 'num', mid), O('Payback months, high', 'num', pay('{in:high}')),
        O('Royalties a month, mid', 'money', 'ROUND(%s*(%s),0)' % (cp('1'), rpc_f)),
        O('Own ratio today (this format per ebook copy)', 'num', 'IFERROR(ROUND(SUMIFS({range:cost_edition.copies_month},{range:cost_edition.format},%s,{range:cost_edition.%s},1)/SUMIFS({range:cost_edition.copies_month},{range:cost_edition.format},%s,{range:cost_edition.%s},1),3),0)' % (fmt_tok, hasf, F_EB, hasf)),
        O('Verdict', 'text', 'IF(%s="",%s,IF(%s<={set:go_payback_months},%s,IF(%s<={set:stretch_months},%s,%s)))' % (mid, ca('Skip'), mid, ca('Produce'), mid, ca('Wait'), ca('Skip')))], grid)


tools.append(go_tool('audio_go', 'Audio Go or No-go', 'Should this title become an audiobook',
    'Pick a title and type the narration rate and the audiobook price: the finished hours, the cost, the copies a month from the title\'s own ebook sales and the payback in low, mid and high cases.',
    F_AU, 'Audiobook', 0.09, [I('rate', 'Narration rate per finished hour', 285.0), I('extra', 'Extra cost (sample, mastering, setup)', 150.0), I('price', 'Audiobook price', 17.99), I('share', 'Royalty share (check each store\'s current terms)', 0.40, 'pct')],
    'ROUND({in:rate}*IFERROR(INDEX({range:titles.words},MATCH({in:title},{range:titles.title},0)),0)/9300+{in:extra},0)', '({in:price}*{in:share})',
    GR('What if', ('A cheaper narrator, 200 an hour', {'rate': 200}), ('A top narrator, 450 an hour', {'rate': 450}), ('Price 22.99', {'price': 22.99}), ('Ratio 0.05', {'ratio': 0.05}), ('Ratio 0.14', {'ratio': 0.14}),
       ('Salt Pier Letter', {'title': '=' + tok('title', 'The Salt Pier Letter')}))))
tools.append(go_tool('lp_go', 'Large Print Go or No-go', 'Should this title get a large print edition',
    'Pick a title and type the formatting, setup, price and print cost: the cost, the copies a month from the title\'s own ebook sales and the payback in low, mid and high cases.',
    F_LP, 'Large print', 0.05, [I('format_cost', 'Formatting and cover wrap cost', 240.0), I('setup', 'Setup and proof copy', 60.0), I('price', 'List price', 17.99), I('share', 'Royalty share (check each store\'s current terms)', 0.60, 'pct'),
                                I('ucost', 'Print cost per copy', 5.4)],
    '({in:format_cost}+{in:setup})', '({in:price}*{in:share}-{in:ucost})',
    GR('What if', ('Price 19.99', {'price': 19.99}), ('Price 15.99', {'price': 15.99}), ('Ratio 0.03', {'ratio': 0.03}), ('Ratio 0.08', {'ratio': 0.08}), ('Cost doubles', {'format_cost': 480, 'setup': 120}),
       ('Salt Pier Letter', {'title': '=' + tok('title', 'The Salt Pier Letter')}))))
tools.append(go_tool('hc_go', 'Hardcover Go or No-go', 'Should this title get a hardcover edition',
    'Pick a title and type the set-up, price and print cost: the cost, the copies a month from the title\'s own ebook sales and the payback in low, mid and high cases.',
    F_HC, 'Hardcover', 0.035, [I('format_cost', 'Formatting and cover wrap cost', 260.0), I('setup', 'Setup and proof copy', 80.0), I('price', 'List price', 24.99), I('share', 'Royalty share (check each store\'s current terms)', 0.60, 'pct'),
                               I('ucost', 'Print cost per copy', 11.0)],
    '({in:format_cost}+{in:setup})', '({in:price}*{in:share}-{in:ucost})',
    GR('What if', ('Price 27.99', {'price': 27.99}), ('Price 21.99', {'price': 21.99}), ('Ratio 0.02', {'ratio': 0.02}), ('Ratio 0.06', {'ratio': 0.06}), ('Cost doubles', {'format_cost': 520, 'setup': 160}),
       ('Salt Pier Letter', {'title': '=' + tok('title', 'The Salt Pier Letter')}))))

# 9 ------------------------------------------------------------ translation business case
WORDS = TLX('words')
TCOST_ = '({in:rate}*%s/1000+{in:edit}+{in:cover})' % WORDS; TRPC = '({in:price}*{in:share}-{in:ucost})'
TPAY = lambda f: 'IF({in:copies}*%s*%s>0,ROUND(%s/({in:copies}*%s*%s),1),"")' % (f, TRPC, TCOST_, f, TRPC)
NETH = '({in:copies}*%s*{in:horizon}-%s)' % (TRPC, TCOST_)
tools.append(TOOL('translation_case', 'Translation Business Case', 'Translate this book, wait or sell the rights',
    'Pick a title and a language and type the rate, price and copies a month you expect: the cost, the payback in low, mid and high cases and what the same book gives if you sell the rights instead.', [
    IL('title', 'Title', 'title', 'The Salt Pier Letter'), IL('language', 'Language', 'language', 'German'), I('rate', 'Translation rate per 1,000 words', 55.0), I('edit', 'Edit and proofread cost', 380.0), I('cover', 'Cover cost', 260.0),
    I('price', 'Ebook price', 5.99), I('share', 'Royalty share (check each store\'s current terms)', 0.70, 'pct'), I('ucost', 'Delivery cost per copy', 0.12), I('copies', 'Copies a month you expect (mid case)', 40, 'int'),
    I('horizon', 'Months you look ahead', 24, 'int'), I('fee', 'Fee offered for the rights', 1800.0)], [
    O('Words in the book', 'int', WORDS), O('Translation cost', 'money', '{in:rate}*%s/1000' % WORDS), O('Total cost with edit and cover', 'money', TCOST_), O('Royalty per copy', 'money', TRPC),
    O('Payback months, low (half the copies)', 'num', TPAY('0.5')), O('Payback months, mid', 'num', TPAY('1')), O('Payback months, high (1.6 times the copies)', 'num', TPAY('1.6')),
    O('Net after the months you look ahead, mid', 'money', NETH), O('Fee offered for the rights', 'money', '{in:fee}'), O('Cases on file for this title and language', 'int', 'COUNTIFS({range:translation.title},{in:title},{range:translation.language},{in:language})'),
    O('Verdict', 'text', 'IF(%s<={in:fee},%s,IF(AND(%s<>"",%s<={set:translate_go_months}),%s,%s))' % (NETH, ca('Sell the rights instead'), TPAY('1'), TPAY('1'), ca('Translate'), ca('Wait')))],
    GR('What if', ('Copies 80 a month', {'copies': 80}), ('Copies 120 a month', {'copies': 120}), ('Price 6.99', {'price': 6.99}), ('Cheaper translator, 45 per 1,000', {'rate': 45}), ('Fee 4000', {'fee': 4000}),
       ('Look ahead 48 months', {'horizon': 48}))))

# 10 ----------------------------------------------------------- translate or write the next book
SAVG = 'IFERROR(AVERAGEIFS({range:payback.avg_monthly},{range:payback.series},{in:series},{range:payback.status},%s),0)' % RELEASED
SCOST = 'IFERROR(AVERAGEIFS({range:titles.total_cost},{range:titles.series},{in:series},{range:titles.status},%s),0)' % RELEASED
TRY = 'ROUND(%s*{in:uplift},0)' % PBX('avg_monthly')
P_T = 'IF({in:tcost}>0,%s/({in:tcost}/1000),0)' % TRY; P_W = 'IF({in:wcost}>0,%s/({in:wcost}/1000),0)' % SAVG
tools.append(TOOL('translate_or_write', 'Translate or Write', 'Spend the next 1,000 on a translation or on a new book',
    'Pick the book you could translate and the series you could extend: the expected royalties a month per 1,000 spent on each option, from your own averages, and which to do first.', [
    IL('title', 'Book to translate', 'title', 'The Salt Pier Letter'), IL('series', 'Series for the new book', 'series', 'The Ember Crown'), I('tcost', 'Total cost to translate', 4930.0),
    I('uplift', 'Share of the original\'s royalties a translation earns', 0.30, 'pct'), I('wcost', 'Cost to produce the new book', 5200.0)], [
    O('Own monthly average of the book, last 6 months', 'money', PBX('avg_monthly')), O('Expected royalties a month, translation', 'money', TRY),
    O('Own average monthly royalties of a book in the series', 'money', 'ROUND(%s,0)' % SAVG), O('Own average cost of a book in the series', 'money', 'ROUND(%s,0)' % SCOST),
    O('Royalties a month per 1,000 spent, translation', 'money', 'ROUND(%s,1)' % P_T), O('Royalties a month per 1,000 spent, new book', 'money', 'ROUND(%s,1)' % P_W),
    O('Months to pay back, translation', 'num', 'IF(%s>0,ROUND({in:tcost}/%s,1),"")' % (TRY, TRY)), O('Months to pay back, new book', 'num', 'IF(%s>0,ROUND({in:wcost}/%s,1),"")' % (SAVG, SAVG)),
    O('Verdict', 'text', 'IF(%s>1.15*%s,%s,IF(%s>1.15*%s,%s,%s))' % (P_T, P_W, ca('Translate'), P_W, P_T, c2('Write'), c2('Both')))],
    GR('What if', ('Translation costs 3500', {'tcost': 3500}), ('Translation earns 50%', {'uplift': 0.5}), ('New book costs 3500', {'wcost': 3500}), ('New book costs 8000', {'wcost': 8000}),
       ('Translate The Orchard Key', {'title': '=' + tok('title', 'The Orchard Key'), 'tcost': 4600}), ('Extend Lantern Bay', {'series': '=' + tok('series', 'Lantern Bay Mysteries')}))))

# 11 ----------------------------------------------------------- deposit and milestone scheduler
D1 = '{in:start}'; D2 = '({in:start}+INT(({in:due}-{in:start})/2))'; D3 = '({in:due}+{in:delay})'
A1 = 'ROUND({in:quote}*{in:dep},2)'; A2 = 'ROUND({in:quote}*{in:mil},2)'; A3 = '({in:quote}-%s-%s)' % (A1, A2)
AVG6 = 'IFERROR(AVERAGEIFS({range:cash_month.closing},{range:cash_month.month},">="&EDATE(%s,-6),{range:cash_month.month},"<"&%s),0)' % (MS, MS)
def CASHAT(d): return 'IF(%s<={today}+30,%s-SUMIFS({range:jobpay.amount},{range:jobpay.status},"<>"&%s,{range:jobpay.date},"<="&%s),%s)' % (d, CASHNOW, PAID, d, AVG6)
CA1 = '(%s-%s)' % (CASHAT(D1), A1); CA2 = '(%s-%s-IF(%s<={today}+30,%s,0))' % (CASHAT(D2), A2, D2, A1); CA3 = '(%s-%s-IF(%s<={today}+30,%s+%s,0))' % (CASHAT(D3), A3, D3, A1, A2)
tools.append(TOOL('pay_scheduler', 'Payment Scheduler', 'When can I pay a job in stages and keep my cash floor',
    'Type the quote, the deposit and milestone shares and the dates: the amount and date of each payment and the cash left after it, from cash now (next 30 days) or your 6-month average.', [
    I('quote', 'Quote', 3200.0), I('dep', 'Deposit share', 0.25, 'pct'), I('mil', 'Milestone share', 0.35, 'pct'), I('start', 'Start date', 'today', 'date'), I('due', 'Due date of the work', 'today+75', 'date'),
    I('delay', 'Days after delivery that the final payment is due', 10, 'int')], [
    O('Deposit', 'money', A1), O('Deposit date', 'date', D1), O('Milestone payment', 'money', A2), O('Milestone date', 'date', D2), O('Final payment', 'money', A3), O('Final payment date', 'date', D3),
    O('Cash after the deposit', 'money', 'ROUND(%s,0)' % CA1), O('Cash after the milestone payment', 'money', 'ROUND(%s,0)' % CA2), O('Cash after the final payment', 'money', 'ROUND(%s,0)' % CA3),
    O('Lowest cash on the schedule', 'money', 'ROUND(MIN(%s,%s,%s),0)' % (CA1, CA2, CA3)), O('Own average cash, last 6 months', 'money', 'ROUND(%s,0)' % AVG6),
    O('Verdict', 'text', 'IF(MIN(%s,%s,%s)>={set:cash_floor},%s,%s)' % (CA1, CA2, CA3, c2('Schedule fits'), c2('Move a payment later')))],
    GR('What if', ('Deposit 40%, milestone 30%', {'dep': 0.4, 'mil': 0.3}), ('Deposit 50%, no milestone', {'dep': 0.5, 'mil': 0.0}), ('Start in 30 days', {'start': '={today}+30', 'due': '={today}+105'}),
       ('Start in 90 days', {'start': '={today}+90', 'due': '={today}+165'}), ('Quote 2000', {'quote': 2000}), ('Quote 9000', {'quote': 9000}))))

# 12 ----------------------------------------------------------- contractor concentration check
TOPV = 'MAX({range:contractors.share12})'
TOPN = 'IFERROR(INDEX({range:contractors.contractor},MATCH(%s,{range:contractors.share12},0))&"","")' % TOPV
TOPPAID = 'SUMIFS({range:contractors.paid_12m},{range:contractors.share12},%s)' % TOPV
tools.append(TOOL('concentration', 'Contractor Concentration', 'Am I relying on one contractor too much',
    'Type the share limit and a new job for the largest contractor: the shares of the three largest contractors in the last 12 months, the share after the new job and a verdict.', [
    I('limit', 'Largest share you accept for one contractor', 0.35, 'pct'), I('newjob', 'New job for the largest contractor', 0.0)], [
    O('Production paid, last 12 months', 'money', 'SUM({range:contractors.paid_12m})'), O('Contractors paid in 12 months', 'int', 'COUNTIFS({range:contractors.paid_12m},">0")'),
    O('Largest contractor', 'text', TOPN), O('Share of the largest', 'pct', TOPV), O('Second share', 'pct', 'LARGE({range:contractors.share12},2)'), O('Third share', 'pct', 'LARGE({range:contractors.share12},3)'),
    O('Share of the three largest together', 'pct', 'LARGE({range:contractors.share12},1)+LARGE({range:contractors.share12},2)+LARGE({range:contractors.share12},3)'),
    O('Share of the largest after the new job', 'pct', 'IF(SUM({range:contractors.paid_12m})+{in:newjob}>0,(%s+{in:newjob})/(SUM({range:contractors.paid_12m})+{in:newjob}),0)' % TOPPAID),
    O('Verdict', 'text', 'IF(IF(SUM({range:contractors.paid_12m})+{in:newjob}>0,(%s+{in:newjob})/(SUM({range:contractors.paid_12m})+{in:newjob}),0)>{in:limit},%s,%s)' % (TOPPAID, c2('Spread the work'), c2('Concentration is ok')))],
    GR('What if', ('Limit 30%', {'limit': 0.30}), ('Limit 50%', {'limit': 0.50}), ('A new job of 1000', {'newjob': 1000}), ('A new job of 3000', {'newjob': 3000}), ('A new job of 6000', {'newjob': 6000}))))

# 13 ----------------------------------------------------------- quote comparison
OAQ = 'IF(SUMIFS({range:jobs.units},{range:jobs.kind},{in:kind})>0,%s,IFERROR(AVERAGEIFS({range:jobs.quote},{range:jobs.kind},{in:kind}),0))' % OWNAVG('{in:kind}')
PU = lambda q: '(%s/{in:units})' % q
SC_ = lambda q, d: '({in:wt}*IF(%s>0,%s/%s,0)+(1-{in:wt})*MIN({in:da},{in:db},{in:dc})/%s)' % (PU(q), OAQ, PU(q), d)
tools.append(TOOL('quote_chooser', 'Quote Chooser', 'Which of three quotes should I accept',
    'Pick the kind of job and type up to three quotes with their days to deliver: the price per unit, the difference from your own average and a score that weighs price against speed.', [
    IL('kind', 'Kind of job', 'jobkind', 'Copy edit'), I('units', 'Units, thousand words or finished hours', 98, 'num'), I('qa', 'Quote A', 1830.0), I('da', 'Days to deliver A', 28, 'int'), I('qb', 'Quote B', 1990.0),
    I('db', 'Days to deliver B', 25, 'int'), I('qc', 'Quote C', 1760.0), I('dc', 'Days to deliver C', 45, 'int'), I('wt', 'Weight of price against speed', 0.7, 'pct')], [
    O('Own average per unit for this kind', 'money', 'ROUND(%s,2)' % OAQ), O('Price per unit, A', 'money', 'ROUND(%s,2)' % PU('{in:qa}')), O('Price per unit, B', 'money', 'ROUND(%s,2)' % PU('{in:qb}')),
    O('Price per unit, C', 'money', 'ROUND(%s,2)' % PU('{in:qc}')),
    O('A against your average', 'pct', 'IF(%s>0,%s/%s-1,0)' % (OAQ, PU('{in:qa}'), OAQ)), O('B against your average', 'pct', 'IF(%s>0,%s/%s-1,0)' % (OAQ, PU('{in:qb}'), OAQ)),
    O('C against your average', 'pct', 'IF(%s>0,%s/%s-1,0)' % (OAQ, PU('{in:qc}'), OAQ)),
    O('Score A', 'num', 'ROUND(%s,3)' % SC_('{in:qa}', '{in:da}')), O('Score B', 'num', 'ROUND(%s,3)' % SC_('{in:qb}', '{in:db}')), O('Score C', 'num', 'ROUND(%s,3)' % SC_('{in:qc}', '{in:dc}')),
    O('Verdict', 'text', 'IF(%s>=MAX(%s,%s),%s,IF(%s>=%s,%s,%s))' % (SC_('{in:qa}', '{in:da}'), SC_('{in:qb}', '{in:db}'), SC_('{in:qc}', '{in:dc}'), c2('Choose A'), SC_('{in:qb}', '{in:db}'), SC_('{in:qc}', '{in:dc}'), c2('Choose B'), c2('Choose C')))],
    GR('What if', ('Speed matters most, weight 30%', {'wt': 0.3}), ('Price only, weight 100%', {'wt': 1.0}), ('C in 20 days', {'dc': 20}), ('B drops to 1800', {'qb': 1800}),
       ('Narration, 10 hours', {'kind': '=' + tok('jobkind', 'Narration'), 'units': 10, 'qa': 2850, 'qb': 4650, 'qc': 3300, 'da': 60, 'db': 75, 'dc': 50}))))

# 14 ----------------------------------------------------------- late job impact
JSEL = '({range:jobs.title}={in:title})*({range:jobs.kind}={in:kind})'
J_DUE = 'SUMPRODUCT(MAX(%s*{range:jobs.due_date}))' % JSEL; J_DEL = 'SUMPRODUCT(MAX(%s*{range:jobs.delivered_on}))' % JSEL
J_LATE = 'IF(%s>0,MAX(0,%s-%s),MAX(0,{today}-%s))' % (J_DEL, J_DEL, J_DUE, J_DUE)
REL = TLX('release_date'); LASTJ = 'SUMPRODUCT(MAX(({range:jobs.title}={in:title})*{range:jobs.due_date}))'
MOVE = 'MAX(0,%s+{in:extra}-(%s-%s))' % (J_LATE, REL, LASTJ)
tools.append(TOOL('late_impact', 'Late Job Impact', 'Does this late job move my release date',
    'Pick a title and the late job and add days if it slips further: the jobs that follow, the days left between the last job and the release and whether the release date moves.', [
    IL('title', 'Title', 'title', 'The Kelp Throne'), IL('kind', 'Late job', 'jobkind', 'Copy edit'), I('extra', 'Further days it may slip', 0, 'int')], [
    O('Due date of the job', 'date', 'IF(%s>0,%s,"")' % (J_DUE, J_DUE)), O('Days late now', 'int', 'IF(%s>0,%s,0)' % (J_DUE, J_LATE)),
    O('Jobs of the title due after it', 'int', 'COUNTIFS({range:jobs.title},{in:title},{range:jobs.due_date},">"&%s)' % J_DUE), O('Release date', 'date', REL),
    O('Due date of the last job of the title', 'date', 'IF(%s>0,%s,"")' % (LASTJ, LASTJ)), O('Days between the last job and the release', 'int', 'IF(%s>0,%s-%s,0)' % (LASTJ, REL, LASTJ)),
    O('Total delay carried to the following jobs', 'int', '%s+{in:extra}' % J_LATE), O('Days the release must move', 'int', MOVE), O('New release date', 'date', '%s+%s' % (REL, MOVE)),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (MOVE, c2('Move the release'), c2('Absorb the delay')))],
    GR('What if', ('Slips 10 more days', {'extra': 10}), ('Slips 20 more days', {'extra': 20}), ('Slips 40 more days', {'extra': 40}), ('Slips 80 more days', {'extra': 80}),
       ('Crown of Last Embers, narration', {'title': '=' + tok('title', 'Crown of Last Embers'), 'kind': '=' + tok('jobkind', 'Narration')}))))

# 15 ----------------------------------------------------------- cost cap per title
OWNCOST = 'IFERROR(AVERAGEIFS({range:titles.total_cost},{range:titles.status},%s),0)' % RELEASED
OWNROY = 'IFERROR(AVERAGEIFS({range:payback.avg_monthly},{range:payback.status},%s),0)' % RELEASED
CAP = '({in:months}*{in:roy})'
tools.append(TOOL('cost_cap', 'Cost Cap per Title', 'What is the most I should spend on the next title',
    'Type the months you want for payback and the royalties a month you expect: the largest production budget, the copies a month a planned budget needs and your own averages for comparison.', [
    I('months', 'Months to pay back', 18, 'int'), I('roy', 'Expected royalties a month', 420.0), I('plan', 'Planned production budget', 5200.0), I('rpc', 'Royalty per copy, all formats', 3.4)], [
    O('Largest budget (months times royalties a month)', 'money', CAP), O('Planned budget over (+) or under (-) the cap', 'money', '{in:plan}-%s' % CAP),
    O('Copies a month needed to pay back the plan', 'num', 'IF({in:rpc}>0,ROUND({in:plan}/({in:months}*{in:rpc}),1),0)'), O('Royalties a month needed for the plan', 'money', 'IF({in:months}>0,ROUND({in:plan}/{in:months},0),0)'),
    O('Own average cost of a released title', 'money', 'ROUND(%s,0)' % OWNCOST), O('Own average monthly royalties of a released title', 'money', 'ROUND(%s,0)' % OWNROY),
    O('Months to pay back at your own average royalties', 'num', 'IF(%s>0,ROUND({in:plan}/%s,1),"")' % (OWNROY, OWNROY)),
    O('Verdict', 'text', 'IF({in:plan}<=%s,%s,%s)' % (CAP, c2('Within the cap'), c2('Over the cap')))],
    GR('What if', ('12 months', {'months': 12}), ('24 months', {'months': 24}), ('Royalties 300 a month', {'roy': 300}), ('Royalties 600 a month', {'roy': 600}), ('Plan 3500', {'plan': 3500}), ('Plan 8000', {'plan': 8000}))))

# 16 ----------------------------------------------------------- series budget planner
NEWM = '(%s*{in:left})' % SAVG; BUD = '({in:cost}*{in:left})'
tools.append(TOOL('series_budget', 'Series Budget Planner', 'Can I afford the books left in this series',
    'Pick a series and type the books left and the cost per book: the budget, the royalties a month the new books may earn from the series\' own history and the months to pay back.', [
    IL('series', 'Series', 'series', 'The Ember Crown'), I('left', 'Books still to produce', 2, 'int'), I('cost', 'Cost per book', 5200.0)], [
    O('Released books in the series', 'int', 'COUNTIFS({range:payback.series},{in:series},{range:payback.status},%s)' % RELEASED), O('Own average cost of a book in the series', 'money', 'ROUND(%s,0)' % SCOST),
    O('Own average monthly royalties of a book', 'money', 'ROUND(%s,0)' % SAVG), O('Budget for the books left', 'money', BUD), O('Expected royalties a month from the new books', 'money', 'ROUND(%s,0)' % NEWM),
    O('Months to pay back the budget', 'num', 'IF(%s>0,ROUND(%s/%s,1),"")' % (NEWM, BUD, NEWM)),
    O('Verdict', 'text', 'IF(%s<=0,%s,IF(%s/%s<={set:go_payback_months},%s,IF(%s/%s<={set:stretch_months},%s,%s)))' % (NEWM, c2('Too heavy'), BUD, NEWM, c2('Affordable'), BUD, NEWM, c2('Stretch'), c2('Too heavy')))],
    GR('What if', ('One book left', {'left': 1}), ('Three books left', {'left': 3}), ('Books cost 3500', {'cost': 3500}), ('Books cost 8000', {'cost': 8000}),
       ('Lantern Bay', {'series': '=' + tok('series', 'Lantern Bay Mysteries'), 'left': 1}), ('Tidebound Realms', {'series': '=' + tok('series', 'Tidebound Realms'), 'left': 1}))))

# 17 ----------------------------------------------------------- cover refresh test
CPM = 'SUMIFS({range:cost_edition.copies_month},{range:cost_edition.title},{in:title})'
BRPC = 'IFERROR(SUMIFS({range:cost_edition.royalties_earned},{range:cost_edition.title},{in:title})/SUMIFS({range:cost_edition.copies_sold},{range:cost_edition.title},{in:title}),0)'
XTRA = 'IF(%s>0,{in:cost}/({in:months}*%s),0)' % (BRPC, BRPC)
tools.append(TOOL('cover_refresh', 'Cover Refresh Test', 'Will a new cover pay for itself',
    'Pick a title and type the new cover cost: the extra copies a month a new cover must add to pay back in the months you choose, as a share of today\'s sales, against the lift you think is realistic.', [
    IL('title', 'Title', 'title', 'The Drowned Ledger'), I('cost', 'Cost of the new cover', 550.0), I('months', 'Months to pay back', 12, 'int'), I('maxlift', 'Lift in copies a new cover can give (your own number)', 0.15, 'pct')], [
    O('Copies a month now, all formats', 'num', 'ROUND(%s,1)' % CPM), O('Royalty per copy, all formats', 'money', 'ROUND(%s,2)' % BRPC), O('Extra copies a month needed', 'num', 'ROUND(%s,1)' % XTRA),
    O('Lift needed', 'pct', 'IF(%s>0,%s/%s,0)' % (CPM, XTRA, CPM)), O('Lift you think is realistic', 'pct', '{in:maxlift}'), O('Extra royalties a month needed', 'money', 'IF({in:months}>0,ROUND({in:cost}/{in:months},0),0)'),
    O('Cost of your last cover for this title', 'money', 'SUMIFS({range:jobs.quote},{range:jobs.title},{in:title},{range:jobs.kind},%s)' % tok('jobkind', 'Cover design')),
    O('Verdict', 'text', 'IF(AND(%s>0,%s/%s<={in:maxlift}),%s,%s)' % (CPM, XTRA, CPM, c2('Refresh the cover'), c2('Hold the cover')))],
    GR('What if', ('Cover costs 300', {'cost': 300}), ('Cover costs 900', {'cost': 900}), ('Pay back in 6 months', {'months': 6}), ('Pay back in 24 months', {'months': 24}), ('Expect a 30% lift', {'maxlift': 0.3}),
       ('The Salt Pier Letter', {'title': '=' + tok('title', 'The Salt Pier Letter')}))))

# 18 ----------------------------------------------------------- payback horizon what-if
def MSTEP(x): return 'IF(%s<=0,0,IF(%s>0,ROUND(%s/(%s*(1+%s)),1),""))' % (GAP, PBX('avg_monthly'), GAP, PBX('avg_monthly'), x)
def ONTIME(x): return 'IF(%s<=0,1,IF(%s>0,IF(%s+%s/(%s*(1+%s))<={in:target},1,0),0))' % (GAP, PBX('avg_monthly'), PBX('months_on_sale'), GAP, PBX('avg_monthly'), x)
tools.append(TOOL('horizon_whatif', 'Payback What-if', 'Does the payback hold if sales move 20 percent',
    'Pick a title: the months still needed with sales down 20 percent, down 10, as now, up 10 and up 20, and how many of your titles stay on track in the worst and best step.', [
    IL('title', 'Title', 'title', TITLE_DEF), I('target', 'Months a title should take to earn back its cost', 24, 'int')], [
    O('Still to earn back', 'money', GAP), O('Months on sale', 'int', PBX('months_on_sale')), O('Months still needed, sales down 20%', 'num', MSTEP('-0.2')), O('Months still needed, sales down 10%', 'num', MSTEP('-0.1')),
    O('Months still needed, sales as now', 'num', MSTEP('0')), O('Months still needed, sales up 10%', 'num', MSTEP('0.1')), O('Months still needed, sales up 20%', 'num', MSTEP('0.2')),
    O('Titles on track or paid back, sales down 20%', 'int', 'SUM({range:payback.ok_m20})'), O('Titles on track or paid back, sales as now', 'int', 'SUM({range:payback.ok_0})'),
    O('Titles on track or paid back, sales up 20%', 'int', 'SUM({range:payback.ok_p20})'),
    O('Verdict', 'text', 'IF(%s=1,%s,%s)' % (ONTIME('-0.2'), c2('Robust'), c2('Sensitive')))],
    GR('What if', ('Target 12 months', {'target': 12}), ('Target 36 months', {'target': 36}), ('Crown of Last Embers', {'title': '=' + tok('title', 'Crown of Last Embers')}),
       ('The Last Lamp Out', {'title': '=' + tok('title', 'The Last Lamp Out')}), ('Salt and Lantern Sky', {'title': '=' + tok('title', 'Salt and Lantern Sky')}))))
assert len(tools) == 18, len(tools)
