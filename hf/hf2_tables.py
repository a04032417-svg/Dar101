"""Household Finance suite part 2 (Bills, Subscriptions and Due Dates): settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf2_lists import *
import hf2_data as D


def LK(t, c, keycol, keyexpr, kind='t'):
    """lookup of t.c in the row of t whose keycol equals keyexpr: t text, n number, d optional date (blank when 0)"""
    r = '{range:%s.%s}' % (t, c); k = '{range:%s.%s}' % (t, keycol); m = 'MATCH(%s,%s,0)' % (keyexpr, k)
    if kind == 't': return 'IFERROR(INDEX(%s,%s)&"","")' % (r, m)
    if kind == 'n': return 'IFERROR(INDEX(%s,%s),"")' % (r, m)
    return 'IFERROR(IF(INDEX(%s,%s)=0,"",INDEX(%s,%s)),"")' % (r, m, r, m)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def DOM(y, m, d): return 'DATE(%s,%s,MIN(%s,DAY(EOMONTH(DATE(%s,%s,1),0))))' % (y, m, d, y, m)
def ROLEPH(role): return 'IFERROR(INDEX({range:team.phone},MATCH(%s,{range:team.role},0))&"","")' % tok('role', role)
def ROLENM(role): return 'IFERROR(INDEX({range:team.name},MATCH(%s,{range:team.role},0))&"","")' % tok('role', role)
def HOME(): return CA('home', 'Household', 'text', '{set:household}', 24)
def P1PH(): return CA('p1_phone', 'Partner 1 phone', 'text', ROLEPH('Partner 1'), 18)
def P2PH(): return CA('p2_phone', 'Partner 2 phone', 'text', ROLEPH('Partner 2'), 18)
def P1N(): return CA('p1_name', 'Partner 1 name', 'text', '{set:partner1}', 14)
def P2N(): return CA('p2_name', 'Partner 2 name', 'text', '{set:partner2}', 14)
def BANKPH(): return CA('bank_phone', 'Bank branch phone', 'text', ROLEPH('Bank branch'), 18)
def BANKNM(): return CA('bank_contact', 'Bank branch contact', 'text', ROLENM('Bank branch'), 22)

MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
PAID = tok('bstatus', 'Paid'); UNPAID = tok('bstatus', 'Unpaid'); LATE = tok('bstatus', 'Late')
MO = tok('cycle', 'Monthly'); YR = tok('cycle', 'Yearly')
KEEP = tok('decision', 'Keep'); REVIEW = tok('decision', 'Review'); CANCEL = tok('decision', 'Cancel')
INS = tok('bcat', 'Insurance'); UTIL = tok('bcat', 'Utilities'); KIND_INS = tok('ckind', 'Insurance')
PAYDAY = '{set:next_payday}'
PAYGAP = 'IF({set:pay_freq}=%s,7,IF({set:pay_freq}=%s,14,IF({set:pay_freq}=%s,15,30)))' % (tok('payfreq', 'Weekly'), tok('payfreq', 'Every two weeks'), tok('payfreq', 'Twice a month'))
PERIODS = 'IF({set:pay_freq}=%s,52,IF({set:pay_freq}=%s,26,IF({set:pay_freq}=%s,24,12)))' % (tok('payfreq', 'Weekly'), tok('payfreq', 'Every two weeks'), tok('payfreq', 'Twice a month'))
JB = 'SUMIFS({range:accounts.balance_now},{range:accounts.account_id},{set:joint_account_id})'
TIE2 = 'VALUE(RIGHT({col:%s},2))/100000'
TIE4 = 'VALUE(RIGHT({col:due_id},4))/100000'

settings = [
    S('household', 'Your household name', 'text', HOUSEHOLD), S('partner1', 'Name of partner 1', 'text', PARTNER1), S('partner2', 'Name of partner 2, leave as it is if you are a single adult', 'text', PARTNER2),
    S('pay_freq', 'How partner 1 is paid', 'list', key('payfreq', PAY_FREQ), list='payfreq'), S('next_payday', 'Next pay date of partner 1', 'date', iso(PAYDAY1_NEXT)),
    S('cash_floor', 'Cash floor of the joint account, your own number', 'money', CASH_FLOOR), S('joint_account_id', 'Id of the joint account whose balance you protect', 'text', 'AC-01'),
    S('calendar_days', 'Days ahead shown on the bills calendar', 'int', 14), S('renewal_days', 'Days ahead for the renewals page', 'int', 60),
    S('review_days', 'Review insurance and contracts this many days before renewal', 'int', REVIEW_DAYS), S('sub_unused_days', 'A subscription not used for this many days is flagged', 'int', SUB_UNUSED_DAYS),
    S('cancel_notice_days', 'Days before a renewal you must cancel', 'int', 3), S('price_rise_alert', 'A bill that rose by this share is flagged, your own number', 'pct', 0.05),
    S('sub_rise_alert', 'A subscription that rose by this share is flagged for review', 'pct', 0.15), S('creep_alert', 'Subscription cost growth on 6 months ago that you call creep', 'pct', 0.10),
    S('autopay_gap', 'Days before payday that make a bill risky', 'int', 3), S('on_time_target', 'Share of bills paid on time you want, your own number', 'pct', 0.95),
    S('autopay_target', 'Share of bills on autopay you want, your own number', 'pct', 0.70),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 team ---------------------------------------------------------------------
tables.append(T('team', 'Team', 'Household members and outside contacts',
    'One row per household member or outside contact with phone and e-mail; every message to a landlord, utility company, insurance agent, bank branch or school office uses these phones.', [
    C('member_id', 'Member ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 18), LST('group', 'Group', 'tgroup', 11), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
    C('note', 'Note', 'text', 28), C('start', 'Since', 'date', 11)], D.team_d(), 60))
# 2 accounts -----------------------------------------------------------------
tables.append(T('accounts', 'Accounts', 'Accounts the bills are paid from',
    'One row per account with its type, owner and balance; a card or loan balance is the amount you owe. The joint account balance feeds the unpaid-bills checks.', [
    C('account_id', 'Account ID', 'text', 10, required=True), C('account', 'Account', 'text', 28), LST('type', 'Type', 'atype', 12), LST('owner', 'Owner', 'person', 11),
    C('opening_balance', 'Opening balance', 'money', 14), C('balance_now', 'Balance now', 'money', 13)], D.accounts_d(), 40))
# 3 bills --------------------------------------------------------------------
tables.append(T('bills', 'Bills', 'Every bill with its due day, amount and autopay',
    'One row per bill (16 monthly, 4 yearly in the demo): due day, amount, autopay and contact. Next due date, cost per month and paycheck, price change and the day after payday fill in.', [
    C('bill_id', 'Bill ID', 'text', 9, required=True), C('bill', 'Bill', 'text', 24), LST('category', 'Category', 'bcat', 20), C('amount', 'Amount', 'money', 11), C('due_day', 'Due day', 'int', 8),
    LST('cycle', 'Cycle', 'cycle', 10), C('autopay', 'Autopay', 'bool', 9), REF('account_id', 'Account ID', 'accounts.account_id', 10), REF('contact_id', 'Contact ID', 'team.member_id', 10),
    C('payee', 'Payee', 'text', 22), C('due_month', 'Due month, yearly bills', 'int', 9), C('last_amount', 'Amount a year ago', 'money', 12), C('since', 'Bill since', 'date', 11),
    CA('contact', 'Contact', 'text', LK('team', 'name', 'member_id', '{col:contact_id}'), 22), CA('phone', 'Contact phone', 'text', LK('team', 'phone', 'member_id', '{col:contact_id}'), 18),
    CA('account', 'Account', 'text', LK('accounts', 'account', 'account_id', '{col:account_id}'), 22),
    CA('next_due', 'Next due date', 'date', 'IF({col:cycle}=%s,IF(%s>={today},%s,%s),IF(%s>={today},%s,%s))' % (
        MO, DOM('YEAR({today})', 'MONTH({today})', '{col:due_day}'), DOM('YEAR({today})', 'MONTH({today})', '{col:due_day}'), DOM('YEAR(EDATE({today},1))', 'MONTH(EDATE({today},1))', '{col:due_day}'),
        DOM('YEAR({today})', '{col:due_month}', '{col:due_day}'), DOM('YEAR({today})', '{col:due_month}', '{col:due_day}'), DOM('YEAR({today})+1', '{col:due_month}', '{col:due_day}')), 11),
    CA('days_away', 'Days to next due date', 'int', '{col:next_due}-{today}', 9), CA('monthly_cost', 'Cost per month', 'money', 'IF({col:cycle}=%s,{col:amount}/12,{col:amount})' % YR, 11),
    CA('yearly_cost', 'Cost per year', 'money', 'IF({col:cycle}=%s,{col:amount},{col:amount}*12)' % YR, 11), CA('per_paycheck', 'To set aside per paycheck', 'money', 'ROUND({col:monthly_cost}*12/%s,2)' % PERIODS, 12),
    CA('change', 'Change on a year ago', 'money', 'IF({col:last_amount}>0,{col:amount}-{col:last_amount},"")', 11), CA('change_share', 'Change share', 'pct', 'IF({col:last_amount}>0,{col:amount}/{col:last_amount}-1,"")', 9),
    CA('rise_score', 'Rise rank score', 'num', 'IFERROR({col:change_share}+%s,"")' % (TIE2 % 'bill_id'), 9), CA('days_before_pay', 'Days before a payday', 'int', 'MOD(%s-{col:next_due},%s)' % (PAYDAY, PAYGAP), 10),
    CA('new_day', 'Day after payday', 'int', 'DAY(%s+1)' % PAYDAY, 9), CA('yearly_next', 'Next yearly due date', 'date', 'IF({col:cycle}=%s,{col:next_due},"")' % YR, 11), BANKPH(), BANKNM(), HOME()],
    D.bills_d(), 60, [A('autopay', '= ' + YES, 'good'), A('change_share', '>= {set:price_rise_alert}', 'warn')]))
# 4 bills due ----------------------------------------------------------------
tables.append(T('bill_due', 'Bills Due', 'Every bill due date with status, 24 months back and 12 ahead',
    'One row per bill and due date: amount, status and paid date. Days to due, the paid on time or late flag and the sort keys of the calendar and late lists fill in by themselves.', [
    C('due_id', 'Due ID', 'text', 9, required=True), REF('bill_id', 'Bill ID', 'bills.bill_id', 9), REF('bill', 'Bill', 'bills.bill', 24), C('due_date', 'Due date', 'date', 11), C('month', 'Month', 'date', 11),
    C('amount', 'Amount', 'money', 11), LST('status', 'Status', 'bstatus', 10), C('paid_on', 'Paid on', 'date', 11), C('account_id', 'Account ID', 'text', 10), C('autopay', 'Autopay', 'bool', 9),
    LST('category', 'Category', 'bcat', 20), LST('account', 'Paid from', 'payacct', 18), LST('cycle', 'Cycle', 'cycle', 10), LST('dayband', 'Day of the month', 'dayband', 14),
    CA('days_to_due', 'Days to due', 'int', 'IF({col:status}<>%s,{col:due_date}-{today},"")' % PAID, 9), CA('days_paid_late', 'Days paid late', 'int', 'IF({col:paid_on}>0,MAX(0,{col:paid_on}-{col:due_date}),"")', 9),
    CA('flag', 'Payment flag', 'text', 'IF({col:status}=%s,IF(IF(ISNUMBER({col:days_paid_late}),{col:days_paid_late},0)>0,%s,%s),IF({col:due_date}<{today},%s,IF({col:due_date}-{today}<={set:calendar_days},%s,%s)))' % (
        PAID, V('Paid late'), V('Paid on time'), V('Late now'), V('Due soon'), V('Open')), 13),
    CA('cal_key', 'Calendar sort key', 'num', 'IF({col:due_date}>={today},{col:due_date}+%s,"")' % TIE4, 11),
    CA('open_key', 'Open bill sort key', 'num', 'IF({col:status}<>%s,{col:due_date}+%s,"")' % (PAID, TIE4), 11),
    CA('late_score', 'Late rank score', 'num', 'IFERROR(IF(AND({col:status}<>%s,{col:due_date}<{today}),1000+{today}-{col:due_date},IF(AND(IF(ISNUMBER({col:days_paid_late}),{col:days_paid_late},0)>=1,{col:due_date}>={today}-365),{col:days_paid_late},""))+%s,"")' % (PAID, TIE4), 11),
    CA('contact_id', 'Contact ID', 'text', LK('bills', 'contact_id', 'bill_id', '{col:bill_id}'), 10), CA('contact', 'Contact', 'text', LK('team', 'name', 'member_id', '{col:contact_id}'), 22),
    CA('phone', 'Contact phone', 'text', LK('team', 'phone', 'member_id', '{col:contact_id}'), 18), P2PH(), P2N(), HOME()],
    D.bill_due_d(), 800, [A('status', '= ' + LATE, 'bad'), A('status', '= ' + UNPAID, 'warn'), A('status', '= ' + PAID, 'good')]))
# 5 bills calendar -----------------------------------------------------------
def BD(c, kind='t'): return LK('bill_due', c, 'due_id', '{col:due_id}', kind)
tables.append(T('bills_cal', 'Bills Calendar', 'The next bills in date order with the paid flag',
    'The next 20 bill due dates from today in date order; the ones inside the days-ahead setting are flagged. The bill, amount, days away, autopay and account fill in by themselves.', [
    C('rank', 'No.', 'int', 6, required=True),
    CA('due_id', 'Due ID', 'text', 'IFERROR(INDEX({range:bill_due.due_id},MATCH(SMALL({range:bill_due.cal_key},{col:rank}),{range:bill_due.cal_key},0)),"")', 9),
    CA('bill', 'Bill', 'text', BD('bill'), 24), CA('due_date', 'Due date', 'date', BD('due_date', 'd'), 11), CA('amount', 'Amount', 'money', BD('amount', 'n'), 11),
    CA('days_away', 'Days away', 'int', 'IF({col:due_date}="","",{col:due_date}-{today})', 9), CA('flag', 'Payment flag', 'text', BD('flag'), 13),
    CA('autopay', 'Autopay', 'text', 'IF(%s=%s,%s,%s)' % (BD('autopay'), YES, V('Autopay'), V('Manual')), 10), CA('account', 'Paid from', 'text', BD('account'), 18),
    CA('window', 'In the window', 'text', 'IF({col:days_away}<={set:calendar_days},%s,%s)' % (V('Within the window'), V('Later')), 13),
    CA('day_n', 'Bills on that day', 'int', 'COUNTIFS({range:bill_due.due_date},{col:due_date},{range:bill_due.due_id},"<>")', 9),
    CA('window_n', 'Bills in the window', 'int', 'COUNTIFS({range:bill_due.due_date},">="&{today},{range:bill_due.due_date},"<="&({today}+{set:calendar_days}),{range:bill_due.due_id},"<>")', 9),
    CA('window_total', 'Total in the window', 'money', 'SUMIFS({range:bill_due.amount},{range:bill_due.due_date},">="&{today},{range:bill_due.due_date},"<="&({today}+{set:calendar_days}))', 11),
    CA('window_unpaid', 'Unpaid in the window', 'int', 'COUNTIFS({range:bill_due.due_date},">="&{today},{range:bill_due.due_date},"<="&({today}+{set:calendar_days}),{range:bill_due.status},"<>"&%s,{range:bill_due.due_id},"<>")' % PAID, 9),
    BANKPH(), BANKNM(), HOME()], D.rk(20), 30, [A('window', '= ' + V('Within the window'), 'warn')]))
# 6 unpaid before payday -------------------------------------------------------
tables.append(T('unpaid_pay', 'Unpaid Before Payday', 'Open bills in date order against the joint balance',
    'The next 12 open bills including any late one: running total of the bills due before payday and the joint balance after each, against your cash floor. Fills in by itself.', [
    C('rank', 'No.', 'int', 6, required=True),
    CA('due_id', 'Due ID', 'text', 'IFERROR(INDEX({range:bill_due.due_id},MATCH(SMALL({range:bill_due.open_key},{col:rank}),{range:bill_due.open_key},0)),"")', 9),
    CA('bill', 'Bill', 'text', BD('bill'), 24), CA('due_date', 'Due date', 'date', BD('due_date', 'd'), 11), CA('amount', 'Amount', 'money', BD('amount', 'n'), 11),
    CA('before', 'Before payday', 'int', 'IF({col:due_date}="","",IF({col:due_date}<%s,1,0))' % PAYDAY, 9),
    CA('running_total', 'Running total before payday', 'money', 'IF({col:before}=1,SUMIFS({range:unpaid_pay.amount},{range:unpaid_pay.rank},"<="&{col:rank},{range:unpaid_pay.before},1),"")', 13),
    CA('balance_after', 'Joint balance after', 'money', 'IF({col:before}=1,%s-{col:running_total},"")' % JB, 12),
    CA('under', 'Under the floor', 'int', 'IF({col:before}=1,IF({col:balance_after}<{set:cash_floor},1,0),"")', 9),
    CA('check', 'Check', 'text', 'IF({col:before}=1,IF({col:under}=1,%s,%s),%s)' % (V('Under the floor'), V('Above the floor'), V('After payday')), 15),
    CA('before_n', 'Bills before payday', 'int', 'COUNTIFS({range:unpaid_pay.before},1)', 9), CA('before_total', 'Total before payday', 'money', 'SUMIFS({range:unpaid_pay.amount},{range:unpaid_pay.before},1)', 12),
    CA('joint_now', 'Joint balance now', 'money', JB, 12), P2PH(), P2N(), HOME()], D.rk(12), 20, [A('check', '= ' + V('Under the floor'), 'bad'), A('check', '= ' + V('Above the floor'), 'good')]))
# 7 late and missed -----------------------------------------------------------
tables.append(T('late_list', 'Late and Missed', 'Late bills and the longest late payments, last 12 months',
    'The 12 worst late payments ranked by days late: a bill still open comes first. Days late, contact and the next step fill in by themselves.', [
    C('rank', 'No.', 'int', 6, required=True),
    CA('due_id', 'Due ID', 'text', 'IFERROR(INDEX({range:bill_due.due_id},MATCH(LARGE({range:bill_due.late_score},{col:rank}),{range:bill_due.late_score},0)),"")', 9),
    CA('bill', 'Bill', 'text', BD('bill'), 24), CA('due_date', 'Due date', 'date', BD('due_date', 'd'), 11),
    CA('days_late', 'Days late', 'int', 'IFERROR(IF(%s<>%s,{today}-{col:due_date},%s-{col:due_date}),"")' % (BD('status'), PAID, BD('paid_on', 'n')), 9), CA('amount', 'Amount', 'money', BD('amount', 'n'), 11),
    CA('flag', 'Payment flag', 'text', BD('flag'), 13), CA('contact', 'Contact', 'text', BD('contact'), 22), CA('phone', 'Contact phone', 'text', BD('phone'), 18),
    CA('next_step', 'Next step', 'text', 'IF(%s<>%s,IF({col:amount}<=%s,%s,%s),IF(%s=%s,%s,%s))' % (BD('status'), PAID, JB, V('Pay today'), V('Call to agree a date'), BD('autopay'), YES, V('Check the balance on due day'), V('Switch to autopay')), 24),
    P2PH(), P2N(), HOME()], D.rk(12), 20, [A('flag', '= ' + V('Late now'), 'bad')]))
# 8 bills by month -------------------------------------------------------------
def BDM(extra=''): return '{range:bill_due.month},{col:month}' + extra
tables.append(T('bills_month', 'Bills by Month', 'Bills due, paid on time, paid late and total by month',
    'One row per month: bills due, paid on time, paid late and the total amount fill in from the Bills Due sheet; utilities against the same month last year show the seasons.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('bills_due', 'Bills due', 'int', 'COUNTIFS(%s)' % BDM(), 9), CA('paid_on_time', 'Paid on time', 'int', 'COUNTIFS(%s,{range:bill_due.flag},%s)' % (BDM(), V('Paid on time')), 9),
    CA('paid_late', 'Paid late', 'int', 'COUNTIFS(%s,{range:bill_due.flag},%s)' % (BDM(), V('Paid late')), 9), CA('open_n', 'Still open', 'int', 'COUNTIFS(%s,{range:bill_due.status},"<>"&%s,{range:bill_due.due_id},"<>")' % (BDM(), PAID), 9),
    CA('total_amount', 'Total amount', 'money', 'SUMIFS({range:bill_due.amount},%s)' % BDM(), 12),
    CA('on_time_share', 'Paid on time share', 'pct', 'IF({col:paid_on_time}+{col:paid_late}>0,{col:paid_on_time}/({col:paid_on_time}+{col:paid_late}),"")', 10),
    CA('utilities', 'Utilities', 'money', 'SUMIFS({range:bill_due.amount},%s,{range:bill_due.category},%s)' % (BDM(), UTIL), 11),
    CA('utilities_ly', 'Utilities, same month last year', 'money', 'SUMIFS({range:bill_due.amount},{range:bill_due.month},EDATE({col:month},-12),{range:bill_due.category},%s)' % UTIL, 12),
    CA('year_total', 'Bills due, last 12 months', 'money', 'SUMIFS({range:bill_due.amount},{range:bill_due.month},">="&EDATE(%s,-12),{range:bill_due.month},"<"&%s)' % (MS, MS), 13),
    CA('year_bills', 'Bills, last 12 months', 'int', 'COUNTIFS({range:bill_due.month},">="&EDATE(%s,-12),{range:bill_due.month},"<"&%s)' % (MS, MS), 10),
    CA('year_late', 'Paid late, last 12 months', 'int', 'COUNTIFS({range:bill_due.month},">="&EDATE(%s,-12),{range:bill_due.month},"<"&%s,{range:bill_due.flag},%s)' % (MS, MS, V('Paid late')), 10),
    P2PH(), P2N(), HOME()], D.bills_month_d(), 40, [A('on_time_share', '< 0.9', 'warn')]))
# 9 bills by category ----------------------------------------------------------
tables.append(T('bills_cat', 'Bills by Category', 'Monthly average and share of bills by category',
    'One row per bill category: the monthly average of the last 12 complete months and the share of all bills fill in from the Bills Due sheet.', [
    LST('category', 'Category', 'bcat', 22, required=True),
    CA('monthly_avg', 'Monthly average, 12 months', 'money', 'SUMIFS({range:bill_due.amount},{range:bill_due.category},{col:category},{range:bill_due.month},">="&EDATE(%s,-12),{range:bill_due.month},"<"&%s)/12' % (MS, MS), 13),
    CA('share', 'Share of bills', 'pct', 'IF(SUM({range:bills_cat.monthly_avg})>0,{col:monthly_avg}/SUM({range:bills_cat.monthly_avg}),0)', 10)], D.bills_cat_d(), 20))
# 10 autopay map ---------------------------------------------------------------
def BL(c, kind='t'): return LK('bills', c, 'bill', '{col:bill}', kind)
tables.append(T('autopay_map', 'Autopay Map', 'Autopay against manual for every bill',
    'One row per bill: autopay or manual, account, due day and how many days before a payday it falls; a check flags autopay or manual bills that land just before payday.', [
    REF('bill', 'Bill', 'bills.bill', 24, required=True),
    CA('autopay', 'Autopay', 'text', 'IF(%s=%s,%s,%s)' % (BL('autopay'), YES, V('Autopay'), V('Manual')), 10), CA('account', 'Account', 'text', BL('account'), 22), CA('due_day', 'Due day', 'int', BL('due_day', 'n'), 8),
    CA('next_due', 'Next due date', 'date', BL('next_due', 'd'), 11), CA('days_before_pay', 'Days before a payday', 'int', BL('days_before_pay', 'n'), 10),
    CA('check', 'Check', 'text', 'IF(%s=%s,IF(AND({col:days_before_pay}>=1,{col:days_before_pay}<={set:autopay_gap}),%s,%s),IF(AND({col:days_before_pay}>=1,{col:days_before_pay}<={set:autopay_gap}),%s,%s))' % (
        BL('autopay'), YES, V('Autopay lands before payday'), V('Autopay is fine'), V('Manual, due just before payday'), V('Manual, timing is fine')), 26)],
    D.autopay_d(), 40, [A('check', '= ' + V('Manual, due just before payday'), 'bad'), A('check', '= ' + V('Autopay lands before payday'), 'warn')]))
# 11 price changes -------------------------------------------------------------
def BLR(c, kind='t'): return LK('bills', c, 'bill', '{col:bill}', kind)
tables.append(T('price_changes', 'Price Changes', 'Bills ranked by how much they rose against a year ago',
    'The 12 bills with the largest rise on a year ago: amount then, amount now, change and share; a flag shows the ones above your price-rise alert. Fills in by itself.', [
    C('rank', 'No.', 'int', 6, required=True),
    CA('bill', 'Bill', 'text', 'IFERROR(INDEX({range:bills.bill},MATCH(LARGE({range:bills.rise_score},{col:rank}),{range:bills.rise_score},0)),"")', 24),
    CA('last_amount', 'Amount a year ago', 'money', BLR('last_amount', 'n'), 12), CA('amount', 'Amount now', 'money', BLR('amount', 'n'), 11),
    CA('change', 'Change', 'money', '{col:amount}-{col:last_amount}', 10), CA('change_share', 'Change share', 'pct', 'IF({col:last_amount}>0,{col:amount}/{col:last_amount}-1,"")', 9),
    CA('flag', 'Flag', 'text', 'IF({col:change_share}>={set:price_rise_alert},%s,IF({col:change_share}>0,%s,%s))' % (V('Ask for a better price'), V('Small rise'), V('No rise')), 22),
    CA('contact', 'Contact', 'text', BLR('contact'), 22), CA('phone', 'Contact phone', 'text', BLR('phone'), 18), HOME()],
    D.rk(12), 20, [A('flag', '= ' + V('Ask for a better price'), 'warn')]))
# 12 subscriptions -------------------------------------------------------------
tables.append(T('subs', 'Subscriptions', 'Every subscription with price, renewal and last use',
    'One row per subscription: price, renewal date, last used, price 6 months ago and your decision. Days since use, price creep, a suggested decision and the ranking keys fill in by themselves.', [
    C('sub_id', 'Sub ID', 'text', 9, required=True), C('name', 'Subscription', 'text', 24), C('price', 'Price', 'money', 10), LST('cycle', 'Cycle', 'cycle', 10), C('monthly_cost', 'Cost per month', 'money', 11),
    C('yearly_cost', 'Cost per year', 'money', 11), LST('card', 'Paid with', 'card', 11), C('renewal_date', 'Renewal date', 'date', 11), C('last_used', 'Last used', 'date', 11),
    C('price_6m_ago', 'Price 6 months ago', 'money', 12), LST('decision', 'Decision', 'decision', 10), LST('owner', 'Owner', 'person', 11), C('start_date', 'Started on', 'date', 11),
    LST('use_band', 'Days since last use', 'useband', 24), C('provider_phone', 'Provider phone', 'text', 18),
    CA('account_id', 'Account ID', 'text', LK('accounts', 'account_id', 'account', '{col:card}'), 10), CA('days_since_use', 'Days since use', 'int', '{today}-{col:last_used}', 9),
    CA('then_monthly', 'Cost per month 6 months ago', 'money', 'IF({col:cycle}=%s,{col:price_6m_ago}/12,{col:price_6m_ago})' % YR, 12),
    CA('change_6m', 'Change per month', 'money', '{col:monthly_cost}-{col:then_monthly}', 10), CA('creep_share', 'Price change share', 'pct', 'IF({col:then_monthly}>0,{col:monthly_cost}/{col:then_monthly}-1,"")', 9),
    CA('suggested', 'Suggested decision', 'text', 'IF({col:days_since_use}>={set:sub_unused_days},%s,IF(OR({col:days_since_use}>=ROUND({set:sub_unused_days}/2,0),IF(ISNUMBER({col:creep_share}),{col:creep_share},0)>={set:sub_rise_alert}),%s,%s))' % (CANCEL, REVIEW, KEEP), 12),
    CA('rank_score', 'Cost rank score', 'num', '{col:yearly_cost}+%s' % (TIE2 % 'sub_id'), 10), CA('use_score', 'Use rank score', 'num', '{col:days_since_use}+%s' % (TIE2 % 'sub_id'), 10),
    CA('renew_key', 'Renewal sort key', 'num', 'IF({col:renewal_date}>={today},{col:renewal_date}+%s,"")' % (TIE2 % 'sub_id'), 10),
    CA('owner_phone', 'Owner phone', 'text', 'IF({col:owner}=%s,%s,%s)' % (tok('person', 'Partner 2'), ROLEPH('Partner 2'), ROLEPH('Partner 1')), 18),
    CA('now_total', 'All subscriptions per month', 'money', 'SUM({range:subs.monthly_cost})', 12), CA('then_total', 'All per month 6 months ago', 'money', 'SUM({range:subs.then_monthly})', 12),
    CA('cancel_n', 'Marked cancel', 'int', 'COUNTIFS({range:subs.decision},%s,{range:subs.sub_id},"<>")' % CANCEL, 9),
    CA('cancel_yearly', 'Saved a year if cancelled', 'money', 'SUMIFS({range:subs.yearly_cost},{range:subs.decision},%s)' % CANCEL, 12),
    P1PH(), P1N(), BANKPH(), BANKNM(), HOME()], D.subs_d(), 50, [A('decision', '= ' + CANCEL, 'bad'), A('decision', '= ' + REVIEW, 'warn'), A('days_since_use', '>= {set:sub_unused_days}', 'bad')]))
# 13 subscription ranking --------------------------------------------------------
def SB(c, kind='t'): return LK('subs', c, 'sub_id', '{col:sub_id}', kind)
tables.append(T('subs_rank', 'Subscription Ranking', 'Subscriptions ranked by yearly cost',
    'Every subscription from the dearest per year to the cheapest, with days since use, your decision, the suggested decision and the saving if it were cancelled. Fills in by itself.', [
    C('rank', 'No.', 'int', 6, required=True),
    CA('sub_id', 'Sub ID', 'text', 'IFERROR(INDEX({range:subs.sub_id},MATCH(LARGE({range:subs.rank_score},{col:rank}),{range:subs.rank_score},0)),"")', 9),
    CA('name', 'Subscription', 'text', SB('name'), 24), CA('yearly_cost', 'Cost per year', 'money', SB('yearly_cost', 'n'), 11), CA('days_since_use', 'Days since use', 'int', SB('days_since_use', 'n'), 9),
    CA('decision', 'Decision', 'text', SB('decision'), 10), CA('suggested', 'Suggested decision', 'text', SB('suggested'), 12), CA('saved_if_cancelled', 'Saved a year if cancelled', 'money', '{col:yearly_cost}', 12),
    CA('running_yearly', 'Running cost per year', 'money', 'SUMIFS({range:subs_rank.yearly_cost},{range:subs_rank.rank},"<="&{col:rank})', 12),
    CA('share', 'Share of yearly cost', 'pct', 'IF(SUM({range:subs_rank.yearly_cost})>0,{col:yearly_cost}/SUM({range:subs_rank.yearly_cost}),"")', 9),
    CA('all_yearly', 'All subscriptions per year', 'money', 'SUM({range:subs.yearly_cost})', 12),
    CA('review_n', 'To review or cancel', 'int', 'COUNTIFS({range:subs.suggested},"<>"&%s,{range:subs.sub_id},"<>")' % KEEP, 9),
    CA('review_yearly', 'Yearly cost to review', 'money', 'SUMIFS({range:subs.yearly_cost},{range:subs.suggested},"<>"&%s)' % KEEP, 12), HOME()], D.rk(14), 30,
    [A('suggested', '= ' + CANCEL, 'bad'), A('suggested', '= ' + REVIEW, 'warn')]))
# 14 subscription creep --------------------------------------------------------------
def SC(extra): return 'SUMIFS({range:sub_charges.amount},{range:sub_charges.month},%s)' % extra
tables.append(T('sub_creep', 'Subscription Creep', 'Subscription charges against 6 months earlier',
    'One row per month: charges paid, the same month 6 months earlier, the change and the change against the average of the 3 months before. Fills in from the Subscription Charges sheet.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('charges', 'Charges', 'money', SC('{col:month}'), 11), CA('six_ago', 'Charges 6 months earlier', 'money', SC('EDATE({col:month},-6)'), 12),
    CA('change', 'Change on 6 months earlier', 'money', '{col:charges}-{col:six_ago}', 12), CA('change_share', 'Change share', 'pct', 'IF({col:six_ago}>0,{col:charges}/{col:six_ago}-1,"")', 9),
    CA('avg3', 'Average of the 3 months before', 'money', '(SUMIFS({range:sub_charges.amount},{range:sub_charges.month},">="&EDATE({col:month},-3),{range:sub_charges.month},"<"&{col:month}))/3', 12),
    CA('vs_avg3', 'Change on that average', 'pct', 'IF({col:avg3}>0,{col:charges}/{col:avg3}-1,"")', 9),
    CA('cost_now', 'All subscriptions per month now', 'money', 'SUM({range:subs.monthly_cost})', 12), CA('cost_then', 'All per month 6 months ago', 'money', 'SUM({range:subs.then_monthly})', 12),
    CA('creep_now', 'Creep against 6 months ago', 'pct', 'IF({col:cost_then}>0,{col:cost_now}/{col:cost_then}-1,"")', 10), HOME()], D.sub_creep_d(), 30, [A('change_share', '>= {set:creep_alert}', 'warn')]))
# 15 renewals ----------------------------------------------------------------------
tables.append(T('renewals', 'Renewals Next 60 Days', 'Subscriptions in the order they renew',
    'The next 12 subscription renewals with price, days away, your decision and the date to decide by (renewal date less the cancel notice days). Fills in by itself.', [
    C('rank', 'No.', 'int', 6, required=True),
    CA('sub_id', 'Sub ID', 'text', 'IFERROR(INDEX({range:subs.sub_id},MATCH(SMALL({range:subs.renew_key},{col:rank}),{range:subs.renew_key},0)),"")', 9),
    CA('name', 'Subscription', 'text', SB('name'), 24), CA('renewal_date', 'Renewal date', 'date', SB('renewal_date', 'd'), 11), CA('days_away', 'Days away', 'int', 'IF({col:renewal_date}="","",{col:renewal_date}-{today})', 9),
    CA('price', 'Price', 'money', SB('price', 'n'), 10), CA('decision', 'Decision', 'text', SB('decision'), 10), CA('decide_by', 'Decide by', 'date', 'IF({col:renewal_date}="","",{col:renewal_date}-{set:cancel_notice_days})', 11),
    CA('window', 'In the window', 'text', 'IF({col:days_away}<={set:renewal_days},%s,%s)' % (V('Renews soon'), V('Later')), 13),
    CA('renew_n', 'Renewals in the window', 'int', 'COUNTIFS({range:subs.renewal_date},">="&{today},{range:subs.renewal_date},"<="&({today}+{set:renewal_days}))', 9),
    CA('renew_total', 'Amount renewing', 'money', 'SUMIFS({range:subs.price},{range:subs.renewal_date},">="&{today},{range:subs.renewal_date},"<="&({today}+{set:renewal_days}))', 12), P2PH(), P2N(), HOME()],
    D.rk(12), 20, [A('window', '= ' + V('Renews soon'), 'warn')]))
# 16 unused subscriptions ----------------------------------------------------------------
tables.append(T('unused_subs', 'Unused Subscriptions', 'Subscriptions ranked by days since they were last used',
    'The 12 subscriptions you have not used for the longest time with their yearly cost and a suggested decision from your unused-days setting. Fills in by itself.', [
    C('rank', 'No.', 'int', 6, required=True),
    CA('sub_id', 'Sub ID', 'text', 'IFERROR(INDEX({range:subs.sub_id},MATCH(LARGE({range:subs.use_score},{col:rank}),{range:subs.use_score},0)),"")', 9),
    CA('name', 'Subscription', 'text', SB('name'), 24), CA('days_since_use', 'Days since use', 'int', SB('days_since_use', 'n'), 9), CA('yearly_cost', 'Cost per year', 'money', SB('yearly_cost', 'n'), 11),
    CA('suggested', 'Suggested decision', 'text', SB('suggested'), 12), CA('owner', 'Owner', 'text', SB('owner'), 11),
    CA('unused_n', 'Unused subscriptions', 'int', 'COUNTIFS({range:subs.days_since_use},">="&{set:sub_unused_days})', 9),
    CA('unused_yearly', 'Yearly cost of unused', 'money', 'SUMIFS({range:subs.yearly_cost},{range:subs.days_since_use},">="&{set:sub_unused_days})', 12), P1PH(), P2PH(), P1N(), P2N(), HOME()],
    D.rk(12), 20, [A('suggested', '= ' + CANCEL, 'bad'), A('suggested', '= ' + REVIEW, 'warn')]))
# 17 subscription charges --------------------------------------------------------------
tables.append(T('sub_charges', 'Subscription Charges', 'Subscription charges paid, about two years',
    'One row per subscription charge on a card: date, payee and amount; the account name fills in. The creep sheet and charts read these rows.', [
    C('tx_id', 'Transaction ID', 'text', 11, required=True), C('date', 'Date', 'date', 11), C('payee', 'Payee', 'text', 24), C('amount', 'Amount', 'money', 10), C('account_id', 'Account ID', 'text', 10), C('month', 'Month', 'date', 11),
    CA('account', 'Account', 'text', LK('accounts', 'account', 'account_id', '{col:account_id}'), 20)], D.sub_charges_d(), 300))
# 18 contracts ------------------------------------------------------------------------
tables.append(T('contracts', 'Contracts', 'Insurance, utility, phone, rent and loan contracts',
    'One row per contract: cost, renewal date, notice days and the date to review. Days to renewal, days to review and a review flag fill in by themselves.', [
    C('contract_id', 'Contract ID', 'text', 10, required=True), C('contract', 'Contract', 'text', 24), LST('kind', 'Kind', 'ckind', 18), REF('contact_id', 'Contact ID', 'team.member_id', 10), C('amount', 'Amount', 'money', 11),
    LST('cycle', 'Cycle', 'cycle', 10), C('yearly_cost', 'Cost per year', 'money', 12), C('renewal_date', 'Renewal date', 'date', 11), C('notice_days', 'Notice days', 'int', 9), C('review_on', 'Review on', 'date', 11),
    C('reviewed', 'Reviewed this cycle', 'bool', 10),
    CA('contact', 'Contact', 'text', LK('team', 'name', 'member_id', '{col:contact_id}'), 22), CA('phone', 'Contact phone', 'text', LK('team', 'phone', 'member_id', '{col:contact_id}'), 18),
    CA('days_to_renewal', 'Days to renewal', 'int', '{col:renewal_date}-{today}', 9), CA('days_to_review', 'Days to review', 'int', '{col:review_on}-{today}', 9),
    CA('review_flag', 'Review flag', 'text', 'IF({col:reviewed}=%s,%s,IF({col:days_to_review}<=0,%s,IF({col:days_to_review}<=30,%s,%s)))' % (YES, V('Reviewed'), V('Review now'), V('Review soon'), V('On schedule')), 13),
    CA('review_score', 'Review rank score', 'num', '{col:days_to_review}+%s' % (TIE2 % 'contract_id'), 10), P1PH(), P1N(), HOME()],
    D.contracts_d(), 30, [A('review_flag', '= ' + V('Review now'), 'bad'), A('review_flag', '= ' + V('Review soon'), 'warn'), A('review_flag', '= ' + V('Reviewed'), 'good')]))
# 19 insurance calendar ------------------------------------------------------------------
tables.append(T('ins_cal', 'Insurance Calendar', 'Insurance premiums, renewals and reviews, next 12 months',
    'One row per month ahead: insurance premiums due, insurance contracts renewing and contract reviews due; the share of the year shows which month carries the big premium.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('premiums', 'Insurance premiums due', 'money', 'SUMIFS({range:bill_due.amount},{range:bill_due.month},{col:month},{range:bill_due.category},%s)' % INS, 13),
    CA('renewals', 'Insurance renewals', 'int', 'COUNTIFS({range:contracts.kind},%s,{range:contracts.renewal_date},">="&{col:month},{range:contracts.renewal_date},"<"&EDATE({col:month},1))' % KIND_INS, 10),
    CA('reviews_due', 'Contract reviews due', 'int', 'COUNTIFS({range:contracts.review_on},">="&{col:month},{range:contracts.review_on},"<"&EDATE({col:month},1))', 10),
    CA('yearly_share', 'Share of the year premiums', 'pct', 'IF(SUM({range:ins_cal.premiums})>0,{col:premiums}/SUM({range:ins_cal.premiums}),0)', 10)], D.ins_cal_d(), 20))
# 20 contract review list ------------------------------------------------------------------
def CNT(c, kind='t'): return LK('contracts', c, 'contract_id', '{col:contract_id}', kind)
tables.append(T('contract_review', 'Contract Review List', 'Contracts in the order they need a review',
    'All 12 contracts from the one to review first: days to review, yearly cost and what to do. The action follows the review flag and your review days setting. Fills in by itself.', [
    C('rank', 'No.', 'int', 6, required=True),
    CA('contract_id', 'Contract ID', 'text', 'IFERROR(INDEX({range:contracts.contract_id},MATCH(SMALL({range:contracts.review_score},{col:rank}),{range:contracts.review_score},0)),"")', 10),
    CA('contract', 'Contract', 'text', CNT('contract'), 24), CA('kind', 'Kind', 'text', CNT('kind'), 18), CA('days_to_review', 'Days to review', 'int', CNT('days_to_review', 'n'), 9),
    CA('review_on', 'Review on', 'date', CNT('review_on', 'd'), 11), CA('renewal_date', 'Renewal date', 'date', CNT('renewal_date', 'd'), 11), CA('yearly_cost', 'Cost per year', 'money', CNT('yearly_cost', 'n'), 11),
    CA('action', 'Action', 'text', 'IF(%s=%s,%s,IF({col:days_to_review}<=0,%s,IF({col:days_to_review}<=30,%s,%s)))' % (CNT('reviewed'), YES, V('Keep, already reviewed'), V('Ask for a renewal quote'), V('Prepare your questions'), V('Wait for the review date')), 24),
    CA('contact', 'Contact', 'text', CNT('contact'), 22), CA('phone', 'Contact phone', 'text', CNT('phone'), 18), HOME()], D.rk(12), 20,
    [A('action', '= ' + V('Ask for a renewal quote'), 'bad'), A('action', '= ' + V('Prepare your questions'), 'warn')]))
for _t in tables: _t['rows'] = max(50, _t['rows'])
assert len(tables) == 20, len(tables)
