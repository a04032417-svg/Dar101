import json
W='/home/claude/work/wp/'
TAG={
1:"Know you are funded, what is due next and when cash runs short",
2:"Know how many guests will come and which households to chase",
3:"Know the true cost of every quote and your next contract date",
4:"See what is late, who holds too much and what to do this week",
5:"Know your guests fit, seat every table and order the right rentals",
6:"Fit the day to your venue hours and give everyone a page of their own",
7:"See what each event, the travel and the honeymoon cost, and the gap",
8:"Make or buy, clear the thank-you backlog and see the cost per guest",
}
SIG={
1:{
"Final balance cover check":("Final balance cover check","See which final balance you cannot cover on its due date, after the payments due before it"),
"Cash needed by month":("Cash needed by month","Find the first month cash goes short: payments due against savings and family transfers"),
"Payment mover":("Payment mover","Pick which unpaid payment to ask a vendor to move, ranked by amount and ease of moving"),
"Budget rebalancer":("Budget rebalancer","Cover an over-plan line from the most flexible categories, with the amount taken from each"),
"Cut guests scenario":("Cut guests scenario","See what fewer guests change: per-guest lines scale, the minimum guarantee holds, fixed lines stay"),
"Settle-up between payers":("Settle-up between payers","See who owes whom: each payer's agreed share of everything paid against what they paid"),
"Savings pace":("Savings pace","Know the extra saving each month that closes the funding gap by the last payment date"),
"True budget and reserve":("True budget and reserve","See the plan plus expected hidden costs and tips, and test your reserve against them"),
"Move the date scenario":("Move the date scenario","Compare quotes for the big five vendors on each date you consider, with the lead-time check"),
"Funding plan check":("Funding plan check","Know if you are funded: received and promised money against budget, cash gifts only once received"),
},
2:{
"Final headcount forecast":("Final headcount forecast","Give the caterer one number: low, likely and high from your yes rate, with the cost of each"),
"B list cascade":("B list cascade","Fill the seats declines open: the next B list household by rank, from open seats at expected headcount"),
"Last send date for the B list":("Last send date for the B list","Find the latest day a second-wave invitation can still go out, counted back from your reply-by date"),
"RSVP chase ranker":("RSVP chase ranker","Chase the right households first: ranked by guests at stake, days silent and contact status"),
"Plus-one and children policy test":("Plus-one and children policy test","Compare 4 policies on headcount, food cost and venue fit, with the cheapest and most inclusive named"),
"Guarantee exposure":("Guarantee exposure","See what empty seats cost if fewer guests come than your minimum guarantee, on 5 headcounts"),
"Room block attrition exposure":("Room block attrition exposure","See the rooms you must fill against the rooms you expect, priced at your rate, before the attrition date"),
"Side balance check":("Side balance check","See which side is heavy and by how many guests, against the split you agreed"),
"Capacity traffic light":("Capacity traffic light","Know if you fit: three headcounts against seated capacity, shown as fits, tight or over by a number of seats"),
"Reply pace forecast":("Reply pace forecast","See if replies will arrive by the reply-by date: your weekly pace, slowing, against guests still silent"),
},
3:{
"True-cost comparison":("True-cost comparison","Find the quote that is really cheapest: service charge, taxes, delivery, overtime, travel and tip added"),
"Weighted score ranker":("Weighted score ranker","Pick the best fit, not only the lowest price: your ratings for fit, reply and reviews, weights you edit"),
"Quote negotiation lever":("Quote negotiation lever","Know whom to ask and for how much: the price drop that lets the second-best quote win"),
"Contract completeness check":("Contract completeness check","Find what a booked contract is missing: inclusions, cancellation terms, final payment date, arrival"),
"Final headcount date alarm":("Final headcount date alarm","Know when the caterer, venue and rentals need your count, with the figure to send and the days left"),
"Cancellation exposure":("Cancellation exposure","See the deposits and payments you could lose if you cancelled, per vendor and in total"),
"Arrival overlap finder":("Arrival overlap finder","Catch two vendors setting up in the same place at the same time, with the first clash time"),
"Contract deadline countdown":("Contract deadline countdown","See contract dates, unpaid payments and quote expiry in one list, red, amber or green"),
"Booking deadline ranker":("Booking deadline ranker","Know which open category to book first, ranked by days left before its latest booking date"),
"Plan fit by category":("Plan fit by category","See the room left in each budget line: booked contracts plus the leading quote of each open slot"),
},
4:{
"Master timeline builder":("Master timeline builder","Get every task dated from the wedding day for your wedding type, with the tasks that do not apply hidden"),
"Compressed mode re-dater":("Compressed mode re-dater","Planning in under 12 months? Tasks are re-dated in proportion and those that miss their lead time named"),
"Invitation print slip":("Invitation print slip","Find the latest day the invitation files can reach the printer, counted back from your reply-by date"),
"Critical path slack":("Critical path slack","See which late task moves the wedding: the days between each critical task and the next"),
"Owner workload balance":("Owner workload balance","See when one person holds too much: open tasks by owner against your limit, with the owner named"),
"Delegation suggester":("Delegation suggester","Hand off the right task: the first non-critical task of the heaviest owner moves to the usual helper"),
"Deadline countdown":("Deadline countdown","See the next dates from payments, replies, headcount, room cut-off, vendors and fittings, red, amber or green"),
"Date change impact":("Date change impact","Move the wedding date and see which dates shift and which tasks become overdue"),
"Lead-time check":("Lead-time check","Find the task that started too late: each open task against the typical lead time of its area"),
"Done pace forecast":("Done pace forecast","Get a finish date from your own pace, with the days it falls before the wedding"),
},
5:{
"Table count solver":("Table count solver","Know how many tables you need and if you fit: headcount plus couple, vendor and spare seats"),
"Table size comparison":("Table size comparison","Pick the table size for your room: tables of 6, 8, 10 and 12 compared on tables, empty seats and floor area"),
"Everyone-says-yes scenario":("Everyone-says-yes scenario","See how many seats over you are if every invited guest comes, and how many must decline"),
"Late reply seat finder":("Late reply seat finder","Seat a late yes fast: the table with room that fits its side best, or a prompt to open a table"),
"Keep together and keep apart checker":("Keep together and keep apart checker","Find every broken seat rule, listed in fix order, tested against your table assignments"),
"Seat swap suggester":("Seat swap suggester","Fix each conflict: the guest to move, the table to move to, and a swap when that table is full"),
"Rental quantity calculator":("Rental quantity calculator","Order the right amount: chairs, linens, plates and glasses from final tables plus your spare share"),
"Spare seat reserve":("Spare seat reserve","Hold the right seats back: spare seats at each table for late replies, and the tables that stay full"),
"Floor space check":("Floor space check","Check the room is not too tight: floor area less dance floor, buffet, stage and walkways, per guest"),
"Final seating sign-off":("Final seating sign-off","Know when seating is ready to print: 8 checks on one page, with the items left to fix"),
},
6:{
"Last safe order date":("Last safe order date","Never order an outfit too late: counted back from the fitting, alteration weeks and shipping days"),
"Run of show overrun check":("Run of show overrun check","See if the day fits your venue hours: plan end against closing time, with overtime cost and minutes to cut"),
"Travel time check":("Travel time check","Test every move between the hotel, the venue and the shuttle against the minutes the plan gives it"),
"Who needs to be where":("Who needs to be where","Pick a person or group and a time to see the step, the place and the person in charge"),
"Page per person":("Page per person","Print one page for the wedding party, the parents, the vendors, the officiant and the guests"),
"Late start impact":("Late start impact","See what a late ceremony does: which steps slide, the new end time and the overtime it adds"),
"Day-of contact list":("Day-of contact list","Name one person and a backup for the gifts, the cards, the tip envelopes and the returns"),
"Buffer planner":("Buffer planner","Find which block of the day needs buffer minutes first, from its vendor and guest steps"),
"Fitting calendar with a clash flag":("Fitting calendar with a clash flag","See fittings by date and flag the days that hold more people than your shop can fit"),
"Sunset and light check":("Sunset and light check","Check portraits and ceremony against your sunset time, with the minutes to move them earlier"),
},
7:{
"Multi-event cost planner":("Multi-event cost planner","See every event's cost, paid, still to pay and cost per invitee: shower, weekends away and dinners in one place"),
"Event invitee check":("Event invitee check","Check each event's invitees as a part of your guest list, with the overlap between two events"),
"Guest-nights counter":("Guest-nights counter","Count the guests staying each night, with the rooms needed at the busiest night against the rooms you hold"),
"Destination cost total":("Destination cost total","Get one verdict for a destination wedding: your travel, the party travel you cover and local quotes at your rate"),
"Exchange rate sensitivity":("Exchange rate sensitivity","See the range: local quotes priced back into your currency with the rate moved down and up"),
"Travel decline uplift":("Travel decline uplift","Allow for extra declines from guests who travel: your expected headcount and the number for the caterer, as an estimate"),
"Big wedding against small ceremony plus party":("Big wedding or small ceremony plus party","Compare both tracks line by line from your own budget, with cost per guest and a verdict on the difference"),
"Honeymoon two options side by side":("Honeymoon two options side by side","Compare the beach week and the city minimoon on total, cost per day and the gap against money received and promised"),
"Minimoon fallback":("Minimoon fallback","See how many days of the dearer option your money can pay for once the fixed costs are kept"),
"Honeymoon savings pace":("Honeymoon savings pace","Know the extra saving a month that closes the gap by the first booking date, from your own funds"),
},
8:{
"DIY make or buy":("DIY make or buy","Get Make, Buy or Make half for every project: supplies plus your hours at your hour value against the cost to buy"),
"DIY start date":("DIY start date","Find the latest day to start a project so it is done your chosen days before the wedding: Start by or Late by"),
"Thank-you backlog ranker":("Thank-you backlog ranker","See which gifts still need a note, oldest first against your alert days, with the notes to write this week"),
"Thank-you pace":("Thank-you pace","Know how many notes a week finish the backlog by your target date, counted from the oldest gift"),
"Cash gifts and funding link":("Cash gifts and funding","Split cash gifts between the budget and the honeymoon; expected gifts count only once received"),
"Honeymoon gap":("Honeymoon gap","See the honeymoon budget against funds received and savings promised, with the saving a month that closes the gap"),
"Final budget against actual":("Final budget against actual","Close the budget: planned, committed, paid and still due for every category, with the one that ended over plan named"),
"Cost per guest":("Cost per guest","See what the wedding really cost per guest: final cost over final headcount, against your target and a typical starting value"),
"Returns and refunds tracker":("Returns and refunds tracker","Track rentals to return and deposits to claim by date, with the refunds you can expect"),
"Wrap-up readiness":("Wrap-up readiness","Know when the wedding can be closed: 10 checks on balances, returns, notes, budget and paperwork"),
},
}
for i in range(1,9):
    p=W+f'wp{i}.en.json'
    d=json.load(open(p,encoding='utf8'))
    d['tagline']=TAG[i]
    m=SIG[i]; seen=set()
    for x in d['signature']:
        key=x['name']
        if key not in m and key=="Cost per guest Check": pass
        if key in m: x['name'],x['why']=m[key]; seen.add(key)
    # fallbacks by index for renamed keys
    miss=[k for k in m if k not in seen]
    assert not miss,(i,miss,[x['name'] for x in d['signature']])
    json.dump(d,open(p,'w',encoding='utf8'),indent=1,ensure_ascii=False)
print('ok')
