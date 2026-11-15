"""Author and self-publisher suite part 6: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au6_lists import *
from au6_tables import WIN, MS, REL, STEP1, KEEP, REPRICE, REPACK, RETIRE
import au6_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": vv} for l, vv in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
PN = [tok('penname', p) for p in PEN_NAMES]
def WN(r, a='{in:months}', b=None):
    """complete months from a months back up to (not including) b months back (this month when b is None)"""
    lo = 'EDATE(%s,-%s)' % (MS, a)
    hi = MS if b is None else 'EDATE(%s,-%s)' % (MS, b)
    return '{range:%s},">="&%s,{range:%s},"<"&%s' % (r, lo, r, hi)
def TI(col, t='title'): return 'IFERROR(INDEX({range:titles.%s},MATCH({in:%s},{range:titles.title},0)),0)' % (col, t)
def DC(col): return 'IFERROR(INDEX({range:decisions.%s},MATCH({in:title},{range:decisions.title},0)),"")' % col
def YT(col): return 'IFERROR(INDEX({range:ytest.%s},MATCH({in:title},{range:ytest.title},0)),"")' % col
def TR(col): return 'IFERROR(INDEX({range:trend.%s},MATCH({in:title},{range:trend.title},0)),"")' % col
def NZ(f): return 'IF(%s="",0,%s)' % (f, f)
def TOTAL_ROY(): return 'SUM({range:titles.royalties_12m})'
tools = []

# 1 ------------------------------------------------------------ series money case
def CHN(k, m):
    if k == 1: return '1'
    if k == 2: return '({in:rt1}*%s)' % m
    return '({in:rt1}*%s)*{in:rtl}^%d' % (m, k - 2)
def CPY(k, m='1'): return 'IF({in:books}>=%d,{in:b1}*%s*MAX(0,24-%d*{in:gap}),0)' % (k, CHN(k, m), k - 1)
def COPIES(m='1'): return '(' + '+'.join(CPY(k, m) for k in range(1, 7)) + ')'
def NET(k): return '(%s*{in:roy}-{in:cost_each})' % CPY(k)
def verdict_series():
    f = 'IF(AND({in:books}>=%d,%s<0),%s,IF({in:books}=%d,%s,%s))'
    out = v('Build the series')
    for k in range(6, 0, -1):
        if k == 1: stop = v('Do not start the series')
        else: stop = 'IF({in:books}=%d,%s,%s&" %d")' % (k, v('Stretch'), v('Stop at book'), k - 1)
        out = 'IF(AND({in:books}>=%d,%s<0),%s,%s)' % (k, NET(k), stop, out)
    return out
tools.append(TOOL('series_money', 'Series Money Case', 'Does this series earn its cost in 24 months',
    'Type the books planned, the cost of each, the gap between releases, the copies book 1 sells a month and your read-through (book 1 to 2, and each later step); see the copies and royalties of the series over 24 months, the cost, the payback and the book at which to stop. Up to 6 books; a forecast, not a promise.', [
    I('books', 'Books planned in the series (up to 6)', 5, 'int'), I('cost_each', 'Production cost of each book', 4200), I('gap', 'Months between releases', 3, 'int'), I('b1', 'Copies book 1 sells a month', 300, 'int'),
    I('rt1', 'Read-through, book 1 to book 2', 0.55, 'pct'), I('rtl', 'Read-through at each later step', 0.90, 'pct'), I('roy', 'Your royalty per copy', 3.0)], [
    O('Copies in 24 months', 'int', COPIES()), O('Royalties in 24 months', 'money', '%s*{in:roy}' % COPIES()), O('Production cost of the series', 'money', '{in:books}*{in:cost_each}'),
    O('Net after production cost', 'money', '%s*{in:roy}-{in:books}*{in:cost_each}' % COPIES()),
    O('Months to earn back the cost (average pace)', 'num', 'IF(%s>0,{in:books}*{in:cost_each}/(%s*{in:roy}/24),"")' % (COPIES(), COPIES())),
    O('Royalties, worst case (read-through 20% lower)', 'money', '%s*{in:roy}' % COPIES('0.8')), O('Royalties, best case (read-through 20% higher)', 'money', '%s*{in:roy}' % COPIES('1.2')),
    O('Net of book 1', 'money', NET(1)), O('Net of book 2', 'money', 'IF({in:books}>=2,%s,"")' % NET(2)), O('Net of book 3', 'money', 'IF({in:books}>=3,%s,"")' % NET(3)),
    O('Net of book 4', 'money', 'IF({in:books}>=4,%s,"")' % NET(4)), O('Net of book 5', 'money', 'IF({in:books}>=5,%s,"")' % NET(5)),
    O('Verdict', 'text', verdict_series())],
    GR('What if', ('Read-through only 25 percent', {'rt1': 0.25}), ('Releases 6 months apart', {'gap': 6}), ('Each book costs 6,000', {'cost_each': 6000}), ('Book 1 sells only 150 a month', {'b1': 150}),
       ('Royalty per copy 2.00', {'roy': 2.0}))))

# 2 ------------------------------------------------------------ books to reach a target income
NOWI = '(%s/12)' % TOTAL_ROY()
GAPI = 'MAX(0,{in:target}-%s)' % NOWI
PERB = '({in:a_new}*(1+{in:lift}))'
NB = 'IF(%s<=0,0,ROUNDUP(%s/%s,0))' % (GAPI, GAPI, PERB)
tools.append(TOOL('target_books', 'Books to Reach a Target', 'How many more books reach my target income',
    'Type the royalties you want each month, what a new book brings and the lift it gives earlier books; the royalties of your last 12 months are read from Titles. See the books needed, the months at your pace and the date.', [
    I('target', 'Royalties you want each month', 14000), I('a_new', 'Royalties a new book brings each month (your own number)', 540), I('lift', 'Lift a new book gives earlier books', 0.05, 'pct'),
    I('pace', 'Books you publish in a year', 2, 'int'), I('cap', 'Most books you accept to write for the target', 8, 'int')], [
    O('Royalties a month now (last 12 months)', 'money', NOWI), O('Gap to the target', 'money', GAPI), O('Added by one new book (with the lift)', 'money', PERB),
    O('Books needed', 'int', NB), O('Months at your pace', 'num', '%s/MAX(1,{in:pace})*12' % NB), O('Target reached by', 'date', 'EDATE({today},ROUNDUP(%s/MAX(1,{in:pace})*12,0))' % NB),
    O('Income after 1 new book', 'money', '%s+%s' % (NOWI, PERB)), O('Income after 2 new books', 'money', '%s+2*%s' % (NOWI, PERB)), O('Income after 3 new books', 'money', '%s+3*%s' % (NOWI, PERB)),
    O('Verdict', 'text', 'IF(%s<=0,%s,IF(%s<={in:cap},%s&" "&%s,%s))' % (GAPI, v('Target reached'), NB, NB, v('more books at this pace'), v('Target is far')))],
    GR('What if', ('Target 18,000 a month', {'target': 18000}), ('Four books a year', {'pace': 4}), ('New books bring 400', {'a_new': 400}), ('No lift on earlier books', {'lift': 0.0}), ('Target 12,000 a month', {'target': 12000}))))

# 3 ------------------------------------------------------------ read-through by step
def RS(col): return 'SUMIFS({range:rtstep.%s},{range:rtstep.series},{in:series},{range:rtstep.stepno},{in:stepno})' % col
tools.append(TOOL('rt_tool', 'Step Read-through Verdict', 'Is this step of the series healthy',
    'Pick a series and a step; see the copies of book n and book n+1 of the last 12 months, the read-through against your threshold, the copies and royalties you would gain by closing part of the gap, and a verdict that names the step.', [
    IL('series', 'Series', 'series4', 'Tidebound Realms'), IL('stepno', 'Step', 'bstep', 'Step 1'), I('close', 'Share of the gap you can close', 0.5, 'pct')], [
    O('Copies of book n', 'int', RS('copies_from')), O('Copies of book n+1', 'int', RS('copies_to')), O('Read-through', 'pct', 'IF(%s>0,%s/%s,0)' % (RS('copies_from'), RS('copies_to'), RS('copies_from'))),
    O('Your threshold for this step', 'pct', RS('threshold')), O('Copies at your threshold', 'int', 'ROUND(%s*%s,0)' % (RS('copies_from'), RS('threshold'))),
    O('Copies short of the threshold', 'int', 'MAX(0,ROUND(%s*%s-%s,0))' % (RS('copies_from'), RS('threshold'), RS('copies_to'))),
    O('Extra copies if you close part of the gap', 'int', 'ROUND(MAX(0,%s*%s-%s)*{in:close},0)' % (RS('copies_from'), RS('threshold'), RS('copies_to'))),
    O('Royalties those copies bring in a year', 'money', 'MAX(0,%s*%s-%s)*{in:close}*%s' % (RS('copies_from'), RS('threshold'), RS('copies_to'), RS('royalty_copy'))),
    O('Steps below the threshold in this series', 'int', 'COUNTIFS({range:rtstep.series},{in:series},{range:rtstep.flag},%s)' % v('Below the threshold')),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s>=%s,%s,IF({in:stepno}=%s,%s,%s))&" ("&{in:series}&", "&{in:stepno}&")")' % (
        RS('copies_from'), v('No data for this step'), RS('readthrough'), RS('threshold'), v('Step is healthy'), STEP1, v('Book 2 needs work'), v('Step needs work')))],
    GR('What if', ('Close all of the gap', {'close': 1.0}), ('Close a quarter of the gap', {'close': 0.25}))))

# 4 ------------------------------------------------------------ where readers drop
def DRP(col, n): return 'IFERROR(INDEX({range:drops.%s},%d),"")' % (col, n)
tools.append(TOOL('drops_tool', 'Drop Fix First', 'Which step of which series loses the most readers',
    'All series steps are ranked by readers lost (copies of book n minus copies of book n+1, last 12 months); type the share of the lost readers you could win back to see the copies and royalties at stake, with a verdict that names the step to fix first.', [
    I('win', 'Share of the lost readers you could win back', 0.10, 'pct')], [
    O('Readers lost, all steps', 'int', 'SUM({range:rtstep.lost})'), O('Steps below the threshold', 'int', 'COUNTIFS({range:rtstep.flag},%s)' % v('Below the threshold')),
    O('First: series', 'text', DRP('series', 1)), O('First: step', 'text', DRP('stepno', 1)), O('First: readers lost', 'int', NZ(DRP('lost', 1))), O('First: share of all readers lost', 'pct', NZ(DRP('share_all', 1))),
    O('Second: series and step', 'text', '%s&", "&%s' % (DRP('series', 2), DRP('stepno', 2))), O('Second: readers lost', 'int', NZ(DRP('lost', 2))),
    O('Third: series and step', 'text', '%s&", "&%s' % (DRP('series', 3), DRP('stepno', 3))), O('Third: readers lost', 'int', NZ(DRP('lost', 3))),
    O('Readers won back at the first step', 'int', 'ROUND(%s*{in:win},0)' % NZ(DRP('lost', 1))), O('Royalties those readers bring', 'money', '%s*{in:win}' % NZ(DRP('lost_value', 1))),
    O('Verdict', 'text', '%s&" "&%s&", "&%s&" ("&%s&")"' % (v('Fix first:'), DRP('series', 1), DRP('stepno', 1), DRP('from_title', 1)))],
    GR('What if', ('Win back 25 percent', {'win': 0.25}), ('Win back 5 percent', {'win': 0.05}))))

# 5 ------------------------------------------------------------ value of a reader
def VR(col, no='1'): return 'SUMIFS({range:vreader.%s},{range:vreader.series},{in:series},{range:vreader.no},%s)' % (col, no)
SERVAL = 'SUMIFS({range:vreader.series_value},{range:vreader.series},{in:series})'
ACTAD = 'IFERROR(SUMIFS({range:titles.ad_12m},{range:titles.series},{in:series},{range:titles.series_order},1)/SUMIFS({range:titles.copies_12m},{range:titles.series},{in:series},{range:titles.series_order},1),0)'
tools.append(TOOL('reader_value', 'Reader Value and Ad Ceiling', 'What is a book-1 reader worth and what may book 1 ads cost',
    'Pick a series: your royalty per copy times the read-through chain gives the royalties per book-1 buyer over the whole series; the share you accept as ad cost sets the ad ceiling for a sale of book 1.', [
    IL('series', 'Series', 'series4', 'Lantern Bay Mysteries'), I('ad_share', 'Share of the value you accept as ad cost', 0.35, 'pct')], [
    O('Copies of book 1, last 12 months', 'int', VR('copies')), O('Royalty per copy of book 1', 'money', VR('roy_copy')), O('Read-through from book 1 into book 2', 'pct', 'IFERROR(SUMIFS({range:rtstep.readthrough},{range:rtstep.series},{in:series},{range:rtstep.stepno},%s),0)' % STEP1),
    O('Value of a book-1 reader over the series', 'money', SERVAL), O('Of it, from later books', 'money', '%s-%s' % (SERVAL, VR('roy_copy'))),
    O('Break-even ad cost for a sale of book 1', 'money', SERVAL), O('Ad ceiling at your share', 'money', '%s*{in:ad_share}' % SERVAL), O('Your ad spend per copy of book 1', 'money', ACTAD),
    O('Room under the ceiling', 'money', '%s*{in:ad_share}-%s' % (SERVAL, ACTAD)),
    O('Verdict', 'text', 'IF(%s>%s*{in:ad_share},%s,%s&" "&ROUND(%s*{in:ad_share},2))' % (ACTAD, SERVAL, v('Ads cost more than the ceiling'), v('Ads justified up to a cost per sale of'), SERVAL))],
    GR('What if', ('Accept 25 percent', {'ad_share': 0.25}), ('Accept 50 percent', {'ad_share': 0.5}), ('Accept 10 percent', {'ad_share': 0.10}))))

# 6 ------------------------------------------------------------ book 1 price test
RN = '({in:p_now}*{in:s_now})'; RW = '({in:p_new}*{in:s_new})'
TN = '({in:copies}*(%s+{in:later}))' % RN; TW = '({in:copies}*(1+{in:lift})*(%s+{in:later}))' % RW
tools.append(TOOL('price_test', 'Book 1 Price Test', 'Should book 1 cost less, the same or more',
    'Type the price now and the new price with the royalty share at each (check each store\'s current terms; a low price often pays a lower share), the copies a month and the lift you expect; the royalties of later books that these readers bring in are added.', [
    I('p_now', 'Price now', 2.99), I('p_new', 'New price', 0.99), I('s_now', 'Royalty share at the price now', 0.70, 'pct'), I('s_new', 'Royalty share at the new price', 0.35, 'pct'),
    I('copies', 'Copies a month at the price now', 300, 'int'), I('lift', 'Lift in copies you expect at the new price', 0.40, 'pct'), I('later', 'Royalties of later books per reader (see Value of a Reader)', 3.0)], [
    O('Royalty per copy now', 'money', RN), O('Royalty per copy at the new price', 'money', RW), O('Copies needed to hold the book 1 royalties', 'int', 'IF(%s>0,ROUND({in:copies}*%s/%s,0),0)' % (RW, RN, RW)),
    O('Copies you expect at the new price', 'int', 'ROUND({in:copies}*(1+{in:lift}),0)'), O('Book 1 royalties a month now', 'money', '{in:copies}*%s' % RN), O('Book 1 royalties a month at the new price', 'money', '{in:copies}*(1+{in:lift})*%s' % RW),
    O('Extra royalties of later books a month', 'money', '{in:copies}*{in:lift}*{in:later}'), O('Total a month now', 'money', TN), O('Total a month at the new price', 'money', TW), O('Change a month', 'money', '%s-%s' % (TW, TN)),
    O('Verdict', 'text', 'IF(ABS(%s-%s)<=0.05*%s,%s,IF(%s>%s,IF({in:p_new}<{in:p_now},%s,%s),%s))' % (TW, TN, TN, v('Keep the price'), TW, TN, v('Lower the price'), v('Raise the price'), v('Keep the price')))],
    GR('What if', ('Lift of 100 percent', {'lift': 1.0}), ('Lift of 20 percent', {'lift': 0.2}), ('Price 4.99, copies fall 20 percent', {'p_new': 4.99, 's_new': 0.70, 'lift': -0.2}), ('Later books bring 5.00 a reader', {'later': 5.0}))))

# 7 ------------------------------------------------------------ pen-name profit and loss
def PSUM(col, i, tab='pnl'): return 'SUMIFS({range:%s.%s},{range:%s.pen_name},%s,%s)' % (tab, col, tab, PN[i], WN('%s.month' % tab))
def MARG(i): return 'IF(%s>0,%s/%s,0)' % (PSUM('royalties', i), PSUM('profit', i), PSUM('royalties', i))
tools.append(TOOL('pen_pl', 'Pen-name Profit Verdict', 'Which pen name earns its keep',
    'Type the months to look back (up to 22 complete months); revenue, direct costs, shared costs under the rule you set on Start, profit and margin of each pen name come from the pen-name sheet, with a verdict on which pen name to feed. A small press reads the pen name as an author.', [
    I('months', 'Months to look back', 11, 'int'), I('gap', 'Margin difference you call balanced', 0.05, 'pct')], [
    O('%s: revenue' % PEN_NAMES[0], 'money', PSUM('royalties', 0)), O('%s: direct costs' % PEN_NAMES[0], 'money', PSUM('direct', 0)), O('%s: shared costs' % PEN_NAMES[0], 'money', PSUM('shared', 0)),
    O('%s: profit' % PEN_NAMES[0], 'money', PSUM('profit', 0)), O('%s: margin' % PEN_NAMES[0], 'pct', MARG(0)),
    O('%s: revenue' % PEN_NAMES[1], 'money', PSUM('royalties', 1)), O('%s: direct costs' % PEN_NAMES[1], 'money', PSUM('direct', 1)), O('%s: shared costs' % PEN_NAMES[1], 'money', PSUM('shared', 1)),
    O('%s: profit' % PEN_NAMES[1], 'money', PSUM('profit', 1)), O('%s: margin' % PEN_NAMES[1], 'pct', MARG(1)),
    O('Pen names under your margin target', 'int', '(%s<{set:margin_target})+(%s<{set:margin_target})' % (MARG(0), MARG(1))), O('Shared cost rule on Start', 'text', '{set:cost_rule}'),
    O('Verdict', 'text', 'IF(ABS(%s-%s)<{in:gap},%s,%s&" "&IF(%s>%s,%s,%s))' % (MARG(0), MARG(1), v('Balanced'), v('Feed pen name'), MARG(0), MARG(1), PN[0], PN[1]))],
    GR('What if', ('Look back 6 months', {'months': 6}), ('Look back 3 months', {'months': 3}), ('Balanced within 10 points', {'gap': 0.10}))))

# 8 ------------------------------------------------------------ shared cost rule comparer
def SP(col, i): return 'SUMIFS({range:pnl.%s},{range:pnl.pen_name},%s,%s)' % (col, PN[i], WN('pnl.month'))
def SSH(col, i): return 'SUMIFS({range:sharesplit.%s},{range:sharesplit.pen_name},%s,%s)' % (col, PN[i], WN('sharesplit.month'))
def GAPR(col): return 'ABS(%s/%s-%s/%s)' % (SP(col, 0), SP('royalties', 0), SP(col, 1), SP('royalties', 1))
def SWING(i): return '(MAX(%s,%s,%s)-MIN(%s,%s,%s))' % (SSH('equal', i), SSH('by_rev', i), SSH('by_titles', i), SSH('equal', i), SSH('by_rev', i), SSH('by_titles', i))
G1, G2, G3 = GAPR('profit_eq'), GAPR('profit_rev'), GAPR('profit_tit')
tools.append(TOOL('rule_compare', 'Shared Cost Rule Comparer', 'Which rule splits the shared costs fairest',
    'The shared costs of the last months are split three ways between the pen names (equal, by revenue, by number of titles); see the profit of each pen name under every rule, the largest swing and the rule that leaves the margins closest. Confirm your choice with your accountant.', [
    I('months', 'Months to look back', 11, 'int')], [
    O('%s: profit, equal rule' % PEN_NAMES[0], 'money', SP('profit_eq', 0)), O('%s: profit, by revenue' % PEN_NAMES[0], 'money', SP('profit_rev', 0)), O('%s: profit, by titles' % PEN_NAMES[0], 'money', SP('profit_tit', 0)),
    O('%s: profit, equal rule' % PEN_NAMES[1], 'money', SP('profit_eq', 1)), O('%s: profit, by revenue' % PEN_NAMES[1], 'money', SP('profit_rev', 1)), O('%s: profit, by titles' % PEN_NAMES[1], 'money', SP('profit_tit', 1)),
    O('Margin gap, equal rule', 'pct', G1), O('Margin gap, by revenue', 'pct', G2), O('Margin gap, by titles', 'pct', G3),
    O('Largest swing between rules for one pen name', 'money', 'MAX(%s,%s)' % (SWING(0), SWING(1))),
    O('Verdict', 'text', 'IF(%s<=MIN(%s,%s),%s&" "&%s,IF(%s<=%s,%s&" "&%s,%s&" "&%s))' % (G1, G2, G3, v('Fairest rule is'), tok('rule', 'Equal'), G2, G3, v('Fairest rule is'), tok('rule', 'By revenue'), v('Fairest rule is'), tok('rule', 'By titles')))],
    GR('What if', ('Last 6 months', {'months': 6}), ('Last 3 months', {'months': 3}))))

# 9 ------------------------------------------------------------ box set case
BX = '({in:copies}*{in:b_price}*{in:share}-{in:taken}*{in:single}*{in:share})'
NETC = '({in:b_price}*{in:share}-{in:taken}/MAX(1,{in:copies})*{in:single}*{in:share})'
tools.append(TOOL('box_case', 'Box Set Case', 'Is a box set worth making',
    'Type the average price of a single book, the box set price, your royalty share (check each store\'s current terms), the copies you expect and the single copies it takes from you; see the extra income a month, the break-even copies in a closed form and the months to earn back the set-up cost.', [
    I('books', 'Books in the box set', 3, 'int'), I('single', 'Average price of a single book', 5.99), I('b_price', 'Box set price', 10.99), I('share', 'Royalty share', 0.70, 'pct'),
    I('copies', 'Box set copies a month you expect', 60, 'int'), I('taken', 'Single copies a month it takes', 25, 'int'), I('setup', 'Set-up cost (cover, files, narration if any)', 880), I('limit', 'Months you accept to earn it back', 12, 'int')], [
    O('Prices of the single books together', 'money', '{in:books}*{in:single}'), O('Discount to the singles', 'pct', 'IF({in:books}*{in:single}>0,1-{in:b_price}/({in:books}*{in:single}),0)'),
    O('Royalty per box set copy', 'money', '{in:b_price}*{in:share}'), O('Royalty lost per single copy taken', 'money', '{in:single}*{in:share}'), O('Extra income a month', 'money', BX),
    O('Net gain per box set copy', 'money', NETC), O('Break-even box set copies', 'int', 'IF(%s>0,ROUNDUP({in:setup}/%s,0),"")' % (NETC, NETC)),
    O('Months to earn back the set-up cost', 'num', 'IF(%s>0,{in:setup}/%s,"")' % (BX, BX)), O('Income in the first year after cost', 'money', '%s*12-{in:setup}' % BX),
    O('Verdict', 'text', 'IF(AND(%s>0,%s<={in:limit}*%s),%s,%s)' % (BX, '{in:setup}', BX, v('Make the box set'), v('Skip the box set')))],
    GR('What if', ('Only 30 box sets a month', {'copies': 30}), ('It takes 50 single copies', {'taken': 50}), ('Price 12.99', {'b_price': 12.99}), ('Set-up cost 1,500', {'setup': 1500}))))

# 10 ----------------------------------------------------------- bundle cannibalisation check
START = 'DATE(YEAR(%s),MONTH(%s)+1,1)' % (TI('release_date', 'box'), TI('release_date', 'box'))
SGL = '{range:tsales.series},{in:ser},{range:tsales.book_no},"<="&{in:last_book}'
BEF = 'SUMIFS({range:tsales.royalties},%s,{range:tsales.month},">="&EDATE(%s,-1-{in:nm}),{range:tsales.month},"<"&EDATE(%s,-1))' % (SGL, START, START)
AFT = 'SUMIFS({range:tsales.royalties},%s,{range:tsales.month},">="&%s,{range:tsales.month},"<"&EDATE(%s,{in:nm}))' % (SGL, START, START)
BOXR = 'SUMIFS({range:tsales.royalties},{range:tsales.title},{in:box},{range:tsales.month},">="&%s,{range:tsales.month},"<"&EDATE(%s,{in:nm}))' % (START, START)
tools.append(TOOL('bundle_check', 'Bundle Cannibalisation Check', 'Did the box set add income or only swap it',
    'Pick an existing box set, the series of its single books and the last book number inside it; the royalties of the single books in the months before and after its release are compared with the box set royalties. Seasons also move sales, so read the result with your own calendar in mind.', [
    IL('box', 'Existing box set', 'title', 'The Ember Crown Books 1-3'), IL('ser', 'Series of the single books', 'series', 'The Ember Crown'), I('last_book', 'Last single book inside the box set', 3, 'int'), I('nm', 'Months compared before and after', 3, 'int')], [
    O('Release date of the box set', 'date', TI('release_date', 'box')), O('Single books, royalties before', 'money', BEF), O('Single books, royalties after', 'money', AFT),
    O('Change of the single books', 'pct', 'IF(%s>0,%s/%s-1,0)' % (BEF, AFT, BEF)), O('Box set royalties after', 'money', BOXR), O('Singles plus box set after', 'money', '%s+%s' % (AFT, BOXR)),
    O('Change against the singles before', 'pct', 'IF(%s>0,(%s+%s)/%s-1,0)' % (BEF, AFT, BOXR, BEF)),
    O('Share of the box set income taken from the singles', 'pct', 'IF(%s>0,MAX(0,%s-%s)/%s,0)' % (BOXR, BEF, AFT, BOXR)),
    O('Verdict', 'text', 'IF(%s+%s>=%s,%s,%s)' % (AFT, BOXR, BEF, v('Bundle adds'), v('Bundle swaps')))],
    GR('What if', ('Compare 2 months', {'nm': 2}), ('Compare 4 months', {'nm': 4}), ('Only books 1 and 2 count', {'last_book': 2}))))

# 11 ----------------------------------------------------------- catalogue decision
tools.append(TOOL('catalogue_tool', 'Catalogue Decision', 'Keep, reprice, repackage or retire this title',
    'Pick a title: its age, royalties and ad spend of the last 12 months, the cost left to recover, the trend and its role in the series give the verdict with one reason; type a change in pace to see how long the cost would take to earn back.', [
    IL('title', 'Title', 'title', "The Glassmaker's Orchard"), I('pace', 'Change in monthly royalties you expect', 0.0, 'pct')], [
    O('Verdict', 'text', DC('verdict')), O('Reason', 'text', DC('reason')), O('Status', 'text', DC('status')), O('Age (months)', 'int', NZ(DC('age'))), O('Role in the series', 'text', DC('role')),
    O('Royalties, last 12 months', 'money', NZ(DC('roy12'))), O('Ad spend, last 12 months', 'money', NZ(DC('ad12'))), O('Ad spend as a share of royalties', 'pct', 'IF(%s>0,%s/%s,0)' % (NZ(DC('roy12')), NZ(DC('ad12')), NZ(DC('roy12')))),
    O('Cost left to recover', 'money', NZ(DC('cost_left'))), O('Change, last 3 months', 'pct', NZ(DC('trend_chg'))), O('Yearly return', 'pct', NZ(DC('ret'))),
    O('Months to earn back the cost left', 'num', 'IF(%s>0,%s/(%s/12*(1+{in:pace})),0)' % (NZ(DC('roy12')), NZ(DC('cost_left')), NZ(DC('roy12')))), O('Price to test if you reprice', 'money', NZ(DC('new_price'))),
    O('Decision you took', 'text', DC('decision'))],
    GR('What if', ('Royalties rise 25 percent', {'pace': 0.25}), ('Royalties fall 25 percent', {'pace': -0.25}))))

# 12 ----------------------------------------------------------- yearly return test
tools.append(TOOL('return_tool', 'Return Test Verdict', 'Does this title earn its production cost back each year',
    'Pick a title and type your yearly return target (your own number); the royalties of the last 12 months divided by the production cost give the return, with the royalties a month the title needs to pass and how many titles fail at this target.', [
    IL('title', 'Title', 'title', "The Glassmaker's Orchard"), I('target', 'Yearly return you want', 0.10, 'pct')], [
    O('Production cost', 'money', NZ(YT('cost'))), O('Royalties, last 12 months', 'money', NZ(YT('roy12'))), O('Yearly return', 'pct', NZ(YT('ret'))),
    O('Royalties a month needed to pass', 'money', '%s*{in:target}/12' % NZ(YT('cost'))), O('Short of it each month', 'money', 'IF(%s="",0,MAX(0,%s*{in:target}/12-%s/12))' % (YT('ret'), NZ(YT('cost')), NZ(YT('roy12')))),
    O('Titles tested', 'int', 'COUNTIFS({range:ytest.status},%s)' % REL), O('Titles that fail at this target', 'int', 'COUNTIFS({range:ytest.ret},"<"&{in:target})'),
    O('Verdict', 'text', 'IF(%s="",%s,IF(%s>={in:target},%s,%s))' % (YT('ret'), v('Not tested'), YT('ret'), v('Passes'), v('Fails')))],
    GR('What if', ('Target 25 percent', {'target': 0.25}), ('Target 50 percent', {'target': 0.5}), ('Target 100 percent', {'target': 1.0}))))

# 13 ----------------------------------------------------------- title trend
tools.append(TOOL('trend_tool', 'Title Trend Verdict', 'Is this title growing, flat or declining',
    'Pick a title: royalties of the last 3 months against the 3 months before, the same months last year and your own 3-month average; type the change that counts as growing or declining.', [
    IL('title', 'Title', 'title', 'The Pale Bell Ringers'), I('flag', 'Change that counts as growing or declining', 0.20, 'pct')], [
    O('Last 3 months', 'money', NZ(TR('last3'))), O('Previous 3 months', 'money', NZ(TR('prev3'))), O('Same 3 months last year', 'money', NZ(TR('ly3'))), O('Change against previous 3 months', 'pct', NZ(TR('change_prev'))),
    O('Change against last year', 'pct', NZ(TR('change_ly'))), O('Your 3-month average', 'money', NZ(TR('avg3'))), O('Last 3 months against your average', 'pct', NZ(TR('vs_avg'))),
    O('Verdict', 'text', 'IF(%s="",%s,IF(%s>{in:flag},%s,IF(%s<-{in:flag},%s,%s)))' % (TR('change_prev'), v('Too new to judge'), TR('change_prev'), v('Growing'), TR('change_prev'), v('Declining'), v('Flat')))],
    GR('What if', ('Flag at 10 percent', {'flag': 0.10}), ('Flag at 30 percent', {'flag': 0.30}), ('Flag at 60 percent', {'flag': 0.60}))))

# 14 ----------------------------------------------------------- series completion value
SER_REL = 'COUNTIFS({range:titles.series},{in:series},{range:titles.status},%s)' % REL
SER_ROY = 'SUMIFS({range:titles.royalties_12m},{range:titles.series},{in:series})'
LREL = 'SUMPRODUCT(MAX(({range:titles.series}={in:series})*({range:titles.status}=%s)*({range:titles.release_date})))' % REL
LSTART = 'DATE(YEAR(%s),MONTH(%s)+1,1)' % (LREL, LREL)
EARL = '{range:tsales.series},{in:series},{range:tsales.book_no},"<"&%s' % SER_REL
LBEF = 'SUMIFS({range:tsales.royalties},%s,{range:tsales.month},">="&EDATE(%s,-4),{range:tsales.month},"<"&EDATE(%s,-1))' % (EARL, LSTART, LSTART)
LAFT = 'SUMIFS({range:tsales.royalties},%s,{range:tsales.month},">="&%s,{range:tsales.month},"<"&EDATE(%s,3))' % (EARL, LSTART, LSTART)
FIN = '({in:left}*%s/%s+{in:lift}*%s)' % (SER_ROY, SER_REL, SER_ROY)
NEWV = '({in:left}*AVERAGEIFS({range:titles.royalties_12m},{range:titles.status},%s))' % REL
tools.append(TOOL('completion', 'Series Completion Value', 'Finish this series or start a new one',
    'Pick a series and the books still to write; what finishing adds is the royalties of the new books at the series average plus the lift on the earlier books (your own number, the lift measured in your own history is shown, and it moves with the seasons), set against the average of your released titles.', [
    IL('series', 'Series', 'series4', 'Lantern Bay Mysteries'), I('left', 'Books left to write', 1, 'int'), I('lift', 'Lift on the earlier books (your own number)', 0.05, 'pct')], [
    O('Books released in the series', 'int', SER_REL), O('Royalties of the series, last 12 months', 'money', SER_ROY), O('Average royalties a released book', 'money', 'IF(%s>0,%s/%s,0)' % (SER_REL, SER_ROY, SER_REL)),
    O('Release date of the last book', 'date', LREL), O('Earlier books, 3 months before the last release', 'money', LBEF), O('Earlier books, 3 months after', 'money', LAFT),
    O('Lift measured in your own history', 'pct', 'IF(%s>0,%s/%s-1,0)' % (LBEF, LAFT, LBEF)),
    O('Extra royalties in 12 months if you finish', 'money', 'IF(%s>0,%s,0)' % (SER_REL, FIN)), O('Same books as a new series, average title', 'money', NEWV),
    O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % ('IF(%s>0,%s,0)' % (SER_REL, FIN), NEWV, v('Finish the series'), v('Start a new series')))],
    GR('What if', ('Two books left', {'left': 2}), ('Lift of 15 percent', {'lift': 0.15}), ('No lift', {'lift': 0.0}))))

# 15 ----------------------------------------------------------- next book forecast
C3 = '({in:list_size}*{in:share}+{in:prior}*{in:rt})'
tools.append(TOOL('next_book', 'Next Book Forecast', 'Will the next book earn back its cost',
    'Type your list size, the share of it that buys at launch, the copies the previous book sold in its last 3 months and your read-through into the next book; see the copies and royalties of the first 3 months in a Base, Best and Worst case and the months to earn back the cost. A forecast from your own numbers, not a promise.', [
    I('list_size', 'Newsletter list size', 5200, 'int'), I('share', 'Share of the list that buys at launch (your own number)', 0.08, 'pct'), I('prior', 'Copies of the previous book in its last 3 months', 410, 'int'),
    I('rt', 'Read-through into the next book', 0.70, 'pct'), I('roy', 'Royalty per copy', 3.10), I('cost', 'Production cost of the next book', 4750), I('horizon', 'Months you accept to earn it back', 12, 'int'),
    I('best', 'Best case against Base', 1.25, 'num'), I('worst', 'Worst case against Base', 0.70, 'num')], [
    O('Copies from your list', 'int', '{in:list_size}*{in:share}'), O('Copies from read-through', 'int', '{in:prior}*{in:rt}'), O('Copies in 3 months, Base', 'int', C3),
    O('Copies in 3 months, Best', 'int', '%s*{in:best}' % C3), O('Copies in 3 months, Worst', 'int', '%s*{in:worst}' % C3), O('Royalties in 3 months, Base', 'money', '%s*{in:roy}' % C3),
    O('Royalties in 3 months, Best', 'money', '%s*{in:roy}*{in:best}' % C3), O('Royalties in 3 months, Worst', 'money', '%s*{in:roy}*{in:worst}' % C3),
    O('Months to earn back the cost, Base', 'num', 'IF(%s>0,{in:cost}/(%s*{in:roy}/3),"")' % (C3, C3)), O('Months to earn back the cost, Worst', 'num', 'IF(%s>0,{in:cost}/(%s*{in:roy}*{in:worst}/3),"")' % (C3, C3)),
    O('Verdict', 'text', 'IF(%s>0,IF({in:cost}/(%s*{in:roy}*{in:worst}/3)<={in:horizon},%s,%s),%s)' % (C3, C3, v('Expected to earn back'), v('May not earn back'), v('May not earn back')))],
    GR('What if', ('List of 3,000 readers', {'list_size': 3000}), ('Read-through 40 percent', {'rt': 0.40}), ('Cost 8,000', {'cost': 8000}), ('Launch share 4 percent', {'share': 0.04}))))

# 16 ----------------------------------------------------------- backlist against frontlist
BL1 = 'SUMIFS({range:titles.royalties_12m},{range:titles.age_months},">"&{in:cut1})'
BL2 = 'SUMIFS({range:titles.royalties_12m},{range:titles.age_months},">"&{in:cut2})'
M7 = 'EDATE(%s,-7)' % MS
tools.append(TOOL('backlist_tool', 'Backlist against Frontlist', 'Do old books or new books carry your income',
    'Type the ages in months that count as backlist; the share of the royalties of the last 12 months from titles older than each age is shown, with the backlist share 7 months ago for comparison and a verdict.', [
    I('cut1', 'Backlist starts after (months)', 12, 'int'), I('cut2', 'Strong backlist starts after (months)', 24, 'int'), I('pivot', 'Share at which the backlist carries the income', 0.50, 'pct')], [
    O('Royalties, last 12 months', 'money', TOTAL_ROY()), O('From titles older than the first age', 'money', BL1), O('Backlist share', 'pct', 'IF(%s>0,%s/%s,0)' % (TOTAL_ROY(), BL1, TOTAL_ROY())),
    O('From titles older than the second age', 'money', BL2), O('Share from the older titles', 'pct', 'IF(%s>0,%s/%s,0)' % (TOTAL_ROY(), BL2, TOTAL_ROY())),
    O('Frontlist share', 'pct', 'IF(%s>0,1-%s/%s,0)' % (TOTAL_ROY(), BL1, TOTAL_ROY())),
    O('Backlist share 7 months ago', 'pct', 'IFERROR(SUMIFS({range:backlist.back},{range:backlist.month},%s)/SUMIFS({range:backlist.total},{range:backlist.month},%s),0)' % (M7, M7)),
    O('Verdict', 'text', 'IF(%s>={in:pivot}*%s,%s&" "&ROUND(%s/%s*100,0)&"%%",%s&" "&ROUND((1-%s/%s)*100,0)&"%%")' % (BL1, TOTAL_ROY(), v('Backlist carries'), BL1, TOTAL_ROY(), v('Frontlist carries'), BL1, TOTAL_ROY()))],
    GR('What if', ('Backlist after 18 months', {'cut1': 18}), ('Backlist after 6 months', {'cut1': 6}), ('Pivot at 70 percent', {'pivot': 0.70}))))

# 17 ----------------------------------------------------------- top title dependence
TOPN = 'SUMIFS({range:titles.royalties_12m},{range:titles.rank_key},">="&LARGE({range:titles.rank_key},{in:topn}))'
tools.append(TOOL('top3_tool', 'Top Title Dependence', 'How much of your income hangs on a few titles',
    'Type how many top titles to count and the share you accept; see their share of the royalties of the last 12 months, the top three titles by name and the income a month you would lose if the top title stopped selling.', [
    I('topn', 'Top titles to count', 3, 'int'), I('limit', 'Highest share you accept', 0.40, 'pct')], [
    O('Royalties, last 12 months', 'money', TOTAL_ROY()), O('Share of the top titles', 'pct', 'IF(%s>0,%s/%s,0)' % (TOTAL_ROY(), TOPN, TOTAL_ROY())), O('Royalties from outside the top titles', 'money', '%s-%s' % (TOTAL_ROY(), TOPN)),
    O('Top title', 'text', 'INDEX({range:ranking.title},1)'), O('Second title', 'text', 'INDEX({range:ranking.title},2)'), O('Third title', 'text', 'INDEX({range:ranking.title},3)'),
    O('Income a month lost if the top title stopped', 'money', 'INDEX({range:ranking.roy12},1)/12'), O('Share of royalties of the top title', 'pct', 'INDEX({range:ranking.share},1)'),
    O('Titles that earn half of your royalties', 'int', 'COUNTIFS({range:ranking.cum_share},"<0.5")+1'),
    O('Verdict', 'text', 'IF(IF(%s>0,%s/%s,0)>{in:limit},%s,%s)' % (TOTAL_ROY(), TOPN, TOTAL_ROY(), v('Diversify'), v('Dependence is ok')))],
    GR('What if', ('Count the top 5', {'topn': 5}), ('Count the top 1', {'topn': 1}), ('Accept only 20 percent', {'limit': 0.20}))))

# 18 ----------------------------------------------------------- pen-name growth compare
def GRW(i, col='royalties', cur=True):
    w = WN('pnl.month') if cur else WN('pnl.month', '2*{in:months}', '{in:months}')
    return 'SUMIFS({range:pnl.%s},{range:pnl.pen_name},%s,%s)' % (col, PN[i], w)
def GR_(i): return 'IF(%s>0,%s/%s-1,0)' % (GRW(i, cur=False), GRW(i), GRW(i, cur=False))
def ADDED(i): return 'COUNTIFS({range:titles.pen_name},%s,{range:titles.release_date},">="&EDATE(%s,-{in:months}),{range:titles.release_date},"<"&%s)' % (PN[i], MS, MS)
tools.append(TOOL('pen_growth', 'Pen-name Growth Compare', 'Which pen name is growing faster',
    'Type the months to compare (up to 11, the complete months of your history); royalties, copies and titles added of the latest period against the period before, by pen name, with a verdict on the faster-growing pen name.', [
    I('months', 'Months in each period', 11, 'int'), I('level', 'Difference you call level', 0.02, 'pct')], [
    O('%s: royalties, latest period' % PEN_NAMES[0], 'money', GRW(0)), O('%s: royalties, period before' % PEN_NAMES[0], 'money', GRW(0, cur=False)), O('%s: growth' % PEN_NAMES[0], 'pct', GR_(0)),
    O('%s: copies, latest period' % PEN_NAMES[0], 'int', GRW(0, 'copies')), O('%s: titles added' % PEN_NAMES[0], 'int', ADDED(0)),
    O('%s: royalties, latest period' % PEN_NAMES[1], 'money', GRW(1)), O('%s: royalties, period before' % PEN_NAMES[1], 'money', GRW(1, cur=False)), O('%s: growth' % PEN_NAMES[1], 'pct', GR_(1)),
    O('%s: copies, latest period' % PEN_NAMES[1], 'int', GRW(1, 'copies')), O('%s: titles added' % PEN_NAMES[1], 'int', ADDED(1)),
    O('Verdict', 'text', 'IF(ABS(%s-%s)<={in:level},%s,%s&" "&IF(%s>%s,%s,%s)&" "&%s)' % (GR_(0), GR_(1), v('Growth is level'), v('Pen name'), GR_(0), GR_(1), PN[0], PN[1], v('is growing faster')))],
    GR('What if', ('Compare 6 months', {'months': 6}), ('Compare 3 months', {'months': 3}), ('Level within 10 points', {'level': 0.10}))))
assert len(tools) == 18, len(tools)
