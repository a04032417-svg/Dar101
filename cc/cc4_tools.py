"""Childcare center suite part 4: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc4_lists import *
import cc4_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def R(t, c): return '{range:%s.%s}' % (t, c)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YES = '{list:yesno.yes}'
ENR = tok('cstatus', 'Enrolled'); LEFT = tok('cstatus', 'Left'); WK = tok('cycle', 'Weekly'); MO = tok('cycle', 'Monthly'); HELD = tok('depstatus', 'Held')
RT = {r: tok('room', r) for r in ROOMS}
def RATE(room, sched): return 'SUMIFS(%s,%s,%s,%s,%s)' % (R('rates', 'weekly_rate'), R('rates', 'room'), room, R('rates', 'schedule'), sched)
def RCOL(col, room, sched): return 'SUMIFS(%s,%s,%s,%s,%s)' % (R('rates', col), R('rates', 'room'), room, R('rates', 'schedule'), sched)
BASE3 = '(SUMIFS(%s,%s,">="&EDATE(%s,-3),%s,"<"&%s)/3)' % (R('rev_room', 'revenue'), R('rev_room', 'month'), MS, R('rev_room', 'month'), MS)
KIDS = 'COUNTIFS(%s,%s)' % (R('children', 'status'), ENR)
NEXT_MON = '({today}+MOD(8-WEEKDAY({today},2),7))'
tools = []
_enr = [c for c in D.CHF if c['status'] == 'Enrolled']
_sib = [c for c in _enr if c['discount'] == 'Sibling']
SIB_RATE = round(sum(D._wr(c) for c in _sib) / len(_sib))
AVG_WEEK = round(sum(D._wr(c) for c in _enr) / len(_enr))
_last = (TODAY.replace(day=1) - __import__('datetime').timedelta(days=1))
HELD_LAST = sum(x['amount'] for x in D.DPF if x['received_on'] <= iso(_last) and not (x['settled_on'] and x['settled_on'] <= iso(_last)))
import datetime as _dt
NEXT_MONDAY = iso(TODAY + _dt.timedelta(days=(7 - TODAY.weekday()) % 7 or 7))
STMT_FAMILY = [s for s in D.STF if s['year'] == TODAY.year][0]['family']
STMT_FAMILY_BAD = [s for s in D.STF if s['year'] == TODAY.year][6]['family']

# 1 ------------------------------------------------------------ rate card and invoice builder
W1 = RATE('{in:room}', '{in:sched}')
WKS1 = 'IF({in:cycle}=%s,52/12,1)' % MO
TU1 = 'ROUND(%s*%s,2)' % (W1, WKS1)
DS1 = 'IF({in:disc}=%s,{set:sibling_pct},IF({in:disc}=%s,{set:staff_pct},0))' % (tok('discount', 'Sibling'), tok('discount', 'Staff'))
DI1 = 'ROUND({in:dropin}*%s*(1+{set:drop_in_surcharge}),2)' % RCOL('day_rate', '{in:room}', '{in:sched}')
AM1 = '%s-ROUND(%s*%s,2)+{in:reg}*{set:reg_fee}+{in:supply}*{set:supply_fee}+%s+{in:late}' % (TU1, TU1, DS1, DI1)
LN1 = '(({in:reg}>0)+({in:supply}>0)+({in:dropin}>0)+({in:late}>0)+IF({in:last}>0,IF(ABS((%s)/{in:last}-1)>0.15,1,0),0))' % AM1
tools.append(TOOL('invoice_builder', 'Rate Card and Invoice Builder', 'Is this invoice ready to send',
    'Pick the room, schedule and cycle; weekly, monthly, daily and hourly rates and every invoice line appear against the last invoice, with the lines to check.', [
    IL('room', 'Room', 'room', 'Toddlers'), IL('sched', 'Schedule', 'schedule', '5 full days'), IL('cycle', 'Billing cycle', 'cycle', 'Monthly'), IL('disc', 'Discount', 'discount', 'None'),
    I('reg', 'Registration fee charged, 1 for yes', 0, 'int'), I('supply', 'Supply fee charged, 1 for yes', 0, 'int'), I('dropin', 'Drop-in days in the previous period', 1, 'int'), I('late', 'Late pickup fees in the previous period', 24),
    I('last', 'Amount of the last invoice of this family', 1640)], [
    O('Weekly rate', 'money', W1), O('Monthly rate, 52 weeks over 12', 'money', 'ROUND(%s*52/12,2)' % W1), O('Rate for one day', 'money', RCOL('day_rate', '{in:room}', '{in:sched}')), O('Rate per hour', 'money', RCOL('hour_rate', '{in:room}', '{in:sched}')),
    O('Weeks billed', 'num', WKS1), O('Tuition line', 'money', TU1), O('Discount line', 'money', '-ROUND(%s*%s,2)' % (TU1, DS1)), O('Registration line', 'money', '{in:reg}*{set:reg_fee}'),
    O('Supply fee line', 'money', '{in:supply}*{set:supply_fee}'), O('Drop-in line, with surcharge', 'money', DI1), O('Late pickup line', 'money', '{in:late}'), O('Invoice amount', 'money', AM1),
    O('Change against the last invoice', 'pct', 'IF({in:last}>0,(%s)/{in:last}-1,0)' % AM1), O('Lines to check', 'int', LN1),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (LN1, c2('Invoice ready'), c2('Lines to check')))],
    GR('What if', ('Infants, 5 full days', {'room': '=' + RT['Infants']}), ('Weekly cycle', {'cycle': '=' + WK, 'dropin': 0, 'late': 0}), ('Sibling discount', {'disc': '=' + tok('discount', 'Sibling')}),
       ('New starter with fees', {'reg': 1, 'supply': 1, 'dropin': 0, 'late': 0}), ('School-age, 3 half days', {'room': '=' + RT['School-age'], 'sched': '=' + tok('schedule', '3 half days'), 'last': 360}))))

# 2 ------------------------------------------------------------ invoice check
AD = R('inv_check', 'abs_diff')
def NTH(k, col): return 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),"")' % (R('inv_check', col), AD, k, AD)
DIF2 = 'COUNT(%s)-COUNTIFS(%s,"<="&{in:tol})' % (AD, AD)
tools.append(TOOL('invoice_check_tool', 'Invoice Check Tool', 'Which invoices differ from booked days times the rate',
    'Type the rounding tolerance; every invoice on the Invoice Check sheet is compared with booked days times the weekly rate, and the largest differences are named so you can open them first.', [
    I('tol', 'Rounding tolerance', 1.0)], [
    O('Invoices checked', 'int', 'COUNT(%s)' % AD), O('Invoices within the tolerance', 'int', 'COUNTIFS(%s,"<="&{in:tol})' % AD), O('Invoices that differ', 'int', DIF2),
    O('Share of invoices that match', 'pct', 'IFERROR(COUNTIFS(%s,"<="&{in:tol})/COUNT(%s),0)' % (AD, AD)), O('Tuition that differs, no sign', 'money', 'SUMIFS(%s,%s,">"&{in:tol})' % (AD, AD)),
    O('Largest difference', 'money', 'IFERROR(LARGE(%s,1),0)' % AD), O('Invoice with the largest difference', 'text', NTH(1, 'invoice_id')), O('Family of that invoice', 'text', NTH(1, 'family')),
    O('Second largest difference', 'money', 'IFERROR(LARGE(%s,2),0)' % AD), O('Invoice with the second largest difference', 'text', NTH(2, 'invoice_id')),
    O('Third largest difference', 'money', 'IFERROR(LARGE(%s,3),0)' % AD), O('Invoice with the third largest difference', 'text', NTH(3, 'invoice_id')),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (DIF2, c2('All match'), c2('Some differ')))],
    GR('What if', ('Tolerance 0.50', {'tol': 0.5}), ('Tolerance 5', {'tol': 5}), ('Tolerance 20', {'tol': 20}), ('Tolerance 100', {'tol': 100}), ('Tolerance 400', {'tol': 400}))))

# 3 ------------------------------------------------------------ sibling and multi-day discount tester
M3 = '({in:rate}*52/12)'
NA = '{in:fams}*%s*(1-{in:pct})' % M3; NB = '{in:fams}*(%s-{in:flat})' % M3; NC = '{in:fams}*%s*(1-{in:churn})' % M3
tools.append(TOOL('discount_tester', 'Sibling Discount Tester', 'Which sibling rule keeps the family at the lowest cost',
    'Type the weekly rate of a second child, how many families have one and the chance they leave without a discount; a percent, a flat amount and no discount are compared by the tuition you keep.', [
    I('rate', 'Weekly rate of a second child', SIB_RATE), I('fams', 'Families with a second child', 6, 'int'), I('pct', 'Percent off the second child', 0.10, 'pct'), I('flat', 'Flat amount off a month', 180),
    I('churn', 'Share of these families that leave with no discount', 0.35, 'pct')], [
    O('Tuition of one second child, a month', 'money', M3), O('Given away each month, percent rule', 'money', '{in:fams}*%s*{in:pct}' % M3), O('Given away each month, flat rule', 'money', '{in:fams}*{in:flat}'),
    O('Given away each year, percent rule', 'money', '12*{in:fams}*%s*{in:pct}' % M3), O('Given away each year, flat rule', 'money', '12*{in:fams}*{in:flat}'),
    O('Tuition kept each month, percent rule', 'money', NA), O('Tuition kept each month, flat rule', 'money', NB), O('Tuition kept each month, no discount', 'money', NC),
    O('Best rule keeps more than no discount by, a year', 'money', '12*(MAX(%s,%s)-%s)' % (NA, NB, NC)), O('Sibling discount cost today, a month', 'money', 'SUMIFS(%s,%s,%s)' % (R('discounted', 'monthly_cost'), R('discounted', 'discount'), tok('discount', 'Sibling'))),
    O('Verdict', 'text', 'IF(AND(%s>=%s,%s>=%s),%s,IF(%s>=%s,%s,%s))' % (NA, NB, NA, NC, c2('Percent rule is cheapest'), NB, NC, c2('Flat amount is cheapest'), c2('No discount is cheapest')))],
    GR('What if', ('Flat amount 100', {'flat': 100}), ('Percent 15', {'pct': 0.15}), ('Few leave without it', {'churn': 0.05}), ('Ten families', {'fams': 10}), ('Percent 5', {'pct': 0.05}))))

# 4 ------------------------------------------------------------ fee-rise planner
PC4 = 'IFERROR(%s/%s,0)' % (BASE3, KIDS)
NET4 = '((%s-{in:leavers}*%s)*(1+{in:rise}))' % (BASE3, PC4)
NEED4 = 'MAX(0,IFERROR({set:staff_pay_month}/({set:staff_share_target}*(%s-{in:leavers}*%s))-1,0))' % (BASE3, PC4)
tools.append(TOOL('rise_planner', 'Fee Rise Planner', 'Does this fee rise hold the staff cost share',
    'Type the rise, expected leavers and start date; revenue after leavers, the staff cost share and the rise needed to hold it come from your own last 3 months.', [
    I('rise', 'Proposed fee rise', 0.05, 'pct'), I('leavers', 'Children you expect to lose', 1, 'int'), I('start', 'Wanted start date of the rise', ahead(75), 'date'), I('notice', 'Notice days you give families', 30, 'int')], [
    O('Monthly revenue now, last 3 months', 'money', BASE3), O('Children enrolled', 'int', KIDS), O('Revenue per child, a month', 'money', PC4), O('Net revenue after the rise and leavers', 'money', NET4),
    O('Gain each month', 'money', '%s-%s' % (NET4, BASE3)), O('Gain each year', 'money', '12*(%s-%s)' % (NET4, BASE3)), O('Planned monthly staff pay', 'money', '{set:staff_pay_month}'),
    O('Staff cost share if rates stay', 'pct', 'IFERROR({set:staff_pay_month}/%s,0)' % BASE3), O('Staff cost share after the rise', 'pct', 'IFERROR({set:staff_pay_month}/%s,0)' % NET4), O('Share you want to hold', 'pct', '{set:staff_share_target}'),
    O('Rise needed to hold that share', 'pct', NEED4), O('Leavers that cancel the rise', 'num', 'IFERROR(%s*{in:rise}/((1+{in:rise})*%s),0)' % (BASE3, PC4)),
    O('Announce by', 'date', '{in:start}-{in:notice}'), O('Earliest start if announced today', 'date', '{today}+{in:notice}'),
    O('Verdict', 'text', 'IF(%s<=%s,%s,IF({in:start}-{in:notice}<{today},%s,%s))' % (NET4, BASE3, c2('Rise less'), c2('Rise at a later date'), c2('Rise now')))],
    GR('What if', ('Rise 3 percent', {'rise': 0.03}), ('Rise 7 percent', {'rise': 0.07}), ('Three leavers', {'leavers': 3}), ('Eight leavers', {'leavers': 8}), ('Start in 10 days', {'start': '={today}+10'}))))

# 5 ------------------------------------------------------------ late-pickup fee tool
WIN5 = '(%s>={today}-180)' % R('late_fees', 'date')
BL5 = 'SUMPRODUCT(%s*(%s>{in:grace})*ROUNDUP((%s-{in:grace})/{in:block},0))' % (WIN5, R('late_fees', 'late_minutes'), R('late_fees', 'late_minutes'))
MIN5 = 'SUMPRODUCT(%s*%s)' % (WIN5, R('late_fees', 'late_minutes'))
FEE5 = '({in:rate}*%s)' % BL5; COST5 = '(%s/60*{in:cost}*{in:staff})' % MIN5; NET5 = '(%s*(1-{in:waive})-%s)' % (FEE5, COST5)
RS = R('repeat_late', 'rank_score')
def RK(k, col): return 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),"")' % (R('repeat_late', col), RS, k, RS)
tools.append(TOOL('late_tool', 'Late Pickup Fee Tool', 'Does the late pickup fee cover the overtime it causes',
    'Type the grace, the fee for a block of minutes, the staff who stay and the share waived; fees are set against the overtime cost of 180 days.', [
    I('grace', 'Grace minutes', 5, 'int'), I('rate', 'Fee for each block of minutes', 2.0), I('block', 'Minutes in a block', 1, 'int'), I('staff', 'Staff members who stay late', 2, 'int'), I('cost', 'Cost of one staff member for one late hour', 23.65), I('waive', 'Share of late fees you waive', 0.33, 'pct')], [
    O('Late pickups, last 180 days', 'int', 'COUNTIFS(%s,">="&({today}-180))' % R('late_fees', 'date')), O('Late minutes, last 180 days', 'int', MIN5), O('Pickups past the grace', 'int', 'SUMPRODUCT(%s*(%s>{in:grace}))' % (WIN5, R('late_fees', 'late_minutes'))),
    O('Fee blocks charged under your rule', 'int', BL5), O('Fees under your rule, before waivers', 'money', FEE5), O('Fees after waivers', 'money', '%s*(1-{in:waive})' % FEE5), O('Overtime cost of the late minutes', 'money', COST5),
    O('Fees after waivers minus overtime cost', 'money', NET5), O('Fees for each unit of overtime cost', 'num', 'IFERROR(%s*(1-{in:waive})/%s,0)' % (FEE5, COST5)),
    O('Lowest fee for a block that covers the cost', 'money', 'IFERROR(%s/(%s*(1-{in:waive})),0)' % (COST5, BL5)), O('Highest share you can waive and still cover the cost', 'pct', 'IFERROR(MAX(0,1-%s/%s),0)' % (COST5, FEE5)),
    O('Repeat-late families', 'int', 'COUNTIFS(%s,%s)' % (R('repeat_late', 'status'), ca('Repeat late'))), O('Most late pickups, family', 'text', RK(1, 'family')), O('Most late pickups, events', 'int', RK(1, 'events')),
    O('Second, family', 'text', RK(2, 'family')), O('Third, family', 'text', RK(3, 'family')), O('Verdict', 'text', 'IF(%s>=0,%s,%s)' % (NET5, c2('Fee covers the cost'), c2('Fee below the cost')))],
    GR('What if', ('Grace 10 minutes', {'grace': 10}), ('Blocks of 10 minutes at 12', {'block': 10, 'rate': 12.0}), ('Waive two thirds', {'waive': 0.66}), ('Fee 0.50 a minute', {'rate': 0.5}), ('Four staff stay', {'staff': 4, 'rate': 0.5}))))

# 6 ------------------------------------------------------------ deposit and registration ledger
REC6 = 'SUMIFS(%s,%s,"<="&{in:asof})' % (R('deposits', 'amount'), R('deposits', 'received_on'))
def SET6(st): return 'SUMIFS(%s,%s,%s,%s,"<="&{in:asof})' % (R('deposits', 'amount'), R('deposits', 'status'), tok('depstatus', st), R('deposits', 'settled_on'))
HELD6 = '(%s-SUMIFS(%s,%s,"<="&{in:asof}))' % (REC6, R('deposits', 'amount'), R('deposits', 'settled_on'))
EXP6 = 'SUMIFS(%s,%s,%s)*{in:weeks}' % (R('children', 'weekly_rate'), R('children', 'status'), ENR)
tools.append(TOOL('deposit_ledger', 'Deposit and Registration Ledger', 'Does the deposit ledger match the account at month end',
    'Type the month-end date and the balance of the account that holds deposits; deposits received, applied, refunded and kept to that date give the amount still held, a liability and not income.', [
    I('asof', 'Ledger date, a month end', iso(_last), 'date'), I('account', 'Balance of the deposit account on that date', HELD_LAST), I('weeks', 'Weeks of tuition held as a deposit', 1, 'int')], [
    O('Deposits received to the date', 'money', REC6), O('Applied to a last invoice', 'money', SET6('Applied')), O('Refunded', 'money', SET6('Refunded')), O('Kept after short notice', 'money', SET6('Kept')),
    O('Held on the date, a liability', 'money', HELD6), O('Deposits held on the date', 'int', 'COUNTIFS(%s,"<="&{in:asof})-COUNTIFS(%s,"<="&{in:asof})' % (R('deposits', 'received_on'), R('deposits', 'settled_on'))),
    O('Held now', 'money', 'SUMIFS(%s,%s,%s)' % (R('deposits', 'amount'), R('deposits', 'status'), HELD)), O('Deposits held against enrolled children', 'money', EXP6),
    O('Held now minus the deposits expected', 'money', 'SUMIFS(%s,%s,%s)-%s' % (R('deposits', 'amount'), R('deposits', 'status'), HELD, EXP6)),
    O('To refund in the next 30 days', 'money', 'SUMIFS(%s,%s,">="&{today},%s,"<="&({today}+30))' % (R('deposits', 'amount'), R('deposits', 'refund_date'), R('deposits', 'refund_date'))),
    O('Ledger minus the account', 'money', '%s-{in:account}' % HELD6), O('Verdict', 'text', 'IF(ABS(%s-{in:account})<={set:tolerance},%s,%s)' % (HELD6, c2('Ledger matches'), c2('Ledger differs')))],
    GR('What if', ('Account 366 short', {'account': HELD_LAST - 366}), ('Ledger date two months ago', {'asof': '=EOMONTH({today},-3)', 'account': 0}), ('Two weeks of tuition held', {'weeks': 2}), ('Account 50 over', {'account': HELD_LAST + 50}))))

# 7 ------------------------------------------------------------ yearly payment statement
def ST7(col): return 'IFERROR(INDEX(%s,{in:no}),0)' % R('statements', col)
def ST7T(col): return 'IFERROR(INDEX(%s,{in:no})&"","")' % R('statements', col)
_ids = [x['statement_id'] for x in D.STF]
NO_THIS = [i + 1 for i, x in enumerate(D.STF) if x['year'] == TODAY.year and x['government_paid'] > 0][2]
NO_BAD = [i + 1 for i, x in enumerate(D.STF) if x['year'] == TODAY.year][6]
NO_LAST = [i + 1 for i, x in enumerate(D.STF) if x['year'] == TODAY.year - 1][0]
tools.append(TOOL('statement_tool', 'Yearly Payment Statement', 'Does the family statement match the ledger',
    'Type the row number of a statement on the Statements sheet; its parent and government payments are set against the ledger and the statements of that year that differ are counted.', [
    I('no', 'Row number on the Statements sheet', NO_THIS, 'int')], [
    O('Family', 'text', ST7T('family')), O('Year', 'text', ST7T('year')), O('Paid by the family', 'money', ST7('parent_paid')), O('Paid by a government childcare payment', 'money', ST7('government_paid')),
    O('Total paid for childcare', 'money', ST7('total_paid')), O('Payments in the year', 'int', ST7('payments')), O('Ledger total for the family', 'money', ST7('ledger_paid')), O('Difference to the ledger', 'money', ST7('difference')),
    O('Share paid by the government', 'pct', 'IFERROR(%s/%s,0)' % (ST7('government_paid'), ST7('total_paid'))), O('Sent check', 'text', ST7T('sent_flag')),
    O('Statements of that year', 'int', 'COUNTIFS(%s,INDEX(%s,{in:no}))' % (R('statements', 'year'), R('statements', 'year'))), O('Statements of that year that differ', 'int', 'COUNTIFS(%s,INDEX(%s,{in:no}),%s,%s)' % (R('statements', 'year'), R('statements', 'year'), R('statements', 'check'), ca('Statement differs'))),
    O('Verdict', 'text', 'IF(ABS(%s)<={set:tolerance},%s,%s)' % (ST7('difference'), c2('Statement matches ledger'), c2('Statement differs from ledger')))],
    GR('What if', ('A statement that differs', {'no': NO_BAD}), ('A statement of last year', {'no': NO_LAST}), ('The next statement', {'no': NO_THIS + 1}), ('Another that differs', {'no': [i + 1 for i, x in enumerate(D.STF) if x['year'] == TODAY.year][18]}))))

# 8 ------------------------------------------------------------ weekly versus monthly billing
def CY(cyc, col, extra=''): return 'AVERAGEIFS(%s,%s,%s%s)' % (R('invoices', col), R('invoices', 'cycle'), cyc, extra)
PD = R('invoices', 'paid_on')
LATE_W = 'IFERROR(COUNTIFS(%s,%s,%s,">0")/COUNTIFS(%s,%s,%s,">0"),0)' % (R('invoices', 'cycle'), WK, R('invoices', 'days_late'), R('invoices', 'cycle'), WK, PD)
LATE_M = 'IFERROR(COUNTIFS(%s,%s,%s,">0")/COUNTIFS(%s,%s,%s,">0"),0)' % (R('invoices', 'cycle'), MO, R('invoices', 'days_late'), R('invoices', 'cycle'), MO, PD)
HW = '(52*%s*{in:chase}/60)' % LATE_W; HM = '(12*%s*{in:chase}/60)' % LATE_M
SAVE8 = '({in:move}*(%s-%s))' % (HW, HM)
LAGW = 'IFERROR(%s,0)' % CY(WK, 'cash_lag'); LAGM = 'IFERROR(%s,0)' % CY(MO, 'cash_lag')
tools.append(TOOL('cycle_effect', 'Weekly or Monthly Billing', 'Should more families move to monthly billing',
    'Type the families you would move and the minutes a late invoice costs you; the share of late invoices, the days late, the days to cash and the chasing hours of each cycle come from your own invoices.', [
    I('move', 'Families you would move to monthly', 5, 'int'), I('chase', 'Minutes of chasing for one late invoice', 15, 'int'), I('hour', 'Cost of one hour of billing time', 23.65), I('extra', 'Extra days to cash you accept', 3, 'int')], [
    O('Weekly invoices this year', 'int', 'COUNTIFS(%s,%s)' % (R('invoices', 'cycle'), WK)), O('Monthly invoices this year', 'int', 'COUNTIFS(%s,%s)' % (R('invoices', 'cycle'), MO)),
    O('Weekly invoices paid late, share', 'pct', LATE_W), O('Monthly invoices paid late, share', 'pct', LATE_M), O('Weekly, average days late when late', 'num', 'IFERROR(AVERAGEIFS(%s,%s,%s,%s,">0"),0)' % (R('invoices', 'days_late'), R('invoices', 'cycle'), WK, R('invoices', 'days_late')), ),
    O('Monthly, average days late when late', 'num', 'IFERROR(AVERAGEIFS(%s,%s,%s,%s,">0"),0)' % (R('invoices', 'days_late'), R('invoices', 'cycle'), MO, R('invoices', 'days_late'))),
    O('Weekly, days from mid-period to payment', 'num', LAGW), O('Monthly, days from mid-period to payment', 'num', LAGM), O('Chasing hours a year for one weekly family', 'num', HW),
    O('Chasing hours a year for one monthly family', 'num', HM), O('Hours saved a year by moving these families', 'num', SAVE8), O('Value of the hours saved', 'money', '%s*{in:hour}' % SAVE8),
    O('Families on weekly billing now', 'int', 'COUNTIFS(%s,%s,%s,">0")' % (R('families', 'cycle'), WK, R('families', 'kids_now'))), O('Extra days to cash on monthly billing', 'num', '%s-%s' % (LAGM, LAGW)),
    O('Verdict', 'text', 'IF(AND(%s>0,%s-%s<={in:extra}),%s,%s)' % (SAVE8, LAGM, LAGW, c2('Offer monthly'), c2('Keep weekly')))],
    GR('What if', ('Ten families move', {'move': 10}), ('Accept no extra days', {'extra': 0}), ('Chasing takes 30 minutes', {'chase': 30}), ('One family moves', {'move': 1}), ('Chasing takes 5 minutes', {'chase': 5}))))

# 9 ------------------------------------------------------------ drop-in day price
DAY9 = RCOL('day_rate', '{in:room}', '{in:sched}'); PR9 = 'ROUND(%s*(1+{in:sur}),2)' % DAY9
CO9 = '({in:food}+{in:staff})'
tools.append(TOOL('dropin_price', 'Drop-in Day Price', 'Should this drop-in day be accepted and at what price',
    'Pick the room and the schedule whose day rate you start from and type the free places and the cost of the extra child; the price with the surcharge, the margin and a verdict follow.', [
    IL('room', 'Room', 'room', 'Toddlers'), IL('sched', 'Schedule the day rate comes from', 'schedule', '5 full days'), I('free', 'Free places that day', 1, 'int'), I('sur', 'Surcharge on the day rate', 0.15, 'pct'),
    I('food', 'Food and supplies for one day', 3.10), I('staff', 'Extra staff cost if another staff member is needed', 0), I('margin', 'Lowest margin share you accept', 0.30, 'pct')], [
    O('Day rate', 'money', DAY9), O('Surcharge', 'money', 'ROUND(%s*{in:sur},2)' % DAY9), O('Price to charge', 'money', PR9), O('What a five-day family pays for one day', 'money', 'ROUND(%s/5,2)' % RATE('{in:room}', tok('schedule', '5 full days'))),
    O('Cost of the extra child', 'money', CO9), O('Margin', 'money', '%s-%s' % (PR9, CO9)), O('Margin share of the price', 'pct', 'IFERROR((%s-%s)/%s,0)' % (PR9, CO9, PR9)),
    O('Lowest price that keeps your margin', 'money', 'IFERROR(%s/(1-{in:margin}),0)' % CO9), O('Verdict', 'text', 'IF(AND({in:free}>0,IFERROR((%s-%s)/%s,0)>={in:margin}),%s,%s)' % (PR9, CO9, PR9, c2('Accept the day'), c2('Decline the day')))],
    GR('What if', ('No free place', {'free': 0}), ('Another staff member needed', {'staff': 140}), ('Infants room', {'room': '=' + RT['Infants']}), ('No surcharge', {'sur': 0.0}), ('Half day rate', {'sched': '=' + tok('schedule', '5 half days')}))))

# 10 ----------------------------------------------------------- camp week fee against tuition
TU10 = 'ROUND(%s*(1-{in:disc}),2)' % RATE('{in:room}', '{in:sched}'); CF10 = '({in:price}*{in:days})'
tools.append(TOOL('camp_vs_tuition', 'Camp Fee Against Tuition', 'Should a camp week be billed as a camp fee or as tuition',
    'Pick the room and schedule and type the camp price and days; the camp fee that replaces a week of tuition is compared with the tuition.', [
    IL('room', 'Room', 'room', 'School-age'), IL('sched', 'Schedule', 'schedule', '5 half days'), I('price', 'Camp price for one day', 46), I('days', 'Days of camp in the week', 5, 'int'), I('kids', 'Children in the camp week', 6, 'int'),
    I('disc', 'Discount on tuition of these children', 0.0, 'pct'), I('weeks', 'Camp weeks in a year', 8, 'int')], [
    O('Tuition of the week, after discount', 'money', TU10), O('Camp fee of the week', 'money', CF10), O('Difference for one child', 'money', '%s-%s' % (CF10, TU10)), O('Difference for all children in the week', 'money', '{in:kids}*(%s-%s)' % (CF10, TU10)),
    O('Difference over the camp weeks of the year', 'money', '{in:weeks}*{in:kids}*(%s-%s)' % (CF10, TU10)), O('Camp price for one day that equals the tuition', 'money', 'IFERROR(%s/{in:days},0)' % TU10),
    O('Camp fee against tuition', 'pct', 'IFERROR(%s/%s-1,0)' % (CF10, TU10)), O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (CF10, TU10, c2('Bill camp fee'), c2('Bill tuition')))],
    GR('What if', ('5 full days', {'sched': '=' + tok('schedule', '5 full days')}), ('Camp price 38', {'price': 38}), ('Four-day week', {'days': 4}), ('3 half days', {'sched': '=' + tok('schedule', '3 half days')}), ('Sibling discount', {'disc': 0.10}))))

# 11 ----------------------------------------------------------- staff and sibling discount cost
GROSS11 = '(SUMIFS(%s,%s,%s)*52/12)' % (R('children', 'weekly_rate'), R('children', 'status'), ENR)
SIB11 = 'SUMIFS(%s,%s,%s)' % (R('discounted', 'monthly_cost'), R('discounted', 'discount'), tok('discount', 'Sibling'))
STF11 = 'SUMIFS(%s,%s,%s)' % (R('discounted', 'monthly_cost'), R('discounted', 'discount'), tok('discount', 'Staff'))
EXT11 = '({in:xsib}*{set:sibling_pct}+{in:xstaff}*{set:staff_pct})*{in:avg}*52/12'
tools.append(TOOL('discount_cost', 'Discount Cost', 'Are the sibling and staff discounts within your limit',
    'Type how many more sibling and staff children you may add; the monthly and yearly cost of each discount, the tuition you keep and the discount share are set against the limit you chose.', [
    I('xsib', 'More sibling discount children', 2, 'int'), I('xstaff', 'More staff discount children', 1, 'int'), I('avg', 'Weekly rate of a new child', AVG_WEEK)], [
    O('Sibling discount, a month', 'money', SIB11), O('Staff discount, a month', 'money', STF11), O('Both discounts, a year', 'money', '12*(%s+%s)' % (SIB11, STF11)), O('Tuition of enrolled children before discounts, a month', 'money', GROSS11),
    O('Tuition you keep, a month', 'money', '%s-%s-%s' % (GROSS11, SIB11, STF11)), O('Discount share of tuition now', 'pct', 'IFERROR((%s+%s)/%s,0)' % (SIB11, STF11, GROSS11)), O('Cost of the extra discounts, a month', 'money', EXT11),
    O('Discount share with the extra children', 'pct', 'IFERROR((%s+%s+%s)/(%s+({in:xsib}+{in:xstaff})*{in:avg}*52/12),0)' % (SIB11, STF11, EXT11, GROSS11)), O('Most discounts you give', 'pct', '{set:discount_limit}'),
    O('Verdict', 'text', 'IF(IFERROR((%s+%s+%s)/(%s+({in:xsib}+{in:xstaff})*{in:avg}*52/12),0)<={set:discount_limit},%s,%s)' % (SIB11, STF11, EXT11, GROSS11, c2('Keep the discounts'), c2('Limit the discounts')))],
    GR('What if', ('Six more sibling children', {'xsib': 6}), ('Five more staff children', {'xstaff': 5}), ('No more children', {'xsib': 0, 'xstaff': 0}), ('Infant rate', {'avg': 410}), ('Ten more of each', {'xsib': 10, 'xstaff': 10}))))

# 12 ----------------------------------------------------------- fee rise notice calculator
tools.append(TOOL('notice_calc', 'Fee Rise Notice Calculator', 'By which day must the notice of the rise go out',
    'Type the wanted start date of a rise and the notice days; the latest day to send the notice, the first weekly and monthly invoices the rise touches and the families affected are shown.', [
    I('start', 'Wanted start date of the rise', ahead(75), 'date'), I('notice', 'Notice days', 30, 'int')], [
    O('Send the notice by', 'date', '{in:start}-{in:notice}'), O('Days left to send it', 'int', '{in:start}-{in:notice}-{today}'), O('Earliest start if announced today', 'date', '{today}+{in:notice}'),
    O('First weekly invoice with the new rates', 'date', '{in:start}+MOD(8-WEEKDAY({in:start},2),7)'), O('First monthly invoice with the new rates', 'date', 'DATE(YEAR({in:start}),MONTH({in:start})+IF(DAY({in:start})=1,0,1),1)'),
    O('Weekly invoices issued before the rise', 'int', 'INT(({in:start}+MOD(8-WEEKDAY({in:start},2),7)-%s)/7)' % NEXT_MON), O('Families on weekly billing', 'int', 'COUNTIFS(%s,%s,%s,">0")' % (R('families', 'cycle'), WK, R('families', 'kids_now'))),
    O('Families on monthly billing', 'int', 'COUNTIFS(%s,%s,%s,">0")' % (R('families', 'cycle'), MO, R('families', 'kids_now'))), O('Weekly tuition of all families, before the rise', 'money', 'SUMIFS(%s,%s,%s)' % (R('children', 'net_weekly'), R('children', 'status'), ENR)),
    O('Weekly tuition added by the planned rise', 'money', 'SUMIFS(%s,%s,%s)*{set:planned_rise}' % (R('children', 'net_weekly'), R('children', 'status'), ENR)),
    O('Verdict', 'text', 'IF({in:start}-{in:notice}>={today},%s,%s)' % (c3('Send notice by'), c3('Notice period too short')))],
    GR('What if', ('Start in 20 days', {'start': '={today}+20'}), ('Start in 40 days', {'start': '={today}+40'}), ('Start on the 1st, in 100 days', {'start': '={today}+100'}), ('Notice 60 days', {'notice': 60}), ('Notice 14 days', {'notice': 14}))))

# 13 ----------------------------------------------------------- rate card against own history
def RISE(room): return 'IFERROR(SUMIFS(%s,%s,%s)/SUMIFS(%s,%s,%s)-1,0)' % (R('rates', 'weekly_rate'), R('rates', 'room'), room, R('rates', 'last_year_rate'), R('rates', 'room'), room)
RISES = [RISE(RT[r]) for r in ROOMS]
HI13 = 'MAX(%s)' % ','.join(RISES); LO13 = 'MIN(%s)' % ','.join(RISES)
HIR = 'IF(%s=%s,%s,IF(%s=%s,%s,IF(%s=%s,%s,IF(%s=%s,%s,%s))))' % (RISES[0], HI13, RT['Infants'], RISES[1], HI13, RT['Toddlers'], RISES[2], HI13, RT['Twos'], RISES[3], HI13, RT['Preschool'], RT['School-age'])
tools.append(TOOL('rate_history', 'Rate Card History', 'Is this year rise even across the rooms',
    'Pick a room and the spread you accept; the rise of every room against last year, the highest and lowest rise and the yearly revenue the rise brings on enrolled children are compared.', [
    IL('room', 'Room', 'room', 'Toddlers'), I('spread', 'Spread between rooms you accept', 0.01, 'pct')], [
    O('Rise of the chosen room', 'pct', RISE('{in:room}')), O('Rise, Infants', 'pct', RISES[0]), O('Rise, Toddlers', 'pct', RISES[1]), O('Rise, Twos', 'pct', RISES[2]), O('Rise, Preschool', 'pct', RISES[3]), O('Rise, School-age', 'pct', RISES[4]),
    O('Rise of the whole rate card', 'pct', 'SUM(%s)/SUM(%s)-1' % (R('rates', 'weekly_rate'), R('rates', 'last_year_rate'))), O('Highest rise', 'pct', HI13), O('Lowest rise', 'pct', LO13), O('Spread between rooms', 'pct', '%s-%s' % (HI13, LO13)),
    O('Room with the highest rise', 'text', HIR), O('Extra tuition a year from the rise, enrolled children', 'money', '(SUMIFS(%s,%s,%s)-SUMIFS(%s,%s,%s))*{set:weeks_open}' % (R('children', 'weekly_rate'), R('children', 'status'), ENR, R('children', 'last_year_rate'), R('children', 'status'), ENR)),
    O('Verdict', 'text', 'IF(%s-%s<={in:spread},%s,%s)' % (HI13, LO13, c3('Rise is even'), c3('Uneven by room')))],
    GR('What if', ('Infants', {'room': '=' + RT['Infants']}), ('Preschool', {'room': '=' + RT['Preschool']}), ('School-age', {'room': '=' + RT['School-age']}), ('Spread 0.1 points', {'spread': 0.001}), ('Spread 3 points', {'spread': 0.03}))))

# 14 ----------------------------------------------------------- registration and supply fee check
SD14 = 'DATE(YEAR({today}),9,1)'
SEP14 = '(COUNTIFS(%s,"<="&%s,%s,%s)+COUNTIFS(%s,"<="&%s,%s,">="&%s,%s,%s))' % (R('children', 'start_date'), SD14, R('children', 'status'), ENR, R('children', 'start_date'), SD14, R('children', 'end_date'), SD14, R('children', 'status'), LEFT)
ST14 = '%s,">="&EDATE({today},-{in:months})' % R('starters', 'start_date')
SUPD = '(%s*{set:supply_fee}-SUM(%s))' % (SEP14, R('invoices', 'supply_fee'))
MISS14 = 'COUNTIFS(%s,%s,%s)' % (ST14, R('starters', 'fee_flag'), ca('Registration missing'))
tools.append(TOOL('fee_check', 'Registration Supply Fee Check', 'Were the registration and supply fees charged',
    'Type how many months of new starters to check; their registration fees and the September supply fees of the children enrolled then are set against what the invoices charged.', [
    I('months', 'Months of new starters to check', 12, 'int')], [
    O('New starters in the period', 'int', 'COUNTIFS(%s)' % ST14), O('Registration fees expected', 'money', 'COUNTIFS(%s)*{set:reg_fee}' % ST14), O('Registration fees charged', 'money', 'SUMIFS(%s,%s)' % (R('starters', 'registration'), ST14)),
    O('Starters with no registration fee', 'int', MISS14), O('Children enrolled on 1 September', 'int', SEP14), O('Supply fees expected', 'money', '%s*{set:supply_fee}' % SEP14), O('Supply fees charged this year', 'money', 'SUM(%s)' % R('invoices', 'supply_fee')),
    O('Supply fees not charged', 'money', SUPD), O('Deposits recorded for these starters', 'money', 'SUMIFS(%s,%s)' % (R('starters', 'deposit'), ST14)),
    O('Verdict', 'text', 'IF(AND(%s=0,ABS(%s)<={set:tolerance}),%s,%s)' % (MISS14, SUPD, c3('Fees charged'), c3('Fees missing')))],
    GR('What if', ('Last 3 months', {'months': 3}), ('Last 6 months', {'months': 6}), ('Last 2 months', {'months': 2}), ('Last 24 months', {'months': 24}), ('Last month', {'months': 1}))))

# 15 ----------------------------------------------------------- mid-month start proration
PS15 = 'IF({in:cycle}=%s,DATE(YEAR({in:start}),MONTH({in:start}),1),{in:start}-WEEKDAY({in:start},2)+1)' % MO
PE15 = 'IF({in:cycle}=%s,EOMONTH({in:start},0),(%s)+4)' % (MO, PS15)
SH15 = 'IFERROR(NETWORKDAYS(MAX({in:start},%s),%s)/NETWORKDAYS(%s,%s),0)' % (PS15, PE15, PS15, PE15)
TU15 = 'ROUND(%s*IF({in:cycle}=%s,52/12,1)*%s*(1-{in:disc}),2)' % (RATE('{in:room}', '{in:sched}'), MO, SH15)
FI15 = '(%s+{in:reg}*{set:reg_fee}+{in:supply}*{set:supply_fee})' % TU15
tools.append(TOOL('proration', 'Mid-Month Start Proration', 'What is the first invoice for a child who starts mid-period',
    'Pick the room, schedule, billing cycle and the start date; the weekdays billed in the first period, the tuition, the registration and supply fees and the deposit add up to the first invoice.', [
    IL('room', 'Room', 'room', 'Twos'), IL('sched', 'Schedule', 'schedule', '5 full days'), IL('cycle', 'Billing cycle', 'cycle', 'Monthly'), I('start', 'Start date', iso(TODAY + _dt.timedelta(days=12 if (TODAY + _dt.timedelta(days=12)).weekday() < 5 else 14)), 'date'),
    I('reg', 'Registration fee charged, 1 for yes', 1, 'int'), I('supply', 'Supply fee charged, 1 for yes', 0, 'int'), I('disc', 'Discount share', 0.0, 'pct')], [
    O('Weekly rate', 'money', RATE('{in:room}', '{in:sched}')), O('First period starts', 'date', PS15), O('First period ends', 'date', PE15), O('Weekdays in the period', 'int', 'NETWORKDAYS(%s,%s)' % (PS15, PE15)),
    O('Weekdays billed from the start date', 'int', 'NETWORKDAYS(MAX({in:start},%s),%s)' % (PS15, PE15)), O('Share of the period billed', 'pct', SH15), O('Tuition of the first period', 'money', TU15),
    O('Registration fee', 'money', '{in:reg}*{set:reg_fee}'), O('Supply fee', 'money', '{in:supply}*{set:supply_fee}'), O('First invoice', 'money', FI15), O('Deposit, one week of tuition', 'money', RATE('{in:room}', '{in:sched}')),
    O('To collect before the first day', 'money', '%s+%s' % (FI15, RATE('{in:room}', '{in:sched}'))),
    O('Verdict', 'text', 'IF(OR(WEEKDAY({in:start},2)>5,{in:start}<{today}-30),%s,%s)' % (c3('Check the start date'), c3('First invoice ready')))],
    GR('What if', ('Weekly cycle', {'cycle': '=' + WK}), ('Infants, 3 full days', {'room': '=' + RT['Infants'], 'sched': '=' + tok('schedule', '3 full days')}), ('Start on a Saturday', {'start': '={today}+(13-WEEKDAY({today},2))'}),
       ('Sibling discount', {'disc': 0.10}), ('Starts on the 1st of next month', {'start': '=DATE(YEAR({today}),MONTH({today})+1,1)'}))))

# 16 ----------------------------------------------------------- closure day credit rule
CY16 = '%s,">="&DATE(YEAR({today}),1,1),%s,"<="&DATE(YEAR({today}),12,31)' % (R('closures', 'date'), R('closures', 'date'))
TR16 = 'COUNTIFS(%s,%s,%s)' % (CY16, R('closures', 'reason'), tok('creason', 'Staff training day'))
DT16 = 'IFERROR(AVERAGE(%s),0)' % R('closures', 'day_tuition')
CB16 = '((%s+{in:unplanned})*%s)' % (TR16, DT16); CD16 = '((%s+{in:unplanned})*%s*{in:makeup})' % (TR16, KIDS)
tools.append(TOOL('closure_rule', 'Closure Day Credit Rule', 'Which closure day rule costs least and stays fair',
    'Type the unplanned closure days you expect and the cost of a make-up day; crediting every closure, crediting only the days you choose, a make-up day and no credit are costed from your closure list.', [
    I('unplanned', 'Unplanned closure days expected this year', 2, 'int'), I('makeup', 'Cost of a make-up day for one child', 35)], [
    O('Closure days this year', 'int', 'COUNTIFS(%s)' % CY16), O('Staff training days this year', 'int', TR16), O('Tuition of one closure day', 'money', DT16),
    O('Cost a year: credit every closure day', 'money', '(COUNTIFS(%s)+{in:unplanned})*%s' % (CY16, DT16)), O('Cost a year: credit the days you choose', 'money', CB16),
    O('Cost a year: a make-up day for the days you choose', 'money', CD16), O('Cost a year: no credit', 'money', '0'), O('Share of a year of tuition, credit only the days you choose', 'pct', 'IFERROR(%s/(SUMIFS(%s,%s,%s)*{set:weeks_open}),0)' % (CB16, R('children', 'net_weekly'), R('children', 'status'), ENR)),
    O('Verdict', 'text', 'IF(%s+{in:unplanned}=0,%s,IF(%s<%s,%s,%s))' % (TR16, c3('No credit'), CD16, CB16, c3('Offer a make-up day'), c3('Credit centre-chosen days')))],
    GR('What if', ('Four unplanned days', {'unplanned': 4}), ('No unplanned days', {'unplanned': 0}), ('Make-up day costs 90', {'makeup': 90}), ('Make-up day costs 150', {'makeup': 150}), ('Make-up day free', {'makeup': 0}))))

# 17 ----------------------------------------------------------- hourly rate by schedule
HR = [(s, RCOL('hour_rate', '{in:room}', tok('schedule', s))) for s in SCHEDULES]
LO17 = 'MIN(%s)' % ','.join(h for _, h in HR); HI17 = 'MAX(%s)' % ','.join(h for _, h in HR)
LOS = 'IF(%s=%s,%s,IF(%s=%s,%s,IF(%s=%s,%s,IF(%s=%s,%s,%s))))' % (HR[0][1], LO17, tok('schedule', HR[0][0]), HR[1][1], LO17, tok('schedule', HR[1][0]), HR[2][1], LO17, tok('schedule', HR[2][0]), HR[3][1], LO17, tok('schedule', HR[3][0]), tok('schedule', HR[4][0]))
tools.append(TOOL('hourly_rank', 'Hourly Rate by Schedule', 'Which schedule pays least for each hour of care',
    'Pick a room and the lowest hourly rate you accept; the weekly rate divided by the hours of every schedule shows which schedule pays least and where it ranks on the whole rate card.', [
    IL('room', 'Room', 'room', 'School-age'), I('minimum', 'Lowest rate per hour you accept', 5.50)], [
    O('Rate per hour, 5 full days', 'money', HR[0][1]), O('Rate per hour, 3 full days', 'money', HR[1][1]), O('Rate per hour, 2 full days', 'money', HR[2][1]), O('Rate per hour, 5 half days', 'money', HR[3][1]), O('Rate per hour, 3 half days', 'money', HR[4][1]),
    O('Lowest rate per hour', 'money', LO17), O('Schedule that pays least', 'text', LOS), O('Highest rate per hour', 'money', HI17), O('Lowest against highest', 'pct', 'IFERROR(%s/%s-1,0)' % (LO17, HI17)),
    O('Rank on the whole rate card, 1 is lowest of 25', 'int', 'COUNTIFS(%s,"<"&%s)+1' % (R('rates', 'hour_rate'), LO17)), O('Hours of care in that schedule', 'num', 'SUMIFS(%s,%s,{in:room},%s,%s)*SUMIFS(%s,%s,{in:room},%s,%s)/1' % (R('rates', 'days'), R('rates', 'room'), R('rates', 'hour_rate'), LO17, R('rates', 'hours_day'), R('rates', 'room'), R('rates', 'hour_rate'), LO17)),
    O('Weekly rate needed to reach your lowest rate', 'money', 'ROUND({in:minimum}*SUMIFS(%s,%s,{in:room},%s,%s)*SUMIFS(%s,%s,{in:room},%s,%s),0)' % (R('rates', 'days'), R('rates', 'room'), R('rates', 'hour_rate'), LO17, R('rates', 'hours_day'), R('rates', 'room'), R('rates', 'hour_rate'), LO17)),
    O('Verdict', 'text', 'IF(%s<{in:minimum},%s,%s)' % (LO17, c3('Reprice the lowest schedule'), c3('Rates are in line')))],
    GR('What if', ('Preschool', {'room': '=' + RT['Preschool'], 'minimum': 7.0}), ('Infants', {'room': '=' + RT['Infants'], 'minimum': 10.0}), ('Toddlers', {'room': '=' + RT['Toddlers'], 'minimum': 8.0}), ('Twos', {'room': '=' + RT['Twos'], 'minimum': 7.5}), ('School-age, lowest 5', {'minimum': 5.0}))))

# 18 ----------------------------------------------------------- invoice run planner
WN = 'COUNTIFS(%s,">0")' % R('weekly_run', 'children'); MN = 'COUNTIFS(%s,">0")' % R('monthly_run', 'children')
WT = 'SUM(%s)' % R('weekly_run', 'amount'); MT = 'SUM(%s)' % R('monthly_run', 'amount')
PW = 'IF(WEEKDAY({in:plan},2)=1,1,0)'; PM = 'IF(DAY({in:plan})=1,1,0)'
tools.append(TOOL('run_planner', 'Invoice Run Planner', 'Which invoices go out on this date',
    'Type the date of the run; the weekly invoices (issued Monday) and monthly invoices (issued on the 1st) that fall on it are counted from the two run sheets with their amounts and due dates.', [
    I('plan', 'Date of the run', NEXT_MONDAY, 'date')], [
    O('Next weekly run', 'date', NEXT_MON), O('Weekly invoices in the run', 'int', WN), O('Weekly run amount', 'money', WT), O('Weekly run parent due', 'money', 'SUM(%s)' % R('weekly_run', 'parent_due')),
    O('Next monthly run', 'date', 'IF(DAY({today})=1,{today},DATE(YEAR({today}),MONTH({today})+1,1))'), O('Monthly invoices in the run', 'int', MN), O('Monthly run amount', 'money', MT), O('Monthly run parent due', 'money', 'SUM(%s)' % R('monthly_run', 'parent_due')),
    O('Invoices to issue on the chosen date', 'int', '%s*%s+%s*%s' % (PW, WN, PM, MN)), O('Amount to issue on the chosen date', 'money', '%s*%s+%s*%s' % (PW, WT, PM, MT)),
    O('Weekly invoices fall due on', 'date', '{in:plan}+{set:weekly_due_days}'), O('Monthly invoices fall due on', 'date', '{in:plan}+{set:invoice_days}'),
    O('Verdict', 'text', 'IF(%s+%s=2,%s,IF(%s=1,%s,IF(%s=1,%s,%s)))' % (PW, PM, c3('Issue both runs'), PW, c3('Issue the weekly run'), PM, c3('Issue the monthly run'), c3('No run on this date')))],
    GR('What if', ('The 1st of next month', {'plan': '=DATE(YEAR({today}),MONTH({today})+1,1)'}), ('A Tuesday', {'plan': '={today}+MOD(9-WEEKDAY({today},2),7)+1'}), ('The Monday after', {'plan': '=' + NEXT_MON + '+7'}))))
assert len(tools) == 18, len(tools)
