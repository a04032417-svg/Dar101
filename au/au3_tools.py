"""Part 3: the 18 decision tools (verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au3_lists import *
import au3_data as D

def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
M1 = 'EDATE(%s,-1)' % MS
ST = story()
def ROY_M(m, extra=''): return 'SUMIFS({range:mstore.royalty_home},{range:mstore.month},%s%s)' % (m, extra)
def ROY_R(a, b, extra=''): return 'SUMIFS({range:mstore.royalty_home},{range:mstore.month},">="&%s,{range:mstore.month},"<"&%s%s)' % (a, b, extra)
def ST_R(store): return ',{range:mstore.store},%s' % store
def PRI_R(a, b): return 'SUMIFS({range:pagereads.income},{range:pagereads.month},">="&%s,{range:pagereads.month},"<"&%s)' % (a, b)
EXP, OPN = tok('ststatus', 'Expected'), tok('ststatus', 'Open')
def S_SUM(col, store, month): return 'SUMIFS({range:statements.%s},{range:statements.store},%s,{range:statements.month},%s)' % (col, store, month)
tools = []

# 1 ------------------------------------------------------------ earned against paid reconciler
STM = S_SUM('statement_amount', '{in:store}', '{in:month}'); REC = S_SUM('received', '{in:store}', '{in:month}'); PAID = S_SUM('paid_on', '{in:store}', '{in:month}'); EXPD = S_SUM('expected_on', '{in:store}', '{in:month}')
UNEX = 'SUMIFS({range:payments.unexplained},{range:payments.store},{in:store},{range:payments.month},{in:month})'
story_month = ST['statement']['month']
def SG(lbl, st, mo): return (lbl, {'store': '=' + tok('store', st), 'month': '=EDATE(%s,%d)' % (MS, mo)})
tools.append(TOOL('recon', 'Earned Against Paid Reconciler', 'Did this store pay what it earned for this month',
    'Pick a store and a month: the statement, the amount received, the difference, the part that fees do not explain and the days past the expected date, with a verdict.', [
    IL('store', 'Store', 'store', 'Wide distribution'), I('month', 'Month of the statement (first day)', story_month, 'date')], [
    O('Statement amount', 'money', STM), O('Amount received', 'money', REC), O('Difference', 'money', '(%s)-(%s)' % (STM, REC)), O('Short, not explained by fees', 'money', UNEX),
    O('Expected on', 'date', 'IF(%s=0,"-",%s)' % (EXPD, EXPD)), O('Paid on', 'date', 'IF(%s=0,"-",%s)' % (PAID, PAID)),
    O('Days past the expected date', 'int', 'IF(%s>0,%s-%s,MAX(0,{today}-%s))' % (PAID, PAID, EXPD, EXPD)),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s>0,IF(%s>{set:short_tolerance},%s,%s),IF({today}>%s,%s,%s)))' % (STM, tok('v1', 'No statement'), PAID, UNEX, tok('v1', 'Short-paid'), tok('v1', 'Paid in full'), EXPD, tok('v1', 'Overdue'), tok('v1', 'Not yet due')))],
    GR('What if', SG('Ebook store, 3 months back', 'Ebook store', -3), SG('Print-on-demand, 2 months back', 'Print-on-demand', -2), SG('Library and lending, last month', 'Library and lending', -1),
       SG('Wide distribution, 4 months back', 'Wide distribution', -4), SG('Direct store, 2 months back', 'Direct store', -2))))

# 2 ------------------------------------------------------------ overdue statement ranker
DPR = '{range:oldest.days_past}'
def RK(k, what):
    dp = 'LARGE(%s,%d)' % (DPR, k)
    nm = 'INDEX({range:oldest.store},MATCH(%s,%s,0))' % (dp, DPR)
    owed = 'SUMIFS({range:statements.statement_amount},{range:statements.store},%s,{range:statements.status},%s)+SUMIFS({range:statements.statement_amount},{range:statements.store},%s,{range:statements.status},%s)' % (nm, EXP, nm, OPN)
    days = 'ROUND(%s,0)+{in:shift}' % dp
    if what == 'store': return nm
    if what == 'days': return days
    if what == 'owed': return owed
    return 'IF(%s<=0,%s,IF(%s<={set:escalate_days},%s,%s))' % (days, tok('v1', 'Wait'), days, tok('v1', 'Write today'), tok('v1', 'Escalate'))
outs = []
for k in (1, 2, 3):
    outs += [O('Store ranked %d' % k, 'text', RK(k, 'store')), O('Days past expected, rank %d' % k, 'int', RK(k, 'days')), O('Amount unpaid, rank %d' % k, 'money', RK(k, 'owed')), O('Verdict, rank %d' % k, 'text', RK(k, 'v'))]
outs += [O('Unpaid amount, all stores', 'money', 'SUMIFS({range:statements.statement_amount},{range:statements.status},%s)+SUMIFS({range:statements.statement_amount},{range:statements.status},%s)' % (EXP, OPN)),
         O('Stores to write to or escalate', 'int', 'COUNTIFS(%s,">"&(-{in:shift}))' % DPR), O('Short-paid amount still to claim', 'money', 'SUMIFS({range:statements.short_by},{range:statements.status},%s)' % tok('ststatus', 'Short-paid'))]
tools.append(TOOL('overdue_rank', 'Overdue Statement Ranker', 'Which store to write to first',
    'Stores are ranked by the days past the expected date of their oldest unpaid month, with the unpaid amount and a verdict to wait, write today or escalate. Add days to test a slower month.', [
    I('shift', 'Days to add to every store (what if)', 0, 'int')], outs,
    GR('What if the money were this many days later', ('Add 30 days', {'shift': 30}), ('Add 60 days', {'shift': 60}), ('Add 90 days', {'shift': 90}), ('Add 120 days', {'shift': 120}))))

# 3 ------------------------------------------------------------ short-payment finder
DIFF = '({range:payments.statement_amount}-{range:payments.fee}-{range:payments.fx_loss}-{range:payments.received})'
LAR = 'SUMPRODUCT(MAX(%s))' % DIFF
ROWL = 'SUMPRODUCT(MATCH(%s,%s,0))' % (LAR, DIFF)
tools.append(TOOL('short_finder', 'Short-Payment Finder', 'Which payments came in short, and what to claim',
    'Every payment under its statement by more than the fees and your tolerance: how many, the amount to claim in total, the largest one and its store, with a verdict.', [
    I('tol', 'Tolerance, amount', 5.0)], [
    O('Payments checked', 'int', 'COUNTA({range:payments.payment_id})'), O('Payments short beyond the tolerance', 'int', 'SUMPRODUCT(--(%s>{in:tol}))' % DIFF),
    O('Amount to claim in total', 'money', 'SUMPRODUCT((%s>{in:tol})*%s)' % (DIFF, DIFF)), O('Largest shortfall', 'money', LAR),
    O('Store of the largest', 'text', 'IF(%s<={in:tol},"-",INDEX({range:payments.store},%s))' % (LAR, ROWL)),
    O('Month of the largest', 'date', 'IF(%s<={in:tol},"-",INDEX({range:payments.month},%s))' % (LAR, ROWL)),
    O('Payment of the largest', 'text', 'IF(%s<={in:tol},"-",INDEX({range:payments.payment_id},%s))' % (LAR, ROWL)),
    O('Small gaps within the tolerance', 'int', 'SUMPRODUCT((%s>0.005)*(%s<={in:tol}))' % (DIFF, DIFF)),
    O('Verdict', 'text', 'IF(SUMPRODUCT(--(%s>{in:tol}))>0,%s,%s)' % (DIFF, tok('v1', 'Claim now'), tok('v1', 'Within tolerance')))],
    GR('What if the tolerance were', ('0.50', {'tol': 0.5}), ('25', {'tol': 25}), ('100', {'tol': 100}), ('400', {'tol': 400}), ('1,000', {'tol': 1000}))))

# 4 ------------------------------------------------------------ expected cash by pay month
def PS(n): return '{today}' if n == 1 else 'EDATE(%s,%d)' % (MS, n - 1)
def PE(n): return 'EDATE(%s,%d)' % (MS, n)
AVG3 = 'SUMIFS({range:mstore.royalty_home},{range:mstore.store},{range:stores.store},{range:mstore.month},">="&EDATE(%s,-3),{range:mstore.month},"<"&%s)/3' % (MS, MS)
def BASE(n):
    known = 'SUMIFS({range:statements.statement_amount},{range:statements.status},%s,{range:statements.expected_on},">="&%s,{range:statements.expected_on},"<"&%s)+SUMIFS({range:statements.statement_amount},{range:statements.status},%s,{range:statements.expected_on},">="&%s,{range:statements.expected_on},"<"&%s)' % (EXP, PS(n), PE(n), OPN, PS(n), PE(n))
    proj = '+'.join('SUMPRODUCT(({range:stores.delay_days}+EOMONTH(%s,%d)>=%s)*({range:stores.delay_days}+EOMONTH(%s,%d)<%s)*(%s))' % (MS, k, PS(n), MS, k, PE(n), AVG3) for k in (1, 2, 3))
    return '(%s)+%s' % (known, proj)
outs = []
for n in range(1, 5): outs.append(O('Base, month %d' % n, 'money', BASE(n)))
for n in range(1, 5): outs.append(O('Best, month %d' % n, 'money', '(%s)*(1+{in:up})' % BASE(n)))
for n in range(1, 5): outs.append(O('Worst, month %d' % n, 'money', '(%s)*(1-{in:down})' % BASE(n)))
for n in range(1, 5): outs.append(O('Verdict, month %d (Base)' % n, 'text', 'IF(%s<{in:need},%s,%s)' % (BASE(n), tok('v2', 'Gap in month %d' % n), tok('v2', 'Cash arrives as planned'))))
tools.append(TOOL('cash_pay', 'Expected Cash by Pay Month', 'What lands in the bank in each of the next 4 months',
    'Unpaid statements by expected date plus the 3-month average for months not yet reported, each store with its own delay: Base, Best, Worst and a verdict per month. Estimates until paid.', [
    I('need', 'Royalty cash you need each month', 6000.0), I('up', 'Best case, change', 0.10, 'pct'), I('down', 'Worst case, change', 0.15, 'pct')], outs,
    GR('What if you need', ('4,000 a month', {'need': 4000}), ('8,000 a month', {'need': 8000}), ('10,000 a month', {'need': 10000}), ('Worst case 30% lower', {'down': 0.30}))))

# 5 ------------------------------------------------------------ fee and exchange loss tool
COST = '({in:fixed}+{in:size}*{in:pct}+{in:size}*{in:fx})'
tools.append(TOOL('fee_tool', 'Fee and Exchange Loss Tool', 'Are fees eating this payment',
    'Type the payment size, the fixed fee, the percent fee and the exchange loss: what you keep, the share fees take, the smallest payment under your flag and the saving from batching.', [
    I('size', 'Payment size', 300.0), I('fixed', 'Fixed fee per payment', 10.0), I('pct', 'Percent fee', 0.0, 'pct'), I('fx', 'Exchange loss', 0.006, 'pct'), I('per_year', 'Payments a year', 12, 'int')], [
    O('Fixed fee', 'money', '{in:fixed}'), O('Percent fee amount', 'money', '{in:size}*{in:pct}'), O('Exchange loss amount', 'money', '{in:size}*{in:fx}'), O('Total cost of the payment', 'money', COST),
    O('You keep', 'money', '{in:size}-%s' % COST), O('Cost, share of the payment', 'pct', 'IF({in:size}=0,0,%s/{in:size})' % COST), O('Your flag limit', 'pct', '{set:fee_flag_pct}'),
    O('Smallest payment under the limit', 'money', 'IF({set:fee_flag_pct}>{in:pct}+{in:fx},{in:fixed}/({set:fee_flag_pct}-{in:pct}-{in:fx}),0)'),
    O('Cost over a year as it is', 'money', '%s*{in:per_year}' % COST), O('Cost over a year in 4 batched payments', 'money', '4*{in:fixed}+{in:size}*{in:per_year}*({in:pct}+{in:fx})'),
    O('Saved by batching', 'money', '%s*{in:per_year}-(4*{in:fixed}+{in:size}*{in:per_year}*({in:pct}+{in:fx}))' % COST),
    O('Verdict', 'text', 'IF({in:size}=0,%s,IF(%s/{in:size}>{set:fee_flag_pct},%s,%s))' % (tok('v2', 'Batch payments'), COST, tok('v2', 'Batch payments'), tok('v2', 'Fine')))],
    GR('What if the payment were', ('150', {'size': 150}), ('600', {'size': 600}), ('1,200', {'size': 1200}), ('2,400', {'size': 2400}), ('2,400 with a 1.5% fee', {'size': 2400, 'pct': 0.015}))))

# 6 ------------------------------------------------------------ payout threshold optimiser
KMIN = 'MAX(1,ROUNDUP({in:minimum}/{in:monthly},0))'
KOPT = 'MIN(12,MAX(%s,ROUND(SQRT(2*{in:fee}/({in:wait}*{in:monthly})),0)))' % KMIN
tools.append(TOOL('payout', 'Payout Threshold Optimiser', 'How often to withdraw from a store',
    'Type the fee per withdrawal, the minimum payout, the royalties a month and what waiting costs you: the best number of months between withdrawals, the fee saved a year and a verdict.', [
    I('fee', 'Fee per withdrawal', 8.0), I('minimum', 'Minimum payout', 100.0), I('monthly', 'Royalties a month at this store', 180.0), I('wait', 'Cost of waiting, per month on the balance held', 0.005, 'pct')], [
    O('Months to reach the minimum', 'int', KMIN), O('Best interval from the numbers', 'int', 'MIN(12,ROUND(SQRT(2*{in:fee}/({in:wait}*{in:monthly})),0))'), O('Months between withdrawals', 'int', KOPT),
    O('Withdrawals a year', 'num', '12/(%s)' % KOPT), O('Fees a year at that interval', 'money', '12*{in:fee}/(%s)' % KOPT), O('Fees a year if you withdraw monthly', 'money', '12*{in:fee}'),
    O('Fees saved a year', 'money', '12*{in:fee}-12*{in:fee}/(%s)' % KOPT), O('Cost of waiting a year', 'money', '12*{in:wait}*{in:monthly}*((%s)-1)/2' % KOPT),
    O('Net saving a year', 'money', '12*{in:fee}-12*{in:fee}/(%s)-12*{in:wait}*{in:monthly}*((%s)-1)/2' % (KOPT, KOPT)),
    O('Verdict', 'text', 'CHOOSE(%s,%s)' % (KOPT, ','.join(tok('v5', l) for l in V5)))],
    GR('What if royalties a month were', ('60', {'monthly': 60}), ('120', {'monthly': 120}), ('400', {'monthly': 400}), ('900', {'monthly': 900}), ('Minimum payout 250', {'minimum': 250}))))

# 7 ------------------------------------------------------------ royalty per copy by edition and store
_ped = [e for e in D.EDS if e['title_id'] == 'TL-001' and e['format'] == 'Paperback'][0]['edition_id']
EDL = lambda c: 'INDEX({range:editions.%s},MATCH({in:edition},{range:editions.edition_id},0))' % c
PRICE = '(%s*(1+{in:change}))' % EDL('list_price'); SHARE = 'SUMIFS({range:stores.royalty_share},{range:stores.store},{in:store})'
tools.append(TOOL('roy_copy', 'Royalty per Copy Calculator', 'Does this price hold your royalty per copy',
    'Type an edition id, a store and a price change: the royalty per copy (price x store share - cost of a copy) and the price that holds your target royalty, with a verdict.', [
    I('edition', 'Edition ID', _ped, 'text'), IL('store', 'Store', 'store', 'Print-on-demand'), I('change', 'Price change', 0.0, 'pct'), I('target', 'Royalty per copy you want', 3.5)], [
    O('Title', 'text', EDL('title')), O('Format', 'text', EDL('format')), O('List price', 'money', EDL('list_price')), O('Price after the change', 'money', PRICE), O('Cost of one copy', 'money', EDL('unit_cost')),
    O('Store share (check current terms)', 'pct', SHARE), O('Royalty per copy', 'money', '%s*%s-%s' % (PRICE, SHARE, EDL('unit_cost'))), O('Royalty, share of the price', 'pct', '(%s*%s-%s)/%s' % (PRICE, SHARE, EDL('unit_cost'), PRICE)),
    O('Price that holds the target', 'money', '(({in:target}+%s)/%s)' % (EDL('unit_cost'), SHARE)), O('Raise the price by', 'money', 'MAX(0,(({in:target}+%s)/%s)-%s)' % (EDL('unit_cost'), SHARE, PRICE)),
    O('Verdict', 'text', 'IF(%s*%s-%s>={in:target},%s,%s)' % (PRICE, SHARE, EDL('unit_cost'), tok('v2', 'Price holds'), tok('v2', 'Raise the price')))],
    GR('What if', ('Price down 10%', {'change': -0.10}), ('Price down 5%', {'change': -0.05}), ('Price up 5%', {'change': 0.05}), ('Price up 10%', {'change': 0.10}), ('Sold at the wide distribution service', {'store': '=' + tok('store', 'Wide distribution')}))))

# 8 ------------------------------------------------------------ page-read income estimator
_pg = sum(x['pages_read'] for x in D.PRD if x['month'] == iso(month_start(1)))
INC = '({in:pages}/1000*{in:rate})'
ALLR = ROY_M(M1)
tools.append(TOOL('pr_est', 'Page-Read Income Estimator', 'How much does the page-read rate matter',
    'Type the pages read and the pay per 1,000 pages (an estimate until paid): income at the rate minus and plus 10% and 20%, its share of all royalties and a verdict.', [
    I('pages', 'Pages read in the month', _pg, 'int'), I('rate', 'Pay per 1,000 pages', 4.2, 'num'), I('risk', 'Loss you accept, share of all income', 0.01, 'pct')], [
    O('Income at this rate', 'money', INC), O('At the rate minus 20%', 'money', INC + '*0.8'), O('At the rate minus 10%', 'money', INC + '*0.9'), O('At the rate plus 10%', 'money', INC + '*1.1'), O('At the rate plus 20%', 'money', INC + '*1.2'),
    O('Royalties of last month, all stores', 'money', ALLR), O('Page-read share of all income', 'pct', 'IFERROR(%s/(%s+%s),0)' % (INC, INC, ALLR)),
    O('Lost at minus 20%', 'money', INC + '*0.2'), O('Lost at minus 20%, share of all income', 'pct', 'IFERROR(%s*0.2/(%s+%s),0)' % (INC, INC, ALLR)),
    O('Your own pay per 1,000 pages, last 3 months', 'num', 'IFERROR(%s/SUMIFS({range:pagereads.pages_read},{range:pagereads.month},">="&EDATE(%s,-3),{range:pagereads.month},"<"&%s)*1000,0)' % (PRI_R('EDATE(%s,-3)' % MS, MS), MS, MS)),
    O('Verdict', 'text', 'IF(IFERROR(%s*0.2/(%s+%s),0)>{in:risk},%s,%s)' % (INC, INC, ALLR, tok('v2', 'Income at risk'), tok('v2', 'Stable')))],
    GR('What if', ('Half the pages', {'pages': round(_pg / 2)}), ('Pay 3.50 per 1,000', {'rate': 3.5}), ('Pay 5.00 per 1,000', {'rate': 5.0}), ('Pages up 50%', {'pages': round(_pg * 1.5)}), ('Accept a 3% loss', {'risk': 0.03}))))

# 9 ------------------------------------------------------------ exclusivity test
EBK = tok('format', 'Ebook')
PROG = '{range:edroy.format},%s,{range:edroy.in_program},%s' % (EBK, '{list:yesno.yes}')
WIDE = '{range:edroy.format},%s,{range:edroy.in_program},%s,{range:edroy.status},%s' % (EBK, '{list:yesno.no}', tok('estatus', 'Live'))
PR12 = PRI_R('EDATE(%s,-12)' % MS, MS)
PROG_I = '(SUMIFS({range:edroy.royalty_home},%s)+%s)' % (PROG, PR12)
tools.append(TOOL('exclusivity', 'Exclusivity Test', 'Stay in the page-read program or go wide',
    'Income per ebook copy of the titles in the page-read program (royalties plus page reads) against the same figure for your wide ebooks over the last 12 months: stay or test going wide.', [
    I('margin', 'Wide must beat the program by', 0.0, 'pct')], [
    O('Program ebook copies, 12 months', 'int', 'SUMIFS({range:edroy.units},%s)' % PROG), O('Program royalties', 'money', 'SUMIFS({range:edroy.royalty_home},%s)' % PROG), O('Program page-read income', 'money', PR12),
    O('Program income per copy', 'money', 'IFERROR(%s/SUMIFS({range:edroy.units},%s),0)' % (PROG_I, PROG)), O('Page reads, share of program income', 'pct', 'IFERROR(%s/%s,0)' % (PR12, PROG_I)),
    O('Wide ebook copies, 12 months', 'int', 'SUMIFS({range:edroy.units},%s)' % WIDE), O('Wide royalties', 'money', 'SUMIFS({range:edroy.royalty_home},%s)' % WIDE),
    O('Wide income per copy', 'money', 'IFERROR(SUMIFS({range:edroy.royalty_home},%s)/SUMIFS({range:edroy.units},%s),0)' % (WIDE, WIDE)),
    O('Program against wide', 'pct', 'IFERROR((%s/SUMIFS({range:edroy.units},%s))/(SUMIFS({range:edroy.royalty_home},%s)/SUMIFS({range:edroy.units},%s))-1,0)' % (PROG_I, PROG, WIDE, WIDE)),
    O('Verdict', 'text', 'IF(IFERROR(SUMIFS({range:edroy.royalty_home},%s)/SUMIFS({range:edroy.units},%s),0)>IFERROR(%s/SUMIFS({range:edroy.units},%s),0)*(1+{in:margin}),%s,%s)' % (WIDE, WIDE, PROG_I, PROG, tok('v3', 'Test going wide'), tok('v3', 'Stay in the program')))],
    GR('What if wide must beat the program by', ('10%', {'margin': 0.10}), ('25%', {'margin': 0.25}), ('50%', {'margin': 0.5}), ('Nothing, and 15% less', {'margin': -0.15}))))

# 10 ------------------------------------------------------------ format mix check
def FSH(fmt, a, b):
    return 'IFERROR(SUMIFS({range:mformat.royalty_home},{range:mformat.format},%s,{range:mformat.month},">="&%s,{range:mformat.month},"<"&%s)/SUMIFS({range:mformat.royalty_home},{range:mformat.month},">="&%s,{range:mformat.month},"<"&%s),0)' % (tok('format', fmt), a, b, a, b)
NOW_A, NOW_B = 'EDATE(%s,-12)' % MS, MS; OLD_A, OLD_B = 'EDATE(%s,-24)' % MS, 'EDATE(%s,-12)' % MS
tools.append(TOOL('format_mix', 'Format Mix Check', 'Which format deserves the next push',
    'The share of royalties by format over the last 12 months against the 12 months before, set against the share you want for audio and paperback: a verdict on where to push.', [
    I('audio', 'Audio share you want', 0.08, 'pct'), I('print', 'Paperback share you want', 0.15, 'pct')], [
    O('Ebook share, last 12 months', 'pct', FSH('Ebook', NOW_A, NOW_B)), O('Ebook share, 12 months before', 'pct', FSH('Ebook', OLD_A, OLD_B)),
    O('Paperback share, last 12 months', 'pct', FSH('Paperback', NOW_A, NOW_B)), O('Paperback share, 12 months before', 'pct', FSH('Paperback', OLD_A, OLD_B)),
    O('Audio share, last 12 months', 'pct', FSH('Audiobook', NOW_A, NOW_B)), O('Audio share, 12 months before', 'pct', FSH('Audiobook', OLD_A, OLD_B)),
    O('Audio change, points', 'pct', '%s-%s' % (FSH('Audiobook', NOW_A, NOW_B), FSH('Audiobook', OLD_A, OLD_B))), O('Paperback change, points', 'pct', '%s-%s' % (FSH('Paperback', NOW_A, NOW_B), FSH('Paperback', OLD_A, OLD_B))),
    O('Royalties, last 12 months', 'money', ROY_R(NOW_A, NOW_B)), O('Royalties, 12 months before', 'money', ROY_R(OLD_A, OLD_B)),
    O('Verdict', 'text', 'IF(%s<{in:audio},%s,IF(%s<{in:print},%s,%s))' % (FSH('Audiobook', NOW_A, NOW_B), tok('v3', 'Push audio'), FSH('Paperback', NOW_A, NOW_B), tok('v3', 'Push paperback'), tok('v3', 'Balanced')))],
    GR('What if you want', ('Audio 4%', {'audio': 0.04}), ('Audio 4% and paperback 20%', {'audio': 0.04, 'print': 0.20}), ('Audio 4% and paperback 10%', {'audio': 0.04, 'print': 0.10}), ('Audio 12%', {'audio': 0.12}))))

# 11 ------------------------------------------------------------ store dependence stress test
R3 = ROY_R('EDATE(%s,-3)' % MS, MS); ST3 = ROY_R('EDATE(%s,-3)' % MS, MS, ST_R('{in:store}'))
LEFT = '((%s)-(%s))/3' % (R3, ST3)
tools.append(TOOL('dependence', 'Store Dependence Stress Test', 'What if you lost this store',
    'Pick a store: its share of the last 3 months, the income and cash months left without it against your monthly costs, with a verdict to diversify or keep the mix.', [
    IL('store', 'Store you could lose', 'store', 'Ebook store'), I('costs', 'Your monthly costs', 3500.0), I('cash', 'Cash on hand', 8900.0), I('safety', 'Cover wanted above costs', 0.25, 'pct')], [
    O('Royalties a month, last 3 months', 'money', '(%s)/3' % R3), O('This store, share', 'pct', 'IFERROR((%s)/(%s),0)' % (ST3, R3)),
    O('Largest store last month', 'text', 'INDEX({range:depmonth.largest_store},MATCH(%s,{range:depmonth.month},0))' % M1), O('Largest store share last month', 'pct', 'INDEX({range:depmonth.largest_share},MATCH(%s,{range:depmonth.month},0))' % M1),
    O('Your limit for one store', 'pct', '{set:dependence_limit}'), O('Income left a month without it', 'money', LEFT), O('Income left minus costs', 'money', '%s-{in:costs}' % LEFT),
    O('Monthly shortfall', 'money', 'MAX(0,{in:costs}-%s)' % LEFT), O('Months of cash at that shortfall (99 = none)', 'num', 'IF({in:costs}<=%s,99,MIN(99,{in:cash}/({in:costs}-%s)))' % (LEFT, LEFT)),
    O('Income needed for the cover you want', 'money', '{in:costs}*(1+{in:safety})'),
    O('Verdict', 'text', 'IF(OR(IFERROR((%s)/(%s),0)>{set:dependence_limit},%s<{in:costs}*(1+{in:safety})),%s,%s)' % (ST3, R3, LEFT, tok('v3', 'Diversify'), tok('v3', 'Keep the mix')))],
    GR('What if you lost', ('The print-on-demand service', {'store': '=' + tok('store', 'Print-on-demand')}), ('The wide distribution service', {'store': '=' + tok('store', 'Wide distribution')}), ('The audiobook store', {'store': '=' + tok('store', 'Audiobook store')}),
       ('The direct store', {'store': '=' + tok('store', 'Direct store')}), ('The ebook store, costs 2,500', {'costs': 2500}))))

# 12 ------------------------------------------------------------ currency exposure test
HOME = tok('currency', 'Home currency')
CW = '({range:curmonth.month}>=EDATE(%s,-12))*({range:curmonth.month}<%s)' % (MS, MS)
TOT12 = 'SUMPRODUCT(%s*{range:curmonth.amount_store}*{range:curmonth.rate_used})/100' % CW
NON12 = 'SUMPRODUCT((({range:curmonth.currency}<>%s)*({range:curmonth.currency}<>""))*%s*{range:curmonth.amount_store}*{range:curmonth.rate_used})/100' % (HOME, CW)
tools.append(TOOL('currency', 'Currency Exposure Test', 'How much do exchange rates move your income',
    'The share of royalties of the last 12 months earned outside your home currency and what a rate move of minus 10%, minus 5%, plus 5% or plus 10% does to the home amount, with a verdict.', [
    I('move', 'Rate move to test', 0.10, 'pct'), I('tolerance', 'Income swing you accept', 0.05, 'pct')], [
    O('Royalties, last 12 months', 'money', TOT12), O('Earned outside the home currency', 'money', NON12), O('Share outside the home currency', 'pct', 'IFERROR((%s)/(%s),0)' % (NON12, TOT12)),
    O('Total at minus 10%', 'money', '(%s)-0.10*(%s)' % (TOT12, NON12)), O('Total at minus 5%', 'money', '(%s)-0.05*(%s)' % (TOT12, NON12)), O('Total at plus 5%', 'money', '(%s)+0.05*(%s)' % (TOT12, NON12)),
    O('Total at plus 10%', 'money', '(%s)+0.10*(%s)' % (TOT12, NON12)), O('Change at the move you chose, downward', 'money', '-{in:move}*(%s)' % NON12),
    O('That change, share of royalties', 'pct', 'IFERROR({in:move}*(%s)/(%s),0)' % (NON12, TOT12)),
    O('Verdict', 'text', 'IF(IFERROR({in:move}*(%s)/(%s),0)>{in:tolerance},%s,%s)' % (NON12, TOT12, tok('v3', 'Hedge by pricing'), tok('v3', 'Exposure is fine')))],
    GR('What if the move were', ('2%', {'move': 0.02}), ('5%', {'move': 0.05}), ('15%', {'move': 0.15}), ('20%', {'move': 0.20}), ('10% with 8% accepted', {'tolerance': 0.08}))))

# 13 ------------------------------------------------------------ month close status
SM = 'COUNTIFS({range:statements.month},{in:month},{range:statements.status},%s)' % OPN
tools.append(TOOL('month_close', 'Month Close Status', 'Can you close this month',
    'Pick a month: the stores that reported sales, the statements issued and the ones still missing, what is still unpaid and a verdict to close the month or wait for stores.', [
    I('month', 'Month (first day)', iso(month_start(1)), 'date')], [
    O('Stores you sell through', 'int', 'COUNTA({range:stores.store})'), O('Stores with sales entered', 'int', 'COUNTIFS({range:mstore.month},{in:month},{range:mstore.royalty_home},">0")'),
    O('Statements issued', 'int', 'COUNTIFS({range:statements.month},{in:month},{range:statements.status},"<>"&%s)' % OPN), O('Stores still missing a statement', 'int', SM),
    O('Royalties entered for the month', 'money', ROY_M('{in:month}')), O('Statements, amount of the month', 'money', 'SUMIFS({range:statements.statement_amount},{range:statements.month},{in:month})'),
    O('Still unpaid', 'money', 'SUMIFS({range:statements.statement_amount},{range:statements.month},{in:month},{range:statements.status},%s)+SUMIFS({range:statements.statement_amount},{range:statements.month},{in:month},{range:statements.status},%s)' % (EXP, OPN)),
    O('Days since the month ended', 'int', '{today}-EOMONTH({in:month},0)'),
    O('Verdict', 'text', 'IF(AND(EOMONTH({in:month},0)<{today},%s=0),%s,%s)' % (SM, tok('v3', 'Close the month'), tok('v3', 'Wait for stores')))],
    GR('What if the month were', ('This month', {'month': '=' + MS}), ('2 months back', {'month': '=EDATE(%s,-2)' % MS}), ('4 months back', {'month': '=EDATE(%s,-4)' % MS}), ('A year back', {'month': '=EDATE(%s,-12)' % MS}))))

# 14 ------------------------------------------------------------ royalty trend and forecast
A12 = '(%s/12)' % ROY_R('EDATE(%s,-12)' % MS, MS); A3 = '(%s/3)' % ROY_R('EDATE(%s,-3)' % MS, MS); PRV = '(%s/12)' % ROY_R('EDATE(%s,-23)' % MS, 'EDATE(%s,-11)' % MS)
TREND = 'MIN({in:cap},MAX(2-{in:cap},%s/%s))' % (A3, A12)
def SEAS(i): return '(%s/%s)' % (ROY_M('EDATE(%s,%d)' % (MS, i - 12)), PRV)
def FC(i): return '%s*%s*%s' % (A12, TREND, SEAS(i))
outs = [O('Average month, last 12 months', 'money', A12), O('Average month, last 3 months', 'money', A3), O('Trend factor', 'num', TREND)]
for i in (1, 2, 3): outs.append(O('Season index, month +%d' % i, 'num', SEAS(i)))
for i in (1, 2, 3): outs.append(O('Base, month +%d' % i, 'money', FC(i)))
for i in (1, 2, 3): outs.append(O('Best, month +%d' % i, 'money', '(%s)*(1+{set:upside_pct})' % FC(i)))
for i in (1, 2, 3): outs.append(O('Worst, month +%d' % i, 'money', '(%s)*(1-{set:downside_pct})' % FC(i)))
AVGF = '(%s*%s*(%s+%s+%s)/3)' % (A12, TREND, SEAS(1), SEAS(2), SEAS(3))
outs.append(O('Base forecast against your 12-month average', 'pct', '%s/%s-1' % (AVGF, A12)))
outs.append(O('Verdict', 'text', 'IF(%s>%s*(1+{set:near_pct}),%s,IF(%s<%s*(1-{set:near_pct}),%s,%s))' % (AVGF, A12, tok('v4', 'Above your average'), AVGF, A12, tok('v4', 'Below your average'), tok('v4', 'Near your average'))))
tools.append(TOOL('forecast', 'Royalty Trend and Forecast', 'What will the next 3 months bring',
    'Your last 12 and last 3 months, the trend and last year\'s season: the next 3 months in Base, Best and Worst against your own average. An estimate from your own history.', [
    I('cap', 'Highest trend factor you allow', 1.2, 'num')], outs,
    GR('What if the trend factor is capped at', ('1.00 (no trend)', {'cap': 1.0}), ('1.10', {'cap': 1.1}), ('1.30', {'cap': 1.3}), ('1.50', {'cap': 1.5}))))

# 15 ------------------------------------------------------------ title ranking
TR_ = '{range:titles.total_12m}'
outs = []
for i in range(5):
    rk = '({in:start}+%d)' % i
    lg = 'IF(%s>COUNT(%s),"",LARGE(%s,%s))' % (rk, TR_, TR_, rk)
    outs += [O('Title, place %d of the list' % (i + 1), 'text', 'IF(%s="","",INDEX({range:titles.title},MATCH(%s,%s,0)))' % (lg, lg, TR_)), O('Income, 12 months, place %d' % (i + 1), 'money', 'IF(%s="",0,%s)' % (lg, lg)),
             O('Share of all, place %d' % (i + 1), 'pct', 'IF(%s="",0,%s/SUM(%s))' % (lg, lg, TR_))]
outs += [O('Top three titles, share', 'pct', '(LARGE(%s,1)+LARGE(%s,2)+LARGE(%s,3))/SUM(%s)' % (TR_, TR_, TR_, TR_)), O('Income of all titles, 12 months', 'money', 'SUM(%s)' % TR_), O('Titles counted', 'int', 'COUNT(%s)' % TR_),
         O('Verdict', 'text', 'IF((LARGE(%s,1)+LARGE(%s,2)+LARGE(%s,3))/SUM(%s)>0.5,%s,%s)' % (TR_, TR_, TR_, TR_, tok('v4', 'Top three carry over half'), tok('v4', 'Spread across titles')))]
tools.append(TOOL('title_rank', 'Title Ranking', 'Which titles carry the income',
    'Titles ranked by royalties plus page-read income of the last 12 months: choose the first place to show (1 for the top five, a later place for the middle, the count minus 4 for the bottom five).', [
    I('start', 'First place to show', 1, 'int')], outs,
    GR('Show', ('Top five', {'start': 1}), ('Places 6 to 10', {'start': 6}), ('Places 11 to 15', {'start': 11}), ('Bottom five', {'start': '=COUNT({range:titles.total_12m})-4'}))))

# 16 ------------------------------------------------------------ country growth finder
G = '{range:ctyfmt.country_growth}'; STEP = 'COUNTA({range:formats.format})'
def GK(k): return 'LARGE(%s,1+(%d-1)*%s)' % (G, k, STEP)
outs = []
for k in range(1, 5):
    outs += [O('Country ranked %d' % k, 'text', 'INDEX({range:ctyfmt.country},MATCH(%s,%s,0))' % (GK(k), G)), O('Growth, rank %d' % k, 'pct', GK(k)),
             O('Royalty, 12 months, rank %d' % k, 'money', 'INDEX({range:ctyfmt.country_total},MATCH(%s,%s,0))' % (GK(k), G))]
outs += [O('Slowest country', 'text', 'INDEX({range:ctyfmt.country},MATCH(SMALL(%s,1),%s,0))' % (G, G)), O('Slowest growth', 'pct', 'SMALL(%s,1)' % G),
         O('All countries, growth', 'pct', 'SUM({range:ctyfmt.royalty_home})/SUM({range:ctyfmt.royalty_prev})-1'),
         O('Verdict', 'text', 'IF(%s>SUM({range:ctyfmt.royalty_home})/SUM({range:ctyfmt.royalty_prev})-1+{in:gap},%s,%s)' % (GK(1), tok('v4', 'Advertise in the top country'), tok('v4', 'Hold')))]
tools.append(TOOL('country_growth', 'Country Growth Finder', 'Where is your income growing',
    'Countries ranked by the change of royalties over the last 12 months against the 12 months before: the fastest four, the slowest one and a verdict on where to advertise.', [
    I('gap', 'Top country must beat the total by', 0.02, 'pct')], outs,
    GR('What if the top country must beat the total by', ('0%', {'gap': 0.0}), ('5%', {'gap': 0.05}), ('10%', {'gap': 0.10}))))

# 17 ------------------------------------------------------------ missing sale detector
LIVE_T = tok('estatus', 'Live')
COND = '(({range:edroy.months_sold}>={in:months})*({range:edroy.units_month}=0)*({range:edroy.status}=%s))' % LIVE_T
OFF = 'SUMPRODUCT(MATCH(1,%s,0))' % COND
CNT = 'SUMPRODUCT(%s)' % COND
tools.append(TOOL('missing', 'Missing Sale Detector', 'Which edition stopped selling this month',
    'Editions that sold in most of the last 12 months and have no sale this month: how many, the first one with its title and what it earned a month, with a verdict to ask the store for the report.', [
    I('months', 'Months with a sale (of 12) that make a sale expected', 8, 'int')], [
    O('Live editions with a sale most months', 'int', 'SUMPRODUCT(({range:edroy.months_sold}>={in:months})*({range:edroy.status}=%s))' % LIVE_T), O('Of those, with no sale this month', 'int', CNT),
    O('First edition', 'text', 'IF(%s=0,"-",INDEX({range:edroy.edition_id},%s))' % (CNT, OFF)), O('Its title', 'text', 'IF(%s=0,"-",INDEX({range:edroy.title},%s))' % (CNT, OFF)),
    O('Its format', 'text', 'IF(%s=0,"-",INDEX({range:edroy.format},%s))' % (CNT, OFF)), O('Months with a sale', 'int', 'IF(%s=0,0,INDEX({range:edroy.months_sold},%s))' % (CNT, OFF)),
    O('Royalty a month, last 12 months', 'money', 'IF(%s=0,0,INDEX({range:edroy.royalty_home},%s)/12)' % (CNT, OFF)), O('Copies, last 3 months', 'int', 'IF(%s=0,0,INDEX({range:edroy.units_3m},%s))' % (CNT, OFF)),
    O('Live editions selling under 5 copies in 3 months', 'int', 'COUNTIFS({range:edroy.status},%s,{range:edroy.units_3m},"<5")' % LIVE_T),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (CNT, tok('v4', 'Ask the store for the report'), tok('v4', 'Normal')))],
    GR('What if you expect a sale in', ('6 months of 12', {'months': 6}), ('10 months of 12', {'months': 10}), ('12 months of 12', {'months': 12}), ('3 months of 12', {'months': 3}))))

# 18 ------------------------------------------------------------ own-history compare
FR = '(DAY({today})/DAY(EOMONTH({today},0)))'
MTD = ROY_M(MS, ST_R('{in:store}')); PROJ = '(%s/%s)' % (MTD, FR); AV3 = '(%s/3)' % ROY_R('EDATE(%s,-3)' % MS, MS, ST_R('{in:store}')); LY = ROY_M('EDATE(%s,-12)' % MS, ST_R('{in:store}'))
def VD(base): return 'IF(%s>%s*(1+{set:change_flag_pct}),%s,IF(%s<%s*(1-{set:change_flag_pct}),%s,%s))' % (PROJ, base, tok('v4', 'Up'), PROJ, base, tok('v4', 'Down'), tok('v4', 'Flat'))
tools.append(TOOL('history', 'Own-History Compare', 'Is this store up or down against your own history',
    'Pick a store: this month so far, the month projected to its full length, the 3-month average and the same month last year, with up, flat or down beyond your flag.', [
    IL('store', 'Store', 'store', 'Print-on-demand')], [
    O('This month so far', 'money', MTD), O('Share of the month passed', 'pct', FR), O('This month projected', 'money', PROJ), O('Average of the last 3 months', 'money', AV3), O('Same month last year', 'money', LY),
    O('Change against the 3-month average', 'pct', 'IFERROR(%s/%s-1,0)' % (PROJ, AV3)), O('Change against last year', 'pct', 'IFERROR(%s/%s-1,0)' % (PROJ, LY)), O('Verdict against the 3-month average', 'text', VD(AV3)), O('Verdict against last year', 'text', VD(LY))],
    GR('Store', ('Ebook store', {'store': '=' + tok('store', 'Ebook store')}), ('Audiobook store', {'store': '=' + tok('store', 'Audiobook store')}), ('Library and lending', {'store': '=' + tok('store', 'Library and lending')}),
       ('Wide distribution', {'store': '=' + tok('store', 'Wide distribution')}), ('Direct store', {'store': '=' + tok('store', 'Direct store')}))))
assert len(tools) == 18, len(tools)
