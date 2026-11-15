"""Author and Self-Publisher suite part 1: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au1_lists import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, f, formula): return OUT(label, f, formula)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
GAP = '{set:min_release_gap_days}'
REL = '{range:titles.release_date}'
PLN = est('Planned'); LIVE = est('Live'); RELD = tst('Released')
def TI(c, tid='{in:tid}'): return 'INDEX({range:titles.%s},MATCH(%s,{range:titles.title_id},0))' % (c, tid)
tools = []

# 1 ------------------------------------------------------------ release slot finder
def PUSH(s): return 'MAX(%s,SUMPRODUCT(MAX((%s>(%s)-%s)*(%s<(%s)+%s)*(%s+%s))))' % (s, REL, s, GAP, REL, s, GAP, REL, GAP)
F3 = PUSH(PUSH(PUSH('{in:pdate}')))
NX = 'SUMPRODUCT(MIN((%s>{in:pdate})*%s+(%s<={in:pdate})*999999))' % (REL, REL, REL)
INGAP = 'COUNTIFS(%s,">"&({in:pdate}-%s),%s,"<"&({in:pdate}+%s))' % (REL, GAP, REL, GAP)
tools.append(TOOL('slot', 'Release Slot Finder', 'Is this release date free of conflicts',
    'Type a proposed release date: it is set against every release, pre-order, promotion and deadline in your catalogue, with the neighbours either side, the earliest clear date and a verdict.', [
    I('pdate', 'Proposed release date', ahead(45), 'date'), I('max_move', 'Longest move you accept, days', 30, 'int')], [
    O('Release before that date', 'date', 'SUMPRODUCT(MAX((%s<{in:pdate})*%s))' % (REL, REL)),
    O('Days since the release before', 'int', '{in:pdate}-SUMPRODUCT(MAX((%s<{in:pdate})*%s))' % (REL, REL)),
    O('Days to the release after (999 means none)', 'int', 'IF(%s>900000,999,%s-{in:pdate})' % (NX, NX)),
    O('Releases inside the minimum gap', 'int', INGAP),
    O('Calendar entries within 7 days', 'int', 'COUNTIFS({range:calendar.date},">="&({in:pdate}-7),{range:calendar.date},"<="&({in:pdate}+7))'),
    O('Earliest clear date', 'date', F3), O('Days to move', 'int', '(%s)-{in:pdate}' % F3),
    O('Verdict', 'text', 'IF(%s=0,%s,IF((%s)-{in:pdate}<={in:max_move},%s,%s))' % (INGAP, v1('Slot is free'), F3, v1('Move the date'), v1('Too close to a release')))],
    GR('What if the date moves', ('In 30 days', {'pdate': '={today}+30'}), ('In 60 days', {'pdate': '={today}+60'}), ('In 90 days', {'pdate': '={today}+90'}), ('In 120 days', {'pdate': '={today}+120'}), ('In 180 days', {'pdate': '={today}+180'}))))

# 2 ------------------------------------------------------------ series timeline builder
def DK(k): return '{in:first}+(MIN(%d,{in:books})-1)*{in:gap}' % k
DUE = 'MIN({in:books},IF({today}<{in:first},0,INT(({today}-{in:first})/{in:gap})+1))'
BEHIND = 'MAX(0,%s-{in:released})' % DUE
tools.append(TOOL('timeline', 'Series Timeline Builder', 'When does each book land, and what does the series cost',
    'Type the first release date, the books planned, your gap in days and the cost of a book: see the release date of each book, the last date, the total cost and whether the series is on plan.', [
    I('first', 'First release date', ago(1080), 'date'), I('books', 'Books planned', 4, 'int'), I('gap', 'Gap between books, days', 330, 'int'), I('cost', 'Cost of one book', 3800), I('released', 'Books released so far', 2, 'int')], [
    O('Release date of book 2', 'date', DK(2)), O('Release date of book 3', 'date', DK(3)), O('Release date of book 4', 'date', DK(4)),
    O('Release date of the last book', 'date', '{in:first}+({in:books}-1)*{in:gap}'), O('Years from first to last book', 'num', 'ROUND(({in:books}-1)*{in:gap}/365,1)'),
    O('Total series cost', 'money', '{in:books}*{in:cost}'), O('Cost a year over the plan', 'money', 'IF({in:books}>1,ROUND({in:books}*{in:cost}/(({in:books}-1)*{in:gap}/365),0),{in:cost})'),
    O('Books due by today on this plan', 'int', DUE), O('Books behind the plan', 'int', BEHIND),
    O('Next planned release date', 'date', '{in:first}+MIN(%s,{in:books}-1)*{in:gap}' % DUE),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (BEHIND, v1('On plan'), v1('Behind plan')))],
    GR('What if the gap changes', ('Gap 240 days', {'gap': 240}), ('Gap 300 days', {'gap': 300}), ('Gap 330 days', {'gap': 330}), ('Gap 400 days', {'gap': 400}), ('Gap 480 days', {'gap': 480}))))

# 3 ------------------------------------------------------------ next book date solver
SER = '({range:titles.series}={in:series})*(%s<={today})' % REL
NREL = 'COUNTIFS({range:titles.series},{in:series},%s,"<="&{today})' % REL
N4 = 'MIN(4,%s)' % NREL
LAT = 'SUMPRODUCT(LARGE(%s*%s,1))' % (SER, REL)
AVG = 'IF(%s>=2,(%s-SUMPRODUCT(LARGE(%s*%s,%s)))/(%s-1),{in:fallback})' % (N4, LAT, SER, REL, N4, N4)
NEXT = '%s+%s' % (LAT, AVG)
WD = 'ROUND({in:words}/{in:wpm}*30,0)'
STARTBY = '(%s)-{in:lead}-%s' % (NEXT, WD)
tools.append(TOOL('nextbook', 'Next Book Date Solver', 'When should the next book of a series land and start',
    'Pick a series: your own average gap between its last four releases gives the expected next release; your writing pace and production lead then give the date to start by and the days left.', [
    IL('series', 'Series', 'series', 'Lantern Bay Mysteries'), I('words', 'Words in the next book', 92000, 'int'), I('wpm', 'Words you write a month (your own number)', 40000, 'int'),
    I('lead', 'Days from finished draft to release', 110, 'int'), I('fallback', 'Gap to use when the series has one book, days', 330, 'int')], [
    O('Books released', 'int', NREL), O('Latest release', 'date', LAT), O('Average gap, days', 'int', 'ROUND(%s,0)' % AVG), O('Expected next release', 'date', 'ROUND(%s,0)' % NEXT),
    O('Writing days needed', 'int', WD), O('Start the draft by', 'date', 'ROUND(%s,0)' % STARTBY), O('Days left to start', 'int', 'ROUND(%s,0)-{today}' % STARTBY),
    O('Verdict', 'text', 'IF(ROUND(%s,0)-{today}<0,%s,IF(ROUND(%s,0)-{today}<=30,%s,%s))' % (STARTBY, v1('Late'), STARTBY, v1('Start now'), v1('On time')))],
    GR('What if you write faster or slower', ('20,000 words a month', {'wpm': 20000}), ('30,000 words a month', {'wpm': 30000}), ('40,000 words a month', {'wpm': 40000}), ('60,000 words a month', {'wpm': 60000}), ('80,000 words a month', {'wpm': 80000}))))

# 4 ------------------------------------------------------------ writing pace planner
DAYS = '({in:deadline}-{today})'
AV = 'ROUND(%s/7*%%s,0)' % DAYS
tools.append(TOOL('pace', 'Writing Pace Planner', 'Can the manuscript be finished by its deadline',
    'Type the words still to write, the deadline, your writing days a week and your own pace per writing day: Base, Best and Worst plans show the words a day needed and the verdict.', [
    I('words', 'Words still to write', 95000, 'int'), I('deadline', 'Manuscript deadline', ahead(120), 'date'), I('days_week', 'Writing days a week (Base)', 5, 'int'), I('pace', 'Words per writing day you reach (your own number)', 1000, 'int')], [
    O('Days to the deadline', 'int', DAYS), O('Writing days available, Base', 'int', AV % '{in:days_week}'), O('Words per writing day needed, Base', 'int', 'ROUND({in:words}/MAX(1,%s),0)' % (AV % '{in:days_week}')),
    O('Words per writing day needed, Best (one more day a week)', 'int', 'ROUND({in:words}/MAX(1,%s),0)' % (AV % 'MIN(7,{in:days_week}+1)')),
    O('Words per writing day needed, Worst (one day fewer)', 'int', 'ROUND({in:words}/MAX(1,%s),0)' % (AV % 'MAX(1,{in:days_week}-1)')),
    O('Your own pace per writing day', 'int', '{in:pace}'), O('Latest finish date at your pace, Base', 'date', '{today}+ROUND({in:words}/{in:pace}/{in:days_week}*7,0)'),
    O('Days to move the deadline', 'int', 'MAX(0,{today}+ROUND({in:words}/{in:pace}/{in:days_week}*7,0)-{in:deadline})'),
    O('Verdict', 'text', 'IF(ROUND({in:words}/MAX(1,%s),0)<={in:pace},%s,IF(ROUND({in:words}/MAX(1,%s),0)<={in:pace},%s,%s))' % (AV % '{in:days_week}', v1('Realistic'), AV % 'MIN(7,{in:days_week}+1)', v1('Compress the plan'), v1('Move the date')))],
    GR('What if you write fewer or more days', ('3 days a week', {'days_week': 3}), ('4 days a week', {'days_week': 4}), ('5 days a week', {'days_week': 5}), ('6 days a week', {'days_week': 6}), ('7 days a week', {'days_week': 7}))))

# 5 ------------------------------------------------------------ production lead-time planner
LT = lambda k: '{in:rel}-{in:%s}' % k
tools.append(TOOL('leadtime', 'Production Lead-Time Planner', 'When must each production job start for a release date',
    'Type the release date and the lead days each job needs (your own numbers): see the latest start date of editing, cover, formatting and narration, the days left and whether any job is already late.', [
    I('rel', 'Release date', ahead(150), 'date'), I('edit', 'Editing lead, days before release', 110, 'int'), I('cover', 'Cover lead, days', 80, 'int'), I('format', 'Formatting lead, days', 65, 'int'), I('audio', 'Narration lead, days', 100, 'int')], [
    O('Latest start, editing', 'date', LT('edit')), O('Latest start, cover design', 'date', LT('cover')), O('Latest start, formatting', 'date', LT('format')), O('Latest start, narration', 'date', LT('audio')),
    O('Days left to start editing', 'int', '(%s)-{today}' % LT('edit')), O('Days left to start the cover', 'int', '(%s)-{today}' % LT('cover')), O('Days left to start formatting', 'int', '(%s)-{today}' % LT('format')),
    O('Days left to start narration', 'int', '(%s)-{today}' % LT('audio')), O('Earliest start date of all jobs', 'date', '{in:rel}-MAX({in:edit},{in:cover},{in:format},{in:audio})'),
    O('Jobs already late', 'int', '({in:rel}-{in:edit}<{today})+({in:rel}-{in:cover}<{today})+({in:rel}-{in:format}<{today})+({in:rel}-{in:audio}<{today})'),
    O('Verdict', 'text', 'IF(({in:rel}-{in:edit}<{today})+({in:rel}-{in:cover}<{today})+({in:rel}-{in:format}<{today})+({in:rel}-{in:audio}<{today})>0,%s,%s)' % (v1('Already late'), v1('Start by the dates below')))],
    GR('What if the release moves', ('In 60 days', {'rel': '={today}+60'}), ('In 90 days', {'rel': '={today}+90'}), ('In 120 days', {'rel': '={today}+120'}), ('In 180 days', {'rel': '={today}+180'}), ('In 240 days', {'rel': '={today}+240'}))))

# 6 ------------------------------------------------------------ pre-order window planner
tools.append(TOOL('preorder', 'Pre-Order Window Planner', 'Is the pre-order window safe and long enough',
    'Type the day the pre-order opens and the release date: see the days live, the last safe upload date from your upload lead and whether the window is longer than you want.', [
    I('open', 'Pre-order opens on', ahead(3), 'date'), I('rel', 'Release date', ahead(63), 'date')], [
    O('Days live before release', 'int', '{in:rel}-{in:open}'), O('Last safe upload date', 'date', '{in:open}-{set:upload_lead_days}'), O('Days left to upload', 'int', '{in:open}-{set:upload_lead_days}-{today}'),
    O('Days until the pre-order opens', 'int', '{in:open}-{today}'), O('Longest window you want, days', 'int', '{set:preorder_max_days}'), O('Days over the longest window', 'int', 'MAX(0,{in:rel}-{in:open}-{set:preorder_max_days})'),
    O('Verdict', 'text', 'IF({in:rel}-{in:open}>{set:preorder_max_days},%s,IF({in:open}-{set:upload_lead_days}-{today}<=2,%s,%s))' % (v1('Window too long'), v1('Upload now'), v1('Safe')))],
    GR('What if the window changes', ('Opens 30 days before', {'open': '={in:rel}-30'}), ('Opens 45 days before', {'open': '={in:rel}-45'}), ('Opens 60 days before', {'open': '={in:rel}-60'}),
       ('Opens 90 days before', {'open': '={in:rel}-90'}), ('Opens 120 days before', {'open': '={in:rel}-120'}))))

# 7 ------------------------------------------------------------ edition coverage ranker
def RK(c, k): return 'IFERROR(INDEX({range:coverage.%s},MATCH(%d,{range:coverage.rank},0)),%s)' % (c, k, '"-"' if c in ('title', 'best_format') else '0')
TOPG = 'IFERROR(INDEX({range:coverage.best_gain},MATCH(1,{range:coverage.rank},0)),0)'
TOPF = 'IFERROR(INDEX({range:coverage.best_format},MATCH(1,{range:coverage.rank},0)),"")'
tools.append(TOOL('covrank', 'Edition Coverage Ranker', 'Which missing format would add the most copies',
    'Every released title missing a format is ranked by the copies a month the format would add (its own ebook copies times your own ratio for that format); the verdict names the format to add first.', [
    I('min_gain', 'Smallest gain worth acting on, copies a month', 3, 'num')], [
    O('Titles missing a format', 'int', 'COUNTIFS({range:coverage.best_gain},">0")'),
    O('First, title', 'text', RK('title', 1)), O('Second, title', 'text', RK('title', 2)), O('Third, title', 'text', RK('title', 3)), O('Fourth, title', 'text', RK('title', 4)), O('Fifth, title', 'text', RK('title', 5)),
    O('First, format to add', 'text', RK('best_format', 1)), O('Second, format to add', 'text', RK('best_format', 2)), O('Third, format to add', 'text', RK('best_format', 3)),
    O('First, copies a month added', 'num', RK('best_gain', 1)), O('Second, copies a month added', 'num', RK('best_gain', 2)), O('Third, copies a month added', 'num', RK('best_gain', 3)),
    O('Fourth, copies a month added', 'num', RK('best_gain', 4)), O('Fifth, copies a month added', 'num', RK('best_gain', 5)),
    O('Copies a month if the best format is added to all', 'num', 'SUM({range:coverage.best_gain})'),
    O('Verdict', 'text', 'IF(%s<{in:min_gain},%s,IF(%s=%s,%s,IF(%s=%s,%s,IF(%s=%s,%s,%s))))' % (TOPG, v2('Covered'), TOPF, fmt('Audiobook'), v2('Add audio first'), TOPF, fmt('Large print'), v2('Add large print first'),
        TOPF, fmt('Paperback'), v2('Add paperback first'), v2('Add hardcover first')))],
    GR('What if the bar is higher', ('Bar 1 copy', {'min_gain': 1}), ('Bar 5 copies', {'min_gain': 5}), ('Bar 10 copies', {'min_gain': 10}), ('Bar 20 copies', {'min_gain': 20}), ('Bar 40 copies', {'min_gain': 40}))))

# 8 ------------------------------------------------------------ format launch order
HASF = '(COUNTIFS({range:editions.title_id},{range:titles.title_id},{range:editions.format},{in:format},{range:editions.status},"<>"&%s)>0)' % PLN
SERR = '({range:titles.series}={in:series})*({range:titles.status}=%s)' % RELD
WITH = 'SUMPRODUCT(%s*%s)' % (SERR, HASF)
RATIO = 'IF({in:format}=%s,{set:ratio_ebook},IF({in:format}=%s,{set:ratio_paperback},IF({in:format}=%s,{set:ratio_hardcover},IF({in:format}=%s,{set:ratio_large_print},{set:ratio_audio}))))' % (fmt('Ebook'), fmt('Paperback'), fmt('Hardcover'), fmt('Large print'))
COPY = 'ROUND(SUMPRODUCT(%s*(1-%s)*{range:titles.ebook_copies_month})*%s,1)' % (SERR, HASF, RATIO)
ROYC = 'IFERROR(AVERAGEIFS({range:editions.royalty_per_copy},{range:editions.series},{in:series},{range:editions.format},{in:format},{range:editions.status},%s),IFERROR(AVERAGEIFS({range:editions.royalty_per_copy},{range:editions.format},{in:format},{range:editions.status},%s),0))' % (LIVE, LIVE)
tools.append(TOOL('fmtorder', 'Format Launch Order', 'Is it time to add this format to a series',
    'Pick a series and a format: books without it, the copies a month it would add (their ebook copies times your ratio), the royalty a month and the months to earn back its cost.', [
    IL('series', 'Series', 'series', 'The Ember Crown'), IL('format', 'Format to add', 'format', 'Large print'), I('cost', 'Cost of adding it to all those books', 760)], [
    O('Released books in the series', 'int', 'COUNTIFS({range:titles.series},{in:series},{range:titles.status},%s)' % RELD), O('Books with the format on sale', 'int', WITH),
    O('Books without it', 'int', 'COUNTIFS({range:titles.series},{in:series},{range:titles.status},%s)-%s' % (RELD, WITH)), O('Copies a month the format would add', 'num', COPY),
    O('Royalty per copy of this format', 'money', 'ROUND(%s,2)' % ROYC), O('Royalty a month added', 'money', 'ROUND(%s*%s,2)' % (COPY, ROYC)),
    O('Months to earn back the cost', 'num', 'IF(%s*%s>0,ROUND({in:cost}/(%s*%s),1),99)' % (COPY, ROYC, COPY, ROYC)),
    O('Months you accept', 'int', '{set:payback_limit_months}'),
    O('Verdict', 'text', 'IF(%s*%s>0,IF({in:cost}/(%s*%s)<={set:payback_limit_months},%s,%s),%s)' % (COPY, ROYC, COPY, ROYC, v2('Add now'), v2('Wait'), v2('Wait')))],
    GR('What if the cost changes', ('Cost 300', {'cost': 300}), ('Cost 760', {'cost': 760}), ('Cost 2,000', {'cost': 2000}), ('Cost 4,000', {'cost': 4000}), ('Cost 8,000', {'cost': 8000}))))

# 9 ------------------------------------------------------------ price consistency checker
CND = '({range:editions.series}={in:series})*({range:editions.format}={in:format})*({range:editions.status}=%s)' % LIVE
PR_ = '{range:editions.list_price}'
NN = 'SUMPRODUCT(%s)' % CND
MED = 'IF(%s=0,0,(SUMPRODUCT(LARGE(%s*%s,INT((%s+1)/2)))+SUMPRODUCT(LARGE(%s*%s,INT(%s/2)+1)))/2)' % (NN, CND, PR_, NN, CND, PR_, NN)
OUTSIDE = 'SUMPRODUCT(%s*(ABS(%s-%s)>{set:price_tolerance_pct}*%s))' % (CND, PR_, MED, MED)
tools.append(TOOL('priceconsist', 'Price Consistency Checker', 'Do editions of one format in a series share a price',
    'Pick a series and a format: live editions are set against the series median price; the editions outside your tolerance are counted and the verdict says whether to align them.', [
    IL('series', 'Series', 'series', 'Lantern Bay Mysteries'), IL('format', 'Format', 'format', 'Ebook')], [
    O('Live editions in the group', 'int', NN), O('Median list price', 'money', 'ROUND(%s,2)' % MED),
    O('Lowest list price', 'money', 'IF(%s=0,0,SUMPRODUCT(MIN(%s*%s+(1-%s)*99999)))' % (NN, CND, PR_, CND)), O('Highest list price', 'money', 'SUMPRODUCT(MAX(%s*%s))' % (CND, PR_)),
    O('Spread of the group, share of the median', 'pct', 'IF(%s=0,0,(SUMPRODUCT(MAX(%s*%s))-SUMPRODUCT(MIN(%s*%s+(1-%s)*99999)))/(%s))' % (MED, CND, PR_, CND, PR_, CND, MED)),
    O('Tolerance you accept', 'pct', '{set:price_tolerance_pct}'), O('Editions outside the tolerance', 'int', OUTSIDE),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (OUTSIDE, v2('Align the prices'), v2('Prices are consistent')))],
    GR('What if you check another group', ('Quiet Hollow Cases, ebook', {'series': '=' + sr('Quiet Hollow Cases')}), ('The Ember Crown, ebook', {'series': '=' + sr('The Ember Crown')}),
       ('Tidebound Realms, ebook', {'series': '=' + sr('Tidebound Realms')}), ('Lantern Bay, paperback', {'format': '=' + fmt('Paperback')}), ('Lantern Bay, audiobook', {'format': '=' + fmt('Audiobook')}))))

# 10 ----------------------------------------------------------- price per page test
OWN = 'IFERROR(AVERAGEIFS({range:pricepage.price_per_page},{range:pricepage.format},{in:format}),0)'
PPP = '{in:price}/{in:pages}*100'
tools.append(TOOL('ppp', 'Price per Page Test', 'Is a print price fair for the page count',
    'Type a print price, page count and unit cost: the price per 100 pages is set against your own average for that format, with the print cost share and the price that holds your cost share limit.', [
    IL('format', 'Format', 'format', 'Paperback'), I('price', 'Planned list price', 14.99), I('pages', 'Pages', 320, 'int'), I('cost', 'Unit cost of one printed copy', 5.2)], [
    O('Price per 100 pages', 'money', 'ROUND(%s,2)' % PPP), O('Your own average per 100 pages, this format', 'money', 'ROUND(%s,2)' % OWN),
    O('Difference from your own average', 'pct', 'IF(%s>0,(%s)/%s-1,0)' % (OWN, PPP, OWN)), O('Print cost share of the price', 'pct', '{in:cost}/{in:price}'),
    O('Highest cost share you accept', 'pct', '{set:print_cost_share_max}'), O('Price that holds the cost share limit', 'money', 'ROUND({in:cost}/{set:print_cost_share_max},2)'),
    O('Price at your own average per page', 'money', 'ROUND(%s*{in:pages}/100,2)' % OWN),
    O('Verdict', 'text', 'IF(%s>0,IF((%s)/%s-1>{set:price_tolerance_pct},%s,IF((%s)/%s-1<-{set:price_tolerance_pct},%s,%s)),%s)' % (OWN, PPP, OWN, v2('Price high'), PPP, OWN, v2('Price low'), v2('Price fair'), v2('Price fair')))],
    GR('What if the price changes', ('Price 9.99', {'price': 9.99}), ('Price 12.99', {'price': 12.99}), ('Price 14.99', {'price': 14.99}), ('Price 16.99', {'price': 16.99}), ('Price 19.99', {'price': 19.99}))))

# 11 ----------------------------------------------------------- identifier and field gap finder
def PB(c, k): return 'IFERROR(INDEX({range:completeness.%s},MATCH(%d,{range:completeness.problem_rank},0)),%s)' % (c, k, '"-"' if c == 'edition_id' else ck('No problem'))
tools.append(TOOL('gapfinder', 'Identifier and Field Gap Finder', 'Are the editions ready to upload',
    'Counts the editions with a missing or duplicated identifier, a missing price, pages or release date, and lists the first five problems to fix before you upload; planned editions are not checked.', [
    I('limit', 'Editions with a problem you accept', 0, 'int')], [
    O('Editions checked', 'int', 'COUNTA({range:editions.edition_id})-COUNTIFS({range:editions.status},%s)' % PLN), O('Identifiers missing', 'int', 'SUM({range:completeness.id_missing})'),
    O('Identifiers used twice', 'int', 'SUM({range:completeness.id_dup})'), O('Prices missing', 'int', 'SUM({range:completeness.price_missing})'),
    O('Pages or hours missing', 'int', 'SUM({range:completeness.pages_missing})'), O('Release dates missing', 'int', 'SUM({range:completeness.date_missing})'),
    O('Editions with a problem', 'int', 'COUNTIFS({range:completeness.problems},">0")')] +
    [O('Problem %d, edition' % k, 'text', PB('edition_id', k)) for k in range(1, 6)] + [O('Problem %d, what to fix' % k, 'text', PB('issue', k)) for k in range(1, 6)] + [
    O('Verdict', 'text', 'IF(COUNTIFS({range:completeness.problems},">0")<={in:limit},%s,%s)' % (v2('Clean'), v2('Fix before upload')))],
    GR('What if you accept more', ('Accept 0', {'limit': 0}), ('Accept 2', {'limit': 2}), ('Accept 4', {'limit': 4}), ('Accept 5', {'limit': 5}), ('Accept 8', {'limit': 8}))))

# 12 ----------------------------------------------------------- release spacing scenario
N0 = TI('release_date')
OTH = '({range:titles.title_id}<>{in:tid})*(%s>0)' % REL
def G(s): return 'SUMPRODUCT(MIN(ABS(%s+(%s)-%s)*%s+(1-%s)*99999))' % (N0, s, REL, OTH, OTH)
tools.append(TOOL('spacing', 'Release Spacing Scenario', 'Which move keeps a release clear of the others',
    'Pick a title and a move in days: see the new date, the smallest gap to another release and the conflicts left; five moves from -30 to +30 days are tried and the smallest that clears the gap named.', [
    IN('tid', 'Title ID, for example TL-018', 'text', 'TL-018'), I('shift', 'Move by, days', 0, 'int')], [
    O('Title', 'text', TI('title')), O('Release date now', 'date', N0), O('Release date after the move', 'date', '%s+{in:shift}' % N0),
    O('Smallest gap to another release after the move', 'int', G('{in:shift}')),
    O('Releases inside the minimum gap after the move', 'int', 'COUNTIFS(%s,">"&(%s+{in:shift}-%s),%s,"<"&(%s+{in:shift}+%s),{range:titles.title_id},"<>"&{in:tid})' % (REL, N0, GAP, REL, N0, GAP)),
    O('Smallest gap if moved -30 days', 'int', G('-30')), O('Smallest gap if moved -15 days', 'int', G('-15')), O('Smallest gap if not moved', 'int', G('0')),
    O('Smallest gap if moved +15 days', 'int', G('15')), O('Smallest gap if moved +30 days', 'int', G('30')),
    O('Smallest move that clears the gap (999 means none)', 'int', 'IF(%s>=%s,0,IF(%s>=%s,15,IF(%s>=%s,-15,IF(%s>=%s,30,IF(%s>=%s,-30,999)))))' % (G('0'), GAP, G('15'), GAP, G('-15'), GAP, G('30'), GAP, G('-30'), GAP)),
    O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (G('0'), GAP, v2('Keep the date'), v2('Move the release')))],
    GR('What if the release moves', ('Move -30 days', {'shift': -30}), ('Move -15 days', {'shift': -15}), ('No move', {'shift': 0}), ('Move +15 days', {'shift': 15}), ('Move +30 days', {'shift': 30}))))

# 13 ----------------------------------------------------------- calendar load by month
def CMR(c, k): return 'IFERROR(INDEX({range:calmonths.%s},MATCH(%d,{range:calmonths.rank},0)),0)' % (c, k)
tools.append(TOOL('load', 'Calendar Load by Month', 'Which months are too busy',
    'Months are ranked busiest first by releases, pre-orders, promotions, planned editions and contractor deadlines against the load you can carry; the verdict says whether to spread the work.', [
    I('limit', 'Entries a month you can carry', 6, 'int')], [
    O('Busiest month', 'date', CMR('month', 1)), O('Second busiest month', 'date', CMR('month', 2)), O('Third busiest month', 'date', CMR('month', 3)), O('Fourth busiest month', 'date', CMR('month', 4)),
    O('Entries in the busiest month', 'int', CMR('entries', 1)), O('Entries in the second month', 'int', CMR('entries', 2)), O('Entries in the third month', 'int', CMR('entries', 3)), O('Entries in the fourth month', 'int', CMR('entries', 4)),
    O('Months at or over the limit', 'int', 'COUNTIFS({range:calmonths.entries},">="&{in:limit})'), O('Entries over the limit in the busiest month', 'int', 'MAX(0,%s-{in:limit})' % CMR('entries', 1)),
    O('Releases in the busiest month', 'int', CMR('releases', 1)), O('Deadlines in the busiest month', 'int', CMR('deadlines', 1)),
    O('Verdict', 'text', 'IF(COUNTIFS({range:calmonths.entries},">="&{in:limit})>0,%s,%s)' % (v3('Spread the work'), v3('Load is ok')))],
    GR('What if the limit changes', ('Limit 4', {'limit': 4}), ('Limit 5', {'limit': 5}), ('Limit 6', {'limit': 6}), ('Limit 8', {'limit': 8}), ('Limit 10', {'limit': 10}))))

# 14 ----------------------------------------------------------- series reader wait check
SERC = '({range:titles.series}={in:series})'
FIRSTD = 'SUMPRODUCT(MIN(%s*(%s<={today})*%s+(1-%s*(%s<={today}))*999999))' % (SERC, REL, REL, SERC, REL)
LASTD = 'SUMPRODUCT(MAX(%s*(%s<={today})*%s))' % (SERC, REL, REL)
NXTD = 'SUMPRODUCT(MIN(%s*(%s>{today})*%s+(1-%s*(%s>{today}))*999999))' % (SERC, REL, REL, SERC, REL)
NB_ = 'COUNTIFS({range:titles.series},{in:series},%s,"<="&{today})' % REL
AVGM = 'IF(%s>1,(%s-%s)/(%s-1)/30.4,0)' % (NB_, LASTD, FIRSTD, NB_)
WAITN = 'IF(%s>900000,({today}-%s)/30.4,(%s-%s)/30.4)' % (NXTD, LASTD, NXTD, LASTD)
tools.append(TOOL('readerwait', 'Series Reader Wait Check', 'Are readers waiting too long between books',
    'Pick a series: the gap between its books and the months readers wait for the next one are set against the longest wait you accept, with a verdict.', [
    IL('series', 'Series', 'series', 'Tidebound Realms')], [
    O('Books released', 'int', NB_), O('First release', 'date', FIRSTD), O('Latest release', 'date', LASTD), O('Average gap between books, months', 'num', 'ROUND(%s,1)' % AVGM),
    O('Months since the latest release', 'num', 'ROUND(({today}-%s)/30.4,1)' % LASTD), O('Months the wait for the next book will be', 'num', 'ROUND(%s,1)' % WAITN),
    O('Longest wait you accept, months', 'int', '{set:reader_wait_months}'),
    O('Verdict', 'text', 'IF(MAX(%s,%s)>{set:reader_wait_months},%s,%s)' % (AVGM, WAITN, v3('Readers wait too long'), v3('Wait is ok')))],
    GR('What if you check another series', ('Lantern Bay Mysteries', {'series': '=' + sr('Lantern Bay Mysteries')}), ('Quiet Hollow Cases', {'series': '=' + sr('Quiet Hollow Cases')}),
       ('The Ember Crown', {'series': '=' + sr('The Ember Crown')}), ('Tidebound Realms', {'series': '=' + sr('Tidebound Realms')}), ('Standalone titles', {'series': '=' + sr('Standalone')}))))

# 15 ----------------------------------------------------------- pen-name balance check
P1, P2 = tok('penname', 'Tamsin Hartwell'), tok('penname', 'Corvin Ashdale')
WIN = '{range:titles.release_date},">="&EDATE({today},-{in:months}),{range:titles.release_date},"<="&{today}'
R1 = 'COUNTIFS({range:titles.pen_name},%s,%s)' % (P1, WIN); R2 = 'COUNTIFS({range:titles.pen_name},%s,%s)' % (P2, WIN)
SH1 = 'IF(%s+%s=0,0,%s/(%s+%s))' % (R1, R2, R1, R1, R2)
tools.append(TOOL('penbal', 'Pen-Name Balance Check', 'Is one pen name being starved of releases',
    'Titles, words, releases in your window and earlier royalties for both pen names, set against the share of releases you want for the first; the verdict says which pen name to feed.', [
    I('target', 'Share of releases you want for the first pen name', 0.5, 'pct'), I('months', 'Look-back window, months', 14, 'int'), I('tol', 'Difference you accept', 0.10, 'pct')], [
    O('Titles, first pen name', 'int', 'COUNTIFS({range:titles.pen_name},%s)' % P1), O('Titles, second pen name', 'int', 'COUNTIFS({range:titles.pen_name},%s)' % P2),
    O('Words, first pen name', 'int', 'SUMIFS({range:titles.words},{range:titles.pen_name},%s)' % P1), O('Words, second pen name', 'int', 'SUMIFS({range:titles.words},{range:titles.pen_name},%s)' % P2),
    O('Releases in the window, first pen name', 'int', R1), O('Releases in the window, second pen name', 'int', R2),
    O('Royalties before this workbook, first pen name', 'money', 'SUMIFS({range:titles.royalty_before},{range:titles.pen_name},%s)' % P1),
    O('Royalties before this workbook, second pen name', 'money', 'SUMIFS({range:titles.royalty_before},{range:titles.pen_name},%s)' % P2),
    O('Share of releases, first pen name', 'pct', SH1), O('Difference from your target', 'pct', '%s-{in:target}' % SH1),
    O('Verdict', 'text', 'IF(%s<{in:target}-{in:tol},%s,IF(%s>{in:target}+{in:tol},%s,%s))' % (SH1, v3('Feed Tamsin Hartwell'), SH1, v3('Feed Corvin Ashdale'), v3('Balanced')))],
    GR('What if the window changes', ('Window 6 months', {'months': 6}), ('Window 12 months', {'months': 12}), ('Window 14 months', {'months': 14}), ('Window 24 months', {'months': 24}), ('Window 36 months', {'months': 36}))))

# 16 ----------------------------------------------------------- backlist price refresh screen
def OLD(c, k): return 'IFERROR(INDEX({range:storeprices.%s},MATCH(LARGE({range:storeprices.backlist_key},%d),{range:storeprices.backlist_key},0)),%s)' % (c, k, '"-"' if c != 'days_since' else '0')
tools.append(TOOL('refresh', 'Backlist Price Refresh Screen', 'Which backlist prices have not been checked for too long',
    'Store prices of titles on sale for the backlist months you set are ranked by the days since the check; those past your day limit are counted and the oldest four are named.', [
    I('days', 'Days since the check that count as old', 180, 'int')], [
    O('Backlist price rows', 'int', 'COUNT({range:storeprices.backlist_key})'), O('Rows past the day limit', 'int', 'COUNTIFS({range:storeprices.backlist_key},">="&{in:days})')] +
    [O('Oldest %d, edition' % k, 'text', OLD('edition_id', k)) for k in range(1, 5)] + [O('Oldest %d, store' % k, 'text', OLD('store', k)) for k in range(1, 5)] +
    [O('Oldest %d, days since the check' % k, 'int', 'IFERROR(INT(LARGE({range:storeprices.backlist_key},%d)),0)' % k) for k in range(1, 3)] + [
    O('Verdict', 'text', 'IF(COUNTIFS({range:storeprices.backlist_key},">="&{in:days})>0,%s,%s)' % (v3('Refresh prices'), v3('Prices up to date')))],
    GR('What if the limit changes', ('Limit 60 days', {'days': 60}), ('Limit 120 days', {'days': 120}), ('Limit 180 days', {'days': 180}), ('Limit 270 days', {'days': 270}), ('Limit 365 days', {'days': 365}))))

# 17 ----------------------------------------------------------- pre-order readiness check
TT = TI('title')
SAFE = '(%s-{in:window}-{set:upload_lead_days})' % TI('release_date')
JOBS = '{range:deadlines.title},%s' % TT
tools.append(TOOL('readiness', 'Pre-Order Readiness Check', 'Will the files be ready before the pre-order opens',
    'Type a title ID and the days before release that the pre-order opens: its production jobs are counted as delivered, open, late and due after the last safe upload date, with a verdict.', [
    IN('tid', 'Title ID, for example TL-018', 'text', 'TL-018'), I('window', 'Pre-order opens, days before release', 60, 'int')], [
    O('Title', 'text', TT), O('Release date', 'date', TI('release_date')), O('Days to release', 'int', '%s-{today}' % TI('release_date')),
    O('Last safe upload date', 'date', SAFE), O('Jobs on this title in the deadline list', 'int', 'COUNTIFS(%s)' % JOBS),
    O('Jobs delivered', 'int', 'COUNTIFS(%s,{range:deadlines.delivered_on},">0")' % JOBS), O('Jobs still open', 'int', 'COUNTIFS(%s,{range:deadlines.delivered_on},"")' % JOBS),
    O('Open jobs already late', 'int', 'COUNTIFS(%s,{range:deadlines.delivered_on},"",{range:deadlines.due_date},"<"&{today})' % JOBS),
    O('Open jobs due after the last safe upload', 'int', 'COUNTIFS(%s,{range:deadlines.delivered_on},"",{range:deadlines.due_date},">"&%s)' % (JOBS, SAFE)),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,{range:deadlines.delivered_on},"",{range:deadlines.due_date},"<"&{today})+COUNTIFS(%s,{range:deadlines.delivered_on},"",{range:deadlines.due_date},">"&%s)>0,%s,%s)' % (JOBS, JOBS, SAFE, v3('Pre-order is at risk'), v3('Pre-order is safe')))],
    GR('What if the pre-order opens earlier or later', ('Opens 30 days before', {'window': 30}), ('Opens 45 days before', {'window': 45}), ('Opens 60 days before', {'window': 60}), ('Opens 75 days before', {'window': 75}), ('Opens 90 days before', {'window': 90}))))

# 18 ----------------------------------------------------------- planned edition go list
def WK(c, k, fb): return 'IFERROR(INDEX({range:wishlist.%s},MATCH(%d,{range:wishlist.rank},0)),%s)' % (c, k, fb)
tools.append(TOOL('golist', 'Planned Edition Go List', 'Which planned edition should be made first',
    'The format wish list is ranked by the royalty a month per unit of cost; planned editions that earn back their cost inside your months limit are counted and the first in line gets a verdict.', [
    I('limit', 'Months you accept to earn back the cost', 12, 'int')], [
    O('Planned editions on the list', 'int', 'COUNTA({range:wishlist.wish_id})'), O('Planned editions inside the limit', 'int', 'COUNTIFS({range:wishlist.months_to_earn},"<="&{in:limit})'),
    O('Cost of those editions', 'money', 'SUMIFS({range:wishlist.planned_cost},{range:wishlist.months_to_earn},"<="&{in:limit})'),
    O('Royalty a month from those editions', 'money', 'SUMIFS({range:wishlist.royalty_month},{range:wishlist.months_to_earn},"<="&{in:limit})')] +
    [O('Rank %d, title' % k, 'text', WK('title', k, '"-"')) for k in range(1, 5)] + [O('Rank %d, format' % k, 'text', WK('format', k, '"-"')) for k in range(1, 5)] +
    [O('Rank %d, months to earn back' % k, 'num', WK('months_to_earn', k, '99')) for k in range(1, 4)] + [
    O('Verdict', 'text', 'IF(%s<={in:limit},%s,IF(%s<=2*{in:limit},%s,%s))' % (WK('months_to_earn', 1, '99'), ck('Do now'), WK('months_to_earn', 1, '99'), ck('Next quarter'), ck('Drop')))],
    GR('What if you accept longer', ('Limit 6 months', {'limit': 6}), ('Limit 9 months', {'limit': 9}), ('Limit 12 months', {'limit': 12}), ('Limit 18 months', {'limit': 18}), ('Limit 24 months', {'limit': 24}))))
assert len(tools) == 18, len(tools)
