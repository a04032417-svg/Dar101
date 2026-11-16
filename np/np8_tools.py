"""Nonprofit suite part 8: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np8_lists import *
import np8_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v_} for l, v_ in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def IYN(k, label, yes=True): return IN(k, label, 'list', 'yes' if yes else 'no', list='yesno')
def R(t, c): return '{range:%s.%s}' % (t, c)
YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
JAN1 = 'DATE(YEAR({today}),1,1)'
CURM = 'DATE(YEAR({today}),MONTH({today}),1)'
THIS = tok('yr', 'This year'); LAST = tok('yr', 'Last year'); TWO = tok('yr', 'Two years ago')
def FI(name): return 'SUMIFS(%s,%s,%s)' % (R('forecast_inputs', 'value'), R('forecast_inputs', 'item'), tok('finput', name))
def NOWROW(col): return 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (R('cash', col), R('cash', 'month'), R('cash', 'month'))
FC = lambda c: R('forecast', c)
AVG1 = 'INDEX(%s,1)' % FC('avg_expense')
def FS(col, p): return 'SUMIFS(%s,%s,%s)' % (R('functional', col), R('functional', 'period'), p)
def SH(col, p): return 'IFERROR(%s/%s,0)' % (FS(col, p), FS('total', p))
def MN(x): return 'ROUND(%s,2)' % x
tools = []

# 1 ------------------------------------------------------------ budget against actual by area
BA = lambda c: R('budget_actual', c)
def BAS(col, area=None, extra=''):
    a = '%s,%s,' % (BA('area'), area) if area else ''
    return 'SUMIFS(%s,%s%s,">="&EDATE(%s,-{in:months})%s)' % (BA(col), a, BA('month'), CURM, extra)
DIFF1 = '%s-%s' % (BAS('actual', '{in:area}'), BAS('budget', '{in:area}'))
tools.append(TOOL('ba_tool', 'Budget vs Actual Tool', 'Are we on budget, and where are we over',
    'Pick an area and the months to look back; the budget, the actual cost (shared costs split by their rule) and the share used are shown for the area and for all areas, with the difference of every area.', [
    IL('area', 'Budget area', 'area', 'Fundraising'), I('months', 'Complete months to look back', 3, 'int')], [
    O('Budget of the area', 'money', BAS('budget', '{in:area}')), O('Actual of the area', 'money', BAS('actual', '{in:area}')), O('Difference of the area', 'money', DIFF1),
    O('Share of the budget used', 'pct', 'IFERROR(%s/%s,0)' % (BAS('actual', '{in:area}'), BAS('budget', '{in:area}'))),
    O('Budget of all areas', 'money', BAS('budget')), O('Actual of all areas', 'money', BAS('actual')), O('Difference of all areas', 'money', '%s-%s' % (BAS('actual'), BAS('budget')))] + [
    O('Difference, %s' % a, 'money', '%s-%s' % (BAS('actual', tok('area', a)), BAS('budget', tok('area', a)))) for a in BUDGET_AREAS] + [
    O('Verdict', 'text', 'IF(%s<={set:tolerance}*%s,%s,%s&" "&ROUND(%s,0)&" "&%s&" "&{in:area})' % (DIFF1, BAS('budget', '{in:area}'), v('On budget'), v('Over by'), DIFF1, v('in')))],
    GR('What if', ('Fundraising, 6 months', {'months': 6}), ('Management, 3 months', {'area': '=' + tok('area', 'Management')}), ('Family Food Pantry', {'area': '=' + tok('area', 'Family Food Pantry')}),
       ('Summer Youth Camp, 5 months', {'area': '=' + tok('area', 'Summer Youth Camp'), 'months': 5}), ('Last month only', {'months': 1}))))

# 2 ------------------------------------------------------------ shared cost allocator
PAYW = lambda f, extra='': 'SUMIFS(%s,%s,%s,%s,">="&EDATE(%s,-12),%s,"<"&%s%s)' % (R('pay', 'total'), R('pay', 'function'), tok('function', f), R('pay', 'month'), CURM, R('pay', 'month'), CURM, extra)
PAYALL = 'SUMIFS(%s,%s,">="&EDATE(%s,-12),%s,"<"&%s)' % (R('pay', 'total'), R('pay', 'month'), CURM, R('pay', 'month'), CURM)
HC = lambda f: 'COUNTIFS(%s,%s,%s,EDATE(%s,-1))' % (R('pay', 'function'), tok('function', f), R('pay', 'month'), CURM)
HCALL = 'COUNTIFS(%s,EDATE(%s,-1))' % (R('pay', 'month'), CURM)
OWN = lambda col: 'IFERROR(INDEX(%s,MATCH({in:category},%s,0)),0)' % (R('expense_categories', col), R('expense_categories', 'category'))
TIMEP = {f: 'IFERROR(%s/%s,0)' % (PAYW(f), PAYALL) for f in ('Program', 'Management', 'Fundraising')}
AREAP = {'Program': '{set:area_program}', 'Management': '{set:area_management}', 'Fundraising': '(1-{set:area_program}-{set:area_management})'}
HCP = {f: 'IFERROR(%s/%s,0)' % (HC(f), HCALL) for f in ('Program', 'Management', 'Fundraising')}
OWNP = {'Program': OWN('program_share'), 'Management': OWN('management_share'), 'Fundraising': OWN('fundraising_share')}
def CHOSEN(f): return 'IF({in:rule}=%s,%s,IF({in:rule}=%s,%s,IF({in:rule}=%s,%s,%s)))' % (tok('rule', 'Staff time'), TIMEP[f], tok('rule', 'Floor area'), AREAP[f], tok('rule', 'Headcount'), HCP[f], OWNP[f])
tools.append(TOOL('allocator', 'Shared Cost Allocator', 'Who carries this shared cost, by the rule you choose',
    'Pick a cost category, the amount and a rule: staff time, floor area or headcount use your pay, floor shares and staff count; use and direct take the Expense Categories shares.', [
    IL('category', 'Cost category', 'category', 'Rent and utilities'), I('amount', 'Shared cost amount', 6693), IL('rule', 'Rule', 'rule', 'Floor area')], [
    O('Charged to programs', 'money', '{in:amount}*%s' % CHOSEN('Program')), O('Charged to management', 'money', '{in:amount}*%s' % CHOSEN('Management')), O('Charged to fundraising', 'money', '{in:amount}*%s' % CHOSEN('Fundraising')),
    O('Program share used', 'pct', CHOSEN('Program')), O('Fundraising share used', 'pct', CHOSEN('Fundraising')),
    O('Program share by staff time', 'pct', TIMEP['Program']), O('Program share by floor area', 'pct', AREAP['Program']), O('Program share by headcount', 'pct', HCP['Program']),
    O('Program share set on Expense Categories', 'pct', OWNP['Program']), O('Fundraising amount by staff time', 'money', '{in:amount}*%s' % TIMEP['Fundraising']),
    O('Fundraising amount by headcount', 'money', '{in:amount}*%s' % HCP['Fundraising']), O('Fundraising amount on Expense Categories', 'money', '{in:amount}*%s' % OWNP['Fundraising']),
    O('Verdict', 'text', '%s&" "&ROUND({in:amount},0)&", "&{in:rule}' % v('Rule applied to'))],
    GR('What if', ('Staff time', {'rule': '=' + tok('rule', 'Staff time')}), ('Headcount', {'rule': '=' + tok('rule', 'Headcount')}), ('Insurance by headcount', {'category': '=' + tok('category', 'Insurance'), 'rule': '=' + tok('rule', 'Headcount'), 'amount': 1800}),
       ('Printing by use', {'category': '=' + tok('category', 'Printing and mail'), 'rule': '=' + tok('rule', 'Use'), 'amount': 2100}), ('Double the amount', {'amount': 13386}))))

# 3 ------------------------------------------------------------ program expense share
CHG3 = '(%s-%s)*100' % (SH('program', THIS), SH('program', LAST))
R3 = 'IFERROR(SUMIFS(%s,%s,">="&EDATE(%s,-3),%s,"<"&%s)/SUMIFS(%s,%s,">="&EDATE(%s,-3),%s,"<"&%s),0)' % (R('functional', 'program'), R('functional', 'month'), CURM, R('functional', 'month'), CURM, R('functional', 'total'),
                                                                                                          R('functional', 'month'), CURM, R('functional', 'month'), CURM)
tools.append(TOOL('program_share_tool', 'Program Expense Share', 'Is the share of cost that goes to programs steady',
    'Type how many points of change you accept; the program share this year is set against last year and two years ago from your own history, with the last 3 months.', [
    I('tolerance', 'Points of change you accept', 1.0, 'num')], [
    O('Program share this year', 'pct', SH('program', THIS)), O('Program share last year', 'pct', SH('program', LAST)), O('Program share two years ago', 'pct', SH('program', TWO)),
    O('Change on last year, points', 'num', MN(CHG3)), O('Program share, last 3 months', 'pct', R3), O('Program cost this year', 'money', FS('program', THIS)), O('Total cost this year', 'money', FS('total', THIS)),
    O('Management share this year', 'pct', SH('management', THIS)), O('Fundraising share this year', 'pct', SH('fundraising', THIS)),
    O('Verdict', 'text', 'IF(%s<-{in:tolerance},%s&" "&ROUND(-%s,1)&" "&%s,IF(%s>{in:tolerance},%s&" "&ROUND(%s,1)&" "&%s,%s))' % (CHG3, v('Falling by'), CHG3, v('points'), CHG3, v('Rising by'), CHG3, v('points'), v('Steady')))],
    GR('What if', ('Accept 0.5 points', {'tolerance': 0.5}), ('Accept 2 points', {'tolerance': 2}), ('Accept 5 points', {'tolerance': 5}), ('Accept no change', {'tolerance': 0}))))

# 4 ------------------------------------------------------------ fundraising share alert
INY = 'SUMIFS(%s,%s,%s)' % (R('income_source', 'total'), R('income_source', 'period'), THIS)
R4 = 'IFERROR(SUMIFS(%s,%s,">="&EDATE(%s,-3),%s,"<"&%s)/SUMIFS(%s,%s,">="&EDATE(%s,-3),%s,"<"&%s),0)' % (R('functional', 'fundraising'), R('functional', 'month'), CURM, R('functional', 'month'), CURM, R('functional', 'total'),
                                                                                                          R('functional', 'month'), CURM, R('functional', 'month'), CURM)
tools.append(TOOL('fundraising_alert', 'Fundraising Share Alert', 'Is fundraising taking a bigger share of our cost',
    'Type the points of rise you accept; the fundraising share this year and in the last 3 months is set against last year, and the cost to raise one dollar against your setting.', [
    I('tolerance', 'Points of rise you accept', 1.0, 'num')], [
    O('Fundraising share this year', 'pct', SH('fundraising', THIS)), O('Fundraising share last year', 'pct', SH('fundraising', LAST)), O('Fundraising share, last 3 months', 'pct', R4),
    O('Change on last year, points', 'num', MN('(%s-%s)*100' % (SH('fundraising', THIS), SH('fundraising', LAST)))), O('Fundraising cost this year', 'money', FS('fundraising', THIS)),
    O('Money in this year', 'money', INY), O('Cost to raise one dollar this year', 'num', 'IFERROR(ROUND(%s/%s,3),0)' % (FS('fundraising', THIS), INY)),
    O('Cost to raise one dollar, your setting', 'num', '{set:cost_per_dollar}'), O('Cost to raise one dollar last year', 'num', 'IFERROR(ROUND(%s/SUMIFS(%s,%s,%s),3),0)' % (FS('fundraising', LAST), R('income_source', 'total'), R('income_source', 'period'), LAST)),
    O('Verdict', 'text', 'IF(OR(%s>%s+{in:tolerance}/100,%s>%s+{in:tolerance}/100),%s,%s)' % (SH('fundraising', THIS), SH('fundraising', LAST), R4, SH('fundraising', THIS), v('Rising, review'), v('Steady')))],
    GR('What if', ('Accept 3 points', {'tolerance': 3}), ('Accept 0.5 points', {'tolerance': 0.5}), ('Accept 5 points', {'tolerance': 5}), ('Accept no rise', {'tolerance': 0}))))

# 5 ------------------------------------------------------------ budget builder
ELAPSED = '(MONTH(%s)-1)' % CURM
def NEXT(a, extra): return 'IFERROR(SUMIFS(%s,%s,%s)*12/%s*(1+{in:trend}%s),0)' % (BA('actual'), BA('area'), a, ELAPSED, extra)
TOTN = lambda extra: 'IFERROR(SUM(%s)*12/%s*(1+{in:trend}%s),0)' % (BA('actual'), ELAPSED, extra)
tools.append(TOOL('budget_builder', 'Budget Builder', 'What should next year\'s budget be',
    'Type the trend factor and how far the best and worst cases move it; next year\'s line for each area is this year\'s actual cost, spread over twelve months, times the trend.', [
    I('trend', 'Trend factor, your estimate', 0.04, 'pct'), I('best', 'Best case moves the trend by', -0.02, 'pct'), I('worst', 'Worst case moves the trend by', 0.03, 'pct')], [
    O('Actual cost this year so far', 'money', 'SUM(%s)' % BA('actual'))] + [O('Next year, %s' % a, 'money', NEXT(tok('area', a), '')) for a in BUDGET_AREAS] + [
    O('Next year, base total', 'money', TOTN('')), O('Next year, best case total', 'money', TOTN('+{in:best}')), O('Next year, worst case total', 'money', TOTN('+{in:worst}')),
    O('This year budget, all months', 'money', 'SUMIFS(%s,%s,">="&%s,%s,"<"&DATE(YEAR({today})+1,1,1))' % (R('budget', 'budget'), R('budget', 'month'), JAN1, R('budget', 'month'))),
    O('Verdict', 'text', '%s&" "&ROUND(%s,0)&", "&%s' % (v('Budget'), TOTN(''), v('your estimate')))],
    GR('What if', ('Trend 2 percent', {'trend': 0.02}), ('Trend 6 percent', {'trend': 0.06}), ('Trend 8 percent', {'trend': 0.08}), ('No trend', {'trend': 0.0}))))

# 6 ------------------------------------------------------------ income against budget
def INC6(col): return 'SUMIFS(%s,%s,">="&EDATE(%s,-{in:months}),%s,"<"&%s)' % (R('income_source', col), R('income_source', 'month'), CURM, R('income_source', 'month'), CURM)
DIFF6 = '%s-%s' % (INC6('total'), INC6('budget'))
tools.append(TOOL('income_tool', 'Income vs Budget Tool', 'Is money in ahead of plan or behind',
    'Type the complete months to look back; gifts, grants, events and dues are set against the income budget, with the difference and a verdict.', [
    I('months', 'Complete months to look back', 6, 'int')], [
    O('Gifts', 'money', INC6('gifts')), O('Gifts budget', 'money', INC6('bud_gifts')), O('Grants', 'money', INC6('grants')), O('Grants budget', 'money', INC6('bud_grants')), O('Events', 'money', INC6('events')),
    O('Events budget', 'money', INC6('bud_events')), O('Dues', 'money', INC6('dues')), O('Dues budget', 'money', INC6('bud_dues')), O('Money in', 'money', INC6('total')), O('Income budget', 'money', INC6('budget')),
    O('Difference', 'money', DIFF6), O('Share of the budget', 'pct', 'IFERROR(%s/%s,0)' % (INC6('total'), INC6('budget'))),
    O('Verdict', 'text', 'IF(%s>{set:tolerance}*%s,%s,IF(%s<-{set:tolerance}*%s,%s&" "&ROUND(-(%s),0),%s))' % (DIFF6, INC6('budget'), v('Ahead'), DIFF6, INC6('budget'), v('Behind by'), DIFF6, v('On plan')))],
    GR('What if', ('Last 3 months', {'months': 3}), ('Last 12 months', {'months': 12}), ('Last month', {'months': 1}), ('Last 9 months', {'months': 9}))))

# 7 ------------------------------------------------------------ cash forecast tool
def TERM(k): return 'INDEX(%s,%d)+{in:gifts}*INDEX(%s,%d)-{in:expenses}*INDEX(%s,%d)' % (FC('closing'), k, FC('cum_gifts'), k, FC('cum_exp'), k)
LOW7 = 'MIN(%s)' % ','.join(TERM(k) for k in range(1, 13))
IDX7 = 'MATCH(%s,CHOOSE({1,2,3,4,5,6,7,8,9,10,11,12},%s),0)' % (LOW7, ','.join(TERM(k) for k in range(1, 13)))
tools.append(TOOL('cash_forecast_tool', 'Cash Forecast Tool', 'When is cash lowest in the next 12 months',
    'Type a change in gifts and in expenses; the 12-month forecast (gifts, recurring, pledges, grant instalments, event net, expenses) is rebuilt and the lowest cash month named.', [
    I('gifts', 'Change in gifts on the plan', 0.0, 'pct'), I('expenses', 'Change in expenses on the plan', 0.0, 'pct')], [
    O('Cash now', 'money', NOWROW('closing')), O('Cash after 3 months', 'money', TERM(3)), O('Cash after 6 months', 'money', TERM(6)), O('Cash after 12 months', 'money', TERM(12)),
    O('Lowest cash in the 12 months', 'money', LOW7), O('Lowest cash, month', 'date', 'INDEX(%s,%s)' % (FC('month'), IDX7)),
    O('Free money at the lowest cash', 'money', '%s-%s-%s' % (LOW7, NOWROW('restricted'), NOWROW('designated'))),
    O('Months of reserve at the lowest cash', 'num', 'ROUND((%s-%s-%s)/%s,2)' % (LOW7, NOWROW('restricted'), NOWROW('designated'), AVG1)),
    O('Net for the 12 months', 'money', 'SUM(%s)+{in:gifts}*SUM(%s)-{in:expenses}*SUM(%s)' % (FC('net'), FC('gifts'), FC('expenses'))),
    O('Verdict', 'text', '%s&" "&%s&" "&%s&" "&ROUND(%s,0)' % (v('Cash low in'), MONONLY('INDEX(%s,%s)' % (FC('month'), IDX7)), v('at'), LOW7))],
    GR('What if', ('Gifts down 10 percent', {'gifts': -0.10}), ('Expenses up 5 percent', {'expenses': 0.05}), ('Gifts up 10 percent', {'gifts': 0.10}), ('Both worse', {'gifts': -0.05, 'expenses': 0.05}))))

# 8 ------------------------------------------------------------ lowest cash month
RESMIN = 'MIN(%s)' % FC('reserve_months')
AT8 = lambda col: 'INDEX(%s,MATCH(%s,%s,0))' % (FC(col), RESMIN, FC('reserve_months'))
tools.append(TOOL('lowest_tool', 'Lowest Cash Month Tool', 'Which month is the tightest, and why',
    'Type the band of months above your setting that counts as a watch; the lowest cash, free money and months of reserve are found with their months, and the causes in the tightest month are listed.', [
    I('band', 'Watch band above the setting, months', 0.5, 'num')], [
    O('Lowest closing cash', 'money', 'MIN(%s)' % FC('closing')), O('Lowest closing cash, month', 'date', 'INDEX(%s,MATCH(MIN(%s),%s,0))' % (FC('month'), FC('closing'), FC('closing'))),
    O('Lowest free money', 'money', 'MIN(%s)' % FC('free_money')), O('Lowest months of reserve', 'num', RESMIN), O('Lowest months of reserve, month', 'date', AT8('month')),
    O('Gifts in that month', 'money', AT8('gifts')), O('Grants in that month', 'money', AT8('grants')), O('Expenses in that month', 'money', AT8('expenses')), O('One-off cost in that month', 'money', AT8('one_off')),
    O('Net in that month', 'money', AT8('net')), O('Months under the setting', 'int', 'COUNTIFS(%s,"<"&{set:reserve_months})' % FC('reserve_months')),
    O('Verdict', 'text', 'IF(%s<{set:reserve_months},%s,IF(%s<{set:reserve_months}+{in:band},%s&" "&%s,%s))' % (RESMIN, v('Act now'), RESMIN, v('Watch'), MONTXT(AT8('month')), v('Safe')))],
    GR('What if', ('Band of 0.1', {'band': 0.1}), ('Band of 1 month', {'band': 1.0}), ('Band of 0.25', {'band': 0.25}), ('No band', {'band': 0.0}))))

# 9 ------------------------------------------------------------ reserve months
RM9 = 'ROUND(%s/%s,2)' % (NOWROW('free_money'), NOWROW('avg_monthly_expense'))
tools.append(TOOL('reserve_tool', 'Reserve Months Tool', 'How many months of reserve do we have',
    'Type the months of reserve you want (starting point 3) and the band that counts as at it; free money (cash less restricted and designated money) is divided by the average monthly expense.', [
    I('setting', 'Months of reserve you want, starting point, set your own', RESERVE_MONTHS, 'num'), I('band', 'Band above the setting that counts as at it, months', 0.25, 'num')], [
    O('Free money now', 'money', NOWROW('free_money')), O('Average monthly expense, last 12 months', 'money', NOWROW('avg_monthly_expense')), O('Months of reserve now', 'num', RM9),
    O('Months of reserve a year ago', 'num', 'SUMIFS(%s,%s,EDATE(MAX(%s),-12))' % (R('cash', 'reserve_months'), R('cash', 'month'), R('cash', 'month'))),
    O('Change on a year ago, months', 'num', 'ROUND(%s-SUMIFS(%s,%s,EDATE(MAX(%s),-12)),2)' % (RM9, R('cash', 'reserve_months'), R('cash', 'month'), R('cash', 'month'))),
    O('Free money needed for the setting', 'money', '{in:setting}*%s' % NOWROW('avg_monthly_expense')), O('Free money above or below the setting', 'money', '%s-{in:setting}*%s' % (NOWROW('free_money'), NOWROW('avg_monthly_expense'))),
    O('Restricted money now', 'money', NOWROW('restricted')), O('Designated money now', 'money', NOWROW('designated')), O('Lowest months of reserve in the forecast', 'num', RESMIN),
    O('Verdict', 'text', 'IF(%s>={in:setting}+{in:band},%s,IF(%s>={in:setting},%s,%s))&", "&%s&" "&%s' % (RM9, v('Above'), RM9, v('On the setting'), v('Below'), RM9, v('months')))],
    GR('What if', ('Want 4 months', {'setting': 4.0}), ('Want 3.5 months', {'setting': 3.5}), ('Want 2 months', {'setting': 2.0}), ('Want 6 months', {'setting': 6.0}))))

# 10 ----------------------------------------------------------- reserve date finder
K10 = 'MIN(%s)' % ','.join('IF(INDEX(%s,%d)<{in:setting},%d,99)' % (FC('reserve_months'), k, k) for k in range(1, 13))
BURN = '(SUM(%s)/12)' % FC('net')
tools.append(TOOL('reserve_date', 'Reserve Date Finder', 'When does free money first fall below the reserve setting',
    'Type the months of reserve you want; the 12 forecast months are scanned for the first month below it, and the run-rate months to the setting are worked out from the forecast net.', [
    I('setting', 'Months of reserve you want, starting point, set your own', RESERVE_MONTHS, 'num')], [
    O('Month number of the first month below', 'int', K10), O('First month below the setting', 'date', 'IFERROR(INDEX(%s,%s),"-")' % (FC('month'), K10)),
    O('Months of reserve in that month', 'num', 'IFERROR(INDEX(%s,%s),"-")' % (FC('reserve_months'), K10)), O('Free money in that month', 'money', 'IFERROR(INDEX(%s,%s),"-")' % (FC('free_money'), K10)),
    O('Months under the setting in the 12 months', 'int', 'COUNTIFS(%s,"<"&{in:setting})' % FC('reserve_months')),
    O('Average net a month in the forecast', 'money', BURN), O('Free money above the setting now', 'money', '%s-{in:setting}*%s' % (NOWROW('free_money'), NOWROW('avg_monthly_expense'))),
    O('Months to the setting at the average net, closed form', 'num', 'IF(%s<0,ROUND((%s-{in:setting}*%s)/-%s,1),0)' % (BURN, NOWROW('free_money'), NOWROW('avg_monthly_expense'), BURN)),
    O('Verdict', 'text', 'IF(%s=99,%s,%s&" "&%s)' % (K10, v('Not within 12 months'), v('Below in'), MONTXT('INDEX(%s,%s)' % (FC('month'), K10))))],
    GR('What if', ('Want 2.5 months', {'setting': 2.5}), ('Want 3.2 months', {'setting': 3.2}), ('Want 4 months', {'setting': 4.0}), ('Want 2 months', {'setting': 2.0}))))

# 11 ----------------------------------------------------------- reserve rebuild plan
SHORT11 = 'MAX(0,{in:setting}*%s-MIN(%s))' % (AVG1, FC('free_money'))
tools.append(TOOL('rebuild_plan', 'Reserve Rebuild Plan', 'How much must we save each month to get back to the setting',
    'Type the months of reserve you want and the months you give yourself; the gap at the lowest point of the forecast is divided into equal monthly savings.', [
    I('setting', 'Months of reserve you want, starting point, set your own', RESERVE_MONTHS, 'num'), I('months', 'Months to rebuild in', 6, 'int')], [
    O('Lowest free money in the forecast', 'money', 'MIN(%s)' % FC('free_money')), O('Free money needed for the setting', 'money', '{in:setting}*%s' % AVG1), O('Gap at the lowest point', 'money', SHORT11),
    O('Months of reserve at the lowest point', 'num', RESMIN), O('Saving needed each month', 'money', 'ROUND(%s/{in:months},0)' % SHORT11), O('Saving needed in total', 'money', SHORT11),
    O('Saving as a share of average monthly expense', 'pct', 'IFERROR(%s/{in:months}/%s,0)' % (SHORT11, AVG1)),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&ROUND(%s/{in:months},0)&" "&%s&" "&{in:months}&" "&%s)' % (SHORT11, v('Already at the setting'), v('Save'), SHORT11, v('a month for'), v('months')))],
    GR('What if', ('Rebuild in 3 months', {'months': 3}), ('Rebuild in 12 months', {'months': 12}), ('Want 3.5 months', {'setting': 3.5}), ('Want 4 months in 12', {'setting': 4.0, 'months': 12}))))

# 12 ----------------------------------------------------------- can we afford this
def BAD(s, k): return 'IF({in:months}>%d,IF(INDEX(%s,%s+%d)<{in:setup}+{in:cost}*%d,1,0),0)' % (k, FC('headroom'), s, k, k + 1)
SHORT12 = '+'.join(BAD('{in:start}', k) for k in range(4))
def BADL(s): return '+'.join(BAD(str(s), k) for k in range(4) if s + k <= 12)
F12 = '0'
for _s in range(12, 0, -1): F12 = 'IF(AND(%d>={in:start},%s=0),%d,%s)' % (_s, BADL(_s), _s, F12)
tools.append(TOOL('afford_tool', 'Can We Afford This', 'Can we afford a new hire or program, and when',
    'Type the monthly cost, the set-up cost, the month you would start (1 is next month) and the months of the cost the reserve must cover (1 to 4); each forecast month is tested against your setting.', [
    I('cost', 'Monthly cost', 3000), I('setup', 'Set-up cost', 1500), I('start', 'Start month number', 1, 'int'), I('months', 'Months the reserve must cover (1 to 4)', 3, 'int')], [
    O('Cost for a full year', 'money', '{in:cost}*12+{in:setup}'),
    O('Months funded above the setting', 'int', 'IFERROR(MAX(0,ROUNDDOWN((MIN(%s)-{set:reserve_months}*%s-{in:setup})/{in:cost},0)),0)' % (','.join('IF(%d>={in:start},INDEX(%s,%d),1E9)' % (k, FC('free_money'), k) for k in range(1, 13)), AVG1)),
    O('Lowest months of reserve after the cost starts', 'num', 'IFERROR(ROUND(MIN(%s),2),0)' % ','.join('IFERROR(IF({in:months}>%d,(INDEX(%s,{in:start}+%d)-{in:cost}*%d-{in:setup})/%s,1E9),1E9)' % (k, FC('free_money'), k, k + 1, AVG1) for k in range(4))),
    O('Months under the setting if you start as planned', 'int', SHORT12), O('Earliest start month number', 'int', F12), O('Earliest start month', 'date', 'IFERROR(INDEX(%s,1/(1/(%s))),"-")' % (FC('month'), F12)),
    O('Hire capacity a month on free money now', 'money', 'MAX(0,ROUND((%s-{set:reserve_months}*%s)/12,0))' % (NOWROW('free_money'), NOWROW('avg_monthly_expense'))),
    O('Verdict', 'text', 'IF((%s)=0,%s,IFERROR(%s&" "&%s,%s))' % (SHORT12, v('Yes'), v('Yes after'), MONONLY('INDEX(%s,%s-1)' % (FC('month'), F12)), v('Not yet')))],
    GR('What if', ('Start in month 5', {'start': 5}), ('Cost 1,500 a month', {'cost': 1500}), ('Cost 5,000 a month', {'cost': 5000}), ('Cover 1 month', {'months': 1}), ('Cover 4 months, start 2', {'months': 4, 'start': 2}))))

# 13 ----------------------------------------------------------- hire cost calculator
PAY13 = 'IF({in:rate}>0,{in:rate}*{in:hours}*52/12,{in:salary})'
tools.append(TOOL('hire_cost', 'Hire Cost Calculator', 'What does a hire really cost in a year',
    'Type a monthly salary or an hourly rate and hours a week, the employer cost percentage and the set-up cost; the full monthly and yearly cost is shown against what you spent on pay last year.', [
    I('salary', 'Monthly salary', 3800), I('rate', 'Hourly rate (leave 0 for a salary)', 0), I('hours', 'Hours a week', 0, 'int'), I('employer', 'Employer costs on top of pay', EMPLOYER_COST_PCT, 'pct'), I('setup', 'Set-up cost', 1500),
    I('months', 'Months paid in the year', 12, 'int')], [
    O('Monthly pay', 'money', PAY13), O('Employer cost each month', 'money', '%s*{in:employer}' % PAY13), O('Full monthly cost', 'money', '%s*(1+{in:employer})' % PAY13),
    O('Full cost for the months paid', 'money', '%s*(1+{in:employer})*{in:months}' % PAY13), O('First year cost with the set-up', 'money', '%s*(1+{in:employer})*{in:months}+{in:setup}' % PAY13),
    O('Pay cost last year', 'money', 'SUMIFS(%s,%s,">="&DATE(YEAR({today})-1,1,1),%s,"<="&DATE(YEAR({today})-1,12,1))' % (R('pay', 'total'), R('pay', 'month'), R('pay', 'month'))),
    O('Share added to last year pay cost', 'pct', 'IFERROR(%s*(1+{in:employer})*{in:months}/SUMIFS(%s,%s,">="&DATE(YEAR({today})-1,1,1),%s,"<="&DATE(YEAR({today})-1,12,1)),0)' % (PAY13, R('pay', 'total'), R('pay', 'month'), R('pay', 'month'))),
    O('Hire capacity a month on free money now', 'money', 'MAX(0,ROUND((%s-{set:reserve_months}*%s)/12,0))' % (NOWROW('free_money'), NOWROW('avg_monthly_expense'))),
    O('Verdict', 'text', '%s&" "&ROUND(%s*(1+{in:employer})*{in:months}+{in:setup},0)' % (v('Full yearly cost'), PAY13))],
    GR('What if', ('Hourly 21, 20 hours', {'salary': 0, 'rate': 21, 'hours': 20}), ('Salary 5,100', {'salary': 5100}), ('Employer cost 20 percent', {'employer': 0.20}), ('Six months only', {'months': 6}))))

# 14 ----------------------------------------------------------- scenario tester
SC = lambda col: R('scenarios', col)
SCN = lambda name, col: 'SUMIFS(%s,%s,%s)' % (SC(col), SC('scenario'), tok('scen', name))
INC14 = '{in:gifts}*SUM(%s)+{in:recurring}*SUM(%s)-IF({in:donor}=%s,%s,0)-IF({in:grant}=%s,MAX(%s),0)' % (FC('gifts'), FC('recurring'), YES, FI('Biggest donor giving a year'), YES, FC('grants'))
END14 = 'INDEX(%s,MATCH(MAX(%s),%s,0))+%s-{in:cost}*SUM(%s)' % (FC('closing'), FC('month'), FC('month'), INC14, FC('expenses'))
RES14 = 'ROUND((%s-%s-%s)/%s,2)' % (END14, NOWROW('restricted'), NOWROW('designated'), AVG1)
WORST = 'INDEX(%s,MATCH(MIN(%s),%s,0))' % (SC('scenario'), SC('reserve_months'), SC('reserve_months'))
tools.append(TOOL('scenario_tool', 'Scenario Tester', 'What if we lose a donor, a grant or costs rise',
    'Type your own scenario (changes in gifts, recurring gifts and costs, a lost donor or grant); year-end cash and months of reserve are shown with the worst and best on the Scenarios sheet.', [
    I('gifts', 'Change in gifts', -0.05, 'pct'), I('recurring', 'Change in recurring gifts', 0.0, 'pct'), I('cost', 'Change in costs', 0.08, 'pct'), IYN('donor', 'Lose the biggest donor', False), IYN('grant', 'Lose one grant', False)], [
    O('Income change', 'money', INC14), O('Cost change', 'money', '{in:cost}*SUM(%s)' % FC('expenses')), O('Year-end cash', 'money', END14), O('Months of reserve at year end', 'num', RES14),
    O('Base scenario, months of reserve', 'num', SCN('Base', 'reserve_months')), O('Months of reserve, worst scenario on the sheet', 'num', 'MIN(%s)' % SC('reserve_months')), O('Months of reserve, best scenario on the sheet', 'num', 'MAX(%s)' % SC('reserve_months')),
    O('Scenarios under the setting', 'int', 'COUNTIFS(%s,"<"&{set:reserve_months},%s,"<>")' % (SC('reserve_months'), SC('scenario'))), O('Your scenario against the setting, months', 'num', 'ROUND(%s-{set:reserve_months},2)' % RES14),
    O('Verdict', 'text', '%s&" "&%s&" "&MIN(%s)&" "&%s' % (WORST, v('leaves'), SC('reserve_months'), v('months')))],
    GR('What if', ('Lose the biggest donor', {'donor': '=' + YES, 'gifts': 0, 'cost': 0}), ('Lose one grant', {'grant': '=' + YES, 'gifts': 0, 'cost': 0}), ('Costs up 12 percent', {'gifts': 0, 'cost': 0.12}),
       ('Recurring grows 10 percent', {'gifts': 0, 'recurring': 0.10, 'cost': 0}), ('Everything goes wrong', {'donor': '=' + YES, 'grant': '=' + YES}))))

# 15 ----------------------------------------------------------- sensitivity row
def DELTA(which): return 'IF(%s=%s,SUM(%s),IF(%s=%s,SUM(%s),IF(%s=%s,SUM(%s),IF(%s=%s,-SUM(%s),0))))' % (which, tok('finput', 'Gifts change'), FC('gifts'), which, tok('finput', 'Recurring change'), FC('recurring'),
                                                                                                           which, tok('finput', 'Grants received share'), FC('grants'), which, tok('finput', 'Expenses change'), FC('expenses'))
END15 = '(INDEX(%s,MATCH(MAX(%s),%s,0)))' % (FC('free_money'), FC('month'), FC('month'))
def SENS(j): return 'ROUND((%s+%d*{in:step}*%s)/%s,2)' % (END15, j, DELTA('{in:which}'), AVG1)
def EFF(name): return 'ABS({in:step}*%s)' % DELTA(tok('finput', name))
NAMES15 = ['Gifts change', 'Recurring change', 'Grants received share', 'Expenses change']
MX15 = 'MAX(%s)' % ','.join(EFF(n) for n in NAMES15)
tools.append(TOOL('sensitivity', 'Sensitivity Row', 'Which input moves our reserve the most',
    'Pick an input and a step; year-end months of reserve are shown with the input moved down and up by one and two steps, and the four inputs are ranked by how much a step moves the reserve.', [
    IL('which', 'Input to move', 'finput', 'Expenses change'), I('step', 'Step, share of the plan', 0.05, 'pct')], [
    O('Months of reserve at year end, two steps down', 'num', SENS(-2)), O('Months of reserve at year end, one step down', 'num', SENS(-1)), O('Months of reserve at year end, as planned', 'num', SENS(0)),
    O('Months of reserve at year end, one step up', 'num', SENS(1)), O('Months of reserve at year end, two steps up', 'num', SENS(2))] + [
    O('Cash effect of one step, %s' % n, 'money', EFF(n)) for n in NAMES15] + [
    O('Verdict', 'text', '%s&" "&IF(%s=%s,%s,IF(%s=%s,%s,IF(%s=%s,%s,%s)))' % (v('Most sensitive to'), EFF(NAMES15[3]), MX15, tok('finput', NAMES15[3]), EFF(NAMES15[0]), MX15, tok('finput', NAMES15[0]),
                                                                          EFF(NAMES15[1]), MX15, tok('finput', NAMES15[1]), tok('finput', NAMES15[2])))],
    GR('What if', ('Gifts change', {'which': '=' + tok('finput', 'Gifts change')}), ('Recurring change', {'which': '=' + tok('finput', 'Recurring change')}), ('Grants, 10 points', {'which': '=' + tok('finput', 'Grants received share'), 'step': 0.10}),
       ('Expenses, 10 points', {'step': 0.10}))))

# 16 ----------------------------------------------------------- bank tie-out
BM = 'EDATE(%s,-{in:back})' % CURM
OPEN16 = 'SUMIFS(%s,%s,%s)' % (R('cash', 'opening'), R('cash', 'month'), BM)
IN16 = 'SUMIFS(%s,%s,%s)' % (R('bank', 'money_in'), R('bank', 'month'), BM); OUT16 = 'SUMIFS(%s,%s,%s)' % (R('bank', 'money_out'), R('bank', 'month'), BM)
CL16 = 'SUMIFS(%s,%s,%s)' % (R('cash', 'closing'), R('cash', 'month'), BM)
UN16 = 'COUNTIFS(%s,%s,%s,%s)' % (R('bank', 'month'), BM, R('bank', 'reconciled'), NO)
tools.append(TOOL('bank_tieout', 'Bank Tie-out', 'Does the bank agree with our cash, and what is not matched',
    'Type how many months back to check (0 is this month); the opening cash plus the bank money in less money out is set against the closing cash, and the lines not reconciled are counted.', [
    I('back', 'Months back (0 is this month)', 1, 'int')], [
    O('Opening cash', 'money', OPEN16), O('Bank money in', 'money', IN16), O('Bank money out', 'money', OUT16), O('Expected closing cash', 'money', '%s+%s-%s' % (OPEN16, IN16, OUT16)), O('Closing cash on Cash by Month', 'money', CL16),
    O('Difference', 'money', 'ROUND(%s+%s-%s-%s,2)' % (OPEN16, IN16, OUT16, CL16)), O('Lines not reconciled that month', 'int', UN16), O('Lines not reconciled in all', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (R('bank', 'reconciled'), NO, R('bank', 'bank_id'))),
    O('Oldest line not reconciled', 'date', 'IFERROR(SMALL(%s,1),"-")' % R('bank', 'open_date')), O('Money in not reconciled that month', 'money', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('bank', 'money_in'), R('bank', 'month'), BM, R('bank', 'reconciled'), NO)),
    O('Verdict', 'text', 'IF(AND(ABS(%s+%s-%s-%s)<1,%s=0),%s,%s&" "&%s&" "&%s)' % (OPEN16, IN16, OUT16, CL16, UN16, v('Tied'), v('Check'), UN16, v('lines')))],
    GR('What if', ('This month', {'back': 0}), ('Two months back', {'back': 2}), ('Three months back', {'back': 3}), ('Six months back', {'back': 6}))))

# 17 ----------------------------------------------------------- annual report numbers builder
AS = lambda n: 'IFERROR(IF(INDEX(%s,MATCH(%d,%s,0))="","-",INDEX(%s,MATCH(%d,%s,0))),"-")' % (R('annual_report', 'sentence'), n, R('annual_report', 'no'), R('annual_report', 'sentence'), n, R('annual_report', 'no'))
tools.append(TOOL('annual_builder', 'Annual Report Numbers Builder', 'Are the numbers for the annual report ready',
    'Type the value of one volunteer hour (your setting); each number of the annual report is shown as a plain sentence from Annual Report Numbers, and the items still missing are counted and named.', [
    I('hour', 'Value of one volunteer hour, your setting', VOLUNTEER_HOUR_VALUE)], [
    O('Money in', 'text', AS(1)), O('Gifts', 'text', AS(2)), O('Grants', 'text', AS(3)), O('Money out', 'text', AS(7)), O('Net for the year', 'text', AS(11)), O('Program share of cost', 'text', AS(12)), O('People served', 'text', AS(16)),
    O('Volunteer hours', 'text', AS(17)), O('Donors who gave', 'text', AS(19)), O('Donor retention rate', 'text', AS(20)),
    O('Volunteer time last year, valued', 'money', 'IFERROR(INDEX(%s,MATCH(17,%s,0))*{in:hour},0)' % (R('annual_report', 'typed_last'), R('annual_report', 'no'))),
    O('Items ready', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (R('annual_report', 'status'), v('Ready'), R('annual_report', 'item'))), O('Items missing', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (R('annual_report', 'status'), v('Missing'), R('annual_report', 'item'))),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,%s,%s,"<>")=0,%s,%s&" "&IFERROR(INDEX(%s,MATCH(%s,%s,0)),""))' % (R('annual_report', 'status'), v('Missing'), R('annual_report', 'item'), v('Ready'), v('Missing'), R('annual_report', 'item'), v('Missing'), R('annual_report', 'status')))],
    GR('What if', ('Hour valued at 25', {'hour': 25}), ('Hour valued at 35', {'hour': 35}), ('Hour valued at 20', {'hour': 20}), ('Hour valued at 40', {'hour': 40}))))

# 18 ----------------------------------------------------------- year-end pack checker
PACK = ['Bank statements for every month', 'Payroll summary for the year', 'Grant award letters and reports', 'List of pledges still open', 'Restricted fund balances', 'List of equipment and assets',
        'Insurance policy list', 'Board minutes that approved the budget', 'Gift totals tied to the bank', 'Volunteer hours summary']
NOS = '(%s)' % '+'.join('IF({in:p%d}=%s,1,0)' % (i, NO) for i in range(len(PACK)))
tools.append(TOOL('pack_checker', 'Year-End Pack Checker', 'Does the accountant have everything',
    'Answer yes or no for each paper the accountant needs (ask your accountant what your rules need); the missing ones are counted against what is on file.', [
    IYN('p%d' % i, name, i not in (3, 7)) for i, name in enumerate(PACK)], [
    O('Papers on file', 'int', '%d-%s' % (len(PACK), NOS)), O('Papers missing', 'int', NOS), O('Share on file', 'pct', '(%d-%s)/%d' % (len(PACK), NOS, len(PACK))),
    O('Money out this year, to give the accountant', 'money', 'SUMIFS(%s,%s,">="&%s)' % (R('expenses', 'amount'), R('expenses', 'date'), JAN1)), O('Money in this year, to give the accountant', 'money', 'SUMIFS(%s,%s,">="&%s)' % (R('income_source', 'total'), R('income_source', 'month'), JAN1)),
    O('Bank lines not reconciled', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (R('bank', 'reconciled'), NO, R('bank', 'bank_id'))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s&" "&%s)' % (NOS, v('Complete'), v('Add'), NOS, v('Items missing')))],
    GR('What if', ('All on file', {'p3': '=' + YES, 'p7': '=' + YES}), ('Bank statements missing', {'p0': '=' + NO}), ('Payroll missing too', {'p0': '=' + NO, 'p1': '=' + NO}))))
assert len(tools) == 18, len(tools)
