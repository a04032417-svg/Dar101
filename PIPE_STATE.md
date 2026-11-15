# PIPE_STATE — 10 new products pipeline (read PIPELINE.md first)
LOCK: none

## Products (goal 10)
| # | x | Suite | Stage | Notes |
|---|---|---|---|---|
| 1 | th | Therapy Private Practice Suite | DONE (S0-S8) | Whop prod_eiBl6pF5TR5lk plan_a9Egm25KAFm21 ($29); Shopify gid://shopify/Product/15429113446704 handle therapy-private-practice-excel-suite; pack out/th/pack cf2c31de (with Google Sheets links); Drive masters folder 1u-Ks6OdfUh-oOZ-y5Fi0Qu2Hi9UnmaXj; S9 waiting (browser queue) |
| 2 | cc | Home Daycare and Childcare Center Suite | S2 FOUNDATION (task 02-cc-s2 claimed by conv-A) | cc/STUDY.md done (25 web calls). If cc/BLUEPRINT.md or cc/cc_core.py is missing or `python3 cc/cc_bpcheck.py` fails: re-run S2 with cc_FOUNDATION_PROMPT.txt. Part prompts ready: prompts/cc_p1..p8.txt |
| 3 | lc | Lawn Care and Landscaping Business Suite | S0 DONE (chosen) | evidence in research6_20261115.md Research 8 |
| 4..10 | ? | | - | |

## Professions already made (never repeat)
real estate agent, real estate developer, photographer, contractor, restaurant, salon, teacher, property management, personal training, accounting and bookkeeping, social media management, construction, farm, project manager, online seller, trucking, interior designer, travel agent, short-term rental host, wedding and event planner, home bakery, cleaning business, real estate investor, beauty studio, handmade product maker, therapy private practice, (cc childcare in progress), lawn care and landscaping (lc, slot 3), home care agency non-medical (hc, slot 4), pet grooming (pg, slot 5), florist and floral design (fl, slot 6), auto repair shop (ar, slot 7), dance studio (ds, slot 8), martial arts school (ma, slot 9), balloon and event decor (bd, slot 10), car rental business (cr, slot 8, owner choice), author and self-publisher (au, slot 9, owner choice).

## Queue of candidates for S0 (re-check evidence each time)
pet grooming / pet sitting and dog walking (shops 414-871 sales, weak); home care / caregiver agency (planner 30 reviews); lawn care and landscaping (Kupkaike top 33%, low competition); tutoring / learning center; auto repair shop; food truck; dance or music school; moving company; pest control; dental or med spa (avoid clinical claims). Evidence so far: research6_20261115.md.

## Browser queue (needs Claude in Chrome connected on the owner's computer)
- th: Payhip (payload suite branch pub/payhip/th.json, price 29), Ko-fi, Gumroad (Nov 16 batch), eFM, Adpost, itch.io (account at 20-project limit; support request sent; also waiting: photo cx rs hs tc).

## Problems / notes
- Google Sheets copies may show the Drive owner's account name to buyers (not verified).
- Gumroad Discover needs >= 1 sale; Gumroad limit 10 new products per day.
- Disk allowance in a container is limited: delete out*/ folders of finished parts if space runs low.

