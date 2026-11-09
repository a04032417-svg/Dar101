<?php
// Read-only (2026-11-09), second look at the platform WhatsApp: messages per hour for 4 days, the one unanswered thread's flags
// (no text), and how the gateway (wa.dar.ink) names a sender — its own source lines and the tail of its logs, long numbers masked.
// The gateway's login data is never opened. Nothing changes. Run: php fxwa2.php <base64 key>
$K = base64_decode($argv[1] ?? '', true); if (!$K || strlen($K) !== 32) { echo "key?\n"; exit(1); }
$site = '/home/u791571885/domains/dar.ink/public_html';
chdir($site); $_SERVER['REQUEST_TIME_FLOAT'] = microtime(true); $argv = ['dar-sync.php', 'job']; $argc = 2;
require $site . '/dar-sync.php';
$mask = fn($s) => preg_replace(['/\d{8,}/', '/([A-Za-z0-9_\-]{32,})/', '/((?:secret|token|key|password|passwd|auth)["\']?\s*[:=]\s*["\']?)[^"\'\s,;]+/i'], ['#', '<long>', '$1<hidden>'], (string)$s);
$S = ['at' => gmdate('c')];
$sec = function (string $k, callable $f) use (&$S) { try { $S[$k] = $f(); } catch (Throwable $e) { $S[$k] = 'err: ' . substr($e->getMessage(), 0, 200) . ' @' . $e->getLine(); } };
$sec('per_hour', function () {
  $o = []; foreach (q('SELECT type, at FROM wag_events WHERE at > ? AND sid = ?', [now_ms() - 4 * 86400000, 'platform'])->fetchAll() as $r) { $h = gmdate('m-d H', intdiv((int)$r['at'], 1000)); $o[$h][$r['type']] = ($o[$h][$r['type']] ?? 0) + 1; }
  ksort($o); $in = []; wa_in_db(); $own = wag_platform_phone();
  foreach (q('SELECT frm, status, at FROM wa_in WHERE at > ?', [now_ms() - 4 * 86400000])->fetchAll() as $r) { $h = gmdate('m-d H', intdiv((int)$r['at'], 1000)); $w = $r['frm'] === $own ? 'own' : 'other'; $in[$h][$w . ':' . $r['status']] = ($in[$h][$w . ':' . $r['status']] ?? 0) + 1; }
  ksort($in); return ['events' => $o, 'wa_in' => $in];
});
$sec('thread', function () {
  foreach (wa_recent(3) as $x) { $th = wa_agent_thread((string)$x['num']); $m = is_array($th['m'] ?? null) ? $th['m'] : []; $u = ''; foreach (array_reverse($m) as $y) if (($y['r'] ?? '') === 'user') { $u = (string)($y['t'] ?? ''); break; }
    return ['keys' => array_keys($th), 'auto_at_min' => isset($th['auto_at']) ? (int)((now_ms() - (int)$th['auto_at']) / 60000) : null, 'fresh' => function_exists('waa_fresh') ? waa_fresh($th) : null,
      'auto_rule' => function_exists('waa_auto_reply') ? waa_auto_reply($u, $th) : null, 'lines' => count(array_filter(explode("\n", $u), 'trim')), 'has_link' => (bool)preg_match('#https?://|www\.#', $u), 'who_kind' => isset($th['who']) ? 'set' : '']; }
  return null;
});
$sec('gateway_files', function () use ($mask) {
  $roots = glob('/home/u791571885/domains/wa.dar.ink/*', GLOB_ONLYDIR) ?: []; $out = ['roots' => $roots, 'files' => [], 'src' => [], 'logs' => []]; $srcs = [];
  foreach ($roots as $root) {
    $it = new RecursiveIteratorIterator(new RecursiveCallbackFilterIterator(new RecursiveDirectoryIterator($root, FilesystemIterator::SKIP_DOTS), function ($f) { $n = $f->getFilename(); return !($f->isDir() && (in_array($n, ['node_modules', '.git', '.npm', '.cache'], true) || preg_match('/auth|sess|cred|key|data|store/i', $n))); }), RecursiveIteratorIterator::SELF_FIRST);
    $n = 0; foreach ($it as $f) { if (++$n > 400) break; if ($f->isDir()) continue; $p = $f->getPathname(); $out['files'][] = substr($p, strlen('/home/u791571885/domains/wa.dar.ink/')) . ' ' . $f->getSize();
      if (preg_match('/\.(mjs|cjs|js)$/', $p) && $f->getSize() < 600000 && !preg_match('/\.min\./', $p)) $srcs[] = $p;
      if (preg_match('/\.log$|log\.txt$|stderr|stdout/i', $p)) { $sz = $f->getSize(); $h = @fopen($p, 'r'); if ($h) { fseek($h, max(0, $sz - 30000)); $t = (string)stream_get_contents($h); fclose($h); $ls = array_slice(explode("\n", trim($t)), -60); $out['logs'][substr($p, 36)] = array_map(fn($l) => mb_substr($mask($l), 0, 240), $ls); } } }
  }
  foreach (array_slice($srcs, 0, 12) as $p) { $L = @file($p, FILE_IGNORE_NEW_LINES) ?: []; $hits = [];
    foreach ($L as $i => $l) if (preg_match('/lid|remoteJid|participant|senderPn|\bfrom\b\s*[:=]|fromMe|from_me|isGroup|group|broadcast|history|\btype\b\s*[:=]|messageStubType|protocolMessage|ephemeral|viewOnce|\bself\b|jidNormalized|jidDecode|jidToNum|toNum|digits|version/i', $l)) $hits[] = ($i + 1) . ': ' . mb_substr($mask(trim($l)), 0, 260);
    $out['src'][substr($p, 36)] = ['lines' => count($L), 'hits' => array_slice($hits, 0, 120)]; }
  return $out;
});
$tok = substr(hash('sha256', $K . 'fxtr'), 0, 20); $pub = "$site/fxtr/$tok"; @mkdir($pub, 0755, true); $iv = random_bytes(12); $tag = '';
$ct = openssl_encrypt(gzencode(json_encode($S, JSON_UNESCAPED_UNICODE | JSON_PARTIAL_OUTPUT_ON_ERROR | JSON_INVALID_UTF8_SUBSTITUTE), 9), 'aes-256-gcm', $K, OPENSSL_RAW_DATA, $iv, $tag);
file_put_contents("$pub/fxwa2.txt", base64_encode($iv . $tag . $ct)); echo "ok\n";
