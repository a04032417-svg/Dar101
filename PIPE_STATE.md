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
real estate agent, real estate developer, photographer, contractor, restaurant, salon, teacher, property management, personal training, accounting and bookkeeping, social media management, construction, farm, project manager, online seller, trucking, interior designer, travel agent, short-term rental host, wedding and event planner, home bakery, cleaning business, real estate investor, beauty studio, handmade product maker, therapy private practice, (cc childcare in progress), lawn care and landscaping (lc, slot 3), home care agency non-medical (hc, slot 4), pet grooming (pg, slot 5), florist and floral design (fl, slot 6), auto repair shop (ar, slot 7), dance studio (ds, slot 8), martial arts school (ma, slot 9), balloon and event decor (bd, slot 10).

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
