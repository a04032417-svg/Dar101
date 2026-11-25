<?php
// Installs Dar 3.34.19 on the live site (the owner, 2026-11-25: remove the templates factory and Telegram, fix the buyers' preview).
// Usage: php dp.php <64-hex key>. Runs once (a lock, then a report kept outside the site); later runs only print that report.
// The package is AES-256-GCM (iv 12 | tag 16 | ciphertext) and the key never lives in this file. It uses Dar's own installer steps:
// the package is checked, the site is backed up (Dar's backups), written, checked from outside (guard_canary) and put back at once
// if that check fails. Before anything, the database is copied outside the site. Nothing is deleted that cannot be brought back:
// the factory's folders and the removed files are MOVED outside the site, not erased; only the Telegram keys are erased.
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$key = $argv[1] ?? ''; if (!preg_match('/^[0-9a-f]{64}$/', $key)) { echo "{\"err\":\"key\"}\n"; exit; }
const BLOB = 'https://raw.githubusercontent.com/a04032417-svg/Dar101/6a8b7a5d6e1a42aaca23c362d28b915b4cd91e43/t/dp.bin';
$H = '/home/u791571885'; $D = "$H/domains/dar.ink/public_html"; $T = "$H/xfer-dp"; @mkdir($T, 0700, true);
$stamp = '20261125'; $KEEP = "$H/dar-removed-$stamp"; @mkdir($KEEP, 0700, true);
$rep = "$T/report.json"; if (is_file($rep)) { echo file_get_contents($rep), "\n"; exit; }
$lk = fopen("$T/lock", 'c'); if (!flock($lk, LOCK_EX | LOCK_NB)) { echo "{\"busy\":true}\n"; exit; }
if (is_file($rep)) { echo file_get_contents($rep), "\n"; exit; }
$out = ['started' => gmdate('c')]; $say = function ($o) use ($rep) { file_put_contents($rep, json_encode($o, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE)); echo json_encode($o, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE), "\n"; exit; };
// 1) the package
$bin = @file_get_contents(BLOB, false, stream_context_create(['http' => ['timeout' => 120]])); if (!is_string($bin) || strlen($bin) < 1000) $say($out + ['err' => 'download']);
$plain = openssl_decrypt(substr($bin, 28), 'aes-256-gcm', hex2bin($key), OPENSSL_RAW_DATA, substr($bin, 0, 12), substr($bin, 12, 16)); unset($bin);
if (!is_string($plain)) $say($out + ['err' => 'decrypt']);
$pk = "$T/pkg.zip"; file_put_contents($pk, $plain); unset($plain);
$P = new ZipArchive(); if ($P->open($pk) !== true) $say($out + ['err' => 'zip']);
$plan = json_decode((string)$P->getFromName('plan.json'), true); if (!is_array($plan)) $say($out + ['err' => 'plan']);
$siteZip = "$T/site.zip"; file_put_contents($siteZip, (string)$P->getFromName('site.zip'));
$gw = (string)$P->getFromName('gw.zip'); $P->close();
// 2) Dar itself (its installer's steps); the database copied outside the site first
chdir($D); require $D . '/dar-sync.php';
$dbf = data_dir() . '/dar.sqlite'; $dbk = "$KEEP/dar-before-3.34.19.sqlite";
try { if (!is_file($dbk)) db()->exec('VACUUM INTO ' . db()->quote($dbk)); } catch (Throwable $e) { $say($out + ['err' => 'db_backup', 'why' => substr($e->getMessage(), 0, 160)]); }
$out['db_backup'] = is_file($dbk) ? round(filesize($dbk) / 1048576, 1) . ' MB' : 'missing'; if (!is_file($dbk)) $say($out + ['err' => 'db_backup']);
// 3) out of the site: the factory's folders and Telegram's dumps (moved, not erased)
$moved = [];
foreach ($plan['move'] as $rel) { $src = $D . '/' . $rel; if (!file_exists($src)) continue; $dst = $KEEP . '/site/' . $rel; @mkdir(dirname($dst), 0700, true); if (@rename($src, $dst)) $moved[] = $rel; }
$out['moved_out'] = $moved;
$back = function () use ($moved, $D, $KEEP) { foreach ($moved as $rel) { $dst = $D . '/' . $rel; if (!file_exists($dst)) @rename($KEEP . '/site/' . $rel, $dst); } };
// 4) the new version, by Dar's own installer steps
$z = new ZipArchive(); if ($z->open($siteZip) !== true) { $back(); $say($out + ['err' => 'site_zip']); }
try {
    $entries = site_entries($z);
    foreach ($entries as $name => $i) { if (strtolower(pathinfo($name, PATHINFO_EXTENSION)) !== 'php') continue; try { token_get_all((string)$z->getFromIndex($i), TOKEN_PARSE); } catch (Throwable $e) { $back(); $say($out + ['err' => 'php_parse', 'file' => $name]); } }
    if (function_exists('guard_check_zip') && ($bad = guard_check_zip($z, $entries))) { $back(); $say($out + ['err' => 'guard_check', 'bad' => array_slice((array)$bad, 0, 8)]); }
    $backup = site_backup($D); $out['site_backup'] = $backup;
    $out['files'] = site_extract($z, $entries, $D);
} catch (Throwable $e) { $z->close(); $back(); $say($out + ['err' => 'install', 'why' => substr($e->getMessage(), 0, 200)]); }
$z->close();
// the files this version no longer has (moved out too)
$gone = []; foreach ($plan['remove'] as $rel) { $src = $D . '/' . $rel; if (!is_file($src)) continue; $dst = $KEEP . '/site/' . $rel; @mkdir(dirname($dst), 0700, true); if (@rename($src, $dst)) $gone[] = $rel; }
$out['removed'] = $gone; if (function_exists('opcache_reset')) @opcache_reset();
// 5) checked from outside; broken → everything put back at once
$g = function_exists('guard_canary') ? guard_canary() : ['ok' => null, 'why' => 'no_guard'];
$out['canary'] = ['ok' => $g['ok'], 'fails' => array_slice((array)($g['fails'] ?? []), 0, 6), 'why' => $g['why'] ?? ''];
if ($g['ok'] === false) {
    $z2 = new ZipArchive(); if ($z2->open(data_dir() . '/backups/' . $backup) === true) { try { site_extract($z2, site_entries($z2, false), $D); } finally { $z2->close(); } }
    foreach ($gone as $rel) @rename($KEEP . '/site/' . $rel, $D . '/' . $rel); $back(); $again = guard_canary();
    $say($out + ['err' => 'canary_failed_rolled_back', 'back' => $again['ok']]);
}
try { $mj = json_decode((string)@file_get_contents($D . '/lib/manifest.json'), true); if (is_array($mj) && is_array($mj['files'] ?? null) && function_exists('doc_golden_make')) $out['golden'] = doc_golden_make($mj); } catch (Throwable $e) { $out['golden'] = false; }
meta_set('guard_update', jenc(['at' => now_ms(), 'backup' => $backup, 'version' => '3.34.20', 'files' => []]));
try { $out['assets'] = assets_autoswitch(true); } catch (Throwable $e) { $out['assets'] = substr($e->getMessage(), 0, 100); }
// 6) Telegram's keys and settings erased (the keys of his own account and of the bot; the channel; the alerts' chat)
$tg = [];
foreach (['grow:telegram', 'p:rq.tgu.api_hash', 'p:rq.alerts.tg_token'] as $k) { if (vault_get($k) !== null) { vault_put($k, null); $tg[] = $k; } }
$c = function_exists('rq_cfg') ? rq_cfg() : (o2a(jdec(meta_get('rq_cfg'))) ?: []); $ch = false; foreach (['tgu.api_id', 'alerts.tg_chat'] as $k) if (array_key_exists($k, $c)) { unset($c[$k]); $ch = true; $tg[] = 'rq_cfg:' . $k; }
if ($ch) meta_set('rq_cfg', jenc((object)$c));
$sm = o2a(jdec(meta_get('secrets_meta'))) ?: []; $ch = false; foreach (['rq.tgu.api_hash', 'rq.alerts.tg_token'] as $k) if (array_key_exists($k, $sm)) { unset($sm[$k]); $ch = true; $tg[] = 'secrets_meta:' . $k; }
if ($ch) meta_set('secrets_meta', jenc((object)$sm));
$PR = platform_rec(); if (isset($PR->grow) && is_object($PR->grow) && property_exists($PR->grow, 'telegram')) { unset($PR->grow->telegram); kv_put('platform', 'platform', jenc($PR), 'update'); $tg[] = 'platform:grow.telegram'; }
$out['telegram_erased'] = $tg;
// the gateway's Telegram session (his account's login on the gateway) — erased; the gateway's new package is left beside its site
$ses = []; foreach ([$H . '/.dar-wa/_tg', $H . '/domains/wa.dar.ink/.dar-wa/_tg'] as $d) if (is_dir($d)) { foreach (new RecursiveIteratorIterator(new RecursiveDirectoryIterator($d, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::CHILD_FIRST) as $f) { $f->isDir() ? @rmdir($f->getPathname()) : @unlink($f->getPathname()); } @rmdir($d); $ses[] = $d; }
$out['tg_session_erased'] = $ses;
if ($gw !== '') { $gd = $H . '/domains/wa.dar.ink/public_html'; if (is_dir($gd)) { file_put_contents($gd . '/dar-wa-gateway-1.2.0.zip', $gw); $out['gateway_zip'] = 'public_html/dar-wa-gateway-1.2.0.zip'; } else $out['gateway_zip'] = 'no_dir'; }
@unlink($pk); @unlink($siteZip);
$mv = json_decode((string)@file_get_contents($D . '/lib/manifest.json'), true); $out['version'] = (string)($mv['version'] ?? '?'); $out['done'] = gmdate('c');
$say($out);
