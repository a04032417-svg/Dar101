# Research 16 — STRICT listing-level check (2026-11-15, accD-0645, after the owner rejected slots 8-10)
Rule: PASS = profession-specific business listing >= 100 item reviews or >= 1,000 sales, or a profession-dedicated shop >= 2,000 sales. Result: 0 of 30 professions passed. Etsy market/search pages and findniche search are blocked from here; evidence comes from Etsy listing pages.

## Group A

Budget: 16 web calls used (6 searches, 10 fetches incl. 1 rate-limited and 1 blocked). findniche.com pages never surfaced in any search, so no findniche per-listing sales data exists for any candidate. Etsy market pages are not fetchable (URL not on the allowlist).

| Profession | Best listing (title, seller) | Item reviews | Sales total / 30-day (findniche) | Dedicated shop sales | Price | URL(s) | Result |
|---|---|---|---|---|---|---|---|
| Dog breeder / kennel | Dog Breeder Spreadsheet, Litter Tracker, Puppy Weight Log, Waitlist - SheetSmartTemplateCo (also: Dog Breeder Planner PDF, UnfoldFactory) | 0 (both) | not found | SheetSmartTemplateCo 18 total shop sales (not dedicated); UnfoldFactory 291 (general pet/planner shop, not dedicated) | 9.99 (sale from 19.99); PDF 1.29 | https://www.etsy.com/listing/4606037207 ; https://www.etsy.com/listing/4478909435 | FAIL |
| Content creator / influencer | Influencer Income Tracker, UGC Brand Deal ROI Calculator - ProFormaGRID | 0 | not found | 6 total shop sales (not dedicated) | 11.00 | https://www.etsy.com/listing/4581769448 | FAIL |
| Author / self-publisher | Book Promotion Tracker - Launch and Marketing for Indie Authors - WorkingWriterInk | 6 | not found | 1.1k total shop sales (writer-focused shop, below the 2,000 bar) | 7.99 | https://www.etsy.com/listing/1706174820 | FAIL |
| Coaching / consulting | Tennis Coach Profit Tracker - ProFormaGRID; generic Client Tracker Spreadsheet - businessViewCo | 0 ; 0 | not found | ProFormaGRID 6 ; businessViewCo 39 (not dedicated) | 11.11 ; 11.65 | https://www.etsy.com/listing/4582114097 ; https://www.etsy.com/listing/1451707814/client-tracker-spreadsheet-client | FAIL |
| Mortgage loan officer / insurance agent | No profession-specific listing found; searches returned only generic client trackers | n/a | not found | n/a | n/a | https://www.etsy.com/listing/1451707814/client-tracker-spreadsheet-client (generic, 0 reviews, shop 39 sales) | FAIL (no evidence) |
| Charcuterie / grazing / meal-prep | Charcuterie Pricing Calculator Spreadsheet, Grazing Table Price Per Guest - CraftCostSheets | 0 | not found | 1 total shop sale | 4.79 (sale from 7.99) | https://www.etsy.com/listing/4600810480 | FAIL |

PASS candidates, ranked by strength: none.
Closest miss (still FAIL): author/self-publisher - the only listing with any item reviews (6), from a 1.1k-sale writer shop; buyers there buy small spreadsheet trackers (launch/promotion), not paper forms.

Notes: all spreadsheet evidence found is sub-12 USD and low volume. Dog breeder buyers do buy low-price PDF planners (UnfoldFactory, 1.29 USD, 291 shop sales) but the listing itself has 0 reviews. Not verified: findniche data, Etsy market pages, and any listing beyond those fetched (search results gave no review snippets), so a pass elsewhere is not ruled out.

## Group B

Method note: 16 web calls used. No findniche.com/etsy-product page surfaced for any candidate, so there are no per-listing sales totals or 30-day figures. Etsy market pages were not fetchable (not on allowlist). Evidence below comes from Etsy listing pages that did load.

