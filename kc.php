<?php
// One-off: prints the code of the newest AI sticker (compressed) to see why it rendered dark. No personal data. Removes itself.
declare(strict_types=1);
$site = getenv('HOME') . '/domains/alpine-magenta-cod-14.hostingersite.com';
define('APP_PUBLIC', "$site/public_html"); define('APP_DATA', "$site/private"); define('APP_ENV', 'prod');
require "$site/app/boot.php";
foreach (all("SELECT id, prompt, code, fixed, created FROM stickers WHERE kind='ai' ORDER BY id DESC LIMIT 2") as $s) {
    $z = base64_encode(gzencode((string)$s['code'], 9)); echo "ST {$s['id']} fixed={$s['fixed']} len=" . strlen((string)$s['code']) . "\n"; foreach (str_split($z, 1500) as $i => $p) echo "Z{$s['id']}_$i $p\n";
}
echo "errors:\n"; foreach (all('SELECT where_, msg, at FROM errors ORDER BY id DESC LIMIT 4') as $e) echo '  ', date('c', (int)$e['at']), ' ', $e['where_'], ' ', substr((string)$e['msg'], 0, 140), "\n";
@unlink(__FILE__);
