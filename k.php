<?php
// Post-install check: what the live page sends first (identity, scheme, + button, push key present) and the latest server
// errors (message + place only). No keys, no personal data. Removes itself.
declare(strict_types=1);
$site = getenv('HOME') . '/domains/alpine-magenta-cod-14.hostingersite.com';
define('APP_PUBLIC', "$site/public_html"); define('APP_DATA', "$site/private"); define('APP_ENV', 'prod');
require "$site/app/boot.php";
$r = http_call('GET', 'https://alpine-magenta-cod-14.hostingersite.com/', [], null, 20); $html = $r['body'];
preg_match_all('/<html[^>]*>/', $html, $m); echo "status {$r['status']}\n", $m[0][0] ?? 'no html tag', "\n";
echo 'title: ', preg_match('/<title>([^<]*)/', $html, $t) ? $t[1] : '-', "\n";
echo 'dark palette: ', str_contains($html, 'prefers-color-scheme: dark') ? 'yes' : 'no', "\n";
echo 'push key in page: ', preg_match('/"vapid":"([A-Za-z0-9_-]{80,})"/', $html) ? 'yes' : 'no', "\n";
foreach (['/assets/logos/thread-huddle-192.png', '/sw.js', '/manifest.webmanifest', '/icon.svg'] as $p) { $x = http_call('GET', 'https://alpine-magenta-cod-14.hostingersite.com' . $p, [], null, 15); echo "$p {$x['status']}", $p === '/sw.js' ? (str_contains($x['body'], "addEventListener('push'") ? ' (push handler)' : ' (no push handler)') . ' type=' . ($x['headers']['content-type'] ?? '-') . ' cache=' . ($x['headers']['cache-control'] ?? '-') : '', "\n"; }
echo 'sw.js on disk has push: ', str_contains((string)@file_get_contents(APP_PUBLIC . '/sw.js'), 'showNotification') ? 'yes' : 'no', "\n";
echo 'version: ', APP_VERSION, "\n";
echo "brand: ", json_encode(array_intersect_key(brand(), array_flip(['id', 'allowed', 'mark', 'accent', 'accent2'])), JSON_UNESCAPED_SLASHES), "\n";
echo "errors:\n"; foreach (all('SELECT where_, msg, file, at FROM errors ORDER BY id DESC LIMIT 6') as $e) echo '  ', date('c', (int)$e['at']), ' ', $e['where_'], ' ', substr((string)$e['msg'], 0, 160), ' @', $e['file'], "\n";
@unlink(__FILE__);
