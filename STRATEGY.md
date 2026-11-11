# Dar — strategy for speed, quality and Excel files that really work (the owner, 2026-11-09)

The owner: «كل 3 ساعات يجب أن ينتج منتج مهني متخصص واحد على الأقل … استراتيجية تضمن السرعة … ترفع الجودة … تتأكد أن ملفات
اكسل تعمل فعلًا بلا أي أخطاء». Every worker (Claude's deep review, fxverify, Dar's teams) follows this file. One Dar release a day:
take the first item below that is not live yet. Check the live version before any release.

## 0. The first Excel-rules check of the two kits on sale (2026-11-09, fx/xlcheck/audit.json)
- Corrected: the check first flagged NETWORKDAYS.INTL (sheet Leave, 32 workbooks) as needing `_xlfn.` — wrong. It is a
  standard function, written without the prefix (checked against the standard's function list and LibreOffice: with the prefix
  LibreOffice shows #NAME?). With the corrected rule both kits have 0 Excel problems. Nothing was changed in the live files.
- Real but minor: about 25 list words left in English — Hindi (months, Yes, Cash, New in the Developer kit; End, Cash in PRO),
  Urdu (End, Cash, New), Russian (New), Chinese (Net). Not worth replacing live files on three platforms now (the Gumroad connector
  cannot remove the old file, buyers would see two ZIPs): fix them with the kits' next update, or when the owner asks.
- Lesson: a new check is confirmed on one real case (LibreOffice + the standard's function list) before a finding goes to the owner.
- The language check now ignores a text that every language keeps (helper-column keys like `dig`, codes like INV-001, USD).

## 0b. OmniRoute gateway (the owner, 2026-11-09: «أضف OmniRoute إلى منظومة دار فورًا»)
- Installed 2026-11-09 04:45 UTC on Dar's Hostinger account as the Node.js site **https://ai.dar.ink** (OmniRoute 3.8.53, Node 24,
  app archive omniroute-dar.zip, entry server.mjs, data in /home/u791571885/omniroute-data). Checked: /api/health 200; /v1/* refuse
  requests without a key (REQUIRE_API_KEY=true); dashboard login works. Secrets live only in the site's environment variables.
- Tested 2026-11-09 04:55 UTC with Dar's key: WITHOUT any account, the DuckDuckGo free-chat models answer (ddgw/gpt-5.4-mini,
  ddgw/gpt-5.6-luna, ddgw/claude-haiku-4-5, ddgw/mistral-small-2603, ddgw/tinfoil/gpt-oss-120b, ddgw/tinfoil/gemma4-31b). The
  `auto/*` combos fail (they try cfp first: Cloudflare Playground needs Chromium on the server). dva/cxa/aug/zc (Claude Opus/Fable,
  GPT-6, Sonnet names) need those companies' CLIs installed and logged in (subscriptions) — 503/502 here. unc closed.
  These are small models: a backup when Dar's own providers rest, not a quality gain; DuckDuckGo may limit the server's IP.
- **Next Dar release (not the same UTC day as another release):** add «omniroute» to Dar's AI router as an OpenAI-compatible
  provider (base https://ai.dar.ink/v1, models: the ddgw list above, strongest first), AFTER Dar's own providers, used only when
  they are resting; Dar's quality gates still decide. Its key for Dar is in the owner's Drive file «OmniRoute – مفتاح دار (سري).txt»: read it once, give it to the installer
  on the command line (never in the repo or a log), then trash that Drive file. Enable it only if a test call through it answers
  (at least one provider connected); otherwise leave it disabled and say so.

## Measures (fx/status.json, written by fxverify every hour)
- Target: 8 complete specialised suites in 24 h (`complete_last_24h` / `target_per_day`).
- 3-hour alert: now minus the later of `last_complete_at` and `counter_since` ≥ 3 h (the watcher computes it and says it first).
- Also watch: dropped share (`parts.dropped` / all parts), suites in progress, failed files, `excel_problems`.

## 1. Speed — most of the delay is inside Dar
1. **Stop the drops.** 165 of 189 files were dropped (2026-11-09). Find the causes with fxdiag3/fxdiag7, count them, fix the
   biggest first. A dropped file throws away a whole design cycle; a fixable error must go back for repair, never be dropped.
2. **Finish before starting.** At most 3 suites in progress; a new suite starts only when one is complete. (71 suites started,
   10 in progress for 1–2 days, 0 complete in 24 h: the work is spread too thin.)
3. **Repair loop.** A failed file goes back to the architect with fxverify's exact errors, at most 2 repairs, then a lesson.
4. **API budget.** `fx_anth_cap` 80 → 200 (release p3414); spend it on finishing open suites first, new research last.
5. **GitHub (done 2026-11-09).** fxverify runs every hour and skips LibreOffice when nothing is ready, so a ready suite is
   built within the hour.

## 2. Quality — a gate at every step, and every failure becomes a lesson
1. **Research gate.** For each profession, a must-have list (sheets, documents, rules, KPIs, local practice) taken from at least
   3 real competing templates and professional sources, plus at least one useful thing the best competitor lacks.
2. **Critic gate.** Dar's critic scores the spec against that list as the toughest buyer of the profession; below the bar it
   goes back to the architect with the missing items.
3. **Build gate (GitHub, free).** verify.py (LibreOffice) and xlcheck.py (Excel rules) — section 3.
4. **Language gate.** The title names the SAME profession in all 15 languages (p3414 fidelity check); no English left in
   another language (xlcheck «language» warnings must be 0 for ar fa ur ru hi zh); right-to-left for ar fa ur.
5. **Picture gate.** One contact sheet per language, read; anything cut, empty, generic, untranslated or from another product
   fails.
6. **Claude's review.** Arabic, English and one rotating language read in full, as the toughest buyer; then deliver.
Every failure goes back to Dar as a lesson so the same mistake is not made twice (and is written in the Drive status file).

## 2b. Depth gate (2026-11-09) — «لا يجب أن تكرر المنظومة عدم الاتقان هذا»
A Photographer pack passed every earlier gate and still shipped thin: no profession-specific services, 12 near-identical demo rows,
pictures that repeated one dashboard, picture texts in English inside 14 languages. "Ready" meant "valid", not "specialised".
- **engine/depth.py** (called by validate.validate, so the architect gets its messages through the normal repair loop): ≥6 signature
  services (each with a `where` sheet), ≥3 competitors, ≥2 tools, ≥3 messages, ≥1 document, ≥1 checklist; every table with 4+
  columns ≥12 demo rows, two tables ≥24, one date column spanning ≥270 days; list columns use ≥3 values; money columns not
  near-identical; unique ids; month columns hold the 1st of each month; no underscore in sheet/column names; every text the
  pictures print (headline, tagline, dashboard title, signature name + why) translated in all 14 languages.
- **runtime/verifier.py gate_parts()**: every ready file is judged the moment it is ready (not when its whole suite is), first
  validate+depth, then one strict build of the file alone (max 2 per run). A failure is written to the manifest as `failed` with
  the exact errors and `spec_sha` — the same path as a failed suite build — and recorded in `fx/gate.json`. `--plan` counts
  unjudged ready files so the hourly run wakes for them.
- Proof: the old Photographer files fail (23 and 18 messages); the rebuilt ones pass.
**For Dar's next release (after 00:00 UTC 2026-11-10, one release per day):** put the same numbers into the architect and critic
prompts so a file is designed deep the first time instead of repaired afterwards — SPEC v1.1 services are mandatory, demo ≥12
rows (24+ in main tables) spread over twelve months with 1st-of-month month columns, picture texts in `i18n`; critic fails any
spec that depth.py would fail; research must name ≥3 competitors with what each lacks.

## 3. Excel files that really work — three independent checks
1. **LibreOffice** (verify.py, existing): every workbook in 15 languages + the demo recalculated; zero formula errors; demo
   numbers equal an independent recalculation; charts, gauges and KPIs show real values; no #### columns.
2. **Excel rules** (runtime/xlcheck.py, 2026-11-09): what Excel rejects and LibreOffice accepts — `_xlfn.` prefixes, text
   constants and in-cell lists over 255 characters, formulas over 8192 characters or 64 levels, #REF!, sheet names, texts over
   32767, saved values / fullCalcOnLoad, right-to-left, English left in other languages. Runs on every built ZIP →
   `fx/xlcheck/<suite>.json`; `excel_problems` in status.json. **A suite with Excel problems is not delivered** until the cause
   is fixed in the engine or in Dar's architect rules.
3. **Products already on sale.** fxverify with `audit_urls` (workflow_dispatch) checks published ZIPs the same way →
   `fx/xlcheck/audit.json`. Re-check after any change to a live product.
Next, one at a time and tested before it ships:
- Check whether Excel's Protected View shows the demo empty (formulas without saved values). If it does, ship the English demo
  with the values LibreOffice computed, so the buyer sees numbers before «Enable Editing».
- After a week of runs with no false problem, make xlcheck problems fail the build (FX_STRICT) instead of only blocking delivery.
- MAXIFS / MINIFS / TEXTJOIN need Excel 2019 or later: say so in the listing and README, or replace them where simple.
