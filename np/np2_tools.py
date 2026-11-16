"""Nonprofit suite part 2: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np2_lists import *
import np2_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def R(t, c): return '{range:%s.%s}' % (t, c)
G = lambda c: R('giving', c)
PR = lambda c: R('prospects', c)
YN = 'YEAR({today})'
THIS, LASTY, TWO = tok('yr', 'This year'), tok('yr', 'Last year'), tok('yr', 'Two years ago')
THIS2, LAST2 = tok('yr2', 'This year'), tok('yr2', 'Last year')
ALL = tok('dgroup', 'All donors')
S_LAP, S_RET = tok('gstate', 'Lapsed'), tok('gstate', 'Retained')
F_UP = tok('gflag', 'Upgraded')
CLOSED, ASKMADE, CULT = tok('pstage', 'Closed'), tok('pstage', 'Ask made'), tok('pstage', 'Cultivation')


def RD(col, yr='{in:year}', grp=ALL): return 'SUMIFS(%s,%s,%s,%s,%s)' % (R('ret_detail', col), R('ret_detail', 'year'), yr, R('ret_detail', 'group'), grp)
def TY3(col, yr, grp=ALL): return 'SUMIFS(%s,%s,%s,%s,%s)' % (R('three_year', col), R('three_year', 'year'), yr, R('three_year', 'group'), grp)
def MED(c):
    n = 'COUNTIF(%s,">0")' % c
    return 'IFERROR((LARGE(%s,INT((%s+1)/2))+LARGE(%s,INT(%s/2)+1))/2,0)' % (c, n, c, n)
def NTH(tbl, col, rankcol, k): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (R(tbl, col), k, R(tbl, rankcol))
tools = []

# 1 ---------------------------------------------------------------- retention checker
D1, B1, RT1, LR1 = RD('donors'), RD('base'), RD('retained'), RD('last_ret')
tools.append(TOOL('retention_checker', 'Retention Checker', 'Is retention better than your own last year',
    'Pick the year; retained, new, lapsed and recaptured donors and the retention rate come from Retention Detail, set against your own year before and your target.', [
    IN('year', 'Year to check', 'list', key('yr2', 'This year'), list='yr2'), I('extra', 'Lapsed donors you expect to win back before year end', 10, 'int')], [
    O('Donors who gave', 'int', D1), O('Donors the year before', 'int', B1), O('Retained donors', 'int', RT1), O('New donors', 'int', RD('new')), O('Lapsed donors', 'int', RD('lapsed')), O('Recaptured donors', 'int', RD('recaptured')),
    O('Retention rate', 'pct', RD('retention')), O('Your own retention the year before', 'pct', LR1), O('Difference in points', 'pct', '%s-%s' % (RD('retention'), LR1)),
    O('Your target', 'pct', '{set:retention_target}'), O('Retention if the donors you expect return', 'pct', 'IFERROR((%s+{in:extra})/%s,0)' % (RT1, B1)),
    O('Donors to win back to match your own last year', 'int', 'MAX(0,ROUNDUP(%s*%s-%s,0))' % (LR1, B1, RT1)),
    O('Verdict', 'text', 'IF(%s-%s>0.005,%s,IF(%s-%s<-0.005,%s,%s))' % (RD('retention'), LR1, vb('Better than last year'), RD('retention'), LR1, vb('Worse than last year'), vb('Same as last year')))],
    GR('What if', ('Last year', {'year': '=' + LAST2}), ('Twenty donors return', {'extra': 20}), ('Fifty donors return', {'extra': 50}), ('None return', {'extra': 0}))))

# 2 ---------------------------------------------------------------- new-donor retention
YN2 = '(%s-IF({in:year}=%s,1,2))' % (YN, THIS2)
BASE2 = 'COUNTIFS(%s,%s)' % (G('first_year'), YN2)
GAVE2 = 'IF({in:year}=%s,COUNTIFS(%s,%s,%s,">0"),COUNTIFS(%s,%s,%s,">0"))' % (THIS2, G('first_year'), YN2, G('y0'), G('first_year'), YN2, G('y1'))
AVG2 = 'IFERROR(AVERAGEIFS(%s,%s,">="&DATE(%s,1,1),%s,"<="&DATE(%s,12,31)),0)' % (R('first_time', 'first_amount'), R('first_time', 'first_gift'), YN2, R('first_time', 'first_gift'), YN2)
tools.append(TOOL('new_retention', 'New-Donor Retention Tracker', 'Do first-time donors give a second year',
    "First-time donors of the year before who gave again, against your own rate of last year, and what a second-gift plan could add.", [
    IN('year', 'Year to check', 'list', key('yr2', 'This year'), list='yr2'), I('gain', 'Points a second-gift plan could add, your estimate', 0.05, 'pct')], [
    O('First-time donors of the year before', 'int', BASE2), O('Gave again', 'int', GAVE2), O('New-donor retention', 'pct', 'IFERROR(%s/%s,0)' % (GAVE2, BASE2)),
    O('Your own rate last year', 'pct', RD('new_ret', LAST2)), O('Difference in points', 'pct', 'IFERROR(%s/%s,0)-%s' % (GAVE2, BASE2, RD('new_ret', LAST2))),
    O('Donors short of your own rate', 'int', 'MAX(0,ROUNDUP(%s*%s-%s,0))' % (RD('new_ret', LAST2), BASE2, GAVE2)),
    O('Extra donors with a plan', 'num', '%s*{in:gain}' % BASE2), O('Average first gift', 'money', AVG2), O('Money a plan could add', 'money', '%s*{in:gain}*%s' % (BASE2, AVG2)),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s,0)<%s,%s,%s)' % (GAVE2, BASE2, RD('new_ret', LAST2), va('Second-gift plan needed'), va('Holding')))],
    GR('What if', ('Last year', {'year': '=' + LAST2}), ('Plan adds 10 points', {'gain': 0.10}), ('Plan adds 2 points', {'gain': 0.02}))))

# 3 ---------------------------------------------------------------- repeat-donor retention
RBASE = 'IF({in:year}=%s,COUNTIFS(%s,">0",%s,"<"&(%s-1)),COUNTIFS(%s,">0",%s,"<"&(%s-2)))' % (THIS2, G('y1'), G('first_year'), YN, G('y2'), G('first_year'), YN)
tools.append(TOOL('repeat_retention', 'Repeat-Donor Retention Tracker', 'Do repeat donors keep giving',
    'Donors who gave in two or more years and kept giving, against your own rate the year before, with the money of repeat donors who have lapsed.', [
    IN('year', 'Year to check', 'list', key('yr2', 'This year'), list='yr2'), I('warn', 'Fall in points that worries you', 0.03, 'pct')], [
    O('Repeat donors the year before', 'int', RBASE), O('Repeat retention', 'pct', RD('repeat_ret')), O('Repeat donors kept', 'int', 'ROUND(%s*%s,0)' % (RBASE, RD('repeat_ret'))),
    O('Repeat donors lost', 'int', '%s-ROUND(%s*%s,0)' % (RBASE, RBASE, RD('repeat_ret'))), O('Your own rate last year', 'pct', RD('repeat_ret', LAST2)),
    O('Fall in points', 'pct', '%s-%s' % (RD('repeat_ret', LAST2), RD('repeat_ret'))), O('Money lapsed from repeat donors, last year gifts', 'money', 'SUMIFS(%s,%s,%s,%s,"<"&(%s-1))' % (G('y1'), G('state'), S_LAP, G('first_year'), YN)),
    O('Verdict', 'text', 'IF(%s-%s>{in:warn},%s,%s)' % (RD('repeat_ret', LAST2), RD('repeat_ret'), va('Falling'), va('Steady')))],
    GR('What if', ('Last year', {'year': '=' + LAST2}), ('Worry at 1 point', {'warn': 0.01}), ('Worry at 8 points', {'warn': 0.08}))))

# 4 ---------------------------------------------------------------- lapsed donor ranker
LP = lambda c: 'IFERROR(INDEX(%s,MATCH({in:rank_n},%s,0)),"")' % (R('lapsed', c), R('lapsed', 'rank'))
tools.append(TOOL('lapsed_ranker', 'Lapsed Donor Ranker', 'Which lapsed donors do I call first',
    'Donors who gave last year and not this year are ranked by their last 3 years of giving; each gets Call, Write or Let go from your two setting amounts. Type a rank to see that donor.', [
    I('rank_n', 'Show the donor at rank', 1, 'int'), I('per_day', 'Calls you can make in a day', 10, 'int')], [
    O('Lapsed donors', 'int', 'COUNTIFS(%s,%s)' % (G('state'), S_LAP)), O('Money they gave last year', 'money', 'SUMIFS(%s,%s,%s)' % (G('y1'), G('state'), S_LAP)),
    O('To call', 'int', 'COUNTIFS(%s,%s)' % (G('outreach'), va('Call'))), O('To write to', 'int', 'COUNTIFS(%s,%s)' % (G('outreach'), va('Write'))), O('To let go', 'int', 'COUNTIFS(%s,%s)' % (G('outreach'), va('Let go'))),
    O('Last year money of the donors to call', 'money', 'SUMIFS(%s,%s,%s)' % (G('y1'), G('outreach'), va('Call'))), O('Days of calls', 'int', 'ROUNDUP(COUNTIFS(%s,%s)/{in:per_day},0)' % (G('outreach'), va('Call'))),
    O('Donor at that rank', 'text', LP('donor')), O('Last gift on', 'date', LP('last_gift')), O('Given in the 3 years before this one', 'money', LP('three_years')), O('Years given', 'int', LP('years_given')),
    O('Verdict for that donor', 'text', LP('next_step'))],
    GR('What if', ('Rank 2', {'rank_n': 2}), ('Rank 10', {'rank_n': 10}), ('Rank 60', {'rank_n': 60}), ('Five calls a day', {'per_day': 5}))))

# 5 ---------------------------------------------------------------- win-back planner
def band(k): return 'COUNTIFS(%s,%d)' % (G('gap_years'), k)
def bmoney(k): return 'SUMIFS(%s,%s,%d)' % (G('last_given'), G('gap_years'), k)
EXP5 = '(%s*{set:win1}+%s*{set:win2}+%s*{set:win3})' % (bmoney(1), bmoney(2), bmoney(3))
COST5 = '(%s+%s+%s)*{in:cost_each}' % (band(1), band(2), band(3))
tools.append(TOOL('winback_planner', 'Win-Back Planner', 'Is a win-back campaign worth it',
    'Lapsed donors by years since their last gift, your estimate of who returns, the money that brings and the cost of reaching them, with a best and a worst case.', [
    I('scale', 'Return share against your estimates, 1 is as set', 1.0, 'num'), I('cost_each', 'Cost of one letter or call', 3.0), I('best', 'Best case multiplier', 1.5, 'num'), I('worst', 'Worst case multiplier', 0.5, 'num')], [
    O('Lapsed 1 year, donors', 'int', band(1)), O('Lapsed 2 years, donors', 'int', band(2)), O('Lapsed 3 years, donors', 'int', band(3)), O('Their last gifts, 1 year', 'money', bmoney(1)),
    O('Their last gifts, 2 years', 'money', bmoney(2)), O('Their last gifts, 3 years', 'money', bmoney(3)),
    O('Donors who return, your estimate', 'num', '(%s*{set:win1}+%s*{set:win2}+%s*{set:win3})*{in:scale}' % (band(1), band(2), band(3))), O('Money back, base case', 'money', '%s*{in:scale}' % EXP5),
    O('Money back, best case', 'money', '%s*{in:scale}*{in:best}' % EXP5), O('Money back, worst case', 'money', '%s*{in:scale}*{in:worst}' % EXP5), O('Cost of reaching them all', 'money', COST5),
    O('Cost per dollar, base case', 'num', 'IFERROR(%s/(%s*{in:scale}),0)' % (COST5, EXP5)), O('Net money, base case', 'money', '%s*{in:scale}-%s' % (EXP5, COST5)),
    O('Verdict', 'text', 'IF(IFERROR(%s/(%s*{in:scale}),1)<={set:cost_per_dollar},%s,%s)' % (COST5, EXP5, va('Worth a campaign'), va('Low value')))],
    GR('What if', ('Half return', {'scale': 0.5}), ('Costly calls', {'cost_each': 12.0}), ('Very costly calls', {'cost_each': 60.0, 'scale': 0.3}), ('Double the return', {'scale': 2.0}))))

# 6 ---------------------------------------------------------------- upgrade ask ranker
EL6 = '(%s>={in:min_years})*(%s>0)*(%s>0)*(%s<>%s)' % (G('years_given'), G('y0'), G('y1'), G('flag'), F_UP)
UP = lambda c: 'IFERROR(INDEX(%s,MATCH({in:rank_n},%s,0)),"")' % (R('upgrade', c), R('upgrade', 'rank'))
tools.append(TOOL('upgrade_ranker', 'Upgrade Ask Ranker', 'Which regular donors do I ask for more',
    'Regular donors who gave in several years including the last two, with the extra a gentle ask could bring at your take-up estimate; type a rank to see the ask for that donor.', [
    I('uplift', 'Raise on their average gift', 0.20, 'pct'), I('min_years', 'Years given at least', 3, 'int'), I('take_up', 'Share who say yes, your estimate', 0.25, 'pct'), I('rank_n', 'Show the donor at rank', 1, 'int')], [
    O('Donors to ask', 'int', 'SUMPRODUCT(%s)' % EL6), O('Given this year by those donors', 'money', 'SUMPRODUCT(%s*%s)' % (EL6, G('y0'))), O('Extra if every one agreed', 'money', 'SUMPRODUCT(%s*%s)*{in:uplift}' % (EL6, G('y0'))),
    O('Extra at your take-up estimate', 'money', 'SUMPRODUCT(%s*%s)*{in:uplift}*{in:take_up}' % (EL6, G('y0'))), O('Ask now on the list', 'int', 'COUNTIFS(%s,%s)' % (R('upgrade', 'verdict'), va('Ask now'))),
    O('Wait on the list', 'int', 'COUNTIFS(%s,%s)' % (R('upgrade', 'verdict'), va('Wait'))), O('Donor at that rank', 'text', UP('donor')), O('Their average gift', 'money', UP('avg_gift')),
    O('Ask with your raise', 'money', 'IFERROR(MAX(ROUND(%s*(1+{in:uplift})/5,0)*5,%s+5),"")' % (UP('avg_gift'), UP('avg_gift'))), O('Years they gave', 'int', UP('years_given')), O('Verdict for that donor', 'text', UP('verdict'))],
    GR('What if', ('Raise 10 percent', {'uplift': 0.10}), ('Raise 35 percent', {'uplift': 0.35}), ('Four years only', {'min_years': 4}), ('Half say yes', {'take_up': 0.5}))))

# 7 ---------------------------------------------------------------- downgrade watcher
EL7 = '(%s>={in:min_prior})*(%s>0)*(%s<=%s*(1-{in:drop}))' % (G('y1'), G('y0'), G('y0'), G('y1'))
tools.append(TOOL('downgrade_watcher', 'Downgrade Watcher', 'Which donors are giving less',
    'Donors who gave this year but fell by more than your share, the money they fell by and who to call this month. This year is to date, so judge with care before year end.', [
    I('drop', 'Fall that counts', 0.30, 'pct'), I('min_prior', 'Gave at least last year', 100)], [
    O('Donors who gave less', 'int', 'SUMPRODUCT(%s)' % EL7), O('Money they fell by', 'money', 'SUMPRODUCT(%s*(%s-%s))' % (EL7, G('y1'), G('y0'))), O('Share of last year giving they hold', 'pct', 'SUMPRODUCT(%s*%s)/SUM(%s)' % (EL7, G('y1'), G('y1'))),
    O('To call this month', 'int', 'COUNTIFS(%s,%s)' % (R('downgrade', 'verdict'), va('Call this month'))), O('To note only', 'int', 'COUNTIFS(%s,%s)' % (R('downgrade', 'verdict'), va('Note'))),
    O('Largest fall, donor', 'text', NTH('downgrade', 'donor', 'rank', 1)), O('Largest fall, amount', 'money', NTH('downgrade', 'drop', 'rank', 1)), O('Given this year by that donor', 'money', NTH('downgrade', 'this_year', 'rank', 1)),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,%s)>0,%s,%s)' % (R('downgrade', 'verdict'), va('Call this month'), va('Call this month'), va('Note')))],
    GR('What if', ('Fall of 50 percent', {'drop': 0.5}), ('Fall of 15 percent', {'drop': 0.15}), ('Gave 500 or more', {'min_prior': 500}))))

# 8 ---------------------------------------------------------------- average and median
AVGY = lambda y: 'IFERROR(%s/%s,0)' % (TY3('amount', y), TY3('donors', y))
BANDI = lambda c: 'IFERROR(INDEX(%s,MATCH({in:band},%s,0)),0)' % (R('bands', c), R('bands', 'band'))
tools.append(TOOL('avg_median', 'Average and Median Gift View', 'Do a few large gifts lift the average',
    "This year's average and median gift, the average and median yearly giving per donor over the years, and one size band, with a verdict.", [
    I('lift', 'Average above the median by this many times counts as lifted', 1.5, 'num'), IL('band', 'Band to look at', 'band', '250 to 499')], [
    O('Average gift this year', 'money', 'SUM(%s)/COUNT(%s)' % (R('gifts', 'amount'), R('gifts', 'amount'))), O('Median gift this year', 'money', 'MEDIAN(%s)' % R('gifts', 'amount')),
    O('Average divided by median', 'num', 'SUM(%s)/COUNT(%s)/MEDIAN(%s)' % (R('gifts', 'amount'), R('gifts', 'amount'), R('gifts', 'amount'))),
    O('Average giving per donor, this year', 'money', AVGY(THIS)), O('Average giving per donor, last year', 'money', AVGY(LASTY)), O('Average giving per donor, 2 years ago', 'money', AVGY(TWO)),
    O('Median giving per donor, this year', 'money', MED(G('y0'))), O('Median giving per donor, last year', 'money', MED(G('y1'))), O('Median giving per donor, 2 years ago', 'money', MED(G('y2'))),
    O('Donors in the band', 'int', BANDI('donors')), O('Share of the year they give', 'pct', BANDI('share')), O('Average per donor in the band', 'money', BANDI('avg_donor')),
    O('Verdict', 'text', 'IF(SUM(%s)/COUNT(%s)/MEDIAN(%s)>={in:lift},%s,%s)' % (R('gifts', 'amount'), R('gifts', 'amount'), R('gifts', 'amount'), vb('A few large gifts lift the average'), vb('Spread evenly')))],
    GR('What if', ('Lift at 3 times', {'lift': 3.0}), ('Lift at 5 times', {'lift': 5.0}), ('Band 1,000 to 2,499', {'band': '=' + tok('band', '1,000 to 2,499')}), ('Band 25,000 and over', {'band': '=' + tok('band', '25,000 and over')}))))

# 9 ---------------------------------------------------------------- second-gift plan
CV = lambda c: 'IFERROR(INDEX(%s,MATCH({in:appeal},%s,0)),0)' % (R('conversion', c), R('conversion', 'appeal'))
WAIT9 = 'COUNTIFS(%s,{in:appeal},%s,%s,%s,">="&({today}-{in:window}))' % (R('first_time', 'first_appeal'), R('first_time', 'flag'), vb('Waiting for second gift'), R('first_time', 'first_gift'))
tools.append(TOOL('second_gift_plan', 'Second-Gift Plan', 'Who gets a second-gift ask, and when',
    'Pick an appeal; first-time donors still waiting for a second gift are counted, with the day to send, your conversion against your own last year and the message that fits.', [
    IL('appeal', 'Appeal', 'appeal', 'Thank-you and renewal'), I('window', 'First gift within this many days', 120, 'int'), I('send_in', 'Working days until you send', 3, 'int')], [
    O('Donors waiting for a second gift', 'int', WAIT9), O('Waiting, all appeals', 'int', 'COUNTIFS(%s,%s,%s,">="&({today}-{in:window}))' % (R('first_time', 'flag'), vb('Waiting for second gift'), R('first_time', 'first_gift'))),
    O('Conversion of this appeal', 'pct', CV('conversion')), O('Your own conversion the year before', 'pct', CV('last_conv')), O('Points against your own', 'pct', '%s-%s' % (CV('conversion'), CV('last_conv'))),
    O('Second gifts to expect', 'num', '%s*%s' % (WAIT9, CV('conversion'))), O('Average first gift', 'money', 'IFERROR(AVERAGEIFS(%s,%s,{in:appeal}),0)' % (R('first_time', 'first_amount'), R('first_time', 'first_appeal'))),
    O('Send on', 'date', 'WORKDAY({today},{in:send_in})'), O('Message to send', 'text', 'IF(%s<%s,%s,%s)' % (CV('conversion'), CV('last_conv'), vb('Send the second-gift ask'), vb('Send a thank-you only'))),
    O('Donors to send it to', 'int', WAIT9)],
    GR('What if', ('Within 60 days', {'window': 60}), ('Within 240 days', {'window': 240}), ('Spring gala invitation', {'appeal': '=' + tok('appeal', 'Gala invitation')}), ('Year-end letter', {'appeal': '=' + tok('appeal', 'Year-end letter')}))))

# 10 --------------------------------------------------------------- second-gift gap solver
FT_ = 'SUM(%s)' % R('conversion', 'first_timers')
GV_ = 'SUM(%s)' % R('conversion', 'gave_again')
OWN10 = 'IFERROR(SUMPRODUCT(%s,%s)/SUM(%s),0)' % (R('conversion', 'earlier_timers'), R('conversion', 'last_conv'), R('conversion', 'earlier_timers'))
NEED10 = 'MAX(0,ROUNDUP((%s+{in:extra})*%s-%s,0))' % (OWN10, FT_, GV_)
tools.append(TOOL('second_gift_gap', 'Second-Gift Gap Solver', 'How many more second gifts do we need',
    'Solves for the second gifts needed to reach your own conversion of the year before, plus any extra points you want, and what they are worth at the average first gift.', [
    I('extra', 'Extra points you want above your own', 0.10, 'pct'), I('avg_second', 'Average second gift', 60)], [
    O('First-time donors in the group', 'int', FT_), O('Gave again within 12 months', 'int', GV_), O('Conversion now', 'pct', 'IFERROR(%s/%s,0)' % (GV_, FT_)), O('Your own conversion the year before', 'pct', OWN10),
    O('Conversion you want', 'pct', '%s+{in:extra}' % OWN10), O('Second gifts needed', 'int', NEED10), O('Money those gifts bring', 'money', '%s*{in:avg_second}' % NEED10),
    O('Needed a month, over 12 months', 'num', '%s/12' % NEED10), O('Verdict', 'text', 'IF(%s>0,%s,%s)' % (NEED10, vb('Need more second gifts'), vb('Second-gift target met')))],
    GR('What if', ('No extra points', {'extra': 0}), ('Five extra points', {'extra': 0.05}), ('Ten extra points', {'extra': 0.10}), ('Larger second gift', {'avg_second': 120}))))

# 11 --------------------------------------------------------------- major-gift pipeline view
def STW(s): return 'SUMIFS(%s,%s,%s)*{in:shift}' % (PR('weighted_value'), PR('stage'), s)
TOT11 = 'SUMIFS(%s,%s,"<>"&%s)*{in:shift}' % (PR('weighted_value'), PR('stage'), CLOSED)
LEFT11 = 'MAX(0,{in:goal}-SUMIFS(%s,%s,%s))' % (PR('ask_amount'), PR('stage'), CLOSED)
tools.append(TOOL('pipeline_view', 'Major-Gift Pipeline View', 'Does the pipeline cover the major-gift goal',
    'Weighted value by stage with your own stage estimates, what has already closed and how much of the rest of the goal the open pipeline covers.', [
    I('goal', 'Major-gift goal this year', 45000), I('shift', 'Move all your estimates by this factor, 1 is as set', 1.0, 'num')], [
    O('Identified, weighted', 'money', STW(tok('pstage', 'Identified'))), O('Cultivation, weighted', 'money', STW(CULT)), O('Ask made, weighted', 'money', STW(ASKMADE)), O('Committed, weighted', 'money', STW(tok('pstage', 'Committed'))),
    O('Open pipeline, weighted', 'money', TOT11), O('Open pipeline, asked', 'money', 'SUMIFS(%s,%s,"<>"&%s)' % (PR('ask_amount'), PR('stage'), CLOSED)), O('Closed so far', 'money', 'SUMIFS(%s,%s,%s)' % (PR('ask_amount'), PR('stage'), CLOSED)),
    O('Goal still to find', 'money', LEFT11), O('Share of the rest the pipeline covers', 'pct', 'IFERROR(%s/%s,0)' % (TOT11, LEFT11)), O('Gap after the pipeline', 'money', 'MAX(0,%s-%s)' % (LEFT11, TOT11)),
    O('Open prospects', 'int', 'COUNTIFS(%s,"<>",%s,"<>"&%s)' % (PR('prospect_id'), PR('stage'), CLOSED)), O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (TOT11, LEFT11, vb('Pipeline covers the goal'), vb('Pipeline short of the goal')))],
    GR('What if', ('Estimates 20 percent lower', {'shift': 0.8}), ('Estimates 30 percent higher', {'shift': 1.3}), ('Goal 60,000', {'goal': 60000}), ('Goal 30,000', {'goal': 30000}))))

# 12 --------------------------------------------------------------- ask-this-month list
AS = lambda k, c: 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),"")' % (PR(c), PR('ask_score'), k, PR('ask_score'))
tools.append(TOOL('ask_list', 'Ask-This-Month List', 'Who do we ask or cultivate this month',
    'Prospects at the cultivation or ask stage whose next step falls in the next 30 days or is already late, ranked by weighted value, with a verdict.', [
    I('floor', 'Weighted value at least', 500)], [
    O('Prospects on the list', 'int', 'COUNT(%s)' % PR('ask_score')), O('Of them worth the floor or more', 'int', 'COUNTIFS(%s,">="&{in:floor})' % PR('ask_score')), O('Amount asked', 'money', 'SUMIFS(%s,%s,">0")' % (PR('ask_amount'), PR('ask_score'))),
    O('Weighted value', 'money', 'SUMIFS(%s,%s,">0")' % (PR('weighted_value'), PR('ask_score'))), O('At the ask stage', 'int', 'COUNTIFS(%s,">0",%s,%s)' % (PR('ask_score'), PR('stage'), ASKMADE)),
    O('In cultivation', 'int', 'COUNTIFS(%s,">0",%s,%s)' % (PR('ask_score'), PR('stage'), CULT)), O('First prospect', 'text', AS(1, 'donor')), O('Its weighted value', 'money', AS(1, 'weighted_value')),
    O('Second prospect', 'text', AS(2, 'donor')), O('Third prospect', 'text', AS(3, 'donor')), O('Next step of the first', 'text', AS(1, 'next_step')),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">0",%s,%s)>0,%s,IF(COUNT(%s)>0,%s,%s))' % (PR('ask_score'), PR('stage'), ASKMADE, va('Ask'), PR('ask_score'), va('Cultivate'), va('Pause')))],
    GR('What if', ('Floor 1,000', {'floor': 1000}), ('Floor 2,500', {'floor': 2500}), ('Floor 0', {'floor': 0}))))

# 13 --------------------------------------------------------------- overdue next-step chaser
CH = lambda k, c: 'IFERROR(INDEX(%s,MATCH(LARGE(%s,%d),%s,0)),"")' % (PR(c), PR('chase_score'), k, PR('chase_score'))
tools.append(TOOL('chaser', 'Overdue Next-Step Chaser', 'Which overdue next steps do I act on today',
    'Next steps past their date, ranked by days late and then value; steps older than your stale limit are better rescheduled than chased.', [
    I('stale', 'Days late after which you reschedule', 14, 'int')], [
    O('Next steps overdue', 'int', 'COUNT(%s)' % PR('chase_score')), O('Oldest, days', 'int', 'MAX(%s)' % PR('overdue_days')), O('Weighted value waiting', 'money', 'SUMIFS(%s,%s,">0")' % (PR('weighted_value'), PR('overdue_days'))),
    O('Older than your limit', 'int', 'COUNTIFS(%s,">"&{in:stale})' % PR('overdue_days')), O('To act on today', 'int', 'COUNTIFS(%s,">0",%s,"<="&{in:stale})' % (PR('overdue_days'), PR('overdue_days'))),
    O('First, most days late', 'text', CH(1, 'donor')), O('Its days late', 'int', CH(1, 'overdue_days')), O('Its next step', 'text', CH(1, 'next_step')), O('Second', 'text', CH(2, 'donor')), O('Third', 'text', CH(3, 'donor')),
    O('Verdict for the first', 'text', 'IF(COUNT(%s)=0,%s,IF(%s>{in:stale},%s,%s))' % (PR('chase_score'), va('On schedule'), CH(1, 'overdue_days'), va('Reschedule'), va('Act today')))],
    GR('What if', ('Limit 7 days', {'stale': 7}), ('Limit 30 days', {'stale': 30}), ('Limit 60 days', {'stale': 60}))))

# 14 --------------------------------------------------------------- appeal keep-fix-stop
AR = lambda c: 'IFERROR(INDEX(%s,MATCH({in:appeal},%s,0)),0)' % (R('appeal_results', c), R('appeal_results', 'appeal'))
CPD2 = 'IFERROR(%s*(1-{in:cut})/%s,0)' % (AR('cost'), AR('amount'))
tools.append(TOOL('keep_fix_stop', 'Appeal Keep-Fix-Stop', 'Do we keep, fix or stop this appeal',
    'Pick an appeal; its gifts, cost and cost to raise one dollar are set against your starting point and your own last year, with the cost cut or extra money needed.', [
    IL('appeal', 'Appeal', 'appeal', 'Camp scholarship letter'), I('cut', 'Cost you could cut', 0.20, 'pct')], [
    O('Gifts', 'int', AR('gifts_n')), O('Donors', 'int', AR('donors')), O('Amount raised', 'money', AR('amount')), O('Cost', 'money', AR('cost')), O('Cost per dollar', 'num', AR('cost_per_dollar')),
    O('Your starting point', 'num', '{set:cost_per_dollar}'), O('Your own cost per dollar last year', 'num', AR('last_cpd')), O('Cost to cut to reach your starting point', 'money', 'MAX(0,%s-{set:cost_per_dollar}*%s)' % (AR('cost'), AR('amount'))),
    O('Extra raised needed at the same cost', 'money', 'MAX(0,%s/{set:cost_per_dollar}-%s)' % (AR('cost'), AR('amount'))), O('Cost per dollar after your cut', 'num', CPD2),
    O('Verdict now', 'text', 'IF(%s<={set:cost_per_dollar},%s,IF(AND(%s>2*{set:cost_per_dollar},%s>%s),%s,%s))' % (AR('cost_per_dollar'), va('Keep'), AR('cost_per_dollar'), AR('cost_per_dollar'), AR('last_cpd'), va('Stop'), va('Fix'))),
    O('Verdict after your cut', 'text', 'IF(%s<={set:cost_per_dollar},%s,IF(AND(%s>2*{set:cost_per_dollar},%s>%s),%s,%s))' % (CPD2, va('Keep'), CPD2, CPD2, AR('last_cpd'), va('Stop'), va('Fix'))),
    O('Appeals to keep', 'int', 'COUNTIFS(%s,%s)' % (R('appeal_results', 'verdict'), va('Keep'))), O('Appeals to fix', 'int', 'COUNTIFS(%s,%s)' % (R('appeal_results', 'verdict'), va('Fix'))),
    O('Appeals to stop', 'int', 'COUNTIFS(%s,%s)' % (R('appeal_results', 'verdict'), va('Stop')))],
    GR('What if', ('Gala invitation', {'appeal': '=' + tok('appeal', 'Gala invitation')}), ('Senior holiday card', {'appeal': '=' + tok('appeal', 'Senior holiday card')}), ('Monthly giving page', {'appeal': '=' + tok('appeal', 'Monthly giving page')}), ('Cut half the cost', {'cut': 0.5}))))

# 15 --------------------------------------------------------------- source comparison
SRC = lambda c, ch: 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('source_results', c), ch, R('source_results', 'channel'))
IDX = lambda ch: 'IFERROR(%s/%s,0)' % (SRC('retention', ch), SRC('cost_per_dollar', ch))
WIN15 = 'IF(%s>=%s,{in:chan_a},{in:chan_b})' % (IDX('{in:chan_a}'), IDX('{in:chan_b}'))
GA = lambda ch: 'SUMIFS(%s,%s,%s)' % (R('gifts', 'amount'), R('gifts', 'channel'), ch)
tools.append(TOOL('source_compare', 'Source Comparison', 'Which channel deserves more effort',
    'Two channels side by side: money, cost to raise one dollar and the retention of the donors each brings, with the lasting return per dollar spent and a verdict.', [
    IL('chan_a', 'Channel A', 'channel', 'Online form'), IL('chan_b', 'Channel B', 'channel', 'Mail'), I('move', 'Cost you could move', 1000)], [
    O('Money from A this year', 'money', GA('{in:chan_a}')), O('Money from B this year', 'money', GA('{in:chan_b}')), O('Cost per dollar, A', 'num', SRC('cost_per_dollar', '{in:chan_a}')), O('Cost per dollar, B', 'num', SRC('cost_per_dollar', '{in:chan_b}')),
    O('Retention of donors from A', 'pct', SRC('retention', '{in:chan_a}')), O('Retention of donors from B', 'pct', SRC('retention', '{in:chan_b}')), O('Lasting return per dollar, A', 'num', IDX('{in:chan_a}')), O('Lasting return per dollar, B', 'num', IDX('{in:chan_b}')),
    O('Return gap on the cost you move, if rates held', 'money', '{in:move}*ABS(%s-%s)' % (IDX('{in:chan_a}'), IDX('{in:chan_b}'))),
    O('Cheapest channel of all', 'text', 'INDEX(%s,MATCH(SMALL(%s,1),%s,0))' % (R('source_results', 'channel'), R('source_results', 'cost_per_dollar'), R('source_results', 'cost_per_dollar'))),
    O('Best retention of all', 'text', 'INDEX(%s,MATCH(LARGE(%s,1),%s,0))' % (R('source_results', 'channel'), R('source_results', 'retention'), R('source_results', 'retention'))),
    O('Verdict', 'text', 'CHOOSE(MATCH(%s,%s,0),%s)' % (WIN15, R('source_results', 'channel'), ','.join(vb('Shift effort to ' + c) for c in CHANNELS)))],
    GR('What if', ('Event against Mail', {'chan_a': '=' + tok('channel', 'Event'), 'chan_b': '=' + tok('channel', 'Mail')}), ('In person against Online', {'chan_a': '=' + tok('channel', 'In person'), 'chan_b': '=' + tok('channel', 'Online form')}), ('Payroll against Mail', {'chan_a': '=' + tok('channel', 'Payroll giving'), 'chan_b': '=' + tok('channel', 'Mail')}), ('Move 5,000', {'move': 5000}))))

# 16 --------------------------------------------------------------- concentration check
SH = lambda n: 'SUMIFS(%s,%s,"<="&%d)/SUM(%s)' % (R('top_donors', 'amount'), R('top_donors', 'rank'), n, G('y0'))
tools.append(TOOL('concentration', 'Concentration Check', 'Are we too reliant on a few donors',
    "The share of this year's giving from the top 5 and top 10 donors against your own comfort level and your own last year.", [
    I('watch', 'Top 5 share you are comfortable with', 0.15, 'pct')], [
    O('Share from the top 5', 'pct', SH(5)), O('Share from the top 10', 'pct', SH(10)), O('Share from the biggest donor', 'pct', SH(1)), O('Money from the top 5', 'money', 'SUMIFS(%s,%s,"<=5")' % (R('top_donors', 'amount'), R('top_donors', 'rank'))),
    O('Top 5 share last year, your own', 'pct', TY3('top_share', LASTY)), O('Change in points', 'pct', '%s-%s' % (SH(5), TY3('top_share', LASTY))),
    O('Donors making half the year (30 = 30 or more)', 'int', 'COUNTIFS(%s,"<0.5")+1' % R('top_donors', 'cum_share')), O('Watch level', 'pct', '{in:watch}'), O('Risk level, 1.5 times the watch level', 'pct', '{in:watch}*1.5'),
    O('Verdict', 'text', 'IF(%s<{in:watch},%s,IF(%s<{in:watch}*1.5,%s,%s))' % (SH(5), va('Spread out'), SH(5), va('Watch'), va('At risk')))],
    GR('What if', ('Comfort at 10 percent', {'watch': 0.10}), ('Comfort at 20 percent', {'watch': 0.20}), ('Comfort at 30 percent', {'watch': 0.30}))))

# 17 --------------------------------------------------------------- lose the biggest donor
TD = lambda c, k=1: 'IFERROR(INDEX(%s,MATCH(%d,%s,0)),0)' % (R('top_donors', c), k, R('top_donors', 'rank'))
LOST17 = '(%s*{in:loss}*(1-{in:replace}))' % TD('yearly')
LAP17 = 'SUMIFS(%s,%s,%s,%s,">="&{set:major_min})' % (G('y1'), G('state'), S_LAP, G('y1'))
T3 = 'SUMIFS(%s,%s,"<=3")' % (R('top_donors', 'yearly'), R('top_donors', 'rank'))
FM = '{set:free_money}'; ME = '{set:monthly_expense}'
tools.append(TOOL('lose_biggest', 'Lose-the-Biggest-Donor Scenario', 'What if our biggest donor left',
    "The biggest donor's giving, what is left in free money and months of reserve against your own reserve months, a row for the top 3 and one for the lapsing major donors who may not return.", [
    I('loss', 'Share of their giving lost', 1.0, 'pct'), I('replace', 'Share you could replace from other gifts', 0.0, 'pct')], [
    O('Biggest donor', 'text', 'IFERROR(INDEX(%s,MATCH(1,%s,0)),"")' % (R('top_donors', 'donor'), R('top_donors', 'rank'))), O('Their giving at risk', 'money', TD('yearly')), O('Money lost after replacing', 'money', LOST17),
    O('Free money after', 'money', '%s-%s' % (FM, LOST17)), O('Months of reserve left', 'num', '(%s-%s)/%s' % (FM, LOST17, ME)),
    O('Gap to your reserve months', 'money', 'MAX(0,{set:reserve_months}*%s-(%s-%s))' % (ME, FM, LOST17)),
    O('Verdict', 'text', 'IF({set:reserve_months}*%s>%s-%s,%s,%s)' % (ME, FM, LOST17, va('Gap'), va('Covered'))),
    O('Top 3 donors, money lost', 'money', '%s*{in:loss}*(1-{in:replace})' % T3), O('Top 3, months of reserve left', 'num', '(%s-%s*{in:loss}*(1-{in:replace}))/%s' % (FM, T3, ME)),
    O('Top 3, gap to your reserve months', 'money', 'MAX(0,{set:reserve_months}*%s-(%s-%s*{in:loss}*(1-{in:replace})))' % (ME, FM, T3)),
    O('Lapsing donor at the top of the lapsed list', 'text', NTH('lapsed', 'donor', 'rank', 1)), O('Their last 3 years of giving', 'money', NTH('lapsed', 'three_years', 'rank', 1)),
    O('Their giving last year', 'money', NTH('lapsed', 'last_year', 'rank', 1)), O('Months left if they do not return', 'num', '(%s-%s)/%s' % (FM, NTH('lapsed', 'last_year', 'rank', 1), ME)),
    O('Giving of all lapsing major donors', 'money', LAP17), O('Months left if none return', 'num', '(%s-%s)/%s' % (FM, LAP17, ME))],
    GR('What if', ('Half the giving', {'loss': 0.5}), ('Replace half', {'replace': 0.5}), ('Lose it all, replace none', {'loss': 1.0, 'replace': 0.0}), ('Replace 90 percent', {'replace': 0.9}))))

# 18 --------------------------------------------------------------- donor story writer
SY = lambda c: TY3(c, '{in:year}')
DD18 = 'IF(%s>%s*(1+{in:flat}),1,IF(%s<%s*(1-{in:flat}),3,2))' % (SY('donors'), SY('donors_prev'), SY('donors'), SY('donors_prev'))
MM18 = 'IF(%s>%s*(1+{in:flat}),1,IF(%s<%s*(1-{in:flat}),3,2))' % (SY('amount'), SY('amount_prev'), SY('amount'), SY('amount_prev'))
tools.append(TOOL('story_writer', 'Donor Story Writer', 'What is the donor story of the year',
    'Three years of donors, money and average gift turned into one plain sentence, with the direction of donors and of money. This year is to date.', [
    IN('year', 'Year to tell', 'list', key('yr', 'This year'), list='yr'), I('flat', 'Change that still counts as flat', 0.02, 'pct')], [
    O('Donors', 'int', SY('donors')), O('Donors the year before', 'int', SY('donors_prev')), O('Money given', 'money', SY('amount')), O('Money the year before', 'money', SY('amount_prev')),
    O('Average gift', 'money', SY('avg_gift')), O('Retention', 'pct', SY('retention')), O('Change in donors', 'pct', 'IFERROR(%s/%s-1,0)' % (SY('donors'), SY('donors_prev'))),
    O('Change in money', 'pct', 'IFERROR(%s/%s-1,0)' % (SY('amount'), SY('amount_prev'))), O('Share from the top 5', 'pct', SY('top_share')),
    O('Direction of donors', 'text', 'CHOOSE(%s,%s,%s,%s)' % (DD18, vb('Donors up'), vb('Donors flat'), vb('Donors down'))), O('Direction of money', 'text', 'CHOOSE(%s,%s,%s,%s)' % (MM18, vb('Money up'), vb('Money flat'), vb('Money down'))),
    O('The story in a sentence', 'text', 'CHOOSE((%s-1)*3+%s,%s)' % (DD18, MM18, ','.join(vc(s) for s in STORY)))],
    GR('What if', ('Last year', {'year': '=' + LASTY}), ('Two years ago', {'year': '=' + TWO}), ('Flat within 10 percent', {'flat': 0.10}))))
assert len(tools) == 18
