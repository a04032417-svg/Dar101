# Dar Template Factory — spec contract v1 (`fx: 1`)

One JSON document describes one Excel product. Dar's AI teams write it (research → architect → critic → copy → translate);
Claude's builder (`/home/claude/fx/engine`) turns it into 15 language workbooks + an English demo copy, checks them and
renders the listing pictures. Both sides validate against this file. Anything not described here is rejected.

## Top level

```json
{
  "fx": 1,
  "id": "fx-20261107-1200-dental-clinic",          // unique, [a-z0-9-], <= 60
  "slug": "dental-clinic-manager",                 // url slug, [a-z0-9-], <= 50
  "profession": "Dental clinic",                   // English, who it is for
  "name": "Dental Clinic Manager",                 // product name, English, <= 40
  "tagline": "Patients, visits, treatments and money in one Excel file", // <= 80
  "price_usd": 20,                                 // 9..49
  "colors": {"primary": "#1F3A68", "accent": "#E9B949"},
  "settings": [Setting],                           // 3..20
  "lists":    [List],                              // 1..20
  "tables":   [Table],                             // 3..14 data sheets
  "dashboard": Dashboard,
  "forms":    [Form],                              // 0..4 printable one-record sheets
  "guide":    ["step text", "..."],                // 5..20 short steps, plain English
  "listing":  Listing,
  "i18n":     {"ar": {"<English text>": "<translation>"}, "fr": {...}, ...}   // 14 languages, see below
}
```

Languages: en (source) + ar fr es de it pt tr nl ru fa ur hi zh id. ar, fa, ur are right-to-left.

## Setting
`{"key":"vat","label":"VAT on invoices %","type":"pct|money|int|num|text|date|list","default":0.15,"list":"<list key if type=list>"}`
Shown on the Start sheet; formulas use them with `{set:vat}`.

## List
`{"key":"status","label":"Status","values":[{"key":"active","label":"Active"},{"key":"lost","label":"Lost"}]}` (2..30 values)
A Lists sheet holds every list; data columns of type `list` get a drop-down. Formulas never write a label as text: they
use `{list:status.active}`, which the builder turns into a reference to that label's cell — so every language works.

## Table (one data sheet)
```json
{"key":"visits","sheet":"Visits","title":"Visits","hint":"One row per visit ...","rows":1000,
 "columns":[Column], "alerts":[Alert], "demo":[{"<col key>": value, ...}]}
```
- `key` [a-z][a-z0-9_]{1,20}; `sheet` <= 31 chars, unique, none of `[]:*?/\`.
- `rows` = empty input rows prepared (50..3000).
- demo: 5..60 realistic rows (only input columns; dates as "YYYY-MM-DD", or relative "today-12" / "today+30"; a `list` column holds
  the value's KEY — never its label, the builder shows the label in each language).

### Column
```json
{"key":"amount","label":"Amount","type":"text|int|num|money|pct|date|time|list|ref|bool|calc|link","width":14,
 "list":"status",                 // type=list
 "ref":"patients.name",           // type=ref: drop-down of the values of another table's column
 "format":"int|num|money|pct|date|time|text|hours", // type=calc: how to show the result
 "formula":"...",                 // type=calc (DSL below); computed for every prepared row, blank when the row is blank
 "required":true,                 // the row counts as filled when its first required column is filled
 "visual":"bar|up|down"}          // (v1.3) number columns only: a data bar, or a colour scale green-when-high / green-when-low
```
At least one input column must be `required`. A calc column must only refer to its own row with `{col:x}` and to whole
columns with `{range:t.c}`.

### Alert (conditional colour)
`{"column":"due","when":"> 0" | "< {today}" | "= {list:status.lost}" | "<= {set:warn_days}","style":"bad|warn|good"}`

## Dashboard
```json
{"title":"Dashboard",
 "kpis":[{"label":"Active patients","formula":"COUNTIFS({range:patients.status},{list:status.active})","format":"int"}],  // 6..24
 "monthly":{"title":"By month","date":"payments.date","series":[{"label":"Revenue","sum":"payments.amount"},
                                                                  {"label":"Expenses","sum":"expenses.amount"}]},          // 1..4 series, 12 months of the chosen year
 "breakdowns":[{"title":"Revenue by treatment","by":"visits.treatment","value":"visits.price","agg":"sum|count"}]}           // 0..4 tables, one row per list value / ref value
