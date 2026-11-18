"""Home Management suite - part 3: Cleaning, Laundry and Chore Rotation."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho3_lists import *
from ho3_tables import settings, tables, R, YES, A1, A2, C1, C2, OVD, DUES, OKS, WS, LOGW, W30, NOTPAU, DAILY, WEEKLY, FORTN, MONTHLY, QUART, TWICE, YEARLY
from ho3_tools import tools
import ho3_data as D

NOTE = "Sample wording: adapt it to your own household."
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
CH = lambda c: R('chores', c)
LG = lambda c: R('chore_log', c)
SG = ['Adult 1', 'Adult 2']
MSD = 'DATE(YEAR({today}),MONTH({today}),1)'

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('chore_card', 'Chore Card', 'One chore with its room, owner and next due date', 'chores.chore_id', F(
        ('Chore', 'chores.chore'), ('Room', 'chores.room'), ('Frequency', 'chores.frequency'), ('Minutes', 'chores.minutes'), ('Default owner', 'chores.owner'), ('Points', 'chores.points'),
        ('Last done', 'chores.last_done'), ('Next due', 'chores.next_due'), ('Days to due', 'chores.days_to_due'), ('Overdue days', 'chores.overdue_days'), ('Status', 'chores.status')) + [
        FF('Chores in the same room', 'COUNTIFS(%s,%s)' % (CH('room'), LK('chores', 'chore_id', 'room')), 'int'),
        FF('Minutes a week of the room', 'ROUND(SUMIFS(%s,%s,%s),0)' % (CH('min_week'), CH('room'), LK('chores', 'chore_id', 'room')), 'int'),
        FF('Times done in the log', 'COUNTIFS(%s,{pick})' % LG('chore_id'), 'int')]),
    FORM('chore_done_sheet', 'Chore Done Sheet', 'One chore done, by whom and how long it took', 'chore_log.log_id', F(
        ('Chore', 'chore_log.chore'), ('Room', 'chore_log.room'), ('Done on', 'chore_log.done'), ('Who', 'chore_log.who'), ('Minutes', 'chore_log.minutes'), ('Points', 'chore_log.points'),
        ('Weekday', 'chore_log.weekday'), ('By the default owner, 1 or 0', 'chore_log.by_owner'), ('Adult 1 late day, 1 or 0', 'chore_log.late_day')) + [
        FF('Chores done by that person, last 30 days', 'COUNTIFS(%s,%s,%s,1)' % (LG('who'), LK('chore_log', 'log_id', 'who'), LG('last30')), 'int'),
        FF('Minutes by that person, last 30 days', 'SUMIFS(%s,%s,%s,%s,1)' % (LG('minutes'), LG('who'), LK('chore_log', 'log_id', 'who'), LG('last30')), 'int'),
        FF('Times this chore was done, in all', 'COUNTIFS(%s,%s)' % (LG('chore_id'), LK('chore_log', 'log_id', 'chore_id')), 'int')]),
    FORM('cleaning_round_sheet', 'Cleaning Round Sheet', 'One chore of the cleaning round, room by room', 'cleaning.chore_id', F(
        ('Chore', 'cleaning.chore'), ('Room', 'cleaning.room'), ('Frequency', 'cleaning.frequency'), ('Last done', 'cleaning.last_done'), ('Next due', 'cleaning.next_due'), ('Overdue days', 'cleaning.overdue_days'),
        ('Status', 'cleaning.status'), ('Minutes', 'cleaning.minutes'), ('Chores in the room', 'cleaning.room_n'), ('Overdue chores in the room', 'cleaning.room_over'), ('Deep clean minutes of the room', 'cleaning.deep_min')) + [
        FF('Overdue minutes in the room', 'SUMIFS(%s,%s,%s,%s,%s)' % (CH('minutes'), CH('room'), LK('cleaning', 'chore_id', 'room'), CH('status'), OVD), 'int'),
        FF('Done on', '{today}', 'date')]),
    FORM('rotation_week_sheet', 'Rotation Week Sheet', 'One chore across the four rotation weeks', 'rotation.chore_id', F(
        ('Chore', 'rotation.chore'), ('Default owner', 'rotation.owner'), ('Minutes', 'rotation.minutes'), ('Minutes a week', 'rotation.min_week'), ('Points a week', 'rotation.pts_week'),
        ('Week 1', 'rotation.w1'), ('Week 2', 'rotation.w2'), ('Week 3', 'rotation.w3'), ('Week 4', 'rotation.w4'), ('Week 1 starts', 'rotation.week_date')) + [
        FF('Chores in week 1 for the same person', 'COUNTIFS(%s,%s)' % (R('rotation', 'w1'), LK('rotation', 'chore_id', 'w1')), 'int'),
        FF('Rotation method, from Settings', 'IF({set:rot_method}=%s,%s,%s)' % (tok('meth', 'Rotation'), tok('meth', 'Rotation'), tok('meth', 'Balance by points')), 'text')]),
    FORM('swap_request_sheet', 'Swap Request Sheet', 'One chore proposed for a swap and its 30 days', 'rotation.chore_id', F(
        ('Chore', 'rotation.chore'), ('Default owner', 'rotation.owner'), ('Week 1', 'rotation.w1'), ('Week 2', 'rotation.w2'), ('Minutes a week', 'rotation.min_week')) + [
        FF('Person after any swap', 'IF(%s="",%s,%s)' % (LK('rotation', 'chore_id', 'swap'), LK('rotation', 'chore_id', 'owner'), LK('rotation', 'chore_id', 'swap')), 'text'),
        FF('Minutes of this chore, last 30 days', 'SUMIFS(%s,%s,%s,%s,1)' % (LG('minutes'), LG('chore_id'), LK('rotation', 'chore_id', 'chore_id'), LG('last30')), 'int'),
        FF('Times done, last 30 days', 'COUNTIFS(%s,%s,%s,1)' % (LG('chore_id'), LK('rotation', 'chore_id', 'chore_id'), LG('last30')), 'int'),
        FF('Adult 2 share of adult minutes now', 'IFERROR(%s/(%s+%s),0)' % (LOGW('minutes', A2, W30, '{today}'), LOGW('minutes', A1, W30, '{today}'), LOGW('minutes', A2, W30, '{today}')), 'pct'),
        FF('Agreed share of adult 2, from Settings', '{set:agreed_split_a2}', 'pct')]),
    FORM('child_points_sheet', 'Child Points Sheet', "One child's week: points earned and balance", 'child_points.cp_id', F(
        ('Child', 'child_points.child'), ('Week', 'child_points.wk'), ('Week of', 'child_points.week_start'), ('Points earned', 'child_points.points'), ('Weekly points goal', 'child_points.goal'),
        ('Goal reached, 1 or 0', 'child_points.reached'), ('Points to goal', 'child_points.to_goal'), ('Points spent', 'child_points.spent'), ('Balance carried forward', 'child_points.balance'), ('Chores of the child', 'child_points.own_list')) + [
        FF('Weeks at goal of the 13', 'COUNTIFS(%s,%s,%s,1)' % (R('child_points', 'child'), LK('child_points', 'cp_id', 'child'), R('child_points', 'reached')), 'int'),
        FF('Points earned in the 13 weeks', 'SUMIFS(%s,%s,%s)' % (R('child_points', 'points'), R('child_points', 'child'), LK('child_points', 'cp_id', 'child')), 'int')]),
    FORM('reward_claim_sheet', 'Reward Claim Sheet', 'One reward for one child against the balance', 'ladder.rl_id', F(
        ('Child', 'ladder.child'), ('Reward', 'ladder.reward'), ('Points needed', 'ladder.points_needed'), ('Balance now', 'ladder.balance'), ('Points to go', 'ladder.to_go'), ('Status', 'ladder.status'),
        ('Points this week', 'ladder.pts_wk'), ('Points a week, last 4 weeks', 'ladder.avg_week'), ('Weeks to go', 'ladder.weeks_to_go')) + [
        FF('Balance after claiming', 'MAX(0,%s-%s)' % (LK('ladder', 'rl_id', 'balance'), LK('ladder', 'rl_id', 'points_needed')), 'int'),
        FF('Rewards on the ladder', 'COUNTA(%s)' % R('rewards', 'reward'), 'int')]),
    FORM('laundry_day_sheet', 'Laundry Day Sheet', 'One load type: day, interval, next change', 'laundry.load', F(
        ('Usual day', 'laundry.usual_day'), ('Who', 'laundry.who'), ('Loads a week', 'laundry.loads_wk'), ('Minutes per load', 'laundry.minutes'), ('Change every, days', 'laundry.interval_days'), ('Last changed', 'laundry.last_changed'),
        ('Next change', 'laundry.next_change'), ('Days to the change', 'laundry.days_to'), ('Status', 'laundry.status'), ('Minutes a week', 'laundry.min_week'), ('Loads on that day', 'laundry.day_loads'), ('Busiest day', 'laundry.busy_day')) + [
        FF('Share of all laundry loads', 'IFERROR(%s/SUM(%s),0)' % (LK('laundry', 'load', 'loads_wk'), R('laundry', 'loads_wk')), 'pct')]),
    FORM('away_week_sheet', 'Away Week Sheet', 'One away day and the chores that move', 'away.away_id', F(
        ('Day', 'away.day'), ('Person away', 'away.person'), ('Hours away', 'away.hours'), ('Note', 'away.note'), ('Chores of the person that day', 'away.owned_n'), ('Minutes of the person that day', 'away.owned_min'),
        ('Covered by', 'away.cover'), ('Away from', 'away.away_from'), ('Away until', 'away.away_to'), ('Chores unowned until then', 'away.unowned')) + [
        FF('Away days of that person', 'COUNTIFS(%s,%s)' % (R('away', 'person'), LK('away', 'away_id', 'person')), 'int'),
        FF('Hours away of that person in all', 'SUMIFS(%s,%s,%s)' % (R('away', 'hours'), R('away', 'person'), LK('away', 'away_id', 'person')), 'int')]),
    FORM('fairness_review_sheet', 'Fairness Review Sheet', 'One household member against the agreed share', 'team.member_id', F(
        ('Name', 'team.name'), ('Person in the chore sheets', 'team.person'), ('Minutes last 30 days', 'team.mins30'), ('Points this week', 'team.pts_wk'), ('Share of adult minutes', 'team.share30'),
        ('Agreed share', 'team.agreed'), ('Hidden jobs held', 'team.hidden_n'), ('Hidden minutes a month', 'team.hidden_min'), ('Own chores', 'team.own_list')) + [
        FF('Gap to the agreed share, points of share', 'IF(%s="","",ROUND((%s-%s)*100,0))' % (LK('team', 'member_id', 'share30'), LK('team', 'member_id', 'share30'), LK('team', 'member_id', 'agreed')), 'int'),
        FF('In line when within, points of share', 'ROUND({set:fair_band}*100,0)', 'int'),
        FF('Adult minutes in all, last 30 days', 'SUMIFS(%s,%s,%s)+SUMIFS(%s,%s,%s)' % (R('team', 'mins30'), R('team', 'person'), A1, R('team', 'mins30'), R('team', 'person'), A2), 'int')]),
    FORM('room_deep_clean_sheet', 'Room Deep Clean Sheet', 'One room: usual and deep clean minutes', 'room_load.room', F(
        ('Minutes a week', 'room_load.min_week'), ('Overdue chores', 'room_load.overdue')) + [
        FF('Chores in the room, daily ones left out', 'COUNTIFS(%s,{pick},%s,"<>"&%s,%s,"<>"&%s,%s)' % (CH('room'), CH('hidden'), YES, CH('frequency'), DAILY, NOTPAU), 'int'),
        FF('Usual minutes of those chores', 'SUMIFS(%s,%s,{pick},%s,"<>"&%s,%s,"<>"&%s,%s)' % (CH('minutes'), CH('room'), CH('hidden'), YES, CH('frequency'), DAILY, NOTPAU), 'int'),
        FF('Deep clean minutes', 'ROUND({set:deep_factor}*SUMIFS(%s,%s,{pick},%s,"<>"&%s,%s,"<>"&%s,%s),0)' % (CH('minutes'), CH('room'), CH('hidden'), YES, CH('frequency'), DAILY, NOTPAU), 'int'),
        FF('Days at the pace in Settings', 'ROUNDUP({set:deep_factor}*SUMIFS(%s,%s,{pick},%s,"<>"&%s,%s,"<>"&%s,%s)/{set:pace_min},0)' % (CH('minutes'), CH('room'), CH('hidden'), YES, CH('frequency'), DAILY, NOTPAU), 'int'),
        FF('Longest chore of the room', 'IFERROR(INDEX(%s,MATCH({pick}&"-1",%s,0)),"")' % (CH('chore'), CH('rkey')), 'text'),
        FF('Share of all chore minutes', 'IFERROR(%s/SUM(%s),0)' % (LK('room_load', 'room', 'min_week'), R('room_load', 'min_week')), 'pct')]),
    FORM('hidden_job_sheet', 'Hidden Job Sheet', 'One hidden job: planning, booking or remembering', 'hidden.chore', F(
        ('Default owner', 'hidden.owner'), ('Minutes a month', 'hidden.min_month')) + [
        FF('Frequency', 'INDEX(%s,MATCH({pick},%s,0))' % (CH('frequency'), CH('chore')), 'text'), FF('Minutes each time', 'INDEX(%s,MATCH({pick},%s,0))' % (CH('minutes'), CH('chore')), 'int'),
        FF('Last done', 'INDEX(%s,MATCH({pick},%s,0))' % (CH('last_done'), CH('chore')), 'date'), FF('Next due', 'INDEX(%s,MATCH({pick},%s,0))' % (CH('next_due'), CH('chore')), 'date'),
        FF('Hidden minutes a month of the same owner', 'SUMIFS(%s,%s,%s)' % (R('hidden', 'min_month'), R('hidden', 'owner'), LK('hidden', 'chore', 'owner')), 'int'),
        FF('Share of all hidden minutes', 'IFERROR(%s/SUM(%s),0)' % (LK('hidden', 'chore', 'min_month'), R('hidden', 'min_month')), 'pct')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('weekly_plan_doc', 'Weekly Cleaning Plan', 'Weekly cleaning plan, most overdue first', 'cleaning_plan.rank', [
        'Weekly cleaning plan of {set:household} for the week of {col:cleaning_plan.week_date}, dated {today}. Place {col:cleaning_plan.rank}: {col:cleaning_plan.chore}, room {col:cleaning_plan.room}.',
        'Do by {col:cleaning_plan.due_date}. Days overdue: {col:cleaning_plan.overdue_days}. Minutes: {col:cleaning_plan.minutes}. Default owner: {col:cleaning_plan.owner}. Suggested doer from the work pattern: {col:cleaning_plan.suggested}.',
        'Minutes so far down the list: {col:cleaning_plan.cum_min}. The ranking is calculated from the dates you typed; nothing here is a deadline.',
        'Tick when done: [ ]'], SG, NOTE),
    DOC('fridge_chart_doc', 'Chore Chart for the Fridge', 'Chore chart for the fridge, by person and day', 'chores.chore_id', [
        'Chore chart of {set:household}, dated {today}. {col:chores.chore}, in the {col:chores.room}: {col:chores.frequency}, about {col:chores.minutes} minutes, {col:chores.points} points.',
        'Default owner: {col:chores.owner}. Last done: {col:chores.last_done}. Next due: {col:chores.next_due}. Status: {col:chores.status}.',
        'Mon [ ]  Tue [ ]  Wed [ ]  Thu [ ]  Fri [ ]  Sat [ ]  Sun [ ]',
        'Tick the day it is done and type it in the Chore log on Sunday.'], SG, NOTE),
    DOC('kids_chart_doc', "Kids Chore and Points Chart", "Children's chore and points chart", 'child_points.cp_id', [
        "Chart of {col:child_points.first_name} for the week of {col:child_points.week_start}, {set:household}. Chores: {col:child_points.own_list}.",
        'Points earned: {col:child_points.points} of the goal of {col:child_points.goal}. Goal reached, 1 or 0: {col:child_points.reached}. Points spent: {col:child_points.spent}. Balance carried forward: {col:child_points.balance}.',
        'Points are for chores done, never money. A star for each day: Mon [ ] Tue [ ] Wed [ ] Thu [ ] Fri [ ] Sat [ ] Sun [ ]',
        'Talk it through together on {col:child_points.weekend}.'], ['Adult', 'Child'], NOTE),
    DOC('ladder_doc', 'Reward Ladder Page', 'Reward ladder page for one child', 'ladder.rl_id', [
        'Reward ladder of {col:ladder.first_name}, {set:household}, dated {today}. Reward: {col:ladder.reward}, {col:ladder.points_needed} points.',
        'Balance now: {col:ladder.balance}. Points to go: {col:ladder.to_go}. Status: {col:ladder.status}. Points a week over the last 4 weeks: {col:ladder.avg_week}. Weeks to go at that pace: {col:ladder.weeks_to_go}.',
        'Points this week: {col:ladder.pts_wk}. The ladder is points only, never money.',
        'Claimed on: ________'], ['Adult', 'Child'], NOTE),
    DOC('laundry_page_doc', 'Laundry Rota Page', 'Laundry rota page by load type', 'laundry.load', [
        'Laundry rota of {set:household} for the week of {col:laundry.week_date}. Load: {col:laundry.load}, usual day {col:laundry.usual_day}, done by {col:laundry.who}.',
        'Loads a week: {col:laundry.loads_wk}, {col:laundry.minutes} minutes per load. Busiest day of the week: {col:laundry.busy_day}, {col:laundry.day_loads} loads on that day. Loads a week, all types: {col:laundry.loads_total}.',
        'Change every {col:laundry.interval_days} days, typical, your own habit. Last changed {col:laundry.last_changed}, next change {col:laundry.next_change}, status {col:laundry.status}.',
        'Check the label of each item before you wash it.'], SG, NOTE),
    DOC('rotation_plan_doc', 'Rotation Plan for 4 Weeks', 'Rotation plan for four weeks', 'rotation.chore_id', [
        'Rotation plan of {set:household}, dated {today}, week 1 starts {col:rotation.week_date}. Chore: {col:rotation.chore}, {col:rotation.minutes} minutes, default owner {col:rotation.owner}.',
        'Week 1: {col:rotation.w1}. Week 2: {col:rotation.w2}. Week 3: {col:rotation.w3}. Week 4: {col:rotation.w4}.',
        'Minutes a week: {col:rotation.min_week}. Points a week: {col:rotation.pts_week}. A swap typed in the Swap cell holds for all four weeks.',
        'Agreed together on: ________'], SG, NOTE),
    DOC('fairness_doc', 'Fairness Summary', 'Fairness summary for the household meeting', 'team.member_id', [
        'Fairness summary of {set:household}, dated {today}, for {col:team.name}, shown as {col:team.person}. Next meeting: {col:team.meeting_date}.',
        'Minutes in the last 30 days: {col:team.mins30}. Points this week: {col:team.pts_wk}. Share of adult minutes: {col:team.share30} against an agreed {col:team.agreed}.',
        'Hidden jobs held: {col:team.hidden_n}, about {col:team.hidden_min} minutes a month. Chores: {col:team.own_list}.',
        'This is a view calculated from the Chore log, not a verdict. What shall we change? ________'], SG, NOTE),
    DOC('away_plan_doc', 'Away-Week Chore Plan', 'Away-week chore plan', 'away.away_id', [
        'Away-week chore plan of {set:household}, dated {today}. {col:away.person} is away on {col:away.day}, from {col:away.away_from} to {col:away.away_to}. Hours away: {col:away.hours}.',
        'Chores of the person that day: {col:away.owned_n}, {col:away.owned_min} minutes. Covered by: {col:away.cover}. Chores unowned until {col:away.away_to}: {col:away.unowned}.',
        'Note: {col:away.note}. Pick the unowned chores together and write the name on the chart.',
        'Agreed on: ________'], SG, NOTE),
    DOC('spring_plan_doc', 'Spring Clean Plan by Room', 'Spring clean plan by room', 'cleaning.chore_id', [
        'Spring clean plan of {set:household}, dated {today}. Room: {col:cleaning.room}, with {col:cleaning.room_n} chores and about {col:cleaning.room_wk} minutes a week.',
        'Deep clean minutes of the room: {col:cleaning.deep_min}, about {col:cleaning.deep_days} days at {set:pace_min} minutes a day. Longest chores: {col:cleaning.t1}, {col:cleaning.t2}, {col:cleaning.t3}.',
        'Check the manufacturer\'s instructions for every product and surface. Overdue chores in the room: {col:cleaning.room_over}.',
        'Day of the room: ________   Done by: ________'], SG, NOTE),
    DOC('sitter_card_doc', 'Chore Card for a Sitter', 'Chore card for a sitter or a grandparent', 'team.member_id', [
        'Chore card of {set:household} for {col:team.first_name}, dated {today}. What is expected, nothing more.',
        'Child 1 does {col:team.c1a}. Child 2 does {col:team.c2a} and {col:team.c2b}. The chart is on the fridge; please tick it with them.',
        'Everything else can stay as it is. Thank you.',
        'Our numbers are on the emergency page of this household.'], ['Household', 'Visitor'], NOTE),
    DOC('monthly_review_doc', 'Monthly Chore Review', 'Monthly chore review', 'history.month', [
        'Monthly chore review of {set:household} for the month starting {col:history.month}.',
        'Chores done: {col:history.done}. Chores missed: {col:history.missed}. Minutes of adult 1: {col:history.a1_min}. Minutes of adult 2: {col:history.a2_min}. Minutes of the children: {col:history.kids_min}.',
        'Adult 2 share of adult minutes: {col:history.a2_share}, against {col:history.avg3} on average in the 3 months before.',
        'One thing to change next month: ________'], SG, NOTE),
    DOC('room_checklist_doc', 'Room-by-Room Cleaning Page', 'Room-by-room cleaning checklist page', 'room_load.room', [
        'Cleaning page of {set:household} for the {col:room_load.room}, dated {today}. Minutes a week: {col:room_load.min_week}. Overdue chores: {col:room_load.overdue}.',
        'Dust high to low [ ]   Wipe the surfaces [ ]   Clean the floor [ ]   Empty the bin [ ]   Check the corners [ ]',
        'Write the extra jobs of the room below.',
        '____________________________________________'], SG, NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('daily_reset', 'Daily Reset Steps', 'work_pattern', 'work_pattern.date', [('Dishes into the machine or washed', 0), ('Wipe the kitchen surfaces', 0), ('Tidy the living room', 0), ('Feed the pets', 0), ('Check the chore chart', 0)]),
    CHK('weekly_clean', 'Weekly Clean by Room Steps', 'work_pattern', 'work_pattern.date', [('Open the Cleaning Plan This Week', 0), ('Kitchen: floor and cupboard fronts', 1), ('Bathroom: clean and toilet', 2), ('Vacuum the living areas and stairs', 3), ('Dust the surfaces', 4), ('Type the chores done in the Chore log', 6)]),
    CHK('laundry_day', 'Laundry Day Steps', 'laundry', 'laundry.last_changed', [('Sort the loads by type', 0), ('Check the care labels', 0), ('Start the first load', 0), ('Hang or dry the loads', 1), ('Fold and put away', 1), ('Type the day in the Laundry rota', 2)]),
    CHK('bedding_change', 'Bedding and Towel Change Steps', 'laundry', 'laundry.last_changed', [('Strip the beds', 0), ('Wash the bed linen', 0), ('Wash the towels', 1), ('Make the beds', 1), ('Type the date of the change', 2)]),
    CHK('monthly_deep', 'Monthly Deep Clean Steps', 'history', 'history.month', [('Clean the oven', 0), ('Descale the kettle', 1), ('Wipe the skirting boards', 2), ('Vacuum under the furniture', 3), ('Scrub the bathroom grout', 4), ('Read the monthly chore review', 27)]),
    CHK('quarterly_windows', 'Quarterly Windows Steps', 'chores', 'chores.last_done', [('Pick a dry day', 0), ('Wash the windows', 1), ('Take down the curtains', 2), ('Wash the curtains', 2), ('Hang the curtains again', 3), ('Type the date in the Chores sheet', 3)]),
    CHK('spring_clean', 'Spring Clean Steps', 'chores', 'chores.last_done', [('Open the Spring Clean Planner', 0), ('Split the rooms between the adults', 0), ('Declutter the cupboards', 1), ('Deep clean the oven and extractor', 2), ('Turn the mattresses', 3), ('Wash the outdoor furniture', 4), ('Type the dates in the Chores sheet', 5)]),
    CHK('wardrobe_swap', 'Autumn Wardrobe Swap Steps', 'history', 'history.month', [('Take out the winter clothes', 0), ('Wash what has been stored', 1), ('Sort the outgrown clothes', 2), ('Store the summer clothes', 3), ('Type the date in the Chores sheet', 4)]),
    CHK('rotation_day', 'Rotation Day Steps', 'work_pattern', 'work_pattern.date', [('Open the Chore Rotation Generator', 0), ('Choose the method', 0), ('Check the swaps', 0), ('Print the Rotation Plan for 4 Weeks', 0), ('Put the chart on the fridge', 1)]),
    CHK('chore_meeting', 'Household Chore Meeting Steps', 'history', 'history.month', [('Print the Fairness Summary', 27), ('Read the fairness check together', 28), ('Look at the hidden jobs', 28), ('Agree one change', 28), ('Write the change on the chart', 28)]),
    CHK('away_week', 'Week With One Person Away Steps', 'away', 'away.day', [('Open the Chore Week One Person Away', -3), ('Pick the covering person', -2), ('Share the unowned chores', -1), ('Update the chart', 0), ('Welcome back and hand the chores over', 5)]),
    CHK('single_start', 'Single Adult Cleaning Steps', 'team', 'team.start', [('Replace the demo chores with your own', 0), ('Leave the children and rotation sheets empty', 0), ('Type the last done date of each chore', 1), ('Read Cleaning Plan This Week', 2), ('Set the due soon window in Settings', 3), ('Type what you did in the Chore log', 7)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('a2_share', 'Adult 2: share of adult minutes', 'team', 'team.a2_phone', 'Hi {first_name}, in the last 30 days you carry {share30} of the adult chore minutes against our agreed {agreed}. Shall we look at the rotation? {household}'),
    M('a2_late', 'Adult 2: chore on a Late shift', 'chores', 'chores.a2late_phone', 'Hi {owner_first}, {chore} is yours on {next_due} and your shift is {a2_shift_due}. Shall we swap? {household}'),
    M('a2_thanks', 'Adult 2: thank you for a chore', 'chore_log', 'chore_log.a2_phone', 'Hi {who_first}, thank you for {chore} on {done}, it took {minutes} minutes.'),
    M('a1_rotation', 'Adult 1: the rotation gives you a chore', 'rotation', 'rotation.a1_phone', 'Hi {w1_first}, the rotation for the week of {week_date} gives you {chore}, {minutes} minutes. {household}'),
    M('a1_hidden', 'Adult 1: hidden jobs held', 'team', 'team.hm_phone', 'Hi {first_name}, the hidden jobs list shows {hidden_n} jobs with you, about {hidden_min} minutes a month. Shall we share the planning? {household}'),
    M('a1_overdue', 'Adult 1: a chore is overdue', 'chores', 'chores.od_phone', 'Hi {owner_first}, {chore} is {overdue_days} days overdue. Can we agree who does it by {agree_by}? {household}'),
    M('a1_late', 'Adult 1: late day plan', 'work_pattern', 'work_pattern.a1_phone_late', 'Hi {a1_first}, late day on {date}: I have the dishes and the bedtime routine, you take the lunch boxes in the morning. {household}'),
    M('c1_week', 'Child 1: chores and points this week', 'team', 'team.c1_phone', 'Hi {first_name}, your chores this week are {own_list}, you have {pts_wk} points of {goal_pts}. {household}'),
    M('c1_well', 'Child 1: well done, next reward', 'ladder', 'ladder.phone_c1', 'Hi {first_name}, well done, you reached {pts_wk} points this week and the next reward is {reward} at {points_needed} points. {household}'),
    M('c1_please', 'Child 1: please do a chore', 'chores', 'chores.c1_phone', 'Hi {owner_first}, please do {chore} by {agree_by}, it is worth {points} points. {household}'),
    M('c1_balance', 'Child 1: points balance', 'child_points', 'child_points.c1_phone', 'Hi {first_name}, your points balance is {balance}, carried to next week. {household}'),
    M('c2_chore', 'Child 2: chore this week', 'team', 'team.c2_phone', 'Hi {first_name}, your chore this week is {c2a}, we do it together on {meeting_date}. {household}'),
    M('c2_points', 'Child 2: points this week', 'ladder', 'ladder.phone_c2', 'Hi {first_name}, you earned {pts_wk} points this week, the next reward is {reward}. {household}'),
    M('c2_pets', 'Child 2: feed the pets', 'team', 'team.c2_phone', 'Hi {first_name}, please feed the pets from {week_date} and tick the chart. {household}'),
    M('gp_thanks', 'Grandparent: thank you for helping', 'team', 'team.gp_phone', 'Hello {first_name}, thank you for helping on {next_date}. The chore for your visit is watering the plants only. {household}'),
    M('gp_rest', 'Grandparent: a rest day', 'team', 'team.gp_phone', 'Hello {first_name}, your visit on {next_date} is a rest day, nothing is expected. {household}'),
    M('bs_bedtime', 'Babysitter: chore before bedtime', 'team', 'team.bs_phone', 'Hi {first_name}, on {next_date} the children have {c1a} before bedtime, the chart is on the fridge. {household}'),
    M('bs_evening', 'Babysitter: chores for the evening', 'team', 'team.bs_phone', 'Hi {first_name}, the children\'s chores for the evening are {c2a} and {c2b}. {household}'),
    M('cp_lift', 'Carpool family: before the lift', 'team', 'team.cp_phone', 'Hello {first_name}, the children are doing {c1a} before the lift on {next_date}, we leave at {at_time}. {household}'),
    M('nb_away', 'Neighbour: we are away', 'team', 'team.nb_phone', 'Hello {first_name}, we are away from {next_date} to {end_date}, please water the plants if you can. {household}'),
    M('nb_bins', 'Neighbour: thank you for the bins', 'team', 'team.nb_phone', 'Hello {first_name}, thank you for taking the bins in this week, the week of {week_date}. {household}'),
    M('dw_dinner', "Dog walker: the dog's dinner", 'team', 'team.dw_phone', 'Hi {first_name}, the dog\'s dinner is at {at_time} on {next_date}, the bowl is on the counter. {household}'),
    M('dw_tick', 'Dog walker: tick the walk', 'team', 'team.dw_phone', 'Hi {first_name}, please tick the walk on the chart on {next_date}. {household}'),
    M('sc_away', 'School office: child away', 'team', 'team.sc_phone', 'Hello {first_name}, {child1} is away on {next_date}, the chore day moves. {household}'),
    M('hm_plan', 'Household member: cleaning plan is up', 'team', 'team.hm_phone', 'Hi {first_name}, the cleaning plan for the week of {week_date} is on the fridge, {due_n} chores due. {household}'),
    M('hm_laundry', 'Household member: the laundry rota', 'laundry', 'laundry.phone', 'Hi {who_first}, the laundry rota for the week of {week_date} has {loads_total} loads, the busiest day is {busy_day}. {household}'),
    M('hm_bedding', 'Household member: the bedding change', 'laundry', 'laundry.phone', 'Hi {who_first}, the {load} change is on {next_change}. {household}'),
    M('hm_meeting', 'Household member: monthly meeting', 'done_missed', 'done_missed.phone', 'Hi {first_name}, the monthly chore meeting is on {meeting_date} at {meeting_time}. {household}'),
    M('hm_away', 'Household member: someone is away', 'away', 'away.cover_phone', 'Hi {cover_first}, {person} is away from {away_from} to {away_to}, {unowned} chores are unowned, please pick one. {household}'),
    M('hm_soon', 'Household member: a chore is due soon', 'chores', 'chores.soon_phone', 'Hi {owner_first}, {chore} is due on {next_due}, who takes it? {household}'),
    M('hm_windows', 'Household member: a deep clean is due', 'chores', 'chores.deep_phone', 'Hi {owner_first}, {chore} is due on {next_due}, it is a {minutes}-minute job. {household}'),
    M('hm_overdue', 'Household member: chores are overdue', 'team', 'team.hm_phone', 'Hi {first_name}, {overdue_n} chores are overdue, the list is on the fridge. {household}'),
    M('hm_spring', 'Household member: the spring clean', 'chores', 'chores.spring_phone', 'Hi {owner_first}, the spring clean is on {spring_date}, the {room} is yours. {household}'),
    M('hm_review', 'Household member: month chore review', 'history', 'history.phone', 'Hi {first_name}, month chore review for the month starting {month}: {done} done, {missed} missed. {household}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def W_(c, op, v): return (c, op, v)
HB = R('hidden', 'min_month')
kpis = [
    KPI('Chores in the plan', 'COUNTIFS(%s,"<>",%s)' % (CH('chore_id'), NOTPAU), 'int'),
    KPI('Chores due this week', 'COUNTIFS(%s,1)' % CH('due_week'), 'int'),
    KPI('Chores overdue', 'COUNTIFS(%s,%s)' % (CH('status'), OVD), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Overdue minutes', 'SUMIFS(%s,%s,%s)' % (CH('minutes'), CH('status'), OVD), 'int'),
    KPI('Chores done, last 30 days', 'COUNTIFS(%s,1)' % LG('last30'), 'int'),
    KPI('Chore minutes done, last 30 days', 'SUMIFS(%s,%s,1)' % (LG('minutes'), LG('last30')), 'int'),
    KPI('Chore points earned, last 30 days', 'SUMIFS(%s,%s,1)' % (LG('points'), LG('last30')), 'int'),
    KPI('Adult 1 minutes, last 30 days', LOGW('minutes', A1, W30, '{today}'), 'int'),
    KPI('Adult 2 minutes, last 30 days', LOGW('minutes', A2, W30, '{today}'), 'int'),
    KPI('Adult 2 share of adult minutes, 30 days', 'IFERROR(%s/(%s+%s),0)' % (LOGW('minutes', A2, W30, '{today}'), LOGW('minutes', A1, W30, '{today}'), LOGW('minutes', A2, W30, '{today}')), 'pct'),
    KPI('Gap to the agreed share, points of share', 'ROUND((IFERROR(%s/(%s+%s),0)-{set:agreed_split_a2})*100,0)' % (LOGW('minutes', A2, W30, '{today}'), LOGW('minutes', A1, W30, '{today}'), LOGW('minutes', A2, W30, '{today}')), 'int', alert={"when": "> 5", "style": "warn"}),
    KPI("Children's minutes, last 30 days", '%s+%s' % (LOGW('minutes', C1, W30, '{today}'), LOGW('minutes', C2, W30, '{today}')), 'int'),
    KPI('Child 1 points this week', LOGW('points', C1, WS, '{today}'), 'int'),
    KPI('Child 2 points this week', LOGW('points', C2, WS, '{today}'), 'int'),
    KPI("Children's points balance", 'SUMIFS(%s,%s,13)' % (R('child_points', 'balance'), R('child_points', 'wkn')), 'int'),
    KPI('Children at the goal, last full week', 'COUNTIFS(%s,12,%s,1)' % (R('child_points', 'wkn'), R('child_points', 'reached')), 'int'),
    KPI('Hidden jobs in the plan', 'COUNTIFS(%s,%s,%s)' % (CH('hidden'), YES, NOTPAU), 'int'),
    KPI('Hidden-job minutes a month', 'SUM(%s)' % HB, 'int'),
    KPI('Hidden-job share held by adult 1', 'IFERROR(SUMIFS(%s,%s,%s)/SUM(%s),0)' % (HB, R('hidden', 'owner'), A1, HB), 'pct'),
    KPI('Chores without an owner', 'COUNTIFS(%s,"<>",%s,0,%s)' % (CH('chore_id'), CH('grp'), NOTPAU), 'int'),
    KPI('Daily chores done yesterday', 'COUNTIFS(%s,{today}-1,%s,1)' % (LG('done'), LG('freq_d')), 'int'),
    KPI('Laundry loads a week', 'SUM(%s)' % R('laundry', 'loads_wk'), 'num'),
    KPI('Busiest laundry day', 'IFERROR(INDEX(%s,1),"")' % R('laundry', 'busy_day'), 'text'),
    KPI('Weeks in a row at goal', 'SUMIFS(%s,%s,12)' % (R('done_missed', 'run'), R('done_missed', 'wkn')), 'int'),
    KPI('Chores done share, last 4 full weeks', 'IFERROR(SUMIFS(%s,%s,">=9",%s,"<=12")/SUMIFS(%s,%s,">=9",%s,"<=12"),0)' % (R('done_missed', 'done'), R('done_missed', 'wkn'), R('done_missed', 'wkn'), R('done_missed', 'due'), R('done_missed', 'wkn'), R('done_missed', 'wkn')), 'pct'),
    KPI('Chores missed, last 4 complete weeks', 'SUMIFS(%s,%s,">=9",%s,"<=12")' % (R('done_missed', 'missed'), R('done_missed', 'wkn'), R('done_missed', 'wkn')), 'int'),
    KPI('Average adult 2 share, 3 complete months', 'IFERROR(AVERAGEIFS(%s,%s,">="&EDATE(%s,-3),%s,"<"&%s),0)' % (R('history', 'a2_share'), R('history', 'month'), MSD, R('history', 'month'), MSD), 'pct'),
    KPI('Rooms with overdue chores', 'COUNTIFS(%s,">0")' % R('room_load', 'overdue'), 'int'),
    KPI('Most overdue chore, days', 'MAX(%s)' % CH('overdue_days'), 'int'),
    KPI('Deep cleans due in the next 30 days', '+'.join('COUNTIFS(%s,%s,%s,">="&{today},%s,"<="&({today}+30),%s)' % (CH('frequency'), f, CH('next_due'), CH('next_due'), NOTPAU) for f in (QUART, TWICE, YEARLY)), 'int'),
]
assert len(kpis) == 30, len(kpis)
dashboard = {"title": "Chores and Laundry Dashboard", "kpis": kpis,
    "monthly": {"title": "Chore minutes per month: adult 1, adult 2 and the children", "date": "history.month", "series": [
        {"label": "Adult 1 minutes", "sum": "history.a1_min", "date": "history.month"}, {"label": "Adult 2 minutes", "sum": "history.a2_min", "date": "history.month"},
        {"label": "Children minutes", "sum": "history.kids_min", "date": "history.month"}]},
    "breakdowns": [{"title": "Chores by room", "by": "chores.room", "value": "chores.minutes", "agg": "count"}, {"title": "Chore minutes by frequency", "by": "freq_sum.frequency", "value": "freq_sum.min_week", "agg": "sum"},
                   {"title": "Chores by default owner", "by": "chores.owner", "value": "chores.minutes", "agg": "count"}, {"title": "Laundry loads by type", "by": "laundry.load", "value": "laundry.loads_wk", "agg": "sum"}]}
ROOMS_ = ['Kitchen', 'Living room', 'Bathroom', 'Utility room']
insights = {"filters": [{"label": "Room", "list": "room"}, {"label": "Person", "list": "person"}, {"label": "Frequency", "list": "freq"}],
    "gauges": [
        {"title": "Chores not overdue", "num": AGG('count', 'chores', where=[W_('status', '<>', OVD)]), "den": AGG('count', 'chores')},
        {"title": "Adult 2 share of adult minutes", "num": AGG('sum', 'fairness', 'fairness.minutes', where=[W_('person', '=', A2)]), "den": AGG('sum', 'fairness', 'fairness.minutes', where=[W_('person', '=', A1)])},
        {"title": "Children's weekly points goal reached", "num": AGG('sum', 'child_points', 'child_points.points', where=[W_('wkn', '=', 13)]), "den": AGG('sum', 'child_points', 'child_points.goal', where=[W_('wkn', '=', 13)])},
        {"title": "Hidden jobs held by adult 1", "num": AGG('count', 'chores', where=[W_('hidden', '=', YES), W_('owner', '=', A1)]), "den": AGG('count', 'chores', where=[W_('hidden', '=', YES)])},
        {"title": "Overdue minutes against free minutes", "num": AGG('sum', 'chores', 'chores.minutes', where=[W_('status', '=', OVD)]), "den": AGG('sum', 'work_pattern', 'work_pattern.free_both', where=[W_('this_week', '=', 1)])},
        {"title": "Chores with an owner", "num": AGG('count', 'chores', where=[W_('grp', '>', 0)]), "den": AGG('count', 'chores')}],
    "charts": [
        CHART('Chore minutes per month by person', 'column', 'month', [AGG('sum', 'chore_log', 'chore_log.minutes', date='chore_log.done', where=[W_('who', '=', p)], label=l) for p, l in ((A1, 'Adult 1'), (A2, 'Adult 2'), (C1, 'Child 1'), (C2, 'Child 2'))]),
        CHART('Adult 2 share per month', 'column', 'month', [AGG('avg', 'history', 'history.a2_share', date='history.month', label='Adult 2 share')]),
        CHART('Chores done per month', 'column', 'month', [AGG('count', 'chore_log', date='chore_log.done', label='Chores done')]),
        CHART('Done and missed per week', 'column', 'done_missed.wk', [AGG('sum', 'done_missed', 'done_missed.done', label='Done'), AGG('sum', 'done_missed', 'done_missed.missed', label='Missed')]),
        CHART('Minutes a week by room', 'bar', 'room_load.room', [AGG('sum', 'room_load', 'room_load.min_week', label='Minutes a week')]),
        CHART('Minutes a week by frequency', 'bar', 'freq_sum.frequency', [AGG('sum', 'freq_sum', 'freq_sum.min_week', label='Minutes a week')]),
        CHART('Chores by room', 'bar', 'chores.room', [AGG('count', 'chores', label='Chores')]),
        CHART('Minutes by person, last 30 days', 'bar', 'chore_log.who', [AGG('sum', 'chore_log', 'chore_log.minutes', where=[W_('last30', '=', 1)], label='Minutes')]),
        CHART('Points by person per month', 'column', 'month', [AGG('sum', 'chore_log', 'chore_log.points', date='chore_log.done', where=[W_('who', '=', p)], label=l) for p, l in ((A1, 'Adult 1'), (A2, 'Adult 2'), (C1, 'Child 1'), (C2, 'Child 2'))]),
        CHART("Children's points per week", 'column', 'child_points.wk', [AGG('sum', 'child_points', 'child_points.points', where=[W_('child', '=', C1)], label='Child 1'), AGG('sum', 'child_points', 'child_points.points', where=[W_('child', '=', C2)], label='Child 2')]),
        CHART('Hidden jobs by owner', 'bar', 'chores.owner', [AGG('count', 'chores', where=[W_('hidden', '=', YES)], label='Hidden jobs')]),
        CHART('Overdue chores by room', 'bar', 'chores.room', [AGG('count', 'chores', where=[W_('status', '=', OVD)], label='Overdue chores')]),
        CHART('Overdue days by frequency', 'bar', 'chores.frequency', [AGG('sum', 'chores', 'chores.overdue_days', label='Overdue days')]),
        CHART('Chores by default owner', 'bar', 'chores.owner', [AGG('count', 'chores', label='Chores')]),
        CHART('Laundry loads by type', 'bar', 'laundry.load', [AGG('sum', 'laundry', 'laundry.loads_wk', label='Loads a week')]),
        CHART('Utility room minutes per month', 'column', 'month', [AGG('sum', 'chore_log', 'chore_log.minutes', date='chore_log.done', where=[W_('room', '=', tok('room', 'Utility room'))], label='Minutes')]),
        CHART('Chores done by weekday', 'bar', 'chore_log.weekday', [AGG('count', 'chore_log', label='Chores done')]),
        CHART('Chores done per month by room', 'column', 'month', [AGG('count', 'chore_log', date='chore_log.done', where=[W_('room', '=', tok('room', r))], label=r) for r in ROOMS_]),
        CHART('Late-day chores by person', 'bar', 'chore_log.who', [AGG('count', 'chore_log', where=[W_('late_day', '=', 1)], label='Chores on adult 1 late days')]),
        CHART('Points a week by frequency', 'bar', 'chores.frequency', [AGG('sum', 'chores', 'chores.pts_week', label='Points a week')]),
        CHART('Adult and children minutes per month', 'column', 'month', [AGG('sum', 'chore_log', 'chore_log.minutes', date='chore_log.done', where=[W_('adult', '=', 1)], label='Adults'), AGG('sum', 'chore_log', 'chore_log.minutes', date='chore_log.done', where=[W_('adult', '=', 0)], label='Children')]),
        CHART('Rewards by points needed', 'bar', 'ladder.reward', [AGG('avg', 'ladder', 'ladder.points_needed', label='Points needed')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Fairness check, last 30 days", "why": "each adult's minutes and points from the Chore log, the share of adult minutes and the gap to the share you agreed, as a view and never an alarm", "where": "Fairness Check, Last 30 Days"},
    {"name": "Fairness with hidden jobs", "why": "the same check after adding the planning, booking and remembering that never reach the chart", "where": "Fairness With Hidden Jobs"},
    {"name": "Chore rotation generator", "why": "a four-week rotation by method, rotation or balance by points, with a swap cell and the gap between the adults", "where": "Chore Rotation Generator"},
    {"name": "Cleaning plan this week", "why": "chores ranked most overdue first with the minutes and a suggested doer from the work pattern", "where": "Cleaning Plan This Week"},
    {"name": "Chore week with one person away", "why": "remove a person for chosen days and see who takes the chores and which stay unowned", "where": "Chore Week One Person Away"},
    {"name": "Children's points and reward", "why": "points this week against the goal, the balance carried forward and the points to the next reward, never money", "where": "Children Points and Reward"},
    {"name": "Who does what on a late day", "why": "the late days of adult 1 and the shift of adult 2 against the evening chores, with the minutes a helper covers", "where": "Who Does What on a Late Day"},
    {"name": "Free minutes by shift week", "why": "how many free hours each adult has in a late-shift week against a usual week", "where": "Free Minutes by Shift Week"},
    {"name": "Compare with own history", "why": "this month's adult 2 share against the 3 complete months before it, from your own Chore log", "where": "Compare With Own History"},
    {"name": "Chore swap tester", "why": "swap two chores between people and see the new shares before you agree", "where": "Chore Swap Tester"}]
competitors = [
    {"what": "single-slice cleaning log or chore chart template", "lacks": "a grid of ticks with no next due date, no overdue days, no rotation and no check of whose share is bigger"},
    {"what": "chore app with points and a yearly renewal", "lacks": "charges every year and keeps the household in an account, with no fairness check for the adults and no hidden jobs beside the visible ones"},
    {"what": "printable rota or rotation sheet", "lacks": "a fixed pattern you fill in by hand: no shift weeks, no swap cell, no away week and no minutes behind each name"},
    {"what": "meal-planner app with a paywall", "lacks": "plans dinners but does not know who does the chores that follow, so nothing says that adult 2 carries most of the minutes"},
    {"what": "single-sheet home organizer", "lacks": "one tab for everything: no laundry rota with the next bedding change, no reward ladder and no done and missed streaks"}]
guide = [
    'Start here: this workbook shows who does what in the house and whether it is fair. Open Settings on the Start sheet and type your household name, the children\'s first names and the agreed split in the yellow cells.',
    'Replace the demo data: clear the sample rows of Chores, Chore log, Rewards, Work pattern, Laundry rota and Away-week scenario and type your own; keep the lists and settings. Grey cells calculate by themselves.',
    'Chores: type each recurring chore with its room, frequency, minutes, default owner, effort points and the date it was last done; next due, overdue days and status calculate. Tick Paused when out of season. Intervals are typical, your own.',
    'Chore log: type each chore done with the date, who did it and how long it took. The fairness check, the history by month and the children\'s points all read this one sheet.',
    'Ranked and typed-once sheets (Cleaning Plan, Cleaning Schedule, Chore Rotation, Reward Ladder, Streaks): type the ranks or the names once and the rest fills in.',
    'Weekly routine, Sunday: plan the meals, check the shopping list, rotate the chores with the Chore Rotation Generator, read the Cleaning Plan and glance at the calendar.',
    'Monthly routine: pantry and freezer check, maintenance due, renewals in the next 90 days, a project check, and the household chore meeting with the Fairness Summary.',
    'Use the 18 tools for the questions of the week: what do we clean first, who carries what, how many points to the next reward, who does the evenings on a late day, what changes if someone is away.',
    'Print 12 sheets and 12 documents, follow 12 checklists and tap a message link to send a text with the details already written in; the tables with a phone column carry the links.',
    'A single adult uses the Chores and Cleaning sheets and leaves the children\'s points, fairness and rotation sheets empty; the Cleaning Plan still ranks what is overdue.',
    'Renters: read "a trade" as "a maintenance request to the landlord", and leave out the garden and exterior chores you do not own.',
    'Fairness is a view calculated from your entries, never a verdict or an alarm: it shows the minutes and the share so that the household can talk about them.',
    'Why a workbook: one flat price, no yearly renewal, your data stays with you, nothing to link or re-connect, no ads and no upsell. It works in Excel and Google Sheets with no macros, no add-ins and no accounts.',
    'What this is not: not a safety service, not a reminder app, not medical, veterinary, legal or financial advice. Every date, rank and share is calculated from your entries: typical, check the manufacturer\'s instructions and your local rules.']
assert 5 <= len(guide) <= 20
listing = {"title": "Chore Chart and Rotation Excel Template: Cleaning Schedule, Fairness Check, Laundry Rota, Kids Points and Rewards",
    "headline": "See who does what at home, what is overdue and whether it is fair",
    "tags": ["chore chart", "chore rotation", "cleaning schedule", "laundry rota", "fair share", "mental load", "kids chore points", "reward ladder", "household chores", "home management", "excel template", "family planner", "no subscription"],
    "description": ("Run the chores of your home from one Excel workbook: about 45 recurring chores by room and frequency with minutes, effort points and a default owner, a next due date and overdue days for every chore, and a weekly cleaning plan ranked most overdue first. "
        "Built for a single adult, a couple or a family, owners or renters, with a household of two adults, two children and a grandparent as the sample.\n\n"
        "The fairness check reads your Chore log and shows each adult's minutes and points in the last 30 days, the share of the adult total against the share you agreed, and the hidden jobs (planning, booking, remembering) beside the visible ones. It is a view calculated from your entries, never an alarm. "
        "The rotation generator builds four weeks by rotation or by balancing points, with a swap cell, and the away week moves the chores of one person to the others and lists what stays unowned.\n\n"
        "Children earn points, never money, on a reward ladder with a balance carried forward; the laundry rota shows the busiest day and the next bedding and towel change; done and missed by week, streaks and this month against the 3 complete months before it come from your own history. "
        "18 tools answer the questions of the week: what do we clean first, who does the evening chores on a late day, how many free hours each adult has in a late-shift week, how many days to clear the overdue list, and what a swap of two chores does to the shares. "
        "Print 12 sheets and 12 documents, follow 12 checklists and send 34 ready text messages to the household, the grandparent, the babysitter, the neighbour, the dog walker and the school office.\n\n"
        "This is part three of the eight-part Home Management suite. A standard .xlsx workbook with no macros, no accounts and no yearly renewal, with a demo copy full of sample data to explore first. "
        "Every date, rank and share is calculated from your entries: typical, check the manual and your local rules. It is a home kit, not a safety service, and gives no health, medical or legal advice."),
    "features": ["About 45 chores by room with next due and overdue days", "Weekly cleaning plan ranked most overdue first", "Fairness check with hidden jobs, a view and never an alarm", "Four-week rotation by method with a swap cell",
                 "Away week: who takes the chores, what stays unowned", "Children's points and a reward ladder, never money", f"{len(tools)} tools for the questions of every week", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "Single adults and renters can use it unchanged", "No macros, no accounts, no yearly renewal"]}
SUITE_ID = SUITE
s = spec(id=f'{SUITE_ID}-p3', slug='home-management-chores', profession='Home Management', name='Chores, Laundry and Rotation',
         tagline='See who does what at home, what is overdue and whether it is fair', price_usd=29,
         colors={"primary": "#3E5C76", "accent": "#E07A5F"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE_ID, "part": 3, "of": 8, "focus": "Cleaning, laundry and chore rotation: who does what and whether it is fair"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ho3.en.json'))
    names = [t['sheet'] for t in tables] + [t['sheet'] for t in tools] + [f['sheet'] for f in forms] + [d['sheet'] for d in documents]
    assert len(names) == len(set(names)), [n for n in names if names.count(n) > 1]
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
