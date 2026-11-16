"""Household Finance suite part 7: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hf7_lists import *
import hf7_data as D


def R(t, c): return '{range:%s.%s}' % (t, c)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)


MS = 'DATE(YEAR({today}),MONTH({today}),1)'
G_FIX, G_VAR, G_WANT, G_SAV, G_DEBT = (tok('group', g) for g in GROUPS)
NOA, IKE, BOTH = tok('child', 'Noa'), tok('child', 'Ike'), tok('child', 'Both children')


def TL(col, role):
    """a team value by role (Partner 1, Bank branch ...)"""
    return 'IFERROR(INDEX(%s,MATCH({list:role.%s},%s,0))&"","")' % (R('team', col), key('role', role), R('team', 'role'))


def SCV(item): return 'SUMIFS(%s,%s,%s)' % (R('scenarios', 'value'), R('scenarios', 'item'), tok('sitem', item))
def NEED(): return '(SUMIFS(%s,%s,%s)+SUMIFS(%s,%s,%s))' % (R('lose', 'plan'), R('lose', 'group'), G_FIX, R('lose', 'plan'), R('lose', 'group'), G_VAR)
def INC(p, d0, d1): return 'SUMIFS(%s,%s,%s,%s,">="&%s,%s,"<"&%s)' % (R('income', 'net'), R('income', 'person'), p, R('income', 'date'), d0, R('income', 'date'), d1)
def INCALL(d0, d1): return 'SUMIFS(%s,%s,">="&%s,%s,"<"&%s)' % (R('income', 'net'), R('income', 'date'), d0, R('income', 'date'), d1)
def SHARE(d0, d1): return 'IFERROR(%s/%s,0)' % (INC(P1, d0, d1), INCALL(d0, d1))
def HH(): return CA('household', 'Household', 'text', '{set:household}', 22)
def N1(): return CA('partner1', 'Partner 1 name', 'text', '{set:partner1}', 14)
def N2(): return CA('partner2', 'Partner 2 name', 'text', '{set:partner2}', 14)
def PH(role, k, label): return CA(k, label, 'text', TL('phone', role), 18)


settings = [
    S('household', 'Household name', 'text', HOUSEHOLD), S('partner1', 'Partner 1 name, shown in messages', 'text', 'Partner 1'), S('partner2', 'Partner 2 name, shown in messages', 'text', 'Partner 2'),
    S('agreed_p1_share', 'Partner 1 agreed share of shared costs', 'pct', AGREED_P1_SHARE), S('custom_p1_share', 'Partner 1 share in a custom split you test', 'pct', 0.55),
    S('share_tol', 'Within this share of the costs counts as on the agreed share', 'pct', 0.05), S('share_months', 'Months of take-home used for the income share', 'int', 6),
    S('settle_day', 'Day of the month by which you settle up', 'int', 5), S('joint_monthly', 'Monthly amount the joint account needs from the partners', 'money', 4800),
    S('emergency_balance', 'Emergency fund balance, type it', 'money', 11800), S('emergency_monthly', 'Monthly deposit into the emergency fund', 'money', 400),
    S('emergency_low', 'Emergency months, low end, a typical range', 'int', EMERGENCY_MONTHS_LOW),
    S('emergency_high', 'Emergency months, high end, a typical range', 'int', EMERGENCY_MONTHS_HIGH),
    S('household_size', 'People in the household sharing costs', 'int', 5), S('report_year', 'Year the kids and member pages report on', 'int', Y),
    S('save_target', 'Share of allowance a child should save', 'pct', 0.30), S('baby_month', 'First month of the new baby plan', 'date', iso(month_start(-2))),
    S('baby_savings', 'Savings set aside for the new baby plan', 'money', 8000), S('monthly_surplus', 'Money left over each month before the baby, type it', 'money', 350),
    S('leave_income', 'Monthly take-home of the partner who takes leave', 'money', 4680),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 team ------------------------------------------------------------------------
tables.append(T('team', 'Team', 'Household members and outside contacts',
    'One row per household member and outside contact: role, phone and e-mail; the messages in this workbook use these phone numbers.', [
    C('member_id', 'Member ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 18), LST('group', 'Group', 'tgroup', 11), C('phone', 'Phone', 'text', 18),
    C('email', 'E-mail', 'text', 26), C('note', 'Note', 'text', 30), C('start', 'Since', 'date', 11)], D.team_d(), 50))
# 2 shared costs ----------------------------------------------------------------
tables.append(T('shared', 'Shared costs', 'Shared Cost Log',
    'Every cost the partners share, one row each: who paid, the agreed share of partner 1 and the split rule; each partner\'s share fills in by itself.', [
    C('shared_id', 'Shared ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    C('description', 'Description', 'text', 24), LST('category', 'Category', 'sharedcat', 20), C('amount', 'Amount', 'money', 11), LST('paid_by', 'Paid by', 'payer', 11),
    C('agreed_p1', 'Agreed share, partner 1', 'pct', 12), LST('split_rule', 'Split rule', 'split', 13),
    CA('p1_share', 'Partner 1 share', 'money', '{col:amount}*{col:agreed_p1}', 12), CA('p2_share', 'Partner 2 share', 'money', '{col:amount}-{col:p1_share}', 12)],
    D.shared_d(), 1200, [A('paid_by', '= ' + P2, 'warn')]))
# 3 settle up ------------------------------------------------------------------------
_SM = '%s,{col:month}' % R('shared', 'month')
tables.append(T('settle', 'Settle up months', 'Settle Up by Month',
    'One row per complete month: who paid what against the agreed share, who owes whom and the running balance carried month to month; type only the date you settle.', [
    C('settle_id', 'Settle ID', 'text', 9, required=True), C('month', 'Month', 'date', 11),
    CA('total', 'Shared total', 'money', 'SUMIFS(%s,%s)' % (R('shared', 'amount'), _SM), 12),
    CA('p1_paid', 'Partner 1 paid', 'money', 'SUMIFS(%s,%s,%s,%s)' % (R('shared', 'amount'), _SM, R('shared', 'paid_by'), P1), 12),
    CA('p2_paid', 'Partner 2 paid', 'money', 'SUMIFS(%s,%s,%s,%s)' % (R('shared', 'amount'), _SM, R('shared', 'paid_by'), P2), 12),
    CA('p1_share', 'Partner 1 share', 'money', 'SUMIFS(%s,%s)' % (R('shared', 'p1_share'), _SM), 12), CA('p2_share', 'Partner 2 share', 'money', '{col:total}-{col:p1_share}', 12),
    CA('diff', 'Partner 2 over (+) or under (-)', 'money', '{col:p2_paid}-{col:p2_share}', 14),
    CA('from_partner', 'From partner', 'text', 'IF(ROUND({col:diff},0)>0,{set:partner1},IF(ROUND({col:diff},0)<0,{set:partner2},""))', 14),
    CA('to_partner', 'To partner', 'text', 'IF(ROUND({col:diff},0)>0,{set:partner2},IF(ROUND({col:diff},0)<0,{set:partner1},""))', 14),
    CA('amount', 'Amount to settle', 'money', 'ROUND(ABS({col:diff}),2)', 12), CA('due_date', 'Settle by', 'date', 'EDATE({col:month},1)+{set:settle_day}-1', 11),
    C('settled_on', 'Settled on', 'date', 11),
    CA('status', 'Status', 'text', 'IF(ROUND({col:diff},0)=0,%s,IF({col:settled_on}>0,%s,IF({col:due_date}<{today},%s,%s)))' % (V('Square'), V('Settled'), V('Overdue'), V('Open')), 11),
    CA('open_diff', 'Open difference', 'money', 'IF({col:settled_on}>0,0,{col:diff})', 12),
    CA('running_balance', 'Running balance owed to partner 2', 'money', 'SUMIFS(%s,%s,"<="&{col:month})' % (R('settle', 'open_diff'), R('settle', 'month')), 16),
    HH(), N1(), N2(), PH('Partner 1', 'p1_phone', 'Partner 1 phone'), PH('Partner 2', 'p2_phone', 'Partner 2 phone'), PH('Bank branch', 'bank_phone', 'Bank branch phone')],
    D.settle_d(), 60, [A('status', '= ' + V('Overdue'), 'bad'), A('status', '= ' + V('Settled'), 'good')]))
# 4 income -------------------------------------------------------------------------------
tables.append(T('income', 'Income', 'Take-home Income by Person',
    'Every paycheck and client payment as take-home pay, one row each; the income share, the lose-one-income test and the new baby plan read from it.', [
    C('income_id', 'Income ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    LST('person', 'Person', 'payer', 11), C('source', 'Source', 'text', 14), C('net', 'Take-home', 'money', 12)], D.income_d(), 600))
# 5 fair split by month ---------------------------------------------------------------
_FM = '%s,{col:month}' % R('shared', 'month')
tables.append(T('fair_split', 'Fair split by month', 'Fair Split by Month',
    'Each month: shared costs, the take-home share of partner 1, what each partner should pay, what each paid and the difference; also the transfer to the joint account on an income share.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('shared_total', 'Shared total', 'money', 'SUMIFS(%s,%s)' % (R('shared', 'amount'), _FM), 12),
    CA('p1_takehome_share', 'Partner 1 take-home share', 'pct', SHARE('EDATE({col:month},1-{set:share_months})', 'EDATE({col:month},1)'), 13),
    CA('p1_share', 'Partner 1 should pay', 'money', 'SUMIFS(%s,%s)' % (R('shared', 'p1_share'), _FM), 12), CA('p2_share', 'Partner 2 should pay', 'money', '{col:shared_total}-{col:p1_share}', 12),
    CA('p1_paid', 'Partner 1 paid', 'money', 'SUMIFS(%s,%s,%s,%s)' % (R('shared', 'amount'), _FM, R('shared', 'paid_by'), P1), 12),
    CA('p2_paid', 'Partner 2 paid', 'money', 'SUMIFS(%s,%s,%s,%s)' % (R('shared', 'amount'), _FM, R('shared', 'paid_by'), P2), 12),
    CA('difference', 'Partner 2 over (+) or under (-)', 'money', '{col:p2_paid}-{col:p2_share}', 14),
    CA('flag', 'On the agreed share', 'text', 'IF(ABS({col:difference})<={set:share_tol}*{col:shared_total},%s,IF({col:difference}>0,%s,%s))' % (V('On share'), V('Partner 2 over'), V('Partner 1 over')), 14),
    CA('p1_by_income', 'Partner 1 pays on an income share', 'money', '{col:shared_total}*{col:p1_takehome_share}', 14),
    CA('p1_transfer', 'Partner 1 joint transfer, income share', 'money', '{set:joint_monthly}*{col:p1_takehome_share}', 14),
    CA('p2_transfer', 'Partner 2 joint transfer, income share', 'money', '{set:joint_monthly}-{col:p1_transfer}', 14),
    HH(), N1(), N2(), PH('Partner 1', 'p1_phone', 'Partner 1 phone'), PH('Partner 2', 'p2_phone', 'Partner 2 phone'), PH('Grandparent', 'member_phone', 'Household member phone')],
    D.fair_split_d(), 60, [A('flag', '= ' + V('Partner 2 over'), 'warn')]))
# 6 split rule comparison -----------------------------------------------------------------
_SW = 'EDATE(%s,-{col:months})' % MS
tables.append(T('split_cmp', 'Split rule comparison', 'Split Rule Comparison',
    'The same shared costs under an income share, an equal split and your custom share, for the last 1, 3, 6 and 12 complete months, against the agreed split now.', [
    C('sc_id', 'Compare ID', 'text', 10, required=True), LST('rule', 'Split rule', 'split', 13), C('months', 'Months back', 'int', 10),
    CA('shared_total', 'Shared total', 'money', 'SUMIFS(%s,%s,">="&%s,%s,"<"&%s)' % (R('shared', 'amount'), R('shared', 'date'), _SW, R('shared', 'date'), MS), 12),
    CA('p1_ratio', 'Partner 1 share', 'pct', 'IF({col:rule}=%s,0.5,IF({col:rule}=%s,{set:custom_p1_share},%s))' % (tok('split', 'Equal'), tok('split', 'Custom'), SHARE(_SW, MS)), 11),
    CA('p1_pays', 'Partner 1 pays', 'money', '{col:shared_total}*{col:p1_ratio}', 12), CA('p2_pays', 'Partner 2 pays', 'money', '{col:shared_total}-{col:p1_pays}', 12),
    CA('p2_now', 'Partner 2 pays on the agreed split', 'money', '{col:shared_total}*(1-{set:agreed_p1_share})', 14),
    CA('difference', 'Partner 2 difference to now', 'money', '{col:p2_pays}-{col:p2_now}', 14)], D.split_cmp_d(), 50))
# 7 monthly transfer to joint -------------------------------------------------------------------
_RATIO = 'IF({col:basis}=%s,{set:agreed_p1_share},IF({col:basis}=%s,%s,IF({col:basis}=%s,0.5,{set:custom_p1_share})))' % (
    tok('tbasis', 'Agreed split'), tok('tbasis', 'Income share'), SHARE('EDATE(%s,-{set:share_months})' % MS, MS), tok('tbasis', 'Equal'))
tables.append(T('transfer_joint', 'Joint transfers', 'Monthly Transfer to the Joint Account',
    'What each partner moves into the joint account each month under the agreed split, an income share, an equal split or a custom share.', [
    LST('partner', 'Partner', 'payer', 12, required=True), LST('basis', 'Basis', 'tbasis', 14),
    CA('transfer', 'Transfer a month', 'money', '{set:joint_monthly}*IF({col:partner}=%s,%s,1-%s)' % (P1, _RATIO, _RATIO), 14)], D.transfer_d(), 50))
# 8 over-paid streak -------------------------------------------------------------------------------
_OM = '%s,{col:month}' % R('shared', 'month')
_CALM = 'SUMPRODUCT(MAX((%s<={col:month})*(%s=0)*%s))' % (R('overpaid', 'month'), R('overpaid', 'over'), R('overpaid', 'month'))
tables.append(T('overpaid', 'Over-paid streak', 'Over-paid Streak',
    'Each month: the share of shared costs partner 2 paid against the agreed share and how many months in a row it was over; the current month counts so far.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('p2_paid_share', 'Partner 2 share paid', 'pct', 'IFERROR(SUMIFS(%s,%s,%s,%s)/SUMIFS(%s,%s),0)' % (R('shared', 'amount'), _OM, R('shared', 'paid_by'), P2, R('shared', 'amount'), _OM), 12),
    CA('agreed_p2', 'Agreed share, partner 2', 'pct', 'IFERROR(1-SUMIFS(%s,%s)/SUMIFS(%s,%s),1-{set:agreed_p1_share})' % (R('shared', 'p1_share'), _OM, R('shared', 'amount'), _OM), 12),
    CA('over_by', 'Partner 2 over (+) or under (-)', 'money', 'SUMIFS(%s,%s,%s,%s)-SUMIFS(%s,%s)' % (R('shared', 'amount'), _OM, R('shared', 'paid_by'), P2, R('shared', 'p2_share'), _OM), 14),
    CA('over', 'Over the agreed share', 'int', 'IF(AND(SUMIFS(%s,%s)>0,{col:p2_paid_share}>{col:agreed_p2}+{set:share_tol}),1,0)' % (R('shared', 'amount'), _OM), 11),
    CA('calm_before', 'Last month on the share', 'date', 'IF({col:over}=1,IF(%s=0,"",%s),"")' % (_CALM, _CALM), 12),
    CA('streak', 'Months in a row over', 'int', 'IF({col:over}=1,IF({col:calm_before}="",COUNTIFS(%s,"<="&{col:month}),(YEAR({col:month})-YEAR({col:calm_before}))*12+MONTH({col:month})-MONTH({col:calm_before})),0)' % R('overpaid', 'month'), 12),
    CA('agreed_p1', 'Agreed share, partner 1', 'pct', '1-{col:agreed_p2}', 12), CA('review_on', 'Review the split on', 'date', '{today}+7', 12),
    HH(), N2(), PH('Partner 2', 'p2_phone', 'Partner 2 phone')], D.overpaid_d(), 60, [A('streak', '>= 2', 'warn'), A('streak', '>= 3', 'bad')]))
# 9 settle up plan -----------------------------------------------------------------------------------
_PW = '%s,">="&EDATE(%s,-{col:months_back}),%s,"<"&%s' % (R('settle', 'month'), MS, R('settle', 'month'), MS)
tables.append(T('settle_plan', 'Settle up plan', 'Settle Up Plan with the Fewest Payments',
    'Net the open months of the last 1 to 12 into one payment: who pays whom, by when, and how many payments and how much money moves if you settled month by month instead.', [
    C('months_back', 'Open months netted', 'int', 11, required=True),
    CA('net', 'Net owed to partner 2', 'money', 'SUMIFS(%s,%s)' % (R('settle', 'open_diff'), _PW), 13),
    CA('from_partner', 'From partner', 'text', 'IF(ROUND({col:net},0)>0,{set:partner1},IF(ROUND({col:net},0)<0,{set:partner2},""))', 14),
    CA('to_partner', 'To partner', 'text', 'IF(ROUND({col:net},0)>0,{set:partner2},IF(ROUND({col:net},0)<0,{set:partner1},""))', 14),
    CA('amount', 'One payment', 'money', 'ROUND(ABS({col:net}),2)', 12),
    CA('due', 'Pay by', 'date', 'IF(DATE(YEAR({today}),MONTH({today}),{set:settle_day})>={today},DATE(YEAR({today}),MONTH({today}),{set:settle_day}),EDATE(DATE(YEAR({today}),MONTH({today}),{set:settle_day}),1))', 11),
    CA('separate_payments', 'Payments month by month', 'int', 'COUNTIFS(%s,">0.5",%s)+COUNTIFS(%s,"<-0.5",%s)' % (R('settle', 'open_diff'), _PW, R('settle', 'open_diff'), _PW), 12),
    CA('separate_money', 'Money moved month by month', 'money', 'SUMIFS(%s,%s,%s,">0.5")-SUMIFS(%s,%s,%s,"<-0.5")' % (R('settle', 'open_diff'), _PW, R('settle', 'open_diff'), R('settle', 'open_diff'), _PW, R('settle', 'open_diff')), 13),
    CA('payments_saved', 'Payments saved by one payment', 'int', 'MAX(0,{col:separate_payments}-IF({col:amount}>0.5,1,0))', 12)], D.settle_plan_d(), 50))
# 10 kids costs -------------------------------------------------------------------------------------
tables.append(T('kids_costs', 'Kids costs', 'Kids Cost Log',
    'Every cost for the children, one row each: child, kind and amount; the child page, the yearly totals and the allowance pages read from it.', [
    C('kid_cost_id', 'Kids cost ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    LST('child', 'Child', 'child', 14), LST('kind', 'Kind', 'kidkind', 14), C('amount', 'Amount', 'money', 11), C('tx_id', 'Payment ID', 'text', 11),
    HH(), PH('Childcare provider', 'provider_phone', 'Childcare provider phone'), PH('School office', 'school_phone', 'School office phone')], D.kids_costs_d(), 1500))
# 11 allowances ---------------------------------------------------------------------------------------
tables.append(T('allowances', 'Allowances', 'Allowance Log',
    'Each weekly allowance paid to a child: the amount, what was saved and who paid; spent, the weekday and the saved share fill in by themselves.', [
    C('allowance_id', 'Allowance ID', 'text', 10, required=True), C('date', 'Date', 'date', 11), CA('month', 'Month', 'date', 'DATE(YEAR({col:date}),MONTH({col:date}),1)', 11),
    LST('child', 'Child', 'kid', 10), C('amount', 'Amount', 'money', 11), C('saved', 'Saved', 'money', 11), CA('spent', 'Spent', 'money', '{col:amount}-{col:saved}', 11),
    LST('paid_by', 'Paid by', 'payer', 11),
    CA('weekday', 'Weekday', 'text', 'CHOOSE(WEEKDAY({col:date},2),{list:wday.monday},{list:wday.tuesday},{list:wday.wednesday},{list:wday.thursday},{list:wday.friday},{list:wday.saturday},{list:wday.sunday})', 11),
    CA('saved_share', 'Saved share', 'pct', 'IF({col:amount}>0,{col:saved}/{col:amount},0)', 10), HH(),
    CA('child_phone', 'Child phone', 'text', 'IFERROR(INDEX(%s,MATCH({col:child}&"*",%s,0))&"","")' % (R('team', 'phone'), R('team', 'name')), 18), PH('Grandparent', 'member_phone', 'Household member phone')],
    D.allowances_d(), 800))
# 12 kids costs by child and year -------------------------------------------------------------------
_KY = '%s,">="&DATE({col:year},1,1),%s,"<="&DATE({col:year},12,31)' % (R('kids_costs', 'date'), R('kids_costs', 'date'))
def _KYK(kind): return 'SUMIFS(%s,%s,{col:child},%s,%s,%s)' % (R('kids_costs', 'amount'), R('kids_costs', 'child'), R('kids_costs', 'kind'), tok('kidkind', kind), _KY)
tables.append(T('kids_year', 'Kids costs by year', 'Kids Costs by Child and Year',
    'Per child and year: childcare, school, activities, clothing, allowance and other costs against the plan you type; next year\'s row is your plan.', [
    C('ky_id', 'Row ID', 'text', 11, required=True), C('year', 'Year', 'int', 8), LST('child', 'Child', 'child', 14), C('plan', 'Plan for the year', 'money', 12),
    CA('childcare', 'Childcare', 'money', _KYK('Childcare'), 11), CA('school', 'School costs', 'money', _KYK('School costs'), 11), CA('activities', 'Activities', 'money', _KYK('Activities'), 11),
    CA('clothing', 'Clothing', 'money', _KYK('Clothing'), 11), CA('allowance', 'Allowance', 'money', _KYK('Allowance'), 11), CA('other', 'Other', 'money', _KYK('Other'), 11),
    CA('total', 'Total', 'money', '{col:childcare}+{col:school}+{col:activities}+{col:clothing}+{col:allowance}+{col:other}', 12),
    CA('plan_to_date', 'Plan to date', 'money', 'IF({col:year}<YEAR({today}),{col:plan},IF({col:year}=YEAR({today}),{col:plan}*({today}-DATE({col:year},1,1)+1)/(DATE({col:year}+1,1,1)-DATE({col:year},1,1)),0))', 12),
    CA('vs_plan', 'Over (+) or under (-) the plan', 'money', '{col:total}-{col:plan_to_date}', 14), HH(), PH('Grandparent', 'member_phone', 'Household member phone')], D.kids_year_d(), 50))
# 13 cost per household member ---------------------------------------------------------------------------
_CY = '%s,">="&DATE({col:year},1,1),%s,"<="&DATE({col:year},12,31)'
_CK = lambda who: 'SUMIFS(%s,%s,%s,%s)' % (R('kids_costs', 'amount'), R('kids_costs', 'child'), who, _CY % (R('kids_costs', 'date'), R('kids_costs', 'date')))
tables.append(T('cost_member', 'Cost per member', 'Cost per Household Member',
    'The yearly cost of each household member: the child\'s own costs plus half of the costs for both children, and an even share of the shared costs.', [
    C('cm_id', 'Row ID', 'text', 11, required=True), LST('member', 'Household member', 'member', 16), C('year', 'Year', 'int', 8),
    CA('kids_share', 'Kids costs', 'money', 'IF(OR({col:member}=%s,{col:member}=%s),%s+0.5*%s,0)' % (tok('member', 'Noa'), tok('member', 'Ike'), _CK('{col:member}'), _CK(BOTH)), 12),
    CA('shared_share', 'Share of shared costs', 'money', 'SUMIFS(%s,%s)/{set:household_size}' % (R('shared', 'amount'), _CY % (R('shared', 'date'), R('shared', 'date'))), 14),
    CA('total', 'Total for the year', 'money', '{col:kids_share}+{col:shared_share}', 13),
    CA('per_month', 'Per month with costs', 'money', 'IFERROR({col:total}/COUNTIFS(%s,">="&DATE({col:year},1,1),%s,"<="&DATE({col:year},12,31),%s,">0"),0)' % (R('fair_split', 'month'), R('fair_split', 'month'), R('fair_split', 'shared_total')), 13),
    CA('name', 'Name', 'text', 'IF({col:member}=%s,{set:partner1},IF({col:member}=%s,{set:partner2},IF({col:member}=%s,%s,IFERROR(INDEX(%s,MATCH({col:member}&"*",%s,0))&"",""))))' % (
        tok('member', 'Partner 1'), tok('member', 'Partner 2'), tok('member', 'Grandparent'), TL('name', 'Grandparent'), R('team', 'name'), R('team', 'name')), 20),
    CA('phone', 'Phone', 'text', 'IF({col:member}=%s,%s,IF({col:member}=%s,%s,IF({col:member}=%s,%s,IFERROR(INDEX(%s,MATCH({col:member}&"*",%s,0))&"",""))))' % (
        tok('member', 'Partner 1'), TL('phone', 'Partner 1'), tok('member', 'Partner 2'), TL('phone', 'Partner 2'), tok('member', 'Grandparent'), TL('phone', 'Grandparent'), R('team', 'phone'), R('team', 'name')), 18),
    HH(), PH('Grandparent', 'member_phone', 'Household member phone')], D.cost_member_d(), 50))
# 14 allowance summary ----------------------------------------------------------------------------------------
_AM = '%s,{col:month},%s,{col:child}' % (R('allowances', 'month'), R('allowances', 'child'))
tables.append(T('allowance_summary', 'Allowance summary', 'Allowance Summary by Month and Child',
    'For each month and child: allowance paid, saved and spent, the saved share and whether the child saves what you hoped.', [
    C('as_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('child', 'Child', 'kid', 10),
    CA('paid', 'Paid', 'money', 'SUMIFS(%s,%s)' % (R('allowances', 'amount'), _AM), 10), CA('saved', 'Saved', 'money', 'SUMIFS(%s,%s)' % (R('allowances', 'saved'), _AM), 10),
    CA('spent', 'Spent', 'money', '{col:paid}-{col:saved}', 10), CA('saved_share', 'Saved share', 'pct', 'IF({col:paid}>0,{col:saved}/{col:paid},0)', 10),
    CA('flag', 'Saving check', 'text', 'IF({col:paid}=0,"",IF({col:saved_share}>={set:save_target},%s,%s))' % (V('Saving well'), V('Ask to save more')), 16),
    HH(), CA('child_phone', 'Child phone', 'text', 'IFERROR(INDEX(%s,MATCH({col:child}&"*",%s,0))&"","")' % (R('team', 'phone'), R('team', 'name')), 18)], D.allowance_summary_d(), 120,
    [A('flag', '= ' + V('Ask to save more'), 'warn')]))
# 15 scenario inputs --------------------------------------------------------------------------------------------
tables.append(T('scenarios', 'Scenario inputs', 'Scenario Inputs',
    'The numbers behind the scenario tests: shares kept, one-off costs, rate changes, mortgage and new baby inputs; change a value and every test reads it.', [
    C('scenario_id', 'Scenario ID', 'text', 11, required=True), LST('scenario', 'Scenario', 'scen', 20), LST('item', 'Item', 'sitem', 32), C('value', 'Value', 'num', 12),
    C('unit', 'Unit', 'text', 10), C('set_on', 'Last set on', 'date', 11)], D.scenarios_d(), 50))
# 16 lose one income ---------------------------------------------------------------------------------------------
_INC1 = '(%s/{set:share_months})' % INC(P1, 'EDATE(%s,-{set:share_months})' % MS, MS)
_INC2 = '(%s/{set:share_months})' % INC(P2, 'EDATE(%s,-{set:share_months})' % MS, MS)
tables.append(T('lose', 'Lose one income', 'Lose One Income',
    'The monthly plan by category with the share you could cut: the gap if one income stops, the cuts that close it and the months your emergency fund covers the rest.', [
    C('category', 'Category', 'text', 24, required=True), LST('group', 'Group', 'group', 15), C('plan', 'Plan a month', 'money', 12), C('cut_share', 'Share you could cut', 'pct', 12),
    CA('cut_amount', 'Cut amount', 'money', 'ROUND({col:plan}*{col:cut_share},2)', 11), CA('new_plan', 'New plan', 'money', '{col:plan}-{col:cut_amount}', 11),
    CA('rank_key', 'Rank key', 'num', '{col:cut_amount}+(100-MATCH({col:category},%s,0))/1000000' % R('lose', 'category'), 11),
    CA('rank_cut', 'Cut rank', 'int', 'COUNTIFS(%s,">"&{col:rank_key})+1' % R('lose', 'rank_key'), 9),
    CA('bigger_cuts', 'Cuts larger than this one', 'money', 'SUMIFS(%s,%s,">"&{col:cut_amount})' % (R('lose', 'cut_amount'), R('lose', 'cut_amount')), 13),
    CA('inc1', 'Partner 1 take-home a month', 'money', _INC1, 13), CA('inc2', 'Partner 2 take-home a month', 'money', _INC2, 13),
    CA('plan_total', 'Plan total', 'money', 'SUM(%s)' % R('lose', 'plan'), 11),
    CA('gap_p1', 'Gap if partner 1 income stops', 'money', '{col:plan_total}-{col:inc2}', 13), CA('gap_p2', 'Gap if partner 2 income stops', 'money', '{col:plan_total}-{col:inc1}', 13),
    CA('cut_total', 'Cuts available', 'money', 'SUM(%s)' % R('lose', 'cut_amount'), 11),
    CA('left_p1', 'Gap left after cuts, partner 1 stops', 'money', 'MAX(0,{col:gap_p1}-{col:cut_total})', 13), CA('left_p2', 'Gap left after cuts, partner 2 stops', 'money', 'MAX(0,{col:gap_p2}-{col:cut_total})', 13),
    CA('months_p1', 'Months of cover, partner 1 stops', 'num', 'IF({col:left_p1}>0,{set:emergency_balance}/{col:left_p1},"")', 13),
    CA('months_p2', 'Months of cover, partner 2 stops', 'num', 'IF({col:left_p2}>0,{set:emergency_balance}/{col:left_p2},"")', 13),
    CA('p1_scn_income', 'Partner 1 income in the scenario', 'money', '{col:inc1}*%s' % SCV('Reduced hours of partner 1'), 13),
    CA('p1_scn_gap', 'Gap in the partner 1 scenario', 'money', '{col:plan_total}-({col:p1_scn_income}+{col:inc2})', 13),
    CA('p2_scn_income', 'Partner 2 income in the scenario', 'money', '{col:inc2}*%s' % SCV('Income of partner 2 kept'), 13),
    CA('p2_scn_gap', 'Gap in the partner 2 scenario', 'money', '{col:plan_total}-({col:inc1}+{col:p2_scn_income})', 13),
    CA('fund_now', 'Emergency fund now', 'money', '{set:emergency_balance}', 12), CA('fund_need', 'Fund for the high end of the range', 'money', 'MAX({col:left_p1},{col:left_p2})*{set:emergency_high}', 14),
    HH(), N1(), N2(), PH('Partner 1', 'p1_phone', 'Partner 1 phone'), PH('Partner 2', 'p2_phone', 'Partner 2 phone'), PH('Tax preparer', 'tax_phone', 'Tax preparer phone')],
    D.lose_d(), 60))
# 17 expense shock ---------------------------------------------------------------------------------------------------
_MA = '((YEAR({col:month})-YEAR(%s))*12+MONTH({col:month})-MONTH(%s))' % (MS, MS)
tables.append(T('expense_shock', 'Expense shock', 'Expense Shock by Month',
    'A one-off cost from Scenario inputs landing in each of the next 12 months: the emergency fund before and after, and the months of essential spending it still covers.', [
    C('month', 'Month', 'date', 11, required=True), CA('cost', 'One-off cost', 'money', SCV('One-off cost'), 12),
    CA('fund_before', 'Emergency fund before', 'money', '{set:emergency_balance}+{set:emergency_monthly}*%s' % _MA, 14), CA('balance_after', 'Emergency fund after', 'money', '{col:fund_before}-{col:cost}', 14),
    CA('months_left', 'Months of essentials left', 'num', 'MAX(0,{col:balance_after})/%s' % NEED(), 13), CA('months_used', 'Months of essentials used', 'num', '{col:cost}/%s' % NEED(), 13),
    HH(), N2(), PH('Partner 2', 'p2_phone', 'Partner 2 phone')], D.expense_shock_d(), 50))
# 18 interest-rate change ------------------------------------------------------------------------------------------------
_PM = lambda rate: 'IF({col:term_months}>0,PMT((%s)/12,{col:term_months},-{col:balance}),{col:balance}*(%s)/12)' % (rate, rate)
tables.append(T('rate_change', 'Rate change', 'Interest-rate Change by Debt',
    'Each debt with its balance and rate, tested with a rise of 1, 2 or 3 points: the new payment (interest only on a card) and the extra cost over a year.', [
    C('rc_id', 'Row ID', 'text', 9, required=True), LST('debt', 'Debt', 'debt', 14), C('balance', 'Balance', 'money', 12), C('rate', 'Rate now', 'pct', 10), C('term_months', 'Months left, 0 on a card', 'int', 12),
    C('points', 'Points added', 'pct', 10), CA('rate_after', 'Rate after', 'pct', '{col:rate}+{col:points}', 10),
    CA('payment_now', 'Payment now', 'money', _PM('{col:rate}'), 12), CA('payment_after', 'Payment after', 'money', _PM('{col:rate_after}'), 12),
    CA('extra_month', 'Extra a month', 'money', '{col:payment_after}-{col:payment_now}', 12), CA('extra_cost_year', 'Extra cost a year', 'money', '12*{col:extra_month}', 12),
    HH(), N1(), PH('Bank branch', 'bank_phone', 'Bank branch phone')], D.rate_change_d(), 50))
# 19 new baby plan -----------------------------------------------------------------------------------------------------------
tables.append(T('new_baby', 'New baby', 'New Baby Plan by Month',
    'Twelve months from the first month of the plan: one-off costs, monthly costs, income lost on leave, the gap after your monthly surplus and the savings left.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('one_off', 'One-off costs', 'money', 'IF({col:month}={set:baby_month},%s,0)' % SCV('One-off costs'), 12),
    CA('monthly', 'Monthly costs', 'money', 'IF({col:month}>={set:baby_month},%s,0)' % SCV('Monthly costs'), 12),
    CA('leave_loss', 'Income lost on leave', 'money', 'IF(AND({col:month}>={set:baby_month},{col:month}<EDATE({set:baby_month},%s)),-%s*{set:leave_income},0)' % (SCV('Months of leave'), SCV('Income change on leave')), 13),
    CA('gap', 'Gap after surplus', 'money', '{col:one_off}+{col:monthly}+{col:leave_loss}-{set:monthly_surplus}', 13),
    CA('cum_gap', 'Gap so far', 'money', 'SUMIFS(%s,%s,"<="&{col:month})' % (R('new_baby', 'gap'), R('new_baby', 'month')), 12),
    CA('savings_left', 'Savings left', 'money', '{set:baby_savings}-{col:cum_gap}', 12), CA('leave_start', 'Leave starts', 'date', '{set:baby_month}', 11),
    HH(), N1(), N2(), PH('Partner 2', 'p2_phone', 'Partner 2 phone'), PH('Payroll office', 'payroll_phone', 'Payroll office phone')], D.new_baby_d(), 50, [A('savings_left', '< 0', 'bad')]))
# 20 mortgage switch -------------------------------------------------------------------------------------------------------------
tables.append(T('mortgage', 'Mortgage switch', 'Mortgage Switch Line by Line',
    'Monthly housing costs now against after a switch, line by line, with the difference a month and a year; type the payment from the Mortgage Switch tool.', [
    C('item', 'Item', 'text', 30, required=True), C('rent_now', 'Now, a month', 'money', 12), C('mortgage_cost', 'After the switch, a month', 'money', 14),
    CA('difference', 'Difference a month', 'money', '{col:mortgage_cost}-{col:rent_now}', 13), CA('yearly_diff', 'Difference a year', 'money', '12*{col:difference}', 13),
    CA('total_diff', 'Total difference a month', 'money', 'SUM(%s)-SUM(%s)' % (R('mortgage', 'mortgage_cost'), R('mortgage', 'rent_now')), 14),
    HH(), N1(), PH('Partner 1', 'p1_phone', 'Partner 1 phone')], D.mortgage_d(), 50))
assert len(tables) == 20
