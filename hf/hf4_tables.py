"""Household Finance suite part 4: settings and the 20 tables (debts, payments, the payoff engine with closed-form cascades, schedules, ratios and history)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf4_lists import *
import hf4_data as D


def R(t, c): return '{range:%s.%s}' % (t, c)
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)
def G(idc, body): return 'IF({col:%s}="","",%s)' % (idc, body)
def DB(c): return R('debts', c)


MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YES, NO = '{list:yesno.yes}', '{list:yesno.no}'
P_ = D.PH
def PHC(who, label): return CA(who + '_phone', label, 'text', '"%s"' % P_[who], 18)
def NAMEC(who, label): return CA(who + '_name', label, 'text', '{set:%s_contact}' % who, 16)
def HH(): return CA('household', 'Household', 'text', '{set:household}', 22)
def N1(): return CA('partner1', 'Partner 1 name', 'text', '{set:partner1}', 14)
def N2(): return CA('partner2', 'Partner 2 name', 'text', '{set:partner2}', 14)
CARD, LOAN_K = tok('dkind', 'Credit card'), tok('dkind', 'Instalment loan')
EXTRA = '{set:extra_payment}'
NS = 8       # debts the payoff engine can order (slots)


def ANN(p, n, b, r):
    """total interest of a debt paid p a month for n months (the last payment is what is left), closed form"""
    return '(%s*(%s-1)+(%s*(1+%s)^(%s-1)-%s*((1+%s)^(%s-1)-1)/%s)*(1+%s)-%s)' % (p, n, b, r, n, p, r, n, r, r, b)


def NP(r, p, b): return 'ROUNDUP(NPER(%s,-%s,%s),0)' % (r, p, b)
TH12 = 'SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&%s)/12' % (R('income', 'net'), R('income', 'month'), MS, R('income', 'month'), MS)
GR12 = 'SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&%s)/12' % (R('income', 'gross'), R('income', 'month'), MS, R('income', 'month'), MS)
BAL = lambda: 'SUM(%s)' % DB('balance')
MINS = 'SUMIFS(%s,%s,">0")' % (DB('min_payment'), DB('balance'))
EXTRAS = 'SUMIFS(%s,%s,">0")' % (DB('extra_planned'), DB('balance'))

settings = [
    S('household', 'Household name', 'text', HOUSEHOLD), S('partner1', 'Partner 1 name, shown in messages', 'text', 'Partner 1'), S('partner2', 'Partner 2 name, shown in messages', 'text', 'Partner 2'),
    S('extra_payment', 'Extra payment a month on all debts', 'money', EXTRA_PAYMENT), S('payoff_method', 'Payoff method you follow', 'list', key('method', 'Avalanche'), list='method'),
    S('next_payday', 'Next payday of partner 1', 'date', iso(PAYDAY1_NEXT)), S('pay_gap_days', 'Days between paydays', 'int', 14), S('margin_days', 'A due date this many days before payday is tight', 'int', 3),
    S('debt_gross_range', 'Debt payments over gross, a typical range', 'pct', DEBT_INCOME_GROSS), S('consumer_debt_range', 'Card debt over take-home, a typical range', 'pct', CONSUMER_DEBT_TAKEHOME),
    S('minimums_range', 'Minimum payments over take-home, your own limit', 'pct', 0.30), S('card_low', 'Card interest, low end, about 12%, check your cards', 'pct', 0.12),
    S('card_high', 'Card interest, high end, about 28%, check your cards', 'pct', 0.28), S('emergency_low', 'Emergency fund months, low end of a typical range', 'int', EMERGENCY_MONTHS_LOW),
    S('emergency_high', 'Emergency fund months, high end of a typical range', 'int', EMERGENCY_MONTHS_HIGH), S('bank_contact', 'Name of your contact at the bank branch', 'text', D.CONTACT['bank']),
    S('tax_contact', 'Name of your tax preparer', 'text', D.CONTACT['tax']), S('ins_contact', 'Name of your insurance agent', 'text', D.CONTACT['ins']),
    S('payroll_contact', 'Name of your contact at the payroll office', 'text', D.CONTACT['payroll']), S('gp_contact', 'Name of the grandparent or household member', 'text', D.CONTACT['gp'])]

tables = []
# 1 debts ------------------------------------------------------------------------------------------------------------------
def snowkey(): return G('debt_id', 'IF({col:balance}>0,ROUND({col:balance}+MATCH({col:debt_id},%s,0)/1000000,6),"")' % DB('debt_id'))
def avalkey(): return G('debt_id', 'IF({col:balance}>0,ROUND({col:rate}*1000-MATCH({col:debt_id},%s,0)/10000,6),"")' % DB('debt_id'))
def PAYO(c): return 'IFERROR(INDEX(%s,MATCH({col:debt},%s,0)),"")' % (R('aval_order', c), R('aval_order', 'debt'))
tables.append(T('debts', 'Debts', 'Debts, Cards and Loans',
    'Up to eight debts with balance, rate, minimum payment and due day; interest, months at the minimum, the snowball and avalanche order and the payoff date fill in. Paid-off debts stay at zero.', [
    C('debt_id', 'Debt ID', 'text', 9, required=True), C('debt', 'Debt', 'text', 26), LST('kind', 'Kind', 'dkind', 14), REF('account_id', 'Account ID', 'accounts.account_id', 10),
    C('balance', 'Balance', 'money', 12), C('rate', 'Yearly rate', 'pct', 9), C('min_payment', 'Minimum payment', 'money', 12), C('due_day', 'Due day', 'int', 8),
    C('extra_planned', 'Extra planned a month', 'int', 11), C('original_amount', 'Original amount', 'int', 11), C('term_months', 'Term months', 'int', 9), LST('owner', 'Owner', 'person', 10),
    C('opened', 'Opened', 'date', 11),
    CA('status', 'Status', 'text', G('debt_id', 'IF({col:balance}>0,%s,%s)' % (st('Active'), st('Paid off'))), 10),
    CA('rm', 'Monthly rate', 'pct', G('debt_id', 'MAX({col:rate}/12,0.000000001)'), 9),
    CA('monthly_interest', 'Interest a month', 'money', G('debt_id', 'IF({col:balance}>0,{col:balance}*{col:rate}/12,0)'), 11),
    CA('covers', 'Minimum against interest', 'text', G('debt_id', 'IF({col:balance}>0,IF({col:min_payment}>{col:monthly_interest}+0.005,%s,%s),%s)' % (st('Covers interest'), st('Below interest'), st('Paid off'))), 15),
    CA('months_min', 'Months at the minimum', 'int', G('debt_id', 'IF({col:balance}>0,IF({col:min_payment}>{col:monthly_interest}+0.005,%s,999),0)' % NP('{col:rm}', '{col:min_payment}', '{col:balance}')), 11),
    CA('min_interest', 'Interest at the minimum', 'money', G('debt_id', 'IF(AND({col:balance}>0,{col:months_min}<999),%s,0)' % ANN('{col:min_payment}', '{col:months_min}', '{col:balance}', '{col:rm}')), 12),
    CA('plan_months', 'Months in the current plan', 'int', G('debt_id', 'IF({col:balance}>0,IF({col:min_payment}+{col:extra_planned}>{col:monthly_interest}+0.005,%s,999),0)' % NP('{col:rm}', '({col:min_payment}+{col:extra_planned})', '{col:balance}')), 11),
    CA('plan_interest', 'Interest in the current plan', 'money', G('debt_id', 'IF(AND({col:balance}>0,{col:plan_months}<999),%s,0)' % ANN('({col:min_payment}+{col:extra_planned})', '{col:plan_months}', '{col:balance}', '{col:rm}')), 12),
    CA('snow_key', 'Snowball key', 'num', snowkey(), 11), CA('snow_rank', 'Snowball order', 'int', G('debt_id', 'IF({col:balance}>0,COUNTIF(%s,"<"&{col:snow_key})+1,"")' % DB('snow_key')), 9),
    CA('aval_key', 'Avalanche key', 'num', avalkey(), 11), CA('aval_rank', 'Avalanche order', 'int', G('debt_id', 'IF({col:balance}>0,COUNTIF(%s,">"&{col:aval_key})+1,"")' % DB('aval_key')), 9),
    CA('int_key', 'Interest rank key', 'num', G('debt_id', 'IF({col:balance}>0,ROUND({col:monthly_interest}+MATCH({col:debt_id},%s,0)/1000000,6),"")' % DB('debt_id')), 11),
    CA('aval_months', 'Months by avalanche', 'int', G('debt_id', PAYO('payoff_month')), 11),
    CA('payoff_date', 'Payoff date by avalanche', 'date', G('debt_id', 'IFERROR(IF(%s=0,"",%s),"")' % (PAYO('payoff_date'), PAYO('payoff_date'))), 12),
    CA('total_debt', 'Total debt', 'money', 'SUM(%s)' % DB('balance'), 12), CA('asof', 'Today', 'date', '{today}', 11),
    CA('new_day', 'Suggested due day', 'int', G('debt_id', 'MIN(28,DAY({set:next_payday})+3)'), 9),
    HH(), N1(), NAMEC('bank', 'Bank branch contact'), PHC('bank', 'Bank branch phone'), PHC('p1', 'Partner 1 phone')],
    D.debts_d(), 50, [A('status', '= ' + st('Paid off'), 'good'), A('covers', '= ' + st('Below interest'), 'bad')]))
# 2 debt payments ---------------------------------------------------------------------------------------------------------
tables.append(T('debt_payments', 'Debt payments', 'Debt Payments',
    'One row for each payment on a card or loan: the minimum, the extra, the interest and the principal; the debt name, the kind and whether it was on time fill in by themselves.', [
    C('payment_id', 'Payment ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), CA('month', 'Month', 'date', G('payment_id', 'DATE(YEAR({col:date}),MONTH({col:date}),1)'), 11),
    REF('debt_id', 'Debt ID', 'debts.debt_id', 9), CA('debt', 'Debt', 'text', LKT('debts.debt', 'debts.debt_id', 'debt_id'), 22), C('minimum', 'Minimum', 'money', 11), C('extra', 'Extra', 'int', 9),
    C('amount', 'Amount', 'money', 11), C('interest', 'Interest', 'money', 11), C('principal', 'Principal', 'money', 11), C('balance_after', 'Balance after', 'money', 12),
    CA('kind', 'Kind', 'text', LKT('debts.kind', 'debts.debt_id', 'debt_id'), 15),
    CA('interest_share', 'Interest share of payment', 'pct', G('payment_id', 'IF({col:amount}>0,{col:interest}/{col:amount},0)'), 12),
    CA('ontime', 'On time', 'int', G('payment_id', 'IF(DAY({col:date})<=IFERROR(INDEX(%s,MATCH({col:debt_id},%s,0)),31)+3,1,0)' % (DB('due_day'), DB('debt_id'))), 8),
    CA('due_day', 'Due day', 'int', G('payment_id', LKN('debts.due_day', 'debts.debt_id', 'debt_id')), 8), HH(), NAMEC('bank', 'Bank branch contact'), PHC('bank', 'Bank branch phone')],
    [{k: v for k, v in r.items() if k != 'debt'} for r in D.payments_d()], 400, [A('ontime', '= 0', 'warn')]))
# 3 accounts ---------------------------------------------------------------------------------------------------------------
tables.append(T('accounts', 'Accounts', 'Accounts',
    'Every account the household holds: current accounts, savings, cards, loans and retirement; a card or loan balance is the amount owed.', [
    C('account_id', 'Account ID', 'text', 10, required=True), C('account', 'Account', 'text', 28), LST('type', 'Type', 'atype', 14), LST('owner', 'Owner', 'person', 10),
    C('opening_balance', 'Opening balance', 'money', 14), C('balance_now', 'Balance now', 'money', 13)], D.accounts_d(), 50))
# 4 income -------------------------------------------------------------------------------------------------------------------
tables.append(T('income', 'Income', 'Income Received',
    'Every paycheck and payment received, with gross and take-home amounts; the debt ratios and the minimums share read the last twelve complete months.', [
    C('income_id', 'Income ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), CA('month', 'Month', 'date', G('income_id', 'DATE(YEAR({col:date}),MONTH({col:date}),1)'), 11),
    LST('person', 'Person', 'payer', 10), LST('source', 'Source', 'isource', 13), C('gross', 'Gross', 'money', 11), C('net', 'Take-home', 'money', 11)], D.income_d(), 300))
# 5 net worth -----------------------------------------------------------------------------------------------------------------
tables.append(T('networth', 'Net worth', 'Net Worth by Account and Month',
    'The month-end balance of every account; cards and loans are liabilities (the amount owed). The balance history reads this sheet.', [
    C('nw_id', 'Net worth ID', 'text', 10, required=True), C('month', 'Month', 'date', 11), REF('account_id', 'Account ID', 'accounts.account_id', 10), LST('type', 'Type', 'atype', 14),
    LST('side', 'Asset or liability', 'side', 12), C('balance', 'Balance', 'money', 13)], D.networth_d(), 500))

# ---- the payoff engine: order tables with a closed-form cascade (the freed payments roll to the next debt) -------------------------
def slot_vals(t, j, W=None, scen=False):
    """expressions of slot j: balance (less a windfall), monthly rate, minimum, payment while first"""
    B = 'INDEX(%s,%d)' % (R(t, 'bal'), j) if W is None else 'MAX(0,INDEX(%s,%d)-MAX(0,%s-INDEX(%s,%d)))' % (R(t, 'bal'), j, W, R(t, 'bcum'), j)
    P = 'INDEX(%s,%d)' % (R(t, 'pay'), j) if not scen else '(INDEX(%s,%d)+{col:xtr}+INDEX(%s,%d))' % (R(t, 'mnp'), j, R(t, 'mroll'), j)
    return dict(B=B, r='INDEX(%s,%d)' % (R(t, 'rm'), j), m='INDEX(%s,%d)' % (R(t, 'mnp'), j), P=P)


def RAW(B, r, m, prev): return '(%s*(1+%s)^%s-%s*((1+%s)^%s-1)/%s)' % (B, r, prev, m, r, prev, r)
def ZV(B, r, m, prev): return 'MAX(0,ROUND(%s,2))' % RAW(B, r, m, prev)


def chain_cols(t, W=None):
    """work columns z1..zN (balance when slot j gets the focus), c1..cN (month slot j is cleared), i1..iN (interest of slot j)"""
    cols = []
    for j in range(1, NS + 1):
        v = slot_vals(t, j, W, True); B, r, m, Pj = v['B'], v['r'], v['m'], v['P']
        prev = '{col:c%d}' % (j - 1) if j > 1 else '0'
        cols.append(CA('z%d' % j, 'Work: start balance, slot %d' % j, 'money', ZV(B, r, m, prev), 11))
        cols.append(CA('c%d' % j, 'Work: cleared in month, slot %d' % j, 'int', 'MIN(999,%s+IF({col:z%d}=0,0,IF(%s<={col:z%d}*%s+0.005,999,%s)))' % (prev, j, Pj, j, r, NP(r, Pj, '{col:z%d}' % j)), 9))
        nf = '({col:c%d}-%s)' % (j, prev)
        early = ANN(m, NP(r, m, B), B, r)
        focus = '(%s*%s+%s*(%s-1)+({col:z%d}*(1+%s)^(%s-1)-%s*((1+%s)^(%s-1)-1)/%s)*(1+%s)-%s)' % (m, prev, Pj, nf, j, r, nf, Pj, r, nf, r, r, B)
        cols.append(CA('i%d' % j, 'Work: interest, slot %d' % j, 'money', 'IF(%s<=0,0,IF({col:z%d}=0,%s,IF({col:c%d}>=999,0,%s)))' % (B, j, early, j, focus), 11))
    return cols


def order_table(t, sheet, title, hint, rank, other):
    def pick(c, default='0'): return 'IFERROR(INDEX(%s,MATCH({col:slot},%s,0)),%s)' % (DB(c), DB(rank), default)
    Rt = lambda c: R(t, c)
    ch = []
    for j in range(1, NS + 1):
        v = slot_vals(t, j); B, r, m, Pj = v['B'], v['r'], v['m'], v['P']
        prev = '{col:c%d}' % (j - 1) if j > 1 else '0'
        z = ZV(B, r, m, prev)
        ch.append(CA('c%d' % j, 'Work: cleared in month, slot %d' % j, 'int', G('slot', 'MIN(999,%s+IF(%s=0,0,IF(%s<=%s*%s+0.005,999,%s)))' % (prev, z, Pj, z, r, NP(r, Pj, z))), 9))
    cs = ','.join('{col:c%d}' % j for j in range(1, NS + 1))
    cols = [C('slot', 'Order', 'int', 7, required=True),
        CA('debt', 'Debt', 'text', pick('debt', '""'), 20), CA('bal', 'Balance', 'money', pick('balance'), 11),
        CA('rate', 'Yearly rate', 'pct', pick('rate'), 9), CA('mnp', 'Minimum payment', 'money', pick('min_payment'), 11),
        CA('rm', 'Monthly rate', 'pct', 'MAX({col:rate}/12,0.000000001)', 9),
        CA('tm', 'Months at the minimum', 'int', 'IF({col:bal}>0,IF({col:mnp}>{col:bal}*{col:rm}+0.005,%s,999),0)' % NP('{col:rm}', '{col:mnp}', '{col:bal}'), 10),
        CA('mroll', 'Earlier minimums', 'money', 'IF({col:slot}="",0,SUMIFS(%s,%s,"<"&{col:slot}))' % (Rt('mnp'), Rt('slot')), 11),
        CA('bcum', 'Earlier balances', 'money', 'IF({col:slot}="",0,SUMIFS(%s,%s,"<"&{col:slot}))' % (Rt('bal'), Rt('slot')), 11),
        CA('pay', 'Payment while first', 'money', 'IF({col:bal}>0,{col:mnp}+%s+{col:mroll},0)' % EXTRA, 11)] + ch + [
        CA('sp', 'Starts after month', 'int', 'IFERROR(IF({col:slot}=1,0,CHOOSE({col:slot}-1,%s)),0)' % ','.join('{col:c%d}' % j for j in range(1, NS)), 9),
        CA('clr', 'Cleared by month', 'int', 'IFERROR(CHOOSE({col:slot},%s),0)' % cs, 9),
        CA('bal0', 'Balance when first', 'money', 'IF({col:bal}=0,0,%s)' % ZV('{col:bal}', '{col:rm}', '{col:mnp}', '{col:sp}'), 11),
        CA('payoff_month', 'Payoff month number', 'int', 'IF({col:bal}=0,0,IF({col:bal0}=0,{col:tm},{col:clr}))', 9),
        CA('payoff_date', 'Payoff date', 'date', 'IF(OR({col:bal}=0,{col:payoff_month}>=999),"",EOMONTH(%s,{col:payoff_month}))' % MS, 11),
        CA('interest', 'Interest to payoff', 'money', 'IF(OR({col:bal}=0,{col:payoff_month}>=999),0,IF({col:bal0}=0,%s,%s))' % (
            ANN('{col:mnp}', '{col:tm}', '{col:bal}', '{col:rm}'),
            '({col:mnp}*{col:sp}+{col:pay}*({col:clr}-{col:sp}-1)+({col:bal0}*(1+{col:rm})^({col:clr}-{col:sp}-1)-{col:pay}*((1+{col:rm})^({col:clr}-{col:sp}-1)-1)/{col:rm})*(1+{col:rm})-{col:bal})'), 11),
        CA('tot_b', 'Total debt', 'money', 'SUM(%s)' % Rt('bal'), 12),
        CA('budget', 'Monthly payment, all debts', 'money', 'SUM(%s)+%s' % (Rt('mnp'), EXTRA), 13), CA('months_all', 'Months to debt-free', 'int', 'MAX(%s)' % Rt('payoff_month'), 10),
        CA('interest_all', 'Total interest', 'money', 'SUM(%s)' % Rt('interest'), 12),
        CA('free_date', 'Debt-free date', 'date', 'IF(OR({col:months_all}=0,{col:months_all}>=999),"",EOMONTH(%s,{col:months_all}))' % MS, 12),
        CA('other_months', 'Months, other method', 'int', 'MAX(%s)' % R(other, 'payoff_month'), 10), CA('other_interest', 'Interest, other method', 'money', 'SUM(%s)' % R(other, 'interest'), 12),
        CA('saved_interest', 'Interest less than the other method', 'money', '{col:other_interest}-{col:interest_all}', 13), CA('saved_months', 'Months less than the other method', 'int', '{col:other_months}-{col:months_all}', 11),
        HH(), N1(), N2(), PHC('p1', 'Partner 1 phone'), PHC('p2', 'Partner 2 phone')]
    return T(t, sheet, title, hint, cols, D.slots_d(), 50, [A('payoff_month', '>= 999', 'bad')])


tables.append(order_table('snow_order', 'Snowball order', 'Snowball Order, Smallest Balance First',
    'The debts from the smallest balance up: the first gets the extra payment, and a cleared debt rolls its payment to the next. Payoff month, date and interest fill in. Estimates.', 'snow_rank', 'aval_order'))
tables.append(order_table('aval_order', 'Avalanche order', 'Avalanche Order, Highest Rate First',
    'The debts from the highest rate down: the first gets the extra payment, and a cleared debt rolls its payment to the next. Payoff month, date and interest fill in. Estimates.', 'aval_rank', 'snow_order'))
# schedules (rows = months) -----------------------------------------------------------------------------------------------------------------
def BALX(t, nx):
    sp, s, rm, b, m, P, z, tm = (R(t, c) for c in ('sp', 'clr', 'rm', 'bal', 'mnp', 'pay', 'bal0', 'tm'))
    g1 = '(1+%s)^%s' % (rm, nx); g2 = '(1+%s)^(%s-%s)' % (rm, nx, sp)
    return '(%s<=%s)*(%s<%s)*(%s*%s-%s*(%s-1)/%s)+(%s>%s)*(%s<%s)*(%s*%s-%s*(%s-1)/%s)' % (nx, sp, nx, tm, b, g1, m, g1, rm, nx, sp, nx, s, z, g2, P, g2, rm)


def sched_table(t, sheet, title, hint, order):
    Rt = lambda c: R(t, c)
    return T(t, sheet, title, hint, [
        C('month_no', 'Month number', 'int', 8, required=True), CA('month', 'Month', 'date', G('month_no', 'EDATE(%s,{col:month_no})' % MS), 11),
        CA('payment', 'Payment', 'money', G('month_no', '{col:interest}+{col:principal}'), 11),
        CA('interest', 'Interest', 'money', G('month_no', 'SUMPRODUCT(IFERROR(%s*(%s),0))' % (R(order, 'rm'), BALX(order, '({col:month_no}-1)'))), 11),
        CA('principal', 'Principal', 'money', G('month_no', 'IF({col:month_no}=1,SUM(%s),INDEX(%s,{col:month_no}-1))-{col:balance}' % (R(order, 'bal'), Rt('balance'))), 11),
        CA('balance', 'Total balance', 'money', G('month_no', 'SUMPRODUCT(IFERROR(%s,0))' % BALX(order, '{col:month_no}')), 12),
        CA('debts_left', 'Debts left', 'int', G('month_no', 'SUMPRODUCT(ISNUMBER(%s)*ISNUMBER(%s)*(%s>0)*({col:month_no}<%s))' % (R(order, 'bal'), R(order, 'payoff_month'), R(order, 'bal'), R(order, 'payoff_month'))), 8),
        CA('cum_interest', 'Interest so far', 'money', G('month_no', 'SUMIFS(%s,%s,"<="&{col:month_no})' % (Rt('interest'), Rt('month_no'))), 12),
        CA('paid_share', 'Share of debt paid', 'pct', G('month_no', 'IF(SUM(%s)>0,1-{col:balance}/SUM(%s),0)' % (R(order, 'bal'), R(order, 'bal'))), 10),
        LST('planyear', 'Plan year', 'planyear', 9)], D.sched_d(), 60)
tables.append(sched_table('sched_snow', 'Snowball schedule', 'Snowball Payoff Schedule, Month by Month', 'Month by month: the payment, the interest, the principal and the balance left if the smallest balance gets the extra payment first. An estimate from your numbers.', 'snow_order'))
tables.append(sched_table('sched_aval', 'Avalanche schedule', 'Avalanche Payoff Schedule, Month by Month', 'Month by month: the payment, the interest, the principal and the balance left if the highest rate gets the extra payment first. An estimate from your numbers.', 'aval_order'))

# 10 payoff comparison -----------------------------------------------------------------------------------------------------------------
XT = lambda c: R('extra_test', c)
PL = lambda lab: tok('plans', lab)
def PICK5(a, b, c, d, e): return 'IF({col:plan}=%s,%s,IF({col:plan}=%s,%s,IF({col:plan}=%s,%s,IF({col:plan}=%s,%s,%s))))' % (PL(PLANS[0]), a, PL(PLANS[1]), b, PL(PLANS[2]), c, PL(PLANS[3]), d, e)
tables.append(T('compare', 'Payoff comparison', 'Payoff Comparison, Five Ways to Pay',
    'The months to debt-free and the total interest if you pay only the minimums, keep your current plan, follow snowball, follow avalanche, or follow avalanche with 100 more; estimates from your numbers.', [
    LST('plan', 'Payoff plan', 'plans', 26, required=True),
    CA('months', 'Months to debt-free', 'int', G('plan', PICK5('MAX(%s)' % DB('months_min'), 'MAX(%s)' % DB('plan_months'), 'MAX(%s)' % R('snow_order', 'payoff_month'), 'MAX(%s)' % R('aval_order', 'payoff_month'),
                                                          'IFERROR(INDEX(%s,MATCH(100,%s,0)),"")' % (XT('months'), XT('offset')))), 12),
    CA('interest', 'Total interest', 'money', G('plan', PICK5('SUM(%s)' % DB('min_interest'), 'SUM(%s)' % DB('plan_interest'), 'SUM(%s)' % R('snow_order', 'interest'), 'SUM(%s)' % R('aval_order', 'interest'),
                                                           'IFERROR(INDEX(%s,MATCH(100,%s,0)),"")' % (XT('interest'), XT('offset')))), 13)],
    D.plans_d(), 50))
# 11 extra payment plan (per debt: the plan now against all the extra on the highest rate) ------------------------------------------------
def LD(c, default='0'): return 'IFERROR(INDEX(%s,MATCH({col:debt},%s,0)),%s)' % (DB(c), DB('debt'), default)
def I12(p): return '(%s*{T}-{col:balance}+({col:balance}*(1+{col:rm})^{T}-%s*((1+{col:rm})^{T}-1)/{col:rm}))' % (p, p)
def I12X(p): return I12(p).replace('{T}', 'IFERROR(MIN(12,NPER({col:rm},-%s,{col:balance})),12)' % p)
EP = lambda c: R('extra_plan', c)
tables.append(T('extra_plan', 'Extra payment plan', 'Extra Payment Plan, Current Split and Avalanche',
    'Each debt with the extra you pay now and the extra it would get if all of it went to the highest rate; the interest lost in 12 months fills in. An estimate.', [
    REF('debt', 'Debt', 'debts.debt', 26, required=True), CA('balance', 'Balance', 'money', G('debt', LD('balance')), 11), CA('rate', 'Yearly rate', 'pct', G('debt', LD('rate')), 9),
    CA('rm', 'Monthly rate', 'pct', G('debt', LD('rm', '0.000000001')), 9), CA('min_payment', 'Minimum payment', 'money', G('debt', LD('min_payment')), 11),
    CA('extra_now', 'Extra now', 'money', G('debt', LD('extra_planned')), 10), CA('top', 'Highest rate', 'int', G('debt', 'IF(%s=1,1,0)' % LD('aval_rank')), 8),
    CA('extra_aval', 'Extra by avalanche', 'money', G('debt', 'IF({col:top}=1,%s,0)' % EXTRAS), 11), CA('difference', 'Move (+) or take away (-)', 'money', G('debt', '{col:extra_aval}-{col:extra_now}'), 12),
    CA('int12_now', 'Interest in 12 months now', 'money', G('debt', 'IF({col:balance}>0,%s,0)' % I12X('({col:min_payment}+{col:extra_now})')), 12),
    CA('int12_aval', 'Interest in 12 months by avalanche', 'money', G('debt', 'IF({col:balance}>0,%s,0)' % I12X('({col:min_payment}+{col:extra_aval})')), 13),
    CA('interest_lost_year', 'Interest lost in a year', 'money', G('debt', '{col:int12_now}-{col:int12_aval}'), 12),
    CA('months_now', 'Months, current plan', 'int', G('debt', LD('plan_months')), 10),
    CA('months_aval', 'Months, avalanche', 'int', G('debt', 'IFERROR(INDEX(%s,MATCH({col:debt},%s,0)),0)' % (R('aval_order', 'payoff_month'), R('aval_order', 'debt'))), 10),
    CA('months_snow', 'Months, snowball', 'int', G('debt', 'IFERROR(INDEX(%s,MATCH({col:debt},%s,0)),0)' % (R('snow_order', 'payoff_month'), R('snow_order', 'debt'))), 10),
    CA('status', 'Rate order', 'text', G('debt', 'IF({col:balance}=0,%s,IF({col:top}=1,%s,%s))' % (st('Paid off'), st('Highest rate'), st('Lower rate'))), 12),
    CA('lost_total', 'Interest lost in a year, all debts', 'money', 'SUM(%s)' % R('extra_plan', 'interest_lost_year'), 13), CA('move_total', 'Extra to move to the highest rate', 'money', 'IFERROR(INDEX(%s,MATCH(1,%s,0)),0)' % (R('extra_plan', 'difference'), R('extra_plan', 'top')), 13),
    HH(), N2(), PHC('p2', 'Partner 2 phone'), NAMEC('gp', 'Grandparent contact'), PHC('gp', 'Grandparent phone')], D.debt_names_d(), 50, [A('status', '= ' + st('Highest rate'), 'warn')]))
# 12 extra payment test (rows = extra payment steps, the avalanche cascade for each) -----------------------------------------------------
def offset_formula():
    f = '0'
    for off, lab in reversed(list(zip(XOFF, XSTEPS))): f = 'IF({col:step}=%s,%d,%s)' % (tok('xstep', lab), off, f)
    return f
MINMONTHS, MININT = 'MAX(%s)' % DB('months_min'), 'SUM(%s)' % DB('min_interest')
def scen_summary(idc, base_m, base_i):
    return [CA('months', 'Months to debt-free', 'int', G(idc, '{col:c%d}' % NS), 10),
            CA('debt_free', 'Debt-free date', 'date', G(idc, 'IF(OR({col:months}=0,{col:months}>=999),"",EOMONTH(%s,{col:months}))' % MS), 12),
            CA('interest', 'Total interest', 'money', G(idc, '+'.join('{col:i%d}' % j for j in range(1, NS + 1))), 12),
            CA('months_saved', 'Months saved', 'int', G(idc, 'IF({col:months}>=999,"",%s-{col:months})' % base_m), 10),
            CA('interest_saved', 'Interest saved', 'money', G(idc, 'IF({col:months}>=999,"",%s-{col:interest})' % base_i), 12)]
def gchain(cols, idc):
    out = []
    for c in cols:
        c = dict(c); c['formula'] = G(idc, c['formula']); out.append(c)
    return out
tables.append(T('extra_test', 'Extra test steps', 'Extra Payment Test, What Each Step Saves',
    'The avalanche plan at each step above or below your extra payment in Settings: the debt-free date, the months and the interest saved against paying only the minimums. Estimates from your numbers.', [
    LST('step', 'Extra payment step', 'xstep', 18, required=True), CA('offset', 'Step', 'int', G('step', offset_formula()), 8),
    CA('xtr', 'Extra a month', 'money', G('step', 'MAX(0,%s+{col:offset})' % EXTRA), 11)] + scen_summary('step', MINMONTHS, MININT) + [HH(), N2(), PHC('p2', 'Partner 2 phone')]
    + gchain(chain_cols('aval_order'), 'step'), D.xsteps_d(), 50))
# 13 minimum only payoff ----------------------------------------------------------------------------------------------------------------
def LD2(c, default='0'): return 'IFERROR(INDEX(%s,MATCH({col:debt},%s,0)),%s)' % (DB(c), DB('debt'), default)
tables.append(T('min_only', 'Minimum only by debt', 'Minimum Only Payoff, Each Debt',
    'Each debt paid at its minimum only: the months, the payoff date and the interest; a minimum that does not cover the monthly interest is flagged with the amount it falls short.', [
    REF('debt', 'Debt', 'debts.debt', 26, required=True), CA('rate', 'Yearly rate', 'pct', G('debt', LD2('rate')), 9), CA('min_payment', 'Minimum payment', 'money', G('debt', LD2('min_payment')), 11),
    CA('balance', 'Balance', 'money', G('debt', LD2('balance')), 11), CA('monthly_interest', 'Interest a month', 'money', G('debt', LD2('monthly_interest')), 11),
    CA('months', 'Months at the minimum', 'int', G('debt', LD2('months_min')), 11), CA('payoff_date', 'Payoff date at the minimum', 'date', G('debt', 'IF(OR({col:months}=0,{col:months}>=999),"",EOMONTH(%s,{col:months}))' % MS), 13),
    CA('interest', 'Interest at the minimum', 'money', G('debt', LD2('min_interest')), 12), CA('covers', 'Minimum against interest', 'text', G('debt', LD2('covers', '""') + '&""'), 15),
    CA('shortfall', 'Short of the interest by', 'money', G('debt', 'IF(AND({col:balance}>0,{col:min_payment}<={col:monthly_interest}+0.005),{col:monthly_interest}+0.01-{col:min_payment},0)'), 12),
    CA('plan_months', 'Months, current plan', 'int', G('debt', LD2('plan_months')), 10), HH(), N1(), PHC('p1', 'Partner 1 phone'), NAMEC('bank', 'Bank branch contact'), PHC('bank', 'Bank branch phone'), NAMEC('payroll', 'Payroll office contact'), PHC('payroll', 'Payroll office phone'), NAMEC('ins', 'Insurance agent contact'), PHC('ins', 'Insurance agent phone')],
    D.debt_names_d(), 50, [A('shortfall', '> 0', 'bad')]))
# 14 minimums against pay ----------------------------------------------------------------------------------------------------------------
tables.append(T('mins_pay', 'Minimums against pay', 'Minimum Payments Against Take-home Pay',
    'For each complete month: the minimum payments made, the take-home pay received, the share and whether it is within your own limit in Settings.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('minimums', 'Minimums paid', 'money', G('month', 'SUMIFS(%s,%s,{col:month})' % (R('debt_payments', 'minimum'), R('debt_payments', 'month'))), 12),
    CA('take_home', 'Take-home pay', 'money', G('month', 'SUMIFS(%s,%s,{col:month})' % (R('income', 'net'), R('income', 'month'))), 12),
    CA('share', 'Share of take-home', 'pct', G('month', 'IF({col:take_home}>0,{col:minimums}/{col:take_home},0)'), 11),
    CA('ok', 'Within your limit', 'int', G('month', 'IF({col:share}<={set:minimums_range},1,0)'), 9),
    CA('flag', 'Status', 'text', G('month', 'IF({col:ok}=1,%s,%s)' % (st('Within your limit'), st('Above your limit'))), 15), HH(), N2(), PHC('p2', 'Partner 2 phone')],
    D.months24_d(), 50, [A('flag', '= ' + st('Above your limit'), 'warn')]))
# 15 debt ratios -------------------------------------------------------------------------------------------------------------------------------
CARDPAY = '(SUMIFS(%s,%s,%s,%s,">0")+SUMIFS(%s,%s,%s,%s,">0"))' % (DB('min_payment'), DB('kind'), CARD, DB('balance'), DB('extra_planned'), DB('kind'), CARD, DB('balance'))
LOANPAY = '(SUMIFS(%s,%s,%s,%s,">0")+SUMIFS(%s,%s,%s,%s,">0"))' % (DB('min_payment'), DB('kind'), LOAN_K, DB('balance'), DB('extra_planned'), DB('kind'), LOAN_K, DB('balance'))
CARDBAL = 'SUMIFS(%s,%s,%s)' % (DB('balance'), DB('kind'), CARD)
PAYTOT = '(%s+%s)' % (MINS, EXTRAS)
RT = lambda lab: tok('ratio', lab)
RVAL = [('Debt payments over gross income', '%s/(%s)' % (PAYTOT, GR12), '{set:debt_gross_range}'), ('Consumer debt over take-home', '%s/(%s)' % (CARDPAY, TH12), '{set:consumer_debt_range}'),
        ('Minimum payments over take-home', '%s/(%s)' % (MINS, TH12), '{set:minimums_range}'), ('Loan payments over take-home', '%s/(%s)' % (LOANPAY, TH12), '""'),
        ('Total debt over yearly gross income', '%s/(12*(%s))' % (BAL(), GR12), '""'), ('Card balances over yearly take-home', '%s/(12*(%s))' % (CARDBAL, TH12), '""'),
        ('Extra payment over take-home', '%s/(%s)' % (EXTRAS, TH12), '""'), ('Interest share of debt payments', 'SUM(%s)/%s' % (DB('monthly_interest'), PAYTOT), '""'),
        ('Highest rate against the card range', 'SUMPRODUCT(MAX((%s>0)*%s))' % (DB('balance'), DB('rate')), '{set:card_high}'),
        ('Average rate against the card range', 'SUMPRODUCT(%s,%s)/SUM(%s)' % (DB('balance'), DB('rate'), DB('balance')), '{set:card_high}'),
        ('Cards share of total debt', '%s/%s' % (CARDBAL, BAL()), '""'), ('Loans share of total debt', '1-%s/%s' % (CARDBAL, BAL()), '""')]
def rsel(idx):
    f = '0' if idx == 1 else '""'
    for lab, v, r in reversed(RVAL): f = 'IF({col:ratio}=%s,%s,%s)' % (RT(lab), (lab, v, r)[idx], f)
    return f
tables.append(T('ratios', 'Debt ratio list', 'Debt Ratios Against Typical Ranges',
    'Twelve ratios of your debts to your income, each against the typical range in Settings where one exists; every range is a typical range, check your own numbers, never advice.', [
    LST('ratio', 'Ratio', 'ratio', 34, required=True), CA('value', 'Value', 'pct', G('ratio', 'IFERROR(%s,0)' % rsel(1)), 10), CA('range', 'Typical range', 'pct', G('ratio', rsel(2)), 11),
    CA('has_range', 'Has a range', 'int', G('ratio', 'IF({col:range}="",0,1)'), 8),
    CA('in_range', 'Within the range', 'int', G('ratio', 'IF({col:has_range}=0,0,IF(OR({col:ratio}=%s,{col:ratio}=%s),IF(AND({col:value}>={set:card_low},{col:value}<={set:card_high}),1,0),IF({col:value}<={col:range},1,0)))' % (RT('Highest rate against the card range'), RT('Average rate against the card range'))), 9),
    CA('diff', 'Above (+) or below (-) the range', 'pct', G('ratio', 'IF({col:has_range}=0,"",{col:value}-{col:range})'), 13),
    CA('flag', 'Status', 'text', G('ratio', 'IF({col:has_range}=0,%s,IF({col:in_range}=1,%s,IF({col:value}>{col:range},%s,%s)))' % (st('No typical range'), st('Within range'), st('Above range'), st('Below range'))), 14),
    HH(), N2(), PHC('p2', 'Partner 2 phone'), NAMEC('bank', 'Bank branch contact'), PHC('bank', 'Bank branch phone')], D.ratios_d(), 50, [A('flag', '= ' + st('Above range'), 'warn'), A('flag', '= ' + st('Within range'), 'good')]))
# 16 balance history ----------------------------------------------------------------------------------------------------------------------------
NWR = lambda c: R('networth', c)
LIAB, ASSET = '{list:side.liability}', '{list:side.asset}'
tables.append(T('history', 'Balance history', 'Balance History, Cards and Loans by Month',
    'The month-end balance of cards and loans from the net worth sheet, with the total debt, the change on the month before and the net worth; it feeds the trend tool and the charts.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('cards', 'Card balances', 'money', G('month', 'SUMIFS(%s,%s,{col:month},%s,%s)' % (NWR('balance'), NWR('month'), NWR('type'), tok('atype', 'Credit card'))), 12),
    CA('loans', 'Loan balances', 'money', G('month', 'SUMIFS(%s,%s,{col:month},%s,%s)' % (NWR('balance'), NWR('month'), NWR('type'), tok('atype', 'Loan'))), 12),
    CA('total_debt', 'Total debt', 'money', G('month', '{col:cards}+{col:loans}'), 12),
    CA('change', 'Change on the month before', 'money', G('month', 'IF(COUNTIFS(%s,EDATE({col:month},-1))=0,0,{col:total_debt}-SUMIFS(%s,%s,EDATE({col:month},-1),%s,%s))' % (NWR('month'), NWR('balance'), NWR('month'), NWR('side'), LIAB)), 13),
    CA('assets', 'Assets', 'money', G('month', 'SUMIFS(%s,%s,{col:month},%s,%s)' % (NWR('balance'), NWR('month'), NWR('side'), ASSET)), 12),
    CA('net_worth', 'Net worth', 'money', G('month', '{col:assets}-{col:total_debt}'), 12), CA('ago12', 'A year ago', 'int', G('month', 'IF({col:month}=EDATE(%s,-12),1,0)' % MS), 8),
    CA('ago3', '3 months ago', 'int', G('month', 'IF({col:month}=EDATE(%s,-3),1,0)' % MS), 8), HH(), N1(), N2(), PHC('p1', 'Partner 1 phone'), PHC('p2', 'Partner 2 phone'), NAMEC('gp', 'Grandparent contact'), PHC('gp', 'Grandparent phone')],
    D.months25_d(), 50))
# 17 interest paid by month ------------------------------------------------------------------------------------------------------------------------
DPR = lambda c: R('debt_payments', c)
tables.append(T('interest_month', 'Interest paid by month', 'Interest, Principal and Extra Paid by Month',
    'For each complete month: the minimum and extra payments made, how much was interest and how much reduced the debt; the months that met the planned extra payment are marked.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('minimum_paid', 'Minimums paid', 'money', G('month', 'SUMIFS(%s,%s,{col:month})' % (DPR('minimum'), DPR('month'))), 11),
    CA('extra_paid', 'Extra paid', 'money', G('month', 'SUMIFS(%s,%s,{col:month})' % (DPR('extra'), DPR('month'))), 11),
    CA('interest', 'Interest paid', 'money', G('month', 'SUMIFS(%s,%s,{col:month})' % (DPR('interest'), DPR('month'))), 11),
    CA('principal', 'Principal paid', 'money', G('month', 'SUMIFS(%s,%s,{col:month})' % (DPR('principal'), DPR('month'))), 11),
    CA('total_paid', 'Total paid', 'money', G('month', '{col:minimum_paid}+{col:extra_paid}'), 11),
    CA('extra_met', 'Met the planned extra', 'int', G('month', 'IF(AND(%s>0,{col:extra_paid}>=%s-0.005),1,0)' % (EXTRA, EXTRA)), 9),
    HH(), N1(), N2(), PHC('p1', 'Partner 1 phone'), PHC('p2', 'Partner 2 phone')], D.months24_d(), 50))
# 18 payments by debt ------------------------------------------------------------------------------------------------------------------------------
def PB(c): return 'SUMIFS(%s,%s,{col:debt},%s,">="&EDATE(%s,-12),%s,"<"&%s)' % (DPR(c), DPR('debt'), DPR('month'), MS, DPR('month'), MS)
tables.append(T('pay_by_debt', 'Payments by debt', 'Payments by Debt, Last 12 Complete Months',
    'For each debt the payments of the last twelve complete months: total paid, interest, principal and extra, and how the balance changed in the year.', [
    REF('debt', 'Debt', 'debts.debt', 26, required=True), CA('paid12', 'Paid, 12 months', 'money', G('debt', PB('amount')), 12), CA('interest12', 'Interest, 12 months', 'money', G('debt', PB('interest')), 12),
    CA('principal12', 'Principal, 12 months', 'money', G('debt', PB('principal')), 12), CA('extra12', 'Extra, 12 months', 'money', G('debt', PB('extra')), 12),
    CA('count12', 'Payments made', 'int', G('debt', 'COUNTIFS(%s,{col:debt},%s,">="&EDATE(%s,-12),%s,"<"&%s)' % (DPR('debt'), DPR('month'), MS, DPR('month'), MS)), 9),
    CA('balance_now', 'Balance now', 'money', G('debt', LD2('balance')), 11),
    CA('balance_ago', 'Balance a year ago', 'money', G('debt', 'SUMIFS(%s,%s,%s,%s,EDATE(%s,-12))' % (NWR('balance'), NWR('account_id'), LD2('account_id', '""'), NWR('month'), MS)), 13),
    CA('change', 'Balance change', 'money', G('debt', '{col:balance_now}-{col:balance_ago}'), 12), CA('interest_share', 'Interest share of payments', 'pct', G('debt', 'IF({col:paid12}>0,{col:interest12}/{col:paid12},0)'), 12),
    HH(), N1(), PHC('p1', 'Partner 1 phone'), NAMEC('tax', 'Tax preparer contact'), PHC('tax', 'Tax preparer phone')], D.debt_names_d(), 50))
# 19 due days map -----------------------------------------------------------------------------------------------------------------------------------
tables.append(T('due_map', 'Due days map', 'Due Days Map, Due Dates Against Payday',
    'For each debt: the next due date, the paydays around it and the days before payday; a due date within a few days before payday is tight and gets a suggested due day.', [
    REF('debt', 'Debt', 'debts.debt', 26, required=True), CA('due_day', 'Due day', 'int', G('debt', LD2('due_day')), 8),
    CA('active', 'Active', 'int', G('debt', 'IF(%s>0,1,0)' % LD2('balance')), 7),
    CA('next_due', 'Next due date', 'date', G('debt', 'IF({col:active}=0,"",IF(DAY({today})<=MIN({col:due_day},28),DATE(YEAR({today}),MONTH({today}),MIN({col:due_day},28)),DATE(YEAR({today}),MONTH({today})+1,MIN({col:due_day},28))))'), 12),
    CA('days_to_due', 'Days to due', 'int', G('debt', 'IF({col:next_due}="","",{col:next_due}-{today})'), 8),
    CA('prev_payday', 'Payday before', 'date', G('debt', 'IF({col:next_due}="","",{set:next_payday}+{set:pay_gap_days}*INT(({col:next_due}-{set:next_payday})/{set:pay_gap_days}))'), 12),
    CA('next_payday', 'Payday after', 'date', G('debt', 'IF({col:next_due}="","",{col:prev_payday}+{set:pay_gap_days})'), 12),
    CA('days_before', 'Days before payday', 'int', G('debt', 'IF({col:next_due}="","",{col:next_payday}-{col:next_due})'), 10),
    CA('flag', 'Due date against payday', 'text', G('debt', 'IF({col:next_due}="",%s,IF({col:days_before}<={set:margin_days},%s,%s))' % (st('Paid off'), st('Tight'), st('Comfortable'))), 14),
    CA('pay_on', 'Pay on', 'date', G('debt', 'IF({col:next_due}="","",IF({col:flag}=%s,MAX({today},{col:prev_payday}),{col:next_due}))' % st('Tight')), 11),
    CA('new_day', 'Suggested due day', 'int', G('debt', 'IF({col:next_payday}="","",MIN(28,DAY({col:next_payday})+3))'), 9), HH(), N1(), NAMEC('bank', 'Bank branch contact'), PHC('bank', 'Bank branch phone'), PHC('p1', 'Partner 1 phone'), NAMEC('gp', 'Grandparent contact'), PHC('gp', 'Grandparent phone')],
    D.debt_names_d(), 50, [A('flag', '= ' + st('Tight'), 'warn')]))
# 20 windfall to debt --------------------------------------------------------------------------------------------------------------------------------
tables.append(T('windfall', 'Windfall steps', 'Windfall to Debt, Each Amount Applied to the Highest Rate',
    'A windfall of each size applied to the highest-rate debt first (then the next); the new debt-free date, the months and the interest saved against the avalanche plan. Estimates from your numbers.', [
    C('wfa', 'Windfall amount', 'money', 11, required=True), CA('xtr', 'Extra a month', 'money', 'IF({col:wfa}="",0,%s)' % EXTRA, 11),
    CA('applied', 'Applied to debts', 'money', G('wfa', 'MIN({col:wfa},SUM(%s))' % R('aval_order', 'bal')), 11),
    CA('target', 'First debt it goes to', 'text', G('wfa', 'IFERROR(INDEX(%s,1),"")&""' % R('aval_order', 'debt')), 20)]
    + scen_summary('wfa', 'MAX(%s)' % R('aval_order', 'payoff_month'), 'SUM(%s)' % R('aval_order', 'interest')) + [
    CA('left_over', 'Left after all debts', 'money', G('wfa', '{col:wfa}-{col:applied}'), 12), HH(), N2(), PHC('p2', 'Partner 2 phone')]
    + gchain(chain_cols('aval_order', '{col:wfa}'), 'wfa'), D.windfall_d(), 50))
