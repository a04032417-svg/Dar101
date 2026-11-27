<?php
// Post-install check for 2.7.0: removes the earlier test pictures, then draws three real sticker arts with the app's own
// pipeline (plan → free image model) and prints where they are, so they can be looked at. No personal data. Removes itself.
declare(strict_types=1);
$site = getenv('HOME') . '/domains/alpine-magenta-cod-14.hostingersite.com';
define('APP_PUBLIC', "$site/public_html"); define('APP_DATA', "$site/private"); define('APP_ENV', 'prod');
require "$site/app/boot.php"; @set_time_limit(280);
foreach (glob(APP_PUBLIC . '/_t/*') ?: [] as $f) @unlink($f); @rmdir(APP_PUBLIC . '/_t');
echo 'version: ', APP_VERSION, ' schema: ', (int)db()->query('PRAGMA user_version')->fetchColumn(), ' spec column: ', db()->query("SELECT COUNT(*) FROM pragma_table_info('stickers') WHERE name='spec'")->fetchColumn(), "\n";
foreach ([['طفل يضحك بشدة', 'cartoon'], ['قطة تقول صباح الخير', '3d'], ['فنجان قهوة عربية سعيد', 'clay']] as [$p, $style]) {
    $t0 = microtime(true); $plan = sticker_plan($p, 'ar'); $art = sticker_art($plan['art'], $style, random_int(1, 99999)); $ms = (int)((microtime(true) - $t0) * 1000);
    if (!$art) { echo "$p: no art ({$ms}ms)\n"; continue; }
    $u = media_put($art['bytes'], $art['mime'] === 'image/png' ? 'png' : 'jpg'); echo "$p [$style] via {$art['via']} {$ms}ms motion={$plan['motion']} fx=" . implode(',', $plan['fx']) . " caption={$plan['caption']}\n  art: {$plan['art']}\n  https://alpine-magenta-cod-14.hostingersite.com$u\n";
}
echo "errors:\n"; foreach (all("SELECT where_, msg, at FROM errors WHERE at > ? ORDER BY id DESC LIMIT 5", [time() - 900]) as $e) echo '  ', $e['where_'], ' ', substr((string)$e['msg'], 0, 160), "\n";
@unlink(__FILE__);
