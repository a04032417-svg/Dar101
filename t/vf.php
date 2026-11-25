<?php
// Read-only check of the live site after 3.34.19: the pages by their own address, the buyers' preview pages, the WhatsApp gateway's health.
if (PHP_SAPI !== 'cli') exit;
$H = '/home/u791571885'; $D = "$H/domains/dar.ink/public_html"; chdir($D); require $D . '/dar-sync.php';
$get = function (string $u): array { $c = curl_init($u); curl_setopt_array($c, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 25, CURLOPT_FOLLOWLOCATION => false, CURLOPT_USERAGENT => 'Mozilla/5.0 dar-check']); $b = (string)curl_exec($c); $s = (int)curl_getinfo($c, CURLINFO_HTTP_CODE); curl_close($c); return [$s, $b]; };
$out = []; @unlink("$H/p.php"); foreach (['report.json', 'lock', 'pkg.zip', 'site.zip'] as $x) @unlink("$H/xfer-dp/$x"); @rmdir("$H/xfer-dp"); $out['files_check'] = doc_chk_files(true); $out['version'] = SYNC_VERSION; $out['auto_soon'] = meta_get('auto_soon');
foreach (['/', '/app/', '/builders/', '/providers/', '/developer/', '/upload/'] as $p) { [$s, $b] = $get('https://dar.ink' . $p); $out['page' . $p] = [$s, str_contains($b, '3.34.20-bcd981a6')]; }
$t = pv_token(); $cfg = pv_cfg(); $out['preview_on'] = (bool)$cfg['on']; $out['preview_gate'] = pv_login() !== null;
if ($t !== '') foreach (['', 'offices', 'developers', 'providers', 'marketers', 'programmers', 'platform'] as $p) { [$s, $b] = $get('https://dar.ink/v/' . $t . '/' . $p); $out['pv/' . ($p ?: 'root')] = [$s, strlen($b), str_contains($b, 'pv_user') ? 'gate' : (str_contains($b, 'pv-flag.js') ? 'interface' : (str_contains($b, 'class="cards"') ? 'chooser' : '?'))]; }
foreach (['assets/pvfill.js', 'assets/ex-plat.js', 'dar-tg.php', 'dar-fx.php', 'assets/tgqr.js'] as $f) { [$s] = $get('https://dar.ink/' . $f); $out['file:' . $f] = $s; }
[$s, $b] = $get('https://wa.dar.ink/health'); $j = json_decode($b, true); $out['gateway'] = [$s, $j['v'] ?? null, array_key_exists('tg', (array)$j) ? 'has_tg' : 'no_tg', $j['ok'] ?? null];
echo json_encode($out, JSON_UNESCAPED_SLASHES), "\n";