```
The builder adds a year selector, a bar chart of the monthly table and status colours.

## Form (printable sheet built around one record)
```json
{"key":"invoice","sheet":"Invoice","title":"Invoice","pick":"visits.id",            // the user types/chooses a value of this column
 "fields":[{"label":"Patient","value":"visits.patient"}, {"label":"Total","formula":"...","format":"money"}],
 "lines":{"from":"visit_items","match":"visit_items.visit","columns":["item","qty","price","total"],"max":20}}  // optional
```
`value` = the chosen record's value in that column; `formula` may use `{pick}` (the chosen value) and `{range:...}`.

## Formula DSL
Plain Excel formulas (English function names, comma separators) with these tokens only:
- `{col:k}` this row's cell of column k (same table) · `{range:t.c}` the whole prepared range of table t column c
- `{set:k}` a setting · `{list:l.v}` a list value's label · `{today}` TODAY() · `{pick}` (forms only)
Allowed functions: SUM SUMIFS COUNTIFS COUNTA COUNT AVERAGEIFS AVERAGE MIN MAX MAXIFS MINIFS IF IFERROR AND OR NOT
INDEX MATCH ROUND ROUNDUP ROUNDDOWN ABS DATE YEAR MONTH DAY EDATE EOMONTH TODAY NETWORKDAYS DATEDIF TEXTJOIN LEFT RIGHT
MID LEN TRIM UPPER LOWER SUMPRODUCT ISNUMBER ISBLANK VALUE MOD INT HYPERLINK. No VLOOKUP/XLOOKUP/FILTER/SORT/UNIQUE/
INDIRECT/OFFSET/LET/LAMBDA, no text literals in another language, no hard-coded row numbers.

## Listing
```json
{"title":"<= 140 chars, Etsy style","headline":"<= 80","tags":["13 tags, each <= 20 chars"],
 "description":"plain text, 900..2500 chars, only claims the spec really contains",
 "features":["6..12 short bullet lines"]}
```

## i18n
For every language: a map from each English string used anywhere (sheet names, titles, hints, labels, list labels,
settings, KPI labels, guide steps, form labels, the builder's own fixed words listed in `engine/fixed_en.json`) to its
translation. Sheet names must stay valid (<= 31 chars, unique, no `[]:*?/\`). Missing strings fail the build.

## Exchange between Dar and Claude
- Dar writes every approved spec to `<data dir>/fx/out/<id>/spec.json` (pretty JSON, one value per line) and keeps
  `<data dir>/fx/out/index.json` = `{"pubkey":"fx/out/pubkey.pem","items":[{"id","slug","name","status":"ready|built|published|failed","at"}]}`.
  `<data dir>` is `.dar` under the site root (never served on the web). Claude reads these files through the Hostinger
  file-read API (paths relative to the site root, e.g. `.dar/fx/out/index.json`).
- Dar's RSA-3072 key pair is made once; the public key is `<data dir>/fx/out/pubkey.pem`.
- Claude publishes results on the public GitHub repo `a04032417-svg/Dar101`, branch `fx`:
  `fx/manifest.json` = `{"items":[{"id","status":"built|failed","pkg":"fx/<id>/pkg.fxp","sha256":"<of pkg.fxp>",
   "images":["fx/<id>/01-hero.png", ...],"whop":{"product":"prod_x","plan":"plan_x","checkout":"https://whop.com/checkout/plan_x"},
   "shopify":"<product url>","error":"<why it failed, for the architect to repair>","at":"<ISO time>"}]}`.
  Dar polls `https://raw.githubusercontent.com/a04032417-svg/Dar101/fx/fx/manifest.json`.

