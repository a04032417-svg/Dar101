"""Childcare center suite - part 6: Meals, Health and Safety Records."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from cc6_lists import *
from cc6_tables import settings, tables
from cc6_tools import tools

SUITE = 'fx-20261115-childcare-center'
NOTE = "Sample wording: adapt it to your own center and check your local rules."
def F(*pairs): return [FV(a, b) for a, b in pairs]
MS = 'DATE(YEAR({today}),MONTH({today}),1)'
SIGN = 'Willow Lane Early Learning'
ONF, DUE, MISS = tok('hstatus', 'On file'), tok('hstatus', 'Due'), tok('hstatus', 'Missing'); OPEN = tok('fup', 'Open')

forms = [
    FORM('meal_count_sheet', 'Daily Meal Count Sheet', 'Daily meal count for one meal and room', 'meals.meal_id', F(
        ('Date', 'meals.date'), ('Meal', 'meals.meal'), ('Room', 'meals.room'), ('Children present', 'meals.children_present'), ('Meals served', 'meals.served'), ('Eligible meals', 'meals.eligible'),
        ('Unit cost', 'meals.unit_cost'), ('Cost', 'meals.cost'), ('Over by', 'meals.over_by'), ('Meal check', 'meals.check_flag')) + [
        FF('Meals served at this meal that day', 'SUMIFS({range:meals.served},{range:meals.date},INDEX({range:meals.date},MATCH({pick},{range:meals.meal_id},0)),{range:meals.meal},INDEX({range:meals.meal},MATCH({pick},{range:meals.meal_id},0)))', 'int')]),
    FORM('menu_plan_sheet', 'Menu Plan Sheet', 'Menu plan for one dish with the day and the order', 'menu.menu_id', F(
        ('Cycle week', 'menu.cycle_week'), ('Weekday', 'menu.weekday'), ('Meal', 'menu.meal'), ('Dish', 'menu.dish'), ('Cost per child', 'menu.cost_child'), ('Portions per kg', 'menu.portions_per_kg'),
        ('Cost of the day per child', 'menu.day_cost'), ('Kilograms for your order', 'menu.kg_order'), ('Cost for your order', 'menu.cost_order'), ('Cost rank in the meal', 'menu.meal_rank'),
        ('Breakfast of the day', 'menu.dish_b'), ('Lunch of the day', 'menu.dish_l'), ('Snack of the day', 'menu.dish_s'))),
    FORM('food_order_sheet', 'Food Order Sheet', 'Food order with cost per child-day', 'food.exp_id', F(
        ('Date', 'food.date'), ('Category', 'food.category'), ('Description', 'food.description'), ('Amount', 'food.amount'), ('Paid to', 'food.paid_to'), ('Supplier phone', 'food.supplier_phone'),
        ('Child-days that week', 'food.child_days'), ('Cost per child-day', 'food.per_child_day'), ('Cost check', 'food.cost_flag'))),
    FORM('claim_check_sheet', 'Meal Claim Check Sheet', 'Meal-program claim check for one month and meal', 'claim.claim_id', F(
        ('Month', 'claim.month'), ('Meal', 'claim.meal'), ('Children present', 'claim.children_present'), ('Meals served', 'claim.served'), ('Eligible meals', 'claim.eligible'), ('Days failing the check', 'claim.days_failing'),
        ('Claim rate', 'claim.claim_rate'), ('Claim amount', 'claim.claim_amount'), ('Served share of present', 'claim.served_share'), ('Claim check', 'claim.check_flag'))),
    FORM('allergy_update_sheet', 'Allergy Status Update Sheet', 'Allergy status update for one child, status only', 'cook.child_id', F(
        ('Child', 'cook.child'), ('Room', 'cook.room'), ('Allergy status', 'cook.allergy'), ('Allergy status due', 'cook.allergy_due'), ('Medical permission', 'cook.permission'), ('Records not on file', 'cook.open_records'),
        ('Diet list check', 'cook.diet_flag'), ('Family phone', 'cook.phone'))),
    FORM('permission_sheet', 'Medical Permission Sheet', 'Medical permission chase, status only', 'follow.fu_id', F(
        ('Child', 'follow.child'), ('Family', 'follow.family'), ('Room', 'follow.room'), ('Record', 'follow.record'), ('Status', 'follow.status'), ('Due date', 'follow.due_date'), ('Days past due', 'follow.days_overdue'),
        ('Next step', 'follow.action'), ('Family phone', 'follow.phone'))),
    FORM('immunisation_sheet', 'Immunisation Status Sheet', 'Record status for one child and record', 'health.record_id', F(
        ('Child', 'health.child'), ('Room', 'health.room'), ('Record', 'health.record'), ('Status', 'health.status'), ('Due date', 'health.due_date'), ('Last checked', 'health.last_checked'), ('Days past due', 'health.days_past'),
        ('Days to the due date', 'health.days_left'), ('Record check', 'health.record_flag'), ('Family', 'health.family'), ('Family phone', 'health.phone')) + [
        FF('Records of this child not on file', 'COUNTIFS({range:health.child_id},INDEX({range:health.child_id},MATCH({pick},{range:health.record_id},0)),{range:health.status},"<>"&%s)' % ONF, 'int')]),
    FORM('incident_report_sheet', 'Incident Report Sheet', 'Incident report: date, room, type, status', 'incidents.incident_id', F(
        ('Date', 'incidents.date'), ('Time', 'incidents.incident_time'), ('Child', 'incidents.child'), ('Room', 'incidents.room'), ('Type', 'incidents.type'), ('Family told', 'incidents.parent_informed'),
        ('Staff member', 'incidents.staff'), ('Follow-up done', 'incidents.follow_up_done'), ('Hour of the day', 'incidents.hour_slot'), ('Family phone', 'incidents.phone'))),
    FORM('incident_follow_sheet', 'Incident Follow-up Sheet', 'Incident follow-up check for one incident', 'incidents.incident_id', F(
        ('Date', 'incidents.date'), ('Child', 'incidents.child'), ('Room', 'incidents.room'), ('Type', 'incidents.type'), ('Family told', 'incidents.parent_informed'), ('Follow-up done', 'incidents.follow_up_done'),
        ('Follow-up check', 'incidents.follow_flag'), ('Days the follow-up is open', 'incidents.open_days'), ('Family', 'incidents.family'), ('Family phone', 'incidents.phone')) + [
        FF('Incidents of this child in the log', 'COUNTIFS({range:incidents.child_id},INDEX({range:incidents.child_id},MATCH({pick},{range:incidents.incident_id},0)))', 'int')]),
    FORM('drill_record_sheet', 'Drill Record Sheet', 'Drill record for one drill', 'drills.drill_id', F(
        ('Date', 'drills.date'), ('Kind', 'drills.kind'), ('Minutes', 'drills.minutes'), ('Children present', 'drills.children_present'), ('Run by', 'drills.staff'), ('Status', 'drills.status'), ('Children per minute', 'drills.children_per_minute')) + [
        FF('Drills of this kind in the log', 'COUNTIFS({range:drills.kind},INDEX({range:drills.kind},MATCH({pick},{range:drills.drill_id},0)))', 'int')]),
    FORM('cleaning_check_sheet', 'Cleaning Check Sheet', 'Cleaning check record for one room and day', 'checks.check_id', F(
        ('Date', 'checks.date'), ('Room', 'checks.room'), ('Kind', 'checks.kind'), ('Status', 'checks.status'), ('Done by', 'checks.done_by'), ('Minutes', 'checks.minutes'), ('Week', 'checks.week'), ('Lead teacher phone', 'checks.teacher_phone'))),
    FORM('safety_check_sheet', 'Safety Check Sheet', 'Safety check schedule line for one room and kind', 'clean_sched.cs_id', F(
        ('Room', 'clean_sched.room'), ('Kind', 'clean_sched.kind'), ('Days between checks', 'clean_sched.freq_days'), ('Last done', 'clean_sched.last_done'), ('Next due', 'clean_sched.next_due'), ('Days overdue', 'clean_sched.days_overdue'),
        ('Schedule check', 'clean_sched.sched_flag'), ('Missed in the room, last 90 days', 'clean_sched.room_missed'), ('Lead teacher phone', 'clean_sched.teacher_phone'))),
]
assert len(forms) == 12

documents = [
    DOC('weekly_menu', 'Weekly Menu for Families', 'Weekly menu for families, one day of the cycle', 'menu.menu_id', [
        'Menu of {set:company}, dated {today}. Menu cycle week {col:menu.cycle_week}, {col:menu.weekday}.',
        'Breakfast: {col:menu.dish_b}. Lunch: {col:menu.dish_l}. Afternoon snack: {col:menu.dish_s}.',
        'Please tell us about any change in your child\'s food status before the next menu week. Menus can change when a delivery is late; we will tell you the same day.'], ['Cook', 'Owner-director'], NOTE),
    DOC('meal_counts_week', 'Meal Counts for the Week', 'Meal counts for the week', 'menu_week.mw_id', [
        'Meal counts of {set:company}, dated {today}. Week of {col:menu_week.week}, {col:menu_week.open_days} open days.',
        'Child-days present {col:menu_week.child_days}. Breakfasts served {col:menu_week.served_b}, lunches {col:menu_week.served_l}, afternoon snacks {col:menu_week.served_s}; meals served in total {col:menu_week.meals_served}, {col:menu_week.meals_per_day} a day.',
        'Cost of the meals {col:menu_week.meals_cost}, which is {col:menu_week.cost_child_day} per child-day against your 12-week average of {col:menu_week.avg12}. Cost check: {col:menu_week.cost_flag}.'], ['Cook', 'Assistant director'], NOTE),
    DOC('supplier_list', 'Shopping List for the Supplier', 'Shopping list line for the food supplier', 'menu.menu_id', [
        'Shopping list of {set:company}, dated {today}. Menu cycle week {col:menu.cycle_week}, {col:menu.weekday}, {col:menu.meal}.',
        'Dish: {col:menu.dish}. Portions per kilogram: {col:menu.portions_per_kg}. For {set:order_children} children we need {col:menu.kg_order} kilograms, at a cost of {col:menu.cost_order}.',
        'Please confirm the quantity and the delivery day. If a price has changed, tell us before the delivery so we can update the menu cost.'], ['Cook', 'Food supplier'], NOTE),
    DOC('claim_sheet_doc', 'Monthly Meal Claim Sheet', 'Monthly meal-program claim sheet for one meal', 'claim.claim_id', [
        'Meal claim sheet of {set:company}, dated {today}. Month of {col:claim.month}, meal: {col:claim.meal}.',
        'Children present at the meal {col:claim.children_present}. Meals served {col:claim.served}. Eligible meals {col:claim.eligible}. Days failing the count check {col:claim.days_failing}.',
        'Claim at the rate of {col:claim.claim_rate} per eligible meal: {col:claim.claim_amount}. Check: {col:claim.check_flag}. A claim is made to a food program for meals served; check your local rules before you send it.'], ['Assistant director', 'Owner-director'], NOTE),
    DOC('cook_status_list', 'Allergy Status List', 'Allergy and permission status for the cook', 'cook.child_id', [
        'Status list of {set:company}, dated {today}. Child: {col:cook.child}, room {col:cook.room}.',
        'Allergy status: {col:cook.allergy}, due {col:cook.allergy_due}. Medical permission: {col:cook.permission}. Records not on file: {col:cook.open_records}. Diet list check: {col:cook.diet_flag}.',
        'This list holds status and dates only. Ask the family for the detail and keep it where your local rules say. Update the list the same day a status changes.'], ['Cook', 'Assistant director'], NOTE),
    DOC('records_due_room', 'Records Due List by Room', 'Records due list for a room and record', 'board.board_id', [
        'Records due list of {set:company}, dated {today}. Room: {col:board.room}. Record: {col:board.record}.',
        'On file {col:board.on_file}, due {col:board.due}, missing {col:board.missing}, share on file {col:board.share_on_file}. Nearest due date: {col:board.next_due}. Board check: {col:board.board_flag}.',
        'The lead teacher asks each family on the list for the update. The assistant director checks the list again at the end of the week.'], ['Lead teacher', 'Assistant director'], NOTE),
    DOC('incident_notice', 'Incident Notice for a Family', 'Incident notice for a family: date, room, type, status', 'incidents.incident_id', [
        'Incident notice of {set:company}, dated {today}. Child: {col:incidents.child}, room {col:incidents.room}.',
        'Date and time: {col:incidents.date}, {col:incidents.incident_time}. Type: {col:incidents.type}. Staff member: {col:incidents.staff}. Family told: {col:incidents.parent_informed}. Follow-up status: {col:incidents.follow_flag}.',
        'Please call us if you want to talk about it. We keep a record of every incident and close each follow-up with the family.'], ['Staff member', 'Parent or guardian'], NOTE),
    DOC('incident_summary', 'Monthly Incident Summary', 'Monthly incident summary for the owner-director', 'inc_month.im_id', [
        'Incident summary of {set:company}, dated {today}. Room: {col:inc_month.room}, month of {col:inc_month.month}.',
        'Incidents {col:inc_month.incidents} over {col:inc_month.child_days} child-days, which is {col:inc_month.per1000} per 1,000 child-days against your usual {col:inc_month.usual} for the room. Rate check: {col:inc_month.rate_flag}.',
        'Incidents in the room over the last 3 months: {col:inc_month.room_90}. Read the incident log for the hours and types before you decide anything.'], ['Assistant director', 'Owner-director'], NOTE),
    DOC('drill_record_doc', 'Drill Record', 'Drill record for one drill', 'drills.drill_id', [
        'Drill record of {set:company}, dated {today}. Kind: {col:drills.kind}. Date: {col:drills.date}.',
        'Minutes {col:drills.minutes}. Children present {col:drills.children_present}. Run by {col:drills.staff}. Status: {col:drills.status}. Children per minute {col:drills.children_per_minute}.',
        'Write below anything to improve for the next drill. Keep this record where your local rules say.'], ['Staff member', 'Owner-director'], NOTE),
    DOC('drill_schedule_year', 'Drill Schedule for the Year', 'Drill schedule line for a month and kind', 'drill_plan.dp_id', [
        'Drill schedule of {set:company}, dated {today}. Month: {col:drill_plan.month}. Kind: {col:drill_plan.kind}.',
        'Months between drills {col:drill_plan.freq}. Last drill before the month {col:drill_plan.last_prior}. Due date {col:drill_plan.due_date}. Done on {col:drill_plan.done_on}. Status: {col:drill_plan.flag}.',
        'The months between drills are your own plan; check your local rules for what you must hold.'], ['Assistant director', 'Owner-director'], NOTE),
    DOC('clean_schedule_doc', 'Cleaning Schedule Sheet', 'Cleaning and safety schedule for a room', 'clean_sched.cs_id', [
        'Cleaning and safety schedule of {set:company}, dated {today}. Room: {col:clean_sched.room}. Kind: {col:clean_sched.kind}.',
        'Every {col:clean_sched.freq_days} days. Last done {col:clean_sched.last_done}. Next due {col:clean_sched.next_due}. Days overdue {col:clean_sched.days_overdue}. Schedule check: {col:clean_sched.sched_flag}.',
        'Missed checks in this room in the last 90 days: {col:clean_sched.room_missed}. The lead teacher signs when the check is done.'], ['Lead teacher', 'Assistant director'], NOTE),
    DOC('completion_report', 'Completion Report', 'Safety and cleaning completion report for a room', 'check_week.cw_id', [
        'Completion report of {set:company}, dated {today}. Room: {col:check_week.room}, week of {col:check_week.week}.',
        'Checks done {col:check_week.done}, missed {col:check_week.missed}, completion share {col:check_week.completion}. Target check against {set:completion_target}: {col:check_week.target_flag}.',
        'This report helps you keep track of checks; it does not replace your own judgement or your local rules.'], ['Lead teacher', 'Owner-director'], NOTE),
]
assert len(documents) == 12

checklists = [
    CHK('plan_menu', 'Planning the Weekly Menu Steps', 'menu_week', 'menu_week.week', [('Look at last week\'s cost per child-day', -5), ('Pick the dishes for each weekday from the cycle', -4), ('Check the menu against the allergy status list', -4), ('Check the cost of the day against your usual', -3), ('Share the menu with families', -2), ('Send the menu to the cook and the supplier', -2)]),
    CHK('daily_meal_count', 'Daily Meal Count Steps', 'meals', 'meals.date', [('Count the children present in each room before the meal', 0), ('Write the meals served for each meal and room', 0), ('Check that meals served do not exceed children present', 0), ('Mark the eligible meals', 0), ('Hand the sheet to the assistant director', 1)]),
    CHK('weekly_food_order', 'Weekly Food Order Steps', 'food', 'food.date', [('Count the stock left', -4), ('Build the shopping list from the menu and the counts', -3), ('Check the quantity against the meals served last week', -3), ('Send the order to the supplier', -2), ('Check the delivery against the order', 0), ('Record the amount paid', 1)]),
    CHK('month_end_claim', 'Month-End Meal Claim Steps', 'claim', 'claim.month', [('Add up the meals served and eligible by type', 28), ('Fix any day where meals served are above children present', 29), ('Check the claim at your own rates', 30), ('Ask the owner-director to check the total', 31), ('Send the claim following your local rules', 32), ('File the sheet', 33)]),
    CHK('enrol_records', 'Enrolment Records Check Steps', 'children', 'children.start_date', [('List the four records for the child', -14), ('Ask the family for each record', -14), ('Write the status and due date of each record', -7), ('Check the allergy status with the cook list', -3), ('Check the emergency contacts and the pickup list', -1), ('Re-check on the first day', 0)]),
    CHK('monthly_records', 'Monthly Records Review Steps', 'health', 'health.due_date', [('Open the status board for every room', -30), ('List the records due in 30 days', -30), ('Send a reminder to each family', -28), ('Call the families past their due date', -14), ('Pass records past 21 days to the owner-director', -7), ('Update the cook list', 0)]),
    CHK('record_incident', 'Recording an Incident Steps', 'incidents', 'incidents.date', [('Make sure every child is safe and supervised', 0), ('Write the date, time, room and type', 0), ('Tell the family the same day', 0), ('Write who was told and when', 0), ('Set the follow-up for the next day', 1)]),
    CHK('incident_followup', 'Incident Follow-up Steps', 'incidents', 'incidents.date', [('Speak to the family about the incident', 1), ('Ask whether the family wants to add anything', 1), ('Check the room for a cause and fix it', 2), ('Tell the team at the next meeting', 3), ('Mark the follow-up done', 3)]),
    CHK('fire_drill', 'Fire Drill Steps', 'drills', 'drills.date', [('Choose the day and tell the staff', -7), ('Check the exits are clear', -1), ('Sound the alarm and start the clock', 0), ('Count every child at the meeting point', 0), ('Write the minutes and the children present', 0), ('Talk about what to improve', 1)]),
    CHK('evacuation_drill', 'Evacuation Drill Steps', 'drill_plan', 'drill_plan.month', [('Plan the route for every room', 0), ('Tell the staff the week of the drill', 7), ('Check the exits and the meeting point', 14), ('Run the drill and time it', 15), ('Count the children and the staff', 15), ('Record the drill and the improvements', 16)]),
    CHK('daily_clean', 'Daily Cleaning Check Steps', 'checks', 'checks.date', [('Check the floor and the play area for hazards', 0), ('Clean tables and shared surfaces', 0), ('Check the exits and the gates', 0), ('Check the equipment for damage', 0), ('Write the check as done or missed', 0)]),
    CHK('weekly_deep_clean', 'Weekly Deep Clean Steps', 'check_week', 'check_week.week', [('Plan the room for the deep clean', 0), ('Clean toys and shared equipment', 1), ('Wash soft items and bedding', 2), ('Clean floors and sanitary areas', 3), ('Check the cleaning supplies', 4), ('Record the deep clean for the room', 4)]),
]
assert len(checklists) == 12

def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text + ' ' + SIGN)
messages = [
    M('f_immun', 'Family: your record is due', 'health', 'health.phone', 'Hello, the {record} record for {child} is due on {due_date}. Please send the update.'),
    M('f_permission', 'Family: permission form is missing', 'health', 'health.phone', 'Hello, the medical permission form for {child} is missing. Please return it.'),
    M('f_allergy', 'Family: confirm the allergy status', 'cook', 'cook.phone', 'Hello, please confirm that the allergy status on file for {child} is current.'),
    M('f_contacts', 'Family: update emergency contacts', 'health', 'health.phone', 'Hello, the emergency contacts for {child} need an update. Please send them by {due_date}.'),
    M('f_pastdue', 'Family: a record is past due', 'health', 'health.phone', 'Hello, the {record} record for {child} is now {days_past} days past due. Please send it today.'),
    M('f_thanks', 'Family: thank you, record on file', 'health', 'health.phone', 'Thank you, the {record} record for {child} is on file.'),
    M('f_incident', 'Family: an incident was recorded', 'incidents', 'incidents.phone', 'Hello, an incident of type {type} was recorded on {date} in the {room} room. Follow-up status: {follow_flag}.'),
    M('f_informed', 'Family: you were told about the incident', 'incidents', 'incidents.phone', 'Hello, you were told about the incident of {date} for {child}. Is there anything you want to add?'),
    M('f_menu', 'Family: this week\'s menu', 'children', 'children.phone', 'Hello {guardian}, this week\'s menu is on the notice board. Please tell us about any change in the food status of {child}.'),
    M('f_menuchange', 'Family: a menu change', 'children', 'children.phone', 'Hello, the menu changes on {next_day}. Please ask us if {child} needs anything different.'),
    M('f_foodstatus', 'Family: tell us of any food change', 'children', 'children.phone', 'Hello, please tell us any change in the food status of {child} before the next menu week.'),
    M('f_drill', 'Family: a drill took place', 'children', 'children.phone', 'Hello, a drill took place on {last_drill}. No action is needed from the family of {child}.'),
    M('c_list', 'Cook: today\'s list by room is ready', 'board', 'board.cook_phone', 'Hello, the list for the {room} room is ready: {on_file} on file, {due} due and {missing} missing for {record}.'),
    M('c_newallergy', 'Cook: new allergy status', 'cook', 'cook.cook_phone', 'Hello, there is a new allergy status for {child} in the {room} room. Please check the list.'),
    M('c_counts', 'Cook: meal counts for tomorrow', 'menu_week', 'menu_week.cook_phone', 'Hello, in the week of {week} we served {meals_served} meals, {meals_per_day} a day. Please plan tomorrow\'s counts from that.'),
    M('c_menu', 'Cook: the menu for next week is ready', 'menu_week', 'menu_week.cook_phone', 'Hello, the menu for next week is ready. Please confirm quantities: in the week of {week} we served {child_days} child-days at {cost_child_day} per child-day.'),
    M('c_claim', 'Cook: the claim sheet has days to check', 'claim', 'claim.cook_phone', 'Hello, the claim sheet for {month} has {days_failing} days to check for {meal}. Please look at the counts.'),
    M('s_order', 'Food supplier: the order is attached', 'food', 'food.supplier_phone', 'Hello, the order for {date} is attached. Please confirm the delivery day.'),
    M('s_qty', 'Food supplier: quantities changed', 'food', 'food.supplier_phone', 'Hello, the quantities for the order of {date} changed. Please confirm the new list before the delivery.'),
    M('s_price', 'Food supplier: price change received', 'food', 'food.supplier_phone', 'Hello, we received your price change. The order of {date} was {amount}; please send the new price list.'),
    M('s_short', 'Food supplier: the delivery was short', 'food', 'food.supplier_phone', 'Hello, the delivery on {date} was short. Please tell us when the rest will arrive.'),
    M('t_records', 'Lead teacher: records due in your room', 'board', 'board.teacher_phone', 'Hello, in the {room} room {due} records are due and {missing} are missing for {record}. Please ask the families this week.'),
    M('t_followup', 'Lead teacher: please close the follow-up', 'incidents', 'incidents.teacher_phone', 'Hello, please close the follow-up for {child}, incident of {date}. It has been open {open_days} days.'),
    M('t_missed', 'Lead teacher: your room missed checks', 'check_week', 'check_week.teacher_phone', 'Hello, the {room} room missed {missed} checks in the week of {week}. Please catch up.'),
    M('t_drill', 'Lead teacher: a drill is due this month', 'drill_plan', 'drill_plan.lead_phone', 'Hello, a {kind} is due in {month}. Please plan it for your room.'),
    M('a_check', 'Assistant: please complete the check', 'clean_sched', 'clean_sched.assistant_phone', 'Hello, please complete the {kind} for the {room} room, due on {next_due}.'),
    M('cl_deep', 'Cleaner: a deep clean is due', 'clean_sched', 'clean_sched.cleaner_phone', 'Hello, the {kind} for the {room} room is due on {next_due}.'),
    M('cl_week', 'Cleaner: the weekly clean list', 'check_week', 'check_week.cleaner_phone', 'Hello, the weekly clean list for the week of {week}: the {room} room has {missed} missed checks to redo.'),
    M('m_equipment', 'Maintenance: equipment check due', 'clean_sched', 'clean_sched.maint_phone', 'Hello, the equipment check is due in the {room} room on {next_due}.'),
    M('m_issue', 'Maintenance: a safety issue was logged', 'incidents', 'incidents.maint_phone', 'Hello, a safety issue was logged on {date} in the {room} room. Please check the area.'),
    M('ad_records', 'Assistant director: records to chase', 'follow', 'follow.ad_phone', 'Hello, {child}: the {record} record is {status}, {days_overdue} days past due. Next step: {action}.'),
    M('ad_incidents', 'Assistant director: no follow-up yet', 'incidents', 'incidents.ad_phone', 'Hello, the incident of {date} for {child} has no follow-up yet. It has been open {open_days} days.'),
    M('o_claim', 'Owner: the monthly claim is ready', 'claim', 'claim.owner_phone', 'Hello, the claim for {month}, {meal}, is {claim_amount}. Please check it. Status: {check_flag}.'),
    M('o_drills', 'Owner: drills overdue', 'drill_plan', 'drill_plan.owner_phone', 'Hello, the {kind} due on {due_date} is {flag}.'),
]
assert len(messages) == 34, len(messages)

def CNT(*w): return 'COUNTIFS(%s)' % ','.join(w)
def R(t, c): return '{range:%s.%s}' % (t, c)
M30 = '%s,">"&({today}-30),%s,"<="&{today}'
kpis = [
    KPI('Meals served this month', 'SUMIFS(%s,%s,%s)' % (R('claim', 'served'), R('claim', 'month'), MS), 'int'),
    KPI('Meals served, last 30 days', 'SUMIFS(%s,%s,">"&({today}-30))' % (R('meals', 'served'), R('meals', 'date')), 'int'),
    KPI('Meals served on the last open day', 'SUMIFS(%s,%s,MAX(%s))' % (R('meals', 'served'), R('meals', 'date'), R('meals', 'date')), 'int'),
    KPI('Average meals per open day, last 4 weeks', 'IFERROR(SUMIFS(%s,%s,">"&({today}-28))/SUMIFS(%s,%s,">"&({today}-28)),0)' % (R('menu_week', 'meals_served'), R('menu_week', 'week'), R('menu_week', 'open_days'), R('menu_week', 'week')), 'num'),
    KPI('Food cost this month', 'SUMIFS(%s,%s,">="&%s)' % (R('food', 'amount'), R('food', 'date'), MS), 'money'),
    KPI('Food cost per child-day, last 4 weeks', 'IFERROR(SUMIFS(%s,%s,">"&({today}-28))/SUMIFS(%s,%s,">"&({today}-28)),0)' % (R('food', 'amount'), R('food', 'date'), R('menu_week', 'child_days'), R('menu_week', 'week')), 'money'),
    KPI('Food cost per child-day, last 12 months', 'IFERROR(SUMIFS(%s,%s,">"&({today}-364))/SUMIFS(%s,%s,">"&({today}-364)),0)' % (R('food', 'amount'), R('food', 'date'), R('menu_week', 'child_days'), R('menu_week', 'week')), 'money'),
    KPI('Days failing the meal check, 12 months', 'SUMIFS(%s,%s,">"&EDATE(%s,-12))' % (R('claim', 'days_failing'), R('claim', 'month'), MS), 'int'),
    KPI('Meal claim, last full month', 'SUMIFS(%s,%s,EDATE(%s,-1))' % (R('claim', 'claim_amount'), R('claim', 'month'), MS), 'money'),
    KPI('Records on file', 'COUNTIFS(%s,%s)' % (R('health', 'status'), ONF), 'int'),
    KPI('Records due in the next 30 days', 'COUNTIFS(%s,%s,%s,">="&{today},%s,"<="&({today}+{set:record_warn_days}))' % (R('health', 'status'), DUE, R('health', 'due_date'), R('health', 'due_date')), 'int'),
    KPI('Records missing', 'COUNTIFS(%s,%s)' % (R('health', 'status'), MISS), 'int'),
    KPI('Records past due', 'COUNTIFS(%s,">0")' % R('health', 'days_past'), 'int'),
    KPI('Children with all records on file', 'COUNTIFS(%s,0)' % R('cook', 'open_records'), 'int'),
    KPI('Oldest record past due, days', 'MAX(%s)' % R('health', 'days_past'), 'int'),
    KPI('Incidents this month', 'COUNTIFS(%s,">="&%s)' % (R('incidents', 'date'), MS), 'int'),
    KPI('Incidents, last 30 days', 'COUNTIFS(%s,">"&({today}-30))' % R('incidents', 'date'), 'int'),
    KPI('Incidents per 1,000 child-days, 3 months', 'IFERROR(SUMIFS(%s,%s,">="&EDATE(%s,-2))/SUMIFS(%s,%s,">="&EDATE(%s,-2))*1000,0)' % (R('inc_month', 'incidents'), R('inc_month', 'month'), MS, R('inc_month', 'child_days'), R('inc_month', 'month'), MS), 'num'),
    KPI('Busiest incident hour', 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (R('inc_hour', 'hour'), R('inc_hour', 'incidents'), R('inc_hour', 'incidents')), 'text'),
    KPI('Room with most incidents, 3 months', 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (R('inc_month', 'room'), R('inc_month', 'room_90'), R('inc_month', 'room_90')), 'text'),
    KPI('Families not told', 'COUNTIFS(%s,%s)' % (R('incidents', 'parent_informed'), NO), 'int'),
    KPI('Follow-ups open', 'COUNTIFS(%s,%s)' % (R('incidents', 'follow_up_done'), OPEN), 'int'),
    KPI('Oldest open follow-up, days', 'MAX(%s)' % R('incidents', 'open_days'), 'int'),
    KPI('Drills done this year', 'COUNTIFS(%s,">="&DATE(YEAR({today}),1,1),%s,%s)' % (R('drills', 'date'), R('drills', 'status'), tok('dstatus', 'Done')), 'int'),
    KPI('Drills overdue', 'COUNTIFS(%s,1)' % R('drill_plan', 'overdue'), 'int'),
    KPI('Days since the last drill', '{today}-MAX(%s)' % R('drills', 'date'), 'int'),
    KPI('Check completion, last 4 weeks', 'IFERROR(COUNTIFS(%s,%s,%s,">"&({today}-28))/COUNTIFS(%s,">"&({today}-28)),0)' % (R('checks', 'status'), tok('checkstatus', 'Done'), R('checks', 'date'), R('checks', 'date')), 'pct'),
    KPI('Checks missed, last 90 days', 'COUNTIFS(%s,%s,%s,">"&({today}-90))' % (R('checks', 'status'), tok('checkstatus', 'Missed'), R('checks', 'date')), 'int'),
    KPI('Room with most missed checks, 90 days', 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (R('clean_sched', 'room'), R('clean_sched', 'room_missed'), R('clean_sched', 'room_missed')), 'text'),
    KPI('Deep cleans done this month', 'COUNTIFS(%s,">="&%s,%s,%s,%s,%s)' % (R('checks', 'date'), MS, R('checks', 'kind'), tok('ckind', 'Deep clean'), R('checks', 'status'), tok('checkstatus', 'Done')), 'int'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Meals and Safety Dashboard", "kpis": kpis,
    "monthly": {"title": "Food purchases and meal claim", "date": "food.date", "series": [
        {"label": "Food purchases", "sum": "food.amount", "date": "food.date"}, {"label": "Meal claim", "sum": "claim.claim_amount", "date": "claim.month"}]},
    "breakdowns": [{"title": "Records by status", "by": "health.status", "value": "health.days_past", "agg": "count"}, {"title": "Incidents by room", "by": "incidents.room", "value": "incidents.open_days", "agg": "count"},
                   {"title": "Meals served by room", "by": "meals.room", "value": "meals.served", "agg": "sum"}, {"title": "Missed checks by room", "by": "check_week.room", "value": "check_week.missed", "agg": "sum"}]}
def AF(t, col): return AGG('count', t, where=[(col[0], col[1], col[2])])
insights = {"filters": [{"label": "Room", "list": "room"}],
    "gauges": [{"title": "Records on file", "num": AGG('count', 'health', where=[('status', '=', ONF)]), "den": AGG('count', 'health')},
               {"title": "Meal counts consistent with attendance", "num": AGG('count', 'meals', where=[('over_by', '=', 0)]), "den": AGG('count', 'meals')},
               {"title": "Incidents with a follow-up done", "num": AGG('count', 'incidents', where=[('follow_up_done', '=', tok('fup', 'Done'))]), "den": AGG('count', 'incidents')},
               {"title": "Drills current", "num": AGG('sum', 'drill_plan', 'drill_plan.ok_now'), "den": AGG('sum', 'drill_plan', 'drill_plan.is_now')},
               {"title": "Checks completed", "num": AGG('count', 'checks', where=[('status', '=', tok('checkstatus', 'Done'))]), "den": AGG('count', 'checks')},
               {"title": "Food cost against your own average", "num": AGG('sum', 'menu_week', 'menu_week.at_or_below'), "den": AGG('count', 'menu_week')}],
    "charts": [
        CHART('Meals per month', 'bar', 'month', [AGG('sum', 'claim', 'claim.served', date='claim.month', label='Meals served')]),
        CHART('Meals by type', 'bar', 'claim.meal', [AGG('sum', 'claim', 'claim.served', label='Meals served'), AGG('sum', 'claim', 'claim.eligible', label='Eligible meals')]),
        CHART('Meals by room', 'bar', 'meals.room', [AGG('sum', 'meals', 'meals.served', label='Meals served')]),
        CHART('Food cost per month', 'bar', 'month', [AGG('sum', 'food', 'food.amount', date='food.date', label='Food purchases')]),
        CHART('Cost per child-day per month', 'column', 'month', [AGG('avg', 'menu_week', 'menu_week.cost_child_day', date='menu_week.week', label='Cost per child-day')]),
        CHART('Meals served against children present per month', 'column', 'month', [AGG('sum', 'claim', 'claim.served', date='claim.month', label='Meals served'), AGG('sum', 'claim', 'claim.children_present', date='claim.month', label='Children present')]),
        CHART('Claim per month', 'bar', 'month', [AGG('sum', 'claim', 'claim.claim_amount', date='claim.month', label='Claim')]),
        CHART('Records by status', 'bar', 'health.status', [AGG('count', 'health', label='Records')]),
        CHART('Records by type', 'bar', 'health.record', [AGG('count', 'health', label='Records')]),
        CHART('Records due by month', 'bar', 'month', [AGG('count', 'health', date='health.due_date', where=[('status', '=', DUE)], label='Records due')]),
        CHART('Records not on file by room', 'bar', 'health.room', [AGG('count', 'health', where=[('status', '<>', ONF)], label='Due or missing')]),
        CHART('Incidents per month', 'bar', 'month', [AGG('count', 'incidents', date='incidents.date', label='Incidents')]),
        CHART('Incidents by type', 'bar', 'incidents.type', [AGG('count', 'incidents', label='Incidents')]),
        CHART('Incidents by room', 'bar', 'incidents.room', [AGG('count', 'incidents', label='Incidents')]),
        CHART('Incidents by hour of day', 'bar', 'inc_hour.hour', [AGG('sum', 'inc_hour', 'inc_hour.incidents', label='Incidents')]),
        CHART('Incidents by follow-up status', 'bar', 'incidents.follow_up_done', [AGG('count', 'incidents', label='Incidents')]),
        CHART('Drills per month', 'bar', 'month', [AGG('count', 'drills', date='drills.date', label='Drills')]),
        CHART('Drills by kind', 'bar', 'drills.kind', [AGG('count', 'drills', label='Drills')]),
        CHART('Drill minutes by kind', 'bar', 'drills.kind', [AGG('avg', 'drills', 'drills.minutes', label='Average minutes')]),
        CHART('Checks per month', 'bar', 'month', [AGG('count', 'checks', date='checks.date', label='Checks')]),
        CHART('Check completion by room', 'bar', 'check_week.room', [AGG('avg', 'check_week', 'check_week.completion', label='Completion share')]),
        CHART('Checks by kind', 'bar', 'checks.kind', [AGG('count', 'checks', label='Checks')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6
signature = [
    {"name": "Meal and menu planner with cost", "why": "pick a menu day and the children expected: meals to prepare from the share who take each meal, cost per child-day and a verdict against your own 12 weeks", "where": "Meal and Menu Planner"},
    {"name": "Meal-program claim sheet", "why": "meals served and eligible by type and month at your own rates, a check that served never exceeds present and the days to fix named", "where": "Meal-Program Claim Sheet"},
    {"name": "Allergy and permission status board", "why": "records on file, due and missing by room and type, status and dates only, with today's list for the cook and who needs an update", "where": "Status Board"},
    {"name": "Incident pattern finder", "why": "incidents counted by hour and room to find the hour that repeats, with type counts and a watch verdict, no medical wording", "where": "Incident Pattern Finder"},
    {"name": "Emergency drill planner", "why": "months between drills by kind from your own plan, the date each is due, what is overdue and the minutes a year it takes", "where": "Emergency Drill Planner"},
    {"name": "Cleaning and safety completion tracker", "why": "checks done and missed by room and week against your target, with the room that needs a talk named", "where": "Cleaning and Safety Tracker"},
    {"name": "Missing records chase list", "why": "every record that is due or missing ranked by days past due, with the family phone and a call, remind or escalate step", "where": "Missing Records Chaser"},
    {"name": "Incident follow-up chaser", "why": "incidents where the family was not told or the follow-up is open, ranked by age so you close the oldest first", "where": "Incident Follow-up Chaser"},
    {"name": "Food cost per child-day against your own year", "why": "food purchases divided by child-days present, set against your own last 12 months, with the gap between bought and served", "where": "Food Cost per Child-Day"},
    {"name": "Supplier price rise test", "why": "a food price rise turned into extra cost a week, the fee rise per child to cover it and an absorb, renegotiate or raise verdict", "where": "Supplier Price Rise Test"}]
competitors = [
    {"what": "free meal count sheets", "lacks": "record the counts but never check meals served against children present, price the meals or total the claim"},
    {"what": "paper health and permission binders", "lacks": "hold the forms but cannot show which records are due or missing by room, the days past due or a list for the cook"},
    {"what": "subscription childcare management software", "lacks": "charge every month or per child and keep food cost, drills and checks in separate paid modules you cannot adapt"},
    {"what": "generic incident logs", "lacks": "list the events but never find the hour or room that repeats, rank open follow-ups or compare a room with its own usual rate"},
    {"what": "single-sheet safety checklists", "lacks": "tick the box but never show completion by room and week, the next drill due or the checks missed over time"}]
guide = [
    'Open Start and type your center name, your own claim rates, the months between drills and the days between checks in the yellow cells. They are your own plan, check your local rules for what you must hold.',
    'Check Rooms and Children. They hold the rooms and the children the other sheets look up; keep statuses and dates only, never health detail.',
    'Fill the Menu with your menu cycle: one row per weekday and meal with the dish, the cost per child and the portions a kilogram.',
    'Write the meal counts on Meals: children present, meals served and eligible meals by day, meal and room. Any meal served to more children than were present is flagged.',
    'Read Menu Cost by Week and Food Purchases to see the food cost per child-day against your own average, and Meal Claim by Month before you send a claim.',
    'Keep Health Records up to date: status (on file, due, missing), due date and last checked, one row per child and record. Status Board by Room, the Cook\'s Daily List and Missing Records Follow-up fill in.',
    'Log every incident on Incidents: date, time, child, room, type, whether the family was told and whether the follow-up is done. Incidents by Hour and by Room and Month show the patterns.',
    'Write each drill on Drills and read Drill Schedule by Month for what is due, done and overdue.',
    'Log room checks on Checks. Check Completion by Week and Cleaning and Safety Schedule show completion by room and what is due next.',
    f'Use the {len(tools)} calculators for the menu, the claim, the status board, incident patterns, drills, checks, shopping, food cost and price rises.',
    f'Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Meals, Health and Safety Dashboard and Charts every week: meals, food cost, records, incidents, drills and checks.']
listing = {"title": "Childcare Center Meals, Health and Safety Excel Template: Meal Claim, Menu Cost, Records Status, Incident Log, Drills, Checks",
    "headline": "Keep meals, records, incidents, drills and checks under control",
    "tags": ["childcare center", "daycare template", "home daycare", "meal claim sheet", "menu cost planner", "allergy status", "incident log", "drill planner", "cleaning checklist", "daycare excel", "safety checks", "food cost tracker", "daycare owner"],
    "description": ("Run the kitchen and the safety paperwork of a home daycare or childcare center in one Excel workbook. Built for an owner-director with 1 to 5 rooms. "
        "Meals go on one sheet by day, meal and room, and any meal served to more children than were present is flagged before you send a meal-program claim, a claim for meals served made to a food program. "
        "The menu cycle gives the cost per child, the kilograms for your order and the dearest dishes; Menu Cost by Week and Food Purchases show the food cost per child-day against your own last 12 months.\n\n"
        "Health Records keep the status of each record (on file, due, missing) and its due date, never health detail. The Status Board by Room, the Cook's Daily List and Missing Records Follow-up show who needs an update and who to call first. "
        "Incidents record date, room, type, whether the family was told and whether the follow-up is done; Incidents by Hour and by Room and Month find the hour that repeats and compare a room with its own usual rate. "
        "Drills, the monthly drill schedule, Checks, completion by week and the cleaning and safety schedule help you keep track of what is due and what was missed.\n\n"
        f"{len(tools)} calculators cover the menu and cost, the claim, the status board, incident patterns, drills, completion, shopping, food cost per child-day, over-orders, price rises and the diet list. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to families, the cook, the supplier, teachers and the cleaner. Children's data is names, rooms, dates and status only.\n\n"
        "This is part six of the Home Daycare and Childcare Center suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. It helps you keep track of meals, records and safety paperwork; it does not promise results or replace your local rules."),
    "features": ["Meal counts with an over-count check against children present", "Meal-program claim sheet by month and meal at your own rates", "Menu cycle with cost per child, kilograms and a dearest-dish ranking", "Food cost per child-day against your own last 12 months",
                 "Record status board by room, status and dates only", "Missing records chase list with call, remind or escalate", "Incident log with pattern finder by hour, room and type", f"{len(tools)} calculators for meals, records, incidents, drills and checks",
                 f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(dashboard['kpis'])} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p6', slug='childcare-center-health-safety', profession='Home Daycare and Childcare Center', name='Meals, Health and Safety Records',
         tagline='Keep meals, records, incidents, drills and checks under control', price_usd=29,
         colors={"primary": "#33658A", "accent": "#F6AE2D"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 6, "of": 8, "focus": "Meals, health and safety records"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cc6.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(dashboard['kpis']), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
