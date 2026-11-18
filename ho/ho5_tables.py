"""Home Management suite part 5: settings and the 20 tables with their calculated columns (inventory, repairs, warranty countdown, ranked lists, values and the repair-or-replace view)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho5_lists import *
import ho5_data as D


def R(t, c): return '{range:%s.%s}' % (t, c)
def CA(k, label, fmt, formula, w=12, **kw): return CALC(k, label, fmt, formula, w, **kw)


YES = '{list:yesno.yes}'
OPEN, WAIT, FIXED = (tok('rstatus', s) for s in ('Open', 'Waiting', 'Fixed'))
NONEKEPT = tok('kept', 'None kept')
APPL = tok('icat', 'Appliance')
W_COV, W_SOON, W_EXP, W_NONE = (lbl(w) for w in ('Covered', 'Ending soon', 'Expired', 'None typed'))
W_YES, W_NO = lbl('Yes'), lbl('No')
W_OPENW, W_USED, W_INSIDE, W_OUTSIDE = (lbl(w) for w in ('Open fault in warranty', 'Warranty used', 'Fault inside warranty', 'Outside warranty'))
W_REPAIR, W_WATCH, W_REPLACE, W_NOREP, W_NOPRICE = (lbl(w) for w in ('Repair', 'Watch', 'Replace', 'No repairs logged', 'No price typed'))

IR = lambda c: R('inventory', c)
RR = lambda c: R('repairs', c)
PR = lambda c: R('replace', c)
VR = lambda c: R('repair_view', c)
FIRST = 'DATE(YEAR({today}),MONTH({today}),1)'


def TLR(role, col): return 'IFERROR(INDEX({range:team.%s},MATCH({list:role.%s},{range:team.role},0))&"","")' % (col, key('role', role))
def TLC(n, col): return 'IFERROR(INDEX({range:team.%s},MATCH({set:child%d_id},{range:team.member_id},0))&"","")' % (col, n)
def GU(g, f): return 'IF(%s="","",%s)' % (g, f) if g else f


def NP(code, role, g=None):
    """name and phone columns of a person found by role (blank on an empty ranked row when a guard column is given)"""
    return [CA(code + '_name', role + ' name', 'text', GU(g, TLR(role, 'short')), 14), CA(code + '_phone', role + ' phone', 'text', GU(g, TLR(role, 'phone')), 18)]
def NPC(n, g=None):
    return [CA('c%d_name' % n, 'Child %d name' % n, 'text', GU(g, TLC(n, 'short')), 14), CA('c%d_phone' % n, 'Child %d phone' % n, 'text', GU(g, TLC(n, 'phone')), 18)]
def NPS(code, label, g=None):
    return [CA(code + '_name', label + ' name', 'text', GU(g, '{set:%s_name}' % code), 14), CA(code + '_phone', label + ' phone', 'text', GU(g, '{set:%s_phone}' % code), 18)]
def PH(code, label, g=None):
    """phone column only (messages to a person without a name placeholder)"""
    f = {'a1': TLR('Adult 1', 'phone'), 'a2': TLR('Adult 2', 'phone'), 'c1': TLC(1, 'phone'), 'c2': TLC(2, 'phone'), 'gp': TLR('Grandparent', 'phone'), 'bs': TLR('Babysitter', 'phone'),
         'cp': TLR('Carpool family', 'phone'), 'nb': TLR('Neighbour', 'phone'), 'so': TLR('School office', 'phone'), 'pl': TLR('Plumber', 'phone'), 'el': TLR('Electrician', 'phone'),
         'cm': TLR('Car mechanic', 'phone')}[code]
    return CA(code + '_phone', label + ' phone', 'text', GU(g, f), 18)
def HOUSE(g=None): return CA('household', 'Household', 'text', GU(g, '{set:household}'), 24)


settings = [
    S('household', 'Household name', 'text', HOUSEHOLD), S('adult1', 'Adult 1 shown as', 'text', 'Adult 1'), S('adult2', 'Adult 2 shown as', 'text', 'Adult 2'),
    S('child1_id', 'Team member ID of child 1', 'text', 'HO-03'), S('child2_id', 'Team member ID of child 2', 'text', 'HO-04'),
    S('warranty_days', 'Warranty ending soon: within this many days (often 1 to 5 years, check your paperwork)', 'int', 90),
    S('urgent_days', 'Report a fault soon: warranty ends within this many days', 'int', 30),
    S('repair_rule', 'Your repair rule: repairs over this share of the replacement price suggest replacing', 'pct', 0.5),
    S('old_years', 'An item counts as old after this many years', 'int', 5), S('receipt_goal', 'Receipt goal: share of items with a receipt date', 'pct', 0.9),
    S('ar_name', 'Appliance repairer, first name', 'text', 'Dana'), S('ar_phone', 'Appliance repairer, phone', 'text', '+49 50 555 5202'),
    S('hm_name', 'Handyman, first name', 'text', 'Omar'), S('hm_phone', 'Handyman, phone', 'text', '+61 57 555 5239'),
]
assert 3 <= len(settings) <= 20, len(settings)

tables = []
# 1 team ------------------------------------------------------------------------
tables.append(T('team', 'Team', 'Household members and outside contacts',
    'One row per household member and outside contact: role, phone and e-mail; the texts in this workbook use these numbers. Children are listed by first name. Renters read a trade as the landlord.', [
    C('member_id', 'Member ID', 'text', 9, required=True), C('name', 'Name', 'text', 24), LST('role', 'Role', 'role', 16), C('group', 'Group', 'text', 10), C('phone', 'Phone', 'text', 18),
    C('email', 'E-mail', 'text', 26), C('note', 'Note', 'text', 30), C('start', 'Since', 'date', 11), C('short', 'Short name', 'text', 12), HOUSE()], D.team_d(), 50))

# 2 inventory -------------------------------------------------------------------
def GI(f): return 'IF({col:item_id}="","",%s)' % f
RC = lambda a, b: 'COUNTIFS(%s,{col:item_id},%s,%s)' % (RR('item_id'), RR('status'), b)
def RK(cond, tail): return 'IF(%s,1+%s,"")' % (cond, tail)
inv_cols = [
    C('item_id', 'Item ID', 'text', 9, required=True), C('item', 'Item', 'text', 26), LST('room', 'Room', 'room', 14), LST('category', 'Category', 'icat', 16), C('purchase_date', 'Purchase date', 'date', 12),
    C('price', 'Price (typed cost line)', 'money', 12), C('serial', 'Serial number', 'text', 16), C('warranty_end', 'Warranty end', 'date', 12), C('receipt_date', 'Receipt date', 'date', 12),
    LST('manual_place', 'Manual place', 'kept', 28),
    CA('age_years', 'Age, years', 'num', GI('IF({col:purchase_date}="","",ROUND(({today}-{col:purchase_date})/365.25,1))'), 8),
    CA('days_left', 'Days of warranty left', 'int', GI('IF({col:warranty_end}="","",{col:warranty_end}-{today})'), 9),
    CA('status', 'Warranty status', 'text', GI('IF({col:days_left}="",%s,IF({col:days_left}<0,%s,IF({col:days_left}<={set:warranty_days},%s,%s)))' % (W_NONE, W_EXP, W_SOON, W_COV)), 13),
    CA('no_receipt', 'No receipt date, 1 or 0', 'int', GI('IF({col:receipt_date}="",1,0)'), 8),
    CA('no_serial', 'No serial, 1 or 0', 'int', GI('IF({col:serial}="",1,0)'), 8),
    CA('no_manual', 'No manual kept, 1 or 0', 'int', GI('IF(OR({col:manual_place}="",{col:manual_place}=%s),1,0)' % NONEKEPT), 8),
    CA('missing_n', 'Fields to fill, 0 to 3', 'int', GI('{col:no_receipt}+{col:no_serial}+{col:no_manual}'), 8),
    CA('rep_n', 'Repairs logged', 'int', GI('COUNTIFS(%s,{col:item_id})' % RR('item_id')), 8),
    CA('rep_cost', 'Repair cost lines', 'money', GI('SUMIFS(%s,%s,{col:item_id})' % (RR('cost'), RR('item_id'))), 10),
    CA('open_rep', 'Open repairs', 'int', GI('COUNTIFS(%s,{col:item_id},%s,%s)+COUNTIFS(%s,{col:item_id},%s,%s)' % (RR('item_id'), RR('status'), OPEN, RR('item_id'), RR('status'), WAIT)), 8),
    CA('open_left', 'Days left, open fault in warranty', 'int', GI('IF(AND({col:open_rep}>0,{col:days_left}<>""),IF({col:days_left}>=0,{col:days_left},""),"")'), 9),
    # ranks (one key per row, no ties)
    CA('wkey', 'Countdown sort key', 'int', GI('IF({col:days_left}="",200000,IF({col:days_left}>=0,{col:days_left},100000-{col:days_left}))'), 9),
    CA('wrk', 'Countdown rank', 'int', GI('1+COUNTIFS(%s,"<"&{col:wkey})+COUNTIFS(%s,{col:wkey},%s,"<"&{col:item_id})' % (IR('wkey'), IR('wkey'), IR('item_id'))), 8),
    CA('r90', 'Rank, ending soon', 'int', RK('AND({col:days_left}<>"",{col:days_left}>=0,{col:days_left}<={set:warranty_days})', 'COUNTIFS(%s,">=0",%s,"<"&{col:days_left})+COUNTIFS(%s,{col:days_left},%s,"<"&{col:item_id})' % (IR('days_left'), IR('days_left'), IR('days_left'), IR('item_id'))), 8),
    CA('rex', 'Rank, expired (latest first)', 'int', RK('AND({col:days_left}<>"",{col:days_left}<0)', 'COUNTIFS(%s,"<0",%s,">"&{col:days_left})+COUNTIFS(%s,{col:days_left},%s,"<"&{col:item_id})' % (IR('days_left'), IR('days_left'), IR('days_left'), IR('item_id'))), 8),
    CA('rmiss', 'Rank, missing fields', 'int', RK('{col:missing_n}>0', 'COUNTIFS(%s,">"&{col:missing_n})+COUNTIFS(%s,{col:missing_n},%s,">"&{col:price})+COUNTIFS(%s,{col:missing_n},%s,{col:price},%s,"<"&{col:item_id})' % (
        IR('missing_n'), IR('missing_n'), IR('price'), IR('missing_n'), IR('price'), IR('item_id'))), 8),
    CA('rcon', 'Rank, contents by room', 'int', GI('1+COUNTIFS(%s,"<"&{col:room})+COUNTIFS(%s,{col:room},%s,">"&{col:price})+COUNTIFS(%s,{col:room},%s,{col:price},%s,"<"&{col:item_id})' % (
        IR('room'), IR('room'), IR('price'), IR('room'), IR('price'), IR('item_id'))), 8),
    CA('rrec', 'Rank, recent purchases', 'int', RK('AND({col:item_id}<>"",{col:purchase_date}<>"",{col:purchase_date}>={today}-730)', 'COUNTIFS(%s,">"&{col:purchase_date})+COUNTIFS(%s,{col:purchase_date},%s,"<"&{col:item_id})' % (
        IR('purchase_date'), IR('purchase_date'), IR('item_id'))), 8),
    CA('rold', 'Rank, oldest first', 'int', RK('AND({col:item_id}<>"",{col:purchase_date}<>"")', 'COUNTIFS(%s,"<"&{col:purchase_date})+COUNTIFS(%s,{col:purchase_date},%s,"<"&{col:item_id})' % (
        IR('purchase_date'), IR('purchase_date'), IR('item_id'))), 8),
    CA('okey', 'Oldest key (room and age rank)', 'text', GI('IF({col:purchase_date}="","",{col:room}&"|"&(1+COUNTIFS(%s,{col:room},%s,"<"&{col:purchase_date})+COUNTIFS(%s,{col:room},%s,{col:purchase_date},%s,"<"&{col:item_id})))' % (
        IR('room'), IR('purchase_date'), IR('room'), IR('purchase_date'), IR('item_id'))), 14),
    HOUSE('{col:item_id}')]
for code, lab in (('a1', 'Adult 1'), ('a2', 'Adult 2'), ('c1', 'Child 1'), ('c2', 'Child 2'), ('gp', 'Grandparent'), ('bs', 'Babysitter'), ('cp', 'Carpool family'), ('nb', 'Neighbour'), ('so', 'School office')):
    inv_cols.append(PH(code, lab, '{col:item_id}'))
tables.append(T('inventory', 'Inventory', 'Home inventory: every item with price, serial, warranty end, receipt and manual',
    'One row per item you own: room, category, purchase date, price, serial, warranty end from your paperwork, receipt date, manual place; age, days left and status fill in. Renters list their own.',
    inv_cols, D.inventory_d(), 250, [A('status', '= ' + W_EXP, 'bad'), A('status', '= ' + W_SOON, 'warn'), A('status', '= ' + W_COV, 'good'), A('open_rep', '> 0', 'warn')]))

# 3 repairs ---------------------------------------------------------------------
def GR(f): return 'IF({col:repair_id}="","",%s)' % f
rep_cols = [
    C('repair_id', 'Repair ID', 'text', 9, required=True), C('date', 'Fault date', 'date', 11), LST('room', 'Room', 'room', 14), C('issue', 'Issue', 'text', 34), LST('trade', 'Trade', 'trade', 17),
    C('quote', 'Quote', 'money', 10), C('cost', 'Cost', 'money', 10), LST('status', 'Status', 'rstatus', 10), C('fixed_on', 'Fixed on', 'date', 11), C('warranty_used', 'Warranty used', 'bool', 9),
    REF('item_id', 'Item ID', 'inventory.item_id', 9),
    CA('open', 'Open or waiting, 1 or 0', 'int', GR('IF(OR({col:status}=%s,{col:status}=%s),1,0)' % (OPEN, WAIT)), 8),
    CA('linked', 'Linked to an item, 1 or 0', 'int', GR('IF({col:item_id}="",0,1)'), 8),
    CA('item_name', 'Item', 'text', GR('IF({col:item_id}="","",IFERROR(INDEX(%s,MATCH({col:item_id},%s,0))&"",""))' % (IR('item'), IR('item_id'))), 24),
    CA('w_end', 'Warranty end of the item', 'date', GR('IF({col:item_id}="","",IFERROR(IF(INDEX(%s,MATCH({col:item_id},%s,0))=0,"",INDEX(%s,MATCH({col:item_id},%s,0))),""))' % (IR('warranty_end'), IR('item_id'), IR('warranty_end'), IR('item_id'))), 12),
    CA('days_w', 'Days of warranty left', 'int', GR('IF({col:w_end}="","",{col:w_end}-{today})'), 9),
    CA('inwarr', 'Fault inside the warranty, 1 or 0', 'int', GR('IF({col:w_end}="","",IF({col:date}<={col:w_end},1,0))'), 9),
    CA('claim', 'On the claims list, 1 or 0', 'int', GR('IF(OR({col:warranty_used}=%s,{col:linked}=1),1,0)' % YES), 8),
    CA('cstatus', 'Claim status', 'text', GR('IF({col:claim}<>1,"",IF(AND({col:open}=1,{col:days_w}<>"",{col:days_w}>=0),%s,IF({col:warranty_used}=%s,%s,IF({col:inwarr}=1,%s,%s))))' % (W_OPENW, YES, W_USED, W_INSIDE, W_OUTSIDE)), 20),
    CA('claim_open', 'Open fault in warranty, 1 or 0', 'int', GR('IF({col:cstatus}=%s,1,0)' % W_OPENW), 8),
    CA('crk', 'Claim rank, latest first', 'int', 'IF({col:claim}=1,1+COUNTIFS(%s,1,%s,">"&{col:date})+COUNTIFS(%s,1,%s,{col:date},%s,"<"&{col:repair_id}),"")' % (RR('claim'), RR('date'), RR('claim'), RR('date'), RR('repair_id')), 8)]
rep_cols += NPS('ar', 'Appliance repairer', '{col:repair_id}') + NP('ll', 'Landlord or agent', '{col:repair_id}') + NP('pl', 'Plumber', '{col:repair_id}') + NP('el', 'Electrician', '{col:repair_id}') + NPS('hm', 'Handyman', '{col:repair_id}') + NP('cm', 'Car mechanic', '{col:repair_id}') + [
    CA('serial', 'Serial of the item', 'text', GR('IF({col:item_id}="","",IFERROR(INDEX(%s,MATCH({col:item_id},%s,0))&"",""))' % (IR('serial'), IR('item_id'))), 16), HOUSE('{col:repair_id}')]
tables.append(T('repairs', 'Repairs', 'Repairs log with the item it belongs to',
    'One row per repair: fault date, room, issue, trade, quote, cost, status and the item ID when it is an inventory item; the warranty at the fault date and the claim status fill in. Self repair is a trade too.',
    rep_cols, D.repairs_d(), 150, [A('status', '= ' + OPEN, 'warn'), A('status', '= ' + WAIT, 'warn'), A('status', '= ' + FIXED, 'good'), A('cstatus', '= ' + W_OPENW, 'bad')]))

# 4 replacement prices ----------------------------------------------------------
IPOS = 'MATCH({col:item},%s,0)' % IR('item')
def GRI(f): return 'IF({col:item}="","",%s)' % f
tables.append(T('replace', 'Replacement prices', 'Typed replacement price and typical years of use for the big items',
    'One row per big item: type the price you would pay today and the typical years of use as a household note (check the manual); the item ID, age and years left fill in. Not a promise of how long it lasts.', [
    LST('item', 'Item', 'ritem', 26, required=True), C('replacement_price', 'Replacement price', 'money', 12), C('typical_years', 'Typical years of use', 'int', 10),
    CA('item_id', 'Item ID', 'text', GRI('IFERROR(INDEX(%s,%s)&"","")' % (IR('item_id'), IPOS)), 9),
    CA('age_years', 'Age, years', 'num', GRI('IFERROR(INDEX(%s,%s),"")' % (IR('age_years'), IPOS)), 8),
    CA('years_left', 'Typical years left', 'num', GRI('IF({col:age_years}="","",{col:typical_years}-{col:age_years})'), 9),
    CA('past_typ', 'At or past the typical years, 1 or 0', 'int', GRI('IF({col:years_left}="","",IF({col:years_left}<=0,1,0))'), 9)], D.replace_d(), 40))

# 5 warranty countdown (ranked, all items) --------------------------------------
def MR(rank_col): return CA('mr', 'Row in Inventory', 'int', 'IFERROR(MATCH({col:no},%s,0),"")' % IR(rank_col), 8)
def IX(c, as_text=False): return 'IF({col:mr}="","",INDEX(%s,{col:mr})%s)' % (IR(c), '&""' if as_text else '')
def IXD(c): return 'IF({col:mr}="","",IF(INDEX(%s,{col:mr})=0,"",INDEX(%s,{col:mr})))' % (IR(c), IR(c))
tables.append(T('countdown', 'Warranty countdown', 'Every item with the days of warranty left, soonest end first',
    'Type the rank numbers 1 to 120 once; every item appears with its warranty end, the days left and the status, the soonest end first, then expired, then none typed. Calculated from your entries.', [
    C('no', 'Rank', 'int', 7, required=True), MR('wrk'), CA('item', 'Item', 'text', IX('item', True), 26), CA('room', 'Room', 'text', IX('room', True), 14), CA('warranty_end', 'Warranty end', 'date', IXD('warranty_end'), 12),
    CA('days_left', 'Days left', 'int', IX('days_left'), 8), CA('status', 'Status', 'text', IX('status', True), 13)], D.nos(120), 150, [A('status', '= ' + W_EXP, 'bad'), A('status', '= ' + W_SOON, 'warn'), A('status', '= ' + W_COV, 'good')]))

# 6 warranties ending soon (ranked) ---------------------------------------------
tables.append(T('ending90', 'Warranties ending in 90 days', 'Warranties ending soon, nearest first, open repairs flagged',
    'Type the rank numbers 1 to 15 once; items whose warranty ends within the soon window set in Settings appear, nearest first, with the days left and whether a repair is open on them.', [
    C('no', 'Rank', 'int', 7, required=True), MR('r90'), CA('item', 'Item', 'text', IX('item', True), 26), CA('room', 'Room', 'text', IX('room', True), 14), CA('warranty_end', 'Warranty end', 'date', IXD('warranty_end'), 12),
    CA('days_left', 'Days left', 'int', IX('days_left'), 8), CA('open', 'Open repair', 'text', 'IF({col:mr}="","",IF(INDEX(%s,{col:mr})>0,%s,%s))' % (IR('open_rep'), W_YES, W_NO), 10),
    CA('price', 'Price', 'money', IX('price'), 10), CA('n90', 'Warranties ending soon', 'int', 'IF({col:mr}="","",COUNTIFS(%s,">=0",%s,"<="&{set:warranty_days}))' % (IR('days_left'), IR('days_left')), 9)] + NP('a1', 'Adult 1', '{col:mr}') + [HOUSE('{col:mr}')],
    D.nos(15), 30, [A('open', '= ' + W_YES, 'bad'), A('days_left', '<= 30', 'warn')]))

# 7 expired (ranked) ------------------------------------------------------------
tables.append(T('expired', 'Expired warranties', 'Warranties that have ended, the latest first',
    'Type the rank numbers 1 to 25 once; the items whose warranty has ended appear, the most recent first, with the days since and the price. Calculated from the dates you typed.', [
    C('no', 'Rank', 'int', 7, required=True), MR('rex'), CA('item', 'Item', 'text', IX('item', True), 26), CA('room', 'Room', 'text', IX('room', True), 14), CA('warranty_end', 'Warranty end', 'date', IXD('warranty_end'), 12),
    CA('days_since', 'Days since it ended', 'int', 'IF({col:mr}="","",-INDEX(%s,{col:mr}))' % IR('days_left'), 9), CA('price', 'Price', 'money', IX('price'), 10)], D.nos(25), 40))

# 8 missing receipts and manuals (ranked) ---------------------------------------
tables.append(T('missing', 'Receipts and manuals missing', 'Items with no receipt date, no manual or no serial, most gaps first',
    'Type the rank numbers 1 to 30 once; items with a gap appear, the most gaps first, then the dearest. Each flag is 1 when it is missing; fill the yellow cells in Inventory and the row drops out.', [
    C('no', 'Rank', 'int', 7, required=True), MR('rmiss'), CA('item', 'Item', 'text', IX('item', True), 26), CA('room', 'Room', 'text', IX('room', True), 14),
    CA('no_receipt', 'Receipt missing, 1 or 0', 'int', IX('no_receipt'), 9), CA('no_manual', 'Manual missing, 1 or 0', 'int', IX('no_manual'), 9), CA('no_serial', 'Serial missing, 1 or 0', 'int', IX('no_serial'), 9),
    CA('fields', 'Fields to fill', 'int', IX('missing_n'), 8), CA('price', 'Price', 'money', IX('price'), 10), CA('n_no_receipt', 'Items without a receipt date', 'int', 'IF({col:mr}="","",SUM(%s))' % IR('no_receipt'), 9)] +
    NP('a2', 'Adult 2', '{col:mr}') + [HOUSE('{col:mr}')], D.nos(30), 40, [A('fields', '= 3', 'bad')]))

# 9 value by room, 10 value by category, 11 purchases by year -------------------
tables.append(T('val_room', 'Value by room', 'Items and the typed value of each room',
    'One row per room; the items and the total of the prices you typed fill in. A sum of your own typed cost lines, not an appraisal.', [
    LST('room', 'Room', 'room', 16, required=True), CA('items', 'Items', 'int', 'COUNTIFS(%s,{col:room})' % IR('room'), 8), CA('total', 'Total price', 'money', 'SUMIFS(%s,%s,{col:room})' % (IR('price'), IR('room')), 12)], D.val_room_d(), 30))
tables.append(T('val_cat', 'Value by category', 'Items and the typed value of each category',
    'One row per category; the items and the total of the typed prices fill in. A sum of your own cost lines.', [
    LST('category', 'Category', 'icat', 18, required=True), CA('items', 'Items', 'int', 'COUNTIFS(%s,{col:category})' % IR('category'), 8), CA('total', 'Total price', 'money', 'SUMIFS(%s,%s,{col:category})' % (IR('price'), IR('category')), 12)], D.val_cat_d(), 30))
YR = 'VALUE({col:yk})'
def INYEAR(extra=''): return '%s,">="&DATE(%s,1,1),%s,"<="&DATE(%s,12,31)%s' % (IR('purchase_date'), YR, IR('purchase_date'), YR, extra)
tables.append(T('by_year', 'Purchases by year', 'Items bought and the typed price by purchase year',
    'One row per year (the last 11 years); the items bought and the total of their typed prices fill in. Edit the years on the Lists sheet.', [
    LST('yk', 'Purchase year', 'pyear', 12, required=True), CA('items', 'Items', 'int', 'COUNTIFS(%s)' % INYEAR(), 8), CA('total', 'Total price', 'money', 'SUMIFS(%s,%s)' % (IR('price'), INYEAR()), 12)], D.by_year_d(), 30))

# 12 age bands, 13 price bands ---------------------------------------------------
A_ = IR('age_years'); B_ = lambda x: tok('aband', x)
def BANDF(fn, extra):
    parts = [('Under 1 year', '%s,"<1"'), ('1 to 2 years', '%s,">=1",%s,"<2"'), ('2 to 4 years', '%s,">=2",%s,"<4"'), ('4 to 6 years', '%s,">=4",%s,"<6"'), ('6 to 8 years', '%s,">=6",%s,"<8"')]
    out = fn(A_, '%s,">=8"' % A_)
    for lab, c in reversed(parts):
        out = 'IF({col:band}=%s,%s,%s)' % (B_(lab), fn(A_, c.replace('%s', A_)), out)
    return out
cnt = lambda a, c: 'COUNTIFS(%s)' % c
sm = lambda a, c: 'SUMIFS(%s,%s)' % (IR('price'), c)
tables.append(T('age_band', 'Items by age band', 'Items and the typed value by age of the item',
    'One row per age band; the items and their typed total fill in from the purchase dates. Age is calculated from your entries.', [
    LST('band', 'Age band', 'aband', 18, required=True), CA('items', 'Items', 'int', BANDF(cnt, ''), 8), CA('total', 'Total price', 'money', BANDF(sm, ''), 12)], D.age_band_d(), 20))
P_ = IR('price')
def PBAND(fn):
    spec = [('Under 50', '%s,"<50"'), ('50 to 99', '%s,">=50",%s,"<100"'), ('100 to 249', '%s,">=100",%s,"<250"'), ('250 to 499', '%s,">=250",%s,"<500"'), ('500 to 999', '%s,">=500",%s,"<1000"')]
    out = fn(P_, '%s,">=1000"' % P_)
    for lab, c in reversed(spec): out = 'IF({col:band}=%s,%s,%s)' % (tok('pband', lab), fn(P_, c.replace('%s', P_)), out)
    return out
tables.append(T('price_band', 'Items by price band', 'Items and their typed total by price band',
    'One row per price band; the items and their typed total fill in. Edit the bands on the Lists sheet only if you also change the formulas.', [
    LST('band', 'Price band', 'pband', 18, required=True), CA('items', 'Items', 'int', PBAND(cnt), 8), CA('total', 'Total price', 'money', PBAND(sm), 12)], D.price_band_d(), 20))

# 14 repair or replace view -----------------------------------------------------
RP = lambda c: 'IFERROR(INDEX(%s,MATCH({col:item},%s,0)),"")' % (PR(c), PR('item'))
tables.append(T('repair_view', 'Repair or replace view', 'Repairs logged against the typed replacement price, one row per big item',
    'One row per big item; the age, the repairs logged, the repair cost lines and the share of the replacement price fill in, with a verdict against your own rule in Settings. A view, not advice.', [
    LST('item', 'Item', 'ritem', 26, required=True),
    CA('item_id', 'Item ID', 'text', GRI('IFERROR(INDEX(%s,%s)&"","")' % (IR('item_id'), IPOS)), 9), CA('age_years', 'Age, years', 'num', GRI('IFERROR(INDEX(%s,%s),"")' % (IR('age_years'), IPOS)), 8),
    CA('repairs', 'Repairs logged', 'int', GRI('IFERROR(INDEX(%s,%s),0)' % (IR('rep_n'), IPOS)), 8), CA('repair_cost', 'Repair cost lines', 'money', GRI('IFERROR(INDEX(%s,%s),0)' % (IR('rep_cost'), IPOS)), 11),
    CA('replacement', 'Replacement price', 'money', GRI('IF(%s=0,"",%s)' % (RP('replacement_price'), RP('replacement_price'))), 11),
    CA('share', 'Repairs as a share of the price', 'pct', GRI('IF({col:replacement}="","",IF({col:replacement}>0,{col:repair_cost}/{col:replacement},""))'), 10),
    CA('verdict', 'Verdict', 'text', GRI('IF({col:replacement}="",%s,IF({col:repairs}=0,%s,IF({col:share}>={set:repair_rule},%s,IF({col:share}>={set:repair_rule}/2,%s,%s))))' % (W_NOPRICE, W_NOREP, W_REPLACE, W_WATCH, W_REPAIR)), 15),
    CA('with_rep', 'Has repairs, 1 or 0', 'int', GRI('IF({col:repairs}>0,1,0)'), 8),
    CA('under', 'Under your rule, 1 or 0', 'int', GRI('IF({col:with_rep}=1,IF({col:share}="",1,IF({col:share}<{set:repair_rule},1,0)),0)'), 8),
    CA('rk', 'Rank by repair cost lines', 'int', 'IF({col:with_rep}=1,1+COUNTIFS(%s,1,%s,">"&{col:repair_cost})+COUNTIFS(%s,1,%s,{col:repair_cost},%s,"<"&{col:item}),"")' % (VR('with_rep'), VR('repair_cost'), VR('with_rep'), VR('repair_cost'), VR('item')), 8)],
    D.repair_view_d(), 40, [A('verdict', '= ' + W_REPLACE, 'bad'), A('verdict', '= ' + W_WATCH, 'warn'), A('verdict', '= ' + W_REPAIR, 'good')]))

# 15 repairs by item (ranked) ---------------------------------------------------
def VI(c): return 'IF({col:mr}="","",INDEX(%s,{col:mr}))' % VR(c)
tables.append(T('repair_item', 'Repairs by item', 'Items with repairs logged, the dearest repair cost lines first',
    'Type the rank numbers 1 to 15 once; items with repairs appear by repair cost lines with the repairs, the cost and the share of the replacement price you typed.', [
    C('no', 'Rank', 'int', 7, required=True), CA('mr', 'Row in the view', 'int', 'IFERROR(MATCH({col:no},%s,0),"")' % VR('rk'), 8), CA('item', 'Item', 'text', 'IF({col:mr}="","",INDEX(%s,{col:mr})&"")' % VR('item'), 26),
    CA('repairs', 'Repairs logged', 'int', VI('repairs'), 8), CA('repair_cost', 'Repair cost lines', 'money', VI('repair_cost'), 11), CA('share', 'Share of the price', 'pct', VI('share'), 9)], D.nos(15), 30))

# 16 contents list by room (ranked, printable) ----------------------------------
tables.append(T('contents', 'Contents list by room', 'Printable contents list: every item by room, the dearest first',
    'Type the rank numbers 1 to 120 once; every item appears room by room with its price, purchase date and serial. Print it for a walk-through or a move.', [
    C('no', 'Rank', 'int', 7, required=True), MR('rcon'), CA('room', 'Room', 'text', IX('room', True), 14), CA('item', 'Item', 'text', IX('item', True), 26), CA('price', 'Price', 'money', IX('price'), 10),
    CA('purchase_date', 'Purchase date', 'date', IXD('purchase_date'), 12), CA('serial', 'Serial number', 'text', IX('serial', True), 16),
    CA('room_items', 'Items in the room', 'int', 'IF({col:mr}="","",COUNTIFS(%s,{col:room}))' % IR('room'), 8), CA('room_total', 'Typed value of the room', 'money', 'IF({col:mr}="","",SUMIFS(%s,%s,{col:room}))' % (IR('price'), IR('room')), 11),
    CA('walk_date', 'Walk-through on (next Sunday)', 'date', 'IF({col:mr}="","",{today}+MOD(7-WEEKDAY({today},2),7))', 11)] + NP('a2', 'Adult 2', '{col:mr}') + NP('a1', 'Adult 1', '{col:mr}') + [HOUSE('{col:mr}')], D.nos(120), 150))

# 17 manual locations ------------------------------------------------------------
tables.append(T('manuals', 'Manual locations', 'Where the manuals are kept and how many items each place holds',
    'One row per place; the items whose manual is there and how many of them have a serial typed fill in. None kept counts the items with no manual.', [
    LST('place', 'Manual place', 'kept', 30, required=True), CA('items', 'Items', 'int', 'COUNTIFS(%s,{col:place})' % IR('manual_place'), 8),
    CA('with_serial', 'With a serial', 'int', 'COUNTIFS(%s,{col:place},%s,0)' % (IR('manual_place'), IR('no_serial')), 9)], D.manuals_d(), 20))

# 18 warranty claims (ranked) ----------------------------------------------------
def CI(c): return 'IF({col:mr}="","",INDEX(%s,{col:mr}))' % RR(c)
tables.append(T('claims', 'Warranty claims', 'Repairs linked to an item or marked warranty used, the latest first',
    'Type the rank numbers 1 to 12 once; repairs with an item ID or the warranty-used tick appear with the fault date, the warranty end and the claim status. Calculated from the Repairs sheet.', [
    C('no', 'Rank', 'int', 7, required=True), CA('mr', 'Row in Repairs', 'int', 'IFERROR(MATCH({col:no},%s,0),"")' % RR('crk'), 8), CA('repair_id', 'Repair ID', 'text', 'IF({col:mr}="","",INDEX(%s,{col:mr})&"")' % RR('repair_id'), 9),
    CA('item', 'Item or issue', 'text', 'IF({col:mr}="","",IF(INDEX(%s,{col:mr})<>"",INDEX(%s,{col:mr}),INDEX(%s,{col:mr})&""))' % (RR('item_name'), RR('item_name'), RR('issue')), 30),
    CA('fault_date', 'Fault date', 'date', CI('date'), 11), CA('warranty_end', 'Warranty end', 'date', CI('w_end'), 12), CA('days_left', 'Days of warranty left', 'int', CI('days_w'), 9),
    CA('status', 'Claim status', 'text', 'IF({col:mr}="","",INDEX(%s,{col:mr})&"")' % RR('cstatus'), 20)], D.nos(12), 20, [A('status', '= ' + W_OPENW, 'bad'), A('status', '= ' + W_USED, 'good')]))

# 19 warranty end by month -------------------------------------------------------
WEND = IR('warranty_end')
tables.append(T('warr_month', 'Warranty end by month', 'Warranties ending in each of the next 12 months',
    'Type 0 to 12 once, with the month label; the month, the warranties ending and the typed price covered fill in. This month counts from today.', [
    C('mk', 'Months ahead', 'int', 8, required=True), LST('ahead', 'Month ahead', 'ahead13', 13), CA('month', 'Month', 'date', 'EDATE(%s,{col:mk})' % FIRST, 11),
    CA('ends', 'Warranties ending', 'int', 'COUNTIFS(%s,">="&MAX({col:month},{today}),%s,"<"&EDATE({col:month},1))' % (WEND, WEND), 9),
    CA('price', 'Price covered', 'money', 'SUMIFS(%s,%s,">="&MAX({col:month},{today}),%s,"<"&EDATE({col:month},1))' % (IR('price'), WEND, WEND), 11)], D.warr_month_d(), 20, [A('ends', '> 0', 'warn')]))

# 20 recent purchases (ranked) ---------------------------------------------------
tables.append(T('recent', 'Recent purchases', 'Items bought in the last 24 months, the latest first',
    'Type the rank numbers 1 to 20 once; the latest purchases appear with the price, the warranty end and the days left, with the year totals used by the year-review text.', [
    C('no', 'Rank', 'int', 7, required=True), MR('rrec'), CA('item', 'Item', 'text', IX('item', True), 26), CA('purchase_date', 'Purchase date', 'date', IXD('purchase_date'), 12), CA('price', 'Price', 'money', IX('price'), 10),
    CA('warranty_end', 'Warranty end', 'date', IXD('warranty_end'), 12), CA('days_left', 'Days left', 'int', IX('days_left'), 8),
    CA('year', 'Purchase year', 'int', 'IF({col:mr}="","",YEAR({col:purchase_date}))', 9),
    CA('year_items', 'Items bought that year', 'int', 'IF({col:mr}="","",COUNTIFS(%s,">="&DATE({col:year},1,1),%s,"<="&DATE({col:year},12,31)))' % (IR('purchase_date'), IR('purchase_date')), 9),
    CA('year_value', 'Typed value bought that year', 'money', 'IF({col:mr}="","",SUMIFS(%s,%s,">="&DATE({col:year},1,1),%s,"<="&DATE({col:year},12,31)))' % (IR('price'), IR('purchase_date'), IR('purchase_date')), 11)] +
    NP('a1', 'Adult 1', '{col:mr}') + [HOUSE('{col:mr}')], D.nos(20), 30))
for _t in tables: _t['rows'] = max(50, _t['rows'])
assert len(tables) == 20, len(tables)

_TX = {('inventory', 'title'): 'Home inventory: price, serial, warranty end, receipt, manual',
       ('repairs', 'hint'): 'One row per repair: fault date, room, issue, trade, quote, cost, status and the item ID when it is an inventory item; the warranty at the fault date and the claim status fill in.',
       ('replace', 'title'): 'Typed replacement price and typical years for the big items',
       ('replace', 'hint'): 'One row per big item: type the price you would pay today and the typical years of use as a household note (check the manual); the item ID, age and years left fill in.',
       ('ending90', 'title'): 'Warranties ending soon, nearest first, open repairs flagged',
       ('missing', 'title'): 'Items with no receipt, manual or serial, most gaps first',
       ('repair_view', 'title'): 'Repairs against the typed replacement price, per big item',
       ('repair_item', 'title'): 'Items with repairs logged, dearest repair cost lines first',
       ('contents', 'title'): 'Printable contents list: every item by room',
       ('manuals', 'title'): 'Where the manuals are kept and how many items each holds',
       ('claims', 'title'): 'Repairs linked to an item or warranty used, latest first'}
for t in tables:
    for (k, f), v in _TX.items():
        if t['key'] == k: t[f] = v
    if not (len(t['title']) <= 60 and len(t['hint']) <= 200): print('LONG', t['key'], len(t['title']), len(t['hint']))
