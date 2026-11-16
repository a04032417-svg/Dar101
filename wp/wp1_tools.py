"""Wedding suite part 1: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp1_lists import *
import wp1_data as D
from wp1_tables import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v_} for l, v_ in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def SI(t, c_, kc, val): return 'SUMIFS(%s,%s,%s)' % (R(t, c_), R(t, kc), val)
def LKUP(t, rc, kc, val): return 'INDEX(%s,MATCH(%s,%s,0))' % (R(t, rc), val, R(t, kc))
def NM(t, c_, rk, k): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&"","")' % (R(t, c_), k, R(t, rk))
def NMV(t, c_, rk, k): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R(t, c_), k, R(t, rk))
def RND(x): return 'ROUND(%s,0)' % x

tools = []
TB = '{set:total_budget}'
FUND_NC = 'SUMIFS(%s,%s,%s)' % (R('funding', 'amount'), R('funding', 'status'), NOTC)
REC = 'SUMIFS(%s,%s,%s)' % (R('funding', 'amount'), R('funding', 'status'), RECV)
PRM = 'SUMIFS(%s,%s,%s)' % (R('funding', 'amount'), R('funding', 'status'), PROM)
def FSRC(*srcs): return '+'.join('SUMIFS(%s,%s,%s,%s,"<>"&%s)' % (R('funding', 'amount'), R('funding', 'source'), s_, R('funding', 'status'), NOTC) for s_ in srcs)

# 1 ------------------------------------------------------------ funding plan check
X1 = '(%s+{in:extra}+{in:gifts_pct}*%s-%s)' % (FUND_OK, FUND_NC, TB)
tools.append(TOOL('funding_check', 'Funding Plan Check', 'Are we funded for the wedding',
    'Type extra money and the share of not confirmed cash gifts to count (never counted until received); confirmed funding is set against the total budget: Funded or Short by.', [
    I('extra', 'Extra money you could add', 0), I('gifts_pct', 'Share of not confirmed cash gifts to count', 0, 'pct')], [
    O('Total budget', 'money', TB), O('Funding received', 'money', REC), O('Funding promised', 'money', PRM), O('Confirmed funding, received plus promised', 'money', FUND_OK),
    O('Cash gifts not confirmed, not counted', 'money', FUND_NC), O('Confirmed funding with your what-if', 'money', '%s+{in:extra}+{in:gifts_pct}*%s' % (FUND_OK, FUND_NC)),
    O('Surplus or gap against the total budget', 'money', X1), O('Funded share of the budget', 'pct', 'IFERROR((%s+{in:extra}+{in:gifts_pct}*%s)/%s,0)' % (FUND_OK, FUND_NC, TB)),
    O('The couple\'s savings, confirmed', 'money', FSRC(SP1, SP2)), O('Family transfers, confirmed', 'money', FSRC(SF1, SF2)),
    O('Verdict', 'text', 'IF(%s>=0,%s&" "&%s&" "&ROUND(%s,0),%s&" "&ROUND(-%s,0))' % (X1, V('Funded'), V('surplus'), X1, V('Short by'), X1))],
    GR('What if', ('As it is', {'extra': 0, 'gifts_pct': 0}), ('Add 500', {'extra': 500}), ('Add 1000', {'extra': 1000}), ('Count half the cash gifts', {'gifts_pct': 0.5}), ('Count all the cash gifts', {'gifts_pct': 1}))))

# 2 ------------------------------------------------------------ priority ranker
S1, S2 = R('pscore', 'score_p1'), R('pscore', 'score_p2')
NG = 'SUMPRODUCT(--(ABS(%s-%s)>={in:gap_set}))' % (S1, S2)
GAPMAX = 'SUMPRODUCT(MAX(ABS(%s-%s)))' % (S1, S2)
GAPAREA = 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0))&"","")' % (R('bands', 'priority_area'), R('bands', 'gap'), R('bands', 'gap'))
tools.append(TOOL('priority_ranker', 'Priority Ranker', 'What matters most to both of us',
    'Type how many points of difference you want flagged; both partners\' scores are averaged and ranked, the areas where you differ are counted and the verdict names the one to talk about first.', [
    I('gap_set', 'Points of difference to flag', 2, 'int')], [
    O('Top priority area', 'text', NM('prank', 'area', 'rank', 1)), O('Its average score', 'num', NMV('prank', 'avg', 'rank', 1)), O('Second priority area', 'text', NM('prank', 'area', 'rank', 2)),
    O('Third priority area', 'text', NM('prank', 'area', 'rank', 3)), O('Lowest priority area', 'text', 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0))&"","")' % (R('prank', 'area'), R('prank', 'rank'), R('prank', 'rank'))),
    O('Areas where you differ by the flagged points or more', 'int', NG), O('Largest difference, points', 'int', GAPMAX), O('Area with the largest difference', 'text', GAPAREA),
    O('Areas you both score 4 or more', 'int', 'SUMPRODUCT((%s>=4)*(%s>=4))' % (S1, S2)),
    O('Average score of all areas', 'num', 'IFERROR(ROUND((SUM(%s)+SUM(%s))/(COUNT(%s)+COUNT(%s)),1),0)' % (S1, S2, S1, S2)),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s&" "&%s)' % (NG, V('Aligned'), V('Talk about'), GAPAREA, V('first')))],
    GR('What if', ('Flag 1 point', {'gap_set': 1}), ('Flag 2 points', {'gap_set': 2}), ('Flag 3 points', {'gap_set': 3}), ('Flag 4 points', {'gap_set': 4}), ('Flag 5 points', {'gap_set': 5}))))

# 3 ------------------------------------------------------------ budget split suggester
BD = R('bands', 'difference'); BCAT = R('bands', 'category')
AMT3 = 'MIN(MAX(%s),-MIN(%s))' % (BD, BD)
tools.append(TOOL('split_suggester', 'Budget Split Suggester', 'Is our budget split sensible',
    'Pick a category and an amount you could move into it; the plan is set against a split built from typical shares and both partners\' priorities, and the verdict says where to move money from and to.', [
    IL('cat', 'Category', 'category', 'Music'), I('move', 'Amount to move into the category', 0)], [
    O('Total budget to split', 'money', TB), O('Typical shares add up to', 'pct', 'SUM(%s)' % R('bands', 'typical_share')), O('Planned in the category', 'money', LKUP('bands', 'planned', 'category', '{in:cat}')),
    O('Typical share of the category', 'pct', LKUP('bands', 'typical_share', 'category', '{in:cat}')), O('Suggested amount for the category', 'money', LKUP('bands', 'suggested', 'category', '{in:cat}')),
    O('Plan less suggested', 'money', LKUP('bands', 'difference', 'category', '{in:cat}')), O('Plan less suggested after your move', 'money', '%s+{in:move}' % LKUP('bands', 'difference', 'category', '{in:cat}')),
    O('Largest plan above the suggestion', 'text', 'INDEX(%s,MATCH(MAX(%s),%s,0))&" "&ROUND(MAX(%s),0)' % (BCAT, BD, BD, BD)),
    O('Largest plan below the suggestion', 'text', 'INDEX(%s,MATCH(MIN(%s),%s,0))&" "&ROUND(MIN(%s),0)' % (BCAT, BD, BD, BD)),
    O('Verdict', 'text', 'IF(%s<0.005*%s,%s,%s&" "&ROUND(%s,0)&" "&%s&" "&INDEX(%s,MATCH(MAX(%s),%s,0))&" "&%s&" "&INDEX(%s,MATCH(MIN(%s),%s,0)))' % (
        AMT3, TB, V('Split fits'), V('Move'), AMT3, V('from'), BCAT, BD, BD, V('to'), BCAT, BD, BD))],
    GR('What if', ('No move', {'move': 0}), ('Move 200 in', {'move': 200}), ('Move 500 in', {'move': 500}), ('Move 1000 in', {'move': 1000}), ('Take 300 out', {'move': -300}))))

# 4 ------------------------------------------------------------ budget against actual
PL4 = SI('budget', 'planned', 'category', '{in:cat}'); CM4 = '(%s+{in:extra})' % SI('budget', 'committed', 'category', '{in:cat}')
VR4 = 'IF(%s=0,0,%s-%s)' % (CM4, CM4, PL4)
tools.append(TOOL('budget_actual', 'Budget against Actual', 'Is this category on budget',
    'Pick a category and type extra committed money to test; planned, committed, paid, still due and the variance are shown, and the verdict says On track, Watch or Over by.', [
    IL('cat', 'Category', 'category', 'Flowers and decor'), I('extra', 'Extra committed money to test', 0)], [
    O('Planned', 'money', PL4), O('Committed, with your what-if', 'money', CM4), O('Paid', 'money', SI('budget', 'paid', 'category', '{in:cat}')),
    O('Still due', 'money', '%s-%s' % (CM4, SI('budget', 'paid', 'category', '{in:cat}'))), O('Variance, committed less planned', 'money', VR4), O('Variance percent', 'pct', 'IF(%s>0,%s/%s,0)' % (PL4, VR4, PL4)),
    O('All categories planned', 'money', 'SUM(%s)' % R('budget', 'planned')), O('All categories committed', 'money', 'SUM(%s)' % R('budget', 'committed')),
    O('All categories paid', 'money', 'SUM(%s)' % R('budget', 'paid')), O('Categories over plan', 'int', 'COUNTIFS(%s,">0")' % R('budget', 'variance')),
    O('Verdict', 'text', 'IF(%s<=0,%s,IF(IF(%s>0,%s/%s,0)<={set:over_pct},%s,%s&" "&ROUND(%s,0)))' % (VR4, V('On track'), PL4, VR4, PL4, V('Watch'), V('Over by'), VR4))],
    GR('What if', ('As it is', {'extra': 0}), ('Add 100', {'extra': 100}), ('Add 500', {'extra': 500}), ('Add 1000', {'extra': 1000}), ('Take 300 out', {'extra': -300}))))

# 5 ------------------------------------------------------------ over-plan ranker
VP = R('budget', 'variance_pct'); VA = R('budget', 'variance'); BC5 = R('budget', 'category')
tools.append(TOOL('overplan_ranker', 'Over-plan Ranker', 'Which category is furthest over plan',
    'Type the share over plan that worries you; the categories are ranked by percent over plan with the amount, and the verdict names the first.', [
    I('min_pct', 'Share over plan that worries you', 0.05, 'pct')], [
    O('Furthest over plan', 'text', 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0))&"","")' % (BC5, VP, VP)), O('Its percent over plan', 'pct', 'MAX(0,MAX(%s))' % VP),
    O('Its amount over plan', 'money', 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0)),0)' % (VA, VP, VP)), O('Second furthest over plan', 'text', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,2),%s,0))&"","")' % (BC5, VP, VP)),
    O('Second one, percent over plan', 'pct', 'MAX(0,LARGE(%s,2))' % VP), O('Categories over plan', 'int', 'COUNTIFS(%s,">0")' % VA), O('Categories over by your share or more', 'int', 'COUNTIFS(%s,">="&{in:min_pct})' % VP),
    O('Total over plan', 'money', 'SUMIFS(%s,%s,">0")' % (VA, VA)), O('Reserve line planned', 'money', SI('budget', 'planned', 'category', RESERVE)),
    O('Reserve left after the overruns', 'money', '%s-SUMIFS(%s,%s,">0")' % (SI('budget', 'planned', 'category', RESERVE), VA, VA)),
    O('Verdict', 'text', 'IF(MAX(%s)<=0,%s,INDEX(%s,MATCH(MAX(%s),%s,0))&" "&%s&" "&ROUND(MAX(%s)*100,0)&" "&%s)' % (VP, V('All lines on track'), BC5, VP, VP, V('is'), VP, V('percent over')))],
    GR('What if', ('Worry at 1%', {'min_pct': 0.01}), ('Worry at 5%', {'min_pct': 0.05}), ('Worry at 10%', {'min_pct': 0.1}), ('Worry at 15%', {'min_pct': 0.15}), ('Worry at 25%', {'min_pct': 0.25}))))

# 6 ------------------------------------------------------------ true budget and reserve
HX = 'SUMIFS(%s,%s,%s)' % (R('hidden', 'expected'), R('hidden', 'status'), EXPECTED)
RES = SI('budget', 'planned', 'category', RESERVE)
TB6 = '(SUM(%s)+{in:extra})' % R('truebud', 'true_budget')
tools.append(TOOL('true_budget', 'True Budget and Reserve', 'What is our true budget and is the reserve enough',
    'Type an extra hidden cost and the hidden-cost share you want to test; the plan plus expected hidden costs plus tips is the true budget, and the verdict compares the reserve with the hidden costs.', [
    I('extra', 'Extra hidden cost to test', 0), I('hidden_pct', 'Hidden costs as a share of spend, typical, edit', HIDDEN_COST_PCT, 'pct')], [
    O('Planned total', 'money', 'SUM(%s)' % R('budget', 'planned')), O('Hidden costs still expected', 'money', HX), O('Hidden costs already paid', 'money', 'SUMIFS(%s,%s,%s)' % (R('hidden', 'expected'), R('hidden', 'status'), tok('hstatus', 'Paid'))),
    O('Planned tips beyond the Tips and fees line', 'money', 'SUM(%s)' % R('truebud', 'planned_tips')), O('True budget, with your extra', 'money', TB6),
    O('True budget over the total budget', 'money', '%s-%s' % (TB6, TB)), O('Reserve line', 'money', RES), O('Reserve less the hidden costs expected', 'money', '%s-%s-{in:extra}' % (RES, HX)),
    O('Typical hidden costs at your share of committed money', 'money', 'ROUND({in:hidden_pct}*SUM(%s),0)' % R('budget', 'committed')), O('Reserve less the typical hidden costs', 'money', '%s-ROUND({in:hidden_pct}*SUM(%s),0)' % (RES, R('budget', 'committed'))),
    O('Verdict', 'text', 'IF(%s>=%s+{in:extra},%s,%s&" "&ROUND(%s+{in:extra}-%s,0))' % (RES, HX, V('Reserve covers'), V('Short by'), HX, RES))],
    GR('What if', ('As it is', {'extra': 0}), ('Add 100 hidden', {'extra': 100}), ('Add 300 hidden', {'extra': 300}), ('Hidden costs at 7%', {'hidden_pct': 0.07}), ('Hidden costs at 12%', {'hidden_pct': 0.12}))))

# 7 ------------------------------------------------------------ next payments due
DI = lambda n: 'SUMIFS(%s,%s,"<>"&%s,%s,"<="&{today}+%s)' % (R('schedule', 'amount_due'), R('schedule', 'status'), PAID, R('schedule', 'due_date'), n)
def NXT(k): return 'IFERROR(INDEX(%s,%d)&" "&ROUND(INDEX(%s,%d),0),"")' % (R('due60', 'vendor'), k, R('due60', 'amount'), k)
OVERDUE = 'SUMIFS(%s,%s,"<>"&%s,%s,"<"&{today})' % (R('schedule', 'amount_due'), R('schedule', 'status'), PAID, R('schedule', 'due_date'))
tools.append(TOOL('next_payments', 'Next Payments', 'What do we have to pay next',
    'Type how many days ahead counts as pay now; unpaid payments due within 30, 60 and 90 days are totalled, the next five are listed and the verdict says Pay now or On time.', [
    I('days', 'Days ahead that count as pay now', 14, 'int')], [
    O('Overdue now', 'money', OVERDUE), O('Due within 30 days, including overdue', 'money', DI(30)), O('Due within 60 days, including overdue', 'money', DI(60)), O('Due within 90 days, including overdue', 'money', DI(90)),
    O('Next payment', 'text', NXT(1)), O('Next payment due date', 'date', 'IFERROR(IF(INDEX(%s,1)=0,"",INDEX(%s,1)),"")' % (R('due60', 'due_date'), R('due60', 'due_date'))),
    O('Days to the next payment', 'int', 'IFERROR(INDEX(%s,1),"")' % R('due60', 'days_left')), O('Second payment', 'text', NXT(2)), O('Third payment', 'text', NXT(3)), O('Fourth payment', 'text', NXT(4)), O('Fifth payment', 'text', NXT(5)),
    O('Verdict', 'text', 'IF(OR(%s>0,IFERROR(INDEX(%s,1),999)<={in:days}),%s&" "&ROUND(%s,0),%s)' % (OVERDUE, R('due60', 'days_left'), V('Pay now'), DI('{in:days}'), V('On time')))],
    GR('What if', ('Pay now within 7 days', {'days': 7}), ('Within 14 days', {'days': 14}), ('Within 30 days', {'days': 30}), ('Within 60 days', {'days': 60}), ('Within 90 days', {'days': 90}))))

# 8 ------------------------------------------------------------ final balance cover check
FS = R('schedule', 'fb_short'); SD = R('schedule', 'short_date')
FIRSTD = 'IFERROR(SMALL(%s,1),"")' % SD
FIRSTS = 'IFERROR(INDEX(%s,MATCH(SMALL(%s,1),%s,0)),0)' % (FS, SD, SD)
SH8 = 'MAX(0,%s-{in:extra})' % FIRSTS
tools.append(TOOL('final_cover', 'Final Balance Cover Check', 'Can we pay every final balance on its date',
    'Type money you could add now; every unpaid final balance is checked against the money set aside on its due date after the payments due before it, and the verdict says Covered or Short by.', [
    I('extra', 'Money you could add now', 0)], [
    O('Money set aside now', 'money', CASH_NOW), O('Final balances still unpaid', 'int', 'COUNTIFS(%s,%s,%s,"<>"&%s,%s,"<>")' % (R('schedule', 'kind'), FB, R('schedule', 'status'), PAID, R('schedule', 'pay_id'))),
    O('Total of the unpaid final balances', 'money', 'SUMIFS(%s,%s,%s,%s,"<>"&%s)' % (R('schedule', 'amount_due'), R('schedule', 'kind'), FB, R('schedule', 'status'), PAID)),
    O('Final balances covered', 'int', 'COUNTIFS(%s,"<=0")' % FS), O('Final balances not covered', 'int', 'COUNTIFS(%s,">0")' % FS),
    O('First balance not covered, due date', 'date', FIRSTD), O('First balance not covered, vendor', 'text', 'IFERROR(INDEX(%s,MATCH(SMALL(%s,1),%s,0))&"","")' % (R('schedule', 'vendor'), SD, SD)),
    O('Its amount due', 'money', 'IFERROR(INDEX(%s,MATCH(SMALL(%s,1),%s,0)),0)' % (R('schedule', 'amount_due'), SD, SD)),
    O('Unpaid payments due before it', 'money', 'IFERROR(SUMIFS(%s,%s,"<>"&%s,%s,"<"&SMALL(%s,1)),0)' % (R('schedule', 'amount_due'), R('schedule', 'status'), PAID, R('schedule', 'due_date'), SD)),
    O('Shortfall after your money', 'money', SH8), O('Verdict', 'text', 'IF(%s>0,%s&" "&ROUND(%s,0),%s)' % (SH8, V('Short by'), SH8, V('Covered')))],
    GR('What if', ('As it is', {'extra': 0}), ('Add 500', {'extra': 500}), ('Add 1000', {'extra': 1000}), ('Add 1500', {'extra': 1500}), ('Add 2000', {'extra': 2000}))))

# 9 ------------------------------------------------------------ cash needed by month
CL = R('cash', 'ahead'); CM = R('cash', 'month')
tools.append(TOOL('cash_by_month', 'Cash Needed by Month', 'Will we have the cash each month',
    'Type money you could add now; payments due each month are set against the savings, family transfers and money set aside, and the verdict shows the lowest point and how much to move.', [
    I('add_now', 'Money you could add now', 0)], [
    O('Money set aside now', 'money', CASH_NOW), O('Payments out this month, paid and still due', 'money', NMV('cash', 'payments_out', 'month', MS)),
    O('Money coming in over the next 3 months', 'money', 'SUMIFS(%s,%s,">"&%s,%s,"<="&EDATE(%s,3))' % (R('cash', 'funding_in'), CM, MS, CM, MS)),
    O('Closing cash this month, with your money', 'money', '%s+{in:add_now}' % NMV('cash', 'closing', 'month', MS)), O('Lowest month-end cash, with your money', 'money', 'MIN(%s)+{in:add_now}' % CL),
    O('Month of the lowest cash', 'date', 'IFERROR(INDEX(%s,MATCH(MIN(%s),%s,0)),"")' % (CM, CL, CL)), O('First month below your floor, before your money', 'date', 'IFERROR(SMALL(%s,1),"")' % R('cash', 'neg_month')),
    O('Months below your floor, with your money', 'int', 'COUNTIFS(%s,"<"&({set:cash_floor}-{in:add_now}),%s,"<>")' % (CL, CM)),
    O('Funding still promised', 'money', PRM), O('Payments still to make', 'money', UNPAID_DUE), O('Cash left after everything', 'money', '%s+%s-%s+{in:add_now}' % (CASH_NOW, PRM, UNPAID_DUE)),
    O('Verdict', 'text', 'IF(MIN(%s)+{in:add_now}>={set:cash_floor},%s,%s&" "&ROUND({set:cash_floor}-MIN(%s)-{in:add_now},0))' % (CL, V('Cash stays positive'), V('Negative, move'), CL))],
    GR('What if', ('As it is', {'add_now': 0}), ('Add 500', {'add_now': 500}), ('Add 1000', {'add_now': 1000}), ('Add 1500', {'add_now': 1500}), ('Add 2500', {'add_now': 2500}))))

# 10 ----------------------------------------------------------- payment mover
MS_ = R('schedule', 'mover_score')
def TOPS(col, k): return 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),0)' % (R('schedule', col), MS_, k, MS_)
def TOPT(col, k): return 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0))&"","")' % (R('schedule', col), MS_, k, MS_)
SHORT10 = 'MAX(0,{set:cash_floor}-MIN(%s))' % CL
tools.append(TOOL('payment_mover', 'Payment Mover', 'Which payment could we ask to move',
    'Type how many days later a vendor may let a payment move; unpaid payments due by the first short month are ranked by amount and ease, and the verdict names the one to ask first.', [
    I('days', 'Days later a payment may move, ask each vendor', 30, 'int')], [
    O('First month below your floor', 'date', 'IFERROR(SMALL(%s,1),"")' % R('cash', 'neg_month')), O('Shortfall at the lowest point', 'money', SHORT10),
    O('Best payment to move, vendor', 'text', TOPT('vendor', 1)), O('Best payment to move, kind', 'text', TOPT('kind', 1)), O('Its amount', 'money', TOPS('amount_due', 1)),
    O('Its due date', 'date', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,1),%s,0)),"")' % (R('schedule', 'due_date'), MS_, MS_)), O('Its date if moved', 'date', 'IFERROR(INDEX(%s,MATCH(LARGE(%s,1),%s,0))+{in:days},"")' % (R('schedule', 'due_date'), MS_, MS_)),
    O('Second payment to move, vendor', 'text', TOPT('vendor', 2)), O('Second payment amount', 'money', TOPS('amount_due', 2)), O('Moving the top two frees', 'money', '%s+%s' % (TOPS('amount_due', 1), TOPS('amount_due', 2))),
    O('Still short after moving the top two', 'money', 'MAX(0,%s-%s-%s)' % (SHORT10, TOPS('amount_due', 1), TOPS('amount_due', 2))),
    O('Verdict', 'text', 'IF(%s<=0,%s,%s&" "&%s&" "&%s&" "&%s)' % (SHORT10, V('Nothing to move'), V('Ask'), TOPT('vendor', 1), V('to move'), TOPT('kind', 1)))],
    GR('What if', ('Move 14 days', {'days': 14}), ('Move 30 days', {'days': 30}), ('Move 45 days', {'days': 45}), ('Move 60 days', {'days': 60}), ('Move 90 days', {'days': 90}))))

# 11 ----------------------------------------------------------- cut guests scenario
H1 = 'MAX(0,%s-{in:cut})' % H0
tools.append(TOOL('cut_guests', 'Cut Guests Scenario', 'What do we save if we cut guests',
    'Type how many guests to remove; per-guest lines scale, the minimum guarantee and table rounding hold, fixed lines stay, and the verdict gives the saving and cost per guest.', [
    I('cut', 'Guests to remove', 10, 'int')], [
    O('Headcount after the cut', 'int', H1), O('Tables needed', 'int', 'ROUNDUP(%s/{set:table_size},0)' % H1), O('Guests the caterer charges for', 'int', BILLED(H1)),
    O('Catering after the cut', 'money', RND('IFERROR(%s/%s*%s,0)' % (CAT0, BILLED(H0), BILLED(H1)))), O('Other per-guest lines after the cut', 'money', RND('IFERROR((%s-%s)/%s*%s,0)' % (PG0, CAT0, SEATS(H0), SEATS(H1)))),
    O('Fixed lines, they stay', 'money', RND('%s-%s' % (EXP_TOTAL, PG0))), O('Total cost after the cut', 'money', RND(TOTAL_AT(H1))), O('Saving', 'money', RND('%s-%s' % (EXP_TOTAL, TOTAL_AT(H1)))),
    O('Cost per guest after the cut', 'money', 'IF(%s>0,ROUND(%s/%s,0),0)' % (H1, TOTAL_AT(H1), H1)), O('Guests you still pay for beyond the cut', 'int', '%s-%s' % (BILLED(H1), H1)),
    O('Verdict', 'text', '%s&" "&ROUND(%s-%s,0)&", "&%s&" "&IF(%s>0,ROUND(%s/%s,0),0)' % (V('Saves'), EXP_TOTAL, TOTAL_AT(H1), V('cost per guest'), H1, TOTAL_AT(H1), H1))],
    GR('What if', ('Cut 5', {'cut': 5}), ('Cut 10', {'cut': 10}), ('Cut 20', {'cut': 20}), ('Cut 30', {'cut': 30}), ('Cut 40', {'cut': 40}))))

# 12 ----------------------------------------------------------- move the date scenario
OT = R('dates', 'option_total'); DO = R('dates', 'option')
A_TOT = SI('dates', 'quote', 'option', OPT_A); BEST = '(%s-MIN(%s)-{in:change})' % (A_TOT, OT)
tools.append(TOOL('move_date', 'Move the Date Scenario', 'Would another date save us money',
    'Pick a date option and type what moving your bookings would cost; the quotes on each date are totalled against your current date, the lead times are checked, and the verdict names the best date.', [
    IL('opt', 'Date option', 'dopt', 'Option B: a Friday, three weeks later'), I('change', 'Cost of moving your bookings, your estimate', 300)], [
    O('Total on your current date', 'money', A_TOT), O('Total on the chosen date', 'money', SI('dates', 'quote', 'option', '{in:opt}')), O('Difference against your current date', 'money', '%s-%s' % (A_TOT, SI('dates', 'quote', 'option', '{in:opt}'))),
    O('Saving after the cost of moving', 'money', '%s-%s-{in:change}' % (A_TOT, SI('dates', 'quote', 'option', '{in:opt}'))), O('Days to the chosen date', 'int', 'IFERROR(%s,0)' % LKUP('dates', 'days_to', 'option', '{in:opt}')),
    O('Months to the chosen date', 'num', 'IFERROR(%s,0)' % LKUP('dates', 'months_to', 'option', '{in:opt}')),
    O('Vendors whose lead time you should check', 'int', 'COUNTIFS(%s,{in:opt},%s,%s)' % (DO, R('dates', 'lead_flag'), V('Check lead time'))),
    O('Cheapest option', 'text', 'IFERROR(INDEX(%s,MATCH(MIN(%s),%s,0))&"","")' % (DO, OT, OT)), O('Best saving after the cost of moving', 'money', BEST),
    O('Verdict', 'text', 'IF(%s>0,%s&" "&INDEX(%s,MATCH(MIN(%s),%s,0))&" "&%s&" "&ROUND(%s,0),%s)' % (BEST, V('Best date'), DO, OT, OT, V('saving'), BEST, V('Keep your date')))],
    GR('What if', ('Moving costs nothing', {'change': 0}), ('Moving costs 300', {'change': 300}), ('Moving costs 600', {'change': 600}), ('Moving costs 900', {'change': 900}), ('Moving costs 1500', {'change': 1500}))))

# 13 ----------------------------------------------------------- budget rebalancer
OVER13 = 'MAX(0,%s-%s)' % (SI('budget', 'committed', 'category', '{in:over}'), SI('budget', 'planned', 'category', '{in:over}'))
def ROOM(k): return '%s*{in:take_pct}' % NMV('rebal', 'room', 'rank', k)
A1 = 'MIN(%s,%s)' % (OVER13, ROOM(1)); A2 = 'MIN(%s-%s,%s)' % (OVER13, A1, ROOM(2)); A3 = 'MIN(%s-%s-%s,%s)' % (OVER13, A1, A2, ROOM(3))
TOT13 = '(%s+%s+%s)' % (A1, A2, A3)
tools.append(TOOL('rebalancer', 'Budget Rebalancer', 'How do we cover a line that runs over',
    'Pick the category that is over and the share of each other category\'s free room you will take; the most flexible categories are used in order and the verdict says Balanced or Still over by.', [
    IL('over', 'Category that is over', 'category', 'Flowers and decor'), I('take_pct', 'Share of each free room you will take', 0.5, 'pct')], [
    O('Amount over plan', 'money', OVER13), O('First category to take from', 'text', NM('rebal', 'category', 'rank', 1)), O('Take from it', 'money', RND(A1)),
    O('Second category to take from', 'text', NM('rebal', 'category', 'rank', 2)), O('Take from it', 'money', RND(A2)), O('Third category to take from', 'text', NM('rebal', 'category', 'rank', 3)),
    O('Take from it', 'money', RND(A3)), O('Total covered', 'money', RND(TOT13)), O('Still over by', 'money', RND('%s-%s' % (OVER13, TOT13))), O('Share of the overrun covered', 'pct', 'IF(%s>0,%s/%s,1)' % (OVER13, TOT13, OVER13)),
    O('Verdict', 'text', 'IF(%s-%s<0.5,%s,%s&" "&ROUND(%s-%s,0))' % (OVER13, TOT13, V('Balanced'), V('Still over by'), OVER13, TOT13))],
    GR('What if', ('Take a quarter', {'take_pct': 0.25}), ('Take a third', {'take_pct': 0.33}), ('Take half', {'take_pct': 0.5}), ('Take three quarters', {'take_pct': 0.75}), ('Take all of it', {'take_pct': 1}))))

# 14 ----------------------------------------------------------- cost per guest verdict
FIX14 = '(%s-%s)' % (EXP_TOTAL, PG0); RATE14 = 'IFERROR(%s/%s,0)' % (PG0, H0)
TOT14 = '(%s+%s*{in:guests})' % (FIX14, RATE14); CPG14 = 'IF({in:guests}>0,%s/{in:guests},0)' % TOT14
tools.append(TOOL('cost_per_guest', 'Cost per Guest Verdict', 'Are we on target for cost per guest',
    'Type your headcount and the cost per guest you aim for; fixed lines and the per-guest lines are costed at that headcount, and the verdict says On target or how far above.', [
    I('guests', 'Headcount to cost', 118, 'int'), I('target', 'Cost per guest you aim for, your own number', COST_PER_GUEST_TARGET)], [
    O('Fixed cost, it does not change with guests', 'money', RND(FIX14)), O('Cost of one more guest', 'num', 'ROUND(%s,2)' % RATE14), O('Total at your headcount', 'money', RND(TOT14)),
    O('Cost per guest', 'money', 'ROUND(%s,0)' % CPG14), O('Your target', 'money', '{in:target}'), O('Cost per guest less your target', 'money', 'ROUND(%s-{in:target},0)' % CPG14),
    O('A typical starting value, not a fact about your area', 'money', '{set:cpg_benchmark}'), O('Cost per guest less the typical starting value', 'money', 'ROUND(%s-{set:cpg_benchmark},0)' % CPG14),
    O('Headcount at which you hit your target', 'int', 'IF({in:target}>%s,ROUND(%s/({in:target}-%s),0),"")' % (RATE14, FIX14, RATE14)),
    O('Verdict', 'text', 'IF(%s<={in:target},%s,ROUND(%s-{in:target},0)&" "&%s)' % (CPG14, V('On target'), CPG14, V('above')))],
    GR('What if', ('100 guests', {'guests': 100}), ('110 guests', {'guests': 110}), ('118 guests', {'guests': 118}), ('130 guests', {'guests': 130}), ('150 guests', {'guests': 150}))))

# 15 ----------------------------------------------------------- base best worst
def T15(k): return 'ROUND(%s,0)' % TOTAL_AT('{in:%s}' % k)
def C15(k): return 'IF({in:%s}>0,ROUND(%s/{in:%s},0),0)' % (k, TOTAL_AT('{in:%s}' % k), k)
tools.append(TOOL('scenarios', 'Base, Best and Worst Cost', 'What if fewer or more guests come',
    'Type a low, a likely and a high headcount (your estimates); the total and the cost per guest are shown at each, with the funding confirmed so far set against the worst case.', [
    I('low', 'Low headcount, the Best case', 100, 'int'), I('likely', 'Likely headcount, the Base case', 118, 'int'), I('high', 'High headcount, the Worst case', 135, 'int')], [
    O('Best case total', 'money', T15('low')), O('Base case total', 'money', T15('likely')), O('Worst case total', 'money', T15('high')), O('Best case cost per guest', 'money', C15('low')),
    O('Base case cost per guest', 'money', C15('likely')), O('Worst case cost per guest', 'money', C15('high')), O('Spread between worst and best', 'money', '%s-%s' % (T15('high'), T15('low'))),
    O('Confirmed funding less the worst case', 'money', '%s-%s' % (FUND_OK, T15('high'))), O('Reserve line', 'money', RES),
    O('Verdict', 'text', '%s&" "&%s' % (V('Worst case'), T15('high')))],
    GR('What if', ('90, 110, 125', {'low': 90, 'likely': 110, 'high': 125}), ('100, 118, 135', {'low': 100, 'likely': 118, 'high': 135}), ('105, 118, 130', {'low': 105, 'likely': 118, 'high': 130}),
       ('100, 120, 150', {'low': 100, 'likely': 120, 'high': 150}), ('80, 100, 118', {'low': 80, 'likely': 100, 'high': 118}))))

# 16 ----------------------------------------------------------- tips planner
FLATT = 'SUMIFS(%s,%s,%s,%s,%s)' % (R('tips', 'flat'), R('tips', 'basis'), FLAT, R('tips', 'gratuity_included'), NO)
PCTT = 'ROUND(SUMPRODUCT((%s=%s)*(%s=%s)*%s)*{in:pct},0)' % (R('tips', 'basis'), PCT, R('tips', 'gratuity_included'), NO, R('tips', 'bill'))
TOT16 = '(%s+%s+{in:bonus})' % (FLATT, PCTT); TF16 = SI('budget', 'planned', 'category', TIPSFEES)
tools.append(TOOL('tips_planner', 'Tips Planner', 'What do tips add to the budget',
    'Type the tip percent and any extra envelope (tips are optional and vary by market); flat and percent tips are totalled and the verdict says what to add to the true budget.', [
    I('pct', 'Tip percent for percent lines, optional, typical, edit', TIP_PCT, 'pct'), I('bonus', 'Extra envelope, your own number', 0)], [
    O('Flat tips', 'money', FLATT), O('Percent tips at your percent', 'money', PCTT), O('Tips total, with your extra envelope', 'money', RND(TOT16)), O('Tips and fees line planned', 'money', TF16),
    O('Tips beyond that line', 'money', RND('MAX(0,%s-%s)' % (TOT16, TF16))), O('Tips total in the Tips sheet', 'money', 'SUM(%s)' % R('tips', 'planned_tip')), O('Vendors with a gratuity already included', 'int', 'COUNTIFS(%s,%s)' % (R('tips', 'gratuity_included'), YES)),
    O('Envelopes still to prepare', 'int', 'COUNTIFS(%s,">0",%s,%s)' % (R('tips', 'planned_tip'), R('tips', 'envelope_ready'), NO)), O('Largest envelope', 'money', 'MAX(%s)' % R('tips', 'planned_tip')),
    O('Verdict', 'text', '%s&" "&ROUND(%s,0)&", "&IF(%s>%s,%s&" "&ROUND(%s-%s,0)&" "&%s,%s)' % (V('Tips total'), TOT16, TOT16, TF16, V('add'), TOT16, TF16, V('to the true budget'), V('inside your tips line')))],
    GR('What if', ('Percent at 10%', {'pct': 0.10}), ('Percent at 15%', {'pct': 0.15}), ('Percent at 18%', {'pct': 0.18}), ('Percent at 20%', {'pct': 0.2}), ('Percent at 18% and an extra 100', {'pct': 0.18, 'bonus': 100}))))

# 17 ----------------------------------------------------------- settle-up
TP17 = 'SUM(%s)' % R('payments', 'amount')
def AGR(t): return 'SUMIFS(%s,%s,%s)' % (R('settle', 'agreed'), R('settle', 'payer'), t)
def PDD(t): return 'SUMIFS(%s,%s,%s)' % (R('settle', 'paid'), R('settle', 'payer'), t)
def BAL(t): return '(%s-%s)' % (PDD(t), AGR(t))
BC_, B1_, B2_ = BAL(PC), BAL(P1F), BAL(P2F)
MINB = 'MIN(%s,%s,%s)' % (BC_, B1_, B2_); MAXB = 'MAX(%s,%s,%s)' % (BC_, B1_, B2_)
DEBT = 'IF(AND(%s<=%s,%s<=%s),%s,IF(%s<=%s,%s,%s))' % (BC_, B1_, BC_, B2_, PC, B1_, B2_, P1F, P2F); CRED = 'IF(AND(%s>=%s,%s>=%s),%s,IF(%s>=%s,%s,%s))' % (BC_, B1_, BC_, B2_, PC, B1_, B2_, P1F, P2F)
AMT17 = 'MIN(-%s,%s)' % (MINB, MAXB)
tools.append(TOOL('settle_up', 'Settle-up between Payers', 'Who owes whom',
    'Type the difference below which you call it settled; each payer\'s agreed share of everything paid is set against what they actually paid, and the verdict says who owes whom.', [
    I('tol', 'Differences below this count as settled', 5)], [
    O('Total paid so far', 'money', TP17), O('Agreed share of the couple', 'money', AGR(PC)), O('Agreed share of partner 1 family', 'money', AGR(P1F)),
    O('Agreed share of partner 2 family', 'money', AGR(P2F)), O('Paid by the couple', 'money', PDD(PC)), O('Paid by partner 1 family', 'money', PDD(P1F)), O('Paid by partner 2 family', 'money', PDD(P2F)),
    O('Couple paid more (or less) than agreed', 'money', BC_), O('Partner 1 family paid more (or less) than agreed', 'money', B1_), O('Partner 2 family paid more (or less) than agreed', 'money', B2_),
    O('Verdict', 'text', 'IF(%s-%s<{in:tol},%s,%s&" "&%s&" "&%s&" "&ROUND(%s,0))' % (MAXB, MINB, V('Settled'), DEBT, V('owes'), CRED, AMT17))],
    GR('What if', ('Settled below 1', {'tol': 1}), ('Settled below 5', {'tol': 5}), ('Settled below 50', {'tol': 50}), ('Settled below 500', {'tol': 500}), ('Settled below 3000', {'tol': 3000}))))

# 18 ----------------------------------------------------------- savings pace
GOAL18 = 'IF({in:goal_true}=1,SUM(%s),%s)' % (R('truebud', 'true_budget'), TB)
GAP18 = 'MAX(0,%s-%s-{in:gifts_pct}*%s)' % (GOAL18, FUND_OK, FUND_NC)
MON18 = 'IF(COUNT(%s)=0,1,MAX(1,(MAX(%s)-{today})/30.4))' % (R('schedule', 'due_date'), R('schedule', 'due_date'))
tools.append(TOOL('savings_pace', 'Savings Pace', 'How much more must we save each month',
    'Type 1 to fund the true budget and the share of not confirmed gifts to count; the gap is spread over the months to the last payment: On pace or Save more a month.', [
    I('goal_true', 'Fund the true budget (1) or the total budget (0)', 0, 'int'), I('gifts_pct', 'Share of not confirmed cash gifts to count', 0, 'pct')], [
    O('Budget to fund', 'money', GOAL18), O('Confirmed funding', 'money', FUND_OK), O('Gap to close', 'money', GAP18),
    O('Last payment date', 'date', 'IF(COUNT(%s)=0,"",MAX(%s))' % (R('schedule', 'due_date'), R('schedule', 'due_date'))), O('Months to the last payment', 'num', 'ROUND(%s,1)' % MON18),
    O('Extra saving needed a month', 'money', 'ROUND(%s/%s,0)' % (GAP18, MON18)), O('Savings promised a month on average', 'money', 'ROUND((%s)/%s,0)' % (
        'SUMIFS(%s,%s,%s,%s,%s)+SUMIFS(%s,%s,%s,%s,%s)' % (R('funding', 'amount'), R('funding', 'source'), SP1, R('funding', 'status'), PROM, R('funding', 'amount'), R('funding', 'source'), SP2, R('funding', 'status'), PROM), MON18)),
    O('Extra saving a month, last payment 2 months sooner', 'money', 'ROUND(%s/MAX(1,%s-2),0)' % (GAP18, MON18)),
    O('Verdict', 'text', 'IF(%s<=0,%s,%s&" "&ROUND(%s/%s,0)&" "&%s)' % (GAP18, V('On pace'), V('Save'), GAP18, MON18, V('more a month')))],
    GR('What if', ('Total budget, no gifts', {'goal_true': 0, 'gifts_pct': 0}), ('True budget, no gifts', {'goal_true': 1, 'gifts_pct': 0}), ('True budget, half the gifts', {'goal_true': 1, 'gifts_pct': 0.5}),
       ('Total budget, all the gifts', {'goal_true': 0, 'gifts_pct': 1}), ('True budget, all the gifts', {'goal_true': 1, 'gifts_pct': 1}))))
assert len(tools) == 18
