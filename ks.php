<?php
// One-off quality check: the live AI providers write three living stickers; prints the code (for testing in a browser) and
// whether each passes the server's safety filter. No personal data. Removes itself.
declare(strict_types=1);
$site = getenv('HOME') . '/domains/alpine-magenta-cod-14.hostingersite.com';
define('APP_PUBLIC', "$site/public_html"); define('APP_DATA', "$site/private"); define('APP_ENV', 'prod');
require "$site/app/boot.php";
$out = [];
foreach (['قمر يبتسم حين ألمسه', 'نجوم تتفرقع عند اللمس', 'كلمة «صباح الخير» تتمايل مع الضوء'] as $p) {
    $t0 = microtime(true); $code = null; $raw = '';
    for ($try = 0; $try < 2 && !$code; $try++) { $raw = (string)ai_chat([['role' => 'system', 'content' => "You are a creative coder who makes tiny living animated stickers.\n" . STUDIO_DOC], ['role' => 'user', 'content' => 'The sticker: ' . $p]], ['max' => 2200, 'temp' => .7]); $code = studio_code($raw); }
    $out[] = ['prompt' => $p, 'ok' => (bool)$code, 'ms' => (int)((microtime(true) - $t0) * 1000), 'code' => base64_encode($code ?? $raw)];
}
$z = base64_encode(gzencode(json_encode($out), 9)); echo 'STICKERS ', strlen($z), "\n"; foreach (str_split($z, 1800) as $i => $part) echo "Z$i $part\n";
@unlink(__FILE__);
