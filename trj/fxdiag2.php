<?php
// Read-only (2026-11-08, the owner: «كم ملف أنتجت؟»): why the factory drops files — compact. Nothing in Dar changes.
// Run: php fxdiag2.php <base64 key>  → fxtr/<tok>/fxdiag2.txt (base64 of iv|tag|AES-256-GCM(gzip(json)))
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$site = '/home/u791571885/domains/dar.ink/public_html';
chdir($site); $_SERVER['REQUEST_TIME_FLOAT'] = microtime(true); $argv = ['dar-sync.php', 'job']; $argc = 2;
require $site . '/dar-sync.php';
$S = ['at' => gmdate('c'), 'version' => defined('SYNC_VERSION') ? SYNC_VERSION : ''];
try {
  $S['items'] = [];
  foreach (q("SELECT id, stage, status, round, score, fails, errors, x, created, updated FROM fx_items WHERE created > ? ORDER BY created DESC LIMIT 80", [time() - 43200])->fetchAll() as $r) {
    $e = json_decode((string)$r['errors'], true) ?: []; $x = json_decode((string)$r['x'], true) ?: []; $le = end($e) ?: [];
    $S['items'][] = [$r['id'], $r['stage'], $r['status'], (int)$r['round'], (int)$r['score'], (int)$r['fails'], gmdate('H:i', (int)$r['created']), gmdate('H:i', (int)$r['updated']),
      mb_substr((string)($x['dropped'] ?? ''), 0, 160), ($le['stage'] ?? '') . ': ' . mb_substr((string)($le['msg'] ?? ''), 0, 200)];
  }
  $S['ai_3h'] = q("SELECT provider, SUM(ok) ok, SUM(1 - ok) fail FROM ai_log WHERE at > ? GROUP BY provider ORDER BY 2 DESC", [time() - 10800])->fetchAll();
  $S['ai_fail_3h'] = q("SELECT provider, model, code, COUNT(*) n FROM ai_log WHERE at > ? AND ok = 0 GROUP BY provider, model, code ORDER BY n DESC LIMIT 12", [time() - 10800])->fetchAll();
  $S['workers'] = function_exists('fx_workers') ? fx_workers() : null;
} catch (Throwable $e) { $S['err'] = $e->getMessage(); }
$f = data_dir() . '/server-errors.log'; if (is_file($f)) { $L = file($f); $S['faults'] = array_slice(array_map(fn($l) => mb_substr(trim($l), 0, 240), array_values(array_filter(array_slice($L, -300), fn($l) => strpos($l, 'fx') !== false))), -12); }
$tok = substr(hash('sha256', $K . 'fxtr'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true); $iv = random_bytes(12); $tag = '';
$ct = openssl_encrypt(gzencode(json_encode($S, JSON_UNESCAPED_UNICODE | JSON_PARTIAL_OUTPUT_ON_ERROR), 9), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag);
file_put_contents("$pub/fxdiag2.txt", base64_encode($iv . $tag . $ct)); echo "ok\n";
