<?php
// A live check run on the host: the outside services the app uses, tested from the server itself, plus health.
// Prints only results — no keys, no personal data. Usage: php livecheck.php [site-folder]
declare(strict_types=1);
$site = $argv[1] ?? getenv('HOME') . '/domains/alpine-magenta-cod-14.hostingersite.com';
define('APP_PUBLIC', "$site/public_html"); define('APP_DATA', "$site/private"); define('APP_ENV', 'prod');
require "$site/app/boot.php";
$o = [];
foreach (['catalog', 'places', 'embed', 'push', 'cron'] as $id) { $t0 = microtime(true); try { $r = integration_test($id, ['email' => '']); } catch (Throwable $e) { $r = ['ok' => false, 'note' => 'error: ' . $e->getMessage()]; } $o[$id] = ['ok' => $r['ok'], 'note' => substr((string)$r['note'], 0, 100), 'ms' => (int)((microtime(true) - $t0) * 1000)]; }
foreach ((array)setting('ai.providers', []) as $p) if (empty($p['off'])) { $t0 = microtime(true); $r = integration_test('ai.' . $p['id'], ['email' => '']); $o['ai.' . $p['id']] = ['ok' => $r['ok'], 'note' => substr((string)$r['note'], 0, 100), 'ms' => (int)((microtime(true) - $t0) * 1000)]; }
$h = health(); unset($h['backup_last']['counts']);
echo json_encode(['services' => $o, 'health' => $h, 'mail_function' => function_exists('mail')], JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT), "\n";
if (str_contains(__FILE__, '/lc.php')) @unlink(__FILE__);