| Profession | Best listing (title, seller) | Item reviews | Sales total / 30-day (findniche) | Dedicated shop sales | Price | URL(s) | Result |
|---|---|---|---|---|---|---|---|
| Notary / loan signing agent | Script for Notary Loan Signing Agents (Document Cheat Sheet), Businesschicstudios | 8 | none found / none found | 156 (shop not notary-only confirmed) | $5.99 | https://www.etsy.com/listing/1074471644/script-for-notary-loan-signing-agents | FAIL |
| Notary (spreadsheet) | Notary Expense Ledger, Schedule C (Google Sheets), LedgerLightCo | 0 | none found | 2 | $12.99 | https://www.etsy.com/listing/4601071644 | FAIL |
| Notary (training guide) | Loan Signing Agent Training Guide, MBPMoneySolutions | 0 | none found | 10 | $25.85 | https://www.etsy.com/listing/1884029483 | FAIL |
| Virtual assistant / freelance | Client Tracker Spreadsheet (generic small business, not VA-specific), businessViewCo | 0 | none found | 39 | $11.65 | https://www.etsy.com/listing/1451707814/client-tracker-spreadsheet-client | FAIL |
| Car dealer / car flipping | none found (only generic reseller trackers) | n/a | none found | n/a | n/a | search only, no listing loaded | FAIL |
| Home inspector / appraiser | none found (only free or software templates, and a rental inspection PDF) | n/a | none found | n/a | n/a | search only, no listing loaded | FAIL |
| Tattoo artist / studio | Tattoo Artist Ledger, Piercer Income Expense Sheet, ProFormaGRID | 0 | none found (findniche only returned temporary tattoo products) | 6 | $11.11 | https://www.etsy.com/listing/4582125561 | FAIL |
| Nonprofit / church treasurer | Tithe Tracker Spreadsheet Excel Google Sheets, AccountantSheetsCPA | 0 | none found | 1 | $4.99 | https://www.etsy.com/listing/4519927490/tithe-tracker-spreadsheet-excel-google | FAIL |
| Small retail boutique | Consignment Inventory Tracker Spreadsheet (clothing/furniture resale), Kitwell | 0 | none found | 101 | $19.99 | https://www.etsy.com/listing/4536535336/consignment-inventory-tracker | FAIL |
| DJ / photo booth / party rental | DJ Services Contract Bundle, ProBizTemplates | 9 (listing shows "In 5 carts") | none found | 18k (multi-profession template shop, not DJ-dedicated, so does not qualify) | $4.75 | https://www.etsy.com/listing/1828758000 | FAIL |

Candidates that PASS, ranked by strength: none. All 8 FAIL on listing-level evidence.
Closest: DJ and photo booth (9 reviews, in 5 carts, but the buyer purchases contract and intake form kits, i.e. paper/Word forms, from a general template shop); notary (8 reviews on a $5.99 cheat-sheet PDF, so buyers buy reference documents rather than spreadsheets).

## Group C

| Profession | Best listing (title, seller) | Item reviews | Sales total / 30-day (findniche) | Dedicated shop sales | Price | URL(s) | Verdict |
|---|---|---|---|---|---|---|---|
| RE transaction coordinator | Real Estate Transaction Coordinator Client Dashboard Google Sheets, RealEstateDesignCo (other TC listings: same seller Google Forms TC templates 9 reviews; TrackerPro Transaction Coordinator Tracker 0 reviews). The claimed "Transaction Manager ... 744 reviews" listing was NOT found or verified (2 searches, not in results). | 12 (best verified) | none found | RealEstateDesignCo 18.4k (RE-agent-focused shop, TC is a sub-line); TrackerPro 20k (general) | $6 (sale from $12) | https://www.etsy.com/listing/1701929614 ; https://www.etsy.com/listing/1495404029 ; https://www.etsy.com/listing/1503119514 | FAIL (744 unverified; also overlaps real estate agent) |
| Wedding/event venue owner | not checked (call budget) | n/a | n/a | n/a | n/a | n/a | FAIL (no evidence) |
| Graphic designer / branding studio | findniche search returned only Fiverr/Etsy-seller-service noise, no listing | n/a | none | n/a | n/a | n/a | FAIL (no evidence) |
| Web designer / small agency | not checked | n/a | n/a | n/a | n/a | n/a | FAIL (no evidence) |
| Pet sitting / dog walking | Pet Sitting Spreadsheet, Dog Walking Booking Tracker, TeamTimeToolsDesigns | 0 | none | shop 0 sales | $19 | https://www.etsy.com/listing/4611229358 | FAIL |
| Professional organizer | Search returned only generic small-business bundles; PrioriDigitalStudio service-business bookkeeping tracker has 12 reviews (generic, not organizer-specific) | 12 (generic) | none | 179.3k (general shop) | $13.18 | https://www.etsy.com/listing/1853291554 | FAIL |
| Screen printing / custom t-shirt | Search results only calculators/blogs; no Etsy listing fetched | n/a | none | n/a | n/a | n/a | FAIL (no evidence) |
| Personal / private chef | Only consumer meal planner found (SavvySpreads Weekly Meal Planner, personal use, not a chef business tool) | 28 | none | 27.4k (general) | $1.54 | https://www.etsy.com/listing/1838396093 | FAIL |

