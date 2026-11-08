#!/usr/bin/env python3
# Dar 3.34.11 (2026-11-08, the owner: «نعم صلح الاثنين»): 1) the fields are ranked by what buyers really search too — Google's own
# monthly searches (Keyword Planner, read through the Google Ads account «Dar», United States, English) next to the marketplace evidence;
# 2) law reopened: a field dropped before 3.34.10's fixes (the formula repairs, the critic's extra rounds) was resting for reasons that
# no longer hold, so drops before this version no longer count; 3) quality: only strong models work, two critics of two providers approve, what is new
# is scored and required, a strong copy editor judges the listing, translations refused when English is left. usage: p3411.py <src dir> [--built ISO]
import sys, os, json, hashlib

SRC = sys.argv[1]; BUILT = sys.argv[sys.argv.index('--built') + 1] if '--built' in sys.argv else '2026-11-08T16:00:00+03:00'
OLDV, NEWV = '3.34.10', '3.34.11'
def rd(p): return open(os.path.join(SRC, p), 'rb').read().decode('utf8')
def wr(p, s): open(os.path.join(SRC, p), 'wb').write(s.encode('utf8'))
def sub1(s, old, new, what):
    n = s.count(old)
    if n != 1: sys.exit(f'PATCH FAIL {what}: found {n}x')
    return s.replace(old, new)

F = rd('dar-fx.php')
R = [
 # the migration: the searches read today, and the drops before this version no longer count
 ("    if (meta_get('fx_rank_v') === '2') { meta_set('fx_rank_v', '3'); fx_research_only(); } // v3.34.7\n",
  "    if (meta_get('fx_rank_v') === '2') { meta_set('fx_rank_v', '3'); fx_research_only(); } // v3.34.7\n"
  "    try { db()->exec('ALTER TABLE fx_rank ADD COLUMN search INTEGER NOT NULL DEFAULT -1'); } catch (Throwable $e) { /* (there already) */ } // v3.34.11: Google's monthly searches (-1: not read)\n"
  "    if (meta_get('fx_rank_v') === '3') { meta_set('fx_rank_v', '4'); fx_search_seed(); meta_set('fx_drop_epoch', (string)now_ms()); } // v3.34.11\n", 'migration'),
 # a drop before this version is not counted against a field
 ("    $drops = []; foreach (q('SELECT profession, stage, x FROM fx_items')->fetchAll() as $r) { $k = strtolower((string)$r['profession']); if ($r['stage'] !== 'dropped') { $used[$k] = 1; continue; }\n",
  "    $ep = (int)(meta_get('fx_drop_epoch') ?? 0); // v3.34.11 (the owner: «صلح الاثنين» — law reopened): the drops before 3.34.10's fixes no longer count\n"
  "    $drops = []; foreach (q('SELECT profession, stage, x, updated FROM fx_items')->fetchAll() as $r) { $k = strtolower((string)$r['profession']); if ($r['stage'] !== 'dropped') { $used[$k] = 1; continue; } if ((int)$r['updated'] < $ep) continue;\n", 'drop epoch'),
 # the panel shows the searches
 ("'why' => $r['why'], 'source' => (string)($r['src'] ?? '')], q('SELECT * FROM fx_rank ORDER BY score DESC LIMIT ' . $n)->fetchAll()); }",
  "'why' => $r['why'], 'source' => (string)($r['src'] ?? ''), 'google_month' => (int)($r['search'] ?? -1)], q('SELECT * FROM fx_rank ORDER BY score DESC LIMIT ' . $n)->fetchAll()); }", 'rank view'),
 # the market team reads the searches too
 ("        . \"- evidence: what you saw and where (the marketplace, the number of listings, the reviews or sales of the leaders, the search volume), with the address; empty when you could not read the web.\\n\"",
  "        . \"- evidence: what you saw and where (the marketplace, the number of listings, the reviews or sales of the leaders, the monthly searches for its templates on Google and on the marketplace), with the address; empty when you could not read the web.\\n\"", 'market prompt'),
]
for old, new, what in R: F = sub1(F, old, new, what)

