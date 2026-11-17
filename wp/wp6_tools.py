"""Wedding suite part 6: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp6_lists import *
import wp6_data as D
from wp6_tables import *


def GR(title, *rows): return {"title": title, "rows": [{"label": l, "values": v_} for l, v_ in rows]}
def I(k, label, d, t='money', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, label_default): return IN(k, label, 'list', key(lst, label_default), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def IDX(t, c_, rk, k, txt=False): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0))%s,%s)' % (R(t, c_), k, R(t, rk), '&""' if txt else '', '""' if txt else '0')
def W(*words): return '&" "&'.join(words)


tools = []
PCOUNT = 'COUNTIFS(%s,"<>")' % R('party', 'party_id')

# 1 ------------------------------------------------------------ party roster check
MAXGAP = 'MAX(%s)' % R('party', 'gap_n')
GAPAT = 'MATCH(%s,%s,0)' % (MAXGAP, R('party', 'gap_n'))
tools.append(TOOL('roster_check', 'Party Roster Check', 'Does every party member have a role, task, outfit and phone',
    'Type how many people you expect in the party; every row is checked for a role, a task, an outfit status and a phone, and the verdict names the first gap.', [
    I('expected', 'People you expect in the roster', 14, 'int')], [
    O('People on the roster', 'int', PCOUNT), O('People you expect', 'int', '{in:expected}'),
    O('Rows without a role', 'int', 'COUNTIFS(%s,"<>",%s,"")' % (R('party', 'party_id'), R('party', 'role'))), O('Rows without a task', 'int', 'COUNTIFS(%s,"<>",%s,"")' % (R('party', 'party_id'), R('party', 'task'))),
    O('Rows without an outfit status', 'int', 'COUNTIFS(%s,"<>",%s,"")' % (R('party', 'party_id'), R('party', 'attire_status'))), O('Rows without a phone', 'int', 'COUNTIFS(%s,"<>",%s,"")' % (R('party', 'party_id'), R('party', 'phone'))),
    O('People with a complete row', 'int', 'COUNTIFS(%s,0)' % R('party', 'gap_n')), O('Gaps in all', 'int', 'SUM(%s)' % R('party', 'gap_n')),
    O('First person with a gap', 'text', 'IF(SUM(%s)=0,"",INDEX(%s,%s)&"")' % (R('party', 'gap_n'), R('party', 'person'), GAPAT)),
    O('Verdict', 'text', 'IF(SUM(%s)>0,%s&" "&INDEX(%s,%s)&" "&%s&" "&INDEX(%s,%s),IF(%s<{in:expected},%s&" "&({in:expected}-%s)&" "&%s,%s))' % (
        R('party', 'gap_n'), v('Missing'), R('party', 'gap_item'), GAPAT, v('for'), R('party', 'person'), GAPAT, PCOUNT, v('Add'), PCOUNT, v('people'), v('Complete')))],
    GR('What if', ('Fourteen expected', {'expected': 14}), ('Ten expected', {'expected': 10}), ('Twelve expected', {'expected': 12}), ('Sixteen expected', {'expected': 16}), ('Twenty expected', {'expected': 20}))))

# 2 ------------------------------------------------------------ last safe order date
PK = lambda c_: 'INDEX(%s,MATCH({in:person},%s,0))' % (R('party', c_), R('party', 'person'))
ALT = 'IF({in:alt}>0,{in:alt},%s)' % PK('alteration_weeks')
LATEST = '({set:wedding_day}-%s*7-{in:margin})' % ALT
LAST = 'MIN(%s,%s)-{in:ship}' % (PK('fitting_date'), LATEST)
tools.append(TOOL('order_date', 'Last Safe Order Date', 'By when must each outfit be ordered',
    'Pick a person and type the shipping days, the safety margin and the alteration weeks (0 uses the roster); it counts back from the fitting and says how many days are left.', [
    IL('person', 'Person', 'person', 'Hugo Lund'), I('ship', 'Days the outfit takes to arrive', 21, 'int'), I('margin', 'Safety margin in days', 7, 'int'), I('alt', 'Alteration weeks, 0 uses the roster', 0, 'int')], [
    O('Attire status', 'text', PK('attire_status') + '&""'), O('Fitting date', 'date', PK('fitting_date')), O('Alteration weeks used', 'int', ALT),
    O('Latest fitting date that leaves time for alterations', 'date', LATEST), O('Last safe order date', 'date', LAST), O('Days left to order', 'int', LAST + '-{today}'),
    O('Days to move the fitting earlier', 'int', 'MAX(0,%s-%s)' % (PK('fitting_date'), LATEST)),
    O('Earliest open order date in the party', 'date', 'IFERROR(SMALL(%s,1),"")' % R('party', 'open_order_date')), O('Outfits not started', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (R('party', 'attire_status'), NS, R('party', 'party_id'))),
    O('Verdict', 'text', 'IF(%s<{today},%s&" "&({today}-(%s))&" "&%s,%s&" "&((%s)-{today})&" "&%s)' % (LAST, v('Late by'), LAST, v('days'), v('Order within'), LAST, v('days')))],
    GR('What if', ('As in the roster', {'ship': 21, 'margin': 7, 'alt': 0}), ('Shipping 14 days', {'ship': 14}), ('Shipping 42 days', {'ship': 42}), ('Margin 21 days', {'margin': 21}), ('Six weeks of alterations', {'alt': 6}))))

# 3 ------------------------------------------------------------ attire status tracker
ATC = lambda s_: 'COUNTIFS(%s,%s,%s,"<>")' % (R('party', 'attire_status'), s_, R('party', 'party_id'))
AFTER = 'COUNTIFS(%s,">=2")' % R('party', 'stage')
tools.append(TOOL('attire_tracker', 'Attire Status Tracker', 'How many outfits are not ordered yet',
    'Type the share of the party you want ordered or further; the tool counts the people at each status, the share ordered and how many are short of your target.', [
    I('target', 'Share you want ordered or further', 0.9, 'pct')], [
    O('Not started', 'int', ATC(NS)), O('Ordered', 'int', ATC(ORD)), O('Arrived', 'int', ATC(ARR)), O('Fitted', 'int', ATC(FITD)), O('Ready', 'int', ATC(READY)), O('People on the roster', 'int', PCOUNT),
    O('Share ordered or further', 'pct', 'IFERROR(%s/%s,0)' % (AFTER, PCOUNT)), O('People short of your target', 'int', 'MAX(0,ROUNDUP({in:target}*%s,0)-%s)' % (PCOUNT, AFTER)),
    O('Earliest open order date', 'date', 'IFERROR(SMALL(%s,1),"")' % R('party', 'open_order_date')),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s)' % (ATC(NS), v('All outfits ordered'), ATC(NS), v('outfits not ordered')))],
    GR('What if', ('Ninety percent', {'target': 0.9}), ('Half the party', {'target': 0.5}), ('Three quarters', {'target': 0.75}), ('Everyone', {'target': 1}), ('Two thirds', {'target': 0.67}))))

# 4 ------------------------------------------------------------ fitting calendar
FD = R('party', 'fitting_date')
tools.append(TOOL('fitting_calendar', 'Fitting Calendar', 'Do too many fittings fall on one day',
    'Type how many fittings your shop or tailor can do in a day; the tool counts the days with more people than that, names the first clash date and the next fitting.', [
    I('per_day', 'Fittings in one day', 2, 'int')], [
    O('Fittings still to come', 'int', 'COUNTIFS(%s,">="&{today},%s,"<>")' % (FD, R('party', 'party_id'))), O('Fittings done', 'int', 'COUNTIFS(%s,"<"&{today},%s,"<>")' % (FD, R('party', 'party_id'))),
    O('Next fitting in days', 'int', 'IFERROR(SMALL(%s,COUNTIFS(%s,"<"&{today})+1)-{today},"")' % (FD, FD)),
    O('Fittings in the next 30 days', 'int', 'COUNTIFS(%s,">="&{today},%s,"<="&({today}+30))' % (FD, FD)), O('Most people fitted on one day', 'int', 'MAX(%s)' % R('fits', 'same_day')),
    O('People on a day above your number', 'int', 'COUNTIFS(%s,">"&{in:per_day})' % R('fits', 'same_day')), O('Days above your number', 'int', 'ROUND(SUMIFS(%s,%s,">"&{in:per_day}),0)' % (R('fits', 'inv_day'), R('fits', 'same_day')), ),
    O('First clash date at the number in Settings', 'date', 'IFERROR(SMALL(%s,1),"")' % R('fits', 'clash_date')), O('Fittings too late for the alterations', 'int', 'COUNTIFS(%s,%s)' % (R('fits', 'fit_flag'), v('Too late'))),
    O('Verdict', 'text', 'IF(ROUND(SUMIFS(%s,%s,">"&{in:per_day}),0)=0,%s,%s&" "&ROUND(SUMIFS(%s,%s,">"&{in:per_day}),0)&" "&%s)' % (R('fits', 'inv_day'), R('fits', 'same_day'), v('Clear'), v('Clash on'), R('fits', 'inv_day'), R('fits', 'same_day'), v('days')))],
    GR('What if', ('Two a day', {'per_day': 2}), ('One a day', {'per_day': 1}), ('Three a day', {'per_day': 3}), ('Four a day', {'per_day': 4}), ('Five a day', {'per_day': 5}))))

# 5 ------------------------------------------------------------ who pays for outfits
PC = lambda p_: 'SUMIFS(%s,%s,%s)' % (R('party', 'outfit_cost'), R('party', 'paid_by'), tok('paidby', p_))
CP = '(%s+{in:extra})' % PC('Couple'); OT = '(%s+%s)' % (PC('Own'), PC('Parent'))
tools.append(TOOL('outfit_payers', 'Who Pays for Outfits', 'What do we pay for outfits and what do others pay',
    'Type an extra outfit the couple takes on and the most the couple wants to pay; the tool splits the outfit costs between the couple, the parents and the people themselves.', [
    I('extra', 'Extra outfit cost the couple takes on', 0), I('cap', 'Most the couple wants to pay', 800)], [
    O('Couple pays', 'money', CP), O('Parents pay', 'money', PC('Parent')), O('People pay for themselves', 'money', PC('Own')), O('All outfits', 'money', '%s+%s' % (CP, OT)),
    O('Share paid by the couple', 'pct', 'IFERROR(%s/(%s+%s),0)' % (CP, CP, OT)), O('People the couple pays for', 'int', 'COUNTIFS(%s,%s,%s,"<>")' % (R('party', 'paid_by'), COUPLE_PAYS, R('party', 'party_id'))),
    O('Room left under your limit', 'money', '{in:cap}-%s' % CP), O('Dearest single outfit', 'money', 'MAX(%s)' % R('party', 'outfit_cost')),
    O('Verdict', 'text', '%s&" "&ROUND(%s,0)&", "&%s&" "&ROUND(%s,0)' % (v('Couple pays'), CP, v('others pay'), OT))],
    GR('What if', ('As it is', {'extra': 0, 'cap': 800}), ('Add one outfit of 180', {'extra': 180}), ('Add two outfits of 180', {'extra': 360}), ('Limit of 500', {'cap': 500}), ('Limit of 1,200', {'cap': 1200}))))

# 6 ------------------------------------------------------------ run of show builder
IDLE = R('run', 'idle_before')
LGAP = 'MAX(0,MAX(%s))' % IDLE
LONGAT = 'INDEX(%s,MATCH(MAX(%s),%s,0))' % (R('run', 'start_m'), IDLE, IDLE)
NGAP = 'COUNTIFS(%s,">"&{in:min_gap})' % IDLE
tools.append(TOOL('run_builder', 'Run of Show Builder', 'Does the day run without idle gaps',
    'Type the idle minutes you accept; every step is checked against the steps before it, and the verdict says Fits or names the longest gap and the time it starts.', [
    I('min_gap', 'Idle minutes you accept', 10, 'int')], [
    O('Steps planned', 'int', 'COUNTIFS(%s,"<>")' % R('run', 'step_id')), O('Day starts at', 'text', 'IF(COUNT(%s)=0,"",%s)' % (R('run', 'start'), HMT(PLAN_START))), O('Plan ends at', 'text', 'IF(COUNT(%s)=0,"",%s)' % (R('run', 'start'), HMT(PLAN_END))),
    O('Minutes planned in all steps', 'int', 'SUM(%s)' % R('run', 'minutes')), O('Buffer minutes planned', 'int', 'SUM(%s)' % R('run', 'buffer_min')),
    O('Longest idle gap in minutes', 'int', LGAP), O('Steps with an idle gap above your number', 'int', NGAP),
    O('Steps still running when the next one starts', 'int', 'COUNTIFS(%s,"<0")' % R('run', 'gap_next')),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s&" "&%s&" "&%s)' % (NGAP, v('Fits'), v('Gap of'), LGAP, v('minutes at'), HMT(LONGAT)))],
    GR('What if', ('Accept 10 idle minutes', {'min_gap': 10}), ('Accept none', {'min_gap': 0}), ('Accept 5', {'min_gap': 5}), ('Accept 20', {'min_gap': 20}), ('Accept 60', {'min_gap': 60}))))

# 7 ------------------------------------------------------------ overrun check
OV = 'MAX(0,%s-%s-{in:extend}-{in:trim})' % (OVER_MIN, '0')
tools.append(TOOL('overrun_check', 'Run of Show Overrun Check', 'Does the day end before the venue closes',
    'Type minutes the venue lets you stay, minutes you cut from the end of the plan and the overtime rate; the tool compares the plan end with the closing time in Venue Hours and prices the overtime.', [
    I('extend', 'Minutes the venue lets you stay longer', 0, 'int'), I('trim', 'Minutes you cut from the end of the plan', 0, 'int'), I('rate', 'Overtime per hour, from your contract', 250)], [
    O('Plan ends at', 'text', HMT(PLAN_END)), O('Venue ends at', 'text', HMT(VEND_MIN)), O('Overrun now, minutes', 'int', OVER_MIN), O('Overrun after your changes, minutes', 'int', OV),
    O('Overtime hours after your changes', 'num', 'ROUND((%s)/60,2)' % OV), O('Overtime cost, pro rata', 'money', 'ROUND((%s)/60*{in:rate},0)' % OV), O('Overtime cost if each started hour is billed', 'money', 'ROUNDUP((%s)/60,0)*{in:rate}' % OV),
    O('Steps that end after the venue closes', 'int', 'COUNTIFS(%s,0)' % R('run', 'within')), O('Minutes to cut to finish on time', 'int', OV),
    O('Verdict', 'text', 'IF((%s)=0,%s,%s&" "&(%s)&" "&%s&" "&ROUND((%s)/60*{in:rate},0))' % (OV, v('Fits'), v('Over by'), OV, v('minutes, overtime cost'), OV))],
    GR('What if', ('As planned', {'extend': 0, 'trim': 0}), ('Venue lets you stay 30 more', {'extend': 30}), ('Cut 15 minutes', {'trim': 15}), ('Cut 30 minutes', {'trim': 30}), ('Overtime at 400 an hour', {'rate': 400}))))

# 8 ------------------------------------------------------------ travel time check
AH, AL = R('moves', 'allowed_h'), R('moves', 'allowed_l')
ADD = 'MAX(IF(COUNT(%s)=0,0,MAX(0,{in:hotel}-MIN(%s))),IF(COUNT(%s)=0,0,MAX(0,{in:load}-MIN(%s))))' % (AH, AH, AL, AL)
tools.append(TOOL('travel_check', 'Travel Time Check', 'Is there enough time to get from one place to the next',
    'Type the minutes by road between the hotel and the venue and the minutes to load a shuttle; every move in Moves is checked against the time the plan gives it.', [
    I('hotel', 'Minutes by road, hotel and venue', 25, 'int'), I('load', 'Minutes to load or leave a shuttle', 5, 'int')], [
    O('Moves checked', 'int', 'COUNTIFS(%s,"<>")' % R('moves', 'move_id')), O('Moves between different places', 'int', 'COUNTIFS(%s,">0")' % R('moves', 'kind')),
    O('Hotel and venue moves short of time', 'int', 'COUNTIFS(%s,"<"&{in:hotel})' % AH), O('Shuttle moves short of time', 'int', 'COUNTIFS(%s,"<"&{in:load})' % AL),
    O('Tightest hotel and venue move, minutes allowed', 'int', 'IF(COUNT(%s)=0,"",MIN(%s))' % (AH, AH)), O('Tightest shuttle move, minutes allowed', 'int', 'IF(COUNT(%s)=0,"",MIN(%s))' % (AL, AL)),
    O('Moves that overlap the next step', 'int', 'COUNTIFS(%s,"<0")' % R('moves', 'allowed')), O('Minutes to add', 'int', ADD),
    O('Verdict', 'text', 'IF(%s=0,%s,%s&" "&%s&" "&%s)' % (ADD, v('Enough'), v('Add'), ADD, v('minutes')))],
    GR('What if', ('As in Settings', {'hotel': 25, 'load': 5}), ('Hotel 40 minutes away', {'hotel': 40}), ('Hotel 15 minutes away', {'hotel': 15}), ('Shuttle load 10 minutes', {'load': 10}), ('Shuttle load 0', {'load': 0}))))

# 9 ------------------------------------------------------------ buffer planner
DEF = R('run', 'deficit')
TOPB = 'INDEX(%s,MATCH(MAX(%s),%s,0))&""' % (R('run', 'block'), DEF, DEF)
BUSYN = 'COUNTIFS(%s,%s,%s,%s)+COUNTIFS(%s,%s,%s,%s)' % (R('run', 'block'), TOPB, R('run', 'who'), W_VE, R('run', 'block'), TOPB, R('run', 'who'), W_AG)
tools.append(TOOL('buffer_planner', 'Buffer Planner', 'Where do we add buffer minutes first',
    'Type the buffer minutes you can add in all; blocks with many vendor and guest steps and little buffer come first, and the verdict names the block to add buffer to.', [
    I('extra', 'Buffer minutes you can add in all', 30, 'int')], [
    O('Buffer minutes planned', 'int', 'SUM(%s)' % R('run', 'buffer_min')), O('Buffer goal, minutes in all steps', 'int', 'SUM(%s)' % R('run', 'buffer_goal')),
    O('Share of the goal planned', 'pct', 'IFERROR(SUM(%s)/SUM(%s),0)' % (R('run', 'buffer_min'), R('run', 'buffer_goal'))), O('Block that needs the most buffer', 'text', TOPB),
    O('Buffer still to add in that block', 'int', 'MAX(0,MAX(%s))' % DEF), O('Vendor and guest steps in that block', 'int', BUSYN),
    O('Minutes added to each of those steps', 'num', 'IFERROR(ROUND(MIN({in:extra},MAX(0,MAX(%s)))/(%s),1),0)' % (DEF, BUSYN)), O('Still to add after your extra minutes', 'int', 'MAX(0,MAX(%s)-{in:extra})' % DEF),
    O('Steps with no buffer', 'int', 'COUNTIFS(%s,0,%s,"<>")' % (R('run', 'buffer_min'), R('run', 'step_id'))),
    O('Verdict', 'text', 'IF(MAX(%s)<=0,%s,%s&" "&%s)' % (DEF, v('Buffer is enough'), v('Add buffer to'), TOPB))],
    GR('What if', ('Add 30 minutes', {'extra': 30}), ('Add 10', {'extra': 10}), ('Add 20', {'extra': 20}), ('Add 60', {'extra': 60}), ('Add 90', {'extra': 90}))))

# 10 ----------------------------------------------------------- who needs to be where
T_ = '({in:hour}*60+{in:minute})'
ATT = 'IF(OR({in:who}=%s,{in:who}=%s,{in:who}=%s),0,1)' % (W_VE, W_OF, W_AG)
def COV(who): return '%s*(%s=%s)*(%s<=%s)*(%s>%s)' % (ID, '{range:run.who}', who, RS, T_, RE, T_)
S_OWN = 'SUMPRODUCT(MAX(%s*%s))' % (COV('{in:who}'), RS)
S_AG = '%s*SUMPRODUCT(MAX(%s*%s))' % (ATT, COV(W_AG), RS)
N_COV = 'SUMPRODUCT(%s)+%s*SUMPRODUCT(%s)' % (COV('{in:who}'), ATT, COV(W_AG))
BEST = 'MAX(%s,%s)' % (S_OWN, S_AG)
KEYM = 'MATCH(%s&"|"&IF(%s>=%s,{in:who},%s),%s,0)' % (BEST, S_OWN, S_AG, W_AG, R('run', 'key_who'))
def STEPC(c_, txt=True): return 'IFERROR(INDEX(%s,%s)%s,"")' % (R('run', c_), KEYM, '&""' if txt else '')
NEXTM = 'SUMPRODUCT(MIN(%s*(%s>%s)*%s+(1-%s*(%s>%s))*99999))' % ('(%s*((%s={in:who})+(%s=%s)*%s>0))' % (ID, '{range:run.who}', '{range:run.who}', W_AG, ATT), RS, T_, RS,
                                                               '(%s*((%s={in:who})+(%s=%s)*%s>0))' % (ID, '{range:run.who}', '{range:run.who}', W_AG, ATT), RS, T_)
tools.append(TOOL('who_where', 'Who Needs to Be Where', 'Where is a person or group at a chosen time',
    'Pick a person or group and type the hour and minute; the tool finds the step they are in at that time, the place, the person in charge and the next step.', [
    IL('who', 'Person or group', 'who', 'Wedding party'), I('hour', 'Hour, 24-hour clock', 15, 'int'), I('minute', 'Minute', 40, 'int')], [
    O('Time asked', 'text', HMT(T_)), O('Steps running at that time', 'int', N_COV), O('Doing', 'text', 'IF(%s=0,"",%s)' % (N_COV, STEPC('what'))), O('At', 'text', 'IF(%s=0,"",%s)' % (N_COV, STEPC('place'))),
    O('Step ends at', 'text', 'IF(%s=0,"",%s)' % (N_COV, HMT('%s+IFERROR(INDEX(%s,%s),0)' % (BEST, R('run', 'minutes'), KEYM)))), O('Person in charge', 'text', 'IF(%s=0,"",%s)' % (N_COV, STEPC('lead'))),
    O('Vendor there', 'text', 'IF(%s=0,"",%s)' % (N_COV, STEPC('vendor'))), O('Next step for them starts at', 'text', 'IF(%s>=99999,"",%s)' % (NEXTM, HMT(NEXTM))),
    O('Verdict', 'text', 'IF(%s=0,%s,{in:who}&" "&%s&" "&%s&" "&%s&" "&%s)' % (N_COV, v('Nothing planned at this time'), v('is at'), STEPC('place'), v('doing'), STEPC('what')))],
    GR('What if', ('Wedding party photos', {'hour': 15, 'minute': 40}), ('Hair and makeup', {'hour': 7, 'minute': 45}), ('Travel to the venue', {'hour': 14, 'minute': 40}), ('Dinner', {'hour': 18, 'minute': 45}), ('The last dance', {'hour': 23, 'minute': 5}))))

# 11 ----------------------------------------------------------- page per person
PG = lambda c_: R('pages', c_)
PN = 'COUNTIFS(%s,{in:who},%s,"<>")' % (PG('who'), PG('step_id'))
PNL = 'SUMIFS(%s,%s,{in:who})' % (PG('no_lead'), PG('who'))
tools.append(TOOL('page_person', 'Page per Person Check', 'Is the printed page of a person or group ready',
    'Pick a person or group; the tool counts the steps on their page, the first start, the last end, the places and the steps that still have no person in charge.', [
    IL('who', 'Person or group', 'who', 'Wedding party'), I('from_hour', 'Count the steps from this hour', 0, 'int')], [
    O('Steps on the page', 'int', PN), O('First start', 'text', IDX('pages', 'start', 'who', '{in:who}', True)),
    O('Last end', 'text', 'IFERROR(INDEX(%s,MATCH({in:who},%s,0)+%s-1)&"","")' % (PG('end'), PG('who'), PN)),
    O('Steps at the hotel', 'int', 'COUNTIFS(%s,{in:who},%s,%s)' % (PG('who'), PG('place'), PL_H)), O('Steps at the venue', 'int', 'COUNTIFS(%s,{in:who},%s,%s)' % (PG('who'), PG('place'), PL_V)),
    O('Steps in transport', 'int', 'COUNTIFS(%s,{in:who},%s,%s)' % (PG('who'), PG('place'), PL_T)), O('Steps from the hour you chose', 'int', 'COUNTIFS(%s,{in:who},%s,">="&({in:from_hour}*60))' % (PG('who'), PG('start_m'))),
    O('Steps without a person', 'int', PNL), O('Verdict', 'text', 'IF(%s=0,IF(%s=0,%s,%s),%s&" "&%s&" "&%s)' % (PNL, PN, v('Add steps to the page'), v('Page ready'), v('Add a person to'), PNL, v('steps')))],
    GR('What if', ('From the start', {'from_hour': 0}), ('From noon', {'from_hour': 12}), ('From 4 pm', {'from_hour': 16}), ('From 6 pm', {'from_hour': 18}), ('From 10 pm', {'from_hour': 22}))))

# 12 ----------------------------------------------------------- day-of contact list
DU = lambda c_: R('duties', c_)
PBL = 'IF({in:all}=1,%s,%s)' % (DU('problem'), DU('problem_core'))
def FIRSTM(col): return 'IFERROR(INDEX(%s,MATCH(1,%s,0)),IF({in:need_backup}=1,IFERROR(INDEX(%s,MATCH(2,%s,0)),""),""))' % (DU('duty'), col, DU('duty'), col)
MISS = 'IF({in:all}=1,COUNTIFS(%s,1)+{in:need_backup}*COUNTIFS(%s,2),COUNTIFS(%s,1)+{in:need_backup}*COUNTIFS(%s,2))' % (DU('problem'), DU('problem'), DU('problem_core'), DU('problem_core'))
FIRSTD = 'IF({in:all}=1,%s,%s)' % (FIRSTM(DU('problem')), FIRSTM(DU('problem_core')))
tools.append(TOOL('contact_list', 'Day-of Contact List', 'Does every day-of duty have a named person and a backup',
    'Type 1 to check every duty and 1 to require a backup; the tool checks that the gifts, the cards, the tip envelopes and the returns each have a named person with a phone, and names the first gap.', [
    I('all', 'Check every duty, 1 for yes, 0 for the four core duties', 0, 'int'), I('need_backup', 'Require a backup, 1 for yes', 1, 'int')], [
    O('Duties on the list', 'int', 'COUNTIFS(%s,"<>")' % DU('duty')), O('Core duties: gifts, cards, tips and returns', 'int', 'SUM(%s)' % DU('core')),
    O('Core duties with a named person and a phone', 'int', 'COUNTIFS(%s,1,%s,1)' % (DU('core'), DU('named_ok'))), O('Core duties with a backup and a phone', 'int', 'COUNTIFS(%s,1,%s,1)' % (DU('core'), DU('backup_ok'))),
    O('All duties without a named person', 'int', 'COUNTIFS(%s,0)' % DU('named_ok')), O('All duties without a backup', 'int', 'COUNTIFS(%s,0)' % DU('backup_ok')),
    O('Gaps in the duties you chose', 'int', MISS), O('First duty with a gap', 'text', 'IF((%s)="",%s,%s)' % (FIRSTD, v('None'), FIRSTD)),
    O('Verdict', 'text', 'IF((%s)=0,%s,%s&" "&(%s))' % (MISS, v('Complete'), v('Missing'), FIRSTD))],
    GR('What if', ('Four core duties', {'all': 0, 'need_backup': 1}), ('Every duty', {'all': 1}), ('Every duty, no backup needed', {'all': 1, 'need_backup': 0}), ('Core duties, no backup needed', {'all': 0, 'need_backup': 0}))))

# 13 ----------------------------------------------------------- vendor arrival and leave times
OS = lambda c_: R('onsite', c_)
LONGV = 'INDEX(%s,MATCH(MAX(%s),%s,0))&""' % (OS('vendor'), OS('hours'), OS('hours'))
tools.append(TOOL('vendor_times', 'Vendor Arrival and Leave Times', 'Who is on site the longest',
    'Type the hours that count as a long day for a vendor; the tool finds the first arrival, the last step to end and the vendor on site the longest.', [
    I('long_day', 'Hours that count as a long day', 8, 'num')], [
    O('Vendors on site', 'int', 'COUNTIFS(%s,">0")' % OS('steps')), O('First arrival', 'text', 'IF(COUNT(%s)=0,"",%s)' % (OS('arrives'), HMT('ROUND(MIN(%s)*1440,0)' % OS('arrives')))),
    O('Last step ends', 'text', 'IF(COUNT(%s)=0,"",%s)' % (OS('leaves'), HMT('ROUND(MAX(%s)*1440,0)' % OS('leaves')))), O('Longest on site, hours', 'num', 'MAX(%s)' % OS('hours')), O('Vendor on site the longest', 'text', LONGV),
    O('Vendors above your long day', 'int', 'COUNTIFS(%s,">"&{in:long_day})' % OS('hours')), O('Vendor hours in all', 'num', 'ROUND(SUM(%s),1)' % OS('hours')), O('Average hours on site', 'num', 'IFERROR(ROUND(AVERAGE(%s),1),0)' % OS('hours')),
    O('Vendors with no step on the day', 'int', 'COUNTIFS(%s,0)' % OS('steps')),
    O('Verdict', 'text', '%s&" "&%s&" "&ROUND(MAX(%s),1)&" "&%s' % (v('Longest on site'), LONGV, OS('hours'), v('hours')))],
    GR('What if', ('Eight hours', {'long_day': 8}), ('Four hours', {'long_day': 4}), ('Six hours', {'long_day': 6}), ('Ten hours', {'long_day': 10}), ('Twelve hours', {'long_day': 12}))))

# 14 ----------------------------------------------------------- tip hand-out plan
TP = lambda c_: R('tips', c_)
ENV = 'COUNTIFS(%s,">0")' % TP('planned')
def BYH(h): return 'COUNTIFS(%s,%s,%s,">0")' % (TP('handed_by'), tok('hander', h), TP('planned'))
tools.append(TOOL('tip_plan', 'Tip Hand-out Plan', 'Who hands out each tip envelope and are they ready',
    'Type an extra amount to add to every tip; the tool counts the envelopes, the ones not ready, the total and who hands them out. Tips are optional and vary by market.', [
    I('extra_each', 'Extra amount to add to each tip', 0)], [
    O('Envelopes with a tip', 'int', ENV), O('Envelopes ready', 'int', 'SUM(%s)' % TP('ready_n')), O('Envelopes not ready', 'int', 'SUM(%s)' % TP('notready_n')),
    O('Tips planned in all', 'money', 'SUM(%s)+{in:extra_each}*%s' % (TP('planned'), ENV)), O('Handed out by the day-of coordinator', 'int', BYH('Day-of coordinator')),
    O('Handed out by a friend or relative', 'int', BYH('Friend or relative')), O('Handed out by the wedding party lead', 'int', BYH('Wedding party lead')),
    O('Handed out by the couple or a parent', 'int', '%s+%s' % (BYH('Both partners'), BYH('Parent of partner 1'))), O('Largest tip', 'money', 'MAX(%s)+{in:extra_each}' % TP('planned')),
    O('Verdict', 'text', '%s&" "&%s&", "&SUM(%s)&" "&%s' % (ENV, v('envelopes'), TP('notready_n'), v('not ready')))],
    GR('What if', ('As planned', {'extra_each': 0}), ('Add 5 to each', {'extra_each': 5}), ('Add 10 to each', {'extra_each': 10}), ('Add 20 to each', {'extra_each': 20}), ('Take 10 off each', {'extra_each': -10}))))

# 15 ----------------------------------------------------------- late start impact
CERS = MSTART(C_(ABLK(B_CER)))
SLIDE = 'MAX(0,{in:delay}-MIN({in:delay},SUMIFS(%s,%s,">="&%s)))' % (R('run', 'buffer_min'), R('run', 'start_m'), CERS)
NEWOV = 'MAX(0,%s+%s-%s)' % (PLAN_END, SLIDE, VEND_MIN)
tools.append(TOOL('late_start', 'Late Start Impact', 'What happens if the ceremony starts late',
    'Type how many minutes late the ceremony starts; the buffer in the later steps absorbs some of it, the rest slides every later step, and the tool gives the new end time and the overtime.', [
    I('delay', 'Minutes the ceremony starts late', 45, 'int')], [
    O('Ceremony planned for', 'text', 'IF(%s>=99999,"",%s)' % (CERS, HMT(CERS))), O('Steps that slide', 'int', 'COUNTIFS(%s,">="&%s)' % (R('run', 'start_m'), CERS)),
    O('Buffer in those steps, minutes', 'int', 'SUMIFS(%s,%s,">="&%s)' % (R('run', 'buffer_min'), R('run', 'start_m'), CERS)), O('Delay the buffer absorbs', 'int', 'MIN({in:delay},SUMIFS(%s,%s,">="&%s))' % (R('run', 'buffer_min'), R('run', 'start_m'), CERS)),
    O('Slide of the end of the day, minutes', 'int', SLIDE), O('New plan end', 'text', HMT('%s+%s' % (PLAN_END, SLIDE))), O('Overrun against the venue, minutes', 'int', NEWOV),
    O('Overtime cost after the delay', 'money', 'ROUND((%s)/60*{set:overtime_rate},0)' % NEWOV), O('Extra overtime the delay causes', 'money', 'ROUND((%s)/60*{set:overtime_rate},0)-ROUND((%s)/60*{set:overtime_rate},0)' % (NEWOV, OVER_MIN)),
    O('Verdict', 'text', '%s&" "&%s&", "&%s&" "&ROUND((%s)/60*{set:overtime_rate},0)' % (v('Ends at'), HMT('%s+%s' % (PLAN_END, SLIDE)), v('overtime'), NEWOV))],
    GR('What if', ('45 minutes late', {'delay': 45}), ('On time', {'delay': 0}), ('10 minutes late', {'delay': 10}), ('30 minutes late', {'delay': 30}), ('60 minutes late', {'delay': 60}))))

# 16 ----------------------------------------------------------- sunset and light check
PHOEND = MEND(C_(ABLK(B_PHO))); CEREND = MEND(C_(ABLK(B_CER)))
LIGHT = '(ROUND({in:sunset}*60,0)-%s)' % PHOEND
tools.append(TOOL('light_check', 'Sunset and Light Check', 'Are the portraits taken in good light',
    'Type the sunset time for the wedding day (your own local value) and the minutes of good light you want after the last portrait; the tool compares them with the Photos block and the ceremony.', [
    I('sunset', 'Sunset, 24-hour clock, 20.75 is 20:45', 20.75, 'num'), I('margin', 'Minutes of good light you want after the last portrait', 45, 'int')], [
    O('Sunset at', 'text', HMT('ROUND({in:sunset}*60,0)')), O('First portrait starts at', 'text', HMS(C_(ABLK(B_PHO)))), O('Last portrait ends at', 'text', HME(C_(ABLK(B_PHO)))),
    O('Minutes of light after the last portrait', 'int', LIGHT), O('Ceremony ends at', 'text', HME(C_(ABLK(B_CER)))), O('Minutes of light after the ceremony', 'int', '(ROUND({in:sunset}*60,0)-%s)' % CEREND),
    O('Minutes you want after the last portrait', 'int', '{in:margin}'), O('Minutes to move the portraits earlier', 'int', 'MAX(0,{in:margin}-%s)' % LIGHT),
    O('Verdict', 'text', 'IF({in:margin}<=%s,%s,%s&" "&({in:margin}-%s)&" "&%s)' % (LIGHT, v('Portraits in light'), v('Move'), LIGHT, v('minutes earlier')))],
    GR('What if', ('Summer sunset 20:45', {'sunset': 20.75}), ('Sunset 19:00', {'sunset': 19}), ('Sunset 18:00', {'sunset': 18}), ('Winter sunset 17:15', {'sunset': 17.25}), ('Want 90 minutes of light', {'margin': 90}))))

# 17 ----------------------------------------------------------- party task load
LD = lambda c_: R('load', c_)
MOREN = 'ROUND(MAX(%s)-AVERAGE(%s),0)' % (LD('tasks'), LD('tasks'))
tools.append(TOOL('task_load', 'Party Task Load', 'Is the work shared evenly across the party',
    'Type how many tasks above the average count as too many; the tool compares every person with the average and names the person who holds the most.', [
    I('gap', 'Tasks above the average that count as too many', 2, 'int')], [
    O('Tasks in all', 'int', 'SUM(%s)' % LD('tasks')), O('Open tasks', 'int', 'SUM(%s)' % LD('open')), O('People with a task', 'int', 'COUNTIFS(%s,">0")' % LD('tasks')),
    O('Average tasks a person', 'num', 'IFERROR(ROUND(AVERAGE(%s),1),0)' % LD('tasks')), O('Most tasks held by one person', 'int', 'MAX(%s)' % LD('tasks')),
    O('Person with the most tasks', 'text', 'INDEX(%s,MATCH(MAX(%s),%s,0))&""' % (LD('person'), LD('tasks'), LD('tasks'))), O('Person with the most open tasks', 'text', 'INDEX(%s,MATCH(MAX(%s),%s,0))&""' % (LD('person'), LD('open'), LD('open'))),
    O('People above your number', 'int', 'COUNTIFS(%s,">="&{in:gap})' % LD('vs_avg')),
    O('Verdict', 'text', 'IF(MAX(%s)-AVERAGE(%s)<{in:gap},%s,INDEX(%s,MATCH(MAX(%s),%s,0))&" "&%s&" "&%s&" "&%s)' % (LD('tasks'), LD('tasks'), v('Even'), LD('person'), LD('tasks'), LD('tasks'), v('holds'), MOREN, v('more')))],
    GR('What if', ('Two above average', {'gap': 2}), ('Any difference', {'gap': 0}), ('One above', {'gap': 1}), ('Three above', {'gap': 3}), ('Five above', {'gap': 5}))))

# 18 ----------------------------------------------------------- emergency contact check
MISSALL = 'COUNTIFS(%s,"<>",%s,"")+{in:include_team}*COUNTIFS(%s,"<>",%s,"")+COUNTIFS(%s,0)+IF({set:meeting_point}="",1,0)' % (R('vendors', 'vendor_id'), R('vendors', 'phone'), R('team', 'team_id'), R('team', 'phone'), R('duties', 'named_ok'))
tools.append(TOOL('emergency_check', 'Emergency Contact Check', 'Can we reach every vendor and key person on the day',
    'Type 1 to include the team in the check; the tool counts the vendors, the team and the named duty people without a phone and checks that the meeting point is set.', [
    I('include_team', 'Include the team, 1 for yes', 1, 'int')], [
    O('Vendors on the sheet', 'int', 'COUNTIFS(%s,"<>")' % R('vendors', 'vendor_id')), O('Vendors with a phone', 'int', 'COUNTIFS(%s,"<>",%s,"<>")' % (R('vendors', 'vendor_id'), R('vendors', 'phone'))),
    O('Vendors without a phone', 'int', 'COUNTIFS(%s,"<>",%s,"")' % (R('vendors', 'vendor_id'), R('vendors', 'phone'))), O('Team members', 'int', 'COUNTIFS(%s,"<>")' % R('team', 'team_id')),
    O('Team members without a phone', 'int', 'COUNTIFS(%s,"<>",%s,"")' % (R('team', 'team_id'), R('team', 'phone'))), O('Duty people without a phone', 'int', 'COUNTIFS(%s,0)' % R('duties', 'named_ok')),
    O('Meeting point', 'text', '{set:meeting_point}&""'), O('Contacts missing in all', 'int', MISSALL),
    O('Verdict', 'text', 'IF((%s)=0,%s,%s&" "&(%s)&" "&%s)' % (MISSALL, v('Sheet complete'), v('Missing'), MISSALL, v('phones or the meeting point')))],
    GR('What if', ('Team included', {'include_team': 1}), ('Vendors only', {'include_team': 0}))))
assert len(tools) == 18, len(tools)
