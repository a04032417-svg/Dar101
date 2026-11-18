"""Nonprofit Organization suite - part 3: Grants and Restricted Funds."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np3_lists import *
from np3_tables import settings, tables
from np3_tools import tools
import np3_data as D

SUITE = 'fx-20261115-nonprofit'
NOTE = "Sample wording: adapt it to your own organization and check your local rules."
YES = '{list:yesno.yes}'
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
YS = 'DATE(YEAR({today}),1,1)'
STG = lambda s: tok('gstage', s)
RCV = tok('gpay', 'Received'); SUBM = tok('rstatus', 'Submitted')
def R(t, c): return '{range:%s.%s}' % (t, c)
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
def LKD(t, idc, c): return 'IFERROR(IF(%s=0,"",%s),"")' % (LK(t, idc, c), LK(t, idc, c))

# ------------------------------------------------------------------ forms (12)
G = lambda c: LK('grants', 'grant_id', c)
forms = [
    FORM('prospect_sheet', 'Grant Prospect Sheet', 'A new grant prospect', 'grants.grant_id', F(
        ('Funder', 'grants.funder'), ('Funder type', 'grants.funder_type'), ('Program', 'grants.program'), ('Project', 'grants.project'), ('Fund', 'grants.fund'), ('Stage', 'grants.stage'), ('Asked', 'grants.asked'),
        ('Chance of an award, your estimate', 'grants.probability'), ('Owner', 'grants.owner'), ('Prospect on', 'grants.prospect_on'), ('Decision on', 'grants.decision_on'), ('Hours to write', 'grants.write_hours')) + [
        FF('Weighted amount', G('weighted'), 'money'), FF('Cost to write', G('write_cost'), 'money'), FF('Days from prospect to decision', 'IFERROR(%s-%s,"")' % (G('decision_on'), G('prospect_on')), 'int'),
        FF('Weighted amount for each writing hour', 'IFERROR(%s/%s,0)' % (G('weighted'), G('write_hours')), 'money')]),
    FORM('inquiry_sheet', 'Letter of Inquiry Sheet', 'Letter of inquiry to a funder', 'grants.grant_id', F(
        ('Funder', 'grants.funder'), ('Project', 'grants.project'), ('Program', 'grants.program'), ('Fund', 'grants.fund'), ('Asked', 'grants.asked'), ('Owner', 'grants.owner'), ('Prospect on', 'grants.prospect_on'),
        ('Inquiry sent on', 'grants.loi_on'), ('Decision on', 'grants.decision_on'), ('Restricted', 'grants.restricted')) + [
        FF('Days from prospect to inquiry', 'IFERROR(%s-%s,"")' % (G('loi_on'), G('prospect_on')), 'int'), FF('Days since the inquiry', 'IF(%s>0,{today}-%s,"")' % (G('loi_on'), G('loi_on')), 'int'),
        FF('Chance after an inquiry, your estimate', '{set:prob_inquiry}', 'pct')]),
    FORM('application_sheet', 'Grant Application Sheet', 'Grant application', 'grants.grant_id', F(
        ('Funder', 'grants.funder'), ('Project', 'grants.project'), ('Program', 'grants.program'), ('Fund', 'grants.fund'), ('Asked', 'grants.asked'), ('Owner', 'grants.owner'), ('Applied on', 'grants.applied_on'),
        ('Decision on', 'grants.decision_on'), ('Hours to write', 'grants.write_hours'), ('Stage', 'grants.stage')) + [
        FF('Days since the application', 'IF(%s>0,{today}-%s,"")' % (G('applied_on'), G('applied_on')), 'int'), FF('Cost to write', G('write_cost'), 'money'), FF('Weighted amount', G('weighted'), 'money')]),
    FORM('award_sheet', 'Award Record Sheet', 'Award record', 'grants.grant_id', F(
        ('Funder', 'grants.funder'), ('Project', 'grants.project'), ('Program', 'grants.program'), ('Fund', 'grants.fund'), ('Asked', 'grants.asked'), ('Awarded', 'grants.awarded'), ('Decision on', 'grants.decision_on'),
        ('Start on', 'grants.start_on'), ('End on', 'grants.end_on'), ('Owner', 'grants.owner'), ('Restricted', 'grants.restricted')) + [
        FF('Share of the amount asked', 'IFERROR(%s/%s,0)' % (G('awarded'), G('asked')), 'pct'), FF('Term in months', 'IFERROR(ROUND((%s-%s)/30.4375,0),"")' % (G('end_on'), G('start_on')), 'int'),
        FF('Average award for each month', 'IFERROR(%s/ROUND((%s-%s)/30.4375,0),0)' % (G('awarded'), G('end_on'), G('start_on')), 'money')]),
    FORM('budget_sheet', 'Grant Budget Sheet', 'Grant budget against spending', 'grant_actual.grant_id', F(
        ('Funder', 'grant_actual.funder'), ('Project', 'grant_actual.project'), ('Awarded', 'grant_actual.awarded'), ('Start on', 'grant_actual.start_on'), ('End on', 'grant_actual.end_on'), ('Spent', 'grant_actual.spent'),
        ('Remaining', 'grant_actual.remaining'), ('Share of the period', 'grant_actual.elapsed'), ('Share spent', 'grant_actual.share_spent'), ('Forecast to the end', 'grant_actual.forecast'), ('Status', 'grant_actual.status')) + [
        FF('Staff line of the budget', 'SUMIFS(%s,%s,{pick},%s,%s)' % (R('grant_budget_lines', 'budget'), R('grant_budget_lines', 'grant_id'), R('grant_budget_lines', 'line'), tok('gline', 'Staff')), 'money'),
        FF('Direct costs line of the budget', 'SUMIFS(%s,%s,{pick},%s,%s)' % (R('grant_budget_lines', 'budget'), R('grant_budget_lines', 'grant_id'), R('grant_budget_lines', 'line'), tok('gline', 'Direct costs')), 'money'),
        FF('Other costs line of the budget', 'SUMIFS(%s,%s,{pick},%s,%s)' % (R('grant_budget_lines', 'budget'), R('grant_budget_lines', 'grant_id'), R('grant_budget_lines', 'line'), tok('gline', 'Other costs')), 'money')]),
    FORM('payment_sheet', 'Grant Payment Sheet', 'Grant instalment', 'grant_payments.pay_id', F(
        ('Grant', 'grant_payments.grant_id'), ('Funder', 'grant_payments.funder'), ('Project', 'grant_payments.project'), ('Instalment number', 'grant_payments.number'), ('Due date', 'grant_payments.due_date'), ('Amount', 'grant_payments.amount'),
        ('Received on', 'grant_payments.received_on'), ('Status', 'grant_payments.status'), ('Days late', 'grant_payments.days_late'), ('Timing', 'grant_payments.timing')) + [
        FF('Instalments of this grant', 'COUNTIFS(%s,%s)' % (R('grant_payments', 'grant_id'), LK('grant_payments', 'pay_id', 'grant_id')), 'int'),
        FF('Money of this grant still to come', 'SUMIFS(%s,%s,%s,%s,"<>"&%s)' % (R('grant_payments', 'amount'), R('grant_payments', 'grant_id'), LK('grant_payments', 'pay_id', 'grant_id'), R('grant_payments', 'status'), RCV), 'money')]),
    FORM('report_sheet', 'Grant Report Sheet', 'Funder report', 'grant_reports.report_id', F(
        ('Grant', 'grant_reports.grant_id'), ('Funder', 'grant_reports.funder'), ('Project', 'grant_reports.project'), ('Kind', 'grant_reports.kind'), ('Due date', 'grant_reports.due_date'),
        ('Status', 'grant_reports.status'), ('Owner', 'grant_reports.owner'), ('Days to due', 'grant_reports.days_to_due'), ('Share spent', 'grant_reports.share_spent'), ('Share of the period', 'grant_reports.elapsed'), ('Action', 'grant_reports.action')) + [
        FF('Spent minus the share of the period', 'IFERROR(%s,"")' % LK('grant_reports', 'report_id', 'gap'), 'pct'), FF('Reports of this grant', 'COUNTIFS(%s,%s)' % (R('grant_reports', 'grant_id'), LK('grant_reports', 'report_id', 'grant_id')), 'int'),
        FF('Of those, not yet submitted', 'COUNTIFS(%s,%s,%s,"<>"&%s)' % (R('grant_reports', 'grant_id'), LK('grant_reports', 'report_id', 'grant_id'), R('grant_reports', 'status'), SUBM), 'int')]),
    FORM('spending_sheet', 'Grant Spending Sheet', 'Expense coded to a grant', 'grant_spending.expense_id', F(
        ('Date', 'grant_spending.date'), ('Grant', 'grant_spending.grant_id'), ('Funder', 'grant_spending.funder'), ('Category', 'grant_spending.category'), ('Amount', 'grant_spending.amount'), ('Program', 'grant_spending.program'),
        ('Fund', 'grant_spending.fund'), ('Budget line', 'grant_spending.line')) + [
        FF('Share of the award', 'IFERROR(%s/INDEX(%s,MATCH(%s,%s,0)),0)' % (LK('grant_spending', 'expense_id', 'amount'), R('grant_actual', 'awarded'), LK('grant_spending', 'expense_id', 'grant_id'), R('grant_actual', 'grant_id')), 'pct'),
        FF('Remaining on the grant', 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),"")' % (R('grant_actual', 'remaining'), LK('grant_spending', 'expense_id', 'grant_id'), R('grant_actual', 'grant_id')), 'money'),
        FF('Spent on this budget line so far', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('grant_spending', 'amount'), R('grant_spending', 'grant_id'), LK('grant_spending', 'expense_id', 'grant_id'), R('grant_spending', 'line'), LK('grant_spending', 'expense_id', 'line')), 'money')]),
    FORM('transfer_sheet', 'Fund Transfer Sheet', 'Transfer from one fund to General Fund', 'fund_months.row_id', F(
        ('Fund', 'fund_months.fund'), ('Month', 'fund_months.month'), ('Restriction', 'fund_months.restriction'), ('Receipts', 'fund_months.receipts'), ('Released', 'fund_months.released'), ('Transfers', 'fund_months.transfers'),
        ('Balance', 'fund_months.balance'), ('Money left', 'fund_months.spare')) + [
        FF('Balance after moving all the money left', '%s-%s' % (LK('fund_months', 'row_id', 'balance'), LK('fund_months', 'row_id', 'spare')), 'money'),
        FF('General Fund balance this month', 'SUMIFS(%s,%s,%s,%s,1)' % (R('fund_position', 'balance'), R('fund_position', 'fund'), tok('fund', 'General Fund'), R('fund_position', 'is_now')), 'money'),
        FF('General Fund after the transfer', 'SUMIFS(%s,%s,%s,%s,1)+%s' % (R('fund_position', 'balance'), R('fund_position', 'fund'), tok('fund', 'General Fund'), R('fund_position', 'is_now'), LK('fund_months', 'row_id', 'spare')), 'money')]),
    FORM('release_sheet', 'Release from Restriction Sheet', 'Release from restriction', 'release_journal.release_id', F(
        ('Date', 'release_journal.date'), ('Fund', 'release_journal.fund'), ('Amount', 'release_journal.amount'), ('Program', 'release_journal.program'), ('Grant', 'release_journal.grant_id'), ('Funder', 'release_journal.funder')) + [
        FF('Balance of the fund this month', 'SUMIFS(%s,%s,%s,%s,1)' % (R('fund_position', 'balance'), R('fund_position', 'fund'), LK('release_journal', 'release_id', 'fund'), R('fund_position', 'is_now')), 'money'),
        FF('Released from this fund this year', 'SUMIFS(%s,%s,%s,%s,">="&%s)' % (R('release_journal', 'amount'), R('release_journal', 'fund'), LK('release_journal', 'release_id', 'fund'), R('release_journal', 'date'), YS), 'money'),
        FF('Release lines of this fund this month', 'COUNTIFS(%s,%s,%s,%s)' % (R('release_journal', 'fund'), LK('release_journal', 'release_id', 'fund'), R('release_journal', 'month'), MS), 'int')]),
    FORM('timesplit_sheet', 'Staff Time Split Sheet', 'Staff time split for one month', 'staff_check.check_id', F(
        ('Staff member', 'staff_check.staff'), ('Month', 'staff_check.month'), ('Total percent', 'staff_check.total_percent'), ('Difference from 100%', 'staff_check.diff'), ('Flag', 'staff_check.flag'),
        ('Percent on grants', 'staff_check.grant_percent'), ('Cost to grants', 'staff_check.cost_to_grants'), ('Total cost', 'staff_check.total_cost')) + [
        FF('Percent still to place', 'MAX(0,1-%s)' % LK('staff_check', 'check_id', 'total_percent'), 'pct'), FF('Percent to take away', 'MAX(0,%s-1)' % LK('staff_check', 'check_id', 'total_percent'), 'pct'),
        FF('Cost of one percent of the month', 'IFERROR(%s/(%s*100),0)' % (LK('staff_check', 'check_id', 'total_cost'), LK('staff_check', 'check_id', 'total_percent')), 'money')]),
    FORM('apply_sheet', 'Apply or Skip Sheet', 'Apply or skip a grant', 'grants.grant_id', F(
        ('Funder', 'grants.funder'), ('Funder type', 'grants.funder_type'), ('Project', 'grants.project'), ('Stage', 'grants.stage'), ('Asked', 'grants.asked'), ('Chance of an award, your estimate', 'grants.probability'), ('Hours to write', 'grants.write_hours')) + [
        FF('Cost to write', G('write_cost'), 'money'), FF('Expected award', 'ROUND(%s*%s,0)' % (G('asked'), G('probability')), 'money'),
        FF('Net expected value per writing hour', 'IFERROR((%s*%s-%s)/%s,0)' % (G('asked'), G('probability'), G('write_cost'), G('write_hours')), 'money'),
        FF('Your own money won for each writing hour', 'IFERROR(SUMIFS(%s,%s,1)/SUMIFS(%s,%s,1),0)' % (R('grants', 'awarded'), R('grants', 'decided'), R('grants', 'write_hours'), R('grants', 'decided')), 'money'),
        FF('Verdict', 'IF(IFERROR((%s*%s-%s)/%s,0)>=0.25*IFERROR(SUMIFS(%s,%s,1)/SUMIFS(%s,%s,1),0),%s,IF(IFERROR((%s*%s-%s)/%s,0)>=0.1*IFERROR(SUMIFS(%s,%s,1)/SUMIFS(%s,%s,1),0),%s,%s))' % (
            G('asked'), G('probability'), G('write_cost'), G('write_hours'), R('grants', 'awarded'), R('grants', 'decided'), R('grants', 'write_hours'), R('grants', 'decided'), c3('Apply'),
            G('asked'), G('probability'), G('write_cost'), G('write_hours'), R('grants', 'awarded'), R('grants', 'decided'), R('grants', 'write_hours'), R('grants', 'decided'), c3('Apply if time'), c3('Skip')), 'text')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
def C_(t, c): return '{col:%s.%s}' % (t, c)
documents = [
    DOC('pipeline_doc', 'Grant Pipeline Report', 'Grant pipeline report for one stage', 'pipeline_stage.stage', [
        'Grant pipeline report of {set:org}, dated {today}. Stage: {col:pipeline_stage.stage}.',
        'Money asked at this stage: {col:pipeline_stage.asked}. Weighted amount at this stage: {col:pipeline_stage.weighted}. The weighted amount is the money asked times your own chance of an award, so it is your estimate and not a promise.',
        'Use one page for each stage. Together the open stages (Prospect, Letter of inquiry and Application) show the grant income you may expect and when to follow up.',
        'The chance of an award at each stage is set on the Start sheet. Review the chances once a year against your own wins and declines.'], ['Development manager', 'Executive director'], NOTE),
    DOC('calendar_doc', 'Grant Calendar 90 Days', 'Grant calendar item for the next 90 days', 'calendar90.item_id', [
        'Grant calendar of {set:org}, dated {today}. Item: {col:calendar90.item_id}, a {col:calendar90.kind} of {col:calendar90.funder}, grant {col:calendar90.grant_id}.',
        'Date: {col:calendar90.date}. Days away: {col:calendar90.days_away}. Amount: {col:calendar90.amount}. Owner: {col:calendar90.owner}. State: {col:calendar90.state}.',
        'In the next 90 days there are {col:calendar90.open_n} open items, {col:calendar90.late_n} are late and {col:calendar90.week_n} are due this week. Money still to come: {col:calendar90.open_money}.',
        'Check each item against the funder\'s agreement. Late items come first.'], ['Development manager', 'Executive director'], NOTE),
    DOC('inquiry_doc', 'Letter of Inquiry Outline', 'Letter of inquiry outline', 'grants.grant_id', [
        'Letter of inquiry of {set:org}, dated {today}. To: {col:grants.funder}. Project: {col:grants.project}, program {col:grants.program}.',
        'Opening: thank you for the chance to introduce {col:grants.project}. We ask {col:grants.asked} from {col:grants.funder} for this work, paid into {col:grants.fund}.',
        'Need: describe in two or three sentences the need that the project meets, in your own words and with the numbers you keep. Plan: what you will do, when and with whom. Result: what you will count and report back.',
        'Budget: the amount asked, the share of the cost it covers and the other sources. Close: name the contact person ({col:grants.owner}) and the date you hope for a reply ({col:grants.expected_on}).'], ['Owner of the grant', 'Executive director'], NOTE),
    DOC('acceptance_doc', 'Award Acceptance Letter', 'Award acceptance letter', 'grants.grant_id', [
        'Letter of {set:org}, dated {today}. To: {col:grants.funder}. Project: {col:grants.project}.',
        'Thank you for the award of {col:grants.awarded}, decided on {col:grants.decision_on}. We accept the award and will use it for {col:grants.project} in {col:grants.program}.',
        'The grant period runs from {col:grants.start_on} to {col:grants.end_on}. We will hold the money in {col:grants.fund} and report as your agreement asks.',
        'Please tell us the payment dates and the report dates in writing so that we can plan. Check the terms of the award against your own rules before you sign.'], ['Executive director', 'Funder'], NOTE),
    DOC('report_cover_doc', 'Report Cover Note', 'Cover note for a funder report', 'grant_reports.report_id', [
        'Cover note of {set:org}, dated {today}. To: {col:grant_reports.funder}. Report {col:grant_reports.report_id}, a {col:grant_reports.kind} report on {col:grant_reports.project}, due {col:grant_reports.due_date}.',
        'Spending: {col:grant_reports.share_spent} of the award is spent and {col:grant_reports.elapsed} of the grant period has passed. Explain in a sentence any difference between the two.',
        'People served in the period: write the number from your program records here: __________. Main results of the period: __________.',
        'Thank you for your support. Please contact {col:grant_reports.owner} with any question.'], ['Report owner', 'Executive director'], NOTE),
    DOC('budget_doc', 'Grant Budget Statement', 'Grant budget against actual statement', 'grant_actual.grant_id', [
        'Statement of {set:org}, dated {today}. Funder: {col:grant_actual.funder}. Project: {col:grant_actual.project}. Grant {col:grant_actual.grant_id}.',
        'Awarded: {col:grant_actual.awarded}. Spent to date: {col:grant_actual.spent}. Remaining: {col:grant_actual.remaining}. Grant period: {col:grant_actual.start_on} to {col:grant_actual.end_on}.',
        'Share of the period that has passed: {col:grant_actual.elapsed}. Share of the award spent: {col:grant_actual.share_spent}. Forecast to the end date at the present pace: {col:grant_actual.forecast}.',
        'Status: {col:grant_actual.status}. Money at risk of being returned at the present pace: {col:grant_actual.at_risk}. This is your estimate, not a promise.'], ['Program manager', 'Executive director'], NOTE),
    DOC('thanks_doc', 'Funder Thank-You Letter', 'Thank-you letter to a funder for an instalment', 'grant_payments.pay_id', [
        'Letter of {set:org}, dated {today}. To: {col:grant_payments.funder}.',
        'Thank you for instalment {col:grant_payments.number} of {col:grant_payments.amount} for {col:grant_payments.project}, received on {col:grant_payments.received_on}.',
        'Your support keeps the work going. We will report as agreed and we would be glad to show you the program in person.',
        'Please keep this letter as a record of the payment.'], ['Executive director', 'Funder'], NOTE),
    DOC('reminder_doc', 'Late Payment Reminder', 'Late payment reminder to a funder', 'grant_payments.pay_id', [
        'Letter of {set:org}, dated {today}. To: {col:grant_payments.funder}. Grant {col:grant_payments.grant_id}, {col:grant_payments.project}.',
        'Instalment {col:grant_payments.number} of {col:grant_payments.amount} was due on {col:grant_payments.due_date}. We have not yet received it, and it is now {col:grant_payments.days_late} days past the due date.',
        'Could you tell us when we may expect the payment, or whether you need anything from us first? If you paid it recently, please accept our thanks and ignore this letter.',
        'Contact: {col:grant_payments.funder} program contact and our development manager.'], ['Development manager', 'Funder'], NOTE),
    DOC('fund_doc', 'Restricted Fund Statement', 'Restricted fund statement for one fund and month', 'fund_months.row_id', [
        'Fund statement of {set:org}, dated {today}. Fund: {col:fund_months.fund}. Month: {col:fund_months.month}. Restriction: {col:fund_months.restriction}.',
        'Receipts of the month: {col:fund_months.receipts}. Released from restriction (spent money moved from the fund to expense): {col:fund_months.released}. Transfers: {col:fund_months.transfers}. Balance at the end of the month: {col:fund_months.balance}.',
        'Receipts this year to the month: {col:fund_months.receipts_ytd}. Released this year to the month: {col:fund_months.released_ytd}.',
        'A balance below zero means more was charged to the fund than it holds. Ask your accountant how to correct it.'], ['Bookkeeper', 'Treasurer'], NOTE),
    DOC('release_doc', 'Release Journal Page', 'Release from restriction journal page', 'release_journal.release_id', [
        'Release journal page of {set:org}, dated {today}. Entry: {col:release_journal.release_id}, dated {col:release_journal.date}.',
        'Fund: {col:release_journal.fund}. Amount released: {col:release_journal.amount}. Program: {col:release_journal.program}. Grant: {col:release_journal.grant_id}, funder {col:release_journal.funder}.',
        'The release moves the amount from the restricted fund to expense because the money was spent for the purpose it was given for.',
        'Check the entry against the spending coded to the grant. Ask your accountant what your own rules need.'], ['Bookkeeper', 'Executive director'], NOTE),
    DOC('timesheet_doc', 'Staff Time Sheet by Grant', 'Staff time sheet for one staff month', 'staff_check.check_id', [
        'Staff time sheet of {set:org}, dated {today}. Staff member: {col:staff_check.staff}. Month: {col:staff_check.month}.',
        'Total of the month: {col:staff_check.total_percent}. Difference from 100%: {col:staff_check.diff}. Flag: {col:staff_check.flag}.',
        'Percent of the month on grants: {col:staff_check.grant_percent}. Cost charged to grants: {col:staff_check.cost_to_grants}. Total cost of the month: {col:staff_check.total_cost}.',
        'The staff member confirms that this split is a fair record of the month. Keep the signed page with the grant file.'], ['Staff member', 'Program manager'], NOTE),
    DOC('next_year_doc', 'Grant Calendar Next Year', 'Grant calendar for one quarter of next year', 'income_quarter.quarter_start', [
        'Grant calendar of {set:org}, dated {today}. Quarter from {col:income_quarter.quarter_start} to {col:income_quarter.quarter_end}.',
        'Instalments due: {col:income_quarter.pay_due}, together {col:income_quarter.awarded_inst}. Reports due: {col:income_quarter.reports_due}. Weighted pipeline expected: {col:income_quarter.weighted}, your estimate.',
        'Total grant income for the quarter: {col:income_quarter.total}, against a quarter of your budget of {col:income_quarter.needed}. Over or short: {col:income_quarter.gap} ({col:income_quarter.status}).',
        'Use one page for each quarter to plan the writing, the reports and the follow-up.'], ['Development manager', 'Executive director'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('prospect_chk', 'New Grant Prospect Steps', 'grants', 'grants.prospect_on', [('Check the funder\'s purpose and limits', 0), ('Check that the project fits the purpose', 3), ('Decide who owns the grant', 5), ('Find the deadline and the reporting rules', 7), ('Write down the hours you expect to need', 10), ('Decide: send a letter of inquiry, apply or skip', 14)]),
    CHK('submission_chk', 'Application Submission Steps', 'grants', 'grants.applied_on', [('Check the budget adds up', -10), ('Check the attachments', -7), ('Ask the executive director to read it', -5), ('Check the amount asked against the budget', -3), ('Submit before the deadline', 0), ('Send a short thank-you note', 1), ('Note the expected decision date', 1)]),
    CHK('award_chk', 'Award Received Steps', 'grants', 'grants.decision_on', [('Read the award terms carefully', 0), ('Send the acceptance letter', 3), ('Open the fund and the budget lines', 5), ('Enter the payment dates and the report dates', 7), ('Tell the program manager the spending rules', 10), ('Add the grant to staff time', 14)]),
    CHK('report_write_chk', 'Report Writing Steps', 'grant_reports', 'grant_reports.due_date', [('Ask the program manager for people served numbers', -30), ('Pull spending against budget', -21), ('Write the draft', -14), ('Ask the executive director to review', -7), ('Fix the numbers with the bookkeeper', -5)]),
    CHK('report_submit_chk', 'Report Submission Steps', 'grant_reports', 'grant_reports.due_date', [('Check the report against the funder\'s form', -5), ('Attach the budget statement', -3), ('Submit the report', 0), ('Mark the report submitted', 0), ('Send the cover note', 1), ('Keep a copy with the grant file', 2)]),
    CHK('budget_check_chk', 'Monthly Grant Budget Check', 'free_money', 'free_money.month', [('Run Grant Budget vs Actual', 31), ('Flag grants behind the period', 32), ('Flag grants over budget', 32), ('Run the Underspend Rescue Plan for those behind', 33), ('Tell the program manager', 34), ('Note the actions', 35)]),
    CHK('quarterly_chk', 'Quarterly Grant Review', 'income_quarter', 'income_quarter.quarter_start', [('Review the pipeline by stage', 80), ('Update the chances you estimate', 81), ('Check the win rate by funder type', 82), ('Check grant income against the budget', 83), ('Plan the writing for the next quarter', 85), ('Report to the board', 88)]),
    CHK('fund_month_chk', 'Restricted Fund Month-End', 'fund_months', 'fund_months.month', [('Check every fund balance', 30), ('Look for any fund below zero', 31), ('Correct coding with the bookkeeper', 32), ('Check receipts to each fund', 33), ('Send balances to the accountant', 35)]),
    CHK('release_chk', 'Release from Restriction Steps', 'release_journal', 'release_journal.date', [('Add up spending coded to each restricted fund', 0), ('Check the grant codes', 1), ('Write the release journal lines', 2), ('Check the fund balances after the release', 3), ('Ask your accountant to review', 7)]),
    CHK('timesplit_chk', 'Staff Time Split Month-End', 'staff_check', 'staff_check.month', [('Ask each staff member to confirm their split', 28), ('Check every month totals 100%', 30), ('Fix the months that are short or over', 31), ('Check the cost charged to each grant', 32), ('Send the totals to the bookkeeper', 33)]),
    CHK('closeout_chk', 'Grant Close-Out Steps', 'grants', 'grants.end_on', [('Check that all money is spent or agreed', -30), ('Ask for an extension if money is left', -21), ('Write the final report', -14), ('Submit the final report', 0), ('Release the last spending from restriction', 5), ('Thank the funder', 7), ('Close the fund or move it to General Fund', 14)]),
    CHK('founder_chk', 'First Grant for a Founder', 'grants', 'grants.prospect_on', [('List two funders that give to work like yours', 0), ('Read their guidelines and deadlines', 3), ('Write one page about the need and the plan', 10), ('Make a small budget', 14), ('Ask a volunteer to read it', 17), ('Send the application', 21), ('Record the grant on the Grants sheet', 21)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
fn = first_name
DM, ED, PM, BK, ACC, TR = fn(DEV_MANAGER), fn(OWNER), fn(D.TEAMID['NP-03']['name']), fn(D.TEAMID['NP-08']['name']), fn(D.TEAMID['NP-09']['name']), fn(D.TREAS['name'])
VN = fn(D.VOL['name'])
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('f_consider', 'Funder: thank you for considering', 'grants', 'grants.phone', 'Hello {funder}, thank you for considering {project}. Our letter is attached. {org}'),
    M('f_applied', 'Funder: our application was sent', 'grants', 'grants.phone', 'Hello {funder}, our application for {project} was sent on {applied_on}. Please tell us if you need anything more. {org}'),
    M('f_award', 'Funder: thank you for the award', 'grants', 'grants.phone', 'Hello {funder}, thank you for the award of {awarded} for {project}. We start on {start_on}. {org}'),
    M('f_instalment', 'Funder: your instalment', 'grant_payments', 'grant_payments.phone', 'Hello {funder}, instalment {number} of {amount} was due on {due_date}. Could you tell us when we may expect it? {org}'),
    M('f_report', 'Funder: our report is attached', 'grant_reports', 'grant_reports.phone', 'Hello {funder}, our report for {project} is attached, due {due_date}. Thank you for your support. {org}'),
    M('f_extension', 'Funder: ask for a report extension', 'grant_reports', 'grant_reports.phone', 'Hello {funder}, we ask for an extension of the report on {project} due on {due_date}. May we agree a new date? {org}'),
    M('f_move', 'Funder: ask to move between lines', 'grant_lines', 'grant_lines.phone', 'Hello {funder}, we ask to move {over_by} between budget lines of grant {grant_id}. Please tell us if you agree. {org}'),
    M('f_end', 'Funder: ask to extend the end date', 'grant_actual', 'grant_actual.phone', 'Hello {funder}, we ask to extend the end date of grant {grant_id} to {new_end} so that the work is finished well. {org}'),
    M('f_received', 'Funder: thank you, we received it', 'grant_payments', 'grant_payments.phone', 'Hello {funder}, thank you, we received {amount} on {received_on}. {org}'),
    M('f_update', 'Funder: an update on the project', 'grant_actual', 'grant_actual.phone', 'Hello {funder}, here is an update on {project}: {share_spent} of the award is spent and {elapsed} of the period has passed. {org}'),
    M('f_visit', 'Funder: invitation to a visit', 'grants', 'grants.phone', 'Hello {funder}, we invite you to see {project} on {visit_on}. We would be glad to welcome you. {org}'),
    M('f_declined', 'Funder: not successful, ask feedback', 'grants', 'grants.phone', 'Hello {funder}, we were not successful with {project} this time. May we ask for feedback for the next time? {org}'),
    M('po_spending', 'Program officer: spending to date', 'grant_actual', 'grant_actual.po_phone', 'Hello Isabella, a short note on grant {grant_id}: {share_spent} of the award is spent, {remaining} remains. {org}'),
    M('po_visit', 'Program officer: thank you for the visit', 'grants', 'grants.phone', 'Hello {funder}, thank you for the visit on {visit_on}. We hope it gave you a good picture of {project}. {org}'),
    M('dm_reports', 'Development manager: reports due', 'grant_reports', 'grant_reports.dev_phone', 'Hello %s, {due_n} reports are due in the next {warn_days} days. Please check the Report Due Ranker. {org}' % DM),
    M('dm_report_one', 'Development manager: one report is due', 'grant_reports', 'grant_reports.dev_phone', 'Hello %s, the {funder} report is due in {days_to_due} days and spending is at {share_spent}. {org}' % DM),
    M('dm_late', 'Development manager: instalment late', 'grant_payments', 'grant_payments.dev_phone', 'Hello %s, the {funder} instalment of {amount} is {days_late} days late. {org}' % DM),
    M('dm_pipeline', 'Development manager: pipeline', 'grants', 'grants.dev_phone', 'Hello %s, {pipe_n} grants are in the pipeline worth {pipe_weighted}, your estimate. {org}' % DM),
    M('ed_income', 'Executive director: quarter income', 'income_quarter', 'income_quarter.ed_phone', 'Hello %s, grant income for the quarter starting {quarter_start} is {total} against {needed} in the budget. {org}' % ED),
    M('ed_underspent', 'Executive director: grants underspent', 'grant_actual', 'grant_actual.ed_phone', 'Hello %s, {under_n} grants are underspent, {risk_total} is at risk of being returned. {org}' % ED),
    M('pm_people', 'Program manager: people served numbers', 'grant_reports', 'grant_reports.pm_phone', 'Hello %s, please send the people served numbers for the {funder} report by {due_date}. {org}' % PM),
    M('pm_fund', 'Program manager: fund balance', 'fund_months', 'fund_months.pm_phone', 'Hello %s, {fund} has {balance} left. Please plan spending for {plan_month}. {org}' % PM),
    M('pm_remaining', 'Program manager: money left on a grant', 'grant_actual', 'grant_actual.pm_phone', 'Hello %s, grant {grant_id} has {remaining} left to spend by {end_on}. {org}' % PM),
    M('bk_code', 'Bookkeeper: code an expense', 'grant_spending', 'grant_spending.bk_phone', 'Hello %s, please code {amount} of expense {expense_id} to {grant_id}. {org}' % BK),
    M('bk_below', 'Bookkeeper: fund below zero', 'fund_months', 'fund_months.bk_phone', 'Hello %s, {fund} is below zero by {below_by}. Please check the coding. {org}' % BK),
    M('bk_release', 'Bookkeeper: release from restriction', 'release_journal', 'release_journal.bk_phone', 'Hello %s, please release {amount} from {fund} for {month}. {org}' % BK),
    M('bk_time', 'Bookkeeper: staff time total', 'staff_check', 'staff_check.bk_phone', 'Hello %s, staff time of {staff} for {month} totals {total_percent}. Please check. {org}' % BK),
    M('bk_transfer', 'Bookkeeper: transfer to General Fund', 'fund_months', 'fund_months.bk_phone', 'Hello %s, please prepare a transfer of {spare} from {fund} to General Fund once the board agrees. {org}' % BK),
    M('acc_funds', 'Accountant: fund balances', 'fund_months', 'fund_months.acc_phone', 'Hello %s, restricted fund balances at {as_of} are attached. {org}' % ACC),
    M('acc_lines', 'Accountant: spending by line', 'grant_lines', 'grant_lines.acc_phone', 'Hello %s, grant spending by line for {grant_id} is attached. {org}' % ACC),
    M('board_free', 'Board member: free money', 'free_money', 'free_money.treas_phone', 'Hello %s, free money is {free_money}, which is {reserve_months} months of average expense. {org}' % TR),
    M('fin_near', 'Finance committee: funds near zero', 'fund_months', 'fund_months.treas_phone', 'Hello finance committee, {near_n} restricted funds are near zero or below. {org}'),
    M('staff_confirm', 'Staff member: confirm your time split', 'staff_check', 'staff_check.phone', 'Hello {staff}, please confirm your time split for {month}. It totals {total_percent}. {org}'),
    M('vol_report', 'Volunteer: help assemble a report', 'grant_reports', 'grant_reports.vol_phone', 'Hello %s, could you help assemble the {funder} report? It is due {due_date}. {org}' % VN),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def OPEN3(f): return '(' + '+'.join(f % s for s in [STG(x) for x in OPEN_STAGES]) + ')'
NOWF = '%s,1' % R('fund_position', 'is_now')
kpis = [
    KPI('Grants in the pipeline', OPEN3('COUNTIFS({range:grants.stage},%s)'), 'int'),
    KPI('Weighted pipeline value', OPEN3('SUMIFS({range:grants.weighted},{range:grants.stage},%s)'), 'money'),
    KPI('Grants awarded this year', 'COUNTIFS(%s,">0",%s,">="&%s)' % (R('grants', 'awarded'), R('grants', 'decision_on'), YS), 'int'),
    KPI('Money awarded this year', 'SUMIFS(%s,%s,">="&%s)' % (R('grants', 'awarded'), R('grants', 'decision_on'), YS), 'money'),
    KPI('Grants declined this year', 'COUNTIFS(%s,%s,%s,">="&%s)' % (R('grants', 'stage'), STG('Declined'), R('grants', 'decision_on'), YS), 'int'),
    KPI('Own win rate, last 12 months', 'IFERROR(SUMIFS(%s,%s,">="&({today}-365))/SUMIFS(%s,%s,">="&({today}-365)),0)' % (R('grants', 'won'), R('grants', 'decision_on'), R('grants', 'decided'), R('grants', 'decision_on')), 'pct'),
    KPI('Money asked, not yet decided', OPEN3('SUMIFS({range:grants.asked},{range:grants.stage},%s)'), 'money'),
    KPI('Decisions expected, next 90 days', 'COUNTIFS(%s,">="&{today},%s,"<="&({today}+90))' % (R('grants', 'expected_on'), R('grants', 'expected_on')), 'int'),
    KPI('Instalments due, next 30 days', 'COUNTIFS(%s,"<>"&%s,%s,">="&{today},%s,"<="&({today}+30))' % (R('grant_payments', 'status'), RCV, R('grant_payments', 'due_date'), R('grant_payments', 'due_date')), 'int'),
    KPI('Instalments late now', 'COUNTIFS(%s,">0")' % R('grant_payments', 'days_late'), 'int'),
    KPI('Money late now', 'SUMIFS(%s,%s,">0")' % (R('grant_payments', 'amount'), R('grant_payments', 'days_late')), 'money'),
    KPI('Reports due, next 30 days', 'COUNTIFS(%s,"<>"&%s,%s,">="&{today},%s,"<="&({today}+30))' % (R('grant_reports', 'status'), SUBM, R('grant_reports', 'due_date'), R('grant_reports', 'due_date')), 'int'),
    KPI('Reports late now', 'COUNTIFS(%s,"<>"&%s,%s,"<"&{today})' % (R('grant_reports', 'status'), SUBM, R('grant_reports', 'due_date')), 'int'),
    KPI('Days to the next report', 'IFERROR(SMALL(%s,COUNTIF(%s,"<0")+1),0)' % (R('grant_reports', 'days_to_due'), R('grant_reports', 'days_to_due')), 'int'),
    KPI('Grants with spending behind the period', 'COUNTIFS(%s,%s)' % (R('grant_actual', 'status'), c1('Underspending')), 'int'),
    KPI('Money at risk of being returned', 'SUM(%s)' % R('grant_actual', 'at_risk'), 'money'),
    KPI('Grants overspent', 'COUNTIFS(%s,%s)' % (R('grant_actual', 'status'), c1('Overspending')), 'int'),
    KPI('Spent to date on active grants', 'SUMIFS(%s,%s,"<="&{today},%s,">="&{today})' % (R('grant_actual', 'spent'), R('grant_actual', 'start_on'), R('grant_actual', 'end_on')), 'money'),
    KPI('Remaining on active grants', 'SUMIFS(%s,%s,"<="&{today},%s,">="&{today})' % (R('grant_actual', 'remaining'), R('grant_actual', 'start_on'), R('grant_actual', 'end_on')), 'money'),
    KPI('Restricted money held now', 'SUMIFS(%s,%s)' % (R('fund_position', 'restricted_balance'), NOWF), 'money'),
    KPI('Restricted funds below zero', 'COUNTIFS(%s,%s,%s,1,%s,1)' % (R('fund_position', 'status'), c1('Below zero'), R('fund_position', 'is_now'), R('fund_position', 'is_restricted')), 'int'),
    KPI('Total below zero', '-SUMIFS(%s,%s,"<0",%s,1,%s,1)' % (R('fund_position', 'balance'), R('fund_position', 'balance'), R('fund_position', 'is_now'), R('fund_position', 'is_restricted')), 'money'),
    KPI('Money released this month', 'SUMIFS(%s,%s,%s)' % (R('release_journal', 'amount'), R('release_journal', 'month'), MS), 'money'),
    KPI('Money released this year', 'SUMIFS(%s,%s,">="&%s)' % (R('release_journal', 'amount'), R('release_journal', 'date'), YS), 'money'),
    KPI('Free money now', 'SUMIFS(%s,%s,1)' % (R('free_money', 'free_money'), R('free_money', 'is_now')), 'money'),
    KPI('Months of reserve now', 'SUMIFS(%s,%s,1)' % (R('free_money', 'reserve_months'), R('free_money', 'is_now')), 'num'),
    KPI('Staff months not at 100%', 'COUNTIFS(%s,%s)+COUNTIFS(%s,%s)' % (R('staff_check', 'flag'), c1('Short of 100%'), R('staff_check', 'flag'), c1('Over 100%')), 'int'),
    KPI('Cost allocated to grants this month', 'SUMIFS(%s,%s,%s,%s,%s)' % (R('staff_time', 'cost'), R('staff_time', 'month'), MS, R('staff_time', 'target_kind'), tok('tkind', 'Grant')), 'money'),
    KPI('Hours to write open applications', 'SUMIFS(%s,%s,%s)+SUMIFS(%s,%s,%s)' % (R('grants', 'write_hours'), R('grants', 'stage'), STG('Prospect'), R('grants', 'write_hours'), R('grants', 'stage'), STG('Letter of inquiry')), 'int'),
    KPI('Best funder type by win rate', 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0))&"","")' % (R('win_rate', 'funder_type'), R('win_rate', 'qualified'), R('win_rate', 'qualified')), 'text'),
]
assert len(kpis) == 30
dashboard = {"title": "Grants Dashboard", "kpis": kpis,
    "monthly": {"title": "Awarded, received, spent and released", "date": "grants.decision_on", "series": [
        {"label": "Money awarded", "sum": "grants.awarded", "date": "grants.decision_on"}, {"label": "Instalments received", "sum": "grant_payments.amount", "date": "grant_payments.received_on"},
        {"label": "Grant spending", "sum": "grant_spending.amount", "date": "grant_spending.date"}, {"label": "Released from restriction", "sum": "release_journal.amount", "date": "release_journal.date"}]},
    "breakdowns": [{"title": "Weighted pipeline by stage", "by": "grants.stage", "value": "grants.weighted", "agg": "sum"}, {"title": "Money awarded by funder type", "by": "grants.funder_type", "value": "grants.awarded", "agg": "sum"},
                   {"title": "Fund balance by fund, this month", "by": "fund_position.fund", "value": "fund_position.balance", "agg": "sum"}, {"title": "Reports by status", "by": "grant_reports.status", "value": "grant_reports.amount_dummy", "agg": "count"}]}
dashboard["breakdowns"][3] = {"title": "Reports by status", "by": "grant_reports.status", "value": "grant_reports.days_to_due", "agg": "count"}

def W(c, o, v): return (c, o, v)
ACTIVE = [W('start_on', '<=', '{today}'), W('end_on', '>=', '{today}')]
insights = {"filters": [{"label": "Fund", "list": "fund"}, {"label": "Funder type", "list": "ftype"}, {"label": "Staff member", "list": "staff"}],
    "gauges": [
        {"title": "Grant spend against period elapsed", "num": AGG('sum', 'grant_actual', 'grant_actual.spent', where=ACTIVE), "den": AGG('sum', 'grant_actual', 'grant_actual.expected_spend', where=ACTIVE)},
        {"title": "Reports submitted on time", "num": AGG('count', 'grant_reports', where=[W('timing', '=', c1('Submitted on time'))]), "den": AGG('count', 'grant_reports', where=[W('status', '=', SUBM)])},
        {"title": "Instalments received on time", "num": AGG('count', 'grant_payments', where=[W('timing', '=', c1('Received on time'))]), "den": AGG('count', 'grant_payments', where=[W('status', '=', RCV)])},
        {"title": "Own win rate, all decisions", "num": AGG('sum', 'grants', 'grants.won'), "den": AGG('sum', 'grants', 'grants.decided')},
        {"title": "Restricted funds at or above zero", "num": AGG('sum', 'fund_position', 'fund_position.ok_restricted', where=[W('is_now', '=', 1)]), "den": AGG('sum', 'fund_position', 'fund_position.is_restricted', where=[W('is_now', '=', 1)])},
        {"title": "Free money against the reserve setting", "num": AGG('sum', 'free_money', 'free_money.free_money', where=[W('is_now', '=', 1)]), "den": AGG('sum', 'free_money', 'free_money.target_money', where=[W('is_now', '=', 1)])}],
    "charts": [
        CHART('Money awarded per month', 'column', 'month', [AGG('sum', 'grants', 'grants.awarded', date='grants.decision_on', label='Money awarded')]),
        CHART('Pipeline asked by stage', 'bar', 'grants.stage', [AGG('sum', 'grants', 'grants.asked', label='Asked')]),
        CHART('Weighted pipeline by stage', 'bar', 'grants.stage', [AGG('sum', 'grants', 'grants.weighted', label='Weighted amount')]),
        CHART('Awards by funder type', 'bar', 'grants.funder_type', [AGG('sum', 'grants', 'grants.awarded', label='Money awarded')]),
        CHART('Win rate by funder type, all decisions', 'bar', 'win_rate.funder_type', [AGG('avg', 'win_rate', 'win_rate.win_rate', where=[W('period', '=', tok('period', 'All decisions'))], label='Win rate')]),
        CHART('Awarded by program', 'bar', 'grants.program', [AGG('sum', 'grants', 'grants.awarded', label='Money awarded')]),
        CHART('Instalments due per month', 'column', 'month', [AGG('sum', 'grant_payments', 'grant_payments.amount', date='grant_payments.due_date', label='Instalments due')]),
        CHART('Instalments received per month', 'column', 'month', [AGG('sum', 'grant_payments', 'grant_payments.amount', date='grant_payments.received_on', label='Instalments received')]),
        CHART('Reports due per month', 'column', 'month', [AGG('count', 'grant_reports', date='grant_reports.due_date', label='Reports due')]),
        CHART('Reports by status', 'bar', 'grant_reports.status', [AGG('count', 'grant_reports', label='Reports')]),
        CHART('Grant spending per month', 'column', 'month', [AGG('sum', 'grant_spending', 'grant_spending.amount', date='grant_spending.date', label='Grant spending')]),
        CHART('Spent by grant category', 'bar', 'grant_spending.category', [AGG('sum', 'grant_spending', 'grant_spending.amount', label='Spent')]),
        CHART('Share spent by funder type, grants with a budget', 'bar', 'grant_actual.funder_type', [AGG('avg', 'grant_actual', 'grant_actual.share_spent', label='Share spent')]),
        CHART('Balance by fund, this month', 'bar', 'fund_position.fund', [AGG('sum', 'fund_position', 'fund_position.balance', where=[W('is_now', '=', 1)], label='Balance')]),
        CHART('Restricted and designated money per month', 'column', 'month', [AGG('sum', 'fund_months', 'fund_months.restricted_bal', date='fund_months.month', label='Restricted'), AGG('sum', 'fund_months', 'fund_months.designated_bal', date='fund_months.month', label='Designated')]),
        CHART('Released from restriction per month', 'column', 'month', [AGG('sum', 'release_journal', 'release_journal.amount', date='release_journal.date', label='Released')]),
        CHART('Released by program', 'bar', 'release_journal.program', [AGG('sum', 'release_journal', 'release_journal.amount', label='Released')]),
        CHART('Receipts by fund', 'bar', 'fund_months.fund', [AGG('sum', 'fund_months', 'fund_months.receipts', label='Receipts')]),
        CHART('Free money per month', 'column', 'month', [AGG('sum', 'free_money', 'free_money.free_money', date='free_money.month', label='Free money')]),
        CHART('Months of reserve per month', 'column', 'month', [AGG('sum', 'free_money', 'free_money.reserve_months', date='free_money.month', label='Months of reserve')]),
        CHART('Staff time cost by program', 'bar', 'staff_time.program', [AGG('sum', 'staff_time', 'staff_time.cost', label='Staff time cost')]),
        CHART('Staff time cost per month', 'column', 'month', [AGG('sum', 'staff_time', 'staff_time.cost', date='staff_time.month', label='Staff time cost')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Grant income forecast", "why": "instalments due plus the weighted pipeline for four quarters in Base, Best and Worst, with the first quarter that is short of your budget", "where": "Grant Income Forecast"},
    {"name": "Report due ranker", "why": "open funder reports ranked by days to due and by spending behind the period, so you know which to write now", "where": "Report Due Ranker"},
    {"name": "Grant budget against actual", "why": "the share of the period passed set against the share spent, with a forecast to the end date and a status for every grant", "where": "Grant Budget Against Actual"},
    {"name": "Underspend rescue plan", "why": "the monthly spend that uses the award before the end date, or the sign that you should ask for an extension", "where": "Underspend Rescue Plan"},
    {"name": "Fund balance check", "why": "every restricted fund checked from its opening balance, receipts and releases, with any fund below zero named", "where": "Fund Balance Check"},
    {"name": "Free money position", "why": "cash less restricted and designated money, in months of reserve, with the effect of a one-off cost", "where": "Free Money Tool"},
    {"name": "Grant should-we-apply tool", "why": "expected value for each writing hour set against your own history, with a verdict to apply, apply if time or skip", "where": "Grant Should-We-Apply Tool"},
    {"name": "Late grant payment chaser", "why": "instalments past due ranked by money times days late, with the first funder to chase named", "where": "Late Grant Payment Chaser"},
    {"name": "Release from restriction check", "why": "spending coded to restricted funds set against the release journal, with the amount still to release this month", "where": "Release from Restriction"},
    {"name": "Staff time allocator", "why": "every staff month added up across grants, programs, management and fundraising and checked against 100 percent", "where": "Staff Time Allocator"}]
competitors = [
    {"what": "donor-management software", "lacks": "tracks gifts well but has no grant budget against spending, no restricted fund balances and no staff time split across grants"},
    {"what": "single-purpose grant tracker templates", "lacks": "list grants and deadlines but never test spending against the period, release spent money from restriction or show free money"},
    {"what": "generic donation log spreadsheets", "lacks": "record money in with no stages, no instalments, no reports due and no win rate from your own history"},
    {"what": "nonprofit accounting add-ons", "lacks": "keep the ledger but give no pipeline by quarter, no underspend plan and no apply or skip decision for a grant"}]
guide = [
    'Open Start and type your organization name, the grant income in your budget, the chances of an award at each stage and the near-zero limit for restricted funds.',
    'Record every grant on the Grants sheet with its funder, stage, amount asked, dates and the hours to write; the weighted amount fills in.',
    'Enter each instalment on Grant Payments and each report on Grant Reports; days late, days to due and the action fill in.',
    'Enter the budget lines of each awarded grant on Grant Budget Lines and code every expense to a grant on Grant Spending.',
    'Add awarded grants to Grant Budget vs Actual and Grant Spending by Line to see the share of the period against the share spent.',
    'Keep Fund Months up to date each month end; Fund Position, Free Money Position and the restricted balances fill in from it.',
    'Write each release from restriction (spent money moved from a restricted fund to expense) in the Release Journal.',
    'Split each staff member\'s month across grants, programs, management and fundraising on Staff Time and check it on Staff Time Check.',
    'List the next instalments and reports on the Next 90 Days Calendar and open it every week.',
    f'Use the {len(tools)} tools for decisions: the forecast, the report ranker, the chaser, the rescue plan, the fund check and the apply or skip tool.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'Read the Grants Dashboard and the charts every week. A founder with volunteers can use the same sheets with a handful of grants and one restricted fund.']
listing = {"title": "Nonprofit Grants and Restricted Funds Excel Template: Grant Pipeline, Reports Due, Budget vs Actual, Fund Balances",
    "headline": "Track every grant from first idea to final report, and every restricted fund",
    "tags": ["nonprofit", "grant tracker", "grant management", "restricted funds", "grant budget", "excel template", "charity", "grant pipeline", "grant reports", "fund balance", "nonprofit finance", "grant calendar", "free money"],
    "description": ("Run the grant side of a small community nonprofit in one Excel workbook. Built for an executive director, a development manager and a bookkeeper who move grants from first idea to final report and must keep money given for one purpose in the right fund. "
        "Grants holds every grant with stage, amount asked, chance of an award, dates and hours to write, and Grant Payments and Grant Reports show instalments and reports with days late and days to due. Grant Budget vs Actual sets the share of the period against the share spent and forecasts the spend to the end date.\n\n"
        "Fund Months, Fund Position and the Release Journal keep restricted funds, show any fund below zero and record each release from restriction (spent money moved from a restricted fund to expense). Free Money Position shows cash less restricted and designated money in months of reserve. Staff Time and Staff Time Check split each staff month across grants, programs, management and fundraising and test it against 100 percent. "
        f"{len(tools)} tools answer the weekly questions: the grant pipeline and income forecast with Base, Best and Worst, the win rate from your own history, the report due ranker, the late payment chaser, the underspend rescue plan, the overspend limit, the line mover, the fund balance check, spending against a fund and a should-we-apply tool. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to funders, staff and the board.\n\n"
        "This is part three of the Nonprofit Organization suite. It works in Excel and Google Sheets, has no macros and no subscription, and comes with a demo copy full of sample data. Chances, forecasts and verdicts are your own estimate, not a promise of income. It helps you keep records and is not accounting or legal advice; ask your accountant what your own rules need."),
    "features": ["Grant pipeline by stage and quarter", "Win rate from your own history", "Instalments and reports on one calendar", "Grant budget against actual with forecast", "Restricted fund balances and releases",
                 "Free money in months of reserve", "Staff time split across grants", f"{len(tools)} decision tools", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "Works for a founder with one grant"]}
s = spec(id=f'{SUITE}-p3', slug='nonprofit-grants', profession='Nonprofit Organization', name='Grants and Restricted Funds',
         tagline='Track every grant and every restricted fund, from first idea to final report', price_usd=29,
         colors={"primary": "#22577A", "accent": "#F2A541"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 3, "of": 8, "focus": "Grants and restricted funds"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'np3.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