# ---- 3) quality (the owner, 2026-11-08: «نعم ضيفها … ركز على الجودة وتخصيص ما يجب تخصيصه»)
R2 = [
 # a. every stage asks the strong models only; a small or weak one that answers anyway is refused (the file waits for a strong one)
 ("    if (!empty($o['avoid'])) $req['avoid'] = array_values($o['avoid']);\n",
  "    if (!empty($o['avoid'])) $req['avoid'] = array_values($o['avoid']);\n"
  "    if (empty($o['weak'])) { $req['strong'] = true; $req['strict'] = true; } // v3.34.11: the factory's work is never a small or weak model's\n", 'strict ask'),
 ("    $j = fx_json((string)($r['text'] ?? '')); $by = (string)($r['provider'] ?? '') . (($r['model'] ?? '') !== '' ? '/' . $r['model'] : '');\n",
  "    $j = fx_json((string)($r['text'] ?? '')); $by = (string)($r['provider'] ?? '') . (($r['model'] ?? '') !== '' ? '/' . $r['model'] : '');\n"
  "    if (empty($o['weak']) && !fx_strong((string)($r['provider'] ?? ''), (string)($r['model'] ?? ''))) return ['err' => 'weak model (' . $by . '): the factory waits for a strong one'];\n", 'strict check'),
 # a2. waiting for a strong model is not a failure: it never counts toward the six that drop a file (the owner: quality first, never a weak answer)
 ("function fx_back(array &$it, string $why): void { $it['fails']++;",
  "function fx_back(array &$it, string $why): void { if (preg_match('/ai_unavailable|weak model|waits for (?:a |the )?second|rate.?limit|quota|\\b429\\b|timed? ?out|no_time|no_ai|overloaded|\\b50[23]\\b/i', $why)) { $w = (int)($it['x']['waits'] ?? 0) + 1; $it['x']['waits'] = $w; $it['next_at'] = time() + min(3600, 300 * (2 ** min(4, $w - 1))); fx_note($it, $it['stage'], 'waits for a strong model: ' . $why); return; } // v3.34.11\n    $it['fails']++;", 'wait is not a failure'),
 # b. research: what no template of the field does yet
 ('"competitor_gaps":["what the usual templates for this field miss or get wrong"],',
  '"competitor_gaps":["what the usual templates for this field miss or get wrong"],"innovations":["3 to 6 things NO template for this field does today that its professionals would gladly pay for — what it does, which daily job it saves, why it is new (not a usual sheet)"],', 'research innovations'),
 ("foreach (['buyers', 'jobs', 'must_have_sheets', 'calculations', 'kpis'] as $k)",
  "foreach (['buyers', 'jobs', 'must_have_sheets', 'calculations', 'kpis', 'innovations'] as $k)", 'research needs innovations'),
 # c. the architect builds them
 ('        . "- a guide of short steps a non-technical buyer can follow.\\n"',
  '        . "- a guide of short steps a non-technical buyer can follow;\\n"\n'
  '        . "- the brief\'s innovations (or better ones), built for real in sheets, calculated columns, KPIs and forms: what no competitor\'s template for this field does — the reason to buy this one; and the field\'s own documents, rules and calculations, never a generic business file renamed.\\n"', 'architect innovations'),
 # d. the critic scores what is new, and approval needs two strong critics of two providers
 ("        . \"- dashboard and charts: KPIs, live charts and gauges that each answer a real question, filters the buyer picks (a person, a place, a project…) that redraw them, indicators on the decisive columns — far beyond the usual templates (20)\\n\"",
  "        . \"- dashboard and charts: KPIs, live charts and gauges that each answer a real question, filters the buyer picks (a person, a place, a project…) that redraw them, indicators on the decisive columns — far beyond the usual templates (15)\\n\"", 'rubric dashboard'),
 ('        . "- services only this field has (15)\\n- data model integrity',
  '        . "- services only this field has (15)\\n- innovation: what it does that no competitor\'s template for this field does, useful to its professionals every week (10)\\n- data model integrity', 'rubric innovation'),
 ('"signature_enough":true|false (are they enough for this field, as its best specialist would judge?),',
  '"signature_enough":true|false (are they enough for this field, as its best specialist would judge?),"innovations":["each thing this workbook does that the best competitor templates for this field do not, one line"],"innovation_enough":true|false (would a professional of this field see something new worth paying for?),', 'critic json'),
 ("    $r = fx_ai($sys, 'Review it now. One JSON object only.', 'deep', 3000, fx_dl($left, 60), ['temp' => 0.2, 'avoid' => $avoid]);\n    if (isset($r['err'])) { fx_back($it, 'critic: ' . $r['err']); return 'retry'; }\n",
  "    $c1 = $it['x']['crit1'] ?? null; // v3.34.11: a first review kept while the second critic is awaited (same round, three hours)\n"
  "    if (is_array($c1) && (int)($c1['round'] ?? -1) === (int)$it['round'] && (int)($c1['at'] ?? 0) > time() - 10800 && is_array($c1['j'] ?? null)) $r = ['j' => $c1['j'], 'by' => (string)($c1['by'] ?? ''), 'provider' => (string)($c1['provider'] ?? '')];\n"
  "    else $r = fx_ai($sys, 'Review it now. One JSON object only.', 'deep', 3000, fx_dl($left, 60), ['temp' => 0.2, 'avoid' => $avoid]);\n    if (isset($r['err'])) { fx_back($it, 'critic: ' . $r['err']); return 'retry'; }\n", 'critic first'),
 ("    if ($left() > 75 && (string)($r['provider'] ?? '') !== '') {\n        $r2 = fx_ai(",
  "    // v3.34.11 (the owner: «ركز على الجودة»): a design that passes the first critic is approved only when a second strong critic of another\n"
  "    // provider agrees — never by one alone; while none answers, the first review is kept and the file waits\n"
  "    $pass1 = (float)$j['score'] >= $cfg['min_score'] && ($j['signature_enough'] ?? true) !== false && ($j['innovation_enough'] ?? true) !== false && !empty($it['spec']['insights']['charts']);\n"
  "    if ($pass1) { $it['x']['crit1'] = ['j' => $j, 'by' => (string)$r['by'], 'provider' => (string)($r['provider'] ?? ''), 'round' => (int)$it['round'], 'at' => (int)($c1['at'] ?? 0) > time() - 10800 && is_array($c1) ? (int)$c1['at'] : time()];\n"
  "        if ($left() < 50) { fx_back($it, 'critic: approval waits for the second critic (time)'); return 'retry'; } }\n"
  "    if ($pass1) {\n        $r2 = fx_ai(", 'second critic always'),
 ("        $j2 = $r2['j'] ?? null;\n        if (is_array($j2) && is_numeric($j2['score'] ?? null)) {\n",
  "        $j2 = $r2['j'] ?? null; $p2 = (string)($r2['provider'] ?? '');\n"
  "        if (!is_array($j2) || !is_numeric($j2['score'] ?? null) || ($p2 === (string)($r['provider'] ?? '') && $p2 !== 'test')) { fx_back($it, 'critic: approval waits for a second strong critic from another provider' . (isset($r2['err']) ? ' (' . mb_substr((string)$r2['err'], 0, 160) . ')' : '')); return 'retry'; }\n"
  "        {\n", 'second critic required'),
 ("            if (count($L($j2['signature'] ?? null)) < count($L($j['signature'] ?? null))) $j['signature'] = $j2['signature'];\n",
  "            if (count($L($j2['signature'] ?? null)) < count($L($j['signature'] ?? null))) $j['signature'] = $j2['signature'];\n"
  "            if (($j2['innovation_enough'] ?? true) === false) $j['innovation_enough'] = false;\n"
  "            if (count($L($j2['innovations'] ?? null)) < count($L($j['innovations'] ?? null))) $j['innovations'] = $j2['innovations'];\n", 'merge innovation'),
 ("    if ($cfg['min_signature'] === 0 && (($j['signature_enough'] ?? true) === false || !$sig)) $gate[] =",
  "    $inno = array_values(array_filter(array_map(fn($f) => is_scalar($f) ? trim((string)$f) : '', is_array($j['innovations'] ?? null) ? $j['innovations'] : []), fn($f) => mb_strlen($f) >= 8)); $it['critique']['innovations'] = array_slice($inno, 0, 12);\n"
  "    if (($j['innovation_enough'] ?? true) === false || !$inno) $gate[] = 'nothing new beyond the best templates for ' . $it['profession'] . ': build the brief\\'s innovations (or better ones) for real — what no competitor does'; // v3.34.11\n"
  "    if ($cfg['min_signature'] === 0 && (($j['signature_enough'] ?? true) === false || !$sig)) $gate[] =", 'innovation gate'),
 ("    $it['score'] = $sc; $it['x']['by']['critic'] = $r['by']; $it['x']['scores'][] = $sc; $it['fails'] = 0;\n",
  "    $it['score'] = $sc; $it['x']['by']['critic'] = $r['by']; $it['x']['scores'][] = $sc; $it['fails'] = 0; unset($it['x']['crit1']);\n", 'crit1 done'),
 # e. the listing tells what only this one does
 ('        . "\\n\\nFACTS:\\n" . fx_facts($it[\'spec\']) . "\\n\\nBUYERS (research): "',
  '        . "\\n\\nFACTS:\\n" . fx_facts($it[\'spec\']) . "\\n\\nWHAT ONLY THIS ONE DOES (the critics\' findings, true of this design): " . jenc([\'for_this_field\' => $it[\'critique\'][\'signature\'] ?? [], \'new\' => $it[\'critique\'][\'innovations\'] ?? []]) . "\\n\\nBUYERS (research): "', 'copy facts'),
 ('            . "\\n\\nTHE FIELD: " . $f[\'profession\'] . "\\nFACTS:\\n" . fx_suite_facts($ok)',
  '            . "\\n\\nTHE FIELD: " . $f[\'profession\'] . "\\nFACTS:\\n" . fx_suite_facts($ok) . "\\nWHAT ONLY THIS SUITE DOES (the critics\' findings): " . jenc(array_map(fn($p) => [\'for_this_field\' => $p[\'critique\'][\'signature\'] ?? [], \'new\' => $p[\'critique\'][\'innovations\'] ?? []], $ok))', 'suite copy facts'),
 # f. the suite's listing is judged by a strong copy editor before it is kept
 ("        unset($x['slerrs']); $x['suite_listing'] = $l; $x['suite_i18n'] = []; $f['fails'] = 0; return 'suite listing';",
  "        $rv = fx_copy_review($l, $f['profession'], fx_suite_facts($ok), $left); // v3.34.11 (the owner: «الوصف والعناوين غير جيدة»)\n"
  "        if (is_string($rv)) { fx_back($f, 'suite copy review: ' . $rv); return 'retry'; }\n"
  "        if ($rv['score'] < 85) { $x['srev'] = (int)($x['srev'] ?? 0) + 1; $x['slerrs'] = array_merge(['the copy editor scored it ' . $rv['score'] . ' (85 needed)'], $rv['fixes']); fx_note($f, 'suite-copy', 'review ' . $rv['score'] . ' by ' . $rv['by'] . ': ' . implode(' | ', array_slice($rv['fixes'], 0, 4)));\n"
  "            $f['next_at'] = $x['srev'] % 4 === 0 ? time() + 6 * 3600 : 0; return 'invalid'; }\n"
  "        $x['suite_review'] = ['score' => $rv['score'], 'by' => $rv['by']];\n"
  "        unset($x['slerrs']); $x['suite_listing'] = $l; $x['suite_i18n'] = []; $f['fails'] = 0; return 'suite listing';", 'suite copy review'),
 # g. translations by strong models, refused when English is left or the script is wrong
 ("        $r = fx_ai($sys, jenc($en), 'economy', 5000, fx_dl($left, 60), ['temp' => 0.3]); $calls++;",
  "        $r = fx_ai($sys, jenc($en), 'standard', 5000, fx_dl($left, 60), ['temp' => 0.3]); $calls++;", 'suite translate tier'),
 ("$E = fx_suite_lerrs($l, 600);",
  "$E = array_merge(fx_suite_lerrs($l, 600), fx_lang_errs($l, $L));", 'suite translate language'),
 ("            $r = fx_ai($sys, jenc($ids), 'economy', 8000, fx_dl($left, 75), ['temp' => 0.2]); $calls++;",
  "            $r = fx_ai($sys, jenc($ids), 'standard', 8000, fx_dl($left, 75), ['temp' => 0.2]); $calls++;", 'translate tier'),
 ("function fx_tr_take(array $have, array $S, string $en, $v): ?string\n{\n    if (!is_string($v) || ($v = trim($v)) === '' || mb_strlen($v) > max(400, mb_strlen($en) * 4)) return null;\n",
  "function fx_tr_take(array $have, array $S, string $en, $v, string $L = ''): ?string\n{\n    if (!is_string($v) || ($v = trim($v)) === '' || mb_strlen($v) > max(400, mb_strlen($en) * 4)) return null;\n"
  "    if ($L !== '' && fx_left_english($en, $v, $L)) return null; // v3.34.11: English left in a translation is asked again\n", 'tr take lang'),
 ("        foreach ($have as $e => $v) if (fx_tr_take($have, $S, $e, $v) === null) unset($have[$e]);",
  "        foreach ($have as $e => $v) if (fx_tr_take($have, $S, $e, $v, $L) === null) unset($have[$e]);", 'tr take have'),
 ("$v = fx_tr_take($have, $S, $e, $T[(string)($i + 1)] ?? null);",
  "$v = fx_tr_take($have, $S, $e, $T[(string)($i + 1)] ?? null, $L);", 'tr take chunk'),
]
for old, new, what in R2: F = sub1(F, old, new, what)