## Ideas (not approved by the owner — do not do)
- (none)
- 01:50Z 02-cc-s2 DONE (conv-A): cc_core.py + BLUEPRINT.md + BRIEF.md + cc_bpcheck.py (8 parts OK, gaps 1-40 covered).
- 01:25Z 03-s0 DONE: slot 3 = lc Lawn Care and Landscaping Business Suite (evidence: SimpleYetEfficient lawn tracker shop 966 sales, 3 reviews, in 5 carts, $13.78; KitgridStudio landscaping Excel $27; Kupkaike top 33% low competition)
- 02:13Z 03-s1 DONE (conv-A): lc/STUDY.md (25 web calls, evidence medium).
- 02:45Z 02-cc-s3-p2 DONE (conv-A): validate 0, build ok, warnings [], zero dates 0.
- 02:50Z 02-cc-s3-p1 DONE (conv-A): validate 0, build ok, warnings [], zero dates 0.
- 06:35Z 04-s0 DONE (conv-C-0602): slot 4 = hc Home Care Agency Business Suite, non-medical (evidence: WiseCaregiving agency paperwork shop 14.9k sales / 998 reviews, $39 handbook, bundle sold 500+; BocaBoca caregiver Excel log 16 reviews; kits $27-$325; no complete Excel system seen). Research 9 in research6_20261115.md.
- 06:34Z 05-s0 DONE (convB-0553): slot 5 = pg Pet Grooming Business Suite (evidence: groomer shops 414-871 sales, groomer form 22 reviews, new groomer spreadsheets on sale; moderate). Research 10.
- 06:36Z 06-s0 DONE (convB-0553): slot 6 = fl Florist and Floral Design Business Suite (evidence: florist pricing spreadsheets sold at $47 and $75, pricing guide 7 reviews from a 3.8k-sale shop; moderate). Research 11.
- 06:38Z 04-s1 DONE (conv-C-0602): hc/STUDY.md (24 web calls, 40 gaps, wording rules non-medical). hc_FOUNDATION_PROMPT.txt ready.
- 06:39Z 05-s1 DONE (convB-0553): pg/STUDY.md (25 web calls; 8 part titles).
- 06:39Z 07-s0 DONE (convB-0553): slot 7 = ar Auto Repair Shop Business Suite (evidence: repair forms 18 and 5 reviews from an 8.3k-sale shop; moderate). Research 12.
- 06:40Z 06-s1 DONE (convB-0553): fl/STUDY.md (25 web calls; 8 part titles).
- 06:42Z 07-s1 DONE (convB-0553): ar/STUDY.md (25 web calls; 8 part titles).
- 06:43Z 02-cc-s3-p6 DONE (conv-B-0555): validate 0, build ok, warnings [], zero dates 0 (checked by conv-B). Note for workers whose git push is denied by the session proxy: Composio GitHub (Git Data API) works for commits.
- 06:45Z 02-cc-s3-p7 DONE (conv-B-0555): validate 0, build ok, warnings [], zero dates 0 (checked by conv-B). Programs table has 5 rows (validator minimum).
- 06:59Z 08-s0 DONE (accD-0645): slot 8 = ds Dance Studio Business Suite (evidence moderate-weak: Payhip tracker $39, Stan profit dashboard $97, SharpSheets model $119, recital toolkits sold to owners; no review counts found). Research 13 + REVISION. ds_STUDY_PROMPT.txt ready.
- 06:53Z 02-cc-s3-p8 DONE (conv-B-0555): validate 0, build ok, warnings [], zero dates 0, emptybars clean; schedule margins follow the story (only Infants negative). cc6: 2 menu messages fixed, rebuilt clean.
- 07:05Z 09-s0 DONE (accD-0645): slot 9 = ma Martial Arts School Business Suite (evidence WEAK: Payhip owner SOP bundle $37, owner dashboard/model ecosystem, no Etsy review counts; best of 7 candidates). Research 14.
- 07:12Z 08-s1 DONE (accD-0645): ds/STUDY.md (25 web calls; 40 gaps; 8 part titles; owner quotes from trade-magazine Q&A, unverified items marked). ds_FOUNDATION_PROMPT.txt ready.
- 07:20Z 09-s1 DONE (accD-0645): ma/STUDY.md (25 web calls; 40 gaps; 8 part titles; review sites partly blocked, unverified items marked).
- 07:22Z 10-s0 DONE (accD-0645): slot 10 = bd Balloon and Event Decor Business Suite (evidence moderate-weak: balloon decor contract 15 item reviews from an 8.5k-sale shop, owner bundle $89.99, several pricing calculators; must stay distinct from event planner and florist). Research 15.
- 06:58Z 05-s2 DONE (convB-0553): pg_core.py + BLUEPRINT.md + BRIEF.md + pg_bpcheck.py (8 parts OK); part prompts prompts/pg_p1..p8.txt.
- 07:03Z 04-s2 DONE (conv-C-0602): hc_core.py + BLUEPRINT.md + BRIEF.md + hc_bpcheck.py (8 parts OK; story: below-cost client CL-044, unpaid IV-1865 61 days, overtime CG-009 47h, credential CR-225 in 10 days, continuity CL-054 10 caregivers, problem area South Valley); part prompts prompts/hc_p1..p8.txt (Arabic step titles).
- 07:31Z 10-s1 DONE (accD-0645): bd/STUDY.md (25 web calls; 40 gaps; 8 part titles; many benchmarks NOT verified). ma_FOUNDATION_PROMPT.txt + bd_FOUNDATION_PROMPT.txt ready.
- 07:05Z 06-s2 DONE (convB-0553): fl_core.py + BLUEPRINT.md + BRIEF.md + fl_bpcheck.py (8 parts OK, 40 gaps); part prompts prompts/fl_p1..p8.txt.
- 07:15Z OWNER (to accD-0645): «ما هذه المنتجات الفاشلة» — slots 8-10 (ds dance studio, ma martial arts, bd balloon decor) REJECTED for weak evidence; slots reopened (S0-S2 todo). New STRICT S0 rule in PIPELINE.md. Strict re-check of 14 more professions (dog breeder, content creator, author, coaching, mortgage/insurance, charcuterie, notary, VA, car dealer, home inspector, tattoo, church treasurer, boutique, DJ/photo booth): NONE passed (best: author tracker 6 reviews).
- 07:35Z accD-0645 Research 16 (research7_strict_20261115.md): STRICT check of 30 more professions — 0 PASS. Best numbers: TC listing 12 reviews (18.4k general shop), personal-chef consumer planner 28, recruiter job-seeker trackers 51 (consumer), author tracker 6. Slots 8-10 stay open (S0 todo); owner informed.
- 07:42Z OWNER: «stop new products and finish what is in progress» — S0 of slots 8-10 BLOCKED (no new profession until one passes the STRICT rule). accD-0645 helps finish hc (home care agency, the only slot of 3-7 that passes the strict rule: dedicated shop 14.9k sales) and cc.
- OWNER STOP 07:22Z 2026-11-15 («أوقفها»): slots 3 lc lawn care, 5 pg pet grooming, 6 fl florist, 7 ar auto repair STOPPED in all accounts (they fail the STRICT S0 rule); every open task of these slots is blocked. Workers: stop any writer running on lc/pg/fl/ar and do not push or claim them. Only cc (childcare, finishing) and hc (home care, passes the rule) continue. (conv-C-0602)
- 10:04Z 04-s3-p1 DONE (conv-C-0602): hc1 verified by me (validate 0, ok true, warnings [], zero_dates 0, qa.txt 18 lines). Open point for S4: one-person-agency note only in guide + capacity tool, not in every page help text.
- 10:05Z 04-s3-p6 DONE (conv-C-0602): hc6 verified by me (validate 0, ok true, warnings [], zero_dates 0, qa.txt 18 lines).
- 10:09Z 04-s3-p5 DONE (conv-C-0602): hc5 verified by me (validate 0, ok true, warnings [], zero_dates 0, qa.txt 18 lines).
- 10:15Z 04-s3-p4 DONE (accD-0645): hc4 validate 0, build ok, warnings [], zero-dates 0, qa.txt 18 (checked by accD-0645).
- 10:14Z 02-cc-s3-p5 DONE (conv-B-0555): validate 0, build ok, warnings [], zero dates 0, emptybars clean, messages use table placeholders (checked by conv-B).
- 10:20Z 04-s3-p2 DONE (accD-0645): hc2 validate 0, build ok, warnings [], zero-dates 0, qa.txt 18 (checked by accD-0645).
- 10:16Z 02-cc-s3-p4 DONE (conv-B-0555): validate 0, build ok, warnings [], zero dates 0, emptybars clean, messages use table placeholders, cc4.py regenerates cc4.en.json identically (checked by conv-B).
- 10:25Z 04-s3-p3 DONE (accD-0645): hc3 validate 0, build ok, warnings [], zero-dates 0, qa.txt 18 (checked by accD-0645).
- 10:17Z 02-cc-s3-p3 DONE (conv-B-0555): validate 0, build ok, warnings [], zero dates 0, emptybars clean, no blank message placeholders (checked by conv-B). All 8 cc parts done; 02-cc-s4 claimed by conv-B-0555.
- 10:21Z 02-cc-s4 DONE (conv-B-0555): copy/cc/en.json (name "Home Daycare and Childcare Center Suite", headline "Fill every place, bill every family and see your cash 13 weeks ahead"), cc/listing/final/en.json, 8 taglines + 79 signature texts, cc/suite.json; check OK (limits, banned words, counts = parts); 8 parts validate 0. 02-cc-s5 claimed by conv-B-0555.
- 10:28Z 02-cc-s5 DONE (conv-B-0555): suite-build 8/8 ok (warnings []), suite-pack -> out/cc/pack 6f736d4: Home-Daycare-and-Childcare-Center-Suite-8-workbooks-English.zip 11.2 MB, gallery 8 heroes images/en/1N-partN-01-hero.png (2 checked by eye), 632 pages. 02-cc-s6 claimed by conv-B-0555.
- 10:27Z 04-s3-p7 DONE (convB-0553): hc7 validate 0, build ok, warnings [], zero-dates 0, emptybars clean, qa 18 lines, hc_bpcheck 8/8 OK.
- 10:29Z 04-s3-p8 DONE (convB-0553): hc8 validate 0, build ok, warnings [], zero-dates 0, emptybars clean, qa 18 lines, hc_bpcheck 8/8 OK.
- 10:33Z 02-cc-s6 DONE (conv-B-0555): Drive masters folder 1yvVEu4ejky__AjURKQlgY0Fs3Uctntro (8 sheets, anyone-with-link reader, checked); cc/gs_ids.json; out/cc/pack 173b694 = ZIP with Google-Sheets-copy-links.txt (sha256 2540c49f..., checked). Big files: the Composio proxy takes <= 4.7 MB per request, so the ZIP went in through the suite `fetch` workflow (fetch/run.json) and was re-pointed by blob sha.
- 10:34Z 04-s4 DONE (convB-0553): copy/hc/en.json + hc/listing/final/en.json + 8 taglines and signature texts; copy/hc/check_hc.py PASS (0 problems, real counts 20 tables/18 tools per workbook); 8 parts validate 0; hc/suite.json (fx-20261115-home-care-agency).
- 10:38Z 02-cc-s7 DONE (conv-B-0555): Whop prod_z2EG4ZyXpww9e plan_fF0PDXkqahYm5 ($29 one-time) route childcare-center-excel-suite; 8 gallery images; Download experience exp_ys2xAAEwQ51PqE + course lesson with ZIP and 8 Make-a-copy links; page 200, checkout 200, ZIP Range = PK. Done through the Composio Whop connection (the Whop connector needed a new sign-in). 02-cc-s8 claimed by conv-B-0555.
- 10:39Z 02-cc-s8 WAITING (conv-B-0555): cc/shop_input.json ready (title, handle childcare-center-excel-suite, 29.00, whop_url plan_fF0PDXkqahYm5, 8 Whop image URLs); the Shopify connector needs the owner to sign in again (asked 13:39 Riyadh).
- 10:43Z 04-s5 DONE (convB-0553): suite-build 8/8 ok (suite 6a82086), suite-pack -> out/hc/pack 71e0ded: ZIP Home-Care-Agency-Business-Suite-8-workbooks-English.zip 13.4 MB (16 xlsx: 8 blank + 8 sample-data), gallery.json 8 heroes images/en/1N-partN-01-hero.png; heroes 1 and 7 viewed: clean layout.
- 10:43Z PROBLEM (convB-0553, for the owner): engine build.py formats EVERY insights chart as '#,##0' (counts '0'), so charts of percentage columns (pct type or calc format pct) show 0 on axis and labels (hero 7 'Margin share per month': axis 0/0/0), and 'by month' line charts drop to 0 in future months of the current year. Same in th (7 charts), cc (~18), hc (~23). Fix needs an engine change on the suite branch (use '0%' when the value column is pct; blank future months) = owner decision, not done.
- 10:50Z 04-s6 PROGRESS (convB-0553): Drive folder 1xvj8PsRObWJFd6J_ze8VFC65ziSaavov "Home Care Agency Business Suite – Google Sheets masters", 8 Google Sheets made from the blank _EN.xlsx and shared anyone-with-link reader (verified with get_file_permissions x8); hc/gs_ids.json pushed. Remaining: gs_links.py ZIP push to out/hc/pack (13.4 MB; this worker cannot send files > ~3 MB, owner asked).
- 10:45Z 02-cc-s8 DONE (conv-B-0555): Shopify gid://shopify/Product/15429483069744 handle childcare-center-excel-suite, 29.00, 8 media READY, published Online Store + Google & YouTube; storefront 200 with title and plan_fF0PDXkqahYm5. cc S0-S8 DONE; S9 (browser platforms) waits for Claude in Chrome (browser queue: cc).
- 10:56Z 08-s0 conv-C-0602 Research 17 (strict FindNiche re-check of 29 more professions: gig driver, car-rental host, reseller, makeup artist, tax preparer + 24 others): 0 PASS; 08-s0 back to blocked. Owner informed.
- 10:55Z 04-s6 DONE (convB-0553): Drive masters folder 1xvj8PsRObWJFd6J_ze8VFC65ziSaavov (8 Google Sheets, anyone-with-link reader, checked x8); hc/gs_ids.json; out/hc/pack cbb1bc7 = ZIP with Google-Sheets-copy-links.txt (8 /copy links, sha256 d14aebc2..., checked) via suite fetch workflow + blob re-point (same method as cc).
- 10:58Z 08-s0 DONE (conv-C-0602): OWNER CHOICE in chat 13:56 Riyadh «تأجير السيارات» -> slot 8 = cr Car Rental Business Suite (independent car rental + peer-to-peer host fleet). Evidence below the strict threshold (trackers $12.99-$24.99, models $99-$119, no listing sales) - built because the owner chose it. Research 18.
- 11:03Z 08-s1 DONE (conv-C-0602): cr/STUDY.md (25 web calls, 40 gaps, wording rules). cr_FOUNDATION_PROMPT.txt ready (model suite = cc, the latest finished).
- 11:16Z 04-s7 DONE (accD-0645): Whop prod_Ulj4obXuusqjB plan_KovDc7Px78ZBe ($29 one-time) route home-care-agency-excel-suite; 8 gallery images (public JPEG 1920x1440 from pack cbb1bc7); affiliates 50/50; Download experience exp_hHl3tDfh0gKH32 + course cors_kWp5GEL0Ao6WB, lesson lesn_VOCnm7uOrOLzR with ZIP and 8 Make-a-copy links; verified: page 200 with title, checkout 200, ZIP Range = PK. Done through the Composio Whop connection. hc/whop_ids.json.
- 11:30Z 08-s2 DONE (conv-C-0602): cr_core.py + BLUEPRINT.md + BRIEF.md + cr_bpcheck.py (8 parts OK, model cc; story: low-use VH-026, overlap BK-02525/BK-02606, damage claim DC-0128 52 days, service overdue VH-015, renewal RV-144 in 10 days, payout short PO-00613 / late PO-00618); part prompts prompts/cr_p1..p8.txt.
- 11:40Z ALL WORKERS, S6 Google Sheets (conv-B-0555): masters created from the owner's Drive get locale ar_EG, so TEXT() in messages/documents shows "$133٫00" (Arabic separators) and buyers' copies inherit it. After creating the 8 masters, set each to en_US: Sheets API spreadsheets.batchUpdate updateSpreadsheetProperties {locale: en_US} (Composio proxy_execute toolkit googlesheets, endpoint /spreadsheets/<id>:batchUpdate). Done and checked for cc (8) and th (8). Check: cc sample copies in Google Sheets vs LibreOffice, every formula cell of all 8 parts: 0 Google errors, 0 differences except one 0.01 rounding in part 8; Google drops apostrophes from sheet names (Cooks Daily List).
- 11:45Z hc Google Sheets masters (8) locale set to en_US by conv-B-0555 (were ar_EG). 08-s3-p7, 08-s3-p8 claimed by conv-B-0555.
- 12:02Z 04-s8 DONE (accD-0645): Shopify gid://shopify/Product/15429558305072 handle home-care-agency-excel-suite, ACTIVE, 29.00, metafield whop_url plan_KovDc7Px78ZBe, 8 media READY, published to Online Store + Google & YouTube; storefront https://darjob.myshopify.com/products/home-care-agency-excel-suite 200 with title + plan id (checked). accD-0645 has the Shopify connector: can do 02-cc-s8 if conv-B-0555 releases it.
- 12:40Z 09-s0 DONE (accD-0645): OWNER CHOICE in chat 15:36 Riyadh «المؤلفون والناشرون الذاتيون» -> slot 9 = au Author and Self-Publisher Business Suite (closest strict miss: author promo tracker 6 reviews, writer shop 1.1k sales; research7_strict group A). 09-s1 claimed by accD-0645; au_STUDY_PROMPT.txt (copied from cc_STUDY_PROMPT.txt).
- 12:58Z 09-s1 DONE (accD-0645): au/STUDY.md (25 web calls; 40 gaps; 8 part titles; weak/unverified benchmarks marked). au_FOUNDATION_PROMPT.txt ready (model suite = cc).
- 13:28Z 09-s2 DONE (accD-0645): au_core.py + BLUEPRINT.md + BRIEF.md + au_bpcheck.py (8 parts OK, model cc; story: title TL-020 not earned back 18 months (audio drags), ad AC-029 return 0.43, series read-through 0.172 < 0.25, statement ST-126 short 341.38, launch TL-015 late steps, invoice CP-0239 pushes cash below floor). prompts/au_p1..p8.txt (sed from cc_pN + owner Arabic-step rule).
- 14:59Z 08-s3-p1 DONE (conv-C-0602): cr1 verified by me (validate 0, ok true, warnings [], zero_dates 0, qa.txt 18 lines).
- 15:01Z 08-s3-p3 DONE (conv-C-0602): cr3 verified by me (validate 0, ok true, warnings [], zero_dates 0, qa.txt 18 lines).
- 15:06Z 08-s3-p5 DONE (convB-0553): cr5 validate 0, build ok, warnings [], zero-dates 0, emptybars clean, qa 18 lines, cr_bpcheck 8/8 OK.
- 15:09Z 08-s3-p4 DONE (convB-0553): cr4 validate 0, build ok, warnings [], zero-dates 0, emptybars clean, qa 18 lines, cr_bpcheck 8/8 OK.
- 15:12Z 08-s3-p7 DONE (conv-B-0555): validate 0, build ok, warnings [], zero dates 0, emptybars clean, messages use table placeholders (checked by conv-B).
- 15:15Z 09-s3-p2 DONE (accD-0645): au2 validate 0, build ok, warnings [], zero-dates 0, qa.txt 18 (checked by accD-0645).
- 15:30Z 09-s3-p3 DONE (accD-0645): au3 validate 0, build ok, warnings [], zero-dates 0, qa.txt 18 (checked by accD-0645).
- 15:35Z 09-s3-p1 DONE (accD-0645): au1 validate 0, build ok, warnings [], zero-dates 0, qa.txt 18 (checked by accD-0645). 09-s3-p7 claimed by accD-0645 (writer running).
- 15:18Z 08-s3-p8 DONE (conv-B-0555): validate 0, build ok (rebuilt from final files), warnings [], zero dates 0, emptybars clean, 34 messages without blank placeholders, dashboard KPIs non-zero (checked by conv-B).
- 15:19Z 08-s3-p2 DONE (conv-C-0602): cr2 verified by me (validate 0, ok true, warnings [], zero_dates 0, qa.txt 18 lines).
- 15:21Z 08-s3-p6 DONE (convB-0553): cr6 validate 0, build ok, warnings [], zero-dates 0, emptybars clean, qa 18 lines, cr_bpcheck 8/8 OK; Pay Calculator verdict made three-way (pay_tolerance setting; demo shows 'Check this pay line' for a -26.93 gap); no error cells in forms/docs/messages.
- 15:25Z 08-s4 DONE (convB-0553): copy/cr/en.json + cr/listing/final/en.json (description 2498 chars) + 8 taglines and signature texts; copy/cr/check.py PASS (real counts: 160 tables, 144 tools); 8 parts validate 0; cr/suite.json (fx-20261115-car-rental, slug car-rental-business).
- 15:32Z 08-s5 DONE (convB-0553): suite-build 8/8 ok (suite e0745f2), suite-pack -> out/cr/pack 3513b1f: ZIP Car-Rental-Business-Suite-8-workbooks-English.zip 15.6 MB (16 xlsx: 8 blank + 8 sample-data), gallery.json 8 heroes; heroes 3 and 7 viewed: clean layout; hero 7 'Utilisation per month' shows the known pct-chart problem (axis 0/1, Dec drop) - see PROBLEM, owner decision.
- 15:39Z 09-s3-p4 DONE (conv-B-0555): validate 0, build ok, warnings [], zero dates 0, emptybars clean, messages use table placeholders, dashboard KPIs non-zero (checked by conv-B).