## Package format (`pkg.fxp`) — the buyer's ZIP, encrypted so the public repo never exposes it
`"FXP1"` (4 bytes) · u16 big-endian length N · N bytes = the 32-byte AES key wrapped with RSA-OAEP (SHA-1, MGF1-SHA-1 —
what PHP's `openssl_private_decrypt(..., OPENSSL_PKCS1_OAEP_PADDING)` reads) · 12-byte IV · 16-byte GCM tag ·
ciphertext = AES-256-GCM(zip bytes), no associated data. Dar decrypts it to `<data dir>/fx/files/<id>.zip`.

## Delivery
The Whop product's `redirect_purchase_url` is `https://dar.ink/dar-sync.php?fxd=<slug>`. Dar records every Whop payment
of an fx plan (webhook) with the buyer's e-mail; the page gives the ZIP only to a buyer it can match (a Whop
payment/receipt/membership id in the address that Dar verifies with Whop's API, or the e-mail used at checkout).

## v1.1 — profession-specific services (the owner, 2026-11-07: «نماذج متخصصة لكل مهنة … وخدمات خاصة لها وليس نسخ لصق … تتفوق على المنافسين بمراحل»)
Every spec must be built around what ONLY that profession needs. Top-level additions (all optional in the schema, but
the critic rejects a spec whose services are generic):
```json
"signature": [{"name":"Recall planner","why":"patients due for 6-month check-ups never slip","where":"<sheet name>"}],   // 5..12, each specific to this profession
"competitors": [{"what":"typical Etsy dental template","lacks":"no recall planning, no insurance claims"}],                // 3..8, and how this beats them
"tools": [Tool],            // 0..6 calculators/planners specific to the profession
"messages": [Message],      // 0..20 ready WhatsApp/e-mail texts for this profession's real moments
"documents": [Document],    // 0..4 printable letters/contracts/reports filled from a record (like forms, free text with placeholders)
"checklists": [Checklist]   // 0..4 stage templates (e.g. a case, a project, an order) whose steps get due dates from a start date
```
### Tool (a calculator / planner sheet)
`{"key":"recipe_cost","sheet":"Recipe costing","title":"...","hint":"...",
  "inputs":[{"key":"portions","label":"Portions","type":"int|num|money|pct|date|list|text","default":10,"list":"<list>"}],
  "outputs":[{"label":"Cost per portion","formula":"...","format":"money"}],        // formulas use {in:key}, {set:}, {range:}, {list:}
  "grid":{"title":"Scenarios","rows":[{"label":"Price +10%","values":{"price":"=..."}}]}}   // optional what-if table`
### Message
`{"key":"recall","moment":"Recall due","text":"Hello {name}, ... {date} ...","table":"patients","phone":"patients.phone"}` →
a «Send on WhatsApp» link column is added to that table (wa.me with the text filled from the row; placeholders are that table's column keys).
### Document
`{"key":"treatment_consent","sheet":"Consent","title":"...","pick":"patients.id","paragraphs":["Text with {col:patients.name} …"],"sign":["Patient","Dentist"],"note":"sample wording …"}`
### Checklist
`{"key":"new_case","title":"New case","table":"cases","start":"cases.opened","steps":[{"label":"...","days":0},{"label":"...","days":7}]}` →
a sheet listing the steps for the case chosen, each with its due date from the start column and a done/late status.

Critic rubric (Dar side, out of 100): profession depth & signature services 30 · calculation depth/correctness 20 ·
beats named competitors 15 · dashboard & decisions 10 · usability/guide 10 · demo realism 10 · copy honesty 5.
Any score < 85, or fewer than 5 truly profession-specific signature services, sends it back to the architect.


## Charts sheet (v1.3, optional `insights`)
```json
"insights":{"filters":[{"label":"Agent","ref":"staff.name"},{"label":"Category","list":"category"}],
  "gauges":[{"title":"Collected of billed","num":AGG,"den":AGG}],
  "charts":[{"title":"Billed and collected by month","type":"column|bar|line|stacked|doughnut|pie|combo","by":"month | table.column",
             "series":[AGG + "label"],"line":1}]}
AGG = {"agg":"sum|count|avg","table":"t","value":"t.c (sum, avg)","date":"t.c (by month; and the year the buyer picks)",
       "where":[{"column":"c","op":"= <> > < >= <=","value":"{list:l.v} | {set:k} | {today} | number"}]}
```
A «Charts» sheet after the dashboard: the buyer picks the year and each filter in yellow cells; every gauge and chart redraws from
visible formula tables. Limits: filters 0..3, gauges 0..6, charts 1..16 — as many as the field needs. A chart grouped by a column has
every series on that column's table; doughnut/pie one series; combo 2..4 series and `line`. A gauge is a share (num of den, 0..1).
