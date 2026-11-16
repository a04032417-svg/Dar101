"""Doula business suite part 7: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du7_lists import *
import du7_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='num', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, lab): return IN(k, label, 'list', key(lst, lab), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YES = '{list:yesno.yes}'
CANC = tok('ctstatus', 'Cancelled'); TYS = tok('mkind', 'Referral thank-yous')
CARE, PAST, SUPP, CLSS = tok('rsource', 'Care provider'), tok('rsource', 'Past client'), tok('rsource', 'Support professional'), tok('rsource', 'Class or workshop')
SIGNED = tok('estatus', 'Signed')
def DW(col, n): return '{range:%s},">="&({today}-%s),{range:%s},"<="&{today}' % (col, n, col)
def DM(col, n): return '{range:%s},">"&EDATE({today},-%s),{range:%s},"<="&{today}' % (col, n, col)
def MM(n): return '{range:marketing.month},">"&EDATE(%s,-%s),{range:marketing.month},"<="&%s' % (MS, n, MS)
tools = []

# 1 ------------------------------------------------------------ referral source value ranker
S_ENQ = 'COUNTIFS({range:enquiries.source},{in:source},%s)' % DM('enquiries.date', '{in:months}')
S_CLN = 'COUNTIFS({range:contracts.source},{in:source},%s,{range:contracts.status},"<>"&%s)' % (DM('contracts.signed_on', '{in:months}'), CANC)
S_INC = 'SUMIFS({range:contracts.price},{range:contracts.source},{in:source},%s,{range:contracts.status},"<>"&%s)' % (DM('contracts.signed_on', '{in:months}'), CANC)
S_COST = '(SUMIFS({range:referrals.gift_cost},{range:referrals.source},{in:source},%s)+SUMIFS({range:marketing.cost},{range:marketing.source},{in:source},%s,{range:marketing.kind},"<>"&%s))' % (DM('referrals.date', '{in:months}'), MM('{in:months}'), TYS)
A_INC = 'SUMIFS({range:contracts.price},%s,{range:contracts.status},"<>"&%s)' % (DM('contracts.signed_on', '{in:months}'), CANC)
A_CLN = 'COUNTIFS(%s,{range:contracts.status},"<>"&%s)' % (DM('contracts.signed_on', '{in:months}'), CANC)
RANK = '1+SUMPRODUCT(--(SUMIFS({range:contracts.price},{range:contracts.source},{range:sources.source},%s,{range:contracts.status},"<>"&%s)>%s))' % (DM('contracts.signed_on', '{in:months}'), CANC, S_INC)
tools.append(TOOL('src_ranker', 'Source Value Ranker', 'Which sources earn their place, ranked by income and not by count',
    'Pick a source and the months to look back: enquiries, clients, income, income per client, the cost of gifts and fees, the rank by income and a feed, hold or cut verdict against the cost per signed client you accept.', [
    IL('source', 'Source', 'source', 'Care provider'), I('months', 'Months to look back', 12, 'int')], [
    O('Enquiries', 'int', S_ENQ), O('Clients signed', 'int', S_CLN), O('Enquiries that became clients', 'pct', 'IFERROR(%s/%s,0)' % (S_CLN, S_ENQ)), O('Income of those clients', 'money', S_INC),
    O('Income per client', 'money', 'IFERROR(%s/%s,0)' % (S_INC, S_CLN)), O('Average income per client, all sources', 'money', 'IFERROR(%s/%s,0)' % (A_INC, A_CLN)),
    O('Cost of gifts and fees', 'money', S_COST), O('Cost per signed client', 'money', 'IFERROR(%s/%s,0)' % (S_COST, S_CLN)), O('Income left after the cost', 'money', '%s-%s' % (S_INC, S_COST)),
    O('Share of all income', 'pct', 'IFERROR(%s/%s,0)' % (S_INC, A_INC)), O('Rank by income, among 8 sources', 'int', RANK),
    O('Top source by income, all time', 'text', 'IFERROR(INDEX({range:src_value.source},MATCH(MAX({range:src_value.income}),{range:src_value.income},0))&"","")'),
    O('Cost per signed client you accept', 'money', '{set:cac_max}'),
    O('Verdict', 'text', 'IF(%s=0,IF(%s>0,%s,%s),IF(%s/%s>3*{set:cac_max},%s,IF(OR(%s/%s>{set:cac_max},%s/%s<%s/%s),%s,%s)))' % (
        S_CLN, S_COST, ca('Cut'), ca('Hold'), S_COST, S_CLN, ca('Cut'), S_COST, S_CLN, S_INC, S_CLN, A_INC, A_CLN, ca('Hold'), ca('Feed')))],
    GR('What if', ('Past client', {'source': '=' + tok('source', 'Past client')}), ('Online search', {'source': '=' + tok('source', 'Online search')}), ('Social media', {'source': '=' + tok('source', 'Social media')}),
       ('Care provider, 6 months', {'months': 6}), ('Care provider, 24 months', {'months': 24}))))

# 2 ------------------------------------------------------------ thank-you due list
TY_N = 'COUNTIFS({range:referrals.signed},1,{range:referrals.thanked},0,{range:referrals.age_days},"<="&{in:days})'
def TY_G(s): return 'COUNTIFS({range:referrals.signed},1,{range:referrals.thanked},0,{range:referrals.age_days},"<="&{in:days},{range:referrals.source},%s)*IFERROR(INDEX({range:sources.gift_value},MATCH(%s,{range:sources.source},0)),0)' % (s, s)
TY_V = 'IF({in:gift}>0,{in:gift}*%s,%s)' % (TY_N, '+'.join(TY_G(s) for s in (CARE, PAST, SUPP, CLSS)))
tools.append(TOOL('thanks_tool', 'Thank-you Due Tool', 'Which referrals still need a thank-you and what the gifts will cost',
    'Type the days back to look and a gift value if you use one price: the referrals that became clients and were not thanked, the gift value, the longest wait and how fast you usually thank; read from Referrals and Thank-you Due.', [
    I('days', 'Days back to look', 90, 'int'), I('gift', 'One gift value for all (0 = value of each source)', 0, 'money')], [
    O('Referrals waiting for a thank-you', 'int', TY_N), O('Referrers with a thank-you due now', 'int', 'COUNTIFS({range:thanks.flag},%s)' % ca('Thank-you due')),
    O('Gift value to send', 'money', TY_V), O('Older thank-yous you missed', 'int', 'COUNTIFS({range:referrals.signed},1,{range:referrals.thanked},0,{range:referrals.age_days},">"&{in:days})'),
    O('Longest wait, days', 'int', 'MAX({range:thanks.waiting_days})'), O('Average days to thank, all referrals thanked', 'num', 'IFERROR(AVERAGEIFS({range:referrals.days_to_thank},{range:referrals.thanked},1),0)'),
    O('Thanked within your late limit', 'pct', 'IFERROR(SUM({range:referrals.in_time})/SUM({range:referrals.matured}),0)'), O('Gift cost, last 12 months', 'money', 'SUMIFS({range:referrals.gift_cost},%s)' % DW('referrals.date', 365)),
    O('Share of your yearly gift budget used', 'pct', 'IFERROR(SUMIFS({range:referrals.gift_cost},%s)/{set:gift_budget_year},0)' % DW('referrals.date', 365)),
    O('Verdict', 'text', 'IF(%s>0,%s&": "&%s&", "&%s&" "&ROUND(%s,0),%s)' % (TY_N, c2('Thank-yous to send'), TY_N, c2('worth'), TY_V, c2('No thank-yous due')))],
    GR('What if', ('Last 30 days', {'days': 30}), ('Last 60 days', {'days': 60}), ('Last 180 days', {'days': 180}), ('Last 365 days', {'days': 365}), ('One gift of 20 for all', {'gift': 20}))))

# 3 ------------------------------------------------------------ referral gap list
GAPS = '{range:referrers.prev12},">="&{in:min},{range:referrers.last12},0'
BIG = 'MAX({range:referrers.silent_prev})'
tools.append(TOOL('gap_tool', 'Referral Gap Tool', 'Which referrers went quiet and who to visit or call first',
    'Type the fewest referrals before a silence and your follow-up days: how many referrers sent clients in the 12 months before and none in the last 12, what they were worth, the biggest gap and the follow-up date.', [
    I('min', 'Fewest referrals before the silence', 2, 'int'), I('follow', 'Days from today for the follow-up', 14, 'int')], [
    O('Referrers who went silent', 'int', 'COUNTIFS(%s)' % GAPS), O('Referrals they sent in the 12 months before', 'int', 'SUMIFS({range:referrers.prev12},%s)' % GAPS),
    O('Clients they sent in all', 'int', 'SUMIFS({range:referrers.clients},%s)' % GAPS), O('Income of those clients', 'money', 'SUMIFS({range:referrers.income},%s)' % GAPS),
    O('Care-provider offices sending less', 'int', 'COUNTIFS({range:referrers.office_trend},"<0")'),
    O('Referrers sending less than before', 'int', 'COUNTIFS({range:gaps.flag},%s)' % ca('Sending less')),
    O('Biggest gap', 'text', 'IF(%s>0,INDEX({range:referrers.referrer},MATCH(%s,{range:referrers.silent_prev},0)),"")' % (BIG, BIG)), O('Referrals before the silence', 'int', BIG),
    O('Phone of the biggest gap', 'text', 'IF(%s>0,INDEX({range:referrers.phone},MATCH(%s,{range:referrers.silent_prev},0)),"")' % (BIG, BIG)), O('Follow-up date', 'date', '{today}+{in:follow}'),
    O('Verdict', 'text', 'IF(COUNTIFS(%s)>0,%s&": "&INDEX({range:referrers.referrer},MATCH(%s,{range:referrers.silent_prev},0)),%s)' % (GAPS, c2('Visit or call first'), BIG, c2('No silent referrers')))],
    GR('What if', ('Two or more referrals before', {'min': 2}), ('Three or more', {'min': 3}), ('Four or more', {'min': 4}), ('Any referral before', {'min': 1}), ('Follow up in 30 days', {'follow': 30}))))

# 4 ------------------------------------------------------------ class and workshop economics
C_INC = '({in:price}*{in:signups})'
C_COST = '({in:venue}+{in:hours}*{set:instructor_rate})'
def CT(c): return 'IFERROR(INDEX({range:ctype_stats.%s},MATCH({in:class},{range:ctype_stats.class},0)),0)' % c
C_OWNF = 'IFERROR(SUMIFS({range:class_sessions.signed_up},{range:class_sessions.class},{in:class})/SUMIFS({range:class_sessions.seats},{range:class_sessions.class},{in:class}),0)'
C_OWNP = 'IFERROR(SUMIFS({range:class_sessions.profit},{range:class_sessions.class},{in:class})/COUNTIFS({range:class_sessions.class},{in:class}),0)'
tools.append(TOOL('class_econ_tool', 'Class Economics Tool', 'Does one class or workshop earn its time and cost',
    'Pick a class type and type price, seats, sign-ups, hours and venue cost: income, instructor time, profit, profit per class hour and the break-even sign-ups, set against your own history of that class and the clients it brought.', [
    IL('class', 'Class', 'ctype', 'Newborn workshop'), I('price', 'Price per seat', 55, 'money'), I('seats', 'Seats', 12, 'int'), I('signups', 'Sign-ups', 9, 'int'), I('hours', 'Class hours', 3),
    I('venue', 'Venue cost', 120, 'money')], [
    O('Income', 'money', C_INC), O('Instructor time cost', 'money', '{in:hours}*{set:instructor_rate}'), O('Total cost', 'money', C_COST), O('Profit', 'money', '%s-%s' % (C_INC, C_COST)),
    O('Profit per class hour', 'money', 'IFERROR((%s-%s)/{in:hours},0)' % (C_INC, C_COST)), O('Break-even sign-ups', 'int', 'IF({in:price}>0,ROUNDUP(%s/{in:price},0),0)' % C_COST),
    O('Fill of the seats', 'pct', 'IFERROR({in:signups}/{in:seats},0)'), O('Your own fill for this class', 'pct', C_OWNF), O('Your own profit per class hour for this class', 'money', CT('profit_hour')),
    O('Your own profit per session for this class', 'money', C_OWNP), O('Profit against your own average', 'money', '%s-%s-%s' % (C_INC, C_COST, C_OWNP)),
    O('New clients per session from this class', 'num', 'IFERROR(SUMIFS({range:class_sessions.new_clients},{range:class_sessions.class},{in:class})/COUNTIFS({range:class_sessions.class},{in:class}),0)'),
    O('Profit per class hour you want', 'money', '{set:class_hour_target}'),
    O('Verdict', 'text', 'IF(%s-%s<0,%s,IF(IFERROR((%s-%s)/{in:hours},0)>={set:class_hour_target},%s,%s))' % (C_INC, C_COST, ca('Drop'), C_INC, C_COST, ca('Run'), ca('Reprice')))],
    GR('What if', ('4 sign-ups', {'signups': 4}), ('6 sign-ups', {'signups': 6}), ('8 sign-ups', {'signups': 8}), ('10 sign-ups', {'signups': 10}), ('12 sign-ups, full', {'signups': 12}))))

# 5 ------------------------------------------------------------ class break-even solver
B_COST = '({in:venue}+{in:hours}*{set:instructor_rate})'
B_BE = 'IF({in:price}>0,ROUNDUP(%s/{in:price},0),0)' % B_COST
B_AVG = 'IFERROR(AVERAGEIFS({range:class_sessions.signed_up},{range:class_sessions.class},{in:class}),0)'
tools.append(TOOL('breakeven_tool', 'Class Break-even Solver', 'How many sign-ups cover a session and what price would',
    'Pick a class type and type price, venue cost, hours and seats: the fewest sign-ups that cover venue cost plus instructor time, the sign-ups for your profit per hour, the price needed at your average sign-ups and how often this class missed break-even.', [
    IL('class', 'Class', 'ctype', 'Partner workshop'), I('price', 'Price per seat', 45, 'money'), I('venue', 'Venue cost', 112, 'money'), I('hours', 'Class hours', 2.5), I('seats', 'Seats', 12, 'int')], [
    O('Fixed cost of one session', 'money', B_COST), O('Sign-ups to break even', 'int', B_BE),
    O('Sign-ups for your profit per hour', 'int', 'IF({in:price}>0,ROUNDUP((%s+{in:hours}*{set:class_hour_target})/{in:price},0),0)' % B_COST),
    O('Seats left over at break-even', 'int', '{in:seats}-%s' % B_BE), O('Your average sign-ups for this class', 'num', 'ROUND(%s,1)' % B_AVG),
    O('Price at break-even for your average sign-ups', 'money', 'IFERROR(ROUND(%s/%s,2),0)' % (B_COST, B_AVG)), O('Price at break-even with full seats', 'money', 'IFERROR(ROUND(%s/{in:seats},2),0)' % B_COST),
    O('Price for your profit target at your average', 'money', 'IFERROR(ROUND((%s+{in:hours}*{set:class_hour_target})/%s,2),0)' % (B_COST, B_AVG)),
    O('Sessions of this class below break-even', 'pct', 'IFERROR(COUNTIFS({range:class_sessions.class},{in:class},{range:class_sessions.above},0)/COUNTIFS({range:class_sessions.class},{in:class}),0)'),
    O('Verdict', 'text', 'IF(%s>{in:seats},%s,%s&" "&%s&" "&ROUND(%s,1))' % (B_BE, c2('Cannot break even with these seats'), B_BE, c2('sign-ups needed, you averaged'), B_AVG))],
    GR('What if', ('Price 40', {'price': 40}), ('Price 50', {'price': 50}), ('Price 60', {'price': 60}), ('Venue cost 80', {'venue': 80}), ('Venue cost 150', {'venue': 150}))))

# 6 ------------------------------------------------------------ class calendar planner
M_AVG = 'COUNTIFS(%s)/12' % DM('class_sessions.date', 12)
M_SAME = 'COUNTIFS({range:class_sessions.month},EDATE({in:month},-12))'
MNAME = 'CHOOSE(MONTH({in:month}),%s)' % ','.join(tok('mname', m) for m in MNAMES)
M_SESS = 'COUNTIFS(%s)' % DM('class_sessions.date', 12)
tools.append(TOOL('calendar_tool', 'Class Calendar Planner', 'Does a month have enough class sessions and how much income to expect',
    'Pick a month and type the sessions you plan: the same month last year, your monthly average, the quiet months, the seats to fill and the income to expect at your own averages.', [
    I('month', 'Month to plan (first day)', iso(add_months(month_start(0), 1)), 'date'), I('planned', 'Sessions planned', 2, 'int')], [
    O('Sessions in the same month last year', 'int', M_SAME), O('Income in the same month last year', 'money', 'SUMIFS({range:class_sessions.income},{range:class_sessions.month},EDATE({in:month},-12))'),
    O('Sessions a month, last 12 months', 'num', 'ROUND(%s,1)' % M_AVG), O('Quiet months in the last 12', 'int', 'SUMPRODUCT(({range:review_month.month}>EDATE(%s,-13))*({range:review_month.month}<%s)*(COUNTIFS({range:class_sessions.month},{range:review_month.month})<%s/24))' % (MS, MS, M_SESS)),
    O('Seats per session, last 12 months', 'num', 'IFERROR(ROUND(SUMIFS({range:class_sessions.seats},%s)/%s,1),0)' % (DM('class_sessions.date', 12), M_SESS)),
    O('Seats to fill at your fill target', 'num', 'IFERROR(ROUND({in:planned}*SUMIFS({range:class_sessions.seats},%s)/%s*{set:class_fill_target},0),0)' % (DM('class_sessions.date', 12), M_SESS)),
    O('Sign-ups to expect', 'num', 'IFERROR(ROUND({in:planned}*SUMIFS({range:class_sessions.signed_up},%s)/%s,0),0)' % (DM('class_sessions.date', 12), M_SESS)),
    O('Income to expect', 'money', 'IFERROR(ROUND({in:planned}*SUMIFS({range:class_sessions.income},%s)/%s,0),0)' % (DM('class_sessions.date', 12), M_SESS)),
    O('Verdict', 'text', 'IF({in:planned}<%s,%s,%s)&" "&%s' % (M_AVG, c2('Add a session in'), c2('Enough sessions in'), MNAME))],
    GR('What if', ('1 session', {'planned': 1}), ('3 sessions', {'planned': 3}), ('4 sessions', {'planned': 4}), ('5 sessions', {'planned': 5}), ('6 sessions', {'planned': 6}))))

# 7 ------------------------------------------------------------ review and testimonial pipeline
R_FIRST = 'SUMPRODUCT(({range:clients.attended_on}>0)*({range:clients.attended_on}+{in:ask}<={today})*({range:clients.attended_on}>={today}-{in:back})*({range:clients.status}<>%s)*(COUNTIF({range:reviews.client_id},{range:clients.client_id})=0))' % tok('cstatus', 'Cancelled')
R_ASKED = 'COUNTIFS({range:reviews.asked_on},">="&({today}-{in:back}))'
R_ANS = 'COUNTIFS({range:reviews.asked_on},">="&({today}-{in:back}),{range:reviews.answered},1)'
R_REM = 'COUNTIFS({range:reviews.asked_on},">="&({today}-{in:back}),{range:reviews.asked_on},"<="&({today}-{in:ask}),{range:reviews.answered},0)'
tools.append(TOOL('review_pipeline', 'Review Pipeline', 'How many clients to ask for a review today and how many to remind',
    'Type the days after the birth to ask and the days back to look: clients due a first request, reminders due, requests waiting, the answer rate against your target and the average stars; read from Clients and Reviews.', [
    I('ask', 'Days after the birth to ask', 14, 'int'), I('back', 'Days back to look', 120, 'int')], [
    O('Clients due a first request', 'int', R_FIRST), O('Reminders due', 'int', R_REM), O('Requests waiting for an answer', 'int', 'COUNTIFS({range:reviews.asked_on},">"&({today}-{in:ask}),{range:reviews.answered},0)'),
    O('Requests asked in the period', 'int', R_ASKED), O('Answers from those requests', 'int', R_ANS), O('Answer rate', 'pct', 'IFERROR(%s/%s,0)' % (R_ANS, R_ASKED)), O('Answer rate you want', 'pct', '{set:review_rate_min}'),
    O('Average stars in the period', 'num', 'IFERROR(ROUND(AVERAGEIFS({range:reviews.stars},{range:reviews.received_on},">="&({today}-{in:back})),2),0)'),
    O('Average stars you want', 'num', '{set:star_target}'),
    O('Verdict', 'text', 'IF(%s+%s>0,%s&": "&%s&", "&%s&" "&%s,%s)' % (R_FIRST, R_REM, c2('Ask clients today'), R_FIRST, c2('Reminders to send'), R_REM, c2('No review requests due')))],
    GR('What if', ('Ask after 7 days', {'ask': 7}), ('Ask after 21 days', {'ask': 21}), ('Ask after 30 days', {'ask': 30}), ('Look back 60 days', {'back': 60}), ('Look back 180 days', {'back': 180}))))

# 8 ------------------------------------------------------------ review rate by doula and channel
V_OLD = '{range:reviews.asked_on},"<="&({today}-{set:review_ask_days})'
tools.append(TOOL('review_rate', 'Review Rate by Doula', 'Which doula or channel needs more review requests',
    'Pick a doula and a channel: requests asked, answers, the answer rate and the average stars of that doula against the whole team, and the answers and stars of that channel; requests asked in the last ask days are not counted yet.', [
    IL('doula', 'Doula', 'doula', 'Priya Raman'), IL('channel', 'Channel', 'channel', 'Online listing')], [
    O('Requests asked of this doula', 'int', 'COUNTIFS({range:reviews.doula},{in:doula},%s)' % V_OLD), O('Answers', 'int', 'COUNTIFS({range:reviews.doula},{in:doula},%s,{range:reviews.answered},1)' % V_OLD),
    O('Answer rate of this doula', 'pct', 'IFERROR(COUNTIFS({range:reviews.doula},{in:doula},%s,{range:reviews.answered},1)/COUNTIFS({range:reviews.doula},{in:doula},%s),0)' % (V_OLD, V_OLD)),
    O('Answer rate of the whole team', 'pct', 'IFERROR(COUNTIFS(%s,{range:reviews.answered},1)/COUNTIFS(%s),0)' % (V_OLD, V_OLD)),
    O('Average stars of this doula', 'num', 'IFERROR(ROUND(AVERAGEIFS({range:reviews.stars},{range:reviews.doula},{in:doula}),2),0)'), O('Average stars of the whole team', 'num', 'IFERROR(ROUND(AVERAGE({range:reviews.stars}),2),0)'),
    O('Answers on this channel', 'int', 'COUNTIFS({range:reviews.channel},{in:channel})'), O('Share of all answers on this channel', 'pct', 'IFERROR(COUNTIFS({range:reviews.channel},{in:channel})/SUM({range:reviews.answered}),0)'),
    O('Average stars on this channel', 'num', 'IFERROR(ROUND(AVERAGEIFS({range:reviews.stars},{range:reviews.channel},{in:channel}),2),0)'), O('Answer rate you want', 'pct', '{set:review_rate_min}'),
    O('Verdict', 'text', 'IF(IFERROR(COUNTIFS({range:reviews.doula},{in:doula},%s,{range:reviews.answered},1)/COUNTIFS({range:reviews.doula},{in:doula},%s),0)<MIN({set:review_rate_min},IFERROR(COUNTIFS(%s,{range:reviews.answered},1)/COUNTIFS(%s),0)),%s,%s)' % (V_OLD, V_OLD, V_OLD, V_OLD, c2('Ask more often'), c2('Steady')))],
    GR('What if', ('Amara Okonkwo', {'doula': '=' + tok('doula', 'Amara Okonkwo')}), ('Mei-Ling Chen', {'doula': '=' + tok('doula', 'Mei-Ling Chen')}), ('Fatou Diop', {'doula': '=' + tok('doula', 'Fatou Diop')}),
       ('Own website', {'channel': '=' + tok('channel', 'Own website')}), ('Private note', {'channel': '=' + tok('channel', 'Private note')}))))

# 9 ------------------------------------------------------------ marketing keep or drop
K_COST = 'SUMIFS({range:marketing.cost},{range:marketing.kind},{in:kind},%s)' % MM('{in:months}')
K_ENQ = 'SUMIFS({range:marketing.enquiries},{range:marketing.kind},{in:kind},%s)' % MM('{in:months}')
K_SGN = 'SUMIFS({range:marketing.signed},{range:marketing.kind},{in:kind},%s)' % MM('{in:months}')
K_AVG = 'IFERROR(AVERAGEIFS({range:contracts.price},%s,{range:contracts.status},"<>"&%s),0)' % (DM('contracts.signed_on', '{in:months}'), CANC)
K_CPS = 'IF(%s>0,%s/%s,%s)' % (K_SGN, K_COST, K_SGN, K_COST)
tools.append(TOOL('mkt_keepdrop', 'Marketing Keep or Drop', 'Is a listing, post or flyer worth what it costs',
    'Pick a kind of marketing and the months to look back: cost, enquiries, signed clients, cost per signed client, the income of those clients at your average price and months to pay back; the verdict uses the cost per signed client you accept.', [
    IL('kind', 'Kind of marketing', 'mkind', 'Local flyers'), I('months', 'Months to look back', 12, 'int')], [
    O('Cost', 'money', K_COST), O('Enquiries', 'int', K_ENQ), O('Signed clients', 'int', K_SGN), O('Cost per enquiry', 'money', 'IFERROR(%s/%s,0)' % (K_COST, K_ENQ)),
    O('Cost per signed client', 'money', K_CPS), O('Average price of a client contract', 'money', K_AVG), O('Income of the signed clients', 'money', '%s*%s' % (K_SGN, K_AVG)),
    O('Income for every unit spent', 'num', 'IFERROR(%s*%s/%s,0)' % (K_SGN, K_AVG, K_COST)), O('Months of that income to pay back the cost', 'num', 'IFERROR(%s/(%s*%s/{in:months}),0)' % (K_COST, K_SGN, K_AVG)),
    O('Cost per signed client you accept', 'money', '{set:cac_max}'),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s<={set:cac_max},%s,IF(%s<=3*{set:cac_max},%s,%s)))' % (K_SGN, ca('Drop'), K_CPS, ca('Keep'), K_CPS, ca('Renegotiate'), ca('Drop')))],
    GR('What if', ('Online listing', {'kind': '=' + tok('mkind', 'Online listing')}), ('Website upkeep', {'kind': '=' + tok('mkind', 'Website upkeep')}), ('Social posts', {'kind': '=' + tok('mkind', 'Social posts')}),
       ('Event stand', {'kind': '=' + tok('mkind', 'Event stand')}), ('Referral thank-yous', {'kind': '=' + tok('mkind', 'Referral thank-yous')}))))

# 10 ----------------------------------------------------------- referral conversion by referrer type
def CV_E(s): return 'COUNTIFS({range:enquiries.source},%s,%s)' % (s, DM('enquiries.date', '{in:months}'))
def CV_S(s): return 'COUNTIFS({range:enquiries.source},%s,{range:enquiries.status},%s,%s)' % (s, SIGNED, DM('enquiries.date', '{in:months}'))
def CV(s): return 'IFERROR(%s/%s,0)' % (CV_S(s), CV_E(s))
CVMAX = 'MAX(%s)' % ','.join(CV(s) for s in (CARE, PAST, SUPP, CLSS))
CVNAME = 'IF(%s=%s,%s,IF(%s=%s,%s,IF(%s=%s,%s,%s)))' % (CV(CARE), CVMAX, CARE, CV(PAST), CVMAX, PAST, CV(SUPP), CVMAX, SUPP, CLSS)
tools.append(TOOL('conv_type', 'Referral Conversion', 'Which type of referrer sends enquiries that become clients',
    'Type the months to look back: enquiries and signed clients from care providers, past clients, support professionals and classes, the share that signed for each and for all enquiries, and the type that converts best.', [
    I('months', 'Months to look back', 12, 'int')], [
    O('Care provider enquiries', 'int', CV_E(CARE)), O('Care provider clients signed', 'int', CV_S(CARE)), O('Care provider conversion', 'pct', CV(CARE)),
    O('Past client enquiries', 'int', CV_E(PAST)), O('Past client clients signed', 'int', CV_S(PAST)), O('Past client conversion', 'pct', CV(PAST)),
    O('Support professional enquiries', 'int', CV_E(SUPP)), O('Support professional clients signed', 'int', CV_S(SUPP)), O('Support professional conversion', 'pct', CV(SUPP)),
    O('Class enquiries', 'int', CV_E(CLSS)), O('Class clients signed', 'int', CV_S(CLSS)), O('Class conversion', 'pct', CV(CLSS)),
    O('Conversion of all enquiries', 'pct', 'IFERROR(COUNTIFS({range:enquiries.status},%s,%s)/COUNTIFS(%s),0)' % (SIGNED, DM('enquiries.date', '{in:months}'), DM('enquiries.date', '{in:months}'))),
    O('Best conversion of the four', 'pct', CVMAX), O('Verdict', 'text', '%s&": "&%s' % (c2('Converts best'), CVNAME))],
    GR('What if', ('Last 3 months', {'months': 3}), ('Last 6 months', {'months': 6}), ('Last 18 months', {'months': 18}), ('Last 24 months', {'months': 24}), ('Last 36 months', {'months': 36}))))

# 11 ----------------------------------------------------------- class to client funnel
F_SESS = 'COUNTIFS({range:class_sessions.class},{in:class},%s)' % DM('class_sessions.date', '{in:months}')
F_ATT = 'SUMIFS({range:class_sessions.attended},{range:class_sessions.class},{in:class},%s)' % DM('class_sessions.date', '{in:months}')
F_NEW = 'SUMIFS({range:class_sessions.new_clients},{range:class_sessions.class},{in:class},%s)' % DM('class_sessions.date', '{in:months}')
F_PROF = 'SUMIFS({range:class_sessions.profit},{range:class_sessions.class},{in:class},%s)' % DM('class_sessions.date', '{in:months}')
F_AVG = 'IFERROR(AVERAGEIFS({range:contracts.price},%s,{range:contracts.status},"<>"&%s),0)' % (DM('contracts.signed_on', '{in:months}'), CANC)
tools.append(TOOL('class_funnel', 'Class to Client Funnel', 'Do classes bring clients or are they only a cost',
    'Pick a class type and the months to look back: sessions, sign-ups, attendees, new clients, clients per 100 attendees, the profit and the value of the new clients at your average contract price; enquiries and clients from classes are shown for all class types.', [
    IL('class', 'Class', 'ctype', 'Newborn workshop'), I('months', 'Months to look back', 12, 'int')], [
    O('Sessions', 'int', F_SESS), O('Sign-ups', 'int', 'SUMIFS({range:class_sessions.signed_up},{range:class_sessions.class},{in:class},%s)' % DM('class_sessions.date', '{in:months}')),
    O('Attendees', 'int', F_ATT), O('New clients from this class', 'int', F_NEW), O('New clients per 100 attendees', 'num', 'IFERROR(ROUND(100*%s/%s,1),0)' % (F_NEW, F_ATT)),
    O('Profit of this class', 'money', F_PROF), O('Average price of a client contract', 'money', F_AVG), O('Value of the new clients', 'money', '%s*%s' % (F_NEW, F_AVG)),
    O('Enquiries from classes, all types', 'int', 'COUNTIFS({range:enquiries.source},%s,%s)' % (CLSS, DM('enquiries.date', '{in:months}'))),
    O('Clients from classes, all types', 'int', 'COUNTIFS({range:contracts.source},%s,%s,{range:contracts.status},"<>"&%s)' % (CLSS, DM('contracts.signed_on', '{in:months}'), CANC)),
    O('Income of clients from classes', 'money', 'SUMIFS({range:contracts.price},{range:contracts.source},%s,%s,{range:contracts.status},"<>"&%s)' % (CLSS, DM('contracts.signed_on', '{in:months}'), CANC)),
    O('Verdict', 'text', 'IF(AND(%s>0,%s+%s*%s>0),%s,%s)' % (F_NEW, F_PROF, F_NEW, F_AVG, c2('Classes bring clients'), c2('Classes are a cost')))],
    GR('What if', ('Education series', {'class': '=' + tok('ctype', 'Education series')}), ('Partner workshop', {'class': '=' + tok('ctype', 'Partner workshop')}), ('Planning workshop', {'class': '=' + tok('ctype', 'Planning workshop')}),
       ('Infant care evening', {'class': '=' + tok('ctype', 'Infant care evening')}), ('24 months', {'months': 24}))))

# 12 ----------------------------------------------------------- class pricing test
P_SUP = 'MIN({in:seats},{in:seats}*{in:fill}*(1+{in:resp}))'
P_SUM = '{in:seats}*{in:fill}*(1-{in:resp})'
P_SAS = '{in:seats}*{in:fill}'
P_COST = '({in:venue}+{in:hours}*{set:instructor_rate})'
P_DN = '(%s*{in:price}*0.9-%s)' % (P_SUP, P_COST)
P_AS = '(%s*{in:price}-%s)' % (P_SAS, P_COST)
P_UP = '(%s*{in:price}*1.1-%s)' % (P_SUM, P_COST)
tools.append(TOOL('price_test', 'Class Pricing Test', 'Would a price 10% lower or 10% higher earn more from a class',
    'Type the price, seats, your own fill, hours, venue cost and how many sign-ups you gain or lose for a 10% price change: sign-ups, profit and profit per class hour at -10%, as is and +10%, and whether to raise, hold or lower.', [
    I('price', 'Price per seat', 55, 'money'), I('seats', 'Seats', 12, 'int'), I('fill', 'Your own fill of the seats', 0.71, 'pct'), I('hours', 'Class hours', 3), I('venue', 'Venue cost', 112, 'money'),
    I('resp', 'Sign-ups gained or lost for a 10% price change', 0.08, 'pct')], [
    O('Price at -10%', 'money', '{in:price}*0.9'), O('Sign-ups at -10%', 'num', 'ROUND(%s,1)' % P_SUP), O('Profit at -10%', 'money', P_DN), O('Profit per class hour at -10%', 'money', 'IFERROR(%s/{in:hours},0)' % P_DN),
    O('Sign-ups as is', 'num', 'ROUND(%s,1)' % P_SAS), O('Profit as is', 'money', P_AS), O('Profit per class hour as is', 'money', 'IFERROR(%s/{in:hours},0)' % P_AS),
    O('Price at +10%', 'money', '{in:price}*1.1'), O('Sign-ups at +10%', 'num', 'ROUND(%s,1)' % P_SUM), O('Profit at +10%', 'money', P_UP), O('Profit per class hour at +10%', 'money', 'IFERROR(%s/{in:hours},0)' % P_UP),
    O('Profit per class hour you want', 'money', '{set:class_hour_target}'),
    O('Verdict', 'text', 'IF(AND(%s>%s,%s>=%s),%s,IF(%s>%s,%s,%s))' % (P_UP, P_AS, P_UP, P_DN, c2('Raise the price'), P_DN, P_AS, c2('Lower the price'), c2('Hold the price')))],
    GR('What if', ('No change in sign-ups', {'resp': 0}), ('5% change in sign-ups', {'resp': 0.05}), ('10% change in sign-ups', {'resp': 0.10}), ('15% change in sign-ups', {'resp': 0.15}), ('25% change in sign-ups', {'resp': 0.25}))))

# 13 ----------------------------------------------------------- class fill forecast
def FM(k): return 'EDATE(%s,%d)' % (MS, k)
SCF = 'IF({in:scenario}=%s,{set:scen_best},IF({in:scenario}=%s,{set:scen_worst},1))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
AVGI = 'SUMIFS({range:class_sessions.income},%s)/12' % DM('class_sessions.date', 12)
def FC(k): return '(0.5*SUMIFS({range:class_sessions.income},{range:class_sessions.month},EDATE(%s,-12))+0.5*%s)*{in:trend}*%s' % (FM(k), AVGI, SCF)
tools.append(TOOL('fill_forecast', 'Class Fill Forecast', 'How much class income to expect in the next 3 months',
    'Pick a scenario and type a trend factor: each of the next 3 months blends the same month last year with your 12-month average, so a quiet December shows, then applies the trend and the Base, Best or Worst multiplier from Settings.', [
    IL('scenario', 'Scenario', 'scen', 'Base'), I('trend', 'Trend factor (100% = no change)', 1.05, 'pct')], [
    O('Month 1', 'date', FM(1)), O('Income to expect, month 1', 'money', 'ROUND(%s,0)' % FC(1)), O('Month 2', 'date', FM(2)), O('Income to expect, month 2', 'money', 'ROUND(%s,0)' % FC(2)),
    O('Month 3', 'date', FM(3)), O('Income to expect, month 3', 'money', 'ROUND(%s,0)' % FC(3)), O('Income to expect, 3 months', 'money', 'ROUND(%s+%s+%s,0)' % (FC(1), FC(2), FC(3))),
    O('Income of the last 3 months', 'money', 'SUMIFS({range:class_sessions.income},{range:class_sessions.month},">="&EDATE(%s,-3),{range:class_sessions.month},"<"&%s)' % (MS, MS)),
    O('Class income, last 12 months', 'money', 'SUMIFS({range:class_sessions.income},%s)' % DM('class_sessions.date', 12)),
    O('Average fill, last 12 months', 'pct', 'IFERROR(SUMIFS({range:class_sessions.signed_up},%s)/SUMIFS({range:class_sessions.seats},%s),0)' % (DM('class_sessions.date', 12), DM('class_sessions.date', 12))),
    O('Fill you want', 'pct', '{set:class_fill_target}'), O('Scenario multiplier', 'pct', SCF),
    O('Verdict', 'text', '%s&" "&ROUND(%s+%s+%s,0)' % (c2('Expect class income of'), FC(1), FC(2), FC(3)))],
    GR('What if', ('Best scenario', {'scenario': '=' + tok('scen', 'Best')}), ('Worst scenario', {'scenario': '=' + tok('scen', 'Worst')}), ('Trend 90%', {'trend': 0.9}), ('Trend 100%', {'trend': 1.0}), ('Trend 120%', {'trend': 1.2}))))

# 14 ----------------------------------------------------------- past-client referral nudge
NG = 'COUNTIFS({range:reviews.nudge},1,{range:reviews.received_on},">="&({today}-{in:back}))'
NG_ROW = 'MATCH(MAX({range:reviews.nudge_date}),{range:reviews.nudge_date},0)'
PC_REF = 'COUNTIFS({range:referrals.source},%s,%s)' % (PAST, DW('referrals.date', 365))
PC_DONE = 'COUNTIFS({range:clients.status},%s)' % tok('cstatus', 'Completed')
PC_CONV = 'IFERROR(SUMIFS({range:referrers.clients},{range:referrers.source},%s)/SUMIFS({range:referrers.referrals},{range:referrers.source},%s),0)' % (PAST, PAST)
tools.append(TOOL('nudge_tool', 'Past-Client Referral Nudge', 'Which past clients to ask for a referral now',
    'Type the days back to look and a gift value: past clients who left a review of your lowest stars or more and have not referred anyone yet, the latest one to ask first, and the referrals, clients and income to expect at your own rates.', [
    I('back', 'Days back to look at reviews', 180, 'int'), I('gift', 'Gift value for a referral that signs', 15, 'money')], [
    O('Past clients to ask', 'int', NG), O('Ask first', 'text', 'IF(MAX({range:reviews.nudge_date})>0,INDEX({range:reviews.client},%s),"")' % NG_ROW),
    O('Phone of that client', 'text', 'IF(MAX({range:reviews.nudge_date})>0,INDEX({range:reviews.phone},%s),"")' % NG_ROW), O('Stars of that review', 'int', 'IF(MAX({range:reviews.nudge_date})>0,INDEX({range:reviews.stars},%s),0)' % NG_ROW),
    O('Past-client referrals, last 12 months', 'int', PC_REF), O('Clients who finished their care', 'int', PC_DONE),
    O('Referrals per client who finished', 'pct', 'IFERROR(%s/%s,0)' % (PC_REF, PC_DONE)), O('Share of past-client referrals that signed', 'pct', PC_CONV),
    O('Referrals to expect from this list', 'num', 'ROUND(%s*IFERROR(%s/%s,0),1)' % (NG, PC_REF, PC_DONE)), O('Clients to expect from this list', 'num', 'ROUND(%s*IFERROR(%s/%s,0)*%s,1)' % (NG, PC_REF, PC_DONE, PC_CONV)),
    O('Income to expect from those clients', 'money', 'ROUND(%s*IFERROR(%s/%s,0)*%s*IFERROR(INDEX({range:src_value.income_client},MATCH(%s,{range:src_value.source},0)),0),0)' % (NG, PC_REF, PC_DONE, PC_CONV, PAST)),
    O('Gift cost if they all sign', 'money', 'ROUND(%s*IFERROR(%s/%s,0)*%s*{in:gift},0)' % (NG, PC_REF, PC_DONE, PC_CONV)),
    O('Verdict', 'text', 'IF(%s>0,%s&": "&INDEX({range:reviews.client},%s),%s)' % (NG, c2('Ask for a referral'), NG_ROW, c2('No past client to ask yet')))],
    GR('What if', ('Look back 60 days', {'back': 60}), ('Look back 90 days', {'back': 90}), ('Look back 365 days', {'back': 365}), ('Gift of 25', {'gift': 25}), ('Gift of 0', {'gift': 0}))))

# 15 ----------------------------------------------------------- gift budget planner
G_COST = 'SUMIFS({range:referrals.gift_cost},%s)' % DW('referrals.date', 365)
G_CLN = 'COUNTIFS({range:contracts.from_referral},1,%s,{range:contracts.status},"<>"&%s)' % (DM('contracts.signed_on', 12), CANC)
G_EXP = '{in:expected}*IFERROR(%s/%s,0)' % (G_COST, G_CLN)
tools.append(TOOL('gift_budget', 'Gift Budget Planner', 'How much to budget for thank-you gifts next year',
    'Type the clients you expect from referrals and your gift budget: the gifts you gave in the last 12 months by source, the gift cost per referral client and the gift cost to expect against your budget.', [
    I('expected', 'Clients from referrals you expect in 12 months', 80, 'int'), I('budget', 'Gift budget for the year', 1800, 'money')], [
    O('Gift cost, last 12 months', 'money', G_COST), O('Thank-you gifts given', 'int', 'COUNTIFS({range:referrals.gift_cost},">0",%s)' % DW('referrals.date', 365)),
    O('Care provider gifts', 'money', 'SUMIFS({range:referrals.gift_cost},{range:referrals.source},%s,%s)' % (CARE, DW('referrals.date', 365))),
    O('Past client gifts', 'money', 'SUMIFS({range:referrals.gift_cost},{range:referrals.source},%s,%s)' % (PAST, DW('referrals.date', 365))),
    O('Support professional gifts', 'money', 'SUMIFS({range:referrals.gift_cost},{range:referrals.source},%s,%s)' % (SUPP, DW('referrals.date', 365))),
    O('Clients from referrals, last 12 months', 'int', G_CLN), O('Gift cost per referral client', 'money', 'IFERROR(%s/%s,0)' % (G_COST, G_CLN)),
    O('Gift cost to expect', 'money', 'ROUND(%s,0)' % G_EXP), O('Room left in your budget', 'money', '{in:budget}-ROUND(%s,0)' % G_EXP), O('Budget set in Settings', 'money', '{set:gift_budget_year}'),
    O('Verdict', 'text', 'IF(%s<={in:budget},%s&": "&ROUND(%s,0),%s)' % (G_EXP, c2('Budget for gifts'), G_EXP, c2('Over the gift setting')))],
    GR('What if', ('50 clients', {'expected': 50}), ('100 clients', {'expected': 100}), ('120 clients', {'expected': 120}), ('Budget 1200', {'budget': 1200}), ('Budget 2400', {'budget': 2400}))))

# 16 ----------------------------------------------------------- review score tracker
def RM(c, m='{in:month}'): return 'IFERROR(INDEX({range:review_month.%s},MATCH(%s,{range:review_month.month},0)),0)' % (c, m)
S_NOW = RM('avg_stars')
S_3M = 'IFERROR(AVERAGEIFS({range:reviews.stars},{range:reviews.received_on},">="&EDATE({in:month},-3),{range:reviews.received_on},"<"&{in:month}),0)'
S_LY = RM('avg_stars', 'EDATE({in:month},-12)')
tools.append(TOOL('score_tracker', 'Review Score Tracker', 'Are your review stars slipping, steady or improving',
    'Pick a month (first day): the stars of that month against the 3 months before and the same month last year, the answers and the answer rate, and your share of four and five star reviews.', [
    I('month', 'Month to check (first day)', iso(month_start(1)), 'date')], [
    O('Answers received in the month', 'int', RM('received')), O('Average stars of the month', 'num', S_NOW), O('Average stars, 3 months before', 'num', 'ROUND(%s,2)' % S_3M),
    O('Average stars, same month last year', 'num', S_LY), O('Change against the 3 months before', 'num', 'ROUND(%s-%s,2)' % (S_NOW, S_3M)), O('Change against last year', 'num', 'ROUND(%s-%s,2)' % (S_NOW, S_LY)),
    O('Answer rate of requests asked in the month', 'pct', RM('rate')), O('Four and five star share, last 12 months', 'pct', 'IFERROR(COUNTIFS({range:reviews.good},1,%s)/COUNTIFS({range:reviews.answered},1,%s),0)' % (DM('reviews.received_on', 12), DM('reviews.received_on', 12))),
    O('Average stars you want', 'num', '{set:star_target}'),
    O('Verdict', 'text', 'IF(%s<%s-0.1,%s,IF(%s>%s+0.1,%s,%s))' % (S_NOW, S_3M, c2('Stars slipping'), S_NOW, S_3M, c2('Stars improving'), c2('Stars steady')))],
    GR('What if', ('Two months ago', {'month': '=' + 'EDATE(%s,-2)' % MS}), ('Three months ago', {'month': '=' + 'EDATE(%s,-3)' % MS}), ('Six months ago', {'month': '=' + 'EDATE(%s,-6)' % MS}),
       ('Nine months ago', {'month': '=' + 'EDATE(%s,-9)' % MS}), ('A year ago', {'month': '=' + 'EDATE(%s,-12)' % MS}))))

# 17 ----------------------------------------------------------- source mix risk
X_CNT = 'COUNTIFS({range:contracts.source},{range:sources.source},%s,{range:contracts.status},"<>"&%s)' % (DM('contracts.signed_on', '{in:months}'), CANC)
X_TOT = 'COUNTIFS(%s,{range:contracts.status},"<>"&%s)' % (DM('contracts.signed_on', '{in:months}'), CANC)
X_TOP = 'SUMPRODUCT(MAX(%s))' % X_CNT
X_2ND = 'SUMPRODUCT(LARGE(%s,2))' % X_CNT
X_NAME = 'INDEX({range:sources.source},SUMPRODUCT(MAX((%s=%s)*IFERROR(MATCH({range:sources.source},{range:sources.source},0),0))))' % (X_CNT, X_TOP)
X_POS = 'IFERROR(MATCH({range:sources.source},{range:sources.source},0),0)'
X_P1 = 'SUMPRODUCT(MAX((%s=%s)*%s))' % (X_CNT, X_TOP, X_POS)
X_NAME2 = 'INDEX({range:sources.source},SUMPRODUCT(MAX((%s=%s)*(%s<>%s)*%s)))' % (X_CNT, X_2ND, X_POS, X_P1, X_POS)
tools.append(TOOL('mix_risk', 'Source Mix Risk', 'Do too many clients come from one source',
    'Type the months to look back and the highest share you accept from one source: the top source and its share, the top two together, how many of the 8 sources brought a client and a concentration index; the verdict names a source you rely on too much.', [
    I('months', 'Months to look back', 12, 'int'), I('limit', 'Highest share you accept from one source', 0.30, 'pct')], [
    O('Clients signed in the period', 'int', X_TOT), O('Top source', 'text', X_NAME), O('Clients from the top source', 'int', X_TOP), O('Share of clients from the top source', 'pct', 'IFERROR(%s/%s,0)' % (X_TOP, X_TOT)),
    O('Second source', 'text', X_NAME2), O('Share from the top two sources', 'pct', 'IFERROR((%s+%s)/%s,0)' % (X_TOP, X_2ND, X_TOT)),
    O('Sources that brought a client', 'int', 'SUMPRODUCT(--(%s>0))' % X_CNT), O('Concentration index (1 = one source)', 'num', 'IFERROR(ROUND(SUMPRODUCT((%s/%s)^2),3),0)' % (X_CNT, X_TOT)),
    O('Share you accept', 'pct', '{in:limit}'),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s,0)>{in:limit},%s&" "&%s,%s)' % (X_TOP, X_TOT, c2('Too reliant on'), X_NAME, c2('Sources are spread')))],
    GR('What if', ('Accept 20%', {'limit': 0.20}), ('Accept 25%', {'limit': 0.25}), ('Accept 35%', {'limit': 0.35}), ('Last 6 months', {'months': 6}), ('Last 24 months', {'months': 24}))))

# 18 ----------------------------------------------------------- care-provider office planner
def RFO(c): return 'IFERROR(INDEX({range:referrers.%s},MATCH({in:office},{range:referrers.referrer},0)),0)' % c
O_NOW, O_BEF = RFO('last12'), RFO('prev12')
O_CHG = 'IFERROR(%s/%s-1,0)' % (O_NOW, O_BEF)
tools.append(TOOL('office_planner', 'Care Provider Office Planner', 'Which care-provider office to visit, thank or leave alone',
    'Type an office name as it appears in Referrer Ranking and the fall in referrals that needs a visit: referrals in the last 12 months against the 12 before, clients, income, the last referral, thank-yous due and the rank by trend among the offices.', [
    I('office', 'Office', D.DEF_DECLINE, 'text'), I('drop', 'Fall in referrals that needs a visit', 0.25, 'pct')], [
    O('Referrals, last 12 months', 'int', O_NOW), O('Referrals, 12 months before', 'int', O_BEF), O('Change', 'pct', O_CHG),
    O('Clients, last 12 months', 'int', 'COUNTIFS({range:referrals.referrer},{in:office},{range:referrals.signed},1,%s)' % DW('referrals.date', 365)),
    O('Income of all its clients', 'money', RFO('income')), O('Last referral', 'date', 'IFERROR(IF(INDEX({range:referrers.last_referral},MATCH({in:office},{range:referrers.referrer},0))=0,"",INDEX({range:referrers.last_referral},MATCH({in:office},{range:referrers.referrer},0))),"")'),
    O('Days since the last referral', 'int', 'IFERROR({today}-INDEX({range:referrers.last_referral},MATCH({in:office},{range:referrers.referrer},0)),0)'), O('Thank-yous due', 'int', RFO('due_n')),
    O('Care-provider offices', 'int', 'COUNTIFS({range:referrers.source},%s)' % CARE), O('Rank by trend (1 = falling the most)', 'int', 'IFERROR(COUNTIFS({range:referrers.source},%s,{range:referrers.trend},"<"&%s)+1,0)' % (CARE, RFO('trend'))),
    O('Office falling the most', 'text', 'IFERROR(INDEX({range:referrers.referrer},MATCH(MIN({range:referrers.office_trend}),{range:referrers.office_trend},0)),"")'), O('Its change in referrals', 'int', 'MIN({range:referrers.office_trend})'),
    O('Verdict', 'text', 'IF(OR(AND(%s=0,%s>0),AND(%s>0,%s<=-{in:drop})),%s,IF(%s>0,%s,%s))' % (O_NOW, O_BEF, O_BEF, O_CHG, ca('Visit'), RFO('due_n'), ca('Thank'), ca('Hold')))],
    GR('What if', ('Visit at a fall of 10%', {'drop': 0.10}), ('Visit at a fall of 20%', {'drop': 0.20}), ('Visit at a fall of 30%', {'drop': 0.30}), ('Visit at a fall of 50%', {'drop': 0.50}), ('Visit at a fall of 70%', {'drop': 0.70}))))
assert len(tools) == 18, len(tools)
