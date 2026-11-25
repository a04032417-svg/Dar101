<?php
// Packs the live Dar CODE (no data, no downloads, no factory outputs) into an encrypted file for a one-time transfer.
// Usage: php tpk.php <64-hex key>. Idempotent: the work is done once; later runs only print the same report.
// The key never lives in this file (it is passed by the cron command); the output is AES-256-GCM: iv(12) | tag(16) | ciphertext.
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$key = $argv[1] ?? ''; if (!preg_match('/^[0-9a-f]{64}$/', $key)) { echo "{\"err\":\"key\"}\n"; exit; }
$H = '/home/u791571885'; $D = "$H/domains/dar.ink/public_html"; $T = "$H/xfer-tmp"; @mkdir($T, 0700, true);
$tag8 = substr(hash('sha256', 'dir' . $key), 0, 24); $name = substr(hash('sha256', 'file' . $key), 0, 24) . '.bin';
$outDir = "$D/x$tag8"; $out = "$outDir/$name"; $rep = "$T/report.json";
if (is_file($rep) && is_file($out)) { echo file_get_contents($rep), "\n"; exit; }
$lk = fopen("$T/lock", 'c'); if (!flock($lk, LOCK_EX | LOCK_NB)) { echo "{\"busy\":true}\n"; exit; }
if (is_file($rep) && is_file($out)) { echo file_get_contents($rep), "\n"; exit; }
$skipTop = ['dl', 'fxtr', 'fxv', 'upload', 'x' . $tag8];
$skipRe = '#^(\.dar/(data|fx|cache|tmp|logs?)(/|$))#';
$zipPath = "$T/src-" . getmypid() . ".zip"; @unlink($zipPath);
$z = new ZipArchive(); if ($z->open($zipPath, ZipArchive::CREATE | ZipArchive::OVERWRITE) !== true) { echo "{\"err\":\"zip\"}\n"; exit; }
$n = 0; $bytes = 0; $skipped = [];
$it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($D, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::SELF_FIRST);
foreach ($it as $f) {
  $p = $f->getPathname(); $r = substr($p, strlen($D) + 1); $top = explode('/', $r)[0];
  if (in_array($top, $skipTop, true) || preg_match($skipRe, $r) || $f->isLink()) { if (substr_count($r, '/') <= 1) $skipped[$r] = 1; continue; }
  if ($f->isDir()) continue;
  if (preg_match('/\.(sqlite|sqlite3|db|log)$/i', $r)) { $skipped[$r] = 1; continue; }
  $z->addFile($p, $r); $n++; $bytes += $f->getSize();
}
$z->close();
$plain = file_get_contents($zipPath); $iv = random_bytes(12); $tag = '';
$ct = openssl_encrypt($plain, 'aes-256-gcm', hex2bin($key), OPENSSL_RAW_DATA, $iv, $tag);
@mkdir($outDir, 0755, true); file_put_contents($out, $iv . $tag . $ct); @unlink($zipPath);
$o = ['files' => $n, 'raw_mb' => round($bytes / 1048576, 1), 'zip_mb' => round(strlen($plain) / 1048576, 1),
  'url' => "https://dar.ink/x$tag8/$name", 'sha256' => hash_file('sha256', $out), 'skipped' => array_keys($skipped)];
file_put_contents($rep, json_encode($o, JSON_UNESCAPED_SLASHES));
echo json_encode($o, JSON_UNESCAPED_SLASHES), "\n";
