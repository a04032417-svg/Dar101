"""Home Management suite - part 8: Projects, Hosting and Declutter."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho8_lists import *
from ho8_tables import *
from ho8_tools import tools
import ho8_data as D

SUITE = 'fx-20261118-home-management'
NOTE = "Sample wording: adapt it to your own household, check the manufacturer's instructions and your local rules."
def FW(*pairs): return [FV(a, b) for a, b in pairs]
YESV = '{list:yesno.yes}'


# ------------------------------------------------------------------ forms (12)
def PCNT(extra=''): return 'COUNTIFS(%s,{pick}%s)' % (PT('project_id'), extra)
forms = [
    FORM('project_card', 'Project Card', 'One project with its phases', 'projects.project_id', FW(('Project', 'projects.project'), ('Kind', 'projects.kind')) + [
        FF('Tasks', PCNT(), 'int'), FF('Tasks done', PCNT(',%s,%s' % (PT('status'), S_DONE)), 'int'), FF('Tasks open', PCNT(',%s,1' % PT('open')), 'int'),
        FF('Estimate of all tasks', 'SUMIFS(%s,%s,{pick})' % (PT('est_cost'), PT('project_id')), 'money'), FF('Actual cost to date', 'SUMIFS(%s,%s,{pick})' % (PT('actual_cost'), PT('project_id')), 'money'),
        FF('Days late, worst task', 'SUMPRODUCT(MAX((%s={pick})*(%s<>%s)*(%s<{today})*({today}-%s)))' % (PT('project_id'), PT('status'), S_DONE, PT('due'), PT('due')), 'int')],
        {"from": "project_plan", "match": "project_plan.project_id", "columns": ["phase", "start", "end", "owner", "estimate", "stage"], "max": 10}),
    FORM('task_sheet', 'Project Task Sheet', 'One task with owner, dates and cost line', 'project_tasks.task_id', FW(
        ('Task', 'project_tasks.task'), ('Project', 'project_tasks.project'), ('Phase', 'project_tasks.phase'), ('Owner', 'project_tasks.owner'), ('Start', 'project_tasks.start'), ('Due', 'project_tasks.due'),
        ('Status', 'project_tasks.status'), ('Effort minutes', 'project_tasks.minutes'), ('Days late', 'project_tasks.days_late'), ('Days until due', 'project_tasks.due_in'), ('Suggested new due date', 'project_tasks.new_due'))),
    FORM('cost_sheet', 'Project Cost Sheet', 'Estimate, actual and paid cost lines', 'projects.project_id', FW(('Project', 'projects.project')) + [
        FF('Estimate', 'SUMIFS(%s,%s,{pick})' % (PT('est_cost'), PT('project_id')), 'money'), FF('Actual cost to date', 'SUMIFS(%s,%s,{pick})' % (PT('actual_cost'), PT('project_id')), 'money'),
        FF('Paid, finished tasks', 'SUMIFS(%s,%s,{pick},%s,%s)' % (PT('actual_cost'), PT('project_id'), PT('status'), S_DONE), 'money'),
        FF('Estimate, finished tasks', 'SUMIFS(%s,%s,{pick},%s,%s)' % (PT('est_cost'), PT('project_id'), PT('status'), S_DONE), 'money'),
        FF('Paid less estimate, finished tasks', 'SUMIFS(%s,%s,{pick},%s,%s)-SUMIFS(%s,%s,{pick},%s,%s)' % (PT('actual_cost'), PT('project_id'), PT('status'), S_DONE, PT('est_cost'), PT('project_id'), PT('status'), S_DONE), 'money')]),
    FORM('move_sheet', 'Move Date Sheet', 'One countdown step and its shifted date', 'move_countdown.step', FW(
        ('Days before the move', 'move_countdown.days_before'), ('Weeks before', 'move_countdown.weeks_before'), ('Due date', 'move_countdown.due'), ('Date if the move shifts', 'move_countdown.shifted'),
        ('Status', 'move_countdown.status'), ('Move day', 'move_countdown.move_date'), ('Old home released', 'move_countdown.end_date'), ('Open items that move with the date', 'move_countdown.tasks_moved'))),
    FORM('packing_sheet', 'Packing Room Sheet', 'One room: boxes, label and the day it moves', 'move_boxes.label', FW(
        ('Room', 'move_boxes.room'), ('Boxes counted', 'move_boxes.boxes'), ('Packed', 'move_boxes.packed'), ('Boxes left', 'move_boxes.left'), ('Moves on', 'move_boxes.moves_on'), ('Pack by', 'move_boxes.pack_by'),
        ('Days to the move', 'move_boxes.days_left'), ('Status', 'move_boxes.status'), ('Notes', 'move_boxes.notes')) + [
        FF('Boxes left in all rooms', 'SUM(%s)' % MB('left'), 'int'), FF('Boxes counted in all rooms', 'SUM(%s)' % MB('boxes'), 'int')]),
    FORM('address_sheet', 'Change Of Address Sheet', 'One organisation to tell about the new address', 'address_list.orgtype', FW(
        ('Notice needed, days', 'address_list.notice_days'), ('Done', 'address_list.done'), ('Tell them by', 'address_list.needed_by'), ('Days left', 'address_list.days_left'), ('Status', 'address_list.status')) + [
        FF('Organisation types left', 'COUNTIFS(%s,%s,%s,"<>")' % (AD('done'), NO, AD('orgtype')), 'int')]),
    FORM('guest_sheet', 'Guest Sheet', 'One guest: reply, party size, preference label', 'guests.guest_id', FW(
        ('Guest', 'guests.guest'), ('RSVP', 'guests.rsvp'), ('Party size', 'guests.party_size'), ('Preference label', 'guests.pref_label'), ('Phone', 'guests.phone'), ('Table number', 'guests.table_no'),
        ('Dinner date', 'guests.dinner'), ('Dinner time', 'guests.dinner_time'), ('Reply by', 'guests.rsvp_by'), ('Moved to', 'guests.new_date'), ('People confirmed', 'guests.people_yes'), ('People invited', 'guests.people_invited'))),
    FORM('menu_sheet', 'Menu Sheet', 'One dish of the dinner with its ingredient lines', 'menu.recipe_id', FW(
        ('Recipe', 'menu.recipe'), ('Course', 'menu.course'), ('Portions', 'menu.portions'), ('Cook', 'menu.cook'), ('Day to cook', 'menu.day_to_cook'), ('Recipe servings', 'menu.servings'),
        ('Prep minutes', 'menu.prep_min'), ('Scale factor', 'menu.scale'), ('Days until cooking', 'menu.days_to_cook')),
        {"from": "recipe_ingredients", "match": "recipe_ingredients.recipe_id", "columns": ["item", "qty", "unit", "menu_qty"], "max": 20}),
    FORM('timeline_sheet', 'Hosting Timeline Sheet', 'One hosting task counted back from the dinner date', 'hosting_timeline.task', FW(
        ('Days before the dinner', 'hosting_timeline.days_before'), ('Owner', 'hosting_timeline.owner'), ('Due date', 'hosting_timeline.due'), ('Status', 'hosting_timeline.status'),
        ('Dinner date', 'hosting_timeline.dinner'), ('Days to the dinner', 'hosting_timeline.days_to_dinner'), ('Guests at the table', 'hosting_timeline.guests'), ('Hosting tasks open', 'hosting_timeline.tasks_open'),
        ('Menu items not bought', 'hosting_timeline.items_not_bought'), ('Dinner time', 'hosting_timeline.dinner_time'))),
    FORM('declutter_sheet', 'Declutter Area Sheet', 'One area with its items by decision', 'declutter_areas.area', FW(('Items decided', 'declutter_areas.decided'), ('Share of the count', 'declutter_areas.share')) + [
        FF('Items kept', 'SUMIFS(%s,%s,{pick},%s,%s)' % (DL('count'), DL('area'), DL('decision'), tok('decision', 'Keep')), 'int'),
        FF('Items donated', 'SUMIFS(%s,%s,{pick},%s,%s)' % (DL('count'), DL('area'), DL('decision'), DONATE), 'int'),
        FF('Items sold', 'SUMIFS(%s,%s,{pick},%s,%s)' % (DL('count'), DL('area'), DL('decision'), SELL), 'int'), FF('Items binned', 'SUMIFS(%s,%s,{pick},%s,%s)' % (DL('count'), DL('area'), DL('decision'), BIN), 'int')],
        {"from": "declutter", "match": "declutter.area", "columns": ["date", "item", "decision", "count"], "max": 15}),
    FORM('donation_sheet', 'Donation Drop-Off Sheet', 'One donation line for the drop-off record', 'donations.no', FW(
        ('Date', 'donations.date'), ('Area', 'donations.area'), ('Item', 'donations.item'), ('Count', 'donations.count'), ('Destination', 'donations.destination'), ('Year', 'donations.year')) + [
        FF('Items donated on the same day', 'SUMIFS(%s,%s,INDEX(%s,MATCH({pick},%s,0)))' % (DN('count'), DN('date'), DN('date'), DN('no')), 'int')]),
    FORM('year_sheet', 'Year In Review Sheet', 'One measure of the year against last year', 'year_review.measure', FW(
        ('This year', 'year_review.this_year'), ('Last year', 'year_review.last_year'), ('Change', 'year_review.change'), ('Improvement share', 'year_review.gain'), ('Verdict', 'year_review.verdict'),
        ('Next-year line', 'year_review.next_year'), ('Year', 'year_review.year'), ('Measures improved', 'year_review.improved_n')))]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('plan_page', 'Project Plan Page', 'Project plan page with tasks by status and owner', 'project_tasks.task_id', [
        'Project plan page of {set:household}, dated {today}. Project: {col:project_tasks.project}. Phase: {col:project_tasks.phase}. Task {col:project_tasks.task_id}: {col:project_tasks.task}.',
        'Owner: {col:project_tasks.owner}. Start {col:project_tasks.start}, due {col:project_tasks.due}. Status: {col:project_tasks.status}. Effort: {col:project_tasks.minutes} minutes.',
        'Days late: {col:project_tasks.days_late}. Days until due: {col:project_tasks.due_in}. A suggested new due date is {col:project_tasks.new_due}.',
        'Change the status on the Project tasks sheet: Not started, In progress, Blocked or Done. Days late and the open count are calculated from your entries.'], ['Project owner', 'Household member'], NOTE),
    DOC('cost_summary', 'Project Cost Summary', 'Project cost summary: estimate, actual and paid', 'project_status.phase', [
        'Project cost summary of {set:household}, dated {today}. Project {col:project_status.project}, phase {col:project_status.phase}.',
        'Estimate {col:project_status.est}. Actual to date {col:project_status.actual}. Paid for finished tasks {col:project_status.paid} against an estimate of {col:project_status.est_done} for the same tasks.',
        'Finished work against its estimate: {col:project_status.cost_diff}, a share of {col:project_status.cost_over}. Verdict: {col:project_status.verdict}.',
        'Cost lines are your own entries and the arithmetic is calculated; they are not a quote or advice. Check every trade quote in writing.'], ['Project owner', 'Household member'], NOTE),
    DOC('moving_list', 'Moving Checklist By Room', 'Moving checklist by room with boxes and labels', 'move_boxes.label', [
        'Moving checklist of {set:household}, dated {today}. Room: {col:move_boxes.room}. Box label: {col:move_boxes.label}. Boxes counted: {col:move_boxes.boxes}. Packed: {col:move_boxes.packed}.',
        'Boxes left: {col:move_boxes.left}. The room moves on {col:move_boxes.moves_on}; pack it by {col:move_boxes.pack_by}, {col:move_boxes.days_left} days before the move. Status: {col:move_boxes.status}. Note: {col:move_boxes.notes}.',
        'Write the label on two sides of every box and keep a first-night box apart. Tick the room on the Moving boxes by room sheet when it is packed.'], ['Packer', 'Household member'], NOTE),
    DOC('address_page', 'Change Of Address List', 'Change-of-address list by organisation type', 'address_list.orgtype', [
        'Change-of-address list of {set:household}, dated {today}. Organisation type: {col:address_list.orgtype}. Notice typically needed: {col:address_list.notice_days} days (check each one).',
        'Move day: {set:move_date}. Tell them by {col:address_list.needed_by}. Days left: {col:address_list.days_left}. Status: {col:address_list.status}. Done: {col:address_list.done}.',
        'Keep the new address, the effective date and a reference for every notice you give. Notice periods are typical: check each organisation and your local rules.'], ['Household member', 'Household member'], NOTE),
    DOC('countdown_page', 'Move Countdown Timeline', 'Move countdown timeline from 8 weeks to 1 day before', 'move_countdown.step', [
        'Move countdown of {set:household}, dated {today}. Step: {col:move_countdown.step}. It falls {col:move_countdown.days_before} days ({col:move_countdown.weeks_before} weeks) before the move day, {col:move_countdown.move_date}.',
        'Due date {col:move_countdown.due}. If the move day shifts by {set:move_shift} days it becomes {col:move_countdown.shifted}. Status: {col:move_countdown.status}. The old home is released on {col:move_countdown.end_date}.',
        'Steps and notices still open that move with the date: {col:move_countdown.tasks_moved}. Change the move day in Settings and every date follows.'], ['Household member', 'Household member'], NOTE),
    DOC('hosting_plan', 'Hosting Plan', 'Hosting plan with guests, menu and timeline', 'hosting_timeline.task', [
        'Hosting plan of {set:household}, dated {today}. Dinner on {col:hosting_timeline.dinner} at {col:hosting_timeline.dinner_time}, {col:hosting_timeline.days_to_dinner} days away, for {col:hosting_timeline.guests} guests.',
        'Task: {col:hosting_timeline.task}. Owner: {col:hosting_timeline.owner}. Due {col:hosting_timeline.due}, {col:hosting_timeline.days_before} days before the dinner. Status: {col:hosting_timeline.status}.',
        'Hosting tasks open: {col:hosting_timeline.tasks_open}. Menu items not bought: {col:hosting_timeline.items_not_bought}. Children eat at {col:hosting_timeline.kids_eat}; helpers come from {col:hosting_timeline.come_from}.'], ['Host', 'Household member'], NOTE),
    DOC('guest_list', 'Guest List With RSVP', 'Guest list with RSVP and preference labels', 'guests.guest_id', [
        'Guest list of {set:household}, dated {today}. Guest {col:guests.guest_id}: {col:guests.guest}. Reply: {col:guests.rsvp}. Party size: {col:guests.party_size}. Preference label: {col:guests.pref_label}.',
        'Dinner on {col:guests.dinner} at {col:guests.dinner_time}. Reply by {col:guests.rsvp_by}. Phone: {col:guests.phone}. Table number: {col:guests.table_no}.',
        'People invited: {col:guests.people_invited}. People confirmed: {col:guests.people_yes}. A preference label is a short note for the cook, never health advice.'], ['Host', 'Household member'], NOTE),
    DOC('menu_list', 'Menu And Shopping List', 'Menu and shopping list for the dinner', 'menu_shop.item', [
        'Shopping list of {set:household}, dated {today}. Item: {col:menu_shop.item} ({col:menu_shop.section}). Needed for the menu: {col:menu_shop.qty} {col:menu_shop.unit}, used by {col:menu_shop.lines} recipes.',
        'Pack size {col:menu_shop.pack_size}. Packs to buy: {col:menu_shop.packs}, spare in the last pack: {col:menu_shop.spare}. Bought: {col:menu_shop.bought}.',
        'Quantities are scaled from the recipe servings to the portions of the dinner menu and rounded up to whole packs. Check the label of every pack.'], ['Shopper', 'Household member'], NOTE),
    DOC('place_cards', 'Place Cards And Table Plan', 'Place cards and table plan list', 'guests.guest_id', [
        'Table plan of {set:household}, dated {today}. Dinner on {col:guests.dinner} at {col:guests.dinner_time}.',
        'Place card: {col:guests.guest}, table {col:guests.table_no}, party of {col:guests.party_size}. Reply: {col:guests.rsvp}. Label for the cook: {col:guests.pref_label}.',
        'Write one card for every confirmed guest and one for every maybe guest; keep the table numbers on the Guests sheet in step with the plan.'], ['Host', 'Household member'], NOTE),
    DOC('declutter_page', 'Declutter Progress Page', 'Declutter progress by area', 'declutter.declutter_id', [
        'Declutter progress of {set:household}, dated {today}. Log line {col:declutter.declutter_id} of {col:declutter.date}: area {col:declutter.area}, item {col:declutter.item}, decision {col:declutter.decision}, count {col:declutter.count}.',
        'Areas in the home: {col:declutter.areas_total}. Areas not started: {col:declutter.areas_open}. The next area to start is {col:declutter.next_area}. Decisions are keep, donate, sell or bin, counted on the Declutter areas sheet.',
        'Decide one shelf or one drawer at a time and finish the area before you open the next.'], ['Household member', 'Household member'], NOTE),
    DOC('donation_page', 'Donation Record Page', 'Donation record page', 'donations.no', [
        'Donation record of {set:household}, dated {today}. Donation line {col:donations.no} of {col:donations.year}.',
        'Date {col:donations.date}. Area: {col:donations.area}. Item: {col:donations.item}. Count: {col:donations.count}. Destination: {col:donations.destination}.',
        'Keep this page with the receipt from the place you gave to, if they give one. Ask your local charity shop what they accept.'], ['Household member', 'Household member'], NOTE),
    DOC('year_page', 'Year In Review Page', 'Year in review page with the next-year lines', 'year_review.measure', [
        'Year in review {col:year_review.year} of {set:household}, dated {today}. Measure: {col:year_review.measure}. This year {col:year_review.this_year}, last year {col:year_review.last_year}, change {col:year_review.change}.',
        'Improvement share: {col:year_review.gain}. Verdict: {col:year_review.verdict}. Measures improved on last year: {col:year_review.improved_n} of 14.',
        'Line for next year: {col:year_review.next_year}. Type the numbers from the other workbooks of the suite and keep three lines for next year.'], ['Adult 1', 'Adult 2'], NOTE)]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('start_project', 'Start a Project', 'project_plan', 'project_plan.start', [('Write what the project is and what finished means', -7), ('Choose the owner of every phase', -7), ('Type the start and end dates of the phases', -5), ('Type the estimate of every phase', -5), ('Ask for two quotes where a trade is needed', -3), ('Book the first task', 0), ('Review the plan after the first week', 7)]),
    CHK('renovation_week', 'Renovation Week', 'project_tasks', 'project_tasks.start', [('Confirm the trade visits for the week', -3), ('Clear the access and cover the floors', -1), ('Move what must stay dry or safe', -1), ('Be at home for the first visit', 0), ('Check the work against the task list at the end of the day', 0), ('Clear up and type the actual cost line', 1)]),
    CHK('garden_bed', 'Garden Bed', 'project_plan', 'project_plan.start', [('Mark the bed with string or sand', 0), ('Dig and remove the stones', 1), ('Build the edge', 2), ('Fill with compost', 3), ('Plant with the children', 5), ('Water and mulch', 6), ('Set a watering rota', 7)]),
    CHK('move_8_weeks', 'Move 8 Weeks To 1 Day', 'move_boxes', 'move_boxes.moves_on', [('Give notice or confirm the completion date', -56), ('Book the removal van or helpers', -49), ('Order boxes and packing materials', -42), ('Start the change-of-address list', -35), ('Book the time off and the sitter', -28), ('Pack the rooms you use least', -21), ('Book the final meter readings', -14), ('Collect the keys of the new home', -10), ('Redirect the post', -7), ('Defrost the freezer', -3), ('Pack a first-night box', -2), ('Confirm the van and the keys', -1)]),
    CHK('moving_day', 'Moving Day', 'move_boxes', 'move_boxes.moves_on', [('Keys, phones and chargers in your pocket', 0), ('Walk the old home with the check list', 0), ('Take the final meter readings', 0), ('Load the van by room', 0), ('Hand over the keys', 0), ('Unpack the first-night box', 0)]),
    CHK('after_move', 'After The Move', 'move_boxes', 'move_boxes.moves_on', [('Unpack the kitchen and the bedrooms first', 1), ('Check every box label against the Moving boxes sheet', 1), ('Tell the organisations that are still open', 3), ('Find the stopcock and the fuse box', 1), ('Unpack the living areas', 5), ('Declutter the boxes you do not need', 10), ('Return keys, boxes and borrowed items', 14)]),
    CHK('host_dinner', 'Host A Holiday Dinner', 'project_plan', 'project_plan.end', [('Ask for replies and preference notes', -30), ('Plan the menu and drinks', -28), ('Borrow extra chairs and a table', -21), ('Order the main dish', -14), ('Shop for what keeps', -10), ('Deep clean the house', -3), ('Shop for fresh food', -2), ('Make the starters and dessert', -1), ('Set the table', 0), ('Clear up and thank the helpers', 1)]),
    CHK('hosting_week', 'Hosting Week', 'project_plan', 'project_plan.end', [('Shop for fresh food', -2), ('Cook what can be made ahead', -2), ('Set the table and the place cards', -1), ('Chill the drinks', -1), ('Check the plates and glasses for every guest', -1), ('Start the main dish on time', 0), ('Clear and wash up', 1)]),
    CHK('declutter_area', 'Declutter An Area', 'declutter', 'declutter.date', [('Choose one area and set a timer', 0), ('Take everything out of one shelf or drawer', 0), ('Sort into keep, donate, sell and bin', 0), ('Put the keep items back in order', 0), ('Bag the donate and bin items', 0), ('Type the counts in the Declutter log', 1)]),
    CHK('donation_dropoff', 'Donation Drop-Off', 'declutter', 'declutter.date', [('Check that the items are clean and complete', -2), ('Ask what the place accepts', -2), ('Bag and count the items', -1), ('Take them to the drop-off', 0), ('Keep the receipt if you get one', 0), ('Check the donation log', 1)]),
    CHK('spring_round', 'Spring Declutter Round', 'declutter', 'declutter.date', [('Pick the areas and give each one an owner', -7), ('Book the donation drop-off', -5), ('Declutter the first area', 0), ('Declutter the next areas', 7), ('Sell what is worth selling', 14), ('Take the bags to the drop-off', 21), ('Walk through and type the last counts', 28)]),
    CHK('year_end', 'Year-End Home Review', 'year_review', 'year_review.typed_on', [('Copy the numbers from the other workbooks', 0), ('Type last year numbers where you kept them', 0), ('Read the measures that got worse', 2), ('Write three lines for next year', 3), ('Pick one owner for every line', 4), ('Print the year in review page', 5)])]
assert len(checklists) == 12


# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
HH = ' {household}'
messages = [
    M('a1_late_task', 'Adult 1: the task is late, move the date', 'project_tasks', 'project_tasks.a1_phone', 'Hi {a1_name}, the task {task} is {days_late} days late. Shall we move the due date to {new_due}?' + HH),
    M('a2_task', 'Adult 2: this task is yours', 'project_tasks', 'project_tasks.a2_phone', 'Hi {a2_name}, the task {task} is yours, due on {due}. It depends on {depends_on}.' + HH),
    M('a2_cost', 'Adult 2: review the cost line', 'cost_lines', 'cost_lines.a2_phone', 'Hi {a2_name}, the cost line for {project} is {actual} against an estimate of {estimate}. Can we review it?' + HH),
    M('a1_dinner', 'Adult 1: days left to the dinner', 'hosting_timeline', 'hosting_timeline.a1_phone', 'Hi {a1_name}, the holiday dinner is on {dinner}, {days_to_dinner} days left and {tasks_open} hosting tasks open.' + HH),
    M('a2_shop', 'Adult 2: the fresh food shop', 'hosting_timeline', 'hosting_timeline.a2_phone', 'Hi {a2_name}, please do the fresh food shop on {due}. The list for {guests} guests is ready.' + HH),
    M('a1_guests', 'Adult 1: the guest list so far', 'guests', 'guests.a1_phone', 'Hi {a1_name}, the guest list for the dinner is {people_invited} people and {people_yes} are confirmed.' + HH),
    M('a2_move', 'Adult 2: the move date', 'move_countdown', 'move_countdown.a2_phone', 'Hi {a2_name}, the move date is now {move_date} and {tasks_moved} open items move with it.' + HH),
    M('c1_plates', 'Child 1: check the plates and glasses', 'hosting_timeline', 'hosting_timeline.c1_phone', 'Hi {c1_name}, please check the plates and glasses for {guests} guests by {due}.' + HH),
    M('c1_pack', 'Child 1: you are packing a room', 'move_boxes', 'move_boxes.c1_phone', 'Hi {c1_name}, you are packing the {room} by {pack_by}. The {boxes} boxes are in the hall.' + HH),
    M('c2_table', 'Child 2: help set the table', 'hosting_timeline', 'hosting_timeline.c2_phone', 'Hi {c2_name}, please help set the table on {due}. The place cards are yours.' + HH),
    M('c2_toys', 'Child 2: choose toys to donate', 'donations', 'donations.c2_phone', 'Hi {c2_name}, please choose the toys to donate by {date}. We are giving {count} items.' + HH),
    M('gp_help', 'Grandparent: help with the dinner', 'hosting_timeline', 'hosting_timeline.gp_phone', 'Hi {gp_name}, can you come on {due} to help with the dinner? We are {guests} at the table.' + HH),
    M('gp_thanks', 'Grandparent: thank you, the time', 'hosting_timeline', 'hosting_timeline.gp_phone', 'Hi {gp_name}, thank you for the help. The dinner is on {dinner} at {dinner_time}.' + HH),
    M('bs_host', 'Babysitter: we host, come from', 'hosting_timeline', 'hosting_timeline.bs_phone', 'Hi {bs_name}, on {dinner} we host {guests} guests. Can you come from {come_from}?' + HH),
    M('bs_kids', 'Babysitter: the children eat first', 'hosting_timeline', 'hosting_timeline.bs_phone', 'Hi {bs_name}, the children eat first on {dinner} at {kids_eat}. The plan is attached.' + HH),
    M('cp_lift', 'Carpool family: the activity lift moves', 'hosting_timeline', 'hosting_timeline.cp_phone', 'Hi {cp_name}, we host a dinner on {dinner}, so the activity lift moves to {come_from}. Is that all right?' + HH),
    M('cp_clothes', 'Carpool family: outgrown clothes', 'donations', 'donations.cp_phone', 'Hi {cp_name}, we donate outgrown kids clothes on {date}. Would you like a bag?' + HH),
    M('so_trip', 'School office: the trip form is signed', 'move_countdown', 'move_countdown.so_phone', 'Hi {so_name}, the school trip form is signed. {c1_name} will be away on {due}.' + HH),
    M('nb_parking', 'Neighbour: parking may be busy', 'hosting_timeline', 'hosting_timeline.nb_phone', 'Hi {nb_name}, we host {guests} guests on {dinner}, so parking may be busy. Thank you.' + HH),
    M('nb_donate', 'Neighbour: first choice of the donations', 'donations', 'donations.nb_phone', 'Hi {nb_name}, we are donating {count} items on {date}. Would you like first choice?' + HH),
    M('nb_key', 'Neighbour: hold the spare key', 'move_countdown', 'move_countdown.nb_phone', 'Hi {nb_name}, our move is on {move_date}. Please hold the spare key until {end_date}.' + HH),
    M('dw_dog', 'Dog walker: collect the dog', 'hosting_timeline', 'hosting_timeline.dw_phone', 'Hi {dw_name}, the house is busy on {dinner} with the dinner. Please collect the dog at {collect_at}.' + HH),
    M('pl_visit', 'Plumber: confirm the bathroom visit', 'project_tasks', 'project_tasks.pl_phone', 'Hi {pl_name}, please confirm the visit for the bathroom on {due}. The old suite is out.' + HH),
    M('el_visit', 'Electrician: confirm the first fix', 'project_tasks', 'project_tasks.el_phone', 'Hi {el_name}, please confirm the first fix on {due} for the bathroom.' + HH),
    M('helper_quote', 'Helper: please quote for the garden work', 'project_plan', 'project_plan.helper_phone', 'Hi {helper}, please quote for the phase {phase} of the garden bed, due by {end}. {note}.' + HH),
    M('ll_out', 'Landlord or agent: key hand-over', 'move_countdown', 'move_countdown.ll_phone', 'Hi {ll_name}, we move out on {move_date}. Please confirm the key hand-over and the check date.' + HH),
    M('ll_notice', 'Landlord or agent: confirm our notice', 'move_countdown', 'move_countdown.ll_phone', 'Hi {ll_name}, please confirm the notice we gave on {due} for the move on {move_date}.' + HH),
    M('g_invite', 'Guest: you are invited', 'guests', 'guests.phone', 'Hi {guest}, you are invited to the holiday dinner on {dinner} at {dinner_time}. Please reply by {rsvp_by}.' + HH),
    M('g_pref', 'Guest: tell us a preference note', 'guests', 'guests.phone', 'Hi {guest}, please tell us any preference or avoid note for the dinner by {rsvp_by}.' + HH),
    M('g_moved', 'Guest: the dinner has moved', 'guests', 'guests.phone', 'Hi {guest}, the dinner on {dinner} has moved to {new_date}. Please tell us if that works.' + HH),
    M('hm_declutter', 'Household member: the declutter starts', 'declutter', 'declutter.a2_phone', 'Hi {a2_name}, the spring declutter starts on {date}. There are {areas_total} areas, please pick yours.' + HH),
    M('hm_areas', 'Household member: areas not started', 'declutter', 'declutter.a2_phone', 'Hi {a2_name}, {areas_open} areas are not started. The next is {next_area}.' + HH),
    M('hm_dropoff', 'Household member: the donation drop-off', 'donations', 'donations.a1_phone', 'Hi {a1_name}, the donation drop-off is on {date}. We are giving {count} items.' + HH),
    M('hm_year', 'Household member: the year in review', 'year_review', 'year_review.a1_phone', 'Hi {a1_name}, the year in review for {year} is ready. {improved_n} of 14 measures improved.' + HH)]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def C_(*a): return 'COUNTIFS(' + ','.join(a) + ')'
K = lambda label, f, fmt='int', **kw: KPI(label, f, fmt, **kw)
OWNMAX = 'MAX(%s)' % ','.join(C_(PT('owner'), tok('powner', o), PT('open'), '1') for o in POWNER)
OPEN_PJ = 'SUMPRODUCT((%s<>"")*(COUNTIFS(%s,%s,%s,1)>0))' % (PR('project_id'), PT('project_id'), PR('project_id'), PT('open'))
kpis = [
    K('Projects in progress', OPEN_PJ),
    K('Project tasks open', C_(PT('open'), '1')),
    K('Project tasks done', C_(PT('status'), S_DONE)),
    K('Share of tasks done, all projects', 'IFERROR(%s/COUNTA(%s),0)' % (C_(PT('status'), S_DONE), PT('task_id')), 'pct'),
    K('Project tasks late', C_(PT('days_late'), '">0"'), alert={"when": "> 0", "style": "bad"}),
    K('Days late, worst task', 'MAX(%s)' % PT('days_late'), alert={"when": "> 0", "style": "bad"}),
    K('Blocked tasks', C_(PT('status'), S_BL), alert={"when": "> 0", "style": "warn"}),
    K('Phases at risk or late', '%s+%s' % (C_(PS('verdict'), W_RISK), C_(PS('verdict'), W_LATE)), alert={"when": "> 0", "style": "warn"}),
    K('Estimate of the open tasks', 'SUMIFS(%s,%s,1)' % (PT('est_cost'), PT('open')), 'money'),
    K('Actual cost to date', 'SUM(%s)' % PT('actual_cost'), 'money'),
    K('Bathroom finished work against estimate', 'IFERROR(SUMIFS(%s,%s,INDEX(%s,1))/SUMIFS(%s,%s,INDEX(%s,1)),0)' % (CL('paid'), CL('project'), PR('project'), CL('est_done'), CL('project'), PR('project')), 'pct'),
    K('Project tasks due in the next 14 days', 'SUM(%s)' % PT('next14')),
    K('Open tasks of the busiest owner', OWNMAX),
    K('Days to the holiday dinner', 'IF({set:dinner_date}="","",{set:dinner_date}-{today})'),
    K('Guests invited, people', 'SUM(%s)' % GS('party_size')),
    K('Guests confirmed, people', 'SUMIFS(%s,%s,%s)' % (GS('party_size'), GS('rsvp'), tok('rsvp', 'Yes'))),
    K('Guests maybe, people', 'SUMIFS(%s,%s,%s)' % (GS('party_size'), GS('rsvp'), tok('rsvp', 'Maybe'))),
    K('Hosting tasks open', C_(HT('done_flag'), '0', HT('task'), '"<>"')),
    K('Menu items not bought', C_(MS('bought'), NO, MS('item'), '"<>"'), alert={"when": "> 0", "style": "warn"}),
    K('Days to the move date, typed', '{set:move_date}-{today}'),
    K('Boxes counted', 'SUM(%s)' % MB('boxes')),
    K('Boxes packed', 'SUMIFS(%s,%s,%s)' % (MB('boxes'), MB('packed'), YES)),
    K('Change-of-address items left', C_(AD('done'), NO, AD('orgtype'), '"<>"'), alert={"when": "> 0", "style": "warn"}),
    K('Spring declutter decisions logged', C_(DL('project_id'), 'INDEX(%s,4)' % PR('project_id'))),
    K('Items donated', 'SUMIFS(%s,%s,%s)' % (DL('count'), DL('decision'), DONATE)),
    K('Items sold, value', 'SUMIFS(%s,%s,%s)' % (DL('value'), DL('decision'), SELL), 'money'),
    K('Items binned', 'SUMIFS(%s,%s,%s)' % (DL('count'), DL('decision'), BIN)),
    K('Areas not started', C_(DA('decided'), '0', DA('area'), '"<>"'), alert={"when": "> 0", "style": "warn"}),
    K('Donation drop-offs this year', 'SUMIFS(%s,%s,YEAR({today}))' % (DN('drop_off'), DN('year'))),
    K('Measures improved on last year', C_(YV('verdict'), W_IMP))]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Projects Dashboard", "kpis": kpis,
    "monthly": {"title": "Project cost lines: estimate and actual by due month", "date": "project_tasks.due", "series": [
        {"label": "Actual cost", "sum": "project_tasks.actual_cost", "date": "project_tasks.due"}, {"label": "Estimate", "sum": "project_tasks.est_cost", "date": "project_tasks.due"}]},
    "breakdowns": [{"title": "Tasks by status", "by": "project_tasks.status", "agg": "count"}, {"title": "Tasks by owner", "by": "project_tasks.owner", "agg": "count"},
                   {"title": "Declutter items by decision", "by": "declutter.decision", "value": "declutter.count", "agg": "sum"}, {"title": "Guests by reply", "by": "guests.rsvp", "value": "guests.party_size", "agg": "sum"}]}
def W(c, op, v): return (c, op, v)
DEC_ = lambda d: tok('decision', d)
insights = {"filters": [{"label": "Task owner", "list": "powner"}, {"label": "Task status", "list": "tstatus"}],
    "gauges": [
        {"title": "Project tasks done against planned", "num": AGG('count', 'project_tasks', where=[W('status', '=', tok('tstatus', 'Done'))]), "den": AGG('count', 'project_tasks')},
        {"title": "Hosting tasks done", "num": AGG('sum', 'hosting_timeline', 'hosting_timeline.done_flag'), "den": AGG('count', 'hosting_timeline')},
        {"title": "Shopping bought for the dinner", "num": AGG('count', 'menu_shop', where=[W('bought', '=', YESV)]), "den": AGG('count', 'menu_shop')},
        {"title": "Boxes packed", "num": AGG('sum', 'move_boxes', 'move_boxes.boxes', where=[W('packed', '=', YESV)]), "den": AGG('sum', 'move_boxes', 'move_boxes.boxes')},
        {"title": "Declutter areas started", "num": AGG('count', 'declutter_areas', where=[W('decided', '>', 0)]), "den": AGG('count', 'declutter_areas')},
        {"title": "Measures improved on last year", "num": AGG('count', 'year_review', where=[W('gain', '>', '{set:same_band}')]), "den": AGG('count', 'year_review', where=[W('has_last', '=', 1)])}],
    "charts": [
        CHART('Tasks by status', 'bar', 'project_tasks.status', [AGG('count', 'project_tasks', label='Tasks')]),
        CHART('Tasks by project', 'bar', 'project_tasks.project_id', [AGG('count', 'project_tasks', label='Tasks')]),
        CHART('Tasks by owner', 'bar', 'project_tasks.owner', [AGG('count', 'project_tasks', label='Tasks')]),
        CHART('Tasks due per month', 'column', 'month', [AGG('count', 'project_tasks', date='project_tasks.due', label='Tasks due')]),
        CHART('Tasks done per month', 'column', 'month', [AGG('count', 'project_tasks', date='project_tasks.done_on', where=[W('status', '=', tok('tstatus', 'Done'))], label='Tasks done')]),
        CHART('Days late by phase', 'bar', 'project_tasks.phase', [AGG('sum', 'project_tasks', 'project_tasks.days_late', label='Days late')]),
        CHART('Estimate against actual by project', 'bar', 'cost_lines.project', [AGG('sum', 'cost_lines', 'cost_lines.estimate', label='Estimate'), AGG('sum', 'cost_lines', 'cost_lines.actual', label='Actual')]),
        CHART('Cost lines by project phase', 'bar', 'project_status.phase', [AGG('sum', 'project_status', 'project_status.est', label='Estimate'), AGG('sum', 'project_status', 'project_status.actual', label='Actual')]),
        CHART('Actual cost per month', 'column', 'month', [AGG('sum', 'project_tasks', 'project_tasks.actual_cost', date='project_tasks.done_on', label='Actual cost')]),
        CHART('Share of tasks done by phase', 'bar', 'project_status.phase', [AGG('sum', 'project_status', 'project_status.share_done', label='Share done')]),
        CHART('Guests by reply', 'bar', 'guests.rsvp', [AGG('sum', 'guests', 'guests.party_size', label='People')]),
        CHART('Guests by preference label', 'bar', 'guests.pref_label', [AGG('count', 'guests', label='Guests')]),
        CHART('Menu packs to buy by section', 'bar', 'menu_shop.section', [AGG('sum', 'menu_shop', 'menu_shop.packs', label='Packs')]),
        CHART('Hosting tasks by owner', 'bar', 'hosting_timeline.owner', [AGG('count', 'hosting_timeline', label='Tasks')]),
        CHART('Boxes by room', 'bar', 'move_boxes.room', [AGG('sum', 'move_boxes', 'move_boxes.boxes', label='Boxes')]),
        CHART('Boxes packed and left by room', 'bar', 'move_boxes.room', [AGG('sum', 'move_boxes', 'move_boxes.boxes', where=[W('packed', '=', YESV)], label='Packed'), AGG('sum', 'move_boxes', 'move_boxes.left', label='Left')]),
        CHART('Notice needed by organisation type', 'bar', 'address_list.orgtype', [AGG('sum', 'address_list', 'address_list.notice_days', label='Notice, days')]),
        CHART('Declutter items by decision', 'bar', 'declutter.decision', [AGG('sum', 'declutter', 'declutter.count', label='Items')]),
        CHART('Declutter items by area', 'bar', 'declutter_areas.area', [AGG('sum', 'declutter_areas', 'declutter_areas.decided', label='Items')]),
        CHART('Items donated per month', 'column', 'month', [AGG('sum', 'declutter', 'declutter.count', date='declutter.date', where=[W('decision', '=', DEC_('Donate'))], label='Donated')]),
        CHART('Items sold and binned per month', 'column', 'month', [AGG('sum', 'declutter', 'declutter.count', date='declutter.date', where=[W('decision', '=', DEC_('Sell'))], label='Sold'),
                                                                   AGG('sum', 'declutter', 'declutter.count', date='declutter.date', where=[W('decision', '=', DEC_('Bin'))], label='Binned')]),
        CHART('Year in review: this year against last year', 'bar', 'year_review.measure', [AGG('sum', 'year_review', 'year_review.this_year', label='This year'), AGG('sum', 'year_review', 'year_review.last_year', label='Last year')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Project health", "why": "tasks, share done, the worst days late, blocked tasks and the cost of finished work against its estimate in one verdict: on track, at risk or late", "where": "Project health"},
    {"name": "Move date moved", "why": "type the days the move day moves: every step, notice and box group shifts, with the open items now before today and the extra overlap days", "where": "Move date moved"},
    {"name": "Hosting countdown", "why": "days left to the dinner, hosting tasks open and menu items not bought in one line", "where": "Hosting countdown"},
    {"name": "Guest count to menu quantities", "why": "every menu item scaled to the guests you type and rounded up to whole packs", "where": "Guest count to menu quantities"},
    {"name": "Critical path", "why": "the longest chain of waiting tasks, the slip a late task passes down the chain and the forecast finish", "where": "Critical path"},
    {"name": "Declutter progress by area", "why": "areas decided against areas not started, with the items decided in each area", "where": "Declutter progress by area"},
    {"name": "Year in review summary", "why": "the 14 measures of the home this year against last year, with how many improved and how many got worse", "where": "Year in review summary"},
    {"name": "RSVP summary", "why": "yes, maybe, no and no reply in people, with the guests to expect at the table", "where": "RSVP summary"},
    {"name": "Packing progress", "why": "boxes counted, packed and left against the days to the move day and the boxes a day to finish", "where": "Packing progress"},
    {"name": "Task owner load", "why": "open tasks and minutes per person in the look-ahead window against the agreed share", "where": "Task owner load"}]
competitors = [
    {"what": "project management app with a subscription", "lacks": "charges every year, keeps your plans in an account and has no cost line against the estimate, no move date scenario and no hosting or declutter pages for a home"},
    {"what": "single-sheet renovation tracker template", "lacks": "a list of tasks with a status and no dependencies, no days late, no critical path and no verdict for the project"},
    {"what": "moving checklist app with ads", "lacks": "a fixed list of steps with no box count by room, no change-of-address notice days and no shift when the move date changes"},
    {"what": "party planner app with a paywall", "lacks": "a guest list and a menu with no pack-rounded shopping quantities for the typed guest count and no timeline counted back from the date"},
    {"what": "decluttering challenge app", "lacks": "daily prompts with no log of keep, donate, sell and bin, no donation record and no progress by area"}]
guide = [
    'Start here: this workbook runs the things in your home with a start and an end: a renovation, a move, a holiday dinner and a declutter, and ends the year with a review. Type the household name on Start.',
    'Replace demo data: clear the yellow demo cells of Team, Projects, Project plan, Project tasks, Guests, Recipes, the menu and moving sheets, Declutter log and Year in review. Keep the lists and settings.',
    'Type the household and the outside contacts first on Team. The texts and the forms read the first names and phone numbers from there by role.',
    'Calculated sheets (Hosting timeline, Project status board, Task dependencies, Cost lines by project, Move countdown, Declutter areas, Donation log): type the phase, task number, step, area or number once and the rest fills in.',
    'Project routine, every week: set the status of each task on Project tasks, read Project status board for the verdict of each phase and use Critical path to see what a late task pushes back.',
    'Set the dinner date, the guests at the table and the move date in Settings. Every due date in Hosting timeline and Move countdown follows them.',
    'Hosting routine: type the replies on Guests, check the menu on Menu for the dinner, use Guest count to menu quantities for the packs, tick Bought on Menu shopping and read Hosting countdown.',
    'Move routine: count the boxes by room, tick Packed, work through Move countdown and the Change-of-address list and use Move date moved to see what changes if the move day shifts.',
    'Declutter routine: log what you decide in Declutter log (keep, donate, sell or bin and the count), read Declutter areas for the areas not started and keep the Donation log.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'The Year in review takes numbers you type or paste from the other seven workbooks of the suite; each workbook also works alone. Type last year where you kept it and write three lines for next year.',
    'Notice periods, lead times and costs are typical or your own: check each organisation, the trade quotes and your local rules.',
    'A single adult uses projects, declutter and the year review unchanged and scales hosting to the guest list. Renters use the move, declutter and hosting sheets and leave renovation tasks that need the landlord consent as Waiting.',
    'Why a workbook: one flat price, no yearly renewal, your data stays with you, nothing to link, no ads and no upsell. It runs in Excel and Google Sheets with no macros, no add-ins and no accounts.',
    'What this is not: not a project management service, not a booking service, not legal, financial, safety or medical advice. Every date and total is calculated from your entries.']
listing = {"title": "Home Projects, Hosting and Declutter Excel Template: Renovation Tracker, Move Planner, Dinner Hosting Plan, Declutter Log",
    "headline": "Run a renovation, a move, a holiday dinner and a declutter, then review the year",
    "tags": ["home project tracker", "renovation planner", "moving checklist", "move planner", "hosting planner", "dinner party planner", "declutter log", "donation log", "year in review", "home management", "household planner", "excel template", "no subscription"],
    "description": ("Run the projects of your home in one Excel workbook. Built for a single adult, a couple or a family, owners or renters: a bathroom refresh, a garden bed, a move, a holiday dinner for twelve and a spring declutter, each with a start, an end and an owner. "
        "Project tasks hold the owner, the dates, the status and the task each one waits for; Project status board gives every phase a verdict (on track, at risk or late) from the share done, the days late and the cost of finished work against its estimate, and Critical path shows what a late task pushes back.\n\n"
        "Type the move day and every countdown step from 8 weeks to 1 day before, every change-of-address notice and every box group follows it; the Move date moved tool shifts the date by the days you type and counts the open items that fall before today and the extra days both homes overlap. "
        "For the dinner, the guests and their replies, the menu, the shopping quantities rounded to packs for the guest count you type and the timeline counted back from the date give one line: days left, tasks open, items not bought.\n\n"
        f"The declutter log records keep, donate, sell or bin for every area, the donation log keeps the record and the year in review compares 14 measures of the home with last year. {len(tools)} tools, {len(forms)} printable sheets, {len(documents)} documents, {len(checklists)} checklists and {len(messages)} ready text messages to the household, the grandparent, the sitter, guests and the trades.\n\n"
        "This is part eight of the eight-part Home Management suite. A standard .xlsx workbook with no macros, no accounts and no yearly renewal, with a demo copy full of sample data and a blank copy. Dates, totals and verdicts are calculated from your entries and are not advice; notice periods and quotes are typical or your own, check each one."),
    "features": ["Project tasks with owner, dates, status and dependencies", "Verdict per phase: on track, at risk or late", "Critical path and forecast finish", "Move date scenario: every step, notice and box group shifts",
                 "Guest list, menu and pack-rounded shopping for the guest count", "Hosting timeline counted back from the dinner date", f"{len(tools)} tools for the questions of every project", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", "Declutter and donation logs with progress by area", f"{len(messages)} ready text messages", "No macros, no accounts, no yearly renewal"]}
lists = lists_base + verdict_lists()
assert len(lists) <= 20, len(lists)
s = spec(id=f'{SUITE}-p8', slug='home-management-projects', profession='Home Management', name='Projects, Hosting and Declutter',
         tagline='Run a renovation, a move, a holiday dinner and a declutter, then review the year', price_usd=29,
         colors={"primary": "#3E5C76", "accent": "#E07A5F"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 8, "of": 8, "focus": "Projects, hosting and declutter"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ho8.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'lists', len(lists), 'desc', len(listing['description']), 'title', len(listing['title']))
