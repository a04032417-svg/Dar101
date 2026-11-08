<?php
// Read-only (2026-11-08): the models resting (provider|model, key names hashed), the request caps and the lanes of Gemini, Groq,
// Mistral and OpenRouter. Nothing in Dar changes. Run: php fxdiag7.php <base64 key>
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$site = '/home/u791571885/domains/dar.ink/public_html';
chdir($site); $_SERVER['REQUEST_TIME_FLOAT'] = microtime(true); $argv = ['dar-sync.php', 'job']; $argc = 2;
require $site . '/dar-sync.php';
$S = ['at' => gmdate('c'), 'version' => defined('SYNC_VERSION') ? SYNC_VERSION : ''];
try {
  $cfg = ai_cfg(); $S['mrest'] = []; foreach ((array)($cfg['mrest'] ?? []) as $k => $u) { if ((int)$u <= time()) continue; $p = explode('|', (string)$k); $S['mrest'][] = ['p' => $p[0] ?? '', 'm' => $p[1] ?? '', 'key' => isset($p[2]) ? substr(hash('sha256', $p[2]), 0, 6) : '', 'min' => (int)ceil(((int)$u - time()) / 60)]; }
  $S['caps'] = []; foreach ((array)($cfg['caps'] ?? []) as $k => $c) if (preg_match('/^(gemini|groq|mistral|openrouter|anthropic)\|/', (string)$k)) $S['caps'][$k] = $c;
  $S['lanes'] = []; foreach (['gemini', 'groq', 'mistral', 'openrouter'] as $id) foreach (['deep', 'standard'] as $t) $S['lanes'][$id][$t] = ai_lane_models($cfg, $id, $t);
  $S['scores'] = []; try { foreach (q("SELECT * FROM ai_scores WHERE provider IN ('gemini','groq') LIMIT 40")->fetchAll() as $r) $S['scores'][] = $r; } catch (Throwable $e) { $S['scores'] = 'n/a ' . $e->getMessage(); }
} catch (Throwable $e) { $S['err'] = $e->getMessage() . ' @' . $e->getLine(); }
$tok = substr(hash('sha256', $K . 'fxtr'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true); $iv = random_bytes(12); $tag = '';
$ct = openssl_encrypt(gzencode(json_encode($S, JSON_UNESCAPED_UNICODE | JSON_PARTIAL_OUTPUT_ON_ERROR), 9), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag);
file_put_contents("$pub/fxdiag8.txt", base64_encode($iv . $tag . $ct)); echo "ok\n";