ADD = r"""
// ================================================================ v3.34.11 — what buyers really search (2026-11-08, Claude)
// Google Keyword Planner, read through Dar's Google Ads account (United States, English), the leading template phrase of each field and
// its average monthly searches. Fields absent from Google's answer are left as the marketplace evidence ranks them (not read, not zero).
const FX_SEARCH = [
    ['Wedding planner', 'wedding planner spreadsheet', 2400, 'also «wedding budget spreadsheet» 2,400 — mostly couples planning their own wedding'],
    ['Bookkeeper', 'bookkeeping template google sheets', 590, '«bookkeeping template» 390, «bookkeeping excel template» 320, «small business bookkeeping template» 320'],
    ['Real estate investor', 'rental property spreadsheet', 320, '«rental income spreadsheet» 320; landlords of a few properties'],
    ['Event planner', 'event planning excel template', 320, '«event budget template excel» and «event planning spreadsheet» also asked'],
    ['Restaurant', 'restaurant inventory spreadsheet', 260, '«restaurant inventory sheet» 260, «restaurant food inventory template» 170; cost per click USD 56–63 — buyers who pay'],
    ['Law firm', 'legal case management spreadsheet template', 30, '«case management excel template» 50 (not only law); Google searches are few, Etsy shows the demand'],
    ['Solo lawyer', 'attorney case management spreadsheet', 10, 'few Google searches; Etsy legal case trackers show the demand'],
];
function fx_search_bonus(int $m): float { return $m < 0 ? 0.0 : round(min(15, 5 * log10(max(10, $m) / 10)), 1); } // 10 a month → 0, 320 → 7.5, 2,400 → 11.9
function fx_search_seed(): void
{
    $have = array_flip(array_map('strtolower', fx_professions()));
    // a field with Google's searches and no marketplace row yet (the restaurant): researched from Google alone
    $add = ['restaurant' => ['Restaurant', 80, 60, 25, 'Google Keyword Planner (US): restaurant inventory and food-cost spreadsheets searched every month, high cost per click']];
    foreach ($add as $k => [$p, $d, $c, $price, $why]) if (isset($have[$k]) && !one('SELECT 1 FROM fx_rank WHERE lower(p) = ?', [$k]))
        q('INSERT INTO fx_rank (p, demand, comp, price, score, why, at, src) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', [$p, $d, $c, $price, round($d * (1 - $c / 200) + 20, 1), $why, time(), 'research']);
    foreach (FX_SEARCH as [$p, $kw, $m, $note]) {
        $r = one('SELECT * FROM fx_rank WHERE lower(p) = ?', [strtolower($p)]); if (!$r) continue;
        $base = in_array((string)$r['src'], ['research'], true) ? round((int)$r['demand'] * (1 - (int)$r['comp'] / 200) + 20, 1) : (float)$r['score'];
        $why = mb_substr((string)$r['why'] . ' | Google (US) «' . $kw . '»: ' . $m . ' a month; ' . $note, 0, 600);
        q('UPDATE fx_rank SET score = ?, why = ?, search = ?, at = ? WHERE p = ?', [round($base + fx_search_bonus($m), 1), $why, $m, time(), $r['p']]);
    }
}

// ---------------------------------------------------------------- v3.34.11 — quality: strong models only, the copy editor, the language
const FX_WEAK_RE = '/flash-lite|(?:^|[\/:._-])lite(?:$|[\/:._-])|small|kilo-auto|(?:^|\/)free$|^default$/i'; // (besides Dar's own small-model pattern)
function fx_strong(string $provider, string $model): bool
{
    if ($provider === 'test') return true; // (the tests' own AI)
    if ((defined('AI_STRENGTH') ? (AI_STRENGTH[$provider] ?? 40) : 60) < 55) return false;
    if ($model !== '' && ((defined('AI_SMALL_RE') && preg_match(AI_SMALL_RE, $model)) || preg_match(FX_WEAK_RE, $model))) return false;
    return true;
}
// the strong copy editor: a listing is kept only at 85 or more, by the rules buyers of that field and market would judge it
function fx_copy_review(array $l, string $field, string $facts, callable $left, string $lang = 'English')
{
    $sys = "FX-STAGE: copy-review\nYou are the toughest editor of marketplace listings (Etsy, Shopify, Gumroad) for premium Excel templates bought by «" . $field . "». Score this listing, written in " . $lang . ", from 0 to 100 as a buyer of that field and as the best copywriter of that market would:\n"
        . "- it speaks this field's own daily pain, words and documents — not generic business talk (20)\n- the title: the phrase buyers search first, then one clear benefit; natural, never a list of keywords (15)\n"
        . "- benefits before features, with the exact numbers of the facts (15)\n- what only this product does — its services for this field and what is new — is plain to see (15)\n"
        . "- natural, fluent and native " . $lang . ": no translation smell, no hype, no clichés, no filler (15)\n- every claim true to the facts below; nothing invented: no reviews, ratings, guarantees or features the facts do not have (15)\n"
        . "- easy to scan: short lines, one idea each, the strongest benefit first (5)\n"
        . "Be strict: 85+ only when it would outsell the best listing of this field. Return ONE JSON object: {\"score\":0-100,\"fixes\":[\"exactly what to change and where\"]}\n\nFACTS:\n" . mb_substr($facts, 0, 9000);
    $r = fx_ai($sys, jenc($l), 'deep', 1500, fx_dl($left, 50), ['temp' => 0.2]);
    if (isset($r['err'])) return (string)$r['err'];
    if (!is_numeric($r['j']['score'] ?? null)) return 'the copy editor gave no score';
    return ['score' => max(0, min(100, (int)round((float)$r['j']['score']))), 'fixes' => array_slice(array_values(array_filter(array_map(fn($x) => is_scalar($x) ? trim((string)$x) : '', (array)($r['j']['fixes'] ?? [])), fn($x) => $x !== '')), 0, 8), 'by' => (string)$r['by']];
}
// English left in a translation: for a language of another script, Latin words that are not names of products; for a Latin one, English's own small words
const FX_KEEP_LATIN = ['excel', 'microsoft', 'libreoffice', 'google', 'sheets', 'pdf', 'kpi', 'kpis', 'crm', 'etsy', 'whop', 'shopify', 'gumroad', 'whatsapp', 'windows', 'mac', 'macos', 'office', 'id', 'vat', 'usd', 'roi', 'cpa', 'sku', 'pos', 'airbnb', 'iban', 'swift', 'hr', 'pro', 'demo', 'qr', 'url', 'email', 'e-mail', 'xlsx', 'csv', 'iso', 'gst', 'hvac', 'llc'];
const FX_EN_SMALL = ['the', 'and', 'your', 'with', 'you', 'this', 'that', 'every', 'from', 'which', 'will', 'our', 'into', 'without', 'each', 'yours', 'its', 'their', 'than', 'then', 'when', 'what', 'who', 'how'];
function fx_left_english(string $en, string $v, string $L): bool
{
    if (in_array($L, ['ar', 'fa', 'ur', 'hi', 'zh', 'ru'], true)) {
        preg_match_all('/[A-Za-z][A-Za-z\'-]{2,}/u', $v, $m); $bad = array_filter($m[0], fn($w) => !in_array(mb_strtolower($w), FX_KEEP_LATIN, true));
        return count($bad) >= 2 || (count($bad) === 1 && mb_strtolower(trim($v)) === mb_strtolower(trim($en)) && mb_strlen($en) >= 4);
    }
    preg_match_all('/\p{L}+/u', mb_strtolower($v), $m); $w = $m[0]; if (count($w) < 4) return false;
    $n = count(array_filter($w, fn($x) => in_array($x, ['the', 'and', 'your', 'with', 'you', 'this', 'that', 'every', 'which', 'will', 'our', 'without'], true)));
    return $n >= 2;
}
function fx_lang_errs(array $l, string $L): array
{
    $E = []; $txt = trim(implode("\n", [(string)($l['name'] ?? ''), (string)($l['title'] ?? ''), (string)($l['headline'] ?? ''), (string)($l['description'] ?? ''), implode("\n", array_map('strval', (array)($l['features'] ?? [])))]));
    $script = ['ar' => '/\p{Arabic}/u', 'fa' => '/\p{Arabic}/u', 'ur' => '/\p{Arabic}/u', 'hi' => '/\p{Devanagari}/u', 'zh' => '/\p{Han}/u', 'ru' => '/\p{Cyrillic}/u'][$L] ?? null;
    if ($script) {
        preg_match_all('/\p{L}/u', $txt, $a); preg_match_all($script, $txt, $b); $all = max(1, count($a[0]));
        if (count($b[0]) / $all < 0.75) $E[] = 'language: the text must be written in ' . (FX_LNAME[$L] ?? $L) . ' (only ' . (int)round(100 * count($b[0]) / $all) . '% of its letters are) — no English left beyond product names (Excel, Google Sheets)';
        foreach (['title', 'headline'] as $k) if (fx_left_english('', (string)($l[$k] ?? ''), $L)) $E[] = "$k: English words left — write it in " . (FX_LNAME[$L] ?? $L);
    } else {
        preg_match_all('/\p{L}+/u', mb_strtolower($txt), $m); $w = $m[0]; $n = count(array_filter($w, fn($x) => in_array($x, FX_EN_SMALL, true)));
        if (count($w) && $n / count($w) > 0.02) $E[] = 'language: English words left (' . $n . ' of ' . count($w) . ') — write all of it in ' . (FX_LNAME[$L] ?? $L);
        foreach (['title', 'headline'] as $k) if (fx_left_english('', (string)($l[$k] ?? ''), $L)) $E[] = "$k: English words left — write it in " . (FX_LNAME[$L] ?? $L);
    }
    return $E;
}
"""
F = F.rstrip('\n') + '\n' + ADD.lstrip('\n')
wr('dar-fx.php', F)

