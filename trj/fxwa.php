<?php
// Read-only (2026-11-09): why the platform's WhatsApp number answers its owner but not other people. Reads the channel settings
// (test mode), the agent switch, the linked session, and the last 48 h of the inbound log by status — numbers hashed, no message
// text. Nothing in Dar changes. Run: php fxwa.php <base64 key>
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$site = '/home/u791571885/domains/dar.ink/public_html';
chdir($site); $_SERVER['REQUEST_TIME_FLOAT'] = microtime(true); $argv = ['dar-sync.php', 'job']; $argc = 2;
require $site . '/dar-sync.php';
$H = fn($n) => substr(hash('sha256', 'fxwa|' . preg_replace('/\D/', '', (string)$n)), 0, 6) . '…' . substr(preg_replace('/\D/', '', (string)$n), -2);
$S = ['at' => gmdate('c'), 'version' => defined('SYNC_VERSION') ? SYNC_VERSION : ''];
$sec = function (string $k, callable $f) use (&$S) { try { $S[$k] = $f(); } catch (Throwable $e) { $S[$k] = 'err: ' . substr($e->getMessage(), 0, 200) . ' @' . $e->getLine(); } };
$sec('channels', function () { $c = chan_cfg(); return ['test' => $c['test'], 'mode' => $c['mode'] ?? '', 'wa_on' => $c['whatsapp']['on'] ?? null, 'wa_meta_phone_id' => ($c['whatsapp']['phone_id'] ?? '') !== '', 'wa_ready' => chan_ready('whatsapp', $c)]; });
$sec('agent', function () { $x = platform_rec()->wa_agent ?? null; return ['all' => function_exists('wa_agent_all') ? wa_agent_all() : null, 'keys' => is_object($x) ? array_keys(get_object_vars($x)) : gettype($x), 'reply_all' => is_object($x) && property_exists($x, 'reply_all') ? $x->reply_all : '(unset)']; });
$sec('gateway', function () use ($H) {
  $g = wag_cfg(); $out = ['on' => $g['on'], 'url' => $g['url'] !== '', 'secret' => $g['secret'] !== '', 'ready' => wag_ready(), 'platform_open' => wag_platform_open(), 'carry_clients' => wag_carry_clients(),
    'wag_in_at' => (int)meta_get('wag_in_at'), 'wag_tick_at' => (int)meta_get('wag_tick_at'), 'wa_in_at' => (int)meta_get('wa_in_at'), 'now' => time(), 'sessions' => []];
  foreach (q('SELECT sid, ns, status, phone, mode, at FROM wag_sessions')->fetchAll() as $r) $out['sessions'][] = ['sid' => strlen($r['sid']) > 12 ? substr($r['sid'], 0, 4) . '…' : $r['sid'], 'ns' => strlen($r['ns']) > 12 ? substr($r['ns'], 0, 4) . '…' : $r['ns'], 'status' => $r['status'], 'phone' => $r['phone'] !== '' ? $H($r['phone']) : '', 'mode' => $r['mode'], 'min_ago' => (int)((now_ms() - (int)$r['at']) / 60000)];
  $out['events_24h'] = []; foreach (q('SELECT type, COUNT(*) n, MAX(at) last FROM wag_events WHERE at > ? GROUP BY type', [now_ms() - 86400000])->fetchAll() as $r) $out['events_24h'][$r['type']] = ['n' => (int)$r['n'], 'min_ago' => (int)((now_ms() - (int)$r['last']) / 60000)];
  return $out;
});
$sec('inbound_48h', function () use ($H) {
  wa_in_db(); $own = function_exists('wag_platform_phone') ? wag_platform_phone() : '';
  $rows = q('SELECT id, frm, status, reply, at, done_at FROM wa_in WHERE at > ? ORDER BY at DESC LIMIT 400', [now_ms() - 2 * 86400000])->fetchAll();
  $by = []; $last = [];
  foreach ($rows as $r) {
    $f = (string)$r['frm']; $who = $f === $own ? 'own' : (function_exists('talk_owner_of') && talk_owner_of('whatsapp', $f) ? 'owner' : (function_exists('wa_who') && wa_who($f) ? 'known' : 'other'));
    $by[$who][$r['status']] = ($by[$who][$r['status']] ?? 0) + 1;
    if (count($last) < 25) $last[] = ['min_ago' => (int)((now_ms() - (int)$r['at']) / 60000), 'from' => $H($f), 'who' => $who, 'status' => $r['status'], 'reply_len' => mb_strlen((string)$r['reply']), 'took_s' => $r['done_at'] ? (int)(((int)$r['done_at'] - (int)$r['at']) / 1000) : null];
  }
  return ['by_sender' => $by, 'last' => $last];
});
$sec('agent_state', function () use ($H) {
  $out = ['human_2h' => 0, 'retry' => [], 'recent' => []];
  foreach (q("SELECT k, v FROM meta WHERE k LIKE 'wa_agent_h:%'")->fetchAll() as $r) if ((int)$r['v'] > now_ms() - WA_AGENT_HUMAN_H * 3600000) $out['human_2h']++;
  foreach (q("SELECT k, v FROM meta WHERE k LIKE 'wa_agent_rt:%' LIMIT 20")->fetchAll() as $r) { $x = json_decode((string)$r['v'], true); $out['retry'][] = ['num' => $H(substr($r['k'], 12)), 'n' => (int)($x['n'] ?? 0), 'min_ago' => (int)((now_ms() - (int)($x['at'] ?? 0)) / 60000)]; }
  foreach (function_exists('wa_recent') ? wa_recent(10) : [] as $x) {
    $th = wa_agent_thread((string)$x['num']); $m = array_slice(is_array($th['m'] ?? null) ? $th['m'] : [], -6);
    $out['recent'][] = ['num' => $H($x['num']), 'min_ago' => (int)((now_ms() - (int)$x['at']) / 60000), 'quiet' => function_exists('waa_quiet') ? waa_quiet((string)$x['num']) : null,
      'last' => array_map(fn($y) => ['r' => $y['r'] ?? '', 'by' => $y['by'] ?? '', 'min_ago' => (int)((now_ms() - (int)($y['at'] ?? 0)) / 60000), 'len' => mb_strlen((string)($y['t'] ?? ''))], $m)];
  }
  return $out;
});
$sec('ai_2h', function () {
  $o = []; foreach (q('SELECT provider, ok, COUNT(*) n, AVG(ms) ms FROM ai_log WHERE at > ? GROUP BY provider, ok', [now_ms() - 7200000])->fetchAll() as $r) $o[$r['provider']][$r['ok'] ? 'ok' : 'fail'] = [(int)$r['n'], (int)$r['ms']];
  $codes = []; foreach (q('SELECT provider, code, COUNT(*) n FROM ai_log WHERE at > ? AND ok = 0 GROUP BY provider, code ORDER BY n DESC LIMIT 25', [now_ms() - 7200000])->fetchAll() as $r) $codes[] = $r['provider'] . ' ' . $r['code'] . ' ×' . $r['n'];
  return ['by_provider' => $o, 'fail_codes' => $codes];
});
$sec('faults', function () {
  $f = data_dir() . '/server-errors.log'; if (!is_file($f)) return 'no file'; $sz = filesize($f); $h = fopen($f, 'r'); fseek($h, max(0, $sz - 400000)); $t = stream_get_contents($h); fclose($h);
  $o = []; foreach (array_reverse(explode("\n", trim($t))) as $l) { $j = json_decode($l, true); if (!is_array($j)) continue; if (!preg_match('/wag|wa_|waa|talk|chan|duty/i', (string)($j['where'] ?? ''))) continue; if (strtotime((string)$j['t']) < time() - 172800) break; $o[] = $j['t'] . ' ' . $j['where'] . ' ' . preg_replace('/\d{8,}/', '#', substr((string)$j['msg'], 0, 180)); if (count($o) >= 30) break; }
  return $o;
});
$tok = substr(hash('sha256', $K . 'fxtr'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true); $iv = random_bytes(12); $tag = '';
$ct = openssl_encrypt(gzencode(json_encode($S, JSON_UNESCAPED_UNICODE | JSON_PARTIAL_OUTPUT_ON_ERROR), 9), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag);
file_put_contents("$pub/fxwa.txt", base64_encode($iv . $tag . $ct)); echo "ok\n";
