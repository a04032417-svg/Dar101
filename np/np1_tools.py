"""Nonprofit suite part 1: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np1_lists import *
import np1_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def R(t, c_): return '{range:%s.%s}' % (t, c_)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
Y0F = 'DATE(YEAR({today}),1,1)'
ONE = tok('gtype', 'One-time')
DUE = tok('instatus', 'Due'); OVERD = tok('instatus', 'Overdue'); PAIDS = tok('instatus', 'Paid')
BANKED = tok('batch', 'Banked'); BOPEN = tok('batch', 'Open')
ACTIVE = tok('recstatus', 'Active'); FAILED = tok('recstatus', 'Failed')
EXPECTED = tok('mstatus', 'Expected'); REQUESTED = tok('mstatus', 'Requested'); RECEIVED = tok('mstatus', 'Received')
NOTREC = tok('basis', 'Not recorded')
tools = []
LAST = [g for g in D.GF if g['gift_type'] == 'One-time' and g['donor_id']][-1]
STMT_DONOR = 'DN-0662'
HH_DONOR = 'DN-0051'
DUP_DONOR = 'DN-0945'
Y = TODAY.year
# median gift of the last 90 days over the Gift Log (no array formula needed)
N90 = 'COUNTIFS(%s,">="&({today}-90))' % R('gifts', 'date')
ARR90 = '((%s>={today}-90)*%s)' % (R('gifts', 'date'), R('gifts', 'amount'))
MED90 = '((SUMPRODUCT(LARGE(%s,INT((%s+1)/2)))+SUMPRODUCT(LARGE(%s,INT(%s/2)+1)))/2)' % (ARR90, N90, ARR90, N90)

# 1 ------------------------------------------------------------ gift entry check
DID = '{in:donor_id}'
DUPC = '%s,%s,%s,{in:amount},%s,%s,%s,">="&({in:date}-{set:dup_days}),%s,"<="&({in:date}+{set:dup_days})' % (R('gifts', 'donor_id'), DID, R('gifts', 'amount'), R('gifts', 'gift_type'), ONE, R('gifts', 'date'), R('gifts', 'date'))
def DUPN(): return 'COUNTIFS(%s)' % DUPC
def DUPID(): return 'IF(%s=0,0,IFERROR(INDEX(%s,MATCH(SUMIFS(%s,%s),%s,0)),""))' % (DUPN(), R('gifts', 'gift_id'), R('gifts', 'idnum'), DUPC, R('gifts', 'idnum'))
tools.append(TOOL('gift_entry_check', 'Gift Entry Check', 'Can this gift be saved as it is',
    'Type the donor ID, amount, date and fund of a new gift; the tool checks the donor, the fund, a possible duplicate and an unusual size before you save it.', [
    I('donor_id', 'Donor ID', LAST['donor_id'], 'text'), I('amount', 'Gift amount', 150), I('date', 'Gift date', 'today', 'date'), IL('fund', 'Fund', 'fund', 'General Fund'), I('fund_set', 'Fund picked, 1 for yes', 1, 'int')], [
    O('Donors with this ID', 'int', 'COUNTIFS(%s,%s)' % (R('donors', 'donor_id'), DID)), O('Donor name', 'text', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (R('donors', 'donor'), DID, R('donors', 'donor_id'))),
    O('Gifts from this donor, last 12 months', 'int', 'COUNTIFS(%s,%s,%s,">="&({today}-365))' % (R('gifts', 'donor_id'), DID, R('gifts', 'date'))),
    O('Median gift, last 90 days', 'money', MED90), O('Amount that is checked twice', 'money', '{set:big_gift_multiple}*%s' % MED90),
    O('Same-size one-time gifts within the duplicate days', 'int', DUPN()), O('Possible duplicate of gift', 'text', DUPID()),
    O('Written acknowledgement', 'text', 'IF({in:amount}>{set:ack_over},%s,%s)' % (c('Letter needed'), c('Note enough'))), O('Thank-you due by', 'date', 'WORKDAY({in:date},{set:thankyou_days})'),
    O('Gift size against your median', 'num', 'IFERROR({in:amount}/%s,0)' % MED90),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,%s)=0,%s,IF({in:fund_set}=0,%s,IF(%s>0,%s&" "&%s,IF({in:amount}>{set:big_gift_multiple}*%s,%s,%s))))' % (
        R('donors', 'donor_id'), DID, c('Fix the donor'), c('Fix the fund'), DUPN(), c('Possible duplicate'), DUPID(), MED90, c('Check the amount'), c('Save')))],
    GR('What if', ('The same gift again', {'amount': LAST['amount']}), ('A very large gift', {'amount': 9000}), ('No fund picked', {'fund_set': 0}), ('A small gift', {'amount': 25}), ('A gift above the letter amount', {'amount': 300}))))

# 2 ------------------------------------------------------------ weekly banking tie-out
WK = '%s,">="&({today}-7*{in:weeks}),%s,%s' % (R('batches', 'week_start'), R('batches', 'status'), BANKED)
OFFN = '(COUNTIFS(%s,%s,">"&{in:tol})+COUNTIFS(%s,%s,"<"&-{in:tol}))' % (WK, R('batches', 'gap'), WK, R('batches', 'gap'))
BIG = 'ROUND(SUMPRODUCT(MAX((%s=%s)*(%s>={today}-7*{in:weeks})*ABS(%s-%s))),2)' % (R('batches', 'status'), BANKED, R('batches', 'week_start'), R('batches', 'banked_amount'), R('batches', 'logged_amount'))
tools.append(TOOL('banking_tieout', 'Weekly Banking Tie-out', 'Does what we logged match what we banked',
    'Type how many weeks to look back and the gap you accept; logged and banked amounts are compared batch by batch and the batches off by more than the gap are counted and named.', [
    I('weeks', 'Weeks to look back', 13, 'int'), I('tol', 'Gap you accept', 25)], [
    O('Banked batches in the period', 'int', 'COUNTIFS(%s)' % WK), O('Logged in those batches', 'money', 'SUMIFS(%s,%s)' % (R('batches', 'logged_amount'), WK)),
    O('Banked in those batches', 'money', 'SUMIFS(%s,%s)' % (R('batches', 'banked_amount'), WK)), O('Banked less logged', 'money', 'SUMIFS(%s,%s)-SUMIFS(%s,%s)' % (R('batches', 'banked_amount'), WK, R('batches', 'logged_amount'), WK)),
    O('Batches off by more than the gap you accept', 'int', OFFN), O('Largest gap, no sign', 'money', BIG),
    O('Batch with the largest gap', 'text', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (R('batches', 'batch_id'), BIG, R('batches', 'abs_gap'))),
    O('Batches not banked yet', 'int', 'COUNTIFS(%s,%s)' % (R('batches', 'status'), BOPEN)), O('Logged in batches not banked yet', 'money', 'SUMIFS(%s,%s,%s)' % (R('batches', 'logged_amount'), R('batches', 'status'), BOPEN)),
    O('Average days from week start to bank', 'num', 'IFERROR(AVERAGEIFS(%s,%s),0)' % (R('batches', 'days_to_bank'), WK)),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (OFFN, c('Tied'), c('Chase batches'), OFFN))],
    GR('What if', ('Accept no gap', {'tol': 0}), ('Accept 10', {'tol': 10}), ('Accept 25', {'tol': 25}), ('Accept 50', {'tol': 50}), ('Accept 150', {'tol': 150}))))

# 3 ------------------------------------------------------------ thank-you backlog ranker
def TOPG(k):
    m = 'MATCH(%d,%s,0)' % (k, R('gifts', 'thank_rank'))
    return 'IFERROR(INDEX(%s,%s)&" "&INDEX(%s,%s)&" "&INDEX(%s,%s)&" "&INDEX(%s,%s),"")' % (R('gifts', 'gift_id'), m, R('gifts', 'donor'), m, R('gifts', 'amount'), m, R('gifts', 'days_waiting'), m)
LATE3 = 'COUNTIFS(%s,">"&{in:days})' % R('gifts', 'wd_waiting')
tools.append(TOOL('thankyou_ranker', 'Thank-you Backlog Ranker', 'Which gifts still need a thank-you, oldest first',
    'Type the working days you allow; every gift without a thank-you is counted, the oldest five are named with their wait, and the verdict says Send today or On time.', [
    I('days', 'Working days you allow', 2, 'int')], [
    O('Gifts waiting for a thank-you', 'int', 'COUNTIFS(%s,">=0")' % R('gifts', 'days_waiting')), O('Late under your rule', 'int', LATE3),
    O('Amount waiting', 'money', 'SUMIFS(%s,%s,">=0")' % (R('gifts', 'amount'), R('gifts', 'days_waiting'))), O('Oldest wait in days', 'int', 'MAX(%s)' % R('gifts', 'days_waiting')),
    O('Average wait in days', 'num', 'IFERROR(AVERAGEIFS(%s,%s,">=0"),0)' % (R('gifts', 'days_waiting'), R('gifts', 'days_waiting'))), O('Gifts that need a letter', 'int', 'COUNTIFS(%s,1)' % R('gifts', 'letter_due')),
    O('First: gift, donor, amount, days waiting', 'text', TOPG(1)), O('Second: gift, donor, amount, days waiting', 'text', TOPG(2)), O('Third: gift, donor, amount, days waiting', 'text', TOPG(3)),
    O('Fourth: gift, donor, amount, days waiting', 'text', TOPG(4)), O('Fifth: gift, donor, amount, days waiting', 'text', TOPG(5)),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (LATE3, c('Send today'), c('On time')))],
    GR('What if', ('Allow 0 days', {'days': 0}), ('Allow 1 day', {'days': 1}), ('Allow 2 days', {'days': 2}), ('Allow 3 days', {'days': 3}), ('Allow 5 days', {'days': 5}))))

# 4 ------------------------------------------------------------ acknowledgement amount rule
AB = '%s,">"&{in:limit}' % R('gifts', 'amount')
tools.append(TOOL('ack_rule', 'Acknowledgement Amount Rule', 'Which larger gifts still need a written letter',
    'Type your own amount above which a gift gets a written acknowledgement; gifts above it without a letter are counted, the oldest wait is shown and the verdict says Letter needed or Note enough.', [
    I('limit', 'Letter above this amount, your own rule', 250), I('days', 'Days to look back', 90, 'int')], [
    O('Gifts above the amount in the period', 'int', 'COUNTIFS(%s,%s,">="&({today}-{in:days}))' % (AB, R('gifts', 'date'))), O('Their total', 'money', 'SUMIFS(%s,%s,%s,">="&({today}-{in:days}))' % (R('gifts', 'amount'), AB, R('gifts', 'date'))),
    O('Still without a letter', 'int', 'COUNTIFS(%s,%s,">=0")' % (AB, R('gifts', 'days_waiting'))), O('Amount without a letter', 'money', 'SUMIFS(%s,%s,%s,">=0")' % (R('gifts', 'amount'), AB, R('gifts', 'days_waiting'))),
    O('Letters already sent in the period', 'int', 'COUNTIFS(%s,%s,">="&({today}-{in:days}),%s,">0")' % (AB, R('gifts', 'date'), R('gifts', 'ack_sent'))),
    O('Share with a letter', 'pct', 'IFERROR(COUNTIFS(%s,%s,">="&({today}-{in:days}),%s,">0")/COUNTIFS(%s,%s,">="&({today}-{in:days})),0)' % (AB, R('gifts', 'date'), R('gifts', 'ack_sent'), AB, R('gifts', 'date'))),
    O('Oldest gift without a letter, days', 'int', 'SUMPRODUCT(MAX((%s>{in:limit})*(%s=0)*({today}-%s)))' % (R('gifts', 'amount'), R('gifts', 'ack_sent'), R('gifts', 'date'))),
    O('Largest gift without a letter', 'money', 'SUMPRODUCT(MAX((%s>{in:limit})*(%s=0)*%s))' % (R('gifts', 'amount'), R('gifts', 'ack_sent'), R('gifts', 'amount'))),
    O('Gifts a note is enough for, in the period', 'int', 'COUNTIFS(%s,"<="&{in:limit},%s,">="&({today}-{in:days}))' % (R('gifts', 'amount'), R('gifts', 'date'))),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,%s,">=0")>0,%s,%s)' % (AB, R('gifts', 'days_waiting'), c('Letter needed'), c('Note enough')))],
    GR('What if', ('Letter above 100', {'limit': 100}), ('Letter above 250', {'limit': 250}), ('Letter above 500', {'limit': 500}), ('Letter above 1,000', {'limit': 1000}), ('Letter above 2,500', {'limit': 2500}))))

# 5 ------------------------------------------------------------ year-end statement builder
SD = '%s,{in:donor_id},%s,">="&DATE({in:year},1,1),%s,"<="&DATE({in:year},12,31)' % (R('gifts', 'donor_id'), R('gifts', 'date'), R('gifts', 'date'))
SCOND = '(%s={in:donor_id})*(%s>=DATE({in:year},1,1))*(%s<=DATE({in:year},12,31))' % (R('gifts', 'donor_id'), R('gifts', 'date'), R('gifts', 'date'))
FIRSTG = 'SUMPRODUCT(MIN(%s*%s+(1-%s)*1000000))' % (SCOND, R('gifts', 'date'), SCOND)
tools.append(TOOL('statement_builder', 'Year-end Statement Builder', 'Is this donor statement ready to print',
    'Type a donor ID and a year; gifts, total, funds and first and last gift are listed, with a flag for a gift with no fund. A record of the gifts you can keep; ask your accountant what your rules need.', [
    I('donor_id', 'Donor ID', STMT_DONOR, 'text'), I('year', 'Year', Y, 'int')], [
    O('Donor name', 'text', 'IFERROR(INDEX(%s,MATCH({in:donor_id},%s,0)),"")' % (R('donors', 'donor'), R('donors', 'donor_id'))), O('Gifts in the year', 'int', 'COUNTIFS(%s)' % SD),
    O('Total given in the year', 'money', 'SUMIFS(%s,%s)' % (R('gifts', 'amount'), SD)), O('Average gift', 'money', 'IFERROR(SUMIFS(%s,%s)/COUNTIFS(%s),0)' % (R('gifts', 'amount'), SD, SD)),
    O('Largest gift', 'money', 'SUMPRODUCT(MAX(%s*%s))' % (SCOND, R('gifts', 'amount'))), O('First gift', 'date', 'IF(%s>=1000000,"",%s)' % (FIRSTG, FIRSTG)), O('Last gift', 'date', 'IF(COUNTIFS(%s)=0,"",SUMPRODUCT(MAX(%s*%s)))' % (SD, SCOND, R('gifts', 'date'))),
    O('Funds the gifts went to', 'int', 'SUMPRODUCT(--(COUNTIFS(%s,{in:donor_id},%s,%s,%s,">="&DATE({in:year},1,1),%s,"<="&DATE({in:year},12,31))>0))' % (R('gifts', 'donor_id'), R('gifts', 'fund'), R('funds', 'fund'), R('gifts', 'date'), R('gifts', 'date'))),
    O('Gifts missing a fund', 'int', 'COUNTIFS(%s,%s,2)' % (SD.replace(R('gifts', 'date'), R('gifts', 'date')), R('gifts', 'issue')) if False else 'COUNTIFS(%s,%s,2)' % (SD, R('gifts', 'issue'))),
    O('Gifts without a thank-you yet', 'int', 'COUNTIFS(%s,%s,">=0")' % (SD, R('gifts', 'days_waiting'))), O('Given last year, from your earlier log', 'money', 'SUMIFS(%s,%s,{in:donor_id})' % (R('giving_years', 'last_year'), R('giving_years', 'donor_id'))),
    O('Verdict', 'text', 'IF(COUNTIFS(%s)=0,%s,IF(COUNTIFS(%s,%s,2)>0,%s,%s))' % (SD, c('No gifts in the year'), SD, R('gifts', 'issue'), c('Gifts missing a fund'), c('Ready')))],
    ))

# 6 ------------------------------------------------------------ statement batch list
GYF = R('giving_years', 'statement_total')
tools.append(TOOL('statement_batch', 'Statement Batch List', 'How many yearly statements can we print now',
    'Type the smallest yearly total that gets a statement; every donor with a total at or above it is counted as ready or blocked by a data check, with the amounts and a verdict.', [
    I('min', 'Smallest yearly total that gets a statement', 25)], [
    O('Statement year', 'int', '{set:statement_year}'), O('Donors with a total at or above the minimum', 'int', 'COUNTIFS(%s,">="&{in:min})' % GYF),
    O('Ready to print', 'int', 'COUNTIFS(%s,">="&{in:min},%s,%s)' % (GYF, R('giving_years', 'flag'), c('Ready'))), O('Blocked, gifts missing a fund', 'int', 'COUNTIFS(%s,">="&{in:min},%s,%s)' % (GYF, R('giving_years', 'flag'), c('Gifts missing a fund'))),
    O('Amount in ready statements', 'money', 'SUMIFS(%s,%s,">="&{in:min},%s,%s)' % (GYF, GYF, R('giving_years', 'flag'), c('Ready'))), O('Amount in blocked statements', 'money', 'SUMIFS(%s,%s,">="&{in:min},%s,%s)' % (GYF, GYF, R('giving_years', 'flag'), c('Gifts missing a fund'))),
    O('Average statement total', 'money', 'IFERROR(AVERAGEIFS(%s,%s,">="&{in:min}),0)' % (GYF, GYF)), O('Largest statement total', 'money', 'MAX(%s)' % GYF),
    O('Donors below the minimum, no statement', 'int', 'COUNTIFS(%s,">0",%s,"<"&{in:min})' % (GYF, GYF)),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">="&{in:min},%s,%s)=0,%s&" "&COUNTIFS(%s,">="&{in:min},%s,%s),%s&" "&COUNTIFS(%s,">="&{in:min},%s,%s))' % (
        GYF, R('giving_years', 'flag'), c('Gifts missing a fund'), c('Print statements'), GYF, R('giving_years', 'flag'), c('Ready'), c('Fix first'), GYF, R('giving_years', 'flag'), c('Gifts missing a fund')))],
    GR('What if', ('Minimum 1', {'min': 1}), ('Minimum 25', {'min': 25}), ('Minimum 100', {'min': 100}), ('Minimum 250', {'min': 250}), ('Minimum 1,000', {'min': 1000}))))

# 7 ------------------------------------------------------------ pledge schedule planner
INST = 'ROUND({in:total}/{in:inst},2)'
DUEN = 'IF({today}>={in:first},MIN({in:inst},INT(DATEDIF({in:first},{today},"M")/{in:every})+1),0)'
BEH = 'MAX(0,%s-{in:paid_n})' % DUEN
tools.append(TOOL('pledge_planner', 'Pledge Schedule Planner', 'Is this pledge on schedule',
    'Type the pledge total, the number of instalments, the months between them, the first date and how many are paid; the dates, amounts, balance and days behind are worked out.', [
    I('total', 'Pledge total', 12000), I('inst', 'Number of instalments', 6, 'int'), I('every', 'Months between instalments', 2, 'int'), I('first', 'First due date', 'today-100', 'date'), I('paid_n', 'Instalments paid so far', 1, 'int')], [
    O('Instalment amount', 'money', INST), O('Last instalment, with rounding', 'money', '{in:total}-%s*({in:inst}-1)' % INST), O('Last due date', 'date', 'EDATE({in:first},{in:every}*({in:inst}-1))'),
    O('Next due date', 'date', 'IF({in:paid_n}<{in:inst},EDATE({in:first},{in:every}*{in:paid_n}),"")'), O('Instalments due by today', 'int', DUEN), O('Should have been paid by today', 'money', 'MIN({in:total},%s*%s)' % (DUEN, INST)),
    O('Paid to date', 'money', 'MIN({in:total},{in:paid_n}*%s)' % INST), O('Balance', 'money', 'MAX(0,{in:total}-{in:paid_n}*%s)' % INST), O('Instalments behind', 'int', BEH),
    O('Days behind', 'int', 'IF(%s>0,{today}-EDATE({in:first},{in:every}*{in:paid_n}),0)' % BEH),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&({today}-EDATE({in:first},{in:every}*{in:paid_n})))' % (BEH, c('On schedule'), c('Days behind')))],
    GR('What if', ('All paid so far', {'paid_n': 2}), ('One behind', {'paid_n': 1}), ('Two behind', {'paid_n': 0}), ('Monthly instalments, 3 paid', {'every': 1, 'paid_n': 3}), ('Twelve instalments', {'inst': 12, 'every': 1, 'paid_n': 2}))))

# 8 ------------------------------------------------------------ overdue pledge ranker
def TOPP(k):
    m = 'MATCH(%d,%s,0)' % (k, R('instalments', 'overdue_rank'))
    return 'IFERROR(INDEX(%s,%s)&" "&INDEX(%s,%s)&" "&INDEX(%s,%s)&" "&INDEX(%s,%s),"")' % (R('instalments', 'pp_id'), m, R('instalments', 'donor'), m, R('instalments', 'days_overdue'), m, R('instalments', 'amount_due'), m)
OLD = 'MAX(%s)' % R('instalments', 'days_overdue')
tools.append(TOOL('overdue_ranker', 'Overdue Pledge Ranker', 'Which pledge instalments do we chase or write off',
    'Type the days that mean chase, final notice and write-off; open instalments are ranked by days overdue and amount, and the verdict names the step for the oldest.', [
    I('chase', 'Days late before you chase', 30, 'int'), I('final', 'Days late before a final notice', 90, 'int'), I('wo', 'Days late before you propose a write-off', 180, 'int')], [
    O('Instalments overdue now', 'int', 'COUNTIFS(%s,">0")' % R('instalments', 'days_overdue')), O('Amount overdue now', 'money', 'SUMIFS(%s,%s,">0")' % (R('instalments', 'amount_due'), R('instalments', 'days_overdue'))),
    O('At or past the chase days', 'int', 'COUNTIFS(%s,">="&{in:chase})' % R('instalments', 'days_overdue')), O('Amount at or past the chase days', 'money', 'SUMIFS(%s,%s,">="&{in:chase})' % (R('instalments', 'amount_due'), R('instalments', 'days_overdue'))),
    O('At or past the final notice days', 'int', 'COUNTIFS(%s,">="&{in:final})' % R('instalments', 'days_overdue')), O('At or past the write-off days', 'int', 'COUNTIFS(%s,">="&{in:wo})' % R('instalments', 'days_overdue')),
    O('Oldest instalment, days overdue', 'int', OLD),
    O('Write-off proposal date of the oldest', 'date', 'IFERROR(INDEX(%s,MATCH(1,%s,0))+{in:wo},"")' % (R('instalments', 'due_date'), R('instalments', 'overdue_rank'))),
    O('First: instalment, donor, days, amount', 'text', TOPP(1)), O('Second: instalment, donor, days, amount', 'text', TOPP(2)),     O('Verdict', 'text', 'IF(%s=0,%s,IF(%s>={in:wo},%s,IF(%s>={in:final},%s,IF(%s>={in:chase},%s,%s))))' % (OLD, c('Nothing overdue'), OLD, c('Propose write-off'), OLD, c('Final notice'), OLD, c('Chase'), c('Not late yet')))],
    GR('What if', ('Chase after 14 days', {'chase': 14}), ('Chase after 30 days', {'chase': 30}), ('Chase after 60 days', {'chase': 60}), ('Chase after 75 days', {'chase': 75}), ('Chase after 90 days', {'chase': 90}))))

# 9 ------------------------------------------------------------ pledges due this quarter
def MD(a, b): return 'SUMIFS(%s,%s,%s,%s,">="&%s,%s,"<="&%s)' % (R('instalments', 'amount_due'), R('instalments', 'status'), DUE, R('instalments', 'due_date'), a, R('instalments', 'due_date'), b)
def MC(a, b): return 'COUNTIFS(%s,%s,%s,">="&%s,%s,"<="&%s)' % (R('instalments', 'status'), DUE, R('instalments', 'due_date'), a, R('instalments', 'due_date'), b)
M1 = (MD('{today}', 'EOMONTH({today},0)')); M2 = MD('EOMONTH({today},0)+1', 'EOMONTH({today},1)'); M3 = MD('EOMONTH({today},1)+1', 'EOMONTH({today},2)')
TOT3 = MD('{today}', 'EOMONTH({today},2)')
AVG6 = '(SUMIFS(%s,%s,">="&EDATE({today},-6))/6)' % (R('instalments', 'amount_paid'), R('instalments', 'paid_on'))
tools.append(TOOL('pledges_due', 'Pledges Due This Quarter', 'How much pledge money should arrive in the next three months',
    'Type the share you expect on time in a Base, Best and Worst case (your estimate); instalments due in the next three months are added up and set against your last six months.', [
    I('base', 'Base case, share received on time', 0.90, 'pct'), I('best', 'Best case, share received on time', 1.0, 'pct'), I('worst', 'Worst case, share received on time', 0.70, 'pct')], [
    O('Instalments due, rest of this month', 'int', MC('{today}', 'EOMONTH({today},0)')), O('Amount due, rest of this month', 'money', M1), O('Amount due, next month', 'money', M2), O('Amount due, the month after', 'money', M3),
    O('Instalments due in the three months', 'int', MC('{today}', 'EOMONTH({today},2)')), O('Amount due in the three months', 'money', TOT3), O('Base case, expected', 'money', '%s*{in:base}' % TOT3), O('Best case, expected', 'money', '%s*{in:best}' % TOT3),
    O('Worst case, expected', 'money', '%s*{in:worst}' % TOT3), O('Already overdue, not in the months above', 'money', 'SUMIFS(%s,%s,">0")' % (R('instalments', 'amount_due'), R('instalments', 'days_overdue'))),
    O('Paid per month, your last six months', 'money', AVG6), O('Three months due against three months of your history', 'num', 'IFERROR(%s/(%s*3),0)' % (TOT3, AVG6)), O('Open pledge balance', 'money', 'SUMIFS(%s,%s,%s)' % (R('pledges', 'balance'), R('pledges', 'status'), tok('plstatus', 'Open'))),
    O('Verdict', 'text', c('Counts toward cash forecast'))],
    GR('What if', ('Base 70%', {'base': 0.7}), ('Base 80%', {'base': 0.8}), ('Base 90%', {'base': 0.9}), ('Base 95%', {'base': 0.95}), ('Base 100%', {'base': 1.0}))))

# 10 ----------------------------------------------------------- recurring base value
RMA = lambda m: 'SUMIFS(%s,%s,%s)' % (R('recurring_months', 'recurring_amount'), R('recurring_months', 'month'), m)
LASTM = 'EDATE(%s,-1)' % MS
GROW = 'IFERROR(%s/%s-1,0)' % (RMA(LASTM), RMA('EDATE(%s,-13)' % MS))
R3 = 'SUMIFS(%s,%s,">="&EDATE(%s,-3),%s,"<"&%s)/3' % (R('recurring_months', 'recurring_amount'), R('recurring_months', 'month'), MS, R('recurring_months', 'month'), MS)
R3P = 'SUMIFS(%s,%s,">="&EDATE(%s,-6),%s,"<"&EDATE(%s,-3))/3' % (R('recurring_months', 'recurring_amount'), R('recurring_months', 'month'), MS, R('recurring_months', 'month'), MS)
tools.append(TOOL('recurring_base', 'Recurring Base Value', 'Is our monthly giving base growing',
    'Type the change that counts as flat; the monthly amount of active recurring donors, the yearly value and the growth of the last full month against 12 months before are worked out.', [
    I('flat', 'Change that still counts as flat', 0.03, 'pct')], [
    O('Active recurring donors', 'int', 'COUNTIFS(%s,%s)' % (R('recurring', 'status'), ACTIVE)), O('Monthly amount of active donors', 'money', 'SUMIFS(%s,%s,%s)' % (R('recurring', 'amount'), R('recurring', 'status'), ACTIVE)),
    O('Annualised value', 'money', '12*SUMIFS(%s,%s,%s)' % (R('recurring', 'amount'), R('recurring', 'status'), ACTIVE)),
    O('Recurring share of gift amount, last 90 days', 'pct', 'IFERROR(SUMIFS(%s,%s,%s,%s,">="&({today}-90))/SUMIFS(%s,%s,">="&({today}-90)),0)' % (R('gifts', 'amount'), R('gifts', 'gift_type'), tok('gtype', 'Recurring'), R('gifts', 'date'), R('gifts', 'amount'), R('gifts', 'date'))),
    O('Recurring amount, last full month', 'money', RMA(LASTM)), O('Same month a year before', 'money', RMA('EDATE(%s,-13)' % MS)), O('Growth against 12 months before', 'pct', GROW),
    O('Average of the last 3 full months', 'money', R3), O('Average of the 3 months before those', 'money', R3P), O('Trend of the last 6 months', 'pct', 'IFERROR(%s/(%s)-1,0)' % (R3, R3P)),
    O('Next month, your estimate', 'money', 'IFERROR(%s*POWER(%s/(%s),1/3),0)' % (R3, R3, R3P)),
    O('Verdict', 'text', 'IF(%s>{in:flat},%s,IF(%s<-{in:flat},%s,%s))' % (GROW, c('Base growing'), GROW, c('Base shrinking'), c('Base flat')))],
    GR('What if', ('Flat means 0%', {'flat': 0}), ('Flat means 1%', {'flat': 0.01}), ('Flat means 3%', {'flat': 0.03}), ('Flat means 5%', {'flat': 0.05}), ('Flat means 10%', {'flat': 0.10}))))

# 11 ----------------------------------------------------------- failed payment chaser
def TOPR(k):
    m = 'MATCH(%d,%s,0)' % (k, R('recurring', 'chase_rank'))
    return 'IFERROR(INDEX(%s,%s)&" "&INDEX(%s,%s)&" "&INDEX(%s,%s)&" "&INDEX(%s,%s),"")' % (R('recurring', 'recurring_id'), m, R('recurring', 'donor'), m, R('recurring', 'amount'), m, R('recurring', 'missed'), m)
CONT = '(COUNTIFS(%s,1,%s,%s)+COUNTIFS(%s,1,%s,%s,%s,">="&{in:after}))' % (R('recurring', 'needs'), R('recurring', 'status'), FAILED, R('recurring', 'needs'), R('recurring', 'status'), ACTIVE, R('recurring', 'missed'))
tools.append(TOOL('failed_chaser', 'Failed Payment Chaser', 'Which monthly donors do we contact today',
    'Type how many missed gifts mean a call; recurring donors with a failed or missed payment are ranked by amount, and the verdict says Contact today or Wait one more cycle.', [
    I('after', 'Missed gifts before you contact the donor', 2, 'int')], [
    O('Recurring donors needing attention', 'int', 'COUNTIFS(%s,1)' % R('recurring', 'needs')), O('Monthly amount at risk', 'money', 'SUMIFS(%s,%s,1)' % (R('recurring', 'amount'), R('recurring', 'needs'))),
    O('Yearly value at risk', 'money', '12*SUMIFS(%s,%s,1)' % (R('recurring', 'amount'), R('recurring', 'needs'))), O('To contact today', 'int', CONT), O('To leave one more cycle', 'int', 'COUNTIFS(%s,1)-%s' % (R('recurring', 'needs'), CONT)),
    O('With a failed payment', 'int', 'COUNTIFS(%s,%s)' % (R('recurring', 'status'), FAILED)), O('Active with two or more missed', 'int', 'COUNTIFS(%s,%s,%s,">=2")' % (R('recurring', 'status'), ACTIVE, R('recurring', 'missed'))),
    O('First: recurring ID, donor, amount, missed', 'text', TOPR(1)), O('Second: recurring ID, donor, amount, missed', 'text', TOPR(2)), O('Third: recurring ID, donor, amount, missed', 'text', TOPR(3)), O('Fourth: recurring ID, donor, amount, missed', 'text', TOPR(4)),
    O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (CONT, c('Contact today'), c('Wait one more cycle')))],
    GR('What if', ('Contact after 1 missed', {'after': 1}), ('Contact after 2 missed', {'after': 2}), ('Contact after 3 missed', {'after': 3}))))

# 12 ----------------------------------------------------------- recurring conversion planner
CAND = '(COUNTIFS(%s,">=3",%s,%s)-COUNTIFS(%s,%s))' % (R('donors', 'gifts'), R('donors', 'status'), tok('dstatus', 'Active'), R('recurring', 'status'), ACTIVE)
NEED = 'ROUNDUP({in:target}/{in:avg},0)'
ASK = 'ROUNDUP(%s/{in:conv},0)' % NEED
tools.append(TOOL('conversion_planner', 'Recurring Conversion Planner', 'How many one-time donors do we ask to give monthly',
    'Type the monthly income you want, the average monthly gift and the share you expect to say yes (your estimate); donors who gave three or more times and are not yet monthly are the people to ask.', [
    I('target', 'New monthly income wanted', 800), I('avg', 'Average monthly gift', 25), I('conv', 'Share who say yes, your estimate', 0.12, 'pct')], [
    O('Active donors with 3 or more gifts, not monthly yet', 'int', CAND), O('New monthly donors needed', 'int', NEED), O('Donors to ask', 'int', ASK), O('Share of the candidates to ask', 'pct', 'IFERROR(%s/%s,0)' % (ASK, CAND)),
    O('Monthly income from active recurring donors now', 'money', 'SUMIFS(%s,%s,%s)' % (R('recurring', 'amount'), R('recurring', 'status'), ACTIVE)),
    O('Monthly income after the target', 'money', 'SUMIFS(%s,%s,%s)+{in:target}' % (R('recurring', 'amount'), R('recurring', 'status'), ACTIVE)), O('Yearly value of the new income', 'money', '12*{in:target}'),
    O('Median monthly gift in your log', 'money', 'MEDIAN(%s)' % R('recurring', 'amount')), O('Donors to ask if half as many say yes', 'int', 'ROUNDUP(%s/({in:conv}/2),0)' % NEED),
    O('Verdict', 'text', 'IF(%s<=%s,%s&" "&%s,%s)' % (ASK, CAND, c('Ask donors'), ASK, c('Widen the list')))],
    GR('What if', ('5% say yes', {'conv': 0.05}), ('10% say yes', {'conv': 0.10}), ('15% say yes', {'conv': 0.15}), ('20% say yes', {'conv': 0.20}), ('30% say yes', {'conv': 0.30}))))

# 13 ----------------------------------------------------------- in-kind value check
UNIT13 = '({in:value}/MAX(1,{in:qty}))'
TYP13 = 'IFERROR(AVERAGEIFS(%s,%s,{in:kind}),0)' % (R('inkind', 'unit_value'), R('inkind', 'kind'))
tools.append(TOOL('inkind_check', 'In-kind Value Check', 'Is the value of this in-kind gift recorded properly',
    'Type the kind, value, quantity and who set the value; the value of one is compared with your own log for that kind, and the verdict says Value recorded or Basis missing.', [
    IL('kind', 'Kind', 'ikind', 'Food'), I('value', 'Fair value of the gift', 1200), I('qty', 'Quantity', 4, 'int'), IL('basis', 'Who set the value', 'basis', 'Price list')], [
    O('Value of one', 'money', UNIT13), O('Typical value of one of this kind in your log', 'money', TYP13), O('Against the typical value', 'num', 'IFERROR(%s/%s,0)' % (UNIT13, TYP13)),
    O('Gifts of this kind this year', 'int', 'COUNTIFS(%s,{in:kind},%s,">="&%s)' % (R('inkind', 'kind'), R('inkind', 'date'), Y0F)), O('Average value of a gift of this kind', 'money', 'IFERROR(AVERAGEIFS(%s,%s,{in:kind}),0)' % (R('inkind', 'fair_value'), R('inkind', 'kind'))),
    O('Gifts in your log without a value basis', 'int', 'COUNTIFS(%s,%s)' % (R('inkind', 'value_basis'), NOTREC)), O('Share with a value basis', 'pct', 'IFERROR(1-COUNTIFS(%s,%s)/COUNTA(%s),0)' % (R('inkind', 'value_basis'), NOTREC, R('inkind', 'inkind_id'))),
    O('Value of in-kind gifts this year', 'money', 'SUMIFS(%s,%s,">="&%s)' % (R('inkind', 'fair_value'), R('inkind', 'date'), Y0F)),
    O('Verdict', 'text', 'IF({in:basis}=%s,%s,IF(%s>3*%s,%s,%s))' % (NOTREC, c('Basis missing'), UNIT13, TYP13, c('Check the amount'), c('Value recorded')))],
    GR('What if', ('Value 200', {'value': 200}), ('Value 600', {'value': 600}), ('Value 1,200', {'value': 1200}), ('Value 3,000', {'value': 3000}), ('Value 9,000', {'value': 9000}))))

# 14 ----------------------------------------------------------- match chase ranker
def TOPM(k):
    m = 'MATCH(%d,%s,0)' % (k, R('matching', 'open_rank'))
    return 'IFERROR(INDEX(%s,%s)&" "&INDEX(%s,%s)&" "&INDEX(%s,%s),"")' % (R('matching', 'employer'), m, R('matching', 'expected'), m, R('matching', 'days_waiting'), m)
PASTC = 'COUNTIFS(%s,1,%s,">"&{in:chase})' % (R('matching', 'open'), R('matching', 'days_waiting'))
BIGM = 'SUMPRODUCT(MAX((%s=%s)*({today}-%s>{in:chase})*%s))' % (R('matching', 'status'), REQUESTED, R('matching', 'requested_on'), R('matching', 'expected'))
BIGID = 'SUMIFS(%s,%s,%s,%s,%s,%s,"<"&({today}-{in:chase}))' % (R('matching', 'idnum'), R('matching', 'status'), REQUESTED, R('matching', 'expected'), BIGM, R('matching', 'requested_on'))
BIGEMP = 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (R('matching', 'employer'), BIGID, R('matching', 'idnum'))
tools.append(TOOL('match_chase_ranker', 'Match Chase Ranker', 'Which employer matches do we chase',
    'Type the days you wait before chasing; open matching gifts (money an employer adds to a donor gift) are counted, ranked by amount and the verdict names the biggest employer to chase.', [
    I('chase', 'Days waiting before you chase', 45, 'int')], [
    O('Matching gifts still open', 'int', 'COUNTIFS(%s,1)' % R('matching', 'open')), O('Amount expected, open', 'money', 'SUMIFS(%s,%s,1)' % (R('matching', 'expected'), R('matching', 'open'))),
    O('Waiting longer than the chase days', 'int', PASTC), O('Amount waiting longer than the chase days', 'money', 'SUMIFS(%s,%s,1,%s,">"&{in:chase})' % (R('matching', 'expected'), R('matching', 'open'), R('matching', 'days_waiting'))),
    O('Average days waiting, open matches', 'num', 'IFERROR(AVERAGEIFS(%s,%s,1),0)' % (R('matching', 'days_waiting'), R('matching', 'open'))), O('Not yet requested', 'int', 'COUNTIFS(%s,%s)' % (R('matching', 'status'), EXPECTED)),
    O('Received to date, all matches', 'money', 'SUMIFS(%s,%s,%s)' % (R('matching', 'received'), R('matching', 'status'), RECEIVED)),
    O('First: employer, expected, days waiting', 'text', TOPM(1)), O('Second: employer, expected, days waiting', 'text', TOPM(2)), O('Third: employer, expected, days waiting', 'text', TOPM(3)), O('Fourth: employer, expected, days waiting', 'text', TOPM(4)),
    O('Biggest employer to chase', 'text', 'IF(%s>0,%s,0)' % (PASTC, BIGEMP)),
    O('Verdict', 'text', 'IF(%s>0,%s&" "&%s,%s)' % (PASTC, c('Chase now'), BIGEMP, c('Wait')))],
    GR('What if', ('Chase after 14 days', {'chase': 14}), ('Chase after 30 days', {'chase': 30}), ('Chase after 45 days', {'chase': 45}), ('Chase after 90 days', {'chase': 90}), ('Chase after 365 days', {'chase': 365}))))

# 15 ----------------------------------------------------------- match opportunity finder
OPC = 'COUNTIFS(%s,%s,%s,">="&{in:min},%s,">="&({today}-{in:days}))' % (R('gifts', 'gift_type'), ONE, R('gifts', 'amount'), R('gifts', 'date'))
OPS = 'SUMIFS(%s,%s,%s,%s,">="&{in:min},%s,">="&({today}-{in:days}))' % (R('gifts', 'amount'), R('gifts', 'gift_type'), ONE, R('gifts', 'amount'), R('gifts', 'date'))
tools.append(TOOL('match_opportunity', 'Match Opportunity Finder', 'How many donors should we ask about an employer match',
    'Type the smallest gift worth asking about, the share of donors whose employer matches (your estimate) and the ratio; one-time gifts give the donors to ask and the extra money.', [
    I('min', 'Smallest gift worth asking about', 100), I('days', 'Days to look back', 90, 'int'), I('share', 'Share with an employer program, your estimate', 0.20, 'pct'), I('ratio', 'Match ratio, 1 means one for one', 1.0, 'num')], [
    O('One-time gifts at or above the minimum', 'int', OPC), O('Their total', 'money', OPS), O('Donors to ask', 'int', 'ROUNDUP(%s*{in:share},0)' % OPC), O('Extra money if they all match, your estimate', 'money', 'ROUND(%s*{in:share}*{in:ratio},0)' % OPS),
    O('Matches already asked for or expected in the period', 'int', 'COUNTIFS(%s,">="&({today}-{in:days}))' % R('matching', 'requested_on')),
    O('Average match received so far', 'money', 'IFERROR(AVERAGEIFS(%s,%s,%s),0)' % (R('matching', 'received'), R('matching', 'status'), RECEIVED)),
    O('Matches received so far', 'int', 'COUNTIFS(%s,%s)' % (R('matching', 'status'), RECEIVED)), O('Matching gifts as a share of all gift amount this year', 'pct', 'IFERROR(SUMIFS(%s,%s,%s,%s,">="&%s)/SUMIFS(%s,%s,">="&%s),0)' % (R('gifts', 'amount'), R('gifts', 'gift_type'), tok('gtype', 'Matching gift'), R('gifts', 'date'), Y0F, R('gifts', 'amount'), R('gifts', 'date'), Y0F)),
    O('Verdict', 'text', 'IF(ROUNDUP(%s*{in:share},0)>0,%s&" "&ROUNDUP(%s*{in:share},0),%s)' % (OPC, c('Ask donors'), OPC, c('Nothing to chase')))],
    GR('What if', ('5% have a program', {'share': 0.05}), ('10% have a program', {'share': 0.10}), ('20% have a program', {'share': 0.20}), ('30% have a program', {'share': 0.30}), ('Two for one', {'ratio': 2.0}))))

# 16 ----------------------------------------------------------- duplicate donor finder
DL = lambda col: 'IFERROR(INDEX(%s,MATCH({in:donor_id},%s,0)),"")' % (R('donors', col), R('donors', 'donor_id'))
EM = DL('email'); TY = DL('type')
SAMEM = 'IF(%s="",0,COUNTIFS(%s,%s,%s,%s))' % (EM, R('donors', 'email'), EM, R('donors', 'type'), TY)
FIRST = 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (R('donors', 'donor_id'), EM, R('donors', 'email'))
SAMNM = 'IF(%s="",0,COUNTIFS(%s,%s))' % (DL('donor'), R('donors', 'donor'), DL('donor'))
tools.append(TOOL('duplicate_donor', 'Duplicate Donor Finder', 'Are these two donor records the same donor',
    'Type a donor ID; records with the same e-mail and type or the same name are counted, the first record is named and the verdict says merge into it or keep both.', [
    I('donor_id', 'Donor ID to check', DUP_DONOR, 'text')], [
    O('Donor name', 'text', DL('donor')), O('E-mail', 'text', EM), O('Records with this e-mail and type', 'int', SAMEM), O('Records with this name', 'int', SAMNM), O('First record with this e-mail', 'text', FIRST),
    O('Gifts on this record', 'int', 'IFERROR(INDEX(%s,MATCH({in:donor_id},%s,0)),0)' % (R('donors', 'gifts'), R('donors', 'donor_id'))), O('Gifts on the first record', 'int', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('donors', 'gifts'), FIRST, R('donors', 'donor_id'))),
    O('Total given on both records', 'money', 'IFERROR(INDEX(%s,MATCH({in:donor_id},%s,0)),0)+IF(%s={in:donor_id},0,IFERROR(INDEX(%s,MATCH(%s,%s,0)),0))' % (R('donors', 'total_given'), R('donors', 'donor_id'), FIRST, R('donors', 'total_given'), FIRST, R('donors', 'donor_id'))),
    O('Same-day, same-size gift pairs this year', 'int', 'ROUNDDOWN(COUNTIFS(%s,{in:donor_id},%s,3)/2,0)' % (R('gifts', 'donor_id'), R('gifts', 'issue'))),
    O('Verdict', 'text', 'IF(%s>1,IF(%s={in:donor_id},%s,{in:donor_id}&" "&%s&" "&%s),IF(%s>1,%s,%s))' % (SAMEM, FIRST, c('Keep'), c('merge into'), FIRST, SAMNM, c('Keep both'), c('Keep')))]))

# 17 ----------------------------------------------------------- household giving view
HM = 'IFERROR(DATEDIF(IFERROR(INDEX(%s,MATCH({in:donor_id},%s,0)),0),{today},"M"),"")' % (R('donors', 'last_gift'), R('donors', 'donor_id'))
GY = lambda col: 'SUMIFS(%s,%s,{in:donor_id})' % (R('giving_years', col), R('giving_years', 'donor_id'))
tools.append(TOOL('household_view', 'Household Giving View', 'Is this household still giving',
    'Type a donor ID and the months that mean lapsed; the contacts, gifts, total, last gift and the years given of the last three are shown with a giving state (Active, Lapsing or Lapsed).', [
    I('donor_id', 'Household donor ID', HH_DONOR, 'text'), I('lapse', 'Months without a gift that mean lapsed', 12, 'int')], [
    O('Household name', 'text', 'IFERROR(INDEX(%s,MATCH({in:donor_id},%s,0)),"")' % (R('donors', 'donor'), R('donors', 'donor_id'))), O('Contacts under this household', 'int', 'COUNTIFS(%s,{in:donor_id})' % R('contacts', 'donor_id')),
    O('Gifts, all time in your log', 'int', 'IFERROR(INDEX(%s,MATCH({in:donor_id},%s,0)),0)' % (R('donors', 'gifts'), R('donors', 'donor_id'))), O('Total given, all time', 'money', 'IFERROR(INDEX(%s,MATCH({in:donor_id},%s,0)),0)' % (R('donors', 'total_given'), R('donors', 'donor_id'))),
    O('Last gift', 'date', 'IFERROR(IF(INDEX(%s,MATCH({in:donor_id},%s,0))=0,"",INDEX(%s,MATCH({in:donor_id},%s,0))),"")' % (R('donors', 'last_gift'), R('donors', 'donor_id'), R('donors', 'last_gift'), R('donors', 'donor_id'))),
    O('Months since the last gift', 'int', HM), O('Given this year', 'money', GY('this_year')), O('Given last year', 'money', GY('last_year')), O('Given two years ago', 'money', GY('two_years_ago')),
    O('Years given, of the last three', 'int', '(%s>0)+(%s>0)+(%s>0)' % (GY('this_year'), GY('last_year'), GY('two_years_ago'))),
    O('Verdict', 'text', 'IF(%s="",%s,IF(%s>={in:lapse},%s,IF(%s>={in:lapse}-3,%s,%s)))' % (HM, c('No gift yet'), HM, c('Lapsed'), HM, c('Lapsing'), c('Active')))],
    GR('What if', ('Lapsed after 3 months', {'lapse': 3}), ('Lapsed after 6 months', {'lapse': 6}), ('Lapsed after 9 months', {'lapse': 9}), ('Lapsed after 12 months', {'lapse': 12}), ('Lapsed after 24 months', {'lapse': 24}))))

# 18 ----------------------------------------------------------- data health score
NG = 'COUNTA(%s)' % R('gifts', 'gift_id')
def SC(cond):  # score of the gifts matching cond (a COUNTIFS argument list), weights from the inputs
    return 'IFERROR(100*({in:w1}*COUNTIFS(%s,%s,1)/COUNTIFS(%s)+{in:w2}*COUNTIFS(%s,%s,1)/COUNTIFS(%s)+{in:w3}*COUNTIFS(%s,%s,"<4")/COUNTIFS(%s)),0)' % (
        cond, R('gifts', 'filled'), cond, cond, R('gifts', 'thank_ok'), cond, cond, R('gifts', 'issue'), cond)
THISM = '%s,%s' % (R('gifts', 'month'), MS); LASTM2 = '%s,EDATE(%s,-1)' % (R('gifts', 'month'), MS)
FIX = 'COUNTIFS(%s,">0",%s,"<4")' % (R('gifts', 'issue'), R('gifts', 'issue'))
tools.append(TOOL('data_health', 'Data Health Score', 'Is the gift log clean enough to report from',
    'Set how much each check counts; the share of gifts with a donor and a fund, thanked on time and free of record problems gives a score for this month, compared with your own last month.', [
    I('w1', 'Weight: donor and fund filled', 0.4, 'pct'), I('w2', 'Weight: thanked on time', 0.3, 'pct'), I('w3', 'Weight: no record problem', 0.3, 'pct')], [
    O('Gifts in the log', 'int', NG), O('With donor and fund filled', 'pct', 'IFERROR(COUNTIFS(%s,1)/%s,0)' % (R('gifts', 'filled'), NG)), O('Thanked on time', 'pct', 'IFERROR(COUNTIFS(%s,1)/%s,0)' % (R('gifts', 'thank_ok'), NG)),
    O('Free of record problems', 'pct', 'IFERROR(COUNTIFS(%s,"<4")/%s,0)' % (R('gifts', 'issue'), NG)), O('Gifts missing a donor or fund, or possible duplicates', 'int', FIX),
    O('Score, this month', 'num', SC(THISM)), O('Score, last month', 'num', SC(LASTM2)), O('Change on last month', 'num', '%s-%s' % (SC(THISM), SC(LASTM2))),
    O('Score, all gifts in the log', 'num', SC('%s,">0"' % R('gifts', 'amount'))), O('Gifts in batches that are off', 'int', 'COUNTIFS(%s,4)' % R('gifts', 'issue')),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (FIX, c('Healthy'), c('Fix rows'), FIX))],
    GR('What if', ('Donor and fund count most', {'w1': 0.7, 'w2': 0.15, 'w3': 0.15}), ('Thank-you counts most', {'w1': 0.15, 'w2': 0.7, 'w3': 0.15}), ('Equal weights', {'w1': 0.34, 'w2': 0.33, 'w3': 0.33}), ('Records count most', {'w1': 0.15, 'w2': 0.15, 'w3': 0.7}))))
assert len(tools) == 18
