<?php
// A live check run on the host: the outside services the app uses, tested from the server itself, plus health.
// Prints only results — no keys, no personal data. Usage: php livecheck.php [site-folder]
declare(strict_types=1);
ini_set('display_errors', '1'); error_reporting(E_ALL); set_time_limit(240);
register_shutdown_function(function () { $e = error_get_last(); if ($e && in_array($e['type'], [E_ERROR, E_PARSE, E_CORE_ERROR, E_COMPILE_ERROR], true)) echo "FATAL: {$e['message']} at " . basename($e['file']) . ':' . $e['line'] . "\n"; });
$site = $argv[1] ?? getenv('HOME') . '/domains/alpine-magenta-cod-14.hostingersite.com';
define('APP_PUBLIC', "$site/public_html"); define('APP_DATA', "$site/private"); define('APP_ENV', 'prod');
require "$site/app/boot.php";
$o = [];
$ids = ['push', 'cron', 'embed', 'places', 'catalog']; foreach ((array)setting('ai.providers', []) as $p) if (empty($p['off'])) $ids[] = 'ai.' . $p['id'];
foreach ($ids as $id) { echo "… $id\n"; $t0 = microtime(true); try { $r = integration_test($id, ['email' => '']); } catch (Throwable $e) { $r = ['ok' => false, 'note' => 'error: ' . $e->getMessage() . ' at ' . basename($e->getFile()) . ':' . $e->getLine()]; } $o[$id] = ['ok' => $r['ok'], 'note' => substr((string)$r['note'], 0, 140), 'ms' => (int)((microtime(true) - $t0) * 1000)]; echo '  ', json_encode($o[$id], JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE), "\n"; }
$h = health(); unset($h['backup_last']['counts']);
echo json_encode(['health' => $h, 'mail_function' => function_exists('mail')], JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT), "\n";
if (dirname(__FILE__) === getenv('HOME')) @unlink(__FILE__);
