<?php
// One-off job, 2026-11-07: Dar's own AI writes the store listings of the two real-estate Excel kits (Agent PRO v3, Developer v2) in
// 14 more languages — localised copy with the search words of each market, every fact kept, checked here and retried with the reasons —
// and leaves each finished file, encrypted, where Claude's pick-up fetches it. Nothing in Dar changes: this only calls fx_ai().
// Run: php ltr.php <base64 key> <langs,comma>
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$only = array_filter(explode(',', $argv[2] ?? ''));
$here = __DIR__; $site = getenv('TR_SITE') ?: '/home/u791571885/domains/dar.ink/public_html';
$lk = fopen("$here/llock-" . md5(implode(',', $only)), 'c'); if (!flock($lk, LOCK_EX | LOCK_NB)) { echo "busy\n"; exit(0); }
chdir($site); $_SERVER['REQUEST_TIME_FLOAT'] = microtime(true); $argv = ['dar-sync.php', 'job']; $argc = 2;
require $site . '/dar-sync.php';
$T0 = time(); $BUDGET = (int)(getenv("TR_BUDGET") ?: 230); $left = fn() => $BUDGET - (time() - $T0);
$jb = (string)@file_get_contents("$here/ljob.bin"); $job = json_decode((string)openssl_decrypt(substr($jb, 28), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, substr($jb, 0, 12), substr($jb, 12, 16)), true); if (!is_array($job)) { echo "job?\n"; exit(1); }
$st = "$here/lst"; @mkdir($st, 0700, true); $tok = substr(hash('sha256', $K . 'fxtr'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true);
$langs = $job['langs']; if ($only) $langs = array_intersect_key($langs, array_flip($only));
$get = function (string $f) { return is_file($f) ? json_decode(file_get_contents($f), true) : null; };
$NONLATIN = ['ar' => '\p{Arabic}', 'fa' => '\p{Arabic}', 'ur' => '\p{Arabic}', 'ru' => '\p{Cyrillic}', 'hi' => '\p{Devanagari}', 'zh' => '\p{Han}'];
$check = function (array $en, $o, string $code) use ($NONLATIN): array {
    $e = []; if (!is_array($o)) return ['not a JSON object'];
    foreach (['title', 'headline', 'description'] as $k) if (!is_string($o[$k] ?? null) || trim($o[$k]) === '') $e[] = "\"$k\" missing";
    if ($e) return $e;
    $tl = mb_strlen($o['title']); if ($tl > 140 || $tl < 50) $e[] = "title: $tl characters — it must be 50 to 140 (front-load the words buyers search)";
    $tg = $o['tags'] ?? null;
    if (!is_array($tg) || count($tg) !== 13) $e[] = 'tags: exactly 13 needed, got ' . (is_array($tg) ? count($tg) : 0);
    else { foreach ($tg as $t) if (!is_string($t) || trim($t) === '' || mb_strlen($t) > 20) $e[] = 'tag «' . (is_string($t) ? $t : '?') . '»: 1 to 20 characters';
        if (count(array_unique(array_map(fn($t) => mb_strtolower(trim((string)$t)), $tg))) !== 13) $e[] = 'tags: two are the same'; }
    $fe = $o['features'] ?? null; if (!is_array($fe) || count($fe) !== count($en['features'])) $e[] = 'features: exactly ' . count($en['features']) . ' needed, one per input feature, same order';
    $d = $o['description']; $ratio = mb_strlen($d) / max(1, mb_strlen($en['description']));
    if ($ratio < ($code === 'zh' ? 0.25 : 0.6)) $e[] = 'description too short: it must keep every section and every fact of the English';
    if (mb_strlen($d) > 4800) $e[] = 'description longer than 4800 characters';
    $bE = substr_count($en['description'], '•'); $bO = substr_count($d, '•'); if (abs($bE - $bO) > 2) $e[] = "description: keep the bullets «•» ($bE in the English, $bO in yours)";
    foreach (['12', '15', '13'] as $n) if (str_contains($en['description'], $n) && !preg_match('/(?<![0-9])' . $n . '(?![0-9])/u', $d)) $e[] = "description: the number $n is missing (keep every number as a digit)";
    foreach (['Excel', 'WhatsApp', 'LibreOffice'] as $w) if (str_contains($en['description'], $w) && !str_contains($d, $w)) $e[] = "description: keep «{$w}» as it is";
    if (isset($NONLATIN[$code])) { $all = $o['title'] . ' ' . $o['headline'] . ' ' . $d; $own = preg_match_all('/' . $NONLATIN[$code] . '/u', $all); $lat = preg_match_all('/[A-Za-z]/u', preg_replace('/Excel|WhatsApp|LibreOffice|Microsoft|ZIP|xlsx|CRM|PRO|m²/u', '', $all));
        if ($own < 3 * $lat) $e[] = 'too much left in English: write it all in the target language (only Excel, WhatsApp, LibreOffice, Microsoft, ZIP, CRM stay)'; }
    return $e;
};
$done = 0; $total = 0; $fail = []; $calls = 0; $last = '';
foreach ($langs as $code => $lname) foreach ($job['items'] as $kind => $en) {
    $total++; $f = "$st/$code-$kind.json"; $r = $get($f); if ($r && !empty($r['ok'])) { $done++; continue; }
    if (($r['tries'] ?? 0) >= 10) { $fail[] = "$code/$kind: " . implode(' | ', array_slice($r['errors'] ?? [], 0, 3)); continue; }
    if ($left() < 90) continue;
    $sys = "FX-STAGE: listing-localise\nYou are a native $lname e-commerce copywriter and marketplace SEO specialist (Etsy, Shopify, Gumroad, Whop). Write the store listing of this digital product for buyers who read $lname: "
        . "not a word-for-word translation — the copy a top seller of that market would write: natural, persuasive, clear, with the exact words and phrases real-estate professionals there type into a marketplace search.\n"
        . "Rules:\n1. Keep EVERY fact, number and feature of the English, and add none: no new feature, no new claim, no price, no discount, no review.\n"
        . "2. title: 50 to 140 characters, the main search phrase first, then the strongest features, separated by commas.\n"
        . "3. tags: exactly 13, each at most 20 characters, all different, in $lname, the phrases buyers search (mix broad and specific).\n"
        . "4. headline: one sentence. features: exactly as many as the English, same order, each one short line.\n"
        . "5. description: the same sections in the same order, section headings in capitals where the script has them, bullets «•», numbers as digits; keep Excel, WhatsApp, LibreOffice, Microsoft and ZIP as they are. Sheet and chart names as a professional of that market calls them.\n"
        . "6. Answer with ONE JSON object: {\"title\":\"…\",\"tags\":[13],\"headline\":\"…\",\"features\":[…],\"description\":\"…\"}.";
    $usr = "THE ENGLISH LISTING:\n" . json_encode($en, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . "\nWrite the $lname listing now. One JSON object only." . (!empty($r['errors']) ? "\nYour previous answer was refused: " . implode('; ', array_slice($r['errors'], 0, 10)) : '');
    $a = fx_ai($sys, $usr, 'deep', 6000, (int)min(160, $left() - 10), ['temp' => 0.5]); $calls++;
    $o = $a['j'] ?? null; $e = isset($a['err']) ? ['ai: ' . $a['err']] : $check($en, $o, $code);
    if ($e) { file_put_contents($f, json_encode(['ok' => false, 'tries' => ($r['tries'] ?? 0) + (isset($a['err']) && (str_contains($a['err'], 'no_time') || str_contains($a['err'], 'unavailable')) ? 0 : 1), 'errors' => $e, 'by' => $a['by'] ?? ''], JSON_UNESCAPED_UNICODE)); $last = "$code/$kind: " . $e[0]; continue; }
    $o = ['title' => trim($o['title']), 'tags' => array_map('trim', $o['tags']), 'headline' => trim($o['headline']), 'features' => array_map('strval', $o['features']), 'description' => trim($o['description'])];
    file_put_contents($f, json_encode(['ok' => true, 'out' => $o, 'by' => $a['by'] ?? '', 'at' => gmdate('c')], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT)); $done++;
}
$files = [];
foreach ($langs as $code => $ln) { $m = []; foreach ($job['items'] as $kind => $_) { $r = $get("$st/$code-$kind.json"); if ($r && !empty($r['ok'])) $m[$kind] = $r['out']; }
    if (count($m) !== count($job['items'])) continue; $iv = random_bytes(12); $tag = '';
    $ct = openssl_encrypt(json_encode($m, JSON_UNESCAPED_UNICODE), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag); file_put_contents("$pub/L-$code.json.bin", $iv . $tag . $ct); $files[] = "L-$code.json"; }
@file_put_contents("$pub/lstatus-" . ($only ? implode('', $only) : 'all') . '.json', json_encode(['at' => gmdate('c'), 'done' => $done, 'total' => $total, 'files' => $files, 'failed' => $fail, 'calls' => $calls, 'last_note' => mb_substr($last, 0, 300)], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
echo json_encode(['done' => $done, 'total' => $total, 'files' => count($files), 'calls' => $calls]), "\n";
