<?php
// One-off quality check: the live AI writes ONE living sticker (prompt picked by the minute) with the app's own brief and
// strong model; prints the plain code to test in a browser. No personal data. Removes itself.
declare(strict_types=1);
$site = getenv('HOME') . '/domains/alpine-magenta-cod-14.hostingersite.com';
define('APP_PUBLIC', "$site/public_html"); define('APP_DATA', "$site/private"); define('APP_ENV', 'prod');
require "$site/app/boot.php"; @set_time_limit(170);
$ps = ['طفل يضحك', 'قمر يبتسم حين ألمسه', 'قطة تلوّح بيدها', 'كلمة «صباح الخير» تتمايل مع الضوء'];
$p = $ps[intdiv((int)date('i'), 5) % count($ps)]; $t0 = microtime(true); $code = null; $raw = '';
for ($try = 0; $try < 2 && !$code; $try++) { $raw = (string)ai_chat([['role' => 'system', 'content' => "You are a creative coder and illustrator who makes tiny living animated stickers.\n" . STUDIO_DOC], ['role' => 'user', 'content' => 'The sticker: ' . $p]], ['max' => 2600, 'temp' => .7, 'strong' => true, 'timeout' => 55]); $code = studio_code($raw); }
echo "PROMPT $p ok=", $code ? 1 : 0, ' ms=', (int)((microtime(true) - $t0) * 1000), ' version=', APP_VERSION, "\n", $code ?? substr($raw, 0, 600), "\n----\n";
@unlink(__FILE__);
