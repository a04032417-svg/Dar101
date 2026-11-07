<?php
// One-off job, round 3 (2026-11-07): the strings Dar's translation left in English in the two real-estate kits — Dar's AI translates
// them now, checked here (count, placeholders, ★, the language's own script, Excel tab-name rules) and retried with the reasons.
// Run: php fixtr.php <base64 key> <langs,comma>
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$only = array_filter(explode(',', $argv[2] ?? ''));
$here = __DIR__; $site = getenv('TR_SITE') ?: '/home/u791571885/domains/dar.ink/public_html';
$lk = fopen("$here/flock-" . md5(implode(',', $only)), 'c'); if (!flock($lk, LOCK_EX | LOCK_NB)) { echo "busy\n"; exit(0); }
chdir($site); $_SERVER['REQUEST_TIME_FLOAT'] = microtime(true); $argv = ['dar-sync.php', 'job']; $argc = 2;
require $site . '/dar-sync.php';
$T0 = time(); $BUDGET = (int)(getenv("TR_BUDGET") ?: 230); $left = fn() => $BUDGET - (time() - $T0);
$jb = (string)@file_get_contents("$here/fix.bin"); $job = json_decode((string)openssl_decrypt(substr($jb, 28), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, substr($jb, 0, 12), substr($jb, 12, 16)), true); if (!is_array($job)) { echo "job?\n"; exit(1); }
$st = "$here/fst"; @mkdir($st, 0700, true); $tok = substr(hash('sha256', $K . 'fxtr'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true);
$get = function (string $f) { return is_file($f) ? json_decode(file_get_contents($f), true) : null; };
$SCRIPT = ['ar' => '\p{Arabic}', 'fa' => '\p{Arabic}', 'ur' => '\p{Arabic}', 'ru' => '\p{Cyrillic}', 'hi' => '\p{Devanagari}', 'zh' => '\p{Han}'];
$KEEP = '/^(WhatsApp|Email|Excel|ID|PRO|CRM|EMI|m²|%|[0-9 .,:\/\-+#%²★{}a-z_]+)$/u';
$ph = function (string $s): array { preg_match_all('/\{[a-z]+\}/', $s, $m); $x = $m[0]; sort($x); return $x; };
$done = 0; $total = 0; $fail = []; $calls = 0; $last = '';
foreach ($job['chunks'] as $c) {
    if ($only && !in_array($c['lang'], $only, true)) continue;
    $total++; $f = "$st/{$c['id']}.json"; $r = $get($f); if ($r && !empty($r['ok'])) { $done++; continue; }
    if (($r['tries'] ?? 0) >= 10) { $fail[] = "{$c['id']}: " . implode(' | ', array_slice($r['errors'] ?? [], 0, 3)); continue; }
    if ($left() < 90) continue;
    $L = $c['lang']; $ln = $job['langs'][$L];
    $send = array_map(fn($x) => [$x[0] . '.' . $x[2], str_starts_with($x[1 + 2], '★') ? ltrim(mb_substr($x[3], 1)) : $x[3]], $c['items']);
    $sys = "FX-STAGE: kit-translate-fix\nThese texts of a premium real-estate Excel workbook were left in English in its $ln version. Translate each into $ln as a native professional of that market writes "
        . "(the terms property offices there really use; column headers 1–4 words, drop-down choices 1–3 words; natural, concise, never word for word).\n"
        . "Rules:\n1. Answer with ONE JSON object {\"t\":[…]}: exactly one string per input item, in the same order. Each input item is [hint key, English].\n"
        . "2. Keep every {placeholder} exactly. Keep WhatsApp, Email, Excel, m², %, numbers and codes as they are.\n"
        . "3. Text inside «…» names a tab: write that tab's $ln name (from the list below), inside «…».\n"
        . "4. An item whose key starts with " . implode(', ', array_map(fn($s) => "\"$s.\"", $c['sheets'])) . " is an Excel tab name: at most 31 characters, none of [ ] : * ? / \\, different from every other tab.\n"
        . (isset($SCRIPT[$L]) ? "5. Write every item in $ln script; English words stay only for WhatsApp, Email, Excel and codes.\n" : "5. Only if an item is correctly written exactly the same in $ln (a word the market really uses as it is), return it unchanged.\n")
        . "THE TABS OF THIS FILE (English → $ln now): " . implode(' | ', array_map(fn($t) => $t[0] . ' → ' . $t[1], $c['tabs'])) . "\nWHAT EACH SECTION IS: " . json_encode($c['hints'], JSON_UNESCAPED_UNICODE);
    $usr = json_encode($send, JSON_UNESCAPED_UNICODE) . "\nTranslate now. One JSON object only." . (!empty($r['errors']) ? "\nYour previous answer was refused: " . implode('; ', array_slice($r['errors'], 0, 12)) : '');
    $a = fx_ai($sys, $usr, 'standard', 7000, (int)min(150, $left() - 10), ['temp' => 0.3]); $calls++;
    $o = $a['j']['t'] ?? null; $e = [];
    if (isset($a['err'])) $e[] = 'ai: ' . $a['err'];
    elseif (!is_array($o) || count($o) !== count($c['items'])) $e[] = 'exactly ' . count($c['items']) . ' strings needed in "t", got ' . (is_array($o) ? count($o) : 0);
    else foreach ($c['items'] as $i => [$sec, $idx, $key, $en]) {
        $v = $o[$i]; if (!is_string($v) || trim($v) === '') { $e[] = "item $i ($sec.$key) empty"; continue; }
        if (str_starts_with($en, '★') && !str_starts_with(ltrim($v), '★')) $o[$i] = $v = '★ ' . ltrim($v);
        if ($ph($v) !== $ph($en)) $e[] = "item $i ($sec.$key): keep exactly the placeholders " . implode(' ', $ph($en) ?: ['(none)']);
        if (in_array($sec, $c['sheets'], true) && (mb_strlen($v) > 31 || preg_match('#[\[\]:*?/\\\\]#u', $v))) $e[] = "item $i ($sec.$key): a tab name at most 31 characters without [ ] : * ? / \\";
        if (isset($SCRIPT[$L]) && !preg_match('/' . $SCRIPT[$L] . '/u', $v) && !preg_match($KEEP, trim($v))) $e[] = "item $i ($sec.$key) still in English: «" . mb_substr($v, 0, 60) . '»';
        if (isset($SCRIPT[$L]) === false && trim($v) === trim($en) && mb_strlen($en) > 40) $e[] = "item $i ($sec.$key): a whole sentence left in English — translate it";
    }
    if ($e) { file_put_contents($f, json_encode(['ok' => false, 'tries' => ($r['tries'] ?? 0) + (isset($a['err']) && (str_contains($a['err'], 'no_time') || str_contains($a['err'], 'unavailable')) ? 0 : 1), 'errors' => array_slice($e, 0, 20)], JSON_UNESCAPED_UNICODE)); $last = "{$c['id']}: " . $e[0]; continue; }
    file_put_contents($f, json_encode(['ok' => true, 'out' => array_values($o), 'by' => $a['by'] ?? '', 'at' => gmdate('c')], JSON_UNESCAPED_UNICODE)); $done++;
}
$files = []; $pairs = [];
foreach ($job['chunks'] as $c) $pairs[$c['lang'] . '-' . $c['kind']][] = $c;
foreach ($pairs as $p => $cs) { if ($only && !in_array($cs[0]['lang'], $only, true)) continue; $m = []; $ok = true;
    foreach ($cs as $c) { $r = $get("$st/{$c['id']}.json"); if (!$r || empty($r['ok'])) { $ok = false; break; } foreach ($c['items'] as $i => [$sec, $idx]) $m[$sec][(string)$idx] = $r['out'][$i]; }
    if (!$ok) continue; $iv = random_bytes(12); $tag = '';
    $ct = openssl_encrypt(json_encode($m, JSON_UNESCAPED_UNICODE), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag); file_put_contents("$pub/F-$p.json.bin", $iv . $tag . $ct); $files[] = "F-$p.json"; }
@file_put_contents("$pub/fstatus-" . ($only ? implode('', $only) : 'all') . '.json', json_encode(['at' => gmdate('c'), 'done' => $done, 'total' => $total, 'files' => $files, 'failed' => $fail, 'calls' => $calls, 'last_note' => mb_substr($last, 0, 300)], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
echo json_encode(['done' => $done, 'total' => $total, 'files' => count($files), 'calls' => $calls]), "\n";
