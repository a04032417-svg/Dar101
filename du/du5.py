"""Doula business suite - part 5: Visits, Hours, Mileage and Births."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from du5_lists import *
from du5_tables import settings, tables
from du5_tools import tools

SUITE = 'fx-20261115-doula-business'
NOTE = "Sample wording: adapt it to your own business and check your local rules."
YES = '{list:yesno.yes}'
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
PRE = tok('vkind', 'Prenatal visit'); PPV = tok('vkind', 'Postpartum visit'); NIGHT = tok('vkind', 'Night shift'); DEB = tok('vkind', 'Debrief visit')
OVER, WITHIN, NOH = ca('Over plan'), ca('Within plan'), ca('No hours logged')

# ------------------------------------------------------------------ forms (12)
VL = {"from": "visits", "match": "visits.client", "columns": ["date", "kind", "hours", "miles", "doula"], "max": 12}
forms = [
    FORM('visit_sheet', 'Visit Log Sheet', 'Visit log with the hours of the client and the doula', 'visits.visit_id', F(
        ('Date', 'visits.date'), ('Start time', 'visits.time'), ('Client', 'visits.client'), ('Doula', 'visits.doula'), ('Kind of visit', 'visits.kind'), ('Hours', 'visits.hours'), ('Miles', 'visits.miles'), ('Area', 'visits.area'),
        ('Mileage cost', 'visits.mileage_cost'), ('Week starting', 'visits.week'), ('Below the minimum', 'visits.short'), ('Log complete', 'visits.complete')) + [
        FF('Visit hours of this client so far', 'SUMIFS({range:visits.hours},{range:visits.client},%s)' % LK('visits', 'visit_id', 'client'), 'num'),
        FF('Visits of this doula in the same week', 'COUNTIFS({range:visits.doula},%s,{range:visits.week},%s)' % (LK('visits', 'visit_id', 'doula'), LK('visits', 'visit_id', 'week')), 'int'),
        FF('Hours of this doula in the same week', 'SUMIFS({range:visits.hours},{range:visits.doula},%s,{range:visits.week},%s)' % (LK('visits', 'visit_id', 'doula'), LK('visits', 'visit_id', 'week')), 'num')]),
    FORM('prenatal_sheet', 'Prenatal Visit Sheet', 'Prenatal visits planned, done and left for a client', 'clients.client', F(
        ('Client ID', 'clients.client_id'), ('Phone', 'clients.phone'), ('Area', 'clients.area'), ('Package', 'clients.package'), ('Signed on', 'clients.signed_on'), ('Estimated due date', 'clients.edd'), ('On-call start', 'clients.oncall_start'),
        ('Doula', 'clients.doula'), ('Prenatal visits planned', 'clients.prenatal_plan'), ('Prenatal visits done', 'clients.prenatal_n'), ('Prenatal visits left', 'clients.prenatal_left'), ('Days to the on-call start', 'clients.days_to_oncall')) + [
        FF('Prenatal hours so far', 'SUMIFS({range:visits.hours},{range:visits.client},{pick},{range:visits.kind},%s)' % PRE, 'num'),
        FF('Latest day for the last prenatal visit', '%s-7' % LK('clients', 'client', 'oncall_start'), 'date')], VL),
    FORM('postpartum_sheet', 'Postpartum Visit Sheet', 'Postpartum hours used and left for a client', 'clients.client', F(
        ('Client ID', 'clients.client_id'), ('Package', 'clients.package'), ('Doula', 'clients.doula'), ('Status', 'clients.status'), ('Visits so far', 'clients.visits_n'), ('Postpartum hours so far', 'clients.pp_hours'),
        ('Minimum booking, hours', 'clients.min_hours'), ('Last visit', 'clients.last_visit')) + [
        FF('Postpartum hours in the package', 'IFERROR(INDEX({range:packages.postpartum_hours},MATCH(%s,{range:packages.package},0)),0)' % LK('clients', 'client', 'package'), 'num'),
        FF('Hours left in the package', 'MAX(0,IFERROR(INDEX({range:packages.postpartum_hours},MATCH(%s,{range:packages.package},0)),0)-%s)' % (LK('clients', 'client', 'package'), LK('clients', 'client', 'pp_hours')), 'num'),
        FF('Rate for extra hours', '{set:extra_hour_rate}', 'money')], VL),
    FORM('night_sheet', 'Night Shift Sheet', 'Night shifts and night calls of a doula', 'team.name', F(
        ('Role', 'team.role'), ('Phone', 'team.phone'), ('Hours this week', 'team.hours_week'), ('Weekly cap', 'team.cap'), ('Night calls and shifts, 30 days', 'team.nights_30'), ('Weekly hours, last 4 weeks', 'team.hours_4wk')) + [
        FF('Night shifts, last 90 days', 'COUNTIFS({range:visits.doula},{pick},{range:visits.kind},%s,{range:visits.date},">="&({today}-90))' % NIGHT, 'int'),
        FF('Night calls, last 90 days', 'COUNTIFS({range:births.doula},{pick},{range:births.night_call},1,{range:births.date},">="&({today}-90))', 'int'),
        FF('Night shift hours, 12 months', 'SUMIFS({range:visits.hours},{range:visits.doula},{pick},{range:visits.kind},%s,{range:visits.date},">="&EDATE({today},-12))' % NIGHT, 'num'),
        FF('Limit per 30 days', '{set:night_max}', 'int')]),
    FORM('birth_sheet', 'Birth Attended Log Sheet', 'Birth attended with call, arrival and leave times', 'births.birth_id', F(
        ('Date', 'births.date'), ('Client', 'births.client'), ('Doula who attended', 'births.doula'), ('Assigned doula', 'births.assigned'), ('Backup used', 'births.backup_used'), ('Call time', 'births.call_time'),
        ('Arrival time', 'births.arrive_time'), ('Leave time', 'births.leave_time'), ('Hours', 'births.hours'), ('Miles', 'births.miles'), ('Area', 'births.area'), ('On-call day', 'births.on_call_day'),
        ('Minutes to arrive', 'births.arrive_min'), ('Planned birth hours', 'births.plan_hours')) + [
        FF('Hours over or under the plan', '%s-%s' % (LK('births', 'birth_id', 'hours'), LK('births', 'birth_id', 'plan_hours')), 'num'),
        FF('Mileage cost', 'ROUND(%s*SUMIFS({range:areas.mileage_rate},{range:areas.area},%s,{range:areas.in_use},1),2)' % (LK('births', 'birth_id', 'miles'), LK('births', 'birth_id', 'area')), 'money')]),
    FORM('oncall_sheet', 'On-call Contact Log Sheet', 'Contact hours inside an on-call window', 'oncall.window_id', F(
        ('Client', 'oncall.client'), ('Doula', 'oncall.doula'), ('On-call start', 'oncall.oncall_start'), ('On-call end', 'oncall.oncall_end'), ('Attended on', 'oncall.attended_on'), ('Contact hours', 'oncall.contact_hours')) + [
        FF('Days in the window', '%s-%s+1' % (LK('oncall', 'window_id', 'oncall_end'), LK('oncall', 'window_id', 'oncall_start')), 'int'),
        FF('Contact hours per day', 'IFERROR(%s/(%s-%s+1),0)' % (LK('oncall', 'window_id', 'contact_hours'), LK('oncall', 'window_id', 'oncall_end'), LK('oncall', 'window_id', 'oncall_start')), 'num'),
        FF('Days from the start to the birth', '%s-%s' % (LK('oncall', 'window_id', 'attended_on'), LK('oncall', 'window_id', 'oncall_start')), 'int'),
        FF('Windows of this doula', 'COUNTIFS({range:oncall.doula},%s)' % LK('oncall', 'window_id', 'doula'), 'int')]),
    FORM('mileage_sheet', 'Mileage Log Sheet', 'Mileage of a client against the package price', 'mil_client.client', F(
        ('Package', 'mil_client.package'), ('Trips', 'mil_client.trips'), ('Miles', 'mil_client.miles'), ('Mileage cost', 'mil_client.mileage_cost'), ('List price', 'mil_client.price'), ('Share of the price', 'mil_client.share'), ('Mileage check', 'mil_client.flag')) + [
        FF('Mileage cost per trip', 'IFERROR(%s/%s,0)' % (LK('mil_client', 'client', 'mileage_cost'), LK('mil_client', 'client', 'trips')), 'money'),
        FF('Mileage share you accept', '{set:mileage_share_max}', 'pct'),
        FF('Cost above the share you accept', 'MAX(0,%s-%s*{set:mileage_share_max})' % (LK('mil_client', 'client', 'mileage_cost'), LK('mil_client', 'client', 'price')), 'money')]),
    FORM('pack_use_sheet', 'Hour Pack Use Sheet', 'Hours used and left on an hour pack', 'ledger.pack_id', F(
        ('Client', 'ledger.client'), ('Doula', 'ledger.doula'), ('Package', 'ledger.package'), ('Hours bought', 'ledger.hours_bought'), ('Hours used', 'ledger.hours_used'), ('Hours left', 'ledger.hours_left'), ('Expires on', 'ledger.expires_on'),
        ('Days to expiry', 'ledger.days_to_expiry'), ('Extra hours', 'ledger.extra_hours'), ('Pack check', 'ledger.pack_flag'), ('Hours a week to finish', 'ledger.pace_week')) + [
        FF('Share of the pack used', 'IFERROR(%s/%s,0)' % (LK('ledger', 'pack_id', 'used_in_pack'), LK('ledger', 'pack_id', 'hours_bought')), 'pct'),
        FF('Value of the hours left', LK('ledger', 'pack_id', 'value_left'), 'money')]),
    FORM('adjust_sheet', 'Hours Adjustment Sheet', 'Hours used, extra hours and the invoice for one pack', 'packs.pack_id', F(
        ('Client', 'packs.client'), ('Doula', 'packs.doula'), ('Package', 'packs.package'), ('Hours bought', 'packs.hours_bought'), ('Hours used', 'packs.hours_used'), ('Extra hours', 'packs.extra_hours'), ('Price', 'packs.price'),
        ('Bought on', 'packs.bought_on'), ('Expires on', 'packs.expires_on'), ('Price per hour', 'packs.price_hour'), ('Extra hours amount', 'packs.extra_amount')) + [
        FF('Hours used after one more minimum visit', '%s+{set:min_booking_hours}' % LK('packs', 'pack_id', 'hours_used'), 'num'),
        FF('Extra hours after one more minimum visit', 'MAX(0,%s+{set:min_booking_hours}-%s)' % (LK('packs', 'pack_id', 'hours_used'), LK('packs', 'pack_id', 'hours_bought')), 'num')]),
    FORM('debrief_sheet', 'Debrief Visit Sheet', 'Debrief visit after a birth attended', 'clients.client', F(
        ('Client ID', 'clients.client_id'), ('Phone', 'clients.phone'), ('Package', 'clients.package'), ('Doula', 'clients.doula'), ('Status', 'clients.status'), ('Last visit', 'clients.last_visit'), ('Visits so far', 'clients.visits_n'),
        ('Postpartum hours so far', 'clients.pp_hours')) + [
        FF('Date of the birth attended', 'IFERROR(INDEX({range:births.date},MATCH({pick},{range:births.client},0)),"")', 'date'),
        FF('Debrief visits so far', 'COUNTIFS({range:visits.client},{pick},{range:visits.kind},%s)' % DEB, 'int'),
        FF('Days from the birth to the last visit', 'IFERROR(%s-INDEX({range:births.date},MATCH({pick},{range:births.client},0)),"")' % LK('clients', 'client', 'last_visit'), 'int')], VL),
    FORM('week_sheet', 'Weekly Hours Sheet', 'Team hours for one week against the cap', 'wk_all.week', F(
        ('Week number', 'wk_all.week_no'), ('Visits', 'wk_all.visits'), ('Visit hours', 'wk_all.visit_hours'), ('Birth hours', 'wk_all.birth_hours'), ('Total hours', 'wk_all.total_hours'), ('Births', 'wk_all.births')) + [
        FF('Average hours per visit', 'IFERROR(%s/%s,0)' % (LK('wk_all', 'week', 'visit_hours'), LK('wk_all', 'week', 'visits')), 'num'),
        FF('Team cap for a week', 'SUM({range:team.cap})', 'num'),
        FF('Share of the team cap', 'IFERROR(%s/SUM({range:team.cap}),0)' % LK('wk_all', 'week', 'total_hours'), 'pct')],
        {"from": "visits", "match": "visits.week", "columns": ["date", "client", "doula", "kind", "hours"], "max": 20}),
    FORM('rest_sheet', 'Rest Day Sheet', 'Rest days between two births of a doula', 'rest.birth_id', F(
        ('Doula', 'rest.doula'), ('Birth date', 'rest.date'), ('Previous birth', 'rest.previous_birth'), ('Rest days between', 'rest.rest_days'), ('Rest check', 'rest.flag'), ('Minimum rest days', 'rest.min_rest')) + [
        FF('Days short of the minimum', 'MAX(0,%s-%s)' % (LK('rest', 'birth_id', 'min_rest'), LK('rest', 'birth_id', 'rest_days')), 'int'),
        FF('Births of this doula, 12 months', 'COUNTIFS({range:births.doula},%s,{range:births.date},">="&EDATE({today},-12))' % LK('rest', 'birth_id', 'doula'), 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('visit_summary_doc', 'Visit Summary', 'Visit summary for a client (dates and hours only)', 'clients.client', [
        'Visit summary of {set:company}, dated {today}. Client: {col:clients.client}, client ID {col:clients.client_id}. Package: {col:clients.package}. Doula: {col:clients.doula}.',
        'Visits so far: {col:clients.visits_n}. Visit hours so far: {col:clients.visit_hours}. Prenatal visits done: {col:clients.prenatal_n} of {col:clients.prenatal_plan} planned. Postpartum hours so far: {col:clients.pp_hours}. Last visit: {col:clients.last_visit}.',
        'The minimum booking for a postpartum visit is {col:clients.min_hours} hours. This page lists dates, hours and visit counts only.', 'Please tell us about any difference between this page and your own notes.'], ['Doula', 'Client'], NOTE),
    DOC('pack_statement_doc', 'Hour Pack Statement', 'Hour pack statement: bought, used, left and expiry', 'ledger.pack_id', [
        'Hour pack statement of {set:company}, dated {today}. Pack {col:ledger.pack_id} for {col:ledger.client}. Package: {col:ledger.package}. Doula: {col:ledger.doula}.',
        'Hours bought: {col:ledger.hours_bought}. Hours used: {col:ledger.hours_used}. Hours left: {col:ledger.hours_left}. The pack expires on {col:ledger.expires_on}, which is {col:ledger.days_to_expiry} days from today.',
        'Extra hours beyond the pack: {col:ledger.extra_hours}. Amount for the extra hours: {col:ledger.extra_amount}. Value of the hours left: {col:ledger.value_left}. Pack check: {col:ledger.pack_flag}.',
        'Hours not used by the expiry date lapse. Please book your visits early so that the hours are used.'], ['Doula', 'Client'], NOTE),
    DOC('phase_report_doc', 'Hours by Phase Report', 'Hours by phase for a client against the package plan', 'phase.client', [
        'Hours by phase of {set:company}, dated {today}. Client: {col:phase.client}. Package: {col:phase.package}.',
        'Prenatal hours: {col:phase.prenatal_hours}. On-call contact hours: {col:phase.oncall_hours}. Birth hours: {col:phase.birth_hours}. Postpartum hours: {col:phase.postpartum_hours}. Total hours: {col:phase.total_hours}.',
        'Planned hours of the package: {col:phase.plan_hours}. Hours over plan: {col:phase.excess_hours}. Share over plan: {col:phase.over_share}. Plan check: {col:phase.flag}.',
        'The agency accepts a share over plan of up to the value in Settings. Review the package price when many clients run over plan.'], ['Owner-doula'], NOTE),
    DOC('mileage_doc', 'Mileage Statement', 'Mileage statement for a doula', 'team.name', [
        'Mileage statement of {set:company}, dated {today}. Doula: {col:team.name}. Role: {col:team.role}.',
        'Miles this month: {col:team.miles_month}. Mileage cost this month: {col:team.cost_month}. Miles in the last 12 months: {col:team.miles_12}. Mileage cost in the last 12 months: {col:team.cost_12}.',
        'Mileage is counted from the miles written in the Visit Log and the Birth Log at the rate of the area. Please check your log and tell us about any trip that is missing.', 'Visit logs missing miles in the last 7 days: {col:team.missing_logs}.'], ['Doula', 'Owner-doula'], NOTE),
    DOC('weekly_report_doc', 'Weekly Hours Report', 'Weekly hours report for a doula', 'team.name', [
        'Weekly hours report of {set:company}, dated {today}. Doula: {col:team.name}.',
        'Hours this week: {col:team.hours_week}. Weekly cap: {col:team.cap}. Average weekly hours in the last 4 weeks: {col:team.hours_4wk}. Weeks over the cap in the last 12 weeks: {col:team.weeks_over_12}.',
        'Night calls and night shifts in the last 30 days: {col:team.nights_30}. A rest week is advised after {set:weeks_over_warn} weeks over the cap in a row.', 'Please tell the owner-doula if your hours or rest need to change.'], ['Doula', 'Owner-doula'], NOTE),
    DOC('births_report_doc', 'Births Attended Report', 'Births attended report for a month (counts and hours only)', 'births_month.month', [
        'Births attended report of {set:company}, dated {today}. Month: {col:births_month.month}.',
        'Births attended: {col:births_month.births}. Hours attended: {col:births_month.hours}. Average hours per birth: {col:births_month.avg_hours}. Births with a backup doula: {col:births_month.backup_births}. Night calls: {col:births_month.night_calls}.',
        'Births in the quarter: {col:births_month.births_quarter} against a maximum of {col:births_month.quarter_max}.', 'This report holds counts and hours only, with no detail of any birth.'], ['Owner-doula'], NOTE),
    DOC('extra_invoice_doc', 'Invoice Extra Hours', 'Invoice for extra postpartum hours', 'packs.pack_id', [
        'Invoice of {set:company}, dated {today}. Client: {col:packs.client}. Pack {col:packs.pack_id}, package {col:packs.package}. Doula: {col:packs.doula}.',
        'Hours bought: {col:packs.hours_bought}. Hours used: {col:packs.hours_used}. Extra hours beyond the pack: {col:packs.extra_hours}. Rate for extra hours: {set:extra_hour_rate} an hour.',
        'Amount due for the extra hours: {col:packs.extra_amount}. Prices are before any tax. The pack was bought on {col:packs.bought_on} and expires on {col:packs.expires_on}.', 'Please pay by the date agreed in your contract. Check the contract terms for late payment.'], ['Owner-doula', 'Client'], NOTE),
    DOC('prenatal_schedule_doc', 'Prenatal Visit Schedule', 'Prenatal visit schedule for a client', 'clients.client', [
        'Prenatal visit schedule of {set:company}, dated {today}. Client: {col:clients.client}. Package: {col:clients.package}. Doula: {col:clients.doula}.',
        'Prenatal visits planned: {col:clients.prenatal_plan}. Done: {col:clients.prenatal_n}. Left: {col:clients.prenatal_left}. The estimated due date is {col:clients.edd} and the on-call window starts on {col:clients.oncall_start}.',
        'The next visit is on {col:clients.next_visit} at {col:clients.visit_time}. Please book the remaining visits before the on-call window starts.', 'The estimated due date is a date you give us. We use it only to plan the on-call window.'], ['Doula', 'Client'], NOTE),
    DOC('expiry_notice_doc', 'Pack Expiry Notice', 'Notice that an hour pack is ending', 'ledger.pack_id', [
        'Pack expiry notice of {set:company}, dated {today}. Dear {col:ledger.client}, your hour pack {col:ledger.pack_id} ({col:ledger.package}) ends on {col:ledger.expires_on}.',
        'You have used {col:ledger.hours_used} of {col:ledger.hours_hours_placeholder} hours.'.replace('{col:ledger.hours_hours_placeholder}', '{col:ledger.hours_bought}') + ' Hours left: {col:ledger.hours_left}. To use them you would need about {col:ledger.pace_week} hours a week until the end date.',
        'Hours that are not used by the end date lapse. Please call {col:ledger.owner_phone} to book your next visits.', 'We are glad to help you find times that suit you.'], ['Owner-doula', 'Client'], NOTE),
    DOC('monthly_summary_doc', 'Monthly Hours Summary', 'Monthly hours summary for the owner-doula', 'mil_month.month', [
        'Monthly hours summary of {set:company}, dated {today}. Month: {col:mil_month.month}.',
        'Visits: {col:mil_month.visits}. Births attended: {col:mil_month.births}. Visit hours: {col:mil_month.visit_hours}. Birth hours: {col:mil_month.birth_hours}.',
        'Miles: {col:mil_month.miles}. Mileage cost: {col:mil_month.mileage_cost}. Cost per trip: {col:mil_month.cost_per_trip}. Postpartum visits below the minimum: {col:mil_month.short_visits}.',
        'Extra hours still to invoice up to this month: {col:mil_month.to_invoice}. Packs ending in this month with extra hours: {col:mil_month.extra_hours} hours.'], ['Owner-doula'], NOTE),
    DOC('rest_plan_doc', 'Rest Days Plan', 'Rest days plan after a birth attended', 'rest.birth_id', [
        'Rest days plan of {set:company}, dated {today}. Doula: {col:rest.doula}. Birth {col:rest.birth_id} on {col:rest.date}.',
        'The previous birth of this doula was on {col:rest.previous_birth}. Rest days between the two births: {col:rest.rest_days}. The agreed minimum is {col:rest.min_rest} days. Rest check: {col:rest.flag}.',
        'Please keep the days after a birth free of new visits where you can. Tell the owner-doula if you need a backup doula for the next window.', 'This plan holds dates and days only.'], ['Doula', 'Owner-doula'], NOTE),
    DOC('yearly_summary_doc', 'Yearly Hours Summary', 'Yearly hours summary for a doula', 'team.name', [
        'Yearly hours summary of {set:company}, dated {today}. Doula: {col:team.name}.',
        'Visit hours in the last 12 months: {col:team.yr_visit_hours}. Birth hours in the last 12 months: {col:team.yr_birth_hours}. Capacity at the weekly cap: {col:team.yr_capacity} hours a year. Share of capacity used: {col:team.yr_share}.',
        'Miles in the last 12 months: {col:team.miles_12}. Mileage cost: {col:team.cost_12}.', 'Use this page for the yearly review of hours, rest and travel.'], ['Doula', 'Owner-doula'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('visit_day', 'Visit Day Steps', 'visits', 'visits.date', [('Confirm the visit with the client the day before', -1), ('Check the area and the miles to drive', -1), ('Start on time and note the start time', 0), ('Write the hours and miles in the Visit Log', 0), ('Book the next visit with the client', 0), ('Check that the log is complete', 1)]),
    CHK('prenatal_visit', 'Prenatal Visit Steps', 'clients', 'clients.oncall_start', [('Book the next prenatal visit', -49), ('Confirm the visit the day before', -43), ('Hold the visit and log the hours and miles', -42), ('Check the visits left in the package', -41), ('Book the last prenatal visit', -21), ('Confirm the on-call start with the client', -14), ('Check the backup doula is named', -7)]),
    CHK('postpartum_shift', 'Postpartum Shift Steps', 'visits', 'visits.date', [('Confirm the shift time and the minimum booking', -1), ('Start the shift and note the start time', 0), ('Write the end time, hours and miles', 0), ('Tell the client the hours used so far', 0), ('Update the Hour Pack Ledger', 1), ('Book the next shift', 1)]),
    CHK('night_shift', 'Night Shift Steps', 'visits', 'visits.date', [('Confirm the night shift with the client', -2), ('Check that the doula has rested', -1), ('Start the shift and note the start time', 0), ('Write the hours and miles the next morning', 1), ('Count the night shifts of the doula this month', 1), ('Rotate the next night shift if the limit is reached', 2)]),
    CHK('after_birth', 'After a Birth Attended Steps', 'births', 'births.date', [('Write the call, arrival and leave times', 0), ('Write the hours and miles', 0), ('Tell the owner-doula the birth is attended', 0), ('Check the rest days before the next window', 1), ('Book the first postpartum or debrief visit', 3), ('Ask for a review after the debrief visit', 14)]),
    CHK('weekly_check', 'Weekly Hours Check Steps', 'wk_all', 'wk_all.week', [('Check that every visit of the week is logged', 7), ('Count the hours of each doula against the cap', 7), ('Plan a rest week after weeks over the cap in a row', 8), ('Check the packs ending this month', 8), ('Send the weekly hours to each doula', 9)]),
    CHK('month_close', 'Month-End Hours Close Steps', 'mil_month', 'mil_month.month', [('Check that every visit and birth of the month is logged', 28), ('Fix the visits with no miles', 29), ('Total the hours and miles', 30), ('Invoice the extra hours', 31), ('Send the mileage totals to the accountant', 33), ('Note the births of the quarter', 33)]),
    CHK('mileage_check', 'Mileage Log Check Steps', 'mil_month', 'mil_month.month', [('Ask each doula to check their miles', 28), ('Compare the miles with the area distances', 29), ('Check the mileage rate in Areas', 30), ('Check the clients with a high mileage share', 31), ('Decide on a travel fee for far clients', 35)]),
    CHK('pack_expiry', 'Pack Expiry Review Steps', 'packs', 'packs.expires_on', [('Check the hours left on the pack', -60), ('Message the client about the hours left', -45), ('Book visits for the hours left', -30), ('Remind the client again', -14), ('Check the extra hours and invoice them', 0), ('Close the pack in the ledger', 7)]),
    CHK('over_plan', 'Hours Over Plan Review Steps', 'clients', 'clients.edd', [('List the clients over plan in Hours by Phase', 45), ('Find the phase that took the extra hours', 46), ('Check that extra hours were agreed with the client', 47), ('Invoice extra hours where the contract allows', 50), ('Review the package plan hours', 60), ('Review the package price', 60)]),
    CHK('rest_after_birth', 'Rest Days After a Birth Steps', 'births', 'births.date', [('Keep the doula free of new visits', 1), ('Check the next on-call window of the doula', 1), ('Name a backup doula if the rest is short', 2), ('Check the weekly hours after the birth', 7), ('Record the rest days in Rest Days Between Births', 7)]),
    CHK('yearly_review', 'Yearly Hours Review Steps', 'births_month', 'births_month.month', [('Total the hours of each doula for the year', 30), ('Compare the hours with the weekly cap times 52', 31), ('Review the births with too little rest', 32), ('Review the miles and the mileage cost', 33), ('Review the packages with the most extra hours', 35), ('Set the cap and the minimum booking for next year', 40)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('c_next', 'Client: your next visit', 'clients', 'clients.phone', 'Hello {client}, your next visit with {doula} is on {next_visit} at {visit_time}. {company}'),
    M('c_remind', 'Client: reminder, your visit is tomorrow', 'clients', 'clients.phone', 'Hello {client}, a reminder: your visit with {doula} is tomorrow, {next_visit}, at {visit_time}. {company}'),
    M('c_move', 'Client: your visit needs to move', 'clients', 'clients.phone', 'Hello {client}, {doula} needs to move your visit of {next_visit}. May we offer you two other times? {company}'),
    M('c_prenatal', 'Client: prenatal visit is due', 'clients', 'clients.phone', 'Hello {client}, your prenatal visit {prenatal_no} is due before {oncall_start}. Which day suits you? {company}'),
    M('c_thanks', 'Client: thank you, your hours so far', 'clients', 'clients.phone', 'Hello {client}, thank you for today. Your visits so far add up to {visit_hours} hours. {company}'),
    M('c_night', 'Client: your night shift is booked', 'clients', 'clients.phone', 'Hello {client}, your night shift with {doula} is booked for {next_visit} at {visit_time}. {company}'),
    M('c_min', 'Client: the minimum booking', 'clients', 'clients.phone', 'Hello {client}, the minimum booking for a postpartum visit is {min_hours} hours. Please tell us the hours you want. {company}'),
    M('c_debrief', 'Client: your debrief visit is booked', 'clients', 'clients.phone', 'Hello {client}, your debrief visit with {doula} is booked for {next_visit} at {visit_time}. {company}'),
    M('c_total', 'Client: your visits so far', 'clients', 'clients.phone', 'Hello {client}, you have had {visits_n} visits so far, {visit_hours} hours in all, {pp_hours} of them after the birth. {company}'),
    M('d_log', 'Doula: please log the visit hours', 'clients', 'clients.doula_phone', 'Hello {doula}, please log your visit hours and miles for {client}. Thank you. {company}'),
    M('l_used', 'Client: hours used of your hour pack', 'ledger', 'ledger.phone', 'Hello {client}, you have used {hours_used} of {hours_bought} hours of your hour pack. {company}'),
    M('l_left', 'Client: hours left on your hour pack', 'ledger', 'ledger.phone', 'Hello {client}, your hour pack has {hours_left} hours left. Shall we book the next visit? {company}'),
    M('l_ends', 'Client: your hour pack ends soon', 'ledger', 'ledger.phone', 'Hello {client}, your hour pack ends on {expires_on} with {hours_left} hours left. Would you like to book them? {company}'),
    M('l_ended', 'Client: your hour pack ended', 'ledger', 'ledger.phone', 'Hello {client}, your hour pack ended on {expires_on} with {hours_left} hours unused. {company}'),
    M('l_extra', 'Client: extra hours invoiced', 'ledger', 'ledger.phone', 'Hello {client}, your extra hours of {extra_hours} are invoiced at {extra_amount}. {company}'),
    M('o_pack', 'Owner: a pack ends with hours unused', 'ledger', 'ledger.owner_phone', 'Hello, the pack of {client} ends on {expires_on} with {hours_left} hours unused. Pack check: {pack_flag}. {company}'),
    M('d_left', 'Doula: hours still to book', 'ledger', 'ledger.doula_phone', 'Hello {doula}, {client} still has {hours_left} hours to book before {expires_on}. {company}'),
    M('a_extra', 'Admin: extra hours to invoice', 'ledger', 'ledger.admin_phone', 'Hello, please invoice the extra hours of {client}: {extra_hours} hours, {extra_amount}. {company}'),
    M('d_birth', 'Doula: birth attended log needs times', 'births', 'births.doula_phone', 'Hello {doula}, your birth attended log for {client} on {date} needs the call, arrival and leave times. {company}'),
    M('b_call', 'Backup doula: call-out log needs times', 'births', 'births.doula_phone', 'Hello {doula}, your call-out log for {client} on {date} needs the times of the call and the arrival. {company}'),
    M('o_over', 'Owner: a client is over plan hours', 'phase', 'phase.owner_phone', 'Hello, {client} is over plan by {over_share}: {total_hours} hours against {plan_hours} for {package}. {company}'),
    M('o_cap', 'Owner: a doula is over the weekly cap', 'wk_doula', 'wk_doula.owner_phone', 'Hello, {doula} is over the weekly hours cap for {weeks_over} weeks in a row: {total_hours} hours against {cap}. {company}'),
    M('d_week', 'Doula: your weekly hours', 'wk_doula', 'wk_doula.doula_phone', 'Hello {doula}, your hours for the week of {week} are {total_hours} against a cap of {cap}. {company}'),
    M('o_rest', 'Owner: too few rest days', 'rest', 'rest.owner_phone', 'Hello, {doula} had only {rest_days} rest days before the birth on {date}. The minimum is {min_rest}. {company}'),
    M('d_rest', 'Doula: your rest days', 'rest', 'rest.doula_phone', 'Hello {doula}, you had {rest_days} rest days before the birth on {date}. The agreed minimum is {min_rest}. {company}'),
    M('o_mile', 'Owner: mileage this month', 'mil_month', 'mil_month.owner_phone', 'Hello, mileage for {month} is {mileage_cost} for {miles} miles and {trips} trips. {company}'),
    M('o_extra', 'Owner: extra hours to invoice', 'mil_month', 'mil_month.owner_phone', 'Hello, extra hours still to invoice up to {month} come to {to_invoice}. {company}'),
    M('o_short', 'Owner: visits below the minimum', 'mil_month', 'mil_month.owner_phone', 'Hello, postpartum visits shorter than the minimum in {month} are {short_visits}. {company}'),
    M('x_mile', 'Accountant: mileage totals', 'mil_month', 'mil_month.accountant_phone', 'Hello, the mileage totals for {month} are {miles} miles and {mileage_cost}. {company}'),
    M('o_quarter', 'Owner: births attended this quarter', 'births_month', 'births_month.owner_phone', 'Hello, births attended in this quarter are {births_quarter} against a maximum of {quarter_max}. {company}'),
    M('d_mileage', 'Doula: your mileage log is ready', 'team', 'team.phone', 'Hello {name}, your mileage log for {report_month} is ready to check: {miles_month} miles so far. {company}'),
    M('d_nights', 'Doula: your night shifts this month', 'team', 'team.phone', 'Hello {name}, your night calls and night shifts in the last 30 days are {nights_30}. {company}'),
    M('a_logs', 'Admin: visit logs missing', 'team', 'team.phone', 'Hello {name}, {missing_logs} visit logs of the last 7 days have no miles. Please check them. {company}'),
    M('a_packs', 'Admin: hour packs ending this month', 'team', 'team.phone', 'Hello {name}, {packs_ending} hour packs with hours left end this month. Please check them. {company}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30), dashboard, insights
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def D(col, n): return '{range:%s},">="&({today}-%s),{range:%s},"<="&{today}' % (col, n, col)
QS = 'DATE(YEAR({today}),3*INT((MONTH({today})-1)/3)+1,1)'
TOO = ca('Too little rest')
kpis = [
    KPI('Visits this month', 'COUNTIFS({range:visits.month},%s)' % MS, 'int'),
    KPI('Visits, last 30 days', 'COUNTIFS(%s)' % D('visits.date', 30), 'int'),
    KPI('Visit hours this month', 'SUMIFS({range:visits.hours},{range:visits.month},%s)' % MS, 'num'),
    KPI('Visit hours, last 30 days', 'SUMIFS({range:visits.hours},%s)' % D('visits.date', 30), 'num'),
    KPI('Prenatal visits this month', 'COUNTIFS({range:visits.month},%s,{range:visits.kind},%s)' % (MS, PRE), 'int'),
    KPI('Postpartum visit hours this month', 'SUMIFS({range:visits.hours},{range:visits.month},%s,{range:visits.kind},%s)' % (MS, PPV), 'num'),
    KPI('Night shifts this month', 'COUNTIFS({range:visits.month},%s,{range:visits.kind},%s)' % (MS, NIGHT), 'int'),
    KPI('Average visit length, last 90 days', 'IFERROR(AVERAGEIFS({range:visits.hours},%s),0)' % D('visits.date', 90), 'num'),
    KPI('Visits below the minimum, 30 days', 'COUNTIFS(%s,{range:visits.short},1)' % D('visits.date', 30), 'int'),
    KPI('Births attended this month', 'COUNTIFS({range:births.month},%s)' % MS, 'int'),
    KPI('Births attended, last 90 days', 'COUNTIFS(%s)' % D('births.date', 90), 'int'),
    KPI('Births attended, last 12 months', 'COUNTIFS(%s)' % D('births.date', 365), 'int'),
    KPI('Births this quarter so far', 'COUNTIFS({range:births.qtr},%s)' % QS, 'int', alert={"when": "> {set:births_quarter_max}", "style": "bad"}),
    KPI('Average hours per birth, 12 months', 'IFERROR(AVERAGEIFS({range:births.hours},%s),0)' % D('births.date', 365), 'num'),
    KPI('Longest birth attended, 12 months', 'SUMPRODUCT(MAX(({range:births.date}>={today}-365)*{range:births.hours}))', 'num'),
    KPI('Births with a backup doula, 12 months', 'COUNTIFS({range:births.backup_used},%s,%s)' % (YES, D('births.date', 365)), 'int'),
    KPI('Average rest days between births', 'IFERROR(AVERAGE({range:rest.rest_days}),0)', 'num'),
    KPI('Births with too little rest, 12 months', 'COUNTIFS({range:rest.flag},%s,%s)' % (TOO, D('rest.date', 365)), 'int'),
    KPI('Clients over plan hours', 'COUNTIFS({range:phase.flag},%s)' % OVER, 'int'),
    KPI('Average hours per birth client', 'IFERROR(AVERAGEIFS({range:phase.total_hours},{range:phase.kind},%s,{range:phase.total_hours},">0"),0)' % tok('ckind', 'Birth'), 'num'),
    KPI('Average hours per postpartum client', 'IFERROR(AVERAGEIFS({range:phase.total_hours},{range:phase.kind},%s,{range:phase.total_hours},">0"),0)' % tok('ckind', 'Postpartum'), 'num'),
    KPI('Hour packs running', 'COUNTIFS({range:ledger.days_to_expiry},">=0")', 'int'),
    KPI('Unused pack hours ending in 60 days', 'SUMIFS({range:ledger.hours_left},{range:ledger.pack_flag},%s)+SUMIFS({range:ledger.hours_left},{range:ledger.pack_flag},%s)' % (ca('Ending in 30 days'), ca('Ending in 60 days')), 'num'),
    KPI('Packs ending in 30 days', 'COUNTIFS({range:ledger.pack_flag},%s)' % ca('Ending in 30 days'), 'int'),
    KPI('Extra hours to invoice', 'SUMIFS({range:ledger.extra_hours},{range:ledger.to_invoice},1)', 'num'),
    KPI('Busiest doula weekly hours, 4 weeks', 'MAX({range:wk_doula.hours_last4})', 'num'),
    KPI('Weeks over the cap, last 12 weeks', 'COUNTIFS({range:wk_doula.week},">="&({today}-84),{range:wk_doula.flag},%s)+COUNTIFS({range:wk_doula.week},">="&({today}-84),{range:wk_doula.flag},%s)' % (ca('Over cap'), ca('Over cap in a row')), 'int'),
    KPI('Miles this month', 'SUMIFS({range:mil_month.miles},{range:mil_month.month},%s)' % MS, 'num'),
    KPI('Mileage cost this month', 'SUMIFS({range:mil_month.mileage_cost},{range:mil_month.month},%s)' % MS, 'money'),
    KPI('Mileage cost per client, 12 months', 'IFERROR(SUMIFS({range:mil_month.mileage_cost},{range:mil_month.month},">="&EDATE(%s,-12),{range:mil_month.month},"<="&%s)/COUNTIFS({range:clients.edd},">"&EDATE({today},-12),{range:clients.edd},"<="&{today},{range:clients.status},"<>"&%s),0)' % (MS, MS, tok('cstatus', 'Cancelled')), 'money'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Hours Dashboard", "kpis": kpis,
    "monthly": {"title": "Visit hours, birth hours, miles and mileage cost", "date": "visits.date", "series": [
        {"label": "Visit hours", "sum": "visits.hours", "date": "visits.date"}, {"label": "Birth hours", "sum": "births.hours", "date": "births.date"},
        {"label": "Miles", "sum": "mil_month.miles", "date": "mil_month.month"}, {"label": "Mileage cost", "sum": "mil_month.mileage_cost", "date": "mil_month.month"}]},
    "breakdowns": [{"title": "Visit hours by kind", "by": "visits.kind", "value": "visits.hours", "agg": "sum"}, {"title": "Visit hours by doula", "by": "visits.doula", "value": "visits.hours", "agg": "sum"},
                   {"title": "Births attended by area", "by": "births.area", "value": "births.hours", "agg": "count"}, {"title": "Mileage cost by area", "by": "mil_doula.area", "value": "mil_doula.mileage_cost", "agg": "sum"}]}
insights = {"filters": [{"label": "Doula", "list": "doula"}, {"label": "Visit kind", "list": "vkind"}, {"label": "Area", "list": "area"}],
    "gauges": [
        {"title": "Clients within plan hours", "num": AGG('count', 'phase', where=[('flag', '=', WITHIN)]), "den": AGG('count', 'phase', where=[('flag', '<>', NOH)])},
        {"title": "Doula weeks within the hours cap", "num": AGG('count', 'wk_doula', where=[('flag', '=', ca('Within cap'))]), "den": AGG('count', 'wk_doula')},
        {"title": "Pack hours used before expiry", "num": AGG('sum', 'ledger', 'ledger.used_in_pack', where=[('expires_on', '<', '{today}')]), "den": AGG('sum', 'ledger', 'ledger.hours_bought', where=[('expires_on', '<', '{today}')])},
        {"title": "Births with enough rest days", "num": AGG('count', 'rest', where=[('flag', '=', ca('Enough rest'))]), "den": AGG('count', 'rest')},
        {"title": "Postpartum visits at the minimum length", "num": AGG('count', 'visits', where=[('kind', '=', PPV), ('short', '=', 0)]), "den": AGG('count', 'visits', where=[('kind', '=', PPV)])},
        {"title": "Visit logs complete this month", "num": AGG('count', 'visits', where=[('this_month', '=', 1), ('complete', '=', 1)]), "den": AGG('count', 'visits', where=[('this_month', '=', 1)])}],
    "charts": [
        CHART('Visit hours per month', 'column', 'month', [AGG('sum', 'visits', 'visits.hours', date='visits.date', label='Visit hours')]),
        CHART('Visits per month', 'column', 'month', [AGG('count', 'visits', date='visits.date', label='Visits')]),
        CHART('Visits by kind', 'bar', 'visits.kind', [AGG('count', 'visits', label='Visits')]),
        CHART('Visit hours by doula', 'bar', 'visits.doula', [AGG('sum', 'visits', 'visits.hours', label='Visit hours')]),
        CHART('Visits by area', 'bar', 'visits.area', [AGG('count', 'visits', label='Visits')]),
        CHART('Visit miles by doula', 'bar', 'visits.doula', [AGG('sum', 'visits', 'visits.miles', label='Miles')]),
        CHART('Births attended per month', 'column', 'month', [AGG('count', 'births', date='births.date', label='Births attended')]),
        CHART('Birth hours per month', 'column', 'month', [AGG('sum', 'births', 'births.hours', date='births.date', label='Birth hours')]),
        CHART('Birth hours by area', 'bar', 'births.area', [AGG('sum', 'births', 'births.hours', label='Birth hours')]),
        CHART('Births attended by area', 'bar', 'births.area', [AGG('count', 'births', label='Births attended')]),
        CHART('Birth call hour by month', 'column', 'month', [AGG('avg', 'births', 'births.call_hour', date='births.date', label='Average call hour')]),
        CHART('Miles per month', 'column', 'month', [AGG('sum', 'mil_month', 'mil_month.miles', date='mil_month.month', label='Miles')]),
        CHART('Mileage cost per month', 'column', 'month', [AGG('sum', 'mil_month', 'mil_month.mileage_cost', date='mil_month.month', label='Mileage cost')]),
        CHART('Mileage cost by doula', 'bar', 'mil_doula.doula', [AGG('sum', 'mil_doula', 'mil_doula.mileage_cost', label='Mileage cost')]),
        CHART('Mileage cost by area', 'bar', 'mil_doula.area', [AGG('sum', 'mil_doula', 'mil_doula.mileage_cost', label='Mileage cost')]),
        CHART('Hour packs bought per month', 'column', 'month', [AGG('count', 'packs', date='packs.bought_on', label='Hour packs bought')]),
        CHART('Hour packs by package', 'bar', 'packs.package', [AGG('count', 'packs', label='Hour packs')]),
        CHART('Pack hours bought and used by month', 'column', 'month', [AGG('sum', 'packs', 'packs.hours_bought', date='packs.bought_on', label='Hours bought'), AGG('sum', 'packs', 'packs.hours_used', date='packs.bought_on', label='Hours used')]),
        CHART('Extra hours per month', 'column', 'month', [AGG('sum', 'packs', 'packs.extra_hours', date='packs.expires_on', label='Extra hours')]),
        CHART('Weekly team hours, last 26 weeks', 'line', 'wk_all.week_no', [AGG('avg', 'wk_all', 'wk_all.total_hours', label='Total hours')]),
        CHART('Visit hours by kind per month', 'stacked', 'month', [AGG('sum', 'visits', 'visits.hours', date='visits.date', where=[('kind', '=', k)], label=l) for k, l in ((PRE, 'Prenatal'), (PPV, 'Postpartum'), (NIGHT, 'Night shift'), (DEB, 'Debrief'))]),
        CHART('Births with a backup doula by month', 'column', 'month', [AGG('count', 'births', date='births.date', where=[('backup_used', '=', YES)], label='With a backup doula'), AGG('count', 'births', date='births.date', label='All births')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Actual hours vs plan by phase", "why": "every client's prenatal, on-call, birth and postpartum hours set against the package plan, with the worst client named", "where": "Actual Hours vs Plan"},
    {"name": "Postpartum hours ledger", "why": "hours bought, used and left for every pack, with extra hours turned into an invoice-ready amount", "where": "Postpartum Hours Ledger"},
    {"name": "Weekly hours load with rest-week warning", "why": "each doula's weekly hours against the cap and how many weeks in a row they were over it", "where": "Weekly Hours Load"},
    {"name": "Mileage log totals and travel fee test", "why": "mileage cost as a share of the package price, so you know when a travel fee is needed", "where": "Mileage Log Totals"},
    {"name": "Births attended summary", "why": "births per month, doula and quarter against your own maximum, with hours and averages", "where": "Births Attended Summary"},
    {"name": "Rest days between births", "why": "days between two births of one doula against your minimum, before the next window opens", "where": "Rest Days Check"},
    {"name": "Pack expiry planner", "why": "packs ending in 30 and 60 days, the visits a week needed to use the hours and the hours that will lapse", "where": "Pack Expiry Planner"},
    {"name": "Pack pace check", "why": "hours used per week since the first visit against the pace needed to finish before the expiry date", "where": "Pack Pace Check"},
    {"name": "Hours forecast for the next 4 weeks", "why": "open packs, on-call windows and booked visits turned into expected hours per week, Base, Best or Worst", "where": "Hours Forecast"},
    {"name": "Call-to-arrival time", "why": "minutes from the call to the arrival for each doula, day and night, against the limit you set", "where": "Call-to-Arrival Time"},
    {"name": "Hours by phase for every client", "why": "one calculated row per client with the share over plan and a flag, ready for the review of package hours", "where": "Hours by Phase"}]
competitors = [
    {"what": "free client-tracker templates", "lacks": "list clients and dates but never compare actual hours with the package plan or show the hours left on a prepaid pack"},
    {"what": "subscription practice-management software", "lacks": "charge every month and hide the hours, mileage and rest-day logic behind reports you cannot change"},
    {"what": "single-sheet mileage logs", "lacks": "add up miles but know nothing of packages, so they never show mileage as a share of the price or when to add a travel fee"},
    {"what": "generic time-tracking spreadsheets", "lacks": "log hours but not births, on-call windows, hour packs, night shifts or the weekly cap of each doula"},
    {"what": "paper visit and birth books", "lacks": "record the day but cannot total hours by phase, count rest days between births or warn that a pack ends soon"}]
guide = [
    'Open Start and type your business name and your own limits in the yellow cells: the weekly hours cap, the minimum booking, the rest days between births and the share over plan that you accept.',
    'Check Packages, Areas and Doulas. They hold the planned hours of each package, the mileage rate of each area and the weekly cap of each doula that the other sheets read.',
    'Write every visit in Visits: date, start time, client, doula, kind, hours, miles and area. The week, the mileage cost and the short and complete checks fill in by themselves.',
    'Write each birth in Births Attended: the call, arrival and leave times, the hours and the miles. The minutes to arrive, the night call and the quarter fill in. Nothing else about a birth is recorded.',
    'Keep Hour Packs up to date with the hours used and any extra hours. Hour Pack Ledger shows the hours left, the expiry check and the amount ready to invoice.',
    'Open Hours by Phase to see every client against the package plan, and Weekly Hours by Doula to see who is over the weekly cap.',
    'Read Mileage by Month, Mileage by Client and Mileage by Doula and Area when you set a travel fee or check the mileage you pay.',
    'Use Births per Month, Rest Days Between Births, Birth Hours Bands and Call Time Bands to see how many births you attend, how much rest follows and when calls come.',
    f'Use the {len(tools)} tools to compare hours with the plan, plan next week, test a travel fee, check rest, plan pack expiry and forecast the next 4 weeks.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Hours Dashboard and the charts every week. A solo doula uses the same sheets with one doula and no backup rota.']
listing = {"title": "Doula Business Visits, Hours, Mileage and Births Excel Template: Hour Pack Ledger, Weekly Hours Cap, Mileage Log, Birth Log",
    "headline": "Know the real hours behind every package, visit and birth",
    "tags": ["doula", "doula business", "doula template", "birth log", "mileage log", "visit log", "hour pack", "postpartum hours", "excel template", "weekly hours", "rest days", "business tracker", "time tracking"],
    "description": ("Keep track of the hours your doula business really takes in one Excel workbook. Built for an owner-doula who also takes clients, contracted doulas, backup doulas and a part-time admin, and just as useful for a solo doula who wants a personal time and mileage log. "
        "Visits records every prenatal, postpartum, night and debrief visit with hours, miles and area. Births Attended records the call, arrival and leave times, the hours and the miles of each birth, with no detail beyond that. Hour Packs and the Hour Pack Ledger show hours bought, used and left for every prepaid pack (a set number of postpartum hours bought together), the expiry check and the extra hours as an invoice-ready amount.\n\n"
        "Hours by Phase sets every client against the planned hours of the package. Weekly Hours by Doula counts visit and birth hours against the weekly cap and the weeks over it in a row. Mileage by Month, by Client and by Doula and Area show the mileage cost and its share of the package price. Rest Days Between Births, Births per Month, Birth Hours Bands and Call Time Bands show how many births are attended, how much rest follows and when the calls come.\n\n"
        f"{len(tools)} tools answer the weekly questions: actual hours against plan, the postpartum hours ledger, the weekly hours load, mileage totals and a travel fee test, the births attended summary, rest days, visit hours by kind, pack expiry and pace, extra hours to invoice, visit length, area clustering, birth hours, call-to-arrival time, night work, prenatal visit timing, a 4-week hours forecast and yearly hours per doula. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to clients, doulas, backup doulas, the admin, the owner-doula and the accountant.\n\n"
        "This is part five of the Doula Business suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Clients appear by name, area and dates only, with no medical detail. It helps you keep track of hours, dates, money and capacity and does not promise any result. Check your local rules for records, insurance and tax."),
    "features": ["Actual hours against the package plan", "Hour pack ledger with expiry and extra hours", "Weekly hours cap per doula", "Mileage log with travel fee test", "Birth log with call, arrival and leave times", "Rest days between births",
                 "Hours forecast for the next 4 weeks", f"{len(tools)} decision tools with a verdict", f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts",
                 f"{len(messages)} ready text messages"]}
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
s = spec(id=f'{SUITE}-p5', slug='doula-business-visits', profession='Doula Business', name='Visits, Hours, Mileage and Births',
         tagline='Know the real hours, miles and rest behind every package and birth', price_usd=29,
         colors={"primary": "#4A3F6B", "accent": "#E8A87C"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 5, "of": 8, "focus": "Visits, hours, mileage and births"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'du5.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
