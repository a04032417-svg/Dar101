"""Author and self-publisher suite part 5: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au5_lists import *
import au5_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def BYROLE(role): return 'IFERROR(INDEX({range:team.phone},MATCH(%s,{range:team.role},0))&"","")' % tok('role', role)
def NAMEROLE(role): return 'IFERROR(INDEX({range:team.name},MATCH(%s,{range:team.role},0))&"","")' % tok('role', role)
def VA_PH(): return CA('va_phone', 'Assistant phone', 'text', BYROLE('Virtual assistant'), 18)
def VA_NAME(): return CA('va_name', 'Assistant name', 'text', NAMEROLE('Virtual assistant'), 20)
def AU_PH(): return CA('author_phone', 'Author phone', 'text', BYROLE('Author-publisher'), 18)
def CO_PH(): return CA('coord_phone', 'Launch coordinator phone', 'text', BYROLE('Launch coordinator'), 18)
def CO_NM(): return CA('coord_name', 'Launch coordinator name', 'text', NAMEROLE('Launch coordinator'), 20)
def AD_NM(): return CA('ad_name', 'Ad specialist name', 'text', NAMEROLE('Ad specialist'), 20)
def DS_NM(): return CA('designer_name', 'Cover designer name', 'text', NAMEROLE('Cover designer'), 20)
def COMPANY_(): return CA('company', 'Imprint', 'text', '{set:company}', 20)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
OPEN = tok('taskstatus', 'Open'); DONE = tok('taskstatus', 'Done')
POSTED = tok('arcstatus', 'Review posted'); NOTSENT = tok('arcstatus', 'Not sent'); NOREPLY = tok('arcstatus', 'No reply'); REMINDED = tok('arcstatus', 'Reminded'); COPYSENT = tok('arcstatus', 'Copy sent')
NEXTREL = 'INDEX({range:titles.release_date},MATCH({set:next_title},{range:titles.title},0))'


def STEPDAYS(step_tok): return 'INDEX({range:steps.days_from_release},MATCH(%s,{range:steps.step},0))' % step_tok


settings = [
    S('company', 'Your imprint name', 'text', COMPANY),
    S('next_title', 'Title of your next launch', 'list', key('title', D.NEXT_TITLE), list='title'),
    S('late_limit', 'Late launch steps you accept before you delay', 'int', 3),
    S('review_rate_target', 'Reviews you want per copy sent (your own number)', 'pct', 0.55),
    S('reviewer_drop_rate', 'Response rate under which a reviewer is removed', 'pct', 0.25),
    S('min_copies', 'Copies a reviewer needs before you judge them', 'int', 3),
    S('remind_days', 'Days after sending before a reminder', 'int', 21),
    S('drop_days', 'Days after sending before you mark no reply', 'int', 45),
    S('open_rate_target', 'Open rate you want (your own number)', 'pct', 0.45),
    S('cost_per_sub_limit', 'Highest cost per new subscriber you accept', 'money', 1.0),
    S('sub_value', 'Royalties one new reader brings in a year (your own number)', 'money', 0.5),
    S('copy_royalty', 'Royalty per copy sold from a send or swap (your own number)', 'money', 2.9),
    S('swap_time_cost', 'Cost of your time for one swap, even a free one', 'money', 10),
    S('payback_target', 'Payback you want from a swap (1.00 = paid back)', 'pct', 1.0),
    S('good_send_pct', 'A send is good above this share of your average', 'pct', 1.2),
    S('weak_send_pct', 'A send is weak below this share of your average', 'pct', 0.8),
    S('list_start', 'Newsletter list size when the first month began', 'int', 1900),
    S('list_target', 'List size you want in 6 months', 'int', 5500),
    S('launch_ad_budget', 'Ad budget you plan for a launch', 'money', 300),
    S('dependant_weight', 'Days a late step counts for each later step waiting on it', 'num', 2),
]
assert 3 <= len(settings) <= 20

tables = []
# ---------------------------------------------------------------- 1 launch tasks
tables.append(T('tasks', 'Launch Tasks', 'Launch checklist steps with day counts and late flags',
    'One row per launch step of a title: owner, due date and done date; the days from release, days late, the late flag and the later steps waiting on it fill in by themselves.', [
    C('task_id', 'Step ID', 'text', 10, required=True), REF('title_id', 'Title ID', 'titles.title_id', 10), REF('title', 'Title', 'titles.title', 26), LST('step', 'Step', 'step', 22), REF('owner', 'Owner', 'team.name', 20), LST('owner_role', 'Owner role', 'ownerrole', 17),
    C('due_date', 'Due date', 'date', 11), C('done_on', 'Done on', 'date', 11), LST('status', 'Status', 'taskstatus', 9),
    CA('release_date', 'Release date', 'date', LKD('titles.release_date', 'titles.title', 'title'), 11),
    CA('days_from_release', 'Days from release', 'int', 'IF({col:release_date}="","",{col:due_date}-{col:release_date})', 9),
    CA('days_to_due', 'Days to due', 'int', 'IF({col:status}=%s,{col:due_date}-{today},"")' % OPEN, 9),
    CA('days_late', 'Days late', 'int', 'IF({col:status}=%s,MAX(0,{col:done_on}-{col:due_date}),MAX(0,{today}-{col:due_date}))' % DONE, 9),
    CA('late_flag', 'Step check', 'text', 'IF({col:status}=%s,IF({col:done_on}<={col:due_date},%s,%s),IF({col:due_date}<{today},%s,IF({col:due_date}-{today}<=7,%s,%s)))' % (
        DONE, ca('Done on time'), ca('Done late'), ca('Late'), ca('Due soon'), ca('Not due yet')), 14),
    CA('open_key', 'Open order key', 'num', 'IF({col:status}=%s,{col:due_date}+VALUE(RIGHT({col:task_id},3))/1000,99999)' % OPEN, 11),
    CA('later_open', 'Later steps still open', 'int', 'IF({col:status}=%s,COUNTIFS({range:tasks.title},{col:title},{range:tasks.status},%s,{range:tasks.due_date},">"&{col:due_date}),0)' % (OPEN, OPEN), 10),
    CA('owner_phone', 'Owner phone', 'text', LKT('team.phone', 'team.name', 'owner'), 18), CO_PH(), CO_NM(), DS_NM(), CA('designer_phone', 'Cover designer phone', 'text', BYROLE('Cover designer'), 18), AU_PH(), COMPANY_()],
    D.tasks_d(), 200, [A('late_flag', '= ' + ca('Late'), 'bad'), A('late_flag', '= ' + ca('Due soon'), 'warn'), A('late_flag', '= ' + ca('Done on time'), 'good')]))
# ---------------------------------------------------------------- 2 launch steps
tables.append(T('steps', 'Launch Steps', 'The 13 launch steps, days from release and owner role',
    'One row per standard launch step with its day count from the release day (minus is before) and the role that owns it; the launch plans and the readiness check read these days.', [
    LST('step', 'Step', 'step', 24, required=True), C('days_from_release', 'Days from release', 'int', 12), LST('owner_role', 'Owner role', 'ownerrole', 20)],
    D.steps_d(), 50))
# ---------------------------------------------------------------- 3 reviewers
tables.append(T('reviewers', 'Reviewers', 'Reviewer list with copies sent and reviews posted',
    'One row per reviewer, blogger, street team member, librarian or bookseller who gets advance copies; copies sent, reviews posted and the response rate fill in from the advance copies.', [
    C('reviewer_id', 'Reviewer ID', 'text', 10, required=True), C('name', 'Name', 'text', 24), LST('kind', 'Kind', 'rkind', 13), C('email', 'E-mail', 'text', 26), C('phone', 'Phone', 'text', 18), C('joined_on', 'Joined on', 'date', 11),
    CA('copies_sent', 'Copies sent', 'int', 'COUNTIFS({range:arcs.reviewer},{col:name},{range:arcs.sent_on},">0")', 9),
    CA('reviews_posted', 'Reviews posted', 'int', 'COUNTIFS({range:arcs.reviewer},{col:name},{range:arcs.status},%s)' % POSTED, 9),
    CA('posted_12m', 'Posted, last 12 months', 'int', 'COUNTIFS({range:arcs.reviewer},{col:name},{range:arcs.posted_on},">="&({today}-365))', 10),
    CA('response_rate', 'Response rate', 'pct', 'IF({col:copies_sent}>0,{col:reviews_posted}/{col:copies_sent},"")', 10), COMPANY_()],
    D.reviewers_d(), 200, [A('response_rate', '< {set:reviewer_drop_rate}', 'warn')]))
# ---------------------------------------------------------------- 4 advance copies
tables.append(T('arcs', 'Advance Copies', 'Advance copies with sent, due and posted dates',
    'One row per advance copy (a free copy sent to a reviewer before release): dates and status; the days since sent, the days to a review and the overdue check fill in by themselves.', [
    C('arc_id', 'Copy ID', 'text', 10, required=True), REF('title_id', 'Title ID', 'titles.title_id', 10), REF('title', 'Title', 'titles.title', 26), REF('reviewer', 'Reviewer', 'reviewers.name', 22),
    C('sent_on', 'Sent on', 'date', 11), C('due_on', 'Review due', 'date', 11), C('posted_on', 'Posted on', 'date', 11), LST('status', 'Status', 'arcstatus', 14),
    CA('reviewer_kind', 'Reviewer kind', 'text', LKT('reviewers.kind', 'reviewers.name', 'reviewer'), 13), CA('reviewer_phone', 'Reviewer phone', 'text', LKT('reviewers.phone', 'reviewers.name', 'reviewer'), 18),
    CA('days_since_sent', 'Days since sent', 'int', 'IF({col:sent_on}>0,{today}-{col:sent_on},0)', 9),
    CA('days_to_review', 'Days to a review', 'int', 'IF(AND({col:posted_on}>0,{col:sent_on}>0),{col:posted_on}-{col:sent_on},"")', 9),
    CA('check', 'Copy check', 'text', 'IF({col:status}=%s,%s,IF({col:status}=%s,%s,IF({col:status}=%s,%s,IF({col:due_on}<{today},%s,%s))))' % (
        POSTED, ca('Posted'), NOTSENT, ca('Not sent yet'), NOREPLY, ca('Marked no reply'), ca('Overdue'), ca('Waiting for review')), 16), COMPANY_()],
    D.arcs_d(), 500, [A('check', '= ' + ca('Overdue'), 'bad'), A('check', '= ' + ca('Not sent yet'), 'warn'), A('check', '= ' + ca('Posted'), 'good')]))
# ---------------------------------------------------------------- 5 newsletter sends
tables.append(T('sends', 'Newsletter Sends', 'Newsletter sends with opens, clicks and sales in 7 days',
    'One row per newsletter send: list size, copies sent, opens, clicks, unsubscribes, sign-ups and the sales and royalties in the 7 days after; estimates until the stores pay.', [
    C('send_id', 'Send ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('month', 'Month', 'date', 11), LST('kind', 'Kind', 'skind', 15), C('list_size', 'List size', 'int', 9), C('sent', 'Sent', 'int', 9),
    C('opens', 'Opens', 'int', 9), C('clicks', 'Clicks', 'int', 9), C('unsubscribes', 'Unsubscribes', 'int', 11), C('new_subscribers', 'New subscribers', 'int', 11), C('sales_7d', 'Sales in 7 days', 'int', 10),
    C('royalty_7d', 'Royalties in 7 days', 'money', 12), VA_NAME(), VA_PH(), AU_PH(), COMPANY_()],
    D.sends_d(), 300, [A('unsubscribes', '> 20', 'warn')]))
# ---------------------------------------------------------------- 6 subscribers by source
tables.append(T('subs', 'Subscribers by Source', 'New and lost subscribers by month and source',
    'One row per month and source: new subscribers, lost subscribers and what the source cost; the net gain and the cost per new subscriber fill in by themselves.', [
    C('row_id', 'Row ID', 'text', 9, required=True), C('month', 'Month', 'date', 11), LST('source', 'Source', 'subsource', 16), C('new_subscribers', 'New subscribers', 'int', 11), C('lost', 'Lost', 'int', 8), C('cost', 'Cost', 'money', 11),
    CA('net', 'Net gain', 'int', '{col:new_subscribers}-{col:lost}', 9), CA('cost_per_sub', 'Cost per new subscriber', 'money', 'IF({col:new_subscribers}>0,{col:cost}/{col:new_subscribers},0)', 12)],
    D.subs_d(), 400, [A('cost_per_sub', '> {set:cost_per_sub_limit}', 'warn')]))
# ---------------------------------------------------------------- 7 swaps and promotions
tables.append(T('swaps', 'Swaps and Promotions', 'Newsletter swaps and paid promotions with readers gained',
    'One row per swap (you and a partner author mention each other) or paid promotion: partner, title, cost, readers gained, clicks and sales in 7 days; the results sheet works out the payback.', [
    C('swap_id', 'Swap ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('partner', 'Partner', 'text', 20), C('phone', 'Phone', 'text', 18), LST('kind', 'Kind', 'swapkind', 15), REF('title', 'Title promoted', 'titles.title', 26),
    C('cost', 'Cost', 'money', 10), C('subscribers', 'Subscribers gained', 'int', 11), C('clicks', 'Clicks', 'int', 8), C('sales_7d', 'Sales in 7 days', 'int', 10)],
    D.swaps_d(), 200))
# ---------------------------------------------------------------- 8 titles
tables.append(T('titles', 'Titles', 'Titles with release date, pre-orders and launch readiness',
    'One row per title: pen name, series, release date, status and pre-orders (sales taken before release); the days to release, the launch steps, advance copies and the key dates fill in by themselves.', [
    C('title_id', 'Title ID', 'text', 10, required=True), C('title', 'Title', 'text', 28), LST('pen_name', 'Pen name', 'penname', 17), LST('series', 'Series', 'series', 20), C('release_date', 'Release date', 'date', 11),
    LST('status', 'Status', 'tstatus', 13), C('preorders', 'Pre-orders', 'int', 10),
    CA('days_to_release', 'Days to release', 'int', '{col:release_date}-{today}', 9),
    CA('total_steps', 'Launch steps', 'int', 'COUNTIFS({range:tasks.title},{col:title})', 8), CA('open_steps', 'Steps open', 'int', 'COUNTIFS({range:tasks.title},{col:title},{range:tasks.status},%s)' % OPEN, 8),
    CA('percent_ready', 'Percent ready', 'pct', 'IF({col:total_steps}>0,COUNTIFS({range:tasks.title},{col:title},{range:tasks.status},%s)/{col:total_steps},0)' % DONE, 9),
    CA('unsent_copies', 'Advance copies not sent', 'int', 'COUNTIFS({range:arcs.title},{col:title},{range:arcs.status},%s)' % NOTSENT, 10),
    CA('reviews_posted', 'Reviews posted', 'int', 'COUNTIFS({range:arcs.title},{col:title},{range:arcs.status},%s)' % POSTED, 9),
    CA('response_rate', 'Response rate', 'pct', 'IF(COUNTIFS({range:arcs.title},{col:title},{range:arcs.sent_on},">0")>0,{col:reviews_posted}/COUNTIFS({range:arcs.title},{col:title},{range:arcs.sent_on},">0"),0)', 9),
    CA('ad_budget', 'Launch ad budget', 'money', '{set:launch_ad_budget}', 11),
    CA('copies_out_on', 'Reviewer copies out by', 'date', '{col:release_date}+%s' % STEPDAYS(tok('step', 'Reviewer copies sent')), 11),
    CA('teaser_on', 'Newsletter teaser on', 'date', '{col:release_date}+%s' % STEPDAYS(tok('step', 'Newsletter teaser')), 11),
    CA('reminders_on', 'Reviewer reminders on', 'date', '{col:release_date}+%s' % STEPDAYS(tok('step', 'Reviewer reminders')), 11),
    CA('ads_on', 'Ads ready by', 'date', '{col:release_date}+%s' % STEPDAYS(tok('step', 'Ads prepared')), 11),
    CA('price_on', 'Launch price set by', 'date', '{col:release_date}+%s' % STEPDAYS(tok('step', 'Launch price set')), 11),
    CA('thanks_on', 'Thank the reviewers on', 'date', '{col:release_date}+%s' % STEPDAYS(tok('step', 'Thank the reviewers')), 11),
    VA_NAME(), VA_PH(), CO_PH(), CO_NM(), AD_NM(), CA('ad_phone', 'Ad specialist phone', 'text', BYROLE('Ad specialist'), 18), AU_PH(), COMPANY_()],
    D.titles_d(), 100, [A('status', '= ' + tok('tstatus', 'Pre-order'), 'good'), A('open_steps', '> 0', 'warn')]))
# ---------------------------------------------------------------- 9 team
tables.append(T('team', 'Team', 'The author, assistant, freelancers and service providers',
    'One row per person you work with: role, phone and e-mail; a freelancer is paid per job, the assistant by the hour, and these phones feed the message links.', [
    C('person_id', 'Person ID', 'text', 10, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 18), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26)],
    D.team_d(), 50))
# ---------------------------------------------------------------- 10 sales by title and month
tables.append(T('titlesales', 'Sales by Title and Month', 'Copies and royalties by title and month',
    'One row per title and month: copies sold in all stores and formats and the royalties in your home currency (estimates until the payment arrives); the launch results read the first 12 months from here.', [
    REF('title', 'Title', 'titles.title', 28, required=True), C('month', 'Month', 'date', 11), C('units', 'Copies', 'int', 9), C('royalties', 'Royalties and page reads', 'money', 13)],
    D.titlesales_d(), 700))
# ---------------------------------------------------------------- 11 launch results
REL_M = 'DATE(YEAR({col:release_date}),MONTH({col:release_date}),1)'
tables.append(T('launchres', 'Launch Results', 'Launch results against your own launch share',
    'One row per launch: the copies of the first 7 and 30 days and the pre-orders from your store reports; the 12-month copies, launch share and verdict against your own average fill in.', [
    REF('title', 'Title', 'titles.title', 28, required=True), C('copies_7d', 'Copies, first 7 days', 'int', 10), C('copies_30d', 'Copies, first 30 days', 'int', 10), C('royalties_30d', 'Royalties, first 30 days', 'money', 12),
    C('copies_12m_typed', 'Copies in 12 months, typed', 'int', 11), C('pre_30', 'Pre-orders 30 days before', 'int', 11), C('pre_total', 'Pre-orders at release', 'int', 11),
    CA('release_date', 'Release date', 'date', LKD('titles.release_date', 'titles.title', 'title'), 11),
    CA('copies_12m', 'Copies, first 12 months', 'int', 'IF(SUMIFS({range:titlesales.units},{range:titlesales.title},{col:title},{range:titlesales.month},%s)>0,SUMIFS({range:titlesales.units},{range:titlesales.title},{col:title},{range:titlesales.month},">="&%s,{range:titlesales.month},"<"&EDATE(%s,12)),{col:copies_12m_typed})' % (REL_M, REL_M, REL_M), 11),
    CA('share_7d', 'Launch share, 7 days', 'pct', 'IF({col:copies_12m}>0,{col:copies_7d}/{col:copies_12m},0)', 10),
    CA('launch_share', 'Launch share, 30 days', 'pct', 'IF({col:copies_12m}>0,{col:copies_30d}/{col:copies_12m},0)', 10),
    CA('royalty_copy', 'Royalty per copy, 30 days', 'money', 'IF({col:copies_30d}>0,{col:royalties_30d}/{col:copies_30d},0)', 10),
    CA('own_avg', 'Your average launch share', 'pct', 'AVERAGE({range:launchres.launch_share})', 10),
    CA('diff_pts', 'Difference to your average', 'pct', '{col:launch_share}-{col:own_avg}', 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:launch_share}>={col:own_avg},%s,IF({col:launch_share}>={col:own_avg}*0.9,%s,%s))' % (c3('Launch worked'), c3('In line with my average'), c3('Weaker than my average')), 20),
    CO_PH(), CO_NM(), COMPANY_()],
    D.launchres_d(), 60, [A('verdict', '= ' + c3('Weaker than my average'), 'warn'), A('verdict', '= ' + c3('Launch worked'), 'good')]))
# ---------------------------------------------------------------- 12 launch readiness (next launch)
tables.append(T('readiness', 'Launch Readiness', 'The next launch step by step',
    'One row per standard step for the launch chosen on Start: due date from the release date, done date, days late, a check and the order in which to finish the open steps; the percent done fills in.', [
    LST('step', 'Step', 'step', 24, required=True),
    CA('due_date', 'Due date', 'date', '%s+%s' % (NEXTREL, STEPDAYS('{col:step}')), 11), CA('owner_role', 'Owner role', 'text', LKT('steps.owner_role', 'steps.step', 'step'), 18),
    CA('done', 'Done', 'int', 'IF(COUNTIFS({range:tasks.title},{set:next_title},{range:tasks.step},{col:step},{range:tasks.status},%s)>0,1,0)' % DONE, 7),
    CA('done_on', 'Done on', 'date', 'IF({col:done}=1,IF(SUMIFS({range:tasks.done_on},{range:tasks.title},{set:next_title},{range:tasks.step},{col:step})=0,"",SUMIFS({range:tasks.done_on},{range:tasks.title},{set:next_title},{range:tasks.step},{col:step})),"")', 11),
    CA('days_late', 'Days late', 'int', 'IF({col:done}=1,0,MAX(0,{today}-{col:due_date}))', 8),
    CA('check', 'Step check', 'text', 'IF({col:done}=1,%s,IF({col:due_date}<{today},%s,IF({col:due_date}-{today}<=7,%s,%s)))' % (ca('Done'), ca('Late'), ca('Due soon'), ca('Not due yet')), 13),
    CA('todo_no', 'Order to finish', 'int', 'IF({col:done}=1,0,COUNTIFS({range:readiness.done},0,{range:readiness.due_date},"<"&{col:due_date})+1)', 9),
    CA('percent_done', 'Percent of steps done', 'pct', 'SUM({range:readiness.done})/COUNT({range:readiness.done})', 10)],
    D.readiness_d(), 50, [A('check', '= ' + ca('Late'), 'bad'), A('check', '= ' + ca('Due soon'), 'warn'), A('check', '= ' + ca('Done'), 'good')]))
# ---------------------------------------------------------------- 13 reviewer ranking
RV = 'reviewer_id'
tables.append(T('ranking', 'Reviewer Ranking', 'Reviewers ranked by response rate and speed',
    'One row per reviewer: copies sent, reviews posted, response rate, average days to a review, a score and the rank; the verdict says keep, test or remove from the list against your own targets.', [
    REF('reviewer_id', 'Reviewer ID', 'reviewers.reviewer_id', 10, required=True),
    CA('name', 'Reviewer', 'text', LKT('reviewers.name', 'reviewers.reviewer_id', 'reviewer_id'), 24), CA('kind', 'Kind', 'text', LKT('reviewers.kind', 'reviewers.reviewer_id', 'reviewer_id'), 13),
    CA('phone', 'Phone', 'text', LKT('reviewers.phone', 'reviewers.reviewer_id', 'reviewer_id'), 18),
    CA('copies_sent', 'Copies sent', 'int', LKN('reviewers.copies_sent', 'reviewers.reviewer_id', 'reviewer_id'), 9),
    CA('reviews_posted', 'Reviews posted', 'int', LKN('reviewers.reviews_posted', 'reviewers.reviewer_id', 'reviewer_id'), 9),
    CA('response_rate', 'Response rate', 'pct', 'IF({col:copies_sent}>0,{col:reviews_posted}/{col:copies_sent},0)', 10),
    CA('avg_days', 'Average days to a review', 'num', 'IFERROR(AVERAGEIFS({range:arcs.days_to_review},{range:arcs.reviewer},{col:name}),0)', 11),
    CA('score', 'Score', 'num', 'IF({col:copies_sent}=0,-1,{col:response_rate}*100-{col:avg_days}/3-VALUE(RIGHT({col:reviewer_id},3))/1000000)', 9),
    CA('rank', 'Rank', 'int', 'COUNTIFS({range:ranking.score},">"&{col:score})+1', 7),
    CA('weak_key', 'Weakest order key', 'num', 'IF({col:copies_sent}>={set:min_copies},{col:score},9999)', 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:copies_sent}=0,%s,IF(AND({col:copies_sent}>={set:min_copies},{col:response_rate}<{set:reviewer_drop_rate}),%s,IF({col:response_rate}>={set:review_rate_target},%s,%s)))' % (
        ca('Test'), ca('Remove from the list'), ca('Keep'), ca('Test')), 20), COMPANY_()],
    D.ranking_d(), 200, [A('verdict', '= ' + ca('Remove from the list'), 'bad'), A('verdict', '= ' + ca('Keep'), 'good')]))
# ---------------------------------------------------------------- 14 response by title
tables.append(T('responses', 'Response by Title', 'Reviews per 100 copies sent, by title',
    'One row per title: advance copies sent, reviews posted, reviews per 100 copies, copies with no reply and a verdict against your own response target.', [
    REF('title', 'Title', 'titles.title', 28, required=True),
    CA('copies_sent', 'Copies sent', 'int', 'COUNTIFS({range:arcs.title},{col:title},{range:arcs.sent_on},">0")', 9),
    CA('reviews_posted', 'Reviews posted', 'int', 'COUNTIFS({range:arcs.title},{col:title},{range:arcs.status},%s)' % POSTED, 9),
    CA('per_100', 'Reviews per 100 copies', 'num', 'IF({col:copies_sent}>0,{col:reviews_posted}/{col:copies_sent}*100,0)', 10),
    CA('no_reply', 'No reply', 'int', 'COUNTIFS({range:arcs.title},{col:title},{range:arcs.status},%s)+COUNTIFS({range:arcs.title},{col:title},{range:arcs.status},%s)' % (NOREPLY, REMINDED), 9),
    CA('unsent', 'Copies not sent', 'int', 'COUNTIFS({range:arcs.title},{col:title},{range:arcs.status},%s)' % NOTSENT, 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:copies_sent}=0,IF({col:unsent}>0,%s,%s),IF({col:per_100}>={set:review_rate_target}*100,%s,%s))' % (ca('Send more copies'), ca('No copies sent'), ca('Good response'), ca('Low response')), 18)],
    D.responses_d(), 100, [A('verdict', '= ' + ca('Low response'), 'warn'), A('verdict', '= ' + ca('Send more copies'), 'bad'), A('verdict', '= ' + ca('Good response'), 'good')]))
# ---------------------------------------------------------------- 15 send results
tables.append(T('sendres', 'Send Results', 'Each send against your own average of the same kind',
    'One row per send: open, click and unsubscribe rates and royalties in 7 days per 1,000 readers, set against your own average for the same kind of send, with a verdict.', [
    REF('send_id', 'Send ID', 'sends.send_id', 9, required=True),
    CA('date', 'Date', 'date', LKD('sends.date', 'sends.send_id', 'send_id'), 11), CA('kind', 'Kind', 'text', LKT('sends.kind', 'sends.send_id', 'send_id'), 15),
    CA('open_rate', 'Open rate', 'pct', 'IFERROR(INDEX({range:sends.opens},MATCH({col:send_id},{range:sends.send_id},0))/INDEX({range:sends.sent},MATCH({col:send_id},{range:sends.send_id},0)),0)', 9),
    CA('click_rate', 'Click rate', 'pct', 'IFERROR(INDEX({range:sends.clicks},MATCH({col:send_id},{range:sends.send_id},0))/INDEX({range:sends.sent},MATCH({col:send_id},{range:sends.send_id},0)),0)', 9),
    CA('unsub_rate', 'Unsubscribe rate', 'pct', 'IFERROR(INDEX({range:sends.unsubscribes},MATCH({col:send_id},{range:sends.send_id},0))/INDEX({range:sends.sent},MATCH({col:send_id},{range:sends.send_id},0)),0)', 10),
    CA('rpk', 'Royalties per 1,000 readers', 'money', 'IFERROR(INDEX({range:sends.royalty_7d},MATCH({col:send_id},{range:sends.send_id},0))/INDEX({range:sends.list_size},MATCH({col:send_id},{range:sends.send_id},0))*1000,0)', 12),
    CA('kind_avg', 'Your average, same kind', 'money', 'AVERAGEIFS({range:sendres.rpk},{range:sendres.kind},{col:kind})', 12),
    CA('vs_avg', 'Against your average', 'pct', 'IF({col:kind_avg}>0,{col:rpk}/{col:kind_avg},0)', 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:vs_avg}>={set:good_send_pct},%s,IF({col:vs_avg}<{set:weak_send_pct},%s,%s))' % (c2('Good send'), c2('Weak send'), c2('Average send')), 14), AU_PH(), COMPANY_()],
    D.sendres_d(), 300, [A('verdict', '= ' + c2('Weak send'), 'warn'), A('verdict', '= ' + c2('Good send'), 'good')]))
# ---------------------------------------------------------------- 16 list growth by month
tables.append(T('growth', 'List Growth by Month', 'Newsletter list size and growth by month',
    'One row per month: sends, new and lost subscribers, net growth, the list size at month end, open and click rates and royalties in 7 days; all counted from the sends and sources sheets.', [
    C('month', 'Month', 'date', 11, required=True),
    CA('sends', 'Sends', 'int', 'COUNTIFS({range:sends.month},{col:month})', 7), CA('new', 'New subscribers', 'int', 'SUMIFS({range:subs.new_subscribers},{range:subs.month},{col:month})', 10),
    CA('lost', 'Lost subscribers', 'int', 'SUMIFS({range:subs.lost},{range:subs.month},{col:month})', 10), CA('net', 'Net growth', 'int', '{col:new}-{col:lost}', 8),
    CA('list_size', 'List size at month end', 'int', '{set:list_start}+SUMIFS({range:subs.new_subscribers},{range:subs.month},"<="&{col:month})-SUMIFS({range:subs.lost},{range:subs.month},"<="&{col:month})', 11),
    CA('growth_pct', 'Growth percent', 'pct', 'IF({col:list_size}-{col:net}>0,{col:net}/({col:list_size}-{col:net}),0)', 9),
    CA('open_rate', 'Open rate', 'pct', 'IFERROR(SUMIFS({range:sends.opens},{range:sends.month},{col:month})/SUMIFS({range:sends.sent},{range:sends.month},{col:month}),0)', 9),
    CA('click_rate', 'Click rate', 'pct', 'IFERROR(SUMIFS({range:sends.clicks},{range:sends.month},{col:month})/SUMIFS({range:sends.sent},{range:sends.month},{col:month}),0)', 9),
    CA('royalties_7d', 'Royalties in 7 days', 'money', 'SUMIFS({range:sends.royalty_7d},{range:sends.month},{col:month})', 12), AU_PH(), COMPANY_()],
    D.growth_d(), 60, [A('net', '< 0', 'bad')]))
# ---------------------------------------------------------------- 17 cost per subscriber by source
tables.append(T('srccost', 'Cost per Subscriber by Source', 'Cost per new subscriber by source, last 12 months',
    'One row per subscriber source: new subscribers in the last 12 months and the cost per new subscriber; the ranker tool adds the keep or stop verdict.', [
    LST('source', 'Source', 'subsource', 18, required=True),
    CA('new_12m', 'New subscribers, 12 months', 'int', 'SUMIFS({range:subs.new_subscribers},{range:subs.source},{col:source},{range:subs.month},">"&EDATE(%s,-12))' % MS, 12),
    CA('cost_per_sub', 'Cost per subscriber', 'money', 'IF({col:new_12m}>0,SUMIFS({range:subs.cost},{range:subs.source},{col:source},{range:subs.month},">"&EDATE(%s,-12))/{col:new_12m},0)' % MS, 12)],
    D.srccost_d(), 50, [A('cost_per_sub', '> {set:cost_per_sub_limit}', 'warn')]))
# ---------------------------------------------------------------- 18 swap results
tables.append(T('swapres', 'Swap Results', 'Swap payback and a swap again verdict',
    'One row per swap or promotion: cost per subscriber, the royalties and the value of the readers gained against cost plus your time, the payback and a verdict; your own numbers are on Start.', [
    REF('swap_id', 'Swap ID', 'swaps.swap_id', 9, required=True),
    CA('date', 'Date', 'date', LKD('swaps.date', 'swaps.swap_id', 'swap_id'), 11), CA('partner', 'Partner', 'text', LKT('swaps.partner', 'swaps.swap_id', 'swap_id'), 20), CA('phone', 'Partner phone', 'text', LKT('swaps.phone', 'swaps.swap_id', 'swap_id'), 18),
    CA('kind', 'Kind', 'text', LKT('swaps.kind', 'swaps.swap_id', 'swap_id'), 15), CA('cost', 'Cost', 'money', LKN('swaps.cost', 'swaps.swap_id', 'swap_id'), 9),
    CA('subscribers', 'Subscribers gained', 'int', LKN('swaps.subscribers', 'swaps.swap_id', 'swap_id'), 10), CA('sales_7d', 'Sales in 7 days', 'int', LKN('swaps.sales_7d', 'swaps.swap_id', 'swap_id'), 9),
    CA('cost_per_sub', 'Cost per subscriber', 'money', 'IF({col:subscribers}>0,{col:cost}/{col:subscribers},0)', 10),
    CA('royalties', 'Royalties in 7 days', 'money', '{col:sales_7d}*{set:copy_royalty}', 10), CA('value', 'Value of readers gained', 'money', '{col:subscribers}*{set:sub_value}', 11),
    CA('payback', 'Payback', 'pct', '({col:royalties}+{col:value})/({col:cost}+{set:swap_time_cost})', 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:payback}>={set:payback_target},%s,IF({col:payback}>={set:payback_target}*0.6,%s,%s))' % (c2('Swap again'), c2('Change partner'), c2('Stop')), 15),
    CA('partner_swaps', 'Swaps with this partner', 'int', 'COUNTIFS({range:swaps.partner},{col:partner})', 9),
    CA('partner_avg', 'Partner average subscribers', 'num', 'IFERROR(AVERAGEIFS({range:swaps.subscribers},{range:swaps.partner},{col:partner}),0)', 11),
    CA('next_slot', 'Next slot', 'date', '{col:date}+28', 11), AU_PH(), COMPANY_()],
    D.swapres_d(), 100, [A('verdict', '= ' + c2('Stop'), 'bad'), A('verdict', '= ' + c2('Change partner'), 'warn'), A('verdict', '= ' + c2('Swap again'), 'good')]))
# ---------------------------------------------------------------- 19 newsletter to sales by kind
tables.append(T('kindsales', 'Newsletter to Sales by Kind', 'Sends and royalties per 1,000 readers by kind of send',
    'One row per kind of send: the sends in the last 12 months and the average royalties in 7 days per 1,000 readers; the compare tool turns it into a send more or send fewer verdict.', [
    LST('kind', 'Kind', 'skind', 18, required=True),
    CA('sends_12m', 'Sends, last 12 months', 'int', 'COUNTIFS({range:sends.kind},{col:kind},{range:sends.date},">"&({today}-365))', 11),
    CA('rpk', 'Royalties per 1,000 readers', 'money', 'IFERROR(AVERAGEIFS({range:sendres.rpk},{range:sendres.kind},{col:kind},{range:sendres.date},">"&({today}-365)),0)', 13)],
    D.kindsales_d(), 50))
# ---------------------------------------------------------------- 20 late launch steps
tables.append(T('latesteps', 'Late Launch Steps', 'Late steps first, then the next open steps',
    'Rows 1 to 12: the open steps of all launches in due date order, so the late ones come first; days late, the later steps waiting on each and a score to act first fill in by themselves.', [
    C('rank_no', 'Order', 'int', 7, required=True),
    CA('pos', 'Row in launch tasks', 'int', 'IF(SMALL({range:tasks.open_key},{col:rank_no})<99999,MATCH(SMALL({range:tasks.open_key},{col:rank_no}),{range:tasks.open_key},0),"")', 9),
    CA('title', 'Title', 'text', 'IF({col:pos}="","",INDEX({range:tasks.title},{col:pos}))', 26), CA('step', 'Step', 'text', 'IF({col:pos}="","",INDEX({range:tasks.step},{col:pos}))', 22),
    CA('owner', 'Owner', 'text', 'IF({col:pos}="","",INDEX({range:tasks.owner},{col:pos}))', 20), CA('due_date', 'Due date', 'date', 'IF({col:pos}="","",INDEX({range:tasks.due_date},{col:pos}))', 11),
    CA('days_late', 'Days late', 'int', 'IF({col:pos}="","",INDEX({range:tasks.days_late},{col:pos}))', 8), CA('later_open', 'Later steps waiting', 'int', 'IF({col:pos}="","",INDEX({range:tasks.later_open},{col:pos}))', 9),
    CA('score', 'Act-first score', 'num', 'IF({col:pos}="","",{col:days_late}+{set:dependant_weight}*{col:later_open}-{col:rank_no}/1000)', 9),
    CA('check', 'Step check', 'text', 'IF({col:pos}="","",INDEX({range:tasks.late_flag},{col:pos}))', 13),
    CA('coord_phone', 'Launch coordinator phone', 'text', 'IF({col:pos}="","",%s)' % BYROLE('Launch coordinator'), 18)],
    D.latesteps_d(), 50, [A('check', '= ' + ca('Late'), 'bad'), A('check', '= ' + ca('Due soon'), 'warn')]))
assert len(tables) == 20
