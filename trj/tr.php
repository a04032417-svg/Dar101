<?php
// One-off job, 2026-11-07: Dar's own AI translates the texts of the two real-estate Excel kits (Agent PRO v3, Developer v2) into
// 14 languages — a few requests per run, checked here, retried with the reasons — and leaves each finished file, encrypted, where
// Claude's pick-up fetches it. Nothing in Dar changes: this only calls fx_ai(). Run: php tr.php <base64 key> <langs,comma>
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$only = array_filter(explode(',', $argv[2] ?? ''));
$here = __DIR__; $site = getenv('TR_SITE') ?: '/home/u791571885/domains/dar.ink/public_html';
$lk = fopen("$here/lock-" . md5(implode(',', $only)), 'c'); if (!flock($lk, LOCK_EX | LOCK_NB)) { echo "busy\n"; exit(0); }
chdir($site); $_SERVER['REQUEST_TIME_FLOAT'] = microtime(true); $argv = ['dar-sync.php', 'job']; $argc = 2;
require $site . '/dar-sync.php';
$T0 = time(); $BUDGET = 225; $left = fn() => $BUDGET - (time() - $T0);
$jb = (string)@file_get_contents("$here/job.bin"); $job = json_decode((string)openssl_decrypt(substr($jb, 28), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, substr($jb, 0, 12), substr($jb, 12, 16)), true); if (!is_array($job)) { echo "job?\n"; exit(1); } $st = "$here/st"; @mkdir($st, 0700, true);
$tok = substr(hash('sha256', $K . 'fxtr'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true);
$langs = $job['langs']; if ($only) $langs = array_intersect_key($langs, array_flip($only));
$byId = []; foreach ($job['chunks'] as $c) $byId[$c['id']] = $c;
$get = function (string $code, string $id) use ($st) { $f = "$st/$code/$id.json"; return is_file($f) ? json_decode(file_get_contents($f), true) : null; };
$put = function (string $code, string $id, array $v) use ($st) { @mkdir("$st/$code", 0700, true); file_put_contents("$st/$code/$id.json", json_encode($v, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT)); };
$ph = function (string $s): array { preg_match_all('/\{[a-z]+\}/', $s, $m); $x = $m[0]; sort($x); return $x; };
$names = function (string $code, string $kind) use ($get): array { // the tab names of that file, once its first request is done
    $r = []; $a = $get($code, $kind . '-0'); if ($a && !empty($a['ok'])) foreach ($a['out'] as $v) $r = array_merge($r, $v);
    if ($kind === 'dev') { $p = $get($code, 'pro-0'); if ($p && !empty($p['ok'])) $r = array_merge($r, array_slice($p['out']['sheet3'], 0, 5)); }
    return $r;
};
$check = function (array $c, $o, string $code) use ($ph, $names): array {
    $e = []; if (!is_array($o)) return ['not a JSON object'];
    foreach ($c['texts'] as $sec => $items) {
        $g = $o[$sec] ?? null; if (!is_array($g) || array_values($g) !== $g) { $e[] = "section \"$sec\" missing or not an array"; continue; }
        if (count($g) !== count($items)) { $e[] = "section \"$sec\": " . count($g) . ' strings, ' . count($items) . ' expected (one per input item, same order)'; continue; }
        foreach ($items as $i => [$k, $en]) {
            $v = $g[$i]; if (!is_string($v) || trim($v) === '') { $e[] = "$sec[$i] ($k) empty"; continue; }
            if ($ph($v) !== $ph($en)) $e[] = "$sec[$i] ($k): keep exactly the placeholders " . implode(' ', $ph($en) ?: ['(none)']) . ' — got: ' . mb_substr($v, 0, 80);
            if (str_starts_with($en, '★') && !str_starts_with(ltrim($v), '★')) $e[] = "$sec[$i] ($k) must start with ★";
        }
    }
    foreach (array_diff(array_keys($o), array_keys($c['texts'])) as $x) $e[] = "unknown section \"$x\"";
    if (!empty($c['sheets']) && !$e) {
        $all = []; foreach ($c['texts'] as $sec => $_) $all = array_merge($all, $o[$sec]);
        $other = $c['kind'] === 'dev' ? $names($code, 'dev') : []; // (the PRO staff tabs that the developer file shows too)
        foreach ($all as $n) if (mb_strlen($n) > 31 || preg_match('#[\[\]:*?/\\\\]#u', $n) || str_starts_with($n, "'") || str_ends_with($n, "'")) $e[] = "tab name not allowed by Excel (≤31 characters, none of [ ] : * ? / \\): $n";
        $low = array_map('mb_strtolower', array_merge($all, $other)); if (count(array_unique($low)) !== count($low)) $e[] = 'two tabs share a name: ' . implode(', ', array_keys(array_filter(array_count_values($low), fn($n) => $n > 1)));
    }
    return $e;
};
$prompt = function (array $c, string $code, string $lname) use ($job, $names): string {
    $n = $c['kind'] === 'pro' ? 'pro' : 'dev'; $tabs = $names($code, $c['kind']);
    $s = "FX-STAGE: kit-translate\nYou translate the texts of a premium Excel workbook for {$job['products'][$n]}. Translate from English into $lname.\n"
       . "These are the words a real-estate professional sees in Excel: tab names, column headers, drop-down choices, instructions, dashboard labels, ready WhatsApp messages and sample rows. "
       . "Write as a native professional of that market writes: the terms property offices there really use, natural and concise (column headers 1–4 words, drop-down choices 1–3 words), never word for word, never explaining, nothing added or left out.\n"
       . "Rules:\n1. Answer with ONE JSON object: the same section keys as in \"texts\", each an array with exactly as many strings as the input, in the same order. Each input item is [key, English]; the key is only a hint — answer the translated string alone.\n"
       . "2. Keep every {placeholder} exactly as written, e.g. {name} {agent} {date} — never translate, add or drop one.\n3. A text that starts with ★ keeps the ★ at its start.\n"
       . "4. Text inside «…» names a tab or a column: write that tab's or column's translated name, also inside «…»." . ($tabs ? ' The tabs of this file are named: ' . implode(' | ', $tabs) . '.' : '') . "\n"
       . "5. Keep as they are: WhatsApp, Email, m², %, numbers, currency codes and codes such as ID.\n6. \"hints\" says what each section is: follow it.\n";
    if (!empty($c['sheets'])) $s .= "7. These are Excel tab names: each at most 31 characters (best under 20), none of [ ] : * ? / \\, all different from each other"
       . ($c['kind'] === 'dev' && $tabs ? ' and from these tabs of the same file: ' . implode(' | ', $tabs) : '') . ".\n";
    return $s;
};
$done = 0; $total = 0; $fail = []; $calls = 0; $last = '';
$order = []; foreach ($job['chunks'] as $c) foreach ($langs as $code => $ln) $order[] = [$code, $c]; // (every language's tab names first: the rest uses them)
foreach ($order as [$code, $c]) {
    $total++; $r = $get($code, $c['id']); if ($r && !empty($r['ok'])) { $done++; continue; }
    if (($r['tries'] ?? 0) >= 8) { $fail[] = "$code/{$c['id']}: " . implode(' | ', array_slice($r['errors'] ?? [], 0, 3)); continue; }
    if (empty($c['sheets'])) { $z = $get($code, $c['kind'] . '-0'); if (!$z || empty($z['ok'])) continue; }
    if ($c['kind'] === 'dev' && !empty($c['sheets'])) { $z = $get($code, 'pro-0'); if (!$z || empty($z['ok'])) continue; }
    if ($left() < 75) continue;
    $usr = json_encode(['hints' => $c['hints'], 'texts' => $c['texts']], JSON_UNESCAPED_UNICODE) . "\nTranslate now. One JSON object only." . (!empty($r['errors']) ? "\nYour previous answer was refused: " . implode('; ', array_slice($r['errors'], 0, 12)) : '');
    $a = fx_ai($prompt($c, $code, $langs[$code]), $usr, 'standard', 7000, (int)min(150, $left() - 10), ['temp' => 0.3]); $calls++;
    $o = $a['j'] ?? null; if (is_array($o) && isset($o['texts']) && is_array($o['texts']) && count($o) <= 2) $o = $o['texts'];
    $e = isset($a['err']) ? ['ai: ' . $a['err']] : $check($c, $o, $code);
    if ($e) { $put($code, $c['id'], ['ok' => false, 'tries' => ($r['tries'] ?? 0) + (isset($a['err']) && str_contains($a['err'], 'no_time') ? 0 : 1), 'errors' => $e, 'by' => $a['by'] ?? '']); $last = "$code/{$c['id']}: " . $e[0]; continue; }
    $put($code, $c['id'], ['ok' => true, 'out' => $o, 'by' => $a['by'] ?? '', 'at' => gmdate('c')]); $done++;
}
// each finished file, encrypted for the pick-up: {section: [strings]} in the file's own order
$files = [];
foreach ($langs as $code => $ln) foreach (['pro', 'dev'] as $kind) {
    $m = []; $ok = true; foreach ($job['chunks'] as $c) if ($c['kind'] === $kind) { $r = $get($code, $c['id']); if (!$r || empty($r['ok'])) { $ok = false; break; } $m += $r['out']; }
    if (!$ok) continue; $o = []; foreach ($job['order'][$kind] as $sec) if (isset($m[$sec])) $o[$sec] = $m[$sec];
    $name = ($kind === 'pro' ? $code : 'dev-' . $code) . '.json'; $iv = random_bytes(12); $tag = '';
    $ct = openssl_encrypt(json_encode($o, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag);
    file_put_contents("$pub/$name.bin", $iv . $tag . $ct); $files[] = $name;
}
$sfile = data_dir() . '/fx/tr-status-' . ($only ? implode('', $only) : 'all') . '.json';
$sj = json_encode(['at' => gmdate('c'), 'done' => $done, 'total' => $total, 'files' => $files, 'failed' => $fail, 'calls' => $calls, 'last_note' => mb_substr($last, 0, 300)], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
@file_put_contents("$pub/status-" . ($only ? implode('', $only) : 'all') . '.json', $sj);
@file_put_contents($sfile, json_encode(['at' => gmdate('c'), 'done' => $done, 'total' => $total, 'files' => $files, 'failed' => $fail, 'calls' => $calls, 'last_note' => mb_substr($last, 0, 300)], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
echo json_encode(['done' => $done, 'total' => $total, 'files' => count($files), 'calls' => $calls]), "\n";
