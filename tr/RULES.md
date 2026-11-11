# Translating a Dar Templates suite (the owner's quality bar)

The owner (Arabic speaker, sells worldwide) rejected earlier translations: «سوء الترجمة … لا تجعل أي جهة تكرر ذات الخطأ», «لماذا موظفة وليس موظف»,
«وش ايجار الكرسي؟! لم اسمع بها». Every language must read as if a native professional in that field wrote it.

## Input / output
- Input: /home/claude/work/pm/strings.json = list of {"en": "...", "where": "...", "max": n or null, "kind": "sheet|label|sentence|message|document|list|setting|title"}.
- Output for language L: /home/claude/work/pm/i18n/<L>.json = {"<en>": "<translation>", ...} covering EVERY "en" exactly (same keys, no extras).
- Also write /home/claude/work/pm/i18n/<L>.glossary.json first: the 40–60 key terms of property management in L (rent roll, tenant, landlord/owner,
  lease, deposit, arrears, overdue, late fee, renewal, vacancy, occupancy, unit, building, work order, vendor, inspection, make-ready, service charge,
  management fee, payout, statement, reconciliation, budget, yield, cap rate, net operating income, comparables, asking rent, achieved rent, days on market,
  supply, demand, booking, check-in, check-out, nightly rate, occupancy, channel, cleaning, lead, proposal, contract, staff member, task…), then use them
  consistently in every string.

## Rules
1. Placeholders stay exactly as written and in a natural position: {name}, {amount}, {col:leases.end}, {set:grace}, {today}. Never translate or drop them.
2. Sheet names ("kind": "sheet"): at most 31 characters, none of [ ] : * ? / \ , unique within the language. Short and clear.
3. "max" given → never longer than that many characters (labels of 30, titles, tags of 20…).
4. Words for people are neutral or the language's standard generic form: Arabic «موظف» «المستأجر» «المالك» «العميل» (never the feminine form unless the
   English says so); French «locataire», «propriétaire», «membre de l'équipe»; Spanish «inquilino», «propietario»… no gendered job titles where a neutral
   one exists.
5. Use the standard, widely understood professional term of the language — not a literal word-for-word rendering, not a rare regional word, not an
   invented phrase. If two terms are common, pick the one used across the most countries of that language.
6. Native script only: Arabic, Persian and Urdu in their own script (no Latin transliteration); Hindi in Devanagari; Chinese in Simplified characters.
   Keep only these in Latin script: WhatsApp, Excel, LibreOffice, Airbnb, Booking.com, Vrbo, IBAN, VAT if it is the local usage, m², ID codes.
7. Labels and titles: concise, sentence case where the language uses it, no full stop. Sentences, messages and documents: natural, polite, professional.
   Messages are WhatsApp texts to tenants, owners, guests or staff: warm and clear.
8. Never write the word for "compatible", never an Excel version number, never invent facts.
9. List values (kind "list") are drop-down choices: short nouns or states, consistent with each other.
10. Numbers, %, m², dates and codes inside strings stay as they are.
11. Before writing the file, check: every key present, every placeholder kept, every sheet name ≤31 and unique, every "max" respected, no English left
    (except rule 6), no transliteration. Then report the counts.
