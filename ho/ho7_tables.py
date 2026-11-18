"""Home Management suite part 7: settings and the 20 tables with their calculated columns (documents, contacts, renewal sources, ranked lists)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho7_lists import *
import ho7_data as D


def R(t, c): return '{range:%s.%s}' % (t, c)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)
def LKT(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0))&"","")' % (src, my, kc)
def LKN(src, kc, my): return 'IFERROR(INDEX({range:%s},MATCH({col:%s},{range:%s},0)),0)' % (src, my, kc)


YES = '{list:yesno.yes}'
K_TRAV, K_LIC, K_POL, K_CON, K_WAR, K_SCH, K_PET, K_OTH = (tok('dkind', k) for k in DOC_KINDS)
S_VALID, S_START, S_RENEWED = tok('dstatus', 'Valid'), tok('dstatus', 'Renewal started'), tok('dstatus', 'Renewed')
RT_DOC, RT_CON, RT_WAR, RT_VEH, RT_PET, RT_TASK = (tok('rtype', t) for t in RTYPES)
H1, H2, HT = (tok('hand', h) for h in HAND)
HP1, HP2, HPC1, HPC2, HPW = (tok('epeople', h) for h in EVENT_PEOPLE)
W_RENEWED, W_EXPIRED, W_STARTED, W_MISSED, W_NOW, W_SOON, W_OK = (lbl(w) for w in ('Renewed', 'Expired', 'Renewal started', 'Lead time missed', 'Act now', 'Soon', 'OK'))

SRC = ['documents', 'warranties', 'vehicle_dates', 'pet_dates', 'tasks']
DR = lambda c: R('documents', c)
WR = lambda c: R('warranties', c)
VR = lambda c: R('vehicle_dates', c)
PR = lambda c: R('pet_dates', c)
TR = lambda c: R('tasks', c)
CR = lambda c: R('contacts', c)
KR = lambda c: R('keys', c)
RMR = lambda c: R('renew_month', c)
RTR = lambda c: R('renew_type', c)
ER = lambda c: R('emergency', c)
SR = lambda c: R('sitter', c)
RNR = lambda c: R('renewals', c)
BR = lambda c: R('board', c)
FIRST = 'DATE(YEAR({today}),MONTH({today}),1)'


def TLR(role, col): return 'IFERROR(INDEX({range:team.%s},MATCH({list:role.%s},{range:team.role},0))&"","")' % (col, key('role', role))
def TLC(n, col): return 'IFERROR(INDEX({range:team.%s},MATCH({set:child%d_id},{range:team.member_id},0))&"","")' % (col, n)
def NAME(role, k, label=None): return CA(k, label or (role + ' name'), 'text', TLR(role, 'short'), 14)
def PHONE(role, k, label=None): return CA(k, label or (role + ' phone'), 'text', TLR(role, 'phone'), 18)
def CNAME(n, k): return CA(k, 'Child %d name' % n, 'text', TLC(n, 'short'), 14)
def CPHONE(n, k): return CA(k, 'Child %d phone' % n, 'text', TLC(n, 'phone'), 18)
def HOUSE(): return CA('household', 'Household', 'text', '{set:household}', 24)
def A12(): return [NAME('Adult 1', 'a1_name'), PHONE('Adult 1', 'a1_phone'), NAME('Adult 2', 'a2_name'), PHONE('Adult 2', 'a2_phone')]
def PERS(col):   # name or phone of the person in this row's holder column
    return ('IF({col:holder}=%s,%s,IF({col:holder}=%s,%s,IF({col:holder}=%s,%s,IF({col:holder}=%s,%s,%s))))'
            % (HP1, TLR('Adult 1', col), HP2, TLR('Adult 2', col), HPC1, TLC(1, col), HPC2, TLC(2, col), TLR('Adult 1', col)))


settings = [
    S('household', 'Household name', 'text', HOUSEHOLD), S('adult1', 'Adult 1 shown as', 'text', 'Adult 1'), S('adult2', 'Adult 2 shown as', 'text', 'Adult 2'),
    S('child1_id', 'Team member ID of child 1', 'text', 'HO-03'), S('child2_id', 'Team member ID of child 2', 'text', 'HO-04'),
    S('trip_date', 'Family trip: first day', 'date', ahead(70)), S('trip_days', 'Family trip: days away', 'int', 10),
    S('default_lead', 'Usual lead time: act this many days before a date (typical 60 for a travel document)', 'int', 60),
    S('other_lead', 'Lead time for warranties, vehicle, pet and home task dates, days', 'int', 30),
    S('act_now_days', 'Act now: the action date is within this many days', 'int', 14), S('soon_days', 'Soon: the action date is within this many days', 'int', 60),
    S('review_lead', 'Contract review: look this many days before the end', 'int', 45), S('notice_days', 'Notice period of a contract, days (check your contract)', 'int', 60),
    S('stale_days', 'A contact is not used for this many days', 'int', 365), S('check_days', 'An emergency number is checked again after this many days', 'int', 180),
    S('key_days', 'A key is out too long after this many days', 'int', 60), S('fair_share', 'Adult 1 fair share of renewals handled', 'pct', 0.5),
    S('fair_margin', 'A share is fair within this margin', 'pct', 0.15), S('visit_hour', 'Usual appointment hour, 24-hour clock', 'int', 10),
]
assert 3 <= len(settings) <= 20, len(settings)

# ---- shared renewal-source columns -------------------------------------------------------------------------------------------------------------
def RK(code, t, idk):
    return CA('rkey', 'Ranking key', 'int', 'IF({col:in90}=1,({col:rdate}-{today})*10000+%d+MATCH({col:%s},%s,0),"")' % (code, idk, R(t, idk)), 16)


GRK = CA('grk', 'Rank in the next 90 days, 1 is first', 'int', 'IF({col:rkey}="","",1+' + '+'.join('COUNTIFS(%s,"<"&{col:rkey})' % R(t, 'rkey') for t in SRC) + ')', 10)


def DL(): return CA('days_left', 'Days left', 'int', 'IF({col:rdate}="","",{col:rdate}-{today})', 8)
def I90(): return CA('in90', 'In the next 90 days, 1 or 0', 'int', 'IF({col:rdate}="",0,IF(AND({col:rdate}>={today},{col:rdate}<={today}+90),1,0))', 9)
def I12(): return CA('in12', 'In the next 12 months, 1 or 0', 'int', 'IF({col:rdate}="",0,IF(AND({col:rdate}>={today},{col:rdate}<EDATE(%s,12)),1,0))' % FIRST, 9)


tables = []
# 1 team ------------------------------------------------------------------------
tables.append(T('team', 'Team', 'Household members and outside contacts',
    'One row per household member and outside contact: role, phone and e-mail; the texts in this workbook use these numbers. Children are listed by first name. Renters read a trade as the landlord.', [
    C('member_id', 'Member ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 16), C('group', 'Group', 'text', 10), C('phone', 'Phone', 'text', 18),
    C('email', 'E-mail', 'text', 26), C('note', 'Note', 'text', 30), C('start', 'Since', 'date', 11), C('short', 'Short name', 'text', 12), HOUSE()], D.team_d(), 50))

# 2 documents -------------------------------------------------------------------
ACT = 'IF(OR({col:status}=%s,{col:expiry}=""),0,1)' % S_RENEWED
tables.append(T('documents', 'Documents', 'Documents and renewals checklist with the action date',
    'One row per document or agreement: holder, expiry or renewal date, the days before it you act, where it is kept and who handles it; days left, the action date and the status fill in. Renters add the tenancy agreement as a Contract.', [
    C('doc_id', 'Document ID', 'text', 10, required=True), C('doc', 'Document', 'text', 34), LST('kind', 'Kind', 'dkind', 16), LST('holder', 'Holder', 'epeople', 16), C('expiry', 'Expiry or renewal date', 'date', 12),
    C('renew_lead_days', 'Act this many days before', 'int', 10), LST('kept_where', 'Kept where', 'kept', 22), LST('status', 'Status', 'dstatus', 14), C('renewed_on', 'Renewed on', 'date', 12), LST('handler', 'Handled by', 'hand', 11),
    CA('active', 'Active, 1 or 0', 'int', ACT, 8),
    CA('days_left', 'Days left', 'int', 'IF({col:active}=1,{col:expiry}-{today},"")', 8),
    CA('action_date', 'Action date', 'date', 'IF({col:expiry}="","",{col:expiry}-{col:renew_lead_days})', 11),
    CA('dta', 'Days to the action date', 'int', 'IF({col:active}=1,{col:action_date}-{today},"")', 9),
    CA('astatus', 'Action status', 'text', 'IF({col:expiry}="","",IF({col:active}=0,%s,IF({col:days_left}<0,%s,IF({col:status}=%s,%s,IF({col:dta}<0,%s,IF({col:dta}<={set:act_now_days},%s,IF({col:dta}<={set:soon_days},%s,%s)))))))'
       % (W_RENEWED, W_EXPIRED, S_START, W_STARTED, W_MISSED, W_NOW, W_SOON, W_OK), 15),
    CA('rtype', 'Renewal type', 'text', 'IF(OR({col:kind}=%s,{col:kind}=%s),%s,%s)' % (K_CON, K_POL, RT_CON, RT_DOC), 20),
    CA('rdate', 'Renewal date', 'date', 'IF({col:active}=1,{col:expiry},"")', 11), I90(), I12(), RK(1000, 'documents', 'doc_id'), GRK,
    CA('drk', 'Rank by days left, 1 is soonest', 'int', 'IF({col:active}=1,1+COUNTIFS(%s,"<"&{col:days_left})+COUNTIFS(%s,{col:days_left},%s,"<"&{col:doc_id}),"")' % (DR('days_left'), DR('days_left'), DR('doc_id')), 9),
    CA('ark', 'Rank of the action dates to the end of this month', 'int', 'IF({col:active}=1,IF({col:action_date}<=EOMONTH({today},0),1+COUNTIFS(%s,"<"&{col:dta})+COUNTIFS(%s,{col:dta},%s,"<"&{col:doc_id}),""),"")' % (DR('dta'), DR('dta'), DR('doc_id')), 10),
    CA('kept_missing', 'No place kept, 1 or 0', 'int', 'IF(AND({col:active}=1,{col:kept_where}=""),1,0)', 9),
    CA('trip_date', 'Family trip', 'date', '{set:trip_date}', 11), CA('trip_end', 'Back from the trip', 'date', '{set:trip_date}+{set:trip_days}-1', 11),
    CA('trip_margin', 'Travel document: days valid after the trip', 'int', 'IF(AND({col:active}=1,{col:kind}=%s),{col:expiry}-{col:trip_end},"")' % K_TRAV, 11),
    CA('early', 'Renewed before the action date, 1 or 0', 'int', 'IF(OR({col:renewed_on}="",{col:expiry}=""),"",IF({col:renewed_on}<={col:action_date},1,0))', 10),
    CA('on_time', 'Renewed on time, 1 or 0', 'int', 'IF(OR({col:renewed_on}="",{col:expiry}=""),"",IF({col:renewed_on}<={col:expiry},1,0))', 9),
    CA('visit_at', 'Appointment time', 'time', '{set:visit_hour}/24', 9)] + A12() + [CNAME(1, 'c1_name'), CPHONE(1, 'c1_phone'), CNAME(2, 'c2_name'), CPHONE(2, 'c2_phone'), HOUSE()],
    D.docs_d(), 200, [A('astatus', '= ' + W_MISSED, 'bad'), A('astatus', '= ' + W_EXPIRED, 'bad'), A('astatus', '= ' + W_NOW, 'warn'), A('astatus', '= ' + W_SOON, 'warn'), A('astatus', '= ' + W_OK, 'good')]))

# 3 contacts --------------------------------------------------------------------
tables.append(T('contacts', 'Contacts', 'Household contacts: trades, school, neighbour and family',
    'One row per contact: kind, trade, phone, e-mail, when you last used them, the cost line of the last job and whether you would use them again; the phone, days since and a stale flag fill in. The vet clinic is a dates-only contact.', [
    C('contact_id', 'Contact ID', 'text', 10, required=True), C('name', 'Name', 'text', 22), LST('kind', 'Kind', 'ckind', 12), C('trade', 'Trade or role', 'text', 24), C('phone', 'Phone', 'text', 18), C('email', 'E-mail', 'text', 28),
    C('last_used', 'Last used', 'date', 11), C('cost_last', 'Cost line, last time', 'money', 11), C('would_use_again', 'Would use again', 'bool', 9), REF('member_id', 'Team member ID', 'team.member_id', 10),
    CA('phone_ok', 'Has a phone, 1 or 0', 'int', 'IF({col:contact_id}="","",IF({col:phone}="",0,1))', 8), CA('days_since', 'Days since last used', 'int', 'IF({col:last_used}="","",{today}-{col:last_used})', 9),
    CA('stale', 'Not used for a long time, 1 or 0', 'int', 'IF({col:contact_id}="","",IF({col:last_used}="",1,IF({today}-{col:last_used}>{set:stale_days},1,0)))', 9), HOUSE()],
    D.contacts_d(), 100, [A('would_use_again', '= ' + YES, 'good'), A('stale', '= 1', 'warn')]))

# 4 warranties ------------------------------------------------------------------
tables.append(T('warranties', 'Warranty dates', 'Items with a warranty end date typed',
    'One row per item with a warranty end: room, price, who handles it, whether the receipt and the manual are kept; days left and the in-the-next-90-days flag fill in. Keep the receipt with the warranty paper.', [
    C('item_id', 'Item ID', 'text', 9, required=True), C('item', 'Item', 'text', 26), C('room', 'Room', 'text', 16), C('warranty_end', 'Warranty end', 'date', 11), C('price', 'Price', 'money', 10), LST('handler', 'Handled by', 'hand', 11),
    C('receipt', 'Receipt kept', 'bool', 8), C('manual', 'Manual kept', 'text', 26), C('note', 'Note', 'text', 30),
    CA('rdate', 'Renewal date', 'date', 'IF({col:warranty_end}="","",{col:warranty_end})', 11), DL(), I90(), I12(), RK(2000, 'warranties', 'item_id'), GRK],
    D.warranties_d(), 150, [A('in90', '= 1', 'warn')]))

# 5 vehicle dates ---------------------------------------------------------------
tables.append(T('vehicle_dates', 'Vehicle dates', 'Service, tyres, annual test, insurance and registration dates',
    'One row per vehicle date: service, tyres, annual vehicle test, insurance renewal, registration renewal or a repair; days left and the in-the-next-90-days flag fill in. Intervals are typical, check the manual.', [
    C('vd_id', 'Vehicle date ID', 'text', 10, required=True), C('vehicle', 'Vehicle', 'text', 18), LST('kind', 'Kind', 'vkind', 18), C('date', 'Date', 'date', 11), C('notes', 'Notes', 'text', 36), LST('handler', 'Handled by', 'hand', 11),
    CA('rdate', 'Renewal date', 'date', 'IF({col:date}="","",{col:date})', 11), DL(), I90(), I12(), RK(3000, 'vehicle_dates', 'vd_id'), GRK, NAME('Car mechanic', 'cm_name'), PHONE('Car mechanic', 'cm_phone'), HOUSE()],
    D.vehicle_dates_d(), 50, [A('in90', '= 1', 'warn')]))

# 6 pet dates -------------------------------------------------------------------
tables.append(T('pet_dates', 'Pet dates', 'Vet visits, vaccinations, grooming and food dates',
    'One row per pet date: grooming, vet visit, vaccination visit, nail trim, food bag due or bath, and whether it is booked; dates only, no health notes. Days left and the in-the-next-90-days flag fill in.', [
    C('pd_id', 'Pet date ID', 'text', 10, required=True), C('pet', 'Pet', 'text', 12), LST('task', 'Task', 'ptask', 18), C('date', 'Date', 'date', 11), C('booked', 'Booked', 'bool', 8), LST('handler', 'Handled by', 'hand', 11),
    CA('rdate', 'Renewal date', 'date', 'IF({col:date}="","",{col:date})', 11), DL(), I90(), I12(), RK(4000, 'pet_dates', 'pd_id'), GRK], D.pet_dates_d(), 50, [A('in90', '= 1', 'warn'), A('booked', '= ' + YES, 'good')]))

# 7 maintenance due dates -------------------------------------------------------
tables.append(T('tasks', 'Maintenance due dates', 'Filters, alarms and services with the next due date',
    'One row per maintenance task: area, who does it, the interval and when it was last done (typical intervals, check the manual); next due and the flags fill in. Tick the filter, alarm and service tasks that belong in the renewals list.', [
    C('task_id', 'Task ID', 'text', 9, required=True), C('task', 'Task', 'text', 34), C('area', 'Area', 'text', 20), LST('assigned', 'Assigned to', 'hand', 11), C('interval_days', 'Interval, days', 'int', 9),
    C('last_done', 'Last done', 'date', 11), C('fa', 'Filter, alarm or service', 'bool', 10),
    CA('next_due', 'Next due', 'date', 'IF({col:last_done}="","",{col:last_done}+{col:interval_days})', 11),
    CA('rdate', 'Renewal date', 'date', 'IF(AND({col:fa}=%s,{col:next_due}<>""),{col:next_due},"")' % YES, 11), DL(), I90(), I12(), RK(5000, 'tasks', 'task_id'), GRK], D.tasks_d(), 100, [A('in90', '= 1', 'warn')]))

# 8 routines --------------------------------------------------------------------
tables.append(T('routines', 'Home routines', 'House routines for the sitter sheet',
    'One row per routine: bin day, school hours, bedtimes, feed times, quiet hours; type when it happens and a note. No health details, ever. Single adults leave the children and school rows empty.', [
    C('routine', 'Routine', 'text', 22, required=True), C('when', 'When', 'text', 50), C('notes', 'Notes', 'text', 40), C('reviewed', 'Last reviewed', 'date', 11),
    CA('age', 'Days since reviewed', 'int', 'IF({col:reviewed}="","",{today}-{col:reviewed})', 9), NAME('Babysitter', 'bs_name'), PHONE('Babysitter', 'bs_phone'), NAME('Neighbour', 'nb_name'), HOUSE()], D.routines_d(), 50))

# 9 where things are ------------------------------------------------------------
tables.append(T('where_things', 'Where things are', 'Stopcock, fuse box, spare key, manuals and torches',
    'One row per thing a sitter or visitor needs to find: where it is and a note; the days since you last checked fill in. Check the stopcock and the fuse box once a year.', [
    C('thing', 'Thing', 'text', 24, required=True), C('place', 'Place', 'text', 32), C('notes', 'Notes', 'text', 40), C('checked', 'Last checked', 'date', 11),
    CA('age', 'Days since checked', 'int', 'IF({col:checked}="","",{today}-{col:checked})', 9), NAME('Plumber', 'pl_name'), PHONE('Plumber', 'pl_phone'), HOUSE()], D.where_d(), 50))

# 10 keys -----------------------------------------------------------------------
tables.append(T('keys', 'Key and access list', 'Who holds a key, since when, returned or not',
    'One row per key or remote handed to someone: holder, what, since when, the date it came back and a note; whether it is out and how long fill in. Leave Returned empty while it is out.', [
    C('key_id', 'Key ID', 'text', 9, required=True), LST('holder', 'Holder', 'kholder', 16), C('what', 'What', 'text', 28), C('since', 'Since', 'date', 11), C('returned', 'Returned', 'date', 11), C('note', 'Note', 'text', 36),
    CA('out', 'Out, 1 or 0', 'int', 'IF({col:key_id}="","",IF({col:since}="",0,IF({col:returned}="",1,0)))', 7), CA('days_out', 'Days out', 'int', 'IF({col:out}=1,{today}-{col:since},"")', 8),
    CA('trip_date', 'Family trip', 'date', '{set:trip_date}', 11), CA('trip_end', 'Back from the trip', 'date', '{set:trip_date}+{set:trip_days}-1', 11), CA('key_from', 'Hold the key from', 'date', '{set:trip_date}-1', 11),
    NAME('Grandparent', 'gp_name'), PHONE('Grandparent', 'gp_phone'), NAME('Neighbour', 'nb_name'), PHONE('Neighbour', 'nb_phone'), NAME('Dog walker', 'dw_name'), PHONE('Dog walker', 'dw_phone'), HOUSE()],
    D.keys_d(), 60, [A('out', '= 1', 'warn')]))

# 11 renewals next 90 days (ranked) ---------------------------------------------
def MT(t): return 'IFERROR(MATCH({col:no},%s,0),"")' % R(t, 'grk')
def CH(*parts): return 'IF({col:src}="","",IFERROR(CHOOSE({col:src},%s),""))' % ','.join(parts)
def PI(t, c): return 'INDEX(%s,{col:pos})' % R(t, c)
tables.append(T('renewals', 'Renewals next 90 days', 'Everything that comes due in the next 90 days, in one ranked list',
    'Type the rank numbers 1 to 60 once. Documents, contracts, warranties, vehicle dates, pet dates and filter, alarm and service tasks fall into one list by date with the owner, days left and the action date.', [
    C('no', 'Rank', 'int', 7, required=True),
    CA('s1', 'Documents row', 'int', MT('documents'), 8), CA('s2', 'Warranties row', 'int', MT('warranties'), 8), CA('s3', 'Vehicle dates row', 'int', MT('vehicle_dates'), 8),
    CA('s4', 'Pet dates row', 'int', MT('pet_dates'), 8), CA('s5', 'Tasks row', 'int', MT('tasks'), 8),
    CA('src', 'Source, 1 to 5', 'int', 'IF({col:no}="","",IF({col:s1}<>"",1,IF({col:s2}<>"",2,IF({col:s3}<>"",3,IF({col:s4}<>"",4,IF({col:s5}<>"",5,""))))))', 8),
    CA('pos', 'Row in the source', 'int', 'IF({col:src}="","",CHOOSE({col:src},{col:s1},{col:s2},{col:s3},{col:s4},{col:s5}))', 8),
    CA('type', 'Type', 'text', CH(PI('documents', 'rtype'), RT_WAR, RT_VEH, RT_PET, RT_TASK), 20),
    CA('name', 'Name', 'text', CH(PI('documents', 'doc'), PI('warranties', 'item'), PI('vehicle_dates', 'vehicle') + '&" - "&' + PI('vehicle_dates', 'kind'), PI('pet_dates', 'pet') + '&" - "&' + PI('pet_dates', 'task'), PI('tasks', 'task')), 34),
    CA('owner', 'Owner', 'text', CH(PI('documents', 'handler'), PI('warranties', 'handler'), PI('vehicle_dates', 'handler'), PI('pet_dates', 'handler'), PI('tasks', 'assigned')), 11),
    CA('date', 'Date', 'date', CH(PI('documents', 'rdate'), PI('warranties', 'rdate'), PI('vehicle_dates', 'rdate'), PI('pet_dates', 'rdate'), PI('tasks', 'rdate')), 11),
    CA('days_left', 'Days left', 'int', 'IF({col:date}="","",{col:date}-{today})', 8),
    CA('action', 'Action date', 'date', 'IF({col:src}="","",IF({col:src}=1,%s,{col:date}-{set:other_lead}))' % PI('documents', 'action_date'), 11),
    CA('action_in', 'Days to the action date', 'int', 'IF({col:action}="","",{col:action}-{today})', 9),
    CA('verdict', 'Action status', 'text', 'IF({col:action_in}="","",IF({col:action_in}<0,%s,IF({col:action_in}<={set:act_now_days},%s,IF({col:action_in}<={set:soon_days},%s,%s))))' % (W_MISSED, W_NOW, W_SOON, W_OK), 15)],
    [dict(no=i) for i in range(1, 61)], 60, [A('verdict', '= ' + W_MISSED, 'bad'), A('verdict', '= ' + W_NOW, 'warn')]))

# 12 renewals by month ----------------------------------------------------------
def CNT(t, extra=''): return 'COUNTIFS(%s,">="&{col:lo},%s,"<"&{col:hi}%s)' % (R(t, 'rdate'), R(t, 'rdate'), extra)
tables.append(T('renew_month', 'Renewals by month', 'The next 12 months: items, documents, contracts, warranties and dates by month',
    'Type 0 to 11 once, with the month label from the lists; the month, all items due and the split by documents, contracts, policies, warranties, vehicles, pets and tasks fill in, with the first document of the month.', [
    C('mk', 'Months ahead', 'int', 8, required=True), LST('ahead', 'Month ahead', 'ahead12', 13), LST('qtr', 'Quarter ahead', 'qtr4', 14),
    CA('month', 'Month', 'date', 'EDATE(%s,{col:mk})' % FIRST, 11), CA('lo', 'From', 'date', 'MAX({col:month},{today})', 11), CA('hi', 'Before', 'date', 'EDATE({col:month},1)', 11),
    CA('items', 'Items due', 'int', '+'.join(CNT(t) for t in SRC), 8), CA('docs', 'Documents and contracts', 'int', CNT('documents'), 10),
    CA('contracts', 'Contracts', 'int', CNT('documents', ',%s,%s' % (DR('kind'), K_CON)), 9), CA('policies', 'Policies', 'int', CNT('documents', ',%s,%s' % (DR('kind'), K_POL)), 9),
    CA('warr', 'Warranty ends', 'int', CNT('warranties'), 9), CA('veh', 'Vehicle dates', 'int', CNT('vehicle_dates'), 9), CA('pets', 'Pet dates', 'int', CNT('pet_dates'), 9), CA('tasks', 'Filter, alarm and service tasks', 'int', CNT('tasks'), 10),
    CA('actions', 'Action dates in the month', 'int', 'COUNTIFS(%s,1,%s,">="&{col:month},%s,"<"&{col:hi})' % (DR('active'), DR('action_date'), DR('action_date')), 10),
    CA('first_date', 'First document date', 'date', 'IF({col:docs}=0,"",MINIFS(%s,%s,">="&{col:lo},%s,"<"&{col:hi}))' % (DR('rdate'), DR('rdate'), DR('rdate')), 11),
    CA('first_doc', 'First document', 'text', 'IF({col:first_date}="","",IFERROR(INDEX(%s,MATCH({col:first_date},%s,0)),""))' % (DR('doc'), DR('rdate')), 30)] + [NAME('Adult 1', 'a1_name'), PHONE('Adult 1', 'a1_phone'), HOUSE()],
    D.month_d(), 50, [A('items', '> 0', 'warn')]))

# 13 renewals by type -----------------------------------------------------------
def TY(col, flag): return 'SUMIFS(%s,%s,{col:type})+({col:type}=%s)*SUM(%s)+({col:type}=%s)*SUM(%s)+({col:type}=%s)*SUM(%s)+({col:type}=%s)*SUM(%s)' % (
    DR(flag), DR('rtype'), RT_WAR, WR(flag), RT_VEH, VR(flag), RT_PET, PR(flag), RT_TASK, TR(flag))
tables.append(T('renew_type', 'Renewals by type', 'Renewals of the next 90 days and 12 months by type',
    'One row per renewal type; the items due in the next 90 days and the next 12 months fill in from the six source sheets. Type the six types once.', [
    LST('type', 'Type', 'rtype', 22, required=True), CA('next90', 'Next 90 days', 'int', TY('n90', 'in90'), 9), CA('next12', 'Next 12 months', 'int', TY('n12', 'in12'), 9)],
    D.rtype_d(), 50))

# 14 document status board ------------------------------------------------------
def BI(c): return 'IF({col:mr}="","",INDEX(%s,{col:mr}))' % DR(c)
tables.append(T('board', 'Document status board', 'Every document by days left: holder, action date and status',
    'Type the rank numbers 1 to 41 once; the documents appear by days left with the holder, expiry, action date and status. Contacts for the school, landlord and heating engineer are looked up for the texts.', [
    C('no', 'Rank', 'int', 7, required=True), CA('mr', 'Row in Documents', 'int', 'IFERROR(MATCH({col:no},%s,0),"")' % DR('drk'), 8),
    CA('doc', 'Document', 'text', BI('doc'), 34), CA('holder', 'Holder', 'text', BI('holder'), 16), CA('expiry', 'Expiry or renewal date', 'date', BI('expiry'), 12),
    CA('days_left', 'Days left', 'int', BI('days_left'), 8), CA('action_date', 'Action date', 'date', BI('action_date'), 11), CA('status', 'Status', 'text', BI('astatus'), 15), CA('handler', 'Handled by', 'text', BI('handler'), 11), CA('kind', 'Kind', 'text', BI('kind'), 16), CA('kept_where', 'Kept where', 'text', 'IF({col:mr}="","",INDEX(%s,{col:mr})&"")' % DR('kept_where'), 22),
    CA('review_by', 'Review by', 'date', 'IF({col:mr}="","",{col:expiry}-{set:review_lead})', 11), CA('notice_by', 'Give notice by', 'date', 'IF({col:mr}="","",{col:expiry}-{set:notice_days})', 11),
    CA('trip_date', 'Family trip', 'date', 'IF({col:mr}="","",{set:trip_date})', 11), CA('trip_end', 'Back from the trip', 'date', 'IF({col:mr}="","",{set:trip_date}+{set:trip_days}-1)', 11),
    NAME('Adult 2', 'a2_name'), PHONE('Adult 2', 'a2_phone'), NAME('Grandparent', 'gp_name'), PHONE('Grandparent', 'gp_phone'), NAME('Carpool family', 'cp_name'), PHONE('Carpool family', 'cp_phone'), NAME('School office', 'so_name'), PHONE('School office', 'so_phone'),
    NAME('Landlord or agent', 'll_name'), PHONE('Landlord or agent', 'll_phone'), NAME('Heating engineer', 'he_name'), PHONE('Heating engineer', 'he_phone'), HOUSE()],
    D.board_d(), 50, [A('status', '= ' + W_MISSED, 'bad'), A('status', '= ' + W_NOW, 'warn'), A('status', '= ' + W_OK, 'good')]))

# 15 action dates this month ----------------------------------------------------
def AI(c): return 'IF({col:mr}="","",INDEX(%s,{col:mr}))' % DR(c)
tables.append(T('actions', 'Action dates this month', 'Documents whose action date is this month or already past',
    'Type the rank numbers 1 to 20 once; documents whose action date falls by the end of this month appear, the soonest first, with a flag when the lead time was missed.', [
    C('no', 'Rank', 'int', 7, required=True), CA('mr', 'Row in Documents', 'int', 'IFERROR(MATCH({col:no},%s,0),"")' % DR('ark'), 8),
    CA('doc', 'Document', 'text', AI('doc'), 34), CA('holder', 'Holder', 'text', AI('holder'), 16), CA('action_date', 'Action date', 'date', AI('action_date'), 11), CA('days_to', 'Days to the action date', 'int', AI('dta'), 9),
    CA('missed', 'Lead time missed, 1 or 0', 'int', 'IF({col:mr}="","",IF({col:days_to}<0,1,0))', 9)], D.actions_d(), 50, [A('missed', '= 1', 'bad')]))

# 16 documents by holder --------------------------------------------------------
tables.append(T('holders', 'Documents by holder', 'Documents per household member with the nearest expiry',
    'One row per holder; the documents held, the next expiry and the days to it fill in, with the person name and phone for the texts. Single adults delete the children.', [
    LST('holder', 'Holder', 'epeople', 16, required=True), LST('kind', 'Kind', 'dkind', 16), CA('docs', 'Documents', 'int', 'COUNTIFS(%s,{col:holder},%s,{col:kind},%s,1)' % (DR('holder'), DR('kind'), DR('active')), 9),
    CA('next_rk', 'Rank of the next document', 'int', 'IF(COUNTIFS(%s,{col:holder},%s,{col:kind},%s,">=0")=0,"",MINIFS(%s,%s,{col:holder},%s,{col:kind},%s,">=0"))' % (DR('holder'), DR('kind'), DR('days_left'), DR('drk'), DR('holder'), DR('kind'), DR('days_left')), 9),
    CA('next_expiry', 'Next expiry', 'date', 'IF({col:next_rk}="","",INDEX(%s,MATCH({col:next_rk},%s,0)))' % (DR('expiry'), DR('drk')), 11),
    CA('next_days', 'Days to the next expiry', 'int', 'IF({col:next_expiry}="","",{col:next_expiry}-{today})', 9),
    CA('next_doc', 'Next document', 'text', 'IF({col:next_rk}="","",INDEX(%s,MATCH({col:next_rk},%s,0)))' % (DR('doc'), DR('drk')), 30),
    CA('name', 'Name', 'text', PERS('short'), 14), CA('phone', 'Phone', 'text', PERS('phone'), 18), CA('review_date', 'Document review on', 'date', '{today}+MOD(6-WEEKDAY({today},2),7)', 11), HOUSE()], D.holder_d(), 50))

# 17 contacts by kind -----------------------------------------------------------
tables.append(T('contact_kind', 'Contacts by kind', 'Contacts per kind with the last time used',
    'One row per contact kind; the contacts, how many have a phone, how many you would use again and when one was last used fill in.', [
    LST('kind', 'Kind', 'ckind', 14, required=True), CA('contacts', 'Contacts', 'int', 'COUNTIFS(%s,{col:kind})' % CR('kind'), 9), CA('with_phone', 'With a phone', 'int', 'SUMIFS(%s,%s,{col:kind})' % (CR('phone_ok'), CR('kind')), 9)], D.ckind_d(), 50))

# 18 emergency contact sheet ----------------------------------------------------
tables.append(T('emergency', 'Emergency contact sheet', 'Who to call, the phone, when to call and when it was checked',
    'One row per person or service to call: the role, the page they belong to, when to call and when you last checked the number; the name and phone fill in from Team. No health details.', [
    LST('who', 'Who', 'role', 16, required=True), C('page', 'Page', 'text', 18), C('when_to_call', 'When to call', 'text', 40), C('last_checked', 'Number last checked', 'date', 11),
    CA('name', 'Name', 'text', LKT('team.short', 'team.role', 'who'), 14), CA('phone', 'Phone', 'text', LKT('team.phone', 'team.role', 'who'), 18),
    CA('phone_ok', 'Has a phone, 1 or 0', 'int', 'IF({col:who}="","",IF({col:phone}="",0,1))', 8), CA('days_checked', 'Days since checked', 'int', 'IF({col:last_checked}="","",{today}-{col:last_checked})', 9),
    CA('stale', 'Check again, 1 or 0', 'int', 'IF({col:who}="","",IF({col:last_checked}="",1,IF({today}-{col:last_checked}>{set:check_days},1,0)))', 8)] +
    [NAME('Carpool family', 'cp_name'), PHONE('Carpool family', 'cp_phone'), NAME('School office', 'so_name'), PHONE('School office', 'so_phone'), NAME('Babysitter', 'bs_name'), PHONE('Babysitter', 'bs_phone'), NAME('Neighbour', 'nb_name'), PHONE('Neighbour', 'nb_phone'), HOUSE()], D.emergency_d(), 50, [A('stale', '= 1', 'warn')]))

# 19 sitter sheet ---------------------------------------------------------------
LK_TEAM = 'IFERROR(INDEX(%s,MATCH({col:lookup},%s,0))&", "&INDEX(%s,MATCH({col:lookup},%s,0)),"")' % (R('team', 'short'), R('team', 'member_id'), R('team', 'phone'), R('team', 'member_id'))
LK_RT = 'IFERROR(INDEX(%s,MATCH({col:lookup},%s,0))&"","")' % (R('routines', 'when'), R('routines', 'routine'))
LK_WH = 'IFERROR(INDEX(%s,MATCH({col:lookup},%s,0))&"","")' % (R('where_things', 'place'), R('where_things', 'thing'))
LK_CT = 'IFERROR(INDEX(%s,MATCH({col:lookup},%s,0))&", "&INDEX(%s,MATCH({col:lookup},%s,0)),"")' % (CR('name'), CR('trade'), CR('phone'), CR('trade'))
tables.append(T('sitter', 'Sitter sheet', 'The one-page sitter sheet: children, numbers, routines and where things are',
    'One row per line of the sheet: type what it is, the source (Team, Home routines, Where things are or Contacts) and the key to look up; the value fills in. Children appear by first name; no health details. A single adult leaves the children rows empty.', [
    C('item', 'Item', 'text', 28, required=True), LST('source', 'Source', 'ssrc', 16), C('sheet', 'Sheet', 'text', 16), C('lookup', 'Look up', 'text', 24),
    CA('value', 'Value', 'text', 'IF({col:lookup}="","",IF({col:source}=%s,%s,IF({col:source}=%s,%s,IF({col:source}=%s,%s,IF({col:source}=%s,%s,"")))))' % (
        tok('ssrc', 'Team'), LK_TEAM, tok('ssrc', 'Home routines'), LK_RT, tok('ssrc', 'Where things are'), LK_WH, tok('ssrc', 'Contacts'), LK_CT), 44),
    CA('filled', 'Filled, 1 or 0', 'int', 'IF({col:item}="","",IF({col:value}="",0,1))', 8), CA('sheet_date', 'Sheet for the evening of', 'date', '{today}+MOD(5-WEEKDAY({today},2),7)', 11), NAME('Babysitter', 'bs_name'), PHONE('Babysitter', 'bs_phone'), HOUSE()],
    D.sitter_d(), 50, [A('filled', '= 0', 'warn')]))

# 20 storage places -------------------------------------------------------------
tables.append(T('storage', 'Storage places', 'Where the documents are kept and what expires there',
    'One row per place a paper is kept; the documents in it and how many expire in the next 12 months fill in. Keep copies in a second place.', [
    LST('kept', 'Kept where', 'kept', 24, required=True), CA('docs', 'Documents', 'int', 'COUNTIFS(%s,{col:kept},%s,1)' % (DR('kept_where'), DR('active')), 9),
    CA('exp12', 'Expiring in 12 months', 'int', 'SUMIFS(%s,%s,{col:kept})' % (DR('in12'), DR('kept_where')), 10)], D.storage_d(), 50))
assert len(tables) == 20, len(tables)


# ---- fixups: limits on titles and hints, and blank-row guards on the calculated sheets
_TX = {
    ('documents', 'hint'): 'One row per document: holder, expiry or renewal date, days before it you act, where kept, who handles it. Days left, action date and status fill in.',
    ('contacts', 'hint'): 'One row per contact: kind, trade, phone, e-mail, last used, cost line of the last job, would use again. Phone, days since and a stale flag fill in.',
    ('warranties', 'hint'): 'One row per item with a warranty end: room, price, who handles it, receipt and manual kept. Days left and the next-90-days flag fill in.',
    ('vehicle_dates', 'title'): 'Vehicle service, test, insurance and registration dates',
    ('vehicle_dates', 'hint'): 'One row per vehicle date: service, tyres, annual test, insurance or registration renewal, repair. Days left and the next-90-days flag fill in.',
    ('pet_dates', 'hint'): 'One row per pet date: grooming, vet or vaccination visit, nail trim, food bag, bath, and whether booked; dates only. Days left and the next-90-days flag fill in.',
    ('tasks', 'hint'): 'One row per maintenance task: area, who does it, interval, last done (typical intervals; check the manual). Next due and the flags fill in.',
    ('renewals', 'title'): 'Everything due in the next 90 days, ranked',
    ('renewals', 'hint'): 'Type the rank numbers 1 to 60 once. Documents, contracts, warranties, vehicle and pet dates and home tasks fall into one list by date with owner, days left and action date.',
    ('renew_month', 'title'): 'The next 12 months by month and by type of item',
    ('renew_month', 'hint'): 'Type 0 to 11 once, with the month label; the month, items due and the split by documents, contracts, policies, warranties, vehicles, pets and tasks fill in.',
    ('board', 'hint'): 'Type the rank numbers 1 to 41 once; the documents appear by days left with holder, expiry, action date and status. School, landlord and engineer contacts feed the texts.',
    ('sitter', 'title'): 'One-page sitter sheet: numbers, routines, where things are',
    ('sitter', 'hint'): 'One row per line: what it is, the source (Team, Home routines, Where things are or Contacts) and the key to look up; the value fills in. No health details.',
    ('holders', 'title'): 'Documents per holder and kind with the nearest expiry',
    ('holders', 'hint'): 'One row per holder and document kind; the documents held, the next expiry and the days to it fill in, with the person name and phone for the texts.',
}
_LB = {('documents', 'ark'): 'Rank of action dates to the month end', ('documents', 'trip_margin'): 'Travel document: days valid after trip'}
for _s in settings:
    if _s['key'] == 'default_lead': _s['label'] = 'Usual lead time in days (60 for a travel document)'
    if _s['key'] == 'other_lead': _s['label'] = 'Lead time for warranty, vehicle, pet, task dates'
_KEY = {'renew_month': 'mk', 'renew_type': 'type', 'holders': 'holder', 'contact_kind': 'kind', 'storage': 'kept', 'board': 'no', 'actions': 'no', 'renewals': 'no'}
for _t in tables:
    for (_k, _f), _v in _TX.items():
        if _t['key'] == _k: _t[_f] = _v
    for _c in _t['columns']:
        if (_t['key'], _c['key']) in _LB: _c['label'] = _LB[(_t['key'], _c['key'])]
        _kk = _KEY.get(_t['key'])
        if _kk and _c['type'] == 'calc' and _c['key'] != _kk and not _c['formula'].startswith('IF({col:%s}=""' % _kk) and not _c['formula'].startswith('IF({col:mr}=""') and not _c['formula'].startswith('IF({col:no}=""'):
            _c['formula'] = 'IF({col:%s}="","",%s)' % (_kk, _c['formula'])
