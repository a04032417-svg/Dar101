# The 6-hour run — Claude's half of «مصنع القوالب»

Dar (dar.ink, 3.34.0+) designs suites of Excel files without a stop. Every 6 hours a Claude session takes what is ready, builds it, checks
it, publishes it, and tells the owner in Arabic, briefly, what is verified and what is not. Use as few model turns as possible: the steps
below are scripted; read only what a step needs.

## 0. Setup (fresh container)
```
git clone -q -b fx https://github.com/a04032417-svg/Dar101 /home/claude/fx && cd /home/claude/fx
```
The engine needs LibreOffice (present) and the xlsx skill's recalc.py (found by engine/common.py; set FX_RECALC if not).

## 0b. The verification worker (since Dar 3.34.1) does steps 1–4 by itself
GitHub Actions `fxverify` on Dar101 main runs every 2 hours (and on demand): it reads Dar's feed `https://dar.ink/fxv/6c5b0240f916684723f4/`
(each spec encrypted for its key, the secret FX_VERIFY_KEY), builds and verifies every ready suite strictly (FX_STRICT=1) and pushes the
result to branch fx. So a 6-hour run normally starts at step 3 with what is already `built` in `fx/manifest.json`: look at it, publish,
report. Steps 1–2 below remain the manual way when the worker is down.

## 1. What Dar prepared (read-only, Hostinger connector)
- `hosting_files_website-content` username `u791571885`, domain `dar.ink`, path `.dar/fx/out/index.json` (max_lines 5000).
  It lists `items` (each file: id, status ready/published/failed) and `suites` (key, profession, parts, `listing` path when the
  suite's listing and its translations are done) and carries Dar's public key (`pubkey_pem`).
- A suite is ready to build when its `listing` is set and its key is not already `built` in `fx/manifest.json` here.
- For each such suite read `.dar/fx/out/<key>/suite.json` and every part's `.dar/fx/out/<id>/spec.json` (pages of 5000 lines: pass
  `from_line` 0, 5000, 10000 … until `total_lines`; save each result file). Then:
  `python3 runtime/fx.py spec work/<id>.json <saved pages…>` per part, `python3 runtime/fx.py pubkey work/pub.pem <index.json saved>`.

## 2. Build, check, package
`python3 runtime/fx.py suite work/<key>.suite.json work/<key> . work/<id1>.json work/<id2>.json …` (copy pub.pem into work/<key>/).
Every language of every file is built, recalculated in LibreOffice and verified (no formula error, demo totals equal an independent
recalculation); pictures come from the recalculated English demo. A file that fails is written back as `failed` with its errors —
Dar's architect repairs it (twice at most). Never publish a suite with a failed file in it unless the remaining files stand alone.

## 3. Look at it
Open 2–3 of the pictures (Read) and one workbook's dashboard values (openpyxl data_only on the recalculated demo). Anything that looks
generic, broken or empty: mark the suite failed with the reason instead of publishing.

## 4. Push for Dar
`python3 runtime/fx.py push . "fx: <suite names>"` — one orphan commit on branch fx (encrypted packages and pictures only).
Dar takes the package in within ~5 minutes and serves it only to buyers it can verify.

## 5. Publish (price 29 USD (the owner, 2026-11-07), all platforms, the suite's listing in its 15 languages from suite.json)
- Whop (account «Dar»): product + one-time 29 USD plan; delivery link `https://dar.ink/dar-sync.php?fxd=<slug of the key part>`.
- Shopify «Dar Templates»: product with the pictures, Buy now → the Whop checkout; translations of title/description.
- Gumroad: product 29 USD with the ZIP (a temporary public copy on a throw-away Dar101 branch, deleted right after Gumroad took it).
- Payhip and E2C through Composio; Etsy through AnythingMCP once Etsy approved the app; others as the owner adds them.
- Every language its own listing (the owner, 2026-11-07: «كل لغة يفترض ان يكون لها قائمة خاصة في كل منصات النشر فيها لكي لا يضيع الزبون»), with
  its own pictures (engine v1.4, 2026-11-08: «اجعله ينشئ صور بكل اللغات»): the manifest's `images_i18n[<lang>]` (fx/<key>/<lang>/…) are that
  language's pictures — the product's words from its i18n, the fixed phrases from engine/fixed_pic.json (written by Dar's copy team).
  English stays in `images`. Never put English pictures on another language's listing.
Record links: `python3 runtime/fx.py links . <key> <whop_product> <whop_plan> <whop_checkout> <shopify_url>` then push again.

## 6. Report
One short message in Arabic: suites published (names, platforms, links), files failed and why, what was not verified.
Never claim a check that did not run.
