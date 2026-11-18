"""Home Management suite part 8: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho8_lists import *
import ho8_data as D


def R(t, c): return '{range:%s.%s}' % (t, c)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)


YES = '{list:yesno.yes}'; NO = '{list:yesno.no}'
S_NS, S_IP, S_BL, S_DONE = (tok('tstatus', s) for s in TASK_STATUS)
DONATE = tok('decision', 'Donate'); SELL = tok('decision', 'Sell'); BIN = tok('decision', 'Bin')
W_OK, W_SOON, W_OVER, W_DONE = lbl('OK'), lbl('Due soon'), lbl('Overdue'), lbl('Done')
W_ON, W_RISK, W_LATE = lbl('On track'), lbl('At risk'), lbl('Late')
W_CAN, W_WAIT, W_BLK = lbl('Can start'), lbl('Waiting for the earlier task'), lbl('Blocked')
W_PACKED, W_TOPACK = lbl('Packed'), lbl('To pack')
W_IMP, W_WORSE, W_SAME, W_NOLAST = lbl('Improved'), lbl('Worse'), lbl('Same'), lbl('No last year')


def PT(c): return R('project_tasks', c)
def PP(c): return R('project_plan', c)
def PR(c): return R('projects', c)
def GS(c): return R('guests', c)
def HT(c): return R('hosting_timeline', c)
def MB(c): return R('move_boxes', c)
def AD(c): return R('address_list', c)
def MC(c): return R('move_countdown', c)
def DL(c): return R('declutter', c)
def DA(c): return R('declutter_areas', c)
def DN(c): return R('donations', c)
def YV(c): return R('year_review', c)
def MS(c): return R('menu_shop', c)
def MN(c): return R('menu', c)
def RIR(c): return R('recipe_ingredients', c)
def TD(c): return R('task_deps', c)
def PS(c): return R('project_status', c)
def CL(c): return R('cost_lines', c)

def TLR(role, col): return 'IFERROR(INDEX({range:team.%s},MATCH({list:role.%s},{range:team.role},0))&"","")' % (col, key('role', role))
def TLC(n, col): return 'IFERROR(INDEX({range:team.%s},MATCH({set:child%d_id},{range:team.member_id},0))&"","")' % (col, n)
def NAME(role, k, label=None): return CA(k, label or (role + ' name'), 'text', TLR(role, 'short'), 14)
def PHONE(role, k, label=None): return CA(k, label or (role + ' phone'), 'text', TLR(role, 'phone'), 18)
def CNAME(n, k): return CA(k, 'Child %d name' % n, 'text', TLC(n, 'short'), 14)
def CPHONE(n, k): return CA(k, 'Child %d phone' % n, 'text', TLC(n, 'phone'), 18)
def HOUSE(): return CA('household', 'Household', 'text', '{set:household}', 24)
def A12(): return [NAME('Adult 1', 'a1_name'), PHONE('Adult 1', 'a1_phone'), NAME('Adult 2', 'a2_name'), PHONE('Adult 2', 'a2_phone')]
def PAIR(role, p): return [NAME(role, p + '_name'), PHONE(role, p + '_phone')]

YEAR_S = lambda c, y='{set:review_year}': '%s,">="&DATE(%s,1,1),%s,"<="&DATE(%s,12,31)' % (c, y, c, y)

settings = [
    S('household', 'Household name', 'text', HOUSEHOLD), S('adult1', 'Adult 1 shown as', 'text', 'Adult 1'), S('adult2', 'Adult 2 shown as', 'text', 'Adult 2'),
    S('child1_id', 'Team member ID of child 1', 'text', 'HO-03'), S('child2_id', 'Team member ID of child 2', 'text', 'HO-04'),
    S('soon_days', 'Due soon: days before the due date (typed, edit it)', 'int', SOON_DAYS), S('cost_margin', 'At risk when finished work is this share over estimate', 'pct', 0.1),
    S('dinner_date', 'Date of the holiday dinner', 'date', iso(D.DINNER)), S('dinner_hour', 'Dinner is served at this hour, 24-hour clock', 'int', 18),
    S('guests_at_table', 'Guests planned at the table', 'int', 12), S('hosts_at_table', 'Household members at the table', 'int', 4),
    S('rsvp_days', 'Ask for replies this many days before the dinner', 'int', 21), S('hosting_shift', 'Days the dinner may move, for the moved-date text', 'int', 7),
    S('move_date', 'Planned move day (a sample plan, type your own)', 'date', iso(D.MOVE)), S('key_date', 'Key date of the new home', 'date', iso(D.MOVE - D._dt.timedelta(days=10))),
    S('cleanup_days', 'Days to clear and clean the old home after the move', 'int', 2), S('move_shift', 'Days the move date may move (what-if)', 'int', 14),
    S('review_year', 'Year in review: the year', 'int', Y), S('agreed_split_a2', 'Adult 2 agreed share of adult task and chore minutes', 'pct', AGREED_SPLIT_A2),
    S('same_band', 'Year in review: a change within this share is the same', 'pct', 0.02)]
assert 3 <= len(settings) <= 20

tables = []
# 1 team ----------------------------------------------------------------------
tables.append(T('team', 'Team', 'Household members and outside contacts',
    'One row per household member and outside contact: role, phone and e-mail; the texts in this workbook use these numbers. Renters read a trade as the landlord.', [
    C('member_id', 'Member ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 16), C('group', 'Group', 'text', 10), C('phone', 'Phone', 'text', 18),
    C('email', 'E-mail', 'text', 26), C('note', 'Note', 'text', 30), C('start', 'Since', 'date', 11), C('short', 'Short name', 'text', 12), HOUSE()], D.team_d(), 50))
# 2 projects ------------------------------------------------------------------
tables.append(T('projects', 'Projects', 'The projects of the home',
    'One row per project: a renovation, a garden bed, hosting a dinner or a declutter. Phases, tasks and cost lines are on the next sheets; the health of each project is on Project status board.', [
    C('project_id', 'Project ID', 'text', 9, required=True), C('project', 'Project', 'text', 30), LST('kind', 'Kind', 'pkind', 12)], D.projects_d(), 50))
# 3 project plan --------------------------------------------------------------
tables.append(T('project_plan', 'Project plan', 'Phases of every project with dates, owner and estimate',
    'One row per phase of a project: start, end, owner, the estimate (a cost line) and the stage; add the trade or helper and the phone for the phase if you want to send a text.', [
    REF('project_id', 'Project ID', 'projects.project_id', 9), C('phase', 'Phase', 'text', 24, required=True), C('start', 'Start', 'date', 11), C('end', 'End', 'date', 11), LST('owner', 'Owner', 'powner', 10),
    C('estimate', 'Estimate', 'money', 11), LST('stage', 'Stage', 'pstage', 12), C('note', 'Note', 'text', 30), C('helper', 'Trade or helper', 'text', 16), C('helper_phone', 'Helper phone', 'text', 18),
    CA('days_to_end', 'Days to the end', 'int', '{col:end}-{today}', 9), HOUSE()], D.plan_d(), 60, [A('stage', '= ' + tok('pstage', 'Waiting'), 'warn'), A('stage', '= ' + tok('pstage', 'Done'), 'good')]))
# 4 project tasks -------------------------------------------------------------
tables.append(T('project_tasks', 'Project tasks', 'Every project task with owner, dates, status and cost lines',
    'One row per task: owner, start, due, status, the task it waits for, effort minutes and the estimate and actual cost line; days late, the open dependency and days until due fill in.', [
    C('task_id', 'Task ID', 'text', 9, required=True), REF('project_id', 'Project ID', 'projects.project_id', 9), REF('phase', 'Phase', 'project_plan.phase', 20), C('task', 'Task', 'text', 30),
    LST('owner', 'Owner', 'powner', 10), C('start', 'Start', 'date', 11), C('due', 'Due', 'date', 11), LST('status', 'Status', 'tstatus', 12), C('depends_on', 'Depends on', 'text', 9),
    C('minutes', 'Effort minutes', 'int', 9), C('est_cost', 'Estimated cost', 'money', 11), C('actual_cost', 'Actual cost', 'money', 11), C('done_on', 'Done on', 'date', 11),
    CA('project', 'Project', 'text', LKT('projects.project', 'projects.project_id', 'project_id'), 24),
    CA('days_late', 'Days late', 'int', 'IF({col:due}="",0,IF(AND({col:status}<>%s,{col:due}<{today}),{today}-{col:due},0))' % S_DONE, 8),
    CA('open', 'Open, 1 or 0', 'int', 'IF({col:status}=%s,0,1)' % S_DONE, 8),
    CA('blocked_by', 'Waiting for task', 'text', 'IF({col:depends_on}="","",IF(COUNTIFS(%s,{col:depends_on},%s,"<>"&%s)>0,{col:depends_on},""))' % (PT('task_id'), PT('status'), S_DONE), 10),
    CA('due_in', 'Days until due', 'int', 'IF({col:status}=%s,"",{col:due}-{today})' % S_DONE, 9),
    CA('next14', 'Due in the next 14 days, 1 or 0', 'int', 'IF(AND({col:status}<>%s,{col:due}>={today},{col:due}<={today}+13),1,0)' % S_DONE, 9),
    CA('pidx', 'Project number', 'int', 'VALUE(RIGHT({col:project_id},2))', 8), CA('new_due', 'Suggested new due date', 'date', '{today}+7', 11)]
    + A12() + PAIR('Plumber', 'pl') + PAIR('Electrician', 'el') + [HOUSE()],
    D.tasks_d(), 120, [A('status', '= ' + S_BL, 'bad'), A('days_late', '> 0', 'bad'), A('status', '= ' + S_DONE, 'good'), A('status', '= ' + S_IP, 'warn')]))
# 5 guests --------------------------------------------------------------------
tables.append(T('guests', 'Guests', 'Guest list with RSVP, party size and preference label',
    'One row per guest or party: the reply, the party size, a short preference or avoid label (never health advice), the table and the phone; the reply-by date and moved date fill in.', [
    C('guest_id', 'Guest ID', 'text', 9, required=True), C('guest', 'Guest', 'text', 18), LST('rsvp', 'RSVP', 'rsvp', 10), C('party_size', 'Party size', 'int', 8), LST('pref_label', 'Preference label', 'gprefs', 24),
    REF('project_id', 'Project ID', 'projects.project_id', 9), C('invited_on', 'Invited on', 'date', 11), C('phone', 'Phone', 'text', 18), C('table_no', 'Table number', 'int', 8),
    CA('dinner', 'Dinner date', 'date', '{set:dinner_date}', 11), CA('dinner_time', 'Dinner time', 'time', '{set:dinner_hour}/24', 9), CA('rsvp_by', 'Reply by', 'date', '{set:dinner_date}-{set:rsvp_days}', 11),
    CA('new_date', 'Moved to', 'date', '{set:dinner_date}+{set:hosting_shift}', 11), CA('people_invited', 'People invited', 'int', 'SUM(%s)' % GS('party_size'), 9),
    CA('people_yes', 'People confirmed', 'int', 'SUMIFS(%s,%s,%s)' % (GS('party_size'), GS('rsvp'), tok('rsvp', 'Yes')), 9)] + [NAME('Adult 1', 'a1_name'), PHONE('Adult 1', 'a1_phone'), HOUSE()],
    D.guests_d(), 50, [A('rsvp', '= ' + tok('rsvp', 'Yes'), 'good'), A('rsvp', '= ' + tok('rsvp', 'Maybe'), 'warn'), A('rsvp', '= ' + tok('rsvp', 'No reply'), 'bad')]))
# 6 recipes -------------------------------------------------------------------
tables.append(T('recipes', 'Recipes', 'Household recipes used for the dinner menu',
    'One row per household recipe: prep minutes, servings and a plain preference label (never health advice); the ingredient count and whether the dinner menu uses it fill in.', [
    C('recipe_id', 'Recipe ID', 'text', 9, required=True), C('recipe', 'Recipe', 'text', 28), LST('category', 'Category', 'rcat', 16), C('prep_min', 'Prep minutes', 'int', 9), C('servings', 'Servings', 'int', 9),
    LST('pref_label', 'Preference label', 'pref', 16),
    CA('ingredient_count', 'Ingredient lines', 'int', 'COUNTIFS(%s,{col:recipe_id})' % RIR('recipe_id'), 9),
    CA('in_menu', 'On the dinner menu, 1 or 0', 'int', 'IF(COUNTIFS(%s,{col:recipe_id})>0,1,0)' % MN('recipe_id'), 9),
    CA('menu_portions', 'Menu portions', 'int', 'SUMIFS(%s,%s,{col:recipe_id})' % (MN('portions'), MN('recipe_id')), 9)], D.recipes_d(), 80, [A('in_menu', '= 1', 'good')]))
# 7 recipe ingredients --------------------------------------------------------
tables.append(T('recipe_ingredients', 'Recipe ingredients', 'Ingredient lines with the quantity the dinner menu needs',
    'One row per ingredient of a recipe, quantity for the recipe servings; the quantity the dinner menu needs, scaled to the menu portions, fills in.', [
    C('ingredient_id', 'Ingredient ID', 'text', 11, required=True), REF('recipe_id', 'Recipe ID', 'recipes.recipe_id', 9),
    CA('recipe', 'Recipe', 'text', LKT('recipes.recipe', 'recipes.recipe_id', 'recipe_id'), 26), C('item', 'Item', 'text', 18), C('qty', 'Quantity', 'num', 9), LST('unit', 'Unit', 'unit', 8),
    C('section', 'Section', 'text', 16), CA('rec_servings', 'Recipe servings', 'int', LKN('recipes.servings', 'recipes.recipe_id', 'recipe_id'), 9),
    CA('menu_portions', 'Menu portions', 'int', 'SUMIFS(%s,%s,{col:recipe_id})' % (MN('portions'), MN('recipe_id')), 9),
    CA('menu_qty', 'Needed for the dinner menu', 'num', 'IF(OR({col:menu_portions}=0,{col:rec_servings}=0),0,ROUND({col:qty}*{col:menu_portions}/{col:rec_servings},3))', 11)], D.ri_d(), 400))
# 8 menu ----------------------------------------------------------------------
tables.append(T('menu', 'Menu for the dinner', 'The menu: course, recipe, portions, cook and the day to cook',
    'One row per dish of the holiday dinner: the recipe, the portions planned, who cooks and the day to cook; the recipe name, servings, prep minutes and the scale factor fill in.', [
    REF('recipe_id', 'Recipe ID', 'recipes.recipe_id', 9, required=True), C('course', 'Course', 'text', 10), C('portions', 'Portions', 'int', 9), LST('cook', 'Cook', 'powner', 10), C('day_to_cook', 'Day to cook', 'date', 11),
    CA('recipe', 'Recipe', 'text', LKT('recipes.recipe', 'recipes.recipe_id', 'recipe_id'), 26), CA('servings', 'Recipe servings', 'int', LKN('recipes.servings', 'recipes.recipe_id', 'recipe_id'), 9),
    CA('prep_min', 'Prep minutes', 'int', LKN('recipes.prep_min', 'recipes.recipe_id', 'recipe_id'), 9), CA('scale', 'Scale factor', 'num', 'IF({col:servings}=0,"",ROUND({col:portions}/{col:servings},2))', 9),
    CA('days_to_cook', 'Days until cooking', 'int', '{col:day_to_cook}-{today}', 9)], D.menu_d(), 50))
# 9 menu shopping -------------------------------------------------------------
tables.append(T('menu_shop', 'Menu shopping', 'Shopping quantities for the dinner menu, rounded to packs',
    'One row per item the menu needs: section, unit, the pack size you type and bought; the quantity for the menu portions, the packs to buy and the share of a pack fill in.', [
    C('item', 'Item', 'text', 20, required=True), LST('section', 'Section', 'msect', 18), LST('unit', 'Unit', 'unit', 8), C('pack_size', 'Pack size', 'num', 9), C('bought', 'Bought', 'bool', 8),
    CA('qty', 'Quantity for the menu', 'num', 'ROUND(SUMIFS(%s,%s,{col:item}),2)' % (RIR('menu_qty'), RIR('item')), 11),
    CA('lines', 'Recipes using it', 'int', 'COUNTIFS(%s,{col:item},%s,">0")' % (RIR('item'), RIR('menu_portions')), 9),
    CA('exact', 'Packs, exact', 'num', 'IF({col:pack_size}>0,ROUND({col:qty}/{col:pack_size},6),"")', 9),
    CA('packs', 'Packs to buy', 'int', 'IF(AND({col:qty}>0,{col:pack_size}>0),ROUNDUP({col:exact},0),0)', 9),
    CA('spare', 'Spare in the last pack', 'num', 'IF({col:packs}>0,ROUND({col:packs}*{col:pack_size}-{col:qty},2),"")', 10)], D.menu_shop_d(), 80, [A('bought', '= ' + YES, 'good')]))
# 10 hosting timeline ---------------------------------------------------------
tables.append(T('hosting_timeline', 'Hosting timeline', 'Hosting tasks counted back from the dinner date',
    'One row per hosting task: days before the dinner and the owner (type -1 for a day after); the due date, status from Project tasks, days left and the dinner facts fill in.', [
    C('task', 'Task', 'text', 34, required=True), C('days_before', 'Days before the dinner', 'int', 10), LST('owner', 'Owner', 'hown', 10),
    CA('due', 'Due date', 'date', '{set:dinner_date}-{col:days_before}', 11),
    CA('task_status', 'Task status', 'text', 'IFERROR(INDEX(%s,MATCH({col:task},%s,0))&"","")' % (PT('status'), PT('task')), 12),
    CA('done_flag', 'Done, 1 or 0', 'int', 'IF({col:task_status}=%s,1,0)' % S_DONE, 8),
    CA('open_due', 'Due date of an open task', 'date', 'IF({col:done_flag}=1,"",{col:due})', 11),
    CA('status', 'Status', 'text', 'IF({col:done_flag}=1,%s,IF({col:due}<{today},%s,IF({col:due}-{today}<={set:soon_days},%s,%s)))' % (W_DONE, W_OVER, W_SOON, W_OK), 10),
    CA('days_left', 'Days left', 'int', 'IF({col:done_flag}=1,"",{col:due}-{today})', 8),
    CA('dinner', 'Dinner date', 'date', '{set:dinner_date}', 11), CA('days_to_dinner', 'Days to the dinner', 'int', '{set:dinner_date}-{today}', 9),
    CA('guests', 'Guests at the table', 'int', '{set:guests_at_table}', 9), CA('tasks_open', 'Hosting tasks open', 'int', 'COUNTIFS(%s,0,%s,"<>")' % (HT('done_flag'), HT('task')), 9),
    CA('items_not_bought', 'Menu items not bought', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (MS('bought'), NO, MS('item')), 9),
    CA('dinner_time', 'Dinner time', 'time', '{set:dinner_hour}/24', 9), CA('kids_eat', 'Children eat at', 'time', '({set:dinner_hour}-1)/24', 9),
    CA('come_from', 'Helpers come from', 'time', '({set:dinner_hour}-2)/24', 9), CA('collect_at', 'Collect the dog at', 'time', '({set:dinner_hour}-3)/24', 9)]
    + A12() + [CNAME(1, 'c1_name'), CPHONE(1, 'c1_phone'), CNAME(2, 'c2_name'), CPHONE(2, 'c2_phone')] + PAIR('Grandparent', 'gp') + PAIR('Babysitter', 'bs') + PAIR('Carpool family', 'cp')
    + PAIR('Neighbour', 'nb') + PAIR('Dog walker', 'dw') + [HOUSE()],
    D.timeline_d(), 50, [A('status', '= ' + W_OVER, 'bad'), A('status', '= ' + W_SOON, 'warn'), A('status', '= ' + W_DONE, 'good')]))
# 11 project status board -----------------------------------------------------
tables.append(T('project_status', 'Project status board', 'Every phase: share done, days late, cost against estimate',
    'One row per phase: type the phase once; tasks, share done, days late, the cost of finished work against its estimate and a verdict (On track, At risk, Late or Done) fill in.', [
    REF('phase', 'Phase', 'project_plan.phase', 22, required=True),
    CA('project', 'Project', 'text', 'IFERROR(INDEX(%s,MATCH(INDEX(%s,MATCH({col:phase},%s,0)),%s,0)),"")' % (PR('project'), PP('project_id'), PP('phase'), PR('project_id')), 24),
    CA('tasks', 'Tasks', 'int', 'COUNTIFS(%s,{col:phase})' % PT('phase'), 8), CA('done', 'Tasks done', 'int', 'COUNTIFS(%s,{col:phase},%s,%s)' % (PT('phase'), PT('status'), S_DONE), 8),
    CA('share_done', 'Share done', 'pct', 'IF({col:tasks}=0,"",ROUND({col:done}/{col:tasks},4))', 9),
    CA('days_late', 'Days late, worst task', 'int', 'SUMPRODUCT(MAX((%s={col:phase})*(%s<>%s)*(%s<{today})*({today}-%s)))' % (PT('phase'), PT('status'), S_DONE, PT('due'), PT('due')), 10),
    CA('blocked', 'Blocked tasks', 'int', 'COUNTIFS(%s,{col:phase},%s,%s)' % (PT('phase'), PT('status'), S_BL), 8),
    CA('est', 'Estimate', 'money', 'SUMIFS(%s,%s,{col:phase})' % (PT('est_cost'), PT('phase')), 11), CA('actual', 'Actual to date', 'money', 'SUMIFS(%s,%s,{col:phase})' % (PT('actual_cost'), PT('phase')), 11),
    CA('paid', 'Paid, finished tasks', 'money', 'SUMIFS(%s,%s,{col:phase},%s,%s)' % (PT('actual_cost'), PT('phase'), PT('status'), S_DONE), 11),
    CA('est_done', 'Estimate, finished tasks', 'money', 'SUMIFS(%s,%s,{col:phase},%s,%s)' % (PT('est_cost'), PT('phase'), PT('status'), S_DONE), 11),
    CA('cost_diff', 'Finished work against estimate', 'money', 'ROUND({col:paid}-{col:est_done},2)', 12),
    CA('cost_over', 'Share over the estimate', 'pct', 'IF({col:est_done}=0,0,ROUND(({col:paid}-{col:est_done})/{col:est_done},4))', 9),
    CA('verdict', 'Verdict', 'text', 'IF({col:tasks}=0,"",IF({col:done}={col:tasks},%s,IF({col:days_late}>0,%s,IF(OR({col:blocked}>0,{col:cost_over}>{set:cost_margin}),%s,%s))))' % (W_DONE, W_LATE, W_RISK, W_ON), 10)],
    D.status_d(), 50, [A('verdict', '= ' + W_LATE, 'bad'), A('verdict', '= ' + W_RISK, 'warn'), A('verdict', '= ' + W_ON, 'good'), A('verdict', '= ' + W_DONE, 'good')]))


def DEPL(prev, nxt): return 'IF({col:%s}="","",IFERROR(INDEX(%s,MATCH({col:%s},%s,0))&"",""))' % (prev, PT('depends_on'), prev, PT('task_id'))
def DLATE(d): return 'IF({col:%s}="",0,IFERROR(INDEX(%s,MATCH({col:%s},%s,0)),0))' % (d, PT('days_late'), d, PT('task_id'))
def DOPEN(d): return 'IF({col:%s}="",0,IFERROR(INDEX(%s,MATCH({col:%s},%s,0)),0))' % (d, PT('open'), d, PT('task_id'))
# 12 task dependencies --------------------------------------------------------
tables.append(T('task_deps', 'Task dependencies', 'Which task waits for which, and the chain of open tasks',
    'One row per task (type the task ID once): the task it waits for, whether that is done, can it start, days its wait has run, the chain of open tasks (up to 5) and the forecast finish.', [
    REF('task_id', 'Task ID', 'project_tasks.task_id', 9, required=True), CA('task', 'Task', 'text', LKT('project_tasks.task', 'project_tasks.task_id', 'task_id'), 30),
    CA('project', 'Project', 'text', LKT('project_tasks.project', 'project_tasks.task_id', 'task_id'), 24), CA('pidx', 'Project number', 'int', LKN('project_tasks.pidx', 'project_tasks.task_id', 'task_id'), 8),
    CA('status', 'Status', 'text', LKT('project_tasks.status', 'project_tasks.task_id', 'task_id'), 12), CA('due', 'Due', 'date', LKN('project_tasks.due', 'project_tasks.task_id', 'task_id'), 11),
    CA('dep1', 'Depends on', 'text', LKT('project_tasks.depends_on', 'project_tasks.task_id', 'task_id'), 9),
    CA('dep_status', 'Dependency status', 'text', 'IF({col:dep1}="","",IFERROR(INDEX(%s,MATCH({col:dep1},%s,0))&"",""))' % (PT('status'), PT('task_id')), 12),
    CA('dep_due', 'Dependency due', 'date', 'IF({col:dep1}="","",IFERROR(INDEX(%s,MATCH({col:dep1},%s,0)),""))' % (PT('due'), PT('task_id')), 11),
    CA('dep_done', 'Dependency done, 1 or 0', 'int', 'IF({col:dep1}="",1,IF({col:dep_status}=%s,1,0))' % S_DONE, 9),
    CA('can_start', 'Can start', 'text', 'IF({col:status}=%s,%s,IF({col:dep_done}=0,%s,IF({col:status}=%s,%s,%s)))' % (S_DONE, W_DONE, W_WAIT, S_BL, W_BLK, W_CAN), 26),
    CA('blocked_days', 'Blocked days', 'int', 'IF({col:dep_done}=1,0,MAX(0,{today}-{col:dep_due}))', 9),
    CA('dep2', 'Chain level 2', 'text', DEPL('dep1', 'dep2'), 9), CA('dep3', 'Chain level 3', 'text', DEPL('dep2', 'dep3'), 9), CA('dep4', 'Chain level 4', 'text', DEPL('dep3', 'dep4'), 9),
    CA('late_self', 'Days late', 'int', LKN('project_tasks.days_late', 'project_tasks.task_id', 'task_id'), 8),
    CA('slip', 'Slip, worst late day in the chain', 'int', 'MAX({col:late_self},%s)' % ','.join(DLATE(d) for d in ('dep1', 'dep2', 'dep3', 'dep4')), 10),
    CA('open_chain', 'Open tasks in the chain', 'int', 'IF({col:status}=%s,"",1+%s)' % (S_DONE, '+'.join(DOPEN(d) for d in ('dep1', 'dep2', 'dep3', 'dep4'))), 10),
    CA('forecast', 'Forecast finish', 'date', 'IF({col:status}=%s,"",{col:due}+{col:slip})' % S_DONE, 11),
    CA('fc_key', 'Forecast key', 'int', 'IF({col:forecast}="","",{col:pidx}*100000+{col:forecast})', 10),
    CA('chain_key', 'Chain key', 'int', 'IF({col:open_chain}="","",{col:pidx}*100+{col:open_chain})', 10), CA('slip_key', 'Slip key', 'int', 'IF({col:forecast}="","",{col:pidx}*1000+{col:slip})', 10)],
    D.deps_d(), 120, [A('can_start', '= ' + W_WAIT, 'warn'), A('can_start', '= ' + W_BLK, 'bad'), A('blocked_days', '> 0', 'bad')]))
# 13 cost lines by project ----------------------------------------------------
tables.append(T('cost_lines', 'Cost lines by project', 'Estimate, actual and paid cost lines by project and owner',
    'One row per project and owner (adult 1, adult 2 or a trade): the estimate, the actual to date, the paid cost of finished tasks and the difference fill in from Project tasks.', [
    REF('project', 'Project', 'projects.project', 28, required=True), LST('owner', 'Owner', 'powner', 10),
    CA('estimate', 'Estimate', 'money', 'SUMIFS(%s,%s,{col:project},%s,{col:owner})' % (PT('est_cost'), PT('project'), PT('owner')), 11),
    CA('actual', 'Actual to date', 'money', 'SUMIFS(%s,%s,{col:project},%s,{col:owner})' % (PT('actual_cost'), PT('project'), PT('owner')), 11),
    CA('paid', 'Paid, finished tasks', 'money', 'SUMIFS(%s,%s,{col:project},%s,{col:owner},%s,%s)' % (PT('actual_cost'), PT('project'), PT('owner'), PT('status'), S_DONE), 11),
    CA('est_done', 'Estimate, finished tasks', 'money', 'SUMIFS(%s,%s,{col:project},%s,{col:owner},%s,%s)' % (PT('est_cost'), PT('project'), PT('owner'), PT('status'), S_DONE), 11),
    CA('difference', 'Paid less estimate', 'money', 'ROUND({col:paid}-{col:est_done},2)', 11),
    CA('project_estimate', 'Project estimate', 'money', 'SUMIFS(%s,%s,{col:project})' % (CL('estimate'), CL('project')), 12), CA('project_actual', 'Project actual', 'money', 'SUMIFS(%s,%s,{col:project})' % (CL('actual'), CL('project')), 12)]
    + [NAME('Adult 2', 'a2_name'), PHONE('Adult 2', 'a2_phone'), HOUSE()], D.cost_d(), 50, [A('difference', '> 0', 'warn')]))
# 14 moving boxes by room -----------------------------------------------------
tables.append(T('move_boxes', 'Moving boxes by room', 'Boxes by room: counted, label, packed, move day',
    'One row per box group: the room, the boxes counted, the label on the box, packed yes or no, the day it moves and a note; boxes left, the pack-by day and days left fill in.', [
    C('label', 'Box label', 'text', 10, required=True), LST('room', 'Room', 'room', 14), C('boxes', 'Boxes counted', 'int', 9), C('packed', 'Packed', 'bool', 8), C('notes', 'Notes', 'text', 30), C('moves_on', 'Moves on', 'date', 11),
    CA('left', 'Boxes left', 'int', 'IF({col:packed}=%s,0,{col:boxes})' % YES, 8), CA('pack_by', 'Pack by', 'date', '{col:moves_on}-2', 11), CA('days_left', 'Days to the move', 'int', '{col:moves_on}-{today}', 9),
    CA('status', 'Status', 'text', 'IF({col:packed}=%s,%s,IF({col:moves_on}-{today}<={set:soon_days},%s,%s))' % (YES, W_PACKED, W_SOON, W_TOPACK), 10), CNAME(1, 'c1_name'), CPHONE(1, 'c1_phone'), HOUSE()],
    D.boxes_d(), 50, [A('packed', '= ' + YES, 'good'), A('status', '= ' + W_SOON, 'warn')]))
# 15 change of address --------------------------------------------------------
tables.append(T('address_list', 'Change-of-address list', 'Organisation types to tell about the new address',
    'One row per organisation type: the notice typically needed in days (check each one), done yes or no and the date; the day to tell them by, days left and the status fill in.', [
    LST('orgtype', 'Organisation type', 'orgtype', 30, required=True), C('notice_days', 'Notice needed, days', 'int', 10), C('done', 'Done', 'bool', 8), C('done_on', 'Date done', 'date', 11),
    CA('needed_by', 'Tell them by', 'date', '{set:move_date}-{col:notice_days}', 11), CA('open_by', 'Tell them by, open items', 'date', 'IF({col:done}=%s,"",{set:move_date}-{col:notice_days})' % YES, 11), CA('days_left', 'Days left', 'int', 'IF({col:done}=%s,"",{col:needed_by}-{today})' % YES, 8),
    CA('status', 'Status', 'text', 'IF({col:done}=%s,%s,IF({col:needed_by}<{today},%s,IF({col:needed_by}-{today}<={set:soon_days},%s,%s)))' % (YES, W_DONE, W_OVER, W_SOON, W_OK), 10), HOUSE()],
    D.address_d(), 50, [A('status', '= ' + W_OVER, 'bad'), A('status', '= ' + W_SOON, 'warn'), A('status', '= ' + W_DONE, 'good')]))
# 16 move countdown -----------------------------------------------------------
tables.append(T('move_countdown', 'Move countdown', 'Move steps from 8 weeks to 1 day before',
    'One row per step: days before the move day and done yes or no; the due date, the date if the move shifts, the status and the days left fill in from Settings.', [
    C('step', 'Step', 'text', 34, required=True), C('days_before', 'Days before the move', 'int', 10), C('done', 'Done', 'bool', 8),
    CA('weeks_before', 'Weeks before', 'num', 'ROUND({col:days_before}/7,1)', 8), CA('due', 'Due date', 'date', '{set:move_date}-{col:days_before}', 11),
    CA('shifted', 'Shifted date', 'date', '{col:due}+{set:move_shift}', 11),
    CA('status', 'Status', 'text', 'IF({col:done}=%s,%s,IF({col:due}<{today},%s,IF({col:due}-{today}<={set:soon_days},%s,%s)))' % (YES, W_DONE, W_OVER, W_SOON, W_OK), 10),
    CA('days_left', 'Days left', 'int', 'IF({col:done}=%s,"",{col:due}-{today})' % YES, 8),
    CA('move_date', 'Move day', 'date', '{set:move_date}', 11), CA('end_date', 'Old home released', 'date', '{set:move_date}+{set:cleanup_days}', 11),
    CA('tasks_moved', 'Tasks that move with the date', 'int', 'COUNTIFS(%s,%s,%s,"<>")+COUNTIFS(%s,%s,%s,"<>")' % (MC('done'), NO, MC('step'), AD('done'), NO, AD('orgtype')), 10)]
    + [NAME('Adult 2', 'a2_name'), PHONE('Adult 2', 'a2_phone'), CNAME(1, 'c1_name')] + PAIR('School office', 'so') + PAIR('Neighbour', 'nb') + PAIR('Landlord or agent', 'll') + [HOUSE()],
    D.countdown_d(), 50, [A('status', '= ' + W_OVER, 'bad'), A('status', '= ' + W_SOON, 'warn'), A('status', '= ' + W_DONE, 'good')]))
# 17 declutter log ------------------------------------------------------------
tables.append(T('declutter', 'Declutter log', 'Declutter log: keep, donate, sell or bin',
    'One row per batch of items: date, area, item, the decision (keep, donate, sell or bin), the count, the destination and the value of items sold (a cost line); the donation order fills in.', [
    C('declutter_id', 'Declutter ID', 'text', 11, required=True), C('date', 'Date', 'date', 11), LST('area', 'Area', 'room', 14), C('item', 'Item', 'text', 26), LST('decision', 'Decision', 'decision', 9), C('count', 'Count', 'int', 8),
    REF('project_id', 'Project ID', 'projects.project_id', 9), C('destination', 'Destination', 'text', 18), C('value', 'Value', 'money', 10),
    CA('seq', 'Sequence', 'int', 'VALUE(RIGHT({col:declutter_id},3))', 8),
    CA('donate_seq', 'Donation number', 'int', 'IF({col:decision}=%s,COUNTIFS(%s,%s,%s,"<="&{col:seq}),"")' % (DONATE, DL('decision'), DONATE, DL('seq')), 9),
    CA('areas_total', 'Areas', 'int', 'COUNTIFS(%s,"<>")' % DA('area'), 8), CA('areas_open', 'Areas not started', 'int', 'COUNTIFS(%s,0,%s,"<>")' % (DA('decided'), DA('area')), 9),
    CA('next_area', 'Next area', 'text', 'IFERROR(INDEX(%s,MATCH(0,%s,0))&"","")' % (DA('area'), DA('decided')), 14)] + [NAME('Adult 2', 'a2_name'), PHONE('Adult 2', 'a2_phone'), HOUSE()],
    D.declutter_d(), 220, [A('decision', '= ' + DONATE, 'good'), A('decision', '= ' + BIN, 'warn')]))
# 18 declutter progress by area -----------------------------------------------
tables.append(T('declutter_areas', 'Declutter areas', 'Items decided in every area and the share of the count',
    'One row per area (type the 10 areas once): the items decided and the share of all items decided fill in from the Declutter log; an area with 0 items has not started.', [
    LST('area', 'Area', 'room', 16, required=True),
    CA('decided', 'Items decided', 'int', 'SUMIFS(%s,%s,{col:area})' % (DL('count'), DL('area')), 11),
    CA('share', 'Share of the count', 'pct', 'IF(SUM(%s)=0,0,ROUND({col:decided}/SUM(%s),4))' % (DA('decided'), DA('decided')), 11)], D.areas_d(), 50, [A('decided', '= 0', 'warn')]))
# 19 donation log -------------------------------------------------------------
tables.append(T('donations', 'Donation log', 'Every donation from the Declutter log in order',
    'One row per donation (type the numbers 1 to 30 once; add more as you go): the date, area, item, count and destination fill in from rows decided Donate in the Declutter log.', [
    C('no', 'Donation number', 'int', 9, required=True),
    CA('date', 'Date', 'date', 'IFERROR(INDEX(%s,MATCH({col:no},%s,0)),"")' % (DL('date'), DL('donate_seq')), 11),
    CA('area', 'Area', 'text', 'IFERROR(INDEX(%s,MATCH({col:no},%s,0))&"","")' % (DL('area'), DL('donate_seq')), 14),
    CA('item', 'Item', 'text', 'IFERROR(INDEX(%s,MATCH({col:no},%s,0))&"","")' % (DL('item'), DL('donate_seq')), 26),
    CA('count', 'Count', 'int', 'IFERROR(INDEX(%s,MATCH({col:no},%s,0)),"")' % (DL('count'), DL('donate_seq')), 8),
    CA('destination', 'Destination', 'text', 'IFERROR(INDEX(%s,MATCH({col:no},%s,0))&"","")' % (DL('destination'), DL('donate_seq')), 18),
    CA('year', 'Year', 'int', 'IF({col:date}="","",YEAR({col:date}))', 7),
    CA('drop_off', 'First of its day, 1 or 0', 'int', 'IF({col:date}="","",IF(COUNTIFS(%s,{col:date},%s,"<"&{col:no})=0,1,0))' % (DN('date'), DN('no')), 9)]
    + A12() + [CNAME(2, 'c2_name'), CPHONE(2, 'c2_phone')] + PAIR('Carpool family', 'cp') + PAIR('Neighbour', 'nb') + [HOUSE()], D.donations_d(), 60))
# 20 year in review -----------------------------------------------------------
YM = lambda n: tok('ymeasure', n)
HERE = ('IF({col:measure}=%s,SUMPRODUCT((%s<>"")*(COUNTIFS(%s,%s)>0)*(COUNTIFS(%s,%s,%s,"<>"&%s)=0)),'
        'IF({col:measure}=%s,COUNTIFS(%s,%s,%s),IF({col:measure}=%s,COUNTIFS(%s,">0"),IF({col:measure}=%s,SUMIFS(%s,%s,%s,%s),""))))') % (
    YM('Projects finished'), PR('project_id'), PT('project_id'), PR('project_id'), PT('project_id'), PR('project_id'), PT('status'), S_DONE,
    YM('Project tasks done'), PT('status'), S_DONE, YEAR_S(PT('done_on')), YM('Areas decluttered, of 10'), DA('decided'),
    YM('Items donated'), DL('count'), DL('decision'), DONATE, YEAR_S(DL('date')))
tables.append(T('year_review', 'Year in review', 'The year in review: 14 measures against last year',
    'One row per measure: type the number from the other workbooks (or leave it blank for the four calculated here), last year when you have it, and a next-year line; change and verdict fill in.', [
    LST('measure', 'Measure', 'ymeasure', 34, required=True), C('this_typed', 'This year, typed', 'num', 11), C('last_year', 'Last year', 'num', 10), C('higher_better', 'Higher is better', 'bool', 9),
    C('next_year', 'Next-year line', 'text', 40), C('typed_on', 'Numbers typed on', 'date', 11),
    CA('here', 'Calculated here', 'num', HERE, 10), CA('this_year', 'This year', 'num', 'IF({col:this_typed}<>"",{col:this_typed},{col:here})', 10),
    CA('change', 'Change', 'num', 'IF(OR({col:this_year}="",{col:last_year}=""),"",ROUND({col:this_year}-{col:last_year},2))', 9),
    CA('gain', 'Improvement share', 'pct', 'IF(OR({col:this_year}="",{col:last_year}=""),"",IF({col:last_year}=0,"",ROUND(IF({col:higher_better}=%s,1,-1)*({col:this_year}-{col:last_year})/ABS({col:last_year}),4)))' % YES, 10),
    CA('verdict', 'Verdict', 'text', 'IF({col:gain}="",%s,IF({col:gain}>{set:same_band},%s,IF({col:gain}<-{set:same_band},%s,%s)))' % (W_NOLAST, W_IMP, W_WORSE, W_SAME), 12),
    CA('year', 'Year', 'int', '{set:review_year}', 7), CA('has_last', 'Has last year, 1 or 0', 'int', 'IF({col:last_year}="",0,1)', 8), CA('improved_n', 'Measures improved', 'int', 'COUNTIFS(%s,%s)' % (YV('verdict'), W_IMP), 9)] + [NAME('Adult 1', 'a1_name'), PHONE('Adult 1', 'a1_phone'), HOUSE()],
    D.year_d(), 50, [A('verdict', '= ' + W_IMP, 'good'), A('verdict', '= ' + W_WORSE, 'warn')]))
assert len(tables) == 20, len(tables)
