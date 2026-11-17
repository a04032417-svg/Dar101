"""Doula business suite - part 6: Doulas, Agency Splits and Pay Runs."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du6_lists import *
from du6_tables import settings, tables
from du6_tools import tools

SUITE = 'fx-20261115-doula-business'
NOTE = "Sample wording: adapt it to your own business and check your local rules about contractor terms."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
PC = tok('basis', 'Per client'); PH = tok('basis', 'Per hour'); MIL = tok('basis', 'Mileage'); STI = tok('basis', 'Backup stipend'); CALL = tok('basis', 'Backup call-out')
PAID = tok('paystatus', 'Paid'); DUE = tok('paystatus', 'Due')

# ------------------------------------------------------------------ forms (12)
def SPAY(extra): return 'SUMIFS({range:pay.pay_due},{range:pay.doula},{pick}%s)' % extra
forms = [
    FORM('payrun_sheet', 'Pay Run Sheet', 'Pay run for one doula and month', 'payrun.run_id', F(
        ('Month', 'payrun.month'), ('Doula', 'payrun.doula'), ('Per-client pay', 'payrun.per_client'), ('Per-hour pay', 'payrun.per_hour'), ('Mileage', 'payrun.mileage'), ('Backup pay', 'payrun.backup'), ('Total due', 'payrun.total_due'),
        ('Paid', 'payrun.paid'), ('Not paid yet', 'payrun.unpaid'), ('Difference', 'payrun.difference'), ('Check', 'payrun.check'), ('Statement sent on', 'payrun.sent_on')) + [
        FF('Total due, all doulas, this month', LK('payrun', 'run_id', 'month_due_all'), 'money'),
        FF('Share of the month total', 'IFERROR(%s/%s,0)' % (LK('payrun', 'run_id', 'total_due'), LK('payrun', 'run_id', 'month_due_all')), 'pct')]),
    FORM('doula_statement', 'Doula Statement Sheet', 'Statement of what a person is due now', 'team.name', F(
        ('Role', 'team.role'), ('Pay type', 'team.pay_type'), ('Phone', 'team.phone'), ('Agency share', 'team.agency_share'), ('Hourly rate', 'team.hourly_rate')) + [
        FF('Pay due this month so far', SPAY(',{range:pay.month},%s' % MS), 'money'), FF('Pay due last month', SPAY(',{range:pay.month},EDATE(%s,-1)' % MS), 'money'),
        FF('Paid last month', 'SUMIFS({range:pay.paid_amount},{range:pay.doula},{pick},{range:pay.month},EDATE(%s,-1))' % MS, 'money'),
        FF('Lines not paid yet', 'COUNTIFS({range:pay.doula},{pick},{range:pay.status},%s)' % DUE, 'int')],
        {"from": "pay", "match": "pay.doula", "columns": ["month", "client", "basis", "pay_due", "paid_amount", "status"], "max": 12}),
    FORM('split_agreement', 'Split Agreement Sheet', 'Agency share and hourly pay agreed with a doula', 'doulas.doula', F(('Agency share', 'doulas.agency_share'), ('Hourly pay', 'doulas.hourly_pay')) + [
        FF('Pay type', 'IFERROR(INDEX({range:team.pay_type},MATCH({pick},{range:team.name},0)),"")', 'text'), FF('Most due dates a month', 'IFERROR(INDEX({range:team.cap_births},MATCH({pick},{range:team.name},0)),0)', 'int'),
        FF('Clients with pay lines', 'IFERROR(INDEX({range:team.clients},MATCH({pick},{range:team.name},0)),0)', 'int'), FF('Margin per client now', 'IFERROR(INDEX({range:team.margin_pc},MATCH({pick},{range:team.name},0)),0)', 'money'),
        FF('Your target margin per client', '{set:target_margin_client}', 'money'), FF('Overhead per client', '{set:agency_cost_client}', 'money')]),
    FORM('split_change', 'Split Change Sheet', 'Proposed agency share and its effect', 'splits.split_id', F(
        ('Doula', 'splits.doula'), ('Proposed on', 'splits.proposed_on'), ('Current share', 'splits.current_share'), ('New agency share', 'splits.new_share'), ('Clients a year', 'splits.clients_year'), ('Average birth part', 'splits.avg_package'),
        ('Owner margin change a year', 'splits.margin_change'), ('Margin per client now', 'splits.mpc_now'), ('Margin per client after', 'splits.mpc_after'), ('Share that keeps your target', 'splits.counter_share'), ('Verdict', 'splits.verdict')) + [
        FF('Doula pay change per client', '-%s*(%s-%s)' % (LK('splits', 'split_id', 'avg_package'), LK('splits', 'split_id', 'new_share'), LK('splits', 'split_id', 'current_share')), 'money')]),
    FORM('adjust_sheet', 'Pay Adjustment Sheet', 'Adjustment for a pay line paid differently from what was due', 'diffs.pay_id', F(
        ('Doula', 'diffs.doula'), ('Client', 'diffs.client'), ('Month', 'diffs.month'), ('Pay due', 'diffs.pay_due'), ('Paid amount', 'diffs.paid_amount'), ('Difference', 'diffs.difference'), ('Status', 'diffs.status'),
        ('Adjustment to make', 'diffs.adjust'), ('Check', 'diffs.check')) + [
        FF('Basis of the line', 'IFERROR(INDEX({range:pay.basis},MATCH({pick},{range:pay.pay_id},0)),"")', 'text'), FF('Gross of the line', 'IFERROR(INDEX({range:pay.gross},MATCH({pick},{range:pay.pay_id},0)),0)', 'money'),
        FF('Agency keeps on the line', 'IFERROR(INDEX({range:pay.agency_keeps},MATCH({pick},{range:pay.pay_id},0)),0)', 'money')]),
    FORM('mileage_claim', 'Mileage Claim Sheet', 'Mileage claim of a doula for a month', 'payrun.run_id', F(
        ('Month', 'payrun.month'), ('Doula', 'payrun.doula'), ('Miles on the pay line', 'payrun.miles'), ('Mileage due', 'payrun.mileage'), ('Total paid', 'payrun.paid')) + [
        FF('Miles in Visits and Births Attended', 'SUMIFS({range:visits.miles},{range:visits.doula},%s,{range:visits.month},%s)+SUMIFS({range:births.miles},{range:births.doula},%s,{range:births.month},%s)' % (LK('payrun', 'run_id', 'doula'), LK('payrun', 'run_id', 'month'), LK('payrun', 'run_id', 'doula'), LK('payrun', 'run_id', 'month')), 'num'),
        FF('Mileage cost at the area rates', 'SUMIFS({range:visits.mileage_cost},{range:visits.doula},%s,{range:visits.month},%s)+SUMIFS({range:births.mileage_cost},{range:births.doula},%s,{range:births.month},%s)' % (LK('payrun', 'run_id', 'doula'), LK('payrun', 'run_id', 'month'), LK('payrun', 'run_id', 'doula'), LK('payrun', 'run_id', 'month')), 'money'),
        FF('Mileage rate, Northgate', '{set:mileage_rate_north}', 'money'), FF('Mileage rate, Southbank', '{set:mileage_rate_south}', 'money')]),
    FORM('stipend_sheet', 'Backup Stipend Sheet', 'Backup stipends and call-outs for a month', 'backup_month.month', F(
        ('Stipends', 'backup_month.stipend'), ('Call-out pay', 'backup_month.call_outs'), ('Total backup pay', 'backup_month.total'), ('Call-outs', 'backup_month.call_out_n'), ('Rota weeks', 'backup_month.rota_weeks'),
        ('Stipend on the rota', 'backup_month.rota_stipend'), ('Stipends paid less rota', 'backup_month.stipend_diff')) + [
        FF('Stipend per rota week', '{set:backup_stipend_week}', 'money'), FF('Call-outs at the flat pay', '%s*{set:backup_flat_pay}' % LK('backup_month', 'month', 'call_out_n'), 'money')],
        {"from": "pay", "match": "pay.month", "columns": ["doula", "client", "basis", "pay_due", "paid_amount"], "max": 20}),
    FORM('callout_sheet', 'Call-out Pay Sheet', 'Flat call-out pay of a backup doula', 'pay.pay_id', F(
        ('Month', 'pay.month'), ('Backup doula', 'pay.doula'), ('Client ID', 'pay.client_id'), ('Client', 'pay.client'), ('Hours attended', 'pay.hours'), ('Pay due', 'pay.pay_due'), ('Paid amount', 'pay.paid_amount'), ('Status', 'pay.status'),
        ('Difference', 'pay.difference')) + [FF('Flat call-out pay in Settings', '{set:backup_flat_pay}', 'money'), FF('Pay due less the flat pay', '%s-{set:backup_flat_pay}' % LK('pay', 'pay_id', 'pay_due'), 'money')]),
    FORM('new_doula_sheet', 'New Doula Sheet', 'Terms of a new contracted or backup doula', 'team.name', F(
        ('Staff ID', 'team.staff_id'), ('Role', 'team.role'), ('Pay type', 'team.pay_type'), ('Phone', 'team.phone'), ('Email', 'team.email'), ('Service', 'team.service'), ('Hourly rate', 'team.hourly_rate'),
        ('Most due dates a month', 'team.cap_births'), ('Weekly hours cap', 'team.weekly_hours_cap'), ('Start', 'team.start'), ('First review on', 'team.review_on')) + [
        FF('Agency share on the birth part', LK('team', 'name', 'agency_share'), 'pct'), FF('Overhead per client', '{set:agency_cost_client}', 'money')]),
    FORM('review_sheet', 'Doula Review Sheet', 'Review of a doula with the numbers behind it', 'team.name', F(
        ('Clients with pay lines', 'team.clients'), ('Margin after costs', 'team.margin'), ('Margin per client', 'team.margin_pc'), ('Clients over plan hours', 'team.over_share'), ('Hours worked, 12 months', 'team.hours_12'),
        ('Pay per hour worked, 12 months', 'team.pay_hour_12'), ('Review on', 'team.review_on')) + [
        FF('Margin per client less your target', '%s-{set:target_margin_client}' % LK('team', 'name', 'margin_pc'), 'money'), FF('Pay per hour less the lowest fair pay', '%s-{set:min_pay_hour}' % LK('team', 'name', 'pay_hour_12'), 'money')]),
    FORM('owner_time_sheet', 'Owner Time Sheet', 'Owner hours for one week', 'owner_time.log_id', F(
        ('Week', 'owner_time.week'), ('Own client hours', 'owner_time.own_client_hours'), ('Management hours', 'owner_time.management_hours'), ('Admin hours', 'owner_time.admin_hours'), ('Total hours', 'owner_time.total_hours')) + [
        FF('Owner draw per hour worked', '{set:owner_draw}*12/52/%s' % LK('owner_time', 'log_id', 'total_hours'), 'money'), FF('Share of hours on own clients', '%s/%s' % (LK('owner_time', 'log_id', 'own_client_hours'), LK('owner_time', 'log_id', 'total_hours')), 'pct'),
        FF('Pay per hour you want', '{set:target_income_hour}', 'money')]),
    FORM('yearend_sheet', 'Year-End Pay Sheet', 'Year-end pay of a person for the last 12 months', 'team.name', F(
        ('Role', 'team.role'), ('Doula pay, 12 months', 'team.pay_12'), ('Mileage paid, 12 months', 'team.mileage_12'), ('Backup pay, 12 months', 'team.backup_12')) + [
        FF('Paid, 12 months', 'SUMIFS({range:pay.paid_amount},{range:pay.doula},{pick},{range:pay.month},">="&EDATE(%s,-12),{range:pay.month},"<"&%s)' % (MS, MS), 'money'),
        FF('Pay lines, 12 months', 'COUNTIFS({range:pay.doula},{pick},{range:pay.month},">="&EDATE(%s,-12),{range:pay.month},"<"&%s)' % (MS, MS), 'int'),
        FF('Lines that differ, 12 months', 'SUMIFS({range:pay.differs},{range:pay.doula},{pick},{range:pay.month},">="&EDATE(%s,-12),{range:pay.month},"<"&%s)' % (MS, MS), 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('pay_statement_doc', 'Doula Pay Statement', 'Pay statement for a doula and a month', 'payrun.run_id', [
        'Pay statement of {set:company}, dated {today}. Month: {col:payrun.month}. Doula: {col:payrun.doula}.',
        'Per-client pay: {col:payrun.per_client}. Per-hour pay: {col:payrun.per_hour}. Mileage: {col:payrun.mileage} for {col:payrun.miles} miles. Backup pay: {col:payrun.backup}. Total due: {col:payrun.total_due}.',
        'Paid so far: {col:payrun.paid}. Not paid yet: {col:payrun.unpaid}. Difference between paid and due: {col:payrun.difference}. Check: {col:payrun.check}.',
        'Please tell us within a few days about any line you do not agree with. This statement shows dates, hours, miles and amounts only.'], ['Owner-doula', 'Doula'], NOTE),
    DOC('payrun_summary_doc', 'Pay Run Summary', 'Pay run summary for the owner-doula', 'payrun.run_id', [
        'Pay run summary of {set:company}, dated {today}. Month: {col:payrun.month}.',
        'Total due to all doulas and backup doulas: {col:payrun.month_due_all}. Not paid yet: {col:payrun.month_open_due}. Pay lines that differ from what was due: {col:payrun.month_diff_lines}.',
        'The line of {col:payrun.doula} shows a total due of {col:payrun.total_due}, paid {col:payrun.paid}, check: {col:payrun.check}.', 'Check the lines that differ before the run is closed.'], ['Owner-doula'], NOTE),
    DOC('split_summary_doc', 'Agency Split Summary', 'Summary of the split terms of a doula', 'team.name', [
        'Agency split summary of {set:company}, dated {today}. Doula: {col:team.name}. Pay type: {col:team.pay_type}.',
        'The agency keeps {col:team.agency_share} of the birth part of each package. The hourly pay for postpartum hours is {col:team.hourly_rate}. The most due dates in a month is {col:team.cap_births}.',
        'Clients with pay lines so far: {col:team.clients}. Margin per client for the agency after pay, mileage and overhead: {col:team.margin_pc}.', 'These are the terms in use today. Check your local rules about contractor terms before you change them.'], ['Owner-doula', 'Doula'], NOTE),
    DOC('split_letter_doc', 'Split Change Letter', 'Letter about a change of the agency share', 'splits.split_id', [
        'Letter of {set:company}, dated {today}. Dear {col:splits.doula},',
        'We would like to change the agency share on the birth part of each package from {col:splits.current_share} to {col:splits.new_share}, from {col:splits.proposed_on}.',
        'On about {col:splits.clients_year} clients a year with an average birth part of {col:splits.avg_package}, this changes the agency margin by {col:splits.margin_change} a year. The agency margin per client would be {col:splits.mpc_after}. Verdict: {col:splits.verdict}.',
        'The share that keeps the agency target is {col:splits.counter_share}. Please reply with your view before the new share starts.'], ['Owner-doula', 'Doula'], NOTE),
    DOC('backup_statement_doc', 'Backup Stipend Statement', 'Statement of backup stipends for a month', 'backup_month.month', [
        'Backup stipend statement of {set:company}, dated {today}. Month: {col:backup_month.month}.',
        'Stipends paid or due: {col:backup_month.stipend}. Rota weeks: {col:backup_month.rota_weeks}. Stipend on the rota: {col:backup_month.rota_stipend}. Difference: {col:backup_month.stipend_diff}.',
        'Call-outs: {col:backup_month.call_out_n}. Call-out pay: {col:backup_month.call_outs}. Total backup pay: {col:backup_month.total}.', 'A backup doula is paid a weekly stipend plus a flat call-out when they attend.'], ['Owner-doula', 'Backup doula'], NOTE),
    DOC('callout_statement_doc', 'Call-out Pay Statement', 'Statement of one call-out of a backup doula', 'pay.pay_id', [
        'Call-out pay statement of {set:company}, dated {today}. Backup doula: {col:pay.doula}. Month: {col:pay.month}.',
        'Client: {col:pay.client} ({col:pay.client_id}). Hours attended: {col:pay.hours}. Pay due: {col:pay.pay_due}. Paid: {col:pay.paid_amount} ({col:pay.status}). Difference: {col:pay.difference}.',
        'The flat call-out pay in Settings is {set:backup_flat_pay}.', 'This statement holds the date, the hours and the amount only.'], ['Owner-doula', 'Backup doula'], NOTE),
    DOC('mileage_statement_doc', 'Mileage Statement', 'Mileage statement for a doula and a month', 'payrun.run_id', [
        'Mileage statement of {set:company}, dated {today}. Month: {col:payrun.month}. Doula: {col:payrun.doula}.',
        'Miles on the pay line: {col:payrun.miles}. Mileage due: {col:payrun.mileage}. The rates are {set:mileage_rate_north} a mile in Northgate and {set:mileage_rate_south} a mile in Southbank.',
        'Mileage is counted from the miles written in the Visit Log and the Birth Log. Please tell us about any trip that is missing.'], ['Doula', 'Owner-doula'], NOTE),
    DOC('offer_letter_doc', 'New Doula Offer Letter', 'Offer letter for a new contracted doula', 'team.name', [
        'Offer of {set:company}, dated {today}. Dear {col:team.name},',
        'We would like you to join as {col:team.role}, from {col:team.start}. Pay type: {col:team.pay_type}. Agency share on the birth part: {col:team.agency_share}. Hourly pay for postpartum hours: {col:team.hourly_rate}.',
        'Most due dates in a month: {col:team.cap_births}. Weekly hours cap: {col:team.weekly_hours_cap}. Your first review is on {col:team.review_on}.', 'Terms, insurance and records follow your local rules. Please check them with your own adviser before you sign.'], ['Owner-doula', 'Doula'], NOTE),
    DOC('review_note_doc', 'Doula Review Note', 'Review note for a doula', 'team.name', [
        'Review note of {set:company}, dated {today}. Doula: {col:team.name}. Review on {col:team.review_on}.',
        'Clients with pay lines: {col:team.clients}. Margin after costs for the agency: {col:team.margin}, or {col:team.margin_pc} per client. Share of clients over plan hours: {col:team.over_share}.',
        'Hours worked in 12 months: {col:team.hours_12}. Pay per hour worked: {col:team.pay_hour_12}.', 'Use this note to talk about terms, capacity and hours. It holds numbers only.'], ['Owner-doula', 'Doula'], NOTE),
    DOC('capacity_plan_doc', 'Capacity Plan by Doula', 'Capacity plan for a doula and a month', 'cap.cap_id', [
        'Capacity plan of {set:company}, dated {today}. Doula: {col:cap.doula}. Month: {col:cap.month}.',
        'Clients with a due date: {col:cap.clients}. On-call windows: {col:cap.windows}. On-call days: {col:cap.oncall_days}. Most due dates a month: {col:cap.cap}. Places left: {col:cap.free}. Share used: {col:cap.share_used}. Check: {col:cap.flag}.',
        'When the check says over capacity, name a backup doula or move a due date to another doula.', 'The estimated due date is a date the client gives. It is used only to plan the on-call window.'], ['Owner-doula', 'Doula'], NOTE),
    DOC('yearend_summary_doc', 'Year-End Pay Statement', 'Year-end pay summary for the accountant', 'team.name', [
        'Year-end pay summary of {set:company}, dated {today}. Person: {col:team.name}. Role: {col:team.role}.',
        'Doula pay in the last 12 months: {col:team.pay_12}. Mileage paid: {col:team.mileage_12}. Backup pay: {col:team.backup_12}.',
        'Hours worked in the last 12 months: {col:team.hours_12}. Pay per hour worked: {col:team.pay_hour_12}.', 'Amounts are before any tax. Income tax and contractor questions: check with your adviser and your local rules.'], ['Owner-doula', 'Accountant'], NOTE),
    DOC('owner_time_doc', 'Owner Time Report', 'Owner time report for a month', 'owner_load.month', [
        'Owner time report of {set:company}, dated {today}. Month: {col:owner_load.month}.',
        'Hours on own clients: {col:owner_load.own_hours}. Management hours: {col:owner_load.mgmt_hours}. Admin hours: {col:owner_load.admin_hours}. Total: {col:owner_load.total_hours}. Owner draw per hour worked: {col:owner_load.pay_hour}.',
        'Clients signed: {col:owner_load.new_clients}. Admin cost per new client: {col:owner_load.admin_cost_client} against an overhead setting of {col:owner_load.overhead_client}.', 'Use this report to decide which hours to hand over.'], ['Owner-doula'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('monthly_payrun', 'Monthly Pay Run Steps', 'payrun', 'payrun.month', [('Check that every visit and birth of the month is logged', 28), ('Write the pay lines of the month', 30), ('Check the lines against the hours and miles', 31), ('Send the statements', 33), ('Pay the doulas and backup doulas', 38), ('Record the paid dates and any difference', 40)]),
    CHK('pay_adjust', 'Pay Adjustment Steps', 'pay', 'pay.month', [('Find the pay lines paid differently from what was due', 38), ('Ask the doula to confirm the hours', 40), ('Write the adjustment', 42), ('Pay or deduct it in the next run', 68), ('Tell the doula in writing', 45)]),
    CHK('split_review', 'Agency Split Review Steps', 'splits', 'splits.proposed_on', [('List the clients and the margin per client of the doula', 0), ('Test the proposed share in Agency Split Proposal', 1), ('Compare with your target margin', 2), ('Reply to the doula with a counter share if needed', 5), ('Write the agreed share in Doulas', 10), ('Send the split change letter', 12)]),
    CHK('new_doula', 'New Contracted Doula Steps', 'team', 'team.start', [('Test the case in New Doula Case', -30), ('Agree the share, hourly pay and caps', -21), ('Check insurance and contractor terms with your adviser', -14), ('Add the doula to Team and Doulas', -7), ('Introduce the first clients', 14), ('Hold the first review', 60)]),
    CHK('backup_run', 'Backup Stipend Run Steps', 'rota', 'rota.week', [('Check the rota weeks of each backup doula', 28), ('Write the stipend lines', 30), ('Add the call-out pay for each birth attended', 31), ('Send the backup statements', 33), ('Pay the stipends and call-outs', 38)]),
    CHK('mileage_check', 'Mileage Check Steps', 'payrun', 'payrun.month', [('Ask each doula for the mileage log', 28), ('Compare the miles with Visits and Births Attended', 30), ('Check the area rates in Settings', 31), ('Fix any difference in the mileage line', 33), ('Send the mileage totals to the accountant', 35)]),
    CHK('doula_review', 'Doula Review Steps', 'team', 'team.review_on', [('Open the Doula Review Sheet', -7), ('Check the margin per client and the hours over plan', -5), ('Check the pay per hour worked', -3), ('Hold the review meeting', 0), ('Agree any change of share or caps', 1), ('Write the next review date', 2)]),
    CHK('year_end_pay', 'Year-End Pay Steps', 'owner_load', 'owner_load.month', [('Check that all pay lines of the year are paid', 31), ('Run Year-End Pay Summary and check the totals tie', 33), ('Send the year-end pay summary to the accountant', 36), ('Send each doula their summary', 38), ('Keep the records as your local rules ask', 45)]),
    CHK('doula_leaving', 'Doula Leaving Steps', 'oncall', 'oncall.oncall_end', [('Agree the last working day', -28), ('List the clients and windows to move', -21), ('Name new doulas for the clients', -14), ('Pay the last pay run and mileage', 30), ('Update Team and Doulas', 31), ('Check your local rules for records and contractor terms', 32)]),
    CHK('owner_time_review', 'Owner Time Review Steps', 'owner_time', 'owner_time.week', [('Write the hours of the week', 7), ('Check the share on own clients', 8), ('Check the draw per hour worked', 9), ('Choose one task to hand over', 10), ('Review the month against Owner Own-Client Load', 28)]),
    CHK('capacity_review', 'Capacity Review by Doula Steps', 'cap', 'cap.month', [('Open Capacity by Doula for the month', -60), ('Find doulas over or at capacity', -55), ('Name a backup doula for any window without one', -45), ('Move a due date to a doula with room', -35), ('Confirm the places with each doula', -30)]),
    CHK('margin_review', 'Quarterly Margin Review Steps', 'profit', 'profit.month', [('Open Agency Margin by Client', 90), ('Find doulas with a negative margin', 91), ('Run Losing Split Finder', 92), ('Plan a counter share or a price change', 95), ('Review the overhead per client', 98), ('Write the decisions in Split Proposals', 100)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('d_statement', 'Doula: your statement is ready', 'payrun', 'payrun.doula_phone', 'Hello {doula}, your statement for {month} is ready, total {total_due}. {company}'),
    M('d_paid', 'Doula: your pay was sent', 'pay', 'pay.doula_phone', 'Hello {doula}, your pay of {paid_amount} was sent on {paid_on}. {company}'),
    M('d_differs', 'Doula: a pay line differs', 'pay', 'pay.doula_phone', 'Hello {doula}, the pay of {client} differs by {difference} from what was due. We are checking. {company}'),
    M('d_adjusted', 'Doula: your pay was adjusted', 'diffs', 'diffs.doula_phone', 'Hello {doula}, your pay for {client} was adjusted by {adjust}. {company}'),
    M('d_mileage_log', 'Doula: please send your mileage log', 'payrun', 'payrun.doula_phone', 'Hello {doula}, please send your mileage log for {month}. {company}'),
    M('d_mileage_pay', 'Doula: your mileage pay', 'pay', 'pay.doula_phone', 'Hello {doula}, your mileage of {miles} miles is {pay_due}. {company}'),
    M('d_split', 'Doula: your split changes', 'splits', 'splits.doula_phone', 'Hello {doula}, your agency share changes to {new_share} from {proposed_on}. The effect for the agency is {margin_change} a year. {company}'),
    M('d_hourly', 'Doula: your hourly pay changes', 'team', 'team.phone', 'Hello {name}, your hourly pay changes to {hourly_rate} from {review_on}. {company}'),
    M('d_newclient', 'Doula: a new client is assigned', 'clients', 'clients.doula_phone', 'Hello {doula}, a new client is assigned to you: {client}, due {edd}. {company}'),
    M('d_load', 'Doula: your clients and on-call days', 'cap', 'cap.doula_phone', 'Hello {doula}, you have {clients} clients and {oncall_days} on-call days in {month}. {company}'),
    M('d_room', 'Doula: you have room for another client', 'cap', 'cap.doula_phone', 'Hello {doula}, you have {free} places left in {month}. {company}'),
    M('d_yearend', 'Doula: your year-end pay summary', 'team', 'team.phone', 'Hello {name}, your year-end pay summary is ready: {pay_12} in the last 12 months. {company}'),
    M('d_hours', 'Doula: please confirm your hours', 'pay', 'pay.doula_phone', 'Hello {doula}, please confirm your hours for {client}: {hours} hours for {month}. {company}'),
    M('d_review', 'Doula: your review meeting', 'team', 'team.phone', 'Hello {name}, your review meeting is on {review_on}. {company}'),
    M('b_stipend', 'Backup doula: your pay for the month', 'payrun', 'payrun.doula_phone', 'Hello {doula}, your backup pay for {month} is {backup}. {company}'),
    M('b_callout', 'Backup doula: your call-out pay', 'pay', 'pay.doula_phone', 'Hello {doula}, your call-out pay for {client} is {pay_due}. {company}'),
    M('b_rota', 'Backup doula: your rota weeks', 'payrun', 'payrun.doula_phone', 'Hello {doula}, you have {rota_weeks} rota weeks in {month}. {company}'),
    M('o_payrun', 'Owner: the pay run totals', 'payrun', 'payrun.owner_phone', 'Hello, the pay run for {month} totals {month_due_all}. {company}'),
    M('o_differ', 'Owner: pay lines differ from due', 'payrun', 'payrun.owner_phone', 'Hello, {month_diff_lines} pay lines of {month} differ from what was due. {company}'),
    M('o_leaves', 'Owner: a doula leaves a margin', 'team', 'team.owner_phone', 'Hello, {name} leaves the agency {margin} after costs, {margin_pc} per client. {company}'),
    M('o_loses', 'Owner: the agency loses on a doula', 'team', 'team.owner_phone', 'Hello, the agency loses {loss} on the births of {name}. {company}'),
    M('o_proposal', 'Owner: a split changes your margin', 'splits', 'splits.owner_phone', 'Hello, the split proposal from {doula} would change your margin by {margin_change} a year. {company}'),
    M('o_ownhours', 'Owner: your own client hours', 'owner_load', 'owner_load.owner_phone', 'Hello, your own client hours in {month} are {own_hours}. {company}'),
    M('o_payhour', 'Owner: your pay per hour worked', 'owner_load', 'owner_load.owner_phone', 'Hello, your pay per hour worked in {month} is {pay_hour}. {company}'),
    M('o_assign', 'Owner: a doula to assign for the month', 'cap', 'cap.owner_phone', 'Hello, {doula} has {free} places left in {month}, a good doula to assign. {company}'),
    M('o_nextrun', 'Owner: the pay due next run', 'payrun', 'payrun.owner_phone', 'Hello, the pay not paid yet for {month} is {month_open_due}. {company}'),
    M('o_overhead', 'Owner: overhead against your setting', 'owner_load', 'owner_load.owner_phone', 'Hello, admin cost per new client in {month} is {admin_cost_client} against your overhead setting of {overhead_client}. {company}'),
    M('o_waiting', 'Owner: a split proposal is waiting', 'splits', 'splits.owner_phone', 'Hello, {doula} has a new split proposal waiting: agency share {new_share}. {company}'),
    M('a_check', 'Admin: pay lines to check before the run', 'payrun', 'payrun.admin_phone', 'Hello, {month_diff_lines} pay lines of {month} need a check before the run. {company}'),
    M('a_send', 'Admin: statements to send today', 'payrun', 'payrun.admin_phone', 'Hello, please send the statement of {doula} for {month}, total {total_due}. {company}'),
    M('a_mileage', 'Admin: mileage logs still missing', 'payrun', 'payrun.admin_phone', 'Hello, the mileage log of {doula} for {month} is still missing: mileage due {mileage}. {company}'),
    M('x_pay', 'Accountant: doula pay for the month', 'payrun', 'payrun.accountant_phone', 'Hello, doula pay for {month} is {month_due_all}. {company}'),
    M('x_year', 'Accountant: the year-end pay summary', 'team', 'team.accountant_phone', 'Hello, the year-end pay summary of {name} is ready: {pay_12} in the last 12 months. {company}'),
    M('x_backup', 'Accountant: backup pay for the month', 'backup_month', 'backup_month.accountant_phone', 'Hello, backup stipends and call-outs for {month}: {stipend} and {call_outs}, {total} in all. {company}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30)
W12 = '{range:pay.month},">="&EDATE(%s,-12),{range:pay.month},"<"&%s' % (MS, MS)
def P12(b, c='pay_due'): return 'SUMIFS({range:pay.%s},{range:pay.basis},%s,%s)' % (c, b, W12)
M12 = '{range:margin.edd},">="&EDATE(%s,-12),{range:margin.edd},"<"&%s' % (MS, MS)
H12 = '{range:hrs.month},">="&EDATE(%s,-12),{range:hrs.month},"<"&%s' % (MS, MS)
NDOU = 'COUNTIFS({range:doulas.doula},"<>")'
OT4 = lambda c: 'SUMIFS({range:owner_time.%s},{range:owner_time.week},">="&({today}-28))' % c
DAYS = '(DAY({today})/DAY(EDATE(%s,1)-1))' % MS
kpis = [
    KPI('Pay due this month', 'SUMIFS({range:pay.pay_due},{range:pay.month},%s)' % MS, 'money'),
    KPI('Pay due last month', 'SUMIFS({range:pay.pay_due},{range:pay.month},EDATE(%s,-1))' % MS, 'money'),
    KPI('Pay paid last month', 'SUMIFS({range:pay.paid_amount},{range:pay.month},EDATE(%s,-1))' % MS, 'money'),
    KPI('Pay lines due not yet paid', 'COUNTIFS({range:pay.status},%s)' % DUE, 'int'),
    KPI('Pay lines that differ from what was due', 'COUNTIFS({range:pay.differs},1)', 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Amount of differences (paid less due)', 'SUMIFS({range:pay.difference},{range:pay.differs},1)', 'money'),
    KPI('Doula pay, last 12 months', '%s+%s' % (P12(PC), P12(PH)), 'money'),
    KPI('Backup pay, last 12 months', '%s+%s' % (P12(STI), P12(CALL)), 'money'),
    KPI('Mileage paid, last 12 months', P12(MIL), 'money'),
    KPI('Agency revenue, last 12 months', '%s+%s' % (P12(PC, 'gross'), P12(PH, 'gross')), 'money'),
    KPI('Agency margin after costs, 12 months', 'SUMIFS({range:margin.margin},%s)' % M12, 'money'),
    KPI('Agency margin per client, last 12 months', 'IFERROR(SUMIFS({range:margin.margin},%s)/COUNTIFS(%s),0)' % (M12, M12), 'money'),
    KPI('Agency share of revenue, last 12 months', 'IFERROR(1-(%s+%s)/(%s+%s),0)' % (P12(PC), P12(PH), P12(PC, 'gross'), P12(PH, 'gross')), 'pct'),
    KPI('Doulas with a negative margin', 'COUNTIFS({range:margin_doula.margin},"<0")', 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Margin of the best doula', 'MAX({range:margin_doula.margin})', 'money'),
    KPI('Margin of the lowest doula', 'MIN({range:margin_doula.margin})', 'money'),
    KPI('Clients per contracted doula', 'SUM({range:margin_doula.clients})/COUNTIFS({range:margin_doula.doula},"<>")', 'num'),
    KPI('Active clients per doula', '(COUNTIFS({range:clients.status},%s)+COUNTIFS({range:clients.status},%s)+COUNTIFS({range:clients.status},%s))/%s' % (tok('cstatus', 'Booked'), tok('cstatus', 'On call'), tok('cstatus', 'Postpartum care'), NDOU), 'num'),
    KPI('On-call days per doula this month', 'SUMIFS({range:cap.oncall_days},{range:cap.month},%s)/%s' % (MS, NDOU), 'num'),
    KPI('Free capacity, next 3 months (places)', 'SUMIFS({range:cap.free},{range:cap.month},">"&%s,{range:cap.month},"<="&EDATE(%s,3))' % (MS, MS), 'int'),
    KPI('Doula pay per hour worked, 12 months', 'IFERROR(SUMIFS({range:hrs.pay},%s)/SUMIFS({range:hrs.total_hours},%s,{range:hrs.doula},"<>"&%s),0)' % (H12, H12, tok('doula', OWNER)), 'money'),
    KPI('Per-client pay share of pay', 'IFERROR(%s/(%s+%s),0)' % (P12(PC), P12(PC), P12(PH)), 'pct'),
    KPI('Per-hour pay share of pay', 'IFERROR(%s/(%s+%s),0)' % (P12(PH), P12(PC), P12(PH)), 'pct'),
    KPI('Backup call-out pay, last 12 months', P12(CALL), 'money'),
    KPI('Owner own-client hours, last 4 weeks', OT4('own_client_hours'), 'num'),
    KPI('Owner management and admin, 4 weeks', '%s+%s' % (OT4('management_hours'), OT4('admin_hours')), 'num'),
    KPI('Owner pay per hour worked', 'IFERROR({set:owner_draw}/((%s+%s+%s)*52/12/4),0)' % (OT4('own_client_hours'), OT4('management_hours'), OT4('admin_hours')), 'money'),
    KPI('Overhead per client from admin hours', 'IFERROR(AVERAGEIFS({range:owner_load.admin_cost_client},{range:owner_load.month},">="&EDATE(%s,-12),{range:owner_load.month},"<"&%s,{range:owner_load.admin_cost_client},">0"),0)' % (MS, MS), 'money'),
    KPI('Next pay run total (projected)', 'IFERROR(SUMIFS({range:pay.pay_due},{range:pay.month},%s)/%s,0)' % (MS, DAYS), 'money'),
    KPI('Doulas on the agency', NDOU, 'int'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Agency Pay Dashboard", "kpis": kpis,
    "monthly": {"title": "Pay due, paid and gross revenue by month", "date": "pay.month", "series": [
        {"label": "Pay due", "sum": "pay.pay_due", "date": "pay.month"}, {"label": "Paid", "sum": "pay.paid_amount", "date": "pay.month"}, {"label": "Gross revenue", "sum": "pay.gross", "date": "pay.month"},
        {"label": "Own client hours", "sum": "owner_time.own_client_hours", "date": "owner_time.week"}]},
    "breakdowns": [{"title": "Pay due by doula", "by": "pay.doula", "value": "pay.pay_due", "agg": "sum"}, {"title": "Pay due by basis", "by": "pay.basis", "value": "pay.pay_due", "agg": "sum"},
                   {"title": "Pay lines by status", "by": "pay.status", "value": "pay.pay_due", "agg": "count"}, {"title": "Clients by doula", "by": "clients.doula", "value": "clients.client_id", "agg": "count"}]}
def PL(w): return [('basis', '=', w)] if isinstance(w, str) else w
FOUR = ['Mei-Ling Chen', 'Sven Lindqvist', 'Katarzyna Nowak', 'Fatou Diop']
insights = {"filters": [{"label": "Paid person", "list": "payee"}, {"label": "Pay basis", "list": "basis"}, {"label": "Area", "list": "area"}],
    "gauges": [
        {"title": "Pay lines paid as due", "num": AGG('count', 'pay', where=[('status', '=', PAID), ('differs', '=', 0)]), "den": AGG('count', 'pay', where=[('status', '=', PAID)])},
        {"title": "Clients meeting the target margin", "num": AGG('count', 'margin', where=[('meets', '=', 1)]), "den": AGG('count', 'margin')},
        {"title": "Doulas with a positive margin", "num": AGG('count', 'margin_doula', where=[('margin', '>', 0)]), "den": AGG('count', 'margin_doula')},
        {"title": "Capacity used next month", "num": AGG('sum', 'cap', 'cap.clients', where=[('next_month', '=', 1)]), "den": AGG('sum', 'cap', 'cap.cap', where=[('next_month', '=', 1)])},
        {"title": "Clients that cover their overhead", "num": AGG('count', 'margin', where=[('margin', '>=', 0)]), "den": AGG('count', 'margin')},
        {"title": "Statements sent on time", "num": AGG('count', 'payrun', where=[('on_time', '=', 1)]), "den": AGG('count', 'payrun', where=[('sent', '=', 1)])}],
    "charts": [
        CHART('Doula pay per month', 'column', 'month', [AGG('sum', 'pay', 'pay.pay_due', date='pay.month', where=[('basis', '=', PC)], label='Per-client pay'), AGG('sum', 'pay', 'pay.pay_due', date='pay.month', where=[('basis', '=', PH)], label='Per-hour pay')]),
        CHART('Doula pay by doula', 'bar', 'pay.doula', [AGG('sum', 'pay', 'pay.pay_due', label='Pay due')]),
        CHART('Pay by basis', 'bar', 'pay.basis', [AGG('sum', 'pay', 'pay.pay_due', label='Pay due')]),
        CHART('Pay lines by status', 'bar', 'pay.status', [AGG('count', 'pay', label='Pay lines')]),
        CHART('Pay lines per month', 'column', 'month', [AGG('count', 'pay', date='pay.month', label='Pay lines')]),
        CHART('Mileage pay per month', 'column', 'month', [AGG('sum', 'pay', 'pay.pay_due', date='pay.month', where=[('basis', '=', MIL)], label='Mileage pay')]),
        CHART('Mileage pay by doula', 'bar', 'pay.doula', [AGG('sum', 'pay', 'pay.pay_due', where=[('basis', '=', MIL)], label='Mileage pay')]),
        CHART('Backup pay per month', 'stacked', 'month', [AGG('sum', 'pay', 'pay.pay_due', date='pay.month', where=[('basis', '=', STI)], label='Stipends'), AGG('sum', 'pay', 'pay.pay_due', date='pay.month', where=[('basis', '=', CALL)], label='Call-outs')]),
        CHART('Backup stipends by backup doula', 'bar', 'rota.backup', [AGG('sum', 'rota', 'rota.stipend', label='Stipend on the rota')]),
        CHART('Gross revenue by doula', 'bar', 'profit.doula', [AGG('sum', 'profit', 'profit.revenue', label='Revenue')]),
        CHART('Pay due by doula per month', 'stacked', 'month', [AGG('sum', 'pay', 'pay.pay_due', date='pay.month', where=[('doula', '=', tok('payee', n))], label=n) for n in FOUR]),
        CHART('Agency share by doula', 'bar', 'doulas.doula', [AGG('avg', 'doulas', 'doulas.agency_share', label='Agency share')]),
        CHART('Hours worked by doula', 'bar', 'hrs.doula', [AGG('sum', 'hrs', 'hrs.visit_hours', label='Visit hours'), AGG('sum', 'hrs', 'hrs.birth_hours', label='Birth hours')]),
        CHART('Clients by doula', 'bar', 'clients.doula', [AGG('count', 'clients', label='Clients')]),
        CHART('Clients by doula and status', 'bar', 'clients.doula', [AGG('count', 'clients', where=[('status', '=', tok('cstatus', s))], label=s) for s in ('Booked', 'On call', 'Postpartum care', 'Completed')]),
        CHART('Births attended by doula', 'bar', 'births.doula', [AGG('count', 'births', label='Births attended')]),
        CHART('Visit hours by doula', 'bar', 'visits.doula', [AGG('sum', 'visits', 'visits.hours', label='Visit hours')]),
        CHART('Owner own-client hours per month', 'column', 'month', [AGG('sum', 'owner_time', 'owner_time.own_client_hours', date='owner_time.week', label='Own client hours')]),
        CHART('Owner management hours per month', 'column', 'month', [AGG('sum', 'owner_time', 'owner_time.management_hours', date='owner_time.week', label='Management hours')]),
        CHART('Owner admin hours per month', 'column', 'month', [AGG('sum', 'owner_time', 'owner_time.admin_hours', date='owner_time.week', label='Admin hours')]),
        CHART('Unpaid pay per month', 'column', 'month', [AGG('sum', 'pay', 'pay.pay_due', date='pay.month', where=[('status', '=', DUE)], label='Pay not paid yet')]),
        CHART('Paid amount per month', 'column', 'month', [AGG('sum', 'pay', 'pay.paid_amount', date='pay.month', label='Paid')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Agency doula pay calculator", "why": "a package, a doula and the trips turned into pay, backup, mileage, overhead and the margin per client against your target", "where": "Agency Doula Pay Calculator"},
    {"name": "Agency capacity by doula", "why": "places left for each doula in any month, with the best doula to assign for a birth or postpartum client", "where": "Agency Capacity by Doula"},
    {"name": "Agency split proposal", "why": "a proposed share tested for the owner margin and the doula pay, with the counter share that keeps your target", "where": "Agency Split Proposal"},
    {"name": "Doula pay run", "why": "per-client, per-hour, mileage and backup pay checked against what was paid, with every difference counted", "where": "Doula Pay Run"},
    {"name": "Owner own-client load", "why": "your hours as a doula and as a manager against your draw, with the hours to hand over", "where": "Owner Own-Client Load"},
    {"name": "Losing split finder", "why": "the doula whose split loses money and the closed-form share that breaks even", "where": "Losing Split Finder"},
    {"name": "Profit by doula", "why": "revenue, pay, mileage and margin per doula and per hour worked", "where": "Profit by Doula"},
    {"name": "Pay run statement", "why": "one row per person and month with the check against what was paid and whether the statement was sent on time", "where": "Pay Run Statement"},
    {"name": "Agency margin by client", "why": "revenue, doula pay, mileage and overhead for every client, so the margin is never a guess", "where": "Agency Margin by Client"},
    {"name": "Backup stipend and call-out run", "why": "rota weeks and call-outs turned into what each backup doula is due", "where": "Backup Pay Run"}]
competitors = [
    {"what": "free client-tracker templates", "lacks": "list clients and dates but never work out what each doula is paid or what the agency keeps"},
    {"what": "subscription practice-management software", "lacks": "charge every month and hide the split and pay run logic behind reports you cannot change"},
    {"what": "generic payroll spreadsheets", "lacks": "know nothing of per-client pay, agency shares, backup call-outs or mileage per area"},
    {"what": "generic invoice spreadsheets", "lacks": "bill clients but never show the margin per client after doula pay, mileage and overhead"},
    {"what": "single-sheet on-call calendars", "lacks": "show who is free but not the places left against each doula's cap or the best doula to assign"}]
guide = [
    'Open Start and type your business name and your own targets in the yellow cells: the margin per client you want, the overhead per client, the backup pay and the mileage rates.',
    'Check Doulas, Packages and Team. They hold the agency share and hourly pay of each doula, the birth part of each package and the caps the other sheets read. A solo doula keeps one row and no split.',
    'Write each pay line in Pay Lines: month, doula, client, basis, hours, miles, gross, agency share, pay due and, once paid, the paid amount and date. The difference and the differs check fill in.',
    'Read Pay Run Statement before every pay run. It totals per-client pay, per-hour pay, mileage and backup pay for each person and month and checks them against what was paid.',
    'Open Paid vs Due Differences to see the lines paid differently and the adjustment to make.',
    'Agency Margin by Client and Margin by Doula show what the agency keeps after doula pay, mileage and overhead. A negative margin means the split loses money.',
    'Use Capacity by Doula and Hours by Doula to see places left, on-call days and pay per hour worked. Backup Pay by Month checks stipends against the Backup Rota.',
    'Test a new share in Split Proposals and Agency Split Proposal, and read Owner Load by Month to see what your own hours are worth.',
    f'Use the {len(tools)} tools to price a package, assign a doula, test a split, run the pay run, check mileage and decide whether to add a doula.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Agency Pay Dashboard and the charts every month. Check your local rules about contractor terms, records and tax with your adviser.']
listing = {"title": "Doula Business Agency Splits, Pay Runs and Capacity Excel Template: Contractor Pay Run, Margin per Client, Backup Pay",
    "headline": "Know what every doula is paid and what the agency keeps",
    "tags": ["doula", "doula business", "doula agency", "pay run", "agency split", "contractor pay", "margin per client", "backup doula", "mileage log", "excel template", "capacity planning", "business tracker", "doula pay"],
    "description": ("Run the money side of a doula agency in one Excel workbook. Built for an owner-doula who also takes clients, contracted doulas paid per client or per hour with an agency split, backup doulas on a shared rota and a part-time admin, and just as useful for a solo doula who wants to see pay per hour worked and their own load.\n\n"
        "Pay Lines records what each doula is due and what was paid, with the difference and the lines paid differently. Pay Run Statement totals per-client pay, per-hour pay, mileage and backup pay for every person and month and checks them against the paid amount. Agency Margin by Client shows revenue, doula pay, mileage and overhead for each client, and Margin by Doula shows which split leaves the agency out of pocket.\n\n"
        f"Capacity by Doula shows clients, on-call days and places left against each doula's cap for the next months, Hours by Doula shows pay per hour worked, Split Proposals tests a new agency share, Backup Pay by Month checks stipends against the rota and Owner Load by Month shows what your own hours are worth. {len(tools)} tools answer the weekly questions: a pay calculator, capacity, split proposal, pay run, owner load, losing split finder, profit by doula, per-client against per-hour pay, backup pay run, pay forecast, mileage check, new doula case, overhead check, earnings per hour, package comparison, owner against contracted margin, year-end summary and a doula scorecard. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to doulas, backup doulas, the admin, the owner-doula and the accountant.\n\n"
        "This is part six of the Doula Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Clients appear by name, area and dates only, with no medical detail. It helps you keep track of hours, dates, money and capacity and does not promise any result. Check your local rules about contractor terms, records, insurance and tax."),
    "features": ["Pay run statement checked against what was paid", "Agency margin by client and by doula", "Losing split finder with the break-even share", "Split proposals with the effect on your margin", "Capacity by doula with the best doula to assign",
                 "Backup stipend and call-out pay run", "Pay per hour worked for every doula", "Owner load as a doula and a manager", f"{len(tools)} decision tools with a verdict", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
def _cut(x, n):
    if len(x) <= n: return x
    y = x[:n - 1]
    for sep in ('. ', '; ', ': ', ', '):
        i = y.rfind(sep)
        if i > n * 0.55: return y[:i].rstrip() + '.'
    return y[:y.rfind(' ')].rstrip(' ,;:') + '.'
for _t in tables + tools:
    _t['hint'] = _cut(_t['hint'], 200); _t['title'] = _cut(_t['title'], 60).rstrip('.')
for _f in forms: _f['title'] = _cut(_f['title'], 50).rstrip('.')
s = spec(id=f'{SUITE}-p6', slug='doula-business-payruns', profession='Doula Business', name='Doulas, Agency Splits and Pay Runs',
         tagline='Know what every doula is paid and what the agency keeps', price_usd=29,
         colors={"primary": "#4A3F6B", "accent": "#E8A87C"}, settings=settings, lists=get_lists(), tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 6, "of": 8, "focus": "Doulas, agency splits and pay runs"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'du6.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'lists', len(s['lists']))
