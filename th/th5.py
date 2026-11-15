"""Therapy Private Practice suite - part 5: Clinician Pay and Productivity."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from th5_lists import *
from th5_tables import settings, tables
from th5_tools import tools

SUITE = 'fx-20261115-therapy-practice'
NOTE = "Sample wording: adapt it to your own practice and check your own local rules."
YES = '{list:yesno.yes}'
def F(*pairs): return [FV(a, b) for a, b in pairs]
def pk(tbl, idc, col): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (tbl, col, tbl, idc)
PT = lambda x: tok('paytype', x)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; NXT = 'DATE(YEAR({today}),MONTH({today})+1,1)'; LM = 'EDATE(%s,-1)' % MS
def D30(c): return '{range:%s},">="&({today}-30),{range:%s},"<="&{today}' % (c, c)
def SM(tbl, col, a, b, extra=''):
    return 'SUMIFS({range:%s.%s},{range:%s.month},">="&%s,{range:%s.month},"<"&%s%s)' % (tbl, col, tbl, a, tbl, b, extra)
def CMM(col, a=LM, b=MS): return SM('clin_months', col, a, b)
def LMX(tbl, col, extra=''): return SM(tbl, col, LM, MS, extra)
def CNT(tbl, a, b, extra=''):
    return 'COUNTIFS({range:%s.month},">="&%s,{range:%s.month},"<"&%s%s)' % (tbl, a, tbl, b, extra)

forms = [
    FORM('month_sheet', 'Clinician Month Sheet', 'Clinician month with own-history comparison', 'clin_months.row_id', F(
        ('Month', 'clin_months.month'), ('Clinician', 'clin_months.clinician'), ('Working weeks', 'clin_months.working_weeks'), ('Session capacity', 'clin_months.capacity'), ('Booked', 'clin_months.booked'),
        ('Attended', 'clin_months.attended'), ('Cancelled', 'clin_months.cancelled'), ('Late cancels', 'clin_months.late_cancels'), ('No-shows', 'clin_months.no_shows'), ('Clinical hours', 'clin_months.clinical_hours'),
        ('Revenue', 'clin_months.revenue'), ('Booked share of cap', 'clin_months.share_of_cap'), ('Utilization band', 'clin_months.band'), ('Attendance rate', 'clin_months.attendance_rate'),
        ('Revenue per clinical hour', 'clin_months.rev_per_hour'), ('3-month average per hour', 'clin_months.rph_avg3'), ('Same month last year per hour', 'clin_months.rph_last_year'),
        ('Change vs 3-month average', 'clin_months.rph_vs_avg3')) + [
        FF('Clinical hours per working week', 'IFERROR(%s/%s,0)' % (pk('clin_months', 'row_id', 'clinical_hours'), pk('clin_months', 'row_id', 'working_weeks')), 'num'),
        FF('Revenue per attended session', 'IFERROR(%s/%s,0)' % (pk('clin_months', 'row_id', 'revenue'), pk('clin_months', 'row_id', 'attended')), 'money')]),
    FORM('target_sheet', 'Monthly Target Sheet', 'Monthly target with pace and gap', 'targets.target_id', F(
        ('Month', 'targets.month'), ('Clinician', 'targets.clinician'), ('Target sessions', 'targets.target_sessions'), ('Target revenue', 'targets.target_revenue'), ('Attended so far', 'targets.attended'),
        ('Revenue so far', 'targets.revenue_actual'), ('Share of the month gone', 'targets.pace'), ('Gap to pace', 'targets.gap'), ('Revenue gap to pace', 'targets.revenue_gap'), ('Target check', 'targets.target_flag'),
        ('Clinician phone', 'targets.phone')) + [
        FF('Sessions still needed', 'MAX(0,%s-%s)' % (pk('targets', 'target_id', 'target_sessions'), pk('targets', 'target_id', 'attended')), 'int')]),
    FORM('review_sheet', 'Productivity Review Sheet', 'Productivity review finding, action and status', 'reviews.review_id', F(
        ('Date', 'reviews.date'), ('Clinician', 'reviews.clinician'), ('Finding', 'reviews.finding'), ('Action', 'reviews.action'), ('Due date', 'reviews.due_date'), ('Done on', 'reviews.done_on'),
        ('Review status', 'reviews.review_status'), ('Days open', 'reviews.days_open'), ('Clinician phone', 'reviews.phone')) + [
        FF('Reviews of this clinician not done', 'COUNTIFS({range:reviews.clinician},%s)-COUNTIFS({range:reviews.clinician},%s,{range:reviews.review_status},%s)' % (
            pk('reviews', 'review_id', 'clinician'), pk('reviews', 'review_id', 'clinician'), V('Done')), 'int')]),
    FORM('retention_sheet', 'Retention Review Sheet', 'Client retention to six sessions', 'retention.client_id', F(
        ('Client', 'retention.client'), ('Clinician', 'retention.clinician'), ('Service', 'retention.service'), ('First session', 'retention.first_session'), ('Sessions attended', 'retention.sessions_attended'),
        ('Last session', 'retention.last_session'), ('Client status', 'retention.status'), ('Retention check', 'retention.retained'), ('Weeks in care', 'retention.weeks_in_care'), ('Clinician phone', 'retention.phone')) + [
        FF('Retained to 6, this clinician', 'IFERROR(COUNTIFS({range:retention.clinician},%s,{range:retention.retained},%s)/COUNTIFS({range:retention.clinician},%s),0)' % (
            pk('retention', 'client_id', 'clinician'), V('Retained to 6'), pk('retention', 'client_id', 'clinician')), 'pct')]),
    FORM('admin_sheet', 'Admin Time Sheet', 'Admin time with the clinician total', 'admin_log.admin_id', F(
        ('Date', 'admin_log.date'), ('Clinician', 'admin_log.clinician'), ('Task', 'admin_log.task'), ('Minutes', 'admin_log.minutes'), ('Hours', 'admin_log.hours')) + [
        FF('Admin hours of this clinician, 30 days', 'SUMIFS({range:admin_log.hours},{range:admin_log.clinician},%s,{range:admin_log.date},">="&({today}-30),{range:admin_log.date},"<="&{today})' % pk('admin_log', 'admin_id', 'clinician'), 'num'),
        FF('Admin hours, all clinicians, 30 days', 'SUMIFS({range:admin_log.hours},%s)' % D30('admin_log.date'), 'num')]),
    FORM('pay_sheet', 'Pay Summary Sheet', 'Pay row with employer cost and pay share', 'pay.pay_id', F(
        ('Month', 'pay.month'), ('Person', 'pay.person'), ('Pay type', 'pay.pay_type'), ('Sessions', 'pay.sessions'), ('Hours', 'pay.hours'), ('Fees charged', 'pay.fees_charged'), ('Split', 'pay.split_pct'),
        ('Amount', 'pay.amount'), ('Employer cost', 'pay.employer_cost'), ('Paid on', 'pay.paid_on'), ('Pay status', 'pay.status'), ('Pay per session', 'pay.pay_per_session'), ('All-in pay', 'pay.all_in_pay'),
        ('Pay share of fees', 'pay.pay_share'), ('Person phone', 'pay.phone')) + [
        FF('Pay of this person, 12 months', 'SUMIFS({range:pay.amount},{range:pay.person},%s,{range:pay.month},">"&EDATE(%s,-12),{range:pay.month},"<="&%s)' % (
            pk('pay', 'pay_id', 'person'), pk('pay', 'pay_id', 'month'), pk('pay', 'pay_id', 'month')), 'money')]),
    FORM('statement_sheet', 'Contractor Statement Sheet', 'Contractor statement with card fees and split', 'contractor_statements.pay_id', F(
        ('Month', 'contractor_statements.month'), ('Contractor', 'contractor_statements.contractor'), ('Sessions', 'contractor_statements.sessions'), ('Fees charged', 'contractor_statements.fees_charged'),
        ('Split', 'contractor_statements.split_pct'), ('Amount', 'contractor_statements.amount'), ('Card fees', 'contractor_statements.card_fees'), ('Check total', 'contractor_statements.check_total'),
        ('Difference', 'contractor_statements.difference'), ('Pay after card fees', 'contractor_statements.pay_after_fees'), ('Effective split', 'contractor_statements.effective_split'),
        ('Contractor phone', 'contractor_statements.phone')) + [
        FF('Statements of this contractor, 12 months', 'COUNTIFS({range:contractor_statements.contractor},%s,{range:contractor_statements.month},">"&EDATE(%s,-12))' % (
            pk('contractor_statements', 'pay_id', 'contractor'), pk('contractor_statements', 'pay_id', 'month')), 'int')]),
    FORM('invoice_sheet', 'Contractor Invoice Check Sheet', 'Contractor invoice against the statement', 'contractor_invoices.invoice_id', F(
        ('Month', 'contractor_invoices.month'), ('Contractor', 'contractor_invoices.contractor'), ('Received on', 'contractor_invoices.received_on'), ('Invoice amount', 'contractor_invoices.amount'),
        ('Paid on', 'contractor_invoices.paid_on'), ('Statement amount', 'contractor_invoices.statement_amount'), ('Difference', 'contractor_invoices.difference'), ('Invoice check', 'contractor_invoices.match_flag'),
        ('Contractor phone', 'contractor_invoices.phone')) + [
        FF('Invoices of this contractor not matching', 'COUNTIFS({range:contractor_invoices.contractor},%s,{range:contractor_invoices.match_flag},%s)' % (
            pk('contractor_invoices', 'invoice_id', 'contractor'), V('Does not match')), 'int')]),
    FORM('associate_sheet', 'Associate Pay Sheet', 'Associate pay with supervision cost loaded', 'allin.allin_id', F(
        ('Month', 'allin.month'), ('Clinician', 'allin.clinician'), ('Pay type', 'allin.pay_type'), ('Sessions', 'allin.sessions'), ('Revenue', 'allin.revenue'), ('Pay', 'allin.clinician_pay'),
        ('Supervision cost', 'allin.supervision_cost'), ('Room cost', 'allin.room_cost'), ('Admin cost', 'allin.admin_cost'), ('All-in cost', 'allin.all_in_cost'), ('Margin', 'allin.margin'),
        ('Margin per session', 'allin.margin_per_session'), ('Margin share of revenue', 'allin.margin_share'), ('Margin check', 'allin.margin_flag')) + [
        FF('Supervision hours loaded', 'IFERROR(%s/{set:supervision_rate},0)' % pk('allin', 'allin_id', 'supervision_cost'), 'num'),
        FF('Supervision share of revenue', 'IFERROR(%s/%s,0)' % (pk('allin', 'allin_id', 'supervision_cost'), pk('allin', 'allin_id', 'revenue')), 'pct')]),
    FORM('change_sheet', 'Pay Change Sheet', 'Pay change with old and new rate', 'pay_changes.change_id', F(
        ('Date', 'pay_changes.date'), ('Person', 'pay_changes.person'), ('Change', 'pay_changes.change'), ('Unit', 'pay_changes.unit'), ('Old rate', 'pay_changes.old_rate'), ('New rate', 'pay_changes.new_rate'),
        ('Reason', 'pay_changes.reason'), ('Change share', 'pay_changes.change_share'), ('Change status', 'pay_changes.change_status'), ('Person phone', 'pay_changes.phone')) + [
        FF('Pay changes of this person', 'COUNTIFS({range:pay_changes.person},%s)' % pk('pay_changes', 'change_id', 'person'), 'int')]),
    FORM('timesheet_sheet', 'Timesheet Sheet', 'Coordinator week with overtime and pay', 'timesheet.ts_id', F(
        ('Week', 'timesheet.week'), ('Hours', 'timesheet.hours'), ('Overtime hours', 'timesheet.overtime_hours'), ('Tasks', 'timesheet.tasks'), ('Hourly rate', 'timesheet.hourly_rate'), ('Pay', 'timesheet.pay'),
        ('Overtime check', 'timesheet.overtime_check')) + [
        FF('Hours in the 4 weeks to this week', 'SUMIFS({range:timesheet.hours},{range:timesheet.week},">"&(%s-28),{range:timesheet.week},"<="&%s)' % (pk('timesheet', 'ts_id', 'week'), pk('timesheet', 'ts_id', 'week')), 'num')]),
    FORM('leave_sheet', 'Leave Request Sheet', 'Leave request with days left and clash check', 'leave.leave_id', F(
        ('Year', 'leave.year'), ('Person', 'leave.person'), ('Leave days allowed', 'leave.leave_days_allowed'), ('Days taken', 'leave.days_taken'), ('Leave from', 'leave.leave_from'), ('Days requested', 'leave.leave_days_next'),
        ('Days left', 'leave.days_left'), ('Days left after the request', 'leave.days_left_after'), ('Sessions to move', 'leave.sessions_to_move'), ('Clash check', 'leave.clash_check'), ('Person phone', 'leave.phone')) + [
        FF('Leave rows of this person', 'COUNTIFS({range:leave.person},%s)' % pk('leave', 'leave_id', 'person'), 'int')]),
]
assert len(forms) == 12

documents = [
    DOC('month_doc', 'Monthly Clinician Report', 'Monthly clinician report with own-history row', 'clin_months.row_id', [
        'Monthly clinician report of {set:company}, dated {today}. Clinician: {col:clin_months.clinician}. Month: {col:clin_months.month}.',
        'Working weeks {col:clin_months.working_weeks}, session capacity {col:clin_months.capacity}, booked {col:clin_months.booked}, attended {col:clin_months.attended}, cancelled {col:clin_months.cancelled}, late cancels {col:clin_months.late_cancels}, no-shows {col:clin_months.no_shows}. Clinical hours: {col:clin_months.clinical_hours}. Revenue: {col:clin_months.revenue}.',
        'Booked share of cap: {col:clin_months.share_of_cap} ({col:clin_months.band}). Attendance rate: {col:clin_months.attendance_rate}. Revenue per clinical hour: {col:clin_months.rev_per_hour}.',
        'Compare with your own history. Revenue per clinical hour: this month {col:clin_months.rev_per_hour}, 3-month average {col:clin_months.rph_avg3}, same month last year {col:clin_months.rph_last_year}. Booked share of cap: this month {col:clin_months.share_of_cap}, 3-month average {col:clin_months.share_avg3}, same month last year {col:clin_months.share_last_year}.'], ['Owner', 'Clinician'], NOTE),
    DOC('statement_doc', 'Contractor Statement', 'Contractor statement for a month', 'contractor_statements.pay_id', [
        'Contractor statement of {set:company}, dated {today}. Contractor: {col:contractor_statements.contractor}. Month: {col:contractor_statements.month}.',
        'Sessions: {col:contractor_statements.sessions}. Fees charged to clients: {col:contractor_statements.fees_charged}. Split: {col:contractor_statements.split_pct}. Amount due to you: {col:contractor_statements.amount}. Check total: {col:contractor_statements.check_total}.',
        'Card fees on your clients payments: {col:contractor_statements.card_fees}. Pay after card fees: {col:contractor_statements.pay_after_fees}, an effective split of {col:contractor_statements.effective_split}.', 'Please send an invoice for the amount due. Tell us within 5 working days if a figure looks wrong.'], ['Practice', 'Contractor'], NOTE),
    DOC('pay_doc', 'Pay Summary', 'Pay summary for an employee', 'pay.pay_id', [
        'Pay summary of {set:company}, dated {today}. Name: {col:pay.person}. Month: {col:pay.month}. Pay type: {col:pay.pay_type}.',
        'Sessions: {col:pay.sessions}. Hours: {col:pay.hours}. Fees charged: {col:pay.fees_charged}. Split: {col:pay.split_pct}. Pay: {col:pay.amount}. Employer cost: {col:pay.employer_cost}. All-in pay: {col:pay.all_in_pay}.',
        'Paid on: {col:pay.paid_on}. Status: {col:pay.status}. Pay per session: {col:pay.pay_per_session}.', 'Taxes and deductions follow your own local rules: confirm with your adviser.'], ['Practice', 'Employee'], NOTE),
    DOC('associate_doc', 'Associate Pay Statement', 'Associate pay statement with supervision cost', 'allin.allin_id', [
        'Associate pay statement of {set:company}, dated {today}. Associate: {col:allin.clinician}. Month: {col:allin.month}.',
        'Sessions attended: {col:allin.sessions}. Pay: {col:allin.clinician_pay}. Revenue from the sessions: {col:allin.revenue}.',
        'Supervision cost carried on the practice for this month: {col:allin.supervision_cost}. Room cost: {col:allin.room_cost}. Admin cost: {col:allin.admin_cost}. All-in cost: {col:allin.all_in_cost}. Margin per session after supervision: {col:allin.margin_per_session}.',
        'Pay is released after the supervision log for the month is complete.'], ['Practice', 'Associate'], NOTE),
    DOC('change_doc', 'Pay Change Letter', 'Pay change letter', 'pay_changes.change_id', [
        'Pay change letter of {set:company}, dated {today}. Name: {col:pay_changes.person}.',
        'Your {col:pay_changes.change} changes from {col:pay_changes.old_rate} to {col:pay_changes.new_rate} ({col:pay_changes.unit}) from {col:pay_changes.date}. Reason: {col:pay_changes.reason}. Change: {col:pay_changes.change_share}. Status: {col:pay_changes.change_status}.',
        'All other terms stay as agreed. Please sign and return a copy.'], ['Practice', 'Employee'], NOTE),
    DOC('leave_doc', 'Leave Approval Note', 'Leave approval note', 'leave.leave_id', [
        'Leave approval note of {set:company}, dated {today}. Name: {col:leave.person}. Year: {col:leave.year}.',
        'Leave from {col:leave.leave_from}, {col:leave.leave_days_next} days. Days allowed {col:leave.leave_days_allowed}, days taken {col:leave.days_taken}, days left after this leave {col:leave.days_left_after}.',
        'Sessions to move before the leave: {col:leave.sessions_to_move}. Clash check: {col:leave.clash_check}.', 'The coordinator moves the sessions and tells the clients before the leave starts.'], ['Practice', 'Employee'], NOTE),
    DOC('target_doc', 'Monthly Target Agreement', 'Monthly target agreement', 'targets.target_id', [
        'Monthly target agreement of {set:company}, dated {today}. Clinician: {col:targets.clinician}. Month: {col:targets.month}.',
        'Target sessions: {col:targets.target_sessions}. Target revenue: {col:targets.target_revenue}. Attended so far: {col:targets.attended}. Gap to pace: {col:targets.gap}. Target check: {col:targets.target_flag}.',
        'The target is set from your session cap, working weeks and attendance rate. We review it together at the monthly productivity review.'], ['Owner', 'Clinician'], NOTE),
    DOC('review_doc', 'Productivity Review Notes', 'Productivity review notes', 'reviews.review_id', [
        'Productivity review notes of {set:company}, dated {today}. Clinician: {col:reviews.clinician}. Review date: {col:reviews.date}.',
        'Finding: {col:reviews.finding}. Action agreed: {col:reviews.action}. Due: {col:reviews.due_date}. Done on: {col:reviews.done_on}. Status: {col:reviews.review_status}.',
        'These notes cover numbers and actions only. They hold no client details.'], ['Owner', 'Clinician'], NOTE),
    DOC('terms_doc', 'Contractor Fee Terms Summary', 'Contractor fee terms summary (adapt to your terms)', 'contractor_statements.pay_id', [
        'Contractor fee terms summary of {set:company}, dated {today}. Contractor: {col:contractor_statements.contractor}.',
        'The contractor receives {col:contractor_statements.split_pct} of the fees charged for their own client sessions. Card fees on the payments are shared as set in the written contract. Last statement: {col:contractor_statements.month}, fees charged {col:contractor_statements.fees_charged}, card fees {col:contractor_statements.card_fees}, effective split {col:contractor_statements.effective_split}.',
        'The contractor sends an invoice for the statement amount. This summary does not replace your written contract.', 'Check your own local rules and your contract terms.'], ['Practice', 'Contractor'], NOTE),
    DOC('year_doc', 'Yearly Clinician Summary', 'Yearly clinician summary', 'clin_months.row_id', [
        'Yearly clinician summary of {set:company}, dated {today}. Clinician: {col:clin_months.clinician}. The 12 months to {col:clin_months.month}.',
        'Sessions attended: {col:clin_months.attended_12m}. Clinical hours: {col:clin_months.hours_12m}. Revenue: {col:clin_months.revenue_12m}.',
        'Revenue per clinical hour this month: {col:clin_months.rev_per_hour}, 3-month average {col:clin_months.rph_avg3}, same month last year {col:clin_months.rph_last_year}. Booked share of cap this month: {col:clin_months.share_of_cap}.',
        'Use this summary for the yearly review of pay and workload.'], ['Owner', 'Clinician'], NOTE),
    DOC('payroll_doc', 'Payroll Summary', 'Payroll summary for the accountant', 'payroll.payroll_id', [
        'Payroll summary of {set:company}, dated {today}. For: {col:payroll.accountant}. Month: {col:payroll.month}.',
        'Salaries: {col:payroll.salaries}. Hourly pay: {col:payroll.hourly_pay}. Contractor pay: {col:payroll.contractor_pay}. Associate pay: {col:payroll.associate_pay}. Employer costs: {col:payroll.employer_costs}. Total: {col:payroll.total_pay}.',
        'Revenue for the month: {col:payroll.revenue}. Pay share of revenue: {col:payroll.pay_share}, target {set:pay_share_target}. Check: {col:payroll.pay_flag}.', 'Tax and filing follow your own local rules: confirm with your adviser.'], ['Owner', 'Accountant'], NOTE),
    DOC('split_doc', 'Contractor Split Proposal Note', 'Contractor split proposal note (adapt to your own terms)', 'contractor_statements.pay_id', [
        'Contractor split proposal note of {set:company}, dated {today}. Contractor: {col:contractor_statements.contractor}.',
        'Current split: {col:contractor_statements.split_pct}. Effective split after card fees in {col:contractor_statements.month}: {col:contractor_statements.effective_split}. Fees charged that month: {col:contractor_statements.fees_charged}.',
        'The practice looks at the all-in cost of the contractor (room time, admin and card fees) against a margin target of {set:profit_target} before it agrees a new split. A counter-offer can follow if the margin falls below the target.', 'This note is a proposal only. It does not replace your written contract.'], ['Owner', 'Contractor'], NOTE),
]
assert len(documents) == 12

checklists = [
    CHK('pay_run', 'Monthly Pay Run Steps', 'payroll', 'payroll.month', [('Close the month and check sessions of every clinician', 31), ('Check clinical hours and hourly pay', 32), ('Check contractor statements against fees charged', 33), ('Check associate pay against the supervision log', 34), ('Add employer costs', 35), ('Compare pay share of revenue with the target', 36), ('Send the payroll summary to the accountant', 37), ('Release the pay', 40)]),
    CHK('statement_run', 'Contractor Statement Steps', 'contractor_statements', 'contractor_statements.month', [('Total the fees charged for the contractor', 31), ('Apply the agreed split', 31), ('Take off the card fees', 32), ('Check the effective split', 32), ('Send the statement to the contractor', 33), ('Ask the contractor for the invoice', 33)]),
    CHK('invoice_run', 'Contractor Invoice Steps', 'contractor_invoices', 'contractor_invoices.received_on', [('Check the invoice matches the statement amount', 1), ('Query any difference with the contractor', 2), ('Record the corrected invoice', 4), ('Approve the invoice', 5), ('Pay the invoice', 10), ('Record the paid date', 10)]),
    CHK('associate_run', 'Associate Pay Check Steps', 'allin', 'allin.month', [('Count the associate sessions attended', 31), ('Check the supervision log for the month', 32), ('Check supervision hours against the ratio', 32), ('Work out the pay at the session rate', 33), ('Load the supervision cost on the associate', 33), ('Release the pay once the log is complete', 35)]),
    CHK('setup_run', 'New Clinician Pay Set-up Steps', 'team', 'team.start', [('Agree the pay type and rate', -21), ('Send the written terms', -14), ('Collect the payment details', -10), ('Add the person to the pay sheets', -7), ('Add the leave allowance', -7), ('Set the first pay date', -3), ('Send the pay set-up message', -2)]),
    CHK('change_run', 'Pay Change Steps', 'pay_changes', 'pay_changes.date', [('Record the reason for the change', -30), ('Check the effect on the margin', -28), ('Agree the change with the person', -21), ('Send the pay change letter', -14), ('Tell the accountant', -10), ('Update the pay sheet before the next pay run', -3)]),
    CHK('leave_run', 'Leave Request Steps', 'leave', 'leave.leave_from', [('Check the days left', -28), ('Check clashes with other clinicians', -28), ('Count the sessions to move', -21), ('Approve the leave', -21), ('Tell the clients and move the sessions', -14), ('Send the leave approval note', -14)]),
    CHK('review_run', 'Productivity Review Steps', 'clin_months', 'clin_months.month', [('Open the clinician month figures', 32), ('Check the booked share of cap band', 32), ('Check revenue per clinical hour against the target', 33), ('Compare with the 3-month average and last year', 33), ('Agree one action', 35), ('Record the review and the due date', 35)]),
    CHK('target_run', 'Target Setting Steps', 'targets', 'targets.month', [('Check the session cap and working weeks', -30), ('Check the attendance rate', -28), ('Set the session target', -25), ('Set the revenue target', -25), ('Agree the target with the clinician', -21), ('Send the target agreement', -20)]),
    CHK('retention_run', 'Retention Review Steps', 'dropouts', 'dropouts.date', [('List clients who stopped after the intake', 7), ('List clients who stopped before six sessions', 7), ('Check the reason for each', 10), ('Compare with the clinician own history', 14), ('Agree actions with the clinician', 21)]),
    CHK('split_run', 'Contractor Split Review Steps', 'pay', 'pay.month', [('Total fees charged for the contractor', 31), ('Add room cost, admin and card fees', 32), ('Work out the all-in cost share of fees', 33), ('Compare the margin with the target', 33), ('Test the proposed split in the tool', 35), ('Accept or make a counter-offer', 38)]),
    CHK('leaving_run', 'Clinician Leaving Steps', 'retention', 'retention.last_session', [('List the clients of the clinician', 1), ('Agree the handover for each client', 3), ('Tell the clients about the change', 7), ('Move the booked sessions', 10), ('Work out the final pay and leave days', 14), ('Send the final pay summary', 18), ('Remove the person from the pay sheets', 30)]),
]
assert len(checklists) == 12
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('k_month', 'Clinician: your month in numbers', 'clin_months', 'clin_months.phone', 'Hello {clinician}, your month in numbers for {month}: {attended} sessions attended and {clinical_hours} clinical hours, with {revenue} in fees. {owner}.'),
    M('k_util', 'Clinician: your utilization last month', 'clin_months', 'clin_months.phone', 'Hello {clinician}, your booked share of cap in {month} was {share_of_cap}, which is {band}. {owner}.'),
    M('k_target', 'Clinician: your target for the month', 'targets', 'targets.phone', 'Hello {clinician}, your target for {month} is {target_sessions} sessions and {target_revenue} in fees. {owner}.'),
    M('k_ahead', 'Clinician: you are ahead of your target', 'targets', 'targets.phone', 'Hello {clinician}, you have {attended} of {target_sessions} sessions for {month}, a gap to pace of {gap}. Target check: {target_flag}. {owner}.'),
    M('c_split', 'Contractor: a proposal for a new split', 'contractor_statements', 'contractor_statements.phone', 'Hello {contractor}, we would like to talk about a new split. Your current split is {split_pct} and your effective split after card fees in {month} was {effective_split}. {owner}.'),
    M('k_retain', 'Clinician: your retention to 6 sessions', 'team', 'team.phone', 'Hello {name}, your retention to 6 sessions is {retention_rate}. We look at it together at the next review. {owner}.'),
    M('k_stopped', 'Clinician: clients who stopped early', 'dropouts', 'dropouts.phone', 'Hello {clinician}, {client} stopped after {sessions} sessions on {date} (reason: {reason}). Please look at it before the next review. Check: {dropout_check}.'),
    M('k_pay', 'Clinician: your pay summary', 'pay', 'pay.phone', 'Hello {person}, your pay summary for {month}: {sessions} sessions, pay {amount}, status {status}. {owner}.'),
    M('k_change', 'Clinician: your pay change starts', 'pay_changes', 'pay_changes.phone', 'Hello {person}, your {change} changes from {old_rate} to {new_rate} on {date}. {owner}.'),
    M('k_leave_ok', 'Clinician: your leave is approved', 'leave', 'leave.phone', 'Hello {person}, your leave from {leave_from} ({leave_days_next} days) is approved. You will have {days_left_after} leave days left. {owner}.'),
    M('k_leave_left', 'Clinician: you have leave days left', 'leave', 'leave.phone', 'Hello {person}, you have {days_left} leave days left for {year}. {owner}.'),
    M('k_review', 'Clinician: your productivity review', 'reviews', 'reviews.phone', 'Hello {clinician}, your productivity review is due on {due_date}. Topic: {finding}. Action: {action}. {owner}.'),
    M('k_history', 'Clinician: your month and your history', 'clin_months', 'clin_months.phone', 'Hello {clinician}, revenue per clinical hour in {month} was {rev_per_hour}, against {rph_avg3} for the last 3 months and {rph_last_year} a year ago. {owner}.'),
    M('c_stmt', 'Contractor: your statement is ready', 'contractor_statements', 'contractor_statements.phone', 'Hello {contractor}, your statement for {month} is {amount} on fees charged of {fees_charged}. {accountant}.'),
    M('c_inv_ask', 'Contractor: please send your invoice', 'contractor_statements', 'contractor_statements.phone', 'Hello {contractor}, please send your invoice for {month}. The amount due is {amount}. {accountant}.'),
    M('c_inv_diff', 'Contractor: your invoice does not match', 'contractor_invoices', 'contractor_invoices.phone', 'Hello {contractor}, your invoice for {month} is {amount} but the statement is {statement_amount}, a difference of {difference}. Please check and send a corrected invoice. {accountant}.'),
    M('c_paid', 'Contractor: your payment was sent', 'contractor_invoices', 'contractor_invoices.phone', 'Hello {contractor}, your payment of {amount} for {month} was sent on {paid_on}. {accountant}.'),
    M('a_pay', 'Associate: your pay for the month', 'pay', 'pay.phone', 'Hello {person}, your pay for {month} is {amount} for {sessions} sessions. {owner}.'),
    M('a_log', 'Associate: complete the supervision log', 'allin', 'allin.phone', 'Hello {clinician}, please complete the supervision log for {month} before the pay run. Supervision cost carried so far: {supervision_cost}. {owner}.'),
    M('o_sheet', 'Coordinator: approve your timesheet', 'timesheet', 'timesheet.coord_phone', 'Hello {coord}, please approve your timesheet for the week of {week}: {hours} hours, {overtime_hours} overtime hours. {owner}.'),
    M('w_actfirst', 'Owner: act-first, a clinician to review', 'team', 'team.owner_phone', 'Hello {owner}, act-first list: {name} needs a review. Act-first score {act_score}, rank {act_rank}, booked share of cap {util_last}.'),
    M('o_payrun', 'Coordinator: the pay run is on its date', 'pay', 'pay.coord_phone', 'Hello {coord}, the pay run for {month} is on {paid_on}. {person}: {amount}, status {status}.'),
    M('w_util', 'Owner: utilization is outside the band', 'clin_months', 'clin_months.owner_phone', 'Hello {owner}, the booked share of cap of {clinician} in {month} is {share_of_cap}, band: {band}. Please look at the diary and the targets.'),
    M('w_payshare', 'Owner: pay cost share of revenue', 'payroll', 'payroll.owner_phone', 'Hello {owner}, pay cost for {month} is {pay_share} of revenue ({total_pay} on revenue of {revenue}). Check: {pay_flag}.'),
    M('w_report', 'Owner: the productivity report is ready', 'targets', 'targets.owner_phone', 'Hello {owner}, the monthly productivity report is ready. {clinician} has {attended} of {target_sessions} sessions for {month}. Target check: {target_flag}.'),
    M('w_allin', 'Owner: the all-in cost share of fees', 'allin', 'allin.owner_phone', 'Hello {owner}, the all-in cost of {clinician} for {month} is {all_in_share} of fees, a margin of {margin_share}. Check: {margin_flag}.'),
    M('w_retain', 'Owner: retention fell for a clinician', 'team', 'team.owner_phone', 'Hello {owner}, retention to 6 sessions for {name} is {retention_rate}. Please look at the clients who stopped early.'),
    M('w_away', 'Owner: two clinicians are away together', 'leave', 'leave.owner_phone', 'Hello {owner}, {person} is away from {leave_from} for {leave_days_next} days. Clash check: {clash_check}. {sessions_to_move} sessions to move.'),
    M('x_payroll', 'Accountant: payroll for the month', 'payroll', 'payroll.accountant_phone', 'Hello {accountant}, payroll for {month}: salaries {salaries}, hourly pay {hourly_pay}, contractor pay {contractor_pay}, associate pay {associate_pay}, employer costs {employer_costs}, total {total_pay}.'),
    M('x_contract', 'Accountant: contractor payments', 'contractor_statements', 'contractor_statements.accountant_phone', 'Hello {accountant}, contractor payment for {month}: {contractor} {amount} on fees charged of {fees_charged}.'),
    M('x_changes', 'Accountant: pay changes this month', 'pay_changes', 'pay_changes.accountant_phone', 'Hello {accountant}, a pay change from {date}: {person}, {change}, from {old_rate} to {new_rate}. Reason: {reason}.'),
    M('x_employer', 'Accountant: employer costs', 'pay', 'pay.accountant_phone', 'Hello {accountant}, employer costs for {person} in {month}: {employer_cost} on pay of {amount}.'),
    M('n_welcome', 'New clinician: welcome, your pay set-up', 'team', 'team.phone', 'Welcome {name}. Your pay set-up: {pay_type}, from {start}. Please check the details and tell us if anything is wrong. {owner}.'),
    M('n_first', 'New clinician: your first pay date', 'pay', 'pay.phone', 'Hello {person}, your first pay date is {paid_on} for {month}: {amount}. {coord}.'),
]
assert len(messages) == 34, len(messages)

CM = lambda col, a=LM, b=MS: CMM(col, a, b)
kpis = [
    KPI('Clinical hours this month', CMM('clinical_hours', MS, NXT), 'num'),
    KPI('Clinicians in strain band, last month', 'COUNTIFS({range:clin_months.month},%s,{range:clin_months.band},%s)' % (LM, V('Strain')), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Utilization Rate, last month', 'IFERROR(%s/%s,0)' % (CM('booked'), CM('capacity')), 'pct', alert={"when": "> {set:util_strain_above}", "style": "warn"}),
    KPI('Utilization Rate, last 3 full months', 'IFERROR(%s/%s,0)' % (CMM('booked', 'EDATE(%s,-3)' % MS, MS), CMM('capacity', 'EDATE(%s,-3)' % MS, MS)), 'pct'),
    KPI('Hours per working week, last month', 'IFERROR(%s/%s,0)' % (CM('clinical_hours'), CM('working_weeks')), 'num'),
    KPI('Revenue per clinical hour, last month', 'IFERROR(%s/%s,0)' % (CM('revenue'), CM('clinical_hours')), 'money', alert={"when": "< {set:rev_hour_target}", "style": "warn"}),
    KPI('Revenue per clinical hour, 12 months', 'IFERROR(%s/%s,0)' % (CMM('revenue', 'EDATE(%s,-12)' % MS, MS), CMM('clinical_hours', 'EDATE(%s,-12)' % MS, MS)), 'money'),
    KPI('Revenue per attended session, last month', 'IFERROR(%s/%s,0)' % (CM('revenue'), CM('attended')), 'money'),
    KPI('Sessions per discharged client, 12 mo', 'IFERROR(AVERAGEIFS({range:dropouts.sessions},{range:dropouts.date},">="&({today}-365),{range:dropouts.date},"<="&{today}),0)', 'num'),
    KPI('Retention to 6 sessions', 'IFERROR(COUNTIFS({range:retention.retained},%s)/(COUNTIFS({range:retention.retained},%s)+COUNTIFS({range:retention.retained},%s)),0)' % (V('Retained to 6'), V('Retained to 6'), V('Stopped early')), 'pct', alert={"when": "< {set:retention_target}", "style": "warn"}),
    KPI('Drop-outs after the intake, this year', 'COUNTIFS({range:dropouts.dropout_check},%s,{range:dropouts.date},">="&DATE(YEAR({today}),1,1),{range:dropouts.date},"<="&{today})' % V('After intake only'), 'int'),
    KPI('Rebooking rate, last 30 days', 'IFERROR(SUMIFS({range:rebook.rebooked},%s)/COUNTIFS(%s),0)' % (D30('rebook.date'), D30('rebook.date')), 'pct', alert={"when": "< {set:rebook_target}", "style": "warn"}),
    KPI('Contractor effective split, last month', 'IFERROR(%s/%s,0)' % (LMX('contractor_statements', 'pay_after_fees'), LMX('contractor_statements', 'fees_charged')), 'pct'),
    KPI('Clinicians below target, last month', 'COUNTIFS({range:targets.month},%s,{range:targets.target_flag},%s)' % (LM, V('Below target')), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Clinicians idle, last month', 'COUNTIFS({range:clin_months.month},%s,{range:clin_months.band},%s)' % (LM, V('Idle')), 'int'),
    KPI('Pay this month so far', LMX('pay', 'amount').replace(LM, MS).replace('"<"&' + MS, '"<"&' + NXT), 'money'),
    KPI('Pay last month', LMX('pay', 'amount'), 'money'),
    KPI('Pay share of revenue, last month', 'IFERROR(%s/%s,0)' % (LMX('payroll', 'total_pay'), LMX('payroll', 'revenue')), 'pct', alert={"when": "> {set:pay_share_target}", "style": "warn"}),
    KPI('Contractor pay, last month', LMX('payroll', 'contractor_pay'), 'money'),
    KPI('Associate pay, last month', LMX('payroll', 'associate_pay'), 'money'),
    KPI('Salaries and employer costs, last month', '%s+%s' % (LMX('payroll', 'salaries'), LMX('payroll', 'employer_costs')), 'money'),
    KPI('Coordinator hours this month', 'SUMIFS({range:timesheet.hours},{range:timesheet.week},">="&%s,{range:timesheet.week},"<"&%s)' % (MS, NXT), 'num'),
    KPI('Associate margin per session, last month', 'IFERROR(%s/%s,0)' % (LMX('allin', 'margin', ',{range:allin.pay_type},' + PT('Per session')), LMX('allin', 'sessions', ',{range:allin.pay_type},' + PT('Per session'))), 'money'),
    KPI('Contractor all-in cost share of fees', 'IFERROR(%s/%s,0)' % (LMX('allin', 'all_in_cost', ',{range:allin.pay_type},' + PT('Percentage split')), LMX('allin', 'revenue', ',{range:allin.pay_type},' + PT('Percentage split'))), 'pct'),
    KPI('Contractor invoices not matched', 'COUNTIFS({range:contractor_invoices.match_flag},%s)' % V('Does not match'), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Leave days left this year', 'SUMIFS({range:leave.days_left},{range:leave.year},YEAR({today}))', 'int'),
    KPI('Admin hours, last 30 days', 'SUMIFS({range:admin_log.hours},%s)' % D30('admin_log.date'), 'num'),
    KPI('Admin share of clinician time', 'IFERROR(SUMIFS({range:admin_log.hours},%s)/(SUMIFS({range:admin_log.hours},%s)+SUMIFS({range:sessions.clinical_hours},{range:sessions.status},%s,%s)),0)' % (
        D30('admin_log.date'), D30('admin_log.date'), tok('sstatus', 'Attended'), D30('sessions.date')), 'pct', alert={"when": "> {set:admin_share_target}", "style": "warn"}),
    KPI('All-in cost per attended session', 'IFERROR(%s/%s,0)' % (LMX('allin', 'all_in_cost'), LMX('allin', 'sessions')), 'money'),
    KPI('Practice margin per attended session', 'IFERROR(%s/%s,0)' % (LMX('allin', 'margin'), LMX('allin', 'sessions')), 'money'),
]
assert len(kpis) == 30, len(kpis)
for k in kpis: assert len(k['label']) <= 40, k['label']
dashboard = {"title": "KPI Dashboard", "kpis": kpis,
    "monthly": {"title": "Capacity, booked and attended sessions per month", "date": "clin_months.month", "series": [
        {"label": "Capacity", "sum": "clin_months.capacity", "date": "clin_months.month"}, {"label": "Booked", "sum": "clin_months.booked", "date": "clin_months.month"},
        {"label": "Attended", "sum": "clin_months.attended", "date": "clin_months.month"}]},
    "breakdowns": [{"title": "Sessions by service", "by": "sessions.service", "agg": "count"}, {"title": "Sessions by clinician", "by": "sessions.clinician", "agg": "count"},
                   {"title": "Pay by pay type", "by": "pay.pay_type", "agg": "sum", "value": "pay.amount"}, {"title": "Clients by service", "by": "retention.service", "agg": "count"}]}
def SUMC(table, col, label, date=None, where=None): return AGG('sum', table, '%s.%s' % (table, col), date='%s.%s' % (table, date) if date else None, where=where, label=label)
def AVGC(table, col, label, date=None): return AGG('avg', table, '%s.%s' % (table, col), date='%s.%s' % (table, date) if date else None, label=label)
insights = {"filters": [{"label": "Clinician", "list": "clin"}, {"label": "Service", "list": "svc"}, {"label": "Pay type", "list": "paytype"}],
    "gauges": [
        {"title": "Booked share of cap in the healthy band", "num": AGG('count', 'clin_months', where=[('band', '=', V('Healthy'))]), "den": AGG('count', 'clin_months')},
        {"title": "Clinician months on target", "num": AGG('count', 'targets', where=[('target_flag', '=', V('On target'))]), "den": AGG('count', 'targets')},
        {"title": "Retention to 6 sessions", "num": AGG('count', 'retention', where=[('retained', '=', V('Retained to 6'))]), "den": AGG('count', 'retention')},
        {"title": "Rebooking within 14 days", "num": AGG('count', 'rebook', where=[('rebook_check', '=', V('Rebooked'))]), "den": AGG('count', 'rebook')},
        {"title": "Pay share of revenue within the target", "num": AGG('count', 'payroll', where=[('pay_flag', '=', V('Within the target'))]), "den": AGG('count', 'payroll')},
        {"title": "Practice margin on target", "num": AGG('count', 'allin', where=[('margin_flag', '=', V('Margin on target'))]), "den": AGG('count', 'allin')}],
    "charts": [
        CHART('Clinical hours per month', 'column', 'month', [SUMC('clin_months', 'clinical_hours', 'Clinical hours', 'month')]),
        CHART('Clinical hours by clinician', 'bar', 'clin_months.clinician', [AGG('sum', 'clin_months', 'clin_months.clinical_hours', label='Clinical hours')]),
        CHART('Revenue by clinician', 'bar', 'clin_months.clinician', [AGG('sum', 'clin_months', 'clin_months.revenue', label='Revenue')]),
        CHART('Revenue per clinical hour per month', 'line', 'month', [AVGC('clin_months', 'rev_per_hour', 'Revenue per hour', 'month')]),
        CHART('Capacity against attended per month', 'column', 'month', [SUMC('clin_months', 'capacity', 'Capacity', 'month'), SUMC('clin_months', 'attended', 'Attended', 'month')]),
        CHART('Target against attended per month', 'column', 'month', [SUMC('targets', 'target_sessions', 'Target', 'month'), SUMC('targets', 'attended', 'Attended', 'month')]),
        CHART('Booked share of cap by clinician and strain line', 'combo', 'clin_months.clinician', [AGG('avg', 'clin_months', 'clin_months.share_of_cap', label='Booked share of cap'), AGG('avg', 'clin_months', 'clin_months.strain_line', label='Strain line')], line=1),
        CHART('Sessions per discharged client by clinician', 'bar', 'dropouts.clinician', [AGG('avg', 'dropouts', 'dropouts.sessions', label='Sessions per client')]),
        CHART('Late cancels and no-shows by clinician', 'stacked', 'clin_months.clinician', [AGG('sum', 'clin_months', 'clin_months.late_cancels', label='Late cancels'), AGG('sum', 'clin_months', 'clin_months.no_shows', label='No-shows')]),
        CHART('Pay per month', 'column', 'month', [SUMC('pay', 'amount', 'Pay', 'month')]),
        CHART('Pay by person', 'bar', 'pay.person', [AGG('sum', 'pay', 'pay.amount', label='Pay')]),
        CHART('Pay by pay type', 'bar', 'pay.pay_type', [AGG('sum', 'pay', 'pay.amount', label='Pay')]),
        CHART('Contractor pay per month', 'column', 'month', [SUMC('payroll', 'contractor_pay', 'Contractor pay', 'month')]),
        CHART('Supervision cost per month', 'column', 'month', [SUMC('allin', 'supervision_cost', 'Supervision cost', 'month')]),
        CHART('All-in cost per session by pay type', 'bar', 'allin.pay_type', [AGG('avg', 'allin', 'allin.cost_per_session', label='All-in cost per session')]),
        CHART('Practice margin by clinician', 'bar', 'allin.clinician', [AGG('sum', 'allin', 'allin.margin', label='Margin')]),
        CHART('Rebooked within 14 days per month', 'line', 'month', [SUMC('rebook', 'rebooked', 'Rebooked', 'date')]),
        CHART('Drop-outs by clinician', 'bar', 'dropouts.clinician', [AGG('count', 'dropouts', label='Drop-outs')]),
        CHART('Retained clients by service', 'bar', 'retention.service', [AGG('count', 'retention', where=[('retained', '=', V('Retained to 6'))], label='Retained to 6')]),
        CHART('Admin minutes by clinician', 'bar', 'admin_log.clinician', [AGG('sum', 'admin_log', 'admin_log.minutes', label='Admin minutes')]),
        CHART('Admin minutes per month', 'line', 'month', [SUMC('admin_log', 'minutes', 'Admin minutes', 'date')]),
        CHART('Contractor effective split per month', 'line', 'month', [AVGC('contractor_statements', 'effective_split', 'Effective split', 'month')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6
signature = [
    {"name": "Utilization and revenue per hour by clinician", "why": "booked share of cap in an idle, healthy or strain band beside the revenue of every clinical hour, each with the clinician's own 3-month and last-year figures", "where": "Clinician Months"},
    {"name": "Pay by pay type with employer costs", "why": "salary, percentage split, per-session and hourly pay side by side, with the employer cost and the pay share of fees for every person and month", "where": "Pay"},
    {"name": "Contractor statement and invoice check", "why": "fees charged, split and card fees give the amount due, and every invoice is matched to its statement so a difference is flagged before you pay", "where": "Contractor Invoices"},
    {"name": "Associate pay against the supervision log", "why": "session pay plus the supervision cost loaded onto the associate shows the net margin per session after supervision", "where": "All-in Cost"},
    {"name": "Salary or split comparison on the all-in cost", "why": "pay, employer cost, room time and admin for each pay type at five weekly loads, with the break-even load solved for you", "where": "Salary or Split Comparison"},
    {"name": "Clinician break-even sessions", "why": "the sessions a week a clinician needs to cover the all-in cost at the average charge", "where": "Clinician Break-even Sessions"},
    {"name": "Contractor split proposal tool", "why": "a new split tested on the practice margin per session and per year, with the highest split that keeps your margin target", "where": "Contractor Split Proposal"},
    {"name": "Retention, rebooking and drop-outs", "why": "who stays to six sessions, who rebooks within 14 days and who stops after the intake, per clinician and over time", "where": "Client Retention"},
    {"name": "Act-first clinician list", "why": "utilization band, retention, late notes, pay share and margin of each clinician ranked, with Review now, Watch or Fine", "where": "Act-first Clinician List"},
    {"name": "Monthly targets, reviews and leave balances", "why": "session and revenue targets with a pace gap, productivity reviews with an owner and a due date, and leave days left with sessions to move", "where": "Monthly Targets"}]
competitors = [
    {"what": "free payroll templates", "lacks": "list pay but have no pay type rules, employer costs, contractor card fees or room and admin cost per clinician"},
    {"what": "subscription practice-management software", "lacks": "charge per clinician and keep your data in their system, with no editable bands, split proposals or all-in cost by pay type"},
    {"what": "generic spreadsheet planners", "lacks": "hold hours and pay but never compare a salary with a split, check an invoice against a statement or show the margin per clinician"},
    {"what": "payroll apps for employees only", "lacks": "ignore contractors, per-session associates and supervision cost, so the true cost of each clinician stays hidden"},
    {"what": "paper timesheets and pay notebooks", "lacks": "cannot total booked share of cap, revenue per clinical hour or retention, and a wrong invoice is found only after payment"}]
guide = [
    'Open Start and type your practice name and your own limits in the yellow cells: the utilization bands, the profit target, the pay share target, the card fee share, the supervision rate and the retention and rebooking targets.',
    'Check Team, Services and Leave Balances. Team holds every clinician with the pay type, the split, the session rate, the session cap and the session target; the coordinator and the accountant are in the same list.',
    'Fill Clinician Months each month: weeks, capacity, booked and attended sessions, hours and revenue. Booked share of cap, the band and revenue per hour fill in, with your own history.',
    'Set Monthly Targets for the months ahead and note each Productivity Review with its action and due date.',
    'Keep Pay, Payroll Months and All-in Cost current. Pay per session, employer cost, total pay, pay share of revenue and the margin per clinician show where the money goes.',
    'Enter each contractor statement on Contractor Statements and each invoice on Contractor Invoices. A difference is flagged before you pay.',
    'Log Client Retention, Drop-outs and the Rebooking Log, and the Admin Time Log and Coordinator Timesheet each week.',
    'Use the decision tools for utilization, revenue per hour, all-in cost, contractor split, salary or split, break-even, retention, targets, leave, pay rises and the forecast. Each gives a verdict and a what-if table.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written.',
    'Read the Act-first Clinician List every month to see which clinician to review first.',
    'Read the KPI Dashboard and Charts every month: utilization, revenue per hour, pay share, margin per session, retention and rebooking.',
    'Replace the demo data with your own, row by row. The workbook holds numbers only, never session notes or diagnoses, and every pay rule is yours to check with your adviser.']
listing = {"title": "Therapy Practice Clinician Pay and Productivity Excel Template: Utilization, Revenue per Hour, Contractor Split, Associate Pay, Margin",
    "headline": "Know what every clinician earns the practice and costs it",
    "tags": ["therapy practice", "clinician pay", "payroll template", "contractor split", "associate pay", "excel template", "utilization rate", "revenue per hour", "private practice", "group practice", "clinician hours", "retention tracker", "practice management"],
    "description": ("Work out what every clinician earns your group therapy practice and what they cost it, in one Excel workbook. Built for an owner-clinician, employed clinicians, contract (self-employed) clinicians, an associate (works under supervision) and a front-desk coordinator.\n\n"
        "Clinician Months show sessions booked, attended, late cancelled and missed, clinical hours and revenue for every clinician and month. Booked share of cap is shown in three bands (idle below 70 percent, healthy 75 to 85 percent and strain above 90 percent, all editable), beside revenue per clinical hour and a compare-with-own-history row: this month, the 3-month average and the same month last year.\n\n"
        "Pay covers every pay type: salary with employer costs, percentage split for contractors, per-session pay for the associate and hourly pay for the coordinator. All-in Cost adds room time, admin and the supervision cost carried on the associate, so you see the practice margin per clinician against your profit target and pay as a share of revenue against your own target. "
        "Contractor Statements and Contractor Invoices are checked against each other, with the effective split after card fees, so a wrong invoice is caught before you pay it.\n\n"
        f"{len(tools)} decision tools answer the questions owners ask with a verdict and a what-if table: contractor split proposals, salary or split, break-even sessions, associate pay, pay rises, targets, leave, retention, rebooking and an act-first clinician list. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages.\n\n"
        "This is part five of the Therapy Private Practice suite. A standard .xlsx workbook with no macros and no subscription, one flat price with no per-clinician fee, your data stays with you, 15 languages in one purchase, with a demo copy full of sample data. The workbook holds numbers only, never session notes or diagnoses, and it does not promise results. Pay and tax rules differ: check your own local rules and confirm with your adviser."),
    "features": ["Booked share of cap in idle, healthy and strain bands", "Revenue per clinical hour with your own history", "Pay by pay type with employer costs", "All-in cost and margin per clinician",
                 "Contractor statements checked against invoices", "Contractor split proposal tool", "Retention, rebooking and drop-outs", f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "One flat price, your data stays with you"]}
import lib as _lib
s = _lib.spec(id=f'{SUITE}-p5', slug='therapy-practice-clinicians', profession='Therapy Private Practice', name='Clinician Pay and Productivity',
         tagline='Know what every clinician earns the practice and costs it', price_usd=29, colors={"primary": "#2F5D62", "accent": "#A7C4BC"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard,
         forms=forms, guide=guide, listing=listing, insights=insights, suite={"key": SUITE, "part": 5, "of": 8, "focus": "Clinician pay and productivity"}, signature=signature, competitors=competitors,
         tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'th5.en.json'))
    print('tables', len(tables), 'rows', sum(len(t['demo']) for t in tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']), 'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
