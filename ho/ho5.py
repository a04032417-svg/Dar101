"""Home Management suite - part 5: Home Inventory and Warranties."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from ho5_lists import *
from ho5_tables import *
from ho5_tools import tools, V, F as FX
import ho5_data as D

_TT = {'open_fault': 'Which open repair sits on an item still under warranty', 'where_manual': 'Where are the manual, receipt and serial number of one item',
       'repair_replace': 'Do the repairs so far pass your own rule for replacing', 'oldest_items': 'Which items are the oldest and how many pass an age you pick',
       'wait_replace': 'Does a planned replacement date fall inside the warranty', 'annual_cost': 'About what one item costs a year, price and repairs spread',
       'repairs_vs_plan': 'Repair cost lines per year against a typed plan price', 'replacement_plan': 'Which big items are old enough to plan for and the total',
       'purchases_history': 'Are this year purchases above or below last year'}
for _t in tools:
    if _t['key'] in _TT: _t['title'] = _TT[_t['key']]
for _s in settings:
    if _s['key'] == 'warranty_days': _s['label'] = 'Warranty ending soon: within this many days'
    if _s['key'] == 'repair_rule': _s['label'] = 'Repair rule: share of the replacement price'

SUITE = 'fx-20261118-home-management'
NOTE = "Sample wording: adapt it to your own household and your local rules; check your paperwork and the manufacturer's instructions."
def FW(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
def LKD(t, idc, c): return 'IF(%s=0,"",%s)' % (LK(t, idc, c), LK(t, idc, c))

# ------------------------------------------------------------------ forms (12)
def IK(c): return LK('inventory', 'item_id', c)
forms = [
    FORM('item_card', 'Inventory Item Card', 'One item with its dates, price and status', 'inventory.item_id', FW(
        ('Item', 'inventory.item'), ('Room', 'inventory.room'), ('Category', 'inventory.category'), ('Purchase date', 'inventory.purchase_date'), ('Price', 'inventory.price'), ('Serial number', 'inventory.serial'),
        ('Warranty end', 'inventory.warranty_end'), ('Receipt date', 'inventory.receipt_date'), ('Manual place', 'inventory.manual_place'), ('Age, years', 'inventory.age_years'),
        ('Days of warranty left', 'inventory.days_left'), ('Warranty status', 'inventory.status')) + [
        FF('Warranty length typed, years', 'IFERROR(ROUND((%s-%s)/365.25,1),"")' % (IK('warranty_end'), IK('purchase_date')), 'num'), FF('Items in the same room', 'COUNTIFS({range:inventory.room},%s)' % IK('room'), 'int')]),
    FORM('purchase_sheet', 'New Purchase Sheet', 'One recent purchase and its year totals', 'recent.no', FW(
        ('Item', 'recent.item'), ('Purchase date', 'recent.purchase_date'), ('Price', 'recent.price'), ('Warranty end', 'recent.warranty_end'), ('Days of warranty left', 'recent.days_left'),
        ('Purchase year', 'recent.year'), ('Items bought that year', 'recent.year_items'), ('Typed value bought that year', 'recent.year_value')) + [
        FF('Share of the year value', 'IFERROR(%s/%s,0)' % (LK('recent', 'no', 'price'), LK('recent', 'no', 'year_value')), 'pct'),
        FF('Warranty length typed, years', 'IFERROR(ROUND((%s-%s)/365.25,1),"")' % (LK('recent', 'no', 'warranty_end'), LK('recent', 'no', 'purchase_date')), 'num')]),
    FORM('warranty_sheet', 'Warranty Check Sheet', 'One item: warranty end and the claim date', 'inventory.item_id', FW(
        ('Item', 'inventory.item'), ('Room', 'inventory.room'), ('Warranty end', 'inventory.warranty_end'), ('Days of warranty left', 'inventory.days_left'), ('Warranty status', 'inventory.status'),
        ('Receipt date', 'inventory.receipt_date'), ('Manual place', 'inventory.manual_place'), ('Serial number', 'inventory.serial'), ('Open repairs', 'inventory.open_rep')) + [
        FF('Start the claim by', '%s-{set:urgent_days}' % IK('warranty_end'), 'date'), FF('Days to start the claim', '%s-{set:urgent_days}-{today}' % IK('warranty_end'), 'int')]),
    FORM('receipt_sheet', 'Receipt And Manual Sheet', 'One item with a gap: receipt, manual or serial', 'missing.no', FW(
        ('Item', 'missing.item'), ('Room', 'missing.room'), ('Receipt missing, 1 or 0', 'missing.no_receipt'), ('Manual missing, 1 or 0', 'missing.no_manual'), ('Serial missing, 1 or 0', 'missing.no_serial'),
        ('Fields to fill', 'missing.fields'), ('Price', 'missing.price'), ('Items without a receipt date', 'missing.n_no_receipt')) + [
        FF('Fields filled of 3', '3-%s' % LK('missing', 'no', 'fields'), 'int'), FF('Share of the items without a receipt', 'IFERROR(1/%s,0)' % LK('missing', 'no', 'n_no_receipt'), 'pct')]),
    FORM('repair_sheet', 'Repair Or Replace Sheet', 'One big item: repairs against its price', 'repair_view.item', FW(
        ('Item ID', 'repair_view.item_id'), ('Age, years', 'repair_view.age_years'), ('Repairs logged', 'repair_view.repairs'), ('Repair cost lines', 'repair_view.repair_cost'), ('Replacement price', 'repair_view.replacement'),
        ('Repairs as a share of the price', 'repair_view.share'), ('Verdict', 'repair_view.verdict')) + [
        FF('Your repair rule', '{set:repair_rule}', 'pct'), FF('Repair cost lines left before the rule', 'MAX(0,{set:repair_rule}*%s-%s)' % (LK('repair_view', 'item', 'replacement'), LK('repair_view', 'item', 'repair_cost')), 'money')]),
    FORM('room_sheet', 'Room Contents Sheet', 'One room with every item in it', 'val_room.room', FW(
        ('Room', 'val_room.room'), ('Items', 'val_room.items'), ('Total price', 'val_room.total')) + [
        FF('Share of all typed value', 'IFERROR(%s/SUM({range:val_room.total}),0)' % LK('val_room', 'room', 'total'), 'pct'), FF('Share of all items', 'IFERROR(%s/SUM({range:val_room.items}),0)' % LK('val_room', 'room', 'items'), 'pct')],
        {"from": "inventory", "match": "inventory.room", "columns": ["item", "price", "purchase_date", "serial"], "max": 30}),
    FORM('claim_sheet', 'Warranty Claim Sheet', 'One repair against the warranty of its item', 'claims.no', FW(
        ('Repair ID', 'claims.repair_id'), ('Item or issue', 'claims.item'), ('Fault date', 'claims.fault_date'), ('Warranty end', 'claims.warranty_end'), ('Days of warranty left', 'claims.days_left'), ('Claim status', 'claims.status')) + [
        FF('Days since the fault date', '{today}-%s' % LK('claims', 'no', 'fault_date'), 'int'), FF('Days the fault was inside the warranty', '%s-%s' % (LK('claims', 'no', 'warranty_end'), LK('claims', 'no', 'fault_date')), 'int')]),
    FORM('serial_sheet', 'Serial Number Sheet', 'One item: what to quote when you ring', 'inventory.item_id', FW(
        ('Item', 'inventory.item'), ('Serial number', 'inventory.serial'), ('Purchase date', 'inventory.purchase_date'), ('Receipt date', 'inventory.receipt_date'), ('Room', 'inventory.room'),
        ('Manual place', 'inventory.manual_place'), ('Age, years', 'inventory.age_years')) + [
        FF('Warranty end typed', '%s' % LKD('inventory', 'item_id', 'warranty_end'), 'date'), FF('Days of warranty left', '%s' % IK('days_left'), 'int')]),
    FORM('sold_sheet', 'Item Sold Or Given Sheet', 'One item leaving the home: age, price and use', 'inventory.item_id', FW(
        ('Item', 'inventory.item'), ('Room', 'inventory.room'), ('Category', 'inventory.category'), ('Purchase date', 'inventory.purchase_date'), ('Price', 'inventory.price'), ('Age, years', 'inventory.age_years'),
        ('Receipt date', 'inventory.receipt_date')) + [
        FF('Price per year of use', 'IFERROR(ROUND(%s/MAX(1,%s),2),0)' % (IK('price'), IK('age_years')), 'money'), FF('Days of warranty left', '%s' % IK('days_left'), 'int'), FF('Repair cost lines logged', '%s' % IK('rep_cost'), 'money')]),
    FORM('price_sheet', 'Replacement Price Sheet', 'One big item: replacement price and years', 'replace.item', FW(
        ('Item ID', 'replace.item_id'), ('Replacement price', 'replace.replacement_price'), ('Typical years of use', 'replace.typical_years'), ('Age, years', 'replace.age_years'),
        ('Typical years left', 'replace.years_left'), ('At or past the typical years, 1 or 0', 'replace.past_typ')) + [
        FF('Price per typical year', 'IFERROR(ROUND(%s/%s,2),0)' % (LK('replace', 'item', 'replacement_price'), LK('replace', 'item', 'typical_years')), 'money'),
        FF('Share of all replacement prices', 'IFERROR(%s/SUM({range:replace.replacement_price}),0)' % LK('replace', 'item', 'replacement_price'), 'pct')]),
    FORM('manual_sheet', 'Manual Location Sheet', 'One storage place and the manuals in it', 'manuals.place', FW(
        ('Manual place', 'manuals.place'), ('Items', 'manuals.items'), ('With a serial', 'manuals.with_serial')) + [
        FF('Share of all items', 'IFERROR(%s/SUM({range:manuals.items}),0)' % LK('manuals', 'place', 'items'), 'pct'), FF('Items with no serial typed', '%s-%s' % (LK('manuals', 'place', 'items'), LK('manuals', 'place', 'with_serial')), 'int')],
        {"from": "inventory", "match": "inventory.manual_place", "columns": ["item", "room", "serial"], "max": 30}),
    FORM('move_sheet', 'Item Move Sheet', 'One item changing room or home', 'inventory.item_id', FW(
        ('Item', 'inventory.item'), ('Room now', 'inventory.room'), ('Category', 'inventory.category'), ('Price', 'inventory.price'), ('Serial number', 'inventory.serial'), ('Manual place', 'inventory.manual_place')) + [
        FF('Items in the room now', 'COUNTIFS({range:inventory.room},%s)' % IK('room'), 'int'), FF('Typed value of the room now', 'SUMIFS({range:inventory.price},{range:inventory.room},%s)' % IK('room'), 'money'),
        FF('Share of the room value', 'IFERROR(%s/SUMIFS({range:inventory.price},{range:inventory.room},%s),0)' % (IK('price'), IK('room')), 'pct')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('contents_doc', 'Contents List Page', 'Contents list page, one item of the list', 'contents.no', [
        'Home inventory of {set:household}, dated {today}. Line {col:contents.no}: {col:contents.item} in the {col:contents.room}, price {col:contents.price}, bought on {col:contents.purchase_date}, serial {col:contents.serial}.',
        'The {col:contents.room} holds {col:contents.room_items} items with a typed value of {col:contents.room_total}.',
        'Print the Contents list by room sheet for the whole list. The prices are the cost lines you typed, not an appraisal.',
        'Checked on the walk-through of {col:contents.walk_date}.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('countdown_doc', 'Warranty Countdown Page', 'Warranty countdown page, soonest end first', 'ending90.no', [
        'Warranties of {set:household}, dated {today}. Rank {col:ending90.no}: {col:ending90.item} in the {col:ending90.room}, price {col:ending90.price}.',
        'Warranty end typed: {col:ending90.warranty_end}, {col:ending90.days_left} days left. Open repair: {col:ending90.open}. In all, {col:ending90.n90} warranties end within the soon window.',
        'Find the receipt and the manual, test the item and report any fault before the warranty ends. Warranty lengths are often 1 to 5 years: check your paperwork.',
        'The days are calculated from the dates you typed.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('card_doc', 'Item Card Page', 'Item card with serial, receipt and manual place', 'inventory.item_id', [
        'Item card of {set:household}, dated {today}. {col:inventory.item_id}: {col:inventory.item} in the {col:inventory.room}, category {col:inventory.category}.',
        'Bought on {col:inventory.purchase_date} for {col:inventory.price}. Serial number: {col:inventory.serial}. Receipt date: {col:inventory.receipt_date}. Manual kept in: {col:inventory.manual_place}.',
        'Warranty end typed: {col:inventory.warranty_end}, {col:inventory.days_left} days left, status {col:inventory.status}. Repairs logged: {col:inventory.rep_n}.',
        'Keep this card with the receipt.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('repair_doc', 'Repair Replace Summary', 'Repair-or-replace summary for one item', 'repair_view.item', [
        'Repair or replace summary of {set:household}, dated {today}. Item: {col:repair_view.item} ({col:repair_view.item_id}), age {col:repair_view.age_years} years.',
        'Repairs logged: {col:repair_view.repairs}. Repair cost lines: {col:repair_view.repair_cost}. Replacement price typed: {col:repair_view.replacement}. Repairs as a share of that price: {col:repair_view.share}.',
        'Verdict against your own rule of {set:repair_rule}: {col:repair_view.verdict}. This is a view of your own entries, not advice.',
        'Decision and date:'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('claim_letter', 'Warranty Claim Letter', 'Letter to an appliance repairer about a fault', 'inventory.item_id', [
        'Dear {set:ar_name}, our {col:inventory.item} in the {col:inventory.room} has a fault and we would like to book a visit.',
        'It was bought on {col:inventory.purchase_date} and we have a receipt dated {col:inventory.receipt_date}. The serial number is {col:inventory.serial}. The warranty end we have on paper is {col:inventory.warranty_end}.',
        'Please tell us what you need from us, whether the visit is covered and which dates you have free. Our phone numbers are in the signature.',
        'Thank you, {set:household}.'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('missing_doc', 'Missing Receipts List', 'Receipts and manuals missing, one item', 'missing.no', [
        'Gaps in the inventory of {set:household}, dated {today}. Rank {col:missing.no}: {col:missing.item} in the {col:missing.room}, price {col:missing.price}.',
        'Receipt missing (1 yes): {col:missing.no_receipt}. Manual missing: {col:missing.no_manual}. Serial missing: {col:missing.no_serial}. Fields to fill: {col:missing.fields}.',
        'In all, {col:missing.n_no_receipt} items have no receipt date. Type the missing fields in the yellow cells of Inventory and the item leaves this list.',
        'Done on:'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('room_doc', 'Value By Room Summary', 'Value by room summary, one room', 'val_room.room', [
        'Typed value of {set:household}, dated {today}. Room: {col:val_room.room}. Items: {col:val_room.items}. Total of the typed prices: {col:val_room.total}.',
        'The total is a sum of the cost lines you typed. It is not an appraisal and not advice.',
        'Compare it with the Contents list by room before you update it.',
        'Checked by:'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('insurance_doc', 'Insurance Contents Page', 'Contents list for an insurance conversation', 'val_cat.category', [
        'Contents list of {set:household}, dated {today}. Category: {col:val_cat.category}. Items: {col:val_cat.items}. Typed total: {col:val_cat.total}.',
        'Have the receipts, serial numbers and photos ready and ask your own insurer what it needs. The list shows what you typed; it is not advice and not a valuation.',
        'Print the Contents list by room as the attachment.',
        'Prepared by:'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('sitter_doc', 'Sitter Handover List', 'Handover list of manuals for a sitter', 'manuals.place', [
        'Manuals of {set:household}, dated {today}. Place: {col:manuals.place}. Items whose manual is there: {col:manuals.items}, with a serial typed: {col:manuals.with_serial}.',
        'A sitter or visitor can find the manual for a machine in this place. The Manual Location Sheet lists the items.',
        'Do not use any item that is waiting for a repair. Call the adults first.',
        'Handed over to:'], ['Adult 1', 'Babysitter'], NOTE),
    DOC('expired_doc', 'Expired Warranties Page', 'Expired warranties page, one item', 'expired.no', [
        'Expired warranties of {set:household}, dated {today}. Rank {col:expired.no}: {col:expired.item} in the {col:expired.room}, price {col:expired.price}.',
        'The warranty end you typed was {col:expired.warranty_end}, {col:expired.days_since} days ago.',
        'Keep the receipt and the manual for the record or clear them; check your local rules before you throw papers away.',
        'Reviewed on:'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('year_doc', 'Purchases Of The Year', 'Purchases of the year page', 'by_year.yk', [
        'Purchases of {set:household}, dated {today}. Year: {col:by_year.yk}. Items bought: {col:by_year.items}. Typed total price: {col:by_year.total}.',
        'The list comes from the purchase dates and prices you typed on Inventory.',
        'Use it as your own year in review of the home.',
        'Reviewed by:'], ['Adult 1', 'Adult 2'], NOTE),
    DOC('move_doc', 'Move Inventory Page', 'Move inventory: items of a room to pack', 'val_room.room', [
        'Move inventory of {set:household}, dated {today}. Room: {col:val_room.room}. Items to pack: {col:val_room.items}. Typed value: {col:val_room.total}.',
        'Print the Contents list by room and tick each item as it goes into a box; mark the boxes with the room name.',
        'After the move, check every item against the list and type the new room in Inventory. Renters list only their own items.',
        'Packed by:'], ['Adult 1', 'Adult 2'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('add_purchase', 'Add A New Purchase', 'inventory', 'inventory.purchase_date', [('Type the item, room, category and price', 0), ('Photograph the serial number and type it', 0), ('Keep the receipt and type its date', 1), ('Put the manual away and type where', 1), ('Type the warranty end from the paperwork', 2), ('Check the item in the warranty countdown', 7)]),
    CHK('yearly_walk', 'Yearly Inventory Walk Through', 'team', 'team.start', [('Pick a Sunday and print the Contents list by room', 0), ('Walk the kitchen and the utility room', 1), ('Walk the living room and the hallway', 2), ('Walk the bedrooms and the bathroom', 3), ('Walk the garage and the garden', 4), ('Type what is new, sold or gone', 5), ('Check receipts and manuals missing', 7)]),
    CHK('quarterly_check', 'Quarterly Warranty Check', 'team', 'team.start', [('Open the Warranties ending in 90 days sheet', 0), ('Find the receipts of the items ending', 3), ('Test each item that ends', 7), ('Type any fault in Repairs with the item ID', 10), ('Decide: report, repair or let it end', 14)]),
    CHK('before_ends', 'Before A Warranty Ends', 'inventory', 'inventory.warranty_end', [('Find the receipt and the manual', -60), ('Test the item and list the faults', -45), ('Ring the seller or the repairer about a fault', -30), ('Send the receipt and the photos', -21), ('Decide: repair, replace or let it end', -7), ('Type the outcome in Repairs', 0)]),
    CHK('after_repair', 'After A Repair', 'repairs', 'repairs.date', [('Type the repair on Repairs', 0), ('Add the item ID when it is an inventory item', 0), ('Type the cost line', 3), ('Mark it fixed and type the date', 7), ('Tick warranty used when it was claimed', 7), ('Look at the repair or replace view', 14)]),
    CHK('room_count', 'Room By Room Count', 'team', 'team.start', [('Count the kitchen items against the list', 0), ('Count the living room', 1), ('Count the bedrooms', 2), ('Count the bathroom and the hallway', 3), ('Count the garage and the garden', 4), ('Type the differences', 5)]),
    CHK('tidy_papers', 'Receipts And Manuals Tidy Up', 'team', 'team.start', [('Open the Receipts and manuals missing sheet', 0), ('Collect the receipts you can find', 3), ('Type the receipt dates', 4), ('Put each manual in its place and type it', 7), ('Photograph the serial numbers', 10), ('Check the sheet is shorter', 14)]),
    CHK('replace_appliance', 'Replace An Appliance', 'inventory', 'inventory.warranty_end', [('Check the warranty of the old item', -30), ('Collect two quotes', -21), ('Look at the repair or replace view', -14), ('Type the replacement price', -7), ('Buy the new item', 0), ('Add it to Inventory with the warranty end', 1), ('Sell, give or recycle the old item', 7)]),
    CHK('sell_item', 'Sell Or Give Away An Item', 'inventory', 'inventory.purchase_date', [('Check the item is clean and complete', 0), ('Take photos and write the description', 2), ('Agree the price or the gift', 7), ('Hand over with the manual', 8), ('Remove it from Inventory', 9), ('Type the sale as a note', 10)]),
    CHK('before_move', 'Before A Move', 'team', 'team.start', [('Print the Contents list by room', -42), ('Decide what to keep, sell or give away', -35), ('Pack the rooms you use least', -21), ('Photograph the serial numbers of the big items', -14), ('Pack the manuals and receipts in one box', -7), ('Label every box with the room', -3)]),
    CHK('after_move', 'After A Move', 'team', 'team.start', [('Check every box against the list', 0), ('Type the new room of each item', 3), ('Check the big items for damage', 3), ('Update the warranty papers with the new address', 14), ('Type what is missing or broken', 21)]),
    CHK('single_first', 'Single Adult First Inventory', 'team', 'team.start', [('Replace the demo data with your own items', 0), ('Type your rooms and your items', 1), ('Type prices and purchase dates', 2), ('Type the warranty ends from your paperwork', 3), ('Type where the manuals and receipts are', 4), ('Leave the children and pet items empty', 5)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
messages = [
    M('ar_fault', 'Appliance repairer: book a visit', 'repairs', 'repairs.ar_phone', 'Hello {ar_name}, we logged {issue} in the {room} on {date}. Can you book a visit? {household}'),
    M('ar_covered', 'Appliance repairer: is it covered', 'repairs', 'repairs.ar_phone', 'Hello {ar_name}, is the repair of {issue} covered? Item {item_name}, warranty end on file {w_end}. {household}'),
    M('ar_receipt', 'Appliance repairer: we have the receipt', 'repairs', 'repairs.ar_phone', 'Hello {ar_name}, we have the receipt for {item_name} ({issue}), tell us what you need. {household}'),
    M('ar_open', 'Repairer: the fault is still open', 'repairs', 'repairs.ar_phone', 'Hello {ar_name}, the fault of {date} ({issue}) is still open, please confirm a date. {household}'),
    M('ar_thanks', 'Repairer: please send the papers', 'repairs', 'repairs.ar_phone', 'Hello {ar_name}, thank you, the repair on {fixed_on} is done, please send the paperwork. {household}'),
    M('pl_fit', 'Plumber: look at a fault', 'repairs', 'repairs.pl_phone', 'Hello {pl_name}, can you look at {issue} in the {room}? Logged on {date}. {household}'),
    M('el_socket', 'Electrician: look at a fault', 'repairs', 'repairs.el_phone', 'Hello {el_name}, {issue} in the {room} needs an electrician, logged on {date}. {household}'),
    M('hm_move', 'Handyman: help with a job', 'repairs', 'repairs.hm_phone', 'Hello {hm_name}, can you help with {issue} in the {room}? Logged on {date}. {household}'),
    M('ll_property', 'Landlord or agent: a fixture stopped', 'repairs', 'repairs.ll_phone', 'Hello {ll_name}, {issue} in the {room} was logged on {date}, it belongs to the property, please confirm a repair. {household}'),
    M('ll_list', 'Landlord or agent: our own item', 'repairs', 'repairs.ll_phone', 'Hello {ll_name}, {issue} in the {room} is our own item, we can send you a copy of our inventory. {household}'),
    M('cm_serial', 'Car mechanic: confirm a serial', 'repairs', 'repairs.cm_phone', 'Hello {cm_name}, for {issue} in the {room} we have the serial {serial}, please confirm it. {household}'),
    M('a1_ends', 'Adult 1: the warranty ends soon', 'inventory', 'inventory.a1_phone', 'Hi, the warranty on the {item} ends on {warranty_end}, {days_left} days left, shall we report the fault now? {household}'),
    M('a1_receipt', 'Adult 1: find the receipt', 'inventory', 'inventory.a1_phone', 'Hi, please find the receipt of the {item}, bought on {purchase_date}. {household}'),
    M('a1_repairs', 'Adult 1: look at the repair view', 'inventory', 'inventory.a1_phone', 'Hi, the {item} has had {rep_n} repairs, shall we look at the repair or replace view? {household}'),
    M('a2_manual', 'Adult 2: where the manual is', 'inventory', 'inventory.a2_phone', 'Hi, the manual of the {item} is in {manual_place}. {household}'),
    M('a2_serial', 'Adult 2: photograph the serial', 'inventory', 'inventory.a2_phone', 'Hi, please photograph the serial of the {item} in the {room}. {household}'),
    M('a2_receipts', 'Adult 2: items without a receipt', 'missing', 'missing.a2_phone', 'Hi {a2_name}, {n_no_receipt} items have no receipt date, please add them this week. {household}'),
    M('a2_bought', 'Adult 2: a purchase is added', 'inventory', 'inventory.a2_phone', 'Hi, the {item} was bought on {purchase_date} for {price}, I added it to the inventory. {household}'),
    M('c1_dontmove', 'Child 1: please do not move it', 'inventory', 'inventory.c1_phone', 'Hi, please do not move the {item} in the {room}, it is on the warranty list. {household}'),
    M('c1_laptop', 'Child 1: keep the box and charger', 'inventory', 'inventory.c1_phone', 'Hi, the {item} has a warranty until {warranty_end}, please keep the box and the charger. {household}'),
    M('c2_tablet', 'Child 2: keep it in its case', 'inventory', 'inventory.c2_phone', 'Hi, please keep the {item} in its case, the warranty ends on {warranty_end}. {household}'),
    M('gp_receipt', 'Grandparent: do you have the receipt', 'inventory', 'inventory.gp_phone', 'Hello, we are checking the warranty of the {item}, do you still have the receipt dated {receipt_date}? {household}'),
    M('gp_thanks', 'Grandparent: thank you for the item', 'inventory', 'inventory.gp_phone', 'Hello, thank you for the {item}, I added it to the inventory. {household}'),
    M('bs_repair', 'Babysitter: an item waits for a repair', 'inventory', 'inventory.bs_phone', 'Hello, the {item} in the {room} is waiting for a repair, please do not use it. {household}'),
    M('cp_borrow', 'Carpool family: you may borrow it', 'inventory', 'inventory.cp_phone', 'Hello, you may borrow our {item} this weekend, please bring it back within a week. {household}'),
    M('nb_back', 'Neighbour: please bring it back', 'inventory', 'inventory.nb_phone', 'Hello, you borrowed our {item}, please bring it back this week. {household}'),
    M('nb_lent', 'Neighbour: we lent you an item', 'inventory', 'inventory.nb_phone', 'Hello, we lent you the {item}, it is {price} new, please tell us when you finish. {household}'),
    M('so_laptop', 'School office: school item in repair', 'inventory', 'inventory.so_phone', 'Hello, the {item} (serial {serial}) is in repair, we will bring it to the office soon. {household}'),
    M('hm_ends90', 'Adult 1: warranties end in 90 days', 'ending90', 'ending90.a1_phone', 'Hi {a1_name}, {n90} warranties end soon, the list is on the fridge. {household}'),
    M('hm_walk', 'Adult 2: the inventory walk-through', 'contents', 'contents.a2_phone', 'Hi {a2_name}, the inventory walk-through is on {walk_date}, please tick the {room}. {household}'),
    M('hm_sold', 'Adult 1: an item is sold', 'inventory', 'inventory.a1_phone', 'Hi, the {item} (bought for {price}) is sold, I removed it from the list. {household}'),
    M('hm_replaced', 'Adult 2: an item was replaced', 'inventory', 'inventory.a2_phone', 'Hi, the {item} was replaced on {purchase_date}, its new warranty ends on {warranty_end}. {household}'),
    M('hm_room', 'Adult 1: typed value of a room', 'contents', 'contents.a1_phone', 'Hi {a1_name}, the typed value of the {room} is {room_total}, {room_items} items. {household}'),
    M('hm_year', 'Adult 1: year review of the inventory', 'recent', 'recent.a1_phone', 'Hi {a1_name}, inventory review for {year}: {year_items} items added, typed value {year_value}. {household}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def C_(*a): return 'COUNTIFS(' + ','.join(a) + ')'
K = lambda label, f, fmt='int', **kw: KPI(label, f, fmt, **kw)
APPLT = tok('icat', 'Appliance')
kpis = [
    K('Items in the inventory', 'COUNTA(%s)' % IR('item_id')),
    K('Typed value of all items', 'SUM(%s)' % IR('price'), 'money'),
    K('Items in the largest room', 'MAX(%s)' % R('val_room', 'items')),
    K('Items with a warranty end', 'COUNTIFS(%s,">=0")+COUNTIFS(%s,"<0")' % (IR('days_left'), IR('days_left'))),
    K('Items covered now', 'COUNTIFS(%s,">=0")' % IR('days_left')),
    K('Warranties ending in 30 days', 'COUNTIFS(%s,">=0",%s,"<="&{set:urgent_days})' % (IR('days_left'), IR('days_left')), alert={"when": "> 0", "style": "warn"}),
    K('Warranties ending in 90 days', 'COUNTIFS(%s,">=0",%s,"<="&{set:warranty_days})' % (IR('days_left'), IR('days_left')), alert={"when": "> 0", "style": "warn"}),
    K('Warranties expired', 'COUNTIFS(%s,"<0")' % IR('days_left')),
    K('Days to the next warranty end', 'IFERROR(SMALL(%s,COUNTIF(%s,"<0")+1),"")' % (IR('days_left'), IR('days_left'))),
    K('Value ending in 90 days', 'SUMIFS(%s,%s,">=0",%s,"<="&{set:warranty_days})' % (IR('price'), IR('days_left'), IR('days_left')), 'money'),
    K('Items with an open repair', C_(IR('open_rep'), '">0"'), alert={"when": "> 0", "style": "warn"}),
    K('Open fault in warranty', C_(IR('open_rep'), '">0"', IR('days_left'), '">=0"'), alert={"when": "> 0", "style": "bad"}),
    K('Items without a receipt date', 'COUNTIFS(%s,1)' % IR('no_receipt'), alert={"when": "> 0", "style": "warn"}),
    K('Items without a serial number', 'COUNTIFS(%s,1)' % IR('no_serial')),
    K('Items with no manual kept', 'COUNTIFS(%s,1)' % IR('no_manual')),
    K('Share with a receipt date', 'IFERROR(COUNTIFS(%s,0)/COUNTA(%s),0)' % (IR('no_receipt'), IR('item_id')), 'pct'),
    K('Items bought last 12 months', C_(IR('purchase_date'), '">="&({today}-364)', IR('purchase_date'), '"<="&{today}')),
    K('Value bought last 12 months', 'SUMIFS(%s,%s,">="&({today}-364),%s,"<="&{today})' % (IR('price'), IR('purchase_date'), IR('purchase_date')), 'money'),
    K('Items bought last 30 days', C_(IR('purchase_date'), '">="&({today}-29)', IR('purchase_date'), '"<="&{today}')),
    K('Items past your old-item age', C_(IR('age_years'), '">"&{set:old_years}')),
    K('Oldest item, years', 'MAX(%s)' % IR('age_years'), 'num'),
    K('Average appliance age, years', 'IFERROR(ROUND(AVERAGEIFS(%s,%s,%s),1),"")' % (IR('age_years'), IR('category'), APPLT), 'num'),
    K('Items with repairs logged', C_(IR('rep_n'), '">0"')),
    K('Repair cost lines, items', 'SUMIFS(%s,%s,1)' % (RR('cost'), RR('linked')), 'money'),
    K('Items over your repair rule', C_(VR('verdict'), W_REPLACE), alert={"when": "> 0", "style": "warn"}),
    K('Items on the replacement list', 'COUNTA(%s)' % PR('item')),
    K('Typed replacement total', 'SUM(%s)' % PR('replacement_price'), 'money'),
    K('Items in garage and garden', C_(IR('room'), tok('room', 'Garage')) + '+' + C_(IR('room'), tok('room', 'Garden'))),
    K('Warranty claims open', 'SUM(%s)' % RR('claim_open'), alert={"when": "> 0", "style": "bad"}),
    K('Value covered by a warranty', 'SUMIFS(%s,%s,">=0")' % (IR('price'), IR('days_left')), 'money'),
]
assert len(kpis) == 30, len(kpis)
assert all(len(k['label']) <= 30 for k in kpis), [k['label'] for k in kpis if len(k['label']) > 30]
dashboard = {"title": "Inventory Dashboard", "kpis": kpis,
    "monthly": {"title": "Items bought and repair cost lines by month", "date": "inventory.purchase_date", "series": [
        {"label": "Price of items bought", "sum": "inventory.price", "date": "inventory.purchase_date"}, {"label": "Repair cost lines", "sum": "repairs.cost", "date": "repairs.date"}]},
    "breakdowns": [{"title": "Items by room", "by": "val_room.room", "value": "val_room.items", "agg": "sum"},
                   {"title": "Typed value by category", "by": "val_cat.category", "value": "val_cat.total", "agg": "sum"},
                   {"title": "Items by age band", "by": "age_band.band", "value": "age_band.items", "agg": "sum"},
                   {"title": "Manual locations", "by": "manuals.place", "value": "manuals.items", "agg": "sum"}]}
def W(c, op, v): return (c, op, v)
insights = {"filters": [{"label": "Room", "list": "room"}, {"label": "Category", "list": "icat"}],
    "gauges": [
        {"title": "Items with a receipt date", "num": AGG('count', 'inventory', where=[W('no_receipt', '=', 0)]), "den": AGG('count', 'inventory')},
        {"title": "Items covered by a warranty now", "num": AGG('count', 'inventory', where=[W('days_left', '>=', 0)]), "den": AGG('count', 'inventory')},
        {"title": "Items with a serial number", "num": AGG('count', 'inventory', where=[W('no_serial', '=', 0)]), "den": AGG('count', 'inventory')},
        {"title": "Items with a manual location", "num": AGG('count', 'inventory', where=[W('no_manual', '=', 0)]), "den": AGG('count', 'inventory')},
        {"title": "Open faults inside a warranty", "num": AGG('sum', 'repairs', 'repairs.claim_open'), "den": AGG('sum', 'repairs', 'repairs.open')},
        {"title": "Items under your repair rule", "num": AGG('sum', 'repair_view', 'repair_view.under'), "den": AGG('sum', 'repair_view', 'repair_view.with_rep')}],
    "charts": [
        CHART('Items by room', 'bar', 'inventory.room', [AGG('count', 'inventory', label='Items')]),
        CHART('Typed value by room', 'bar', 'inventory.room', [AGG('sum', 'inventory', 'inventory.price', label='Typed value')]),
        CHART('Items by category', 'bar', 'inventory.category', [AGG('count', 'inventory', label='Items')]),
        CHART('Typed value by category', 'bar', 'inventory.category', [AGG('sum', 'inventory', 'inventory.price', label='Typed value')]),
        CHART('Purchases per year', 'column', 'by_year.yk', [AGG('sum', 'by_year', 'by_year.items', label='Items bought')]),
        CHART('Typed value bought per year', 'column', 'by_year.yk', [AGG('sum', 'by_year', 'by_year.total', label='Typed value')]),
        CHART('Warranties ending per month, next 12', 'column', 'warr_month.ahead', [AGG('sum', 'warr_month', 'warr_month.ends', label='Warranties ending')]),
        CHART('Warranty status by category', 'stacked', 'inventory.category', [
            AGG('count', 'inventory', where=[W('status', '=', W_COV)], label='Covered'), AGG('count', 'inventory', where=[W('status', '=', W_SOON)], label='Ending soon'),
            AGG('count', 'inventory', where=[W('status', '=', W_EXP)], label='Expired'), AGG('count', 'inventory', where=[W('status', '=', W_NONE)], label='None typed')]),
        CHART('Items by age band', 'bar', 'age_band.band', [AGG('sum', 'age_band', 'age_band.items', label='Items')]),
        CHART('Typed value by age band', 'bar', 'age_band.band', [AGG('sum', 'age_band', 'age_band.total', label='Typed value')]),
        CHART('Items with a receipt by room', 'bar', 'inventory.room', [AGG('count', 'inventory', where=[W('no_receipt', '=', 0)], label='With a receipt date')]),
        CHART('Items without a serial by category', 'bar', 'inventory.category', [AGG('count', 'inventory', where=[W('no_serial', '=', 1)], label='No serial')]),
        CHART('Manual locations', 'bar', 'manuals.place', [AGG('sum', 'manuals', 'manuals.items', label='Items')]),
        CHART('Repairs by inventory item', 'bar', 'repair_view.item', [AGG('sum', 'repair_view', 'repair_view.repairs', label='Repairs')]),
        CHART('Repair cost lines by item category', 'bar', 'inventory.category', [AGG('sum', 'inventory', 'inventory.rep_cost', label='Repair cost lines')]),
        CHART('Repairs on inventory items per month', 'column', 'month', [AGG('count', 'repairs', date='repairs.date', where=[W('linked', '=', 1)], label='Repairs')]),
        CHART('Items bought per month', 'column', 'month', [AGG('count', 'inventory', date='inventory.purchase_date', label='Items')]),
        CHART('Warranty end by room', 'bar', 'inventory.room', [AGG('count', 'inventory', where=[W('status', '=', W_SOON)], label='Ending soon'), AGG('count', 'inventory', where=[W('status', '=', W_EXP)], label='Expired')]),
        CHART('Replacement prices by item', 'bar', 'replace.item', [AGG('sum', 'replace', 'replace.replacement_price', label='Replacement price')]),
        CHART('Repair share of price by item', 'bar', 'repair_view.item', [AGG('sum', 'repair_view', 'repair_view.share', label='Share of the price')]),
        CHART('Appliances bought per month', 'column', 'month', [AGG('count', 'inventory', date='inventory.purchase_date', where=[W('category', '=', APPLT)], label='Appliances')]),
        CHART('Items by price band', 'bar', 'price_band.band', [AGG('sum', 'price_band', 'price_band.items', label='Items')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Warranty countdown", "why": "type an item: days of warranty left or days since it ended, from the end date you typed", "where": "Warranty Countdown Tool"},
    {"name": "Open fault against the warranty", "why": "the open repair on an item still under warranty and how long you have to report it", "where": "Open Fault Against Warranty"},
    {"name": "Where is the manual and receipt", "why": "one search cell: the room, serial, receipt date and manual place of any item", "where": "Where Is The Manual"},
    {"name": "Replace or repair", "why": "the repair cost lines as a share of the replacement price you type, against your own rule", "where": "Replace Or Repair Tool"},
    {"name": "Missing documents finder", "why": "every item with no receipt date, manual or serial, the gaps counted and ranked", "where": "Missing Documents Finder"},
    {"name": "Wait or replace now", "why": "a planned replacement date against the warranty end of the old item", "where": "Wait Or Replace Now"},
    {"name": "Annual cost of owning an item", "why": "the price spread over its age plus the repair cost lines per year, with no resale value", "where": "Annual Cost Of Owning"},
    {"name": "Warranties ending soon", "why": "a ranked list of what ends in the next 90 days with the open repairs flagged", "where": "Warranties Ending Soon Tool"},
    {"name": "Serial finder for a call", "why": "the serial, purchase date and receipt date to quote when you phone a repairer", "where": "Serial Finder For A Call"},
    {"name": "Repair cost over time", "why": "the repair cost lines of one item year by year and what a next repair would add", "where": "Repair Cost Over Time"}]
competitors = [
    {"what": "single-tab home inventory sheet", "lacks": "lists items and prices but has no warranty countdown, no ranked ending-soon list, no repair-or-replace view and no missing receipts finder"},
    {"what": "home inventory app with a yearly renewal", "lacks": "keeps your list in an account you pay for every year, with no repairs log tied to each item and no warranty claim sheet"},
    {"what": "warranty tracker template with dates only", "lacks": "shows an end date but not the days left, the open fault, the receipt and manual place or the cost of repairs against the price"},
    {"what": "notes or photos on a phone", "lacks": "holds pictures of receipts but cannot count the days left, rank what ends next, total the value by room or print a contents list"}]
guide = [
    'Start here: this workbook is the inventory of your home and the countdown of its warranties. Open Start and type the household name and the Settings in the yellow cells.',
    'Replace demo data: clear the yellow demo cells of Team, Inventory, Repairs and Replacement prices. Keep the lists and settings. Type your household and your rooms first.',
    'Inventory: one row per item with its room, category, purchase date, price, serial number, warranty end, receipt date and manual place. Age, days left and status fill in.',
    'Warranty lengths are never assumed: they are often 1 to 5 years, so type the real end date from your paperwork. Leave it empty when there is none.',
    'Repairs: log each repair with its fault date, cost and status; type the item ID when it belongs to an inventory item and the countdown, the claims list and the repair-or-replace view use it.',
    'Calculated sheets (Warranty countdown, Warranties ending in 90 days, Expired warranties, Receipts and manuals missing, Contents list by room): type the rank numbers once and the rest fills in.',
    'Replacement prices: type what you would pay today and the typical years of use as a household note; the repair-or-replace view compares the repair cost lines with your own rule in Settings.',
    'Weekly routine: on Sunday glance at the ending soon list and any open repair on an item under warranty.',
    'Monthly routine: check the warranties ending in 90 days, the receipts and manuals missing and add what you bought.',
    'Yearly routine: walk through every room with the Contents list by room, update prices and dates, and read the year in review.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'A single adult uses it unchanged and leaves the children, pet and school items empty. Renters list their own items only and read a trade as a maintenance request to the landlord.',
    'Intervals, warranty lengths and typical years are typical: check your paperwork, the manufacturer instructions and your local rules.',
    'Why a workbook: one flat price, no yearly renewal, your data stays with you, nothing to link, no ads and no upsell. It runs in Excel and Google Sheets with no macros, no add-ins and no accounts.',
    'What this is not: not a safety service, not a reminder app, not an insurance valuation and not legal, medical, veterinary or financial advice. Every figure is calculated from your entries.',
]
listing = {"title": "Home Inventory and Warranty Tracker Excel Template: Warranty Countdown, Receipts and Manuals, Repair or Replace, Contents List",
    "headline": "Know what you own, what is still covered and where the papers are",
    "tags": ["home inventory", "warranty tracker", "household inventory", "contents list", "warranty countdown", "repair or replace", "receipt tracker", "manual locations", "appliance tracker", "household planner", "serial numbers", "no subscription", "home management"],
    "description": ("A home inventory built for a single adult, a couple or a family, owners or renters. List every item with its room, category, purchase date, price, serial number, warranty end, receipt date and the place the manual is kept; the age, the days of warranty left and the status fill in by themselves from your entries.\n\n"
        "A warranty countdown ranks every item by days left, a ranked list shows what ends in the next 90 days with the open repairs flagged, and a list of expired warranties shows what has ended. Warranty lengths are never assumed: you type the real end date from your paperwork.\n\n"
        f"{len(tools)} tools answer the questions of every month: how many days of warranty are left, which open fault must be reported, where the manual and the receipt are, whether repairs pass your own rule for replacing, what an item costs a year and which items to plan for. "
        "A repairs log is tied to the item, so the claims list and the repair-or-replace view read your own history. Totals by room, category, year and age band come from the prices you typed, and a printable contents list is ready for a walk-through or a move.\n\n"
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to the repairer, the plumber, the landlord, the household and the neighbour.\n\n"
        "This is part five of the eight-part Home Management suite. A standard .xlsx workbook that opens in Excel and Google Sheets, with no macros, no accounts and no yearly renewal, with a demo copy full of sample data and a blank copy. Dates and totals are calculated from your entries and are not advice."),
    "features": ["Warranty countdown for every item from the end date you type", "Ranked list of warranties ending in 90 days", "Where is the manual and receipt search", "Repair or replace view against your own rule",
                 "Missing receipts, manuals and serial numbers ranked", f"{len(tools)} tools for the questions of every month", f"{len(forms)} printable sheets and {len(documents)} documents",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages", "No macros, no accounts, no yearly renewal"]}
lists = lists_base + verdict_lists()
assert len(lists) <= 20, len(lists)
s = spec(id=f'{SUITE}-p5', slug='home-management-inventory', profession='Home Management', name='Home Inventory and Warranties',
         tagline='Know what you own, what is still covered and where the papers are', price_usd=29,
         colors={"primary": "#3E5C76", "accent": "#E07A5F"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 5, "of": 8, "focus": "Home inventory and warranties"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ho5.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'lists', len(lists), 'desc', len(listing['description']), 'title', len(listing['title']))