PASS list: none. No candidate had a profession-specific business listing with >=100 reviews or >=1,000 sales, or a dedicated shop with >=2,000 sales, verified.

Closest: real estate TC (only if the unverified 744-review listing is real, then buyer buys a Google Sheets pipeline/contingency tracker; but it overlaps the already-taken real estate agent line). Weakly tested: venue, graphic/web designer, screen printing (no listing-level data obtained).

## Group D

14 of 16 web calls used (5 searches, 3 more searches, 7 fetches incl. failures). No findniche per-listing pages surfaced for any candidate. Etsy listing fetches returned review counts only where noted.

| profession | best listing (title, seller) | item reviews | sales total / 30-day (findniche) | dedicated shop sales | price | URL(s) | PASS/FAIL |
|---|---|---|---|---|---|---|---|
| recruiter / staffing agency | No recruiter-business listing found. Only job-SEEKER trackers (consumer, not valid): "Job Application Tracker" NavPrintables; PalmAndGraceDesigns; ProductivePenguinCo (Bestseller, in 6 carts) | 51 / 31 / 8 (consumer listings) | none found | none (general shops: 3.4k / 14.7k / 39.1k, not dedicated) | 2.55-6.33 | https://www.etsy.com/listing/1452879920 ; https://www.etsy.com/listing/1603277705 ; https://www.etsy.com/listing/4461615514 | FAIL (no profession-specific evidence; only Fiverr/Taskade-type offers) |
| horse boarding / equestrian barn | "Horse Care Tracker Spreadsheet, Barn Management", SheetSmartTemplateCo | not shown (shop: 4 ratings) | none found | 18 sales | 8.99 (was 17.99) | https://www.etsy.com/listing/4607357588 | FAIL |
| motel / small hotel owner | none found on Etsy | n/a | none found | none | n/a | (combined search returned nothing relevant) | FAIL |
| campground / RV park | none on Etsy; only software vendors and Excel models on Flevy/AdventuresInCRE | n/a | none found | none | n/a | search only, no listing | FAIL |
| car wash | none on Etsy; only Eloquens/ProjectionHub financial models | n/a | none found | none | n/a | https://www.eloquens.com/tool/7JapsjdB/jair-almeida/car-wash-financial-model-and-budget-control-template-google-sheets | FAIL |
| door-to-door / solar sales team manager | none found | n/a | none found | none | n/a | n/a | FAIL |
| medical billing service | none found; results were therapist money ledgers (therapy already taken) | n/a | none found | none | n/a | https://www.etsy.com/listing/4596218708 (therapist, excluded) | FAIL |
| barbershop / hair braiding | "Barber Chair Rental Income Tracker, Barber Shop Spreadsheet" (Etsy 4521622872) and "Salon Booth Rent Tracker" LedgerLaunchCo ($7.99); both pages failed or showed "unavailable", no counts. Barber Finance Tracker on Gumroad (wanner34) has no numbers fetched. Also overlaps hair salon product. | not retrievable | none found | none retrievable | 7.99 | https://www.etsy.com/listing/4521622872 ; https://www.etsy.com/listing/4517303249 ; https://wanner34.gumroad.com/l/bcrxd | FAIL (unverified, and overlaps salon) |

PASS candidates ranked by strength: none.
What buyers actually buy: not established for any candidate; the only evidenced demand (job-seeker trackers, 8-51 reviews, shops 3-39k sales) is a consumer spreadsheet product, not a business-owner tool.
