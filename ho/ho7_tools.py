"""Home Management suite part 7: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho7_lists import *
import ho7_data as D
from ho7_tables import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, dflt): return IN(k, label, 'list', key(lst, dflt), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def V(*parts):
    """a verdict: words (list labels) and numbers or names joined with spaces; a tuple ('f', formula) is a value"""
    out = []
    for p in parts:
        if isinstance(p, tuple): out.append('(' + p[1] + ')')
        else: out.append(lbl(p))
    return '&" "&'.join(out)
def F(x): return ('f', x)
def G(cnt, expr): return 'IF(%s=0,"",%s)' % (cnt, expr)
def MNAME(expr): return 'CHOOSE(%s,%s)' % (expr, ','.join(tok('mname', m) for m in MONTH_NAMES))
def PCT(x): return 'ROUND(%s*100,0)&"%%"' % x


tools = []
TRV = 'COUNTIFS(%s,%s,%s,1)' % (DR('kind'), K_TRAV, DR('active'))
ACTIVE = 'COUNTIFS(%s,1)' % DR('active')

# 1 ---------------------------------------------------------------- renewals in the next 90 days
def N1(extra=''): return 'COUNTIFS(%s,"<="&{in:within}%s)' % (RNR('days_left'), extra)
FIRST1 = 'IF(INDEX(%s,1)="","",%s)'
tools.append(TOOL('renewals90', 'Renewals 90 Days Tool', 'What comes due in the next 90 days, all types in one list',
    'Documents, contracts, warranties, vehicle dates, pet dates and filter, alarm and service tasks in one ranked list; type how many days ahead to look and read the count by type and the first item.', [
    I('within', 'Look this many days ahead, 1 to 90', 90)], [
    O('Renewals in the window', 'int', N1()), O('Documents', 'int', N1(',%s,%s' % (RNR('type'), RT_DOC))), O('Contracts and policies', 'int', N1(',%s,%s' % (RNR('type'), RT_CON))),
    O('Warranties', 'int', N1(',%s,%s' % (RNR('type'), RT_WAR))), O('Vehicle dates', 'int', N1(',%s,%s' % (RNR('type'), RT_VEH))), O('Pet dates', 'int', N1(',%s,%s' % (RNR('type'), RT_PET))),
    O('Home tasks', 'int', N1(',%s,%s' % (RNR('type'), RT_TASK))), O('First item', 'text', 'INDEX(%s,1)&""' % RNR('name')), O('Its date', 'date', 'IF(INDEX(%s,1)="","",INDEX(%s,1))' % (RNR('name'), RNR('date'))),
    O('Days to it', 'int', 'IF(INDEX(%s,1)="","",INDEX(%s,1))' % (RNR('name'), RNR('days_left'))), O('Its owner', 'text', 'INDEX(%s,1)&""' % RNR('owner')),
    O('Its action date', 'date', 'IF(INDEX(%s,1)="","",INDEX(%s,1))' % (RNR('name'), RNR('action'))),
    O('Items past their action date or due to start now', 'int', 'COUNTIFS(%s,%s)+COUNTIFS(%s,%s)' % (RNR('verdict'), W_MISSED, RNR('verdict'), W_NOW)),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (N1(), lbl('Nothing due in this window'), V(F(N1()), 'renewals in', F('{in:within}'), 'days, first item:', F('INDEX(%s,1)' % RNR('name')), 'in', F('INDEX(%s,1)' % RNR('days_left')), 'days')))],
    GR('What if you look closer', ('14 days', {'within': 14}), ('30 days', {'within': 30}), ('45 days', {'within': 45}), ('60 days', {'within': 60}), ('90 days', {'within': 90}))))

# 2 ---------------------------------------------------------------- travel documents against a trip date
END2 = '({in:trip}+{in:days}-1)'
COV2 = 'COUNTIFS(%s,%s,%s,1,%s,">="&%s)' % (DR('kind'), K_TRAV, DR('active'), DR('expiry'), END2)
BEF2 = '(%s-%s)' % (TRV, COV2)
EARL2 = G(BEF2, 'MINIFS(%s,%s,%s,%s,1,%s,"<"&%s)' % (DR('expiry'), DR('kind'), K_TRAV, DR('active'), DR('expiry'), END2))
RK2 = G(BEF2, 'MINIFS(%s,%s,%s,%s,1,%s,"<"&%s)' % (DR('drk'), DR('kind'), K_TRAV, DR('active'), DR('expiry'), END2))
BY2 = '(%s-{in:lead})' % EARL2
tools.append(TOOL('trip_docs', 'Trip Document Check', 'Do the travel documents last until the family is back',
    'Each travel document expiry against the trip date you type and the lead time you type: how many expire before the trip, the date to renew by and how many days of lead time are missed.', [
    I('trip', 'First day of the trip', 'today+70', 'date'), I('days', 'Days away', 10), I('lead', 'Lead time: act this many days before the expiry', 60)], [
    O('Travel documents tracked', 'int', TRV), O('Cover the trip', 'int', COV2), O('Expire before the trip ends', 'int', BEF2), O('Earliest expiry before the trip', 'date', EARL2),
    O('That document', 'text', 'IF(%s="","",INDEX(%s,MATCH(%s,%s,0)))' % (RK2, DR('doc'), RK2, DR('drk'))), O('Renew by', 'date', 'IF(%s="","",%s)' % (EARL2, BY2)),
    O('Days to renew by, negative is past', 'int', 'IF(%s="","",%s-{today})' % (EARL2, BY2)), O('Lead time missed by, days', 'int', 'IF(%s="","",MAX(0,{today}-%s))' % (EARL2, BY2)),
    O('Trip ends on', 'date', END2), O('Days to the trip', 'int', '{in:trip}-{today}'),
    O('Verdict', 'text', 'IF(%s=0,"",IF(%s=0,%s,IF(%s<{today},%s,%s)))' % (TRV, BEF2, lbl('All cover the trip'), BY2, V('Lead time missed by', F('{today}-%s' % BY2), 'days'), V(F(BEF2), 'expire before it, renew in', F('%s-{today}' % BY2), 'days')))],
    GR('What if the lead time changes', ('Lead 30 days', {'lead': 30}), ('Lead 45 days', {'lead': 45}), ('Lead 60 days', {'lead': 60}), ('Lead 90 days', {'lead': 90}), ('Lead 120 days', {'lead': 120}), ('Trip in 100 days', {'trip': '=TODAY()+100'}))))

# 3 ---------------------------------------------------------------- action date finder
ST3 = '({in:expiry}-{in:lead})'
tools.append(TOOL('action_finder', 'Action Date Finder', 'When to start a renewal: the expiry minus the days you need',
    'Type any expiry or renewal date and the days you need before it: the date to start, the days from now, the first working day on or after it and how much of the lead time is left.', [
    I('expiry', 'Expiry or renewal date', 'today+90', 'date'), I('lead', 'Days needed before it', 60)], [
    O('Start by', 'date', ST3), O('Days from now, negative is past', 'int', '%s-{today}' % ST3), O('Days to the expiry', 'int', '{in:expiry}-{today}'),
    O('First working day to start', 'date', 'WORKDAY(%s-1,1)' % ST3), O('Share of the lead time left', 'pct', 'IF({in:lead}=0,0,MAX(0,MIN(1,({in:expiry}-{today})/{in:lead})))'),
    O('Documents already with this action date', 'int', 'COUNTIFS(%s,%s,%s,1)' % (DR('action_date'), ST3, DR('active'))),
    O('Status', 'text', 'IF(%s<{today},%s,IF(%s-{today}<={set:act_now_days},%s,IF(%s-{today}<={set:soon_days},%s,%s)))' % (ST3, W_MISSED, ST3, W_NOW, ST3, W_SOON, W_OK)),
    O('Verdict', 'text', 'IF(%s<{today},%s,%s)' % (ST3, V('Lead time missed by', F('{today}-%s' % ST3), 'days'), V('Start in', F('%s-{today}' % ST3), 'days from now')))],
    GR('What if you need more or fewer days', ('14 days', {'lead': 14}), ('30 days', {'lead': 30}), ('45 days', {'lead': 45}), ('60 days', {'lead': 60}), ('90 days', {'lead': 90}), ('120 days', {'lead': 120}))))

# 4 ---------------------------------------------------------------- lead time what-if
IN4 = 'COUNTIFS(%s,1,%s,">=0",%s,"<="&{in:lead})' % (DR('active'), DR('days_left'), DR('days_left'))
ST4 = 'COUNTIFS(%s,1,%s,">=0",%s,"<="&{in:lead},%s,%s)' % (DR('active'), DR('days_left'), DR('days_left'), DR('status'), S_START)
NR4 = 'MINIFS(%s,%s,1,%s,">="&0)' % (DR('drk'), DR('active'), DR('days_left'))
tools.append(TOOL('lead_whatif', 'Lead Time What-if', 'Documents that need action at a longer or shorter lead time',
    'The lead time stepped five times: the documents whose expiry falls inside it, how many of those you have not started and how many are started; your own typed lead times for comparison.', [
    I('lead', 'Lead time to test, days', 60)], [
    O('Documents inside the lead time', 'int', IN4), O('Of those, renewal started', 'int', ST4), O('Of those, not started', 'int', '%s-%s' % (IN4, ST4)),
    O('Documents beyond the lead time', 'int', 'COUNTIFS(%s,1,%s,">"&{in:lead})' % (DR('active'), DR('days_left'))),
    O('Share of active documents inside', 'pct', 'IFERROR(ROUND(%s/%s,3),0)' % (IN4, ACTIVE)), O('Longest lead time you typed', 'int', 'MAX(%s)' % DR('renew_lead_days')),
    O('Average lead time you typed', 'int', 'IFERROR(ROUND(AVERAGEIFS(%s,%s,1),0),0)' % (DR('renew_lead_days'), DR('active')), ),
    O('Nearest document', 'text', 'IF(COUNTIFS(%s,1,%s,">=0")=0,"",INDEX(%s,MATCH(%s,%s,0)))' % (DR('active'), DR('days_left'), DR('doc'), NR4, DR('drk'))),
    O('Its days left', 'int', 'IF(COUNTIFS(%s,1,%s,">=0")=0,"",INDEX(%s,MATCH(%s,%s,0)))' % (DR('active'), DR('days_left'), DR('days_left'), NR4, DR('drk'))),
    O('Verdict', 'text', V(F(IN4), 'documents need action at', F('{in:lead}'), 'days'))],
    GR('What if the lead time changes', ('14 days', {'lead': 14}), ('30 days', {'lead': 30}), ('45 days', {'lead': 45}), ('60 days', {'lead': 60}), ('90 days', {'lead': 90}), ('180 days', {'lead': 180}))))

# 5 ---------------------------------------------------------------- passports for the family trip
END5 = '({in:trip}+{in:days}-1+{in:extra})'
def EXP5(h): return G('COUNTIFS(%s,%s,%s,1,%s,%s)' % (DR('kind'), K_TRAV, DR('active'), DR('holder'), h), 'MINIFS(%s,%s,%s,%s,1,%s,%s)' % (DR('expiry'), DR('kind'), K_TRAV, DR('active'), DR('holder'), h))
COV5 = 'COUNTIFS(%s,%s,%s,1,%s,">="&%s)' % (DR('kind'), K_TRAV, DR('active'), DR('expiry'), END5)
tools.append(TOOL('family_trip', 'Passports For The Trip', 'Do all four travel documents cover the family trip',
    'The four travellers against the trip date: each expiry and the days it is valid after you are back, with the extra days some countries ask for after the return; check the entry rules of where you go.', [
    I('trip', 'First day of the trip', 'today+70', 'date'), I('days', 'Days away', 10), I('extra', 'Extra days of validity asked after the return', 0)], [
    O('Adult 1 travel document expires', 'date', EXP5(HP1)), O('Adult 2 travel document expires', 'date', EXP5(HP2)), O('Child 1 travel document expires', 'date', EXP5(HPC1)), O('Child 2 travel document expires', 'date', EXP5(HPC2)),
    O('Adult 1 days valid after the trip', 'int', 'IF(%s="","",%s-%s)' % (EXP5(HP1), EXP5(HP1), END5)), O('Adult 2 days valid after the trip', 'int', 'IF(%s="","",%s-%s)' % (EXP5(HP2), EXP5(HP2), END5)),
    O('Child 1 days valid after the trip', 'int', 'IF(%s="","",%s-%s)' % (EXP5(HPC1), EXP5(HPC1), END5)), O('Child 2 days valid after the trip', 'int', 'IF(%s="","",%s-%s)' % (EXP5(HPC2), EXP5(HPC2), END5)),
    O('Travellers with a travel document', 'int', TRV), O('Travel documents that cover the trip', 'int', COV5), O('Days to the trip', 'int', '{in:trip}-{today}'),
    O('Verdict', 'text', V(F(COV5), 'of', F(TRV), 'travel documents cover the trip'))],
    GR('What if the trip or the extra days change', ('Trip in 30 days', {'trip': '=TODAY()+30'}), ('Trip in 70 days', {'trip': '=TODAY()+70'}), ('Trip in 120 days', {'trip': '=TODAY()+120'}), ('Trip in 300 days', {'trip': '=TODAY()+300'}), ('Extra 180 days', {'extra': 180}))))

# 6 ---------------------------------------------------------------- contract review window
CON6 = 'COUNTIFS(%s,%s,%s,1)' % (DR('rtype'), RT_CON, DR('active'))
AHEAD6 = 'COUNTIFS(%s,%s,%s,1,%s,">=0")' % (DR('rtype'), RT_CON, DR('active'), DR('days_left'))
NX6 = G(AHEAD6, 'MINIFS(%s,%s,%s,%s,1,%s,">=0")' % (DR('drk'), DR('rtype'), RT_CON, DR('active'), DR('days_left')))
def PX6(c): return 'IF(%s="","",INDEX(%s,MATCH(%s,%s,0)))' % (NX6, DR(c), NX6, DR('drk'))
REVBY6 = '(%s-{in:review})' % PX6('expiry')
tools.append(TOOL('contract_review', 'Contract Review Window', 'Which contract or policy to review next',
    'Contracts and policies with a review lead you type: how many are inside the review window now, the next one to review, the date to look at it and how many days remain.', [
    I('review', 'Review this many days before the end', 45)], [
    O('Contracts and policies tracked', 'int', CON6), O('Ending in the next 12 months', 'int', 'SUMIFS(%s,%s,%s)' % (DR('in12'), DR('rtype'), RT_CON)),
    O('Inside the review window now', 'int', 'COUNTIFS(%s,%s,%s,1,%s,">=0",%s,"<="&{in:review})' % (DR('rtype'), RT_CON, DR('active'), DR('days_left'), DR('days_left'))),
    O('Next to review', 'text', PX6('doc')), O('It ends on', 'date', PX6('expiry')), O('Review by', 'date', 'IF(%s="","",%s)' % (NX6, REVBY6)),
    O('Days to the review date, negative is past', 'int', 'IF(%s="","",%s-{today})' % (NX6, REVBY6)), O('Days to the end', 'int', PX6('days_left')), O('Handled by', 'text', PX6('handler') + '&""'),
    O('Verdict', 'text', 'IF(%s="",%s,IF(%s<={today},%s,%s))' % (NX6, lbl('No contract ahead'), REVBY6, V('Review', F(PX6('doc')), 'now, it ends in', F(PX6('days_left')), 'days'), V('Review', F(PX6('doc')), 'in', F('%s-{today}' % REVBY6), 'days')))],
    GR('What if the review lead changes', ('30 days', {'review': 30}), ('45 days', {'review': 45}), ('60 days', {'review': 60}), ('90 days', {'review': 90}), ('120 days', {'review': 120}))))

# 7 ---------------------------------------------------------------- notice period checker
POS7 = 'MATCH({in:doc_id},%s,0)' % DR('doc_id')
def DX7(c): return 'IFERROR(INDEX(%s,%s),"")' % (DR(c), POS7)
BY7 = '(%s-{in:notice})' % DX7('expiry')
tools.append(TOOL('notice_checker', 'Notice Period Checker', 'Is there still time to give notice on a contract',
    'Type a contract ID from Documents and its notice period (check your contract): the end date, the last day to give notice and whether the window is still open.', [
    I('doc_id', 'Document ID of the contract', 'DC-15', 'text'), I('notice', 'Notice period, days', 60)], [
    O('Contract', 'text', DX7('doc') + '&""'), O('Ends on', 'date', DX7('expiry')), O('Give notice by', 'date', 'IF(%s="","",%s)' % (DX7('expiry'), BY7)),
    O('Days to give notice, negative is past', 'int', 'IF(%s="","",%s-{today})' % (DX7('expiry'), BY7)), O('Days to the end', 'int', DX7('days_left')),
    O('Last working day to send it', 'date', 'IF(%s="","",WORKDAY(%s+1,-1))' % (DX7('expiry'), BY7)), O('Handled by', 'text', DX7('handler') + '&""'),
    O('Verdict', 'text', 'IF(%s="","",IF(%s>={today},%s,%s))' % (DX7('expiry'), BY7, V('Give notice in', F('%s-{today}' % BY7), 'days'), lbl('Notice window passed')))],
    GR('What if the notice period changes', ('30 days', {'notice': 30}), ('60 days', {'notice': 60}), ('90 days', {'notice': 90}), ('120 days', {'notice': 120}), ('180 days', {'notice': 180}), ('365 days', {'notice': 365}))))

# 8 ---------------------------------------------------------------- renewals per month
IT8 = 'SUMIFS(%s,%s,"<"&{in:months})' % (RMR('items'), RMR('mk'))
MX8 = 'MAXIFS(%s,%s,"<"&{in:months})' % (RMR('items'), RMR('mk'))
POS8 = 'MATCH(%s,%s,0)' % (MX8, RMR('items'))
MN8 = G(MX8, MNAME('MONTH(INDEX(%s,%s))' % (RMR('month'), POS8)))
tools.append(TOOL('renewals_month', 'Renewals Per Month Tool', 'Which month of the next 12 is the busiest',
    'The renewals of the next months counted from the six source sheets: the busiest month, the months with nothing and the split by type; type how many months to look at.', [
    I('months', 'Months to look at, 1 to 12', 12)], [
    O('Renewals in these months', 'int', IT8), O('Busiest month', 'text', MN8), O('Renewals in the busiest month', 'int', MX8), O('Months with nothing due', 'int', 'COUNTIFS(%s,"<"&{in:months},%s,0)' % (RMR('mk'), RMR('items'))),
    O('Documents and contracts', 'int', 'SUMIFS(%s,%s,"<"&{in:months})' % (RMR('docs'), RMR('mk'))), O('Warranty ends', 'int', 'SUMIFS(%s,%s,"<"&{in:months})' % (RMR('warr'), RMR('mk'))),
    O('Vehicle dates', 'int', 'SUMIFS(%s,%s,"<"&{in:months})' % (RMR('veh'), RMR('mk'))), O('Pet dates', 'int', 'SUMIFS(%s,%s,"<"&{in:months})' % (RMR('pets'), RMR('mk'))),
    O('Filter, alarm and service tasks', 'int', 'SUMIFS(%s,%s,"<"&{in:months})' % (RMR('tasks'), RMR('mk'))), O('Average renewals a month', 'num', 'ROUND(%s/{in:months},1)' % IT8),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (IT8, lbl('Nothing due in these months'), V('Busiest month', F(MN8), 'with', F(MX8), 'renewals')))],
    GR('What if you look at fewer months', ('3 months', {'months': 3}), ('6 months', {'months': 6}), ('9 months', {'months': 9}), ('12 months', {'months': 12}))))

# 9 ---------------------------------------------------------------- documents without a place
NO9 = 'SUM(%s)' % DR('kept_missing')
tools.append(TOOL('docs_no_place', 'Documents Without A Place', 'Which documents have no kept-where place typed',
    'Active documents with an empty Kept where: how many, how many of them come due soon and the first one to fix; a paper nobody can find is the one that expires.', [
    I('days', 'Count the ones due within this many days', 365)], [
    O('Active documents', 'int', ACTIVE), O('With a place', 'int', '%s-%s' % (ACTIVE, NO9)), O('Without a place', 'int', NO9), O('Share without a place', 'pct', 'IFERROR(ROUND(%s/%s,3),0)' % (NO9, ACTIVE)),
    O('Without a place and due soon', 'int', 'COUNTIFS(%s,1,%s,">=0",%s,"<="&{in:days})' % (DR('kept_missing'), DR('days_left'), DR('days_left'))),
    O('First one to fix', 'text', G(NO9, 'INDEX(%s,MATCH(1,%s,0))' % (DR('doc'), DR('kept_missing')))), O('Its expiry', 'date', G(NO9, 'INDEX(%s,MATCH(1,%s,0))' % (DR('expiry'), DR('kept_missing')))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (NO9, lbl('Every document has a place'), V('Add a place for', F(NO9), 'documents')))],
    GR('What if you look further ahead', ('30 days', {'days': 30}), ('60 days', {'days': 60}), ('90 days', {'days': 90}), ('180 days', {'days': 180}), ('365 days', {'days': 365}))))

# 10 --------------------------------------------------------------- who holds which document
H10 = 'COUNTIFS(%s,{in:holder},%s,1)' % (DR('holder'), DR('active'))
NX10 = G('COUNTIFS(%s,{in:holder},%s,">=0")' % (DR('holder'), DR('days_left')), 'MINIFS(%s,%s,{in:holder},%s,">=0")' % (DR('drk'), DR('holder'), DR('days_left')))
def PX10(c): return 'IF(%s="","",INDEX(%s,MATCH(%s,%s,0)))' % (NX10, DR(c), NX10, DR('drk'))
tools.append(TOOL('holder_docs', 'Who Holds Which Document', 'How many documents each person holds and the next expiry',
    'Pick a holder: the documents held, the next expiry and which one it is, those due in 12 months, past their action date or with no place; the whole household holds the shared ones.', [
    IL('holder', 'Holder', 'epeople', 'Child 1')], [
    O('Documents held', 'int', H10), O('Next expiry', 'date', PX10('expiry')), O('Days to it', 'int', PX10('days_left')), O('Next document', 'text', PX10('doc') + '&""'),
    O('Due in the next 12 months', 'int', 'SUMIFS(%s,%s,{in:holder})' % (DR('in12'), DR('holder'))), O('Past their action date', 'int', 'COUNTIFS(%s,{in:holder},%s,"<0")' % (DR('holder'), DR('dta'))),
    O('Renewal started', 'int', 'COUNTIFS(%s,{in:holder},%s,%s,%s,1)' % (DR('holder'), DR('status'), S_START, DR('active'))), O('With no place kept', 'int', 'SUMIFS(%s,%s,{in:holder})' % (DR('kept_missing'), DR('holder'))),
    O('Travel documents held', 'int', 'COUNTIFS(%s,{in:holder},%s,%s,%s,1)' % (DR('holder'), DR('kind'), K_TRAV, DR('active'))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (H10, V(F('{in:holder}'), 'has no documents'), V(F('{in:holder}'), 'has', F(H10), 'documents, next in', F(PX10('days_left')), 'days')))],
    GR('What if you pick another holder', ('Adult 1', {'holder': '=' + HP1}), ('Adult 2', {'holder': '=' + HP2}), ('Child 1', {'holder': '=' + HPC1}), ('Child 2', {'holder': '=' + HPC2}), ('Whole household', {'holder': '=' + HPW}))))

# 11 --------------------------------------------------------------- renewal load by adult
def L11(h): return '(' + '+'.join('COUNTIFS(%s,%s,%s,1)' % (R(t, 'handler' if t != 'tasks' else 'assigned'), h, R(t, 'in12')) for t in SRC) + ')'
A1_, A2_, TR_ = L11(H1), L11(H2), L11(HT)
SH11 = 'IFERROR(%s/(%s+%s),0)' % (A1_, A1_, A2_)
tools.append(TOOL('renewal_load', 'Renewal Load By Adult', 'Who handles the renewals of the next 12 months',
    'Renewals of the next 12 months by who handles them (adult 1, adult 2 or a trade) and adult 1 share against a fair share you type. A line for a talk, not a score.', [
    I('fair', 'Fair share for adult 1', 0.5, 'pct'), I('margin', 'Fair within this margin', 0.15, 'pct')], [
    O('Handled by adult 1', 'int', A1_), O('Handled by adult 2', 'int', A2_), O('Handled by a trade', 'int', TR_), O('Renewals in the next 12 months', 'int', '%s+%s+%s' % (A1_, A2_, TR_)),
    O('Adult 1 share of the adult-handled', 'pct', 'ROUND(%s,3)' % SH11), O('Adult 2 share of the adult-handled', 'pct', 'IF(%s+%s=0,0,ROUND(1-%s,3))' % (A1_, A2_, SH11)),
    O('Adult 1 share against the fair share', 'pct', 'ROUND(%s-{in:fair},3)' % SH11), O('Renewals to move to even it out', 'int', 'MAX(0,ROUND((%s-{in:fair})*(%s+%s),0))' % (SH11, A1_, A2_)),
    O('Verdict', 'text', 'IF(%s+%s=0,"",%s&" "&IF(ABS(%s-{in:fair})<={in:margin},%s,IF(%s>{in:fair},%s,%s)))' % (A1_, A2_, V('Adult 1 handles', F(PCT(SH11)), 'of renewals,'), SH11, lbl('in balance'), SH11, lbl('above your fair share'), lbl('below your fair share')))],
    GR('What if the fair share or margin changes', ('Fair 40%', {'fair': 0.4}), ('Fair 50%', {'fair': 0.5}), ('Fair 60%', {'fair': 0.6}), ('Margin 5%', {'margin': 0.05}), ('Margin 25%', {'margin': 0.25}))))

# 12 --------------------------------------------------------------- sitter sheet builder
EMP12 = 'COUNTIFS(%s,0)' % SR('filled')
tools.append(TOOL('sitter_builder', 'Sitter Sheet Builder', 'Is the one-page sitter sheet ready to print',
    'The typed lines of the Sitter sheet checked against Team, routines, places and Contacts: how many are filled and how old the routines are. First names and numbers only.', [
    I('stale', 'A routine or place is old after this many days', 180)], [
    O('Lines on the sheet', 'int', 'COUNTA(%s)' % SR('item')), O('Lines filled', 'int', 'SUM(%s)' % SR('filled')), O('Lines empty', 'int', EMP12),
    O('Children and household numbers filled', 'int', 'COUNTIFS(%s,%s,%s,1)' % (SR('source'), tok('ssrc', 'Team'), SR('filled'))), O('Routine lines filled', 'int', 'COUNTIFS(%s,%s,%s,1)' % (SR('source'), tok('ssrc', 'Home routines'), SR('filled'))),
    O('Where-things lines filled', 'int', 'COUNTIFS(%s,%s,%s,1)' % (SR('source'), tok('ssrc', 'Where things are'), SR('filled'))), O('Contact lines filled', 'int', 'COUNTIFS(%s,%s,%s,1)' % (SR('source'), tok('ssrc', 'Contacts'), SR('filled'))),
    O('Routines not reviewed for that long', 'int', 'COUNTIFS(%s,">"&{in:stale})' % R('routines', 'age')), O('Places not checked for that long', 'int', 'COUNTIFS(%s,">"&{in:stale})' % R('where_things', 'age')),
    O('Sheet for the evening of', 'date', 'IF(COUNTA(%s)=0,"",INDEX(%s,1))' % (SR('item'), SR('sheet_date'))),
    O('Verdict', 'text', 'IF(COUNTA(%s)=0,"",IF(%s=0,%s,%s))' % (SR('item'), EMP12, lbl('Ready to print'), V('Sheet lines still empty:', F(EMP12))))],
    GR('What if old means sooner', ('90 days', {'stale': 90}), ('180 days', {'stale': 180}), ('365 days', {'stale': 365}), ('540 days', {'stale': 540}))))

# 13 --------------------------------------------------------------- emergency contacts check
MISS13 = '(COUNTIFS(%s,0)+COUNTIFS(%s,0))' % (ER('phone_ok'), CR('phone_ok'))
tools.append(TOOL('emergency_check', 'Emergency Contacts Check', 'Which emergency or household contacts are missing a phone',
    'The emergency sheet and the contacts directory checked for phones, and the numbers not checked for the days you type; adults, school, neighbour and trades are counted separately.', [
    I('days', 'Check a number again after this many days', 180)], [
    O('Emergency lines', 'int', 'COUNTA(%s)' % ER('who')), O('Emergency lines with a phone', 'int', 'SUM(%s)' % ER('phone_ok')), O('Contacts in the directory', 'int', 'COUNTA(%s)' % CR('contact_id')),
    O('Contacts without a phone', 'int', 'COUNTIFS(%s,0)' % CR('phone_ok')), O('Contacts missing a phone, both sheets', 'int', MISS13),
    O('Emergency numbers not checked within the days', 'int', 'COUNTIFS(%s,">"&{in:days})+COUNTIFS(%s,"<>",%s,"")' % (ER('days_checked'), ER('who'), ER('last_checked'))),
    O('Adults with a phone', 'int', 'COUNTIFS(%s,%s,%s,1)+COUNTIFS(%s,%s,%s,1)' % (ER('who'), tok('role', 'Adult 1'), ER('phone_ok'), ER('who'), tok('role', 'Adult 2'), ER('phone_ok'))),
    O('School office with a phone', 'int', 'COUNTIFS(%s,%s,%s,1)' % (ER('who'), tok('role', 'School office'), ER('phone_ok'))), O('Neighbour with a phone', 'int', 'COUNTIFS(%s,%s,%s,1)' % (ER('who'), tok('role', 'Neighbour'), ER('phone_ok'))),
    O('Plumber, electrician and heating engineer with a phone', 'int', '+'.join('COUNTIFS(%s,%s,%s,1)' % (ER('who'), tok('role', r), ER('phone_ok')) for r in ('Plumber', 'Electrician', 'Heating engineer'))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (MISS13, lbl('Every contact has a phone'), V('Contacts missing a phone:', F(MISS13))))],
    GR('What if you check more often', ('90 days', {'days': 90}), ('180 days', {'days': 180}), ('270 days', {'days': 270}), ('365 days', {'days': 365}))))

# 14 --------------------------------------------------------------- contact lookup
POS14 = 'MATCH({in:role},%s,0)' % CR('trade')
def CL(c): return 'IFERROR(INDEX(%s,%s),"")' % (CR(c), POS14)
tools.append(TOOL('contact_lookup', 'Contact Lookup', 'Find the contact for a role: phone, last used, last job cost',
    'Pick a role such as the plumber: the name, the phone, when you last used them, the cost line of the last job and whether you would use them again, from the Contacts sheet.', [
    IL('role', 'Role', 'role', 'Plumber')], [
    O('Name', 'text', CL('name') + '&""'), O('Phone', 'text', CL('phone') + '&""'), O('E-mail', 'text', CL('email') + '&""'), O('Last used', 'date', CL('last_used')), O('Days since last used', 'int', CL('days_since')),
    O('Cost line, last time', 'money', CL('cost_last')), O('Would use again', 'text', 'IF(%s="","",IF(%s=%s,%s,%s))' % (CL('name'), CL('would_use_again'), YES, lbl('Yes'), lbl('No'))),
    O('Contacts of the same kind', 'int', 'IFERROR(COUNTIFS(%s,INDEX(%s,%s)),0)' % (CR('kind'), CR('kind'), POS14)),
    O('Verdict', 'text', 'IF(%s="",%s,%s)' % (CL('name'), lbl('No contact for this role'), V('Call', F(CL('name')), 'last used', F(CL('days_since')), 'days ago')))],
    GR('What if you need another role', ('Plumber', {'role': '=' + tok('role', 'Plumber')}), ('Electrician', {'role': '=' + tok('role', 'Electrician')}), ('Heating engineer', {'role': '=' + tok('role', 'Heating engineer')}),
       ('Car mechanic', {'role': '=' + tok('role', 'Car mechanic')}), ('Dog walker', {'role': '=' + tok('role', 'Dog walker')}))))

# 15 --------------------------------------------------------------- key and access check
OUT15 = 'SUM(%s)' % KR('out')
OLD15 = G(OUT15, 'MINIFS(%s,%s,1)' % (KR('since'), KR('out')))
tools.append(TOOL('key_check', 'Key And Access Check', 'Who holds a key and for how long',
    'The key list: keys out, keys returned, the oldest key out and the keys out longer than the days you type, by the neighbour, the dog walker, the sitter and the grandparent.', [
    I('days', 'A key is out too long after this many days', 60)], [
    O('Keys on the list', 'int', 'COUNTA(%s)' % KR('key_id')), O('Keys out', 'int', OUT15), O('Keys returned', 'int', 'COUNTIFS(%s,0)' % KR('out')), O('Oldest key out since', 'date', OLD15),
    O('Days out, the oldest', 'int', G(OUT15, '{today}-%s' % OLD15)), O('Keys out longer than the days', 'int', 'COUNTIFS(%s,">"&{in:days})' % KR('days_out')),
    O('Neighbour keys out', 'int', 'COUNTIFS(%s,%s,%s,1)' % (KR('holder'), tok('kholder', 'Neighbour'), KR('out'))), O('Dog walker keys out', 'int', 'COUNTIFS(%s,%s,%s,1)' % (KR('holder'), tok('kholder', 'Dog walker'), KR('out'))),
    O('Babysitter keys out', 'int', 'COUNTIFS(%s,%s,%s,1)' % (KR('holder'), tok('kholder', 'Babysitter'), KR('out'))), O('Grandparent keys out', 'int', 'COUNTIFS(%s,%s,%s,1)' % (KR('holder'), tok('kholder', 'Grandparent'), KR('out'))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (OUT15, lbl('No keys out'), V(F(OUT15), 'keys out, oldest out', F('{today}-%s' % OLD15), 'days')))],
    GR('What if too long means sooner', ('14 days', {'days': 14}), ('30 days', {'days': 30}), ('60 days', {'days': 60}), ('180 days', {'days': 180}), ('365 days', {'days': 365}))))

# 16 --------------------------------------------------------------- expiries by quarter
def Q16(q): return 'SUMIFS(%s,%s,%s)' % (RMR('docs'), RMR('qtr'), tok('qtr4', QTR[q]))
HIST16 = 'COUNTIFS(%s,">="&({today}-91*{in:back}),%s,"<"&{today})' % (DR('expiry'), DR('expiry'))
USU16 = 'ROUND(%s/{in:back},1)' % HIST16
tools.append(TOOL('quarter_tool', 'Expiries By Quarter', 'Is the next quarter busier than your usual quarter',
    'Document expiries of the next four quarters counted from the months ahead, against your own usual quarter from the quarters you type; a quarter here is three months ahead from this month.', [
    I('back', 'Quarters of your own history to average', 4)], [
    O('Next quarter', 'int', Q16(0)), O('Second quarter', 'int', Q16(1)), O('Third quarter', 'int', Q16(2)), O('Fourth quarter', 'int', Q16(3)),
    O('Expiries in the next 12 months', 'int', 'SUM(%s)' % RMR('docs')), O('Expiries in your history window', 'int', HIST16), O('Your usual quarter', 'num', USU16),
    O('Next quarter against the usual', 'num', 'ROUND(%s-%s,1)' % (Q16(0), USU16)), O('Busiest of the four', 'int', 'MAX(%s,%s,%s,%s)' % (Q16(0), Q16(1), Q16(2), Q16(3))),
    O('Verdict', 'text', V('Next quarter has', F(Q16(0)), 'expiries, usual', F(USU16)))],
    GR('What if you average more history', ('1 quarter', {'back': 1}), ('2 quarters', {'back': 2}), ('3 quarters', {'back': 3}), ('4 quarters', {'back': 4}), ('6 quarters', {'back': 6}))))

# 17 --------------------------------------------------------------- renewal checklist for one document
POS17 = 'MATCH({in:doc_id},%s,0)' % DR('doc_id')
EX17 = 'IFERROR(INDEX(%s,%s),"")' % (DR('expiry'), POS17)
def S17(f): return 'IF(%s="","",%s-ROUND({in:lead}*%s,0))' % (EX17, EX17, f)
STEPS17 = ['1', '0.75', '0.5', '0.25', '0']
PAST17 = '+'.join('(%s<{today})' % S17(f) for f in STEPS17)
K17 = 'MIN(5,%s+1)' % PAST17
tools.append(TOOL('checklist_one', 'Renewal Steps One Document', 'The dated steps of one renewal, counted back from the expiry',
    'Type a document ID and the days you need: five steps are dated back from the expiry (check what is needed, gather the papers, book, submit, collect) and the next step is shown.', [
    I('doc_id', 'Document ID', 'DC-11', 'text'), I('lead', 'Days you need before the expiry', 60)], [
    O('Document', 'text', 'IFERROR(INDEX(%s,%s),"")' % (DR('doc'), POS17)), O('Expires on', 'date', EX17), O('Step 1: check what is needed', 'date', S17('1')), O('Step 2: gather the papers', 'date', S17('0.75')),
    O('Step 3: book the appointment', 'date', S17('0.5')), O('Step 4: submit the application', 'date', S17('0.25')), O('Step 5: collect the new document', 'date', S17('0')),
    O('Steps already past', 'int', 'IF(%s="","",%s)' % (EX17, PAST17)), O('Next step number', 'int', 'IF(%s="","",%s)' % (EX17, K17)),
    O('Days to the next step', 'int', 'IF(%s="","",CHOOSE(%s,%s,%s,%s,%s,%s)-{today})' % (EX17, K17, S17('1'), S17('0.75'), S17('0.5'), S17('0.25'), S17('0'))),
    O('Verdict', 'text', 'IF(%s="","",IF(%s>=5,IF(%s<{today},%s,%s),%s))' % (EX17, PAST17, EX17, lbl('Past the expiry, replace it now'), V('Step 5 is due in', F('%s-{today}' % EX17), 'days'),
        V('Step', F(K17), 'is due in', F('CHOOSE(%s,%s,%s,%s,%s,%s)-{today}' % (K17, S17('1'), S17('0.75'), S17('0.5'), S17('0.25'), S17('0'))), 'days')))],
    GR('What if you need more or fewer days', ('30 days', {'lead': 30}), ('45 days', {'lead': 45}), ('60 days', {'lead': 60}), ('75 days', {'lead': 75}), ('90 days', {'lead': 90}))))

# 18 --------------------------------------------------------------- documents compared with own history
def WIN(a, b): return '%s,">="&({today}-%d),%s,"<"&({today}-%d)' % (DR('renewed_on'), a, DR('renewed_on'), b)
NOW18, PRE18 = 'COUNTIFS(%s)' % WIN(364, -1), 'COUNTIFS(%s)' % WIN(729, 364)
OT_N, OT_P = 'COUNTIFS(%s,%s,1)' % (WIN(364, -1), DR('on_time')), 'COUNTIFS(%s,%s,1)' % (WIN(729, 364), DR('on_time'))
ER_N, ER_P = 'COUNTIFS(%s,%s,1)' % (WIN(364, -1), DR('early')), 'COUNTIFS(%s,%s,1)' % (WIN(729, 364), DR('early'))
SN, SP = 'IFERROR(%s/%s,0)' % (OT_N, NOW18), 'IFERROR(%s/%s,0)' % (OT_P, PRE18)
tools.append(TOOL('history_tool', 'Documents Against History', 'Are documents renewed on time more often than last year',
    'Documents renewed in the last 12 months against the 12 months before: how many were renewed on or before the expiry and before the action date; a comparison with your own history, no score.', [
    I('margin', 'In line within this margin', 0.1, 'pct')], [
    O('Renewed in the last 12 months', 'int', NOW18), O('On time, last 12 months', 'int', OT_N), O('Share on time, last 12 months', 'pct', 'ROUND(%s,3)' % SN), O('Started before the action date, last 12 months', 'int', ER_N),
    O('Renewed in the 12 months before', 'int', PRE18), O('On time, the 12 months before', 'int', OT_P), O('Share on time, the 12 months before', 'pct', 'ROUND(%s,3)' % SP), O('Started before the action date, the 12 months before', 'int', ER_P),
    O('Change in the share on time', 'pct', 'ROUND(%s-%s,3)' % (SN, SP)),
    O('Verdict', 'text', 'IF(OR(%s=0,%s=0),%s,IF(%s>%s+{in:margin},%s,IF(%s<%s-{in:margin},%s,%s)))' % (NOW18, PRE18, lbl('No earlier year to compare'), SN, SP, lbl('Better than your own history'), SN, SP, lbl('Worse than your own history'), lbl('In line with your own history')))],
    GR('What if in line means wider', ('Margin 5%', {'margin': 0.05}), ('Margin 10%', {'margin': 0.1}), ('Margin 20%', {'margin': 0.2}), ('Margin 30%', {'margin': 0.3}))))
assert len(tools) == 18, len(tools)
