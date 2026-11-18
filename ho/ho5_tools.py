"""Home Management suite part 5: the 18 decision tools (each with a verdict, the numbers behind it and a what-if grid where the inputs are numbers)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho5_lists import *
import ho5_data as D
from ho5_tables import *


def GRD(title, *rows): return {"title": title, "rows": [{"label": l, "values": v} for l, v in rows]}
def I(k, label, d, t='int', **kw): return IN(k, label, t, d, **kw)
def IL(k, label, lst, dflt): return IN(k, label, 'list', key(lst, dflt), list=lst)
def O(label, fmt, f): return OUT(label, fmt, f)
def V(*parts):
    """a verdict: words (list labels) and numbers or names joined with spaces; a tuple ('f', formula) is a value"""
    out = []
    for p in parts:
        if isinstance(p, tuple): out.append('(' + p[1] + ')')
        else: out.append(lbl(p))
    return '&" "&'.join(out)
def F(x): return ('f', x)
def MNAME(expr): return 'CHOOSE(%s,%s)' % (expr, ','.join(tok('mname', m) for m in MONTH_NAMES))
def PCT(x): return 'ROUND(%s*100,0)&"%%"' % x


POS = 'MATCH({in:item},%s,0)' % IR('item')
FOUND = 'ISNUMBER(%s)' % POS
NOTF = lbl('Type an item as written in Inventory')
def X(c): return 'IFERROR(INDEX(%s,%s),"")' % (IR(c), POS)
def XT(c): return 'IFERROR(INDEX(%s,%s)&"","")' % (IR(c), POS)
def XD(c): return 'IFERROR(IF(INDEX(%s,%s)=0,"",INDEX(%s,%s)),"")' % (IR(c), POS, IR(c), POS)
def NF(good): return 'IF(NOT(%s),%s,%s)' % (FOUND, NOTF, good)
def Z(x): return 'IF(%s="",0,%s)' % (x, x)
tools = []

# 1 ---------------------------------------------------------------- warranty countdown
DL1 = X('days_left')
tools.append(TOOL('warranty_count', 'Warranty Countdown Tool', 'How many days of warranty are left on one item',
    'Type an item as written in Inventory: the warranty end you typed, the days left or the days since it ended and the status. Warranty lengths are never assumed: check your paperwork.', [
    I('item', 'Item, as written in Inventory', 'Washing machine', 'text'), I('window', 'Ending soon: within this many days', 90)], [
    O('Item found', 'text', XT('item')), O('Room', 'text', XT('room')), O('Purchase date', 'date', XD('purchase_date')), O('Warranty end typed', 'date', XD('warranty_end')),
    O('Days of warranty left, negative is ended', 'int', DL1), O('Open repairs on the item', 'int', X('open_rep')),
    O('Status', 'text', 'IF(NOT(%s),"",IF(%s="",%s,IF(%s<0,%s,IF(%s<={in:window},%s,%s))))' % (FOUND, DL1, W_NONE, DL1, W_EXP, DL1, W_SOON, W_COV)),
    O('Verdict', 'text', NF('IF(%s="",%s,IF(%s>=0,%s,%s))' % (DL1, lbl('No warranty typed'), DL1, V(F(DL1), 'days of warranty left'), V('Expired', F('-' + DL1), 'days ago'))))],
    GRD('What if the ending soon window changes', ('30 days', {'window': 30}), ('60 days', {'window': 60}), ('90 days', {'window': 90}), ('120 days', {'window': 120}), ('180 days', {'window': 180}))))

# 2 ---------------------------------------------------------------- warranties ending in 90 days
N2 = 'COUNTIFS(%s,">=0",%s,"<="&{in:within})' % (IR('days_left'), IR('days_left'))
NEAR2 = 'IFERROR(SMALL(%s,COUNTIF(%s,"<0")+1),"")' % (IR('days_left'), IR('days_left'))
M2 = 'MATCH(%s,%s,0)' % (NEAR2, IR('days_left'))
tools.append(TOOL('ending_soon', 'Warranties Ending Soon Tool', 'Which warranties end in the next days, nearest first',
    'The items whose warranty ends within the days you type, their typed value, how many have an open repair and the nearest end: check these before the warranty runs out.', [
    I('within', 'Look this many days ahead', 90)], [
    O('Warranties ending in the window', 'int', N2), O('Typed value of those items', 'money', 'SUMIFS(%s,%s,">=0",%s,"<="&{in:within})' % (IR('price'), IR('days_left'), IR('days_left'))),
    O('With an open repair', 'int', 'COUNTIFS(%s,">=0",%s,"<="&{in:within},%s,">0")' % (IR('days_left'), IR('days_left'), IR('open_rep'))),
    O('Nearest item', 'text', 'IF(%s=0,"",IFERROR(INDEX(%s,%s)&"",""))' % (N2, IR('item'), M2)), O('Its room', 'text', 'IF(%s=0,"",IFERROR(INDEX(%s,%s)&"",""))' % (N2, IR('room'), M2)),
    O('Its warranty end', 'date', 'IF(%s=0,"",IFERROR(INDEX(%s,%s),""))' % (N2, IR('warranty_end'), M2)), O('Days left on it', 'int', 'IF(%s=0,"",%s)' % (N2, NEAR2)),
    O('Ending in the urgent window of Settings', 'int', 'COUNTIFS(%s,">=0",%s,"<="&{set:urgent_days})' % (IR('days_left'), IR('days_left'))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (N2, lbl('Nothing ends in this window'), V('Check', F('INDEX(%s,%s)' % (IR('item'), M2)), 'in', F(NEAR2), 'days,', F(N2), 'warranties end in all')))],
    GRD('What if you look closer or further', ('14 days', {'within': 14}), ('30 days', {'within': 30}), ('60 days', {'within': 60}), ('90 days', {'within': 90}), ('180 days', {'within': 180}), ('365 days', {'within': 365}))))

# 3 ---------------------------------------------------------------- open fault against the warranty
OL = IR('open_left')
NEAR3 = 'IFERROR(SMALL(%s,1),"")' % OL
M3 = 'MATCH(%s,%s,0)' % (NEAR3, OL)
ID3 = 'INDEX(%s,%s)' % (IR('item_id'), M3)
FAULT3 = 'SUMPRODUCT(MAX((%s=%s)*((%s=%s)+(%s=%s))*%s))' % (RR('item_id'), ID3, RR('status'), OPEN, RR('status'), WAIT, RR('date'))
OPENN = 'COUNTIFS(%s,">0")' % IR('open_rep')
INW = 'COUNTIFS(%s,">=0")' % OL
tools.append(TOOL('open_fault', 'Open Fault Against Warranty', 'Which open repair sits on an item that is still under warranty',
    'Items with an open or waiting repair and the days of warranty left: report the fault before the warranty ends; type the days a repairer needs to book a visit.', [
    I('visit', 'Days a repairer needs to book a visit', 21)], [
    O('Items with an open repair', 'int', OPENN), O('Of them still under warranty', 'int', INW), O('Item with the least warranty left', 'text', 'IF(%s=0,"",IFERROR(INDEX(%s,%s)&"",""))' % (INW, IR('item'), M3)),
    O('Its warranty end', 'date', 'IF(%s=0,"",IFERROR(INDEX(%s,%s),""))' % (INW, IR('warranty_end'), M3)), O('Days of warranty left', 'int', 'IF(%s=0,"",%s)' % (INW, NEAR3)),
    O('Fault logged on', 'date', 'IF(%s=0,"",%s)' % (INW, FAULT3)), O('Days since the fault was logged', 'int', 'IF(%s=0,"",{today}-%s)' % (INW, FAULT3)),
    O('Days left after a visit is booked', 'int', 'IF(%s=0,"",%s-{in:visit})' % (INW, NEAR3)),
    O('Verdict', 'text', 'IF(%s=0,%s,IF(%s=0,%s,IF(%s>{in:visit},%s,%s)))' % (OPENN, lbl('No open repairs'), INW, lbl('Open repairs are outside any warranty'),
        NEAR3, V('Report', F('INDEX(%s,%s)' % (IR('item'), M3)), 'within', F('%s-{in:visit}' % NEAR3), 'days,', F(NEAR3), 'days left'), V('Report', F('INDEX(%s,%s)' % (IR('item'), M3)), 'now, only', F(NEAR3), 'days left')))],
    GRD('What if a visit takes longer', ('7 days', {'visit': 7}), ('14 days', {'visit': 14}), ('21 days', {'visit': 21}), ('30 days', {'visit': 30}), ('45 days', {'visit': 45}))))

# 4 ---------------------------------------------------------------- where is the manual and receipt
tools.append(TOOL('where_manual', 'Where Is The Manual', 'Where are the manual, the receipt and the serial number of one item',
    'Type an item as written in Inventory: its room, serial number, receipt date and where the manual is kept; the verdict says where to look or what to add.', [
    I('item', 'Item, as written in Inventory', 'Washing machine', 'text')], [
    O('Item found', 'text', XT('item')), O('Room', 'text', XT('room')), O('Serial number', 'text', XT('serial')), O('Purchase date', 'date', XD('purchase_date')), O('Receipt date', 'date', XD('receipt_date')),
    O('Manual place', 'text', XT('manual_place')), O('Price', 'money', X('price')), O('Items with the manual in the same place', 'int', 'IFERROR(COUNTIFS(%s,INDEX(%s,%s)),"")' % (IR('manual_place'), IR('manual_place'), POS)),
    O('Fields still to fill, 0 to 3', 'int', X('missing_n')),
    O('Verdict', 'text', NF('IF(OR(%s="",%s=%s),%s,%s)' % (X('manual_place'), XT('manual_place'), NONEKEPT, lbl('Add a location'), V('Found in', F(XT('manual_place'))))))]))

# 5 ---------------------------------------------------------------- replace or repair
CST5 = Z(X('rep_cost'))
SH5 = 'IF({in:replacement}>0,(%s+{in:quote})/{in:replacement},0)' % CST5
tools.append(TOOL('repair_replace', 'Replace Or Repair Tool', 'Do the repairs so far pass your own rule for replacing one item',
    'Type an item, the replacement price you would pay and your rule: the repair cost lines from Repairs as a share of that price; a view against your own rule, not advice.', [
    I('item', 'Item, as written in Inventory', 'Dishwasher', 'text'), I('replacement', 'Replacement price', 370, 'money'), I('rule', 'Your rule: replace at this share', 0.5, 'pct'), I('quote', 'Quote for the next repair', 0, 'money')], [
    O('Age, years', 'num', X('age_years')), O('Repairs logged', 'int', X('rep_n')), O('Repair cost lines so far', 'money', CST5), O('With the next quote', 'money', '%s+{in:quote}' % CST5),
    O('Share of the replacement price so far', 'pct', 'IF({in:replacement}>0,%s/{in:replacement},0)' % CST5), O('Share with the next quote', 'pct', SH5),
    O('Repair cost lines left before the rule', 'money', 'MAX(0,{in:rule}*{in:replacement}-%s-{in:quote})' % CST5),
    O('Verdict', 'text', NF('IF({in:replacement}<=0,%s,IF(%s>={in:rule},%s,%s))' % (lbl('Type a replacement price'), SH5, V('Replace: repairs are', F(PCT(SH5)), 'of the price'), V('Repair: repairs are', F(PCT(SH5)), 'of the price'))))],
    GRD('What if the price or the rule changes', ('Price 300', {'replacement': 300}), ('Price 370', {'replacement': 370}), ('Price 450', {'replacement': 450}), ('Price 600', {'replacement': 600}), ('Rule 40%', {'rule': 0.4}), ('Rule 60%', {'rule': 0.6}))))

# 6 ---------------------------------------------------------------- repair cost over time
ID6 = X('item_id')
def RS6(a, b): return 'SUMIFS(%s,%s,%s,%s,">="&({today}-%d),%s,"<"&({today}-%d))' % (RR('cost'), RR('item_id'), ID6, RR('date'), a, RR('date'), b)
Y1 = RS6(364, -1); Y2 = RS6(729, 364); OLD6 = RS6(4000, 729)
TOT6 = Z(X('rep_cost'))
SH6 = 'IF({in:replacement}>0,(%s+{in:next_repair})/{in:replacement},0)' % TOT6
tools.append(TOOL('repair_over_time', 'Repair Cost Over Time', 'How the repair cost lines of one item add up year by year',
    'Repair cost lines for one item in the last 12 months, the 12 months before and earlier, then what a next repair would add to the share of the replacement price you typed.', [
    I('item', 'Item, as written in Inventory', 'Dishwasher', 'text'), I('next_repair', 'A possible next repair', 120, 'money'), I('replacement', 'Replacement price', 370, 'money')], [
    O('Repairs logged', 'int', X('rep_n')), O('Repair cost lines, last 12 months', 'money', 'IF(%s="","",%s)' % (ID6, Y1)), O('Repair cost lines, the 12 months before', 'money', 'IF(%s="","",%s)' % (ID6, Y2)),
    O('Repair cost lines, earlier', 'money', 'IF(%s="","",%s)' % (ID6, OLD6)), O('Repair cost lines in all', 'money', TOT6), O('After the next repair', 'money', '%s+{in:next_repair}' % TOT6),
    O('Share of the price after it', 'pct', SH6),
    O('Verdict', 'text', NF(V('Next repair would take it to', F(PCT(SH6)), 'of the price')))],
    GRD('What if the next repair costs', ('50', {'next_repair': 50}), ('100', {'next_repair': 100}), ('150', {'next_repair': 150}), ('200', {'next_repair': 200}), ('300', {'next_repair': 300}), ('450', {'next_repair': 450}))))

# 7 ---------------------------------------------------------------- contents of a room
N7 = 'COUNTIFS(%s,{in:room},%s,">="&{in:min_price})' % (IR('room'), IR('price'))
T7 = 'SUMIFS(%s,%s,{in:room},%s,">="&{in:min_price})' % (IR('price'), IR('room'), IR('price'))
OLDM = 'MATCH({in:room}&"|1",%s,0)' % IR('okey')
DEAM = 'MATCH(COUNTIFS(%s,"<"&{in:room})+1,%s,0)' % (IR('room'), IR('rcon'))
tools.append(TOOL('room_contents', 'Contents Of A Room', 'What is in one room, what it is worth and what is oldest',
    'Pick a room: the items, the total of the typed prices, the oldest and the dearest item and the share of all typed value; type a minimum price to count only the bigger items.', [
    IL('room', 'Room', 'room', 'Kitchen'), I('min_price', 'Count items priced from', 0, 'money')], [
    O('Items counted', 'int', N7), O('Typed value of them', 'money', T7), O('Items in the room, all prices', 'int', 'COUNTIFS(%s,{in:room})' % IR('room')),
    O('Oldest item', 'text', 'IFERROR(INDEX(%s,%s)&"","")' % (IR('item'), OLDM)), O('Its age, years', 'num', 'IFERROR(INDEX(%s,%s),"")' % (IR('age_years'), OLDM)),
    O('Dearest item', 'text', 'IFERROR(INDEX(%s,%s)&"","")' % (IR('item'), DEAM)), O('Its price', 'money', 'IFERROR(INDEX(%s,%s),"")' % (IR('price'), DEAM)),
    O('Share of all typed value', 'pct', 'IFERROR(%s/SUM(%s),0)' % (T7, IR('price'))),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (N7, lbl('No items in this room'), V(F('{in:room}'), 'has', F(N7), 'items worth', F('ROUND(%s,0)' % T7))))],
    GRD('What if you count only bigger items', ('From 0', {'min_price': 0}), ('From 25', {'min_price': 25}), ('From 50', {'min_price': 50}), ('From 100', {'min_price': 100}), ('From 250', {'min_price': 250}), ('From 500', {'min_price': 500}))))

# 8 ---------------------------------------------------------------- contents summary by category
VC = lambda c: R('val_cat', c)
MX8 = 'MAX(%s)' % VC('total')
M8 = 'MATCH(%s,%s,0)' % (MX8, VC('total'))
tools.append(TOOL('category_summary', 'Contents By Category', 'Which category holds most of the typed value',
    'The typed prices summed by category: the largest and the smallest group, their share of the total and how many groups pass the share you type. A sum of your own cost lines.', [
    I('share_limit', 'Flag a group above this share of the total', 0.2, 'pct')], [
    O('Typed value of all items', 'money', 'SUM(%s)' % VC('total')), O('Largest group', 'text', 'IFERROR(INDEX(%s,%s)&"","")' % (VC('category'), M8)), O('Its typed value', 'money', MX8),
    O('Its items', 'int', 'IFERROR(INDEX(%s,%s),"")' % (VC('items'), M8)), O('Its share of the total', 'pct', 'IFERROR(%s/SUM(%s),0)' % (MX8, VC('total'))),
    O('Smallest group, typed value', 'money', 'SMALL(%s,1)' % VC('total')), O('Groups above your share', 'int', 'COUNTIFS(%s,">"&{in:share_limit}*SUM(%s))' % (VC('total'), VC('total'))),
    O('Verdict', 'text', 'IF(SUM(%s)=0,%s,%s)' % (VC('total'), lbl('No prices typed yet'), V('Largest group', F('INDEX(%s,%s)' % (VC('category'), M8)), 'worth', F('ROUND(%s,0)' % MX8))))],
    GRD('What if the share limit changes', ('Limit 15%', {'share_limit': 0.15}), ('Limit 20%', {'share_limit': 0.2}), ('Limit 25%', {'share_limit': 0.25}), ('Limit 30%', {'share_limit': 0.3}), ('Limit 40%', {'share_limit': 0.4}))))

# 9 ---------------------------------------------------------------- missing documents finder
MP = '%s,">="&{in:min_price}' % IR('price')
N9 = 'COUNTIFS(%s,1,%s)' % (IR('no_receipt'), MP)
M9 = 'MATCH(1,%s,0)' % IR('rmiss')
tools.append(TOOL('missing_finder', 'Missing Documents Finder', 'How many items have no receipt date, manual or serial number',
    'Counts the items with a gap, the typed value without a receipt and the first item to fix; type a minimum price to start with the bigger items.', [
    I('min_price', 'Count items priced from', 0, 'money')], [
    O('Items without a receipt date', 'int', N9), O('Items with no manual kept', 'int', 'COUNTIFS(%s,1,%s)' % (IR('no_manual'), MP)), O('Items without a serial number', 'int', 'COUNTIFS(%s,1,%s)' % (IR('no_serial'), MP)),
    O('Items missing at least one', 'int', 'COUNTIFS(%s,">0",%s)' % (IR('missing_n'), MP)), O('Typed value without a receipt date', 'money', 'SUMIFS(%s,%s,1,%s)' % (IR('price'), IR('no_receipt'), MP)),
    O('First item to fix', 'text', 'IFERROR(INDEX(%s,%s)&"","")' % (IR('item'), M9)), O('Its fields to fill', 'int', 'IFERROR(INDEX(%s,%s),"")' % (IR('missing_n'), M9)),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (N9, lbl('Every item has a receipt date'), V(F(N9), 'items need a receipt note')))],
    GRD('What if you start with bigger items', ('From 0', {'min_price': 0}), ('From 50', {'min_price': 50}), ('From 100', {'min_price': 100}), ('From 250', {'min_price': 250}), ('From 500', {'min_price': 500}), ('From 1000', {'min_price': 1000}))))

# 10 --------------------------------------------------------------- oldest items
O10 = 'MATCH(1,%s,0)' % IR('rold')
ON10 = 'MATCH({in:rank},%s,0)' % IR('rold')
tools.append(TOOL('oldest_items', 'Oldest Items Tool', 'Which items are the oldest and how many pass an age you choose',
    'The oldest item by purchase date, the item at the rank you type and the items past the years you type with their typed value: the age is calculated from your entries.', [
    I('rank', 'Show the item at this age rank', 5), I('years', 'Count items at or past this many years', 8)], [
    O('Oldest item', 'text', 'IFERROR(INDEX(%s,%s)&"","")' % (IR('item'), O10)), O('Its age, years', 'num', 'IFERROR(INDEX(%s,%s),"")' % (IR('age_years'), O10)), O('Its room', 'text', 'IFERROR(INDEX(%s,%s)&"","")' % (IR('room'), O10)),
    O('Item at your rank', 'text', 'IFERROR(INDEX(%s,%s)&"","")' % (IR('item'), ON10)), O('Age at your rank, years', 'num', 'IFERROR(INDEX(%s,%s),"")' % (IR('age_years'), ON10)),
    O('Items at or past the years', 'int', 'COUNTIFS(%s,">="&{in:years})' % IR('age_years')), O('Their typed value', 'money', 'SUMIFS(%s,%s,">="&{in:years})' % (IR('price'), IR('age_years'))),
    O('Share of all items', 'pct', 'IFERROR(COUNTIFS(%s,">="&{in:years})/COUNTIFS(%s,">=0"),0)' % (IR('age_years'), IR('age_years'))),
    O('Verdict', 'text', 'IF(COUNTIFS(%s,">=0")=0,%s,%s)' % (IR('age_years'), lbl('No purchase dates typed'), V('Oldest', F('INDEX(%s,%s)' % (IR('item'), O10)), F('INDEX(%s,%s)' % (IR('age_years'), O10)), 'years')))],
    GRD('What if the age line moves', ('3 years', {'years': 3}), ('5 years', {'years': 5}), ('8 years', {'years': 8}), ('10 years', {'years': 10}), ('12 years', {'years': 12}))))

# 11 --------------------------------------------------------------- warranty calendar by month
WM = lambda c: R('warr_month', c)
MXW = 'MAX(%s)' % WM('ends')
MW = 'MATCH(%s,%s,0)' % (MXW, WM('ends'))
MN11 = MNAME('MONTH(INDEX(%s,%s))' % (WM('month'), MW))
tools.append(TOOL('warranty_calendar', 'Warranty Calendar By Month', 'Which month of the next 12 has the most warranties ending',
    'The warranties ending in each of the next 12 months: the busiest month, the months with nothing and the typed price covered in the busiest month.', [
    I('min_items', 'Count months with at least this many ending', 2)], [
    O('Warranties ending, next 12 months', 'int', 'SUM(%s)' % WM('ends')), O('Busiest month', 'text', 'IF(%s=0,"",%s)' % (MXW, MN11)), O('Warranties ending in it', 'int', MXW),
    O('Typed price covered in it', 'money', 'IFERROR(INDEX(%s,%s),"")' % (WM('price'), MW)), O('Months with at least your number', 'int', 'COUNTIFS(%s,">="&{in:min_items})' % WM('ends')),
    O('Months with nothing ending', 'int', 'COUNTIFS(%s,0)' % WM('ends')), O('Typed price covered, all months', 'money', 'SUM(%s)' % WM('price')),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (MXW, lbl('No warranty ends in the next 12 months'), V('Busiest end month', F(MN11), F(MXW), 'items')))],
    GRD('What if you count busier months only', ('At least 1', {'min_items': 1}), ('At least 2', {'min_items': 2}), ('At least 3', {'min_items': 3}), ('At least 4', {'min_items': 4}), ('At least 6', {'min_items': 6}))))

# 12 --------------------------------------------------------------- wait or replace now
DL12 = X('days_left')
tools.append(TOOL('wait_replace', 'Wait Or Replace Now', 'Does a planned replacement date fall inside the warranty of the old item',
    'Type the old item and in how many days you plan to replace it: the warranty days left at that date and what an open fault means; a view of your own dates, not advice.', [
    I('item', 'Old item, as written in Inventory', 'Washing machine', 'text'), I('plan_in', 'Planned replacement in this many days', 45)], [
    O('Warranty end typed', 'date', XD('warranty_end')), O('Days of warranty left', 'int', DL12), O('Planned replacement date', 'date', '{today}+{in:plan_in}'),
    O('Warranty days left at that date', 'int', 'IF(%s="","",%s-{in:plan_in})' % (DL12, DL12)), O('Open repairs on the item', 'int', X('open_rep')),
    O('Verdict', 'text', NF('IF(%s="",%s,IF(%s<0,%s,IF(%s>0,%s,IF({in:plan_in}<=0,%s,IF(%s>{in:plan_in},%s,%s)))))' % (
        DL12, lbl('No warranty typed, nothing to wait for'), DL12, lbl('Replace now, the warranty has ended'), X('open_rep'), V('Report the fault first,', F(DL12), 'days left'),
        V('Replace now, but', F(DL12), 'days of warranty go with it'), DL12, V('Wait, the warranty is still on for', F(DL12), 'days'), V('Replace as planned, the warranty ends', F('{in:plan_in}-%s' % DL12), 'days earlier'))))],
    GRD('What if you replace sooner or later', ('Now', {'plan_in': 0}), ('In 15 days', {'plan_in': 15}), ('In 30 days', {'plan_in': 30}), ('In 45 days', {'plan_in': 45}), ('In 60 days', {'plan_in': 60}), ('In 90 days', {'plan_in': 90}))))

# 13 --------------------------------------------------------------- annual cost of owning an item
YRS13 = 'MAX(1,%s+{in:extra_years})' % Z(X('age_years'))
PY13 = '%s/%s' % (Z(X('price')), YRS13)
RY13 = '%s/%s' % (Z(X('rep_cost')), YRS13)
tools.append(TOOL('annual_cost', 'Annual Cost Of Owning', 'About what one item costs a year: price and repairs spread over its age',
    'The typed price spread over the years you have had the item plus the repair cost lines per year, with no resale value; type extra years to see the cost fall.', [
    I('item', 'Item, as written in Inventory', 'Dishwasher', 'text'), I('extra_years', 'Years you will still keep it', 0)], [
    O('Price typed', 'money', X('price')), O('Age, years', 'num', X('age_years')), O('Years counted, at least 1', 'num', 'IF(%s,%s,"")' % (FOUND, YRS13)),
    O('Price per year', 'money', 'IF(%s,ROUND(%s,2),"")' % (FOUND, PY13)), O('Repair cost lines so far', 'money', X('rep_cost')), O('Repair cost lines per year', 'money', 'IF(%s,ROUND(%s,2),"")' % (FOUND, RY13)),
    O('Cost per year in all', 'money', 'IF(%s,ROUND(%s+%s,2),"")' % (FOUND, PY13, RY13)),
    O('Verdict', 'text', NF(V('About', F('ROUND(%s+%s,0)' % (PY13, RY13)), 'a year')))],
    GRD('What if you keep it longer', ('0 more years', {'extra_years': 0}), ('1 more year', {'extra_years': 1}), ('2 more years', {'extra_years': 2}), ('3 more years', {'extra_years': 3}), ('5 more years', {'extra_years': 5}), ('8 more years', {'extra_years': 8}))))

# 14 --------------------------------------------------------------- repairs against the typical range
YRS14 = 'MAX(1,%s)' % Z(X('age_years'))
RY14 = '%s/%s' % (Z(X('rep_cost')), YRS14)
tools.append(TOOL('repairs_vs_plan', 'Repairs Against A Plan Price', 'Your repair cost lines per year against a typed extended-plan price',
    'The repair cost lines of one item averaged over its age against a yearly plan price you type: the numbers side by side, no advice and no promise of future repairs.', [
    I('item', 'Item, as written in Inventory', 'Dishwasher', 'text'), I('plan_price', 'Typed plan price per year', 40, 'money')], [
    O('Age, years', 'num', X('age_years')), O('Repairs logged', 'int', X('rep_n')), O('Repair cost lines so far', 'money', X('rep_cost')), O('Repair cost lines per year', 'money', 'IF(%s,ROUND(%s,2),"")' % (FOUND, RY14)),
    O('Plan price per year, typed', 'money', '{in:plan_price}'), O('Plan price over the item age', 'money', 'IF(%s,ROUND({in:plan_price}*%s,2),"")' % (FOUND, YRS14)),
    O('Repairs minus the plan price, per year', 'money', 'IF(%s,ROUND(%s-{in:plan_price},2),"")' % (FOUND, RY14)),
    O('Verdict', 'text', NF(V('Your repairs on this item average', F('ROUND(%s,0)' % RY14), 'a year')))],
    GRD('What if the plan price changes', ('Plan 20', {'plan_price': 20}), ('Plan 40', {'plan_price': 40}), ('Plan 60', {'plan_price': 60}), ('Plan 80', {'plan_price': 80}), ('Plan 120', {'plan_price': 120}))))

# 15 --------------------------------------------------------------- serial finder for a call
tools.append(TOOL('serial_finder', 'Serial Finder For A Call', 'What to quote when you ring about one item',
    'Type an item: the serial number, the purchase date, the receipt date and the warranty end to have in front of you when you phone; add a serial in Inventory when it says none.', [
    I('item', 'Item, as written in Inventory', 'Washing machine', 'text')], [
    O('Serial number', 'text', 'IF(NOT(%s),"",IF(%s="",%s,%s))' % (FOUND, XT('serial'), lbl('Not typed yet'), XT('serial'))), O('Purchase date', 'date', XD('purchase_date')), O('Receipt date', 'date', XD('receipt_date')),
    O('Days since the purchase', 'int', 'IFERROR({today}-%s,"")' % XD('purchase_date')), O('Warranty end typed', 'date', XD('warranty_end')), O('Days of warranty left', 'int', X('days_left')), O('Room', 'text', XT('room')),
    O('Manual place', 'text', XT('manual_place')),
    O('Verdict', 'text', NF('IF(%s="",%s,%s)' % (XT('serial'), lbl('Add the serial from the item label'), V('Quote', F(XT('serial')), 'bought', F('IFERROR({today}-%s,"")' % XD('purchase_date')), 'days ago'))))]))

# 16 --------------------------------------------------------------- replacement planning
N16 = 'COUNTIFS(%s,">="&{in:years})' % PR('age_years')
T16 = 'SUMIFS(%s,%s,">="&{in:years})' % (PR('replacement_price'), PR('age_years'))
tools.append(TOOL('replacement_plan', 'Replacement Planning Tool', 'Which big items are old enough to plan for and what it adds up to',
    'The items on the replacement list at or past the years you type, their typed replacement total and the items reaching their typical years soon (a household note, check the manual).', [
    I('years', 'Plan for items at or past this age, years', 6), I('look_ahead', 'Also count items reaching their typical years within', 2)], [
    O('Items on the replacement list', 'int', 'COUNTA(%s)' % PR('item')), O('Items at or past the age', 'int', N16), O('Their typed replacement total', 'money', T16),
    O('Items reaching typical years soon', 'int', 'COUNTIFS(%s,"<="&{in:look_ahead})' % PR('years_left')), O('Their typed replacement total, soon', 'money', 'SUMIFS(%s,%s,"<="&{in:look_ahead})' % (PR('replacement_price'), PR('years_left'))),
    O('Typed replacement total, whole list', 'money', 'SUM(%s)' % PR('replacement_price')), O('Items already past their typical years', 'int', 'COUNTIFS(%s,1)' % PR('past_typ')),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (N16, lbl('No listed item is that old'), V(F(N16), 'items to plan for, about', F('ROUND(%s,0)' % T16))))],
    GRD('What if the age line moves', ('4 years', {'years': 4}), ('6 years', {'years': 6}), ('8 years', {'years': 8}), ('10 years', {'years': 10}), ('12 years', {'years': 12}))))

# 17 --------------------------------------------------------------- insurance contents list check
M17 = '%s,">="&{in:min_price}' % IR('price')
N17 = 'COUNTIFS(%s)' % M17
W17 = 'COUNTIFS(%s,0,%s)' % (IR('no_receipt'), M17)
SH17 = 'IF(%s=0,0,%s/%s)' % (N17, W17, N17)
tools.append(TOOL('contents_check', 'Contents List Check', 'How much of the contents list has a receipt date behind it',
    'The items from the price you type: how many have a receipt date, the typed value with and without one and the gap to your goal in Settings. A list check, not advice.', [
    I('min_price', 'Check items priced from', 100, 'money')], [
    O('Items in the check', 'int', N17), O('With a receipt date', 'int', W17), O('Without a receipt date', 'int', '%s-%s' % (N17, W17)), O('Share with a receipt date', 'pct', SH17),
    O('Typed value with a receipt date', 'money', 'SUMIFS(%s,%s,0,%s)' % (IR('price'), IR('no_receipt'), M17)), O('Typed value without one', 'money', 'SUMIFS(%s,%s,1,%s)' % (IR('price'), IR('no_receipt'), M17)),
    O('Your receipt goal, Settings', 'pct', '{set:receipt_goal}'), O('Items to add to reach the goal', 'int', 'MAX(0,ROUNDUP({set:receipt_goal}*%s-%s,0))' % (N17, W17)),
    O('Verdict', 'text', 'IF(%s=0,%s,%s)' % (N17, lbl('No items at this price'), V(F(PCT(SH17)), 'of items have a receipt date')))],
    GRD('What if you check smaller or bigger items', ('From 0', {'min_price': 0}), ('From 50', {'min_price': 50}), ('From 100', {'min_price': 100}), ('From 250', {'min_price': 250}), ('From 500', {'min_price': 500}), ('From 1000', {'min_price': 1000}))))

# 18 --------------------------------------------------------------- compare purchases with own history
PD = IR('purchase_date')
THIS = 'SUMIFS(%s,%s,">="&DATE(YEAR({today}),1,1),%s,"<="&{today})' % (IR('price'), PD, PD)
LAST = 'SUMIFS(%s,%s,">="&DATE(YEAR({today})-1,1,1),%s,"<="&EDATE({today},-12))' % (IR('price'), PD, PD)
RAT = 'IF(%s=0,0,%s/%s)' % (LAST, THIS, LAST)
tools.append(TOOL('purchases_history', 'Purchases Against History', 'Are this year purchases above or below the same dates last year',
    'Typed purchase prices from 1 January to today against 1 January to the same day last year (complete, equal periods) with the margin you type for in line. Your own history, not a benchmark.', [
    I('margin', 'In line within this share', 0.1, 'pct')], [
    O('Typed value bought this year to date', 'money', THIS), O('Typed value bought, same dates last year', 'money', LAST),
    O('Items bought this year to date', 'int', 'COUNTIFS(%s,">="&DATE(YEAR({today}),1,1),%s,"<="&{today})' % (PD, PD)),
    O('Items bought, same dates last year', 'int', 'COUNTIFS(%s,">="&DATE(YEAR({today})-1,1,1),%s,"<="&EDATE({today},-12))' % (PD, PD)),
    O('Difference', 'money', '%s-%s' % (THIS, LAST)), O('This year as a share of last year', 'pct', RAT),
    O('Verdict', 'text', 'IF(AND(%s=0,%s=0),%s,IF(%s=0,%s,IF(%s>1+{in:margin},%s,IF(%s<1-{in:margin},%s,%s))))' % (
        THIS, LAST, lbl('Nothing bought in either period'), LAST, lbl('Above history, nothing last year'),
        RAT, V('Above your own history:', F(PCT(RAT)), 'of last year'), RAT, V('Below your own history:', F(PCT(RAT)), 'of last year'), V('In line with your own history:', F(PCT(RAT)), 'of last year')))],
    GRD('What if in line is wider or narrower', ('5%', {'margin': 0.05}), ('10%', {'margin': 0.1}), ('20%', {'margin': 0.2}), ('30%', {'margin': 0.3}), ('50%', {'margin': 0.5}))))

assert len(tools) == 18, len(tools)
