<?php
// One-off read-only check (2026-11-09, Claude): why Claude answers Dar with «200 empty answer» or a timeout. The same factory-sized
// question is sent to Anthropic three ways with Dar's first Anthropic key; what comes back is described (code, stop reason, the kinds
// of blocks, the length of the text, the time). No key and no answer text is written anywhere. Run: php antchk.php <base64 key>
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$here = __DIR__; $site = '/home/u791571885/domains/dar.ink/public_html';
$lk = fopen("$here/antchk.lock", 'c'); if (!flock($lk, LOCK_EX | LOCK_NB)) { echo "busy\n"; exit(0); }
chdir($site); $_SERVER['REQUEST_TIME_FLOAT'] = microtime(true); $argv = ['dar-sync.php', 'job']; $argc = 2;
require $site . '/dar-sync.php';
$S = ['at' => gmdate('c'), 'version' => defined('SYNC_VERSION') ? SYNC_VERSION : '', 'runs' => []];
try {
  $cfg = ai_cfg(); $slots = ai_slots($cfg, 'anthropic'); $S['slots'] = count($slots);
  $key = $slots ? (string)(vault_get($slots[0]) ?? '') : ''; $S['have_key'] = $key !== '';
  $q = "You design Excel workbooks for one profession. For a hair salon, list as JSON {\"sheets\":[{\"name\":...,\"purpose\":...,\"columns\":[...]}]} the 8 sheets it needs, each with 8 to 12 columns. "
     . str_repeat("Context: a salon tracks clients, stylists, appointments, services, products, commissions, no-shows and rebooking. ", 40);
  $msgs = [['role' => 'user', 'content' => $q]];
  $variants = [
    'sonnet_now' => ['model' => 'claude-sonnet-5-5', 'max_tokens' => 4000, 'messages' => $msgs],
    'sonnet_fix' => ['model' => 'claude-sonnet-5-5', 'max_tokens' => 4000, 'messages' => $msgs, 'thinking' => ['type' => 'between_tools'], 'output_config' => ['effort' => 'low']],
    'fable_fix'  => ['model' => 'claude-fable-5-1', 'max_tokens' => 8000, 'messages' => $msgs, 'output_config' => ['effort' => 'low']],
    'haiku_now'  => ['model' => 'claude-haiku-4-5-20251001', 'max_tokens' => 4000, 'messages' => $msgs],
  ];
  foreach ($variants as $nm => $body) {
    if ($key === '') break; $t = microtime(true);
    [$code, $res, $err] = array_pad(ai_http('POST', 'https://api.anthropic.com/v1/messages', ['Content-Type: application/json', 'x-api-key: ' . $key, 'anthropic-version: 2023-06-01'], json_encode($body), 90), 3, '');
    $j = json_decode((string)$res, true); $types = []; $tl = 0;
    foreach ((array)($j['content'] ?? []) as $b) { $types[] = (string)($b['type'] ?? '?'); if (($b['type'] ?? '') === 'text') $tl += mb_strlen((string)($b['text'] ?? '')); }
    $S['runs'][$nm] = ['code' => (int)$code, 'ms' => (int)round((microtime(true) - $t) * 1000), 'stop' => (string)($j['stop_reason'] ?? ''), 'blocks' => $types, 'text_len' => $tl,
      'usage' => $j['usage'] ?? null, 'error' => mb_substr((string)($j['error']['message'] ?? $err), 0, 300)];
  }
} catch (Throwable $e) { $S['err'] = $e->getMessage() . ' @' . $e->getLine(); }
$tok = substr(hash('sha256', $K . 'fxtr'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true); $iv = random_bytes(12); $tag = '';
$ct = openssl_encrypt(gzencode(json_encode($S, JSON_UNESCAPED_UNICODE | JSON_PARTIAL_OUTPUT_ON_ERROR), 9), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag);
file_put_contents("$pub/antchk.txt", base64_encode($iv . $tag . $ct)); echo "ok\n";
