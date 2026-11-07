<?php
// One-off read (2026-11-07, the owner: «هل المنصة حاليا تعمل وتقوم بإنتاج منتجات اخرى»): why the factory drops its files. Read-only —
// nothing in Dar changes. The result is encrypted for Claude's pick-up. Run: php fxdiag.php <base64 key>
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$here = __DIR__; $site = '/home/u791571885/domains/dar.ink/public_html';
chdir($site); $_SERVER['REQUEST_TIME_FLOAT'] = microtime(true); $argv = ['dar-sync.php', 'job']; $argc = 2;
require $site . '/dar-sync.php';
$S = ['at' => gmdate('c'), 'version' => defined('SYNC_VERSION') ? SYNC_VERSION : ''];
try {
  $S['items'] = [];
  foreach (q("SELECT id, profession, stage, status, round, score, repairs, fails, next_at, errors, x, created, updated FROM fx_items ORDER BY created DESC LIMIT 60")->fetchAll() as $r) {
    $e = json_decode((string)$r['errors'], true) ?: []; $x = json_decode((string)$r['x'], true) ?: [];
    $S['items'][] = ['id' => $r['id'], 'p' => $r['profession'], 'stage' => $r['stage'], 'status' => $r['status'], 'round' => (int)$r['round'], 'score' => (int)$r['score'], 'fails' => (int)$r['fails'],
      'repairs' => (int)$r['repairs'], 'next_at' => (int)$r['next_at'] > time() ? gmdate('c', (int)$r['next_at']) : '', 'created' => gmdate('c', (int)$r['created']), 'updated' => gmdate('c', (int)$r['updated']),
      'dropped' => mb_substr((string)($x['dropped'] ?? ''), 0, 300), 'part' => $x['suite']['part'] ?? null, 'of' => $x['suite']['of'] ?? null,
      'last_errors' => array_map(fn($a) => ['at' => $a['at'] ?? '', 'stage' => $a['stage'] ?? '', 'msg' => mb_substr((string)($a['msg'] ?? ''), 0, 400)], array_slice($e, -6))];
  }
  $S['claims'] = q('SELECT id, w, at FROM fx_claims')->fetchAll();
  $S['meta'] = []; foreach (q("SELECT k, v FROM meta WHERE k LIKE 'fx%'")->fetchAll() as $m) $S['meta'][$m['k']] = mb_substr((string)$m['v'], 0, 300);
  $S['rank'] = q('SELECT COUNT(*) n, MAX(at) last FROM fx_rank')->fetch();
  $S['ai_3h'] = q("SELECT provider, SUM(ok) ok, SUM(1 - ok) fail FROM ai_log WHERE at > ? GROUP BY provider ORDER BY 2 DESC", [time() - 10800])->fetchAll();
  $S['ai_fail_3h'] = q("SELECT provider, model, code, COUNT(*) n FROM ai_log WHERE at > ? AND ok = 0 GROUP BY provider, model, code ORDER BY n DESC LIMIT 20", [time() - 10800])->fetchAll();
} catch (Throwable $e) { $S['err'] = $e->getMessage(); }
$f = data_dir() . '/server-errors.log'; if (is_file($f)) { $L = file($f); $S['faults'] = array_map(fn($l) => mb_substr(trim($l), 0, 400), array_values(array_filter(array_slice($L, -400), fn($l) => strpos($l, 'fx') !== false))); $S['faults'] = array_slice($S['faults'], -40); }
$tok = substr(hash('sha256', $K . 'fxtr'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true); $iv = random_bytes(12); $tag = '';
$ct = openssl_encrypt(json_encode($S, JSON_UNESCAPED_UNICODE | JSON_PARTIAL_OUTPUT_ON_ERROR), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag); file_put_contents("$pub/fxdiag.json.bin", $iv . $tag . $ct); echo "ok\n";