A = rd('dar-ai.php')
A = sub1(A, "        if (!empty($X['req']['strong']) && !$X['imgs']) { $big = array_values(array_filter($models, fn($m) => !preg_match(AI_SMALL_RE, (string)$m))); if ($big) $models = $big; }",
  "        if (!empty($X['req']['strong']) && !$X['imgs']) { $big = array_values(array_filter($models, fn($m) => !preg_match(AI_SMALL_RE, (string)$m))); if ($big) $models = $big; }\n"
  "        if (!empty($X['req']['strict']) && !$X['imgs']) { if ((AI_STRENGTH[$id] ?? 40) < 55) { $X['tried'][] = $id . ': not strong enough for this work'; return null; } $models = array_values(array_filter($models, fn($m) => !preg_match(AI_SMALL_RE, (string)$m) && !preg_match('/flash-lite|(?:^|[\\/:._-])lite(?:$|[\\/:._-])|small|kilo-auto|(?:^|\\/)free$|^default$/i', (string)$m))); if (!$models) { $X['tried'][] = $id . ': no strong model'; return null; } } // v3.34.11: the template factory's work (strict) — a strong provider's strong models only",
  'ai strict')
wr('dar-ai.php', A)

old_tok = json.load(open(os.path.join(SRC, 'lib/manifest.json')))['token']
TOK = NEWV + '-' + hashlib.sha256((NEWV + '\n').encode() + F.encode('utf8')).hexdigest()[:8]
S = rd('dar-sync.php'); S = sub1(S, f"const SYNC_VERSION = '{OLDV}';", f"const SYNC_VERSION = '{NEWV}';", 'sync version'); wr('dar-sync.php', S)
changed = {'dar-fx.php', 'dar-sync.php', 'dar-ai.php'}
for root, _, files in os.walk(SRC):
    for fn in files:
        p = os.path.join(root, fn); rel = os.path.relpath(p, SRC)
        if rel == 'lib/manifest.json': continue
        try: s = open(p, 'rb').read().decode('utf8')
        except Exception: continue
        if old_tok in s: open(p, 'wb').write(s.replace(old_tok, TOK).encode('utf8')); changed.add(rel)
C = rd('assets/core.js'); C = sub1(C, f"export const VERSION = '{OLDV}-fx';", f"export const VERSION = '{NEWV}-fx';", 'core version'); wr('assets/core.js', C); changed.add('assets/core.js')
M = json.load(open(os.path.join(SRC, 'lib/manifest.json')))
M['version'] = NEWV; M['token'] = TOK; M['built'] = BUILT
for rel in list(M['files']):
    p = os.path.join(SRC, rel)
    if os.path.isfile(p): M['files'][rel] = hashlib.sha1(open(p, 'rb').read()).hexdigest()
open(os.path.join(SRC, 'lib/manifest.json'), 'w').write(json.dumps(M, ensure_ascii=False, separators=(',', ':')))
print(json.dumps({'token': TOK, 'changed': len(changed)}))
