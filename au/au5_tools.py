"""Author and self-publisher suite part 5: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au5_lists import *
import au5_data as D


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def O(label, fmt, f): return OUT(label, fmt, f)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
OPEN = tok('taskstatus', 'Open'); DONE = tok('taskstatus', 'Done'); POSTED = tok('arcstatus', 'Review posted'); REMINDED = tok('arcstatus', 'Reminded'); COPYSENT = tok('arcstatus', 'Copy sent')
NEXTREL = 'INDEX({range:titles.release_date},MATCH({set:next_title},{range:titles.title},0))'
LAST = D.launchres_d()[0]
_R = dd = to_date(D.TD['TL-006']['release_date'])
LAST_12M = sum(v[0] for (tid, m), v in D._AGG.items() if tid == 'TL-006')
PRIOR = D.launchres_d()[1]
def LR(col, t): return 'IFERROR(INDEX({range:launchres.%s},MATCH({in:%s},{range:launchres.title},0)),0)' % (col, t)
LASTTITLE = 'INDEX({range:launchres.title},MATCH(MAX({range:launchres.release_date}),{range:launchres.release_date},0))'
def NTH(n): return 'MATCH(LARGE({range:launchres.release_date},%d),{range:launchres.release_date},0)' % n
OWN_RATE = 'IFERROR(COUNTIFS({range:arcs.status},%s)/COUNTIFS({range:arcs.sent_on},">0"),0)' % POSTED
tools = []

# 1 ------------------------------------------------------------ launch readiness verdict
LATE_R = 'COUNTIFS({range:readiness.check},%s)' % ca('Late')
DAYS_R = '(%s-{today})' % NEXTREL
def STEPN(n, col='step'): return 'IFERROR(INDEX({range:readiness.%s},MATCH(%d,{range:readiness.todo_no},0)),"")' % (col, n)
tools.append(TOOL('ready_tool', 'Launch Readiness Verdict', 'Is the next launch ready to go',
    'Type the late steps you accept and the days before release when one late step means delay; see the percent done, the late steps and the first three steps to finish for the launch on Start.', [
    I('late_limit', 'Late steps you accept', 3, 'int'), I('risk_days', 'Days before release when one late step means delay', 7, 'int')], [
    O('Launch', 'text', '{set:next_title}'), O('Release date', 'date', NEXTREL), O('Days to release', 'int', DAYS_R),
    O('Steps in the plan', 'int', 'COUNT({range:readiness.done})'), O('Steps done', 'int', 'SUM({range:readiness.done})'), O('Percent of steps done', 'pct', 'IFERROR(SUM({range:readiness.done})/COUNT({range:readiness.done}),0)'),
    O('Steps late', 'int', LATE_R), O('Steps due in the next 7 days', 'int', 'COUNTIFS({range:readiness.check},%s)' % ca('Due soon')),
    O('First step to finish', 'text', STEPN(1)), O('Days late, first step', 'int', 'IF(%s="",0,%s)' % (STEPN(1), STEPN(1, 'days_late'))),
    O('Second step to finish', 'text', STEPN(2)), O('Third step to finish', 'text', STEPN(3)),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(OR(%s>{in:late_limit},AND(%s<={in:risk_days},%s>0)),%s,%s))' % (LATE_R, ca('Ready to launch'), LATE_R, DAYS_R, LATE_R, ca('Delay the launch'), ca('At risk')))],
    GR('What if', ('Accept 1 late step', {'late_limit': 1}), ('Accept 2 late steps', {'late_limit': 2}), ('Accept 5 late steps', {'late_limit': 5}), ('Any late step means delay within 30 days', {'risk_days': 30}),
       ('Any late step means delay within 14 days', {'risk_days': 14}))))

# 2 ------------------------------------------------------------ late step ranker
def TOPL(n, col): return 'IFERROR(INDEX({range:latesteps.%s},MATCH(LARGE({range:latesteps.score},%d),{range:latesteps.score},0)),"")' % (col, n)
tools.append(TOOL('late_rank', 'Late Step Ranker', 'Which late launch step to finish first',
    'Open steps are ranked by the days late plus the later steps that wait on each; type the days late at which a step must be done today and how many steps you can finish in a day.', [
    I('today_days', 'Days late at which a step is done today', 10, 'int'), I('per_day', 'Steps you can finish in a day', 2, 'int')], [
    O('Steps late now', 'int', 'COUNTIFS({range:tasks.late_flag},%s)' % ca('Late')), O('Open steps, all launches', 'int', 'COUNTIFS({range:tasks.status},%s)' % OPEN),
    O('First: step', 'text', TOPL(1, 'step')), O('First: title', 'text', TOPL(1, 'title')), O('First: owner', 'text', TOPL(1, 'owner')), O('First: days late', 'int', 'IF(%s="",0,%s)' % (TOPL(1, 'days_late'), TOPL(1, 'days_late'))),
    O('First: later steps waiting', 'int', 'IF(%s="",0,%s)' % (TOPL(1, 'later_open'), TOPL(1, 'later_open'))), O('First: act-first score', 'num', 'IF(%s="",0,%s)' % (TOPL(1, 'score'), TOPL(1, 'score'))),
    O('Second: step', 'text', TOPL(2, 'step')), O('Second: days late', 'int', 'IF(%s="",0,%s)' % (TOPL(2, 'days_late'), TOPL(2, 'days_late'))),
    O('Third: step', 'text', TOPL(3, 'step')), O('Third: days late', 'int', 'IF(%s="",0,%s)' % (TOPL(3, 'days_late'), TOPL(3, 'days_late'))),
    O('Days needed to clear the late steps', 'int', 'ROUNDUP(COUNTIFS({range:tasks.late_flag},%s)/MAX(1,{in:per_day}),0)' % ca('Late')),
    O('Verdict', 'text', 'IF(IF(%s="",0,%s)>={in:today_days},%s,%s)' % (TOPL(1, 'days_late'), TOPL(1, 'days_late'), ca('Do today'), ca('This week')))],
    GR('What if', ('Done today from 5 days late', {'today_days': 5}), ('Done today from 20 days late', {'today_days': 20}), ('One step a day', {'per_day': 1}), ('Four steps a day', {'per_day': 4}))))

# 3 ------------------------------------------------------------ launch result and launch share
OWN30 = 'AVERAGE({range:launchres.launch_share})'
tools.append(TOOL('launch_share', 'Launch Result and Launch Share', 'Did the launch beat your own average launch share',
    'Type the copies in the first 7 and 30 days and in the first 12 months (so far, for a young title); see the launch share against your own average launch share and the copies that would have matched it.', [
    I('copies_7d', 'Copies, first 7 days', LAST['copies_7d'], 'int'), I('copies_30d', 'Copies, first 30 days', LAST['copies_30d'], 'int'), I('copies_12m', 'Copies, first 12 months (so far)', LAST_12M, 'int'),
    I('royalties_30d', 'Royalties, first 30 days', LAST['royalties_30d'])], [
    O('Launch share, 7 days', 'pct', 'IFERROR({in:copies_7d}/{in:copies_12m},0)'), O('Launch share, 30 days', 'pct', 'IFERROR({in:copies_30d}/{in:copies_12m},0)'),
    O('Your average launch share, 30 days', 'pct', OWN30), O('Your average launch share, 7 days', 'pct', 'AVERAGE({range:launchres.share_7d})'),
    O('Difference to your average, 30 days', 'pct', 'IFERROR({in:copies_30d}/{in:copies_12m},0)-%s' % OWN30),
    O('Copies in 30 days that would match your average', 'int', 'ROUNDUP(%s*{in:copies_12m},0)' % OWN30), O('Copies above or below that', 'int', '{in:copies_30d}-ROUNDUP(%s*{in:copies_12m},0)' % OWN30),
    O('Share of the first 30 days in the first week', 'pct', 'IFERROR({in:copies_7d}/{in:copies_30d},0)'), O('Your own first-week share of 30 days', 'pct', 'SUM({range:launchres.copies_7d})/SUM({range:launchres.copies_30d})'),
    O('Royalty per copy, 30 days', 'money', 'IFERROR({in:royalties_30d}/{in:copies_30d},0)'), O('Your own royalty per copy, 30 days', 'money', 'AVERAGE({range:launchres.royalty_copy})'),
    O('Launch share of your last launch', 'pct', 'INDEX({range:launchres.launch_share},MATCH(MAX({range:launchres.release_date}),{range:launchres.release_date},0))'),
    O('Verdict', 'text', 'IF(IFERROR({in:copies_30d}/{in:copies_12m},0)>=%s,%s,IF(IFERROR({in:copies_30d}/{in:copies_12m},0)>=%s*0.9,%s,%s))' % (OWN30, c3('Launch worked'), OWN30, c3('In line with my average'), c3('Weaker than my average')))],
    GR('What if', ('30-day copies 20% lower', {'copies_30d': '=ROUND({in:copies_30d}*0.8,0)'}), ('30-day copies 20% higher', {'copies_30d': '=ROUND({in:copies_30d}*1.2,0)'}),
       ('12-month copies 25% higher', {'copies_12m': '=ROUND({in:copies_12m}*1.25,0)'}), ('A quiet launch', {'copies_7d': 120, 'copies_30d': 260}))))

# 4 ------------------------------------------------------------ launch compare with the last launch
def DP(a, b): return 'IF(%s>0,%s/%s-1,0)' % (b, a, b)
tools.append(TOOL('launch_compare', 'Launch Compare', 'Is this launch better than the last one',
    'Pick two launches; see the copies, launch share and royalties side by side and the difference in percent; a difference inside the flat band counts as flat.', [
    IL('title_a', 'Launch A', 'title', 'The Last Lamp Out'), IL('title_b', 'Launch B', 'title', 'Ashes Under Hollow Lane'), I('flat_band', 'Difference counted as flat', 0.1, 'pct')], [
    O('Copies, 30 days, A', 'int', LR('copies_30d', 'title_a')), O('Copies, 30 days, B', 'int', LR('copies_30d', 'title_b')),
    O('Launch share, 30 days, A', 'pct', LR('launch_share', 'title_a')), O('Launch share, 30 days, B', 'pct', LR('launch_share', 'title_b')),
    O('Copies, 12 months, A', 'int', LR('copies_12m', 'title_a')), O('Copies, 12 months, B', 'int', LR('copies_12m', 'title_b')),
    O('Royalties, 30 days, A', 'money', LR('royalties_30d', 'title_a')), O('Royalties, 30 days, B', 'money', LR('royalties_30d', 'title_b')),
    O('Copies, first 7 days, A', 'int', LR('copies_7d', 'title_a')), O('Copies, first 7 days, B', 'int', LR('copies_7d', 'title_b')),
    O('Difference in 30-day copies, A against B', 'pct', DP(LR('copies_30d', 'title_a'), LR('copies_30d', 'title_b'))),
    O('Difference in launch share, A against B', 'pct', DP(LR('launch_share', 'title_a'), LR('launch_share', 'title_b'))),
    O('Difference in royalties, A against B', 'pct', DP(LR('royalties_30d', 'title_a'), LR('royalties_30d', 'title_b'))),
    O('Verdict', 'text', 'IF(%s>{in:flat_band},%s,IF(%s<-{in:flat_band},%s,%s))' % (DP(LR('copies_30d', 'title_a'), LR('copies_30d', 'title_b')), c3('Better'), DP(LR('copies_30d', 'title_a'), LR('copies_30d', 'title_b')), c3('Worse'), c3('Flat')))],
    GR('What if', ('Flat band 5%', {'flat_band': 0.05}), ('Flat band 25%', {'flat_band': 0.25}), ('Compare the two Lantern Bay launches', {'title_a': '=' + tok('title', 'Knots of Marrow Bay'), 'title_b': '=' + tok('title', 'The Pale Bell Ringers')}),
       ('Compare the box set with a book', {'title_a': '=' + tok('title', 'The Ember Crown Books 1-3'), 'title_b': '=' + tok('title', 'The Hollow Sunrise')}))))

# 5 ------------------------------------------------------------ launch target solver
LPR = 'IFERROR(SUMIFS({range:sends.sales_7d},{range:sends.kind},%s)/SUMIFS({range:sends.sent},{range:sends.kind},%s),0)' % (tok('skind', 'Launch push'), tok('skind', 'Launch push'))
NEED30 = 'ROUNDUP({in:copies_goal}*{in:share_goal},0)'
CAP = 'ROUND({in:list_size}*%s*{in:pushes},0)' % LPR
FROMLIST = 'ROUNDUP(%s*{in:list_part},0)' % NEED30
tools.append(TOOL('launch_target', 'Launch Target Solver', 'How many copies the launch needs and can your list give them',
    'Type the copies you want in 12 months and the launch share you aim for; see the copies needed in the first 7 and 30 days and whether your list, at your own buying rate, can give its part.', [
    I('copies_goal', 'Copies wanted in 12 months', 1800, 'int'), I('share_goal', 'Launch share wanted, first 30 days', 0.30, 'pct'), I('list_size', 'Readers on your list', 4740, 'int'),
    I('pushes', 'Launch sends planned', 3, 'int'), I('list_part', 'Share of launch copies that come from your list', 0.35, 'pct')], [
    O('Copies needed in the first 30 days', 'int', NEED30), O('Copies needed in the first 7 days', 'int', 'ROUNDUP(%s*SUM({range:launchres.copies_7d})/SUM({range:launchres.copies_30d}),0)' % NEED30),
    O('Your average launch share, 30 days', 'pct', OWN30), O('Copies per reader per launch send, your own', 'num', LPR),
    O('Copies your list can give', 'int', CAP), O('Copies needed from your list', 'int', FROMLIST), O('Gap, list capacity less need', 'int', '%s-%s' % (CAP, FROMLIST)),
    O('List size that would cover the need', 'int', 'IFERROR(ROUNDUP(%s/(%s*{in:pushes}),0),0)' % (FROMLIST, LPR)),
    O('Launch share wanted against your average', 'pct', '{in:share_goal}-%s' % OWN30),
    O('Verdict', 'text', 'IF(%s>=%s,%s,%s)' % (CAP, FROMLIST, c3('Reachable from your list'), c3('Stretch')))],
    GR('What if', ('Share wanted 25%', {'share_goal': 0.25}), ('Share wanted 35%', {'share_goal': 0.35}), ('Five launch sends', {'pushes': 5}), ('A list of 7,000', {'list_size': 7000}), ('Goal 1,200 copies', {'copies_goal': 1200}))))

# 6 ------------------------------------------------------------ review target planner
tools.append(TOOL('review_plan', 'Review Target Planner', 'How many advance copies to send for the reviews you want',
    'Type the reviews you want, your own response rate and the copies you can send; see the copies to send with a spare share and whether the copies you have are enough.', [
    I('reviews_wanted', 'Reviews wanted', 25, 'int'), I('response_rate', 'Reviews you get per copy sent', 0.59, 'pct'), I('spare', 'Spare share for copies that bounce', 0.1, 'pct'), I('copies_ready', 'Copies ready to send', 40, 'int')], [
    O('Copies to send', 'int', 'ROUNDUP({in:reviews_wanted}/MAX(0.01,{in:response_rate})*(1+{in:spare}),0)'), O('Reviews expected from the copies ready', 'int', 'ROUND({in:copies_ready}*{in:response_rate},0)'),
    O('Copies short or spare', 'int', '{in:copies_ready}-ROUNDUP({in:reviews_wanted}/MAX(0.01,{in:response_rate})*(1+{in:spare}),0)'),
    O('Your own response rate, all copies', 'pct', OWN_RATE), O('Your response rate on the last launch', 'pct', 'IFERROR(INDEX({range:responses.per_100},MATCH(%s,{range:responses.title},0))/100,0)' % LASTTITLE),
    O('Copies to send at your own rate', 'int', 'ROUNDUP({in:reviews_wanted}/MAX(0.01,%s)*(1+{in:spare}),0)' % OWN_RATE), O('Copies not yet sent, all titles', 'int', 'SUM({range:titles.unsent_copies})'),
    O('Reviewers on your list', 'int', 'COUNTA({range:reviewers.reviewer_id})'), O('Reviewers who posted in the last 12 months', 'int', 'COUNTIFS({range:reviewers.posted_12m},">0")'),
    O('Verdict', 'text', 'IF({in:copies_ready}>=ROUNDUP({in:reviews_wanted}/MAX(0.01,{in:response_rate})*(1+{in:spare}),0),%s,%s)' % (ca('Enough copies'), ca('Send more copies')))],
    GR('What if', ('Response rate 45%', {'response_rate': 0.45}), ('Response rate 70%', {'response_rate': 0.70}), ('40 reviews wanted', {'reviews_wanted': 40}), ('No spare share', {'spare': 0}), ('60 copies ready', {'copies_ready': 60}))))

# 7 ------------------------------------------------------------ reminder scheduler
SHARE_BY = 'IFERROR(COUNTIFS({range:arcs.days_to_review},"<="&{in:days_since})/COUNTIFS({range:arcs.status},%s),0)' % POSTED
EXPECT = '{in:copies_sent}*%s*%s' % (OWN_RATE, SHARE_BY)
tools.append(TOOL('reminder_tool', 'Reminder Scheduler', 'Who to remind today and who to mark as no reply',
    'Type the copies you sent, the days since and the reviews so far; your own history of how fast reviews arrive says if you are behind, then remind, wait or mark the rest as no reply.', [
    I('copies_sent', 'Copies sent in the batch', 40, 'int'), I('days_since', 'Days since the copies were sent', 40, 'int'), I('reviews_so_far', 'Reviews posted so far', 4, 'int'),
    I('remind_after', 'Days after sending to remind', 21, 'int'), I('drop_after', 'Days after sending to mark no reply', 45, 'int')], [
    O('Your own response rate, all copies', 'pct', OWN_RATE), O('Share of your reviews that arrive within these days', 'pct', SHARE_BY),
    O('Reviews expected by now', 'num', EXPECT), O('Reviews missing against that', 'num', 'MAX(0,%s-{in:reviews_so_far})' % EXPECT),
    O('Copies still open', 'int', '{in:copies_sent}-{in:reviews_so_far}'), O('Reviewers to remind today', 'int', 'IF(AND({in:days_since}>={in:remind_after},{in:days_since}<{in:drop_after},{in:reviews_so_far}<%s),{in:copies_sent}-{in:reviews_so_far},0)' % EXPECT),
    O('Copies to mark as no reply', 'int', 'IF({in:days_since}>={in:drop_after},{in:copies_sent}-{in:reviews_so_far},0)'),
    O('Open copies in your list now', 'int', 'COUNTIFS({range:arcs.status},%s)+COUNTIFS({range:arcs.status},%s)' % (COPYSENT, REMINDED)),
    O('Of them past the mark-no-reply day', 'int', 'COUNTIFS({range:arcs.status},%s,{range:arcs.days_since_sent},">="&{in:drop_after})+COUNTIFS({range:arcs.status},%s,{range:arcs.days_since_sent},">="&{in:drop_after})' % (COPYSENT, REMINDED)),
    O('Verdict', 'text', 'IF({in:days_since}>={in:drop_after},%s,IF(AND({in:days_since}>={in:remind_after},{in:reviews_so_far}<%s),%s,%s))' % (ca('Mark no reply'), EXPECT, ca('Remind today'), ca('Wait')))],
    GR('What if', ('10 days since sending', {'days_since': 10}), ('30 days, 2 reviews', {'days_since': 30, 'reviews_so_far': 2}), ('50 days since sending', {'days_since': 50}), ('Plenty of reviews already', {'reviews_so_far': 15}), ('Remind after 14 days', {'remind_after': 14}))))

# 8 ------------------------------------------------------------ reviewer ranking tool
def BESTN(n, col='name'): return 'IFERROR(INDEX({range:ranking.%s},MATCH(%d,{range:ranking.rank},0)),"")' % (col, n)
def WEAKN(n, col='name'): return 'IFERROR(INDEX({range:ranking.%s},MATCH(SMALL({range:ranking.weak_key},%d),{range:ranking.weak_key},0)),"")' % (col, n)
KEEPN = 'COUNTIFS({range:ranking.copies_sent},">="&{in:min_copies},{range:ranking.response_rate},">="&{in:keep_rate})'
REMN = 'COUNTIFS({range:ranking.copies_sent},">="&{in:min_copies},{range:ranking.response_rate},"<"&{in:drop_rate})'
tools.append(TOOL('rank_tool', 'Reviewer Keep or Remove', 'Which reviewers to keep, test or remove from the list',
    'Type the response rate that keeps a reviewer, the rate that removes one and the copies needed before you judge; see the best and the weakest reviewers and how many fall in each group.', [
    I('keep_rate', 'Response rate that keeps a reviewer', 0.55, 'pct'), I('drop_rate', 'Response rate that removes a reviewer', 0.25, 'pct'), I('min_copies', 'Copies before you judge a reviewer', 3, 'int')], [
    O('Best reviewer 1', 'text', BESTN(1)), O('Best reviewer 2', 'text', BESTN(2)), O('Best reviewer 3', 'text', BESTN(3)), O('Best reviewer 4', 'text', BESTN(4)), O('Best reviewer 5', 'text', BESTN(5)),
    O('Response rate of the best reviewer', 'pct', 'IFERROR(%s,0)' % BESTN(1, 'response_rate')),
    O('Weakest reviewer 1', 'text', WEAKN(1)), O('Weakest reviewer 2', 'text', WEAKN(2)), O('Weakest reviewer 3', 'text', WEAKN(3)), O('Weakest reviewer 4', 'text', WEAKN(4)), O('Weakest reviewer 5', 'text', WEAKN(5)),
    O('Response rate of the weakest reviewer', 'pct', 'IFERROR(%s,0)' % WEAKN(1, 'response_rate')),
    O('Reviewers to keep', 'int', KEEPN), O('Reviewers to remove', 'int', REMN), O('Reviewers still to test', 'int', 'COUNTA({range:reviewers.reviewer_id})-%s-%s' % (KEEPN, REMN)),
    O('Average days to a review, all reviewers', 'num', 'IFERROR(AVERAGE({range:arcs.days_to_review}),0)'),
    O('Verdict on the weakest reviewer', 'text', 'IF(%s<{in:drop_rate},%s,IF(%s<{in:keep_rate},%s,%s))' % (WEAKN(1, 'response_rate'), ca('Remove from the list'), WEAKN(1, 'response_rate'), ca('Test'), ca('Keep')))],
    GR('What if', ('Keep from 45%', {'keep_rate': 0.45}), ('Keep from 65%', {'keep_rate': 0.65}), ('Remove under 35%', {'drop_rate': 0.35}), ('Judge after 2 copies', {'min_copies': 2}), ('Judge after 5 copies', {'min_copies': 5}))))

# 9 ------------------------------------------------------------ ARC response analyser
def KR(k): return 'IFERROR(COUNTIFS({range:arcs.reviewer_kind},%s,{range:arcs.status},%s)/COUNTIFS({range:arcs.reviewer_kind},%s,{range:arcs.sent_on},">0"),0)' % (tok('rkind', k), POSTED, tok('rkind', k))
KRS = [KR(k) for k in REVIEWER_KINDS]
tools.append(TOOL('arc_mix', 'ARC Response Analyser', 'Does your reviewer mix give the reviews you need',
    'Pick a title and type the response rate you want; see the response rate of each kind of reviewer, reviews per 100 copies for the title against all titles, and whether the mix works.', [
    IL('title', 'Title', 'title', 'The Last Lamp Out'), I('target_rate', 'Response rate you want', 0.55, 'pct')], [
    O('Response rate: Readers', 'pct', KRS[0]), O('Response rate: Bloggers', 'pct', KRS[1]), O('Response rate: Street team', 'pct', KRS[2]), O('Response rate: Librarians', 'pct', KRS[3]), O('Response rate: Booksellers', 'pct', KRS[4]),
    O('Your response rate, all copies', 'pct', OWN_RATE), O('Highest rate of a kind', 'pct', 'MAX(%s)' % ','.join(KRS)), O('Lowest rate of a kind', 'pct', 'MIN(%s)' % ','.join(KRS)),
    O('Reviews per 100 copies, this title', 'num', 'IFERROR(INDEX({range:responses.per_100},MATCH({in:title},{range:responses.title},0)),0)'),
    O('Reviews per 100 copies, all titles', 'num', 'IFERROR(SUM({range:responses.reviews_posted})/SUM({range:responses.copies_sent})*100,0)'),
    O('This title against all titles', 'pct', 'IFERROR(INDEX({range:responses.per_100},MATCH({in:title},{range:responses.title},0))/(SUM({range:responses.reviews_posted})/SUM({range:responses.copies_sent})*100)-1,0)'),
    O('Verdict', 'text', 'IF(AND(%s>={in:target_rate},MIN(%s)>={in:target_rate}*0.6),%s,%s)' % (OWN_RATE, ','.join(KRS), c3('Reviewer mix works'), c3('Change the mix')))],
    GR('What if', ('Want 50%', {'target_rate': 0.5}), ('Want 65%', {'target_rate': 0.65}), ('Want 75%', {'target_rate': 0.75}), ('Another title', {'title': '=' + tok('title', 'Candle at Gull Point')}))))

# 10 ----------------------------------------------------------- list growth forecast
GN = 'INDEX({range:growth.list_size},MATCH(%s,{range:growth.month},0))' % MS
A12 = '(SUMIFS({range:growth.net},{range:growth.month},">="&EDATE(%s,-12),{range:growth.month},"<"&%s)/12)' % (MS, MS)
A3 = '(SUMIFS({range:growth.net},{range:growth.month},">="&EDATE(%s,-3),{range:growth.month},"<"&%s)/3)' % (MS, MS)
TREND = 'MIN(1.5,MAX(0.5,%s/%s))' % (A3, A12)
def ADJ(s): return {'Base': '0', 'Best': '{in:best_pct}', 'Worst': '{in:worst_pct}'}[s]
def FC(s, m): return '%s+%d*%s*%s*(1+%s)' % (GN, m, A12, TREND, ADJ(s))
SEL = 'IF({in:scenario}=%s,{in:best_pct},IF({in:scenario}=%s,{in:worst_pct},0))' % (tok('scen', 'Best'), tok('scen', 'Worst'))
MONTHLY = '%s*%s*(1+%s)' % (A12, TREND, SEL)
tools.append(TOOL('growth_fc', 'List Growth Forecast', 'Will the newsletter list reach its target size',
    'Pick Base, Best or Worst; the forecast is your last 12 months of net growth times your recent trend, moved up or down by the percents you type, against the list size you want.', [
    IL('scenario', 'Scenario', 'scen', 'Base'), I('best_pct', 'Best case, change in monthly growth', 0.25, 'pct'), I('worst_pct', 'Worst case, change in monthly growth', -0.3, 'pct'), I('target_size', 'List size you want in 6 months', 5500, 'int')], [
    O('List size now', 'int', GN), O('Net growth a month, last 12 months', 'num', A12), O('Trend factor, last 3 months against 12', 'num', TREND),
    O('Base: list in 3 months', 'int', 'ROUND(%s,0)' % FC('Base', 3)), O('Base: list in 6 months', 'int', 'ROUND(%s,0)' % FC('Base', 6)),
    O('Best: list in 3 months', 'int', 'ROUND(%s,0)' % FC('Best', 3)), O('Best: list in 6 months', 'int', 'ROUND(%s,0)' % FC('Best', 6)),
    O('Worst: list in 3 months', 'int', 'ROUND(%s,0)' % FC('Worst', 3)), O('Worst: list in 6 months', 'int', 'ROUND(%s,0)' % FC('Worst', 6)),
    O('Chosen scenario: list in 6 months', 'int', 'ROUND(%s+6*%s,0)' % (GN, MONTHLY)), O('Months to reach the size you want', 'num', 'IF(%s>0,MAX(0,({in:target_size}-%s)/(%s)),0)' % (MONTHLY, GN, MONTHLY)),
    O('Net growth needed a month for the target', 'num', '({in:target_size}-%s)/6' % GN),
    O('Verdict', 'text', 'IF(%s+6*%s>={in:target_size},%s,%s)' % (GN, MONTHLY, c2('On the way to the target'), c2('Behind the target')))],
    GR('What if', ('Best case', {'scenario': '=' + tok('scen', 'Best')}), ('Worst case', {'scenario': '=' + tok('scen', 'Worst')}), ('Target 5,000', {'target_size': 5000}), ('Target 6,500', {'target_size': 6500}), ('Best case plus 50%', {'scenario': '=' + tok('scen', 'Best'), 'best_pct': 0.5}))))

# 11 ----------------------------------------------------------- cost per subscriber ranker
def CPS(k): return 'INDEX({range:srccost.cost_per_sub},MATCH(%s,{range:srccost.source},0))' % tok('subsource', k)
def KEPT(k): return 'IFERROR(1-SUMIFS({range:subs.lost},{range:subs.source},%s,{range:subs.month},">"&EDATE(%s,-12))/SUMIFS({range:subs.new_subscribers},{range:subs.source},%s,{range:subs.month},">"&EDATE(%s,-12)),0)' % (tok('subsource', k), MS, tok('subsource', k), MS)
def VER(k): return 'IF(AND(%s<={in:cost_limit},%s>={in:kept_min}),%s,IF(OR(%s>{in:cost_limit}*2,%s<{in:kept_min}-0.1),%s,%s))' % (CPS(k), KEPT(k), c2('Keep this source'), CPS(k), KEPT(k), c2('Stop this source'), c2('Watch this source'))
src_out = []
for k in SUB_SOURCES:
    src_out += [O('%s: cost per subscriber' % k, 'money', CPS(k)), O('%s: share kept' % k, 'pct', KEPT(k)), O('%s: verdict' % k, 'text', VER(k))]
tools.append(TOOL('source_rank', 'Cost per Subscriber Ranker', 'Which subscriber sources to keep and which to stop',
    'Type the highest cost per new subscriber you accept and the share of new readers who should stay; each source gets its cost, its share kept after the unsubscribes and a keep, watch or stop verdict.', [
    I('cost_limit', 'Highest cost per new subscriber', 1.0), I('kept_min', 'Share of new readers who should stay', 0.7, 'pct')], src_out + [
    O('Most expensive source', 'text', 'INDEX({range:srccost.source},MATCH(MAX({range:srccost.cost_per_sub}),{range:srccost.cost_per_sub},0))'),
    O('New subscribers, last 12 months', 'int', 'SUM({range:srccost.new_12m})')],
    GR('What if', ('Limit 0.50', {'cost_limit': 0.5}), ('Limit 3.00', {'cost_limit': 3}), ('Keep 80% of readers', {'kept_min': 0.8}), ('Keep 60% of readers', {'kept_min': 0.6}))))

# 12 ----------------------------------------------------------- swap payback
RET = '({in:sales_7d}*{in:copy_royalty}+{in:subscribers}*{in:sub_value})'
TOTC = '({in:cost}+{in:time_cost})'
tools.append(TOOL('swap_payback', 'Swap Payback', 'Is this swap or promotion worth repeating',
    'Type the cost, the readers gained and the sales in 7 days, with your own value for a copy and a reader; see the payback, the break-even readers and how many swaps would gain the readers you want.', [
    I('cost', 'Cost of the swap or promotion', 60), I('subscribers', 'Subscribers gained', 95, 'int'), I('sales_7d', 'Sales in 7 days', 12, 'int'), I('copy_royalty', 'Royalty per copy (your own number)', 2.9),
    I('sub_value', 'Royalties one reader brings in a year (your own number)', 0.5), I('time_cost', 'Cost of your time for one swap', 10), I('target_subs', 'Readers you want to gain', 500, 'int')], [
    O('Royalties from the sales', 'money', '{in:sales_7d}*{in:copy_royalty}'), O('Value of the readers gained', 'money', '{in:subscribers}*{in:sub_value}'), O('Total return', 'money', RET),
    O('Total cost with your time', 'money', TOTC), O('Payback', 'pct', 'IFERROR(%s/%s,0)' % (RET, TOTC)), O('Profit or loss', 'money', '%s-%s' % (RET, TOTC)),
    O('Cost per subscriber', 'money', 'IFERROR({in:cost}/{in:subscribers},0)'), O('Subscribers needed to break even', 'int', 'IFERROR(MAX(0,ROUNDUP((%s-{in:sales_7d}*{in:copy_royalty})/{in:sub_value},0)),0)' % TOTC),
    O('Swaps like this to gain the readers you want', 'int', 'IFERROR(ROUNDUP({in:target_subs}/{in:subscribers},0),0)'), O('Cost of those swaps', 'money', 'IFERROR(ROUNDUP({in:target_subs}/{in:subscribers},0)*%s,0)' % TOTC),
    O('Your payback, all swaps of the last 12 months', 'pct', 'IFERROR((SUMIFS({range:swapres.royalties},{range:swapres.date},">"&({today}-365))+SUMIFS({range:swapres.value},{range:swapres.date},">"&({today}-365)))/(SUMIFS({range:swapres.cost},{range:swapres.date},">"&({today}-365))+COUNTIFS({range:swapres.date},">"&({today}-365))*{set:swap_time_cost}),0)'),
    O('Verdict', 'text', 'IF(IFERROR(%s/%s,0)>={set:payback_target},%s,IF(IFERROR(%s/%s,0)>={set:payback_target}*0.6,%s,%s))' % (RET, TOTC, c2('Swap again'), RET, TOTC, c2('Change partner'), c2('Stop')))],
    GR('What if', ('A paid promotion of 180', {'cost': 180}), ('A free swap', {'cost': 0}), ('Only 40 readers gained', {'subscribers': 40, 'sales_7d': 3}), ('Readers worth 1 a year', {'sub_value': 1}), ('Sales 25 in 7 days', {'sales_7d': 25}))))

# 13 ----------------------------------------------------------- swap partner ranker
PN = 'INDEX({range:swapres.partner},{in:row_no})'
PS = 'COUNTIFS({range:swaps.partner},%s)' % PN
def PAVG(c): return 'IFERROR(AVERAGEIFS({range:swaps.%s},{range:swaps.partner},%s),0)' % (c, PN)
def OAVG(c): return 'AVERAGE({range:swaps.%s})' % c
SCORE = '((%s/%s)+(%s/%s)+(%s/%s))/3' % (PAVG('subscribers'), OAVG('subscribers'), PAVG('clicks'), OAVG('clicks'), PAVG('sales_7d'), OAVG('sales_7d'))
tools.append(TOOL('partner_rank', 'Swap Partner Ranker', 'Which partner authors to invite again',
    'Type the row of any swap of the partner on Swap Results (1 is the oldest); see the readers, clicks and sales per swap against your own average of all partners and an invite again or skip verdict.', [
    I('row_no', 'Row of a swap of the partner on Swap Results', 5, 'int'), I('min_swaps', 'Swaps before you judge a partner', 2, 'int')], [
    O('Partner', 'text', PN), O('Swaps with this partner', 'int', PS), O('Subscribers per swap', 'num', PAVG('subscribers')), O('Your average, all partners', 'num', OAVG('subscribers')),
    O('Clicks per swap', 'num', PAVG('clicks')), O('Your average clicks per swap', 'num', OAVG('clicks')), O('Sales in 7 days per swap', 'num', PAVG('sales_7d')), O('Your average sales per swap', 'num', OAVG('sales_7d')),
    O('Average payback with this partner', 'pct', 'IFERROR(AVERAGEIFS({range:swapres.payback},{range:swapres.partner},%s),0)' % PN),
    O('Partner score against your average', 'pct', 'IFERROR(%s,0)' % SCORE),
    O('Best partner, most subscribers per swap', 'text', 'INDEX({range:swapres.partner},MATCH(MAX({range:swapres.partner_avg}),{range:swapres.partner_avg},0))'),
    O('Weakest partner, fewest subscribers per swap', 'text', 'INDEX({range:swapres.partner},MATCH(MIN({range:swapres.partner_avg}),{range:swapres.partner_avg},0))'),
    O('Verdict', 'text', 'IF(AND(%s>={in:min_swaps},IFERROR(%s,0)>=1),%s,IF(%s<{in:min_swaps},%s,%s))' % (PS, SCORE, c2('Invite again'), PS, c2('Invite again'), c2('Skip')))],
    GR('What if', ('Swap row 2', {'row_no': 2}), ('Swap row 9', {'row_no': 9}), ('Swap row 17', {'row_no': 17}), ('Judge after 3 swaps', {'min_swaps': 3}))))

# 14 ----------------------------------------------------------- newsletter to sales
def SR(col): return 'IFERROR(INDEX({range:sendres.%s},{in:send_no}),0)' % col
def SD(col): return 'IFERROR(INDEX({range:sends.%s},{in:send_no}),0)' % col
tools.append(TOOL('nl_sales', 'Newsletter to Sales', 'Did this send earn its keep',
    'Type the row of a send on Newsletter Sends (1 is the oldest); see clicks, sales and royalties in 7 days and royalties per 1,000 readers against your own average of the same kind, with a verdict.', [
    I('send_no', 'Row of the send on Newsletter Sends', 108, 'int')], [
    O('Date of the send', 'date', SR('date')), O('Kind of send', 'text', 'IFERROR(INDEX({range:sendres.kind},{in:send_no}),"")'),
    O('Readers on the list', 'int', SD('list_size')), O('Clicks', 'int', SD('clicks')), O('Sales in 7 days', 'int', SD('sales_7d')), O('Royalties in 7 days', 'money', SD('royalty_7d')),
    O('Sales per 100 clicks', 'num', 'IFERROR(%s/%s*100,0)' % (SD('sales_7d'), SD('clicks'))), O('Open rate', 'pct', SR('open_rate')), O('Click rate', 'pct', SR('click_rate')),
    O('Royalties per 1,000 readers', 'money', SR('rpk')), O('Your average, same kind of send', 'money', SR('kind_avg')), O('Against your average', 'pct', SR('vs_avg')),
    O('Verdict', 'text', 'IF(%s>={set:good_send_pct},%s,IF(%s<{set:weak_send_pct},%s,%s))' % (SR('vs_avg'), c2('Good send'), SR('vs_avg'), c2('Weak send'), c2('Average send')))],
    GR('What if', ('A send 40 rows earlier', {'send_no': 68}), ('A send 10 rows earlier', {'send_no': 98}), ('The newest send', {'send_no': 109}), ('The first send', {'send_no': 1}))))

# 15 ----------------------------------------------------------- send kind compare
def KOR(k, c): return 'IFERROR(SUMIFS({range:sends.%s},{range:sends.kind},%s,{range:sends.date},">"&({today}-365))/SUMIFS({range:sends.sent},{range:sends.kind},%s,{range:sends.date},">"&({today}-365)),0)' % (c, tok('skind', k), tok('skind', k))
kc_out = []
for k in SEND_KINDS:
    kc_out += [O('%s: open rate' % k, 'pct', KOR(k, 'opens')), O('%s: click rate' % k, 'pct', KOR(k, 'clicks')),
               O('%s: royalties per 1,000 readers' % k, 'money', 'IFERROR(INDEX({range:kindsales.rpk},MATCH(%s,{range:kindsales.kind},0)),0)' % tok('skind', k))]
BESTK = 'MAX({range:kindsales.rpk})'; WORSTK = 'MIN({range:kindsales.rpk})'
tools.append(TOOL('kind_compare', 'Send Kind Compare', 'Which kind of send to send more of',
    'Compares the five kinds of send over the last 12 months: open rate, click rate and royalties per 1,000 readers; type how much better the best kind must be before you shift your sends.', [
    I('gap', 'Gap that makes you shift sends', 0.5, 'pct')], kc_out[:15] + [
    O('Send more of', 'text', 'INDEX({range:kindsales.kind},MATCH(%s,{range:kindsales.rpk},0))' % BESTK), O('Send fewer of', 'text', 'INDEX({range:kindsales.kind},MATCH(%s,{range:kindsales.rpk},0))' % WORSTK),
    O('Best kind against the weakest', 'pct', 'IF(%s>0,%s/%s-1,0)' % (WORSTK, BESTK, WORSTK)),
    O('Sends in the last 12 months', 'int', 'SUM({range:kindsales.sends_12m})'),
    O('Verdict', 'text', 'IF(IF(%s>0,%s/%s-1,0)>={in:gap},%s,%s)' % (WORSTK, BESTK, WORSTK, c2('Send more of this'), c2('Send fewer of this')))],
    GR('What if', ('Shift at a gap of 25%', {'gap': 0.25}), ('Shift at a gap of 100%', {'gap': 1.0}), ('Shift at a gap of 200%', {'gap': 2.0}))))

# 16 ----------------------------------------------------------- list clean-up test
RM = '{in:not_opened}'
tools.append(TOOL('cleanup', 'List Clean-up Test', 'Should you remove readers who never open',
    'Type the readers who did not open your last sends and your open rate; see the open rate after removing them, the sending cost saved and the share of the list they are.', [
    I('list_size', 'Readers on your list', 4740, 'int'), I('not_opened', 'Readers who opened none of the last sends', 640, 'int'), I('n_sends', 'Sends counted', 6, 'int'), I('open_rate', 'Open rate now', 0.46, 'pct'),
    I('cost_per_1000', 'Service cost a month per 1,000 readers (your own number)', 4.5), I('clean_share', 'Share of the list that makes you clean it', 0.1, 'pct')], [
    O('Share of the list that never opens', 'pct', 'IFERROR({in:not_opened}/{in:list_size},0)'), O('List size after the clean-up', 'int', '{in:list_size}-{in:not_opened}'),
    O('Open rate after the clean-up', 'pct', 'IFERROR({in:open_rate}*{in:list_size}/({in:list_size}-{in:not_opened}),0)'),
    O('Gain in open rate', 'pct', 'IFERROR({in:open_rate}*{in:list_size}/({in:list_size}-{in:not_opened}),0)-{in:open_rate}'), O('Open rate you want', 'pct', '{set:open_rate_target}'),
    O('Your open rate, last 90 days', 'pct', 'IFERROR(SUMIFS({range:sends.opens},{range:sends.date},">"&({today}-90))/SUMIFS({range:sends.sent},{range:sends.date},">"&({today}-90)),0)'),
    O('Service cost saved a month', 'money', '{in:not_opened}/1000*{in:cost_per_1000}'), O('Service cost saved a year', 'money', '{in:not_opened}/1000*{in:cost_per_1000}*12'),
    O('Royalties per 1,000 readers per send, your own', 'money', 'IFERROR(SUMIFS({range:sends.royalty_7d},{range:sends.date},">"&({today}-365))/SUMIFS({range:sends.list_size},{range:sends.date},">"&({today}-365))*1000,0)'),
    O('Verdict', 'text', 'IF(IFERROR({in:not_opened}/{in:list_size},0)>={in:clean_share},%s,%s)' % (c2('Clean the list'), c2('Keep the list')))],
    GR('What if', ('300 readers never open', {'not_opened': 300}), ('1,000 readers never open', {'not_opened': 1000}), ('Clean at 15%', {'clean_share': 0.15}), ('Service costs 8 per 1,000', {'cost_per_1000': 8}))))

# 17 ----------------------------------------------------------- launch week plan
def STEPDATE(name): return '{in:release}+INDEX({range:steps.days_from_release},MATCH(%s,{range:steps.step},0))' % tok('step', name)
INWIN = 'COUNTIFS({range:steps.days_from_release},">="&-{in:days_before},{range:steps.days_from_release},"<="&{in:days_after})'
LPN = 'COUNTIFS({range:sends.kind},%s)' % tok('skind', 'Launch push')
tools.append(TOOL('week_plan', 'Launch Week Plan', 'Does the launch week plan fit your steps and sends',
    'Type the release date, the days before and after to plan and the newsletter pushes you want; see which steps fall in the window, the dates of the key steps and whether the number of sends fits.', [
    I('release', 'Release date', 'today+28', 'date'), I('days_before', 'Days before release in the plan', 7, 'int'), I('days_after', 'Days after release in the plan', 7, 'int'),
    I('pushes', 'Newsletter pushes planned in the window', 4, 'int'), I('push_limit', 'Most pushes you allow', 5, 'int'), I('min_pushes', 'Fewest pushes you want', 3, 'int')], [
    O('Days to release', 'int', '{in:release}-{today}'), O('Steps that fall in the window', 'int', INWIN),
    O('Steps before release in the window', 'int', 'COUNTIFS({range:steps.days_from_release},">="&-{in:days_before},{range:steps.days_from_release},"<0")'),
    O('Steps on or after release in the window', 'int', 'COUNTIFS({range:steps.days_from_release},">=0",{range:steps.days_from_release},"<="&{in:days_after})'),
    O('Reviewer reminders on', 'date', STEPDATE('Reviewer reminders')), O('Ads prepared by', 'date', STEPDATE('Ads prepared')), O('Launch price set by', 'date', STEPDATE('Launch price set')),
    O('Launch day newsletter on', 'date', STEPDATE('Launch day newsletter')), O('Store pages checked on', 'date', STEPDATE('Store pages checked')), O('Reviewers thanked on', 'date', STEPDATE('Thank the reviewers')),
    O('Pushes planned against your limit', 'int', '{in:push_limit}-{in:pushes}'),
    O('Launch push sends in your history', 'int', LPN),
    O('Launches in your sends history', 'int', 'COUNTIFS({range:titles.release_date},">="&MIN({range:sends.date}),{range:titles.release_date},"<="&{today})'),
    O('Launch pushes per launch, your own', 'num', 'IFERROR(%s/COUNTIFS({range:titles.release_date},">="&MIN({range:sends.date}),{range:titles.release_date},"<="&{today}),0)' % LPN),
    O('Verdict', 'text', 'IF({in:pushes}>{in:push_limit},%s,IF({in:pushes}<{in:min_pushes},%s,%s))' % (c3('Too many sends'), c3('Too few sends'), c3('Plan fits')))],
    GR('What if', ('Seven pushes', {'pushes': 7}), ('Two pushes', {'pushes': 2}), ('Release in 14 days', {'release': '={today}+14'}), ('A wider window of 14 days', {'days_before': 14, 'days_after': 14}))))

# 18 ----------------------------------------------------------- pre-order momentum check
def S30(n): return '(INDEX({range:launchres.pre_30},%s)/INDEX({range:launchres.pre_total},%s))' % (NTH(n), NTH(n))
def EXP(n):
    s = S30(n); d = '{in:days_to_release}'
    return 'INDEX({range:launchres.pre_total},%s)*IF(%s>=30,%s*MAX(0,60-%s)/30,%s+(1-%s)*(30-%s)/30)' % (NTH(n), d, s, d, s, s, d)
AVGX = '((%s)+(%s))/2' % (EXP(1), EXP(2))
tools.append(TOOL('preorder_tool', 'Pre-order Momentum Check', 'Are pre-orders ahead of your last two launches',
    'Type the pre-orders so far and the days to release; your last two launches show their pre-orders at the same point, so you see if you are ahead, on pace or behind.', [
    I('preorders_now', 'Pre-orders so far', 225, 'int'), I('days_to_release', 'Days to release', 28, 'int'), I('band', 'Band counted as on pace', 0.1, 'pct')], [
    O('Last launch', 'text', LASTTITLE), O('Pre-orders at release, last launch', 'int', 'INDEX({range:launchres.pre_total},%s)' % NTH(1)),
    O('Pre-orders at the same point, last launch', 'int', 'ROUND(%s,0)' % EXP(1)), O('Pre-orders at the same point, the launch before', 'int', 'ROUND(%s,0)' % EXP(2)),
    O('Your own pace at this point', 'int', 'ROUND(%s,0)' % AVGX), O('Difference to your own pace', 'pct', 'IFERROR({in:preorders_now}/(%s)-1,0)' % AVGX),
    O('Expected pre-orders at release', 'int', 'ROUND({in:preorders_now}/((%s)/((INDEX({range:launchres.pre_total},%s)+INDEX({range:launchres.pre_total},%s))/2)),0)' % (AVGX, NTH(1), NTH(2))),
    O('Pre-orders needed a day to match the last launch', 'num', 'IF({in:days_to_release}>0,MAX(0,INDEX({range:launchres.pre_total},%s)-{in:preorders_now})/{in:days_to_release},0)' % NTH(1)),
    O('Pre-orders on the title now', 'int', 'IFERROR(INDEX({range:titles.preorders},MATCH({set:next_title},{range:titles.title},0)),0)'),
    O('Verdict', 'text', 'IF({in:preorders_now}>(%s)*(1+{in:band}),%s,IF({in:preorders_now}<(%s)*(1-{in:band}),%s,%s))' % (AVGX, c3('Ahead'), AVGX, c3('Behind'), c3('On pace')))],
    GR('What if', ('200 pre-orders so far', {'preorders_now': 200}), ('300 pre-orders so far', {'preorders_now': 300}), ('150 pre-orders so far', {'preorders_now': 150}), ('Two weeks to release', {'days_to_release': 14, 'preorders_now': 280}), ('Six weeks to release', {'days_to_release': 42, 'preorders_now': 120}))))
assert len(tools) == 18, len(tools)
