"""Household Finance suite part 8: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf8_lists import *
from hf8_tables import R, MS, YES, NO, BOUGHT, CAR, MOVE, TH, HAVE_MOVE, BAL_NOW
import hf8_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, default): return IN(k, label, 'list', key(lst, default), list=lst)
BP, TD, DED, MP, EB, SA, EP, YM, CC, NP = (lambda c, t=t: R(t, c) for t in ('big_purchases', 'tax_docs', 'deductions', 'move_plan', 'event_budget', 'set_aside', 'est_payments', 'year_months', 'category_changes', 'next_year_plan'))
MISS, MREC = (lambda c, t=t: R(t, c) for t in ('missing_docs', 'missing_receipts'))
THISY, LASTY = 'YEAR({today})&""', '(YEAR({today})-1)&""'
def PM(loan, rate, n): return 'IF(%s<=0,0,IF(%s=0,%s/%s,-PMT(%s/12,%s,%s)))' % (n, rate, loan, n, rate, n, loan)
def W(c, win='last12'): return 'SUMIFS(%s,%s,1)' % (YM(c), YM(win))
def DT(months): return '{today}+ROUND((%s)*30.4375,0)' % months
tools = []
# 1 car purchase decision ---------------------------------------------------------------------------------------------
LOANC = 'MAX(0,{in:price}-{in:down}-{in:trade})'
CST = '(%s+{in:running})' % PM(LOANC, '{in:rate}', '{in:months}')
tools.append(TOOL('car_buy', 'Car Purchase Decision', 'Can we afford this car',
    'Price, deposit, trade-in, loan term, rate and running cost: monthly cost, total over the years and share of take-home against your limit. Not advice.', [
    I('price', 'Price', 13500), I('down', 'Deposit', 3000), I('trade', 'Trade-in value', 1500), I('months', 'Loan months', 48, 'int'), I('rate', 'Yearly rate', 0.079, 'pct'), I('running', 'Running cost a month', 320)], [
    O('Loan amount', 'money', LOANC), O('Monthly payment', 'money', PM(LOANC, '{in:rate}', '{in:months}')), O('Monthly cost with running cost', 'money', CST),
    O('Total over the years you keep it', 'money', '{in:down}+%s*{in:months}+{in:running}*MAX({set:car_years}*12,{in:months})' % PM(LOANC, '{in:rate}', '{in:months}')),
    O('Average monthly take-home, last 12 months', 'money', TH), O('Share of take-home', 'pct', 'IFERROR(%s/(%s),0)' % (CST, TH)), O('Monthly cost you accept', 'money', '{set:car_limit}*(%s)' % TH),
    O('Over (+) or under (-) your limit a month', 'money', '%s-{set:car_limit}*(%s)' % (CST, TH)),
    O('Verdict', 'text', 'IF(%s<={set:car_limit}*(%s),%s,%s)' % (CST, TH, vd('Within your limit'), vd('Above your limit')))],
    GR('What if the loan runs', ('24 months', {'months': 24}), ('36 months', {'months': 36}), ('48 months', {'months': 48}), ('60 months', {'months': 60}), ('72 months', {'months': 72}))))
# 2 car loan payment --------------------------------------------------------------------------------------------------
PAY2 = PM('{in:loan}', '{in:rate}', '{in:months}')
NX = 'IF({in:rate}=0,{in:loan}/(%s+{in:extra}),NPER({in:rate}/12,-(%s+{in:extra}),{in:loan}))' % (PAY2, PAY2)
tools.append(TOOL('car_loan', 'Car Loan Payment', 'What does the loan cost and what does extra change',
    'The payment of a typed loan, the interest over the whole loan and what a monthly extra payment changes: months saved and interest saved, estimates from your numbers.', [
    I('loan', 'Loan amount', 9000), I('months', 'Loan months', 48, 'int'), I('rate', 'Yearly rate', 0.079, 'pct'), I('extra', 'Extra payment a month', 100)], [
    O('Monthly payment', 'money', PAY2), O('Total paid over the loan', 'money', '%s*{in:months}' % PAY2), O('Interest over the loan', 'money', '%s*{in:months}-{in:loan}' % PAY2),
    O('Months with the extra payment', 'num', 'ROUNDUP(%s,0)' % NX), O('Months saved', 'num', '{in:months}-ROUNDUP(%s,0)' % NX),
    O('Interest with the extra payment', 'money', 'MAX(0,(%s+{in:extra})*%s-{in:loan})' % (PAY2, NX)), O('Interest saved', 'money', '(%s*{in:months}-{in:loan})-MAX(0,(%s+{in:extra})*%s-{in:loan})' % (PAY2, PAY2, NX)),
    O('Verdict', 'text', 'IF({in:extra}>0,%s,%s)' % (vd('Loan is shortened by the extra payment'), vd('Loan runs as standard')))],
    GR('What if the extra payment is', ('Nothing', {'extra': 0}), ('50', {'extra': 50}), ('100', {'extra': 100}), ('200', {'extra': 200}), ('400', {'extra': 400}))))
# 3 buy or keep the car ----------------------------------------------------------------------------------------------------
CUR3 = '({in:cur_run}+{in:cur_rep}/12)'; NEW3 = '({in:new_pay}+{in:new_run})'
tools.append(TOOL('buy_keep', 'Buy or Keep the Car', 'Does a newer car cost more or less than the one we have',
    'The monthly cost of the car you have (running cost plus repairs) against the monthly cost of the newer one (payment plus running cost), with the difference over the years you keep it.', [
    I('cur_run', 'Current car running cost a month', 395), I('cur_rep', 'Repairs you expect a year', 480), I('new_pay', 'New car payment a month', 220), I('new_run', 'New car running cost a month', 320)], [
    O('Current car, a month', 'money', CUR3), O('New car, a month', 'money', NEW3), O('New costs more (+) or less (-) a month', 'money', '%s-%s' % (NEW3, CUR3)),
    O('Over a year', 'money', '(%s-%s)*12' % (NEW3, CUR3)), O('Over the years you keep it', 'money', '(%s-%s)*12*{set:car_years}' % (NEW3, CUR3)),
    O('Difference as a share of take-home', 'pct', 'IFERROR((%s-%s)/(%s),0)' % (NEW3, CUR3, TH)),
    O('Verdict', 'text', 'IF(ABS(%s-%s)<5,%s,IF(%s>%s,%s,%s))' % (NEW3, CUR3, vd('About the same cost a month'), NEW3, CUR3, vd('New car costs more a month'), vd('New car costs less a month')))],
    GR('What if the repairs a year are', ('0', {'cur_rep': 0}), ('480', {'cur_rep': 480}), ('1000', {'cur_rep': 1000}), ('1800', {'cur_rep': 1800}), ('3000', {'cur_rep': 3000}))))
# 4 big purchase saving plan ----------------------------------------------------------------------------------------------
NEED4 = 'MAX(0,{in:target}-{in:saved})'
tools.append(TOOL('save_plan', 'Big Purchase Saving Plan', 'How much a month reaches the target by the date',
    'The monthly saving that reaches a typed target by a typed number of months, set against the monthly amount in Settings, with the earliest date at that amount.', [
    I('target', 'Target', 11500), I('saved', 'Saved so far', 4750), I('months', 'Months until the planned date', 10, 'int')], [
    O('Still to save', 'money', NEED4), O('Saving needed a month', 'money', 'IF({in:months}<1,%s,%s/{in:months})' % (NEED4, NEED4)), O('Monthly amount in Settings', 'money', '{set:big_saving}'),
    O('Months needed at the Settings amount', 'num', 'IFERROR(ROUNDUP(%s/{set:big_saving},0),0)' % NEED4), O('Earliest date at the Settings amount', 'date', DT('IFERROR(ROUNDUP(%s/{set:big_saving},0),0)' % NEED4)),
    O('Saving short each month', 'money', 'MAX(0,IF({in:months}<1,%s,%s/{in:months})-{set:big_saving})' % (NEED4, NEED4)),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(AND({in:months}>=1,%s/{in:months}<={set:big_saving}),%s,%s))' % (NEED4, vd('Already saved'), NEED4, vd('Save the monthly amount shown'), vd('Date too soon for this target')))],
    GR('What if the months are', ('6', {'months': 6}), ('10', {'months': 10}), ('15', {'months': 15}), ('24', {'months': 24}), ('36', {'months': 36}))))
# 5 purchase order ----------------------------------------------------------------------------------------------------------
OK = BP('order_key')
def NTH(k, c): return 'IFERROR(INDEX(%s,MATCH(SMALL(%s,%d),%s,0)),%s)' % (BP(c), OK, k, OK, '""' if c in ('item',) else '0')
tools.append(TOOL('purchase_order', 'Purchase Order', 'Which big purchase do we fund first',
    'The purchases still to buy, in the order of their dates, and when each is funded if one monthly amount pays for them one after the other.', [I('pot', 'Monthly amount for big purchases', 450)], [
    O('First: item', 'text', NTH(1, 'item')), O('First: left to save', 'money', NTH(1, 'left')), O('First: funded on', 'date', 'IFERROR({today}+ROUND(%s/{in:pot}*30.4375,0),"")' % NTH(1, 'left')),
    O('Second: item', 'text', NTH(2, 'item')), O('Second: left to save', 'money', NTH(2, 'left')), O('Second: funded on', 'date', 'IFERROR({today}+ROUND((%s+%s)/{in:pot}*30.4375,0),"")' % (NTH(1, 'left'), NTH(2, 'left'))),
    O('Third: item', 'text', NTH(3, 'item')), O('Third: funded on', 'date', 'IFERROR({today}+ROUND((%s+%s+%s)/{in:pot}*30.4375,0),"")' % (NTH(1, 'left'), NTH(2, 'left'), NTH(3, 'left'))),
    O('Saving needed a month for all, to their dates', 'money', 'SUM(%s)' % BP('per_month')), O('Months to fund all', 'num', 'IFERROR(SUM(%s)/{in:pot},0)' % BP('left')),
    O('Verdict', 'text', vd('Purchase order set by date and gap'))],
    GR('What if the monthly amount is', ('300', {'pot': 300}), ('450', {'pot': 450}), ('700', {'pot': 700}), ('1000', {'pot': 1000}), ('1500', {'pot': 1500}))))
# 6 moving plan --------------------------------------------------------------------------------------------------------------
LEFT6 = 'SUM(%s)+{in:overlap}*{in:rent}' % MP('left')
SHORT6 = 'MAX(0,%s-{in:have})' % LEFT6
MD = 'LARGE(%s,1)' % MP('move_date')
tools.append(TOOL('moving_plan', 'Moving Plan', 'How much cash does the move need and when do we have it',
    'The total of the move costs, what is paid, extra months of overlapping rent and the money you hold for the move: the cash still needed and the date you have it at your monthly saving.', [
    I('have', 'Saved for the move', 2100), I('save', 'Monthly saving for the move', 450), I('overlap', 'Extra months of overlapping rent', 0, 'int'), I('rent', 'Rent a month', 1650)], [
    O('Total move costs', 'money', 'SUM(%s)' % MP('estimate')), O('Paid so far', 'money', 'SUM(%s)' % MP('paid')), O('Left to pay, with extra overlapping rent', 'money', LEFT6),
    O('Cash still to save', 'money', SHORT6), O('Months to save it', 'num', 'IFERROR(ROUNDUP(%s/{in:save},0),0)' % SHORT6), O('You have it on', 'date', DT('IFERROR(ROUNDUP(%s/{in:save},0),0)' % SHORT6)),
    O('Move date', 'date', MD), O('Days between your date and the move date', 'int', '%s-%s' % (MD, '({today}+ROUND(IFERROR(ROUNDUP(%s/{in:save},0),0)*30.4375,0))' % SHORT6)),
    O('Verdict', 'text', 'IF({today}+ROUND(IFERROR(ROUNDUP(%s/{in:save},0),0)*30.4375,0)<=%s,%s,%s)' % (SHORT6, MD, vd('Covered by the move date'), vd('Short at the move date')))],
    GR('What if the monthly saving is', ('250', {'save': 250}), ('450', {'save': 450}), ('650', {'save': 650}), ('900', {'save': 900}), ('1200', {'save': 1200}))))
# 7 move date finder -----------------------------------------------------------------------------------------------------------
GAP7 = 'MAX(0,SUM(%s)+{in:first}-{in:have})' % MP('left')
tools.append(TOOL('move_date', 'Move Date Finder', 'What is the earliest date we can move',
    'The earliest date at your monthly saving, after you first fund another purchase if you choose (for example the car gap).', [
    I('have', 'Saved for the move', 2100), I('save', 'Monthly saving', 450), I('first', 'Another purchase to fund first', 0)], [
    O('Move costs still to pay', 'money', 'SUM(%s)' % MP('left')), O('Cash to save, with the other purchase', 'money', GAP7), O('Months to save', 'num', 'IFERROR(ROUNDUP(%s/{in:save},0),0)' % GAP7),
    O('Earliest move date', 'date', DT('IFERROR(ROUNDUP(%s/{in:save},0),0)' % GAP7)), O('Planned move date', 'date', MD),
    O('Days later (+) or earlier (-) than planned', 'int', '{today}+ROUND(IFERROR(ROUNDUP(%s/{in:save},0),0)*30.4375,0)-%s' % (GAP7, MD)),
    O('Verdict', 'text', 'IF(IFERROR(%s/{in:save},0)>120,%s,%s)' % (GAP7, vd('Not reached within 10 years'), vd('Earliest move date shown')))],
    GR('What if another purchase is funded first', ('None', {'first': 0}), ('1000', {'first': 1000}), ('3000', {'first': 3000}), ('6750', {'first': 6750}), ('10000', {'first': 10000}))))
# 8 rent or buy comparison -------------------------------------------------------------------------------------------------------
def RENT(n): return '({in:rent}*12*((1+{in:rg}/100)^%s-1)/MAX({in:rg}/100,0.000000001)+{in:rr}*12*%s-({in:down}+{in:price}*{in:bc}/100)*((1+{in:ret}/100)^%s-1))' % (n, n, n)
RM = 'MAX({in:rate}/1200,0.000000001)'
PMT8 = '(-PMT(%s,{in:term}*12,{in:price}-{in:down}))' % RM
def BUY(n):
    return '({in:down}+{in:price}*{in:bc}/100+%s*12*MIN(%s,{in:term})+({in:upkeep}+{in:br}*12)*%s-({in:price}*(1+{in:pg}/100)^%s*(1-{in:sc}/100)-(({in:price}-{in:down})*(1+%s)^(12*%s)-%s*((1+%s)^(12*%s)-1)/%s)))' % (
        PMT8, n, n, n, RM, n, PMT8, RM, n, RM)
tools.append(TOOL('rent_buy', 'Rent or Buy Decision', 'Does buying beat renting over the years we would stay',
    'Your numbers for renting and buying: monthly cost of each, total cost after the years you stay and the break-even year. Your numbers, not advice.', [
    I('rent', 'Monthly rent', 1650), I('rg', 'Rent growth, percent a year', 3, 'num'), I('rr', 'Other running cost a month, renting', 60), I('price', 'Home price', 310000), I('down', 'Down payment', 40000),
    I('rate', 'Mortgage rate, percent a year', 5.9, 'num'), I('term', 'Mortgage term, years', 25, 'int'), I('pg', 'Home price growth, percent a year', 2, 'num'), I('upkeep', 'Upkeep and local charges a year', 4800),
    I('br', 'Other running cost a month, buying', 140), I('bc', 'Buying costs, percent of price', 3, 'num'), I('sc', 'Selling costs, percent of price', 5, 'num'), I('ret', 'Return on kept money, percent a year', 4, 'num'),
    I('years', 'Years you would stay', 10, 'int')], [
    O('Renting, a month', 'money', '{in:rent}+{in:rr}'), O('Mortgage payment, a month', 'money', PMT8), O('Buying, a month, with upkeep and running cost', 'money', '%s+{in:upkeep}/12+{in:br}' % PMT8),
    O('Buying costs more (+) or less (-) a month', 'money', '%s+{in:upkeep}/12+{in:br}-{in:rent}-{in:rr}' % PMT8), O('Renting costs in total over the years', 'money', RENT('{in:years}')),
    O('Buying costs in total over the years', 'money', BUY('{in:years}')), O('Buying more (+) or less (-) in total', 'money', '%s-%s' % (BUY('{in:years}'), RENT('{in:years}'))),
    O('Break-even year in the comparison sheet', 'int', '{range:rb_compare.be_years}' if False else 'IFERROR(INDEX(%s,MATCH(1,%s,0)),0)' % (R('rb_compare', 'year'), R('rb_compare', 'break_even'))),
    O('Verdict', 'text', 'IF(%s<=%s,%s,%s)' % (BUY('{in:years}'), RENT('{in:years}'), vd('Buying breaks even in the years shown'), vd('Renting costs less in the years tested')))],
    GR('What if you stay', ('3 years', {'years': 3}), ('5 years', {'years': 5}), ('8 years', {'years': 8}), ('12 years', {'years': 12}), ('15 years', {'years': 15}))))
# 9 event budget -----------------------------------------------------------------------------------------------------------------
EST9 = '(SUM(%s)+{in:extra})' % EB('estimate')
tools.append(TOOL('event_tool', 'Event Budget Tool', 'Is the event on target',
    'The estimates of the event against the target total, with an extra cost you type, the money still to pay, the deposits due and the monthly saving to the last due date.', [
    I('target', 'Target total', 2600), I('extra', 'An extra cost to add', 0)], [
    O('Estimate total, with the extra cost', 'money', EST9), O('Paid so far', 'money', 'SUM(%s)' % EB('paid')), O('Left to pay', 'money', '%s-SUM(%s)' % (EST9, EB('paid'))),
    O('Over (+) or under (-) the target', 'money', '%s-{in:target}' % EST9), O('Share of the target', 'pct', 'IFERROR(%s/{in:target},0)' % EST9),
    O('Deposits still to pay', 'money', 'SUMIFS(%s,%s,%s)' % (EB('left'), EB('deposit'), YES)), O('Last due date', 'date', 'LARGE(%s,1)' % EB('due_date')),
    O('Saving a month to the last due date', 'money', 'IFERROR(MAX(0,%s-SUM(%s))/MAX(1,(LARGE(%s,1)-{today})/30.4375),0)' % (EST9, EB('paid'), EB('due_date'))),
    O('Verdict', 'text', 'IF(%s>{in:target},%s,%s)' % (EST9, vd('Over target'), vd('On target')))],
    GR('What if an extra cost is added', ('Nothing', {'extra': 0}), ('100', {'extra': 100}), ('250', {'extra': 250}), ('-200', {'extra': -200}), ('-480', {'extra': -480}))))
# 10 tax documents countdown -------------------------------------------------------------------------------------------------------
TY = '%s,{in:year}' % TD('tax_year')
tools.append(TOOL('doc_countdown', 'Tax Documents Countdown', 'How many tax documents are missing and how long is left',
    'The documents of one tax year by status and the days to the due date your tax office gave you. Check your local rules for what you need.', [IL('year', 'Tax year', 'tyear', '2026'), I('warn', 'Warn this many days before the due date', 30, 'int')], [
    O('Documents in the year', 'int', 'COUNTIFS(%s,%s,"<>")' % (TY, TD('doc_id'))), O('In hand', 'int', 'COUNTIFS(%s,%s,1)' % (TY, TD('got'))), O('Filed', 'int', 'COUNTIFS(%s,%s,%s)' % (TY, TD('filed'), YES)),
    O('Missing, past the expected date', 'int', 'COUNTIFS(%s,%s,%s)' % (TY, TD('status'), st('Overdue'))), O('Still expected', 'int', 'COUNTIFS(%s,%s,%s)' % (TY, TD('status'), st('Expected'))),
    O('Share in hand', 'pct', 'IFERROR(COUNTIFS(%s,%s,1)/COUNTIFS(%s,%s,"<>"),0)' % (TY, TD('got'), TY, TD('doc_id'))),
    O('Due date', 'date', 'SUMPRODUCT(MAX((%s={in:year})*(%s)))' % (TD('tax_year'), TD('due_date'))),
    O('Days to the due date', 'int', 'SUMPRODUCT(MAX((%s={in:year})*(%s)))-{today}' % (TD('tax_year'), TD('due_date'))),
    O('Days left after the warning period', 'int', 'SUMPRODUCT(MAX((%s={in:year})*(%s)))-{today}-{in:warn}' % (TD('tax_year'), TD('due_date'))),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,%s,%s)>0,%s,%s)' % (TY, TD('status'), st('Overdue'), vd('Documents are missing'), vd('All documents received')))],
    GR('What if you warn', ('7 days before', {'warn': 7}), ('14 days before', {'warn': 14}), ('30 days before', {'warn': 30}), ('60 days before', {'warn': 60}), ('90 days before', {'warn': 90}))))
# 11 missing documents finder ---------------------------------------------------------------------------------------------------------
def MX(k, c): return 'IFERROR(INDEX(%s,%d)&"","")' % (MISS(c), k)
tools.append(TOOL('missing_finder', 'Missing Documents Finder', 'Which document do we ask for first',
    'The documents not in hand, the most overdue first, with who to ask. A minus in days overdue means it is not due yet.', [I('min_days', 'Show documents overdue by at least this many days', 0, 'int')], [
    O('First: document', 'text', MX(1, 'description')), O('First: who to ask', 'text', MX(1, 'contact')), O('First: days overdue', 'int', 'IFERROR(INDEX(%s,1),0)' % MISS('days_overdue')),
    O('Second: document', 'text', MX(2, 'description')), O('Second: who to ask', 'text', MX(2, 'contact')), O('Third: document', 'text', MX(3, 'description')),
    O('Documents overdue by that many days or more', 'int', 'COUNTIFS(%s,">="&{in:min_days})' % TD('miss_key')), O('Documents not in hand at all', 'int', 'COUNTIFS(%s,0,%s,"<>")' % (TD('got'), TD('doc_id'))),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">="&{in:min_days})>0,%s,%s)' % (TD('miss_key'), vd('Ask for the first document'), st('Nothing is missing')))],
    GR('What if you show documents overdue by', ('Any', {'min_days': -999}), ('0 days', {'min_days': 0}), ('7 days', {'min_days': 7}), ('30 days', {'min_days': 30}), ('90 days', {'min_days': 90}))))
# 12 deduction totals ------------------------------------------------------------------------------------------------------------------
DY = '%s,{in:year},%s,">="&{in:min}' % (DED('tax_year'), DED('amount'))
tools.append(TOOL('ded_totals', 'Deduction Records Totals', 'What have we recorded and which receipts are missing',
    'The records of one tax year: the amount recorded, the receipts kept and missing and the amount without a receipt. The records say nothing about what is allowed: ask your adviser.', [IL('year', 'Tax year', 'tyear', '2026'), I('min', 'Only records of this amount or more', 0)], [
    O('Amount recorded', 'money', 'SUMIFS(%s,%s)' % (DED('amount'), DY)), O('Records', 'int', 'COUNTIFS(%s,%s,"<>")' % (DY, DED('deduction_id'))), O('Receipts kept', 'int', 'COUNTIFS(%s,%s,%s)' % (DY, DED('receipt'), YES)),
    O('Receipts missing', 'int', 'COUNTIFS(%s,%s,%s)' % (DY, DED('receipt'), NO)), O('Amount without a receipt', 'money', 'SUMIFS(%s,%s,%s,%s)' % (DED('amount'), DY, DED('receipt'), NO)),
    O('Share of records with a receipt', 'pct', 'IFERROR(COUNTIFS(%s,%s,%s)/COUNTIFS(%s,%s,"<>"),0)' % (DY, DED('receipt'), YES, DY, DED('deduction_id'))),
    O('Average record', 'money', 'IFERROR(SUMIFS(%s,%s)/COUNTIFS(%s,%s,"<>"),0)' % (DED('amount'), DY, DY, DED('deduction_id'))),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,%s,%s)>0,%s,%s)' % (DY, DED('receipt'), NO, vd('Receipts are missing'), vd('All receipts kept')))],
    GR('What if you count records of', ('Any amount', {'min': 0}), ('25 or more', {'min': 25}), ('50 or more', {'min': 50}), ('100 or more', {'min': 100}), ('200 or more', {'min': 200}))))
# 13 missing receipts finder -------------------------------------------------------------------------------------------------------------
tools.append(TOOL('receipt_finder', 'Missing Receipts Finder', 'Which receipts do we look for first',
    'The records without a receipt, the biggest first: how many, the amount at stake and the first three to find.', [I('min', 'Only records of this amount or more', 0)], [
    O('Records without a receipt', 'int', 'COUNTIFS(%s,">="&{in:min})' % DED('miss_key')), O('Amount at stake', 'money', 'SUMIFS(%s,%s,">="&{in:min})' % (DED('amount'), DED('miss_key'))),
    O('First: description', 'text', 'IFERROR(INDEX(%s,1)&"","")' % MREC('description')), O('First: amount', 'money', 'IFERROR(INDEX(%s,1)+0,0)' % MREC('amount')),
    O('Second: description', 'text', 'IFERROR(INDEX(%s,2)&"","")' % MREC('description')), O('Second: amount', 'money', 'IFERROR(INDEX(%s,2)+0,0)' % MREC('amount')),
    O('Third: description', 'text', 'IFERROR(INDEX(%s,3)&"","")' % MREC('description')), O('Third: amount', 'money', 'IFERROR(INDEX(%s,3)+0,0)' % MREC('amount')),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">="&{in:min})>0,%s,%s)' % (DED('miss_key'), vd('Find the listed receipts'), st('No receipt is missing')))],
    GR('What if you look at records of', ('Any amount', {'min': 0}), ('25 or more', {'min': 25}), ('50 or more', {'min': 50}), ('100 or more', {'min': 100}), ('200 or more', {'min': 200}))))
# 14 estimated tax set-aside ---------------------------------------------------------------------------------------------------------------
L91 = '%s,">"&({today}-91)' % SA('date')
tools.append(TOOL('set_aside_tool', 'Estimated Tax Set-aside', 'How much of this quarter\'s freelance income do we set aside',
    'A typed percentage of the freelance income you received, set against what you really moved in the last 91 days and the balance now. Confirm the percentage with your adviser.', [
    I('income', 'Freelance income received this quarter', 6200), I('pct', 'Percentage to set aside', 0.25, 'pct')], [
    O('Set aside from this income', 'money', '{in:income}*{in:pct}'), O('Income received in the last 91 days', 'money', 'SUMIFS(%s,%s)' % (SA('amount'), L91)),
    O('Moved to the set-aside in the last 91 days', 'money', 'SUMIFS(%s,%s)' % (SA('moved'), L91)), O('The percentage would have set aside', 'money', 'SUMIFS(%s,%s)*{in:pct}' % (SA('amount'), L91)),
    O('Set-aside balance now', 'money', BAL_NOW), O('Balance after this set-aside', 'money', '%s+{in:income}*{in:pct}' % BAL_NOW), O('Share of take-home set aside, last 12 months', 'pct', 'IFERROR(SUMIFS(%s,%s,">="&EDATE({today},-12))/SUMIFS(%s,%s,">="&EDATE({today},-12)),0)' % (SA('moved'), SA('date'), SA('amount'), SA('date'))),
    O('Verdict', 'text', vd('Set aside the amount shown'))],
    GR('What if the percentage is', ('15%', {'pct': 0.15}), ('20%', {'pct': 0.2}), ('25%', {'pct': 0.25}), ('30%', {'pct': 0.3}), ('35%', {'pct': 0.35}))))
# 15 set-aside check ------------------------------------------------------------------------------------------------------------------------
NXT = 'SUMIFS(%s,%s,1)'
tools.append(TOOL('set_aside_check', 'Set-aside Check', 'Is the set-aside on track for the next estimated payment',
    'The set-aside balance against the next estimated payment, with the balance expected by then at the monthly average you moved over the last 12 months.', [I('extra', 'Extra you will move before the payment', 0)], [
    O('Set-aside balance now', 'money', BAL_NOW), O('Next payment', 'money', NXT % (EP('payment'), EP('is_next'))), O('Next payment date', 'date', 'IFERROR(SMALL(%s,COUNTIF(%s,"<="&{today})+1),"")' % (EP('date'), EP('date'))),
    O('Balance expected by then', 'money', NXT % (EP('balance_before'), EP('is_next')) + '+{in:extra}'), O('Spare (+) or short (-) at that date', 'money', NXT % (EP('balance_before'), EP('is_next')) + '+{in:extra}-' + NXT % (EP('payment'), EP('is_next'))),
    O('Average moved a month, last 12 months', 'money', 'SUMIFS(%s,%s,">="&EDATE({today},-12))/12' % (SA('moved'), SA('date'))),
    O('Verdict', 'text', 'IF(%s+{in:extra}>=%s,%s,%s)' % (NXT % (EP('balance_before'), EP('is_next')), NXT % (EP('payment'), EP('is_next')), vd('On track'), vd('Short of the next payment')))],
    GR('What if you move extra of', ('Nothing', {'extra': 0}), ('500', {'extra': 500}), ('1000', {'extra': 1000}), ('2000', {'extra': 2000}), ('4000', {'extra': 4000}))))
# 16 year review ------------------------------------------------------------------------------------------------------------------------------
SR = 'IFERROR(%s/%s,0)' % (W('total_saved'), W('basis'))
NWC = '(SUMIFS(%s,%s,EDATE(%s,-1))-SUMIFS(%s,%s,EDATE(%s,-13)))' % (YM('net_worth'), YM('month'), MS, YM('net_worth'), YM('month'), MS)
tools.append(TOOL('year_tool', 'Year Review Tool', 'How did the last 12 months go',
    'Income, spending, saving, debt, interest and the net worth change for the last 12 complete months, with the savings rate against your own target. Estimates from your numbers, not advice.', [I('target', 'Savings rate you want', 0.2, 'pct')], [
    O('Take-home pay', 'money', W('take_home')), O('Counted spending', 'money', W('spending')), O('Total saved', 'money', W('total_saved')), O('Savings rate', 'pct', SR), O('Debt payments', 'money', W('debt_paid')),
    O('Interest paid', 'money', W('interest_paid')), O('Net worth change', 'money', NWC), O('Savings rate, the 12 months before', 'pct', 'IFERROR(%s/%s,0)' % (W('total_saved', 'prev12'), W('basis', 'prev12'))),
    O('Against your target', 'text', 'IF(%s>={in:target},%s,%s)' % (SR, st('Savings rate at or above your target'), st('Savings rate below your target'))),
    O('Verdict', 'text', 'IF(%s>=0,%s,%s)' % (NWC, vd('Net worth up'), vd('Net worth down')))],
    GR('What if your target is', ('10%', {'target': 0.1}), ('15%', {'target': 0.15}), ('20%', {'target': 0.2}), ('25%', {'target': 0.25}), ('30%', {'target': 0.3}))))
# 17 category changes -------------------------------------------------------------------------------------------------------------------------------
def RK(k, c): return 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),%s)' % (CC(c), CC('rise_key'), k, CC('rise_key'), '""' if c == 'category' else '0')
tools.append(TOOL('change_tool', 'Category Changes Check', 'Which categories rose most against last year',
    'The categories that rose most in the last 12 months against the 12 before, with the amount and the share of all rises.', [I('min', 'Only count rises of this amount or more', 100)], [
    O('First: category', 'text', RK(1, 'category')), O('First: up by', 'money', RK(1, 'change')), O('Second: category', 'text', RK(2, 'category')), O('Second: up by', 'money', RK(2, 'change')),
    O('Third: category', 'text', RK(3, 'category')), O('Third: up by', 'money', RK(3, 'change')), O('Categories up by that amount or more', 'int', 'COUNTIFS(%s,">="&{in:min})' % CC('change')),
    O('All rises together', 'money', 'SUMIFS(%s,%s,">0")' % (CC('change'), CC('change'))), O('Share of all rises in the top three', 'pct', 'IFERROR((%s+%s+%s)/SUMIFS(%s,%s,">0"),0)' % (RK(1, 'change'), RK(2, 'change'), RK(3, 'change'), CC('change'), CC('change'))),
    O('Verdict', 'text', 'IF(%s>={in:min},%s,%s)' % (RK(1, 'change'), st('Biggest rise shown'), st('No category is up')))],
    GR('What if you count rises of', ('Any', {'min': 1}), ('50 or more', {'min': 50}), ('100 or more', {'min': 100}), ('300 or more', {'min': 300}), ('1000 or more', {'min': 1000}))))
# 18 next-year plan builder -------------------------------------------------------------------------------------------------------------------------------
PL = 'SUM(%s)*(1+{in:extra})' % NP('plan'); LYT = 'SUM(%s)' % NP('last_year'); INC18 = '(%s)*(1+{set:income_change})' % ('SUMIFS(%s,%s,1)+SUMIFS(%s,%s,1)' % (YM('take_home'), YM('last12'), YM('retirement'), YM('last12')))
tools.append(TOOL('plan_builder', 'Next-year Plan Builder', 'What will next year cost with our typed changes',
    'Last year\'s actuals with the change typed for each category, plus one change you apply to everything: the plan a month and for each paycheck against expected income. An estimate from your numbers.', [I('extra', 'One more change on every category', 0, 'pct')], [
    O('Last 12 months, all categories', 'money', LYT), O('Plan for next year', 'money', PL), O('Plan a month', 'money', '(%s)/12' % PL), O('Plan for each paycheck', 'money', '(%s)/{set:pay_per_year}' % PL),
    O('More (+) or less (-) than last year', 'money', '%s-%s' % (PL, LYT)), O('Change on last year', 'pct', 'IFERROR((%s)/%s-1,0)' % (PL, LYT)),
    O('Expected income, with the change in Settings', 'money', INC18), O('Income left after the plan (+) or short (-)', 'money', '%s-%s' % (INC18, PL)),
    O('Verdict', 'text', 'IF(ABS(%s-%s)<1,%s,IF(%s<%s,%s,%s))' % (PL, LYT, st('Plan matches this year'), PL, LYT, st('Plan is below this year'), st('Plan is above this year')))],
    GR('What if every category changes by', ('-10%', {'extra': -0.1}), ('-5%', {'extra': -0.05}), ('Nothing', {'extra': 0}), ('5%', {'extra': 0.05}), ('10%', {'extra': 0.1}))))
assert len(tools) == 18, len(tools)
