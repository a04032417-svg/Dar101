"""Short-term rental host suite - part 5: Maintenance, Damage and Safety."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from sr5_lists import *
from sr5_tables import settings, tables
from sr5_tools import tools

SUITE = 'fx-20261113-short-term-rental'
NOTE = "Sample wording: adapt it to your own practice and check your own local rules."
TS = lambda s: tok('tkst', s)
def F(*pairs): return [FV(a, b) for a, b in pairs]
forms = [
    FORM('ticket_sheet', 'Maintenance Ticket Sheet', 'Maintenance ticket with fix-by date and cost', 'tickets.ticket_id', F(
        ('Reported on', 'tickets.reported_on'), ('Unit', 'tickets.unit'), ('Kind', 'tickets.kind'), ('Priority', 'tickets.priority'), ('Source', 'tickets.source'), ('Handyperson', 'tickets.handyperson'), ('Status', 'tickets.status'),
        ('Parts cost', 'tickets.parts_cost'), ('Labour cost', 'tickets.labour_cost'), ('Cost', 'tickets.cost'), ('Guest impact', 'tickets.guest_impact'), ('Fix by', 'tickets.fix_by'), ('Days open', 'tickets.days_open'),
        ('Ticket check', 'tickets.chk'), ('Next check-in at the unit', 'tickets.next_checkin'), ('Handyperson phone', 'tickets.handyperson_phone')) + [
        FF('Tickets on this unit in 12 months', 'COUNTIFS({range:tickets.unit},INDEX({range:tickets.unit},MATCH({pick},{range:tickets.ticket_id},0)),{range:tickets.reported_on},">"&({today}-365))', 'int')]),
    FORM('claim_sheet', 'Damage Claim Sheet', 'Damage claim with deposit and amount to claim', 'claims.claim_id', F(
        ('Reported on', 'claims.reported_on'), ('Booking', 'claims.booking_id'), ('Unit', 'claims.unit'), ('Guest', 'claims.guest'), ('Channel', 'claims.channel'), ('Damage', 'claims.damage'), ('Claimed amount', 'claims.claimed_amount'),
        ('Deposit held', 'claims.deposit_held'), ('To claim after the deposit', 'claims.to_claim'), ('Repair cost', 'claims.repair_cost'), ('Status', 'claims.status'), ('Paid amount', 'claims.paid_amount'), ('Unrecovered amount', 'claims.unrecovered'),
        ('Days pending', 'claims.days_pending'), ('Claim check', 'claims.claim_flag')) + [FF('Claimed so far on this unit', 'SUMIFS({range:claims.claimed_amount},{range:claims.unit},INDEX({range:claims.unit},MATCH({pick},{range:claims.claim_id},0)))', 'money')]),
    FORM('deposit_sheet', 'Deposit Release Sheet', 'Deposit with the amount to return', 'deposits.dep_id', F(
        ('Booking', 'deposits.booking_id'), ('Unit', 'deposits.unit'), ('Guest', 'deposits.guest'), ('Check-out', 'deposits.check_out'), ('Deposit amount', 'deposits.amount'), ('Kept amount', 'deposits.kept_amount'), ('Reason for keeping', 'deposits.reason'),
        ('Days since check-out', 'deposits.days_since'), ('Held now', 'deposits.held'), ('Returned to the guest', 'deposits.returned'), ('Deposit status', 'deposits.status'), ('Guest phone', 'deposits.guest_phone'))),
    FORM('safety_sheet', 'Safety Check Sheet', 'Safety check with the next date', 'safety.safety_id', F(
        ('Date', 'safety.date'), ('Unit', 'safety.unit'), ('Item', 'safety.item'), ('Result', 'safety.result'), ('Next check', 'safety.next_check'), ('Done by', 'safety.done_by'), ('Days to next check', 'safety.days_left'), ('Latest check', 'safety.latest'),
        ('Check status', 'safety.status'))),
    FORM('service_sheet', 'Service Booking Sheet', 'Recurring service with next due date', 'services.service_id', F(
        ('Unit', 'services.unit'), ('Service', 'services.service'), ('Every months', 'services.every_months'), ('Last done', 'services.last_done'), ('Cost', 'services.cost'), ('Next due', 'services.next_due'), ('Days to due', 'services.days_to_due'),
        ('Service status', 'services.status'), ('Cost per year', 'services.cost_year'), ('Owner phone', 'services.owner_phone'))),
    FORM('quote_sheet', 'Repair Quote Sheet', 'Repair quote with decision', 'quotes.quote_id', F(
        ('Date', 'quotes.date'), ('Unit', 'quotes.unit'), ('Work', 'quotes.work'), ('Supplier', 'quotes.supplier'), ('Amount', 'quotes.amount'), ('Decision', 'quotes.decision'), ('Days to decide', 'quotes.days_waiting'), ('Owner approval', 'quotes.limit_flag'),
        ('Quote check', 'quotes.flag'), ('Supplier phone', 'quotes.supplier_phone'), ('Owner phone', 'quotes.owner_phone'))),
    FORM('parts_sheet', 'Parts Order Sheet', 'Parts order with delivery check', 'parts.part_id', F(
        ('Date', 'parts.date'), ('Ticket', 'parts.ticket_id'), ('Unit', 'parts.unit'), ('Part', 'parts.part'), ('Quantity', 'parts.qty'), ('Price each', 'parts.unit_price'), ('Order value', 'parts.amount'), ('Supplier', 'parts.supplier'),
        ('Delivery date', 'parts.delivery_date'), ('Order status', 'parts.status'), ('Delivery check', 'parts.flag'), ('Handyperson', 'parts.handyperson'))),
    FORM('incident_sheet', 'Incident Sheet', 'Incident with action and days to close', 'incidents.inc_id', F(
        ('Date', 'incidents.date'), ('Unit', 'incidents.unit'), ('Kind', 'incidents.kind'), ('Guest', 'incidents.guest'), ('Action taken', 'incidents.action'), ('Days to close', 'incidents.days_open'), ('Incident status', 'incidents.status'))),
    FORM('appliance_sheet', 'Appliance Sheet', 'Appliance with warranty and age', 'appliances.app_id', F(
        ('Unit', 'appliances.unit'), ('Appliance', 'appliances.appliance'), ('Bought on', 'appliances.bought_on'), ('Warranty until', 'appliances.warranty_until'), ('Cost', 'appliances.cost'), ('Warranty left, days', 'appliances.warranty_left'),
        ('Age in years', 'appliances.age_years'), ('Warranty check', 'appliances.status'), ('Age check', 'appliances.age_flag'))),
    FORM('capex_sheet', 'Capex Request Sheet', 'Capital spend request with payback', 'capex.cx_id', F(
        ('Unit', 'capex.unit'), ('Item', 'capex.item'), ('Planned month', 'capex.planned_month'), ('Cost', 'capex.cost'), ('Saving per year', 'capex.saving_per_year'), ('Reason', 'capex.reason'), ('Status', 'capex.status'),
        ('Months to go', 'capex.months_to'), ('Payback, months', 'capex.payback_months'), ('Payback check', 'capex.flag'), ('Owner phone', 'capex.owner_phone'))),
]
assert len(forms) == 10
documents = [
    DOC('job_sheet', 'Maintenance Job Sheet', 'Maintenance job sheet for one ticket', 'tickets.ticket_id', [
        'Maintenance job sheet of {set:company}, dated {today}. Ticket {col:tickets.ticket_id} reported on {col:tickets.reported_on} for {col:tickets.unit}. Kind: {col:tickets.kind}. Source: {col:tickets.source}.',
        'Priority: {col:tickets.priority}. Fix by {col:tickets.fix_by}. Status: {col:tickets.status}. Handyperson: {col:tickets.handyperson}. Guest affected: {col:tickets.guest_impact}. Next check-in at the unit: {col:tickets.next_checkin}.',
        'Parts cost {col:tickets.parts_cost}, labour cost {col:tickets.labour_cost}, total {col:tickets.cost}. Cost check: {col:tickets.cost_flag}. Ticket check: {col:tickets.chk}.',
        'Photos before and after the work are added to the ticket. The handyperson signs when the work is done and the host checks the result before the next guest arrives.'], ['Host', 'Handyperson'], NOTE),
    DOC('claim_summary', 'Damage Claim Summary', 'Damage claim summary with evidence list', 'claims.claim_id', [
        'Damage claim summary of {set:company}, dated {today}. Claim {col:claims.claim_id} on booking {col:claims.booking_id}, unit {col:claims.unit}, guest {col:claims.guest}, channel {col:claims.channel}.',
        'Damage found on {col:claims.reported_on}: {col:claims.damage}. Repair cost {col:claims.repair_cost}. Amount claimed {col:claims.claimed_amount}. Deposit held {col:claims.deposit_held}. To claim after the deposit {col:claims.to_claim}.',
        'Status: {col:claims.status}. Paid so far {col:claims.paid_amount}. Not recovered {col:claims.unrecovered}. Days pending {col:claims.days_pending}. Claim check: {col:claims.claim_flag}.',
        'Evidence to attach: photos of the damage, photos taken at check-in, the repair invoice or quote, the messages with the guest and the booking record. Keep every file for the claim.'], ['Host', 'Co-host'], NOTE),
    DOC('claim_letter', 'Damage Claim Letter', 'Damage claim letter to a guest', 'claims.claim_id', [
        'Letter of {set:company}, dated {today}. Dear {col:claims.guest},',
        'Thank you for staying in {col:claims.unit}. After check-out we found damage: {col:claims.damage}. We took photos and kept the repair estimate. The repair cost is {col:claims.repair_cost}.',
        'We ask for {col:claims.claimed_amount}, of which {col:claims.deposit_held} is covered by the deposit you paid. The amount still to pay is {col:claims.to_claim}. Please reply within 7 days if you want to discuss the photos or the amount.',
        'We would like to settle this directly and fairly. Thank you for your help.'], ['Host', 'Guest'], NOTE),
    DOC('safety_report', 'Safety Check Report', 'Safety check report for one check', 'safety.safety_id', [
        'Safety check report of {set:company}, dated {today}. Check {col:safety.safety_id} on {col:safety.date} at {col:safety.unit}.',
        'Item: {col:safety.item}. Result: {col:safety.result}. Done by {col:safety.done_by}. Next check on {col:safety.next_check}, in {col:safety.days_left} days. Check status: {col:safety.status}.',
        'If the result needs a repair, a ticket is opened the same day and the unit is not rented until the item is safe. Check your own local rules for the checks you must keep on record.',
        'The person who did the check signs below and the host keeps the report with the unit file.'], ['Host', 'Handyperson'], NOTE),
    DOC('service_schedule', 'Unit Service Schedule', 'Service schedule for one unit', 'units.unit_id', [
        'Service schedule of {set:company}, dated {today}. Unit {col:units.unit_id}: {col:units.name} in {col:units.city}, owner {col:units.owner}.',
        'Services in the schedule: {col:units.services_n}. Overdue or due soon: {col:units.services_due}. Service cost per year: {col:units.service_cost_year}. Safety checks overdue: {col:units.safety_overdue}.',
        'Maintenance cost over the last 12 months: {col:units.cost_12m} for {col:units.nights_12m} booked nights, which is {col:units.cost_per_night} a night. Check: {col:units.cost_flag}. Open tickets: {col:units.tickets_open}.',
        'Each service is booked before its due date and written in the Service Schedule sheet with the new last-done date.'], ['Host', 'Owner'], NOTE),
    DOC('quote_approval', 'Repair Quote Approval', 'Repair quote approval for the owner', 'quotes.quote_id', [
        'Repair quote approval of {set:company}, dated {today}. Quote {col:quotes.quote_id} of {col:quotes.date} for {col:quotes.unit}.',
        'Work: {col:quotes.work}. Supplier: {col:quotes.supplier}. Amount: {col:quotes.amount}. Owner approval check: {col:quotes.limit_flag}. Decision so far: {col:quotes.decision}.',
        'The owner approves any repair above the repair limit before the work starts. Days since the quote was asked: {col:quotes.days_waiting}.',
        'The owner signs to approve or decline the quote. The host writes the decision in the Repair Quotes sheet.'], ['Host', 'Owner'], NOTE),
    DOC('appliance_doc', 'Appliance and Warranty Record', 'Appliance and warranty record for one appliance', 'appliances.app_id', [
        'Appliance and warranty record of {set:company}, dated {today}. Appliance {col:appliances.app_id}: {col:appliances.appliance} in {col:appliances.unit}.',
        'Bought on {col:appliances.bought_on} for {col:appliances.cost}. Warranty until {col:appliances.warranty_until}, {col:appliances.warranty_left} days left. Warranty check: {col:appliances.status}.',
        'Age {col:appliances.age_years} years. Age check: {col:appliances.age_flag}. Keep the receipt and the manual with this record.',
        'A repair needed during the warranty is claimed from the seller before any handyperson is paid.'], ['Host', 'Handyperson'], NOTE),
    DOC('cost_report', 'Monthly Maintenance Report', 'Monthly maintenance cost report for one unit month', 'cost_unit.cu_id', [
        'Monthly maintenance cost report of {set:company}, dated {today}. Month {col:cost_unit.month}, unit {col:cost_unit.unit} ({col:cost_unit.city}).',
        'Tickets: {col:cost_unit.tickets}. Parts cost {col:cost_unit.parts_cost}. Labour cost {col:cost_unit.labour_cost}. Total {col:cost_unit.cost}.',
        'Booked nights {col:cost_unit.booked_nights}. Cost per booked night {col:cost_unit.cost_per_night}. Cost check: {col:cost_unit.flag}.',
        'The report goes to the owner and the accountant with the invoices of the month.'], ['Host', 'Accountant'], NOTE),
    DOC('incident_report', 'Incident Report', 'Incident report for one incident', 'incidents.inc_id', [
        'Incident report of {set:company}, dated {today}. Incident {col:incidents.inc_id} on {col:incidents.date} at {col:incidents.unit}.',
        'What happened: {col:incidents.kind}. Guest: {col:incidents.guest}. Action taken: {col:incidents.action}.',
        'Days to close: {col:incidents.days_open}. Status: {col:incidents.status}.',
        'Write what was seen and said, attach photos, and tell the owner. For any injury or legal question, check your own local rules and contact your liability insurance.'], ['Host', 'Co-host'], NOTE),
    DOC('capex_doc', 'Capex Plan Sheet', 'Capital spending plan for one item', 'capex.cx_id', [
        'Capital spending plan of {set:company}, dated {today}. Plan {col:capex.cx_id}: {col:capex.item} for {col:capex.unit}.',
        'Planned month {col:capex.planned_month}, in {col:capex.months_to} months. Cost {col:capex.cost}. Saving per year {col:capex.saving_per_year}. Payback {col:capex.payback_months} months. Check: {col:capex.flag}.',
        'Reason: {col:capex.reason}. Status: {col:capex.status}.',
        'The owner approves the spend before it is ordered. The host reviews the payback after 12 months.'], ['Host', 'Owner'], NOTE),
]
assert len(documents) == 10
checklists = [
    CHK('new_ticket', 'New Ticket Handling Steps', 'tickets', 'tickets.reported_on', [('Write the ticket with photos and the unit', 0), ('Set the priority and the fix-by date', 0), ('Check the next check-in at the unit', 0), ('Send the ticket to the handyperson', 0), ('Tell the guest if they are affected', 0),
        ('Order parts if needed', 1), ('Confirm the visit date', 1), ('Tell the owner if the cost is over the repair limit', 2), ('Check the result with photos', 4), ('Close the ticket and thank the handyperson', 5)]),
    CHK('damage_found', 'Damage Found at Check-out Steps', 'claims', 'claims.reported_on', [('Take photos of the damage straight away', 0), ('Compare with the check-in photos', 0), ('Tell the guest in writing', 0), ('Open a ticket for the repair', 0), ('Collect an estimate or invoice', 2), ('Decide if the deposit covers it', 2), ('Start the claim', 3)]),
    CHK('claim_filing', 'Damage Claim Filing Steps', 'claims', 'claims.reported_on', [('Gather photos, estimate and messages', 0), ('Work out the amount to claim', 1), ('File the claim on the booking platform or send the letter to the guest', 2), ('Answer questions within 2 days', 4), ('Chase the claim if it waits too long', 14), ('Record the paid amount and the date', 21), ('Tell the owner the result', 22)]),
    CHK('deposit_release', 'Deposit Release Steps', 'deposits', 'deposits.check_out', [('Inspect the unit after check-out', 0), ('Compare with the check-in photos', 0), ('Decide the amount to keep, if any', 1), ('Write to the guest with the reason', 1), ('Return the deposit', 3), ('Record the release date', 3), ('Close the booking file', 7)]),
    CHK('safety_month', 'Monthly Safety Check Steps', 'safety', 'safety.date', [('List the checks due this month', 0), ('Test each smoke and carbon monoxide alarm', 1), ('Check fire extinguishers and gas appliances', 2), ('Test the door lock and the entry code', 2), ('Write each result in the sheet', 3), ('Open a ticket for any failed item', 3), ('Send the report to the host', 4)]),
    CHK('preseason', 'Pre-season Unit Check Steps', 'units', 'units.since', [('Walk through every room with the checklist', 0), ('Service the heating or air conditioning', 3), ('Test every appliance', 4), ('Replace worn linen and small items', 7), ('Check windows, blinds and balcony', 8), ('Clear the gutters and the exterior', 10), ('Update photos in the listing', 14)]),
    CHK('appliance_service', 'Appliance Service Steps', 'appliances', 'appliances.bought_on', [('Check the warranty date', 0), ('Clean filters and seals', 1), ('Run a test cycle', 2), ('Book a service if the age is high', 3), ('Write the date in the register', 4), ('Plan a replacement if repairs repeat', 30)]),
    CHK('lock_change', 'Lock and Key Change Steps', 'locks', 'locks.date', [('Change the entry code at once', 0), ('Test the new code at the door', 0), ('Tell the co-host and the cleaners', 0), ('Update the code in the guest messages', 1), ('Record the change in the log', 1), ('Replace the lock if a key was lost', 7)]),
    CHK('pest_exterior', 'Pest and Exterior Check Steps', 'pest', 'pest.date', [('Check kitchen, bathroom and entrance', 0), ('Check balcony, roof and gutters', 1), ('Look for damp, cracks and loose rails', 1), ('Record each finding', 2), ('Book the action for each finding', 3), ('Check again after the action', 30)]),
    CHK('capex_review', 'Quarterly Capex Review Steps', 'capex', 'capex.planned_month', [('List the plans for the next quarter', -30), ('Check the cost against the quote', -21), ('Check the payback of each plan', -14), ('Ask each owner to approve', -10), ('Order the items', -5), ('Check the result after the work', 30), ('Review the saving after 12 months', 365)]),
]
assert len(checklists) == 10
def M(key_, moment, table, phone, text): return MSG(key_, moment, table, phone, text)
messages = [
    M('hp_new', 'Handyperson: new ticket at a unit', 'tickets', 'tickets.handyperson_phone', 'Hello {handyperson}, new ticket {ticket_id} at {unit}: {kind}. Please fix by {fix_by}.'),
    M('hp_urgent', 'Handyperson: urgent, guest arrives', 'tickets', 'tickets.handyperson_phone', 'Hello {handyperson}, urgent: a guest arrives at {unit} on {next_checkin}. Ticket {ticket_id} must be done before then.'),
    M('hp_quote', 'Handyperson: please send a quote', 'quotes', 'quotes.supplier_phone', 'Hello {supplier}, please send a quote for {work} at {unit}. I need it by the end of the week.'),
    M('hp_part', 'Handyperson: the part arrived', 'parts', 'parts.handyperson_phone', 'Hello {handyperson}, the part {part} for {unit} arrived. Please book the repair for ticket {ticket_id}.'),
    M('hp_visit', 'Handyperson: your visit is confirmed', 'tickets', 'tickets.handyperson_phone', 'Hello {handyperson}, your visit at {unit} for ticket {ticket_id} is confirmed. The guest is {guest}.'),
    M('hp_photos', 'Handyperson: please add photos', 'tickets', 'tickets.handyperson_phone', 'Hello {handyperson}, please add photos before and after for ticket {ticket_id} at {unit}.'),
    M('hp_thanks', 'Handyperson: ticket closed, thanks', 'tickets', 'tickets.handyperson_phone', 'Hello {handyperson}, thank you. Ticket {ticket_id} at {unit} is closed. Total cost {cost}.'),
    M('hp_safety', 'Handyperson: a safety check is due', 'safety', 'safety.doer_phone', 'Hello {done_by}, a safety check is due at {unit}: {item}. Next check date {next_check}.'),
    M('g_sorry', 'Guest: sorry, we fix it today', 'tickets', 'tickets.guest_phone', 'Hello {guest}, we are sorry about the problem at {unit}. We are fixing it today and will tell you when it is done.'),
    M('g_visit', 'Guest: a handyperson will visit', 'tickets', 'tickets.guest_phone', 'Hello {guest}, a handyperson will visit {unit} by {fix_by} to fix the {kind} problem. Is there a time that suits you?'),
    M('g_damage', 'Guest: damage found after stay', 'claims', 'claims.guest_phone', 'Hello {guest}, after your stay at {unit} we found damage: {damage}. I will send you the photos and the repair cost.'),
    M('g_released', 'Guest: your deposit has been released', 'deposits', 'deposits.guest_phone', 'Hello {guest}, your deposit for {unit} is released. Amount returned: {returned}. Thank you for staying with us.'),
    M('g_keep', 'Guest: part of the deposit kept', 'deposits', 'deposits.guest_phone', 'Hello {guest}, we need to keep {kept_amount} of your deposit for {unit}: {reason}. I can send photos and the invoice.'),
    M('g_thanks', 'Guest: thank you for reporting the issue', 'tickets', 'tickets.guest_phone', 'Hello {guest}, thank you for telling us about the {kind} problem at {unit}. It helps us look after the place.'),
    M('c_impact', 'Co-host: a ticket affects the guest', 'tickets', 'tickets.cohost_phone', 'Hello, ticket {ticket_id} at {unit} affects the guest {guest}. Please keep them updated until {fix_by}.'),
    M('c_done', 'Co-host: the repair is done', 'tickets', 'tickets.cohost_phone', 'Hello, the repair at {unit} is done (ticket {ticket_id}). The unit is ready for the next guest.'),
    M('c_lock', 'Co-host: check the lock code', 'locks', 'locks.cohost_phone', 'Hello, please check the lock code at {unit}. Event on {date}: {event}. Code changed: {code_changed}.'),
    M('h_overdue', 'Host: a ticket is overdue', 'tickets', 'tickets.host_phone', 'Hello, ticket {ticket_id} at {unit} ({kind}) is overdue. It was due on {fix_by}. Handyperson: {handyperson}.'),
    M('h_claim', 'Host: a damage claim is waiting', 'claims', 'claims.host_phone', 'Hello, the damage claim {claim_id} of {claimed_amount} for {unit} is waiting. Days pending: {days_pending}.'),
    M('h_approved', 'Host: the claim was approved', 'claims', 'claims.host_phone', 'Hello, the claim {claim_id} for {unit} was approved. Amount claimed {claimed_amount}. Please check the payout.'),
    M('h_rejected', 'Host: claim rejected, check evidence', 'claims', 'claims.host_phone', 'Hello, the claim {claim_id} for {unit} was rejected. Please review the evidence for the amount of {claimed_amount}.'),
    M('h_safety', 'Host: a safety check is overdue', 'safety', 'safety.host_phone', 'Hello, the safety check {item} at {unit} was due on {next_check}. Status: {status}.'),
    M('h_report', 'Host: monthly report is ready', 'cost_unit', 'cost_unit.host_phone', 'Hello, the maintenance report for {month} at {unit} is ready: cost {cost}, cost per booked night {cost_per_night}.'),
    M('h_warranty', 'Host: a warranty is ending', 'appliances', 'appliances.host_phone', 'Hello, the warranty of the {appliance} at {unit} ends on {warranty_until}, in {warranty_left} days. Check it for faults now.'),
    M('o_cost', 'Owner: a repair at your unit costs', 'tickets', 'tickets.owner_phone', 'Hello, the repair at {unit} (ticket {ticket_id}, {kind}) costs {cost}. I will send the invoice with the monthly statement.'),
    M('o_quote', 'Owner: please approve the quote', 'quotes', 'quotes.owner_phone', 'Hello, please approve the quote of {amount} for {work} at {unit}. The supplier is {supplier}.'),
    M('o_claim', 'Owner: the damage claim for your unit', 'claims', 'claims.owner_phone', 'Hello, we filed a damage claim of {claimed_amount} for {unit}: {damage}. Status: {status}.'),
    M('a_costs', 'Accountant: costs for the month', 'cost_unit', 'cost_unit.accountant_phone', 'Hello, the maintenance costs for {month} at {unit} are attached: parts {parts_cost}, labour {labour_cost}, total {cost}.'),
]
assert len(messages) == 28
MS = 'DATE(YEAR({today}),MONTH({today}),1)'; NXT = 'DATE(YEAR({today}),MONTH({today})+1,1)'; Y1 = 'DATE(YEAR({today})-1,MONTH({today}),1)'; YS = 'DATE(YEAR({today}),1,1)'
YE = 'DATE(YEAR({today})+1,1,1)'
def TM(col='tickets.reported_on'): return '{range:%s},">="&%s,{range:%s},"<"&%s' % (col, MS, col, NXT)
NOTDONE = '{range:tickets.ticket_id},"<>",{range:tickets.status},"<>"&' + TS('Done')
kpis = [
    KPI('Tickets opened this month', 'COUNTIFS(%s)' % TM(), 'int'),
    KPI('Open tickets', 'COUNTIFS(%s)' % NOTDONE, 'int'),
    KPI('Overdue tickets', 'COUNTIFS({range:tickets.chk},%s)' % ca('Overdue'), 'int'),
    KPI('High priority tickets open', 'COUNTIFS({range:tickets.priority},%s,%s)' % (tok('prio', 'High'), NOTDONE), 'int'),
    KPI('Tickets done this month', 'COUNTIFS(%s,{range:tickets.status},%s)' % (TM('tickets.done_on'), TS('Done')), 'int'),
    KPI('Average days to fix', 'IFERROR(AVERAGEIFS({range:tickets.days_to_fix},{range:tickets.status},%s),0)' % TS('Done'), 'num'),
    KPI('Maintenance cost this month', 'SUMIFS({range:tickets.cost},%s)' % TM(), 'money'),
    KPI('Maintenance cost, last 12 months', 'SUMIFS({range:cost_unit.cost},{range:cost_unit.month},">="&%s,{range:cost_unit.month},"<"&%s)' % (Y1, MS), 'money'),
    KPI('Maintenance cost per booked night', 'IFERROR(SUMIFS({range:cost_unit.cost},{range:cost_unit.month},">="&%s,{range:cost_unit.month},"<"&%s)/SUMIFS({range:cost_unit.booked_nights},{range:cost_unit.month},">="&%s,{range:cost_unit.month},"<"&%s),0)' % (Y1, MS, Y1, MS), 'money'),
    KPI('Parts cost this month', 'SUMIFS({range:tickets.parts_cost},%s)' % TM(), 'money'),
    KPI('Labour cost this month', 'SUMIFS({range:tickets.labour_cost},%s)' % TM(), 'money'),
    KPI('Tickets with guest impact, last 90 days', 'COUNTIFS({range:tickets.guest_impact},%s,{range:tickets.reported_on},">"&({today}-90))' % tok('yn', 'Yes'), 'int'),
    KPI('Handyperson hours this month', 'SUMIFS({range:handy.hours},{range:handy.week},">"&(%s-7),{range:handy.week},"<="&{today})' % MS, 'int'),
    KPI('Tickets waiting for parts', 'COUNTIFS({range:tickets.status},%s)' % TS('Waiting parts'), 'int'),
    KPI('Damage claims pending', 'COUNTIFS({range:claims.status},%s)' % tok('dmst', 'Pending'), 'int'),
    KPI('Value of claims pending', 'SUMIFS({range:claims.claimed_amount},{range:claims.status},%s)' % tok('dmst', 'Pending'), 'money'),
    KPI('Claims paid this year', 'SUMIFS({range:claims.paid_amount},{range:claims.paid_on},">="&%s)' % YS, 'money'),
    KPI('Recovered share of claimed amount', 'IFERROR(SUM({range:claims.paid_amount})/SUMIFS({range:claims.claimed_amount},{range:claims.status},"<>"&%s),0)' % tok('dmst', 'Pending'), 'pct'),
    KPI('Average claim amount', 'IFERROR(AVERAGE({range:claims.claimed_amount}),0)', 'money'),
    KPI('Deposits held now', 'SUM({range:deposits.held})', 'money'),
    KPI('Safety checks overdue', 'COUNTIFS({range:safety.status},%s)' % ca('Overdue'), 'int'),
    KPI('Services due in 30 days', 'COUNTIFS({range:services.days_to_due},">=0",{range:services.days_to_due},"<="&{set:service_warn_days})', 'int'),
    KPI('Warranties ending in 60 days', 'COUNTIFS({range:appliances.warranty_left},">=0",{range:appliances.warranty_left},"<="&{set:warranty_warn_days})', 'int'),
    KPI('Units with repeat issues', 'COUNTIFS({range:units.repeat_n},">0")', 'int'),
    KPI('Most expensive unit this year', 'INDEX({range:units.name},MATCH(MAX({range:units.cost_year}),{range:units.cost_year},0))', 'text'),
    KPI('Repairs over the repair limit this year', 'COUNTIFS({range:tickets.cost},">"&{set:repair_limit},{range:tickets.reported_on},">="&%s)' % YS, 'int'),
    KPI('Capex planned this year', 'SUMIFS({range:capex.cost},{range:capex.planned_month},">="&%s,{range:capex.planned_month},"<"&%s)' % (YS, YE), 'money'),
    KPI('Inspections passed share', 'IFERROR(COUNTIFS({range:inspections.pass_flag},%s)/COUNT({range:inspections.score}),0)' % ca('Passed'), 'pct'),
    KPI('Incidents this year', 'COUNTIFS({range:incidents.date},">="&%s,{range:incidents.date},"<="&{today})' % YS, 'int'),
]
assert len(kpis) == 29, len(kpis)
dashboard = {"title": "Maintenance Dashboard", "kpis": kpis,
    "monthly": {"title": "Maintenance cost and damage claims", "date": "tickets.reported_on", "series": [
        {"label": "Maintenance cost", "sum": "tickets.cost", "date": "tickets.reported_on"}, {"label": "Parts cost", "sum": "tickets.parts_cost", "date": "tickets.reported_on"},
        {"label": "Damage claimed", "sum": "claims.claimed_amount", "date": "claims.reported_on"}, {"label": "Damage paid", "sum": "claims.paid_amount", "date": "claims.reported_on"}]},
    "breakdowns": [{"title": "Maintenance cost by kind", "by": "tickets.kind", "value": "tickets.cost", "agg": "sum"}, {"title": "Tickets by city", "by": "tickets.city", "value": "tickets.cost", "agg": "count"},
                   {"title": "Damage claimed by channel", "by": "claims.channel", "value": "claims.claimed_amount", "agg": "sum"}, {"title": "Cost by unit type", "by": "tickets.unit_type", "value": "tickets.cost", "agg": "sum"}]}
insights = {"filters": [{"label": "Unit", "ref": "units.name"}, {"label": "Unit type", "list": "utype"}, {"label": "City", "list": "city"}],
    "gauges": [{"title": "Tickets closed on time", "num": AGG('count', 'tickets', where=[('chk', '=', ca('Closed on time'))]), "den": AGG('count', 'tickets', where=[('status', '=', TS('Done'))])},
               {"title": "Claims recovered", "num": AGG('sum', 'claims', 'claims.paid_amount', where=[('status', '<>', tok('dmst', 'Pending'))]), "den": AGG('sum', 'claims', 'claims.claimed_amount', where=[('status', '<>', tok('dmst', 'Pending'))])},
               {"title": "Safety checks up to date", "num": AGG('count', 'safety', where=[('status', '=', ca('Up to date'))]), "den": AGG('count', 'safety', where=[('status', '<>', ca('Superseded'))])},
               {"title": "Inspections passed", "num": AGG('count', 'inspections', where=[('pass_flag', '=', ca('Passed'))]), "den": AGG('count', 'inspections')},
               {"title": "High priority share of open tickets", "num": AGG('count', 'tickets', where=[('priority', '=', tok('prio', 'High')), ('status', '<>', TS('Done'))]), "den": AGG('count', 'tickets', where=[('status', '<>', TS('Done'))])},
               {"title": "Services on schedule", "num": AGG('count', 'services', where=[('status', '=', ca('On schedule'))]), "den": AGG('count', 'services')}],
    "charts": [
        CHART('Tickets opened per month', 'column', 'month', [AGG('count', 'tickets', date='tickets.reported_on', label='Tickets')]),
        CHART('Maintenance cost per month', 'column', 'month', [AGG('sum', 'tickets', 'tickets.cost', date='tickets.reported_on', label='Cost')]),
        CHART('Tickets by kind', 'bar', 'tickets.kind', [AGG('count', 'tickets', label='Tickets')]),
        CHART('Cost by kind', 'bar', 'tickets.kind', [AGG('sum', 'tickets', 'tickets.cost', label='Cost')]),
        CHART('Tickets by priority', 'bar', 'tickets.priority', [AGG('count', 'tickets', label='Tickets')]),
        CHART('Tickets by source', 'bar', 'tickets.source', [AGG('count', 'tickets', label='Tickets')]),
        CHART('Tickets by status', 'bar', 'tickets.status', [AGG('count', 'tickets', label='Tickets')]),
        CHART('Tickets by unit type', 'bar', 'tickets.unit_type', [AGG('count', 'tickets', label='Tickets')]),
        CHART('Tickets by city', 'bar', 'tickets.city', [AGG('count', 'tickets', label='Tickets')]),
        CHART('Average days to fix per month', 'line', 'month', [AGG('avg', 'tickets', 'tickets.days_to_fix', date='tickets.reported_on', where=[('status', '=', TS('Done'))], label='Days to fix')]),
        CHART('Damage claims per month', 'column', 'month', [AGG('count', 'claims', date='claims.reported_on', label='Claims')]),
        CHART('Claims by status', 'bar', 'claims.status', [AGG('count', 'claims', label='Claims')]),
        CHART('Claimed against paid per month', 'column', 'month', [AGG('sum', 'claims', 'claims.claimed_amount', date='claims.reported_on', label='Claimed'), AGG('sum', 'claims', 'claims.paid_amount', date='claims.reported_on', label='Paid')]),
        CHART('Damage claimed by channel', 'bar', 'claims.channel', [AGG('sum', 'claims', 'claims.claimed_amount', label='Claimed')]),
        CHART('Parts against labour per month', 'column', 'month', [AGG('sum', 'tickets', 'tickets.parts_cost', date='tickets.reported_on', label='Parts'), AGG('sum', 'tickets', 'tickets.labour_cost', date='tickets.reported_on', label='Labour')]),
        CHART('Safety checks done per month', 'column', 'month', [AGG('count', 'safety', date='safety.date', label='Checks')]),
        CHART('Cost per booked night per month', 'line', 'month', [AGG('avg', 'cost_unit', 'cost_unit.cost_per_night', date='cost_unit.month', label='Cost per night')]),
        CHART('Tickets per handyperson', 'bar', 'tickets.handyperson', [AGG('count', 'tickets', label='Tickets')])]}
signature = [
    {"name": "Maintenance ticket board with due dates", "why": "every problem has a priority, a fix-by date, days open and a check that shows overdue, due soon, waiting for parts or closed on time", "where": "Maintenance Tickets"},
    {"name": "Overdue ticket alert", "why": "tickets past their fix-by date turn red and a ready message goes to the handyperson and the host", "where": "Maintenance Tickets"},
    {"name": "Damage claim builder with evidence list", "why": "repair cost, extra cleaning, lost nights and the deposit give the amount to claim and the number of proof items to collect", "where": "Damage Claim Builder"},
    {"name": "Deposit release check", "why": "deposit, claim and days since check-out say how much to return, how much to keep and whether the release is overdue", "where": "Deposit Release Check"},
    {"name": "Pending claims tracker", "why": "every claim shows the days it has waited, the unrecovered amount and the amount left to claim after the deposit", "where": "Damage Claims"},
    {"name": "Safety check schedule", "why": "smoke alarms, gas, locks, extinguishers and sockets show the latest check of each unit with overdue and due soon alerts", "where": "Safety Checks"},
    {"name": "Repair or replace decision", "why": "repair cost, replacement cost, age, expected life and warranty give the cheaper choice and the cost per year of each", "where": "Repair or Replace"},
    {"name": "Appliance and warranty register", "why": "every appliance with its warranty end, age and a warning before the cover ends, so a faulty machine is claimed from the seller", "where": "Appliance Register"},
    {"name": "Preventive service planner", "why": "each recurring service shows the next due date, the days left and the yearly cost, and the planner prices a new service for all units", "where": "Service Schedule"},
    {"name": "Maintenance cost per night by unit", "why": "cost by unit and month divided by the nights booked shows which unit costs most to keep and which repairs keep coming back", "where": "Cost by Unit"}]
competitors = [
    {"what": "free occupancy templates", "lacks": "count nights and revenue but have no tickets, no damage claims, no deposits and no safety checks, so a repair or a claim lives in a chat or in your head"},
    {"what": "subscription property-management software", "lacks": "charge every month and hide the cost behind reports, with no repair or replace calculator and no claim builder you can adjust"},
    {"what": "single-sheet booking trackers", "lacks": "list bookings but never connect a ticket or a damage claim to the unit, the guest and the next check-in"},
    {"what": "generic expense spreadsheets", "lacks": "total the costs but cannot give the cost per booked night of each unit, the repeat issues or the days a ticket stayed open"},
    {"what": "paper checklists and notebooks", "lacks": "cannot warn that a safety check or a warranty ends soon and cannot add up what each unit cost to keep"}]
guide = [
    'Open Start and type your company name and your own limits in the yellow cells: days to fix each priority, the repair limit, the wanted cost per booked night, the days to release a deposit and the warning days.',
    'Check Units, Bookings and Team. They hold your units, the bookings used for the next check-in and the handypeople the other sheets look up.',
    'Log every problem on Maintenance Tickets with its kind, priority, handyperson and cost. The fix-by date, days open and the ticket check fill in; overdue tickets turn red.',
    'Record each damage found after a stay on Damage Claims and each deposit on Deposits Held. See the days pending, the amount not recovered and which deposits are overdue to release.',
    'Keep Safety Checks, Service Schedule and Appliance Register up to date. They warn of overdue checks, services due soon and warranties that end soon.',
    'Use Repair Quotes, Parts Orders and Handyperson Weeks to see what is waiting for a decision, for parts or for a free handyperson.',
    'Write incidents, lock events and pest and exterior checks as they happen. Recurring Issues shows the kinds of problem that keep coming back in a unit.',
    'Fill Cost by Unit each month and read Capex Plan to decide what to spend on next and how fast it pays back.',
    f'Use the {len(tools)} calculators for priority and due dates, workload, repair or replace, damage claims, deposits, cost per night, services, warranties, safety checks, capex, parts, guest impact, deadlines and what-ifs.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Maintenance Dashboard and Charts every week: tickets, cost, claims, safety, services and cost per booked night.']
listing = {"title": "Short-Term Rental Maintenance Excel Template: Repair Tickets, Damage Claims, Deposits, Safety Checks, Warranty and Cost per Night",
    "headline": "Keep every unit guest-ready and know what each one costs to keep",
    "tags": ["short term rental", "vacation rental", "rental host", "maintenance tracker", "damage claims", "excel template", "safety checks", "repair tickets", "deposit tracker", "warranty tracker", "property host", "holiday let", "cost per night"],
    "description": ("Run the maintenance side of a short-term or vacation rental business in one Excel workbook. Built for a host or co-host with 3 to 15 furnished units rented by the night through booking platforms and direct bookings. "
        "Maintenance Tickets follow every problem from the report to done with a priority, a fix-by date, days open, the handyperson, parts and labour cost, the guest impact and the next check-in at the unit, and overdue tickets turn red.\n\n"
        "Damage Claims and Deposits Held show the amount claimed, the deposit held, the days a claim has waited, what is still unrecovered and which deposits are overdue to release. Safety Checks, Service Schedule and Appliance Register keep smoke alarms, gas, locks, services and warranties on time, with a warning before each date. "
        "Repair Quotes, Parts Orders, Inspections, Incidents, Handyperson Weeks, Recurring Issues, Capex Plan, Key and Lock Log and Pest and Exterior Checks cover the rest of the week. Cost by Unit gives the maintenance cost per booked night of each unit and month.\n\n"
        f"{len(tools)} calculators cover ticket priority and due date, handyperson workload, repair or replace, the damage claim and its proof list, the deposit release, cost per night, preventive services, warranty cover, safety checks, capex payback, parts orders, the cost of a guest failure, the last safe day to start a repair and a spend and revenue grid. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to handypeople, guests, the co-host (a helper who handles guests for a fee), the host, owners and the accountant.\n\n"
        "This is part five of the Short-Term Rental Host suite. A standard .xlsx workbook with no macros and no subscription, 15 languages in one purchase, with a demo copy full of sample data for a small portfolio to explore first. It helps you plan and track maintenance and does not give legal or insurance advice."),
    "features": ["Maintenance tickets with fix-by dates and overdue alerts", "Damage claim tracker with deposits", "Safety check schedule with warnings", "Service schedule and appliance warranty register", "Repair or replace calculator",
                 "Maintenance cost per booked night by unit", "Repair quotes, parts orders and handyperson weeks", "Capex plan with payback", f"{len(tools)} calculators for repairs and claims", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p5', slug='short-term-rental-maintenance', profession='Short-Term Rental Host', name='Maintenance, Damage and Safety',
         tagline='Keep every unit guest-ready and know what each one costs to keep', price_usd=29,
         colors={"primary": "#264653", "accent": "#E9C46A"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 5, "of": 8, "focus": "Maintenance, damage and safety"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sr5.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'rows', sum(len(t['demo']) for t in tables))
