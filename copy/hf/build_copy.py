import json
name = "Household Finance Suite"
title = "Household Budget Excel Template, Family Finance Spreadsheet, Paycheck Budget, Bills, Debt Payoff, Net Worth, Google Sheets"
headline = "See your cash low point before every payday and give each paycheck a job"
seo_title = "Household Budget System in Excel: See Your Cash Before Payday"
seo_description = "Run your household money from 8 Excel workbooks: paychecks, bills, spending, debt, goals, net worth, shared costs, big purchases. 29 dollars, once."
tags = ["household budget", "family budget", "budget spreadsheet", "paycheck budget", "zero based budget",
        "bills tracker", "debt payoff planner", "sinking funds", "net worth tracker", "couples budget",
        "irregular income", "biweekly budget", "excel budget"]
description = """Household budget in 8 Excel workbooks: paycheck split, bills, spending, debt payoff, goals and net worth. One payment of 29 dollars, no subscription, no macros.
For a single adult, a couple with joint and separate accounts or a family with children who run their own money and want to see the cash low point before payday, not only what was spent last month.

WHAT YOU CAN DO
✓ Split each paycheck line by line until nothing is left to assign: weekly, every two weeks, twice a month or monthly pay.
✓ See the lowest balance before every payday and the bill that pushes the joint account under your floor.
✓ Budget from your lowest months when income is irregular, and keep what lands above them as a buffer.
✓ Rank subscriptions and contracts by yearly cost and renewal date, and see which ones you stopped using.
✓ Compare snowball and avalanche payoff with your own numbers: an estimated payoff date and interest.
✓ Set aside an amount per paycheck for every goal and every yearly cost.
✓ Split shared costs fairly, settle up in the fewest payments and test what happens if one income stops.
✓ Plan a car, a move and the tax papers, then review the year.

WHAT IS INSIDE: 8 WORKBOOKS
1 Money Plan and Paychecks
2 Bills, Subscriptions and Due Dates
3 Spending Tracker and Groceries
4 Debt Payoff Planner
5 Savings Goals and Sinking Funds
6 Net Worth and Accounts
7 Partners, Kids and Shared Costs
8 Big Purchases, Tax and Year Review
Each workbook has 20 tables, 18 tools, 12 forms, 12 documents, 12 checklists, 34 message texts, 30 dashboard numbers, 22 charts and 6 gauges. Across the 8 workbooks that is 160 tables, 144 tools, 96 forms, 96 documents, 96 checklists, 272 message texts, 240 dashboard numbers, 176 charts and 48 gauges. Each part comes twice: blank, and filled with sample data from a fictional household, so every page works before you add your own. Each workbook works on its own for the one household.

WHO IT IS FOR
A single adult with one income (use most sheets and leave the partner 2, children and shared-cost rows empty), a couple with joint and separate accounts, or a family with children. Pay can be weekly, every two weeks, twice a month, monthly or irregular: it is a setting.
NOT FOR: a bank app. Nothing reads your bank account: you type or paste rows. These are workbooks, not tax, legal, investment or credit advice. Payoff dates, interest and projections are estimates from your numbers, and every range is a typical range, check your own numbers.

HOW IT WORKS
1 Open the workbook for the job and read the first sheet.
2 Replace the sample rows with your own in the coloured input cells, and set your pay rhythm and currency symbol.
3 Read the dashboard, use the tools and follow the month-end checklist.

FILE FORMAT
Standard .xlsx files for Microsoft Excel, Google Sheets and LibreOffice. No macros. No subscription. Formula cells are locked against accidental edits (no password), input cells are coloured and instructions are on the first sheet. Dates follow your computer's regional format. One-time price of 29 dollars, instant download.

WHY NOT AN APP
Budgeting apps are usually billed every month or every year, and single budget sheets cover only one job. This is 29 dollars, once.

GUARANTEE
If a file does not work as described, we fix it, replace it or refund you within 14 days.

FAQ
Answers on Google Sheets, currency and dates, who it fits, pay rhythms, your bank and refunds are in the questions below."""
features = [
 "See the lowest balance before every payday and the bill that breaks your floor",
 "Split each paycheck line by line until nothing is left to assign",
 "Budget from your lowest months when pay is irregular and keep the rest as a buffer",
 "Know every bill due in the next 14 days and what is still unpaid before payday",
 "Find the subscriptions you stopped using and see what they cost a year",
 "Catch a grocery overspend before the month ends, not after",
 "Compare snowball and avalanche payoff and see an estimated payoff date",
 "Turn goals and yearly costs into an amount to set aside per paycheck",
 "See net worth by month and which accounts moved it",
 "Split shared costs fairly and settle up in the fewest payments",
 "Test a lost income or a one-off cost and see the gap and the months of cover",
 "Keep tax papers and receipts in one place and see what is still missing",
]
faq = [
 {"q": "Does it work in Google Sheets?",
  "a": "Yes. The files are standard .xlsx files that open in Google Sheets, Microsoft Excel and LibreOffice. They use the same engine as our published suites, which were tested in Google Sheets. There are no macros."},
 {"q": "Can I use my own currency and date format?",
  "a": "Yes. Dates follow your computer's regional format, and the currency symbol changes in one cell. Amounts are plain numbers, so any currency works."},
 {"q": "Does it fit a single adult, a couple or a family?",
  "a": "Yes. A single adult uses most sheets and leaves the partner 2, children and shared-cost rows empty. A couple with joint and separate accounts uses the fair split, settle up and account map. A family adds children's costs and allowances."},
 {"q": "Can it handle weekly, every-two-weeks or irregular pay?",
  "a": "Yes. Weekly, every two weeks, twice a month and monthly pay are settings, and months with three pay days are shown. For irregular income you budget from your lowest recent months and keep the rest as a buffer."},
 {"q": "Does it connect to my bank?",
  "a": "No. Nothing reads your bank account: you type or paste rows. That means there is nothing to re-authorise or repair, and your data stays in your files."},
 {"q": "What if a file does not work?",
  "a": "If a file does not work as described, we fix it, replace it or refund you within 14 days. Each part comes blank and with sample data, so you can try every page first."},
]
out = {"name": name, "title": title, "headline": headline, "seo_title": seo_title, "seo_description": seo_description,
       "tags": tags, "description": description, "features": features, "faq": faq,
       "stats_note": "{files} workbooks · {pages} pages · English edition",
       "inside_h1": "Every page of the suite"}
s = json.dumps(out, indent=1, ensure_ascii=False)
open('/home/claude/work/copy/hf/en.json', 'w').write(s)
open('/home/claude/work/hf/listing/final/en.json', 'w').write(s)
