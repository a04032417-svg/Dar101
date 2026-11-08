<?php
// One-off job, 2026-11-08 (the owner: «اجعله ينشئ صور بكل اللغات … اجعله هو من يفعل»): Dar's copy team writes, once, the fixed
// phrases of the factory's listing pictures (engine/pictures.py, board design) in the 14 other languages. The engine then prints every
// product's pictures in each language: the product's own words come from its i18n, these fixed phrases from this table.
// A checker refuses an answer that drops a placeholder, a <b> tag or a number, is too long for the picture, or stays in English.
// Nothing in Dar changes: this only calls fx_ai(). Run: php pic.php <base64 key> [langs,comma]   → fxtr/<tok>/fixed_pic.json.bin
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$only = array_filter(explode(',', $argv[2] ?? ''));
$here = __DIR__; $site = getenv('TR_SITE') ?: '/home/u791571885/domains/dar.ink/public_html';
$lk = fopen("$here/plock-" . md5(implode(',', $only)), 'c'); if (!flock($lk, LOCK_EX | LOCK_NB)) { echo "busy\n"; exit(0); }
chdir($site); $_SERVER['REQUEST_TIME_FLOAT'] = microtime(true); $argv = ['dar-sync.php', 'job']; $argc = 2;
require $site . '/dar-sync.php';
$T0 = time(); $BUDGET = (int)(getenv('TR_BUDGET') ?: 230); $left = fn() => $BUDGET - (time() - $T0);
$EN = json_decode((string)@file_get_contents("$here/pic_en.json"), true); if (!is_array($EN)) { echo "pic_en?\n"; exit(1); }
$LN = ['ar' => 'Arabic', 'fr' => 'French', 'es' => 'Spanish', 'de' => 'German', 'it' => 'Italian', 'pt' => 'Portuguese (Brazil)', 'tr' => 'Turkish',
       'nl' => 'Dutch', 'ru' => 'Russian', 'fa' => 'Persian', 'ur' => 'Urdu', 'hi' => 'Hindi', 'zh' => 'Simplified Chinese', 'id' => 'Indonesian'];
