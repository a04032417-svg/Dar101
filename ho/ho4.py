"""Home Management suite - part 4: Home Maintenance and Repairs."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho4_lists import *
from ho4_tables import settings, tables, R, YES, OKS, DUES, OVD, A1w, A2w, TRw, OPEN, WAITING, FIXED, MSD, MT, LG, RP, CT, TM, AP, CS, RO, AS, OR_, N12, LL_TOK
from ho4_tools import tools, WIN, OVN, TASKS_ALL, SOVD, OPN, TW
import ho4_data as D

NOTE = "Sample wording: adapt it to your own household."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
def LKD(t, idc, c): return 'IFERROR(IF(%s=0,"",%s),"")' % (LK(t, idc, c), LK(t, idc, c))
SG = ['Adult', 'Trade']
SG2 = ['Adult 1', 'Adult 2']

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('task_sheet', 'Maintenance Task Sheet', 'One task with its interval and next due date', 'maintenance.task_id', F(
        ('Task', 'maintenance.task'), ('Area', 'maintenance.area'), ('Season', 'maintenance.season'), ('Interval, days (typical)', 'maintenance.interval_days'), ('Assigned', 'maintenance.assigned'),
        ('Typical cost line', 'maintenance.typical_cost'), ('Safety check', 'maintenance.safety'), ('Minutes', 'maintenance.minutes'), ('Last done', 'maintenance.last_done'), ('Next due', 'maintenance.next_due'),
        ('Days to due', 'maintenance.days_to_due'), ('Overdue days', 'maintenance.overdue_days'), ('Status', 'maintenance.status')) + [
        FF('Tasks in the same area', 'COUNTIFS(%s,%s)' % (MT('area'), LK('maintenance', 'task_id', 'area')), 'int'),
        FF('Times done in the log', 'COUNTIFS(%s,{pick})' % LG('task_id'), 'int'),
        FF('Typical cost lines a year', 'IFERROR(ROUND(365/%s*%s,0),0)' % (LK('maintenance', 'task_id', 'interval_days'), LK('maintenance', 'task_id', 'typical_cost')), 'money'),
        FF('Minutes a year', 'IFERROR(ROUND(365/%s*%s,0),0)' % (LK('maintenance', 'task_id', 'interval_days'), LK('maintenance', 'task_id', 'minutes')), 'int'),
        FF('Next due after this one', 'IFERROR(%s+%s,"")' % (LK('maintenance', 'task_id', 'next_due'), LK('maintenance', 'task_id', 'interval_days')), 'date')]),
    FORM('task_done_sheet', 'Task Done Sheet', 'One task done, by whom and at what cost line', 'maintenance_log.log_id', F(
        ('Task', 'maintenance_log.task'), ('Done on', 'maintenance_log.done'), ('Done by', 'maintenance_log.who'), ('Cost line', 'maintenance_log.cost'), ('Note', 'maintenance_log.note'),
        ('Year', 'maintenance_log.year'), ('Interval, days', 'maintenance_log.interval'), ('On time, 1 or 0', 'maintenance_log.on_time')) + [
        FF('Days since it was done', '{today}-%s' % LK('maintenance_log', 'log_id', 'done'), 'int'),
        FF('Times this task was done, in all', 'COUNTIFS(%s,%s)' % (LG('task_id'), LK('maintenance_log', 'log_id', 'task_id')), 'int'),
        FF('Cost lines of this task, in all', 'SUMIFS(%s,%s,%s)' % (LG('cost'), LG('task_id'), LK('maintenance_log', 'log_id', 'task_id')), 'money'),
        FF('Tasks done by that person, last 30 days', 'COUNTIFS(%s,%s,%s,1)' % (LG('who'), LK('maintenance_log', 'log_id', 'who'), LG('last30')), 'int')]),
    FORM('repair_report_sheet', 'Repair Report Sheet', 'One repair: room, issue, trade and days open', 'repairs.repair_id', F(
        ('Reported on', 'repairs.date'), ('Room', 'repairs.room'), ('Issue', 'repairs.issue'), ('Trade called', 'repairs.trade'), ('Status', 'repairs.status'), ('Quote', 'repairs.quote'),
        ('Year', 'repairs.year'), ('Days open', 'repairs.days_open'), ('Repeat in the same room, 1 or 0', 'repairs.repeat'), ('Phone of the trade', 'repairs.tphone')) + [
        FF('Repairs in the room, repeat window', 'COUNTIFS(%s,%s,%s,">="&({today}-{set:repeat_days}),%s,"<="&{today})' % (RP('room'), LK('repairs', 'repair_id', 'room'), RP('date'), RP('date')), 'int'),
        FF('Repairs by the same trade, in all', 'COUNTIFS(%s,%s)' % (RP('trade'), LK('repairs', 'repair_id', 'trade')), 'int'),
        FF('Open repairs in the home', OPN, 'int')]),
    FORM('repair_update_sheet', 'Repair Update Sheet', 'One repair: status, quote, cost and fixed date', 'repairs.repair_id', F(
        ('Issue', 'repairs.issue'), ('Status', 'repairs.status'), ('Quote', 'repairs.quote'), ('Cost line', 'repairs.cost'), ('Fixed on', 'repairs.fixed_on'), ('Warranty used', 'repairs.warranty_used'),
        ('Days open', 'repairs.days_open'), ('Reported on', 'repairs.date')) + [
        FF('Cost against the quote', 'IFERROR(%s-%s,0)' % (LK('repairs', 'repair_id', 'cost'), LK('repairs', 'repair_id', 'quote')), 'money'),
        FF('Days past the chase days in Settings', 'IF(%s=1,MAX(0,%s-{set:wait_days}),0)' % (LK('repairs', 'repair_id', 'open'), LK('repairs', 'repair_id', 'days_open')), 'int'),
        FF('Waiting for a trade in the home', 'COUNTIFS(%s,%s)' % (RP('status'), WAITING), 'int')]),
    FORM('trade_call_sheet', 'Trade Call Sheet', 'One trade: phone, last used and cost last time', 'contacts.contact_id', F(
        ('Name', 'contacts.name'), ('Kind', 'contacts.kind'), ('Trade or contact type', 'contacts.trade'), ('Phone', 'contacts.phone'), ('Email', 'contacts.email'), ('Last used', 'contacts.last_used'),
        ('Cost last time', 'contacts.cost_last'), ('Would use again', 'contacts.would_use_again'), ('Days since last used', 'contacts.days_since')) + [
        FF('Repairs by this trade in the log', 'COUNTIFS(%s,%s)' % (RP('trade'), LK('contacts', 'contact_id', 'trade')), 'int'),
        FF('Cost lines of those repairs', 'SUMIFS(%s,%s,%s)' % (RP('cost'), RP('trade'), LK('contacts', 'contact_id', 'trade')), 'money'),
        FF('Idle 12 months or more, 1 or 0', 'IFERROR(%s+0,0)' % LK('contacts', 'contact_id', 'idle'), 'int')]),
    FORM('quote_sheet', 'Quote Comparison Sheet', 'One quote against the cost and the trade average', 'repairs.repair_id', F(
        ('Issue', 'repairs.issue'), ('Room', 'repairs.room'), ('Trade called', 'repairs.trade'), ('Quote', 'repairs.quote'), ('Cost line', 'repairs.cost'), ('Status', 'repairs.status')) + [
        FF('Quotes of the same trade', 'COUNTIFS(%s,%s,%s,">0")' % (RP('trade'), LK('repairs', 'repair_id', 'trade'), RP('quote')), 'int'),
        FF('Average quote of the same trade', 'IFERROR(ROUND(AVERAGEIFS(%s,%s,%s,%s,">0"),0),0)' % (RP('quote'), RP('trade'), LK('repairs', 'repair_id', 'trade'), RP('quote')), 'money'),
        FF('Cost line against the quote', 'IFERROR(%s-%s,0)' % (LK('repairs', 'repair_id', 'cost'), LK('repairs', 'repair_id', 'quote')), 'money'),
        FF('Quote against the average of the trade', 'IFERROR(%s/AVERAGEIFS(%s,%s,%s,%s,">0")-1,0)' % (LK('repairs', 'repair_id', 'quote'), RP('quote'), RP('trade'), LK('repairs', 'repair_id', 'trade'), RP('quote')), 'pct')]),
    FORM('filter_change_sheet', 'Filter Change Sheet', 'One filter: interval, stock and order-before date', 'consumables.item', F(
        ('Size or code', 'consumables.code'), ('Where used', 'consumables.where_used'), ('Change every, days (typical)', 'consumables.interval_days'), ('Last changed', 'consumables.last_changed'),
        ('Units in stock', 'consumables.units'), ('Kept in', 'consumables.stored'), ('Task ID', 'consumables.task_id')) + [
        FF('Next change', 'IFERROR(INDEX(%s,MATCH({pick},%s,0)),"")' % (RO('next_change'), RO('item')), 'date'),
        FF('Order before', 'IFERROR(INDEX(%s,MATCH({pick},%s,0)),"")' % (RO('reorder_before'), RO('item')), 'date'),
        FF('Days to the change', 'IFERROR(INDEX(%s,MATCH({pick},%s,0)),"")' % (RO('days_to'), RO('item')), 'int'),
        FF('Stock flag', 'IFERROR(INDEX(%s,MATCH({pick},%s,0))&"","")' % (RO('flag'), RO('item')), 'text')]),
    FORM('appliance_sheet', 'Appliance Service Sheet', 'One appliance: last and next service, cost a year', 'appliances.item_id', F(
        ('Item', 'appliances.item'), ('Room', 'appliances.room'), ('Purchase date', 'appliances.purchase_date'), ('Warranty end', 'appliances.warranty_end'), ('Service task ID', 'appliances.service_task_id')) + [
        FF('Last service', 'IFERROR(INDEX(%s,MATCH({pick},%s,0)),"")' % (AS('last_service'), AS('item_id')), 'date'),
        FF('Next service', 'IFERROR(INDEX(%s,MATCH({pick},%s,0)),"")' % (AS('next_service'), AS('item_id')), 'date'),
        FF('Status', 'IFERROR(INDEX(%s,MATCH({pick},%s,0))&"","")' % (AS('status'), AS('item_id')), 'text'),
        FF('Done by', 'IFERROR(INDEX(%s,MATCH({pick},%s,0))&"","")' % (AS('who'), AS('item_id')), 'text'),
        FF('Services logged', 'IFERROR(INDEX(%s,MATCH({pick},%s,0)),0)' % (AS('services'), AS('item_id')), 'int'),
        FF('Repairs logged', 'IFERROR(INDEX(%s,MATCH({pick},%s,0)),0)' % (AS('repairs'), AS('item_id')), 'int'),
        FF('Cost lines per year of age', 'IFERROR(INDEX(%s,MATCH({pick},%s,0)),0)' % (AS('yearly_cost'), AS('item_id')), 'money')]),
    FORM('landlord_sheet', 'Landlord Request Sheet', 'For renters: one request and when to ask again', 'repairs.repair_id', F(
        ('First reported', 'repairs.date'), ('Room', 'repairs.room'), ('Request', 'repairs.issue'), ('Status', 'repairs.status'), ('Days waiting', 'repairs.days_open')) + [
        FF('Days until you ask again', 'IF(%s=1,MAX(0,{set:wait_days}-%s),0)' % (LK('repairs', 'repair_id', 'open'), LK('repairs', 'repair_id', 'days_open')), 'int'),
        FF('Days past the ask-again days', 'IF(%s=1,MAX(0,%s-{set:wait_days}),0)' % (LK('repairs', 'repair_id', 'open'), LK('repairs', 'repair_id', 'days_open')), 'int'),
        FF('Open requests in all', OPN, 'int'),
        FF('Phone of the landlord or agent', 'IFERROR(INDEX(%s,MATCH(%s,%s,0))&"","")' % (CT('phone'), LL_TOK, CT('trade')), 'text')]),
    FORM('seasonal_sheet', 'Seasonal Check Sheet', 'One season: tasks, due, minutes and cost lines', 'season_view.season', F(
        ('Tasks in the season', 'season_view.tasks'), ('Due in the next 90 days', 'season_view.due_90')) + [
        FF('Overdue now', 'COUNTIFS(%s,{pick},%s,%s)' % (MT('season'), MT('status'), OVD), 'int'),
        FF('Minutes of the tasks', 'SUMIFS(%s,%s,{pick})' % (MT('minutes'), MT('season')), 'int'),
        FF('Typical cost lines', 'SUMIFS(%s,%s,{pick})' % (MT('typical_cost'), MT('season')), 'money'),
        FF('Tasks for adult 1', 'COUNTIFS(%s,{pick},%s,%s)' % (MT('season'), MT('assigned'), A1w), 'int'),
        FF('Tasks for adult 2', 'COUNTIFS(%s,{pick},%s,%s)' % (MT('season'), MT('assigned'), A2w), 'int'),
        FF('Tasks for a trade', 'COUNTIFS(%s,{pick},%s,%s)' % (MT('season'), MT('assigned'), TRw), 'int')]),
    FORM('contact_card', 'Contact Card', 'One household member or contact', 'team.member_id', F(
        ('Name', 'team.name'), ('Role', 'team.role'), ('Group', 'team.group'), ('Phone', 'team.phone'), ('Note', 'team.note'), ('Since', 'team.start')) + [
        FF('Days in the household or contacts', '{today}-%s' % LK('team', 'member_id', 'start'), 'int'),
        FF('Contacts in the same group', 'COUNTIFS(%s,%s)' % (TM('group'), LK('team', 'member_id', 'group')), 'int'),
        FF('Open repairs in the home', OPN, 'int')]),
    FORM('safety_sheet', 'Safety Check Sheet', 'One safety check: interval and next due', 'maintenance.task_id', F(
        ('Task', 'maintenance.task'), ('Interval, days (typical)', 'maintenance.interval_days'), ('Assigned', 'maintenance.assigned'), ('Minutes', 'maintenance.minutes'),
        ('Last done', 'maintenance.last_done'), ('Next due', 'maintenance.next_due'), ('Days to due', 'maintenance.days_to_due'), ('Status', 'maintenance.status')) + [
        FF('Times done in the log', 'COUNTIFS(%s,{pick})' % LG('task_id'), 'int'),
        FF('Safety checks overdue in the plan', SOVD, 'int'),
        FF('Alarm test every, days (Settings)', '{set:alarm_test_days}', 'int'),
        FF('Alarm batteries every, days (Settings)', '{set:alarm_battery_days}', 'int')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('schedule_doc', 'Schedule for the Next 12 Months', 'Maintenance schedule for the next 12 months, task by task', 'next12.task_id', [
        'Maintenance schedule of {set:household} for the next 12 months, dated {today}. Task: {col:next12.task}, every {col:next12.interval} days (typical, check the manual).',
        'Next due: {col:next12.next_due}. Typical cost line: {col:next12.typical}. Times in the next 12 months: {col:next12.total}. Cost lines in the next 12 months: {col:next12.cost12}.',
        'The repeat dates are calculated from the last done date and the interval; nothing here is a deadline.',
        'Tick when done: [ ]   Done on: ________'], SG2, NOTE),
    DOC('overdue_doc', 'Most Overdue List, Fridge Page', 'Most overdue tasks, the fridge page', 'overdue.rank', [
        'Most overdue list of {set:household}, dated {today}. Place {col:overdue.rank}: {col:overdue.task}, area {col:overdue.area}.',
        'Overdue days: {col:overdue.overdue_days}. Assigned: {col:overdue.assigned}. Typical cost line: {col:overdue.typical_cost}. Minutes: {col:overdue.minutes}. Minutes so far down the list: {col:overdue.cum_min}.',
        'The ranking is calculated from the dates you typed; intervals are typical, check the manual.',
        'Done on: ________   By: ________'], SG2, NOTE),
    DOC('season_doc', 'Seasonal Checklist Page', 'Seasonal checklist page for one season', 'season_view.season', [
        'Seasonal checklist of {set:household} for {col:season_view.season}, dated {today}. Tasks in the season: {col:season_view.tasks}. Due in the next 90 days: {col:season_view.due_90}.',
        'Walk the house and the garden with the Maintenance sheet open, filter the season and tick each task. Intervals are typical, check the manual and your local rules.',
        'Gutters and drains [ ]   Filters [ ]   Alarms [ ]   Taps and vents [ ]   Doors and windows [ ]   Garden [ ]',
        'Extra jobs found: ________________________________'], SG2, NOTE),
    DOC('repair_report_doc', 'Repair Report to a Trade', 'Repair report to send to a trade', 'repairs.repair_id', [
        'Repair report of {set:household}, dated {today}. To {col:repairs.tfirst}, trade {col:repairs.trade}. Issue: {col:repairs.issue}, in the {col:repairs.room}, first noticed on {col:repairs.date}.',
        'Item: {col:repairs.item}. Warranty ends: {col:repairs.warranty_end}. Quote so far: {col:repairs.quote}. Status: {col:repairs.status}. Days open: {col:repairs.days_open}.',
        'Please send a quote before you start, and tell us the earliest day you can come.',
        'Phone of the trade: {col:repairs.tphone}.'], SG, NOTE),
    DOC('landlord_doc', 'Request to the Landlord', 'Maintenance request to the landlord, for renters', 'repairs.repair_id', [
        'Maintenance request of {set:household}, dated {today}. Request: {col:repairs.issue}, in the {col:repairs.room}, first reported on {col:repairs.date}.',
        'Status: {col:repairs.status}. Days open: {col:repairs.days_open}. We would like a date for the visit. Previous quote or note: {col:repairs.quote}.',
        'Please confirm a date in writing. If there is no answer after {set:wait_days} days we will write again.',
        'Sent on: ________   Answer received on: ________'], SG, NOTE),
    DOC('filters_doc', 'Filters and Consumables Page', 'Filters and consumables page: change dates and stock', 'reorder.item', [
        'Filters and consumables of {set:household}, dated {today}. Item: {col:reorder.item}, kept in {col:reorder.stored}.',
        'Next change: {col:reorder.next_change}, days to the change: {col:reorder.days_to}, status: {col:reorder.change_status}. Order before: {col:reorder.reorder_before}. Units in stock: {col:reorder.units}. Stock flag: {col:reorder.flag}.',
        'Change intervals are typical, check the manual and the label.',
        'Changed on: ________   Units bought: ________'], SG2, NOTE),
    DOC('appliance_doc', 'Appliance Service History Page', 'Appliance service history page', 'app_service.item_id', [
        'Service history of {set:household}, dated {today}. Item: {col:app_service.item}, service task {col:app_service.task_id}, done by {col:app_service.who}.',
        'Last service: {col:app_service.last_service}. Next service: {col:app_service.next_service}. Status: {col:app_service.status}. Services logged: {col:app_service.services}. Repairs logged: {col:app_service.repairs}.',
        'Cost lines in all: {col:app_service.life_cost}, about {col:app_service.yearly_cost} per year of age ({col:app_service.age_years} years).',
        'Notes: ____________________________________'], SG, NOTE),
    DOC('year_doc', 'Repairs and Trades Year Summary', 'Repairs and trades summary for the year', 'cost_year.year', [
        'Repairs and trades summary of {set:household} for {col:cost_year.year}.',
        'Maintenance cost lines: {col:cost_year.maint_cost}. Repair cost lines: {col:cost_year.repair_cost}. Both are simple cost lines typed in the Maintenance log and the Repairs sheet.',
        'Look at the Repairs by room and year sheet and the Trades used sheet for the rooms and the trades behind these totals.',
        'What shall we change next year? ________'], SG2, NOTE),
    DOC('trades_doc', 'Trades and Contacts Page', 'Trades and contacts page', 'contacts.contact_id', [
        'Contact page of {set:household}, dated {today}. {col:contacts.name}, {col:contacts.trade}. Phone: {col:contacts.phone}. Email: {col:contacts.email}.',
        'Last used: {col:contacts.last_used}. Cost last time: {col:contacts.cost_last}. Would use again: {col:contacts.would_use_again}.',
        'Keep the numbers of the trades near the door of the utility room.',
        'Note: ____________________________________'], SG2, NOTE),
    DOC('quote_doc', 'Quote Comparison Page', 'Quote comparison page', 'repairs.repair_id', [
        'Quote comparison of {set:household}, dated {today}. Issue: {col:repairs.issue}, in the {col:repairs.room}. Trade called: {col:repairs.trade}.',
        'Quote: {col:repairs.quote}. Cost line: {col:repairs.cost}. Status: {col:repairs.status}.',
        'Write the other quotes here and compare what is included, not only the price. Quote 2: ________   Quote 3: ________',
        'Chosen: ________   Date: ________'], SG, NOTE),
    DOC('alarm_log_doc', 'Alarm Test Log Page', 'Alarm test log page, dates only', 'maintenance.task_id', [
        'Alarm test log of {set:household}, dated {today}. Task: {col:maintenance.task}, every {col:maintenance.interval_days} days (typical, check the manual).',
        'Last done: {col:maintenance.last_done}. Next due: {col:maintenance.next_due}. Minutes: {col:maintenance.minutes}.',
        'Tested on: ________   ________   ________   ________   ________   ________',
        'Dates only. Check the manufacturer\'s instructions and your local rules for the test steps.'], SG2, NOTE),
    DOC('handover_doc', 'House-Sitter Handover Notes', 'House handover notes for a house-sitter', 'team.member_id', [
        'Handover notes of {set:household} for {col:team.first_name}, dated {col:team.from_date}. Tasks due in the next 7 days: {col:team.due_n}. Repairs open: {col:team.open_n}, the oldest is {col:team.oldest_issue}, {col:team.oldest_days} days.',
        'What to check: the post and the bins, the taps and the heating, the alarms, the plants. Please do not start any repair; call the number on the contact page.',
        'The numbers of the trades and of the household are on the Trades and Contacts page.',
        'Keys left with: ________   Back on: ________'], ['Household', 'House-sitter'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('monthly_safety', 'Monthly Safety Checks Steps', 'maintenance_log', 'maintenance_log.done', [('Press the test button of each alarm', 0), ('Check the filters of the heating and the extractor', 1), ('Look at the escape route and the shut-off valve', 2), ('Type the dates in the Maintenance log', 3)]),
    CHK('spring_check', 'Spring House Check Steps', 'maintenance', 'maintenance.last_done', [('Open the Season Prep Planner for spring', 0), ('Check the roof and the gutters from the ground', 1), ('Check the doors, the windows and the seals', 2), ('Clean the outdoor drains', 3), ('Type the dates in the Maintenance log', 5)]),
    CHK('summer_check', 'Summer Outdoor Check Steps', 'maintenance', 'maintenance.last_done', [('Open the Season Prep Planner for summer', 0), ('Check the fence, the gate and the shed', 1), ('Clean the outdoor taps and hoses', 2), ('Service the lawn mower', 3), ('Type the dates in the Maintenance log', 5)]),
    CHK('autumn_check', 'Autumn Heating Gutters Steps', 'maintenance', 'maintenance.last_done', [('Open the Season Prep Planner for autumn', 0), ('Book the yearly heating service', 0), ('Clear the gutters', 2), ('Bleed the radiators if the manual says so', 3), ('Change the heating filter', 4), ('Type the dates in the Maintenance log', 6)]),
    CHK('winter_prep', 'Winter Prep Steps', 'maintenance', 'maintenance.last_done', [('Open the Season Prep Planner for winter', 0), ('Insulate the outdoor taps', 1), ('Check the heating and the vents', 2), ('Know where the water shut-off valve is', 3), ('Type the dates in the Maintenance log', 5)]),
    CHK('before_trade', 'Before a Trade Visit Steps', 'repairs', 'repairs.date', [('Write the issue and when it started', 0), ('Ask for the quote before the work starts', 1), ('Clear the way to the work area', 2), ('Tell the neighbour or the grandparent if someone holds a key', 2), ('Print the Repair Report to a Trade', 2)]),
    CHK('after_repair', 'After a Repair Steps', 'repairs', 'repairs.fixed_on', [('Check the repair together with the trade', 0), ('Type the cost line and the fixed date in the Repairs sheet', 0), ('Keep the receipt and the paperwork', 1), ('Tidy the work area', 1), ('Note whether you would use the trade again', 2)]),
    CHK('appliance_round', 'Appliance Service Round Steps', 'appliances', 'appliances.purchase_date', [('Open the Appliance Service History', 0), ('Pick the appliances due in the next 60 days', 0), ('Book the services or do the cleaning tasks', 7), ('Type the dates in the Maintenance log', 14)]),
    CHK('filter_round', 'Quarterly Filter Round Steps', 'consumables', 'consumables.last_changed', [('Open the Filters and Consumables sheet', 0), ('Check the units in stock', 1), ('Order what is low', 2), ('Change the filters (typical, check the manual)', 5), ('Type the change dates', 6)]),
    CHK('landlord_followup', 'Landlord Follow-Up Steps', 'repairs', 'repairs.date', [('Write the request with the date and the room', 0), ('Ask again after the days set in Settings', 14), ('Escalate in writing if there is no date', 28), ('Keep every message with its date', 28)]),
    CHK('year_end', 'Year-End Review Steps', 'maintenance_log', 'maintenance_log.done', [('Print the Repairs and Trades Summary for the Year', 0), ('Read the repeat repairs', 1), ('Decide which tasks change interval', 2), ('Choose the trades to keep', 3)]),
    CHK('single_start', 'Single Adult First Plan Steps', 'team', 'team.start', [('Replace the demo tasks with your own', 0), ('Type the last done date of each task', 1), ('Read Most Overdue First', 2), ('Set the due soon window in Settings', 3), ('Type what you did in the Maintenance log', 7)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('he_book', 'Heating engineer: book the service', 'maintenance', 'maintenance.heat_phone', 'Hello, we would like to book {task}, our last visit was on {last_done}. {household}'),
    M('he_confirm', 'Heating engineer: confirm the visit', 'team', 'team.eng_phone', 'Hello {first_name}, please confirm the visit on {next_date} at {at_time}. {household}'),
    M('he_pressure', 'Heating engineer: pressure dropped', 'team', 'team.eng_phone', 'Hello {first_name}, the pressure dropped again on {from_date}, when can you come? {household}'),
    M('pl_started', 'Plumber: the issue started', 'repairs', 'repairs.pl_open', 'Hello {tfirst}, the {issue} in the {room} started on {date}, when can you visit? {household}'),
    M('pl_quote', 'Plumber: please send a quote', 'repairs', 'repairs.pl_open', 'Hello {tfirst}, please send a quote for {issue} in the {room}. {household}'),
    M('pl_thanks', 'Plumber: thank you for the visit', 'repairs', 'repairs.pl_done', 'Hello {tfirst}, thank you for the visit on {fixed_on}, the quote was {quote}. {household}'),
    M('el_look', 'Electrician: the issue needs a look', 'repairs', 'repairs.el_phone', 'Hello {tfirst}, the {issue} in the {room} needs a look, when are you free? {household}'),
    M('el_confirm', 'Electrician: confirm the visit', 'team', 'team.elec_phone', 'Hello {first_name}, please confirm the visit on {next_date} at {at_time}. {household}'),
    M('ap_stopped', 'Appliance repairer: the item stopped', 'repairs', 'repairs.ap_open', 'Hello {tfirst}, the {item} stopped on {date}, the warranty ends on {warranty_end}, when can you come? {household}'),
    M('ap_quote', 'Appliance repairer: quote first', 'repairs', 'repairs.ap_open', 'Hello {tfirst}, please send a quote for {issue} before you start. {household}'),
    M('ap_again', 'Appliance repairer: repair did not hold', 'repairs', 'repairs.ap_done', 'Hello {tfirst}, the repair on {fixed_on} did not hold, can you come back? {household}'),
    M('ll_report', 'Landlord or agent: a repair is needed', 'repairs', 'repairs.ll_open', 'Hello, the {issue} in the {room} needs a repair, first reported on {date}. {household}'),
    M('ll_chase', 'Landlord or agent: please confirm a date', 'repairs', 'repairs.ll_open', 'Hello, it is {days_open} days since we reported {issue}, please confirm a date. {household}'),
    M('ll_visit', 'Landlord or agent: confirm the visit', 'team', 'team.ll_phone', 'Hello {first_name}, please confirm the trade visit on {next_date} between {at_time} and {end_time}. {household}'),
    M('ll_thanks', 'Landlord or agent: thank you', 'repairs', 'repairs.ll_done', 'Hello, thank you, the repair of {issue} was done on {fixed_on}. {household}'),
    M('mech_quote', 'Car mechanic: a quote is needed', 'team', 'team.mech_phone', 'Hello {first_name}, we need a quote for a service and a check, the older car is available on {next_date}. {household}'),
    M('nb_key', 'Neighbour: hold the spare key', 'team', 'team.nb_phone', 'Hello {first_name}, a trade comes on {next_date} at {at_time}, please hold the spare key. {household}'),
    M('ro_gutter', 'Roofer: look at the gutter joint', 'repairs', 'repairs.ro_phone', 'Hello {tfirst}, please look at {issue} in the {room}, we noticed it on {date}. {household}'),
    M('ha_fence', 'Handyman: quote for the fence panel', 'repairs', 'repairs.ha_phone', 'Hello {tfirst}, please quote for {issue}, loose since {date}. {household}'),
    M('pe_signs', 'Pest controller: signs in the garage', 'repairs', 'repairs.pe_phone', 'Hello {tfirst}, we saw signs in the {room} on {date}, please call us. {household}'),
    M('a1_overdue', 'Adult 1: a task is overdue', 'maintenance', 'maintenance.a1_od_phone', 'Hi, {task} is {overdue_days} days overdue, can you do it by {agree_by}? {household}'),
    M('a1_alarm', 'Adult 1: the alarm test is due', 'maintenance', 'maintenance.a1_alarm_phone', 'Hi, {task} is due on {next_due}, it takes {minutes} minutes. {household}'),
    M('a2_due', 'Adult 2: a task is due', 'maintenance', 'maintenance.a2_due_phone', 'Hi, {task} is due on {next_due}, the cost line is about {typical_cost}. {household}'),
    M('a2_filter', 'Adult 2: the filter change is overdue', 'reorder', 'reorder.a2_phone', 'Hi, the change of {item} is overdue, the new one is in the {stored}. {household}'),
    M('a2_heating', 'Adult 2: be home for the heating service', 'team', 'team.a2_phone', 'Hi {first_name}, the heating service is on {next_date}, please be home between {at_time} and {end_time}. {household}'),
    M('c1_alarm', 'Child 1: help with the alarm test', 'maintenance', 'maintenance.c1_phone', 'Hi, please help with the alarm test on {next_due}, you press the button. {household}'),
    M('c2_alarm', 'Child 2: we test the alarms', 'maintenance', 'maintenance.c2_phone', 'Hi, on {next_due} we test the alarms, it will be loud. {household}'),
    M('gp_trade', 'Grandparent: a trade comes', 'team', 'team.gp_phone', 'Hello {first_name}, a trade comes on {next_date}, can you be at the house between {at_time} and {end_time}? {household}'),
    M('gp_thanks', 'Grandparent: thanks for letting in', 'team', 'team.gp_phone', 'Hello {first_name}, thank you for letting the trade in this week, dated {from_date}. {household}'),
    M('hm_week', 'Household member: tasks of the week', 'team', 'team.hm_phone', 'Hi {first_name}, the maintenance list for the week of {from_date} has {due_n} tasks. {household}'),
    M('hm_repairs', 'Household member: repairs are open', 'team', 'team.hm_phone', 'Hi {first_name}, {open_n} repairs are open, the oldest is {oldest_issue} at {oldest_days} days. {household}'),
    M('hm_filter', 'Household member: filter ordered', 'reorder', 'reorder.hm_phone', 'Hi, the new {item} is ordered, change it by {next_change}. {household}'),
    M('hm_autumn', 'Household member: autumn checks', 'team', 'team.hm_phone', 'Hi {first_name}, the autumn checks start on {sat_date}, {autumn_n} tasks. {household}'),
    M('hm_year', 'Household member: year review', 'team', 'team.hm_phone', 'Hi {first_name}, year review of maintenance for {year}: {done_year} done, {repairs_year} repairs. {household}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def W_(c, op, v): return (c, op, v)
LAST90 = '%s,">="&({today}-89),%s,"<="&{today}' % (RP('fixed_on'), RP('fixed_on'))
kpis = [
    KPI('Maintenance tasks in the plan', TASKS_ALL, 'int'),
    KPI('Tasks overdue', OVN, 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Tasks due in the next 14 days', 'COUNTIFS(%s)' % WIN('next_due', 14), 'int'),
    KPI('Tasks due in the next 30 days', 'COUNTIFS(%s)' % WIN('next_due', 30), 'int'),
    KPI('Tasks done, last 30 days', 'COUNTIFS(%s,1)' % LG('last30'), 'int'),
    KPI('Tasks done this year', 'COUNTIFS(%s,1)' % LG('this_year'), 'int'),
    KPI('Most overdue task, days', 'MAX(%s)' % MT('overdue_days'), 'int'),
    KPI('Average days overdue', 'IFERROR(ROUND(AVERAGEIFS(%s,%s,%s),0),0)' % (MT('overdue_days'), MT('status'), OVD), 'int'),
    KPI('Overdue share of all tasks', 'IFERROR(%s/%s,0)' % (OVN, TASKS_ALL), 'pct'),
    KPI('Safety checks overdue', SOVD, 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Tasks needing a trade, next 60 days', 'COUNTIFS(%s,%s,1)' % (WIN('next_due', 60), MT('trade_task')), 'int'),
    KPI('Cost lines of tasks due in 30 days', 'SUMIFS(%s,%s)' % (MT('typical_cost'), WIN('next_due', 30)), 'money'),
    KPI('Maintenance cost lines, last 30 days', 'SUMIFS(%s,%s,1)' % (LG('cost'), LG('last30')), 'money'),
    KPI('Maintenance cost lines this year', 'SUMIFS(%s,%s,1)' % (LG('cost'), LG('this_year')), 'money'),
    KPI('Busiest month ahead, tasks', 'MAX(%s)' % R('month_load', 'tasks_due'), 'int'),
    KPI('Filters due for change, next 30 days', 'COUNTIFS(%s,">="&{today},%s,"<="&({today}+29))' % (RO('next_change'), RO('next_change')), 'int'),
    KPI('Consumables below one unit in stock', 'COUNTIFS(%s,"<1",%s,"<>")' % (RO('units'), RO('item')), 'int'),
    KPI('Consumables to reorder, next 14 days', 'COUNTIFS(%s,"<="&({today}+13),%s,"<1")' % (RO('reorder_before'), RO('units')), 'int'),
    KPI('Appliances and systems', 'COUNTIFS(%s,"<>")' % AP('item_id'), 'int'),
    KPI('Appliance services overdue', 'COUNTIFS(%s,%s)' % (AS('status'), OVD), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Next appliance service, days', 'IFERROR(SMALL(%s,COUNTIFS(%s,"<0")+1),"")' % (AS('days_to'), AS('days_to')), 'int'),
    KPI('Open repairs', OPN, 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Repairs waiting for a trade', 'COUNTIFS(%s,"<>",%s,%s)' % (RP('repair_id'), RP('status'), WAITING), 'int'),
    KPI('Oldest open repair, days', 'IFERROR(INDEX(%s,1),0)' % OR_('days_open'), 'int'),
    KPI('Repairs fixed, last 90 days', 'COUNTIFS(%s)' % LAST90, 'int'),
    KPI('Repair cost lines this year', 'SUMIFS(%s,%s,YEAR({today}))' % (RP('cost'), RP('year')), 'money'),
    KPI('Repeat-repair rooms', 'COUNTIFS(%s,">=2")' % R('repeat_repairs', 'repairs12'), 'int'),
    KPI('Repairs with the warranty used this year', 'COUNTIFS(%s,%s,%s,YEAR({today}))' % (RP('warranty_used'), YES, RP('year')), 'int'),
    KPI('Trades marked would use again', 'COUNTIFS(%s,1,%s,%s)' % (CT('is_trade'), CT('would_use_again'), YES), 'int'),
    KPI('Trades not used for 12 months or more', 'COUNTIFS(%s,1)' % CT('idle'), 'int'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Maintenance Dashboard", "kpis": kpis,
    "monthly": {"title": "Maintenance and repair cost lines per month", "date": "maintenance_log.done", "series": [
        {"label": "Maintenance cost lines", "sum": "maintenance_log.cost", "date": "maintenance_log.done"}, {"label": "Repair cost lines", "sum": "repairs.cost", "date": "repairs.date"}]},
    "breakdowns": [{"title": "Tasks by area", "by": "maintenance.area", "value": "maintenance.typical_cost", "agg": "count"}, {"title": "Repairs by room", "by": "repair_room_year.room", "value": "repair_room_year.repairs", "agg": "sum"},
                   {"title": "Repair cost lines by trade", "by": "trades_used.trade", "value": "trades_used.cost_lines", "agg": "sum"}, {"title": "Tasks by season", "by": "maintenance.season", "value": "maintenance.typical_cost", "agg": "count"}]}
insights = {"filters": [{"label": "Area", "list": "area"}, {"label": "Room", "list": "room"}, {"label": "Trade", "list": "trade"}],
    "gauges": [
        {"title": "Tasks done on time this year", "num": AGG('count', 'maintenance_log', where=[W_('this_year', '=', 1), W_('on_time', '=', 1)]), "den": AGG('count', 'maintenance_log', where=[W_('this_year', '=', 1)])},
        {"title": "Tasks not overdue", "num": AGG('count', 'maintenance', where=[W_('status', '<>', OVD)]), "den": AGG('count', 'maintenance')},
        {"title": "Safety checks up to date", "num": AGG('count', 'maintenance', where=[W_('safety', '=', YES), W_('status', '<>', OVD)]), "den": AGG('count', 'maintenance', where=[W_('safety', '=', YES)])},
        {"title": "Repairs fixed against reported", "num": AGG('count', 'repairs', where=[W_('status', '=', FIXED)]), "den": AGG('count', 'repairs')},
        {"title": "Filters changed before the due date", "num": AGG('count', 'maintenance_log', where=[W_('is_filter', '=', 1), W_('on_time', '=', 1)]), "den": AGG('count', 'maintenance_log', where=[W_('is_filter', '=', 1)])},
        {"title": "Appliances serviced on schedule", "num": AGG('count', 'app_service', where=[W_('status', '<>', OVD)]), "den": AGG('count', 'app_service')}],
    "charts": [
        CHART('Tasks due per month, next 12', 'column', 'month_load.ahead', [AGG('sum', 'month_load', 'month_load.tasks_due', label='Tasks due')]),
        CHART('Tasks by area', 'bar', 'maintenance.area', [AGG('count', 'maintenance', label='Tasks')]),
        CHART('Tasks by season', 'bar', 'maintenance.season', [AGG('count', 'maintenance', label='Tasks')]),
        CHART('Tasks by assigned person', 'bar', 'maintenance.assigned', [AGG('count', 'maintenance', label='Tasks')]),
        CHART('Overdue days by area', 'bar', 'maintenance.area', [AGG('sum', 'maintenance', 'maintenance.overdue_days', label='Overdue days')]),
        CHART('Maintenance done per month', 'column', 'month', [AGG('count', 'maintenance_log', date='maintenance_log.done', label='Tasks done')]),
        CHART('Maintenance cost lines per month', 'column', 'month', [AGG('sum', 'maintenance_log', 'maintenance_log.cost', date='maintenance_log.done', label='Cost lines')]),
        CHART('Tasks done by who per month', 'column', 'month', [AGG('count', 'maintenance_log', date='maintenance_log.done', where=[W_('who', '=', tok('mwho', w))], label=w) for w in MWHO]),
        CHART('Typical cost lines by area', 'bar', 'maintenance.area', [AGG('sum', 'maintenance', 'maintenance.typical_cost', label='Typical cost lines')]),
        CHART('Filters changed per month', 'column', 'month', [AGG('count', 'maintenance_log', date='maintenance_log.done', where=[W_('is_filter', '=', 1)], label='Filters changed')]),
        CHART('Appliance services per month', 'column', 'month', [AGG('count', 'maintenance_log', date='maintenance_log.done', where=[W_('svc', '=', 1)], label='Services')]),
        CHART('Repairs per month', 'column', 'month', [AGG('count', 'repairs', date='repairs.date', label='Repairs')]),
        CHART('Repairs by room', 'bar', 'repair_room_year.room', [AGG('sum', 'repair_room_year', 'repair_room_year.repairs', label='Repairs')]),
        CHART('Repairs by trade', 'bar', 'trades_used.trade', [AGG('sum', 'trades_used', 'trades_used.calls', label='Repairs')]),
        CHART('Repair cost lines by room', 'bar', 'repair_room_year.room', [AGG('sum', 'repair_room_year', 'repair_room_year.cost_lines', label='Cost lines')]),
        CHART('Repair cost lines per year', 'column', 'repair_room_year.year', [AGG('sum', 'repair_room_year', 'repair_room_year.cost_lines', label='Cost lines')]),
        CHART('Repairs by status', 'bar', 'repairs.status', [AGG('count', 'repairs', label='Repairs')]),
        CHART('Average days open by status', 'bar', 'repairs.status', [AGG('avg', 'repairs', 'repairs.days_open', label='Days open')]),
        CHART('Trade calls per year', 'column', 'trades_used.year', [AGG('sum', 'trades_used', 'trades_used.calls', label='Calls')]),
        CHART('Cost lines by trade', 'bar', 'trades_used.trade', [AGG('sum', 'trades_used', 'trades_used.cost_lines', label='Cost lines')]),
        CHART('Repairs with the warranty used per year', 'column', 'repair_room_year.year', [AGG('sum', 'repair_room_year', 'repair_room_year.warranty_n', label='Warranty used')]),
        CHART('Maintenance and repair cost lines per month', 'column', 'month', [AGG('sum', 'maintenance_log', 'maintenance_log.cost', date='maintenance_log.done', label='Maintenance'), AGG('sum', 'repairs', 'repairs.cost', date='repairs.date', label='Repairs')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Most overdue task", "why": "tasks ranked by days overdue with the person and the typical cost line, calculated from the last done date and the interval", "where": "Most Overdue Task"},
    {"name": "Next due date of every task", "why": "a forecast from the last done date and the interval: how many tasks, minutes and cost lines fall in the days you choose", "where": "Next Due Date Of Every Task"},
    {"name": "Busiest month ahead", "why": "the repeat dates of every task counted for the next 12 months, so you see the busy month before it arrives", "where": "Busiest Month Ahead"},
    {"name": "Safety checks due", "why": "alarm tests, alarm batteries, the escape plan and the shut-off valve check from their typed intervals, typical, check the manual", "where": "Safety Checks Due"},
    {"name": "Repeat repair finder", "why": "the rooms with more than one repair in the window, with the latest issue and the cost lines", "where": "Repeat Repair Finder"},
    {"name": "Which trade to call", "why": "pick the kind of issue and read the trade, the name, the phone, the last used date and whether you would use them again", "where": "Which Trade To Call"},
    {"name": "Overdue catch-up plan", "why": "the minutes of the overdue tasks spread over the minutes a day you can give, with the date you would be clear", "where": "Overdue Catch-Up Plan"},
    {"name": "Cost against your own history", "why": "maintenance and repair cost lines from 1 January to today against the same dates last year, from your own log", "where": "Cost Against Own History"}]
competitors = [
    {"what": "single-slice home maintenance checklist template", "lacks": "a list of tasks with ticks and no last done date, so no next due date, no overdue days and no ranking of what to do first"},
    {"what": "home-care app with a yearly renewal", "lacks": "charges every year and keeps the household in an account, with no repeat-repair finder and no trade directory with last used and cost last time"},
    {"what": "printable seasonal chores sheet", "lacks": "a fixed list for every house: no intervals of your own, no 12-month calendar of repeat dates and no busiest month"},
    {"what": "simple repair log spreadsheet", "lacks": "records the repair but not the days open, the repeat in the same room, the warranty used or the trade to call next time"},
    {"what": "single-sheet home organizer", "lacks": "one tab for everything: no filters and consumables with an order-before date, no appliance service history and no landlord request tracker for renters"}]
guide = [
    'Start here: this workbook shows what the house needs and when. Open Settings on the Start sheet and type your household name, the due soon window and the days to order consumables before a change in the yellow cells.',
    'Replace the demo data: clear the sample rows of Maintenance, Maintenance log, Repairs, Appliances and systems, Trades directory and Filters and consumables and type your own; keep the lists and settings. Grey cells calculate by themselves.',
    'Maintenance: type each task with its area, season, interval in days, who does it, the typical cost line and the date it was last done; next due, days to due and status calculate. Intervals are typical, check the manual and your local rules.',
    'Maintenance log: type each task done with the date, who did it and the cost line. The done-on-time figures, the cost lines per year and the appliance service history all read this one sheet.',
    'Repairs: type each repair with the date, room, issue, trade called, quote, cost line, status and the date it was fixed; days open, repeat repairs and the totals by room and year calculate.',
    'Calculated and ranked sheets (Master Schedule, Most Overdue First, Next 12 Months, Open Repairs by Days Open): type the ranks or the names once and the rest fills in.',
    'Weekly routine, Sunday: plan the meals, check the shopping list, rotate the chores, glance at the calendar and read Most Overdue First.',
    'Monthly routine: pantry and freezer check, maintenance due in the next 30 days, renewals in the next 90 days, a project check, and the monthly safety checks.',
    'Use the 18 tools for the questions of the month: what do we do first, which month is busiest, what to reorder, which trade to call, which room keeps needing repairs, what a new interval does to the next due date.',
    'Print 12 sheets and 12 documents, follow 12 checklists and tap a message link to send a text with the details already written in; the tables with a phone column carry the links.',
    'A single adult uses the Maintenance, Repairs and Filters sheets unchanged and leaves the rows about children and a grandparent empty; Most Overdue First still ranks the tasks.',
    'Renters: read "a trade" as "a maintenance request to the landlord", keep the same dates, use the Landlord Request Tracker and the repairs log to show how long a request has been open, and leave out the owner-only tasks.',
    'Why a workbook: one flat price, no yearly renewal, your data stays with you, nothing to link or re-connect, no ads and no upsell. It works in Excel and Google Sheets with no macros, no add-ins and no accounts.',
    'What this is not: not a safety service, not a reminder app, not medical, legal or financial advice. Every date, rank and cost line is calculated from your entries: typical, check the manufacturer\'s instructions and your local rules.']
assert 5 <= len(guide) <= 20
listing = {"title": "Home Maintenance Schedule and Repairs Log Excel Template: Next Due Dates, Filters, Appliance Service, Trades Directory",
    "headline": "See what the house needs, what is overdue and which repairs keep coming back",
    "tags": ["maintenance schedule", "maintenance list", "repairs log", "home repair tracker", "filter change", "smoke alarm test", "appliance service", "seasonal tasks", "trades directory", "landlord requests", "home management", "excel template", "no subscription"],
    "description": ("Run the upkeep of your home from one Excel workbook: a master schedule of 50 maintenance tasks (filters, alarm tests, gutters, the boiler or furnace service, appliance cleaning, the garden and the seasonal jobs) with the area, the season, the interval in days and the date it was last done, "
        "an automatic next due date, a status of OK, due soon or overdue and a most overdue first list. Built for a single adult, a couple or a family, owners or renters, with a household of two adults, two children and a grandparent as the sample.\n\n"
        "The next 12 months are projected for every task, with the repeat dates counted month by month and the busiest month named; filters and consumables show the next change, the units in stock and the date to order before; the appliance and system service history shows who did it, the cost lines and the next service. "
        "The repairs log records the date, room, issue, trade called, quote, cost line and status, counts the days open, flags repeat repairs in the same room and totals the cost lines by room and year; the trades directory keeps the last used date, the cost last time and whether you would use them again.\n\n"
        "Renters read a trade as a maintenance request to the landlord and keep the same dates; the landlord request tracker shows when to ask again and when to escalate. "
        "18 tools answer the questions of the month: what do we do first, which month is busiest, which safety checks are due, which trade to call, what to reorder, how long to clear the overdue list and whether this year's cost lines are above your own history. "
        "Print 12 sheets and 12 documents, follow 12 checklists and send 34 ready text messages to the plumber, the electrician, the heating engineer, the landlord, the neighbour and the household.\n\n"
        "This is part four of the eight-part Home Management suite. A standard .xlsx workbook with no macros, no accounts and no yearly renewal, with a demo copy full of sample data to explore first. "
        "Every interval is typical, check the manual and your local rules. It is a home kit, not a safety service, and gives no medical or legal advice."),
    "features": ["50 maintenance tasks with next due date, status and ranking", "Most overdue first list with minutes and cost lines", "Next 12 months of repeat dates and the busiest month", "Filters and consumables with an order-before date",
                 "Appliance and system service history with who did it", "Repairs log with days open and repeat repairs in the same room", "Trades directory with last used, cost last time and would use again", "Landlord request tracker for renters",
                 f"{len(tools)} tools for the questions of the month", f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages",
                 "No macros, no accounts, no yearly renewal"]}
SUITE_ID = SUITE
s = spec(id=f'{SUITE_ID}-p4', slug='home-management-maintenance', profession='Home Management', name='Home Maintenance and Repairs',
         tagline='See what the house needs, what is overdue and which repairs repeat', price_usd=29,
         colors={"primary": "#3E5C76", "accent": "#E07A5F"}, settings=settings, lists=lists_base + verdict_lists(), tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE_ID, "part": 4, "of": 8, "focus": "What the house needs and when: maintenance schedule, filters, appliance service, repairs and trades"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
TT = {'maintenance': 'Every task with its interval, last done and next due', 'repairs': 'Every repair: what, where, trade, quote and cost line', 'appliances': 'Appliances and systems with their service task',
      'contacts': 'Trades and contacts: last used, cost, use again', 'consumables': 'Filters and consumables with change intervals', 'next12': 'Every task and its repeat dates, next 12 months',
      'reorder': 'When to change and when to order the next one', 'app_service': 'Last and next service of every appliance'}
SL = {'filter_days': 'Filter change every, days (typical)', 'alarm_test_days': 'Alarm test every, days (typical)', 'alarm_battery_days': 'Alarm batteries every, days (typical)',
      'service_months': 'Boiler or furnace service, months (typical)', 'grace_days': 'Days after due that still count as on time'}
for t in tables:
    t['title'] = TT.get(t['key'], t['title']); t['rows'] = max(50, t['rows'])
for st in settings: st['label'] = SL.get(st['key'], st['label'])
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ho4.en.json'))
    names = [t['sheet'] for t in tables] + [t['sheet'] for t in tools] + [f['sheet'] for f in forms] + [d['sheet'] for d in documents]
    assert len(names) == len(set(names)), [n for n in names if names.count(n) > 1]
    assert all(len(n) <= 31 for n in names), [n for n in names if len(n) > 31]
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
