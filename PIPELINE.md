# Dar Templates — autonomous pipeline: 10 new products (runbook for scheduled runs)

Goal set by the owner (2026-11-15): produce and publish 10 NEW profession suites by themselves, without waiting for him.
Product 1 = TH (Therapy Private Practice) DONE. Product 2 = CC (Home Daycare and Childcare Center) IN PROGRESS. Then 8 more.
State lives in PIPE_STATE.md (this branch). Read it first, update it at the end of every run.

## 0. Owner rules (binding, never break)
- EVERY message to the owner in ARABIC ONLY (final run summary included). Brief; separate «تم وتحققت منه» from «لم يتم / لم أتحقق». Never claim anything unverified.
- Minimal usage: sonnet (or haiku) for every agent, at most 3 agents at once, foreground agents (no polling loops), few large file writes, no re-reading big files. Stop the run after the budget below.
- English edition only for now, price 29 USD for new products (published older products stay as they are). 8 workbooks per product, 8 single big gallery images (one hero per part) — never a grid cover, never change the picture style.
- Profession study FIRST, built on REAL sales evidence (Etsy listing reviews / shop sales, Payhip/Gumroad pages), never search-interest data alone. Specialised professional products, far beyond competitors. Creativity and quality first.
- Excel + Google Sheets support (say "Excel & Google Sheets" in pictures/copy), dates follow regional format, currency symbol in one cell, formula cells locked (no password), coloured input cells, instructions on the first sheet, Business English terms, advanced formulas that work everywhere (never MAXIFS/MINIFS/TEXTJOIN/FILTER/XLOOKUP/LET/dynamic arrays, no macros).
- Never: the word "compatible", Excel version numbers, brand names except WhatsApp, Excel, LibreOffice, Google Sheets; law/agency/licence/program/standard names; medical claims; fake reviews/urgency.
- Money/accounts: no paid platforms or fees; never create accounts, enter passwords, API keys, payment/bank data or IDs; no CAPTCHA; no fabricated identities.
- Do NOT publish on Khamsat. Do NOT work on Buy Me a Coffee, Kit, Contra. Never e-mail Mais (owner ban; the address is in the owner memory, never write it here). No outreach from the owner's personal Gmail. No social-media linking. No mass scraping.
- This repo is PUBLIC: never commit personal data, owner e-mails, signed ZIP URLs or secrets. Contact address on products: service@dar.ink only.
- Never delete Hostinger crons fFL5aLOA8I, ZoeMVxGcZi, FZyifHInJo, jECgVbtoin. Do not edit the Shopify MAIN theme via API.
- Ask before adding anything the owner did not ask for (in a scheduled run: do not add it; note it in PIPE_STATE "ideas").
- Git commit messages end with: "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" and "Claude-Session: scheduled pipeline run".

## 1. Setup at the start of every run (fresh container)
```
cd /home/claude
[ -d work/.git ] || git clone -q --depth 1 -b pipeline https://github.com/a04032417-svg/Dar101 work
[ -d suite/.git ] || git clone -q --depth 1 -b suite https://github.com/a04032417-svg/Dar101 suite
[ -e d101 ] || ln -s /home/claude/suite /home/claude/d101      # engine = /home/claude/d101/engine, SPEC = /home/claude/d101/SPEC.md
git -C work config user.name a04032417-svg; git -C work config user.email a04032417-svg@users.noreply.github.com
git -C suite config user.name a04032417-svg; git -C suite config user.email a04032417-svg@users.noreply.github.com
python3 -c "import openpyxl, PIL" && which soffice   # LibreOffice is needed by run.py; install only if missing
```
Push errors "expected 'acknowledgments'" are harmless: verify with `git ls-remote origin <branch>`.
LOCK: PIPE_STATE.md line `LOCK:`. If it holds a time less than 150 minutes old, another run is working: exit with a one-line Arabic note. Otherwise write `LOCK: <UTC now>`, commit, push `pipeline`, then work. Clear it (`LOCK: none`) at the end.

