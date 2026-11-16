"""HVAC and plumbing contractor suite - part 6: Sites, Equipment and Agreements."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from hv6_lists import *
from hv6_tables import settings, tables, WIN_DONE, WIN_EXP
from hv6_tools import tools, RR12, M12
import hv6_data as D

SUITE = 'fx-20261115-hvac-plumbing'
NOTE = "Sample wording: adapt it to your own business and check your local rules."
YES, NO = '{list:yesno.yes}', '{list:yesno.no}'
ACT, RD, LAP, CAN = (tok('agrstatus', s) for s in ('Active', 'Renewal due', 'Lapsed', 'Cancelled'))
DONE, DUE, BOOKED, MISSED = (tok('visitstatus', s) for s in ('Done', 'Due', 'Booked', 'Missed'))
RENEWED, ROPEN = tok('renewout', 'Renewed'), tok('renewout', 'Open')
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
def F(*pairs): return [FV(a, b) for a, b in pairs]

forms = [
    FORM('site_record_sheet', 'Site Record Sheet', 'Customer site record', 'sites.site_id', F(
        ('Site reference', 'sites.site_ref'), ('Area', 'sites.area'), ('Site type', 'sites.site_type'), ('Landlord or business account', 'sites.account'), ('Phone', 'sites.phone'), ('Member', 'sites.member'),
        ('Equipment records', 'sites.equipment'), ('Oldest equipment, years', 'sites.oldest_age'), ('Last service', 'sites.last_service'), ('Months since a service', 'sites.gap_months'), ('Jobs', 'sites.jobs'),
        ('First job', 'sites.first_job'), ('Last job', 'sites.last_job'), ('Revenue to date', 'sites.revenue'), ('Open tune-ups', 'sites.open_visits'))),
    FORM('equipment_sheet', 'Equipment Record Sheet', 'Equipment record with age and lead score', 'equipment.equipment_id', F(
        ('Site reference', 'equipment.site_ref'), ('Type', 'equipment.type'), ('Fuel', 'equipment.fuel'), ('Install date', 'equipment.install_date'), ('Warranty end', 'equipment.warranty_end'), ('Make', 'equipment.make'),
        ('Model', 'equipment.model'), ('Serial', 'equipment.serial'), ('Last service', 'equipment.last_service'), ('Age, years', 'equipment.age_years'), ('Months since a service', 'equipment.gap_months'),
        ('Jobs at the site', 'equipment.site_jobs'), ('Lead score', 'equipment.lead_score'), ('Replacement value', 'equipment.replace_value'), ('Call now, mail or hold', 'equipment.verdict'))),
    FORM('signup_sheet', 'Agreement Sign-up Sheet', 'Maintenance agreement sign-up', 'agreements.agreement_id', F(
        ('Site reference', 'agreements.site_ref'), ('Site type', 'agreements.site_type'), ('Phone', 'agreements.phone'), ('Plan', 'agreements.plan'), ('Price a year', 'agreements.price'), ('Visits a year', 'agreements.visits_per_year'),
        ('Billing', 'agreements.billing'), ('Start date', 'agreements.start_date'), ('Renewal date', 'agreements.renewal_date'), ('Sold by', 'agreements.sold_by'), ('Member discount on repairs', 'agreements.member_pct')) + [
        FF('Monthly amount if billed monthly', 'INDEX({range:agreements.price},MATCH({pick},{range:agreements.agreement_id},0))/12', 'money'),
        FF('Bonus for the sale', '{set:spiff_agreement}', 'money')]),
    FORM('renewal_sheet', 'Agreement Renewal Sheet', 'Agreement renewal call sheet', 'renew_due.rank_no', F(
        ('Agreement', 'renew_due.agreement_id'), ('Site reference', 'renew_due.site_ref'), ('Plan', 'renew_due.plan'), ('Price a year', 'renew_due.price'), ('Renewal date', 'renew_due.renewal_date'), ('Days left', 'renew_due.days_left'),
        ('Flag', 'renew_due.flag'), ('Call by', 'renew_due.call_by'), ('Phone', 'renew_due.phone'), ('Renewals due this month', 'renew_due.due_count'), ('Revenue at risk this month', 'renew_due.risk_total'))),
    FORM('cancel_sheet', 'Agreement Cancellation Sheet', 'Agreement cancellation record', 'lapse.rank_no', F(
        ('Agreement', 'lapse.agreement_id'), ('Site reference', 'lapse.site_ref'), ('Plan', 'lapse.plan'), ('Ended on', 'lapse.end_date'), ('Price a year', 'lapse.price'), ('Months as a member', 'lapse.months_member'),
        ('Reason noted', 'lapse.reason'), ('Phone', 'lapse.phone'))),
    FORM('visit_sheet', 'Tune-up Visit Sheet', 'Tune-up visit record', 'visits.visit_id', F(
        ('Agreement', 'visits.agreement_id'), ('Site reference', 'visits.site_ref'), ('Phone', 'visits.phone'), ('Plan', 'visits.plan'), ('Window', 'visits.season'), ('Planned date', 'visits.planned_date'), ('Status', 'visits.status'),
        ('Technician for the visit', 'visits.assigned'), ('Value of the visit', 'visits.visit_value'), ('Plan price', 'visits.plan_price'))),
    FORM('booking_sheet', 'Tune-up Booking Sheet', 'Tune-up booking with the days left in the window', 'visits.visit_id', F(
        ('Site reference', 'visits.site_ref'), ('Phone', 'visits.phone'), ('Window', 'visits.season'), ('Window start', 'visits.window_start'), ('Window end', 'visits.window_end'), ('Planned date', 'visits.planned_date'),
        ('Technician for the visit', 'visits.assigned'), ('Technician phone', 'visits.tech_phone')) + [
        FF('Days from planned date to window end', 'INDEX({range:visits.window_end},MATCH({pick},{range:visits.visit_id},0))-INDEX({range:visits.planned_date},MATCH({pick},{range:visits.visit_id},0))', 'int'),
        FF('Hours to hold on the board', '{set:visit_hours}', 'num')]),
    FORM('completion_sheet', 'Visit Completion Sheet', 'Visit completion with the date and the technician', 'visits.visit_id', F(
        ('Site reference', 'visits.site_ref'), ('Plan', 'visits.plan'), ('Done on', 'visits.done_on'), ('Technician', 'visits.technician'), ('Job', 'visits.job_id'), ('Status', 'visits.status'), ('Value of the visit', 'visits.visit_value')) + [
        FF('Days from the planned date to the visit', 'INDEX({range:visits.done_on},MATCH({pick},{range:visits.visit_id},0))-INDEX({range:visits.planned_date},MATCH({pick},{range:visits.visit_id},0))', 'int')]),
    FORM('reminder_sheet', 'Pre-season Reminder Sheet', 'Pre-season reminder to one site', 'campaign.campaign_id', F(
        ('Site reference', 'campaign.site_ref'), ('Phone', 'campaign.phone'), ('Channel', 'campaign.channel'), ('Reminder sent', 'campaign.reminder_sent'), ('Last service', 'campaign.last_service'), ('Oldest equipment, years', 'campaign.equip_age'),
        ('Cost of the reminder', 'campaign.cost'), ('Next window starts', 'campaign.next_window'), ('Booked', 'campaign.booked'), ('Agreement sold', 'campaign.converted'))),
    FORM('campaign_sheet', 'Campaign Result Sheet', 'Campaign result for one month', 'campaign_month.month', F(
        ('Reminders', 'campaign_month.reminders'), ('Tune-ups booked', 'campaign_month.booked'), ('Agreements sold', 'campaign_month.sold'), ('Cost', 'campaign_month.cost'), ('Booked rate', 'campaign_month.booked_rate'),
        ('Cost per booked tune-up', 'campaign_month.cost_per_booked')) + [FF('Booked rate you want', '{set:booked_target}', 'pct')]),
    FORM('lead_sheet', 'Replacement Lead Sheet', 'Replacement lead from aged equipment', 'aged.rank_no', F(
        ('Equipment', 'aged.equipment_id'), ('Site reference', 'aged.site_ref'), ('Type', 'aged.type'), ('Age, years', 'aged.age_years'), ('Service record', 'aged.service_note'), ('Lead score', 'aged.lead_score'),
        ('Replacement value', 'aged.replace_value'), ('This week', 'aged.call_week'), ('Phone', 'aged.phone'))),
    FORM('member_change_sheet', 'Member Change Sheet', 'Change of plan or billing for a member', 'agreements.agreement_id', F(
        ('Site reference', 'agreements.site_ref'), ('Phone', 'agreements.phone'), ('Plan', 'agreements.plan'), ('Price a year', 'agreements.price'), ('Billing', 'agreements.billing'), ('Status', 'agreements.status'),
        ('Renewal date', 'agreements.renewal_date'), ('Renewals so far', 'agreements.renewals'), ('Visits done', 'agreements.visits_done')) + [
        FF('Difference to the Premium plan price', 'INDEX({range:plans.price},MATCH(%s,{range:plans.plan},0))-INDEX({range:agreements.price},MATCH({pick},{range:agreements.agreement_id},0))' % tok('plan', 'Premium comfort'), 'money')]),
]
assert len(forms) == 12
SG = ['Contractor', 'Customer']
documents = [
    DOC('agreement_doc', 'Agreement Summary', 'Maintenance agreement summary for a customer', 'agreements.agreement_id', [
        'Maintenance agreement summary of {set:company}, dated {today}. Agreement {col:agreements.agreement_id} for site reference {col:agreements.site_ref}.',
        'Plan: {col:agreements.plan}. Price: {col:agreements.price} a year, before sales tax, billed {col:agreements.billing}. Tune-up visits a year: {col:agreements.visits_per_year}. Start date: {col:agreements.start_date}. Renewal date: {col:agreements.renewal_date}.',
        'Members receive {col:agreements.member_pct} off repairs. A tune-up is a planned seasonal visit to one system. Please check the terms of the agreement before you sign.', 'Notes are written below.'], SG, NOTE),
    DOC('renewal_notice_doc', 'Renewal Notice', 'Agreement renewal notice with price and date', 'renew_due.rank_no', [
        'Agreement renewal notice of {set:company}, dated {today}. Agreement {col:renew_due.agreement_id}, site reference {col:renew_due.site_ref}, plan {col:renew_due.plan}.',
        'Your agreement renews on {col:renew_due.renewal_date} for {col:renew_due.price} a year, before sales tax. Days left: {col:renew_due.days_left}.', 'Please contact {set:company} before the renewal date if you want to change your plan or stop the agreement.', 'The reply of the customer is written below.'], SG, NOTE),
    DOC('welcome_doc', 'Agreement Welcome Letter', 'Agreement welcome letter', 'agreements.agreement_id', [
        'Welcome letter of {set:company}, dated {today}. Site reference {col:agreements.site_ref}.', 'Thank you for joining the {col:agreements.plan} plan on {col:agreements.start_date}. Your plan includes {col:agreements.visits_per_year} tune-up visits a year and {col:agreements.member_pct} off repairs.',
        'We will contact you before each tune-up window opens. Your next renewal date is {col:agreements.renewal_date}.', 'Contact {set:company} to book or move a visit.'], ['Contractor'], NOTE),
    DOC('visit_confirm_doc', 'Tune-up Confirmation', 'Tune-up visit confirmation', 'visits.visit_id', [
        'Tune-up visit confirmation of {set:company}, dated {today}. Visit {col:visits.visit_id} at site reference {col:visits.site_ref}, plan {col:visits.plan}.',
        'Your tune-up is planned for {col:visits.planned_date}. The window for this visit runs from {col:visits.window_start} to {col:visits.window_end}. Technician: {col:visits.assigned}.', 'Please make sure someone can give access to the site. Call {set:company} if the date does not suit you.', 'Changes are written below.'], ['Dispatcher'], NOTE),
    DOC('visit_report_doc', 'Tune-up Visit Report', 'Tune-up visit report, a plain list of tasks done', 'visits.visit_id', [
        'Tune-up visit report of {set:company}, dated {today}. Visit {col:visits.visit_id}, job {col:visits.job_id}, site reference {col:visits.site_ref}.', 'Plan: {col:visits.plan}. Window: {col:visits.season}. Visit date: {col:visits.done_on}. Technician: {col:visits.technician}. Status: {col:visits.status}.',
        'The tasks done and any follow-up the customer may want are written below as a plain list.', 'The customer signs to confirm the visit took place.'], SG, NOTE),
    DOC('reminder_letter_doc', 'Pre-season Reminder Letter', 'Pre-season reminder letter', 'campaign.campaign_id', [
        'Pre-season reminder of {set:company}, dated {col:campaign.reminder_sent}. Site reference {col:campaign.site_ref}.', 'The next tune-up window starts on {col:campaign.next_window}. Your last service with us was on {col:campaign.last_service}.',
        'Book early to choose the day that suits you. Call {set:company} or reply to this message.', 'Notes of the call are written below.'], ['Office'], NOTE),
    DOC('aged_letter_doc', 'Aged Equipment Letter', 'Aged equipment letter for a customer', 'aged.rank_no', [
        'Letter of {set:company}, dated {today}. Site reference {col:aged.site_ref}.', 'Our records show equipment of type {col:aged.type} at your site, about {col:aged.age_years} years old, service record: {col:aged.service_note}.',
        'It may be worth a look at replacement options. We can give you a priced estimate with three options for one job. Please contact {set:company} to book a visit.', 'The reply of the customer is written below.'], ['Office'], NOTE),
    DOC('winback_doc', 'Lapse Win-back Letter', 'Win-back letter for a lapsed agreement', 'lapse.rank_no', [
        'Letter of {set:company}, dated {today}. Site reference {col:lapse.site_ref}.', 'Your {col:lapse.plan} agreement ended on {col:lapse.end_date} after {col:lapse.months_member} months. We would be glad to welcome you back at {col:lapse.price} a year, before sales tax.',
        'Tell us if something in the service could have been better. Please contact {set:company} to rejoin.', 'The reply of the customer is written below.'], ['Office'], NOTE),
    DOC('price_list_doc', 'Agreement Price List', 'Agreement price list for one plan', 'plans.plan', [
        'Agreement price list of {set:company}, dated {today}.', 'Plan: {col:plans.plan}. Price: {col:plans.price} a year, before sales tax. Tune-up visits a year: {col:plans.visits_per_year}.',
        'Members receive {set:member_discount} off repairs. Prices may change at renewal. Please check the terms of the agreement.', 'Notes are written below.'], ['Office'], NOTE),
    DOC('register_doc', 'Landlord Equipment Register', 'Equipment register for a landlord or business account', 'sites.site_id', [
        'Equipment register of {set:company}, dated {today}. Account {col:sites.account}, site reference {col:sites.site_ref}, area {col:sites.area}.', 'Equipment records at the site: {col:sites.equipment}. Oldest equipment: {col:sites.oldest_age} years. Last service: {col:sites.last_service}. Open tune-ups: {col:sites.open_visits}.',
        'The lines of the register (type, age and last service of each record) are written below.', 'The account contact signs to confirm the list.'], ['Contractor', 'Account contact'], NOTE),
    DOC('visits_plan_doc', 'Visits Due Plan', 'Visits due by month plan', 'visits_month.month', [
        'Visits plan of {set:company}, dated {today}. Month starting {col:visits_month.month}.', 'Visits due: {col:visits_month.visits_due}. Visits done: {col:visits_month.visits_done}. Hours needed: {col:visits_month.hours_needed}. Hours free for tune-ups: {col:visits_month.capacity_hours}. Slack hours: {col:visits_month.slack_hours}.',
        'Month check: {col:visits_month.flag}. Actions for the month are written below.'], ['Office manager', 'Owner'], NOTE),
    DOC('book_report_doc', 'Agreement Book Report', 'Agreement book report for the owner', 'book_month.month', [
        'Agreement book report of {set:company}, dated {today}. Month starting {col:book_month.month}.', 'New agreements: {col:book_month.new}. Renewed: {col:book_month.renewed}. Renewals lapsed: {col:book_month.renew_lapsed}. Agreements ended: {col:book_month.lapsed}. Running at month end: {col:book_month.running}.',
        'Monthly recurring revenue: {col:book_month.mrr}. Renewal rate: {col:book_month.renew_rate}.', 'Actions for the next review are written below.'], ['Owner', 'Office manager'], NOTE),
]
assert len(documents) == 12
checklists = [
    CHK('site_created', 'Site Record Created', 'sites', 'sites.first_job', [('Write the site reference and the area', 0), ('Add the phone number', 0), ('Mark landlord or business accounts with the account number', 0), ('Add the equipment records', 1), ('Note the last service date', 1), ('Offer an agreement at the first visit', 2)]),
    CHK('equipment_recorded', 'Equipment Recorded', 'equipment', 'equipment.last_service', [('Write the type and the fuel', 0), ('Add the install date and the warranty end', 0), ('Add the make, model and serial', 0), ('Link the record to the site', 0), ('Set the next service date', 1)]),
    CHK('agreement_sold', 'Agreement Sold', 'agreements', 'agreements.start_date', [('Write the plan, price and billing', 0), ('Link the agreement to the site', 0), ('Plan the two tune-up windows', 1), ('Record who sold it for the bonus', 1), ('Take the first payment', 2)]),
    CHK('welcome_pack', 'Welcome Pack Sent', 'agreements', 'agreements.start_date', [('Print the agreement summary', 0), ('Send the welcome letter', 1), ('Tell the customer the member discount', 1), ('Add the renewal date to the board', 2), ('Ask for a review after the first visit', 30)]),
    CHK('visit_booked', 'Tune-up Visit Booked', 'visits', 'visits.window_start', [('Send the reminder before the window', 0), ('Offer two dates', 7), ('Confirm the date by text', 10), ('Add the visit to the dispatch board', 10), ('Check the parts for the season', 14)]),
    CHK('visit_completed', 'Tune-up Visit Completed', 'visits', 'visits.planned_date', [('Check the visit sheet', -1), ('Arrive in the window', 0), ('Write the tasks done on the visit report', 0), ('Get the customer signature', 0), ('Mark the visit done', 1), ('Send the visit report', 2)]),
    CHK('renewal_notice', 'Renewal Notice Sent', 'agreements', 'agreements.renewal_date', [('Check the plan and the price', -60), ('Send the renewal notice', -45), ('Remind by text', -30), ('Record the reply', -21)]),
    CHK('renewal_call', 'Renewal Call Made', 'agreements', 'agreements.renewal_date', [('Call the customer', -21), ('Offer to move to another plan if useful', -21), ('Note the answer', -20), ('Update the status', -14), ('Call again if there is no answer', -7)]),
    CHK('lapse_followup', 'Lapsed Agreement Follow-up', 'agreements', 'agreements.end_date', [('Note the reason for ending', 0), ('Send the win-back letter', 14), ('Call after a month', 30), ('Offer a tune-up before the next window', 90), ('Close the file if there is no reply', 180)]),
    CHK('campaign_setup', 'Pre-season Campaign Setup', 'campaign', 'campaign.reminder_sent', [('Pick the sites by last service and equipment age', -14), ('Choose the channel for each group', -10), ('Write the reminder', -7), ('Send the reminders', 0), ('Count the tune-ups booked after two weeks', 14), ('Record agreements sold', 30)]),
    CHK('book_review', 'Monthly Agreement Book Review', 'book_month', 'book_month.month', [('Check running agreements and recurring revenue', 28), ('Check new, renewed and ended agreements', 28), ('Read the renewal rate against your target', 29), ('List the renewals still open', 29), ('Plan the calls for next month', 30)]),
    CHK('aged_review', 'Aged Equipment Review', 'equipment', 'equipment.last_service', [('Open the Aged Equipment Lead List', 0), ('Call the top leads of the week', 1), ('Mail the rest of the list', 3), ('Note the replies on the equipment record', 7), ('Review the leads again next month', 30)]),
]
assert len(checklists) == 12
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('c_due', 'Customer: tune-up due, choose a time', 'visits', 'visits.phone', 'Hello, your {plan} tune-up for {site_ref} is due. Please choose a time between {window_start} and {window_end}. {company}'),
    M('c_booked', 'Customer: your tune-up is booked', 'visits', 'visits.phone', 'Hello, your tune-up for {site_ref} is booked for {planned_date}. {company}'),
    M('c_tomorrow', 'Customer: your tune-up is tomorrow', 'visits', 'visits.phone', 'Hello, reminder from {company}: your tune-up for {site_ref} is planned for {planned_date}.'),
    M('c_thanks', 'Customer: your tune-up is done', 'visits', 'visits.phone', 'Hello, thank you for your tune-up at {site_ref} on {done_on}. {company}'),
    M('c_renews', 'Customer: agreement renews on a date', 'agreements', 'agreements.phone', 'Hello, your {plan} agreement for {site_ref} renews on {renewal_date} for {price} a year. {company}'),
    M('c_renews_days', 'Customer: agreement renews in days', 'agreements', 'agreements.phone', 'Hello, your agreement for {site_ref} renews in {days_left} days. Reply to {company} with any change.'),
    M('c_renewed', 'Customer: your agreement has renewed', 'agreements', 'agreements.phone', 'Hello, your {plan} agreement for {site_ref} has renewed. Thank you. {company}'),
    M('c_rejoin', 'Customer: your agreement ended, rejoin?', 'lapse', 'lapse.phone', 'Hello, we noticed your {plan} agreement for {site_ref} ended on {end_date}. Would you like to rejoin? {company}'),
    M('c_missed', 'Customer: you missed your window', 'visits', 'visits.phone', 'Hello, the tune-up window for {site_ref} ended on {window_end}. Can we rebook a visit? {company}'),
    M('c_age', 'Customer: your equipment is getting old', 'aged', 'aged.phone', 'Hello, the equipment at {site_ref} is about {age_years} years old. Ask {company} about replacement options.'),
    M('c_welcome', 'Customer: welcome to the agreement', 'agreements', 'agreements.phone', 'Welcome to the {plan} agreement for {site_ref}, starting {start_date}, with {visits_per_year} tune-ups a year. {company}'),
    M('c_member', 'Customer: your member repair discount', 'agreements', 'agreements.phone', 'Hello, as a member on the {plan} plan you get {member_pct} off repairs at {site_ref}. {company}'),
    M('c_season', 'Customer: book before the season', 'campaign', 'campaign.phone', 'Hello, please book your tune-up for {site_ref} before the season starts on {next_window}. {company}'),
    M('c_report', 'Customer: your visit report is ready', 'visits', 'visits.phone', 'Hello, your visit report for {site_ref} on {done_on} is ready. {company}'),
    M('c_review', 'Customer: would you recommend us?', 'visits', 'visits.phone', 'Hello, thank you for choosing {company} for your visit at {site_ref}. Would you recommend us to a neighbour?'),
    M('l_visits', 'Landlord account: tune-ups due', 'sites', 'sites.phone', 'Hello {account}, {open_visits} tune-ups are open at {site_ref}. Please confirm access. {company}'),
    M('l_list', 'Landlord account: equipment list', 'sites', 'sites.phone', 'Hello {account}, the equipment list for {site_ref} ({equipment} records) is attached. {company}'),
    M('l_renew', 'Landlord account: renewals due', 'agreements', 'agreements.phone', 'Hello {account}, the agreement for {site_ref} renews on {renewal_date}. {company}'),
    M('t_week', 'Technician: your tune-ups', 'visits', 'visits.tech_phone', 'Hello {assigned}, your tune-up at {site_ref} is planned for {planned_date}, window {window_start} to {window_end}. {company}'),
    M('t_report', 'Technician: complete the visit report', 'visits', 'visits.tech_phone', 'Hello {assigned}, please complete the visit report for {site_ref}, visit {visit_id}. {company}'),
    M('t_aged', 'Technician: aged equipment at a site', 'visits', 'visits.tech_phone', 'Hello {assigned}, please note any aged equipment at {site_ref} on your visit and tell the office. {company}'),
    M('a_ride', 'Apprentice: you ride along on tune-ups', 'visits', 'visits.apprentice_phone', 'Hello {apprentice}, you ride along on the tune-up at {site_ref} on {planned_date}. {company}'),
    M('om_renewals', 'Office manager: renewals due this month', 'renew_due', 'renew_due.office_phone', 'Agreements due for renewal this month: {due_count}. Please start the renewal calls. {company}'),
    M('om_overdue', 'Office manager: visits overdue', 'visits', 'visits.office_phone', 'Tune-up visits overdue: {overdue_count}. Please call the list today. {company}'),
    M('om_window', 'Office manager: the window is behind', 'visits_month', 'visits_month.office_phone', 'The open tune-up window is {window_gap} points against last year at this point. Please plan the calls. {company}'),
    M('om_book', 'Office manager: book tune-ups this week', 'visits_month', 'visits_month.office_phone', 'Please book {book_week} tune-ups this week. {company}'),
    M('ow_book', 'Owner: book and recurring revenue', 'book_month', 'book_month.owner_phone', 'Agreement book for the month of {month}: {running} running, monthly recurring revenue {mrr}. {company}'),
    M('ow_open', 'Owner: renewals still open', 'renew_due', 'renew_due.owner_phone', 'Renewals still open this month: {due_count}. {company}'),
    M('ow_risk', 'Owner: agreement revenue at risk', 'renew_due', 'renew_due.owner_phone', 'Agreement revenue at risk this month: {risk_total}. {company}'),
    M('ow_campaign', 'Owner: the campaign booked tune-ups', 'campaign_month', 'campaign_month.owner_phone', 'The campaign of {month} booked {booked} tune-ups from {reminders} reminders. {company}'),
    M('ow_aged', 'Owner: aged equipment leads', 'aged', 'aged.owner_phone', 'Aged equipment leads this month: {aged_count} records are over the replace age. {company}'),
    M('s_volume', 'Equipment supplier: replacement volume', 'age_bands', 'age_bands.supplier_phone', 'Hello, expected replacements next year for {type}, {band}: about {expected_whole}. {company}'),
    M('ac_mrr', 'Accountant: recurring revenue summary', 'book_month', 'book_month.acct_phone', 'Hello, recurring revenue summary for the month of {month}: {mrr} a month from {running} agreements. {company}'),
    M('p_parts', 'Parts counter: tune-up parts', 'visits_month', 'visits_month.parts_phone', 'Hello, {visits_due} tune-ups are planned in the month of {month}. Please prepare the tune-up parts. {company}'),
]
assert len(messages) == 34, len(messages)

def CD(c, n): return '{range:%s},">="&({today}-%d),{range:%s},"<="&{today}' % (c, n, c)
INM = lambda c: '{range:%s},">="&%s,{range:%s},"<"&EDATE(%s,1)' % (c, MS, c, MS)
kpis = [
    KPI('Customer sites', 'COUNTA({range:sites.site_id})', 'int'),
    KPI('Sites with an agreement', 'COUNTIFS({range:sites.member},%s)' % YES, 'int'),
    KPI('Share of sites with an agreement', 'IFERROR(COUNTIFS({range:sites.member},%s)/COUNTA({range:sites.site_id}),0)' % YES, 'pct'),
    KPI('Equipment records', 'COUNTA({range:equipment.equipment_id})', 'int'),
    KPI('Equipment older than the replace age', 'COUNTIFS({range:equipment.aged},1)', 'int'),
    KPI('Equipment never serviced by the shop', 'COUNTIFS({range:equipment.never_serviced},1)', 'int'),
    KPI('Running agreements', 'COUNTIFS({range:agreements.running},1)', 'int'),
    KPI('New agreements, last 30 days', 'COUNTIFS(%s)' % CD('agreements.start_date', 30), 'int'),
    KPI('New agreements, last 90 days', 'COUNTIFS(%s)' % CD('agreements.start_date', 90), 'int'),
    KPI('Agreements ended, last 90 days', 'COUNTIFS(%s)' % CD('agreements.end_date', 90), 'int'),
    KPI('Monthly recurring revenue', 'SUM({range:agreements.mrr})', 'money'),
    KPI('Yearly agreement revenue', 'SUMIFS({range:agreements.price},{range:agreements.running},1)', 'money'),
    KPI('Average agreement price', 'IFERROR(SUMIFS({range:agreements.price},{range:agreements.running},1)/COUNTIFS({range:agreements.running},1),0)', 'money'),
    KPI('Renewals due this month', 'COUNTIFS({range:renewals.month},%s)' % MS, 'int'),
    KPI('Renewals done this month', 'COUNTIFS({range:renewals.month},%s,{range:renewals.outcome},%s)' % (MS, RENEWED), 'int'),
    KPI('Renewal rate, last 12 months', RR12, 'pct'),
    KPI('Renewal rate against the target, points', RR12 + '-{set:renewal_target}', 'pct'),
    KPI('Revenue at risk this month', 'SUMIFS({range:agreements.price},{range:agreements.due_month},1)', 'money'),
    KPI('Tune-up visits due this month', 'COUNTIFS(%s)' % INM('visits.planned_date'), 'int'),
    KPI('Tune-up visits done this month', 'COUNTIFS(%s)' % INM('visits.done_on'), 'int'),
    KPI('Visits overdue', 'COUNTIFS({range:visits.overdue_score},">0")', 'int'),
    KPI('Open window done share', WIN_DONE(), 'pct'),
    KPI('Open window expected share, last year', WIN_EXP(), 'pct'),
    KPI('Open window gap, points', WIN_DONE() + '-' + WIN_EXP(), 'pct'),
    KPI('Tune-up hours needed, next 3 months', 'SUMIFS({range:visits_month.hours_needed},{range:visits_month.month},">"&%s,{range:visits_month.month},"<="&EDATE(%s,3))' % (MS, MS), 'num'),
    KPI('Slack hours, next 3 months', 'SUMIFS({range:visits_month.slack_hours},{range:visits_month.month},">"&%s,{range:visits_month.month},"<="&EDATE(%s,3))' % (MS, MS), 'num'),
    KPI('Member revenue per site, 12 months', 'IFERROR(SUMIFS({range:member_rev.total_revenue},{range:member_rev.member},%s)/SUMIFS({range:member_rev.sites},{range:member_rev.member},%s),0)' % (YES, YES), 'money'),
    KPI('Non-member revenue per site, 12 months', 'IFERROR(SUMIFS({range:member_rev.total_revenue},{range:member_rev.member},%s)/SUMIFS({range:member_rev.sites},{range:member_rev.member},%s),0)' % (NO, NO), 'money'),
    KPI('Campaign reminders, last 90 days', 'COUNTIFS(%s)' % CD('campaign.reminder_sent', 90), 'int'),
    KPI('Campaign cost per booked tune-up', 'IFERROR(SUMIFS({range:campaign.cost},%s)/COUNTIFS(%s,{range:campaign.booked},%s),0)' % (CD('campaign.reminder_sent', 365), CD('campaign.reminder_sent', 365), YES), 'money'),
]
assert len(kpis) == 30, len(kpis)
def BS(c, label): return {"label": label, "sum": "book_month." + c, "date": "book_month.month"}
dashboard = {"title": "Agreements and Sites Dashboard", "kpis": kpis,
    "monthly": {"title": "New, renewed and ended agreements by month", "date": "book_month.month", "series": [BS('new', 'New agreements'), BS('renewed', 'Renewed'), BS('lapsed', 'Agreements ended')]},
    "breakdowns": [{"title": "Agreements by plan", "by": "agreements.plan", "value": "agreements.price", "agg": "count"}, {"title": "Agreements by status", "by": "agreements.status", "value": "agreements.price", "agg": "count"},
                   {"title": "Tune-up visits by status", "by": "visits.status", "value": "visits.visit_value", "agg": "count"}, {"title": "Equipment by type", "by": "equipment.type", "value": "equipment.replace_value", "agg": "count"}]}
def CM(title, typ, tbl, col, label, agg='sum'): return CHART(title, typ, 'month', [AGG(agg, tbl, '%s.%s' % (tbl, col), date='%s.month' % tbl, label=label)])
def CNT(title, tbl, col, where=None, label=None): return CHART(title, 'bar', '%s.%s' % (tbl, col), [AGG('count', tbl, where=where, label=label or title.split(' by ')[0])])
RUN = [('running', '=', 1)]
insights = {"filters": [{"label": "Technician", "list": "tech"}, {"label": "Area", "list": "area"}, {"label": "Plan", "list": "plan"}],
    "gauges": [{"title": "Renewal rate against the target", "num": AGG('count', 'renewals', where=[('outcome', '=', RENEWED)]), "den": AGG('count', 'renewals', where=[('outcome', '<>', ROPEN)])},
               {"title": "Open window done against expected", "num": AGG('count', 'visits', where=[('status', '=', DONE), ('window_end', '>=', '{today}')]), "den": AGG('count', 'visits', where=[('window_end', '>=', '{today}')])},
               {"title": "Visits done on time", "num": AGG('count', 'visits', where=[('status', '=', DONE)]), "den": AGG('count', 'visits', where=[('status', '<>', DUE), ('status', '<>', BOOKED)])},
               {"title": "Sites with an agreement", "num": AGG('count', 'sites', where=[('member', '=', YES)]), "den": AGG('count', 'sites')},
               {"title": "Equipment records complete", "num": AGG('count', 'equipment', where=[('complete', '=', 1)]), "den": AGG('count', 'equipment')},
               {"title": "Reminders that booked", "num": AGG('count', 'campaign', where=[('booked', '=', YES)]), "den": AGG('count', 'campaign')}],
    "charts": [
        CNT('Customer sites by area', 'sites', 'area'), CNT('Customer sites by site type', 'sites', 'site_type'), CNT('Equipment by type', 'equipment', 'type'), CNT('Equipment by fuel', 'equipment', 'fuel'),
        CHART('Equipment by age band', 'bar', 'age_bands.band', [AGG('sum', 'age_bands', 'age_bands.records', label='Records')]),
        CNT('Running agreements by plan', 'agreements', 'plan', RUN, 'Running agreements'), CNT('Agreements by status', 'agreements', 'status'),
        CM('New agreements per month', 'column', 'book_month', 'new', 'New agreements'), CM('Agreements ended per month', 'column', 'book_month', 'lapsed', 'Agreements ended'),
        CM('Running agreements per month', 'line', 'book_month', 'running', 'Running agreements'), CM('Monthly recurring revenue per month', 'line', 'book_month', 'mrr', 'Monthly recurring revenue'),
        CNT('Renewals by outcome', 'renewals', 'outcome'), CM('Renewals due per month', 'column', 'book_month', 'renewals_due', 'Renewals due'), CM('Renewal rate per month', 'line', 'book_month', 'renew_rate', 'Renewal rate', 'avg'),
        CNT('Visits by window', 'visits', 'season'), CNT('Visits by status', 'visits', 'status'), CM('Visits done per month', 'column', 'visits_month', 'visits_done', 'Visits done'),
        CHART('Visits due against capacity per month', 'line', 'month', [AGG('sum', 'visits_month', 'visits_month.hours_needed', date='visits_month.month', label='Hours needed'), AGG('sum', 'visits_month', 'visits_month.capacity_hours', date='visits_month.month', label='Hours free for tune-ups')]),
        CHART('Revenue by member group and area', 'bar', 'member_rev.area', [AGG('sum', 'member_rev', 'member_rev.total_revenue', where=[('member', '=', YES)], label='Members'), AGG('sum', 'member_rev', 'member_rev.total_revenue', where=[('member', '=', NO)], label='Non-members')]),
        CHART('Agreement revenue by plan', 'bar', 'plan_status.plan', [AGG('sum', 'plan_status', 'plan_status.revenue', where=[('status', '<>', LAP), ('status', '<>', CAN)], label='Yearly fees')]),
        CM('Campaign reminders per month', 'column', 'campaign_month', 'reminders', 'Reminders'), CM('Campaign tune-ups booked per month', 'column', 'campaign_month', 'booked', 'Tune-ups booked')]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6
signature = [
    {"name": "Aged Equipment Lead List", "why": "records over your replace age are scored by age, service gap and jobs at the site, ranked, and the top leads of the week get a call now or mail verdict", "where": "Aged Equipment Lead List"},
    {"name": "Agreement Book Health", "why": "running agreements, recurring revenue and renewal rate against your target and your own last 12 months, with a growing, flat or shrinking verdict", "where": "Agreement Book Health"},
    {"name": "Renewals Due This Month", "why": "the ten agreements to call first, ranked by value then days left, with a call-by date and the fees at risk", "where": "Renewals Due This Month"},
    {"name": "Tune-Up Window Tracker", "why": "the open tune-up window against the same point last year, the visits to book this week and a traffic light", "where": "Tune-Up Window Tracker"},
    {"name": "Tune-Up Scheduling by Season", "why": "visits due for each month against the technician hours left after the work of the season: over-capacity and too-empty months", "where": "Tune-Up Scheduling by Season"},
    {"name": "Agreement Profit by Plan", "why": "plan price less visits, travel and member discount, plus the profit on the repairs and replacements members buy, with a price up, hold or add a visit verdict", "where": "Agreement Profit by Plan"},
    {"name": "Pre-Season Campaign Planner", "why": "sites by last service and equipment age become a reminder list with booked rate from your own history and the cost per booked tune-up", "where": "Pre-Season Campaign Planner"},
    {"name": "Visit Overdue List", "why": "visits whose window ended without a visit, ranked by plan value, with the revenue at risk and a call list", "where": "Visit Overdue List"},
    {"name": "Slow-Season Filler", "why": "free technician hours in the slow months turned into tune-ups you could book and the revenue they add", "where": "Slow-Season Filler"},
    {"name": "Agreement Revenue Forecast", "why": "recurring revenue for the next 12 months from your renewal rate and sign-ups, with base, best and worst rows", "where": "Agreement Revenue Forecast"}]
competitors = [
    {"what": "field-service app with a per-technician fee", "lacks": "charges each person every month, keeps agreements as a list of dates and does not rank renewals by value or aged equipment by lead score"},
    {"what": "generic customer list template", "lacks": "stores sites and phone numbers but has no equipment age, no agreement book, no tune-up windows and no renewal rate"},
    {"what": "single-sheet quote calculator", "lacks": "prices one job but cannot show agreement profit by plan, member against non-member revenue or the sign-ups needed"},
    {"what": "pen-and-paper job book", "lacks": "keeps no equipment history, so aged equipment, missed tune-ups and lapsed agreements never show up"}]
guide = [
    'Open Start and type your company name and your own limits in the yellow cells: the equipment age that makes a replacement lead, the renewal rate you want, the technicians who run tune-ups and the cost of a reminder.',
    'Check Agreement Plans, Technicians and Equipment Types. They hold your plans, your lead technicians and the replacement ticket of each equipment type.',
    'List every customer on Customer Sites by site reference, area and phone, and every piece of equipment on Equipment with type, install date, make, model and serial. Age and the lead score fill in by themselves.',
    'Enter each maintenance agreement on Agreements and each renewal that came due on Renewals. Days left, the renewal flag and the ranking of renewals due fill in by themselves.',
    'Plan each tune-up on Tune-up Visits with its window, planned date, date done and status. Behind, overdue and the value of the visit calculate themselves.',
    'Write each reminder you send on Campaign List with its channel and whether it booked a tune-up or sold an agreement. Campaign Results counts them by month.',
    'Type the month starts on Agreement Book by Month, Visits Due by Month and Campaign Results. The counts, the recurring revenue and the rates calculate themselves.',
    'Type the profit inputs on Agreement Profit and Member Revenue from your own jobs, and the share you expect to replace on Equipment by Age Band.',
    f'Use the {len(tools)} tools: each answers one question with a verdict. Change the yellow inputs to try another plan, price, channel or number of technicians.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Sites, Equipment and Agreements Dashboard and the Charts every week. A one-person owner-operator with one van uses the same sheets as the customer book; a shop with a dispatcher uses the dispatcher columns.']
listing = {"title": "HVAC and Plumbing Contractor Excel Template: Customer Sites, Equipment, Maintenance Agreements, Tune-up Schedule, Renewals",
    "headline": "Your customer book: sites, equipment, maintenance agreements and tune-ups",
    "tags": ["hvac template", "plumbing template", "agreement tracker", "tune-up schedule", "customer book", "equipment records", "contractor excel", "service business", "renewal tracker", "membership plan", "aged equipment", "field service", "tradesman"],
    "description": ("Run the customer side of an HVAC and plumbing contractor business in one Excel workbook. Built for an owner-run residential and light-commercial service shop with 1 to 15 technicians, an office manager who also dispatches, and a van for each lead technician. "
        "A one-person owner-operator with one van uses the same sheets as a customer book; a shop with a dispatcher uses the dispatcher columns.\n\n"
        "Customer Sites holds every site by reference, area, site type and phone, with no personal names. Equipment keeps type, fuel, install date, make, model, serial and last service, and works out the age, a lead score and a call now, mail or hold verdict. "
        "Agreements, Renewals and Tune-up Visits hold the maintenance agreement book: plan, price, renewal date, status, the two seasonal windows and what is behind. The Agreement Book by Month shows new, renewed, ended and running agreements with monthly recurring revenue and your renewal rate.\n\n"
        f"{len(tools)} tools answer weekly questions with a clear verdict: an aged equipment lead list, renewals ranked by value, the open tune-up window against last year, tune-up months against technician hours, agreement profit by plan, a pre-season campaign planner with cost per booked tune-up, a lapse analyser and a 12-month recurring revenue forecast. "
        f"Print {len(forms)} sheets and {len(documents)} documents such as the agreement summary and the renewal notice, follow {len(checklists)} checklists and send {len(messages)} ready text messages to customers, landlord accounts, technicians, your office, your equipment supplier and the accountant.\n\n"
        "This is part six of the HVAC and Plumbing Contractor suite. A standard .xlsx workbook with no macros and no per-technician fee: you keep your data. A demo copy full of sample data and a blank copy are included. It helps you keep track of your business and does not promise results."),
    "features": ["Customer sites by reference, area and phone, never by name", "Equipment records with age, lead score and a call or mail verdict", "Aged equipment lead list ranked for the week", "Maintenance agreement book with plan, price, renewal date and status",
                 "Renewals ranked by value with a call-by date and the revenue at risk", "Tune-up window tracker against the same point last year", "Tune-up months against technician hours, over capacity or too empty", "Agreement profit by plan with a price up, hold or add a visit verdict",
                 "Pre-season campaign planner with cost per booked tune-up", "12-month recurring revenue forecast with base, best and worst", f"{len(tools)} decision tools with verdicts", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
HINTS = {}

TH = {  # table title and hint overrides (limits: title 60, hint 200)
 'sites': 'One row per customer site: reference, area, site type, account, phone, equipment and jobs; oldest equipment, last service and open tune-ups fill in. A reference, never a name.',
 'equipment': 'One row per piece of equipment: type, fuel, install date, make, model, serial and last service; age, lead score and the call now, mail or hold verdict fill in. No technical data.',
 'agreements': 'One row per maintenance agreement, a yearly plan with two tune-ups: plan, price, dates and status; days left, renewal flag and monthly revenue fill in by themselves.',
 'visits_month': 'One row per month: visits due and done, hours needed against the technician hours free after the season work, slack and the open window gap fill in by themselves.',
 'plan_profit': 'One row per plan and site type: visit cost, travel and discount from your own jobs; profit, margin and the profit on follow-on repairs fill in by themselves.',
 'campaign': 'One row per reminder sent before a tune-up window: date, channel, booked and agreement sold; last service, equipment age, cost and next window start fill in by themselves.',
 'age_bands': 'One row per age band and type: records counted from Equipment, the share you expect to replace (set your own) and the replacements and revenue that follow.',
 'attach': 'One row per technician and period: the eligible jobs you count; agreements sold, attach rate and bonus cost fill in from the Agreements sheet.'}
for _t in tables:
    if _t['key'] in TH: _t['hint'] = TH[_t['key']]
TOOLH = {
 'aged_leads': 'Type the age that makes a lead and your win share: aged records, replacement value, the top leads of the week and a call now, mail or hold verdict.',
 'site_lookup': 'Type a site reference: area, phone, equipment with oldest age and last service, agreement plan and renewal date, jobs and revenue. No personal data.',
 'age_band_view': 'Type the spread and your install crew capacity: records by age band, replacements expected next year and their revenue, base, best and worst.',
 'book_health': 'Type the change you call flat: running agreements now against 12 months ago, recurring revenue, renewal rate against target and a verdict.',
 'renew_calls': 'Type the share you expect to keep: renewals due this month, fees at risk, those past the date and the ten to call first with days left.',
 'lapse_analyser': 'Pick a plan and a win-back share: agreements ended in 12 months, fees lost, reasons noted, the plan with the highest lapse rate and a verdict.',
 'attach_rate': 'Pick a technician: agreements sold over eligible jobs against your target, bonus cost, best technician and the sales needed, with a verdict.',
 'signups_needed': 'Type the fixed cost of the program and a recurring revenue goal: profit of an average agreement, agreements needed and the sign-ups a month.',
 'window_tracker': 'Type your amber and red gaps: the open window, visits planned, done and behind, the share against last year, visits to book and a traffic light.',
 'tuneup_schedule': 'Type technicians, visit hours and an empty load: 12 months of visits due against free technician hours, over-capacity and empty months.',
 'visit_overdue': 'Type the share you expect to rebook: visits whose window ended with no visit, their value and the ten to call first ranked by plan value.',
 'slow_filler': 'Type technicians, visit hours, the share bookable and a visit value: free hours of the slow months, tune-ups that fit and revenue added.',
 'plan_profit_tool': 'Pick a plan and a price change: visit, travel and discount cost, profit and margin, follow-on profit and a price up, hold or add a visit verdict.',
 'member_value': 'Type your margin: revenue per member site against a non-member site, the yearly value of a member and the break-even plan price.',
 'price_test': 'Pick a plan, a rise and the extra lapses you fear: revenue and profit change, the break-even lapse increase and a raise or hold verdict.',
 'campaign_plan': 'Type equipment age, months since service and channel: sites to remind, booked rate from your history, cost per booked tune-up and a verdict.',
 'campaign_results': 'Pick a channel and days back: reminders, booked tune-ups, cost per booked tune-up against the shop average and the cheapest channel.',
 'agr_forecast': 'Type the renewal rate, sign-ups and price: recurring revenue 6 and 12 months ahead and over 12 months, base, best and worst.'}
TOOLT = {'site_lookup': 'Everything on one site, no personal data', 'age_band_view': 'Replacements to expect next year by age band', 'member_value': 'Member value and break-even plan price', 'price_test': 'Agreement price test with a break-even lapse', 'agr_forecast': 'Recurring revenue for the next 12 months'}
for _t in tools:
    _t['hint'] = TOOLH[_t['key']]
    if _t['key'] in TOOLT: _t['title'] = TOOLT[_t['key']]
s = spec(id=f'{SUITE}-p6', slug='hvac-plumbing-agreements-sites', profession='HVAC and Plumbing Contractor', name='Sites, Equipment and Agreements',
         tagline='Your customer book: sites, equipment, maintenance agreements and tune-ups', price_usd=29,
         colors={"primary": "#1F4E5F", "accent": "#E07A3F"}, settings=settings, lists=base_lists + ck_lists(), tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 6, "of": 8, "focus": "Sites, equipment and agreements"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hv6.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']), 'lists', len(s['lists']))
