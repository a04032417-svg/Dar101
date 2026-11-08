<?php
// Read-only (2026-11-08): which validator rules and critic fixes keep the factory's files from passing, and which caller still asks
// a retired model. Nothing in Dar changes. Run: php fxdiag3.php <base64 key>  → fxtr/<tok>/fxdiag3.txt (base64 iv|tag|AES-GCM(gzip(json)))
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$site = '/home/u791571885/domains/dar.ink/public_html';
chdir($site); $_SERVER['REQUEST_TIME_FLOAT'] = microtime(true); $argv = ['dar-sync.php', 'job']; $argc = 2;
require $site . '/dar-sync.php';
$S = ['at' => gmdate('c'), 'version' => defined('SYNC_VERSION') ? SYNC_VERSION : ''];
try {
  $S['cfg'] = function_exists('fx_cfg') ? fx_cfg() : null; $S['workers'] = function_exists('fx_workers') ? fx_workers() : null; $S['workers_set'] = meta_get('fx_workers');
  foreach (['fx_last', 'fx_last_1', 'fx_last_2', 'fx_last_3'] as $k) $S['last'][$k] = mb_substr((string)meta_get($k), 0, 1200);
  $S['items'] = [];
  foreach (q("SELECT * FROM fx_items WHERE updated > ? ORDER BY updated DESC LIMIT 30", [time() - 86400])->fetchAll() as $r) {
    $e = json_decode((string)$r['errors'], true) ?: []; $x = json_decode((string)$r['x'], true) ?: []; $cr = json_decode((string)$r['critique'], true) ?: [];
    $notes = []; foreach (array_slice($e, -14) as $n) $notes[] = ($n['at'] ?? '') . ' ' . ($n['stage'] ?? '') . ': ' . mb_substr((string)($n['msg'] ?? ''), 0, 700);
    $S['items'][] = ['id' => $r['id'], 'stage' => $r['stage'], 'status' => $r['status'], 'round' => (int)$r['round'], 'score' => (int)$r['score'], 'fails' => (int)$r['fails'],
      'next_at' => (int)$r['next_at'] ? gmdate('H:i', (int)$r['next_at']) : '', 'by' => $x['by'] ?? null, 'scores' => $x['scores'] ?? null, 'vfails' => $x['vfails'] ?? null, 'parks' => $x['parks'] ?? null,
      'crit' => ['verdict' => mb_substr((string)($cr['verdict'] ?? ''), 0, 300), 'fixes' => array_map(fn($f) => mb_substr(is_scalar($f) ? (string)$f : json_encode($f), 0, 300), array_slice((array)($cr['fixes'] ?? []), 0, 10)), 'gate' => $cr['gate'] ?? null, 'by' => $cr['by'] ?? ''],
      'notes' => $notes];
  }
  $t1 = (time() - 3600) * 1000; $t3 = (time() - 10800) * 1000;
  $S['retired_callers'] = q("SELECT ns, uid, COUNT(*) n FROM ai_log WHERE model = 'gemini-2.5-flash' AND at > ? GROUP BY ns, uid ORDER BY n DESC LIMIT 10", [$t3])->fetchAll();
  $S['ai_1h'] = q("SELECT provider, model, SUM(ok) ok, SUM(1 - ok) bad FROM ai_log WHERE at > ? GROUP BY provider, model ORDER BY bad DESC LIMIT 30", [$t1])->fetchAll();
  $S['ai_ns_1h'] = q("SELECT ns, SUM(ok) ok, SUM(1 - ok) bad FROM ai_log WHERE at > ? GROUP BY ns ORDER BY bad DESC LIMIT 15", [$t1])->fetchAll();
  $S['at_unit'] = q("SELECT MAX(at) m FROM ai_log")->fetch();
} catch (Throwable $e) { $S['err'] = $e->getMessage() . ' @' . $e->getLine(); }
$tok = substr(hash('sha256', $K . 'fxtr'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true); $iv = random_bytes(12); $tag = '';
$ct = openssl_encrypt(gzencode(json_encode($S, JSON_UNESCAPED_UNICODE | JSON_PARTIAL_OUTPUT_ON_ERROR), 9), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag);
file_put_contents("$pub/fxdiag3.txt", base64_encode($iv . $tag . $ct)); echo "ok\n";
