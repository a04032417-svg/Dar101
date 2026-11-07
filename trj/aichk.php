<?php
// One-off check (2026-11-07, the owner: «يوجد أكثر من حساب لكل مزود … تأكد بأنهم يعملون جميعا بلا استثناء»): every AI key Dar holds,
// provider by provider, is asked one short question with the model Dar uses for the factory (standard and deep), and one factory-sized
// question; plus what Dar's own log says about the last 24 hours. Read-only: nothing in Dar changes. No key is printed — keys are named
// by their position only. The result is encrypted for Claude's pick-up. Run: php aichk.php <base64 key>
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$here = __DIR__; $site = getenv('TR_SITE') ?: '/home/u791571885/domains/dar.ink/public_html';
$lk = fopen("$here/aichk.lock", 'c'); if (!flock($lk, LOCK_EX | LOCK_NB)) { echo "busy\n"; exit(0); }
chdir($site); $_SERVER['REQUEST_TIME_FLOAT'] = microtime(true); $argv = ['dar-sync.php', 'job']; $argc = 2;
require $site . '/dar-sync.php';
$T0 = time(); $left = fn() => 230 - (time() - $T0);
$sf = "$here/aichk-state.json"; $S = is_file($sf) ? (json_decode(file_get_contents($sf), true) ?: []) : []; $S['keys'] = $S['keys'] ?? [];
$cfg = ai_cfg(); $big = str_repeat("A real-estate office tracks clients, listings, viewings, deals, rentals and commissions in one workbook. ", 260); // (~6,000 tokens)
foreach ($cfg['order'] as $id) {
    $slots = ai_slots($cfg, $id); if (!$slots) continue;
    foreach ($slots as $i => $slot) {
        $nm = "$id#" . ($i + 1); if (isset($S['keys'][$nm]['done'])) continue; if ($left() < 45) break 2;
        $st = ai_key_state($cfg, $slot); $open = ai_is_open($slot); $key = $open ? '' : (string)(vault_get($slot) ?? '');
        $row = ['provider' => $id, 'n' => $i + 1, 'enabled' => (bool)($cfg['providers'][$id]['enabled'] ?? false), 'open' => $open, 'resting_until' => (int)($st['rest_until'] ?? 0) > time() ? gmdate('c', (int)$st['rest_until']) : '', 'empty_key' => !$open && $key === ''];
        foreach (['standard', 'deep'] as $tier) {
            $m = ai_model($cfg, $id, $tier); if ($m === '' || ($tier === 'deep' && $m === ai_model($cfg, $id, 'standard'))) continue;
            $t = microtime(true); $r = ai_try($cfg, $id, $key, $m, [['role' => 'user', 'content' => 'Reply with the single word: OK']], ['max_tokens' => 64, 'temperature' => 0], 25);
            $row[$tier] = ['model' => $m, 'code' => (int)$r['code'], 'ms' => (int)round((microtime(true) - $t) * 1000), 'ok' => $r['code'] >= 200 && $r['code'] < 300 && trim((string)$r['text']) !== '', 'err' => mb_substr((string)preg_replace('/(sk|gsk|AIza|key)[-_A-Za-z0-9]{8,}/', '[key]', (string)$r['err']), 0, 160)];
        }
        if (($row['standard']['ok'] ?? false) && $left() > 60) { $m = ai_model($cfg, $id, 'standard'); $t = microtime(true);
            $r = ai_try($cfg, $id, $key, $m, [['role' => 'user', 'content' => $big . "\nHow many sentences above? Answer with one number."]], ['max_tokens' => 64, 'temperature' => 0], 40);
            $row['big'] = ['code' => (int)$r['code'], 'ms' => (int)round((microtime(true) - $t) * 1000), 'ok' => $r['code'] >= 200 && $r['code'] < 300, 'err' => mb_substr((string)preg_replace('/(sk|gsk|AIza|key)[-_A-Za-z0-9]{8,}/', '[key]', (string)$r['err']), 0, 160)]; }
        $row['done'] = 1; $S['keys'][$nm] = $row; file_put_contents($sf, json_encode($S, JSON_UNESCAPED_UNICODE));
    }
}
$all = 0; foreach ($cfg['order'] as $id) $all += count(ai_slots($cfg, $id));
$S['total_keys'] = $all; $S['checked'] = count($S['keys']); $S['at'] = gmdate('c'); $S['order'] = $cfg['order'];
$S['enabled'] = array_values(array_filter($cfg['order'], fn($id) => !empty($cfg['providers'][$id]['enabled']))); $S['ready_now'] = ai_ready($cfg);
$S['caps'] = $cfg['caps'] ?? []; $S['mrest'] = array_filter((array)($cfg['mrest'] ?? []), fn($u) => (int)$u > time());
try { $S['log24'] = q("SELECT provider, SUM(ok) ok, SUM(1 - ok) fail, CAST(AVG(ms) AS INTEGER) ms FROM ai_log WHERE at > ? GROUP BY provider ORDER BY 2 DESC", [time() - 86400])->fetchAll();
      $S['fails24'] = q("SELECT provider, model, code, COUNT(*) n FROM ai_log WHERE at > ? AND ok = 0 GROUP BY provider, model, code ORDER BY n DESC LIMIT 25", [time() - 86400])->fetchAll(); } catch (Throwable $e) { $S['log_err'] = $e->getMessage(); }
file_put_contents($sf, json_encode($S, JSON_UNESCAPED_UNICODE));
$tok = substr(hash('sha256', $K . 'fxtr'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true); $iv = random_bytes(12); $tag = '';
$ct = openssl_encrypt(json_encode($S, JSON_UNESCAPED_UNICODE), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag); file_put_contents("$pub/aichk.json.bin", $iv . $tag . $ct);
echo json_encode(['checked' => $S['checked'], 'total_keys' => $all]), "\n";
