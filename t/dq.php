<?php
// Installs Dar 3.34.20, token 3.34.20-5055fc0f (the owner, 2026-11-25: «يوجد خلل في سرعة Dar.ink» — the main page took 10–15 s):
// boot.js asks for every file a page will import at once (modulepreload) instead of about ten levels one after another, and
// .htaccess finally sends the year-long Cache-Control of a versioned file (its max-age=0 section used to replace it).
// Usage: php dq.php <64-hex key>. Runs once (a lock, then a report kept outside the site); later runs only print that report.
// Dar's own installer steps: the package checked, the site backed up, written, checked from outside (guard_canary) and put back
// at once if that check fails. Nothing is moved or removed; the database is not touched.
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$key = $argv[1] ?? ''; if (!preg_match('/^[0-9a-f]{64}$/', $key)) { echo "{\"err\":\"key\"}\n"; exit; }
const BLOB = 'https://raw.githubusercontent.com/a04032417-svg/Dar101/eaa7d154c49dd42428b9fb89299a068323f0dc4e/t/dq.bin';
const TOK = '3.34.20-5055fc0f';
$H = getenv('DQ_HOME') ?: '/home/u791571885'; $D = getenv('DQ_SITE') ?: "$H/domains/dar.ink/public_html"; $T = "$H/xfer-dq"; @mkdir($T, 0700, true);
$rep = "$T/report.json"; if (is_file($rep)) { echo file_get_contents($rep), "\n"; exit; }
$lk = fopen("$T/lock", 'c'); if (!flock($lk, LOCK_EX | LOCK_NB)) { echo "{\"busy\":true}\n"; exit; }
if (is_file($rep)) { echo file_get_contents($rep), "\n"; exit; }
@unlink("$H/p.php");
$out = ['started' => gmdate('c')]; $say = function ($o) use ($rep) { file_put_contents($rep, json_encode($o, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE)); echo json_encode($o, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE), "\n"; exit; };
// 1) the package
$bin = getenv('DQ_BLOB_FILE') ? @file_get_contents(getenv('DQ_BLOB_FILE')) : @file_get_contents(BLOB, false, stream_context_create(['http' => ['timeout' => 120]]));
if (!is_string($bin) || strlen($bin) < 1000) $say($out + ['err' => 'download']);
$plain = openssl_decrypt(substr($bin, 28), 'aes-256-gcm', hex2bin($key), OPENSSL_RAW_DATA, substr($bin, 0, 12), substr($bin, 12, 16)); unset($bin);
if (!is_string($plain)) $say($out + ['err' => 'decrypt']);
$pk = "$T/pkg.zip"; file_put_contents($pk, $plain); unset($plain);
$P = new ZipArchive(); if ($P->open($pk) !== true) $say($out + ['err' => 'zip']);
$siteZip = "$T/site.zip"; file_put_contents($siteZip, (string)$P->getFromName('site.zip')); $P->close();
// 2) Dar itself, by its installer's steps
chdir($D); require $D . '/dar-sync.php';
$out['from'] = (string)((json_decode((string)@file_get_contents($D . '/lib/manifest.json'), true) ?: [])['token'] ?? '?');
$z = new ZipArchive(); if ($z->open($siteZip) !== true) $say($out + ['err' => 'site_zip']);
try {
    $entries = site_entries($z);
    foreach ($entries as $name => $i) { if (strtolower(pathinfo($name, PATHINFO_EXTENSION)) !== 'php') continue; try { token_get_all((string)$z->getFromIndex($i), TOKEN_PARSE); } catch (Throwable $e) { $say($out + ['err' => 'php_parse', 'file' => $name]); } }
    if (function_exists('guard_check_zip') && ($bad = guard_check_zip($z, $entries))) $say($out + ['err' => 'guard_check', 'bad' => array_slice((array)$bad, 0, 8)]);
    $backup = site_backup($D); $out['site_backup'] = $backup;
    $out['files'] = site_extract($z, $entries, $D);
} catch (Throwable $e) { $z->close(); $say($out + ['err' => 'install', 'why' => substr($e->getMessage(), 0, 200)]); }
$z->close(); if (function_exists('opcache_reset')) @opcache_reset();
// 3) checked from outside; broken → the previous files put back at once
$g = getenv('DQ_NO_CANARY') ? ['ok' => true, 'why' => 'rehearsal'] : (function_exists('guard_canary') ? guard_canary() : ['ok' => null, 'why' => 'no_guard']);
$out['canary'] = ['ok' => $g['ok'], 'fails' => array_slice((array)($g['fails'] ?? []), 0, 6), 'why' => $g['why'] ?? ''];
if ($g['ok'] === false) {
    $z2 = new ZipArchive(); if ($z2->open(data_dir() . '/backups/' . $backup) === true) { try { site_extract($z2, site_entries($z2, false), $D); } finally { $z2->close(); } }
    if (function_exists('opcache_reset')) @opcache_reset(); $again = guard_canary();
    $say($out + ['err' => 'canary_failed_rolled_back', 'back' => $again['ok']]);
}
try { $mj = json_decode((string)@file_get_contents($D . '/lib/manifest.json'), true); if (is_array($mj) && is_array($mj['files'] ?? null) && function_exists('doc_golden_make')) $out['golden'] = doc_golden_make($mj); } catch (Throwable $e) { $out['golden'] = false; }
meta_set('guard_update', jenc(['at' => now_ms(), 'backup' => $backup, 'version' => '3.34.20', 'files' => []]));
try { $out['assets'] = assets_autoswitch(true); } catch (Throwable $e) { $out['assets'] = substr($e->getMessage(), 0, 100); }
@unlink($pk); @unlink($siteZip);
// 4) what a browser now receives: the versioned code kept a year, the page itself never kept
$head = function (string $u): array { $c = curl_init($u); curl_setopt_array($c, [CURLOPT_RETURNTRANSFER => true, CURLOPT_HEADER => true, CURLOPT_NOBODY => false, CURLOPT_TIMEOUT => 25, CURLOPT_USERAGENT => 'Mozilla/5.0 dar-check', CURLOPT_HTTPHEADER => ['Accept-Encoding: br, gzip']]); $r = (string)curl_exec($c); $s = (int)curl_getinfo($c, CURLINFO_HTTP_CODE); $hs = (int)curl_getinfo($c, CURLINFO_HEADER_SIZE); curl_close($c); $h = strtolower(substr($r, 0, $hs)); preg_match('/^cache-control:\s*(.+)$/m', $h, $m); return [$s, trim($m[1] ?? '-')]; };
if (!getenv('DQ_NO_CANARY')) {
    $b = 'https://dar.ink';
    $out['http'] = ['core.js' => $head($b . '/assets/v/' . TOK . '/core.js?v=' . TOK), 'boot.js' => $head($b . '/assets/v/' . TOK . '/boot.js'), 'dar.css' => $head($b . '/assets/v/' . TOK . '/dar.css'), 'page' => $head($b . '/'), 'config.json' => $head($b . '/config.json')];
    $p = (string)@file_get_contents($b . '/', false, stream_context_create(['http' => ['timeout' => 20]])); $out['page_token'] = page_token($p);
}
$mv = json_decode((string)@file_get_contents($D . '/lib/manifest.json'), true); $out['version'] = (string)($mv['version'] ?? '?'); $out['token'] = (string)($mv['token'] ?? '?'); $out['done'] = gmdate('c');
$say($out);
