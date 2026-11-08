<?php
// Read-only (2026-11-08): why no strong model answers the factory since 3.34.11 — each provider's readiness and its keys' rest (no key
// values), and the AI log of the last six hours by provider, model and code. Nothing in Dar changes. Run: php fxdiag7.php <base64 key>
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$site = '/home/u791571885/domains/dar.ink/public_html';
chdir($site); $_SERVER['REQUEST_TIME_FLOAT'] = microtime(true); $argv = ['dar-sync.php', 'job']; $argc = 2;
require $site . '/dar-sync.php';
$S = ['at' => gmdate('c'), 'version' => defined('SYNC_VERSION') ? SYNC_VERSION : ''];
try {
  $cfg = ai_cfg(); $ready = ai_ready($cfg); $S['ready'] = $ready; $S['providers'] = [];
  foreach (AI_ORDER as $id) {
    $sl = []; foreach (ai_slots($cfg, $id) as $i => $k) { $st = ai_key_state($cfg, $k); $sl[] = ['i' => $i, 'open' => ai_is_open($k), 'rest_min' => max(0, (int)ceil(((int)($st['rest_until'] ?? 0) - time()) / 60)), 'err' => (string)($st['err'] ?? ''), 'note' => mb_substr((string)($st['note'] ?? ''), 0, 220), 'ok_ago_min' => (int)($st['ok_at'] ?? 0) ? (int)round((time() - (int)$st['ok_at']) / 60) : null]; }
    if (!$sl) continue;
    $S['providers'][$id] = ['strength' => AI_STRENGTH[$id] ?? null, 'ready' => in_array($id, $ready, true), 'enabled' => $cfg['providers'][$id]['enabled'] ?? null, 'deep' => ai_model($cfg, $id, 'deep'), 'standard' => ai_model($cfg, $id, 'standard'), 'keys' => $sl];
  }
  $t6 = (time() - 6 * 3600) * 1000;
  $S['ai_6h'] = q("SELECT provider, model, code, SUM(ok) ok, COUNT(*) n, MAX(at) last FROM ai_log WHERE at > ? GROUP BY provider, model, code ORDER BY n DESC LIMIT 60", [$t6])->fetchAll();
  $S['ai_6h_ns'] = q("SELECT ns, provider, SUM(ok) ok, COUNT(*) n FROM ai_log WHERE at > ? GROUP BY ns, provider ORDER BY n DESC LIMIT 40", [$t6])->fetchAll();
  $S['rank'] = q('SELECT p, score, src, search FROM fx_rank ORDER BY score DESC LIMIT 16')->fetchAll(); $S['drop_epoch'] = meta_get('fx_drop_epoch'); $S['rank_v'] = meta_get('fx_rank_v');
} catch (Throwable $e) { $S['err'] = $e->getMessage() . ' @' . $e->getLine(); }
$tok = substr(hash('sha256', $K . 'fxtr'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true); $iv = random_bytes(12); $tag = '';
$ct = openssl_encrypt(gzencode(json_encode($S, JSON_UNESCAPED_UNICODE | JSON_PARTIAL_OUTPUT_ON_ERROR), 9), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag);
file_put_contents("$pub/fxdiag7.txt", base64_encode($iv . $tag . $ct)); echo "ok\n";
