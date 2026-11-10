<?php
// Read-only (2026-11-10): why «فرح» stops after a while. Reads the Telegram link, the gateway, her switches, every chat's mode,
// log size, minutes since its last message in and her last message out, and the hourly caps' current counts; then the last 12 h
// by hour, in and out. No message text, nothing sent, nothing changed. Output: .dar/tgdiag.txt (a folder the web cannot read).
$site = '/home/u791571885/domains/dar.ink/public_html';
chdir($site); $_SERVER['REQUEST_TIME_FLOAT'] = microtime(true); $argv = ['dar-sync.php', 'job']; $argc = 2;
require $site . '/dar-sync.php';
$S = ['at' => gmdate('c'), 'version' => defined('SYNC_VERSION') ? SYNC_VERSION : ''];
$sec = function (string $k, callable $f) use (&$S) { try { $S[$k] = $f(); } catch (Throwable $e) { $S[$k] = 'err: ' . substr($e->getMessage(), 0, 200) . ' @' . $e->getLine(); } };
$hit = function (string $bucket) { $r = one('SELECT n, at FROM hits WHERE k = ?', [hash('sha256', $bucket . '|*')]); return $r ? ['n' => (int)$r['n'], 'age_min' => (int)((time() - (int)$r['at']) / 60)] : null; };
$sec('switches', function () { $p = tgu_persona(); return ['reply_all' => tgu_reply_all_on(), 'persona_on' => !empty($p['on']), 'name' => (string)($p['name'] ?? ''), 'notes_len' => mb_strlen((string)($p['notes'] ?? '')), 'notes_head' => mb_substr((string)($p['notes'] ?? ''), 0, 300), 'status_meta' => json_decode((string)(meta_get('tgu_status') ?? ''), true), 'now' => time()]; });
$sec('gateway', function () { $g = wag_cfg(); return ['ready' => tgu_ready(), 'host' => parse_url((string)$g['url'], PHP_URL_HOST), 'wag_in_at' => (int)meta_get('wag_in_at'), 'wag_tick_at' => (int)meta_get('wag_tick_at'), 'now' => time()]; });
$sec('state', function () { $s = tgu_state(); return array_intersect_key($s, array_flip(['status', 'why', 'keys', 'reason', 'since', 'at'])); });
$sec('caps', function () use ($hit) { return ['tgu_all' => $hit('tgu_all'), 'tgu_sweep' => $hit('tgu_sweep')]; });
$sec('chats', function () use ($hit) {
    $now = now_ms(); $rows = []; $types = [];
    foreach (tgu_chats() as $id => $x) {
        $l = tgu_log((string)$id); $in = array_values(array_filter($l, fn($y) => empty($y['out']))); $o = array_values(array_filter($l, fn($y) => !empty($y['out'])));
        $t = (string)($x['type'] ?? ''); $types[$t] = ($types[$t] ?? 0) + 1;
        $rows[] = ['id' => substr(hash('sha256', 'tgd|' . $id), 0, 6), 'type' => $t, 'mode' => (string)($x['mode'] ?? 'off'), 'log' => count($l),
            'in_min' => $in ? (int)(($now - (int)end($in)['at']) / 60000) : null, 'out_min' => $o ? (int)(($now - (int)end($o)['at']) / 60000) : null, 'cap' => $hit('tgu_chat:' . $id)];
    }
    usort($rows, fn($a, $b) => ($a['in_min'] ?? PHP_INT_MAX) <=> ($b['in_min'] ?? PHP_INT_MAX));
    return ['n' => count($rows), 'types' => $types, 'rows' => array_slice($rows, 0, 45)];
});
$sec('hours', function () {
    $now = now_ms(); $h = [];
    foreach (tgu_chats() as $id => $x) foreach (tgu_log((string)$id) as $y) { $ago = intdiv($now - (int)($y['at'] ?? 0), 3600000); if ($ago < 0 || $ago > 11) continue; $k = !empty($y['out']) ? 'out' : 'in'; $h[$ago][$k] = ($h[$ago][$k] ?? 0) + 1; }
    ksort($h); $out = []; foreach ($h as $ago => $v) $out[gmdate('H', intdiv($now, 1000) - $ago * 3600) . 'h'] = $v; return $out;
});
$sec('dialogs', function () { $x = tgu_call('GET', '/dialogs?limit=100'); $it = is_array($x['json']['items'] ?? null) ? $x['json']['items'] : null; $t = []; if ($it) foreach ($it as $d) { $k = (string)($d['type'] ?? ''); $t[$k] = ($t[$k] ?? 0) + 1; } return ['code' => (int)$x['code'], 'why' => $x['code'] == 200 ? '' : tgu_why($x), 'n' => $it === null ? null : count($it), 'types' => $t]; });
@file_put_contents($site . '/.dar/tgdiag.txt', json_encode($S, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n");
echo "ok\n";
