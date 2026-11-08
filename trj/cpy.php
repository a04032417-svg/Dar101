<?php
// One-off job, 2026-11-08 (the owner: «اجعل الوصف والاسم أفضل … ويستخدم نظريات علمية بالكتابة … اجعله هو من يفعل»): Dar's own copy
// team writes, for each real-estate kit and each of the 15 languages, the store listing from the verified facts — written for that
// market, not translated, on research-based persuasion (PAS, AIDA, 4U, loss aversion, specificity, fluency, serial position, honest
// authority) — and the texts of every listing picture in that language. A checker refuses what breaks a rule and asks again with the
// reasons. Nothing in Dar changes: this only calls fx_ai(). Run: php cpy.php <base64 key> [langs,comma]
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$only = array_filter(explode(',', $argv[2] ?? ''));
$here = __DIR__; $site = getenv('TR_SITE') ?: '/home/u791571885/domains/dar.ink/public_html';
$lk = fopen("$here/clock-" . md5(implode(',', $only)), 'c'); if (!flock($lk, LOCK_EX | LOCK_NB)) { echo "busy\n"; exit(0); }
chdir($site); $_SERVER['REQUEST_TIME_FLOAT'] = microtime(true); $argv = ['dar-sync.php', 'job']; $argc = 2;
require $site . '/dar-sync.php';
$T0 = time(); $BUDGET = (int)(getenv('TR_BUDGET') ?: 230); $left = fn() => $BUDGET - (time() - $T0);
$jb = (string)@file_get_contents("$here/cjob.bin"); $job = json_decode((string)openssl_decrypt(substr($jb, 28), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, substr($jb, 0, 12), substr($jb, 12, 16)), true);
if (!is_array($job)) { echo "job?\n"; exit(1); }
$st = "$here/cst"; @mkdir($st, 0700, true); $tok = substr(hash('sha256', $K . 'fxtr'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true);
$langs = $job['langs']; if ($only) $langs = array_intersect_key($langs, array_flip($only));
const LENS = ['*' => ['t' => [25, 80], 'st' => 60, 'sd' => [110, 165], 'd' => [800, 1600]], 'zh' => ['t' => [10, 40], 'st' => 30, 'sd' => [45, 90], 'd' => [380, 900]]];
const RULES = 3; // a failure under older rules gets fresh tries
$get = fn(string $f) => is_file($f) ? json_decode((string)file_get_contents($f), true) : null;
$SCRIPT = ['ar' => '\p{Arabic}', 'fa' => '\p{Arabic}', 'ur' => '\p{Arabic}', 'ru' => '\p{Cyrillic}', 'hi' => '\p{Devanagari}', 'zh' => '\p{Han}'];
$KEEP = ['Excel', 'WhatsApp', 'LibreOffice', 'Microsoft', 'ZIP', 'CRM', 'PRO', 'Real Estate', 'Toolkit', 'Charts', 'Dashboard'];
$own = function (string $s, string $code) use ($SCRIPT): bool { // most letters in the language's own script
    if (!isset($SCRIPT[$code])) return true; $t = preg_replace('/Excel|WhatsApp|LibreOffice|Microsoft|ZIP|CRM|PRO|365|<\/?b>/u', '', $s);
    return preg_match_all('/' . $SCRIPT[$code] . '/u', $t) >= 2 * preg_match_all('/[A-Za-z]/u', $t); };
$chkL = function ($o, array $it, string $code) use ($own): array {
    $e = []; if (!is_array($o)) return ['not a JSON object'];
    foreach (['title', 'headline', 'description', 'seo_title', 'seo_description'] as $k) if (!is_string($o[$k] ?? null) || trim($o[$k]) === '') $e[] = "\"$k\" missing";
    if ($e) return $e;
    $L = fn($k) => mb_strlen(trim($o[$k]));
    $N = LENS[$code] ?? LENS['*']; // Chinese says in one character what a Latin script says in three
    if ($L('title') > $N['t'][1] || $L('title') < $N['t'][0]) $e[] = 'title: ' . $L('title') . " characters — {$N['t'][0]} to {$N['t'][1]}";
    if ($L('headline') > $N['t'][1] || $L('headline') < $N['t'][0]) $e[] = 'headline: ' . $L('headline') . " characters — one complete sentence of {$N['t'][0]} to {$N['t'][1]}";
    if ($L('seo_title') > $N['st']) $e[] = "seo_title: at most {$N['st']} characters"; if ($L('seo_description') < $N['sd'][0] || $L('seo_description') > $N['sd'][1]) $e[] = "seo_description: {$N['sd'][0]} to {$N['sd'][1]} characters";
    if ($L('description') < $N['d'][0] || $L('description') > $N['d'][1]) $e[] = 'description: ' . $L('description') . " characters — {$N['d'][0]} to {$N['d'][1]}";
    foreach (['title', 'headline', 'description', 'seo_title', 'seo_description'] as $k) if (preg_match('/…|\.\.\./u', $o[$k])) $e[] = "$k: no ellipsis — every sentence complete";
    if (preg_match_all('/[,،，、]/u', $o['title']) > 1) $e[] = 'title: a list of words separated by commas is refused — one search phrase, then one benefit (at most one separator – or :)';
    if (in_array($code, ['ar', 'fa', 'ur'], true)) foreach (['title', 'headline', 'description'] as $k) if (preg_match('/[A-Za-z0-9\p{Arabic}\s]\s*,\s*[\p{Arabic}]/u', $o[$k])) $e[] = "$k: use the Arabic comma «،», never «,»";
    $b = substr_count($o['description'], '•'); if ($b < 4 || $b > 8) $e[] = "description: 4 to 8 bullets «•» (got $b)";
    foreach ($it['must'] as $n) if (!preg_match('/(?<![0-9])' . $n . '(?![0-9])/u', $o['description'])) $e[] = "description: the number $n is missing (write it as a digit)";
    if (!str_contains($o['description'], 'Excel')) $e[] = 'description: keep the word «Excel»';
    if ($code === 'en' && preg_match('/\b(reviews?|rated|stars?|best[- ]?selling|#1|guarantee[ds]?|limited time|discount|% off|bestseller)\b/i', $o['title'] . ' ' . $o['headline'] . ' ' . $o['description'])) $e[] = 'no reviews, ratings, rankings, guarantees, discounts or deadlines — they are not in the facts';
    $tg = $o['tags'] ?? null; if (!is_array($tg) || count($tg) !== 13) $e[] = 'tags: exactly 13 (got ' . (is_array($tg) ? count($tg) : 0) . ')';
    else { foreach ($tg as $t) if (!is_string($t) || trim($t) === '' || mb_strlen($t) > 20) $e[] = 'tag «' . (is_string($t) ? $t : '?') . '»: 1 to 20 characters';
        if (count(array_unique(array_map(fn($t) => mb_strtolower(trim((string)$t)), $tg))) !== 13) $e[] = 'tags: two are the same'; }
    if (!$own($o['title'] . ' ' . $o['headline'] . ' ' . $o['description'], $code)) $e[] = 'too much left in English — write it in the language (only Excel, WhatsApp, LibreOffice, Microsoft, ZIP, CRM stay)';
    foreach (['title', 'headline', 'seo_title'] as $k) if (!$own($o[$k], $code)) $e[] = "$k: written in English — write it in the language of the buyer";
    if ($code !== 'en') foreach (['title', 'headline', 'seo_title'] as $k) if (preg_match('/\b(Real Estate|Spreadsheet|Languages|Toolkit|Template|Developer|Agent|Feasibility|Tracker|Charts)\b/i', $o[$k])) $e[] = "$k: English words — use the words buyers of this market type in search (only Excel, CRM, WhatsApp stay)";
    return $e; };
$chkC = function ($a, array $en, string $code) use ($own): array {
    if (!is_array($a) || array_is_list($a) === false) { if (is_array($a) && isset($a['captions']) && is_array($a['captions'])) $a = $a['captions']; else return ['answer with a JSON array of strings']; }
    $e = []; if (count($a) !== count($en)) return ['exactly ' . count($en) . ' strings needed, same order (got ' . count($a) . ')'];
    foreach ($en as $i => $s) { $t = $a[$i] ?? null; $n = $i + 1;
        if (!is_string($t) || trim($t) === '') { $e[] = "#$n empty"; continue; }
        if (substr_count($s, '<b>') !== substr_count($t, '<b>') || substr_count($s, '</b>') !== substr_count($t, '</b>')) $e[] = "#$n: keep the <b>…</b> tags";
        $lim = (int)ceil(mb_strlen(strip_tags($s)) * ($code === 'zh' ? 1.0 : 1.4)) + 12; if (mb_strlen(strip_tags($t)) > $lim) $e[] = "#$n: too long for the picture (" . mb_strlen(strip_tags($t)) . " > $lim)";
        preg_match_all('/\d+/', $s, $m1); foreach ($m1[0] as $num) if (!preg_match('/(?<![0-9])' . $num . '(?![0-9])/u', $t)) $e[] = "#$n: keep the number $num";
        if (mb_strlen($s) > 25 && !$own($t, $code)) $e[] = "#$n: write it in the language";
        if (count($e) > 14) break; }
    return $e; };
$done = 0; $total = 0; $fail = []; $calls = 0; $last = '';
foreach ($langs as $code => $lname) foreach ($job['items'] as $kind => $it) foreach (['L', 'C'] as $part) {
    if ($part === 'C' && $code === 'en') continue; // (the English picture texts are the reviewed originals)
    $total++; $f = "$st/$code-$kind-$part.json"; $r = $get($f);
    if ($r && !empty($r['ok']) && $part === 'L' && ($e0 = $chkL($r['out'], $it, $code))) { $r = ['ok' => false, 'tries' => 0, 'rules' => RULES, 'errors' => $e0]; file_put_contents($f, json_encode($r, JSON_UNESCAPED_UNICODE)); } // a newer rule re-reads earlier answers
    if ($r && !empty($r['ok'])) { $done++; continue; }
    if ($r && empty($r['ok']) && ($r['rules'] ?? 1) < RULES) $r['tries'] = 0;
    if (($r['tries'] ?? 0) >= 8) { $fail[] = "$code/$kind/$part: " . implode(' | ', array_slice($r['errors'] ?? [], 0, 3)); continue; }
    if ($left() < 100) continue;
    $prev = !empty($r['errors']) ? "\nYour previous answer was refused for: " . implode('; ', array_slice($r['errors'], 0, 12)) . "\nFix every point." : '';
    if ($part === 'L') { $N = LENS[$code] ?? LENS['*'];
        $punct = in_array($code, ['ar', 'fa', 'ur'], true) ? "\nPunctuation of the language: the Arabic comma «،» (never «,»), its own question mark." : ($code === 'zh' ? "\nChinese punctuation (，。：)." : '');
        $sys = "FX-STAGE: listing-science\nYou are the senior conversion copywriter of a premium template store, a native $lname speaker who knows how real-estate professionals of that market speak and search. "
            . "Write the store listing of this digital product for $lname-speaking buyers — written from scratch for that market, NOT a translation — applying research-based persuasion:\n"
            . "1. PAS (Problem, Agitate, Solution) in the opening: name the buyer's daily pain concretely, let the cost of doing nothing be felt (loss aversion, Kahneman & Tversky), then present the product as the way out.\n"
            . "2. AIDA for the whole description: Attention (the opening), Interest (what changes for the buyer), Desire (benefits with exact numbers), Action (one calm, clear next step at the end).\n"
            . "3. Headline by the 4U rule: useful, unique, ultra-specific (urgent only if true). One complete sentence, {$N['t'][0]} to {$N['t'][1]} characters, never cut, no ellipsis.\n"
            . "4. Specificity effect: use the exact numbers of the facts (sheets, charts, gauges, languages, steps) — specific claims are believed, vague ones are not.\n"
            . "5. Benefit before feature (jobs to be done): each bullet starts with what the buyer gains, then the feature that gives it.\n"
            . "6. Processing fluency: short sentences, the everyday words of that market's professionals, one idea per line.\n"
            . "7. Serial-position effect: the strongest benefit first, the second strongest last.\n"
            . "8. Honest authority (Cialdini without manipulation): authority only through concrete facts. NO invented reviews, ratings, buyer counts, awards, guarantees, discounts, deadlines or scarcity.\n"
            . "9. Search: the main phrase that market's buyers type into a marketplace search comes in the first 40 characters of the title; title {$N['t'][0]} to {$N['t'][1]} characters; at most ONE separator (– or :) — never a comma list of keywords.\n"
            . "Fields: title; headline; description ({$N['d'][0]} to {$N['d'][1]} characters: the PAS opening paragraph, a blank line, 5 to 7 bullets starting with «• », a blank line, one line on what the buyer receives (the ZIP, the 15 languages, the demo copy, Excel 2019/2021/Microsoft 365 or LibreOffice), and a closing call to action); seo_title (at most {$N['st']}); seo_description ({$N['sd'][0]} to {$N['sd'][1]}); tags (13 different search phrases of that market, at most 20 characters each).\n"
            . "Keep as they are: Excel, WhatsApp, LibreOffice, Microsoft 365, ZIP. Numbers as digits.$punct\n"
            . "Use ONLY the facts given — add no feature and no claim. Answer with ONE JSON object: {\"title\":\"…\",\"headline\":\"…\",\"description\":\"…\",\"seo_title\":\"…\",\"seo_description\":\"…\",\"tags\":[13]}.";
        $usr = "PRODUCT: " . $it['name'] . "\nPRICE: USD 29, one payment, instant download.\nTHE VERIFIED FACTS (an earlier English listing — its facts are true, its style is not to be copied):\n" . json_encode($it['facts'], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . "\nWrite the $lname listing now. One JSON object only.$prev";
        $a = fx_ai($sys, $usr, 'deep', 5000, (int)min(170, $left() - 15), ['temp' => 0.6]); $calls++;
        $o = $a['j'] ?? null; $e = isset($a['err']) ? ['ai: ' . $a['err']] : $chkL($o, $it, $code);
        if (!$e) $o = ['title' => trim($o['title']), 'headline' => trim($o['headline']), 'description' => trim($o['description']), 'seo_title' => trim($o['seo_title']), 'seo_description' => trim($o['seo_description']), 'tags' => array_map('trim', $o['tags'])];
    } else {
        $map = $job['sheets'][$kind][$code] ?? [];
        $sys = "FX-STAGE: captions-localise\nYou are a native $lname conversion copywriter. These are the texts printed on the listing pictures of an Excel product for real-estate professionals. "
            . "Write each one in $lname for that market: short, concrete, persuasive, the words its professionals use — the same meaning, not word for word.\n"
            . "Rules: answer with a JSON array of exactly " . count($it['captions']) . " strings in the same order; keep every <b>…</b> around the matching words; numbers as digits; keep Excel, WhatsApp, LibreOffice, Microsoft, 365 and ZIP; "
            . "each string at most about as long as its English (" . ($code === 'zh' ? 'the same length' : 'up to 1.4 times') . ") — the pictures have fixed space; when a string names a sheet, write the sheet's name exactly as in this list of the $lname workbook: "
            . json_encode($map, JSON_UNESCAPED_UNICODE) . ($code === 'ar' || $code === 'fa' || $code === 'ur' ? "\nUse the Arabic comma «،»." : '');
        $usr = "THE ENGLISH TEXTS (JSON array):\n" . json_encode($it['captions'], JSON_UNESCAPED_UNICODE) . "\nAnswer with the JSON array only.$prev";
        $a = fx_ai($sys, $usr, 'deep', 7000, (int)min(170, $left() - 15), ['temp' => 0.4]); $calls++;
        $o = $a['j'] ?? null; if (is_array($o) && isset($o['captions'])) $o = $o['captions'];
        $e = isset($a['err']) ? ['ai: ' . $a['err']] : $chkC($o, $it['captions'], $code);
        if (!$e) $o = array_map(fn($s) => trim((string)$s), array_values($o));
    }
    if ($e) { $soft = isset($a['err']) && preg_match('/no_time|unavailable|deadline/', (string)$a['err']); file_put_contents($f, json_encode(['ok' => false, 'tries' => ($r['tries'] ?? 0) + ($soft ? 0 : 1), 'rules' => RULES, 'errors' => $e, 'by' => $a['by'] ?? ''], JSON_UNESCAPED_UNICODE)); $last = "$code/$kind/$part: " . $e[0]; continue; }
    file_put_contents($f, json_encode(['ok' => true, 'out' => $o, 'by' => $a['by'] ?? '', 'at' => gmdate('c')], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT)); $done++;
}
$files = [];
foreach ($job['langs'] as $code => $ln) { $m = []; $need = 0; $have = 0;
    foreach ($job['items'] as $kind => $_) foreach (['L', 'C'] as $part) { if ($part === 'C' && $code === 'en') continue; $need++; $r = $get("$st/$code-$kind-$part.json"); if ($r && !empty($r['ok'])) { $m[$kind][$part] = $r['out']; $m[$kind]['by_' . $part] = $r['by'] ?? ''; $have++; } }
    if ($have !== $need) continue; $iv = random_bytes(12); $tag = '';
    $ct = openssl_encrypt(json_encode($m, JSON_UNESCAPED_UNICODE), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag); file_put_contents("$pub/C-$code.json.bin", $iv . $tag . $ct); $files[] = "C-$code"; }
@file_put_contents("$pub/cstatus.json", json_encode(['at' => gmdate('c'), 'done' => $done, 'total' => $total, 'files' => $files, 'failed' => $fail, 'calls' => $calls, 'last_note' => mb_substr($last, 0, 300)], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
echo json_encode(['done' => $done, 'total' => $total, 'files' => count($files), 'calls' => $calls]), "\n";
