"""Author and Self-Publisher Business suite - part 5: Readers, Newsletter and Launches."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from au5_lists import *
from au5_tables import settings, tables
from au5_tools import tools

SUITE = 'fx-20261115-author-publisher'
NOTE = "Sample wording: adapt it to your own business."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
OPEN = tok('taskstatus', 'Open'); DONE = tok('taskstatus', 'Done'); POSTED = tok('arcstatus', 'Review posted'); NOTSENT = tok('arcstatus', 'Not sent'); REMINDED = tok('arcstatus', 'Reminded'); COPYSENT = tok('arcstatus', 'Copy sent')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('launch_plan_sheet', 'Launch Plan Sheet', 'Launch plan for one title', 'titles.title_id', F(
        ('Title', 'titles.title'), ('Pen name', 'titles.pen_name'), ('Series', 'titles.series'), ('Release date', 'titles.release_date'), ('Status', 'titles.status'), ('Pre-orders', 'titles.preorders'),
        ('Days to release', 'titles.days_to_release'), ('Launch steps', 'titles.total_steps'), ('Steps still open', 'titles.open_steps'), ('Percent ready', 'titles.percent_ready'),
        ('Advance copies not sent', 'titles.unsent_copies'), ('Reviews posted', 'titles.reviews_posted')) + [
        FF('Steps late for this title', 'COUNTIFS({range:tasks.title_id},{pick},{range:tasks.late_flag},%s)' % ca('Late'), 'int')],
        {"from": "tasks", "match": "tasks.title_id", "columns": ["step", "owner", "due_date", "done_on", "status", "late_flag"], "max": 14}),
    FORM('step_update_sheet', 'Launch Step Update Sheet', 'Update of one launch step', 'tasks.task_id', F(
        ('Title', 'tasks.title'), ('Step', 'tasks.step'), ('Owner', 'tasks.owner'), ('Owner phone', 'tasks.owner_phone'), ('Release date', 'tasks.release_date'), ('Days from release', 'tasks.days_from_release'),
        ('Due date', 'tasks.due_date'), ('Done on', 'tasks.done_on'), ('Status', 'tasks.status'), ('Days late', 'tasks.days_late'), ('Step check', 'tasks.late_flag')) + [
        FF('Steps still open for this title', 'COUNTIFS({range:tasks.title},%s,{range:tasks.status},%s)' % (LK('tasks', 'task_id', 'title'), OPEN), 'int'),
        FF('Percent of this title steps done', 'IFERROR(COUNTIFS({range:tasks.title},%s,{range:tasks.status},%s)/COUNTIFS({range:tasks.title},%s),0)' % (LK('tasks', 'task_id', 'title'), DONE, LK('tasks', 'task_id', 'title')), 'pct')]),
    FORM('reviewer_entry_sheet', 'Reviewer Entry Sheet', 'Reviewer profile and record', 'reviewers.reviewer_id', F(
        ('Name', 'reviewers.name'), ('Kind', 'reviewers.kind'), ('E-mail', 'reviewers.email'), ('Phone', 'reviewers.phone'), ('Joined on', 'reviewers.joined_on'), ('Copies sent', 'reviewers.copies_sent'),
        ('Reviews posted', 'reviewers.reviews_posted'), ('Reviews posted, last 12 months', 'reviewers.posted_12m'), ('Response rate', 'reviewers.response_rate')) + [
        FF('Rank among all reviewers', 'INDEX({range:ranking.rank},MATCH({pick},{range:ranking.reviewer_id},0))', 'int'),
        FF('Average days to a review', 'INDEX({range:ranking.avg_days},MATCH({pick},{range:ranking.reviewer_id},0))', 'num'),
        FF('Verdict', 'INDEX({range:ranking.verdict},MATCH({pick},{range:ranking.reviewer_id},0))', 'text')]),
    FORM('advance_copy_sheet', 'Advance Copy Sheet', 'Advance copy sent to a reviewer', 'arcs.arc_id', F(
        ('Title', 'arcs.title'), ('Reviewer', 'arcs.reviewer'), ('Reviewer kind', 'arcs.reviewer_kind'), ('Reviewer phone', 'arcs.reviewer_phone'), ('Sent on', 'arcs.sent_on'), ('Review due', 'arcs.due_on'),
        ('Status', 'arcs.status'), ('Days since sent', 'arcs.days_since_sent'), ('Copy check', 'arcs.check')) + [
        FF('Copies sent of this title', 'COUNTIFS({range:arcs.title},%s,{range:arcs.sent_on},">0")' % LK('arcs', 'arc_id', 'title'), 'int'),
        FF('Copies of this title not yet sent', 'COUNTIFS({range:arcs.title},%s,{range:arcs.status},%s)' % (LK('arcs', 'arc_id', 'title'), NOTSENT), 'int')]),
    FORM('review_posted_sheet', 'Review Posted Sheet', 'Review posted by a reviewer', 'arcs.arc_id', F(
        ('Title', 'arcs.title'), ('Reviewer', 'arcs.reviewer'), ('Sent on', 'arcs.sent_on'), ('Review due', 'arcs.due_on'), ('Posted on', 'arcs.posted_on'), ('Days to a review', 'arcs.days_to_review'), ('Status', 'arcs.status')) + [
        FF('Reviews posted for this title', 'INDEX({range:titles.reviews_posted},MATCH(%s,{range:titles.title},0))' % LK('arcs', 'arc_id', 'title'), 'int'),
        FF('Reviews per 100 copies, this title', 'INDEX({range:responses.per_100},MATCH(%s,{range:responses.title},0))' % LK('arcs', 'arc_id', 'title'), 'num'),
        FF('Average days to a review, all', 'IFERROR(AVERAGE({range:arcs.days_to_review}),0)', 'num')]),
    FORM('reminder_sheet', 'Reviewer Reminder Sheet', 'Open copies of one reviewer', 'reviewers.reviewer_id', F(
        ('Name', 'reviewers.name'), ('Phone', 'reviewers.phone'), ('E-mail', 'reviewers.email'), ('Copies sent', 'reviewers.copies_sent'), ('Reviews posted', 'reviewers.reviews_posted')) + [
        FF('Open copies waiting for a review', 'COUNTIFS({range:arcs.reviewer},%s,{range:arcs.status},%s)+COUNTIFS({range:arcs.reviewer},%s,{range:arcs.status},%s)' % (LK('reviewers', 'reviewer_id', 'name'), COPYSENT, LK('reviewers', 'reviewer_id', 'name'), REMINDED), 'int'),
        FF('Copies already reminded', 'COUNTIFS({range:arcs.reviewer},%s,{range:arcs.status},%s)' % (LK('reviewers', 'reviewer_id', 'name'), REMINDED), 'int'),
        FF('Copies overdue', 'COUNTIFS({range:arcs.reviewer},%s,{range:arcs.check},%s)' % (LK('reviewers', 'reviewer_id', 'name'), ca('Overdue')), 'int'),
        FF('Copies marked no reply', 'COUNTIFS({range:arcs.reviewer},%s,{range:arcs.status},%s)' % (LK('reviewers', 'reviewer_id', 'name'), tok('arcstatus', 'No reply')), 'int'),
        FF('Verdict', 'INDEX({range:ranking.verdict},MATCH({pick},{range:ranking.reviewer_id},0))', 'text')]),
    FORM('send_sheet', 'Newsletter Send Sheet', 'Newsletter send with its results', 'sends.send_id', F(
        ('Date', 'sends.date'), ('Kind of send', 'sends.kind'), ('List size', 'sends.list_size'), ('Sent', 'sends.sent'), ('Opens', 'sends.opens'), ('Clicks', 'sends.clicks'), ('Unsubscribes', 'sends.unsubscribes'),
        ('New subscribers', 'sends.new_subscribers'), ('Sales in 7 days', 'sends.sales_7d'), ('Royalties in 7 days', 'sends.royalty_7d')) + [
        FF('Open rate', 'INDEX({range:sendres.open_rate},MATCH({pick},{range:sendres.send_id},0))', 'pct'), FF('Click rate', 'INDEX({range:sendres.click_rate},MATCH({pick},{range:sendres.send_id},0))', 'pct'),
        FF('Royalties per 1,000 readers', 'INDEX({range:sendres.rpk},MATCH({pick},{range:sendres.send_id},0))', 'money'), FF('Your average, same kind', 'INDEX({range:sendres.kind_avg},MATCH({pick},{range:sendres.send_id},0))', 'money'),
        FF('Verdict', 'INDEX({range:sendres.verdict},MATCH({pick},{range:sendres.send_id},0))', 'text')]),
    FORM('source_sheet', 'Subscriber Source Sheet', 'Subscribers from one source in one month', 'subs.row_id', F(
        ('Month', 'subs.month'), ('Source', 'subs.source'), ('New subscribers', 'subs.new_subscribers'), ('Lost', 'subs.lost'), ('Cost', 'subs.cost'), ('Net gain', 'subs.net'), ('Cost per new subscriber', 'subs.cost_per_sub')) + [
        FF('New subscribers, this source, 12 months', 'INDEX({range:srccost.new_12m},MATCH(%s,{range:srccost.source},0))' % LK('subs', 'row_id', 'source'), 'int'),
        FF('Cost per subscriber, 12 months', 'INDEX({range:srccost.cost_per_sub},MATCH(%s,{range:srccost.source},0))' % LK('subs', 'row_id', 'source'), 'money'),
        FF('Cost per subscriber limit', '{set:cost_per_sub_limit}', 'money')]),
    FORM('swap_booking_sheet', 'Swap Booking Sheet', 'Swap or promotion booked with a partner', 'swaps.swap_id', F(
        ('Date', 'swaps.date'), ('Partner', 'swaps.partner'), ('Partner phone', 'swaps.phone'), ('Kind', 'swaps.kind'), ('Title promoted', 'swaps.title'), ('Cost', 'swaps.cost')) + [
        FF('Swaps with this partner', 'COUNTIFS({range:swaps.partner},%s)' % LK('swaps', 'swap_id', 'partner'), 'int'),
        FF('Subscribers per swap with this partner', 'IFERROR(AVERAGEIFS({range:swaps.subscribers},{range:swaps.partner},%s),0)' % LK('swaps', 'swap_id', 'partner'), 'num'),
        FF('Your average subscribers per swap', 'AVERAGE({range:swaps.subscribers})', 'num'), FF('Next slot to offer', 'INDEX({range:swapres.next_slot},MATCH({pick},{range:swapres.swap_id},0))', 'date')]),
    FORM('swap_result_sheet', 'Swap Result Sheet', 'Result and payback of one swap', 'swapres.swap_id', F(
        ('Date', 'swapres.date'), ('Partner', 'swapres.partner'), ('Kind', 'swapres.kind'), ('Cost', 'swapres.cost'), ('Subscribers gained', 'swapres.subscribers'), ('Sales in 7 days', 'swapres.sales_7d'),
        ('Cost per subscriber', 'swapres.cost_per_sub'), ('Royalties in 7 days', 'swapres.royalties'), ('Value of readers gained', 'swapres.value'), ('Payback', 'swapres.payback'), ('Verdict', 'swapres.verdict')) + [
        FF('Swaps with this partner', 'INDEX({range:swapres.partner_swaps},MATCH({pick},{range:swapres.swap_id},0))', 'int'), FF('Payback you want', '{set:payback_target}', 'pct')]),
    FORM('launch_result_sheet', 'Launch Result Sheet', 'Launch result against your own average', 'launchres.title', F(
        ('Release date', 'launchres.release_date'), ('Copies, first 7 days', 'launchres.copies_7d'), ('Copies, first 30 days', 'launchres.copies_30d'), ('Copies, first 12 months', 'launchres.copies_12m'),
        ('Launch share, 7 days', 'launchres.share_7d'), ('Launch share, 30 days', 'launchres.launch_share'), ('Royalties, first 30 days', 'launchres.royalties_30d'), ('Your average launch share', 'launchres.own_avg'),
        ('Difference to your average', 'launchres.diff_pts'), ('Verdict', 'launchres.verdict')) + [
        FF('Royalty per copy, 30 days', 'INDEX({range:launchres.royalty_copy},MATCH({pick},{range:launchres.title},0))', 'money')]),
    FORM('preorder_sheet', 'Pre-order Count Sheet', 'Pre-order count of a launch and the next one', 'launchres.title', F(
        ('Release date', 'launchres.release_date'), ('Pre-orders 30 days before', 'launchres.pre_30'), ('Pre-orders at release', 'launchres.pre_total'), ('Copies, first 30 days', 'launchres.copies_30d')) + [
        FF('Share of pre-orders in before day 30', 'IFERROR(INDEX({range:launchres.pre_30},MATCH({pick},{range:launchres.title},0))/INDEX({range:launchres.pre_total},MATCH({pick},{range:launchres.title},0)),0)', 'pct'),
        FF('Pre-orders as share of 30-day copies', 'IFERROR(INDEX({range:launchres.pre_total},MATCH({pick},{range:launchres.title},0))/INDEX({range:launchres.copies_30d},MATCH({pick},{range:launchres.title},0)),0)', 'pct'),
        FF('Pre-orders now, next launch', 'INDEX({range:titles.preorders},MATCH({set:next_title},{range:titles.title},0))', 'int'),
        FF('Days to the next release', 'INDEX({range:titles.days_to_release},MATCH({set:next_title},{range:titles.title},0))', 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('launch_plan_doc', 'Launch Plan', 'Launch plan for a title', 'titles.title_id', [
        'Launch plan of {set:company}, dated {today}. Title: {col:titles.title}, by {col:titles.pen_name} ({col:titles.series}). Release date: {col:titles.release_date}, in {col:titles.days_to_release} days. Pre-orders so far: {col:titles.preorders}.',
        'Key dates. Reviewer copies out by {col:titles.copies_out_on}. Newsletter teaser on {col:titles.teaser_on}. Reviewer reminders on {col:titles.reminders_on}. Ads ready by {col:titles.ads_on} with a budget of {col:titles.ad_budget}. Launch price set by {col:titles.price_on}. Reviewers thanked on {col:titles.thanks_on}.',
        'Progress. {col:titles.open_steps} of {col:titles.total_steps} steps are open and {col:titles.percent_ready} are done. {col:titles.unsent_copies} advance copies are not yet sent. Each step has an owner and a due date on the Launch Tasks sheet.',
        'Write the owners and any change of date below.'], ['Author-publisher', 'Launch coordinator'], NOTE),
    DOC('invite_doc', 'Reviewer Invitation', 'Reviewer invitation letter', 'reviewers.reviewer_id', [
        'Letter of {set:company}, dated {today}. Dear {col:reviewers.name}, thank you for being on our reviewer list since {col:reviewers.joined_on}.',
        'We would like to invite you to read the next book before it is released. An advance copy is a free copy sent to a reviewer before release. There is no duty to write a review and no duty to praise the book. An honest review, a short one, helps other readers.',
        'If you would like a copy, reply to this letter and tell us your preferred format. We will write the due date for the review on the cover note.', 'Thank you for your time.'], ['Author-publisher', 'Reviewer'], NOTE),
    DOC('cover_note_doc', 'Advance Copy Note', 'Advance copy cover note', 'arcs.arc_id', [
        'Cover note of {set:company}, dated {today}. Dear {col:arcs.reviewer}, here is your advance copy of {col:arcs.title}, sent on {col:arcs.sent_on}.',
        'Please read it at your own pace. If you would like to post a review, the date we hope for is {col:arcs.due_on}. A review is welcome but never a duty. Please do not share the file.',
        'Say in your review that you received a free advance copy. Check each store\'s current terms for how to post it.', 'With thanks for your help.'], ['Author-publisher', 'Reviewer'], NOTE),
    DOC('reminder_doc', 'Review Reminder', 'Review reminder letter', 'arcs.arc_id', [
        'Letter of {set:company}, dated {today}. Dear {col:arcs.reviewer}, a friendly reminder about {col:arcs.title}.',
        'The copy was sent on {col:arcs.sent_on}, which is {col:arcs.days_since_sent} days ago, and the review was hoped for by {col:arcs.due_on}. The copy check says: {col:arcs.check}.',
        'If you have no time, that is fine. Please tell us so that we can keep your place on the list for the next book. If the review is ready, thank you.', 'With kind regards.'], ['Author-publisher', 'Reviewer'], NOTE),
    DOC('thanks_doc', 'Reviewer Thank-you', 'Thank-you note to a reviewer', 'arcs.arc_id', [
        'Note of {set:company}, dated {today}. Dear {col:arcs.reviewer}, thank you for your review of {col:arcs.title}.',
        'It was posted on {col:arcs.posted_on}, {col:arcs.days_to_review} days after we sent the copy. Reviews from readers like you help new readers decide.',
        'We hope you will read the next book too. We will keep you on the list.', 'With warm thanks.'], ['Author-publisher', 'Reviewer'], NOTE),
    DOC('run_sheet_doc', 'Launch Day Run Sheet', 'Launch day run sheet', 'titles.title_id', [
        'Launch day run sheet of {set:company}, dated {today}. Title: {col:titles.title}. Release date: {col:titles.release_date}. Pre-orders: {col:titles.preorders}.',
        'Morning. Check that the book is live on every store page and that the price is the launch price set by {col:titles.price_on}. Send the launch day newsletter. Post the launch message on your own channels.',
        'Afternoon. Answer reader messages. Note the first copies sold. Ask the assistant to check the store pages ({col:titles.va_name}).',
        'Evening. Write the copies of the day on the Launch Results sheet. Reviewers are thanked on {col:titles.thanks_on}.'], ['Author-publisher', 'Assistant'], NOTE),
    DOC('week_news_doc', 'Launch Week Newsletters', 'Newsletter plan for a launch week', 'titles.title_id', [
        'Newsletter plan of {set:company}, dated {today}. Title: {col:titles.title}, release date {col:titles.release_date}.',
        'Plan the pushes of the launch week: the teaser was due on {col:titles.teaser_on}; one send on the day before release; the launch day send on {col:titles.release_date}; one reminder send two or three days after. Your own limit is on the Start sheet and the Launch Week Plan sheet checks it.',
        'For each send write the kind (launch push, price promotion, story update), the day and the link. Record the result on the Newsletter Sends sheet after 7 days.', 'The assistant is {col:titles.va_name}.'], ['Author-publisher', 'Assistant'], NOTE),
    DOC('swap_proposal_doc', 'Swap Proposal', 'Swap proposal to a partner author', 'swapres.swap_id', [
        'Proposal of {set:company}, dated {today}. Dear {col:swapres.partner}, thank you for the swap on {col:swapres.date}.',
        'It brought {col:swapres.subscribers} readers to our list and {col:swapres.sales_7d} sales in the 7 days after. We would like to offer the next slot on {col:swapres.next_slot}.',
        'Each of us writes a short blurb and a link and sends it by email to our own list. Tell us if the slot suits you and what you would like us to feature.', 'With kind regards.'], ['Author-publisher', 'Partner author'], NOTE),
    DOC('swap_report_doc', 'Swap Result Report', 'Swap result report', 'swapres.swap_id', [
        'Swap result report of {set:company}, dated {today}. Partner: {col:swapres.partner}. Date: {col:swapres.date}. Kind: {col:swapres.kind}.',
        'Cost: {col:swapres.cost}. Subscribers gained: {col:swapres.subscribers}. Cost per subscriber: {col:swapres.cost_per_sub}. Sales in 7 days: {col:swapres.sales_7d}. Royalties in 7 days: {col:swapres.royalties}. Value of the readers gained: {col:swapres.value}.',
        'Payback: {col:swapres.payback} (1.00 means paid back). Verdict: {col:swapres.verdict}. This partner has {col:swapres.partner_swaps} swaps with an average of {col:swapres.partner_avg} readers.', 'Figures are estimates, the values per copy and per reader are your own numbers.'], ['Author-publisher'], NOTE),
    DOC('launch_report_doc', 'Launch Result Report', 'Launch result report with your own launch share', 'launchres.title', [
        'Launch result report of {set:company}, dated {today}. Title: {col:launchres.title}. Release date: {col:launchres.release_date}.',
        'Copies in the first 7 days: {col:launchres.copies_7d}. In the first 30 days: {col:launchres.copies_30d}. In the first 12 months: {col:launchres.copies_12m}. Royalties in the first 30 days: {col:launchres.royalties_30d}.',
        'Launch share (the share of the first 12 months sold in the first 30 days): {col:launchres.launch_share}. Your own average: {col:launchres.own_avg}. Verdict: {col:launchres.verdict}.',
        'Pre-orders at release: {col:launchres.pre_total}. Figures are estimates until the stores pay.'], ['Author-publisher'], NOTE),
    DOC('growth_report_doc', 'List Growth Report', 'Newsletter list growth report', 'growth.month', [
        'List growth report of {set:company}, dated {today}. Month: {col:growth.month}.',
        'Sends: {col:growth.sends}. New subscribers: {col:growth.new}. Lost subscribers: {col:growth.lost}. Net growth: {col:growth.net}. List size at month end: {col:growth.list_size}. Growth: {col:growth.growth_pct}.',
        'Open rate: {col:growth.open_rate}. Click rate: {col:growth.click_rate}. Royalties in 7 days from the sends: {col:growth.royalties_7d}.', 'Compare with the same month a year ago on the List Growth by Month sheet.'], ['Author-publisher'], NOTE),
    DOC('reviewer_summary_doc', 'Reviewer List Summary', 'Reviewer list summary for one reviewer', 'ranking.reviewer_id', [
        'Reviewer summary of {set:company}, dated {today}. Reviewer: {col:ranking.name} ({col:ranking.kind}), phone {col:ranking.phone}.',
        'Copies sent: {col:ranking.copies_sent}. Reviews posted: {col:ranking.reviews_posted}. Response rate: {col:ranking.response_rate}. Average days to a review: {col:ranking.avg_days}. Rank on the list: {col:ranking.rank}.',
        'Verdict against your own targets: {col:ranking.verdict}. A reviewer with few copies is tested before you decide.', 'Write your decision below.'], ['Author-publisher'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('launch_60', 'Launch 60 Days Out', 'titles', 'titles.release_date', [('Open the pre-order and check the price', -60), ('Confirm the final cover on every store page', -58), ('Check the reviewer list and remove silent reviewers', -56), ('Book newsletter swaps for the launch month', -55), ('Brief the cover designer on the teaser graphic', -50), ('Send the advance copies to reviewers', -42)]),
    CHK('launch_30', 'Launch 30 Days Out', 'titles', 'titles.release_date', [('Finish the teaser chapter', -35), ('Check the pre-orders against your own pace', -30), ('Send the first reviewer reminder', -28), ('Send the newsletter teaser', -21), ('Check the reminders and the late steps', -21), ('Plan the launch week sends', -14)]),
    CHK('launch_week', 'Launch Week Steps', 'titles', 'titles.release_date', [('Send the second reviewer reminder', -10), ('Prepare the ads with the budget', -7), ('Write the launch day newsletter', -5), ('Set the launch price', -3), ('Test every link in the newsletter', -1), ('Tell the assistant the launch day plan', -1)]),
    CHK('launch_day', 'Launch Day Steps', 'titles', 'titles.release_date', [('Check the book is live in every store', 0), ('Send the launch day newsletter', 0), ('Post the launch message on your channels', 0), ('Answer reader messages', 0), ('Write the copies of the day', 0), ('Thank the people who helped', 0)]),
    CHK('after_launch', 'After Launch Week', 'titles', 'titles.release_date', [('Check the store pages and the price', 1), ('Record the copies of the first 7 days', 7), ('Send a story update to the list', 8), ('Thank the reviewers', 10), ('Record the copies of the first 30 days', 30), ('Write the launch result and compare it with your average', 31)]),
    CHK('send_copies', 'Sending Advance Copies', 'arcs', 'arcs.due_on', [('Choose the reviewers for this title', -45), ('Check the file opens on a reading app', -42), ('Send the copies with the cover note', -37), ('Write the sent date in the Advance Copies sheet', -37), ('Send a reminder to reviewers who have not answered', -14), ('Mark the silent copies as no reply', 14)]),
    CHK('review_follow', 'Review Follow-up', 'arcs', 'arcs.due_on', [('Remind the reviewers due this week', -3), ('Check which reviews are posted', 0), ('Send the second reminder', 7), ('Thank the reviewers who posted', 8), ('Mark the silent copies as no reply', 21), ('Update the Reviewer Ranking', 22)]),
    CHK('weekly_send', 'Weekly Newsletter Send', 'sends', 'sends.date', [('Choose the kind of send', -3), ('Write the message and the link', -2), ('Test the links and the preview', -1), ('Send the newsletter', 0), ('Write opens, clicks and sign-ups in the sheet', 1), ('Write the sales in 7 days', 7)]),
    CHK('list_cleanup', 'List Clean-up Steps', 'growth', 'growth.month', [('Export the readers who opened none of the last sends', 1), ('Send one re-engagement message', 3), ('Wait a week for answers', 10), ('Remove the readers who stayed silent', 11), ('Write the new list size on the List Growth sheet', 12), ('Check the open rate of the next send', 20)]),
    CHK('book_swap', 'Booking a Swap', 'swaps', 'swaps.date', [('Ask the partner author for a slot', -21), ('Agree the date and the blurb', -14), ('Send your blurb and link', -7), ('Check the links on both sides', -1), ('The swap goes out', 0)]),
    CHK('after_swap', 'After a Swap', 'swaps', 'swaps.date', [('Write the readers gained', 1), ('Write the sales in 7 days', 7), ('Work out the payback on the Swap Results sheet', 8), ('Decide: swap again, change partner or stop', 9), ('Thank the partner and offer the next slot', 10)]),
    CHK('monthly_review', 'Monthly Reader Review', 'growth', 'growth.month', [('Write the new and lost subscribers by source', 2), ('Check the cost per subscriber of each source', 3), ('Compare the send results with your own average', 4), ('Check the reviewer ranking', 5), ('Check the swap results', 6), ('Decide next month sends and swaps', 8)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
RP = 'arcs.reviewer_phone'; SP = 'swapres.phone'
messages = [
    M('r_ready', 'Reviewer: advance copy ready', 'arcs', RP, 'Hello {reviewer}, your advance copy of {title} is ready. The review is hoped for by {due_on}. Thank you. {company}'),
    M('r_remind', 'Reviewer: review reminder', 'arcs', RP, 'Hello {reviewer}, a friendly reminder: the review of {title} is due on {due_on}. If you have no time, please tell me so I keep your place. {company}'),
    M('r_thanks', 'Reviewer: thank you for the review', 'arcs', RP, 'Hello {reviewer}, thank you for your review of {title}, posted on {posted_on}. It helps new readers. {company}'),
    M('r_new', 'Reviewer: a new advance copy', 'arcs', RP, 'Hello {reviewer}, a new advance copy is available for {title}. Would you like it? The review would be due on {due_on}. {company}'),
    M('r_silent', 'Reviewer: keep your place?', 'arcs', RP, 'Hello {reviewer}, we have not heard about {title}, sent {days_since_sent} days ago. Shall we keep your place on the reviewer list? {company}'),
    M('r_live', 'Reviewer: the book is live', 'arcs', RP, 'Hello {reviewer}, {title} is now live. If you have read it, please post your review. Thank you. {company}'),
    M('r_attach', 'Reviewer: copy attached', 'arcs', RP, 'Hello {reviewer}, the advance copy of {title} is attached. The review is hoped for by {due_on}. {company}'),
    M('r_list', 'Reviewer: thanks for being on the list', 'arcs', RP, 'Hello {reviewer}, thank you for being part of the reviewer list of {company}. Your reviews help readers find our books.'),
    M('s_offer', 'Swap partner: offer a swap date', 'swapres', SP, 'Hello {partner}, would you like a newsletter swap on {next_slot}? Our last swap on {date} brought {subscribers} readers. {company}'),
    M('s_thanks', 'Swap partner: thanks, readers joined', 'swapres', SP, 'Hello {partner}, thank you for the swap on {date}. {subscribers} readers joined our list. {company}'),
    M('s_booked', 'Swap partner: swap booked', 'swapres', SP, 'Hello {partner}, your swap is booked for {next_slot}. {company}'),
    M('s_blurb', 'Swap partner: send your blurb', 'swapres', SP, 'Hello {partner}, please send your blurb and link for the swap on {next_slot}. {company}'),
    M('s_slot', 'Swap partner: next slot', 'swapres', SP, 'Hello {partner}, the next swap slot is {next_slot}. Does it suit you? {company}'),
    M('s_payback', 'Swap partner: payback of the last swap', 'swapres', SP, 'Hello {partner}, the payback of our last swap on {date} was {payback}. Shall we plan the next one? {company}'),
    M('v_copies', 'Assistant: send the advance copies', 'titles', 'titles.va_phone', 'Hello {va_name}, please send the advance copies of {title}. {unsent_copies} copies are not yet sent. {company}'),
    M('v_remind', 'Assistant: send reviewer reminders', 'titles', 'titles.va_phone', 'Hello {va_name}, please send the reviewer reminders for {title} on {reminders_on}. {company}'),
    M('v_setup', 'Assistant: set up the next newsletter', 'sends', 'sends.va_phone', 'Hello {va_name}, please set up the next newsletter. The last one went out on {date} ({kind}) to {list_size} readers. {company}'),
    M('v_launch', 'Assistant: schedule the launch day send', 'titles', 'titles.va_phone', 'Hello {va_name}, please schedule the launch day newsletter for {release_date} ({title}). {company}'),
    M('v_preorder', 'Assistant: check the pre-order is live', 'titles', 'titles.va_phone', 'Hello {va_name}, please check that the pre-order of {title} is live. We have {preorders} pre-orders so far. {company}'),
    M('v_thank', 'Assistant: thank the reviewers', 'titles', 'titles.va_phone', 'Hello {va_name}, please thank the reviewers of {title} on {thanks_on}. {reviews_posted} reviews are posted so far. {company}'),
    M('v_record', 'Assistant: record the result of a send', 'sends', 'sends.va_phone', 'Hello {va_name}, please record the result of the send on {date}: opens, clicks, sign-ups and the sales in 7 days. {company}'),
    M('c_open', 'Launch coordinator: steps still open', 'titles', 'titles.coord_phone', 'Hello {coord_name}, {title} launches on {release_date} and {open_steps} steps are open. Please tell me what you still need. {company}'),
    M('c_late', 'Launch coordinator: a step is late', 'tasks', 'tasks.coord_phone', 'Hello {coord_name}, the step {step} for {title} is {days_late} days late. Please tell me when it will be done. {company}'),
    M('c_plan', 'Launch coordinator: reviewer plan', 'titles', 'titles.coord_phone', 'Hello {coord_name}, please confirm the reviewer plan for {title}. {unsent_copies} advance copies are not yet sent. {company}'),
    M('c_result', 'Launch coordinator: launch result ready', 'launchres', 'launchres.coord_phone', 'Hello {coord_name}, the launch result of {title} is ready: {copies_30d} copies in the first 30 days. {company}'),
    M('a_ads', 'Ad specialist: launch ads brief', 'titles', 'titles.ad_phone', 'Hello {ad_name}, the launch of {title} is on {release_date}. Ads should be ready by {ads_on}, budget {ad_budget}. {company}'),
    M('d_teaser', 'Cover designer: teaser graphic due', 'tasks', 'tasks.designer_phone', 'Hello {designer_name}, the teaser graphic for {title} is due on {due_date}. Please send it when it is ready. {company}'),
    M('o_step', 'Author: a step is overdue', 'tasks', 'tasks.author_phone', 'Reminder for the author: {step} for {title} was due on {due_date}. It is {days_late} days late. {company}'),
    M('o_ready', 'Author: percent ready and days left', 'titles', 'titles.author_phone', 'Reminder for the author: {title} is {percent_ready} ready, {days_to_release} days to release, {open_steps} steps open. {company}'),
    M('o_unsent', 'Author: advance copies not sent', 'titles', 'titles.author_phone', 'Reminder for the author: {unsent_copies} advance copies of {title} are not yet sent. {company}'),
    M('o_reviews', 'Author: reviews and response rate', 'titles', 'titles.author_phone', 'Note for the author: {reviews_posted} reviews of {title} are posted, a response rate of {response_rate}. {company}'),
    M('o_list', 'Author: list size and growth', 'growth', 'growth.author_phone', 'Note for the author: for {month} the list has {list_size} readers, {net} net new. {company}'),
    M('o_send', 'Author: send earnings per 1,000', 'sendres', 'sendres.author_phone', 'Note for the author: the send of {date} earned {rpk} per 1,000 readers ({verdict}). {company}'),
    M('o_swap', 'Author: swap payback', 'swapres', 'swapres.author_phone', 'Note for the author: the swap with {partner} on {date} paid back {payback}. {company}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30), dashboard, insights
NEXTREL = 'INDEX({range:titles.release_date},MATCH({set:next_title},{range:titles.title},0))'
LASTM = 'MATCH(MAX({range:launchres.release_date}),{range:launchres.release_date},0)'
S90 = '{range:sends.date},">"&({today}-90)'
S12 = '{range:sends.date},">"&({today}-365)'
M12 = '{range:subs.month},">"&EDATE(%s,-12)' % MS
kpis = [
    KPI('Next launch in days', '%s-{today}' % NEXTREL, 'int'),
    KPI('Launch steps done (percent)', 'IFERROR(SUM({range:readiness.done})/COUNT({range:readiness.done}),0)', 'pct'),
    KPI('Launch steps late', 'COUNTIFS({range:tasks.late_flag},%s)' % ca('Late'), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Steps due in the next 7 days', 'COUNTIFS({range:tasks.status},%s,{range:tasks.due_date},">="&{today},{range:tasks.due_date},"<="&({today}+7))' % OPEN, 'int'),
    KPI('Advance copies sent', 'COUNTIFS({range:arcs.sent_on},">0")', 'int'),
    KPI('Advance copies not yet sent', 'COUNTIFS({range:arcs.status},%s)' % NOTSENT, 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Reviews posted', 'COUNTIFS({range:arcs.status},%s)' % POSTED, 'int'),
    KPI('Reviews posted for the last launch', 'COUNTIFS({range:arcs.title},INDEX({range:launchres.title},%s),{range:arcs.status},%s)' % (LASTM, POSTED), 'int'),
    KPI('Response rate', 'IFERROR(COUNTIFS({range:arcs.status},%s)/COUNTIFS({range:arcs.sent_on},">0"),0)' % POSTED, 'pct'),
    KPI('Reviews posted, last 180 days', 'COUNTIFS({range:arcs.posted_on},">="&({today}-180))', 'int'),
    KPI('Advance copies overdue', 'COUNTIFS({range:arcs.check},%s)' % ca('Overdue'), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Reviewers on the list', 'COUNTA({range:reviewers.reviewer_id})', 'int'),
    KPI('Reviewers who posted, last 12 months', 'COUNTIFS({range:reviewers.posted_12m},">0")', 'int'),
    KPI('Average days to a review', 'IFERROR(AVERAGE({range:arcs.days_to_review}),0)', 'num'),
    KPI('Pre-orders so far', 'INDEX({range:titles.preorders},MATCH({set:next_title},{range:titles.title},0))', 'int'),
    KPI('Own launch share (average)', 'AVERAGE({range:launchres.launch_share})', 'pct'),
    KPI('Launch share of the last launch', 'INDEX({range:launchres.launch_share},%s)' % LASTM, 'pct'),
    KPI('Copies in the first 30 days, last launch', 'INDEX({range:launchres.copies_30d},%s)' % LASTM, 'int'),
    KPI('List size now', 'INDEX({range:growth.list_size},MATCH(%s,{range:growth.month},0))' % MS, 'int'),
    KPI('New subscribers this month', 'SUMIFS({range:subs.new_subscribers},{range:subs.month},%s)' % MS, 'int'),
    KPI('New subscribers, last 12 months', 'SUMIFS({range:subs.new_subscribers},%s)' % M12, 'int'),
    KPI('Lost subscribers, last 12 months', 'SUMIFS({range:subs.lost},%s)' % M12, 'int'),
    KPI('Net list growth, last 12 months', 'SUMIFS({range:subs.new_subscribers},%s)-SUMIFS({range:subs.lost},%s)' % (M12, M12), 'int'),
    KPI('Open rate, last 90 days', 'IFERROR(SUMIFS({range:sends.opens},%s)/SUMIFS({range:sends.sent},%s),0)' % (S90, S90), 'pct'),
    KPI('Click rate, last 90 days', 'IFERROR(SUMIFS({range:sends.clicks},%s)/SUMIFS({range:sends.sent},%s),0)' % (S90, S90), 'pct'),
    KPI('Unsubscribe rate, last 90 days', 'IFERROR(SUMIFS({range:sends.unsubscribes},%s)/SUMIFS({range:sends.sent},%s),0)' % (S90, S90), 'pct'),
    KPI('Cost per subscriber, last 12 months', 'IFERROR(SUMIFS({range:subs.cost},%s)/SUMIFS({range:subs.new_subscribers},%s),0)' % (M12, M12), 'money'),
    KPI('Royalties per 1,000 readers per send', 'IFERROR(SUMIFS({range:sends.royalty_7d},%s)/SUMIFS({range:sends.list_size},%s)*1000,0)' % (S12, S12), 'money'),
    KPI('Swaps and promotions, last 12 months', 'COUNTIFS({range:swaps.date},">"&({today}-365))', 'int'),
    KPI('Swap payback, last 12 months', 'IFERROR((SUMIFS({range:swapres.royalties},{range:swapres.date},">"&({today}-365))+SUMIFS({range:swapres.value},{range:swapres.date},">"&({today}-365)))/(SUMIFS({range:swapres.cost},{range:swapres.date},">"&({today}-365))+COUNTIFS({range:swapres.date},">"&({today}-365))*{set:swap_time_cost}),0)', 'pct'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Readers Dashboard", "kpis": kpis,
    "monthly": {"title": "New subscribers, lost subscribers and sends by month", "date": "growth.month", "series": [
        {"label": "New subscribers", "sum": "growth.new", "date": "growth.month"}, {"label": "Lost subscribers", "sum": "growth.lost", "date": "growth.month"}, {"label": "Sends", "sum": "growth.sends", "date": "growth.month"}]},
    "breakdowns": [{"title": "New subscribers by source", "by": "subs.source", "value": "subs.new_subscribers", "agg": "sum"}, {"title": "Advance copies by status", "by": "arcs.status", "agg": "count"},
                   {"title": "Reviewers by kind", "by": "reviewers.kind", "agg": "count"}, {"title": "Swap and promotion cost by kind", "by": "swaps.kind", "value": "swaps.cost", "agg": "sum"}]}
insights = {"filters": [{"label": "Reviewer kind", "list": "rkind"}, {"label": "Send kind", "list": "skind"}, {"label": "Subscriber source", "list": "subsource"}],
    "gauges": [
        {"title": "Launch steps on time", "num": AGG('count', 'tasks', where=[('late_flag', '=', ca('Done on time'))]), "den": AGG('count', 'tasks', where=[('status', '=', DONE)])},
        {"title": "Advance copies sent", "num": AGG('count', 'arcs', where=[('status', '<>', NOTSENT)]), "den": AGG('count', 'arcs')},
        {"title": "Reviews posted of copies sent", "num": AGG('count', 'arcs', where=[('status', '=', POSTED)]), "den": AGG('count', 'arcs', where=[('sent_on', '>', 0)])},
        {"title": "Open rate at your target", "num": AGG('count', 'sendres', where=[('open_rate', '>=', '{set:open_rate_target}')]), "den": AGG('count', 'sendres')},
        {"title": "Swaps that paid back", "num": AGG('count', 'swapres', where=[('payback', '>=', '{set:payback_target}')]), "den": AGG('count', 'swapres')},
        {"title": "Subscribers kept", "num": AGG('sum', 'growth', 'growth.net'), "den": AGG('sum', 'growth', 'growth.new')}],
    "charts": [
        CHART('Launch steps by status', 'bar', 'tasks.status', [AGG('count', 'tasks', label='Steps')]),
        CHART('Launch steps by owner role', 'bar', 'tasks.owner_role', [AGG('count', 'tasks', label='Steps')]),
        CHART('Launch steps done per month', 'column', 'month', [AGG('count', 'tasks', date='tasks.done_on', where=[('status', '=', DONE)], label='Steps done')]),
        CHART('Advance copies by status', 'bar', 'arcs.status', [AGG('count', 'arcs', label='Copies')]),
        CHART('Advance copies sent by title', 'bar', 'responses.title', [AGG('sum', 'responses', 'responses.copies_sent', label='Copies sent')]),
        CHART('Reviews posted per month', 'column', 'month', [AGG('count', 'arcs', date='arcs.posted_on', where=[('status', '=', POSTED)], label='Reviews posted')]),
        CHART('Reviewers by kind', 'bar', 'reviewers.kind', [AGG('count', 'reviewers', label='Reviewers')]),
        CHART('Response rate by reviewer kind', 'bar', 'reviewers.kind', [AGG('avg', 'reviewers', 'reviewers.response_rate', label='Response rate')]),
        CHART('Newsletter list size per month', 'line', 'month', [AGG('avg', 'growth', 'growth.list_size', date='growth.month', label='List size')]),
        CHART('New subscribers per month', 'column', 'month', [AGG('sum', 'subs', 'subs.new_subscribers', date='subs.month', label='New subscribers')]),
        CHART('Lost subscribers per month', 'column', 'month', [AGG('sum', 'subs', 'subs.lost', date='subs.month', label='Lost subscribers')]),
        CHART('Net growth per month', 'line', 'month', [AGG('avg', 'growth', 'growth.net', date='growth.month', label='Net growth')]),
        CHART('New subscribers by source', 'bar', 'subs.source', [AGG('sum', 'subs', 'subs.new_subscribers', label='New subscribers')]),
        CHART('Cost per subscriber by source', 'bar', 'srccost.source', [AGG('avg', 'srccost', 'srccost.cost_per_sub', label='Cost per subscriber')]),
        CHART('Sends per month', 'column', 'month', [AGG('count', 'sends', date='sends.date', label='Sends')]),
        CHART('Sends by kind', 'bar', 'sends.kind', [AGG('count', 'sends', label='Sends')]),
        CHART('Open rate per month', 'line', 'month', [AGG('avg', 'growth', 'growth.open_rate', date='growth.month', label='Open rate')]),
        CHART('Click rate per month', 'line', 'month', [AGG('avg', 'growth', 'growth.click_rate', date='growth.month', label='Click rate')]),
        CHART('Royalties in 7 days per month', 'column', 'month', [AGG('sum', 'sends', 'sends.royalty_7d', date='sends.date', label='Royalties in 7 days')]),
        CHART('Swaps per month', 'column', 'month', [AGG('count', 'swaps', date='swaps.date', label='Swaps')]),
        CHART('Swap cost by kind', 'bar', 'swaps.kind', [AGG('sum', 'swaps', 'swaps.cost', label='Cost')]),
        CHART('Subscribers gained by swap kind', 'bar', 'swaps.kind', [AGG('sum', 'swaps', 'swaps.subscribers', label='Subscribers gained')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Launch readiness verdict", "why": "percent done, late steps and days to release turned into ready, at risk or delay, with the first three steps to finish", "where": "Launch Readiness Verdict"},
    {"name": "Late step act-first ranking", "why": "open steps ranked by days late and by how many later steps wait on them, so the first call is never a guess", "where": "Late Step Ranker"},
    {"name": "Launch share against your own average", "why": "copies in the first 7 and 30 days against your own average launch share and the copies that would have matched it", "where": "Launch Result and Launch Share"},
    {"name": "Review target planner", "why": "the reviews you want and your own response rate turned into the advance copies to send, with a spare share", "where": "Review Target Planner"},
    {"name": "Reviewer ranking with keep or remove", "why": "every reviewer scored on response rate and speed against your own targets, with a keep, test or remove verdict", "where": "Reviewer Ranking"},
    {"name": "Cost per subscriber ranker", "why": "each source ranked by cost per new subscriber and by the share of readers who stay, with a keep, watch or stop verdict", "where": "Cost per Subscriber Ranker"},
    {"name": "Swap payback with your own numbers", "why": "cost plus your time against the sales and the readers gained, with the break-even readers and the swaps to repeat", "where": "Swap Payback"},
    {"name": "Newsletter to sales per 1,000 readers", "why": "every send judged by royalties per 1,000 readers against your own average of the same kind of send", "where": "Newsletter to Sales"},
    {"name": "List growth forecast in three scenarios", "why": "list size in 3 and 6 months from your own last 12 months, Base, Best and Worst, against the size you want", "where": "List Growth Forecast"},
    {"name": "Pre-order momentum check", "why": "pre-orders so far against what your last two launches had at the same days before release: ahead, on pace or behind", "where": "Pre-order Momentum Check"}]
competitors = [
    {"what": "free launch checklist templates", "lacks": "list steps but never count days late, rank the late steps or give a ready, at risk or delay verdict"},
    {"what": "subscription newsletter dashboards", "lacks": "show opens and clicks but not royalties per 1,000 readers, cost per subscriber or the payback of a swap"},
    {"what": "generic reviewer and contact spreadsheets", "lacks": "keep names and emails but no copies sent, response rate, days to a review or keep or remove verdict"},
    {"what": "single-sheet book launch plans", "lacks": "give one fixed schedule with no launch share against your own history and no pre-order pace check"},
    {"what": "store sales dashboards", "lacks": "show sales by day but not the launch share of 12 months, the reviews per 100 copies or what a swap really paid back"}]
guide = [
    'Open Start and type your imprint name, the title of your next launch and your own targets in the yellow cells: reviews per copy, open rate, cost per subscriber, payback of a swap and the list size you want.',
    'Check Titles, Team and Launch Steps. Titles holds the release dates and pre-orders, Team holds the phones for the message links and Launch Steps holds the standard days from release.',
    'Write each launch step in Launch Tasks with its owner, due date and done date. The step check, days late and the later steps waiting fill in by themselves; Launch Readiness and Late Launch Steps show what to do first.',
    'Keep the reviewer list in Reviewers and write every advance copy in Advance Copies. The overdue check, reviews per 100 copies, Reviewer Ranking and Response by Title fill in.',
    'Write each newsletter send in Newsletter Sends, then the new and lost subscribers by source in Subscribers by Source. List Growth by Month, Send Results and Cost per Subscriber by Source fill in.',
    'Write each swap and paid promotion in Swaps and Promotions. Swap Results works out the cost per subscriber, the payback and a swap again verdict with the numbers on Start (your own numbers).',
    'After a launch write the copies of the first 7 and 30 days in Launch Results. The launch share and the verdict against your own average fill in; the pre-order columns feed the momentum check.',
    f'Use the {len(tools)} calculators to judge the launch, rank the late steps, plan the reviews, test the list, forecast its growth and check the pre-order pace.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'A first-time author with one to three books keeps one launch, a short reviewer list and one send a month; a small press reads the pen-name columns as author columns. Figures are estimates until the stores pay.']
listing = {"title": "Author and Self-Publisher Readers, Newsletter and Launch Planner Excel Template: Launch Plan, Reviewer List, List Growth, Swap Payback",
    "headline": "Launch every book with a plan, a reviewer list and a newsletter you can measure",
    "tags": ["author template", "book launch", "launch checklist", "reviewer list", "advance copies", "newsletter growth", "self publishing", "indie author", "excel template", "author business", "swap tracker", "pre-order tracker", "launch planner"],
    "description": ("Run the reader side of an author or small publishing business in one Excel workbook. Built for an independent author who publishes under one or two pen names, often with a part-time assistant and a launch coordinator. "
        "Launch Tasks lists every launch step with its owner, due date, days late and a step check, and Launch Readiness turns the next launch into a ready, at risk or delay verdict. Late Launch Steps ranks the open steps by days late and by the later steps that wait on them.\n\n"
        "Reviewers and Advance Copies keep the reviewer list (an advance copy is a free copy sent to a reviewer before release): copies sent, review due, review posted, response rate, reviews per 100 copies sent and a keep, test or remove verdict for each reviewer. "
        "Newsletter Sends, Subscribers by Source and List Growth by Month show the list size, new and lost readers, open and click rates, cost per subscriber and royalties per 1,000 readers. Swap Results works out the payback of each swap or paid promotion against your own numbers. "
        "Launch Results sets the first 7 and 30 days against your own average launch share, and the pre-order check compares your pre-orders with your last two launches.\n\n"
        f"{len(tools)} calculators cover the launch verdict, the late steps, launch share, review targets, reminders, reviewer ranking, list growth in three scenarios, cost per subscriber, swap payback, partners, clean-up and the launch week plan. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to reviewers, swap partners, an assistant, a launch coordinator and the author.\n\n"
        "This is part five of the Author and Self-Publisher Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Figures are estimates until the stores pay, and every target is your own number. It helps you keep track and does not promise sales."),
    "features": ["Launch checklist with days late and a readiness verdict", "Reviewer list with response rate and ranking", "Advance copy tracker with overdue checks", "Newsletter list growth by source and month",
                 "Cost per subscriber with keep or stop verdicts", "Swap and promotion payback with your own numbers", "Launch share against your own average", "Pre-order pace against your last two launches",
                 f"{len(tools)} calculators for launch and list decisions", f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
HINTS = {}
for _t in tables + tools:
    if _t['key'] in HINTS: _t['hint'] = HINTS[_t['key']]
s = spec(id=f'{SUITE}-p5', slug='author-publisher-readers', profession='Author and Self-Publisher Business', name='Readers, Newsletter and Launches',
         tagline='Launches, reviewers and a newsletter list you can measure', price_usd=29,
         colors={"primary": "#2B3A55", "accent": "#CE7777"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 5, "of": 8, "focus": "Readers, newsletter and launches"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'au5.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
