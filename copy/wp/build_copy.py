import json
d={}
d["name"]="Wedding Planning Suite"
d["title"]="Wedding Planner Excel Template, Wedding Budget, Guest List RSVP Tracker, Seating Chart, Vendor Tracker, Run of Show, Checklist"
d["headline"]="Know what you owe, who is coming and where everyone sits"
d["seo_title"]="Wedding Planner in Excel – Know Your Costs and Headcount"
d["seo_description"]="8 Excel workbooks to plan your own wedding: budget, guests and RSVPs, vendors, seating, run of show, honeymoon. Sample data inside. 29 dollars once."
d["tags"]=["wedding planner","wedding budget","wedding checklist","guest list tracker","rsvp tracker","seating chart","wedding timeline","vendor tracker","run of show","wedding spreadsheet","honeymoon budget","excel template","wedding planning"]
d["description"]="""Plan your own wedding with 8 Excel workbooks: budget and payments, guests and RSVPs, vendors, seating, checklist, run of show and honeymoon. One payment of 29 dollars, no subscription, no macros.

Know what you owe, when it is due, who is coming and where they sit, before the next deposit. A sample wedding is already inside, so every verdict works before you type a row.

WHAT YOU CAN DO
- See if you are funded, what is over plan and when cash runs short.
- Give the caterer a headcount from your RSVPs: low, likely and high.
- Compare quotes on true cost, with charges, taxes and overtime added.
- Test if your guests fit, even if everyone says yes.
- Date every task from the wedding day, even with under 12 months left.
- Plan the day by the minute against your venue hours.
- Clear the thank-you backlog and see what the wedding cost per guest.

WHAT IS INSIDE: 8 WORKBOOKS
1 Budget, Payments and Cash Plan
2 Guests, Invitations and RSVPs
3 Vendors, Quotes and Contracts
4 Master Timeline and Task Owners
5 Venue Capacity and Seating Plan
6 Wedding Party and Day-Of Run-of-Show
7 Events, Travel and Honeymoon
8 Attire, Decor, Gifts and Wrap-up
Each workbook has 20 tables, 18 tools, 12 forms, 12 documents, 12 checklists, 34 message texts, 30 dashboard numbers, 22 charts and 6 gauges. Over the eight: 160 tables, 144 tools, 96 forms, 96 documents, 96 checklists, 272 message texts, 240 dashboard numbers, 176 charts and 48 gauges.

WHO IT IS FOR
Engaged couples planning their own wedding, with or without a planner, and the parents and helpers who lend a hand. NOT FOR: booking, online RSVP collection, taking payments or legal or tax advice. The workbooks take typed or pasted data.

WHY A WORKBOOK
Wedding apps and websites are often free but push vendor ads and upsells, and a single planner sheet covers one job. This is 29 dollars once.

HOW IT WORKS
1 Open the workbook for the job you need first.
2 Replace the sample rows in the coloured input cells with your own.
3 Read the dashboard; each tool ends in a plain verdict.

FILE FORMAT
Standard .xlsx files for Microsoft Excel, Google Sheets and LibreOffice. A blank workbook and a sample-data copy for every part. Formula cells are locked against accidental edits (no password); instructions are on the first sheet. Instant download.

GUARANTEE
If a file does not work as described, we fix it, replace it or refund you within 14 days.

See the FAQ for Google Sheets, currency, small and large weddings, helpers and refunds."""
d["features"]=[
"Know if you are funded and what each family still owes before the next payment",
"Find the first month cash runs short, with the payment to move or the amount to add",
"See the true cost of each quote with service charge, taxes, delivery and overtime",
"Give the caterer a headcount from your own RSVPs: low, likely and high",
"Chase the silent households in order of the guests at stake",
"Test if your guests fit, and what happens if everyone says yes",
"Seat every table with keep-together and keep-apart rules checked",
"Date every task from the wedding day, even with under 12 months left",
"See contract dates and final balances come due, red, amber or green",
"Plan the day by the minute and see the overrun against your venue hours",
"Compare one big wedding with a small ceremony plus a party, line by line",
"Clear the thank-you backlog and see what the wedding cost per guest"]
d["faq"]=[
{"q":"Does it work in Google Sheets?","a":"Yes. The files are standard .xlsx files for Microsoft Excel, Google Sheets and LibreOffice. They use the same engine as our published suites, which were tested in Google Sheets."},
{"q":"Can I change the currency and the date format?","a":"Yes. Dates follow your computer's regional format, and the currency symbol changes in one cell. Amounts are plain numbers, so any currency works."},
{"q":"Can we use it for a small courthouse wedding or a 200-guest weekend?","a":"Yes. A 30-guest wedding uses the same sheets with fewer rows, and a small wedding hides the areas that do not apply. For a big weekend, the events, guest-nights and room block sheets handle several events and many guests."},
{"q":"Can parents or a planner help in the same files?","a":"Yes. Tasks have owners, and the files print a page per person for those who do not edit. A parent, wedding party lead, day-of coordinator or planner can use the same workbooks; share the files as you share any file."},
{"q":"What if a file does not work as described?","a":"We fix it, replace it or refund you within 14 days. That is the store's refund policy, and it applies to every file in the suite."},
{"q":"Where do I start, and can I replace the sample data?","a":"Start with the workbook for the job that worries you most. Each one works on its own and comes blank and filled with sample data. Type over the sample rows in the coloured cells. No macros, no subscription."}]
d["stats_note"]="{files} workbooks · {pages} pages · sample data included"
d["inside_h1"]="Every page in the suite"
for p in ('/home/claude/work/copy/wp/en.json','/home/claude/work/wp/listing/final/en.json'):
    json.dump(d,open(p,'w',encoding='utf8'),indent=1,ensure_ascii=False)