if ($only) $LN = array_intersect_key($LN, array_flip($only));
$st = "$here/pst"; @mkdir($st, 0700, true); $tok = substr(hash('sha256', $K . 'fxtr'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true);
$SCRIPT = ['ar' => '\p{Arabic}', 'fa' => '\p{Arabic}', 'ur' => '\p{Arabic}', 'ru' => '\p{Cyrillic}', 'hi' => '\p{Devanagari}', 'zh' => '\p{Han}'];
$own = function (string $s, string $code) use ($SCRIPT): bool {
    if (!isset($SCRIPT[$code])) return true; $t = preg_replace('/\{[a-z_]+\}|Excel|LibreOffice|<\/?b>|\d+/u', '', $s);
    return preg_match_all('/' . $SCRIPT[$code] . '/u', $t) >= 2 * preg_match_all('/[A-Za-z]/u', $t); };
$chk = function ($o, string $code) use ($EN, $own): array {
    if (!is_array($o)) return ['answer with one JSON object'];
    $e = [];
    foreach ($EN as $k => $s) { $t = $o[$k] ?? null;
        if (!is_string($t) || trim($t) === '') { $e[] = "«{$k}» missing"; continue; }
        preg_match_all('/\{[a-z_]+\}/', $s, $a); preg_match_all('/\{[a-z_]+\}/', $t, $b); sort($a[0]); sort($b[0]);
        if ($a[0] !== $b[0]) $e[] = "«{$k}»: keep exactly the placeholders " . (implode(' ', $a[0]) ?: '(none)') . ' untranslated';
        if (substr_count($s, '<b>') !== substr_count($t, '<b>') || substr_count($s, '</b>') !== substr_count($t, '</b>')) $e[] = "«{$k}»: keep the <b>…</b> tags";
        preg_match_all('/\d+/', $s, $m); foreach ($m[0] as $n) if (!preg_match('/(?<![0-9])' . $n . '(?![0-9])/u', $t)) $e[] = "«{$k}»: keep the number $n";
        $lim = (int)ceil(mb_strlen(strip_tags($s)) * ($code === 'zh' ? 1.0 : 1.45)) + 10; if (mb_strlen(strip_tags($t)) > $lim) $e[] = "«{$k}»: too long for the picture";
        if (mb_strlen($s) > 20 && !$own($t, $code)) $e[] = "«{$k}»: write it in the language";
        if (preg_match('/…|\.\.\./u', $t)) $e[] = "«{$k}»: no ellipsis"; }
    foreach (array_keys($o) as $k) if (!isset($EN[$k])) { $e[] = "unknown key «{$k}»"; break; }
    return array_slice($e, 0, 16); };
$done = 0; $calls = 0; $last = ''; $fail = [];
foreach ($LN as $code => $lname) {
    $f = "$st/$code.json"; $r = is_file($f) ? json_decode((string)file_get_contents($f), true) : null;
    if ($r && !empty($r['ok'])) { $done++; continue; }
    if (($r['tries'] ?? 0) >= 8) { $fail[] = "$code: " . implode(' | ', array_slice($r['errors'] ?? [], 0, 3)); continue; }
    if ($left() < 90) continue;
    $prev = !empty($r['errors']) ? "\nYour previous answer was refused for: " . implode('; ', $r['errors']) . "\nFix every point." : '';
    $sys = "FX-STAGE: picture-phrases\nYou are a native $lname conversion copywriter. These are the fixed phrases printed on the listing pictures of Excel workbooks sold to professionals "
        . "(a picture shows the real sheet with zoomed cells and these phrases as headings, captions and footers). Write each one in $lname for that market: short, concrete, natural, "
        . "the words professionals of that language use — the same meaning, not word for word.\n"
        . "Rules: answer with ONE JSON object with exactly the same keys; keep every {placeholder} exactly as written (it is replaced by the product's own words, already in $lname); "
        . "keep the <b>…</b> tags around the matching words; numbers as digits; keep Excel, LibreOffice and 365; each phrase at most about as long as the English (" . ($code === 'zh' ? 'the same length' : 'up to 1.4 times')
        . ") — the picture has fixed space; no ellipsis." . (in_array($code, ['ar', 'fa', 'ur'], true) ? ' Use the Arabic comma «،».' : '') . ($code === 'zh' ? ' Chinese punctuation (，。：).' : '');
    $usr = "THE ENGLISH PHRASES (JSON):\n" . json_encode($EN, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . "\nAnswer with the JSON object only.$prev";
    $a = fx_ai($sys, $usr, 'deep', 4000, (int)min(150, $left() - 15), ['temp' => 0.4]); $calls++;
    $o = $a['j'] ?? null; $e = isset($a['err']) ? ['ai: ' . $a['err']] : $chk($o, $code);
    if ($e) { $soft = isset($a['err']) && preg_match('/no_time|unavailable|deadline/', (string)$a['err']);
        file_put_contents($f, json_encode(['ok' => false, 'tries' => ($r['tries'] ?? 0) + ($soft ? 0 : 1), 'errors' => $e, 'by' => $a['by'] ?? ''], JSON_UNESCAPED_UNICODE)); $last = "$code: " . $e[0]; continue; }
    $o = array_map(fn($s) => trim((string)$s), array_intersect_key($o, $EN));
    file_put_contents($f, json_encode(['ok' => true, 'out' => $o, 'by' => $a['by'] ?? '', 'at' => gmdate('c')], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT)); $done++;
}
$all = ['en' => $EN]; foreach (glob("$st/*.json") as $p) { $r = json_decode((string)file_get_contents($p), true); if (!empty($r['ok'])) $all[basename($p, '.json')] = $r['out'] + ['_by' => $r['by'] ?? '']; }
$iv = random_bytes(12); $tag = ''; $ct = openssl_encrypt(json_encode($all, JSON_UNESCAPED_UNICODE), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag);
file_put_contents("$pub/fixed_pic.json.bin", $iv . $tag . $ct);
@file_put_contents("$pub/pstatus.json", json_encode(['at' => gmdate('c'), 'langs' => array_keys($all), 'failed' => $fail, 'calls' => $calls, 'last_note' => mb_substr($last, 0, 300)], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
echo json_encode(['done' => $done, 'langs' => count($all), 'calls' => $calls]), "\n";