## 2. Budget per run
At most ~100 minutes of work or 2 stages (whichever comes first), then save state (section 5). Leave the rest for the next run.

## 3. Stages of one product (prefix x = 2 letters, folder /home/claude/work/x/)
S0 RESEARCH (only when starting a new product): ~8-12 WebSearch/WebFetch calls for real sales evidence (Etsy listing review counts and shop sales, Payhip/Gumroad). Candidate list in PIPE_STATE "queue" (re-check, add better ones). Never repeat a profession already made (list in PIPE_STATE). Append the evidence to research6_20261115.md (new section) and record the decision in PIPE_STATE.
S1 STUDY: copy cc_STUDY_PROMPT.txt to x_STUDY_PROMPT.txt, adapt buyer/business/sections to the new profession, run ONE sonnet agent: "Read /home/claude/work/x_STUDY_PROMPT.txt and do exactly what it says." -> x/STUDY.md.
S2 FOUNDATION: copy cc_FOUNDATION_PROMPT.txt to x_FOUNDATION_PROMPT.txt (model suite = the latest finished one, e.g. /home/claude/work/cc/), adapt names/key ('fx-<yyyymmdd>-<slug>'), demo business, story rows, colors (pick a new professional pair). Run ONE sonnet agent. Check: `cd x && python3 x_bpcheck.py` all OK.
S3 PARTS: prompts = prompts/cc_pN.txt with cc->x (sed 's#/cc/#/x/#g; s#cc_core#x_core#g; s#cc\([0-9]\)#x\1#g'). Run parts 1+2(+3) as up to 3 parallel sonnet agents ("Read <prompt file> and do exactly what it says."), then the next ones. A part is done only if: validate 0 errors (FX_EDITION=en FX_LANGS=en), outN/result.json ok true and warnings [], zero_dates prints 0, outN/qa.txt exists. Check it yourself; re-run a writer on its own file if not clean.
S4 COPY: prompts/th_copy.txt adapted (th->x, real counts, names) -> copy/x/en.json + x/listing/final/en.json + picture texts in xN.en.json; re-validate all 8 (0 errors). Write x/suite.json like th/suite.json (key, slug, parts p1..p8, rev "1", name/headline/stats_note/inside_h1 in "en").
S5 CI BUILD + PACK (repo /home/claude/suite, branch suite):
```
mkdir -p build/x && echo "English edition (owner 2026-11-15)" > build/x/EN_ONLY
for i in 1..8: python3 -c "import json;json.dump(json.load(open('/home/claude/work/x/x$i.en.json')),open('build/x/p$i.json','w'),ensure_ascii=False,separators=(',',':'))"
git add build/x && git commit -m "x parts" && git push origin HEAD:suite        # starts suite-build -> branches out/x/p1..p8
bash /home/claude/work/tools/packwatch.sh x 8     # waits for 8 builds ok, pushes build/x/suite.json -> suite-pack -> branch out/x/pack
```
packwatch runs in the foreground (it sleeps 60 s per loop; budget ~25 min). Then check out/x/pack: ZIP + gallery.json (8 images images/en/1N-partN-01-hero.png). Look at 2 of the images (Read) for quality.
S6 GOOGLE SHEETS MASTERS: clone out/x/pack shallow, unzip the 8 blank *_EN.xlsx into /home/claude/work/x/gs/ (must be under /home/claude/work). Create a Drive folder "<Suite name> – Google Sheets masters" (or reuse) and upload each with mcp__Google_Drive__create_file: title "0N <part name>", contentMimeType application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, parentId <folder>, base64Content "sha256:<sha256 hex>:<absolute path>" (converts to a Google Sheet). Share each: mcp__Google_Drive__share_file permissionId "anyoneWithLink" role "reader"; verify with get_file_permissions. Write x/gs_ids.json [["01 - <ZIP folder name>", "<id>"], ...] and run `python3 tools/gs_links.py pack.zip new.zip x/gs_ids.json "<Suite name>"`; push the new ZIP over the old one on branch out/x/pack (same file name). If the Drive tools are missing or need an approval nobody gives: skip S6, note it, continue.
S7 WHOP (account biz_EPdES7EEpWl9qp, Courses app app_0vPZThfBpAwLo): one intent_id UUID per run. files_create x8 (visibility public, "<slug>-N.jpg") + x1 ZIP (private). PUT the bytes from the Composio workbench (mcp__composio__COMPOSIO_REMOTE_WORKBENCH; the shell cannot reach S3): download hero PNG N from https://raw.githubusercontent.com/a04032417-svg/Dar101/<pack commit>/images/en/<1(N-1)>-partN-01-hero.png, convert to JPEG 1920x1440 quality 88, PUT with Content-Type image/jpeg; ZIP from the same commit, PUT application/zip; print status codes. files_get until ready. products_create (title <=80 "<Suite name>: Excel & Google Sheets Templates", headline <=80 from copy, route "<slug>-excel-suite", description <=1500 chars built from copy/x/en.json (hook, what you can do, inside with real counts and pages, file format incl. Make a copy links, not for, guarantee), gallery 8 file ids, global+member affiliate enabled 50, visibility visible). variants_create one_time 29 usd, title "Full suite, one-time". experiences_create (Courses app, name "Download – <Suite name>") + experiences_attach + courses_create (gives lesson) + course-lessons_update (title "Download the 8 workbooks", markdown with 3 steps, the 8 Google Sheets /copy links, help line service@dar.ink + 14-day guarantee, attachments [ZIP file id]). Verify from the workbench: product page https://whop.com/dar-94b4/<route>/ 200 with title, checkout https://whop.com/checkout/<plan> 200, ZIP url Range bytes=0-3 gives PK.
S8 SHOPIFY: build x/shop_input.json like work/th/shop_input.json (productSet input: title, handle "<slug>-excel-suite", vendor "Dar Templates", status ACTIVE, productType "Digital download", descriptionHtml from copy/x/en.json with <strong> headings and <ul> lists, seo, 13 tags, one variant price "29.00" inventoryItem {requiresShipping false, tracked false}, metafield custom.whop_url = Whop checkout, files = the 8 public Whop image URLs). mcp__Shopify__graphql_mutation productSet(synchronous:true) then publishablePublish to gid://shopify/Publication/315639890224 (Online Store) and gid://shopify/Publication/317039280432 (Google & YouTube). Verify media READY and storefront https://darjob.myshopify.com/products/<handle> 200 with title + plan id (via workbench).
S9 BROWSER PLATFORMS (only if Claude in Chrome tools are connected; otherwise add the product to PIPE_STATE "browser queue" and move on): Payhip (payload suite branch pub/payhip/x.json like th.json, runner prompts/chr_runner17.js, price 29), Ko-fi, Gumroad (10 new products per day limit; English listing, 8 images, ZIP), eFM (English edition < 10 MB), Adpost ad, itch.io (project limit: see PIPE_STATE).
Then mark the product DONE in PIPE_STATE and start S0 of the next product (if budget remains).

## 4. Quality gates (never skip)
- Every count in copy/pictures = real counts from the built files. Pages = number of sheets across the 8 blank workbooks.
- No banned words (check like copy/th/check_th.py). Demo data realistic; story rows visible on dashboards.
- If something fails twice, record it in PIPE_STATE "problems" and continue with what can be done.

## 5. End of every run
Update PIPE_STATE.md (product table, stage, ids, verified facts, problems, browser queue, `LOCK: none`), `git add -A` in /home/claude/work (.gitignore keeps out*/ xlsx zip pycache out), commit, push `pipeline`; push suite-branch work too. Final message to the owner IN ARABIC, max 8 lines: what was done and verified, what is waiting, the next step. No English sentences.
