"""Wedding Planning suite - part 8: Attire, Decor, Gifts and Wrap-up (DIY make or buy, attire shopping, gifts and thank-you notes, cash gifts, final budget, returns, paperwork)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from wp8_lists import *
from wp8_tables import settings, tables
from wp8_tools import tools
import wp8_data as D

SUITE = 'fx-20261116-wedding'
NOTE = "Sample wording: adapt it to your own wedding."
YES = '{list:yesno.yes}'
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c_): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c_, t, idc)

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('diy_project_sheet', 'DIY Project Sheet', 'DIY project with its cost to make', 'diy.diy_id', F(
        ('Project', 'diy.project'), ('Basis', 'diy.basis'), ('Hours of work', 'diy.hours'), ('Cost to buy', 'diy.buy_cost'), ('Status', 'diy.status'), ('Planned start', 'diy.start_by'), ('Owner', 'diy.owner'),
        ('Supplies cost', 'diy.supplies_cost'), ('Cost to make', 'diy.make_cost'), ('Saving from making', 'diy.saving'), ('Make or buy', 'diy.make_or_buy'), ('Latest start', 'diy.latest_start')) + [
        FF('Days from today to the planned start', '%s-{today}' % LK('diy', 'diy_id', 'start_by'), 'int'), FF('Cost to make per hour of work', 'IFERROR(%s/%s,0)' % (LK('diy', 'diy_id', 'make_cost'), LK('diy', 'diy_id', 'hours')), 'money')]),
    FORM('supply_sheet', 'Supply Sheet', 'Supply with its quantity and cost', 'supplies.supply_id', F(
        ('Project', 'supplies.project'), ('Item', 'supplies.item'), ('Basis', 'supplies.basis'), ('Quantity per', 'supplies.qty_per'), ('Unit cost', 'supplies.unit_cost'), ('Status', 'supplies.status'), ('Bought on', 'supplies.bought_on'),
        ('Quantity for your headcount and tables', 'supplies.qty'), ('Cost', 'supplies.cost')) + [
        FF('Share of the project supplies cost', 'IFERROR(%s/SUMIFS({range:supplies.cost},{range:supplies.diy_id},%s),0)' % (LK('supplies', 'supply_id', 'cost'), LK('supplies', 'supply_id', 'diy_id')), 'pct')]),
    FORM('attire_sheet', 'Attire Shopping Sheet', 'Attire item with its order-by date', 'attire.attire_id', F(
        ('Item', 'attire.item'), ('For', 'attire.for_person'), ('Kind', 'attire.kind'), ('Vendor', 'attire.vendor'), ('Cost', 'attire.cost'), ('Status', 'attire.status'), ('Order by', 'attire.order_by'), ('In budget', 'attire.in_budget'),
        ('Action', 'attire.action')) + [
        FF('Days from order-by date to the wedding', '{set:wedding_day}-%s' % LK('attire', 'attire_id', 'order_by'), 'int'), FF('Share of all attire cost', 'IFERROR(%s/SUM({range:attire.cost}),0)' % LK('attire', 'attire_id', 'cost'), 'pct')]),
    FORM('gift_entry_sheet', 'Gift Entry Sheet', 'Gift with its thank-you state', 'gifts.gift_id', F(
        ('Date', 'gifts.date'), ('Household', 'gifts.household'), ('Event', 'gifts.event'), ('Kind', 'gifts.kind'), ('Description', 'gifts.description'), ('Cash amount', 'gifts.amount'), ('Cash gift goes to', 'gifts.cash_use'),
        ('Contact', 'gifts.contact'), ('Thank-you state', 'gifts.status'), ('Note written on', 'gifts.written_on'), ('Note sent on', 'gifts.sent_on'), ('Days to write the note', 'gifts.days_to_note')) + [
        FF('Your target date for the note', '%s+{set:thankyou_target_days}' % LK('gifts', 'gift_id', 'date'), 'date')]),
    FORM('cash_gift_sheet', 'Cash Gift Sheet', 'Cash gift with where it goes', 'gifts.gift_id', F(
        ('Household', 'gifts.household'), ('Date', 'gifts.date'), ('Event', 'gifts.event'), ('Cash amount', 'gifts.amount'), ('Cash gift goes to', 'gifts.cash_use'), ('Through your payment provider', 'gifts.via_provider'),
        ('Fee on this gift', 'gifts.fee'), ('You keep', 'gifts.kept'), ('Thank-you state', 'gifts.status')) + [
        FF('Share of all cash gifts received', 'IFERROR(%s/SUM({range:gifts.amount}),0)' % LK('gifts', 'gift_id', 'amount'), 'pct')]),
    FORM('thankyou_note_sheet', 'Thank-you Note Sheet', 'Thank-you note with its dates', 'thanks.note_id', F(
        ('Gift ID', 'thanks.gift_id'), ('Household', 'thanks.household'), ('Gift date', 'thanks.gift_date'), ('Written on', 'thanks.written_on'), ('Sent on', 'thanks.sent_on'), ('Channel', 'thanks.channel'),
        ('Days to write', 'thanks.days_to_write'), ('Days to send', 'thanks.days_to_send'), ('State', 'thanks.state')) + [
        FF('Your target date for the note', '%s+{set:thankyou_target_days}' % LK('thanks', 'note_id', 'gift_date'), 'date'), FF('Days ahead of your target', '{set:thankyou_target_days}-%s' % LK('thanks', 'note_id', 'days_to_write'), 'int')]),
    FORM('thankyou_sent_sheet', 'Thank-you Sent Sheet', 'Where the written notes stand', 'thanks.note_id', F(
        ('Household', 'thanks.household'), ('Written on', 'thanks.written_on'), ('Sent on', 'thanks.sent_on'), ('State', 'thanks.state'), ('Channel', 'thanks.channel')) + [
        FF('Notes written in total', 'COUNTIFS({range:thanks.note_id},"<>")', 'int'), FF('Notes sent in total', 'COUNTIFS({range:thanks.sent_on},">0")', 'int'),
        FF('Notes written but not sent', 'COUNTIFS({range:thanks.note_id},"<>")-COUNTIFS({range:thanks.sent_on},">0")', 'int')]),
    FORM('fee_sheet', 'Fee Sheet', 'Fee on a cash gift', 'gifts.gift_id', F(
        ('Household', 'gifts.household'), ('Cash amount', 'gifts.amount'), ('Through your payment provider', 'gifts.via_provider'), ('Fee on this gift', 'gifts.fee'), ('You keep', 'gifts.kept')) + [
        FF('Percent fee you entered', '{set:provider_fee_pct}', 'pct'), FF('Fixed fee you entered', '{set:provider_fee_flat}', 'money'),
        FF('Fee as share of this gift', 'IFERROR(%s/%s,0)' % (LK('gifts', 'gift_id', 'fee'), LK('gifts', 'gift_id', 'amount')), 'pct'), FF('Fees on all cash gifts', 'SUM({range:gifts.fee})', 'money')]),
    FORM('return_sheet', 'Return Sheet', 'Return or refund with its date', 'returns.return_id', F(
        ('Item', 'returns.item'), ('Vendor', 'returns.vendor'), ('Kind', 'returns.kind'), ('Due date', 'returns.due_date'), ('Status', 'returns.status'), ('Days to the due date', 'returns.days_to_due'),
        ('Flag', 'returns.flag')) + [
        FF('Days after the wedding', '%s-{set:wedding_day}' % LK('returns', 'return_id', 'due_date'), 'int'), FF('Refund expected on this item', '%s+0' % LK('returns', 'return_id', 'refund'), 'money'), FF('Refunds expected in total', 'SUMIFS({range:returns.refund},{range:returns.status},"<>"&%s)' % tok('rstatus', 'Done'), 'money')]),
    FORM('vendor_balance_sheet', 'Vendor Balance Sheet', 'Vendor balance with its dates', 'balances.vendor_id', F(
        ('Vendor', 'balances.vendor'), ('Contract total', 'balances.contract_total'), ('Paid', 'balances.paid'), ('Next payment', 'balances.next_due'), ('Final payment', 'balances.final_due'), ('Still due', 'balances.still_due'),
        ('Days to the next payment', 'balances.days_to_next'), ('State', 'balances.state')) + [
        FF('Share of the contract paid', 'IFERROR(%s/%s,0)' % (LK('balances', 'vendor_id', 'paid'), LK('balances', 'vendor_id', 'contract_total')), 'pct')]),
    FORM('paperwork_step_sheet', 'Paperwork Step Sheet', 'Paperwork or name change step', 'paperwork.item_id', F(
        ('Step', 'paperwork.item'), ('Kind', 'paperwork.kind'), ('Optional', 'paperwork.optional'), ('Due date', 'paperwork.due_date'), ('Status', 'paperwork.status'), ('Owner', 'paperwork.owner'), ('Flag', 'paperwork.flag')) + [
        FF('Days from today to the due date', '%s-{today}' % LK('paperwork', 'item_id', 'due_date'), 'int'), FF('Days from the due date to the wedding', '%s-{set:wedding_day}' % LK('paperwork', 'item_id', 'due_date'), 'int')]),
    FORM('wrapup_sheet', 'Wrap-up Sheet', 'Wrap-up check with its count', 'wrapup.check', F(
        ('Still open', 'wrapup.count'), ('Status', 'wrapup.status')) + [
        FF('Checks done in total', 'COUNTIFS({range:wrapup.status},%s)' % c('Done'), 'int'), FF('Checks still to finish', 'COUNTIFS({range:wrapup.status},%s)' % c('To finish'), 'int'),
        FF('Share of the checks done', 'IFERROR(COUNTIFS({range:wrapup.status},%s)/COUNTIFS({range:wrapup.check},"<>"),0)' % c('Done'), 'pct')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('diy_plan_page', 'DIY Plan Page', 'DIY plan for one project', 'diy.diy_id', [
        '{set:couple}, dated {today}. DIY plan for {col:diy.project}, project {col:diy.diy_id}.',
        'Owner: {col:diy.owner}. Status: {col:diy.status}. The work is about {col:diy.hours} hours, planned to start on {col:diy.start_by}. At your hours a week it needs {col:diy.weeks_needed} weeks, so the latest start is {col:diy.latest_start}.',
        'Supplies cost {col:diy.supplies_cost} for {col:diy.units} units on a {col:diy.basis} basis. The start check says: {col:diy.start_flag}.'], ['Owner', 'Partner'], NOTE),
    DOC('diy_shopping_page', 'DIY Shopping List Page', 'DIY shopping list', 'shopping.rank', [
        '{set:couple}, dated {today}. DIY shopping list.',
        'Item {col:shopping.rank}: {col:shopping.item} for {col:shopping.project}. Quantity {col:shopping.qty}, cost {col:shopping.cost}, status {col:shopping.status}.',
        'In all, {col:shopping.count_left} supplies are still to buy, about {col:shopping.cost_left}. Quantities follow your headcount and table count in your settings.'], ['Shopper'], NOTE),
    DOC('make_buy_page', 'Make or Buy Page', 'Make or buy for one project', 'diy.diy_id', [
        '{set:couple}, dated {today}. Make or buy: {col:diy.project}.',
        'Making it costs {col:diy.make_cost}: supplies {col:diy.supplies_cost} plus {col:diy.hours} hours of your work at {set:diy_hour_value} an hour. Buying or renting it costs {col:diy.buy_cost}.',
        'The saving from making it is {col:diy.saving}, so the verdict is: {col:diy.make_or_buy}. Your own rule is to make a project only when it costs at least {set:make_margin} less than buying.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('attire_page', 'Attire Shopping Page', 'Attire shopping item', 'attire.attire_id', [
        '{set:couple}, dated {today}. Attire shopping: {col:attire.item}, item {col:attire.attire_id}.',
        'For {col:attire.for_person}, kind {col:attire.kind}, cost {col:attire.cost}, status {col:attire.status}. Order it by {col:attire.order_by}.',
        'Action: {col:attire.action}. In the budget: {col:attire.in_budget}. The roster and fittings of the wedding party are kept in the wedding party workbook.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('gift_log_page', 'Gift Log Page', 'Gift log of one household', 'ledger.household_id', [
        '{set:couple}, dated {today}. Gift log for {col:ledger.household}, household {col:ledger.household_id}.',
        'Contact: {col:ledger.contact}. Gifts received: {col:ledger.gifts}. Cash gifts: {col:ledger.cash}. Last gift on {col:ledger.last_gift}.',
        'Share of the gifts already thanked: {col:ledger.thanked_share}. Gifts still without a note: {col:ledger.waiting}.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('thankyou_list_page', 'Thank-you Note List Page', 'Thank-you note list entry', 'backlog.rank', [
        '{set:couple}, dated {today}. Thank-you list, entry {col:backlog.rank}.',
        'Gift {col:backlog.gift_id} from {col:backlog.household}, {col:backlog.description}, received on {col:backlog.date} at the {col:backlog.event}. It has waited {col:backlog.days_waiting} days: {col:backlog.verdict}.',
        'In all, {col:backlog.waiting_n} gifts have no note and {col:backlog.written} of {col:backlog.total} notes are written. The oldest wait is {col:backlog.oldest_days} days. At {col:backlog.rate} notes a week you finish by your target.'], ['Writer'], NOTE),
    DOC('thankyou_wording_page', 'Thank-you Wording Page', 'Thank-you note wording', 'gifts.gift_id', [
        'Dear {col:gifts.contact},',
        'Thank you so much for the {col:gifts.description} you gave us at the {col:gifts.event}. It was kind of you to think of us, and we will think of you each time we use it.',
        'Our thanks for being part of the road to our wedding. With love, {set:couple}.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('cash_honeymoon_page', 'Cash Gifts and Honeymoon Page', 'Cash gifts and the honeymoon fund', 'honeyfund.hf_id', [
        '{set:couple}, dated {today}. Honeymoon fund line {col:honeyfund.hf_id}, month {col:honeyfund.month}.',
        'Source {col:honeyfund.source}, amount {col:honeyfund.amount}, status {col:honeyfund.status}. The honeymoon budget is {set:honeymoon_goal}.',
        'Funds received so far: {col:honeyfund.funds}. Savings promised: {col:honeyfund.promised}. Gap to the honeymoon budget: {col:honeyfund.gap}. Cash gifts that are not confirmed are never counted until received.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('final_budget_page', 'Final Budget Page', 'Final budget of one category', 'final.category', [
        '{set:couple}, dated {today}. Final budget against actual: {col:final.category}.',
        'Planned {col:final.planned}, committed {col:final.committed}, paid {col:final.paid}, still due {col:final.still_due}. Over or under plan: {col:final.variance}. Verdict: {col:final.verdict}.',
        'This category is {col:final.share} of the final cost. The final cost so far is {col:final.total_cost}, which is {col:final.per_guest} per guest.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('cost_guest_page', 'Cost per Guest Page', 'What the wedding cost per guest', 'perguest.item', [
        '{set:couple}, dated {today}. What the wedding cost: {col:perguest.item}.',
        'Amount {col:perguest.amount}, which is {col:perguest.per_guest} per guest at a final headcount of {set:headcount}.',
        'Your own target is {set:cost_per_guest_target} per guest. A typical starting value is {set:cost_per_guest_bench}, which is not a fact about your area.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('balances_returns_page', 'Vendor Balances Page', 'Vendor balance and what to return', 'balances.vendor_id', [
        '{set:couple}, dated {today}. Vendor balance: {col:balances.vendor}, {col:balances.vendor_id}.',
        'Contract total {col:balances.contract_total}, paid {col:balances.paid}, still due {col:balances.still_due}. Next payment on {col:balances.next_due}, final payment on {col:balances.final_due}. State: {col:balances.state}.',
        'In all, {col:balances.balances_n} vendors have a balance, {col:balances.balances_total} still due. Check your contract for the terms of each payment and any deposit return.'], ['Partner 1', 'Partner 2'], NOTE),
    DOC('paperwork_page', 'Paperwork Page', 'Paperwork and name change step', 'paperwork.item_id', [
        '{set:couple}, dated {today}. Paperwork step {col:paperwork.item_id}: {col:paperwork.item}.',
        'Kind: {col:paperwork.kind}. Optional: {col:paperwork.optional}. Due on {col:paperwork.due_date}. Status: {col:paperwork.status}. Owner: {col:paperwork.owner}.',
        'Check with your officiant or local office what each step needs. Optional rows are yours to edit, hide or delete.'], ['Partner 1', 'Partner 2'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('diy_project_start', 'DIY Project Start', 'diy', 'diy.start_by', [('Collect the supplies and clear a table', 0), ('Make one test piece', 2), ('Make the first batch', 7), ('Check the quantity against your headcount', 10), ('Finish and store it', 14)]),
    CHK('diy_supplies_run', 'DIY Supplies Run', 'diy', 'diy.start_by', [('Print the shopping list', 0), ('Buy the per-table items', 1), ('Buy the per-guest items', 2), ('Check each item against the list', 3), ('Mark the supplies as bought', 4)]),
    CHK('attire_pickup', 'Attire Pick-up', 'attire', 'attire.order_by', [('Confirm the order and the date', 0), ('Pick up or receive the item', 14), ('Try it on and check the fit', 15), ('Book any alterations', 17), ('Hang it in its bag', 30)]),
    CHK('gift_log_day', 'Gift Log on the Day', 'gifts', 'gifts.date', [('Write down who gave what', 0), ('Keep the card with the gift', 0), ('Add the gift to the log', 1), ('Photograph the gift if you like', 1)]),
    CHK('thankyou_weekly', 'Thank-you Notes Weekly', 'gifts', 'gifts.date', [('Open the thank-you backlog', 0), ('Write the oldest notes first', 3), ('Send the notes you wrote', 7), ('Mark each gift as thanked', 7)]),
    CHK('thankyou_after', 'Thank-you Notes After the Day', 'gifts', 'gifts.date', [('Write the notes for the wedding gifts', 0), ('Add a photo if you like', 14), ('Send the notes', 28), ('Finish by your target day', 56)]),
    CHK('cash_gift_handling', 'Cash Gift Handling', 'gifts', 'gifts.date', [('Count the cash or confirm the transfer', 0), ('Log the amount in the gift log', 1), ('Choose the budget or the honeymoon', 3), ('Enter any fee your provider took', 7)]),
    CHK('return_rentals', 'Return Rentals, Claim Deposits', 'returns', 'returns.due_date', [('Gather the items and check them against the list', 0), ('Return them or book the pick-up', 1), ('Ask for the deposit back', 3), ('Mark the refund as received', 14)]),
    CHK('final_balances', 'Final Vendor Balances', 'balances', 'balances.final_due', [('Check the invoice against the contract', 0), ('Pay the balance by the date', 1), ('Ask for a receipt', 2), ('Mark it paid and tip as planned', 3)]),
    CHK('final_budget_guest', 'Final Budget and Cost per Guest', 'funding', 'funding.date', [('Mark every contract as paid or still due', 1), ('Save the final budget against actual', 7), ('Work out the cost per guest', 8), ('Write down what you would change', 14)]),
    CHK('paperwork_name', 'Paperwork and Name Change', 'paperwork', 'paperwork.due_date', [('Ask your officiant or local office what is needed', 0), ('Gather the documents', 3), ('Complete the step', 7), ('Mark it done', 8)]),
    CHK('small_after', 'Small Wedding After the Day', 'returns', 'returns.due_date', [('Return anything borrowed or rented', 0), ('Pay any last balance', 3), ('Write the thank-you notes', 7), ('Save the final budget and the photos', 14)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(key_, moment, table, phone, text): return MSG(key_, moment, table, phone, text)
messages = [
    M('m_thanks_item', 'Household: thank you for the gift', 'gifts', 'gifts.phone', 'Hello {contact}, thank you for the {description}, we love it. {couple}'),
    M('m_thanks_cash', 'Household: thank you for your gift', 'cash', 'cash.phone', 'Hello {contact}, thank you for your gift of {amount}. It means a lot to us. {couple}'),
    M('m_thanks_celebrate', 'Household: thank you for celebrating', 'ledger', 'ledger.phone', 'Hello {contact}, thank you for celebrating with us. {couple}'),
    M('m_thanks_event', 'Household: thank you for the event gift', 'gifts', 'gifts.phone', 'Hello {contact}, thank you for the gift at the {event}. {couple}'),
    M('m_writing_now', 'Household: we are writing your note', 'backlog', 'backlog.phone', 'Hello {contact}, we are writing your thank-you note now and it will reach you soon. {couple}'),
    M('m_friend_notes', 'Friend helper: help with notes', 'backlog', 'backlog.friend_phone', 'Can you help write notes this week? {waiting_n} gifts are waiting. {couple}'),
    M('m_friend_diyday', 'Friend helper: DIY day', 'diy', 'diy.friend_phone', 'DIY day for {project} is on {start_by}. Please bring {item}. {couple}'),
    M('m_friend_list', 'Friend helper: supplies list', 'diy', 'diy.friend_phone', 'The supplies list for {project} is attached. {couple}'),
    M('m_friend_collect', 'Friend helper: collect from the shop', 'shopping', 'shopping.friend_phone', 'Please collect {item} from the shop, quantity {qty}. {couple}'),
    M('m_parent1_help', 'Parent of partner 1: thanks for the help', 'diy', 'diy.parent1_phone', 'Thank you for the help with {project}. {couple}'),
    M('m_parent2_help', 'Parent of partner 2: thanks for the help', 'diy', 'diy.parent2_phone', 'Thank you for the help with {project}. {couple}'),
    M('m_lead_diy', 'Wedding party lead: DIY day', 'diy', 'diy.lead_phone', 'The DIY day for {project} is on {start_by}. Can you bring one helper? {couple}'),
    M('m_lead_return', 'Wedding party lead: return the items', 'returns', 'returns.lead_phone', 'Please return {item} by {due_date}. {couple}'),
    M('m_partner_unthanked', 'Partner: gifts without a note', 'backlog', 'backlog.partner_phone', '{over_n} gifts have no note after {alert_days} days. The oldest has waited {oldest_days} days.'),
    M('m_partner_pace', 'Partner: notes pace', 'backlog', 'backlog.partner_phone', 'We have written {written} of {total} notes. {rate} a week finishes the backlog by your target.'),
    M('m_partner_cash', 'Partner: cash gifts received', 'cash', 'cash.partner_phone', 'Cash gifts received are {total_received}. Expected gifts of {expected} are not counted until received.'),
    M('m_partner_honey', 'Partner: honeymoon fund', 'honeyfund', 'honeyfund.partner_phone', 'The honeymoon fund is {funds}, the gap is {gap}.'),
    M('m_partner_make', 'Partner: make or buy', 'diy', 'diy.partner_phone', 'Verdict for {project}: {make_or_buy}, saving {saving}.'),
    M('m_partner_start', 'Partner: DIY start date', 'diy', 'diy.partner_phone', 'Start {project} by {latest_start} to finish early.'),
    M('m_partner_cost', 'Partner: final cost per guest', 'final', 'final.partner_phone', 'The final cost so far is {total_cost}, per guest {per_guest}.'),
    M('m_partner_balances', 'Partner: vendor balances', 'balances', 'balances.partner_phone', '{balances_n} vendor balances are still due, {balances_total} in total.'),
    M('m_partner_returns', 'Partner: items to return', 'returns', 'returns.partner_phone', '{open_n} items to return, the first on {first_due}, refunds expected {open_refund}.'),
    M('m_partner_paper', 'Partner: paperwork step', 'paperwork', 'paperwork.partner_phone', 'Paperwork step: {item}, due on {due_date}. Optional rows are yours to skip.'),
    M('m_partner_wrap', 'Partner: wrap-up steps left', 'paperwork', 'paperwork.partner_phone', 'The wrap-up has {steps_left} steps left.'),
    M('m_attire_pickup', 'Attire shop: confirm pick-up', 'attire', 'attire.phone', 'Hello, please confirm pick-up of {item} on {order_by}. {couple}'),
    M('m_attire_return', 'Attire shop: confirm the return', 'returns', 'returns.phone', 'Hello, please confirm the return of the accessories on {due_date}. {couple}'),
    M('m_rentals', 'Rentals: pick-up and deposit', 'returns', 'returns.phone', 'Please confirm the pick-up on {due_date} and the deposit refund of {refund}. {couple}'),
    M('m_venue_deposit', 'Venue: security deposit', 'returns', 'returns.phone', 'Please confirm the return of the security deposit of {refund}. {couple}'),
    M('m_florist_vases', 'Florist: collect the vases', 'returns', 'returns.phone', 'Please collect the vases on {due_date}. {couple}'),
    M('m_cake_stand', 'Cake baker: collect the cake stand', 'returns', 'returns.phone', 'Please collect the cake stand on {due_date}. {couple}'),
    M('m_caterer_invoice', 'Caterer: final invoice', 'balances', 'balances.phone', 'Hello {vendor}, please send the final invoice after the headcount adjustment. {couple}'),
    M('m_photo_gallery', 'Photographer: send the gallery', 'returns', 'returns.phone', 'Please send the gallery by {due_date}. {couple}'),
    M('m_hotel_credit', 'Hotel contact: unused rooms credit', 'returns', 'returns.phone', 'Please confirm the unused rooms credit of {refund}. {couple}'),
    M('m_vendor_thanks', 'Vendor: thank you for the day', 'balances', 'balances.phone', 'Thank you for the day, {vendor}. Here is a note and a photo. {couple}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ dashboard
def Z(t, c_): return '{range:%s.%s}' % (t, c_)
KP = [
    KPI('DIY projects', 'COUNTIFS(%s,"<>")' % Z('diy', 'diy_id'), 'int'),
    KPI('DIY projects done', 'COUNTIFS(%s,%s)' % (Z('diy', 'status'), tok('dstatus', 'Done')), 'int'),
    KPI('DIY hours left', 'SUM(%s)' % Z('diy', 'hours_left'), 'num'),
    KPI('DIY cost to make', 'SUM(%s)' % Z('diy', 'make_cost'), 'money'),
    KPI('DIY cost to buy', 'SUM(%s)' % Z('diy', 'buy_cost'), 'money'),
    KPI('DIY saving from making', 'SUMIFS(%s,%s,%s)' % (Z('diy', 'saving'), Z('diy', 'make_or_buy'), c('Make')), 'money'),
    KPI('Supplies still to buy', 'COUNTIFS(%s,1)' % Z('supplies', 'to_buy'), 'int'),
    KPI('Supplies cost still to buy', 'SUM(%s)' % Z('supplies', 'cost_to_buy'), 'money'),
    KPI('Days to the next DIY start', 'MIN(%s)' % Z('diy', 'days_to_start'), 'int'),
    KPI('Attire items still to order', 'COUNTIFS(%s,%s)' % (Z('attire', 'status'), tok('sstatus', 'To buy')), 'int'),
    KPI('Attire cost total', 'SUM(%s)' % Z('attire', 'cost'), 'money'),
    KPI('Attire cost in the budget', 'SUMIFS(%s,%s,%s)' % (Z('attire', 'cost'), Z('attire', 'in_budget'), YES), 'money'),
    KPI('Gifts received', 'COUNTIFS(%s,"<>")' % Z('gifts', 'gift_id'), 'int'),
    KPI('Gifts without a note', 'COUNTIFS(%s,0)' % Z('gifts', 'thanked'), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Gifts waiting more than the alert days', 'COUNTIFS(%s,1)' % Z('gifts', 'late'), 'int', alert={"when": "> 0", "style": "bad"}),
    KPI('Oldest wait for a note, days', 'MAX(%s)' % Z('gifts', 'days_waiting'), 'int'),
    KPI('Notes written', 'COUNTIFS(%s,"<>")' % Z('thanks', 'note_id'), 'int'),
    KPI('Notes sent', 'COUNTIFS(%s,">0")' % Z('thanks', 'sent_on'), 'int'),
    KPI('Notes written, not sent', 'COUNTIFS(%s,"<>")-COUNTIFS(%s,">0")' % (Z('thanks', 'note_id'), Z('thanks', 'sent_on')), 'int', alert={"when": "> 0", "style": "warn"}),
    KPI('Share of gifts thanked', 'IFERROR(COUNTIFS(%s,1)/COUNTIFS(%s,"<>"),0)' % (Z('gifts', 'thanked'), Z('gifts', 'gift_id')), 'pct'),
    KPI('Cash gifts received', 'SUM(%s)' % Z('gifts', 'amount'), 'money'),
    KPI('Cash gifts expected, not confirmed', 'SUMIFS(%s,%s,%s,%s,%s)+SUMIFS(%s,%s,%s,%s,%s)' % (Z('funding', 'amount'), Z('funding', 'source'), tok('source', 'Cash gifts'), Z('funding', 'status'), tok('fstatus', 'Not confirmed'),
                                                                                               Z('honeyfund', 'amount'), Z('honeyfund', 'source'), tok('hsource', 'Cash gifts'), Z('honeyfund', 'status'), tok('fstatus', 'Not confirmed')), 'money'),
    KPI('Fee on cash gifts', 'SUM(%s)' % Z('gifts', 'fee'), 'money'),
    KPI('Cash gifts toward the honeymoon', 'SUMIFS(%s,%s,%s)' % (Z('gifts', 'amount'), Z('gifts', 'cash_use'), tok('cuse', 'Honeymoon fund')), 'money'),
    KPI('Final cost so far', 'SUM(%s)' % Z('final', 'committed'), 'money'),
    KPI('Final cost per guest', 'ROUND(SUM(%s)/{set:headcount},0)' % Z('final', 'committed'), 'money'),
    KPI('Variance to plan, negative is under', 'SUM(%s)-SUM(%s)' % (Z('final', 'committed'), Z('final', 'planned')), 'money'),
    KPI('Unpaid vendor balances', 'SUM(%s)' % Z('balances', 'still_due'), 'money', alert={"when": "> 0", "style": "warn"}),
    KPI('Items to return', 'COUNTIFS(%s,"<>")-COUNTIFS(%s,%s)' % (Z('returns', 'return_id'), Z('returns', 'status'), tok('rstatus', 'Done')), 'int'),
    KPI('Refunds expected', 'SUMIFS(%s,%s,"<>"&%s)' % (Z('returns', 'refund'), Z('returns', 'status'), tok('rstatus', 'Done')), 'money'),
]
kpis = KP
assert len(kpis) == 30
dashboard = {"title": "After the Wedding Dashboard", "kpis": kpis,
    "monthly": {"title": "Cash gifts and honeymoon fund by month", "date": "gifts.month", "series": [
        {"label": "Cash gifts", "sum": "gifts.amount", "date": "gifts.month"}, {"label": "Honeymoon fund", "sum": "honeyfund.amount", "date": "honeyfund.month"}]},
    "breakdowns": [{"title": "DIY projects by status", "by": "diy.status", "agg": "count"}, {"title": "Gifts by event", "by": "gifts.event", "agg": "count"},
                   {"title": "Committed by category", "by": "budget.category", "value": "budget.committed", "agg": "sum"}, {"title": "Returns by status", "by": "returns.status", "agg": "count"}]}

def W(col, op, v): return (col, op, v)
insights = {"filters": [{"label": "Event", "list": "gevent"}, {"label": "Owner", "list": "owner"}],
    "gauges": [
        {"title": "Gifts thanked", "num": AGG('count', 'gifts', where=[('thanked', '=', 1)]), "den": AGG('count', 'gifts', where=[('thanked', '>=', 0)])},
        {"title": "Thank-you notes sent, of those written", "num": AGG('count', 'thanks', where=[('is_sent', '=', 1)]), "den": AGG('count', 'thanks', where=[('is_sent', '>=', 0)])},
        {"title": "DIY projects done", "num": AGG('count', 'diy', where=[('status', '=', tok('dstatus', 'Done'))]), "den": AGG('count', 'diy', where=[('hours', '>=', 0)])},
        {"title": "Vendor contracts paid", "num": AGG('sum', 'balances', 'balances.paid'), "den": AGG('sum', 'balances', 'balances.contract_total')},
        {"title": "Returns done", "num": AGG('count', 'returns', where=[('is_done', '=', 1)]), "den": AGG('count', 'returns', where=[('is_done', '>=', 0)])},
        {"title": "Paperwork steps done", "num": AGG('count', 'paperwork', where=[('is_done', '=', 1)]), "den": AGG('count', 'paperwork', where=[('is_done', '>=', 0)])}],
    "charts": [
        CHART('DIY cost to make against buy by project', 'bar', 'diy.project', [AGG('sum', 'diy', 'diy.make_cost', label='Cost to make'), AGG('sum', 'diy', 'diy.buy_cost', label='Cost to buy')]),
        CHART('DIY hours by project', 'bar', 'diy.project', [AGG('sum', 'diy', 'diy.hours', label='Hours')]),
        CHART('DIY projects by status', 'bar', 'diy.status', [AGG('count', 'diy', label='Projects')]),
        CHART('Supplies by status', 'bar', 'supplies.status', [AGG('count', 'supplies', label='Supplies')]),
        CHART('Supplies cost by project', 'bar', 'supplies.project', [AGG('sum', 'supplies', 'supplies.cost', label='Supplies cost')]),
        CHART('Supplies cost by basis', 'bar', 'supplies.basis', [AGG('sum', 'supplies', 'supplies.cost', label='Supplies cost')]),
        CHART('Attire cost by kind', 'bar', 'attire.kind', [AGG('sum', 'attire', 'attire.cost', label='Cost')]),
        CHART('Attire items by status', 'bar', 'attire.status', [AGG('count', 'attire', label='Items')]),
        CHART('Gifts by event', 'bar', 'gifts.event', [AGG('count', 'gifts', label='Gifts')]),
        CHART('Gifts by kind', 'bar', 'gifts.kind', [AGG('count', 'gifts', label='Gifts')]),
        CHART('Gifts received by month', 'column', 'month', [AGG('count', 'gifts', date='gifts.date', label='Gifts')]),
        CHART('Cash gifts by month', 'column', 'month', [AGG('sum', 'gifts', 'gifts.amount', date='gifts.date', label='Cash gifts')]),
        CHART('Notes written by month', 'column', 'month', [AGG('count', 'thanks', date='thanks.written_on', label='Notes written')]),
        CHART('Notes by channel', 'bar', 'thanks.channel', [AGG('count', 'thanks', label='Notes')]),
        CHART('Gifts thanked and not thanked by event', 'bar', 'gifts.event', [AGG('count', 'gifts', label='Thanked', where=[('thanked', '=', 1)]), AGG('count', 'gifts', label='Not thanked', where=[('thanked', '=', 0)])]),
        CHART('Cash gifts by where they go', 'bar', 'gifts.cash_use', [AGG('sum', 'gifts', 'gifts.amount', label='Cash gifts')]),
        CHART('Funding by source and status', 'bar', 'funding.source', [AGG('sum', 'funding', 'funding.amount', label='Received', where=[('status', '=', tok('fstatus', 'Received'))]),
                                                                       AGG('sum', 'funding', 'funding.amount', label='Promised', where=[('status', '=', tok('fstatus', 'Promised'))]),
                                                                       AGG('sum', 'funding', 'funding.amount', label='Not confirmed', where=[('status', '=', tok('fstatus', 'Not confirmed'))])]),
        CHART('Honeymoon fund by month', 'column', 'month', [AGG('sum', 'honeyfund', 'honeyfund.amount', date='honeyfund.month', label='Honeymoon fund')]),
        CHART('Planned, committed and paid by category', 'bar', 'budget.category', [AGG('sum', 'budget', 'budget.planned', label='Planned'), AGG('sum', 'budget', 'budget.committed', label='Committed'), AGG('sum', 'budget', 'budget.paid', label='Paid')]),
        CHART('Returns by kind', 'bar', 'returns.kind', [AGG('count', 'returns', label='Returns')]),
        CHART('Returns by status', 'bar', 'returns.status', [AGG('count', 'returns', label='Returns')]),
        CHART('Paperwork by kind and status', 'bar', 'paperwork.kind', [AGG('count', 'paperwork', label='Done', where=[('status', '=', tok('pstatus', 'Done'))]), AGG('count', 'paperwork', label='In progress', where=[('status', '=', tok('pstatus', 'In progress'))]),
                                                                          AGG('count', 'paperwork', label='Not started', where=[('status', '=', tok('pstatus', 'Not started'))])])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "DIY make or buy", "why": "supplies plus your hours at your own hour value against the cost to buy, with Make, Buy or Make half for every project", "where": "DIY Make or Buy"},
    {"name": "DIY start date", "why": "the latest day to start a project so the work is done your chosen days before the wedding, with Start by or Late by", "where": "DIY Start Date"},
    {"name": "Thank-you backlog ranker", "why": "every gift without a note ranked oldest first against your own alert days, with the notes to write this week", "where": "Thank-you Backlog Ranker"},
    {"name": "Thank-you pace", "why": "how many notes a week finish the backlog by your own target date, counted from the oldest gift", "where": "Thank-you Pace"},
    {"name": "Cash gifts and funding link", "why": "cash gifts split between the budget and the honeymoon; expected gifts are never counted until they are received", "where": "Cash Gifts and Funding"},
    {"name": "Honeymoon gap", "why": "the honeymoon budget against funds received and savings promised, with the saving a month that closes the gap", "where": "Honeymoon Gap"},
    {"name": "Final budget against actual", "why": "planned, committed, paid and still due for every category, with the one that ended over plan named", "where": "Final Budget Check"},
    {"name": "Cost per guest", "why": "the final cost over your final headcount against your own target and a typical starting value", "where": "Cost per Guest Check"},
    {"name": "Returns and refunds tracker", "why": "rentals to return and deposits to claim by date, with the refunds you can expect", "where": "Returns and Refunds Tracker"},
    {"name": "Wrap-up readiness", "why": "ten checks that tell you when the wedding can be closed: balances, returns, notes, budget and paperwork", "where": "Wrap-up Readiness"}]
competitors = [
    {"what": "a free planning app", "lacks": "keeps a to-do list but has no DIY make-or-buy, no thank-you backlog by days waiting and no final budget against actual"},
    {"what": "a single budget spreadsheet", "lacks": "totals the spend but never links cash gifts to the honeymoon, checks the cost per guest or tracks returns and deposits"},
    {"what": "a printable wedding binder", "lacks": "gives blank pages for gifts and notes, with no days-waiting count, no pace to finish and nothing that recalculates"},
    {"what": "a wedding website with a registry", "lacks": "lists gifts for guests but keeps your thank-you notes, cash gift fees and wrap-up checks out of your own hands"}]
guide = [
    'Open Start here and type your names, your wedding day, your final headcount and your table count. Replace demo data: clear the sample rows and type your own.',
    'List each DIY project in DIY projects with its hours, the cost to buy it and who owns it; add its supplies in Supplies with the quantity per guest, per table or once.',
    'Open DIY Make or Buy to see Make, Buy or Make half for each project, then DIY Start Date and DIY Hours Load to plan the work before the wedding.',
    'Use DIY Shopping Run and the Shopping list before each trip to the shop; quantities follow your headcount and tables.',
    'Add every attire item in Attire shopping with its order-by date; Attire Order Planner names the next item to order.',
    'Log each gift in the Gift Log the day it arrives, with the cash amount for cash gifts and where the money goes.',
    'Write each note in Thank-you notes; the Thank-you backlog lists the gifts still without one, oldest first, and Thank-you Pace says how many a week finish them.',
    'Cash Gifts and Funding and the Honeymoon Gap show what cash gifts do for the budget and the honeymoon; expected gifts are never counted until received.',
    'Enter the fee your payment provider charges in your settings and mark the gifts that came through it; Payment Service Fee shows what you keep.',
    'After the wedding open Final Budget Check and Cost per Guest Check, then Vendor Balance Check, Returns and Refunds Tracker and Paperwork Tracker.',
    'Wrap-up Readiness counts what is still open and says Close the wedding when nothing is left.',
    f'Use the {len(tools)} tools, print {len(forms)} sheets and {len(documents)} pages, follow {len(checklists)} checklists and tap a message link to send a text with the details written in.',
    'A couple with a small wedding uses the gift log, the thank-you notes, the final budget and the wrap-up with no DIY: leave the DIY and attire sheets empty.',
    'No macros; it works in Excel and Google Sheets and prints for the day. Why a workbook: one flat price, no vendor ever sees your details, no gift fees and your own numbers.',
    'What this is not: not a booking service, not a payment service, and not legal or tax advice. Check with your officiant or local office, and ask your accountant what your own rules need.']
listing = {"title": "Wedding After and Gifts Excel Template: DIY Make or Buy, Thank-you Note Tracker, Cash Gifts, Final Budget, Cost per Guest, Returns",
    "headline": "Make or buy, thank every guest and close the wedding budget in one workbook",
    "tags": ["wedding planner", "thank you tracker", "wedding gift log", "diy wedding", "wedding budget", "cash gift tracker", "honeymoon fund", "cost per guest", "wedding checklist", "name change", "excel template", "wedding wrap up", "returns tracker"],
    "description": ("Close the last part of your wedding in one Excel workbook. Built for an engaged couple who make some of the decor themselves, log every shower and engagement gift, write thank-you notes and want to know what the wedding really cost. "
        "DIY projects and Supplies work out the quantity from your headcount and table count, set the cost to make against the cost to buy and say Make, Buy or Make half. The DIY start date, the DIY hours load and the shopping list keep the work done before the wedding. Attire shopping lists outfits, shoes, accessories and alterations with an order-by date.\n\n"
        "The Gift Log, Thank-you notes and Thank-you backlog show every gift without a note, oldest first, against your own alert days, and the pace tool says how many notes a week finish the job. Cash gifts are logged separately, linked to the honeymoon fund and the budget gap, and expected gifts are never counted until they are received. You enter the fee your payment provider charges and see what you keep.\n\n"
        "After the day, Final Budget against Actual shows planned, committed, paid and still due for every category, the cost per guest against your own target, the vendor balances still due, rentals to return and deposits to claim, and a paperwork and name change list in generic words with optional rows you can edit. A wrap-up check tells you when the wedding can be closed.\n\n"
        f"{len(tools)} tools answer weekly questions with a clear verdict. Print {len(forms)} sheets and {len(documents)} pages, follow {len(checklists)} checklists and send {len(messages)} ready text messages to guests, helpers, family and vendors. "
        "A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Guests appear as names only. It is a planning kit, not a booking or payment service, and gives no legal or tax advice. This is part eight of the Wedding Planning suite."),
    "features": ["DIY make or buy with a verdict per project", "DIY start date and hours load", "Shopping list scaled to your guests and tables", "Gift log with days waiting for a note", "Thank-you backlog, oldest first",
                 "Cash gifts linked to the honeymoon and budget gap", "Fee on cash gifts that you enter yourself", "Final budget against actual by category", "Cost per guest against your own target",
                 "Vendor balances, returns and deposit tracker", f"{len(tools)} decision tools", f"{len(forms)} printable sheets and {len(documents)} pages",
                 f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
s = spec(id=f'{SUITE}-p8', slug='wedding-after', profession='Wedding Planning', name='Attire, Decor, Gifts and Wrap-up',
         tagline='Make or buy, thank every guest and close the wedding budget in one workbook', price_usd=29,
         colors={"primary": "#7A4B68", "accent": "#D9A86C"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 8, "of": 8, "focus": "Attire, decor, gifts and after the wedding: DIY, thank-you notes, cash gifts, final budget, returns and paperwork"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wp8.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
