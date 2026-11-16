#!/usr/bin/env python3
"""Write the picture texts (tagline, signature name and why) into du1..du8.en.json. Only these fields change."""
import json
W = '/home/claude/work/du/'
T = {
1: ("Price each quote by income per hour and see where enquiries drop out", [
 ("Quote with income per hour", "Price a package, add-ons, travel and discount on one page, with the deposit, balance and instalment dates"),
 ("Funnel leak finder", "See the step where enquiries drop out, each step set against your own last 6 months"),
 ("Lost-enquiry cause ranking", "Fix the biggest cause first: price, date full, no backup, another doula or no reply, with the quote value lost"),
 ("Due-month demand map", "Spot months where demand passes your monthly limit before you say yes, with clients booked and open quotes"),
 ("30-day contract forecast", "Expect contracts in 30 days from open enquiries and your own step rates, in Base, Best and Worst"),
 ("Reply-time impact", "Compare booking and signing after a fast and a slow first reply, and the contracts a faster reply would add each month"),
 ("Price-lost break-even", "Know how many price-lost enquiries a discount must win back to pay for itself, from your own history"),
 ("Quote expiry tracker", "Chase the quotes ending this week first, with the value at risk"),
 ("Follow-up call list", "Know who to call, write to or close today, from days since the consultation and its outcome"),
 ("Reply coverage by weekday", "Find the weekday that needs cover from your average hours to a first reply"),
]),
2: ("Rank every package by income per hour and test a price before you change it", [
 ("Package ranking by income per hour", "Find the lowest-earning package before it costs another year: real hours per phase, mileage taken off"),
 ("Price check: raise, hold or lower", "Turn your owner pay and costs into the income per hour you need, the price needed and a verdict"),
 ("Combined-package test", "Learn whether a bundle pays: its price against its parts, the discount given and the income per hour"),
 ("Add-on keep, reprice or drop", "Stop a small add-on hiding a loss: income, hours and attach rate against your target"),
 ("Break-even price solver", "Get the price that earns your target per hour, at plan hours and at actual hours"),
 ("Hour-pack sizing", "Compare the 40, 80 and 120 hour packs and the night pack with shift rates and the discount each gives away"),
 ("Discount ceiling", "Find the biggest community-rate or returning-client discount that still holds your target income per hour"),
 ("Plan hours against actual hours", "Fix plan hours that are wrong: planned against real hours per package, with the clients over plan"),
 ("Price change scenarios", "Test a rise or cut on one package in Base, Best or Worst: yearly income and income per hour"),
 ("Local range position", "See each package price below, inside or above your own local low and high"),
]),
3: ("Chase the right balance first and see cash held for work not yet done", [
 ("Deposit and balance chase list", "Know who to chase first: deposits unpaid and balances overdue in 0 to 30, 31 to 60 and 61 or more day bands"),
 ("Payment plan builder", "Split a balance into 2 to 6 instalments and see if the plan ends before the on-call window opens"),
 ("Cash held for work not yet done", "See prepaid cash per client and in total, earned by phase at shares you set"),
 ("Refund and change rate", "Compare your change and cancellation rate with your own setting: cash kept, refunded and the top reason"),
 ("Cancellation settlement", "Type a client and a date to see the cash kept, the refund and the unearned cash released"),
 ("12-week cash receipts forecast", "Expect cash from instalments and balances due, times your own on-time share, in Base, Best and Worst"),
 ("Window-entry balance check", "Catch clients entering the on-call window soon with money still owed, and who to chase first"),
 ("Overdue chase ranking", "Call the right client first: unpaid balances ranked by amount times days overdue"),
 ("Payment plan risk check", "Move dates before the window opens: plans ending after the on-call start or with a late instalment"),
]),
4: ("Test any new due date against windows, monthly cap and backup cover", [
 ("On-call forecast, 6 months ahead", "See every client window day by day and week by week, with the busiest weeks ranked and a verdict"),
 ("Can I take this client?", "Get yes, yes with backup booked or decline from a due date and a doula: overlaps, monthly cap used, backup free"),
 ("Monthly cap and free dates", "See due dates booked against your own cap for 12 months, the months left open and a what-if cap"),
 ("Overlap scenario test", "Learn if your backups are enough when all clients due in one month are attended in the same 7 days"),
 ("Backup cover check", "Find windows with no backup named, soonest first, with the backup load that week"),
 ("Backup pay and missed-birth rule", "Work out flat, share or hourly backup pay, what doula and agency keep, and the rule if the backup cannot attend"),
 ("Time-off planner", "Test blackout dates against windows and due dates: the first client affected and the earliest clash-free start"),
 ("Daily on-call load", "Spot days with 2 or 3 windows: clients on call, doulas on call and the busiest doula each day"),
 ("Busiest weeks ranked", "Put backup cover where it counts: weeks ahead ranked by clients on call and windows of one doula"),
 ("Unnamed backup alerts", "Fix the soonest window with no backup in one call: the client, the doula and the days left"),
 ("Peak season planner", "Plan backups for the peak month from due dates by month, this year and last, with your own trend"),
]),
5: ("Compare planned and real hours, miles and rest days for every client", [
 ("Actual hours against plan", "Find the client furthest over plan: prenatal, on-call, birth and postpartum hours against the package"),
 ("Postpartum hours ledger", "Bill extra hours at once: hours bought, used and left per pack, with extra hours as an invoice-ready amount"),
 ("Weekly hours load", "Spot overload early: each doula's weekly hours against the cap and the weeks in a row over it"),
 ("Mileage cost and travel fee test", "Know when a travel fee is needed: mileage cost as a share of the package price"),
 ("Births attended summary", "Count births per month, doula and quarter against your own maximum, with hours and averages"),
 ("Rest days between births", "Check the days between two births of one doula against your minimum before the next window opens"),
 ("Pack expiry planner", "Use hours before they lapse: packs ending in 30 and 60 days, visits a week needed and hours at risk"),
 ("Pack pace check", "See if a pack will finish in time: hours used per week against the pace needed before expiry"),
 ("4-week hours forecast", "Expect hours per week from open packs, on-call windows and booked visits, in Base, Best or Worst"),
 ("Call-to-arrival time", "Watch response time: minutes from call to arrival per doula, day and night, against your limit"),
 ("Hours by phase per client", "Review package hours client by client: the share over plan and a flag on one row each"),
]),
6: ("Check each pay run and find the split that costs the agency money", [
 ("Agency pay and margin calculator", "Know the margin before you assign: pay, backup, mileage and overhead for a package, doula and trips"),
 ("Best doula to assign", "See places left per doula in any month and the best doula for a birth or postpartum client"),
 ("Agency split proposal", "Test a proposed share on owner margin and doula pay, with the counter share that keeps your target"),
 ("Doula pay run check", "Catch every difference: per-client, per-hour, mileage and backup pay against what was paid"),
 ("Owner own-client load", "See your hours as doula and as manager against your draw, with the hours to hand over"),
 ("Losing split finder", "Find the doula whose split loses money and the share that breaks even"),
 ("Profit by doula", "Compare doulas on revenue, pay, mileage and margin, per doula and per hour worked"),
 ("Pay run statement", "Send each person a monthly statement checked against what was paid, and see if it went on time"),
 ("Agency margin by client", "See the margin on every client: revenue, doula pay, mileage and overhead"),
 ("Backup stipend and call-out run", "Pay backup doulas right: rota weeks and call-outs turned into what each is due"),
]),
7: ("Rank sources by income, find class break-even and chase reviews and thank-yous", [
 ("Referral source ranking by income", "Feed, hold or cut each source by income, not count, after gifts and fees"),
 ("Referral gap list", "Win back referrers who sent clients before and none now, with the follow-up date"),
 ("Thank-you due list", "Thank every referral that became a client, with the gift value to send"),
 ("Class and workshop economics", "See profit per class hour: price, seats, sign-ups and break-even against your own history of each class"),
 ("Class break-even solver", "Know the fewest sign-ups that cover venue cost and instructor time, and the price that would"),
 ("Review request pipeline", "Know who to ask for a review today and who to remind, with the answer rate against your target"),
 ("Marketing keep or drop", "Drop what does not pay back: cost per signed client and months to pay back for each listing, post or flyer"),
 ("Source mix risk", "Avoid relying on one source: the share of clients from your top source and top two"),
 ("Care provider office planner", "Plan the next visit, thank-you or hold: offices ranked by referral trend over 12 months"),
 ("Class income forecast", "Expect 3 months of class income from your own history, with the quiet December and Base, Best and Worst"),
]),
8: ("12-month cash forecast, owner draw check and renewal dates in red and amber", [
 ("12-month cash forecast", "Find the lowest month and the cover against your floor, from due dates, payment plans and unbooked births"),
 ("Owner pay and tax set-aside", "Answer can I pay myself this month: the set-aside to move and the draw your cash allows (confirm with your adviser)"),
 ("Renewal dates in red and amber", "Never miss a renewal: red within 30 days, amber within 60, with the cost of the year"),
 ("Profit ratios by month", "Compare margin, doula pay share and cost per birth with your last 3 months and the same month last year"),
 ("Compare with own history", "Spot drops: every monthly figure against its 3-month average and last year, flagged over your set share"),
 ("Year-end summary and plan", "Plan next year: births, income and profit, then the births a month your income target needs at your prices"),
 ("Break-even births a month", "Know the births a month that cover fixed costs and your draw, with a price what-if"),
 ("Unearned cash by contract", "See cash received for work not yet done, contract by contract, against the cash you hold"),
 ("Budget against actual ranking", "Rank expense categories by overspend against the monthly budget and the same month last year"),
 ("Time-off cash test", "Test a break: weeks without new births against cash held and the months of cover that costs and draw need"),
]),
}
for n, (tag, items) in T.items():
    p = W + f'du{n}.en.json'
    d = json.load(open(p, encoding='utf8'))
    sig = d['signature']
    assert len(sig) == len(items), (n, len(sig), len(items))
    d['tagline'] = tag
    for s, (nm, why) in zip(sig, items):
        s['name'] = nm; s['why'] = why
    json.dump(d, open(p, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print('part', n, 'ok', len(tag))
