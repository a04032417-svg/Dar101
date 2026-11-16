"""Nonprofit suite part 4: Events and Campaigns. Writes np4.en.json."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from np4_lists import *
from np4_tables import settings, tables
from np4_tools import tools
import np4_data as D

SUITE = 'fx-20261115-nonprofit'
NOTE = "Sample wording: adapt it to your own organization and check your local rules."
YES = '{list:yesno.yes}'
DONE = tok('estatus', 'Done'); PLANNED = tok('estatus', 'Planned'); SOLD = tok('auction', 'Sold'); UNSOLD = tok('auction', 'Unsold'); DECL = tok('sstatus', 'Declined')
def F(*pairs): return [FV(a, b) for a, b in pairs]
def LK(t, idc, c): return 'INDEX({range:%s.%s},MATCH({pick},{range:%s.%s},0))' % (t, c, t, idc)
def R(t, c): return '{range:%s.%s}' % (t, c)

# ------------------------------------------------------------------ forms (12)
forms = [
    FORM('event_plan_sheet', 'Event Plan Sheet', 'Plan of one event', 'events.event_id', F(
        ('Event', 'events.event'), ('Kind', 'events.kind'), ('Date', 'events.date'), ('Venue', 'events.venue'), ('Doors open', 'events.doors'), ('Guests expected', 'events.expected'), ('Money goal', 'events.goal'), ('Budget cost', 'events.budget_cost'), ('Status', 'events.status')) + [
        FF('Days to the event', LK('events', 'event_id', 'days_to'), 'int'), FF('Seats sold so far', LK('events', 'event_id', 'seats_sold'), 'int'), FF('Seats left', 'N(%s)' % LK('events', 'event_id', 'seats_left'), 'int'),
        FF('Cost allowed at your setting', '%s*{set:cost_per_dollar}' % LK('events', 'event_id', 'goal'), 'money'), FF('Programs needed by', LK('events', 'event_id', 'program_by'), 'date')]),
    FORM('event_budget_sheet', 'Event Budget Sheet', 'Budget against actual cost of an event', 'events.event_id', F(
        ('Event', 'events.event'), ('Budget cost', 'events.budget_cost'), ('Actual cost so far', 'events.actual_cost'), ('Over budget by', 'events.cost_over'), ('Money goal', 'events.goal'), ('Money raised so far', 'events.raised'), ('Net raised so far', 'events.net_raised')) + [
        FF('Limit counted as over budget', '%s*(1+{set:over_budget_pct})' % LK('events', 'event_id', 'budget_cost'), 'money'), FF('Budget as a share of the goal', 'IFERROR(%s/%s,0)' % (LK('events', 'event_id', 'budget_cost'), LK('events', 'event_id', 'goal')), 'pct'),
        FF('Cost allowed at your setting', '%s*{set:cost_per_dollar}' % LK('events', 'event_id', 'goal'), 'money'), FF('Budget left', '%s-%s' % (LK('events', 'event_id', 'budget_cost'), LK('events', 'event_id', 'actual_cost')), 'money')]),
    FORM('ticket_sale_sheet', 'Ticket Sale Sheet', 'One ticket sale', 'event_tickets.ticket_id', F(
        ('Buyer', 'event_tickets.buyer'), ('Event', 'event_tickets.event'), ('Sold on', 'event_tickets.sold_on'), ('Ticket type', 'event_tickets.ticket_type'), ('Quantity', 'event_tickets.quantity'), ('Price each', 'event_tickets.price_each'), ('Benefit value each', 'event_tickets.benefit_each'),
        ('Seats', 'event_tickets.seats'), ('Amount', 'event_tickets.amount'), ('Gift part', 'event_tickets.gift_part')) + [
        FF('Gift share of the price', 'IFERROR(%s/%s,0)' % (LK('event_tickets', 'ticket_id', 'gift_part'), LK('event_tickets', 'ticket_id', 'amount')), 'pct'), FF('Money per seat', 'IFERROR(%s/%s,0)' % (LK('event_tickets', 'ticket_id', 'amount'), LK('event_tickets', 'ticket_id', 'seats')), 'money'),
        FF('Names needed by', 'N(%s)' % LK('event_tickets', 'ticket_id', 'names_by'), 'date')]),
    FORM('table_booking_sheet', 'Table Booking Sheet', 'Table booking and guest names', 'event_tickets.ticket_id', F(
        ('Table host', 'event_tickets.buyer'), ('Event', 'event_tickets.event'), ('Event date', 'event_tickets.event_date'), ('Venue', 'event_tickets.venue'), ('Doors open', 'event_tickets.doors'), ('Seats', 'event_tickets.seats'), ('Amount', 'event_tickets.amount'), ('Names needed by', 'event_tickets.names_by')) + [
        FF('Names to collect', LK('event_tickets', 'ticket_id', 'seats'), 'int'), FF('Seats left at the event', 'N(%s)' % LK('event_tickets', 'ticket_id', 'seats_left'), 'int'),
        FF('Days to send the names', 'N(%s)-{today}' % LK('event_tickets', 'ticket_id', 'names_by'), 'int')]),
    FORM('sponsor_sheet', 'Sponsor Sheet', 'One sponsor and the money promised', 'sponsors.sponsor_id', F(
        ('Sponsor', 'sponsors.sponsor'), ('Contact', 'sponsors.contact'), ('Event', 'sponsors.event'), ('Level', 'sponsors.level'), ('Promised', 'sponsors.promised'), ('Received', 'sponsors.received'), ('Not yet paid', 'sponsors.unpaid'), ('Status', 'sponsors.status'), ('Payment due', 'sponsors.due_date')) + [
        FF('Share paid', 'IFERROR(%s/%s,0)' % (LK('sponsors', 'sponsor_id', 'received'), LK('sponsors', 'sponsor_id', 'promised')), 'pct'), FF('Days to the payment due date', 'N(%s)-{today}' % LK('sponsors', 'sponsor_id', 'due_date'), 'int'),
        FF('Share of the event money', 'IFERROR(%s/%s,0)' % (LK('sponsors', 'sponsor_id', 'promised'), LK('sponsors', 'sponsor_id', 'event_raised')), 'pct')]),
    FORM('sponsor_benefit_sheet', 'Sponsor Benefit Sheet', 'Benefits owed to a sponsor', 'benefit_tracker.sponsor_id', F(
        ('Sponsor', 'benefit_tracker.sponsor'), ('Event', 'benefit_tracker.event'), ('Level', 'benefit_tracker.level'), ('Event date', 'benefit_tracker.event_date'), ('Benefits owed', 'benefit_tracker.owed'), ('Delivered', 'benefit_tracker.delivered'),
        ('Left to deliver', 'benefit_tracker.left'), ('Deliver by', 'benefit_tracker.due_date'), ('Status', 'benefit_tracker.flag')) + [
        FF('Cost of the benefits left', '%s*{set:benefit_cost}' % LK('benefit_tracker', 'sponsor_id', 'left'), 'money'), FF('Share delivered', 'IFERROR(%s/%s,0)' % (LK('benefit_tracker', 'sponsor_id', 'delivered'), LK('benefit_tracker', 'sponsor_id', 'owed')), 'pct'),
        FF('Days to deliver', '%s' % LK('benefit_tracker', 'sponsor_id', 'days_to_due'), 'int')]),
    FORM('auction_item_sheet', 'Auction Item Sheet', 'One auction or raffle item', 'auction_items.item_id', F(
        ('Item', 'auction_items.item'), ('Event', 'auction_items.event'), ('Donated by', 'auction_items.donated_by'), ('Fair value', 'auction_items.fair_value'), ('Starting bid', 'auction_items.starting_bid'), ('Sold price', 'auction_items.sold_price'),
        ('Buyer', 'auction_items.buyer'), ('Status', 'auction_items.status'), ('Check', 'auction_items.check')) + [
        FF('Starting bid as a share of value', 'IFERROR(%s/%s,0)' % (LK('auction_items', 'item_id', 'starting_bid'), LK('auction_items', 'item_id', 'fair_value')), 'pct'),
        FF('Sold price as a share of value', 'IFERROR(%s/%s,0)' % (LK('auction_items', 'item_id', 'sold_price'), LK('auction_items', 'item_id', 'fair_value')), 'pct'),
        FF('Donor sends the item by', 'N(%s)' % LK('auction_items', 'item_id', 'send_by'), 'date'), FF('Buyer pays by', 'N(%s)' % LK('auction_items', 'item_id', 'pay_by'), 'date')]),
    FORM('night_gift_sheet', 'Donation on the Night Sheet', 'A gift at an event or in an appeal', 'event_gifts.gift_id', F(
        ('Donor', 'event_gifts.donor'), ('Date', 'event_gifts.date'), ('Amount', 'event_gifts.amount'), ('Campaign', 'event_gifts.campaign'), ('Appeal', 'event_gifts.appeal'), ('Gift type', 'event_gifts.gift_type'),
        ('Campaign raised', 'event_gifts.camp_raised'), ('Campaign goal', 'event_gifts.camp_goal'), ('Days left in the campaign', 'event_gifts.days_left')) + [
        FF('Share of the campaign goal', 'IFERROR(%s/%s,0)' % (LK('event_gifts', 'gift_id', 'amount'), LK('event_gifts', 'gift_id', 'camp_goal')), 'pct'),
        FF('First gift in this campaign, 1 for yes', 'N(%s)' % LK('event_gifts', 'gift_id', 'first_here'), 'int'),
        FF('Gifts from this donor in the list', 'COUNTIFS({range:event_gifts.donor_id},%s)' % LK('event_gifts', 'gift_id', 'donor_id'), 'int')]),
    FORM('event_cost_sheet', 'Event Cost Sheet', 'One event cost', 'event_costs.expense_id', F(
        ('Date', 'event_costs.date'), ('Event', 'event_costs.event'), ('Category', 'event_costs.category'), ('Vendor', 'event_costs.vendor'), ('Amount', 'event_costs.amount'), ('Budget of the event', 'event_costs.budget'), ('Share of the budget', 'event_costs.share_of_budget')) + [
        FF('Budget left after this cost', '%s-%s' % (LK('event_costs', 'expense_id', 'budget'), LK('event_costs', 'expense_id', 'amount')), 'money'),
        FF('Costs of this event in the list', 'SUMIFS({range:event_costs.amount},{range:event_costs.event},%s)' % LK('event_costs', 'expense_id', 'event'), 'money'),
        FF('Costs in this category for the event', 'SUMIFS({range:event_costs.amount},{range:event_costs.event},%s,{range:event_costs.category},%s)' % (LK('event_costs', 'expense_id', 'event'), LK('event_costs', 'expense_id', 'category')), 'money')]),
    FORM('event_debrief_sheet', 'Event Debrief Sheet', 'What the event raised, cost and taught us', 'event_result.event', F(
        ('Ticket money', 'event_result.tickets'), ('Sponsor money', 'event_result.sponsors'), ('Auction income', 'event_result.auction'), ('Gifts', 'event_result.gifts'), ('Total raised', 'event_result.raised'), ('Costs', 'event_result.costs'), ('Net raised', 'event_result.net'),
        ('Cost per dollar', 'event_result.cost_per_dollar'), ('Guests', 'event_result.guests'), ('Net per guest', 'event_result.net_per_guest'), ('Last year net per guest', 'event_result.last_npg'), ('Verdict', 'event_result.verdict')) + [
        FF('Cost per dollar, your setting', '{set:cost_per_dollar}', 'num'), FF('Staff hours', 'N(%s)' % LK('event_result', 'event', 'staff_hours'), 'hours'), FF('Volunteer hours', 'N(%s)' % LK('event_result', 'event', 'volunteer_hours'), 'hours'),
        FF('Value of volunteer hours, your setting', 'N(%s)*{set:volunteer_hour_value}' % LK('event_result', 'event', 'volunteer_hours'), 'money')]),
    FORM('campaign_goal_sheet', 'Campaign Goal Sheet', 'Goal and progress of a campaign', 'campaign_progress.campaign_id', F(
        ('Campaign', 'campaign_progress.campaign'), ('Year', 'campaign_progress.year'), ('Start', 'campaign_progress.start_date'), ('End', 'campaign_progress.end_date'), ('Goal', 'campaign_progress.goal'), ('Raised', 'campaign_progress.raised'), ('Pledged, not yet paid', 'campaign_progress.pledged'),
        ('Share of the goal', 'campaign_progress.share'), ('Days left', 'campaign_progress.days_left'), ('Status', 'campaign_progress.status')) + [
        FF('Pace needed a week', 'N(%s)' % LK('campaign_progress', 'campaign_id', 'pace_needed'), 'money'), FF('Pace now a week', 'N(%s)' % LK('campaign_progress', 'campaign_id', 'recent_pace'), 'money'),
        FF('Forecast to finish', 'N(%s)' % LK('campaign_progress', 'campaign_id', 'forecast'), 'money'), FF('Still to raise', 'MAX(0,%s-%s)' % (LK('campaign_progress', 'campaign_id', 'goal'), LK('campaign_progress', 'campaign_id', 'raised')), 'money')]),
    FORM('go_no_go_sheet', 'Go or No-go Sheet', 'Go or no-go test before booking an event', 'events.event_id', F(
        ('Event', 'events.event'), ('Date', 'events.date'), ('Guests expected', 'events.expected'), ('Money goal', 'events.goal'), ('Budget cost', 'events.budget_cost'), ('Ticket money per seat', 'events.price_seat'), ('Break-even tickets', 'events.break_even_tickets'), ('Verdict', 'events.go_verdict')) + [
        FF('Cost per dollar if the goal is met', 'IFERROR(%s/%s,0)' % (LK('events', 'event_id', 'budget_cost'), LK('events', 'event_id', 'goal')), 'num'), FF('Cost per dollar, your setting', '{set:cost_per_dollar}', 'num'),
        FF('Budget cost allowed at your setting', '%s*{set:cost_per_dollar}' % LK('events', 'event_id', 'goal'), 'money'), FF('Cost to cut to reach the setting', 'MAX(0,%s-%s*{set:cost_per_dollar})' % (LK('events', 'event_id', 'budget_cost'), LK('events', 'event_id', 'goal')), 'money')]),
]
assert len(forms) == 12

# ------------------------------------------------------------------ documents (12)
documents = [
    DOC('event_result_doc', 'Event Budget and Result', 'Budget and result of an event', 'event_result.event', [
        'Event result of {set:org}, dated {today}. Event: {col:event_result.event}. Date: {col:event_result.date}. Status: {col:event_result.status}.',
        'Ticket money: {col:event_result.tickets}. Sponsor money received: {col:event_result.sponsors}. Auction income: {col:event_result.auction}. Gifts: {col:event_result.gifts}. Total raised: {col:event_result.raised}.',
        'Costs: {col:event_result.costs} against a budget of {col:event_result.budget_cost}. Net raised: {col:event_result.net}. Cost to raise one dollar: {col:event_result.cost_per_dollar}. Your setting: {set:cost_per_dollar}.',
        'Guests: {col:event_result.guests}. Net per guest: {col:event_result.net_per_guest}. Last year, same kind of event: {col:event_result.last_npg}. Verdict: {col:event_result.verdict}.'], ['Development manager', 'Executive director'], NOTE),
    DOC('debrief_doc', 'Event Debrief Report', 'Debrief report for the board', 'event_result.event', [
        'Debrief report of {set:org}, dated {today}. Event: {col:event_result.event}.',
        'We raised {col:event_result.raised} and spent {col:event_result.costs}, so the net is {col:event_result.net}. Cost to raise one dollar was {col:event_result.cost_per_dollar} against our setting of {set:cost_per_dollar}.',
        'Net per guest was {col:event_result.net_per_guest} against {col:event_result.last_npg} for the same kind of event a year earlier. Change in net: {col:event_result.net_vs_last}.',
        'Staff hours: {col:event_result.staff_hours}. Volunteer hours: {col:event_result.volunteer_hours}. Verdict: {col:event_result.verdict}. What to keep, change and drop next year is written below.'], ['Development manager', 'Board chair'], NOTE),
    DOC('package_doc', 'Sponsorship Package', 'Sponsorship level, price and benefits', 'sponsor_levels.level', [
        'Sponsorship package of {set:org}, dated {today}. Level: {col:sponsor_levels.level}. Kind of event: {col:sponsor_levels.kind}.',
        'Price: {col:sponsor_levels.price}. Benefits in the package: {col:sponsor_levels.benefits_count}. Sponsors at this level so far: {col:sponsor_levels.sold}.',
        'Benefits are delivered within {set:benefit_days} days of the event. Payment is due {set:pay_days_before} days before the event.',
        'Thank you for considering a partnership with us. Please call us to talk about the level that suits you.'], ['Development manager', 'Sponsor'], NOTE),
    DOC('sponsor_thanks_doc', 'Sponsor Thank-you Letter', 'Thank-you letter to a sponsor', 'sponsors.sponsor_id', [
        'Dear {col:sponsors.contact}, dated {today}.',
        'Thank you to {col:sponsors.sponsor} for supporting {col:sponsors.event} at the {col:sponsors.level} level. Your support of {col:sponsors.promised} helps us do our work.',
        'Benefits owed to you: {col:sponsors.benefits_owed}. Delivered so far: {col:sponsors.benefits_delivered}. We will deliver the rest within {set:benefit_days} days of the event.',
        'We are grateful for your partnership. With thanks from everyone at {set:org}.'], ['Development manager', 'Sponsor'], NOTE),
    DOC('renewal_doc', 'Sponsor Renewal Letter', 'Renewal letter to a sponsor', 'sponsor_renewal.sponsor_id', [
        'Dear partner at {col:sponsor_renewal.sponsor}, dated {today}.',
        'Thank you for supporting {col:sponsor_renewal.event} at the {col:sponsor_renewal.level} level with {col:sponsor_renewal.last_amount}. We would like to talk about next year.',
        'We would be glad to visit you on or near {col:sponsor_renewal.next_step_date}, show you what your support achieved and agree a renewal that suits you.',
        'Please reply to this letter or call us. With thanks from {set:org}.'], ['Development manager', 'Sponsor'], NOTE),
    DOC('ticket_confirm_doc', 'Ticket Order Confirmation', 'Confirmation of a ticket order', 'event_tickets.ticket_id', [
        'Ticket confirmation of {set:org}, dated {today}. Order {col:event_tickets.ticket_id} for {col:event_tickets.buyer}.',
        'Event: {col:event_tickets.event} on {col:event_tickets.event_date} at {col:event_tickets.venue}. Doors open at {col:event_tickets.doors}.',
        'Ticket type: {col:event_tickets.ticket_type}. Quantity: {col:event_tickets.quantity}. Price each: {col:event_tickets.price_each}. Amount paid: {col:event_tickets.amount}.',
        'Part of your ticket, {col:event_tickets.gift_part}, is a gift to us; the rest pays for what you receive on the night. Keep this page as your record.'], ['Development manager', 'Guest'], NOTE),
    DOC('table_host_doc', 'Table Host Letter', 'Letter to the host of a table', 'event_tickets.ticket_id', [
        'Dear {col:event_tickets.buyer}, dated {today}. Thank you for hosting a table at {col:event_tickets.event}.',
        'Your table has {col:event_tickets.seats} seats. The event is on {col:event_tickets.event_date} at {col:event_tickets.venue}, doors open at {col:event_tickets.doors}.',
        'Please send us the names of your guests and any dietary needs by {col:event_tickets.names_by}.',
        'We look forward to welcoming you. With thanks from {set:org}.'], ['Development manager', 'Table host'], NOTE),
    DOC('auction_donor_doc', 'Auction Item Donor Letter', 'Letter to a donor of an auction item', 'auction_items.item_id', [
        'Dear {col:auction_items.donated_by}, dated {today}.',
        'Thank you for donating {col:auction_items.item} to {col:auction_items.event}. We have recorded a fair value of {col:auction_items.fair_value}.',
        'Please send the item to us by {col:auction_items.send_by}. The event is on {col:auction_items.event_date}.',
        'Keep this letter for your records. Please confirm with your own adviser what you may record. With thanks from {set:org}.'], ['Development manager', 'Donor'], NOTE),
    DOC('auction_catalog_doc', 'Auction Catalog Page', 'Catalog page for an auction item', 'auction_items.item_id', [
        'Auction catalog of {set:org}. Item {col:auction_items.item_id}: {col:auction_items.item}.',
        'Donated by {col:auction_items.donated_by}. Fair value: {col:auction_items.fair_value}. Starting bid: {col:auction_items.starting_bid}.',
        'Event: {col:auction_items.event} on {col:auction_items.event_date}. Status: {col:auction_items.status}.',
        'All money raised goes to our work. Thank you for bidding.'], ['Development manager', 'Guest'], NOTE),
    DOC('campaign_page_doc', 'Campaign Progress Page', 'Goal, money raised and days left', 'campaign_progress.campaign_id', [
        'Campaign progress of {set:org}, dated {today}. Campaign: {col:campaign_progress.campaign}, {col:campaign_progress.year}.',
        'Goal: {col:campaign_progress.goal}. Raised: {col:campaign_progress.raised}. Pledged, not yet paid: {col:campaign_progress.pledged}. Share of the goal: {col:campaign_progress.share}.',
        'Days left: {col:campaign_progress.days_left}. Pace needed a week: {col:campaign_progress.pace_needed}. Pace now a week: {col:campaign_progress.recent_pace}.',
        'Forecast to finish: {col:campaign_progress.forecast}. Status: {col:campaign_progress.status}.'], ['Development manager', 'Executive director'], NOTE),
    DOC('campaign_case_doc', 'Campaign Case Summary', 'Case summary of a campaign', 'campaign_progress.campaign_id', [
        'Campaign case of {set:org}, dated {today}. Campaign: {col:campaign_progress.campaign}, {col:campaign_progress.year}, from {col:campaign_progress.start_date} to {col:campaign_progress.end_date}.',
        'We ask our community to help us reach {col:campaign_progress.goal}. So far {col:campaign_progress.raised} has been raised, which is {col:campaign_progress.share} of the goal.',
        'Every gift helps. With {col:campaign_progress.days_left} days left we need about {col:campaign_progress.pace_needed} a week.',
        'Thank you to everyone who has given. Please give or share this page.'], ['Development manager', 'Executive director'], NOTE),
    DOC('three_year_doc', 'Campaign Year Comparison', 'One campaign compared with the year before', 'campaign_compare.campaign_id', [
        'Campaign comparison of {set:org}, dated {today}. Campaign: {col:campaign_compare.campaign}, {col:campaign_compare.year}.',
        'Goal: {col:campaign_compare.goal}. Raised in all: {col:campaign_compare.raised}. Cost: {col:campaign_compare.cost}. Cost to raise one dollar: {col:campaign_compare.cost_per_dollar}.',
        'Donors: {col:campaign_compare.donors}, of them new: {col:campaign_compare.new_donors}. Raised the year before: {col:campaign_compare.prev_raised}. Change: {col:campaign_compare.change}.',
        'Verdict: {col:campaign_compare.verdict}. Your setting for cost to raise one dollar: {set:cost_per_dollar}.'], ['Development manager', 'Board chair'], NOTE),
]
assert len(documents) == 12

# ------------------------------------------------------------------ checklists (12)
checklists = [
    CHK('go_no_go_chk', 'Event Go or No-go Steps', 'events', 'events.date', [('Type low, expected and high guests in the Go or No-go tool', -150), ('Check the cost per dollar against your setting', -145), ('Check the break-even guests', -140), ('Ask the board chair to agree the date', -135), ('Book the venue', -130), ('Write the decision down', -128)]),
    CHK('six_weeks_chk', 'Event Six Weeks Out Steps', 'events', 'events.date', [('Open ticket sales', -45), ('Send sponsor invitations', -45), ('Ask for auction items', -42), ('Confirm the caterer menu', -35), ('Send programs to print', -28), ('Recruit volunteers for each work area', -28), ('Check the budget lines', -21)]),
    CHK('event_week_chk', 'Event Week Steps', 'events', 'events.date', [('Send the final guest count to the venue and caterer', -7), ('Collect guest names for every table', -7), ('Confirm every volunteer shift', -5), ('Print the guest list and the auction sheets', -3), ('Test the sound and the payment tools', -1), ('Send a reminder to every guest', -1)]),
    CHK('event_day_chk', 'Event Day Steps', 'events', 'events.date', [('Set up the room and decor', 0), ('Brief the volunteers', 0), ('Open the check-in desk', 0), ('Record gifts on the night', 0), ('Close the auction and take payment', 0), ('Count the money with two people', 0), ('Clear up and return borrowed items', 0)]),
    CHK('after_event_chk', 'After the Event Steps', 'events', 'events.date', [('Send thank-you messages to every guest', 1), ('Record every gift and auction payment', 3), ('Chase unpaid sponsors and auction buyers', 7), ('Enter every cost in Event Costs', 10), ('Send photos and numbers to sponsors', 14), ('Fill the Event Debrief Sheet', 21), ('Present the result to the board', 30)]),
    CHK('benefit_delivery_chk', 'Sponsor Benefits Delivery Steps', 'sponsors', 'sponsors.promised_on', [('List the benefits owed in the Sponsor Benefit Sheet', 7), ('Deliver the benefits that come before the event', 30), ('Deliver the benefits that come at the event', 60), ('Send photos and numbers after the event', 90), ('Mark every benefit delivered', 100)]),
    CHK('sponsor_renewal_chk', 'Sponsor Renewal Steps', 'sponsors', 'sponsors.next_step_date', [('Check the renewal list for the sponsor', -14), ('Book a visit or a call', -7), ('Send the renewal letter', -3), ('Hold the visit', 0), ('Write the answer in Sponsors', 3), ('Send a thank-you', 7)]),
    CHK('auction_collect_chk', 'Auction Items Collection Steps', 'auction_items', 'auction_items.received_on', [('Record the item and its fair value', 0), ('Send the donor letter', 1), ('Photograph the item', 3), ('Write the catalog page', 7), ('Set the starting bid', 10), ('Store the item safely', 14)]),
    CHK('campaign_launch_chk', 'Campaign Launch Steps', 'campaigns', 'campaigns.start_date', [('Set the goal and the dates', -28), ('Write the case summary', -21), ('Make a list of donors to ask', -14), ('Send the launch messages', -1), ('Record the first gifts', 0), ('Check the thermometer after one week', 7)]),
    CHK('campaign_weekly_chk', 'Campaign Weekly Check Steps', 'campaigns', 'campaigns.start_date', [('Record every gift of the week', 7), ('Check the pace needed and the pace now', 7), ('Thank new donors', 8), ('Send a progress message', 9), ('Write what to change next week', 9)]),
    CHK('campaign_close_chk', 'Campaign Close Steps', 'campaigns', 'campaigns.end_date', [('Send the last reminder', -3), ('Record every gift and pledge', 1), ('Send thank-you messages', 2), ('Chase pledges not yet paid', 14), ('Fill the three-year comparison', 21), ('Tell donors what was achieved', 30)]),
    CHK('first_event_chk', 'First Small Event Steps', 'events', 'events.date', [('Choose a simple event kind and a date', -90), ('Set a small budget and goal', -85), ('Ask five people to help', -80), ('Ask three sponsors', -70), ('Sell tickets by message', -45), ('Hold the event', 0), ('Thank everyone and count the result', 7)]),
]
assert len(checklists) == 12

# ------------------------------------------------------------------ messages (34)
def M(k, moment, table, phone, text): return MSG(k, moment, table, phone, text)
DM = 'Hello, '
messages = [
    M('g_thanks', 'Guest: thank you for buying tickets', 'event_tickets', 'event_tickets.phone', 'Hello {buyer}, thank you for buying {quantity} tickets to {event}. {org}'),
    M('g_date', 'Guest: date, venue and doors', 'event_tickets', 'event_tickets.phone', 'Hello {buyer}, {event} is on {event_date} at {venue}. Doors open at {doors}. {org}'),
    M('g_remind', 'Guest: tickets are still available', 'event_tickets', 'event_tickets.phone', 'Hello {buyer}, tickets are still available for {event} on {event_date}, {seats_left} seats left. Please share. {org}'),
    M('g_came', 'Guest: thank you for coming', 'event_tickets', 'event_tickets.phone', 'Hello {buyer}, thank you for coming to {event}. Your ticket order of {amount} helped us. {org}'),
    M('g_gift', 'Guest: part of your ticket is a gift', 'event_tickets', 'event_tickets.phone', 'Hello {buyer}, part of your ticket for {event}, {gift_part}, is a gift. Thank you. {org}'),
    M('t_host', 'Table host: names needed', 'event_tickets', 'event_tickets.phone', 'Hello {buyer}, your table for {event} has {seats} seats. Please send the names by {names_by}. {org}'),
    M('s_thanks', 'Sponsor: thank you for supporting', 'sponsors', 'sponsors.phone', 'Hello {contact}, thank you for supporting {event} at {level}, {promised}. {org}'),
    M('s_due', 'Sponsor: your payment is due', 'sponsors', 'sponsors.phone', 'Hello {contact}, your payment of {unpaid} for {event} is due on {due_date}. {org}'),
    M('s_benefits', 'Sponsor: benefits delivered so far', 'sponsors', 'sponsors.phone', 'Hello {contact}, benefits delivered so far for {event} are {benefits_delivered} of {benefits_owed}. {org}'),
    M('s_photos', 'Sponsor: photos and numbers', 'sponsors', 'sponsors.phone', 'Hello {contact}, here are the photos and numbers from {event}. Together we raised {event_raised}. {org}'),
    M('s_renew', 'Sponsor: would you renew', 'sponsors', 'sponsors.phone', 'Hello {contact}, would you renew at {level} for next year after {event}? {org}'),
    M('s_visit', 'Sponsor: a visit about next year', 'sponsors', 'sponsors.phone', 'Hello {contact}, may we visit on {next_step_date} to talk about next year? {org}'),
    M('a_thanks', 'Auction donor: thank you', 'auction_items', 'auction_items.donor_phone', 'Hello {donated_by}, thank you for donating {item}, valued at {fair_value}. {org}'),
    M('a_send', 'Auction donor: please send the item', 'auction_items', 'auction_items.donor_phone', 'Hello {donated_by}, please send {item} by {send_by}. {org}'),
    M('a_won', 'Auction buyer: you won', 'auction_items', 'auction_items.buyer_phone', 'Hello {buyer}, congratulations, you won {item} for {sold_price}. {org}'),
    M('a_pay', 'Auction buyer: please pay', 'auction_items', 'auction_items.buyer_phone', 'Hello {buyer}, please pay {sold_price} for {item} by {pay_by}. {org}'),
    M('d_raised', 'Donor: how far the campaign is', 'event_gifts', 'event_gifts.phone', 'Hello {donor}, {campaign} has raised {camp_raised} of {camp_goal}, {days_left} days left. {org}'),
    M('d_reach', 'Donor: help us reach the goal', 'event_gifts', 'event_gifts.phone', 'Hello {donor}, help us reach {camp_goal} for {campaign} by {end_date}. {org}'),
    M('d_match', 'Donor: a matching offer', 'event_gifts', 'event_gifts.phone', 'Hello {donor}, a matching offer applies to {campaign} until {end_date}. Your gift could do twice as much. {org}'),
    M('d_goal', 'Donor: we reached the goal', 'event_gifts', 'event_gifts.phone', 'Hello {donor}, thank you, we reached {camp_goal} for {campaign}. {org}'),
    M('dm_cost', 'Manager: costs against budget', 'events', 'events.director_phone', 'Costs of {event} are {actual_cost} against {budget_cost}. {org}'),
    M('dm_cpd', 'Manager: cost per dollar', 'events', 'events.director_phone', 'Cost per dollar for {event} is {cost_per_dollar}. {org}'),
    M('dm_benefits', 'Manager: benefits due this month', 'benefit_tracker', 'benefit_tracker.director_phone', '{due_n} sponsor benefits are due this month. See the Benefit Tracker. {org}'),
    M('dm_renew', 'Manager: renewal calls', 'sponsor_renewal', 'sponsor_renewal.director_phone', '{call_n} sponsors are due for a renewal call. First on the list: {sponsor}. {org}'),
    M('ed_gonogo', 'Executive director: go or no-go', 'events', 'events.exec_phone', 'The go or no-go for {event} says {go_verdict}. {org}'),
    M('ed_camp', 'Executive director: campaign progress', 'campaign_progress', 'campaign_progress.exec_phone', '{campaign} is {share} of the way with {days_left} days left. {org}'),
    M('bm_result', 'Board member: event result ready', 'event_result', 'event_result.chair_phone', 'The event result for {event} is ready, net {net}. {org}'),
    M('fc_break', 'Fundraising committee: break-even', 'events', 'events.chair_phone', 'The break-even for {event} is {break_even_tickets} tickets. {org}'),
    M('v_confirm', 'Venue contact: confirm date and guests', 'events', 'events.venue_phone', 'Please confirm {date} for {event} and the number of guests, {seats_sold}. {org}'),
    M('c_final', 'Caterer: final number', 'events', 'events.caterer_phone', 'The final number for {event} is {seats_sold}. Dietary counts are attached. {org}'),
    M('p_programs', 'Printer: programs needed', 'events', 'events.printer_phone', '{seats_sold} programs for {event} are needed by {program_by}. {org}'),
    M('vol_help', 'Volunteer: please help', 'event_hours', 'event_hours.lead_phone', 'Hello {lead}, please help at {event} on {work_date}, {area}. {org}'),
    M('vc_needed', 'Volunteer coordinator: volunteers needed', 'event_hours', 'event_hours.coordinator_phone', '{still_needed} volunteers are still needed for {event} in {area}. {org}'),
    M('bk_code', 'Bookkeeper: code event costs', 'event_costs', 'event_costs.bookkeeper_phone', 'Please code {amount} of event costs to {event}, {category}. {org}'),
]
assert len(messages) == 34, len(messages)

# ------------------------------------------------------------------ KPIs (30)
def NX(c): return 'IFERROR(INDEX(%s,MATCH(MIN(%s),%s,0)),0)' % (R('events', c), R('events', 'upcoming'), R('events', 'upcoming'))
LASTD = 'SUMPRODUCT(MAX((%s=%s)*%s))' % (R('events', 'status'), DONE, R('events', 'date'))
def LE(c): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('event_result', c), LASTD, R('event_result', 'date'))
def MC(c): return 'IFERROR(INDEX(%s,MATCH(%s,%s,0)),0)' % (R('campaign_progress', c), YES, R('campaign_progress', 'main'))
YS = 'DATE(YEAR({today}),1,1)'
kpis = [
    KPI('Events this year', 'COUNTIFS(%s,YEAR({today}))' % R('events', 'year'), 'int'),
    KPI('Next event date', 'IF(COUNT(%s)=0,"",MIN(%s))' % (R('events', 'upcoming'), R('events', 'upcoming')), 'date'),
    KPI('Tickets sold for the next event', NX('seats_sold'), 'int'),
    KPI('Seats left for the next event', NX('seats_left'), 'int'),
    KPI('Ticket money for the next event', NX('ticket_money'), 'money'),
    KPI('Sponsor money promised, next event', NX('sponsor_promised'), 'money'),
    KPI('Sponsor money received this year', 'SUMIFS(%s,%s,">="&%s)' % (R('sponsors', 'received'), R('sponsors', 'received_on'), YS), 'money'),
    KPI('Auction income this year', 'SUMIFS(%s,%s,%s,%s,">="&%s,%s,"<="&{today})' % (R('auction_items', 'sold_price'), R('auction_items', 'status'), SOLD, R('auction_items', 'event_date'), YS, R('auction_items', 'event_date')), 'money'),
    KPI('Net raised at the last event', LE('net'), 'money'),
    KPI('Cost per dollar at the last event', LE('cost_per_dollar'), 'num'),
    KPI('Net per attendee at the last event', LE('net_per_guest'), 'money'),
    KPI('Last event against last year', LE('net_vs_last'), 'pct'),
    KPI('Events above the cost setting', 'COUNTIFS(%s,">"&{set:cost_per_dollar},%s,%s)' % (R('event_result', 'cost_per_dollar'), R('event_result', 'status'), DONE), 'int'),
    KPI('Event costs over budget now', 'SUM(%s)' % R('events', 'cost_over'), 'money'),
    KPI('Sponsor money promised, not paid', 'SUMIFS(%s,%s,"<>"&%s)' % (R('sponsors', 'unpaid'), R('sponsors', 'status'), DECL), 'money'),
    KPI('Sponsor benefits owed, not delivered', 'SUM(%s)' % R('benefit_tracker', 'left'), 'int'),
    KPI('Sponsors up for renewal', 'COUNTIFS(%s,">0")' % R('sponsor_renewal', 'score'), 'int'),
    KPI('Renewal money at stake', 'SUMIFS(%s,%s,">0")' % (R('sponsor_renewal', 'last_amount'), R('sponsor_renewal', 'score')), 'money'),
    KPI('Auction items unsold', 'COUNTIFS(%s,%s)' % (R('auction_items', 'status'), UNSOLD), 'int'),
    KPI('Auction items missing a fair value', 'SUMPRODUCT((%s<>"")*(%s=0))' % (R('auction_items', 'item'), R('auction_items', 'fair_value')), 'int'),
    KPI('Campaigns running now', 'COUNTIFS(%s,%s)' % (R('campaigns', 'state'), ca('Running')), 'int'),
    KPI('Next campaign end date', 'IF(COUNTIFS(%s,"<"&{today})=COUNT(%s),"",SMALL(%s,COUNTIFS(%s,"<"&{today})+1))' % (R('campaigns', 'end_date'), R('campaigns', 'end_date'), R('campaigns', 'end_date'), R('campaigns', 'end_date')), 'date'),
    KPI('Raised in the main campaign', MC('raised'), 'money'),
    KPI('Share of the main campaign goal', MC('share'), 'pct'),
    KPI('Days left in the main campaign', MC('days_left'), 'int'),
    KPI('Pace needed a week, main campaign', 'N(%s)' % MC('pace_needed'), 'money'),
    KPI('Forecast to finish the main campaign', MC('forecast'), 'money'),
    KPI('Pledged not yet paid in campaigns', 'SUM(%s)' % R('campaigns', 'pledged_open'), 'money'),
    KPI('Cheapest method by cost per dollar', 'IFERROR(INDEX(%s,MATCH(1,%s,0)),"")' % (R('method_rank', 'campaign'), R('method_rank', 'rank')), 'text'),
    KPI('Dearest method by cost per dollar', 'IFERROR(INDEX(%s,MATCH(MAX(%s),%s,0)),"")' % (R('method_rank', 'campaign'), R('method_rank', 'rank'), R('method_rank', 'rank')), 'text'),
]
assert len(kpis) == 30
dashboard = {"title": "Events and Campaigns Dashboard", "kpis": kpis,
    "monthly": {"title": "Event gifts, ticket money, sponsor money and costs", "date": "event_gifts.month", "series": [
        {"label": "Event gifts", "sum": "event_gifts.amount", "date": "event_gifts.month"}, {"label": "Ticket money", "sum": "event_tickets.amount", "date": "event_tickets.month"},
        {"label": "Sponsor money received", "sum": "sponsors.received", "date": "sponsors.received_on"}, {"label": "Event costs", "sum": "event_costs.amount", "date": "event_costs.date"}]},
    "breakdowns": [{"title": "Gifts by gift type", "by": "event_gifts.gift_type", "value": "event_gifts.amount", "agg": "sum"},
                   {"title": "Volunteer hours by work area", "by": "event_hours.area", "value": "event_hours.volunteer_hours", "agg": "sum"},
                   {"title": "Sponsors by next step", "by": "sponsors.next_step", "value": "sponsors.promised", "agg": "count"}]}
YR = D.T0.year
insights = {
    "gauges": [
        {"title": "Seats sold against seats expected", "num": AGG('sum', 'events', 'events.seats_sold', where=[('status', '=', PLANNED)]), "den": AGG('sum', 'events', 'events.expected', where=[('status', '=', PLANNED)])},
        {"title": "Sponsor money received against promised", "num": AGG('sum', 'sponsors', 'sponsors.received'), "den": AGG('sum', 'sponsors', 'sponsors.promised')},
        {"title": "Sponsor benefits delivered", "num": AGG('sum', 'benefit_tracker', 'benefit_tracker.delivered'), "den": AGG('sum', 'benefit_tracker', 'benefit_tracker.owed')},
        {"title": "Cost share of money raised, done events", "num": AGG('sum', 'event_result', 'event_result.costs', where=[('status', '=', DONE)]), "den": AGG('sum', 'event_result', 'event_result.raised', where=[('status', '=', DONE)])},
        {"title": "Main campaign against goal", "num": AGG('sum', 'campaign_progress', 'campaign_progress.raised', where=[('main', '=', YES)]), "den": AGG('sum', 'campaign_progress', 'campaign_progress.goal', where=[('main', '=', YES)])},
        {"title": "Auction items sold", "num": AGG('count', 'auction_items', where=[('status', '=', SOLD)]), "den": AGG('count', 'auction_items')}],
    "charts": [
        CHART('Event net by event', 'bar', 'event_result.event', [AGG('sum', 'event_result', 'event_result.net', label='Net raised')]),
        CHART('Event money raised by event', 'bar', 'event_result.event', [AGG('sum', 'event_result', 'event_result.raised', label='Raised')]),
        CHART('Event cost by event', 'bar', 'event_result.event', [AGG('sum', 'event_result', 'event_result.costs', label='Costs')]),
        CHART('Cost per dollar by event', 'bar', 'event_result.event', [AGG('avg', 'event_result', 'event_result.cost_per_dollar', label='Cost per dollar')]),
        CHART('Tickets by ticket type', 'bar', 'event_tickets.ticket_type', [AGG('sum', 'event_tickets', 'event_tickets.quantity', label='Tickets')]),
        CHART('Ticket money by ticket type', 'bar', 'event_tickets.ticket_type', [AGG('sum', 'event_tickets', 'event_tickets.amount', label='Ticket money')]),
        CHART('Ticket sales per month', 'column', 'month', [AGG('sum', 'event_tickets', 'event_tickets.amount', date='event_tickets.month', label='Ticket money')]),
        CHART('Sponsor money by level', 'bar', 'sponsors.level', [AGG('sum', 'sponsors', 'sponsors.received', label='Received')]),
        CHART('Sponsor money by event', 'bar', 'sponsors.event', [AGG('sum', 'sponsors', 'sponsors.received', label='Received')]),
        CHART('Sponsors by status', 'bar', 'sponsors.status', [AGG('count', 'sponsors', label='Sponsors')]),
        CHART('Auction fair value received per month', 'column', 'month', [AGG('sum', 'auction_items', 'auction_items.fair_value', date='auction_items.received_on', label='Fair value')]),
        CHART('Auction items by status', 'bar', 'auction_items.status', [AGG('count', 'auction_items', label='Items')]),
        CHART('Event gifts per month', 'column', 'month', [AGG('sum', 'event_gifts', 'event_gifts.amount', date='event_gifts.month', label='Gifts')]),
        CHART('Event costs by category', 'bar', 'event_costs.category', [AGG('sum', 'event_costs', 'event_costs.amount', label='Costs')]),
        CHART('Staff and volunteer hours by event', 'bar', 'event_hours.event', [AGG('sum', 'event_hours', 'event_hours.staff_hours', label='Staff hours'), AGG('sum', 'event_hours', 'event_hours.volunteer_hours', label='Volunteer hours')]),
        CHART('Campaign raised by campaign', 'bar', 'campaign_compare.campaign', [AGG('sum', 'campaign_compare', 'campaign_compare.raised', label='Raised')]),
        CHART('Campaign goal by campaign', 'bar', 'campaign_compare.campaign', [AGG('sum', 'campaign_compare', 'campaign_compare.goal', label='Goal')]),
        CHART('Gifts per month, not at an event', 'column', 'month', [AGG('sum', 'event_gifts', 'event_gifts.amount', date='event_gifts.month', where=[('at_event', '=', 0)], label='Gifts')]),
        CHART('Year-end appeal, cumulative per week', 'line', 'campaign_weeks.week', [AGG('sum', 'campaign_weeks', 'campaign_weeks.cumulative', where=[('campaign', '=', tok('campaign', 'Year-End Appeal')), ('year', '=', YR - 1)], label='Cumulative raised')]),
        CHART('Campaign donors by campaign', 'bar', 'campaign_compare.campaign', [AGG('sum', 'campaign_compare', 'campaign_compare.donors', label='Donors')]),
        CHART('Campaign cost by campaign', 'bar', 'campaign_compare.campaign', [AGG('sum', 'campaign_compare', 'campaign_compare.cost', label='Cost')]),
        CHART('Cost per dollar by campaign', 'bar', 'campaign_compare.campaign', [AGG('avg', 'campaign_compare', 'campaign_compare.cost_per_dollar', label='Cost per dollar')])]}
assert len(insights['charts']) == 22 and len(insights['gauges']) == 6

signature = [
    {"name": "Event result card", "why": "pick an event and see tickets, sponsors, auction, gifts, costs, net and cost per dollar against your own last year, with a what-if on costs", "where": "Event Result Card"},
    {"name": "Event go or no-go", "why": "low, expected and high guests with your sponsor, auction and cost guesses give net, cost per dollar, break-even seats and a verdict before you book", "where": "Event Go or No-go"},
    {"name": "Break-even solver", "why": "the guests, tickets or sponsors that close the gap to the net you want", "where": "Break-even Solver"},
    {"name": "Ticket and benefit split", "why": "the part of each ticket that is a gift, set apart from the value of what the guest receives", "where": "Ticket and Benefit Split"},
    {"name": "Cost line watcher", "why": "each budget line against its actual cost, the biggest overrun named and the line to cut next year", "where": "Event Cost Line Watcher"},
    {"name": "Sponsor renewal ranker", "why": "the open sponsors with the most money to renew, ranked, with who to call this week", "where": "Sponsor Renewal Ranker"},
    {"name": "Sponsor benefit tracker", "why": "benefits owed and delivered by sponsor, with the ones due this month and the ones overdue", "where": "Sponsor Benefit Tracker"},
    {"name": "Campaign thermometer", "why": "goal, raised, days left, pace needed and pace now, with pledges counted or left out", "where": "Campaign Thermometer"},
    {"name": "Campaign finish forecast", "why": "base, best and worst finish from today's pace and last year's own curve", "where": "Campaign Finish Forecast"},
    {"name": "Cheapest method ranker", "why": "campaign types ranked by cost to raise one dollar over three years, with what to do more and less of", "where": "Cheapest Method Ranker"}]
competitors = [
    {"what": "generic event spreadsheets", "lacks": "list tickets and costs but never show cost to raise one dollar, net per guest or the gift part of a ticket"},
    {"what": "subscription fundraising platforms", "lacks": "charge every month and hide the sums, so you cannot test a go or no-go, a break-even or a package price before you decide"},
    {"what": "free event budget templates", "lacks": "stop at a budget and leave out sponsors, auction items, benefits owed and the renewal list"},
    {"what": "single-sheet campaign trackers", "lacks": "show a thermometer but not pledges apart from cash, the pace needed or a forecast to finish"},
    {"what": "paper ledgers and committee notes", "lacks": "keep the numbers but never compare this year with last year or rank the methods by cost"}]
guide = [
    'Open Start and type your organization name, your cost-to-raise-one-dollar setting, the value of a volunteer hour and the number of days for names, payments and benefits.',
    'Replace the demo data: clear the demo rows and type your own events in Events, then your tickets, sponsors, auction items, event gifts, costs and hours in their sheets.',
    'Keep Events up to date: date, venue, budget cost, goal and expected guests. Actual cost, raised money and the go or no-go verdict fill in by themselves.',
    'Record every ticket in Event Tickets and every sponsor in Sponsors with the amount promised, the amount received and the benefits owed and delivered.',
    'Record auction and raffle items with a fair value and a starting bid, and write the sold price and the buyer when the item sells.',
    'Enter every event cost in Event Costs and every gift in Event Gifts. Event Result then shows net raised, cost per dollar and net per guest against last year.',
    'Before booking, use the Event Go or No-go and the Break-even Solver with low, expected and high guests; they show the net and the cost line to cut.',
    'Open Campaigns for the goal and dates, then Campaign Progress and Campaign by Week to see the thermometer, the pace needed and the forecast to finish.',
    'Use the Sponsor Renewal List and the Benefit Tracker every month to see who to call and which benefits are due.',
    f'Use the {len(tools)} calculators for your decisions, print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and tap a message link to send a text with the details already written in.',
    'Read the Events and Campaigns Dashboard and the charts every month. A founder who runs one event a year can start with the Event Go or No-go and the First Small Event checklist.',
    'This is a standard workbook with no macros: it works offline, you own the file, and it keeps all your figures in one place that you can read, check and change. It is not an accounting system or a tax record.']
listing = {"title": "Nonprofit Events and Campaigns Excel Template: Event Budget, Tickets, Sponsors, Auction, Campaign Goal and Forecast",
    "headline": "Know what each event really raised and what each campaign will finish at",
    "tags": ["nonprofit", "fundraising event", "gala budget", "event budget", "sponsor tracker", "auction tracker", "campaign tracker", "fundraising goal", "cost per dollar", "excel template", "charity event", "ticket sales", "break-even"],
    "description": ("Run the event and campaign side of fundraising in one Excel workbook. Built for a development manager, an executive director and a founder with volunteers who hold one or more events a year and run appeals and campaigns around them. "
        "Events holds each event with date, venue, budget cost, goal and expected guests. Event Tickets lists every ticket by type with the benefit value of each ticket set apart, so the gift part of a ticket is shown on its own. Sponsors lists each sponsor with the level, the money promised and received, the benefits owed and delivered and the next step. "
        "Auction Items records fair value, starting bid, sold price and buyer. Event Gifts, Event Costs and Event Hours add the gifts on the night, the direct costs and the staff and volunteer hours.\n\n"
        "Event Result works out raised, costs, net, cost to raise one dollar and net per guest and compares them with your own last year. The Sponsor Renewal List ranks who to call, and the Benefit Tracker shows what is due. Campaigns, Campaign Progress and Campaign by Week show the goal, the thermometer, pledges apart from cash, days left, the pace needed and a forecast to finish. "
        "Campaign Comparison and Method Ranking set three years side by side and rank each way of raising money by what it costs.\n\n"
        f"{len(tools)} calculators include an event result card, a go or no-go test with low, expected and high sales, a break-even solver, a cost line watcher, a sponsor package pricer, a campaign thermometer, a finish forecast and a cheapest method ranker. "
        f"Print {len(forms)} sheets and {len(documents)} documents, follow {len(checklists)} checklists and send {len(messages)} ready text messages to guests, table hosts, sponsors, auction donors, donors, the venue, the caterer and your team.\n\n"
        "This is part four of the Nonprofit Organization suite. A standard .xlsx workbook with no macros and no subscription, with a demo copy full of sample data to explore first. Donors and guests appear by name, contact status, amounts and dates only. It helps you keep track of your own figures and does not promise results. "
        "Check your local rules for gift receipts and benefits, and ask your adviser about tax."),
    "features": ["Event result with cost per dollar and net per guest", "Go or no-go with low, expected and high sales", "Break-even guests, tickets and sponsors", "Gift part of each ticket shown apart", "Sponsor log with benefits owed and delivered",
                 "Sponsor renewal list ranked by money", "Auction items with value and sold price", "Campaign thermometer with pledges apart from cash", "Forecast to finish a campaign", f"{len(tools)} calculators for event and campaign decisions",
                 f"{len(forms)} printable sheets and {len(documents)} documents", f"Dashboard with {len(kpis)} live figures and {len(insights['charts'])} charts", f"{len(messages)} ready text messages"]}
def fixN(f):
    out, i = '', 0
    while i < len(f):
        if f.startswith('N(', i) and (i == 0 or not (f[i-1].isalnum() or f[i-1] in '_.:')):
            j, d, q = i + 2, 1, False
            while j < len(f) and d:
                ch = f[j]
                if ch == '"': q = not q
                elif not q:
                    d += (ch == '(') - (ch == ')')
                j += 1
            out += 'IFERROR((' + fixN(f[i+2:j-1]) + ')*1,0)'; i = j
        else: out += f[i]; i += 1
    return out
def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == 'formula' and isinstance(v, str): o[k] = fixN(v)
            else: walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
for t_ in tables: t_['rows'] = max(t_['rows'], 50)
s = spec(id=f'{SUITE}-p4', slug='nonprofit-events', profession='Nonprofit Organization', name='Events and Campaigns',
         tagline='Know what each event really raised and what each campaign will finish at', price_usd=29,
         colors={"primary": "#22577A", "accent": "#F2A541"}, settings=settings, lists=lists, tables=tables, dashboard=dashboard, forms=forms, guide=guide,
         listing=listing, insights=insights, suite={"key": SUITE, "part": 4, "of": 8, "focus": "Events and campaigns"},
         signature=signature, competitors=competitors, tools=tools, messages=messages, documents=documents, checklists=checklists, i18n={})
walk(s)
if __name__ == '__main__':
    dump(s, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'np4.en.json'))
    print('tables', len(tables), 'tools', len(tools), 'forms', len(forms), 'docs', len(documents), 'chk', len(checklists), 'msg', len(messages), 'kpis', len(kpis), 'charts', len(insights['charts']),
          'gauges', len(insights['gauges']), 'sig', len(signature), 'desc', len(listing['description']), 'title', len(listing['title']))
