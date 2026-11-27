<?php
// Post-install check for 2.8.0 (the order of ruck): version, schema, the new tables, the new services answering, the public
// pages rendering and the new bundle in place. Prints no personal data. Removes itself.
declare(strict_types=1);
$site = getenv('HOME') . '/domains/alpine-magenta-cod-14.hostingersite.com';
define('APP_PUBLIC', "$site/public_html"); define('APP_DATA', "$site/private"); define('APP_ENV', 'prod');
require "$site/app/boot.php"; @set_time_limit(120);
echo 'version: ', APP_VERSION, ' schema: ', (int)db()->query('PRAGMA user_version')->fetchColumn(), "\n";
$need = ['usage', 'experiments', 'sunset_q', 'night_msgs', 'place_notes', 'poem_lines', 'mail', 'pigeons', 'relays', 'races', 'promises', 'badges', 'trips', 'tr_cache', 'council', 'twin_trips', 'truth', 'key_buys', 'treasures', 'book_orders'];
$miss = array_filter($need, fn($t) => !val("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", [$t])); echo 'tables: ', $miss ? 'MISSING ' . implode(',', $miss) : 'all ' . count($need) . ' present', "\n";
echo 'services: ', count(SERVICES), ' · apis: ', count(array_filter(array_keys($GLOBALS['API']), fn($n) => preg_match('/^(sunsetq|night|poem|moodmap|moon|phenom|season|placebook|sound|gift|challenge|harvest|skybook|mail|pigeon|relay|race|promise|threads|badge|hardday|trip|twin\.trips|laugh|whisper|truth|treasure|welcome|widget|tr\.text|services|track)/', $n))), "\n";
$own = one("SELECT * FROM users WHERE role='owner' ORDER BY id LIMIT 1");
if ($own) { $GLOBALS['__as'] = $own;
  foreach (['services.mine', 'sky.extras', 'season.now', 'phenom.list', 'moon.pano', 'poem.today', 'race.now', 'mail.inbox', 'pigeon.me', 'challenge.now', 'widget.data', 'admin.services', 'admin.ops'] as $n) { try { $r = api_run($n, []); echo "  $n ok", is_array($r) ? ' (' . count($r) . ' keys)' : '', "\n"; } catch (Throwable $e) { echo "  $n FAIL ", ($e instanceof ApiError ? $e->codeName : substr($e->getMessage(), 0, 120)), "\n"; } }
  unset($GLOBALS['__as']); }
ob_start(); $GLOBALS['PAGES']['#^/sky-now/?$#']([]); $h = ob_get_clean(); echo 'sky-now page: ', str_contains($h, 'سماء العالم الآن') ? 'renders ' . strlen($h) . ' bytes' : 'FAIL', "\n";
$man = json_decode((string)@file_get_contents(APP_PUBLIC . '/assets/manifest.json'), true) ?: []; $js = (string)@file_get_contents(APP_PUBLIC . ($man['main']['js'] ?? '/x'));
$chunks = implode('', array_map('file_get_contents', glob(APP_PUBLIC . '/assets/c-*.js') ?: []));
foreach (['circle.me', 'sky.extras', 'mail.inbox', 'night.room', 'jw_outbox', 'twin.command', 'whisper.play'] as $k) echo "  bundle $k: ", str_contains($js . $chunks, $k) ? 'yes' : 'NO', "\n";
echo "errors (15 min):\n"; foreach (all("SELECT where_, msg FROM errors WHERE at > ? ORDER BY id DESC LIMIT 6", [time() - 900]) as $e) echo '  ', $e['where_'], ' ', substr((string)$e['msg'], 0, 160), "\n";
@unlink(__FILE__);
