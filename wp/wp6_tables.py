"""Wedding suite part 6: settings and the 20 tables with their calculated columns."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp6_lists import *
import wp6_data as D


def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)
def LKD(src, kc, my): return 'IFERROR(IF(INDEX({range:%s},MATCH({col:%s},{range:%s},0))=0,"",INDEX({range:%s},MATCH({col:%s},{range:%s},0))),"")' % (src, my, kc, src, my, kc)
def CA(key_, label, fmt, formula, w=12, **kw): return CALC(key_, label, fmt, formula, w, **kw)
def LIT(key_, label, phone): return CA(key_, label, 'text', '"%s"' % phone, 18)
def R(t, c_): return '{range:%s.%s}' % (t, c_)
def CPL(): return CA('couple', 'Couple', 'text', '{set:couple}', 20)
def HMT(m): return 'RIGHT("0"&INT((%s)/60),2)&":"&RIGHT("0"&MOD((%s),60),2)' % (m, m)


YES = '{list:yesno.yes}'
V = v
NS, ORD, ARR, FITD, READY = (tok('attire', s_) for s_ in ATTIRE_STATUS)
DONE = tok('tstatus', 'Done'); INPR = tok('tstatus', 'In progress')
W_CO, W_WP, W_PA, W_VE, W_OF, W_AG = (tok('who', s_) for s_ in ('Couple', 'Wedding party', 'Parents', 'Vendors', 'Officiant', 'All guests'))
B_PREP, B_CER, B_PHO, B_COC, B_DIN, B_DAN, B_CLO = (tok('block', s_) for s_ in RUN_BLOCKS)
PL_H, PL_V, PL_T = (tok('place', s_) for s_ in PLACES)
COUPLE_PAYS = tok('paidby', 'Couple')
VT = lambda n: tok('vname', n)
DT = lambda n: tok('duty', n)

# the run of show as arrays over the input columns (blank prepared rows are cut out by ID)
ID = '({range:run.step_id}<>"")'
RS = 'ROUND({range:run.start}*1440,0)'
RM = '{range:run.minutes}'
RE = '(%s+%s)' % (RS, RM)
VEND_MIN = 'ROUND(INDEX({range:hours.time},MATCH(%s,{range:hours.item},0))*1440,0)' % tok('hitem', 'Venue closes')
PLAN_END = 'SUMPRODUCT(MAX(%s*%s))' % (ID, RE)
PLAN_START = 'SUMPRODUCT(MIN(%s*%s+(1-%s)*99999))' % (ID, RS, ID)
OVER_MIN = 'MAX(0,%s-%s)' % (PLAN_END, VEND_MIN)


def MSTART(cond): return 'SUMPRODUCT(MIN(%s*%s+(1-%s)*99999))' % (cond, RS, cond)       # earliest start in minutes of the steps matching an array condition
def MEND(cond): return 'SUMPRODUCT(MAX(%s*%s))' % (cond, RE)
def MCNT(cond): return 'SUMPRODUCT(%s)' % cond
def HMS(cond): return 'IF(%s=0,"",%s)' % (MCNT(cond), HMT(MSTART(cond)))                # start of the first matching step as HH:MM text, blank when none
def HME(cond): return 'IF(%s=0,"",%s)' % (MCNT(cond), HMT(MEND(cond)))
def C_(*parts): return '(' + ID + ''.join('*(%s)' % p for p in parts) + ')'
def AWHO(g): return '({range:run.who}=%s)' % g
def ABLK(b): return '({range:run.block}=%s)' % b
def APLC(p): return '({range:run.place}=%s)' % p
def AVEN(n): return '({range:run.vendor}=%s)' % VT(n)
def RLK(c_, k): return 'INDEX({range:run.%s},MATCH({col:%s},{range:run.step_id},0))' % (c_, k)

settings = [
    S('couple', 'Your names as the couple', 'text', COUPLE),
    S('wedding_day', 'Wedding day', 'date', iso(WEDDING_DAY)),
    S('ship_days', 'Days an outfit takes to arrive, typical, edit', 'int', 21),
    S('margin_days', 'Safety margin in days before alterations end, your own', 'int', 7),
    S('order_warn_days', 'Days left that count as order soon, your own number', 'int', 30),
    S('fittings_per_day', 'Fittings your tailor can do in one day, typical, edit', 'int', 2),
    S('overtime_rate', 'Venue overtime per hour, from your contract, your own number', 'money', OVERTIME_RATE),
    S('hotel_venue_min', 'Minutes by road, hotel to venue, your own number', 'int', 25),
    S('load_min', 'Minutes to load or leave a shuttle, typical, edit', 'int', 5),
    S('buffer_target_min', 'Buffer minutes you want in each busy step, typical, edit', 'int', 5),
    S('gap_alert', 'Idle minutes that count as a gap, your own number', 'int', 10),
    S('load_gap', 'Tasks above the average that flag a person, your own number', 'int', 2),
    S('confirm_days', 'Days you give a person to confirm a task, your own number', 'int', 7),
    S('officiant_early_min', 'Minutes before the ceremony the officiant arrives', 'int', 40),
    S('late_min', 'Minutes late you plan for, your own number', 'int', 20),
    S('rehearsal_date', 'Rehearsal date', 'date', iso(dt.date.fromisoformat(D.REHEARSAL['date']))),
    S('rehearsal_start', 'Rehearsal start, 24-hour clock', 'text', '17:00'),
    S('meeting_point', 'Emergency meeting point on the day', 'text', 'The main entrance of the venue'),
]
assert 3 <= len(settings) <= 20

tables = []
# 1 wedding party ------------------------------------------------------------
tables.append(T('party', 'Wedding Party', 'Wedding Party', 'One row per person who stands with you or helps on the day: role, task, outfit status, cost, who pays and the fitting. The last safe order date, days left and where to be on the day fill in.', [
    C('party_id', 'Party ID', 'text', 9, required=True), LST('person', 'Person', 'person', 20), C('guest_id', 'Guest ID', 'text', 9), LST('side', 'Side', 'pside', 11), LST('role', 'Role', 'prole', 14),
    C('task', 'Task', 'text', 34), LST('attire_status', 'Attire status', 'attire', 13), C('outfit_cost', 'Outfit cost', 'money', 11), LST('paid_by', 'Paid by', 'paidby', 9), C('fitting_date', 'Fitting date', 'date', 11),
    C('alteration_weeks', 'Alteration weeks', 'int', 10), REF('arrive_step', 'Arrives at step', 'run.step_id', 11), C('phone', 'Phone', 'text', 18),
    CA('stage', 'Stage', 'int', 'IF({col:attire_status}=%s,1,IF({col:attire_status}=%s,2,IF({col:attire_status}=%s,3,IF({col:attire_status}=%s,4,5))))' % (NS, ORD, ARR, FITD), 7),
    CA('latest_fit', 'Latest fitting date', 'date', '{set:wedding_day}-{col:alteration_weeks}*7-{set:margin_days}', 12),
    CA('last_order_date', 'Last safe order date', 'date', 'IF({col:fitting_date}="","",MIN({col:fitting_date},{col:latest_fit})-{set:ship_days})', 12),
    CA('days_left', 'Days left to order', 'int', 'IF({col:last_order_date}="","",{col:last_order_date}-{today})', 9),
    CA('open_order_date', 'Open order date', 'date', 'IF({col:stage}=1,{col:last_order_date},"")', 12),
    CA('order_flag', 'Order flag', 'text', 'IF({col:stage}>=2,%s,IF({col:days_left}<0,%s,IF({col:days_left}<={set:order_warn_days},%s,%s)))' % (V('Ordered'), V('Late'), V('Order soon'), V('On time')), 11),
    CA('couple_cost', 'Cost paid by the couple', 'money', 'IF({col:paid_by}=%s,{col:outfit_cost},0)' % COUPLE_PAYS, 12),
    CA('gap_n', 'Missing items', 'int', '({col:role}="")+({col:task}="")+({col:attire_status}="")+({col:phone}="")', 8),
    CA('gap_item', 'First missing item', 'text', 'IF({col:role}="",%s,IF({col:task}="",%s,IF({col:attire_status}="",%s,IF({col:phone}="",%s,""))))' % (V('a role'), V('a task'), V('an outfit status'), V('a phone')), 14),
    CA('arrive_place', 'Arrives at, place', 'text', 'IFERROR(INDEX({range:run.place},MATCH({col:arrive_step},{range:run.step_id},0))&"","")', 11),
    CA('arrive_at', 'Arrives at, time', 'text', 'IFERROR(%s,"")' % HMT('ROUND(INDEX({range:run.start},MATCH({col:arrive_step},{range:run.step_id},0))*1440,0)'), 9),
    CA('confirm_by', 'Confirm by', 'date', '{today}+{set:confirm_days}', 11), CA('rehearsal_date', 'Rehearsal date', 'date', '{set:rehearsal_date}', 11), CA('rehearsal_start', 'Rehearsal start', 'text', '{set:rehearsal_start}', 9),
    CA('wedding_day', 'Wedding day', 'date', '{set:wedding_day}', 11), CPL()],
    D.party_d(), 50, [A('order_flag', '= ' + V('Late'), 'bad'), A('order_flag', '= ' + V('Order soon'), 'warn'), A('order_flag', '= ' + V('Ordered'), 'good')]))

# 2 team ---------------------------------------------------------------------
PARTYR = tok('role', 'Parent of partner 1'), tok('role', 'Parent of partner 2')
def TPH(k, label, role_tokens):
    cond = role_tokens[0] if len(role_tokens) == 1 else 'OR(%s)' % ','.join(role_tokens)
    cond = ('{col:role}=%s' % role_tokens[0]) if len(role_tokens) == 1 else 'OR(%s)' % ','.join('{col:role}=%s' % t for t in role_tokens)
    return CA(k, label, 'text', 'IF(%s,{col:phone},"")' % cond, 18)
PAR = C_(AWHO(W_PA), ABLK(B_PREP)); PARP = C_(AWHO(W_PA), ABLK(B_PHO)); TIPS = C_(AWHO(W_VE), ABLK(B_CLO))
GIFT_BACKUP = 'IFERROR(INDEX({range:duties.backup},MATCH(%s,{range:duties.duty},0))&"","")' % DT('Gifts table and gift log')
tables.append(T('team', 'Team', 'Team', 'The 16 people who run the wedding with you: partners, parents, siblings, party leads, a friend, the coordinator, vendor contacts and the officiant. Duties fill in.', [
    C('team_id', 'Team ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 22), LST('team', 'Team', 'team', 18), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 26),
    CA('duties', 'Day-of duties named', 'int', 'COUNTIFS({range:duties.named},{col:name})', 9), CA('steps_led', 'Steps led', 'int', 'COUNTIFS({range:run.lead},{col:name},{range:run.step_id},"<>")', 8),
    TPH('ph_par1', 'Phone, parent of partner 1', [PARTYR[0]]), TPH('ph_par2', 'Phone, parent of partner 2', [PARTYR[1]]), TPH('ph_parents', 'Phone, a parent', list(PARTYR)),
    TPH('ph_friend', 'Phone, close friend helper', [tok('role', 'Close friend helper')]), TPH('ph_coord', 'Phone, day-of coordinator', [tok('role', 'Day-of coordinator')]),
    CA('hm_place', 'Parents hair and makeup, place', 'text', 'IF(%s=0,"",INDEX({range:run.place},MATCH(%s&"|"&%s,{range:run.key_who},0))&"")' % (MCNT(PAR), MSTART(PAR), W_PA), 11),
    CA('hm_start', 'Parents hair and makeup, start', 'text', HMS(PAR), 9), CA('ph_place', 'Parents photos, place', 'text', 'IF(%s=0,"",INDEX({range:run.place},MATCH(%s&"|"&%s,{range:run.key_who},0))&"")' % (MCNT(PARP), MSTART(PARP), W_PA), 11),
    CA('ph_start', 'Parents photos, start', 'text', HMS(PARP), 9), CA('gifts_backup', 'Backup for gifts and cards', 'text', GIFT_BACKUP, 18), CA('tips_at', 'Tip envelopes handed out at', 'text', HMS(TIPS), 9),
    CA('steps', 'Run of show steps', 'int', 'COUNTIFS({range:run.step_id},"<>")', 8), CA('buffer', 'Buffer minutes planned', 'int', 'SUM({range:run.buffer_min})', 8),
    CA('plan_end_t', 'Plan ends at', 'text', 'IF(%s=0,"",%s)' % (PLAN_END, HMT(PLAN_END)), 9), CA('venue_end_t', 'Venue ends at', 'text', HMT(VEND_MIN), 9),
    CA('buffer_block', 'Block to add buffer to', 'text', 'IFERROR(INDEX({range:run.block},MATCH(MAX({range:run.deficit}),{range:run.deficit},0))&"","")', 14), CA('buffer_add', 'Buffer minutes to add', 'int', 'MAX(0,MAX({range:run.deficit}))', 8), CPL()],
    D.team_d(), 40))

# 3 run of show --------------------------------------------------------------
def NS_(c_): return c_
BUSY = '(COUNTIFS({range:run.block},{col:block},{range:run.who},%s)+COUNTIFS({range:run.block},{col:block},{range:run.who},%s))' % (W_VE, W_AG)
tables.append(T('run', 'Run of Show', 'Run of Show', 'The minute-by-minute plan, one row per step: start, minutes, buffer, block, who, place, vendor and the person who leads it. End time, gaps and overrun fill in.', [
    C('step_id', 'Step ID', 'text', 9, required=True), C('date', 'Date', 'date', 11), C('start', 'Start', 'time', 8), C('minutes', 'Minutes', 'int', 8), C('buffer_min', 'Buffer minutes', 'int', 9),
    LST('block', 'Block', 'block', 14), C('what', 'What happens', 'text', 44), LST('who', 'Who', 'who', 14), LST('place', 'Place', 'place', 10), LST('vendor', 'Vendor', 'vname', 18), LST('lead', 'Person in charge', 'helper', 16),
    CA('vendor_id', 'Vendor ID', 'text', 'IFERROR(INDEX({range:vendors.vendor_id},MATCH({col:vendor},{range:vendors.vendor},0))&"","")', 9),
    CA('end', 'End', 'time', '{col:start}+{col:minutes}/1440', 8),
    CA('start_m', 'Start in minutes', 'int', 'ROUND({col:start}*1440,0)', 9),
    CA('next_start', 'Next start', 'time', 'IF(SUMPRODUCT(%s*(%s>{col:start_m}))=0,"",SUMPRODUCT(MIN(%s*(%s>{col:start_m})*%s+(1-%s*(%s>{col:start_m}))*99999))/1440)' % (ID, RS, ID, RS, RS, ID, RS), 9),
    CA('gap_next', 'Gap to the next start, minutes', 'int', 'IF({col:next_start}="","",ROUND({col:next_start}*1440,0)-({col:start_m}+{col:minutes}))', 10),
    CA('idle_before', 'Idle minutes before this step', 'int', 'IF(SUMPRODUCT(%s*(%s<{col:start_m}))=0,"",{col:start_m}-SUMPRODUCT(MAX(%s*(%s<{col:start_m})*%s)))' % (ID, RS, ID, RS, RE), 10),
    CA('within', 'Within venue hours', 'int', 'IF({col:start_m}+{col:minutes}<=%s,1,0)' % VEND_MIN, 8), CA('late_min', 'Minutes after the venue closes', 'int', 'MAX(0,{col:start_m}+{col:minutes}-%s)' % VEND_MIN, 9),
    CA('lead_set', 'Has a person', 'int', 'IF({col:lead}="",0,1)', 7), CA('deficit', 'Buffer still to add in the block', 'int', '%s*{set:buffer_target_min}-SUMIFS({range:run.buffer_min},{range:run.block},{col:block})' % BUSY, 10),
    CA('buffer_goal', 'Buffer goal', 'int', '{set:buffer_target_min}', 7),
    CA('key_who', 'Key start and who', 'text', '{col:start_m}&"|"&{col:who}', 14), CA('key_vendor', 'Key start and vendor', 'text', 'IF({col:vendor}="","",{col:start_m}&"|"&{col:vendor})', 14),
    CA('plan_end_t', 'Plan ends at', 'text', HMT(PLAN_END), 9), CA('venue_end_t', 'Venue ends at', 'text', HMT(VEND_MIN), 9), CA('first_start_t', 'Day starts at', 'text', HMT(PLAN_START), 9),
    CA('over_min', 'Plan overrun, minutes', 'int', OVER_MIN, 9), CA('overtime_cost', 'Overtime cost estimate', 'money', 'ROUND(%s/60*{set:overtime_rate},0)' % OVER_MIN, 11),
    CA('no_person', 'Steps with no person', 'int', 'COUNTIFS({range:run.step_id},"<>",{range:run.lead},"")', 9), CA('partner_phone', 'Partner phone', 'text', '"%s"' % D.TEAM['WP-02']['phone'], 18),
    CA('wedding_day', 'Wedding day', 'date', '{set:wedding_day}', 11), CPL()],
    D.run_d(), 60, [A('late_min', '> 0', 'bad'), A('idle_before', '> {set:gap_alert}', 'warn'), A('lead_set', '= 0', 'warn')]))

# 4 vendors ------------------------------------------------------------------
def VPH(k, label, name): return CA(k, label, 'text', 'IF({col:vendor}=%s,{col:phone},"")' % VT(name), 18)
PHOTO = C_(ABLK(B_PHO), AVEN('Photographer')); FAMILY = C_(ABLK(B_PHO), AWHO(W_PA)); VENUEIN = C_(AWHO(W_VE), APLC(PL_V))
BAND_C = C_(AVEN('Band or DJ'), ABLK(B_COC)); BAND_ALL = C_(AVEN('Band or DJ')); BAND_D = C_(AVEN('Band or DJ'), ABLK(B_DIN))
CERE = C_(ABLK(B_CER), AWHO(W_OF)); TRANS = C_(AVEN('Transport'))
DINNER_MAX = 'SUMPRODUCT(MAX(%s*%s))' % (C_(ABLK(B_DIN), AVEN('Caterer')), RM)
DINNER_C = C_(ABLK(B_DIN), AVEN('Caterer'), '(%s=%s)' % (RM, DINNER_MAX))
tables.append(T('vendors', 'Vendors', 'Vendors', 'The vendors on site on the day, with the contact, phone and what each does. Steps, key times and the texts to each vendor fill in.', [
    C('vendor_id', 'Vendor ID', 'text', 9, required=True), LST('vendor', 'Vendor', 'vname', 20), C('category', 'Category', 'text', 24), C('contact', 'Contact', 'text', 22), C('phone', 'Phone', 'text', 18), C('day_role', 'Role on the day', 'text', 36),
    CA('steps', 'Steps on the day', 'int', 'COUNTIFS({range:run.vendor},{col:vendor},{range:run.step_id},"<>")', 8),
    VPH('ph_venue', 'Venue phone', 'Venue'), VPH('ph_photog', 'Photographer phone', 'Photographer'), VPH('ph_band', 'Band or DJ phone', 'Band or DJ'), VPH('ph_caterer', 'Caterer phone', 'Caterer'),
    VPH('ph_officiant', 'Officiant phone', 'Officiant'), VPH('ph_hotel', 'Hotel phone', 'Hotel room block'),
    CA('plan_end_t', 'Plan ends at', 'text', 'IF(%s=0,"",%s)' % (PLAN_END, HMT(PLAN_END)), 9), CA('venue_end_t', 'Venue ends at', 'text', HMT(VEND_MIN), 9), CA('vendors_in', 'Vendors arrive at the venue from', 'text', HMS(VENUEIN), 9),
    CA('portrait_start', 'Portraits start', 'text', HMS(PHOTO), 9), CA('portrait_place', 'Portraits place', 'text', 'IF(%s=0,"",INDEX({range:run.place},MATCH(%s&"|"&%s,{range:run.key_vendor},0))&"")' % (MCNT(PHOTO), MSTART(PHOTO), VT('Photographer')), 10),
    CA('family_start', 'Family photos start', 'text', HMS(FAMILY), 9), CA('family_place', 'Family photos place', 'text', 'IF(%s=0,"",INDEX({range:run.place},MATCH(%s&"|"&%s,{range:run.key_who},0))&"")' % (MCNT(FAMILY), MSTART(FAMILY), W_PA), 10),
    CA('band_start', 'Band set starts', 'text', HMS(BAND_C), 9), CA('band_end', 'Band set ends', 'text', HME(BAND_ALL), 9), CA('band_break', 'Band dinner break', 'text', HMS(BAND_D), 9),
    CA('dinner_start', 'Dinner service starts', 'text', HMS(DINNER_C), 9), CA('ceremony_start', 'Ceremony starts', 'text', HMS(CERE), 9),
    CA('ceremony_min', 'Ceremony minutes', 'int', 'IF(%s=0,0,SUMPRODUCT(MAX(%s*%s)))' % (MCNT(CERE), CERE, RM), 8),
    CA('officiant_arrive', 'Officiant arrives at', 'text', 'IF(%s=0,"",%s)' % (MCNT(CERE), HMT('%s-{set:officiant_early_min}' % MSTART(CERE))), 9),
    CA('shuttle_at', 'Last shuttle pick-up', 'text', 'IF(%s=0,"",%s)' % (MCNT(TRANS), HMT('SUMPRODUCT(MAX(%s*%s))' % (TRANS, RS))), 9),
    CA('wedding_day', 'Wedding day', 'date', '{set:wedding_day}', 11), CPL()],
    D.vendors_d(), 40))

# 5 venue hours --------------------------------------------------------------
tables.append(T('hours', 'Venue Hours', 'Venue Hours', 'The hours your venue allows, from your contract: when vendors and guests may enter, when the bar and the music stop and when the venue closes. The run of show is checked against Venue closes.', [
    LST('item', 'Item', 'hitem', 22, required=True), C('time', 'Time', 'time', 9), C('note', 'Note', 'text', 44)], D.hours_d(), 20))

# 6 moves between places -----------------------------------------------------
tables.append(T('moves', 'Moves', 'Moves Between Places', 'One row per move of a person or a vendor from one step to another: the minutes allowed, the minutes you need between those places and a flag. Travel times are in Settings.', [
    C('move_id', 'Move ID', 'text', 9, required=True), REF('from_step', 'From step', 'run.step_id', 9), REF('to_step', 'To step', 'run.step_id', 9),
    CA('who', 'Who', 'text', RLK('who', 'from_step') + '&""', 13), CA('from_place', 'From place', 'text', RLK('place', 'from_step') + '&""', 10), CA('to_place', 'To place', 'text', RLK('place', 'to_step') + '&""', 10),
    CA('from_end', 'Leaves at', 'time', RLK('start', 'from_step') + '+' + RLK('minutes', 'from_step') + '/1440', 8), CA('to_start', 'Must be there at', 'time', RLK('start', 'to_step'), 8),
    CA('allowed', 'Minutes allowed', 'int', 'ROUND(%s*1440,0)-(ROUND(%s*1440,0)+%s)+%s' % (RLK('start', 'to_step'), RLK('start', 'from_step'), RLK('minutes', 'from_step'), RLK('buffer_min', 'from_step')), 9),
    CA('kind', 'Kind of move', 'int', 'IF({col:from_place}={col:to_place},0,IF(OR({col:from_place}=%s,{col:to_place}=%s),1,2))' % (PL_T, PL_T), 7),
    CA('needed', 'Minutes needed', 'int', 'IF({col:kind}=0,0,IF({col:kind}=1,{set:load_min},{set:hotel_venue_min}))', 9),
    CA('allowed_h', 'Allowed, hotel and venue', 'int', 'IF({col:kind}=2,{col:allowed},"")', 9), CA('allowed_l', 'Allowed, shuttle', 'int', 'IF({col:kind}=1,{col:allowed},"")', 9),
    CA('short', 'Minutes short', 'int', 'MAX(0,{col:needed}-{col:allowed})', 8),
    CA('flag', 'Flag', 'text', 'IF({col:allowed}<0,%s,IF({col:short}>0,%s,%s))' % (V('Overlap'), V('Add time'), V('Enough')), 10)],
    D.moves_d(), 40, [A('flag', '= ' + V('Add time'), 'warn'), A('flag', '= ' + V('Overlap'), 'bad'), A('flag', '= ' + V('Enough'), 'good')]))

# 7 who and where ------------------------------------------------------------
def MW(): return C_('({range:run.block}={col:block})', '(%s+%s*IF(OR({col:who}=%s,{col:who}=%s,{col:who}=%s),0,1))>0' % (AWHO('{col:who}'), AWHO(W_AG), W_VE, W_OF, W_AG))
MWH = MW()
def MWP(p): return 'SUMPRODUCT(%s*%s)' % (MWH, APLC(p))
tables.append(T('where', 'Who and Where', 'Who and Where', 'The who-needs-to-be-where matrix: one row per person or group and block, with the steps, the first start, the last end and the place.', [
    C('where_id', 'Row ID', 'text', 8, required=True), LST('who', 'Person or group', 'who', 14), LST('block', 'Block', 'block', 14),
    CA('steps', 'Steps', 'int', MCNT(MWH), 7), CA('first_start', 'First start', 'text', HMS(MWH), 9), CA('last_end', 'Last end', 'text', HME(MWH), 9),
    CA('place', 'Place', 'text', 'IF({col:steps}=0,"",IF(%s={col:steps},%s,IF(%s={col:steps},%s,IF(%s={col:steps},%s,%s))))' % (MWP(PL_V), PL_V, MWP(PL_H), PL_H, MWP(PL_T), PL_T, V('Several places')), 14)],
    D.where_d(), 40))

# 8 page per person ----------------------------------------------------------
PL = lambda c_: 'IFERROR(INDEX({range:run.%s},MATCH({col:step_id},{range:run.step_id},0))&"","")' % c_
tables.append(T('pages', 'Page per Person', 'Page per Person', 'The steps on the printed page of each person or group. Add a row to put a step on a page; times, place and the person in charge fill in.', [
    C('page_id', 'Page row', 'text', 8, required=True), LST('who', 'Person or group', 'who', 14), REF('step_id', 'Step', 'run.step_id', 9),
    CA('start', 'Start', 'text', 'IFERROR(%s,"")' % HMT('ROUND(INDEX({range:run.start},MATCH({col:step_id},{range:run.step_id},0))*1440,0)'), 8),
    CA('end', 'End', 'text', 'IFERROR(%s,"")' % HMT('ROUND(INDEX({range:run.start},MATCH({col:step_id},{range:run.step_id},0))*1440,0)+INDEX({range:run.minutes},MATCH({col:step_id},{range:run.step_id},0))'), 8),
    CA('what', 'What', 'text', PL('what'), 44), CA('place', 'Place', 'text', PL('place'), 10), CA('block', 'Block', 'text', PL('block'), 13),
    CA('lead', 'Person in charge', 'text', PL('lead'), 16),
    CA('start_m', 'Start in minutes', 'int', 'IFERROR(ROUND(INDEX({range:run.start},MATCH({col:step_id},{range:run.step_id},0))*1440,0),"")', 8),
    CA('with_whom', 'With whom', 'text', 'IFERROR(IF(INDEX({range:run.vendor},MATCH({col:step_id},{range:run.step_id},0))<>"",INDEX({range:vendors.contact},MATCH(INDEX({range:run.vendor},MATCH({col:step_id},{range:run.step_id},0)),{range:vendors.vendor},0)),{col:lead}),"")', 20),
    CA('no_lead', 'No person yet', 'int', 'IF({col:lead}="",1,0)', 7)],
    D.pages_d(), 100, [A('no_lead', '= 1', 'warn')]))

# 9 day-of duties ------------------------------------------------------------
CORE = ','.join('{col:duty}=%s' % DT(n) for n in ('Gifts table and gift log', 'Cards and card box', 'Tip envelopes', 'Rentals and returns'))
tables.append(T('duties', 'Day-of Duties', 'Day-of Duties', 'One row per job on the day that needs a named person: gifts, cards, tip envelopes, returns and more, with a backup and the phones. Missing names and backups are flagged.', [
    LST('duty', 'Duty', 'duty', 26, required=True), LST('named', 'Named person', 'helper', 16), LST('backup', 'Backup', 'helper', 16), LST('status', 'Briefed', 'tstatus', 11),
    CA('phone', 'Phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH({col:named},{range:team.name},0))&"","")', 18),
    CA('backup_phone', 'Backup phone', 'text', 'IFERROR(INDEX({range:team.phone},MATCH({col:backup},{range:team.name},0))&"","")', 18),
    CA('core', 'Gifts, cards, tips or returns', 'int', 'IF(OR(%s),1,0)' % CORE, 9), CA('named_ok', 'Named with a phone', 'int', 'IF(AND({col:named}<>"",{col:phone}<>""),1,0)', 9),
    CA('backup_ok', 'Backup with a phone', 'int', 'IF(AND({col:backup}<>"",{col:backup_phone}<>""),1,0)', 9),
    CA('problem', 'Gap', 'int', 'IF({col:named_ok}=0,1,IF({col:backup_ok}=0,2,0))', 6), CA('problem_core', 'Gap in a core duty', 'int', '{col:problem}*{col:core}', 8)],
    D.duties_d(), 30, [A('problem', '= 1', 'bad'), A('problem', '= 2', 'warn')]))

# 10 attire by status --------------------------------------------------------
tables.append(T('attire_s', 'Attire by Status', 'Attire by Status', 'One row per attire status: how many people and what their outfits cost, from the Wedding Party sheet.', [
    LST('status', 'Status', 'attire', 14, required=True), CA('people', 'People', 'int', 'COUNTIFS({range:party.attire_status},{col:status},{range:party.party_id},"<>")', 8),
    CA('cost', 'Outfit cost', 'money', 'SUMIFS({range:party.outfit_cost},{range:party.attire_status},{col:status})', 11)], D.attire_s_d(), 10))

# 11 fitting plan ------------------------------------------------------------
PNL = lambda c_: LKD('party.%s' % c_, 'party.person', 'person')
LEADN = D.TEAM['WP-07'];
tables.append(T('fits', 'Fitting Plan', 'Fitting Plan', 'One row per person: the fitting date, the last safe order date, the latest fitting that leaves time for alterations and a flag for a clash or a late fitting. The wedding party lead texts fill in.', [
    LST('person', 'Person', 'person', 20, required=True), CA('fitting_date', 'Fitting date', 'date', PNL('fitting_date'), 11), CA('last_order_date', 'Last safe order date', 'date', PNL('last_order_date'), 12),
    CA('latest_fit', 'Latest fitting date', 'date', PNL('latest_fit'), 12), CA('status', 'Attire status', 'text', LKT('party.attire_status', 'party.person', 'person'), 13),
    CA('days_to_fit', 'Days to the fitting', 'int', 'IF({col:fitting_date}="","",{col:fitting_date}-{today})', 9), CA('same_day', 'People fitted that day', 'int', 'IF({col:fitting_date}="","",COUNTIFS({range:party.fitting_date},{col:fitting_date},{range:party.party_id},"<>"))', 9),
    CA('fit_flag', 'Flag', 'text', 'IF({col:fitting_date}="",%s,IF({col:fitting_date}<{today},%s,IF({col:fitting_date}>{col:latest_fit},%s,IF({col:same_day}>{set:fittings_per_day},%s,%s))))' % (V('No date'), V('Past'), V('Too late'), V('Clash'), V('Clear')), 10),
    CA('late_n', 'Clash or late', 'int', 'IF(OR({col:fit_flag}=%s,{col:fit_flag}=%s),1,0)' % (V('Clash'), V('Too late')), 7),
    CA('inv_day', 'One over people that day', 'num', 'IF({col:fitting_date}="","",1/{col:same_day})', 8), CA('clash_date', 'Clash date', 'date', 'IF({col:fit_flag}=%s,{col:fitting_date},"")' % V('Clash'), 11),
    CA('lead_name', 'Wedding party lead', 'text', 'IFERROR(INDEX({range:team.name},MATCH(%s,{range:team.role},0)),"")' % tok('role', 'Wedding party lead 1'), 12), LIT('lead_phone', 'Lead phone', LEADN['phone']),
    CA('not_ordered', 'Outfits not ordered', 'int', 'COUNTIFS({range:party.attire_status},%s,{range:party.party_id},"<>")' % NS, 9),
    CA('party_start', 'Wedding party starts at', 'text', HMS(C_(AWHO(W_WP))), 9), CA('party_place', 'Wedding party starts at, place', 'text', 'IF(%s=0,"",INDEX({range:run.place},MATCH(%s&"|"&%s,{range:run.key_who},0))&"")' % (MCNT(C_(AWHO(W_WP))), MSTART(C_(AWHO(W_WP))), W_WP), 10),
    CA('programs_at', 'Programs handed out at', 'text', HMS(C_(AWHO(W_WP), ABLK(B_PREP), APLC(PL_V))), 9), CA('wedding_day', 'Wedding day', 'date', '{set:wedding_day}', 11), CPL()],
    D.fits_d(), 30, [A('fit_flag', '= ' + V('Clash'), 'warn'), A('fit_flag', '= ' + V('Too late'), 'bad'), A('fit_flag', '= ' + V('Past'), 'good')]))

# 12 party tasks -------------------------------------------------------------
tables.append(T('ptasks', 'Party Tasks', 'Party Tasks', 'One row per task of a person in the wedding party: the task, the due date and the status. Days left, a flag and the phone fill in.', [
    C('task_id', 'Task ID', 'text', 8, required=True), LST('person', 'Person', 'person', 20), C('task', 'Task', 'text', 36), C('due_date', 'Due date', 'date', 11), LST('status', 'Status', 'tstatus', 11),
    CA('days_left', 'Days left', 'int', 'IF({col:status}=%s,"",{col:due_date}-{today})' % DONE, 8),
    CA('flag', 'Flag', 'text', 'IF({col:status}=%s,%s,IF({col:due_date}<{today},%s,IF({col:due_date}-{today}<=30,%s,%s)))' % (DONE, V('Done'), V('Late'), V('Due soon'), V('On time')), 10),
    CA('phone', 'Phone', 'text', LKT('party.phone', 'party.person', 'person'), 18)],
    D.ptasks_d(), 60, [A('flag', '= ' + V('Late'), 'bad'), A('flag', '= ' + V('Due soon'), 'warn'), A('flag', '= ' + V('Done'), 'good')]))

# 13 party workload ----------------------------------------------------------
tables.append(T('load', 'Party Workload', 'Party Workload', 'One row per person: how many tasks they hold, how many are open, their share of the open tasks and how far they are from the average.', [
    LST('person', 'Person', 'person', 20, required=True), CA('tasks', 'Tasks', 'int', 'COUNTIFS({range:ptasks.person},{col:person},{range:ptasks.task_id},"<>")', 8),
    CA('open', 'Open tasks', 'int', 'COUNTIFS({range:ptasks.person},{col:person},{range:ptasks.status},"<>"&%s,{range:ptasks.task_id},"<>")' % DONE, 8),
    CA('share', 'Share of open tasks', 'pct', 'IF(SUM({range:load.open})=0,0,{col:open}/SUM({range:load.open}))', 9), CA('vs_avg', 'Tasks above the average', 'num', 'ROUND({col:tasks}-AVERAGE({range:load.tasks}),1)', 9)],
    D.load_d(), 30, [A('vs_avg', '>= {set:load_gap}', 'warn')]))

# 14 block timing ------------------------------------------------------------
tables.append(T('blocks', 'Block Timing', 'Block Timing', 'One row per block of the day: the planned minutes of its steps and its share of the day.', [
    LST('block', 'Block', 'block', 14, required=True), CA('minutes', 'Planned minutes', 'int', 'SUMIFS({range:run.minutes},{range:run.block},{col:block})', 10),
    CA('share', 'Share of the day', 'pct', 'IF(SUM({range:run.minutes})=0,0,{col:minutes}/SUM({range:run.minutes}))', 10)], D.blocks_d(), 15))

# 15 overrun by block --------------------------------------------------------
BM = '(%s*(%s={col:block}))' % (ID, '{range:run.block}')
tables.append(T('overrun', 'Overrun by Block', 'Overrun by Block', 'One row per block: when its last step ends and how many minutes that is past the closing time in Venue Hours.', [
    LST('block', 'Block', 'block', 14, required=True),
    CA('planned_end', 'Planned end', 'text', 'IF(COUNTIFS({range:run.block},{col:block},{range:run.step_id},"<>")=0,"",%s)' % HMT('SUMPRODUCT(MAX(%s*%s))' % (BM, RE)), 10),
    CA('overrun', 'Overrun minutes', 'int', 'IF(COUNTIFS({range:run.block},{col:block},{range:run.step_id},"<>")=0,0,MAX(0,SUMPRODUCT(MAX(%s*%s))-%s))' % (BM, RE, VEND_MIN), 10)], D.overrun_d(), 15,
    [A('overrun', '> 0', 'bad')]))

# 16 vendor on-site times ----------------------------------------------------
MV = '(%s*(%s={col:vendor}))' % (ID, '{range:run.vendor}')
tables.append(T('onsite', 'Vendor On-site', 'Vendor On-site Times', 'One row per vendor: when they arrive, when their last step ends, the hours on site and their first place. The texts to the hair and makeup artist and the transport vendor fill in.', [
    LST('vendor', 'Vendor', 'vname', 20, required=True), CA('steps', 'Steps', 'int', 'COUNTIFS({range:run.vendor},{col:vendor},{range:run.step_id},"<>")', 7),
    CA('arrives', 'Arrives', 'time', 'IF({col:steps}=0,"",SUMPRODUCT(MIN(%s*%s+(1-%s)*99999))/1440)' % (MV, RS, MV), 8), CA('leaves', 'Last step ends', 'time', 'IF({col:steps}=0,"",SUMPRODUCT(MAX(%s*%s))/1440)' % (MV, RE), 9),
    CA('hours', 'Hours on site', 'hours', 'IF({col:steps}=0,"",ROUND(({col:leaves}-{col:arrives})*24,2))', 9),
    CA('arrives_t', 'Arrives at', 'text', 'IF({col:steps}=0,"",%s)' % HMT('ROUND({col:arrives}*1440,0)'), 8),
    CA('last_start', 'Last step starts at', 'text', 'IF({col:steps}=0,"",%s)' % HMT('SUMPRODUCT(MAX(%s*%s))' % (MV, RS)), 9),
    CA('first_place', 'First place', 'text', 'IF({col:steps}=0,"",IFERROR(INDEX({range:run.place},MATCH(ROUND({col:arrives}*1440,0)&"|"&{col:vendor},{range:run.key_vendor},0))&"",""))', 10),
    CA('phone', 'Phone', 'text', LKT('vendors.phone', 'vendors.vendor', 'vendor'), 18), CA('contact', 'Contact', 'text', LKT('vendors.contact', 'vendors.vendor', 'vendor'), 20), VPH('ph_hair', 'Hair and makeup phone', 'Hair and makeup'), VPH('ph_transport', 'Transport phone', 'Transport'),
    CA('wedding_day', 'Wedding day', 'date', '{set:wedding_day}', 11), CPL()], D.onsite_d(), 30))

# 17 outfit costs by payer ---------------------------------------------------
tables.append(T('paycost', 'Outfit Cost by Payer', 'Outfit Costs by Payer', 'One row per payer: how many outfits and what they cost, from the Wedding Party sheet.', [
    LST('paid_by', 'Paid by', 'paidby', 12, required=True), CA('people', 'People', 'int', 'COUNTIFS({range:party.paid_by},{col:paid_by},{range:party.party_id},"<>")', 8),
    CA('cost', 'Outfit cost', 'money', 'SUMIFS({range:party.outfit_cost},{range:party.paid_by},{col:paid_by})', 11)], D.paycost_d(), 10))

# 18 roles summary -----------------------------------------------------------
tables.append(T('roles', 'Roles Summary', 'Roles Summary', 'One row per role: how many people hold it and its share of the party. Role names are labels you can edit.', [
    LST('role', 'Role', 'prole', 16, required=True), CA('people', 'People', 'int', 'COUNTIFS({range:party.role},{col:role},{range:party.party_id},"<>")', 8),
    CA('share', 'Share', 'pct', 'IF(COUNTIFS({range:party.party_id},"<>")=0,0,{col:people}/COUNTIFS({range:party.party_id},"<>"))', 9)], D.roles_d(), 10))

# 19 tips handed out ---------------------------------------------------------
tables.append(T('tips', 'Tips Handed Out', 'Tips Handed Out', 'One row per vendor: the tip you plan, who hands the envelope, whether it is ready and when the vendor is done on the day. Tips are optional and vary by market.', [
    LST('vendor', 'Vendor', 'vname', 20, required=True), LST('handed_by', 'Who hands it', 'hander', 18), C('planned', 'Planned tip', 'money', 11), C('envelope_ready', 'Envelope ready', 'bool', 9),
    CA('hand_at', 'Hand out at', 'text', 'IFERROR(IF(INDEX({range:onsite.steps},MATCH({col:vendor},{range:onsite.vendor},0))=0,%s,%s),"")' % (V('After the day'), HMT('ROUND(INDEX({range:onsite.leaves},MATCH({col:vendor},{range:onsite.vendor},0))*1440,0)')), 12),
    CA('ready_n', 'Ready', 'int', 'IF(AND({col:planned}>0,{col:envelope_ready}=%s),1,0)' % YES, 6), CA('notready_n', 'Not ready', 'int', 'IF(AND({col:planned}>0,{col:envelope_ready}<>%s),1,0)' % YES, 7)],
    D.tips_d(), 30, [A('notready_n', '= 1', 'warn')]))

# 20 guest timeline ----------------------------------------------------------
tables.append(T('gtl', 'Guest Timeline', 'Day-of Timeline for Guests', 'What guests do and when, taken from the run of show: add a step to show it to guests, remove one to keep it private. Share this page with the guests or put it on the welcome sign.', [
    REF('step_id', 'Step', 'run.step_id', 9, required=True), CA('time', 'Time', 'text', 'IFERROR(%s,"")' % HMT('ROUND(INDEX({range:run.start},MATCH({col:step_id},{range:run.step_id},0))*1440,0)'), 8),
    CA('what', 'What guests do', 'text', LKT('run.what', 'run.step_id', 'step_id'), 44), CA('place', 'Place', 'text', LKT('run.place', 'run.step_id', 'step_id'), 10), CA('block', 'Block', 'text', LKT('run.block', 'run.step_id', 'step_id'), 13)],
    D.gtl_d(), 30))
assert len(tables) == 20, len(tables)
